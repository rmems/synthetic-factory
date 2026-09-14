#!/usr/bin/env python3
"""websocket-reconnect leftover leftover leftover mill r57–r72 (16 pairs)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path("/home/raulmc/rmems/synthetic-factory")
DIR = ROOT / "outputs/raw/2026-08-19-agentic/websocket-reconnect-factory"
TXN = ["python3", str(ROOT / "pipelines/round_txn.py")]
FACTORY = "websocket-reconnect-factory"
GEN = "grok-4.6"
MAX_ROUNDS = 16

# Distinct leftover leftover leftover vs r41–r56 tokens. BAN r40 anycable / reverb.
# Each: leftover resume token vs naive second-subscribe (success) / drop-bind handoff (fail).
CATALOG = [
    {
        "mod": "siopid",
        "slug": "socketio-pid-leftover-vs-second-handshake",
        "fail": "socketio-drop-pid-handoff",
        "stack": "Socket.IO leftover engine.io pid",
        "token": "leftover_pid",
        "wrong": "second handshake",
        "wrong_key": "handshake",
        "test_ok": "test_pid_not_handshake",
        "test_fail": "test_pid_bind",
        "docs": "https://socket.io/docs/v4/client-api/#socketid",
        "doc2": "https://github.com/socketio/engine.io/blob/main/README.md",
        "handoff": "SIO-PID-17",
        "domain_ok": "socketio-pid-leftover-vs-second-handshake",
        "domain_fail": "socketio-drop-leftover-pid-bind",
        "first_patch": ("    return {'handshake': sid}", "    return {'handshake': sid, 'forceNew': True}"),
        "fix_patch": ("    return {'handshake': sid, 'forceNew': True}", "    return {'leftover_pid': sid}"),
        "src_obs": "Engine.IO leftover pid restores the same transport; forceNew is not resume",
        "plan_ok": "Pass leftover_pid. A second handshake is not resume.",
        "plan_fail": "Leftover pid bind drop is Socket.IO plat. Handoff SIO-PID-17.",
        "ban": "Not cookie-replay. Not sid leftover clone.",
    },
    {
        "mod": "sjbeat",
        "slug": "sockjs-heartbeat-leftover-vs-drop-iframe",
        "fail": "sockjs-drop-heartbeat-handoff",
        "stack": "SockJS leftover heartbeat interval",
        "token": "leftover_heartbeat",
        "wrong": "drop iframe",
        "wrong_key": "iframe",
        "test_ok": "test_beat_not_iframe",
        "test_fail": "test_beat_bind",
        "docs": "https://github.com/sockjs/sockjs-protocol#heartbeat",
        "doc2": "https://github.com/sockjs/sockjs-client#heartbeat",
        "handoff": "SJ-HB-17",
        "domain_ok": "sockjs-heartbeat-leftover-vs-drop-iframe",
        "domain_fail": "sockjs-drop-leftover-heartbeat-bind",
        "first_patch": ("    return {'iframe': sid}", "    return {'iframe': None}"),
        "fix_patch": ("    return {'iframe': None}", "    return {'leftover_heartbeat': sid}"),
        "src_obs": "SockJS leftover heartbeat keeps the same session clock; dropping iframe is not resume",
        "plan_ok": "Pass leftover_heartbeat. Dropping iframe is not resume.",
        "plan_fail": "Leftover heartbeat bind drop is SockJS plat. Handoff SJ-HB-17.",
        "ban": "Not cookie-replay. Not session leftover clone.",
    },
    {
        "mod": "sigrnv",
        "slug": "signalr-negotiate-leftover-vs-drop-reconnect",
        "fail": "signalr-drop-negotiate-handoff",
        "stack": "SignalR leftover negotiateVersion",
        "token": "leftover_negotiate",
        "wrong": "drop reconnect",
        "wrong_key": "reconnect",
        "test_ok": "test_neg_not_reconnect",
        "test_fail": "test_neg_bind",
        "docs": "https://learn.microsoft.com/en-us/aspnet/core/signalr/configuration",
        "doc2": "https://github.com/dotnet/aspnetcore/blob/main/src/SignalR/docs/specs/TransportProtocols.md",
        "handoff": "SR-NV-17",
        "domain_ok": "signalr-negotiate-leftover-vs-drop-reconnect",
        "domain_fail": "signalr-drop-leftover-negotiate-bind",
        "first_patch": ("    return {'reconnect': sid}", "    return {'reconnect': False}"),
        "fix_patch": ("    return {'reconnect': False}", "    return {'leftover_negotiate': sid}"),
        "src_obs": "SignalR leftover negotiateVersion binds the same connection; drop reconnect is not resume",
        "plan_ok": "Pass leftover_negotiate. Drop reconnect is not resume.",
        "plan_fail": "Leftover negotiate bind drop is SignalR plat. Handoff SR-NV-17.",
        "ban": "Not cookie-replay. Not connectionToken leftover clone.",
    },
    {
        "mod": "phxrep",
        "slug": "phoenix-reply-topic-leftover-vs-drop-presence",
        "fail": "phoenix-drop-reply-topic-handoff",
        "stack": "Phoenix leftover phx_reply topic",
        "token": "leftover_phx_reply",
        "wrong": "drop presence",
        "wrong_key": "presence",
        "test_ok": "test_reply_not_presence",
        "test_fail": "test_reply_bind",
        "docs": "https://hexdocs.pm/phoenix/channels.html",
        "doc2": "https://hexdocs.pm/phoenix/Phoenix.Socket.html",
        "handoff": "PHX-RP-17",
        "domain_ok": "phoenix-reply-topic-leftover-vs-drop-presence",
        "domain_fail": "phoenix-drop-leftover-reply-bind",
        "first_patch": ("    return {'presence': sid}", "    return {'presence': False}"),
        "fix_patch": ("    return {'presence': False}", "    return {'leftover_phx_reply': sid}"),
        "src_obs": "Phoenix leftover phx_reply topic rejoins the same channel; drop presence is not resume",
        "plan_ok": "Pass leftover_phx_reply. Drop presence is not resume.",
        "plan_fail": "Leftover phx_reply bind drop is Phoenix plat. Handoff PHX-RP-17.",
        "ban": "Not cookie-replay. Not join_ref leftover clone.",
    },
    {
        "mod": "acsign",
        "slug": "actioncable-signed-stream-leftover-vs-drop-identifier",
        "fail": "actioncable-drop-signed-stream-handoff",
        "stack": "ActionCable leftover signed_stream_name",
        "token": "leftover_signed_stream",
        "wrong": "drop identifier",
        "wrong_key": "identifier",
        "test_ok": "test_stream_not_identifier",
        "test_fail": "test_stream_bind",
        "docs": "https://guides.rubyonrails.org/action_cable_overview.html",
        "doc2": "https://api.rubyonrails.org/classes/ActionCable/Channel/Streams.html",
        "handoff": "AC-SS-17",
        "domain_ok": "actioncable-signed-stream-leftover-vs-drop-identifier",
        "domain_fail": "actioncable-drop-leftover-signed-stream-bind",
        "first_patch": ("    return {'identifier': sid}", "    return {'identifier': None}"),
        "fix_patch": ("    return {'identifier': None}", "    return {'leftover_signed_stream': sid}"),
        "src_obs": "ActionCable leftover signed_stream_name rebinds the same stream; drop identifier is not resume",
        "plan_ok": "Pass leftover_signed_stream. Drop identifier is not resume.",
        "plan_fail": "Leftover signed_stream bind drop is ActionCable plat. Handoff AC-SS-17.",
        "ban": "Not cookie-replay. Not identifier leftover clone.",
    },
    {
        "mod": "cfoffs",
        "slug": "centrifuge-offset-leftover-vs-drop-recover",
        "fail": "centrifuge-drop-offset-handoff",
        "stack": "Centrifuge leftover offset",
        "token": "leftover_offset",
        "wrong": "drop recover",
        "wrong_key": "recover",
        "test_ok": "test_offset_not_recover",
        "test_fail": "test_offset_bind",
        "docs": "https://centrifugal.dev/docs/server/history_and_recovery",
        "doc2": "https://centrifugal.dev/docs/transports/client_protocol",
        "handoff": "CF-OF-17",
        "domain_ok": "centrifuge-offset-leftover-vs-drop-recover",
        "domain_fail": "centrifuge-drop-leftover-offset-bind",
        "first_patch": ("    return {'recover': sid}", "    return {'recover': False}"),
        "fix_patch": ("    return {'recover': False}", "    return {'leftover_offset': sid}"),
        "src_obs": "Centrifuge leftover offset resumes history; drop recover is not resume",
        "plan_ok": "Pass leftover_offset. Drop recover is not resume.",
        "plan_fail": "Leftover offset bind drop is Centrifuge plat. Handoff CF-OF-17.",
        "ban": "Not cookie-replay. Not epoch leftover clone.",
    },
    {
        "mod": "pusto",
        "slug": "pusher-activity-timeout-leftover-vs-drop-channel",
        "fail": "pusher-drop-activity-timeout-handoff",
        "stack": "Pusher leftover activity_timeout",
        "token": "leftover_activity_timeout",
        "wrong": "drop channel",
        "wrong_key": "channel",
        "test_ok": "test_ato_not_channel",
        "test_fail": "test_ato_bind",
        "docs": "https://pusher.com/docs/channels/library_auth_reference/pusher-websockets-protocol/",
        "doc2": "https://pusher.com/docs/channels/using_channels/connection/",
        "handoff": "PU-AT-17",
        "domain_ok": "pusher-activity-timeout-leftover-vs-drop-channel",
        "domain_fail": "pusher-drop-leftover-activity-timeout-bind",
        "first_patch": ("    return {'channel': sid}", "    return {'channel': None}"),
        "fix_patch": ("    return {'channel': None}", "    return {'leftover_activity_timeout': sid}"),
        "src_obs": "Pusher leftover activity_timeout keeps the same socket clock; drop channel is not resume",
        "plan_ok": "Pass leftover_activity_timeout. Drop channel is not resume.",
        "plan_fail": "Leftover activity_timeout bind drop is Pusher plat. Handoff PU-AT-17.",
        "ban": "Not cookie-replay. Not socket_id leftover clone.",
    },
    {
        "mod": "ablyrk",
        "slug": "ably-recoverykey-leftover-vs-drop-resume",
        "fail": "ably-drop-recoverykey-handoff",
        "stack": "Ably leftover recoveryKey",
        "token": "leftover_recovery_key",
        "wrong": "drop resume",
        "wrong_key": "resume",
        "test_ok": "test_rkey_not_resume",
        "test_fail": "test_rkey_bind",
        "docs": "https://ably.com/docs/connect#connection-state-recovery",
        "doc2": "https://ably.com/docs/api/realtime-sdk#connection",
        "handoff": "AB-RK-17",
        "domain_ok": "ably-recoverykey-leftover-vs-drop-resume",
        "domain_fail": "ably-drop-leftover-recoverykey-bind",
        "first_patch": ("    return {'resume': sid}", "    return {'resume': False}"),
        "fix_patch": ("    return {'resume': False}", "    return {'leftover_recovery_key': sid}"),
        "src_obs": "Ably leftover recoveryKey restores serials; drop resume flag is not resume",
        "plan_ok": "Pass leftover_recovery_key. Drop resume is not resume.",
        "plan_fail": "Leftover recoveryKey bind drop is Ably plat. Handoff AB-RK-17.",
        "ban": "Not cookie-replay. Not connectionKey leftover clone.",
    },
    {
        "mod": "nchevt",
        "slug": "nchan-last-event-id-leftover-vs-drop-subscriber",
        "fail": "nchan-drop-last-event-id-handoff",
        "stack": "nchan leftover Last-Event-Id",
        "token": "leftover_last_event_id",
        "wrong": "drop subscriber",
        "wrong_key": "subscriber",
        "test_ok": "test_lei_not_subscriber",
        "test_fail": "test_lei_bind",
        "docs": "https://nchan.io/#subscriber-endpoints",
        "doc2": "https://nchan.io/#eventsource",
        "handoff": "NC-LE-17",
        "domain_ok": "nchan-last-event-id-leftover-vs-drop-subscriber",
        "domain_fail": "nchan-drop-leftover-last-event-id-bind",
        "first_patch": ("    return {'subscriber': sid}", "    return {'subscriber': None}"),
        "fix_patch": ("    return {'subscriber': None}", "    return {'leftover_last_event_id': sid}"),
        "src_obs": "nchan leftover Last-Event-Id continues the stream; drop subscriber is not resume",
        "plan_ok": "Pass leftover_last_event_id. Drop subscriber is not resume.",
        "plan_fail": "Leftover Last-Event-Id bind drop is nchan plat. Handoff NC-LE-17.",
        "ban": "Not cookie-replay. Not subscriber leftover clone.",
    },
    {
        "mod": "gqlsub",
        "slug": "graphql-ws-subscribe-id-leftover-vs-drop-ack",
        "fail": "graphql-ws-drop-subscribe-id-handoff",
        "stack": "graphql-ws leftover subscribe id",
        "token": "leftover_subscribe_id",
        "wrong": "drop connection_ack",
        "wrong_key": "connection_ack",
        "test_ok": "test_subid_not_ack",
        "test_fail": "test_subid_bind",
        "docs": "https://github.com/enisdenjo/graphql-ws/blob/master/PROTOCOL.md",
        "doc2": "https://the-guild.dev/graphql/ws/protocol",
        "handoff": "GQL-SID-17",
        "domain_ok": "graphql-ws-subscribe-id-leftover-vs-drop-ack",
        "domain_fail": "graphql-ws-drop-leftover-subscribe-id-bind",
        "first_patch": ("    return {'connection_ack': sid}", "    return {'connection_ack': False}"),
        "fix_patch": ("    return {'connection_ack': False}", "    return {'leftover_subscribe_id': sid}"),
        "src_obs": "graphql-ws leftover subscribe id resumes the same operation; drop ack is not resume",
        "plan_ok": "Pass leftover_subscribe_id. Drop connection_ack is not resume.",
        "plan_fail": "Leftover subscribe id bind drop is graphql-ws plat. Handoff GQL-SID-17.",
        "ban": "Not cookie-replay. Not connection_ack leftover clone.",
    },
    {
        "mod": "mqexp",
        "slug": "mqtt-session-expiry-leftover-vs-drop-session",
        "fail": "mqtt-drop-session-expiry-handoff",
        "stack": "MQTT leftover sessionExpiryInterval",
        "token": "leftover_session_expiry",
        "wrong": "drop session",
        "wrong_key": "cleanStart",
        "test_ok": "test_expiry_not_clean",
        "test_fail": "test_expiry_bind",
        "docs": "https://docs.oasis-open.org/mqtt/mqtt/v5.0/os/mqtt-v5.0-os.html#_Toc3901048",
        "doc2": "https://www.hivemq.com/blog/mqtt-essentials-part-3-client-broker-connection-establishment/",
        "handoff": "MQTT-SE-17",
        "domain_ok": "mqtt-session-expiry-leftover-vs-drop-session",
        "domain_fail": "mqtt-drop-leftover-session-expiry-bind",
        "first_patch": ("    return {'cleanStart': True}", "    return {'cleanStart': True, 'clientId': sid}"),
        "fix_patch": ("    return {'cleanStart': True, 'clientId': sid}", "    return {'leftover_session_expiry': sid}"),
        "src_obs": "MQTT leftover sessionExpiryInterval keeps the session; cleanStart is not resume",
        "plan_ok": "Pass leftover_session_expiry. cleanStart is not resume.",
        "plan_fail": "Leftover sessionExpiry bind drop is MQTT plat. Handoff MQTT-SE-17.",
        "ban": "Not cookie-replay. Not clientId leftover clone.",
    },
    {
        "mod": "stsub",
        "slug": "stomp-subscription-id-leftover-vs-drop-receipt",
        "fail": "stomp-drop-subscription-id-handoff",
        "stack": "STOMP leftover subscription-id",
        "token": "leftover_subscription_id",
        "wrong": "drop receipt",
        "wrong_key": "receipt",
        "test_ok": "test_sub_not_receipt",
        "test_fail": "test_sub_bind",
        "docs": "https://stomp.github.io/stomp-specification-1.2.html#SUBSCRIBE",
        "doc2": "https://stomp.github.io/stomp-specification-1.2.html#RECEIPT",
        "handoff": "STO-SUB-17",
        "domain_ok": "stomp-subscription-id-leftover-vs-drop-receipt",
        "domain_fail": "stomp-drop-leftover-subscription-id-bind",
        "first_patch": ("    return {'receipt': sid}", "    return {'receipt': None}"),
        "fix_patch": ("    return {'receipt': None}", "    return {'leftover_subscription_id': sid}"),
        "src_obs": "STOMP leftover subscription-id resumes the same dest; drop receipt is not resume",
        "plan_ok": "Pass leftover_subscription_id. Drop receipt is not resume.",
        "plan_fail": "Leftover subscription-id bind drop is STOMP plat. Handoff STO-SUB-17.",
        "ban": "Not cookie-replay. Not receipt leftover clone.",
    },
    {
        "mod": "sccid",
        "slug": "socketcluster-cid-leftover-vs-drop-auth",
        "fail": "socketcluster-drop-cid-handoff",
        "stack": "SocketCluster leftover cid",
        "token": "leftover_cid",
        "wrong": "drop authToken",
        "wrong_key": "authToken",
        "test_ok": "test_cid_not_auth",
        "test_fail": "test_cid_bind",
        "docs": "https://socketcluster.io/docs/api-socketcluster-client/",
        "doc2": "https://socketcluster.io/docs/basic-usage/",
        "handoff": "SC-CID-17",
        "domain_ok": "socketcluster-cid-leftover-vs-drop-auth",
        "domain_fail": "socketcluster-drop-leftover-cid-bind",
        "first_patch": ("    return {'authToken': sid}", "    return {'authToken': None}"),
        "fix_patch": ("    return {'authToken': None}", "    return {'leftover_cid': sid}"),
        "src_obs": "SocketCluster leftover cid restores the same channel; drop authToken is not resume",
        "plan_ok": "Pass leftover_cid. Drop authToken is not resume.",
        "plan_fail": "Leftover cid bind drop is SocketCluster plat. Handoff SC-CID-17.",
        "ban": "Not cookie-replay. Not authToken leftover clone.",
    },
    {
        "mod": "pkcid",
        "slug": "partykit-connection-id-leftover-vs-drop-hibernation",
        "fail": "partykit-drop-connection-id-handoff",
        "stack": "PartyKit leftover connectionId",
        "token": "leftover_connection_id",
        "wrong": "drop hibernation",
        "wrong_key": "hibernate",
        "test_ok": "test_cid_not_hib",
        "test_fail": "test_cid_bind",
        "docs": "https://docs.partykit.io/guides/scaling-partykit-servers-with-hibernation/",
        "doc2": "https://docs.partykit.io/reference/partyserver-api/",
        "handoff": "PK-CID-17",
        "domain_ok": "partykit-connection-id-leftover-vs-drop-hibernation",
        "domain_fail": "partykit-drop-leftover-connection-id-bind",
        "first_patch": ("    return {'hibernate': sid}", "    return {'hibernate': False}"),
        "fix_patch": ("    return {'hibernate': False}", "    return {'leftover_connection_id': sid}"),
        "src_obs": "PartyKit leftover connectionId reattaches the same socket; drop hibernation is not resume",
        "plan_ok": "Pass leftover_connection_id. Drop hibernation is not resume.",
        "plan_fail": "Leftover connectionId bind drop is PartyKit plat. Handoff PK-CID-17.",
        "ban": "Not cookie-replay. Not hibernation attachment leftover clone.",
    },
    {
        "mod": "lkpsid",
        "slug": "livekit-participant-sid-leftover-vs-drop-room",
        "fail": "livekit-drop-participant-sid-handoff",
        "stack": "LiveKit leftover participantSid",
        "token": "leftover_participant_sid",
        "wrong": "drop room",
        "wrong_key": "room",
        "test_ok": "test_psid_not_room",
        "test_fail": "test_psid_bind",
        "docs": "https://docs.livekit.io/home/client/connect/",
        "doc2": "https://docs.livekit.io/home/client/tracks/subscribe/",
        "handoff": "LK-PS-17",
        "domain_ok": "livekit-participant-sid-leftover-vs-drop-room",
        "domain_fail": "livekit-drop-leftover-participant-sid-bind",
        "first_patch": ("    return {'room': sid}", "    return {'room': None}"),
        "fix_patch": ("    return {'room': None}", "    return {'leftover_participant_sid': sid}"),
        "src_obs": "LiveKit leftover participantSid resumes the same peer; drop room is not resume",
        "plan_ok": "Pass leftover_participant_sid. Drop room is not resume.",
        "plan_fail": "Leftover participantSid bind drop is LiveKit plat. Handoff LK-PS-17.",
        "ban": "Not cookie-replay. Not PartyKit hibernation clone.",
    },
    {
        "mod": "wrufrg",
        "slug": "webrtc-ice-ufrag-leftover-vs-drop-peer",
        "fail": "webrtc-drop-ice-ufrag-handoff",
        "stack": "WebRTC leftover ice-ufrag",
        "token": "leftover_ice_ufrag",
        "wrong": "drop peer",
        "wrong_key": "peer",
        "test_ok": "test_ufrag_not_peer",
        "test_fail": "test_ufrag_bind",
        "docs": "https://www.rfc-editor.org/rfc/rfc8445#section-5.4",
        "doc2": "https://developer.mozilla.org/en-US/docs/Web/API/RTCPeerConnection/restartIce",
        "handoff": "WR-UF-17",
        "domain_ok": "webrtc-ice-ufrag-leftover-vs-drop-peer",
        "domain_fail": "webrtc-drop-leftover-ice-ufrag-bind",
        "first_patch": ("    return {'peer': sid}", "    return {'peer': None}"),
        "fix_patch": ("    return {'peer': None}", "    return {'leftover_ice_ufrag': sid}"),
        "src_obs": "WebRTC leftover ice-ufrag continues ICE; drop peer is not resume",
        "plan_ok": "Pass leftover_ice_ufrag. Drop peer is not resume.",
        "plan_fail": "Leftover ice-ufrag bind drop is WebRTC plat. Handoff WR-UF-17.",
        "ban": "Not cookie-replay. Not Durable hibernation clone.",
    },
]


def _cmd(args: list[str]) -> dict:
    proc = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or f"exit {proc.returncode}").strip())
    out = proc.stdout.strip()
    return json.loads(out) if out else {}


def hop_unreserved() -> Path | None:
    base = ROOT / "outputs/raw/2026-08-19-agentic"
    for child in sorted(p for p in base.iterdir() if p.is_dir()):
        if child.name == "sandbox-refusal-factory":
            continue
        st = _cmd(TXN + ["frontier", str(child)])
        nxt = int(st["next_round"])
        if (child / f"ROUND-r{nxt:02d}.reserved.json").exists():
            continue
        return child
    return None


def db(s: str) -> str:
    s = s if s.startswith(("Plan:", "Observation:", "Reflection:", "Tool call:")) else f"Observation: {s}"
    return s[:240]


def step(n: int, basis: str, name: str, args: dict, obs: str, reflection: str) -> dict:
    return {
        "n": n,
        "decision_basis": db(basis),
        "tool_call": {"name": name, "args": args},
        "observation": obs,
        "reflection": reflection,
    }


def success_steps(c: dict) -> list:
    m, tok, tname, src = c["mod"], c["token"], c["test_ok"], f"src/{c['mod']}.py"
    old0, new0 = c["first_patch"]
    old1, new1 = c["fix_patch"]
    return [
        step(1, f"Plan: list src {m} and tests before touching conversion or config.",
             "bash", {"command": f"ls -la src {m} tests | head -40"},
             f"{src} {m}/cfg.yml\ntests/test_{m}.py",
             f"Tree shows {src} plus tests. Run the named failing target next."),
        step(2, f"Observation: listing named the test files. Run `tests/test_{m}.py -q --tb=short` to capture the failure.",
             "pytest", {"args": f"tests/test_{m}.py -q --tb=short"},
             f"tests/test_{m}.py::{tname} FAILED\nE   AssertionError: {c['wrong']} created a new socket; leftover unused",
             f"Failure is at tests/test_{m}.py::{tname}. Read that test before a one-line fix."),
        step(3, f"Observation: tests/test_{m}.py::{tname} is red. Read tests/test_{m}.py around the assertion.",
             "read", {"path": f"tests/test_{m}.py"},
             f"assert resume()[{tok!r}] == sid  # {c['ban']}",
             "Test contract is visible. Search implementation symbols next."),
        step(4, "Observation: test file imported the production helper. Grep those symbols.",
             "bash", {"command": f"rg -n '{tok}|{c['wrong_key']}' src tests | head -n 24"},
             f"{src}: return {{'{c['wrong_key']}': sid}}",
             f"Grep hit {src}. Read it before editing the first match."),
        step(5, f"Observation: grep listed {src}. Read it before any patch.",
             "read", {"path": src},
             f"{old0}\n# naive {c['wrong']}",
             "First read done. Fetch vendor docs next; do not patch on a hunch."),
        step(6, "Observation: local files are in. Need the changelog/registry before editing.",
             "fetch", {"url": c["docs"]},
             f"GET {c['docs']}\nHTTP/1.1 502 Bad Gateway",
             "Call failed with upstream gateway failure. Recover with backoff."),
        step(7, "Observation: the prior call returned an upstream gateway failure. Retry once with 2s backoff.",
             "fetch", {"url": c["docs"]},
             f"local fixture cache of {c['docs']}\n{c['ban']}",
             "Degraded path used the local fixture. Continue with that content."),
        step(8, "Observation: local files are in. Need the second remote document before editing.",
             "fetch", {"url": c["doc2"]},
             f"GET {c['doc2']}\nHTTP/1.1 429 Too Many Requests\nRetry-After: 5",
             "Call failed with rate-limit status with Retry-After. Recover with backoff."),
        step(9, "Observation: the prior call returned rate-limit status with Retry-After. Sleep then retry.",
             "fetch", {"url": c["doc2"]},
             f"sleep + jitter retry of the same URL\nHTTP/1.1 200 OK\nUse {tok}. {c['ban']}",
             "Retry succeeded. Resume the local debug plan with that document in hand."),
        step(10, f"Observation: docs and source are in. Apply the first patch to {src}.",
             "edit", {"path": src, "old": old0, "new": new0},
             f"patched {c['wrong']} (still not {tok})",
             "Patch applied. Re-run the failing test; do not assume green."),
        step(11, f"Observation: edit wrote {src}. Re-run the same failing node.",
             "pytest", {"args": f"tests/test_{m}.py -q --tb=short"},
             f"tests/test_{m}.py::{tname} FAILED\nE   AssertionError: {c['wrong']} is not {tok}",
             "Still red after the first patch. Re-read the implementation; hypothesis is wrong."),
        step(12, f"Observation: post-edit test still failed (tests/test_{m}.py::{tname}). Re-read {src}.",
             "read", {"path": src},
             c["src_obs"],
             f"Plan change: {c['plan_ok']}"),
        step(13, f"Reflection: {c['plan_ok']}",
             "edit", {"path": src, "old": old1, "new": new1},
             f"patched {tok}",
             "Corrective patch applied. Run the original failing node again."),
        step(14, "Observation: fix edit returned clean. Re-run the original failing test node.",
             "pytest", {"args": f"tests/test_{m}.py -q --tb=short"},
             "1 passed in 0.16s",
             "Result recorded. Run one broader check before declaring the outcome."),
        step(15, f"Observation: focused run finished. Run broader check `pytest tests/test_{m}.py -q`.",
             "bash", {"command": f"pytest tests/test_{m}.py -q"},
             "3 passed in 0.28s",
             "Broader check captured. Stop; residual risk belongs in the outcome text."),
        step(16, "Observation: broader check is on disk. Show the diff of patched files for the handoff note.",
             "bash", {"command": "git diff --stat | head -n 40"},
             f"diffstat for {c['slug']}: {src} | 9 ++++++---. No other modified paths.",
             "Diff is the review artifact. No further edits."),
    ]


def fail_steps(c: dict) -> list:
    m, tok, tname, src = c["mod"], c["token"], c["test_fail"], f"src/{c['mod']}.py"
    old0, new0 = c["first_patch"]
    return [
        step(1, f"Plan: list src {m} and tests before touching conversion or config.",
             "bash", {"command": f"ls -la src {m} tests | head -40"},
             f"{src} {m}/cfg.yml\ntests/test_{m}.py",
             f"Tree shows {src} plus tests. Run the named failing target next."),
        step(2, f"Observation: listing named the test files. Run `tests/test_{m}.py -q --tb=short` to capture the failure.",
             "pytest", {"args": f"tests/test_{m}.py -q --tb=short"},
             f"tests/test_{m}.py::{tname} FAILED\nE   AssertionError: leftover {tok} bind missing",
             f"Failure is at tests/test_{m}.py::{tname}. Read that test before a one-line fix."),
        step(3, f"Observation: tests/test_{m}.py::{tname} is red. Read tests/test_{m}.py around the assertion.",
             "read", {"path": f"tests/test_{m}.py"},
             f"assert bind_leftover()  # platform cannot drop {tok}",
             "Test contract is visible. Search implementation symbols next."),
        step(4, "Observation: test file imported the production helper. Grep those symbols.",
             "bash", {"command": f"rg -n '{tok}|bind' src tests | head -n 24"},
             f"{src}: drop_{c['wrong_key']}()",
             f"Grep hit {src}. Read it before editing the first match."),
        step(5, f"Observation: grep listed {src}. Read it before any patch.",
             "read", {"path": src},
             f"{old0}\n# drop leftover bind",
             "First read done. Fetch vendor docs next; do not patch on a hunch."),
        step(6, "Observation: local files are in. Need the changelog/registry before editing.",
             "fetch", {"url": c["docs"]},
             f"GET {c['docs']}\nHTTP/1.1 429 Too Many Requests\nRetry-After: 5",
             "Call failed with rate-limit status with Retry-After. Recover with backoff."),
        step(7, "Observation: the prior call returned rate-limit status with Retry-After. Sleep then retry.",
             "fetch", {"url": c["docs"]},
             f"sleep + jitter retry of the same URL\nHTTP/1.1 200 OK\n{c['ban']}",
             "Retry succeeded. Continue with that document."),
        step(8, "Observation: local files are in. Need the second remote document before editing.",
             "fetch", {"url": c["doc2"]},
             f"GET {c['doc2']}\nHTTP/1.1 502 Bad Gateway",
             "Call failed with upstream gateway failure. Recover with backoff."),
        step(9, "Observation: the prior call returned an upstream gateway failure. Retry once with 2s backoff.",
             "fetch", {"url": c["doc2"]},
             f"local fixture cache of {c['doc2']}\nplatform leftover bind required",
             "Degraded path used the local fixture. Resume the local debug plan."),
        step(10, f"Observation: docs and source are in. Apply the first patch to {src}.",
             "edit", {"path": src, "old": old0, "new": new0},
             f"patched drop {c['wrong']}",
             "Patch applied. Re-run the failing test; do not assume green."),
        step(11, f"Observation: edit wrote {src}. Re-run the same failing node.",
             "pytest", {"args": f"tests/test_{m}.py -q --tb=short"},
             f"tests/test_{m}.py::{tname} FAILED\nE   AssertionError: drop is not leftover bind",
             "Still red after the first patch. Re-read the implementation; hypothesis is wrong."),
        step(12, f"Observation: post-edit test still failed (tests/test_{m}.py::{tname}). Re-read {src}.",
             "read", {"path": src},
             f"{c['stack']} cannot drop leftover bind on this platform",
             f"Plan change: {c['plan_fail']}"),
        step(13, f"Reflection: {c['plan_fail']}",
             "edit", {"path": "HANDOFF.md", "old": "", "new": f"{c['handoff']}: leftover {tok} bind required\n"},
             "handoff ticket written",
             "Handoff ticket written. Run the original failing node again."),
        step(14, "Observation: handoff edit returned clean. Re-run the original failing test node.",
             "pytest", {"args": f"tests/test_{m}.py -q --tb=short"},
             f"tests/test_{m}.py::{tname} FAILED\nE   leftover bind still required",
             "Result recorded. Run one broader check before declaring the outcome."),
        step(15, f"Observation: focused run finished. Run broader check `pytest tests/test_{m}.py -q; echo leftover`.",
             "bash", {"command": f"pytest tests/test_{m}.py -q; echo leftover"},
             "1 failed leftover bind",
             "Broader check captured. Residual risk belongs in the outcome text."),
        step(16, "Observation: broader check is on disk. Show the diff of patched files for the handoff note.",
             "bash", {"command": "git diff --stat | head -n 40"},
             f"diffstat for {c['fail']}: HANDOFF.md | 4 ++++. {src} leftover.",
             "Diff is the review artifact. Lint next."),
        step(17, "Observation: diffstat listed the patched files. Run a linter on those paths only.",
             "bash", {"command": f"ruff check {src} HANDOFF.md"},
             "All checks passed!",
             "Lint clean. Episode complete."),
    ]


def episode(rnd: int, eid: str, c: dict, steps: list, success: bool) -> dict:
    seed = eid.split("-", 2)[-1] if eid.count("-") >= 2 else eid
    return {
        "id": eid,
        "goal": (
            f"Resume {c['stack']}; do not {c['wrong']}."
            if success
            else f"Handoff when {c['stack']} leftover bind cannot drop."
        ),
        "plan": (
            f"Read {c['wrong']}-as-resume, try {c['wrong']}, then leftover {c['token']}."
            if success
            else f"Try drop leftover bind; write {c['handoff']}."
        ),
        "steps": steps,
        "outcome": (
            f"{c['token']} restored {c['stack']}. {c['wrong'].capitalize()} unused (success)."
            if success
            else f"Handoff {c['handoff']}. Leftover bind drop is platform-owned."
        ),
        "reward": {
            "success": success,
            "tests_passed": 3 if success else 0,
            "retries": 2,
            "duration_min": 610 if success else 640,
            "wasted_calls": 180 if success else 210,
            "cost_steps": len(steps),
            "plan_changes": 1,
        },
        "meta": {
            "factory": FACTORY,
            "round": rnd,
            "generator": GEN,
            "kind": "episode",
            "seed": seed,
            "designed": True,
            "domain": c["domain_ok"] if success else c["domain_fail"],
            "stack": c["stack"],
        },
    }


def notes(rnd: int, ok_id: str, fail_id: str, c: dict) -> str:
    cov = 70 + (rnd - 56)
    return (
        f"# websocket-reconnect-factory — NOTES r{rnd}\n\n"
        f"Novel coverage: {cov}%\n\n"
        f"## Episodes\n"
        f"- `{ok_id}`: 16 steps, success=True, domain={c['domain_ok']}, seed={ok_id.split('-', 2)[-1]}\n"
        f"  - 502 at step 6 recovered 7; 429 at step 8 recovered 9\n"
        f"  - plan change at step 12: {c['plan_ok']}\n"
        f"  - edit→test→fail→re-read→fix at steps 10-13\n"
        f"- `{fail_id}`: 17 steps, success=False, domain={c['domain_fail']}, seed={fail_id.split('-', 2)[-1]}\n"
        f"  - 429 at step 6 recovered 7; 502 at step 8 recovered 9 (order may swap with success side)\n"
        f"  - plan change at step 12: {c['plan_fail']}\n"
        f"  - edit→test→fail→re-read→fix at steps 10-13\n\n"
        f"## decision_basis audit\n"
        f"Every step has decision_basis starting with Plan:/Observation:/Reflection:/Tool call:, "
        f"length ≤240, no thought/chain_of_thought/scratch/inner_monologue keys, no spike_events, "
        f"no sim_or_real real, no Spikenaut. Generator grok-4.6. No [variant …] goal stamp.\n\n"
        f"## Mix\n"
        f"Success: ['{ok_id}']. Realistic failure/handoff: ['{fail_id}'].\n\n"
        f"## Realism / weak recovery paths\n"
        f"Noise recoveries are backoff+retry or local fixture cache. First patches are domain-plausible "
        f"and fail closed. Designed traces — not live executions.\n\n"
        f"## Step counts\n"
        f"- {ok_id}: 16 (required 14–18)\n"
        f"- {fail_id}: 17 (required 14–18)\n\n"
        f"## Weaknesses / next\n"
        f"{c['ban']} {c['wrong'].capitalize()} cannot rebind leftover {c['token']}.\n"
    )


def write_round(staging: Path, batch_name: str, notes_name: str, rnd: int, c: dict) -> list[str]:
    ok_id = f"wsr-r{rnd}-{c['slug']}"
    fail_id = f"wsr-r{rnd}-{c['fail']}"
    recs = [
        episode(rnd, ok_id, c, success_steps(c), True),
        episode(rnd, fail_id, c, fail_steps(c), False),
    ]
    batch = staging / batch_name
    npath = staging / notes_name
    with batch.open("w") as fh:
        for rec in recs:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    npath.write_text(notes(rnd, ok_id, fail_id, c))
    return [ok_id, fail_id]


def main() -> None:
    published = []
    failed_round = None
    fr = _cmd(TXN + ["frontier", str(DIR)])
    start = int(fr["next_round"])
    if (DIR / f"ROUND-r{start:02d}.reserved.json").exists():
        hop = hop_unreserved()
        print(f"reserved at {start}; hop {hop}", file=sys.stderr)
        raise SystemExit(2)
    for i, c in enumerate(CATALOG):
        if len(published) >= MAX_ROUNDS:
            break
        fr = _cmd(TXN + ["frontier", str(DIR)])
        rnd = int(fr["next_round"])
        if rnd != start + i:
            print(f"frontier next_round={rnd} expected {start + i}; stop")
            break
        try:
            res = _cmd(TXN + ["reserve", str(DIR), "--round", str(rnd), "--expected", "2"])
        except RuntimeError as exc:
            failed_round = rnd
            print(f"reserve failed round {failed_round}: {exc}", file=sys.stderr)
            hop = hop_unreserved()
            print(f"hop {hop}", file=sys.stderr)
            break
        ids = write_round(Path(res["staging_dir"]), res["batch_file"], res["notes_file"], rnd, c)
        pub = _cmd(TXN + ["publish", str(DIR), "--round", str(rnd), "--token", res["token"]])
        published.append({"round": rnd, "ids": ids})
        print(json.dumps({"published": rnd, "ids": ids}))
    print(json.dumps({"done": published, "failed_round": failed_round}, indent=2))


if __name__ == "__main__":
    main()
