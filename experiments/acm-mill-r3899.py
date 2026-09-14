#!/usr/bin/env python3
"""Third unique OpenAPI-drift ACM catalog after r3883 mill.

BAN r3866 proto-optional, r3850 accept-language/iso639, r3713 smile/cbor,
r3560 422/207, w131 cartesian, r3561–r3851 leftover leftover leftover,
and r3867/r3883 OAS plants.
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
            slug="oas-format-iri",
            domain="oas-format-iri-vs-ascii-uri",
            success=True,
            name="fmtiri",
            stack="OpenAPI 3.1 format=iri + Go",
            field="format",
            old="ascii uri leftover",
            new="format iri",
            fail_err="400: leftover ascii uri after iri-only",
            plan="format=iri-only 400s leftover ascii uri. Dual-accept ascii uri for one release.",
            residual="cdn still ascii leftover; drop after cdn 5",
            vs="r3883 oas-format-email-idn (iri vs ascii uri, not idn-email)",
            fetch1="https://json-schema.org/understanding-json-schema/reference/string#resource-identifiers",
            fetch1_ok="format=iri is not format=uri ASCII.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types",
            fetch2_ok="Exclusive format=iri 400 leftover ascii uri.",
        ),
        plant(
            slug="leftover-ascii-uri",
            domain="ascii-uri-vs-oas-format-iri",
            success=False,
            name="ascuri",
            stack="OpenAPI leftover ascii uri + Java + TS",
            field="format",
            old="format iri",
            new="ascii uri leftover only",
            fail_err="400: leftover iri after ascii-uri-only",
            plan="Ascii-uri-only 400s leftover iri. Freeze iri, spec ascii leftover.",
            residual="handoff: keep format=iri or force ascii uri leftover",
            vs="r3883 leftover-ascii-email (ascii uri leftover, not ascii email)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types",
            fetch1_ok="format=uri ASCII is not format=iri.",
            fetch2="https://json-schema.org/understanding-json-schema/reference/string#resource-identifiers",
            fetch2_ok="Exclusive ascii uri 400 leftover iri.",
        ),
    ),
    (
        plant(
            slug="oas-mutualtls-scheme",
            domain="oas-mutualtls-vs-client-header",
            success=True,
            name="mtls",
            stack="OpenAPI 3.1 mutualTLS + Go",
            field="mutualTLS",
            old="client cert header leftover",
            new="mutualTLS security scheme",
            fail_err="401: leftover client-cert header after mutualTLS-only",
            plan="mutualTLS-only 401s leftover client-cert header. Dual-accept header for one release.",
            residual="edge still header leftover; drop after edge 6",
            vs="r3867 oas-oidc-scheme (mutualTLS vs client header, not OIDC)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object",
            fetch1_ok="mutualTLS is a security scheme, not a client cert header.",
            fetch2="https://datatracker.ietf.org/doc/html/rfc8705",
            fetch2_ok="Exclusive mutualTLS 401 leftover client-cert header.",
        ),
        plant(
            slug="leftover-client-cert-header",
            domain="client-header-vs-oas-mutualtls",
            success=False,
            name="cchdr",
            stack="OpenAPI leftover client cert header + Java + TS",
            field="X-Client-Cert",
            old="mutualTLS security scheme",
            new="client cert header leftover only",
            fail_err="401: leftover mutualTLS after header-only",
            plan="Header-only 401s leftover mutualTLS. Freeze mutualTLS, spec header leftover.",
            residual="handoff: keep mutualTLS or force client-cert header leftover",
            vs="r3867 leftover-oauth-implicit-flow (client-cert header leftover, not implicit)",
            fetch1="https://datatracker.ietf.org/doc/html/rfc8705",
            fetch1_ok="A client cert header is not mutualTLS.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object",
            fetch2_ok="Exclusive client-cert header 401 leftover mutualTLS.",
        ),
    ),
    (
        plant(
            slug="oas-query-allowemptyvalue",
            domain="oas-allowemptyvalue-vs-omit-empty",
            success=True,
            name="qempty",
            stack="OpenAPI 3.1 allowEmptyValue + Go",
            field="allowEmptyValue",
            old="omit empty leftover",
            new="query allowEmptyValue",
            fail_err="400: leftover omit-empty after allowEmptyValue-only",
            plan="allowEmptyValue-only 400s leftover omit-empty. Dual-omit empty for one release.",
            residual="gateway still omit leftover; drop after gateway 4",
            vs="r3867 oas-query-allowreserved (allowEmptyValue vs omit-empty, not allowReserved)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object",
            fetch1_ok="allowEmptyValue keeps empty query params, not omits them.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#style-values",
            fetch2_ok="Exclusive allowEmptyValue 400 leftover omit-empty.",
        ),
        plant(
            slug="leftover-omit-empty-query",
            domain="omit-empty-vs-oas-allowemptyvalue",
            success=False,
            name="omitq",
            stack="OpenAPI leftover omit empty query + Java + TS",
            field="omitEmpty",
            old="query allowEmptyValue",
            new="omit empty leftover only",
            fail_err="400: leftover allowEmptyValue after omit-only",
            plan="Omit-only 400s leftover allowEmptyValue. Freeze allowEmptyValue, spec omit leftover.",
            residual="handoff: keep allowEmptyValue or force omit leftover",
            vs="r3867 leftover-query-pctencode (omit-empty leftover, not percent-encode)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#style-values",
            fetch1_ok="Omitting empty params is not allowEmptyValue.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object",
            fetch2_ok="Exclusive omit-empty 400 leftover allowEmptyValue.",
        ),
    ),
    (
        plant(
            slug="oas-response-link-params",
            domain="oas-link-params-vs-hardcoded-next",
            success=True,
            name="lnkprm",
            stack="OpenAPI 3.1 link parameters + Go",
            field="parameters",
            old="hardcoded next leftover",
            new="link parameter expressions",
            fail_err="400: leftover hardcoded next after link-params-only",
            plan="Link-params-only 400s leftover hardcoded next. Dual-emit hardcoded for one release.",
            residual="sdk still hardcoded leftover; drop after sdk 6",
            vs="r3867 oas-links-opref (link parameters vs hardcoded next, not operationRef)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#link-object",
            fetch1_ok="Link parameters are runtime expressions, not hardcoded next URLs.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#runtime-expressions",
            fetch2_ok="Exclusive link params 400 leftover hardcoded next.",
        ),
        plant(
            slug="leftover-hardcoded-next",
            domain="hardcoded-next-vs-oas-link-params",
            success=False,
            name="hardnxt",
            stack="OpenAPI leftover hardcoded next + Java + TS",
            field="next",
            old="link parameter expressions",
            new="hardcoded next leftover only",
            fail_err="400: leftover link params after hardcoded-next-only",
            plan="Hardcoded-next-only 400s leftover link params. Freeze expressions, spec hardcoded leftover.",
            residual="handoff: keep link params or force hardcoded leftover",
            vs="r3867 leftover-links-opid (hardcoded next leftover, not operationId)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#runtime-expressions",
            fetch1_ok="A hardcoded next URL is not a link parameter expression.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#link-object",
            fetch2_ok="Exclusive hardcoded next 400 leftover link params.",
        ),
    ),
    (
        plant(
            slug="oas-xml-namespace",
            domain="oas-xml-ns-vs-unqualified-xml",
            success=True,
            name="xmlns",
            stack="OpenAPI 3.1 xml.namespace + Go",
            field="namespace",
            old="unqualified xml leftover",
            new="xml namespace",
            fail_err="415: leftover unqualified xml after namespace-only",
            plan="xml.namespace-only 415s leftover unqualified xml. Dual-read unqualified for one release.",
            residual="batch still unqualified leftover; drop after batch 5",
            vs="wrap xml-wrapped-array (xml.namespace vs unqualified, not wrapped array)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#xml-object",
            fetch1_ok="xml.namespace is not an unqualified element name.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object",
            fetch2_ok="Exclusive xml.namespace 415 leftover unqualified.",
        ),
        plant(
            slug="leftover-unqualified-xml",
            domain="unqualified-xml-vs-oas-xml-ns",
            success=False,
            name="xmluq",
            stack="OpenAPI leftover unqualified xml + Java + TS",
            field="name",
            old="xml namespace",
            new="unqualified xml leftover only",
            fail_err="415: leftover xml.namespace after unqualified-only",
            plan="Unqualified-only 415s leftover xml.namespace. Freeze namespace, spec unqualified leftover.",
            residual="handoff: keep xml.namespace or force unqualified leftover",
            vs="wrap xml-wrapped-array (unqualified leftover, not wrapped cartesian)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object",
            fetch1_ok="Unqualified XML names are not xml.namespace.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#xml-object",
            fetch2_ok="Exclusive unqualified xml 415 leftover namespace.",
        ),
    ),
    (
        plant(
            slug="oas-format-int64",
            domain="oas-int64-vs-json-number",
            success=True,
            name="fmt64",
            stack="OpenAPI 3.1 format=int64 + Go",
            field="format",
            old="json number leftover",
            new="format int64",
            fail_err="400: leftover json number after int64-only",
            plan="format=int64-only 400s leftover json number. Dual-read number for one release.",
            residual="js client still number leftover; drop after js 7",
            vs="wrap int32-sku-qty (int64 vs json number leftover, not int32 sku)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types",
            fetch1_ok="format=int64 is not an unconstrained JSON number.",
            fetch2="https://datatracker.ietf.org/doc/html/rfc8259",
            fetch2_ok="Exclusive int64 400 leftover json number.",
        ),
        plant(
            slug="leftover-json-number",
            domain="json-number-vs-oas-int64",
            success=False,
            name="jsnum",
            stack="OpenAPI leftover json number + Java + TS",
            field="type",
            old="format int64",
            new="json number leftover only",
            fail_err="400: leftover int64 after json-number-only",
            plan="Json-number-only 400s leftover int64. Freeze int64, spec number leftover.",
            residual="handoff: keep format=int64 or force json number leftover",
            vs="wrap int32-sku-qty (json number leftover, not int32 cartesian)",
            fetch1="https://datatracker.ietf.org/doc/html/rfc8259",
            fetch1_ok="JSON number is not format=int64.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types",
            fetch2_ok="Exclusive json number 400 leftover int64.",
        ),
    ),
    (
        plant(
            slug="oas-additionalproperties-false",
            domain="oas-closed-object-vs-open-object",
            success=True,
            name="addpf",
            stack="OpenAPI 3.1 additionalProperties false + Go",
            field="additionalProperties",
            old="open object leftover",
            new="additionalProperties false",
            fail_err="400: leftover open object after closed-object-only",
            plan="Closed-object-only 400s leftover open object. Dual-accept extras for one release.",
            residual="partner still open leftover; drop after partner 5",
            vs="r3715 json-schema-unevaluatedproperties-vs-additionalproperties (false vs open leftover, not unevaluated)",
            fetch1="https://json-schema.org/understanding-json-schema/reference/object#additionalproperties",
            fetch1_ok="additionalProperties:false closes the object.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object",
            fetch2_ok="Exclusive closed object 400 leftover open object.",
        ),
        plant(
            slug="leftover-open-object",
            domain="open-object-vs-oas-closed-object",
            success=False,
            name="openobj",
            stack="OpenAPI leftover open object + Java + TS",
            field="additionalProperties",
            old="additionalProperties false",
            new="open object leftover only",
            fail_err="400: leftover closed object after open-only",
            plan="Open-only 400s leftover closed object. Freeze false, spec open leftover.",
            residual="handoff: keep closed object or force open leftover",
            vs="r3715 json-schema-unevaluatedproperties-vs-additionalproperties (open leftover, not unevaluated)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object",
            fetch1_ok="Open objects are not additionalProperties:false.",
            fetch2="https://json-schema.org/understanding-json-schema/reference/object#additionalproperties",
            fetch2_ok="Exclusive open object 400 leftover closed object.",
        ),
    ),
    (
        plant(
            slug="oas-pattern-anchor",
            domain="oas-anchored-pattern-vs-unanchored",
            success=True,
            name="patanc",
            stack="OpenAPI 3.1 anchored pattern + Go",
            field="pattern",
            old="unanchored regex leftover",
            new="anchored pattern",
            fail_err="400: leftover unanchored regex after anchored-only",
            plan="Anchored-pattern-only 400s leftover unanchored. Dual-read unanchored for one release.",
            residual="validator still unanchored leftover; drop after validator 4",
            vs="wrap e164-phone-pattern (anchored pattern vs unanchored leftover, not E.164)",
            fetch1="https://json-schema.org/understanding-json-schema/reference/regular_expressions",
            fetch1_ok="Anchored patterns are not substring-unanchored regexes.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object",
            fetch2_ok="Exclusive anchored pattern 400 leftover unanchored.",
        ),
        plant(
            slug="leftover-unanchored-regex",
            domain="unanchored-regex-vs-oas-anchored-pattern",
            success=False,
            name="unanc",
            stack="OpenAPI leftover unanchored regex + Java + TS",
            field="pattern",
            old="anchored pattern",
            new="unanchored regex leftover only",
            fail_err="400: leftover anchored after unanchored-only",
            plan="Unanchored-only 400s leftover anchored pattern. Freeze anchored, spec unanchored leftover.",
            residual="handoff: keep anchored pattern or force unanchored leftover",
            vs="wrap e164-phone-pattern (unanchored leftover, not E.164 cartesian)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object",
            fetch1_ok="Unanchored regex is not an anchored pattern.",
            fetch2="https://json-schema.org/understanding-json-schema/reference/regular_expressions",
            fetch2_ok="Exclusive unanchored 400 leftover anchored pattern.",
        ),
    ),
    (
        plant(
            slug="oas-encoding-explode-form",
            domain="oas-encoding-explode-vs-unexplode",
            success=True,
            name="encxpl",
            stack="OpenAPI 3.1 encoding.explode + Go",
            field="explode",
            old="encoding unexplode leftover",
            new="encoding explode form",
            fail_err="400: leftover unexplode after encoding-explode-only",
            plan="encoding.explode-only 400s leftover unexplode. Dual-read unexplode for one release.",
            residual="multipart still unexplode leftover; drop after multipart 6",
            vs="r3867 oas-encoding-ctype (encoding.explode vs unexplode, not contentType)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#encoding-object",
            fetch1_ok="encoding.explode is not encoding.explode=false leftover.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#style-values",
            fetch2_ok="Exclusive encoding.explode 400 leftover unexplode.",
        ),
        plant(
            slug="leftover-encoding-unexplode",
            domain="encoding-unexplode-vs-oas-explode",
            success=False,
            name="encunx",
            stack="OpenAPI leftover encoding unexplode + Java + TS",
            field="explode",
            old="encoding explode form",
            new="encoding unexplode leftover only",
            fail_err="400: leftover explode after unexplode-only",
            plan="Unexplode-only 400s leftover encoding.explode. Freeze explode, spec unexplode leftover.",
            residual="handoff: keep encoding.explode or force unexplode leftover",
            vs="r3867 leftover-prop-mediatype (unexplode leftover, not property media)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#style-values",
            fetch1_ok="Unexploded encoding is not encoding.explode true.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#encoding-object",
            fetch2_ok="Exclusive unexplode 400 leftover encoding.explode.",
        ),
    ),
    (
        plant(
            slug="oas-server-var-default",
            domain="oas-server-default-vs-missing-default",
            success=True,
            name="srvdef",
            stack="OpenAPI 3.1 server variable default + Go",
            field="default",
            old="missing default leftover",
            new="server variable default",
            fail_err="400: leftover missing default after default-only",
            plan="Server-variable-default-only 400s leftover missing default. Dual-require explicit for one release.",
            residual="mesh still missing leftover; drop after mesh 5",
            vs="r3867 oas-srv-var-enum (variable default vs missing default, not enum)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#server-variable-object",
            fetch1_ok="Server variables require a default, not a missing default.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#server-object",
            fetch2_ok="Exclusive server default 400 leftover missing default.",
        ),
        plant(
            slug="leftover-missing-srv-default",
            domain="missing-default-vs-oas-server-default",
            success=False,
            name="srvmiss",
            stack="OpenAPI leftover missing server default + Java + TS",
            field="variables",
            old="server variable default",
            new="missing default leftover only",
            fail_err="400: leftover default after missing-only",
            plan="Missing-default-only 400s leftover server default. Freeze default, spec missing leftover.",
            residual="handoff: keep server default or force missing leftover",
            vs="r3867 leftover-freeform-host (missing default leftover, not freeform host)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#server-object",
            fetch1_ok="Missing defaults are not server variable defaults.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#server-variable-object",
            fetch2_ok="Exclusive missing default 400 leftover server default.",
        ),
    ),
    (
        plant(
            slug="oas-operationid-unique",
            domain="oas-unique-opid-vs-duplicate-opid",
            success=True,
            name="opiduniq",
            stack="OpenAPI 3.1 unique operationId + Go",
            field="operationId",
            old="duplicate opid leftover",
            new="unique operationId",
            fail_err="400: leftover duplicate operationId after unique-only",
            plan="Unique-operationId-only 400s leftover duplicates. Dual-accept duplicates for one release.",
            residual="codegen still duplicate leftover; drop after codegen 6",
            vs="r3867 leftover-links-opid (unique operationId vs duplicates, not link opId)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#operation-object",
            fetch1_ok="operationId must be unique among all operations.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#fixed-fields-8",
            fetch2_ok="Exclusive unique operationId 400 leftover duplicates.",
        ),
        plant(
            slug="leftover-duplicate-opid",
            domain="duplicate-opid-vs-oas-unique-opid",
            success=False,
            name="opiddup",
            stack="OpenAPI leftover duplicate operationId + Java + TS",
            field="operationId",
            old="unique operationId",
            new="duplicate opid leftover only",
            fail_err="400: leftover unique operationId after duplicate-only",
            plan="Duplicate-only 400s leftover unique operationId. Freeze unique, spec duplicate leftover.",
            residual="handoff: keep unique operationId or force duplicate leftover",
            vs="r3867 oas-links-opref (duplicate leftover, not operationRef)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#fixed-fields-8",
            fetch1_ok="Duplicate operationIds are not unique.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#operation-object",
            fetch2_ok="Exclusive duplicate operationId 400 leftover unique.",
        ),
    ),
    (
        plant(
            slug="oas-header-required-true",
            domain="oas-required-header-vs-optional-header",
            success=True,
            name="hdrreq",
            stack="OpenAPI 3.1 required header + Go",
            field="required",
            old="optional header leftover",
            new="required header",
            fail_err="400: leftover optional header after required-only",
            plan="Required-header-only 400s leftover optional. Dual-accept missing for one release.",
            residual="proxy still optional leftover; drop after proxy 5",
            vs="r3867 oas-hdr-simple-explode (required header vs optional leftover, not explode)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#header-object",
            fetch1_ok="required:true on headers is not optional leftover.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object",
            fetch2_ok="Exclusive required header 400 leftover optional.",
        ),
        plant(
            slug="leftover-optional-header",
            domain="optional-header-vs-oas-required-header",
            success=False,
            name="hdropt",
            stack="OpenAPI leftover optional header + Java + TS",
            field="required",
            old="required header",
            new="optional header leftover only",
            fail_err="400: leftover required header after optional-only",
            plan="Optional-only 400s leftover required header. Freeze required, spec optional leftover.",
            residual="handoff: keep required header or force optional leftover",
            vs="r3867 leftover-hdr-form-style (optional header leftover, not form style)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object",
            fetch1_ok="Optional headers are not required:true.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#header-object",
            fetch2_ok="Exclusive optional header 400 leftover required.",
        ),
    ),
    (
        plant(
            slug="oas-encoding-headers-map",
            domain="oas-encoding-headers-vs-part-headers",
            success=True,
            name="enchdr",
            stack="OpenAPI 3.1 encoding.headers + Go",
            field="headers",
            old="part headers leftover",
            new="encoding headers map",
            fail_err="400: leftover part headers after encoding-headers-only",
            plan="encoding.headers-only 400s leftover part headers. Dual-read part headers for one release.",
            residual="multipart still part leftover; drop after multipart 7",
            vs="r3883 oas-header-content-json (encoding.headers vs part headers, not header content)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#encoding-object",
            fetch1_ok="encoding.headers describes per-property headers, not raw MIME part headers.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#header-object",
            fetch2_ok="Exclusive encoding.headers 400 leftover part headers.",
        ),
        plant(
            slug="leftover-part-headers",
            domain="part-headers-vs-oas-encoding-headers",
            success=False,
            name="parth",
            stack="OpenAPI leftover MIME part headers + Java + TS",
            field="Content-Disposition",
            old="encoding headers map",
            new="part headers leftover only",
            fail_err="400: leftover encoding.headers after part-only",
            plan="Part-headers-only 400s leftover encoding.headers. Freeze encoding.headers, spec part leftover.",
            residual="handoff: keep encoding.headers or force part leftover",
            vs="r3883 leftover-header-schema-string (part headers leftover, not header schema-string)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#header-object",
            fetch1_ok="Raw MIME part headers are not encoding.headers.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#encoding-object",
            fetch2_ok="Exclusive part headers 400 leftover encoding.headers.",
        ),
    ),
    (
        plant(
            slug="oas-webhook-post-only",
            domain="oas-webhook-post-vs-webhook-get",
            success=True,
            name="whkpost",
            stack="OpenAPI 3.1 webhook POST + Go",
            field="post",
            old="webhook GET leftover",
            new="webhook POST only",
            fail_err="405: leftover webhook GET after POST-only",
            plan="Webhook-POST-only 405s leftover GET. Dual-accept GET for one release.",
            residual="edge still GET leftover; drop after edge 4",
            vs="r3867 oas31-webhooks-map (webhook POST vs GET leftover, not callbacks map)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#oasWebhooks",
            fetch1_ok="Webhook Path Items commonly POST; leftover GET is not the contract.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#path-item-object",
            fetch2_ok="Exclusive webhook POST 405 leftover GET.",
        ),
        plant(
            slug="leftover-webhook-get",
            domain="webhook-get-vs-oas-webhook-post",
            success=False,
            name="whkget",
            stack="OpenAPI leftover webhook GET + Java + TS",
            field="get",
            old="webhook POST only",
            new="webhook GET leftover only",
            fail_err="405: leftover webhook POST after GET-only",
            plan="Webhook-GET-only 405s leftover POST. Freeze POST, spec GET leftover.",
            residual="handoff: keep webhook POST or force GET leftover",
            vs="r3867 oas30-callbacks-map (webhook GET leftover, not callbacks map)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#path-item-object",
            fetch1_ok="Webhook GET is not the POST-only contract.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#oasWebhooks",
            fetch2_ok="Exclusive webhook GET 405 leftover POST.",
        ),
    ),
    (
        plant(
            slug="oas-content-schema-ref",
            domain="oas-content-schema-ref-vs-inline-schema",
            success=True,
            name="csref",
            stack="OpenAPI 3.1 content schema $ref + Go",
            field="$ref",
            old="inline schema leftover",
            new="content schema ref",
            fail_err="400: leftover inline schema after content-ref-only",
            plan="Content-$ref-only 400s leftover inline schema. Dual-read inline for one release.",
            residual="sdk still inline leftover; drop after sdk 5",
            vs="r3867 oas-pathitem-dollarref (content schema $ref vs inline, not Path Item $ref)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#media-type-object",
            fetch1_ok="Media type schema $ref is not an inline schema copy.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object",
            fetch2_ok="Exclusive content $ref 400 leftover inline schema.",
        ),
        plant(
            slug="leftover-inline-schema",
            domain="inline-schema-vs-oas-content-ref",
            success=False,
            name="inschema",
            stack="OpenAPI leftover inline schema + Java + TS",
            field="schema",
            old="content schema ref",
            new="inline schema leftover only",
            fail_err="400: leftover content $ref after inline-only",
            plan="Inline-only 400s leftover content $ref. Freeze $ref, spec inline leftover.",
            residual="handoff: keep content $ref or force inline leftover",
            vs="r3867 leftover-dup-inline-path (inline schema leftover, not inline path)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object",
            fetch1_ok="Inline schemas are not media type $ref.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object",
            fetch2_ok="Exclusive inline schema 400 leftover content $ref.",
        ),
    ),
    (
        plant(
            slug="oas-propertynames-format",
            domain="oas-propertynames-vs-free-keys",
            success=True,
            name="pnames",
            stack="OpenAPI 3.1 propertyNames + Go",
            field="propertyNames",
            old="free keys leftover",
            new="propertyNames format",
            fail_err="400: leftover free keys after propertyNames-only",
            plan="propertyNames-only 400s leftover free keys. Dual-accept free keys for one release.",
            residual="map still free leftover; drop after map 6",
            vs="wrap propertynames-extension (propertyNames format vs free keys, not extension)",
            fetch1="https://json-schema.org/understanding-json-schema/reference/object#propertyNames",
            fetch1_ok="propertyNames constrains keys; free keys are leftover.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object",
            fetch2_ok="Exclusive propertyNames 400 leftover free keys.",
        ),
        plant(
            slug="leftover-free-keys",
            domain="free-keys-vs-oas-propertynames",
            success=False,
            name="freek",
            stack="OpenAPI leftover free keys + Java + TS",
            field="additionalProperties",
            old="propertyNames format",
            new="free keys leftover only",
            fail_err="400: leftover propertyNames after free-keys-only",
            plan="Free-keys-only 400s leftover propertyNames. Freeze propertyNames, spec free leftover.",
            residual="handoff: keep propertyNames or force free keys leftover",
            vs="wrap propertynames-extension (free keys leftover, not extension cartesian)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object",
            fetch1_ok="Free object keys are not propertyNames.",
            fetch2="https://json-schema.org/understanding-json-schema/reference/object#propertyNames",
            fetch2_ok="Exclusive free keys 400 leftover propertyNames.",
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
    print(json.dumps({"round": round_n, "idx": idx, "ids": [e1["id"], e2["id"]], "catalog": "r3899"}))


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
