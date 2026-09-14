#!/usr/bin/env python3
"""Unique OpenAPI-drift ACM catalog r4310. Fast slug load."""
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
    (p(slug="oas-format-byte-rfc4648", domain="oas-format-byte-rfc4648-vs-leftover-hex-as-byte", success=True, name="45a876", stack="OpenAPI 3.1 format + Go", field="format", old="hex as byte leftover", new="format byte rfc4648", fail_err="400: leftover hex as byte leftover after format byte rfc4648-only", plan="format byte rfc4648-only 400s leftover hex as byte leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (format byte rfc4648 vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="format=byte is base64, leftover hex fails closed.", fetch2="https://datatracker.ietf.org/doc/html/rfc4648", fetch2_ok="Exclusive byte 400 leftover hex."),
     p(slug="leftover-hex-as-byte", domain="leftover-hex-as-byte-vs-oas-format-byte-rfc4648", success=False, name="6fc606", stack="OpenAPI leftover format + Java + TS", field="format", old="format byte rfc4648", new="hex as byte leftover only", fail_err="400: leftover format byte rfc4648 after hex as byte leftover-only", plan="hex as byte leftover-only 400s leftover format byte rfc4648. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (hex as byte leftover leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc4648", fetch1_ok="Exclusive byte 400 leftover hex.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="format=byte is base64, leftover hex fails closed.")),
    (p(slug="oas-tag-name-unique", domain="oas-tag-name-unique-vs-leftover-duplicate-tag-name", success=True, name="d3be23", stack="OpenAPI 3.1 name + Go", field="name", old="duplicate tag leftover", new="unique tag name", fail_err="400: leftover duplicate tag leftover after unique tag name-only", plan="unique tag name-only 400s leftover duplicate tag leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (unique tag name vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#tag-object", fetch1_ok="tag names must be unique, leftover duplicates fail closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#tags", fetch2_ok="Exclusive unique tag 400 leftover duplicate."),
     p(slug="leftover-duplicate-tag-name", domain="leftover-duplicate-tag-name-vs-oas-tag-name-unique", success=False, name="5c205a", stack="OpenAPI leftover name + Java + TS", field="name", old="unique tag name", new="duplicate tag leftover only", fail_err="400: leftover unique tag name after duplicate tag leftover-only", plan="duplicate tag leftover-only 400s leftover unique tag name. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (duplicate tag leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#tags", fetch1_ok="Exclusive unique tag 400 leftover duplicate.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#tag-object", fetch2_ok="tag names must be unique, leftover duplicates fail closed.")),
    (p(slug="oas-servers-https-required", domain="oas-servers-https-required-vs-leftover-plain-http-server", success=True, name="57532a", stack="OpenAPI 3.1 url + Go", field="url", old="plain http leftover", new="https server url", fail_err="400: leftover plain http leftover after https server url-only", plan="https server url-only 400s leftover plain http leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (https server url vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#server-object", fetch1_ok="Production servers must be https, leftover http fails closed.", fetch2="https://datatracker.ietf.org/doc/html/rfc9110", fetch2_ok="Exclusive https server 400 leftover http."),
     p(slug="leftover-plain-http-server", domain="leftover-plain-http-server-vs-oas-servers-https-required", success=False, name="56d176", stack="OpenAPI leftover url + Java + TS", field="url", old="https server url", new="plain http leftover only", fail_err="400: leftover https server url after plain http leftover-only", plan="plain http leftover-only 400s leftover https server url. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (plain http leftover leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc9110", fetch1_ok="Exclusive https server 400 leftover http.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#server-object", fetch2_ok="Production servers must be https, leftover http fails closed.")),
    (p(slug="oas-schema-enum-typed", domain="oas-schema-enum-typed-vs-leftover-enum-untyped", success=True, name="05ad46", stack="OpenAPI 3.1 enum + Go", field="enum", old="untyped enum leftover", new="typed enum", fail_err="400: leftover untyped enum leftover after typed enum-only", plan="typed enum-only 400s leftover untyped enum leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (typed enum vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/generic#enumerated-values", fetch1_ok="enum values must match type, leftover untyped fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive typed enum 400 leftover untyped."),
     p(slug="leftover-enum-untyped", domain="leftover-enum-untyped-vs-oas-schema-enum-typed", success=False, name="f71273", stack="OpenAPI leftover enum + Java + TS", field="enum", old="typed enum", new="untyped enum leftover only", fail_err="400: leftover typed enum after untyped enum leftover-only", plan="untyped enum leftover-only 400s leftover typed enum. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (untyped enum leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive typed enum 400 leftover untyped.", fetch2="https://json-schema.org/understanding-json-schema/reference/generic#enumerated-values", fetch2_ok="enum values must match type, leftover untyped fails closed.")),
    (p(slug="oas-oneof-with-discriminator", domain="oas-oneof-with-discriminator-vs-leftover-oneof-no-disc", success=True, name="fb8800", stack="OpenAPI 3.1 discriminator + Go", field="discriminator", old="oneof no disc leftover", new="oneOf discriminator", fail_err="400: leftover oneof no disc leftover after oneOf discriminator-only", plan="oneOf discriminator-only 400s leftover oneof no disc leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (oneOf discriminator vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#discriminator-object", fetch1_ok="oneOf payloads need a discriminator, leftover none fails closed.", fetch2="https://json-schema.org/understanding-json-schema/reference/combining#oneof", fetch2_ok="Exclusive oneOf disc 400 leftover none."),
     p(slug="leftover-oneof-no-disc", domain="leftover-oneof-no-disc-vs-oas-oneof-with-discriminator", success=False, name="4a6025", stack="OpenAPI leftover discriminator + Java + TS", field="discriminator", old="oneOf discriminator", new="oneof no disc leftover only", fail_err="400: leftover oneOf discriminator after oneof no disc leftover-only", plan="oneof no disc leftover-only 400s leftover oneOf discriminator. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (oneof no disc leftover leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/combining#oneof", fetch1_ok="Exclusive oneOf disc 400 leftover none.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#discriminator-object", fetch2_ok="oneOf payloads need a discriminator, leftover none fails closed.")),
    (p(slug="oas-link-param-runtime-expr", domain="oas-link-param-runtime-expr-vs-leftover-hardcoded-link-param", success=True, name="4623e3", stack="OpenAPI 3.1 parameters + Go", field="parameters", old="hardcoded link leftover", new="link param runtime expr", fail_err="400: leftover hardcoded link leftover after link param runtime expr-only", plan="link param runtime expr-only 400s leftover hardcoded link leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (link param runtime expr vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#link-object", fetch1_ok="link.parameters use runtime expressions, leftover hardcoded fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#runtime-expressions", fetch2_ok="Exclusive link expr 400 leftover hardcoded."),
     p(slug="leftover-hardcoded-link-param", domain="leftover-hardcoded-link-param-vs-oas-link-param-runtime-expr", success=False, name="4071d6", stack="OpenAPI leftover parameters + Java + TS", field="parameters", old="link param runtime expr", new="hardcoded link leftover only", fail_err="400: leftover link param runtime expr after hardcoded link leftover-only", plan="hardcoded link leftover-only 400s leftover link param runtime expr. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (hardcoded link leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#runtime-expressions", fetch1_ok="Exclusive link expr 400 leftover hardcoded.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#link-object", fetch2_ok="link.parameters use runtime expressions, leftover hardcoded fails closed.")),
    (p(slug="oas-oauth2-client-credentials", domain="oas-oauth2-client-credentials-vs-leftover-password-as-clientcreds", success=True, name="14a852", stack="OpenAPI 3.1 clientCredentials + Go", field="clientCredentials", old="password as client leftover", new="clientCredentials flow", fail_err="401: leftover password as client leftover after clientCredentials flow-only", plan="clientCredentials flow-only 401s leftover password as client leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (clientCredentials flow vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#oauth-flows-object", fetch1_ok="clientCredentials is not leftover password-as-client.", fetch2="https://datatracker.ietf.org/doc/html/rfc6749#section-4.4", fetch2_ok="Exclusive client creds 401 leftover password."),
     p(slug="leftover-password-as-clientcreds", domain="leftover-password-as-clientcreds-vs-oas-oauth2-client-credentials", success=False, name="c261f9", stack="OpenAPI leftover clientCredentials + Java + TS", field="clientCredentials", old="clientCredentials flow", new="password as client leftover only", fail_err="401: leftover clientCredentials flow after password as client leftover-only", plan="password as client leftover-only 401s leftover clientCredentials flow. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (password as client leftover leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc6749#section-4.4", fetch1_ok="Exclusive client creds 401 leftover password.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#oauth-flows-object", fetch2_ok="clientCredentials is not leftover password-as-client.")),
    (p(slug="oas-oauth2-refresh-token-url", domain="oas-oauth2-refresh-token-url-vs-leftover-token-url-as-refresh", success=True, name="ebce93", stack="OpenAPI 3.1 refreshUrl + Go", field="refreshUrl", old="tokenUrl as refresh leftover", new="oauth2 refreshUrl", fail_err="401: leftover tokenUrl as refresh leftover after oauth2 refreshUrl-only", plan="oauth2 refreshUrl-only 401s leftover tokenUrl as refresh leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (oauth2 refreshUrl vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#oauth-flow-object", fetch1_ok="refreshUrl is distinct from tokenUrl, leftover reuse fails closed.", fetch2="https://datatracker.ietf.org/doc/html/rfc6749#section-6", fetch2_ok="Exclusive refreshUrl 401 leftover tokenUrl."),
     p(slug="leftover-token-url-as-refresh", domain="leftover-token-url-as-refresh-vs-oas-oauth2-refresh-token-url", success=False, name="92df05", stack="OpenAPI leftover refreshUrl + Java + TS", field="refreshUrl", old="oauth2 refreshUrl", new="tokenUrl as refresh leftover only", fail_err="401: leftover oauth2 refreshUrl after tokenUrl as refresh leftover-only", plan="tokenUrl as refresh leftover-only 401s leftover oauth2 refreshUrl. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (tokenUrl as refresh leftover leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc6749#section-6", fetch1_ok="Exclusive refreshUrl 401 leftover tokenUrl.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#oauth-flow-object", fetch2_ok="refreshUrl is distinct from tokenUrl, leftover reuse fails closed.")),
    (p(slug="oas-schema-min-contains-n", domain="oas-schema-min-contains-n-vs-leftover-contains-without-min", success=True, name="24ee0a", stack="OpenAPI 3.1 minContains + Go", field="minContains", old="contains no min leftover", new="minContains", fail_err="400: leftover contains no min leftover after minContains-only", plan="minContains-only 400s leftover contains no min leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (minContains vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/array#mincontains", fetch1_ok="minContains bounds contains matches, leftover unbounded fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive minContains 400 leftover no min."),
     p(slug="leftover-contains-without-min", domain="leftover-contains-without-min-vs-oas-schema-min-contains-n", success=False, name="8c95d4", stack="OpenAPI leftover minContains + Java + TS", field="minContains", old="minContains", new="contains no min leftover only", fail_err="400: leftover minContains after contains no min leftover-only", plan="contains no min leftover-only 400s leftover minContains. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (contains no min leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive minContains 400 leftover no min.", fetch2="https://json-schema.org/understanding-json-schema/reference/array#mincontains", fetch2_ok="minContains bounds contains matches, leftover unbounded fails closed.")),
    (p(slug="oas-schema-max-contains-n", domain="oas-schema-max-contains-n-vs-leftover-unlimited-contains", success=True, name="ac8d0e", stack="OpenAPI 3.1 maxContains + Go", field="maxContains", old="unlimited contains leftover", new="maxContains", fail_err="400: leftover unlimited contains leftover after maxContains-only", plan="maxContains-only 400s leftover unlimited contains leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (maxContains vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/array#maxcontains", fetch1_ok="maxContains caps contains matches, leftover unlimited fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive maxContains 400 leftover unlimited."),
     p(slug="leftover-unlimited-contains", domain="leftover-unlimited-contains-vs-oas-schema-max-contains-n", success=False, name="c48128", stack="OpenAPI leftover maxContains + Java + TS", field="maxContains", old="maxContains", new="unlimited contains leftover only", fail_err="400: leftover maxContains after unlimited contains leftover-only", plan="unlimited contains leftover-only 400s leftover maxContains. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (unlimited contains leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive maxContains 400 leftover unlimited.", fetch2="https://json-schema.org/understanding-json-schema/reference/array#maxcontains", fetch2_ok="maxContains caps contains matches, leftover unlimited fails closed.")),
    (p(slug="oas-dependent-schemas-map", domain="oas-dependent-schemas-map-vs-leftover-if-then-schema", success=True, name="17da4c", stack="OpenAPI 3.1 dependentSchemas + Go", field="dependentSchemas", old="if-then leftover", new="dependentSchemas", fail_err="400: leftover if-then leftover after dependentSchemas-only", plan="dependentSchemas-only 400s leftover if-then leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (dependentSchemas vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/conditionals#dependentschemas", fetch1_ok="dependentSchemas is not leftover if/then.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive dependentSchemas 400 leftover if-then."),
     p(slug="leftover-if-then-schema", domain="leftover-if-then-schema-vs-oas-dependent-schemas-map", success=False, name="b2bf12", stack="OpenAPI leftover dependentSchemas + Java + TS", field="dependentSchemas", old="dependentSchemas", new="if-then leftover only", fail_err="400: leftover dependentSchemas after if-then leftover-only", plan="if-then leftover-only 400s leftover dependentSchemas. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (if-then leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive dependentSchemas 400 leftover if-then.", fetch2="https://json-schema.org/understanding-json-schema/reference/conditionals#dependentschemas", fetch2_ok="dependentSchemas is not leftover if/then.")),
    (p(slug="oas-pattern-properties-map", domain="oas-pattern-properties-map-vs-leftover-additional-as-pattern", success=True, name="1b7da8", stack="OpenAPI 3.1 patternProperties + Go", field="patternProperties", old="additional as pattern leftover", new="patternProperties", fail_err="400: leftover additional as pattern leftover after patternProperties-only", plan="patternProperties-only 400s leftover additional as pattern leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (patternProperties vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/object#patternproperties", fetch1_ok="patternProperties is not leftover additionalProperties.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive patternProperties 400 leftover additional."),
     p(slug="leftover-additional-as-pattern", domain="leftover-additional-as-pattern-vs-oas-pattern-properties-map", success=False, name="b094e1", stack="OpenAPI leftover patternProperties + Java + TS", field="patternProperties", old="patternProperties", new="additional as pattern leftover only", fail_err="400: leftover patternProperties after additional as pattern leftover-only", plan="additional as pattern leftover-only 400s leftover patternProperties. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (additional as pattern leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive patternProperties 400 leftover additional.", fetch2="https://json-schema.org/understanding-json-schema/reference/object#patternproperties", fetch2_ok="patternProperties is not leftover additionalProperties.")),
    (p(slug="oas-items-false-closed-tuple", domain="oas-items-false-closed-tuple-vs-leftover-open-items-schema", success=True, name="272d8c", stack="OpenAPI 3.1 items + Go", field="items", old="open items leftover", new="items false closed tuple", fail_err="400: leftover open items leftover after items false closed tuple-only", plan="items false closed tuple-only 400s leftover open items leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (items false closed tuple vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/array#items", fetch1_ok="items false forbids leftover tuple tails.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive items false 400 leftover open items."),
     p(slug="leftover-open-items-schema", domain="leftover-open-items-schema-vs-oas-items-false-closed-tuple", success=False, name="c57963", stack="OpenAPI leftover items + Java + TS", field="items", old="items false closed tuple", new="open items leftover only", fail_err="400: leftover items false closed tuple after open items leftover-only", plan="open items leftover-only 400s leftover items false closed tuple. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (open items leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive items false 400 leftover open items.", fetch2="https://json-schema.org/understanding-json-schema/reference/array#items", fetch2_ok="items false forbids leftover tuple tails.")),
    (p(slug="oas-type-integer-exclusive", domain="oas-type-integer-exclusive-vs-leftover-json-number-as-int", success=True, name="bde333", stack="OpenAPI 3.1 type + Go", field="type", old="json number leftover", new="type integer exclusive", fail_err="400: leftover json number leftover after type integer exclusive-only", plan="type integer exclusive-only 400s leftover json number leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (type integer exclusive vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/numeric#integer", fetch1_ok="type=integer rejects leftover JSON numbers with fractions.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="Exclusive integer 400 leftover json number."),
     p(slug="leftover-json-number-as-int", domain="leftover-json-number-as-int-vs-oas-type-integer-exclusive", success=False, name="c6aceb", stack="OpenAPI leftover type + Java + TS", field="type", old="type integer exclusive", new="json number leftover only", fail_err="400: leftover type integer exclusive after json number leftover-only", plan="json number leftover-only 400s leftover type integer exclusive. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (json number leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="Exclusive integer 400 leftover json number.", fetch2="https://json-schema.org/understanding-json-schema/reference/numeric#integer", fetch2_ok="type=integer rejects leftover JSON numbers with fractions.")),
    (p(slug="oas-format-float-ieee", domain="oas-format-float-ieee-vs-leftover-decimal-as-float", success=True, name="fef99b", stack="OpenAPI 3.1 format + Go", field="format", old="decimal as float leftover", new="format float ieee", fail_err="400: leftover decimal as float leftover after format float ieee-only", plan="format float ieee-only 400s leftover decimal as float leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (format float ieee vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="format=float is IEEE-754 binary32, leftover decimal fails closed.", fetch2="https://json-schema.org/understanding-json-schema/reference/numeric", fetch2_ok="Exclusive float 400 leftover decimal."),
     p(slug="leftover-decimal-as-float", domain="leftover-decimal-as-float-vs-oas-format-float-ieee", success=False, name="9178b6", stack="OpenAPI leftover format + Java + TS", field="format", old="format float ieee", new="decimal as float leftover only", fail_err="400: leftover format float ieee after decimal as float leftover-only", plan="decimal as float leftover-only 400s leftover format float ieee. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (decimal as float leftover leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/numeric", fetch1_ok="Exclusive float 400 leftover decimal.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="format=float is IEEE-754 binary32, leftover decimal fails closed.")),
    (p(slug="oas-format-double-ieee", domain="oas-format-double-ieee-vs-leftover-float-as-double", success=True, name="a22233", stack="OpenAPI 3.1 format + Go", field="format", old="float as double leftover", new="format double ieee", fail_err="400: leftover float as double leftover after format double ieee-only", plan="format double ieee-only 400s leftover float as double leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (format double ieee vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="format=double is binary64, leftover float-as-double fails closed.", fetch2="https://json-schema.org/understanding-json-schema/reference/numeric", fetch2_ok="Exclusive double 400 leftover float."),
     p(slug="leftover-float-as-double", domain="leftover-float-as-double-vs-oas-format-double-ieee", success=False, name="95737b", stack="OpenAPI leftover format + Java + TS", field="format", old="format double ieee", new="float as double leftover only", fail_err="400: leftover format double ieee after float as double leftover-only", plan="float as double leftover-only 400s leftover format double ieee. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (float as double leftover leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/numeric", fetch1_ok="Exclusive double 400 leftover float.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="format=double is binary64, leftover float-as-double fails closed.")),
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
    print(json.dumps({"round": round_n, "idx": idx, "ids": [e1["id"], e2["id"]], "catalog": "r4310"}))


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
