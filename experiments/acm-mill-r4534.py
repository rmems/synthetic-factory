#!/usr/bin/env python3
"""Unique OpenAPI-drift ACM catalog r4534. Fast slug load."""
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
    (p(slug="oas-rate-limit-policy-header", domain="oas-rate-limit-policy-header-vs-leftover-unspecified-quota", success=True, name="85f50f", stack="OpenAPI 3.1 RateLimit-Policy + Go", field="RateLimit-Policy", old="unspecified quota leftover", new="RateLimit-Policy header", fail_err="429: leftover unspecified quota leftover after RateLimit-Policy header-only", plan="RateLimit-Policy header-only 429s leftover unspecified quota leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (RateLimit-Policy header vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch1_ok="RateLimit-Policy documents quota, leftover unspecified fails closed.", fetch2="https://datatracker.ietf.org/doc/html/rfc6585", fetch2_ok="Exclusive RateLimit-Policy 429 leftover unspecified."),
     p(slug="leftover-unspecified-quota", domain="leftover-unspecified-quota-vs-oas-rate-limit-policy-header", success=False, name="9b86a3", stack="OpenAPI leftover RateLimit-Policy + Java + TS", field="RateLimit-Policy", old="RateLimit-Policy header", new="unspecified quota leftover only", fail_err="429: leftover RateLimit-Policy header after unspecified quota leftover-only", plan="unspecified quota leftover-only 429s leftover RateLimit-Policy header. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (unspecified quota leftover leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc6585", fetch1_ok="Exclusive RateLimit-Policy 429 leftover unspecified.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch2_ok="RateLimit-Policy documents quota, leftover unspecified fails closed.")),
    (p(slug="oas-signature-input-header", domain="oas-signature-input-header-vs-leftover-unsigned-request", success=True, name="7f3de5", stack="OpenAPI 3.1 Signature-Input + Go", field="Signature-Input", old="unsigned leftover", new="Signature-Input header", fail_err="401: leftover unsigned leftover after Signature-Input header-only", plan="Signature-Input header-only 401s leftover unsigned leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (Signature-Input header vs leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc9421", fetch1_ok="signed requests need Signature-Input, leftover unsigned fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch2_ok="Exclusive Signature-Input 401 leftover unsigned."),
     p(slug="leftover-unsigned-request", domain="leftover-unsigned-request-vs-oas-signature-input-header", success=False, name="e4fc60", stack="OpenAPI leftover Signature-Input + Java + TS", field="Signature-Input", old="Signature-Input header", new="unsigned leftover only", fail_err="401: leftover Signature-Input header after unsigned leftover-only", plan="unsigned leftover-only 401s leftover Signature-Input header. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (unsigned leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch1_ok="Exclusive Signature-Input 401 leftover unsigned.", fetch2="https://datatracker.ietf.org/doc/html/rfc9421", fetch2_ok="signed requests need Signature-Input, leftover unsigned fails closed.")),
    (p(slug="oas-authorization-required-write", domain="oas-authorization-required-write-vs-leftover-anonymous-write", success=True, name="655e12", stack="OpenAPI 3.1 security + Go", field="security", old="anonymous write leftover", new="authorization required write", fail_err="401: leftover anonymous write leftover after authorization required write-only", plan="authorization required write-only 401s leftover anonymous write leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (authorization required write vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch1_ok="writes require security, leftover anonymous fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#security-requirement-object", fetch2_ok="Exclusive write auth 401 leftover anonymous."),
     p(slug="leftover-anonymous-write", domain="leftover-anonymous-write-vs-oas-authorization-required-write", success=False, name="1ff800", stack="OpenAPI leftover security + Java + TS", field="security", old="authorization required write", new="anonymous write leftover only", fail_err="401: leftover authorization required write after anonymous write leftover-only", plan="anonymous write leftover-only 401s leftover authorization required write. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (anonymous write leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#security-requirement-object", fetch1_ok="Exclusive write auth 401 leftover anonymous.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch2_ok="writes require security, leftover anonymous fails closed.")),
    (p(slug="oas-scope-read-write-split", domain="oas-scope-read-write-split-vs-leftover-single-scope-all", success=True, name="8f41ba", stack="OpenAPI 3.1 scopes + Go", field="scopes", old="single scope leftover", new="read write scope split", fail_err="401: leftover single scope leftover after read write scope split-only", plan="read write scope split-only 401s leftover single scope leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (read write scope split vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#oauth-flow-object", fetch1_ok="read and write scopes are split, leftover all-in-one fails closed.", fetch2="https://datatracker.ietf.org/doc/html/rfc6749", fetch2_ok="Exclusive split scopes 401 leftover single."),
     p(slug="leftover-single-scope-all", domain="leftover-single-scope-all-vs-oas-scope-read-write-split", success=False, name="feb484", stack="OpenAPI leftover scopes + Java + TS", field="scopes", old="read write scope split", new="single scope leftover only", fail_err="401: leftover read write scope split after single scope leftover-only", plan="single scope leftover-only 401s leftover read write scope split. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (single scope leftover leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc6749", fetch1_ok="Exclusive split scopes 401 leftover single.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#oauth-flow-object", fetch2_ok="read and write scopes are split, leftover all-in-one fails closed.")),
    (p(slug="oas-audience-required-jwt", domain="oas-audience-required-jwt-vs-leftover-any-aud-jwt", success=True, name="1141e6", stack="OpenAPI 3.1 aud + Go", field="aud", old="any aud leftover", new="JWT audience required", fail_err="401: leftover any aud leftover after JWT audience required-only", plan="JWT audience required-only 401s leftover any aud leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (JWT audience required vs leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc7519", fetch1_ok="JWT aud is required, leftover any-aud fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch2_ok="Exclusive aud 401 leftover any."),
     p(slug="leftover-any-aud-jwt", domain="leftover-any-aud-jwt-vs-oas-audience-required-jwt", success=False, name="5c2e14", stack="OpenAPI leftover aud + Java + TS", field="aud", old="JWT audience required", new="any aud leftover only", fail_err="401: leftover JWT audience required after any aud leftover-only", plan="any aud leftover-only 401s leftover JWT audience required. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (any aud leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch1_ok="Exclusive aud 401 leftover any.", fetch2="https://datatracker.ietf.org/doc/html/rfc7519", fetch2_ok="JWT aud is required, leftover any-aud fails closed.")),
    (p(slug="oas-resource-indicator", domain="oas-resource-indicator-vs-leftover-no-resource-param", success=True, name="61ac04", stack="OpenAPI 3.1 resource + Go", field="resource", old="no resource leftover", new="resource indicator", fail_err="401: leftover no resource leftover after resource indicator-only", plan="resource indicator-only 401s leftover no resource leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (resource indicator vs leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc8707", fetch1_ok="resource indicator is required, leftover missing fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#oauth-flow-object", fetch2_ok="Exclusive resource 401 leftover none."),
     p(slug="leftover-no-resource-param", domain="leftover-no-resource-param-vs-oas-resource-indicator", success=False, name="7fe1cf", stack="OpenAPI leftover resource + Java + TS", field="resource", old="resource indicator", new="no resource leftover only", fail_err="401: leftover resource indicator after no resource leftover-only", plan="no resource leftover-only 401s leftover resource indicator. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (no resource leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#oauth-flow-object", fetch1_ok="Exclusive resource 401 leftover none.", fetch2="https://datatracker.ietf.org/doc/html/rfc8707", fetch2_ok="resource indicator is required, leftover missing fails closed.")),
    (p(slug="oas-cors-expose-headers", domain="oas-cors-expose-headers-vs-leftover-unexposed-headers", success=True, name="c71f16", stack="OpenAPI 3.1 Access-Control-Expose-Headers + Go", field="Access-Control-Expose-Headers", old="unexposed leftover", new="CORS expose headers", fail_err="400: leftover unexposed leftover after CORS expose headers-only", plan="CORS expose headers-only 400s leftover unexposed leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (CORS expose headers vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch1_ok="non-simple headers must be exposed, leftover unexposed fails closed.", fetch2="https://datatracker.ietf.org/doc/html/rfc9110", fetch2_ok="Exclusive expose 400 leftover unexposed."),
     p(slug="leftover-unexposed-headers", domain="leftover-unexposed-headers-vs-oas-cors-expose-headers", success=False, name="f73db0", stack="OpenAPI leftover Access-Control-Expose-Headers + Java + TS", field="Access-Control-Expose-Headers", old="CORS expose headers", new="unexposed leftover only", fail_err="400: leftover CORS expose headers after unexposed leftover-only", plan="unexposed leftover-only 400s leftover CORS expose headers. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (unexposed leftover leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc9110", fetch1_ok="Exclusive expose 400 leftover unexposed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch2_ok="non-simple headers must be exposed, leftover unexposed fails closed.")),
    (p(slug="oas-if-unmodified-since", domain="oas-if-unmodified-since-vs-leftover-put-no-date-precond", success=True, name="c5f9d3", stack="OpenAPI 3.1 If-Unmodified-Since + Go", field="If-Unmodified-Since", old="no date leftover", new="If-Unmodified-Since", fail_err="412: leftover no date leftover after If-Unmodified-Since-only", plan="If-Unmodified-Since-only 412s leftover no date leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (If-Unmodified-Since vs leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc9110#name-if-unmodified-since", fetch1_ok="PUT should send If-Unmodified-Since, leftover missing fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="Exclusive If-Unmodified-Since 412 leftover none."),
     p(slug="leftover-put-no-date-precond", domain="leftover-put-no-date-precond-vs-oas-if-unmodified-since", success=False, name="392854", stack="OpenAPI leftover If-Unmodified-Since + Java + TS", field="If-Unmodified-Since", old="If-Unmodified-Since", new="no date leftover only", fail_err="412: leftover If-Unmodified-Since after no date leftover-only", plan="no date leftover-only 412s leftover If-Unmodified-Since. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (no date leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="Exclusive If-Unmodified-Since 412 leftover none.", fetch2="https://datatracker.ietf.org/doc/html/rfc9110#name-if-unmodified-since", fetch2_ok="PUT should send If-Unmodified-Since, leftover missing fails closed.")),
    (p(slug="oas-accept-encoding-gzip", domain="oas-accept-encoding-gzip-vs-leftover-identity-only-encoding", success=True, name="2df591", stack="OpenAPI 3.1 Accept-Encoding + Go", field="Accept-Encoding", old="identity only leftover", new="Accept-Encoding gzip", fail_err="400: leftover identity only leftover after Accept-Encoding gzip-only", plan="Accept-Encoding gzip-only 400s leftover identity only leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (Accept-Encoding gzip vs leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc9110#name-accept-encoding", fetch1_ok="gzip is accepted, leftover identity-only fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="Exclusive gzip 400 leftover identity."),
     p(slug="leftover-identity-only-encoding", domain="leftover-identity-only-encoding-vs-oas-accept-encoding-gzip", success=False, name="207db1", stack="OpenAPI leftover Accept-Encoding + Java + TS", field="Accept-Encoding", old="Accept-Encoding gzip", new="identity only leftover only", fail_err="400: leftover Accept-Encoding gzip after identity only leftover-only", plan="identity only leftover-only 400s leftover Accept-Encoding gzip. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (identity only leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="Exclusive gzip 400 leftover identity.", fetch2="https://datatracker.ietf.org/doc/html/rfc9110#name-accept-encoding", fetch2_ok="gzip is accepted, leftover identity-only fails closed.")),
    (p(slug="oas-content-encoding-gzip", domain="oas-content-encoding-gzip-vs-leftover-uncompressed-only", success=True, name="9af2ab", stack="OpenAPI 3.1 Content-Encoding + Go", field="Content-Encoding", old="uncompressed leftover", new="Content-Encoding gzip", fail_err="415: leftover uncompressed leftover after Content-Encoding gzip-only", plan="Content-Encoding gzip-only 415s leftover uncompressed leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (Content-Encoding gzip vs leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc9110#name-content-encoding", fetch1_ok="gzip content-encoding is not leftover uncompressed-only.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch2_ok="Exclusive gzip encoding 415 leftover uncompressed."),
     p(slug="leftover-uncompressed-only", domain="leftover-uncompressed-only-vs-oas-content-encoding-gzip", success=False, name="a5d9a6", stack="OpenAPI leftover Content-Encoding + Java + TS", field="Content-Encoding", old="Content-Encoding gzip", new="uncompressed leftover only", fail_err="415: leftover Content-Encoding gzip after uncompressed leftover-only", plan="uncompressed leftover-only 415s leftover Content-Encoding gzip. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (uncompressed leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch1_ok="Exclusive gzip encoding 415 leftover uncompressed.", fetch2="https://datatracker.ietf.org/doc/html/rfc9110#name-content-encoding", fetch2_ok="gzip content-encoding is not leftover uncompressed-only.")),
    (p(slug="oas-transfer-encoding-ban", domain="oas-transfer-encoding-ban-vs-leftover-chunked-declared", success=True, name="bf9cb4", stack="OpenAPI 3.1 Transfer-Encoding + Go", field="Transfer-Encoding", old="chunked leftover", new="Transfer-Encoding banned", fail_err="400: leftover chunked leftover after Transfer-Encoding banned-only", plan="Transfer-Encoding banned-only 400s leftover chunked leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (Transfer-Encoding banned vs leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc9112", fetch1_ok="HTTP/1.1 chunked should not be declared in OAS, leftover chunked fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch2_ok="Exclusive TE ban 400 leftover chunked."),
     p(slug="leftover-chunked-declared", domain="leftover-chunked-declared-vs-oas-transfer-encoding-ban", success=False, name="d1c529", stack="OpenAPI leftover Transfer-Encoding + Java + TS", field="Transfer-Encoding", old="Transfer-Encoding banned", new="chunked leftover only", fail_err="400: leftover Transfer-Encoding banned after chunked leftover-only", plan="chunked leftover-only 400s leftover Transfer-Encoding banned. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (chunked leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch1_ok="Exclusive TE ban 400 leftover chunked.", fetch2="https://datatracker.ietf.org/doc/html/rfc9112", fetch2_ok="HTTP/1.1 chunked should not be declared in OAS, leftover chunked fails closed.")),
    (p(slug="oas-http2-server-push-ban", domain="oas-http2-server-push-ban-vs-leftover-push-promise", success=True, name="82b26b", stack="OpenAPI 3.1 PUSH_PROMISE + Go", field="PUSH_PROMISE", old="push leftover", new="HTTP/2 push banned", fail_err="400: leftover push leftover after HTTP/2 push banned-only", plan="HTTP/2 push banned-only 400s leftover push leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (HTTP/2 push banned vs leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc9113", fetch1_ok="Server push is banned here, leftover PUSH_PROMISE fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch2_ok="Exclusive push ban 400 leftover push."),
     p(slug="leftover-push-promise", domain="leftover-push-promise-vs-oas-http2-server-push-ban", success=False, name="45d803", stack="OpenAPI leftover PUSH_PROMISE + Java + TS", field="PUSH_PROMISE", old="HTTP/2 push banned", new="push leftover only", fail_err="400: leftover HTTP/2 push banned after push leftover-only", plan="push leftover-only 400s leftover HTTP/2 push banned. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (push leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch1_ok="Exclusive push ban 400 leftover push.", fetch2="https://datatracker.ietf.org/doc/html/rfc9113", fetch2_ok="Server push is banned here, leftover PUSH_PROMISE fails closed.")),
    (p(slug="oas-websocket-upgrade-ban", domain="oas-websocket-upgrade-ban-vs-leftover-upgrade-websocket", success=True, name="9cd1c1", stack="OpenAPI 3.1 Upgrade + Go", field="Upgrade", old="websocket leftover", new="WebSocket upgrade banned", fail_err="400: leftover websocket leftover after WebSocket upgrade banned-only", plan="WebSocket upgrade banned-only 400s leftover websocket leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (WebSocket upgrade banned vs leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc6455", fetch1_ok="WebSocket upgrade is out of band, leftover Upgrade fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#path-item-object", fetch2_ok="Exclusive WS ban 400 leftover upgrade."),
     p(slug="leftover-upgrade-websocket", domain="leftover-upgrade-websocket-vs-oas-websocket-upgrade-ban", success=False, name="78f1f6", stack="OpenAPI leftover Upgrade + Java + TS", field="Upgrade", old="WebSocket upgrade banned", new="websocket leftover only", fail_err="400: leftover WebSocket upgrade banned after websocket leftover-only", plan="websocket leftover-only 400s leftover WebSocket upgrade banned. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (websocket leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#path-item-object", fetch1_ok="Exclusive WS ban 400 leftover upgrade.", fetch2="https://datatracker.ietf.org/doc/html/rfc6455", fetch2_ok="WebSocket upgrade is out of band, leftover Upgrade fails closed.")),
    (p(slug="oas-graphql-over-http-ban", domain="oas-graphql-over-http-ban-vs-leftover-graphql-post-json", success=True, name="ec0d13", stack="OpenAPI 3.1 graphql + Go", field="graphql", old="graphql leftover", new="GraphQL over HTTP banned", fail_err="415: leftover graphql leftover after GraphQL over HTTP banned-only", plan="GraphQL over HTTP banned-only 415s leftover graphql leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (GraphQL over HTTP banned vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch1_ok="This API is REST, leftover GraphQL POST fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch2_ok="Exclusive GraphQL ban 415 leftover graphql."),
     p(slug="leftover-graphql-post-json", domain="leftover-graphql-post-json-vs-oas-graphql-over-http-ban", success=False, name="5cb7f0", stack="OpenAPI leftover graphql + Java + TS", field="graphql", old="GraphQL over HTTP banned", new="graphql leftover only", fail_err="415: leftover GraphQL over HTTP banned after graphql leftover-only", plan="graphql leftover-only 415s leftover GraphQL over HTTP banned. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (graphql leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch1_ok="Exclusive GraphQL ban 415 leftover graphql.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch2_ok="This API is REST, leftover GraphQL POST fails closed.")),
    (p(slug="oas-prefer-return-minimal", domain="oas-prefer-return-minimal-vs-leftover-prefer-return-rep", success=True, name="5f4fa4", stack="OpenAPI 3.1 Prefer + Go", field="Prefer", old="return representation leftover", new="Prefer return=minimal", fail_err="400: leftover return representation leftover after Prefer return=minimal-only", plan="Prefer return=minimal-only 400s leftover return representation leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (Prefer return=minimal vs leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc7240", fetch1_ok="Prefer return=minimal is not leftover representation.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch2_ok="Exclusive return=minimal 400 leftover representation."),
     p(slug="leftover-prefer-return-rep", domain="leftover-prefer-return-rep-vs-oas-prefer-return-minimal", success=False, name="6698a5", stack="OpenAPI leftover Prefer + Java + TS", field="Prefer", old="Prefer return=minimal", new="return representation leftover only", fail_err="400: leftover Prefer return=minimal after return representation leftover-only", plan="return representation leftover-only 400s leftover Prefer return=minimal. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (return representation leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch1_ok="Exclusive return=minimal 400 leftover representation.", fetch2="https://datatracker.ietf.org/doc/html/rfc7240", fetch2_ok="Prefer return=minimal is not leftover representation.")),
    (p(slug="oas-prefer-handling-strict", domain="oas-prefer-handling-strict-vs-leftover-prefer-lenient", success=True, name="30312b", stack="OpenAPI 3.1 Prefer + Go", field="Prefer", old="lenient leftover", new="Prefer handling=strict", fail_err="400: leftover lenient leftover after Prefer handling=strict-only", plan="Prefer handling=strict-only 400s leftover lenient leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (Prefer handling=strict vs leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc7240", fetch1_ok="Prefer handling=strict is not leftover lenient.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch2_ok="Exclusive handling=strict 400 leftover lenient."),
     p(slug="leftover-prefer-lenient", domain="leftover-prefer-lenient-vs-oas-prefer-handling-strict", success=False, name="6f95ad", stack="OpenAPI leftover Prefer + Java + TS", field="Prefer", old="Prefer handling=strict", new="lenient leftover only", fail_err="400: leftover Prefer handling=strict after lenient leftover-only", plan="lenient leftover-only 400s leftover Prefer handling=strict. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (lenient leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch1_ok="Exclusive handling=strict 400 leftover lenient.", fetch2="https://datatracker.ietf.org/doc/html/rfc7240", fetch2_ok="Prefer handling=strict is not leftover lenient.")),
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
    print(json.dumps({"round": round_n, "idx": idx, "ids": [e1["id"], e2["id"]], "catalog": "r4534"}))


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
