#!/usr/bin/env python3
"""Sixth leftover unique ACM catalog after g46-w2 exhausts at r3762."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("acm_w2", HERE / "acm-mill-g46-w2.py")
_w2 = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_w2)

plant = _w2.plant
ok = _w2.ok
bad = _w2.bad
GEN = _w2.GEN
BANNED_BLOB = _w2.BANNED_BLOB
BANNED_SLUG_NEEDLES = _w2.BANNED_SLUG_NEEDLES
build_episode = _w2.build_episode
notes_text = _w2.notes_text
published_slugs = _w2.published_slugs
OAS = _w2.OAS
JS = _w2.JS

BANNED_PRIOR = set(_w2.BANNED_PRIOR)
BANNED_PRIOR |= {p[0]["slug"] for p in _w2.PAIRS} | {p[1]["slug"] for p in _w2.PAIRS}

PAIRS: list[tuple[dict, dict]] = [
    (
        ok(slug="trailer-fields", domain="trailer-fields-vs-content-length-only", name="trl", field="Trailer",
           old="Content-Length leftover only", new="Trailer Digest required",
           fail_err="400: leftover Content-Length-only after Trailer-only",
           plan="Trailer-only 400s leftover Content-Length-only. Abandon exclusive Trailer; dual-accept Content-Length-only for one release.",
           residual="proxy still Content-Length; drop after proxy 2",
           vs="wrap content-digest-rfc9530 (Trailer field, not Content-Digest)",
           fetch1="https://www.rfc-editor.org/rfc/rfc9110.html#name-trailer",
           fetch1_ok="Trailer lists fields after chunked body.",
           fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive Trailer 400s leftover Content-Length-only."),
        bad(slug="content-length-only", domain="content-length-vs-trailer-fields", name="clen", field="Content-Length",
            old="Trailer leftover Digest", new="Content-Length only",
            fail_err="400: leftover Trailer after Content-Length-only",
            plan="Content-Length-only 400s leftover Trailer. Abandon exclusive Content-Length; keep Trailer — HTTP/1 wants Content-Length. Freeze Trailer, spec Content-Length.",
            residual="handoff: keep Trailer or force Content-Length; do not claim Content-Length-only shipped",
            vs="wrap content-digest-rfc9530 (Content-Length leftover, not Content-Digest)",
            fetch1="https://www.rfc-editor.org/rfc/rfc9110.html#name-content-length",
            fetch1_ok="Content-Length is delimiting. leftover Trailer is chunked metadata.",
            fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive Content-Length 400s leftover Trailer."),
    ),
    (
        ok(slug="expect-100-continue", domain="expect-100-continue-vs-no-expect", name="expc", field="Expect",
           old="no-Expect leftover", new="Expect 100-continue",
           fail_err="417: leftover no-Expect after 100-continue-only",
           plan="100-continue-only 417s leftover no-Expect. Abandon exclusive Expect; dual-accept missing Expect for one release.",
           residual="uploader still no Expect; drop after uploader 8",
           vs="r3578 status-202-location (Expect 100-continue, not 202)",
           fetch1="https://www.rfc-editor.org/rfc/rfc9110.html#name-expect",
           fetch1_ok="Expect: 100-continue waits for continue.",
           fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive 100-continue 417s leftover no-Expect."),
        bad(slug="no-expect-header", domain="no-expect-vs-100-continue", name="noexp", field="Expect",
            old="100-continue leftover", new="no Expect header",
            fail_err="400: leftover 100-continue after no-Expect-only",
            plan="no-Expect-only 400s leftover 100-continue. Abandon exclusive no-Expect; keep 100-continue — uploads want no Expect. Freeze 100-continue, spec no-Expect.",
            residual="handoff: keep 100-continue or force no-Expect; do not claim no-Expect shipped",
            vs="r3578 status-202-location (no Expect leftover, not 202)",
            fetch1="https://www.rfc-editor.org/rfc/rfc9110.html#name-expect",
            fetch1_ok="Omitting Expect is not 100-continue.",
            fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive no-Expect 400s leftover 100-continue."),
    ),
    (
        ok(slug="ws-subprotocol", domain="websocket-subprotocol-vs-none", name="wsp", field="Sec-WebSocket-Protocol",
           old="no-subprotocol leftover", new="graphql-transport-ws required",
           fail_err="400: leftover no-subprotocol after protocol-only",
           plan="protocol-only 400s leftover none. Abandon exclusive subprotocol; dual-accept no-subprotocol for one release.",
           residual="browser still none; drop after browser 3",
           vs="r3614 connect+proto (WebSocket subprotocol, not Connect proto)",
           fetch1="https://www.rfc-editor.org/rfc/rfc6455.html#section-1.9",
           fetch1_ok="Sec-WebSocket-Protocol selects a subprotocol.",
           fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive subprotocol 400s leftover unsubprotocoled sockets."),
        bad(slug="no-ws-protocol", domain="no-websocket-subprotocol-vs-required", name="nwsp", field="Sec-WebSocket-Protocol",
            old="graphql-transport-ws leftover", new="no subprotocol",
            fail_err="400: leftover subprotocol after none-only",
            plan="none-only 400s leftover subprotocol. Abandon exclusive none; keep subprotocol — GQL wants none. Freeze subprotocol, spec none.",
            residual="handoff: keep subprotocol or force none; do not claim no-subprotocol shipped",
            vs="r3614 connect+proto (no WebSocket subprotocol leftover, not Connect)",
            fetch1="https://www.rfc-editor.org/rfc/rfc6455.html#section-1.9",
            fetch1_ok="Omitting Sec-WebSocket-Protocol is not a named subprotocol.",
            fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive none 400s leftover subprotocol."),
    ),
    (
        ok(slug="sec-fetch-dest", domain="sec-fetch-dest-vs-no-fetch-metadata", name="sfde", field="Sec-Fetch-Dest",
           old="no-fetch-metadata leftover", new="Sec-Fetch-Dest document",
           fail_err="403: leftover missing Sec-Fetch-Dest after dest-required",
           plan="dest-required 403s leftover missing. Abandon exclusive Sec-Fetch-Dest; dual-accept missing for one release.",
           residual="old WebView still missing; drop after webview 2",
           vs="r3620 sec-fetch-site (Sec-Fetch-Dest, not Sec-Fetch-Site)",
           fetch1="https://www.w3.org/TR/fetch-metadata/#sec-fetch-dest-header",
           fetch1_ok="Sec-Fetch-Dest names the destination.",
           fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive Sec-Fetch-Dest 403s leftover no-metadata."),
        bad(slug="no-fetch-metadata", domain="no-fetch-metadata-vs-sec-fetch-dest", name="nofm", field="Sec-Fetch-Dest",
            old="document leftover dest", new="no Fetch Metadata",
            fail_err="403: leftover Sec-Fetch-Dest after no-metadata-only",
            plan="no-metadata-only 403s leftover dest. Abandon exclusive omit; keep dest — security wants omit. Freeze dest, spec omit.",
            residual="handoff: keep Sec-Fetch-Dest or force omit; do not claim no-metadata shipped",
            vs="r3620 sec-fetch-site (no Fetch Metadata leftover, not Sec-Fetch-Site)",
            fetch1="https://www.w3.org/TR/fetch-metadata/",
            fetch1_ok="Omitting Fetch Metadata is not Sec-Fetch-Dest.",
            fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive omit 403s leftover Sec-Fetch-Dest."),
    ),
    (
        ok(slug="save-data-hint", domain="save-data-client-hint-vs-none", name="sdat", field="Save-Data",
           old="no-Save-Data leftover", new="Save-Data on",
           fail_err="400: leftover missing Save-Data after on-required",
           plan="Save-Data-required 400s leftover missing. Abandon exclusive on; dual-accept missing Save-Data for one release.",
           residual="desktop still missing; drop after desktop 1",
           vs="r3620 critical-ch-ua (Save-Data hint, not Critical-CH)",
           fetch1="https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Save-Data",
           fetch1_ok="Save-Data: on requests reduced data.",
           fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive Save-Data 400s leftover omitters."),
        bad(slug="no-save-data", domain="no-save-data-vs-on", name="nsdat", field="Save-Data",
            old="on leftover", new="no Save-Data",
            fail_err="400: leftover Save-Data after none-only",
            plan="none-only 400s leftover Save-Data. Abandon exclusive omit; keep on — lite wants omit. Freeze on, spec omit.",
            residual="handoff: keep Save-Data or force omit; do not claim no-Save-Data shipped",
            vs="r3620 critical-ch-ua (no Save-Data leftover, not Critical-CH)",
            fetch1="https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Save-Data",
            fetch1_ok="Omitting Save-Data is not on.",
            fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive omit 400s leftover Save-Data."),
    ),
    (
        ok(slug="referrer-policy-strict", domain="referrer-policy-strict-origin-vs-unsafe-url", name="rpol", field="Referrer-Policy",
           old="unsafe-url leftover", new="strict-origin-when-cross-origin",
           fail_err="400: leftover unsafe-url after strict-only",
           plan="strict-only 400s leftover unsafe-url. Abandon exclusive strict; dual-accept unsafe-url for one release.",
           residual="analytics still unsafe-url; drop after analytics 4",
           vs="r3620 coop-same-origin (Referrer-Policy, not COOP)",
           fetch1="https://www.w3.org/TR/referrer-policy/",
           fetch1_ok="strict-origin-when-cross-origin strips path cross-origin.",
           fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive strict 400s leftover unsafe-url."),
        bad(slug="unsafe-url-referrer", domain="unsafe-url-vs-strict-referrer-policy", name="unref", field="Referrer-Policy",
            old="strict leftover", new="unsafe-url only",
            fail_err="400: leftover strict after unsafe-url-only",
            plan="unsafe-url-only 400s leftover strict. Abandon exclusive unsafe-url; keep strict — ads want unsafe-url. Freeze strict, spec unsafe-url.",
            residual="handoff: keep strict or force unsafe-url; do not claim unsafe-url shipped",
            vs="r3620 coop-same-origin (unsafe-url leftover, not COOP)",
            fetch1="https://www.w3.org/TR/referrer-policy/#referrer-policy-unsafe-url",
            fetch1_ok="unsafe-url sends the full URL.",
            fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive unsafe-url 400s leftover strict."),
    ),
    (
        ok(slug="coep-require-corp", domain="coep-require-corp-vs-unsafe-none", name="coepr", field="Cross-Origin-Embedder-Policy",
           old="unsafe-none leftover", new="require-corp",
           fail_err="400: leftover unsafe-none after require-corp-only",
           plan="require-corp-only 400s leftover unsafe-none. Abandon exclusive require-corp; dual-accept unsafe-none for one release.",
           residual="widget still unsafe-none; drop after widget 6",
           vs="r3620 coop-same-origin (COEP require-corp, not COOP)",
           fetch1="https://html.spec.whatwg.org/multipage/browsers.html#cross-origin-embedder-policy",
           fetch1_ok="require-corp needs CORP on no-cors embeds.",
           fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive require-corp 400s leftover unsafe-none."),
        bad(slug="coep-unsafe-none", domain="coep-unsafe-none-vs-require-corp", name="coepu", field="Cross-Origin-Embedder-Policy",
            old="require-corp leftover", new="unsafe-none only",
            fail_err="400: leftover require-corp after unsafe-none-only",
            plan="unsafe-none-only 400s leftover require-corp. Abandon exclusive unsafe-none; keep require-corp — embeds want unsafe-none. Freeze require-corp, spec unsafe-none.",
            residual="handoff: keep require-corp or force unsafe-none; do not claim unsafe-none shipped",
            vs="r3620 coop-same-origin (COEP unsafe-none leftover, not COOP)",
            fetch1="https://html.spec.whatwg.org/multipage/browsers.html#cross-origin-embedder-policy",
            fetch1_ok="unsafe-none is the default.",
            fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive unsafe-none 400s leftover require-corp."),
    ),
    (
        ok(slug="corp-same-origin", domain="corp-same-origin-vs-cross-origin", name="corph", field="Cross-Origin-Resource-Policy",
           old="cross-origin leftover", new="same-origin",
           fail_err="400: leftover cross-origin after same-origin-only",
           plan="same-origin-only 400s leftover cross-origin. Abandon exclusive same-origin; dual-accept cross-origin for one release.",
           residual="CDN still cross-origin; drop after cdn 3",
           vs="r3620 coop-same-origin (CORP same-origin, not COOP)",
           fetch1="https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cross-Origin-Resource-Policy",
           fetch1_ok="same-origin CORP blocks cross-origin no-cors.",
           fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive same-origin 400s leftover cross-origin."),
        bad(slug="corp-cross-origin", domain="corp-cross-origin-vs-same-origin", name="corpc", field="Cross-Origin-Resource-Policy",
            old="same-origin leftover", new="cross-origin only",
            fail_err="400: leftover same-origin after cross-origin-only",
            plan="cross-origin-only 400s leftover same-origin. Abandon exclusive cross-origin; keep same-origin — CDN wants cross-origin. Freeze same-origin, spec cross-origin.",
            residual="handoff: keep same-origin or force cross-origin; do not claim cross-origin shipped",
            vs="r3620 coop-same-origin (CORP cross-origin leftover, not COOP)",
            fetch1="https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cross-Origin-Resource-Policy",
            fetch1_ok="cross-origin CORP allows no-cors.",
            fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive cross-origin 400s leftover same-origin."),
    ),
    (
        ok(slug="status-414-uri-too-long", domain="status-414-vs-400-on-long-url", name="s414", field="status",
           old="400 leftover on long URL", new="414 URI Too Long",
           fail_err="400: leftover 400 after 414-only",
           plan="414-only 400s leftover 400 on long URLs. Abandon exclusive 414; dual-map leftover 400 for one release.",
           residual="WAF still 400; drop after waf 3",
           vs="r3560 422-vs-400-validation (414 vs leftover 400, not 422 vs 400)",
           fetch1="https://www.rfc-editor.org/rfc/rfc9110.html#name-414-uri-too-long",
           fetch1_ok="414 is for overlong URIs.",
           fetch2=f"{OAS}#responses-object", fetch2_ok="Exclusive 414 400s leftover 400-on-long-URL."),
        bad(slug="leftover-400-on-long-url", domain="400-on-long-url-vs-414", name="s400u", field="status",
            old="414 leftover", new="400 on long URL",
            fail_err="400: leftover 414 after 400-only",
            plan="400-only 400s leftover 414. Abandon exclusive 400; keep 414 — gateway wants 400. Freeze 414, spec 400.",
            residual="handoff: keep 414 or force 400; do not claim 400-on-long-URL shipped",
            vs="r3560 422-vs-400-validation (400 leftover vs 414, not 422)",
            fetch1="https://www.rfc-editor.org/rfc/rfc9110.html#name-400-bad-request",
            fetch1_ok="400 is generic. leftover 414 is the overlong-URI code.",
            fetch2=f"{OAS}#responses-object", fetch2_ok="Exclusive 400 400s leftover 414."),
    ),
    (
        ok(slug="status-416-unsatisfiable", domain="status-416-vs-200-full-body", name="s416", field="status",
           old="200 leftover full body", new="416 Range Not Satisfiable",
           fail_err="400: leftover 200 after 416-only",
           plan="416-only 400s leftover 200 full body. Abandon exclusive 416; dual-accept 200 full for one release.",
           residual="CDN still 200; drop after cdn 4",
           vs="wrap range-requests-206 (416 unsatisfiable, not 206 partial)",
           fetch1="https://www.rfc-editor.org/rfc/rfc9110.html#name-416-range-not-satisfiable",
           fetch1_ok="416 is for unsatisfiable ranges.",
           fetch2=f"{OAS}#responses-object", fetch2_ok="Exclusive 416 400s leftover 200-full-on-Range."),
        bad(slug="full-200-body", domain="200-full-vs-416", name="s200f", field="status",
            old="416 leftover", new="200 full body on Range",
            fail_err="400: leftover 416 after 200-full-only",
            plan="200-full-only 400s leftover 416. Abandon exclusive 200; keep 416 — player wants 200. Freeze 416, spec 200.",
            residual="handoff: keep 416 or force 200-full; do not claim 200-full shipped",
            vs="wrap range-requests-206 (200 full leftover, not 206)",
            fetch1="https://www.rfc-editor.org/rfc/rfc9110.html#name-200-ok",
            fetch1_ok="200 with full body on Range is allowed but different.",
            fetch2=f"{OAS}#responses-object", fetch2_ok="Exclusive 200-full 400s leftover 416."),
    ),
    (
        ok(slug="status-205-reset-content", domain="status-205-vs-204-no-reset", name="s205", field="status",
           old="204 leftover no reset", new="205 Reset Content",
           fail_err="400: leftover 204 after 205-only",
           plan="205-only 400s leftover 204. Abandon exclusive 205; dual-accept 204 for one release.",
           residual="form still 204; drop after form 2",
           vs="r3578 status-204-no-body (205 Reset Content, not 204)",
           fetch1="https://www.rfc-editor.org/rfc/rfc9110.html#name-205-reset-content",
           fetch1_ok="205 tells the user agent to reset the document view.",
           fetch2=f"{OAS}#responses-object", fetch2_ok="Exclusive 205 400s leftover 204."),
        bad(slug="status-204-no-reset", domain="204-no-reset-vs-205", name="s204n", field="status",
            old="205 leftover", new="204 No Content",
            fail_err="400: leftover 205 after 204-only",
            plan="204-only 400s leftover 205. Abandon exclusive 204; keep 205 — UI wants 204. Freeze 205, spec 204.",
            residual="handoff: keep 205 or force 204; do not claim 204-only shipped",
            vs="r3578 status-204-no-body (204 leftover vs 205, not empty 204 plant)",
            fetch1="https://www.rfc-editor.org/rfc/rfc9110.html#name-204-no-content",
            fetch1_ok="204 has no reset semantics.",
            fetch2=f"{OAS}#responses-object", fetch2_ok="Exclusive 204 400s leftover 205."),
    ),
    (
        ok(slug="hsts-preload", domain="hsts-preload-vs-http-cleartext", name="hstsp", field="Strict-Transport-Security",
           old="http leftover cleartext", new="max-age=63072000; includeSubDomains; preload",
           fail_err="400: leftover http after hsts-preload-only",
           plan="hsts-preload-only 400s leftover http. Abandon exclusive preload; dual-accept http for one release then redirect.",
           residual="health still http; drop after health 8",
           vs="r3577 status-308-https (HSTS preload, not 308)",
           fetch1="https://www.rfc-editor.org/rfc/rfc6797.html",
           fetch1_ok="HSTS preload pins HTTPS.",
           fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive HSTS preload 400s leftover http."),
        bad(slug="http-cleartext", domain="http-cleartext-vs-hsts-preload", name="hclr", field="scheme",
            old="HSTS leftover preload", new="http cleartext only",
            fail_err="400: leftover HSTS after http-only",
            plan="http-only 400s leftover HSTS. Abandon exclusive http; keep HSTS — probe wants http. Freeze HSTS, spec http.",
            residual="handoff: keep HSTS or force http; do not claim http-only shipped",
            vs="r3577 status-308-https (http cleartext leftover, not 308)",
            fetch1="https://www.rfc-editor.org/rfc/rfc9110.html#name-http-and-https-uri-schemes",
            fetch1_ok="http scheme is cleartext.",
            fetch2=f"{OAS}#server-object", fetch2_ok="Exclusive http 400s leftover HSTS."),
    ),
    (
        ok(slug="clear-site-data", domain="clear-site-data-vs-manual-cookie-clear", name="csite", field="Clear-Site-Data",
           old="Set-Cookie leftover Max-Age=0", new='Clear-Site-Data "cookies"',
           fail_err="400: leftover Max-Age=0 after Clear-Site-Data-only",
           plan="Clear-Site-Data-only 400s leftover Max-Age=0. Abandon exclusive Clear-Site-Data; dual-send Max-Age=0 for one release.",
           residual="logout still Max-Age=0; drop after logout 3",
           vs="r3567 cookie-session-token (Clear-Site-Data, not cookie session token)",
           fetch1="https://www.w3.org/TR/clear-site-data/",
           fetch1_ok="Clear-Site-Data wipes browsing data.",
           fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive Clear-Site-Data 400s leftover Max-Age=0."),
        bad(slug="manual-cookie-clear", domain="max-age-zero-vs-clear-site-data", name="mcc", field="Set-Cookie",
            old="Clear-Site-Data leftover", new="Max-Age=0 only",
            fail_err="400: leftover Clear-Site-Data after Max-Age-0-only",
            plan="Max-Age-0-only 400s leftover Clear-Site-Data. Abandon exclusive Max-Age=0; keep Clear-Site-Data — native wants Max-Age=0. Freeze Clear-Site-Data, spec Max-Age=0.",
            residual="handoff: keep Clear-Site-Data or force Max-Age=0; do not claim Max-Age=0 shipped",
            vs="r3567 cookie-session-token (Max-Age=0 leftover, not cookie session token)",
            fetch1="https://www.rfc-editor.org/rfc/rfc6265.html#section-4.1.2.2",
            fetch1_ok="Max-Age=0 expires one cookie.",
            fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive Max-Age=0 400s leftover Clear-Site-Data."),
    ),
    (
        ok(slug="csp-trusted-types", domain="csp-trusted-types-vs-innerhtml", name="ttypes", field="Content-Security-Policy",
           old="innerHTML leftover", new="require-trusted-types-for 'script'",
           fail_err="400: leftover innerHTML after trusted-types-only",
           plan="trusted-types-only 400s leftover innerHTML. Abandon exclusive Trusted Types; dual-accept innerHTML for one release.",
           residual="admin still innerHTML; drop after admin 7",
           vs="r3620 csp-report-to (Trusted Types, not report-to)",
           fetch1="https://www.w3.org/TR/trusted-types/",
           fetch1_ok="require-trusted-types-for blocks innerHTML assignment.",
           fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive Trusted Types 400s leftover innerHTML."),
        bad(slug="innerhtml-leftover", domain="innerhtml-vs-trusted-types", name="ihtml", field="Content-Security-Policy",
            old="trusted-types leftover", new="innerHTML allowed",
            fail_err="400: leftover Trusted Types after innerHTML-only",
            plan="innerHTML-only 400s leftover Trusted Types. Abandon exclusive innerHTML; keep TT — CMS wants innerHTML. Freeze TT, spec innerHTML.",
            residual="handoff: keep Trusted Types or force innerHTML; do not claim innerHTML shipped",
            vs="r3620 csp-report-to (innerHTML leftover, not report-to)",
            fetch1="https://html.spec.whatwg.org/multipage/dynamic-markup-insertion.html#dom-element-innerhtml",
            fetch1_ok="innerHTML assigns markup.",
            fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive innerHTML 400s leftover Trusted Types."),
    ),
    (
        ok(slug="origin-agent-cluster", domain="origin-agent-cluster-vs-none", name="oach", field="Origin-Agent-Cluster",
           old="no-OAC leftover", new="Origin-Agent-Cluster ?1",
           fail_err="400: leftover missing OAC after ?1-only",
           plan="OAC-only 400s leftover missing. Abandon exclusive ?1; dual-accept missing OAC for one release.",
           residual="embed still missing; drop after embed 2",
           vs="r3620 coop-same-origin (Origin-Agent-Cluster, not COOP)",
           fetch1="https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Origin-Agent-Cluster",
           fetch1_ok="Origin-Agent-Cluster ?1 requests origin-keyed agent clusters.",
           fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive OAC 400s leftover missing-OAC."),
        bad(slug="no-oac-header", domain="no-oac-vs-origin-agent-cluster", name="nooac", field="Origin-Agent-Cluster",
            old="?1 leftover", new="no OAC header",
            fail_err="400: leftover OAC after none-only",
            plan="none-only 400s leftover OAC. Abandon exclusive omit; keep ?1 — isolation wants omit. Freeze OAC, spec omit.",
            residual="handoff: keep OAC or force omit; do not claim no-OAC shipped",
            vs="r3620 coop-same-origin (no OAC leftover, not COOP)",
            fetch1="https://html.spec.whatwg.org/multipage/origin.html#origin-keyed-agent-clusters",
            fetch1_ok="Omitting OAC is site-keyed.",
            fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive omit 400s leftover OAC."),
    ),
    (
        ok(slug="options-allow-header", domain="options-allow-vs-empty-options", name="oall", field="Allow",
           old="empty OPTIONS leftover", new="Allow GET,POST,HEAD",
           fail_err="400: leftover empty OPTIONS after Allow-required",
           plan="Allow-required 400s leftover empty OPTIONS. Abandon exclusive Allow; dual-accept empty OPTIONS for one release.",
           residual="gateway still empty; drop after gw 2",
           vs="r3579 status-304-empty (OPTIONS Allow, not 304 empty)",
           fetch1="https://www.rfc-editor.org/rfc/rfc9110.html#name-options",
           fetch1_ok="OPTIONS should advertise Allow.",
           fetch2=f"{OAS}#operation-object", fetch2_ok="Exclusive Allow 400s leftover empty OPTIONS."),
        bad(slug="options-empty", domain="empty-options-vs-allow-header", name="oemp", field="Allow",
            old="Allow leftover list", new="empty OPTIONS only",
            fail_err="400: leftover Allow after empty-OPTIONS-only",
            plan="empty-OPTIONS-only 400s leftover Allow. Abandon exclusive empty; keep Allow — CORS wants empty. Freeze Allow, spec empty.",
            residual="handoff: keep Allow or force empty OPTIONS; do not claim empty-OPTIONS shipped",
            vs="r3579 status-304-empty (empty OPTIONS leftover, not 304)",
            fetch1="https://www.rfc-editor.org/rfc/rfc9110.html#name-options",
            fetch1_ok="Empty OPTIONS is not an Allow list.",
            fetch2=f"{OAS}#operation-object", fetch2_ok="Exclusive empty OPTIONS 400s leftover Allow."),
    ),
    (
        ok(slug="json-schema-allof-merge", domain="json-schema-allof-vs-single-schema", name="jallof", field="allOf",
           old="single leftover schema", new="allOf merge required",
           fail_err="400: leftover single schema after allOf-only",
           plan="allOf-only 400s leftover single. Abandon exclusive allOf; dual-accept single schema for one release.",
           residual="SDK still single; drop after sdk 5",
           vs="r3561 json-schema-if-then-else (allOf merge, not if/then)",
           fetch1=f"{JS}/combining.html#allof",
           fetch1_ok="allOf merges subschemas. leftover single schema is not composition.",
           fetch2=f"{OAS}#schema-object", fetch2_ok="Exclusive allOf 400s leftover single schemas."),
        bad(slug="single-schema-leftover", domain="single-schema-vs-allof", name="jsing", field="schema",
            old="allOf leftover", new="single schema only",
            fail_err="400: leftover allOf after single-only",
            plan="single-only 400s leftover allOf. Abandon exclusive single; keep allOf — codegen wants single. Freeze allOf, spec single.",
            residual="handoff: keep allOf or force single; do not claim single-only shipped",
            vs="r3561 json-schema-if-then-else (single leftover, not if/then)",
            fetch1=f"{JS}/combining.html#allof",
            fetch1_ok="A single schema is not allOf.",
            fetch2=f"{OAS}#schema-object", fetch2_ok="Exclusive single 400s leftover allOf."),
    ),
    (
        ok(slug="json-schema-anyof-closed", domain="json-schema-anyof-vs-open-object", name="janyof", field="anyOf",
           old="open leftover object", new="anyOf closed branches",
           fail_err="400: leftover open object after anyOf-only",
           plan="anyOf-only 400s leftover open. Abandon exclusive anyOf; dual-accept open objects for one release.",
           residual="partner still open; drop after partner 2",
           vs="r3561 unevaluated-properties (anyOf closed, not unevaluatedProperties)",
           fetch1=f"{JS}/combining.html#anyof",
           fetch1_ok="anyOf requires one matching branch.",
           fetch2=f"{OAS}#schema-object", fetch2_ok="Exclusive anyOf 400s leftover open objects."),
        bad(slug="open-additionalprops", domain="open-object-vs-anyof-closed", name="jopen", field="additionalProperties",
            old="anyOf leftover closed", new="additionalProperties true",
            fail_err="400: leftover anyOf after open-only",
            plan="open-only 400s leftover anyOf. Abandon exclusive open; keep anyOf — OEM wants open. Freeze anyOf, spec open.",
            residual="handoff: keep anyOf or force open; do not claim open-only shipped",
            vs="r3561 unevaluated-properties (open leftover, not unevaluatedProperties)",
            fetch1=f"{JS}/object.html#additionalproperties",
            fetch1_ok="additionalProperties true is open. leftover anyOf is closed.",
            fetch2=f"{OAS}#schema-object", fetch2_ok="Exclusive open 400s leftover anyOf."),
    ),
    (
        ok(slug="websocket-over-h3", domain="websocket-over-h3-vs-h1-upgrade", name="wsh3", field=":protocol",
           old="HTTP/1 leftover Upgrade", new="WebSocket over HTTP/3",
           fail_err="400: leftover h1 Upgrade after h3-ws-only",
           plan="h3-ws-only 400s leftover h1 Upgrade. Abandon exclusive h3; dual-accept h1 Upgrade for one release.",
           residual="proxy still h1; drop after proxy 6",
           vs="r3577 status-308-https (WebSocket over h3, not 308)",
           fetch1="https://www.rfc-editor.org/rfc/rfc9220.html",
           fetch1_ok="RFC 9220 boots WebSocket over HTTP/3.",
           fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive h3-ws 400s leftover h1 Upgrade."),
        bad(slug="websocket-h1-upgrade", domain="websocket-h1-upgrade-vs-h3", name="wsh1", field="Upgrade",
            old="h3 leftover :protocol", new="HTTP/1 Upgrade websocket",
            fail_err="400: leftover h3-ws after h1-upgrade-only",
            plan="h1-upgrade-only 400s leftover h3-ws. Abandon exclusive h1; keep h3 — mesh wants h1. Freeze h3, spec h1.",
            residual="handoff: keep h3-ws or force h1 Upgrade; do not claim h1-only shipped",
            vs="r3577 status-308-https (h1 Upgrade leftover, not 308)",
            fetch1="https://www.rfc-editor.org/rfc/rfc6455.html#section-1.3",
            fetch1_ok="HTTP/1 Upgrade is not RFC 9220 h3.",
            fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive h1 Upgrade 400s leftover h3-ws."),
    ),
    (
        ok(slug="document-policy-js", domain="document-policy-vs-none", name="docpol", field="Document-Policy",
           old="no-Document-Policy leftover", new="Document-Policy js-profiling",
           fail_err="400: leftover missing Document-Policy after required",
           plan="Document-Policy-only 400s leftover missing. Abandon exclusive policy; dual-accept missing for one release.",
           residual="legacy still missing; drop after legacy 4",
           vs="r3620 permissions-policy (Document-Policy, not Permissions-Policy)",
           fetch1="https://wicg.github.io/document-policy/",
           fetch1_ok="Document-Policy configures document features.",
           fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive Document-Policy 400s leftover omitters."),
        bad(slug="no-document-policy", domain="no-document-policy-vs-required", name="ndocp", field="Document-Policy",
            old="js-profiling leftover", new="no Document-Policy",
            fail_err="400: leftover Document-Policy after none-only",
            plan="none-only 400s leftover Document-Policy. Abandon exclusive omit; keep policy — embed wants omit. Freeze policy, spec omit.",
            residual="handoff: keep Document-Policy or force omit; do not claim none shipped",
            vs="r3620 permissions-policy (no Document-Policy leftover, not Permissions-Policy)",
            fetch1="https://wicg.github.io/document-policy/",
            fetch1_ok="Omitting Document-Policy is not js-profiling.",
            fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive omit 400s leftover Document-Policy."),
    ),
    (
        ok(slug="sf-inner-list", domain="sf-inner-list-vs-flat-list", name="sfin", field="Accept-Signature",
           old="flat leftover list", new="sf Inner List (a b)",
           fail_err="400: leftover flat list after inner-list-only",
           plan="inner-list-only 400s leftover flat. Abandon exclusive Inner List; dual-parse flat lists for one release.",
           residual="signer still flat; drop after signer 3",
           vs="r3587 ratelimit-policy-header (sf Inner List, not RateLimit)",
           fetch1="https://www.rfc-editor.org/rfc/rfc8941.html#name-inner-lists",
           fetch1_ok="Inner Lists are parenthesized sequences.",
           fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive Inner List 400s leftover flat lists."),
        bad(slug="sf-list-flat", domain="sf-flat-list-vs-inner-list", name="sfflat", field="Accept-Signature",
            old="Inner List leftover", new="flat sf List only",
            fail_err="400: leftover Inner List after flat-only",
            plan="flat-only 400s leftover Inner List. Abandon exclusive flat; keep Inner List — gateway wants flat. Freeze Inner List, spec flat.",
            residual="handoff: keep Inner List or force flat; do not claim flat-only shipped",
            vs="r3587 ratelimit-policy-header (flat sf List leftover, not RateLimit)",
            fetch1="https://www.rfc-editor.org/rfc/rfc8941.html#name-lists",
            fetch1_ok="A flat List is not an Inner List.",
            fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive flat 400s leftover Inner List."),
    ),
    (
        ok(slug="timing-allow-origin", domain="timing-allow-origin-vs-blocked", name="tao", field="Timing-Allow-Origin",
           old="timing leftover blocked", new="Timing-Allow-Origin *",
           fail_err="400: leftover blocked timing after TAO-only",
           plan="TAO-only 400s leftover blocked. Abandon exclusive TAO; dual-accept missing TAO for one release.",
           residual="CDN still blocked; drop after cdn 1",
           vs="r3587 server-timing-metric (Timing-Allow-Origin, not Server-Timing)",
           fetch1="https://www.w3.org/TR/resource-timing/#sec-timing-allow-origin",
           fetch1_ok="Timing-Allow-Origin exposes Resource Timing.",
           fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive TAO 400s leftover blocked timing."),
        bad(slug="timing-blocked", domain="timing-blocked-vs-tao", name="tblk", field="Timing-Allow-Origin",
            old="TAO leftover *", new="no Timing-Allow-Origin",
            fail_err="400: leftover TAO after blocked-only",
            plan="blocked-only 400s leftover TAO. Abandon exclusive block; keep TAO — privacy wants block. Freeze TAO, spec block.",
            residual="handoff: keep TAO or force block; do not claim blocked-only shipped",
            vs="r3587 server-timing-metric (blocked leftover, not Server-Timing)",
            fetch1="https://www.w3.org/TR/resource-timing/#sec-timing-allow-origin",
            fetch1_ok="Omitting TAO hides cross-origin timing.",
            fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive block 400s leftover TAO."),
    ),
    (
        ok(slug="sf-boolean-item", domain="sf-boolean-vs-true-string", name="sfbool", field="Feature",
           old="true leftover string", new="sf Boolean ?1",
           fail_err="400: leftover true-string after sf-boolean-only",
           plan="sf-boolean-only 400s leftover true string. Abandon exclusive ?1; dual-read true/false strings for one release.",
           residual="client still true; drop after client 2",
           vs="r3587 ratelimit-policy-header (sf Boolean, not RateLimit)",
           fetch1="https://www.rfc-editor.org/rfc/rfc8941.html#name-booleans",
           fetch1_ok="sf Booleans are ?0/?1. leftover true is a string.",
           fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive sf Boolean 400s leftover true strings."),
        bad(slug="true-string-header", domain="true-string-vs-sf-boolean", name="trstr", field="Feature",
            old="?1 leftover", new="true string only",
            fail_err="400: leftover ?1 after true-string-only",
            plan="true-string-only 400s leftover ?1. Abandon exclusive true; keep ?1 — gateway wants true. Freeze ?1, spec true.",
            residual="handoff: keep ?1 or force true string; do not claim true-string shipped",
            vs="r3587 ratelimit-policy-header (true string leftover, not RateLimit)",
            fetch1="https://www.rfc-editor.org/rfc/rfc9110.html#name-field-values",
            fetch1_ok="The token true is not an sf Boolean.",
            fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive true 400s leftover ?1."),
    ),
    (
        ok(slug="private-network-access", domain="private-network-access-vs-none", name="pna", field="Access-Control-Request-Private-Network",
           old="no-PNA leftover", new="Private Network Access preflight",
           fail_err="400: leftover missing PNA after required",
           plan="PNA-required 400s leftover missing. Abandon exclusive PNA; dual-accept missing preflight for one release.",
           residual="intranet still missing; drop after intranet 5",
           vs="r3620 origin-required-mutating (PNA preflight, not Origin required)",
           fetch1="https://wicg.github.io/private-network-access/",
           fetch1_ok="PNA adds a preflight for public-to-private requests.",
           fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive PNA 400s leftover missing preflight."),
        bad(slug="no-pna-preflight", domain="no-pna-vs-required", name="nopna", field="Access-Control-Request-Private-Network",
            old="PNA leftover preflight", new="no PNA header",
            fail_err="400: leftover PNA after none-only",
            plan="none-only 400s leftover PNA. Abandon exclusive omit; keep PNA — LAN wants omit. Freeze PNA, spec omit.",
            residual="handoff: keep PNA or force omit; do not claim no-PNA shipped",
            vs="r3620 origin-required-mutating (no PNA leftover, not Origin required)",
            fetch1="https://wicg.github.io/private-network-access/",
            fetch1_ok="Omitting PNA is not a private-network preflight.",
            fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive omit 400s leftover PNA."),
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
        assert "sim_or_real" not in e
    batch = staging / f"batch-r{round_n:02d}.jsonl"
    notes = staging / f"NOTES-r{round_n:02d}.md"
    batch.write_text(json.dumps(e1, ensure_ascii=False) + "\n" + json.dumps(e2, ensure_ascii=False) + "\n")
    notes.write_text(notes_text(round_n, [e1, e2], [t1, t2], idx))
    print(json.dumps({"round": round_n, "idx": idx, "ids": [e1["id"], e2["id"]], "catalog": "g46-w3"}))


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
