#!/usr/bin/env python3
"""Eighth unique OpenAPI-drift ACM catalog after r3963 mill."""
from __future__ import annotations

import argparse
import importlib.util
import json
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
published_slugs = _b.published_slugs

priors = [
    "acm-mill-r3620.py", "acm-mill-r3667.py", "acm-mill-r3698.py",
    "acm-mill-r3714.py", "acm-mill-r3787.py", "acm-mill-r3851.py",
    "acm-mill-r3867.py", "acm-mill-r3883.py", "acm-mill-r3899.py",
    "acm-mill-r3915.py", "acm-mill-r3931.py", "acm-mill-r3947.py",
    "acm-mill-r3963.py",
]
BANNED_PRIOR = {p[0]["slug"] for p in _b.PAIRS} | {p[1]["slug"] for p in _b.PAIRS}
for fname in priors:
    sp = importlib.util.spec_from_file_location(fname.replace("-", "_"), HERE / fname)
    mod = importlib.util.module_from_spec(sp)
    assert sp.loader is not None
    sp.loader.exec_module(mod)
    BANNED_PRIOR |= {p[0]["slug"] for p in mod.PAIRS} | {p[1]["slug"] for p in mod.PAIRS}

BANNED_PRIOR |= {
    "oas-lll4-proto-optional", "protobuf-lll4-optional-oas",
    "accept-language-bcp47", "iso639-language",
    "smile-binary-json", "cbor-majortype-vs-smile",
    "422-vs-400-validation", "207-multistatus-batch",
}


def p(**kw):
    return plant(**kw)


PAIRS: list[tuple[dict, dict]] = [
    (p(slug="oas-info-contact-url", domain="oas-contact-url-vs-missing-url", success=True, name="cturl", stack="OpenAPI 3.1 contact.url + Go", field="url", old="missing contact url leftover", new="contact url", fail_err="400: leftover missing contact url after url-only", plan="contact.url-only 400s leftover missing url. Dual-omit url for one release.", residual="portal still missing leftover; drop after portal 5", vs="r3963 oas-info-contact-email (contact url vs missing leftover, not email)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#contact-object", fetch1_ok="contact.url is not leftover missing url.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#info-object", fetch2_ok="Exclusive contact url 400 leftover missing."),
     p(slug="leftover-missing-contact-url", domain="missing-contact-url-vs-oas-contact-url", success=False, name="nocturl", stack="OpenAPI leftover missing contact url + Java + TS", field="url", old="contact url", new="missing contact url leftover only", fail_err="400: leftover contact url after missing-only", plan="Missing-only 400s leftover contact url. Freeze url, spec missing leftover.", residual="handoff: keep contact url or force missing leftover", vs="r3963 leftover-missing-contact (missing url leftover, not missing contact)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#info-object", fetch1_ok="Missing contact url is not contact.url.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#contact-object", fetch2_ok="Exclusive missing contact url 400 leftover url.")),
    (p(slug="oas-info-contact-name", domain="oas-contact-name-vs-anonymous", success=True, name="ctname", stack="OpenAPI 3.1 contact.name + Go", field="name", old="anonymous contact leftover", new="contact name", fail_err="400: leftover anonymous after name-only", plan="contact.name-only 400s leftover anonymous. Dual-omit name for one release.", residual="portal still anonymous leftover; drop after portal 4", vs="r3963 oas-info-contact-email (contact name vs anonymous leftover, not email)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#contact-object", fetch1_ok="contact.name is not leftover anonymous contact.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#info-object", fetch2_ok="Exclusive contact name 400 leftover anonymous."),
     p(slug="leftover-anonymous-contact", domain="anonymous-vs-oas-contact-name", success=False, name="anonct", stack="OpenAPI leftover anonymous contact + Java + TS", field="name", old="contact name", new="anonymous contact leftover only", fail_err="400: leftover contact name after anonymous-only", plan="Anonymous-only 400s leftover contact name. Freeze name, spec anonymous leftover.", residual="handoff: keep contact name or force anonymous leftover", vs="r3963 leftover-missing-contact (anonymous leftover, not missing contact)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#info-object", fetch1_ok="Anonymous contact is not contact.name.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#contact-object", fetch2_ok="Exclusive anonymous 400 leftover name.")),
    (p(slug="oas-externaldocs-description", domain="oas-extdocs-desc-vs-url-only-docs", success=True, name="extdesc", stack="OpenAPI 3.1 externalDocs.description + Go", field="description", old="url only docs leftover", new="externalDocs description", fail_err="400: leftover url-only docs after description-only", plan="externalDocs.description-only 400s leftover url-only. Dual-omit description for one release.", residual="portal still url-only leftover; drop after portal 6", vs="r3883 oas-tag-externaldocs (externalDocs description vs url-only leftover, not tag docs)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#external-documentation-object", fetch1_ok="externalDocs.description documents the URL, leftover url-only fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#info-object", fetch2_ok="Exclusive externalDocs description 400 leftover url-only."),
     p(slug="leftover-url-only-docs", domain="url-only-docs-vs-oas-extdocs-desc", success=False, name="urldocs", stack="OpenAPI leftover url-only docs + Java + TS", field="url", old="externalDocs description", new="url only docs leftover only", fail_err="400: leftover description after url-only", plan="Url-only 400s leftover externalDocs description. Freeze description, spec url leftover.", residual="handoff: keep externalDocs description or force url-only leftover", vs="r3883 leftover-untagged-ops (url-only leftover, not untagged)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#info-object", fetch1_ok="URL-only docs are not described.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#external-documentation-object", fetch2_ok="Exclusive url-only docs 400 leftover description.")),
    (p(slug="oas-operation-description", domain="oas-op-desc-vs-summary-only", success=True, name="opdesc", stack="OpenAPI 3.1 operation description + Go", field="description", old="summary only leftover", new="operation description", fail_err="400: leftover summary-only after description-only", plan="Operation-description-only 400s leftover summary-only. Dual-omit description for one release.", residual="portal still summary leftover; drop after portal 5", vs="r3947 oas-operation-summary-req (op description vs summary-only leftover, not required summary)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch1_ok="description is CommonMark; leftover summary-only is not that.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#fixed-fields-8", fetch2_ok="Exclusive operation description 400 leftover summary-only."),
     p(slug="leftover-summary-only", domain="summary-only-vs-oas-op-desc", success=False, name="sumonly", stack="OpenAPI leftover summary-only + Java + TS", field="summary", old="operation description", new="summary only leftover only", fail_err="400: leftover description after summary-only", plan="Summary-only 400s leftover operation description. Freeze description, spec summary leftover.", residual="handoff: keep operation description or force summary leftover", vs="r3947 leftover-missing-summary (summary-only leftover, not missing summary)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#fixed-fields-8", fetch1_ok="Summary-only is not operation.description.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch2_ok="Exclusive summary-only 400 leftover description.")),
    (p(slug="oas-schema-description", domain="oas-schema-desc-vs-undocumented-schema", success=True, name="schdesc", stack="OpenAPI 3.1 schema description + Go", field="description", old="undocumented schema leftover", new="schema description", fail_err="400: leftover undocumented schema after description-only", plan="Schema-description-only 400s leftover undocumented. Dual-omit description for one release.", residual="sdk still undocumented leftover; drop after sdk 6", vs="r3963 oas-response-description-req (schema description vs undocumented leftover, not response desc)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Schema description documents the model, leftover undocumented fails closed.", fetch2="https://json-schema.org/understanding-json-schema/reference/generic#annotation", fetch2_ok="Exclusive schema description 400 leftover undocumented."),
     p(slug="leftover-undocumented-schema", domain="undocumented-schema-vs-oas-schema-desc", success=False, name="undsch", stack="OpenAPI leftover undocumented schema + Java + TS", field="schema", old="schema description", new="undocumented schema leftover only", fail_err="400: leftover description after undocumented-only", plan="Undocumented-only 400s leftover schema description. Freeze description, spec undocumented leftover.", residual="handoff: keep schema description or force undocumented leftover", vs="r3963 leftover-missing-resp-desc (undocumented leftover, not missing resp desc)", fetch1="https://json-schema.org/understanding-json-schema/reference/generic#annotation", fetch1_ok="Undocumented schemas are not described.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive undocumented schema 400 leftover description.")),
    (p(slug="oas-format-password", domain="oas-format-password-vs-plain-secret", success=True, name="fmtpw", stack="OpenAPI 3.1 format=password + Go", field="format", old="plain secret leftover", new="format password", fail_err="400: leftover plain secret after format-password-only", plan="format=password-only 400s leftover plain secret. Dual-read plain for one release.", residual="logs still plain leftover; drop after logs 7", vs="r3963 oas-format-byte (format=password vs plain leftover, not byte)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="format=password hints UI masking, leftover plain secrets fail closed.", fetch2="https://json-schema.org/understanding-json-schema/reference/string", fetch2_ok="Exclusive format=password 400 leftover plain secret."),
     p(slug="leftover-plain-secret", domain="plain-secret-vs-oas-format-password", success=False, name="plsec", stack="OpenAPI leftover plain secret + Java + TS", field="type", old="format password", new="plain secret leftover only", fail_err="400: leftover format=password after plain-only", plan="Plain-only 400s leftover format=password. Freeze password, spec plain leftover.", residual="handoff: keep format=password or force plain leftover", vs="r3963 leftover-plain-string (plain secret leftover, not plain string)", fetch1="https://json-schema.org/understanding-json-schema/reference/string", fetch1_ok="Plain secrets are not format=password.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="Exclusive plain secret 400 leftover password.")),
    (p(slug="oas-security-oauth2-authcode", domain="oas-authcode-vs-password-token", success=True, name="acflow", stack="OpenAPI 3.1 oauth2 authorizationCode + Go", field="authorizationCode", old="password token leftover", new="authorizationCode flow", fail_err="401: leftover password token after authorizationCode-only", plan="authorizationCode-only 401s leftover password token. Dual-accept password for one release.", residual="legacy still password leftover; drop after legacy 6", vs="r3963 oas-security-oauth2-clientcreds (authorizationCode vs password leftover, not clientCredentials)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#oauth-flows-object", fetch1_ok="authorizationCode is not leftover password token.", fetch2="https://datatracker.ietf.org/doc/html/rfc6749#section-4.1", fetch2_ok="Exclusive authorizationCode 401 leftover password."),
     p(slug="leftover-password-token", domain="password-token-vs-oas-authcode", success=False, name="pwtok", stack="OpenAPI leftover password token + Java + TS", field="password", old="authorizationCode flow", new="password token leftover only", fail_err="401: leftover authorizationCode after password-only", plan="Password-only 401s leftover authorizationCode. Freeze authorizationCode, spec password leftover.", residual="handoff: keep authorizationCode or force password leftover", vs="r3963 leftover-password-flow (password token leftover, not password flow plant)", fetch1="https://datatracker.ietf.org/doc/html/rfc6749#section-4.3", fetch1_ok="Password tokens are not authorizationCode.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#oauth-flows-object", fetch2_ok="Exclusive password token 401 leftover authorizationCode.")),
    (p(slug="oas-components-responses", domain="oas-components-responses-vs-inline-resp", success=True, name="cresp", stack="OpenAPI 3.1 components.responses + Go", field="responses", old="inline responses leftover", new="components responses", fail_err="400: leftover inline responses after components-only", plan="components.responses-only 400s leftover inline. Dual-read inline for one release.", residual="sdk still inline leftover; drop after sdk 5", vs="r3963 oas-components-headers (components.responses vs inline leftover, not headers)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#components-object", fetch1_ok="components.responses reuse Response Objects.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#response-object", fetch2_ok="Exclusive components.responses 400 leftover inline."),
     p(slug="leftover-inline-responses", domain="inline-resp-vs-oas-components-responses", success=False, name="iresp", stack="OpenAPI leftover inline responses + Java + TS", field="responses", old="components responses", new="inline responses leftover only", fail_err="400: leftover components.responses after inline-only", plan="Inline-only 400s leftover components.responses. Freeze components.responses, spec inline leftover.", residual="handoff: keep components.responses or force inline leftover", vs="r3963 leftover-inline-headers (inline responses leftover, not headers)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#response-object", fetch1_ok="Inline responses are not components.responses.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#components-object", fetch2_ok="Exclusive inline responses 400 leftover components.")),
    (p(slug="oas-components-parameters", domain="oas-components-params-vs-inline-params", success=True, name="cparm", stack="OpenAPI 3.1 components.parameters + Go", field="parameters", old="inline params leftover", new="components parameters", fail_err="400: leftover inline params after components-only", plan="components.parameters-only 400s leftover inline. Dual-read inline for one release.", residual="gateway still inline leftover; drop after gateway 6", vs="r3963 oas-path-param-required (components.parameters vs inline leftover, not required path)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#components-object", fetch1_ok="components.parameters reuse Parameter Objects.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="Exclusive components.parameters 400 leftover inline."),
     p(slug="leftover-inline-params", domain="inline-params-vs-oas-components-params", success=False, name="iparm", stack="OpenAPI leftover inline params + Java + TS", field="parameters", old="components parameters", new="inline params leftover only", fail_err="400: leftover components.parameters after inline-only", plan="Inline-only 400s leftover components.parameters. Freeze components.parameters, spec inline leftover.", residual="handoff: keep components.parameters or force inline leftover", vs="r3963 leftover-optional-path (inline leftover, not optional path)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="Inline params are not components.parameters.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#components-object", fetch2_ok="Exclusive inline params 400 leftover components.")),
    (p(slug="oas-components-requestbodies", domain="oas-components-bodies-vs-inline-bodies", success=True, name="cbody", stack="OpenAPI 3.1 components.requestBodies + Go", field="requestBodies", old="inline bodies leftover", new="components requestBodies", fail_err="400: leftover inline bodies after components-only", plan="components.requestBodies-only 400s leftover inline. Dual-read inline for one release.", residual="sdk still inline leftover; drop after sdk 5", vs="r3963 oas-requestbody-json-required (components.requestBodies vs inline leftover, not json required)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#components-object", fetch1_ok="components.requestBodies reuse Request Body Objects.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#request-body-object", fetch2_ok="Exclusive components.requestBodies 400 leftover inline."),
     p(slug="leftover-inline-bodies", domain="inline-bodies-vs-oas-components-bodies", success=False, name="ibody", stack="OpenAPI leftover inline bodies + Java + TS", field="requestBody", old="components requestBodies", new="inline bodies leftover only", fail_err="400: leftover components.requestBodies after inline-only", plan="Inline-only 400s leftover components.requestBodies. Freeze components.requestBodies, spec inline leftover.", residual="handoff: keep components.requestBodies or force inline leftover", vs="r3963 leftover-empty-json (inline leftover, not empty json)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#request-body-object", fetch1_ok="Inline bodies are not components.requestBodies.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#components-object", fetch2_ok="Exclusive inline bodies 400 leftover components.")),
    (p(slug="oas-components-securityschemes", domain="oas-components-sec-vs-inline-sec", success=True, name="csec", stack="OpenAPI 3.1 components.securitySchemes + Go", field="securitySchemes", old="inline security leftover", new="components securitySchemes", fail_err="401: leftover inline security after components-only", plan="components.securitySchemes-only 401s leftover inline. Dual-read inline for one release.", residual="gateway still inline leftover; drop after gateway 7", vs="r3947 oas-security-http-bearer (components.securitySchemes vs inline leftover, not bearer)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#components-object", fetch1_ok="components.securitySchemes reuse Security Scheme Objects.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch2_ok="Exclusive components.securitySchemes 401 leftover inline."),
     p(slug="leftover-inline-security", domain="inline-sec-vs-oas-components-sec", success=False, name="isec", stack="OpenAPI leftover inline security + Java + TS", field="security", old="components securitySchemes", new="inline security leftover only", fail_err="401: leftover components.securitySchemes after inline-only", plan="Inline-only 401s leftover components.securitySchemes. Freeze components.securitySchemes, spec inline leftover.", residual="handoff: keep components.securitySchemes or force inline leftover", vs="r3947 leftover-http-basic (inline leftover, not basic)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch1_ok="Inline security is not components.securitySchemes.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#components-object", fetch2_ok="Exclusive inline security 401 leftover components.")),
    (p(slug="oas-server-var-description", domain="oas-srv-var-desc-vs-undocumented-var", success=True, name="svdesc", stack="OpenAPI 3.1 server variable description + Go", field="description", old="undocumented var leftover", new="server variable description", fail_err="400: leftover undocumented var after description-only", plan="Server-variable-description-only 400s leftover undocumented. Dual-omit description for one release.", residual="mesh still undocumented leftover; drop after mesh 5", vs="r3899 oas-server-var-default (variable description vs undocumented leftover, not default)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#server-variable-object", fetch1_ok="Server variable description documents the substitution.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#server-object", fetch2_ok="Exclusive variable description 400 leftover undocumented."),
     p(slug="leftover-undocumented-var", domain="undocumented-var-vs-oas-srv-var-desc", success=False, name="undvar", stack="OpenAPI leftover undocumented var + Java + TS", field="variables", old="server variable description", new="undocumented var leftover only", fail_err="400: leftover description after undocumented-only", plan="Undocumented-only 400s leftover variable description. Freeze description, spec undocumented leftover.", residual="handoff: keep variable description or force undocumented leftover", vs="r3899 leftover-missing-srv-default (undocumented leftover, not missing default)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#server-object", fetch1_ok="Undocumented vars are not described.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#server-variable-object", fetch2_ok="Exclusive undocumented var 400 leftover description.")),
    (p(slug="oas-link-description", domain="oas-link-desc-vs-undocumented-link", success=True, name="lnkdesc", stack="OpenAPI 3.1 link description + Go", field="description", old="undocumented link leftover", new="link description", fail_err="400: leftover undocumented link after description-only", plan="Link-description-only 400s leftover undocumented. Dual-omit description for one release.", residual="sdk still undocumented leftover; drop after sdk 4", vs="r3867 oas-links-opref (link description vs undocumented leftover, not operationRef)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#link-object", fetch1_ok="Link description documents the follow-on operation.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#response-object", fetch2_ok="Exclusive link description 400 leftover undocumented."),
     p(slug="leftover-undocumented-link", domain="undocumented-link-vs-oas-link-desc", success=False, name="undlnk", stack="OpenAPI leftover undocumented link + Java + TS", field="links", old="link description", new="undocumented link leftover only", fail_err="400: leftover description after undocumented-only", plan="Undocumented-only 400s leftover link description. Freeze description, spec undocumented leftover.", residual="handoff: keep link description or force undocumented leftover", vs="r3867 leftover-links-opid (undocumented leftover, not operationId)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#response-object", fetch1_ok="Undocumented links are not described.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#link-object", fetch2_ok="Exclusive undocumented link 400 leftover description.")),
    (p(slug="oas-callback-description", domain="oas-callback-desc-vs-undocumented-cb", success=True, name="cbdesc", stack="OpenAPI 3.1 callback description + Go", field="description", old="undocumented callback leftover", new="callback description", fail_err="400: leftover undocumented callback after description-only", plan="Callback-description-only 400s leftover undocumented. Dual-omit description for one release.", residual="bus still undocumented leftover; drop after bus 5", vs="r3947 oas-callback-pathitem (callback description vs undocumented leftover, not Path Item)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#callback-object", fetch1_ok="Callback Path Items should describe the event.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#path-item-object", fetch2_ok="Exclusive callback description 400 leftover undocumented."),
     p(slug="leftover-undocumented-cb", domain="undocumented-cb-vs-oas-callback-desc", success=False, name="undcb", stack="OpenAPI leftover undocumented callback + Java + TS", field="callbacks", old="callback description", new="undocumented callback leftover only", fail_err="400: leftover description after undocumented-only", plan="Undocumented-only 400s leftover callback description. Freeze description, spec undocumented leftover.", residual="handoff: keep callback description or force undocumented leftover", vs="r3947 leftover-notify-post (undocumented leftover, not notify post)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#path-item-object", fetch1_ok="Undocumented callbacks are not described.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#callback-object", fetch2_ok="Exclusive undocumented callback 400 leftover description.")),
    (p(slug="oas-media-example", domain="oas-media-example-vs-undocumented-media", success=True, name="medex", stack="OpenAPI 3.1 media example + Go", field="example", old="undocumented media leftover", new="media example", fail_err="400: leftover undocumented media after example-only", plan="Media-example-only 400s leftover undocumented. Dual-omit example for one release.", residual="docs still undocumented leftover; drop after docs 6", vs="r3947 oas-example-external-value (media example vs undocumented leftover, not externalValue)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch1_ok="Media Type example documents the payload, leftover undocumented fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#example-object", fetch2_ok="Exclusive media example 400 leftover undocumented."),
     p(slug="leftover-undocumented-media", domain="undocumented-media-vs-oas-media-example", success=False, name="undmed", stack="OpenAPI leftover undocumented media + Java + TS", field="content", old="media example", new="undocumented media leftover only", fail_err="400: leftover example after undocumented-only", plan="Undocumented-only 400s leftover media example. Freeze example, spec undocumented leftover.", residual="handoff: keep media example or force undocumented leftover", vs="r3947 leftover-inline-example (undocumented leftover, not inline example)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#example-object", fetch1_ok="Undocumented media is not example.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch2_ok="Exclusive undocumented media 400 leftover example.")),
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
    print(json.dumps({"round": round_n, "idx": idx, "ids": [e1["id"], e2["id"]], "catalog": "r3978"}))


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
