#!/usr/bin/env python3
"""Build leftover3 dbm episodes from the pinned catalog.

The 16-step expand-and-backfill shape is AST-extracted from
``unique_dbm_leftover3_mill.py``. This module never imports that mill.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

if __name__.startswith("pipelines."):
    from ..db_episode_scaffold import (
        EpisodeAssembly,
        assemble_episode,
        bash as _bash,
        step as _shared_step,
        write as _write,
    )
else:
    from db_episode_scaffold import (
        EpisodeAssembly,
        assemble_episode,
        bash as _bash,
        step as _shared_step,
        write as _write,
    )

from ._contract import (
    BANNED_KEYS,
    COVERAGE_FLOOR,
    FACTORY,
    FAMILY_PREFIX,
    FINDING_GENERATE_GOAL,
    FINDING_GENERATE_HIDDEN,
    FINDING_GENERATE_SHAPE,
    GENERATOR,
    START_ROUND,
    SUCCESS_STEPS,
    bind_import_twin,
    contains_hidden_reasoning_key,
    dumps_exact_json,
    refuse_when,
)

RECYCLE_SUFFIX = re.compile(r"-r\d+$")
PLACEHOLDER_GOALS = frozenset({"", "x", "placeholder", "todo", "tbd", "fix it"})

__all__ = [
    "build_episode",
    "coverage_for",
    "dumps_episode",
    "expand_sql",
    "lock_sql",
    "residual",
    "short_name",
    "stem",
]


def residual(plant: Mapping[str, str]) -> str:
    table = plant["table"].split(".")[-1]
    return (
        f"{table}.{plant['col']} + {plant['col_v2']}; leftover leftover leftover "
        f"{plant['leftover']}; leftover {plant['leftover2']}"
    )


def short_name(plant: Mapping[str, str]) -> str:
    return plant["table"].split(".")[-1]


def stem(plant: Mapping[str, str]) -> str:
    return plant["slug"].replace("-", "_")


def expand_sql(plant: Mapping[str, str]) -> str:
    return f"ALTER TABLE {plant['table']} ADD COLUMN {plant['col_v2']} {plant['col_type']}"


def lock_sql(plant: Mapping[str, str]) -> str:
    return (
        f"SET lock_timeout='8s'; ALTER TABLE {plant['table']} "
        f"ADD COLUMN IF NOT EXISTS {plant['col_v2']} {plant['col_type']}"
    )


def coverage_for(round_n: int) -> int:
    return min(96, COVERAGE_FLOOR + (round_n - START_ROUND) * 2)


def dumps_episode(episode: dict[str, Any]) -> str:
    return dumps_exact_json(episode, ensure_ascii=False, sort_keys=True)


def _step(n: int, basis: str, tool: dict[str, Any], observation: str) -> dict[str, Any]:
    refuse_when(not basis.strip(), FINDING_GENERATE_SHAPE, f"step {n} empty decision_basis")
    refuse_when(not observation.strip(), FINDING_GENERATE_SHAPE, f"step {n} empty observation")
    return _shared_step(n, basis, tool, observation)


def _assert_clean(obj: Any, path: str = "") -> None:
    if isinstance(obj, dict):
        for key, value in obj.items():
            refuse_when(key in BANNED_KEYS, FINDING_GENERATE_HIDDEN, f"banned key {key} at {path}")
            refuse_when(
                key == "sim_or_real" and value == "real",
                FINDING_GENERATE_HIDDEN,
                f"sim_or_real real at {path}",
            )
            refuse_when(key == "spike_events", FINDING_GENERATE_HIDDEN, f"spike_events at {path}")
            _assert_clean(value, f"{path}.{key}")
        return
    if isinstance(obj, list):
        for index, item in enumerate(obj):
            _assert_clean(item, f"{path}[{index}]")


def _goal_ok(goal: str) -> str:
    refuse_when(not goal.strip(), FINDING_GENERATE_GOAL, "empty goal")
    refuse_when(
        goal.strip().lower() in PLACEHOLDER_GOALS,
        FINDING_GENERATE_GOAL,
        f"placeholder goal: {goal!r}",
    )
    refuse_when(
        "[variant" in goal.lower(),
        FINDING_GENERATE_GOAL,
        f"variant stamp in goal: {goal!r}",
    )
    return goal


def build_episode(round_n: int, plant: Mapping[str, str], slot: int) -> dict[str, Any]:
    ver = 2500 + (round_n - START_ROUND) * 2 + slot
    slug = plant["slug"]
    table = plant["table"]
    col = plant["col"]
    col_v2 = plant["col_v2"]
    leftover = plant["leftover"]
    leftover2 = plant["leftover2"]
    res = residual(plant)
    sname = short_name(plant)
    st = stem(plant)
    mig = f"migrations/{ver}_{st}.sql"
    down = f"migrations/{ver}_{st}.down.sql"
    test = f"tests/test_{st}.py"
    runbook = f"docs/{slug}.md"
    backfill = f"jobs/backfill_{st}.py"
    checksum = f"jobs/checksum_{st}.py"
    inspect_cmd = plant["inspect"]
    seed_cmd = plant["seed"]
    abort_cmd = plant["abort"]
    lock_cmd = f'psql -X -c "{lock_sql(plant)}"'
    lock_fail = plant.get("lock_fail") or f"ERROR: lock timeout ADD {col_v2} on {table}"
    expand = expand_sql(plant)
    inspect_obs = (
        f"{table} present\n"
        f"pending: {plant['fail']}\n"
        f"shape now: {res}\n"
        f"catalog: {plant['catalog']}\n"
        f"locks/mutations: 1 active; dual leftover leftover leftover objects"
    )
    eid = f"{FAMILY_PREFIX}-r{round_n}-{slug}"
    refuse_when(
        bool(RECYCLE_SUFFIX.search(eid)),
        FINDING_GENERATE_SHAPE,
        f"recycle suffix in id: {eid}",
    )
    goal = _goal_ok(
        f"{plant['plant']}: {plant['engine']} {seed_cmd} on {table}.{col} failed "
        f"({plant['fail'][:140]}). Expand {col_v2}, backfill, residual {res}."
    )
    plan = (
        f"Abort in-place rewrite; expand-contract via {expand}; keep {col}; "
        f"dual leftover leftover leftover objects."
    )
    steps = [
        _step(
            1,
            f"Plan: inspect {plant['engine']} leftover leftover leftover catalog for {table} "
            f"before apply {ver} ({slug}).",
            _bash(inspect_cmd),
            inspect_obs,
        ),
        _step(
            2,
            f"Plan: apply naive leftover leftover leftover change on {table}.{col}.",
            _bash(seed_cmd),
            plant["fail"],
        ),
        _step(
            3,
            f"Observation: first apply failed ({plant['fail'][:90]}). Plan change: abort "
            f"in-place rewrite; expand {col_v2} + backfill; leave {col} residual.",
            _bash(abort_cmd),
            "leftovers leftover leftover leftover dropped or cancelled; naive rewrite aborted; "
            "dual objects still planned",
        ),
        _step(
            4,
            f"Plan: write expand-only migration {ver} adding {col_v2} (keep {col}).",
            _write(
                mig,
                f"-- {ver} expand {table} {col_v2}\n{expand};\n"
                f"-- never drop {col}; leftover leftover leftover residual\n"
                f"-- {plant['catalog']}\n",
            ),
            "expand-only written",
        ),
        _step(
            5,
            f"Plan: apply expand {ver} with short lock timeout.",
            _bash(lock_cmd),
            lock_fail,
        ),
        _step(
            6,
            "Observation: lock timeout on expand. Plan: retry lock timeout off-peak; "
            "ACCESS EXCLUSIVE avoided.",
            _bash(lock_cmd),
            f"ok retry expand {col_v2}",
        ),
        _step(
            7,
            f"Plan: batched backfill {col_v2} from {col} without validating leftover leftover "
            "leftover constraints.",
            _bash(f"python {backfill} --batch 8000 --from {col} --to {col_v2}"),
            f"copied batch ok; remaining 0 on {table}; dual residual {res}",
        ),
        _step(
            8,
            f"Plan: tests {test} (catalog residual must remain).",
            _bash(f"pytest -q {test}"),
            "3 passed",
        ),
        _step(
            9,
            f"Plan: down {ver} must refuse lossy drop of {col_v2}.",
            _write(
                down,
                f"SELECT raise_error('lossy {col_v2} drop; leftover leftover leftover residual "
                f"{sname} must remain');\n",
            ),
            "down v2 guard",
        ),
        _step(10, f"Observation: dual residual {res}.", _bash(inspect_cmd), res),
        _step(
            11,
            "Plan: runbook never in-place rewrite via naive leftover leftover leftover DDL.",
            _write(
                runbook,
                f"Never {seed_cmd}. Expand {col_v2}, backfill, dual-read. Residual: {res}. "
                f"Restore leftovers leftover leftover leftover before retry. {plant['catalog']}",
            ),
            "runbook",
        ),
        _step(
            12,
            f"Plan: extra tests {test} + tests/test_schema.py.",
            _bash(f"pytest -q {test} tests/test_schema.py"),
            "4 passed",
        ),
        _step(
            13,
            "Tool call: leftover leftover leftover catalog objects after abort.",
            _bash(f"rg '{leftover}|{leftover2}|{col_v2}' || echo none-in-rewrite-path"),
            "none in rewrite path; dual leftover leftover leftover objects remain as residual",
        ),
        _step(
            14,
            (
                f"Plan: checksum {col} vs {col_v2}; confirm leftover leftover leftover "
                "objects still dual."
            ),
            _bash(f"python {checksum}"),
            f"mismatch 0 on backfilled rows; dual residual {res}",
        ),
        _step(
            15,
            f"Plan: confirm no active locks/mutations on {sname}.",
            _bash(inspect_cmd),
            "0 blockers; dual leftover leftover leftover objects still present",
        ),
        _step(16, f"Plan: stamp schema version {ver}.", _bash(f"echo {ver}"), str(ver)),
    ]
    refuse_when(
        len(steps) != SUCCESS_STEPS,
        FINDING_GENERATE_SHAPE,
        f"{eid} expected {SUCCESS_STEPS} steps",
    )
    episode = assemble_episode(EpisodeAssembly(
        episode_id=eid,
        goal=goal,
        plan=plan,
        steps=steps,
        outcome=(
            "Naive leftover leftover leftover apply failed. Plan change: "
            f"expand {col_v2} + backfill. Tests 4/4. Residual: {res}."
        ),
        meta={
            "factory": FACTORY,
            "round": round_n,
            "generator": GENERATOR,
            "kind": "episode",
            "plant": plant["plant"],
            "sim_or_real": "designed",
            "surface": plant["surface"],
        },
    ))
    _assert_clean(episode)
    refuse_when(
        contains_hidden_reasoning_key(episode),
        FINDING_GENERATE_HIDDEN,
        f"{eid} carries a hidden-reasoning key",
    )
    return episode


bind_import_twin(__name__)
