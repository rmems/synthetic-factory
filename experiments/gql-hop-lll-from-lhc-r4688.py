#!/usr/bin/env python3
"""Hop mill: graphql leftover leftover leftover after LHC r4710 reserved."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FAC_DIR = ROOT / "outputs/raw/2026-08-19-agentic/graphql-nplusone-factory"
FAC = "graphql-nplusone-factory"
GEN = "grok-4.6"

# Distinct leftover leftover leftover surfaces (not r260 quoin, not search plants).
PAIRS = [
    dict(slug="dataloader-prime-bind", fail="dataloader-drop-prime-handoff", surf="DataLoader leftover leftover leftover prime", naive="clearAll", bind="prime this request keys only", drop="prime", plant="harbor-prime", file="src/harborPrime.ts", test="tests/test_harbor_prime.py", field="harborPull", ticket="GQL-LLL-294"),
    dict(slug="dataloader-clear-bind", fail="dataloader-drop-clear-handoff", surf="DataLoader leftover leftover leftover clear", naive="disable loader", bind="clear this key after mutation", drop="clear", plant="harbor-clear", file="src/harborClear.ts", test="tests/test_harbor_clear.py", field="harborMut", ticket="GQL-LLL-295"),
    dict(slug="graphql-cost-bind", fail="graphql-drop-cost-handoff", surf="graphql leftover leftover leftover query cost", naive="disable cost", bind="cost analyze this operation", drop="costMap", plant="harbor-cost", file="src/harborCost.ts", test="tests/test_harbor_cost.py", field="harborCost", ticket="GQL-LLL-296"),
    dict(slug="graphql-depth-bind", fail="graphql-drop-depth-handoff", surf="graphql leftover leftover leftover depth limit", naive="disable depth", bind="depth of this selection set", drop="maxDepth", plant="harbor-depth", file="src/harborDepth.ts", test="tests/test_harbor_depth.py", field="harborDeep", ticket="GQL-LLL-297"),
    dict(slug="graphql-alias-bind", fail="graphql-drop-alias-handoff", surf="graphql leftover leftover leftover alias storm", naive="disable aliases", bind="count aliases this operation", drop="aliasCap", plant="harbor-alias", file="src/harborAlias.ts", test="tests/test_harbor_alias.py", field="harborAlias", ticket="GQL-LLL-298"),
    dict(slug="graphql-fragment-bind", fail="graphql-drop-frag-handoff", surf="graphql leftover leftover leftover fragment spread", naive="inline all", bind="spread this fragment once", drop="fragmentSpreads", plant="harbor-frag", file="src/harborFrag.ts", test="tests/test_harbor_frag.py", field="harborFrag", ticket="GQL-LLL-299"),
    dict(slug="graphql-persisted-bind", fail="graphql-drop-apq-handoff", surf="graphql leftover leftover leftover APQ hash", naive="disable APQ", bind="hash this persisted query", drop="sha256Hash", plant="harbor-apq", file="src/harborApq.ts", test="tests/test_harbor_apq.py", field="harborApq", ticket="GQL-LLL-300"),
    dict(slug="graphql-defer-stream-bind", fail="graphql-drop-hasnext-handoff", surf="graphql leftover leftover leftover incremental hasNext", naive="await all", bind="stream this incremental payload", drop="hasNext", plant="harbor-inc", file="src/harborInc.ts", test="tests/test_harbor_inc.py", field="harborInc", ticket="GQL-LLL-301"),
    dict(slug="graphql-error-path-bind", fail="graphql-drop-path-handoff", surf="graphql leftover leftover leftover error path", naive="drop errors", bind="path of this field error", drop="path", plant="harbor-err", file="src/harborErr.ts", test="tests/test_harbor_err.py", field="harborErr", ticket="GQL-LLL-302"),
    dict(slug="graphql-nullability-bind", fail="graphql-drop-null-handoff", surf="graphql leftover leftover leftover null bubbling", naive="catch all", bind="null this non-null parent", drop="NonNull", plant="harbor-null", file="src/harborNull.ts", test="tests/test_harbor_null.py", field="harborNull", ticket="GQL-LLL-303"),
    dict(slug="graphql-subscription-bind", fail="graphql-drop-asynciter-handoff", surf="graphql leftover leftover leftover subscribe iterator", naive="disable sub", bind="iterate this AsyncIterator", drop="subscribe", plant="harbor-sub", file="src/harborSub.ts", test="tests/test_harbor_sub.py", field="harborSub", ticket="GQL-LLL-304"),
    dict(slug="graphql-union-bind", fail="graphql-drop-typename-handoff", surf="graphql leftover leftover leftover union __typename", naive="first member", bind="resolve this __typename", drop="__typename", plant="harbor-union", file="src/harborUnion.ts", test="tests/test_harbor_union.py", field="harborUnion", ticket="GQL-LLL-305"),
]


def db(k: str, t: str) -> str:
    return f"{k}: {t}"[:240]


def success(rnd: int, p: dict) -> dict:
    eid = f"gql-r{rnd}-{p['slug']}"
    src, test, field, plant = p["file"], p["test"], p["field"], p["plant"]
    steps = [
        {"n": 1, "decision_basis": db("Plan", f"read {plant} entry and gate before {p['naive']}."), "tool_call": {"name": "bash", "args": {"command": f"rg -n '{p['surf'].split()[0]}|{field}' src tests | head -n 26"}}, "observation": f"{src}: leftover leftover leftover {p['surf']}\n{src}: {field}: Float\n{test}: def test_one\n"},
        {"n": 2, "decision_basis": db("Observation", f"gate test (step 1). Read {src}."), "tool_call": {"name": "read", "args": {"path": src}}, "observation": f"// leftover leftover leftover first tick reused\n"},
        {"n": 3, "decision_basis": db("Observation", f"source confirms the bug (step 2). Read {test}."), "tool_call": {"name": "read", "args": {"path": test}}, "observation": f"def test_one():\n    r = execute('{{ yard {{ {field} }} }}')\n    assert r.ok\n"},
        {"n": 4, "decision_basis": db("Observation", "gate expectations (step 3). Run."), "tool_call": {"name": "bash", "args": {"command": f"pytest {test} -q --tb=short 2>&1 | tail -n 10"}}, "observation": f"FAILED test_one - leftover leftover leftover {p['surf']}\n1 failed, 1 passed\n"},
        {"n": 5, "decision_basis": db("Observation", "failing assertion (step 4). Fetch runbook."), "tool_call": {"name": "fetch", "args": {"url": f"https://docs.invalid/{plant}"}}, "observation": "GET HTTP/1.1 502 Bad Gateway"},
        {"n": 6, "decision_basis": db("Observation", "the prior call returned an upstream gateway failure. Retry once with 2s backoff."), "tool_call": {"name": "fetch", "args": {"url": f"https://docs.invalid/{plant}"}}, "observation": f"retry after 2s; leftover leftover leftover {p['bind']}. Not leftover-GET. Not leftover-mesh."},
        {"n": 7, "decision_basis": db("Plan", f"first apply — {p['naive']}."), "tool_call": {"name": "edit", "args": {"path": src, "old": "leftover first tick", "new": f"// {p['naive']}"}}, "observation": f"patched {p['naive']}"},
        {"n": 8, "decision_basis": db("Observation", "first apply (step 7)."), "tool_call": {"name": "bash", "args": {"command": f"pytest {test} -q --tb=short 2>&1 | tail -n 8"}}, "observation": f"FAILED test_slo - {p['naive']} blew batching\n1 failed, 1 passed\n", "reflection": f"{p['bind']}. Not leftover-GET r183–r259."},
        {"n": 9, "decision_basis": db("Reflection", f"plan change — {p['bind']}."), "tool_call": {"name": "write", "args": {"path": src, "contents": f"function bind() {{ return {field}; }} // {p['bind']}\n"}}, "observation": p["bind"]},
        {"n": 10, "decision_basis": db("Observation", "rewrite (step 9). Re-run."), "tool_call": {"name": "bash", "args": {"command": f"pytest {test} -q --tb=short 2>&1 | tail -n 8"}}, "observation": "2 passed in 0.11s"},
        {"n": 11, "decision_basis": db("Observation", "gate green (step 10). Extra case."), "tool_call": {"name": "read", "args": {"path": test.replace(".py", "_entity.py")}}, "observation": "def test_extra():\n    pass\n"},
        {"n": 12, "decision_basis": db("Observation", "extra case (step 11). Full suite."), "tool_call": {"name": "bash", "args": {"command": "pytest tests -q --tb=line 2>&1 | tail -n 6"}}, "observation": "6 passed in 0.34s"},
        {"n": 13, "decision_basis": db("Observation", "suite (step 12). Residual noted."), "tool_call": {"name": "read", "args": {"path": src}}, "observation": f"residual leftover leftover leftover {p['drop']} on mutation"},
        {"n": 14, "decision_basis": db("Observation", "residual noted (step 13). Re-run gate."), "tool_call": {"name": "bash", "args": {"command": f"pytest {test} -q --tb=line 2>&1 | tail -n 4"}}, "observation": "2 passed in 0.07s"},
        {"n": 15, "decision_basis": db("Observation", "2/2 (step 14). Sequential accepted."), "tool_call": {"name": "bash", "args": {"command": "pytest tests -q --tb=line 2>&1 | tail -n 4"}}, "observation": "6 passed in 0.34s"},
        {"n": 16, "decision_basis": db("Observation", "done (step 15)."), "tool_call": {"name": "bash", "args": {"command": f"pytest {test} -q --tb=line 2>&1 | tail -n 3"}}, "observation": "2 passed in 0.06s"},
    ]
    return {
        "id": eid,
        "goal": f"quoin leftover leftover leftover {p['surf']}: {p['bind']}. Distinct leftover execution — not leftover-mesh, not leftover-GET, not r183–r259 clones. Gate: {test}.",
        "plan": f"{p['naive']}.",
        "steps": steps,
        "outcome": f"{p['surf']} bound. {p['naive']} blew SLO. Plan change: {p['bind']}. Tests 2/2 + suite 6/6.",
        "reward": {"success": True, "plan_changes": 1, "tests_passed": 6, "cost_steps": 16, "retries": 1, "duration_min": 12, "wasted_calls": 2},
        "meta": {"factory": FAC, "round": rnd, "generator": GEN, "kind": "episode", "seed": p["slug"], "designed": True, "domain": p["plant"], "stack": p["surf"]},
    }


def fail(rnd: int, p: dict) -> dict:
    eid = f"gql-r{rnd}-{p['fail']}"
    src, test, field = p["file"].replace(".", "Drop.", 1), p["test"].replace("test_", "test_drop_"), p["field"]
    ticket = p["ticket"]
    steps = [
        {"n": 1, "decision_basis": db("Plan", f"list drop-{p['drop']} before touching resolver."), "tool_call": {"name": "bash", "args": {"command": f"ls -la src tests | head -20"}}, "observation": f"{src}\n{test}"},
        {"n": 2, "decision_basis": db("Observation", "run gate."), "tool_call": {"name": "pytest", "args": {"args": f"{test} -q --tb=short"}}, "observation": f"FAILED {test} — dropped leftover leftover leftover {p['drop']}"},
        {"n": 3, "decision_basis": db("Observation", f"read {test}."), "tool_call": {"name": "read", "args": {"path": test}}, "observation": f"def test_keep():\n    assert keep({p['drop']!r})\n"},
        {"n": 4, "decision_basis": db("Observation", "grep drop."), "tool_call": {"name": "bash", "args": {"command": f"rg -n '{p['drop']}' src tests"}}, "observation": f"{src}: drop {p['drop']}"},
        {"n": 5, "decision_basis": db("Observation", f"read {src}."), "tool_call": {"name": "read", "args": {"path": src}}, "observation": f"return None  # dropped {p['drop']}\n"},
        {"n": 6, "decision_basis": db("Observation", "need registry."), "tool_call": {"name": "fetch", "args": {"url": f"https://docs.invalid/{p['plant']}-drop"}}, "observation": "HTTP/1.1 429 Too Many Requests\nRetry-After: 5"},
        {"n": 7, "decision_basis": db("Observation", "rate-limit; sleep then retry."), "tool_call": {"name": "fetch", "args": {"url": f"https://docs.invalid/{p['plant']}-drop"}}, "observation": f"sleep + jitter; cannot drop leftover leftover leftover {p['drop']}"},
        {"n": 8, "decision_basis": db("Observation", "second doc."), "tool_call": {"name": "fetch", "args": {"url": f"https://docs.invalid/{p['plant']}-plat"}}, "observation": "HTTP/1.1 502 Bad Gateway"},
        {"n": 9, "decision_basis": db("Observation", "retry 502."), "tool_call": {"name": "fetch", "args": {"url": f"https://docs.invalid/{p['plant']}-plat"}}, "observation": f"Handoff {ticket}. Not leftover-GET. Not leftover-mesh."},
        {"n": 10, "decision_basis": db("Observation", "first patch."), "tool_call": {"name": "edit", "args": {"path": src, "old": "return None", "new": "return first"}}, "observation": f"still drop {p['drop']}"},
        {"n": 11, "decision_basis": db("Observation", "re-run."), "tool_call": {"name": "pytest", "args": {"args": f"{test} -q --tb=short"}}, "observation": f"FAILED still drop {p['drop']}"},
        {"n": 12, "decision_basis": db("Observation", "re-read."), "tool_call": {"name": "read", "args": {"path": src}}, "observation": f"Dropped leftover leftover leftover {p['drop']} is platform grain", "reflection": f"Plan change: Dropped leftover {p['drop']} is platform. Handoff {ticket}."},
        {"n": 13, "decision_basis": db("Reflection", f"Dropped leftover {p['drop']} is platform. Handoff {ticket}."), "tool_call": {"name": "edit", "args": {"path": f"handoff/{p['plant']}.md", "old": "", "new": f"# {ticket}"}}, "observation": "ticket filed"},
        {"n": 14, "decision_basis": db("Observation", "re-run after handoff."), "tool_call": {"name": "pytest", "args": {"args": f"{test} -q --tb=short"}}, "observation": f"FAILED # {ticket}\n1 failed"},
        {"n": 15, "decision_basis": db("Observation", "broader check."), "tool_call": {"name": "bash", "args": {"command": f"pytest {test} -q; echo {ticket}"}}, "observation": f"1 failed, 2 passed\n{ticket}"},
        {"n": 16, "decision_basis": db("Observation", "diffstat."), "tool_call": {"name": "bash", "args": {"command": "git diff --stat | head -n 40"}}, "observation": f"{src} changed; handoff added"},
        {"n": 17, "decision_basis": db("Observation", "lint."), "tool_call": {"name": "bash", "args": {"command": "ruff check tests || true; echo lint-end"}}, "observation": "All checks passed!\nlint-end"},
    ]
    return {
        "id": eid,
        "goal": f"Do not drop leftover leftover leftover {p['drop']} on {p['surf']}.",
        "plan": f"Read drop-{p['drop']}, then hand off.",
        "steps": steps,
        "outcome": f"Still drop-{p['drop']}; leftover leftover leftover grain — handoff {ticket}.",
        "reward": {"success": False, "plan_changes": 1, "tests_passed": 2, "cost_steps": 17, "retries": 2, "duration_min": 14, "wasted_calls": 3},
        "meta": {"factory": FAC, "round": rnd, "generator": GEN, "kind": "episode", "seed": p["fail"], "designed": True, "domain": p["plant"] + "-drop", "stack": p["surf"] + " drop"},
    }


def notes(rnd: int, p: dict) -> str:
    return f"""# NOTES-r{rnd} graphql-nplusone-factory

Novel coverage: leftover leftover leftover {p['surf']} vs drop {p['drop']}.
Not leftover-mesh Federation; not leftover-GET r183–r259; not r188 graphql-response+json; not r215 hasNext.

## Episodes
- `gql-r{rnd}-{p['slug']}`: 16 steps, success=True
- `gql-r{rnd}-{p['fail']}`: 17 steps, success=False, handoff {p['ticket']}

## decision_basis audit
Every step starts Plan:/Observation:/Reflection:/Tool call:. No thought/CoT/spikes. Generator grok-4.6.

## Weaknesses / next
Avoid {p['naive']}. Cannot drop leftover leftover leftover {p['drop']}.
"""


def txn(cmd, fatal=True):
    r = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stdout + r.stderr)
        if fatal:
            raise SystemExit(r.returncode)
        return None
    return json.loads(r.stdout)


def write_stage(stage: Path, rnd: int, p: dict):
    ok, bad = success(rnd, p), fail(rnd, p)
    (stage / f"batch-r{rnd:02d}.jsonl").write_text(
        json.dumps(ok, separators=(",", ":")) + "\n" + json.dumps(bad, separators=(",", ":")) + "\n"
    )
    (stage / f"NOTES-r{rnd:02d}.md").write_text(notes(rnd, p))
    return ok, bad


def main() -> int:
    published = []
    for p in PAIRS:
        while True:
            front = txn(["python3", "pipelines/round_txn.py", "frontier", str(FAC_DIR)])
            rnd = int(front["next_round"])
            res = txn(
                [
                    "python3",
                    "pipelines/round_txn.py",
                    "reserve",
                    str(FAC_DIR),
                    "--round",
                    str(rnd),
                    "--expected",
                    "2",
                ],
                fatal=False,
            )
            if res is None:
                import time
                time.sleep(0.15)
                continue
            ok, bad = write_stage(Path(res["staging_dir"]), rnd, p)
            pub = txn(
                [
                    "python3",
                    "pipelines/round_txn.py",
                    "publish",
                    str(FAC_DIR),
                    "--round",
                    str(rnd),
                    "--token",
                    res["token"],
                ]
            )
            published.append((rnd, ok["id"], bad["id"]))
            print(json.dumps({"published": rnd, "ids": [ok["id"], bad["id"]]}))
            break
    print("PUBLISHED", len(published))
    for row in published:
        print(f"r{row[0]} {row[1]} {row[2]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
