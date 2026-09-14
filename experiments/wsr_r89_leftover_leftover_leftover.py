#!/usr/bin/env python3
"""websocket leftover leftover leftover mill hop: queue-backpressure r78 reserved.

Staging only. Never sir-/search ids. Distinct leftover leftover leftover resume binds.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FAC_DIR = ROOT / "outputs/raw/2026-08-19-agentic/websocket-reconnect-factory"
FAC = "websocket-reconnect-factory"
GEN = "grok-4.6"
PREFIX = "wsr"

# Unused leftover leftover leftover resume grains vs r57–r88 (socket.io pid, sockjs,
# signalr negotiate, phoenix reply, actioncable signed-stream, centrifuge offset,
# pusher activity, ably recovery, nchan last-event, graphql-ws subscribe, mqtt
# session, stomp subscription, socketcluster cid, partykit, livekit, webrtc ice,
# daily, twilio, agora, ack-id, invocation, join-push, stream-from, epoch,
# channel-data, ably serial, graphqlws sub, mqtt packet, stomp dest, partykit
# hibernation, cf durable alarm). BAN disruptor/chronicle/search clones.
PAIRS = [
    dict(
        slug="mercure-last-event-id-leftover-vs-drop-topic",
        fail="mercure-drop-last-event-id-handoff",
        mod="mceid",
        drop="mcdrop",
        stack="Mercure",
        idf="lastEventId",
        evf="topic",
        naive="retry_ms",
        bound="lastEventId",
        dropk="topic",
        doc="https://www.rfc-editor.org/rfc/rfc8872.html",
        doc2="https://mercure.rocks/spec",
        domain="mercure-leftover-lasteventid-vs-retry",
        ticket="MC-L3-89",
        test_ok="test_lasteventid_not_retry",
        test_fail="test_must_keep_lasteventid",
        short="mceid",
        dshort="mcdrop",
    ),
    dict(
        slug="sse-last-event-id-leftover-vs-drop-retry",
        fail="sse-drop-last-event-id-handoff",
        mod="sseleid",
        drop="ssedrop",
        stack="SSE",
        idf="Last-Event-ID",
        evf="id",
        naive="retry",
        bound="Last-Event-ID",
        dropk="retry",
        doc="https://html.spec.whatwg.org/multipage/server-sent-events.html",
        doc2="https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events",
        domain="sse-leftover-last-event-id-vs-retry",
        ticket="SSE-L3-90",
        test_ok="test_last_event_id_not_retry",
        test_fail="test_must_keep_last_event_id",
        short="sseleid",
        dshort="ssedrop",
    ),
    dict(
        slug="rsocket-stream-id-leftover-vs-drop-lease",
        fail="rsocket-drop-stream-id-handoff",
        mod="rssid",
        drop="rsdrop",
        stack="RSocket",
        idf="streamId",
        evf="resumeToken",
        naive="keepalive_ms",
        bound="streamId",
        dropk="lease",
        doc="https://rsocket.io/about/protocol",
        doc2="https://rsocket.io/guides/rsocket-js",
        domain="rsocket-leftover-streamid-vs-keepalive",
        ticket="RS-L3-91",
        test_ok="test_streamid_not_keepalive",
        test_fail="test_must_keep_streamid",
        short="rssid",
        dshort="rsdrop",
    ),
    dict(
        slug="grpc-bidi-stream-id-leftover-vs-drop-call",
        fail="grpc-drop-stream-id-handoff",
        mod="grpcsid",
        drop="grpcdrop",
        stack="gRPC-bidi",
        idf="stream_id",
        evf="grpc-previous-rpc-attempts",
        naive="deadline_s",
        bound="stream_id",
        dropk="call",
        doc="https://grpc.io/docs/guides/retry/",
        doc2="https://github.com/grpc/proposal/blob/master/A6-client-retries.md",
        domain="grpc-leftover-stream-id-vs-deadline",
        ticket="GR-L3-92",
        test_ok="test_stream_id_not_deadline",
        test_fail="test_must_keep_stream_id",
        short="grpcsid",
        dshort="grpcdrop",
    ),
    dict(
        slug="engineio-sid-leftover-vs-drop-ping",
        fail="engineio-drop-sid-handoff",
        mod="eiosid",
        drop="eiodrop",
        stack="Engine.IO",
        idf="sid",
        evf="pingInterval",
        naive="pingTimeout",
        bound="sid",
        dropk="pingTimeout",
        doc="https://socket.io/docs/v4/engine-io-protocol/",
        doc2="https://github.com/socketio/engine.io-protocol",
        domain="engineio-leftover-sid-vs-pingtimeout",
        ticket="EIO-L3-93",
        test_ok="test_sid_not_pingtimeout",
        test_fail="test_must_keep_sid",
        short="eiosid",
        dshort="eiodrop",
    ),
    dict(
        slug="faye-client-id-leftover-vs-drop-channel",
        fail="faye-drop-client-id-handoff",
        mod="faycid",
        drop="faydrop",
        stack="Faye",
        idf="clientId",
        evf="channel",
        naive="interval",
        bound="clientId",
        dropk="channel",
        doc="https://faye.jcoglan.com/architecture.html",
        doc2="https://faye.jcoglan.com/browser.html",
        domain="faye-leftover-clientid-vs-interval",
        ticket="FY-L3-94",
        test_ok="test_clientid_not_interval",
        test_fail="test_must_keep_clientid",
        short="faycid",
        dshort="faydrop",
    ),
    dict(
        slug="channels-channel-name-leftover-vs-drop-group",
        fail="channels-drop-channel-name-handoff",
        mod="djch",
        drop="djdrop",
        stack="Django-channels",
        idf="channel_name",
        evf="group",
        naive="timeout_s",
        bound="channel_name",
        dropk="group",
        doc="https://channels.readthedocs.io/en/latest/topics/channel_layers.html",
        doc2="https://channels.readthedocs.io/en/latest/topics/consumers.html",
        domain="channels-leftover-channel-name-vs-timeout",
        ticket="DJ-L3-95",
        test_ok="test_channel_name_not_timeout",
        test_fail="test_must_keep_channel_name",
        short="djch",
        dshort="djdrop",
    ),
    dict(
        slug="starlette-websocket-state-leftover-vs-drop-scope",
        fail="starlette-drop-websocket-state-handoff",
        mod="stws",
        drop="stdrop",
        stack="Starlette",
        idf="websocket.state",
        evf="scope",
        naive="timeout",
        bound="websocket.state",
        dropk="scope",
        doc="https://www.starlette.io/websockets/",
        doc2="https://www.starlette.io/requests/",
        domain="starlette-leftover-ws-state-vs-timeout",
        ticket="ST-L3-96",
        test_ok="test_ws_state_not_timeout",
        test_fail="test_must_keep_ws_state",
        short="stws",
        dshort="stdrop",
    ),
    dict(
        slug="fastapi-websocket-state-leftover-vs-drop-dep",
        fail="fastapi-drop-websocket-state-handoff",
        mod="faws",
        drop="fadrop",
        stack="FastAPI",
        idf="websocket.state",
        evf="dependency",
        naive="timeout",
        bound="websocket.state",
        dropk="dependency",
        doc="https://fastapi.tiangolo.com/advanced/websockets/",
        doc2="https://fastapi.tiangolo.com/advanced/using-request-directly/",
        domain="fastapi-leftover-ws-state-vs-timeout",
        ticket="FA-L3-97",
        test_ok="test_fastapi_state_not_timeout",
        test_fail="test_must_keep_fastapi_state",
        short="faws",
        dshort="fadrop",
    ),
    dict(
        slug="caddy-ws-subprotocol-leftover-vs-drop-route",
        fail="caddy-drop-ws-subprotocol-handoff",
        mod="cdws",
        drop="cddrop",
        stack="Caddy",
        idf="Sec-WebSocket-Protocol",
        evf="route",
        naive="idle_timeout",
        bound="Sec-WebSocket-Protocol",
        dropk="route",
        doc="https://caddyserver.com/docs/caddyfile/directives/reverse_proxy",
        doc2="https://caddyserver.com/docs/modules/http.reverse_proxy",
        domain="caddy-leftover-subprotocol-vs-idle",
        ticket="CD-L3-98",
        test_ok="test_subprotocol_not_idle",
        test_fail="test_must_keep_subprotocol",
        short="cdws",
        dshort="cddrop",
    ),
    dict(
        slug="haproxy-ws-stick-table-leftover-vs-drop-backend",
        fail="haproxy-drop-ws-stick-table-handoff",
        mod="haws",
        drop="hadrop",
        stack="HAProxy",
        idf="stick-table",
        evf="backend",
        naive="timeout_tunnel",
        bound="stick-table",
        dropk="backend",
        doc="https://www.haproxy.com/documentation/haproxy-configuration-manual/latest/",
        doc2="https://docs.haproxy.org/2.8/configuration.html",
        domain="haproxy-leftover-stick-table-vs-tunnel",
        ticket="HA-L3-99",
        test_ok="test_stick_table_not_tunnel",
        test_fail="test_must_keep_stick_table",
        short="haws",
        dshort="hadrop",
    ),
    dict(
        slug="traefik-ws-sticky-leftover-vs-drop-service",
        fail="traefik-drop-ws-sticky-handoff",
        mod="trws",
        drop="trdrop",
        stack="Traefik",
        idf="sticky.cookie",
        evf="service",
        naive="idleTimeout",
        bound="sticky.cookie",
        dropk="service",
        doc="https://doc.traefik.io/traefik/routing/services/",
        doc2="https://doc.traefik.io/traefik/middlewares/http/retry/",
        domain="traefik-leftover-sticky-vs-idle",
        ticket="TR-L3-100",
        test_ok="test_sticky_not_idle",
        test_fail="test_must_keep_sticky",
        short="trws",
        dshort="trdrop",
    ),
    dict(
        slug="kong-ws-upstream-hash-leftover-vs-drop-route",
        fail="kong-drop-ws-upstream-hash-handoff",
        mod="kgws",
        drop="kgdrop",
        stack="Kong",
        idf="hash_on",
        evf="route",
        naive="timeouts.connect",
        bound="hash_on",
        dropk="route",
        doc="https://docs.konghq.com/gateway/latest/reference/configuration/",
        doc2="https://docs.konghq.com/gateway/latest/production/loadbalancing/",
        domain="kong-leftover-hash-on-vs-connect",
        ticket="KG-L3-101",
        test_ok="test_hash_on_not_connect",
        test_fail="test_must_keep_hash_on",
        short="kgws",
        dshort="kgdrop",
    ),
    dict(
        slug="envoy-ws-route-hash-leftover-vs-drop-cluster",
        fail="envoy-drop-ws-route-hash-handoff",
        mod="envws",
        drop="envdrop",
        stack="Envoy",
        idf="hash_policy",
        evf="cluster",
        naive="idle_timeout",
        bound="hash_policy",
        dropk="cluster",
        doc="https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/http/http_connection_management",
        doc2="https://www.envoyproxy.io/docs/envoy/latest/api-v3/config/route/v3/route_components.proto",
        domain="envoy-leftover-hash-policy-vs-idle",
        ticket="EN-L3-102",
        test_ok="test_hash_policy_not_idle",
        test_fail="test_must_keep_hash_policy",
        short="envws",
        dshort="envdrop",
    ),
    dict(
        slug="istio-ws-destination-leftover-vs-drop-vs",
        fail="istio-drop-ws-destination-handoff",
        mod="istws",
        drop="istdrop",
        stack="Istio",
        idf="destination.host",
        evf="virtualservice",
        naive="idleTimeout",
        bound="destination.host",
        dropk="virtualservice",
        doc="https://istio.io/latest/docs/reference/config/networking/destination-rule/",
        doc2="https://istio.io/latest/docs/reference/config/networking/virtual-service/",
        domain="istio-leftover-destination-host-vs-idle",
        ticket="IS-L3-103",
        test_ok="test_destination_not_idle",
        test_fail="test_must_keep_destination",
        short="istws",
        dshort="istdrop",
    ),
    dict(
        slug="nats-ws-inbox-leftover-vs-drop-sub",
        fail="nats-ws-drop-inbox-handoff",
        mod="natws",
        drop="natdrop",
        stack="NATS-WS",
        idf="_INBOX",
        evf="sid",
        naive="pingInterval",
        bound="_INBOX",
        dropk="sid",
        doc="https://docs.nats.io/using-nats/developer/connecting/ws",
        doc2="https://docs.nats.io/nats-concepts/core-nats/reqreply",
        domain="nats-ws-leftover-inbox-vs-ping",
        ticket="NW-L3-104",
        test_ok="test_inbox_not_ping",
        test_fail="test_must_keep_inbox",
        short="natws",
        dshort="natdrop",
    ),
]


def db(kind: str, text: str) -> str:
    s = f"{kind}: {text}"
    return s[:240]


def success_ep(rnd: int, p: dict) -> dict:
    eid = f"{PREFIX}-r{rnd:02d}-{p['slug']}"
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
    eid = f"{PREFIX}-r{rnd:02d}-{p['fail']}"
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
            "domain": p["domain"].replace("vs", "drop-vs"),
            "stack": f"{p['stack']} leftover leftover leftover drop {p['dropk']}",
        },
    }


def notes(rnd: int, p: dict) -> str:
    ok = f"{PREFIX}-r{rnd:02d}-{p['slug']}"
    bad = f"{PREFIX}-r{rnd:02d}-{p['fail']}"
    return f"""# websocket-reconnect-factory — NOTES r{rnd:02d}

Novel coverage: leftover leftover leftover {p['stack']} {p['idf']} vs drop {p['dropk']}. Not r57–r88 clones. Not disruptor. Not chronicle. Not search-index.

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
            return 2
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
        published.append((rnd, ok["id"], bad["id"], p["stack"]))
        print(json.dumps({"published": pub["round"], "ids": [ok["id"], bad["id"]]}))
        pair_i += 1
        loops += 1
        already.add(p["slug"])
        already.add(p["fail"])
    print("PUBLISHED", len(published))
    for row in published:
        print(f"r{row[0]:02d} {row[1]} {row[2]} {row[3]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
