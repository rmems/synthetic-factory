#!/usr/bin/env python3
"""New unique OpenAPI-drift ACM catalog from r4007.

BAN r4006 oas-allowemptyvalue-header / leftover-omit-header-empty,
r3866 proto-optional, r3850 BCP47/ISO639, r3713 smile/cbor,
r3560 422/207, w131 cartesian, and r3561–r3993 mill catalogs.
"""
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
    (p(slug="oas-info-summary-required", domain="oas-info-summary-vs-missing", success=True, name="infosum", stack="OpenAPI 3.1 info.summary + Go", field="summary", old="missing info summary leftover", new="info summary", fail_err="400: leftover missing info summary after summary-only", plan="info.summary-only 400s leftover missing. Dual-omit summary for one release.", residual="portal still missing leftover; drop after portal 5", vs="r3993 oas-info-title-required (info.summary vs missing leftover, not title)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#info-object", fetch1_ok="info.summary is a short description, leftover missing summaries fail closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#fixed-fields", fetch2_ok="Exclusive info.summary 400 leftover missing."),
     p(slug="leftover-missing-info-summary", domain="missing-info-summary-vs-oas", success=False, name="noisum", stack="OpenAPI leftover missing info summary + Java + TS", field="summary", old="info summary", new="missing info summary leftover only", fail_err="400: leftover info.summary after missing-only", plan="Missing-only 400s leftover info.summary. Freeze summary, spec missing leftover.", residual="handoff: keep info.summary or force missing leftover", vs="r3993 leftover-missing-title (missing info summary leftover, not missing title)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#fixed-fields", fetch1_ok="Missing info.summary is not the 3.1 info object.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#info-object", fetch2_ok="Exclusive missing info summary 400 leftover summary.")),
    (p(slug="oas-json-schema-comment", domain="oas-schema-comment-vs-x-comment", success=True, name="schcmt", stack="OpenAPI 3.1 $comment + Go", field="$comment", old="x-comment leftover", new="schema dollarcomment", fail_err="400: leftover x-comment after $comment-only", plan="$comment-only 400s leftover x-comment. Dual-read x-comment for one release.", residual="codegen still x-comment leftover; drop after codegen 6", vs="r3993 oas-schema-id ($comment vs x-comment leftover, not $id)", fetch1="https://json-schema.org/understanding-json-schema/reference/generic#comment", fetch1_ok="$comment is an annotation, not leftover x-comment.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive $comment 400 leftover x-comment."),
     p(slug="leftover-x-comment", domain="x-comment-vs-oas-schema-comment", success=False, name="xcomment", stack="OpenAPI leftover x-comment + Java + TS", field="x-comment", old="schema dollarcomment", new="x-comment leftover only", fail_err="400: leftover $comment after x-comment-only", plan="x-comment-only 400s leftover $comment. Freeze $comment, spec x-comment leftover.", residual="handoff: keep $comment or force x-comment leftover", vs="r3993 leftover-missing-schema-id (x-comment leftover, not missing $id)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="x-comment extensions are not $comment.", fetch2="https://json-schema.org/understanding-json-schema/reference/generic#comment", fetch2_ok="Exclusive x-comment 400 leftover $comment.")),
    (p(slug="oas-schema-examples-array", domain="oas-examples-array-vs-single-example", success=True, name="schex", stack="OpenAPI 3.1 schema examples + Go", field="examples", old="single example leftover", new="schema examples array", fail_err="400: leftover single example after examples-array-only", plan="examples-array-only 400s leftover single example. Dual-read single for one release.", residual="docs still single leftover; drop after docs 5", vs="r3947 oas-example-external-value (schema examples vs single leftover, not externalValue)", fetch1="https://json-schema.org/understanding-json-schema/reference/generic#enum", fetch1_ok="JSON Schema examples is an array, not leftover example singular.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive examples array 400 leftover single example."),
     p(slug="leftover-single-example", domain="single-example-vs-oas-examples-array", success=False, name="sngex", stack="OpenAPI leftover single example + Java + TS", field="example", old="schema examples array", new="single example leftover only", fail_err="400: leftover examples array after single-only", plan="Single-only 400s leftover examples array. Freeze examples, spec single leftover.", residual="handoff: keep examples array or force single leftover", vs="r3947 leftover-inline-example (single leftover, not inline example)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Singular example is not examples[].", fetch2="https://json-schema.org/understanding-json-schema/reference/generic#enum", fetch2_ok="Exclusive single example 400 leftover examples array.")),
    (p(slug="oas-format-duration-week", domain="oas-duration-week-vs-days-int", success=True, name="durwk", stack="OpenAPI 3.1 format=duration PnW + Go", field="format", old="days int leftover", new="duration week", fail_err="400: leftover days-int after duration-week-only", plan="duration-week-only 400s leftover days-int. Dual-read days for one release.", residual="batch still days leftover; drop after batch 6", vs="r3883 oas-format-duration (week duration vs days leftover, not generic duration)", fetch1="https://json-schema.org/understanding-json-schema/reference/string#duration", fetch1_ok="format=duration PnW is ISO 8601 weeks, not leftover day counts.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="Exclusive duration week 400 leftover days-int."),
     p(slug="leftover-days-int", domain="days-int-vs-oas-duration-week", success=False, name="daysi", stack="OpenAPI leftover days int + Java + TS", field="days", old="duration week", new="days int leftover only", fail_err="400: leftover duration-week after days-only", plan="Days-only 400s leftover duration-week. Freeze duration, spec days leftover.", residual="handoff: keep duration-week or force days leftover", vs="r3883 leftover-seconds-int (days leftover, not seconds-int)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="Integer days are not format=duration weeks.", fetch2="https://json-schema.org/understanding-json-schema/reference/string#duration", fetch2_ok="Exclusive days-int 400 leftover duration-week.")),
    (p(slug="oas-format-hostname-puny", domain="oas-puny-hostname-vs-raw-idn", success=True, name="punyhn", stack="OpenAPI 3.1 punycode hostname + Go", field="format", old="raw idn host leftover", new="punycode hostname", fail_err="400: leftover raw idn after punycode-only", plan="punycode-hostname-only 400s leftover raw idn. Dual-read raw idn for one release.", residual="dns still raw leftover; drop after dns 5", vs="r3947 leftover-punycode-only (puny hostname vs raw idn leftover, not punycode-only mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/string#hostname", fetch1_ok="format=hostname is ASCII/punycode, leftover raw IDN fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="Exclusive punycode hostname 400 leftover raw idn."),
     p(slug="leftover-raw-idn-host", domain="raw-idn-vs-oas-puny-hostname", success=False, name="rawidn", stack="OpenAPI leftover raw idn host + Java + TS", field="host", old="punycode hostname", new="raw idn host leftover only", fail_err="400: leftover punycode hostname after raw-idn-only", plan="Raw-idn-only 400s leftover punycode hostname. Freeze punycode, spec raw leftover.", residual="handoff: keep punycode hostname or force raw leftover", vs="r3947 oas-format-hostname-idn (raw leftover, not idn-hostname mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="Raw IDN hosts are not format=hostname punycode.", fetch2="https://json-schema.org/understanding-json-schema/reference/string#hostname", fetch2_ok="Exclusive raw idn 400 leftover punycode hostname.")),
    (p(slug="oas-security-oauth2-refresh", domain="oas-refresh-token-vs-no-refresh", success=True, name="refresh", stack="OpenAPI 3.1 oauth2 refreshUrl + Go", field="refreshUrl", old="no refresh leftover", new="oauth2 refreshUrl", fail_err="401: leftover no-refresh after refreshUrl-only", plan="refreshUrl-only 401s leftover no-refresh. Dual-omit refresh for one release.", residual="spa still no-refresh leftover; drop after spa 7", vs="r3978 oas-security-oauth2-authcode (refreshUrl vs no-refresh leftover, not auth code)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#oauth-flow-object", fetch1_ok="refreshUrl documents token refresh, leftover no-refresh fails closed.", fetch2="https://datatracker.ietf.org/doc/html/rfc6749#section-6", fetch2_ok="Exclusive refreshUrl 401 leftover no-refresh."),
     p(slug="leftover-no-refresh", domain="no-refresh-vs-oas-refresh-token", success=False, name="noref", stack="OpenAPI leftover no refresh + Java + TS", field="tokenUrl", old="oauth2 refreshUrl", new="no refresh leftover only", fail_err="401: leftover refreshUrl after no-refresh-only", plan="No-refresh-only 401s leftover refreshUrl. Freeze refreshUrl, spec no-refresh leftover.", residual="handoff: keep refreshUrl or force no-refresh leftover", vs="r3978 leftover-password-token (no-refresh leftover, not password token)", fetch1="https://datatracker.ietf.org/doc/html/rfc6749#section-6", fetch1_ok="No refresh endpoint is not refreshUrl.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#oauth-flow-object", fetch2_ok="Exclusive no-refresh 401 leftover refreshUrl.")),
    (p(slug="oas-parameter-style-label-query", domain="oas-query-label-vs-query-simple", success=True, name="qlabel", stack="OpenAPI 3.1 query style=label + Go", field="style", old="query simple leftover", new="query label style", fail_err="400: leftover query simple after label-only", plan="Query-label-only 400s leftover simple. Dual-read simple for one release.", residual="gateway still simple leftover; drop after gateway 5", vs="r3931 oas-path-label-style (query label vs simple leftover, not path label)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch1_ok="Query style=label is not leftover style=simple.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="Exclusive query label 400 leftover simple."),
     p(slug="leftover-query-simple", domain="query-simple-vs-oas-query-label", success=False, name="qsimpl", stack="OpenAPI leftover query simple + Java + TS", field="style", old="query label style", new="query simple leftover only", fail_err="400: leftover query label after simple-only", plan="Simple-only 400s leftover query label. Freeze label, spec simple leftover.", residual="handoff: keep query label or force simple leftover", vs="r3883 leftover-path-simple (query simple leftover, not path simple)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="Query simple is not style=label.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch2_ok="Exclusive query simple 400 leftover label.")),
    (p(slug="oas-header-deprecated", domain="oas-header-deprecated-vs-live-header", success=True, name="hdrdep", stack="OpenAPI 3.1 header deprecated + Go", field="deprecated", old="live header leftover", new="header deprecated", fail_err="400: leftover live header after deprecated-only", plan="Deprecated-header-only 400s leftover live. Dual-keep live for one release.", residual="proxy still live leftover; drop after proxy 6", vs="r3963 oas-parameter-deprecated (header deprecated vs live leftover, not param)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch1_ok="deprecated:true on headers is not leftover live headers.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="Exclusive deprecated header 400 leftover live."),
     p(slug="leftover-live-header", domain="live-header-vs-oas-header-deprecated", success=False, name="hdrlive", stack="OpenAPI leftover live header + Java + TS", field="deprecated", old="header deprecated", new="live header leftover only", fail_err="400: leftover deprecated header after live-only", plan="Live-only 400s leftover deprecated header. Freeze deprecated, spec live leftover.", residual="handoff: keep deprecated header or force live leftover", vs="r3963 leftover-live-param (live header leftover, not live param)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="Live leftover headers are not deprecated:true.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch2_ok="Exclusive live header 400 leftover deprecated.")),
    (p(slug="oas-response-links-required", domain="oas-resp-links-vs-no-links", success=True, name="rlinks", stack="OpenAPI 3.1 response links + Go", field="links", old="no links leftover", new="response links", fail_err="400: leftover no-links after links-only", plan="Response-links-only 400s leftover no-links. Dual-omit links for one release.", residual="sdk still no-links leftover; drop after sdk 5", vs="r3993 oas-components-links (response links vs no-links leftover, not components.links)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#response-object", fetch1_ok="Response links advertise follow-on operations, leftover no-links fail closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#link-object", fetch2_ok="Exclusive response links 400 leftover no-links."),
     p(slug="leftover-no-links", domain="no-links-vs-oas-resp-links", success=False, name="nolnk", stack="OpenAPI leftover no links + Java + TS", field="links", old="response links", new="no links leftover only", fail_err="400: leftover response links after no-links-only", plan="No-links-only 400s leftover response links. Freeze links, spec no-links leftover.", residual="handoff: keep response links or force no-links leftover", vs="r3993 leftover-inline-links (no-links leftover, not inline links)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#link-object", fetch1_ok="Missing links are not Response.links.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#response-object", fetch2_ok="Exclusive no-links 400 leftover response links.")),
    (p(slug="oas-webhook-put", domain="oas-webhook-put-vs-webhook-patch", success=True, name="whkput", stack="OpenAPI 3.1 webhook PUT + Go", field="put", old="webhook PATCH leftover", new="webhook PUT", fail_err="405: leftover webhook PATCH after PUT-only", plan="Webhook-PUT-only 405s leftover PATCH. Dual-accept PATCH for one release.", residual="edge still PATCH leftover; drop after edge 4", vs="r3899 oas-webhook-post-only (webhook PUT vs PATCH leftover, not POST)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#oasWebhooks", fetch1_ok="Webhook Path Items may PUT; leftover PATCH is not the contract.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#path-item-object", fetch2_ok="Exclusive webhook PUT 405 leftover PATCH."),
     p(slug="leftover-webhook-patch", domain="webhook-patch-vs-oas-webhook-put", success=False, name="whkpat", stack="OpenAPI leftover webhook PATCH + Java + TS", field="patch", old="webhook PUT", new="webhook PATCH leftover only", fail_err="405: leftover webhook PUT after PATCH-only", plan="Webhook-PATCH-only 405s leftover PUT. Freeze PUT, spec PATCH leftover.", residual="handoff: keep webhook PUT or force PATCH leftover", vs="r3899 leftover-webhook-get (PATCH leftover, not GET)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#path-item-object", fetch1_ok="Webhook PATCH is not the PUT-only contract.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#oasWebhooks", fetch2_ok="Exclusive webhook PATCH 405 leftover PUT.")),
    (p(slug="oas-servers-enum-default-match", domain="oas-enum-default-vs-outside-enum", success=True, name="enuddef", stack="OpenAPI 3.1 server enum default match + Go", field="default", old="default outside enum leftover", new="enum matching default", fail_err="400: leftover default-outside-enum after matching-only", plan="Matching-default-only 400s leftover outside-enum. Dual-accept outside for one release.", residual="mesh still outside leftover; drop after mesh 6", vs="r3867 oas-srv-var-enum (enum matching default vs outside leftover, not enum vs free host)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#server-variable-object", fetch1_ok="Server variable default must be in enum when enum is present.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#server-object", fetch2_ok="Exclusive matching default 400 leftover outside-enum."),
     p(slug="leftover-default-outside-enum", domain="outside-enum-vs-oas-enum-default", success=False, name="outdef", stack="OpenAPI leftover default outside enum + Java + TS", field="default", old="enum matching default", new="default outside enum leftover only", fail_err="400: leftover matching default after outside-only", plan="Outside-only 400s leftover matching default. Freeze matching, spec outside leftover.", residual="handoff: keep matching default or force outside leftover", vs="r3899 leftover-missing-srv-default (outside leftover, not missing default)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#server-object", fetch1_ok="A default outside enum is not valid.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#server-variable-object", fetch2_ok="Exclusive outside-enum 400 leftover matching default.")),
    (p(slug="oas-discriminator-mapping-explicit", domain="oas-disc-mapping-vs-implicit", success=True, name="dmap", stack="OpenAPI 3.1 discriminator.mapping + Go", field="mapping", old="implicit disc leftover", new="explicit discriminator mapping", fail_err="400: leftover implicit disc after mapping-only", plan="Explicit-mapping-only 400s leftover implicit. Dual-read implicit for one release.", residual="sdk still implicit leftover; drop after sdk 5", vs="r01 discriminator.mapping miss (explicit mapping vs implicit leftover, not mapping miss)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#discriminator-object", fetch1_ok="mapping remaps payload values to schemas; leftover implicit names fail closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive explicit mapping 400 leftover implicit."),
     p(slug="leftover-implicit-disc", domain="implicit-disc-vs-oas-disc-mapping", success=False, name="idisc", stack="OpenAPI leftover implicit discriminator + Java + TS", field="propertyName", old="explicit discriminator mapping", new="implicit disc leftover only", fail_err="400: leftover mapping after implicit-only", plan="Implicit-only 400s leftover explicit mapping. Freeze mapping, spec implicit leftover.", residual="handoff: keep explicit mapping or force implicit leftover", vs="r3883 leftover-type-field (implicit leftover, not type field)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Implicit discriminator names are not mapping.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#discriminator-object", fetch2_ok="Exclusive implicit disc 400 leftover mapping.")),
    (p(slug="oas-xml-attribute-name", domain="oas-xml-attr-name-vs-element-name", success=True, name="xaname", stack="OpenAPI 3.1 xml.attribute name + Go", field="name", old="element name leftover", new="xml attribute name", fail_err="415: leftover element name after attribute-name-only", plan="xml.attribute-name-only 415s leftover element name. Dual-read element for one release.", residual="batch still element leftover; drop after batch 5", vs="r3947 oas-xml-attribute (attribute name vs element leftover, not attribute bool)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#xml-object", fetch1_ok="xml.name with attribute:true is not leftover element names.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive xml attribute name 415 leftover element."),
     p(slug="leftover-element-name-xml", domain="element-name-vs-oas-xml-attr-name", success=False, name="xelname", stack="OpenAPI leftover xml element name + Java + TS", field="name", old="xml attribute name", new="element name leftover only", fail_err="415: leftover attribute name after element-only", plan="Element-only 415s leftover xml attribute name. Freeze attribute name, spec element leftover.", residual="handoff: keep xml attribute name or force element leftover", vs="r3947 leftover-xml-element (element name leftover, not xml.element mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Element names are not xml.attribute names.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#xml-object", fetch2_ok="Exclusive element name 415 leftover attribute name.")),
    (p(slug="oas-content-encoding-7bit", domain="oas-7bit-vs-8bit-text", success=True, name="enc7", stack="OpenAPI 3.1 contentEncoding 7bit + Go", field="contentEncoding", old="8bit text leftover", new="7bit encoding", fail_err="415: leftover 8bit after 7bit-only", plan="7bit-only 415s leftover 8bit. Dual-read 8bit for one release.", residual="mail still 8bit leftover; drop after mail 6", vs="r3915 oas-content-b64url (7bit vs 8bit leftover, not base64url)", fetch1="https://json-schema.org/understanding-json-schema/reference/non_json_data#contentencoding", fetch1_ok="contentEncoding=7bit is not leftover 8bit text.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive 7bit 415 leftover 8bit."),
     p(slug="leftover-8bit-text", domain="8bit-text-vs-oas-7bit", success=False, name="enc8", stack="OpenAPI leftover 8bit text + Java + TS", field="contentEncoding", old="7bit encoding", new="8bit text leftover only", fail_err="415: leftover 7bit after 8bit-only", plan="8bit-only 415s leftover 7bit. Freeze 7bit, spec 8bit leftover.", residual="handoff: keep 7bit or force 8bit leftover", vs="r3915 leftover-std-b64 (8bit leftover, not std base64)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="8bit text is not contentEncoding=7bit.", fetch2="https://json-schema.org/understanding-json-schema/reference/non_json_data#contentencoding", fetch2_ok="Exclusive 8bit 415 leftover 7bit.")),
    (p(slug="oas-operation-externaldocs", domain="oas-op-extdocs-vs-op-no-docs", success=True, name="opexd", stack="OpenAPI 3.1 operation externalDocs + Go", field="externalDocs", old="op no docs leftover", new="operation externalDocs", fail_err="400: leftover op-no-docs after externalDocs-only", plan="operation.externalDocs-only 400s leftover no-docs. Dual-omit docs for one release.", residual="portal still no-docs leftover; drop after portal 5", vs="r3978 oas-externaldocs-description (op externalDocs vs no-docs leftover, not info docs)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch1_ok="operation.externalDocs points at per-op docs, leftover missing fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#external-documentation-object", fetch2_ok="Exclusive op externalDocs 400 leftover no-docs."),
     p(slug="leftover-op-no-docs", domain="op-no-docs-vs-oas-op-extdocs", success=False, name="opnod", stack="OpenAPI leftover op no docs + Java + TS", field="externalDocs", old="operation externalDocs", new="op no docs leftover only", fail_err="400: leftover externalDocs after no-docs-only", plan="No-docs-only 400s leftover operation.externalDocs. Freeze externalDocs, spec no-docs leftover.", residual="handoff: keep operation.externalDocs or force no-docs leftover", vs="r3978 leftover-url-only-docs (no-docs leftover, not url-only docs)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#external-documentation-object", fetch1_ok="Missing op docs are not externalDocs.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch2_ok="Exclusive no-docs 400 leftover externalDocs.")),
    (p(slug="oas-schema-default-null", domain="oas-default-null-vs-omit-null", success=True, name="defnull", stack="OpenAPI 3.1 default null + Go", field="default", old="omit null leftover", new="default null", fail_err="400: leftover omit-null after default-null-only", plan="default-null-only 400s leftover omit-null. Dual-omit null for one release.", residual="client still omit leftover; drop after client 6", vs="r3849 json-schema-default-applied (default null vs omit leftover, not applied default)", fetch1="https://json-schema.org/understanding-json-schema/reference/generic#default", fetch1_ok="default: null is a documented null, leftover omit-null fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive default null 400 leftover omit-null."),
     p(slug="leftover-omit-null-default", domain="omit-null-vs-oas-default-null", success=False, name="omitn", stack="OpenAPI leftover omit null default + Java + TS", field="default", old="default null", new="omit null leftover only", fail_err="400: leftover default-null after omit-only", plan="Omit-only 400s leftover default-null. Freeze default null, spec omit leftover.", residual="handoff: keep default null or force omit leftover", vs="r3849 omit-default (omit-null leftover, not omit-default mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Omitting null is not default:null.", fetch2="https://json-schema.org/understanding-json-schema/reference/generic#default", fetch2_ok="Exclusive omit-null 400 leftover default-null.")),
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
    print(json.dumps({"round": round_n, "idx": idx, "ids": [e1["id"], e2["id"]], "catalog": "r4007"}))


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
