#!/usr/bin/env python3
"""Rights-export blockers for composed and identity-cleaned trees.

Raw run trees stay structural: this module returns no blockers unless a
compose-manifest or IDENTITY-MANIFEST is present. Research-only retained
records cannot become training-ready.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("training_audit_rights")
    from .curate_identity_registry import default_registry
    from .rights_mapping import RightsPolicyError
    from .rights_record import (
        BLOCKER_PREFIX,
        ENVELOPE_FIELD,
        LANE_FIELD,
        LANE_RESEARCH,
        envelope_for_row,
        envelope_lane,
        invalid_envelope_blocker,
        missing_envelope_blocker,
        prefixed_sha256,
        research_only_blocker,
        training_export_blockers,
        verify_bound_envelope,
    )
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "training_audit_rights"
    )
    from curate_identity_registry import default_registry
    from rights_mapping import RightsPolicyError
    from rights_record import (
        BLOCKER_PREFIX,
        ENVELOPE_FIELD,
        LANE_FIELD,
        LANE_RESEARCH,
        envelope_for_row,
        envelope_lane,
        invalid_envelope_blocker,
        missing_envelope_blocker,
        prefixed_sha256,
        research_only_blocker,
        training_export_blockers,
        verify_bound_envelope,
    )

IDENTITY_MANIFEST_SIDECAR = "IDENTITY-MANIFEST.json"
MANIFEST_DIRNAME = "manifest"
MANIFEST_FILENAME = "compose-manifest.jsonl"
ACTION_RETAINED = "retained"
_DEFECT_MISSING = "missing"
_DEFECT_INVALID = "invalid"


def compose_manifest_path(run_dir: Path) -> Path | None:
    """Return the compose-manifest next to a composed records dir, if present."""

    run_dir = Path(run_dir)
    candidates = (
        run_dir.parent / MANIFEST_DIRNAME / MANIFEST_FILENAME,
        run_dir / MANIFEST_DIRNAME / MANIFEST_FILENAME,
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def identity_manifest_path(run_dir: Path) -> Path | None:
    """Return IDENTITY-MANIFEST.json for an identity-cleaned tree, if present."""

    run_dir = Path(run_dir)
    for candidate in (run_dir / IDENTITY_MANIFEST_SIDECAR, run_dir.parent / IDENTITY_MANIFEST_SIDECAR):
        if candidate.is_file():
            return candidate
    return None


def _load_jsonl_objects(path: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    text = path.read_text(encoding="utf-8")
    for line in text.split("\n"):
        if not line.strip():
            continue
        document = json.loads(line)
        if isinstance(document, dict):
            entries.append(document)
    return entries


def _load_identity_manifest(path: Path) -> list[dict[str, Any]]:
    document = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(document, list):
        return []
    return [item for item in document if isinstance(item, dict)]


def _identity_detail(entry: Mapping[str, Any]) -> dict[str, Any] | None:
    if isinstance(entry.get(ENVELOPE_FIELD), Mapping) and "source" in entry:
        return dict(entry)
    for stage in entry.get("stages") or ():
        if not isinstance(stage, Mapping) or stage.get("lane") != "identity":
            continue
        detail = stage.get("detail")
        if isinstance(detail, dict):
            return detail
    if isinstance(entry.get(ENVELOPE_FIELD), Mapping):
        return dict(entry)
    return None


def _registry_row(mapping: Mapping[str, Any], registry: Any):
    path_id = mapping.get("path_id") or mapping.get("factory")
    if not isinstance(path_id, str):
        return None
    return registry.by_path_id.get(path_id)


def _procedural_eligibility(mapping: Mapping[str, Any]) -> tuple[bool | None, list[str]]:
    authority = mapping.get("procedural_authority")
    if not isinstance(authority, Mapping):
        return None, []
    eligible = authority.get("eligible_training_candidate")
    raw_reasons = authority.get("ineligibility_reasons") or ()
    reasons = (
        [str(item) for item in raw_reasons] if isinstance(raw_reasons, (list, tuple)) else []
    )
    return (bool(eligible) if eligible is not None else None), reasons


def _source_bytes(mapping: Mapping[str, Any]) -> bytes | None:
    source = mapping.get("source")
    original = source.get("original") if isinstance(source, Mapping) else None
    if isinstance(original, str):
        return original.encode("utf-8")
    return None


def _declared_source_digest(mapping: Mapping[str, Any], entry: Mapping[str, Any]) -> str | None:
    source = mapping.get("source")
    if isinstance(source, Mapping) and isinstance(source.get("sha256"), str):
        return source["sha256"]
    declared = entry.get("source_sha256")
    return declared if isinstance(declared, str) else None


def _audit_declared_envelope(
    envelope: Mapping[str, Any],
    *,
    mapping: Mapping[str, Any],
    entry: Mapping[str, Any],
    registry: Any,
    row: Any,
    eligible: bool | None,
    reasons: list[str],
) -> str | None:
    declared = _declared_source_digest(mapping, entry)
    if declared is None or row is None:
        return _DEFECT_INVALID
    try:
        expected = envelope_for_row(
            row,
            source_sha256=declared,
            factory_registry_sha256=registry.sha256,
            eligible=False if eligible is None else eligible,
            ineligibility_reasons=reasons,
        )
        if prefixed_sha256(envelope.get("source_sha256")) != prefixed_sha256(declared):
            return _DEFECT_INVALID
    except RightsPolicyError:
        return _DEFECT_INVALID
    if dict(envelope) != expected:
        return _DEFECT_INVALID
    return None


def _audit_one_envelope(
    envelope: object,
    *,
    mapping: Mapping[str, Any],
    entry: Mapping[str, Any],
    registry: Any,
) -> str | None:
    if not isinstance(envelope, Mapping):
        return _DEFECT_MISSING
    row = _registry_row(mapping, registry)
    eligible, reasons = _procedural_eligibility(mapping)
    source_bytes = _source_bytes(mapping)
    if source_bytes is None:
        return _audit_declared_envelope(
            envelope,
            mapping=mapping,
            entry=entry,
            registry=registry,
            row=row,
            eligible=eligible,
            reasons=reasons,
        )
    try:
        verify_bound_envelope(
            envelope,
            source_bytes=source_bytes,
            factory_registry_bytes=registry.raw_bytes,
            expected_row=row,
            eligible=eligible,
            ineligibility_reasons=reasons,
        )
    except RightsPolicyError:
        return _DEFECT_INVALID
    return None


def _retained_entries(entries: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    retained = []
    for entry in entries:
        action = entry.get("action")
        if action in {ACTION_RETAINED, "retained"}:
            retained.append(entry)
    return retained


def _blockers_for_entries(entries: Sequence[Mapping[str, Any]]) -> list[str]:
    registry = default_registry()
    missing = 0
    invalid = 0
    research = 0
    for entry in _retained_entries(entries):
        mapping = _identity_detail(entry) or dict(entry)
        envelope = mapping.get(ENVELOPE_FIELD)
        if not isinstance(envelope, Mapping):
            envelope = entry.get(ENVELOPE_FIELD)
        if not isinstance(envelope, Mapping):
            missing += 1
            continue
        defect = _audit_one_envelope(
            envelope, mapping=mapping, entry=entry, registry=registry
        )
        if defect == _DEFECT_MISSING:
            missing += 1
            continue
        if defect == _DEFECT_INVALID:
            invalid += 1
            continue
        exportable, _reasons = training_export_blockers(envelope)
        lane = mapping.get(LANE_FIELD) or entry.get(LANE_FIELD) or envelope_lane(envelope)
        if not exportable or lane == LANE_RESEARCH:
            research += 1
    blockers: list[str] = []
    if missing:
        blockers.append(missing_envelope_blocker(missing))
    if invalid:
        blockers.append(invalid_envelope_blocker(invalid))
    if research:
        blockers.append(research_only_blocker(research))
    return blockers


def collect_rights_blockers(run_dir: Path) -> list[str]:
    """Return ``rights:`` blockers for one audited tree, or none for raw trees."""

    run_dir = Path(run_dir)
    compose_path = compose_manifest_path(run_dir)
    if compose_path is not None:
        try:
            return _blockers_for_entries(_load_jsonl_objects(compose_path))
        except (OSError, ValueError, UnicodeError):
            return [invalid_envelope_blocker(1)]
    identity_path = identity_manifest_path(run_dir)
    if identity_path is not None:
        try:
            return _blockers_for_entries(_load_identity_manifest(identity_path))
        except (OSError, ValueError, UnicodeError):
            return [invalid_envelope_blocker(1)]
    return []


def is_rights_blocker(item: object) -> bool:
    """Return whether one audit/export blocker belongs to the rights gate."""

    return isinstance(item, str) and item.startswith(BLOCKER_PREFIX)


if __package__:
    _expose_package_sibling(__name__)
