#!/usr/bin/env python3
"""Unique OpenAPI-drift ACM catalog r4438. Fast slug load."""
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
    (p(slug="oas-json-merge-patch-media", domain="oas-json-merge-patch-media-vs-leftover-json-patch-as-merge", success=True, name="98e970", stack="OpenAPI 3.1 contentType + Go", field="contentType", old="json patch as merge leftover", new="merge-patch+json", fail_err="415: leftover json patch as merge leftover after merge-patch+json-only", plan="merge-patch+json-only 415s leftover json patch as merge leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (merge-patch+json vs leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc7396", fetch1_ok="application/merge-patch+json is not leftover json-patch.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch2_ok="Exclusive merge-patch 415 leftover json-patch."),
     p(slug="leftover-json-patch-as-merge", domain="leftover-json-patch-as-merge-vs-oas-json-merge-patch-media", success=False, name="f8c22c", stack="OpenAPI leftover contentType + Java + TS", field="contentType", old="merge-patch+json", new="json patch as merge leftover only", fail_err="415: leftover merge-patch+json after json patch as merge leftover-only", plan="json patch as merge leftover-only 415s leftover merge-patch+json. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (json patch as merge leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch1_ok="Exclusive merge-patch 415 leftover json-patch.", fetch2="https://datatracker.ietf.org/doc/html/rfc7396", fetch2_ok="application/merge-patch+json is not leftover json-patch.")),
    (p(slug="oas-json-patch-media", domain="oas-json-patch-media-vs-leftover-merge-as-json-patch", success=True, name="938793", stack="OpenAPI 3.1 contentType + Go", field="contentType", old="merge as patch leftover", new="json-patch+json", fail_err="415: leftover merge as patch leftover after json-patch+json-only", plan="json-patch+json-only 415s leftover merge as patch leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (json-patch+json vs leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc6902", fetch1_ok="application/json-patch+json is not leftover merge-patch.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch2_ok="Exclusive json-patch 415 leftover merge."),
     p(slug="leftover-merge-as-json-patch", domain="leftover-merge-as-json-patch-vs-oas-json-patch-media", success=False, name="943891", stack="OpenAPI leftover contentType + Java + TS", field="contentType", old="json-patch+json", new="merge as patch leftover only", fail_err="415: leftover json-patch+json after merge as patch leftover-only", plan="merge as patch leftover-only 415s leftover json-patch+json. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (merge as patch leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch1_ok="Exclusive json-patch 415 leftover merge.", fetch2="https://datatracker.ietf.org/doc/html/rfc6902", fetch2_ok="application/json-patch+json is not leftover merge-patch.")),
    (p(slug="oas-multipart-form-data", domain="oas-multipart-form-data-vs-leftover-urlencoded-as-multipart", success=True, name="09072b", stack="OpenAPI 3.1 contentType + Go", field="contentType", old="urlencoded as multipart leftover", new="multipart form-data", fail_err="415: leftover urlencoded as multipart leftover after multipart form-data-only", plan="multipart form-data-only 415s leftover urlencoded as multipart leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (multipart form-data vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch1_ok="multipart/form-data is not leftover urlencoded.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#encoding-object", fetch2_ok="Exclusive multipart 415 leftover urlencoded."),
     p(slug="leftover-urlencoded-as-multipart", domain="leftover-urlencoded-as-multipart-vs-oas-multipart-form-data", success=False, name="c9b7fc", stack="OpenAPI leftover contentType + Java + TS", field="contentType", old="multipart form-data", new="urlencoded as multipart leftover only", fail_err="415: leftover multipart form-data after urlencoded as multipart leftover-only", plan="urlencoded as multipart leftover-only 415s leftover multipart form-data. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (urlencoded as multipart leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#encoding-object", fetch1_ok="Exclusive multipart 415 leftover urlencoded.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch2_ok="multipart/form-data is not leftover urlencoded.")),
    (p(slug="oas-urlencoded-form", domain="oas-urlencoded-form-vs-leftover-json-as-form", success=True, name="a547d9", stack="OpenAPI 3.1 contentType + Go", field="contentType", old="json as form leftover", new="urlencoded form", fail_err="415: leftover json as form leftover after urlencoded form-only", plan="urlencoded form-only 415s leftover json as form leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (urlencoded form vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch1_ok="application/x-www-form-urlencoded is not leftover JSON.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#encoding-object", fetch2_ok="Exclusive urlencoded 415 leftover json."),
     p(slug="leftover-json-as-form", domain="leftover-json-as-form-vs-oas-urlencoded-form", success=False, name="50fc9d", stack="OpenAPI leftover contentType + Java + TS", field="contentType", old="urlencoded form", new="json as form leftover only", fail_err="415: leftover urlencoded form after json as form leftover-only", plan="json as form leftover-only 415s leftover urlencoded form. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (json as form leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#encoding-object", fetch1_ok="Exclusive urlencoded 415 leftover json.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch2_ok="application/x-www-form-urlencoded is not leftover JSON.")),
    (p(slug="oas-octet-stream-body", domain="oas-octet-stream-body-vs-leftover-base64-in-json-body", success=True, name="78cabe", stack="OpenAPI 3.1 contentType + Go", field="contentType", old="base64 json leftover", new="octet-stream body", fail_err="415: leftover base64 json leftover after octet-stream body-only", plan="octet-stream body-only 415s leftover base64 json leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (octet-stream body vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch1_ok="application/octet-stream is not leftover base64-in-JSON.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="Exclusive octet-stream 415 leftover base64 json."),
     p(slug="leftover-base64-in-json-body", domain="leftover-base64-in-json-body-vs-oas-octet-stream-body", success=False, name="be315f", stack="OpenAPI leftover contentType + Java + TS", field="contentType", old="octet-stream body", new="base64 json leftover only", fail_err="415: leftover octet-stream body after base64 json leftover-only", plan="base64 json leftover-only 415s leftover octet-stream body. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (base64 json leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="Exclusive octet-stream 415 leftover base64 json.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch2_ok="application/octet-stream is not leftover base64-in-JSON.")),
    (p(slug="oas-text-plain-body", domain="oas-text-plain-body-vs-leftover-json-string-as-text", success=True, name="0515a3", stack="OpenAPI 3.1 contentType + Go", field="contentType", old="json string leftover", new="text/plain body", fail_err="415: leftover json string leftover after text/plain body-only", plan="text/plain body-only 415s leftover json string leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (text/plain body vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch1_ok="text/plain is not leftover JSON string bodies.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive text/plain 415 leftover json string."),
     p(slug="leftover-json-string-as-text", domain="leftover-json-string-as-text-vs-oas-text-plain-body", success=False, name="50cbc1", stack="OpenAPI leftover contentType + Java + TS", field="contentType", old="text/plain body", new="json string leftover only", fail_err="415: leftover text/plain body after json string leftover-only", plan="json string leftover-only 415s leftover text/plain body. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (json string leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive text/plain 415 leftover json string.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch2_ok="text/plain is not leftover JSON string bodies.")),
    (p(slug="oas-xml-app-media", domain="oas-xml-app-media-vs-leftover-text-xml-media", success=True, name="d5a4b5", stack="OpenAPI 3.1 contentType + Go", field="contentType", old="text xml leftover", new="application/xml", fail_err="415: leftover text xml leftover after application/xml-only", plan="application/xml-only 415s leftover text xml leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (application/xml vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch1_ok="application/xml is not leftover text/xml.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#xml-object", fetch2_ok="Exclusive application/xml 415 leftover text/xml."),
     p(slug="leftover-text-xml-media", domain="leftover-text-xml-media-vs-oas-xml-app-media", success=False, name="497964", stack="OpenAPI leftover contentType + Java + TS", field="contentType", old="application/xml", new="text xml leftover only", fail_err="415: leftover application/xml after text xml leftover-only", plan="text xml leftover-only 415s leftover application/xml. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (text xml leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#xml-object", fetch1_ok="Exclusive application/xml 415 leftover text/xml.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch2_ok="application/xml is not leftover text/xml.")),
    (p(slug="oas-json-schema-2020-12", domain="oas-json-schema-2020-12-vs-leftover-draft7-schema", success=True, name="6c635b", stack="OpenAPI 3.1 $schema + Go", field="$schema", old="draft7 leftover", new="JSON Schema 2020-12", fail_err="400: leftover draft7 leftover after JSON Schema 2020-12-only", plan="JSON Schema 2020-12-only 400s leftover draft7 leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (JSON Schema 2020-12 vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/schema", fetch1_ok="2020-12 dialect is not leftover draft-07.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive 2020-12 400 leftover draft7."),
     p(slug="leftover-draft7-schema", domain="leftover-draft7-schema-vs-oas-json-schema-2020-12", success=False, name="0ef65c", stack="OpenAPI leftover $schema + Java + TS", field="$schema", old="JSON Schema 2020-12", new="draft7 leftover only", fail_err="400: leftover JSON Schema 2020-12 after draft7 leftover-only", plan="draft7 leftover-only 400s leftover JSON Schema 2020-12. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (draft7 leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive 2020-12 400 leftover draft7.", fetch2="https://json-schema.org/understanding-json-schema/reference/schema", fetch2_ok="2020-12 dialect is not leftover draft-07.")),
    (p(slug="oas-additional-items-removed", domain="oas-additional-items-removed-vs-leftover-additional-items-keyword", success=True, name="24dd1b", stack="OpenAPI 3.1 additionalItems + Go", field="additionalItems", old="additionalItems leftover", new="additionalItems removed", fail_err="400: leftover additionalItems leftover after additionalItems removed-only", plan="additionalItems removed-only 400s leftover additionalItems leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (additionalItems removed vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/array#additionalitems", fetch1_ok="OAS 3.1 dropped additionalItems, leftover keyword fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive additionalItems removed 400 leftover keyword."),
     p(slug="leftover-additional-items-keyword", domain="leftover-additional-items-keyword-vs-oas-additional-items-removed", success=False, name="cbf36c", stack="OpenAPI leftover additionalItems + Java + TS", field="additionalItems", old="additionalItems removed", new="additionalItems leftover only", fail_err="400: leftover additionalItems removed after additionalItems leftover-only", plan="additionalItems leftover-only 400s leftover additionalItems removed. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (additionalItems leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive additionalItems removed 400 leftover keyword.", fetch2="https://json-schema.org/understanding-json-schema/reference/array#additionalitems", fetch2_ok="OAS 3.1 dropped additionalItems, leftover keyword fails closed.")),
    (p(slug="oas-nullable-keyword-removed", domain="oas-nullable-keyword-removed-vs-leftover-nullable-oas30", success=True, name="191341", stack="OpenAPI 3.1 nullable + Go", field="nullable", old="nullable oas30 leftover", new="nullable removed", fail_err="400: leftover nullable oas30 leftover after nullable removed-only", plan="nullable removed-only 400s leftover nullable oas30 leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (nullable removed vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="OAS 3.1 removed nullable, leftover keyword fails closed.", fetch2="https://json-schema.org/understanding-json-schema/reference/null", fetch2_ok="Exclusive nullable removed 400 leftover oas30."),
     p(slug="leftover-nullable-oas30", domain="leftover-nullable-oas30-vs-oas-nullable-keyword-removed", success=False, name="814834", stack="OpenAPI leftover nullable + Java + TS", field="nullable", old="nullable removed", new="nullable oas30 leftover only", fail_err="400: leftover nullable removed after nullable oas30 leftover-only", plan="nullable oas30 leftover-only 400s leftover nullable removed. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (nullable oas30 leftover leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/null", fetch1_ok="Exclusive nullable removed 400 leftover oas30.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="OAS 3.1 removed nullable, leftover keyword fails closed.")),
    (p(slug="oas-example-vs-examples-param", domain="oas-example-vs-examples-param-vs-leftover-param-both-examples", success=True, name="4223a3", stack="OpenAPI 3.1 examples + Go", field="examples", old="param both leftover", new="param example xor examples", fail_err="400: leftover param both leftover after param example xor examples-only", plan="param example xor examples-only 400s leftover param both leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (param example xor examples vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="parameter example and examples are exclusive, leftover both fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#example-object", fetch2_ok="Exclusive param xor 400 leftover both."),
     p(slug="leftover-param-both-examples", domain="leftover-param-both-examples-vs-oas-example-vs-examples-param", success=False, name="f14391", stack="OpenAPI leftover examples + Java + TS", field="examples", old="param example xor examples", new="param both leftover only", fail_err="400: leftover param example xor examples after param both leftover-only", plan="param both leftover-only 400s leftover param example xor examples. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (param both leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#example-object", fetch1_ok="Exclusive param xor 400 leftover both.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="parameter example and examples are exclusive, leftover both fails closed.")),
    (p(slug="oas-style-deepobject-cookie", domain="oas-style-deepobject-cookie-vs-leftover-cookie-bracket-keys", success=True, name="e4f72b", stack="OpenAPI 3.1 style + Go", field="style", old="cookie bracket leftover", new="cookie deepObject", fail_err="400: leftover cookie bracket leftover after cookie deepObject-only", plan="cookie deepObject-only 400s leftover cookie bracket leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (cookie deepObject vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch1_ok="deepObject on cookie is not leftover bracket keys.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="Exclusive cookie deepObject 400 leftover bracket."),
     p(slug="leftover-cookie-bracket-keys", domain="leftover-cookie-bracket-keys-vs-oas-style-deepobject-cookie", success=False, name="245355", stack="OpenAPI leftover style + Java + TS", field="style", old="cookie deepObject", new="cookie bracket leftover only", fail_err="400: leftover cookie deepObject after cookie bracket leftover-only", plan="cookie bracket leftover-only 400s leftover cookie deepObject. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (cookie bracket leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="Exclusive cookie deepObject 400 leftover bracket.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch2_ok="deepObject on cookie is not leftover bracket keys.")),
    (p(slug="oas-allowemptyvalue-query", domain="oas-allowemptyvalue-query-vs-leftover-query-omit-blank", success=True, name="dd658b", stack="OpenAPI 3.1 allowEmptyValue + Go", field="allowEmptyValue", old="omit blank leftover", new="query allowEmptyValue", fail_err="400: leftover omit blank leftover after query allowEmptyValue-only", plan="query allowEmptyValue-only 400s leftover omit blank leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (query allowEmptyValue vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="query allowEmptyValue is not leftover omit-blank.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch2_ok="Exclusive query empty 400 leftover omit blank."),
     p(slug="leftover-query-omit-blank", domain="leftover-query-omit-blank-vs-oas-allowemptyvalue-query", success=False, name="99dea1", stack="OpenAPI leftover allowEmptyValue + Java + TS", field="allowEmptyValue", old="query allowEmptyValue", new="omit blank leftover only", fail_err="400: leftover query allowEmptyValue after omit blank leftover-only", plan="omit blank leftover-only 400s leftover query allowEmptyValue. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (omit blank leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch1_ok="Exclusive query empty 400 leftover omit blank.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="query allowEmptyValue is not leftover omit-blank.")),
    (p(slug="oas-header-deprecated-flag", domain="oas-header-deprecated-flag-vs-leftover-live-deprecated-header", success=True, name="accfe7", stack="OpenAPI 3.1 deprecated + Go", field="deprecated", old="live deprecated leftover", new="header deprecated", fail_err="400: leftover live deprecated leftover after header deprecated-only", plan="header deprecated-only 400s leftover live deprecated leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (header deprecated vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch1_ok="deprecated headers must not ship live, leftover still-live fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="Exclusive header deprecated 400 leftover live."),
     p(slug="leftover-live-deprecated-header", domain="leftover-live-deprecated-header-vs-oas-header-deprecated-flag", success=False, name="b52321", stack="OpenAPI leftover deprecated + Java + TS", field="deprecated", old="header deprecated", new="live deprecated leftover only", fail_err="400: leftover header deprecated after live deprecated leftover-only", plan="live deprecated leftover-only 400s leftover header deprecated. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (live deprecated leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="Exclusive header deprecated 400 leftover live.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch2_ok="deprecated headers must not ship live, leftover still-live fails closed.")),
    (p(slug="oas-param-explode-path-false", domain="oas-param-explode-path-false-vs-leftover-path-explode-true", success=True, name="630684", stack="OpenAPI 3.1 explode + Go", field="explode", old="path explode leftover", new="path explode false", fail_err="400: leftover path explode leftover after path explode false-only", plan="path explode false-only 400s leftover path explode leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (path explode false vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch1_ok="path explode false is not leftover explode true.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="Exclusive path explode false 400 leftover true."),
     p(slug="leftover-path-explode-true", domain="leftover-path-explode-true-vs-oas-param-explode-path-false", success=False, name="d4fa79", stack="OpenAPI leftover explode + Java + TS", field="explode", old="path explode false", new="path explode leftover only", fail_err="400: leftover path explode false after path explode leftover-only", plan="path explode leftover-only 400s leftover path explode false. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (path explode leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="Exclusive path explode false 400 leftover true.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch2_ok="path explode false is not leftover explode true.")),
    (p(slug="oas-server-variable-pattern", domain="oas-server-variable-pattern-vs-leftover-server-var-unbounded", success=True, name="14b687", stack="OpenAPI 3.1 pattern + Go", field="pattern", old="unbounded server var leftover", new="server var pattern", fail_err="400: leftover unbounded server var leftover after server var pattern-only", plan="server var pattern-only 400s leftover unbounded server var leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (server var pattern vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#server-variable-object", fetch1_ok="server variable pattern bounds values, leftover unbounded fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#server-object", fetch2_ok="Exclusive server pattern 400 leftover unbounded."),
     p(slug="leftover-server-var-unbounded", domain="leftover-server-var-unbounded-vs-oas-server-variable-pattern", success=False, name="8cd35c", stack="OpenAPI leftover pattern + Java + TS", field="pattern", old="server var pattern", new="unbounded server var leftover only", fail_err="400: leftover server var pattern after unbounded server var leftover-only", plan="unbounded server var leftover-only 400s leftover server var pattern. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (unbounded server var leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#server-object", fetch1_ok="Exclusive server pattern 400 leftover unbounded.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#server-variable-object", fetch2_ok="server variable pattern bounds values, leftover unbounded fails closed.")),
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
    print(json.dumps({"round": round_n, "idx": idx, "ids": [e1["id"], e2["id"]], "catalog": "r4438"}))


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
