#!/usr/bin/env python3
"""Second unique OpenAPI-drift ACM catalog after r4007 mill."""
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
    "acm-mill-r3620.py", "acm-mill-r3667.py", "acm-mill-r3698.py",
    "acm-mill-r3714.py", "acm-mill-r3787.py", "acm-mill-r3851.py",
    "acm-mill-r3867.py", "acm-mill-r3883.py", "acm-mill-r3899.py",
    "acm-mill-r3915.py", "acm-mill-r3931.py", "acm-mill-r3947.py",
    "acm-mill-r3963.py", "acm-mill-r3978.py", "acm-mill-r3993.py",
    "acm-mill-r4007.py",
]
BANNED_PRIOR = {p[0]["slug"] for p in _b.PAIRS} | {p[1]["slug"] for p in _b.PAIRS}
for fname in priors:
    sp = importlib.util.spec_from_file_location(fname.replace("-", "_"), HERE / fname)
    mod = importlib.util.module_from_spec(sp)
    assert sp.loader is not None
    sp.loader.exec_module(mod)
    BANNED_PRIOR |= {p[0]["slug"] for p in mod.PAIRS} | {p[1]["slug"] for p in mod.PAIRS}

BANNED_PRIOR |= {
    "oas-allowemptyvalue-header", "leftover-omit-header-empty",
    "oas-lll4-proto-optional", "protobuf-lll4-optional-oas",
    "accept-language-bcp47", "iso639-language",
    "smile-binary-json", "cbor-majortype-vs-smile",
    "422-vs-400-validation", "207-multistatus-batch",
}


def p(**kw):
    return plant(**kw)


PAIRS: list[tuple[dict, dict]] = [
    (p(slug="oas-security-apikey-cookie", domain="oas-apikey-cookie-vs-querystring", success=True, name="apikc", stack="OpenAPI 3.1 apiKey cookie + Go", field="in", old="querystring apikey leftover", new="apiKey cookie", fail_err="401: leftover querystring apikey after cookie-only", plan="apiKey-cookie-only 401s leftover querystring. Dual-accept query for one release.", residual="edge still query leftover; drop after edge 6", vs="r3947 leftover-query-apikey (cookie vs querystring leftover, not header mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch1_ok="apiKey in=cookie is not leftover querystring keys.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#fixed-fields-21", fetch2_ok="Exclusive apiKey cookie 401 leftover querystring."),
     p(slug="leftover-apikey-querystring", domain="querystring-apikey-vs-oas-cookie", success=False, name="apikqs", stack="OpenAPI leftover querystring apikey + Java + TS", field="in", old="apiKey cookie", new="querystring apikey leftover only", fail_err="401: leftover apiKey cookie after querystring-only", plan="Querystring-only 401s leftover apiKey cookie. Freeze cookie, spec query leftover.", residual="handoff: keep apiKey cookie or force querystring leftover", vs="r3947 oas-security-apikey-header (querystring leftover, not header)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#fixed-fields-21", fetch1_ok="Querystring apiKeys are not in=cookie.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch2_ok="Exclusive querystring apikey 401 leftover cookie.")),
    (p(slug="oas-parameter-explode-false", domain="oas-unexplode-vs-always-explode", success=True, name="unxpl", stack="OpenAPI 3.1 explode=false + Go", field="explode", old="always explode leftover", new="explode false", fail_err="400: leftover always-explode after explode-false-only", plan="explode-false-only 400s leftover always-explode. Dual-read explode for one release.", residual="gateway still explode leftover; drop after gateway 5", vs="r3931 leftover-unexplode-query (explode false vs always leftover, not query unexplode mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch1_ok="explode=false is not leftover always-explode.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="Exclusive explode=false 400 leftover always-explode."),
     p(slug="leftover-always-explode", domain="always-explode-vs-oas-unexplode", success=False, name="alxpl", stack="OpenAPI leftover always explode + Java + TS", field="explode", old="explode false", new="always explode leftover only", fail_err="400: leftover explode=false after always-only", plan="Always-only 400s leftover explode=false. Freeze false, spec always leftover.", residual="handoff: keep explode=false or force always leftover", vs="r3931 oas-query-form-explode (always leftover, not form explode mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="Always explode is not explode=false.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch2_ok="Exclusive always-explode 400 leftover false.")),
    (p(slug="oas-header-style-simple", domain="oas-header-simple-vs-form-explode", success=True, name="hdrsm", stack="OpenAPI 3.1 header style=simple + Go", field="style", old="header form explode leftover", new="header simple style", fail_err="400: leftover header form after simple-only", plan="Header-simple-only 400s leftover form. Dual-read form for one release.", residual="proxy still form leftover; drop after proxy 5", vs="r3867 leftover-hdr-form-style (header simple vs form leftover, not simple explode mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch1_ok="Header style=simple is the default, leftover form is not.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch2_ok="Exclusive header simple 400 leftover form."),
     p(slug="leftover-header-form-explode", domain="header-form-vs-oas-header-simple", success=False, name="hdrfe", stack="OpenAPI leftover header form explode + Java + TS", field="style", old="header simple style", new="header form explode leftover only", fail_err="400: leftover header simple after form-only", plan="Form-only 400s leftover header simple. Freeze simple, spec form leftover.", residual="handoff: keep header simple or force form leftover", vs="r3867 oas-hdr-simple-explode (form leftover, not simple explode mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch1_ok="Header form explode is not style=simple.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch2_ok="Exclusive header form 400 leftover simple.")),
    (p(slug="oas-response-header-retryafter", domain="oas-retryafter-vs-retry-body", success=True, name="rtaft", stack="OpenAPI 3.1 Retry-After header + Go", field="Retry-After", old="retry body leftover", new="Retry-After header", fail_err="400: leftover retry body after Retry-After-only", plan="Retry-After-only 400s leftover retry body. Dual-emit body for one release.", residual="sdk still body leftover; drop after sdk 6", vs="r3883 leftover-body-ratelimit (Retry-After vs body leftover, not RateLimit body)", fetch1="https://datatracker.ietf.org/doc/html/rfc9110#name-retry-after", fetch1_ok="Retry-After is a response header, not a leftover JSON body.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#response-object", fetch2_ok="Exclusive Retry-After 400 leftover retry body."),
     p(slug="leftover-retry-body", domain="retry-body-vs-oas-retryafter", success=False, name="rtbody", stack="OpenAPI leftover retry body + Java + TS", field="retryAfter", old="Retry-After header", new="retry body leftover only", fail_err="400: leftover Retry-After after body-only", plan="Body-only 400s leftover Retry-After. Freeze header, spec body leftover.", residual="handoff: keep Retry-After or force body leftover", vs="r3883 oas-response-header-rate (retry body leftover, not RateLimit header)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#response-object", fetch1_ok="A retry body field is not Retry-After.", fetch2="https://datatracker.ietf.org/doc/html/rfc9110#name-retry-after", fetch2_ok="Exclusive retry body 400 leftover Retry-After.")),
    (p(slug="oas-webhook-delete", domain="oas-webhook-delete-vs-webhook-head", success=True, name="whkdel", stack="OpenAPI 3.1 webhook DELETE + Go", field="delete", old="webhook HEAD leftover", new="webhook DELETE", fail_err="405: leftover webhook HEAD after DELETE-only", plan="Webhook-DELETE-only 405s leftover HEAD. Dual-accept HEAD for one release.", residual="edge still HEAD leftover; drop after edge 4", vs="r4007 leftover-webhook-patch (DELETE vs HEAD leftover, not PATCH mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#oasWebhooks", fetch1_ok="Webhook Path Items may DELETE; leftover HEAD is not the contract.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#path-item-object", fetch2_ok="Exclusive webhook DELETE 405 leftover HEAD."),
     p(slug="leftover-webhook-head", domain="webhook-head-vs-oas-webhook-delete", success=False, name="whkhd", stack="OpenAPI leftover webhook HEAD + Java + TS", field="head", old="webhook DELETE", new="webhook HEAD leftover only", fail_err="405: leftover webhook DELETE after HEAD-only", plan="Webhook-HEAD-only 405s leftover DELETE. Freeze DELETE, spec HEAD leftover.", residual="handoff: keep webhook DELETE or force HEAD leftover", vs="r4007 oas-webhook-put (HEAD leftover, not PUT mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#path-item-object", fetch1_ok="Webhook HEAD is not the DELETE-only contract.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#oasWebhooks", fetch2_ok="Exclusive webhook HEAD 405 leftover DELETE.")),
    (p(slug="oas-servers-multiple-prod-stage", domain="oas-prod-stage-vs-single-prod", success=True, name="srvps", stack="OpenAPI 3.1 prod+stage servers + Go", field="servers", old="single prod url leftover", new="prod and stage servers", fail_err="400: leftover single-prod after prod-stage-only", plan="Prod-stage-only 400s leftover single-prod. Dual-accept single for one release.", residual="sdk still single leftover; drop after sdk 7", vs="r3931 leftover-single-server (prod+stage vs single leftover, not multi-server mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#oasServers", fetch1_ok="servers[] lists prod and stage, leftover single prod is not that.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#server-object", fetch2_ok="Exclusive prod+stage 400 leftover single-prod."),
     p(slug="leftover-single-prod-url", domain="single-prod-vs-oas-prod-stage", success=False, name="srv1p", stack="OpenAPI leftover single prod url + Java + TS", field="url", old="prod and stage servers", new="single prod url leftover only", fail_err="400: leftover prod-stage after single-only", plan="Single-only 400s leftover prod-stage. Freeze array, spec single leftover.", residual="handoff: keep prod+stage or force single leftover", vs="r3931 oas-servers-multiple (single leftover, not multi mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#server-object", fetch1_ok="A single leftover prod URL is not servers[].", fetch2="https://spec.openapis.org/oas/v3.1.0.html#oasServers", fetch2_ok="Exclusive single-prod 400 leftover prod-stage.")),
    (p(slug="oas-schema-unevaluated-items", domain="oas-uneval-items-vs-additional-items", success=True, name="ueitm", stack="OpenAPI 3.1 unevaluatedItems + Go", field="unevaluatedItems", old="additionalItems leftover", new="unevaluatedItems false", fail_err="400: leftover additionalItems after unevaluatedItems-only", plan="unevaluatedItems-only 400s leftover additionalItems. Dual-read additionalItems for one release.", residual="validator still additional leftover; drop after validator 5", vs="r3715 json-schema-unevaluatedproperties-vs-additionalproperties (unevaluatedItems vs additionalItems leftover, not properties)", fetch1="https://json-schema.org/understanding-json-schema/reference/array#unevaluateditems", fetch1_ok="unevaluatedItems is not leftover draft-04 additionalItems.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive unevaluatedItems 400 leftover additionalItems."),
     p(slug="leftover-additional-items", domain="additional-items-vs-oas-uneval-items", success=False, name="addit", stack="OpenAPI leftover additionalItems + Java + TS", field="additionalItems", old="unevaluatedItems false", new="additionalItems leftover only", fail_err="400: leftover unevaluatedItems after additionalItems-only", plan="additionalItems-only 400s leftover unevaluatedItems. Freeze unevaluatedItems, spec additional leftover.", residual="handoff: keep unevaluatedItems or force additional leftover", vs="r3715 json-schema-unevaluatedproperties-vs-additionalproperties (additionalItems leftover, not properties)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="additionalItems is not unevaluatedItems.", fetch2="https://json-schema.org/understanding-json-schema/reference/array#unevaluateditems", fetch2_ok="Exclusive additionalItems 400 leftover unevaluatedItems.")),
    (p(slug="oas-format-iri-fragment", domain="oas-iri-fragment-vs-hash-only", success=True, name="irifrag", stack="OpenAPI 3.1 IRI fragment + Go", field="format", old="hash only leftover", new="iri fragment", fail_err="400: leftover hash-only after iri-fragment-only", plan="iri-fragment-only 400s leftover hash-only. Dual-read hash for one release.", residual="spa still hash leftover; drop after spa 5", vs="r3963 leftover-relative-path (iri fragment vs hash leftover, not relative path)", fetch1="https://json-schema.org/understanding-json-schema/reference/string#resource-identifiers", fetch1_ok="IRI fragments are not leftover #hash tokens.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="Exclusive iri fragment 400 leftover hash-only."),
     p(slug="leftover-hash-only", domain="hash-only-vs-oas-iri-fragment", success=False, name="hasho", stack="OpenAPI leftover hash-only + Java + TS", field="hash", old="iri fragment", new="hash only leftover only", fail_err="400: leftover iri-fragment after hash-only", plan="Hash-only 400s leftover iri-fragment. Freeze fragment, spec hash leftover.", residual="handoff: keep iri fragment or force hash leftover", vs="r3963 oas-format-iri-reference (hash leftover, not iri-reference)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="Bare hashes are not IRI fragments.", fetch2="https://json-schema.org/understanding-json-schema/reference/string#resource-identifiers", fetch2_ok="Exclusive hash-only 400 leftover iri fragment.")),
    (p(slug="oas-operation-callbacks-required", domain="oas-op-callbacks-vs-no-callbacks", success=True, name="opcb", stack="OpenAPI 3.1 operation callbacks + Go", field="callbacks", old="no callbacks leftover", new="operation callbacks", fail_err="400: leftover no-callbacks after callbacks-only", plan="operation.callbacks-only 400s leftover no-callbacks. Dual-omit callbacks for one release.", residual="bus still no-callbacks leftover; drop after bus 6", vs="r3993 leftover-inline-callbacks (op callbacks vs none leftover, not components.callbacks)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch1_ok="operation.callbacks declare out-of-band calls, leftover missing fail closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#callback-object", fetch2_ok="Exclusive op callbacks 400 leftover none."),
     p(slug="leftover-no-callbacks", domain="no-callbacks-vs-oas-op-callbacks", success=False, name="nocb", stack="OpenAPI leftover no callbacks + Java + TS", field="callbacks", old="operation callbacks", new="no callbacks leftover only", fail_err="400: leftover operation.callbacks after none-only", plan="None-only 400s leftover operation.callbacks. Freeze callbacks, spec none leftover.", residual="handoff: keep operation.callbacks or force none leftover", vs="r3993 oas-components-callbacks (no-callbacks leftover, not components mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#callback-object", fetch1_ok="Missing callbacks are not operation.callbacks.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch2_ok="Exclusive no-callbacks 400 leftover operation.callbacks.")),
    (p(slug="oas-xml-namespace-prefix", domain="oas-ns-prefix-vs-unprefixed-ns", success=True, name="nspre", stack="OpenAPI 3.1 xml namespace+prefix + Go", field="prefix", old="unprefixed ns leftover", new="xml ns prefix", fail_err="415: leftover unprefixed ns after ns-prefix-only", plan="ns-prefix-only 415s leftover unprefixed. Dual-read unprefixed for one release.", residual="batch still unprefixed leftover; drop after batch 5", vs="r3931 leftover-no-prefix (ns prefix vs unprefixed leftover, not xml.prefix mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#xml-object", fetch1_ok="xml.prefix with namespace is not leftover unprefixed names.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive ns prefix 415 leftover unprefixed."),
     p(slug="leftover-unprefixed-ns", domain="unprefixed-ns-vs-oas-ns-prefix", success=False, name="unpns", stack="OpenAPI leftover unprefixed ns + Java + TS", field="namespace", old="xml ns prefix", new="unprefixed ns leftover only", fail_err="415: leftover ns prefix after unprefixed-only", plan="Unprefixed-only 415s leftover ns prefix. Freeze prefix, spec unprefixed leftover.", residual="handoff: keep ns prefix or force unprefixed leftover", vs="r3899 leftover-unqualified-xml (unprefixed leftover, not unqualified mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Unprefixed namespaces are not xml.prefix.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#xml-object", fetch2_ok="Exclusive unprefixed ns 415 leftover prefix.")),
    (p(slug="oas-content-multipart-mixed", domain="oas-multipart-mixed-vs-form-data", success=True, name="mpmix", stack="OpenAPI 3.1 multipart/mixed + Go", field="content", old="multipart form leftover", new="multipart mixed", fail_err="415: leftover multipart/form-data after mixed-only", plan="multipart-mixed-only 415s leftover form-data. Dual-read form for one release.", residual="ingest still form leftover; drop after ingest 6", vs="r3867 leftover-prop-mediatype (multipart mixed vs form leftover, not property media)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch1_ok="multipart/mixed is not leftover multipart/form-data.", fetch2="https://datatracker.ietf.org/doc/html/rfc2046#section-5.1.3", fetch2_ok="Exclusive multipart/mixed 415 leftover form-data."),
     p(slug="leftover-multipart-form", domain="form-data-vs-oas-multipart-mixed", success=False, name="mpform", stack="OpenAPI leftover multipart form + Java + TS", field="content", old="multipart mixed", new="multipart form leftover only", fail_err="415: leftover multipart/mixed after form-only", plan="Form-only 415s leftover multipart/mixed. Freeze mixed, spec form leftover.", residual="handoff: keep multipart/mixed or force form leftover", vs="r3867 oas-encoding-ctype (form leftover, not encoding.contentType)", fetch1="https://datatracker.ietf.org/doc/html/rfc7578", fetch1_ok="multipart/form-data is not multipart/mixed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch2_ok="Exclusive form-data 415 leftover mixed.")),
    (p(slug="oas-security-mutualtls-optional", domain="oas-optional-mtls-vs-required-mtls", success=True, name="mtlsopt", stack="OpenAPI 3.1 optional mutualTLS + Go", field="security", old="required mtls leftover", new="optional mutualTLS", fail_err="401: leftover required mtls after optional-only", plan="Optional-mtls-only 401s leftover required. Dual-require mtls for one release.", residual="edge still required leftover; drop after edge 5", vs="r3899 leftover-client-cert-header (optional mtls vs required leftover, not cert header)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#security-requirement-object", fetch1_ok="Empty security plus mutualTLS makes mTLS optional, leftover required is not that.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch2_ok="Exclusive optional mtls 401 leftover required."),
     p(slug="leftover-mtls-required", domain="required-mtls-vs-oas-optional-mtls", success=False, name="mtlsrq", stack="OpenAPI leftover required mtls + Java + TS", field="mutualTLS", old="optional mutualTLS", new="required mtls leftover only", fail_err="401: leftover optional mtls after required-only", plan="Required-only 401s leftover optional mtls. Freeze optional, spec required leftover.", residual="handoff: keep optional mtls or force required leftover", vs="r3899 oas-mutualtls-scheme (required leftover, not mutualTLS mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch1_ok="Required mTLS is not optional security:[].", fetch2="https://spec.openapis.org/oas/v3.1.0.html#security-requirement-object", fetch2_ok="Exclusive required mtls 401 leftover optional.")),
    (p(slug="oas-schema-prefixitems-rest", domain="oas-prefixitems-rest-vs-homogeneous", success=True, name="prestr", stack="OpenAPI 3.1 prefixItems + items rest + Go", field="prefixItems", old="homogeneous items leftover", new="prefixItems with rest items", fail_err="400: leftover homogeneous after prefixItems-rest-only", plan="prefixItems-rest-only 400s leftover homogeneous. Dual-read homogeneous for one release.", residual="validator still homogeneous leftover; drop after validator 6", vs="wrap prefixitems-latlon (prefixItems rest vs homogeneous leftover, not latlon cartesian)", fetch1="https://json-schema.org/understanding-json-schema/reference/array#tupleValidation", fetch1_ok="prefixItems plus items describes a tuple with rest, leftover homogeneous items are not that.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive prefixItems rest 400 leftover homogeneous."),
     p(slug="leftover-homogeneous-items", domain="homogeneous-vs-oas-prefixitems-rest", success=False, name="homoit", stack="OpenAPI leftover homogeneous items + Java + TS", field="items", old="prefixItems with rest items", new="homogeneous items leftover only", fail_err="400: leftover prefixItems after homogeneous-only", plan="Homogeneous-only 400s leftover prefixItems. Freeze prefixItems, spec homogeneous leftover.", residual="handoff: keep prefixItems rest or force homogeneous leftover", vs="wrap prefixitems-latlon (homogeneous leftover, not latlon cartesian)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Homogeneous items are not prefixItems+rest.", fetch2="https://json-schema.org/understanding-json-schema/reference/array#tupleValidation", fetch2_ok="Exclusive homogeneous 400 leftover prefixItems.")),
    (p(slug="oas-format-email-localpart", domain="oas-email-localpart-vs-display-name", success=True, name="elocal", stack="OpenAPI 3.1 email local-part + Go", field="format", old="display name email leftover", new="email local-part", fail_err="400: leftover display-name email after local-part-only", plan="local-part-only 400s leftover display-name. Dual-read display-name for one release.", residual="crm still display leftover; drop after crm 5", vs="r3947 leftover-unvalidated-email (local-part vs display leftover, not unvalidated mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/string#email", fetch1_ok="format=email is addr-spec, leftover Display Name <addr> fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="Exclusive email local-part 400 leftover display-name."),
     p(slug="leftover-display-name-email", domain="display-name-vs-oas-email-localpart", success=False, name="edisp", stack="OpenAPI leftover display-name email + Java + TS", field="email", old="email local-part", new="display name email leftover only", fail_err="400: leftover local-part after display-only", plan="Display-only 400s leftover local-part. Freeze local-part, spec display leftover.", residual="handoff: keep email local-part or force display leftover", vs="r3947 oas-format-email-ascii (display leftover, not ascii email mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="Display Name emails are not format=email addr-spec.", fetch2="https://json-schema.org/understanding-json-schema/reference/string#email", fetch2_ok="Exclusive display-name 400 leftover local-part.")),
    (p(slug="oas-schema-content-schema", domain="oas-contentschema-vs-untyped-payload", success=True, name="csch", stack="OpenAPI 3.1 contentSchema + Go", field="contentSchema", old="untyped payload leftover", new="contentSchema", fail_err="400: leftover untyped payload after contentSchema-only", plan="contentSchema-only 400s leftover untyped. Dual-read untyped for one release.", residual="store still untyped leftover; drop after store 6", vs="r3931 leftover-untyped-blob (contentSchema vs untyped leftover, not blob mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/non_json_data#contentschema", fetch1_ok="contentSchema validates decoded content, leftover untyped payloads fail closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive contentSchema 400 leftover untyped."),
     p(slug="leftover-untyped-payload", domain="untyped-payload-vs-oas-contentschema", success=False, name="utpay", stack="OpenAPI leftover untyped payload + Java + TS", field="content", old="contentSchema", new="untyped payload leftover only", fail_err="400: leftover contentSchema after untyped-only", plan="Untyped-only 400s leftover contentSchema. Freeze contentSchema, spec untyped leftover.", residual="handoff: keep contentSchema or force untyped leftover", vs="r3931 oas-content-media-type (untyped leftover, not contentMediaType mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Untyped payloads are not contentSchema.", fetch2="https://json-schema.org/understanding-json-schema/reference/non_json_data#contentschema", fetch2_ok="Exclusive untyped payload 400 leftover contentSchema.")),
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
    print(json.dumps({"round": round_n, "idx": idx, "ids": [e1["id"], e2["id"]], "catalog": "r4023"}))


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
