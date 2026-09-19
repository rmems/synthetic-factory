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

# Exact diagnostic pairs emitted by the reviewed adapters.
# They preserve observations across package installation/removal only while
# the current probe still refuses execution. A code alone grants no authority.
_REVIEWED_UNAVAILABLE_DIAGNOSTICS = {
    "nir_rs": (
        ("RUNTIME_NOT_INSTALLED",
         "nir_rs is not installed in this environment; the authority-contract oracle for this family"),
        ("RUNTIME_ADAPTER_NOT_IMPLEMENTED",
         "'nir-rs' is on PATH but this repository ships no adapter for it; the authority-contract oracle for this family"),
        ("RUNTIME_PROBE_FAILED",
         "a nir_rs executable was found but its availability handshake failed; the authority-contract oracle for this family"),
        ("RUNTIME_CONTRACT_MISMATCH",
         "a nir_rs executable was found but declares conventions or coverage outside the documented adapter contract; the authority-contract oracle for this family"),
    ),
    "nir_python": (
        ("RUNTIME_NOT_INSTALLED",
         "nir_python is not installed in this environment; reference NIR serialization library"),
        ("RUNTIME_ADAPTER_NOT_IMPLEMENTED",
         "the 'nir' package is importable but this repository ships no adapter for it; reference NIR serialization library"),
    ),
    "nirtorch_snntorch": (
        ("RUNTIME_NOT_INSTALLED",
         "nirtorch_snntorch is not installed in this environment; upstream-compatible execution backend"),
        ("RUNTIME_ADAPTER_NOT_IMPLEMENTED",
         "the 'snntorch' package is importable but this repository ships no adapter for it; upstream-compatible execution backend"),
    ),
}


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
        errors += _runtime_entry_errors(entry, where)
    return errors


def _runtime_entry_errors(entry, where):
    if not isinstance(entry, dict):
        return [f"{where}: every runtime entry must be an object"]
    name = entry.get("runtime")
    label = f"{where}.oracle.runtimes[{name!r}]"
    expected_runtime = _ALL_RUNTIME_BY_NAME.get(name) if isinstance(name, str) else None
    if expected_runtime is None:
        return [
            f"{label}: runtime is outside the declared inventory "
            "[RUNTIME_STATUS_UNKNOWN]"
        ]
    errors = _runtime_identity_errors(entry, expected_runtime, label)
    errors += _runtime_status_errors(entry, label)
    errors += _runtime_probe_errors(entry, expected_runtime, label)
    return errors


# Reviewed stub-era declarations. Before `nir_rs` had a real adapter its
# entries recorded the stub's empty contract; those records remain intact
# evidence while the runtime is still unavailable, but only in that state.
_REVIEWED_LEGACY_DECLARATIONS = {
    "nir_rs": ({}, []),
}


def _runtime_identity_errors(entry, expected_runtime, label):
    """The entry's identity fields must be the selected implementation's."""
    errors = []
    expected_class = expected_runtime.runtime_class
    if entry.get("runtime_class") != expected_class:
        errors.append(
            f"{label}: runtime_class must be {expected_class!r}, got "
            f"{entry.get('runtime_class')!r} [RUNTIME_STATUS_UNKNOWN]"
        )
    legacy = _REVIEWED_LEGACY_DECLARATIONS.get(entry.get("runtime"))
    allow_legacy = entry.get("status") == STATUS_UNAVAILABLE and legacy is not None
    expected_conventions = dict(getattr(expected_runtime, "conventions", {}))
    if entry.get("conventions") != expected_conventions and not (
        allow_legacy and entry.get("conventions") == legacy[0]
    ):
        errors.append(
            f"{label}: conventions do not match the selected runtime implementation "
            "[COMPARISON_MISMATCH]"
        )
    expected_supported = list(getattr(expected_runtime, "supported_types", ()))
    if entry.get("supported_types") != expected_supported and not (
        allow_legacy and entry.get("supported_types") == legacy[1]
    ):
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
        errors += _nonexecuted_status_errors(entry, label)
    if entry.get("status") == STATUS_EXECUTED:
        errors += _executed_status_errors(entry, label)
    return errors


def _nonempty_text(value):
    return isinstance(value, str) and bool(value.strip())


def _nonexecuted_status_errors(entry, label):
    """Nonexecution forbids outputs and requires a textual diagnostic."""
    errors = []
    if entry.get("outputs") is not None or entry.get("output_digest") is not None:
        errors.append(
            f"{label}: a runtime that did not execute must not carry outputs "
            "[UNAVAILABLE_RUNTIME_HAS_OUTPUT]"
        )
    if not _nonempty_text(entry.get("reason_code")):
        errors.append(
            f"{label}: a runtime that did not execute needs a reason code "
            "[RUNTIME_STATUS_UNKNOWN]"
        )
    if not _nonempty_text(entry.get("detail")):
        errors.append(
            f"{label}: a runtime that did not execute needs a finite text "
            "diagnostic [ENVELOPE_MALFORMED]"
        )
    return errors


def _executed_status_errors(entry, label):
    """An executed claim must carry outputs and stay falsifiable."""
    errors = []
    errors += _executed_output_errors(entry.get("outputs"), label)
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


def _executed_output_errors(outputs, label):
    errors = []
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
    if not _well_formed_availability(availability, available):
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


def _well_formed_availability(availability, available):
    return isinstance(availability, dict) and isinstance(available, bool)


def _unavailable_probe_errors(entry, availability, label):
    """Retain historical diagnostics while the runtime still cannot execute."""
    errors = []
    if entry.get("status") != STATUS_UNAVAILABLE:
        errors.append(
            f"{label}: unavailable runtime cannot be re-executed, so it must "
            f"be recorded as {STATUS_UNAVAILABLE!r}, not "
            f"{entry.get('status')!r} [RUNTIME_STATUS_UNKNOWN]"
        )
    errors += _unavailable_reason_errors(entry, availability, label)
    if entry.get("roundtrip") is not None:
        errors.append(
            f"{label}: an unavailable runtime cannot claim parse/write evidence "
            "[RUNTIME_STATUS_UNKNOWN]"
        )
    return errors


def _unavailable_reason_errors(entry, availability, label):
    """Bind the complete diagnostic to the current probe or reviewed adapter history."""
    errors = []
    expected_reason = availability.get("reason_code")
    if expected_reason not in UNAVAILABLE_REASON_CODES:
        errors.append(
            f"{label}: runtime probe returned unsupported reason_code "
            f"{expected_reason!r} [RUNTIME_STATUS_UNKNOWN]"
        )
    if entry.get("reason_code") not in UNAVAILABLE_REASON_CODES:
        errors.append(
            f"{label}: unavailable reason_code {entry.get('reason_code')!r} is unsupported "
            "[RUNTIME_STATUS_UNKNOWN]"
        )
    errors += _unavailable_diagnostic_errors(entry, availability, label)
    return errors


def _unavailable_diagnostic_errors(entry, availability, label):
    if not _nonempty_text(availability.get("detail")):
        return [
            f"{label}: runtime probe returned a missing or malformed diagnostic "
            "[RUNTIME_STATUS_UNKNOWN]"
        ]
    recorded = (entry.get("reason_code"), entry.get("detail"))
    current = (availability.get("reason_code"), availability.get("detail"))
    reviewed = _REVIEWED_UNAVAILABLE_DIAGNOSTICS.get(entry.get("runtime"), ())
    if recorded == current or recorded in reviewed:
        return []
    return [
        f"{label}: unavailable diagnostic does not match the current probe or "
        "reviewed history for this runtime [RUNTIME_STATUS_UNKNOWN]"
    ]


if __package__:
    _expose_package_sibling(__name__)
