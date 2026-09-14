#!/usr/bin/env python3
"""Unique OpenAPI-drift ACM catalog r4486. Fast slug load."""
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
    (p(slug="oas-type-boolean-strict", domain="oas-type-boolean-strict-vs-leftover-truthy-string", success=True, name="ed93ef", stack="OpenAPI 3.1 type + Go", field="type", old="truthy string leftover", new="boolean strict", fail_err="400: leftover truthy string leftover after boolean strict-only", plan="boolean strict-only 400s leftover truthy string leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (boolean strict vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/boolean", fetch1_ok="type=boolean rejects leftover truthy strings.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="Exclusive boolean 400 leftover truthy."),
     p(slug="leftover-truthy-string", domain="leftover-truthy-string-vs-oas-type-boolean-strict", success=False, name="1ea2c2", stack="OpenAPI leftover type + Java + TS", field="type", old="boolean strict", new="truthy string leftover only", fail_err="400: leftover boolean strict after truthy string leftover-only", plan="truthy string leftover-only 400s leftover boolean strict. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (truthy string leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="Exclusive boolean 400 leftover truthy.", fetch2="https://json-schema.org/understanding-json-schema/reference/boolean", fetch2_ok="type=boolean rejects leftover truthy strings.")),
    (p(slug="oas-type-object-not-array", domain="oas-type-object-not-array-vs-leftover-array-as-object", success=True, name="d2abe0", stack="OpenAPI 3.1 type + Go", field="type", old="array as object leftover", new="type object", fail_err="400: leftover array as object leftover after type object-only", plan="type object-only 400s leftover array as object leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (type object vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/object", fetch1_ok="type=object rejects leftover arrays.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="Exclusive object 400 leftover array."),
     p(slug="leftover-array-as-object", domain="leftover-array-as-object-vs-oas-type-object-not-array", success=False, name="229a78", stack="OpenAPI leftover type + Java + TS", field="type", old="type object", new="array as object leftover only", fail_err="400: leftover type object after array as object leftover-only", plan="array as object leftover-only 400s leftover type object. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (array as object leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="Exclusive object 400 leftover array.", fetch2="https://json-schema.org/understanding-json-schema/reference/object", fetch2_ok="type=object rejects leftover arrays.")),
    (p(slug="oas-type-array-not-object", domain="oas-type-array-not-object-vs-leftover-object-as-array", success=True, name="b8d713", stack="OpenAPI 3.1 type + Go", field="type", old="object as array leftover", new="type array", fail_err="400: leftover object as array leftover after type array-only", plan="type array-only 400s leftover object as array leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (type array vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/array", fetch1_ok="type=array rejects leftover objects.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="Exclusive array 400 leftover object."),
     p(slug="leftover-object-as-array", domain="leftover-object-as-array-vs-oas-type-array-not-object", success=False, name="d51d33", stack="OpenAPI leftover type + Java + TS", field="type", old="type array", new="object as array leftover only", fail_err="400: leftover type array after object as array leftover-only", plan="object as array leftover-only 400s leftover type array. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (object as array leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="Exclusive array 400 leftover object.", fetch2="https://json-schema.org/understanding-json-schema/reference/array", fetch2_ok="type=array rejects leftover objects.")),
    (p(slug="oas-format-uri-abs-only", domain="oas-format-uri-abs-only-vs-leftover-path-as-uri", success=True, name="79cac5", stack="OpenAPI 3.1 format + Go", field="format", old="path as uri leftover", new="format uri absolute", fail_err="400: leftover path as uri leftover after format uri absolute-only", plan="format uri absolute-only 400s leftover path as uri leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (format uri absolute vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/string#resource-identifiers", fetch1_ok="format=uri is absolute, leftover paths fail closed.", fetch2="https://datatracker.ietf.org/doc/html/rfc3986", fetch2_ok="Exclusive uri 400 leftover path."),
     p(slug="leftover-path-as-uri", domain="leftover-path-as-uri-vs-oas-format-uri-abs-only", success=False, name="186241", stack="OpenAPI leftover format + Java + TS", field="format", old="format uri absolute", new="path as uri leftover only", fail_err="400: leftover format uri absolute after path as uri leftover-only", plan="path as uri leftover-only 400s leftover format uri absolute. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (path as uri leftover leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc3986", fetch1_ok="Exclusive uri 400 leftover path.", fetch2="https://json-schema.org/understanding-json-schema/reference/string#resource-identifiers", fetch2_ok="format=uri is absolute, leftover paths fail closed.")),
    (p(slug="oas-format-email-dot-atom", domain="oas-format-email-dot-atom-vs-leftover-email-no-tld", success=True, name="839c6e", stack="OpenAPI 3.1 format + Go", field="format", old="email no tld leftover", new="format email dot-atom", fail_err="400: leftover email no tld leftover after format email dot-atom-only", plan="format email dot-atom-only 400s leftover email no tld leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (format email dot-atom vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/string#resource-identifiers", fetch1_ok="format=email needs a domain, leftover no-tld fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="Exclusive email 400 leftover no tld."),
     p(slug="leftover-email-no-tld", domain="leftover-email-no-tld-vs-oas-format-email-dot-atom", success=False, name="471ac3", stack="OpenAPI leftover format + Java + TS", field="format", old="format email dot-atom", new="email no tld leftover only", fail_err="400: leftover format email dot-atom after email no tld leftover-only", plan="email no tld leftover-only 400s leftover format email dot-atom. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (email no tld leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="Exclusive email 400 leftover no tld.", fetch2="https://json-schema.org/understanding-json-schema/reference/string#resource-identifiers", fetch2_ok="format=email needs a domain, leftover no-tld fails closed.")),
    (p(slug="oas-http-basic-scheme", domain="oas-http-basic-scheme-vs-leftover-basic-in-query", success=True, name="ad3874", stack="OpenAPI 3.1 scheme + Go", field="scheme", old="basic in query leftover", new="HTTP basic", fail_err="401: leftover basic in query leftover after HTTP basic-only", plan="HTTP basic-only 401s leftover basic in query leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (HTTP basic vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch1_ok="HTTP basic is an Authorization header, leftover query fails closed.", fetch2="https://datatracker.ietf.org/doc/html/rfc7617", fetch2_ok="Exclusive basic 401 leftover query."),
     p(slug="leftover-basic-in-query", domain="leftover-basic-in-query-vs-oas-http-basic-scheme", success=False, name="37e2ee", stack="OpenAPI leftover scheme + Java + TS", field="scheme", old="HTTP basic", new="basic in query leftover only", fail_err="401: leftover HTTP basic after basic in query leftover-only", plan="basic in query leftover-only 401s leftover HTTP basic. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (basic in query leftover leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc7617", fetch1_ok="Exclusive basic 401 leftover query.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch2_ok="HTTP basic is an Authorization header, leftover query fails closed.")),
    (p(slug="oas-oauth2-auth-url-https", domain="oas-oauth2-auth-url-https-vs-leftover-auth-url-http", success=True, name="278210", stack="OpenAPI 3.1 authorizationUrl + Go", field="authorizationUrl", old="http auth url leftover", new="authorizationUrl https", fail_err="401: leftover http auth url leftover after authorizationUrl https-only", plan="authorizationUrl https-only 401s leftover http auth url leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (authorizationUrl https vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#oauth-flow-object", fetch1_ok="authorizationUrl must be https, leftover http fails closed.", fetch2="https://datatracker.ietf.org/doc/html/rfc6749", fetch2_ok="Exclusive auth https 401 leftover http."),
     p(slug="leftover-auth-url-http", domain="leftover-auth-url-http-vs-oas-oauth2-auth-url-https", success=False, name="85b00f", stack="OpenAPI leftover authorizationUrl + Java + TS", field="authorizationUrl", old="authorizationUrl https", new="http auth url leftover only", fail_err="401: leftover authorizationUrl https after http auth url leftover-only", plan="http auth url leftover-only 401s leftover authorizationUrl https. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (http auth url leftover leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc6749", fetch1_ok="Exclusive auth https 401 leftover http.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#oauth-flow-object", fetch2_ok="authorizationUrl must be https, leftover http fails closed.")),
    (p(slug="oas-oauth2-token-url-https", domain="oas-oauth2-token-url-https-vs-leftover-token-url-http", success=True, name="6e98fc", stack="OpenAPI 3.1 tokenUrl + Go", field="tokenUrl", old="http token url leftover", new="tokenUrl https", fail_err="401: leftover http token url leftover after tokenUrl https-only", plan="tokenUrl https-only 401s leftover http token url leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (tokenUrl https vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#oauth-flow-object", fetch1_ok="tokenUrl must be https, leftover http fails closed.", fetch2="https://datatracker.ietf.org/doc/html/rfc6749", fetch2_ok="Exclusive token https 401 leftover http."),
     p(slug="leftover-token-url-http", domain="leftover-token-url-http-vs-oas-oauth2-token-url-https", success=False, name="1d2153", stack="OpenAPI leftover tokenUrl + Java + TS", field="tokenUrl", old="tokenUrl https", new="http token url leftover only", fail_err="401: leftover tokenUrl https after http token url leftover-only", plan="http token url leftover-only 401s leftover tokenUrl https. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (http token url leftover leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc6749", fetch1_ok="Exclusive token https 401 leftover http.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#oauth-flow-object", fetch2_ok="tokenUrl must be https, leftover http fails closed.")),
    (p(slug="oas-head-no-response-body", domain="oas-head-no-response-body-vs-leftover-head-with-body", success=True, name="d6fdaa", stack="OpenAPI 3.1 head + Go", field="head", old="HEAD body leftover", new="HEAD no body", fail_err="400: leftover HEAD body leftover after HEAD no body-only", plan="HEAD no body-only 400s leftover HEAD body leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (HEAD no body vs leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc9110#name-head", fetch1_ok="HEAD responses have no body, leftover bodies fail closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#path-item-object", fetch2_ok="Exclusive HEAD empty 400 leftover body."),
     p(slug="leftover-head-with-body", domain="leftover-head-with-body-vs-oas-head-no-response-body", success=False, name="8123be", stack="OpenAPI leftover head + Java + TS", field="head", old="HEAD no body", new="HEAD body leftover only", fail_err="400: leftover HEAD no body after HEAD body leftover-only", plan="HEAD body leftover-only 400s leftover HEAD no body. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (HEAD body leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#path-item-object", fetch1_ok="Exclusive HEAD empty 400 leftover body.", fetch2="https://datatracker.ietf.org/doc/html/rfc9110#name-head", fetch2_ok="HEAD responses have no body, leftover bodies fail closed.")),
    (p(slug="oas-options-allow-header", domain="oas-options-allow-header-vs-leftover-options-no-allow", success=True, name="b7b87f", stack="OpenAPI 3.1 Allow + Go", field="Allow", old="no Allow leftover", new="OPTIONS Allow header", fail_err="400: leftover no Allow leftover after OPTIONS Allow header-only", plan="OPTIONS Allow header-only 400s leftover no Allow leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (OPTIONS Allow header vs leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc9110#name-options", fetch1_ok="OPTIONS should list Allow, leftover missing fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch2_ok="Exclusive Allow 400 leftover none."),
     p(slug="leftover-options-no-allow", domain="leftover-options-no-allow-vs-oas-options-allow-header", success=False, name="60011b", stack="OpenAPI leftover Allow + Java + TS", field="Allow", old="OPTIONS Allow header", new="no Allow leftover only", fail_err="400: leftover OPTIONS Allow header after no Allow leftover-only", plan="no Allow leftover-only 400s leftover OPTIONS Allow header. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (no Allow leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch1_ok="Exclusive Allow 400 leftover none.", fetch2="https://datatracker.ietf.org/doc/html/rfc9110#name-options", fetch2_ok="OPTIONS should list Allow, leftover missing fails closed.")),
    (p(slug="oas-server-default-in-enum", domain="oas-server-default-in-enum-vs-leftover-server-default-off-enum", success=True, name="9d2e5e", stack="OpenAPI 3.1 default + Go", field="default", old="default outside enum leftover", new="server default in enum", fail_err="400: leftover default outside enum leftover after server default in enum-only", plan="server default in enum-only 400s leftover default outside enum leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (server default in enum vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#server-variable-object", fetch1_ok="server default must be in enum, leftover outside fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#server-object", fetch2_ok="Exclusive default in enum 400 leftover outside."),
     p(slug="leftover-server-default-off-enum", domain="leftover-server-default-off-enum-vs-oas-server-default-in-enum", success=False, name="2ac9ee", stack="OpenAPI leftover default + Java + TS", field="default", old="server default in enum", new="default outside enum leftover only", fail_err="400: leftover server default in enum after default outside enum leftover-only", plan="default outside enum leftover-only 400s leftover server default in enum. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (default outside enum leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#server-object", fetch1_ok="Exclusive default in enum 400 leftover outside.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#server-variable-object", fetch2_ok="server default must be in enum, leftover outside fails closed.")),
    (p(slug="oas-xml-name-ncname", domain="oas-xml-name-ncname-vs-leftover-xml-name-colon", success=True, name="a6b92b", stack="OpenAPI 3.1 name + Go", field="name", old="colon name leftover", new="xml name NCName", fail_err="415: leftover colon name leftover after xml name NCName-only", plan="xml name NCName-only 415s leftover colon name leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (xml name NCName vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#xml-object", fetch1_ok="xml.name is an NCName, leftover colons fail closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive NCName 415 leftover colon."),
     p(slug="leftover-xml-name-colon", domain="leftover-xml-name-colon-vs-oas-xml-name-ncname", success=False, name="b26cf0", stack="OpenAPI leftover name + Java + TS", field="name", old="xml name NCName", new="colon name leftover only", fail_err="415: leftover xml name NCName after colon name leftover-only", plan="colon name leftover-only 415s leftover xml name NCName. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (colon name leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive NCName 415 leftover colon.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#xml-object", fetch2_ok="xml.name is an NCName, leftover colons fail closed.")),
    (p(slug="oas-discriminator-mapping-uri", domain="oas-discriminator-mapping-uri-vs-leftover-mapping-short-name", success=True, name="d22aac", stack="OpenAPI 3.1 mapping + Go", field="mapping", old="short name leftover", new="discriminator mapping uri", fail_err="400: leftover short name leftover after discriminator mapping uri-only", plan="discriminator mapping uri-only 400s leftover short name leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (discriminator mapping uri vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#discriminator-object", fetch1_ok="mapping values are schema URIs, leftover short names fail closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive mapping uri 400 leftover short name."),
     p(slug="leftover-mapping-short-name", domain="leftover-mapping-short-name-vs-oas-discriminator-mapping-uri", success=False, name="545672", stack="OpenAPI leftover mapping + Java + TS", field="mapping", old="discriminator mapping uri", new="short name leftover only", fail_err="400: leftover discriminator mapping uri after short name leftover-only", plan="short name leftover-only 400s leftover discriminator mapping uri. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (short name leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive mapping uri 400 leftover short name.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#discriminator-object", fetch2_ok="mapping values are schema URIs, leftover short names fail closed.")),
    (p(slug="oas-callback-expression-query", domain="oas-callback-expression-query-vs-leftover-callback-query-hardcoded", success=True, name="6492ca", stack="OpenAPI 3.1 expression + Go", field="expression", old="hardcoded query leftover", new="callback query expr", fail_err="400: leftover hardcoded query leftover after callback query expr-only", plan="callback query expr-only 400s leftover hardcoded query leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (callback query expr vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#runtime-expressions", fetch1_ok="Callback query expressions are not leftover hardcoded query strings.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#callback-object", fetch2_ok="Exclusive query expr 400 leftover hardcoded."),
     p(slug="leftover-callback-query-hardcoded", domain="leftover-callback-query-hardcoded-vs-oas-callback-expression-query", success=False, name="b13754", stack="OpenAPI leftover expression + Java + TS", field="expression", old="callback query expr", new="hardcoded query leftover only", fail_err="400: leftover callback query expr after hardcoded query leftover-only", plan="hardcoded query leftover-only 400s leftover callback query expr. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (hardcoded query leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#callback-object", fetch1_ok="Exclusive query expr 400 leftover hardcoded.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#runtime-expressions", fetch2_ok="Callback query expressions are not leftover hardcoded query strings.")),
    (p(slug="oas-link-server-https", domain="oas-link-server-https-vs-leftover-link-http-server", success=True, name="202306", stack="OpenAPI 3.1 server + Go", field="server", old="link http leftover", new="link server https", fail_err="400: leftover link http leftover after link server https-only", plan="link server https-only 400s leftover link http leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (link server https vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#link-object", fetch1_ok="link.server must be https, leftover http fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#server-object", fetch2_ok="Exclusive link https 400 leftover http."),
     p(slug="leftover-link-http-server", domain="leftover-link-http-server-vs-oas-link-server-https", success=False, name="098922", stack="OpenAPI leftover server + Java + TS", field="server", old="link server https", new="link http leftover only", fail_err="400: leftover link server https after link http leftover-only", plan="link http leftover-only 400s leftover link server https. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (link http leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#server-object", fetch1_ok="Exclusive link https 400 leftover http.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#link-object", fetch2_ok="link.server must be https, leftover http fails closed.")),
    (p(slug="oas-response-3xx-location", domain="oas-response-3xx-location-vs-leftover-redirect-no-location", success=True, name="806f24", stack="OpenAPI 3.1 Location + Go", field="Location", old="redirect no location leftover", new="3xx Location header", fail_err="400: leftover redirect no location leftover after 3xx Location header-only", plan="3xx Location header-only 400s leftover redirect no location leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (3xx Location header vs leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc9110#name-redirection-3xx", fetch1_ok="3xx responses need Location, leftover missing fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#response-object", fetch2_ok="Exclusive Location 400 leftover none."),
     p(slug="leftover-redirect-no-location", domain="leftover-redirect-no-location-vs-oas-response-3xx-location", success=False, name="625b16", stack="OpenAPI leftover Location + Java + TS", field="Location", old="3xx Location header", new="redirect no location leftover only", fail_err="400: leftover 3xx Location header after redirect no location leftover-only", plan="redirect no location leftover-only 400s leftover 3xx Location header. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (redirect no location leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#response-object", fetch1_ok="Exclusive Location 400 leftover none.", fetch2="https://datatracker.ietf.org/doc/html/rfc9110#name-redirection-3xx", fetch2_ok="3xx responses need Location, leftover missing fails closed.")),
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
    print(json.dumps({"round": round_n, "idx": idx, "ids": [e1["id"], e2["id"]], "catalog": "r4486"}))


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
