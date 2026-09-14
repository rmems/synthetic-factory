#!/usr/bin/env python3
"""websocket-reconnect leftover leftover leftover mill r141–r156 (16 pairs)."""
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

# Distinct leftover leftover leftover vs r41–r140. BAN r40 anycable / reverb. BAN sir-/dbc-/gql- ids.
# Each: leftover leftover leftover resume token vs timeout stretch (success) / drop-bind handoff (fail).
CATALOG = [
    {
        "mod": "istch",
        "dmod": "istchdrop",
        "slug": "istio-consistent-hash-leftover-vs-drop-subset",
        "fail": "istio-drop-consistent-hash-handoff",
        "stack": "Istio leftover leftover leftover consistentHash",
        "token": "consistentHash",
        "extra": "httpCookie",
        "tkey": "idleTimeout",
        "wrong": "drop subset",
        "wrong_key": "subset",
        "test_ok": "test_consistent_hash_not_idle",
        "test_fail": "test_must_keep_consistent_hash",
        "docs": "https://istio.io/latest/docs/reference/config/networking/destination-rule/",
        "doc2": "https://istio.io/latest/docs/concepts/traffic-management/#load-balancing-options",
        "handoff": "IS-CH-141",
        "domain_ok": "istio-leftover-consistent-hash-vs-idle",
        "domain_fail": "istio-leftover-consistent-hash-drop-vs-idle",
        "ban": "Not cookie-replay. Not destination.host leftover clone. Not anycable/reverb.",
    },
    {
        "mod": "natsdur",
        "dmod": "natsddrop",
        "slug": "nats-js-durable-leftover-vs-drop-inbox",
        "fail": "nats-drop-js-durable-handoff",
        "stack": "NATS leftover leftover leftover durable_name",
        "token": "durable_name",
        "extra": "deliver_policy",
        "tkey": "ack_wait",
        "wrong": "drop inbox",
        "wrong_key": "inbox",
        "test_ok": "test_durable_not_ack_wait",
        "test_fail": "test_must_keep_durable",
        "docs": "https://docs.nats.io/nats-concepts/jetstream/consumers",
        "doc2": "https://docs.nats.io/using-nats/developer/connecting/ws",
        "handoff": "NA-DU-141",
        "domain_ok": "nats-leftover-durable-vs-ack-wait",
        "domain_fail": "nats-leftover-durable-drop-vs-ack-wait",
        "ban": "Not cookie-replay. Not inbox leftover clone. Not anycable/reverb.",
    },
    {
        "mod": "hapck",
        "dmod": "hapckdrop",
        "slug": "haproxy-cookie-serverid-leftover-vs-drop-stick",
        "fail": "haproxy-drop-cookie-serverid-handoff",
        "stack": "HAProxy leftover leftover leftover cookie.SERVERID",
        "token": "cookie.SERVERID",
        "extra": "indirect",
        "tkey": "timeout.tunnel",
        "wrong": "drop stick-table",
        "wrong_key": "stick_table",
        "test_ok": "test_serverid_not_tunnel",
        "test_fail": "test_must_keep_serverid",
        "docs": "https://www.haproxy.com/documentation/haproxy-configuration-manual/latest/#4.2-cookie",
        "doc2": "https://www.haproxy.com/documentation/haproxy-configuration-manual/latest/#4.2-timeout%20tunnel",
        "handoff": "HA-CK-141",
        "domain_ok": "haproxy-leftover-serverid-vs-tunnel",
        "domain_fail": "haproxy-leftover-serverid-drop-vs-tunnel",
        "ban": "Not cookie-replay clone. Not stick-table leftover clone. Not anycable/reverb.",
    },
    {
        "mod": "ngxhsh",
        "dmod": "ngxhdrop",
        "slug": "nginx-hash-consistent-leftover-vs-drop-iphash",
        "fail": "nginx-drop-hash-consistent-handoff",
        "stack": "nginx leftover leftover leftover hash.consistent",
        "token": "hash.consistent",
        "extra": "key",
        "tkey": "proxy_read_timeout",
        "wrong": "drop ip_hash",
        "wrong_key": "ip_hash",
        "test_ok": "test_hash_consistent_not_read",
        "test_fail": "test_must_keep_hash_consistent",
        "docs": "https://nginx.org/en/docs/http/ngx_http_upstream_module.html#hash",
        "doc2": "https://nginx.org/en/docs/http/websocket.html",
        "handoff": "NG-HC-141",
        "domain_ok": "nginx-leftover-hash-consistent-vs-read",
        "domain_fail": "nginx-leftover-hash-consistent-drop-vs-read",
        "ban": "Not cookie-replay. Not http11 leftover clone. Not anycable/reverb.",
    },
    {
        "mod": "trfhb",
        "dmod": "trfhbdrop",
        "slug": "traefik-ws-heartbeat-leftover-vs-drop-sticky",
        "fail": "traefik-drop-ws-heartbeat-handoff",
        "stack": "Traefik leftover leftover leftover websocket.heartbeat",
        "token": "websocket.heartbeat",
        "extra": "serversTransport",
        "tkey": "idleTimeout",
        "wrong": "drop sticky",
        "wrong_key": "sticky",
        "test_ok": "test_ws_heartbeat_not_idle",
        "test_fail": "test_must_keep_ws_heartbeat",
        "docs": "https://doc.traefik.io/traefik/routing/services/",
        "doc2": "https://doc.traefik.io/traefik/middlewares/http/headers/",
        "handoff": "TR-HB-141",
        "domain_ok": "traefik-leftover-ws-heartbeat-vs-idle",
        "domain_fail": "traefik-leftover-ws-heartbeat-drop-vs-idle",
        "ban": "Not cookie-replay. Not sticky.cookie leftover clone. Not anycable/reverb.",
    },
    {
        "mod": "cdylb",
        "dmod": "cdylbdrop",
        "slug": "caddy-lb-cookie-leftover-vs-drop-flush",
        "fail": "caddy-drop-lb-cookie-handoff",
        "stack": "Caddy leftover leftover leftover lb_policy.cookie",
        "token": "lb_policy.cookie",
        "extra": "lb_retries",
        "tkey": "flush_interval",
        "wrong": "drop flush",
        "wrong_key": "flush_interval",
        "test_ok": "test_lb_cookie_not_flush",
        "test_fail": "test_must_keep_lb_cookie",
        "docs": "https://caddyserver.com/docs/caddyfile/directives/reverse_proxy",
        "doc2": "https://caddyserver.com/docs/modules/http.reverse_proxy",
        "handoff": "CD-LB-141",
        "domain_ok": "caddy-leftover-lb-cookie-vs-flush",
        "domain_fail": "caddy-leftover-lb-cookie-drop-vs-flush",
        "ban": "Not cookie-replay clone. Not subprotocol leftover clone. Not anycable/reverb.",
    },
    {
        "mod": "sjsid",
        "dmod": "sjsiddrop",
        "slug": "sockjs-server-id-leftover-vs-drop-heartbeat",
        "fail": "sockjs-drop-server-id-handoff",
        "stack": "SockJS leftover leftover leftover server_id",
        "token": "server_id",
        "extra": "session_id",
        "tkey": "heartbeatDelay",
        "wrong": "drop heartbeat",
        "wrong_key": "heartbeat",
        "test_ok": "test_server_id_not_heartbeat",
        "test_fail": "test_must_keep_server_id",
        "docs": "https://github.com/sockjs/sockjs-protocol",
        "doc2": "https://github.com/sockjs/sockjs-client",
        "handoff": "SJ-SID-141",
        "domain_ok": "sockjs-leftover-server-id-vs-heartbeat",
        "domain_fail": "sockjs-leftover-server-id-drop-vs-heartbeat",
        "ban": "Not cookie-replay. Not iframe leftover clone. Not anycable/reverb.",
    },
    {
        "mod": "scsat",
        "dmod": "scsatdrop",
        "slug": "socketcluster-signed-auth-leftover-vs-drop-cid",
        "fail": "socketcluster-drop-signed-auth-handoff",
        "stack": "SocketCluster leftover leftover leftover signedAuthToken",
        "token": "signedAuthToken",
        "extra": "authState",
        "tkey": "ackTimeout",
        "wrong": "drop cid",
        "wrong_key": "cid",
        "test_ok": "test_signed_auth_not_ack",
        "test_fail": "test_must_keep_signed_auth",
        "docs": "https://socketcluster.io/docs/authentication/",
        "doc2": "https://socketcluster.io/docs/basic-usage/",
        "handoff": "SC-SA-141",
        "domain_ok": "socketcluster-leftover-signed-auth-vs-ack",
        "domain_fail": "socketcluster-leftover-signed-auth-drop-vs-ack",
        "ban": "Not cookie-replay. Not cid leftover clone. Not anycable/reverb.",
    },
    {
        "mod": "nchmid",
        "dmod": "nchmdrop",
        "slug": "nchan-message-id-leftover-vs-drop-last-event",
        "fail": "nchan-drop-message-id-handoff",
        "stack": "nchan leftover leftover leftover message_id",
        "token": "message_id",
        "extra": "etag",
        "tkey": "subscriber_timeout",
        "wrong": "drop last-event-id",
        "wrong_key": "last_event_id",
        "test_ok": "test_message_id_not_subscriber",
        "test_fail": "test_must_keep_message_id",
        "docs": "https://nchan.io/",
        "doc2": "https://github.com/slact/nchan",
        "handoff": "NC-MID-141",
        "domain_ok": "nchan-leftover-message-id-vs-subscriber",
        "domain_fail": "nchan-leftover-message-id-drop-vs-subscriber",
        "ban": "Not cookie-replay. Not last-event-id leftover clone. Not anycable/reverb.",
    },
    {
        "mod": "wsext",
        "dmod": "wsextdrop",
        "slug": "ws-permessage-deflate-leftover-vs-drop-ping",
        "fail": "ws-drop-permessage-deflate-handoff",
        "stack": "ws leftover leftover leftover permessage-deflate",
        "token": "permessage-deflate",
        "extra": "client_no_context_takeover",
        "tkey": "pingInterval",
        "wrong": "drop ping",
        "wrong_key": "ping",
        "test_ok": "test_deflate_not_ping",
        "test_fail": "test_must_keep_deflate",
        "docs": "https://datatracker.ietf.org/doc/html/rfc7692",
        "doc2": "https://github.com/websockets/ws",
        "handoff": "WS-PD-141",
        "domain_ok": "ws-leftover-deflate-vs-ping",
        "domain_fail": "ws-leftover-deflate-drop-vs-ping",
        "ban": "Not cookie-replay. Not opcode leftover clone. Not anycable/reverb.",
    },
    {
        "mod": "mqsubid",
        "dmod": "mqsubiddrop",
        "slug": "mqtt-sub-identifier-leftover-vs-drop-packet",
        "fail": "mqtt-drop-sub-identifier-handoff",
        "stack": "MQTT leftover leftover leftover SubscriptionIdentifier",
        "token": "SubscriptionIdentifier",
        "extra": "UserProperty",
        "tkey": "keepAlive",
        "wrong": "drop packetId",
        "wrong_key": "packetId",
        "test_ok": "test_sub_identifier_not_keepalive",
        "test_fail": "test_must_keep_sub_identifier",
        "docs": "https://docs.oasis-open.org/mqtt/mqtt/v5.0/os/mqtt-v5.0-os.html#_Toc3901117",
        "doc2": "https://docs.oasis-open.org/mqtt/mqtt/v5.0/os/mqtt-v5.0-os.html#_Toc3901169",
        "handoff": "MQ-SI-141",
        "domain_ok": "mqtt-leftover-sub-identifier-vs-keepalive",
        "domain_fail": "mqtt-leftover-sub-identifier-drop-vs-keepalive",
        "ban": "Not cookie-replay. Not packet-id leftover clone. Not anycable/reverb.",
    },
    {
        "mod": "stack",
        "dmod": "stackdrop",
        "slug": "stomp-ack-header-leftover-vs-drop-transaction",
        "fail": "stomp-drop-ack-header-handoff",
        "stack": "STOMP leftover leftover leftover ack",
        "token": "ack",
        "extra": "id",
        "tkey": "heartbeat",
        "wrong": "drop transaction",
        "wrong_key": "transaction",
        "test_ok": "test_ack_not_heartbeat",
        "test_fail": "test_must_keep_ack",
        "docs": "https://stomp.github.io/stomp-specification-1.2.html#SUBSCRIBE",
        "doc2": "https://stomp.github.io/stomp-specification-1.2.html#ACK",
        "handoff": "ST-ACK-141",
        "domain_ok": "stomp-leftover-ack-vs-heartbeat",
        "domain_fail": "stomp-leftover-ack-drop-vs-heartbeat",
        "ban": "Not cookie-replay. Not transaction leftover clone. Not anycable/reverb.",
    },
    {
        "mod": "pksza",
        "dmod": "pkszadrop",
        "slug": "partykit-serialize-attachment-leftover-vs-drop-attachment",
        "fail": "partykit-drop-serialize-attachment-handoff",
        "stack": "PartyKit leftover leftover leftover serializeAttachment",
        "token": "serializeAttachment",
        "extra": "deserializeAttachment",
        "tkey": "hibernateAfter",
        "wrong": "drop attachment",
        "wrong_key": "attachment",
        "test_ok": "test_serialize_not_hibernate",
        "test_fail": "test_must_keep_serialize",
        "docs": "https://docs.partykit.io/guides/scaling-partykit-servers-with-hibernation/",
        "doc2": "https://docs.partykit.io/reference/partyserver-api/#serializeattachment",
        "handoff": "PK-SA-141",
        "domain_ok": "partykit-leftover-serialize-vs-hibernate",
        "domain_fail": "partykit-leftover-serialize-drop-vs-hibernate",
        "ban": "Not cookie-replay. Not attachment leftover clone. Not anycable/reverb.",
    },
    {
        "mod": "cfhib",
        "dmod": "cfhibdrop",
        "slug": "cloudflare-hibernate-websocket-leftover-vs-drop-wstag",
        "fail": "cloudflare-drop-hibernate-websocket-handoff",
        "stack": "Cloudflare Durable leftover leftover leftover hibernateWebSocket",
        "token": "hibernateWebSocket",
        "extra": "getWebSockets",
        "tkey": "idleTimeout",
        "wrong": "drop wsTag",
        "wrong_key": "wsTag",
        "test_ok": "test_hibernate_ws_not_idle",
        "test_fail": "test_must_keep_hibernate_ws",
        "docs": "https://developers.cloudflare.com/durable-objects/best-practices/websockets/",
        "doc2": "https://developers.cloudflare.com/durable-objects/api/state/#getwebsockets",
        "handoff": "CF-HW-141",
        "domain_ok": "cfdo-leftover-hibernate-ws-vs-idle",
        "domain_fail": "cfdo-leftover-hibernate-ws-drop-vs-idle",
        "ban": "Not cookie-replay. Not wsTag leftover clone. Not anycable/reverb.",
    },
    {
        "mod": "kghsh",
        "dmod": "kghshdrop",
        "slug": "kong-hash-on-leftover-vs-drop-sticky",
        "fail": "kong-drop-hash-on-handoff",
        "stack": "Kong leftover leftover leftover hash_on",
        "token": "hash_on",
        "extra": "hash_fallback",
        "tkey": "timeouts.connect",
        "wrong": "drop sticky.cookie",
        "wrong_key": "sticky.cookie",
        "test_ok": "test_hash_on_not_connect",
        "test_fail": "test_must_keep_hash_on",
        "docs": "https://docs.konghq.com/gateway/latest/kong-plugins/load-balancing/",
        "doc2": "https://docs.konghq.com/gateway/latest/reference/proxy/",
        "handoff": "KG-HO-141",
        "domain_ok": "kong-leftover-hash-on-vs-connect",
        "domain_fail": "kong-leftover-hash-on-drop-vs-connect",
        "ban": "Not cookie-replay. Not sticky.cookie leftover clone. Not anycable/reverb.",
    },
    {
        "mod": "envhp",
        "dmod": "envhpdrop",
        "slug": "envoy-hash-policy-leftover-vs-drop-upgrade",
        "fail": "envoy-drop-hash-policy-handoff",
        "stack": "Envoy leftover leftover leftover hash_policy",
        "token": "hash_policy",
        "extra": "consistent_hashing_lb_config",
        "tkey": "idle_timeout",
        "wrong": "drop upgrade_configs",
        "wrong_key": "upgrade_configs",
        "test_ok": "test_hash_policy_not_idle",
        "test_fail": "test_must_keep_hash_policy",
        "docs": "https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/load_balancing/load_balancers",
        "doc2": "https://www.envoyproxy.io/docs/envoy/latest/api-v3/config/route/v3/route_components.proto",
        "handoff": "EN-HP-141",
        "domain_ok": "envoy-leftover-hash-policy-vs-idle",
        "domain_fail": "envoy-leftover-hash-policy-drop-vs-idle",
        "ban": "Not cookie-replay. Not upgrade_configs leftover clone. Not anycable/reverb.",
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
        f"Not r41–r140 clones. Not anycable. Not reverb. Not search-index.\n\n"
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


def used_slugs() -> set[str]:
    used: set[str] = set()
    for npath in DIR.glob("NOTES-r*.md"):
        for line in npath.read_text().splitlines():
            if line.startswith("- `wsr-r"):
                used.add(line.split("`")[1].split("-", 2)[-1])
    return used


def main() -> None:
    published = []
    failed_round = None
    fr = _cmd(TXN + ["frontier", str(DIR)])
    start = int(fr["next_round"])
    if (DIR / f"ROUND-r{start:02d}.reserved.json").exists():
        hop = hop_unreserved()
        print(f"reserved at {start}; hop {hop}", file=sys.stderr)
        raise SystemExit(2)
    remaining = [c for c in CATALOG if c["slug"] not in used_slugs() and c["fail"] not in used_slugs()]
    for i, c in enumerate(remaining):
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
