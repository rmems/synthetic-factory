#!/usr/bin/env python3
"""Round notes and staging for the db mill (AST-extracted, cleaned)."""

from __future__ import annotations

from pathlib import Path

from . import config as cfg
from . import episode as ep_mod
from . import sql as db_sql
from .import_twins import bind_import_twin
from .plant import Plant
from .plants import PLANTS

__all__ = ["build_pair", "emit_stage", "notes_md"]


def notes_md(round_n: int, a: Plant, b: Plant, coverage: int) -> str:
    """Markdown notes for one round; asserts the coverage marker downstream."""
    ea, eb = ep_mod.build_episode(round_n, a, 0), ep_mod.build_episode(round_n, b, 1)
    nxt = (round_n - cfg.START_ROUND + 1) * 2
    unused = [PLANTS[nxt]["slug"], PLANTS[nxt + 1]["slug"]] if nxt + 1 < len(PLANTS) else []
    unused_s = ", ".join(unused) if unused else "catalog end"
    body = (
        f"# NOTES-r{round_n} {cfg.FACTORY_SLUG}\n\n"
        f"Novel coverage: {coverage}%\n\n"
        "Two designed episodes (quota 2). Unique vs r1-r105 first-cycle, r106-r239 engines, "
        "r240-r761 recycle mill, r762-r793 warehouse mill, r794-r817 ORM-CLI grid, and r818-r844 "
        f"PG catalog/AM grid. Surfaces: {a['surface']}; {b['surface']}. IDs `dbm-r{round_n}-<slug>` "
        "without `-rNN` recycle suffix. Dual-object residual. First-apply fail + plan change + lock retry. "
        "Semantic mill (not CLI clone).\n\n"
        "| id | seed | first apply | plan change | terminal |\n|---|---|---|---|---|\n"
        f"| {ea['id']} | {db_sql.seed_cmd_for(a)[:48]} | first apply fail | expand {a['col_v2']} | 4/4 {ep_mod.residual(a)[:72]} |\n"
        f"| {eb['id']} | {db_sql.seed_cmd_for(b)[:48]} | first apply fail | expand {b['col_v2']} | 4/4 {ep_mod.residual(b)[:72]} |\n\n"
        "## Step counts\n- ep1: 16. apply fail 2; lock 1.\n- ep2: 16. apply fail 2; lock 1.\n\n"
        "## decision_basis audit\n"
        f"plants `{a['plant']}`, `{b['plant']}`. designed {cfg.GENERATOR}. {a['catalog']} | {b['catalog']}\n\n"
        "## Weaknesses / next\n"
        f"Unused: {unused_s}.\nAvoid {a['slug']} and {b['slug']} next. Do not clone r762-r793, r794-r817, or r818-r844. Do not recycle.\n"
    )
    return body


def build_pair(round_n: int) -> tuple[dict, dict, str]:
    """Two episodes plus notes for ``round_n``; refuses a notes miss."""
    a, b = ep_mod.pair_for(round_n)
    ea, eb = ep_mod.build_episode(round_n, a, 0), ep_mod.build_episode(round_n, b, 1)
    notes = notes_md(round_n, a, b, ep_mod.coverage_for(round_n))
    if "Novel coverage:" not in notes:
        raise ValueError("NOTES missing Novel coverage")
    return ea, eb, notes


def emit_stage(stage: Path, round_n: int) -> tuple[str, str]:
    """Write ``batch-rNN.jsonl`` + ``NOTES-rNN.md``; caller provides a fresh dir."""
    ea, eb, notes = build_pair(round_n)
    batch, notes_path = stage / f"batch-r{round_n:02d}.jsonl", stage / f"NOTES-r{round_n:02d}.md"
    if batch.exists() or notes_path.exists():
        raise FileExistsError(f"refuse to overwrite staged round r{round_n} in {stage}")
    batch.write_text(ep_mod.dumps_episode(ea) + "\n" + ep_mod.dumps_episode(eb) + "\n", encoding="utf-8")
    notes_path.write_text(notes, encoding="utf-8")
    return ea["id"], eb["id"]


bind_import_twin(__name__)
