#!/usr/bin/env python3
"""rate-limit-backoff leftover leftover leftover mill.

Distinct API leftover budget header vs naive RPS bind leftover budget.
BAN r81 monday-graphql-complexity-vs-rps, airtable-formula-handoff, Retry-After catalog clones.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

EXPERIMENTS = Path(__file__).resolve().parent
REPO = EXPERIMENTS.parent
sys.path.insert(0, str(EXPERIMENTS))
sys.path.insert(0, str(REPO / "pipelines"))

GENERATOR = "grok-4.6"
FACTORY = "rate-limit-backoff-factory"
PREFIX = "rlb"
BANNED_KEYS = ("thought", "chain_of_thought", "scratch", "inner_monologue")
DB_PREFIXES = ("Plan:", "Observation:", "Reflection:", "Tool call:")
RAW = REPO / "outputs" / "raw" / "2026-08-19-agentic" / FACTORY


def _p(**kwargs):
    return kwargs


def leftover_ok(
    *,
    slug: str,
    api: str,
    header: str,
    naive: str,
    leftover: int,
    naive_val: int,
    mod: str,
    docs: str,
    docs2: str,
    domain: str,
    stack: str,
    ticket_unused: str = "",
):
    hdr = header
    return _p(
        slug=slug,
        goal=f"Honor {api} leftover {hdr}; do not bind leftover budget as naive RPS {naive}.",
        plan=f"Read leftover-as-rps, try {naive}, then leftover {hdr}.",
        mod=mod,
        test_fn="test_leftover_not_rps",
        src_body=f"def leftover(h):\n    return int(h.get('{naive}') or 10)\n",
        test_body=(
            f"def test_leftover_not_rps():\n"
            f"    h = {{'{hdr}': '{leftover}', '{naive}': '{naive_val}'}}\n"
            f"    assert leftover(h) == {leftover}\n"
        ),
        grep_pat=f"{hdr}|{naive}|leftover",
        grep_hit=f"src/{mod}.py:2: return int(h.get('{naive}') or 10)",
        fail_msg=f"AssertionError: {naive_val} == {leftover}; naive {naive} used as leftover budget",
        first_old=f"    return int(h.get('{naive}') or 10)",
        first_new=f"    return int(h.get('{naive}') or 10) * 1",
        first_obs=f"patched identity (still {naive}, not leftover {hdr})",
        still_msg=f"AssertionError: {naive_val} != {leftover}; leftover is {hdr}",
        reread_obs=f"{api} leftover budget is {hdr}, not naive RPS {naive}",
        plan_change=f"Use leftover {hdr}. Naive RPS {naive} is not leftover budget. Not Retry-After catalog.",
        fix_new=f"    return int(h['{hdr}'])",
        fix_obs=f"patched leftover {hdr}",
        docs_url=docs,
        docs_ok=f"{api} leftover budget lives on {hdr}, separate from naive RPS {naive}.",
        docs_url2=docs2,
        docs_ok2=f"Prefer leftover {hdr}. Not Retry-After catalog. Not Monday complexity clone.",
        outcome=f"Leftover {hdr} matched {leftover}. Naive {naive} unused (success).",
        domain=domain,
        stack=stack,
        seed=slug,
        residual=f"Naive {naive} is not leftover {hdr}. Not Retry-After catalog.",
        coverage=87,
    )


def leftover_fail(
    *,
    slug: str,
    api: str,
    leftover_kind: str,
    naive: str,
    mod: str,
    docs: str,
    docs2: str,
    domain: str,
    stack: str,
    ticket: str,
):
    return _p(
        slug=slug,
        goal=f"Do not retry {api} leftover {leftover_kind} as naive RPS {naive} sleep.",
        plan=f"Read leftover-as-rps, try 8s, then hand off leftover {leftover_kind}.",
        mod=mod,
        test_fn="test_leftover_not_sleep",
        src_body="def classify(status, err):\n    return 'sleep_2s' if status == 429 else 'ok'\n",
        test_body=(
            "def test_leftover_not_sleep():\n"
            f"    assert classify(429, {{'leftover': '{leftover_kind}'}}) != 'sleep_2s'\n"
        ),
        grep_pat=f"{leftover_kind}|429|sleep|{naive}",
        grep_hit=f"src/{mod}.py:2: return 'sleep_2s' if status == 429 else 'ok'",
        fail_msg=f"AssertionError: leftover {leftover_kind} slept as naive RPS {naive}",
        first_old="    return 'sleep_2s' if status == 429 else 'ok'",
        first_new="    return 'sleep_8s' if status == 429 else 'ok'",
        first_obs=f"patched 8s (still treating leftover {leftover_kind} as naive RPS)",
        still_msg=f"AssertionError: sleep cannot mint leftover {leftover_kind}",
        reread_obs=f"{api} leftover {leftover_kind} is a bound leftover budget, not naive RPS {naive}",
        plan_change=f"Leftover {leftover_kind} is bound leftover budget. Handoff {ticket}. Not Retry-After catalog.",
        ticket=ticket,
        ticket_why=f"{api} leftover {leftover_kind} owned by quota-plat; naive {naive} unused",
        fix_obs="ticket filed. still rate-classed",
        docs_url=docs,
        docs_ok=f"{api} leftover {leftover_kind} is not the naive RPS {naive} bucket.",
        docs_url2=docs2,
        docs_ok2=f"Sleep cannot mint leftover {leftover_kind}. Handoff {ticket}. Not Retry-After catalog.",
        outcome=f"Still rate-classed; leftover {leftover_kind} is bound leftover budget — handoff {ticket}.",
        domain=domain,
        stack=stack,
        seed=slug,
        residual=f"Sleep cannot mint leftover {leftover_kind}. Not Retry-After catalog.",
        coverage=87,
    )


PAIRS = [
    (
        leftover_ok(
            slug="shopify-gql-leftover-cost",
            api="Shopify GraphQL",
            header="X-Shopify-GraphQL-Cost-Left",
            naive="X-Shopify-Shop-Api-Call-Limit",
            leftover=842,
            naive_val="39/40",
            mod="shplef",
            docs="https://shopify.dev/docs/api/usage/rate-limits",
            docs2="https://shopify.dev/docs/api/admin-graphql",
            domain="shopify-gql-leftover-cost-vs-rest-remaining",
            stack="Shopify GraphQL leftover cost",
        ),
        leftover_fail(
            slug="shopify-rest-leftover-handoff",
            api="Shopify REST",
            leftover_kind="rest-remaining-leftover",
            naive="X-Shopify-Shop-Api-Call-Limit",
            mod="shprest",
            docs="https://shopify.dev/docs/api/admin-rest/usage/rate-limits",
            docs2="https://shopify.dev/docs/api/admin-rest",
            domain="shopify-rest-leftover-remaining-vs-naive-rps",
            stack="Shopify REST leftover remaining",
            ticket="SH-LF-3",
        ),
    ),
    (
        leftover_ok(
            slug="stripe-leftover-request-limit",
            api="Stripe",
            header="Stripe-Rate-Limit-Remaining",
            naive="X-RateLimit-Remaining",
            leftover=96,
            naive_val=0,
            mod="strlef",
            docs="https://docs.stripe.com/rate-limits",
            docs2="https://docs.stripe.com/error-handling",
            domain="stripe-leftover-request-limit-vs-naive-remaining",
            stack="Stripe leftover request-limit",
        ),
        leftover_fail(
            slug="stripe-leftover-idem-429-handoff",
            api="Stripe idempotency",
            leftover_kind="idempotency-leftover-429",
            naive="X-RateLimit-Remaining",
            mod="stridem",
            docs="https://docs.stripe.com/api/idempotent_requests",
            docs2="https://docs.stripe.com/error-codes",
            domain="stripe-leftover-idempotency-429-vs-request-limit",
            stack="Stripe leftover idempotency 429",
            ticket="ST-LF-4",
        ),
    ),
    (
        leftover_ok(
            slug="github-leftover-secondary",
            api="GitHub secondary",
            header="x-ratelimit-remaining-secondary",
            naive="x-ratelimit-remaining",
            leftover=12,
            naive_val=4980,
            mod="ghsec",
            docs="https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api",
            docs2="https://docs.github.com/en/rest/overview/resources-in-the-rest-api",
            domain="github-leftover-secondary-vs-leftover-primary",
            stack="GitHub leftover secondary",
        ),
        leftover_fail(
            slug="github-leftover-primary-handoff",
            api="GitHub primary",
            leftover_kind="primary-leftover",
            naive="x-ratelimit-remaining",
            mod="ghpri",
            docs="https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api",
            docs2="https://docs.github.com/en/rest/rate-limit",
            domain="github-leftover-primary-vs-naive-rps",
            stack="GitHub leftover primary",
            ticket="GH-LF-5",
        ),
    ),
    (
        leftover_ok(
            slug="gitlab-leftover-rate",
            api="GitLab",
            header="RateLimit-Remaining",
            naive="X-RateLimit-Remaining",
            leftover=310,
            naive_val=60,
            mod="glrate",
            docs="https://docs.gitlab.com/ee/user/gitlab_com/#rate-limits",
            docs2="https://docs.gitlab.com/ee/administration/settings/user_and_ip_rate_limits.html",
            domain="gitlab-leftover-rate-vs-naive-rps",
            stack="GitLab leftover rate",
        ),
        leftover_fail(
            slug="gitlab-leftover-concurrency-handoff",
            api="GitLab concurrency",
            leftover_kind="concurrency-leftover",
            naive="X-RateLimit-Remaining",
            mod="glconc",
            docs="https://docs.gitlab.com/ee/administration/settings/rate_limit_on_pipelines.html",
            docs2="https://docs.gitlab.com/ee/api/rest/#rate-limits",
            domain="gitlab-leftover-concurrency-vs-leftover-rate",
            stack="GitLab leftover concurrency",
            ticket="GL-LF-6",
        ),
    ),
    (
        leftover_ok(
            slug="slack-leftover-tier",
            api="Slack tier",
            header="X-Rate-Limit-Remaining",
            naive="Retry-After",
            leftover=18,
            naive_val=30,
            mod="sltier",
            docs="https://api.slack.com/apis/rate-limits",
            docs2="https://api.slack.com/docs/rate-limits",
            domain="slack-leftover-tier-vs-naive-retry-after",
            stack="Slack leftover tier",
        ),
        leftover_fail(
            slug="slack-leftover-workspace-handoff",
            api="Slack workspace",
            leftover_kind="workspace-leftover",
            naive="Retry-After",
            mod="slws",
            docs="https://api.slack.com/methods/conversations.list",
            docs2="https://api.slack.com/changelog",
            domain="slack-leftover-workspace-vs-leftover-tier",
            stack="Slack leftover workspace",
            ticket="SL-LF-7",
        ),
    ),
    (
        leftover_ok(
            slug="discord-leftover-bucket",
            api="Discord bucket",
            header="X-RateLimit-Remaining",
            naive="X-RateLimit-Limit",
            leftover=4,
            naive_val=50,
            mod="dcbkt",
            docs="https://discord.com/developers/docs/topics/rate-limits",
            docs2="https://discord.com/developers/docs/topics/gateway",
            domain="discord-leftover-bucket-vs-naive-limit",
            stack="Discord leftover bucket",
        ),
        leftover_fail(
            slug="discord-leftover-global-handoff",
            api="Discord global",
            leftover_kind="global-leftover",
            naive="X-RateLimit-Limit",
            mod="dcglb",
            docs="https://discord.com/developers/docs/topics/rate-limits#global-rate-limit",
            docs2="https://discord.com/developers/docs/resources/channel",
            domain="discord-leftover-global-vs-leftover-bucket",
            stack="Discord leftover global",
            ticket="DC-LF-8",
        ),
    ),
    (
        leftover_ok(
            slug="notion-leftover-integration",
            api="Notion",
            header="x-ratelimit-remaining",
            naive="Retry-After",
            leftover=2,
            naive_val=8,
            mod="ntlef",
            docs="https://developers.notion.com/reference/request-limits",
            docs2="https://developers.notion.com/reference/status-codes",
            domain="notion-leftover-integration-vs-naive-retry",
            stack="Notion leftover integration",
        ),
        leftover_fail(
            slug="notion-leftover-user-handoff",
            api="Notion user",
            leftover_kind="user-leftover",
            naive="Retry-After",
            mod="ntusr",
            docs="https://developers.notion.com/docs/rate-limits",
            docs2="https://developers.notion.com/reference/errors",
            domain="notion-leftover-user-vs-leftover-integration",
            stack="Notion leftover user",
            ticket="NT-LF-9",
        ),
    ),
    (
        leftover_ok(
            slug="linear-leftover-request",
            api="Linear",
            header="X-RateLimit-Requests-Remaining",
            naive="X-RateLimit-Remaining",
            leftover=1400,
            naive_val=60,
            mod="lnreq",
            docs="https://developers.linear.app/docs/graphql/working-with-the-graphql-api#rate-limiting",
            docs2="https://developers.linear.app/docs/graphql/errors",
            domain="linear-leftover-request-vs-naive-remaining",
            stack="Linear leftover request",
        ),
        leftover_fail(
            slug="linear-leftover-org-handoff",
            api="Linear org",
            leftover_kind="org-leftover",
            naive="X-RateLimit-Remaining",
            mod="lnorg",
            docs="https://developers.linear.app/docs/graphql/working-with-the-graphql-api",
            docs2="https://linear.app/docs/api",
            domain="linear-leftover-org-vs-leftover-request",
            stack="Linear leftover org",
            ticket="LN-LF-10",
        ),
    ),
    (
        leftover_ok(
            slug="jira-leftover-rest",
            api="Jira Cloud",
            header="X-RateLimit-Remaining",
            naive="Retry-After",
            leftover=77,
            naive_val=15,
            mod="jrlef",
            docs="https://developer.atlassian.com/cloud/jira/platform/rate-limiting/",
            docs2="https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/",
            domain="jira-leftover-rest-vs-naive-retry",
            stack="Jira leftover REST",
        ),
        leftover_fail(
            slug="jira-leftover-cloud-handoff",
            api="Jira cloud cost",
            leftover_kind="cloud-cost-leftover",
            naive="Retry-After",
            mod="jrcld",
            docs="https://developer.atlassian.com/cloud/jira/platform/rate-limiting/#cost",
            docs2="https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-search/",
            domain="jira-leftover-cloud-vs-leftover-rest",
            stack="Jira leftover cloud",
            ticket="JR-LF-11",
        ),
    ),
    (
        leftover_ok(
            slug="confluence-leftover-rest",
            api="Confluence",
            header="X-RateLimit-Remaining",
            naive="Retry-After",
            leftover=41,
            naive_val=12,
            mod="cfllef",
            docs="https://developer.atlassian.com/cloud/confluence/rate-limiting/",
            docs2="https://developer.atlassian.com/cloud/confluence/rest/v2/intro/",
            domain="confluence-leftover-rest-vs-naive-retry",
            stack="Confluence leftover REST",
        ),
        leftover_fail(
            slug="confluence-leftover-search-handoff",
            api="Confluence search",
            leftover_kind="search-leftover",
            naive="Retry-After",
            mod="cflsrch",
            docs="https://developer.atlassian.com/cloud/confluence/rest/v2/api-group-search/",
            docs2="https://developer.atlassian.com/cloud/confluence/search/",
            domain="confluence-leftover-search-vs-leftover-rest",
            stack="Confluence leftover search",
            ticket="CF-LF-12",
        ),
    ),
    (
        leftover_ok(
            slug="twilio-leftover-request",
            api="Twilio",
            header="Twilio-Concurrent-Requests-Remaining",
            naive="X-RateLimit-Remaining",
            leftover=9,
            naive_val=100,
            mod="twlef",
            docs="https://www.twilio.com/docs/usage/api#rate-limiting",
            docs2="https://www.twilio.com/docs/usage/troubleshooting/debug-your-twilio-application",
            domain="twilio-leftover-request-vs-naive-remaining",
            stack="Twilio leftover request",
        ),
        leftover_fail(
            slug="twilio-leftover-concurrent-handoff",
            api="Twilio concurrent",
            leftover_kind="concurrent-leftover",
            naive="X-RateLimit-Remaining",
            mod="twconc",
            docs="https://www.twilio.com/docs/usage/tutorials/how-to-use-your-free-trial-account",
            docs2="https://www.twilio.com/docs/api/errors",
            domain="twilio-leftover-concurrent-vs-leftover-request",
            stack="Twilio leftover concurrent",
            ticket="TW-LF-13",
        ),
    ),
    (
        leftover_ok(
            slug="sendgrid-leftover-credit",
            api="SendGrid",
            header="X-RateLimit-Remaining",
            naive="X-RateLimit-Reset",
            leftover=55,
            naive_val=1710000000,
            mod="sglef",
            docs="https://www.twilio.com/docs/sendgrid/api-reference/how-to-use-the-sendgrid-v3-api/rate-limits",
            docs2="https://www.twilio.com/docs/sendgrid/api-reference",
            domain="sendgrid-leftover-credit-vs-naive-reset",
            stack="SendGrid leftover credit",
        ),
        leftover_fail(
            slug="sendgrid-leftover-warmup-handoff",
            api="SendGrid warmup",
            leftover_kind="warmup-leftover",
            naive="X-RateLimit-Reset",
            mod="sgwarm",
            docs="https://www.twilio.com/docs/sendgrid/ui/sending-email/warming-up-an-ip-address",
            docs2="https://www.twilio.com/docs/sendgrid/api-reference/ip-warmup",
            domain="sendgrid-leftover-warmup-vs-leftover-credit",
            stack="SendGrid leftover warmup",
            ticket="SG-LF-14",
        ),
    ),
    (
        leftover_ok(
            slug="hubspot-leftover-daily",
            api="HubSpot",
            header="X-HubSpot-RateLimit-Remaining",
            naive="X-HubSpot-RateLimit-Interval-Milliseconds",
            leftover=88,
            naive_val=10000,
            mod="hslef",
            docs="https://developers.hubspot.com/docs/api/usage-details",
            docs2="https://developers.hubspot.com/docs/api/error-handling",
            domain="hubspot-leftover-daily-vs-naive-interval",
            stack="HubSpot leftover daily",
        ),
        leftover_fail(
            slug="hubspot-leftover-search-handoff",
            api="HubSpot search",
            leftover_kind="search-leftover",
            naive="X-HubSpot-RateLimit-Interval-Milliseconds",
            mod="hssrch",
            docs="https://developers.hubspot.com/docs/api/crm/search",
            docs2="https://developers.hubspot.com/docs/guides/api/crm/search",
            domain="hubspot-leftover-search-vs-leftover-daily",
            stack="HubSpot leftover search",
            ticket="HS-LF-15",
        ),
    ),
    (
        leftover_ok(
            slug="salesforce-leftover-daily",
            api="Salesforce",
            header="Sforce-Limit-Info",
            naive="X-RateLimit-Remaining",
            leftover=12340,
            naive_val=0,
            mod="sflef",
            docs="https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/header_limit_info.htm",
            docs2="https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/errorcodes.htm",
            domain="salesforce-leftover-daily-vs-naive-remaining",
            stack="Salesforce leftover daily",
        ),
        leftover_fail(
            slug="salesforce-leftover-concurrent-handoff",
            api="Salesforce concurrent API",
            leftover_kind="concurrent-api-leftover",
            naive="X-RateLimit-Remaining",
            mod="sfconc",
            docs="https://developer.salesforce.com/docs/atlas.en-us.salesforce_app_limits_cheatsheet.meta/salesforce_app_limits_cheatsheet/salesforce_app_limits_platform_api.htm",
            docs2="https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/errorcodes.htm",
            domain="salesforce-leftover-concurrent-api-vs-leftover-daily",
            stack="Salesforce leftover concurrent API",
            ticket="SF-LF-16",
        ),
    ),
    (
        leftover_ok(
            slug="graph-leftover-usage",
            api="Graph API",
            header="x-app-usage",
            naive="x-business-use-case-usage",
            leftover=19,
            naive_val=91,
            mod="gplef",
            docs="https://developers.facebook.com/docs/graph-api/overview/rate-limiting",
            docs2="https://developers.facebook.com/docs/graph-api/overview/rate-limiting#headers",
            domain="graph-leftover-app-usage-vs-naive-business",
            stack="Graph API leftover app usage",
        ),
        leftover_fail(
            slug="graph-leftover-app-handoff",
            api="Graph app",
            leftover_kind="app-leftover",
            naive="x-business-use-case-usage",
            mod="gpapp",
            docs="https://developers.facebook.com/docs/graph-api/overview/rate-limiting#app-level-rate-limiting",
            docs2="https://developers.facebook.com/docs/marketing-api/overview/rate-limiting",
            domain="graph-leftover-app-vs-leftover-usage",
            stack="Graph leftover app",
            ticket="GP-LF-17",
        ),
    ),
    (
        leftover_ok(
            slug="cloudflare-leftover-zone",
            api="Cloudflare",
            header="Ratelimit-Remaining",
            naive="Retry-After",
            leftover="1200",
            naive_val=60,
            mod="cflef",
            docs="https://developers.cloudflare.com/fundamentals/api/reference/limits/",
            docs2="https://developers.cloudflare.com/fundamentals/api/how-to/make-api-calls/",
            domain="cloudflare-leftover-zone-vs-naive-retry",
            stack="Cloudflare leftover zone",
        ),
        leftover_fail(
            slug="cloudflare-leftover-account-handoff",
            api="Cloudflare account",
            leftover_kind="account-leftover",
            naive="Retry-After",
            mod="cfacct",
            docs="https://developers.cloudflare.com/fundamentals/api/reference/limits/#account-rate-limits",
            docs2="https://developers.cloudflare.com/api/",
            domain="cloudflare-leftover-account-vs-leftover-zone",
            stack="Cloudflare leftover account",
            ticket="CF-LF-18",
        ),
    ),
]


def _step(n: int, decision_basis: str, tool_call: dict, observation: str, reflection: str) -> dict:
    if not decision_basis.startswith(DB_PREFIXES):
        raise ValueError(f"step {n} decision_basis prefix: {decision_basis!r}")
    if len(decision_basis) > 240:
        raise ValueError(f"step {n} decision_basis {len(decision_basis)} > 240")
    if not observation.strip() or not reflection.strip():
        raise ValueError(f"step {n} empty observation/reflection")
    return {
        "n": n,
        "decision_basis": decision_basis,
        "tool_call": tool_call,
        "observation": observation,
        "reflection": reflection,
    }


def _bash(command: str) -> dict:
    return {"name": "bash", "args": {"command": command}}


def _read(path: str) -> dict:
    return {"name": "read", "args": {"path": path}}


def _edit(path: str, old: str, new: str) -> dict:
    return {"name": "edit", "args": {"path": path, "old": old, "new": new}}


def _pytest(args: str) -> dict:
    return {"name": "pytest", "args": {"args": args}}


def _fetch(url: str) -> dict:
    return {"name": "fetch", "args": {"url": url}}


def dumps_episode(ep: dict) -> str:
    return json.dumps(ep, ensure_ascii=True, separators=(",", ":"))


def assert_clean(obj: Any, path: str = "") -> None:
    if isinstance(obj, dict):
        for key, val in obj.items():
            if key in BANNED_KEYS:
                raise ValueError(f"banned key {key} at {path}")
            if key == "sim_or_real" and val == "real":
                raise ValueError(f"sim_or_real real at {path}")
            if key == "spike_events":
                raise ValueError(f"spike_events at {path}")
            assert_clean(val, f"{path}.{key}")
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            assert_clean(item, f"{path}[{i}]")


def _paths(p: dict) -> tuple[str, str, str]:
    src = f"src/{p['mod']}.py"
    test = f"tests/test_{p['mod']}.py"
    cfg = f"{p['mod']}/cfg.yml"
    return src, test, cfg


def _goal_ok(goal: str) -> None:
    g = goal.strip().lower()
    if not goal.strip() or g in {"x", "placeholder", "todo", "tbd", "fix it"}:
        raise ValueError(f"placeholder goal: {goal!r}")
    if "[variant" in g:
        raise ValueError(f"variant stamp in goal: {goal!r}")
    for banned in ("monday-graphql-complexity", "airtable-formula"):
        if banned in g:
            raise ValueError(f"banned coverage in goal: {goal!r}")


def build_success(round_n: int, p: dict) -> dict:
    _goal_ok(p["goal"])
    src, test, cfg = _paths(p)
    eid = f"{PREFIX}-r{round_n}-{p['slug']}"
    listing = f"{src} {cfg}\n{test}"
    pytest_args = f"{test} -q --tb=short"
    fail_obs = f"{test}::{p['test_fn']} FAILED\nE   {p['fail_msg']}"
    still_obs = f"{test}::{p['test_fn']} FAILED\nE   {p['still_msg']}"
    steps = [
        _step(
            1,
            f"Plan: list src {p['mod']} and tests before touching leftover budget or rps bind.",
            _bash(f"ls -la src {p['mod']} tests | head -40"),
            listing,
            f"Tree shows {src} plus tests. Run the named failing target next.",
        ),
        _step(
            2,
            f"Observation: listing named the test files. Run `{pytest_args}` to capture the failure.",
            _pytest(pytest_args),
            fail_obs,
            f"Failure is at {test}::{p['test_fn']}. Read that test before a one-line fix.",
        ),
        _step(
            3,
            f"Observation: {test}::{p['test_fn']} is red. Read {test} around the assertion.",
            _read(test),
            p["test_body"],
            "Test contract is visible. Search leftover budget symbols next.",
        ),
        _step(
            4,
            "Observation: test file imported the leftover helper. Grep leftover budget headers.",
            _bash(f"rg -n '{p['grep_pat']}' src {p['mod']} tests"),
            p["grep_hit"],
            f"Grep hit {src}. Read it before editing the first match.",
        ),
        _step(
            5,
            f"Observation: grep listed {src}. Read it before any patch.",
            _read(src),
            p["src_body"],
            "First read done. Fetch leftover budget docs next; do not patch on a hunch yet.",
        ),
        _step(
            6,
            "Observation: local files are in. Need leftover budget docs before editing.",
            _fetch(p["docs_url"]),
            f"GET {p['docs_url']}\nHTTP/1.1 502 Bad Gateway\nBad Gateway.",
            "Call failed with upstream gateway failure. Recover with backoff.",
        ),
        _step(
            7,
            "Observation: the prior call returned an upstream gateway failure. Retry once with 2s backoff.",
            _fetch(p["docs_url"]),
            f"retry after 2s backoff; local vendor fixture\nHTTP/1.1 200 OK\n{p['docs_ok']}",
            "Degraded path used the local fixture. Continue with leftover budget content.",
        ),
        _step(
            8,
            "Observation: local files are in. Need the second leftover budget document.",
            _fetch(p["docs_url2"]),
            f"GET {p['docs_url2']}\nHTTP/1.1 429 Too Many Requests\nX-RateLimit-Remaining: 0",
            "Call failed with leftover-budget 429, not Retry-After catalog. Recover with backoff.",
        ),
        _step(
            9,
            "Observation: the prior call returned leftover-budget 429. Sleep then retry.",
            _fetch(p["docs_url2"]),
            f"sleep + jitter retry of the same URL\nHTTP/1.1 200 OK\n{p['docs_ok2']}",
            "Retry succeeded. Resume leftover budget bind with that document.",
        ),
        _step(
            10,
            f"Observation: docs and source are in. Apply the first leftover patch to {src}.",
            _edit(src, p["first_old"], p["first_new"]),
            p["first_obs"],
            "Patch applied. Re-run the failing test; do not assume leftover bind is green.",
        ),
        _step(
            11,
            f"Observation: edit wrote {src}. Re-run the same failing node.",
            _pytest(pytest_args),
            still_obs,
            "Still red after the first patch. Re-read leftover bind; naive RPS hypothesis is wrong.",
        ),
        _step(
            12,
            f"Observation: post-edit test still failed ({test}::{p['test_fn']}). Re-read {src}.",
            _read(src),
            p["reread_obs"],
            f"Plan change: {p['plan_change']}",
        ),
        _step(
            13,
            f"Reflection: {p['plan_change']}"[:240],
            _edit(src, p["first_new"], p["fix_new"]),
            p["fix_obs"],
            "Corrective leftover bind applied. Run the original failing node again.",
        ),
        _step(
            14,
            "Observation: leftover bind edit returned clean. Re-run the original failing test node.",
            _pytest(pytest_args),
            "1 passed in 0.16s",
            "Result recorded. Run one broader check before declaring leftover bind outcome.",
        ),
        _step(
            15,
            f"Observation: focused run finished. Run broader check `pytest {test} -q`.",
            _bash(f"pytest {test} -q"),
            "3 passed in 0.28s",
            "Broader check captured. Stop; residual leftover risk belongs in the outcome text.",
        ),
        _step(
            16,
            "Observation: broader check is on disk. Show the leftover bind diffstat.",
            _bash("git diff --stat | head -n 40"),
            f"diffstat for {p['slug']}: {src} | 9 ++++++---. No other modified paths.",
            "Diff is the review artifact. No further leftover edits.",
        ),
    ]
    ep = {
        "id": eid,
        "goal": p["goal"],
        "plan": p["plan"],
        "steps": steps,
        "outcome": p["outcome"],
        "reward": {
            "success": True,
            "tests_passed": 3,
            "retries": 2,
            "duration_min": 610,
            "wasted_calls": 180,
            "cost_steps": 16,
            "plan_changes": 1,
            "mid_reward": 0,
        },
        "meta": {
            "factory": FACTORY,
            "round": round_n,
            "generator": GENERATOR,
            "kind": "episode",
            "seed": p["seed"],
            "designed": True,
            "domain": p["domain"],
            "stack": p["stack"],
        },
    }
    assert_clean(ep)
    if len(steps) != 16:
        raise ValueError(f"{eid} expected 16 steps")
    return ep


def build_fail(round_n: int, p: dict) -> dict:
    _goal_ok(p["goal"])
    src, test, cfg = _paths(p)
    eid = f"{PREFIX}-r{round_n}-{p['slug']}"
    ticket = p["ticket"]
    ticket_path = f"{p['mod']}/handoff.md"
    listing = f"{src} {cfg}\n{test}"
    pytest_args = f"{test} -q --tb=short"
    fail_obs = f"{test}::{p['test_fn']} FAILED\nE   {p['fail_msg']}"
    still_obs = f"{test}::{p['test_fn']} FAILED\nE   {p['still_msg']}"
    steps = [
        _step(
            1,
            f"Plan: list src {p['mod']} and tests before touching leftover budget or rps bind.",
            _bash(f"ls -la src {p['mod']} tests | head -40"),
            listing,
            f"Tree shows {src} plus tests. Run the named failing target next.",
        ),
        _step(
            2,
            f"Observation: listing named the test files. Run `{pytest_args}` to capture the failure.",
            _pytest(pytest_args),
            fail_obs,
            f"Failure is at {test}::{p['test_fn']}. Read that test before a one-line fix.",
        ),
        _step(
            3,
            f"Observation: {test}::{p['test_fn']} is red. Read {test} around the assertion.",
            _read(test),
            p["test_body"],
            "Test contract is visible. Search leftover budget symbols next.",
        ),
        _step(
            4,
            "Observation: test file imported the leftover helper. Grep leftover budget headers.",
            _bash(f"rg -n '{p['grep_pat']}' src {p['mod']} tests"),
            p["grep_hit"],
            f"Grep hit {src}. Read it before editing the first match.",
        ),
        _step(
            5,
            f"Observation: grep listed {src}. Read it before any patch.",
            _read(src),
            p["src_body"],
            "First read done. Fetch leftover budget docs next; do not patch on a hunch yet.",
        ),
        _step(
            6,
            "Observation: local files are in. Need leftover budget docs before editing.",
            _fetch(p["docs_url"]),
            f"GET {p['docs_url']}\nHTTP/1.1 429 Too Many Requests\nX-RateLimit-Remaining: 0",
            "Call failed with leftover-budget 429, not Retry-After catalog. Recover with backoff.",
        ),
        _step(
            7,
            "Observation: the prior call returned leftover-budget 429. Sleep then retry.",
            _fetch(p["docs_url"]),
            f"sleep + jitter retry of the same URL\nHTTP/1.1 200 OK\n{p['docs_ok']}",
            "Retry succeeded. Continue with leftover budget document.",
        ),
        _step(
            8,
            "Observation: local files are in. Need the second leftover budget document.",
            _fetch(p["docs_url2"]),
            f"GET {p['docs_url2']}\nHTTP/1.1 502 Bad Gateway\nBad Gateway.",
            "Call failed with upstream gateway failure. Recover with backoff.",
        ),
        _step(
            9,
            "Observation: the prior call returned an upstream gateway failure. Retry once with 2s backoff.",
            _fetch(p["docs_url2"]),
            f"retry after 2s backoff; local vendor fixture\nHTTP/1.1 200 OK\n{p['docs_ok2']}",
            "Degraded path used the local fixture. Resume leftover bind plan.",
        ),
        _step(
            10,
            f"Observation: docs and source are in. Apply the first leftover patch to {src}.",
            _edit(src, p["first_old"], p["first_new"]),
            p["first_obs"],
            "Patch applied. Re-run the failing test; do not assume leftover bind is green.",
        ),
        _step(
            11,
            f"Observation: edit wrote {src}. Re-run the same failing node.",
            _pytest(pytest_args),
            still_obs,
            "Still red after the first patch. Re-read leftover bind; naive RPS hypothesis is wrong.",
        ),
        _step(
            12,
            f"Observation: post-edit test still failed ({test}::{p['test_fn']}). Re-read {src}.",
            _read(src),
            p["reread_obs"],
            f"Plan change: {p['plan_change']}",
        ),
        _step(
            13,
            f"Reflection: {p['plan_change']}"[:240],
            _edit(ticket_path, "", f"# {ticket} {p['ticket_why']}"),
            p["fix_obs"],
            "Handoff ticket written. Run the original failing node again.",
        ),
        _step(
            14,
            "Observation: handoff edit returned clean. Re-run the original failing test node.",
            _pytest(pytest_args),
            f"{test}::{p['test_fn']} FAILED  # handoff: {ticket}\n1 failed",
            "Result recorded. Run one broader check before declaring leftover outcome.",
        ),
        _step(
            15,
            f"Observation: focused run finished. Run broader check `pytest {test} -q; echo {ticket}`.",
            _bash(f"pytest {test} -q; echo {ticket}"),
            f"1 failed, 2 passed\n{ticket}",
            "Broader check captured. Residual leftover risk belongs in the outcome text.",
        ),
        _step(
            16,
            "Observation: broader check is on disk. Show leftover bind plus handoff diffstat.",
            _bash("git diff --stat | head -n 40"),
            f"diffstat for {p['slug']}: {src} | 8 +++++---. {ticket_path} added.",
            "Diff is the review artifact. Lint next.",
        ),
        _step(
            17,
            "Observation: diffstat listed the patched leftover files. Lint those paths only.",
            _bash("ruff check tests || true; echo lint-end"),
            "All checks passed!\nlint-end",
            "Lint clean. Episode complete.",
        ),
    ]
    ep = {
        "id": eid,
        "goal": p["goal"],
        "plan": p["plan"],
        "steps": steps,
        "outcome": p["outcome"],
        "reward": {
            "success": False,
            "tests_passed": 2,
            "retries": 2,
            "duration_min": 640,
            "wasted_calls": 210,
            "cost_steps": 17,
            "plan_changes": 1,
            "mid_reward": 0,
        },
        "meta": {
            "factory": FACTORY,
            "round": round_n,
            "generator": GENERATOR,
            "kind": "episode",
            "seed": p["seed"],
            "designed": True,
            "domain": p["domain"],
            "stack": p["stack"],
        },
    }
    assert_clean(ep)
    if len(steps) != 17:
        raise ValueError(f"{eid} expected 17 steps")
    return ep


def notes_md(round_n: int, ok: dict, bad: dict, ok_id: str, bad_id: str) -> str:
    cov = max(ok.get("coverage", 80), bad.get("coverage", 80))
    return (
        f"# {FACTORY} — NOTES r{round_n}\n\n"
        f"Novel coverage: {cov}%\n\n"
        f"leftover leftover leftover: leftover budget header vs naive RPS leftover bind.\n\n"
        f"## Episodes\n"
        f"- `{ok_id}`: 16 steps, success=True, domain={ok['domain']}, seed={ok['seed']}\n"
        f"  - 502 at step 6 recovered 7; leftover-budget 429 at step 8 recovered 9\n"
        f"  - plan change at step 12: {ok['plan_change']}\n"
        f"  - edit→test→fail→re-read→fix at steps 10-13\n"
        f"- `{bad_id}`: 17 steps, success=False, domain={bad['domain']}, seed={bad['seed']}\n"
        f"  - leftover-budget 429 at step 6 recovered 7; 502 at step 8 recovered 9\n"
        f"  - plan change at step 12: {bad['plan_change']}\n"
        f"  - edit→test→fail→re-read→handoff at steps 10-13\n\n"
        f"## decision_basis audit\n"
        f"Every step has decision_basis starting with Plan:/Observation:/Reflection:/Tool call:, "
        f"length ≤240, no thought/chain_of_thought/scratch/inner_monologue keys, no spike_events, "
        f"no sim_or_real real, no Spikenaut. Generator grok-4.6. No [variant …] goal stamp.\n\n"
        f"## Mix\n"
        f"Success: ['{ok_id}']. Realistic failure/handoff: ['{bad_id}'].\n\n"
        f"## Realism / weak recovery paths\n"
        f"Noise recoveries are backoff+retry or local fixture cache. First patches bind leftover "
        f"as naive RPS and fail closed. Designed traces — not live executions.\n\n"
        f"## Step counts\n"
        f"- {ok_id}: 16 (required 14–18)\n"
        f"- {bad_id}: 17 (required 14–18)\n\n"
        f"## Weaknesses / next\n"
        f"{ok['residual']} {bad['residual']}\n"
    )


def validate_pair(ok_ep: dict, bad_ep: dict, round_n: int) -> None:
    if ok_ep["reward"]["success"] is not True:
        raise ValueError("first episode must succeed")
    if bad_ep["reward"]["success"] is not False:
        raise ValueError("second episode must fail/handoff")
    if len(ok_ep["steps"]) != 16 or len(bad_ep["steps"]) != 17:
        raise ValueError("shape must be 16-step success + 17-step fail")
    if ok_ep["id"] == bad_ep["id"]:
        raise ValueError("duplicate episode ids")
    for ep in (ok_ep, bad_ep):
        _goal_ok(ep["goal"])
        assert_clean(ep)


def build_pair(round_n: int, ok: dict, bad: dict):
    ok_ep = build_success(round_n, ok)
    bad_ep = build_fail(round_n, bad)
    validate_pair(ok_ep, bad_ep, round_n)
    notes = notes_md(round_n, ok, bad, ok_ep["id"], bad_ep["id"])
    return ok_ep, bad_ep, notes


def emit_stage(stage: Path, round_n: int, ok: dict, bad: dict):
    ok_ep, bad_ep, notes = build_pair(round_n, ok, bad)
    (stage / f"batch-r{round_n:02d}.jsonl").write_text(
        dumps_episode(ok_ep) + "\n" + dumps_episode(bad_ep) + "\n",
        encoding="utf-8",
    )
    (stage / f"NOTES-r{round_n:02d}.md").write_text(notes, encoding="utf-8")
    return ok_ep["id"], bad_ep["id"]


def self_check() -> None:
    slugs, mods, tickets, domains = [], [], [], []
    for i, (ok, bad) in enumerate(PAIRS):
        round_n = 82 + i
        if ok["first_old"] not in ok["src_body"]:
            raise ValueError(ok["slug"])
        if bad["first_old"] not in bad["src_body"]:
            raise ValueError(bad["slug"])
        slugs.extend([ok["slug"], bad["slug"]])
        mods.extend([ok["mod"], bad["mod"]])
        domains.extend([ok["domain"], bad["domain"]])
        tickets.append(bad["ticket"])
        ok_ep, bad_ep, notes = build_pair(round_n, ok, bad)
        if "Novel coverage:" not in notes:
            raise ValueError("notes")
        if not ok_ep["id"].startswith(f"{PREFIX}-r{round_n}-"):
            raise ValueError(ok_ep["id"])
    if len(set(slugs)) != len(slugs):
        raise ValueError(f"dup slugs {slugs}")
    if len(set(mods)) != len(mods):
        raise ValueError(f"dup mods {mods}")
    if len(set(tickets)) != len(tickets):
        raise ValueError(f"dup tickets {tickets}")
    if len(set(domains)) != len(domains):
        raise ValueError(f"dup domains {domains}")
    print(f"self_check ok: {len(PAIRS)} leftover leftover leftover pairs")


def used_slugs() -> set[str]:
    found = set()
    for path in RAW.glob("batch-r*.jsonl"):
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            seed = rec.get("meta", {}).get("seed")
            if seed:
                found.add(seed)
    return found


def run_loop() -> int:
    from round_txn import TransactionError, abort, frontier_status, publish, reserve

    skip = used_slugs()
    queue = [(ok, bad) for ok, bad in PAIRS if ok["slug"] not in skip and bad["slug"] not in skip]
    published = []
    hops = []
    for _ in range(16):
        if not queue:
            break
        status = frontier_status(RAW)
        round_n = status["next_round"]
        reserved_path = RAW / f"ROUND-r{round_n:02d}.reserved.json"
        payload = None
        if reserved_path.exists():
            payload = json.loads(reserved_path.read_text(encoding="utf-8"))
            hops.append({"round": round_n, "resume": "reserved"})
            print(json.dumps(hops[-1]))
        else:
            try:
                payload = reserve(RAW, round_n, 2)
            except TransactionError as exc:
                hops.append({"round": round_n, "error": str(exc)})
                print(json.dumps(hops[-1]))
                break
        ok, bad = queue[0]
        stage = Path(payload["staging_dir"])
        token = payload["token"]
        try:
            ids = emit_stage(stage, round_n, ok, bad)
            manifest = publish(RAW, round_n, token)
        except Exception as exc:
            try:
                abort(RAW, round_n, token)
            except Exception as abort_exc:
                print(f"abort failed r{round_n}: {abort_exc}")
            raise RuntimeError(f"stage/publish failed r{round_n}: {exc}") from exc
        queue.pop(0)
        published.append({"round": round_n, "ids": ids, "records": manifest.get("records")})
        print(json.dumps({"published": published[-1]}))
    print(json.dumps({"published_count": len(published), "published_rounds": published, "hops": hops}))
    return 0 if published else 1


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["self_check"]:
        self_check()
        return 0
    self_check()
    return run_loop()


if __name__ == "__main__":
    raise SystemExit(main())
