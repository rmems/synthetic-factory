"""Oracle adapters: who measured, and under which authority.

Three shapes of oracle sit behind one adapter surface. ``ReferenceOracle``
runs the deterministic in-repo simulator and says so; ``ExternalCommandOracle``
speaks ``sf-oracle/1`` to a bound named runtime and never falls back; and
``ChainOracle`` runs an ordered pipeline of the other two, attributing each
stage separately. ``OracleRun`` is the only way a measurement leaves an
adapter, and it refuses non-canonical or empty results outright.
"""

import json
from dataclasses import dataclass
from pathlib import Path

from . import canon
from .oracle_protocol import (
    DEFAULT_TIMEOUT_S,
    PROTOCOL,
    OracleError,
    _parse_finite_json_float,
    _reject_duplicate_object_keys,
    _reject_json_constant,
    _run_protocol_command,
)
from .oracle_provenance import is_runtime_commit, module_digest


@dataclass(frozen=True)
class OracleIdentity:
    """The stable, non-secret identity an adapter stamps into stages."""

    oracle_id: str
    oracle_type: str
    description: str
    version: str = "1.0.0"


def _canonical_run_parts(measured, units, stages):
    try:
        return canon.normalize(measured), canon.normalize(units), canon.normalize(stages)
    except (TypeError, ValueError) as exc:
        raise OracleError(
            f"oracle returned a non-canonical value: {type(exc).__name__}"
        ) from exc


def _is_nonempty_dict(value):
    return isinstance(value, dict) and bool(value)


def _is_nonempty_list(value):
    return isinstance(value, list) and bool(value)


def _require_run_shape(measured, units, stages):
    if not _is_nonempty_dict(measured):
        raise OracleError("oracle returned an empty measurement")
    if not _is_nonempty_dict(units):
        raise OracleError("oracle returned no units mapping")
    if not _is_nonempty_list(stages):
        raise OracleError("oracle returned no executed stages")


class OracleRun:
    """One authoritative execution: what was measured and who measured it."""

    __slots__ = ("measured", "units", "stages")

    def __init__(self, measured, units, stages):
        measured, units, stages = _canonical_run_parts(measured, units, stages)
        _require_run_shape(measured, units, stages)
        self.measured = measured
        self.units = units
        self.stages = stages


class OracleAdapter:
    """Common surface for every oracle, named runtime or reference."""

    def __init__(self, identity):
        self.oracle_id = identity.oracle_id
        self.oracle_type = identity.oracle_type
        self.description = identity.description
        self.version = identity.version

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

    def __init__(self, identity, fn, requested_runtime):
        super().__init__(identity)
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


def _is_nonblank_string(value):
    return isinstance(value, str) and bool(value.strip())


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

    def __init__(self, identity, runtime, command, timeout_s=DEFAULT_TIMEOUT_S):
        super().__init__(identity)
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

    def _encoded_payload(self, family, request):
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
        return payload.encode("utf-8")

    def _decoded_response(self, stdout):
        try:
            response = json.loads(
                stdout,
                object_pairs_hook=_reject_duplicate_object_keys,
                parse_constant=_reject_json_constant,
                parse_float=_parse_finite_json_float,
            )
            response = canon.normalize(response)
        except (json.JSONDecodeError, RecursionError, TypeError, ValueError) as exc:
            raise OracleError(f"{self.runtime}: response was not JSON: {exc}") from exc
        if not isinstance(response, dict):
            raise OracleError(f"{self.runtime}: response was not a JSON object")
        return response

    def _require_protocol_fields(self, response):
        if response.get("protocol") != PROTOCOL:
            raise OracleError(f"{self.runtime}: protocol mismatch; expected {PROTOCOL}")
        for field in ("runtime_version", "runtime_commit"):
            if not _is_nonblank_string(response.get(field)):
                raise OracleError(f"{self.runtime}: response is missing {field}")
        if not is_runtime_commit(response["runtime_commit"]):
            raise OracleError(
                f"{self.runtime}: runtime_commit must be a resolved 7-64 digit hexadecimal revision"
            )

    def _stage_block(self, family, response):
        return {
            "stage": family,
            "requested_runtime": self.runtime,
            "implementation": "named-runtime",
            "oracle_id": self.oracle_id,
            "version": response["runtime_version"],
            "runtime_commit": response["runtime_commit"],
            "executable": self.executable_identity,
        }

    def run(self, family, request):
        payload = self._encoded_payload(family, request)
        returncode, stdout = _run_protocol_command(
            self.command,
            payload,
            self.timeout_s,
            self.runtime,
        )
        if returncode != 0:
            # stderr is controlled by an external process and may echo command
            # arguments or environment secrets.  The status is sufficient for
            # the fail-closed record boundary; operator logs remain external.
            raise OracleError(f"{self.runtime}: configured command exited {returncode}")
        response = self._decoded_response(stdout)
        self._require_protocol_fields(response)
        return OracleRun(
            response.get("measured"),
            response.get("units", {}),
            [self._stage_block(family, response)],
        )


class ChainOracle(OracleAdapter):
    """An ordered pipeline of oracles, e.g. limbic-critic -> plasticity-lab.

    Each step is resolved independently, so a deployment that has one of the
    two runtimes bound gets a record whose ``oracle.stages`` says exactly which
    half was measured by the named runtime and which half was the reference.
    """

    def __init__(self, identity, steps):
        super().__init__(identity)
        # steps: [(stage_name, adapter, build_request)]
        self._steps = list(steps)
        self.requested_runtime = [
            getattr(adapter, "requested_runtime", None) for _name, adapter, _build in self._steps
        ]

    @property
    def steps(self):
        """The resolved chain, read-only; stage validation introspects this."""
        return tuple(self._steps)

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

    def _step_request(self, name, build_request, carried):
        if not build_request:
            return carried
        try:
            return build_request(carried)
        except Exception as exc:
            raise OracleError(
                f"stage {name!r}: the previous stage did not supply what it needs: "
                f"{type(exc).__name__}: {exc}"
            ) from exc

    def run(self, family, request):
        measured = {}
        units = {}
        stages = []
        carried = dict(request)
        for name, adapter, build_request in self._steps:
            step_request = self._step_request(name, build_request, carried)
            step = adapter.run(f"{family}:{name}", step_request)
            measured[name] = step.measured
            units[name] = step.units
            stages.extend(step.stages)
            carried = dict(carried)
            carried[name] = step.measured
        return OracleRun(measured, units, stages)
