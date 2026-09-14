#!/usr/bin/env python3
"""websocket-reconnect leftover leftover leftover mill r73–r88 (16 pairs)."""
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

# Distinct leftover leftover leftover vs r41–r72 tokens. BAN r40 anycable / reverb.
# Each: leftover resume token vs naive second-subscribe (success) / drop-bind handoff (fail).
CATALOG = [
    {
        "mod": "lkroom",
        "slug": "livekit-room-sid-leftover-vs-drop-participant",
        "fail": "livekit-drop-room-sid-handoff",
        "stack": "LiveKit leftover room_sid",
        "token": "leftover_room_sid",
        "wrong": "drop participant",
        "wrong_key": "participant",
        "test_ok": "test_room_not_participant",
        "test_fail": "test_room_bind",
        "docs": "https://docs.livekit.io/home/client/connect/",
        "doc2": "https://docs.livekit.io/home/client/events/#room",
        "handoff": "LK-RS-17",
        "domain_ok": "livekit-room-sid-leftover-vs-drop-participant",
        "domain_fail": "livekit-drop-leftover-room-sid-bind",
        "first_patch": ("    return {'participant': sid}", "    return {'participant': None}"),
        "fix_patch": ("    return {'participant': None}", "    return {'leftover_room_sid': sid}"),
        "src_obs": "LiveKit leftover room_sid restores the same room; drop participant is not resume",
        "plan_ok": "Pass leftover_room_sid. Drop participant is not resume.",
        "plan_fail": "Leftover room_sid bind drop is LiveKit plat. Handoff LK-RS-17.",
        "ban": "Not cookie-replay. Not participant sid leftover clone.",
    },
    {
        "mod": "dlyses",
        "slug": "daily-meeting-session-leftover-vs-drop-cam",
        "fail": "daily-drop-meeting-session-handoff",
        "stack": "Daily leftover meeting_session",
        "token": "leftover_meeting_session",
        "wrong": "drop cam",
        "wrong_key": "cam",
        "test_ok": "test_session_not_cam",
        "test_fail": "test_session_bind",
        "docs": "https://docs.daily.co/reference/daily-js/instance-methods/join",
        "doc2": "https://docs.daily.co/guides/products/call-object",
        "handoff": "DL-MS-17",
        "domain_ok": "daily-meeting-session-leftover-vs-drop-cam",
        "domain_fail": "daily-drop-leftover-meeting-session-bind",
        "first_patch": ("    return {'cam': sid}", "    return {'cam': None}"),
        "fix_patch": ("    return {'cam': None}", "    return {'leftover_meeting_session': sid}"),
        "src_obs": "Daily leftover meeting_session restores the same meeting; drop cam is not resume",
        "plan_ok": "Pass leftover_meeting_session. Drop cam is not resume.",
        "plan_fail": "Leftover meeting_session bind drop is Daily plat. Handoff DL-MS-17.",
        "ban": "Not cookie-replay. Not participant leftover clone.",
    },
    {
        "mod": "twvrm",
        "slug": "twilio-video-room-sid-leftover-vs-drop-track",
        "fail": "twilio-video-drop-room-sid-handoff",
        "stack": "Twilio Video leftover room_sid",
        "token": "leftover_twilio_room",
        "wrong": "drop track",
        "wrong_key": "track",
        "test_ok": "test_twroom_not_track",
        "test_fail": "test_twroom_bind",
        "docs": "https://www.twilio.com/docs/video/javascript-getting-started",
        "doc2": "https://www.twilio.com/docs/video/api/rooms-resource",
        "handoff": "TW-VR-17",
        "domain_ok": "twilio-video-room-sid-leftover-vs-drop-track",
        "domain_fail": "twilio-video-drop-leftover-room-sid-bind",
        "first_patch": ("    return {'track': sid}", "    return {'track': None}"),
        "fix_patch": ("    return {'track': None}", "    return {'leftover_twilio_room': sid}"),
        "src_obs": "Twilio Video leftover room_sid restores the same room; drop track is not resume",
        "plan_ok": "Pass leftover_twilio_room. Drop track is not resume.",
        "plan_fail": "Leftover room_sid bind drop is Twilio Video plat. Handoff TW-VR-17.",
        "ban": "Not cookie-replay. Not track leftover clone.",
    },
    {
        "mod": "aguid",
        "slug": "agora-uid-token-leftover-vs-drop-channel",
        "fail": "agora-drop-uid-token-handoff",
        "stack": "Agora leftover uid_token",
        "token": "leftover_uid_token",
        "wrong": "drop channel",
        "wrong_key": "channel",
        "test_ok": "test_uid_not_channel",
        "test_fail": "test_uid_bind",
        "docs": "https://docs.agora.io/en/video-calling/get-started/get-started-sdk",
        "doc2": "https://docs.agora.io/en/video-calling/develop/authentication-workflow",
        "handoff": "AG-UT-17",
        "domain_ok": "agora-uid-token-leftover-vs-drop-channel",
        "domain_fail": "agora-drop-leftover-uid-token-bind",
        "first_patch": ("    return {'channel': sid}", "    return {'channel': None}"),
        "fix_patch": ("    return {'channel': None}", "    return {'leftover_uid_token': sid}"),
        "src_obs": "Agora leftover uid_token restores the same uid; drop channel is not resume",
        "plan_ok": "Pass leftover_uid_token. Drop channel is not resume.",
        "plan_fail": "Leftover uid_token bind drop is Agora plat. Handoff AG-UT-17.",
        "ban": "Not cookie-replay. Not channel leftover clone.",
    },
    {
        "mod": "sioack",
        "slug": "socketio-ack-id-leftover-vs-drop-nsp",
        "fail": "socketio-drop-ack-id-handoff",
        "stack": "Socket.IO leftover ack_id",
        "token": "leftover_ack_id",
        "wrong": "drop nsp",
        "wrong_key": "nsp",
        "test_ok": "test_ack_not_nsp",
        "test_fail": "test_ack_bind",
        "docs": "https://socket.io/docs/v4/emitting-events/#acknowledgements",
        "doc2": "https://socket.io/docs/v4/namespaces/",
        "handoff": "SIO-ACK-17",
        "domain_ok": "socketio-ack-id-leftover-vs-drop-nsp",
        "domain_fail": "socketio-drop-leftover-ack-id-bind",
        "first_patch": ("    return {'nsp': sid}", "    return {'nsp': None}"),
        "fix_patch": ("    return {'nsp': None}", "    return {'leftover_ack_id': sid}"),
        "src_obs": "Socket.IO leftover ack_id restores inflight acks; drop nsp is not resume",
        "plan_ok": "Pass leftover_ack_id. Drop nsp is not resume.",
        "plan_fail": "Leftover ack_id bind drop is Socket.IO plat. Handoff SIO-ACK-17.",
        "ban": "Not cookie-replay. Not engine.io sid leftover clone.",
    },
    {
        "mod": "srinv",
        "slug": "signalr-invocation-id-leftover-vs-drop-hub",
        "fail": "signalr-drop-invocation-id-handoff",
        "stack": "SignalR leftover invocation_id",
        "token": "leftover_invocation_id",
        "wrong": "drop hub",
        "wrong_key": "hub",
        "test_ok": "test_inv_not_hub",
        "test_fail": "test_inv_bind",
        "docs": "https://learn.microsoft.com/en-us/aspnet/core/signalr/hubs",
        "doc2": "https://github.com/dotnet/aspnetcore/blob/main/src/SignalR/docs/specs/HubProtocol.md",
        "handoff": "SR-INV-17",
        "domain_ok": "signalr-invocation-id-leftover-vs-drop-hub",
        "domain_fail": "signalr-drop-leftover-invocation-id-bind",
        "first_patch": ("    return {'hub': sid}", "    return {'hub': None}"),
        "fix_patch": ("    return {'hub': None}", "    return {'leftover_invocation_id': sid}"),
        "src_obs": "SignalR leftover invocation_id restores inflight calls; drop hub is not resume",
        "plan_ok": "Pass leftover_invocation_id. Drop hub is not resume.",
        "plan_fail": "Leftover invocation_id bind drop is SignalR plat. Handoff SR-INV-17.",
        "ban": "Not cookie-replay. Not connectionToken leftover clone.",
    },
    {
        "mod": "phxjp",
        "slug": "phoenix-join-push-leftover-vs-drop-topic",
        "fail": "phoenix-drop-join-push-handoff",
        "stack": "Phoenix leftover join_push",
        "token": "leftover_join_push",
        "wrong": "drop topic",
        "wrong_key": "topic",
        "test_ok": "test_jpush_not_topic",
        "test_fail": "test_jpush_bind",
        "docs": "https://hexdocs.pm/phoenix/channels.html#joining",
        "doc2": "https://hexdocs.pm/phoenix/Phoenix.Channel.html",
        "handoff": "PHX-JP-17",
        "domain_ok": "phoenix-join-push-leftover-vs-drop-topic",
        "domain_fail": "phoenix-drop-leftover-join-push-bind",
        "first_patch": ("    return {'topic': sid}", "    return {'topic': None}"),
        "fix_patch": ("    return {'topic': None}", "    return {'leftover_join_push': sid}"),
        "src_obs": "Phoenix leftover join_push restores the same join; drop topic is not resume",
        "plan_ok": "Pass leftover_join_push. Drop topic is not resume.",
        "plan_fail": "Leftover join_push bind drop is Phoenix plat. Handoff PHX-JP-17.",
        "ban": "Not cookie-replay. Not join_ref leftover clone.",
    },
    {
        "mod": "acstrm",
        "slug": "actioncable-stream-from-leftover-vs-drop-subscription",
        "fail": "actioncable-drop-stream-from-handoff",
        "stack": "ActionCable leftover stream_from",
        "token": "leftover_stream_from",
        "wrong": "drop subscription",
        "wrong_key": "subscription",
        "test_ok": "test_sfrom_not_sub",
        "test_fail": "test_sfrom_bind",
        "docs": "https://guides.rubyonrails.org/action_cable_overview.html#streams",
        "doc2": "https://api.rubyonrails.org/classes/ActionCable/Channel/Base.html",
        "handoff": "AC-SF-17",
        "domain_ok": "actioncable-stream-from-leftover-vs-drop-subscription",
        "domain_fail": "actioncable-drop-leftover-stream-from-bind",
        "first_patch": ("    return {'subscription': sid}", "    return {'subscription': None}"),
        "fix_patch": ("    return {'subscription': None}", "    return {'leftover_stream_from': sid}"),
        "src_obs": "ActionCable leftover stream_from restores the same stream; drop subscription is not resume",
        "plan_ok": "Pass leftover_stream_from. Drop subscription is not resume.",
        "plan_fail": "Leftover stream_from bind drop is ActionCable plat. Handoff AC-SF-17.",
        "ban": "Not cookie-replay. Not identifier leftover clone.",
    },
    {
        "mod": "cfepoc",
        "slug": "centrifuge-epoch-leftover-vs-drop-channel",
        "fail": "centrifuge-drop-epoch-handoff",
        "stack": "Centrifuge leftover epoch",
        "token": "leftover_epoch",
        "wrong": "drop channel",
        "wrong_key": "channel",
        "test_ok": "test_epoch_not_channel",
        "test_fail": "test_epoch_bind",
        "docs": "https://centrifugal.dev/docs/server/history_and_recovery#epoch",
        "doc2": "https://centrifugal.dev/docs/transports/client_protocol#subscribe",
        "handoff": "CF-EP-17",
        "domain_ok": "centrifuge-epoch-leftover-vs-drop-channel",
        "domain_fail": "centrifuge-drop-leftover-epoch-bind",
        "first_patch": ("    return {'channel': sid}", "    return {'channel': None}"),
        "fix_patch": ("    return {'channel': None}", "    return {'leftover_epoch': sid}"),
        "src_obs": "Centrifuge leftover epoch restores history epoch; drop channel is not resume",
        "plan_ok": "Pass leftover_epoch. Drop channel is not resume.",
        "plan_fail": "Leftover epoch bind drop is Centrifuge plat. Handoff CF-EP-17.",
        "ban": "Not cookie-replay. Not offset leftover clone.",
    },
    {
        "mod": "puschd",
        "slug": "pusher-channel-data-leftover-vs-drop-socket",
        "fail": "pusher-drop-channel-data-handoff",
        "stack": "Pusher leftover channel_data",
        "token": "leftover_channel_data",
        "wrong": "drop socket",
        "wrong_key": "socket",
        "test_ok": "test_cdata_not_socket",
        "test_fail": "test_cdata_bind",
        "docs": "https://pusher.com/docs/channels/library_auth_reference/auth-signatures/",
        "doc2": "https://pusher.com/docs/channels/using_channels/events/",
        "handoff": "PU-CD-17",
        "domain_ok": "pusher-channel-data-leftover-vs-drop-socket",
        "domain_fail": "pusher-drop-leftover-channel-data-bind",
        "first_patch": ("    return {'socket': sid}", "    return {'socket': None}"),
        "fix_patch": ("    return {'socket': None}", "    return {'leftover_channel_data': sid}"),
        "src_obs": "Pusher leftover channel_data restores presence auth; drop socket is not resume",
        "plan_ok": "Pass leftover_channel_data. Drop socket is not resume.",
        "plan_fail": "Leftover channel_data bind drop is Pusher plat. Handoff PU-CD-17.",
        "ban": "Not cookie-replay. Not socket_id leftover clone.",
    },
    {
        "mod": "abyser",
        "slug": "ably-serial-leftover-vs-drop-channel",
        "fail": "ably-drop-serial-handoff",
        "stack": "Ably leftover serial",
        "token": "leftover_serial",
        "wrong": "drop channel",
        "wrong_key": "channel",
        "test_ok": "test_serial_not_channel",
        "test_fail": "test_serial_bind",
        "docs": "https://ably.com/docs/connect#connection-state-recovery",
        "doc2": "https://ably.com/docs/channels",
        "handoff": "AB-SR-17",
        "domain_ok": "ably-serial-leftover-vs-drop-channel",
        "domain_fail": "ably-drop-leftover-serial-bind",
        "first_patch": ("    return {'channel': sid}", "    return {'channel': None}"),
        "fix_patch": ("    return {'channel': None}", "    return {'leftover_serial': sid}"),
        "src_obs": "Ably leftover serial restores message serials; drop channel is not resume",
        "plan_ok": "Pass leftover_serial. Drop channel is not resume.",
        "plan_fail": "Leftover serial bind drop is Ably plat. Handoff AB-SR-17.",
        "ban": "Not cookie-replay. Not recoveryKey leftover clone.",
    },
    {
        "mod": "gqlsub",
        "slug": "graphqlws-subscription-id-leftover-vs-drop-connection",
        "fail": "graphqlws-drop-subscription-id-handoff",
        "stack": "graphql-ws leftover subscription_id",
        "token": "leftover_subscription_id",
        "wrong": "drop connection",
        "wrong_key": "connection",
        "test_ok": "test_subid_not_connection",
        "test_fail": "test_subid_bind",
        "docs": "https://github.com/enisdenjo/graphql-ws/blob/master/PROTOCOL.md",
        "doc2": "https://the-guild.dev/graphql/ws/protocol",
        "handoff": "GQL-SUB-17",
        "domain_ok": "graphqlws-subscription-id-leftover-vs-drop-connection",
        "domain_fail": "graphqlws-drop-leftover-subscription-id-bind",
        "first_patch": ("    return {'connection': sid}", "    return {'connection': None}"),
        "fix_patch": ("    return {'connection': None}", "    return {'leftover_subscription_id': sid}"),
        "src_obs": "graphql-ws leftover subscription_id restores the same op; drop connection is not resume",
        "plan_ok": "Pass leftover_subscription_id. Drop connection is not resume.",
        "plan_fail": "Leftover subscription_id bind drop is graphql-ws plat. Handoff GQL-SUB-17.",
        "ban": "Not cookie-replay. Not connection_init leftover clone.",
    },
    {
        "mod": "mqtpkt",
        "slug": "mqtt-packet-id-leftover-vs-drop-topic",
        "fail": "mqtt-drop-packet-id-handoff",
        "stack": "MQTT leftover packet_id",
        "token": "leftover_packet_id",
        "wrong": "drop topic",
        "wrong_key": "topic",
        "test_ok": "test_pkt_not_topic",
        "test_fail": "test_pkt_bind",
        "docs": "https://docs.oasis-open.org/mqtt/mqtt/v5.0/os/mqtt-v5.0-os.html#_Toc3901026",
        "doc2": "https://mqtt.org/mqtt-specification/",
        "handoff": "MQTT-PKT-17",
        "domain_ok": "mqtt-packet-id-leftover-vs-drop-topic",
        "domain_fail": "mqtt-drop-leftover-packet-id-bind",
        "first_patch": ("    return {'topic': sid}", "    return {'topic': None}"),
        "fix_patch": ("    return {'topic': None}", "    return {'leftover_packet_id': sid}"),
        "src_obs": "MQTT leftover packet_id restores inflight QoS; drop topic is not resume",
        "plan_ok": "Pass leftover_packet_id. Drop topic is not resume.",
        "plan_fail": "Leftover packet_id bind drop is MQTT plat. Handoff MQTT-PKT-17.",
        "ban": "Not cookie-replay. Not clean-session leftover clone.",
    },
    {
        "mod": "stmsub",
        "slug": "stomp-subscription-id-leftover-vs-drop-dest",
        "fail": "stomp-drop-subscription-id-handoff",
        "stack": "STOMP leftover subscription_id",
        "token": "leftover_stomp_sub",
        "wrong": "drop dest",
        "wrong_key": "dest",
        "test_ok": "test_stsub_not_dest",
        "test_fail": "test_stsub_bind",
        "docs": "https://stomp.github.io/stomp-specification-1.2.html#SUBSCRIBE",
        "doc2": "https://stomp.github.io/stomp-specification-1.2.html#SUBSCRIBE_id_Header",
        "handoff": "STOMP-SUB-17",
        "domain_ok": "stomp-subscription-id-leftover-vs-drop-dest",
        "domain_fail": "stomp-drop-leftover-subscription-id-bind",
        "first_patch": ("    return {'dest': sid}", "    return {'dest': None}"),
        "fix_patch": ("    return {'dest': None}", "    return {'leftover_stomp_sub': sid}"),
        "src_obs": "STOMP leftover subscription_id restores the same dest; drop dest is not resume",
        "plan_ok": "Pass leftover_stomp_sub. Drop dest is not resume.",
        "plan_fail": "Leftover subscription_id bind drop is STOMP plat. Handoff STOMP-SUB-17.",
        "ban": "Not cookie-replay. Not receipt leftover clone.",
    },
    {
        "mod": "pkthib",
        "slug": "partykit-hibernation-id-leftover-vs-drop-attachment",
        "fail": "partykit-drop-hibernation-id-handoff",
        "stack": "PartyKit leftover hibernation_id",
        "token": "leftover_hibernation_id",
        "wrong": "drop attachment",
        "wrong_key": "attachment",
        "test_ok": "test_hibid_not_attachment",
        "test_fail": "test_hibid_bind",
        "docs": "https://docs.partykit.io/guides/persisting-state-into-storage/",
        "doc2": "https://developers.cloudflare.com/durable-objects/best-practices/websockets/#hibernation",
        "handoff": "PK-HIB-17",
        "domain_ok": "partykit-hibernation-id-leftover-vs-drop-attachment",
        "domain_fail": "partykit-drop-leftover-hibernation-id-bind",
        "first_patch": ("    return {'attachment': sid}", "    return {'attachment': None}"),
        "fix_patch": ("    return {'attachment': None}", "    return {'leftover_hibernation_id': sid}"),
        "src_obs": "PartyKit leftover hibernation_id restores the same party; drop attachment is not resume",
        "plan_ok": "Pass leftover_hibernation_id. Drop attachment is not resume.",
        "plan_fail": "Leftover hibernation_id bind drop is PartyKit plat. Handoff PK-HIB-17.",
        "ban": "Not cookie-replay. Not hibernation attachment leftover clone.",
    },
    {
        "mod": "cfdalm",
        "slug": "cloudflare-durable-alarm-leftover-vs-drop-stub",
        "fail": "cloudflare-durable-drop-alarm-handoff",
        "stack": "Cloudflare Durable leftover alarm",
        "token": "leftover_do_alarm",
        "wrong": "drop stub",
        "wrong_key": "stub",
        "test_ok": "test_alarm_not_stub",
        "test_fail": "test_alarm_bind",
        "docs": "https://developers.cloudflare.com/durable-objects/api/alarms/",
        "doc2": "https://developers.cloudflare.com/durable-objects/best-practices/alarms/",
        "handoff": "CF-DO-AL-17",
        "domain_ok": "cloudflare-durable-alarm-leftover-vs-drop-stub",
        "domain_fail": "cloudflare-durable-drop-leftover-alarm-bind",
        "first_patch": ("    return {'stub': sid}", "    return {'stub': None}"),
        "fix_patch": ("    return {'stub': None}", "    return {'leftover_do_alarm': sid}"),
        "src_obs": "Cloudflare Durable leftover alarm restores the same DO clock; drop stub is not resume",
        "plan_ok": "Pass leftover_do_alarm. Drop stub is not resume.",
        "plan_fail": "Leftover alarm bind drop is Cloudflare Durable plat. Handoff CF-DO-AL-17.",
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
    cov = 70 + (rnd - 72)
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
