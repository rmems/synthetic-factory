#!/usr/bin/env python3
"""Fifth unique OpenAPI-drift ACM catalog after r4054 mill. Fast slug load."""
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
    (p(slug="oas-schema-exclusive-maximum", domain="oas-exmax-vs-inclusive-max", success=True, name="exmax", stack="OpenAPI 3.1 exclusiveMaximum + Go", field="exclusiveMaximum", old="inclusive max leftover", new="exclusiveMaximum", fail_err="400: leftover inclusive max after exclusiveMaximum-only", plan="exclusiveMaximum-only 400s leftover inclusive. Dual-read inclusive for one release.", residual="validator still inclusive leftover; drop after validator 5", vs="r3561 exclusive-minimum-numeric (exclusiveMaximum vs inclusive leftover, not exclusiveMinimum)", fetch1="https://json-schema.org/understanding-json-schema/reference/numeric#exclusivemaximum", fetch1_ok="exclusiveMaximum is not leftover inclusive maximum.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive exclusiveMaximum 400 leftover inclusive."),
     p(slug="leftover-inclusive-max", domain="inclusive-max-vs-oas-exmax", success=False, name="incmax", stack="OpenAPI leftover inclusive max + Java + TS", field="maximum", old="exclusiveMaximum", new="inclusive max leftover only", fail_err="400: leftover exclusiveMaximum after inclusive-only", plan="Inclusive-only 400s leftover exclusiveMaximum. Freeze exclusiveMaximum, spec inclusive leftover.", residual="handoff: keep exclusiveMaximum or force inclusive leftover", vs="r3561 exclusive-minimum-numeric (inclusive leftover, not exclusiveMinimum)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Inclusive maximum is not exclusiveMaximum.", fetch2="https://json-schema.org/understanding-json-schema/reference/numeric#exclusivemaximum", fetch2_ok="Exclusive inclusive max 400 leftover exclusiveMaximum.")),
    (p(slug="oas-json-schema-vocabulary", domain="oas-vocab-vs-draft7", success=True, name="vocab", stack="OpenAPI 3.1 $vocabulary + Go", field="$vocabulary", old="draft7 vocab leftover", new="schema vocabulary", fail_err="400: leftover draft7 vocab after $vocabulary-only", plan="$vocabulary-only 400s leftover draft7. Dual-read draft7 for one release.", residual="codegen still draft7 leftover; drop after codegen 6", vs="r3561 json-schema-dialect-uri ($vocabulary vs draft7 leftover, not dialect mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/schema#vocabulary", fetch1_ok="$vocabulary declares vocabularies, leftover draft-07 is not that.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive $vocabulary 400 leftover draft7."),
     p(slug="leftover-draft7-vocab", domain="draft7-vs-oas-vocab", success=False, name="d7vocab", stack="OpenAPI leftover draft7 vocab + Java + TS", field="$schema", old="schema vocabulary", new="draft7 vocab leftover only", fail_err="400: leftover $vocabulary after draft7-only", plan="Draft7-only 400s leftover $vocabulary. Freeze $vocabulary, spec draft7 leftover.", residual="handoff: keep $vocabulary or force draft7 leftover", vs="r3561 json-schema-dialect-uri (draft7 leftover, not dialect)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Draft-07 leftover is not $vocabulary.", fetch2="https://json-schema.org/understanding-json-schema/reference/schema#vocabulary", fetch2_ok="Exclusive draft7 400 leftover $vocabulary.")),
    (p(slug="oas-response-default", domain="oas-default-resp-vs-listed-only", success=True, name="rdef", stack="OpenAPI 3.1 responses default + Go", field="default", old="listed status only leftover", new="default response", fail_err="400: leftover listed-only after default-only", plan="responses.default-only 400s leftover listed-only. Dual-omit default for one release.", residual="sdk still listed leftover; drop after sdk 5", vs="r3978 leftover-inline-responses (default vs listed leftover, not components.responses)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#responses-object", fetch1_ok="default covers undeclared status codes, leftover listed-only fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#response-object", fetch2_ok="Exclusive default response 400 leftover listed-only."),
     p(slug="leftover-listed-status-only", domain="listed-only-vs-oas-default-resp", success=False, name="listed", stack="OpenAPI leftover listed status + Java + TS", field="responses", old="default response", new="listed status only leftover only", fail_err="400: leftover responses.default after listed-only", plan="Listed-only 400s leftover responses.default. Freeze default, spec listed leftover.", residual="handoff: keep responses.default or force listed leftover", vs="r3978 oas-components-responses (listed leftover, not components mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#response-object", fetch1_ok="Listed-only statuses are not default.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#responses-object", fetch2_ok="Exclusive listed-only 400 leftover default.")),
    (p(slug="oas-components-path-items", domain="oas-comp-pathitems-vs-inline", success=True, name="cpath", stack="OpenAPI 3.1 components.pathItems + Go", field="pathItems", old="inline pathitem leftover", new="components pathItems", fail_err="400: leftover inline pathitem after components-only", plan="components.pathItems-only 400s leftover inline. Dual-read inline for one release.", residual="sdk still inline leftover; drop after sdk 6", vs="r3993 leftover-inline-callbacks (pathItems vs inline leftover, not callbacks)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#components-object", fetch1_ok="components.pathItems reuse Path Item Objects.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#path-item-object", fetch2_ok="Exclusive components.pathItems 400 leftover inline."),
     p(slug="leftover-inline-pathitem", domain="inline-pathitem-vs-oas-comp-pathitems", success=False, name="ipath", stack="OpenAPI leftover inline pathitem + Java + TS", field="paths", old="components pathItems", new="inline pathitem leftover only", fail_err="400: leftover components.pathItems after inline-only", plan="Inline-only 400s leftover components.pathItems. Freeze components, spec inline leftover.", residual="handoff: keep components.pathItems or force inline leftover", vs="r3993 oas-components-callbacks (inline leftover, not callbacks mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#path-item-object", fetch1_ok="Inline path items are not components.pathItems.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#components-object", fetch2_ok="Exclusive inline pathitem 400 leftover components.")),
    (p(slug="oas-schema-dependent-required", domain="oas-depreq-vs-independent", success=True, name="depreq", stack="OpenAPI 3.1 dependentRequired + Go", field="dependentRequired", old="independent fields leftover", new="dependentRequired", fail_err="400: leftover independent after dependentRequired-only", plan="dependentRequired-only 400s leftover independent. Dual-read independent for one release.", residual="form still independent leftover; drop after form 5", vs="wrap dependentrequired-billing (dependentRequired vs independent leftover, not billing cartesian)", fetch1="https://json-schema.org/understanding-json-schema/reference/conditionals#dependentrequired", fetch1_ok="dependentRequired ties sibling fields, leftover independent fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive dependentRequired 400 leftover independent."),
     p(slug="leftover-independent-fields", domain="independent-vs-oas-depreq", success=False, name="indep", stack="OpenAPI leftover independent fields + Java + TS", field="required", old="dependentRequired", new="independent fields leftover only", fail_err="400: leftover dependentRequired after independent-only", plan="Independent-only 400s leftover dependentRequired. Freeze dependentRequired, spec independent leftover.", residual="handoff: keep dependentRequired or force independent leftover", vs="wrap dependentrequired-billing (independent leftover, not billing cartesian)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Independent leftover fields are not dependentRequired.", fetch2="https://json-schema.org/understanding-json-schema/reference/conditionals#dependentrequired", fetch2_ok="Exclusive independent 400 leftover dependentRequired.")),
    (p(slug="oas-format-time-offset", domain="oas-time-offset-vs-naive-time", success=True, name="tzo", stack="OpenAPI 3.1 format=time with offset + Go", field="format", old="naive time leftover", new="time with offset", fail_err="400: leftover naive time after offset-only", plan="time-offset-only 400s leftover naive. Dual-read naive for one release.", residual="batch still naive leftover; drop after batch 5", vs="r3915 oas-format-time (offset time vs naive leftover, not time-only mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/string#time", fetch1_ok="format=time with offset is not leftover naive clock times.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="Exclusive time offset 400 leftover naive."),
     p(slug="leftover-naive-time", domain="naive-time-vs-oas-time-offset", success=False, name="naive", stack="OpenAPI leftover naive time + Java + TS", field="time", old="time with offset", new="naive time leftover only", fail_err="400: leftover time-offset after naive-only", plan="Naive-only 400s leftover time-offset. Freeze offset, spec naive leftover.", residual="handoff: keep time offset or force naive leftover", vs="r3915 leftover-date-only (naive leftover, not date-only mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="Naive times are not format=time with offset.", fetch2="https://json-schema.org/understanding-json-schema/reference/string#time", fetch2_ok="Exclusive naive time 400 leftover offset.")),
    (p(slug="oas-encoding-headers", domain="oas-enc-headers-vs-no-part-headers", success=True, name="enchdr", stack="OpenAPI 3.1 encoding.headers + Go", field="headers", old="part no headers leftover", new="encoding headers", fail_err="415: leftover part-no-headers after encoding-headers-only", plan="encoding.headers-only 415s leftover no-part-headers. Dual-omit part headers for one release.", residual="ingest still no-headers leftover; drop after ingest 6", vs="r3867 leftover-prop-mediatype (encoding.headers vs none leftover, not property media)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#encoding-object", fetch1_ok="encoding.headers describes per-property headers, leftover missing fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch2_ok="Exclusive encoding.headers 415 leftover none."),
     p(slug="leftover-part-no-headers", domain="no-part-headers-vs-oas-enc-headers", success=False, name="nopart", stack="OpenAPI leftover part no headers + Java + TS", field="headers", old="encoding headers", new="part no headers leftover only", fail_err="415: leftover encoding.headers after none-only", plan="None-only 415s leftover encoding.headers. Freeze headers, spec none leftover.", residual="handoff: keep encoding.headers or force none leftover", vs="r4038 leftover-encoding-simple (no-headers leftover, not encoding simple)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch1_ok="Missing part headers are not encoding.headers.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#encoding-object", fetch2_ok="Exclusive no-part-headers 415 leftover encoding.headers.")),
    (p(slug="oas-link-operation-ref", domain="oas-opref-vs-opid-only", success=True, name="opref", stack="OpenAPI 3.1 link operationRef + Go", field="operationRef", old="opid only leftover", new="link operationRef", fail_err="400: leftover opid-only after operationRef-only", plan="operationRef-only 400s leftover operationId. Dual-read operationId for one release.", residual="sdk still opid leftover; drop after sdk 5", vs="wrap link-operationid-rename (operationRef vs opid leftover, not rename cartesian)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#link-object", fetch1_ok="operationRef and operationId are mutually exclusive.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#runtime-expressions", fetch2_ok="Exclusive operationRef 400 leftover operationId."),
     p(slug="leftover-opid-only-link", domain="opid-only-vs-oas-opref", success=False, name="opidlnk", stack="OpenAPI leftover opid-only link + Java + TS", field="operationId", old="link operationRef", new="opid only leftover only", fail_err="400: leftover operationRef after opid-only", plan="Opid-only 400s leftover operationRef. Freeze operationRef, spec opid leftover.", residual="handoff: keep operationRef or force opid leftover", vs="wrap link-operationid-rename (opid leftover, not rename cartesian)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#runtime-expressions", fetch1_ok="operationId-only links are not operationRef.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#link-object", fetch2_ok="Exclusive opid-only 400 leftover operationRef.")),
    (p(slug="oas-xml-name-override", domain="oas-xml-name-vs-property-name", success=True, name="xmlov", stack="OpenAPI 3.1 xml.name override + Go", field="name", old="property name leftover", new="xml name override", fail_err="415: leftover property name after xml.name-only", plan="xml.name-only 415s leftover property name. Dual-read property for one release.", residual="batch still property leftover; drop after batch 5", vs="r4007 leftover-element-name-xml (xml.name vs property leftover, not element name mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#xml-object", fetch1_ok="xml.name overrides the property name in XML.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive xml.name 415 leftover property name."),
     p(slug="leftover-property-name-xml", domain="property-name-vs-oas-xml-name", success=False, name="propxml", stack="OpenAPI leftover property name xml + Java + TS", field="name", old="xml name override", new="property name leftover only", fail_err="415: leftover xml.name after property-only", plan="Property-only 415s leftover xml.name. Freeze xml.name, spec property leftover.", residual="handoff: keep xml.name or force property leftover", vs="r4007 oas-xml-attribute-name (property leftover, not attribute name mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Property names are not xml.name.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#xml-object", fetch2_ok="Exclusive property name 415 leftover xml.name.")),
    (p(slug="oas-schema-if-then", domain="oas-if-then-vs-unconditional", success=True, name="ifthen", stack="OpenAPI 3.1 if/then + Go", field="if", old="unconditional leftover", new="if then", fail_err="400: leftover unconditional after if-then-only", plan="if-then-only 400s leftover unconditional. Dual-read unconditional for one release.", residual="validator still unconditional leftover; drop after validator 6", vs="r3561 json-schema-if-then-else (if/then vs unconditional leftover, not if-then-else mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/conditionals#ifthenelse", fetch1_ok="if/then applies a subschema conditionally, leftover unconditional is not that.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive if/then 400 leftover unconditional."),
     p(slug="leftover-unconditional", domain="unconditional-vs-oas-if-then", success=False, name="uncond", stack="OpenAPI leftover unconditional + Java + TS", field="properties", old="if then", new="unconditional leftover only", fail_err="400: leftover if/then after unconditional-only", plan="Unconditional-only 400s leftover if/then. Freeze if/then, spec unconditional leftover.", residual="handoff: keep if/then or force unconditional leftover", vs="r3561 json-schema-if-then-else (unconditional leftover, not if-then-else)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Unconditional leftover is not if/then.", fetch2="https://json-schema.org/understanding-json-schema/reference/conditionals#ifthenelse", fetch2_ok="Exclusive unconditional 400 leftover if/then.")),
    (p(slug="oas-content-application-jose", domain="oas-jose-vs-plain-jwt-header", success=True, name="jose", stack="OpenAPI 3.1 application/jose + Go", field="content", old="plain jwt header leftover", new="application jose", fail_err="415: leftover plain jwt after jose-only", plan="application/jose-only 415s leftover plain jwt. Dual-read jwt for one release.", residual="edge still jwt leftover; drop after edge 6", vs="r3561 content-type-jose (application/jose vs plain jwt leftover, not jose mill reuse)", fetch1="https://datatracker.ietf.org/doc/html/rfc7515", fetch1_ok="application/jose is compact JWS/JWE, leftover raw JWT headers fail closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch2_ok="Exclusive application/jose 415 leftover plain jwt."),
     p(slug="leftover-plain-jwt-header", domain="plain-jwt-vs-oas-jose", success=False, name="pjwt", stack="OpenAPI leftover plain jwt header + Java + TS", field="Authorization", old="application jose", new="plain jwt header leftover only", fail_err="415: leftover application/jose after jwt-only", plan="Jwt-only 415s leftover application/jose. Freeze jose, spec jwt leftover.", residual="handoff: keep application/jose or force jwt leftover", vs="r3561 content-type-jose (plain jwt leftover, not jose mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch1_ok="Plain JWT headers are not application/jose.", fetch2="https://datatracker.ietf.org/doc/html/rfc7515", fetch2_ok="Exclusive plain jwt 415 leftover jose.")),
    (p(slug="oas-format-json-pointer-strict", domain="oas-jsonptr-vs-dot-path", success=True, name="jptr", stack="OpenAPI 3.1 format=json-pointer + Go", field="format", old="dot path leftover", new="json pointer", fail_err="400: leftover dot-path after json-pointer-only", plan="json-pointer-only 400s leftover dot-path. Dual-read dots for one release.", residual="sdk still dots leftover; drop after sdk 5", vs="r3561 format-json-pointer (strict json-pointer vs dot leftover, not format mill reuse)", fetch1="https://json-schema.org/understanding-json-schema/reference/string#json-pointer", fetch1_ok="format=json-pointer is RFC 6901, leftover dotted paths fail closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="Exclusive json-pointer 400 leftover dot-path."),
     p(slug="leftover-dot-path", domain="dot-path-vs-oas-jsonptr", success=False, name="dotp", stack="OpenAPI leftover dot path + Java + TS", field="path", old="json pointer", new="dot path leftover only", fail_err="400: leftover json-pointer after dots-only", plan="Dots-only 400s leftover json-pointer. Freeze pointer, spec dots leftover.", residual="handoff: keep json-pointer or force dots leftover", vs="r3561 format-json-pointer (dot leftover, not format mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="Dotted paths are not format=json-pointer.", fetch2="https://json-schema.org/understanding-json-schema/reference/string#json-pointer", fetch2_ok="Exclusive dot-path 400 leftover json-pointer.")),
    (p(slug="oas-format-rel-json-pointer", domain="oas-relptr-vs-absolute-pointer", success=True, name="relptr", stack="OpenAPI 3.1 relative json-pointer + Go", field="format", old="absolute pointer leftover", new="relative json pointer", fail_err="400: leftover absolute pointer after relative-only", plan="relative-json-pointer-only 400s leftover absolute. Dual-read absolute for one release.", residual="patch still absolute leftover; drop after patch 5", vs="r3561 format-relative-json-pointer (relative vs absolute leftover, not format mill reuse)", fetch1="https://json-schema.org/understanding-json-schema/reference/string#relative-json-pointer", fetch1_ok="relative-json-pointer is not leftover absolute pointers.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="Exclusive relative pointer 400 leftover absolute."),
     p(slug="leftover-absolute-pointer", domain="absolute-vs-oas-relptr", success=False, name="absptr", stack="OpenAPI leftover absolute pointer + Java + TS", field="path", old="relative json pointer", new="absolute pointer leftover only", fail_err="400: leftover relative-json-pointer after absolute-only", plan="Absolute-only 400s leftover relative-json-pointer. Freeze relative, spec absolute leftover.", residual="handoff: keep relative pointer or force absolute leftover", vs="r3561 format-relative-json-pointer (absolute leftover, not format mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="Absolute leftover pointers are not relative-json-pointer.", fetch2="https://json-schema.org/understanding-json-schema/reference/string#relative-json-pointer", fetch2_ok="Exclusive absolute pointer 400 leftover relative.")),
    (p(slug="oas-security-openidconnect", domain="oas-oidc-vs-oauth-oidc", success=True, name="oidc", stack="OpenAPI 3.1 openIdConnect + Go", field="openIdConnectUrl", old="oauth oidc leftover", new="openIdConnect", fail_err="401: leftover oauth-oidc after openIdConnect-only", plan="openIdConnect-only 401s leftover oauth-oidc. Dual-accept oauth for one release.", residual="idp still oauth leftover; drop after idp 6", vs="r3867 leftover-oauth-implicit-flow (openIdConnect vs oauth leftover, not implicit mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch1_ok="openIdConnectUrl is not leftover generic oauth.", fetch2="https://openid.net/specs/openid-connect-discovery-1_0.html", fetch2_ok="Exclusive openIdConnect 401 leftover oauth-oidc."),
     p(slug="leftover-oauth-oidc", domain="oauth-oidc-vs-oas-oidc", success=False, name="oautoidc", stack="OpenAPI leftover oauth oidc + Java + TS", field="type", old="openIdConnect", new="oauth oidc leftover only", fail_err="401: leftover openIdConnect after oauth-only", plan="Oauth-only 401s leftover openIdConnect. Freeze openIdConnect, spec oauth leftover.", residual="handoff: keep openIdConnect or force oauth leftover", vs="r3867 oas-oidc-scheme (oauth leftover, not oidc mill reuse)", fetch1="https://openid.net/specs/openid-connect-discovery-1_0.html", fetch1_ok="Generic oauth leftover is not openIdConnect.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch2_ok="Exclusive oauth-oidc 401 leftover openIdConnect.")),
    (p(slug="oas-callback-expression-runtime", domain="oas-runtime-cb-vs-static-url", success=True, name="cbrun", stack="OpenAPI 3.1 callback runtime expr + Go", field="callbacks", old="static callback url leftover", new="callback runtime expression", fail_err="400: leftover static callback after runtime-only", plan="runtime-callback-only 400s leftover static url. Dual-read static for one release.", residual="bus still static leftover; drop after bus 6", vs="r3947 leftover-notify-post (runtime expr vs static leftover, not notify mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#callback-object", fetch1_ok="Callback keys are runtime expressions, leftover static urls fail closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#runtime-expressions", fetch2_ok="Exclusive runtime callback 400 leftover static."),
     p(slug="leftover-static-callback-url", domain="static-cb-vs-oas-runtime-cb", success=False, name="cbstat", stack="OpenAPI leftover static callback + Java + TS", field="url", old="callback runtime expression", new="static callback url leftover only", fail_err="400: leftover runtime callback after static-only", plan="Static-only 400s leftover runtime callback. Freeze runtime, spec static leftover.", residual="handoff: keep runtime callback or force static leftover", vs="r3947 oas-callback-pathitem (static leftover, not Path Item mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#runtime-expressions", fetch1_ok="Static leftover urls are not runtime expressions.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#callback-object", fetch2_ok="Exclusive static callback 400 leftover runtime.")),
    (p(slug="oas-info-terms-of-service-url", domain="oas-tos-vs-missing-tos", success=True, name="tosurl", stack="OpenAPI 3.1 info.termsOfService + Go", field="termsOfService", old="missing tos leftover", new="terms of service url", fail_err="400: leftover missing tos after tos-only", plan="termsOfService-only 400s leftover missing. Dual-omit tos for one release.", residual="portal still missing leftover; drop after portal 4", vs="r3931 leftover-missing-title (tos vs missing leftover, not title mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#info-object", fetch1_ok="termsOfService is a URL, leftover missing tos fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#fixed-fields", fetch2_ok="Exclusive termsOfService 400 leftover missing."),
     p(slug="leftover-missing-tos", domain="missing-tos-vs-oas-tos", success=False, name="notos", stack="OpenAPI leftover missing tos + Java + TS", field="termsOfService", old="terms of service url", new="missing tos leftover only", fail_err="400: leftover termsOfService after missing-only", plan="Missing-only 400s leftover termsOfService. Freeze tos, spec missing leftover.", residual="handoff: keep termsOfService or force missing leftover", vs="r3931 oas-info-terms-url (missing leftover, not terms-url mill reuse)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#fixed-fields", fetch1_ok="Missing tos is not termsOfService.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#info-object", fetch2_ok="Exclusive missing tos 400 leftover termsOfService.")),
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
    print(json.dumps({"round": round_n, "idx": idx, "ids": [e1["id"], e2["id"]], "catalog": "r4070"}))


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
