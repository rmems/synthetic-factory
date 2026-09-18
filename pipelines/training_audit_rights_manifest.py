#!/usr/bin/env python3
"""Strict rights-manifest discovery, decoding, and captured-record payloads."""

from __future__ import annotations

import hashlib
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("training_audit_rights_manifest")
    from .rights_mapping import parse_strict_json_bytes
    from .strict_jsonl import strict_lf_jsonl_records
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "training_audit_rights_manifest"
    )
    from rights_mapping import parse_strict_json_bytes
    from strict_jsonl import strict_lf_jsonl_records

IDENTITY_MANIFEST_SIDECAR = "IDENTITY-MANIFEST.json"
MANIFEST_DIRNAME = "manifest"
MANIFEST_FILENAME = "compose-manifest.jsonl"
ACTION_RETAINED = "retained"


def compose_manifest_path(run_dir: Path) -> Path | None:
    """Return the compose-manifest next to a composed records dir, if present."""

    run_dir = Path(run_dir)
    candidates = (
        run_dir.parent / MANIFEST_DIRNAME / MANIFEST_FILENAME,
        run_dir / MANIFEST_DIRNAME / MANIFEST_FILENAME,
    )
    for candidate in candidates:
        if candidate.exists() or candidate.is_symlink():
            return candidate
    return None


def identity_manifest_path(run_dir: Path) -> Path | None:
    """Return IDENTITY-MANIFEST.json for an identity-cleaned tree, if present."""

    run_dir = Path(run_dir)
    for candidate in (run_dir / IDENTITY_MANIFEST_SIDECAR, run_dir.parent / IDENTITY_MANIFEST_SIDECAR):
        if candidate.exists() or candidate.is_symlink():
            return candidate
    return None


def _require_manifest_entries(document: object) -> list[dict[str, Any]]:
    if not isinstance(document, list) or not document:
        raise ValueError("rights manifest must contain source entries")
    if not all(isinstance(item, dict) for item in document):
        raise ValueError("rights manifest entries must be objects")
    return document


def _load_jsonl_objects(payload: bytes) -> list[dict[str, Any]]:
    entries = [parse_strict_json_bytes(line)
               for line in strict_lf_jsonl_records(payload, "compose manifest")]
    return _require_manifest_entries(entries)


def _load_identity_manifest(payload: bytes) -> list[dict[str, Any]]:
    return _require_manifest_entries(parse_strict_json_bytes(payload))


def _retained_entries(entries: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    return [entry for entry in entries if entry.get("action") == ACTION_RETAINED]


def _missing_rights_manifest(run_dir: Path) -> bool:
    return any(
        (root / sidecar).exists()
        for root in (run_dir, run_dir.parent)
        for sidecar in ("FACTORY-REGISTRY.json", "COMPOSE.json")
    )


def _record_payloads(run_dir: Path) -> dict[str, bytes]:
    root = run_dir / "records" if (run_dir / "records").is_dir() else run_dir
    return {path.relative_to(root).as_posix(): path.read_bytes() for path in root.rglob("*.jsonl")}


def _compose_source(run_dir: Path) -> tuple[Path | None, str | None]:
    parent = run_dir.parent if run_dir.name == "records" else run_dir
    path = parent / "COMPOSE.json"
    if not (path.exists() or path.is_symlink()):
        return None, None
    payload = path.read_bytes()
    summary = parse_strict_json_bytes(payload)
    source = summary.get("source_run") if isinstance(summary, Mapping) else None
    if not isinstance(source, str) or not Path(source).is_absolute():
        raise ValueError("compose source_run must identify an absolute source root")
    return Path(source), hashlib.sha256(payload).hexdigest()


if __package__:
    _expose_package_sibling(__name__)
