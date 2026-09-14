#!/usr/bin/env python3
"""Unique OpenAPI-drift ACM catalog r4598. Fast slug load."""
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
    (p(slug="oas-webhooks-plus-callbacks", domain="oas-webhooks-plus-callbacks-vs-leftover-webhook-as-callback", success=True, name="3291b8", stack="OpenAPI 3.1 webhooks + Go", field="webhooks", old="webhook as callback leftover", new="webhooks plus callbacks", fail_err="400: leftover webhook as callback leftover after webhooks plus callbacks-only", plan="webhooks plus callbacks-only 400s leftover webhook as callback leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (webhooks plus callbacks vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#oasWebhooks", fetch1_ok="webhooks are not leftover callbacks.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#callback-object", fetch2_ok="Exclusive webhooks 400 leftover callbacks."),
     p(slug="leftover-webhook-as-callback", domain="leftover-webhook-as-callback-vs-oas-webhooks-plus-callbacks", success=False, name="a774b3", stack="OpenAPI leftover webhooks + Java + TS", field="webhooks", old="webhooks plus callbacks", new="webhook as callback leftover only", fail_err="400: leftover webhooks plus callbacks after webhook as callback leftover-only", plan="webhook as callback leftover-only 400s leftover webhooks plus callbacks. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (webhook as callback leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#callback-object", fetch1_ok="Exclusive webhooks 400 leftover callbacks.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#oasWebhooks", fetch2_ok="webhooks are not leftover callbacks.")),
    (p(slug="oas-json-schema-dialect-202012", domain="oas-json-schema-dialect-202012-vs-leftover-dialect-draft201909", success=True, name="48a2dc", stack="OpenAPI 3.1 jsonSchemaDialect + Go", field="jsonSchemaDialect", old="2019-09 leftover", new="dialect 2020-12", fail_err="400: leftover 2019-09 leftover after dialect 2020-12-only", plan="dialect 2020-12-only 400s leftover 2019-09 leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (dialect 2020-12 vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#openapi-object", fetch1_ok="default dialect is 2020-12, leftover 2019-09 fails closed.", fetch2="https://json-schema.org/understanding-json-schema/reference/schema", fetch2_ok="Exclusive 2020-12 400 leftover 2019-09."),
     p(slug="leftover-dialect-draft201909", domain="leftover-dialect-draft201909-vs-oas-json-schema-dialect-202012", success=False, name="bb2892", stack="OpenAPI leftover jsonSchemaDialect + Java + TS", field="jsonSchemaDialect", old="dialect 2020-12", new="2019-09 leftover only", fail_err="400: leftover dialect 2020-12 after 2019-09 leftover-only", plan="2019-09 leftover-only 400s leftover dialect 2020-12. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (2019-09 leftover leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/schema", fetch1_ok="Exclusive 2020-12 400 leftover 2019-09.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#openapi-object", fetch2_ok="default dialect is 2020-12, leftover 2019-09 fails closed.")),
    (p(slug="oas-property-names-maxlength", domain="oas-property-names-maxlength-vs-leftover-unbounded-key-length", success=True, name="7fae84", stack="OpenAPI 3.1 propertyNames + Go", field="propertyNames", old="unbounded key leftover", new="propertyNames maxLength", fail_err="400: leftover unbounded key leftover after propertyNames maxLength-only", plan="propertyNames maxLength-only 400s leftover unbounded key leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (propertyNames maxLength vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/object#propertynames", fetch1_ok="propertyNames.maxLength bounds keys, leftover unbounded fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive key maxLength 400 leftover unbounded."),
     p(slug="leftover-unbounded-key-length", domain="leftover-unbounded-key-length-vs-oas-property-names-maxlength", success=False, name="059c2c", stack="OpenAPI leftover propertyNames + Java + TS", field="propertyNames", old="propertyNames maxLength", new="unbounded key leftover only", fail_err="400: leftover propertyNames maxLength after unbounded key leftover-only", plan="unbounded key leftover-only 400s leftover propertyNames maxLength. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (unbounded key leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive key maxLength 400 leftover unbounded.", fetch2="https://json-schema.org/understanding-json-schema/reference/object#propertynames", fetch2_ok="propertyNames.maxLength bounds keys, leftover unbounded fails closed.")),
    (p(slug="oas-pattern-properties-closed", domain="oas-pattern-properties-closed-vs-leftover-pattern-plus-additional", success=True, name="b28a85", stack="OpenAPI 3.1 patternProperties + Go", field="patternProperties", old="pattern plus additional leftover", new="patternProperties closed", fail_err="400: leftover pattern plus additional leftover after patternProperties closed-only", plan="patternProperties closed-only 400s leftover pattern plus additional leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (patternProperties closed vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/object#patternproperties", fetch1_ok="closed patternProperties forbids leftover additional.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive closed pattern 400 leftover additional."),
     p(slug="leftover-pattern-plus-additional", domain="leftover-pattern-plus-additional-vs-oas-pattern-properties-closed", success=False, name="1a2c62", stack="OpenAPI leftover patternProperties + Java + TS", field="patternProperties", old="patternProperties closed", new="pattern plus additional leftover only", fail_err="400: leftover patternProperties closed after pattern plus additional leftover-only", plan="pattern plus additional leftover-only 400s leftover patternProperties closed. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (pattern plus additional leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive closed pattern 400 leftover additional.", fetch2="https://json-schema.org/understanding-json-schema/reference/object#patternproperties", fetch2_ok="closed patternProperties forbids leftover additional.")),
    (p(slug="oas-if-required-then-schema", domain="oas-if-required-then-schema-vs-leftover-if-without-then", success=True, name="1a0453", stack="OpenAPI 3.1 then + Go", field="then", old="if without then leftover", new="if requires then", fail_err="400: leftover if without then leftover after if requires then-only", plan="if requires then-only 400s leftover if without then leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (if requires then vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/conditionals", fetch1_ok="if requires then, leftover if-only fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive if+then 400 leftover if only."),
     p(slug="leftover-if-without-then", domain="leftover-if-without-then-vs-oas-if-required-then-schema", success=False, name="96b401", stack="OpenAPI leftover then + Java + TS", field="then", old="if requires then", new="if without then leftover only", fail_err="400: leftover if requires then after if without then leftover-only", plan="if without then leftover-only 400s leftover if requires then. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (if without then leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive if+then 400 leftover if only.", fetch2="https://json-schema.org/understanding-json-schema/reference/conditionals", fetch2_ok="if requires then, leftover if-only fails closed.")),
    (p(slug="oas-not-type-object", domain="oas-not-type-object-vs-leftover-not-as-enum-ban", success=True, name="3e056a", stack="OpenAPI 3.1 not + Go", field="not", old="not as enum leftover", new="not type object", fail_err="400: leftover not as enum leftover after not type object-only", plan="not type object-only 400s leftover not as enum leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (not type object vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/combining#not", fetch1_ok="not:{type:object} is not leftover enum bans.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive not type 400 leftover enum."),
     p(slug="leftover-not-as-enum-ban", domain="leftover-not-as-enum-ban-vs-oas-not-type-object", success=False, name="42cbdb", stack="OpenAPI leftover not + Java + TS", field="not", old="not type object", new="not as enum leftover only", fail_err="400: leftover not type object after not as enum leftover-only", plan="not as enum leftover-only 400s leftover not type object. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (not as enum leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive not type 400 leftover enum.", fetch2="https://json-schema.org/understanding-json-schema/reference/combining#not", fetch2_ok="not:{type:object} is not leftover enum bans.")),
    (p(slug="oas-oneOf-const-mapping", domain="oas-oneOf-const-mapping-vs-leftover-oneof-unmapped-const", success=True, name="6fa034", stack="OpenAPI 3.1 oneOf + Go", field="oneOf", old="unmapped const leftover", new="oneOf const mapping", fail_err="400: leftover unmapped const leftover after oneOf const mapping-only", plan="oneOf const mapping-only 400s leftover unmapped const leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (oneOf const mapping vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/combining#oneof", fetch1_ok="oneOf consts must map, leftover unmapped fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#discriminator-object", fetch2_ok="Exclusive const mapping 400 leftover unmapped."),
     p(slug="leftover-oneof-unmapped-const", domain="leftover-oneof-unmapped-const-vs-oas-oneOf-const-mapping", success=False, name="3709ff", stack="OpenAPI leftover oneOf + Java + TS", field="oneOf", old="oneOf const mapping", new="unmapped const leftover only", fail_err="400: leftover oneOf const mapping after unmapped const leftover-only", plan="unmapped const leftover-only 400s leftover oneOf const mapping. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (unmapped const leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#discriminator-object", fetch1_ok="Exclusive const mapping 400 leftover unmapped.", fetch2="https://json-schema.org/understanding-json-schema/reference/combining#oneof", fetch2_ok="oneOf consts must map, leftover unmapped fails closed.")),
    (p(slug="oas-allOf-unevaluated-false", domain="oas-allOf-unevaluated-false-vs-leftover-allof-open-merge", success=True, name="2834ea", stack="OpenAPI 3.1 unevaluatedProperties + Go", field="unevaluatedProperties", old="open allOf leftover", new="allOf unevaluated false", fail_err="400: leftover open allOf leftover after allOf unevaluated false-only", plan="allOf unevaluated false-only 400s leftover open allOf leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (allOf unevaluated false vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/combining#allof", fetch1_ok="allOf plus unevaluatedProperties false closes leftover open merges.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive closed allOf 400 leftover open."),
     p(slug="leftover-allof-open-merge", domain="leftover-allof-open-merge-vs-oas-allOf-unevaluated-false", success=False, name="af4ec3", stack="OpenAPI leftover unevaluatedProperties + Java + TS", field="unevaluatedProperties", old="allOf unevaluated false", new="open allOf leftover only", fail_err="400: leftover allOf unevaluated false after open allOf leftover-only", plan="open allOf leftover-only 400s leftover allOf unevaluated false. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (open allOf leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive closed allOf 400 leftover open.", fetch2="https://json-schema.org/understanding-json-schema/reference/combining#allof", fetch2_ok="allOf plus unevaluatedProperties false closes leftover open merges.")),
    (p(slug="oas-anyOf-unevaluated-false", domain="oas-anyOf-unevaluated-false-vs-leftover-anyof-open-merge", success=True, name="dc9c9f", stack="OpenAPI 3.1 unevaluatedProperties + Go", field="unevaluatedProperties", old="open anyOf leftover", new="anyOf unevaluated false", fail_err="400: leftover open anyOf leftover after anyOf unevaluated false-only", plan="anyOf unevaluated false-only 400s leftover open anyOf leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (anyOf unevaluated false vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/combining#anyof", fetch1_ok="anyOf plus unevaluatedProperties false closes leftover open merges.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive closed anyOf 400 leftover open."),
     p(slug="leftover-anyof-open-merge", domain="leftover-anyof-open-merge-vs-oas-anyOf-unevaluated-false", success=False, name="bf30bc", stack="OpenAPI leftover unevaluatedProperties + Java + TS", field="unevaluatedProperties", old="anyOf unevaluated false", new="open anyOf leftover only", fail_err="400: leftover anyOf unevaluated false after open anyOf leftover-only", plan="open anyOf leftover-only 400s leftover anyOf unevaluated false. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (open anyOf leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive closed anyOf 400 leftover open.", fetch2="https://json-schema.org/understanding-json-schema/reference/combining#anyof", fetch2_ok="anyOf plus unevaluatedProperties false closes leftover open merges.")),
    (p(slug="oas-prefixitems-unevaluated", domain="oas-prefixitems-unevaluated-vs-leftover-tuple-open-tail-items", success=True, name="e5e018", stack="OpenAPI 3.1 unevaluatedItems + Go", field="unevaluatedItems", old="open tuple leftover", new="prefixItems unevaluatedItems", fail_err="400: leftover open tuple leftover after prefixItems unevaluatedItems-only", plan="prefixItems unevaluatedItems-only 400s leftover open tuple leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (prefixItems unevaluatedItems vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/array#unevaluateditems", fetch1_ok="prefixItems plus unevaluatedItems closes leftover open tails.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive closed tuple 400 leftover open tail."),
     p(slug="leftover-tuple-open-tail-items", domain="leftover-tuple-open-tail-items-vs-oas-prefixitems-unevaluated", success=False, name="3738d4", stack="OpenAPI leftover unevaluatedItems + Java + TS", field="unevaluatedItems", old="prefixItems unevaluatedItems", new="open tuple leftover only", fail_err="400: leftover prefixItems unevaluatedItems after open tuple leftover-only", plan="open tuple leftover-only 400s leftover prefixItems unevaluatedItems. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (open tuple leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive closed tuple 400 leftover open tail.", fetch2="https://json-schema.org/understanding-json-schema/reference/array#unevaluateditems", fetch2_ok="prefixItems plus unevaluatedItems closes leftover open tails.")),
    (p(slug="oas-exclusive-min-with-minimum", domain="oas-exclusive-min-with-minimum-vs-leftover-both-min-keywords", success=True, name="5174f9", stack="OpenAPI 3.1 minimum + Go", field="minimum", old="both min leftover", new="exclusiveMinimum without minimum", fail_err="400: leftover both min leftover after exclusiveMinimum without minimum-only", plan="exclusiveMinimum without minimum-only 400s leftover both min leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (exclusiveMinimum without minimum vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/numeric#exclusiveminimum", fetch1_ok="Do not pair leftover minimum with exclusiveMinimum.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive exclusiveMinimum 400 leftover both."),
     p(slug="leftover-both-min-keywords", domain="leftover-both-min-keywords-vs-oas-exclusive-min-with-minimum", success=False, name="588c77", stack="OpenAPI leftover minimum + Java + TS", field="minimum", old="exclusiveMinimum without minimum", new="both min leftover only", fail_err="400: leftover exclusiveMinimum without minimum after both min leftover-only", plan="both min leftover-only 400s leftover exclusiveMinimum without minimum. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (both min leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive exclusiveMinimum 400 leftover both.", fetch2="https://json-schema.org/understanding-json-schema/reference/numeric#exclusiveminimum", fetch2_ok="Do not pair leftover minimum with exclusiveMinimum.")),
    (p(slug="oas-exclusive-max-with-maximum", domain="oas-exclusive-max-with-maximum-vs-leftover-both-max-keywords", success=True, name="a9f486", stack="OpenAPI 3.1 maximum + Go", field="maximum", old="both max leftover", new="exclusiveMaximum without maximum", fail_err="400: leftover both max leftover after exclusiveMaximum without maximum-only", plan="exclusiveMaximum without maximum-only 400s leftover both max leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (exclusiveMaximum without maximum vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/numeric#exclusivemaximum", fetch1_ok="Do not pair leftover maximum with exclusiveMaximum.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive exclusiveMaximum 400 leftover both."),
     p(slug="leftover-both-max-keywords", domain="leftover-both-max-keywords-vs-oas-exclusive-max-with-maximum", success=False, name="0b40af", stack="OpenAPI leftover maximum + Java + TS", field="maximum", old="exclusiveMaximum without maximum", new="both max leftover only", fail_err="400: leftover exclusiveMaximum without maximum after both max leftover-only", plan="both max leftover-only 400s leftover exclusiveMaximum without maximum. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (both max leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive exclusiveMaximum 400 leftover both.", fetch2="https://json-schema.org/understanding-json-schema/reference/numeric#exclusivemaximum", fetch2_ok="Do not pair leftover maximum with exclusiveMaximum.")),
    (p(slug="oas-default-readonly-omit", domain="oas-default-readonly-omit-vs-leftover-default-on-write", success=True, name="096341", stack="OpenAPI 3.1 default + Go", field="default", old="default on write leftover", new="readOnly default omit write", fail_err="400: leftover default on write leftover after readOnly default omit write-only", plan="readOnly default omit write-only 400s leftover default on write leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (readOnly default omit write vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="readOnly defaults are omitted on write, leftover write default fails closed.", fetch2="https://json-schema.org/understanding-json-schema/reference/generic#annotation", fetch2_ok="Exclusive omit default 400 leftover write."),
     p(slug="leftover-default-on-write", domain="leftover-default-on-write-vs-oas-default-readonly-omit", success=False, name="cbed40", stack="OpenAPI leftover default + Java + TS", field="default", old="readOnly default omit write", new="default on write leftover only", fail_err="400: leftover readOnly default omit write after default on write leftover-only", plan="default on write leftover-only 400s leftover readOnly default omit write. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (default on write leftover leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/generic#annotation", fetch1_ok="Exclusive omit default 400 leftover write.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="readOnly defaults are omitted on write, leftover write default fails closed.")),
    (p(slug="oas-deprecated-needs-desc", domain="oas-deprecated-needs-desc-vs-leftover-deprecated-no-desc", success=True, name="de0958", stack="OpenAPI 3.1 deprecated + Go", field="deprecated", old="deprecated no desc leftover", new="deprecated with description", fail_err="400: leftover deprecated no desc leftover after deprecated with description-only", plan="deprecated with description-only 400s leftover deprecated no desc leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (deprecated with description vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="deprecated fields need description, leftover missing fails closed.", fetch2="https://json-schema.org/understanding-json-schema/reference/generic#annotation", fetch2_ok="Exclusive deprecated desc 400 leftover none."),
     p(slug="leftover-deprecated-no-desc", domain="leftover-deprecated-no-desc-vs-oas-deprecated-needs-desc", success=False, name="a4fa23", stack="OpenAPI leftover deprecated + Java + TS", field="deprecated", old="deprecated with description", new="deprecated no desc leftover only", fail_err="400: leftover deprecated with description after deprecated no desc leftover-only", plan="deprecated no desc leftover-only 400s leftover deprecated with description. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (deprecated no desc leftover leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/generic#annotation", fetch1_ok="Exclusive deprecated desc 400 leftover none.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="deprecated fields need description, leftover missing fails closed.")),
    (p(slug="oas-examples-typed-values", domain="oas-examples-typed-values-vs-leftover-examples-wrong-type", success=True, name="448125", stack="OpenAPI 3.1 examples + Go", field="examples", old="wrong type examples leftover", new="typed examples", fail_err="400: leftover wrong type examples leftover after typed examples-only", plan="typed examples-only 400s leftover wrong type examples leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (typed examples vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/generic#annotation", fetch1_ok="examples must match the schema type, leftover wrong-type fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive typed examples 400 leftover wrong type."),
     p(slug="leftover-examples-wrong-type", domain="leftover-examples-wrong-type-vs-oas-examples-typed-values", success=False, name="24c941", stack="OpenAPI leftover examples + Java + TS", field="examples", old="typed examples", new="wrong type examples leftover only", fail_err="400: leftover typed examples after wrong type examples leftover-only", plan="wrong type examples leftover-only 400s leftover typed examples. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (wrong type examples leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive typed examples 400 leftover wrong type.", fetch2="https://json-schema.org/understanding-json-schema/reference/generic#annotation", fetch2_ok="examples must match the schema type, leftover wrong-type fails closed.")),
    (p(slug="oas-schema-id-fragment-ok", domain="oas-schema-id-fragment-ok-vs-leftover-id-fragment-rejected", success=True, name="7dd6b8", stack="OpenAPI 3.1 $id + Go", field="$id", old="reject fragment leftover", new="$id fragment allowed", fail_err="400: leftover reject fragment leftover after $id fragment allowed-only", plan="$id fragment allowed-only 400s leftover reject fragment leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv ($id fragment allowed vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/schema#id", fetch1_ok="$id may be a fragment, leftover reject-fragment fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive $id fragment 400 leftover reject."),
     p(slug="leftover-id-fragment-rejected", domain="leftover-id-fragment-rejected-vs-oas-schema-id-fragment-ok", success=False, name="57bb29", stack="OpenAPI leftover $id + Java + TS", field="$id", old="$id fragment allowed", new="reject fragment leftover only", fail_err="400: leftover $id fragment allowed after reject fragment leftover-only", plan="reject fragment leftover-only 400s leftover $id fragment allowed. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (reject fragment leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive $id fragment 400 leftover reject.", fetch2="https://json-schema.org/understanding-json-schema/reference/schema#id", fetch2_ok="$id may be a fragment, leftover reject-fragment fails closed.")),
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
    print(json.dumps({"round": round_n, "idx": idx, "ids": [e1["id"], e2["id"]], "catalog": "r4598"}))


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
