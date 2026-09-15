#!/usr/bin/env python3
"""Replay qbp leftover pairs through hopper builders.

Writes a brand-new destination and refuses ``outputs/raw/``. The legacy
``qbp-mill*.py`` exec path (``--round`` / ``--staging`` / raw harvest) is not
reproduced.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import catalog as cat
from ._contract import (
    FACTORY,
    FAMILY_PREFIX,
    FINDING_GENERATE_DEST_EXISTS,
    FINDING_GENERATE_MILL,
    FINDING_GENERATE_RAW_TREE,
    FINDING_GENERATE_ROUND,
    FINDING_GENERATE_SHAPE,
    HANDOFF_STEPS,
    SUCCESS_STEPS,
    bind_import_twin,
    envelope,
    hopper_episode,
    hopper_notes_md,
    is_under_raw,
    refuse,
    refuse_when,
)


@dataclass(frozen=True)
class BuiltPair:
    mill_id: str
    round_n: int
    ok: dict[str, Any]
    bad: dict[str, Any]
    notes: str


def build_pair(pair: cat.Pair) -> BuiltPair:
    try:
        ok_ep = hopper_episode.build_success(FACTORY, FAMILY_PREFIX, pair.round_n, pair.ok)
        bad_ep = hopper_episode.build_fail(FACTORY, FAMILY_PREFIX, pair.round_n, pair.bad)
        hopper_episode.validate_pair(ok_ep, bad_ep, pair.round_n)
        notes = hopper_notes_md(FACTORY, pair.round_n, pair.ok, pair.bad, ok_ep["id"], bad_ep["id"])
    except envelope.ContractError as exc:
        refuse(FINDING_GENERATE_SHAPE, str(exc))
    refuse_when(len(ok_ep["steps"]) != SUCCESS_STEPS, FINDING_GENERATE_SHAPE, "success steps")
    refuse_when(len(bad_ep["steps"]) != HANDOFF_STEPS, FINDING_GENERATE_SHAPE, "handoff steps")
    refuse_when("Novel coverage:" not in notes, FINDING_GENERATE_SHAPE, "NOTES missing Novel coverage")
    return BuiltPair(mill_id=pair.mill_id, round_n=pair.round_n, ok=ok_ep, bad=bad_ep, notes=notes)


def build_catalog(catalog: cat.Catalog) -> tuple[BuiltPair, ...]:
    return tuple(build_pair(pair) for pair in catalog.pairs)


def _selected(
    catalog: cat.Catalog,
    mill_id: str | None,
    rounds: tuple[int, ...] | None,
) -> tuple[cat.Pair, ...]:
    rows = catalog.pairs
    if mill_id is not None:
        rows = catalog.pairs_for_mill(mill_id)
    if rounds is not None:
        wanted = set(rounds)
        rows = tuple(pair for pair in rows if pair.round_n in wanted)
        missing = wanted.difference(pair.round_n for pair in rows)
        refuse_when(bool(missing), FINDING_GENERATE_ROUND, f"unknown rounds: {sorted(missing)}")
    refuse_when(not rows, FINDING_GENERATE_MILL, "no qbp pairs match the generate filters")
    return rows


def generate(
    out_dir: Path,
    *,
    catalog: cat.Catalog | None = None,
    mill_id: str | None = None,
    rounds: tuple[int, ...] | None = None,
    catalog_path: Path | None = None,
) -> tuple[BuiltPair, ...]:
    """Write leftover batches into a brand-new destination, one mill subdirectory each."""

    loaded = catalog if catalog is not None else cat.catalog_check(catalog_path)
    selected = _selected(loaded, mill_id, rounds)
    refuse_when(is_under_raw(out_dir), FINDING_GENERATE_RAW_TREE, f"refusing raw-tree dest {out_dir}")
    refuse_when(out_dir.exists(), FINDING_GENERATE_DEST_EXISTS, f"destination exists: {out_dir}")
    out_dir.mkdir(parents=True)
    built = tuple(build_pair(pair) for pair in selected)
    for item in built:
        stage = out_dir / item.mill_id
        batch = stage / f"batch-r{item.round_n:02d}.jsonl"
        notes = stage / f"NOTES-r{item.round_n:02d}.md"
        refuse_when(
            is_under_raw(batch) or is_under_raw(notes),
            FINDING_GENERATE_RAW_TREE,
            "refusing raw-tree write",
        )
        refuse_when(batch.exists() or notes.exists(), FINDING_GENERATE_DEST_EXISTS, f"{batch} exists")
        stage.mkdir(parents=True, exist_ok=True)
        batch.write_text(
            hopper_episode.dumps_episode(item.ok) + "\n" + hopper_episode.dumps_episode(item.bad) + "\n",
            encoding="utf-8",
        )
        notes.write_text(item.notes, encoding="utf-8")
    return built


bind_import_twin(__name__)
