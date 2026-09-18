"""Oracle chaining, runtime probing, and binding selection."""

import os
import shlex
import shutil

from .oracle_adapters import ExternalCommandOracle, OracleAdapter, OracleRun, ReferenceOracle
from .oracle_core import PROTOCOL, OracleError, env_key

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

