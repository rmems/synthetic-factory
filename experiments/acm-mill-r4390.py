#!/usr/bin/env python3
"""Unique OpenAPI-drift ACM catalog r4390. Fast slug load."""
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
    (p(slug="oas-prefixitems-plus-items", domain="oas-prefixitems-plus-items-vs-leftover-tuple-as-open-list", success=True, name="ba676a", stack="OpenAPI 3.1 prefixItems + Go", field="prefixItems", old="open list leftover", new="prefixItems plus items", fail_err="400: leftover open list leftover after prefixItems plus items-only", plan="prefixItems plus items-only 400s leftover open list leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (prefixItems plus items vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/array#tuple-validation", fetch1_ok="prefixItems plus items closes leftover open lists.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive prefixItems+items 400 leftover open list."),
     p(slug="leftover-tuple-as-open-list", domain="leftover-tuple-as-open-list-vs-oas-prefixitems-plus-items", success=False, name="ebefe0", stack="OpenAPI leftover prefixItems + Java + TS", field="prefixItems", old="prefixItems plus items", new="open list leftover only", fail_err="400: leftover prefixItems plus items after open list leftover-only", plan="open list leftover-only 400s leftover prefixItems plus items. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (open list leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive prefixItems+items 400 leftover open list.", fetch2="https://json-schema.org/understanding-json-schema/reference/array#tuple-validation", fetch2_ok="prefixItems plus items closes leftover open lists.")),
    (p(slug="oas-property-names-pattern", domain="oas-property-names-pattern-vs-leftover-any-key-charset", success=True, name="2e0e1a", stack="OpenAPI 3.1 propertyNames + Go", field="propertyNames", old="any key charset leftover", new="propertyNames pattern", fail_err="400: leftover any key charset leftover after propertyNames pattern-only", plan="propertyNames pattern-only 400s leftover any key charset leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (propertyNames pattern vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/object#propertynames", fetch1_ok="propertyNames.pattern constrains keys, leftover any-charset fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive propertyNames pattern 400 leftover any charset."),
     p(slug="leftover-any-key-charset", domain="leftover-any-key-charset-vs-oas-property-names-pattern", success=False, name="06b125", stack="OpenAPI leftover propertyNames + Java + TS", field="propertyNames", old="propertyNames pattern", new="any key charset leftover only", fail_err="400: leftover propertyNames pattern after any key charset leftover-only", plan="any key charset leftover-only 400s leftover propertyNames pattern. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (any key charset leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive propertyNames pattern 400 leftover any charset.", fetch2="https://json-schema.org/understanding-json-schema/reference/object#propertynames", fetch2_ok="propertyNames.pattern constrains keys, leftover any-charset fails closed.")),
    (p(slug="oas-default-const-agree", domain="oas-default-const-agree-vs-leftover-default-vs-const", success=True, name="ae7191", stack="OpenAPI 3.1 default + Go", field="default", old="default vs const leftover", new="default agrees const", fail_err="400: leftover default vs const leftover after default agrees const-only", plan="default agrees const-only 400s leftover default vs const leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (default agrees const vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/generic#const", fetch1_ok="default must agree with const, leftover mismatch fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive default=const 400 leftover mismatch."),
     p(slug="leftover-default-vs-const", domain="leftover-default-vs-const-vs-oas-default-const-agree", success=False, name="0e51dc", stack="OpenAPI leftover default + Java + TS", field="default", old="default agrees const", new="default vs const leftover only", fail_err="400: leftover default agrees const after default vs const leftover-only", plan="default vs const leftover-only 400s leftover default agrees const. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (default vs const leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive default=const 400 leftover mismatch.", fetch2="https://json-schema.org/understanding-json-schema/reference/generic#const", fetch2_ok="default must agree with const, leftover mismatch fails closed.")),
    (p(slug="oas-schema-else-branch", domain="oas-schema-else-branch-vs-leftover-if-then-no-else", success=True, name="e4c8ee", stack="OpenAPI 3.1 else + Go", field="else", old="if-then no else leftover", new="if then else", fail_err="400: leftover if-then no else leftover after if then else-only", plan="if then else-only 400s leftover if-then no else leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (if then else vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/conditionals", fetch1_ok="else is required with if/then here, leftover missing else fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive else 400 leftover no else."),
     p(slug="leftover-if-then-no-else", domain="leftover-if-then-no-else-vs-oas-schema-else-branch", success=False, name="e97de8", stack="OpenAPI leftover else + Java + TS", field="else", old="if then else", new="if-then no else leftover only", fail_err="400: leftover if then else after if-then no else leftover-only", plan="if-then no else leftover-only 400s leftover if then else. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (if-then no else leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive else 400 leftover no else.", fetch2="https://json-schema.org/understanding-json-schema/reference/conditionals", fetch2_ok="else is required with if/then here, leftover missing else fails closed.")),
    (p(slug="oas-webhook-header-param", domain="oas-webhook-header-param-vs-leftover-webhook-query-only", success=True, name="4440a9", stack="OpenAPI 3.1 parameters + Go", field="parameters", old="webhook query leftover", new="webhook header param", fail_err="400: leftover webhook query leftover after webhook header param-only", plan="webhook header param-only 400s leftover webhook query leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (webhook header param vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#oasWebhooks", fetch1_ok="Webhook header params are not leftover query-only.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="Exclusive webhook header 400 leftover query."),
     p(slug="leftover-webhook-query-only", domain="leftover-webhook-query-only-vs-oas-webhook-header-param", success=False, name="dc658c", stack="OpenAPI leftover parameters + Java + TS", field="parameters", old="webhook header param", new="webhook query leftover only", fail_err="400: leftover webhook header param after webhook query leftover-only", plan="webhook query leftover-only 400s leftover webhook header param. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (webhook query leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="Exclusive webhook header 400 leftover query.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#oasWebhooks", fetch2_ok="Webhook header params are not leftover query-only.")),
    (p(slug="oas-callback-put-op", domain="oas-callback-put-op-vs-leftover-callback-post-only", success=True, name="cad40c", stack="OpenAPI 3.1 put + Go", field="put", old="callback POST leftover", new="callback PUT", fail_err="400: leftover callback POST leftover after callback PUT-only", plan="callback PUT-only 400s leftover callback POST leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (callback PUT vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#callback-object", fetch1_ok="Callback PUT is distinct, leftover POST-only fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#path-item-object", fetch2_ok="Exclusive callback PUT 400 leftover POST."),
     p(slug="leftover-callback-post-only", domain="leftover-callback-post-only-vs-oas-callback-put-op", success=False, name="3afe03", stack="OpenAPI leftover put + Java + TS", field="put", old="callback PUT", new="callback POST leftover only", fail_err="400: leftover callback PUT after callback POST leftover-only", plan="callback POST leftover-only 400s leftover callback PUT. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (callback POST leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#path-item-object", fetch1_ok="Exclusive callback PUT 400 leftover POST.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#callback-object", fetch2_ok="Callback PUT is distinct, leftover POST-only fails closed.")),
    (p(slug="oas-link-requestbody-expr", domain="oas-link-requestbody-expr-vs-leftover-link-no-request-body", success=True, name="24e308", stack="OpenAPI 3.1 requestBody + Go", field="requestBody", old="link no body leftover", new="link requestBody expr", fail_err="400: leftover link no body leftover after link requestBody expr-only", plan="link requestBody expr-only 400s leftover link no body leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (link requestBody expr vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#link-object", fetch1_ok="link.requestBody is a runtime expression, leftover missing fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#runtime-expressions", fetch2_ok="Exclusive link body 400 leftover none."),
     p(slug="leftover-link-no-request-body", domain="leftover-link-no-request-body-vs-oas-link-requestbody-expr", success=False, name="aaf545", stack="OpenAPI leftover requestBody + Java + TS", field="requestBody", old="link requestBody expr", new="link no body leftover only", fail_err="400: leftover link requestBody expr after link no body leftover-only", plan="link no body leftover-only 400s leftover link requestBody expr. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (link no body leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#runtime-expressions", fetch1_ok="Exclusive link body 400 leftover none.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#link-object", fetch2_ok="link.requestBody is a runtime expression, leftover missing fails closed.")),
    (p(slug="oas-header-required-response", domain="oas-header-required-response-vs-leftover-resp-header-optional", success=True, name="b6e8dc", stack="OpenAPI 3.1 required + Go", field="required", old="optional resp header leftover", new="response header required", fail_err="400: leftover optional resp header leftover after response header required-only", plan="response header required-only 400s leftover optional resp header leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (response header required vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch1_ok="required response headers cannot be leftover optional.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#response-object", fetch2_ok="Exclusive header required 400 leftover optional."),
     p(slug="leftover-resp-header-optional", domain="leftover-resp-header-optional-vs-oas-header-required-response", success=False, name="94c8e9", stack="OpenAPI leftover required + Java + TS", field="required", old="response header required", new="optional resp header leftover only", fail_err="400: leftover response header required after optional resp header leftover-only", plan="optional resp header leftover-only 400s leftover response header required. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (optional resp header leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#response-object", fetch1_ok="Exclusive header required 400 leftover optional.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch2_ok="required response headers cannot be leftover optional.")),
    (p(slug="oas-encoding-style-form-part", domain="oas-encoding-style-form-part-vs-leftover-part-as-json-blob", success=True, name="32bd68", stack="OpenAPI 3.1 style + Go", field="style", old="json part leftover", new="encoding style form", fail_err="415: leftover json part leftover after encoding style form-only", plan="encoding style form-only 415s leftover json part leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (encoding style form vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#encoding-object", fetch1_ok="encoding.style form is not leftover JSON parts.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch2_ok="Exclusive encoding form 415 leftover json part."),
     p(slug="leftover-part-as-json-blob", domain="leftover-part-as-json-blob-vs-oas-encoding-style-form-part", success=False, name="81a39d", stack="OpenAPI leftover style + Java + TS", field="style", old="encoding style form", new="json part leftover only", fail_err="415: leftover encoding style form after json part leftover-only", plan="json part leftover-only 415s leftover encoding style form. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (json part leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch1_ok="Exclusive encoding form 415 leftover json part.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#encoding-object", fetch2_ok="encoding.style form is not leftover JSON parts.")),
    (p(slug="oas-encoding-explode-mpart", domain="oas-encoding-explode-mpart-vs-leftover-multipart-csv-part", success=True, name="9c0574", stack="OpenAPI 3.1 explode + Go", field="explode", old="multipart csv leftover", new="encoding explode multipart", fail_err="415: leftover multipart csv leftover after encoding explode multipart-only", plan="encoding explode multipart-only 415s leftover multipart csv leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (encoding explode multipart vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#encoding-object", fetch1_ok="encoding.explode on multipart is not leftover csv parts.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch2_ok="Exclusive encoding explode 415 leftover csv."),
     p(slug="leftover-multipart-csv-part", domain="leftover-multipart-csv-part-vs-oas-encoding-explode-mpart", success=False, name="d1c259", stack="OpenAPI leftover explode + Java + TS", field="explode", old="encoding explode multipart", new="multipart csv leftover only", fail_err="415: leftover encoding explode multipart after multipart csv leftover-only", plan="multipart csv leftover-only 415s leftover encoding explode multipart. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (multipart csv leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch1_ok="Exclusive encoding explode 415 leftover csv.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#encoding-object", fetch2_ok="encoding.explode on multipart is not leftover csv parts.")),
    (p(slug="oas-cookie-allow-reserved", domain="oas-cookie-allow-reserved-vs-leftover-cookie-percent-all", success=True, name="3a09fa", stack="OpenAPI 3.1 allowReserved + Go", field="allowReserved", old="cookie percent leftover", new="cookie allowReserved", fail_err="400: leftover cookie percent leftover after cookie allowReserved-only", plan="cookie allowReserved-only 400s leftover cookie percent leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (cookie allowReserved vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="cookie allowReserved is not leftover percent-all cookies.", fetch2="https://datatracker.ietf.org/doc/html/rfc3986", fetch2_ok="Exclusive cookie allowReserved 400 leftover percent."),
     p(slug="leftover-cookie-percent-all", domain="leftover-cookie-percent-all-vs-oas-cookie-allow-reserved", success=False, name="826a57", stack="OpenAPI leftover allowReserved + Java + TS", field="allowReserved", old="cookie allowReserved", new="cookie percent leftover only", fail_err="400: leftover cookie allowReserved after cookie percent leftover-only", plan="cookie percent leftover-only 400s leftover cookie allowReserved. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (cookie percent leftover leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc3986", fetch1_ok="Exclusive cookie allowReserved 400 leftover percent.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="cookie allowReserved is not leftover percent-all cookies.")),
    (p(slug="oas-query-allow-empty-value", domain="oas-query-allow-empty-value-vs-leftover-drop-empty-query-param", success=True, name="2dcd79", stack="OpenAPI 3.1 allowEmptyValue + Go", field="allowEmptyValue", old="drop empty leftover", new="query allowEmptyValue", fail_err="400: leftover drop empty leftover after query allowEmptyValue-only", plan="query allowEmptyValue-only 400s leftover drop empty leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (query allowEmptyValue vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="allowEmptyValue on query is not leftover drop-empty.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch2_ok="Exclusive allowEmptyValue 400 leftover drop empty."),
     p(slug="leftover-drop-empty-query-param", domain="leftover-drop-empty-query-param-vs-oas-query-allow-empty-value", success=False, name="480c34", stack="OpenAPI leftover allowEmptyValue + Java + TS", field="allowEmptyValue", old="query allowEmptyValue", new="drop empty leftover only", fail_err="400: leftover query allowEmptyValue after drop empty leftover-only", plan="drop empty leftover-only 400s leftover query allowEmptyValue. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (drop empty leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch1_ok="Exclusive allowEmptyValue 400 leftover drop empty.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="allowEmptyValue on query is not leftover drop-empty.")),
    (p(slug="oas-api-key-header-name", domain="oas-api-key-header-name-vs-leftover-x-api-key-query", success=True, name="512606", stack="OpenAPI 3.1 in + Go", field="in", old="query apikey leftover", new="apiKey header name", fail_err="401: leftover query apikey leftover after apiKey header name-only", plan="apiKey header name-only 401s leftover query apikey leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (apiKey header name vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch1_ok="apiKey in header is not leftover query x-api-key.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#security-requirement-object", fetch2_ok="Exclusive header apikey 401 leftover query."),
     p(slug="leftover-x-api-key-query", domain="leftover-x-api-key-query-vs-oas-api-key-header-name", success=False, name="6c29d0", stack="OpenAPI leftover in + Java + TS", field="in", old="apiKey header name", new="query apikey leftover only", fail_err="401: leftover apiKey header name after query apikey leftover-only", plan="query apikey leftover-only 401s leftover apiKey header name. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (query apikey leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#security-requirement-object", fetch1_ok="Exclusive header apikey 401 leftover query.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch2_ok="apiKey in header is not leftover query x-api-key.")),
    (p(slug="oas-negotiate-http-auth", domain="oas-negotiate-http-auth-vs-leftover-ntlm-auth-header", success=True, name="c5927a", stack="OpenAPI 3.1 scheme + Go", field="scheme", old="ntlm leftover", new="HTTP Negotiate", fail_err="401: leftover ntlm leftover after HTTP Negotiate-only", plan="HTTP Negotiate-only 401s leftover ntlm leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (HTTP Negotiate vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch1_ok="HTTP Negotiate is not leftover NTLM headers.", fetch2="https://datatracker.ietf.org/doc/html/rfc4559", fetch2_ok="Exclusive Negotiate 401 leftover NTLM."),
     p(slug="leftover-ntlm-auth-header", domain="leftover-ntlm-auth-header-vs-oas-negotiate-http-auth", success=False, name="8059d4", stack="OpenAPI leftover scheme + Java + TS", field="scheme", old="HTTP Negotiate", new="ntlm leftover only", fail_err="401: leftover HTTP Negotiate after ntlm leftover-only", plan="ntlm leftover-only 401s leftover HTTP Negotiate. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (ntlm leftover leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc4559", fetch1_ok="Exclusive Negotiate 401 leftover NTLM.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch2_ok="HTTP Negotiate is not leftover NTLM headers.")),
    (p(slug="oas-contact-email-rfc5322", domain="oas-contact-email-rfc5322-vs-leftover-contact-unformatted", success=True, name="1f7ea8", stack="OpenAPI 3.1 email + Go", field="email", old="unformatted contact leftover", new="contact email rfc5322", fail_err="400: leftover unformatted contact leftover after contact email rfc5322-only", plan="contact email rfc5322-only 400s leftover unformatted contact leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (contact email rfc5322 vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#contact-object", fetch1_ok="contact.email is RFC5322, leftover unformatted fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#info-object", fetch2_ok="Exclusive contact email 400 leftover unformatted."),
     p(slug="leftover-contact-unformatted", domain="leftover-contact-unformatted-vs-oas-contact-email-rfc5322", success=False, name="1a6307", stack="OpenAPI leftover email + Java + TS", field="email", old="contact email rfc5322", new="unformatted contact leftover only", fail_err="400: leftover contact email rfc5322 after unformatted contact leftover-only", plan="unformatted contact leftover-only 400s leftover contact email rfc5322. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (unformatted contact leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#info-object", fetch1_ok="Exclusive contact email 400 leftover unformatted.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#contact-object", fetch2_ok="contact.email is RFC5322, leftover unformatted fails closed.")),
    (p(slug="oas-operation-servers-https", domain="oas-operation-servers-https-vs-leftover-op-http-server", success=True, name="db5f71", stack="OpenAPI 3.1 servers + Go", field="servers", old="op http leftover", new="operation https servers", fail_err="400: leftover op http leftover after operation https servers-only", plan="operation https servers-only 400s leftover op http leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (operation https servers vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch1_ok="operation.servers must be https, leftover http fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#server-object", fetch2_ok="Exclusive op https 400 leftover http."),
     p(slug="leftover-op-http-server", domain="leftover-op-http-server-vs-oas-operation-servers-https", success=False, name="27bf71", stack="OpenAPI leftover servers + Java + TS", field="servers", old="operation https servers", new="op http leftover only", fail_err="400: leftover operation https servers after op http leftover-only", plan="op http leftover-only 400s leftover operation https servers. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (op http leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#server-object", fetch1_ok="Exclusive op https 400 leftover http.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch2_ok="operation.servers must be https, leftover http fails closed.")),
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
    print(json.dumps({"round": round_n, "idx": idx, "ids": [e1["id"], e2["id"]], "catalog": "r4390"}))


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
