#!/usr/bin/env python3
"""Authenticate rights against the source records already bound by gate preparation."""

from __future__ import annotations

import sys
from collections import Counter
from collections.abc import Mapping, Sequence

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("curate_gate_rights")
    from .curate_identity import SourceRecord, curate_record, replay_identity_mapping
    from .rights_record import training_export_blockers
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)("curate_gate_rights")
    from curate_identity import SourceRecord, curate_record, replay_identity_mapping
    from rights_record import training_export_blockers


_MESSAGES = {
    "missing": "RIGHTS_MISSING_ENVELOPE: retained identity mappings lack a rights envelope",
    "invalid": "RIGHTS_INVALID_ENVELOPE: retained rights do not replay from authenticated source",
    "research_only": "RIGHTS_RESEARCH_ONLY: retained records are not training-exportable",
}


def _source_index(lanes: Sequence[dict]) -> dict:
    return {
        (entry["source_path"], entry["source_line"]): entry
        for lane in lanes if lane["transform"] == "curate_identity"
        for entry in lane["entries"]
    }


def _identity_proof(mapping: Mapping) -> tuple[Mapping, Mapping]:
    detail = mapping.get("identity_detail")
    if not isinstance(detail, Mapping):
        raise ValueError("missing retained identity proof")
    source = detail.get("source")
    if not isinstance(source, Mapping):
        raise ValueError("missing identity source")
    return detail, source


def replay_gate_identity(mapping: Mapping):
    """Replay the full identity proof and bind it to the gate coordinate."""
    detail, source = _identity_proof(mapping)
    declared = (mapping.get("source_path"), mapping.get("source_line"), mapping.get("source_hash"))
    if declared != (source.get("path"), source.get("line"), source.get("sha256")):
        raise ValueError("identity proof does not match authenticated coordinate")
    result = replay_identity_mapping(detail)
    if result.action != "retained":
        raise ValueError("identity source is not retained")
    return result


def _replayed_envelope(mapping: Mapping, sources: Mapping):
    source = sources.get((mapping.get("source_path"), mapping.get("source_line")))
    if source is None:
        raise ValueError("no authenticated source for rights")
    if "_source_record" not in source:
        return replay_gate_identity(source).mapping.get("rights")
    if mapping.get("source_hash") != source.get("source_hash"):
        raise ValueError("rights source binding differs from authenticated bytes")
    result = curate_record(SourceRecord(
        source["_source_record"], source["source_path"], source["source_line"], source["source_hash"],
    ))
    if result.action != "retained":
        raise ValueError("rights source does not replay to a retained record")
    return result.mapping.get("rights")


def _mapping_defect(mapping: Mapping, sources: Mapping) -> str | None:
    envelope = mapping.get("rights")
    if not isinstance(envelope, Mapping):
        return "missing"
    try:
        expected = _replayed_envelope(mapping, sources)
    except ValueError:
        return "invalid"
    if envelope != expected:
        return "invalid"
    exportable, _ = training_export_blockers(expected)
    return None if exportable else "research_only"


def evaluate_rights(mappings: Sequence[dict], prepared_lanes: Sequence[dict]) -> tuple[dict, list[str]]:
    """Require every retained mapping to carry a replayed, training-eligible verdict."""
    sources = _source_index(prepared_lanes)
    counts = Counter()
    for mapping in mappings:
        if str(mapping.get("action", "")).lower() in {"retained", "retain", "unchanged"}:
            counts[_mapping_defect(mapping, sources)] += 1
    blockers = [f"{message} ({counts[kind]})" for kind, message in _MESSAGES.items() if counts[kind]]
    report = {"passed": not blockers, "enforced": True}
    report.update({kind: counts[kind] for kind in _MESSAGES})
    return report, blockers


if __package__:
    _expose_package_sibling(__name__)
