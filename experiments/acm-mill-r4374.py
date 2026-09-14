#!/usr/bin/env python3
"""Unique OpenAPI-drift ACM catalog r4374. Fast slug load."""
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
    (p(slug="oas-schema-min-length-str", domain="oas-schema-min-length-str-vs-leftover-empty-str-ok", success=True, name="f369aa", stack="OpenAPI 3.1 minLength + Go", field="minLength", old="empty str leftover", new="minLength string", fail_err="400: leftover empty str leftover after minLength string-only", plan="minLength string-only 400s leftover empty str leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (minLength string vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/string#length", fetch1_ok="minLength rejects empty strings, leftover empty-ok fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive minLength 400 leftover empty str."),
     p(slug="leftover-empty-str-ok", domain="leftover-empty-str-ok-vs-oas-schema-min-length-str", success=False, name="176bc7", stack="OpenAPI leftover minLength + Java + TS", field="minLength", old="minLength string", new="empty str leftover only", fail_err="400: leftover minLength string after empty str leftover-only", plan="empty str leftover-only 400s leftover minLength string. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (empty str leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive minLength 400 leftover empty str.", fetch2="https://json-schema.org/understanding-json-schema/reference/string#length", fetch2_ok="minLength rejects empty strings, leftover empty-ok fails closed.")),
    (p(slug="oas-schema-max-length-str", domain="oas-schema-max-length-str-vs-leftover-unbounded-str-len", success=True, name="635816", stack="OpenAPI 3.1 maxLength + Go", field="maxLength", old="unbounded str leftover", new="maxLength string", fail_err="400: leftover unbounded str leftover after maxLength string-only", plan="maxLength string-only 400s leftover unbounded str leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (maxLength string vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/string#length", fetch1_ok="maxLength bounds strings, leftover unbounded fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive maxLength 400 leftover unbounded str."),
     p(slug="leftover-unbounded-str-len", domain="leftover-unbounded-str-len-vs-oas-schema-max-length-str", success=False, name="f62f1d", stack="OpenAPI leftover maxLength + Java + TS", field="maxLength", old="maxLength string", new="unbounded str leftover only", fail_err="400: leftover maxLength string after unbounded str leftover-only", plan="unbounded str leftover-only 400s leftover maxLength string. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (unbounded str leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive maxLength 400 leftover unbounded str.", fetch2="https://json-schema.org/understanding-json-schema/reference/string#length", fetch2_ok="maxLength bounds strings, leftover unbounded fails closed.")),
    (p(slug="oas-schema-multiple-of-n", domain="oas-schema-multiple-of-n-vs-leftover-any-number-step", success=True, name="689bff", stack="OpenAPI 3.1 multipleOf + Go", field="multipleOf", old="any step leftover", new="multipleOf", fail_err="400: leftover any step leftover after multipleOf-only", plan="multipleOf-only 400s leftover any step leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (multipleOf vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/numeric#multiples", fetch1_ok="multipleOf constrains steps, leftover any-step fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive multipleOf 400 leftover any step."),
     p(slug="leftover-any-number-step", domain="leftover-any-number-step-vs-oas-schema-multiple-of-n", success=False, name="12f98e", stack="OpenAPI leftover multipleOf + Java + TS", field="multipleOf", old="multipleOf", new="any step leftover only", fail_err="400: leftover multipleOf after any step leftover-only", plan="any step leftover-only 400s leftover multipleOf. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (any step leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive multipleOf 400 leftover any step.", fetch2="https://json-schema.org/understanding-json-schema/reference/numeric#multiples", fetch2_ok="multipleOf constrains steps, leftover any-step fails closed.")),
    (p(slug="oas-exclusive-max-number", domain="oas-exclusive-max-number-vs-leftover-exclusive-max-boolean", success=True, name="426e45", stack="OpenAPI 3.1 exclusiveMaximum + Go", field="exclusiveMaximum", old="boolean exclusiveMaximum leftover", new="numeric exclusiveMaximum", fail_err="400: leftover boolean exclusiveMaximum leftover after numeric exclusiveMaximum-only", plan="numeric exclusiveMaximum-only 400s leftover boolean exclusiveMaximum leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (numeric exclusiveMaximum vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/numeric#exclusivemaximum", fetch1_ok="exclusiveMaximum is a number, leftover OAS 3.0 boolean fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="Exclusive numeric exclusiveMaximum 400 leftover boolean."),
     p(slug="leftover-exclusive-max-boolean", domain="leftover-exclusive-max-boolean-vs-oas-exclusive-max-number", success=False, name="209a0e", stack="OpenAPI leftover exclusiveMaximum + Java + TS", field="exclusiveMaximum", old="numeric exclusiveMaximum", new="boolean exclusiveMaximum leftover only", fail_err="400: leftover numeric exclusiveMaximum after boolean exclusiveMaximum leftover-only", plan="boolean exclusiveMaximum leftover-only 400s leftover numeric exclusiveMaximum. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (boolean exclusiveMaximum leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="Exclusive numeric exclusiveMaximum 400 leftover boolean.", fetch2="https://json-schema.org/understanding-json-schema/reference/numeric#exclusivemaximum", fetch2_ok="exclusiveMaximum is a number, leftover OAS 3.0 boolean fails closed.")),
    (p(slug="oas-type-array-items-req", domain="oas-type-array-items-req-vs-leftover-untyped-array-elem", success=True, name="318e14", stack="OpenAPI 3.1 items + Go", field="items", old="untyped array leftover", new="array items required", fail_err="400: leftover untyped array leftover after array items required-only", plan="array items required-only 400s leftover untyped array leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (array items required vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/array#items", fetch1_ok="array items schema is required, leftover untyped fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive array items 400 leftover untyped."),
     p(slug="leftover-untyped-array-elem", domain="leftover-untyped-array-elem-vs-oas-type-array-items-req", success=False, name="5ac29f", stack="OpenAPI leftover items + Java + TS", field="items", old="array items required", new="untyped array leftover only", fail_err="400: leftover array items required after untyped array leftover-only", plan="untyped array leftover-only 400s leftover array items required. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (untyped array leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive array items 400 leftover untyped.", fetch2="https://json-schema.org/understanding-json-schema/reference/array#items", fetch2_ok="array items schema is required, leftover untyped fails closed.")),
    (p(slug="oas-examples-example-mutex", domain="oas-examples-example-mutex-vs-leftover-both-example-keys", success=True, name="873927", stack="OpenAPI 3.1 examples + Go", field="examples", old="both example keys leftover", new="example xor examples", fail_err="400: leftover both example keys leftover after example xor examples-only", plan="example xor examples-only 400s leftover both example keys leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (example xor examples vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch1_ok="example and examples are mutually exclusive, leftover both fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#example-object", fetch2_ok="Exclusive xor 400 leftover both keys."),
     p(slug="leftover-both-example-keys", domain="leftover-both-example-keys-vs-oas-examples-example-mutex", success=False, name="6f4f76", stack="OpenAPI leftover examples + Java + TS", field="examples", old="example xor examples", new="both example keys leftover only", fail_err="400: leftover example xor examples after both example keys leftover-only", plan="both example keys leftover-only 400s leftover example xor examples. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (both example keys leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#example-object", fetch1_ok="Exclusive xor 400 leftover both keys.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch2_ok="example and examples are mutually exclusive, leftover both fails closed.")),
    (p(slug="oas-components-params-ref", domain="oas-components-params-ref-vs-leftover-inline-param-only", success=True, name="75b3bd", stack="OpenAPI 3.1 parameters + Go", field="parameters", old="inline param leftover", new="components parameters ref", fail_err="400: leftover inline param leftover after components parameters ref-only", plan="components parameters ref-only 400s leftover inline param leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (components parameters ref vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#components-object", fetch1_ok="components.parameters reuse, leftover inline-only is not that.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="Exclusive components params 400 leftover inline."),
     p(slug="leftover-inline-param-only", domain="leftover-inline-param-only-vs-oas-components-params-ref", success=False, name="ed5285", stack="OpenAPI leftover parameters + Java + TS", field="parameters", old="components parameters ref", new="inline param leftover only", fail_err="400: leftover components parameters ref after inline param leftover-only", plan="inline param leftover-only 400s leftover components parameters ref. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (inline param leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="Exclusive components params 400 leftover inline.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#components-object", fetch2_ok="components.parameters reuse, leftover inline-only is not that.")),
    (p(slug="oas-components-headers-ref", domain="oas-components-headers-ref-vs-leftover-inline-header-only", success=True, name="543a37", stack="OpenAPI 3.1 headers + Go", field="headers", old="inline header leftover", new="components headers ref", fail_err="400: leftover inline header leftover after components headers ref-only", plan="components headers ref-only 400s leftover inline header leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (components headers ref vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#components-object", fetch1_ok="components.headers reuse, leftover inline-only is not that.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch2_ok="Exclusive components headers 400 leftover inline."),
     p(slug="leftover-inline-header-only", domain="leftover-inline-header-only-vs-oas-components-headers-ref", success=False, name="6c5d32", stack="OpenAPI leftover headers + Java + TS", field="headers", old="components headers ref", new="inline header leftover only", fail_err="400: leftover components headers ref after inline header leftover-only", plan="inline header leftover-only 400s leftover components headers ref. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (inline header leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch1_ok="Exclusive components headers 400 leftover inline.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#components-object", fetch2_ok="components.headers reuse, leftover inline-only is not that.")),
    (p(slug="oas-path-item-dollar-ref", domain="oas-path-item-dollar-ref-vs-leftover-duplicated-path-item", success=True, name="4b8800", stack="OpenAPI 3.1 $ref + Go", field="$ref", old="duplicated path leftover", new="pathItem $ref", fail_err="400: leftover duplicated path leftover after pathItem $ref-only", plan="pathItem $ref-only 400s leftover duplicated path leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (pathItem $ref vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#path-item-object", fetch1_ok="Path Item $ref reuses paths, leftover duplicates fail closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#paths-object", fetch2_ok="Exclusive path $ref 400 leftover duplicate."),
     p(slug="leftover-duplicated-path-item", domain="leftover-duplicated-path-item-vs-oas-path-item-dollar-ref", success=False, name="e7b83c", stack="OpenAPI leftover $ref + Java + TS", field="$ref", old="pathItem $ref", new="duplicated path leftover only", fail_err="400: leftover pathItem $ref after duplicated path leftover-only", plan="duplicated path leftover-only 400s leftover pathItem $ref. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (duplicated path leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#paths-object", fetch1_ok="Exclusive path $ref 400 leftover duplicate.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#path-item-object", fetch2_ok="Path Item $ref reuses paths, leftover duplicates fail closed.")),
    (p(slug="oas-trace-method-disabled", domain="oas-trace-method-disabled-vs-leftover-trace-enabled", success=True, name="1864ce", stack="OpenAPI 3.1 trace + Go", field="trace", old="TRACE enabled leftover", new="TRACE disabled", fail_err="400: leftover TRACE enabled leftover after TRACE disabled-only", plan="TRACE disabled-only 400s leftover TRACE enabled leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (TRACE disabled vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#path-item-object", fetch1_ok="TRACE is disabled here, leftover TRACE fails closed.", fetch2="https://datatracker.ietf.org/doc/html/rfc9110#name-trace", fetch2_ok="Exclusive TRACE off 400 leftover enabled."),
     p(slug="leftover-trace-enabled", domain="leftover-trace-enabled-vs-oas-trace-method-disabled", success=False, name="44de1d", stack="OpenAPI leftover trace + Java + TS", field="trace", old="TRACE disabled", new="TRACE enabled leftover only", fail_err="400: leftover TRACE disabled after TRACE enabled leftover-only", plan="TRACE enabled leftover-only 400s leftover TRACE disabled. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (TRACE enabled leftover leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc9110#name-trace", fetch1_ok="Exclusive TRACE off 400 leftover enabled.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#path-item-object", fetch2_ok="TRACE is disabled here, leftover TRACE fails closed.")),
    (p(slug="oas-connect-method-absent", domain="oas-connect-method-absent-vs-leftover-connect-tunnel", success=True, name="12d714", stack="OpenAPI 3.1 connect + Go", field="connect", old="CONNECT leftover", new="CONNECT absent", fail_err="400: leftover CONNECT leftover after CONNECT absent-only", plan="CONNECT absent-only 400s leftover CONNECT leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (CONNECT absent vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#path-item-object", fetch1_ok="CONNECT is not an OAS method, leftover CONNECT fails closed.", fetch2="https://datatracker.ietf.org/doc/html/rfc9110#name-connect", fetch2_ok="Exclusive CONNECT absent 400 leftover tunnel."),
     p(slug="leftover-connect-tunnel", domain="leftover-connect-tunnel-vs-oas-connect-method-absent", success=False, name="e40010", stack="OpenAPI leftover connect + Java + TS", field="connect", old="CONNECT absent", new="CONNECT leftover only", fail_err="400: leftover CONNECT absent after CONNECT leftover-only", plan="CONNECT leftover-only 400s leftover CONNECT absent. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (CONNECT leftover leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc9110#name-connect", fetch1_ok="Exclusive CONNECT absent 400 leftover tunnel.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#path-item-object", fetch2_ok="CONNECT is not an OAS method, leftover CONNECT fails closed.")),
    (p(slug="oas-tag-desc-nonempty", domain="oas-tag-desc-nonempty-vs-leftover-tag-without-desc", success=True, name="2dfa16", stack="OpenAPI 3.1 description + Go", field="description", old="tag name only leftover", new="tag description nonempty", fail_err="400: leftover tag name only leftover after tag description nonempty-only", plan="tag description nonempty-only 400s leftover tag name only leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (tag description nonempty vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#tag-object", fetch1_ok="tag.description must be nonempty, leftover name-only fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#tags", fetch2_ok="Exclusive tag desc 400 leftover name only."),
     p(slug="leftover-tag-without-desc", domain="leftover-tag-without-desc-vs-oas-tag-desc-nonempty", success=False, name="4e67df", stack="OpenAPI leftover description + Java + TS", field="description", old="tag description nonempty", new="tag name only leftover only", fail_err="400: leftover tag description nonempty after tag name only leftover-only", plan="tag name only leftover-only 400s leftover tag description nonempty. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (tag name only leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#tags", fetch1_ok="Exclusive tag desc 400 leftover name only.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#tag-object", fetch2_ok="tag.description must be nonempty, leftover name-only fails closed.")),
    (p(slug="oas-external-docs-https", domain="oas-external-docs-https-vs-leftover-docs-relative-url", success=True, name="bb44f9", stack="OpenAPI 3.1 url + Go", field="url", old="relative docs leftover", new="externalDocs https", fail_err="400: leftover relative docs leftover after externalDocs https-only", plan="externalDocs https-only 400s leftover relative docs leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (externalDocs https vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#external-documentation-object", fetch1_ok="externalDocs.url must be https, leftover relative fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#openapi-object", fetch2_ok="Exclusive docs https 400 leftover relative."),
     p(slug="leftover-docs-relative-url", domain="leftover-docs-relative-url-vs-oas-external-docs-https", success=False, name="b64016", stack="OpenAPI leftover url + Java + TS", field="url", old="externalDocs https", new="relative docs leftover only", fail_err="400: leftover externalDocs https after relative docs leftover-only", plan="relative docs leftover-only 400s leftover externalDocs https. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (relative docs leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#openapi-object", fetch1_ok="Exclusive docs https 400 leftover relative.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#external-documentation-object", fetch2_ok="externalDocs.url must be https, leftover relative fails closed.")),
    (p(slug="oas-callback-servers-item", domain="oas-callback-servers-item-vs-leftover-callback-root-server", success=True, name="d5baec", stack="OpenAPI 3.1 servers + Go", field="servers", old="callback root leftover", new="callback servers", fail_err="400: leftover callback root leftover after callback servers-only", plan="callback servers-only 400s leftover callback root leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (callback servers vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#callback-object", fetch1_ok="callback servers override root, leftover root-only fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#server-object", fetch2_ok="Exclusive callback servers 400 leftover root."),
     p(slug="leftover-callback-root-server", domain="leftover-callback-root-server-vs-oas-callback-servers-item", success=False, name="4ab7dc", stack="OpenAPI leftover servers + Java + TS", field="servers", old="callback servers", new="callback root leftover only", fail_err="400: leftover callback servers after callback root leftover-only", plan="callback root leftover-only 400s leftover callback servers. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (callback root leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#server-object", fetch1_ok="Exclusive callback servers 400 leftover root.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#callback-object", fetch2_ok="callback servers override root, leftover root-only fails closed.")),
    (p(slug="oas-oauth2-scopes-object", domain="oas-oauth2-scopes-object-vs-leftover-scope-csv-string", success=True, name="20c7aa", stack="OpenAPI 3.1 scopes + Go", field="scopes", old="scope csv leftover", new="oauth2 scopes object", fail_err="401: leftover scope csv leftover after oauth2 scopes object-only", plan="oauth2 scopes object-only 401s leftover scope csv leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (oauth2 scopes object vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#oauth-flow-object", fetch1_ok="scopes is a map, leftover csv string fails closed.", fetch2="https://datatracker.ietf.org/doc/html/rfc6749", fetch2_ok="Exclusive scopes map 401 leftover csv."),
     p(slug="leftover-scope-csv-string", domain="leftover-scope-csv-string-vs-oas-oauth2-scopes-object", success=False, name="18d335", stack="OpenAPI leftover scopes + Java + TS", field="scopes", old="oauth2 scopes object", new="scope csv leftover only", fail_err="401: leftover oauth2 scopes object after scope csv leftover-only", plan="scope csv leftover-only 401s leftover oauth2 scopes object. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (scope csv leftover leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc6749", fetch1_ok="Exclusive scopes map 401 leftover csv.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#oauth-flow-object", fetch2_ok="scopes is a map, leftover csv string fails closed.")),
    (p(slug="oas-digest-http-auth", domain="oas-digest-http-auth-vs-leftover-basic-as-digest-auth", success=True, name="08d64e", stack="OpenAPI 3.1 scheme + Go", field="scheme", old="basic as digest leftover", new="HTTP digest", fail_err="401: leftover basic as digest leftover after HTTP digest-only", plan="HTTP digest-only 401s leftover basic as digest leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (HTTP digest vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch1_ok="HTTP digest is not leftover basic-as-digest.", fetch2="https://datatracker.ietf.org/doc/html/rfc7616", fetch2_ok="Exclusive digest 401 leftover basic."),
     p(slug="leftover-basic-as-digest-auth", domain="leftover-basic-as-digest-auth-vs-oas-digest-http-auth", success=False, name="3a4a7a", stack="OpenAPI leftover scheme + Java + TS", field="scheme", old="HTTP digest", new="basic as digest leftover only", fail_err="401: leftover HTTP digest after basic as digest leftover-only", plan="basic as digest leftover-only 401s leftover HTTP digest. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (basic as digest leftover leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc7616", fetch1_ok="Exclusive digest 401 leftover basic.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch2_ok="HTTP digest is not leftover basic-as-digest.")),
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
    print(json.dumps({"round": round_n, "idx": idx, "ids": [e1["id"], e2["id"]], "catalog": "r4374"}))


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
