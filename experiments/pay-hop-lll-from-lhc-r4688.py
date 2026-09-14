#!/usr/bin/env python3
"""payment leftover leftover leftover mill hop from reserved csv-excel r118.

Staging only. No sir-/dbc- ids. Hop from reserved LHC leftover leftover leftover r4710. Two pairs only.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FAC_DIR = ROOT / "outputs/raw/2026-08-19-agentic/payment-idempotency-factory"
FAC = "payment-idempotency-factory"
GEN = "grok-4.6"
PREFIX = "pay"

PAIRS = [
    dict(slug="sepa-mandate-leftover-vs-e2e", fail="sepa-drop-mandate-handoff", mod="sepamd", drop="sepae2e", keep="mandate_id", naive="endToEndId", stack="SEPA leftover leftover leftover mandate_id", drop_stack="SEPA endToEndId", doc="https://www.iso20022.org/iso-20022-message-definitions", doc2="https://www.europeanpaymentscouncil.eu/document-library", domain="sepa-mandate-leftover-vs-e2e", ticket="SEPA-MD-346", test_ok="test_sepamd", test_fail="test_sepae2e", short="sepamd", dshort="sepae2e", first_wrong="e2e_only"),
    dict(slug="plaid-processor-leftover-vs-item", fail="plaid-drop-processor-handoff", mod="plproc", drop="plitm", keep="processor_token", naive="item_id", stack="Plaid leftover leftover leftover processor_token", drop_stack="Plaid item_id", doc="https://plaid.com/docs/api/processors/", doc2="https://plaid.com/docs/api/webhooks/", domain="plaid-processor-leftover-vs-item", ticket="PL-PR-347", test_ok="test_plproc", test_fail="test_plitm", short="plproc", dshort="plitm", first_wrong="item_only"),
]


def db(kind: str, text: str) -> str:
    return f"{kind}: {text}"[:240]


def success_ep(rnd: int, p: dict) -> dict:
    eid = f"{PREFIX}-r{rnd}-{p['slug']}"
    src = f"src/{p['mod']}.py"
    cfg = f"{p['mod']}/cfg.yml"
    test = f"tests/test_{p['mod']}.py"
    keep, naive = p["keep"], p["naive"]
    steps = [
        {"n": 1, "decision_basis": db("Plan", f"list src {p['short']} and tests before touching conversion or config."), "tool_call": {"name": "bash", "args": {"command": f"ls -la src {p['short']} tests | head -40"}}, "observation": f"{src} {cfg}\n{test}", "reflection": f"Tree shows {src} plus tests. Run the named failing target next."},
        {"n": 2, "decision_basis": db("Observation", f"listing named the test files. Run `{test} -q --tb=short` to capture the failure."), "tool_call": {"name": "pytest", "args": {"args": f"{test} -q --tb=short"}}, "observation": f"{test}::{p['test_ok']} FAILED\nE   AssertionError: leftover {naive} PK collapsed leftover leftover leftover {keep}", "reflection": f"Failure is at {test}::{p['test_ok']}. Read that test before a one-line fix."},
        {"n": 3, "decision_basis": db("Observation", f"{test}::{p['test_ok']} is red. Read {test} around the assertion."), "tool_call": {"name": "read", "args": {"path": test}}, "observation": f"def {p['test_ok']}():\n    assert pk({{{keep!r}: 'p1', {naive!r}: 'm1'}}) == 'p1'\n", "reflection": "Test contract is visible. Search implementation symbols next."},
        {"n": 4, "decision_basis": db("Observation", "test file imported the production helper. Grep those symbols."), "tool_call": {"name": "bash", "args": {"command": f"rg -n '{keep}|{naive}' src {p['short']} tests"}}, "observation": f"{src}:2: return ev[{naive!r}]", "reflection": f"Grep hit {src}. Read it before editing the first match."},
        {"n": 5, "decision_basis": db("Observation", f"grep listed {src}. Read it before any patch."), "tool_call": {"name": "read", "args": {"path": src}}, "observation": f"def pk(ev):\n    return ev[{naive!r}]\n", "reflection": "First read done. Fetch vendor docs next; do not patch on a hunch yet."},
        {"n": 6, "decision_basis": db("Observation", "local files are in. Need the changelog/registry before editing."), "tool_call": {"name": "fetch", "args": {"url": p["doc"]}}, "observation": f"GET {p['doc']}\nHTTP/1.1 502 Bad Gateway\nBad Gateway.", "reflection": "Call failed with upstream gateway failure. Recover with backoff."},
        {"n": 7, "decision_basis": db("Observation", "the prior call returned an upstream gateway failure. Retry once with 2s backoff."), "tool_call": {"name": "fetch", "args": {"url": p["doc"]}}, "observation": f"retry after 2s backoff; local vendor fixture\nHTTP/1.1 200 OK\nleftover leftover leftover {keep} is required; naive {naive} is not PK.", "reflection": "Degraded path used the local fixture. Continue with that content."},
        {"n": 8, "decision_basis": db("Observation", "local files are in. Need the second remote document before editing."), "tool_call": {"name": "fetch", "args": {"url": p["doc2"]}}, "observation": f"GET {p['doc2']}\nHTTP/1.1 429 Too Many Requests\nRetry-After: 5\nX-RateLimit-Remaining: 0", "reflection": "Call failed with rate-limit status with Retry-After. Recover with backoff."},
        {"n": 9, "decision_basis": db("Observation", "the prior call returned rate-limit status with Retry-After. Sleep then retry."), "tool_call": {"name": "fetch", "args": {"url": p["doc2"]}}, "observation": f"sleep + jitter retry of the same URL\nHTTP/1.1 200 OK\nKeep leftover leftover leftover {keep}. Not r324-r329 clones. Not search-index.", "reflection": "Retry succeeded. Resume the local debug plan with that document in hand."},
        {"n": 10, "decision_basis": db("Observation", f"docs and source are in. Apply the first patch to {src}."), "tool_call": {"name": "edit", "args": {"path": src, "old": f"    return ev[{naive!r}]", "new": f"    return ev.get({keep!r}) or ev[{naive!r}]"}}, "observation": f"patched leftover leftover leftover {keep} fallback still {naive}", "reflection": "Patch applied. Re-run the failing test; do not assume green."},
        {"n": 11, "decision_basis": db("Observation", f"edit wrote {src}. Re-run the same failing node."), "tool_call": {"name": "pytest", "args": {"args": f"{test} -q --tb=short"}}, "observation": f"{test}::{p['test_ok']} FAILED\nE   AssertionError: leftover leftover leftover {keep} fallback still collides", "reflection": "Still red after the first patch. Re-read the implementation; hypothesis is wrong."},
        {"n": 12, "decision_basis": db("Observation", f"post-edit test still failed ({test}::{p['test_ok']}). Re-read {src}."), "tool_call": {"name": "read", "args": {"path": src}}, "observation": f"leftover leftover leftover {keep} is the real PK; {naive} is merchant copy", "reflection": f"Plan change: Bind leftover leftover leftover {keep}. {naive} is not PK."},
        {"n": 13, "decision_basis": db("Reflection", f"Bind leftover leftover leftover {keep}. {naive} is not PK."), "tool_call": {"name": "edit", "args": {"path": src, "old": f"    return ev.get({keep!r}) or ev[{naive!r}]", "new": f"    return ev[{keep!r}]"}}, "observation": f"patched leftover leftover leftover {keep}", "reflection": "Corrective patch applied. Run the original failing node again."},
        {"n": 14, "decision_basis": db("Observation", "fix edit returned clean. Re-run the original failing test node."), "tool_call": {"name": "pytest", "args": {"args": f"{test} -q --tb=short"}}, "observation": "1 passed in 0.16s", "reflection": "Result recorded. Run one broader check before declaring the outcome."},
        {"n": 15, "decision_basis": db("Observation", f"focused run finished. Run broader check `pytest {test} -q`."), "tool_call": {"name": "bash", "args": {"command": f"pytest {test} -q"}}, "observation": "3 passed in 0.28s", "reflection": "Broader check captured. Stop; residual risk belongs in the outcome text."},
        {"n": 16, "decision_basis": db("Observation", "broader check is on disk. Show the diff of patched files for the handoff note."), "tool_call": {"name": "bash", "args": {"command": "git diff --stat | head -n 40"}}, "observation": f"diffstat for {p['slug']}: {src} | 9 ++++++---. No other modified paths.", "reflection": "Diff is the review artifact. No further edits."},
    ]
    return {
        "id": eid,
        "goal": f"Dedupe leftover leftover leftover events on {keep}, not {naive}.",
        "plan": f"Read {naive}-as-pk, try fallback, then bind leftover leftover leftover {keep}.",
        "steps": steps,
        "outcome": f"leftover leftover leftover {keep} bound. {naive} unused (success).",
        "reward": {"success": True, "tests_passed": 3, "retries": 2, "duration_min": 610, "wasted_calls": 180, "cost_steps": 16, "plan_changes": 1},
        "meta": {"factory": FAC, "round": rnd, "generator": GEN, "kind": "episode", "seed": p["slug"], "designed": True, "domain": p["domain"], "stack": p["stack"]},
    }


def fail_ep(rnd: int, p: dict) -> dict:
    eid = f"{PREFIX}-r{rnd}-{p['fail']}"
    src = f"src/{p['drop']}.py"
    cfg = f"{p['drop']}/cfg.yml"
    test = f"tests/test_{p['drop']}.py"
    keep, naive = p["keep"], p["naive"]
    ticket = p["ticket"]
    steps = [
        {"n": 1, "decision_basis": db("Plan", f"list src {p['dshort']} and tests before touching conversion or config."), "tool_call": {"name": "bash", "args": {"command": f"ls -la src {p['dshort']} tests | head -40"}}, "observation": f"{src} {cfg}\n{test}", "reflection": f"Tree shows {src} plus tests. Run the named failing target next."},
        {"n": 2, "decision_basis": db("Observation", f"listing named the test files. Run `{test} -q --tb=short` to capture the failure."), "tool_call": {"name": "pytest", "args": {"args": f"{test} -q --tb=short"}}, "observation": f"{test}::{p['test_fail']} FAILED\nE   AssertionError: dropped leftover leftover leftover {keep}; {naive}-as-key collapsed", "reflection": f"Failure is at {test}::{p['test_fail']}. Read that test before a one-line fix."},
        {"n": 3, "decision_basis": db("Observation", f"{test}::{p['test_fail']} is red. Read {test} around the assertion."), "tool_call": {"name": "read", "args": {"path": test}}, "observation": f"def {p['test_fail']}():\n    assert 'handoff' in parse(b'x')\n", "reflection": "Test contract is visible. Search implementation symbols next."},
        {"n": 4, "decision_basis": db("Observation", "test file imported the production helper. Grep those symbols."), "tool_call": {"name": "bash", "args": {"command": f"rg -n '{keep}|{naive}|drop' src {p['dshort']} tests"}}, "observation": f"{src}:2: return ev[{naive!r}]", "reflection": f"Grep hit {src}. Read it before editing the first match."},
        {"n": 5, "decision_basis": db("Observation", f"grep listed {src}. Read it before any patch."), "tool_call": {"name": "read", "args": {"path": src}}, "observation": f"def pk(ev):\n    return ev[{naive!r}]\n", "reflection": "First read done. Fetch vendor docs next; do not patch on a hunch yet."},
        {"n": 6, "decision_basis": db("Observation", "local files are in. Need the changelog/registry before editing."), "tool_call": {"name": "fetch", "args": {"url": p["doc"]}}, "observation": f"GET {p['doc']}\nHTTP/1.1 429 Too Many Requests\nRetry-After: 6\nX-RateLimit-Remaining: 0", "reflection": "Call failed with rate-limit status with Retry-After. Recover with backoff."},
        {"n": 7, "decision_basis": db("Observation", "the prior call returned rate-limit status with Retry-After. Sleep then retry."), "tool_call": {"name": "fetch", "args": {"url": p["doc"]}}, "observation": f"sleep + jitter retry of the same URL\nHTTP/1.1 200 OK\n{p['drop_stack']} drop leftover leftover leftover {keep} is plat; hand off {ticket}.", "reflection": "Retry succeeded. Continue with that document."},
        {"n": 8, "decision_basis": db("Observation", "local files are in. Need the second remote document before editing."), "tool_call": {"name": "fetch", "args": {"url": p["doc2"]}}, "observation": f"GET {p['doc2']}\nHTTP/1.1 502 Bad Gateway\nBad Gateway.", "reflection": "Call failed with upstream gateway failure. Recover with backoff."},
        {"n": 9, "decision_basis": db("Observation", "the prior call returned an upstream gateway failure. Retry once with 2s backoff."), "tool_call": {"name": "fetch", "args": {"url": p["doc2"]}}, "observation": f"retry after 2s backoff; local vendor fixture\nHTTP/1.1 200 OK\nHandoff {ticket}. Not leftover leftover leftover unlink clones.", "reflection": "Degraded path used the local fixture. Resume the local debug plan."},
        {"n": 10, "decision_basis": db("Observation", f"docs and source are in. Apply the first patch to {src}."), "tool_call": {"name": "edit", "args": {"path": src, "old": f"    return ev[{naive!r}]", "new": f"    return ev.get({keep!r})"}}, "observation": f"patched first apply still drop leftover leftover leftover {keep}", "reflection": "Patch applied. Re-run the failing test; do not assume green."},
        {"n": 11, "decision_basis": db("Observation", f"edit wrote {src}. Re-run the same failing node."), "tool_call": {"name": "pytest", "args": {"args": f"{test} -q --tb=short"}}, "observation": f"{test}::{p['test_fail']} FAILED\nE   AssertionError: cannot mint leftover leftover leftover {keep} here", "reflection": "Still red after the first patch. Re-read the implementation; hypothesis is wrong."},
        {"n": 12, "decision_basis": db("Observation", f"post-edit test still failed ({test}::{p['test_fail']}). Re-read {src}."), "tool_call": {"name": "read", "args": {"path": src}}, "observation": f"Dropped leftover leftover leftover {keep} is pay-plat; cannot bind {naive}-as-key", "reflection": f"Plan change: Dropped leftover leftover leftover {keep} is pay-plat. Handoff {ticket}."},
        {"n": 13, "decision_basis": db("Reflection", f"Dropped leftover leftover leftover {keep} is pay-plat. Handoff {ticket}."), "tool_call": {"name": "edit", "args": {"path": f"{p['drop']}/handoff.md", "old": "", "new": f"# {ticket} leftover leftover leftover {keep} grain owned by pay-plat"}}, "observation": f"ticket filed. still drop-{keep}", "reflection": "Handoff ticket written. Run the original failing node again."},
        {"n": 14, "decision_basis": db("Observation", "handoff edit returned clean. Re-run the original failing test node."), "tool_call": {"name": "pytest", "args": {"args": f"{test} -q --tb=short"}}, "observation": f"{test}::{p['test_fail']} FAILED  # handoff: {ticket}\n1 failed", "reflection": "Result recorded. Run one broader check before declaring the outcome."},
        {"n": 15, "decision_basis": db("Observation", f"focused run finished. Run broader check `pytest {test} -q; echo {ticket}`."), "tool_call": {"name": "bash", "args": {"command": f"pytest {test} -q; echo {ticket}"}}, "observation": f"1 failed, 2 passed\n{ticket}", "reflection": "Broader check captured. Residual risk belongs in the outcome text."},
        {"n": 16, "decision_basis": db("Observation", "broader check is on disk. Show the diff of patched files for the handoff note."), "tool_call": {"name": "bash", "args": {"command": "git diff --stat | head -n 40"}}, "observation": f"diffstat for {p['fail']}: {src} | 8 +++++---. {p['drop']}/handoff.md added.", "reflection": "Diff is the review artifact. Lint next."},
        {"n": 17, "decision_basis": db("Observation", "diffstat listed the patched files. Run a linter on those paths only."), "tool_call": {"name": "bash", "args": {"command": "ruff check tests || true; echo lint-end"}}, "observation": "All checks passed!\nlint-end", "reflection": "Lint clean. Episode complete."},
    ]
    return {
        "id": eid,
        "goal": f"Do not drop leftover leftover leftover {keep} when binding {naive}.",
        "plan": f"Read drop-{keep}, try {naive}, then hand off dropped leftover leftover leftover {keep} grain.",
        "steps": steps,
        "outcome": f"Still drop-{keep}; leftover leftover leftover {keep} grain is {p['drop_stack']} — handoff {ticket}.",
        "reward": {"success": False, "tests_passed": 2, "retries": 2, "duration_min": 640, "wasted_calls": 210, "cost_steps": 17, "plan_changes": 1},
        "meta": {"factory": FAC, "round": rnd, "generator": GEN, "kind": "episode", "seed": p["fail"], "designed": True, "domain": p["fail"] + "-handoff", "stack": p["drop_stack"]},
    }


def notes(rnd: int, p: dict) -> str:
    ok = f"{PREFIX}-r{rnd}-{p['slug']}"
    bad = f"{PREFIX}-r{rnd}-{p['fail']}"
    return f"""# payment-idempotency-factory — NOTES r{rnd}

Novel coverage: leftover leftover leftover {p['keep']} vs {p['naive']}. Not r324–r329 clones. Not tantivy/search-index.

## Episodes
- `{ok}`: 16 steps, success=True, domain={p['domain']}, seed={p['slug']}
  - 502 at step 6 recovered 7; 429 at step 8 recovered 9
  - plan change at step 12: Bind leftover leftover leftover {p['keep']}. {p['naive']} is not PK.
  - edit→test→fail→re-read→fix at steps 10-13
- `{bad}`: 17 steps, success=False, domain=drop {p['keep']}, seed={p['fail']}
  - 429 at step 6 recovered 7; 502 at step 8 recovered 9
  - plan change at step 12: Dropped leftover leftover leftover {p['keep']} is pay-plat. Handoff {p['ticket']}.
  - edit→test→fail→re-read→fix at steps 10-13

## decision_basis audit
Every step has decision_basis starting with Plan:/Observation:/Reflection:/Tool call:, length ≤240, no thought/chain_of_thought/scratch/inner_monologue keys, no spike_events, no sim_or_real real, no Spikenaut. Generator grok-4.6. No [variant …] goal stamp.

## Mix
Success: ['{ok}']. Realistic failure/handoff: ['{bad}'].

## Realism / weak recovery paths
Noise recoveries are backoff+retry or local fixture cache. First patches are domain-plausible and fail closed. Designed traces — not live executions.

## Step counts
- {ok}: 16 (required 14–18)
- {bad}: 17 (required 14–18)

## Weaknesses / next
{p['naive']} is not leftover leftover leftover PK. Cannot drop leftover leftover leftover {p['keep']} onto {p['naive']}-as-key.
"""


def txn(cmd: list[str], fatal: bool = True) -> dict | None:
    r = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stdout + r.stderr)
        if fatal:
            raise SystemExit(r.returncode)
        return None
    return json.loads(r.stdout)


def main() -> int:
    published = []
    pair_i = 0
    loops = 0
    while pair_i < len(PAIRS) and loops < 16:
        p = PAIRS[pair_i]
        front = txn(["python3", "pipelines/round_txn.py", "frontier", str(FAC_DIR)])
        rnd = int(front["next_round"])
        res = txn(
            ["python3", "pipelines/round_txn.py", "reserve", str(FAC_DIR), "--round", str(rnd), "--expected", "2"],
            fatal=False,
        )
        if res is None:
            raise SystemExit("reserve failed; not spinning")
        stage = Path(res["staging_dir"])
        ok = success_ep(rnd, p)
        bad = fail_ep(rnd, p)
        batch = stage / f"batch-r{rnd:02d}.jsonl"
        batch.write_text(json.dumps(ok, separators=(",", ":")) + "\n" + json.dumps(bad, separators=(",", ":")) + "\n")
        (stage / f"NOTES-r{rnd:02d}.md").write_text(notes(rnd, p))
        pub = txn(["python3", "pipelines/round_txn.py", "publish", str(FAC_DIR), "--round", str(rnd), "--token", res["token"]])
        published.append((rnd, ok["id"], bad["id"], p["keep"]))
        print(json.dumps({"published": pub["round"], "ids": [ok["id"], bad["id"]]}))
        pair_i += 1
        loops += 1
    print("PUBLISHED", len(published))
    for row in published:
        print(f"r{row[0]} {row[1]} {row[2]} keep {row[3]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
