#!/usr/bin/env python3
"""Unique OpenAPI-drift ACM catalog r4262. Fast slug load."""
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
    (p(slug="oas-json-schema-id-uri", domain="oas-json-schema-id-uri-vs-leftover-unanchored-schema", success=True, name="7447ea", stack="OpenAPI 3.1 $id + Go", field="$id", old="unanchored leftover", new="schema $id uri", fail_err="400: leftover unanchored leftover after schema $id uri-only", plan="schema $id uri-only 400s leftover unanchored leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (schema $id uri vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/schema#id", fetch1_ok="$id identifies the schema resource, leftover unanchored fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive $id 400 leftover unanchored."),
     p(slug="leftover-unanchored-schema", domain="leftover-unanchored-schema-vs-oas-json-schema-id-uri", success=False, name="8de4f9", stack="OpenAPI leftover $id + Java + TS", field="$id", old="schema $id uri", new="unanchored leftover only", fail_err="400: leftover schema $id uri after unanchored leftover-only", plan="unanchored leftover-only 400s leftover schema $id uri. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (unanchored leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive $id 400 leftover unanchored.", fetch2="https://json-schema.org/understanding-json-schema/reference/schema#id", fetch2_ok="$id identifies the schema resource, leftover unanchored fails closed.")),
    (p(slug="oas-json-schema-schema-uri", domain="oas-json-schema-schema-uri-vs-leftover-implicit-schema-draft", success=True, name="49d568", stack="OpenAPI 3.1 $schema + Go", field="$schema", old="implicit draft leftover", new="$schema uri", fail_err="400: leftover implicit draft leftover after $schema uri-only", plan="$schema uri-only 400s leftover implicit draft leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv ($schema uri vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/schema#schema", fetch1_ok="$schema names the dialect, leftover implicit fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive $schema 400 leftover implicit."),
     p(slug="leftover-implicit-schema-draft", domain="leftover-implicit-schema-draft-vs-oas-json-schema-schema-uri", success=False, name="fa5fc3", stack="OpenAPI leftover $schema + Java + TS", field="$schema", old="$schema uri", new="implicit draft leftover only", fail_err="400: leftover $schema uri after implicit draft leftover-only", plan="implicit draft leftover-only 400s leftover $schema uri. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (implicit draft leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive $schema 400 leftover implicit.", fetch2="https://json-schema.org/understanding-json-schema/reference/schema#schema", fetch2_ok="$schema names the dialect, leftover implicit fails closed.")),
    (p(slug="oas-operation-deprecated-flag", domain="oas-operation-deprecated-flag-vs-leftover-ship-deprecated-op", success=True, name="900d45", stack="OpenAPI 3.1 deprecated + Go", field="deprecated", old="ship deprecated op leftover", new="operation deprecated", fail_err="400: leftover ship deprecated op leftover after operation deprecated-only", plan="operation deprecated-only 400s leftover ship deprecated op leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (operation deprecated vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch1_ok="deprecated operations must not ship as live, leftover still-shipped fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#path-item-object", fetch2_ok="Exclusive op deprecated 400 leftover live op."),
     p(slug="leftover-ship-deprecated-op", domain="leftover-ship-deprecated-op-vs-oas-operation-deprecated-flag", success=False, name="9a23ff", stack="OpenAPI leftover deprecated + Java + TS", field="deprecated", old="operation deprecated", new="ship deprecated op leftover only", fail_err="400: leftover operation deprecated after ship deprecated op leftover-only", plan="ship deprecated op leftover-only 400s leftover operation deprecated. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (ship deprecated op leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#path-item-object", fetch1_ok="Exclusive op deprecated 400 leftover live op.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch2_ok="deprecated operations must not ship as live, leftover still-shipped fails closed.")),
    (p(slug="oas-response-desc-required", domain="oas-response-desc-required-vs-leftover-blank-response-desc", success=True, name="79914f", stack="OpenAPI 3.1 description + Go", field="description", old="blank response leftover", new="response description", fail_err="400: leftover blank response leftover after response description-only", plan="response description-only 400s leftover blank response leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (response description vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#response-object", fetch1_ok="response.description is required, leftover blank fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#responses-object", fetch2_ok="Exclusive response desc 400 leftover blank."),
     p(slug="leftover-blank-response-desc", domain="leftover-blank-response-desc-vs-oas-response-desc-required", success=False, name="ac1b83", stack="OpenAPI leftover description + Java + TS", field="description", old="response description", new="blank response leftover only", fail_err="400: leftover response description after blank response leftover-only", plan="blank response leftover-only 400s leftover response description. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (blank response leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#responses-object", fetch1_ok="Exclusive response desc 400 leftover blank.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#response-object", fetch2_ok="response.description is required, leftover blank fails closed.")),
    (p(slug="oas-info-desc-required", domain="oas-info-desc-required-vs-leftover-empty-info-desc", success=True, name="8e2601", stack="OpenAPI 3.1 description + Go", field="description", old="empty info leftover", new="info description", fail_err="400: leftover empty info leftover after info description-only", plan="info description-only 400s leftover empty info leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (info description vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#info-object", fetch1_ok="info.description documents the API, leftover empty fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#openapi-object", fetch2_ok="Exclusive info desc 400 leftover empty."),
     p(slug="leftover-empty-info-desc", domain="leftover-empty-info-desc-vs-oas-info-desc-required", success=False, name="921f56", stack="OpenAPI leftover description + Java + TS", field="description", old="info description", new="empty info leftover only", fail_err="400: leftover info description after empty info leftover-only", plan="empty info leftover-only 400s leftover info description. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (empty info leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#openapi-object", fetch1_ok="Exclusive info desc 400 leftover empty.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#info-object", fetch2_ok="info.description documents the API, leftover empty fails closed.")),
    (p(slug="oas-contact-name-required", domain="oas-contact-name-required-vs-leftover-email-only-contact", success=True, name="516328", stack="OpenAPI 3.1 name + Go", field="name", old="email only leftover", new="contact name", fail_err="400: leftover email only leftover after contact name-only", plan="contact name-only 400s leftover email only leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (contact name vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#contact-object", fetch1_ok="contact.name is required with contact, leftover email-only fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#info-object", fetch2_ok="Exclusive contact name 400 leftover email only."),
     p(slug="leftover-email-only-contact", domain="leftover-email-only-contact-vs-oas-contact-name-required", success=False, name="da7f64", stack="OpenAPI leftover name + Java + TS", field="name", old="contact name", new="email only leftover only", fail_err="400: leftover contact name after email only leftover-only", plan="email only leftover-only 400s leftover contact name. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (email only leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#info-object", fetch1_ok="Exclusive contact name 400 leftover email only.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#contact-object", fetch2_ok="contact.name is required with contact, leftover email-only fails closed.")),
    (p(slug="oas-license-url-https", domain="oas-license-url-https-vs-leftover-license-name-only", success=True, name="731457", stack="OpenAPI 3.1 url + Go", field="url", old="license name leftover", new="license url https", fail_err="400: leftover license name leftover after license url https-only", plan="license url https-only 400s leftover license name leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (license url https vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#license-object", fetch1_ok="license.url must be https when present, leftover name-only fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#info-object", fetch2_ok="Exclusive license url 400 leftover name only."),
     p(slug="leftover-license-name-only", domain="leftover-license-name-only-vs-oas-license-url-https", success=False, name="544c0e", stack="OpenAPI leftover url + Java + TS", field="url", old="license url https", new="license name leftover only", fail_err="400: leftover license url https after license name leftover-only", plan="license name leftover-only 400s leftover license url https. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (license name leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#info-object", fetch1_ok="Exclusive license url 400 leftover name only.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#license-object", fetch2_ok="license.url must be https when present, leftover name-only fails closed.")),
    (p(slug="oas-server-desc-required", domain="oas-server-desc-required-vs-leftover-bare-server-url", success=True, name="8f713f", stack="OpenAPI 3.1 description + Go", field="description", old="bare server leftover", new="server description", fail_err="400: leftover bare server leftover after server description-only", plan="server description-only 400s leftover bare server leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (server description vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#server-object", fetch1_ok="server.description documents the target, leftover bare url fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#oasServers", fetch2_ok="Exclusive server desc 400 leftover bare."),
     p(slug="leftover-bare-server-url", domain="leftover-bare-server-url-vs-oas-server-desc-required", success=False, name="c4f7ed", stack="OpenAPI leftover description + Java + TS", field="description", old="server description", new="bare server leftover only", fail_err="400: leftover server description after bare server leftover-only", plan="bare server leftover-only 400s leftover server description. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (bare server leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#oasServers", fetch1_ok="Exclusive server desc 400 leftover bare.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#server-object", fetch2_ok="server.description documents the target, leftover bare url fails closed.")),
    (p(slug="oas-path-item-summary-req", domain="oas-path-item-summary-req-vs-leftover-path-no-summary", success=True, name="f1d2c9", stack="OpenAPI 3.1 summary + Go", field="summary", old="path no summary leftover", new="pathItem summary", fail_err="400: leftover path no summary leftover after pathItem summary-only", plan="pathItem summary-only 400s leftover path no summary leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (pathItem summary vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#path-item-object", fetch1_ok="pathItem.summary is not leftover unnamed paths.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#paths-object", fetch2_ok="Exclusive path summary 400 leftover none."),
     p(slug="leftover-path-no-summary", domain="leftover-path-no-summary-vs-oas-path-item-summary-req", success=False, name="2c5035", stack="OpenAPI leftover summary + Java + TS", field="summary", old="pathItem summary", new="path no summary leftover only", fail_err="400: leftover pathItem summary after path no summary leftover-only", plan="path no summary leftover-only 400s leftover pathItem summary. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (path no summary leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#paths-object", fetch1_ok="Exclusive path summary 400 leftover none.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#path-item-object", fetch2_ok="pathItem.summary is not leftover unnamed paths.")),
    (p(slug="oas-pathitem-desc-required", domain="oas-pathitem-desc-required-vs-leftover-path-no-desc", success=True, name="ecd27f", stack="OpenAPI 3.1 description + Go", field="description", old="path no desc leftover", new="pathItem description", fail_err="400: leftover path no desc leftover after pathItem description-only", plan="pathItem description-only 400s leftover path no desc leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (pathItem description vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#path-item-object", fetch1_ok="pathItem.description documents the resource, leftover missing fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#paths-object", fetch2_ok="Exclusive path desc 400 leftover none."),
     p(slug="leftover-path-no-desc", domain="leftover-path-no-desc-vs-oas-pathitem-desc-required", success=False, name="001b3d", stack="OpenAPI leftover description + Java + TS", field="description", old="pathItem description", new="path no desc leftover only", fail_err="400: leftover pathItem description after path no desc leftover-only", plan="path no desc leftover-only 400s leftover pathItem description. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (path no desc leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#paths-object", fetch1_ok="Exclusive path desc 400 leftover none.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#path-item-object", fetch2_ok="pathItem.description documents the resource, leftover missing fails closed.")),
    (p(slug="oas-operation-tags-nonempty", domain="oas-operation-tags-nonempty-vs-leftover-untagged-operation", success=True, name="be3f53", stack="OpenAPI 3.1 tags + Go", field="tags", old="untagged leftover", new="operation tags nonempty", fail_err="400: leftover untagged leftover after operation tags nonempty-only", plan="operation tags nonempty-only 400s leftover untagged leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (operation tags nonempty vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch1_ok="operation.tags must be nonempty, leftover untagged fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#tag-object", fetch2_ok="Exclusive op tags 400 leftover untagged."),
     p(slug="leftover-untagged-operation", domain="leftover-untagged-operation-vs-oas-operation-tags-nonempty", success=False, name="0d3d99", stack="OpenAPI leftover tags + Java + TS", field="tags", old="operation tags nonempty", new="untagged leftover only", fail_err="400: leftover operation tags nonempty after untagged leftover-only", plan="untagged leftover-only 400s leftover operation tags nonempty. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (untagged leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#tag-object", fetch1_ok="Exclusive op tags 400 leftover untagged.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch2_ok="operation.tags must be nonempty, leftover untagged fails closed.")),
    (p(slug="oas-jsonschema-examples-arr", domain="oas-jsonschema-examples-arr-vs-leftover-single-example-only", success=True, name="03abbc", stack="OpenAPI 3.1 examples + Go", field="examples", old="single example leftover", new="schema examples array", fail_err="400: leftover single example leftover after schema examples array-only", plan="schema examples array-only 400s leftover single example leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (schema examples array vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/generic#annotation", fetch1_ok="JSON Schema examples is an array, leftover single example fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive examples array 400 leftover single."),
     p(slug="leftover-single-example-only", domain="leftover-single-example-only-vs-oas-jsonschema-examples-arr", success=False, name="7f3b87", stack="OpenAPI leftover examples + Java + TS", field="examples", old="schema examples array", new="single example leftover only", fail_err="400: leftover schema examples array after single example leftover-only", plan="single example leftover-only 400s leftover schema examples array. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (single example leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive examples array 400 leftover single.", fetch2="https://json-schema.org/understanding-json-schema/reference/generic#annotation", fetch2_ok="JSON Schema examples is an array, leftover single example fails closed.")),
    (p(slug="oas-schema-not-keyword", domain="oas-schema-not-keyword-vs-leftover-enum-exclusion", success=True, name="e7094e", stack="OpenAPI 3.1 not + Go", field="not", old="enum exclusion leftover", new="schema not", fail_err="400: leftover enum exclusion leftover after schema not-only", plan="schema not-only 400s leftover enum exclusion leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (schema not vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/combining#not", fetch1_ok="not negates a schema, leftover enum-exclusion is not that.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive not 400 leftover enum exclusion."),
     p(slug="leftover-enum-exclusion", domain="leftover-enum-exclusion-vs-oas-schema-not-keyword", success=False, name="2e5444", stack="OpenAPI leftover not + Java + TS", field="not", old="schema not", new="enum exclusion leftover only", fail_err="400: leftover schema not after enum exclusion leftover-only", plan="enum exclusion leftover-only 400s leftover schema not. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (enum exclusion leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive not 400 leftover enum exclusion.", fetch2="https://json-schema.org/understanding-json-schema/reference/combining#not", fetch2_ok="not negates a schema, leftover enum-exclusion is not that.")),
    (p(slug="oas-media-schema-required", domain="oas-media-schema-required-vs-leftover-schemaless-media", success=True, name="7841cd", stack="OpenAPI 3.1 schema + Go", field="schema", old="schemaless media leftover", new="media schema required", fail_err="400: leftover schemaless media leftover after media schema required-only", plan="media schema required-only 400s leftover schemaless media leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (media schema required vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch1_ok="media.schema is required, leftover schemaless fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive media schema 400 leftover schemaless."),
     p(slug="leftover-schemaless-media", domain="leftover-schemaless-media-vs-oas-media-schema-required", success=False, name="5ecb73", stack="OpenAPI leftover schema + Java + TS", field="schema", old="media schema required", new="schemaless media leftover only", fail_err="400: leftover media schema required after schemaless media leftover-only", plan="schemaless media leftover-only 400s leftover media schema required. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (schemaless media leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive media schema 400 leftover schemaless.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch2_ok="media.schema is required, leftover schemaless fails closed.")),
    (p(slug="oas-header-schema-required", domain="oas-header-schema-required-vs-leftover-header-no-schema", success=True, name="3ab7cd", stack="OpenAPI 3.1 schema + Go", field="schema", old="header no schema leftover", new="header schema required", fail_err="400: leftover header no schema leftover after header schema required-only", plan="header schema required-only 400s leftover header no schema leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (header schema required vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch1_ok="header.schema or content is required, leftover untyped fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="Exclusive header schema 400 leftover untyped."),
     p(slug="leftover-header-no-schema", domain="leftover-header-no-schema-vs-oas-header-schema-required", success=False, name="875500", stack="OpenAPI leftover schema + Java + TS", field="schema", old="header schema required", new="header no schema leftover only", fail_err="400: leftover header schema required after header no schema leftover-only", plan="header no schema leftover-only 400s leftover header schema required. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (header no schema leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="Exclusive header schema 400 leftover untyped.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch2_ok="header.schema or content is required, leftover untyped fails closed.")),
    (p(slug="oas-parameter-schema-or-content", domain="oas-parameter-schema-or-content-vs-leftover-bare-parameter", success=True, name="ff81c3", stack="OpenAPI 3.1 schema + Go", field="schema", old="bare parameter leftover", new="parameter schema or content", fail_err="400: leftover bare parameter leftover after parameter schema or content-only", plan="parameter schema or content-only 400s leftover bare parameter leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (parameter schema or content vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="A parameter needs schema or content, leftover bare fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch2_ok="Exclusive param schema 400 leftover bare."),
     p(slug="leftover-bare-parameter", domain="leftover-bare-parameter-vs-oas-parameter-schema-or-content", success=False, name="682b14", stack="OpenAPI leftover schema + Java + TS", field="schema", old="parameter schema or content", new="bare parameter leftover only", fail_err="400: leftover parameter schema or content after bare parameter leftover-only", plan="bare parameter leftover-only 400s leftover parameter schema or content. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (bare parameter leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch1_ok="Exclusive param schema 400 leftover bare.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="A parameter needs schema or content, leftover bare fails closed.")),
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
    print(json.dumps({"round": round_n, "idx": idx, "ids": [e1["id"], e2["id"]], "catalog": "r4262"}))


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
