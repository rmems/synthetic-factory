#!/usr/bin/env python3
"""The dlk pure episode builders over a loaded plant catalog.

These are the ``step``/``success_ep``/``fail_ep``/``notes`` builders carried
over from the legacy ``dlk_rNNNN_leftover3_mill.py`` scripts, with two
cleanups: they take a typed :class:`catalog.Plant` instead of a bare dict, and
the factory/generator literals now come from :mod:`._contract` so the
reviewed prefix home is the single authority. The output records are
byte-for-byte the records the legacy builders produced.

The legacy ``txn`` and ``main`` -- the parts that published raw rounds by
shelling out to ``round_txn.py`` -- are deliberately not carried over. This
module imports no subprocess, defines no ``main``, and writes nothing: it only
builds records in memory for a caller to inspect. That is the "never exec"
contract for this lane; :mod:`tests.test_dlk_mill` pins it by AST-scanning this
file's source.
"""

from __future__ import annotations

from typing import Any

from . import _contract as c
from . import catalog as cat
from ._contract import bind_import_twin

N_SUCCESS_STEPS = 16
N_FAIL_STEPS = 17

__all__ = [
    "N_FAIL_STEPS", "N_SUCCESS_STEPS", "fail_ep", "notes", "step", "success_ep",
]


def step(n: int, basis: str, name: str, args: dict[str, Any], obs: str,
         reflection: str | None = None) -> dict[str, Any]:
    s = {
        "n": n,
        "decision_basis": basis,
        "tool_call": {"name": name, "args": args},
        "observation": obs,
    }
    if reflection:
        s["reflection"] = reflection
    return s


def success_ep(rnd: int, plant: cat.Plant) -> dict[str, Any]:
    src, test, seed = plant.src, plant.test, plant.seed
    leftover = plant.leftover_fn
    steps = [
        step(1, f"Plan: inspect {seed} vs drop without leftover fence before any retry.", "bash",
             {"command": f"rg -n '{plant.probe}' src tests | head -n 40"},
             f"{src}: {plant.bad}\n{test}: test exclusive leftover fence"),
        step(2, f"Observation: {plant.bad} in {src} (step 1). Read source.", "read",
             {"path": src}, plant.bad),
        step(3, "Observation: leftover fence unused (step 2). Read gate test.", "read",
             {"path": test},
             f"def test_{plant.slug.replace('-', '_')}_exclusive(env):\n    a=acquire(); b=acquire()\n    assert a and not b"),
        step(4, "Observation: exclusive assertion (step 3). Run gate.", "bash",
             {"command": f"pytest {test}::test_{plant.slug.replace('-', '_')}_exclusive -q --tb=short 2>&1 | tail -n 16"},
             f"FAILED both acquired via {plant.bad}\n0 passed, 1 failed"),
        step(5, f"Observation: not exclusive (step 4). Dump with {plant.cli}.", "bash",
             {"command": plant.dump}, "leftover fence missing; drop raced"),
        step(6, "Plan: first apply \u2014 retry 3600s still using drop without leftover fence.", "edit",
             {"path": src, "old": "    ok = acquire()\n",
              "new": "    deadline=time.time()+3600\n    ok=False\n    while time.time()<deadline and not ok:\n        ok = acquire()\n"},
             f"3600s retry; still {plant.bad}"),
        step(7, "Observation: hour stretch (step 6). Re-run tests.", "bash",
             {"command": f"pytest {test} -q --tb=short 2>&1 | tail -n 16"},
             f"FAILED test_no_hour_loop +3600\nFAILED still {plant.bad}\n0 passed, 2 failed",
             reflection=f"Hour retry banned. Replace {plant.bad} with leftover fence vs drop."),
        step(8, f"Reflection: plan change \u2014 {plant.fix}.", "write",
             {"path": src, "contents": plant.fix + "\n"}, "leftover fence vs drop landed"),
        step(9, "Observation: fix landed (step 8). Re-run gate.", "bash",
             {"command": f"pytest {test} -q --tb=short 2>&1 | tail -n 12"},
             "4 passed in 0.16s"),
        step(10, "Observation: 4/4 (step 9). Full suite for leftover drop helper.", "bash",
             {"command": "pytest tests -q --tb=line 2>&1 | tail -n 12"},
             f"4 passed, leftover {leftover} already gated"),
        step(11, f"Observation: leftover helper {leftover} (step 10). Confirm {plant.ok_pat}.", "grep",
             {"path": src, "pattern": plant.ok_pat}, f"{plant.ok_pat} present"),
        step(12, "Observation: fence token present (step 11). Confirm no hour stretch.", "grep",
             {"path": src, "pattern": "3600"}, "(no matches)"),
        step(13, "Observation: no hour stretch (step 12). Confirm leftover drop compares token.", "read",
             {"path": src}, f"{plant.fix}; drop compares leftover fence"),
        step(14, "Observation: drop path fenced (step 13). Re-run exclusive+drop tests.", "bash",
             {"command": f"pytest {test} -q --tb=line 2>&1 | tail -n 6"},
             "4 passed"),
        step(15, "Observation: all green (step 14). Confirm uuid fence identity.", "grep",
             {"path": src, "pattern": "uuid"}, "uuid leftover fence present"),
        step(16, "Observation: leftover fencing vs drop complete (step 15).", "read",
             {"path": src}, f"{plant.fix}; no hour retry; drop gated",
             reflection=f"{seed}: drop only if leftover fence still matches."),
    ]
    return {
        "id": f"dlk-r{rnd:04d}-{plant.slug}",
        "goal": (
            f"bolt leftover leftover leftover: {seed}. {plant.why} "
            f"Do not retry 3600s. Tests in {test} are the gate."
        ),
        "plan": f"Retry {plant.bad} for 3600s until exclusive.",
        "steps": steps,
        "outcome": (
            f"{plant.bad} was not exclusive. {plant.why} 3600s retry banned. "
            f"Plan change: {plant.fix}. Gate tests 4/4. leftover drop gated."
        ),
        "reward": {"success": True, "plan_changes": 1, "tests_passed": 4, "cost_steps": 16},
        "meta": {"factory": c.FACTORY, "round": rnd, "generator": c.GEN},
    }


def fail_ep(rnd: int, plant: cat.Plant) -> dict[str, Any]:
    src, test = plant.src, plant.test
    leftover = plant.leftover_fn
    fail_test = test.replace(".py", f"_{leftover}.py")
    steps = [
        step(1, f"Plan: inspect fail path {plant.fail_slug} leftover drop.", "bash",
             {"command": f"rg -n '{leftover}' src tests | head -n 40"},
             f"{src}: {leftover} still {plant.bad}\n{fail_test}: gate leftover drop"),
        step(2, f"Observation: leftover drop helper (step 1). Read {src}.", "read",
             {"path": src}, f"def {leftover}():\n    {plant.bad}"),
        step(3, "Observation: drop ignores leftover fence (step 2). Read fail test.", "read",
             {"path": fail_test},
             f"def test_{leftover}_not_racy(env):\n    assert drop_uses_leftover_fence()"),
        step(4, "Observation: leftover drop assertion (step 3). Run it.", "bash",
             {"command": f"pytest {fail_test} -q --tb=short 2>&1 | tail -n 16"},
             f"FAILED {plant.fail_why}\n0 passed, 1 failed"),
        step(5, f"Observation: leftover drop racy (step 4). Dump {plant.cli}.", "bash",
             {"command": plant.dump}, "leftover fence still live after drop"),
        step(6, "Plan: first apply \u2014 hour retry around leftover drop.", "edit",
             {"path": src, "old": f"    {leftover}()\n",
              "new": "    deadline=time.time()+3600\n    while time.time()<deadline:\n        "
              + leftover + "()\n"},
             f"3600s retry; still {leftover}"),
        step(7, "Observation: hour stretch (step 6). Re-run fail tests.", "bash",
             {"command": f"pytest {fail_test} {test} -q --tb=short 2>&1 | tail -n 16"},
             "FAILED test_no_hour_loop\nFAILED leftover drop\n0 passed, 2 failed",
             reflection="Hour retry banned. Must fence leftover drop or handoff."),
        step(8, f"Reflection: try {plant.fix} only on acquire, leave {leftover}.", "write",
             {"path": src, "contents": plant.fix + f"\n# {leftover} still {plant.bad}\n"},
             "acquire fenced; leftover drop unchanged"),
        step(9, "Observation: acquire gated (step 8). Re-run acquire tests.", "bash",
             {"command": f"pytest {test} -q --tb=short 2>&1 | tail -n 12"},
             "3 passed in 0.14s"),
        step(10, "Observation: acquire green (step 9). Full suite leftover drop.", "bash",
             {"command": "pytest tests -q --tb=line 2>&1 | tail -n 12"},
             f"FAILED {fail_test} leftover drop still racy\n6 passed, 1 failed"),
        step(11, "Observation: leftover drop still racy (step 10). Ticket allows handoff. xfail.", "edit",
             {"path": fail_test, "old": f"def test_{leftover}_not_racy(",
              "new": f"@pytest.mark.xfail(reason=\"handoff: {leftover} still {plant.bad}\", strict=False)\ndef test_{leftover}_not_racy("},
             f"xfails {leftover}"),
        step(12, f"Observation: leftover xfails (step 11). Confirm {plant.ok_pat} on acquire only.", "grep",
             {"path": src, "pattern": plant.ok_pat}, f"{plant.ok_pat} on acquire; {leftover} unfenced"),
        step(13, "Observation: split (step 12). Re-run gate+leftover.", "bash",
             {"command": f"pytest {test} {fail_test} -q --tb=line 2>&1 | tail -n 6"},
             "3 passed, 1 xfailed"),
        step(14, "Observation: gate green leftover xfail (step 13). Confirm uuid on acquire.", "grep",
             {"path": src, "pattern": "uuid"}, "uuid on acquire path"),
        step(15, "Observation: exclusive acquire (step 14). Confirm no hour stretch.", "grep",
             {"path": src, "pattern": "3600"}, "(no matches)"),
        step(16, f"Observation: no hour stretch (step 15). Residual is {leftover}().", "read",
             {"path": src}, f"acquire fenced; {leftover} still {plant.bad}"),
        step(17, "Observation: handoff leftover drop (step 16). Record partial.", "bash",
             {"command": f"pytest {fail_test} -q --tb=line 2>&1 | tail -n 4"},
             "1 xfailed",
             reflection=f"{plant.fail_why} Handoff leftover drop."),
    ]
    return {
        "id": f"dlk-r{rnd:04d}-{plant.fail_slug}",
        "goal": (
            f"bolt leftover leftover leftover fail: {plant.fail_slug}. {plant.fail_why} "
            f"Do not retry 3600s. Distinct from acquire leftover fence. Tests in {fail_test}."
        ),
        "plan": f"Retry {leftover} for 3600s until drop is exclusive.",
        "steps": steps,
        "outcome": (
            f"{plant.fail_why} 3600s retry banned. Acquire fenced via {plant.fix}. "
            f"Gate tests 3/3. Partial: {leftover} still {plant.bad} (xfail handoff)."
        ),
        "reward": {
            "success": False,
            "plan_changes": 1,
            "tests_passed": 3,
            "xfailed": 1,
            "handoff": 1,
            "cost_steps": 17,
        },
        "meta": {"factory": c.FACTORY, "round": rnd, "generator": c.GEN},
    }


def notes(rnd: int, plant: cat.Plant, s: dict[str, Any], f: dict[str, Any]) -> str:
    return f"""# NOTES-r{rnd:04d} distributed-lock-factory

Novel coverage: leftover leftover leftover fencing vs drop for **{plant.seed}**. Distinct lock product; not noun cartesian; not redis-exists-then-set / etcd-serializable-get / zk-exists-then-create / k8s-configmap-as-lease / ddb-update-add-version / s3-copy-no-if-match / flock-nfs-home / pg-discard-all / mysql-is-free-then-get / consul-stale-get.

| id | seed | first apply | plan change | terminal |
|---|---|---|---|---|
| {s['id']} | {plant.seed} | retry 3600s on {plant.bad} | {plant.fix} | success leftover drop gated |
| {f['id']} | leftover drop | retry 3600s on {plant.leftover_fn} | acquire fenced, drop leftover | partial xfail handoff |

## Step counts
- success: 16. first-apply fail 7; plan change 8.
- fail/handoff: 17. first-apply fail 7; plan change 8; xfail leftover drop 11; handoff 17.

## decision_basis audit
Every step starts Plan:/Observation:/Reflection:. No thought/CoT. No spike_events. No sim_or_real: real. Invented plant `bolt`.
"""


bind_import_twin(__name__)
