"""Pure procedural source admission, not a replay or publication certificate.

Only accepted, technically validated records are training candidates. Natural
rejections remain evidence; corrupt evidence raises. Publication additionally
requires the separate fresh replay and actual round-completion gate.
"""
from __future__ import annotations

from typing import Any

from . import _admission_catalog as _catalog
from . import _admission_evidence as _evidence
from . import catalog as cat
from . import source_policy as sp
from ._contract import bind_import_twin, oc

__all__ = ["load_trusted_catalog", "validate_source_route", "natural_eligibility"]


_row_findings = _evidence.row_findings
_factory_matches = _evidence.factory_matches
_generator_matches = _evidence.generator_matches
_payload_findings = _evidence.payload_findings
_source_findings = _evidence.source_findings
_record_findings = _evidence.record_findings
_catalog_snapshot = _catalog.catalog_snapshot
_verify_catalog_bytes = _catalog.verify_catalog_bytes
_copy_catalog = _catalog.copy_catalog
_bound_catalog = _catalog.bound_catalog


def load_trusted_catalog(row: Any = None) -> cat.Catalog:
    """Load the sealed vendored catalog; caller paths never supply authority.

    Every call rechecks current file bytes. The cached parsed snapshot is kept
    private; callers receive independent copies so mutations cannot change it.
    """
    return _catalog.load_trusted_catalog(row)


def validate_source_route(
    record: Any, row: Any, *, catalog: cat.Catalog | None = None,
) -> list[str]:
    """Check reviewed row, generator and source identity; never execute programs.

    The caller resolves the row from the actual source directory. This API has
    no path argument and cannot authenticate a row chosen from payload metadata.
    Full technical validation belongs to the shared family validator below.
    """
    try:
        trusted = _bound_catalog(row, catalog)
    except sp.SourcePolicyError as exc:
        return [str(exc)]
    return _record_findings(record, row, trusted)


def natural_eligibility(
    record: Any, row: Any, *, catalog: cat.Catalog | None = None,
) -> tuple[bool, tuple[str, ...]]:
    """Return eligibility/reasons for valid evidence; raise for corrupt evidence.

    This proves pure technical/policy eligibility only. It cannot establish that
    replay just ran, a round was completed, or anything was published/trained.
    """
    from .validation import validate_record
    from .run_validation import record_identity_matches
    trusted = _bound_catalog(row, catalog)
    findings = _record_findings(record, row, trusted)
    findings += validate_record(record, "record", catalog=trusted)
    if findings:
        raise sp.SourcePolicyError("; ".join(findings))
    if not record_identity_matches(record, trusted):
        raise sp.SourcePolicyError("PROCEDURAL_RECORD_IDENTITY_MISMATCH")
    result = record["result"]
    if (result["outcome"], result["oracle_status"]) == ("accepted", "validated"):
        eligible, reasons = oc.curation_eligible(record, findings)
        return eligible, tuple(reasons)
    return False, tuple(result["reason_codes"]) or ("PROCEDURAL_NATURALLY_INELIGIBLE",)


bind_import_twin(__name__)
