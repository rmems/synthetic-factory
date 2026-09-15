#!/usr/bin/env python3
"""Load the committed pay Archive B catalog (``CATALOG.json`` + ``archive_b.jsonl``)."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ._contract import (
    ARCHIVE,
    CATALOG_FILENAME,
    CATALOG_ID,
    CATALOG_SCHEMA,
    FACTORY,
    FINDING_CATALOG_FIELD_INVALID,
    FINDING_CATALOG_FIELD_MISSING,
    FINDING_CATALOG_FILE_MISSING,
    FINDING_CATALOG_SHA256_MISMATCH,
    FINDING_DUPLICATE_SLUG,
    FINDING_SLICE_A_OVERLAP,
    GENERATOR,
    PAIRS_FILENAME,
    bind_import_twin,
    load_strict_json,
    package_dir,
    refuse,
    refuse_when,
)
from . import pairs as slice_a
from .archive_b_extract import pairs_from_source

__all__ = [
    "ArchiveBCatalog",
    "ArchiveBPair",
    "catalog_path",
    "load_archive_b_catalog",
    "pairs_sha256",
    "sha256_bytes",
]


@dataclass(frozen=True)
class ArchiveBPair:
    ok: Mapping[str, Any]
    fail: Mapping[str, Any]

    @property
    def ok_slug(self) -> str:
        return str(self.ok["slug"])

    @property
    def fail_slug(self) -> str:
        return str(self.fail["slug"])


@dataclass(frozen=True)
class ArchiveBCatalog:
    catalog_id: str
    directory: Path
    pairs_sha256: str
    pairs: tuple[ArchiveBPair, ...]
    meta: Mapping[str, Any]

    def slugs(self) -> frozenset[str]:
        found: set[str] = set()
        for pair in self.pairs:
            found.add(pair.ok_slug)
            found.add(pair.fail_slug)
        return frozenset(found)


def catalog_path() -> Path:
    return package_dir() / CATALOG_FILENAME


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def pairs_sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def _load_pairs_jsonl(path: Path) -> tuple[ArchiveBPair, ...]:
    refuse_when(not path.is_file(), FINDING_CATALOG_FILE_MISSING, f"missing {path.name}")
    rows: list[ArchiveBPair] = []
    seen: set[str] = set()
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        payload = json.loads(line)
        refuse_when(
            not isinstance(payload, dict) or "ok" not in payload or "fail" not in payload,
            FINDING_CATALOG_FIELD_INVALID,
            f"{path.name}:{line_no} must be {{ok, fail}}",
        )
        pair = ArchiveBPair(ok=payload["ok"], fail=payload["fail"])
        for slug in (pair.ok_slug, pair.fail_slug):
            refuse_when(slug in seen, FINDING_DUPLICATE_SLUG, f"duplicate slug {slug!r}")
            seen.add(slug)
        rows.append(pair)
    refuse_when(not rows, FINDING_CATALOG_FIELD_INVALID, f"{path.name} is empty")
    return tuple(rows)


def _assert_disjoint_from_slice_a(catalog: ArchiveBCatalog) -> None:
    slice_slugs = {row["slug"] for row in slice_a.PAIRS}
    slice_slugs.update(row["fail"] for row in slice_a.PAIRS)
    overlap = catalog.slugs() & slice_slugs
    refuse_when(
        bool(overlap),
        FINDING_SLICE_A_OVERLAP,
        f"Archive B slugs overlap landed slice A: {sorted(overlap)}",
    )


def load_archive_b_catalog(directory: Path | None = None) -> ArchiveBCatalog:
    root = package_dir() if directory is None else directory
    meta_path = root / CATALOG_FILENAME
    pairs_path = root / PAIRS_FILENAME
    refuse_when(not meta_path.is_file(), FINDING_CATALOG_FILE_MISSING, f"missing {CATALOG_FILENAME}")
    meta = load_strict_json(meta_path)
    for key in ("catalog_id", "schema", "factory", "generator", "archive", "pairs_sha256", "source", "extract"):
        refuse_when(key not in meta, FINDING_CATALOG_FIELD_MISSING, f"{CATALOG_FILENAME}.{key} is missing")
    refuse_when(meta["catalog_id"] != CATALOG_ID, FINDING_CATALOG_FIELD_INVALID, "catalog_id drift")
    refuse_when(meta["schema"] != CATALOG_SCHEMA, FINDING_CATALOG_FIELD_INVALID, "schema drift")
    refuse_when(meta["factory"] != FACTORY, FINDING_CATALOG_FIELD_INVALID, "factory drift")
    refuse_when(meta["generator"] != GENERATOR, FINDING_CATALOG_FIELD_INVALID, "generator drift")
    refuse_when(meta["archive"] != ARCHIVE, FINDING_CATALOG_FIELD_INVALID, "archive drift")
    digest = pairs_sha256(pairs_path)
    refuse_when(
        digest != meta["pairs_sha256"],
        FINDING_CATALOG_SHA256_MISMATCH,
        f"{PAIRS_FILENAME} sha256 mismatch",
    )
    pairs = _load_pairs_jsonl(pairs_path)
    committed = meta.get("extract", {}).get("committed_pairs")
    refuse_when(
        committed is not None and committed != len(pairs),
        FINDING_CATALOG_FIELD_INVALID,
        "committed_pairs does not match jsonl row count",
    )
    catalog = ArchiveBCatalog(
        catalog_id=meta["catalog_id"],
        directory=root,
        pairs_sha256=digest,
        pairs=pairs,
        meta=meta,
    )
    _assert_disjoint_from_slice_a(catalog)
    return catalog


def catalog_check(source_text: str) -> tuple[dict[str, Any], ...]:
    """Re-extract ``mill_plants.py`` text and return pair mappings."""

    return pairs_from_source(source_text)


if __package__:
    bind_import_twin(__name__)
