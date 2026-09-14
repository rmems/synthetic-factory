#!/usr/bin/env python3
"""Unique OpenAPI-drift ACM catalog r4342. Fast slug load."""
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
    (p(slug="oas-webhook-servers-item", domain="oas-webhook-servers-item-vs-leftover-webhook-root-server-only", success=True, name="cdff99", stack="OpenAPI 3.1 servers + Go", field="servers", old="root webhook leftover", new="webhook servers", fail_err="400: leftover root webhook leftover after webhook servers-only", plan="webhook servers-only 400s leftover root webhook leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (webhook servers vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#oasWebhooks", fetch1_ok="webhook servers override root, leftover root-only fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#server-object", fetch2_ok="Exclusive webhook servers 400 leftover root."),
     p(slug="leftover-webhook-root-server-only", domain="leftover-webhook-root-server-only-vs-oas-webhook-servers-item", success=False, name="3702b1", stack="OpenAPI leftover servers + Java + TS", field="servers", old="webhook servers", new="root webhook leftover only", fail_err="400: leftover webhook servers after root webhook leftover-only", plan="root webhook leftover-only 400s leftover webhook servers. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (root webhook leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#server-object", fetch1_ok="Exclusive webhook servers 400 leftover root.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#oasWebhooks", fetch2_ok="webhook servers override root, leftover root-only fails closed.")),
    (p(slug="oas-operation-external-docs-url", domain="oas-operation-external-docs-url-vs-leftover-op-no-external-docs", success=True, name="054bc6", stack="OpenAPI 3.1 externalDocs + Go", field="externalDocs", old="op no docs leftover", new="operation externalDocs", fail_err="400: leftover op no docs leftover after operation externalDocs-only", plan="operation externalDocs-only 400s leftover op no docs leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (operation externalDocs vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch1_ok="operation.externalDocs.url is required when present, leftover missing fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#external-documentation-object", fetch2_ok="Exclusive op docs 400 leftover none."),
     p(slug="leftover-op-no-external-docs", domain="leftover-op-no-external-docs-vs-oas-operation-external-docs-url", success=False, name="57db55", stack="OpenAPI leftover externalDocs + Java + TS", field="externalDocs", old="operation externalDocs", new="op no docs leftover only", fail_err="400: leftover operation externalDocs after op no docs leftover-only", plan="op no docs leftover-only 400s leftover operation externalDocs. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (op no docs leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#external-documentation-object", fetch1_ok="Exclusive op docs 400 leftover none.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch2_ok="operation.externalDocs.url is required when present, leftover missing fails closed.")),
    (p(slug="oas-tag-external-docs-url", domain="oas-tag-external-docs-url-vs-leftover-tag-no-docs", success=True, name="1cac69", stack="OpenAPI 3.1 externalDocs + Go", field="externalDocs", old="tag no docs leftover", new="tag externalDocs", fail_err="400: leftover tag no docs leftover after tag externalDocs-only", plan="tag externalDocs-only 400s leftover tag no docs leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (tag externalDocs vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#tag-object", fetch1_ok="tag.externalDocs.url is required when present, leftover missing fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#external-documentation-object", fetch2_ok="Exclusive tag docs 400 leftover none."),
     p(slug="leftover-tag-no-docs", domain="leftover-tag-no-docs-vs-oas-tag-external-docs-url", success=False, name="47fbac", stack="OpenAPI leftover externalDocs + Java + TS", field="externalDocs", old="tag externalDocs", new="tag no docs leftover only", fail_err="400: leftover tag externalDocs after tag no docs leftover-only", plan="tag no docs leftover-only 400s leftover tag externalDocs. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (tag no docs leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#external-documentation-object", fetch1_ok="Exclusive tag docs 400 leftover none.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#tag-object", fetch2_ok="tag.externalDocs.url is required when present, leftover missing fails closed.")),
    (p(slug="oas-info-license-url-https", domain="oas-info-license-url-https-vs-leftover-license-http-url", success=True, name="98b722", stack="OpenAPI 3.1 url + Go", field="url", old="http license leftover", new="license url https", fail_err="400: leftover http license leftover after license url https-only", plan="license url https-only 400s leftover http license leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (license url https vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#license-object", fetch1_ok="license.url must be https, leftover http fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#info-object", fetch2_ok="Exclusive license https 400 leftover http."),
     p(slug="leftover-license-http-url", domain="leftover-license-http-url-vs-oas-info-license-url-https", success=False, name="b235c9", stack="OpenAPI leftover url + Java + TS", field="url", old="license url https", new="http license leftover only", fail_err="400: leftover license url https after http license leftover-only", plan="http license leftover-only 400s leftover license url https. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (http license leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#info-object", fetch1_ok="Exclusive license https 400 leftover http.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#license-object", fetch2_ok="license.url must be https, leftover http fails closed.")),
    (p(slug="oas-contact-url-https", domain="oas-contact-url-https-vs-leftover-contact-http-url", success=True, name="8468bc", stack="OpenAPI 3.1 url + Go", field="url", old="http contact leftover", new="contact url https", fail_err="400: leftover http contact leftover after contact url https-only", plan="contact url https-only 400s leftover http contact leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (contact url https vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#contact-object", fetch1_ok="contact.url must be https, leftover http fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#info-object", fetch2_ok="Exclusive contact https 400 leftover http."),
     p(slug="leftover-contact-http-url", domain="leftover-contact-http-url-vs-oas-contact-url-https", success=False, name="7bee26", stack="OpenAPI leftover url + Java + TS", field="url", old="contact url https", new="http contact leftover only", fail_err="400: leftover contact url https after http contact leftover-only", plan="http contact leftover-only 400s leftover contact url https. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (http contact leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#info-object", fetch1_ok="Exclusive contact https 400 leftover http.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#contact-object", fetch2_ok="contact.url must be https, leftover http fails closed.")),
    (p(slug="oas-schema-title-nonempty", domain="oas-schema-title-nonempty-vs-leftover-schema-missing-title", success=True, name="d48535", stack="OpenAPI 3.1 title + Go", field="title", old="untitled leftover", new="schema title nonempty", fail_err="400: leftover untitled leftover after schema title nonempty-only", plan="schema title nonempty-only 400s leftover untitled leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (schema title nonempty vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/generic#annotation", fetch1_ok="title must be nonempty, leftover untitled fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive title 400 leftover untitled."),
     p(slug="leftover-schema-missing-title", domain="leftover-schema-missing-title-vs-oas-schema-title-nonempty", success=False, name="8833f8", stack="OpenAPI leftover title + Java + TS", field="title", old="schema title nonempty", new="untitled leftover only", fail_err="400: leftover schema title nonempty after untitled leftover-only", plan="untitled leftover-only 400s leftover schema title nonempty. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (untitled leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive title 400 leftover untitled.", fetch2="https://json-schema.org/understanding-json-schema/reference/generic#annotation", fetch2_ok="title must be nonempty, leftover untitled fails closed.")),
    (p(slug="oas-xml-attr-flag-true", domain="oas-xml-attr-flag-true-vs-leftover-xml-element-only", success=True, name="a3ab91", stack="OpenAPI 3.1 attribute + Go", field="attribute", old="element only leftover", new="xml attribute true", fail_err="415: leftover element only leftover after xml attribute true-only", plan="xml attribute true-only 415s leftover element only leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (xml attribute true vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#xml-object", fetch1_ok="xml.attribute true is not leftover element-only mapping.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive xml attribute 415 leftover element."),
     p(slug="leftover-xml-element-only", domain="leftover-xml-element-only-vs-oas-xml-attr-flag-true", success=False, name="440b6b", stack="OpenAPI leftover attribute + Java + TS", field="attribute", old="xml attribute true", new="element only leftover only", fail_err="415: leftover xml attribute true after element only leftover-only", plan="element only leftover-only 415s leftover xml attribute true. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (element only leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive xml attribute 415 leftover element.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#xml-object", fetch2_ok="xml.attribute true is not leftover element-only mapping.")),
    (p(slug="oas-xml-wrapped-flag-false", domain="oas-xml-wrapped-flag-false-vs-leftover-always-wrap-xml", success=True, name="428d21", stack="OpenAPI 3.1 wrapped + Go", field="wrapped", old="always wrap leftover", new="xml wrapped false", fail_err="415: leftover always wrap leftover after xml wrapped false-only", plan="xml wrapped false-only 415s leftover always wrap leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (xml wrapped false vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#xml-object", fetch1_ok="xml.wrapped false is not leftover always-wrap.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive wrapped false 415 leftover always wrap."),
     p(slug="leftover-always-wrap-xml", domain="leftover-always-wrap-xml-vs-oas-xml-wrapped-flag-false", success=False, name="3f2876", stack="OpenAPI leftover wrapped + Java + TS", field="wrapped", old="xml wrapped false", new="always wrap leftover only", fail_err="415: leftover xml wrapped false after always wrap leftover-only", plan="always wrap leftover-only 415s leftover xml wrapped false. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (always wrap leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive wrapped false 415 leftover always wrap.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#xml-object", fetch2_ok="xml.wrapped false is not leftover always-wrap.")),
    (p(slug="oas-security-api-key-query", domain="oas-security-api-key-query-vs-leftover-api-key-header-forced", success=True, name="9976ce", stack="OpenAPI 3.1 in + Go", field="in", old="header forced leftover", new="apiKey in query", fail_err="401: leftover header forced leftover after apiKey in query-only", plan="apiKey in query-only 401s leftover header forced leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (apiKey in query vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch1_ok="apiKey in query is not leftover header-forced keys.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#security-requirement-object", fetch2_ok="Exclusive query apikey 401 leftover header."),
     p(slug="leftover-api-key-header-forced", domain="leftover-api-key-header-forced-vs-oas-security-api-key-query", success=False, name="5310e5", stack="OpenAPI leftover in + Java + TS", field="in", old="apiKey in query", new="header forced leftover only", fail_err="401: leftover apiKey in query after header forced leftover-only", plan="header forced leftover-only 401s leftover apiKey in query. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (header forced leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#security-requirement-object", fetch1_ok="Exclusive query apikey 401 leftover header.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch2_ok="apiKey in query is not leftover header-forced keys.")),
    (p(slug="oas-oauth2-auth-code-pkce", domain="oas-oauth2-auth-code-pkce-vs-leftover-auth-code-no-pkce", success=True, name="d3f717", stack="OpenAPI 3.1 authorizationCode + Go", field="authorizationCode", old="no pkce leftover", new="auth code PKCE", fail_err="401: leftover no pkce leftover after auth code PKCE-only", plan="auth code PKCE-only 401s leftover no pkce leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (auth code PKCE vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#oauth-flow-object", fetch1_ok="authorizationCode with PKCE is not leftover code without PKCE.", fetch2="https://datatracker.ietf.org/doc/html/rfc7636", fetch2_ok="Exclusive PKCE 401 leftover no pkce."),
     p(slug="leftover-auth-code-no-pkce", domain="leftover-auth-code-no-pkce-vs-oas-oauth2-auth-code-pkce", success=False, name="627592", stack="OpenAPI leftover authorizationCode + Java + TS", field="authorizationCode", old="auth code PKCE", new="no pkce leftover only", fail_err="401: leftover auth code PKCE after no pkce leftover-only", plan="no pkce leftover-only 401s leftover auth code PKCE. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (no pkce leftover leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc7636", fetch1_ok="Exclusive PKCE 401 leftover no pkce.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#oauth-flow-object", fetch2_ok="authorizationCode with PKCE is not leftover code without PKCE.")),
    (p(slug="oas-openid-connect-url-https", domain="oas-openid-connect-url-https-vs-leftover-oidc-discovery-http", success=True, name="c52b13", stack="OpenAPI 3.1 openIdConnectUrl + Go", field="openIdConnectUrl", old="http discovery leftover", new="OIDC url https", fail_err="401: leftover http discovery leftover after OIDC url https-only", plan="OIDC url https-only 401s leftover http discovery leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (OIDC url https vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch1_ok="openIdConnectUrl must be https, leftover http fails closed.", fetch2="https://datatracker.ietf.org/doc/html/rfc8414", fetch2_ok="Exclusive OIDC https 401 leftover http."),
     p(slug="leftover-oidc-discovery-http", domain="leftover-oidc-discovery-http-vs-oas-openid-connect-url-https", success=False, name="6ca346", stack="OpenAPI leftover openIdConnectUrl + Java + TS", field="openIdConnectUrl", old="OIDC url https", new="http discovery leftover only", fail_err="401: leftover OIDC url https after http discovery leftover-only", plan="http discovery leftover-only 401s leftover OIDC url https. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (http discovery leftover leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc8414", fetch1_ok="Exclusive OIDC https 401 leftover http.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch2_ok="openIdConnectUrl must be https, leftover http fails closed.")),
    (p(slug="oas-mutualtls-required-op", domain="oas-mutualtls-required-op-vs-leftover-optional-client-cert", success=True, name="025f7e", stack="OpenAPI 3.1 mutualTLS + Go", field="mutualTLS", old="optional cert leftover", new="mutualTLS required", fail_err="401: leftover optional cert leftover after mutualTLS required-only", plan="mutualTLS required-only 401s leftover optional cert leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (mutualTLS required vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch1_ok="mutualTLS required is not leftover optional client cert.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#security-requirement-object", fetch2_ok="Exclusive mutualTLS 401 leftover optional cert."),
     p(slug="leftover-optional-client-cert", domain="leftover-optional-client-cert-vs-oas-mutualtls-required-op", success=False, name="412dca", stack="OpenAPI leftover mutualTLS + Java + TS", field="mutualTLS", old="mutualTLS required", new="optional cert leftover only", fail_err="401: leftover mutualTLS required after optional cert leftover-only", plan="optional cert leftover-only 401s leftover mutualTLS required. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (optional cert leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#security-requirement-object", fetch1_ok="Exclusive mutualTLS 401 leftover optional cert.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch2_ok="mutualTLS required is not leftover optional client cert.")),
    (p(slug="oas-components-path-items-ref", domain="oas-components-path-items-ref-vs-leftover-inline-path-item", success=True, name="465c80", stack="OpenAPI 3.1 pathItems + Go", field="pathItems", old="inline path leftover", new="components pathItems ref", fail_err="400: leftover inline path leftover after components pathItems ref-only", plan="components pathItems ref-only 400s leftover inline path leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (components pathItems ref vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#components-object", fetch1_ok="components.pathItems reuse, leftover inline-only is not that.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#path-item-object", fetch2_ok="Exclusive pathItems 400 leftover inline."),
     p(slug="leftover-inline-path-item", domain="leftover-inline-path-item-vs-oas-components-path-items-ref", success=False, name="f37c20", stack="OpenAPI leftover pathItems + Java + TS", field="pathItems", old="components pathItems ref", new="inline path leftover only", fail_err="400: leftover components pathItems ref after inline path leftover-only", plan="inline path leftover-only 400s leftover components pathItems ref. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (inline path leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#path-item-object", fetch1_ok="Exclusive pathItems 400 leftover inline.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#components-object", fetch2_ok="components.pathItems reuse, leftover inline-only is not that.")),
    (p(slug="oas-request-body-required-true", domain="oas-request-body-required-true-vs-leftover-optional-json-body", success=True, name="c7f883", stack="OpenAPI 3.1 required + Go", field="required", old="optional body leftover", new="requestBody required true", fail_err="400: leftover optional body leftover after requestBody required true-only", plan="requestBody required true-only 400s leftover optional body leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (requestBody required true vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#request-body-object", fetch1_ok="required true rejects leftover optional JSON bodies.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch2_ok="Exclusive required body 400 leftover optional."),
     p(slug="leftover-optional-json-body", domain="leftover-optional-json-body-vs-oas-request-body-required-true", success=False, name="ae8a2f", stack="OpenAPI leftover required + Java + TS", field="required", old="requestBody required true", new="optional body leftover only", fail_err="400: leftover requestBody required true after optional body leftover-only", plan="optional body leftover-only 400s leftover requestBody required true. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (optional body leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch1_ok="Exclusive required body 400 leftover optional.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#request-body-object", fetch2_ok="required true rejects leftover optional JSON bodies.")),
    (p(slug="oas-encoding-headers-required", domain="oas-encoding-headers-required-vs-leftover-multipart-part-no-hdr", success=True, name="c00177", stack="OpenAPI 3.1 headers + Go", field="headers", old="part no headers leftover", new="encoding headers required", fail_err="415: leftover part no headers leftover after encoding headers required-only", plan="encoding headers required-only 415s leftover part no headers leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (encoding headers required vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#encoding-object", fetch1_ok="encoding.headers are required here, leftover missing fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch2_ok="Exclusive encoding headers 415 leftover none."),
     p(slug="leftover-multipart-part-no-hdr", domain="leftover-multipart-part-no-hdr-vs-oas-encoding-headers-required", success=False, name="ce56ab", stack="OpenAPI leftover headers + Java + TS", field="headers", old="encoding headers required", new="part no headers leftover only", fail_err="415: leftover encoding headers required after part no headers leftover-only", plan="part no headers leftover-only 415s leftover encoding headers required. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (part no headers leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch1_ok="Exclusive encoding headers 415 leftover none.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#encoding-object", fetch2_ok="encoding.headers are required here, leftover missing fails closed.")),
    (p(slug="oas-callback-expression-header", domain="oas-callback-expression-header-vs-leftover-callback-path-only", success=True, name="41f375", stack="OpenAPI 3.1 expression + Go", field="expression", old="path only leftover", new="callback header expr", fail_err="400: leftover path only leftover after callback header expr-only", plan="callback header expr-only 400s leftover path only leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (callback header expr vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#runtime-expressions", fetch1_ok="Callback expressions may use headers, leftover path-only fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#callback-object", fetch2_ok="Exclusive header expr 400 leftover path only."),
     p(slug="leftover-callback-path-only", domain="leftover-callback-path-only-vs-oas-callback-expression-header", success=False, name="b92eab", stack="OpenAPI leftover expression + Java + TS", field="expression", old="callback header expr", new="path only leftover only", fail_err="400: leftover callback header expr after path only leftover-only", plan="path only leftover-only 400s leftover callback header expr. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (path only leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#callback-object", fetch1_ok="Exclusive header expr 400 leftover path only.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#runtime-expressions", fetch2_ok="Callback expressions may use headers, leftover path-only fails closed.")),
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
    print(json.dumps({"round": round_n, "idx": idx, "ids": [e1["id"], e2["id"]], "catalog": "r4342"}))


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
