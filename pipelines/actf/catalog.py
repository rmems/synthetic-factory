#!/usr/bin/env python3
"""Pinned ACTF mill catalog: compact AST-extract rows in ``lineages.jsonl``.

``lineages_from_recovery`` walks a recover-grok tree with the existing
``records`` scanner (``ast.parse`` only, ``exec: false``). The committed
catalog holds one canonical row per real mill lineage; helper fragments
(``gen_hold.py``, ``_ep*_fragment.py``, …) stay out. Recovered ``gen.py``
sources are not vendored.
"""

from __future__ import annotations

import hashlib
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import lineage as lin
from . import records as rec
from . import vocabulary as cv
from ._contract import bind_import_twin, is_under_raw, load_strict_json

LINEAGE_ROW_FIELDS = (
    "path_key",
    "original_path",
    "original_basename",
    "classification",
    "version_count",
    "canonical_version",
    "canonical_version_id",
    "syntax_status",
    "source_sha256",
    "excluded",
    "reason",
    "functions",
    "classes",
    "imports",
    "calls",
    "episode_functions",
    "factory_literals",
    "operation_counts",
)

PINNED_META = {
    "catalog_id": cv.CATALOG_ID,
    "schema": cv.CATALOG_SCHEMA,
    "family": cv.FAMILY,
    "corpus": cv.CORPUS,
    "factory": cv.FACTORY,
    "extract": "ast.parse",
    "generator_name": cv.GENERATOR_NAME,
    "generator_version": cv.GENERATOR_VERSION,
    "intended_use": cv.INTENDED_USE,
    "project_training_policy": cv.PROJECT_TRAINING_POLICY,
    "source_ref": cv.SOURCE_REF,
    "source_commit": cv.SOURCE_COMMIT,
    "source_tree": cv.SOURCE_TREE,
    "legacy_ref": cv.LEGACY_REF,
    "legacy_commit": cv.LEGACY_COMMIT,
    "legacy_mill_count": 0,
    "recovery_lineages": 68,
    "helper_lineages_excluded": len(cv.HELPER_BASENAMES),
    "lineages_filename": cv.LINEAGES_FILENAME,
}

REQUIRED_META_FIELDS = tuple(PINNED_META) + (
    "lineages_sha256",
    "lineages",
    "helper_path_keys",
)

__all__ = [
    "LINEAGE_ROW_FIELDS",
    "Catalog",
    "LineageRow",
    "catalog_check",
    "catalog_dir",
    "compact_lineage_row",
    "is_mill_catalog_lineage",
    "lineages_from_recovery",
    "load_catalog",
    "sha256_bytes",
]


@dataclass(frozen=True)
class LineageRow:
    """One compact AST-extract row for a recovered mill lineage."""

    path_key: str
    original_path: str
    original_basename: str
    classification: str
    version_count: int
    canonical_version: str | None
    canonical_version_id: str | None
    syntax_status: str
    source_sha256: str | None
    excluded: bool
    reason: str | None
    functions: int | None
    classes: int | None
    imports: int | None
    calls: int | None
    episode_functions: tuple[str, ...]
    factory_literals: tuple[str, ...]
    operation_counts: Mapping[str, int]

    def as_mapping(self) -> dict[str, Any]:
        row = {field: getattr(self, field) for field in LINEAGE_ROW_FIELDS}
        row["episode_functions"] = list(self.episode_functions)
        row["factory_literals"] = list(self.factory_literals)
        row["operation_counts"] = dict(sorted(self.operation_counts.items()))
        return row


@dataclass(frozen=True)
class Catalog:
    catalog_id: str
    lineages: tuple[LineageRow, ...]
    lineages_sha256: str
    meta: Mapping[str, Any]

    def lineage(self, path_key: str) -> LineageRow:
        for item in self.lineages:
            if item.path_key == path_key:
                return item
        cv.refuse(
            cv.FINDING_CATALOG_FIELD_INVALID,
            f"no lineage {cv.shown(path_key)} in the catalog",
        )


def catalog_dir() -> Path:
    return Path(__file__).resolve().parent


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def is_mill_catalog_lineage(lineage: lin.Lineage) -> bool:
    return cv.is_mill_catalog_basename(lineage.original_basename)


def _canonical_record(extracted: tuple[rec.ExtractedRecord, ...]) -> rec.ExtractedRecord:
    kept = tuple(item for item in extracted if not item.excluded)
    if kept:
        return sorted(kept, key=lambda item: item.version_label or "")[0]
    return extracted[0]


def compact_lineage_row(
    lineage: lin.Lineage,
    extracted: tuple[rec.ExtractedRecord, ...],
) -> LineageRow:
    record = _canonical_record(extracted)
    features = record.features or {}
    operations = Counter(item["category"] for item in record.operations)
    return LineageRow(
        path_key=lineage.path_key,
        original_path=lineage.original_path,
        original_basename=lineage.original_basename,
        classification=lineage.classification,
        version_count=lineage.version_count,
        canonical_version=record.version_label,
        canonical_version_id=record.version_id,
        syntax_status=record.syntax_status,
        source_sha256=record.source_sha256,
        excluded=record.excluded,
        reason=record.reason,
        functions=features.get("functions"),
        classes=features.get("classes"),
        imports=features.get("imports"),
        calls=features.get("calls"),
        episode_functions=tuple(features.get("episode_functions") or ()),
        factory_literals=tuple(features.get("factory_literals") or ()),
        operation_counts=dict(sorted(operations.items())),
    )


def lineages_from_recovery(recovery_root: Path) -> tuple[LineageRow, ...]:
    """Build compact rows for every real mill lineage under ``recovery_root``."""

    root = Path(recovery_root)
    cv.refuse_vendor_destination(root)
    cv.refuse_when(
        is_under_raw(root),
        cv.FINDING_RECOVERY_ROOT_UNDER_RAW,
        f"recovery root names the immutable raw tree: {cv.shown(str(root))}",
    )
    rows: list[LineageRow] = []
    for lineage in lin.read_recovery_tree(root):
        if not is_mill_catalog_lineage(lineage):
            continue
        extracted = rec.scan_lineage(lineage)
        rows.append(compact_lineage_row(lineage, extracted))
    return tuple(rows)


def _string_list_field(payload: Mapping[str, Any], label: str, field: str) -> tuple[str, ...]:
    value = payload[field]
    cv.refuse_when(
        not isinstance(value, list) or not all(isinstance(item, str) for item in value),
        cv.FINDING_CATALOG_FIELD_INVALID,
        f"{label} {field} must be a string list",
    )
    return tuple(value)


def _counts_field(payload: Mapping[str, Any], label: str) -> dict[str, int]:
    counts = payload["operation_counts"]
    cv.refuse_when(
        not isinstance(counts, dict)
        or not all(isinstance(key, str) and isinstance(value, int) for key, value in counts.items()),
        cv.FINDING_CATALOG_FIELD_INVALID,
        f"{label} operation_counts must be a string-to-int map",
    )
    return dict(counts)


def _excluded_field(payload: Mapping[str, Any], label: str) -> bool:
    value = payload["excluded"]
    cv.refuse_when(
        not isinstance(value, bool),
        cv.FINDING_CATALOG_FIELD_INVALID,
        f"{label} excluded must be a JSON boolean",
    )
    return value


def _row_from_mapping(payload: Mapping[str, Any], label: str) -> LineageRow:
    missing = [field for field in LINEAGE_ROW_FIELDS if field not in payload]
    cv.refuse_when(
        bool(missing),
        cv.FINDING_CATALOG_FIELD_MISSING,
        f"{label} missing {missing}",
    )
    return LineageRow(
        path_key=str(payload["path_key"]),
        original_path=str(payload["original_path"]),
        original_basename=str(payload["original_basename"]),
        classification=str(payload["classification"]),
        version_count=int(payload["version_count"]),
        canonical_version=payload["canonical_version"],
        canonical_version_id=payload["canonical_version_id"],
        syntax_status=str(payload["syntax_status"]),
        source_sha256=payload["source_sha256"],
        excluded=_excluded_field(payload, label),
        reason=payload["reason"],
        functions=payload["functions"],
        classes=payload["classes"],
        imports=payload["imports"],
        calls=payload["calls"],
        episode_functions=_string_list_field(payload, label, "episode_functions"),
        factory_literals=_string_list_field(payload, label, "factory_literals"),
        operation_counts=_counts_field(payload, label),
    )


def load_catalog(directory: Path | None = None) -> Catalog:
    root = catalog_dir() if directory is None else Path(directory)
    catalog_path = root / cv.CATALOG_FILENAME
    lineages_path = root / cv.LINEAGES_FILENAME
    cv.refuse_first(
        (
            (not catalog_path.is_file(), cv.FINDING_CATALOG_FILE_MISSING, f"missing {catalog_path}"),
            (not lineages_path.is_file(), cv.FINDING_CATALOG_FILE_MISSING, f"missing {lineages_path}"),
        )
    )
    meta = load_strict_json(catalog_path.read_text(encoding="utf-8"))
    cv.refuse_when(
        not isinstance(meta, dict),
        cv.FINDING_CATALOG_FIELD_INVALID,
        "CATALOG.json must be an object",
    )
    missing = [key for key in REQUIRED_META_FIELDS if key not in meta]
    cv.refuse_when(
        bool(missing),
        cv.FINDING_CATALOG_FIELD_MISSING,
        f"CATALOG.json missing {missing}",
    )
    drifted = sorted(key for key, pinned in PINNED_META.items() if meta.get(key) != pinned)
    cv.refuse_when(
        bool(drifted),
        cv.FINDING_CATALOG_FIELD_INVALID,
        f"unexpected catalog identity: {drifted}",
    )
    lineages_bytes = lineages_path.read_bytes()
    digest = sha256_bytes(lineages_bytes)
    cv.refuse_when(
        meta.get("lineages_sha256") != digest,
        cv.FINDING_LINEAGES_SHA_MISMATCH,
        f"lineages.jsonl sha256 {digest} != pinned {meta.get('lineages_sha256')}",
    )
    rows = [
        _row_from_mapping(load_strict_json(line), f"line {lineno}")
        for lineno, line in enumerate(lineages_bytes.decode("utf-8").splitlines(), start=1)
        if line.strip()
    ]
    cv.refuse_when(not rows, cv.FINDING_CATALOG_EMPTY, "lineages.jsonl has no rows")
    cv.refuse_when(
        len(rows) != meta["lineages"],
        cv.FINDING_CATALOG_FIELD_INVALID,
        f"lineages.jsonl has {len(rows)} rows; CATALOG.json says {meta['lineages']}",
    )
    keys = [row.path_key for row in rows]
    cv.refuse_when(
        len(set(keys)) != len(keys),
        cv.FINDING_DUPLICATE_PATH_KEY,
        "duplicate path_key values in lineages.jsonl",
    )
    return Catalog(cv.CATALOG_ID, tuple(rows), digest, meta)


def catalog_check(catalog: Catalog | None = None) -> dict[str, Any]:
    loaded = load_catalog() if catalog is None else catalog
    cv.refuse_when(not loaded.lineages, cv.FINDING_CATALOG_EMPTY, "catalog has no lineages")
    exact = sum(
        1 for row in loaded.lineages if row.classification == cv.CLASSIFICATION_EXACT and not row.excluded
    )
    excluded = sum(1 for row in loaded.lineages if row.excluded)
    return {
        "status": "ok",
        "catalog_id": loaded.catalog_id,
        "lineages": len(loaded.lineages),
        "exact_kept": exact,
        "excluded": excluded,
        "recovery_lineages": loaded.meta["recovery_lineages"],
        "helper_lineages_excluded": loaded.meta["helper_lineages_excluded"],
    }


bind_import_twin(__name__)
