#!/usr/bin/env python3
"""Unique OpenAPI-drift ACM catalog r4550. Fast slug load."""
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
    (p(slug="oas-host-header-required", domain="oas-host-header-required-vs-leftover-missing-host", success=True, name="6af824", stack="OpenAPI 3.1 Host + Go", field="Host", old="missing host leftover", new="Host header required", fail_err="400: leftover missing host leftover after Host header required-only", plan="Host header required-only 400s leftover missing host leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (Host header required vs leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc9110#name-host", fetch1_ok="Host is required, leftover missing fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="Exclusive Host 400 leftover missing."),
     p(slug="leftover-missing-host", domain="leftover-missing-host-vs-oas-host-header-required", success=False, name="b63810", stack="OpenAPI leftover Host + Java + TS", field="Host", old="Host header required", new="missing host leftover only", fail_err="400: leftover Host header required after missing host leftover-only", plan="missing host leftover-only 400s leftover Host header required. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (missing host leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="Exclusive Host 400 leftover missing.", fetch2="https://datatracker.ietf.org/doc/html/rfc9110#name-host", fetch2_ok="Host is required, leftover missing fails closed.")),
    (p(slug="oas-range-requests-bytes", domain="oas-range-requests-bytes-vs-leftover-ignore-range", success=True, name="c31e9f", stack="OpenAPI 3.1 Range + Go", field="Range", old="ignore range leftover", new="byte range requests", fail_err="400: leftover ignore range leftover after byte range requests-only", plan="byte range requests-only 400s leftover ignore range leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (byte range requests vs leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc9110#name-range", fetch1_ok="Range bytes must be honored, leftover ignore fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="Exclusive Range 400 leftover ignore."),
     p(slug="leftover-ignore-range", domain="leftover-ignore-range-vs-oas-range-requests-bytes", success=False, name="667ef9", stack="OpenAPI leftover Range + Java + TS", field="Range", old="byte range requests", new="ignore range leftover only", fail_err="400: leftover byte range requests after ignore range leftover-only", plan="ignore range leftover-only 400s leftover byte range requests. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (ignore range leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="Exclusive Range 400 leftover ignore.", fetch2="https://datatracker.ietf.org/doc/html/rfc9110#name-range", fetch2_ok="Range bytes must be honored, leftover ignore fails closed.")),
    (p(slug="oas-accept-ranges-bytes", domain="oas-accept-ranges-bytes-vs-leftover-no-accept-ranges", success=True, name="37c456", stack="OpenAPI 3.1 Accept-Ranges + Go", field="Accept-Ranges", old="no accept-ranges leftover", new="Accept-Ranges bytes", fail_err="400: leftover no accept-ranges leftover after Accept-Ranges bytes-only", plan="Accept-Ranges bytes-only 400s leftover no accept-ranges leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (Accept-Ranges bytes vs leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc9110#name-accept-ranges", fetch1_ok="Accept-Ranges: bytes is required here, leftover missing fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch2_ok="Exclusive Accept-Ranges 400 leftover none."),
     p(slug="leftover-no-accept-ranges", domain="leftover-no-accept-ranges-vs-oas-accept-ranges-bytes", success=False, name="ba7fe5", stack="OpenAPI leftover Accept-Ranges + Java + TS", field="Accept-Ranges", old="Accept-Ranges bytes", new="no accept-ranges leftover only", fail_err="400: leftover Accept-Ranges bytes after no accept-ranges leftover-only", plan="no accept-ranges leftover-only 400s leftover Accept-Ranges bytes. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (no accept-ranges leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch1_ok="Exclusive Accept-Ranges 400 leftover none.", fetch2="https://datatracker.ietf.org/doc/html/rfc9110#name-accept-ranges", fetch2_ok="Accept-Ranges: bytes is required here, leftover missing fails closed.")),
    (p(slug="oas-content-range-206", domain="oas-content-range-206-vs-leftover-200-as-partial", success=True, name="5ede05", stack="OpenAPI 3.1 Content-Range + Go", field="Content-Range", old="200 as partial leftover", new="206 Content-Range", fail_err="400: leftover 200 as partial leftover after 206 Content-Range-only", plan="206 Content-Range-only 400s leftover 200 as partial leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (206 Content-Range vs leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc9110#name-206-partial-content", fetch1_ok="206 needs Content-Range, leftover 200-as-partial fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#response-object", fetch2_ok="Exclusive 206 400 leftover 200."),
     p(slug="leftover-200-as-partial", domain="leftover-200-as-partial-vs-oas-content-range-206", success=False, name="2c5eb0", stack="OpenAPI leftover Content-Range + Java + TS", field="Content-Range", old="206 Content-Range", new="200 as partial leftover only", fail_err="400: leftover 206 Content-Range after 200 as partial leftover-only", plan="200 as partial leftover-only 400s leftover 206 Content-Range. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (200 as partial leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#response-object", fetch1_ok="Exclusive 206 400 leftover 200.", fetch2="https://datatracker.ietf.org/doc/html/rfc9110#name-206-partial-content", fetch2_ok="206 needs Content-Range, leftover 200-as-partial fails closed.")),
    (p(slug="oas-if-range-conditional", domain="oas-if-range-conditional-vs-leftover-range-no-if-range", success=True, name="35e065", stack="OpenAPI 3.1 If-Range + Go", field="If-Range", old="range no If-Range leftover", new="If-Range required", fail_err="400: leftover range no If-Range leftover after If-Range required-only", plan="If-Range required-only 400s leftover range no If-Range leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (If-Range required vs leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc9110#name-if-range", fetch1_ok="Range with validator needs If-Range, leftover missing fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="Exclusive If-Range 400 leftover none."),
     p(slug="leftover-range-no-if-range", domain="leftover-range-no-if-range-vs-oas-if-range-conditional", success=False, name="9a2d84", stack="OpenAPI leftover If-Range + Java + TS", field="If-Range", old="If-Range required", new="range no If-Range leftover only", fail_err="400: leftover If-Range required after range no If-Range leftover-only", plan="range no If-Range leftover-only 400s leftover If-Range required. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (range no If-Range leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="Exclusive If-Range 400 leftover none.", fetch2="https://datatracker.ietf.org/doc/html/rfc9110#name-if-range", fetch2_ok="Range with validator needs If-Range, leftover missing fails closed.")),
    (p(slug="oas-last-modified-get", domain="oas-last-modified-get-vs-leftover-no-last-modified", success=True, name="13c2f9", stack="OpenAPI 3.1 Last-Modified + Go", field="Last-Modified", old="no last-modified leftover", new="Last-Modified on GET", fail_err="400: leftover no last-modified leftover after Last-Modified on GET-only", plan="Last-Modified on GET-only 400s leftover no last-modified leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (Last-Modified on GET vs leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc9110#name-last-modified", fetch1_ok="GET needs Last-Modified, leftover missing fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch2_ok="Exclusive Last-Modified 400 leftover none."),
     p(slug="leftover-no-last-modified", domain="leftover-no-last-modified-vs-oas-last-modified-get", success=False, name="4ab8a9", stack="OpenAPI leftover Last-Modified + Java + TS", field="Last-Modified", old="Last-Modified on GET", new="no last-modified leftover only", fail_err="400: leftover Last-Modified on GET after no last-modified leftover-only", plan="no last-modified leftover-only 400s leftover Last-Modified on GET. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (no last-modified leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch1_ok="Exclusive Last-Modified 400 leftover none.", fetch2="https://datatracker.ietf.org/doc/html/rfc9110#name-last-modified", fetch2_ok="GET needs Last-Modified, leftover missing fails closed.")),
    (p(slug="oas-expires-http-date", domain="oas-expires-http-date-vs-leftover-expires-delta", success=True, name="7ce4ad", stack="OpenAPI 3.1 Expires + Go", field="Expires", old="delta expires leftover", new="Expires HTTP-date", fail_err="400: leftover delta expires leftover after Expires HTTP-date-only", plan="Expires HTTP-date-only 400s leftover delta expires leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (Expires HTTP-date vs leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc9111#name-expires", fetch1_ok="Expires is an HTTP-date, leftover delta fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch2_ok="Exclusive Expires date 400 leftover delta."),
     p(slug="leftover-expires-delta", domain="leftover-expires-delta-vs-oas-expires-http-date", success=False, name="08e7f9", stack="OpenAPI leftover Expires + Java + TS", field="Expires", old="Expires HTTP-date", new="delta expires leftover only", fail_err="400: leftover Expires HTTP-date after delta expires leftover-only", plan="delta expires leftover-only 400s leftover Expires HTTP-date. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (delta expires leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch1_ok="Exclusive Expires date 400 leftover delta.", fetch2="https://datatracker.ietf.org/doc/html/rfc9111#name-expires", fetch2_ok="Expires is an HTTP-date, leftover delta fails closed.")),
    (p(slug="oas-date-header-required", domain="oas-date-header-required-vs-leftover-missing-date-header", success=True, name="c0c723", stack="OpenAPI 3.1 Date + Go", field="Date", old="missing date leftover", new="Date header required", fail_err="400: leftover missing date leftover after Date header required-only", plan="Date header required-only 400s leftover missing date leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (Date header required vs leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc9110#name-date", fetch1_ok="Date is required on origin responses, leftover missing fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch2_ok="Exclusive Date 400 leftover missing."),
     p(slug="leftover-missing-date-header", domain="leftover-missing-date-header-vs-oas-date-header-required", success=False, name="67796f", stack="OpenAPI leftover Date + Java + TS", field="Date", old="Date header required", new="missing date leftover only", fail_err="400: leftover Date header required after missing date leftover-only", plan="missing date leftover-only 400s leftover Date header required. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (missing date leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch1_ok="Exclusive Date 400 leftover missing.", fetch2="https://datatracker.ietf.org/doc/html/rfc9110#name-date", fetch2_ok="Date is required on origin responses, leftover missing fails closed.")),
    (p(slug="oas-origin-cors-required", domain="oas-origin-cors-required-vs-leftover-no-origin-header", success=True, name="4ffae7", stack="OpenAPI 3.1 Origin + Go", field="Origin", old="no origin leftover", new="Origin header required", fail_err="400: leftover no origin leftover after Origin header required-only", plan="Origin header required-only 400s leftover no origin leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (Origin header required vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="CORS credentialed calls need Origin, leftover missing fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch2_ok="Exclusive Origin 400 leftover none."),
     p(slug="leftover-no-origin-header", domain="leftover-no-origin-header-vs-oas-origin-cors-required", success=False, name="6957b0", stack="OpenAPI leftover Origin + Java + TS", field="Origin", old="Origin header required", new="no origin leftover only", fail_err="400: leftover Origin header required after no origin leftover-only", plan="no origin leftover-only 400s leftover Origin header required. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (no origin leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch1_ok="Exclusive Origin 400 leftover none.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="CORS credentialed calls need Origin, leftover missing fails closed.")),
    (p(slug="oas-ac-allow-methods", domain="oas-ac-allow-methods-vs-leftover-star-allow-methods", success=True, name="5b5d1f", stack="OpenAPI 3.1 Access-Control-Allow-Methods + Go", field="Access-Control-Allow-Methods", old="star methods leftover", new="CORS allow methods list", fail_err="400: leftover star methods leftover after CORS allow methods list-only", plan="CORS allow methods list-only 400s leftover star methods leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (CORS allow methods list vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch1_ok="Allow-Methods must be explicit, leftover * fails closed.", fetch2="https://datatracker.ietf.org/doc/html/rfc9110", fetch2_ok="Exclusive methods list 400 leftover star."),
     p(slug="leftover-star-allow-methods", domain="leftover-star-allow-methods-vs-oas-ac-allow-methods", success=False, name="fab9c1", stack="OpenAPI leftover Access-Control-Allow-Methods + Java + TS", field="Access-Control-Allow-Methods", old="CORS allow methods list", new="star methods leftover only", fail_err="400: leftover CORS allow methods list after star methods leftover-only", plan="star methods leftover-only 400s leftover CORS allow methods list. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (star methods leftover leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc9110", fetch1_ok="Exclusive methods list 400 leftover star.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch2_ok="Allow-Methods must be explicit, leftover * fails closed.")),
    (p(slug="oas-ac-allow-headers", domain="oas-ac-allow-headers-vs-leftover-unlisted-req-headers", success=True, name="5de6da", stack="OpenAPI 3.1 Access-Control-Allow-Headers + Go", field="Access-Control-Allow-Headers", old="unlisted headers leftover", new="CORS allow headers list", fail_err="400: leftover unlisted headers leftover after CORS allow headers list-only", plan="CORS allow headers list-only 400s leftover unlisted headers leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (CORS allow headers list vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch1_ok="request headers must be listed, leftover unlisted fails closed.", fetch2="https://datatracker.ietf.org/doc/html/rfc9110", fetch2_ok="Exclusive allow headers 400 leftover unlisted."),
     p(slug="leftover-unlisted-req-headers", domain="leftover-unlisted-req-headers-vs-oas-ac-allow-headers", success=False, name="9c435a", stack="OpenAPI leftover Access-Control-Allow-Headers + Java + TS", field="Access-Control-Allow-Headers", old="CORS allow headers list", new="unlisted headers leftover only", fail_err="400: leftover CORS allow headers list after unlisted headers leftover-only", plan="unlisted headers leftover-only 400s leftover CORS allow headers list. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (unlisted headers leftover leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc9110", fetch1_ok="Exclusive allow headers 400 leftover unlisted.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch2_ok="request headers must be listed, leftover unlisted fails closed.")),
    (p(slug="oas-ac-max-age-preflight", domain="oas-ac-max-age-preflight-vs-leftover-preflight-no-maxage", success=True, name="9ba373", stack="OpenAPI 3.1 Access-Control-Max-Age + Go", field="Access-Control-Max-Age", old="no max-age leftover", new="CORS max-age", fail_err="400: leftover no max-age leftover after CORS max-age-only", plan="CORS max-age-only 400s leftover no max-age leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (CORS max-age vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch1_ok="preflight needs Max-Age, leftover missing fails closed.", fetch2="https://datatracker.ietf.org/doc/html/rfc9110", fetch2_ok="Exclusive Max-Age 400 leftover none."),
     p(slug="leftover-preflight-no-maxage", domain="leftover-preflight-no-maxage-vs-oas-ac-max-age-preflight", success=False, name="1b5da9", stack="OpenAPI leftover Access-Control-Max-Age + Java + TS", field="Access-Control-Max-Age", old="CORS max-age", new="no max-age leftover only", fail_err="400: leftover CORS max-age after no max-age leftover-only", plan="no max-age leftover-only 400s leftover CORS max-age. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (no max-age leftover leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc9110", fetch1_ok="Exclusive Max-Age 400 leftover none.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch2_ok="preflight needs Max-Age, leftover missing fails closed.")),
    (p(slug="oas-hsts-preload", domain="oas-hsts-preload-vs-leftover-no-hsts", success=True, name="4bf840", stack="OpenAPI 3.1 Strict-Transport-Security + Go", field="Strict-Transport-Security", old="no hsts leftover", new="HSTS preload", fail_err="400: leftover no hsts leftover after HSTS preload-only", plan="HSTS preload-only 400s leftover no hsts leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (HSTS preload vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch1_ok="HSTS is required, leftover missing fails closed.", fetch2="https://datatracker.ietf.org/doc/html/rfc6797", fetch2_ok="Exclusive HSTS 400 leftover none."),
     p(slug="leftover-no-hsts", domain="leftover-no-hsts-vs-oas-hsts-preload", success=False, name="a83e28", stack="OpenAPI leftover Strict-Transport-Security + Java + TS", field="Strict-Transport-Security", old="HSTS preload", new="no hsts leftover only", fail_err="400: leftover HSTS preload after no hsts leftover-only", plan="no hsts leftover-only 400s leftover HSTS preload. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (no hsts leftover leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc6797", fetch1_ok="Exclusive HSTS 400 leftover none.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch2_ok="HSTS is required, leftover missing fails closed.")),
    (p(slug="oas-nosniff-content-type", domain="oas-nosniff-content-type-vs-leftover-no-nosniff", success=True, name="bb17b1", stack="OpenAPI 3.1 X-Content-Type-Options + Go", field="X-Content-Type-Options", old="no nosniff leftover", new="nosniff", fail_err="400: leftover no nosniff leftover after nosniff-only", plan="nosniff-only 400s leftover no nosniff leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (nosniff vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch1_ok="X-Content-Type-Options: nosniff is required, leftover missing fails closed.", fetch2="https://datatracker.ietf.org/doc/html/rfc9110", fetch2_ok="Exclusive nosniff 400 leftover none."),
     p(slug="leftover-no-nosniff", domain="leftover-no-nosniff-vs-oas-nosniff-content-type", success=False, name="8c91fb", stack="OpenAPI leftover X-Content-Type-Options + Java + TS", field="X-Content-Type-Options", old="nosniff", new="no nosniff leftover only", fail_err="400: leftover nosniff after no nosniff leftover-only", plan="no nosniff leftover-only 400s leftover nosniff. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (no nosniff leftover leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc9110", fetch1_ok="Exclusive nosniff 400 leftover none.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch2_ok="X-Content-Type-Options: nosniff is required, leftover missing fails closed.")),
    (p(slug="oas-frame-options-deny", domain="oas-frame-options-deny-vs-leftover-allow-framing", success=True, name="75a62e", stack="OpenAPI 3.1 X-Frame-Options + Go", field="X-Frame-Options", old="allow framing leftover", new="X-Frame-Options DENY", fail_err="400: leftover allow framing leftover after X-Frame-Options DENY-only", plan="X-Frame-Options DENY-only 400s leftover allow framing leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (X-Frame-Options DENY vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch1_ok="X-Frame-Options DENY is required, leftover allow fails closed.", fetch2="https://datatracker.ietf.org/doc/html/rfc7034", fetch2_ok="Exclusive DENY 400 leftover allow."),
     p(slug="leftover-allow-framing", domain="leftover-allow-framing-vs-oas-frame-options-deny", success=False, name="e606fd", stack="OpenAPI leftover X-Frame-Options + Java + TS", field="X-Frame-Options", old="X-Frame-Options DENY", new="allow framing leftover only", fail_err="400: leftover X-Frame-Options DENY after allow framing leftover-only", plan="allow framing leftover-only 400s leftover X-Frame-Options DENY. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (allow framing leftover leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc7034", fetch1_ok="Exclusive DENY 400 leftover allow.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch2_ok="X-Frame-Options DENY is required, leftover allow fails closed.")),
    (p(slug="oas-referrer-policy-strict", domain="oas-referrer-policy-strict-vs-leftover-unsafe-referrer", success=True, name="8178b7", stack="OpenAPI 3.1 Referrer-Policy + Go", field="Referrer-Policy", old="unsafe referrer leftover", new="strict-origin-when-cross-origin", fail_err="400: leftover unsafe referrer leftover after strict-origin-when-cross-origin-only", plan="strict-origin-when-cross-origin-only 400s leftover unsafe referrer leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (strict-origin-when-cross-origin vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch1_ok="Referrer-Policy must be strict, leftover unsafe fails closed.", fetch2="https://datatracker.ietf.org/doc/html/rfc9110", fetch2_ok="Exclusive referrer policy 400 leftover unsafe."),
     p(slug="leftover-unsafe-referrer", domain="leftover-unsafe-referrer-vs-oas-referrer-policy-strict", success=False, name="049ae3", stack="OpenAPI leftover Referrer-Policy + Java + TS", field="Referrer-Policy", old="strict-origin-when-cross-origin", new="unsafe referrer leftover only", fail_err="400: leftover strict-origin-when-cross-origin after unsafe referrer leftover-only", plan="unsafe referrer leftover-only 400s leftover strict-origin-when-cross-origin. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (unsafe referrer leftover leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc9110", fetch1_ok="Exclusive referrer policy 400 leftover unsafe.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch2_ok="Referrer-Policy must be strict, leftover unsafe fails closed.")),
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
    print(json.dumps({"round": round_n, "idx": idx, "ids": [e1["id"], e2["id"]], "catalog": "r4550"}))


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
