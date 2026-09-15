"""Pure episode builders for the pay lane (r330).

AST-extracted from the legacy ``mill_leftover_leftover_leftover_pay_r330``
staging script and cleaned: only the pure record builders remain.
``success_ep`` (16 steps) and ``fail_ep`` (17 steps) emit the two episode
records for one provider pair; ``db`` clips a decision-basis string. These
functions perform no I/O and drive no subprocess — the staging/publish path
that wrapped them is intentionally not vendored (never executed here).
"""

from __future__ import annotations

from .pairs import FAC, GEN, PREFIX

__all__ = ["db", "success_ep", "fail_ep"]


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
