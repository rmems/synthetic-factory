#!/usr/bin/env python3
"""Sixth unique OpenAPI-drift ACM catalog after r4070 mill. Fast slug load."""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
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
FACTORY = _b.FACTORY
SEED_RE = re.compile(r"seed=([a-z0-9-]+)")
SLUG_RE = re.compile(r'slug="([^"]+)"')

BANNED_PRIOR: set[str] = set()
for path in HERE.glob("acm-mill-r*.py"):
    if path.name == Path(__file__).name:
        continue
    BANNED_PRIOR.update(SLUG_RE.findall(path.read_text(errors="ignore")))
BANNED_PRIOR |= {
    "oas-allowemptyvalue-header", "leftover-omit-header-empty",
    "oas-lll4-proto-optional", "protobuf-lll4-optional-oas",
    "accept-language-bcp47", "iso639-language",
    "smile-binary-json", "cbor-majortype-vs-smile",
    "422-vs-400-validation", "207-multistatus-batch",
}


def published_slugs() -> set[str]:
    found: set[str] = set()
    if FACTORY.is_dir():
        for path in FACTORY.glob("NOTES-r*.md"):
            try:
                found.update(SEED_RE.findall(path.read_text(errors="ignore")))
            except OSError:
                continue
    return found


def p(**kw):
    return plant(**kw)


PAIRS: list[tuple[dict, dict]] = [
    (p(slug="oas-schema-max-properties", domain="oas-maxproperties-vs-no-max", success=True, name="maxprop", stack="OpenAPI 3.1 maxProperties + Go", field="maxProperties", old="no max properties leftover", new="object maxProperties", fail_err="400: leftover no-max after maxProperties-only", plan="maxProperties-only 400s leftover no-max. Dual-accept no-max for one release.", residual="form still no-max leftover; drop after form 5", vs="r4038 leftover-empty-object-body (maxProperties vs no-max leftover, not minProperties)", fetch1="https://json-schema.org/understanding-json-schema/reference/object#maxproperties", fetch1_ok="maxProperties caps object keys, leftover unbounded objects fail closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive maxProperties 400 leftover no-max."),
     p(slug="leftover-no-max-properties", domain="no-max-vs-oas-maxproperties", success=False, name="nomaxp", stack="OpenAPI leftover no max properties + Java + TS", field="properties", old="object maxProperties", new="no max properties leftover only", fail_err="400: leftover maxProperties after no-max-only", plan="No-max-only 400s leftover maxProperties. Freeze maxProperties, spec no-max leftover.", residual="handoff: keep maxProperties or force no-max leftover", vs="r4038 oas-schema-min-properties (no-max leftover, not minProperties)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Unbounded leftover objects are not maxProperties.", fetch2="https://json-schema.org/understanding-json-schema/reference/object#maxproperties", fetch2_ok="Exclusive no-max 400 leftover maxProperties.")),
    (p(slug="oas-header-explode-false", domain="oas-header-unexplode-vs-explode", success=True, name="hdrunx", stack="OpenAPI 3.1 header explode=false + Go", field="explode", old="header explode leftover", new="header explode false", fail_err="400: leftover header explode after unexplode-only", plan="header-explode-false-only 400s leftover explode. Dual-read explode for one release.", residual="proxy still explode leftover; drop after proxy 5", vs="r4023 leftover-always-explode (header unexplode vs explode leftover, not query explode)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch1_ok="Header explode=false is not leftover always-explode headers.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch2_ok="Exclusive header unexplode 400 leftover explode."),
     p(slug="leftover-header-explode", domain="header-explode-vs-oas-header-unexplode", success=False, name="hdrexpl", stack="OpenAPI leftover header explode + Java + TS", field="explode", old="header explode false", new="header explode leftover only", fail_err="400: leftover explode=false after explode-only", plan="Explode-only 400s leftover header explode=false. Freeze false, spec explode leftover.", residual="handoff: keep header unexplode or force explode leftover", vs="r4023 oas-parameter-explode-false (header explode leftover, not query explode)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch1_ok="Header explode leftover is not explode=false.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch2_ok="Exclusive header explode 400 leftover false.")),
    (p(slug="oas-webhook-trace", domain="oas-webhook-trace-vs-connect", success=True, name="whktrc", stack="OpenAPI 3.1 webhook TRACE + Go", field="trace", old="webhook CONNECT leftover", new="webhook TRACE", fail_err="405: leftover webhook CONNECT after TRACE-only", plan="Webhook-TRACE-only 405s leftover CONNECT. Dual-accept CONNECT for one release.", residual="edge still CONNECT leftover; drop after edge 4", vs="r4038 leftover-webhook-trace (TRACE vs CONNECT leftover, not OPTIONS mill leftover)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#oasWebhooks", fetch1_ok="Webhook Path Items may TRACE; leftover CONNECT is not the contract.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#path-item-object", fetch2_ok="Exclusive webhook TRACE 405 leftover CONNECT."),
     p(slug="leftover-webhook-connect", domain="webhook-connect-vs-oas-webhook-trace", success=False, name="whkcon", stack="OpenAPI leftover webhook CONNECT + Java + TS", field="connect", old="webhook TRACE", new="webhook CONNECT leftover only", fail_err="405: leftover webhook TRACE after CONNECT-only", plan="Webhook-CONNECT-only 405s leftover TRACE. Freeze TRACE, spec CONNECT leftover.", residual="handoff: keep webhook TRACE or force CONNECT leftover", vs="r4038 oas-webhook-options (CONNECT leftover, not OPTIONS mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#path-item-object", fetch1_ok="Webhook CONNECT is not the TRACE-only contract.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#oasWebhooks", fetch2_ok="Exclusive webhook CONNECT 405 leftover TRACE.")),
    (p(slug="oas-schema-min-contains", domain="oas-mincontains-vs-contains-zero", success=True, name="minc", stack="OpenAPI 3.1 minContains + Go", field="minContains", old="contains zero leftover", new="array minContains", fail_err="400: leftover contains-zero after minContains-only", plan="minContains-only 400s leftover contains-zero. Dual-accept zero for one release.", residual="validator still zero leftover; drop after validator 5", vs="r3947 leftover-unbounded-contains (minContains vs zero leftover, not maxContains)", fetch1="https://json-schema.org/understanding-json-schema/reference/array#mincontains", fetch1_ok="minContains requires matches, leftover zero-match arrays fail closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive minContains 400 leftover zero."),
     p(slug="leftover-contains-zero", domain="contains-zero-vs-oas-mincontains", success=False, name="czero", stack="OpenAPI leftover contains zero + Java + TS", field="contains", old="array minContains", new="contains zero leftover only", fail_err="400: leftover minContains after zero-only", plan="Zero-only 400s leftover minContains. Freeze minContains, spec zero leftover.", residual="handoff: keep minContains or force zero leftover", vs="r3947 oas-maxcontains-array (zero leftover, not maxContains)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Zero-match leftover is not minContains.", fetch2="https://json-schema.org/understanding-json-schema/reference/array#mincontains", fetch2_ok="Exclusive contains-zero 400 leftover minContains.")),
    (p(slug="oas-format-duration-pn-m", domain="oas-duration-month-vs-months-int", success=True, name="durmon", stack="OpenAPI 3.1 format=duration PnM + Go", field="format", old="months int leftover", new="duration month", fail_err="400: leftover months-int after duration-month-only", plan="duration-month-only 400s leftover months-int. Dual-read months for one release.", residual="batch still months leftover; drop after batch 6", vs="r4007 leftover-days-int (PnM duration vs months leftover, not week mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/string#duration", fetch1_ok="format=duration PnM is ISO 8601 months, not leftover month counts.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="Exclusive duration month 400 leftover months-int."),
     p(slug="leftover-months-int", domain="months-int-vs-oas-duration-month", success=False, name="monint", stack="OpenAPI leftover months int + Java + TS", field="months", old="duration month", new="months int leftover only", fail_err="400: leftover duration-month after months-only", plan="Months-only 400s leftover duration-month. Freeze duration, spec months leftover.", residual="handoff: keep duration-month or force months leftover", vs="r4007 oas-format-duration-week (months leftover, not week mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="Integer months are not format=duration PnM.", fetch2="https://json-schema.org/understanding-json-schema/reference/string#duration", fetch2_ok="Exclusive months-int 400 leftover duration-month.")),
    (p(slug="oas-security-oauth2-scopes-required", domain="oas-scopes-vs-unscoped", success=True, name="scopes", stack="OpenAPI 3.1 oauth2 required scopes + Go", field="scopes", old="unscoped token leftover", new="oauth2 required scopes", fail_err="403: leftover unscoped after scopes-only", plan="required-scopes-only 403s leftover unscoped. Dual-accept unscoped for one release.", residual="idp still unscoped leftover; drop after idp 6", vs="wrap oauth-scope-wallet-read (required scopes vs unscoped leftover, not wallet cartesian)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#oauth-flow-object", fetch1_ok="scopes map required privileges, leftover unscoped tokens fail closed.", fetch2="https://datatracker.ietf.org/doc/html/rfc6749#section-3.3", fetch2_ok="Exclusive required scopes 403 leftover unscoped."),
     p(slug="leftover-unscoped-token", domain="unscoped-vs-oas-scopes", success=False, name="unscop", stack="OpenAPI leftover unscoped token + Java + TS", field="scopes", old="oauth2 required scopes", new="unscoped token leftover only", fail_err="403: leftover required scopes after unscoped-only", plan="Unscoped-only 403s leftover required scopes. Freeze scopes, spec unscoped leftover.", residual="handoff: keep required scopes or force unscoped leftover", vs="wrap oauth-scope-wallet-read (unscoped leftover, not wallet cartesian)", fetch1="https://datatracker.ietf.org/doc/html/rfc6749#section-3.3", fetch1_ok="Unscoped leftover tokens are not scopes.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#oauth-flow-object", fetch2_ok="Exclusive unscoped 403 leftover scopes.")),
    (p(slug="oas-xml-xmlns-required", domain="oas-xmlns-vs-no-xmlns", success=True, name="xmlns", stack="OpenAPI 3.1 xml.namespace required + Go", field="namespace", old="no xmlns leftover", new="xml namespace required", fail_err="415: leftover no-xmlns after xmlns-only", plan="xml.namespace-only 415s leftover no-xmlns. Dual-omit namespace for one release.", residual="batch still no-xmlns leftover; drop after batch 5", vs="r4023 leftover-unprefixed-ns (required xmlns vs none leftover, not prefix mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#xml-object", fetch1_ok="xml.namespace is an absolute URI, leftover missing xmlns fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive xmlns 415 leftover none."),
     p(slug="leftover-no-xmlns", domain="no-xmlns-vs-oas-xmlns", success=False, name="noxmlns", stack="OpenAPI leftover no xmlns + Java + TS", field="namespace", old="xml namespace required", new="no xmlns leftover only", fail_err="415: leftover xml.namespace after none-only", plan="None-only 415s leftover xml.namespace. Freeze namespace, spec none leftover.", residual="handoff: keep xml.namespace or force none leftover", vs="r4023 oas-xml-namespace-prefix (no-xmlns leftover, not prefix mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Missing xmlns is not xml.namespace.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#xml-object", fetch2_ok="Exclusive no-xmlns 415 leftover namespace.")),
    (p(slug="oas-content-multipart-digest", domain="oas-mp-digest-vs-unsigned", success=True, name="mpdig", stack="OpenAPI 3.1 multipart/digest + Go", field="content", old="unsigned parts leftover", new="multipart digest", fail_err="415: leftover unsigned parts after digest-only", plan="multipart-digest-only 415s leftover unsigned. Dual-read unsigned for one release.", residual="ingest still unsigned leftover; drop after ingest 6", vs="r4054 leftover-multipart-alternative (digest vs unsigned leftover, not alternative mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch1_ok="multipart/digest is not leftover unsigned parts.", fetch2="https://datatracker.ietf.org/doc/html/rfc2046#section-5.1.5", fetch2_ok="Exclusive multipart/digest 415 leftover unsigned."),
     p(slug="leftover-unsigned-parts", domain="unsigned-vs-oas-mp-digest", success=False, name="unsign", stack="OpenAPI leftover unsigned parts + Java + TS", field="content", old="multipart digest", new="unsigned parts leftover only", fail_err="415: leftover multipart/digest after unsigned-only", plan="Unsigned-only 415s leftover multipart/digest. Freeze digest, spec unsigned leftover.", residual="handoff: keep multipart/digest or force unsigned leftover", vs="r4054 oas-content-multipart-related (unsigned leftover, not related mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc2046#section-5.1.5", fetch1_ok="Unsigned leftover parts are not multipart/digest.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch2_ok="Exclusive unsigned 415 leftover digest.")),
    (p(slug="oas-link-parameters-runtime", domain="oas-link-params-vs-static", success=True, name="lnkrt", stack="OpenAPI 3.1 link parameters runtime + Go", field="parameters", old="static link params leftover", new="link runtime parameters", fail_err="400: leftover static link params after runtime-only", plan="link-runtime-params-only 400s leftover static. Dual-read static for one release.", residual="sdk still static leftover; drop after sdk 5", vs="r4038 leftover-query-link (runtime link params vs static leftover, not query link)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#link-object", fetch1_ok="Link parameters are runtime expressions, leftover static values fail closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#runtime-expressions", fetch2_ok="Exclusive runtime link params 400 leftover static."),
     p(slug="leftover-static-link-params", domain="static-link-vs-oas-runtime-params", success=False, name="lnkst", stack="OpenAPI leftover static link params + Java + TS", field="parameters", old="link runtime parameters", new="static link params leftover only", fail_err="400: leftover runtime params after static-only", plan="Static-only 400s leftover runtime params. Freeze runtime, spec static leftover.", residual="handoff: keep runtime link params or force static leftover", vs="r4038 oas-link-request-body (static leftover, not requestBody mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#runtime-expressions", fetch1_ok="Static leftover params are not runtime expressions.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#link-object", fetch2_ok="Exclusive static link params 400 leftover runtime.")),
    (p(slug="oas-schema-type-array-union", domain="oas-type-union-vs-scalar", success=True, name="typuni", stack="OpenAPI 3.1 type array union + Go", field="type", old="scalar only leftover", new="type array union", fail_err="400: leftover scalar-only after type-union-only", plan="type-union-only 400s leftover scalar. Dual-read scalar for one release.", residual="sdk still scalar leftover; drop after sdk 5", vs="r3561 type-null-union-oas31 (type union vs scalar leftover, not null union mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/type#type-specific-keywords", fetch1_ok="type as an array is a union, leftover scalar-only fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive type union 400 leftover scalar."),
     p(slug="leftover-scalar-only", domain="scalar-only-vs-oas-type-union", success=False, name="scalar", stack="OpenAPI leftover scalar only + Java + TS", field="type", old="type array union", new="scalar only leftover only", fail_err="400: leftover type union after scalar-only", plan="Scalar-only 400s leftover type union. Freeze union, spec scalar leftover.", residual="handoff: keep type union or force scalar leftover", vs="r3561 type-null-union-oas31 (scalar leftover, not null union)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Scalar leftover types are not type arrays.", fetch2="https://json-schema.org/understanding-json-schema/reference/type#type-specific-keywords", fetch2_ok="Exclusive scalar-only 400 leftover type union.")),
    (p(slug="oas-info-license-url", domain="oas-license-url-vs-spdx-only", success=True, name="licurl", stack="OpenAPI 3.1 license.url + Go", field="url", old="spdx only leftover", new="license url", fail_err="400: leftover spdx-only after url-only", plan="license.url-only 400s leftover spdx-only. Dual-omit url for one release.", residual="portal still spdx leftover; drop after portal 5", vs="r4054 leftover-missing-license (license url vs spdx leftover, not missing name)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#license-object", fetch1_ok="license.url is mutually exclusive with identifier in some tooling; leftover identifier-only is not url.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#info-object", fetch2_ok="Exclusive license url 400 leftover spdx-only."),
     p(slug="leftover-spdx-only", domain="spdx-only-vs-oas-license-url", success=False, name="spdxo", stack="OpenAPI leftover spdx only + Java + TS", field="identifier", old="license url", new="spdx only leftover only", fail_err="400: leftover license.url after spdx-only", plan="Spdx-only 400s leftover license.url. Freeze url, spec spdx leftover.", residual="handoff: keep license.url or force spdx leftover", vs="r4054 oas-info-license-name (spdx leftover, not license name)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#info-object", fetch1_ok="SPDX-only leftover is not license.url.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#license-object", fetch2_ok="Exclusive spdx-only 400 leftover url.")),
    (p(slug="oas-operation-callbacks-expression", domain="oas-cb-expr-vs-hardcoded", success=True, name="cbexpr", stack="OpenAPI 3.1 operation callback expr + Go", field="callbacks", old="hardcoded callback leftover", new="operation callback expression", fail_err="400: leftover hardcoded callback after expr-only", plan="callback-expression-only 400s leftover hardcoded. Dual-read hardcoded for one release.", residual="bus still hardcoded leftover; drop after bus 6", vs="r4023 leftover-no-callbacks (callback expr vs hardcoded leftover, not missing callbacks)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch1_ok="operation.callbacks keys are expressions, leftover hardcoded urls fail closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#callback-object", fetch2_ok="Exclusive callback expression 400 leftover hardcoded."),
     p(slug="leftover-hardcoded-callback", domain="hardcoded-vs-oas-cb-expr", success=False, name="cbhard", stack="OpenAPI leftover hardcoded callback + Java + TS", field="url", old="operation callback expression", new="hardcoded callback leftover only", fail_err="400: leftover callback expression after hardcoded-only", plan="Hardcoded-only 400s leftover callback expression. Freeze expression, spec hardcoded leftover.", residual="handoff: keep callback expression or force hardcoded leftover", vs="r4023 oas-operation-callbacks-required (hardcoded leftover, not required callbacks)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#callback-object", fetch1_ok="Hardcoded leftover urls are not callback expressions.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch2_ok="Exclusive hardcoded 400 leftover expression.")),
    (p(slug="oas-parameter-content-xml", domain="oas-param-xml-vs-schema-xml", success=True, name="pcxml", stack="OpenAPI 3.1 parameter content xml + Go", field="content", old="schema xml param leftover", new="parameter content xml", fail_err="415: leftover schema xml after content-xml-only", plan="parameter-content-xml-only 415s leftover schema xml. Dual-read schema for one release.", residual="gateway still schema leftover; drop after gateway 6", vs="r4038 leftover-schema-only-param (param xml content vs schema leftover, not json content)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="content application/xml is not leftover schema-only XML params.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch2_ok="Exclusive parameter xml content 415 leftover schema."),
     p(slug="leftover-schema-xml-param", domain="schema-xml-vs-oas-param-xml", success=False, name="schxml", stack="OpenAPI leftover schema xml param + Java + TS", field="schema", old="parameter content xml", new="schema xml param leftover only", fail_err="415: leftover parameter.content xml after schema-only", plan="Schema-only 415s leftover parameter.content xml. Freeze content, spec schema leftover.", residual="handoff: keep parameter xml content or force schema leftover", vs="r4038 oas-parameter-content-json (schema xml leftover, not json content)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch1_ok="Schema-only XML params are not content.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="Exclusive schema xml param 415 leftover content.")),
    (p(slug="oas-format-uuid-v4-only", domain="oas-uuidv4-vs-any-uuid", success=True, name="uuidv4", stack="OpenAPI 3.1 uuid v4 only + Go", field="format", old="any uuid leftover", new="uuid v4 only", fail_err="400: leftover any-uuid after v4-only", plan="uuid-v4-only 400s leftover any-uuid. Dual-read any for one release.", residual="store still any leftover; drop after store 5", vs="r4038 leftover-hex-id (uuid v4 vs any leftover, not hex mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/string#uuid", fetch1_ok="UUID v4-only is not leftover any-version UUIDs.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="Exclusive uuid v4 400 leftover any."),
     p(slug="leftover-any-uuid", domain="any-uuid-vs-oas-uuidv4", success=False, name="anyu", stack="OpenAPI leftover any uuid + Java + TS", field="id", old="uuid v4 only", new="any uuid leftover only", fail_err="400: leftover uuid-v4 after any-only", plan="Any-only 400s leftover uuid-v4. Freeze v4, spec any leftover.", residual="handoff: keep uuid v4 or force any leftover", vs="r4038 oas-format-uuid-strict (any leftover, not strict uuid mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="Any-version leftover UUIDs are not v4-only.", fetch2="https://json-schema.org/understanding-json-schema/reference/string#uuid", fetch2_ok="Exclusive any-uuid 400 leftover v4.")),
    (p(slug="oas-schema-unevaluated-properties-false", domain="oas-uneval-props-vs-open-additional", success=True, name="ueprop", stack="OpenAPI 3.1 unevaluatedProperties false + Go", field="unevaluatedProperties", old="open additional leftover", new="unevaluatedProperties false", fail_err="400: leftover open additional after unevaluatedProperties-only", plan="unevaluatedProperties-only 400s leftover additionalProperties. Dual-read additional for one release.", residual="validator still additional leftover; drop after validator 5", vs="r4023 leftover-additional-items (unevaluatedProperties vs additional leftover, not items mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/object#unevaluatedproperties", fetch1_ok="unevaluatedProperties false is not leftover additionalProperties.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive unevaluatedProperties 400 leftover additional."),
     p(slug="leftover-open-additional", domain="open-additional-vs-oas-uneval-props", success=False, name="openadd", stack="OpenAPI leftover open additional + Java + TS", field="additionalProperties", old="unevaluatedProperties false", new="open additional leftover only", fail_err="400: leftover unevaluatedProperties after additional-only", plan="Additional-only 400s leftover unevaluatedProperties. Freeze unevaluatedProperties, spec additional leftover.", residual="handoff: keep unevaluatedProperties or force additional leftover", vs="r4023 oas-schema-unevaluated-items (open additional leftover, not items mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="additionalProperties leftover is not unevaluatedProperties.", fetch2="https://json-schema.org/understanding-json-schema/reference/object#unevaluatedproperties", fetch2_ok="Exclusive open additional 400 leftover unevaluatedProperties.")),
    (p(slug="oas-parameter-style-pipe-delimited", domain="oas-pipe-vs-csv-query", success=True, name="qpipe", stack="OpenAPI 3.1 query style=pipeDelimited + Go", field="style", old="csv query leftover", new="query pipeDelimited", fail_err="400: leftover csv query after pipe-only", plan="pipeDelimited-only 400s leftover csv. Dual-read csv for one release.", residual="gateway still csv leftover; drop after gateway 5", vs="wrap form-space-delimited (pipe vs csv leftover, not space cartesian)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch1_ok="style=pipeDelimited is not leftover comma-joined query.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="Exclusive pipeDelimited 400 leftover csv."),
     p(slug="leftover-csv-query", domain="csv-query-vs-oas-pipe", success=False, name="qcsv", stack="OpenAPI leftover csv query + Java + TS", field="style", old="query pipeDelimited", new="csv query leftover only", fail_err="400: leftover pipeDelimited after csv-only", plan="Csv-only 400s leftover pipeDelimited. Freeze pipe, spec csv leftover.", residual="handoff: keep pipeDelimited or force csv leftover", vs="wrap form-space-delimited (csv leftover, not space cartesian)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="CSV leftover query is not pipeDelimited.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch2_ok="Exclusive csv query 400 leftover pipe.")),
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
            if "allowemptyvalue-header" in slug or "omit-header-empty" in slug:
                raise SystemExit(f"banned r4006 plant {slug}")


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
    print(json.dumps({"round": round_n, "idx": idx, "ids": [e1["id"], e2["id"]], "catalog": "r4086"}))


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
