#!/usr/bin/env python3
"""Unique OpenAPI-drift ACM catalog r4230. Fast slug load."""
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
    (p(slug="oas-root-jsonschemadialect-uri", domain="oas-root-jsonschemadialect-uri-vs-leftover-implicit-draft2020", success=True, name="6abcda", stack="OpenAPI 3.1 jsonSchemaDialect + Go", field="jsonSchemaDialect", old="implicit draft leftover", new="root jsonSchemaDialect", fail_err="400: leftover implicit draft leftover after root jsonSchemaDialect-only", plan="root jsonSchemaDialect-only 400s leftover implicit draft leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (root jsonSchemaDialect vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#openapi-object", fetch1_ok="jsonSchemaDialect sets the default dialect, leftover implicit fails closed.", fetch2="https://json-schema.org/understanding-json-schema/reference/schema", fetch2_ok="Exclusive dialect 400 leftover implicit."),
     p(slug="leftover-implicit-draft2020", domain="leftover-implicit-draft2020-vs-oas-root-jsonschemadialect-uri", success=False, name="e5c7a6", stack="OpenAPI leftover jsonSchemaDialect + Java + TS", field="jsonSchemaDialect", old="root jsonSchemaDialect", new="implicit draft leftover only", fail_err="400: leftover root jsonSchemaDialect after implicit draft leftover-only", plan="implicit draft leftover-only 400s leftover root jsonSchemaDialect. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (implicit draft leftover leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/schema", fetch1_ok="Exclusive dialect 400 leftover implicit.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#openapi-object", fetch2_ok="jsonSchemaDialect sets the default dialect, leftover implicit fails closed.")),
    (p(slug="oas-schema-prefixitems-tuple", domain="oas-schema-prefixitems-tuple-vs-leftover-items-array-tuple", success=True, name="fa0e67", stack="OpenAPI 3.1 prefixItems + Go", field="prefixItems", old="items tuple leftover", new="prefixItems tuple", fail_err="400: leftover items tuple leftover after prefixItems tuple-only", plan="prefixItems tuple-only 400s leftover items tuple leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (prefixItems tuple vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/array#tuple-validation", fetch1_ok="prefixItems is positional tuple validation, leftover items-as-tuple fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive prefixItems 400 leftover items tuple."),
     p(slug="leftover-items-array-tuple", domain="leftover-items-array-tuple-vs-oas-schema-prefixitems-tuple", success=False, name="99ca4b", stack="OpenAPI leftover prefixItems + Java + TS", field="prefixItems", old="prefixItems tuple", new="items tuple leftover only", fail_err="400: leftover prefixItems tuple after items tuple leftover-only", plan="items tuple leftover-only 400s leftover prefixItems tuple. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (items tuple leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive prefixItems 400 leftover items tuple.", fetch2="https://json-schema.org/understanding-json-schema/reference/array#tuple-validation", fetch2_ok="prefixItems is positional tuple validation, leftover items-as-tuple fails closed.")),
    (p(slug="oas-unevaluated-items-false", domain="oas-unevaluated-items-false-vs-leftover-open-tuple-tail", success=True, name="637e4c", stack="OpenAPI 3.1 unevaluatedItems + Go", field="unevaluatedItems", old="open tuple tail leftover", new="unevaluatedItems false", fail_err="400: leftover open tuple tail leftover after unevaluatedItems false-only", plan="unevaluatedItems false-only 400s leftover open tuple tail leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (unevaluatedItems false vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/array#unevaluateditems", fetch1_ok="unevaluatedItems false closes leftover tuple tails.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive unevaluatedItems 400 leftover open tail."),
     p(slug="leftover-open-tuple-tail", domain="leftover-open-tuple-tail-vs-oas-unevaluated-items-false", success=False, name="4b5477", stack="OpenAPI leftover unevaluatedItems + Java + TS", field="unevaluatedItems", old="unevaluatedItems false", new="open tuple tail leftover only", fail_err="400: leftover unevaluatedItems false after open tuple tail leftover-only", plan="open tuple tail leftover-only 400s leftover unevaluatedItems false. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (open tuple tail leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive unevaluatedItems 400 leftover open tail.", fetch2="https://json-schema.org/understanding-json-schema/reference/array#unevaluateditems", fetch2_ok="unevaluatedItems false closes leftover tuple tails.")),
    (p(slug="oas-schema-content-media-type", domain="oas-schema-content-media-type-vs-leftover-untyped-encoded-blob", success=True, name="da9a32", stack="OpenAPI 3.1 contentMediaType + Go", field="contentMediaType", old="untyped encoded leftover", new="contentMediaType", fail_err="415: leftover untyped encoded leftover after contentMediaType-only", plan="contentMediaType-only 415s leftover untyped encoded leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (contentMediaType vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/non_json_data#contentmediatype", fetch1_ok="contentMediaType names the decoded type, leftover untyped blobs fail closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="Exclusive contentMediaType 415 leftover untyped blob."),
     p(slug="leftover-untyped-encoded-blob", domain="leftover-untyped-encoded-blob-vs-oas-schema-content-media-type", success=False, name="634444", stack="OpenAPI leftover contentMediaType + Java + TS", field="contentMediaType", old="contentMediaType", new="untyped encoded leftover only", fail_err="415: leftover contentMediaType after untyped encoded leftover-only", plan="untyped encoded leftover-only 415s leftover contentMediaType. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (untyped encoded leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="Exclusive contentMediaType 415 leftover untyped blob.", fetch2="https://json-schema.org/understanding-json-schema/reference/non_json_data#contentmediatype", fetch2_ok="contentMediaType names the decoded type, leftover untyped blobs fail closed.")),
    (p(slug="oas-schema-dynamic-anchor", domain="oas-schema-dynamic-anchor-vs-leftover-static-anchor-only", success=True, name="c38d39", stack="OpenAPI 3.1 $dynamicAnchor + Go", field="$dynamicAnchor", old="static anchor leftover", new="$dynamicAnchor", fail_err="400: leftover static anchor leftover after $dynamicAnchor-only", plan="$dynamicAnchor-only 400s leftover static anchor leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv ($dynamicAnchor vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/schema#dynamic-references", fetch1_ok="$dynamicAnchor is not leftover static $anchor only.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive $dynamicAnchor 400 leftover static."),
     p(slug="leftover-static-anchor-only", domain="leftover-static-anchor-only-vs-oas-schema-dynamic-anchor", success=False, name="41b983", stack="OpenAPI leftover $dynamicAnchor + Java + TS", field="$dynamicAnchor", old="$dynamicAnchor", new="static anchor leftover only", fail_err="400: leftover $dynamicAnchor after static anchor leftover-only", plan="static anchor leftover-only 400s leftover $dynamicAnchor. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (static anchor leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive $dynamicAnchor 400 leftover static.", fetch2="https://json-schema.org/understanding-json-schema/reference/schema#dynamic-references", fetch2_ok="$dynamicAnchor is not leftover static $anchor only.")),
    (p(slug="oas-schema-externaldocs-url", domain="oas-schema-externaldocs-url-vs-leftover-schema-no-docs", success=True, name="c8b97d", stack="OpenAPI 3.1 externalDocs + Go", field="externalDocs", old="schema no docs leftover", new="schema externalDocs url", fail_err="400: leftover schema no docs leftover after schema externalDocs url-only", plan="schema externalDocs url-only 400s leftover schema no docs leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (schema externalDocs url vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#external-documentation-object", fetch1_ok="Schema externalDocs.url is required when present, leftover missing fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive schema docs 400 leftover none."),
     p(slug="leftover-schema-no-docs", domain="leftover-schema-no-docs-vs-oas-schema-externaldocs-url", success=False, name="1cdbae", stack="OpenAPI leftover externalDocs + Java + TS", field="externalDocs", old="schema externalDocs url", new="schema no docs leftover only", fail_err="400: leftover schema externalDocs url after schema no docs leftover-only", plan="schema no docs leftover-only 400s leftover schema externalDocs url. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (schema no docs leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive schema docs 400 leftover none.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#external-documentation-object", fetch2_ok="Schema externalDocs.url is required when present, leftover missing fails closed.")),
    (p(slug="oas-parameter-allow-reserved", domain="oas-parameter-allow-reserved-vs-leftover-always-percent-encode", success=True, name="065454", stack="OpenAPI 3.1 allowReserved + Go", field="allowReserved", old="always percent leftover", new="allowReserved true", fail_err="400: leftover always percent leftover after allowReserved true-only", plan="allowReserved true-only 400s leftover always percent leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (allowReserved true vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="allowReserved lets RFC3986 reserved chars through, leftover always-encode fails closed.", fetch2="https://datatracker.ietf.org/doc/html/rfc3986", fetch2_ok="Exclusive allowReserved 400 leftover percent-all."),
     p(slug="leftover-always-percent-encode", domain="leftover-always-percent-encode-vs-oas-parameter-allow-reserved", success=False, name="78bb0f", stack="OpenAPI leftover allowReserved + Java + TS", field="allowReserved", old="allowReserved true", new="always percent leftover only", fail_err="400: leftover allowReserved true after always percent leftover-only", plan="always percent leftover-only 400s leftover allowReserved true. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (always percent leftover leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc3986", fetch1_ok="Exclusive allowReserved 400 leftover percent-all.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="allowReserved lets RFC3986 reserved chars through, leftover always-encode fails closed.")),
    (p(slug="oas-schema-exclusive-min-number", domain="oas-schema-exclusive-min-number-vs-leftover-exclusive-min-boolean", success=True, name="3c51c6", stack="OpenAPI 3.1 exclusiveMinimum + Go", field="exclusiveMinimum", old="boolean exclusiveMinimum leftover", new="numeric exclusiveMinimum", fail_err="400: leftover boolean exclusiveMinimum leftover after numeric exclusiveMinimum-only", plan="numeric exclusiveMinimum-only 400s leftover boolean exclusiveMinimum leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (numeric exclusiveMinimum vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/numeric#exclusiveminimum", fetch1_ok="JSON Schema 2020-12 exclusiveMinimum is a number, leftover OAS 3.0 boolean fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="Exclusive numeric exclusiveMinimum 400 leftover boolean."),
     p(slug="leftover-exclusive-min-boolean", domain="leftover-exclusive-min-boolean-vs-oas-schema-exclusive-min-number", success=False, name="525a13", stack="OpenAPI leftover exclusiveMinimum + Java + TS", field="exclusiveMinimum", old="numeric exclusiveMinimum", new="boolean exclusiveMinimum leftover only", fail_err="400: leftover numeric exclusiveMinimum after boolean exclusiveMinimum leftover-only", plan="boolean exclusiveMinimum leftover-only 400s leftover numeric exclusiveMinimum. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (boolean exclusiveMinimum leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="Exclusive numeric exclusiveMinimum 400 leftover boolean.", fetch2="https://json-schema.org/understanding-json-schema/reference/numeric#exclusiveminimum", fetch2_ok="JSON Schema 2020-12 exclusiveMinimum is a number, leftover OAS 3.0 boolean fails closed.")),
    (p(slug="oas-type-null-union", domain="oas-type-null-union-vs-leftover-nullable-true-flag", success=True, name="d99d58", stack="OpenAPI 3.1 type + Go", field="type", old="nullable true leftover", new="type null union", fail_err="400: leftover nullable true leftover after type null union-only", plan="type null union-only 400s leftover nullable true leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (type null union vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="OAS 3.1 uses type union with null, leftover nullable true fails closed.", fetch2="https://json-schema.org/understanding-json-schema/reference/null", fetch2_ok="Exclusive type null union 400 leftover nullable."),
     p(slug="leftover-nullable-true-flag", domain="leftover-nullable-true-flag-vs-oas-type-null-union", success=False, name="d1870f", stack="OpenAPI leftover type + Java + TS", field="type", old="type null union", new="nullable true leftover only", fail_err="400: leftover type null union after nullable true leftover-only", plan="nullable true leftover-only 400s leftover type null union. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (nullable true leftover leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/null", fetch1_ok="Exclusive type null union 400 leftover nullable.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="OAS 3.1 uses type union with null, leftover nullable true fails closed.")),
    (p(slug="oas-json-schema-const-value", domain="oas-json-schema-const-value-vs-leftover-single-enum-member", success=True, name="3aef84", stack="OpenAPI 3.1 const + Go", field="const", old="single enum leftover", new="schema const", fail_err="400: leftover single enum leftover after schema const-only", plan="schema const-only 400s leftover single enum leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (schema const vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/generic#const", fetch1_ok="const is a single literal, leftover enum-of-one is not that.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive const 400 leftover singleton enum."),
     p(slug="leftover-single-enum-member", domain="leftover-single-enum-member-vs-oas-json-schema-const-value", success=False, name="898ade", stack="OpenAPI leftover const + Java + TS", field="const", old="schema const", new="single enum leftover only", fail_err="400: leftover schema const after single enum leftover-only", plan="single enum leftover-only 400s leftover schema const. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (single enum leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive const 400 leftover singleton enum.", fetch2="https://json-schema.org/understanding-json-schema/reference/generic#const", fetch2_ok="const is a single literal, leftover enum-of-one is not that.")),
    (p(slug="oas-http-bearer-format", domain="oas-http-bearer-format-vs-leftover-unformatted-bearer", success=True, name="146c54", stack="OpenAPI 3.1 bearerFormat + Go", field="bearerFormat", old="unformatted bearer leftover", new="bearerFormat", fail_err="401: leftover unformatted bearer leftover after bearerFormat-only", plan="bearerFormat-only 401s leftover unformatted bearer leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (bearerFormat vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch1_ok="bearerFormat documents the token, leftover unformatted fails closed.", fetch2="https://datatracker.ietf.org/doc/html/rfc6750", fetch2_ok="Exclusive bearerFormat 401 leftover unformatted."),
     p(slug="leftover-unformatted-bearer", domain="leftover-unformatted-bearer-vs-oas-http-bearer-format", success=False, name="1ff6f4", stack="OpenAPI leftover bearerFormat + Java + TS", field="bearerFormat", old="bearerFormat", new="unformatted bearer leftover only", fail_err="401: leftover bearerFormat after unformatted bearer leftover-only", plan="unformatted bearer leftover-only 401s leftover bearerFormat. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (unformatted bearer leftover leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc6750", fetch1_ok="Exclusive bearerFormat 401 leftover unformatted.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch2_ok="bearerFormat documents the token, leftover unformatted fails closed.")),
    (p(slug="oas-encoding-allow-reserved", domain="oas-encoding-allow-reserved-vs-leftover-encoding-pct-all", success=True, name="b6cefa", stack="OpenAPI 3.1 allowReserved + Go", field="allowReserved", old="encoding percent leftover", new="encoding allowReserved", fail_err="415: leftover encoding percent leftover after encoding allowReserved-only", plan="encoding allowReserved-only 415s leftover encoding percent leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (encoding allowReserved vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#encoding-object", fetch1_ok="encoding.allowReserved is not leftover percent-encode-all parts.", fetch2="https://datatracker.ietf.org/doc/html/rfc3986", fetch2_ok="Exclusive encoding allowReserved 415 leftover percent-all."),
     p(slug="leftover-encoding-pct-all", domain="leftover-encoding-pct-all-vs-oas-encoding-allow-reserved", success=False, name="daae2a", stack="OpenAPI leftover allowReserved + Java + TS", field="allowReserved", old="encoding allowReserved", new="encoding percent leftover only", fail_err="415: leftover encoding allowReserved after encoding percent leftover-only", plan="encoding percent leftover-only 415s leftover encoding allowReserved. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (encoding percent leftover leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc3986", fetch1_ok="Exclusive encoding allowReserved 415 leftover percent-all.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#encoding-object", fetch2_ok="encoding.allowReserved is not leftover percent-encode-all parts.")),
    (p(slug="oas-link-opref-pointer", domain="oas-link-opref-pointer-vs-leftover-link-opid-only", success=True, name="54d3c4", stack="OpenAPI 3.1 operationRef + Go", field="operationRef", old="operationId only leftover", new="link operationRef", fail_err="400: leftover operationId only leftover after link operationRef-only", plan="link operationRef-only 400s leftover operationId only leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (link operationRef vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#link-object", fetch1_ok="operationRef is a runtime pointer, leftover operationId-only is not that.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#runtime-expressions", fetch2_ok="Exclusive operationRef 400 leftover opid only."),
     p(slug="leftover-link-opid-only", domain="leftover-link-opid-only-vs-oas-link-opref-pointer", success=False, name="cc8983", stack="OpenAPI leftover operationRef + Java + TS", field="operationRef", old="link operationRef", new="operationId only leftover only", fail_err="400: leftover link operationRef after operationId only leftover-only", plan="operationId only leftover-only 400s leftover link operationRef. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (operationId only leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#runtime-expressions", fetch1_ok="Exclusive operationRef 400 leftover opid only.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#link-object", fetch2_ok="operationRef is a runtime pointer, leftover operationId-only is not that.")),
    (p(slug="oas-path-head-method", domain="oas-path-head-method-vs-leftover-get-as-head", success=True, name="1a9e5a", stack="OpenAPI 3.1 head + Go", field="head", old="GET as HEAD leftover", new="HEAD method", fail_err="400: leftover GET as HEAD leftover after HEAD method-only", plan="HEAD method-only 400s leftover GET as HEAD leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (HEAD method vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#path-item-object", fetch1_ok="HEAD is a distinct operation, leftover GET-as-HEAD fails closed.", fetch2="https://datatracker.ietf.org/doc/html/rfc9110#name-head", fetch2_ok="Exclusive HEAD 400 leftover GET-as-HEAD."),
     p(slug="leftover-get-as-head", domain="leftover-get-as-head-vs-oas-path-head-method", success=False, name="aaa8d8", stack="OpenAPI leftover head + Java + TS", field="head", old="HEAD method", new="GET as HEAD leftover only", fail_err="400: leftover HEAD method after GET as HEAD leftover-only", plan="GET as HEAD leftover-only 400s leftover HEAD method. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (GET as HEAD leftover leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc9110#name-head", fetch1_ok="Exclusive HEAD 400 leftover GET-as-HEAD.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#path-item-object", fetch2_ok="HEAD is a distinct operation, leftover GET-as-HEAD fails closed.")),
    (p(slug="oas-oauth2-password-flow", domain="oas-oauth2-password-flow-vs-leftover-ropc-query-token", success=True, name="97f47b", stack="OpenAPI 3.1 password + Go", field="password", old="ROPC query leftover", new="oauth2 password flow", fail_err="401: leftover ROPC query leftover after oauth2 password flow-only", plan="oauth2 password flow-only 401s leftover ROPC query leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (oauth2 password flow vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#oauth-flow-object", fetch1_ok="password flow uses tokenUrl, leftover query-token ROPC fails closed.", fetch2="https://datatracker.ietf.org/doc/html/rfc6749#section-4.3", fetch2_ok="Exclusive password flow 401 leftover query token."),
     p(slug="leftover-ropc-query-token", domain="leftover-ropc-query-token-vs-oas-oauth2-password-flow", success=False, name="fe30c0", stack="OpenAPI leftover password + Java + TS", field="password", old="oauth2 password flow", new="ROPC query leftover only", fail_err="401: leftover oauth2 password flow after ROPC query leftover-only", plan="ROPC query leftover-only 401s leftover oauth2 password flow. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (ROPC query leftover leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc6749#section-4.3", fetch1_ok="Exclusive password flow 401 leftover query token.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#oauth-flow-object", fetch2_ok="password flow uses tokenUrl, leftover query-token ROPC fails closed.")),
    (p(slug="oas-security-oidc-url", domain="oas-security-oidc-url-vs-leftover-issuer-only-oidc", success=True, name="1d2392", stack="OpenAPI 3.1 openIdConnectUrl + Go", field="openIdConnectUrl", old="issuer only leftover", new="openIdConnectUrl", fail_err="401: leftover issuer only leftover after openIdConnectUrl-only", plan="openIdConnectUrl-only 401s leftover issuer only leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (openIdConnectUrl vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch1_ok="openIdConnectUrl is the discovery document, leftover issuer-only fails closed.", fetch2="https://datatracker.ietf.org/doc/html/rfc8414", fetch2_ok="Exclusive OIDC url 401 leftover issuer."),
     p(slug="leftover-issuer-only-oidc", domain="leftover-issuer-only-oidc-vs-oas-security-oidc-url", success=False, name="99ce49", stack="OpenAPI leftover openIdConnectUrl + Java + TS", field="openIdConnectUrl", old="openIdConnectUrl", new="issuer only leftover only", fail_err="401: leftover openIdConnectUrl after issuer only leftover-only", plan="issuer only leftover-only 401s leftover openIdConnectUrl. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (issuer only leftover leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc8414", fetch1_ok="Exclusive OIDC url 401 leftover issuer.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch2_ok="openIdConnectUrl is the discovery document, leftover issuer-only fails closed.")),
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
    print(json.dumps({"round": round_n, "idx": idx, "ids": [e1["id"], e2["id"]], "catalog": "r4230"}))


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
