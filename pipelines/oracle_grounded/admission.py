#!/usr/bin/env python3
"""Oracle-grounded admission: is this record trustworthy as training data?

Mirrors the code-repair admission shape: technical validity comes from the
shared oracle validator, never from the record's own ``validation`` block, so
a record whose result was edited while retaining an old ``validation`` stamp is
refused rather than admitted. Callers supply the registry row resolved from the
source directory; a row chosen from payload metadata cannot authenticate.

The record's declared verdict is only allowed to say *rejected* when the
family's own invariants fail. Envelope or declared-status disagreement is
corruption, not honest rejection, and raises.

Accepted reference measurements must reproduce exactly using the built-in
oracle. Named or mixed runtime measurements need authenticated replay evidence
from an explicitly invoked runtime gate; metadata admission never launches an
external command. An explicitly scoped native gate replays each accepted native
record using only the executable selected by the caller. Publication remains
a separate gate.
"""

from __future__ import annotations

from typing import Any, Mapping

from . import admission_checks as _checks
from . import refusals
from .import_twins import bind_import_twin

__all__ = ["OracleAdmissionError", "natural_eligibility", "row_findings"]

_FINDING_CODES = frozenset({
    "ORACLE_ROUTE_UNAUTHORIZED",
    "ORACLE_FAMILY_MISMATCH",
    "ORACLE_GENERATOR_MISMATCH",
    "ORACLE_VALIDATION_INVALID",
})


class OracleAdmissionError(refusals.CodedRefusal):
    """A record that must be excluded, not merely marked ineligible."""

    CODES = _FINDING_CODES


_refuse, _refuse_when, _refuse_first = refusals.helpers(OracleAdmissionError)


row_findings = _checks.row_findings


def _measurement_eligibility(record: Mapping[str, Any]) -> tuple[bool, tuple[str, ...]]:
    """Replay native measurements only under explicit caller authority."""
    if record["oracle"]["implementation"] == "reference":
        return True, ()
    from . import native_gate, record as oracle_record

    environment = native_gate.replay_environ()
    if (record["oracle"]["implementation"] != "named-runtime"
            or environment is None or not native_gate.is_native_record(record)):
        return False, ("authenticated runtime replay required",)
    try:
        status, detail = oracle_record.reproduce(record, environ=environment)
    except Exception as exc:  # untrusted records must never bypass admission
        _refuse("ORACLE_VALIDATION_INVALID", f"native replay raised {type(exc).__name__}")
    if status != "reproduced":
        _refuse("ORACLE_VALIDATION_INVALID", f"native replay {status}: {detail}")
    return True, ()


def _require_consistent_validation(record: Mapping[str, Any]) -> None:
    """Refuse envelope corruption or a verdict contradicted by measured content."""
    from . import record as oracle_record

    try:
        layers = oracle_record.classify(record, check_declared_status=True)
    except Exception as exc:  # final boundary around one untrusted record
        _refuse(
            "ORACLE_VALIDATION_INVALID",
            f"oracle validation raised {type(exc).__name__}",
        )
    if layers["envelope"]:
        _refuse(
            "ORACLE_VALIDATION_INVALID",
            "envelope findings: " + "; ".join(layers["envelope"]),
        )
    if layers["status"]:
        _refuse(
            "ORACLE_VALIDATION_INVALID",
            "declared status disagrees with recomputed status: "
            + "; ".join(layers["status"]),
        )


def _ineligible_reasons(validation: Mapping[str, Any]) -> tuple[str, ...]:
    reason = validation.get("publishable_reason")
    if isinstance(reason, str) and reason:
        return (reason,)
    stored = validation.get("reasons")
    reasons = tuple(str(item) for item in stored) if isinstance(stored, list) else ()
    return reasons or ("ORACLE_NATURALLY_INELIGIBLE",)


def natural_eligibility(record: Any, row: Any) -> tuple[bool, tuple[str, ...]]:
    """Technical eligibility for one oracle record; raises for corrupt evidence.

    Eligibility is recomputed from the record's measured content via
    ``record.classify``. The stored ``validation`` block is never trusted for
    the decision; it is only cross-checked for disagreement.
    """
    if not isinstance(record, Mapping):
        _refuse("ORACLE_VALIDATION_INVALID", "record must be a JSON object")
    findings = row_findings(row) + _checks.factory_findings(record, row)
    findings += _checks.generator_findings(record)
    for code, message in findings:
        _refuse(code, message)

    _require_consistent_validation(record)

    validation = record.get("validation")
    if not isinstance(validation, Mapping):
        _refuse("ORACLE_VALIDATION_INVALID", "missing validation block")
    if validation.get("status") != "accepted" or validation.get("publishable") is not True:
        return False, _ineligible_reasons(validation)
    return _measurement_eligibility(record)


bind_import_twin(__name__)
