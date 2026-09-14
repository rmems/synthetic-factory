#!/usr/bin/env python3
"""Seventh unique OpenAPI-drift ACM catalog after r3947 mill."""
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
]
BANNED_PRIOR = {p[0]["slug"] for p in _b.PAIRS} | {p[1]["slug"] for p in _b.PAIRS}
for fname in priors:
    sp = importlib.util.spec_from_file_location(fname.replace("-", "_"), HERE / fname)
    mod = importlib.util.module_from_spec(sp)
    assert sp.loader is not None
    sp.loader.exec_module(mod)
    BANNED_PRIOR |= {p[0]["slug"] for p in mod.PAIRS} | {p[1]["slug"] for p in mod.PAIRS}

BANNED_PRIOR |= {
    "oas-lll4-proto-optional", "protobuf-lll4-optional-oas",
    "accept-language-bcp47", "iso639-language",
    "smile-binary-json", "cbor-majortype-vs-smile",
    "422-vs-400-validation", "207-multistatus-batch",
}


def p(**kw):
    return plant(**kw)


PAIRS: list[tuple[dict, dict]] = [
    (p(slug="oas-info-contact-email", domain="oas-contact-email-vs-missing-contact", success=True, name="ctem", stack="OpenAPI 3.1 info.contact.email + Go", field="email", old="missing contact leftover", new="contact email", fail_err="400: leftover missing contact after contact-email-only", plan="contact.email-only 400s leftover missing contact. Dual-omit contact for one release.", residual="portal still missing leftover; drop after portal 5", vs="r3931 oas-info-terms-url (contact email vs missing leftover, not terms)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#contact-object", fetch1_ok="contact.email is not leftover missing contact.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#info-object", fetch2_ok="Exclusive contact email 400 leftover missing."),
     p(slug="leftover-missing-contact", domain="missing-contact-vs-oas-contact-email", success=False, name="noct", stack="OpenAPI leftover missing contact + Java + TS", field="contact", old="contact email", new="missing contact leftover only", fail_err="400: leftover contact email after missing-only", plan="Missing-only 400s leftover contact email. Freeze contact, spec missing leftover.", residual="handoff: keep contact email or force missing leftover", vs="r3931 leftover-missing-terms (missing contact leftover, not terms)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#info-object", fetch1_ok="Missing contact is not contact.email.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#contact-object", fetch2_ok="Exclusive missing contact 400 leftover email.")),
    (p(slug="oas-info-version-semver", domain="oas-semver-vs-unversioned", success=True, name="semver", stack="OpenAPI 3.1 info.version semver + Go", field="version", old="unversioned leftover", new="semver version", fail_err="400: leftover unversioned after semver-only", plan="semver-only 400s leftover unversioned. Dual-accept unversioned for one release.", residual="sdk still unversioned leftover; drop after sdk 6", vs="r3947 oas-operation-summary-req (semver vs unversioned leftover, not summary)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#info-object", fetch1_ok="info.version should be semver, not leftover unversioned.", fetch2="https://semver.org/", fetch2_ok="Exclusive semver 400 leftover unversioned."),
     p(slug="leftover-unversioned", domain="unversioned-vs-oas-semver", success=False, name="unver", stack="OpenAPI leftover unversioned + Java + TS", field="version", old="semver version", new="unversioned leftover only", fail_err="400: leftover semver after unversioned-only", plan="Unversioned-only 400s leftover semver. Freeze semver, spec unversioned leftover.", residual="handoff: keep semver or force unversioned leftover", vs="r3947 leftover-missing-summary (unversioned leftover, not missing summary)", fetch1="https://semver.org/", fetch1_ok="Unversioned info is not semver.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#info-object", fetch2_ok="Exclusive unversioned 400 leftover semver.")),
    (p(slug="oas-parameter-deprecated", domain="oas-param-deprecated-vs-live-param", success=True, name="pdep", stack="OpenAPI 3.1 parameter deprecated + Go", field="deprecated", old="live param leftover", new="parameter deprecated", fail_err="400: leftover live param after deprecated-only", plan="Deprecated-param-only 400s leftover live. Dual-keep live for one release.", residual="client still live leftover; drop after client 4", vs="r3931 oas-operation-deprecated (param deprecated vs live leftover, not op deprecated)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="deprecated:true on parameters is not leftover live params.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#fixed-fields-9", fetch2_ok="Exclusive deprecated param 400 leftover live."),
     p(slug="leftover-live-param", domain="live-param-vs-oas-param-deprecated", success=False, name="plive", stack="OpenAPI leftover live param + Java + TS", field="deprecated", old="parameter deprecated", new="live param leftover only", fail_err="400: leftover deprecated param after live-only", plan="Live-only 400s leftover deprecated param. Freeze deprecated, spec live leftover.", residual="handoff: keep deprecated param or force live leftover", vs="r3931 leftover-live-op (live param leftover, not live op)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#fixed-fields-9", fetch1_ok="Live leftover params are not deprecated:true.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="Exclusive live param 400 leftover deprecated.")),
    (p(slug="oas-path-param-required", domain="oas-path-required-vs-optional-path", success=True, name="preq", stack="OpenAPI 3.1 path param required + Go", field="required", old="optional path leftover", new="path param required", fail_err="400: leftover optional path after required-only", plan="Path-required-only 400s leftover optional. Dual-accept optional for one release.", residual="router still optional leftover; drop after router 5", vs="r3899 oas-header-required-true (path required vs optional leftover, not header)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="Path parameters must be required; leftover optional paths fail closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-locations", fetch2_ok="Exclusive path required 400 leftover optional."),
     p(slug="leftover-optional-path", domain="optional-path-vs-oas-path-required", success=False, name="popt", stack="OpenAPI leftover optional path + Java + TS", field="required", old="path param required", new="optional path leftover only", fail_err="400: leftover required path after optional-only", plan="Optional-only 400s leftover required path. Freeze required, spec optional leftover.", residual="handoff: keep path required or force optional leftover", vs="r3899 leftover-optional-header (optional path leftover, not header)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-locations", fetch1_ok="Optional path params are not required:true.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="Exclusive optional path 400 leftover required.")),
    (p(slug="oas-format-byte", domain="oas-format-byte-vs-plain-string", success=True, name="fmtbyte", stack="OpenAPI 3.1 format=byte + Go", field="format", old="plain string leftover", new="format byte", fail_err="400: leftover plain string after format-byte-only", plan="format=byte-only 400s leftover plain string. Dual-read plain for one release.", residual="client still plain leftover; drop after client 6", vs="wrap binary-vs-base64 (format=byte vs plain leftover, not binary cartesian)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="format=byte is base64, not leftover plain strings.", fetch2="https://json-schema.org/understanding-json-schema/reference/non_json_data", fetch2_ok="Exclusive format=byte 400 leftover plain."),
     p(slug="leftover-plain-string", domain="plain-string-vs-oas-format-byte", success=False, name="plain", stack="OpenAPI leftover plain string + Java + TS", field="type", old="format byte", new="plain string leftover only", fail_err="400: leftover format=byte after plain-only", plan="Plain-only 400s leftover format=byte. Freeze byte, spec plain leftover.", residual="handoff: keep format=byte or force plain leftover", vs="wrap binary-vs-base64 (plain leftover, not binary cartesian)", fetch1="https://json-schema.org/understanding-json-schema/reference/non_json_data", fetch1_ok="Plain strings are not format=byte.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="Exclusive plain string 400 leftover byte.")),
    (p(slug="oas-security-oauth2-clientcreds", domain="oas-clientcreds-vs-password-flow", success=True, name="ccflow", stack="OpenAPI 3.1 oauth2 clientCredentials + Go", field="clientCredentials", old="password flow leftover", new="clientCredentials flow", fail_err="401: leftover password flow after clientCredentials-only", plan="clientCredentials-only 401s leftover password. Dual-accept password for one release.", residual="legacy still password leftover; drop after legacy 7", vs="wrap implicit-flow-removed (clientCredentials vs password leftover, not implicit)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#oauth-flows-object", fetch1_ok="clientCredentials is not leftover password flow.", fetch2="https://datatracker.ietf.org/doc/html/rfc6749#section-4.4", fetch2_ok="Exclusive clientCredentials 401 leftover password."),
     p(slug="leftover-password-flow", domain="password-flow-vs-oas-clientcreds", success=False, name="pwflow", stack="OpenAPI leftover password flow + Java + TS", field="password", old="clientCredentials flow", new="password flow leftover only", fail_err="401: leftover clientCredentials after password-only", plan="Password-only 401s leftover clientCredentials. Freeze clientCredentials, spec password leftover.", residual="handoff: keep clientCredentials or force password leftover", vs="wrap implicit-flow-removed (password leftover, not implicit cartesian)", fetch1="https://datatracker.ietf.org/doc/html/rfc6749#section-4.3", fetch1_ok="Password flow is not clientCredentials.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#oauth-flows-object", fetch2_ok="Exclusive password 401 leftover clientCredentials.")),
    (p(slug="oas-components-examples", domain="oas-components-examples-vs-inline-only", success=True, name="cex", stack="OpenAPI 3.1 components.examples + Go", field="examples", old="inline only leftover", new="components examples", fail_err="400: leftover inline-only after components-examples-only", plan="components.examples-only 400s leftover inline. Dual-read inline for one release.", residual="docs still inline leftover; drop after docs 5", vs="r3947 oas-example-external-value (components.examples vs inline leftover, not externalValue)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#components-object", fetch1_ok="components.examples reuse Example Objects, not leftover inline-only.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#example-object", fetch2_ok="Exclusive components.examples 400 leftover inline."),
     p(slug="leftover-inline-only-examples", domain="inline-only-vs-oas-components-examples", success=False, name="inex2", stack="OpenAPI leftover inline-only examples + Java + TS", field="example", old="components examples", new="inline only leftover only", fail_err="400: leftover components.examples after inline-only", plan="Inline-only 400s leftover components.examples. Freeze components.examples, spec inline leftover.", residual="handoff: keep components.examples or force inline leftover", vs="r3947 leftover-inline-example (inline-only leftover, not externalValue)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#example-object", fetch1_ok="Inline-only examples are not components.examples.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#components-object", fetch2_ok="Exclusive inline-only 400 leftover components.examples.")),
    (p(slug="oas-webhook-description", domain="oas-webhook-desc-vs-undocumented-webhook", success=True, name="whkdesc", stack="OpenAPI 3.1 webhook description + Go", field="description", old="undocumented webhook leftover", new="webhook description", fail_err="400: leftover undocumented webhook after description-only", plan="Webhook-description-only 400s leftover undocumented. Dual-omit description for one release.", residual="portal still undocumented leftover; drop after portal 6", vs="r3867 oas31-webhooks-map (webhook description vs undocumented leftover, not callbacks)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#path-item-object", fetch1_ok="Webhook Path Items should describe the event, leftover undocumented fail closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#oasWebhooks", fetch2_ok="Exclusive webhook description 400 leftover undocumented."),
     p(slug="leftover-undocumented-webhook", domain="undocumented-webhook-vs-oas-webhook-desc", success=False, name="whkund", stack="OpenAPI leftover undocumented webhook + Java + TS", field="webhooks", old="webhook description", new="undocumented webhook leftover only", fail_err="400: leftover description after undocumented-only", plan="Undocumented-only 400s leftover webhook description. Freeze description, spec undocumented leftover.", residual="handoff: keep webhook description or force undocumented leftover", vs="r3867 oas30-callbacks-map (undocumented leftover, not callbacks)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#oasWebhooks", fetch1_ok="Undocumented webhooks are not described Path Items.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#path-item-object", fetch2_ok="Exclusive undocumented webhook 400 leftover description.")),
    (p(slug="oas-format-iri-reference", domain="oas-iri-reference-vs-relative-path", success=True, name="iriref", stack="OpenAPI 3.1 format=iri-reference + Go", field="format", old="relative path leftover", new="format iri-reference", fail_err="400: leftover relative path after iri-reference-only", plan="iri-reference-only 400s leftover relative path. Dual-read relative for one release.", residual="cdn still relative leftover; drop after cdn 5", vs="r3899 oas-format-iri (iri-reference vs relative leftover, not absolute iri)", fetch1="https://json-schema.org/understanding-json-schema/reference/string#resource-identifiers", fetch1_ok="format=iri-reference allows relative IRIs, leftover relative paths are not that.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="Exclusive iri-reference 400 leftover relative path."),
     p(slug="leftover-relative-path", domain="relative-path-vs-oas-iri-reference", success=False, name="relp", stack="OpenAPI leftover relative path + Java + TS", field="href", old="format iri-reference", new="relative path leftover only", fail_err="400: leftover iri-reference after relative-only", plan="Relative-only 400s leftover iri-reference. Freeze iri-reference, spec relative leftover.", residual="handoff: keep iri-reference or force relative leftover", vs="r3899 leftover-ascii-uri (relative leftover, not ascii uri)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="Relative leftover paths are not format=iri-reference.", fetch2="https://json-schema.org/understanding-json-schema/reference/string#resource-identifiers", fetch2_ok="Exclusive relative path 400 leftover iri-reference.")),
    (p(slug="oas-tag-description", domain="oas-tag-desc-vs-tag-name-only", success=True, name="tagdesc", stack="OpenAPI 3.1 tag description + Go", field="description", old="tag name only leftover", new="tag description", fail_err="400: leftover tag-name-only after description-only", plan="Tag-description-only 400s leftover name-only. Dual-omit description for one release.", residual="portal still name-only leftover; drop after portal 4", vs="r3883 oas-tag-externaldocs (tag description vs name-only leftover, not externalDocs)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#tag-object", fetch1_ok="Tag description documents the tag, leftover name-only fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch2_ok="Exclusive tag description 400 leftover name-only."),
     p(slug="leftover-tag-name-only", domain="tag-name-only-vs-oas-tag-desc", success=False, name="tagnm", stack="OpenAPI leftover tag name-only + Java + TS", field="name", old="tag description", new="tag name only leftover only", fail_err="400: leftover tag description after name-only", plan="Name-only 400s leftover tag description. Freeze description, spec name leftover.", residual="handoff: keep tag description or force name-only leftover", vs="r3883 leftover-untagged-ops (name-only leftover, not untagged)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch1_ok="Name-only tags are not described.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#tag-object", fetch2_ok="Exclusive name-only 400 leftover tag description.")),
    (p(slug="oas-response-description-req", domain="oas-resp-desc-vs-missing-resp-desc", success=True, name="rdesc", stack="OpenAPI 3.1 response description + Go", field="description", old="missing resp desc leftover", new="response description", fail_err="400: leftover missing resp desc after description-only", plan="Response-description-only 400s leftover missing. Dual-omit for one release.", residual="sdk still missing leftover; drop after sdk 5", vs="r3883 oas-default-response (response description vs missing leftover, not default)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#response-object", fetch1_ok="description is required on Response Objects.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#responses-object", fetch2_ok="Exclusive response description 400 leftover missing."),
     p(slug="leftover-missing-resp-desc", domain="missing-resp-desc-vs-oas-resp-desc", success=False, name="nrdesc", stack="OpenAPI leftover missing resp desc + Java + TS", field="description", old="response description", new="missing resp desc leftover only", fail_err="400: leftover description after missing-only", plan="Missing-only 400s leftover response description. Freeze description, spec missing leftover.", residual="handoff: keep response description or force missing leftover", vs="r3883 leftover-200-only (missing resp desc leftover, not 200-only)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#responses-object", fetch1_ok="Missing descriptions are not Response.description.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#response-object", fetch2_ok="Exclusive missing resp desc 400 leftover description.")),
    (p(slug="oas-requestbody-json-required", domain="oas-json-body-vs-empty-json", success=True, name="jbody", stack="OpenAPI 3.1 JSON requestBody + Go", field="content", old="empty json leftover", new="json requestBody", fail_err="400: leftover empty json after json-body-only", plan="JSON-body-only 400s leftover empty json. Dual-accept empty for one release.", residual="batch still empty leftover; drop after batch 6", vs="r3867 oas-body-must-exist (json body vs empty leftover, not required flag)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#request-body-object", fetch1_ok="application/json requestBody is not leftover empty JSON.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch2_ok="Exclusive json body 400 leftover empty json."),
     p(slug="leftover-empty-json", domain="empty-json-vs-oas-json-body", success=False, name="ejson", stack="OpenAPI leftover empty json + Java + TS", field="content", old="json requestBody", new="empty json leftover only", fail_err="400: leftover json body after empty-only", plan="Empty-only 400s leftover json body. Freeze json body, spec empty leftover.", residual="handoff: keep json body or force empty leftover", vs="r3867 leftover-body-optional (empty json leftover, not optional body)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch1_ok="Empty JSON is not a documented requestBody.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#request-body-object", fetch2_ok="Exclusive empty json 400 leftover json body.")),
    (p(slug="oas-components-headers", domain="oas-components-headers-vs-inline-headers", success=True, name="chdr", stack="OpenAPI 3.1 components.headers + Go", field="headers", old="inline headers leftover", new="components headers", fail_err="400: leftover inline headers after components-headers-only", plan="components.headers-only 400s leftover inline. Dual-read inline for one release.", residual="proxy still inline leftover; drop after proxy 6", vs="r3899 oas-encoding-headers-map (components.headers vs inline leftover, not encoding.headers)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#components-object", fetch1_ok="components.headers reuse Header Objects, not leftover inline copies.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch2_ok="Exclusive components.headers 400 leftover inline."),
     p(slug="leftover-inline-headers", domain="inline-headers-vs-oas-components-headers", success=False, name="ihdr", stack="OpenAPI leftover inline headers + Java + TS", field="headers", old="components headers", new="inline headers leftover only", fail_err="400: leftover components.headers after inline-only", plan="Inline-only 400s leftover components.headers. Freeze components.headers, spec inline leftover.", residual="handoff: keep components.headers or force inline leftover", vs="r3899 leftover-part-headers (inline leftover, not MIME part)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch1_ok="Inline headers are not components.headers.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#components-object", fetch2_ok="Exclusive inline headers 400 leftover components.headers.")),
    (p(slug="oas-format-uri-reference", domain="oas-uri-reference-vs-opaque-href", success=True, name="uriref", stack="OpenAPI 3.1 format=uri-reference + Go", field="format", old="opaque href leftover", new="format uri-reference", fail_err="400: leftover opaque href after uri-reference-only", plan="uri-reference-only 400s leftover opaque href. Dual-read opaque for one release.", residual="sdk still opaque leftover; drop after sdk 4", vs="r3947 oas-format-uri-absolute (uri-reference vs opaque leftover, not absolute uri)", fetch1="https://json-schema.org/understanding-json-schema/reference/string#resource-identifiers", fetch1_ok="format=uri-reference is RFC 3986, not leftover opaque hrefs.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="Exclusive uri-reference 400 leftover opaque href."),
     p(slug="leftover-opaque-href", domain="opaque-href-vs-oas-uri-reference", success=False, name="ophref", stack="OpenAPI leftover opaque href + Java + TS", field="href", old="format uri-reference", new="opaque href leftover only", fail_err="400: leftover uri-reference after opaque-only", plan="Opaque-only 400s leftover uri-reference. Freeze uri-reference, spec opaque leftover.", residual="handoff: keep uri-reference or force opaque leftover", vs="r3947 leftover-path-only-url (opaque leftover, not path-only)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="Opaque hrefs are not format=uri-reference.", fetch2="https://json-schema.org/understanding-json-schema/reference/string#resource-identifiers", fetch2_ok="Exclusive opaque href 400 leftover uri-reference.")),
    (p(slug="oas-xml-name", domain="oas-xml-name-vs-property-key", success=True, name="xmlnm", stack="OpenAPI 3.1 xml.name + Go", field="name", old="property key leftover", new="xml name", fail_err="415: leftover property key after xml-name-only", plan="xml.name-only 415s leftover property key. Dual-read property key for one release.", residual="batch still key leftover; drop after batch 5", vs="r3947 oas-xml-attribute (xml.name vs property key leftover, not attribute)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#xml-object", fetch1_ok="xml.name overrides the property key on the wire.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive xml.name 415 leftover property key."),
     p(slug="leftover-property-key", domain="property-key-vs-oas-xml-name", success=False, name="pkey", stack="OpenAPI leftover property key + Java + TS", field="properties", old="xml name", new="property key leftover only", fail_err="415: leftover xml.name after property-key-only", plan="Property-key-only 415s leftover xml.name. Freeze xml.name, spec key leftover.", residual="handoff: keep xml.name or force property-key leftover", vs="r3947 leftover-xml-element (property-key leftover, not element)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Property keys are not xml.name.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#xml-object", fetch2_ok="Exclusive property key 415 leftover xml.name.")),
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
    print(json.dumps({"round": round_n, "idx": idx, "ids": [e1["id"], e2["id"]], "catalog": "r3963"}))


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
