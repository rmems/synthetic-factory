#!/usr/bin/env python3
"""Plant record constructor for the db mill (AST-extracted, cleaned)."""

from __future__ import annotations

from typing import TypedDict

from . import config as cfg
from .import_twins import bind_import_twin

__all__ = ["Plant", "REQUIRED_KEYS", "make_plant"]


class Plant(TypedDict, total=False):
    """One designed leftover plant; required keys always present."""

    engine: str
    slug: str
    plant: str
    surface: str
    table: str
    col: str
    col_v2: str
    leftover: str
    leftover2: str
    seed: str
    fail: str
    inspect: str
    catalog: str
    abort: str
    col_type: str
    lock_fail: str
    db: str


REQUIRED_KEYS = (
    "engine", "slug", "plant", "surface", "table", "col", "col_v2",
    "leftover", "leftover2", "seed", "fail", "inspect", "catalog",
    "abort", "col_type",
)


def make_plant(
    *,
    engine: str,
    slug: str,
    plant: str,
    surface: str,
    table: str,
    col: str,
    col_v2: str,
    leftover: str,
    leftover2: str,
    seed: str,
    fail: str,
    inspect: str,
    catalog: str,
    abort: str,
    col_type: str,
    lock_fail: str | None = None,
    db: str = "app.db",
) -> Plant:
    """Build one plant record with vocabulary and presence checks."""
    if engine not in cfg.ENGINES:
        raise ValueError(f"unknown engine {engine!r} in {slug!r}")
    record: Plant = {
        "engine": engine, "slug": slug, "plant": plant, "surface": surface,
        "table": table, "col": col, "col_v2": col_v2, "leftover": leftover,
        "leftover2": leftover2, "seed": seed, "fail": fail, "inspect": inspect,
        "catalog": catalog, "abort": abort, "col_type": col_type,
        "lock_fail": lock_fail or "", "db": db,
    }
    for key in REQUIRED_KEYS:
        if not record[key]:
            raise ValueError(f"empty {key} in {slug!r}")
    return record


bind_import_twin(__name__)
