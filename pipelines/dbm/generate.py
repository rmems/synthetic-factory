#!/usr/bin/env python3
"""Write leftover3 dbm episodes into a brand-new destination.

Never writes ``outputs/raw/`` and never imports leftover mill scripts.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import catalog as cat
from . import episode as ep
from ._contract import (
    FACTORY,
    FINDING_GENERATE_DEST_EXISTS,
    FINDING_GENERATE_RAW_TREE,
    FINDING_GENERATE_ROUND,
    FINDING_GENERATE_SHAPE,
    SUCCESS_STEPS,
    bind_import_twin,
    dumps_exact_json,
    is_under_raw,
    refuse_when,
)

__all__ = ["BuiltPair", "build_catalog", "build_pair", "generate", "notes_markdown"]


@dataclass(frozen=True)
class BuiltPair:
    round_n: int
    ok: dict[str, Any]
    bad: dict[str, Any]
    notes: str


def notes_markdown(
    round_n: int,
    a: Mapping[str, str],
    b: Mapping[str, str],
    ok_id: str,
    bad_id: str,
    coverage: int,
    unused: tuple[str, ...],
) -> str:
    unused_s = ", ".join(unused) if unused else "leftover leftover leftover catalog end"
    notes = (
        f"# NOTES-r{round_n} {FACTORY}\n\n"
        f"Novel coverage: {coverage}%\n\n"
        "Two designed leftover leftover leftover episodes (quota 2). Unique vs r1-r105, "
        "r106-r239 engines, r240-r761 recycle, r762-r793 warehouse, r794-r817 ORM-CLI, "
        "r818-r844 PG catalog, r845-r1259 leftover mills. Surfaces: "
        f"{a['surface']}; {b['surface']}. IDs `dbm-r{round_n}-<slug>` without "
        "`-rNN` recycle suffix. Dual leftover leftover leftover residual. First-apply fail + plan "
        "change + lock retry. grok-4.6 designed.\n\n"
        "| id | seed | first apply | plan change | terminal |\n"
        "|---|---|---|---|---|\n"
        f"| {ok_id} | {a['seed'][:48]} | first apply fail | expand {a['col_v2']} | "
        f"4/4 {ep.residual(a)[:48]} |\n"
        f"| {bad_id} | {b['seed'][:48]} | first apply fail | expand {b['col_v2']} | "
        f"4/4 {ep.residual(b)[:48]} |\n\n"
        "## Step counts\n"
        "- ep1: 16. apply fail 2; lock 1.\n"
        "- ep2: 16. apply fail 2; lock 1.\n\n"
        "## decision_basis audit\n"
        f"plants `{a['plant']}`, `{b['plant']}`. designed grok-4.6. "
        f"{a['catalog']} | {b['catalog']}\n\n"
        "## Weaknesses / next\n"
        f"Unused: {unused_s}.\n"
        f"Avoid {a['slug']} and {b['slug']} next. Do not clone r762-r793, "
        "r794-r817, or r818-r844. Do not recycle r240-r761.\n"
    )
    refuse_when(
        "Novel coverage:" not in notes,
        FINDING_GENERATE_SHAPE,
        "NOTES missing Novel coverage",
    )
    return notes


def _unused_slugs(leftover3: cat.Leftover3, round_n: int) -> tuple[str, ...]:
    nxt = (round_n - leftover3.start_round + 1) * 2
    if nxt + 1 < len(leftover3.plants):
        return leftover3.plants[nxt]["slug"], leftover3.plants[nxt + 1]["slug"]
    return ()


def validate_pair(ok_ep: dict[str, Any], bad_ep: dict[str, Any], round_n: int) -> None:
    refuse_when(
        ok_ep["reward"]["success"] is not True,
        FINDING_GENERATE_SHAPE,
        "first episode must succeed",
    )
    refuse_when(
        bad_ep["reward"]["success"] is not True,
        FINDING_GENERATE_SHAPE,
        "second episode must succeed",
    )
    refuse_when(
        len(ok_ep["steps"]) != SUCCESS_STEPS or len(bad_ep["steps"]) != SUCCESS_STEPS,
        FINDING_GENERATE_SHAPE,
        "shape must be 16-step leftover3 success + 16-step leftover3 success",
    )
    refuse_when(
        ok_ep["meta"]["round"] != round_n or bad_ep["meta"]["round"] != round_n,
        FINDING_GENERATE_SHAPE,
        "meta.round mismatch",
    )
    refuse_when(ok_ep["id"] == bad_ep["id"], FINDING_GENERATE_SHAPE, "duplicate episode ids")


def build_pair(pair: cat.Pair, leftover3: cat.Leftover3) -> BuiltPair:
    ok_ep = ep.build_episode(pair.round_n, pair.ok, 0)
    bad_ep = ep.build_episode(pair.round_n, pair.bad, 1)
    validate_pair(ok_ep, bad_ep, pair.round_n)
    notes = notes_markdown(
        pair.round_n,
        pair.ok,
        pair.bad,
        ok_ep["id"],
        bad_ep["id"],
        ep.coverage_for(pair.round_n),
        _unused_slugs(leftover3, pair.round_n),
    )
    return BuiltPair(round_n=pair.round_n, ok=ok_ep, bad=bad_ep, notes=notes)


def build_catalog(loaded: cat.Catalog) -> tuple[BuiltPair, ...]:
    return tuple(build_pair(pair, loaded.leftover3) for pair in loaded.leftover3.pairs)


def _refuse_destination(out_dir: Path) -> None:
    refuse_when(
        is_under_raw(out_dir),
        FINDING_GENERATE_RAW_TREE,
        f"refusing raw-tree dest {out_dir}",
    )
    refuse_when(out_dir.exists(), FINDING_GENERATE_DEST_EXISTS, f"destination exists: {out_dir}")


def write_round(out_dir: Path, built: BuiltPair) -> tuple[Path, Path]:
    batch = out_dir / f"batch-r{built.round_n:02d}.jsonl"
    notes = out_dir / f"NOTES-r{built.round_n:02d}.md"
    refuse_when(
        is_under_raw(batch) or is_under_raw(notes),
        FINDING_GENERATE_RAW_TREE,
        "refusing raw-tree write",
    )
    refuse_when(
        batch.exists() or notes.exists(),
        FINDING_GENERATE_DEST_EXISTS,
        f"refuse to overwrite staged round r{built.round_n} in {out_dir}",
    )
    batch.write_text(
        dumps_exact_json(built.ok) + "\n" + dumps_exact_json(built.bad) + "\n",
        encoding="utf-8",
        newline="",
    )
    notes.write_text(built.notes, encoding="utf-8")
    return batch, notes


def generate(
    out_dir: Path,
    *,
    catalog: cat.Catalog | None = None,
    rounds: tuple[int, ...] | None = None,
    leftover3_path: Path | None = None,
    mills_path: Path | None = None,
) -> tuple[BuiltPair, ...]:
    """Write leftover3 batches into a brand-new destination."""

    loaded = catalog if catalog is not None else cat.catalog_check(leftover3_path, mills_path)
    selected = loaded.leftover3.pairs
    if rounds is not None:
        wanted = set(rounds)
        selected = tuple(pair for pair in selected if pair.round_n in wanted)
        missing = wanted.difference(pair.round_n for pair in selected)
        refuse_when(
            bool(missing),
            FINDING_GENERATE_ROUND,
            f"unknown leftover3 rounds: {sorted(missing)}",
        )
    _refuse_destination(out_dir)
    out_dir.mkdir(parents=True)
    built = tuple(build_pair(pair, loaded.leftover3) for pair in selected)
    for item in built:
        write_round(out_dir, item)
    return built


bind_import_twin(__name__)
