"""Out-of-band limits attestation and JSON body of the code-repair harness protocol."""

from __future__ import annotations

from typing import Any

from . import vocabulary as cv
from ._contract import bind_import_twin, load_strict_json

LIMITS_ATTESTATION_PREFIX = "code-repair-limits-attestation/1 "
LANDLOCK_ATTESTATION_PREFIX = "code-repair-landlock-attestation/1 "
REPORT_FILENAME = "report.json"
REPORT_FD_ENV = "CODE_REPAIR_REPORT_FD"
_ATTESTATION_PREFIX = LIMITS_ATTESTATION_PREFIX.encode()
_LANDLOCK_ATTESTATION_PREFIX = LANDLOCK_ATTESTATION_PREFIX.encode()
_ATTESTATION_BY_TOKEN = {
    str(True).lower().encode(): True,
    str(False).lower().encode(): False,
}


def limits_attested(stdout: bytes) -> bool | str:
    """Authoritative limits flag from the first stdout line, or why there is none."""

    line, newline, _rest = stdout.partition(b"\n")
    if not stdout:
        return "empty stdout"
    if not newline or not line.startswith(_ATTESTATION_PREFIX):
        return "missing limits attestation line"
    applied = _ATTESTATION_BY_TOKEN.get(line[len(_ATTESTATION_PREFIX):].strip())
    return "limits attestation malformed" if applied is None else applied


def landlock_attested(stdout: bytes) -> str:
    """Immutable Landlock token from the second startup line, or why it is absent."""

    _limits, newline, rest = stdout.partition(b"\n")
    if not newline:
        return "missing landlock attestation line"
    line, newline, _rest = rest.partition(b"\n")
    if not newline or not line.startswith(_LANDLOCK_ATTESTATION_PREFIX):
        return "missing landlock attestation line"
    raw = line[len(_LANDLOCK_ATTESTATION_PREFIX):]
    try:
        token = raw.decode("ascii")
    except UnicodeDecodeError:
        return "landlock attestation malformed"
    if not token or token.strip() != token:
        return "landlock attestation malformed"
    return token


def parsed_report(returncode: int, stdout: bytes, body: bytes) -> dict[str, Any] | str:
    """The protocol object the child wrote, or the reason there is none."""

    if returncode != 0:
        return f"exit status {returncode}"
    attested = limits_attested(stdout)
    if not isinstance(attested, bool):
        return attested
    try:
        parsed = load_strict_json(body.decode("utf-8"))
    except ValueError as exc:
        return f"report unreadable: {exc}"
    if not isinstance(parsed, dict) or parsed.get("protocol") != cv.HARNESS_PROTOCOL:
        return "report is not the protocol"
    parsed["_limits_attested"] = attested
    return parsed


bind_import_twin(__name__)
