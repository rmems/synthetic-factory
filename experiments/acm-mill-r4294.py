#!/usr/bin/env python3
"""Unique OpenAPI-drift ACM catalog r4294. Fast slug load."""
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
    (p(slug="oas-schema-default-typed", domain="oas-schema-default-typed-vs-leftover-default-wrong-type", success=True, name="3fa862", stack="OpenAPI 3.1 default + Go", field="default", old="wrong type default leftover", new="typed default", fail_err="400: leftover wrong type default leftover after typed default-only", plan="typed default-only 400s leftover wrong type default leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (typed default vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/generic#annotation", fetch1_ok="default must match the schema type, leftover wrong-type fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive typed default 400 leftover wrong type."),
     p(slug="leftover-default-wrong-type", domain="leftover-default-wrong-type-vs-oas-schema-default-typed", success=False, name="9ef2de", stack="OpenAPI leftover default + Java + TS", field="default", old="typed default", new="wrong type default leftover only", fail_err="400: leftover typed default after wrong type default leftover-only", plan="wrong type default leftover-only 400s leftover typed default. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (wrong type default leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive typed default 400 leftover wrong type.", fetch2="https://json-schema.org/understanding-json-schema/reference/generic#annotation", fetch2_ok="default must match the schema type, leftover wrong-type fails closed.")),
    (p(slug="oas-op-summary-required", domain="oas-op-summary-required-vs-leftover-opid-as-summary", success=True, name="2b9d96", stack="OpenAPI 3.1 summary + Go", field="summary", old="opid as summary leftover", new="operation summary", fail_err="400: leftover opid as summary leftover after operation summary-only", plan="operation summary-only 400s leftover opid as summary leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (operation summary vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch1_ok="summary is human text, leftover operationId-as-summary fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#path-item-object", fetch2_ok="Exclusive op summary 400 leftover opid."),
     p(slug="leftover-opid-as-summary", domain="leftover-opid-as-summary-vs-oas-op-summary-required", success=False, name="a6c02c", stack="OpenAPI leftover summary + Java + TS", field="summary", old="operation summary", new="opid as summary leftover only", fail_err="400: leftover operation summary after opid as summary leftover-only", plan="opid as summary leftover-only 400s leftover operation summary. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (opid as summary leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#path-item-object", fetch1_ok="Exclusive op summary 400 leftover opid.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch2_ok="summary is human text, leftover operationId-as-summary fails closed.")),
    (p(slug="oas-parameter-desc-required", domain="oas-parameter-desc-required-vs-leftover-undocumented-param", success=True, name="6b2446", stack="OpenAPI 3.1 description + Go", field="description", old="undocumented param leftover", new="parameter description", fail_err="400: leftover undocumented param leftover after parameter description-only", plan="parameter description-only 400s leftover undocumented param leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (parameter description vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="parameter.description is required here, leftover undocumented fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch2_ok="Exclusive param desc 400 leftover undocumented."),
     p(slug="leftover-undocumented-param", domain="leftover-undocumented-param-vs-oas-parameter-desc-required", success=False, name="a346f1", stack="OpenAPI leftover description + Java + TS", field="description", old="parameter description", new="undocumented param leftover only", fail_err="400: leftover parameter description after undocumented param leftover-only", plan="undocumented param leftover-only 400s leftover parameter description. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (undocumented param leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch1_ok="Exclusive param desc 400 leftover undocumented.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="parameter.description is required here, leftover undocumented fails closed.")),
    (p(slug="oas-request-body-description", domain="oas-request-body-description-vs-leftover-body-no-desc", success=True, name="6b9f3f", stack="OpenAPI 3.1 description + Go", field="description", old="body no desc leftover", new="requestBody description", fail_err="400: leftover body no desc leftover after requestBody description-only", plan="requestBody description-only 400s leftover body no desc leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (requestBody description vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#request-body-object", fetch1_ok="requestBody.description documents the payload, leftover missing fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch2_ok="Exclusive body desc 400 leftover none."),
     p(slug="leftover-body-no-desc", domain="leftover-body-no-desc-vs-oas-request-body-description", success=False, name="ccaf2e", stack="OpenAPI leftover description + Java + TS", field="description", old="requestBody description", new="body no desc leftover only", fail_err="400: leftover requestBody description after body no desc leftover-only", plan="body no desc leftover-only 400s leftover requestBody description. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (body no desc leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch1_ok="Exclusive body desc 400 leftover none.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#request-body-object", fetch2_ok="requestBody.description documents the payload, leftover missing fails closed.")),
    (p(slug="oas-format-time-rfc3339", domain="oas-format-time-rfc3339-vs-leftover-hhmm-time", success=True, name="cbe51d", stack="OpenAPI 3.1 format + Go", field="format", old="hhmm time leftover", new="format time rfc3339", fail_err="400: leftover hhmm time leftover after format time rfc3339-only", plan="format time rfc3339-only 400s leftover hhmm time leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (format time rfc3339 vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/string#dates-and-times", fetch1_ok="format=time is RFC3339, leftover HHMM fails closed.", fetch2="https://datatracker.ietf.org/doc/html/rfc3339", fetch2_ok="Exclusive time 400 leftover hhmm."),
     p(slug="leftover-hhmm-time", domain="leftover-hhmm-time-vs-oas-format-time-rfc3339", success=False, name="3e2fb0", stack="OpenAPI leftover format + Java + TS", field="format", old="format time rfc3339", new="hhmm time leftover only", fail_err="400: leftover format time rfc3339 after hhmm time leftover-only", plan="hhmm time leftover-only 400s leftover format time rfc3339. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (hhmm time leftover leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc3339", fetch1_ok="Exclusive time 400 leftover hhmm.", fetch2="https://json-schema.org/understanding-json-schema/reference/string#dates-and-times", fetch2_ok="format=time is RFC3339, leftover HHMM fails closed.")),
    (p(slug="oas-format-date-rfc3339", domain="oas-format-date-rfc3339-vs-leftover-us-slash-date", success=True, name="fb10f5", stack="OpenAPI 3.1 format + Go", field="format", old="us slash date leftover", new="format date rfc3339", fail_err="400: leftover us slash date leftover after format date rfc3339-only", plan="format date rfc3339-only 400s leftover us slash date leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (format date rfc3339 vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/string#dates-and-times", fetch1_ok="format=date is full-date, leftover US slashes fail closed.", fetch2="https://datatracker.ietf.org/doc/html/rfc3339", fetch2_ok="Exclusive date 400 leftover us slash."),
     p(slug="leftover-us-slash-date", domain="leftover-us-slash-date-vs-oas-format-date-rfc3339", success=False, name="5cc8ff", stack="OpenAPI leftover format + Java + TS", field="format", old="format date rfc3339", new="us slash date leftover only", fail_err="400: leftover format date rfc3339 after us slash date leftover-only", plan="us slash date leftover-only 400s leftover format date rfc3339. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (us slash date leftover leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc3339", fetch1_ok="Exclusive date 400 leftover us slash.", fetch2="https://json-schema.org/understanding-json-schema/reference/string#dates-and-times", fetch2_ok="format=date is full-date, leftover US slashes fail closed.")),
    (p(slug="oas-schema-min-items-n", domain="oas-schema-min-items-n-vs-leftover-empty-array-ok", success=True, name="2ec95f", stack="OpenAPI 3.1 minItems + Go", field="minItems", old="empty array leftover", new="minItems", fail_err="400: leftover empty array leftover after minItems-only", plan="minItems-only 400s leftover empty array leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (minItems vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/array#minitems", fetch1_ok="minItems rejects empty arrays, leftover empty-ok fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive minItems 400 leftover empty array."),
     p(slug="leftover-empty-array-ok", domain="leftover-empty-array-ok-vs-oas-schema-min-items-n", success=False, name="142e2b", stack="OpenAPI leftover minItems + Java + TS", field="minItems", old="minItems", new="empty array leftover only", fail_err="400: leftover minItems after empty array leftover-only", plan="empty array leftover-only 400s leftover minItems. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (empty array leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive minItems 400 leftover empty array.", fetch2="https://json-schema.org/understanding-json-schema/reference/array#minitems", fetch2_ok="minItems rejects empty arrays, leftover empty-ok fails closed.")),
    (p(slug="oas-schema-max-items-n", domain="oas-schema-max-items-n-vs-leftover-unbounded-array-len", success=True, name="d7b123", stack="OpenAPI 3.1 maxItems + Go", field="maxItems", old="unbounded array leftover", new="maxItems", fail_err="400: leftover unbounded array leftover after maxItems-only", plan="maxItems-only 400s leftover unbounded array leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (maxItems vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/array#maxitems", fetch1_ok="maxItems bounds arrays, leftover unbounded fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive maxItems 400 leftover unbounded."),
     p(slug="leftover-unbounded-array-len", domain="leftover-unbounded-array-len-vs-oas-schema-max-items-n", success=False, name="aaa8fd", stack="OpenAPI leftover maxItems + Java + TS", field="maxItems", old="maxItems", new="unbounded array leftover only", fail_err="400: leftover maxItems after unbounded array leftover-only", plan="unbounded array leftover-only 400s leftover maxItems. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (unbounded array leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive maxItems 400 leftover unbounded.", fetch2="https://json-schema.org/understanding-json-schema/reference/array#maxitems", fetch2_ok="maxItems bounds arrays, leftover unbounded fails closed.")),
    (p(slug="oas-xml-wrapped-array-true", domain="oas-xml-wrapped-array-true-vs-leftover-xml-array-unwrapped", success=True, name="c4d4ee", stack="OpenAPI 3.1 wrapped + Go", field="wrapped", old="unwrapped xml leftover", new="xml wrapped true", fail_err="415: leftover unwrapped xml leftover after xml wrapped true-only", plan="xml wrapped true-only 415s leftover unwrapped xml leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (xml wrapped true vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#xml-object", fetch1_ok="xml.wrapped true wraps arrays, leftover unwrapped fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive xml wrapped 415 leftover unwrapped."),
     p(slug="leftover-xml-array-unwrapped", domain="leftover-xml-array-unwrapped-vs-oas-xml-wrapped-array-true", success=False, name="d6368d", stack="OpenAPI leftover wrapped + Java + TS", field="wrapped", old="xml wrapped true", new="unwrapped xml leftover only", fail_err="415: leftover xml wrapped true after unwrapped xml leftover-only", plan="unwrapped xml leftover-only 415s leftover xml wrapped true. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (unwrapped xml leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive xml wrapped 415 leftover unwrapped.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#xml-object", fetch2_ok="xml.wrapped true wraps arrays, leftover unwrapped fails closed.")),
    (p(slug="oas-components-links-reuse", domain="oas-components-links-reuse-vs-leftover-inline-link-only", success=True, name="009909", stack="OpenAPI 3.1 links + Go", field="links", old="inline link leftover", new="components links reuse", fail_err="400: leftover inline link leftover after components links reuse-only", plan="components links reuse-only 400s leftover inline link leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (components links reuse vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#components-object", fetch1_ok="components.links reuse Link Objects, leftover inline-only is not that.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#link-object", fetch2_ok="Exclusive components links 400 leftover inline."),
     p(slug="leftover-inline-link-only", domain="leftover-inline-link-only-vs-oas-components-links-reuse", success=False, name="ab3c52", stack="OpenAPI leftover links + Java + TS", field="links", old="components links reuse", new="inline link leftover only", fail_err="400: leftover components links reuse after inline link leftover-only", plan="inline link leftover-only 400s leftover components links reuse. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (inline link leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#link-object", fetch1_ok="Exclusive components links 400 leftover inline.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#components-object", fetch2_ok="components.links reuse Link Objects, leftover inline-only is not that.")),
    (p(slug="oas-op-security-override", domain="oas-op-security-override-vs-leftover-root-security-only", success=True, name="9cf98f", stack="OpenAPI 3.1 security + Go", field="security", old="root security leftover", new="operation security override", fail_err="401: leftover root security leftover after operation security override-only", plan="operation security override-only 401s leftover root security leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (operation security override vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch1_ok="operation.security overrides root, leftover root-only fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#security-requirement-object", fetch2_ok="Exclusive op security 401 leftover root."),
     p(slug="leftover-root-security-only", domain="leftover-root-security-only-vs-oas-op-security-override", success=False, name="7f4e4b", stack="OpenAPI leftover security + Java + TS", field="security", old="operation security override", new="root security leftover only", fail_err="401: leftover operation security override after root security leftover-only", plan="root security leftover-only 401s leftover operation security override. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (root security leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#security-requirement-object", fetch1_ok="Exclusive op security 401 leftover root.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch2_ok="operation.security overrides root, leftover root-only fails closed.")),
    (p(slug="oas-header-content-media", domain="oas-header-content-media-vs-leftover-header-schema-only", success=True, name="c2781e", stack="OpenAPI 3.1 content + Go", field="content", old="header schema leftover", new="header content media", fail_err="400: leftover header schema leftover after header content media-only", plan="header content media-only 400s leftover header schema leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (header content media vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch1_ok="header.content is mutually exclusive with schema, leftover schema-only fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch2_ok="Exclusive header content 400 leftover schema."),
     p(slug="leftover-header-schema-only", domain="leftover-header-schema-only-vs-oas-header-content-media", success=False, name="6e91e5", stack="OpenAPI leftover content + Java + TS", field="content", old="header content media", new="header schema leftover only", fail_err="400: leftover header content media after header schema leftover-only", plan="header schema leftover-only 400s leftover header content media. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (header schema leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch1_ok="Exclusive header content 400 leftover schema.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch2_ok="header.content is mutually exclusive with schema, leftover schema-only fails closed.")),
    (p(slug="oas-cookie-required-true", domain="oas-cookie-required-true-vs-leftover-optional-cookie", success=True, name="5aea75", stack="OpenAPI 3.1 required + Go", field="required", old="optional cookie leftover", new="cookie required true", fail_err="400: leftover optional cookie leftover after cookie required true-only", plan="cookie required true-only 400s leftover optional cookie leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (cookie required true vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="required cookie parameters cannot be leftover optional.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch2_ok="Exclusive cookie required 400 leftover optional."),
     p(slug="leftover-optional-cookie", domain="leftover-optional-cookie-vs-oas-cookie-required-true", success=False, name="a5213a", stack="OpenAPI leftover required + Java + TS", field="required", old="cookie required true", new="optional cookie leftover only", fail_err="400: leftover cookie required true after optional cookie leftover-only", plan="optional cookie leftover-only 400s leftover cookie required true. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (optional cookie leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch1_ok="Exclusive cookie required 400 leftover optional.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="required cookie parameters cannot be leftover optional.")),
    (p(slug="oas-options-method-explicit", domain="oas-options-method-explicit-vs-leftover-implicit-options", success=True, name="f516c3", stack="OpenAPI 3.1 options + Go", field="options", old="implicit OPTIONS leftover", new="OPTIONS method", fail_err="400: leftover implicit OPTIONS leftover after OPTIONS method-only", plan="OPTIONS method-only 400s leftover implicit OPTIONS leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (OPTIONS method vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#path-item-object", fetch1_ok="OPTIONS is a distinct operation, leftover implicit fails closed.", fetch2="https://datatracker.ietf.org/doc/html/rfc9110#name-options", fetch2_ok="Exclusive OPTIONS 400 leftover implicit."),
     p(slug="leftover-implicit-options", domain="leftover-implicit-options-vs-oas-options-method-explicit", success=False, name="1781fb", stack="OpenAPI leftover options + Java + TS", field="options", old="OPTIONS method", new="implicit OPTIONS leftover only", fail_err="400: leftover OPTIONS method after implicit OPTIONS leftover-only", plan="implicit OPTIONS leftover-only 400s leftover OPTIONS method. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (implicit OPTIONS leftover leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc9110#name-options", fetch1_ok="Exclusive OPTIONS 400 leftover implicit.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#path-item-object", fetch2_ok="OPTIONS is a distinct operation, leftover implicit fails closed.")),
    (p(slug="oas-schema-writeonly-omit-read", domain="oas-schema-writeonly-omit-read-vs-leftover-echo-writeonly-on-read", success=True, name="4d28b3", stack="OpenAPI 3.1 writeOnly + Go", field="writeOnly", old="echo writeOnly leftover", new="writeOnly omit read", fail_err="400: leftover echo writeOnly leftover after writeOnly omit read-only", plan="writeOnly omit read-only 400s leftover echo writeOnly leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (writeOnly omit read vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="writeOnly must be omitted on read, leftover echo fails closed.", fetch2="https://json-schema.org/understanding-json-schema/reference/object", fetch2_ok="Exclusive writeOnly omit 400 leftover echo."),
     p(slug="leftover-echo-writeonly-on-read", domain="leftover-echo-writeonly-on-read-vs-oas-schema-writeonly-omit-read", success=False, name="8f20dd", stack="OpenAPI leftover writeOnly + Java + TS", field="writeOnly", old="writeOnly omit read", new="echo writeOnly leftover only", fail_err="400: leftover writeOnly omit read after echo writeOnly leftover-only", plan="echo writeOnly leftover-only 400s leftover writeOnly omit read. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (echo writeOnly leftover leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/object", fetch1_ok="Exclusive writeOnly omit 400 leftover echo.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="writeOnly must be omitted on read, leftover echo fails closed.")),
    (p(slug="oas-format-password-mask", domain="oas-format-password-mask-vs-leftover-plaintext-secret", success=True, name="d3a05b", stack="OpenAPI 3.1 format + Go", field="format", old="plaintext secret leftover", new="format password", fail_err="400: leftover plaintext secret leftover after format password-only", plan="format password-only 400s leftover plaintext secret leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (format password vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="format=password is a hint to mask, leftover plaintext fails closed.", fetch2="https://json-schema.org/understanding-json-schema/reference/string", fetch2_ok="Exclusive password 400 leftover plaintext."),
     p(slug="leftover-plaintext-secret", domain="leftover-plaintext-secret-vs-oas-format-password-mask", success=False, name="aef8cc", stack="OpenAPI leftover format + Java + TS", field="format", old="format password", new="plaintext secret leftover only", fail_err="400: leftover format password after plaintext secret leftover-only", plan="plaintext secret leftover-only 400s leftover format password. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (plaintext secret leftover leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/string", fetch1_ok="Exclusive password 400 leftover plaintext.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="format=password is a hint to mask, leftover plaintext fails closed.")),
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
    print(json.dumps({"round": round_n, "idx": idx, "ids": [e1["id"], e2["id"]], "catalog": "r4294"}))


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
