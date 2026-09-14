#!/usr/bin/env python3
"""Unique OpenAPI-drift ACM catalog r4566. Fast slug load."""
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
    (p(slug="oas-permissions-policy", domain="oas-permissions-policy-vs-leftover-unrestricted-features", success=True, name="e59ee6", stack="OpenAPI 3.1 Permissions-Policy + Go", field="Permissions-Policy", old="unrestricted leftover", new="Permissions-Policy", fail_err="400: leftover unrestricted leftover after Permissions-Policy-only", plan="Permissions-Policy-only 400s leftover unrestricted leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (Permissions-Policy vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch1_ok="Permissions-Policy restricts features, leftover unrestricted fails closed.", fetch2="https://datatracker.ietf.org/doc/html/rfc9110", fetch2_ok="Exclusive Permissions-Policy 400 leftover unrestricted."),
     p(slug="leftover-unrestricted-features", domain="leftover-unrestricted-features-vs-oas-permissions-policy", success=False, name="1b3581", stack="OpenAPI leftover Permissions-Policy + Java + TS", field="Permissions-Policy", old="Permissions-Policy", new="unrestricted leftover only", fail_err="400: leftover Permissions-Policy after unrestricted leftover-only", plan="unrestricted leftover-only 400s leftover Permissions-Policy. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (unrestricted leftover leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc9110", fetch1_ok="Exclusive Permissions-Policy 400 leftover unrestricted.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch2_ok="Permissions-Policy restricts features, leftover unrestricted fails closed.")),
    (p(slug="oas-coop-same-origin", domain="oas-coop-same-origin-vs-leftover-no-coop", success=True, name="a44bd1", stack="OpenAPI 3.1 Cross-Origin-Opener-Policy + Go", field="Cross-Origin-Opener-Policy", old="no coop leftover", new="COOP same-origin", fail_err="400: leftover no coop leftover after COOP same-origin-only", plan="COOP same-origin-only 400s leftover no coop leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (COOP same-origin vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch1_ok="COOP same-origin is required, leftover missing fails closed.", fetch2="https://datatracker.ietf.org/doc/html/rfc9110", fetch2_ok="Exclusive COOP 400 leftover none."),
     p(slug="leftover-no-coop", domain="leftover-no-coop-vs-oas-coop-same-origin", success=False, name="bcfdcb", stack="OpenAPI leftover Cross-Origin-Opener-Policy + Java + TS", field="Cross-Origin-Opener-Policy", old="COOP same-origin", new="no coop leftover only", fail_err="400: leftover COOP same-origin after no coop leftover-only", plan="no coop leftover-only 400s leftover COOP same-origin. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (no coop leftover leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc9110", fetch1_ok="Exclusive COOP 400 leftover none.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch2_ok="COOP same-origin is required, leftover missing fails closed.")),
    (p(slug="oas-coep-require-corp", domain="oas-coep-require-corp-vs-leftover-no-coep", success=True, name="a13766", stack="OpenAPI 3.1 Cross-Origin-Embedder-Policy + Go", field="Cross-Origin-Embedder-Policy", old="no coep leftover", new="COEP require-corp", fail_err="400: leftover no coep leftover after COEP require-corp-only", plan="COEP require-corp-only 400s leftover no coep leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (COEP require-corp vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch1_ok="COEP require-corp is required, leftover missing fails closed.", fetch2="https://datatracker.ietf.org/doc/html/rfc9110", fetch2_ok="Exclusive COEP 400 leftover none."),
     p(slug="leftover-no-coep", domain="leftover-no-coep-vs-oas-coep-require-corp", success=False, name="3cf5a4", stack="OpenAPI leftover Cross-Origin-Embedder-Policy + Java + TS", field="Cross-Origin-Embedder-Policy", old="COEP require-corp", new="no coep leftover only", fail_err="400: leftover COEP require-corp after no coep leftover-only", plan="no coep leftover-only 400s leftover COEP require-corp. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (no coep leftover leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc9110", fetch1_ok="Exclusive COEP 400 leftover none.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch2_ok="COEP require-corp is required, leftover missing fails closed.")),
    (p(slug="oas-corp-same-origin", domain="oas-corp-same-origin-vs-leftover-no-corp", success=True, name="677bf2", stack="OpenAPI 3.1 Cross-Origin-Resource-Policy + Go", field="Cross-Origin-Resource-Policy", old="no corp leftover", new="CORP same-origin", fail_err="400: leftover no corp leftover after CORP same-origin-only", plan="CORP same-origin-only 400s leftover no corp leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (CORP same-origin vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch1_ok="CORP same-origin is required, leftover missing fails closed.", fetch2="https://datatracker.ietf.org/doc/html/rfc9110", fetch2_ok="Exclusive CORP 400 leftover none."),
     p(slug="leftover-no-corp", domain="leftover-no-corp-vs-oas-corp-same-origin", success=False, name="b61266", stack="OpenAPI leftover Cross-Origin-Resource-Policy + Java + TS", field="Cross-Origin-Resource-Policy", old="CORP same-origin", new="no corp leftover only", fail_err="400: leftover CORP same-origin after no corp leftover-only", plan="no corp leftover-only 400s leftover CORP same-origin. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (no corp leftover leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc9110", fetch1_ok="Exclusive CORP 400 leftover none.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch2_ok="CORP same-origin is required, leftover missing fails closed.")),
    (p(slug="oas-ref-siblings-oas31", domain="oas-ref-siblings-oas31-vs-leftover-ref-drop-siblings", success=True, name="d6f7cd", stack="OpenAPI 3.1 $ref + Go", field="$ref", old="drop siblings leftover", new="$ref siblings allowed", fail_err="400: leftover drop siblings leftover after $ref siblings allowed-only", plan="$ref siblings allowed-only 400s leftover drop siblings leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv ($ref siblings allowed vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="OAS 3.1 allows $ref siblings, leftover drop-siblings fails closed.", fetch2="https://json-schema.org/understanding-json-schema/reference/schema", fetch2_ok="Exclusive $ref siblings 400 leftover drop."),
     p(slug="leftover-ref-drop-siblings", domain="leftover-ref-drop-siblings-vs-oas-ref-siblings-oas31", success=False, name="364b97", stack="OpenAPI leftover $ref + Java + TS", field="$ref", old="$ref siblings allowed", new="drop siblings leftover only", fail_err="400: leftover $ref siblings allowed after drop siblings leftover-only", plan="drop siblings leftover-only 400s leftover $ref siblings allowed. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (drop siblings leftover leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/schema", fetch1_ok="Exclusive $ref siblings 400 leftover drop.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="OAS 3.1 allows $ref siblings, leftover drop-siblings fails closed.")),
    (p(slug="oas-license-id-xor-url", domain="oas-license-id-xor-url-vs-leftover-license-id-and-url", success=True, name="5242e8", stack="OpenAPI 3.1 identifier + Go", field="identifier", old="id and url leftover", new="license identifier xor url", fail_err="400: leftover id and url leftover after license identifier xor url-only", plan="license identifier xor url-only 400s leftover id and url leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (license identifier xor url vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#license-object", fetch1_ok="identifier and url are exclusive, leftover both fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#info-object", fetch2_ok="Exclusive xor 400 leftover both."),
     p(slug="leftover-license-id-and-url", domain="leftover-license-id-and-url-vs-oas-license-id-xor-url", success=False, name="0d605d", stack="OpenAPI leftover identifier + Java + TS", field="identifier", old="license identifier xor url", new="id and url leftover only", fail_err="400: leftover license identifier xor url after id and url leftover-only", plan="id and url leftover-only 400s leftover license identifier xor url. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (id and url leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#info-object", fetch1_ok="Exclusive xor 400 leftover both.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#license-object", fetch2_ok="identifier and url are exclusive, leftover both fails closed.")),
    (p(slug="oas-operation-tags-declared", domain="oas-operation-tags-declared-vs-leftover-undeclared-op-tag", success=True, name="c38f78", stack="OpenAPI 3.1 tags + Go", field="tags", old="undeclared tag leftover", new="operation tags declared", fail_err="400: leftover undeclared tag leftover after operation tags declared-only", plan="operation tags declared-only 400s leftover undeclared tag leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (operation tags declared vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch1_ok="operation tags must be declared in tags[], leftover undeclared fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#tag-object", fetch2_ok="Exclusive declared tags 400 leftover undeclared."),
     p(slug="leftover-undeclared-op-tag", domain="leftover-undeclared-op-tag-vs-oas-operation-tags-declared", success=False, name="d24728", stack="OpenAPI leftover tags + Java + TS", field="tags", old="operation tags declared", new="undeclared tag leftover only", fail_err="400: leftover operation tags declared after undeclared tag leftover-only", plan="undeclared tag leftover-only 400s leftover operation tags declared. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (undeclared tag leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#tag-object", fetch1_ok="Exclusive declared tags 400 leftover undeclared.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch2_ok="operation tags must be declared in tags[], leftover undeclared fails closed.")),
    (p(slug="oas-oauth2-pkce-s256", domain="oas-oauth2-pkce-s256-vs-leftover-pkce-plain", success=True, name="e9f968", stack="OpenAPI 3.1 code_challenge_method + Go", field="code_challenge_method", old="plain pkce leftover", new="PKCE S256", fail_err="401: leftover plain pkce leftover after PKCE S256-only", plan="PKCE S256-only 401s leftover plain pkce leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (PKCE S256 vs leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc7636", fetch1_ok="PKCE S256 is required, leftover plain fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#oauth-flow-object", fetch2_ok="Exclusive S256 401 leftover plain."),
     p(slug="leftover-pkce-plain", domain="leftover-pkce-plain-vs-oas-oauth2-pkce-s256", success=False, name="ce1b75", stack="OpenAPI leftover code_challenge_method + Java + TS", field="code_challenge_method", old="PKCE S256", new="plain pkce leftover only", fail_err="401: leftover PKCE S256 after plain pkce leftover-only", plan="plain pkce leftover-only 401s leftover PKCE S256. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (plain pkce leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#oauth-flow-object", fetch1_ok="Exclusive S256 401 leftover plain.", fetch2="https://datatracker.ietf.org/doc/html/rfc7636", fetch2_ok="PKCE S256 is required, leftover plain fails closed.")),
    (p(slug="oas-jwks-uri-https", domain="oas-jwks-uri-https-vs-leftover-jwks-http", success=True, name="bfc27b", stack="OpenAPI 3.1 jwks_uri + Go", field="jwks_uri", old="http jwks leftover", new="jwks_uri https", fail_err="401: leftover http jwks leftover after jwks_uri https-only", plan="jwks_uri https-only 401s leftover http jwks leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (jwks_uri https vs leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc7517", fetch1_ok="jwks_uri must be https, leftover http fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch2_ok="Exclusive jwks https 401 leftover http."),
     p(slug="leftover-jwks-http", domain="leftover-jwks-http-vs-oas-jwks-uri-https", success=False, name="14e922", stack="OpenAPI leftover jwks_uri + Java + TS", field="jwks_uri", old="jwks_uri https", new="http jwks leftover only", fail_err="401: leftover jwks_uri https after http jwks leftover-only", plan="http jwks leftover-only 401s leftover jwks_uri https. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (http jwks leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch1_ok="Exclusive jwks https 401 leftover http.", fetch2="https://datatracker.ietf.org/doc/html/rfc7517", fetch2_ok="jwks_uri must be https, leftover http fails closed.")),
    (p(slug="oas-issuer-no-trailing-slash", domain="oas-issuer-no-trailing-slash-vs-leftover-issuer-slash-mismatch", success=True, name="670271", stack="OpenAPI 3.1 issuer + Go", field="issuer", old="slash mismatch leftover", new="issuer no trailing slash", fail_err="401: leftover slash mismatch leftover after issuer no trailing slash-only", plan="issuer no trailing slash-only 401s leftover slash mismatch leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (issuer no trailing slash vs leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc8414", fetch1_ok="issuer strings must match exactly, leftover slash mismatch fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch2_ok="Exclusive issuer 401 leftover slash."),
     p(slug="leftover-issuer-slash-mismatch", domain="leftover-issuer-slash-mismatch-vs-oas-issuer-no-trailing-slash", success=False, name="093efd", stack="OpenAPI leftover issuer + Java + TS", field="issuer", old="issuer no trailing slash", new="slash mismatch leftover only", fail_err="401: leftover issuer no trailing slash after slash mismatch leftover-only", plan="slash mismatch leftover-only 401s leftover issuer no trailing slash. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (slash mismatch leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch1_ok="Exclusive issuer 401 leftover slash.", fetch2="https://datatracker.ietf.org/doc/html/rfc8414", fetch2_ok="issuer strings must match exactly, leftover slash mismatch fails closed.")),
    (p(slug="oas-revocation-endpoint", domain="oas-revocation-endpoint-vs-leftover-delete-as-revoke", success=True, name="ee1424", stack="OpenAPI 3.1 revocation_endpoint + Go", field="revocation_endpoint", old="DELETE as revoke leftover", new="token revocation endpoint", fail_err="401: leftover DELETE as revoke leftover after token revocation endpoint-only", plan="token revocation endpoint-only 401s leftover DELETE as revoke leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (token revocation endpoint vs leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc7009", fetch1_ok="revocation_endpoint is not leftover DELETE-as-revoke.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#oauth-flow-object", fetch2_ok="Exclusive revocation 401 leftover DELETE."),
     p(slug="leftover-delete-as-revoke", domain="leftover-delete-as-revoke-vs-oas-revocation-endpoint", success=False, name="7ad5ea", stack="OpenAPI leftover revocation_endpoint + Java + TS", field="revocation_endpoint", old="token revocation endpoint", new="DELETE as revoke leftover only", fail_err="401: leftover token revocation endpoint after DELETE as revoke leftover-only", plan="DELETE as revoke leftover-only 401s leftover token revocation endpoint. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (DELETE as revoke leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#oauth-flow-object", fetch1_ok="Exclusive revocation 401 leftover DELETE.", fetch2="https://datatracker.ietf.org/doc/html/rfc7009", fetch2_ok="revocation_endpoint is not leftover DELETE-as-revoke.")),
    (p(slug="oas-introspection-endpoint", domain="oas-introspection-endpoint-vs-leftover-decode-jwt-locally", success=True, name="797528", stack="OpenAPI 3.1 introspection_endpoint + Go", field="introspection_endpoint", old="local jwt decode leftover", new="token introspection", fail_err="401: leftover local jwt decode leftover after token introspection-only", plan="token introspection-only 401s leftover local jwt decode leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (token introspection vs leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc7662", fetch1_ok="introspection_endpoint is not leftover local JWT decode.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#oauth-flow-object", fetch2_ok="Exclusive introspection 401 leftover local decode."),
     p(slug="leftover-decode-jwt-locally", domain="leftover-decode-jwt-locally-vs-oas-introspection-endpoint", success=False, name="a25e9a", stack="OpenAPI leftover introspection_endpoint + Java + TS", field="introspection_endpoint", old="token introspection", new="local jwt decode leftover only", fail_err="401: leftover token introspection after local jwt decode leftover-only", plan="local jwt decode leftover-only 401s leftover token introspection. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (local jwt decode leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#oauth-flow-object", fetch1_ok="Exclusive introspection 401 leftover local decode.", fetch2="https://datatracker.ietf.org/doc/html/rfc7662", fetch2_ok="introspection_endpoint is not leftover local JWT decode.")),
    (p(slug="oas-maxcontains-needs-contains", domain="oas-maxcontains-needs-contains-vs-leftover-maxcontains-alone", success=True, name="00e461", stack="OpenAPI 3.1 maxContains + Go", field="maxContains", old="maxContains alone leftover", new="maxContains with contains", fail_err="400: leftover maxContains alone leftover after maxContains with contains-only", plan="maxContains with contains-only 400s leftover maxContains alone leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (maxContains with contains vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/array#maxcontains", fetch1_ok="maxContains requires contains, leftover alone fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive maxContains+contains 400 leftover alone."),
     p(slug="leftover-maxcontains-alone", domain="leftover-maxcontains-alone-vs-oas-maxcontains-needs-contains", success=False, name="56552c", stack="OpenAPI leftover maxContains + Java + TS", field="maxContains", old="maxContains with contains", new="maxContains alone leftover only", fail_err="400: leftover maxContains with contains after maxContains alone leftover-only", plan="maxContains alone leftover-only 400s leftover maxContains with contains. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (maxContains alone leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive maxContains+contains 400 leftover alone.", fetch2="https://json-schema.org/understanding-json-schema/reference/array#maxcontains", fetch2_ok="maxContains requires contains, leftover alone fails closed.")),
    (p(slug="oas-mincontains-needs-contains", domain="oas-mincontains-needs-contains-vs-leftover-mincontains-alone", success=True, name="e6e583", stack="OpenAPI 3.1 minContains + Go", field="minContains", old="minContains alone leftover", new="minContains with contains", fail_err="400: leftover minContains alone leftover after minContains with contains-only", plan="minContains with contains-only 400s leftover minContains alone leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (minContains with contains vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/array#mincontains", fetch1_ok="minContains requires contains, leftover alone fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive minContains+contains 400 leftover alone."),
     p(slug="leftover-mincontains-alone", domain="leftover-mincontains-alone-vs-oas-mincontains-needs-contains", success=False, name="ca9d1e", stack="OpenAPI leftover minContains + Java + TS", field="minContains", old="minContains with contains", new="minContains alone leftover only", fail_err="400: leftover minContains with contains after minContains alone leftover-only", plan="minContains alone leftover-only 400s leftover minContains with contains. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (minContains alone leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive minContains+contains 400 leftover alone.", fetch2="https://json-schema.org/understanding-json-schema/reference/array#mincontains", fetch2_ok="minContains requires contains, leftover alone fails closed.")),
    (p(slug="oas-dynamicref-needs-anchor", domain="oas-dynamicref-needs-anchor-vs-leftover-dynamicref-as-ref", success=True, name="d95118", stack="OpenAPI 3.1 $dynamicRef + Go", field="$dynamicRef", old="dynamicRef as ref leftover", new="$dynamicRef needs $dynamicAnchor", fail_err="400: leftover dynamicRef as ref leftover after $dynamicRef needs $dynamicAnchor-only", plan="$dynamicRef needs $dynamicAnchor-only 400s leftover dynamicRef as ref leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv ($dynamicRef needs $dynamicAnchor vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/schema#dynamic-references", fetch1_ok="$dynamicRef needs a $dynamicAnchor, leftover $ref fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive $dynamicRef 400 leftover $ref."),
     p(slug="leftover-dynamicref-as-ref", domain="leftover-dynamicref-as-ref-vs-oas-dynamicref-needs-anchor", success=False, name="c6b732", stack="OpenAPI leftover $dynamicRef + Java + TS", field="$dynamicRef", old="$dynamicRef needs $dynamicAnchor", new="dynamicRef as ref leftover only", fail_err="400: leftover $dynamicRef needs $dynamicAnchor after dynamicRef as ref leftover-only", plan="dynamicRef as ref leftover-only 400s leftover $dynamicRef needs $dynamicAnchor. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (dynamicRef as ref leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive $dynamicRef 400 leftover $ref.", fetch2="https://json-schema.org/understanding-json-schema/reference/schema#dynamic-references", fetch2_ok="$dynamicRef needs a $dynamicAnchor, leftover $ref fails closed.")),
    (p(slug="oas-anchor-unique-resource", domain="oas-anchor-unique-resource-vs-leftover-duplicate-anchor", success=True, name="8e19aa", stack="OpenAPI 3.1 $anchor + Go", field="$anchor", old="duplicate anchor leftover", new="$anchor unique in resource", fail_err="400: leftover duplicate anchor leftover after $anchor unique in resource-only", plan="$anchor unique in resource-only 400s leftover duplicate anchor leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv ($anchor unique in resource vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/schema#anchor", fetch1_ok="$anchor must be unique in a resource, leftover duplicates fail closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive unique $anchor 400 leftover duplicate."),
     p(slug="leftover-duplicate-anchor", domain="leftover-duplicate-anchor-vs-oas-anchor-unique-resource", success=False, name="292bbf", stack="OpenAPI leftover $anchor + Java + TS", field="$anchor", old="$anchor unique in resource", new="duplicate anchor leftover only", fail_err="400: leftover $anchor unique in resource after duplicate anchor leftover-only", plan="duplicate anchor leftover-only 400s leftover $anchor unique in resource. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (duplicate anchor leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive unique $anchor 400 leftover duplicate.", fetch2="https://json-schema.org/understanding-json-schema/reference/schema#anchor", fetch2_ok="$anchor must be unique in a resource, leftover duplicates fail closed.")),
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
    print(json.dumps({"round": round_n, "idx": idx, "ids": [e1["id"], e2["id"]], "catalog": "r4566"}))


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
