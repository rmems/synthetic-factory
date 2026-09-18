#!/usr/bin/env python3
"""Strict rights-manifest discovery, decoding, and captured-record coverage."""

from __future__ import annotations

import hashlib
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("training_audit_rights_manifest")
    from .curate_identity_json import sha256_json
    from .rights_mapping import parse_strict_json_bytes
    from .strict_jsonl import strict_lf_jsonl_records
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "training_audit_rights_manifest"
    )
    from curate_identity_json import sha256_json
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



def _file_coordinates(relative: str, lines: Sequence[bytes]):
    return {
        (f"records/{relative}", number): sha256_json(parse_strict_json_bytes(line))
        for number, line in enumerate(lines, 1) if line.strip()
    }


def _output_coordinates(files: Mapping[str, bytes], *, preserve_gaps: bool = False) -> dict[tuple[str, int], str]:
    coordinates = {}
    for relative, payload in files.items():
        lines = payload.split(b"\n") if preserve_gaps else strict_lf_jsonl_records(payload, relative)
        coordinates.update(_file_coordinates(relative, lines))
    return coordinates


def _declared_coordinate(entry: Mapping) -> tuple[str, int]:
    path, line = entry.get("output_path"), entry.get("output_line")
    if not isinstance(path, str) or type(line) is not int:
        raise ValueError("invalid retained output coordinate")
    return path, line



def _declared_outputs(entries: Sequence[Mapping]) -> dict:
    declared = {}
    for entry in _retained_entries(entries):
        coordinate = _declared_coordinate(entry)
        if coordinate in declared:
            raise ValueError("duplicate retained output coordinate")
        declared[coordinate] = entry.get("output_sha256")
    return declared



def _require_compose_coverage(entries: Sequence[Mapping], files: Mapping[str, bytes]) -> None:
    if _declared_outputs(entries) != _output_coordinates(files):
        raise ValueError("rights manifest does not cover exact audited records")



def _require_identity_coverage(entries: Sequence[Mapping], files: Mapping[str, bytes]) -> None:
    declared = {}
    for entry in _retained_entries(entries):
        source = entry["source"]
        coordinate = (f"records/{source['path']}", source["line"])
        if coordinate in declared:
            raise ValueError("duplicate identity output coordinate")
        declared[coordinate] = entry["output_sha256"]
    if declared != _output_coordinates(files, preserve_gaps=True):
        raise ValueError("identity manifest does not cover exact audited records")



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
