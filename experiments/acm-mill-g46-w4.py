#!/usr/bin/env python3
"""Seventh leftover unique ACM catalog after g46-w3 exhausts at r3786."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("acm_w3", HERE / "acm-mill-g46-w3.py")
_w3 = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_w3)

ok = _w3.ok
bad = _w3.bad
GEN = _w3.GEN
BANNED_BLOB = _w3.BANNED_BLOB
BANNED_SLUG_NEEDLES = _w3.BANNED_SLUG_NEEDLES
build_episode = _w3.build_episode
notes_text = _w3.notes_text
published_slugs = _w3.published_slugs
OAS = _w3.OAS
JS = _w3.JS

BANNED_PRIOR = set(_w3.BANNED_PRIOR)
BANNED_PRIOR |= {p[0]["slug"] for p in _w3.PAIRS} | {p[1]["slug"] for p in _w3.PAIRS}

PAIRS: list[tuple[dict, dict]] = [
    (
        ok(slug="sf-byte-sequence", domain="sf-byte-sequence-vs-base64-header", name="sfbyte", field="Sig",
           old="base64 leftover header", new="sf Byte Sequence :...:",
           fail_err="400: leftover raw base64 after sf-bytes-only",
           plan="sf-bytes-only 400s leftover raw base64. Abandon exclusive Byte Sequence; dual-read raw base64 for one release.",
           residual="signer still raw; drop after signer 4",
           vs="r3587 ratelimit-policy-header (sf Byte Sequence, not RateLimit)",
           fetch1="https://www.rfc-editor.org/rfc/rfc8941.html#name-byte-sequences",
           fetch1_ok="sf Byte Sequences are colon-wrapped.",
           fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive sf bytes 400s leftover raw base64."),
        bad(slug="base64-header-leftover", domain="raw-base64-vs-sf-byte-sequence", name="b64h", field="Sig",
            old="sf Byte Sequence leftover", new="raw base64 only",
            fail_err="400: leftover :bytes: after raw-base64-only",
            plan="raw-base64-only 400s leftover sf bytes. Abandon exclusive raw; keep sf — gateway wants raw. Freeze sf, spec raw.",
            residual="handoff: keep sf bytes or force raw; do not claim raw-base64 shipped",
            vs="r3587 ratelimit-policy-header (raw base64 leftover, not RateLimit)",
            fetch1="https://www.rfc-editor.org/rfc/rfc4648.html",
            fetch1_ok="Raw base64 is not an sf Byte Sequence.",
            fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive raw 400s leftover sf bytes."),
    ),
    (
        ok(slug="sec-ch-prefers-color", domain="sec-ch-prefers-color-vs-cookie-theme", name="chcolor", field="Sec-CH-Prefers-Color-Scheme",
           old="cookie leftover theme", new="Sec-CH-Prefers-Color-Scheme dark",
           fail_err="400: leftover cookie theme after CH-only",
           plan="CH-only 400s leftover cookie. Abandon exclusive CH; dual-read cookie theme for one release.",
           residual="SPA still cookie; drop after spa 2",
           vs="r3620 critical-ch-ua (prefers-color-scheme CH, not Critical-CH)",
           fetch1="https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Sec-CH-Prefers-Color-Scheme",
           fetch1_ok="Sec-CH-Prefers-Color-Scheme is a client hint.",
           fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive CH 400s leftover cookie themes."),
        bad(slug="cookie-theme-leftover", domain="cookie-theme-vs-sec-ch-prefers-color", name="ckthm", field="theme",
            old="CH leftover dark", new="theme cookie only",
            fail_err="400: leftover CH after cookie-only",
            plan="cookie-only 400s leftover CH. Abandon exclusive cookie; keep CH — SSR wants cookie. Freeze CH, spec cookie.",
            residual="handoff: keep CH or force cookie; do not claim cookie-theme shipped",
            vs="r3620 critical-ch-ua (cookie theme leftover, not Critical-CH)",
            fetch1="https://www.rfc-editor.org/rfc/rfc6265.html",
            fetch1_ok="A theme cookie is not a client hint.",
            fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive cookie 400s leftover CH."),
    ),
    (
        ok(slug="device-memory-hint", domain="device-memory-hint-vs-none", name="devmem", field="Device-Memory",
           old="no-Device-Memory leftover", new="Device-Memory 8",
           fail_err="400: leftover missing Device-Memory after required",
           plan="Device-Memory-required 400s leftover missing. Abandon exclusive hint; dual-accept missing for one release.",
           residual="desktop still missing; drop after desktop 3",
           vs="r3620 critical-ch-ua (Device-Memory, not Critical-CH)",
           fetch1="https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Device-Memory",
           fetch1_ok="Device-Memory reports approximate GiB.",
           fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive Device-Memory 400s leftover omitters."),
        bad(slug="no-device-memory", domain="no-device-memory-vs-required", name="ndevm", field="Device-Memory",
            old="8 leftover", new="no Device-Memory",
            fail_err="400: leftover Device-Memory after none-only",
            plan="none-only 400s leftover Device-Memory. Abandon exclusive omit; keep hint — lite wants omit. Freeze hint, spec omit.",
            residual="handoff: keep Device-Memory or force omit; do not claim none shipped",
            vs="r3620 critical-ch-ua (no Device-Memory leftover, not Critical-CH)",
            fetch1="https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Device-Memory",
            fetch1_ok="Omitting Device-Memory is not the 8 GiB hint.",
            fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive omit 400s leftover Device-Memory."),
    ),
    (
        ok(slug="csp-upgrade-insecure", domain="csp-upgrade-insecure-vs-mixed-content", name="cspupg", field="Content-Security-Policy",
           old="mixed leftover http", new="upgrade-insecure-requests",
           fail_err="400: leftover mixed http after upgrade-only",
           plan="upgrade-only 400s leftover mixed. Abandon exclusive upgrade; dual-accept mixed http for one release.",
           residual="legacy still mixed; drop after legacy 6",
           vs="r3620 csp-report-to (upgrade-insecure-requests, not report-to)",
           fetch1="https://www.w3.org/TR/upgrade-insecure-requests/",
           fetch1_ok="upgrade-insecure-requests upgrades http subresources.",
           fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive upgrade 400s leftover mixed content."),
        bad(slug="mixed-content-ok", domain="mixed-content-vs-upgrade-insecure", name="mixedc", field="Content-Security-Policy",
            old="upgrade leftover", new="mixed content allowed",
            fail_err="400: leftover upgrade after mixed-only",
            plan="mixed-only 400s leftover upgrade. Abandon exclusive mixed; keep upgrade — ads want mixed. Freeze upgrade, spec mixed.",
            residual="handoff: keep upgrade or force mixed; do not claim mixed shipped",
            vs="r3620 csp-report-to (mixed leftover, not report-to)",
            fetch1="https://w3c.github.io/webappsec-mixed-content/",
            fetch1_ok="Allowing mixed content is not upgrade-insecure-requests.",
            fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive mixed 400s leftover upgrade."),
    ),
    (
        ok(slug="json-schema-minproperties", domain="minproperties-vs-empty-object-ok", name="minp", field="attrs",
           old="empty object leftover ok", new="minProperties 1",
           fail_err="400: leftover {} after minProperties-1",
           plan="minProperties-only 400s leftover {}. Abandon exclusive minProperties; dual-accept empty objects for one release.",
           residual="import still {}; drop after import 3",
           vs="r3561 unevaluated-properties (minProperties, not unevaluatedProperties)",
           fetch1=f"{JS}/object.html#size",
           fetch1_ok="minProperties 1 rejects empty objects.",
           fetch2=f"{OAS}#schema-object", fetch2_ok="Exclusive minProperties 400s leftover {}."),
        bad(slug="empty-object-props", domain="empty-object-vs-minproperties", name="eobjp", field="attrs",
            old="minProperties leftover 1", new="empty object allowed",
            fail_err="400: leftover minProperties after empty-ok",
            plan="empty-ok 400s leftover minProperties. Abandon exclusive empty; keep minProperties — catalog wants empty. Freeze minProperties, spec empty-ok.",
            residual="handoff: keep minProperties or force empty-ok; do not claim empty-ok shipped",
            vs="r3561 unevaluated-properties (empty object leftover, not unevaluatedProperties)",
            fetch1=f"{JS}/object.html#size",
            fetch1_ok="Unconstrained objects allow {}.",
            fetch2=f"{OAS}#schema-object", fetch2_ok="Exclusive empty-ok 400s leftover minProperties."),
    ),
    (
        ok(slug="json-schema-maxproperties", domain="maxproperties-vs-unbounded-object", name="maxp", field="attrs",
           old="unbounded leftover object", new="maxProperties 8",
           fail_err="400: leftover 12 keys after maxProperties-8",
           plan="maxProperties-only 400s leftover unbounded. Abandon exclusive maxProperties; dual-accept extra keys for one release.",
           residual="bulk still unbounded; drop after bulk 2",
           vs="r3561 unevaluated-properties (maxProperties, not unevaluatedProperties)",
           fetch1=f"{JS}/object.html#size",
           fetch1_ok="maxProperties 8 rejects larger objects.",
           fetch2=f"{OAS}#schema-object", fetch2_ok="Exclusive maxProperties 400s leftover unbounded."),
        bad(slug="unbounded-object", domain="unbounded-object-vs-maxproperties", name="unbndo", field="attrs",
            old="maxProperties leftover 8", new="unbounded object",
            fail_err="400: leftover maxProperties after unbounded-only",
            plan="unbounded-only 400s leftover maxProperties. Abandon exclusive unbounded; keep maxProperties — search wants unbounded. Freeze maxProperties, spec unbounded.",
            residual="handoff: keep maxProperties or force unbounded; do not claim unbounded shipped",
            vs="r3561 unevaluated-properties (unbounded leftover, not unevaluatedProperties)",
            fetch1=f"{JS}/object.html#size",
            fetch1_ok="No maxProperties means unbounded.",
            fetch2=f"{OAS}#schema-object", fetch2_ok="Exclusive unbounded 400s leftover maxProperties."),
    ),
    (
        ok(slug="status-203-nonauthoritative", domain="status-203-vs-200-transformed", name="s203", field="status",
           old="200 leftover transformed", new="203 Non-Authoritative Information",
           fail_err="400: leftover 200 after 203-only",
           plan="203-only 400s leftover 200. Abandon exclusive 203; dual-accept 200 transformed for one release.",
           residual="proxy still 200; drop after proxy 4",
           vs="r3578 status-202-location (203, not 202)",
           fetch1="https://www.rfc-editor.org/rfc/rfc9110.html#name-203-non-authoritative-information",
           fetch1_ok="203 marks a transformed response.",
           fetch2=f"{OAS}#responses-object", fetch2_ok="Exclusive 203 400s leftover 200."),
        bad(slug="status-200-transformed", domain="200-transformed-vs-203", name="s200t", field="status",
            old="203 leftover", new="200 on transform",
            fail_err="400: leftover 203 after 200-only",
            plan="200-only 400s leftover 203. Abandon exclusive 200; keep 203 — CDN wants 200. Freeze 203, spec 200.",
            residual="handoff: keep 203 or force 200; do not claim 200-transform shipped",
            vs="r3578 status-202-location (200 leftover vs 203, not 202)",
            fetch1="https://www.rfc-editor.org/rfc/rfc9110.html#name-200-ok",
            fetch1_ok="200 does not mark a transform.",
            fetch2=f"{OAS}#responses-object", fetch2_ok="Exclusive 200 400s leftover 203."),
    ),
    (
        ok(slug="status-417-expectation", domain="status-417-vs-ignore-expect", name="s417", field="status",
           old="ignore leftover Expect", new="417 Expectation Failed",
           fail_err="400: leftover ignore after 417-only",
           plan="417-only 400s leftover ignore. Abandon exclusive 417; dual-ignore unknown Expect for one release.",
           residual="gateway still ignores; drop after gw 1",
           vs="r3578 status-202-location (417, not 202)",
           fetch1="https://www.rfc-editor.org/rfc/rfc9110.html#name-417-expectation-failed",
           fetch1_ok="417 is for unsatisfiable Expect.",
           fetch2=f"{OAS}#responses-object", fetch2_ok="Exclusive 417 400s leftover ignore-Expect."),
        bad(slug="ignore-expect", domain="ignore-expect-vs-417", name="igexp", field="Expect",
            old="417 leftover", new="ignore Expect",
            fail_err="400: leftover 417 after ignore-only",
            plan="ignore-only 400s leftover 417. Abandon exclusive ignore; keep 417 — clients want ignore. Freeze 417, spec ignore.",
            residual="handoff: keep 417 or force ignore; do not claim ignore shipped",
            vs="r3578 status-202-location (ignore Expect leftover, not 202)",
            fetch1="https://www.rfc-editor.org/rfc/rfc9110.html#name-expect",
            fetch1_ok="Ignoring Expect is not 417.",
            fetch2=f"{OAS}#responses-object", fetch2_ok="Exclusive ignore 400s leftover 417."),
    ),
    (
        ok(slug="status-505-version", domain="status-505-vs-http11-forced", name="s505", field="status",
           old="HTTP/1.1 leftover forced", new="505 HTTP Version Not Supported",
           fail_err="400: leftover forced 1.1 after 505-only",
           plan="505-only 400s leftover forced 1.1. Abandon exclusive 505; dual-downgrade to 1.1 for one release.",
           residual="mesh still forces 1.1; drop after mesh 5",
           vs="r3577 status-308-https (505, not 308)",
           fetch1="https://www.rfc-editor.org/rfc/rfc9110.html#name-505-http-version-not-supported",
           fetch1_ok="505 refuses the request HTTP version.",
           fetch2=f"{OAS}#responses-object", fetch2_ok="Exclusive 505 400s leftover forced 1.1."),
        bad(slug="http11-forced", domain="http11-forced-vs-505", name="h11f", field="version",
            old="505 leftover", new="force HTTP/1.1",
            fail_err="400: leftover 505 after force-1.1-only",
            plan="force-1.1-only 400s leftover 505. Abandon exclusive force; keep 505 — LB wants 1.1. Freeze 505, spec force.",
            residual="handoff: keep 505 or force 1.1; do not claim force-1.1 shipped",
            vs="r3577 status-308-https (force 1.1 leftover, not 308)",
            fetch1="https://www.rfc-editor.org/rfc/rfc9110.html#name-protocol-version",
            fetch1_ok="Forcing 1.1 is not 505.",
            fetch2=f"{OAS}#responses-object", fetch2_ok="Exclusive force 400s leftover 505."),
    ),
    (
        ok(slug="connect-udp-rfc9298", domain="connect-udp-vs-connect-tcp", name="cudp", field=":protocol",
           old="CONNECT leftover TCP", new="CONNECT-UDP capsule",
           fail_err="400: leftover CONNECT TCP after UDP-only",
           plan="UDP-only 400s leftover TCP CONNECT. Abandon exclusive UDP; dual-accept TCP CONNECT for one release.",
           residual="edge still TCP; drop after edge 2",
           vs="r3614 connect+proto (CONNECT-UDP RFC 9298, not Connect-RPC proto)",
           fetch1="https://www.rfc-editor.org/rfc/rfc9298.html",
           fetch1_ok="RFC 9298 proxies UDP over HTTP.",
           fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive CONNECT-UDP 400s leftover TCP CONNECT."),
        bad(slug="connect-tcp-only", domain="connect-tcp-vs-connect-udp", name="ctcp", field="CONNECT",
            old="CONNECT-UDP leftover", new="CONNECT TCP only",
            fail_err="400: leftover CONNECT-UDP after TCP-only",
            plan="TCP-only 400s leftover CONNECT-UDP. Abandon exclusive TCP; keep UDP — mesh wants TCP. Freeze UDP, spec TCP.",
            residual="handoff: keep CONNECT-UDP or force TCP; do not claim TCP-only shipped",
            vs="r3614 connect+proto (CONNECT TCP leftover, not Connect-RPC)",
            fetch1="https://www.rfc-editor.org/rfc/rfc9110.html#name-connect",
            fetch1_ok="CONNECT TCP is not CONNECT-UDP.",
            fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive TCP 400s leftover CONNECT-UDP."),
    ),
    (
        ok(slug="want-repr-digest", domain="want-repr-digest-vs-no-negotiate", name="wantrd", field="Want-Repr-Digest",
           old="no-digest leftover negotiate", new="Want-Repr-Digest sha-256",
           fail_err="400: leftover missing Want-Repr-Digest after required",
           plan="Want-Repr-Digest-only 400s leftover missing. Abandon exclusive want; dual-accept missing for one release.",
           residual="client still missing; drop after client 4",
           vs="wrap content-digest-rfc9530 (Want-Repr-Digest, not Content-Digest)",
           fetch1="https://www.rfc-editor.org/rfc/rfc9530.html#name-integrity-preference-fields",
           fetch1_ok="Want-Repr-Digest negotiates representation digests.",
           fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive Want-Repr-Digest 400s leftover omitters."),
        bad(slug="no-digest-negotiate", domain="no-digest-negotiate-vs-want-repr", name="nodig", field="Want-Repr-Digest",
            old="sha-256 leftover want", new="no digest negotiate",
            fail_err="400: leftover Want-Repr-Digest after none-only",
            plan="none-only 400s leftover Want-Repr-Digest. Abandon exclusive omit; keep want — CDN wants omit. Freeze want, spec omit.",
            residual="handoff: keep Want-Repr-Digest or force omit; do not claim none shipped",
            vs="wrap content-digest-rfc9530 (no digest negotiate leftover, not Content-Digest)",
            fetch1="https://www.rfc-editor.org/rfc/rfc9530.html",
            fetch1_ok="Omitting Want-Repr-Digest skips negotiation.",
            fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive omit 400s leftover Want-Repr-Digest."),
    ),
    (
        ok(slug="proxy-authenticate-407", domain="proxy-authenticate-407-vs-www-401", name="p407", field="Proxy-Authenticate",
           old="WWW-Authenticate leftover 401", new="407 Proxy Authentication Required",
           fail_err="400: leftover 401 after 407-only",
           plan="407-only 400s leftover 401. Abandon exclusive 407; dual-map leftover 401 for one release.",
           residual="client still 401; drop after client 1",
           vs="r3569 security-mutual-tls (407 Proxy-Authenticate, not mTLS)",
           fetch1="https://www.rfc-editor.org/rfc/rfc9110.html#name-407-proxy-authentication-required",
           fetch1_ok="407 uses Proxy-Authenticate.",
           fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive 407 400s leftover 401 WWW-Authenticate."),
        bad(slug="www-authenticate-401", domain="www-401-vs-proxy-407", name="w401", field="WWW-Authenticate",
            old="407 leftover", new="401 WWW-Authenticate only",
            fail_err="400: leftover 407 after 401-only",
            plan="401-only 400s leftover 407. Abandon exclusive 401; keep 407 — proxy wants 401. Freeze 407, spec 401.",
            residual="handoff: keep 407 or force 401; do not claim 401-only shipped",
            vs="r3569 security-mutual-tls (401 leftover vs 407, not mTLS)",
            fetch1="https://www.rfc-editor.org/rfc/rfc9110.html#name-401-unauthorized",
            fetch1_ok="401 is origin auth, not proxy auth.",
            fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive 401 400s leftover 407."),
    ),
    (
        ok(slug="sf-date-rfc9651", domain="sf-date-vs-unix-epoch-header", name="sfdate", field="Expires-At",
           old="unix leftover epoch", new="sf Date @1700000000",
           fail_err="400: leftover epoch after sf-date-only",
           plan="sf-date-only 400s leftover epoch. Abandon exclusive Date; dual-read unix epoch for one release.",
           residual="worker still epoch; drop after worker 7",
           vs="r3582 unix-epoch-millis (sf Date RFC 9651, not unix-epoch field type)",
           fetch1="https://www.rfc-editor.org/rfc/rfc9651.html#name-dates",
           fetch1_ok="sf Dates are @-prefixed integers.",
           fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive sf Date 400s leftover epoch."),
        bad(slug="unix-epoch-header", domain="unix-epoch-header-vs-sf-date", name="ueph", field="Expires-At",
            old="sf Date leftover", new="unix epoch only",
            fail_err="400: leftover @date after epoch-only",
            plan="epoch-only 400s leftover sf Date. Abandon exclusive epoch; keep Date — cache wants epoch. Freeze Date, spec epoch.",
            residual="handoff: keep sf Date or force epoch; do not claim epoch-only shipped",
            vs="r3582 unix-epoch-millis (epoch header leftover, not millis field)",
            fetch1="https://www.rfc-editor.org/rfc/rfc9110.html#name-date-time-formats",
            fetch1_ok="A raw epoch is not an sf Date.",
            fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive epoch 400s leftover sf Date."),
    ),
    (
        ok(slug="sec-purpose-prefetch", domain="sec-purpose-prefetch-vs-none", name="secpur", field="Sec-Purpose",
           old="no-Purpose leftover", new="Sec-Purpose prefetch",
           fail_err="400: leftover missing Sec-Purpose after prefetch-only",
           plan="prefetch-only 400s leftover missing. Abandon exclusive Sec-Purpose; dual-accept missing for one release.",
           residual="crawler still missing; drop after crawler 2",
           vs="r3620 sec-fetch-site (Sec-Purpose prefetch, not Sec-Fetch-Site)",
           fetch1="https://fetch.spec.whatwg.org/#http-extensions",
           fetch1_ok="Sec-Purpose prefetch marks prefetch requests.",
           fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive Sec-Purpose 400s leftover omitters."),
        bad(slug="no-purpose-header", domain="no-purpose-vs-prefetch", name="npurp", field="Sec-Purpose",
            old="prefetch leftover", new="no Sec-Purpose",
            fail_err="400: leftover Sec-Purpose after none-only",
            plan="none-only 400s leftover Sec-Purpose. Abandon exclusive omit; keep prefetch — CDN wants omit. Freeze prefetch, spec omit.",
            residual="handoff: keep Sec-Purpose or force omit; do not claim none shipped",
            vs="r3620 sec-fetch-site (no Sec-Purpose leftover, not Sec-Fetch-Site)",
            fetch1="https://fetch.spec.whatwg.org/#http-extensions",
            fetch1_ok="Omitting Sec-Purpose is not prefetch.",
            fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive omit 400s leftover Sec-Purpose."),
    ),
    (
        ok(slug="json-schema-pattern-anchor", domain="pattern-anchor-vs-unanchored", name="patanc", field="code",
           old="unanchored leftover regex", new="pattern ^[A-Z]{3}$",
           fail_err="400: leftover unanchored after anchored-only",
           plan="anchored-only 400s leftover unanchored. Abandon exclusive anchors; dual-accept unanchored for one release.",
           residual="SDK still unanchored; drop after sdk 8",
           vs="r3561 json-schema-if-then-else (anchored pattern, not if/then)",
           fetch1=f"{JS}/regular-expressions.html",
           fetch1_ok="JSON Schema patterns are unanchored unless ^$.",
           fetch2=f"{OAS}#schema-object", fetch2_ok="Exclusive anchors 400s leftover unanchored."),
        bad(slug="unanchored-pattern", domain="unanchored-pattern-vs-anchors", name="unanc", field="code",
            old="^$ leftover anchors", new="unanchored pattern",
            fail_err="400: leftover anchors after unanchored-only",
            plan="unanchored-only 400s leftover anchors. Abandon exclusive unanchored; keep anchors — validator wants unanchored. Freeze anchors, spec unanchored.",
            residual="handoff: keep anchors or force unanchored; do not claim unanchored shipped",
            vs="r3561 json-schema-if-then-else (unanchored leftover, not if/then)",
            fetch1=f"{JS}/regular-expressions.html",
            fetch1_ok="Unanchored patterns match substrings.",
            fetch2=f"{OAS}#schema-object", fetch2_ok="Exclusive unanchored 400s leftover ^$."),
    ),
    (
        ok(slug="accept-ch-lifetime", domain="accept-ch-lifetime-vs-no-persist", name="chlife", field="Accept-CH-Lifetime",
           old="no-lifetime leftover", new="Accept-CH-Lifetime 86400",
           fail_err="400: leftover missing lifetime after required",
           plan="lifetime-required 400s leftover missing. Abandon exclusive lifetime; dual-accept missing for one release.",
           residual="browser still missing; drop after browser 5",
           vs="r3620 critical-ch-ua (Accept-CH-Lifetime, not Critical-CH)",
           fetch1="https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Accept-CH",
           fetch1_ok="Accept-CH-Lifetime persisted client hints.",
           fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive lifetime 400s leftover omitters."),
        bad(slug="no-ch-persist", domain="no-ch-persist-vs-lifetime", name="nochp", field="Accept-CH-Lifetime",
            old="86400 leftover", new="no Accept-CH-Lifetime",
            fail_err="400: leftover lifetime after none-only",
            plan="none-only 400s leftover lifetime. Abandon exclusive omit; keep lifetime — privacy wants omit. Freeze lifetime, spec omit.",
            residual="handoff: keep lifetime or force omit; do not claim none shipped",
            vs="r3620 critical-ch-ua (no lifetime leftover, not Critical-CH)",
            fetch1="https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Accept-CH",
            fetch1_ok="Omitting Accept-CH-Lifetime does not persist hints.",
            fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive omit 400s leftover lifetime."),
    ),
]


def catalog_selfcheck() -> None:
    seen: set[str] = set()
    if len(PAIRS) < 16:
        raise SystemExit(f"catalog too small: {len(PAIRS)}")
    for a, b in PAIRS:
        if not a["success"] or b["success"]:
            raise SystemExit(f"pair must be success+fail: {a['slug']} / {b['slug']}")
        for spec in (a, b):
            slug = spec["slug"]
            if slug in seen or slug in BANNED_PRIOR:
                raise SystemExit(f"duplicate or prior slug {slug}")
            seen.add(slug)
            if "w131" in slug or "422-vs-400" in slug or "207-multistatus" in slug:
                raise SystemExit(f"banned {slug}")
            if any(n.lower() in slug or n.lower() in spec["domain"] for n in BANNED_SLUG_NEEDLES):
                raise SystemExit(f"banned needle in {slug} / {spec['domain']}")
            if len("Reflection: " + spec["plan_change"]) > 240:
                raise SystemExit(f"plan_change too long for {slug}")


def next_free_idx(start: int = 0) -> int | None:
    existing = published_slugs()
    for i in range(start, len(PAIRS)):
        a, b = PAIRS[i]
        if a["slug"] not in existing and b["slug"] not in existing:
            return i
    return None


def unused_pairs():
    existing = published_slugs()
    return [p for p in PAIRS if p[0]["slug"] not in existing and p[1]["slug"] not in existing]


def write_round(round_n: int, staging: Path, idx: int | None = None) -> None:
    catalog_selfcheck()
    if idx is None:
        idx = next_free_idx()
        if idx is None:
            raise SystemExit("catalog exhausted")
    t1, t2 = PAIRS[idx]
    existing = published_slugs()
    for spec in (t1, t2):
        if spec["slug"] in existing:
            raise SystemExit(f"slug {spec['slug']} already published")
    e1 = build_episode(round_n, t1)
    e2 = build_episode(round_n, t2)
    for e in (e1, e2):
        blob = json.dumps(e)
        for banned in BANNED_BLOB:
            if f'"{banned}"' in blob:
                raise SystemExit(f"banned key {banned}")
        assert e["meta"]["generator"] == GEN
        assert len(e["steps"]) == 16
    batch = staging / f"batch-r{round_n:02d}.jsonl"
    notes = staging / f"NOTES-r{round_n:02d}.md"
    batch.write_text(json.dumps(e1, ensure_ascii=False) + "\n" + json.dumps(e2, ensure_ascii=False) + "\n")
    notes.write_text(notes_text(round_n, [e1, e2], [t1, t2], idx))
    print(json.dumps({"round": round_n, "idx": idx, "ids": [e1["id"], e2["id"]], "catalog": "g46-w4"}))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--staging", required=True)
    ap.add_argument("--idx", type=int, default=None)
    args = ap.parse_args()
    write_round(args.round, Path(args.staging), args.idx)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
