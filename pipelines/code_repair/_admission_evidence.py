"""Pure route, generator, and catalog evidence checks for admission."""

from __future__ import annotations

from typing import Any, Mapping

from . import catalog as cat
from . import source_policy as sp
from ._contract import bind_import_twin, oc


def row_findings(row: Any) -> list[str]:
    expected = sp.reviewed_row()
    expected.update(provider=None, channel=None, rights_profile_id=sp.POLICY["policy_id"])
    expected["record_kinds"] = frozenset(expected["record_kinds"])
    expected["allowed_curation_lanes"] = tuple(expected["allowed_curation_lanes"])
    actual = {key: getattr(row, key, object()) for key in expected}
    authorized = getattr(row, "identity_authoritative", None) is True
    if not authorized or actual != expected:
        return ["PROCEDURAL_ROUTE_UNAUTHORIZED: row differs from sealed source authority"]
    return []


def factory_matches(meta: Any, row: Any) -> bool:
    if meta is None:
        return True
    return isinstance(meta, Mapping) and meta.get("factory") == row.payload_factory


def generator_matches(generator: Any, row: Any) -> bool:
    if not isinstance(generator, Mapping):
        return False
    expected = {"name": row.generator, "version": row.generator_version,
                "kind": "programmatic", "authority": "propose_only"}
    return (set(generator) == set(expected) | {"seed"}
            and all(generator.get(key) == value for key, value in expected.items()))


def payload_findings(record: Any, row: Any) -> list[str]:
    if not isinstance(record, Mapping) or record.get("family") != sp.POLICY["family"]:
        return ["PROCEDURAL_FAMILY_MISMATCH: expected python-function-repair"]
    if record.get("validation") != oc.unvalidated():
        return ["PROCEDURAL_VALIDATION_STAMP: producer evidence must be unvalidated"]
    if not factory_matches(record.get("meta"), row):
        return ["PROCEDURAL_FACTORY_MISMATCH: payload factory contradicts source route"]
    if not generator_matches(record.get("generator"), row):
        return ["PROCEDURAL_GENERATOR_MISMATCH: generator is not the reviewed implementation"]
    return []


def source_findings(record: Mapping[str, Any], trusted: cat.Catalog) -> list[str]:
    scenario = record.get("scenario")
    source = scenario.get("source") if isinstance(scenario, Mapping) else None
    if not isinstance(source, Mapping):
        return ["PROCEDURAL_SOURCE_MISSING: scenario.source must bind a reviewed program"]
    program = next((p for p in trusted.programs if p.program_id == source.get("program_id")), None)
    if program is None or source != {
        "program_id": program.program_id,
        "family": program.family,
        "upstream": program.upstream,
        "module_sha256": program.sha256,
    }:
        return ["PROCEDURAL_SOURCE_MISMATCH: source differs from independently pinned catalog"]
    return []


def record_findings(record: Any, row: Any, trusted: cat.Catalog) -> list[str]:
    return payload_findings(record, row) or source_findings(record, trusted)


bind_import_twin(__name__)
