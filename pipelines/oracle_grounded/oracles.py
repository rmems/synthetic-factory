"""The oracle boundary: adapters, availability probing, and provenance.

Issue #77 names six ground-truth runtimes (`axon-encoder`, `neuromod`,
`synaptic-mesh`, `limbic-critic`, `plasticity-lab`, and a validated recurrent
SNN). None of them are installed here. This module therefore defines the
boundary rather than pretending to cross it:

* ``ExternalCommandOracle`` speaks a small line protocol (``sf-oracle/1``) over
  stdin/stdout. Point ``SF_ORACLE_AXON_ENCODER_CMD`` at a command that speaks
  it and the real runtime becomes the oracle with no code change here.
* ``ReferenceOracle`` runs the deterministic simulator in ``sim.py`` and stamps
  ``implementation: "reference"`` so no record can pass itself off as output
  from the named runtime.

A bound external oracle never silently degrades to the reference one: if the
command fails, times out, or answers off-protocol, the run raises
``OracleError`` and the record is dropped. Curation fails closed.
"""

import json
import os
import re
import shlex
import shutil
import signal
import subprocess
import threading
import time
from pathlib import Path

from . import canon

PROTOCOL = "sf-oracle/1"
REPO_ROOT = Path(__file__).resolve().parents[2]
REPO_SLUG = "rmems/synthetic-factory"
DEFAULT_TIMEOUT_S = 60
MAX_PROTOCOL_STDOUT_BYTES = 8 * 1024 * 1024
MAX_PROTOCOL_STDERR_BYTES = 1024 * 1024
PROTOCOL_READ_BYTES = 64 * 1024

# The code whose identity a measurement depends on: the simulators, the
# adapters, the family wiring that turns a stored scenario back into an oracle
# request, the scenario RNG, and the canonical form the numbers are stored in.
# `record.py` is excluded because it validates records and never produces a
# measurement. Editing anything listed here changes `oracle.module_digest` and
# so invalidates every golden fixture that claims to have come from it.
IMPLEMENTATION_SOURCES = (
    "canon.py",
    "families.py",
    "generators.py",
    "oracles.py",
    "rng.py",
    "sim.py",
)
MODULE_PATH = "pipelines/oracle_grounded"

_MODULE_DIGEST_CACHE = {}
_SOURCE_COMMIT_CACHE = {}
RUNTIME_COMMIT_RE = re.compile(r"^[0-9a-fA-F]{7,64}$")
SOURCE_COMMIT_RE = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")


class OracleError(RuntimeError):
    """A bound oracle could not produce an authoritative result."""


def _reject_json_constant(value):
    raise ValueError(f"non-finite JSON token {value}")


def module_digest():
    """sha256 over the oracle implementation sources, cached per process."""
    key = "implementation"
    if key not in _MODULE_DIGEST_CACHE:
        here = Path(__file__).resolve().parent
        _MODULE_DIGEST_CACHE[key] = canon.digest_files(
            str(here / name) for name in IMPLEMENTATION_SOURCES
        )
    return _MODULE_DIGEST_CACHE[key]


def env_key(runtime):
    """Environment variable that binds a named runtime to this pipeline."""
    return "SF_ORACLE_" + str(runtime).upper().replace("-", "_").replace(".", "_") + "_CMD"


def is_runtime_commit(value):
    """Whether ``value`` is a resolved hexadecimal source revision."""
    return isinstance(value, str) and RUNTIME_COMMIT_RE.fullmatch(value) is not None


def is_source_commit(value):
    """Whether ``value`` is a fully resolved canonical source revision."""
    return isinstance(value, str) and SOURCE_COMMIT_RE.fullmatch(value) is not None


def resolve_source_commit(value, repo_root=None):
    """Return the canonical commit object id, or ``None`` when it is absent.

    Syntax alone is not provenance.  A full-length hexadecimal string is only
    a resolved source revision when the repository can prove that exact object
    exists and is a commit.
    """
    if not is_source_commit(value):
        return None
    root = Path(repo_root or REPO_ROOT)
    key = (str(root.resolve()), value)
    if key in _SOURCE_COMMIT_CACHE:
        return _SOURCE_COMMIT_CACHE[key]
    git = shutil.which("git")
    if git is None:
        return None
    try:
        resolved = subprocess.run(
            [git, "-C", str(root), "rev-parse", "--verify", f"{value}^{{commit}}"],
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    canonical = resolved.stdout.strip()
    if resolved.returncode != 0 or canonical != value or not is_source_commit(canonical):
        return None
    _SOURCE_COMMIT_CACHE[key] = canonical
    return canonical


def resolve_commit(repo_root=None):
    """(commit, dirty) for the working tree, or ('unknown', None) without git.

    ``unknown`` is rejected by ``record.validate_record``: a record whose code
    provenance cannot be established is not accepted.
    """
    root = Path(repo_root or REPO_ROOT)
    git = shutil.which("git")
    if git is None:
        return "unknown", None
    try:
        head = subprocess.run(
            [git, "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
        )
        if head.returncode != 0:
            return "unknown", None
        status = subprocess.run(
            [git, "-C", str(root), "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError):
        return "unknown", None
    dirty = bool(status.stdout.strip()) if status.returncode == 0 else None
    commit = head.stdout.strip()
    return (resolve_source_commit(commit, root) or "unknown"), dirty


class OracleRun:
    """One authoritative execution: what was measured and who measured it."""

    __slots__ = ("measured", "units", "stages")

    def __init__(self, measured, units, stages):
        try:
            measured = canon.normalize(measured)
            units = canon.normalize(units)
            stages = canon.normalize(stages)
        except (TypeError, ValueError) as exc:
            raise OracleError(
                f"oracle returned a non-canonical value: {type(exc).__name__}"
            ) from exc
        if not isinstance(measured, dict) or not measured:
            raise OracleError("oracle returned an empty measurement")
        if not isinstance(units, dict) or not units:
            raise OracleError("oracle returned no units mapping")
        if not isinstance(stages, list) or not stages:
            raise OracleError("oracle returned no executed stages")
        self.measured = measured
        self.units = units
        self.stages = stages


class OracleAdapter:
    """Common surface for every oracle, named runtime or reference."""

    def __init__(self, oracle_id, oracle_type, description, version="1.0.0"):
        self.oracle_id = oracle_id
        self.oracle_type = oracle_type
        self.description = description
        self.version = version

    @property
    def implementation(self):
        raise NotImplementedError

    @property
    def authority(self):
        raise NotImplementedError

    def run(self, family, request):
        raise NotImplementedError


class ReferenceOracle(OracleAdapter):
    """Deterministic in-repo simulator standing in for an absent runtime."""

    def __init__(self, oracle_id, oracle_type, description, fn, requested_runtime, version="1.0.0"):
        super().__init__(oracle_id, oracle_type, description, version)
        self._fn = fn
        self.requested_runtime = requested_runtime

    @property
    def implementation(self):
        return "reference"

    @property
    def authority(self):
        # Deliberately not "measured-runtime". Records carrying this value are
        # refused publication by record.publishability().
        return "reference-simulator"

    def run(self, family, request):
        try:
            measured, units = self._fn(request)
        except Exception as exc:
            # A malformed request — including one assembled from an upstream
            # chain stage that answered in the wrong shape — is an oracle
            # failure, not a crash. The record is dropped.
            raise OracleError(
                f"{self.oracle_id}: could not run on this request: {type(exc).__name__}: {exc}"
            ) from exc
        return OracleRun(
            measured,
            units,
            [
                {
                    "stage": family,
                    "requested_runtime": self.requested_runtime,
                    "implementation": "reference",
                    "oracle_id": self.oracle_id,
                    "version": self.version,
                    "module_digest": module_digest(),
                }
            ],
        )


class ExternalCommandOracle(OracleAdapter):
    """A named runtime bound through the ``sf-oracle/1`` stdin/stdout protocol.

    Request written to stdin::

        {"protocol": "sf-oracle/1", "oracle": "<runtime>",
         "family": "<family>", "request": {...}}

    Response expected on stdout::

        {"protocol": "sf-oracle/1", "runtime_version": "...",
         "runtime_commit": "...", "measured": {...}, "units": {...}}

    Anything else — nonzero exit, timeout, bad JSON, missing field — raises
    ``OracleError``. There is no fallback path.
    """

    def __init__(
        self,
        oracle_id,
        oracle_type,
        description,
        runtime,
        command,
        version="1.0.0",
        timeout_s=DEFAULT_TIMEOUT_S,
    ):
        super().__init__(oracle_id, oracle_type, description, version)
        self.runtime = runtime
        self.requested_runtime = runtime
        self.command = list(command)
        if not self.command or not self.command[0]:
            raise OracleError(f"{runtime}: configured command has no executable")
        self.timeout_s = timeout_s

    @property
    def executable_identity(self):
        """A bounded, non-secret stage identity; arguments are never retained."""
        return Path(self.command[0]).name or self.runtime

    @property
    def implementation(self):
        return "named-runtime"

    @property
    def authority(self):
        return "measured-runtime"

    def run(self, family, request):
        try:
            payload = json.dumps(
                {
                    "protocol": PROTOCOL,
                    "oracle": self.runtime,
                    "family": family,
                    "request": canon.normalize(request),
                },
                sort_keys=True,
                allow_nan=False,
            )
        except (TypeError, ValueError) as exc:
            raise OracleError(
                f"{self.runtime}: request could not be canonicalized: {type(exc).__name__}"
            ) from exc
        returncode, stdout = _run_protocol_command(
            self.command,
            payload.encode("utf-8"),
            self.timeout_s,
            self.runtime,
        )
        if returncode != 0:
            # stderr is controlled by an external process and may echo command
            # arguments or environment secrets.  The status is sufficient for
            # the fail-closed record boundary; operator logs remain external.
            raise OracleError(f"{self.runtime}: configured command exited {returncode}")
        try:
            response = json.loads(
                stdout,
                parse_constant=_reject_json_constant,
            )
            response = canon.normalize(response)
        except (json.JSONDecodeError, RecursionError, TypeError, ValueError) as exc:
            raise OracleError(f"{self.runtime}: response was not JSON: {exc}") from exc
        if not isinstance(response, dict):
            raise OracleError(f"{self.runtime}: response was not a JSON object")
        if response.get("protocol") != PROTOCOL:
            raise OracleError(f"{self.runtime}: protocol mismatch; expected {PROTOCOL}")
        for field in ("runtime_version", "runtime_commit"):
            value = response.get(field)
            if not isinstance(value, str) or not value.strip():
                raise OracleError(f"{self.runtime}: response is missing {field}")
        if not is_runtime_commit(response["runtime_commit"]):
            raise OracleError(
                f"{self.runtime}: runtime_commit must be a resolved 7-64 digit hexadecimal revision"
            )
        return OracleRun(
            response.get("measured"),
            response.get("units", {}),
            [
                {
                    "stage": family,
                    "requested_runtime": self.runtime,
                    "implementation": "named-runtime",
                    "oracle_id": self.oracle_id,
                    "version": response["runtime_version"],
                    "runtime_commit": response["runtime_commit"],
                    "executable": self.executable_identity,
                }
            ],
        )


def _run_protocol_command(command, payload, timeout_s, runtime):
    """Execute one protocol command while bounding both captured streams."""
    deadline = time.monotonic() + float(timeout_s)
    try:
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
        )
    except OSError as exc:
        detail = exc.strerror or type(exc).__name__
        raise OracleError(f"{runtime}: could not execute configured command: {detail}") from exc

    chunks = {"stdout": [], "stderr": []}
    overflow = []
    io_errors = []

    def remaining():
        return max(0.0, deadline - time.monotonic())

    def stop_process():
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except (OSError, ProcessLookupError):
            try:
                process.kill()
            except (OSError, ProcessLookupError):
                pass

    def read_stream(name, stream, limit):
        total = 0
        try:
            while True:
                chunk = stream.read(PROTOCOL_READ_BYTES)
                if not chunk:
                    break
                total += len(chunk)
                if total > limit:
                    overflow.append(name)
                    stop_process()
                    break
                chunks[name].append(chunk)
        except OSError as exc:
            io_errors.append((name, exc))
            stop_process()
        finally:
            stream.close()

    def write_stdin():
        try:
            process.stdin.write(payload)
            process.stdin.close()
        except BrokenPipeError:
            pass
        except OSError as exc:
            io_errors.append(("stdin", exc))
            stop_process()

    threads = [
        threading.Thread(
            target=read_stream,
            args=("stdout", process.stdout, MAX_PROTOCOL_STDOUT_BYTES),
            daemon=True,
        ),
        threading.Thread(
            target=read_stream,
            args=("stderr", process.stderr, MAX_PROTOCOL_STDERR_BYTES),
            daemon=True,
        ),
        threading.Thread(target=write_stdin, daemon=True),
    ]
    for thread in threads:
        thread.start()

    def join_readers(timeout):
        cutoff = time.monotonic() + timeout
        hung = False
        for thread in threads:
            thread.join(timeout=max(0.0, cutoff - time.monotonic()))
            if thread.is_alive():
                hung = True
        return hung

    try:
        returncode = process.wait(timeout=remaining())
    except subprocess.TimeoutExpired as exc:
        stop_process()
        try:
            process.wait(timeout=max(0.05, remaining()))
        except subprocess.TimeoutExpired:
            pass
        join_readers(remaining())
        raise OracleError(f"{runtime}: timed out after {timeout_s}s") from exc
    if join_readers(remaining()):
        stop_process()
        join_readers(max(0.05, remaining()))
        raise OracleError(
            f"{runtime}: timed out after {timeout_s}s waiting for inherited pipes to close"
        )
    if overflow:
        stream = overflow[0]
        limit = MAX_PROTOCOL_STDOUT_BYTES if stream == "stdout" else MAX_PROTOCOL_STDERR_BYTES
        raise OracleError(f"{runtime}: {stream} exceeded the {limit}-byte protocol limit")
    if io_errors:
        stream, exc = io_errors[0]
        detail = exc.strerror or type(exc).__name__
        raise OracleError(f"{runtime}: {stream} I/O failed: {detail}") from exc
    try:
        stdout = b"".join(chunks["stdout"]).decode("utf-8")
    except UnicodeError as exc:
        raise OracleError(f"{runtime}: response was not valid UTF-8") from exc
    return returncode, stdout


class ChainOracle(OracleAdapter):
    """An ordered pipeline of oracles, e.g. limbic-critic -> plasticity-lab.

    Each step is resolved independently, so a deployment that has one of the
    two runtimes bound gets a record whose ``oracle.stages`` says exactly which
    half was measured by the named runtime and which half was the reference.
    """

    def __init__(self, oracle_id, oracle_type, description, steps, version="1.0.0"):
        super().__init__(oracle_id, oracle_type, description, version)
        # steps: [(stage_name, adapter, build_request)]
        self._steps = list(steps)
        self.requested_runtime = [
            getattr(adapter, "requested_runtime", None) for _name, adapter, _build in self._steps
        ]

    @property
    def implementation(self):
        kinds = {adapter.implementation for _n, adapter, _b in self._steps}
        if kinds == {"named-runtime"}:
            return "named-runtime"
        if kinds == {"reference"}:
            return "reference"
        return "mixed"

    @property
    def authority(self):
        if self.implementation == "named-runtime":
            return "measured-runtime"
        if self.implementation == "reference":
            return "reference-simulator"
        return "mixed-reference-and-runtime"

    def run(self, family, request):
        measured = {}
        units = {}
        stages = []
        carried = dict(request)
        for name, adapter, build_request in self._steps:
            try:
                step_request = build_request(carried) if build_request else carried
            except Exception as exc:
                raise OracleError(
                    f"stage {name!r}: the previous stage did not supply what it needs: "
                    f"{type(exc).__name__}: {exc}"
                ) from exc
            step = adapter.run(f"{family}:{name}", step_request)
            measured[name] = step.measured
            units[name] = step.units
            stages.extend(step.stages)
            carried = dict(carried)
            carried[name] = step.measured
        return OracleRun(measured, units, stages)


def probe_runtime(runtime, environ=None):
    """What we can honestly say about a named runtime's availability."""
    env = os.environ if environ is None else environ
    key = env_key(runtime)
    command = env.get(key, "").strip()
    on_path = shutil.which(runtime) is not None
    if command:
        note = f"bound through {key}"
    elif on_path:
        note = (
            f"{runtime} is on PATH but no {PROTOCOL} binding is configured "
            f"({key} is unset); the reference implementation was used instead"
        )
    else:
        note = f"{runtime} is not installed and {key} is unset"
    return {
        "runtime": runtime,
        "binding_env": key,
        "bound": bool(command),
        "on_path": on_path,
        "note": note,
    }


def bind(runtime, oracle_id, oracle_type, description, reference_fn, environ=None):
    """Return the external adapter when bound, else the reference adapter."""
    env = os.environ if environ is None else environ
    key = env_key(runtime)
    command = env.get(key, "").strip()
    if command:
        try:
            argv = shlex.split(command)
        except ValueError as exc:
            raise OracleError(f"{key} contains a malformed command") from exc
        if not argv or not argv[0]:
            raise OracleError(f"{key} contains a command with no executable")
        return ExternalCommandOracle(
            oracle_id=runtime,
            oracle_type=oracle_type,
            description=f"{runtime} via {PROTOCOL}",
            runtime=runtime,
            command=argv,
        )
    return ReferenceOracle(
        oracle_id=oracle_id,
        oracle_type=oracle_type,
        description=description,
        fn=reference_fn,
        requested_runtime=runtime,
    )


def availability_report(runtimes, environ=None):
    """Environment summary for a record or manifest: what was bound, what was not.

    Deliberately free of interpreter or host details. This block is stored in
    every record and compared byte for byte by the golden fixture test, so it
    must describe the oracle binding and nothing about the machine. The code
    identity that actually matters is ``module_digest``.
    """
    diagnostics = [probe_runtime(runtime, environ) for runtime in runtimes]
    # PATH membership and prose diagnostics describe the current host, not the
    # oracle binding contract.  Keep them available through ``probe_runtime``
    # for operators but exclude them from canonical records and manifests.
    probes = [
        {
            "runtime": probe["runtime"],
            "binding_env": probe["binding_env"],
            "bound": probe["bound"],
        }
        for probe in diagnostics
    ]
    return {
        "protocol": PROTOCOL,
        "runtimes": probes,
        "all_bound": all(probe["bound"] for probe in probes),
        "unbound": [probe["runtime"] for probe in probes if not probe["bound"]],
    }
