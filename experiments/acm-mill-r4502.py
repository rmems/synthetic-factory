#!/usr/bin/env python3
"""Unique OpenAPI-drift ACM catalog r4502. Fast slug load."""
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
    (p(slug="oas-status-204-no-ctype", domain="oas-status-204-no-ctype-vs-leftover-204-content-type", success=True, name="7bc846", stack="OpenAPI 3.1 contentType + Go", field="contentType", old="204 content-type leftover", new="204 no content-type", fail_err="400: leftover 204 content-type leftover after 204 no content-type-only", plan="204 no content-type-only 400s leftover 204 content-type leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (204 no content-type vs leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc9110#name-204-no-content", fetch1_ok="204 has no Content-Type, leftover ctype fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#response-object", fetch2_ok="Exclusive 204 no ctype 400 leftover ctype."),
     p(slug="leftover-204-content-type", domain="leftover-204-content-type-vs-oas-status-204-no-ctype", success=False, name="6fb8b8", stack="OpenAPI leftover contentType + Java + TS", field="contentType", old="204 no content-type", new="204 content-type leftover only", fail_err="400: leftover 204 no content-type after 204 content-type leftover-only", plan="204 content-type leftover-only 400s leftover 204 no content-type. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (204 content-type leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#response-object", fetch1_ok="Exclusive 204 no ctype 400 leftover ctype.", fetch2="https://datatracker.ietf.org/doc/html/rfc9110#name-204-no-content", fetch2_ok="204 has no Content-Type, leftover ctype fails closed.")),
    (p(slug="oas-if-none-match-get", domain="oas-if-none-match-get-vs-leftover-get-no-conditional", success=True, name="b81036", stack="OpenAPI 3.1 If-None-Match + Go", field="If-None-Match", old="no conditional leftover", new="If-None-Match on GET", fail_err="400: leftover no conditional leftover after If-None-Match on GET-only", plan="If-None-Match on GET-only 400s leftover no conditional leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (If-None-Match on GET vs leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc9110#name-if-none-match", fetch1_ok="GET should honor If-None-Match, leftover none fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="Exclusive If-None-Match 400 leftover none."),
     p(slug="leftover-get-no-conditional", domain="leftover-get-no-conditional-vs-oas-if-none-match-get", success=False, name="b1a207", stack="OpenAPI leftover If-None-Match + Java + TS", field="If-None-Match", old="If-None-Match on GET", new="no conditional leftover only", fail_err="400: leftover If-None-Match on GET after no conditional leftover-only", plan="no conditional leftover-only 400s leftover If-None-Match on GET. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (no conditional leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="Exclusive If-None-Match 400 leftover none.", fetch2="https://datatracker.ietf.org/doc/html/rfc9110#name-if-none-match", fetch2_ok="GET should honor If-None-Match, leftover none fails closed.")),
    (p(slug="oas-retry-after-429", domain="oas-retry-after-429-vs-leftover-429-no-retry-after", success=True, name="75c48c", stack="OpenAPI 3.1 Retry-After + Go", field="Retry-After", old="no retry-after leftover", new="429 Retry-After", fail_err="429: leftover no retry-after leftover after 429 Retry-After-only", plan="429 Retry-After-only 429s leftover no retry-after leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (429 Retry-After vs leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc9110#name-retry-after", fetch1_ok="429 needs Retry-After, leftover missing fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch2_ok="Exclusive Retry-After 429 leftover none."),
     p(slug="leftover-429-no-retry-after", domain="leftover-429-no-retry-after-vs-oas-retry-after-429", success=False, name="613003", stack="OpenAPI leftover Retry-After + Java + TS", field="Retry-After", old="429 Retry-After", new="no retry-after leftover only", fail_err="429: leftover 429 Retry-After after no retry-after leftover-only", plan="no retry-after leftover-only 429s leftover 429 Retry-After. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (no retry-after leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch1_ok="Exclusive Retry-After 429 leftover none.", fetch2="https://datatracker.ietf.org/doc/html/rfc9110#name-retry-after", fetch2_ok="429 needs Retry-After, leftover missing fails closed.")),
    (p(slug="oas-www-authenticate-401", domain="oas-www-authenticate-401-vs-leftover-401-no-challenge", success=True, name="b08c46", stack="OpenAPI 3.1 WWW-Authenticate + Go", field="WWW-Authenticate", old="no challenge leftover", new="401 WWW-Authenticate", fail_err="401: leftover no challenge leftover after 401 WWW-Authenticate-only", plan="401 WWW-Authenticate-only 401s leftover no challenge leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (401 WWW-Authenticate vs leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc9110#name-www-authenticate", fetch1_ok="401 needs WWW-Authenticate, leftover missing fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch2_ok="Exclusive WWW-Authenticate 401 leftover none."),
     p(slug="leftover-401-no-challenge", domain="leftover-401-no-challenge-vs-oas-www-authenticate-401", success=False, name="d55cc4", stack="OpenAPI leftover WWW-Authenticate + Java + TS", field="WWW-Authenticate", old="401 WWW-Authenticate", new="no challenge leftover only", fail_err="401: leftover 401 WWW-Authenticate after no challenge leftover-only", plan="no challenge leftover-only 401s leftover 401 WWW-Authenticate. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (no challenge leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch1_ok="Exclusive WWW-Authenticate 401 leftover none.", fetch2="https://datatracker.ietf.org/doc/html/rfc9110#name-www-authenticate", fetch2_ok="401 needs WWW-Authenticate, leftover missing fails closed.")),
    (p(slug="oas-cache-control-get", domain="oas-cache-control-get-vs-leftover-get-no-cache-header", success=True, name="cfc710", stack="OpenAPI 3.1 Cache-Control + Go", field="Cache-Control", old="no cache leftover", new="GET Cache-Control", fail_err="400: leftover no cache leftover after GET Cache-Control-only", plan="GET Cache-Control-only 400s leftover no cache leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (GET Cache-Control vs leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc9111", fetch1_ok="GET responses need Cache-Control, leftover missing fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch2_ok="Exclusive Cache-Control 400 leftover none."),
     p(slug="leftover-get-no-cache-header", domain="leftover-get-no-cache-header-vs-oas-cache-control-get", success=False, name="5a92cc", stack="OpenAPI leftover Cache-Control + Java + TS", field="Cache-Control", old="GET Cache-Control", new="no cache leftover only", fail_err="400: leftover GET Cache-Control after no cache leftover-only", plan="no cache leftover-only 400s leftover GET Cache-Control. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (no cache leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch1_ok="Exclusive Cache-Control 400 leftover none.", fetch2="https://datatracker.ietf.org/doc/html/rfc9111", fetch2_ok="GET responses need Cache-Control, leftover missing fails closed.")),
    (p(slug="oas-vary-accept-header", domain="oas-vary-accept-header-vs-leftover-no-vary-header", success=True, name="5c85ef", stack="OpenAPI 3.1 Vary + Go", field="Vary", old="no Vary leftover", new="Vary Accept", fail_err="400: leftover no Vary leftover after Vary Accept-only", plan="Vary Accept-only 400s leftover no Vary leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (Vary Accept vs leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc9110#name-vary", fetch1_ok="Negotiated GET needs Vary, leftover missing fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch2_ok="Exclusive Vary 400 leftover none."),
     p(slug="leftover-no-vary-header", domain="leftover-no-vary-header-vs-oas-vary-accept-header", success=False, name="291779", stack="OpenAPI leftover Vary + Java + TS", field="Vary", old="Vary Accept", new="no Vary leftover only", fail_err="400: leftover Vary Accept after no Vary leftover-only", plan="no Vary leftover-only 400s leftover Vary Accept. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (no Vary leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch1_ok="Exclusive Vary 400 leftover none.", fetch2="https://datatracker.ietf.org/doc/html/rfc9110#name-vary", fetch2_ok="Negotiated GET needs Vary, leftover missing fails closed.")),
    (p(slug="oas-content-location-header", domain="oas-content-location-header-vs-leftover-no-content-location", success=True, name="da6b5c", stack="OpenAPI 3.1 Content-Location + Go", field="Content-Location", old="no content-location leftover", new="Content-Location header", fail_err="400: leftover no content-location leftover after Content-Location header-only", plan="Content-Location header-only 400s leftover no content-location leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (Content-Location header vs leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc9110#name-content-location", fetch1_ok="Content-Location identifies the variant, leftover missing fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch2_ok="Exclusive Content-Location 400 leftover none."),
     p(slug="leftover-no-content-location", domain="leftover-no-content-location-vs-oas-content-location-header", success=False, name="8f41db", stack="OpenAPI leftover Content-Location + Java + TS", field="Content-Location", old="Content-Location header", new="no content-location leftover only", fail_err="400: leftover Content-Location header after no content-location leftover-only", plan="no content-location leftover-only 400s leftover Content-Location header. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (no content-location leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch1_ok="Exclusive Content-Location 400 leftover none.", fetch2="https://datatracker.ietf.org/doc/html/rfc9110#name-content-location", fetch2_ok="Content-Location identifies the variant, leftover missing fails closed.")),
    (p(slug="oas-content-digest-header", domain="oas-content-digest-header-vs-leftover-no-payload-digest", success=True, name="da180a", stack="OpenAPI 3.1 Content-Digest + Go", field="Content-Digest", old="no digest leftover", new="Content-Digest header", fail_err="400: leftover no digest leftover after Content-Digest header-only", plan="Content-Digest header-only 400s leftover no digest leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (Content-Digest header vs leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc9530", fetch1_ok="Content-Digest covers the payload, leftover missing fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch2_ok="Exclusive Content-Digest 400 leftover none."),
     p(slug="leftover-no-payload-digest", domain="leftover-no-payload-digest-vs-oas-content-digest-header", success=False, name="4de755", stack="OpenAPI leftover Content-Digest + Java + TS", field="Content-Digest", old="Content-Digest header", new="no digest leftover only", fail_err="400: leftover Content-Digest header after no digest leftover-only", plan="no digest leftover-only 400s leftover Content-Digest header. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (no digest leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch1_ok="Exclusive Content-Digest 400 leftover none.", fetch2="https://datatracker.ietf.org/doc/html/rfc9530", fetch2_ok="Content-Digest covers the payload, leftover missing fails closed.")),
    (p(slug="oas-dpop-proof-required", domain="oas-dpop-proof-required-vs-leftover-bearer-no-dpop", success=True, name="f064d9", stack="OpenAPI 3.1 DPoP + Go", field="DPoP", old="bearer no dpop leftover", new="DPoP proof required", fail_err="401: leftover bearer no dpop leftover after DPoP proof required-only", plan="DPoP proof required-only 401s leftover bearer no dpop leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (DPoP proof required vs leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc9449", fetch1_ok="DPoP proof is required, leftover bearer-only fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch2_ok="Exclusive DPoP 401 leftover bearer."),
     p(slug="leftover-bearer-no-dpop", domain="leftover-bearer-no-dpop-vs-oas-dpop-proof-required", success=False, name="fef877", stack="OpenAPI leftover DPoP + Java + TS", field="DPoP", old="DPoP proof required", new="bearer no dpop leftover only", fail_err="401: leftover DPoP proof required after bearer no dpop leftover-only", plan="bearer no dpop leftover-only 401s leftover DPoP proof required. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (bearer no dpop leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch1_ok="Exclusive DPoP 401 leftover bearer.", fetch2="https://datatracker.ietf.org/doc/html/rfc9449", fetch2_ok="DPoP proof is required, leftover bearer-only fails closed.")),
    (p(slug="oas-par-pushed-auth-req", domain="oas-par-pushed-auth-req-vs-leftover-query-auth-request", success=True, name="c860f2", stack="OpenAPI 3.1 PAR + Go", field="PAR", old="query auth leftover", new="pushed authorization request", fail_err="401: leftover query auth leftover after pushed authorization request-only", plan="pushed authorization request-only 401s leftover query auth leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (pushed authorization request vs leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc9126", fetch1_ok="PAR is not leftover query authorization requests.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#oauth-flow-object", fetch2_ok="Exclusive PAR 401 leftover query."),
     p(slug="leftover-query-auth-request", domain="leftover-query-auth-request-vs-oas-par-pushed-auth-req", success=False, name="58fb5b", stack="OpenAPI leftover PAR + Java + TS", field="PAR", old="pushed authorization request", new="query auth leftover only", fail_err="401: leftover pushed authorization request after query auth leftover-only", plan="query auth leftover-only 401s leftover pushed authorization request. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (query auth leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#oauth-flow-object", fetch1_ok="Exclusive PAR 401 leftover query.", fetch2="https://datatracker.ietf.org/doc/html/rfc9126", fetch2_ok="PAR is not leftover query authorization requests.")),
    (p(slug="oas-token-exchange-grant", domain="oas-token-exchange-grant-vs-leftover-refresh-as-exchange", success=True, name="2173f2", stack="OpenAPI 3.1 token-exchange + Go", field="token-exchange", old="refresh as exchange leftover", new="token exchange grant", fail_err="401: leftover refresh as exchange leftover after token exchange grant-only", plan="token exchange grant-only 401s leftover refresh as exchange leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (token exchange grant vs leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc8693", fetch1_ok="token-exchange is not leftover refresh-as-exchange.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#oauth-flow-object", fetch2_ok="Exclusive token exchange 401 leftover refresh."),
     p(slug="leftover-refresh-as-exchange", domain="leftover-refresh-as-exchange-vs-oas-token-exchange-grant", success=False, name="f06443", stack="OpenAPI leftover token-exchange + Java + TS", field="token-exchange", old="token exchange grant", new="refresh as exchange leftover only", fail_err="401: leftover token exchange grant after refresh as exchange leftover-only", plan="refresh as exchange leftover-only 401s leftover token exchange grant. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (refresh as exchange leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#oauth-flow-object", fetch1_ok="Exclusive token exchange 401 leftover refresh.", fetch2="https://datatracker.ietf.org/doc/html/rfc8693", fetch2_ok="token-exchange is not leftover refresh-as-exchange.")),
    (p(slug="oas-mtls-san-match", domain="oas-mtls-san-match-vs-leftover-any-client-cert-dn", success=True, name="cb8831", stack="OpenAPI 3.1 mutualTLS + Go", field="mutualTLS", old="any cert leftover", new="mTLS SAN match", fail_err="401: leftover any cert leftover after mTLS SAN match-only", plan="mTLS SAN match-only 401s leftover any cert leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (mTLS SAN match vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch1_ok="mTLS SAN must match, leftover any-cert fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#security-requirement-object", fetch2_ok="Exclusive SAN match 401 leftover any cert."),
     p(slug="leftover-any-client-cert-dn", domain="leftover-any-client-cert-dn-vs-oas-mtls-san-match", success=False, name="86f24f", stack="OpenAPI leftover mutualTLS + Java + TS", field="mutualTLS", old="mTLS SAN match", new="any cert leftover only", fail_err="401: leftover mTLS SAN match after any cert leftover-only", plan="any cert leftover-only 401s leftover mTLS SAN match. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (any cert leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#security-requirement-object", fetch1_ok="Exclusive SAN match 401 leftover any cert.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch2_ok="mTLS SAN must match, leftover any-cert fails closed.")),
    (p(slug="oas-cookie-samesite-strict", domain="oas-cookie-samesite-strict-vs-leftover-cookie-no-samesite", success=True, name="eda7e7", stack="OpenAPI 3.1 SameSite + Go", field="SameSite", old="no samesite leftover", new="cookie SameSite strict", fail_err="401: leftover no samesite leftover after cookie SameSite strict-only", plan="cookie SameSite strict-only 401s leftover no samesite leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (cookie SameSite strict vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="apiKey cookies need SameSite, leftover missing fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch2_ok="Exclusive SameSite 401 leftover none."),
     p(slug="leftover-cookie-no-samesite", domain="leftover-cookie-no-samesite-vs-oas-cookie-samesite-strict", success=False, name="ef2dee", stack="OpenAPI leftover SameSite + Java + TS", field="SameSite", old="cookie SameSite strict", new="no samesite leftover only", fail_err="401: leftover cookie SameSite strict after no samesite leftover-only", plan="no samesite leftover-only 401s leftover cookie SameSite strict. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (no samesite leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch1_ok="Exclusive SameSite 401 leftover none.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="apiKey cookies need SameSite, leftover missing fails closed.")),
    (p(slug="oas-cookie-secure-flag", domain="oas-cookie-secure-flag-vs-leftover-cookie-insecure", success=True, name="398db1", stack="OpenAPI 3.1 Secure + Go", field="Secure", old="insecure cookie leftover", new="cookie Secure flag", fail_err="401: leftover insecure cookie leftover after cookie Secure flag-only", plan="cookie Secure flag-only 401s leftover insecure cookie leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (cookie Secure flag vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="apiKey cookies need Secure, leftover insecure fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch2_ok="Exclusive Secure 401 leftover insecure."),
     p(slug="leftover-cookie-insecure", domain="leftover-cookie-insecure-vs-oas-cookie-secure-flag", success=False, name="ae02d2", stack="OpenAPI leftover Secure + Java + TS", field="Secure", old="cookie Secure flag", new="insecure cookie leftover only", fail_err="401: leftover cookie Secure flag after insecure cookie leftover-only", plan="insecure cookie leftover-only 401s leftover cookie Secure flag. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (insecure cookie leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch1_ok="Exclusive Secure 401 leftover insecure.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="apiKey cookies need Secure, leftover insecure fails closed.")),
    (p(slug="oas-cors-allow-origin-list", domain="oas-cors-allow-origin-list-vs-leftover-star-with-credentials", success=True, name="5d89ea", stack="OpenAPI 3.1 Access-Control-Allow-Origin + Go", field="Access-Control-Allow-Origin", old="star with credentials leftover", new="CORS origin list", fail_err="400: leftover star with credentials leftover after CORS origin list-only", plan="CORS origin list-only 400s leftover star with credentials leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (CORS origin list vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch1_ok="credentials forbid *, leftover star fails closed.", fetch2="https://datatracker.ietf.org/doc/html/rfc9110", fetch2_ok="Exclusive origin list 400 leftover star."),
     p(slug="leftover-star-with-credentials", domain="leftover-star-with-credentials-vs-oas-cors-allow-origin-list", success=False, name="848df5", stack="OpenAPI leftover Access-Control-Allow-Origin + Java + TS", field="Access-Control-Allow-Origin", old="CORS origin list", new="star with credentials leftover only", fail_err="400: leftover CORS origin list after star with credentials leftover-only", plan="star with credentials leftover-only 400s leftover CORS origin list. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (star with credentials leftover leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc9110", fetch1_ok="Exclusive origin list 400 leftover star.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch2_ok="credentials forbid *, leftover star fails closed.")),
    (p(slug="oas-deprecation-link-header", domain="oas-deprecation-link-header-vs-leftover-no-deprecation-link", success=True, name="f243c0", stack="OpenAPI 3.1 Deprecation + Go", field="Deprecation", old="no deprecation link leftover", new="Deprecation link header", fail_err="400: leftover no deprecation link leftover after Deprecation link header-only", plan="Deprecation link header-only 400s leftover no deprecation link leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (Deprecation link header vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch1_ok="Deprecated ops need a Deprecation/Link header, leftover missing fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch2_ok="Exclusive deprecation link 400 leftover none."),
     p(slug="leftover-no-deprecation-link", domain="leftover-no-deprecation-link-vs-oas-deprecation-link-header", success=False, name="de3dbb", stack="OpenAPI leftover Deprecation + Java + TS", field="Deprecation", old="Deprecation link header", new="no deprecation link leftover only", fail_err="400: leftover Deprecation link header after no deprecation link leftover-only", plan="no deprecation link leftover-only 400s leftover Deprecation link header. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (no deprecation link leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch1_ok="Exclusive deprecation link 400 leftover none.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch2_ok="Deprecated ops need a Deprecation/Link header, leftover missing fails closed.")),
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
    print(json.dumps({"round": round_n, "idx": idx, "ids": [e1["id"], e2["id"]], "catalog": "r4502"}))


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
