#!/usr/bin/env python3
"""Fifth unique OpenAPI-drift ACM catalog after r3915 mill.

BAN r3866 proto-optional, r3850 accept-language/iso639, r3713 smile/cbor,
r3560 422/207, w131 cartesian, r3561–r3851 leftover leftover leftover,
and r3867/r3883/r3899/r3915 OAS plants.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("acm_mill_r3561", HERE / "acm-mill-r3561.py")
_b = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_b)

plant = _b.plant
GEN = _b.GEN
BANNED_BLOB = _b.BANNED_BLOB
build_episode = _b.build_episode
notes_text = _b.notes_text
published_slugs = _b.published_slugs

priors = [
    "acm-mill-r3620.py",
    "acm-mill-r3667.py",
    "acm-mill-r3698.py",
    "acm-mill-r3714.py",
    "acm-mill-r3787.py",
    "acm-mill-r3851.py",
    "acm-mill-r3867.py",
    "acm-mill-r3883.py",
    "acm-mill-r3899.py",
    "acm-mill-r3915.py",
]
BANNED_PRIOR = {p[0]["slug"] for p in _b.PAIRS} | {p[1]["slug"] for p in _b.PAIRS}
for fname in priors:
    sp = importlib.util.spec_from_file_location(fname.replace("-", "_"), HERE / fname)
    mod = importlib.util.module_from_spec(sp)
    assert sp.loader is not None
    sp.loader.exec_module(mod)
    BANNED_PRIOR |= {p[0]["slug"] for p in mod.PAIRS} | {p[1]["slug"] for p in mod.PAIRS}

BANNED_PRIOR |= {
    "oas-lll4-proto-optional",
    "protobuf-lll4-optional-oas",
    "accept-language-bcp47",
    "iso639-language",
    "smile-binary-json",
    "cbor-majortype-vs-smile",
    "422-vs-400-validation",
    "207-multistatus-batch",
}

PAIRS: list[tuple[dict, dict]] = [
    (
        plant(
            slug="oas-format-regex",
            domain="oas-format-regex-vs-glob-pattern",
            success=True,
            name="fmtre",
            stack="OpenAPI 3.1 format=regex + Go",
            field="format",
            old="glob pattern leftover",
            new="format regex",
            fail_err="400: leftover glob after format-regex-only",
            plan="format=regex-only 400s leftover glob. Dual-read glob for one release.",
            residual="filter still glob leftover; drop after filter 5",
            vs="r3899 oas-pattern-anchor (format=regex vs glob leftover, not anchored pattern)",
            fetch1="https://json-schema.org/understanding-json-schema/reference/regular_expressions",
            fetch1_ok="format=regex is a regex, not a leftover glob.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types",
            fetch2_ok="Exclusive format=regex 400 leftover glob.",
        ),
        plant(
            slug="leftover-glob-pattern",
            domain="glob-pattern-vs-oas-format-regex",
            success=False,
            name="globp",
            stack="OpenAPI leftover glob pattern + Java + TS",
            field="glob",
            old="format regex",
            new="glob pattern leftover only",
            fail_err="400: leftover regex after glob-only",
            plan="Glob-only 400s leftover format=regex. Freeze regex, spec glob leftover.",
            residual="handoff: keep format=regex or force glob leftover",
            vs="r3899 leftover-unanchored-regex (glob leftover, not unanchored)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types",
            fetch1_ok="Globs are not format=regex.",
            fetch2="https://json-schema.org/understanding-json-schema/reference/regular_expressions",
            fetch2_ok="Exclusive glob 400 leftover format=regex.",
        ),
    ),
    (
        plant(
            slug="oas-maximum-inclusive",
            domain="oas-maximum-vs-unbounded-number",
            success=True,
            name="maxnum",
            stack="OpenAPI 3.1 maximum + Go",
            field="maximum",
            old="unbounded number leftover",
            new="inclusive maximum",
            fail_err="400: leftover unbounded number after maximum-only",
            plan="maximum-only 400s leftover unbounded number. Dual-accept unbounded for one release.",
            residual="meter still unbounded leftover; drop after meter 6",
            vs="r3867 oas31-exclmin-numeric (inclusive maximum vs unbounded leftover, not exclusiveMinimum)",
            fetch1="https://json-schema.org/understanding-json-schema/reference/numeric#range",
            fetch1_ok="maximum is inclusive; leftover unbounded numbers fail closed.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object",
            fetch2_ok="Exclusive maximum 400 leftover unbounded number.",
        ),
        plant(
            slug="leftover-unbounded-number",
            domain="unbounded-number-vs-oas-maximum",
            success=False,
            name="unbnum",
            stack="OpenAPI leftover unbounded number + Java + TS",
            field="type",
            old="inclusive maximum",
            new="unbounded number leftover only",
            fail_err="400: leftover maximum after unbounded-only",
            plan="Unbounded-only 400s leftover maximum. Freeze maximum, spec unbounded leftover.",
            residual="handoff: keep maximum or force unbounded leftover",
            vs="r3867 oas30-exclmin-flag (unbounded leftover, not exclusiveMinimum bool)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object",
            fetch1_ok="Unbounded numbers are not maximum.",
            fetch2="https://json-schema.org/understanding-json-schema/reference/numeric#range",
            fetch2_ok="Exclusive unbounded number 400 leftover maximum.",
        ),
    ),
    (
        plant(
            slug="oas-multipleof-decimal",
            domain="oas-multipleof-vs-int-only",
            success=True,
            name="multdec",
            stack="OpenAPI 3.1 multipleOf decimal + Go",
            field="multipleOf",
            old="int only leftover",
            new="decimal multipleOf",
            fail_err="400: leftover int-only after multipleOf-decimal-only",
            plan="multipleOf-decimal-only 400s leftover int-only. Dual-read int for one release.",
            residual="ledger still int leftover; drop after ledger 5",
            vs="wrap multipleof-cents (decimal multipleOf vs int leftover, not cents)",
            fetch1="https://json-schema.org/understanding-json-schema/reference/numeric#multiples",
            fetch1_ok="multipleOf 0.01 is not leftover integer-only.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object",
            fetch2_ok="Exclusive multipleOf decimal 400 leftover int-only.",
        ),
        plant(
            slug="leftover-int-only",
            domain="int-only-vs-oas-multipleof",
            success=False,
            name="intonly",
            stack="OpenAPI leftover int-only + Java + TS",
            field="type",
            old="decimal multipleOf",
            new="int only leftover only",
            fail_err="400: leftover multipleOf after int-only",
            plan="Int-only 400s leftover multipleOf. Freeze multipleOf, spec int leftover.",
            residual="handoff: keep multipleOf or force int leftover",
            vs="wrap multipleof-cents (int leftover, not cents cartesian)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object",
            fetch1_ok="Integer-only is not multipleOf decimal.",
            fetch2="https://json-schema.org/understanding-json-schema/reference/numeric#multiples",
            fetch2_ok="Exclusive int-only 400 leftover multipleOf.",
        ),
    ),
    (
        plant(
            slug="oas-uniqueitems-true",
            domain="oas-uniqueitems-vs-dup-ok",
            success=True,
            name="uniqit",
            stack="OpenAPI 3.1 uniqueItems + Go",
            field="uniqueItems",
            old="dup ok leftover",
            new="uniqueItems true",
            fail_err="400: leftover dup-ok after uniqueItems-only",
            plan="uniqueItems-only 400s leftover dup-ok. Dual-accept dups for one release.",
            residual="batch still dup leftover; drop after batch 4",
            vs="wrap uniqueitems-sku (uniqueItems vs dup leftover, not sku)",
            fetch1="https://json-schema.org/understanding-json-schema/reference/array#uniqueitems",
            fetch1_ok="uniqueItems true rejects leftover duplicate arrays.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object",
            fetch2_ok="Exclusive uniqueItems 400 leftover dup-ok.",
        ),
        plant(
            slug="leftover-dup-ok",
            domain="dup-ok-vs-oas-uniqueitems",
            success=False,
            name="dupok",
            stack="OpenAPI leftover dup-ok + Java + TS",
            field="items",
            old="uniqueItems true",
            new="dup ok leftover only",
            fail_err="400: leftover uniqueItems after dup-ok-only",
            plan="Dup-ok-only 400s leftover uniqueItems. Freeze uniqueItems, spec dup leftover.",
            residual="handoff: keep uniqueItems or force dup leftover",
            vs="wrap uniqueitems-sku (dup leftover, not sku cartesian)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object",
            fetch1_ok="Dup-ok arrays are not uniqueItems.",
            fetch2="https://json-schema.org/understanding-json-schema/reference/array#uniqueitems",
            fetch2_ok="Exclusive dup-ok 400 leftover uniqueItems.",
        ),
    ),
    (
        plant(
            slug="oas-format-date",
            domain="oas-format-date-vs-epoch-day",
            success=True,
            name="fmtdate",
            stack="OpenAPI 3.1 format=date + Go",
            field="format",
            old="epoch day leftover",
            new="format date",
            fail_err="400: leftover epoch-day after format-date-only",
            plan="format=date-only 400s leftover epoch-day. Dual-read epoch-day for one release.",
            residual="report still epoch leftover; drop after report 6",
            vs="wrap date-only-due-on (format=date vs epoch-day leftover, not due-on)",
            fetch1="https://json-schema.org/understanding-json-schema/reference/string#dates-and-times",
            fetch1_ok="format=date is RFC 3339 full-date, not leftover epoch days.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types",
            fetch2_ok="Exclusive format=date 400 leftover epoch-day.",
        ),
        plant(
            slug="leftover-epoch-day",
            domain="epoch-day-vs-oas-format-date",
            success=False,
            name="epday",
            stack="OpenAPI leftover epoch day + Java + TS",
            field="days",
            old="format date",
            new="epoch day leftover only",
            fail_err="400: leftover format=date after epoch-day-only",
            plan="Epoch-day-only 400s leftover format=date. Freeze date, spec epoch leftover.",
            residual="handoff: keep format=date or force epoch leftover",
            vs="wrap date-only-due-on (epoch leftover, not due-on cartesian)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types",
            fetch1_ok="Epoch days are not format=date.",
            fetch2="https://json-schema.org/understanding-json-schema/reference/string#dates-and-times",
            fetch2_ok="Exclusive epoch-day 400 leftover format=date.",
        ),
    ),
    (
        plant(
            slug="oas-format-date-time",
            domain="oas-date-time-vs-epoch-ms",
            success=True,
            name="fmtdt",
            stack="OpenAPI 3.1 format=date-time + Go",
            field="format",
            old="epoch ms leftover",
            new="format date-time",
            fail_err="400: leftover epoch-ms after date-time-only",
            plan="format=date-time-only 400s leftover epoch-ms. Dual-read epoch-ms for one release.",
            residual="stream still epoch leftover; drop after stream 5",
            vs="r3915 oas-format-time (date-time vs epoch-ms leftover, not format=time)",
            fetch1="https://json-schema.org/understanding-json-schema/reference/string#dates-and-times",
            fetch1_ok="format=date-time is RFC 3339, not leftover epoch milliseconds.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types",
            fetch2_ok="Exclusive date-time 400 leftover epoch-ms.",
        ),
        plant(
            slug="leftover-epoch-ms",
            domain="epoch-ms-vs-oas-date-time",
            success=False,
            name="epms",
            stack="OpenAPI leftover epoch ms + Java + TS",
            field="millis",
            old="format date-time",
            new="epoch ms leftover only",
            fail_err="400: leftover date-time after epoch-ms-only",
            plan="Epoch-ms-only 400s leftover date-time. Freeze date-time, spec epoch leftover.",
            residual="handoff: keep date-time or force epoch leftover",
            vs="r3915 leftover-hhmm-string (epoch-ms leftover, not hhmm)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types",
            fetch1_ok="Epoch milliseconds are not format=date-time.",
            fetch2="https://json-schema.org/understanding-json-schema/reference/string#dates-and-times",
            fetch2_ok="Exclusive epoch-ms 400 leftover date-time.",
        ),
    ),
    (
        plant(
            slug="oas-content-media-type",
            domain="oas-contentmediatype-vs-untyped-blob",
            success=True,
            name="cmt",
            stack="OpenAPI 3.1 contentMediaType + Go",
            field="contentMediaType",
            old="untyped blob leftover",
            new="contentMediaType",
            fail_err="415: leftover untyped blob after contentMediaType-only",
            plan="contentMediaType-only 415s leftover untyped blob. Dual-read blob for one release.",
            residual="store still blob leftover; drop after store 6",
            vs="r3915 oas-content-b64url (contentMediaType vs untyped blob, not base64url)",
            fetch1="https://json-schema.org/understanding-json-schema/reference/non_json_data#contentmediatype",
            fetch1_ok="contentMediaType declares the decoded media, not leftover untyped blobs.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object",
            fetch2_ok="Exclusive contentMediaType 415 leftover untyped blob.",
        ),
        plant(
            slug="leftover-untyped-blob",
            domain="untyped-blob-vs-oas-contentmediatype",
            success=False,
            name="ublob",
            stack="OpenAPI leftover untyped blob + Java + TS",
            field="blob",
            old="contentMediaType",
            new="untyped blob leftover only",
            fail_err="415: leftover contentMediaType after blob-only",
            plan="Blob-only 415s leftover contentMediaType. Freeze contentMediaType, spec blob leftover.",
            residual="handoff: keep contentMediaType or force blob leftover",
            vs="r3915 leftover-std-b64 (untyped blob leftover, not std base64)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object",
            fetch1_ok="Untyped blobs are not contentMediaType.",
            fetch2="https://json-schema.org/understanding-json-schema/reference/non_json_data#contentmediatype",
            fetch2_ok="Exclusive untyped blob 415 leftover contentMediaType.",
        ),
    ),
    (
        plant(
            slug="oas-xml-prefix",
            domain="oas-xml-prefix-vs-no-prefix",
            success=True,
            name="xmlpre",
            stack="OpenAPI 3.1 xml.prefix + Go",
            field="prefix",
            old="no prefix leftover",
            new="xml prefix",
            fail_err="415: leftover no-prefix after xml-prefix-only",
            plan="xml.prefix-only 415s leftover no-prefix. Dual-read no-prefix for one release.",
            residual="batch still no-prefix leftover; drop after batch 5",
            vs="r3899 oas-xml-namespace (xml.prefix vs no-prefix leftover, not namespace)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#xml-object",
            fetch1_ok="xml.prefix is not leftover unqualified names.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object",
            fetch2_ok="Exclusive xml.prefix 415 leftover no-prefix.",
        ),
        plant(
            slug="leftover-no-prefix",
            domain="no-prefix-vs-oas-xml-prefix",
            success=False,
            name="nopre",
            stack="OpenAPI leftover no xml prefix + Java + TS",
            field="name",
            old="xml prefix",
            new="no prefix leftover only",
            fail_err="415: leftover xml.prefix after no-prefix-only",
            plan="No-prefix-only 415s leftover xml.prefix. Freeze prefix, spec no-prefix leftover.",
            residual="handoff: keep xml.prefix or force no-prefix leftover",
            vs="r3899 leftover-unqualified-xml (no-prefix leftover, not unqualified ns)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object",
            fetch1_ok="No-prefix XML is not xml.prefix.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#xml-object",
            fetch2_ok="Exclusive no-prefix 415 leftover xml.prefix.",
        ),
    ),
    (
        plant(
            slug="oas-servers-multiple",
            domain="oas-multi-server-vs-single-server",
            success=True,
            name="srvmul",
            stack="OpenAPI 3.1 multiple servers + Go",
            field="servers",
            old="single server leftover",
            new="multiple servers",
            fail_err="400: leftover single server after multi-server-only",
            plan="Multi-server-only 400s leftover single server. Dual-accept single for one release.",
            residual="sdk still single leftover; drop after sdk 7",
            vs="r3883 oas-servers-url-template (multiple servers vs single leftover, not url template)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#oasServers",
            fetch1_ok="servers is an array, not a leftover single host.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#server-object",
            fetch2_ok="Exclusive multiple servers 400 leftover single.",
        ),
        plant(
            slug="leftover-single-server",
            domain="single-server-vs-oas-multi-server",
            success=False,
            name="srvsgl",
            stack="OpenAPI leftover single server + Java + TS",
            field="url",
            old="multiple servers",
            new="single server leftover only",
            fail_err="400: leftover multiple servers after single-only",
            plan="Single-only 400s leftover multiple servers. Freeze array, spec single leftover.",
            residual="handoff: keep multiple servers or force single leftover",
            vs="r3883 leftover-hardcoded-host (single leftover, not hardcoded host)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#server-object",
            fetch1_ok="A single leftover host is not servers[].",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#oasServers",
            fetch2_ok="Exclusive single server 400 leftover multiple.",
        ),
    ),
    (
        plant(
            slug="oas-operation-deprecated",
            domain="oas-op-deprecated-vs-live-op",
            success=True,
            name="opdep",
            stack="OpenAPI 3.1 operation deprecated + Go",
            field="deprecated",
            old="live op leftover",
            new="operation deprecated",
            fail_err="400: leftover live op after deprecated-only",
            plan="Deprecated-op-only 400s leftover live op. Dual-keep live for one release.",
            residual="portal still live leftover; drop after portal 4",
            vs="r3867 leftover-deprecated-flag (operation deprecated vs live leftover, not Sunset)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#operation-object",
            fetch1_ok="deprecated:true marks the operation, leftover live ops ignore it.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#fixed-fields-8",
            fetch2_ok="Exclusive deprecated op 400 leftover live.",
        ),
        plant(
            slug="leftover-live-op",
            domain="live-op-vs-oas-op-deprecated",
            success=False,
            name="oplive",
            stack="OpenAPI leftover live op + Java + TS",
            field="deprecated",
            old="operation deprecated",
            new="live op leftover only",
            fail_err="400: leftover deprecated after live-only",
            plan="Live-only 400s leftover deprecated op. Freeze deprecated, spec live leftover.",
            residual="handoff: keep deprecated op or force live leftover",
            vs="r3867 oas-sunset-http-date (live leftover, not Sunset date)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#fixed-fields-8",
            fetch1_ok="Live leftover ops are not deprecated:true.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#operation-object",
            fetch2_ok="Exclusive live op 400 leftover deprecated.",
        ),
    ),
    (
        plant(
            slug="oas-path-label-style",
            domain="oas-path-label-vs-slash-path",
            success=True,
            name="plabel",
            stack="OpenAPI 3.1 path style=label + Go",
            field="style",
            old="slash path leftover",
            new="path label style",
            fail_err="400: leftover slash path after label-only",
            plan="Path-label-only 400s leftover slash path. Dual-read slash for one release.",
            residual="router still slash leftover; drop after router 5",
            vs="r3883 oas-path-matrix-style (label vs slash leftover, not matrix)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#style-values",
            fetch1_ok="Path style=label is not leftover slash-delimited simple.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object",
            fetch2_ok="Exclusive path label 400 leftover slash path.",
        ),
        plant(
            slug="leftover-slash-path",
            domain="slash-path-vs-oas-path-label",
            success=False,
            name="pslash",
            stack="OpenAPI leftover slash path + Java + TS",
            field="style",
            old="path label style",
            new="slash path leftover only",
            fail_err="400: leftover label after slash-only",
            plan="Slash-only 400s leftover path label. Freeze label, spec slash leftover.",
            residual="handoff: keep path label or force slash leftover",
            vs="r3883 leftover-path-simple (slash leftover, not simple)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object",
            fetch1_ok="Slash paths are not style=label.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#style-values",
            fetch2_ok="Exclusive slash path 400 leftover label.",
        ),
    ),
    (
        plant(
            slug="oas-query-form-explode",
            domain="oas-query-explode-vs-unexplode-query",
            success=True,
            name="qexpl",
            stack="OpenAPI 3.1 query form explode + Go",
            field="explode",
            old="unexplode query leftover",
            new="query form explode",
            fail_err="400: leftover unexplode query after explode-only",
            plan="Query-explode-only 400s leftover unexplode. Dual-read unexplode for one release.",
            residual="gateway still unexplode leftover; drop after gateway 6",
            vs="r3899 oas-encoding-explode-form (query explode vs unexplode leftover, not encoding.explode)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#style-values",
            fetch1_ok="Query form explode is not leftover comma-unexploded form.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object",
            fetch2_ok="Exclusive query explode 400 leftover unexplode.",
        ),
        plant(
            slug="leftover-unexplode-query",
            domain="unexplode-query-vs-oas-query-explode",
            success=False,
            name="qunx",
            stack="OpenAPI leftover unexplode query + Java + TS",
            field="explode",
            old="query form explode",
            new="unexplode query leftover only",
            fail_err="400: leftover explode after unexplode-only",
            plan="Unexplode-only 400s leftover query explode. Freeze explode, spec unexplode leftover.",
            residual="handoff: keep query explode or force unexplode leftover",
            vs="r3899 leftover-encoding-unexplode (query unexplode leftover, not encoding)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object",
            fetch1_ok="Unexploded query is not form explode.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#style-values",
            fetch2_ok="Exclusive unexplode query 400 leftover explode.",
        ),
    ),
    (
        plant(
            slug="oas-format-relative-json-pointer",
            domain="oas-rel-json-pointer-vs-rel-dotpath",
            success=True,
            name="relptr",
            stack="OpenAPI 3.1 format=relative-json-pointer + Go",
            field="format",
            old="relative dotpath leftover",
            new="format relative-json-pointer",
            fail_err="400: leftover relative dotpath after rel-pointer-only",
            plan="relative-json-pointer-only 400s leftover relative dotpath. Dual-read dotpath for one release.",
            residual="patch still dotpath leftover; drop after patch 6",
            vs="r3915 oas-format-json-pointer (relative-json-pointer vs rel-dotpath leftover, not absolute pointer)",
            fetch1="https://json-schema.org/understanding-json-schema/reference/string#json-pointer",
            fetch1_ok="relative-json-pointer is not a leftover relative dotpath.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types",
            fetch2_ok="Exclusive relative-json-pointer 400 leftover rel-dotpath.",
        ),
        plant(
            slug="leftover-rel-dotpath",
            domain="rel-dotpath-vs-oas-rel-json-pointer",
            success=False,
            name="reldot",
            stack="OpenAPI leftover relative dotpath + Java + TS",
            field="path",
            old="format relative-json-pointer",
            new="relative dotpath leftover only",
            fail_err="400: leftover relative-json-pointer after rel-dotpath-only",
            plan="Rel-dotpath-only 400s leftover relative-json-pointer. Freeze pointer, spec dotpath leftover.",
            residual="handoff: keep relative-json-pointer or force rel-dotpath leftover",
            vs="r3915 leftover-dotpath (rel-dotpath leftover, not absolute dotpath)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types",
            fetch1_ok="Relative dotpaths are not relative-json-pointer.",
            fetch2="https://json-schema.org/understanding-json-schema/reference/string#json-pointer",
            fetch2_ok="Exclusive rel-dotpath 400 leftover relative-json-pointer.",
        ),
    ),
    (
        plant(
            slug="oas-minimum-inclusive",
            domain="oas-minimum-vs-unbounded-low",
            success=True,
            name="minnum",
            stack="OpenAPI 3.1 minimum + Go",
            field="minimum",
            old="unbounded low leftover",
            new="inclusive minimum",
            fail_err="400: leftover unbounded-low after minimum-only",
            plan="minimum-only 400s leftover unbounded-low. Dual-accept unbounded-low for one release.",
            residual="meter still low leftover; drop after meter 4",
            vs="r3867 oas31-exclmin-numeric (inclusive minimum vs unbounded-low leftover, not exclusiveMinimum)",
            fetch1="https://json-schema.org/understanding-json-schema/reference/numeric#range",
            fetch1_ok="minimum is inclusive; leftover unbounded lows fail closed.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object",
            fetch2_ok="Exclusive minimum 400 leftover unbounded-low.",
        ),
        plant(
            slug="leftover-unbounded-low",
            domain="unbounded-low-vs-oas-minimum",
            success=False,
            name="unblow",
            stack="OpenAPI leftover unbounded low + Java + TS",
            field="type",
            old="inclusive minimum",
            new="unbounded low leftover only",
            fail_err="400: leftover minimum after unbounded-low-only",
            plan="Unbounded-low-only 400s leftover minimum. Freeze minimum, spec low leftover.",
            residual="handoff: keep minimum or force unbounded-low leftover",
            vs="r3867 oas30-exclmin-flag (unbounded-low leftover, not exclusiveMinimum bool)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object",
            fetch1_ok="Unbounded lows are not minimum.",
            fetch2="https://json-schema.org/understanding-json-schema/reference/numeric#range",
            fetch2_ok="Exclusive unbounded-low 400 leftover minimum.",
        ),
    ),
    (
        plant(
            slug="oas-info-terms-url",
            domain="oas-terms-url-vs-missing-terms",
            success=True,
            name="terms",
            stack="OpenAPI 3.1 info.termsOfService + Go",
            field="termsOfService",
            old="missing terms leftover",
            new="termsOfService url",
            fail_err="400: leftover missing terms after terms-url-only",
            plan="termsOfService-only 400s leftover missing terms. Dual-omit terms for one release.",
            residual="portal still missing leftover; drop after portal 5",
            vs="r3883 oas-info-license-identifier (terms URL vs missing leftover, not license identifier)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#info-object",
            fetch1_ok="termsOfService is a URL, leftover missing terms fail closed.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#fixed-fields",
            fetch2_ok="Exclusive terms URL 400 leftover missing terms.",
        ),
        plant(
            slug="leftover-missing-terms",
            domain="missing-terms-vs-oas-terms-url",
            success=False,
            name="noterms",
            stack="OpenAPI leftover missing terms + Java + TS",
            field="info",
            old="termsOfService url",
            new="missing terms leftover only",
            fail_err="400: leftover terms URL after missing-only",
            plan="Missing-only 400s leftover terms URL. Freeze terms, spec missing leftover.",
            residual="handoff: keep terms URL or force missing leftover",
            vs="r3883 leftover-license-url-only (missing terms leftover, not license url)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#fixed-fields",
            fetch1_ok="Missing terms are not termsOfService.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#info-object",
            fetch2_ok="Exclusive missing terms 400 leftover terms URL.",
        ),
    ),
    (
        plant(
            slug="oas-response-headers-required",
            domain="oas-required-resp-header-vs-optional-resp",
            success=True,
            name="rhreq",
            stack="OpenAPI 3.1 required response header + Go",
            field="required",
            old="optional resp header leftover",
            new="required response header",
            fail_err="400: leftover optional resp header after required-only",
            plan="Required-response-header-only 400s leftover optional. Dual-omit for one release.",
            residual="sdk still optional leftover; drop after sdk 5",
            vs="r3899 oas-header-required-true (response header required vs optional leftover, not request header)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#header-object",
            fetch1_ok="required:true on response headers is not leftover optional.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#response-object",
            fetch2_ok="Exclusive required response header 400 leftover optional.",
        ),
        plant(
            slug="leftover-optional-resp-header",
            domain="optional-resp-vs-oas-required-resp-header",
            success=False,
            name="rhopt",
            stack="OpenAPI leftover optional resp header + Java + TS",
            field="required",
            old="required response header",
            new="optional resp header leftover only",
            fail_err="400: leftover required resp header after optional-only",
            plan="Optional-only 400s leftover required response header. Freeze required, spec optional leftover.",
            residual="handoff: keep required response header or force optional leftover",
            vs="r3899 leftover-optional-header (optional resp leftover, not request header)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#response-object",
            fetch1_ok="Optional response headers are not required:true.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#header-object",
            fetch2_ok="Exclusive optional resp header 400 leftover required.",
        ),
    ),
]


def catalog_selfcheck() -> None:
    seen: set[str] = set()
    if len(PAIRS) < 12:
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
            if "smile" in slug or "cbor" in slug:
                raise SystemExit(f"banned smile/cbor {slug}")
            if "lll4" in slug or "accept-language" in slug or "iso639" in slug:
                raise SystemExit(f"banned prior plant {slug}")


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
        assert "[variant" not in e["goal"] and "-w131" not in e["id"]
        assert e["id"].startswith(f"acm-r{round_n:04d}-")
    batch = staging / f"batch-r{round_n:02d}.jsonl"
    notes = staging / f"NOTES-r{round_n:02d}.md"
    batch.write_text(json.dumps(e1, ensure_ascii=False) + "\n" + json.dumps(e2, ensure_ascii=False) + "\n")
    notes.write_text(notes_text(round_n, [e1, e2], [t1, t2], idx))
    print(json.dumps({"round": round_n, "idx": idx, "ids": [e1["id"], e2["id"]], "catalog": "r3931"}))


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
