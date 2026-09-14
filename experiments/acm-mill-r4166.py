#!/usr/bin/env python3
"""Eleventh unique OpenAPI-drift ACM catalog after r4150 mill. Fast slug load."""
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
    (p(slug="oas-schema-max-length", domain="oas-schema-max-length-vs-leftover-no-max-length", success=True, name="maxlen", stack="OpenAPI 3.1 maxLength + Go", field="maxLength", old="unbounded string leftover", new="string maxLength", fail_err="400: leftover unbounded string leftover after string maxLength-only", plan="string maxLength-only 400s leftover unbounded string leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r3947 leftover-unbounded-int (maxLength vs unbounded leftover, not int mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/string#length", fetch1_ok="maxLength caps strings.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive maxLength 400 leftover unbounded."),
     p(slug="leftover-no-max-length", domain="leftover-no-max-length-vs-oas-schema-max-length", success=False, name="unbstr", stack="OpenAPI leftover unbounded string + Java + TS", field="maxLength", old="string maxLength", new="unbounded string leftover only", fail_err="400: leftover string maxLength after unbounded string leftover-only", plan="unbounded string leftover-only 400s leftover string maxLength. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r3947 oas-format-int32 (unbounded leftover, not int mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive maxLength 400 leftover unbounded.", fetch2="https://json-schema.org/understanding-json-schema/reference/string#length", fetch2_ok="maxLength caps strings.")),
    (p(slug="oas-schema-min-length", domain="oas-schema-min-length-vs-leftover-zero-length-str", success=True, name="minlen", stack="OpenAPI 3.1 minLength + Go", field="minLength", old="empty string leftover", new="string minLength", fail_err="400: leftover empty string leftover after string minLength-only", plan="string minLength-only 400s leftover empty string leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4038 leftover-empty-object-body (minLength vs empty leftover, not empty object)", fetch1="https://json-schema.org/understanding-json-schema/reference/string#length", fetch1_ok="minLength rejects leftover empty strings.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive minLength 400 leftover empty."),
     p(slug="leftover-zero-length-str", domain="leftover-zero-length-str-vs-oas-schema-min-length", success=False, name="empstr", stack="OpenAPI leftover empty string + Java + TS", field="minLength", old="string minLength", new="empty string leftover only", fail_err="400: leftover string minLength after empty string leftover-only", plan="empty string leftover-only 400s leftover string minLength. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4038 oas-schema-min-properties (empty leftover, not minProperties)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive minLength 400 leftover empty.", fetch2="https://json-schema.org/understanding-json-schema/reference/string#length", fetch2_ok="minLength rejects leftover empty strings.")),
    (p(slug="oas-parameter-required-query", domain="oas-parameter-required-query-vs-leftover-optional-query", success=True, name="qreq", stack="OpenAPI 3.1 query required + Go", field="required", old="optional query leftover", new="query required", fail_err="400: leftover optional query leftover after query required-only", plan="query required-only 400s leftover optional query leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4134 leftover-always-required-hdr (required query vs optional leftover, not header mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="required true on query params is not leftover optional.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#fixed-fields-9", fetch2_ok="Exclusive required query 400 leftover optional."),
     p(slug="leftover-optional-query", domain="leftover-optional-query-vs-oas-parameter-required-query", success=False, name="qopt", stack="OpenAPI leftover optional query + Java + TS", field="required", old="query required", new="optional query leftover only", fail_err="400: leftover query required after optional query leftover-only", plan="optional query leftover-only 400s leftover query required. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4134 oas-header-required-false (optional leftover, not header mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#fixed-fields-9", fetch1_ok="Exclusive required query 400 leftover optional.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="required true on query params is not leftover optional.")),
    (p(slug="oas-response-content-json", domain="oas-response-content-json-vs-leftover-empty-200-body", success=True, name="rjson", stack="OpenAPI 3.1 200 JSON content + Go", field="content", old="empty 200 leftover", new="json 200 content", fail_err="400: leftover empty 200 leftover after json 200 content-only", plan="json 200 content-only 400s leftover empty 200 leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4150 leftover-any-status (json 200 vs empty leftover, not any-status mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#response-object", fetch1_ok="200 JSON content is not leftover empty bodies.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch2_ok="Exclusive json 200 400 leftover empty."),
     p(slug="leftover-empty-200-body", domain="leftover-empty-200-body-vs-oas-response-content-json", success=False, name="empty200", stack="OpenAPI leftover empty 200 + Java + TS", field="content", old="json 200 content", new="empty 200 leftover only", fail_err="400: leftover json 200 content after empty 200 leftover-only", plan="empty 200 leftover-only 400s leftover json 200 content. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4150 oas-response-200-required (empty leftover, not 200 mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch1_ok="Exclusive json 200 400 leftover empty.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#response-object", fetch2_ok="200 JSON content is not leftover empty bodies.")),
    (p(slug="oas-security-required-global", domain="oas-security-required-global-vs-leftover-unsecured", success=True, name="secreq", stack="OpenAPI 3.1 global security required + Go", field="security", old="unsecured leftover", new="global security required", fail_err="401: leftover unsecured leftover after global security required-only", plan="global security required-only 401s leftover unsecured leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4038 leftover-global-security-only (required global vs unsecured leftover, not override mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#security-requirement-object", fetch1_ok="Root security required is not leftover unsecured.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#oasSecurity", fetch2_ok="Exclusive global security 401 leftover unsecured."),
     p(slug="leftover-unsecured", domain="leftover-unsecured-vs-oas-security-required-global", success=False, name="unsec", stack="OpenAPI leftover unsecured + Java + TS", field="security", old="global security required", new="unsecured leftover only", fail_err="401: leftover global security required after unsecured leftover-only", plan="unsecured leftover-only 401s leftover global security required. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4038 oas-operation-security-override (unsecured leftover, not override mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#oasSecurity", fetch1_ok="Exclusive global security 401 leftover unsecured.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#security-requirement-object", fetch2_ok="Root security required is not leftover unsecured.")),
    (p(slug="oas-operation-deprecated-true", domain="oas-operation-deprecated-true-vs-leftover-undeprecated-op", success=True, name="opdep", stack="OpenAPI 3.1 operation deprecated + Go", field="deprecated", old="undeprecated leftover", new="operation deprecated true", fail_err="400: leftover undeprecated leftover after operation deprecated true-only", plan="operation deprecated true-only 400s leftover undeprecated leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4118 leftover-live-deprecated-op (deprecated true vs undeprecated leftover, not gone mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch1_ok="deprecated true marks the op, leftover live fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#fixed-fields-8", fetch2_ok="Exclusive deprecated 400 leftover live."),
     p(slug="leftover-undeprecated-op", domain="leftover-undeprecated-op-vs-oas-operation-deprecated-true", success=False, name="liveop", stack="OpenAPI leftover undeprecated op + Java + TS", field="deprecated", old="operation deprecated true", new="undeprecated leftover only", fail_err="400: leftover operation deprecated true after undeprecated leftover-only", plan="undeprecated leftover-only 400s leftover operation deprecated true. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4118 oas-deprecated-op-gone (undeprecated leftover, not gone mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#fixed-fields-8", fetch1_ok="Exclusive deprecated 400 leftover live.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch2_ok="deprecated true marks the op, leftover live fails closed.")),
    (p(slug="oas-schema-nullable-union", domain="oas-schema-nullable-union-vs-leftover-omit-null-type", success=True, name="nunion", stack="OpenAPI 3.1 null union + Go", field="type", old="omit null leftover", new="null union type", fail_err="400: leftover omit null leftover after null union type-only", plan="null union type-only 400s leftover omit null leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4007 leftover-omit-null-default (null union vs omit leftover, not default mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/null", fetch1_ok="type arrays may include null, leftover omit-null fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive null union 400 leftover omit."),
     p(slug="leftover-omit-null-type", domain="leftover-omit-null-type-vs-oas-schema-nullable-union", success=False, name="omitn", stack="OpenAPI leftover omit null type + Java + TS", field="type", old="null union type", new="omit null leftover only", fail_err="400: leftover null union type after omit null leftover-only", plan="omit null leftover-only 400s leftover null union type. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4007 oas-schema-default-null (omit leftover, not default mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive null union 400 leftover omit.", fetch2="https://json-schema.org/understanding-json-schema/reference/null", fetch2_ok="type arrays may include null, leftover omit-null fails closed.")),
    (p(slug="oas-format-rfc3339-datetime", domain="oas-format-rfc3339-datetime-vs-leftover-unix-seconds", success=True, name="fmtts", stack="OpenAPI 3.1 format=date-time + Go", field="format", old="unix seconds leftover", new="format date-time", fail_err="400: leftover unix seconds leftover after format date-time-only", plan="format date-time-only 400s leftover unix seconds leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r3561 unix-epoch-millis (date-time vs unix leftover, not millis mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/string#dates-and-times", fetch1_ok="format=date-time is RFC 3339, leftover unix seconds fail closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="Exclusive date-time 400 leftover unix."),
     p(slug="leftover-unix-seconds", domain="leftover-unix-seconds-vs-oas-format-rfc3339-datetime", success=False, name="unixs", stack="OpenAPI leftover unix seconds + Java + TS", field="format", old="format date-time", new="unix seconds leftover only", fail_err="400: leftover format date-time after unix seconds leftover-only", plan="unix seconds leftover-only 400s leftover format date-time. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r3561 unix-epoch-millis (unix leftover, not millis mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="Exclusive date-time 400 leftover unix.", fetch2="https://json-schema.org/understanding-json-schema/reference/string#dates-and-times", fetch2_ok="format=date-time is RFC 3339, leftover unix seconds fail closed.")),
    (p(slug="oas-content-application-xml", domain="oas-content-application-xml-vs-leftover-json-xml-mix", success=True, name="appxml", stack="OpenAPI 3.1 application/xml + Go", field="content", old="json xml mix leftover", new="application xml", fail_err="415: leftover json xml mix leftover after application xml-only", plan="application xml-only 415s leftover json xml mix leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4054 leftover-element-prefix (application/xml vs json mix leftover, not prefix mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch1_ok="application/xml is not leftover JSON-as-XML.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#xml-object", fetch2_ok="Exclusive application/xml 415 leftover mix."),
     p(slug="leftover-json-xml-mix", domain="leftover-json-xml-mix-vs-oas-content-application-xml", success=False, name="jxml", stack="OpenAPI leftover json xml mix + Java + TS", field="content", old="application xml", new="json xml mix leftover only", fail_err="415: leftover application xml after json xml mix leftover-only", plan="json xml mix leftover-only 415s leftover application xml. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4054 oas-xml-attribute-prefix (json mix leftover, not prefix mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#xml-object", fetch1_ok="Exclusive application/xml 415 leftover mix.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch2_ok="application/xml is not leftover JSON-as-XML.")),
    (p(slug="oas-header-schema-string", domain="oas-header-schema-string-vs-leftover-untyped-header", success=True, name="hdrstr", stack="OpenAPI 3.1 header schema string + Go", field="schema", old="untyped header leftover", new="header string schema", fail_err="400: leftover untyped header leftover after header string schema-only", plan="header string schema-only 400s leftover untyped header leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4054 leftover-csv-header (string schema vs untyped leftover, not csv mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch1_ok="Header schema type=string is not leftover untyped headers.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive header string 400 leftover untyped."),
     p(slug="leftover-untyped-header", domain="leftover-untyped-header-vs-oas-header-schema-string", success=False, name="uthdr", stack="OpenAPI leftover untyped header + Java + TS", field="schema", old="header string schema", new="untyped header leftover only", fail_err="400: leftover header string schema after untyped header leftover-only", plan="untyped header leftover-only 400s leftover header string schema. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4054 oas-header-schema-array (untyped leftover, not array mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive header string 400 leftover untyped.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch2_ok="Header schema type=string is not leftover untyped headers.")),
    (p(slug="oas-callback-post-only", domain="oas-callback-post-only-vs-leftover-callback-get", success=True, name="cbpost", stack="OpenAPI 3.1 callback POST + Go", field="post", old="callback GET leftover", new="callback POST only", fail_err="405: leftover callback GET leftover after callback POST only-only", plan="callback POST only-only 405s leftover callback GET leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r3947 leftover-notify-post (POST-only vs GET leftover, not notify mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#callback-object", fetch1_ok="Callback Path Items may POST-only, leftover GET is not that.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#path-item-object", fetch2_ok="Exclusive callback POST 405 leftover GET."),
     p(slug="leftover-callback-get", domain="leftover-callback-get-vs-oas-callback-post-only", success=False, name="cbget", stack="OpenAPI leftover callback GET + Java + TS", field="post", old="callback POST only", new="callback GET leftover only", fail_err="405: leftover callback POST only after callback GET leftover-only", plan="callback GET leftover-only 405s leftover callback POST only. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r3947 oas-callback-pathitem (GET leftover, not Path Item mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#path-item-object", fetch1_ok="Exclusive callback POST 405 leftover GET.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#callback-object", fetch2_ok="Callback Path Items may POST-only, leftover GET is not that.")),
    (p(slug="oas-info-title-nonempty", domain="oas-info-title-nonempty-vs-leftover-blank-title", success=True, name="title", stack="OpenAPI 3.1 info.title nonempty + Go", field="title", old="blank title leftover", new="nonempty title", fail_err="400: leftover blank title leftover after nonempty title-only", plan="nonempty title-only 400s leftover blank title leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r3931 leftover-missing-title (nonempty vs blank leftover, not missing mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#info-object", fetch1_ok="info.title must be nonempty, leftover blank fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#fixed-fields", fetch2_ok="Exclusive nonempty title 400 leftover blank."),
     p(slug="leftover-blank-title", domain="leftover-blank-title-vs-oas-info-title-nonempty", success=False, name="blankt", stack="OpenAPI leftover blank title + Java + TS", field="title", old="nonempty title", new="blank title leftover only", fail_err="400: leftover nonempty title after blank title leftover-only", plan="blank title leftover-only 400s leftover nonempty title. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r3931 oas-info-title-required (blank leftover, not required mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#fixed-fields", fetch1_ok="Exclusive nonempty title 400 leftover blank.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#info-object", fetch2_ok="info.title must be nonempty, leftover blank fails closed.")),
    (p(slug="oas-schema-pattern-properties-x", domain="oas-schema-pattern-properties-x-vs-leftover-free-props", success=True, name="pprop", stack="OpenAPI 3.1 patternProperties + Go", field="patternProperties", old="free props leftover", new="patternProperties x-", fail_err="400: leftover free props leftover after patternProperties x--only", plan="patternProperties x--only 400s leftover free props leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r3561 pattern-properties-x-ext (patternProperties vs free leftover, not mill reuse)", fetch1="https://json-schema.org/understanding-json-schema/reference/object#patternProperties", fetch1_ok="patternProperties constrains leftover free keys.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive patternProperties 400 leftover free."),
     p(slug="leftover-free-props", domain="leftover-free-props-vs-oas-schema-pattern-properties-x", success=False, name="freepr", stack="OpenAPI leftover free props + Java + TS", field="patternProperties", old="patternProperties x-", new="free props leftover only", fail_err="400: leftover patternProperties x- after free props leftover-only", plan="free props leftover-only 400s leftover patternProperties x-. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r3561 pattern-properties-x-ext (free leftover, not mill reuse)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive patternProperties 400 leftover free.", fetch2="https://json-schema.org/understanding-json-schema/reference/object#patternProperties", fetch2_ok="patternProperties constrains leftover free keys.")),
    (p(slug="oas-servers-variable-enum", domain="oas-servers-variable-enum-vs-leftover-free-server-var", success=True, name="svenu2", stack="OpenAPI 3.1 server variable enum + Go", field="enum", old="free server var leftover", new="server variable enum", fail_err="400: leftover free server var leftover after server variable enum-only", plan="server variable enum-only 400s leftover free server var leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4118 leftover-pattern-only-var (enum vs free leftover, not pattern mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#server-variable-object", fetch1_ok="enum on server vars is not leftover free hosts.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#server-object", fetch2_ok="Exclusive server enum 400 leftover free."),
     p(slug="leftover-free-server-var", domain="leftover-free-server-var-vs-oas-servers-variable-enum", success=False, name="freevar", stack="OpenAPI leftover free server var + Java + TS", field="enum", old="server variable enum", new="free server var leftover only", fail_err="400: leftover server variable enum after free server var leftover-only", plan="free server var leftover-only 400s leftover server variable enum. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4118 oas-servers-variables-enum-only (free leftover, not enum-only mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#server-object", fetch1_ok="Exclusive server enum 400 leftover free.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#server-variable-object", fetch2_ok="enum on server vars is not leftover free hosts.")),
    (p(slug="oas-discriminator-property-name", domain="oas-discriminator-property-name-vs-leftover-type-key", success=True, name="discname", stack="OpenAPI 3.1 discriminator propertyName + Go", field="propertyName", old="type key leftover", new="discriminator propertyName", fail_err="400: leftover type key leftover after discriminator propertyName-only", plan="discriminator propertyName-only 400s leftover type key leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4038 leftover-optional-disc (propertyName vs type-key leftover, not optional mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#discriminator-object", fetch1_ok="propertyName is not leftover generic type keys.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive propertyName 400 leftover type-key."),
     p(slug="leftover-type-key", domain="leftover-type-key-vs-oas-discriminator-property-name", success=False, name="typek", stack="OpenAPI leftover type key + Java + TS", field="propertyName", old="discriminator propertyName", new="type key leftover only", fail_err="400: leftover discriminator propertyName after type key leftover-only", plan="type key leftover-only 400s leftover discriminator propertyName. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4038 oas-discriminator-property-required (type-key leftover, not required mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive propertyName 400 leftover type-key.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#discriminator-object", fetch2_ok="propertyName is not leftover generic type keys.")),
    (p(slug="oas-encoding-content-type", domain="oas-encoding-content-type-vs-leftover-part-octet", success=True, name="enctype", stack="OpenAPI 3.1 encoding.contentType + Go", field="contentType", old="part octet leftover", new="encoding contentType", fail_err="415: leftover part octet leftover after encoding contentType-only", plan="encoding contentType-only 415s leftover part octet leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r3867 leftover-prop-mediatype (encoding.contentType vs octet leftover, not property mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#encoding-object", fetch1_ok="encoding.contentType is not leftover octet-stream parts.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch2_ok="Exclusive encoding contentType 415 leftover octet."),
     p(slug="leftover-part-octet", domain="leftover-part-octet-vs-oas-encoding-content-type", success=False, name="octet", stack="OpenAPI leftover part octet + Java + TS", field="contentType", old="encoding contentType", new="part octet leftover only", fail_err="415: leftover encoding contentType after part octet leftover-only", plan="part octet leftover-only 415s leftover encoding contentType. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r3867 oas-encoding-ctype (octet leftover, not mill reuse)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch1_ok="Exclusive encoding contentType 415 leftover octet.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#encoding-object", fetch2_ok="encoding.contentType is not leftover octet-stream parts.")),
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
    print(json.dumps({"round": round_n, "idx": idx, "ids": [e1["id"], e2["id"]], "catalog": "r4166"}))


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
