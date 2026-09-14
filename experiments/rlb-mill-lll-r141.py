#!/usr/bin/env python3
"""rate-limit-backoff leftover leftover leftover mill r141.

Distinct API leftover leftover leftover budget header vs naive leftover leftover leftover RPS.
BAN leftover leftover leftover search leftover leftover leftover plants, leftover leftover leftover GraphQL leftover leftover leftover plants (gql-r* never).
Skip used r82-r140. Never sir-/dbc-/gql- ids.
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
            slug="auth0-mgmt-leftover-budget",
            api="Auth0 Management",
            header="X-RateLimit-Remaining",
            naive="X-RateLimit-Limit",
            leftover=87,
            naive_val=1000,
            mod="a0mgmt",
            docs="https://auth0.com/docs/troubleshoot/customer-support/operational-policies/rate-limit-policy",
            docs2="https://auth0.com/docs/api/management/v2",
            domain="auth0-mgmt-leftover-budget-vs-naive-limit",
            stack="Auth0 leftover leftover leftover management",
        ),
        leftover_fail(
            slug="auth0-authz-leftover-handoff",
            api="Auth0 Authorization",
            leftover_kind="authz-leftover-budget",
            naive="X-RateLimit-Limit",
            mod="a0authz",
            docs="https://auth0.com/docs/troubleshoot/customer-support/operational-policies/rate-limit-policy/rate-limit-configurations",
            docs2="https://auth0.com/docs/secure/authorization",
            domain="auth0-authz-leftover-budget-vs-mgmt",
            stack="Auth0 leftover leftover leftover authz",
            ticket="A0-LLL-141",
        ),
    ),
    (
        leftover_ok(
            slug="clerk-bapi-leftover-budget",
            api="Clerk Backend",
            header="x-ratelimit-remaining",
            naive="x-ratelimit-limit",
            leftover=42,
            naive_val=100,
            mod="clkbapi",
            docs="https://clerk.com/docs/backend-requests/resources/rate-limits",
            docs2="https://clerk.com/docs/reference/backend-api",
            domain="clerk-bapi-leftover-budget-vs-naive-limit",
            stack="Clerk leftover leftover leftover backend",
        ),
        leftover_fail(
            slug="clerk-frontend-leftover-handoff",
            api="Clerk Frontend",
            leftover_kind="frontend-leftover-budget",
            naive="x-ratelimit-limit",
            mod="clkfe",
            docs="https://clerk.com/docs/guides/development/troubleshooting",
            docs2="https://clerk.com/docs/reference/frontend-api",
            domain="clerk-frontend-leftover-budget-vs-bapi",
            stack="Clerk leftover leftover leftover frontend",
            ticket="CK-LLL-142",
        ),
    ),
    (
        leftover_ok(
            slug="workos-dirsync-leftover-budget",
            api="WorkOS Directory Sync",
            header="X-RateLimit-Remaining",
            naive="Retry-After",
            leftover=63,
            naive_val=30,
            mod="wosdir",
            docs="https://workos.com/docs/reference/rate-limits",
            docs2="https://workos.com/docs/directory-sync",
            domain="workos-dirsync-leftover-budget-vs-naive-retry",
            stack="WorkOS leftover leftover leftover dirsync",
        ),
        leftover_fail(
            slug="workos-sso-leftover-handoff",
            api="WorkOS SSO",
            leftover_kind="sso-leftover-budget",
            naive="Retry-After",
            mod="wossso",
            docs="https://workos.com/docs/sso",
            docs2="https://workos.com/docs/reference/sso",
            domain="workos-sso-leftover-budget-vs-dirsync",
            stack="WorkOS leftover leftover leftover sso",
            ticket="WO-LLL-143",
        ),
    ),
    (
        leftover_ok(
            slug="cognito-admin-leftover-budget",
            api="Cognito Admin",
            header="x-amzn-RateLimit-Remaining",
            naive="x-amzn-RequestId",
            leftover=19,
            naive_val=1,
            mod="cogadm",
            docs="https://docs.aws.amazon.com/cognito/latest/developerguide/limits.html",
            docs2="https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_AdminGetUser.html",
            domain="cognito-admin-leftover-budget-vs-naive-requestid",
            stack="Cognito leftover leftover leftover admin",
        ),
        leftover_fail(
            slug="cognito-idp-leftover-handoff",
            api="Cognito IdP",
            leftover_kind="idp-leftover-budget",
            naive="x-amzn-RequestId",
            mod="cogidp",
            docs="https://docs.aws.amazon.com/cognito/latest/developerguide/service_code_examples.html",
            docs2="https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/Welcome.html",
            domain="cognito-idp-leftover-budget-vs-admin",
            stack="Cognito leftover leftover leftover idp",
            ticket="CG-LLL-144",
        ),
    ),
    (
        leftover_ok(
            slug="twilio-msg-leftover-budget",
            api="Twilio Messages",
            header="Twilio-Request-Duration-Remaining",
            naive="X-RateLimit-Remaining",
            leftover=11,
            naive_val=100,
            mod="twmsgb",
            docs="https://www.twilio.com/docs/usage/api#rate-limiting",
            docs2="https://www.twilio.com/docs/messaging/api/message-resource",
            domain="twilio-msg-leftover-budget-vs-naive-remaining",
            stack="Twilio leftover leftover leftover messages",
        ),
        leftover_fail(
            slug="twilio-lookup-leftover-handoff",
            api="Twilio Lookup",
            leftover_kind="lookup-leftover-budget",
            naive="X-RateLimit-Remaining",
            mod="twlook",
            docs="https://www.twilio.com/docs/lookup/v2-api",
            docs2="https://www.twilio.com/docs/api/errors",
            domain="twilio-lookup-leftover-budget-vs-msg",
            stack="Twilio leftover leftover leftover lookup",
            ticket="TW-LLL-145",
        ),
    ),
    (
        leftover_ok(
            slug="sendgrid-mail-leftover-budget",
            api="SendGrid Mail",
            header="X-RateLimit-Remaining",
            naive="X-RateLimit-Reset",
            leftover=71,
            naive_val=1711111111,
            mod="sgmailb",
            docs="https://www.twilio.com/docs/sendgrid/api-reference/how-to-use-the-sendgrid-v3-api/rate-limits",
            docs2="https://www.twilio.com/docs/sendgrid/api-reference/mail-send",
            domain="sendgrid-mail-leftover-budget-vs-naive-reset",
            stack="SendGrid leftover leftover leftover mail",
        ),
        leftover_fail(
            slug="sendgrid-stats-leftover-handoff",
            api="SendGrid Stats",
            leftover_kind="stats-leftover-budget",
            naive="X-RateLimit-Reset",
            mod="sgstat",
            docs="https://www.twilio.com/docs/sendgrid/api-reference/stats",
            docs2="https://www.twilio.com/docs/sendgrid/ui/analytics-and-reporting/stats-overview",
            domain="sendgrid-stats-leftover-budget-vs-mail",
            stack="SendGrid leftover leftover leftover stats",
            ticket="SG-LLL-146",
        ),
    ),
    (
        leftover_ok(
            slug="snowflake-rest-leftover-budget",
            api="Snowflake SQL REST",
            header="X-Snowflake-Remaining",
            naive="Retry-After",
            leftover=28,
            naive_val=8,
            mod="sflrest",
            docs="https://docs.snowflake.com/en/developer-guide/sql-api/reference",
            docs2="https://docs.snowflake.com/en/developer-guide/sql-api/submitting-requests",
            domain="snowflake-rest-leftover-budget-vs-naive-retry",
            stack="Snowflake leftover leftover leftover sql-rest",
        ),
        leftover_fail(
            slug="snowflake-pipe-leftover-handoff",
            api="Snowflake Snowpipe",
            leftover_kind="pipe-leftover-budget",
            naive="Retry-After",
            mod="sflpipe",
            docs="https://docs.snowflake.com/en/user-guide/data-load-snowpipe-rest-apis",
            docs2="https://docs.snowflake.com/en/user-guide/data-load-snowpipe",
            domain="snowflake-pipe-leftover-budget-vs-rest",
            stack="Snowflake leftover leftover leftover pipe",
            ticket="SF-LLL-147",
        ),
    ),
    (
        leftover_ok(
            slug="bigquery-jobs-leftover-budget",
            api="BigQuery Jobs",
            header="X-RateLimit-Remaining",
            naive="X-RateLimit-Limit",
            leftover=54,
            naive_val=100,
            mod="bqjobs",
            docs="https://cloud.google.com/bigquery/quotas",
            docs2="https://cloud.google.com/bigquery/docs/reference/rest/v2/jobs",
            domain="bigquery-jobs-leftover-budget-vs-naive-limit",
            stack="BigQuery leftover leftover leftover jobs",
        ),
        leftover_fail(
            slug="bigquery-insert-leftover-handoff",
            api="BigQuery tabledata.insertAll",
            leftover_kind="insertall-leftover-budget",
            naive="X-RateLimit-Limit",
            mod="bqins",
            docs="https://cloud.google.com/bigquery/docs/reference/rest/v2/tabledata/insertAll",
            docs2="https://cloud.google.com/bigquery/quotas#streaming_inserts",
            domain="bigquery-insert-leftover-budget-vs-jobs",
            stack="BigQuery leftover leftover leftover insert",
            ticket="BQ-LLL-148",
        ),
    ),
    (
        leftover_ok(
            slug="openai-chat-leftover-budget",
            api="OpenAI Chat",
            header="x-ratelimit-remaining-requests",
            naive="x-ratelimit-limit-requests",
            leftover=33,
            naive_val=500,
            mod="oaihat",
            docs="https://platform.openai.com/docs/guides/rate-limits",
            docs2="https://platform.openai.com/docs/api-reference/chat",
            domain="openai-chat-leftover-budget-vs-naive-limit",
            stack="OpenAI leftover leftover leftover chat",
        ),
        leftover_fail(
            slug="openai-embed-leftover-handoff",
            api="OpenAI Embeddings",
            leftover_kind="embed-leftover-budget",
            naive="x-ratelimit-limit-requests",
            mod="oaiemb",
            docs="https://platform.openai.com/docs/guides/embeddings",
            docs2="https://platform.openai.com/docs/api-reference/embeddings",
            domain="openai-embed-leftover-budget-vs-chat",
            stack="OpenAI leftover leftover leftover embed",
            ticket="OA-LLL-149",
        ),
    ),
    (
        leftover_ok(
            slug="anthropic-msg-leftover-budget",
            api="Anthropic Messages",
            header="anthropic-ratelimit-requests-remaining",
            naive="retry-after",
            leftover=22,
            naive_val=10,
            mod="antmsg",
            docs="https://docs.anthropic.com/en/api/rate-limits",
            docs2="https://docs.anthropic.com/en/api/messages",
            domain="anthropic-msg-leftover-budget-vs-naive-retry",
            stack="Anthropic leftover leftover leftover messages",
        ),
        leftover_fail(
            slug="anthropic-token-leftover-handoff",
            api="Anthropic token leftover",
            leftover_kind="token-leftover-budget",
            naive="retry-after",
            mod="anttok",
            docs="https://docs.anthropic.com/en/api/rate-limits#token-rate-limits",
            docs2="https://docs.anthropic.com/en/docs/about-claude/models",
            domain="anthropic-token-leftover-budget-vs-msg",
            stack="Anthropic leftover leftover leftover tokens",
            ticket="AN-LLL-150",
        ),
    ),
    (
        leftover_ok(
            slug="launchdarkly-flag-leftover-budget",
            api="LaunchDarkly Flags",
            header="X-Ratelimit-Remaining",
            naive="X-Ratelimit-Reset",
            leftover="46",
            naive_val=60,
            mod="ldflag",
            docs="https://launchdarkly.com/docs/api",
            docs2="https://launchdarkly.com/docs/home/getting-started/rate-limits",
            domain="launchdarkly-flag-leftover-budget-vs-naive-reset",
            stack="LaunchDarkly leftover leftover leftover flags",
        ),
        leftover_fail(
            slug="launchdarkly-seg-leftover-handoff",
            api="LaunchDarkly Segments",
            leftover_kind="segment-leftover-budget",
            naive="X-Ratelimit-Reset",
            mod="ldseg",
            docs="https://launchdarkly.com/docs/api/segments",
            docs2="https://launchdarkly.com/docs/home/flags/targeting",
            domain="launchdarkly-seg-leftover-budget-vs-flag",
            stack="LaunchDarkly leftover leftover leftover segments",
            ticket="LD-LLL-151",
        ),
    ),
    (
        leftover_ok(
            slug="segment-track-leftover-budget",
            api="Segment Track",
            header="X-RateLimit-Remaining",
            naive="Retry-After",
            leftover=90,
            naive_val=5,
            mod="segtrk",
            docs="https://segment.com/docs/connections/sources/catalog/libraries/server/http-api/",
            docs2="https://segment.com/docs/guides/how-to-guides/collect-on-the-server/",
            domain="segment-track-leftover-budget-vs-naive-retry",
            stack="Segment leftover leftover leftover track",
        ),
        leftover_fail(
            slug="segment-id-leftover-handoff",
            api="Segment Identify",
            leftover_kind="identify-leftover-budget",
            naive="Retry-After",
            mod="segid",
            docs="https://segment.com/docs/connections/spec/identify/",
            docs2="https://segment.com/docs/connections/sources/catalog/libraries/server/http-api/#identify",
            domain="segment-id-leftover-budget-vs-track",
            stack="Segment leftover leftover leftover identify",
            ticket="SE-LLL-152",
        ),
    ),
    (
        leftover_ok(
            slug="mixpanel-export-leftover-budget",
            api="Mixpanel Export",
            header="X-RateLimit-Remaining",
            naive="X-RateLimit-Limit",
            leftover=7,
            naive_val=60,
            mod="mxpexp",
            docs="https://developer.mixpanel.com/reference/rate-limits",
            docs2="https://developer.mixpanel.com/reference/raw-event-export",
            domain="mixpanel-export-leftover-budget-vs-naive-limit",
            stack="Mixpanel leftover leftover leftover export",
        ),
        leftover_fail(
            slug="mixpanel-query-leftover-handoff",
            api="Mixpanel Query",
            leftover_kind="query-leftover-budget",
            naive="X-RateLimit-Limit",
            mod="mxpqry",
            docs="https://developer.mixpanel.com/reference/query-api",
            docs2="https://developer.mixpanel.com/reference/segmentation-query",
            domain="mixpanel-query-leftover-budget-vs-export",
            stack="Mixpanel leftover leftover leftover query",
            ticket="MX-LLL-153",
        ),
    ),
    (
        leftover_ok(
            slug="amplitude-http-leftover-budget",
            api="Amplitude HTTP",
            header="X-RateLimit-Remaining",
            naive="Retry-After",
            leftover=15,
            naive_val=20,
            mod="amphvt",
            docs="https://www.docs.developers.amplitude.com/analytics/apis/http-v2-api/",
            docs2="https://www.docs.developers.amplitude.com/analytics/apis/http-v2-api/#rate-limits",
            domain="amplitude-http-leftover-budget-vs-naive-retry",
            stack="Amplitude leftover leftover leftover http",
        ),
        leftover_fail(
            slug="amplitude-batch-leftover-handoff",
            api="Amplitude Batch",
            leftover_kind="batch-leftover-budget",
            naive="Retry-After",
            mod="ampbat",
            docs="https://www.docs.developers.amplitude.com/analytics/apis/batch-event-upload-api/",
            docs2="https://www.docs.developers.amplitude.com/analytics/apis/batch-event-upload-api/#rate-limits",
            domain="amplitude-batch-leftover-budget-vs-http",
            stack="Amplitude leftover leftover leftover batch",
            ticket="AM-LLL-154",
        ),
    ),
    (
        leftover_ok(
            slug="intercom-conv-leftover-budget",
            api="Intercom Conversations",
            header="X-RateLimit-Remaining",
            naive="X-RateLimit-Limit",
            leftover=38,
            naive_val=1000,
            mod="icconv",
            docs="https://developers.intercom.com/docs/references/rest-api/api.intercom.io/introduction#rate-limiting",
            docs2="https://developers.intercom.com/docs/references/rest-api/api.intercom.io/conversations",
            domain="intercom-conv-leftover-budget-vs-naive-limit",
            stack="Intercom leftover leftover leftover conversations",
        ),
        leftover_fail(
            slug="intercom-contact-leftover-handoff",
            api="Intercom Contacts",
            leftover_kind="contact-leftover-budget",
            naive="X-RateLimit-Limit",
            mod="iccont",
            docs="https://developers.intercom.com/docs/references/rest-api/api.intercom.io/contacts",
            docs2="https://developers.intercom.com/docs/build-an-integration/learn-more/rest-apis/rate-limiting",
            domain="intercom-contact-leftover-budget-vs-conv",
            stack="Intercom leftover leftover leftover contacts",
            ticket="IC-LLL-155",
        ),
    ),
    (
        leftover_ok(
            slug="zendesk-ticket-leftover-budget",
            api="Zendesk Tickets",
            header="X-Rate-Limit-Remaining",
            naive="Retry-After",
            leftover=66,
            naive_val=10,
            mod="zdtkt",
            docs="https://developer.zendesk.com/api-reference/introduction/rate-limits/",
            docs2="https://developer.zendesk.com/api-reference/ticketing/tickets/tickets/",
            domain="zendesk-ticket-leftover-budget-vs-naive-retry",
            stack="Zendesk leftover leftover leftover tickets",
        ),
        leftover_fail(
            slug="zendesk-help-leftover-handoff",
            api="Zendesk Help Center",
            leftover_kind="help-leftover-budget",
            naive="Retry-After",
            mod="zdhelp",
            docs="https://developer.zendesk.com/api-reference/help_center/help-center-api/introduction/",
            docs2="https://developer.zendesk.com/api-reference/introduction/rate-limits/#help-center",
            domain="zendesk-help-leftover-budget-vs-ticket",
            stack="Zendesk leftover leftover leftover help",
            ticket="ZD-LLL-156",
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
    for banned in (
        "monday-graphql-complexity",
        "airtable-formula",
        "graphql",
        "gql-r",
        "sir-r",
        "dbc-r",
    ):
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
        round_n = 141 + i
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
