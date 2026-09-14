#!/usr/bin/env python3
"""Twelfth unique OpenAPI-drift ACM catalog after r4166 mill. Fast slug load."""
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
    (p(slug="oas-schema-minimum-exclusive", domain="oas-schema-minimum-exclusive-vs-leftover-inclusive-min", success=True, name="exmin", stack="OpenAPI 3.1 exclusiveMinimum + Go", field="exclusiveMinimum", old="inclusive min leftover", new="exclusiveMinimum", fail_err="400: leftover inclusive min leftover after exclusiveMinimum-only", plan="exclusiveMinimum-only 400s leftover inclusive min leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4070 leftover-inclusive-max (exclusiveMinimum vs inclusive leftover, not exclusiveMaximum)", fetch1="https://json-schema.org/understanding-json-schema/reference/numeric#exclusiveminimum", fetch1_ok="exclusiveMinimum is not leftover inclusive minimum.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive exclusiveMinimum 400 leftover inclusive."),
     p(slug="leftover-inclusive-min", domain="leftover-inclusive-min-vs-oas-schema-minimum-exclusive", success=False, name="incmin", stack="OpenAPI leftover inclusive min + Java + TS", field="exclusiveMinimum", old="exclusiveMinimum", new="inclusive min leftover only", fail_err="400: leftover exclusiveMinimum after inclusive min leftover-only", plan="inclusive min leftover-only 400s leftover exclusiveMinimum. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4070 oas-schema-exclusive-maximum (inclusive leftover, not exclusiveMaximum)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive exclusiveMinimum 400 leftover inclusive.", fetch2="https://json-schema.org/understanding-json-schema/reference/numeric#exclusiveminimum", fetch2_ok="exclusiveMinimum is not leftover inclusive minimum.")),
    (p(slug="oas-parameter-allow-empty-query", domain="oas-parameter-allow-empty-query-vs-leftover-drop-empty-query", success=True, name="qempty", stack="OpenAPI 3.1 allowEmptyValue query + Go", field="allowEmptyValue", old="omit empty query leftover", new="allowEmptyValue true", fail_err="400: leftover omit empty query leftover after allowEmptyValue true-only", plan="allowEmptyValue true-only 400s leftover omit empty query leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r3561 allow-empty-value-query (allowEmptyValue vs omit leftover, not mill reuse)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="allowEmptyValue is not leftover omitted empty queries.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#fixed-fields-9", fetch2_ok="Exclusive allowEmptyValue 400 leftover omit."),
     p(slug="leftover-drop-empty-query", domain="leftover-drop-empty-query-vs-oas-parameter-allow-empty-query", success=False, name="omitq", stack="OpenAPI leftover omit empty query + Java + TS", field="allowEmptyValue", old="allowEmptyValue true", new="omit empty query leftover only", fail_err="400: leftover allowEmptyValue true after omit empty query leftover-only", plan="omit empty query leftover-only 400s leftover allowEmptyValue true. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r3561 allow-empty-value-query (omit leftover, not mill reuse)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#fixed-fields-9", fetch1_ok="Exclusive allowEmptyValue 400 leftover omit.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="allowEmptyValue is not leftover omitted empty queries.")),
    (p(slug="oas-response-header-content-type", domain="oas-response-header-content-type-vs-leftover-sniff-ctype", success=True, name="rctype", stack="OpenAPI 3.1 Content-Type header + Go", field="Content-Type", old="sniff ctype leftover", new="Content-Type header", fail_err="415: leftover sniff ctype leftover after Content-Type header-only", plan="Content-Type header-only 415s leftover sniff ctype leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4023 leftover-retry-body (Content-Type vs sniff leftover, not Retry-After mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#response-object", fetch1_ok="Content-Type is a response header, leftover sniffing is not that.", fetch2="https://datatracker.ietf.org/doc/html/rfc9110#name-content-type", fetch2_ok="Exclusive Content-Type 415 leftover sniff."),
     p(slug="leftover-sniff-ctype", domain="leftover-sniff-ctype-vs-oas-response-header-content-type", success=False, name="sniff", stack="OpenAPI leftover sniff ctype + Java + TS", field="Content-Type", old="Content-Type header", new="sniff ctype leftover only", fail_err="415: leftover Content-Type header after sniff ctype leftover-only", plan="sniff ctype leftover-only 415s leftover Content-Type header. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4023 oas-response-header-retryafter (sniff leftover, not Retry-After mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc9110#name-content-type", fetch1_ok="Exclusive Content-Type 415 leftover sniff.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#response-object", fetch2_ok="Content-Type is a response header, leftover sniffing is not that.")),
    (p(slug="oas-webhook-parameters-query", domain="oas-webhook-parameters-query-vs-leftover-webhook-no-query", success=True, name="whkq", stack="OpenAPI 3.1 webhook query params + Go", field="parameters", old="no webhook query leftover", new="webhook query params", fail_err="400: leftover no webhook query leftover after webhook query params-only", plan="webhook query params-only 400s leftover no webhook query leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4102 leftover-no-webhook-params (webhook query vs none leftover, not params mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#path-item-object", fetch1_ok="Webhook query parameters are not leftover missing queries.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#oasWebhooks", fetch2_ok="Exclusive webhook query 400 leftover none."),
     p(slug="leftover-webhook-no-query", domain="leftover-webhook-no-query-vs-oas-webhook-parameters-query", success=False, name="whknoq", stack="OpenAPI leftover webhook no query + Java + TS", field="parameters", old="webhook query params", new="no webhook query leftover only", fail_err="400: leftover webhook query params after no webhook query leftover-only", plan="no webhook query leftover-only 400s leftover webhook query params. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4102 oas-webhook-parameters (none leftover, not params mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#oasWebhooks", fetch1_ok="Exclusive webhook query 400 leftover none.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#path-item-object", fetch2_ok="Webhook query parameters are not leftover missing queries.")),
    (p(slug="oas-schema-additional-properties-schema", domain="oas-schema-additional-properties-schema-vs-leftover-additional-true", success=True, name="addsch", stack="OpenAPI 3.1 additionalProperties schema + Go", field="additionalProperties", old="additional true leftover", new="additionalProperties schema", fail_err="400: leftover additional true leftover after additionalProperties schema-only", plan="additionalProperties schema-only 400s leftover additional true leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4134 leftover-open-object-keys (additional schema vs true leftover, not closed mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/object#additionalproperties", fetch1_ok="additionalProperties as a schema is not leftover true.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive additional schema 400 leftover true."),
     p(slug="leftover-additional-true", domain="leftover-additional-true-vs-oas-schema-additional-properties-schema", success=False, name="addtrue", stack="OpenAPI leftover additional true + Java + TS", field="additionalProperties", old="additionalProperties schema", new="additional true leftover only", fail_err="400: leftover additionalProperties schema after additional true leftover-only", plan="additional true leftover-only 400s leftover additionalProperties schema. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4134 oas-schema-additional-properties-false (true leftover, not false mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive additional schema 400 leftover true.", fetch2="https://json-schema.org/understanding-json-schema/reference/object#additionalproperties", fetch2_ok="additionalProperties as a schema is not leftover true.")),
    (p(slug="oas-security-http-scheme-basic", domain="oas-security-http-scheme-basic-vs-leftover-http-scheme-digest", success=True, name="httpbas", stack="OpenAPI 3.1 HTTP basic + Go", field="scheme", old="http digest leftover", new="http basic scheme", fail_err="401: leftover http digest leftover after http basic scheme-only", plan="http basic scheme-only 401s leftover http digest leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r3947 leftover-http-basic (basic vs digest leftover, not bearer mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch1_ok="HTTP basic is not leftover digest.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#fixed-fields-21", fetch2_ok="Exclusive basic 401 leftover digest."),
     p(slug="leftover-http-scheme-digest", domain="leftover-http-scheme-digest-vs-oas-security-http-scheme-basic", success=False, name="httpdig", stack="OpenAPI leftover HTTP digest + Java + TS", field="scheme", old="http basic scheme", new="http digest leftover only", fail_err="401: leftover http basic scheme after http digest leftover-only", plan="http digest leftover-only 401s leftover http basic scheme. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r3947 oas-security-http-bearer (digest leftover, not bearer mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#fixed-fields-21", fetch1_ok="Exclusive basic 401 leftover digest.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch2_ok="HTTP basic is not leftover digest.")),
    (p(slug="oas-operation-tags-single", domain="oas-operation-tags-single-vs-leftover-multi-tag-op", success=True, name="optag1", stack="OpenAPI 3.1 single operation tag + Go", field="tags", old="multi tag leftover", new="single operation tag", fail_err="400: leftover multi tag leftover after single operation tag-only", plan="single operation tag-only 400s leftover multi tag leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r3993 leftover-untagged-op (single tag vs multi leftover, not untagged mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch1_ok="A single operation tag is not leftover multi-tag ops.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#tag-object", fetch2_ok="Exclusive single tag 400 leftover multi."),
     p(slug="leftover-multi-tag-op", domain="leftover-multi-tag-op-vs-oas-operation-tags-single", success=False, name="optagn", stack="OpenAPI leftover multi tag op + Java + TS", field="tags", old="single operation tag", new="multi tag leftover only", fail_err="400: leftover single operation tag after multi tag leftover-only", plan="multi tag leftover-only 400s leftover single operation tag. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r3993 oas-operation-tags-required (multi leftover, not required mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#tag-object", fetch1_ok="Exclusive single tag 400 leftover multi.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch2_ok="A single operation tag is not leftover multi-tag ops.")),
    (p(slug="oas-format-uri-relative", domain="oas-format-uri-relative-vs-leftover-absolute-only-uri", success=True, name="urirel", stack="OpenAPI 3.1 format=uri-reference + Go", field="format", old="absolute only leftover", new="uri-reference format", fail_err="400: leftover absolute only leftover after uri-reference format-only", plan="uri-reference format-only 400s leftover absolute only leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r3947 leftover-path-only-url (uri-reference vs absolute leftover, not path mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/string#resource-identifiers", fetch1_ok="format=uri-reference allows relative, leftover absolute-only fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="Exclusive uri-reference 400 leftover absolute."),
     p(slug="leftover-absolute-only-uri", domain="leftover-absolute-only-uri-vs-oas-format-uri-relative", success=False, name="uriabs2", stack="OpenAPI leftover absolute only uri + Java + TS", field="format", old="uri-reference format", new="absolute only leftover only", fail_err="400: leftover uri-reference format after absolute only leftover-only", plan="absolute only leftover-only 400s leftover uri-reference format. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r3947 oas-format-uri-absolute (absolute leftover, not uri mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="Exclusive uri-reference 400 leftover absolute.", fetch2="https://json-schema.org/understanding-json-schema/reference/string#resource-identifiers", fetch2_ok="format=uri-reference allows relative, leftover absolute-only fails closed.")),
    (p(slug="oas-xml-attribute-true", domain="oas-xml-attribute-true-vs-leftover-xml-child-element", success=True, name="xmlat", stack="OpenAPI 3.1 xml.attribute true + Go", field="attribute", old="child element leftover", new="xml attribute true", fail_err="415: leftover child element leftover after xml attribute true-only", plan="xml attribute true-only 415s leftover child element leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r3947 leftover-xml-element (attribute true vs child leftover, not element mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#xml-object", fetch1_ok="xml.attribute true is not leftover child elements.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive xml.attribute 415 leftover child."),
     p(slug="leftover-xml-child-element", domain="leftover-xml-child-element-vs-oas-xml-attribute-true", success=False, name="xmlch", stack="OpenAPI leftover xml child element + Java + TS", field="attribute", old="xml attribute true", new="child element leftover only", fail_err="415: leftover xml attribute true after child element leftover-only", plan="child element leftover-only 415s leftover xml attribute true. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r3947 oas-xml-attribute (child leftover, not attribute mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive xml.attribute 415 leftover child.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#xml-object", fetch2_ok="xml.attribute true is not leftover child elements.")),
    (p(slug="oas-link-parameters-const", domain="oas-link-parameters-const-vs-leftover-runtime-only-link", success=True, name="lnkcst", stack="OpenAPI 3.1 link const parameters + Go", field="parameters", old="runtime only leftover", new="link const parameters", fail_err="400: leftover runtime only leftover after link const parameters-only", plan="link const parameters-only 400s leftover runtime only leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4086 leftover-static-link-params (const vs runtime leftover, not static mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#link-object", fetch1_ok="Constant link parameters are not leftover runtime-only.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#runtime-expressions", fetch2_ok="Exclusive const link params 400 leftover runtime."),
     p(slug="leftover-runtime-only-link", domain="leftover-runtime-only-link-vs-oas-link-parameters-const", success=False, name="lnkrt2", stack="OpenAPI leftover runtime only link + Java + TS", field="parameters", old="link const parameters", new="runtime only leftover only", fail_err="400: leftover link const parameters after runtime only leftover-only", plan="runtime only leftover-only 400s leftover link const parameters. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4086 oas-link-parameters-runtime (runtime leftover, not runtime mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#runtime-expressions", fetch1_ok="Exclusive const link params 400 leftover runtime.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#link-object", fetch2_ok="Constant link parameters are not leftover runtime-only.")),
    (p(slug="oas-schema-type-boolean", domain="oas-schema-type-boolean-vs-leftover-string-bool", success=True, name="typbool", stack="OpenAPI 3.1 type=boolean + Go", field="type", old="string bool leftover", new="type boolean", fail_err="400: leftover string bool leftover after type boolean-only", plan="type boolean-only 400s leftover string bool leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4150 leftover-number-only (boolean vs string leftover, not integer mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/boolean", fetch1_ok="type=boolean is not leftover string true/false.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive boolean 400 leftover string bool."),
     p(slug="leftover-string-bool", domain="leftover-string-bool-vs-oas-schema-type-boolean", success=False, name="strbool", stack="OpenAPI leftover string bool + Java + TS", field="type", old="type boolean", new="string bool leftover only", fail_err="400: leftover type boolean after string bool leftover-only", plan="string bool leftover-only 400s leftover type boolean. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4150 oas-schema-type-integer (string leftover, not integer mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive boolean 400 leftover string bool.", fetch2="https://json-schema.org/understanding-json-schema/reference/boolean", fetch2_ok="type=boolean is not leftover string true/false.")),
    (p(slug="oas-components-headers-reuse", domain="oas-components-headers-reuse-vs-leftover-inline-resp-headers", success=True, name="chdr", stack="OpenAPI 3.1 components.headers + Go", field="headers", old="inline resp headers leftover", new="components headers", fail_err="400: leftover inline resp headers leftover after components headers-only", plan="components headers-only 400s leftover inline resp headers leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r3963 leftover-inline-headers (components.headers vs inline leftover, not mill reuse)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#components-object", fetch1_ok="components.headers reuse Header Objects.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch2_ok="Exclusive components.headers 400 leftover inline."),
     p(slug="leftover-inline-resp-headers", domain="leftover-inline-resp-headers-vs-oas-components-headers-reuse", success=False, name="ihdr", stack="OpenAPI leftover inline resp headers + Java + TS", field="headers", old="components headers", new="inline resp headers leftover only", fail_err="400: leftover components headers after inline resp headers leftover-only", plan="inline resp headers leftover-only 400s leftover components headers. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r3963 oas-components-headers (inline leftover, not mill reuse)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch1_ok="Exclusive components.headers 400 leftover inline.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#components-object", fetch2_ok="components.headers reuse Header Objects.")),
    (p(slug="oas-parameter-style-matrix-path", domain="oas-parameter-style-matrix-path-vs-leftover-path-slash-join", success=True, name="pmat", stack="OpenAPI 3.1 path style=matrix + Go", field="style", old="slash join leftover", new="path matrix style", fail_err="400: leftover slash join leftover after path matrix style-only", plan="path matrix style-only 400s leftover slash join leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r3561 style-matrix-path (matrix vs slash leftover, not mill reuse)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch1_ok="style=matrix is not leftover slash-joined path params.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="Exclusive matrix 400 leftover slash."),
     p(slug="leftover-path-slash-join", domain="leftover-path-slash-join-vs-oas-parameter-style-matrix-path", success=False, name="pslash", stack="OpenAPI leftover path slash join + Java + TS", field="style", old="path matrix style", new="slash join leftover only", fail_err="400: leftover path matrix style after slash join leftover-only", plan="slash join leftover-only 400s leftover path matrix style. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r3561 style-matrix-path (slash leftover, not mill reuse)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="Exclusive matrix 400 leftover slash.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch2_ok="style=matrix is not leftover slash-joined path params.")),
    (p(slug="oas-info-version-required", domain="oas-info-version-required-vs-leftover-missing-info-version", success=True, name="verreq", stack="OpenAPI 3.1 info.version required + Go", field="version", old="missing info version leftover", new="info version required", fail_err="400: leftover missing info version leftover after info version required-only", plan="info version required-only 400s leftover missing info version leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r3963 leftover-unversioned (required version vs missing leftover, not semver mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#info-object", fetch1_ok="info.version is required, leftover missing fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#fixed-fields", fetch2_ok="Exclusive info.version 400 leftover missing."),
     p(slug="leftover-missing-info-version", domain="leftover-missing-info-version-vs-oas-info-version-required", success=False, name="nover", stack="OpenAPI leftover missing info version + Java + TS", field="version", old="info version required", new="missing info version leftover only", fail_err="400: leftover info version required after missing info version leftover-only", plan="missing info version leftover-only 400s leftover info version required. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r3963 oas-info-version-semver (missing leftover, not semver mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#fixed-fields", fetch1_ok="Exclusive info.version 400 leftover missing.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#info-object", fetch2_ok="info.version is required, leftover missing fails closed.")),
    (p(slug="oas-callback-expression-body", domain="oas-callback-expression-body-vs-leftover-callback-header-expr", success=True, name="cbbody", stack="OpenAPI 3.1 callback body expression + Go", field="callbacks", old="header expr leftover", new="callback body expression", fail_err="400: leftover header expr leftover after callback body expression-only", plan="callback body expression-only 400s leftover header expr leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4070 leftover-static-callback-url (body expr vs header leftover, not static mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#runtime-expressions", fetch1_ok="$request.body expressions are not leftover header expressions.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#callback-object", fetch2_ok="Exclusive body expr 400 leftover header."),
     p(slug="leftover-callback-header-expr", domain="leftover-callback-header-expr-vs-oas-callback-expression-body", success=False, name="cbhdr", stack="OpenAPI leftover callback header expr + Java + TS", field="callbacks", old="callback body expression", new="header expr leftover only", fail_err="400: leftover callback body expression after header expr leftover-only", plan="header expr leftover-only 400s leftover callback body expression. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4070 oas-callback-expression-runtime (header leftover, not runtime mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#callback-object", fetch1_ok="Exclusive body expr 400 leftover header.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#runtime-expressions", fetch2_ok="$request.body expressions are not leftover header expressions.")),
    (p(slug="oas-schema-format-double", domain="oas-schema-format-double-vs-leftover-float32-only", success=True, name="fmtdbl", stack="OpenAPI 3.1 format=double + Go", field="format", old="float32 leftover", new="format double", fail_err="400: leftover float32 leftover after format double-only", plan="format double-only 400s leftover float32 leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r3947 leftover-unbounded-int (double vs float32 leftover, not int mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="format=double is IEEE 754 binary64, leftover float32 fails closed.", fetch2="https://json-schema.org/understanding-json-schema/reference/numeric", fetch2_ok="Exclusive double 400 leftover float32."),
     p(slug="leftover-float32-only", domain="leftover-float32-only-vs-oas-schema-format-double", success=False, name="flt32", stack="OpenAPI leftover float32 only + Java + TS", field="format", old="format double", new="float32 leftover only", fail_err="400: leftover format double after float32 leftover-only", plan="float32 leftover-only 400s leftover format double. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r3947 oas-format-int32 (float32 leftover, not int mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/numeric", fetch1_ok="Exclusive double 400 leftover float32.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="format=double is IEEE 754 binary64, leftover float32 fails closed.")),
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
    print(json.dumps({"round": round_n, "idx": idx, "ids": [e1["id"], e2["id"]], "catalog": "r4182"}))


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
