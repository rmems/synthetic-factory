"""Reference and external-command oracle adapter implementations."""

import json
from pathlib import Path

from . import canon, oracle_protocol
from .oracle_core import (
    DEFAULT_TIMEOUT_S,
    PROTOCOL,
    OracleError,
    _parse_finite_json_float,
    _reject_duplicate_object_keys,
    _reject_json_constant,
    is_runtime_commit,
    module_digest,
)
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
        returncode, stdout = oracle_protocol._run_protocol_command(
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
                object_pairs_hook=_reject_duplicate_object_keys,
                parse_constant=_reject_json_constant,
                parse_float=_parse_finite_json_float,
            )
            response = canon.normalize(response)
        except (RecursionError, TypeError, ValueError) as exc:
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
