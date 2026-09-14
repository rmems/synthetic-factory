#!/usr/bin/env python3
"""Ninth unique OpenAPI-drift ACM catalog after r4118 mill. Fast slug load."""
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
    (p(slug="oas-schema-additional-properties-false", domain="oas-closed-object-vs-open-keys", success=True, name="addpf", stack="OpenAPI 3.1 additionalProperties false + Go", field="additionalProperties", old="open object keys leftover", new="additionalProperties false", fail_err="400: leftover open keys after closed-only", plan="additionalProperties-false-only 400s leftover open keys. Dual-read open for one release.", residual="validator still open leftover; drop after validator 5", vs="r4086 leftover-open-additional (closed object vs open leftover, not unevaluatedProperties)", fetch1="https://json-schema.org/understanding-json-schema/reference/object#additionalproperties", fetch1_ok="additionalProperties false rejects leftover unknown keys.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive closed object 400 leftover open keys."),
     p(slug="leftover-open-object-keys", domain="open-keys-vs-oas-closed-object", success=False, name="openk", stack="OpenAPI leftover open object keys + Java + TS", field="additionalProperties", old="additionalProperties false", new="open object keys leftover only", fail_err="400: leftover additionalProperties false after open-only", plan="Open-only 400s leftover additionalProperties false. Freeze closed, spec open leftover.", residual="handoff: keep closed object or force open leftover", vs="r4086 oas-schema-unevaluated-properties-false (open leftover, not unevaluated mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Open leftover keys are not additionalProperties false.", fetch2="https://json-schema.org/understanding-json-schema/reference/object#additionalproperties", fetch2_ok="Exclusive open keys 400 leftover closed.")),
    (p(slug="oas-content-ndjson", domain="oas-ndjson-vs-json-array", success=True, name="ndjson", stack="OpenAPI 3.1 application/x-ndjson + Go", field="content", old="json array leftover", new="ndjson stream", fail_err="415: leftover json array after ndjson-only", plan="ndjson-only 415s leftover json array. Dual-read array for one release.", residual="ingest still array leftover; drop after ingest 6", vs="r4102 leftover-json-only-body (ndjson vs array leftover, not yaml mill)", fetch1="https://github.com/ndjson/ndjson-spec", fetch1_ok="NDJSON is line-delimited objects, leftover JSON arrays are not that.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch2_ok="Exclusive ndjson 415 leftover json array."),
     p(slug="leftover-json-array-stream", domain="json-array-vs-oas-ndjson", success=False, name="jarrst", stack="OpenAPI leftover json array stream + Java + TS", field="content", old="ndjson stream", new="json array leftover only", fail_err="415: leftover ndjson after array-only", plan="Array-only 415s leftover ndjson. Freeze ndjson, spec array leftover.", residual="handoff: keep ndjson or force array leftover", vs="r4102 oas-content-application-yaml (array leftover, not yaml mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch1_ok="JSON array leftover is not NDJSON.", fetch2="https://github.com/ndjson/ndjson-spec", fetch2_ok="Exclusive json array 415 leftover ndjson.")),
    (p(slug="oas-header-required-false", domain="oas-optional-hdr-vs-always-req", success=True, name="hdropt", stack="OpenAPI 3.1 header required false + Go", field="required", old="always required header leftover", new="header required false", fail_err="400: leftover always-required after optional-only", plan="optional-header-only 400s leftover always-required. Dual-require for one release.", residual="proxy still required leftover; drop after proxy 5", vs="r4102 leftover-undocumented-header (optional vs always leftover, not description mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch1_ok="required false is the header default, leftover always-required is not that.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="Exclusive optional header 400 leftover always-required."),
     p(slug="leftover-always-required-hdr", domain="always-req-vs-oas-optional-hdr", success=False, name="hdralw", stack="OpenAPI leftover always required header + Java + TS", field="required", old="header required false", new="always required header leftover only", fail_err="400: leftover optional header after always-only", plan="Always-only 400s leftover optional header. Freeze optional, spec always leftover.", residual="handoff: keep optional header or force always leftover", vs="r4102 oas-header-description-req (always leftover, not description mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="Always-required leftover headers are not required false.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch2_ok="Exclusive always-required 400 leftover optional.")),
    (p(slug="oas-path-item-servers", domain="oas-path-servers-vs-op-only", success=True, name="pisrv", stack="OpenAPI 3.1 Path Item servers + Go", field="servers", old="op server only leftover", new="path item servers", fail_err="400: leftover op-server after path-servers-only", plan="Path-Item-servers-only 400s leftover op-only. Dual-read op for one release.", residual="sdk still op leftover; drop after sdk 5", vs="r4118 leftover-root-webhook-server (path servers vs op leftover, not webhook mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#path-item-object", fetch1_ok="Path Item servers override root, leftover op-only is not that.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#server-object", fetch2_ok="Exclusive path servers 400 leftover op-only."),
     p(slug="leftover-op-server-only", domain="op-server-vs-oas-path-servers", success=False, name="opsrv", stack="OpenAPI leftover op server only + Java + TS", field="servers", old="path item servers", new="op server only leftover only", fail_err="400: leftover path servers after op-only", plan="Op-only 400s leftover path servers. Freeze path, spec op leftover.", residual="handoff: keep path servers or force op leftover", vs="r4118 oas-webhook-servers-override (op leftover, not webhook mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#server-object", fetch1_ok="Op-only leftover servers are not Path Item servers.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#path-item-object", fetch2_ok="Exclusive op-server 400 leftover path.")),
    (p(slug="oas-schema-enum-closed", domain="oas-closed-enum-vs-open-str", success=True, name="enumc", stack="OpenAPI 3.1 closed enum + Go", field="enum", old="open string leftover", new="closed enum", fail_err="400: leftover open string after enum-only", plan="closed-enum-only 400s leftover open string. Dual-read open for one release.", residual="sdk still open leftover; drop after sdk 5", vs="r4118 leftover-any-number-scale (closed enum vs open leftover, not multipleOf)", fetch1="https://json-schema.org/understanding-json-schema/reference/generic#enumerated-values", fetch1_ok="enum is a closed set, leftover open strings fail closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive closed enum 400 leftover open string."),
     p(slug="leftover-open-string-enum", domain="open-str-vs-oas-closed-enum", success=False, name="openen", stack="OpenAPI leftover open string enum + Java + TS", field="type", old="closed enum", new="open string leftover only", fail_err="400: leftover closed enum after open-only", plan="Open-only 400s leftover closed enum. Freeze enum, spec open leftover.", residual="handoff: keep closed enum or force open leftover", vs="r4118 oas-schema-multipleof-int (open leftover, not multipleOf)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Open leftover strings are not enum.", fetch2="https://json-schema.org/understanding-json-schema/reference/generic#enumerated-values", fetch2_ok="Exclusive open string 400 leftover enum.")),
    (p(slug="oas-format-byte-strict", domain="oas-byte-vs-plain-b64", success=True, name="fmtb", stack="OpenAPI 3.1 format=byte + Go", field="format", old="plain b64 leftover", new="format byte", fail_err="400: leftover plain b64 after byte-only", plan="format=byte-only 400s leftover plain b64. Dual-read plain for one release.", residual="store still plain leftover; drop after store 6", vs="r3963 leftover-plain-string (byte vs plain leftover, not password mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="format=byte is base64, leftover untyped strings fail closed.", fetch2="https://json-schema.org/understanding-json-schema/reference/non_json_data", fetch2_ok="Exclusive format=byte 400 leftover plain."),
     p(slug="leftover-plain-b64-field", domain="plain-b64-vs-oas-byte", success=False, name="plb64", stack="OpenAPI leftover plain b64 + Java + TS", field="type", old="format byte", new="plain b64 leftover only", fail_err="400: leftover format=byte after plain-only", plan="Plain-only 400s leftover format=byte. Freeze byte, spec plain leftover.", residual="handoff: keep format=byte or force plain leftover", vs="r3963 oas-format-password (plain leftover, not password mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/non_json_data", fetch1_ok="Plain leftover strings are not format=byte.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="Exclusive plain b64 400 leftover byte.")),
    (p(slug="oas-security-api-key-query-name", domain="oas-apikey-name-vs-x-api-key", success=True, name="apiname", stack="OpenAPI 3.1 apiKey query name + Go", field="name", old="x-api-key header leftover", new="apiKey query name", fail_err="401: leftover x-api-key after named-query-only", plan="named-query-apikey-only 401s leftover x-api-key. Dual-accept header for one release.", residual="edge still header leftover; drop after edge 6", vs="r4023 leftover-apikey-querystring (named query vs x-api-key leftover, not cookie mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch1_ok="apiKey name in query is not leftover X-Api-Key headers.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#fixed-fields-21", fetch2_ok="Exclusive named query apikey 401 leftover x-api-key."),
     p(slug="leftover-x-api-key-header", domain="x-api-key-vs-oas-apikey-name", success=False, name="xapik", stack="OpenAPI leftover x-api-key header + Java + TS", field="in", old="apiKey query name", new="x-api-key header leftover only", fail_err="401: leftover named query after x-api-key-only", plan="X-api-key-only 401s leftover named query. Freeze query name, spec header leftover.", residual="handoff: keep named query apikey or force x-api-key leftover", vs="r4023 oas-security-apikey-cookie (x-api-key leftover, not cookie mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#fixed-fields-21", fetch1_ok="X-Api-Key leftover is not named query apiKey.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch2_ok="Exclusive x-api-key 401 leftover named query.")),
    (p(slug="oas-operation-externaldocs-url", domain="oas-op-docs-url-vs-wiki", success=True, name="opexurl", stack="OpenAPI 3.1 operation externalDocs.url + Go", field="url", old="wiki only leftover", new="operation externalDocs url", fail_err="400: leftover wiki-only after url-only", plan="externalDocs.url-only 400s leftover wiki. Dual-omit url for one release.", residual="portal still wiki leftover; drop after portal 5", vs="r4007 leftover-op-no-docs (docs url vs wiki leftover, not missing docs mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#external-documentation-object", fetch1_ok="externalDocs.url is required, leftover wiki-only fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch2_ok="Exclusive op docs url 400 leftover wiki."),
     p(slug="leftover-wiki-only-docs", domain="wiki-only-vs-oas-op-docs-url", success=False, name="wikid", stack="OpenAPI leftover wiki-only docs + Java + TS", field="description", old="operation externalDocs url", new="wiki only leftover only", fail_err="400: leftover externalDocs.url after wiki-only", plan="Wiki-only 400s leftover externalDocs.url. Freeze url, spec wiki leftover.", residual="handoff: keep op docs url or force wiki leftover", vs="r4007 oas-operation-externaldocs (wiki leftover, not missing docs mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch1_ok="Wiki leftover docs are not externalDocs.url.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#external-documentation-object", fetch2_ok="Exclusive wiki-only 400 leftover url.")),
    (p(slug="oas-tag-description-req", domain="oas-tag-desc-vs-name-only", success=True, name="tagdesc", stack="OpenAPI 3.1 tag description + Go", field="description", old="name only tag leftover", new="tag description", fail_err="400: leftover name-only tag after description-only", plan="tag.description-only 400s leftover name-only. Dual-omit description for one release.", residual="portal still name-only leftover; drop after portal 4", vs="r4054 leftover-anonymous-tag (tag desc vs name-only leftover, not anonymous mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#tag-object", fetch1_ok="tag.description documents the tag, leftover name-only fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#fixed-fields-18", fetch2_ok="Exclusive tag description 400 leftover name-only."),
     p(slug="leftover-name-only-tag", domain="name-only-tag-vs-oas-tag-desc", success=False, name="tagno", stack="OpenAPI leftover name-only tag + Java + TS", field="name", old="tag description", new="name only tag leftover only", fail_err="400: leftover tag description after name-only", plan="Name-only 400s leftover tag description. Freeze description, spec name leftover.", residual="handoff: keep tag description or force name leftover", vs="r4054 oas-tag-name-required (name-only leftover, not required name mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#fixed-fields-18", fetch1_ok="Name-only leftover tags are not described.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#tag-object", fetch2_ok="Exclusive name-only tag 400 leftover description.")),
    (p(slug="oas-schema-format-int64", domain="oas-int64-vs-js-unsafe", success=True, name="fmt64", stack="OpenAPI 3.1 format=int64 + Go", field="format", old="js unsafe int leftover", new="format int64", fail_err="400: leftover js-unsafe after int64-only", plan="format=int64-only 400s leftover js-unsafe. Dual-read unsafe for one release.", residual="js still unsafe leftover; drop after js 6", vs="r3947 leftover-unbounded-int (int64 vs js-unsafe leftover, not int32 mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="format=int64 is 64-bit, leftover JS-unsafe numbers fail closed.", fetch2="https://json-schema.org/understanding-json-schema/reference/numeric", fetch2_ok="Exclusive int64 400 leftover js-unsafe."),
     p(slug="leftover-js-unsafe-int", domain="js-unsafe-vs-oas-int64", success=False, name="jsint", stack="OpenAPI leftover js unsafe int + Java + TS", field="type", old="format int64", new="js unsafe int leftover only", fail_err="400: leftover int64 after js-unsafe-only", plan="Js-unsafe-only 400s leftover int64. Freeze int64, spec unsafe leftover.", residual="handoff: keep int64 or force js-unsafe leftover", vs="r3947 oas-format-int32 (js-unsafe leftover, not int32 mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/numeric", fetch1_ok="JS-unsafe leftover ints are not format=int64.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="Exclusive js-unsafe 400 leftover int64.")),
    (p(slug="oas-callback-timeout-header", domain="oas-cb-timeout-vs-none", success=True, name="cbtout", stack="OpenAPI 3.1 callback timeout header + Go", field="X-Timeout-Ms", old="no timeout leftover", new="callback timeout header", fail_err="400: leftover no-timeout after timeout-only", plan="callback-timeout-only 400s leftover none. Dual-omit timeout for one release.", residual="bus still none leftover; drop after bus 6", vs="r4070 leftover-static-callback-url (timeout vs none leftover, not static mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#callback-object", fetch1_ok="Callback timeout headers are not leftover unbounded waits.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch2_ok="Exclusive callback timeout 400 leftover none."),
     p(slug="leftover-no-timeout-cb", domain="no-timeout-vs-oas-cb-timeout", success=False, name="notout", stack="OpenAPI leftover no timeout callback + Java + TS", field="timeout", old="callback timeout header", new="no timeout leftover only", fail_err="400: leftover timeout header after none-only", plan="None-only 400s leftover timeout header. Freeze timeout, spec none leftover.", residual="handoff: keep callback timeout or force none leftover", vs="r4070 oas-callback-expression-runtime (no-timeout leftover, not runtime mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch1_ok="Missing leftover timeouts are not X-Timeout-Ms.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#callback-object", fetch2_ok="Exclusive no-timeout 400 leftover header.")),
    (p(slug="oas-xml-namespace-uri", domain="oas-xmlns-uri-vs-relative", success=True, name="xmlnsu", stack="OpenAPI 3.1 xml.namespace absolute URI + Go", field="namespace", old="relative xmlns leftover", new="xml namespace uri", fail_err="415: leftover relative xmlns after uri-only", plan="xml.namespace-uri-only 415s leftover relative. Dual-read relative for one release.", residual="batch still relative leftover; drop after batch 5", vs="r4086 leftover-no-xmlns (absolute URI vs relative leftover, not missing xmlns)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#xml-object", fetch1_ok="xml.namespace MUST be an absolute URI, leftover relative fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive xmlns URI 415 leftover relative."),
     p(slug="leftover-relative-xmlns", domain="relative-xmlns-vs-oas-xmlns-uri", success=False, name="relns", stack="OpenAPI leftover relative xmlns + Java + TS", field="namespace", old="xml namespace uri", new="relative xmlns leftover only", fail_err="415: leftover absolute xmlns after relative-only", plan="Relative-only 415s leftover absolute xmlns. Freeze URI, spec relative leftover.", residual="handoff: keep xmlns URI or force relative leftover", vs="r4086 oas-xml-xmlns-required (relative leftover, not required mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Relative leftover xmlns is not an absolute URI.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#xml-object", fetch2_ok="Exclusive relative xmlns 415 leftover URI.")),
    (p(slug="oas-parameter-style-deep-object", domain="oas-deepobject-vs-flat-query", success=True, name="deepo", stack="OpenAPI 3.1 query style=deepObject + Go", field="style", old="flat query obj leftover", new="query deepObject", fail_err="400: leftover flat query after deepObject-only", plan="deepObject-only 400s leftover flat. Dual-read flat for one release.", residual="gateway still flat leftover; drop after gateway 5", vs="wrap deepobject-filter (deepObject vs flat leftover, not filter cartesian)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch1_ok="style=deepObject is not leftover flattened query keys.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="Exclusive deepObject 400 leftover flat."),
     p(slug="leftover-flat-query-obj", domain="flat-query-vs-oas-deepobject", success=False, name="flatq", stack="OpenAPI leftover flat query obj + Java + TS", field="style", old="query deepObject", new="flat query obj leftover only", fail_err="400: leftover deepObject after flat-only", plan="Flat-only 400s leftover deepObject. Freeze deepObject, spec flat leftover.", residual="handoff: keep deepObject or force flat leftover", vs="wrap deepobject-filter (flat leftover, not filter cartesian)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="Flat leftover query objects are not deepObject.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch2_ok="Exclusive flat query 400 leftover deepObject.")),
    (p(slug="oas-info-license-identifier-spdx", domain="oas-spdx-id-vs-url-only-lic", success=True, name="spdxid", stack="OpenAPI 3.1 license.identifier + Go", field="identifier", old="url only license leftover", new="license identifier", fail_err="400: leftover url-only license after identifier-only", plan="license.identifier-only 400s leftover url-only. Dual-read url for one release.", residual="portal still url leftover; drop after portal 5", vs="r4086 leftover-spdx-only (identifier vs url leftover, not spdx-only mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#license-object", fetch1_ok="identifier is SPDX, leftover url-only is mutually exclusive in some tooling.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#info-object", fetch2_ok="Exclusive license identifier 400 leftover url-only."),
     p(slug="leftover-url-only-license", domain="url-only-lic-vs-oas-spdx-id", success=False, name="urlic", stack="OpenAPI leftover url-only license + Java + TS", field="url", old="license identifier", new="url only license leftover only", fail_err="400: leftover identifier after url-only", plan="Url-only 400s leftover identifier. Freeze identifier, spec url leftover.", residual="handoff: keep license identifier or force url leftover", vs="r4086 oas-info-license-url (url-only leftover, not license url mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#info-object", fetch1_ok="URL-only leftover licenses are not identifier.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#license-object", fetch2_ok="Exclusive url-only license 400 leftover identifier.")),
    (p(slug="oas-schema-unique-items", domain="oas-uniqueitems-vs-dup-array", success=True, name="uniqit", stack="OpenAPI 3.1 uniqueItems + Go", field="uniqueItems", old="dup array leftover", new="array uniqueItems", fail_err="400: leftover dup array after uniqueItems-only", plan="uniqueItems-only 400s leftover dups. Dual-accept dups for one release.", residual="batch still dups leftover; drop after batch 5", vs="wrap uniqueitems-sku (uniqueItems vs dups leftover, not sku cartesian)", fetch1="https://json-schema.org/understanding-json-schema/reference/array#uniqueitems", fetch1_ok="uniqueItems rejects leftover duplicate array values.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive uniqueItems 400 leftover dups."),
     p(slug="leftover-dup-array-items", domain="dup-array-vs-oas-uniqueitems", success=False, name="dupit", stack="OpenAPI leftover dup array + Java + TS", field="items", old="array uniqueItems", new="dup array leftover only", fail_err="400: leftover uniqueItems after dups-only", plan="Dups-only 400s leftover uniqueItems. Freeze uniqueItems, spec dups leftover.", residual="handoff: keep uniqueItems or force dups leftover", vs="wrap uniqueitems-sku (dups leftover, not sku cartesian)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Duplicate leftover arrays are not uniqueItems.", fetch2="https://json-schema.org/understanding-json-schema/reference/array#uniqueitems", fetch2_ok="Exclusive dup array 400 leftover uniqueItems.")),
    (p(slug="oas-servers-variables-default-required", domain="oas-srv-default-vs-missing-default", success=True, name="srvdef", stack="OpenAPI 3.1 server variable default + Go", field="default", old="missing server default leftover", new="server variable default", fail_err="400: leftover missing default after default-only", plan="server-default-only 400s leftover missing. Dual-omit default for one release.", residual="mesh still missing leftover; drop after mesh 5", vs="r3899 leftover-missing-srv-default (required default vs missing leftover, not mill reuse slug)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#server-variable-object", fetch1_ok="default is required on Server Variable Object, leftover missing fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#server-object", fetch2_ok="Exclusive server default 400 leftover missing."),
     p(slug="leftover-missing-server-var-default", domain="missing-default-vs-oas-srv-default", success=False, name="nosdef", stack="OpenAPI leftover missing server default + Java + TS", field="default", old="server variable default", new="missing server default leftover only", fail_err="400: leftover server default after missing-only", plan="Missing-only 400s leftover server default. Freeze default, spec missing leftover.", residual="handoff: keep server default or force missing leftover", vs="r4007 leftover-default-outside-enum (missing leftover, not outside-enum mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#server-object", fetch1_ok="Missing leftover defaults are not Server Variable default.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#server-variable-object", fetch2_ok="Exclusive missing default 400 leftover default.")),
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
    print(json.dumps({"round": round_n, "idx": idx, "ids": [e1["id"], e2["id"]], "catalog": "r4134"}))


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
