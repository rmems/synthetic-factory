#!/usr/bin/env python3
"""Lane-manifest entry parsing for the curation gate.

Split out of ``curate_gate.py`` (CodeScene: Lines of Code in a Single File) by
responsibility; every name is re-exported from ``curate_gate`` so existing
``curate_gate.X`` call sites resolve unchanged.

A lane manifest is either JSONL (one entry per line) or a JSON document whose
entry list sits at the top level or under one of ``MANIFEST_LIST_KEYS``. Both
shapes are parsed from bytes that were captured once, and every entry is then
normalized to one flat record-level vocabulary before authentication.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("curate_gate_manifests")
    from . import curate_gate_contract as _contract
    from . import curate_gate_digest as _digest
    from .check_records import reject_json_constant
    from .exact_json import parse_finite_json_float
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "curate_gate_manifests"
    )
    _PIPELINES = Path(__file__).resolve().parent
    if str(_PIPELINES) not in sys.path:
        sys.path.insert(0, str(_PIPELINES))
    import curate_gate_contract as _contract
    import curate_gate_digest as _digest
    from check_records import reject_json_constant
    from exact_json import parse_finite_json_float

GateError = _contract.GateError
MANIFEST_LIST_KEYS = _contract.MANIFEST_LIST_KEYS
record_sha256 = _digest.record_sha256
_lf_lines = _digest._lf_lines
_read_regular_file_snapshot = _digest._read_regular_file_snapshot


def _manifest_entries(
    path: Path,
    format_hint: str | None = None,
    *,
    payload: bytes | None = None,
) -> list[dict[str, Any]]:
    if format_hint not in {None, "json", "jsonl"}:
        raise GateError(f"{path}: unsupported manifest format {format_hint!r}")
    if payload is None:
        payload, _digest, _size = _read_regular_file_snapshot(path, "lane manifest")
    try:
        text = payload.decode("utf-8")
    except UnicodeError as exc:
        raise GateError(f"cannot decode lane manifest {path}: {exc}") from exc
    if format_hint == "jsonl" or (format_hint is None and path.suffix == ".jsonl"):
        return _jsonl_manifest_entries(path, text)
    return _json_manifest_entries(path, text)


def _jsonl_manifest_entries(path: Path, text: str) -> list[dict[str, Any]]:
    """One object per non-blank line, refused at the first bad line."""
    entries = []
    for number, line in enumerate(_lf_lines(text), 1):
        if not line.strip():
            continue
        try:
            entry = json.loads(
                line,
                parse_constant=reject_json_constant,
                parse_float=parse_finite_json_float,
            )
        except ValueError as exc:
            raise GateError(f"{path}:{number}: invalid JSON manifest line: {exc}") from exc
        if not isinstance(entry, dict):
            raise GateError(f"{path}:{number}: manifest entry must be an object")
        entries.append(entry)
    return entries


def _json_manifest_entries(path: Path, text: str) -> list[dict[str, Any]]:
    """A top-level list, or the first ``MANIFEST_LIST_KEYS`` list in an object."""
    try:
        document = json.loads(
            text,
            parse_constant=reject_json_constant,
            parse_float=parse_finite_json_float,
        )
    except ValueError as exc:
        raise GateError(f"{path}: invalid JSON: {exc}") from exc
    if isinstance(document, list):
        candidates = document
    elif isinstance(document, dict):
        candidates = None
        for key in MANIFEST_LIST_KEYS:
            value = document.get(key)
            if isinstance(value, list):
                candidates = value
                break
        if candidates is None:
            raise GateError(
                f"{path}: manifest object needs one of {', '.join(MANIFEST_LIST_KEYS)} as a list"
            )
    else:
        raise GateError(f"{path}: manifest must be a list or an object")
    for entry in candidates:
        if not isinstance(entry, dict):
            raise GateError(f"{path}: every manifest entry must be an object")
    return list(candidates)


def _normalize_entry(entry: dict[str, Any], lane: dict[str, Any]) -> dict[str, Any]:
    source = entry.get("source")
    if not isinstance(source, dict):
        source = {}
    transform_value = entry.get("transform")
    if isinstance(transform_value, dict):
        transform = transform_value
        transform_name = transform.get("name")
        transform_version = transform.get("version")
    else:
        transform_name = transform_value if isinstance(transform_value, str) else None
        transform_version = None
    declared_transform = entry.get("transform_name") or transform_name
    declared_version = entry.get("transform_version") or transform_version
    reasons = entry.get("reason_codes")
    if reasons is None:
        reasons = []
    return {
        "lane_order": lane["order"],
        "transform": declared_transform or lane["transform"],
        "version": declared_version or lane["version"],
        "declared_transform": declared_transform,
        "declared_version": declared_version,
        "action": entry.get("action"),
        "reason_codes": copy.deepcopy(reasons),
        "source_path": entry.get("source_path") or source.get("path"),
        "source_line": (
            entry.get("source_line") if entry.get("source_line") is not None else source.get("line")
        ),
        "source_hash": (
            entry.get("source_hash") or entry.get("source_sha256") or source.get("sha256")
        ),
        "record_kind": entry.get("record_kind") or entry.get("kind"),
        "classification": entry.get("classification"),
        "output_id": entry.get("output_id"),
        "output_hash": entry.get("output_hash") or entry.get("output_sha256"),
        "id_mappings": copy.deepcopy(entry.get("id_mappings")),
        "provenance_mappings": copy.deepcopy(entry.get("provenance_mappings")),
        "manifest_entry_sha256": record_sha256(entry),
    }


if __package__:
    _expose_package_sibling(__name__)
