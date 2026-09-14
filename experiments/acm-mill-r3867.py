#!/usr/bin/env python3
"""New unique OpenAPI-drift ACM catalog from r3867.

BAN r3866 oas-lll4-proto-optional / protobuf-lll4-optional-oas,
r3850 accept-language-bcp47 / iso639-language, r3713 smile/cbor,
r3560 422-vs-400 / 207-multistatus, prior w131 cartesian, and
r3561–r3851 leftover leftover leftover protocol clones.
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
            slug="oas31-webhooks-map",
            domain="oas31-webhooks-vs-oas30-callbacks",
            success=True,
            name="whk31",
            stack="OpenAPI 3.1 webhooks + Go",
            field="webhooks",
            old="callbacks leftover map",
            new="webhooks OAS31 map",
            fail_err="400: leftover callbacks after OAS 3.1 webhooks-only",
            plan="OAS 3.1 webhooks-only 400s leftover callbacks. Dual-bind callbacks for one release.",
            residual="edge still callbacks leftover; drop after edge 4",
            vs="r3866 oas-lll4-proto-optional (webhooks vs callbacks, not protobuf optional)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#oasWebhooks",
            fetch1_ok="OAS 3.1 webhooks are not OAS 3.0 callbacks maps.",
            fetch2="https://spec.openapis.org/oas/v3.0.3.html#callback-object",
            fetch2_ok="Exclusive webhooks 400 leftover callbacks producers.",
        ),
        plant(
            slug="oas30-callbacks-map",
            domain="oas30-callbacks-vs-oas31-webhooks",
            success=False,
            name="cbk30",
            stack="OpenAPI 3.0 callbacks + Java + TS",
            field="callbacks",
            old="webhooks OAS31 map",
            new="callbacks leftover map only",
            fail_err="400: leftover webhooks after OAS 3.0 callbacks-only",
            plan="Callbacks-only 400s leftover webhooks. Freeze webhooks, spec callbacks leftover.",
            residual="handoff: keep OAS 3.1 webhooks or force callbacks leftover",
            vs="r3866 protobuf-lll4-optional-oas (callbacks vs webhooks, not protobuf optional)",
            fetch1="https://spec.openapis.org/oas/v3.0.3.html#callback-object",
            fetch1_ok="OAS 3.0 callbacks are not OAS 3.1 webhooks.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#oasWebhooks",
            fetch2_ok="Exclusive callbacks 400 leftover webhooks.",
        ),
    ),
    (
        plant(
            slug="oas31-schema-dialect",
            domain="oas31-jsondialect-vs-draft04",
            success=True,
            name="dial31",
            stack="OpenAPI 3.1 jsonSchemaDialect + Go",
            field="jsonSchemaDialect",
            old="draft04 leftover schema",
            new="jsonSchemaDialect 2020-12",
            fail_err="400: leftover draft-04 after OAS 3.1 dialect-only",
            plan="OAS 3.1 dialect-only 400s leftover draft-04. Dual-accept draft-04 for one release.",
            residual="codegen still draft-04 leftover; drop after codegen 5",
            vs="r3850 accept-language-bcp47 (dialect vs draft-04, not BCP 47)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#fixed-fields",
            fetch1_ok="OAS 3.1 jsonSchemaDialect is not draft-04 $schema.",
            fetch2="https://json-schema.org/draft-04/json-schema-core.html",
            fetch2_ok="Exclusive 2020-12 dialect 400 leftover draft-04.",
        ),
        plant(
            slug="leftover-schema-draft04",
            domain="draft04-vs-oas31-jsondialect",
            success=False,
            name="drf04",
            stack="JSON Schema draft-04 leftover + Java + TS",
            field="$schema",
            old="jsonSchemaDialect 2020-12",
            new="draft04 leftover schema only",
            fail_err="400: leftover 2020-12 after draft-04-only",
            plan="Draft-04-only 400s leftover 2020-12. Freeze dialect, spec draft-04 leftover.",
            residual="handoff: keep OAS 3.1 dialect or force draft-04 leftover",
            vs="r3850 iso639-language (draft-04 vs dialect, not ISO 639)",
            fetch1="https://json-schema.org/draft-04/json-schema-core.html",
            fetch1_ok="Draft-04 $schema is not OAS 3.1 jsonSchemaDialect.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#fixed-fields",
            fetch2_ok="Exclusive draft-04 400 leftover 2020-12 dialect.",
        ),
    ),
    (
        plant(
            slug="oas31-exclmin-numeric",
            domain="oas31-exclmin-number-vs-oas30-bool",
            success=True,
            name="xmin31",
            stack="OpenAPI 3.1 exclusiveMinimum number + Go",
            field="exclusiveMinimum",
            old="boolean leftover exclusiveMinimum",
            new="numeric exclusiveMinimum",
            fail_err="400: leftover boolean exclusiveMinimum after OAS 3.1 number-only",
            plan="OAS 3.1 numeric exclusiveMinimum-only 400s leftover boolean. Dual-read boolean for one release.",
            residual="java client still boolean leftover; drop after java 6",
            vs="r3713 smile-binary-json (exclusiveMinimum number vs bool, not Smile)",
            fetch1="https://json-schema.org/understanding-json-schema/reference/numeric#range",
            fetch1_ok="Draft 2020-12 exclusiveMinimum is a number, not a boolean.",
            fetch2="https://spec.openapis.org/oas/v3.0.3.html#data-types",
            fetch2_ok="Exclusive numeric exclusiveMinimum 400 leftover boolean OAS 3.0.",
        ),
        plant(
            slug="oas30-exclmin-flag",
            domain="oas30-exclmin-bool-vs-oas31-number",
            success=False,
            name="xmin30",
            stack="OpenAPI 3.0 exclusiveMinimum boolean + Java + TS",
            field="exclusiveMinimum",
            old="numeric exclusiveMinimum",
            new="boolean leftover exclusiveMinimum only",
            fail_err="400: leftover numeric exclusiveMinimum after OAS 3.0 boolean-only",
            plan="Boolean exclusiveMinimum-only 400s leftover number. Freeze numeric, spec boolean leftover.",
            residual="handoff: keep OAS 3.1 number or force boolean leftover",
            vs="r3713 cbor-majortype-vs-smile (exclusiveMinimum bool vs number, not CBOR)",
            fetch1="https://spec.openapis.org/oas/v3.0.3.html#data-types",
            fetch1_ok="OAS 3.0 exclusiveMinimum is a boolean flag, not a number.",
            fetch2="https://json-schema.org/understanding-json-schema/reference/numeric#range",
            fetch2_ok="Exclusive boolean exclusiveMinimum 400 leftover numeric.",
        ),
    ),
    (
        plant(
            slug="oas-encoding-ctype",
            domain="oas-encoding-contenttype-vs-prop-media",
            success=True,
            name="encct",
            stack="OpenAPI 3.1 encoding.contentType + Go",
            field="contentType",
            old="property media leftover",
            new="encoding contentType",
            fail_err="415: leftover property media after encoding.contentType-only",
            plan="encoding.contentType-only 415s leftover property media. Dual-read property media for one release.",
            residual="multipart still property media leftover; drop after multipart 5",
            vs="r3866 oas-lll4-proto-optional (encoding.contentType, not protobuf nullable)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#encoding-object",
            fetch1_ok="encoding.contentType is not a schema-level media type.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object",
            fetch2_ok="Exclusive encoding.contentType 415 leftover property media.",
        ),
        plant(
            slug="leftover-prop-mediatype",
            domain="prop-media-vs-oas-encoding-contenttype",
            success=False,
            name="pmedia",
            stack="OpenAPI leftover property media + Java + TS",
            field="mediaType",
            old="encoding contentType",
            new="property media leftover only",
            fail_err="415: leftover encoding.contentType after property-media-only",
            plan="Property-media-only 415s leftover encoding.contentType. Freeze encoding, spec property media leftover.",
            residual="handoff: keep encoding.contentType or force property media leftover",
            vs="r3866 protobuf-lll4-optional-oas (property media, not protobuf optional)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#media-type-object",
            fetch1_ok="Property-level media is not encoding.contentType.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#encoding-object",
            fetch2_ok="Exclusive property media 415 leftover encoding.contentType.",
        ),
    ),
    (
        plant(
            slug="oas-pathitem-dollarref",
            domain="oas-pathitem-ref-vs-inline-path",
            success=True,
            name="piref",
            stack="OpenAPI 3.1 Path Item $ref + Go",
            field="$ref",
            old="inline path leftover",
            new="pathItem dollarref",
            fail_err="400: leftover inline path after Path Item $ref-only",
            plan="Path Item $ref-only 400s leftover inline paths. Dual-read inline for one release.",
            residual="gateway still inline leftover; drop after gateway 6",
            vs="r3851 oas-lll4-protobuf-map (Path Item $ref, not additionalProperties map)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#path-item-object",
            fetch1_ok="OAS 3.1 Path Item $ref is not a duplicated inline path.",
            fetch2="https://spec.openapis.org/oas/v3.0.3.html#path-item-object",
            fetch2_ok="Exclusive Path Item $ref 400 leftover inline paths.",
        ),
        plant(
            slug="leftover-dup-inline-path",
            domain="inline-path-vs-oas-pathitem-ref",
            success=False,
            name="pinln",
            stack="OpenAPI leftover inline paths + Java + TS",
            field="paths",
            old="pathItem dollarref",
            new="inline path leftover only",
            fail_err="400: leftover Path Item $ref after inline-only",
            plan="Inline-only 400s leftover Path Item $ref. Freeze $ref, spec inline leftover.",
            residual="handoff: keep Path Item $ref or force inline leftover",
            vs="r3851 protobuf-lll4-map-oas (inline path, not protobuf map)",
            fetch1="https://spec.openapis.org/oas/v3.0.3.html#path-item-object",
            fetch1_ok="Inline paths are not OAS 3.1 Path Item $ref.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#path-item-object",
            fetch2_ok="Exclusive inline paths 400 leftover Path Item $ref.",
        ),
    ),
    (
        plant(
            slug="oas-links-opref",
            domain="oas-link-operationref-vs-opid",
            success=True,
            name="lopref",
            stack="OpenAPI 3.1 links.operationRef + Go",
            field="operationRef",
            old="operationId leftover link",
            new="operationRef link",
            fail_err="400: leftover operationId after operationRef-only",
            plan="operationRef-only 400s leftover operationId links. Dual-read operationId for one release.",
            residual="sdk still operationId leftover; drop after sdk 5",
            vs="wrap link-operationid-rename (operationRef vs operationId leftover, not rename)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#link-object",
            fetch1_ok="operationRef is a runtime expression, not an operationId string.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#fixed-fields-18",
            fetch2_ok="Exclusive operationRef 400 leftover operationId links.",
        ),
        plant(
            slug="leftover-links-opid",
            domain="oas-link-opid-vs-operationref",
            success=False,
            name="lopid",
            stack="OpenAPI leftover operationId links + Java + TS",
            field="operationId",
            old="operationRef link",
            new="operationId leftover link only",
            fail_err="400: leftover operationRef after operationId-only",
            plan="operationId-only 400s leftover operationRef. Freeze operationRef, spec operationId leftover.",
            residual="handoff: keep operationRef or force operationId leftover",
            vs="wrap link-operationid-rename (leftover operationId, not rename cartesian)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#fixed-fields-18",
            fetch1_ok="operationId links are not operationRef expressions.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#link-object",
            fetch2_ok="Exclusive operationId 400 leftover operationRef.",
        ),
    ),
    (
        plant(
            slug="oas31-schema-const",
            domain="oas31-const-vs-enum-singleton",
            success=True,
            name="cnst31",
            stack="OpenAPI 3.1 JSON Schema const + Go",
            field="const",
            old="enum leftover singleton",
            new="schema const",
            fail_err="400: leftover enum singleton after const-only",
            plan="const-only 400s leftover enum singleton. Dual-read enum-of-one for one release.",
            residual="validator still enum leftover; drop after validator 4",
            vs="wrap const-status-replaces-enum (schema const vs enum singleton, not status enum)",
            fetch1="https://json-schema.org/understanding-json-schema/reference/const",
            fetch1_ok="JSON Schema const is not an enum array of one value.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object",
            fetch2_ok="Exclusive const 400 leftover enum singleton.",
        ),
        plant(
            slug="leftover-single-enum",
            domain="enum-singleton-vs-oas31-const",
            success=False,
            name="enum1",
            stack="OpenAPI leftover enum singleton + Java + TS",
            field="enum",
            old="schema const",
            new="enum leftover singleton only",
            fail_err="400: leftover const after enum-singleton-only",
            plan="Enum-singleton-only 400s leftover const. Freeze const, spec enum leftover.",
            residual="handoff: keep const or force enum singleton leftover",
            vs="wrap const-status-replaces-enum (enum leftover, not status const cartesian)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object",
            fetch1_ok="enum:[value] is not JSON Schema const.",
            fetch2="https://json-schema.org/understanding-json-schema/reference/const",
            fetch2_ok="Exclusive enum singleton 400 leftover const.",
        ),
    ),
    (
        plant(
            slug="oas-srv-var-enum",
            domain="oas-server-var-enum-vs-free-host",
            success=True,
            name="svenum",
            stack="OpenAPI 3.1 servers.variables.enum + Go",
            field="enum",
            old="freeform host leftover",
            new="server variable enum",
            fail_err="400: leftover free host after server-variable-enum-only",
            plan="Server variable enum-only 400s leftover free host. Dual-accept free host for one release.",
            residual="mesh still free host leftover; drop after mesh 7",
            vs="wrap server-var-region (server variable enum vs free host, not region)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#server-variable-object",
            fetch1_ok="servers.variables.enum is not an unconstrained hostname.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#server-object",
            fetch2_ok="Exclusive server variable enum 400 leftover free host.",
        ),
        plant(
            slug="leftover-freeform-host",
            domain="free-host-vs-oas-server-var-enum",
            success=False,
            name="freeh",
            stack="OpenAPI leftover free host + Java + TS",
            field="host",
            old="server variable enum",
            new="freeform host leftover only",
            fail_err="400: leftover server variable enum after free-host-only",
            plan="Free-host-only 400s leftover server variable enum. Freeze enum, spec free host leftover.",
            residual="handoff: keep server variable enum or force free host leftover",
            vs="wrap server-var-region (free host leftover, not region cartesian)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#server-object",
            fetch1_ok="Freeform host is not servers.variables.enum.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#server-variable-object",
            fetch2_ok="Exclusive free host 400 leftover server variable enum.",
        ),
    ),
    (
        plant(
            slug="oas-hdr-simple-explode",
            domain="oas-header-simple-explode-vs-form",
            success=True,
            name="hdsexp",
            stack="OpenAPI 3.1 header style=simple explode + Go",
            field="explode",
            old="header form leftover",
            new="header simple explode",
            fail_err="400: leftover header form after simple-explode-only",
            plan="Header simple explode-only 400s leftover form. Dual-read form for one release.",
            residual="proxy still form leftover; drop after proxy 5",
            vs="r3715 openapi-style-deepobject-vs-form (header simple explode, not query deepObject)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#style-values",
            fetch1_ok="Header style=simple explode is not form-style serialization.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object",
            fetch2_ok="Exclusive header simple explode 400 leftover form.",
        ),
        plant(
            slug="leftover-hdr-form-style",
            domain="header-form-vs-oas-simple-explode",
            success=False,
            name="hdfrm",
            stack="OpenAPI leftover header form + Java + TS",
            field="style",
            old="header simple explode",
            new="header form leftover only",
            fail_err="400: leftover simple explode after header-form-only",
            plan="Header-form-only 400s leftover simple explode. Freeze explode, spec form leftover.",
            residual="handoff: keep simple explode or force header form leftover",
            vs="r3715 openapi-style-deepobject-vs-form (header form leftover, not query deepObject)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object",
            fetch1_ok="Header form style is not simple explode.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#style-values",
            fetch2_ok="Exclusive header form 400 leftover simple explode.",
        ),
    ),
    (
        plant(
            slug="oas-in-cookie-param",
            domain="oas-cookie-param-vs-cookie-header",
            success=True,
            name="incook",
            stack="OpenAPI 3.1 in=cookie parameter + Go",
            field="in",
            old="Cookie header leftover",
            new="in cookie parameter",
            fail_err="400: leftover Cookie header after in=cookie-only",
            plan="in=cookie-only 400s leftover Cookie header params. Dual-read Cookie header for one release.",
            residual="browser still Cookie header leftover; drop after browser 6",
            vs="r3835 cookie-samesite-lax (in=cookie parameter, not SameSite)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-locations",
            fetch1_ok="in=cookie is a parameter location, not a raw Cookie header.",
            fetch2="https://datatracker.ietf.org/doc/html/rfc6265",
            fetch2_ok="Exclusive in=cookie 400 leftover Cookie header.",
        ),
        plant(
            slug="leftover-cookie-header-param",
            domain="cookie-header-vs-oas-cookie-param",
            success=False,
            name="ckhdr",
            stack="OpenAPI leftover Cookie header + Java + TS",
            field="Cookie",
            old="in cookie parameter",
            new="Cookie header leftover only",
            fail_err="400: leftover in=cookie after Cookie-header-only",
            plan="Cookie-header-only 400s leftover in=cookie. Freeze in=cookie, spec Cookie header leftover.",
            residual="handoff: keep in=cookie or force Cookie header leftover",
            vs="r3835 cookie-samesite-none (Cookie header leftover, not SameSite)",
            fetch1="https://datatracker.ietf.org/doc/html/rfc6265",
            fetch1_ok="Raw Cookie header is not OAS in=cookie.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-locations",
            fetch2_ok="Exclusive Cookie header 400 leftover in=cookie.",
        ),
    ),
    (
        plant(
            slug="oas-body-must-exist",
            domain="oas-reqbody-required-vs-optional-empty",
            success=True,
            name="bodyrq",
            stack="OpenAPI 3.1 requestBody.required + Go",
            field="required",
            old="optional empty body leftover",
            new="requestBody required",
            fail_err="400: leftover empty body after requestBody.required-only",
            plan="requestBody.required-only 400s leftover empty body. Dual-accept empty for one release.",
            residual="batch still empty body leftover; drop after batch 5",
            vs="wrap requestbody-required-put (required body vs empty leftover, not PUT-only)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#request-body-object",
            fetch1_ok="requestBody.required true is not an optional empty body.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#operation-object",
            fetch2_ok="Exclusive required body 400 leftover empty body.",
        ),
        plant(
            slug="leftover-body-optional",
            domain="optional-empty-vs-oas-reqbody-required",
            success=False,
            name="bodyop",
            stack="OpenAPI leftover optional body + Java + TS",
            field="requestBody",
            old="requestBody required",
            new="optional empty body leftover only",
            fail_err="400: leftover required body after optional-empty-only",
            plan="Optional-empty-only 400s leftover required body. Freeze required, spec empty leftover.",
            residual="handoff: keep required body or force optional empty leftover",
            vs="wrap requestbody-required-put (optional empty leftover, not PUT cartesian)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#operation-object",
            fetch1_ok="Optional empty body is not requestBody.required.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#request-body-object",
            fetch2_ok="Exclusive optional empty 400 leftover required body.",
        ),
    ),
    (
        plant(
            slug="oas-oidc-scheme",
            domain="oas-oidc-vs-oauth-implicit-leftover",
            success=True,
            name="oidcs",
            stack="OpenAPI 3.1 openIdConnect + Go",
            field="openIdConnectUrl",
            old="oauth implicit leftover",
            new="openIdConnect scheme",
            fail_err="401: leftover oauth implicit after openIdConnect-only",
            plan="openIdConnect-only 401s leftover oauth implicit. Dual-accept implicit for one release.",
            residual="spa still implicit leftover; drop after spa 8",
            vs="wrap implicit-flow-removed (OIDC scheme vs implicit leftover, not flow-removed cartesian)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object",
            fetch1_ok="openIdConnect is not oauth2 implicit.",
            fetch2="https://spec.openapis.org/oas/v3.0.3.html#oauth-flows-object",
            fetch2_ok="Exclusive openIdConnect 401 leftover oauth implicit.",
        ),
        plant(
            slug="leftover-oauth-implicit-flow",
            domain="oauth-implicit-vs-oas-oidc",
            success=False,
            name="oaimp",
            stack="OpenAPI leftover oauth implicit + Java + TS",
            field="implicit",
            old="openIdConnect scheme",
            new="oauth implicit leftover only",
            fail_err="401: leftover openIdConnect after implicit-only",
            plan="Implicit-only 401s leftover openIdConnect. Freeze OIDC, spec implicit leftover.",
            residual="handoff: keep openIdConnect or force implicit leftover",
            vs="wrap implicit-flow-removed (implicit leftover, not flow-removed cartesian)",
            fetch1="https://spec.openapis.org/oas/v3.0.3.html#oauth-flows-object",
            fetch1_ok="oauth2 implicit is not openIdConnect.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object",
            fetch2_ok="Exclusive implicit 401 leftover openIdConnect.",
        ),
    ),
    (
        plant(
            slug="oas-query-allowreserved",
            domain="oas-allowreserved-vs-pct-encode",
            success=True,
            name="qalres",
            stack="OpenAPI 3.1 allowReserved + Go",
            field="allowReserved",
            old="percent encode leftover",
            new="query allowReserved",
            fail_err="400: leftover percent-encode after allowReserved-only",
            plan="allowReserved-only 400s leftover percent-encode. Dual-accept encoded for one release.",
            residual="cdn still percent-encode leftover; drop after cdn 4",
            vs="wrap allowreserved-callback (query allowReserved vs percent-encode, not callback URL)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object",
            fetch1_ok="allowReserved lets RFC 3986 reserved chars pass unencoded.",
            fetch2="https://datatracker.ietf.org/doc/html/rfc3986#section-2.2",
            fetch2_ok="Exclusive allowReserved 400 leftover percent-encode.",
        ),
        plant(
            slug="leftover-query-pctencode",
            domain="pct-encode-vs-oas-allowreserved",
            success=False,
            name="qpcte",
            stack="OpenAPI leftover percent-encode + Java + TS",
            field="encode",
            old="query allowReserved",
            new="percent encode leftover only",
            fail_err="400: leftover allowReserved after percent-encode-only",
            plan="Percent-encode-only 400s leftover allowReserved. Freeze allowReserved, spec encode leftover.",
            residual="handoff: keep allowReserved or force percent-encode leftover",
            vs="wrap allowreserved-callback (percent-encode leftover, not callback cartesian)",
            fetch1="https://datatracker.ietf.org/doc/html/rfc3986#section-2.2",
            fetch1_ok="Always percent-encoding is not allowReserved.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object",
            fetch2_ok="Exclusive percent-encode 400 leftover allowReserved.",
        ),
    ),
    (
        plant(
            slug="oas-sunset-http-date",
            domain="oas-sunset-date-vs-deprecated-flag",
            success=True,
            name="sunhd",
            stack="OpenAPI Sunset header + Go",
            field="Sunset",
            old="deprecated flag leftover",
            new="Sunset HTTP-date",
            fail_err="400: leftover deprecated-only after Sunset-date-only",
            plan="Sunset HTTP-date-only 400s leftover deprecated flag. Dual-emit deprecated for one release.",
            residual="portal still deprecated leftover; drop after portal 6",
            vs="wrap sunset-header-deprecation (Sunset HTTP-date vs deprecated flag, not deprecation cartesian)",
            fetch1="https://datatracker.ietf.org/doc/html/rfc8594",
            fetch1_ok="Sunset is an HTTP-date, not OAS deprecated:true alone.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#operation-object",
            fetch2_ok="Exclusive Sunset date 400 leftover deprecated flag.",
        ),
        plant(
            slug="leftover-deprecated-flag",
            domain="deprecated-flag-vs-oas-sunset-date",
            success=False,
            name="depfl",
            stack="OpenAPI leftover deprecated flag + Java + TS",
            field="deprecated",
            old="Sunset HTTP-date",
            new="deprecated flag leftover only",
            fail_err="400: leftover Sunset after deprecated-only",
            plan="Deprecated-only 400s leftover Sunset date. Freeze Sunset, spec deprecated leftover.",
            residual="handoff: keep Sunset date or force deprecated leftover",
            vs="wrap sunset-header-deprecation (deprecated leftover, not sunset cartesian)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#operation-object",
            fetch1_ok="deprecated:true is not a Sunset HTTP-date.",
            fetch2="https://datatracker.ietf.org/doc/html/rfc8594",
            fetch2_ok="Exclusive deprecated flag 400 leftover Sunset date.",
        ),
    ),
    (
        plant(
            slug="oas-readonly-field",
            domain="oas-readonly-vs-writeonly-leftover",
            success=True,
            name="rofld",
            stack="OpenAPI 3.1 readOnly + Go",
            field="readOnly",
            old="writeOnly leftover field",
            new="readOnly response field",
            fail_err="400: leftover writeOnly after readOnly-only",
            plan="readOnly-only 400s leftover writeOnly. Dual-accept writeOnly for one release.",
            residual="form still writeOnly leftover; drop after form 5",
            vs="r3842 minlength-code (readOnly vs writeOnly leftover, not minLength)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object",
            fetch1_ok="readOnly fields belong on responses, not writeOnly requests.",
            fetch2="https://json-schema.org/draft/2020-12/json-schema-validation.html#name-readonly-and-writeonly",
            fetch2_ok="Exclusive readOnly 400 leftover writeOnly.",
        ),
        plant(
            slug="leftover-writeonly-field",
            domain="writeonly-vs-oas-readonly",
            success=False,
            name="wofld",
            stack="OpenAPI leftover writeOnly + Java + TS",
            field="writeOnly",
            old="readOnly response field",
            new="writeOnly leftover field only",
            fail_err="400: leftover readOnly after writeOnly-only",
            plan="writeOnly-only 400s leftover readOnly. Freeze readOnly, spec writeOnly leftover.",
            residual="handoff: keep readOnly or force writeOnly leftover",
            vs="r3842 unconstrained-string (writeOnly leftover, not minLength)",
            fetch1="https://json-schema.org/draft/2020-12/json-schema-validation.html#name-readonly-and-writeonly",
            fetch1_ok="writeOnly is not readOnly.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object",
            fetch2_ok="Exclusive writeOnly 400 leftover readOnly.",
        ),
    ),
    (
        plant(
            slug="oas-param-content-map",
            domain="oas-param-content-vs-schema-only",
            success=True,
            name="pcnt",
            stack="OpenAPI 3.1 parameter content + Go",
            field="content",
            old="schema only leftover",
            new="parameter content map",
            fail_err="400: leftover schema-only param after content-map-only",
            plan="parameter content-only 400s leftover schema-only. Dual-read schema-only for one release.",
            residual="qs still schema-only leftover; drop after qs 6",
            vs="r3829 json-schema-type-array (parameter content vs schema-only, not type array)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object",
            fetch1_ok="parameter content is mutually exclusive with schema in OAS.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object",
            fetch2_ok="Exclusive parameter content 400 leftover schema-only.",
        ),
        plant(
            slug="leftover-param-schema-only",
            domain="schema-only-param-vs-oas-content",
            success=False,
            name="pschm",
            stack="OpenAPI leftover schema-only param + Java + TS",
            field="schema",
            old="parameter content map",
            new="schema only leftover only",
            fail_err="400: leftover parameter content after schema-only",
            plan="Schema-only 400s leftover parameter content. Freeze content, spec schema leftover.",
            residual="handoff: keep parameter content or force schema-only leftover",
            vs="r3829 comma-string-leftover (schema-only leftover, not type array)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#media-type-object",
            fetch1_ok="schema-only params are not parameter content maps.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object",
            fetch2_ok="Exclusive schema-only 400 leftover parameter content.",
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
    print(json.dumps({"round": round_n, "idx": idx, "ids": [e1["id"], e2["id"]], "catalog": "r3867"}))


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
