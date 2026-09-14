#!/usr/bin/env python3
"""websocket-reconnect leftover leftover leftover mill r125–r140 (16 pairs)."""
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

# Distinct leftover leftover leftover vs r41–r124. BAN r40 anycable / reverb. BAN sir-/dbc-/gql- ids.
# Each: leftover leftover leftover resume token vs timeout stretch (success) / drop-bind handoff (fail).
CATALOG = [
    {
        "mod": "dlytok",
        "dmod": "dlytdrop",
        "slug": "daily-meeting-token-leftover-vs-drop-room",
        "fail": "daily-drop-meeting-token-handoff",
        "stack": "Daily leftover leftover leftover meetingToken",
        "token": "meetingToken",
        "extra": "exp",
        "tkey": "idleTimeout",
        "wrong": "drop room",
        "wrong_key": "room",
        "test_ok": "test_meeting_token_not_idle",
        "test_fail": "test_must_keep_meeting_token",
        "docs": "https://docs.daily.co/reference/rest-api/meeting-tokens",
        "doc2": "https://docs.daily.co/reference/daily-js/instance-methods/join",
        "handoff": "DL-MT-125",
        "domain_ok": "daily-leftover-meeting-token-vs-idle",
        "domain_fail": "daily-leftover-meeting-token-drop-vs-idle",
        "ban": "Not cookie-replay. Not recording-id leftover clone. Not anycable/reverb.",
    },
    {
        "mod": "twpsid",
        "dmod": "twpsdrop",
        "slug": "twilio-video-participant-sid-leftover-vs-drop-media",
        "fail": "twilio-video-drop-participant-sid-handoff",
        "stack": "Twilio Video leftover leftover leftover participantSid",
        "token": "participantSid",
        "extra": "identity",
        "tkey": "reconnectTimeout",
        "wrong": "drop media",
        "wrong_key": "media",
        "test_ok": "test_participant_sid_not_reconnect",
        "test_fail": "test_must_keep_participant_sid",
        "docs": "https://www.twilio.com/docs/video/reconnection-states-and-events",
        "doc2": "https://www.twilio.com/docs/video/api/participants-resource",
        "handoff": "TW-PS-125",
        "domain_ok": "twilio-video-leftover-participant-sid-vs-reconnect",
        "domain_fail": "twilio-video-leftover-participant-sid-drop-vs-reconnect",
        "ban": "Not cookie-replay. Not local-track leftover clone. Not anycable/reverb.",
    },
    {
        "mod": "agchkey",
        "dmod": "agckdrop",
        "slug": "agora-channel-key-leftover-vs-drop-uid",
        "fail": "agora-drop-channel-key-handoff",
        "stack": "Agora leftover leftover leftover channelKey",
        "token": "channelKey",
        "extra": "uid",
        "tkey": "timeoutMs",
        "wrong": "drop uid",
        "wrong_key": "uid",
        "test_ok": "test_channel_key_not_timeout",
        "test_fail": "test_must_keep_channel_key",
        "docs": "https://docs.agora.io/en/video-calling/develop/authentication-workflow",
        "doc2": "https://docs.agora.io/en/video-calling/develop/ensure-service-reliability",
        "handoff": "AG-CK-125",
        "domain_ok": "agora-leftover-channel-key-vs-timeout",
        "domain_fail": "agora-leftover-channel-key-drop-vs-timeout",
        "ban": "Not cookie-replay. Not uid leftover clone. Not anycable/reverb.",
    },
    {
        "mod": "lkpkt",
        "dmod": "lkpkdrop",
        "slug": "livekit-data-packet-leftover-vs-drop-room",
        "fail": "livekit-drop-data-packet-handoff",
        "stack": "LiveKit leftover leftover leftover dataPacket",
        "token": "dataPacket",
        "extra": "seq",
        "tkey": "pingTimeout",
        "wrong": "drop room",
        "wrong_key": "room",
        "test_ok": "test_data_packet_not_ping",
        "test_fail": "test_must_keep_data_packet",
        "docs": "https://docs.livekit.io/home/client/events/#data",
        "doc2": "https://docs.livekit.io/home/client/connect/",
        "handoff": "LK-DP-125",
        "domain_ok": "livekit-leftover-data-packet-vs-ping",
        "domain_fail": "livekit-leftover-data-packet-drop-vs-ping",
        "ban": "Not cookie-replay. Not track-sid leftover clone. Not anycable/reverb.",
    },
    {
        "mod": "srgrp",
        "dmod": "srgpdrop",
        "slug": "signalr-groups-token-leftover-vs-drop-hub",
        "fail": "signalr-drop-groups-token-handoff",
        "stack": "SignalR leftover leftover leftover groupsToken",
        "token": "groupsToken",
        "extra": "connectionId",
        "tkey": "KeepAliveInterval",
        "wrong": "drop hub",
        "wrong_key": "hub",
        "test_ok": "test_groups_token_not_keepalive",
        "test_fail": "test_must_keep_groups_token",
        "docs": "https://learn.microsoft.com/en-us/aspnet/core/signalr/configuration",
        "doc2": "https://learn.microsoft.com/en-us/aspnet/core/signalr/groups",
        "handoff": "SR-GT-125",
        "domain_ok": "signalr-leftover-groups-token-vs-keepalive",
        "domain_fail": "signalr-leftover-groups-token-drop-vs-keepalive",
        "ban": "Not cookie-replay. Not connectionToken leftover clone. Not anycable/reverb.",
    },
    {
        "mod": "phxjn",
        "dmod": "phxjndrop",
        "slug": "phoenix-phx-join-leftover-vs-drop-presence",
        "fail": "phoenix-drop-phx-join-handoff",
        "stack": "Phoenix leftover leftover leftover phx_join",
        "token": "phx_join",
        "extra": "join_ref",
        "tkey": "heartbeat_interval_ms",
        "wrong": "drop presence",
        "wrong_key": "presence",
        "test_ok": "test_phx_join_not_heartbeat",
        "test_fail": "test_must_keep_phx_join",
        "docs": "https://hexdocs.pm/phoenix/channels.html",
        "doc2": "https://hexdocs.pm/phoenix/Phoenix.Channel.html#join/3",
        "handoff": "PHX-JN-125",
        "domain_ok": "phoenix-leftover-phx-join-vs-heartbeat",
        "domain_fail": "phoenix-leftover-phx-join-drop-vs-heartbeat",
        "ban": "Not cookie-replay. Not phx-ref leftover clone. Not anycable/reverb.",
    },
    {
        "mod": "accnf",
        "dmod": "accndrop",
        "slug": "actioncable-confirmed-leftover-vs-drop-identifier",
        "fail": "actioncable-drop-confirmed-handoff",
        "stack": "ActionCable leftover leftover leftover confirmed",
        "token": "confirmed",
        "extra": "channel",
        "tkey": "ping_interval",
        "wrong": "drop identifier",
        "wrong_key": "identifier",
        "test_ok": "test_confirmed_not_ping",
        "test_fail": "test_must_keep_confirmed",
        "docs": "https://guides.rubyonrails.org/action_cable_overview.html",
        "doc2": "https://api.rubyonrails.org/classes/ActionCable/Channel/Base.html",
        "handoff": "AC-CF-125",
        "domain_ok": "actioncable-leftover-confirmed-vs-ping",
        "domain_fail": "actioncable-leftover-confirmed-drop-vs-ping",
        "ban": "Not cookie-replay. Not identifier leftover clone. Not anycable/reverb.",
    },
    {
        "mod": "cfree",
        "dmod": "cfrcdrop",
        "slug": "centrifuge-recover-leftover-vs-drop-offset",
        "fail": "centrifuge-drop-recover-handoff",
        "stack": "Centrifuge leftover leftover leftover recover",
        "token": "recover",
        "extra": "epoch",
        "tkey": "pingInterval",
        "wrong": "drop offset",
        "wrong_key": "offset",
        "test_ok": "test_recover_not_ping",
        "test_fail": "test_must_keep_recover",
        "docs": "https://centrifugal.dev/docs/server/history_and_recovery",
        "doc2": "https://centrifugal.dev/docs/transports/websocket",
        "handoff": "CF-RC-125",
        "domain_ok": "centrifuge-leftover-recover-vs-ping",
        "domain_fail": "centrifuge-leftover-recover-drop-vs-ping",
        "ban": "Not cookie-replay. Not epoch leftover clone. Not anycable/reverb.",
    },
    {
        "mod": "pusmem",
        "dmod": "pusmdrop",
        "slug": "pusher-presence-member-leftover-vs-drop-socket",
        "fail": "pusher-drop-presence-member-handoff",
        "stack": "Pusher leftover leftover leftover presence_member",
        "token": "presence_member",
        "extra": "user_id",
        "tkey": "activityTimeout",
        "wrong": "drop socket",
        "wrong_key": "socket",
        "test_ok": "test_presence_member_not_activity",
        "test_fail": "test_must_keep_presence_member",
        "docs": "https://pusher.com/docs/channels/using_channels/presence-channels/",
        "doc2": "https://pusher.com/docs/channels/library_auth_reference/pusher-websockets-protocol/",
        "handoff": "PU-PM-125",
        "domain_ok": "pusher-leftover-presence-member-vs-activity",
        "domain_fail": "pusher-leftover-presence-member-drop-vs-activity",
        "ban": "Not cookie-replay. Not socket_id leftover clone. Not anycable/reverb.",
    },
    {
        "mod": "abmsrl",
        "dmod": "abmsdrop",
        "slug": "ably-msgserial-leftover-vs-drop-key",
        "fail": "ably-drop-msgserial-handoff",
        "stack": "Ably leftover leftover leftover msgSerial",
        "token": "msgSerial",
        "extra": "channelSerial",
        "tkey": "disconnectedRetryTimeout",
        "wrong": "drop key",
        "wrong_key": "connectionKey",
        "test_ok": "test_msgserial_not_retry",
        "test_fail": "test_must_keep_msgserial",
        "docs": "https://ably.com/docs/api/realtime-sdk/connection",
        "doc2": "https://ably.com/docs/connect#connection-state-recovery",
        "handoff": "AB-MS-125",
        "domain_ok": "ably-leftover-msgserial-vs-retry",
        "domain_fail": "ably-leftover-msgserial-drop-vs-retry",
        "ban": "Not cookie-replay. Not connectionKey leftover clone. Not anycable/reverb.",
    },
    {
        "mod": "mqpres",
        "dmod": "mqprdrop",
        "slug": "mqtt-session-present-leftover-vs-drop-clientid",
        "fail": "mqtt-drop-session-present-handoff",
        "stack": "MQTT leftover leftover leftover sessionPresent",
        "token": "sessionPresent",
        "extra": "packetId",
        "tkey": "keepAlive",
        "wrong": "drop clientId",
        "wrong_key": "clientId",
        "test_ok": "test_session_present_not_keepalive",
        "test_fail": "test_must_keep_session_present",
        "docs": "https://docs.oasis-open.org/mqtt/mqtt/v5.0/os/mqtt-v5.0-os.html#_Toc3901048",
        "doc2": "https://docs.oasis-open.org/mqtt/mqtt/v5.0/os/mqtt-v5.0-os.html#_Toc3901042",
        "handoff": "MQ-SP-125",
        "domain_ok": "mqtt-leftover-session-present-vs-keepalive",
        "domain_fail": "mqtt-leftover-session-present-drop-vs-keepalive",
        "ban": "Not cookie-replay. Not clientId leftover clone. Not anycable/reverb.",
    },
    {
        "mod": "sttx",
        "dmod": "sttxdrop",
        "slug": "stomp-transaction-leftover-vs-drop-receipt",
        "fail": "stomp-drop-transaction-handoff",
        "stack": "STOMP leftover leftover leftover transaction",
        "token": "transaction",
        "extra": "id",
        "tkey": "heartbeat",
        "wrong": "drop receipt",
        "wrong_key": "receipt",
        "test_ok": "test_transaction_not_heartbeat",
        "test_fail": "test_must_keep_transaction",
        "docs": "https://stomp.github.io/stomp-specification-1.2.html#BEGIN",
        "doc2": "https://stomp.github.io/stomp-specification-1.2.html#Heart-beating",
        "handoff": "ST-TX-125",
        "domain_ok": "stomp-leftover-transaction-vs-heartbeat",
        "domain_fail": "stomp-leftover-transaction-drop-vs-heartbeat",
        "ban": "Not cookie-replay. Not receipt leftover clone. Not anycable/reverb.",
    },
    {
        "mod": "pkatt",
        "dmod": "pkatdrop",
        "slug": "partykit-attachment-leftover-vs-drop-hibernation",
        "fail": "partykit-drop-attachment-handoff",
        "stack": "PartyKit leftover leftover leftover attachment",
        "token": "attachment",
        "extra": "connectionId",
        "tkey": "hibernateAfter",
        "wrong": "drop hibernation",
        "wrong_key": "hibernation",
        "test_ok": "test_attachment_not_hibernate",
        "test_fail": "test_must_keep_attachment",
        "docs": "https://docs.partykit.io/guides/scaling-partykit-servers-with-hibernation/",
        "doc2": "https://docs.partykit.io/reference/partyserver-api/",
        "handoff": "PK-AT-125",
        "domain_ok": "partykit-leftover-attachment-vs-hibernate",
        "domain_fail": "partykit-leftover-attachment-drop-vs-hibernate",
        "ban": "Not cookie-replay. Not hibernation-id leftover clone. Not anycable/reverb.",
    },
    {
        "mod": "cfwtag",
        "dmod": "cfwtdrop",
        "slug": "cloudflare-durable-ws-tag-leftover-vs-drop-alarm",
        "fail": "cloudflare-durable-drop-ws-tag-handoff",
        "stack": "Cloudflare Durable leftover leftover leftover wsTag",
        "token": "wsTag",
        "extra": "attachment",
        "tkey": "idleTimeout",
        "wrong": "drop alarm",
        "wrong_key": "alarm",
        "test_ok": "test_ws_tag_not_idle",
        "test_fail": "test_must_keep_ws_tag",
        "docs": "https://developers.cloudflare.com/durable-objects/best-practices/websockets/",
        "doc2": "https://developers.cloudflare.com/durable-objects/api/state/#acceptwebsocket",
        "handoff": "CF-WT-125",
        "domain_ok": "cfdo-leftover-ws-tag-vs-idle",
        "domain_fail": "cfdo-leftover-ws-tag-drop-vs-idle",
        "ban": "Not cookie-replay. Not alarm leftover clone. Not anycable/reverb.",
    },
    {
        "mod": "kgstck",
        "dmod": "kgstdrop",
        "slug": "kong-sticky-cookie-leftover-vs-drop-hash",
        "fail": "kong-drop-sticky-cookie-handoff",
        "stack": "Kong leftover leftover leftover sticky.cookie",
        "token": "sticky.cookie",
        "extra": "hash_on",
        "tkey": "timeouts.connect",
        "wrong": "drop hash",
        "wrong_key": "hash_on",
        "test_ok": "test_sticky_cookie_not_connect",
        "test_fail": "test_must_keep_sticky_cookie",
        "docs": "https://docs.konghq.com/gateway/latest/reference/proxy/",
        "doc2": "https://docs.konghq.com/gateway/latest/kong-plugins/load-balancing/",
        "handoff": "KG-SC-125",
        "domain_ok": "kong-leftover-sticky-cookie-vs-connect",
        "domain_fail": "kong-leftover-sticky-cookie-drop-vs-connect",
        "ban": "Not cookie-replay clone. Not hash_on leftover clone. Not anycable/reverb.",
    },
    {
        "mod": "envupg",
        "dmod": "envudrop",
        "slug": "envoy-ws-upgrade-leftover-vs-drop-cluster",
        "fail": "envoy-drop-ws-upgrade-handoff",
        "stack": "Envoy leftover leftover leftover upgrade_configs",
        "token": "upgrade_configs",
        "extra": "hash_policy",
        "tkey": "idle_timeout",
        "wrong": "drop cluster",
        "wrong_key": "cluster",
        "test_ok": "test_upgrade_not_idle",
        "test_fail": "test_must_keep_upgrade",
        "docs": "https://www.envoyproxy.io/docs/envoy/latest/api-v3/config/route/v3/route_components.proto",
        "doc2": "https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/http/upgrades",
        "handoff": "EN-UP-125",
        "domain_ok": "envoy-leftover-upgrade-vs-idle",
        "domain_fail": "envoy-leftover-upgrade-drop-vs-idle",
        "ban": "Not cookie-replay. Not hash_policy leftover clone. Not anycable/reverb.",
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
    tk = c["tkey"]
    return [
        step(1, f"Plan: list src {m} and tests before touching conversion or config.",
             "bash", {"command": f"ls -la src {m} tests | head -40"},
             f"{src} {m}/cfg.yml\ntests/test_{m}.py",
             f"Tree shows {src} plus tests. Run the named failing target next."),
        step(2, f"Observation: listing named the test files. Run `tests/test_{m}.py -q --tb=short` to capture the failure.",
             "pytest", {"args": f"tests/test_{m}.py -q --tb=short"},
             f"tests/test_{m}.py::{tname} FAILED\nE   AssertionError: leftover leftover leftover stretched {tk}; {tok} unbounded",
             f"Failure is at tests/test_{m}.py::{tname}. Read that test before a one-line fix."),
        step(3, f"Observation: tests/test_{m}.py::{tname} is red. Read tests/test_{m}.py around the assertion.",
             "read", {"path": f"tests/test_{m}.py"},
             f"def {tname}():\n    t = tune(True)\n    assert t.get({tok!r}) and {tk!r} not in t\n",
             "Test contract is visible. Search implementation symbols next."),
        step(4, "Observation: test file imported the production helper. Grep those symbols.",
             "bash", {"command": f"rg -n '{tok}|{tk}|leftover' src {m} tests"},
             f"{src}:2: return {{{tk!r}: 5}} if lag else {{}}",
             f"Grep hit {src}. Read it before editing the first match."),
        step(5, f"Observation: grep listed {src}. Read it before any patch.",
             "read", {"path": src},
             f"def tune(lag):\n    return {{{tk!r}: 5}} if lag else {{}}\n",
             "First read done. Fetch vendor docs next; do not patch on a hunch yet."),
        step(6, "Observation: local files are in. Need the changelog/registry before editing.",
             "fetch", {"url": c["docs"]},
             f"GET {c['docs']}\nHTTP/1.1 502 Bad Gateway\nBad Gateway.",
             "Call failed with upstream gateway failure. Recover with backoff."),
        step(7, "Observation: the prior call returned an upstream gateway failure. Retry once with 2s backoff.",
             "fetch", {"url": c["docs"]},
             f"retry after 2s backoff; local vendor fixture\nHTTP/1.1 200 OK\nleftover leftover leftover {tok} binds resume; {tk} is a clock.",
             "Degraded path used the local fixture. Continue with that content."),
        step(8, "Observation: local files are in. Need the second remote document before editing.",
             "fetch", {"url": c["doc2"]},
             f"GET {c['doc2']}\nHTTP/1.1 429 Too Many Requests\nRetry-After: 5\nX-RateLimit-Remaining: 0",
             "Call failed with rate-limit status with Retry-After. Recover with backoff."),
        step(9, "Observation: the prior call returned rate-limit status with Retry-After. Sleep then retry.",
             "fetch", {"url": c["doc2"]},
             f"sleep + jitter retry of the same URL\nHTTP/1.1 200 OK\nBind leftover leftover leftover {tok}, do not {c['wrong']}.",
             "Retry succeeded. Resume the local debug plan with that document in hand."),
        step(10, f"Observation: docs and source are in. Apply the first patch to {src}.",
             "edit", {"path": src, "old": f"    return {{{tk!r}: 5}} if lag else {{}}",
                      "new": f"    return {{{tk!r}: 30}} if lag else {{}}"},
             "patched 30 (still a timeout integer)",
             "Patch applied. Re-run the failing test; do not assume green."),
        step(11, f"Observation: edit wrote {src}. Re-run the same failing node.",
             "pytest", {"args": f"tests/test_{m}.py -q --tb=short"},
             f"tests/test_{m}.py::{tname} FAILED\nE   AssertionError: timeout integer cannot bind leftover leftover leftover {tok}",
             "Still red after the first patch. Re-read the implementation; hypothesis is wrong."),
        step(12, f"Observation: post-edit test still failed (tests/test_{m}.py::{tname}). Re-read {src}.",
             "read", {"path": src},
             f"leftover leftover leftover is {tok}; {tk} is not the leftover leftover leftover bound",
             f"Plan change: bind leftover leftover leftover {tok} plus {c['extra']}. {tk} is not a leftover leftover leftover bound."),
        step(13, f"Reflection: bind leftover leftover leftover {tok} plus {c['extra']}. {tk} is not a leftover leftover leftover bound.",
             "edit", {"path": src, "old": f"    return {{{tk!r}: 30}} if lag else {{}}",
                      "new": f"    return {{{tok!r}: True, {c['extra']!r}: True}} if lag else {{}}"},
             f"patched leftover leftover leftover {tok}",
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
    m, tok, tname, src = c["dmod"], c["token"], c["test_fail"], f"src/{c['dmod']}.py"
    tk = c["tkey"]
    return [
        step(1, f"Plan: list src {m} and tests before touching conversion or config.",
             "bash", {"command": f"ls -la src {m} tests | head -40"},
             f"{src} {m}/cfg.yml\ntests/test_{m}.py",
             f"Tree shows {src} plus tests. Run the named failing target next."),
        step(2, f"Observation: listing named the test files. Run `tests/test_{m}.py -q --tb=short` to capture the failure.",
             "pytest", {"args": f"tests/test_{m}.py -q --tb=short"},
             f"tests/test_{m}.py::{tname} FAILED\nE   AssertionError: leftover leftover leftover slept {tk}; {c['wrong']} is not a leftover leftover leftover bind",
             f"Failure is at tests/test_{m}.py::{tname}. Read that test before a one-line fix."),
        step(3, f"Observation: tests/test_{m}.py::{tname} is red. Read tests/test_{m}.py around the assertion.",
             "read", {"path": f"tests/test_{m}.py"},
             f"def {tname}():\n    assert {tk!r} not in tune(True)\n",
             "Test contract is visible. Search implementation symbols next."),
        step(4, "Observation: test file imported the production helper. Grep those symbols.",
             "bash", {"command": f"rg -n '{tk}|{c['wrong_key']}|leftover' src {m} tests"},
             f"{src}:2: return {{{tk!r}: 5}} if blocked else {{}}",
             f"Grep hit {src}. Read it before editing the first match."),
        step(5, f"Observation: grep listed {src}. Read it before any patch.",
             "read", {"path": src},
             f"def tune(blocked):\n    return {{{tk!r}: 5}} if blocked else {{}}\n",
             "First read done. Fetch vendor docs next; do not patch on a hunch yet."),
        step(6, "Observation: local files are in. Need the changelog/registry before editing.",
             "fetch", {"url": c["docs"]},
             f"GET {c['docs']}\nHTTP/1.1 429 Too Many Requests\nRetry-After: 6\nX-RateLimit-Remaining: 0",
             "Call failed with rate-limit status with Retry-After. Recover with backoff."),
        step(7, "Observation: the prior call returned rate-limit status with Retry-After. Sleep then retry.",
             "fetch", {"url": c["docs"]},
             f"sleep + jitter retry of the same URL\nHTTP/1.1 200 OK\n{c['wrong'].capitalize()} drops leftover leftover leftover; it does not bind {tok}.",
             "Retry succeeded. Continue with that document."),
        step(8, "Observation: local files are in. Need the second remote document before editing.",
             "fetch", {"url": c["doc2"]},
             f"GET {c['doc2']}\nHTTP/1.1 502 Bad Gateway\nBad Gateway.",
             "Call failed with upstream gateway failure. Recover with backoff."),
        step(9, "Observation: the prior call returned an upstream gateway failure. Retry once with 2s backoff.",
             "fetch", {"url": c["doc2"]},
             f"retry after 2s backoff; local vendor fixture\nHTTP/1.1 200 OK\nTimeout cannot mint leftover leftover leftover; {c['wrong']} is platform. Handoff {c['handoff']}.",
             "Degraded path used the local fixture. Resume the local debug plan."),
        step(10, f"Observation: docs and source are in. Apply the first patch to {src}.",
             "edit", {"path": src, "old": f"    return {{{tk!r}: 5}} if blocked else {{}}",
                      "new": f"    return {{{tk!r}: 0}} if blocked else {{}}"},
             "patched 0s (still a timeout integer)",
             "Patch applied. Re-run the failing test; do not assume green."),
        step(11, f"Observation: edit wrote {src}. Re-run the same failing node.",
             "pytest", {"args": f"tests/test_{m}.py -q --tb=short"},
             f"tests/test_{m}.py::{tname} FAILED\nE   AssertionError: timeout cannot mint leftover leftover leftover; {c['wrong']} is not a bind",
             "Still red after the first patch. Re-read the implementation; hypothesis is wrong."),
        step(12, f"Observation: post-edit test still failed (tests/test_{m}.py::{tname}). Re-read {src}.",
             "read", {"path": src},
             f"{c['wrong']} destroys leftover leftover leftover; bind leftover leftover leftover is platform",
             f"Plan change: {c['wrong_key']} drop is platform. Handoff {c['handoff']}."),
        step(13, f"Reflection: {c['wrong_key']} drop is platform. Handoff {c['handoff']}.",
             "edit", {"path": f"{m}/handoff.md", "old": "",
                      "new": f"# {c['handoff']} leftover leftover leftover {tok} owned by ws-plat"},
             "ticket filed. still timeout-classed",
             "Handoff ticket written. Run the original failing node again."),
        step(14, "Observation: handoff edit returned clean. Re-run the original failing test node.",
             "pytest", {"args": f"tests/test_{m}.py -q --tb=short"},
             f"tests/test_{m}.py::{tname} FAILED  # handoff: {c['handoff']}\n1 failed",
             "Result recorded. Run one broader check before declaring the outcome."),
        step(15, f"Observation: focused run finished. Run broader check `pytest tests/test_{m}.py -q; echo {c['handoff']}`.",
             "bash", {"command": f"pytest tests/test_{m}.py -q; echo {c['handoff']}"},
             f"1 failed, 2 passed\n{c['handoff']}",
             "Broader check captured. Residual risk belongs in the outcome text."),
        step(16, "Observation: broader check is on disk. Show the diff of patched files for the handoff note.",
             "bash", {"command": "git diff --stat | head -n 40"},
             f"diffstat for {c['fail']}: {src} | 8 +++++---. {m}/handoff.md added.",
             "Diff is the review artifact. Lint next."),
        step(17, "Observation: diffstat listed the patched files. Run a linter on those paths only.",
             "bash", {"command": "ruff check tests || true; echo lint-end"},
             "All checks passed!\nlint-end",
             "Lint clean. Episode complete."),
    ]


def episode(rnd: int, eid: str, c: dict, steps: list, success: bool) -> dict:
    seed = eid.split("-", 2)[-1] if eid.count("-") >= 2 else eid
    return {
        "id": eid,
        "goal": (
            f"Bind leftover leftover leftover {c['stack'].split(' leftover leftover leftover ', 1)[-1] if ' leftover leftover leftover ' in c['stack'] else c['token']}; do not raise {c['tkey']} to hide lag."
            if success
            else f"Do not {c['wrong']} leftover leftover leftover {c['token']} to hide resume."
        ),
        "plan": (
            f"Read leftover leftover leftover-as-timeout, try 30s, then {c['token']} plus {c['extra']}."
            if success
            else f"Read leftover leftover leftover-as-timeout, try 0s, then hand off {c['wrong'].replace(' ', '-')}."
        ),
        "steps": steps,
        "outcome": (
            f"leftover leftover leftover {c['token']} bound. {c['tkey']} unused (success)."
            if success
            else f"Still timeout-classed; leftover leftover leftover {c['wrong']} is platform — handoff {c['handoff']}."
        ),
        "reward": {
            "success": success,
            "tests_passed": 3 if success else 2,
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
            "stack": c["stack"] if success else f"{c['stack'].split(' leftover leftover leftover ')[0]} leftover leftover leftover {c['wrong']}",
        },
    }


def notes(rnd: int, ok_id: str, fail_id: str, c: dict) -> str:
    return (
        f"# websocket-reconnect-factory — NOTES r{rnd}\n\n"
        f"Novel coverage: leftover leftover leftover {c['token']} vs {c['wrong']}. "
        f"Not r41–r124 clones. Not anycable. Not reverb. Not search-index.\n\n"
        f"## Episodes\n"
        f"- `{ok_id}`: 16 steps, success=True, domain={c['domain_ok']}, seed={ok_id.split('-', 2)[-1]}\n"
        f"  - 502 at step 6 recovered 7; 429 at step 8 recovered 9\n"
        f"  - plan change at step 12: bind leftover leftover leftover {c['token']} plus {c['extra']}. {c['tkey']} is not a leftover leftover leftover bound.\n"
        f"  - edit→test→fail→re-read→fix at steps 10-13\n"
        f"- `{fail_id}`: 17 steps, success=False, domain={c['domain_fail']}, seed={fail_id.split('-', 2)[-1]}\n"
        f"  - 429 at step 6 recovered 7; 502 at step 8 recovered 9 (order may swap with success side)\n"
        f"  - plan change at step 12: {c['wrong_key']} drop is platform. Handoff {c['handoff']}.\n"
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
        f"{c['ban']} {c['tkey']} is not leftover leftover leftover {c['token']}. Cannot {c['wrong']}.\n"
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
        if (DIR / f"ROUND-r{rnd:02d}.reserved.json").exists():
            hop = hop_unreserved()
            print(f"reserved at {rnd}; hop {hop}", file=sys.stderr)
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
        published.append({"round": rnd, "ids": ids, "published": pub.get("round", rnd)})
        print(json.dumps({"published": rnd, "ids": ids}))
    print(json.dumps({"done": published, "failed_round": failed_round}, indent=2))


if __name__ == "__main__":
    main()
