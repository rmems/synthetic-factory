#!/usr/bin/env python3
"""Seventh unique OpenAPI-drift ACM catalog after r4086 mill. Fast slug load."""
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
    (p(slug="oas-response-header-cachecontrol", domain="oas-cachecontrol-vs-expires", success=True, name="ccntrl", stack="OpenAPI 3.1 Cache-Control header + Go", field="Cache-Control", old="Expires header leftover", new="Cache-Control header", fail_err="400: leftover Expires after Cache-Control-only", plan="Cache-Control-only 400s leftover Expires. Dual-emit Expires for one release.", residual="cdn still Expires leftover; drop after cdn 6", vs="r4023 leftover-retry-body (Cache-Control vs Expires leftover, not Retry-After mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc9111#name-cache-control", fetch1_ok="Cache-Control is not leftover Expires.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#response-object", fetch2_ok="Exclusive Cache-Control 400 leftover Expires."),
     p(slug="leftover-expires-header", domain="expires-vs-oas-cachecontrol", success=False, name="expir", stack="OpenAPI leftover Expires header + Java + TS", field="Expires", old="Cache-Control header", new="Expires header leftover only", fail_err="400: leftover Cache-Control after Expires-only", plan="Expires-only 400s leftover Cache-Control. Freeze Cache-Control, spec Expires leftover.", residual="handoff: keep Cache-Control or force Expires leftover", vs="r4023 oas-response-header-retryafter (Expires leftover, not Retry-After)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#response-object", fetch1_ok="Expires leftover is not Cache-Control.", fetch2="https://datatracker.ietf.org/doc/html/rfc9111#name-cache-control", fetch2_ok="Exclusive Expires 400 leftover Cache-Control.")),
    (p(slug="oas-servers-http-https-split", domain="oas-split-scheme-vs-mixed-url", success=True, name="srvsplit", stack="OpenAPI 3.1 split http/https servers + Go", field="url", old="mixed scheme url leftover", new="split http https servers", fail_err="400: leftover mixed-scheme after split-only", plan="split-scheme-only 400s leftover mixed. Dual-accept mixed for one release.", residual="mesh still mixed leftover; drop after mesh 6", vs="r4054 leftover-http-server (split schemes vs mixed leftover, not https-only mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#oasServers", fetch1_ok="Separate http and https server objects are not leftover mixed scheme urls.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#server-object", fetch2_ok="Exclusive split scheme 400 leftover mixed."),
     p(slug="leftover-mixed-scheme-url", domain="mixed-scheme-vs-oas-split", success=False, name="srvmix", stack="OpenAPI leftover mixed scheme url + Java + TS", field="url", old="split http https servers", new="mixed scheme url leftover only", fail_err="400: leftover split scheme after mixed-only", plan="Mixed-only 400s leftover split scheme. Freeze split, spec mixed leftover.", residual="handoff: keep split scheme or force mixed leftover", vs="r4054 oas-servers-https-only (mixed leftover, not https-only mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#server-object", fetch1_ok="Mixed leftover urls are not split servers.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#oasServers", fetch2_ok="Exclusive mixed scheme 400 leftover split.")),
    (p(slug="oas-schema-content-encoding-base32", domain="oas-base32-vs-hex-bytes", success=True, name="b32", stack="OpenAPI 3.1 contentEncoding base32 + Go", field="contentEncoding", old="hex bytes leftover", new="base32 encoding", fail_err="415: leftover hex bytes after base32-only", plan="base32-only 415s leftover hex. Dual-read hex for one release.", residual="store still hex leftover; drop after store 6", vs="r4054 leftover-raw-binary (base32 vs hex leftover, not quoted-printable mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/non_json_data#contentencoding", fetch1_ok="contentEncoding=base32 is not leftover hex bytes.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive base32 415 leftover hex."),
     p(slug="leftover-hex-bytes", domain="hex-bytes-vs-oas-base32", success=False, name="hexb", stack="OpenAPI leftover hex bytes + Java + TS", field="contentEncoding", old="base32 encoding", new="hex bytes leftover only", fail_err="415: leftover base32 after hex-only", plan="Hex-only 415s leftover base32. Freeze base32, spec hex leftover.", residual="handoff: keep base32 or force hex leftover", vs="r4054 oas-content-encoding-quoted-printable (hex leftover, not qp mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Hex leftover bytes are not base32.", fetch2="https://json-schema.org/understanding-json-schema/reference/non_json_data#contentencoding", fetch2_ok="Exclusive hex bytes 415 leftover base32.")),
    (p(slug="oas-security-http-negotiate", domain="oas-negotiate-vs-ntlm", success=True, name="negauth", stack="OpenAPI 3.1 HTTP Negotiate + Go", field="scheme", old="ntlm auth leftover", new="http negotiate", fail_err="401: leftover ntlm after negotiate-only", plan="Negotiate-only 401s leftover ntlm. Dual-accept ntlm for one release.", residual="edge still ntlm leftover; drop after edge 7", vs="r3947 leftover-http-basic (negotiate vs ntlm leftover, not basic mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch1_ok="HTTP Negotiate is not leftover NTLM.", fetch2="https://datatracker.ietf.org/doc/html/rfc4559", fetch2_ok="Exclusive negotiate 401 leftover ntlm."),
     p(slug="leftover-ntlm-auth", domain="ntlm-vs-oas-negotiate", success=False, name="ntlma", stack="OpenAPI leftover ntlm auth + Java + TS", field="scheme", old="http negotiate", new="ntlm auth leftover only", fail_err="401: leftover negotiate after ntlm-only", plan="Ntlm-only 401s leftover negotiate. Freeze negotiate, spec ntlm leftover.", residual="handoff: keep negotiate or force ntlm leftover", vs="r3947 oas-security-http-bearer (ntlm leftover, not bearer mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc4559", fetch1_ok="NTLM leftover is not Negotiate.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch2_ok="Exclusive ntlm 401 leftover negotiate.")),
    (p(slug="oas-content-application-yaml", domain="oas-yaml-vs-json-only", success=True, name="appyaml", stack="OpenAPI 3.1 application/yaml + Go", field="content", old="json only leftover", new="application yaml", fail_err="415: leftover json-only after yaml-only", plan="application/yaml-only 415s leftover json. Dual-read json for one release.", residual="sdk still json leftover; drop after sdk 5", vs="r3561 accept-application-yaml (yaml content vs json leftover, not accept mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch1_ok="application/yaml is not leftover json-only bodies.", fetch2="https://www.rfc-editor.org/rfc/rfc9512.html", fetch2_ok="Exclusive application/yaml 415 leftover json."),
     p(slug="leftover-json-only-body", domain="json-only-vs-oas-yaml", success=False, name="jsononly", stack="OpenAPI leftover json-only body + Java + TS", field="content", old="application yaml", new="json only leftover only", fail_err="415: leftover application/yaml after json-only", plan="Json-only 415s leftover application/yaml. Freeze yaml, spec json leftover.", residual="handoff: keep application/yaml or force json leftover", vs="r3561 accept-application-yaml (json leftover, not accept mill)", fetch1="https://www.rfc-editor.org/rfc/rfc9512.html", fetch1_ok="JSON-only leftover is not application/yaml.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch2_ok="Exclusive json-only 415 leftover yaml.")),
    (p(slug="oas-schema-max-items", domain="oas-maxitems-vs-unbounded-array", success=True, name="maxit", stack="OpenAPI 3.1 maxItems + Go", field="maxItems", old="unbounded array leftover", new="array maxItems", fail_err="400: leftover unbounded array after maxItems-only", plan="maxItems-only 400s leftover unbounded. Dual-accept unbounded for one release.", residual="batch still unbounded leftover; drop after batch 5", vs="r3947 leftover-empty-array (maxItems vs unbounded leftover, not minItems mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/array#maxitems", fetch1_ok="maxItems caps array length, leftover unbounded arrays fail closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive maxItems 400 leftover unbounded."),
     p(slug="leftover-no-max-items", domain="no-max-items-vs-oas-maxitems", success=False, name="nomaxit", stack="OpenAPI leftover no max items + Java + TS", field="items", old="array maxItems", new="no max items leftover only", fail_err="400: leftover maxItems after no-max-only", plan="No-max-only 400s leftover maxItems. Freeze maxItems, spec no-max leftover.", residual="handoff: keep maxItems or force no-max leftover", vs="r3947 oas-minitems-array (no-max leftover, not minItems)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="No-max leftover arrays are not maxItems.", fetch2="https://json-schema.org/understanding-json-schema/reference/array#maxitems", fetch2_ok="Exclusive no-max-items 400 leftover maxItems.")),
    (p(slug="oas-parameter-in-cookie", domain="oas-cookie-param-vs-header-session", success=True, name="ckpar", stack="OpenAPI 3.1 parameter in=cookie + Go", field="in", old="header session leftover", new="cookie parameter", fail_err="400: leftover header session after cookie-only", plan="cookie-param-only 400s leftover header session. Dual-read header for one release.", residual="edge still header leftover; drop after edge 6", vs="r4023 leftover-apikey-querystring (cookie param vs header leftover, not apikey mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="in=cookie is not leftover session headers.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#fixed-fields-9", fetch2_ok="Exclusive cookie param 400 leftover header session."),
     p(slug="leftover-header-session", domain="header-session-vs-oas-cookie-param", success=False, name="hdrses", stack="OpenAPI leftover header session + Java + TS", field="in", old="cookie parameter", new="header session leftover only", fail_err="400: leftover cookie param after header-only", plan="Header-only 400s leftover cookie param. Freeze cookie, spec header leftover.", residual="handoff: keep cookie param or force header leftover", vs="r4023 oas-security-apikey-cookie (header leftover, not apikey cookie mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#fixed-fields-9", fetch1_ok="Header leftover sessions are not in=cookie.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="Exclusive header session 400 leftover cookie.")),
    (p(slug="oas-operation-requestbody-ref", domain="oas-reqbody-ref-vs-inline", success=True, name="rbref", stack="OpenAPI 3.1 requestBody $ref + Go", field="requestBody", old="inline reqbody leftover", new="requestBody ref", fail_err="400: leftover inline reqbody after ref-only", plan="requestBody-$ref-only 400s leftover inline. Dual-read inline for one release.", residual="sdk still inline leftover; drop after sdk 5", vs="r4038 leftover-optional-body (reqbody ref vs inline leftover, not required mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#request-body-object", fetch1_ok="requestBody $ref reuses components, leftover inline bodies are not that.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#components-object", fetch2_ok="Exclusive requestBody $ref 400 leftover inline."),
     p(slug="leftover-inline-reqbody", domain="inline-reqbody-vs-oas-ref", success=False, name="inrb", stack="OpenAPI leftover inline reqbody + Java + TS", field="requestBody", old="requestBody ref", new="inline reqbody leftover only", fail_err="400: leftover requestBody $ref after inline-only", plan="Inline-only 400s leftover requestBody $ref. Freeze $ref, spec inline leftover.", residual="handoff: keep requestBody $ref or force inline leftover", vs="r4038 oas-requestbody-required-post (inline leftover, not required mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#components-object", fetch1_ok="Inline leftover bodies are not $ref.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#request-body-object", fetch2_ok="Exclusive inline reqbody 400 leftover $ref.")),
    (p(slug="oas-security-oauth2-tokenurl", domain="oas-tokenurl-vs-authurl-only", success=True, name="tokurl", stack="OpenAPI 3.1 oauth2 tokenUrl + Go", field="tokenUrl", old="authurl only leftover", new="oauth2 tokenUrl", fail_err="401: leftover authurl-only after tokenUrl-only", plan="tokenUrl-only 401s leftover authurl-only. Dual-omit tokenUrl for one release.", residual="idp still authurl leftover; drop after idp 6", vs="r4007 leftover-no-refresh (tokenUrl vs authurl leftover, not refresh mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#oauth-flow-object", fetch1_ok="tokenUrl is required for code and password flows, leftover authurl-only fails closed.", fetch2="https://datatracker.ietf.org/doc/html/rfc6749#section-3.2", fetch2_ok="Exclusive tokenUrl 401 leftover authurl-only."),
     p(slug="leftover-authurl-only", domain="authurl-only-vs-oas-tokenurl", success=False, name="authonly", stack="OpenAPI leftover authurl only + Java + TS", field="authorizationUrl", old="oauth2 tokenUrl", new="authurl only leftover only", fail_err="401: leftover tokenUrl after authurl-only", plan="Authurl-only 401s leftover tokenUrl. Freeze tokenUrl, spec authurl leftover.", residual="handoff: keep tokenUrl or force authurl leftover", vs="r4007 oas-security-oauth2-refresh (authurl leftover, not refresh mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc6749#section-3.2", fetch1_ok="authorizationUrl-only leftover is not tokenUrl.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#oauth-flow-object", fetch2_ok="Exclusive authurl-only 401 leftover tokenUrl.")),
    (p(slug="oas-schema-pattern", domain="oas-pattern-vs-unvalidated-str", success=True, name="schpat", stack="OpenAPI 3.1 schema pattern + Go", field="pattern", old="unvalidated string leftover", new="schema pattern", fail_err="400: leftover unvalidated string after pattern-only", plan="pattern-only 400s leftover unvalidated. Dual-read unvalidated for one release.", residual="form still unvalidated leftover; drop after form 5", vs="r3947 leftover-unvalidated-email (pattern vs unvalidated leftover, not email mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/regular_expressions", fetch1_ok="pattern is an ECMA regex, leftover unvalidated strings fail closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive pattern 400 leftover unvalidated."),
     p(slug="leftover-unvalidated-str", domain="unvalidated-str-vs-oas-pattern", success=False, name="unvstr", stack="OpenAPI leftover unvalidated string + Java + TS", field="type", old="schema pattern", new="unvalidated string leftover only", fail_err="400: leftover pattern after unvalidated-only", plan="Unvalidated-only 400s leftover pattern. Freeze pattern, spec unvalidated leftover.", residual="handoff: keep pattern or force unvalidated leftover", vs="r3947 oas-format-email-ascii (unvalidated leftover, not email mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Unvalidated leftover strings are not pattern.", fetch2="https://json-schema.org/understanding-json-schema/reference/regular_expressions", fetch2_ok="Exclusive unvalidated 400 leftover pattern.")),
    (p(slug="oas-header-description-req", domain="oas-header-desc-vs-undocumented-hdr", success=True, name="hdrdesc", stack="OpenAPI 3.1 header description + Go", field="description", old="undocumented header leftover", new="header description", fail_err="400: leftover undocumented header after description-only", plan="header-description-only 400s leftover undocumented. Dual-omit description for one release.", residual="portal still undocumented leftover; drop after portal 4", vs="r4007 leftover-live-header (header desc vs undocumented leftover, not deprecated mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch1_ok="Header description documents the header, leftover undocumented fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="Exclusive header description 400 leftover undocumented."),
     p(slug="leftover-undocumented-header", domain="undocumented-hdr-vs-oas-header-desc", success=False, name="undhdr", stack="OpenAPI leftover undocumented header + Java + TS", field="description", old="header description", new="undocumented header leftover only", fail_err="400: leftover header description after undocumented-only", plan="Undocumented-only 400s leftover header description. Freeze description, spec undocumented leftover.", residual="handoff: keep header description or force undocumented leftover", vs="r4007 oas-header-deprecated (undocumented leftover, not deprecated mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="Undocumented leftover headers are not described.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch2_ok="Exclusive undocumented header 400 leftover description.")),
    (p(slug="oas-reqbodies-components-reuse", domain="oas-comp-reqbodies-vs-inline-body", success=True, name="creq", stack="OpenAPI 3.1 components.requestBodies + Go", field="requestBodies", old="inline body leftover", new="components requestBodies", fail_err="400: leftover inline body after components-only", plan="components.requestBodies-only 400s leftover inline. Dual-read inline for one release.", residual="sdk still inline leftover; drop after sdk 5", vs="r4054 leftover-inline-sec-scheme (requestBodies vs inline leftover, not securitySchemes)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#components-object", fetch1_ok="components.requestBodies reuse Request Body Objects.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#request-body-object", fetch2_ok="Exclusive components.requestBodies 400 leftover inline."),
     p(slug="leftover-inline-reqbodies", domain="inline-body-vs-oas-comp-reqbodies", success=False, name="ireq", stack="OpenAPI leftover inline requestBodies + Java + TS", field="requestBody", old="components requestBodies", new="inline body leftover only", fail_err="400: leftover components.requestBodies after inline-only", plan="Inline-only 400s leftover components.requestBodies. Freeze components, spec inline leftover.", residual="handoff: keep components.requestBodies or force inline leftover", vs="r4054 oas-components-security-schemes (inline leftover, not securitySchemes mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#request-body-object", fetch1_ok="Inline leftover bodies are not components.requestBodies.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#components-object", fetch2_ok="Exclusive inline requestBodies 400 leftover components.")),
    (p(slug="oas-schema-title-required", domain="oas-schema-title-vs-untitled", success=True, name="schtit", stack="OpenAPI 3.1 schema title + Go", field="title", old="untitled schema leftover", new="schema title", fail_err="400: leftover untitled after title-only", plan="schema-title-only 400s leftover untitled. Dual-omit title for one release.", residual="docs still untitled leftover; drop after docs 4", vs="r3978 leftover-undocumented-schema (schema title vs untitled leftover, not description mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/generic#title", fetch1_ok="title annotates the schema, leftover untitled fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive schema title 400 leftover untitled."),
     p(slug="leftover-untitled-schema", domain="untitled-vs-oas-schema-title", success=False, name="notitle", stack="OpenAPI leftover untitled schema + Java + TS", field="title", old="schema title", new="untitled schema leftover only", fail_err="400: leftover schema title after untitled-only", plan="Untitled-only 400s leftover schema title. Freeze title, spec untitled leftover.", residual="handoff: keep schema title or force untitled leftover", vs="r3978 oas-schema-description (untitled leftover, not description mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Untitled leftover schemas are not titled.", fetch2="https://json-schema.org/understanding-json-schema/reference/generic#title", fetch2_ok="Exclusive untitled 400 leftover title.")),
    (p(slug="oas-webhook-parameters", domain="oas-webhook-params-vs-no-params", success=True, name="whkpar", stack="OpenAPI 3.1 webhook parameters + Go", field="parameters", old="no webhook params leftover", new="webhook parameters", fail_err="400: leftover no-params after webhook-params-only", plan="webhook-parameters-only 400s leftover none. Dual-omit params for one release.", residual="edge still none leftover; drop after edge 5", vs="r4038 leftover-webhook-trace (webhook params vs none leftover, not TRACE mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#path-item-object", fetch1_ok="Webhook Path Items may declare parameters, leftover missing fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#oasWebhooks", fetch2_ok="Exclusive webhook parameters 400 leftover none."),
     p(slug="leftover-no-webhook-params", domain="no-webhook-params-vs-oas-webhook-params", success=False, name="nowhkp", stack="OpenAPI leftover no webhook params + Java + TS", field="parameters", old="webhook parameters", new="no webhook params leftover only", fail_err="400: leftover webhook parameters after none-only", plan="None-only 400s leftover webhook parameters. Freeze parameters, spec none leftover.", residual="handoff: keep webhook parameters or force none leftover", vs="r4038 oas-webhook-options (no-params leftover, not OPTIONS mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#oasWebhooks", fetch1_ok="Missing leftover webhook params are not parameters.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#path-item-object", fetch2_ok="Exclusive no-webhook-params 400 leftover parameters.")),
    (p(slug="oas-format-regex-ecma", domain="oas-ecma-regex-vs-pcre", success=True, name="ecmare", stack="OpenAPI 3.1 format=regex ECMA + Go", field="format", old="pcre regex leftover", new="ecma regex", fail_err="400: leftover pcre after ecma-only", plan="ecma-regex-only 400s leftover pcre. Dual-read pcre for one release.", residual="validator still pcre leftover; drop after validator 6", vs="r3561 format-regex-ecma (ecma vs pcre leftover, not format mill reuse)", fetch1="https://json-schema.org/understanding-json-schema/reference/regular_expressions", fetch1_ok="format=regex is ECMA-262, leftover PCRE fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="Exclusive ecma regex 400 leftover pcre."),
     p(slug="leftover-pcre-regex", domain="pcre-vs-oas-ecma-regex", success=False, name="pcre", stack="OpenAPI leftover pcre regex + Java + TS", field="pattern", old="ecma regex", new="pcre regex leftover only", fail_err="400: leftover ecma regex after pcre-only", plan="Pcre-only 400s leftover ecma regex. Freeze ecma, spec pcre leftover.", residual="handoff: keep ecma regex or force pcre leftover", vs="r3561 format-regex-ecma (pcre leftover, not format mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="PCRE leftover is not format=regex ECMA.", fetch2="https://json-schema.org/understanding-json-schema/reference/regular_expressions", fetch2_ok="Exclusive pcre 400 leftover ecma.")),
    (p(slug="oas-info-description-commonmark", domain="oas-info-desc-vs-plain-info", success=True, name="infomd", stack="OpenAPI 3.1 info.description CommonMark + Go", field="description", old="plain info leftover", new="info commonmark description", fail_err="400: leftover plain info after commonmark-only", plan="info.description-only 400s leftover plain. Dual-read plain for one release.", residual="portal still plain leftover; drop after portal 5", vs="r4007 leftover-missing-info-summary (info CommonMark vs plain leftover, not summary mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#info-object", fetch1_ok="info.description is CommonMark, leftover plain text is not that.", fetch2="https://spec.commonmark.org/", fetch2_ok="Exclusive info CommonMark 400 leftover plain."),
     p(slug="leftover-plain-info", domain="plain-info-vs-oas-info-desc", success=False, name="plainfo", stack="OpenAPI leftover plain info + Java + TS", field="description", old="info commonmark description", new="plain info leftover only", fail_err="400: leftover info.description after plain-only", plan="Plain-only 400s leftover info.description. Freeze CommonMark, spec plain leftover.", residual="handoff: keep info CommonMark or force plain leftover", vs="r4007 oas-info-summary-required (plain leftover, not summary mill)", fetch1="https://spec.commonmark.org/", fetch1_ok="Plain leftover info is not CommonMark description.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#info-object", fetch2_ok="Exclusive plain info 400 leftover CommonMark.")),
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
    print(json.dumps({"round": round_n, "idx": idx, "ids": [e1["id"], e2["id"]], "catalog": "r4102"}))


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
