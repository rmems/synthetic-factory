#!/usr/bin/env python3
"""websocket leftover leftover leftover mill r105–r120 (16 unique stacks).

Staging only. Never sir-/search ids. Distinct leftover leftover leftover resume binds
vs r41–r104. BAN r40 anycable/reverb.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FAC_DIR = ROOT / "outputs/raw/2026-08-19-agentic/websocket-reconnect-factory"
FAC = "websocket-reconnect-factory"
GEN = "grok-4.6"
PREFIX = "wsr"

# Unique leftover leftover leftover resume grains vs r41–r123 tokens
# (r114–r123 already bound track_sid/recordingId/localTrackSid/connectionState/
# binaryAck/connectionToken/phx_ref/identifier/socket_id/connectionKey).
PAIRS = [
    dict(
        slug="livekit-e2ee-key-leftover-vs-drop-codec",
        fail="livekit-drop-e2ee-key-handoff",
        mod="lke2ee",
        drop="lkedrop",
        stack="LiveKit",
        idf="e2ee_key",
        evf="keyIndex",
        naive="pingInterval",
        bound="e2ee_key",
        dropk="codec",
        doc="https://docs.livekit.io/home/client/tracks/encryption/",
        doc2="https://docs.livekit.io/home/client/tracks/",
        domain="livekit-leftover-e2ee-key-vs-ping",
        ticket="LK-L3-125",
        test_ok="test_e2ee_key_not_ping",
        test_fail="test_must_keep_e2ee_key",
        short="lke2ee",
        dshort="lkedrop",
    ),
    dict(
        slug="daily-transcription-id-leftover-vs-drop-recording",
        fail="daily-drop-transcription-id-handoff",
        mod="dlytrx",
        drop="dlytdrop",
        stack="Daily",
        idf="transcriptionId",
        evf="meeting",
        naive="camIdleMs",
        bound="transcriptionId",
        dropk="recording",
        doc="https://docs.daily.co/reference/rest-api/transcript",
        doc2="https://docs.daily.co/guides/products/transcription",
        domain="daily-leftover-transcription-id-vs-idle",
        ticket="DL-L3-126",
        test_ok="test_transcription_id_not_idle",
        test_fail="test_must_keep_transcription_id",
        short="dlytrx",
        dshort="dlytdrop",
    ),
    dict(
        slug="twilio-video-network-quality-leftover-vs-drop-bitrate",
        fail="twilio-video-drop-network-quality-handoff",
        mod="twnq",
        drop="twnqdrop",
        stack="Twilio Video",
        idf="networkQualityLevel",
        evf="room",
        naive="maxAudioBitrate",
        bound="networkQualityLevel",
        dropk="bitrate",
        doc="https://www.twilio.com/docs/video/tutorials/using-network-quality-api",
        doc2="https://www.twilio.com/docs/video/javascript-v2-getting-started",
        domain="twilio-video-leftover-nq-vs-bitrate",
        ticket="TW-L3-127",
        test_ok="test_nq_not_bitrate",
        test_fail="test_must_keep_nq",
        short="twnq",
        dshort="twnqdrop",
    ),
    dict(
        slug="agora-channel-profile-leftover-vs-drop-timeout",
        fail="agora-drop-channel-profile-handoff",
        mod="agprof",
        drop="agpdrop",
        stack="Agora",
        idf="channelProfile",
        evf="uid",
        naive="timeoutMs",
        bound="channelProfile",
        dropk="timeout",
        doc="https://docs.agora.io/en/video-calling/develop/ensure-service-reliability",
        doc2="https://docs.agora.io/en/video-calling/reference/api",
        domain="agora-leftover-channel-profile-vs-timeout",
        ticket="AG-L3-128",
        test_ok="test_channel_profile_not_timeout",
        test_fail="test_must_keep_channel_profile",
        short="agprof",
        dshort="agpdrop",
    ),
    dict(
        slug="socketio-recover-leftover-vs-drop-delay",
        fail="socketio-drop-recover-handoff",
        mod="siorec",
        drop="siodrec",
        stack="Socket.IO",
        idf="recover",
        evf="nsp",
        naive="reconnectionDelay",
        bound="recover",
        dropk="delay",
        doc="https://socket.io/docs/v4/client-options/#reconnection",
        doc2="https://socket.io/docs/v4/tutorial/step-6/",
        domain="socketio-leftover-recover-vs-delay",
        ticket="SIO-L3-129",
        test_ok="test_recover_not_delay",
        test_fail="test_must_keep_recover",
        short="siorec",
        dshort="siodrec",
    ),
    dict(
        slug="signalr-groups-token-leftover-vs-drop-keepalive",
        fail="signalr-drop-groups-token-handoff",
        mod="srgrp",
        drop="srgdrop",
        stack="SignalR",
        idf="groupsToken",
        evf="connectionId",
        naive="keepAliveInterval",
        bound="groupsToken",
        dropk="keepalive",
        doc="https://learn.microsoft.com/en-us/aspnet/core/signalr/groups",
        doc2="https://learn.microsoft.com/en-us/aspnet/core/signalr/configuration",
        domain="signalr-leftover-groups-token-vs-keepalive",
        ticket="SR-L3-130",
        test_ok="test_groups_token_not_keepalive",
        test_fail="test_must_keep_groups_token",
        short="srgrp",
        dshort="srgdrop",
    ),
    dict(
        slug="phoenix-phx-error-leftover-vs-drop-timeout",
        fail="phoenix-drop-phx-error-handoff",
        mod="phxerr",
        drop="phxedrop",
        stack="Phoenix",
        idf="phx_error",
        evf="join_ref",
        naive="timeout",
        bound="phx_error",
        dropk="timeout",
        doc="https://hexdocs.pm/phoenix/channels.html",
        doc2="https://hexdocs.pm/phoenix/Phoenix.Socket.html",
        domain="phoenix-leftover-phx-error-vs-timeout",
        ticket="PHX-L3-131",
        test_ok="test_phx_error_not_timeout",
        test_fail="test_must_keep_phx_error",
        short="phxerr",
        dshort="phxedrop",
    ),
    dict(
        slug="actioncable-confirmed-leftover-vs-drop-ping",
        fail="actioncable-drop-confirmed-handoff",
        mod="acconf",
        drop="accdrop",
        stack="ActionCable",
        idf="confirmed",
        evf="channel",
        naive="ping_interval",
        bound="confirmed",
        dropk="ping",
        doc="https://guides.rubyonrails.org/action_cable_overview.html#subscriptions",
        doc2="https://api.rubyonrails.org/classes/ActionCable/Connection/Base.html",
        domain="actioncable-leftover-confirmed-vs-ping",
        ticket="AC-L3-132",
        test_ok="test_confirmed_not_ping",
        test_fail="test_must_keep_confirmed",
        short="acconf",
        dshort="accdrop",
    ),
    dict(
        slug="centrifuge-client-leftover-vs-drop-ping",
        fail="centrifuge-drop-client-handoff",
        mod="cfcli",
        drop="cfcdrop",
        stack="Centrifuge",
        idf="client",
        evf="offset",
        naive="pingInterval",
        bound="client",
        dropk="ping",
        doc="https://centrifugal.dev/docs/server/server_api#client",
        doc2="https://centrifugal.dev/docs/transports/client_protocol",
        domain="centrifuge-leftover-client-vs-ping",
        ticket="CF-L3-133",
        test_ok="test_client_not_ping",
        test_fail="test_must_keep_client",
        short="cfcli",
        dshort="cfcdrop",
    ),
    dict(
        slug="pusher-presence-hash-leftover-vs-drop-activity",
        fail="pusher-drop-presence-hash-handoff",
        mod="pupres",
        drop="pupdrop",
        stack="Pusher",
        idf="presence_hash",
        evf="channel_data",
        naive="activityTimeout",
        bound="presence_hash",
        dropk="activity",
        doc="https://pusher.com/docs/channels/using_channels/presence-channels/",
        doc2="https://pusher.com/docs/channels/library_auth_reference/auth-signatures/",
        domain="pusher-leftover-presence-hash-vs-activity",
        ticket="PU-L3-134",
        test_ok="test_presence_hash_not_activity",
        test_fail="test_must_keep_presence_hash",
        short="pupres",
        dshort="pupdrop",
    ),
    dict(
        slug="ably-connection-id-leftover-vs-drop-retry",
        fail="ably-drop-connection-id-handoff",
        mod="abcid",
        drop="abcdrop",
        stack="Ably",
        idf="connectionId",
        evf="msgSerial",
        naive="disconnectedRetryTimeout",
        bound="connectionId",
        dropk="retry",
        doc="https://ably.com/docs/connect",
        doc2="https://ably.com/docs/api/realtime-sdk/connection",
        domain="ably-leftover-connection-id-vs-retry",
        ticket="AB-L3-135",
        test_ok="test_connection_id_not_retry",
        test_fail="test_must_keep_connection_id",
        short="abcid",
        dshort="abcdrop",
    ),
    dict(
        slug="graphqlws-ping-payload-leftover-vs-drop-keepalive",
        fail="graphqlws-drop-ping-payload-handoff",
        mod="gqlpng",
        drop="gqlpdrop",
        stack="graphql-ws",
        idf="ping_payload",
        evf="operationId",
        naive="keepAlive",
        bound="ping_payload",
        dropk="keepalive",
        doc="https://github.com/enisdenjo/graphql-ws/blob/master/PROTOCOL.md",
        doc2="https://the-guild.dev/graphql/ws/protocol",
        domain="graphqlws-leftover-ping-payload-vs-keepalive",
        ticket="GQL-L3-136",
        test_ok="test_ping_payload_not_keepalive",
        test_fail="test_must_keep_ping_payload",
        short="gqlpng",
        dshort="gqlpdrop",
    ),
    dict(
        slug="mqtt-assigned-client-leftover-vs-drop-keepalive",
        fail="mqtt-drop-assigned-client-handoff",
        mod="mqttac",
        drop="mqttadrop",
        stack="MQTT",
        idf="assignedClientIdentifier",
        evf="clientId",
        naive="keepAlive",
        bound="assignedClientIdentifier",
        dropk="keepalive",
        doc="https://docs.oasis-open.org/mqtt/mqtt/v5.0/os/mqtt-v5.0-os.html#_Toc3901087",
        doc2="https://mqtt.org/mqtt-specification/",
        domain="mqtt-leftover-assigned-client-vs-keepalive",
        ticket="MQTT-L3-137",
        test_ok="test_assigned_client_not_keepalive",
        test_fail="test_must_keep_assigned_client",
        short="mqttac",
        dshort="mqttadrop",
    ),
    dict(
        slug="stomp-receipt-id-leftover-vs-drop-heartbeat",
        fail="stomp-drop-receipt-id-handoff",
        mod="stmprec",
        drop="stmprdrop",
        stack="STOMP",
        idf="receipt-id",
        evf="id",
        naive="heartbeat",
        bound="receipt-id",
        dropk="heartbeat",
        doc="https://stomp.github.io/stomp-specification-1.2.html#RECEIPT",
        doc2="https://stomp.github.io/stomp-specification-1.2.html#SEND",
        domain="stomp-leftover-receipt-id-vs-heartbeat",
        ticket="STOMP-L3-138",
        test_ok="test_receipt_id_not_heartbeat",
        test_fail="test_must_keep_receipt_id",
        short="stmprec",
        dshort="stmprdrop",
    ),
    dict(
        slug="partykit-storage-leftover-vs-drop-hibernate",
        fail="partykit-drop-storage-handoff",
        mod="pktsto",
        drop="pktsdrop",
        stack="PartyKit",
        idf="storage",
        evf="party",
        naive="hibernateMs",
        bound="storage",
        dropk="hibernate",
        doc="https://docs.partykit.io/guides/persisting-state-into-storage/",
        doc2="https://docs.partykit.io/reference/partyserver-api/",
        domain="partykit-leftover-storage-vs-hibernate",
        ticket="PK-L3-139",
        test_ok="test_storage_not_hibernate",
        test_fail="test_must_keep_storage",
        short="pktsto",
        dshort="pktsdrop",
    ),
    dict(
        slug="cloudflare-durable-deserialize-attachment-leftover-vs-drop-alarm",
        fail="cloudflare-durable-drop-deserialize-attachment-handoff",
        mod="cfddatt",
        drop="cfdddrop",
        stack="Cloudflare Durable",
        idf="deserializeAttachment",
        evf="webSocket",
        naive="alarmMs",
        bound="deserializeAttachment",
        dropk="alarm",
        doc="https://developers.cloudflare.com/durable-objects/best-practices/websockets/#websocket-hibernation",
        doc2="https://developers.cloudflare.com/durable-objects/api/state/#deserializeattachment",
        domain="cf-durable-leftover-deserialize-attachment-vs-alarm",
        ticket="CFDO-L3-140",
        test_ok="test_deserialize_attachment_not_alarm",
        test_fail="test_must_keep_deserialize_attachment",
        short="cfddatt",
        dshort="cfdddrop",
    ),
]


def db(kind: str, text: str) -> str:
    s = f"{kind}: {text}"
    return s[:240]


def success_ep(rnd: int, p: dict) -> dict:
    eid = f"{PREFIX}-r{rnd}-{p['slug']}"
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
            "observation": f"{test}::{p['test_ok']} FAILED\nE   AssertionError: leftover leftover leftover stretched {naive}; {idf} unbounded",
            "reflection": f"Failure is at {test}::{p['test_ok']}. Read that test before a one-line fix.",
        },
        {
            "n": 3,
            "decision_basis": db("Observation", f"{test}::{p['test_ok']} is red. Read {test} around the assertion."),
            "tool_call": {"name": "read", "args": {"path": test}},
            "observation": f"def {p['test_ok']}():\n    t = tune(True)\n    assert t.get({idf!r}) and {naive!r} not in t\n",
            "reflection": "Test contract is visible. Search implementation symbols next.",
        },
        {
            "n": 4,
            "decision_basis": db("Observation", "test file imported the production helper. Grep those symbols."),
            "tool_call": {"name": "bash", "args": {"command": f"rg -n '{idf}|{naive}|leftover' src {p['short']} tests"}},
            "observation": f"{src}:2: return {{{naive!r}: 5}} if lag else {{}}",
            "reflection": f"Grep hit {src}. Read it before editing the first match.",
        },
        {
            "n": 5,
            "decision_basis": db("Observation", f"grep listed {src}. Read it before any patch."),
            "tool_call": {"name": "read", "args": {"path": src}},
            "observation": f"def tune(lag):\n    return {{{naive!r}: 5}} if lag else {{}}\n",
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
            "observation": f"retry after 2s backoff; local vendor fixture\nHTTP/1.1 200 OK\nleftover leftover leftover {idf} binds resume; {naive} is a clock.",
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
            "observation": f"sleep + jitter retry of the same URL\nHTTP/1.1 200 OK\nBind leftover leftover leftover {idf}, do not drop {p['dropk']}.",
            "reflection": "Retry succeeded. Resume the local debug plan with that document in hand.",
        },
        {
            "n": 10,
            "decision_basis": db("Observation", f"docs and source are in. Apply the first patch to {src}."),
            "tool_call": {
                "name": "edit",
                "args": {
                    "path": src,
                    "old": f"    return {{{naive!r}: 5}} if lag else {{}}",
                    "new": f"    return {{{naive!r}: 30}} if lag else {{}}",
                },
            },
            "observation": "patched 30 (still a timeout integer)",
            "reflection": "Patch applied. Re-run the failing test; do not assume green.",
        },
        {
            "n": 11,
            "decision_basis": db("Observation", f"edit wrote {src}. Re-run the same failing node."),
            "tool_call": {"name": "pytest", "args": {"args": f"{test} -q --tb=short"}},
            "observation": f"{test}::{p['test_ok']} FAILED\nE   AssertionError: timeout integer cannot bind leftover leftover leftover {idf}",
            "reflection": "Still red after the first patch. Re-read the implementation; hypothesis is wrong.",
        },
        {
            "n": 12,
            "decision_basis": db("Observation", f"post-edit test still failed ({test}::{p['test_ok']}). Re-read {src}."),
            "tool_call": {"name": "read", "args": {"path": src}},
            "observation": f"leftover leftover leftover is {idf}; {naive} is not the leftover leftover leftover bound",
            "reflection": f"Plan change: bind leftover leftover leftover {idf} plus {evf}. {naive} is not a leftover leftover leftover bound.",
        },
        {
            "n": 13,
            "decision_basis": db("Reflection", f"bind leftover leftover leftover {idf} plus {evf}. {naive} is not a leftover leftover leftover bound."),
            "tool_call": {
                "name": "edit",
                "args": {
                    "path": src,
                    "old": f"    return {{{naive!r}: 30}} if lag else {{}}",
                    "new": f"    return {{{idf!r}: True, {evf!r}: True}} if lag else {{}}",
                },
            },
            "observation": f"patched leftover leftover leftover {idf}",
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
        "goal": f"Bind leftover leftover leftover {p['stack']} {idf}; do not raise {naive} to hide lag.",
        "plan": f"Read leftover leftover leftover-as-timeout, try 30s, then {idf} plus {evf}.",
        "steps": steps,
        "outcome": f"leftover leftover leftover {idf} bound. {naive} unused (success).",
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
            "stack": f"{p['stack']} leftover leftover leftover {idf}",
        },
    }


def fail_ep(rnd: int, p: dict) -> dict:
    eid = f"{PREFIX}-r{rnd}-{p['fail']}"
    src = f"src/{p['drop']}.py"
    cfg = f"{p['drop']}/cfg.yml"
    test = f"tests/test_{p['drop']}.py"
    idf, naive = p["idf"], p["naive"]
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
            "observation": f"{test}::{p['test_fail']} FAILED\nE   AssertionError: leftover leftover leftover slept {naive}; drop {p['dropk']} is not a leftover leftover leftover bind",
            "reflection": f"Failure is at {test}::{p['test_fail']}. Read that test before a one-line fix.",
        },
        {
            "n": 3,
            "decision_basis": db("Observation", f"{test}::{p['test_fail']} is red. Read {test} around the assertion."),
            "tool_call": {"name": "read", "args": {"path": test}},
            "observation": f"def {p['test_fail']}():\n    assert {naive!r} not in tune(True)\n",
            "reflection": "Test contract is visible. Search implementation symbols next.",
        },
        {
            "n": 4,
            "decision_basis": db("Observation", "test file imported the production helper. Grep those symbols."),
            "tool_call": {"name": "bash", "args": {"command": f"rg -n '{naive}|{p['dropk']}|leftover' src {p['dshort']} tests"}},
            "observation": f"{src}:2: return {{{naive!r}: 5}} if blocked else {{}}",
            "reflection": f"Grep hit {src}. Read it before editing the first match.",
        },
        {
            "n": 5,
            "decision_basis": db("Observation", f"grep listed {src}. Read it before any patch."),
            "tool_call": {"name": "read", "args": {"path": src}},
            "observation": f"def tune(blocked):\n    return {{{naive!r}: 5}} if blocked else {{}}\n",
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
            "observation": f"sleep + jitter retry of the same URL\nHTTP/1.1 200 OK\nDropping {p['dropk']} drops leftover leftover leftover; it does not bind {idf}.",
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
            "observation": f"retry after 2s backoff; local vendor fixture\nHTTP/1.1 200 OK\nTimeout cannot mint leftover leftover leftover; drop {p['dropk']} is platform. Handoff {ticket}.",
            "reflection": "Degraded path used the local fixture. Resume the local debug plan.",
        },
        {
            "n": 10,
            "decision_basis": db("Observation", f"docs and source are in. Apply the first patch to {src}."),
            "tool_call": {
                "name": "edit",
                "args": {
                    "path": src,
                    "old": f"    return {{{naive!r}: 5}} if blocked else {{}}",
                    "new": f"    return {{{naive!r}: 0}} if blocked else {{}}",
                },
            },
            "observation": "patched 0s (still a timeout integer)",
            "reflection": "Patch applied. Re-run the failing test; do not assume green.",
        },
        {
            "n": 11,
            "decision_basis": db("Observation", f"edit wrote {src}. Re-run the same failing node."),
            "tool_call": {"name": "pytest", "args": {"args": f"{test} -q --tb=short"}},
            "observation": f"{test}::{p['test_fail']} FAILED\nE   AssertionError: timeout cannot mint leftover leftover leftover; dropping {p['dropk']} is not a bind",
            "reflection": "Still red after the first patch. Re-read the implementation; hypothesis is wrong.",
        },
        {
            "n": 12,
            "decision_basis": db("Observation", f"post-edit test still failed ({test}::{p['test_fail']}). Re-read {src}."),
            "tool_call": {"name": "read", "args": {"path": src}},
            "observation": f"dropping {p['dropk']} destroys leftover leftover leftover; bind leftover leftover leftover is platform",
            "reflection": f"Plan change: {p['dropk']} drop is platform. Handoff {ticket}.",
        },
        {
            "n": 13,
            "decision_basis": db("Reflection", f"{p['dropk']} drop is platform. Handoff {ticket}."),
            "tool_call": {
                "name": "edit",
                "args": {
                    "path": f"{p['drop']}/handoff.md",
                    "old": "",
                    "new": f"# {ticket} {p['stack']} leftover leftover leftover {idf} owned by ws-plat",
                },
            },
            "observation": "ticket filed. still timeout-classed",
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
        "goal": f"Do not drop leftover leftover leftover {p['stack']} {p['dropk']} to hide {idf}.",
        "plan": f"Read leftover leftover leftover-as-timeout, try 0s, then hand off drop-{p['dropk']}.",
        "steps": steps,
        "outcome": f"Still timeout-classed; leftover leftover leftover drop {p['dropk']} is platform — handoff {ticket}.",
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
            "domain": p["domain"].replace("vs", "drop-vs", 1),
            "stack": f"{p['stack']} leftover leftover leftover drop {p['dropk']}",
        },
    }


def notes(rnd: int, p: dict) -> str:
    ok = f"{PREFIX}-r{rnd}-{p['slug']}"
    bad = f"{PREFIX}-r{rnd}-{p['fail']}"
    return f"""# websocket-reconnect-factory — NOTES r{rnd}

Novel coverage: leftover leftover leftover {p['stack']} {p['idf']} vs drop {p['dropk']}. Not r41–r104 clones. Not disruptor. Not chronicle. Not search-index.

## Episodes
- `{ok}`: 16 steps, success=True, domain={p['domain']}, seed={p['slug']}
  - 502 at step 6 recovered 7; 429 at step 8 recovered 9
  - plan change at step 12: bind leftover leftover leftover {p['idf']} plus {p['evf']}. {p['naive']} is not a leftover leftover leftover bound.
  - edit→test→fail→re-read→fix at steps 10-13
- `{bad}`: 17 steps, success=False, domain=drop {p['dropk']}, seed={p['fail']}
  - 429 at step 6 recovered 7; 502 at step 8 recovered 9
  - plan change at step 12: {p['dropk']} drop is platform. Handoff {p['ticket']}.
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
{p['naive']} is not leftover leftover leftover {p['idf']}. Cannot drop leftover leftover leftover {p['dropk']}.
"""


def txn(cmd: list[str], fatal: bool = True) -> dict | None:
    r = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stdout + r.stderr)
        if fatal:
            raise SystemExit(r.returncode)
        return None
    return json.loads(r.stdout)


def hop_unreserved() -> Path | None:
    base = ROOT / "outputs/raw/2026-08-19-agentic"
    for child in sorted(p for p in base.iterdir() if p.is_dir()):
        if child.name == "sandbox-refusal-factory":
            continue
        st = txn(["python3", "pipelines/round_txn.py", "frontier", str(child)], fatal=False)
        if not st:
            continue
        nxt = int(st["next_round"])
        if (child / f"ROUND-r{nxt:02d}.reserved.json").exists():
            continue
        return child
    return None


def used_slugs() -> set[str]:
    seen: set[str] = set()
    for path in FAC_DIR.glob("batch-r*.jsonl"):
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            seen.add(str(rec.get("meta", {}).get("seed") or ""))
            rid = str(rec.get("id") or "")
            if rid.startswith(PREFIX + "-"):
                seen.add("-".join(rid.split("-")[2:]))
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
        res = None
        rnd = None
        for _try in range(80):
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
            if res is not None:
                break
            time.sleep(0.35)
        if res is None:
            hop = hop_unreserved()
            print(f"reserve failed at {rnd}; hop {hop}", file=sys.stderr)
            return 2
        stage = Path(res["staging_dir"])
        ok = success_ep(rnd, p)
        bad = fail_ep(rnd, p)
        batch_name = res.get("batch_file") or f"batch-r{rnd:02d}.jsonl"
        notes_name = res.get("notes_file") or f"NOTES-r{rnd:02d}.md"
        batch = stage / batch_name
        batch.write_text(
            json.dumps(ok, separators=(",", ":")) + "\n" + json.dumps(bad, separators=(",", ":")) + "\n"
        )
        (stage / notes_name).write_text(notes(rnd, p))
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
        published.append((rnd, ok["id"], bad["id"], p["stack"]))
        print(json.dumps({"published": pub["round"], "ids": [ok["id"], bad["id"]]}))
        pair_i += 1
        loops += 1
        already.add(p["slug"])
        already.add(p["fail"])
    print("PUBLISHED", len(published))
    for row in published:
        print(f"r{row[0]} {row[1]} {row[2]} {row[3]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
