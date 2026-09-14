#!/usr/bin/env python3
"""Do the recorded runtime entries match the runtimes this repository has?

Identity, status, and a fresh probe. An `executed` claim naming a runtime this
validator cannot re-execute is rejected as unfalsifiable, not merely
unverified.
"""

from __future__ import annotations

import sys

if __package__:
    # Import-twin helpers join the package import lock; import-order tests cover this edge.
    from . import _assert_direct_sibling, _expose_package_sibling  # pylint: disable=cyclic-import

    _assert_direct_sibling("nir_equivalence_validate_runtimes")
    from .nir_equivalence_runtimes import (  # noqa: E402
        EXPECTED_RUNTIME_NAMES,
        _ALL_RUNTIME_BY_NAME,
        _RUNTIME_BY_NAME,
    )
    from .nir_equivalence_terms import (  # noqa: E402
        RUNTIME_STATUSES,
        STATUS_EXECUTED,
        STATUS_UNAVAILABLE,
        STATUS_UNSUPPORTED,
        UNAVAILABLE_REASON_CODES,
    )
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "nir_equivalence_validate_runtimes"
    )
    from nir_equivalence_runtimes import (  # noqa: E402
        EXPECTED_RUNTIME_NAMES,
        _ALL_RUNTIME_BY_NAME,
        _RUNTIME_BY_NAME,
    )
    from nir_equivalence_terms import (  # noqa: E402
        RUNTIME_STATUSES,
        STATUS_EXECUTED,
        STATUS_UNAVAILABLE,
        STATUS_UNSUPPORTED,
        UNAVAILABLE_REASON_CODES,
    )

def _check_runtimes(record, where):
    errors = []
    runtimes = ((record.get("oracle") or {}).get("runtimes")) or []
    if not isinstance(runtimes, list) or not runtimes:
        return [f"{where}: oracle.runtimes must be a non-empty array [ENVELOPE_MALFORMED]"]
    names = [
        entry.get("runtime") if isinstance(entry, dict) else None for entry in runtimes
    ]
    if names != list(EXPECTED_RUNTIME_NAMES):
        errors.append(
            f"{where}: oracle.runtimes must contain the complete ordered inventory "
            f"{list(EXPECTED_RUNTIME_NAMES)!r}, got {names!r} "
            "[RUNTIME_STATUS_UNKNOWN]"
        )
    for entry in runtimes:
        name = entry.get("runtime") if isinstance(entry, dict) else None
        label = f"{where}.oracle.runtimes[{name!r}]"
        if not isinstance(entry, dict):
            errors.append(f"{where}: every runtime entry must be an object")
            continue
        expected_runtime = (
            _ALL_RUNTIME_BY_NAME.get(name) if isinstance(name, str) else None
        )
        if expected_runtime is None:
            errors.append(
                f"{label}: runtime is outside the declared inventory "
                "[RUNTIME_STATUS_UNKNOWN]"
            )
            continue
        errors += _runtime_identity_errors(entry, expected_runtime, label)
        errors += _runtime_status_errors(entry, label)
        errors += _runtime_probe_errors(entry, expected_runtime, label)
    return errors


def _runtime_identity_errors(entry, expected_runtime, label):
    """The entry's identity fields must be the selected implementation's."""
    errors = []
    expected_class = expected_runtime.runtime_class
    if entry.get("runtime_class") != expected_class:
        errors.append(
            f"{label}: runtime_class must be {expected_class!r}, got "
            f"{entry.get('runtime_class')!r} [RUNTIME_STATUS_UNKNOWN]"
        )
    expected_conventions = dict(getattr(expected_runtime, "conventions", {}))
    if entry.get("conventions") != expected_conventions:
        errors.append(
            f"{label}: conventions do not match the selected runtime implementation "
            "[COMPARISON_MISMATCH]"
        )
    expected_supported = list(getattr(expected_runtime, "supported_types", ()))
    if entry.get("supported_types") != expected_supported:
        errors.append(
            f"{label}: supported_types do not match the selected runtime "
            "implementation [COMPARISON_MISMATCH]"
        )
    return errors


def _runtime_status_errors(entry, label):
    """What the declared status obliges the entry to carry (or not carry)."""
    errors = []
    if entry.get("status") not in RUNTIME_STATUSES:
        errors.append(
            f"{label}: status must be one of {list(RUNTIME_STATUSES)} "
            "[RUNTIME_STATUS_UNKNOWN]"
        )
    if entry.get("status") in (STATUS_UNAVAILABLE, STATUS_UNSUPPORTED):
        if entry.get("outputs") is not None or entry.get("output_digest") is not None:
            errors.append(
                f"{label}: a runtime that did not execute must not carry outputs "
                "[UNAVAILABLE_RUNTIME_HAS_OUTPUT]"
            )
        if not isinstance(entry.get("reason_code"), str) or not entry[
            "reason_code"
        ].strip():
            errors.append(
                f"{label}: a runtime that did not execute needs a reason code "
                "[RUNTIME_STATUS_UNKNOWN]"
            )
        if not isinstance(entry.get("detail"), str) or not entry["detail"].strip():
            errors.append(
                f"{label}: a runtime that did not execute needs a finite text "
                "diagnostic [ENVELOPE_MALFORMED]"
            )
    if entry.get("status") == STATUS_EXECUTED:
        errors += _executed_status_errors(entry, label)
    return errors


def _executed_status_errors(entry, label):
    """An executed claim must carry outputs and stay falsifiable."""
    errors = []
    outputs = entry.get("outputs")
    if not isinstance(outputs, dict):
        errors.append(f"{label}: an executed runtime must carry outputs")
    else:
        missing = [
            key
            for key in ("output_trace", "spike_events", "spike_count")
            if key not in outputs
        ]
        if missing:
            errors.append(
                f"{label}: executed outputs are missing {missing} "
                "[ENVELOPE_MALFORMED]"
            )
    if not entry.get("output_digest"):
        errors.append(f"{label}: an executed runtime must carry an output digest")
    # An `executed` claim naming a runtime this validator cannot
    # re-execute is unfalsifiable. Without this, a record could name
    # nir_rs -- which is not installed -- as having produced a trace,
    # and nothing downstream would contradict it.
    if entry.get("runtime") not in _RUNTIME_BY_NAME:
        errors.append(
            f"{label}: only runtimes this validator can re-execute may be "
            f"marked {STATUS_EXECUTED!r}; {entry.get('runtime')!r} is not one "
            f"of {sorted(_RUNTIME_BY_NAME)} [RUNTIME_STATUS_UNKNOWN]"
        )
    return errors


def _runtime_probe_errors(entry, expected_runtime, label):
    """Replay the availability probe and hold the entry to what it says."""
    try:
        availability = expected_runtime.availability()
    except Exception as exc:  # noqa: BLE001 - adapter failures are local findings
        return [
            f"{label}: runtime availability probe failed locally: {exc} "
            "[RUNTIME_STATUS_UNKNOWN]"
        ]
    available = availability.get("available") if isinstance(availability, dict) else None
    if not isinstance(availability, dict) or (
        available is not True and available is not False
    ):
        return [
            f"{label}: runtime availability probe returned a malformed capability "
            "[RUNTIME_STATUS_UNKNOWN]"
        ]
    if available is False:
        return _unavailable_probe_errors(entry, availability, label)
    # The probe says the runtime is here, so the entry cannot keep calling it
    # absent: a stale `unavailable` would suppress an authoritative runtime's
    # evidence and carry ORACLE_UNAVAILABLE for a runtime that can execute.
    if entry.get("status") == STATUS_UNAVAILABLE:
        return [
            f"{label}: runtime probe reports available, so the entry cannot be "
            f"recorded as {STATUS_UNAVAILABLE!r} [RUNTIME_STATUS_UNKNOWN]"
        ]
    return []


def _unavailable_probe_errors(entry, availability, label):
    """An unavailable probe pins the entry's status, reason, and detail."""
    errors = []
    if entry.get("status") != STATUS_UNAVAILABLE:
        errors.append(
            f"{label}: unavailable runtime must be recorded as "
            f"{STATUS_UNAVAILABLE!r}, not {entry.get('status')!r} "
            "[RUNTIME_STATUS_UNKNOWN]"
        )
    expected_reason = availability.get("reason_code")
    if expected_reason not in UNAVAILABLE_REASON_CODES:
        errors.append(
            f"{label}: runtime probe returned unsupported reason_code "
            f"{expected_reason!r} [RUNTIME_STATUS_UNKNOWN]"
        )
    elif entry.get("reason_code") != expected_reason:
        errors.append(
            f"{label}: unavailable reason_code {entry.get('reason_code')!r} "
            f"does not match the runtime probe {expected_reason!r} "
            "[RUNTIME_STATUS_UNKNOWN]"
        )
    expected_detail = availability.get("detail")
    if entry.get("detail") != expected_detail:
        errors.append(
            f"{label}: unavailable diagnostic detail does not match the "
            "runtime probe [RUNTIME_STATUS_UNKNOWN]"
        )
    if entry.get("roundtrip") is not None:
        errors.append(
            f"{label}: an unavailable runtime cannot claim parse/write evidence "
            "[RUNTIME_STATUS_UNKNOWN]"
        )
    return errors


if __package__:
    _expose_package_sibling(__name__)
