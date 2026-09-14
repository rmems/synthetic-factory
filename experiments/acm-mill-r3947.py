#!/usr/bin/env python3
"""Sixth unique OpenAPI-drift ACM catalog after r3931 mill.

BAN r3866 proto-optional, r3850 accept-language/iso639, r3713 smile/cbor,
r3560 422/207, w131 cartesian, r3561–r3851 leftover leftover leftover,
and r3867/r3883/r3899/r3915/r3931 OAS plants.
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
    "acm-mill-r3915.py", "acm-mill-r3931.py",
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
    (p(slug="oas-format-email-ascii", domain="oas-email-vs-unvalidated", success=True, name="emasc", stack="OpenAPI 3.1 format=email + Go", field="format", old="unvalidated email leftover", new="format email", fail_err="400: leftover unvalidated email after format-email-only", plan="format=email-only 400s leftover unvalidated. Dual-accept unvalidated for one release.", residual="crm still unvalidated leftover; drop after crm 5", vs="r3883 oas-format-email-idn (ascii email vs unvalidated leftover, not idn-email)", fetch1="https://json-schema.org/understanding-json-schema/reference/string#email", fetch1_ok="format=email is RFC 5321, not leftover unvalidated strings.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="Exclusive format=email 400 leftover unvalidated."),
     p(slug="leftover-unvalidated-email", domain="unvalidated-vs-oas-email", success=False, name="emunv", stack="OpenAPI leftover unvalidated email + Java + TS", field="email", old="format email", new="unvalidated email leftover only", fail_err="400: leftover format=email after unvalidated-only", plan="Unvalidated-only 400s leftover format=email. Freeze email, spec unvalidated leftover.", residual="handoff: keep format=email or force unvalidated leftover", vs="r3883 leftover-ascii-email (unvalidated leftover, not ascii-email)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="Unvalidated strings are not format=email.", fetch2="https://json-schema.org/understanding-json-schema/reference/string#email", fetch2_ok="Exclusive unvalidated 400 leftover format=email.")),
    (p(slug="oas-format-uri-absolute", domain="oas-uri-vs-path-only-url", success=True, name="uriabs", stack="OpenAPI 3.1 format=uri + Go", field="format", old="path only leftover", new="format uri", fail_err="400: leftover path-only after format-uri-only", plan="format=uri-only 400s leftover path-only. Dual-read path-only for one release.", residual="sdk still path leftover; drop after sdk 6", vs="r3899 oas-format-iri (absolute uri vs path-only leftover, not iri)", fetch1="https://json-schema.org/understanding-json-schema/reference/string#resource-identifiers", fetch1_ok="format=uri is absolute, not leftover path-only.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="Exclusive format=uri 400 leftover path-only."),
     p(slug="leftover-path-only-url", domain="path-only-url-vs-oas-uri", success=False, name="pathu", stack="OpenAPI leftover path-only url + Java + TS", field="href", old="format uri", new="path only leftover only", fail_err="400: leftover format=uri after path-only", plan="Path-only 400s leftover format=uri. Freeze uri, spec path leftover.", residual="handoff: keep format=uri or force path leftover", vs="r3899 leftover-ascii-uri (path-only leftover, not ascii uri)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="Path-only hrefs are not format=uri.", fetch2="https://json-schema.org/understanding-json-schema/reference/string#resource-identifiers", fetch2_ok="Exclusive path-only 400 leftover format=uri.")),
    (p(slug="oas-minitems-array", domain="oas-minitems-vs-empty-array", success=True, name="minarr", stack="OpenAPI 3.1 minItems + Go", field="minItems", old="empty array leftover", new="array minItems", fail_err="400: leftover empty array after minItems-only", plan="minItems-only 400s leftover empty array. Dual-accept empty for one release.", residual="batch still empty leftover; drop after batch 4", vs="r3883 leftover-minitems-only (minItems vs empty leftover, not minContains contrast)", fetch1="https://json-schema.org/understanding-json-schema/reference/array#minitems", fetch1_ok="minItems rejects leftover empty arrays.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive minItems 400 leftover empty array."),
     p(slug="leftover-empty-array", domain="empty-array-vs-oas-minitems", success=False, name="emparr", stack="OpenAPI leftover empty array + Java + TS", field="items", old="array minItems", new="empty array leftover only", fail_err="400: leftover minItems after empty-only", plan="Empty-only 400s leftover minItems. Freeze minItems, spec empty leftover.", residual="handoff: keep minItems or force empty leftover", vs="r3883 oas-array-mincontains (empty leftover, not minContains)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Empty arrays are not minItems.", fetch2="https://json-schema.org/understanding-json-schema/reference/array#minitems", fetch2_ok="Exclusive empty array 400 leftover minItems.")),
    (p(slug="oas-maxcontains-array", domain="oas-maxcontains-vs-unbounded-contains", success=True, name="maxc", stack="OpenAPI 3.1 maxContains + Go", field="maxContains", old="unbounded contains leftover", new="array maxContains", fail_err="400: leftover unbounded contains after maxContains-only", plan="maxContains-only 400s leftover unbounded. Dual-accept unbounded for one release.", residual="validator still unbounded leftover; drop after validator 5", vs="r3883 oas-array-mincontains (maxContains vs unbounded leftover, not minContains)", fetch1="https://json-schema.org/understanding-json-schema/reference/array#maxcontains", fetch1_ok="maxContains caps contains matches.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive maxContains 400 leftover unbounded."),
     p(slug="leftover-unbounded-contains", domain="unbounded-contains-vs-oas-maxcontains", success=False, name="unbc", stack="OpenAPI leftover unbounded contains + Java + TS", field="contains", old="array maxContains", new="unbounded contains leftover only", fail_err="400: leftover maxContains after unbounded-only", plan="Unbounded-only 400s leftover maxContains. Freeze maxContains, spec unbounded leftover.", residual="handoff: keep maxContains or force unbounded leftover", vs="r3915 oas-contains-schema (unbounded leftover, not contains vs any-item)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Unbounded contains is not maxContains.", fetch2="https://json-schema.org/understanding-json-schema/reference/array#maxcontains", fetch2_ok="Exclusive unbounded contains 400 leftover maxContains.")),
    (p(slug="oas-dependent-schemas", domain="oas-dependentschemas-vs-flat-schema", success=True, name="depsch", stack="OpenAPI 3.1 dependentSchemas + Go", field="dependentSchemas", old="flat schema leftover", new="dependentSchemas", fail_err="400: leftover flat schema after dependentSchemas-only", plan="dependentSchemas-only 400s leftover flat. Dual-read flat for one release.", residual="form still flat leftover; drop after form 6", vs="wrap dependentrequired-billing (dependentSchemas vs flat leftover, not required)", fetch1="https://json-schema.org/understanding-json-schema/reference/conditionals#dependentschemas", fetch1_ok="dependentSchemas apply subschemas when a key is present.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive dependentSchemas 400 leftover flat."),
     p(slug="leftover-flat-schema", domain="flat-schema-vs-oas-dependentschemas", success=False, name="flatsch", stack="OpenAPI leftover flat schema + Java + TS", field="properties", old="dependentSchemas", new="flat schema leftover only", fail_err="400: leftover dependentSchemas after flat-only", plan="Flat-only 400s leftover dependentSchemas. Freeze dependentSchemas, spec flat leftover.", residual="handoff: keep dependentSchemas or force flat leftover", vs="wrap dependentrequired-billing (flat leftover, not required cartesian)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Flat schemas are not dependentSchemas.", fetch2="https://json-schema.org/understanding-json-schema/reference/conditionals#dependentschemas", fetch2_ok="Exclusive flat schema 400 leftover dependentSchemas.")),
    (p(slug="oas-oneof-union", domain="oas-oneof-vs-type-switch", success=True, name="oneofu", stack="OpenAPI 3.1 oneOf + Go", field="oneOf", old="type switch leftover", new="oneOf union", fail_err="400: leftover type switch after oneOf-only", plan="oneOf-only 400s leftover type switch. Dual-read switch for one release.", residual="sdk still switch leftover; drop after sdk 5", vs="r3915 oas-anyof-types (oneOf vs type-switch leftover, not anyOf)", fetch1="https://json-schema.org/understanding-json-schema/reference/combining#oneOf", fetch1_ok="oneOf requires exactly one match, not leftover type switches.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive oneOf 400 leftover type switch."),
     p(slug="leftover-type-switch", domain="type-switch-vs-oas-oneof", success=False, name="tswitch", stack="OpenAPI leftover type switch + Java + TS", field="type", old="oneOf union", new="type switch leftover only", fail_err="400: leftover oneOf after switch-only", plan="Switch-only 400s leftover oneOf. Freeze oneOf, spec switch leftover.", residual="handoff: keep oneOf or force type-switch leftover", vs="r3915 leftover-type-csv (type-switch leftover, not csv)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Type switches are not oneOf.", fetch2="https://json-schema.org/understanding-json-schema/reference/combining#oneOf", fetch2_ok="Exclusive type switch 400 leftover oneOf.")),
    (p(slug="oas-allof-merge", domain="oas-allof-vs-flat-merge", success=True, name="allofm", stack="OpenAPI 3.1 allOf + Go", field="allOf", old="flat merge leftover", new="allOf merge", fail_err="400: leftover flat merge after allOf-only", plan="allOf-only 400s leftover flat merge. Dual-read flat for one release.", residual="codegen still flat leftover; drop after codegen 6", vs="r3915 oas-anyof-types (allOf vs flat merge leftover, not anyOf)", fetch1="https://json-schema.org/understanding-json-schema/reference/combining#allOf", fetch1_ok="allOf composes subschemas, not leftover flattened properties.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive allOf 400 leftover flat merge."),
     p(slug="leftover-flat-merge", domain="flat-merge-vs-oas-allof", success=False, name="fmerge", stack="OpenAPI leftover flat merge + Java + TS", field="properties", old="allOf merge", new="flat merge leftover only", fail_err="400: leftover allOf after flat-only", plan="Flat-only 400s leftover allOf. Freeze allOf, spec flat leftover.", residual="handoff: keep allOf or force flat leftover", vs="r3947 leftover-flat-schema contrast (flat merge leftover, not dependentSchemas)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Flat merges are not allOf.", fetch2="https://json-schema.org/understanding-json-schema/reference/combining#allOf", fetch2_ok="Exclusive flat merge 400 leftover allOf.")),
    (p(slug="oas-example-external-value", domain="oas-externalvalue-vs-inline-example", success=True, name="exval", stack="OpenAPI 3.1 example.externalValue + Go", field="externalValue", old="inline example leftover", new="example externalValue", fail_err="400: leftover inline example after externalValue-only", plan="externalValue-only 400s leftover inline example. Dual-read inline for one release.", residual="docs still inline leftover; drop after docs 5", vs="r3830 oas-example-singular (externalValue vs inline leftover, not singular example)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#example-object", fetch1_ok="externalValue is mutually exclusive with value.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch2_ok="Exclusive externalValue 400 leftover inline example."),
     p(slug="leftover-inline-example", domain="inline-example-vs-oas-externalvalue", success=False, name="inex", stack="OpenAPI leftover inline example + Java + TS", field="value", old="example externalValue", new="inline example leftover only", fail_err="400: leftover externalValue after inline-only", plan="Inline-only 400s leftover externalValue. Freeze externalValue, spec inline leftover.", residual="handoff: keep externalValue or force inline leftover", vs="r3830 examples-map-leftover (inline leftover, not examples map)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch1_ok="Inline example value is not externalValue.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#example-object", fetch2_ok="Exclusive inline example 400 leftover externalValue.")),
    (p(slug="oas-security-apikey-header", domain="oas-apikey-header-vs-query-key", success=True, name="apikeyh", stack="OpenAPI 3.1 apiKey header + Go", field="in", old="query apikey leftover", new="apiKey header", fail_err="401: leftover query apikey after header-only", plan="apiKey-header-only 401s leftover query key. Dual-accept query for one release.", residual="edge still query leftover; drop after edge 6", vs="r3899 leftover-client-cert-header (apiKey header vs query leftover, not mTLS)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch1_ok="apiKey in=header is not leftover query keys.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#fixed-fields-21", fetch2_ok="Exclusive apiKey header 401 leftover query."),
     p(slug="leftover-query-apikey", domain="query-apikey-vs-oas-apikey-header", success=False, name="apikeyq", stack="OpenAPI leftover query apikey + Java + TS", field="in", old="apiKey header", new="query apikey leftover only", fail_err="401: leftover apiKey header after query-only", plan="Query-only 401s leftover apiKey header. Freeze header, spec query leftover.", residual="handoff: keep apiKey header or force query leftover", vs="r3867 leftover-query-pctencode (query apikey leftover, not percent-encode)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#fixed-fields-21", fetch1_ok="Query apiKeys are not in=header.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch2_ok="Exclusive query apikey 401 leftover header.")),
    (p(slug="oas-security-http-bearer", domain="oas-bearer-vs-http-basic", success=True, name="bearer", stack="OpenAPI 3.1 HTTP bearer + Go", field="scheme", old="http basic leftover", new="http bearer", fail_err="401: leftover http basic after bearer-only", plan="Bearer-only 401s leftover basic. Dual-accept basic for one release.", residual="legacy still basic leftover; drop after legacy 7", vs="r3867 leftover-oauth-implicit-flow (bearer vs basic leftover, not implicit)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch1_ok="HTTP bearer is not leftover HTTP basic.", fetch2="https://datatracker.ietf.org/doc/html/rfc6750", fetch2_ok="Exclusive bearer 401 leftover basic."),
     p(slug="leftover-http-basic", domain="http-basic-vs-oas-bearer", success=False, name="basic", stack="OpenAPI leftover HTTP basic + Java + TS", field="scheme", old="http bearer", new="http basic leftover only", fail_err="401: leftover bearer after basic-only", plan="Basic-only 401s leftover bearer. Freeze bearer, spec basic leftover.", residual="handoff: keep bearer or force basic leftover", vs="r3867 oas-oidc-scheme (basic leftover, not OIDC)", fetch1="https://datatracker.ietf.org/doc/html/rfc7617", fetch1_ok="HTTP basic is not bearer.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch2_ok="Exclusive basic 401 leftover bearer.")),
    (p(slug="oas-format-int32", domain="oas-int32-vs-unbounded-int", success=True, name="fmt32", stack="OpenAPI 3.1 format=int32 + Go", field="format", old="unbounded int leftover", new="format int32", fail_err="400: leftover unbounded int after int32-only", plan="format=int32-only 400s leftover unbounded int. Dual-read unbounded for one release.", residual="js still unbounded leftover; drop after js 5", vs="wrap int32-sku-qty (int32 vs unbounded leftover, not sku qty)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="format=int32 is 32-bit, not leftover unbounded integers.", fetch2="https://json-schema.org/understanding-json-schema/reference/numeric", fetch2_ok="Exclusive int32 400 leftover unbounded int."),
     p(slug="leftover-unbounded-int", domain="unbounded-int-vs-oas-int32", success=False, name="unbint", stack="OpenAPI leftover unbounded int + Java + TS", field="type", old="format int32", new="unbounded int leftover only", fail_err="400: leftover int32 after unbounded-only", plan="Unbounded-only 400s leftover int32. Freeze int32, spec unbounded leftover.", residual="handoff: keep int32 or force unbounded leftover", vs="wrap int32-sku-qty (unbounded leftover, not sku cartesian)", fetch1="https://json-schema.org/understanding-json-schema/reference/numeric", fetch1_ok="Unbounded integers are not format=int32.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="Exclusive unbounded int 400 leftover int32.")),
    (p(slug="oas-xml-attribute", domain="oas-xml-attribute-vs-element", success=True, name="xmlattr", stack="OpenAPI 3.1 xml.attribute + Go", field="attribute", old="xml element leftover", new="xml attribute", fail_err="415: leftover xml element after attribute-only", plan="xml.attribute-only 415s leftover element. Dual-read element for one release.", residual="batch still element leftover; drop after batch 5", vs="wrap xml-wrapped-array (xml.attribute vs element leftover, not wrapped array)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#xml-object", fetch1_ok="xml.attribute true serializes as an attribute, not an element.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive xml.attribute 415 leftover element."),
     p(slug="leftover-xml-element", domain="xml-element-vs-oas-xml-attribute", success=False, name="xmlel", stack="OpenAPI leftover xml element + Java + TS", field="name", old="xml attribute", new="xml element leftover only", fail_err="415: leftover xml.attribute after element-only", plan="Element-only 415s leftover xml.attribute. Freeze attribute, spec element leftover.", residual="handoff: keep xml.attribute or force element leftover", vs="wrap xml-wrapped-array (element leftover, not wrapped cartesian)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="XML elements are not xml.attribute.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#xml-object", fetch2_ok="Exclusive xml element 415 leftover attribute.")),
    (p(slug="oas-callback-pathitem", domain="oas-callback-pathitem-vs-notify-post", success=True, name="cbpath", stack="OpenAPI 3.1 callback Path Item + Go", field="post", old="notify post leftover", new="callback Path Item", fail_err="400: leftover notify post after callback-pathitem-only", plan="Callback-Path-Item-only 400s leftover notify post. Dual-bind notify for one release.", residual="bus still notify leftover; drop after bus 6", vs="r3883 oas-op-callback-expr (callback Path Item vs notify leftover, not runtime expr)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#callback-object", fetch1_ok="Callback values are Path Item objects, not leftover notify posts.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#path-item-object", fetch2_ok="Exclusive callback Path Item 400 leftover notify."),
     p(slug="leftover-notify-post", domain="notify-post-vs-oas-callback-pathitem", success=False, name="ntfpost", stack="OpenAPI leftover notify post + Java + TS", field="notify", old="callback Path Item", new="notify post leftover only", fail_err="400: leftover callback Path Item after notify-only", plan="Notify-only 400s leftover callback Path Item. Freeze Path Item, spec notify leftover.", residual="handoff: keep callback Path Item or force notify leftover", vs="r3883 leftover-static-notify-url (notify post leftover, not static URL)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#path-item-object", fetch1_ok="Notify posts are not callback Path Items.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#callback-object", fetch2_ok="Exclusive notify post 400 leftover callback Path Item.")),
    (p(slug="oas-servers-description", domain="oas-server-desc-vs-undocumented", success=True, name="srvdesc", stack="OpenAPI 3.1 server description + Go", field="description", old="undocumented server leftover", new="server description", fail_err="400: leftover undocumented after description-only", plan="Server-description-only 400s leftover undocumented. Dual-omit description for one release.", residual="portal still undocumented leftover; drop after portal 4", vs="r3931 oas-servers-multiple (server description vs undocumented leftover, not multi-server)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#server-object", fetch1_ok="Server description documents the URL, leftover undocumented hosts fail closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#oasServers", fetch2_ok="Exclusive server description 400 leftover undocumented."),
     p(slug="leftover-undocumented-server", domain="undocumented-vs-oas-server-desc", success=False, name="srvund", stack="OpenAPI leftover undocumented server + Java + TS", field="url", old="server description", new="undocumented server leftover only", fail_err="400: leftover description after undocumented-only", plan="Undocumented-only 400s leftover server description. Freeze description, spec undocumented leftover.", residual="handoff: keep server description or force undocumented leftover", vs="r3931 leftover-single-server (undocumented leftover, not single server)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#oasServers", fetch1_ok="Undocumented servers are not described.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#server-object", fetch2_ok="Exclusive undocumented 400 leftover description.")),
    (p(slug="oas-operation-summary-req", domain="oas-summary-vs-missing-summary", success=True, name="opsum", stack="OpenAPI 3.1 operation summary + Go", field="summary", old="missing summary leftover", new="operation summary", fail_err="400: leftover missing summary after summary-only", plan="Summary-only 400s leftover missing summary. Dual-omit summary for one release.", residual="portal still missing leftover; drop after portal 5", vs="r3931 oas-operation-deprecated (summary vs missing leftover, not deprecated)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch1_ok="summary is a short string; leftover missing summaries fail closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#fixed-fields-8", fetch2_ok="Exclusive summary 400 leftover missing."),
     p(slug="leftover-missing-summary", domain="missing-summary-vs-oas-summary", success=False, name="nosum", stack="OpenAPI leftover missing summary + Java + TS", field="operationId", old="operation summary", new="missing summary leftover only", fail_err="400: leftover summary after missing-only", plan="Missing-only 400s leftover summary. Freeze summary, spec missing leftover.", residual="handoff: keep summary or force missing leftover", vs="r3931 leftover-live-op (missing summary leftover, not live op)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#fixed-fields-8", fetch1_ok="Missing summaries are not operation.summary.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch2_ok="Exclusive missing summary 400 leftover summary.")),
    (p(slug="oas-format-hostname-idn", domain="oas-idn-hostname-vs-punycode-only", success=True, name="idnhn", stack="OpenAPI 3.1 format=idn-hostname + Go", field="format", old="punycode only leftover", new="idn-hostname format", fail_err="400: leftover punycode after idn-hostname-only", plan="idn-hostname-only 400s leftover punycode. Dual-accept punycode for one release.", residual="dns still punycode leftover; drop after dns 6", vs="r3847 format-hostname-ascii (idn-hostname vs punycode leftover, not ascii hostname)", fetch1="https://json-schema.org/understanding-json-schema/reference/string#idn-hostname", fetch1_ok="format=idn-hostname is not leftover punycode-only.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="Exclusive idn-hostname 400 leftover punycode."),
     p(slug="leftover-punycode-only", domain="punycode-only-vs-oas-idn-hostname", success=False, name="puny", stack="OpenAPI leftover punycode + Java + TS", field="format", old="idn-hostname format", new="punycode only leftover only", fail_err="400: leftover idn-hostname after punycode-only", plan="Punycode-only 400s leftover idn-hostname. Freeze idn-hostname, spec punycode leftover.", residual="handoff: keep idn-hostname or force punycode leftover", vs="r3847 idn-hostname-leftover (punycode leftover, not idn leftover plant)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="Punycode-only is not format=idn-hostname.", fetch2="https://json-schema.org/understanding-json-schema/reference/string#idn-hostname", fetch2_ok="Exclusive punycode 400 leftover idn-hostname.")),
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
    print(json.dumps({"round": round_n, "idx": idx, "ids": [e1["id"], e2["id"]], "catalog": "r3947"}))


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
