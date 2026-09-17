#!/usr/bin/env python3
"""Self-check for the db mill: uniqueness, vocabulary, and episode invariants."""

from __future__ import annotations

from . import config as cfg
from . import episode as ep_mod
from .import_twins import bind_import_twin
from .notes import build_pair
from .plants import PLANTS

__all__ = ["self_check"]


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
        for frag in cfg.BANNED_FRAGMENTS:
            if frag in slug:
                raise ValueError(f"banned fragment {frag} in {slug}")
        if cfg.RECYCLE_SUFFIX.search(f"dbm-r{cfg.START_ROUND}-{slug}"):
            raise ValueError(f"recycle suffix slug {slug}")
        if i % 2 == 1:
            round_n = cfg.START_ROUND + i // 2
            ea, eb, notes = build_pair(round_n)
            for ep in (ea, eb):
                assert ep["reward"]["success"] is True
                assert ep["reward"]["apply_fails"] == 2
                assert ep["reward"]["plan_changes"] == 1
                assert ep["reward"]["lock_timeouts"] == 1
                assert len(ep["steps"]) == 16
                assert ep["meta"]["generator"] == cfg.GENERATOR
                assert ep["meta"]["sim_or_real"] == "designed"
                assert not cfg.RECYCLE_SUFFIX.search(ep["id"])
            assert notes.startswith("# NOTES-")
            assert "Novel coverage:" in notes
    if len(set(slugs)) != len(slugs):
        raise ValueError("duplicate slugs")
    if len(set(plants)) != len(plants):
        raise ValueError("duplicate plants")
    if len(set(tables)) != len(tables):
        raise ValueError("duplicate tables")
    if len(set(leftovers)) != len(leftovers):
        raise ValueError("duplicate leftover names")
    if len(set(surfaces)) != len(surfaces):
        raise ValueError("duplicate surfaces")
    if len(PLANTS) % 2:
        raise ValueError("odd plant count")
    print(f"self_check ok: {len(PLANTS)//2} pairs r{cfg.START_ROUND}-r{cfg.START_ROUND + len(PLANTS)//2 - 1}")


bind_import_twin(__name__)
