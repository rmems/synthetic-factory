#!/usr/bin/env python3
"""Unique OpenAPI-drift ACM catalog r4454. Fast slug load."""
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
    (p(slug="oas-webhook-trace-absent", domain="oas-webhook-trace-absent-vs-leftover-webhook-trace-enabled", success=True, name="feb255", stack="OpenAPI 3.1 trace + Go", field="trace", old="webhook TRACE leftover", new="webhook TRACE absent", fail_err="400: leftover webhook TRACE leftover after webhook TRACE absent-only", plan="webhook TRACE absent-only 400s leftover webhook TRACE leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (webhook TRACE absent vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#oasWebhooks", fetch1_ok="Webhook TRACE is absent here, leftover TRACE fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#path-item-object", fetch2_ok="Exclusive webhook TRACE off 400 leftover enabled."),
     p(slug="leftover-webhook-trace-enabled", domain="leftover-webhook-trace-enabled-vs-oas-webhook-trace-absent", success=False, name="0a8069", stack="OpenAPI leftover trace + Java + TS", field="trace", old="webhook TRACE absent", new="webhook TRACE leftover only", fail_err="400: leftover webhook TRACE absent after webhook TRACE leftover-only", plan="webhook TRACE leftover-only 400s leftover webhook TRACE absent. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (webhook TRACE leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#path-item-object", fetch1_ok="Exclusive webhook TRACE off 400 leftover enabled.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#oasWebhooks", fetch2_ok="Webhook TRACE is absent here, leftover TRACE fails closed.")),
    (p(slug="oas-components-pathitems-param", domain="oas-components-pathitems-param-vs-leftover-pathitem-no-params", success=True, name="8910b1", stack="OpenAPI 3.1 parameters + Go", field="parameters", old="pathItem no params leftover", new="components pathItems params", fail_err="400: leftover pathItem no params leftover after components pathItems params-only", plan="components pathItems params-only 400s leftover pathItem no params leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (components pathItems params vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#components-object", fetch1_ok="Reusable pathItems can carry parameters, leftover none fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#path-item-object", fetch2_ok="Exclusive pathItems params 400 leftover none."),
     p(slug="leftover-pathitem-no-params", domain="leftover-pathitem-no-params-vs-oas-components-pathitems-param", success=False, name="f47a07", stack="OpenAPI leftover parameters + Java + TS", field="parameters", old="components pathItems params", new="pathItem no params leftover only", fail_err="400: leftover components pathItems params after pathItem no params leftover-only", plan="pathItem no params leftover-only 400s leftover components pathItems params. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (pathItem no params leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#path-item-object", fetch1_ok="Exclusive pathItems params 400 leftover none.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#components-object", fetch2_ok="Reusable pathItems can carry parameters, leftover none fails closed.")),
    (p(slug="oas-security-optional-and-required", domain="oas-security-optional-and-required-vs-leftover-mixed-security-wrong", success=True, name="33cdfd", stack="OpenAPI 3.1 security + Go", field="security", old="mixed security leftover", new="optional and required security", fail_err="401: leftover mixed security leftover after optional and required security-only", plan="optional and required security-only 401s leftover mixed security leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (optional and required security vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#security-requirement-object", fetch1_ok="Optional {} plus required schemes is not leftover mixed wrong.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch2_ok="Exclusive optional+required 401 leftover mixed."),
     p(slug="leftover-mixed-security-wrong", domain="leftover-mixed-security-wrong-vs-oas-security-optional-and-required", success=False, name="9e168f", stack="OpenAPI leftover security + Java + TS", field="security", old="optional and required security", new="mixed security leftover only", fail_err="401: leftover optional and required security after mixed security leftover-only", plan="mixed security leftover-only 401s leftover optional and required security. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (mixed security leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch1_ok="Exclusive optional+required 401 leftover mixed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#security-requirement-object", fetch2_ok="Optional {} plus required schemes is not leftover mixed wrong.")),
    (p(slug="oas-oauth2-device-code", domain="oas-oauth2-device-code-vs-leftover-device-as-password", success=True, name="0c3728", stack="OpenAPI 3.1 deviceAuthorization + Go", field="deviceAuthorization", old="device as password leftover", new="device code flow", fail_err="401: leftover device as password leftover after device code flow-only", plan="device code flow-only 401s leftover device as password leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (device code flow vs leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc8628", fetch1_ok="Device code flow is not leftover password-as-device.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#oauth-flows-object", fetch2_ok="Exclusive device code 401 leftover password."),
     p(slug="leftover-device-as-password", domain="leftover-device-as-password-vs-oas-oauth2-device-code", success=False, name="0d6268", stack="OpenAPI leftover deviceAuthorization + Java + TS", field="deviceAuthorization", old="device code flow", new="device as password leftover only", fail_err="401: leftover device code flow after device as password leftover-only", plan="device as password leftover-only 401s leftover device code flow. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (device as password leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#oauth-flows-object", fetch1_ok="Exclusive device code 401 leftover password.", fetch2="https://datatracker.ietf.org/doc/html/rfc8628", fetch2_ok="Device code flow is not leftover password-as-device.")),
    (p(slug="oas-mtls-plus-bearer", domain="oas-mtls-plus-bearer-vs-leftover-mtls-only-or-bearer", success=True, name="d372e1", stack="OpenAPI 3.1 security + Go", field="security", old="mtls xor bearer leftover", new="mutualTLS plus bearer", fail_err="401: leftover mtls xor bearer leftover after mutualTLS plus bearer-only", plan="mutualTLS plus bearer-only 401s leftover mtls xor bearer leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (mutualTLS plus bearer vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#security-requirement-object", fetch1_ok="AND of mutualTLS plus bearer is not leftover xor.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch2_ok="Exclusive mtls+bearer 401 leftover xor."),
     p(slug="leftover-mtls-only-or-bearer", domain="leftover-mtls-only-or-bearer-vs-oas-mtls-plus-bearer", success=False, name="67a675", stack="OpenAPI leftover security + Java + TS", field="security", old="mutualTLS plus bearer", new="mtls xor bearer leftover only", fail_err="401: leftover mutualTLS plus bearer after mtls xor bearer leftover-only", plan="mtls xor bearer leftover-only 401s leftover mutualTLS plus bearer. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (mtls xor bearer leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch1_ok="Exclusive mtls+bearer 401 leftover xor.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#security-requirement-object", fetch2_ok="AND of mutualTLS plus bearer is not leftover xor.")),
    (p(slug="oas-api-key-query-name", domain="oas-api-key-query-name-vs-leftover-api-key-as-bearer", success=True, name="d1de0f", stack="OpenAPI 3.1 in + Go", field="in", old="apikey as bearer leftover", new="apiKey query name", fail_err="401: leftover apikey as bearer leftover after apiKey query name-only", plan="apiKey query name-only 401s leftover apikey as bearer leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (apiKey query name vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch1_ok="apiKey in query is not leftover bearer.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#security-requirement-object", fetch2_ok="Exclusive query apikey 401 leftover bearer."),
     p(slug="leftover-api-key-as-bearer", domain="leftover-api-key-as-bearer-vs-oas-api-key-query-name", success=False, name="d54967", stack="OpenAPI leftover in + Java + TS", field="in", old="apiKey query name", new="apikey as bearer leftover only", fail_err="401: leftover apiKey query name after apikey as bearer leftover-only", plan="apikey as bearer leftover-only 401s leftover apiKey query name. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (apikey as bearer leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#security-requirement-object", fetch1_ok="Exclusive query apikey 401 leftover bearer.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch2_ok="apiKey in query is not leftover bearer.")),
    (p(slug="oas-cookie-api-key-httponly", domain="oas-cookie-api-key-httponly-vs-leftover-readable-apikey-cookie", success=True, name="151f50", stack="OpenAPI 3.1 in + Go", field="in", old="readable cookie leftover", new="HttpOnly apiKey cookie", fail_err="401: leftover readable cookie leftover after HttpOnly apiKey cookie-only", plan="HttpOnly apiKey cookie-only 401s leftover readable cookie leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (HttpOnly apiKey cookie vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch1_ok="apiKey cookie must be HttpOnly, leftover readable fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="Exclusive HttpOnly cookie 401 leftover readable."),
     p(slug="leftover-readable-apikey-cookie", domain="leftover-readable-apikey-cookie-vs-oas-cookie-api-key-httponly", success=False, name="ae58a8", stack="OpenAPI leftover in + Java + TS", field="in", old="HttpOnly apiKey cookie", new="readable cookie leftover only", fail_err="401: leftover HttpOnly apiKey cookie after readable cookie leftover-only", plan="readable cookie leftover-only 401s leftover HttpOnly apiKey cookie. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (readable cookie leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="Exclusive HttpOnly cookie 401 leftover readable.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch2_ok="apiKey cookie must be HttpOnly, leftover readable fails closed.")),
    (p(slug="oas-schema-id-absolute-uri", domain="oas-schema-id-absolute-uri-vs-leftover-relative-schema-id", success=True, name="672e24", stack="OpenAPI 3.1 $id + Go", field="$id", old="relative $id leftover", new="$id absolute uri", fail_err="400: leftover relative $id leftover after $id absolute uri-only", plan="$id absolute uri-only 400s leftover relative $id leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv ($id absolute uri vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/schema#id", fetch1_ok="$id should be an absolute URI, leftover relative fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive absolute $id 400 leftover relative."),
     p(slug="leftover-relative-schema-id", domain="leftover-relative-schema-id-vs-oas-schema-id-absolute-uri", success=False, name="13be45", stack="OpenAPI leftover $id + Java + TS", field="$id", old="$id absolute uri", new="relative $id leftover only", fail_err="400: leftover $id absolute uri after relative $id leftover-only", plan="relative $id leftover-only 400s leftover $id absolute uri. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (relative $id leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive absolute $id 400 leftover relative.", fetch2="https://json-schema.org/understanding-json-schema/reference/schema#id", fetch2_ok="$id should be an absolute URI, leftover relative fails closed.")),
    (p(slug="oas-anchor-plain-name", domain="oas-anchor-plain-name-vs-leftover-anchor-as-pointer", success=True, name="73b7ba", stack="OpenAPI 3.1 $anchor + Go", field="$anchor", old="anchor as pointer leftover", new="$anchor plain name", fail_err="400: leftover anchor as pointer leftover after $anchor plain name-only", plan="$anchor plain name-only 400s leftover anchor as pointer leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv ($anchor plain name vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/schema#anchor", fetch1_ok="$anchor is a plain name, leftover pointer-as-anchor fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive $anchor name 400 leftover pointer."),
     p(slug="leftover-anchor-as-pointer", domain="leftover-anchor-as-pointer-vs-oas-anchor-plain-name", success=False, name="6ad707", stack="OpenAPI leftover $anchor + Java + TS", field="$anchor", old="$anchor plain name", new="anchor as pointer leftover only", fail_err="400: leftover $anchor plain name after anchor as pointer leftover-only", plan="anchor as pointer leftover-only 400s leftover $anchor plain name. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (anchor as pointer leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive $anchor name 400 leftover pointer.", fetch2="https://json-schema.org/understanding-json-schema/reference/schema#anchor", fetch2_ok="$anchor is a plain name, leftover pointer-as-anchor fails closed.")),
    (p(slug="oas-dynamicanchor-scope", domain="oas-dynamicanchor-scope-vs-leftover-dynamic-as-static-id", success=True, name="2f31be", stack="OpenAPI 3.1 $dynamicAnchor + Go", field="$dynamicAnchor", old="dynamic as static leftover", new="$dynamicAnchor scope", fail_err="400: leftover dynamic as static leftover after $dynamicAnchor scope-only", plan="$dynamicAnchor scope-only 400s leftover dynamic as static leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv ($dynamicAnchor scope vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/schema#dynamic-references", fetch1_ok="$dynamicAnchor is dynamic scope, leftover static $id fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive $dynamicAnchor 400 leftover static."),
     p(slug="leftover-dynamic-as-static-id", domain="leftover-dynamic-as-static-id-vs-oas-dynamicanchor-scope", success=False, name="a7444d", stack="OpenAPI leftover $dynamicAnchor + Java + TS", field="$dynamicAnchor", old="$dynamicAnchor scope", new="dynamic as static leftover only", fail_err="400: leftover $dynamicAnchor scope after dynamic as static leftover-only", plan="dynamic as static leftover-only 400s leftover $dynamicAnchor scope. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (dynamic as static leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive $dynamicAnchor 400 leftover static.", fetch2="https://json-schema.org/understanding-json-schema/reference/schema#dynamic-references", fetch2_ok="$dynamicAnchor is dynamic scope, leftover static $id fails closed.")),
    (p(slug="oas-vocabulary-boolean-true", domain="oas-vocabulary-boolean-true-vs-leftover-vocab-ignored", success=True, name="c0bfd0", stack="OpenAPI 3.1 $vocabulary + Go", field="$vocabulary", old="vocab ignored leftover", new="$vocabulary true", fail_err="400: leftover vocab ignored leftover after $vocabulary true-only", plan="$vocabulary true-only 400s leftover vocab ignored leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv ($vocabulary true vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/schema#vocabulary", fetch1_ok="$vocabulary true requires the vocab, leftover ignored fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive $vocabulary true 400 leftover ignored."),
     p(slug="leftover-vocab-ignored", domain="leftover-vocab-ignored-vs-oas-vocabulary-boolean-true", success=False, name="192c84", stack="OpenAPI leftover $vocabulary + Java + TS", field="$vocabulary", old="$vocabulary true", new="vocab ignored leftover only", fail_err="400: leftover $vocabulary true after vocab ignored leftover-only", plan="vocab ignored leftover-only 400s leftover $vocabulary true. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (vocab ignored leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive $vocabulary true 400 leftover ignored.", fetch2="https://json-schema.org/understanding-json-schema/reference/schema#vocabulary", fetch2_ok="$vocabulary true requires the vocab, leftover ignored fails closed.")),
    (p(slug="oas-comment-non-validating", domain="oas-comment-non-validating-vs-leftover-comment-as-description", success=True, name="354f2d", stack="OpenAPI 3.1 $comment + Go", field="$comment", old="comment as description leftover", new="$comment non-validating", fail_err="400: leftover comment as description leftover after $comment non-validating-only", plan="$comment non-validating-only 400s leftover comment as description leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv ($comment non-validating vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/generic#annotation", fetch1_ok="$comment does not validate, leftover description-as-comment fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive $comment 400 leftover description."),
     p(slug="leftover-comment-as-description", domain="leftover-comment-as-description-vs-oas-comment-non-validating", success=False, name="6366e4", stack="OpenAPI leftover $comment + Java + TS", field="$comment", old="$comment non-validating", new="comment as description leftover only", fail_err="400: leftover $comment non-validating after comment as description leftover-only", plan="comment as description leftover-only 400s leftover $comment non-validating. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (comment as description leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive $comment 400 leftover description.", fetch2="https://json-schema.org/understanding-json-schema/reference/generic#annotation", fetch2_ok="$comment does not validate, leftover description-as-comment fails closed.")),
    (p(slug="oas-unevaluated-props-schema", domain="oas-unevaluated-props-schema-vs-leftover-additional-as-unevaluated", success=True, name="75fddb", stack="OpenAPI 3.1 unevaluatedProperties + Go", field="unevaluatedProperties", old="additional as unevaluated leftover", new="unevaluatedProperties schema", fail_err="400: leftover additional as unevaluated leftover after unevaluatedProperties schema-only", plan="unevaluatedProperties schema-only 400s leftover additional as unevaluated leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (unevaluatedProperties schema vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/object#unevaluatedproperties", fetch1_ok="unevaluatedProperties is not leftover additionalProperties.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive unevaluatedProperties 400 leftover additional."),
     p(slug="leftover-additional-as-unevaluated", domain="leftover-additional-as-unevaluated-vs-oas-unevaluated-props-schema", success=False, name="7e6161", stack="OpenAPI leftover unevaluatedProperties + Java + TS", field="unevaluatedProperties", old="unevaluatedProperties schema", new="additional as unevaluated leftover only", fail_err="400: leftover unevaluatedProperties schema after additional as unevaluated leftover-only", plan="additional as unevaluated leftover-only 400s leftover unevaluatedProperties schema. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (additional as unevaluated leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive unevaluatedProperties 400 leftover additional.", fetch2="https://json-schema.org/understanding-json-schema/reference/object#unevaluatedproperties", fetch2_ok="unevaluatedProperties is not leftover additionalProperties.")),
    (p(slug="oas-unevaluated-items-schema", domain="oas-unevaluated-items-schema-vs-leftover-items-as-unevaluated", success=True, name="9d055c", stack="OpenAPI 3.1 unevaluatedItems + Go", field="unevaluatedItems", old="items as unevaluated leftover", new="unevaluatedItems schema", fail_err="400: leftover items as unevaluated leftover after unevaluatedItems schema-only", plan="unevaluatedItems schema-only 400s leftover items as unevaluated leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (unevaluatedItems schema vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/array#unevaluateditems", fetch1_ok="unevaluatedItems is not leftover items.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive unevaluatedItems schema 400 leftover items."),
     p(slug="leftover-items-as-unevaluated", domain="leftover-items-as-unevaluated-vs-oas-unevaluated-items-schema", success=False, name="e1adfa", stack="OpenAPI leftover unevaluatedItems + Java + TS", field="unevaluatedItems", old="unevaluatedItems schema", new="items as unevaluated leftover only", fail_err="400: leftover unevaluatedItems schema after items as unevaluated leftover-only", plan="items as unevaluated leftover-only 400s leftover unevaluatedItems schema. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (items as unevaluated leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive unevaluatedItems schema 400 leftover items.", fetch2="https://json-schema.org/understanding-json-schema/reference/array#unevaluateditems", fetch2_ok="unevaluatedItems is not leftover items.")),
    (p(slug="oas-contains-max-one", domain="oas-contains-max-one-vs-leftover-contains-many-ok", success=True, name="0e3def", stack="OpenAPI 3.1 maxContains + Go", field="maxContains", old="many contains leftover", new="maxContains 1", fail_err="400: leftover many contains leftover after maxContains 1-only", plan="maxContains 1-only 400s leftover many contains leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (maxContains 1 vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/array#maxcontains", fetch1_ok="maxContains 1 rejects many matches, leftover many-ok fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive maxContains 1 400 leftover many."),
     p(slug="leftover-contains-many-ok", domain="leftover-contains-many-ok-vs-oas-contains-max-one", success=False, name="bed7ea", stack="OpenAPI leftover maxContains + Java + TS", field="maxContains", old="maxContains 1", new="many contains leftover only", fail_err="400: leftover maxContains 1 after many contains leftover-only", plan="many contains leftover-only 400s leftover maxContains 1. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (many contains leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive maxContains 1 400 leftover many.", fetch2="https://json-schema.org/understanding-json-schema/reference/array#maxcontains", fetch2_ok="maxContains 1 rejects many matches, leftover many-ok fails closed.")),
    (p(slug="oas-prefixitems-len-match", domain="oas-prefixitems-len-match-vs-leftover-tuple-length-open", success=True, name="71c593", stack="OpenAPI 3.1 prefixItems + Go", field="prefixItems", old="open tuple leftover", new="prefixItems length match", fail_err="400: leftover open tuple leftover after prefixItems length match-only", plan="prefixItems length match-only 400s leftover open tuple leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (prefixItems length match vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/array#tuple-validation", fetch1_ok="prefixItems length must match, leftover open length fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive prefixItems length 400 leftover open."),
     p(slug="leftover-tuple-length-open", domain="leftover-tuple-length-open-vs-oas-prefixitems-len-match", success=False, name="9b8f81", stack="OpenAPI leftover prefixItems + Java + TS", field="prefixItems", old="prefixItems length match", new="open tuple leftover only", fail_err="400: leftover prefixItems length match after open tuple leftover-only", plan="open tuple leftover-only 400s leftover prefixItems length match. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (open tuple leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive prefixItems length 400 leftover open.", fetch2="https://json-schema.org/understanding-json-schema/reference/array#tuple-validation", fetch2_ok="prefixItems length must match, leftover open length fails closed.")),
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
    print(json.dumps({"round": round_n, "idx": idx, "ids": [e1["id"], e2["id"]], "catalog": "r4454"}))


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
