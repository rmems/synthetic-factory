#!/usr/bin/env python3
"""Thirteenth unique OpenAPI-drift ACM catalog after r4182 mill. Fast slug load."""
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
    (p(slug="oas-schema-max-length-bytes", domain="oas-schema-max-length-bytes-vs-leftover-rune-count", success=True, name="maxlb", stack="OpenAPI 3.1 maxLength bytes + Go", field="maxLength", old="rune count leftover", new="maxLength bytes", fail_err="400: leftover rune count leftover after maxLength bytes-only", plan="maxLength bytes-only 400s leftover rune count leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4166 leftover-no-max-length (bytes vs rune leftover, not unbounded mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/string#length", fetch1_ok="maxLength is UTF-16 units not leftover rune counts.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive maxLength bytes 400 leftover runes."),
     p(slug="leftover-rune-count", domain="leftover-rune-count-vs-oas-schema-max-length-bytes", success=False, name="runec", stack="OpenAPI leftover rune count + Java + TS", field="maxLength", old="maxLength bytes", new="rune count leftover only", fail_err="400: leftover maxLength bytes after rune count leftover-only", plan="rune count leftover-only 400s leftover maxLength bytes. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4166 oas-schema-max-length (rune leftover, not maxLength mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive maxLength bytes 400 leftover runes.", fetch2="https://json-schema.org/understanding-json-schema/reference/string#length", fetch2_ok="maxLength is UTF-16 units not leftover rune counts.")),
    (p(slug="oas-parameter-in-path-required", domain="oas-parameter-in-path-required-vs-leftover-optional-path-param", success=True, name="pathrq", stack="OpenAPI 3.1 path param required + Go", field="required", old="optional path leftover", new="path param required", fail_err="400: leftover optional path leftover after path param required-only", plan="path param required-only 400s leftover optional path leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4166 leftover-optional-query (path required vs optional leftover, not query mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="Path params MUST be required, leftover optional fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#fixed-fields-9", fetch2_ok="Exclusive path required 400 leftover optional."),
     p(slug="leftover-optional-path-param", domain="leftover-optional-path-param-vs-oas-parameter-in-path-required", success=False, name="pathopt", stack="OpenAPI leftover optional path param + Java + TS", field="required", old="path param required", new="optional path leftover only", fail_err="400: leftover path param required after optional path leftover-only", plan="optional path leftover-only 400s leftover path param required. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4166 oas-parameter-required-query (optional leftover, not query mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#fixed-fields-9", fetch1_ok="Exclusive path required 400 leftover optional.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="Path params MUST be required, leftover optional fails closed.")),
    (p(slug="oas-response-201-location", domain="oas-response-201-location-vs-leftover-201-no-location", success=True, name="r201", stack="OpenAPI 3.1 201 Location + Go", field="Location", old="201 no location leftover", new="201 Location header", fail_err="400: leftover 201 no location leftover after 201 Location header-only", plan="201 Location header-only 400s leftover 201 no location leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4054 leftover-location-body (201 Location vs none leftover, not body mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#response-object", fetch1_ok="201 should include Location, leftover missing fails closed.", fetch2="https://datatracker.ietf.org/doc/html/rfc9110#name-201-created", fetch2_ok="Exclusive 201 Location 400 leftover none."),
     p(slug="leftover-201-no-location", domain="leftover-201-no-location-vs-oas-response-201-location", success=False, name="nloc201", stack="OpenAPI leftover 201 no location + Java + TS", field="Location", old="201 Location header", new="201 no location leftover only", fail_err="400: leftover 201 Location header after 201 no location leftover-only", plan="201 no location leftover-only 400s leftover 201 Location header. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4054 oas-response-header-location (none leftover, not Location mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc9110#name-201-created", fetch1_ok="Exclusive 201 Location 400 leftover none.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#response-object", fetch2_ok="201 should include Location, leftover missing fails closed.")),
    (p(slug="oas-security-api-key-name", domain="oas-security-api-key-name-vs-leftover-generic-apikey", success=True, name="apiname2", stack="OpenAPI 3.1 named apiKey + Go", field="name", old="generic apikey leftover", new="named apiKey", fail_err="401: leftover generic apikey leftover after named apiKey-only", plan="named apiKey-only 401s leftover generic apikey leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4134 leftover-x-api-key-header (named vs generic leftover, not x-api-key mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch1_ok="apiKey name is required, leftover generic keys fail closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#fixed-fields-21", fetch2_ok="Exclusive named apiKey 401 leftover generic."),
     p(slug="leftover-generic-apikey", domain="leftover-generic-apikey-vs-oas-security-api-key-name", success=False, name="genkey", stack="OpenAPI leftover generic apikey + Java + TS", field="name", old="named apiKey", new="generic apikey leftover only", fail_err="401: leftover named apiKey after generic apikey leftover-only", plan="generic apikey leftover-only 401s leftover named apiKey. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4134 oas-security-api-key-query-name (generic leftover, not named mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#fixed-fields-21", fetch1_ok="Exclusive named apiKey 401 leftover generic.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch2_ok="apiKey name is required, leftover generic keys fail closed.")),
    (p(slug="oas-schema-type-array", domain="oas-schema-type-array-vs-leftover-scalar-payload", success=True, name="typarr", stack="OpenAPI 3.1 type=array + Go", field="type", old="scalar payload leftover", new="type array", fail_err="400: leftover scalar payload leftover after type array-only", plan="type array-only 400s leftover scalar payload leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4086 leftover-scalar-only (array vs scalar leftover, not type union mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/array", fetch1_ok="type=array is not leftover scalar payloads.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive type array 400 leftover scalar."),
     p(slug="leftover-scalar-payload", domain="leftover-scalar-payload-vs-oas-schema-type-array", success=False, name="scalarp", stack="OpenAPI leftover scalar payload + Java + TS", field="type", old="type array", new="scalar payload leftover only", fail_err="400: leftover type array after scalar payload leftover-only", plan="scalar payload leftover-only 400s leftover type array. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4086 oas-schema-type-array-union (scalar leftover, not union mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive type array 400 leftover scalar.", fetch2="https://json-schema.org/understanding-json-schema/reference/array", fetch2_ok="type=array is not leftover scalar payloads.")),
    (p(slug="oas-operation-requestbody-json", domain="oas-operation-requestbody-json-vs-leftover-form-request", success=True, name="rbjson", stack="OpenAPI 3.1 json requestBody + Go", field="content", old="form request leftover", new="json requestBody", fail_err="415: leftover form request leftover after json requestBody-only", plan="json requestBody-only 415s leftover form request leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4150 leftover-json-body-form (json body vs form leftover, not form mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#request-body-object", fetch1_ok="JSON requestBody is not leftover form posts.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch2_ok="Exclusive json body 415 leftover form."),
     p(slug="leftover-form-request", domain="leftover-form-request-vs-oas-operation-requestbody-json", success=False, name="rbform", stack="OpenAPI leftover form request + Java + TS", field="content", old="json requestBody", new="form request leftover only", fail_err="415: leftover json requestBody after form request leftover-only", plan="form request leftover-only 415s leftover json requestBody. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4150 oas-content-x-www-form (form leftover, not form mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch1_ok="Exclusive json body 415 leftover form.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#request-body-object", fetch2_ok="JSON requestBody is not leftover form posts.")),
    (p(slug="oas-server-url-with-vars", domain="oas-server-url-with-vars-vs-leftover-fixed-server-host", success=True, name="srvtpl", stack="OpenAPI 3.1 templated server url + Go", field="url", old="hardcoded host leftover", new="templated server url", fail_err="400: leftover hardcoded host leftover after templated server url-only", plan="templated server url-only 400s leftover hardcoded host leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4150 leftover-relative-server (template vs hardcoded leftover, not relative mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#server-object", fetch1_ok="Templated server urls are not leftover hardcoded hosts.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#server-variable-object", fetch2_ok="Exclusive templated url 400 leftover hardcoded."),
     p(slug="leftover-fixed-server-host", domain="leftover-fixed-server-host-vs-oas-server-url-with-vars", success=False, name="srvhard", stack="OpenAPI leftover hardcoded host + Java + TS", field="url", old="templated server url", new="hardcoded host leftover only", fail_err="400: leftover templated server url after hardcoded host leftover-only", plan="hardcoded host leftover-only 400s leftover templated server url. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4150 oas-servers-absolute-url (hardcoded leftover, not absolute mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#server-variable-object", fetch1_ok="Exclusive templated url 400 leftover hardcoded.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#server-object", fetch2_ok="Templated server urls are not leftover hardcoded hosts.")),
    (p(slug="oas-header-explode-true", domain="oas-header-explode-true-vs-leftover-header-no-explode", success=True, name="hdrexpl2", stack="OpenAPI 3.1 header explode true + Go", field="explode", old="header no explode leftover", new="header explode true", fail_err="400: leftover header no explode leftover after header explode true-only", plan="header explode true-only 400s leftover header no explode leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4086 leftover-header-explode (explode true vs none leftover, not explode mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch1_ok="Header explode true is not leftover unexploded headers.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch2_ok="Exclusive header explode 400 leftover none."),
     p(slug="leftover-header-no-explode", domain="leftover-header-no-explode-vs-oas-header-explode-true", success=False, name="hdrnx", stack="OpenAPI leftover header no explode + Java + TS", field="explode", old="header explode true", new="header no explode leftover only", fail_err="400: leftover header explode true after header no explode leftover-only", plan="header no explode leftover-only 400s leftover header explode true. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4086 oas-header-explode-false (none leftover, not false mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch1_ok="Exclusive header explode 400 leftover none.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch2_ok="Header explode true is not leftover unexploded headers.")),
    (p(slug="oas-xml-wrapped-true-array", domain="oas-xml-wrapped-true-array-vs-leftover-xml-bare-list", success=True, name="xmlw2", stack="OpenAPI 3.1 xml.wrapped true + Go", field="wrapped", old="bare xml list leftover", new="xml wrapped true", fail_err="415: leftover bare xml list leftover after xml wrapped true-only", plan="xml wrapped true-only 415s leftover bare xml list leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4118 leftover-bare-xml-array (wrapped true vs bare leftover, not wrapper mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#xml-object", fetch1_ok="xml.wrapped true is not leftover bare lists.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive wrapped 415 leftover bare."),
     p(slug="leftover-xml-bare-list", domain="leftover-xml-bare-list-vs-oas-xml-wrapped-true-array", success=False, name="xmlbare2", stack="OpenAPI leftover xml bare list + Java + TS", field="wrapped", old="xml wrapped true", new="bare xml list leftover only", fail_err="415: leftover xml wrapped true after bare xml list leftover-only", plan="bare xml list leftover-only 415s leftover xml wrapped true. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4118 oas-xml-array-wrapper-name (bare leftover, not wrapper mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive wrapped 415 leftover bare.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#xml-object", fetch2_ok="xml.wrapped true is not leftover bare lists.")),
    (p(slug="oas-format-idn-email-addr", domain="oas-format-idn-email-addr-vs-leftover-ascii-email-only", success=True, name="emidn", stack="OpenAPI 3.1 format=idn-email + Go", field="format", old="ascii email leftover", new="idn-email format", fail_err="400: leftover ascii email leftover after idn-email format-only", plan="idn-email format-only 400s leftover ascii email leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4054 leftover-puny-email (idn-email vs ascii leftover, not puny mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/string#idn-email", fetch1_ok="format=idn-email is not leftover ASCII-only emails.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="Exclusive idn-email 400 leftover ascii."),
     p(slug="leftover-ascii-email-only", domain="leftover-ascii-email-only-vs-oas-format-idn-email-addr", success=False, name="emasc2", stack="OpenAPI leftover ascii email only + Java + TS", field="format", old="idn-email format", new="ascii email leftover only", fail_err="400: leftover idn-email format after ascii email leftover-only", plan="ascii email leftover-only 400s leftover idn-email format. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4054 oas-format-idn-email-rfc (ascii leftover, not idn mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="Exclusive idn-email 400 leftover ascii.", fetch2="https://json-schema.org/understanding-json-schema/reference/string#idn-email", fetch2_ok="format=idn-email is not leftover ASCII-only emails.")),
    (p(slug="oas-callback-ref-component", domain="oas-callback-ref-component-vs-leftover-inline-callback-op", success=True, name="cbref", stack="OpenAPI 3.1 callback $ref + Go", field="callbacks", old="inline callback leftover", new="components callback ref", fail_err="400: leftover inline callback leftover after components callback ref-only", plan="components callback ref-only 400s leftover inline callback leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r3993 leftover-inline-callbacks (callback ref vs inline leftover, not components mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#callback-object", fetch1_ok="Callback $ref reuses components, leftover inline is not that.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#components-object", fetch2_ok="Exclusive callback ref 400 leftover inline."),
     p(slug="leftover-inline-callback-op", domain="leftover-inline-callback-op-vs-oas-callback-ref-component", success=False, name="cbinl", stack="OpenAPI leftover inline callback + Java + TS", field="callbacks", old="components callback ref", new="inline callback leftover only", fail_err="400: leftover components callback ref after inline callback leftover-only", plan="inline callback leftover-only 400s leftover components callback ref. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r3993 oas-components-callbacks (inline leftover, not components mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#components-object", fetch1_ok="Exclusive callback ref 400 leftover inline.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#callback-object", fetch2_ok="Callback $ref reuses components, leftover inline is not that.")),
    (p(slug="oas-info-contact-email-rfc", domain="oas-info-contact-email-rfc-vs-leftover-unvalidated-contact", success=True, name="ctem2", stack="OpenAPI 3.1 contact.email RFC + Go", field="email", old="unvalidated contact leftover", new="contact email rfc", fail_err="400: leftover unvalidated contact leftover after contact email rfc-only", plan="contact email rfc-only 400s leftover unvalidated contact leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r3963 leftover-missing-contact (rfc email vs unvalidated leftover, not missing mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#contact-object", fetch1_ok="contact.email is addr-spec, leftover unvalidated fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#info-object", fetch2_ok="Exclusive contact email 400 leftover unvalidated."),
     p(slug="leftover-unvalidated-contact", domain="leftover-unvalidated-contact-vs-oas-info-contact-email-rfc", success=False, name="ctunv", stack="OpenAPI leftover unvalidated contact + Java + TS", field="email", old="contact email rfc", new="unvalidated contact leftover only", fail_err="400: leftover contact email rfc after unvalidated contact leftover-only", plan="unvalidated contact leftover-only 400s leftover contact email rfc. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r3963 oas-info-contact-email (unvalidated leftover, not email mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#info-object", fetch1_ok="Exclusive contact email 400 leftover unvalidated.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#contact-object", fetch2_ok="contact.email is addr-spec, leftover unvalidated fails closed.")),
    (p(slug="oas-schema-required-array", domain="oas-schema-required-array-vs-leftover-all-optional-fields", success=True, name="reqarr", stack="OpenAPI 3.1 required array + Go", field="required", old="all optional leftover", new="required array", fail_err="400: leftover all optional leftover after required array-only", plan="required array-only 400s leftover all optional leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4070 leftover-independent-fields (required array vs all-optional leftover, not dependent mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/object#required", fetch1_ok="required lists fields, leftover all-optional fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive required array 400 leftover optional."),
     p(slug="leftover-all-optional-fields", domain="leftover-all-optional-fields-vs-oas-schema-required-array", success=False, name="allopt", stack="OpenAPI leftover all optional fields + Java + TS", field="required", old="required array", new="all optional leftover only", fail_err="400: leftover required array after all optional leftover-only", plan="all optional leftover-only 400s leftover required array. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4070 oas-schema-dependent-required (all-optional leftover, not dependent mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive required array 400 leftover optional.", fetch2="https://json-schema.org/understanding-json-schema/reference/object#required", fetch2_ok="required lists fields, leftover all-optional fails closed.")),
    (p(slug="oas-parameter-style-label-path", domain="oas-parameter-style-label-path-vs-leftover-path-dot-join", success=True, name="plab", stack="OpenAPI 3.1 path style=label + Go", field="style", old="dot join leftover", new="path label style", fail_err="400: leftover dot join leftover after path label style-only", plan="path label style-only 400s leftover dot join leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r3561 style-label-path (label vs dot leftover, not mill reuse)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch1_ok="style=label is not leftover dotted path params.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="Exclusive path label 400 leftover dots."),
     p(slug="leftover-path-dot-join", domain="leftover-path-dot-join-vs-oas-parameter-style-label-path", success=False, name="pdot", stack="OpenAPI leftover path dot join + Java + TS", field="style", old="path label style", new="dot join leftover only", fail_err="400: leftover path label style after dot join leftover-only", plan="dot join leftover-only 400s leftover path label style. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r3561 style-label-path (dot leftover, not mill reuse)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="Exclusive path label 400 leftover dots.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch2_ok="style=label is not leftover dotted path params.")),
    (p(slug="oas-security-oauth2-scopes-map", domain="oas-security-oauth2-scopes-map-vs-leftover-scope-csv", success=True, name="scmap", stack="OpenAPI 3.1 oauth2 scopes map + Go", field="scopes", old="scope csv leftover", new="oauth2 scopes map", fail_err="401: leftover scope csv leftover after oauth2 scopes map-only", plan="oauth2 scopes map-only 401s leftover scope csv leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4086 leftover-unscoped-token (scopes map vs csv leftover, not unscoped mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#oauth-flow-object", fetch1_ok="scopes is a map, leftover CSV scopes fail closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch2_ok="Exclusive scopes map 401 leftover csv."),
     p(slug="leftover-scope-csv", domain="leftover-scope-csv-vs-oas-security-oauth2-scopes-map", success=False, name="sccsv", stack="OpenAPI leftover scope csv + Java + TS", field="scopes", old="oauth2 scopes map", new="scope csv leftover only", fail_err="401: leftover oauth2 scopes map after scope csv leftover-only", plan="scope csv leftover-only 401s leftover oauth2 scopes map. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4086 oas-security-oauth2-scopes-required (csv leftover, not required mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch1_ok="Exclusive scopes map 401 leftover csv.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#oauth-flow-object", fetch2_ok="scopes is a map, leftover CSV scopes fail closed.")),
    (p(slug="oas-schema-format-float", domain="oas-schema-format-float-vs-leftover-untyped-number-scale", success=True, name="fmtflt", stack="OpenAPI 3.1 format=float + Go", field="format", old="unbounded number leftover", new="format float", fail_err="400: leftover unbounded number leftover after format float-only", plan="format float-only 400s leftover unbounded number leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4182 leftover-float32-only (float vs unbounded leftover, not double mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="format=float is IEEE 754 binary32, leftover unbounded fails closed.", fetch2="https://json-schema.org/understanding-json-schema/reference/numeric", fetch2_ok="Exclusive float 400 leftover unbounded."),
     p(slug="leftover-untyped-number-scale", domain="leftover-untyped-number-scale-vs-oas-schema-format-float", success=False, name="unbnum", stack="OpenAPI leftover unbounded number + Java + TS", field="format", old="format float", new="unbounded number leftover only", fail_err="400: leftover format float after unbounded number leftover-only", plan="unbounded number leftover-only 400s leftover format float. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4182 oas-schema-format-double (unbounded leftover, not double mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/numeric", fetch1_ok="Exclusive float 400 leftover unbounded.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="format=float is IEEE 754 binary32, leftover unbounded fails closed.")),
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
    print(json.dumps({"round": round_n, "idx": idx, "ids": [e1["id"], e2["id"]], "catalog": "r4198"}))


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
