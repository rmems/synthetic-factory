#!/usr/bin/env python3
"""Build KCL leftover pairs and hop-replay hopper g46c plants.

Leftover generation never writes ``outputs/raw/``, never imports
``kcl-mill*.py``, and never stamps ``grok-4.6``. Hop replay uses hopper on
main (``start_by_factory`` / ``pairs_by_factory`` / ``emit_stage``) for the
**g46c** wave instead of executing a leftover hopper mill.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import catalog as cat
from ._contract import (
    FINDING_DESTINATION_EXISTS,
    FINDING_DESTINATION_UNDER_RAW,
    FINDING_ROUND_INVALID,
    FINDING_UNKNOWN_WAVE,
    FINDING_USAGE,
    HOPPER_WAVE,
    ROW_KIND_REPRESENTATIVE,
    bind_import_twin,
    dumps_exact_json,
    is_under_raw,
    refuse_first,
    refuse_when,
)
from .episode import build_handoff, build_success
from .notes import notes_markdown

if __name__.startswith("pipelines."):
    from ..hopper import emit_stage, pairs_by_factory, start_by_factory
    from ..hopper.plants import WAVES
else:
    from hopper import emit_stage, pairs_by_factory, start_by_factory
    from hopper.plants import WAVES

__all__ = [
    "BuiltPair",
    "HopReplay",
    "build_pair",
    "generate",
    "hop_replay",
    "notes_markdown",
]


@dataclass(frozen=True)
class BuiltPair:
    round_n: int
    ok: dict[str, Any]
    bad: dict[str, Any]
    notes: str


@dataclass(frozen=True)
class HopReplay:
    factory: str
    round_n: int
    ids: tuple[str, str]


def build_pair(plant: cat.Plant, *, round_n: int | None = None) -> BuiltPair:
    spec = cat.spec_for(plant)
    used_round = plant.base_round if round_n is None else round_n
    refuse_when(used_round < 1, FINDING_ROUND_INVALID, f"round {used_round} is not a mill round")
    ok = build_success(spec, round_n=used_round, mill_id=plant.mill_id, plant_id=plant.plant_id)
    bad = build_handoff(spec, round_n=used_round, mill_id=plant.mill_id, plant_id=plant.plant_id)
    refuse_when(ok["id"] == bad["id"], FINDING_USAGE, "duplicate episode ids")
    notes = notes_markdown(spec, ok["id"], bad["id"], used_round)
    return BuiltPair(round_n=used_round, ok=ok, bad=bad, notes=notes)


def _refuse_destination(out_dir: Path) -> None:
    refuse_first(
        (
            (is_under_raw(out_dir), FINDING_DESTINATION_UNDER_RAW, f"refusing raw-tree dest {out_dir}"),
            (out_dir.exists(), FINDING_DESTINATION_EXISTS, f"destination exists: {out_dir}"),
        )
    )


def write_round(out_dir: Path, built: BuiltPair) -> tuple[Path, Path]:
    batch = out_dir / f"batch-r{built.round_n:02d}.jsonl"
    notes = out_dir / f"NOTES-r{built.round_n:02d}.md"
    refuse_when(
        is_under_raw(batch) or is_under_raw(notes),
        FINDING_DESTINATION_UNDER_RAW,
        "refusing raw-tree write",
    )
    batch.write_text(
        dumps_exact_json(built.ok) + "\n" + dumps_exact_json(built.bad) + "\n",
        encoding="utf-8",
        newline="",
    )
    notes.write_text(built.notes, encoding="utf-8")
    return batch, notes


def _resolve_catalog(catalog: cat.Catalog | None, catalog_dir: Path | None) -> cat.Catalog:
    if catalog is not None:
        return catalog
    if catalog_dir is not None:
        return cat.load_catalog(catalog_dir)
    return cat.catalog_check()


def _select_plants(
    loaded: cat.Catalog,
    plant_id: str | None,
    mill_id: str | None,
    all_plants: bool,
) -> tuple[cat.Plant, ...]:
    if plant_id is not None:
        return (loaded.plant(plant_id),)
    if mill_id is not None:
        return loaded.mill_plants(mill_id)
    refuse_when(not all_plants, FINDING_USAGE, "generate needs --plant, --mill, or --all")
    selected = tuple(plant for plant in loaded.plants if plant.row_kind == ROW_KIND_REPRESENTATIVE)
    refuse_when(not selected, FINDING_USAGE, "no representative plants to generate")
    return selected


def generate(
    out_dir: Path,
    *,
    catalog: cat.Catalog | None = None,
    plant_id: str | None = None,
    mill_id: str | None = None,
    all_plants: bool = False,
    round_n: int | None = None,
    catalog_dir: Path | None = None,
) -> tuple[BuiltPair, ...]:
    """Write leftover CrashLoop pairs into a brand-new destination."""

    loaded = _resolve_catalog(catalog, catalog_dir)
    selected = _select_plants(loaded, plant_id, mill_id, all_plants)
    _refuse_destination(out_dir)
    out_dir.mkdir(parents=True)
    # --round pins one exact plant; mill and --all runs step from each base round.
    pinned_round = round_n if plant_id is not None else None
    built: list[BuiltPair] = []
    for offset, plant in enumerate(selected):
        used = plant.base_round + offset if pinned_round is None else pinned_round
        item = build_pair(plant, round_n=used)
        write_round(out_dir, item)
        built.append(item)
    return tuple(built)


def hop_replay(
    out_dir: Path,
    *,
    wave: str = HOPPER_WAVE,
    factory: str | None = None,
    slug: str | None = None,
) -> tuple[HopReplay, ...]:
    """Replay hopper plants through the g46c API. Never exec a leftover hopper mill."""

    refuse_when(wave not in WAVES, FINDING_UNKNOWN_WAVE, f"unknown hopper wave {wave!r}")
    _refuse_destination(out_dir)
    starts = start_by_factory(wave)
    table = pairs_by_factory(wave)
    rows: list[tuple[str, int, Mapping[str, Any], Mapping[str, Any]]] = []
    factories = (factory,) if factory is not None else tuple(table)
    for name in factories:
        refuse_when(name not in table, FINDING_USAGE, f"no {wave} pairs for {name}")
        start = starts[name]
        for index, (ok, bad) in enumerate(table[name]):
            if slug is not None and slug not in {ok["slug"], bad["slug"]}:
                continue
            published = ok.get("published_round")
            round_n = published if isinstance(published, int) else start + index
            rows.append((name, round_n, ok, bad))
    refuse_when(not rows, FINDING_USAGE, "no hopper pairs match the hop-replay filters")
    out_dir.mkdir(parents=True)
    written: list[HopReplay] = []
    for name, round_n, ok, bad in rows:
        ids = emit_stage(out_dir / name, name, round_n, ok, bad)
        written.append(HopReplay(factory=name, round_n=round_n, ids=(ids[0], ids[1])))
    return tuple(written)


bind_import_twin(__name__)
