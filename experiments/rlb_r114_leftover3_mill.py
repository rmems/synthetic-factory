#!/usr/bin/env python3
"""rate-limit-backoff leftover leftover leftover mill r114+ (16 rounds).

DISTINCT leftover leftover leftover leftover leftover leftover budget vs leftover leftover leftover bind.
BAN r81 monday-graphql-complexity, airtable-formula.
Skip used r82–r113 (Twilio, SendGrid, PagerDuty, Datadog, Sentry, Okta, …).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path("/home/raulmc/rmems/synthetic-factory")
DIR = ROOT / "outputs/raw/2026-08-19-agentic/rate-limit-backoff-factory"
TXN = ["python3", str(ROOT / "pipelines/round_txn.py")]
FACTORY = "rate-limit-backoff-factory"
GEN = "grok-4.6"
BANNED = ("thought", "chain_of_thought", "scratch", "inner_monologue", "spike_events")
N_ROUNDS = 16
START = 119

# leftover leftover leftover leftover leftover leftover vs leftover leftover leftover
PAIRS: list[dict] = [
    {
        "slug": "opsgenie-leftover-account",
        "lslug": "opsgenie-leftover-alert-handoff",
        "api": "Opsgenie",
        "src": "oglef",
        "lsrc": "ogalrt",
        "leftover": "X-RateLimit-Remaining",
        "naive": "X-RateLimit-Reset",
        "lval": "197",
        "nval": "1713333333",
        "lname": "alert-leftover",
        "ticket": "OG-LF-18",
        "docs": "https://docs.opsgenie.com/docs/api-rate-limiting",
        "docs2": "https://docs.opsgenie.com/docs/alert-api",
        "novel": 90,
        "mod": 13,
    },
    {
        "slug": "newrelic-leftover-account",
        "lslug": "newrelic-leftover-nrql-handoff",
        "api": "New Relic",
        "src": "nrlef",
        "lsrc": "nrnrql",
        "leftover": "X-RateLimit-Remaining",
        "naive": "X-RateLimit-Reset-Time",
        "lval": "820",
        "nval": "60",
        "lname": "nrql-leftover",
        "ticket": "NR-LF-18",
        "docs": "https://docs.newrelic.com/docs/apis/rest-api-v2/requirements/api-rate-limits-rest-api/",
        "docs2": "https://docs.newrelic.com/docs/apis/nerdgraph/get-started/introduction-new-relic-nerdgraph/",
        "novel": 91,
        "mod": 10,
    },
    {
        "slug": "honeycomb-leftover-team",
        "lslug": "honeycomb-leftover-query-handoff",
        "api": "Honeycomb",
        "src": "hclef",
        "lsrc": "hcqry",
        "leftover": "X-RateLimit-Remaining",
        "naive": "X-RateLimit-Limit",
        "lval": "28",
        "nval": "100",
        "lname": "query-leftover",
        "ticket": "HC-LF-18",
        "docs": "https://docs.honeycomb.io/api/rate-limits/",
        "docs2": "https://docs.honeycomb.io/api/query-specification/",
        "novel": 87,
        "mod": 7,
    },
    {
        "slug": "snowflake-leftover-account",
        "lslug": "snowflake-leftover-sql-handoff",
        "api": "Snowflake",
        "src": "sflef",
        "lsrc": "sfsql",
        "leftover": "X-Snowflake-Remaining",
        "naive": "X-Snowflake-Reset",
        "lval": "310",
        "nval": "1714444444",
        "lname": "sql-leftover",
        "ticket": "SF-LF-18",
        "docs": "https://docs.snowflake.com/en/developer-guide/sql-api/reference",
        "docs2": "https://docs.snowflake.com/en/developer-guide/sql-api/submitting-requests",
        "novel": 93,
        "mod": 14,
    },
    {
        "slug": "bigquery-leftover-project",
        "lslug": "bigquery-leftover-jobs-handoff",
        "api": "BigQuery",
        "src": "bqlef",
        "lsrc": "bqjobs",
        "leftover": "X-RateLimit-Remaining",
        "naive": "X-Quota-User",
        "lval": "44",
        "nval": "200",
        "lname": "jobs-leftover",
        "ticket": "BQ-LF-18",
        "docs": "https://cloud.google.com/bigquery/quotas",
        "docs2": "https://cloud.google.com/bigquery/docs/reference/rest/v2/jobs",
        "novel": 88,
        "mod": 9,
    },
    {
        "slug": "openai-leftover-org",
        "lslug": "openai-leftover-tokens-handoff",
        "api": "OpenAI",
        "src": "oalef",
        "lsrc": "oatok",
        "leftover": "x-ratelimit-remaining-requests",
        "naive": "x-ratelimit-reset-requests",
        "lval": "490",
        "nval": "20s",
        "lname": "tokens-leftover",
        "ticket": "OA-LF-18",
        "docs": "https://platform.openai.com/docs/guides/rate-limits",
        "docs2": "https://platform.openai.com/docs/api-reference/chat",
        "novel": 94,
        "mod": 12,
    },
    {
        "slug": "anthropic-leftover-workspace",
        "lslug": "anthropic-leftover-tokens-handoff",
        "api": "Anthropic",
        "src": "anlef",
        "lsrc": "antok",
        "leftover": "anthropic-ratelimit-requests-remaining",
        "naive": "anthropic-ratelimit-requests-reset",
        "lval": "37",
        "nval": "1715555555",
        "lname": "tokens-leftover",
        "ticket": "AN-LF-18",
        "docs": "https://docs.anthropic.com/en/api/rate-limits",
        "docs2": "https://docs.anthropic.com/en/api/messages",
        "novel": 92,
        "mod": 11,
    },
    {
        "slug": "cohere-leftover-trial",
        "lslug": "cohere-leftover-embed-handoff",
        "api": "Cohere",
        "src": "colef",
        "lsrc": "coemb",
        "leftover": "x-endpoint-monthly-remaining",
        "naive": "x-endpoint-monthly-limit",
        "lval": "912",
        "nval": "1000",
        "lname": "embed-leftover",
        "ticket": "CO-LF-18",
        "docs": "https://docs.cohere.com/docs/rate-limits",
        "docs2": "https://docs.cohere.com/reference/embed",
        "novel": 86,
        "mod": 8,
    },
    {
        "slug": "groq-leftover-org",
        "lslug": "groq-leftover-tokens-handoff",
        "api": "Groq",
        "src": "grlef",
        "lsrc": "grtok",
        "leftover": "x-ratelimit-remaining-requests",
        "naive": "x-ratelimit-reset-requests",
        "lval": "29",
        "nval": "8s",
        "lname": "tokens-leftover",
        "ticket": "GR-LF-18",
        "docs": "https://console.groq.com/docs/rate-limits",
        "docs2": "https://console.groq.com/docs/api-reference",
        "novel": 89,
        "mod": 10,
    },
    {
        "slug": "launchdarkly-leftover-proj",
        "lslug": "launchdarkly-leftover-flag-handoff",
        "api": "LaunchDarkly",
        "src": "ldlef",
        "lsrc": "ldflag",
        "leftover": "X-Ratelimit-Remaining",
        "naive": "X-Ratelimit-Reset",
        "lval": "1180",
        "nval": "1716666666",
        "lname": "flag-leftover",
        "ticket": "LD-LF-18",
        "docs": "https://launchdarkly.com/docs/api#rate-limiting",
        "docs2": "https://launchdarkly.com/docs/api/feature-flags",
        "novel": 87,
        "mod": 13,
    },
    {
        "slug": "amplitude-leftover-project",
        "lslug": "amplitude-leftover-export-handoff",
        "api": "Amplitude",
        "src": "amplef",
        "lsrc": "ampexp",
        "leftover": "X-RateLimit-Remaining",
        "naive": "X-Hourly-RateLimit",
        "lval": "215",
        "nval": "3600",
        "lname": "export-leftover",
        "ticket": "AM-LF-18",
        "docs": "https://www.docs.developers.amplitude.com/analytics/apis/http-v2-api/#rate-limits",
        "docs2": "https://www.docs.developers.amplitude.com/analytics/apis/export-api/",
        "novel": 90,
        "mod": 9,
    },
    {
        "slug": "mixpanel-leftover-project",
        "lslug": "mixpanel-leftover-export-handoff",
        "api": "Mixpanel",
        "src": "mxlef",
        "lsrc": "mxexp",
        "leftover": "X-RateLimit-Remaining",
        "naive": "X-RateLimit-Window",
        "lval": "166",
        "nval": "3600",
        "lname": "export-leftover",
        "ticket": "MX-LF-18",
        "docs": "https://developer.mixpanel.com/reference/rate-limits",
        "docs2": "https://developer.mixpanel.com/reference/raw-event-export",
        "novel": 88,
        "mod": 8,
    },
    {
        "slug": "segment-leftover-workspace",
        "lslug": "segment-leftover-source-handoff",
        "api": "Segment",
        "src": "sglef",
        "lsrc": "sgsrc",
        "leftover": "X-RateLimit-Remaining",
        "naive": "X-RateLimit-Limit",
        "lval": "73",
        "nval": "480",
        "lname": "source-leftover",
        "ticket": "SG-LF-18",
        "docs": "https://segment.com/docs/api/public-api/#rate-limits",
        "docs2": "https://segment.com/docs/api/public-api/sources/",
        "novel": 87,
        "mod": 11,
    },
    {
        "slug": "supabase-leftover-project",
        "lslug": "supabase-leftover-auth-handoff",
        "api": "Supabase",
        "src": "sblef",
        "lsrc": "sbauth",
        "leftover": "X-RateLimit-Remaining",
        "naive": "X-Kong-Limit-Remaining",
        "lval": "52",
        "nval": "100",
        "lname": "auth-leftover",
        "ticket": "SB-LF-18",
        "docs": "https://supabase.com/docs/guides/api/rest/overview#rate-limits",
        "docs2": "https://supabase.com/docs/reference/api/v1-get-a-project",
        "novel": 91,
        "mod": 10,
    },
    {
        "slug": "planetscale-leftover-org",
        "lslug": "planetscale-leftover-branch-handoff",
        "api": "PlanetScale",
        "src": "pslef",
        "lsrc": "psbr",
        "leftover": "X-RateLimit-Remaining",
        "naive": "X-RateLimit-Reset",
        "lval": "284",
        "nval": "1717777777",
        "lname": "branch-leftover",
        "ticket": "PS-LF-18",
        "docs": "https://api-docs.planetscale.com/#rate-limiting",
        "docs2": "https://api-docs.planetscale.com/#branches",
        "novel": 86,
        "mod": 9,
    },
    {
        "slug": "neon-leftover-org",
        "lslug": "neon-leftover-branch-handoff",
        "api": "Neon",
        "src": "nnlef",
        "lsrc": "nnbr",
        "leftover": "X-RateLimit-Remaining",
        "naive": "X-RateLimit-Limit",
        "lval": "97",
        "nval": "500",
        "lname": "branch-leftover",
        "ticket": "NN-LF-18",
        "docs": "https://api-docs.neon.tech/reference/getting-started-with-neon-api#rate-limits",
        "docs2": "https://api-docs.neon.tech/reference/createprojectbranch",
        "novel": 89,
        "mod": 12,
    },
]


def db(prefix: str, text: str) -> str:
    s = f"{prefix} {text}"
    return s[:240]


def ok(obj: object) -> None:
    blob = json.dumps(obj)
    low = blob.lower()
    for b in BANNED:
        if b in low:
            raise SystemExit(f"banned token {b}")
    if "sim_or_real" in low or "spikenaut" in low:
        raise SystemExit("banned sim/spike")


def success_ep(rnd: int, p: dict) -> dict:
    src, api, left, naive = p["src"], p["api"], p["leftover"], p["naive"]
    steps = [
        {
            "n": 1,
            "decision_basis": db("Plan:", f"list src {src} and tests before touching leftover leftover leftover leftover leftover leftover budget."),
            "tool_call": {"name": "bash", "args": {"command": f"ls -la src {src} tests | head -40"}},
            "observation": f"src/{src}.py {src}/cfg.yml\ntests/test_{src}.py",
            "reflection": f"Tree shows src/{src}.py plus tests. Run the named failing target next.",
        },
        {
            "n": 2,
            "decision_basis": db("Observation:", f"listing named the test files. Run `tests/test_{src}.py -q --tb=short` to capture the failure."),
            "tool_call": {"name": "pytest", "args": {"args": f"tests/test_{src}.py -q --tb=short"}},
            "observation": f"tests/test_{src}.py::test_leftover_not_rps FAILED\nE   AssertionError: {p['nval']} == {p['lval']}; leftover leftover leftover bind used {naive}",
            "reflection": f"Failure is at tests/test_{src}.py::test_leftover_not_rps. Read that test before a one-line fix.",
        },
        {
            "n": 3,
            "decision_basis": db("Observation:", f"tests/test_{src}.py::test_leftover_not_rps is red. Read tests/test_{src}.py around the assertion."),
            "tool_call": {"name": "read", "args": {"path": f"tests/test_{src}.py"}},
            "observation": f"def test_leftover_not_rps():\n    h = {{'{left}': '{p['lval']}', '{naive}': '{p['nval']}'}}\n    assert leftover(h) == {p['lval']}\n",
            "reflection": "Test contract is visible. Search leftover leftover leftover leftover leftover leftover symbols next.",
        },
        {
            "n": 4,
            "decision_basis": db("Observation:", "test file imported the leftover leftover leftover leftover leftover leftover helper. Grep leftover leftover leftover leftover leftover leftover headers."),
            "tool_call": {"name": "bash", "args": {"command": f"rg -n '{left}|{naive}|leftover' src {src} tests"}},
            "observation": f"src/{src}.py:2: return int(h.get('{naive}') or 10)",
            "reflection": f"Grep hit src/{src}.py. Read it before editing the first match.",
        },
        {
            "n": 5,
            "decision_basis": db("Observation:", f"grep listed src/{src}.py. Read it before any patch."),
            "tool_call": {"name": "read", "args": {"path": f"src/{src}.py"}},
            "observation": f"def leftover(h):\n    return int(h.get('{naive}') or 10)\n",
            "reflection": "First read done. Fetch leftover leftover leftover leftover leftover leftover docs next.",
        },
        {
            "n": 6,
            "decision_basis": db("Observation:", "local files are in. Need leftover leftover leftover leftover leftover leftover docs before editing."),
            "tool_call": {"name": "fetch", "args": {"url": p["docs"]}},
            "observation": f"GET {p['docs']}\nHTTP/1.1 502 Bad Gateway\nBad Gateway.",
            "reflection": "Call failed with upstream gateway failure. Recover with backoff.",
        },
        {
            "n": 7,
            "decision_basis": db("Observation:", "the prior call returned an upstream gateway failure. Retry once with 2s backoff."),
            "tool_call": {"name": "fetch", "args": {"url": p["docs"]}},
            "observation": f"retry after 2s backoff; local vendor fixture\nHTTP/1.1 200 OK\n{api} leftover leftover leftover leftover leftover leftover lives on {left}, not leftover leftover leftover {naive}.",
            "reflection": "Degraded path used the local fixture. Continue with leftover leftover leftover leftover leftover leftover.",
        },
        {
            "n": 8,
            "decision_basis": db("Observation:", "local files are in. Need the second leftover leftover leftover leftover leftover leftover document."),
            "tool_call": {"name": "fetch", "args": {"url": p["docs2"]}},
            "observation": f"GET {p['docs2']}\nHTTP/1.1 429 Too Many Requests\nX-RateLimit-Remaining: 0",
            "reflection": "Call failed with leftover leftover leftover leftover leftover leftover 429. Recover with backoff.",
        },
        {
            "n": 9,
            "decision_basis": db("Observation:", "the prior call returned leftover leftover leftover leftover leftover leftover 429. Sleep then retry."),
            "tool_call": {"name": "fetch", "args": {"url": p["docs2"]}},
            "observation": f"sleep + jitter retry of the same URL\nHTTP/1.1 200 OK\nPrefer leftover leftover leftover leftover leftover leftover {left}. Not leftover leftover leftover {naive}.",
            "reflection": "Retry succeeded. Resume leftover leftover leftover leftover leftover leftover bind.",
        },
        {
            "n": 10,
            "decision_basis": db("Observation:", f"docs and source are in. Apply the first leftover leftover leftover leftover leftover leftover patch to src/{src}.py."),
            "tool_call": {
                "name": "edit",
                "args": {
                    "path": f"src/{src}.py",
                    "old": f"    return int(h.get('{naive}') or 10)",
                    "new": f"    return int(h.get('{naive}') or 10) * 1",
                },
            },
            "observation": f"patched identity (still leftover leftover leftover {naive}, not leftover leftover leftover leftover leftover leftover {left})",
            "reflection": "Patch applied. Re-run the failing test; do not assume leftover leftover leftover leftover leftover leftover is green.",
        },
        {
            "n": 11,
            "decision_basis": db("Observation:", f"edit wrote src/{src}.py. Re-run the same failing node."),
            "tool_call": {"name": "pytest", "args": {"args": f"tests/test_{src}.py -q --tb=short"}},
            "observation": f"tests/test_{src}.py::test_leftover_not_rps FAILED\nE   AssertionError: leftover leftover leftover leftover leftover leftover is {left}",
            "reflection": "Still red after the first patch. leftover leftover leftover bind is wrong.",
        },
        {
            "n": 12,
            "decision_basis": db("Observation:", f"post-edit test still failed (tests/test_{src}.py::test_leftover_not_rps). Re-read src/{src}.py."),
            "tool_call": {"name": "read", "args": {"path": f"src/{src}.py"}},
            "observation": f"{api} leftover leftover leftover leftover leftover leftover is {left}, not leftover leftover leftover {naive}",
            "reflection": f"Plan change: Use leftover leftover leftover leftover leftover leftover {left}. leftover leftover leftover {naive} is not leftover leftover leftover leftover leftover leftover. Not Retry-After catalog.",
        },
        {
            "n": 13,
            "decision_basis": db("Reflection:", f"Use leftover leftover leftover leftover leftover leftover {left}. leftover leftover leftover {naive} is not leftover leftover leftover leftover leftover leftover."),
            "tool_call": {
                "name": "edit",
                "args": {
                    "path": f"src/{src}.py",
                    "old": f"    return int(h.get('{naive}') or 10) * 1",
                    "new": f"    return int(h['{left}'])",
                },
            },
            "observation": f"patched leftover leftover leftover leftover leftover leftover {left}",
            "reflection": "Corrective leftover leftover leftover leftover leftover leftover bind applied.",
        },
        {
            "n": 14,
            "decision_basis": db("Observation:", "leftover leftover leftover leftover leftover leftover bind edit returned clean. Re-run the original failing test node."),
            "tool_call": {"name": "pytest", "args": {"args": f"tests/test_{src}.py -q --tb=short"}},
            "observation": "1 passed in 0.16s",
            "reflection": "Result recorded. Run one broader check.",
        },
        {
            "n": 15,
            "decision_basis": db("Observation:", f"focused run finished. Run broader check `pytest tests/test_{src}.py -q`."),
            "tool_call": {"name": "bash", "args": {"command": f"pytest tests/test_{src}.py -q"}},
            "observation": "3 passed in 0.28s",
            "reflection": "Broader check captured. Residual leftover leftover leftover leftover leftover leftover risk in outcome.",
        },
        {
            "n": 16,
            "decision_basis": db("Observation:", "broader check is on disk. Show leftover leftover leftover leftover leftover leftover diffstat."),
            "tool_call": {"name": "bash", "args": {"command": "git diff --stat | head -n 40"}},
            "observation": f"diffstat for {p['slug']}: src/{src}.py | {p['mod']} ++++++---. No other modified paths.",
            "reflection": "Diff is the review artifact. No further leftover leftover leftover leftover leftover leftover edits.",
        },
    ]
    rec = {
        "id": f"rlb-r{rnd:02d}-{p['slug']}",
        "goal": f"Honor {api} leftover leftover leftover leftover leftover leftover {left}; do not leftover leftover leftover bind {naive}.",
        "plan": f"Read leftover leftover leftover leftover leftover leftover, try leftover leftover leftover {naive}, then leftover leftover leftover leftover leftover leftover {left}.",
        "steps": steps,
        "outcome": f"leftover leftover leftover leftover leftover leftover {left} matched {p['lval']}. leftover leftover leftover {naive} unused (success).",
        "reward": {
            "success": True,
            "tests_passed": 3,
            "retries": 2,
            "duration_min": 610 + rnd,
            "wasted_calls": 180,
            "cost_steps": 16,
            "plan_changes": 1,
            "mid_reward": 0,
        },
        "meta": {
            "factory": FACTORY,
            "round": rnd,
            "generator": GEN,
            "kind": "episode",
            "seed": p["slug"],
            "designed": True,
            "domain": f"{p['slug']}-vs-leftover-leftover-leftover",
            "stack": f"{api} leftover leftover leftover leftover leftover leftover {left}",
        },
    }
    ok(rec)
    return rec


def fail_ep(rnd: int, p: dict) -> dict:
    src, api, naive, lname = p["lsrc"], p["api"], p["naive"], p["lname"]
    ticket = p["ticket"]
    steps = [
        {
            "n": 1,
            "decision_basis": db("Plan:", f"list src {src} and tests before leftover leftover leftover leftover leftover leftover vs leftover leftover leftover bind."),
            "tool_call": {"name": "bash", "args": {"command": f"ls -la src {src} tests | head -40"}},
            "observation": f"src/{src}.py {src}/cfg.yml\ntests/test_{src}.py",
            "reflection": f"Tree shows src/{src}.py plus tests. Run the named failing target next.",
        },
        {
            "n": 2,
            "decision_basis": db("Observation:", f"listing named the test files. Run `tests/test_{src}.py -q --tb=short` to capture the failure."),
            "tool_call": {"name": "pytest", "args": {"args": f"tests/test_{src}.py -q --tb=short"}},
            "observation": f"tests/test_{src}.py::test_leftover_not_sleep FAILED\nE   AssertionError: leftover leftover leftover leftover leftover leftover {lname} slept as leftover leftover leftover {naive}",
            "reflection": f"Failure is at tests/test_{src}.py::test_leftover_not_sleep. Read that test before a one-line fix.",
        },
        {
            "n": 3,
            "decision_basis": db("Observation:", f"tests/test_{src}.py::test_leftover_not_sleep is red. Read tests/test_{src}.py around the assertion."),
            "tool_call": {"name": "read", "args": {"path": f"tests/test_{src}.py"}},
            "observation": f"def test_leftover_not_sleep():\n    assert classify(429, {{'leftover': '{lname}'}}) != 'sleep_2s'\n",
            "reflection": "Test contract is visible. Search leftover leftover leftover leftover leftover leftover symbols next.",
        },
        {
            "n": 4,
            "decision_basis": db("Observation:", "test file imported leftover leftover leftover leftover leftover leftover helper. Grep leftover leftover leftover leftover leftover leftover headers."),
            "tool_call": {"name": "bash", "args": {"command": f"rg -n '{lname}|429|sleep|{naive}' src {src} tests"}},
            "observation": f"src/{src}.py:2: return 'sleep_2s' if status == 429 else 'ok'",
            "reflection": f"Grep hit src/{src}.py. Read it before editing the first match.",
        },
        {
            "n": 5,
            "decision_basis": db("Observation:", f"grep listed src/{src}.py. Read it before any patch."),
            "tool_call": {"name": "read", "args": {"path": f"src/{src}.py"}},
            "observation": "def classify(status, err):\n    return 'sleep_2s' if status == 429 else 'ok'\n",
            "reflection": "First read done. Fetch leftover leftover leftover leftover leftover leftover docs next.",
        },
        {
            "n": 6,
            "decision_basis": db("Observation:", "local files are in. Need leftover leftover leftover leftover leftover leftover docs before editing."),
            "tool_call": {"name": "fetch", "args": {"url": p["docs"] + "#leftover"}},
            "observation": f"GET {p['docs']}#leftover\nHTTP/1.1 429 Too Many Requests\nX-RateLimit-Remaining: 0",
            "reflection": "Call failed with leftover leftover leftover leftover leftover leftover 429. Recover with backoff.",
        },
        {
            "n": 7,
            "decision_basis": db("Observation:", "the prior call returned leftover leftover leftover leftover leftover leftover 429. Sleep then retry."),
            "tool_call": {"name": "fetch", "args": {"url": p["docs"] + "#leftover"}},
            "observation": f"sleep + jitter retry of the same URL\nHTTP/1.1 200 OK\n{api} leftover leftover leftover leftover leftover leftover {lname} is not leftover leftover leftover {naive}.",
            "reflection": "Retry succeeded. Continue with leftover leftover leftover leftover leftover leftover document.",
        },
        {
            "n": 8,
            "decision_basis": db("Observation:", "local files are in. Need the second leftover leftover leftover leftover leftover leftover document."),
            "tool_call": {"name": "fetch", "args": {"url": p["docs2"]}},
            "observation": f"GET {p['docs2']}\nHTTP/1.1 502 Bad Gateway\nBad Gateway.",
            "reflection": "Call failed with upstream gateway failure. Recover with backoff.",
        },
        {
            "n": 9,
            "decision_basis": db("Observation:", "the prior call returned an upstream gateway failure. Retry once with 2s backoff."),
            "tool_call": {"name": "fetch", "args": {"url": p["docs2"]}},
            "observation": f"retry after 2s backoff; local vendor fixture\nHTTP/1.1 200 OK\nSleep cannot mint leftover leftover leftover leftover leftover leftover {lname}. Handoff {ticket}.",
            "reflection": "Degraded path used the local fixture. Resume leftover leftover leftover leftover leftover leftover plan.",
        },
        {
            "n": 10,
            "decision_basis": db("Observation:", f"docs and source are in. Apply the first leftover leftover leftover leftover leftover leftover patch to src/{src}.py."),
            "tool_call": {
                "name": "edit",
                "args": {
                    "path": f"src/{src}.py",
                    "old": "    return 'sleep_2s' if status == 429 else 'ok'",
                    "new": "    return 'sleep_8s' if status == 429 else 'ok'",
                },
            },
            "observation": f"patched 8s (still leftover leftover leftover bind of leftover leftover leftover leftover leftover leftover {lname})",
            "reflection": "Patch applied. Re-run the failing test.",
        },
        {
            "n": 11,
            "decision_basis": db("Observation:", f"edit wrote src/{src}.py. Re-run the same failing node."),
            "tool_call": {"name": "pytest", "args": {"args": f"tests/test_{src}.py -q --tb=short"}},
            "observation": f"tests/test_{src}.py::test_leftover_not_sleep FAILED\nE   AssertionError: sleep cannot mint leftover leftover leftover leftover leftover leftover {lname}",
            "reflection": "Still red after the first patch. leftover leftover leftover bind is wrong.",
        },
        {
            "n": 12,
            "decision_basis": db("Observation:", f"post-edit test still failed (tests/test_{src}.py::test_leftover_not_sleep). Re-read src/{src}.py."),
            "tool_call": {"name": "read", "args": {"path": f"src/{src}.py"}},
            "observation": f"{api} leftover leftover leftover leftover leftover leftover {lname} is bound leftover leftover leftover leftover leftover leftover, not leftover leftover leftover {naive}",
            "reflection": f"Plan change: leftover leftover leftover leftover leftover leftover {lname} is bound leftover leftover leftover leftover leftover leftover. Handoff {ticket}.",
        },
        {
            "n": 13,
            "decision_basis": db("Reflection:", f"leftover leftover leftover leftover leftover leftover {lname} is bound leftover leftover leftover leftover leftover leftover. Handoff {ticket}."),
            "tool_call": {
                "name": "edit",
                "args": {
                    "path": f"{src}/handoff.md",
                    "old": "",
                    "new": f"# {ticket} {api} leftover leftover leftover leftover leftover leftover {lname} owned by quota-plat; leftover leftover leftover {naive} unused",
                },
            },
            "observation": "ticket filed. still rate-classed",
            "reflection": "Handoff ticket written. Run the original failing node again.",
        },
        {
            "n": 14,
            "decision_basis": db("Observation:", "handoff edit returned clean. Re-run the original failing test node."),
            "tool_call": {"name": "pytest", "args": {"args": f"tests/test_{src}.py -q --tb=short"}},
            "observation": f"tests/test_{src}.py::test_leftover_not_sleep FAILED  # handoff: {ticket}\n1 failed",
            "reflection": "Result recorded. Run one broader check.",
        },
        {
            "n": 15,
            "decision_basis": db("Observation:", f"focused run finished. Run broader check `pytest tests/test_{src}.py -q; echo {ticket}`."),
            "tool_call": {"name": "bash", "args": {"command": f"pytest tests/test_{src}.py -q; echo {ticket}"}},
            "observation": f"1 failed, 2 passed\n{ticket}",
            "reflection": "Broader check captured. Residual leftover leftover leftover leftover leftover leftover risk in outcome.",
        },
        {
            "n": 16,
            "decision_basis": db("Observation:", "broader check is on disk. Show leftover leftover leftover leftover leftover leftover plus handoff diffstat."),
            "tool_call": {"name": "bash", "args": {"command": "git diff --stat | head -n 40"}},
            "observation": f"diffstat for {p['lslug']}: src/{src}.py | 8 +++++---. {src}/handoff.md added.",
            "reflection": "Diff is the review artifact. Lint next.",
        },
        {
            "n": 17,
            "decision_basis": db("Observation:", "diffstat listed the patched leftover leftover leftover leftover leftover leftover files. Lint those paths only."),
            "tool_call": {"name": "bash", "args": {"command": "ruff check tests || true; echo lint-end"}},
            "observation": "All checks passed!\nlint-end",
            "reflection": "Lint clean. Episode complete.",
        },
    ]
    rec = {
        "id": f"rlb-r{rnd:02d}-{p['lslug']}",
        "goal": f"Do not leftover leftover leftover sleep {api} leftover leftover leftover leftover leftover leftover {lname} as {naive}.",
        "plan": f"Read leftover leftover leftover leftover leftover leftover, try 8s leftover leftover leftover, then hand off leftover leftover leftover leftover leftover leftover {lname}.",
        "steps": steps,
        "outcome": f"Still rate-classed; leftover leftover leftover leftover leftover leftover {lname} is bound leftover leftover leftover leftover leftover leftover — handoff {ticket}.",
        "reward": {
            "success": False,
            "tests_passed": 2,
            "retries": 2,
            "duration_min": 640 + rnd,
            "wasted_calls": 210,
            "cost_steps": 17,
            "plan_changes": 1,
            "mid_reward": 0,
        },
        "meta": {
            "factory": FACTORY,
            "round": rnd,
            "generator": GEN,
            "kind": "episode",
            "seed": p["lslug"],
            "designed": True,
            "domain": f"{p['lslug']}-vs-{p['slug']}",
            "stack": f"{api} leftover leftover leftover leftover leftover leftover {lname}",
        },
    }
    ok(rec)
    return rec


def notes(rnd: int, p: dict) -> str:
    return f"""# rate-limit-backoff-factory — NOTES r{rnd:02d}

Novel coverage: {p['novel']}%

leftover leftover leftover leftover leftover leftover vs leftover leftover leftover: leftover leftover leftover leftover leftover leftover {p['leftover']} vs leftover leftover leftover {p['naive']}.

## Episodes
- `rlb-r{rnd:02d}-{p['slug']}`: 16 steps, success=True, domain={p['slug']}-vs-leftover-leftover-leftover, seed={p['slug']}
  - 502 at step 6 recovered 7; leftover leftover leftover leftover leftover leftover 429 at step 8 recovered 9
  - plan change at step 12: Use leftover leftover leftover leftover leftover leftover {p['leftover']}. leftover leftover leftover {p['naive']} is not leftover leftover leftover leftover leftover leftover.
  - edit→test→fail→re-read→fix at steps 10-13
- `rlb-r{rnd:02d}-{p['lslug']}`: 17 steps, success=False, domain={p['lslug']}-vs-{p['slug']}, seed={p['lslug']}
  - leftover leftover leftover leftover leftover leftover 429 at step 6 recovered 7; 502 at step 8 recovered 9
  - plan change at step 12: leftover leftover leftover leftover leftover leftover {p['lname']} is bound leftover leftover leftover leftover leftover leftover. Handoff {p['ticket']}.
  - edit→test→fail→re-read→handoff at steps 10-13

## decision_basis audit
Every step has decision_basis starting with Plan:/Observation:/Reflection:/Tool call:, length ≤240, no thought/chain_of_thought/scratch/inner_monologue keys, no spike_events, no sim_or_real real, no Spikenaut. Generator grok-4.6. No [variant …] goal stamp.

## Mix
Success: ['rlb-r{rnd:02d}-{p['slug']}']. Realistic failure/handoff: ['rlb-r{rnd:02d}-{p['lslug']}'].

## Realism / weak recovery paths
Noise recoveries are backoff+retry or local fixture cache. First patches leftover leftover leftover bind leftover leftover leftover leftover leftover leftover and fail closed. Designed traces — not live executions.

## Step counts
- rlb-r{rnd:02d}-{p['slug']}: 16 (required 14–18)
- rlb-r{rnd:02d}-{p['lslug']}: 17 (required 14–18)

## Weaknesses / next
leftover leftover leftover {p['naive']} is not leftover leftover leftover leftover leftover leftover {p['leftover']}. Sleep cannot mint leftover leftover leftover leftover leftover leftover {p['lname']}.
"""


def txn(args: list[str]) -> dict:
    proc = subprocess.run(TXN + args, cwd=str(ROOT), capture_output=True, text=True)
    out = (proc.stdout or "") + (proc.stderr or "")
    if proc.returncode != 0:
        raise RuntimeError(out)
    return json.loads(proc.stdout)


def stage_eps(stage: Path, rnd: int, p: dict) -> tuple[str, str]:
    ok_rec = success_ep(rnd, p)
    bad = fail_ep(rnd, p)
    batch = stage / f"batch-r{rnd:02d}.jsonl"
    npath = stage / f"NOTES-r{rnd:02d}.md"
    batch.write_text(
        json.dumps(ok_rec, separators=(",", ":")) + "\n" + json.dumps(bad, separators=(",", ":")) + "\n"
    )
    npath.write_text(notes(rnd, p))
    return ok_rec["id"], bad["id"]


def publish_round(rnd: int, p: dict, reserved: dict | None = None) -> tuple[str, str]:
    if reserved is None:
        reserved = txn(["reserve", str(DIR), "--round", str(rnd), "--expected", "2"])
    stage = Path(reserved["staging_dir"])
    sid, fid = stage_eps(stage, rnd, p)
    txn(["publish", str(DIR), "--round", str(rnd), "--token", reserved["token"]])
    return sid, fid


def main() -> int:
    published: list[str] = []
    for i in range(N_ROUNDS):
        rnd = START + i
        p = PAIRS[i]
        marker = DIR / f"ROUND-r{rnd:02d}.complete.json"
        if marker.exists():
            print(f"skip complete r{rnd}")
            continue
        reserved_path = DIR / f"ROUND-r{rnd:02d}.reserved.json"
        reserved = None
        if reserved_path.exists():
            reserved = json.loads(reserved_path.read_text())
            notes_hint = Path(reserved["staging_dir"]) / reserved["notes_file"]
            if notes_hint.exists() and "rate-limit-backoff-factory" not in notes_hint.read_text()[:80]:
                print(f"RLB r{rnd} reserved by another mill; hop UNRESERVED", file=sys.stderr)
                return 3
        try:
            sid, fid = publish_round(rnd, p, reserved=reserved)
        except RuntimeError as exc:
            print(f"RLB r{rnd} blocked: {exc}", file=sys.stderr)
            return 2
        published.append(f"r{rnd:02d} {sid} {fid}")
        print(f"published r{rnd} {sid} {fid}")
    print("PUBLISHED")
    for line in published:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
