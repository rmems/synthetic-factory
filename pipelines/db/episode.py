#!/usr/bin/env python3
"""Designed episode builder for the db mill (AST-extracted, cleaned)."""

from __future__ import annotations

import json
from typing import Any

from . import config as cfg
from . import sql as db_sql
from .import_twins import bind_import_twin
from .plant import Plant
from .plants import PLANTS

__all__ = [
    "assert_clean", "build_episode", "coverage_for", "dumps_episode",
    "pair_for", "residual", "short_name",
]


def _step(n: int, decision_basis: str, tool_call: dict, observation: str) -> dict:
    return {"n": n, "decision_basis": decision_basis, "tool_call": tool_call, "observation": observation}


def _bash(command: str) -> dict:
    return {"name": "bash", "args": {"command": command}}


def _write(path: str, contents: str) -> dict:
    return {"name": "write", "args": {"path": path, "contents": contents}}


def dumps_episode(ep: dict) -> str:
    """Canonical single-line JSON for one episode."""
    return json.dumps(ep, ensure_ascii=True, separators=(",", ":"))


def assert_clean(obj: Any, path: str = "") -> None:
    """Reject banned reasoning keys, real-sim claims, and spike events."""
    if isinstance(obj, dict):
        for key, val in obj.items():
            if key in cfg.BANNED_KEYS:
                raise ValueError(f"banned key {key} at {path}")
            if key == "sim_or_real" and val == "real":
                raise ValueError(f"sim_or_real real at {path}")
            if key == "spike_events":
                raise ValueError(f"spike_events at {path}")
            assert_clean(val, f"{path}.{key}")
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            assert_clean(item, f"{path}[{i}]")


def pair_for(round_n: int) -> tuple[Plant, Plant]:
    """Two plants for ``round_n``; one wrap past the catalog end."""
    idx = round_n - cfg.START_ROUND
    n_pairs = len(PLANTS) // 2
    if idx < 0:
        raise KeyError(f"no plant pair for round {round_n} (before r{cfg.START_ROUND})")
    if idx >= n_pairs:
        idx -= n_pairs
    start = idx * 2
    if idx >= n_pairs or start + 1 >= len(PLANTS):
        raise KeyError(f"no plant pair for round {round_n} (have {n_pairs} from r{cfg.START_ROUND}, one wrap)")
    return PLANTS[start], PLANTS[start + 1]


def coverage_for(round_n: int) -> int:
    return max(cfg.COVERAGE_FLOOR, 91 - (round_n - cfg.START_ROUND))


def short_name(p: Plant) -> str:
    return p["table"].split(".")[-1]


def residual(p: Plant) -> str:
    s = short_name(p)
    return f"{s}.{p['col']} + {p['col_v2']}; leftover {p['leftover']} + {p['leftover2']}"


def build_episode(round_n: int, p: Plant, ep_idx: int) -> dict:
    """Build one 16-step designed episode for plant ``p``."""
    ver = 2200 + (round_n - cfg.START_ROUND) * 2 + ep_idx
    slug, table, col, col_v2 = p["slug"], p["table"], p["col"], p["col_v2"]
    stem = slug.replace("-", "_")
    leftover, leftover2, res, sname = p["leftover"], p["leftover2"], residual(p), short_name(p)
    mig, down, test = f"migrations/{ver}_{stem}.sql", f"migrations/{ver}_{stem}.down.sql", f"tests/test_{stem}.py"
    runbook, backfill, checksum = f"docs/{slug}.md", f"jobs/backfill_{stem}.py", f"jobs/checksum_{stem}.py"
    inspect_cmd, seed_cmd = db_sql.engine_cmd(p, p["inspect"]), db_sql.seed_cmd_for(p)
    abort_cmd = db_sql.engine_cmd(p, p["abort"])
    lock_cmd, lock_fail, expand = db_sql.engine_cmd(p, db_sql.lock_sql(p)), db_sql.default_lock_fail(p), db_sql.expand_sql(p)
    inspect_obs = (f"{table} present\npending: {p['fail']}\nshape now: {res}\n"
                   f"catalog: {p['catalog']}\nlocks/mutations: 1 active; dual leftover objects")
    eid = f"dbm-r{round_n}-{slug}"
    if cfg.RECYCLE_SUFFIX.search(eid):
        raise ValueError(f"recycle suffix in id: {eid}")
    goal = (f"{p['plant']}: {p['engine']} {seed_cmd} on {table}.{col} failed "
            f"({p['fail'][:120]}). Expand {col_v2}, backfill, residual {res}.")
    plan = f"Abort in-place rewrite; expand-contract via {expand}; keep {col}; dual leftover objects."
    steps = [
        _step(1, f"Plan: inspect {p['engine']} catalog for {table} before apply {ver} ({slug}).", _bash(inspect_cmd), inspect_obs),
        _step(2, f"Plan: apply naive catalog change on {table}.{col}.", _bash(seed_cmd), p["fail"]),
        _step(3, (f"Observation: first apply failed ({p['fail'][:90]}). Plan change: abort in-place rewrite; "
                  f"expand {col_v2} + backfill; leave {col} residual."), _bash(abort_cmd),
               "leftovers dropped or cancelled; naive rewrite aborted; dual objects still planned"),
        _step(4, f"Plan: write expand-only migration {ver} adding {col_v2} (keep {col}).",
               _write(mig, f"-- {ver} expand {table} {col_v2}\n{expand};\n-- never drop {col}; keep dual residual\n-- {p['catalog']}\n"),
               "expand-only written"),
        _step(5, f"Plan: apply expand {ver} with short lock timeout.", _bash(lock_cmd), lock_fail),
        _step(6, "Observation: lock timeout on expand. Plan: retry lock timeout off-peak; ACCESS EXCLUSIVE avoided.",
               _bash(lock_cmd), f"ok retry expand {col_v2}"),
        _step(7, f"Plan: batched backfill {col_v2} from {col} without validating leftover constraints.",
               _bash(f"python {backfill} --batch 8000 --from {col} --to {col_v2}"),
               f"copied batch ok; remaining 0 on {table}; dual residual {res}"),
        _step(8, f"Plan: tests {test} (catalog residual must remain).", _bash(f"pytest -q {test}"), "3 passed"),
        _step(9, f"Plan: down {ver} must refuse lossy drop of {col_v2}.",
               _write(down, f"SELECT raise_error('lossy {col_v2} drop; dual residual {sname} must remain');\n"), "down v2 guard"),
        _step(10, f"Observation: dual residual {res}.", _bash(inspect_cmd), res),
        _step(11, "Plan: runbook never in-place rewrite via naive catalog DDL.",
               _write(runbook, f"Never {seed_cmd}. Expand {col_v2}, backfill, dual-read. Residual: {res}. Restore leftovers before retry. {p['catalog']}"), "runbook"),
        _step(12, f"Plan: extra tests {test} + tests/test_schema.py.", _bash(f"pytest -q {test} tests/test_schema.py"), "4 passed"),
        _step(13, "Tool call: leftover catalog objects after abort.",
               _bash(f"rg '{leftover}|{leftover2}|{col_v2}' || echo none-in-rewrite-path"), "none in rewrite path; dual objects remain as residual"),
        _step(14, f"Plan: checksum {col} vs {col_v2}; confirm leftover catalog objects still dual.",
               _bash(f"python {checksum}"), f"mismatch 0 on backfilled rows; dual residual {res}"),
        _step(15, f"Plan: confirm no active locks/mutations on {sname}.", _bash(inspect_cmd), "0 blockers; dual objects still present"),
        _step(16, f"Plan: stamp schema version {ver}.", _bash(f"echo {ver}"), str(ver)),
    ]
    ep = {
        "id": eid, "goal": goal, "plan": plan, "steps": steps,
        "outcome": (f"Naive catalog apply failed. Plan change: expand {col_v2} + backfill. Tests 4/4. Residual: {res}."),
        "reward": {"success": True, "apply_fails": 2, "plan_changes": 1, "lock_timeouts": 1, "tests_passed": 4, "cost_steps": 16},
        "meta": {"factory": cfg.FACTORY_SLUG, "round": round_n, "generator": cfg.GENERATOR,
                 "kind": "episode", "plant": p["plant"], "sim_or_real": "designed", "surface": p["surface"]},
    }
    assert_clean(ep)
    if len(steps) != 16:
        raise ValueError(f"{eid} expected 16 steps")
    return ep


bind_import_twin(__name__)
