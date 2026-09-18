#!/usr/bin/env python3
"""AST-extract deferred Archive B mill_plants_* sources (git-show only, never exec)."""

from __future__ import annotations

import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from ._contract import (
    FINDING_CATALOG_FIELD_INVALID,
    SOURCE_BYTES_COMMIT,
    SOURCE_BYTES_REF,
    bind_import_twin,
    load_strict_json,
    package_dir,
    refuse,
    refuse_when,
    repo_root,
)
from .archive_b_extract import pairs_from_chained_source

__all__ = [
    "deferred_source_rows",
    "deferred_sources",
    "git_show_deferred_source",
    "load_deferred_sources_meta",
]


def load_deferred_sources_meta(catalog_path: Path | None = None) -> tuple[Mapping[str, Any], ...]:
    path = package_dir() / "CATALOG.json" if catalog_path is None else catalog_path
    meta = load_strict_json(path)
    extract = meta.get("extract")
    refuse_when(not isinstance(extract, dict), FINDING_CATALOG_FIELD_INVALID, "extract must be object")
    raw = extract.get("deferred_sources")
    refuse_when(not isinstance(raw, list), FINDING_CATALOG_FIELD_INVALID, "deferred_sources must be a list")
    rows: list[Mapping[str, Any]] = []
    for index, entry in enumerate(raw):
        refuse_when(
            not isinstance(entry, dict),
            FINDING_CATALOG_FIELD_INVALID,
            f"deferred_sources[{index}] must be object",
        )
        refuse_when(
            "path" not in entry or "n_pairs" not in entry,
            FINDING_CATALOG_FIELD_INVALID,
            f"deferred_sources[{index}] missing path or n_pairs",
        )
        rows.append(entry)
    return tuple(rows)


def deferred_sources(catalog_path: Path | None = None) -> tuple[Mapping[str, Any], ...]:
    return load_deferred_sources_meta(catalog_path)


def git_show_deferred_source(path: str) -> str:
    root = repo_root()
    for spec in (
        f"{SOURCE_BYTES_COMMIT}:{path}",
        f"{SOURCE_BYTES_REF}:{path}",
    ):
        try:
            proc = subprocess.run(
                ["git", "show", spec],
                cwd=root,
                check=False,
                capture_output=True,
                text=True,
            )
        except OSError as exc:
            refuse(FINDING_CATALOG_FIELD_INVALID, f"git show failed for {path}: {exc}")
        if proc.returncode == 0:
            return proc.stdout
    refuse(FINDING_CATALOG_FIELD_INVALID, f"deferred source not available via git show: {path}")


def deferred_source_rows(
    text: str,
    *,
    path: str,
    expected_rows: int,
) -> tuple[dict[str, Any], ...]:
    return pairs_from_chained_source(text, source=path, expected_rows=expected_rows)


def extract_all_deferred(
    sources: Sequence[Mapping[str, Any]] | None = None,
) -> tuple[dict[str, Any], ...]:
    """Extract every row pinned under ``extract.deferred_sources`` (for tests and checks)."""

    pinned = deferred_sources() if sources is None else sources
    rows: list[dict[str, Any]] = []
    for entry in pinned:
        path = str(entry["path"])
        expected = entry["n_pairs"]
        refuse_when(
            type(expected) is not int or expected < 1,
            FINDING_CATALOG_FIELD_INVALID,
            f"{path} n_pairs must be positive int",
        )
        text = git_show_deferred_source(path)
        rows.extend(
            deferred_source_rows(text, path=path, expected_rows=expected),
        )
    return tuple(rows)


if __package__:
    bind_import_twin(__name__)
