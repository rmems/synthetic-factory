#!/usr/bin/env python3
"""Unique OpenAPI-drift ACM catalog r4422. Fast slug load."""
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
    (p(slug="oas-webhook-delete-op", domain="oas-webhook-delete-op-vs-leftover-webhook-post-forced", success=True, name="c4e297", stack="OpenAPI 3.1 delete + Go", field="delete", old="webhook POST leftover", new="webhook DELETE", fail_err="400: leftover webhook POST leftover after webhook DELETE-only", plan="webhook DELETE-only 400s leftover webhook POST leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (webhook DELETE vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#oasWebhooks", fetch1_ok="Webhook DELETE is distinct, leftover POST-forced fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#path-item-object", fetch2_ok="Exclusive webhook DELETE 400 leftover POST."),
     p(slug="leftover-webhook-post-forced", domain="leftover-webhook-post-forced-vs-oas-webhook-delete-op", success=False, name="1a39ed", stack="OpenAPI leftover delete + Java + TS", field="delete", old="webhook DELETE", new="webhook POST leftover only", fail_err="400: leftover webhook DELETE after webhook POST leftover-only", plan="webhook POST leftover-only 400s leftover webhook DELETE. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (webhook POST leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#path-item-object", fetch1_ok="Exclusive webhook DELETE 400 leftover POST.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#oasWebhooks", fetch2_ok="Webhook DELETE is distinct, leftover POST-forced fails closed.")),
    (p(slug="oas-path-item-parameters", domain="oas-path-item-parameters-vs-leftover-op-params-only", success=True, name="672564", stack="OpenAPI 3.1 parameters + Go", field="parameters", old="op params leftover", new="pathItem parameters", fail_err="400: leftover op params leftover after pathItem parameters-only", plan="pathItem parameters-only 400s leftover op params leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (pathItem parameters vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#path-item-object", fetch1_ok="pathItem.parameters apply to all ops, leftover op-only fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="Exclusive path params 400 leftover op only."),
     p(slug="leftover-op-params-only", domain="leftover-op-params-only-vs-oas-path-item-parameters", success=False, name="417d17", stack="OpenAPI leftover parameters + Java + TS", field="parameters", old="pathItem parameters", new="op params leftover only", fail_err="400: leftover pathItem parameters after op params leftover-only", plan="op params leftover-only 400s leftover pathItem parameters. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (op params leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="Exclusive path params 400 leftover op only.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#path-item-object", fetch2_ok="pathItem.parameters apply to all ops, leftover op-only fails closed.")),
    (p(slug="oas-op-parameters-override", domain="oas-op-parameters-override-vs-leftover-path-params-only", success=True, name="010b4a", stack="OpenAPI 3.1 parameters + Go", field="parameters", old="path params leftover", new="operation parameters override", fail_err="400: leftover path params leftover after operation parameters override-only", plan="operation parameters override-only 400s leftover path params leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (operation parameters override vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch1_ok="operation.parameters override path, leftover path-only fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="Exclusive op params 400 leftover path only."),
     p(slug="leftover-path-params-only", domain="leftover-path-params-only-vs-oas-op-parameters-override", success=False, name="23a294", stack="OpenAPI leftover parameters + Java + TS", field="parameters", old="operation parameters override", new="path params leftover only", fail_err="400: leftover operation parameters override after path params leftover-only", plan="path params leftover-only 400s leftover operation parameters override. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (path params leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="Exclusive op params 400 leftover path only.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch2_ok="operation.parameters override path, leftover path-only fails closed.")),
    (p(slug="oas-response-default-catch", domain="oas-response-default-catch-vs-leftover-no-default-response", success=True, name="81b7d0", stack="OpenAPI 3.1 default + Go", field="default", old="listed status leftover", new="response default", fail_err="400: leftover listed status leftover after response default-only", plan="response default-only 400s leftover listed status leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (response default vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#responses-object", fetch1_ok="default catches unlisted statuses, leftover listed-only fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#response-object", fetch2_ok="Exclusive default response 400 leftover listed."),
     p(slug="leftover-no-default-response", domain="leftover-no-default-response-vs-oas-response-default-catch", success=False, name="2c96ee", stack="OpenAPI leftover default + Java + TS", field="default", old="response default", new="listed status leftover only", fail_err="400: leftover response default after listed status leftover-only", plan="listed status leftover-only 400s leftover response default. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (listed status leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#response-object", fetch1_ok="Exclusive default response 400 leftover listed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#responses-object", fetch2_ok="default catches unlisted statuses, leftover listed-only fails closed.")),
    (p(slug="oas-status-201-location", domain="oas-status-201-location-vs-leftover-created-no-location", success=True, name="b15259", stack="OpenAPI 3.1 headers + Go", field="headers", old="201 no location leftover", new="201 Location header", fail_err="400: leftover 201 no location leftover after 201 Location header-only", plan="201 Location header-only 400s leftover 201 no location leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (201 Location header vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#response-object", fetch1_ok="201 SHOULD include Location, leftover missing fails closed.", fetch2="https://datatracker.ietf.org/doc/html/rfc9110#name-201-created", fetch2_ok="Exclusive 201 Location 400 leftover none."),
     p(slug="leftover-created-no-location", domain="leftover-created-no-location-vs-oas-status-201-location", success=False, name="b7dc47", stack="OpenAPI leftover headers + Java + TS", field="headers", old="201 Location header", new="201 no location leftover only", fail_err="400: leftover 201 Location header after 201 no location leftover-only", plan="201 no location leftover-only 400s leftover 201 Location header. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (201 no location leftover leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc9110#name-201-created", fetch1_ok="Exclusive 201 Location 400 leftover none.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#response-object", fetch2_ok="201 SHOULD include Location, leftover missing fails closed.")),
    (p(slug="oas-status-202-accepted", domain="oas-status-202-accepted-vs-leftover-202-with-entity-body", success=True, name="97656d", stack="OpenAPI 3.1 content + Go", field="content", old="202 entity leftover", new="202 accepted empty", fail_err="400: leftover 202 entity leftover after 202 accepted empty-only", plan="202 accepted empty-only 400s leftover 202 entity leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (202 accepted empty vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#response-object", fetch1_ok="202 accepted here has no entity, leftover body fails closed.", fetch2="https://datatracker.ietf.org/doc/html/rfc9110#name-202-accepted", fetch2_ok="Exclusive 202 empty 400 leftover entity."),
     p(slug="leftover-202-with-entity-body", domain="leftover-202-with-entity-body-vs-oas-status-202-accepted", success=False, name="bb1427", stack="OpenAPI leftover content + Java + TS", field="content", old="202 accepted empty", new="202 entity leftover only", fail_err="400: leftover 202 accepted empty after 202 entity leftover-only", plan="202 entity leftover-only 400s leftover 202 accepted empty. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (202 entity leftover leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc9110#name-202-accepted", fetch1_ok="Exclusive 202 empty 400 leftover entity.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#response-object", fetch2_ok="202 accepted here has no entity, leftover body fails closed.")),
    (p(slug="oas-status-409-conflict", domain="oas-status-409-conflict-vs-leftover-400-as-conflict", success=True, name="dad4a0", stack="OpenAPI 3.1 409 + Go", field="409", old="400 as conflict leftover", new="409 conflict", fail_err="409: leftover 400 as conflict leftover after 409 conflict-only", plan="409 conflict-only 409s leftover 400 as conflict leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (409 conflict vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#responses-object", fetch1_ok="409 is conflict, leftover 400-as-conflict fails closed.", fetch2="https://datatracker.ietf.org/doc/html/rfc9110#name-409-conflict", fetch2_ok="Exclusive 409  leftover 400."),
     p(slug="leftover-400-as-conflict", domain="leftover-400-as-conflict-vs-oas-status-409-conflict", success=False, name="4ea784", stack="OpenAPI leftover 409 + Java + TS", field="409", old="409 conflict", new="400 as conflict leftover only", fail_err="409: leftover 409 conflict after 400 as conflict leftover-only", plan="400 as conflict leftover-only 409s leftover 409 conflict. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (400 as conflict leftover leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc9110#name-409-conflict", fetch1_ok="Exclusive 409  leftover 400.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#responses-object", fetch2_ok="409 is conflict, leftover 400-as-conflict fails closed.")),
    (p(slug="oas-status-410-gone", domain="oas-status-410-gone-vs-leftover-404-as-gone", success=True, name="e54529", stack="OpenAPI 3.1 410 + Go", field="410", old="404 as gone leftover", new="410 gone", fail_err="410: leftover 404 as gone leftover after 410 gone-only", plan="410 gone-only 410s leftover 404 as gone leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (410 gone vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#responses-object", fetch1_ok="410 is gone, leftover 404-as-gone fails closed.", fetch2="https://datatracker.ietf.org/doc/html/rfc9110#name-410-gone", fetch2_ok="Exclusive 410 leftover 404."),
     p(slug="leftover-404-as-gone", domain="leftover-404-as-gone-vs-oas-status-410-gone", success=False, name="580ded", stack="OpenAPI leftover 410 + Java + TS", field="410", old="410 gone", new="404 as gone leftover only", fail_err="410: leftover 410 gone after 404 as gone leftover-only", plan="404 as gone leftover-only 410s leftover 410 gone. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (404 as gone leftover leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc9110#name-410-gone", fetch1_ok="Exclusive 410 leftover 404.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#responses-object", fetch2_ok="410 is gone, leftover 404-as-gone fails closed.")),
    (p(slug="oas-status-415-unsupported", domain="oas-status-415-unsupported-vs-leftover-400-as-unsupported", success=True, name="e52769", stack="OpenAPI 3.1 415 + Go", field="415", old="400 as unsupported leftover", new="415 unsupported media", fail_err="415: leftover 400 as unsupported leftover after 415 unsupported media-only", plan="415 unsupported media-only 415s leftover 400 as unsupported leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (415 unsupported media vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#responses-object", fetch1_ok="415 is unsupported media, leftover 400-as-415 fails closed.", fetch2="https://datatracker.ietf.org/doc/html/rfc9110#name-415-unsupported-media-type", fetch2_ok="Exclusive 415 leftover 400."),
     p(slug="leftover-400-as-unsupported", domain="leftover-400-as-unsupported-vs-oas-status-415-unsupported", success=False, name="c27aae", stack="OpenAPI leftover 415 + Java + TS", field="415", old="415 unsupported media", new="400 as unsupported leftover only", fail_err="415: leftover 415 unsupported media after 400 as unsupported leftover-only", plan="400 as unsupported leftover-only 415s leftover 415 unsupported media. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (400 as unsupported leftover leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc9110#name-415-unsupported-media-type", fetch1_ok="Exclusive 415 leftover 400.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#responses-object", fetch2_ok="415 is unsupported media, leftover 400-as-415 fails closed.")),
    (p(slug="oas-status-429-problem", domain="oas-status-429-problem-vs-leftover-503-as-ratelimit", success=True, name="beaf59", stack="OpenAPI 3.1 429 + Go", field="429", old="503 as ratelimit leftover", new="429 problem details", fail_err="429: leftover 503 as ratelimit leftover after 429 problem details-only", plan="429 problem details-only 429s leftover 503 as ratelimit leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (429 problem details vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#response-object", fetch1_ok="429 is rate limit, leftover 503-as-429 fails closed.", fetch2="https://datatracker.ietf.org/doc/html/rfc6585#section-4", fetch2_ok="Exclusive 429 leftover 503."),
     p(slug="leftover-503-as-ratelimit", domain="leftover-503-as-ratelimit-vs-oas-status-429-problem", success=False, name="b65315", stack="OpenAPI leftover 429 + Java + TS", field="429", old="429 problem details", new="503 as ratelimit leftover only", fail_err="429: leftover 429 problem details after 503 as ratelimit leftover-only", plan="503 as ratelimit leftover-only 429s leftover 429 problem details. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (503 as ratelimit leftover leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc6585#section-4", fetch1_ok="Exclusive 429 leftover 503.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#response-object", fetch2_ok="429 is rate limit, leftover 503-as-429 fails closed.")),
    (p(slug="oas-problem-details-json", domain="oas-problem-details-json-vs-leftover-plaintext-error", success=True, name="3ebdd3", stack="OpenAPI 3.1 content + Go", field="content", old="plaintext error leftover", new="problem+json", fail_err="400: leftover plaintext error leftover after problem+json-only", plan="problem+json-only 400s leftover plaintext error leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (problem+json vs leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc9457", fetch1_ok="application/problem+json is not leftover plaintext errors.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch2_ok="Exclusive problem+json 400 leftover plaintext."),
     p(slug="leftover-plaintext-error", domain="leftover-plaintext-error-vs-oas-problem-details-json", success=False, name="f7b0d0", stack="OpenAPI leftover content + Java + TS", field="content", old="problem+json", new="plaintext error leftover only", fail_err="400: leftover problem+json after plaintext error leftover-only", plan="plaintext error leftover-only 400s leftover problem+json. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (plaintext error leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch1_ok="Exclusive problem+json 400 leftover plaintext.", fetch2="https://datatracker.ietf.org/doc/html/rfc9457", fetch2_ok="application/problem+json is not leftover plaintext errors.")),
    (p(slug="oas-content-type-problem", domain="oas-content-type-problem-vs-leftover-error-as-json-object", success=True, name="dad386", stack="OpenAPI 3.1 contentType + Go", field="contentType", old="json object error leftover", new="problem content-type", fail_err="400: leftover json object error leftover after problem content-type-only", plan="problem content-type-only 400s leftover json object error leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (problem content-type vs leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc9457", fetch1_ok="problem+json content-type is not leftover generic JSON errors.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch2_ok="Exclusive problem type 400 leftover json object."),
     p(slug="leftover-error-as-json-object", domain="leftover-error-as-json-object-vs-oas-content-type-problem", success=False, name="390c5f", stack="OpenAPI leftover contentType + Java + TS", field="contentType", old="problem content-type", new="json object error leftover only", fail_err="400: leftover problem content-type after json object error leftover-only", plan="json object error leftover-only 400s leftover problem content-type. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (json object error leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch1_ok="Exclusive problem type 400 leftover json object.", fetch2="https://datatracker.ietf.org/doc/html/rfc9457", fetch2_ok="problem+json content-type is not leftover generic JSON errors.")),
    (p(slug="oas-accept-required-header", domain="oas-accept-required-header-vs-leftover-untyped-accept", success=True, name="0296e2", stack="OpenAPI 3.1 Accept + Go", field="Accept", old="untyped Accept leftover", new="Accept header required", fail_err="400: leftover untyped Accept leftover after Accept header required-only", plan="Accept header required-only 400s leftover untyped Accept leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (Accept header required vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="required Accept header is not leftover untyped Accept.", fetch2="https://datatracker.ietf.org/doc/html/rfc9110#name-accept", fetch2_ok="Exclusive Accept 400 leftover untyped."),
     p(slug="leftover-untyped-accept", domain="leftover-untyped-accept-vs-oas-accept-required-header", success=False, name="5ba20f", stack="OpenAPI leftover Accept + Java + TS", field="Accept", old="Accept header required", new="untyped Accept leftover only", fail_err="400: leftover Accept header required after untyped Accept leftover-only", plan="untyped Accept leftover-only 400s leftover Accept header required. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (untyped Accept leftover leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc9110#name-accept", fetch1_ok="Exclusive Accept 400 leftover untyped.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="required Accept header is not leftover untyped Accept.")),
    (p(slug="oas-idempotency-key-header", domain="oas-idempotency-key-header-vs-leftover-replay-without-key", success=True, name="345807", stack="OpenAPI 3.1 Idempotency-Key + Go", field="Idempotency-Key", old="replay leftover", new="Idempotency-Key header", fail_err="400: leftover replay leftover after Idempotency-Key header-only", plan="Idempotency-Key header-only 400s leftover replay leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (Idempotency-Key header vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch1_ok="Idempotency-Key is required on write, leftover replay fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch2_ok="Exclusive idempotency key 400 leftover replay."),
     p(slug="leftover-replay-without-key", domain="leftover-replay-without-key-vs-oas-idempotency-key-header", success=False, name="490eb6", stack="OpenAPI leftover Idempotency-Key + Java + TS", field="Idempotency-Key", old="Idempotency-Key header", new="replay leftover only", fail_err="400: leftover Idempotency-Key header after replay leftover-only", plan="replay leftover-only 400s leftover Idempotency-Key header. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (replay leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch1_ok="Exclusive idempotency key 400 leftover replay.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch2_ok="Idempotency-Key is required on write, leftover replay fails closed.")),
    (p(slug="oas-etag-response-header", domain="oas-etag-response-header-vs-leftover-no-etag-on-get", success=True, name="54dc1f", stack="OpenAPI 3.1 ETag + Go", field="ETag", old="no etag leftover", new="ETag response header", fail_err="400: leftover no etag leftover after ETag response header-only", plan="ETag response header-only 400s leftover no etag leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (ETag response header vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch1_ok="GET responses need ETag, leftover missing fails closed.", fetch2="https://datatracker.ietf.org/doc/html/rfc9110#name-etag", fetch2_ok="Exclusive ETag 400 leftover none."),
     p(slug="leftover-no-etag-on-get", domain="leftover-no-etag-on-get-vs-oas-etag-response-header", success=False, name="39a55e", stack="OpenAPI leftover ETag + Java + TS", field="ETag", old="ETag response header", new="no etag leftover only", fail_err="400: leftover ETag response header after no etag leftover-only", plan="no etag leftover-only 400s leftover ETag response header. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (no etag leftover leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc9110#name-etag", fetch1_ok="Exclusive ETag 400 leftover none.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch2_ok="GET responses need ETag, leftover missing fails closed.")),
    (p(slug="oas-if-match-required", domain="oas-if-match-required-vs-leftover-put-without-if-match", success=True, name="14efb6", stack="OpenAPI 3.1 If-Match + Go", field="If-Match", old="PUT no If-Match leftover", new="If-Match required", fail_err="412: leftover PUT no If-Match leftover after If-Match required-only", plan="If-Match required-only 412s leftover PUT no If-Match leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (If-Match required vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="PUT requires If-Match, leftover missing fails closed.", fetch2="https://datatracker.ietf.org/doc/html/rfc9110#name-if-match", fetch2_ok="Exclusive If-Match 412 leftover none."),
     p(slug="leftover-put-without-if-match", domain="leftover-put-without-if-match-vs-oas-if-match-required", success=False, name="0c49ea", stack="OpenAPI leftover If-Match + Java + TS", field="If-Match", old="If-Match required", new="PUT no If-Match leftover only", fail_err="412: leftover If-Match required after PUT no If-Match leftover-only", plan="PUT no If-Match leftover-only 412s leftover If-Match required. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (PUT no If-Match leftover leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc9110#name-if-match", fetch1_ok="Exclusive If-Match 412 leftover none.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="PUT requires If-Match, leftover missing fails closed.")),
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
    print(json.dumps({"round": round_n, "idx": idx, "ids": [e1["id"], e2["id"]], "catalog": "r4422"}))


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
