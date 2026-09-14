#!/usr/bin/env python3
"""Unique OpenAPI-drift ACM catalog r4406. Fast slug load."""
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
    (p(slug="oas-schema-read-only-flag", domain="oas-schema-read-only-flag-vs-leftover-writable-identifier", success=True, name="760e90", stack="OpenAPI 3.1 readOnly + Go", field="readOnly", old="writable id leftover", new="readOnly true", fail_err="400: leftover writable id leftover after readOnly true-only", plan="readOnly true-only 400s leftover writable id leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (readOnly true vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="readOnly identifiers cannot be leftover writable.", fetch2="https://json-schema.org/understanding-json-schema/reference/object", fetch2_ok="Exclusive readOnly 400 leftover writable id."),
     p(slug="leftover-writable-identifier", domain="leftover-writable-identifier-vs-oas-schema-read-only-flag", success=False, name="40466c", stack="OpenAPI leftover readOnly + Java + TS", field="readOnly", old="readOnly true", new="writable id leftover only", fail_err="400: leftover readOnly true after writable id leftover-only", plan="writable id leftover-only 400s leftover readOnly true. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (writable id leftover leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/object", fetch1_ok="Exclusive readOnly 400 leftover writable id.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="readOnly identifiers cannot be leftover writable.")),
    (p(slug="oas-schema-write-only-flag", domain="oas-schema-write-only-flag-vs-leftover-readable-secret-field", success=True, name="24937e", stack="OpenAPI 3.1 writeOnly + Go", field="writeOnly", old="readable secret leftover", new="writeOnly true", fail_err="400: leftover readable secret leftover after writeOnly true-only", plan="writeOnly true-only 400s leftover readable secret leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (writeOnly true vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="writeOnly secrets cannot be leftover readable.", fetch2="https://json-schema.org/understanding-json-schema/reference/object", fetch2_ok="Exclusive writeOnly 400 leftover readable secret."),
     p(slug="leftover-readable-secret-field", domain="leftover-readable-secret-field-vs-oas-schema-write-only-flag", success=False, name="f15c63", stack="OpenAPI leftover writeOnly + Java + TS", field="writeOnly", old="writeOnly true", new="readable secret leftover only", fail_err="400: leftover writeOnly true after readable secret leftover-only", plan="readable secret leftover-only 400s leftover writeOnly true. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (readable secret leftover leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/object", fetch1_ok="Exclusive writeOnly 400 leftover readable secret.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="writeOnly secrets cannot be leftover readable.")),
    (p(slug="oas-format-binary-octet", domain="oas-format-binary-octet-vs-leftover-utf8-as-binary", success=True, name="7ec7df", stack="OpenAPI 3.1 format + Go", field="format", old="utf8 as binary leftover", new="format binary octet", fail_err="415: leftover utf8 as binary leftover after format binary octet-only", plan="format binary octet-only 415s leftover utf8 as binary leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (format binary octet vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="format=binary is octets, leftover utf8 fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive binary 415 leftover utf8."),
     p(slug="leftover-utf8-as-binary", domain="leftover-utf8-as-binary-vs-oas-format-binary-octet", success=False, name="bce873", stack="OpenAPI leftover format + Java + TS", field="format", old="format binary octet", new="utf8 as binary leftover only", fail_err="415: leftover format binary octet after utf8 as binary leftover-only", plan="utf8 as binary leftover-only 415s leftover format binary octet. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (utf8 as binary leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive binary 415 leftover utf8.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="format=binary is octets, leftover utf8 fails closed.")),
    (p(slug="oas-format-int32-range", domain="oas-format-int32-range-vs-leftover-int32-overflow", success=True, name="40b45f", stack="OpenAPI 3.1 format + Go", field="format", old="int32 overflow leftover", new="format int32 range", fail_err="400: leftover int32 overflow leftover after format int32 range-only", plan="format int32 range-only 400s leftover int32 overflow leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (format int32 range vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="int32 must fit 32-bit, leftover overflow fails closed.", fetch2="https://json-schema.org/understanding-json-schema/reference/numeric", fetch2_ok="Exclusive int32 range 400 leftover overflow."),
     p(slug="leftover-int32-overflow", domain="leftover-int32-overflow-vs-oas-format-int32-range", success=False, name="b482bd", stack="OpenAPI leftover format + Java + TS", field="format", old="format int32 range", new="int32 overflow leftover only", fail_err="400: leftover format int32 range after int32 overflow leftover-only", plan="int32 overflow leftover-only 400s leftover format int32 range. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (int32 overflow leftover leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/numeric", fetch1_ok="Exclusive int32 range 400 leftover overflow.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="int32 must fit 32-bit, leftover overflow fails closed.")),
    (p(slug="oas-format-int64-string", domain="oas-format-int64-string-vs-leftover-int64-as-js-number", success=True, name="949991", stack="OpenAPI 3.1 format + Go", field="format", old="js number int64 leftover", new="int64 as string", fail_err="400: leftover js number int64 leftover after int64 as string-only", plan="int64 as string-only 400s leftover js number int64 leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (int64 as string vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="int64 over 2^53 is a string, leftover JS number fails closed.", fetch2="https://json-schema.org/understanding-json-schema/reference/numeric", fetch2_ok="Exclusive int64 string 400 leftover js number."),
     p(slug="leftover-int64-as-js-number", domain="leftover-int64-as-js-number-vs-oas-format-int64-string", success=False, name="d1f83b", stack="OpenAPI leftover format + Java + TS", field="format", old="int64 as string", new="js number int64 leftover only", fail_err="400: leftover int64 as string after js number int64 leftover-only", plan="js number int64 leftover-only 400s leftover int64 as string. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (js number int64 leftover leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/numeric", fetch1_ok="Exclusive int64 string 400 leftover js number.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="int64 over 2^53 is a string, leftover JS number fails closed.")),
    (p(slug="oas-param-content-json-header", domain="oas-param-content-json-header-vs-leftover-header-as-string-schema", success=True, name="b165d9", stack="OpenAPI 3.1 content + Go", field="content", old="string header leftover", new="header content json", fail_err="400: leftover string header leftover after header content json-only", plan="header content json-only 400s leftover string header leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (header content json vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="header content json is not leftover string schema headers.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch2_ok="Exclusive header json content 400 leftover string."),
     p(slug="leftover-header-as-string-schema", domain="leftover-header-as-string-schema-vs-oas-param-content-json-header", success=False, name="dd2e21", stack="OpenAPI leftover content + Java + TS", field="content", old="header content json", new="string header leftover only", fail_err="400: leftover header content json after string header leftover-only", plan="string header leftover-only 400s leftover header content json. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (string header leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch1_ok="Exclusive header json content 400 leftover string.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="header content json is not leftover string schema headers.")),
    (p(slug="oas-components-examples-value", domain="oas-components-examples-value-vs-leftover-externalvalue-only", success=True, name="fae1da", stack="OpenAPI 3.1 value + Go", field="value", old="externalValue leftover", new="example value", fail_err="400: leftover externalValue leftover after example value-only", plan="example value-only 400s leftover externalValue leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (example value vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#example-object", fetch1_ok="example.value is not leftover externalValue-only.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#components-object", fetch2_ok="Exclusive example value 400 leftover externalValue."),
     p(slug="leftover-externalvalue-only", domain="leftover-externalvalue-only-vs-oas-components-examples-value", success=False, name="21a07a", stack="OpenAPI leftover value + Java + TS", field="value", old="example value", new="externalValue leftover only", fail_err="400: leftover example value after externalValue leftover-only", plan="externalValue leftover-only 400s leftover example value. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (externalValue leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#components-object", fetch1_ok="Exclusive example value 400 leftover externalValue.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#example-object", fetch2_ok="example.value is not leftover externalValue-only.")),
    (p(slug="oas-security-schemes-ref", domain="oas-security-schemes-ref-vs-leftover-inline-security-scheme", success=True, name="17f3b9", stack="OpenAPI 3.1 securitySchemes + Go", field="securitySchemes", old="inline scheme leftover", new="components securitySchemes ref", fail_err="401: leftover inline scheme leftover after components securitySchemes ref-only", plan="components securitySchemes ref-only 401s leftover inline scheme leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (components securitySchemes ref vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#components-object", fetch1_ok="components.securitySchemes reuse, leftover inline-only is not that.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch2_ok="Exclusive securitySchemes 401 leftover inline."),
     p(slug="leftover-inline-security-scheme", domain="leftover-inline-security-scheme-vs-oas-security-schemes-ref", success=False, name="817a5c", stack="OpenAPI leftover securitySchemes + Java + TS", field="securitySchemes", old="components securitySchemes ref", new="inline scheme leftover only", fail_err="401: leftover components securitySchemes ref after inline scheme leftover-only", plan="inline scheme leftover-only 401s leftover components securitySchemes ref. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (inline scheme leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch1_ok="Exclusive securitySchemes 401 leftover inline.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#components-object", fetch2_ok="components.securitySchemes reuse, leftover inline-only is not that.")),
    (p(slug="oas-allof-with-discriminator", domain="oas-allof-with-discriminator-vs-leftover-allof-untyped-merge", success=True, name="933c3b", stack="OpenAPI 3.1 discriminator + Go", field="discriminator", old="untyped allOf leftover", new="allOf discriminator", fail_err="400: leftover untyped allOf leftover after allOf discriminator-only", plan="allOf discriminator-only 400s leftover untyped allOf leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (allOf discriminator vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#discriminator-object", fetch1_ok="allOf plus discriminator is not leftover untyped merge.", fetch2="https://json-schema.org/understanding-json-schema/reference/combining#allof", fetch2_ok="Exclusive allOf disc 400 leftover untyped."),
     p(slug="leftover-allof-untyped-merge", domain="leftover-allof-untyped-merge-vs-oas-allof-with-discriminator", success=False, name="f93574", stack="OpenAPI leftover discriminator + Java + TS", field="discriminator", old="allOf discriminator", new="untyped allOf leftover only", fail_err="400: leftover allOf discriminator after untyped allOf leftover-only", plan="untyped allOf leftover-only 400s leftover allOf discriminator. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (untyped allOf leftover leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/combining#allof", fetch1_ok="Exclusive allOf disc 400 leftover untyped.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#discriminator-object", fetch2_ok="allOf plus discriminator is not leftover untyped merge.")),
    (p(slug="oas-anyof-null-member", domain="oas-anyof-null-member-vs-leftover-anyof-null-only", success=True, name="dfb0bf", stack="OpenAPI 3.1 anyOf + Go", field="anyOf", old="anyOf null only leftover", new="anyOf includes null", fail_err="400: leftover anyOf null only leftover after anyOf includes null-only", plan="anyOf includes null-only 400s leftover anyOf null only leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (anyOf includes null vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/combining#anyof", fetch1_ok="anyOf may include null as a member, leftover null-only fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive anyOf null member 400 leftover null only."),
     p(slug="leftover-anyof-null-only", domain="leftover-anyof-null-only-vs-oas-anyof-null-member", success=False, name="902cb2", stack="OpenAPI leftover anyOf + Java + TS", field="anyOf", old="anyOf includes null", new="anyOf null only leftover only", fail_err="400: leftover anyOf includes null after anyOf null only leftover-only", plan="anyOf null only leftover-only 400s leftover anyOf includes null. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (anyOf null only leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive anyOf null member 400 leftover null only.", fetch2="https://json-schema.org/understanding-json-schema/reference/combining#anyof", fetch2_ok="anyOf may include null as a member, leftover null-only fails closed.")),
    (p(slug="oas-contains-min-one", domain="oas-contains-min-one-vs-leftover-contains-may-miss", success=True, name="9bdbbf", stack="OpenAPI 3.1 contains + Go", field="contains", old="contains may miss leftover", new="contains min one", fail_err="400: leftover contains may miss leftover after contains min one-only", plan="contains min one-only 400s leftover contains may miss leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (contains min one vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/array#contains", fetch1_ok="contains requires at least one match, leftover miss fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive contains min one 400 leftover miss."),
     p(slug="leftover-contains-may-miss", domain="leftover-contains-may-miss-vs-oas-contains-min-one", success=False, name="a9b65d", stack="OpenAPI leftover contains + Java + TS", field="contains", old="contains min one", new="contains may miss leftover only", fail_err="400: leftover contains min one after contains may miss leftover-only", plan="contains may miss leftover-only 400s leftover contains min one. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (contains may miss leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive contains min one 400 leftover miss.", fetch2="https://json-schema.org/understanding-json-schema/reference/array#contains", fetch2_ok="contains requires at least one match, leftover miss fails closed.")),
    (p(slug="oas-unique-contains-items", domain="oas-unique-contains-items-vs-leftover-contains-duplicate-ok", success=True, name="3de4e9", stack="OpenAPI 3.1 uniqueItems + Go", field="uniqueItems", old="contains dups leftover", new="unique contains items", fail_err="400: leftover contains dups leftover after unique contains items-only", plan="unique contains items-only 400s leftover contains dups leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (unique contains items vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/array#uniqueitems", fetch1_ok="contains matches still honor uniqueItems, leftover dups fail closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive unique contains 400 leftover dups."),
     p(slug="leftover-contains-duplicate-ok", domain="leftover-contains-duplicate-ok-vs-oas-unique-contains-items", success=False, name="9d32fe", stack="OpenAPI leftover uniqueItems + Java + TS", field="uniqueItems", old="unique contains items", new="contains dups leftover only", fail_err="400: leftover unique contains items after contains dups leftover-only", plan="contains dups leftover-only 400s leftover unique contains items. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (contains dups leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive unique contains 400 leftover dups.", fetch2="https://json-schema.org/understanding-json-schema/reference/array#uniqueitems", fetch2_ok="contains matches still honor uniqueItems, leftover dups fail closed.")),
    (p(slug="oas-dependent-required-xor", domain="oas-dependent-required-xor-vs-leftover-independent-required", success=True, name="b055a3", stack="OpenAPI 3.1 dependentRequired + Go", field="dependentRequired", old="independent required leftover", new="dependentRequired xor", fail_err="400: leftover independent required leftover after dependentRequired xor-only", plan="dependentRequired xor-only 400s leftover independent required leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (dependentRequired xor vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/object#dependentrequired", fetch1_ok="dependentRequired xor pairing is not leftover independent required.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive xor required 400 leftover independent."),
     p(slug="leftover-independent-required", domain="leftover-independent-required-vs-oas-dependent-required-xor", success=False, name="a725a4", stack="OpenAPI leftover dependentRequired + Java + TS", field="dependentRequired", old="dependentRequired xor", new="independent required leftover only", fail_err="400: leftover dependentRequired xor after independent required leftover-only", plan="independent required leftover-only 400s leftover dependentRequired xor. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (independent required leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive xor required 400 leftover independent.", fetch2="https://json-schema.org/understanding-json-schema/reference/object#dependentrequired", fetch2_ok="dependentRequired xor pairing is not leftover independent required.")),
    (p(slug="oas-min-properties-one", domain="oas-min-properties-one-vs-leftover-empty-map-ok", success=True, name="c9aaa4", stack="OpenAPI 3.1 minProperties + Go", field="minProperties", old="empty map leftover", new="minProperties 1", fail_err="400: leftover empty map leftover after minProperties 1-only", plan="minProperties 1-only 400s leftover empty map leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (minProperties 1 vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/object#minproperties", fetch1_ok="minProperties 1 rejects empty maps, leftover empty-ok fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive minProperties 1 400 leftover empty map."),
     p(slug="leftover-empty-map-ok", domain="leftover-empty-map-ok-vs-oas-min-properties-one", success=False, name="a92587", stack="OpenAPI leftover minProperties + Java + TS", field="minProperties", old="minProperties 1", new="empty map leftover only", fail_err="400: leftover minProperties 1 after empty map leftover-only", plan="empty map leftover-only 400s leftover minProperties 1. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (empty map leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive minProperties 1 400 leftover empty map.", fetch2="https://json-schema.org/understanding-json-schema/reference/object#minproperties", fetch2_ok="minProperties 1 rejects empty maps, leftover empty-ok fails closed.")),
    (p(slug="oas-max-properties-one", domain="oas-max-properties-one-vs-leftover-multi-key-map", success=True, name="562694", stack="OpenAPI 3.1 maxProperties + Go", field="maxProperties", old="multi key leftover", new="maxProperties 1", fail_err="400: leftover multi key leftover after maxProperties 1-only", plan="maxProperties 1-only 400s leftover multi key leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (maxProperties 1 vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/object#maxproperties", fetch1_ok="maxProperties 1 rejects multi-key maps, leftover multi fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive maxProperties 1 400 leftover multi key."),
     p(slug="leftover-multi-key-map", domain="leftover-multi-key-map-vs-oas-max-properties-one", success=False, name="c3c048", stack="OpenAPI leftover maxProperties + Java + TS", field="maxProperties", old="maxProperties 1", new="multi key leftover only", fail_err="400: leftover maxProperties 1 after multi key leftover-only", plan="multi key leftover-only 400s leftover maxProperties 1. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (multi key leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive maxProperties 1 400 leftover multi key.", fetch2="https://json-schema.org/understanding-json-schema/reference/object#maxproperties", fetch2_ok="maxProperties 1 rejects multi-key maps, leftover multi fails closed.")),
    (p(slug="oas-items-schema-required", domain="oas-items-schema-required-vs-leftover-untyped-list-elem", success=True, name="513f38", stack="OpenAPI 3.1 items + Go", field="items", old="untyped list leftover", new="items schema required", fail_err="400: leftover untyped list leftover after items schema required-only", plan="items schema required-only 400s leftover untyped list leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (items schema required vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/array#items", fetch1_ok="items schema is required for lists, leftover untyped fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive items schema 400 leftover untyped list."),
     p(slug="leftover-untyped-list-elem", domain="leftover-untyped-list-elem-vs-oas-items-schema-required", success=False, name="43cf0a", stack="OpenAPI leftover items + Java + TS", field="items", old="items schema required", new="untyped list leftover only", fail_err="400: leftover items schema required after untyped list leftover-only", plan="untyped list leftover-only 400s leftover items schema required. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (untyped list leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive items schema 400 leftover untyped list.", fetch2="https://json-schema.org/understanding-json-schema/reference/array#items", fetch2_ok="items schema is required for lists, leftover untyped fails closed.")),
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
    print(json.dumps({"round": round_n, "idx": idx, "ids": [e1["id"], e2["id"]], "catalog": "r4406"}))


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
