"""Pure procedural source admission, not a replay or publication certificate.

Only accepted, technically validated records are training candidates. Natural
rejections remain evidence; corrupt evidence raises. Publication additionally
requires the separate fresh replay and actual round-completion gate.
"""
from __future__ import annotations

import copy
import hashlib
from functools import cache
from typing import Any, Mapping

from . import catalog as cat
from . import source_policy as sp
from ._contract import bind_import_twin

__all__ = ["load_trusted_catalog", "validate_source_route", "natural_eligibility"]


def _row_findings(row: Any) -> list[str]:
    expected = sp.reviewed_row()
    expected.update(provider=None, channel=None, rights_profile_id=sp.POLICY["policy_id"])
    expected["record_kinds"] = frozenset(expected["record_kinds"])
    expected["allowed_curation_lanes"] = tuple(expected["allowed_curation_lanes"])
    if (getattr(row, "identity_authoritative", None) is not True
            or any(getattr(row, key, object()) != value for key, value in expected.items())):
        return ["PROCEDURAL_ROUTE_UNAUTHORIZED: row differs from sealed source authority"]
    return []


@cache
def _catalog_snapshot() -> cat.Catalog:
    # This shared validator recomputes AST/group/split bindings without execution.
    from .catalog_check import catalog_structure_findings
    try:
        loaded = cat.load_catalog(sp.ROOT / sp.POLICY["catalog_relative_path"])
    except ValueError as exc:
        raise sp.SourcePolicyError(f"PROCEDURAL_CATALOG_INVALID: {exc}") from exc
    if (loaded.programs_sha256 != sp.POLICY["programs_sha256"]
            or loaded.catalog_id != sp.POLICY["catalog_id"]
            or loaded.license_sha256 != sp.POLICY["source_license_evidence"]["license_sha256"]
            or loaded.meta["upstream"] != dict(sp.POLICY["source_license_evidence"])):
        raise sp.SourcePolicyError("PROCEDURAL_CATALOG_PIN_MISMATCH: loaded source drifted")
    findings = catalog_structure_findings(loaded)
    if findings:
        raise sp.SourcePolicyError(f"PROCEDURAL_CATALOG_INVALID: {findings}")
    return loaded


def load_trusted_catalog(row: Any = None) -> cat.Catalog:
    """Load the sealed vendored catalog; caller paths never supply authority.

    Every call rechecks current file bytes. The cached parsed snapshot is kept
    private; callers receive independent copies so mutations cannot change it.
    """
    if row is not None and (findings := _row_findings(row)):
        raise sp.SourcePolicyError("; ".join(findings))
    root = sp.ROOT / sp.POLICY["catalog_relative_path"]
    pins = {
        cat.CATALOG_FILENAME: sp.POLICY["catalog_sha256"],
        cat.PROGRAMS_FILENAME: sp.POLICY["programs_sha256"],
        cat.LICENSE_FILENAME: sp.POLICY["source_license_evidence"]["license_sha256"],
    }
    try:
        for filename, digest in pins.items():
            if hashlib.sha256((root / filename).read_bytes()).hexdigest() != digest:
                raise sp.SourcePolicyError(f"PROCEDURAL_CATALOG_PIN_MISMATCH: {filename}")
    except OSError as exc:
        raise sp.SourcePolicyError(f"PROCEDURAL_CATALOG_UNREADABLE: {exc}") from exc
    return copy.deepcopy(_catalog_snapshot())


def _bound_catalog(row: Any, catalog: cat.Catalog | None) -> cat.Catalog:
    trusted = load_trusted_catalog(row)
    if catalog is not None and catalog != trusted:
        raise sp.SourcePolicyError("PROCEDURAL_CATALOG_SUBSTITUTED: supplied catalog is not trusted")
    return trusted


def validate_source_route(
    record: Any, row: Any, *, catalog: cat.Catalog | None = None,
) -> list[str]:
    """Check reviewed row, generator and source identity; never execute programs.

    The caller resolves the row from the actual source directory. This API has
    no path argument and cannot authenticate a row chosen from payload metadata.
    Full technical validation belongs to the shared family validator below.
    """
    if findings := _row_findings(row):
        return findings
    try:
        trusted = _bound_catalog(row, catalog)
    except sp.SourcePolicyError as exc:
        return [str(exc)]
    if not isinstance(record, Mapping) or record.get("family") != sp.POLICY["family"]:
        return ["PROCEDURAL_FAMILY_MISMATCH: expected python-function-repair"]
    meta = record.get("meta")
    if meta is not None and (
        not isinstance(meta, Mapping) or meta.get("factory") != row.payload_factory
    ):
        return ["PROCEDURAL_FACTORY_MISMATCH: payload factory contradicts source route"]
    generator = record.get("generator")
    if not isinstance(generator, Mapping) or any(
        generator.get(key) != value for key, value in (
            ("name", row.generator), ("version", row.generator_version), ("kind", "programmatic"),
        )
    ):
        return ["PROCEDURAL_GENERATOR_MISMATCH: generator is not the reviewed implementation"]
    scenario = record.get("scenario")
    source = scenario.get("source") if isinstance(scenario, Mapping) else None
    if not isinstance(source, Mapping):
        return ["PROCEDURAL_SOURCE_MISSING: scenario.source must bind a reviewed program"]
    program = next((p for p in trusted.programs if p.program_id == source.get("program_id")), None)
    if program is None or source != {
        "program_id": program.program_id, "family": program.family,
        "upstream": program.upstream, "module_sha256": program.sha256,
    }:
        return ["PROCEDURAL_SOURCE_MISMATCH: source differs from independently pinned catalog"]
    return []


def natural_eligibility(
    record: Any, row: Any, *, catalog: cat.Catalog | None = None,
) -> tuple[bool, tuple[str, ...]]:
    """Return eligibility/reasons for valid evidence; raise for corrupt evidence.

    This proves pure technical/policy eligibility only. It cannot establish that
    replay just ran, a round was completed, or anything was published/trained.
    """
    from .validation import validate_record
    if findings := _row_findings(row):
        raise sp.SourcePolicyError("; ".join(findings))
    trusted = _bound_catalog(row, catalog)
    findings = validate_source_route(record, row, catalog=trusted)
    findings += validate_record(record, "record", catalog=trusted)
    if findings:
        raise sp.SourcePolicyError("; ".join(findings))
    result = record["result"]
    if result["outcome"] == "accepted" and result["oracle_status"] == "validated":
        return True, ()
    return False, tuple(result["reason_codes"]) or ("PROCEDURAL_NATURALLY_INELIGIBLE",)


bind_import_twin(__name__)
