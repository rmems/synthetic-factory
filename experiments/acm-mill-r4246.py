#!/usr/bin/env python3
"""Unique OpenAPI-drift ACM catalog r4246. Fast slug load."""
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
    (p(slug="oas-schema-readonly-omit-write", domain="oas-schema-readonly-omit-write-vs-leftover-write-echo-readonly", success=True, name="16a52a", stack="OpenAPI 3.1 readOnly + Go", field="readOnly", old="write echo leftover", new="readOnly omit write", fail_err="400: leftover write echo leftover after readOnly omit write-only", plan="readOnly omit write-only 400s leftover write echo leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (readOnly omit write vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="readOnly properties must be omitted on write, leftover echo fails closed.", fetch2="https://json-schema.org/understanding-json-schema/reference/object", fetch2_ok="Exclusive readOnly omit 400 leftover write echo."),
     p(slug="leftover-write-echo-readonly", domain="leftover-write-echo-readonly-vs-oas-schema-readonly-omit-write", success=False, name="70f821", stack="OpenAPI leftover readOnly + Java + TS", field="readOnly", old="readOnly omit write", new="write echo leftover only", fail_err="400: leftover readOnly omit write after write echo leftover-only", plan="write echo leftover-only 400s leftover readOnly omit write. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (write echo leftover leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/object", fetch1_ok="Exclusive readOnly omit 400 leftover write echo.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="readOnly properties must be omitted on write, leftover echo fails closed.")),
    (p(slug="oas-schema-deprecated-true", domain="oas-schema-deprecated-true-vs-leftover-ship-deprecated-field", success=True, name="08153b", stack="OpenAPI 3.1 deprecated + Go", field="deprecated", old="ship deprecated leftover", new="schema deprecated true", fail_err="400: leftover ship deprecated leftover after schema deprecated true-only", plan="schema deprecated true-only 400s leftover ship deprecated leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (schema deprecated true vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="deprecated true must not ship as live, leftover still-shipped fails closed.", fetch2="https://json-schema.org/understanding-json-schema/reference/generic#annotation", fetch2_ok="Exclusive deprecated 400 leftover shipped field."),
     p(slug="leftover-ship-deprecated-field", domain="leftover-ship-deprecated-field-vs-oas-schema-deprecated-true", success=False, name="3125df", stack="OpenAPI leftover deprecated + Java + TS", field="deprecated", old="schema deprecated true", new="ship deprecated leftover only", fail_err="400: leftover schema deprecated true after ship deprecated leftover-only", plan="ship deprecated leftover-only 400s leftover schema deprecated true. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (ship deprecated leftover leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/generic#annotation", fetch1_ok="Exclusive deprecated 400 leftover shipped field.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="deprecated true must not ship as live, leftover still-shipped fails closed.")),
    (p(slug="oas-media-single-example", domain="oas-media-single-example-vs-leftover-examples-map-forced", success=True, name="35a55d", stack="OpenAPI 3.1 example + Go", field="example", old="examples map leftover", new="media example", fail_err="400: leftover examples map leftover after media example-only", plan="media example-only 400s leftover examples map leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (media example vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch1_ok="example is a single value, leftover examples-map-only is not that.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#example-object", fetch2_ok="Exclusive media example 400 leftover examples map."),
     p(slug="leftover-examples-map-forced", domain="leftover-examples-map-forced-vs-oas-media-single-example", success=False, name="9e9119", stack="OpenAPI leftover example + Java + TS", field="example", old="media example", new="examples map leftover only", fail_err="400: leftover media example after examples map leftover-only", plan="examples map leftover-only 400s leftover media example. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (examples map leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#example-object", fetch1_ok="Exclusive media example 400 leftover examples map.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch2_ok="example is a single value, leftover examples-map-only is not that.")),
    (p(slug="oas-query-explode-false-obj", domain="oas-query-explode-false-obj-vs-leftover-query-explode-obj", success=True, name="5975ba", stack="OpenAPI 3.1 explode + Go", field="explode", old="explode object leftover", new="query explode false", fail_err="400: leftover explode object leftover after query explode false-only", plan="query explode false-only 400s leftover explode object leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (query explode false vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch1_ok="explode false serializes objects as one param, leftover explode fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="Exclusive explode false 400 leftover explode obj."),
     p(slug="leftover-query-explode-obj", domain="leftover-query-explode-obj-vs-oas-query-explode-false-obj", success=False, name="5bc9aa", stack="OpenAPI leftover explode + Java + TS", field="explode", old="query explode false", new="explode object leftover only", fail_err="400: leftover query explode false after explode object leftover-only", plan="explode object leftover-only 400s leftover query explode false. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (explode object leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="Exclusive explode false 400 leftover explode obj.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch2_ok="explode false serializes objects as one param, leftover explode fails closed.")),
    (p(slug="oas-query-style-space-delim", domain="oas-query-style-space-delim-vs-leftover-query-space-csv", success=True, name="688776", stack="OpenAPI 3.1 style + Go", field="style", old="space csv leftover", new="spaceDelimited query", fail_err="400: leftover space csv leftover after spaceDelimited query-only", plan="spaceDelimited query-only 400s leftover space csv leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (spaceDelimited query vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch1_ok="spaceDelimited is not leftover comma-joined spaces.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="Exclusive spaceDelimited 400 leftover space csv."),
     p(slug="leftover-query-space-csv", domain="leftover-query-space-csv-vs-oas-query-style-space-delim", success=False, name="e95d74", stack="OpenAPI leftover style + Java + TS", field="style", old="spaceDelimited query", new="space csv leftover only", fail_err="400: leftover spaceDelimited query after space csv leftover-only", plan="space csv leftover-only 400s leftover spaceDelimited query. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (space csv leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="Exclusive spaceDelimited 400 leftover space csv.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch2_ok="spaceDelimited is not leftover comma-joined spaces.")),
    (p(slug="oas-info-terms-uri-https", domain="oas-info-terms-uri-https-vs-leftover-tos-plaintext", success=True, name="4fe3a5", stack="OpenAPI 3.1 termsOfService + Go", field="termsOfService", old="plaintext tos leftover", new="termsOfService https uri", fail_err="400: leftover plaintext tos leftover after termsOfService https uri-only", plan="termsOfService https uri-only 400s leftover plaintext tos leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (termsOfService https uri vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#info-object", fetch1_ok="termsOfService must be a URI, leftover plaintext fails closed.", fetch2="https://datatracker.ietf.org/doc/html/rfc3986", fetch2_ok="Exclusive tos uri 400 leftover plaintext."),
     p(slug="leftover-tos-plaintext", domain="leftover-tos-plaintext-vs-oas-info-terms-uri-https", success=False, name="641ace", stack="OpenAPI leftover termsOfService + Java + TS", field="termsOfService", old="termsOfService https uri", new="plaintext tos leftover only", fail_err="400: leftover termsOfService https uri after plaintext tos leftover-only", plan="plaintext tos leftover-only 400s leftover termsOfService https uri. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (plaintext tos leftover leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc3986", fetch1_ok="Exclusive tos uri 400 leftover plaintext.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#info-object", fetch2_ok="termsOfService must be a URI, leftover plaintext fails closed.")),
    (p(slug="oas-xml-attr-ns-uri", domain="oas-xml-attr-ns-uri-vs-leftover-xml-attr-bare", success=True, name="97c853", stack="OpenAPI 3.1 namespace + Go", field="namespace", old="bare xml attr leftover", new="xml attr namespace", fail_err="415: leftover bare xml attr leftover after xml attr namespace-only", plan="xml attr namespace-only 415s leftover bare xml attr leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (xml attr namespace vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#xml-object", fetch1_ok="xml.namespace on attributes is not leftover bare attrs.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive xml attr ns 415 leftover bare."),
     p(slug="leftover-xml-attr-bare", domain="leftover-xml-attr-bare-vs-oas-xml-attr-ns-uri", success=False, name="bc2f0b", stack="OpenAPI leftover namespace + Java + TS", field="namespace", old="xml attr namespace", new="bare xml attr leftover only", fail_err="415: leftover xml attr namespace after bare xml attr leftover-only", plan="bare xml attr leftover-only 415s leftover xml attr namespace. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (bare xml attr leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive xml attr ns 415 leftover bare.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#xml-object", fetch2_ok="xml.namespace on attributes is not leftover bare attrs.")),
    (p(slug="oas-schema-anyof-closed-set", domain="oas-schema-anyof-closed-set-vs-leftover-typeless-union", success=True, name="b7dbe1", stack="OpenAPI 3.1 anyOf + Go", field="anyOf", old="typeless union leftover", new="anyOf closed set", fail_err="400: leftover typeless union leftover after anyOf closed set-only", plan="anyOf closed set-only 400s leftover typeless union leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (anyOf closed set vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/combining#anyof", fetch1_ok="anyOf is a closed alternative set, leftover typeless union fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive anyOf 400 leftover typeless."),
     p(slug="leftover-typeless-union", domain="leftover-typeless-union-vs-oas-schema-anyof-closed-set", success=False, name="f14893", stack="OpenAPI leftover anyOf + Java + TS", field="anyOf", old="anyOf closed set", new="typeless union leftover only", fail_err="400: leftover anyOf closed set after typeless union leftover-only", plan="typeless union leftover-only 400s leftover anyOf closed set. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (typeless union leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive anyOf 400 leftover typeless.", fetch2="https://json-schema.org/understanding-json-schema/reference/combining#anyof", fetch2_ok="anyOf is a closed alternative set, leftover typeless union fails closed.")),
    (p(slug="oas-schema-allof-merge-req", domain="oas-schema-allof-merge-req-vs-leftover-partial-allof-req", success=True, name="c49b32", stack="OpenAPI 3.1 allOf + Go", field="allOf", old="partial allOf leftover", new="allOf merge required", fail_err="400: leftover partial allOf leftover after allOf merge required-only", plan="allOf merge required-only 400s leftover partial allOf leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (allOf merge required vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/combining#allof", fetch1_ok="allOf merges required, leftover partial allOf fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive allOf merge 400 leftover partial."),
     p(slug="leftover-partial-allof-req", domain="leftover-partial-allof-req-vs-oas-schema-allof-merge-req", success=False, name="140a64", stack="OpenAPI leftover allOf + Java + TS", field="allOf", old="allOf merge required", new="partial allOf leftover only", fail_err="400: leftover allOf merge required after partial allOf leftover-only", plan="partial allOf leftover-only 400s leftover allOf merge required. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (partial allOf leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive allOf merge 400 leftover partial.", fetch2="https://json-schema.org/understanding-json-schema/reference/combining#allof", fetch2_ok="allOf merges required, leftover partial allOf fails closed.")),
    (p(slug="oas-cb-components-reuse", domain="oas-cb-components-reuse-vs-leftover-inline-cb-only", success=True, name="982dc6", stack="OpenAPI 3.1 callbacks + Go", field="callbacks", old="inline callback leftover", new="components callbacks reuse", fail_err="400: leftover inline callback leftover after components callbacks reuse-only", plan="components callbacks reuse-only 400s leftover inline callback leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (components callbacks reuse vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#components-object", fetch1_ok="components.callbacks reuse Callback Objects, leftover inline-only is not that.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#callback-object", fetch2_ok="Exclusive components callbacks 400 leftover inline."),
     p(slug="leftover-inline-cb-only", domain="leftover-inline-cb-only-vs-oas-cb-components-reuse", success=False, name="caf695", stack="OpenAPI leftover callbacks + Java + TS", field="callbacks", old="components callbacks reuse", new="inline callback leftover only", fail_err="400: leftover components callbacks reuse after inline callback leftover-only", plan="inline callback leftover-only 400s leftover components callbacks reuse. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (inline callback leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#callback-object", fetch1_ok="Exclusive components callbacks 400 leftover inline.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#components-object", fetch2_ok="components.callbacks reuse Callback Objects, leftover inline-only is not that.")),
    (p(slug="oas-patch-json-merge-patch", domain="oas-patch-json-merge-patch-vs-leftover-put-for-patch", success=True, name="dc0ea9", stack="OpenAPI 3.1 patch + Go", field="patch", old="PUT as PATCH leftover", new="JSON merge PATCH", fail_err="400: leftover PUT as PATCH leftover after JSON merge PATCH-only", plan="JSON merge PATCH-only 400s leftover PUT as PATCH leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (JSON merge PATCH vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#path-item-object", fetch1_ok="PATCH is merge/patch, leftover PUT-as-PATCH fails closed.", fetch2="https://datatracker.ietf.org/doc/html/rfc7396", fetch2_ok="Exclusive merge PATCH 400 leftover PUT."),
     p(slug="leftover-put-for-patch", domain="leftover-put-for-patch-vs-oas-patch-json-merge-patch", success=False, name="016b81", stack="OpenAPI leftover patch + Java + TS", field="patch", old="JSON merge PATCH", new="PUT as PATCH leftover only", fail_err="400: leftover JSON merge PATCH after PUT as PATCH leftover-only", plan="PUT as PATCH leftover-only 400s leftover JSON merge PATCH. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (PUT as PATCH leftover leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc7396", fetch1_ok="Exclusive merge PATCH 400 leftover PUT.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#path-item-object", fetch2_ok="PATCH is merge/patch, leftover PUT-as-PATCH fails closed.")),
    (p(slug="oas-schema-ifthen-else", domain="oas-schema-ifthen-else-vs-leftover-oneof-conditional", success=True, name="a82f6e", stack="OpenAPI 3.1 if + Go", field="if", old="oneOf conditional leftover", new="if then else", fail_err="400: leftover oneOf conditional leftover after if then else-only", plan="if then else-only 400s leftover oneOf conditional leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (if then else vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/conditionals", fetch1_ok="if/then/else is not leftover oneOf-as-conditional.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive if/then/else 400 leftover oneOf."),
     p(slug="leftover-oneof-conditional", domain="leftover-oneof-conditional-vs-oas-schema-ifthen-else", success=False, name="35b499", stack="OpenAPI leftover if + Java + TS", field="if", old="if then else", new="oneOf conditional leftover only", fail_err="400: leftover if then else after oneOf conditional leftover-only", plan="oneOf conditional leftover-only 400s leftover if then else. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (oneOf conditional leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive if/then/else 400 leftover oneOf.", fetch2="https://json-schema.org/understanding-json-schema/reference/conditionals", fetch2_ok="if/then/else is not leftover oneOf-as-conditional.")),
    (p(slug="oas-object-max-properties", domain="oas-object-max-properties-vs-leftover-object-key-unbounded", success=True, name="9dcebd", stack="OpenAPI 3.1 maxProperties + Go", field="maxProperties", old="unbounded keys leftover", new="maxProperties", fail_err="400: leftover unbounded keys leftover after maxProperties-only", plan="maxProperties-only 400s leftover unbounded keys leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (maxProperties vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/object#maxproperties", fetch1_ok="maxProperties bounds object keys, leftover unbounded fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive maxProperties 400 leftover unbounded keys."),
     p(slug="leftover-object-key-unbounded", domain="leftover-object-key-unbounded-vs-oas-object-max-properties", success=False, name="f669ed", stack="OpenAPI leftover maxProperties + Java + TS", field="maxProperties", old="maxProperties", new="unbounded keys leftover only", fail_err="400: leftover maxProperties after unbounded keys leftover-only", plan="unbounded keys leftover-only 400s leftover maxProperties. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (unbounded keys leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive maxProperties 400 leftover unbounded keys.", fetch2="https://json-schema.org/understanding-json-schema/reference/object#maxproperties", fetch2_ok="maxProperties bounds object keys, leftover unbounded fails closed.")),
    (p(slug="oas-object-min-properties", domain="oas-object-min-properties-vs-leftover-zero-key-object", success=True, name="dc1206", stack="OpenAPI 3.1 minProperties + Go", field="minProperties", old="zero key leftover", new="minProperties", fail_err="400: leftover zero key leftover after minProperties-only", plan="minProperties-only 400s leftover zero key leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (minProperties vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/object#minproperties", fetch1_ok="minProperties rejects empty objects, leftover zero-key fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive minProperties 400 leftover empty object."),
     p(slug="leftover-zero-key-object", domain="leftover-zero-key-object-vs-oas-object-min-properties", success=False, name="c8a8ac", stack="OpenAPI leftover minProperties + Java + TS", field="minProperties", old="minProperties", new="zero key leftover only", fail_err="400: leftover minProperties after zero key leftover-only", plan="zero key leftover-only 400s leftover minProperties. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (zero key leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive minProperties 400 leftover empty object.", fetch2="https://json-schema.org/understanding-json-schema/reference/object#minproperties", fetch2_ok="minProperties rejects empty objects, leftover zero-key fails closed.")),
    (p(slug="oas-object-property-names", domain="oas-object-property-names-vs-leftover-any-object-key", success=True, name="05c0a6", stack="OpenAPI 3.1 propertyNames + Go", field="propertyNames", old="any key leftover", new="propertyNames schema", fail_err="400: leftover any key leftover after propertyNames schema-only", plan="propertyNames schema-only 400s leftover any key leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (propertyNames schema vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/object#propertynames", fetch1_ok="propertyNames constrains keys, leftover any-key fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive propertyNames 400 leftover any key."),
     p(slug="leftover-any-object-key", domain="leftover-any-object-key-vs-oas-object-property-names", success=False, name="0b2053", stack="OpenAPI leftover propertyNames + Java + TS", field="propertyNames", old="propertyNames schema", new="any key leftover only", fail_err="400: leftover propertyNames schema after any key leftover-only", plan="any key leftover-only 400s leftover propertyNames schema. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (any key leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive propertyNames 400 leftover any key.", fetch2="https://json-schema.org/understanding-json-schema/reference/object#propertynames", fetch2_ok="propertyNames constrains keys, leftover any-key fails closed.")),
    (p(slug="oas-format-uuid-rfc4122", domain="oas-format-uuid-rfc4122-vs-leftover-guid-braces", success=True, name="0d0207", stack="OpenAPI 3.1 format + Go", field="format", old="braced guid leftover", new="format uuid rfc4122", fail_err="400: leftover braced guid leftover after format uuid rfc4122-only", plan="format uuid rfc4122-only 400s leftover braced guid leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (format uuid rfc4122 vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/string#uuid", fetch1_ok="format=uuid is RFC4122, leftover braced GUIDs fail closed.", fetch2="https://datatracker.ietf.org/doc/html/rfc4122", fetch2_ok="Exclusive uuid 400 leftover braced guid."),
     p(slug="leftover-guid-braces", domain="leftover-guid-braces-vs-oas-format-uuid-rfc4122", success=False, name="65fbcb", stack="OpenAPI leftover format + Java + TS", field="format", old="format uuid rfc4122", new="braced guid leftover only", fail_err="400: leftover format uuid rfc4122 after braced guid leftover-only", plan="braced guid leftover-only 400s leftover format uuid rfc4122. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (braced guid leftover leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc4122", fetch1_ok="Exclusive uuid 400 leftover braced guid.", fetch2="https://json-schema.org/understanding-json-schema/reference/string#uuid", fetch2_ok="format=uuid is RFC4122, leftover braced GUIDs fail closed.")),
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
    print(json.dumps({"round": round_n, "idx": idx, "ids": [e1["id"], e2["id"]], "catalog": "r4246"}))


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
