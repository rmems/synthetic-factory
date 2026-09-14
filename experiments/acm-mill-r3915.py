#!/usr/bin/env python3
"""Fourth unique OpenAPI-drift ACM catalog after r3899 mill.

BAN r3866 proto-optional, r3850 accept-language/iso639, r3713 smile/cbor,
r3560 422/207, w131 cartesian, r3561–r3851 leftover leftover leftover,
and r3867/r3883/r3899 OAS plants.
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
            slug="oas-format-time",
            domain="oas-format-time-vs-hhmm-string",
            success=True,
            name="fmttime",
            stack="OpenAPI 3.1 format=time + Go",
            field="format",
            old="hhmm string leftover",
            new="format time",
            fail_err="400: leftover hhmm after format-time-only",
            plan="format=time-only 400s leftover hhmm. Dual-read hhmm for one release.",
            residual="batch still hhmm leftover; drop after batch 5",
            vs="r3883 oas-format-duration (format=time vs hhmm leftover, not duration)",
            fetch1="https://json-schema.org/understanding-json-schema/reference/string#dates-and-times",
            fetch1_ok="format=time is RFC 3339, not an HHMM leftover string.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types",
            fetch2_ok="Exclusive format=time 400 leftover hhmm.",
        ),
        plant(
            slug="leftover-hhmm-string",
            domain="hhmm-string-vs-oas-format-time",
            success=False,
            name="hhmm",
            stack="OpenAPI leftover hhmm string + Java + TS",
            field="hhmm",
            old="format time",
            new="hhmm string leftover only",
            fail_err="400: leftover format=time after hhmm-only",
            plan="Hhmm-only 400s leftover format=time. Freeze time, spec hhmm leftover.",
            residual="handoff: keep format=time or force hhmm leftover",
            vs="r3883 leftover-seconds-int (hhmm leftover, not seconds-int)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types",
            fetch1_ok="HHMM strings are not format=time.",
            fetch2="https://json-schema.org/understanding-json-schema/reference/string#dates-and-times",
            fetch2_ok="Exclusive hhmm 400 leftover format=time.",
        ),
    ),
    (
        plant(
            slug="oas-format-uuid-string",
            domain="oas-format-uuid-vs-opaque-id",
            success=True,
            name="fmtuuid",
            stack="OpenAPI 3.1 format=uuid + Go",
            field="format",
            old="opaque id leftover",
            new="format uuid",
            fail_err="400: leftover opaque id after format-uuid-only",
            plan="format=uuid-only 400s leftover opaque id. Dual-read opaque for one release.",
            residual="crm still opaque leftover; drop after crm 6",
            vs="wrap uuid-vs-ulid (format=uuid vs opaque leftover, not ULID cartesian)",
            fetch1="https://json-schema.org/understanding-json-schema/reference/string#uuid",
            fetch1_ok="format=uuid is RFC 4122, not an opaque leftover id.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types",
            fetch2_ok="Exclusive format=uuid 400 leftover opaque id.",
        ),
        plant(
            slug="leftover-opaque-id",
            domain="opaque-id-vs-oas-format-uuid",
            success=False,
            name="opidq",
            stack="OpenAPI leftover opaque id + Java + TS",
            field="id",
            old="format uuid",
            new="opaque id leftover only",
            fail_err="400: leftover format=uuid after opaque-only",
            plan="Opaque-only 400s leftover format=uuid. Freeze uuid, spec opaque leftover.",
            residual="handoff: keep format=uuid or force opaque leftover",
            vs="wrap uuid-vs-ulid (opaque leftover, not ULID cartesian)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types",
            fetch1_ok="Opaque ids are not format=uuid.",
            fetch2="https://json-schema.org/understanding-json-schema/reference/string#uuid",
            fetch2_ok="Exclusive opaque id 400 leftover format=uuid.",
        ),
    ),
    (
        plant(
            slug="oas-minlength-token",
            domain="oas-minlength-vs-empty-string",
            success=True,
            name="minltk",
            stack="OpenAPI 3.1 minLength token + Go",
            field="minLength",
            old="empty string leftover",
            new="token minLength",
            fail_err="400: leftover empty string after minLength-only",
            plan="minLength-only 400s leftover empty string. Dual-accept empty for one release.",
            residual="form still empty leftover; drop after form 4",
            vs="r3842 minlength-code (token minLength vs empty leftover, not code)",
            fetch1="https://json-schema.org/understanding-json-schema/reference/string#length",
            fetch1_ok="minLength rejects empty leftover tokens.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object",
            fetch2_ok="Exclusive minLength 400 leftover empty string.",
        ),
        plant(
            slug="leftover-empty-string",
            domain="empty-string-vs-oas-minlength",
            success=False,
            name="emptytk",
            stack="OpenAPI leftover empty string + Java + TS",
            field="token",
            old="token minLength",
            new="empty string leftover only",
            fail_err="400: leftover minLength after empty-only",
            plan="Empty-only 400s leftover minLength. Freeze minLength, spec empty leftover.",
            residual="handoff: keep minLength or force empty leftover",
            vs="r3842 unconstrained-string (empty leftover, not unconstrained)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object",
            fetch1_ok="Empty strings are not minLength tokens.",
            fetch2="https://json-schema.org/understanding-json-schema/reference/string#length",
            fetch2_ok="Exclusive empty string 400 leftover minLength.",
        ),
    ),
    (
        plant(
            slug="oas-maxlength-token",
            domain="oas-maxlength-vs-unbounded-string",
            success=True,
            name="maxltk",
            stack="OpenAPI 3.1 maxLength token + Go",
            field="maxLength",
            old="unbounded string leftover",
            new="token maxLength",
            fail_err="400: leftover unbounded string after maxLength-only",
            plan="maxLength-only 400s leftover unbounded string. Dual-accept unbounded for one release.",
            residual="notes still unbounded leftover; drop after notes 5",
            vs="wrap maxlength-display-name (token maxLength vs unbounded leftover, not display-name)",
            fetch1="https://json-schema.org/understanding-json-schema/reference/string#length",
            fetch1_ok="maxLength caps tokens; unbounded leftover strings fail closed.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object",
            fetch2_ok="Exclusive maxLength 400 leftover unbounded string.",
        ),
        plant(
            slug="leftover-unbounded-string",
            domain="unbounded-string-vs-oas-maxlength",
            success=False,
            name="unbstr",
            stack="OpenAPI leftover unbounded string + Java + TS",
            field="token",
            old="token maxLength",
            new="unbounded string leftover only",
            fail_err="400: leftover maxLength after unbounded-only",
            plan="Unbounded-only 400s leftover maxLength. Freeze maxLength, spec unbounded leftover.",
            residual="handoff: keep maxLength or force unbounded leftover",
            vs="wrap maxlength-display-name (unbounded leftover, not display-name cartesian)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object",
            fetch1_ok="Unbounded strings are not maxLength tokens.",
            fetch2="https://json-schema.org/understanding-json-schema/reference/string#length",
            fetch2_ok="Exclusive unbounded string 400 leftover maxLength.",
        ),
    ),
    (
        plant(
            slug="oas-format-uri-template",
            domain="oas-uri-template-vs-hardcoded-href",
            success=True,
            name="uritmpl",
            stack="OpenAPI 3.1 format=uri-template + Go",
            field="format",
            old="hardcoded href leftover",
            new="format uri-template",
            fail_err="400: leftover hardcoded href after uri-template-only",
            plan="uri-template-only 400s leftover hardcoded href. Dual-read href for one release.",
            residual="sdk still href leftover; drop after sdk 6",
            vs="r3899 oas-format-iri (uri-template vs hardcoded href, not iri)",
            fetch1="https://json-schema.org/understanding-json-schema/reference/string#resource-identifiers",
            fetch1_ok="format=uri-template is RFC 6570, not a hardcoded href.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types",
            fetch2_ok="Exclusive uri-template 400 leftover hardcoded href.",
        ),
        plant(
            slug="leftover-hardcoded-href",
            domain="hardcoded-href-vs-oas-uri-template",
            success=False,
            name="hrefh",
            stack="OpenAPI leftover hardcoded href + Java + TS",
            field="href",
            old="format uri-template",
            new="hardcoded href leftover only",
            fail_err="400: leftover uri-template after href-only",
            plan="Href-only 400s leftover uri-template. Freeze template, spec href leftover.",
            residual="handoff: keep uri-template or force href leftover",
            vs="r3899 leftover-ascii-uri (hardcoded href leftover, not ascii uri)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types",
            fetch1_ok="Hardcoded hrefs are not format=uri-template.",
            fetch2="https://json-schema.org/understanding-json-schema/reference/string#resource-identifiers",
            fetch2_ok="Exclusive hardcoded href 400 leftover uri-template.",
        ),
    ),
    (
        plant(
            slug="oas-security-empty-arr",
            domain="oas-empty-security-vs-required-scheme",
            success=True,
            name="secempty",
            stack="OpenAPI 3.1 empty security array + Go",
            field="security",
            old="required scheme leftover",
            new="empty security array",
            fail_err="401: leftover required scheme after empty-security-only",
            plan="Empty-security-only 401s leftover required scheme. Dual-accept required for one release.",
            residual="gateway still required leftover; drop after gateway 5",
            vs="r3883 oas-security-and-or (empty security vs required leftover, not AND/OR)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#operation-object",
            fetch1_ok="security: [] makes auth optional, not a leftover required scheme.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#security-requirement-object",
            fetch2_ok="Exclusive empty security 401 leftover required scheme.",
        ),
        plant(
            slug="leftover-security-required",
            domain="required-scheme-vs-oas-empty-security",
            success=False,
            name="secreq",
            stack="OpenAPI leftover required scheme + Java + TS",
            field="security",
            old="empty security array",
            new="required scheme leftover only",
            fail_err="401: leftover empty security after required-only",
            plan="Required-only 401s leftover empty security. Freeze empty, spec required leftover.",
            residual="handoff: keep empty security or force required leftover",
            vs="r3883 leftover-single-scheme (required leftover, not single-scheme AND/OR)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#security-requirement-object",
            fetch1_ok="A required scheme is not security: [].",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#operation-object",
            fetch2_ok="Exclusive required scheme 401 leftover empty security.",
        ),
    ),
    (
        plant(
            slug="oas-trace-method",
            domain="oas-trace-vs-x-trace-header",
            success=True,
            name="traceop",
            stack="OpenAPI 3.1 TRACE operation + Go",
            field="trace",
            old="x-trace header leftover",
            new="TRACE operation",
            fail_err="405: leftover x-trace header after TRACE-only",
            plan="TRACE-only 405s leftover x-trace header. Dual-accept header for one release.",
            residual="proxy still header leftover; drop after proxy 6",
            vs="r3899 oas-webhook-post-only (TRACE vs x-trace leftover, not webhook POST)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#path-item-object",
            fetch1_ok="TRACE is a Path Item method, not an x-trace header.",
            fetch2="https://datatracker.ietf.org/doc/html/rfc9110#name-trace",
            fetch2_ok="Exclusive TRACE 405 leftover x-trace header.",
        ),
        plant(
            slug="leftover-x-trace-header",
            domain="x-trace-header-vs-oas-trace",
            success=False,
            name="xtrace",
            stack="OpenAPI leftover x-trace header + Java + TS",
            field="X-Trace",
            old="TRACE operation",
            new="x-trace header leftover only",
            fail_err="405: leftover TRACE after header-only",
            plan="Header-only 405s leftover TRACE. Freeze TRACE, spec header leftover.",
            residual="handoff: keep TRACE or force x-trace leftover",
            vs="r3899 leftover-webhook-get (x-trace leftover, not webhook GET)",
            fetch1="https://datatracker.ietf.org/doc/html/rfc9110#name-trace",
            fetch1_ok="An x-trace header is not the TRACE method.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#path-item-object",
            fetch2_ok="Exclusive x-trace header 405 leftover TRACE.",
        ),
    ),
    (
        plant(
            slug="oas-head-operation",
            domain="oas-head-vs-get-only-probe",
            success=True,
            name="headop",
            stack="OpenAPI 3.1 HEAD operation + Go",
            field="head",
            old="GET-only probe leftover",
            new="HEAD operation",
            fail_err="405: leftover GET-only probe after HEAD-only",
            plan="HEAD-only 405s leftover GET-only probe. Dual-accept GET probe for one release.",
            residual="cdn still GET leftover; drop after cdn 4",
            vs="r3899 oas-webhook-post-only (HEAD vs GET probe leftover, not webhook)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#path-item-object",
            fetch1_ok="HEAD is a first-class Path Item method.",
            fetch2="https://datatracker.ietf.org/doc/html/rfc9110#name-head",
            fetch2_ok="Exclusive HEAD 405 leftover GET-only probe.",
        ),
        plant(
            slug="leftover-get-only-probe",
            domain="get-only-probe-vs-oas-head",
            success=False,
            name="getprb",
            stack="OpenAPI leftover GET-only probe + Java + TS",
            field="get",
            old="HEAD operation",
            new="GET-only probe leftover only",
            fail_err="405: leftover HEAD after GET-only probe",
            plan="GET-only-probe 405s leftover HEAD. Freeze HEAD, spec GET leftover.",
            residual="handoff: keep HEAD or force GET-only leftover",
            vs="r3899 leftover-webhook-get (GET-only probe leftover, not webhook GET)",
            fetch1="https://datatracker.ietf.org/doc/html/rfc9110#name-head",
            fetch1_ok="GET-only probes are not HEAD operations.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#path-item-object",
            fetch2_ok="Exclusive GET-only probe 405 leftover HEAD.",
        ),
    ),
    (
        plant(
            slug="oas-format-ipv6",
            domain="oas-format-ipv6-vs-v4-literal",
            success=True,
            name="fmtip6",
            stack="OpenAPI 3.1 format=ipv6 + Go",
            field="format",
            old="ipv4 literal leftover",
            new="format ipv6",
            fail_err="400: leftover ipv4 literal after ipv6-only",
            plan="format=ipv6-only 400s leftover ipv4 literal. Dual-read ipv4 for one release.",
            residual="acl still ipv4 leftover; drop after acl 5",
            vs="r3841 format-ipv4-only (ipv6 vs leftover ipv4 literal, not ipv4-only plant)",
            fetch1="https://json-schema.org/understanding-json-schema/reference/string#ip-addresses",
            fetch1_ok="format=ipv6 is not an IPv4 leftover literal.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types",
            fetch2_ok="Exclusive format=ipv6 400 leftover ipv4 literal.",
        ),
        plant(
            slug="leftover-v4-literal",
            domain="v4-literal-vs-oas-format-ipv6",
            success=False,
            name="v4lit",
            stack="OpenAPI leftover ipv4 literal + Java + TS",
            field="format",
            old="format ipv6",
            new="ipv4 literal leftover only",
            fail_err="400: leftover ipv6 after ipv4-literal-only",
            plan="Ipv4-literal-only 400s leftover ipv6. Freeze ipv6, spec ipv4 leftover.",
            residual="handoff: keep format=ipv6 or force ipv4 leftover",
            vs="r3841 ipv6-literal-leftover (ipv4 leftover, not ipv6-literal plant)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types",
            fetch1_ok="IPv4 literals are not format=ipv6.",
            fetch2="https://json-schema.org/understanding-json-schema/reference/string#ip-addresses",
            fetch2_ok="Exclusive ipv4 literal 400 leftover ipv6.",
        ),
    ),
    (
        plant(
            slug="oas-content-b64url",
            domain="oas-base64url-vs-std-base64",
            success=True,
            name="b64url",
            stack="OpenAPI 3.1 contentEncoding base64url + Go",
            field="contentEncoding",
            old="std base64 leftover",
            new="base64url encoding",
            fail_err="400: leftover std base64 after base64url-only",
            plan="base64url-only 400s leftover std base64. Dual-read std for one release.",
            residual="client still std leftover; drop after client 6",
            vs="wrap binary-vs-base64 (base64url vs std leftover, not binary cartesian)",
            fetch1="https://json-schema.org/understanding-json-schema/reference/non_json_data#contentencoding",
            fetch1_ok="contentEncoding=base64url is not standard base64.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object",
            fetch2_ok="Exclusive base64url 400 leftover std base64.",
        ),
        plant(
            slug="leftover-std-b64",
            domain="std-base64-vs-oas-base64url",
            success=False,
            name="stdb64",
            stack="OpenAPI leftover std base64 + Java + TS",
            field="contentEncoding",
            old="base64url encoding",
            new="std base64 leftover only",
            fail_err="400: leftover base64url after std-only",
            plan="Std-only 400s leftover base64url. Freeze base64url, spec std leftover.",
            residual="handoff: keep base64url or force std leftover",
            vs="wrap binary-vs-base64 (std leftover, not binary cartesian)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object",
            fetch1_ok="Standard base64 is not base64url.",
            fetch2="https://json-schema.org/understanding-json-schema/reference/non_json_data#contentencoding",
            fetch2_ok="Exclusive std base64 400 leftover base64url.",
        ),
    ),
    (
        plant(
            slug="oas-anyof-types",
            domain="oas-anyof-vs-type-csv",
            success=True,
            name="anyoft",
            stack="OpenAPI 3.1 anyOf types + Go",
            field="anyOf",
            old="type csv leftover",
            new="anyOf type list",
            fail_err="400: leftover type csv after anyOf-only",
            plan="anyOf-only 400s leftover type csv. Dual-read csv for one release.",
            residual="validator still csv leftover; drop after validator 5",
            vs="r3829 json-schema-type-array (anyOf vs type csv leftover, not type array)",
            fetch1="https://json-schema.org/understanding-json-schema/reference/combining#anyOf",
            fetch1_ok="anyOf is not a comma-separated type leftover.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object",
            fetch2_ok="Exclusive anyOf 400 leftover type csv.",
        ),
        plant(
            slug="leftover-type-csv",
            domain="type-csv-vs-oas-anyof",
            success=False,
            name="typecsv",
            stack="OpenAPI leftover type csv + Java + TS",
            field="type",
            old="anyOf type list",
            new="type csv leftover only",
            fail_err="400: leftover anyOf after csv-only",
            plan="Csv-only 400s leftover anyOf. Freeze anyOf, spec csv leftover.",
            residual="handoff: keep anyOf or force type csv leftover",
            vs="r3829 comma-string-leftover (type csv leftover, not type array)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object",
            fetch1_ok="CSV types are not anyOf.",
            fetch2="https://json-schema.org/understanding-json-schema/reference/combining#anyOf",
            fetch2_ok="Exclusive type csv 400 leftover anyOf.",
        ),
    ),
    (
        plant(
            slug="oas-not-schema",
            domain="oas-not-schema-vs-allow-all",
            success=True,
            name="notsch",
            stack="OpenAPI 3.1 not schema + Go",
            field="not",
            old="allow all leftover",
            new="not schema",
            fail_err="400: leftover allow-all after not-only",
            plan="not-only 400s leftover allow-all. Dual-accept allow-all for one release.",
            residual="compat still allow leftover; drop after compat 4",
            vs="r3899 oas-additionalproperties-false (not vs allow-all leftover, not closed object)",
            fetch1="https://json-schema.org/understanding-json-schema/reference/combining#not",
            fetch1_ok="not inverts a subschema; leftover allow-all is not that.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object",
            fetch2_ok="Exclusive not 400 leftover allow-all.",
        ),
        plant(
            slug="leftover-allow-all",
            domain="allow-all-vs-oas-not-schema",
            success=False,
            name="allowall",
            stack="OpenAPI leftover allow-all + Java + TS",
            field="schema",
            old="not schema",
            new="allow all leftover only",
            fail_err="400: leftover not after allow-all-only",
            plan="Allow-all-only 400s leftover not. Freeze not, spec allow-all leftover.",
            residual="handoff: keep not or force allow-all leftover",
            vs="r3899 leftover-open-object (allow-all leftover, not open object)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object",
            fetch1_ok="Allow-all is not a not subschema.",
            fetch2="https://json-schema.org/understanding-json-schema/reference/combining#not",
            fetch2_ok="Exclusive allow-all 400 leftover not.",
        ),
    ),
    (
        plant(
            slug="oas-contains-schema",
            domain="oas-contains-vs-any-item",
            success=True,
            name="contains",
            stack="OpenAPI 3.1 contains + Go",
            field="contains",
            old="any item leftover",
            new="array contains",
            fail_err="400: leftover any-item after contains-only",
            plan="contains-only 400s leftover any-item. Dual-read any-item for one release.",
            residual="batch still any leftover; drop after batch 6",
            vs="r3883 oas-array-mincontains (contains vs any-item leftover, not minContains)",
            fetch1="https://json-schema.org/understanding-json-schema/reference/array#contains",
            fetch1_ok="contains requires a matching item, not any leftover item.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object",
            fetch2_ok="Exclusive contains 400 leftover any-item.",
        ),
        plant(
            slug="leftover-any-item",
            domain="any-item-vs-oas-contains",
            success=False,
            name="anyitem",
            stack="OpenAPI leftover any item + Java + TS",
            field="items",
            old="array contains",
            new="any item leftover only",
            fail_err="400: leftover contains after any-item-only",
            plan="Any-item-only 400s leftover contains. Freeze contains, spec any leftover.",
            residual="handoff: keep contains or force any-item leftover",
            vs="r3883 leftover-minitems-only (any-item leftover, not minItems)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object",
            fetch1_ok="Any-item arrays are not contains.",
            fetch2="https://json-schema.org/understanding-json-schema/reference/array#contains",
            fetch2_ok="Exclusive any-item 400 leftover contains.",
        ),
    ),
    (
        plant(
            slug="oas-patternproperties",
            domain="oas-patternproperties-vs-wildcard-keys",
            success=True,
            name="patprop",
            stack="OpenAPI 3.1 patternProperties + Go",
            field="patternProperties",
            old="wildcard keys leftover",
            new="patternProperties map",
            fail_err="400: leftover wildcard keys after patternProperties-only",
            plan="patternProperties-only 400s leftover wildcard keys. Dual-read wildcard for one release.",
            residual="map still wildcard leftover; drop after map 5",
            vs="r3899 oas-propertynames-format (patternProperties vs wildcard leftover, not propertyNames)",
            fetch1="https://json-schema.org/understanding-json-schema/reference/object#patternProperties",
            fetch1_ok="patternProperties keys are regexes, not leftover wildcards.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object",
            fetch2_ok="Exclusive patternProperties 400 leftover wildcard keys.",
        ),
        plant(
            slug="leftover-wildcard-keys",
            domain="wildcard-keys-vs-oas-patternproperties",
            success=False,
            name="wildk",
            stack="OpenAPI leftover wildcard keys + Java + TS",
            field="additionalProperties",
            old="patternProperties map",
            new="wildcard keys leftover only",
            fail_err="400: leftover patternProperties after wildcard-only",
            plan="Wildcard-only 400s leftover patternProperties. Freeze patternProperties, spec wildcard leftover.",
            residual="handoff: keep patternProperties or force wildcard leftover",
            vs="r3899 leftover-free-keys (wildcard leftover, not free keys)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object",
            fetch1_ok="Wildcard keys are not patternProperties.",
            fetch2="https://json-schema.org/understanding-json-schema/reference/object#patternProperties",
            fetch2_ok="Exclusive wildcard keys 400 leftover patternProperties.",
        ),
    ),
    (
        plant(
            slug="oas-media-charset-utf8",
            domain="oas-charset-utf8-vs-latin1",
            success=True,
            name="csutf8",
            stack="OpenAPI 3.1 charset=utf-8 + Go",
            field="charset",
            old="latin1 leftover",
            new="charset utf-8",
            fail_err="415: leftover latin1 after utf-8-only",
            plan="utf-8-only 415s leftover latin1. Dual-read latin1 for one release.",
            residual="batch still latin1 leftover; drop after batch 7",
            vs="r3867 leftover-prop-mediatype (charset utf-8 vs latin1 leftover, not property media)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#media-type-object",
            fetch1_ok="charset=utf-8 is not leftover latin1.",
            fetch2="https://datatracker.ietf.org/doc/html/rfc6838",
            fetch2_ok="Exclusive utf-8 415 leftover latin1.",
        ),
        plant(
            slug="leftover-charset-latin1",
            domain="latin1-vs-oas-charset-utf8",
            success=False,
            name="cslat1",
            stack="OpenAPI leftover charset latin1 + Java + TS",
            field="charset",
            old="charset utf-8",
            new="latin1 leftover only",
            fail_err="415: leftover utf-8 after latin1-only",
            plan="Latin1-only 415s leftover utf-8. Freeze utf-8, spec latin1 leftover.",
            residual="handoff: keep utf-8 or force latin1 leftover",
            vs="r3867 oas-encoding-ctype (latin1 leftover, not encoding.contentType)",
            fetch1="https://datatracker.ietf.org/doc/html/rfc6838",
            fetch1_ok="latin1 is not charset=utf-8.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object",
            fetch2_ok="Exclusive latin1 415 leftover utf-8.",
        ),
    ),
    (
        plant(
            slug="oas-format-json-pointer",
            domain="oas-json-pointer-vs-dotpath",
            success=True,
            name="jsonptr",
            stack="OpenAPI 3.1 format=json-pointer + Go",
            field="format",
            old="dotpath leftover",
            new="format json-pointer",
            fail_err="400: leftover dotpath after json-pointer-only",
            plan="json-pointer-only 400s leftover dotpath. Dual-read dotpath for one release.",
            residual="patch still dotpath leftover; drop after patch 5",
            vs="r3899 oas-content-schema-ref (json-pointer vs dotpath leftover, not schema $ref)",
            fetch1="https://json-schema.org/understanding-json-schema/reference/string#json-pointer",
            fetch1_ok="format=json-pointer is RFC 6901, not a leftover dotpath.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types",
            fetch2_ok="Exclusive json-pointer 400 leftover dotpath.",
        ),
        plant(
            slug="leftover-dotpath",
            domain="dotpath-vs-oas-json-pointer",
            success=False,
            name="dotp",
            stack="OpenAPI leftover dotpath + Java + TS",
            field="path",
            old="format json-pointer",
            new="dotpath leftover only",
            fail_err="400: leftover json-pointer after dotpath-only",
            plan="Dotpath-only 400s leftover json-pointer. Freeze pointer, spec dotpath leftover.",
            residual="handoff: keep json-pointer or force dotpath leftover",
            vs="r3899 leftover-inline-schema (dotpath leftover, not inline schema)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types",
            fetch1_ok="Dotpaths are not format=json-pointer.",
            fetch2="https://json-schema.org/understanding-json-schema/reference/string#json-pointer",
            fetch2_ok="Exclusive dotpath 400 leftover json-pointer.",
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
            if "uuid-vs-ulid" in slug or "binary-vs-base64" in slug:
                raise SystemExit(f"banned needle {slug}")


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
    print(json.dumps({"round": round_n, "idx": idx, "ids": [e1["id"], e2["id"]], "catalog": "r3915"}))


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
