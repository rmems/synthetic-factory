#!/usr/bin/env python3
"""Eighth leftover unique ACM catalog after g46-w4 exhausts at r3802."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("acm_w4", HERE / "acm-mill-g46-w4.py")
_w4 = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_w4)

ok = _w4.ok
bad = _w4.bad
GEN = _w4.GEN
BANNED_BLOB = _w4.BANNED_BLOB
BANNED_SLUG_NEEDLES = _w4.BANNED_SLUG_NEEDLES
build_episode = _w4.build_episode
notes_text = _w4.notes_text
published_slugs = _w4.published_slugs
OAS = _w4.OAS
JS = _w4.JS

BANNED_PRIOR = set(_w4.BANNED_PRIOR)
BANNED_PRIOR |= {p[0]["slug"] for p in _w4.PAIRS} | {p[1]["slug"] for p in _w4.PAIRS}

PAIRS: list[tuple[dict, dict]] = [
    (
        ok(slug="origin-frame-rfc8336", domain="origin-frame-vs-host-only", name="origf", field="ORIGIN",
           old="Host leftover only", new="HTTP/2 ORIGIN frame",
           fail_err="400: leftover Host-only after ORIGIN-only",
           plan="ORIGIN-only 400s leftover Host. Abandon exclusive ORIGIN; dual-accept Host-only for one release.",
           residual="proxy still Host; drop after proxy 3",
           vs="r3568 servers-trailing-slash (ORIGIN frame RFC 8336, not servers slash)",
           fetch1="https://www.rfc-editor.org/rfc/rfc8336.html",
           fetch1_ok="ORIGIN advertises authoritative origins on h2.",
           fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive ORIGIN 400s leftover Host-only."),
        bad(slug="host-header-only", domain="host-only-vs-origin-frame", name="hosth", field="Host",
            old="ORIGIN leftover frame", new="Host only",
            fail_err="400: leftover ORIGIN after Host-only",
            plan="Host-only 400s leftover ORIGIN. Abandon exclusive Host; keep ORIGIN — h1 wants Host. Freeze ORIGIN, spec Host.",
            residual="handoff: keep ORIGIN or force Host; do not claim Host-only shipped",
            vs="r3568 servers-trailing-slash (Host leftover, not servers slash)",
            fetch1="https://www.rfc-editor.org/rfc/rfc9110.html#name-host-and-authority",
            fetch1_ok="Host is not an ORIGIN frame.",
            fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive Host 400s leftover ORIGIN."),
    ),
    (
        ok(slug="dpr-client-hint", domain="dpr-client-hint-vs-none", name="dprch", field="DPR",
           old="no-DPR leftover", new="DPR 2.0",
           fail_err="400: leftover missing DPR after required",
           plan="DPR-required 400s leftover missing. Abandon exclusive DPR; dual-accept missing for one release.",
           residual="desktop still missing; drop after desktop 2",
           vs="r3620 critical-ch-ua (DPR hint, not Critical-CH)",
           fetch1="https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/DPR",
           fetch1_ok="DPR reports device pixel ratio.",
           fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive DPR 400s leftover omitters."),
        bad(slug="no-dpr-hint", domain="no-dpr-vs-required", name="nodpr", field="DPR",
            old="2.0 leftover", new="no DPR",
            fail_err="400: leftover DPR after none-only",
            plan="none-only 400s leftover DPR. Abandon exclusive omit; keep DPR — images want omit. Freeze DPR, spec omit.",
            residual="handoff: keep DPR or force omit; do not claim none shipped",
            vs="r3620 critical-ch-ua (no DPR leftover, not Critical-CH)",
            fetch1="https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/DPR",
            fetch1_ok="Omitting DPR is not the 2.0 hint.",
            fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive omit 400s leftover DPR."),
    ),
    (
        ok(slug="sec-ch-ua-model", domain="sec-ch-ua-model-vs-ua-string", name="uamodel", field="Sec-CH-UA-Model",
           old="User-Agent leftover string", new="Sec-CH-UA-Model Pixel",
           fail_err="400: leftover UA string after model-only",
           plan="model-only 400s leftover UA. Abandon exclusive model; dual-read UA string for one release.",
           residual="analytics still UA; drop after analytics 5",
           vs="r3620 critical-ch-ua (Sec-CH-UA-Model, not Critical-CH)",
           fetch1="https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Sec-CH-UA-Model",
           fetch1_ok="Sec-CH-UA-Model is the device model hint.",
           fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive model 400s leftover UA strings."),
        bad(slug="ua-string-only", domain="ua-string-vs-sec-ch-ua-model", name="uastr", field="User-Agent",
            old="model leftover Pixel", new="User-Agent only",
            fail_err="400: leftover model after UA-only",
            plan="UA-only 400s leftover model. Abandon exclusive UA; keep model — logs want UA. Freeze model, spec UA.",
            residual="handoff: keep model or force UA; do not claim UA-only shipped",
            vs="r3620 critical-ch-ua (UA leftover, not Critical-CH)",
            fetch1="https://www.rfc-editor.org/rfc/rfc9110.html#name-user-agent",
            fetch1_ok="User-Agent is not Sec-CH-UA-Model.",
            fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive UA 400s leftover model."),
    ),
    (
        ok(slug="json-schema-then-required", domain="then-required-vs-if-without-then", name="jsthen", field="then",
           old="if leftover no then", new="then required subschema",
           fail_err="400: leftover if-only after then-required",
           plan="then-required 400s leftover if-only. Abandon exclusive then; dual-accept if without then for one release.",
           residual="tax still if-only; drop after tax 1",
           vs="r3561 json-schema-if-then-else (then required vs missing then, not VAT if/then)",
           fetch1=f"{JS}/conditionals.html",
           fetch1_ok="then applies when if matches.",
           fetch2=f"{OAS}#schema-object", fetch2_ok="Exclusive then 400s leftover if-only."),
        bad(slug="if-without-then", domain="if-without-then-vs-then-required", name="ifonly", field="if",
            old="then leftover", new="if without then",
            fail_err="400: leftover then after if-only",
            plan="if-only 400s leftover then. Abandon exclusive if; keep then — rules want if-only. Freeze then, spec if-only.",
            residual="handoff: keep then or force if-only; do not claim if-only shipped",
            vs="r3561 json-schema-if-then-else (if leftover without then, not VAT)",
            fetch1=f"{JS}/conditionals.html",
            fetch1_ok="if without then is a no-op annotation.",
            fetch2=f"{OAS}#schema-object", fetch2_ok="Exclusive if-only 400s leftover then."),
    ),
    (
        ok(slug="oas-callback-ref", domain="callback-ref-vs-inline-callback", name="cbref", field="callbacks",
           old="inline leftover callback", new="$ref #/components/callbacks/Hook",
           fail_err="400: leftover inline after callback-ref-only",
           plan="callback-ref-only 400s leftover inline. Abandon exclusive $ref; dual-accept inline callbacks for one release.",
           residual="SDK still inline; drop after sdk 6",
           vs="r3571 webhooks-item-rename (components.callbacks $ref, not webhooks rename)",
           fetch1=f"{OAS}#callback-object",
           fetch1_ok="Callbacks may be $ref to components.",
           fetch2=f"{OAS}#components-object", fetch2_ok="Exclusive callback $ref 400s leftover inline."),
        bad(slug="inline-callback-leftover", domain="inline-callback-vs-ref", name="cbinl", field="callbacks",
            old="components leftover $ref", new="inline callback only",
            fail_err="400: leftover $ref after inline-only",
            plan="inline-only 400s leftover $ref. Abandon exclusive inline; keep $ref — bundler wants inline. Freeze $ref, spec inline.",
            residual="handoff: keep $ref or force inline; do not claim inline-only shipped",
            vs="r3571 webhooks-item-rename (inline callback leftover, not webhooks)",
            fetch1=f"{OAS}#callback-object",
            fetch1_ok="Inline callbacks are not components $ref.",
            fetch2=f"{OAS}#components-object", fetch2_ok="Exclusive inline 400s leftover $ref."),
    ),
    (
        ok(slug="expect-ct-enforce", domain="expect-ct-enforce-vs-none", name="expct", field="Expect-CT",
           old="no-Expect-CT leftover", new="Expect-CT max-age=86400, enforce",
           fail_err="400: leftover missing Expect-CT after enforce-only",
           plan="enforce-only 400s leftover missing. Abandon exclusive Expect-CT; dual-accept missing for one release.",
           residual="edge still missing; drop after edge 8",
           vs="r3577 status-308-https (Expect-CT, not 308)",
           fetch1="https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Expect-CT",
           fetch1_ok="Expect-CT enforce reports and can fail CT.",
           fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive Expect-CT 400s leftover omitters."),
        bad(slug="no-expect-ct", domain="no-expect-ct-vs-enforce", name="nexpct", field="Expect-CT",
            old="enforce leftover", new="no Expect-CT",
            fail_err="400: leftover Expect-CT after none-only",
            plan="none-only 400s leftover Expect-CT. Abandon exclusive omit; keep enforce — CT wants omit. Freeze enforce, spec omit.",
            residual="handoff: keep Expect-CT or force omit; do not claim none shipped",
            vs="r3577 status-308-https (no Expect-CT leftover, not 308)",
            fetch1="https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Expect-CT",
            fetch1_ok="Omitting Expect-CT is not enforce.",
            fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive omit 400s leftover Expect-CT."),
    ),
    (
        ok(slug="sf-decimal-item", domain="sf-decimal-vs-float-string", name="sfdec", field="Q",
           old="float leftover string", new="sf Decimal 1.25",
           fail_err="400: leftover float string after sf-decimal-only",
           plan="sf-decimal-only 400s leftover float string. Abandon exclusive Decimal; dual-read float strings for one release.",
           residual="client still float; drop after client 3",
           vs="r3587 ratelimit-policy-header (sf Decimal, not RateLimit)",
           fetch1="https://www.rfc-editor.org/rfc/rfc8941.html#name-decimals",
           fetch1_ok="sf Decimals have at most three fractional digits.",
           fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive sf Decimal 400s leftover float strings."),
        bad(slug="float-string-header", domain="float-string-vs-sf-decimal", name="fstr", field="Q",
            old="sf Decimal leftover", new="float string only",
            fail_err="400: leftover Decimal after float-only",
            plan="float-only 400s leftover Decimal. Abandon exclusive float; keep Decimal — q wants float. Freeze Decimal, spec float.",
            residual="handoff: keep sf Decimal or force float; do not claim float-string shipped",
            vs="r3587 ratelimit-policy-header (float leftover, not RateLimit)",
            fetch1="https://www.rfc-editor.org/rfc/rfc9110.html#name-field-values",
            fetch1_ok="A float string is not an sf Decimal.",
            fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive float 400s leftover Decimal."),
    ),
    (
        ok(slug="trace-disabled", domain="trace-disabled-vs-echo", name="trdis", field="TRACE",
           old="TRACE leftover echo", new="TRACE disabled",
           fail_err="400: leftover TRACE echo after disabled-only",
           plan="disabled-only 400s leftover echo. Abandon exclusive disable; dual-accept TRACE echo for one release then 405.",
           residual="probe still echoes; drop after probe 2",
           vs="r3578 status-204-no-body (TRACE disabled, not 204)",
           fetch1="https://www.rfc-editor.org/rfc/rfc9110.html#name-trace",
           fetch1_ok="TRACE echoes the request. Disabling it is a security control.",
           fetch2=f"{OAS}#operation-object", fetch2_ok="Exclusive disable 400s leftover echo."),
        bad(slug="trace-echo-leftover", domain="trace-echo-vs-disabled", name="trech", field="TRACE",
            old="disabled leftover", new="TRACE echo",
            fail_err="400: leftover disabled after echo-only",
            plan="echo-only 400s leftover disable. Abandon exclusive echo; keep disable — scanner wants echo. Freeze disable, spec echo.",
            residual="handoff: keep disable or force echo; do not claim echo shipped",
            vs="r3578 status-204-no-body (TRACE echo leftover, not 204)",
            fetch1="https://www.rfc-editor.org/rfc/rfc9110.html#name-trace",
            fetch1_ok="Echoing TRACE is not disable.",
            fetch2=f"{OAS}#operation-object", fetch2_ok="Exclusive echo 400s leftover disable."),
    ),
    (
        ok(slug="nel-success-fraction", domain="nel-success-fraction-vs-failures-only", name="nelsf", field="NEL",
           old="failure leftover only", new="success_fraction 0.01",
           fail_err="400: leftover failures-only after success-fraction-only",
           plan="success-fraction-only 400s leftover failures-only. Abandon exclusive success_fraction; dual-accept failures-only for one release.",
           residual="edge still failures-only; drop after edge 4",
           vs="r3620 nel-report-to (success_fraction, not report-to)",
           fetch1="https://www.w3.org/TR/network-error-logging/",
           fetch1_ok="success_fraction samples successful navigations.",
           fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive success_fraction 400s leftover failures-only."),
        bad(slug="nel-failures-only", domain="nel-failures-only-vs-success-fraction", name="nelfo", field="NEL",
            old="success_fraction leftover", new="failures only",
            fail_err="400: leftover success_fraction after failures-only",
            plan="failures-only 400s leftover success_fraction. Abandon exclusive failures; keep success_fraction — privacy wants failures. Freeze success_fraction, spec failures.",
            residual="handoff: keep success_fraction or force failures-only; do not claim failures-only shipped",
            vs="r3620 nel-report-to (failures-only leftover, not report-to)",
            fetch1="https://www.w3.org/TR/network-error-logging/",
            fetch1_ok="failure_fraction-only is not success_fraction.",
            fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive failures 400s leftover success_fraction."),
    ),
    (
        ok(slug="origin-isolation", domain="origin-isolation-vs-none", name="origi", field="Origin-Isolation",
           old="no-isolation leftover", new="Origin-Isolation ?1",
           fail_err="400: leftover missing Origin-Isolation after required",
           plan="isolation-required 400s leftover missing. Abandon exclusive ?1; dual-accept missing for one release.",
           residual="embed still missing; drop after embed 6",
           vs="r3620 coop-same-origin (Origin-Isolation, not COOP)",
           fetch1="https://html.spec.whatwg.org/multipage/origin.html#origin-isolation",
           fetch1_ok="Origin-Isolation requests an isolated origin.",
           fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive Origin-Isolation 400s leftover omitters."),
        bad(slug="no-origin-isolation", domain="no-origin-isolation-vs-required", name="norigi", field="Origin-Isolation",
            old="?1 leftover", new="no Origin-Isolation",
            fail_err="400: leftover Origin-Isolation after none-only",
            plan="none-only 400s leftover Origin-Isolation. Abandon exclusive omit; keep ?1 — embed wants omit. Freeze ?1, spec omit.",
            residual="handoff: keep Origin-Isolation or force omit; do not claim none shipped",
            vs="r3620 coop-same-origin (no Origin-Isolation leftover, not COOP)",
            fetch1="https://html.spec.whatwg.org/multipage/origin.html#origin-isolation",
            fetch1_ok="Omitting Origin-Isolation is site-keyed.",
            fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive omit 400s leftover Origin-Isolation."),
    ),
    (
        ok(slug="json-schema-type-array", domain="type-array-vs-comma-string", name="tarr", field="tags",
           old="comma leftover string", new="type array",
           fail_err="400: leftover comma-string after array-only",
           plan="array-only 400s leftover comma-string. Abandon exclusive array; dual-split comma strings for one release.",
           residual="CSV still comma; drop after csv 4",
           vs="r3581 int64-as-string-js (type array vs comma string, not int64 string)",
           fetch1=f"{JS}/array.html",
           fetch1_ok="type array is a JSON array. leftover comma strings are not.",
           fetch2=f"{OAS}#data-types", fetch2_ok="Exclusive array 400s leftover comma strings."),
        bad(slug="comma-string-leftover", domain="comma-string-vs-type-array", name="cstr", field="tags",
            old="array leftover", new="comma string only",
            fail_err="400: leftover array after comma-only",
            plan="comma-only 400s leftover array. Abandon exclusive comma; keep array — form wants comma. Freeze array, spec comma.",
            residual="handoff: keep array or force comma; do not claim comma-string shipped",
            vs="r3581 int64-as-string-js (comma leftover, not int64 string)",
            fetch1=f"{JS}/string.html",
            fetch1_ok="A comma-separated string is not type array.",
            fetch2=f"{OAS}#data-types", fetch2_ok="Exclusive comma 400s leftover arrays."),
    ),
    (
        ok(slug="oas-example-singular", domain="example-singular-vs-examples", name="exsing", field="example",
           old="examples leftover plural", new="example singular",
           fail_err="400: leftover examples after example-only",
           plan="example-only 400s leftover examples. Abandon exclusive singular; dual-accept examples map for one release.",
           residual="docs still examples; drop after docs 3",
           vs="r3572 examples-plural-keyword (singular example leftover vs examples, not the plural plant)",
           fetch1=f"{OAS}#example-object",
           fetch1_ok="example is a single value. leftover examples is a map.",
           fetch2=f"{OAS}#schema-object", fetch2_ok="Exclusive example 400s leftover examples."),
        bad(slug="examples-map-leftover", domain="examples-map-vs-singular", name="exmap", field="examples",
            old="example leftover singular", new="examples map only",
            fail_err="400: leftover example after examples-only",
            plan="examples-only 400s leftover example. Abandon exclusive map; keep example — portal wants map. Freeze example, spec map.",
            residual="handoff: keep example or force examples; do not claim examples-only shipped",
            vs="r3572 examples-plural-keyword (examples map leftover vs the plural keyword plant)",
            fetch1=f"{OAS}#example-object",
            fetch1_ok="examples is a named map. leftover example is singular.",
            fetch2=f"{OAS}#schema-object", fetch2_ok="Exclusive examples 400s leftover example."),
    ),
    (
        ok(slug="accept-encoding-zstd", domain="accept-encoding-zstd-vs-gzip-only", name="zstd", field="Accept-Encoding",
           old="gzip leftover only", new="zstd required",
           fail_err="400: leftover gzip after zstd-only",
           plan="zstd-only 400s leftover gzip. Abandon exclusive zstd; dual-accept gzip for one release.",
           residual="CDN still gzip; drop after cdn 7",
           vs="r3563 content-encoding-base64url (Accept-Encoding zstd, not contentEncoding)",
           fetch1="https://www.rfc-editor.org/rfc/rfc8878.html",
           fetch1_ok="zstd is a content-coding. leftover gzip-only clients omit it.",
           fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive zstd 400s leftover gzip-only."),
        bad(slug="gzip-only-encoding", domain="gzip-only-vs-zstd", name="gzipo", field="Accept-Encoding",
            old="zstd leftover", new="gzip only",
            fail_err="400: leftover zstd after gzip-only",
            plan="gzip-only 400s leftover zstd. Abandon exclusive gzip; keep zstd — browsers want gzip. Freeze zstd, spec gzip.",
            residual="handoff: keep zstd or force gzip; do not claim gzip-only shipped",
            vs="r3563 content-encoding-base64url (gzip leftover, not contentEncoding)",
            fetch1="https://www.rfc-editor.org/rfc/rfc9110.html#name-accept-encoding",
            fetch1_ok="gzip-only is not zstd.",
            fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive gzip 400s leftover zstd."),
    ),
    (
        ok(slug="transfer-encoding-chunked", domain="te-chunked-vs-content-length", name="techk", field="Transfer-Encoding",
           old="Content-Length leftover delim", new="chunked required",
           fail_err="400: leftover Content-Length after chunked-only",
           plan="chunked-only 400s leftover Content-Length. Abandon exclusive chunked; dual-accept Content-Length for one release.",
           residual="proxy still Content-Length; drop after proxy 5",
           vs="wrap content-digest-rfc9530 (chunked TE, not Content-Digest)",
           fetch1="https://www.rfc-editor.org/rfc/rfc9112.html#name-transfer-encoding",
           fetch1_ok="chunked delimits without Content-Length.",
           fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive chunked 400s leftover Content-Length."),
        bad(slug="clength-delim-leftover", domain="content-length-delim-vs-chunked", name="cldel", field="Content-Length",
            old="chunked leftover", new="Content-Length delim only",
            fail_err="400: leftover chunked after Content-Length-only",
            plan="Content-Length-only 400s leftover chunked. Abandon exclusive Content-Length; keep chunked — h1 wants Content-Length. Freeze chunked, spec Content-Length.",
            residual="handoff: keep chunked or force Content-Length; do not claim Content-Length-only shipped",
            vs="wrap content-digest-rfc9530 (Content-Length delim leftover, not Content-Digest)",
            fetch1="https://www.rfc-editor.org/rfc/rfc9110.html#name-content-length",
            fetch1_ok="Content-Length delim is not chunked.",
            fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive Content-Length 400s leftover chunked."),
    ),
    (
        ok(slug="accept-patch-merge", domain="accept-patch-merge-vs-json-patch", name="apmrg", field="Accept-Patch",
           old="json-patch leftover", new="application/merge-patch+json",
           fail_err="400: leftover json-patch after merge-only",
           plan="merge-only 400s leftover json-patch. Abandon exclusive merge; dual-accept json-patch for one release.",
           residual="admin still json-patch; drop after admin 2",
           vs="wrap json-patch-vs-merge-patch (Accept-Patch merge leftover, not the wrap plant)",
           fetch1="https://www.rfc-editor.org/rfc/rfc5789.html",
           fetch1_ok="Accept-Patch lists patch media types.",
           fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive merge-patch 400s leftover json-patch."),
        bad(slug="accept-patch-jsonpatch", domain="accept-patch-json-patch-vs-merge", name="apjp", field="Accept-Patch",
            old="merge leftover", new="application/json-patch+json",
            fail_err="400: leftover merge after json-patch-only",
            plan="json-patch-only 400s leftover merge. Abandon exclusive json-patch; keep merge — SPA wants json-patch. Freeze merge, spec json-patch.",
            residual="handoff: keep merge or force json-patch; do not claim json-patch-only shipped",
            vs="wrap json-patch-vs-merge-patch (Accept-Patch json-patch leftover, not wrap plant)",
            fetch1="https://www.rfc-editor.org/rfc/rfc6902.html",
            fetch1_ok="json-patch is not merge-patch.",
            fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive json-patch 400s leftover merge."),
    ),
    (
        ok(slug="link-rel-describedby", domain="link-rel-describedby-vs-self", name="ldesc", field="Link",
           old="rel=self leftover", new="rel=describedby",
           fail_err="400: leftover rel=self after describedby-only",
           plan="describedby-only 400s leftover self. Abandon exclusive describedby; dual-accept rel=self for one release.",
           residual="client still self; drop after client 6",
           vs="r3588 link-rel-successor-version (describedby, not successor-version)",
           fetch1="https://www.rfc-editor.org/rfc/rfc8288.html",
           fetch1_ok="describedby points at a description resource.",
           fetch2=f"{OAS}#link-object", fetch2_ok="Exclusive describedby 400s leftover self."),
        bad(slug="link-rel-self-only", domain="link-rel-self-vs-describedby", name="lself", field="Link",
            old="describedby leftover", new="rel=self only",
            fail_err="400: leftover describedby after self-only",
            plan="self-only 400s leftover describedby. Abandon exclusive self; keep describedby — catalog wants self. Freeze describedby, spec self.",
            residual="handoff: keep describedby or force self; do not claim self-only shipped",
            vs="r3588 link-rel-successor-version (rel=self leftover, not successor-version)",
            fetch1="https://www.rfc-editor.org/rfc/rfc8288.html",
            fetch1_ok="rel=self is not describedby.",
            fetch2=f"{OAS}#link-object", fetch2_ok="Exclusive self 400s leftover describedby."),
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
    print(json.dumps({"round": round_n, "idx": idx, "ids": [e1["id"], e2["id"]], "catalog": "g46-w5"}))


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
