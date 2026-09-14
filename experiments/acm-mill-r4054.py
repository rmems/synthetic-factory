#!/usr/bin/env python3
"""Fourth unique OpenAPI-drift ACM catalog after r4038 mill. Fast slug load."""
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
    (p(slug="oas-schema-not-negation", domain="oas-not-vs-permit-all", success=True, name="schnot", stack="OpenAPI 3.1 not + Go", field="not", old="permit all leftover", new="schema not", fail_err="400: leftover permit-all after not-only", plan="not-only 400s leftover permit-all. Dual-permit for one release.", residual="validator still permit leftover; drop after validator 5", vs="r3947 leftover-type-switch (not vs permit leftover, not oneOf mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/combining#not", fetch1_ok="not rejects matching leftover permit-all payloads.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive not 400 leftover permit-all."),
     p(slug="leftover-permit-all", domain="permit-all-vs-oas-not", success=False, name="permall", stack="OpenAPI leftover permit-all + Java + TS", field="type", old="schema not", new="permit all leftover only", fail_err="400: leftover not after permit-only", plan="Permit-only 400s leftover not. Freeze not, spec permit leftover.", residual="handoff: keep not or force permit leftover", vs="r3947 oas-oneof-union (permit leftover, not oneOf)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Permit-all is not not.", fetch2="https://json-schema.org/understanding-json-schema/reference/combining#not", fetch2_ok="Exclusive permit-all 400 leftover not.")),
    (p(slug="oas-json-schema-dynamic-anchor", domain="oas-dynamic-anchor-vs-static", success=True, name="dynanc", stack="OpenAPI 3.1 $dynamicAnchor + Go", field="$dynamicAnchor", old="static anchor leftover", new="dynamic anchor", fail_err="400: leftover static anchor after dynamic-only", plan="$dynamicAnchor-only 400s leftover static. Dual-read static for one release.", residual="codegen still static leftover; drop after codegen 6", vs="r3561 json-schema-anchor (dynamic vs static leftover, not $anchor mill)", fetch1="https://json-schema.org/understanding-json-schema/structuring#dynamic-anchor", fetch1_ok="$dynamicAnchor is not leftover static $anchor.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive $dynamicAnchor 400 leftover static."),
     p(slug="leftover-static-anchor", domain="static-anchor-vs-oas-dynamic", success=False, name="stanc", stack="OpenAPI leftover static anchor + Java + TS", field="$anchor", old="dynamic anchor", new="static anchor leftover only", fail_err="400: leftover $dynamicAnchor after static-only", plan="Static-only 400s leftover $dynamicAnchor. Freeze dynamic, spec static leftover.", residual="handoff: keep $dynamicAnchor or force static leftover", vs="r3561 json-schema-anchor (static leftover, not $anchor mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Static $anchor is not $dynamicAnchor.", fetch2="https://json-schema.org/understanding-json-schema/structuring#dynamic-anchor", fetch2_ok="Exclusive static anchor 400 leftover dynamic.")),
    (p(slug="oas-header-schema-array", domain="oas-header-array-vs-csv-header", success=True, name="hdrarr", stack="OpenAPI 3.1 header schema array + Go", field="schema", old="csv header leftover", new="header array schema", fail_err="400: leftover csv header after array-only", plan="Header-array-only 400s leftover csv. Dual-read csv for one release.", residual="proxy still csv leftover; drop after proxy 5", vs="r4023 leftover-header-form-explode (header array vs csv leftover, not form explode)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch1_ok="Header schema type=array is not leftover comma-joined strings.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive header array 400 leftover csv."),
     p(slug="leftover-csv-header", domain="csv-header-vs-oas-header-array", success=False, name="csvhdr", stack="OpenAPI leftover csv header + Java + TS", field="style", old="header array schema", new="csv header leftover only", fail_err="400: leftover header array after csv-only", plan="Csv-only 400s leftover header array. Freeze array, spec csv leftover.", residual="handoff: keep header array or force csv leftover", vs="r4023 oas-header-style-simple (csv leftover, not simple style)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="CSV leftover headers are not type=array.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch2_ok="Exclusive csv header 400 leftover array.")),
    (p(slug="oas-components-security-schemes", domain="oas-comp-sec-vs-inline-scheme", success=True, name="csec", stack="OpenAPI 3.1 components.securitySchemes + Go", field="securitySchemes", old="inline security leftover", new="components securitySchemes", fail_err="401: leftover inline security after components-only", plan="components.securitySchemes-only 401s leftover inline. Dual-read inline for one release.", residual="edge still inline leftover; drop after edge 6", vs="r3978 leftover-inline-responses (securitySchemes vs inline leftover, not responses)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#components-object", fetch1_ok="components.securitySchemes reuse Security Scheme Objects.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch2_ok="Exclusive components.securitySchemes 401 leftover inline."),
     p(slug="leftover-inline-sec-scheme", domain="inline-scheme-vs-oas-comp-sec", success=False, name="isec", stack="OpenAPI leftover inline security + Java + TS", field="type", old="components securitySchemes", new="inline security leftover only", fail_err="401: leftover components.securitySchemes after inline-only", plan="Inline-only 401s leftover components.securitySchemes. Freeze components, spec inline leftover.", residual="handoff: keep components.securitySchemes or force inline leftover", vs="r3978 oas-components-responses (inline leftover, not responses mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch1_ok="Inline schemes are not components.securitySchemes.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#components-object", fetch2_ok="Exclusive inline security 401 leftover components.")),
    (p(slug="oas-operation-operationid-unique", domain="oas-unique-opid-vs-dup-opid", success=True, name="opidun", stack="OpenAPI 3.1 unique operationId + Go", field="operationId", old="dup opid leftover", new="unique operationId", fail_err="400: leftover dup opid after unique-only", plan="unique-operationId-only 400s leftover dups. Dual-accept dups for one release.", residual="sdk still dup leftover; drop after sdk 5", vs="r3947 leftover-missing-summary (unique opid vs dup leftover, not missing summary)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch1_ok="operationId MUST be unique among all operations.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#fixed-fields-8", fetch2_ok="Exclusive unique operationId 400 leftover dups."),
     p(slug="leftover-dup-opid", domain="dup-opid-vs-oas-unique-opid", success=False, name="opidup", stack="OpenAPI leftover dup opid + Java + TS", field="operationId", old="unique operationId", new="dup opid leftover only", fail_err="400: leftover unique operationId after dup-only", plan="Dup-only 400s leftover unique operationId. Freeze unique, spec dup leftover.", residual="handoff: keep unique operationId or force dup leftover", vs="r3947 oas-operation-summary-req (dup leftover, not summary mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#fixed-fields-8", fetch1_ok="Duplicate operationIds are not unique.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch2_ok="Exclusive dup opid 400 leftover unique.")),
    (p(slug="oas-content-encoding-quoted-printable", domain="oas-qp-vs-raw-binary", success=True, name="encqp", stack="OpenAPI 3.1 contentEncoding quoted-printable + Go", field="contentEncoding", old="raw binary leftover", new="quoted printable", fail_err="415: leftover raw binary after qp-only", plan="quoted-printable-only 415s leftover raw. Dual-read raw for one release.", residual="mail still raw leftover; drop after mail 6", vs="r4007 leftover-8bit-text (quoted-printable vs raw leftover, not 8bit mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/non_json_data#contentencoding", fetch1_ok="contentEncoding=quoted-printable is not leftover raw bytes.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive quoted-printable 415 leftover raw."),
     p(slug="leftover-raw-binary", domain="raw-binary-vs-oas-qp", success=False, name="rawbin", stack="OpenAPI leftover raw binary + Java + TS", field="contentEncoding", old="quoted printable", new="raw binary leftover only", fail_err="415: leftover quoted-printable after raw-only", plan="Raw-only 415s leftover quoted-printable. Freeze qp, spec raw leftover.", residual="handoff: keep quoted-printable or force raw leftover", vs="r4007 oas-content-encoding-7bit (raw leftover, not 7bit mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Raw binary is not quoted-printable.", fetch2="https://json-schema.org/understanding-json-schema/reference/non_json_data#contentencoding", fetch2_ok="Exclusive raw binary 415 leftover qp.")),
    (p(slug="oas-format-uri-template-strict", domain="oas-uritemplate-vs-sprintf", success=True, name="uritpl", stack="OpenAPI 3.1 format=uri-template + Go", field="format", old="sprintf url leftover", new="uri template", fail_err="400: leftover sprintf after uri-template-only", plan="uri-template-only 400s leftover sprintf. Dual-read sprintf for one release.", residual="sdk still sprintf leftover; drop after sdk 5", vs="r3561 format-uri-template (strict uri-template vs sprintf leftover, not format mill reuse)", fetch1="https://json-schema.org/understanding-json-schema/reference/string#resource-identifiers", fetch1_ok="format=uri-template is RFC 6570, leftover sprintf urls fail closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="Exclusive uri-template 400 leftover sprintf."),
     p(slug="leftover-sprintf-url", domain="sprintf-vs-oas-uritemplate", success=False, name="sprintf", stack="OpenAPI leftover sprintf url + Java + TS", field="href", old="uri template", new="sprintf url leftover only", fail_err="400: leftover uri-template after sprintf-only", plan="Sprintf-only 400s leftover uri-template. Freeze template, spec sprintf leftover.", residual="handoff: keep uri-template or force sprintf leftover", vs="r3561 format-uri-template (sprintf leftover, not format mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="Sprintf urls are not format=uri-template.", fetch2="https://json-schema.org/understanding-json-schema/reference/string#resource-identifiers", fetch2_ok="Exclusive sprintf 400 leftover uri-template.")),
    (p(slug="oas-info-license-name", domain="oas-license-name-vs-missing", success=True, name="licname", stack="OpenAPI 3.1 license.name + Go", field="name", old="missing license leftover", new="license name", fail_err="400: leftover missing license after name-only", plan="license.name-only 400s leftover missing. Dual-omit license for one release.", residual="portal still missing leftover; drop after portal 4", vs="r3931 leftover-missing-title (license name vs missing leftover, not title)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#license-object", fetch1_ok="license.name is required when license is present.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#info-object", fetch2_ok="Exclusive license name 400 leftover missing."),
     p(slug="leftover-missing-license", domain="missing-license-vs-oas-license-name", success=False, name="nolic", stack="OpenAPI leftover missing license + Java + TS", field="license", old="license name", new="missing license leftover only", fail_err="400: leftover license.name after missing-only", plan="Missing-only 400s leftover license.name. Freeze name, spec missing leftover.", residual="handoff: keep license.name or force missing leftover", vs="r3931 oas-info-title-required (missing leftover, not title mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#info-object", fetch1_ok="Missing license is not license.name.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#license-object", fetch2_ok="Exclusive missing license 400 leftover name.")),
    (p(slug="oas-tag-name-required", domain="oas-tag-name-vs-anonymous-tag", success=True, name="tagname", stack="OpenAPI 3.1 tag.name + Go", field="name", old="anonymous tag leftover", new="tag name", fail_err="400: leftover anonymous tag after name-only", plan="tag.name-only 400s leftover anonymous. Dual-omit tags for one release.", residual="portal still anonymous leftover; drop after portal 5", vs="r3993 leftover-untagged-op (tag name vs anonymous leftover, not untagged op)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#tag-object", fetch1_ok="tag.name is required, leftover anonymous tags fail closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#fixed-fields-18", fetch2_ok="Exclusive tag name 400 leftover anonymous."),
     p(slug="leftover-anonymous-tag", domain="anonymous-tag-vs-oas-tag-name", success=False, name="anontag", stack="OpenAPI leftover anonymous tag + Java + TS", field="name", old="tag name", new="anonymous tag leftover only", fail_err="400: leftover tag.name after anonymous-only", plan="Anonymous-only 400s leftover tag.name. Freeze name, spec anonymous leftover.", residual="handoff: keep tag.name or force anonymous leftover", vs="r3993 oas-operation-tags-required (anonymous leftover, not op tags)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#fixed-fields-18", fetch1_ok="Anonymous tags are not tag.name.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#tag-object", fetch2_ok="Exclusive anonymous tag 400 leftover name.")),
    (p(slug="oas-path-item-summary", domain="oas-path-summary-vs-none", success=True, name="pisum", stack="OpenAPI 3.1 Path Item summary + Go", field="summary", old="no path summary leftover", new="path item summary", fail_err="400: leftover no-path-summary after summary-only", plan="Path-Item-summary-only 400s leftover none. Dual-omit summary for one release.", residual="portal still none leftover; drop after portal 5", vs="r4038 leftover-op-desc-only (path summary vs none leftover, not path desc mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#path-item-object", fetch1_ok="Path Item summary is a short string, leftover missing fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#fixed-fields-7", fetch2_ok="Exclusive path summary 400 leftover none."),
     p(slug="leftover-no-path-summary", domain="no-path-summary-vs-oas-path-summary", success=False, name="nopisum", stack="OpenAPI leftover no path summary + Java + TS", field="summary", old="path item summary", new="no path summary leftover only", fail_err="400: leftover path summary after none-only", plan="None-only 400s leftover path summary. Freeze summary, spec none leftover.", residual="handoff: keep path summary or force none leftover", vs="r4038 oas-path-item-description (none leftover, not path desc)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#fixed-fields-7", fetch1_ok="Missing path summaries are not Path Item summary.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#path-item-object", fetch2_ok="Exclusive no-path-summary 400 leftover summary.")),
    (p(slug="oas-parameter-examples-map", domain="oas-param-examples-vs-dual-example", success=True, name="pexmap", stack="OpenAPI 3.1 parameter examples + Go", field="examples", old="dual example leftover", new="parameter examples map", fail_err="400: leftover dual-example after examples-only", plan="parameter.examples-only 400s leftover dual example+examples. Dual-read example for one release.", residual="docs still dual leftover; drop after docs 5", vs="r4007 leftover-single-example (param examples vs dual leftover, not schema examples)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="example and examples are mutually exclusive.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#example-object", fetch2_ok="Exclusive examples map 400 leftover dual."),
     p(slug="leftover-dual-example", domain="dual-example-vs-oas-param-examples", success=False, name="dualex", stack="OpenAPI leftover dual example + Java + TS", field="example", old="parameter examples map", new="dual example leftover only", fail_err="400: leftover examples map after dual-only", plan="Dual-only 400s leftover examples map. Freeze examples, spec dual leftover.", residual="handoff: keep examples map or force dual leftover", vs="r4007 oas-schema-examples-array (dual leftover, not schema examples)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#example-object", fetch1_ok="Dual example+examples is invalid.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="Exclusive dual example 400 leftover examples.")),
    (p(slug="oas-format-idn-email-rfc", domain="oas-idn-email-vs-puny-email", success=True, name="idnem", stack="OpenAPI 3.1 format=idn-email + Go", field="format", old="puny email leftover", new="idn-email format", fail_err="400: leftover puny email after idn-email-only", plan="idn-email-only 400s leftover puny. Dual-read puny for one release.", residual="crm still puny leftover; drop after crm 6", vs="r3883 leftover-ascii-email (idn-email vs puny leftover, not ascii email mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/string#idn-email", fetch1_ok="format=idn-email is not leftover punycode addr-spec.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="Exclusive idn-email 400 leftover puny."),
     p(slug="leftover-puny-email", domain="puny-email-vs-oas-idn-email", success=False, name="punyem", stack="OpenAPI leftover puny email + Java + TS", field="email", old="idn-email format", new="puny email leftover only", fail_err="400: leftover idn-email after puny-only", plan="Puny-only 400s leftover idn-email. Freeze idn-email, spec puny leftover.", residual="handoff: keep idn-email or force puny leftover", vs="r4023 leftover-display-name-email (puny leftover, not display-name mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="Puny emails are not format=idn-email.", fetch2="https://json-schema.org/understanding-json-schema/reference/string#idn-email", fetch2_ok="Exclusive puny email 400 leftover idn-email.")),
    (p(slug="oas-content-multipart-related", domain="oas-related-vs-alternative", success=True, name="mprel", stack="OpenAPI 3.1 multipart/related + Go", field="content", old="multipart alternative leftover", new="multipart related", fail_err="415: leftover multipart/alternative after related-only", plan="multipart-related-only 415s leftover alternative. Dual-read alternative for one release.", residual="ingest still alternative leftover; drop after ingest 6", vs="r4023 leftover-multipart-form (related vs alternative leftover, not form mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch1_ok="multipart/related is not leftover multipart/alternative.", fetch2="https://datatracker.ietf.org/doc/html/rfc2387", fetch2_ok="Exclusive multipart/related 415 leftover alternative."),
     p(slug="leftover-multipart-alternative", domain="alternative-vs-oas-related", success=False, name="mpalt", stack="OpenAPI leftover multipart alternative + Java + TS", field="content", old="multipart related", new="multipart alternative leftover only", fail_err="415: leftover multipart/related after alternative-only", plan="Alternative-only 415s leftover multipart/related. Freeze related, spec alternative leftover.", residual="handoff: keep multipart/related or force alternative leftover", vs="r4023 oas-content-multipart-mixed (alternative leftover, not mixed mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc2046#section-5.1.4", fetch1_ok="multipart/alternative is not multipart/related.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch2_ok="Exclusive alternative 415 leftover related.")),
    (p(slug="oas-xml-attribute-prefix", domain="oas-attr-prefix-vs-element-prefix", success=True, name="xapre", stack="OpenAPI 3.1 xml attribute prefix + Go", field="prefix", old="element prefix leftover", new="xml attribute prefix", fail_err="415: leftover element prefix after attr-prefix-only", plan="xml.attribute-prefix-only 415s leftover element prefix. Dual-read element for one release.", residual="batch still element leftover; drop after batch 5", vs="r4023 leftover-unprefixed-ns (attr prefix vs element leftover, not unprefixed mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#xml-object", fetch1_ok="xml.prefix with attribute:true is not leftover element prefixes.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive attr prefix 415 leftover element prefix."),
     p(slug="leftover-element-prefix", domain="element-prefix-vs-oas-attr-prefix", success=False, name="xelpre", stack="OpenAPI leftover element prefix + Java + TS", field="prefix", old="xml attribute prefix", new="element prefix leftover only", fail_err="415: leftover attr prefix after element-only", plan="Element-only 415s leftover attr prefix. Freeze attr prefix, spec element leftover.", residual="handoff: keep attr prefix or force element leftover", vs="r4007 leftover-element-name-xml (element prefix leftover, not element name)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Element prefixes are not xml.attribute prefixes.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#xml-object", fetch2_ok="Exclusive element prefix 415 leftover attr prefix.")),
    (p(slug="oas-response-header-location", domain="oas-location-vs-location-body", success=True, name="rloc", stack="OpenAPI 3.1 Location header + Go", field="Location", old="location body leftover", new="Location header", fail_err="400: leftover location body after Location-only", plan="Location-header-only 400s leftover location body. Dual-emit body for one release.", residual="sdk still body leftover; drop after sdk 6", vs="r4023 leftover-retry-body (Location vs body leftover, not Retry-After mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc9110#name-location", fetch1_ok="Location is a response header, not a leftover JSON body.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#response-object", fetch2_ok="Exclusive Location 400 leftover location body."),
     p(slug="leftover-location-body", domain="location-body-vs-oas-location", success=False, name="locbody", stack="OpenAPI leftover location body + Java + TS", field="location", old="Location header", new="location body leftover only", fail_err="400: leftover Location after body-only", plan="Body-only 400s leftover Location. Freeze header, spec body leftover.", residual="handoff: keep Location or force body leftover", vs="r4023 oas-response-header-retryafter (location body leftover, not Retry-After)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#response-object", fetch1_ok="A location body field is not Location.", fetch2="https://datatracker.ietf.org/doc/html/rfc9110#name-location", fetch2_ok="Exclusive location body 400 leftover Location.")),
    (p(slug="oas-servers-https-only", domain="oas-https-only-vs-http-server", success=True, name="srvhttps", stack="OpenAPI 3.1 https-only servers + Go", field="url", old="http server leftover", new="https only servers", fail_err="400: leftover http server after https-only", plan="https-only 400s leftover http. Dual-accept http for one release.", residual="edge still http leftover; drop after edge 7", vs="r4023 leftover-single-prod-url (https-only vs http leftover, not single prod)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#server-object", fetch1_ok="https servers are not leftover http urls.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#oasServers", fetch2_ok="Exclusive https-only 400 leftover http."),
     p(slug="leftover-http-server", domain="http-server-vs-oas-https-only", success=False, name="srvhttp", stack="OpenAPI leftover http server + Java + TS", field="url", old="https only servers", new="http server leftover only", fail_err="400: leftover https-only after http-only", plan="Http-only 400s leftover https-only. Freeze https, spec http leftover.", residual="handoff: keep https-only or force http leftover", vs="r4023 oas-servers-multiple-prod-stage (http leftover, not prod-stage mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#oasServers", fetch1_ok="http leftover servers are not https-only.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#server-object", fetch2_ok="Exclusive http server 400 leftover https.")),
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
    print(json.dumps({"round": round_n, "idx": idx, "ids": [e1["id"], e2["id"]], "catalog": "r4054"}))


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
