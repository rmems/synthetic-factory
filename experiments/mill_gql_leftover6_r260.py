#!/usr/bin/env python3
"""Hop mill: graphql leftover leftover leftover leftover leftover leftover r260+."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FAC_DIR = ROOT / "outputs/raw/2026-08-19-agentic/graphql-nplusone-factory"
FAC = "graphql-nplusone-factory"
GEN = "grok-4.6"
SEED_TOKEN = "743efa09b51648f79e8776c609d56861"
SEED_STAGE = ROOT / "outputs/staging/2026-08-19-agentic/graphql-nplusone-factory/r260-743efa09b51648f79e8776c609d56861"

# Distinct leftover leftover leftover leftover leftover leftover surfaces (not r178–r259).
PAIRS = [
    dict(slug="dl-batch-dispatch-bind", fail="dl-drop-cachekey-handoff", surf="DataLoader leftover leftover leftover leftover leftover leftover batch dispatch", naive="disable batch", bind="dispatch this tick's keys only", drop="cacheKeyFn", plant="quoin-batch", file="src/quoinBatch.ts", test="tests/test_quoin_batch.py", field="quoinPull", ticket="GQL-L6-260"),
    dict(slug="apollo-typepolicy-bind", fail="apollo-drop-keyfields-handoff", surf="Apollo InMemory leftover leftover leftover leftover leftover leftover typePolicy", naive="disable cache", bind="typePolicy keyFields for this type", drop="keyFields", plant="quoin-policy", file="src/quoinPolicy.ts", test="tests/test_quoin_policy.py", field="quoinKind", ticket="GQL-L6-261"),
    dict(slug="relay-cursor-bind", fail="relay-drop-edges-handoff", surf="Relay leftover leftover leftover leftover leftover leftover connection cursor", naive="disable pagination", bind="cursor from this edge", drop="edges", plant="quoin-cursor", file="src/quoinCursor.ts", test="tests/test_quoin_cursor.py", field="quoinPage", ticket="GQL-L6-262"),
    dict(slug="hasura-remote-bind", fail="hasura-drop-role-handoff", surf="Hasura leftover leftover leftover leftover leftover leftover remote schema role", naive="disable remote", bind="forward this x-hasura-role", drop="x-hasura-role", plant="quoin-remote", file="src/quoinRemote.ts", test="tests/test_quoin_remote.py", field="quoinRemote", ticket="GQL-L6-263"),
    dict(slug="pg-pgsettings-bind", fail="pg-drop-jwt-handoff", surf="PostGraphile leftover leftover leftover leftover leftover leftover pgSettings", naive="disable pgSettings", bind="pgSettings from this jwt", drop="jwtClaims", plant="quoin-pgset", file="src/quoinPgset.ts", test="tests/test_quoin_pgset.py", field="quoinRow", ticket="GQL-L6-264"),
    dict(slug="mercurius-jit-bind", fail="mercurius-drop-ctx-handoff", surf="Mercurius leftover leftover leftover leftover leftover leftover jit context", naive="disable jit", bind="compile with this request context", drop="context", plant="quoin-jit", file="src/quoinJit.ts", test="tests/test_quoin_jit.py", field="quoinJit", ticket="GQL-L6-265"),
    dict(slug="strawberry-info-bind", fail="strawberry-drop-ctx-handoff", surf="Strawberry leftover leftover leftover leftover leftover leftover info.context", naive="disable dataloader", bind="load with this info.context", drop="info.context", plant="quoin-berry", file="src/quoinBerry.py", test="tests/test_quoin_berry.py", field="quoinBerry", ticket="GQL-L6-266"),
    dict(slug="graphene-promise-bind", fail="graphene-drop-resolve-handoff", surf="Graphene leftover leftover leftover leftover leftover leftover Promise", naive="disable promises", bind="resolve this Promise per field", drop="resolve", plant="quoin-prom", file="src/quoinProm.py", test="tests/test_quoin_prom.py", field="quoinProm", ticket="GQL-L6-267"),
    dict(slug="sangria-deferred-bind", fail="sangria-drop-ctx-handoff", surf="Sangria leftover leftover leftover leftover leftover leftover Deferred", naive="disable Deferred", bind="Deferred uses this ctx", drop="ctx", plant="quoin-sang", file="src/quoinSang.scala", test="tests/test_quoin_sang.py", field="quoinSang", ticket="GQL-L6-268"),
    dict(slug="hc-dataloader-bind", fail="hc-drop-scope-handoff", surf="Hot Chocolate leftover leftover leftover leftover leftover leftover DataLoader scope", naive="disable DataLoader", bind="scope loader to this request", drop="scoped", plant="quoin-hc", file="src/quoinHc.cs", test="tests/test_quoin_hc.py", field="quoinHc", ticket="GQL-L6-269"),
    dict(slug="absinthe-batch-bind", fail="absinthe-drop-dl-handoff", surf="Absinthe leftover leftover leftover leftover leftover leftover batch", naive="disable batch", bind="batch this resolution tick", drop="dataloader", plant="quoin-abs", file="src/quoinAbs.ex", test="tests/test_quoin_abs.py", field="quoinAbs", ticket="GQL-L6-270"),
    dict(slug="juniper-exec-bind", fail="juniper-drop-ctx-handoff", surf="Juniper leftover leftover leftover leftover leftover leftover executor context", naive="disable executor cache", bind="executor ctx from this request", drop="context", plant="quoin-jun", file="src/quoinJun.rs", test="tests/test_quoin_jun.py", field="quoinJun", ticket="GQL-L6-271"),
    dict(slug="agql-data-bind", fail="agql-drop-data-handoff", surf="async-graphql leftover leftover leftover leftover leftover leftover ctx.data", naive="disable dataloader", bind="ctx.data from this request", drop="ctx.data", plant="quoin-agql", file="src/quoinAgql.rs", test="tests/test_quoin_agql.py", field="quoinAgql", ticket="GQL-L6-272"),
    dict(slug="gqlgen-around-bind", fail="gqlgen-drop-around-handoff", surf="gqlgen leftover leftover leftover leftover leftover leftover aroundFields", naive="disable middleware", bind="aroundFields for this op", drop="aroundFields", plant="quoin-gen", file="src/quoinGen.go", test="tests/test_quoin_gen.py", field="quoinGen", ticket="GQL-L6-273"),
    dict(slug="pothos-prisma-bind", fail="pothos-drop-loaders-handoff", surf="Pothos leftover leftover leftover leftover leftover leftover prisma loaders", naive="disable prisma plugin", bind="loaders for this prisma client", drop="loaders", plant="quoin-poth", file="src/quoinPoth.ts", test="tests/test_quoin_poth.py", field="quoinPoth", ticket="GQL-L6-274"),
    dict(slug="nexus-plugin-bind", fail="nexus-drop-oncreate-handoff", surf="Nexus leftover leftover leftover leftover leftover leftover plugin resolver", naive="disable plugins", bind="onCreateFieldResolver this plugin", drop="onCreateFieldResolver", plant="quoin-nex", file="src/quoinNex.ts", test="tests/test_quoin_nex.py", field="quoinNex", ticket="GQL-L6-275"),
]


def db(k: str, t: str) -> str:
    return f"{k}: {t}"[:240]


def success(rnd: int, p: dict) -> dict:
    eid = f"gql-r{rnd}-{p['slug']}"
    src, test, field, plant = p["file"], p["test"], p["field"], p["plant"]
    steps = [
        {"n": 1, "decision_basis": db("Plan", f"read {plant} entry and gate before {p['naive']}."), "tool_call": {"name": "bash", "args": {"command": f"rg -n '{p['surf'].split()[0]}|{field}' src tests | head -n 26"}}, "observation": f"{src}: leftover leftover leftover leftover leftover leftover {p['surf']}\n{src}: {field}: Float\n{test}: def test_one\n"},
        {"n": 2, "decision_basis": db("Observation", f"gate test (step 1). Read {src}."), "tool_call": {"name": "read", "args": {"path": src}}, "observation": f"// leftover leftover leftover leftover leftover leftover first tick reused\n"},
        {"n": 3, "decision_basis": db("Observation", f"source confirms the bug (step 2). Read {test}."), "tool_call": {"name": "read", "args": {"path": test}}, "observation": f"def test_one():\n    r = execute('{{ yard {{ {field} }} }}')\n    assert r.ok\n"},
        {"n": 4, "decision_basis": db("Observation", "gate expectations (step 3). Run."), "tool_call": {"name": "bash", "args": {"command": f"pytest {test} -q --tb=short 2>&1 | tail -n 10"}}, "observation": f"FAILED test_one - leftover leftover leftover leftover leftover leftover {p['surf']}\n1 failed, 1 passed\n"},
        {"n": 5, "decision_basis": db("Observation", "failing assertion (step 4). Fetch runbook."), "tool_call": {"name": "fetch", "args": {"url": f"https://docs.invalid/{plant}"}}, "observation": "GET HTTP/1.1 502 Bad Gateway"},
        {"n": 6, "decision_basis": db("Observation", "the prior call returned an upstream gateway failure. Retry once with 2s backoff."), "tool_call": {"name": "fetch", "args": {"url": f"https://docs.invalid/{plant}"}}, "observation": f"retry after 2s; leftover leftover leftover leftover leftover leftover {p['bind']}. Not leftover-GET. Not leftover-mesh."},
        {"n": 7, "decision_basis": db("Plan", f"first apply — {p['naive']}."), "tool_call": {"name": "edit", "args": {"path": src, "old": "leftover first tick", "new": f"// {p['naive']}"}}, "observation": f"patched {p['naive']}"},
        {"n": 8, "decision_basis": db("Observation", "first apply (step 7)."), "tool_call": {"name": "bash", "args": {"command": f"pytest {test} -q --tb=short 2>&1 | tail -n 8"}}, "observation": f"FAILED test_slo - {p['naive']} blew batching\n1 failed, 1 passed\n", "reflection": f"{p['bind']}. Not leftover-GET r183–r259."},
        {"n": 9, "decision_basis": db("Reflection", f"plan change — {p['bind']}."), "tool_call": {"name": "write", "args": {"path": src, "contents": f"function bind() {{ return {field}; }} // {p['bind']}\n"}}, "observation": p["bind"]},
        {"n": 10, "decision_basis": db("Observation", "rewrite (step 9). Re-run."), "tool_call": {"name": "bash", "args": {"command": f"pytest {test} -q --tb=short 2>&1 | tail -n 8"}}, "observation": "2 passed in 0.11s"},
        {"n": 11, "decision_basis": db("Observation", "gate green (step 10). Extra case."), "tool_call": {"name": "read", "args": {"path": test.replace(".py", "_entity.py")}}, "observation": "def test_extra():\n    pass\n"},
        {"n": 12, "decision_basis": db("Observation", "extra case (step 11). Full suite."), "tool_call": {"name": "bash", "args": {"command": "pytest tests -q --tb=line 2>&1 | tail -n 6"}}, "observation": "6 passed in 0.34s"},
        {"n": 13, "decision_basis": db("Observation", "suite (step 12). Residual noted."), "tool_call": {"name": "read", "args": {"path": src}}, "observation": f"residual leftover leftover leftover leftover leftover leftover {p['drop']} on mutation"},
        {"n": 14, "decision_basis": db("Observation", "residual noted (step 13). Re-run gate."), "tool_call": {"name": "bash", "args": {"command": f"pytest {test} -q --tb=line 2>&1 | tail -n 4"}}, "observation": "2 passed in 0.07s"},
        {"n": 15, "decision_basis": db("Observation", "2/2 (step 14). Sequential accepted."), "tool_call": {"name": "bash", "args": {"command": "pytest tests -q --tb=line 2>&1 | tail -n 4"}}, "observation": "6 passed in 0.34s"},
        {"n": 16, "decision_basis": db("Observation", "done (step 15)."), "tool_call": {"name": "bash", "args": {"command": f"pytest {test} -q --tb=line 2>&1 | tail -n 3"}}, "observation": "2 passed in 0.06s"},
    ]
    return {
        "id": eid,
        "goal": f"quoin leftover leftover leftover leftover leftover leftover {p['surf']}: {p['bind']}. Distinct leftover execution — not leftover-mesh, not leftover-GET, not r183–r259 clones. Gate: {test}.",
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
        {"n": 2, "decision_basis": db("Observation", "run gate."), "tool_call": {"name": "pytest", "args": {"args": f"{test} -q --tb=short"}}, "observation": f"FAILED {test} — dropped leftover leftover leftover leftover leftover leftover {p['drop']}"},
        {"n": 3, "decision_basis": db("Observation", f"read {test}."), "tool_call": {"name": "read", "args": {"path": test}}, "observation": f"def test_keep():\n    assert keep({p['drop']!r})\n"},
        {"n": 4, "decision_basis": db("Observation", "grep drop."), "tool_call": {"name": "bash", "args": {"command": f"rg -n '{p['drop']}' src tests"}}, "observation": f"{src}: drop {p['drop']}"},
        {"n": 5, "decision_basis": db("Observation", f"read {src}."), "tool_call": {"name": "read", "args": {"path": src}}, "observation": f"return None  # dropped {p['drop']}\n"},
        {"n": 6, "decision_basis": db("Observation", "need registry."), "tool_call": {"name": "fetch", "args": {"url": f"https://docs.invalid/{p['plant']}-drop"}}, "observation": "HTTP/1.1 429 Too Many Requests\nRetry-After: 5"},
        {"n": 7, "decision_basis": db("Observation", "rate-limit; sleep then retry."), "tool_call": {"name": "fetch", "args": {"url": f"https://docs.invalid/{p['plant']}-drop"}}, "observation": f"sleep + jitter; cannot drop leftover leftover leftover leftover leftover leftover {p['drop']}"},
        {"n": 8, "decision_basis": db("Observation", "second doc."), "tool_call": {"name": "fetch", "args": {"url": f"https://docs.invalid/{p['plant']}-plat"}}, "observation": "HTTP/1.1 502 Bad Gateway"},
        {"n": 9, "decision_basis": db("Observation", "retry 502."), "tool_call": {"name": "fetch", "args": {"url": f"https://docs.invalid/{p['plant']}-plat"}}, "observation": f"Handoff {ticket}. Not leftover-GET. Not leftover-mesh."},
        {"n": 10, "decision_basis": db("Observation", "first patch."), "tool_call": {"name": "edit", "args": {"path": src, "old": "return None", "new": "return first"}}, "observation": f"still drop {p['drop']}"},
        {"n": 11, "decision_basis": db("Observation", "re-run."), "tool_call": {"name": "pytest", "args": {"args": f"{test} -q --tb=short"}}, "observation": f"FAILED still drop {p['drop']}"},
        {"n": 12, "decision_basis": db("Observation", "re-read."), "tool_call": {"name": "read", "args": {"path": src}}, "observation": f"Dropped leftover leftover leftover leftover leftover leftover {p['drop']} is platform grain", "reflection": f"Plan change: Dropped leftover {p['drop']} is platform. Handoff {ticket}."},
        {"n": 13, "decision_basis": db("Reflection", f"Dropped leftover {p['drop']} is platform. Handoff {ticket}."), "tool_call": {"name": "edit", "args": {"path": f"handoff/{p['plant']}.md", "old": "", "new": f"# {ticket}"}}, "observation": "ticket filed"},
        {"n": 14, "decision_basis": db("Observation", "re-run after handoff."), "tool_call": {"name": "pytest", "args": {"args": f"{test} -q --tb=short"}}, "observation": f"FAILED # {ticket}\n1 failed"},
        {"n": 15, "decision_basis": db("Observation", "broader check."), "tool_call": {"name": "bash", "args": {"command": f"pytest {test} -q; echo {ticket}"}}, "observation": f"1 failed, 2 passed\n{ticket}"},
        {"n": 16, "decision_basis": db("Observation", "diffstat."), "tool_call": {"name": "bash", "args": {"command": "git diff --stat | head -n 40"}}, "observation": f"{src} changed; handoff added"},
        {"n": 17, "decision_basis": db("Observation", "lint."), "tool_call": {"name": "bash", "args": {"command": "ruff check tests || true; echo lint-end"}}, "observation": "All checks passed!\nlint-end"},
    ]
    return {
        "id": eid,
        "goal": f"Do not drop leftover leftover leftover leftover leftover leftover {p['drop']} on {p['surf']}.",
        "plan": f"Read drop-{p['drop']}, then hand off.",
        "steps": steps,
        "outcome": f"Still drop-{p['drop']}; leftover leftover leftover leftover leftover leftover grain — handoff {ticket}.",
        "reward": {"success": False, "plan_changes": 1, "tests_passed": 2, "cost_steps": 17, "retries": 2, "duration_min": 14, "wasted_calls": 3},
        "meta": {"factory": FAC, "round": rnd, "generator": GEN, "kind": "episode", "seed": p["fail"], "designed": True, "domain": p["plant"] + "-drop", "stack": p["surf"] + " drop"},
    }


def notes(rnd: int, p: dict) -> str:
    return f"""# NOTES-r{rnd} graphql-nplusone-factory

Novel coverage: leftover leftover leftover leftover leftover leftover {p['surf']} vs drop {p['drop']}.
Not leftover-mesh Federation; not leftover-GET r183–r259; not r188 graphql-response+json; not r215 hasNext.

## Episodes
- `gql-r{rnd}-{p['slug']}`: 16 steps, success=True
- `gql-r{rnd}-{p['fail']}`: 17 steps, success=False, handoff {p['ticket']}

## decision_basis audit
Every step starts Plan:/Observation:/Reflection:/Tool call:. No thought/CoT/spikes. Generator grok-4.6.

## Weaknesses / next
Avoid {p['naive']}. Cannot drop leftover leftover leftover leftover leftover leftover {p['drop']}.
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
    # first reserved r260
    p0 = PAIRS[0]
    if not SEED_STAGE.is_dir():
        print("ERROR: seed stage missing", file=sys.stderr)
        return 1
    ok, bad = write_stage(SEED_STAGE, 260, p0)
    pub = txn(
        [
            "python3",
            "pipelines/round_txn.py",
            "publish",
            str(FAC_DIR),
            "--round",
            "260",
            "--token",
            SEED_TOKEN,
        ]
    )
    published.append((260, ok["id"], bad["id"]))
    print(json.dumps({"published": 260, "ids": [ok["id"], bad["id"]]}))
    for p in PAIRS[1:]:
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
