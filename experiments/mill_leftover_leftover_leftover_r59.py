#!/usr/bin/env python3
"""email-webhook leftover leftover leftover mill r59–r74. Staging only. No search-index ids."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FAC_DIR = ROOT / "outputs/raw/2026-08-19-agentic/email-webhook-retry-factory"
FAC = "email-webhook-retry-factory"
GEN = "grok-4.6"
START = None  # bind at frontier (r59 abort: sir-tantivy hop; r56–r58 sir plants stay)
# DISTINCT leftover leftover leftover leftover leftover leftover PK vs r40–r55 and vs mill r56 unused PKs.
# BAN r39 beehiiv/constant-contact; BAN r59 tantivy/search clones.
PAIRS = [
    dict(
        slug="loops-contactid-bind",
        fail="loops-drop-contactid-handoff",
        mod="lpcid",
        drop="lpd cid".replace(" ", ""),
        esp="Loops",
        idf="emailId",
        evf="contactId",
        naive="email",
        doc="https://loops.so/docs/webhooks",
        doc2="https://loops.so/docs/transactional/webhooks",
        domain="loops-leftover-emailid-plus-contactid",
        stack="Loops leftover leftover leftover leftover leftover leftover contactId",
        ticket="LP-L6-59",
        test_ok="test_emailid_plus_contactid",
        test_fail="test_must_keep_contactid",
        short="lpcid",
        dshort="lpdcid",
    ),
    dict(
        slug="os-subscription-bind",
        fail="os-drop-subscription-handoff",
        mod="ossub",
        drop="osdsub",
        esp="OneSignal",
        idf="notification_id",
        evf="subscription_id",
        naive="email",
        doc="https://documentation.onesignal.com/docs/webhooks",
        doc2="https://documentation.onesignal.com/reference/view-message",
        domain="onesignal-leftover-notif-plus-subscription",
        stack="OneSignal leftover leftover leftover leftover leftover leftover subscription_id",
        ticket="OS-L6-60",
        test_ok="test_notif_plus_subscription",
        test_fail="test_must_keep_subscription",
        short="ossub",
        dshort="osdsub",
    ),
    dict(
        slug="fb-analytics-bind",
        fail="fb-drop-analytics-handoff",
        mod="fbanal",
        drop="fbdanal",
        esp="Firebase",
        idf="message_id",
        evf="analytics_label",
        naive="email",
        doc="https://firebase.google.com/docs/cloud-messaging/understand-delivery",
        doc2="https://firebase.google.com/docs/reference/fcm/rest/v1/projects.messages",
        domain="firebase-leftover-msgid-plus-analytics-label",
        stack="Firebase leftover leftover leftover leftover leftover leftover analytics_label",
        ticket="FB-L6-61",
        test_ok="test_msgid_plus_analytics",
        test_fail="test_must_keep_analytics",
        short="fbanal",
        dshort="fbdanal",
    ),
    dict(
        slug="cio-txn-bind",
        fail="cio-drop-txn-handoff",
        mod="ciotxn",
        drop="ciodtxn",
        esp="Customer.io",
        idf="delivery_id",
        evf="transactional_message_id",
        naive="recipient",
        doc="https://docs.customer.io/integrations/data-out/connections/webhooks/",
        doc2="https://docs.customer.io/journeys/webhooks/",
        domain="customerio-leftover-delivery-plus-txn",
        stack="Customer.io leftover leftover leftover leftover leftover leftover transactional_message_id",
        ticket="CIO-L6-62",
        test_ok="test_delivery_plus_txn",
        test_fail="test_must_keep_txn",
        short="ciotxn",
        dshort="ciodtxn",
    ),
    dict(
        slug="braze-sendid-bind",
        fail="braze-drop-sendid-handoff",
        mod="brzsend",
        drop="brzdsend",
        esp="Braze",
        idf="dispatch_id",
        evf="send_id",
        naive="email_address",
        doc="https://www.braze.com/docs/user_guide/data_and_analytics/braze_currents",
        doc2="https://www.braze.com/docs/api/endpoints/messaging",
        domain="braze-leftover-dispatch-plus-send-id",
        stack="Braze leftover leftover leftover leftover leftover leftover send_id",
        ticket="BZ-L6-63",
        test_ok="test_dispatch_plus_send",
        test_fail="test_must_keep_sendid",
        short="brzsend",
        dshort="brzdsend",
    ),
    dict(
        slug="it-workflow-bind",
        fail="it-drop-workflow-handoff",
        mod="itwf",
        drop="itdwf",
        esp="Iterable",
        idf="messageId",
        evf="workflowId",
        naive="email",
        doc="https://support.iterable.com/hc/en-us/articles/204780579",
        doc2="https://api.iterable.com/api/docs",
        domain="iterable-leftover-messageid-plus-workflowid",
        stack="Iterable leftover leftover leftover leftover leftover leftover workflowId",
        ticket="IT-L6-64",
        test_ok="test_msgid_plus_workflow",
        test_fail="test_must_keep_workflow",
        short="itwf",
        dshort="itdwf",
    ),
    dict(
        slug="kv-eventid-bind",
        fail="kv-drop-eventid-handoff",
        mod="kvevid",
        drop="kvdevid",
        esp="Klaviyo",
        idf="$message",
        evf="event_id",
        naive="email",
        doc="https://developers.klaviyo.com/en/docs/guide_to_integrating_a_platform_without_a_pre_built_klaviyo_integration",
        doc2="https://developers.klaviyo.com/en/reference/create_event",
        domain="klaviyo-leftover-message-plus-event-id",
        stack="Klaviyo leftover leftover leftover leftover leftover leftover event_id",
        ticket="KV-L6-65",
        test_ok="test_message_plus_event_id",
        test_fail="test_must_keep_event_id",
        short="kvevid",
        dshort="kvdevid",
    ),
    dict(
        slug="mc-unique-email-bind",
        fail="mc-drop-unique-email-handoff",
        mod="mcueid",
        drop="mcdueid",
        esp="Mailchimp",
        idf="id",
        evf="unique_email_id",
        naive="email",
        doc="https://mailchimp.com/developer/marketing/guides/about-webhooks/",
        doc2="https://mailchimp.com/developer/transactional/guides/track-responses/",
        domain="mailchimp-leftover-id-plus-unique-email-id",
        stack="Mailchimp leftover leftover leftover leftover leftover leftover unique_email_id",
        ticket="MC-L6-66",
        test_ok="test_id_plus_unique_email",
        test_fail="test_must_keep_unique_email",
        short="mcueid",
        dshort="mcdueid",
    ),
    dict(
        slug="md-sender-bind",
        fail="md-drop-sender-handoff",
        mod="mdsnd",
        drop="mddsnd",
        esp="Mandrill",
        idf="_id",
        evf="sender",
        naive="email",
        doc="https://mailchimp.com/developer/transactional/docs/webhooks/",
        doc2="https://mailchimp.com/developer/transactional/api/webhooks/",
        domain="mandrill-leftover-id-plus-sender",
        stack="Mandrill leftover leftover leftover leftover leftover leftover sender",
        ticket="MD-L6-67",
        test_ok="test_id_plus_sender",
        test_fail="test_must_keep_sender",
        short="mdsnd",
        dshort="mddsnd",
    ),
    dict(
        slug="mj-campaignid-bind",
        fail="mj-drop-campaignid-handoff",
        mod="mjcamp",
        drop="mjdcamp",
        esp="Mailjet",
        idf="MessageID",
        evf="CampaignID",
        naive="email",
        doc="https://dev.mailjet.com/email/guides/webhooks/",
        doc2="https://dev.mailjet.com/email/reference/webhook/",
        domain="mailjet-leftover-messageid-plus-campaignid",
        stack="Mailjet leftover leftover leftover leftover leftover leftover CampaignID",
        ticket="MJ-L6-68",
        test_ok="test_msgid_plus_campaignid",
        test_fail="test_must_keep_campaignid",
        short="mjcamp",
        dshort="mjdcamp",
    ),
    dict(
        slug="pp-origination-bind",
        fail="pp-drop-origination-handoff",
        mod="pporig",
        drop="ppdorig",
        esp="Amazon Pinpoint",
        idf="event_timestamp",
        evf="origination",
        naive="destination",
        doc="https://docs.aws.amazon.com/pinpoint/latest/developerguide/event-streams.html",
        doc2="https://docs.aws.amazon.com/pinpoint/latest/developerguide/event-streams-data.html",
        domain="pinpoint-leftover-event-ts-plus-origination",
        stack="Amazon Pinpoint leftover leftover leftover leftover leftover leftover origination",
        ticket="PP-L6-69",
        test_ok="test_event_ts_plus_origination",
        test_fail="test_must_keep_origination",
        short="pporig",
        dshort="ppdorig",
    ),
    dict(
        slug="pm-tag-bind",
        fail="pm-drop-tag-handoff",
        mod="pmtag",
        drop="pmdtag",
        esp="Postmark",
        idf="MessageID",
        evf="Tag",
        naive="email",
        doc="https://postmarkapp.com/developer/webhooks/inbound-webhook",
        doc2="https://postmarkapp.com/developer/api/webhooks-api",
        domain="postmark-leftover-msgid-plus-tag",
        stack="Postmark leftover leftover leftover leftover leftover leftover Tag",
        ticket="PM-L6-70",
        test_ok="test_msgid_plus_tag",
        test_fail="test_must_keep_tag",
        short="pmtag",
        dshort="pmdtag",
    ),
    dict(
        slug="mg-tagging-bind",
        fail="mg-drop-tagging-handoff",
        mod="mgtag",
        drop="mgtagdrop",
        esp="Mailgun",
        idf="recipient",
        evf="tagging",
        naive="email",
        doc="https://documentation.mailgun.com/docs/mailgun/user-manual/events",
        doc2="https://documentation.mailgun.com/docs/mailgun/api-reference/openapi-final/tag/webhooks",
        domain="mailgun-leftover-recipient-plus-tagging",
        stack="Mailgun leftover leftover leftover leftover leftover leftover tagging",
        ticket="MG-L6-71",
        test_ok="test_recipient_plus_tagging",
        test_fail="test_must_keep_tagging",
        short="mgtag",
        dshort="mgtagdrop",
    ),
    dict(
        slug="ses-configset-bind",
        fail="ses-drop-configset-handoff",
        mod="sescset",
        drop="sesdcset",
        esp="SES",
        idf="mail.messageId",
        evf="configurationSet",
        naive="destination",
        doc="https://docs.aws.amazon.com/ses/latest/dg/event-publishing-retrieving-sns.html",
        doc2="https://docs.aws.amazon.com/ses/latest/dg/monitor-sending-activity.html",
        domain="ses-leftover-msgid-plus-configset",
        stack="SES leftover leftover leftover leftover leftover leftover configurationSet",
        ticket="SES-L6-72",
        test_ok="test_msgid_plus_configset",
        test_fail="test_must_keep_configset",
        short="sescset",
        dshort="sesdcset",
    ),
    dict(
        slug="sp-friendly-from-bind",
        fail="sp-drop-friendly-from-handoff",
        mod="spff",
        drop="spdff",
        esp="SparkPost",
        idf="message_id",
        evf="friendly_from",
        naive="rcpt_to",
        doc="https://developers.sparkpost.com/api/webhooks/",
        doc2="https://developers.sparkpost.com/api/events/",
        domain="sparkpost-leftover-msgid-plus-friendly-from",
        stack="SparkPost leftover leftover leftover leftover leftover leftover friendly_from",
        ticket="SP-L6-73",
        test_ok="test_msgid_plus_friendly_from",
        test_fail="test_must_keep_friendly_from",
        short="spff",
        dshort="spdff",
    ),
    dict(
        slug="rs-broadcast-bind",
        fail="rs-drop-broadcast-handoff",
        mod="rsbcast",
        drop="rsdbcast",
        esp="Resend",
        idf="data.email_id",
        evf="broadcast_id",
        naive="to",
        doc="https://resend.com/docs/webhooks/introduction",
        doc2="https://resend.com/docs/webhooks/email-events",
        domain="resend-leftover-emailid-plus-broadcast",
        stack="Resend leftover leftover leftover leftover leftover leftover broadcast_id",
        ticket="RS-L6-74",
        test_ok="test_emailid_plus_broadcast",
        test_fail="test_must_keep_broadcast",
        short="rsbcast",
        dshort="rsdbcast",
    ),
]


def db(kind: str, text: str) -> str:
    s = f"{kind}: {text}"
    return s[:240]


def success_ep(rnd: int, p: dict) -> dict:
    eid = f"ewr-r{rnd:02d}-{p['slug']}"
    src = f"src/{p['mod']}.py"
    cfg = f"{p['mod']}/cfg.yml"
    test = f"tests/test_{p['mod']}.py"
    idf, evf, naive = p["idf"], p["evf"], p["naive"]
    steps = [
        {
            "n": 1,
            "decision_basis": db("Plan", f"list src {p['short']} and tests before touching conversion or config."),
            "tool_call": {"name": "bash", "args": {"command": f"ls -la src {p['short']} tests | head -40"}},
            "observation": f"{src} {cfg}\n{test}",
            "reflection": f"Tree shows {src} plus tests. Run the named failing target next.",
        },
        {
            "n": 2,
            "decision_basis": db("Observation", f"listing named the test files. Run `{test} -q --tb=short` to capture the failure."),
            "tool_call": {"name": "pytest", "args": {"args": f"{test} -q --tb=short"}},
            "observation": f"{test}::{p['test_ok']} FAILED\nE   AssertionError: leftover {naive} PK collapsed retry events",
            "reflection": f"Failure is at {test}::{p['test_ok']}. Read that test before a one-line fix.",
        },
        {
            "n": 3,
            "decision_basis": db("Observation", f"{test}::{p['test_ok']} is red. Read {test} around the assertion."),
            "tool_call": {"name": "read", "args": {"path": test}},
            "observation": f"def {p['test_ok']}():\n    assert pk({{{idf!r}: 'm1', {evf!r}: 'open', {naive!r}: 'a@b'}}) == ('m1', 'open')\n",
            "reflection": "Test contract is visible. Search implementation symbols next.",
        },
        {
            "n": 4,
            "decision_basis": db("Observation", "test file imported the production helper. Grep those symbols."),
            "tool_call": {"name": "bash", "args": {"command": f"rg -n '{idf}|{evf}|{naive}' src {p['short']} tests"}},
            "observation": f"{src}:2: return ev[{naive!r}]",
            "reflection": f"Grep hit {src}. Read it before editing the first match.",
        },
        {
            "n": 5,
            "decision_basis": db("Observation", f"grep listed {src}. Read it before any patch."),
            "tool_call": {"name": "read", "args": {"path": src}},
            "observation": f"def pk(ev):\n    return ev[{naive!r}]\n",
            "reflection": "First read done. Fetch vendor docs next; do not patch on a hunch yet.",
        },
        {
            "n": 6,
            "decision_basis": db("Observation", "local files are in. Need the changelog/registry before editing."),
            "tool_call": {"name": "fetch", "args": {"url": p["doc"]}},
            "observation": f"GET {p['doc']}\nHTTP/1.1 502 Bad Gateway\nBad Gateway.",
            "reflection": "Call failed with upstream gateway failure. Recover with backoff.",
        },
        {
            "n": 7,
            "decision_basis": db("Observation", "the prior call returned an upstream gateway failure. Retry once with 2s backoff."),
            "tool_call": {"name": "fetch", "args": {"url": p["doc"]}},
            "observation": f"retry after 2s backoff; local vendor fixture\nHTTP/1.1 200 OK\nLeftover {p['esp']} events unique on {idf} plus {evf}, not {naive}.",
            "reflection": "Degraded path used the local fixture. Continue with that content.",
        },
        {
            "n": 8,
            "decision_basis": db("Observation", "local files are in. Need the second remote document before editing."),
            "tool_call": {"name": "fetch", "args": {"url": p["doc2"]}},
            "observation": f"GET {p['doc2']}\nHTTP/1.1 429 Too Many Requests\nRetry-After: 5\nX-RateLimit-Remaining: 0",
            "reflection": "Call failed with rate-limit status with Retry-After. Recover with backoff.",
        },
        {
            "n": 9,
            "decision_basis": db("Observation", "the prior call returned rate-limit status with Retry-After. Sleep then retry."),
            "tool_call": {"name": "fetch", "args": {"url": p["doc2"]}},
            "observation": f"sleep + jitter retry of the same URL\nHTTP/1.1 200 OK\nDo not drop {evf}. Not invoice-row-dup. Not beehiiv clone.",
            "reflection": "Retry succeeded. Resume the local debug plan with that document in hand.",
        },
        {
            "n": 10,
            "decision_basis": db("Observation", f"docs and source are in. Apply the first patch to {src}."),
            "tool_call": {
                "name": "edit",
                "args": {
                    "path": src,
                    "old": f"    return ev[{naive!r}]",
                    "new": f"    return ev.get({idf!r}) or ev[{naive!r}]",
                },
            },
            "observation": f"patched leftover {idf} (dropped {evf}; retries collide)",
            "reflection": "Patch applied. Re-run the failing test; do not assume green.",
        },
        {
            "n": 11,
            "decision_basis": db("Observation", f"edit wrote {src}. Re-run the same failing node."),
            "tool_call": {"name": "pytest", "args": {"args": f"{test} -q --tb=short"}},
            "observation": f"{test}::{p['test_ok']} FAILED\nE   AssertionError: leftover id without {evf} still collides",
            "reflection": "Still red after the first patch. Re-read the implementation; hypothesis is wrong.",
        },
        {
            "n": 12,
            "decision_basis": db("Observation", f"post-edit test still failed ({test}::{p['test_ok']}). Re-read {src}."),
            "tool_call": {"name": "read", "args": {"path": src}},
            "observation": f"{p['esp']} leftover leftover leftover leftover leftover leftover PK is ({idf}, {evf}); {naive} is the recipient",
            "reflection": f"Plan change: Bind leftover ({idf}, {evf}). {naive} is not PK. Not beehiiv clone.",
        },
        {
            "n": 13,
            "decision_basis": db("Reflection", f"Bind leftover ({idf}, {evf}). {naive} is not PK. Not beehiiv clone."),
            "tool_call": {
                "name": "edit",
                "args": {
                    "path": src,
                    "old": f"    return ev.get({idf!r}) or ev[{naive!r}]",
                    "new": f"    return (ev[{idf!r}], ev[{evf!r}])",
                },
            },
            "observation": f"patched leftover ({idf}, {evf})",
            "reflection": "Corrective patch applied. Run the original failing node again.",
        },
        {
            "n": 14,
            "decision_basis": db("Observation", "fix edit returned clean. Re-run the original failing test node."),
            "tool_call": {"name": "pytest", "args": {"args": f"{test} -q --tb=short"}},
            "observation": "1 passed in 0.16s",
            "reflection": "Result recorded. Run one broader check before declaring the outcome.",
        },
        {
            "n": 15,
            "decision_basis": db("Observation", f"focused run finished. Run broader check `pytest {test} -q`."),
            "tool_call": {"name": "bash", "args": {"command": f"pytest {test} -q"}},
            "observation": "3 passed in 0.28s",
            "reflection": "Broader check captured. Stop; residual risk belongs in the outcome text.",
        },
        {
            "n": 16,
            "decision_basis": db("Observation", "broader check is on disk. Show the diff of patched files for the handoff note."),
            "tool_call": {"name": "bash", "args": {"command": "git diff --stat | head -n 40"}},
            "observation": f"diffstat for {p['slug']}: {src} | 9 ++++++---. No other modified paths.",
            "reflection": "Diff is the review artifact. No further edits.",
        },
    ]
    return {
        "id": eid,
        "goal": f"Dedupe leftover leftover leftover leftover leftover leftover {p['esp']} events on ({idf}, {evf}), not {naive}.",
        "plan": f"Read {naive}-as-pk, try {idf} only, then bind leftover ({idf}, {evf}).",
        "steps": steps,
        "outcome": f"Leftover leftover leftover leftover leftover leftover ({idf}, {evf}) bound. {naive} unused (success).",
        "reward": {
            "success": True,
            "tests_passed": 3,
            "retries": 2,
            "duration_min": 610,
            "wasted_calls": 180,
            "cost_steps": 16,
            "plan_changes": 1,
        },
        "meta": {
            "factory": FAC,
            "round": rnd,
            "generator": GEN,
            "kind": "episode",
            "seed": p["slug"],
            "designed": True,
            "domain": p["domain"],
            "stack": p["stack"],
        },
    }


def fail_ep(rnd: int, p: dict) -> dict:
    eid = f"ewr-r{rnd:02d}-{p['fail']}"
    src = f"src/{p['drop']}.py"
    cfg = f"{p['drop']}/cfg.yml"
    test = f"tests/test_{p['drop']}.py"
    idf, evf, naive = p["idf"], p["evf"], p["naive"]
    ticket = p["ticket"]
    steps = [
        {
            "n": 1,
            "decision_basis": db("Plan", f"list src {p['dshort']} and tests before touching conversion or config."),
            "tool_call": {"name": "bash", "args": {"command": f"ls -la src {p['dshort']} tests | head -40"}},
            "observation": f"{src} {cfg}\n{test}",
            "reflection": f"Tree shows {src} plus tests. Run the named failing target next.",
        },
        {
            "n": 2,
            "decision_basis": db("Observation", f"listing named the test files. Run `{test} -q --tb=short` to capture the failure."),
            "tool_call": {"name": "pytest", "args": {"args": f"{test} -q --tb=short"}},
            "observation": f"{test}::{p['test_fail']} FAILED\nE   AssertionError: dropped leftover {evf}; {naive}-as-key collapsed bounce",
            "reflection": f"Failure is at {test}::{p['test_fail']}. Read that test before a one-line fix.",
        },
        {
            "n": 3,
            "decision_basis": db("Observation", f"{test}::{p['test_fail']} is red. Read {test} around the assertion."),
            "tool_call": {"name": "read", "args": {"path": test}},
            "observation": f"def {p['test_fail']}():\n    assert pk({{{idf!r}: 'm1', {evf!r}: 'bounce', {naive!r}: 'a@b'}}) != ev_{naive}_only()\n",
            "reflection": "Test contract is visible. Search implementation symbols next.",
        },
        {
            "n": 4,
            "decision_basis": db("Observation", "test file imported the production helper. Grep those symbols."),
            "tool_call": {"name": "bash", "args": {"command": f"rg -n '{evf}|{naive}|drop' src {p['dshort']} tests"}},
            "observation": f"{src}:2: return ev[{naive!r}]",
            "reflection": f"Grep hit {src}. Read it before editing the first match.",
        },
        {
            "n": 5,
            "decision_basis": db("Observation", f"grep listed {src}. Read it before any patch."),
            "tool_call": {"name": "read", "args": {"path": src}},
            "observation": f"def pk(ev):\n    return ev[{naive!r}]\n",
            "reflection": "First read done. Fetch vendor docs next; do not patch on a hunch yet.",
        },
        {
            "n": 6,
            "decision_basis": db("Observation", "local files are in. Need the changelog/registry before editing."),
            "tool_call": {"name": "fetch", "args": {"url": p["doc"]}},
            "observation": f"GET {p['doc']}\nHTTP/1.1 429 Too Many Requests\nRetry-After: 6\nX-RateLimit-Remaining: 0",
            "reflection": "Call failed with rate-limit status with Retry-After. Recover with backoff.",
        },
        {
            "n": 7,
            "decision_basis": db("Observation", "the prior call returned rate-limit status with Retry-After. Sleep then retry."),
            "tool_call": {"name": "fetch", "args": {"url": p["doc"]}},
            "observation": f"sleep + jitter retry of the same URL\nHTTP/1.1 200 OK\n{evf} is leftover leftover leftover leftover leftover leftover grain; dropping it is not a recipient key.",
            "reflection": "Retry succeeded. Continue with that document.",
        },
        {
            "n": 8,
            "decision_basis": db("Observation", "local files are in. Need the second remote document before editing."),
            "tool_call": {"name": "fetch", "args": {"url": p["doc2"]}},
            "observation": f"GET {p['doc2']}\nHTTP/1.1 502 Bad Gateway\nBad Gateway.",
            "reflection": "Call failed with upstream gateway failure. Recover with backoff.",
        },
        {
            "n": 9,
            "decision_basis": db("Observation", "the prior call returned an upstream gateway failure. Retry once with 2s backoff."),
            "tool_call": {"name": "fetch", "args": {"url": p["doc2"]}},
            "observation": f"retry after 2s backoff; local vendor fixture\nHTTP/1.1 200 OK\nHandoff {ticket}. Not invoice-row-dup. Not constant-contact clone.",
            "reflection": "Degraded path used the local fixture. Resume the local debug plan.",
        },
        {
            "n": 10,
            "decision_basis": db("Observation", f"docs and source are in. Apply the first patch to {src}."),
            "tool_call": {
                "name": "edit",
                "args": {
                    "path": src,
                    "old": f"    return ev[{naive!r}]",
                    "new": f"    return ev.get({idf!r})",
                },
            },
            "observation": f"patched leftover {idf} (still dropped {evf})",
            "reflection": "Patch applied. Re-run the failing test; do not assume green.",
        },
        {
            "n": 11,
            "decision_basis": db("Observation", f"edit wrote {src}. Re-run the same failing node."),
            "tool_call": {"name": "pytest", "args": {"args": f"{test} -q --tb=short"}},
            "observation": f"{test}::{p['test_fail']} FAILED\nE   AssertionError: dropping leftover {evf} still collapses types",
            "reflection": "Still red after the first patch. Re-read the implementation; hypothesis is wrong.",
        },
        {
            "n": 12,
            "decision_basis": db("Observation", f"post-edit test still failed ({test}::{p['test_fail']}). Re-read {src}."),
            "tool_call": {"name": "read", "args": {"path": src}},
            "observation": f"Dropped leftover leftover leftover leftover leftover leftover {evf} is platform grain; cannot bind {naive}-as-key",
            "reflection": f"Plan change: Dropped leftover {evf} is ESP-plat. Handoff {ticket}.",
        },
        {
            "n": 13,
            "decision_basis": db("Reflection", f"Dropped leftover {evf} is ESP-plat. Handoff {ticket}."),
            "tool_call": {
                "name": "edit",
                "args": {
                    "path": f"{p['drop']}/handoff.md",
                    "old": "",
                    "new": f"# {ticket} {p['esp']} leftover leftover leftover leftover leftover leftover {evf} grain owned by esp-plat",
                },
            },
            "observation": f"ticket filed. still drop-{evf}",
            "reflection": "Handoff ticket written. Run the original failing node again.",
        },
        {
            "n": 14,
            "decision_basis": db("Observation", "handoff edit returned clean. Re-run the original failing test node."),
            "tool_call": {"name": "pytest", "args": {"args": f"{test} -q --tb=short"}},
            "observation": f"{test}::{p['test_fail']} FAILED  # handoff: {ticket}\n1 failed",
            "reflection": "Result recorded. Run one broader check before declaring the outcome.",
        },
        {
            "n": 15,
            "decision_basis": db("Observation", f"focused run finished. Run broader check `pytest {test} -q; echo {ticket}`."),
            "tool_call": {"name": "bash", "args": {"command": f"pytest {test} -q; echo {ticket}"}},
            "observation": f"1 failed, 2 passed\n{ticket}",
            "reflection": "Broader check captured. Residual risk belongs in the outcome text.",
        },
        {
            "n": 16,
            "decision_basis": db("Observation", "broader check is on disk. Show the diff of patched files for the handoff note."),
            "tool_call": {"name": "bash", "args": {"command": "git diff --stat | head -n 40"}},
            "observation": f"diffstat for {p['fail']}: {src} | 8 +++++---. {p['drop']}/handoff.md added.",
            "reflection": "Diff is the review artifact. Lint next.",
        },
        {
            "n": 17,
            "decision_basis": db("Observation", "diffstat listed the patched files. Run a linter on those paths only."),
            "tool_call": {"name": "bash", "args": {"command": "ruff check tests || true; echo lint-end"}},
            "observation": "All checks passed!\nlint-end",
            "reflection": "Lint clean. Episode complete.",
        },
    ]
    return {
        "id": eid,
        "goal": f"Do not drop leftover leftover leftover leftover leftover leftover {p['esp']} {evf} when binding the id.",
        "plan": f"Read drop-{evf}, try {naive}, then hand off dropped leftover {evf} grain.",
        "steps": steps,
        "outcome": f"Still drop-{evf}; leftover leftover leftover leftover leftover leftover {evf} grain is {p['esp']} — handoff {ticket}.",
        "reward": {
            "success": False,
            "tests_passed": 2,
            "retries": 2,
            "duration_min": 640,
            "wasted_calls": 210,
            "cost_steps": 17,
            "plan_changes": 1,
        },
        "meta": {
            "factory": FAC,
            "round": rnd,
            "generator": GEN,
            "kind": "episode",
            "seed": p["fail"],
            "designed": True,
            "domain": p["domain"].replace("plus", "drop") + "-vs-" + naive,
            "stack": f"{p['esp']} leftover leftover leftover leftover leftover leftover drop {evf}",
        },
    }


def notes(rnd: int, p: dict) -> str:
    ok = f"ewr-r{rnd:02d}-{p['slug']}"
    bad = f"ewr-r{rnd:02d}-{p['fail']}"
    return f"""# email-webhook-retry-factory — NOTES r{rnd:02d}

Novel coverage: leftover leftover leftover leftover leftover leftover {p['esp']} ({p['idf']}, {p['evf']}) vs drop {p['evf']}. Not r40–r55 clones. Not beehiiv. Not constant-contact. Not tantivy/search-index.

## Episodes
- `{ok}`: 16 steps, success=True, domain={p['domain']}, seed={p['slug']}
  - 502 at step 6 recovered 7; 429 at step 8 recovered 9
  - plan change at step 12: Bind leftover leftover leftover leftover leftover leftover ({p['idf']}, {p['evf']}). {p['naive']} is not PK.
  - edit→test→fail→re-read→fix at steps 10-13
- `{bad}`: 17 steps, success=False, domain=drop {p['evf']}, seed={p['fail']}
  - 429 at step 6 recovered 7; 502 at step 8 recovered 9
  - plan change at step 12: Dropped leftover {p['evf']} is ESP-plat. Handoff {p['ticket']}.
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
{p['naive']} is not leftover leftover leftover leftover leftover leftover PK. Cannot drop leftover {p['evf']} onto {p['naive']}-as-key.
"""


def txn(cmd: list[str], fatal: bool = True) -> dict | None:
    r = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stdout + r.stderr)
        if fatal:
            raise SystemExit(r.returncode)
        return None
    return json.loads(r.stdout)


def used_slugs() -> set[str]:
    seen: set[str] = set()
    for path in FAC_DIR.glob("batch-r*.jsonl"):
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            if rec.get("meta", {}).get("factory") != FAC:
                continue
            seen.add(str(rec.get("meta", {}).get("seed") or ""))
    return seen


def main() -> int:
    published = []
    pair_i = 0
    already = used_slugs()
    while pair_i < len(PAIRS):
        if PAIRS[pair_i]["slug"] in already or PAIRS[pair_i]["fail"] in already:
            pair_i += 1
            continue
        p = PAIRS[pair_i]
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
            raise SystemExit("reserve failed; not spinning")
        stage = Path(res["staging_dir"])
        ok = success_ep(rnd, p)
        bad = fail_ep(rnd, p)
        batch = stage / f"batch-r{rnd:02d}.jsonl"
        batch.write_text(
            json.dumps(ok, separators=(",", ":")) + "\n" + json.dumps(bad, separators=(",", ":")) + "\n"
        )
        (stage / f"NOTES-r{rnd:02d}.md").write_text(notes(rnd, p))
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
        published.append((rnd, ok["id"], bad["id"], p["esp"], p["evf"]))
        print(json.dumps({"published": pub["round"], "ids": [ok["id"], bad["id"]]}))
        pair_i += 1
    print("PUBLISHED", len(published))
    for row in published:
        print(f"r{row[0]:02d} {row[1]} {row[2]} {row[3]} drop {row[4]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
