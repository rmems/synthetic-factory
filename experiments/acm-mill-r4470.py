#!/usr/bin/env python3
"""Unique OpenAPI-drift ACM catalog r4470. Fast slug load."""
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
    (p(slug="oas-request-body-multipart-enc", domain="oas-request-body-multipart-enc-vs-leftover-multipart-no-encoding", success=True, name="3bf878", stack="OpenAPI 3.1 encoding + Go", field="encoding", old="multipart no encoding leftover", new="multipart encoding map", fail_err="415: leftover multipart no encoding leftover after multipart encoding map-only", plan="multipart encoding map-only 415s leftover multipart no encoding leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (multipart encoding map vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#encoding-object", fetch1_ok="multipart encoding is required here, leftover missing fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#request-body-object", fetch2_ok="Exclusive multipart encoding 415 leftover none."),
     p(slug="leftover-multipart-no-encoding", domain="leftover-multipart-no-encoding-vs-oas-request-body-multipart-enc", success=False, name="825fe4", stack="OpenAPI leftover encoding + Java + TS", field="encoding", old="multipart encoding map", new="multipart no encoding leftover only", fail_err="415: leftover multipart encoding map after multipart no encoding leftover-only", plan="multipart no encoding leftover-only 415s leftover multipart encoding map. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (multipart no encoding leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#request-body-object", fetch1_ok="Exclusive multipart encoding 415 leftover none.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#encoding-object", fetch2_ok="multipart encoding is required here, leftover missing fails closed.")),
    (p(slug="oas-callback-timeout-hint", domain="oas-callback-timeout-hint-vs-leftover-sync-callback-wait", success=True, name="a3c3e5", stack="OpenAPI 3.1 timeout + Go", field="timeout", old="sync wait leftover", new="callback timeout hint", fail_err="400: leftover sync wait leftover after callback timeout hint-only", plan="callback timeout hint-only 400s leftover sync wait leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (callback timeout hint vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#callback-object", fetch1_ok="Callback timeout is a hint, leftover sync-wait fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch2_ok="Exclusive callback timeout 400 leftover sync wait."),
     p(slug="leftover-sync-callback-wait", domain="leftover-sync-callback-wait-vs-oas-callback-timeout-hint", success=False, name="2b5538", stack="OpenAPI leftover timeout + Java + TS", field="timeout", old="callback timeout hint", new="sync wait leftover only", fail_err="400: leftover callback timeout hint after sync wait leftover-only", plan="sync wait leftover-only 400s leftover callback timeout hint. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (sync wait leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch1_ok="Exclusive callback timeout 400 leftover sync wait.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#callback-object", fetch2_ok="Callback timeout is a hint, leftover sync-wait fails closed.")),
    (p(slug="oas-link-opid-xor-opref", domain="oas-link-opid-xor-opref-vs-leftover-link-both-opid-opref", success=True, name="cf84f0", stack="OpenAPI 3.1 operationRef + Go", field="operationRef", old="both opid opref leftover", new="operationId xor operationRef", fail_err="400: leftover both opid opref leftover after operationId xor operationRef-only", plan="operationId xor operationRef-only 400s leftover both opid opref leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (operationId xor operationRef vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#link-object", fetch1_ok="operationId and operationRef are exclusive, leftover both fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#runtime-expressions", fetch2_ok="Exclusive xor 400 leftover both."),
     p(slug="leftover-link-both-opid-opref", domain="leftover-link-both-opid-opref-vs-oas-link-opid-xor-opref", success=False, name="b24ca3", stack="OpenAPI leftover operationRef + Java + TS", field="operationRef", old="operationId xor operationRef", new="both opid opref leftover only", fail_err="400: leftover operationId xor operationRef after both opid opref leftover-only", plan="both opid opref leftover-only 400s leftover operationId xor operationRef. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (both opid opref leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#runtime-expressions", fetch1_ok="Exclusive xor 400 leftover both.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#link-object", fetch2_ok="operationId and operationRef are exclusive, leftover both fails closed.")),
    (p(slug="oas-response-link-array", domain="oas-response-link-array-vs-leftover-single-link-only", success=True, name="dcf6af", stack="OpenAPI 3.1 links + Go", field="links", old="single link leftover", new="response links map", fail_err="400: leftover single link leftover after response links map-only", plan="response links map-only 400s leftover single link leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (response links map vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#response-object", fetch1_ok="links is a map of named links, leftover single-only fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#link-object", fetch2_ok="Exclusive links map 400 leftover single."),
     p(slug="leftover-single-link-only", domain="leftover-single-link-only-vs-oas-response-link-array", success=False, name="414931", stack="OpenAPI leftover links + Java + TS", field="links", old="response links map", new="single link leftover only", fail_err="400: leftover response links map after single link leftover-only", plan="single link leftover-only 400s leftover response links map. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (single link leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#link-object", fetch1_ok="Exclusive links map 400 leftover single.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#response-object", fetch2_ok="links is a map of named links, leftover single-only fails closed.")),
    (p(slug="oas-header-style-simple-path", domain="oas-header-style-simple-path-vs-leftover-header-form-style", success=True, name="556900", stack="OpenAPI 3.1 style + Go", field="style", old="header form leftover", new="header style simple", fail_err="400: leftover header form leftover after header style simple-only", plan="header style simple-only 400s leftover header form leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (header style simple vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch1_ok="headers use style=simple, leftover form fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch2_ok="Exclusive header simple 400 leftover form."),
     p(slug="leftover-header-form-style", domain="leftover-header-form-style-vs-oas-header-style-simple-path", success=False, name="5838f6", stack="OpenAPI leftover style + Java + TS", field="style", old="header style simple", new="header form leftover only", fail_err="400: leftover header style simple after header form leftover-only", plan="header form leftover-only 400s leftover header style simple. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (header form leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch1_ok="Exclusive header simple 400 leftover form.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch2_ok="headers use style=simple, leftover form fails closed.")),
    (p(slug="oas-query-style-pipe-delim", domain="oas-query-style-pipe-delim-vs-leftover-query-pipe-as-csv", success=True, name="3aab7e", stack="OpenAPI 3.1 style + Go", field="style", old="pipe as csv leftover", new="query pipeDelimited", fail_err="400: leftover pipe as csv leftover after query pipeDelimited-only", plan="query pipeDelimited-only 400s leftover pipe as csv leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (query pipeDelimited vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch1_ok="pipeDelimited query is not leftover csv with pipes.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="Exclusive pipeDelimited 400 leftover csv."),
     p(slug="leftover-query-pipe-as-csv", domain="leftover-query-pipe-as-csv-vs-oas-query-style-pipe-delim", success=False, name="c0eabe", stack="OpenAPI leftover style + Java + TS", field="style", old="query pipeDelimited", new="pipe as csv leftover only", fail_err="400: leftover query pipeDelimited after pipe as csv leftover-only", plan="pipe as csv leftover-only 400s leftover query pipeDelimited. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (pipe as csv leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="Exclusive pipeDelimited 400 leftover csv.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch2_ok="pipeDelimited query is not leftover csv with pipes.")),
    (p(slug="oas-path-style-simple-explode", domain="oas-path-style-simple-explode-vs-leftover-path-comma-no-explode", success=True, name="c89c43", stack="OpenAPI 3.1 explode + Go", field="explode", old="comma no explode leftover", new="path simple explode", fail_err="400: leftover comma no explode leftover after path simple explode-only", plan="path simple explode-only 400s leftover comma no explode leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (path simple explode vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch1_ok="path simple explode is not leftover comma without explode.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="Exclusive path explode 400 leftover comma."),
     p(slug="leftover-path-comma-no-explode", domain="leftover-path-comma-no-explode-vs-oas-path-style-simple-explode", success=False, name="923aa7", stack="OpenAPI leftover explode + Java + TS", field="explode", old="path simple explode", new="comma no explode leftover only", fail_err="400: leftover path simple explode after comma no explode leftover-only", plan="comma no explode leftover-only 400s leftover path simple explode. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (comma no explode leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="Exclusive path explode 400 leftover comma.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch2_ok="path simple explode is not leftover comma without explode.")),
    (p(slug="oas-matrix-path-no-explode", domain="oas-matrix-path-no-explode-vs-leftover-matrix-explode-forced", success=True, name="2f6bb8", stack="OpenAPI 3.1 explode + Go", field="explode", old="matrix explode leftover", new="matrix explode false", fail_err="400: leftover matrix explode leftover after matrix explode false-only", plan="matrix explode false-only 400s leftover matrix explode leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (matrix explode false vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch1_ok="matrix explode false is not leftover explode-forced.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="Exclusive matrix no explode 400 leftover forced."),
     p(slug="leftover-matrix-explode-forced", domain="leftover-matrix-explode-forced-vs-oas-matrix-path-no-explode", success=False, name="712382", stack="OpenAPI leftover explode + Java + TS", field="explode", old="matrix explode false", new="matrix explode leftover only", fail_err="400: leftover matrix explode false after matrix explode leftover-only", plan="matrix explode leftover-only 400s leftover matrix explode false. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (matrix explode leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="Exclusive matrix no explode 400 leftover forced.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch2_ok="matrix explode false is not leftover explode-forced.")),
    (p(slug="oas-label-path-no-explode", domain="oas-label-path-no-explode-vs-leftover-label-explode-forced", success=True, name="da0abd", stack="OpenAPI 3.1 explode + Go", field="explode", old="label explode leftover", new="label explode false", fail_err="400: leftover label explode leftover after label explode false-only", plan="label explode false-only 400s leftover label explode leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (label explode false vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch1_ok="label explode false is not leftover explode-forced.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="Exclusive label no explode 400 leftover forced."),
     p(slug="leftover-label-explode-forced", domain="leftover-label-explode-forced-vs-oas-label-path-no-explode", success=False, name="b1fd52", stack="OpenAPI leftover explode + Java + TS", field="explode", old="label explode false", new="label explode leftover only", fail_err="400: leftover label explode false after label explode leftover-only", plan="label explode leftover-only 400s leftover label explode false. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (label explode leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="Exclusive label no explode 400 leftover forced.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch2_ok="label explode false is not leftover explode-forced.")),
    (p(slug="oas-form-query-no-explode", domain="oas-form-query-no-explode-vs-leftover-form-always-explode", success=True, name="707b53", stack="OpenAPI 3.1 explode + Go", field="explode", old="always explode leftover", new="form explode false", fail_err="400: leftover always explode leftover after form explode false-only", plan="form explode false-only 400s leftover always explode leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (form explode false vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch1_ok="form explode false is not leftover always-explode.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="Exclusive form no explode 400 leftover always."),
     p(slug="leftover-form-always-explode", domain="leftover-form-always-explode-vs-oas-form-query-no-explode", success=False, name="59e6b9", stack="OpenAPI leftover explode + Java + TS", field="explode", old="form explode false", new="always explode leftover only", fail_err="400: leftover form explode false after always explode leftover-only", plan="always explode leftover-only 400s leftover form explode false. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (always explode leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="Exclusive form no explode 400 leftover always.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch2_ok="form explode false is not leftover always-explode.")),
    (p(slug="oas-space-delim-no-explode", domain="oas-space-delim-no-explode-vs-leftover-space-as-csv", success=True, name="3abe1f", stack="OpenAPI 3.1 explode + Go", field="explode", old="space csv leftover", new="spaceDelimited no explode", fail_err="400: leftover space csv leftover after spaceDelimited no explode-only", plan="spaceDelimited no explode-only 400s leftover space csv leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (spaceDelimited no explode vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch1_ok="spaceDelimited explode false is not leftover space-as-csv.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="Exclusive space no explode 400 leftover csv."),
     p(slug="leftover-space-as-csv", domain="leftover-space-as-csv-vs-oas-space-delim-no-explode", success=False, name="b3cf9f", stack="OpenAPI leftover explode + Java + TS", field="explode", old="spaceDelimited no explode", new="space csv leftover only", fail_err="400: leftover spaceDelimited no explode after space csv leftover-only", plan="space csv leftover-only 400s leftover spaceDelimited no explode. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (space csv leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="Exclusive space no explode 400 leftover csv.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch2_ok="spaceDelimited explode false is not leftover space-as-csv.")),
    (p(slug="oas-pipe-delim-no-explode", domain="oas-pipe-delim-no-explode-vs-leftover-pipe-as-form", success=True, name="c141cc", stack="OpenAPI 3.1 explode + Go", field="explode", old="pipe as form leftover", new="pipeDelimited no explode", fail_err="400: leftover pipe as form leftover after pipeDelimited no explode-only", plan="pipeDelimited no explode-only 400s leftover pipe as form leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (pipeDelimited no explode vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch1_ok="pipeDelimited explode false is not leftover pipe-as-form.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="Exclusive pipe no explode 400 leftover form."),
     p(slug="leftover-pipe-as-form", domain="leftover-pipe-as-form-vs-oas-pipe-delim-no-explode", success=False, name="152b02", stack="OpenAPI leftover explode + Java + TS", field="explode", old="pipeDelimited no explode", new="pipe as form leftover only", fail_err="400: leftover pipeDelimited no explode after pipe as form leftover-only", plan="pipe as form leftover-only 400s leftover pipeDelimited no explode. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (pipe as form leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="Exclusive pipe no explode 400 leftover form.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch2_ok="pipeDelimited explode false is not leftover pipe-as-form.")),
    (p(slug="oas-deepobject-requires-explode", domain="oas-deepobject-requires-explode-vs-leftover-deepobject-no-explode", success=True, name="d29136", stack="OpenAPI 3.1 explode + Go", field="explode", old="deepObject no explode leftover", new="deepObject explode true", fail_err="400: leftover deepObject no explode leftover after deepObject explode true-only", plan="deepObject explode true-only 400s leftover deepObject no explode leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (deepObject explode true vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch1_ok="deepObject requires explode true, leftover false fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="Exclusive deepObject explode 400 leftover false."),
     p(slug="leftover-deepobject-no-explode", domain="leftover-deepobject-no-explode-vs-oas-deepobject-requires-explode", success=False, name="1cb6ca", stack="OpenAPI leftover explode + Java + TS", field="explode", old="deepObject explode true", new="deepObject no explode leftover only", fail_err="400: leftover deepObject explode true after deepObject no explode leftover-only", plan="deepObject no explode leftover-only 400s leftover deepObject explode true. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (deepObject no explode leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="Exclusive deepObject explode 400 leftover false.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch2_ok="deepObject requires explode true, leftover false fails closed.")),
    (p(slug="oas-content-param-no-style", domain="oas-content-param-no-style-vs-leftover-content-plus-style", success=True, name="7b1fae", stack="OpenAPI 3.1 style + Go", field="style", old="content plus style leftover", new="content param no style", fail_err="400: leftover content plus style leftover after content param no style-only", plan="content param no style-only 400s leftover content plus style leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (content param no style vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="content parameters omit style, leftover style fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch2_ok="Exclusive content no style 400 leftover style."),
     p(slug="leftover-content-plus-style", domain="leftover-content-plus-style-vs-oas-content-param-no-style", success=False, name="0ffb26", stack="OpenAPI leftover style + Java + TS", field="style", old="content param no style", new="content plus style leftover only", fail_err="400: leftover content param no style after content plus style leftover-only", plan="content plus style leftover-only 400s leftover content param no style. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (content plus style leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch1_ok="Exclusive content no style 400 leftover style.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="content parameters omit style, leftover style fails closed.")),
    (p(slug="oas-schema-xor-content-param", domain="oas-schema-xor-content-param-vs-leftover-param-schema-and-content", success=True, name="1d64ef", stack="OpenAPI 3.1 content + Go", field="content", old="schema and content leftover", new="schema xor content", fail_err="400: leftover schema and content leftover after schema xor content-only", plan="schema xor content-only 400s leftover schema and content leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (schema xor content vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="schema and content are exclusive, leftover both fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch2_ok="Exclusive xor 400 leftover both."),
     p(slug="leftover-param-schema-and-content", domain="leftover-param-schema-and-content-vs-oas-schema-xor-content-param", success=False, name="895de3", stack="OpenAPI leftover content + Java + TS", field="content", old="schema xor content", new="schema and content leftover only", fail_err="400: leftover schema xor content after schema and content leftover-only", plan="schema and content leftover-only 400s leftover schema xor content. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (schema and content leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch1_ok="Exclusive xor 400 leftover both.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="schema and content are exclusive, leftover both fails closed.")),
    (p(slug="oas-media-example-xor-examples", domain="oas-media-example-xor-examples-vs-leftover-media-example-and-examples", success=True, name="aae168", stack="OpenAPI 3.1 examples + Go", field="examples", old="example and examples leftover", new="media example xor examples", fail_err="400: leftover example and examples leftover after media example xor examples-only", plan="media example xor examples-only 400s leftover example and examples leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (media example xor examples vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch1_ok="media example and examples are exclusive, leftover both fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#example-object", fetch2_ok="Exclusive media xor 400 leftover both."),
     p(slug="leftover-media-example-and-examples", domain="leftover-media-example-and-examples-vs-oas-media-example-xor-examples", success=False, name="4e8f5e", stack="OpenAPI leftover examples + Java + TS", field="examples", old="media example xor examples", new="example and examples leftover only", fail_err="400: leftover media example xor examples after example and examples leftover-only", plan="example and examples leftover-only 400s leftover media example xor examples. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (example and examples leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#example-object", fetch1_ok="Exclusive media xor 400 leftover both.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch2_ok="media example and examples are exclusive, leftover both fails closed.")),
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
    print(json.dumps({"round": round_n, "idx": idx, "ids": [e1["id"], e2["id"]], "catalog": "r4470"}))


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
