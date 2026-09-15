#!/usr/bin/env python3
"""Load and write the AST-extracted ACM catalog. Never stores mill source."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from . import _contract
from . import identity

CATALOG_FILENAME = "CATALOG.json"
ROWS_FILENAME = "rows.jsonl"

__all__ = [
    "CATALOG_FILENAME",
    "ROWS_FILENAME",
    "catalog_payload",
    "default_catalog_dir",
    "dumps_catalog",
    "dumps_rows",
    "load_catalog",
    "sha256_text",
    "write_catalog",
]


def sha256_text(text: str) -> str:
    """Digest UTF-8 text the same way the extract records source files."""

    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def default_catalog_dir() -> Path:
    """``catalogs/api-contract-migration-v1`` next to ``pipelines/``."""

    return Path(__file__).resolve().parents[2] / "catalogs" / identity.CATALOG_ID


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


def catalog_payload(
    *,
    rows: list[dict[str, Any]],
    sources: list[dict[str, Any]],
    bans: Mapping[str, list[str]],
    source_files: int,
) -> dict[str, Any]:
    """The committed catalog object: identity, bans, sources, rows."""

    return {
        "bans": {
            "blob_keys": list(bans.get("blob_keys", ())),
            "slug_needles": list(bans.get("slug_needles", ())),
        },
        "catalog_id": identity.CATALOG_ID,
        "extract": {
            "exec": False,
            "method": "ast.parse",
            "source_commit": identity.SOURCE_COMMIT,
            "source_files": source_files,
            "source_ref": identity.SOURCE_REF,
        },
        "factory": identity.FACTORY_NAME,
        "family": identity.FAMILY,
        "format": identity.CATALOG_FORMAT,
        "generator": identity.GENERATOR,
        "id_prefix": identity.ID_PREFIX,
        "quota": identity.QUOTA,
        "row_count": len(rows),
        "rows": rows,
        "rows_sha256": sha256_text(dumps_rows(rows)),
        "sources": sources,
        "steps": identity.STEPS,
    }


def write_catalog(directory: Path, payload: Mapping[str, Any]) -> Path:
    """Write metadata and ``rows.jsonl``; mill source never lands here."""

    dest = directory / CATALOG_FILENAME
    rows_path = directory / ROWS_FILENAME
    identity.refuse_vendor_paths((dest, rows_path, directory))
    rows = list(payload["rows"])
    meta = {key: value for key, value in payload.items() if key != "rows"}
    dest.write_text(dumps_catalog(meta), encoding="utf-8")
    rows_path.write_text(dumps_rows(rows), encoding="utf-8")
    return dest


def load_catalog(directory: Path | None = None) -> dict[str, Any]:
    """Load a catalog directory and refuse a drifted identity pin."""

    root = directory or default_catalog_dir()
    path = root / CATALOG_FILENAME
    rows_path = root / ROWS_FILENAME
    if not path.is_file():
        raise FileNotFoundError(f"missing catalog: {path}")
    if not rows_path.is_file():
        raise FileNotFoundError(f"missing catalog rows: {rows_path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("catalog must be an object")
    _require(payload, "format", identity.CATALOG_FORMAT)
    _require(payload, "catalog_id", identity.CATALOG_ID)
    _require(payload, "family", identity.FAMILY)
    _require(payload, "factory", identity.FACTORY_NAME)
    _require(payload, "generator", identity.GENERATOR)
    rows = [json.loads(line) for line in rows_path.read_text(encoding="utf-8").splitlines() if line]
    if payload.get("row_count") != len(rows):
        raise ValueError("catalog.row_count does not match rows")
    digest = sha256_text(dumps_rows(rows))
    if payload.get("rows_sha256") != digest:
        raise ValueError("catalog.rows_sha256 does not match rows")
    payload = dict(payload)
    payload["rows"] = rows
    return payload


def _require(payload: Mapping[str, Any], key: str, expected: object) -> None:
    if payload.get(key) != expected:
        raise ValueError(f"catalog.{key} must be {expected!r}")


_contract.bind_import_twin(__name__)
