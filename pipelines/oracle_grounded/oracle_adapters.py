"""Reference and external-command oracle adapter implementations."""

import json
from dataclasses import dataclass
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


@dataclass(frozen=True)
class OracleIdentity:
    """The static identity every adapter stamps into its oracle block."""

    oracle_id: str
    oracle_type: str
    description: str
    version: str = "1.0.0"


def _require_payload(value, kind, message):
    if not isinstance(value, kind) or not value:
        raise OracleError(message)


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
        _require_payload(measured, dict, "oracle returned an empty measurement")
        _require_payload(units, dict, "oracle returned no units mapping")
        _require_payload(stages, list, "oracle returned no executed stages")
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

    def _request_payload(self, family, request):
        try:
            return json.dumps(
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

    def _parse_response(self, stdout):
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
        return response

    def _require_identity_fields(self, response):
        for field in ("runtime_version", "runtime_commit"):
            value = response.get(field)
            if not isinstance(value, str) or not value.strip():
                raise OracleError(f"{self.runtime}: response is missing {field}")

    def _require_protocol_fields(self, response):
        if response.get("protocol") != PROTOCOL:
            raise OracleError(f"{self.runtime}: protocol mismatch; expected {PROTOCOL}")
        self._require_identity_fields(response)
        if not is_runtime_commit(response["runtime_commit"]):
            raise OracleError(
                f"{self.runtime}: runtime_commit must be a resolved 7-64 digit hexadecimal revision"
            )

    def _stage_entry(self, family, response):
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
        payload = self._request_payload(family, request)
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
        response = self._parse_response(stdout)
        self._require_protocol_fields(response)
        return OracleRun(
            response.get("measured"),
            response.get("units", {}),
            [self._stage_entry(family, response)],
        )
