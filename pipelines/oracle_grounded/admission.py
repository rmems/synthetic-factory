#!/usr/bin/env python3
"""Pure oracle-grounded admission: is this record trustworthy as training data?

Mirrors the code-repair admission shape: technical validity comes from the
shared oracle validator, never from the record's own ``validation`` block, so
a record whose result was edited while retaining an old ``validation`` stamp is
refused rather than admitted. Callers supply the registry row resolved from the
source directory; a row chosen from payload metadata cannot authenticate.

The record's declared verdict is only allowed to say *rejected* when the
family's own invariants fail. Envelope or declared-status disagreement is
corruption, not honest rejection, and raises.

Publication/replay is a separate gate: this proves technical admission only.
"""

from __future__ import annotations

from typing import Any, Mapping

from . import generators, refusals, source_policy

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


def row_findings(row: Any) -> list[tuple[str, str]]:
    """Whether the resolved row is the one sealed oracle authority."""
    expected = source_policy.reviewed_row()
    expected["record_kinds"] = frozenset(expected["record_kinds"])
    expected["allowed_curation_lanes"] = tuple(expected["allowed_curation_lanes"])
    actual = {key: getattr(row, key, object()) for key in expected}
    authorized = getattr(row, "identity_authoritative", None) is True
    if not authorized or actual != expected:
        return [
            ("ORACLE_ROUTE_UNAUTHORIZED", "row differs from sealed source authority")
        ]
    # The row repeating the sealed digests proves nothing about the installed
    # bytes, so the reviewed generation semantics are recomputed here too.
    try:
        source_policy.verify_source_bytes()
    except source_policy.SourcePolicyError as exc:
        return [("ORACLE_ROUTE_UNAUTHORIZED", str(exc))]
    return []


def _factory_findings(record: Mapping[str, Any], row: Any) -> list[tuple[str, str]]:
    """A path-selected row must not authorize a payload naming another factory."""
    if row is None:
        # No authorized oracle row resolves for this path; ``row_findings``
        # already reports ORACLE_ROUTE_UNAUTHORIZED, and there is no row
        # payload_factory to contradict. Refusing is fail-closed either way.
        return []
    meta = record.get("meta")
    if isinstance(meta, Mapping) and meta.get("factory") not in (None, row.payload_factory):
        return [
            (
                "ORACLE_FAMILY_MISMATCH",
                "payload meta.factory contradicts the source route",
            )
        ]
    return []


def _generator_findings(record: Mapping[str, Any]) -> list[tuple[str, str]]:
    generator = record.get("generator")
    if not isinstance(generator, Mapping):
        return [("ORACLE_GENERATOR_MISMATCH", "generator must be an object")]
    if generator.get("authoritative") is not False:
        return [("ORACLE_GENERATOR_MISMATCH", "generator must not be authoritative")]
    if generator.get("name") != generators.GENERATOR_NAME:
        return [
            (
                "ORACLE_GENERATOR_MISMATCH",
                "generator is not the reviewed implementation",
            )
        ]
    if generator.get("version") != generators.GENERATOR_VERSION:
        return [
            (
                "ORACLE_GENERATOR_MISMATCH",
                "generator version is not the reviewed version",
            )
        ]
    return []


def natural_eligibility(record: Any, row: Any) -> tuple[bool, tuple[str, ...]]:
    """Technical eligibility for one oracle record; raises for corrupt evidence.

    Eligibility is recomputed from the record's measured content via
    ``record.classify``. The stored ``validation`` block is never trusted for
    the decision; it is only cross-checked for disagreement.
    """
    from . import record as oracle_record

    if not isinstance(record, Mapping):
        _refuse("ORACLE_VALIDATION_INVALID", "record must be a JSON object")
    findings = row_findings(row) + _factory_findings(record, row)
    findings += _generator_findings(record)
    for code, message in findings:
        _refuse(code, message)

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

    validation = record.get("validation")
    if not isinstance(validation, Mapping):
        _refuse("ORACLE_VALIDATION_INVALID", "missing validation block")
    if validation.get("status") != "accepted" or validation.get("publishable") is not True:
        reasons = validation.get("publishable_reason")
        if not isinstance(reasons, str) or not reasons:
            stored = validation.get("reasons")
            reasons_list = [str(item) for item in stored] if isinstance(stored, list) else []
        else:
            reasons_list = [reasons]
        return False, tuple(reasons_list) or ("ORACLE_NATURALLY_INELIGIBLE",)
    return True, ()


from .import_twins import bind_import_twin

bind_import_twin(__name__)