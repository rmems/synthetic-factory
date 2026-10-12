#!/usr/bin/env python3
"""Self-check for the db mill: uniqueness, vocabulary, and episode invariants."""

from __future__ import annotations

from . import config as cfg
from .import_twins import bind_import_twin
from .notes import build_pair
from .plants import PLANTS

__all__ = ["self_check"]


def _refuse_bad_slug(slug: str) -> None:
    for frag in cfg.BANNED_FRAGMENTS:
        if frag in slug:
            raise ValueError(f"banned fragment {frag} in {slug}")
    if cfg.RECYCLE_SUFFIX.search(f"dbm-r{cfg.START_ROUND}-{slug}"):
        raise ValueError(f"recycle suffix slug {slug}")


def _require(holds: bool) -> None:
    """An ``assert`` that still runs under ``python -O``: the same bare AssertionError."""
    if not holds:
        raise AssertionError


def _assert_built_pair(round_n: int) -> None:
    ea, eb, notes = build_pair(round_n)
    for ep in (ea, eb):
        _require(ep["reward"]["success"] is True)
        _require(ep["reward"]["apply_fails"] == 2)
        _require(ep["reward"]["plan_changes"] == 1)
        _require(ep["reward"]["lock_timeouts"] == 1)
        _require(len(ep["steps"]) == 16)
        _require(ep["meta"]["generator"] == cfg.GENERATOR)
        _require(ep["meta"]["sim_or_real"] == "designed")
        _require(not cfg.RECYCLE_SUFFIX.search(ep["id"]))
    _require(notes.startswith("# NOTES-"))
    _require("Novel coverage:" in notes)


def _refuse_duplicates(columns: tuple[tuple[str, list], ...]) -> None:
    for label, values in columns:
        if len(set(values)) != len(values):
            raise ValueError(f"duplicate {label}")


def self_check() -> None:
    """Validate the catalog and one built pair per odd index; fail closed."""
    slugs, plants, tables, leftovers, surfaces = [], [], [], [], []
    for i, plant in enumerate(PLANTS):
        slug = plant["slug"]
        slugs.append(slug)
        plants.append(plant["plant"])
        tables.append(plant["table"])
        leftovers.extend((plant["leftover"], plant["leftover2"]))
        surfaces.append(plant["surface"])
        _refuse_bad_slug(slug)
        if i % 2 == 1:
            _assert_built_pair(cfg.START_ROUND + i // 2)
    _refuse_duplicates((
        ("slugs", slugs),
        ("plants", plants),
        ("tables", tables),
        ("leftover names", leftovers),
        ("surfaces", surfaces),
    ))
    if len(PLANTS) % 2:
        raise ValueError("odd plant count")
    print(f"self_check ok: {len(PLANTS)//2} pairs r{cfg.START_ROUND}-r{cfg.START_ROUND + len(PLANTS)//2 - 1}")


bind_import_twin(__name__)
