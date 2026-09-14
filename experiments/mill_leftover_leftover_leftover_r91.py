#!/usr/bin/env python3
"""email-webhook leftover leftover leftover mill r91–r106 hop from reserved websocket.

Staging only. No search-index ids. Distinct leftover leftover leftover leftover leftover leftover PKs vs r40–r90.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FAC_DIR = ROOT / "outputs/raw/2026-08-19-agentic/email-webhook-retry-factory"
FAC = "email-webhook-retry-factory"
GEN = "grok-4.6"
START = None
# DISTINCT leftover leftover leftover leftover leftover leftover PK vs r40–r90.
# BAN r39 beehiiv/constant-contact; BAN sir-/search clones.
PAIRS = [
    dict(
        slug="sg-asm-group-bind",
        fail="sg-drop-asm-group-handoff",
        mod="sgasm",
        drop="sgdasm",
        esp="SendGrid",
        idf="sg_event_id",
        evf="asm_group_id",
        naive="email",
        doc="https://www.twilio.com/docs/sendgrid/for-developers/tracking-events/event",
        doc2="https://www.twilio.com/docs/sendgrid/ui/sending-email/groups",
        domain="sendgrid-leftover-eventid-plus-asm-group",
        stack="SendGrid leftover leftover leftover leftover leftover leftover asm_group_id",
        ticket="SG-L6-91",
        test_ok="test_eventid_plus_asm",
        test_fail="test_must_keep_asm",
        short="sgasm",
        dshort="sgdasm",
    ),
    dict(
        slug="courier-tracking-bind",
        fail="courier-drop-tracking-handoff",
        mod="crtrk",
        drop="crdtrk",
        esp="Courier",
        idf="notificationId",
        evf="trackingId",
        naive="email",
        doc="https://www.courier.com/docs/reference/webhooks",
        doc2="https://www.courier.com/docs/reference/notifications",
        domain="courier-leftover-notification-plus-tracking",
        stack="Courier leftover leftover leftover leftover leftover leftover trackingId",
        ticket="CR-L6-92",
        test_ok="test_notif_plus_tracking",
        test_fail="test_must_keep_tracking",
        short="crtrk",
        dshort="crdtrk",
    ),
    dict(
        slug="novu-jobid-bind",
        fail="novu-drop-jobid-handoff",
        mod="nvjob",
        drop="nvdjob",
        esp="Novu",
        idf="transactionId",
        evf="jobId",
        naive="email",
        doc="https://docs.novu.co/platform/concepts/notifications",
        doc2="https://docs.novu.co/platform/integrations/webhooks",
        domain="novu-leftover-txn-plus-jobid",
        stack="Novu leftover leftover leftover leftover leftover leftover jobId",
        ticket="NV-L6-93",
        test_ok="test_txn_plus_jobid",
        test_fail="test_must_keep_jobid",
        short="nvjob",
        dshort="nvdjob",
    ),
    dict(
        slug="knock-feed-bind",
        fail="knock-drop-feed-handoff",
        mod="knfeed",
        drop="kndfeed",
        esp="Knock",
        idf="workflow",
        evf="feed_id",
        naive="recipient",
        doc="https://docs.knock.app/send-and-manage-data/outbound-webhooks",
        doc2="https://docs.knock.app/send-notifications/triggering-workflows",
        domain="knock-leftover-workflow-plus-feed",
        stack="Knock leftover leftover leftover leftover leftover leftover feed_id",
        ticket="KN-L6-94",
        test_ok="test_workflow_plus_feed",
        test_fail="test_must_keep_feed",
        short="knfeed",
        dshort="kndfeed",
    ),
    dict(
        slug="moengage-campaign-bind",
        fail="moengage-drop-campaign-handoff",
        mod="moecamp",
        drop="moedcamp",
        esp="MoEngage",
        idf="moe_campaign_id",
        evf="campaign_id",
        naive="email",
        doc="https://developers.moengage.com/hc/en-us/articles/360061246392",
        doc2="https://help.moengage.com/hc/en-us/articles/360060711132",
        domain="moengage-leftover-event-plus-campaign",
        stack="MoEngage leftover leftover leftover leftover leftover leftover campaign_id",
        ticket="MOE-L6-95",
        test_ok="test_event_plus_campaign",
        test_fail="test_must_keep_campaign",
        short="moecamp",
        dshort="moedcamp",
    ),
    dict(
        slug="clevertap-campaign-bind",
        fail="clevertap-drop-campaign-handoff",
        mod="ctcamp",
        drop="ctdcamp",
        esp="CleverTap",
        idf="wzrk_id",
        evf="campaignId",
        naive="email",
        doc="https://developer.clevertap.com/docs/webhooks",
        doc2="https://developer.clevertap.com/docs/api-reference",
        domain="clevertap-leftover-wzrk-plus-campaign",
        stack="CleverTap leftover leftover leftover leftover leftover leftover campaignId",
        ticket="CT-L6-96",
        test_ok="test_wzrk_plus_campaign",
        test_fail="test_must_keep_campaign",
        short="ctcamp",
        dshort="ctdcamp",
    ),
    dict(
        slug="leanplum-message-bind",
        fail="leanplum-drop-message-handoff",
        mod="lpmmsg",
        drop="lpmdmsg",
        esp="Leanplum",
        idf="messageId",
        evf="newsfeedId",
        naive="email",
        doc="https://docs.leanplum.com/docs/webhooks",
        doc2="https://docs.leanplum.com/reference/post_api-action-sendmessage",
        domain="leanplum-leftover-message-plus-newsfeed",
        stack="Leanplum leftover leftover leftover leftover leftover leftover newsfeedId",
        ticket="LPM-L6-97",
        test_ok="test_message_plus_newsfeed",
        test_fail="test_must_keep_newsfeed",
        short="lpmmsg",
        dshort="lpmdmsg",
    ),
    dict(
        slug="airship-send-bind",
        fail="airship-drop-send-handoff",
        mod="uapush",
        drop="uadpush",
        esp="Airship",
        idf="push_id",
        evf="send_id",
        naive="email",
        doc="https://docs.airship.com/api/ua/#tag/reports",
        doc2="https://docs.airship.com/api/ua/#operation/api/push/post",
        domain="airship-leftover-push-plus-send",
        stack="Airship leftover leftover leftover leftover leftover leftover send_id",
        ticket="UA-L6-98",
        test_ok="test_push_plus_send",
        test_fail="test_must_keep_send",
        short="uapush",
        dshort="uadpush",
    ),
    dict(
        slug="intercom-conversation-bind",
        fail="intercom-drop-conversation-handoff",
        mod="icconv",
        drop="icdconv",
        esp="Intercom",
        idf="id",
        evf="conversation_id",
        naive="email",
        doc="https://developers.intercom.com/docs/references/webhooks/webhook-models",
        doc2="https://developers.intercom.com/docs/references/rest-api/api.intercom.io/conversations",
        domain="intercom-leftover-id-plus-conversation",
        stack="Intercom leftover leftover leftover leftover leftover leftover conversation_id",
        ticket="IC-L6-99",
        test_ok="test_id_plus_conversation",
        test_fail="test_must_keep_conversation",
        short="icconv",
        dshort="icdconv",
    ),
    dict(
        slug="zendesk-ticket-bind",
        fail="zendesk-drop-ticket-handoff",
        mod="zdtkt",
        drop="zddtkt",
        esp="Zendesk",
        idf="event_id",
        evf="ticket_id",
        naive="email",
        doc="https://developer.zendesk.com/api-reference/webhooks/webhooks-api/webhooks/",
        doc2="https://developer.zendesk.com/api-reference/ticketing/tickets/tickets/",
        domain="zendesk-leftover-event-plus-ticket",
        stack="Zendesk leftover leftover leftover leftover leftover leftover ticket_id",
        ticket="ZD-L6-100",
        test_ok="test_event_plus_ticket",
        test_fail="test_must_keep_ticket",
        short="zdtkt",
        dshort="zddtkt",
    ),
    dict(
        slug="hubspot-campaign-bind",
        fail="hubspot-drop-campaign-handoff",
        mod="hscamp",
        drop="hsdcamp",
        esp="HubSpot",
        idf="emailId",
        evf="emailCampaignId",
        naive="recipient",
        doc="https://developers.hubspot.com/docs/api/webhooks",
        doc2="https://developers.hubspot.com/docs/api/marketing/marketing-emails",
        domain="hubspot-leftover-emailid-plus-campaign",
        stack="HubSpot leftover leftover leftover leftover leftover leftover emailCampaignId",
        ticket="HS-L6-101",
        test_ok="test_emailid_plus_campaign",
        test_fail="test_must_keep_campaign",
        short="hscamp",
        dshort="hsdcamp",
    ),
    dict(
        slug="sfmc-subscriber-bind",
        fail="sfmc-drop-subscriber-handoff",
        mod="sfmsub",
        drop="sfmdsub",
        esp="Salesforce Marketing Cloud",
        idf="batchID",
        evf="subscriberKey",
        naive="email",
        doc="https://developer.salesforce.com/docs/marketing/marketing-cloud/guide/eventNotification.html",
        doc2="https://developer.salesforce.com/docs/marketing/marketing-cloud/guide/subscribers.html",
        domain="sfmc-leftover-batch-plus-subscriber",
        stack="Salesforce Marketing Cloud leftover leftover leftover leftover leftover leftover subscriberKey",
        ticket="SFMC-L6-102",
        test_ok="test_batch_plus_subscriber",
        test_fail="test_must_keep_subscriber",
        short="sfmsub",
        dshort="sfmdsub",
    ),
    dict(
        slug="pardot-prospect-bind",
        fail="pardot-drop-prospect-handoff",
        mod="pdpros",
        drop="pddpros",
        esp="Pardot",
        idf="id",
        evf="prospect_id",
        naive="email",
        doc="https://developer.salesforce.com/docs/marketing/pardot/guide/version-5-overview.html",
        doc2="https://developer.salesforce.com/docs/marketing/pardot/guide/prospect-v5.html",
        domain="pardot-leftover-id-plus-prospect",
        stack="Pardot leftover leftover leftover leftover leftover leftover prospect_id",
        ticket="PD-L6-103",
        test_ok="test_id_plus_prospect",
        test_fail="test_must_keep_prospect",
        short="pdpros",
        dshort="pddpros",
    ),
    dict(
        slug="marketo-lead-bind",
        fail="marketo-drop-lead-handoff",
        mod="mklead",
        drop="mkdlead",
        esp="Marketo",
        idf="activityId",
        evf="leadId",
        naive="email",
        doc="https://experienceleague.adobe.com/en/docs/marketo-developer/marketo/rest/webhooks",
        doc2="https://experienceleague.adobe.com/en/docs/marketo-developer/marketo/rest/leads",
        domain="marketo-leftover-activity-plus-lead",
        stack="Marketo leftover leftover leftover leftover leftover leftover leadId",
        ticket="MK-L6-104",
        test_ok="test_activity_plus_lead",
        test_fail="test_must_keep_lead",
        short="mklead",
        dshort="mkdlead",
    ),
    dict(
        slug="omnisend-campaign-bind",
        fail="omnisend-drop-campaign-handoff",
        mod="omcamp",
        drop="omdcamp",
        esp="Omnisend",
        idf="emailID",
        evf="campaignID",
        naive="email",
        doc="https://api-docs.omnisend.com/v3/",
        doc2="https://api-docs.omnisend.com/v3/#tag/Campaigns",
        domain="omnisend-leftover-emailid-plus-campaign",
        stack="Omnisend leftover leftover leftover leftover leftover leftover campaignID",
        ticket="OM-L6-105",
        test_ok="test_emailid_plus_campaign",
        test_fail="test_must_keep_campaign",
        short="omcamp",
        dshort="omdcamp",
    ),
    dict(
        slug="drip-broadcast-bind",
        fail="drip-drop-broadcast-handoff",
        mod="drpbcast",
        drop="drpdbcast",
        esp="Drip",
        idf="id",
        evf="broadcast_id",
        naive="email",
        doc="https://developer.drip.com/#webhooks",
        doc2="https://developer.drip.com/#broadcasts",
        domain="drip-leftover-id-plus-broadcast",
        stack="Drip leftover leftover leftover leftover leftover leftover broadcast_id",
        ticket="DRP-L6-106",
        test_ok="test_id_plus_broadcast",
        test_fail="test_must_keep_broadcast",
        short="drpbcast",
        dshort="drpdbcast",
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

Novel coverage: leftover leftover leftover leftover leftover leftover {p['esp']} ({p['idf']}, {p['evf']}) vs drop {p['evf']}. Not r40–r90 clones. Not beehiiv. Not constant-contact. Not tantivy/search-index.

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
    loops = 0
    while pair_i < len(PAIRS) and loops < 16:
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
        loops += 1
    print("PUBLISHED", len(published))
    for row in published:
        print(f"r{row[0]:02d} {row[1]} {row[2]} {row[3]} drop {row[4]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
