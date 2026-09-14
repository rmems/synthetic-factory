#!/usr/bin/env python3
"""Unique OpenAPI-drift ACM catalog r4278. Fast slug load."""
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
    (p(slug="oas-xml-name-override-elem", domain="oas-xml-name-override-elem-vs-leftover-json-key-as-xml", success=True, name="ca7b1f", stack="OpenAPI 3.1 name + Go", field="name", old="json key xml leftover", new="xml name override", fail_err="415: leftover json key xml leftover after xml name override-only", plan="xml name override-only 415s leftover json key xml leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (xml name override vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#xml-object", fetch1_ok="xml.name overrides the JSON key, leftover key-as-xml fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive xml name 415 leftover json key."),
     p(slug="leftover-json-key-as-xml", domain="leftover-json-key-as-xml-vs-oas-xml-name-override-elem", success=False, name="1392ea", stack="OpenAPI leftover name + Java + TS", field="name", old="xml name override", new="json key xml leftover only", fail_err="415: leftover xml name override after json key xml leftover-only", plan="json key xml leftover-only 415s leftover xml name override. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (json key xml leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive xml name 415 leftover json key.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#xml-object", fetch2_ok="xml.name overrides the JSON key, leftover key-as-xml fails closed.")),
    (p(slug="oas-discriminator-property", domain="oas-discriminator-property-vs-leftover-implicit-type-field", success=True, name="ac62be", stack="OpenAPI 3.1 propertyName + Go", field="propertyName", old="implicit type leftover", new="discriminator propertyName", fail_err="400: leftover implicit type leftover after discriminator propertyName-only", plan="discriminator propertyName-only 400s leftover implicit type leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (discriminator propertyName vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#discriminator-object", fetch1_ok="propertyName is required, leftover implicit type fields fail closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive discriminator 400 leftover implicit."),
     p(slug="leftover-implicit-type-field", domain="leftover-implicit-type-field-vs-oas-discriminator-property", success=False, name="fcb8e9", stack="OpenAPI leftover propertyName + Java + TS", field="propertyName", old="discriminator propertyName", new="implicit type leftover only", fail_err="400: leftover discriminator propertyName after implicit type leftover-only", plan="implicit type leftover-only 400s leftover discriminator propertyName. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (implicit type leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive discriminator 400 leftover implicit.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#discriminator-object", fetch2_ok="propertyName is required, leftover implicit type fields fail closed.")),
    (p(slug="oas-encoding-content-type-xml", domain="oas-encoding-content-type-xml-vs-leftover-json-part-as-xml", success=True, name="d0128f", stack="OpenAPI 3.1 contentType + Go", field="contentType", old="json part xml leftover", new="encoding contentType xml", fail_err="415: leftover json part xml leftover after encoding contentType xml-only", plan="encoding contentType xml-only 415s leftover json part xml leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (encoding contentType xml vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#encoding-object", fetch1_ok="encoding.contentType xml is not leftover JSON parts labeled xml.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch2_ok="Exclusive encoding xml 415 leftover json part."),
     p(slug="leftover-json-part-as-xml", domain="leftover-json-part-as-xml-vs-oas-encoding-content-type-xml", success=False, name="b0f30a", stack="OpenAPI leftover contentType + Java + TS", field="contentType", old="encoding contentType xml", new="json part xml leftover only", fail_err="415: leftover encoding contentType xml after json part xml leftover-only", plan="json part xml leftover-only 415s leftover encoding contentType xml. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (json part xml leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch1_ok="Exclusive encoding xml 415 leftover json part.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#encoding-object", fetch2_ok="encoding.contentType xml is not leftover JSON parts labeled xml.")),
    (p(slug="oas-callback-runtime-expr", domain="oas-callback-runtime-expr-vs-leftover-fixed-callback-href", success=True, name="e91846", stack="OpenAPI 3.1 expression + Go", field="expression", old="fixed callback leftover", new="callback runtime expr", fail_err="400: leftover fixed callback leftover after callback runtime expr-only", plan="callback runtime expr-only 400s leftover fixed callback leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (callback runtime expr vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#callback-object", fetch1_ok="Callback keys are runtime expressions, leftover fixed hrefs fail closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#runtime-expressions", fetch2_ok="Exclusive callback expr 400 leftover fixed href."),
     p(slug="leftover-fixed-callback-href", domain="leftover-fixed-callback-href-vs-oas-callback-runtime-expr", success=False, name="a4f91b", stack="OpenAPI leftover expression + Java + TS", field="expression", old="callback runtime expr", new="fixed callback leftover only", fail_err="400: leftover callback runtime expr after fixed callback leftover-only", plan="fixed callback leftover-only 400s leftover callback runtime expr. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (fixed callback leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#runtime-expressions", fetch1_ok="Exclusive callback expr 400 leftover fixed href.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#callback-object", fetch2_ok="Callback keys are runtime expressions, leftover fixed hrefs fail closed.")),
    (p(slug="oas-webhook-path-item-post", domain="oas-webhook-path-item-post-vs-leftover-webhook-get-only", success=True, name="c15c7d", stack="OpenAPI 3.1 post + Go", field="post", old="webhook GET leftover", new="webhook POST pathItem", fail_err="400: leftover webhook GET leftover after webhook POST pathItem-only", plan="webhook POST pathItem-only 400s leftover webhook GET leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (webhook POST pathItem vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#oasWebhooks", fetch1_ok="Webhook path items typically POST, leftover GET-only fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#path-item-object", fetch2_ok="Exclusive webhook POST 400 leftover GET."),
     p(slug="leftover-webhook-get-only", domain="leftover-webhook-get-only-vs-oas-webhook-path-item-post", success=False, name="4faee2", stack="OpenAPI leftover post + Java + TS", field="post", old="webhook POST pathItem", new="webhook GET leftover only", fail_err="400: leftover webhook POST pathItem after webhook GET leftover-only", plan="webhook GET leftover-only 400s leftover webhook POST pathItem. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (webhook GET leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#path-item-object", fetch1_ok="Exclusive webhook POST 400 leftover GET.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#oasWebhooks", fetch2_ok="Webhook path items typically POST, leftover GET-only fails closed.")),
    (p(slug="oas-components-responses-ref", domain="oas-components-responses-ref-vs-leftover-inline-response-only", success=True, name="a013e9", stack="OpenAPI 3.1 responses + Go", field="responses", old="inline response leftover", new="components responses ref", fail_err="400: leftover inline response leftover after components responses ref-only", plan="components responses ref-only 400s leftover inline response leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (components responses ref vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#components-object", fetch1_ok="components.responses reuse, leftover inline-only is not that.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#response-object", fetch2_ok="Exclusive components responses 400 leftover inline."),
     p(slug="leftover-inline-response-only", domain="leftover-inline-response-only-vs-oas-components-responses-ref", success=False, name="ad0113", stack="OpenAPI leftover responses + Java + TS", field="responses", old="components responses ref", new="inline response leftover only", fail_err="400: leftover components responses ref after inline response leftover-only", plan="inline response leftover-only 400s leftover components responses ref. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (inline response leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#response-object", fetch1_ok="Exclusive components responses 400 leftover inline.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#components-object", fetch2_ok="components.responses reuse, leftover inline-only is not that.")),
    (p(slug="oas-security-empty-optional", domain="oas-security-empty-optional-vs-leftover-always-require-auth", success=True, name="6e6433", stack="OpenAPI 3.1 security + Go", field="security", old="always auth leftover", new="empty security optional", fail_err="401: leftover always auth leftover after empty security optional-only", plan="empty security optional-only 401s leftover always auth leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (empty security optional vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#security-requirement-object", fetch1_ok="Empty security makes the op optional-auth, leftover always-require fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch2_ok="Exclusive optional security 401 leftover always auth."),
     p(slug="leftover-always-require-auth", domain="leftover-always-require-auth-vs-oas-security-empty-optional", success=False, name="57d976", stack="OpenAPI leftover security + Java + TS", field="security", old="empty security optional", new="always auth leftover only", fail_err="401: leftover empty security optional after always auth leftover-only", plan="always auth leftover-only 401s leftover empty security optional. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (always auth leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch1_ok="Exclusive optional security 401 leftover always auth.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#security-requirement-object", fetch2_ok="Empty security makes the op optional-auth, leftover always-require fails closed.")),
    (p(slug="oas-api-key-cookie-name", domain="oas-api-key-cookie-name-vs-leftover-api-key-header-only", success=True, name="9ce85a", stack="OpenAPI 3.1 in + Go", field="in", old="header apikey leftover", new="apiKey cookie name", fail_err="401: leftover header apikey leftover after apiKey cookie name-only", plan="apiKey cookie name-only 401s leftover header apikey leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (apiKey cookie name vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch1_ok="apiKey in cookie is not leftover header-only keys.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#security-requirement-object", fetch2_ok="Exclusive cookie apikey 401 leftover header."),
     p(slug="leftover-api-key-header-only", domain="leftover-api-key-header-only-vs-oas-api-key-cookie-name", success=False, name="a8d151", stack="OpenAPI leftover in + Java + TS", field="in", old="apiKey cookie name", new="header apikey leftover only", fail_err="401: leftover apiKey cookie name after header apikey leftover-only", plan="header apikey leftover-only 401s leftover apiKey cookie name. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (header apikey leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#security-requirement-object", fetch1_ok="Exclusive cookie apikey 401 leftover header.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch2_ok="apiKey in cookie is not leftover header-only keys.")),
    (p(slug="oas-format-uriref-relative", domain="oas-format-uriref-relative-vs-leftover-absolute-uri-only", success=True, name="4b034c", stack="OpenAPI 3.1 format + Go", field="format", old="absolute uri leftover", new="format uri-reference", fail_err="400: leftover absolute uri leftover after format uri-reference-only", plan="format uri-reference-only 400s leftover absolute uri leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (format uri-reference vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/string#resource-identifiers", fetch1_ok="format=uri-reference allows relative, leftover absolute-only fails closed.", fetch2="https://datatracker.ietf.org/doc/html/rfc3986", fetch2_ok="Exclusive uri-reference 400 leftover absolute."),
     p(slug="leftover-absolute-uri-only", domain="leftover-absolute-uri-only-vs-oas-format-uriref-relative", success=False, name="bd48ad", stack="OpenAPI leftover format + Java + TS", field="format", old="format uri-reference", new="absolute uri leftover only", fail_err="400: leftover format uri-reference after absolute uri leftover-only", plan="absolute uri leftover-only 400s leftover format uri-reference. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (absolute uri leftover leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc3986", fetch1_ok="Exclusive uri-reference 400 leftover absolute.", fetch2="https://json-schema.org/understanding-json-schema/reference/string#resource-identifiers", fetch2_ok="format=uri-reference allows relative, leftover absolute-only fails closed.")),
    (p(slug="oas-format-idn-hostname", domain="oas-format-idn-hostname-vs-leftover-ascii-hostname-only", success=True, name="394573", stack="OpenAPI 3.1 format + Go", field="format", old="ascii hostname leftover", new="format idn-hostname", fail_err="400: leftover ascii hostname leftover after format idn-hostname-only", plan="format idn-hostname-only 400s leftover ascii hostname leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (format idn-hostname vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/string#idn-hostname", fetch1_ok="idn-hostname is U-label, leftover ASCII-only fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="Exclusive idn-hostname 400 leftover ascii."),
     p(slug="leftover-ascii-hostname-only", domain="leftover-ascii-hostname-only-vs-oas-format-idn-hostname", success=False, name="a79899", stack="OpenAPI leftover format + Java + TS", field="format", old="format idn-hostname", new="ascii hostname leftover only", fail_err="400: leftover format idn-hostname after ascii hostname leftover-only", plan="ascii hostname leftover-only 400s leftover format idn-hostname. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (ascii hostname leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="Exclusive idn-hostname 400 leftover ascii.", fetch2="https://json-schema.org/understanding-json-schema/reference/string#idn-hostname", fetch2_ok="idn-hostname is U-label, leftover ASCII-only fails closed.")),
    (p(slug="oas-format-ipv4-strict", domain="oas-format-ipv4-strict-vs-leftover-dotted-quad-string", success=True, name="9616e4", stack="OpenAPI 3.1 format + Go", field="format", old="dotted quad leftover", new="format ipv4", fail_err="400: leftover dotted quad leftover after format ipv4-only", plan="format ipv4-only 400s leftover dotted quad leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (format ipv4 vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/string#ipv4", fetch1_ok="format=ipv4 is RFC2673, leftover dotted strings fail closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="Exclusive ipv4 400 leftover dotted quad."),
     p(slug="leftover-dotted-quad-string", domain="leftover-dotted-quad-string-vs-oas-format-ipv4-strict", success=False, name="a924c5", stack="OpenAPI leftover format + Java + TS", field="format", old="format ipv4", new="dotted quad leftover only", fail_err="400: leftover format ipv4 after dotted quad leftover-only", plan="dotted quad leftover-only 400s leftover format ipv4. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (dotted quad leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="Exclusive ipv4 400 leftover dotted quad.", fetch2="https://json-schema.org/understanding-json-schema/reference/string#ipv4", fetch2_ok="format=ipv4 is RFC2673, leftover dotted strings fail closed.")),
    (p(slug="oas-schema-pattern-js", domain="oas-schema-pattern-js-vs-leftover-posix-ere", success=True, name="5a2cdc", stack="OpenAPI 3.1 pattern + Go", field="pattern", old="posix ere leftover", new="ECMA pattern", fail_err="400: leftover posix ere leftover after ECMA pattern-only", plan="ECMA pattern-only 400s leftover posix ere leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (ECMA pattern vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/regular_expressions", fetch1_ok="pattern is ECMA-262, leftover POSIX ERE fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive ECMA pattern 400 leftover POSIX."),
     p(slug="leftover-posix-ere", domain="leftover-posix-ere-vs-oas-schema-pattern-js", success=False, name="6e6fc3", stack="OpenAPI leftover pattern + Java + TS", field="pattern", old="ECMA pattern", new="posix ere leftover only", fail_err="400: leftover ECMA pattern after posix ere leftover-only", plan="posix ere leftover-only 400s leftover ECMA pattern. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (posix ere leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive ECMA pattern 400 leftover POSIX.", fetch2="https://json-schema.org/understanding-json-schema/reference/regular_expressions", fetch2_ok="pattern is ECMA-262, leftover POSIX ERE fails closed.")),
    (p(slug="oas-additional-properties-false", domain="oas-additional-properties-false-vs-leftover-ignore-unknown-keys", success=True, name="480a40", stack="OpenAPI 3.1 additionalProperties + Go", field="additionalProperties", old="ignore unknown leftover", new="additionalProperties false", fail_err="400: leftover ignore unknown leftover after additionalProperties false-only", plan="additionalProperties false-only 400s leftover ignore unknown leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (additionalProperties false vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/object#additionalproperties", fetch1_ok="additionalProperties false rejects unknown keys, leftover ignore fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive additionalProperties false 400 leftover ignore."),
     p(slug="leftover-ignore-unknown-keys", domain="leftover-ignore-unknown-keys-vs-oas-additional-properties-false", success=False, name="a03c5e", stack="OpenAPI leftover additionalProperties + Java + TS", field="additionalProperties", old="additionalProperties false", new="ignore unknown leftover only", fail_err="400: leftover additionalProperties false after ignore unknown leftover-only", plan="ignore unknown leftover-only 400s leftover additionalProperties false. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (ignore unknown leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive additionalProperties false 400 leftover ignore.", fetch2="https://json-schema.org/understanding-json-schema/reference/object#additionalproperties", fetch2_ok="additionalProperties false rejects unknown keys, leftover ignore fails closed.")),
    (p(slug="oas-schema-contains-item", domain="oas-schema-contains-item-vs-leftover-unvalidated-array-elem", success=True, name="60c158", stack="OpenAPI 3.1 contains + Go", field="contains", old="unvalidated elem leftover", new="schema contains", fail_err="400: leftover unvalidated elem leftover after schema contains-only", plan="schema contains-only 400s leftover unvalidated elem leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (schema contains vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/array#contains", fetch1_ok="contains validates at least one item, leftover unvalidated fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive contains 400 leftover unvalidated."),
     p(slug="leftover-unvalidated-array-elem", domain="leftover-unvalidated-array-elem-vs-oas-schema-contains-item", success=False, name="59af1d", stack="OpenAPI leftover contains + Java + TS", field="contains", old="schema contains", new="unvalidated elem leftover only", fail_err="400: leftover schema contains after unvalidated elem leftover-only", plan="unvalidated elem leftover-only 400s leftover schema contains. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (unvalidated elem leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive contains 400 leftover unvalidated.", fetch2="https://json-schema.org/understanding-json-schema/reference/array#contains", fetch2_ok="contains validates at least one item, leftover unvalidated fails closed.")),
    (p(slug="oas-unique-items-true", domain="oas-unique-items-true-vs-leftover-duplicate-array-ok", success=True, name="a7ecd8", stack="OpenAPI 3.1 uniqueItems + Go", field="uniqueItems", old="duplicate array leftover", new="uniqueItems true", fail_err="400: leftover duplicate array leftover after uniqueItems true-only", plan="uniqueItems true-only 400s leftover duplicate array leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (uniqueItems true vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/array#uniqueitems", fetch1_ok="uniqueItems true rejects duplicates, leftover duplicates fail closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive uniqueItems 400 leftover dups."),
     p(slug="leftover-duplicate-array-ok", domain="leftover-duplicate-array-ok-vs-oas-unique-items-true", success=False, name="71685e", stack="OpenAPI leftover uniqueItems + Java + TS", field="uniqueItems", old="uniqueItems true", new="duplicate array leftover only", fail_err="400: leftover uniqueItems true after duplicate array leftover-only", plan="duplicate array leftover-only 400s leftover uniqueItems true. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (duplicate array leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive uniqueItems 400 leftover dups.", fetch2="https://json-schema.org/understanding-json-schema/reference/array#uniqueitems", fetch2_ok="uniqueItems true rejects duplicates, leftover duplicates fail closed.")),
    (p(slug="oas-operation-callbacks-map", domain="oas-operation-callbacks-map-vs-leftover-poll-instead-callback", success=True, name="aac044", stack="OpenAPI 3.1 callbacks + Go", field="callbacks", old="poll leftover", new="operation callbacks map", fail_err="400: leftover poll leftover after operation callbacks map-only", plan="operation callbacks map-only 400s leftover poll leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (operation callbacks map vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch1_ok="operation.callbacks is not leftover client polling.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#callback-object", fetch2_ok="Exclusive callbacks 400 leftover poll."),
     p(slug="leftover-poll-instead-callback", domain="leftover-poll-instead-callback-vs-oas-operation-callbacks-map", success=False, name="92e45a", stack="OpenAPI leftover callbacks + Java + TS", field="callbacks", old="operation callbacks map", new="poll leftover only", fail_err="400: leftover operation callbacks map after poll leftover-only", plan="poll leftover-only 400s leftover operation callbacks map. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (poll leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#callback-object", fetch1_ok="Exclusive callbacks 400 leftover poll.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch2_ok="operation.callbacks is not leftover client polling.")),
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
    print(json.dumps({"round": round_n, "idx": idx, "ids": [e1["id"], e2["id"]], "catalog": "r4278"}))


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
