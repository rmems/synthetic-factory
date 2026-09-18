#!/usr/bin/env python3
"""Rights-export blockers for composed and identity-cleaned trees.

Raw run trees without curation markers stay structural. Curated trees require
complete manifest evidence, including when a manifest is missing or malformed.
Research-only retained records cannot become training-ready.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
import sys
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("training_audit_rights")
    from .curate_identity_registry import default_registry
    from .curate_identity_json import sha256_json
    from . import training_audit_rights_manifest as _manifest
    from .rights_record import (
        BLOCKER_PREFIX,
        ENVELOPE_FIELD,
        invalid_envelope_blocker,
        missing_envelope_blocker,
        research_only_blocker,
        training_export_blockers,
    )
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "training_audit_rights"
    )
    from curate_identity_registry import default_registry
    from curate_identity_json import sha256_json
    import training_audit_rights_manifest as _manifest
    from rights_record import (
        BLOCKER_PREFIX,
        ENVELOPE_FIELD,
        invalid_envelope_blocker,
        missing_envelope_blocker,
        research_only_blocker,
        training_export_blockers,
    )

compose_manifest_path = _manifest.compose_manifest_path
identity_manifest_path = _manifest.identity_manifest_path
_DEFECT_MISSING = "missing"
_DEFECT_INVALID = "invalid"


def _identity_detail(entry: Mapping[str, Any]) -> Mapping[str, Any]:
    if "source" in entry:
        return entry
    stages = entry.get("stages", ())
    if not isinstance(stages, (list, tuple)):
        raise ValueError("compose stages must be a sequence")
    details = [stage.get("detail") for stage in stages
               if isinstance(stage, Mapping) and stage.get("lane") == "identity"]
    detail = details[0] if details else {}
    if not isinstance(detail, Mapping):
        raise ValueError("identity detail must be an object")
    return detail


def _replay_envelope(mapping: Mapping, registry, *, composed: bool):
    if __package__:
        from .compose_curated_rights import replay_composed_identity
        from .curate_identity import replay_identity_mapping
    else:
        from compose_curated_rights import replay_composed_identity
        from curate_identity import replay_identity_mapping
    if composed:
        return replay_composed_identity(mapping)
    replay = replay_identity_mapping(mapping, registry)
    return replay.mapping.get(ENVELOPE_FIELD)


def _entry_defect(entry: Mapping, registry) -> str | None:
    mapping = _identity_detail(entry)
    envelope = mapping.get(ENVELOPE_FIELD)
    if not isinstance(envelope, Mapping):
        return _DEFECT_MISSING
    try:
        expected = _replay_envelope(mapping, registry, composed="source" not in entry)
    except ValueError:
        return _DEFECT_INVALID
    if sha256_json(envelope) != sha256_json(expected):
        return _DEFECT_INVALID
    if sha256_json(entry.get(ENVELOPE_FIELD, envelope)) != sha256_json(expected):
        return _DEFECT_INVALID
    exportable, _ = training_export_blockers(envelope)
    return None if exportable else "research"


def _blockers_for_entries(entries: Sequence[Mapping[str, Any]]) -> list[str]:
    registry = default_registry()
    counts = Counter(_entry_defect(entry, registry) for entry in _manifest._retained_entries(entries))
    render = {
        _DEFECT_MISSING: missing_envelope_blocker,
        _DEFECT_INVALID: invalid_envelope_blocker,
        "research": research_only_blocker,
    }
    return [formatter(counts[kind]) for kind, formatter in render.items() if counts[kind]]


def _identity_tree_blockers(path: Path, payload: bytes, files: Mapping[str, bytes]) -> list[str]:
    # Import at use time: identity attaches rights while constructing its mappings.
    if __package__:
        from .curate_identity import validate_identity_tree
    else:
        from curate_identity import validate_identity_tree
    validate_identity_tree(path.parent, expected_manifest_digest=hashlib.sha256(payload).hexdigest())
    entries = _manifest._load_identity_manifest(payload)
    _manifest._require_identity_coverage(entries, files)
    return _blockers_for_entries(entries)


@dataclass(frozen=True)
class RightsAudit:
    """A rights decision bound to one captured manifest byte sequence."""

    blockers: tuple[str, ...]
    manifest_sha256: str | None = None
    source_run: Path | None = None
    compose_sha256: str | None = None


def _captured_manifest_audit(run_dir: Path, path: Path, files, composed: bool) -> RightsAudit:
    payload = path.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    source_run, compose_digest = _manifest._compose_source(run_dir) if composed else (None, None)
    if composed:
        entries = _manifest._load_jsonl_objects(payload)
        _manifest._require_compose_coverage(entries, _manifest._record_payloads(run_dir) if files is None else files)
        blockers = _blockers_for_entries(entries)
    else:
        blockers = _identity_tree_blockers(
            path, payload, _manifest._record_payloads(run_dir) if files is None else files,
        )
    return RightsAudit(tuple(blockers), digest, source_run, compose_digest)


def capture_rights_audit(run_dir: Path, files: Mapping[str, bytes] | None = None) -> RightsAudit:
    """Capture and audit rights evidence once, before scanning record payloads."""
    run_dir = Path(run_dir)
    compose_path = _manifest.compose_manifest_path(run_dir)
    identity_path = _manifest.identity_manifest_path(run_dir)
    path = compose_path or identity_path
    if path is None:
        blockers = (missing_envelope_blocker(1),) if _manifest._missing_rights_manifest(run_dir) else ()
        return RightsAudit(blockers)
    try:
        return _captured_manifest_audit(run_dir, path, files, compose_path is not None)
    except (OSError, ValueError):
        return RightsAudit((invalid_envelope_blocker(1),))


def collect_rights_blockers(run_dir: Path) -> list[str]:
    """Return rights blockers without exposing the captured audit metadata."""
    return list(capture_rights_audit(run_dir).blockers)


def is_rights_blocker(item: object) -> bool:
    """Return whether one audit/export blocker belongs to the rights gate."""

    return isinstance(item, str) and item.startswith(BLOCKER_PREFIX)


if __package__:
    _expose_package_sibling(__name__)
