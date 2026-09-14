#!/usr/bin/env python3
"""Fourteenth unique OpenAPI-drift ACM catalog after r4198 mill. Fast slug load."""
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
    (p(slug="oas-schema-format-int32-strict", domain="oas-schema-format-int32-strict-vs-leftover-js-number-int", success=True, name="fmt32s", stack="OpenAPI 3.1 format=int32 strict + Go", field="format", old="js number leftover", new="format int32", fail_err="400: leftover js number leftover after format int32-only", plan="format int32-only 400s leftover js number leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r3947 leftover-unbounded-int (int32 vs js number leftover, not unbounded mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="format=int32 is 32-bit, leftover JS numbers fail closed.", fetch2="https://json-schema.org/understanding-json-schema/reference/numeric", fetch2_ok="Exclusive int32 400 leftover js number."),
     p(slug="leftover-js-number-int", domain="leftover-js-number-int-vs-oas-schema-format-int32-strict", success=False, name="jsnum", stack="OpenAPI leftover js number int + Java + TS", field="format", old="format int32", new="js number leftover only", fail_err="400: leftover format int32 after js number leftover-only", plan="js number leftover-only 400s leftover format int32. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r3947 oas-format-int32 (js leftover, not int32 mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/numeric", fetch1_ok="Exclusive int32 400 leftover js number.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="format=int32 is 32-bit, leftover JS numbers fail closed.")),
    (p(slug="oas-parameter-content-form", domain="oas-parameter-content-form-vs-leftover-schema-form-param", success=True, name="pform", stack="OpenAPI 3.1 parameter content form + Go", field="content", old="schema form leftover", new="parameter content form", fail_err="400: leftover schema form leftover after parameter content form-only", plan="parameter content form-only 400s leftover schema form leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4038 leftover-schema-only-param (form content vs schema leftover, not json content mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="parameter.content form is not leftover schema-only form params.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch2_ok="Exclusive param form content 400 leftover schema."),
     p(slug="leftover-schema-form-param", domain="leftover-schema-form-param-vs-oas-parameter-content-form", success=False, name="schform", stack="OpenAPI leftover schema form param + Java + TS", field="content", old="parameter content form", new="schema form leftover only", fail_err="400: leftover parameter content form after schema form leftover-only", plan="schema form leftover-only 400s leftover parameter content form. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4038 oas-parameter-content-json (schema leftover, not json mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch1_ok="Exclusive param form content 400 leftover schema.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="parameter.content form is not leftover schema-only form params.")),
    (p(slug="oas-response-204-empty", domain="oas-response-204-empty-vs-leftover-204-with-body", success=True, name="r204", stack="OpenAPI 3.1 204 empty + Go", field="content", old="204 body leftover", new="204 empty", fail_err="400: leftover 204 body leftover after 204 empty-only", plan="204 empty-only 400s leftover 204 body leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r3561 status-204-no-body (204 empty vs body leftover, not mill reuse)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#response-object", fetch1_ok="204 MUST NOT include a body, leftover bodies fail closed.", fetch2="https://datatracker.ietf.org/doc/html/rfc9110#name-204-no-content", fetch2_ok="Exclusive 204 empty 400 leftover body."),
     p(slug="leftover-204-with-body", domain="leftover-204-with-body-vs-oas-response-204-empty", success=False, name="body204", stack="OpenAPI leftover 204 with body + Java + TS", field="content", old="204 empty", new="204 body leftover only", fail_err="400: leftover 204 empty after 204 body leftover-only", plan="204 body leftover-only 400s leftover 204 empty. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r3561 status-204-no-body (body leftover, not mill reuse)", fetch1="https://datatracker.ietf.org/doc/html/rfc9110#name-204-no-content", fetch1_ok="Exclusive 204 empty 400 leftover body.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#response-object", fetch2_ok="204 MUST NOT include a body, leftover bodies fail closed.")),
    (p(slug="oas-security-oauth2-authorization-url", domain="oas-security-oauth2-authorization-url-vs-leftover-tokenurl-only-flow", success=True, name="authu", stack="OpenAPI 3.1 oauth2 authorizationUrl + Go", field="authorizationUrl", old="tokenurl only leftover", new="authorizationUrl required", fail_err="401: leftover tokenurl only leftover after authorizationUrl required-only", plan="authorizationUrl required-only 401s leftover tokenurl only leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4102 leftover-authurl-only (authorizationUrl vs token-only leftover, not token mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#oauth-flow-object", fetch1_ok="authorizationUrl is required for code flow, leftover token-only fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#oauth-flows-object", fetch2_ok="Exclusive authorizationUrl 401 leftover token-only."),
     p(slug="leftover-tokenurl-only-flow", domain="leftover-tokenurl-only-flow-vs-oas-security-oauth2-authorization-url", success=False, name="tokonly", stack="OpenAPI leftover tokenurl only flow + Java + TS", field="authorizationUrl", old="authorizationUrl required", new="tokenurl only leftover only", fail_err="401: leftover authorizationUrl required after tokenurl only leftover-only", plan="tokenurl only leftover-only 401s leftover authorizationUrl required. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4102 oas-security-oauth2-tokenurl (token-only leftover, not token mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#oauth-flows-object", fetch1_ok="Exclusive authorizationUrl 401 leftover token-only.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#oauth-flow-object", fetch2_ok="authorizationUrl is required for code flow, leftover token-only fails closed.")),
    (p(slug="oas-schema-format-binary", domain="oas-schema-format-binary-vs-leftover-base64-binary", success=True, name="fmtbin", stack="OpenAPI 3.1 format=binary + Go", field="format", old="base64 binary leftover", new="format binary", fail_err="415: leftover base64 binary leftover after format binary-only", plan="format binary-only 415s leftover base64 binary leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4166 leftover-part-octet (binary vs base64 leftover, not octet mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="format=binary is octet stream, leftover base64 fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive binary 415 leftover base64."),
     p(slug="leftover-base64-binary", domain="leftover-base64-binary-vs-oas-schema-format-binary", success=False, name="b64bin", stack="OpenAPI leftover base64 binary + Java + TS", field="format", old="format binary", new="base64 binary leftover only", fail_err="415: leftover format binary after base64 binary leftover-only", plan="base64 binary leftover-only 415s leftover format binary. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4166 oas-encoding-content-type (base64 leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive binary 415 leftover base64.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="format=binary is octet stream, leftover base64 fails closed.")),
    (p(slug="oas-webhook-operation-id", domain="oas-webhook-operation-id-vs-leftover-anonymous-webhook", success=True, name="whkopid", stack="OpenAPI 3.1 webhook operationId + Go", field="operationId", old="anonymous webhook leftover", new="webhook operationId", fail_err="400: leftover anonymous webhook leftover after webhook operationId-only", plan="webhook operationId-only 400s leftover anonymous webhook leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4150 leftover-missing-opid (webhook opid vs anonymous leftover, not missing mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#oasWebhooks", fetch1_ok="Webhook operations need operationId, leftover anonymous fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch2_ok="Exclusive webhook opid 400 leftover anonymous."),
     p(slug="leftover-anonymous-webhook", domain="leftover-anonymous-webhook-vs-oas-webhook-operation-id", success=False, name="whkanon", stack="OpenAPI leftover anonymous webhook + Java + TS", field="operationId", old="webhook operationId", new="anonymous webhook leftover only", fail_err="400: leftover webhook operationId after anonymous webhook leftover-only", plan="anonymous webhook leftover-only 400s leftover webhook operationId. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4150 oas-operation-operationid-required (anonymous leftover, not required mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch1_ok="Exclusive webhook opid 400 leftover anonymous.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#oasWebhooks", fetch2_ok="Webhook operations need operationId, leftover anonymous fails closed.")),
    (p(slug="oas-info-license-required", domain="oas-info-license-required-vs-leftover-unlicensed-info", success=True, name="licreq", stack="OpenAPI 3.1 license required + Go", field="license", old="unlicensed leftover", new="license required", fail_err="400: leftover unlicensed leftover after license required-only", plan="license required-only 400s leftover unlicensed leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4054 leftover-missing-license (required license vs unlicensed leftover, not missing mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#info-object", fetch1_ok="info.license documents terms, leftover unlicensed fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#license-object", fetch2_ok="Exclusive license 400 leftover unlicensed."),
     p(slug="leftover-unlicensed-info", domain="leftover-unlicensed-info-vs-oas-info-license-required", success=False, name="nolic2", stack="OpenAPI leftover unlicensed info + Java + TS", field="license", old="license required", new="unlicensed leftover only", fail_err="400: leftover license required after unlicensed leftover-only", plan="unlicensed leftover-only 400s leftover license required. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4054 oas-info-license-name (unlicensed leftover, not name mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#license-object", fetch1_ok="Exclusive license 400 leftover unlicensed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#info-object", fetch2_ok="info.license documents terms, leftover unlicensed fails closed.")),
    (p(slug="oas-parameter-style-form-query", domain="oas-parameter-style-form-query-vs-leftover-query-csv-join", success=True, name="qform2", stack="OpenAPI 3.1 query style=form + Go", field="style", old="csv join leftover", new="query form style", fail_err="400: leftover csv join leftover after query form style-only", plan="query form style-only 400s leftover csv join leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4086 leftover-csv-query (form vs csv leftover, not pipe mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch1_ok="Query style=form is the default, leftover csv joins are not that.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="Exclusive query form 400 leftover csv."),
     p(slug="leftover-query-csv-join", domain="leftover-query-csv-join-vs-oas-parameter-style-form-query", success=False, name="qcsv2", stack="OpenAPI leftover query csv join + Java + TS", field="style", old="query form style", new="csv join leftover only", fail_err="400: leftover query form style after csv join leftover-only", plan="csv join leftover-only 400s leftover query form style. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4086 oas-parameter-style-pipe-delimited (csv leftover, not pipe mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="Exclusive query form 400 leftover csv.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch2_ok="Query style=form is the default, leftover csv joins are not that.")),
    (p(slug="oas-schema-format-byte-url", domain="oas-schema-format-byte-url-vs-leftover-std-b64-url", success=True, name="b64url", stack="OpenAPI 3.1 byte url encoding + Go", field="format", old="std b64 leftover", new="byte url encoding", fail_err="400: leftover std b64 leftover after byte url encoding-only", plan="byte url encoding-only 400s leftover std b64 leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r3915 leftover-std-b64 (byte url vs std leftover, not mill reuse)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="URL-safe base64 is not leftover standard base64.", fetch2="https://json-schema.org/understanding-json-schema/reference/non_json_data#contentencoding", fetch2_ok="Exclusive byte url 400 leftover std b64."),
     p(slug="leftover-std-b64-url", domain="leftover-std-b64-url-vs-oas-schema-format-byte-url", success=False, name="stdb64", stack="OpenAPI leftover std b64 url + Java + TS", field="format", old="byte url encoding", new="std b64 leftover only", fail_err="400: leftover byte url encoding after std b64 leftover-only", plan="std b64 leftover-only 400s leftover byte url encoding. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r3915 oas-content-b64url (std leftover, not mill reuse)", fetch1="https://json-schema.org/understanding-json-schema/reference/non_json_data#contentencoding", fetch1_ok="Exclusive byte url 400 leftover std b64.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="URL-safe base64 is not leftover standard base64.")),
    (p(slug="oas-components-examples-reuse", domain="oas-components-examples-reuse-vs-leftover-media-inline-example", success=True, name="cex2", stack="OpenAPI 3.1 components.examples reuse + Go", field="examples", old="media inline leftover", new="components examples reuse", fail_err="400: leftover media inline leftover after components examples reuse-only", plan="components examples reuse-only 400s leftover media inline leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r3963 leftover-inline-only (components.examples vs media leftover, not mill reuse)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#components-object", fetch1_ok="components.examples reuse Example Objects.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#example-object", fetch2_ok="Exclusive components.examples 400 leftover inline."),
     p(slug="leftover-media-inline-example", domain="leftover-media-inline-example-vs-oas-components-examples-reuse", success=False, name="minlex", stack="OpenAPI leftover media inline example + Java + TS", field="examples", old="components examples reuse", new="media inline leftover only", fail_err="400: leftover components examples reuse after media inline leftover-only", plan="media inline leftover-only 400s leftover components examples reuse. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r3963 oas-components-examples (media leftover, not mill reuse)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#example-object", fetch1_ok="Exclusive components.examples 400 leftover inline.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#components-object", fetch2_ok="components.examples reuse Example Objects.")),
    (p(slug="oas-operation-servers-item", domain="oas-operation-servers-item-vs-leftover-root-only-op-server", success=True, name="opsrv2", stack="OpenAPI 3.1 operation servers + Go", field="servers", old="root only op leftover", new="operation servers", fail_err="400: leftover root only op leftover after operation servers-only", plan="operation servers-only 400s leftover root only op leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4134 leftover-op-server-only (op servers vs root leftover, not path mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch1_ok="operation.servers override path/root, leftover root-only is not that.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#server-object", fetch2_ok="Exclusive op servers 400 leftover root."),
     p(slug="leftover-root-only-op-server", domain="leftover-root-only-op-server-vs-oas-operation-servers-item", success=False, name="rooto", stack="OpenAPI leftover root only op server + Java + TS", field="servers", old="operation servers", new="root only op leftover only", fail_err="400: leftover operation servers after root only op leftover-only", plan="root only op leftover-only 400s leftover operation servers. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4134 oas-path-item-servers (root leftover, not path mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#server-object", fetch1_ok="Exclusive op servers 400 leftover root.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch2_ok="operation.servers override path/root, leftover root-only is not that.")),
    (p(slug="oas-xml-prefix-required", domain="oas-xml-prefix-required-vs-leftover-xml-no-prefix", success=True, name="xmlpre", stack="OpenAPI 3.1 xml prefix required + Go", field="prefix", old="no xml prefix leftover", new="xml prefix required", fail_err="415: leftover no xml prefix leftover after xml prefix required-only", plan="xml prefix required-only 415s leftover no xml prefix leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4023 leftover-unprefixed-ns (required prefix vs none leftover, not ns mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#xml-object", fetch1_ok="xml.prefix is required with namespace, leftover missing fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive xml prefix 415 leftover none."),
     p(slug="leftover-xml-no-prefix", domain="leftover-xml-no-prefix-vs-oas-xml-prefix-required", success=False, name="nopre", stack="OpenAPI leftover xml no prefix + Java + TS", field="prefix", old="xml prefix required", new="no xml prefix leftover only", fail_err="415: leftover xml prefix required after no xml prefix leftover-only", plan="no xml prefix leftover-only 415s leftover xml prefix required. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4023 oas-xml-namespace-prefix (none leftover, not ns mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive xml prefix 415 leftover none.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#xml-object", fetch2_ok="xml.prefix is required with namespace, leftover missing fails closed.")),
    (p(slug="oas-link-description-req", domain="oas-link-description-req-vs-leftover-link-no-description", success=True, name="lnkdesc", stack="OpenAPI 3.1 link description + Go", field="description", old="undocumented link leftover", new="link description", fail_err="400: leftover undocumented link leftover after link description-only", plan="link description-only 400s leftover undocumented link leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4007 leftover-no-links (link desc vs undocumented leftover, not missing links)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#link-object", fetch1_ok="Link description documents the follow-on, leftover undocumented fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#response-object", fetch2_ok="Exclusive link description 400 leftover undocumented."),
     p(slug="leftover-link-no-description", domain="leftover-link-no-description-vs-oas-link-description-req", success=False, name="nolnkd", stack="OpenAPI leftover undocumented link + Java + TS", field="description", old="link description", new="undocumented link leftover only", fail_err="400: leftover link description after undocumented link leftover-only", plan="undocumented link leftover-only 400s leftover link description. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4007 oas-response-links-required (undocumented leftover, not required links)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#response-object", fetch1_ok="Exclusive link description 400 leftover undocumented.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#link-object", fetch2_ok="Link description documents the follow-on, leftover undocumented fails closed.")),
    (p(slug="oas-schema-format-hostname-ascii", domain="oas-schema-format-hostname-ascii-vs-leftover-ip-as-hostname", success=True, name="hnasc", stack="OpenAPI 3.1 format=hostname ascii + Go", field="format", old="ip as hostname leftover", new="ascii hostname", fail_err="400: leftover ip as hostname leftover after ascii hostname-only", plan="ascii hostname-only 400s leftover ip as hostname leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4007 leftover-raw-idn-host (ascii hostname vs ip leftover, not idn mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/string#hostname", fetch1_ok="format=hostname is not leftover IP literals.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="Exclusive hostname 400 leftover ip."),
     p(slug="leftover-ip-as-hostname", domain="leftover-ip-as-hostname-vs-oas-schema-format-hostname-ascii", success=False, name="iphost", stack="OpenAPI leftover ip as hostname + Java + TS", field="format", old="ascii hostname", new="ip as hostname leftover only", fail_err="400: leftover ascii hostname after ip as hostname leftover-only", plan="ip as hostname leftover-only 400s leftover ascii hostname. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4007 oas-format-hostname-puny (ip leftover, not puny mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="Exclusive hostname 400 leftover ip.", fetch2="https://json-schema.org/understanding-json-schema/reference/string#hostname", fetch2_ok="format=hostname is not leftover IP literals.")),
    (p(slug="oas-security-mutualtls-scheme", domain="oas-security-mutualtls-scheme-vs-leftover-header-client-cert", success=True, name="mtls2", stack="OpenAPI 3.1 mutualTLS scheme + Go", field="type", old="client cert header leftover", new="mutualTLS scheme", fail_err="401: leftover client cert header leftover after mutualTLS scheme-only", plan="mutualTLS scheme-only 401s leftover client cert header leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r3899 leftover-client-cert-header (mutualTLS vs cert header leftover, not mill reuse)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch1_ok="mutualTLS is not leftover x-client-cert headers.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#security-requirement-object", fetch2_ok="Exclusive mutualTLS 401 leftover cert header."),
     p(slug="leftover-header-client-cert", domain="leftover-header-client-cert-vs-oas-security-mutualtls-scheme", success=False, name="certhdr", stack="OpenAPI leftover header client cert + Java + TS", field="type", old="mutualTLS scheme", new="client cert header leftover only", fail_err="401: leftover mutualTLS scheme after client cert header leftover-only", plan="client cert header leftover-only 401s leftover mutualTLS scheme. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r3899 oas-mutualtls-scheme (header leftover, not mill reuse)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#security-requirement-object", fetch1_ok="Exclusive mutualTLS 401 leftover cert header.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch2_ok="mutualTLS is not leftover x-client-cert headers.")),
    (p(slug="oas-encoding-style-pipe", domain="oas-encoding-style-pipe-vs-leftover-encoding-csv", success=True, name="encpipe", stack="OpenAPI 3.1 encoding pipeDelimited + Go", field="style", old="encoding csv leftover", new="encoding pipeDelimited", fail_err="415: leftover encoding csv leftover after encoding pipeDelimited-only", plan="encoding pipeDelimited-only 415s leftover encoding csv leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4086 leftover-csv-query (encoding pipe vs csv leftover, not query mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#encoding-object", fetch1_ok="encoding.style pipeDelimited is not leftover csv parts.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch2_ok="Exclusive encoding pipe 415 leftover csv."),
     p(slug="leftover-encoding-csv", domain="leftover-encoding-csv-vs-oas-encoding-style-pipe", success=False, name="enccsv", stack="OpenAPI leftover encoding csv + Java + TS", field="style", old="encoding pipeDelimited", new="encoding csv leftover only", fail_err="415: leftover encoding pipeDelimited after encoding csv leftover-only", plan="encoding csv leftover-only 415s leftover encoding pipeDelimited. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4086 oas-parameter-style-pipe-delimited (csv leftover, not query mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch1_ok="Exclusive encoding pipe 415 leftover csv.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#encoding-object", fetch2_ok="encoding.style pipeDelimited is not leftover csv parts.")),
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
    print(json.dumps({"round": round_n, "idx": idx, "ids": [e1["id"], e2["id"]], "catalog": "r4214"}))


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
