#!/usr/bin/env python3
"""Ninth leftover unique ACM catalog after g46-w5 exhausts at r3834."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("acm_w5", HERE / "acm-mill-g46-w5.py")
_w5 = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_w5)

ok = _w5.ok
bad = _w5.bad
GEN = _w5.GEN
BANNED_BLOB = _w5.BANNED_BLOB
BANNED_SLUG_NEEDLES = _w5.BANNED_SLUG_NEEDLES
build_episode = _w5.build_episode
notes_text = _w5.notes_text
published_slugs = _w5.published_slugs
OAS = _w5.OAS
JS = _w5.JS

BANNED_PRIOR = set(_w5.BANNED_PRIOR)
BANNED_PRIOR |= {p[0]["slug"] for p in _w5.PAIRS} | {p[1]["slug"] for p in _w5.PAIRS}

PAIRS: list[tuple[dict, dict]] = [
    (
        ok(slug="cookie-samesite-lax", domain="cookie-samesite-lax-vs-none", name="cslax", field="SameSite",
           old="SameSite leftover None", new="SameSite=Lax required",
           fail_err="400: leftover None after Lax-only",
           plan="Lax-only 400s leftover None. Abandon exclusive Lax; dual-accept None for one release.",
           residual="SSO still None; drop after sso 3",
           vs="r3567 cookie-partitioned-chips (SameSite Lax, not Partitioned)",
           fetch1="https://www.rfc-editor.org/rfc/rfc6265.html",
           fetch1_ok="SameSite=Lax is not None.",
           fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive Lax 400s leftover None."),
        bad(slug="cookie-samesite-none", domain="cookie-samesite-none-vs-lax", name="csnone", field="SameSite",
            old="Lax leftover", new="SameSite=None; Secure",
            fail_err="400: leftover Lax after None-only",
            plan="None-only 400s leftover Lax. Abandon exclusive None; keep Lax — ads want None. Freeze Lax, spec None.",
            residual="handoff: keep Lax or force None; do not claim None shipped",
            vs="r3567 cookie-partitioned-chips (SameSite None leftover, not Partitioned)",
            fetch1="https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Set-Cookie/SameSite",
            fetch1_ok="SameSite=None requires Secure.",
            fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive None 400s leftover Lax."),
    ),
    (
        ok(slug="cache-control-no-store", domain="cache-control-no-store-vs-private", name="ccns", field="Cache-Control",
           old="private leftover", new="no-store required",
           fail_err="400: leftover private after no-store-only",
           plan="no-store-only 400s leftover private. Abandon exclusive no-store; dual-accept private for one release.",
           residual="CDN still private; drop after cdn 2",
           vs="r3587 ratelimit-policy-header (no-store, not RateLimit)",
           fetch1="https://www.rfc-editor.org/rfc/rfc9111.html#name-no-store",
           fetch1_ok="no-store forbids storing. leftover private may cache.",
           fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive no-store 400s leftover private."),
        bad(slug="cache-control-private", domain="cache-control-private-vs-no-store", name="ccpriv", field="Cache-Control",
            old="no-store leftover", new="private only",
            fail_err="400: leftover no-store after private-only",
            plan="private-only 400s leftover no-store. Abandon exclusive private; keep no-store — PII wants private. Freeze no-store, spec private.",
            residual="handoff: keep no-store or force private; do not claim private shipped",
            vs="r3587 ratelimit-policy-header (private leftover, not RateLimit)",
            fetch1="https://www.rfc-editor.org/rfc/rfc9111.html#name-private",
            fetch1_ok="private allows browser cache. leftover no-store does not.",
            fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive private 400s leftover no-store."),
    ),
    (
        ok(slug="pragma-no-cache", domain="pragma-no-cache-vs-cache-control", name="pragma", field="Pragma",
           old="Cache-Control leftover only", new="Pragma: no-cache required",
           fail_err="400: leftover missing Pragma after required",
           plan="Pragma-required 400s leftover missing. Abandon exclusive Pragma; dual-accept Cache-Control-only for one release.",
           residual="HTTP/1.0 still missing; drop after h10 4",
           vs="r3587 retry-after-http-date (Pragma no-cache, not Retry-After)",
           fetch1="https://www.rfc-editor.org/rfc/rfc9111.html#name-pragma",
           fetch1_ok="Pragma: no-cache is HTTP/1.0 compatibility.",
           fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive Pragma 400s leftover Cache-Control-only."),
        bad(slug="cache-control-only-pragma", domain="cache-control-only-vs-pragma", name="ccopr", field="Cache-Control",
            old="Pragma leftover", new="Cache-Control only",
            fail_err="400: leftover Pragma after Cache-Control-only",
            plan="Cache-Control-only 400s leftover Pragma. Abandon exclusive Cache-Control; keep Pragma — 1.0 wants Cache-Control. Freeze Pragma, spec Cache-Control.",
            residual="handoff: keep Pragma or force Cache-Control; do not claim Cache-Control-only shipped",
            vs="r3587 retry-after-http-date (Cache-Control leftover vs Pragma, not Retry-After)",
            fetch1="https://www.rfc-editor.org/rfc/rfc9111.html#name-cache-control",
            fetch1_ok="Cache-Control is not Pragma.",
            fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive Cache-Control 400s leftover Pragma."),
    ),
    (
        ok(slug="vary-origin", domain="vary-origin-vs-accept-only", name="vorig", field="Vary",
           old="Vary leftover Accept", new="Vary: Origin required",
           fail_err="400: leftover Accept after Origin-only",
           plan="Origin-only 400s leftover Accept. Abandon exclusive Origin; dual-accept Accept for one release.",
           residual="CDN still Accept; drop after cdn 6",
           vs="r3588 wildcard-media-quality (Vary Origin, not Accept wildcard)",
           fetch1="https://www.rfc-editor.org/rfc/rfc9110.html#name-vary",
           fetch1_ok="Vary: Origin keys CORS caches.",
           fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive Origin 400s leftover Accept."),
        bad(slug="vary-accept-only", domain="vary-accept-vs-origin", name="vacc", field="Vary",
            old="Origin leftover", new="Vary: Accept only",
            fail_err="400: leftover Origin after Accept-only",
            plan="Accept-only 400s leftover Origin. Abandon exclusive Accept; keep Origin — CORS wants Accept. Freeze Origin, spec Accept.",
            residual="handoff: keep Origin or force Accept; do not claim Accept-only shipped",
            vs="r3588 wildcard-media-quality (Vary Accept leftover, not wildcard)",
            fetch1="https://www.rfc-editor.org/rfc/rfc9110.html#name-vary",
            fetch1_ok="Vary: Accept is not Origin.",
            fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive Accept 400s leftover Origin."),
    ),
    (
        ok(slug="x-content-type-options", domain="xcto-nosniff-vs-missing", name="xcto", field="X-Content-Type-Options",
           old="missing leftover nosniff", new="nosniff required",
           fail_err="400: leftover missing after nosniff-only",
           plan="nosniff-only 400s leftover missing. Abandon exclusive nosniff; dual-accept missing for one release.",
           residual="legacy still missing; drop after legacy 1",
           vs="r3563 content-media-type-pdf (X-Content-Type-Options, not contentMediaType)",
           fetch1="https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-Content-Type-Options",
           fetch1_ok="nosniff blocks MIME sniffing.",
           fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive nosniff 400s leftover omitters."),
        bad(slug="missing-nosniff", domain="missing-nosniff-vs-required", name="nnosn", field="X-Content-Type-Options",
            old="nosniff leftover", new="no X-Content-Type-Options",
            fail_err="400: leftover nosniff after none-only",
            plan="none-only 400s leftover nosniff. Abandon exclusive omit; keep nosniff — downloads want omit. Freeze nosniff, spec omit.",
            residual="handoff: keep nosniff or force omit; do not claim none shipped",
            vs="r3563 content-media-type-pdf (missing nosniff leftover, not contentMediaType)",
            fetch1="https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-Content-Type-Options",
            fetch1_ok="Omitting nosniff allows sniffing.",
            fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive omit 400s leftover nosniff."),
    ),
    (
        ok(slug="x-frame-options-deny", domain="xfo-deny-vs-csp-frame-ancestors", name="xfoden", field="X-Frame-Options",
           old="CSP leftover frame-ancestors", new="DENY required",
           fail_err="400: leftover CSP after DENY-only",
           plan="DENY-only 400s leftover CSP. Abandon exclusive DENY; dual-accept frame-ancestors for one release.",
           residual="embed still CSP; drop after embed 5",
           vs="r3620 csp-report-to (X-Frame-Options DENY, not report-to)",
           fetch1="https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-Frame-Options",
           fetch1_ok="DENY forbids framing. leftover CSP frame-ancestors is different.",
           fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive DENY 400s leftover CSP."),
        bad(slug="csp-frame-ancestors", domain="csp-frame-ancestors-vs-xfo-deny", name="cspfa", field="Content-Security-Policy",
            old="DENY leftover", new="frame-ancestors 'none'",
            fail_err="400: leftover DENY after frame-ancestors-only",
            plan="frame-ancestors-only 400s leftover DENY. Abandon exclusive CSP; keep DENY — portal wants CSP. Freeze DENY, spec CSP.",
            residual="handoff: keep DENY or force frame-ancestors; do not claim CSP shipped",
            vs="r3620 csp-report-to (frame-ancestors leftover, not report-to)",
            fetch1="https://www.w3.org/TR/CSP3/#frame-ancestors",
            fetch1_ok="frame-ancestors is not X-Frame-Options.",
            fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive frame-ancestors 400s leftover DENY."),
    ),
    (
        ok(slug="format-ipv4-only", domain="format-ipv4-vs-ipv6-literal", name="ipv4o", field="bind",
           old="IPv6 leftover literal", new="format ipv4",
           fail_err="400: leftover IPv6 after ipv4-only",
           plan="ipv4-only 400s leftover IPv6. Abandon exclusive ipv4; dual-accept IPv6 literals for one release.",
           residual="mesh still IPv6; drop after mesh 2",
           vs="r3585 ipv6-zone-id (format ipv4, not zone-id)",
           fetch1=f"{JS}/string.html#resource-identifiers",
           fetch1_ok="format ipv4 is dotted-quad. leftover IPv6 is different.",
           fetch2=f"{OAS}#data-type-format", fetch2_ok="Exclusive ipv4 400s leftover IPv6."),
        bad(slug="ipv6-literal-leftover", domain="ipv6-literal-vs-ipv4-only", name="ipv6l", field="bind",
            old="ipv4 leftover", new="IPv6 literal only",
            fail_err="400: leftover ipv4 after IPv6-only",
            plan="IPv6-only 400s leftover ipv4. Abandon exclusive IPv6; keep ipv4 — dual-stack wants IPv6. Freeze ipv4, spec IPv6.",
            residual="handoff: keep ipv4 or force IPv6; do not claim IPv6-only shipped",
            vs="r3585 ipv6-zone-id (IPv6 leftover vs ipv4, not zone-id)",
            fetch1=f"{JS}/string.html#resource-identifiers",
            fetch1_ok="IPv6 literals are not format ipv4.",
            fetch2=f"{OAS}#data-type-format", fetch2_ok="Exclusive IPv6 400s leftover ipv4."),
    ),
    (
        ok(slug="minlength-code", domain="minlength-vs-unconstrained-string", name="minlc", field="code",
           old="unconstrained leftover string", new="minLength 3",
           fail_err="400: leftover '' after minLength-3",
           plan="minLength-only 400s leftover empty. Abandon exclusive minLength; dual-accept empty for one release.",
           residual="import still ''; drop after import 4",
           vs="wrap maxlength-display-name (minLength, not maxLength)",
           fetch1=f"{JS}/string.html#length",
           fetch1_ok="minLength 3 rejects empty strings.",
           fetch2=f"{OAS}#schema-object", fetch2_ok="Exclusive minLength 400s leftover empty."),
        bad(slug="unconstrained-string", domain="unconstrained-string-vs-minlength", name="unstrc", field="code",
            old="minLength leftover 3", new="unconstrained string",
            fail_err="400: leftover minLength after unconstrained-only",
            plan="unconstrained-only 400s leftover minLength. Abandon exclusive unconstrained; keep minLength — catalog wants unconstrained. Freeze minLength, spec unconstrained.",
            residual="handoff: keep minLength or force unconstrained; do not claim unconstrained shipped",
            vs="wrap maxlength-display-name (unconstrained leftover, not maxLength)",
            fetch1=f"{JS}/string.html#length",
            fetch1_ok="No minLength allows empty.",
            fetch2=f"{OAS}#schema-object", fetch2_ok="Exclusive unconstrained 400s leftover minLength."),
    ),
    (
        ok(slug="acao-credentials", domain="acao-credentials-vs-omit", name="acaoc", field="Access-Control-Allow-Credentials",
           old="omit leftover credentials", new="true required",
           fail_err="400: leftover omit after credentials-only",
           plan="credentials-only 400s leftover omit. Abandon exclusive true; dual-accept omit for one release.",
           residual="SPA still omit; drop after spa 7",
           vs="r3620 origin-required-mutating (Allow-Credentials, not Origin required)",
           fetch1="https://fetch.spec.whatwg.org/#http-access-control-allow-credentials",
           fetch1_ok="Allow-Credentials: true requires a specific ACAO.",
           fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive credentials 400s leftover omit."),
        bad(slug="omit-credentials", domain="omit-credentials-vs-acao-true", name="omitc", field="Access-Control-Allow-Credentials",
            old="true leftover", new="omit credentials",
            fail_err="400: leftover true after omit-only",
            plan="omit-only 400s leftover true. Abandon exclusive omit; keep true — cookie wants omit. Freeze true, spec omit.",
            residual="handoff: keep true or force omit; do not claim omit shipped",
            vs="r3620 origin-required-mutating (omit credentials leftover, not Origin)",
            fetch1="https://fetch.spec.whatwg.org/#http-access-control-allow-credentials",
            fetch1_ok="Omitting credentials is not true.",
            fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive omit 400s leftover true."),
    ),
    (
        ok(slug="ac-max-age", domain="access-control-max-age-vs-none", name="acma", field="Access-Control-Max-Age",
           old="no-max-age leftover", new="Max-Age 600 required",
           fail_err="400: leftover missing Max-Age after required",
           plan="Max-Age-required 400s leftover missing. Abandon exclusive Max-Age; dual-accept missing for one release.",
           residual="browser still missing; drop after browser 2",
           vs="r3620 origin-required-mutating (AC Max-Age, not Origin required)",
           fetch1="https://fetch.spec.whatwg.org/#http-access-control-max-age",
           fetch1_ok="Max-Age caches preflights.",
           fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive Max-Age 400s leftover omitters."),
        bad(slug="no-preflight-cache", domain="no-preflight-cache-vs-max-age", name="nopfc", field="Access-Control-Max-Age",
            old="600 leftover", new="no Max-Age",
            fail_err="400: leftover Max-Age after none-only",
            plan="none-only 400s leftover Max-Age. Abandon exclusive omit; keep Max-Age — CORS wants omit. Freeze Max-Age, spec omit.",
            residual="handoff: keep Max-Age or force omit; do not claim none shipped",
            vs="r3620 origin-required-mutating (no Max-Age leftover, not Origin)",
            fetch1="https://fetch.spec.whatwg.org/#http-access-control-max-age",
            fetch1_ok="Omitting Max-Age does not cache preflights.",
            fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive omit 400s leftover Max-Age."),
    ),
    (
        ok(slug="xxss-protection-disabled", domain="xxss-disabled-vs-filter-leftover", name="xxssd", field="X-XSS-Protection",
           old="1; leftover mode=block", new="0 disabled",
           fail_err="400: leftover 1;mode=block after 0-only",
           plan="0-only 400s leftover filter. Abandon exclusive 0; dual-accept 1;mode=block for one release.",
           residual="IE still filter; drop after ie 8",
           vs="r3620 csp-report-to (X-XSS-Protection 0, not CSP report-to)",
           fetch1="https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-XSS-Protection",
           fetch1_ok="0 disables the XSS filter.",
           fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive 0 400s leftover 1;mode=block."),
        bad(slug="xss-filter-leftover", domain="xss-filter-vs-disabled", name="xssf", field="X-XSS-Protection",
            old="0 leftover", new="1; mode=block",
            fail_err="400: leftover 0 after filter-only",
            plan="filter-only 400s leftover 0. Abandon exclusive filter; keep 0 — modern wants filter. Freeze 0, spec filter.",
            residual="handoff: keep 0 or force filter; do not claim filter shipped",
            vs="r3620 csp-report-to (XSS filter leftover, not CSP)",
            fetch1="https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-XSS-Protection",
            fetch1_ok="1; mode=block is not 0.",
            fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive filter 400s leftover 0."),
    ),
    (
        ok(slug="json-schema-title-required", domain="schema-title-vs-unnamed", name="jtitle", field="title",
           old="unnamed leftover schema", new="title required",
           fail_err="400: leftover unnamed after title-only",
           plan="title-only 400s leftover unnamed. Abandon exclusive title; dual-accept unnamed for one release.",
           residual="codegen still unnamed; drop after codegen 3",
           vs="r3572 examples-plural-keyword (schema title, not examples)",
           fetch1=f"{JS}/generic.html#annotation",
           fetch1_ok="title is a user-facing name.",
           fetch2=f"{OAS}#schema-object", fetch2_ok="Exclusive title 400s leftover unnamed."),
        bad(slug="unnamed-schema", domain="unnamed-schema-vs-title", name="unnam", field="title",
            old="title leftover", new="unnamed schema only",
            fail_err="400: leftover title after unnamed-only",
            plan="unnamed-only 400s leftover title. Abandon exclusive unnamed; keep title — docs want unnamed. Freeze title, spec unnamed.",
            residual="handoff: keep title or force unnamed; do not claim unnamed shipped",
            vs="r3572 examples-plural-keyword (unnamed leftover, not examples)",
            fetch1=f"{JS}/generic.html#annotation",
            fetch1_ok="Omitting title is not a titled schema.",
            fetch2=f"{OAS}#schema-object", fetch2_ok="Exclusive unnamed 400s leftover title."),
    ),
    (
        ok(slug="format-hostname-ascii", domain="hostname-ascii-vs-idn", name="hascii", field="host",
           old="IDN leftover hostname", new="format hostname ASCII",
           fail_err="400: leftover IDN after hostname-only",
           plan="hostname-only 400s leftover IDN. Abandon exclusive ASCII; dual-accept IDN for one release.",
           residual="l10n still IDN; drop after l10n 2",
           vs="r3586 idn-hostname (ASCII hostname, not idn-hostname plant)",
           fetch1=f"{JS}/string.html#resource-identifiers",
           fetch1_ok="format hostname is ASCII. leftover IDN needs idn-hostname.",
           fetch2=f"{OAS}#data-type-format", fetch2_ok="Exclusive hostname 400s leftover IDN."),
        bad(slug="idn-hostname-leftover", domain="idn-vs-ascii-hostname", name="idnhl", field="host",
            old="ASCII leftover hostname", new="idn-hostname only",
            fail_err="400: leftover ASCII after idn-only",
            plan="idn-only 400s leftover ASCII. Abandon exclusive idn; keep ASCII — DNS wants idn. Freeze ASCII, spec idn.",
            residual="handoff: keep ASCII or force idn; do not claim idn-only shipped",
            vs="r3586 idn-hostname (idn leftover vs ASCII, not the idn plant itself)",
            fetch1=f"{JS}/string.html#resource-identifiers",
            fetch1_ok="idn-hostname is not ASCII hostname.",
            fetch2=f"{OAS}#data-type-format", fetch2_ok="Exclusive idn 400s leftover ASCII."),
    ),
    (
        ok(slug="feature-policy-camera", domain="feature-policy-vs-permissions-policy", name="fpcam", field="Feature-Policy",
           old="Permissions-Policy leftover", new="Feature-Policy camera 'none'",
           fail_err="400: leftover Permissions-Policy after Feature-Policy-only",
           plan="Feature-Policy-only 400s leftover Permissions-Policy. Abandon exclusive Feature-Policy; dual-read Permissions-Policy for one release.",
           residual="browser still Permissions-Policy; drop after browser 4",
           vs="r3620 permissions-policy (Feature-Policy leftover vs Permissions-Policy plant)",
           fetch1="https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Feature-Policy",
           fetch1_ok="Feature-Policy is the predecessor of Permissions-Policy.",
           fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive Feature-Policy 400s leftover Permissions-Policy."),
        bad(slug="permissions-policy-camera", domain="permissions-policy-vs-feature-policy", name="ppcam", field="Permissions-Policy",
            old="Feature-Policy leftover", new="Permissions-Policy camera=()",
            fail_err="400: leftover Feature-Policy after Permissions-Policy-only",
            plan="Permissions-Policy-only 400s leftover Feature-Policy. Abandon exclusive Permissions-Policy; keep Feature-Policy — WebView wants Permissions-Policy. Freeze Feature-Policy, spec Permissions-Policy.",
            residual="handoff: keep Feature-Policy or force Permissions-Policy; do not claim Permissions-Policy shipped",
            vs="r3620 permissions-policy (Permissions-Policy leftover vs Feature-Policy, not the wrap plant)",
            fetch1="https://www.w3.org/TR/permissions-policy-1/",
            fetch1_ok="Permissions-Policy is not Feature-Policy.",
            fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive Permissions-Policy 400s leftover Feature-Policy."),
    ),
    (
        ok(slug="json-schema-default-applied", domain="schema-default-vs-omit", name="jdef", field="default",
           old="omit leftover default", new="default applied",
           fail_err="400: leftover omit after default-applied-only",
           plan="default-applied-only 400s leftover omit. Abandon exclusive apply; dual-accept omit for one release.",
           residual="client still omits; drop after client 5",
           vs="r3572 examples-plural-keyword (schema default, not examples)",
           fetch1=f"{JS}/generic.html#annotation",
           fetch1_ok="default is annotation unless the runtime applies it.",
           fetch2=f"{OAS}#schema-object", fetch2_ok="Exclusive apply 400s leftover omit."),
        bad(slug="omit-default", domain="omit-default-vs-applied", name="omdef", field="default",
            old="applied leftover", new="omit default",
            fail_err="400: leftover applied after omit-only",
            plan="omit-only 400s leftover applied. Abandon exclusive omit; keep applied — forms want omit. Freeze applied, spec omit.",
            residual="handoff: keep applied or force omit; do not claim omit shipped",
            vs="r3572 examples-plural-keyword (omit default leftover, not examples)",
            fetch1=f"{JS}/generic.html#annotation",
            fetch1_ok="Omitting default is not applying it.",
            fetch2=f"{OAS}#schema-object", fetch2_ok="Exclusive omit 400s leftover applied."),
    ),
    (
        ok(slug="accept-language-bcp47", domain="accept-language-bcp47-vs-iso639", name="albcp", field="Accept-Language",
           old="ISO leftover 639-1", new="BCP 47 hyphen tags",
           fail_err="400: leftover en after bcp47-only",
           plan="bcp47-only 400s leftover ISO 639-1. Abandon exclusive BCP 47; dual-accept 639-1 for one release.",
           residual="app still 639-1; drop after app 3",
           vs="wrap locale-bcp47-hyphen (Accept-Language, not locale field)",
           fetch1="https://www.rfc-editor.org/rfc/rfc9110.html#name-accept-language",
           fetch1_ok="Accept-Language uses BCP 47 tags.",
           fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive BCP 47 400s leftover 639-1."),
        bad(slug="iso639-language", domain="iso639-vs-accept-language-bcp47", name="iso639", field="Accept-Language",
            old="BCP leftover 47", new="ISO 639-1 only",
            fail_err="400: leftover en-US after 639-1-only",
            plan="639-1-only 400s leftover BCP 47. Abandon exclusive 639-1; keep BCP 47 — i18n wants 639-1. Freeze BCP 47, spec 639-1.",
            residual="handoff: keep BCP 47 or force 639-1; do not claim 639-1 shipped",
            vs="wrap locale-bcp47-hyphen (ISO 639 leftover, not locale field)",
            fetch1="https://www.rfc-editor.org/rfc/rfc5646.html",
            fetch1_ok="ISO 639-1 is not a full BCP 47 tag.",
            fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive 639-1 400s leftover BCP 47."),
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
    print(json.dumps({"round": round_n, "idx": idx, "ids": [e1["id"], e2["id"]], "catalog": "g46-w6"}))


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
