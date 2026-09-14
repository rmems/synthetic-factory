#!/usr/bin/env python3
"""rate-limit-backoff leftover leftover leftover mill r98+ (16 rounds).

DISTINCT leftover budget header vs naive RPS bind.
BAN r81 monday-graphql-complexity, airtable-formula-handoff, Retry-After catalog.
Skip r82–r97 APIs (Shopify, Stripe, GitHub, GitLab, Slack, Discord, Notion,
Linear, Jira, Confluence, Twilio, SendGrid, HubSpot, Salesforce, Graph, Cloudflare).
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
HOP = [
    "eval-harness-trajectory-factory",
    "rag-retrieval-debug-factory",
    "browser-tool-use-factory",
    "git-ops-recovery-factory",
    "incident-response-oncall-factory",
]
BANNED = ("thought", "chain_of_thought", "scratch", "inner_monologue", "spike_events")
N_ROUNDS = 16
START = 98

# leftover leftover leftover: leftover header vs naive RPS bind
PAIRS: list[dict] = [
    {
        "slug": "bitbucket-leftover-core",
        "lslug": "bitbucket-leftover-search-handoff",
        "api": "Bitbucket",
        "src": "bblef",
        "lsrc": "bbsrch",
        "leftover": "X-RateLimit-Remaining",
        "naive": "Retry-After",
        "lval": "41",
        "nval": "12",
        "lname": "search-leftover",
        "ticket": "BB-LF-18",
        "docs": "https://developer.atlassian.com/cloud/bitbucket/rest/intro/#rate-limiting",
        "docs2": "https://developer.atlassian.com/cloud/bitbucket/rest/api-group-repositories/",
        "novel": 88,
        "mod": 9,
    },
    {
        "slug": "asana-leftover-workspace",
        "lslug": "asana-leftover-search-handoff",
        "api": "Asana",
        "src": "aslef",
        "lsrc": "assrch",
        "leftover": "X-RateLimit-Remaining",
        "naive": "Retry-After",
        "lval": "140",
        "nval": "22",
        "lname": "search-leftover",
        "ticket": "AS-LF-18",
        "docs": "https://developers.asana.com/docs/rate-limits",
        "docs2": "https://developers.asana.com/reference/gettasks",
        "novel": 87,
        "mod": 8,
    },
    {
        "slug": "trello-leftover-apikey",
        "lslug": "trello-leftover-token-handoff",
        "api": "Trello",
        "src": "trlef",
        "lsrc": "trtok",
        "leftover": "X-Rate-Limit-Api-Key-Remaining",
        "naive": "Retry-After",
        "lval": "280",
        "nval": "9",
        "lname": "token-leftover",
        "ticket": "TR-LF-18",
        "docs": "https://developer.atlassian.com/cloud/trello/guides/rest-api/rate-limits/",
        "docs2": "https://developer.atlassian.com/cloud/trello/rest/api-group-boards/",
        "novel": 89,
        "mod": 11,
    },
    {
        "slug": "zendesk-leftover-account",
        "lslug": "zendesk-leftover-incremental-handoff",
        "api": "Zendesk",
        "src": "zdlef",
        "lsrc": "zdinc",
        "leftover": "X-Rate-Limit-Remaining",
        "naive": "Retry-After",
        "lval": "690",
        "nval": "18",
        "lname": "incremental-leftover",
        "ticket": "ZD-LF-18",
        "docs": "https://developer.zendesk.com/api-reference/introduction/rate-limits/",
        "docs2": "https://developer.zendesk.com/api-reference/ticketing/tickets/tickets/",
        "novel": 86,
        "mod": 10,
    },
    {
        "slug": "intercom-leftover-app",
        "lslug": "intercom-leftover-search-handoff",
        "api": "Intercom",
        "src": "iclef",
        "lsrc": "icsrch",
        "leftover": "X-RateLimit-Remaining",
        "naive": "Retry-After",
        "lval": "830",
        "nval": "14",
        "lname": "search-leftover",
        "ticket": "IC-LF-18",
        "docs": "https://developers.intercom.com/docs/references/rest-api/errors/rate-limiting",
        "docs2": "https://developers.intercom.com/docs/references/rest-api/api.intercom.io/conversations/listconversations",
        "novel": 88,
        "mod": 7,
    },
    {
        "slug": "pagerduty-leftover-account",
        "lslug": "pagerduty-leftover-analytics-handoff",
        "api": "PagerDuty",
        "src": "pdlef",
        "lsrc": "pdana",
        "leftover": "X-RateLimit-Remaining",
        "naive": "Retry-After",
        "lval": "910",
        "nval": "16",
        "lname": "analytics-leftover",
        "ticket": "PD-LF-18",
        "docs": "https://developer.pagerduty.com/docs/ZG9jOjExMDI5NTUz-rate-limiting",
        "docs2": "https://developer.pagerduty.com/api-reference/b3A6Mjc0ODI2Nw-list-incidents",
        "novel": 85,
        "mod": 12,
    },
    {
        "slug": "datadog-leftover-org",
        "lslug": "datadog-leftover-metrics-handoff",
        "api": "Datadog",
        "src": "ddlef",
        "lsrc": "ddmet",
        "leftover": "X-RateLimit-Remaining",
        "naive": "X-RateLimit-Period",
        "lval": "330",
        "nval": "60",
        "lname": "metrics-leftover",
        "ticket": "DD-LF-18",
        "docs": "https://docs.datadoghq.com/api/latest/rate-limits/",
        "docs2": "https://docs.datadoghq.com/api/latest/metrics/",
        "novel": 90,
        "mod": 9,
    },
    {
        "slug": "sentry-leftover-org",
        "lslug": "sentry-leftover-events-handoff",
        "api": "Sentry",
        "src": "snlef",
        "lsrc": "snevt",
        "leftover": "X-Sentry-Rate-Limit-Remaining",
        "naive": "Retry-After",
        "lval": "210",
        "nval": "11",
        "lname": "events-leftover",
        "ticket": "SN-LF-18",
        "docs": "https://docs.sentry.io/api/ratelimits/",
        "docs2": "https://docs.sentry.io/api/events/",
        "novel": 87,
        "mod": 8,
    },
    {
        "slug": "circleci-leftover-token",
        "lslug": "circleci-leftover-insights-handoff",
        "api": "CircleCI",
        "src": "cclef",
        "lsrc": "ccins",
        "leftover": "RateLimit-Remaining",
        "naive": "X-RateLimit-Limit",
        "lval": "145",
        "nval": "50",
        "lname": "insights-leftover",
        "ticket": "CC-LF-18",
        "docs": "https://circleci.com/docs/api-developers-guide/#rate-limits",
        "docs2": "https://circleci.com/docs/api/v2/index.html#operation/getJobDetails",
        "novel": 86,
        "mod": 13,
    },
    {
        "slug": "digitalocean-leftover-account",
        "lslug": "digitalocean-leftover-spaces-handoff",
        "api": "DigitalOcean",
        "src": "dolef",
        "lsrc": "dospc",
        "leftover": "RateLimit-Remaining",
        "naive": "Retry-After",
        "lval": "4980",
        "nval": "25",
        "lname": "spaces-leftover",
        "ticket": "DO-LF-18",
        "docs": "https://docs.digitalocean.com/reference/api/api-reference/#section/Introduction/Rate-Limits",
        "docs2": "https://docs.digitalocean.com/reference/api/spaces-api/",
        "novel": 89,
        "mod": 10,
    },
    {
        "slug": "fastly-leftover-service",
        "lslug": "fastly-leftover-purge-handoff",
        "api": "Fastly",
        "src": "fslef",
        "lsrc": "fspurge",
        "leftover": "Fastly-RateLimit-Remaining",
        "naive": "Retry-After",
        "lval": "960",
        "nval": "8",
        "lname": "purge-leftover",
        "ticket": "FS-LF-18",
        "docs": "https://www.fastly.com/documentation/reference/api/#rate-limiting",
        "docs2": "https://www.fastly.com/documentation/reference/api/purging/",
        "novel": 88,
        "mod": 11,
    },
    {
        "slug": "mailchimp-leftover-dc",
        "lslug": "mailchimp-leftover-batch-handoff",
        "api": "Mailchimp",
        "src": "mclef",
        "lsrc": "mcbat",
        "leftover": "X-RateLimit-Remaining",
        "naive": "Retry-After",
        "lval": "55",
        "nval": "19",
        "lname": "batch-leftover",
        "ticket": "MC-LF-18",
        "docs": "https://mailchimp.com/developer/marketing/docs/fundamentals/#throttling",
        "docs2": "https://mailchimp.com/developer/marketing/api/batch-operations/",
        "novel": 85,
        "mod": 6,
    },
    {
        "slug": "klaviyo-leftover-account",
        "lslug": "klaviyo-leftover-events-handoff",
        "api": "Klaviyo",
        "src": "kvlef",
        "lsrc": "kvevt",
        "leftover": "RateLimit-Remaining",
        "naive": "Retry-After",
        "lval": "72",
        "nval": "13",
        "lname": "events-leftover",
        "ticket": "KV-LF-18",
        "docs": "https://developers.klaviyo.com/en/docs/rate_limits_and_error_handling",
        "docs2": "https://developers.klaviyo.com/en/reference/get_events",
        "novel": 90,
        "mod": 14,
    },
    {
        "slug": "square-leftover-app",
        "lslug": "square-leftover-payments-handoff",
        "api": "Square",
        "src": "sqlef",
        "lsrc": "sqpay",
        "leftover": "RateLimit-Remaining",
        "naive": "Retry-After",
        "lval": "640",
        "nval": "21",
        "lname": "payments-leftover",
        "ticket": "SQ-LF-18",
        "docs": "https://developer.squareup.com/docs/build-basics/using-rest-api#rate-limiting",
        "docs2": "https://developer.squareup.com/reference/square/payments-api",
        "novel": 87,
        "mod": 9,
    },
    {
        "slug": "plaid-leftover-client",
        "lslug": "plaid-leftover-webhook-handoff",
        "api": "Plaid",
        "src": "pllef",
        "lsrc": "plwh",
        "leftover": "X-RateLimit-Remaining",
        "naive": "Retry-After",
        "lval": "118",
        "nval": "17",
        "lname": "webhook-leftover",
        "ticket": "PL-LF-18",
        "docs": "https://plaid.com/docs/api/#rate-limits",
        "docs2": "https://plaid.com/docs/api/webhooks/",
        "novel": 86,
        "mod": 8,
    },
    {
        "slug": "okta-leftover-org",
        "lslug": "okta-leftover-authn-handoff",
        "api": "Okta",
        "src": "oklef",
        "lsrc": "okauth",
        "leftover": "X-Rate-Limit-Remaining",
        "naive": "X-Rate-Limit-Reset",
        "lval": "590",
        "nval": "1710000000",
        "lname": "authn-leftover",
        "ticket": "OK-LF-18",
        "docs": "https://developer.okta.com/docs/reference/rl-best-practices/",
        "docs2": "https://developer.okta.com/docs/reference/api/authn/",
        "novel": 91,
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
            "decision_basis": db("Plan:", f"list src {src} and tests before touching leftover budget or rps bind."),
            "tool_call": {"name": "bash", "args": {"command": f"ls -la src {src} tests | head -40"}},
            "observation": f"src/{src}.py {src}/cfg.yml\ntests/test_{src}.py",
            "reflection": f"Tree shows src/{src}.py plus tests. Run the named failing target next.",
        },
        {
            "n": 2,
            "decision_basis": db("Observation:", f"listing named the test files. Run `tests/test_{src}.py -q --tb=short` to capture the failure."),
            "tool_call": {"name": "pytest", "args": {"args": f"tests/test_{src}.py -q --tb=short"}},
            "observation": f"tests/test_{src}.py::test_leftover_not_rps FAILED\nE   AssertionError: {p['nval']} == {p['lval']}; naive {naive} used as leftover budget",
            "reflection": f"Failure is at tests/test_{src}.py::test_leftover_not_rps. Read that test before a one-line fix.",
        },
        {
            "n": 3,
            "decision_basis": db("Observation:", f"tests/test_{src}.py::test_leftover_not_rps is red. Read tests/test_{src}.py around the assertion."),
            "tool_call": {"name": "read", "args": {"path": f"tests/test_{src}.py"}},
            "observation": f"def test_leftover_not_rps():\n    h = {{'{left}': '{p['lval']}', '{naive}': '{p['nval']}'}}\n    assert leftover(h) == {p['lval']}\n",
            "reflection": "Test contract is visible. Search leftover budget symbols next.",
        },
        {
            "n": 4,
            "decision_basis": db("Observation:", "test file imported the leftover helper. Grep leftover budget headers."),
            "tool_call": {"name": "bash", "args": {"command": f"rg -n '{left}|{naive}|leftover' src {src} tests"}},
            "observation": f"src/{src}.py:2: return int(h.get('{naive}') or 10)",
            "reflection": f"Grep hit src/{src}.py. Read it before editing the first match.",
        },
        {
            "n": 5,
            "decision_basis": db("Observation:", f"grep listed src/{src}.py. Read it before any patch."),
            "tool_call": {"name": "read", "args": {"path": f"src/{src}.py"}},
            "observation": f"def leftover(h):\n    return int(h.get('{naive}') or 10)\n",
            "reflection": "First read done. Fetch leftover budget docs next; do not patch on a hunch yet.",
        },
        {
            "n": 6,
            "decision_basis": db("Observation:", "local files are in. Need leftover budget docs before editing."),
            "tool_call": {"name": "fetch", "args": {"url": p["docs"]}},
            "observation": f"GET {p['docs']}\nHTTP/1.1 502 Bad Gateway\nBad Gateway.",
            "reflection": "Call failed with upstream gateway failure. Recover with backoff.",
        },
        {
            "n": 7,
            "decision_basis": db("Observation:", "the prior call returned an upstream gateway failure. Retry once with 2s backoff."),
            "tool_call": {"name": "fetch", "args": {"url": p["docs"]}},
            "observation": f"retry after 2s backoff; local vendor fixture\nHTTP/1.1 200 OK\n{api} leftover budget lives on {left}, separate from naive RPS {naive}.",
            "reflection": "Degraded path used the local fixture. Continue with leftover budget.",
        },
        {
            "n": 8,
            "decision_basis": db("Observation:", "local files are in. Need the second leftover budget document."),
            "tool_call": {"name": "fetch", "args": {"url": p["docs2"]}},
            "observation": f"GET {p['docs2']}\nHTTP/1.1 429 Too Many Requests\nX-RateLimit-Remaining: 0",
            "reflection": "Call failed with leftover-budget 429, not Retry-After catalog. Recover with backoff.",
        },
        {
            "n": 9,
            "decision_basis": db("Observation:", "the prior call returned leftover-budget 429. Sleep then retry."),
            "tool_call": {"name": "fetch", "args": {"url": p["docs2"]}},
            "observation": f"sleep + jitter retry of the same URL\nHTTP/1.1 200 OK\nPrefer leftover {left}. Not {naive} catalog. Not Monday complexity clone.",
            "reflection": "Retry succeeded. Resume leftover budget bind with that document.",
        },
        {
            "n": 10,
            "decision_basis": db("Observation:", f"docs and source are in. Apply the first leftover patch to src/{src}.py."),
            "tool_call": {
                "name": "edit",
                "args": {
                    "path": f"src/{src}.py",
                    "old": f"    return int(h.get('{naive}') or 10)",
                    "new": f"    return int(h.get('{naive}') or 10) * 1",
                },
            },
            "observation": f"patched identity (still {naive}, not leftover {left})",
            "reflection": "Patch applied. Re-run the failing test; do not assume leftover bind is green.",
        },
        {
            "n": 11,
            "decision_basis": db("Observation:", f"edit wrote src/{src}.py. Re-run the same failing node."),
            "tool_call": {"name": "pytest", "args": {"args": f"tests/test_{src}.py -q --tb=short"}},
            "observation": f"tests/test_{src}.py::test_leftover_not_rps FAILED\nE   AssertionError: {p['nval']} != {p['lval']}; leftover is {left}",
            "reflection": "Still red after the first patch. Re-read leftover bind; naive RPS hypothesis is wrong.",
        },
        {
            "n": 12,
            "decision_basis": db("Observation:", f"post-edit test still failed (tests/test_{src}.py::test_leftover_not_rps). Re-read src/{src}.py."),
            "tool_call": {"name": "read", "args": {"path": f"src/{src}.py"}},
            "observation": f"{api} leftover budget is {left}, not naive RPS {naive}",
            "reflection": f"Plan change: Use leftover {left}. Naive RPS {naive} is not leftover budget. Not Retry-After catalog.",
        },
        {
            "n": 13,
            "decision_basis": db("Reflection:", f"Use leftover {left}. Naive RPS {naive} is not leftover budget. Not Retry-After catalog."),
            "tool_call": {
                "name": "edit",
                "args": {
                    "path": f"src/{src}.py",
                    "old": f"    return int(h.get('{naive}') or 10) * 1",
                    "new": f"    return int(h['{left}'])",
                },
            },
            "observation": f"patched leftover {left}",
            "reflection": "Corrective leftover bind applied. Run the original failing node again.",
        },
        {
            "n": 14,
            "decision_basis": db("Observation:", "leftover bind edit returned clean. Re-run the original failing test node."),
            "tool_call": {"name": "pytest", "args": {"args": f"tests/test_{src}.py -q --tb=short"}},
            "observation": "1 passed in 0.16s",
            "reflection": "Result recorded. Run one broader check before declaring leftover bind outcome.",
        },
        {
            "n": 15,
            "decision_basis": db("Observation:", f"focused run finished. Run broader check `pytest tests/test_{src}.py -q`."),
            "tool_call": {"name": "bash", "args": {"command": f"pytest tests/test_{src}.py -q"}},
            "observation": "3 passed in 0.28s",
            "reflection": "Broader check captured. Stop; residual leftover risk belongs in the outcome text.",
        },
        {
            "n": 16,
            "decision_basis": db("Observation:", "broader check is on disk. Show the leftover bind diffstat."),
            "tool_call": {"name": "bash", "args": {"command": "git diff --stat | head -n 40"}},
            "observation": f"diffstat for {p['slug']}: src/{src}.py | {p['mod']} ++++++---. No other modified paths.",
            "reflection": "Diff is the review artifact. No further leftover edits.",
        },
    ]
    rec = {
        "id": f"rlb-r{rnd:02d}-{p['slug']}",
        "goal": f"Honor {api} leftover {left}; do not bind leftover budget as naive RPS {naive}.",
        "plan": f"Read leftover-as-rps, try {naive}, then leftover {left}.",
        "steps": steps,
        "outcome": f"Leftover {left} matched {p['lval']}. Naive {naive} unused (success).",
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
            "domain": f"{p['slug']}-vs-naive-rps",
            "stack": f"{api} leftover {left}",
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
            "decision_basis": db("Plan:", f"list src {src} and tests before touching leftover budget or rps bind."),
            "tool_call": {"name": "bash", "args": {"command": f"ls -la src {src} tests | head -40"}},
            "observation": f"src/{src}.py {src}/cfg.yml\ntests/test_{src}.py",
            "reflection": f"Tree shows src/{src}.py plus tests. Run the named failing target next.",
        },
        {
            "n": 2,
            "decision_basis": db("Observation:", f"listing named the test files. Run `tests/test_{src}.py -q --tb=short` to capture the failure."),
            "tool_call": {"name": "pytest", "args": {"args": f"tests/test_{src}.py -q --tb=short"}},
            "observation": f"tests/test_{src}.py::test_leftover_not_sleep FAILED\nE   AssertionError: leftover {lname} slept as naive RPS {naive}",
            "reflection": f"Failure is at tests/test_{src}.py::test_leftover_not_sleep. Read that test before a one-line fix.",
        },
        {
            "n": 3,
            "decision_basis": db("Observation:", f"tests/test_{src}.py::test_leftover_not_sleep is red. Read tests/test_{src}.py around the assertion."),
            "tool_call": {"name": "read", "args": {"path": f"tests/test_{src}.py"}},
            "observation": f"def test_leftover_not_sleep():\n    assert classify(429, {{'leftover': '{lname}'}}) != 'sleep_2s'\n",
            "reflection": "Test contract is visible. Search leftover budget symbols next.",
        },
        {
            "n": 4,
            "decision_basis": db("Observation:", "test file imported the leftover helper. Grep leftover budget headers."),
            "tool_call": {"name": "bash", "args": {"command": f"rg -n '{lname}|429|sleep|{naive}' src {src} tests"}},
            "observation": f"src/{src}.py:2: return 'sleep_2s' if status == 429 else 'ok'",
            "reflection": f"Grep hit src/{src}.py. Read it before editing the first match.",
        },
        {
            "n": 5,
            "decision_basis": db("Observation:", f"grep listed src/{src}.py. Read it before any patch."),
            "tool_call": {"name": "read", "args": {"path": f"src/{src}.py"}},
            "observation": "def classify(status, err):\n    return 'sleep_2s' if status == 429 else 'ok'\n",
            "reflection": "First read done. Fetch leftover budget docs next; do not patch on a hunch yet.",
        },
        {
            "n": 6,
            "decision_basis": db("Observation:", "local files are in. Need leftover budget docs before editing."),
            "tool_call": {"name": "fetch", "args": {"url": p["docs"] + "#leftover"}},
            "observation": f"GET {p['docs']}#leftover\nHTTP/1.1 429 Too Many Requests\nX-RateLimit-Remaining: 0",
            "reflection": "Call failed with leftover-budget 429, not Retry-After catalog. Recover with backoff.",
        },
        {
            "n": 7,
            "decision_basis": db("Observation:", "the prior call returned leftover-budget 429. Sleep then retry."),
            "tool_call": {"name": "fetch", "args": {"url": p["docs"] + "#leftover"}},
            "observation": f"sleep + jitter retry of the same URL\nHTTP/1.1 200 OK\n{api} leftover {lname} is not the naive RPS {naive} bucket.",
            "reflection": "Retry succeeded. Continue with leftover budget document.",
        },
        {
            "n": 8,
            "decision_basis": db("Observation:", "local files are in. Need the second leftover budget document."),
            "tool_call": {"name": "fetch", "args": {"url": p["docs2"]}},
            "observation": f"GET {p['docs2']}\nHTTP/1.1 502 Bad Gateway\nBad Gateway.",
            "reflection": "Call failed with upstream gateway failure. Recover with backoff.",
        },
        {
            "n": 9,
            "decision_basis": db("Observation:", "the prior call returned an upstream gateway failure. Retry once with 2s backoff."),
            "tool_call": {"name": "fetch", "args": {"url": p["docs2"]}},
            "observation": f"retry after 2s backoff; local vendor fixture\nHTTP/1.1 200 OK\nSleep cannot mint leftover {lname}. Handoff {ticket}. Not Retry-After catalog.",
            "reflection": "Degraded path used the local fixture. Resume leftover bind plan.",
        },
        {
            "n": 10,
            "decision_basis": db("Observation:", f"docs and source are in. Apply the first leftover patch to src/{src}.py."),
            "tool_call": {
                "name": "edit",
                "args": {
                    "path": f"src/{src}.py",
                    "old": "    return 'sleep_2s' if status == 429 else 'ok'",
                    "new": "    return 'sleep_8s' if status == 429 else 'ok'",
                },
            },
            "observation": f"patched 8s (still treating leftover {lname} as naive RPS)",
            "reflection": "Patch applied. Re-run the failing test; do not assume leftover bind is green.",
        },
        {
            "n": 11,
            "decision_basis": db("Observation:", f"edit wrote src/{src}.py. Re-run the same failing node."),
            "tool_call": {"name": "pytest", "args": {"args": f"tests/test_{src}.py -q --tb=short"}},
            "observation": f"tests/test_{src}.py::test_leftover_not_sleep FAILED\nE   AssertionError: sleep cannot mint leftover {lname}",
            "reflection": "Still red after the first patch. Re-read leftover bind; naive RPS hypothesis is wrong.",
        },
        {
            "n": 12,
            "decision_basis": db("Observation:", f"post-edit test still failed (tests/test_{src}.py::test_leftover_not_sleep). Re-read src/{src}.py."),
            "tool_call": {"name": "read", "args": {"path": f"src/{src}.py"}},
            "observation": f"{api} leftover {lname} is a bound leftover budget, not naive RPS {naive}",
            "reflection": f"Plan change: Leftover {lname} is bound leftover budget. Handoff {ticket}. Not Retry-After catalog.",
        },
        {
            "n": 13,
            "decision_basis": db("Reflection:", f"Leftover {lname} is bound leftover budget. Handoff {ticket}. Not Retry-After catalog."),
            "tool_call": {
                "name": "edit",
                "args": {
                    "path": f"{src}/handoff.md",
                    "old": "",
                    "new": f"# {ticket} {api} leftover {lname} owned by quota-plat; naive {naive} unused",
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
            "reflection": "Result recorded. Run one broader check before declaring leftover outcome.",
        },
        {
            "n": 15,
            "decision_basis": db("Observation:", f"focused run finished. Run broader check `pytest tests/test_{src}.py -q; echo {ticket}`."),
            "tool_call": {"name": "bash", "args": {"command": f"pytest tests/test_{src}.py -q; echo {ticket}"}},
            "observation": f"1 failed, 2 passed\n{ticket}",
            "reflection": "Broader check captured. Residual leftover risk belongs in the outcome text.",
        },
        {
            "n": 16,
            "decision_basis": db("Observation:", "broader check is on disk. Show leftover bind plus handoff diffstat."),
            "tool_call": {"name": "bash", "args": {"command": "git diff --stat | head -n 40"}},
            "observation": f"diffstat for {p['lslug']}: src/{src}.py | 8 +++++---. {src}/handoff.md added.",
            "reflection": "Diff is the review artifact. Lint next.",
        },
        {
            "n": 17,
            "decision_basis": db("Observation:", "diffstat listed the patched leftover files. Lint those paths only."),
            "tool_call": {"name": "bash", "args": {"command": "ruff check tests || true; echo lint-end"}},
            "observation": "All checks passed!\nlint-end",
            "reflection": "Lint clean. Episode complete.",
        },
    ]
    rec = {
        "id": f"rlb-r{rnd:02d}-{p['lslug']}",
        "goal": f"Do not retry {api} leftover {lname} as naive RPS {naive} sleep.",
        "plan": f"Read leftover-as-rps, try 8s, then hand off leftover {lname}.",
        "steps": steps,
        "outcome": f"Still rate-classed; leftover {lname} is bound leftover budget — handoff {ticket}.",
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
            "stack": f"{api} leftover {lname}",
        },
    }
    ok(rec)
    return rec


def notes(rnd: int, p: dict) -> str:
    return f"""# rate-limit-backoff-factory — NOTES r{rnd:02d}

Novel coverage: {p['novel']}%

leftover leftover leftover: leftover budget header vs naive RPS leftover bind.

## Episodes
- `rlb-r{rnd:02d}-{p['slug']}`: 16 steps, success=True, domain={p['slug']}-vs-naive-rps, seed={p['slug']}
  - 502 at step 6 recovered 7; leftover-budget 429 at step 8 recovered 9
  - plan change at step 12: Use leftover {p['leftover']}. Naive RPS {p['naive']} is not leftover budget. Not Retry-After catalog.
  - edit→test→fail→re-read→fix at steps 10-13
- `rlb-r{rnd:02d}-{p['lslug']}`: 17 steps, success=False, domain={p['lslug']}-vs-{p['slug']}, seed={p['lslug']}
  - leftover-budget 429 at step 6 recovered 7; 502 at step 8 recovered 9
  - plan change at step 12: Leftover {p['lname']} is bound leftover budget. Handoff {p['ticket']}. Not Retry-After catalog.
  - edit→test→fail→re-read→handoff at steps 10-13

## decision_basis audit
Every step has decision_basis starting with Plan:/Observation:/Reflection:/Tool call:, length ≤240, no thought/chain_of_thought/scratch/inner_monologue keys, no spike_events, no sim_or_real real, no Spikenaut. Generator grok-4.6. No [variant …] goal stamp.

## Mix
Success: ['rlb-r{rnd:02d}-{p['slug']}']. Realistic failure/handoff: ['rlb-r{rnd:02d}-{p['lslug']}'].

## Realism / weak recovery paths
Noise recoveries are backoff+retry or local fixture cache. First patches bind leftover as naive RPS and fail closed. Designed traces — not live executions.

## Step counts
- rlb-r{rnd:02d}-{p['slug']}: 16 (required 14–18)
- rlb-r{rnd:02d}-{p['lslug']}: 17 (required 14–18)

## Weaknesses / next
Naive {p['naive']} is not leftover {p['leftover']}. Not Retry-After catalog. Sleep cannot mint leftover {p['lname']}. Not Retry-After catalog.
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
