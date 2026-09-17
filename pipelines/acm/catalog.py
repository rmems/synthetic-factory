#!/usr/bin/env python3
"""Load and write the AST-extracted ACM catalog. Never stores mill source.

The committed ``CATALOG.json`` next to this module holds the 8 representative
pairs from the 1052-pair / 95-file extract on ``legacy-mill-lane`` at
``SOURCE_COMMIT``. The remaining 1044 pairs live in compact ``rows.jsonl``.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import _contract
from ._contract import (
    CATALOG_FORMAT,
    CATALOG_ID,
    DEFERRED_ROW_COUNT,
    FACTORY_NAME,
    FAMILY,
    FULL_ROW_COUNT,
    GENERATOR,
    ID_PREFIX,
    LOOP_PREFIX,
    QUOTA,
    REPRESENTATIVE_ROW_COUNT,
    ROWS_FILENAME,
    SOURCE_COMMIT,
    SOURCE_REF,
    STEPS,
    VENDOR_PREFIX,
    WRAP_NEEDLES,
    refuse_vendor_paths,
)

CATALOG_FILENAME = "CATALOG.json"

__all__ = [
    "CATALOG_FILENAME",
    "ROWS_FILENAME",
    "Pair",
    "Plant",
    "catalog_payload",
    "check_catalog",
    "check_tree_has_no_vendor",
    "default_catalog_dir",
    "dumps_catalog",
    "dumps_rows",
    "load_catalog",
    "load_rows",
    "plant_from_mapping",
    "row_from_pair",
    "sha256_text",
    "write_catalog",
]


@dataclass(frozen=True)
class Plant:
    """One side of a leftover OpenAPI-drift pair."""

    slug: str
    domain: str
    success: bool
    field: str
    old: str
    new: str
    name: str = ""
    fail_err: str = ""
    vs: str = ""
    fetch1: str = ""
    fetch2: str = ""


@dataclass(frozen=True)
class Pair:
    """Success plant plus the complementary fail/handoff plant."""

    catalog_id: str
    source: str
    kind: str
    success: Plant
    fail: Plant


def sha256_text(text: str) -> str:
    """Digest UTF-8 text the same way the extract records source files."""

    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def default_catalog_dir() -> Path:
    """Package directory that holds the committed catalog and deferred rows."""

    return Path(__file__).resolve().parent


def dumps_catalog(payload: Mapping[str, Any]) -> str:
    """Stable catalog JSON: sorted keys, two-space indent, trailing newline."""

    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def dumps_rows(rows: list[Mapping[str, Any]]) -> str:
    """One pair row per line, sorted keys, so ``rows_sha256`` is stable."""

    lines = [
        json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        for row in rows
    ]
    return "\n".join(lines) + ("\n" if lines else "")


def load_rows(path: Path) -> list[dict[str, Any]]:
    """Load compact JSONL pair rows; refuse a pretty-printed or non-object line."""

    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line:
            continue
        row = json.loads(line)
        if not isinstance(row, dict):
            raise ValueError("catalog row is not an object")
        compact = json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        if line != compact:
            raise ValueError("catalog row is not compact JSONL")
        rows.append(row)
    return rows


def catalog_payload(
    *,
    rows: list[dict[str, Any]],
    sources: list[dict[str, Any]],
    bans: Mapping[str, list[str]],
    source_files: int,
) -> dict[str, Any]:
    """The catalog object: identity, bans, sources, and pair rows."""

    return {
        "bans": {
            "blob_keys": list(bans.get("blob_keys", ())),
            "slug_needles": list(bans.get("slug_needles", ())),
        },
        "catalog_id": CATALOG_ID,
        "extract": {
            "exec": False,
            "method": "ast.parse",
            "source_commit": SOURCE_COMMIT,
            "source_files": source_files,
            "source_ref": SOURCE_REF,
        },
        "factory": FACTORY_NAME,
        "family": FAMILY,
        "format": CATALOG_FORMAT,
        "generator": GENERATOR,
        "id_prefix": ID_PREFIX,
        "quota": QUOTA,
        "row_count": len(rows),
        "rows": rows,
        "rows_sha256": sha256_text(dumps_rows(rows)),
        "sources": sources,
        "steps": STEPS,
    }


def write_catalog(directory: Path, payload: Mapping[str, Any]) -> Path:
    """Write one ``CATALOG.json``; refuse an existing file or a vendor name."""

    dest = directory / CATALOG_FILENAME
    refuse_vendor_paths((dest, directory))
    if dest.exists():
        raise FileExistsError(dest)
    directory.mkdir(parents=True, exist_ok=True)
    dest.write_text(dumps_catalog(payload), encoding="utf-8")
    return dest


def load_catalog(directory: Path | None = None) -> dict[str, Any]:
    """Load a catalog directory and refuse a drifted identity pin."""

    root = directory or default_catalog_dir()
    path = root / CATALOG_FILENAME
    if not path.is_file():
        raise FileNotFoundError(f"missing catalog: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("catalog must be an object")
    _require(payload, "format", CATALOG_FORMAT)
    _require(payload, "catalog_id", CATALOG_ID)
    _require(payload, "family", FAMILY)
    _require(payload, "factory", FACTORY_NAME)
    _require(payload, "generator", GENERATOR)
    rows = payload.get("rows")
    if not isinstance(rows, list):
        raise ValueError("catalog rows are missing")
    if payload.get("row_count") != len(rows):
        raise ValueError("catalog.row_count does not match rows")
    if payload.get("rows_sha256") != sha256_text(dumps_rows(rows)):
        raise ValueError("catalog.rows_sha256 does not match rows")
    loaded = dict(payload)
    deferred = _deferred_rows_from_extract(loaded, root)
    if deferred is not None:
        loaded["deferred_rows"] = deferred
    return loaded


def plant_from_mapping(payload: Mapping[str, Any], *, success: bool | None = None) -> Plant:
    """Build a plant from extracted kwargs or a catalog row half."""

    flag = payload.get("success") if success is None else success
    return Plant(
        slug=str(payload["slug"]),
        domain=str(payload.get("domain") or ""),
        success=bool(flag),
        field=str(payload.get("field") or ""),
        old=str(payload.get("old") or ""),
        new=str(payload.get("new") or ""),
        name=str(payload.get("name") or ""),
        fail_err=str(payload.get("fail_err") or ""),
        vs=str(payload.get("vs") or ""),
        fetch1=str(payload.get("fetch1") or ""),
        fetch2=str(payload.get("fetch2") or ""),
    )


def row_from_pair(pair: Pair) -> dict[str, Any]:
    """One catalog row: identity plus the two slugs and the success surface."""

    return {
        "catalog_id": pair.catalog_id,
        "source": pair.source,
        "kind": pair.kind,
        "success_slug": pair.success.slug,
        "fail_slug": pair.fail.slug,
        "field": pair.success.field,
        "old": pair.success.old,
        "new": pair.success.new,
        "domain": pair.success.domain,
        "fail_err": pair.success.fail_err,
        "vs": pair.success.vs,
        "fetch1": pair.success.fetch1,
        "fetch2": pair.success.fetch2,
    }


def check_tree_has_no_vendor(root: Path) -> None:
    """Refuse a tree that vendors ``acm-mill*.py`` or ``acm-loop*.py``."""

    refuse_vendor_paths(root.rglob(f"{VENDOR_PREFIX}*.py"))
    refuse_vendor_paths(root.rglob(f"{LOOP_PREFIX}*.py"))


def check_catalog(payload: Mapping[str, Any]) -> None:
    """Refuse a catalog that drifted from identity or pair shape."""

    if payload.get("factory") != FACTORY_NAME:
        raise ValueError("catalog factory is not api-contract-migration-factory")
    if payload.get("family") != FAMILY:
        raise ValueError("catalog family is not acm")
    if payload.get("quota") != QUOTA:
        raise ValueError("catalog quota must be 2")
    if payload.get("steps") != STEPS:
        raise ValueError("catalog steps must be 16")
    rows = payload.get("rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError("catalog rows are missing")
    slugs: set[str] = set()
    _check_rows(rows, slugs)
    _check_deferred_union(payload, rows, slugs)


def _deferred_rows_from_extract(
    payload: Mapping[str, Any], root: Path
) -> list[dict[str, Any]] | None:
    extract = payload.get("extract")
    if not isinstance(extract, dict) or extract.get("deferred_rows") is None:
        return None
    if extract.get("deferred_rows") != ROWS_FILENAME:
        raise ValueError("catalog extract.deferred_rows must be rows.jsonl")
    path = root / ROWS_FILENAME
    if not path.is_file():
        raise FileNotFoundError(f"missing catalog rows: {path}")
    rows = load_rows(path)
    if extract.get("deferred_row_count") != len(rows):
        raise ValueError("catalog extract.deferred_row_count does not match rows")
    if extract.get("deferred_rows_sha256") != sha256_text(dumps_rows(rows)):
        raise ValueError("catalog extract.deferred_rows_sha256 does not match rows")
    return rows


def _check_deferred_union(
    payload: Mapping[str, Any], rows: list[object], slugs: set[str]
) -> None:
    deferred = payload.get("deferred_rows")
    if deferred is None:
        return
    if not isinstance(deferred, list) or not deferred:
        raise ValueError("catalog deferred_rows are missing")
    _check_rows(deferred, slugs)
    if len(rows) != REPRESENTATIVE_ROW_COUNT:
        raise ValueError("catalog representative row_count must be 8")
    if len(deferred) != DEFERRED_ROW_COUNT:
        raise ValueError("catalog deferred_row_count must be 1044")
    if len(rows) + len(deferred) != FULL_ROW_COUNT:
        raise ValueError("representative plus deferred rows must total 1052")


def _check_rows(rows: list[object], slugs: set[str]) -> None:
    for row in rows:
        _check_row(row, slugs)


def _check_row(row: object, slugs: set[str]) -> None:
    if not isinstance(row, dict):
        raise ValueError("catalog row is not an object")
    success = row.get("success_slug")
    fail = row.get("fail_slug")
    if not isinstance(success, str) or not isinstance(fail, str):
        raise ValueError("catalog row is missing slugs")
    if success == fail:
        raise ValueError(f"pair slugs are not distinct: {success}")
    for slug in (success, fail):
        if slug in slugs:
            raise ValueError(f"duplicate slug {slug}")
        slugs.add(slug)
        for needle in WRAP_NEEDLES:
            if needle in slug:
                raise ValueError(f"banned needle {needle!r} in {slug}")


def _require(payload: Mapping[str, Any], key: str, expected: object) -> None:
    if payload.get(key) != expected:
        raise ValueError(f"catalog.{key} must be {expected!r}")


_contract.bind_import_twin(__name__)
