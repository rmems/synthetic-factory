#!/usr/bin/env python3
"""Second unique OpenAPI-drift ACM catalog after r3867 mill.

BAN r3866 oas-lll4-proto-optional / protobuf-lll4-optional-oas,
r3850 accept-language-bcp47 / iso639-language, r3713 smile/cbor,
r3560 422-vs-400 / 207-multistatus, prior w131 cartesian,
r3561–r3851 leftover leftover leftover clones, and r3867 OAS plants.
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
            slug="oas-servers-url-template",
            domain="oas-server-template-vs-hardcoded-host",
            success=True,
            name="srvtmpl",
            stack="OpenAPI 3.1 servers.url template + Go",
            field="url",
            old="hardcoded host leftover",
            new="server url template",
            fail_err="400: leftover hardcoded host after server-template-only",
            plan="Server template-only 400s leftover hardcoded host. Dual-accept hardcoded for one release.",
            residual="edge still hardcoded leftover; drop after edge 5",
            vs="r3867 oas-srv-var-enum (url template vs hardcoded host, not variable enum)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#server-object",
            fetch1_ok="servers.url templates are not hardcoded hosts.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#server-variable-object",
            fetch2_ok="Exclusive server template 400 leftover hardcoded host.",
        ),
        plant(
            slug="leftover-hardcoded-host",
            domain="hardcoded-host-vs-oas-server-template",
            success=False,
            name="hrdhost",
            stack="OpenAPI leftover hardcoded host + Java + TS",
            field="host",
            old="server url template",
            new="hardcoded host leftover only",
            fail_err="400: leftover server template after hardcoded-only",
            plan="Hardcoded-only 400s leftover server template. Freeze template, spec hardcoded leftover.",
            residual="handoff: keep server template or force hardcoded leftover",
            vs="r3867 leftover-freeform-host (hardcoded host, not freeform enum leftover)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#server-variable-object",
            fetch1_ok="Hardcoded host is not a servers.url template.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#server-object",
            fetch2_ok="Exclusive hardcoded host 400 leftover server template.",
        ),
    ),
    (
        plant(
            slug="oas-tag-externaldocs",
            domain="oas-tag-docs-vs-untagged-ops",
            success=True,
            name="tagdocs",
            stack="OpenAPI 3.1 tag externalDocs + Go",
            field="externalDocs",
            old="untagged ops leftover",
            new="tag externalDocs",
            fail_err="400: leftover untagged ops after tag-docs-only",
            plan="Tag externalDocs-only 400s leftover untagged ops. Dual-accept untagged for one release.",
            residual="portal still untagged leftover; drop after portal 4",
            vs="r3867 oas31-schema-dialect (tag docs vs untagged, not jsonSchemaDialect)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#tag-object",
            fetch1_ok="Tag externalDocs is not an untagged operation list.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#operation-object",
            fetch2_ok="Exclusive tag docs 400 leftover untagged ops.",
        ),
        plant(
            slug="leftover-untagged-ops",
            domain="untagged-ops-vs-oas-tag-docs",
            success=False,
            name="untag",
            stack="OpenAPI leftover untagged ops + Java + TS",
            field="tags",
            old="tag externalDocs",
            new="untagged ops leftover only",
            fail_err="400: leftover tag docs after untagged-only",
            plan="Untagged-only 400s leftover tag docs. Freeze externalDocs, spec untagged leftover.",
            residual="handoff: keep tag docs or force untagged leftover",
            vs="r3867 leftover-schema-draft04 (untagged ops, not draft-04)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#operation-object",
            fetch1_ok="Untagged operations are not tag externalDocs.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#tag-object",
            fetch2_ok="Exclusive untagged 400 leftover tag docs.",
        ),
    ),
    (
        plant(
            slug="oas-op-callback-expr",
            domain="oas-callback-expr-vs-static-notify",
            success=True,
            name="cbexpr",
            stack="OpenAPI 3.1 callback runtime expression + Go",
            field="{$request.body#/callbackUrl}",
            old="static notify leftover",
            new="callback runtime expression",
            fail_err="400: leftover static notify after callback-expression-only",
            plan="Callback expression-only 400s leftover static notify. Dual-bind static for one release.",
            residual="bus still static leftover; drop after bus 6",
            vs="wrap callback-hmac-sha256 (runtime expression vs static notify, not HMAC)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#callback-object",
            fetch1_ok="Callback keys are runtime expressions, not static URLs.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#runtime-expressions",
            fetch2_ok="Exclusive callback expression 400 leftover static notify.",
        ),
        plant(
            slug="leftover-static-notify-url",
            domain="static-notify-vs-oas-callback-expr",
            success=False,
            name="statcb",
            stack="OpenAPI leftover static notify + Java + TS",
            field="notifyUrl",
            old="callback runtime expression",
            new="static notify leftover only",
            fail_err="400: leftover callback expression after static-only",
            plan="Static-only 400s leftover callback expression. Freeze expression, spec static leftover.",
            residual="handoff: keep callback expression or force static leftover",
            vs="wrap callback-hmac-sha256 (static notify leftover, not HMAC cartesian)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#runtime-expressions",
            fetch1_ok="Static notify URLs are not OAS callback expressions.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#callback-object",
            fetch2_ok="Exclusive static notify 400 leftover callback expression.",
        ),
    ),
    (
        plant(
            slug="oas-array-mincontains",
            domain="oas-mincontains-vs-minitems-only",
            success=True,
            name="minc",
            stack="OpenAPI 3.1 minContains + Go",
            field="minContains",
            old="minItems leftover only",
            new="array minContains",
            fail_err="400: leftover minItems-only after minContains-only",
            plan="minContains-only 400s leftover minItems. Dual-read minItems for one release.",
            residual="validator still minItems leftover; drop after validator 5",
            vs="wrap mincontains-role (minContains vs minItems leftover, not role)",
            fetch1="https://json-schema.org/understanding-json-schema/reference/array#mincontains",
            fetch1_ok="minContains counts contains matches, not array length.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object",
            fetch2_ok="Exclusive minContains 400 leftover minItems.",
        ),
        plant(
            slug="leftover-minitems-only",
            domain="minitems-only-vs-oas-mincontains",
            success=False,
            name="minit",
            stack="OpenAPI leftover minItems + Java + TS",
            field="minItems",
            old="array minContains",
            new="minItems leftover only",
            fail_err="400: leftover minContains after minItems-only",
            plan="minItems-only 400s leftover minContains. Freeze minContains, spec minItems leftover.",
            residual="handoff: keep minContains or force minItems leftover",
            vs="wrap mincontains-role (minItems leftover, not role cartesian)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object",
            fetch1_ok="minItems is not minContains.",
            fetch2="https://json-schema.org/understanding-json-schema/reference/array#mincontains",
            fetch2_ok="Exclusive minItems 400 leftover minContains.",
        ),
    ),
    (
        plant(
            slug="oas-header-content-json",
            domain="oas-header-content-vs-schema-string",
            success=True,
            name="hdrcj",
            stack="OpenAPI 3.1 header content json + Go",
            field="content",
            old="header schema string leftover",
            new="header content json",
            fail_err="400: leftover header schema-string after content-json-only",
            plan="Header content-json-only 400s leftover schema-string. Dual-read schema-string for one release.",
            residual="proxy still schema-string leftover; drop after proxy 6",
            vs="r3867 oas-param-content-map (header content, not parameter content)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#header-object",
            fetch1_ok="Header content is mutually exclusive with schema.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object",
            fetch2_ok="Exclusive header content json 400 leftover schema-string.",
        ),
        plant(
            slug="leftover-header-schema-string",
            domain="header-schema-string-vs-oas-content",
            success=False,
            name="hdrss",
            stack="OpenAPI leftover header schema string + Java + TS",
            field="schema",
            old="header content json",
            new="header schema string leftover only",
            fail_err="400: leftover header content after schema-string-only",
            plan="Schema-string-only 400s leftover header content. Freeze content, spec schema-string leftover.",
            residual="handoff: keep header content or force schema-string leftover",
            vs="r3867 leftover-param-schema-only (header schema-string, not param schema)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#media-type-object",
            fetch1_ok="Header schema:string is not header content json.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#header-object",
            fetch2_ok="Exclusive header schema-string 400 leftover content.",
        ),
    ),
    (
        plant(
            slug="oas-path-matrix-style",
            domain="oas-path-matrix-vs-path-simple",
            success=True,
            name="pmatrix",
            stack="OpenAPI 3.1 path style=matrix + Go",
            field="style",
            old="path simple leftover",
            new="path matrix style",
            fail_err="400: leftover path simple after matrix-only",
            plan="Path matrix-only 400s leftover simple. Dual-read simple for one release.",
            residual="router still simple leftover; drop after router 5",
            vs="r3867 oas-hdr-simple-explode (path matrix, not header simple explode)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#style-values",
            fetch1_ok="Path style=matrix is not style=simple.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object",
            fetch2_ok="Exclusive path matrix 400 leftover simple.",
        ),
        plant(
            slug="leftover-path-simple",
            domain="path-simple-vs-oas-matrix",
            success=False,
            name="psimpl",
            stack="OpenAPI leftover path simple + Java + TS",
            field="style",
            old="path matrix style",
            new="path simple leftover only",
            fail_err="400: leftover path matrix after simple-only",
            plan="Path-simple-only 400s leftover matrix. Freeze matrix, spec simple leftover.",
            residual="handoff: keep path matrix or force simple leftover",
            vs="r3867 leftover-hdr-form-style (path simple leftover, not header form)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object",
            fetch1_ok="Path simple is not matrix style.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#style-values",
            fetch2_ok="Exclusive path simple 400 leftover matrix.",
        ),
    ),
    (
        plant(
            slug="oas-query-pipe-delimited",
            domain="oas-pipe-delimited-vs-comma-query",
            success=True,
            name="qpipe",
            stack="OpenAPI 3.1 query style=pipeDelimited + Go",
            field="style",
            old="comma query leftover",
            new="pipeDelimited query",
            fail_err="400: leftover comma query after pipeDelimited-only",
            plan="pipeDelimited-only 400s leftover comma query. Dual-read comma for one release.",
            residual="gateway still comma leftover; drop after gateway 4",
            vs="wrap form-space-delimited (pipeDelimited vs comma leftover, not spaceDelimited)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#style-values",
            fetch1_ok="pipeDelimited is not comma-separated form.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object",
            fetch2_ok="Exclusive pipeDelimited 400 leftover comma query.",
        ),
        plant(
            slug="leftover-query-comma",
            domain="comma-query-vs-oas-pipe-delimited",
            success=False,
            name="qcomma",
            stack="OpenAPI leftover comma query + Java + TS",
            field="style",
            old="pipeDelimited query",
            new="comma query leftover only",
            fail_err="400: leftover pipeDelimited after comma-only",
            plan="Comma-only 400s leftover pipeDelimited. Freeze pipe, spec comma leftover.",
            residual="handoff: keep pipeDelimited or force comma leftover",
            vs="wrap form-space-delimited (comma leftover, not spaceDelimited cartesian)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object",
            fetch1_ok="Comma query is not pipeDelimited.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#style-values",
            fetch2_ok="Exclusive comma query 400 leftover pipeDelimited.",
        ),
    ),
    (
        plant(
            slug="oas-response-header-rate",
            domain="oas-rate-header-vs-body-ratelimit",
            success=True,
            name="rathdr",
            stack="OpenAPI 3.1 RateLimit header + Go",
            field="RateLimit",
            old="body ratelimit leftover",
            new="RateLimit response header",
            fail_err="400: leftover body ratelimit after RateLimit-header-only",
            plan="RateLimit-header-only 400s leftover body ratelimit. Dual-emit body for one release.",
            residual="sdk still body leftover; drop after sdk 6",
            vs="r3867 oas-sunset-http-date (RateLimit header, not Sunset date)",
            fetch1="https://www.ietf.org/archive/id/draft-ietf-httpapi-ratelimit-headers-07.html",
            fetch1_ok="RateLimit is a response header, not a JSON body field.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#response-object",
            fetch2_ok="Exclusive RateLimit header 400 leftover body ratelimit.",
        ),
        plant(
            slug="leftover-body-ratelimit",
            domain="body-ratelimit-vs-oas-rate-header",
            success=False,
            name="ratbody",
            stack="OpenAPI leftover body ratelimit + Java + TS",
            field="rateLimit",
            old="RateLimit response header",
            new="body ratelimit leftover only",
            fail_err="400: leftover RateLimit header after body-only",
            plan="Body-only 400s leftover RateLimit header. Freeze header, spec body leftover.",
            residual="handoff: keep RateLimit header or force body leftover",
            vs="r3867 leftover-deprecated-flag (body ratelimit leftover, not deprecated flag)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#response-object",
            fetch1_ok="Body ratelimit is not a RateLimit header.",
            fetch2="https://www.ietf.org/archive/id/draft-ietf-httpapi-ratelimit-headers-07.html",
            fetch2_ok="Exclusive body ratelimit 400 leftover RateLimit header.",
        ),
    ),
    (
        plant(
            slug="oas-security-and-or",
            domain="oas-security-andor-vs-single-scheme",
            success=True,
            name="secand",
            stack="OpenAPI 3.1 security AND/OR + Go",
            field="security",
            old="single scheme leftover",
            new="security and-or list",
            fail_err="401: leftover single scheme after and-or-only",
            plan="Security AND/OR-only 401s leftover single scheme. Dual-accept single for one release.",
            residual="gateway still single leftover; drop after gateway 7",
            vs="r3867 oas-oidc-scheme (AND/OR list vs single scheme, not OIDC)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#security-requirement-object",
            fetch1_ok="Security requirement arrays encode AND/OR, not a single scheme.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#operation-object",
            fetch2_ok="Exclusive AND/OR security 401 leftover single scheme.",
        ),
        plant(
            slug="leftover-single-scheme",
            domain="single-scheme-vs-oas-security-andor",
            success=False,
            name="sec1",
            stack="OpenAPI leftover single scheme + Java + TS",
            field="security",
            old="security and-or list",
            new="single scheme leftover only",
            fail_err="401: leftover and-or after single-scheme-only",
            plan="Single-scheme-only 401s leftover AND/OR. Freeze AND/OR, spec single leftover.",
            residual="handoff: keep AND/OR security or force single leftover",
            vs="r3867 leftover-oauth-implicit-flow (single scheme leftover, not implicit)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#operation-object",
            fetch1_ok="A single scheme is not an AND/OR security list.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#security-requirement-object",
            fetch2_ok="Exclusive single scheme 401 leftover AND/OR.",
        ),
    ),
    (
        plant(
            slug="oas-default-response",
            domain="oas-default-response-vs-200-only",
            success=True,
            name="defresp",
            stack="OpenAPI 3.1 default response + Go",
            field="default",
            old="200 only leftover",
            new="default response",
            fail_err="400: leftover 200-only after default-response-only",
            plan="Default-response-only 400s leftover 200-only. Dual-document 200 for one release.",
            residual="client still 200-only leftover; drop after client 5",
            vs="r3560 207-multistatus-batch (default response vs 200-only, not 207)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#responses-object",
            fetch1_ok="default covers undeclared status codes, not only 200.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#response-object",
            fetch2_ok="Exclusive default response 400 leftover 200-only.",
        ),
        plant(
            slug="leftover-200-only",
            domain="200-only-vs-oas-default-response",
            success=False,
            name="only200",
            stack="OpenAPI leftover 200-only + Java + TS",
            field="200",
            old="default response",
            new="200 only leftover only",
            fail_err="400: leftover default after 200-only",
            plan="200-only 400s leftover default response. Freeze default, spec 200 leftover.",
            residual="handoff: keep default response or force 200-only leftover",
            vs="r3560 422-vs-400-validation (200-only leftover, not 422/400)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#response-object",
            fetch1_ok="Documenting only 200 is not a default response.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#responses-object",
            fetch2_ok="Exclusive 200-only 400 leftover default response.",
        ),
    ),
    (
        plant(
            slug="oas-format-duration",
            domain="oas-format-duration-vs-seconds-int",
            success=True,
            name="fmtdur",
            stack="OpenAPI 3.1 format=duration + Go",
            field="format",
            old="seconds int leftover",
            new="format duration",
            fail_err="400: leftover seconds-int after duration-only",
            plan="format=duration-only 400s leftover seconds-int. Dual-read seconds for one release.",
            residual="worker still seconds leftover; drop after worker 6",
            vs="r3867 oas31-exclmin-numeric (duration format, not exclusiveMinimum)",
            fetch1="https://json-schema.org/understanding-json-schema/reference/string#duration",
            fetch1_ok="format=duration is ISO 8601, not an integer second count.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types",
            fetch2_ok="Exclusive format=duration 400 leftover seconds-int.",
        ),
        plant(
            slug="leftover-seconds-int",
            domain="seconds-int-vs-oas-format-duration",
            success=False,
            name="secint",
            stack="OpenAPI leftover seconds int + Java + TS",
            field="seconds",
            old="format duration",
            new="seconds int leftover only",
            fail_err="400: leftover duration after seconds-int-only",
            plan="Seconds-int-only 400s leftover duration. Freeze duration, spec seconds leftover.",
            residual="handoff: keep format=duration or force seconds leftover",
            vs="r3867 oas30-exclmin-flag (seconds leftover, not exclusiveMinimum bool)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types",
            fetch1_ok="Integer seconds are not format=duration.",
            fetch2="https://json-schema.org/understanding-json-schema/reference/string#duration",
            fetch2_ok="Exclusive seconds-int 400 leftover duration.",
        ),
    ),
    (
        plant(
            slug="oas-info-license-identifier",
            domain="oas-license-identifier-vs-url-only",
            success=True,
            name="licid",
            stack="OpenAPI 3.1 license.identifier + Go",
            field="identifier",
            old="license url leftover",
            new="license identifier",
            fail_err="400: leftover license url after identifier-only",
            plan="license.identifier-only 400s leftover url. Dual-emit url for one release.",
            residual="portal still url leftover; drop after portal 5",
            vs="r3867 oas-tag-externaldocs contrast (license identifier, not tag docs)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#license-object",
            fetch1_ok="license.identifier is SPDX, mutually exclusive with url in some tools.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#info-object",
            fetch2_ok="Exclusive license identifier 400 leftover url.",
        ),
        plant(
            slug="leftover-license-url-only",
            domain="license-url-vs-oas-identifier",
            success=False,
            name="licurl",
            stack="OpenAPI leftover license url + Java + TS",
            field="url",
            old="license identifier",
            new="license url leftover only",
            fail_err="400: leftover identifier after url-only",
            plan="Url-only 400s leftover license identifier. Freeze identifier, spec url leftover.",
            residual="handoff: keep license identifier or force url leftover",
            vs="r3867 leftover-untagged-ops contrast (license url leftover, not untagged)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#info-object",
            fetch1_ok="license.url is not an SPDX identifier.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#license-object",
            fetch2_ok="Exclusive license url 400 leftover identifier.",
        ),
    ),
    (
        plant(
            slug="oas-components-pathitems",
            domain="oas-components-pathitems-vs-copypaste",
            success=True,
            name="cpathi",
            stack="OpenAPI 3.1 components.pathItems + Go",
            field="pathItems",
            old="copypaste paths leftover",
            new="components pathItems",
            fail_err="400: leftover copypaste paths after pathItems-only",
            plan="components.pathItems-only 400s leftover copypaste. Dual-read copypaste for one release.",
            residual="gateway still copypaste leftover; drop after gateway 6",
            vs="r3867 oas-pathitem-dollarref (components.pathItems, not inline $ref)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#components-object",
            fetch1_ok="components.pathItems reuse Path Item objects, not copied paths.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#path-item-object",
            fetch2_ok="Exclusive components.pathItems 400 leftover copypaste.",
        ),
        plant(
            slug="leftover-copypaste-paths",
            domain="copypaste-paths-vs-oas-pathitems",
            success=False,
            name="cppath",
            stack="OpenAPI leftover copypaste paths + Java + TS",
            field="paths",
            old="components pathItems",
            new="copypaste paths leftover only",
            fail_err="400: leftover pathItems after copypaste-only",
            plan="Copypaste-only 400s leftover pathItems. Freeze pathItems, spec copypaste leftover.",
            residual="handoff: keep components.pathItems or force copypaste leftover",
            vs="r3867 leftover-dup-inline-path (copypaste leftover, not Path Item $ref)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#path-item-object",
            fetch1_ok="Copied path maps are not components.pathItems.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#components-object",
            fetch2_ok="Exclusive copypaste 400 leftover pathItems.",
        ),
    ),
    (
        plant(
            slug="oas-discriminator-propname",
            domain="oas-disc-propname-vs-type-field",
            success=True,
            name="dprop",
            stack="OpenAPI 3.1 discriminator.propertyName + Go",
            field="propertyName",
            old="type field leftover",
            new="discriminator propertyName",
            fail_err="400: leftover type field after propertyName-only",
            plan="propertyName-only 400s leftover type field. Dual-read type for one release.",
            residual="sdk still type leftover; drop after sdk 5",
            vs="r01 discriminator.mapping miss (propertyName vs leftover type field, not mapping)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#discriminator-object",
            fetch1_ok="discriminator.propertyName is not a free type field.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object",
            fetch2_ok="Exclusive propertyName 400 leftover type field.",
        ),
        plant(
            slug="leftover-type-field",
            domain="type-field-vs-oas-disc-propname",
            success=False,
            name="tfield",
            stack="OpenAPI leftover type field + Java + TS",
            field="type",
            old="discriminator propertyName",
            new="type field leftover only",
            fail_err="400: leftover propertyName after type-field-only",
            plan="Type-field-only 400s leftover propertyName. Freeze propertyName, spec type leftover.",
            residual="handoff: keep propertyName or force type leftover",
            vs="r01 discriminator.mapping miss (type leftover, not mapping cartesian)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object",
            fetch1_ok="A free type field is not discriminator.propertyName.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#discriminator-object",
            fetch2_ok="Exclusive type field 400 leftover propertyName.",
        ),
    ),
    (
        plant(
            slug="oas-maxitems-array",
            domain="oas-maxitems-vs-unbounded-array",
            success=True,
            name="maxit",
            stack="OpenAPI 3.1 maxItems + Go",
            field="maxItems",
            old="unbounded array leftover",
            new="array maxItems",
            fail_err="400: leftover unbounded array after maxItems-only",
            plan="maxItems-only 400s leftover unbounded array. Dual-accept unbounded for one release.",
            residual="batch still unbounded leftover; drop after batch 4",
            vs="r3842 minlength-code (maxItems vs unbounded, not minLength string)",
            fetch1="https://json-schema.org/understanding-json-schema/reference/array#maxitems",
            fetch1_ok="maxItems caps array length; unbounded arrays are leftover.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object",
            fetch2_ok="Exclusive maxItems 400 leftover unbounded.",
        ),
        plant(
            slug="leftover-unbounded-array",
            domain="unbounded-array-vs-oas-maxitems",
            success=False,
            name="unbarr",
            stack="OpenAPI leftover unbounded array + Java + TS",
            field="items",
            old="array maxItems",
            new="unbounded array leftover only",
            fail_err="400: leftover maxItems after unbounded-only",
            plan="Unbounded-only 400s leftover maxItems. Freeze maxItems, spec unbounded leftover.",
            residual="handoff: keep maxItems or force unbounded leftover",
            vs="r3842 unconstrained-string (unbounded leftover, not minLength)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object",
            fetch1_ok="Unbounded arrays are not maxItems.",
            fetch2="https://json-schema.org/understanding-json-schema/reference/array#maxitems",
            fetch2_ok="Exclusive unbounded 400 leftover maxItems.",
        ),
    ),
    (
        plant(
            slug="oas-format-email-idn",
            domain="oas-idn-email-vs-ascii-email",
            success=True,
            name="idnem",
            stack="OpenAPI 3.1 format=idn-email + Go",
            field="format",
            old="ascii email leftover",
            new="idn-email format",
            fail_err="400: leftover ascii email after idn-email-only",
            plan="idn-email-only 400s leftover ascii email. Dual-accept ascii for one release.",
            residual="crm still ascii leftover; drop after crm 7",
            vs="r3847 format-hostname-ascii (idn-email vs ascii email, not hostname)",
            fetch1="https://json-schema.org/understanding-json-schema/reference/string#idn-email",
            fetch1_ok="format=idn-email is not ascii format=email.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types",
            fetch2_ok="Exclusive idn-email 400 leftover ascii email.",
        ),
        plant(
            slug="leftover-ascii-email",
            domain="ascii-email-vs-oas-idn-email",
            success=False,
            name="ascem",
            stack="OpenAPI leftover ascii email + Java + TS",
            field="format",
            old="idn-email format",
            new="ascii email leftover only",
            fail_err="400: leftover idn-email after ascii-only",
            plan="Ascii-only 400s leftover idn-email. Freeze idn-email, spec ascii leftover.",
            residual="handoff: keep idn-email or force ascii leftover",
            vs="r3847 idn-hostname-leftover (ascii email leftover, not hostname)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types",
            fetch1_ok="format=email ascii is not idn-email.",
            fetch2="https://json-schema.org/understanding-json-schema/reference/string#idn-email",
            fetch2_ok="Exclusive ascii email 400 leftover idn-email.",
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
    print(json.dumps({"round": round_n, "idx": idx, "ids": [e1["id"], e2["id"]], "catalog": "r3883"}))


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
