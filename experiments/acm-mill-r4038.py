#!/usr/bin/env python3
"""Third unique OpenAPI-drift ACM catalog after r4023 mill. Fast slug load."""
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
    (p(slug="oas-json-schema-defs", domain="oas-defs-vs-definitions", success=True, name="jsdefs", stack="OpenAPI 3.1 $defs + Go", field="$defs", old="definitions leftover", new="schema dollardefs", fail_err="400: leftover definitions after $defs-only", plan="$defs-only 400s leftover definitions. Dual-read definitions for one release.", residual="codegen still definitions leftover; drop after codegen 6", vs="r3561 leftover draft-04 definitions ($defs vs definitions leftover, not dialect uri)", fetch1="https://json-schema.org/understanding-json-schema/structuring#defs", fetch1_ok="$defs replaces leftover draft-04 definitions.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive $defs 400 leftover definitions."),
     p(slug="leftover-definitions-draft4", domain="definitions-vs-oas-defs", success=False, name="d4defs", stack="OpenAPI leftover draft-04 definitions + Java + TS", field="definitions", old="schema dollardefs", new="definitions leftover only", fail_err="400: leftover $defs after definitions-only", plan="definitions-only 400s leftover $defs. Freeze $defs, spec definitions leftover.", residual="handoff: keep $defs or force definitions leftover", vs="r3561 json-schema-dialect-uri (definitions leftover, not dialect mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="definitions is not $defs.", fetch2="https://json-schema.org/understanding-json-schema/structuring#defs", fetch2_ok="Exclusive definitions 400 leftover $defs.")),
    (p(slug="oas-operation-security-override", domain="oas-op-security-vs-global-only", success=True, name="opsec", stack="OpenAPI 3.1 operation.security + Go", field="security", old="global security leftover", new="operation security override", fail_err="401: leftover global security after op-security-only", plan="operation.security-only 401s leftover global. Dual-apply global for one release.", residual="gateway still global leftover; drop after gateway 5", vs="r4023 leftover-mtls-required (op security vs global leftover, not mtls mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch1_ok="operation.security overrides root security, leftover global-only is not that.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#security-requirement-object", fetch2_ok="Exclusive op security 401 leftover global."),
     p(slug="leftover-global-security-only", domain="global-only-vs-oas-op-security", success=False, name="globsec", stack="OpenAPI leftover global security + Java + TS", field="security", old="operation security override", new="global security leftover only", fail_err="401: leftover operation.security after global-only", plan="Global-only 401s leftover operation.security. Freeze override, spec global leftover.", residual="handoff: keep operation.security or force global leftover", vs="r4023 oas-security-mutualtls-optional (global leftover, not optional mtls)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#security-requirement-object", fetch1_ok="Root-only security is not operation.security.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch2_ok="Exclusive global security 401 leftover override.")),
    (p(slug="oas-parameter-content-json", domain="oas-param-content-vs-schema-only", success=True, name="pcnt", stack="OpenAPI 3.1 parameter content + Go", field="content", old="schema only param leftover", new="parameter content json", fail_err="400: leftover schema-only param after content-only", plan="parameter.content-only 400s leftover schema. Dual-read schema for one release.", residual="gateway still schema leftover; drop after gateway 6", vs="r3978 leftover-inline-params (param content vs schema leftover, not components.parameters)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="content and schema are mutually exclusive; leftover schema-only is not content.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch2_ok="Exclusive parameter content 400 leftover schema-only."),
     p(slug="leftover-schema-only-param", domain="schema-only-vs-oas-param-content", success=False, name="schpar", stack="OpenAPI leftover schema-only param + Java + TS", field="schema", old="parameter content json", new="schema only param leftover only", fail_err="400: leftover parameter.content after schema-only", plan="Schema-only 400s leftover parameter.content. Freeze content, spec schema leftover.", residual="handoff: keep parameter.content or force schema leftover", vs="r3978 oas-components-parameters (schema leftover, not components mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch1_ok="schema-only params are not content.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="Exclusive schema-only param 400 leftover content.")),
    (p(slug="oas-path-item-description", domain="oas-path-desc-vs-op-desc-only", success=True, name="pidesc", stack="OpenAPI 3.1 Path Item description + Go", field="description", old="op desc only leftover", new="path item description", fail_err="400: leftover op-desc-only after path-desc-only", plan="Path-Item-description-only 400s leftover op-desc. Dual-omit path desc for one release.", residual="portal still op-desc leftover; drop after portal 5", vs="r3978 leftover-summary-only (path desc vs op-desc leftover, not op description mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#path-item-object", fetch1_ok="Path Item description documents the path, leftover op-only desc is not that.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#fixed-fields-7", fetch2_ok="Exclusive path description 400 leftover op-desc."),
     p(slug="leftover-op-desc-only", domain="op-desc-only-vs-oas-path-desc", success=False, name="opdonly", stack="OpenAPI leftover op-desc-only + Java + TS", field="description", old="path item description", new="op desc only leftover only", fail_err="400: leftover path description after op-desc-only", plan="Op-desc-only 400s leftover path description. Freeze path desc, spec op leftover.", residual="handoff: keep path description or force op-desc leftover", vs="r3978 oas-operation-description (op-desc leftover, not op description mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#fixed-fields-7", fetch1_ok="Op-only descriptions are not Path Item description.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#path-item-object", fetch2_ok="Exclusive op-desc-only 400 leftover path desc.")),
    (p(slug="oas-requestbody-required-post", domain="oas-required-body-vs-optional-body", success=True, name="rbreq", stack="OpenAPI 3.1 requestBody required POST + Go", field="required", old="optional body leftover", new="requestBody required", fail_err="400: leftover optional body after required-only", plan="requestBody-required-only 400s leftover optional. Dual-accept empty for one release.", residual="sdk still optional leftover; drop after sdk 5", vs="wrap requestbody-required-put (POST required vs optional leftover, not PUT cartesian)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#request-body-object", fetch1_ok="required true on POST bodies is not leftover optional bodies.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch2_ok="Exclusive required POST body 400 leftover optional."),
     p(slug="leftover-optional-body", domain="optional-body-vs-oas-required-body", success=False, name="optbd", stack="OpenAPI leftover optional body + Java + TS", field="required", old="requestBody required", new="optional body leftover only", fail_err="400: leftover required body after optional-only", plan="Optional-only 400s leftover required body. Freeze required, spec optional leftover.", residual="handoff: keep required body or force optional leftover", vs="wrap requestbody-required-put (optional leftover, not PUT cartesian)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch1_ok="Optional leftover bodies are not required:true.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#request-body-object", fetch2_ok="Exclusive optional body 400 leftover required.")),
    (p(slug="oas-encoding-style-form", domain="oas-enc-form-vs-enc-simple", success=True, name="encfrm", stack="OpenAPI 3.1 encoding.style form + Go", field="style", old="encoding simple leftover", new="encoding form style", fail_err="415: leftover encoding simple after form-only", plan="encoding-form-only 415s leftover simple. Dual-read simple for one release.", residual="ingest still simple leftover; drop after ingest 6", vs="r4023 leftover-multipart-form (encoding form vs simple leftover, not multipart mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#encoding-object", fetch1_ok="encoding.style form is the default for application/x-www-form-urlencoded.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch2_ok="Exclusive encoding form 415 leftover simple."),
     p(slug="leftover-encoding-simple", domain="enc-simple-vs-oas-enc-form", success=False, name="encsmp", stack="OpenAPI leftover encoding simple + Java + TS", field="style", old="encoding form style", new="encoding simple leftover only", fail_err="415: leftover encoding form after simple-only", plan="Simple-only 415s leftover encoding form. Freeze form, spec simple leftover.", residual="handoff: keep encoding form or force simple leftover", vs="r4023 oas-content-multipart-mixed (encoding simple leftover, not mixed mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch1_ok="encoding simple is not style=form.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#encoding-object", fetch2_ok="Exclusive encoding simple 415 leftover form.")),
    (p(slug="oas-schema-propertynames-ascii", domain="oas-propertynames-vs-unconstrained", success=True, name="pnascii", stack="OpenAPI 3.1 propertyNames ascii + Go", field="propertyNames", old="unconstrained keys leftover", new="propertyNames ascii", fail_err="400: leftover unconstrained keys after propertyNames-only", plan="propertyNames-only 400s leftover unconstrained. Dual-read unconstrained for one release.", residual="validator still unconstrained leftover; drop after validator 5", vs="wrap propertynames-extension (ascii propertyNames vs unconstrained leftover, not extension cartesian)", fetch1="https://json-schema.org/understanding-json-schema/reference/object#propertyNames", fetch1_ok="propertyNames constrains keys, leftover unconstrained keys fail closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive propertyNames 400 leftover unconstrained."),
     p(slug="leftover-unconstrained-keys", domain="unconstrained-vs-oas-propertynames", success=False, name="uck", stack="OpenAPI leftover unconstrained keys + Java + TS", field="properties", old="propertyNames ascii", new="unconstrained keys leftover only", fail_err="400: leftover propertyNames after unconstrained-only", plan="Unconstrained-only 400s leftover propertyNames. Freeze propertyNames, spec unconstrained leftover.", residual="handoff: keep propertyNames or force unconstrained leftover", vs="wrap propertynames-extension (unconstrained leftover, not extension cartesian)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Unconstrained keys are not propertyNames.", fetch2="https://json-schema.org/understanding-json-schema/reference/object#propertyNames", fetch2_ok="Exclusive unconstrained 400 leftover propertyNames.")),
    (p(slug="oas-schema-min-properties", domain="oas-minproperties-vs-empty-object", success=True, name="minprop", stack="OpenAPI 3.1 minProperties + Go", field="minProperties", old="empty object leftover", new="object minProperties", fail_err="400: leftover empty object after minProperties-only", plan="minProperties-only 400s leftover empty object. Dual-accept empty for one release.", residual="form still empty leftover; drop after form 4", vs="r3947 leftover-empty-array (minProperties vs empty object leftover, not minItems)", fetch1="https://json-schema.org/understanding-json-schema/reference/object#minproperties", fetch1_ok="minProperties rejects leftover empty objects.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive minProperties 400 leftover empty object."),
     p(slug="leftover-empty-object-body", domain="empty-object-vs-oas-minproperties", success=False, name="emptyob", stack="OpenAPI leftover empty object + Java + TS", field="properties", old="object minProperties", new="empty object leftover only", fail_err="400: leftover minProperties after empty-only", plan="Empty-only 400s leftover minProperties. Freeze minProperties, spec empty leftover.", residual="handoff: keep minProperties or force empty leftover", vs="r3947 leftover-empty-array (empty object leftover, not empty array)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Empty objects are not minProperties.", fetch2="https://json-schema.org/understanding-json-schema/reference/object#minproperties", fetch2_ok="Exclusive empty object 400 leftover minProperties.")),
    (p(slug="oas-format-uuid-strict", domain="oas-uuid-vs-hex-id", success=True, name="uuidst", stack="OpenAPI 3.1 format=uuid + Go", field="format", old="hex id leftover", new="format uuid", fail_err="400: leftover hex id after uuid-only", plan="format=uuid-only 400s leftover hex id. Dual-read hex for one release.", residual="store still hex leftover; drop after store 6", vs="r3561 format-uuid-v7 (strict uuid vs hex leftover, not uuid v7 mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/string#uuid", fetch1_ok="format=uuid is RFC 4122, leftover hex ids fail closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="Exclusive format=uuid 400 leftover hex id."),
     p(slug="leftover-hex-id", domain="hex-id-vs-oas-uuid", success=False, name="hexid", stack="OpenAPI leftover hex id + Java + TS", field="id", old="format uuid", new="hex id leftover only", fail_err="400: leftover format=uuid after hex-only", plan="Hex-only 400s leftover format=uuid. Freeze uuid, spec hex leftover.", residual="handoff: keep format=uuid or force hex leftover", vs="r3561 format-uuid-v7 (hex leftover, not uuid v7)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="Bare hex ids are not format=uuid.", fetch2="https://json-schema.org/understanding-json-schema/reference/string#uuid", fetch2_ok="Exclusive hex id 400 leftover uuid.")),
    (p(slug="oas-format-ipv4-cidr", domain="oas-ipv4-cidr-vs-dotted-int", success=True, name="ipv4c", stack="OpenAPI 3.1 ipv4 CIDR + Go", field="format", old="dotted int leftover", new="ipv4 cidr", fail_err="400: leftover dotted-int after ipv4-cidr-only", plan="ipv4-cidr-only 400s leftover dotted-int. Dual-read dotted for one release.", residual="acl still dotted leftover; drop after acl 5", vs="r3561 cidr-max-prefix (ipv4 cidr vs dotted leftover, not max prefix mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/string#ip-addresses", fetch1_ok="IPv4 CIDR is not leftover dotted integers.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="Exclusive ipv4 cidr 400 leftover dotted-int."),
     p(slug="leftover-dotted-int", domain="dotted-int-vs-oas-ipv4-cidr", success=False, name="dotint", stack="OpenAPI leftover dotted int + Java + TS", field="addr", old="ipv4 cidr", new="dotted int leftover only", fail_err="400: leftover ipv4-cidr after dotted-only", plan="Dotted-only 400s leftover ipv4-cidr. Freeze cidr, spec dotted leftover.", residual="handoff: keep ipv4 cidr or force dotted leftover", vs="r3561 cidr-max-prefix (dotted leftover, not max prefix)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="Dotted integers are not IPv4 CIDR.", fetch2="https://json-schema.org/understanding-json-schema/reference/string#ip-addresses", fetch2_ok="Exclusive dotted-int 400 leftover ipv4 cidr.")),
    (p(slug="oas-content-application-problem", domain="oas-problem-json-vs-error-string", success=True, name="problem", stack="OpenAPI 3.1 application/problem+json + Go", field="content", old="error string leftover", new="problem json", fail_err="415: leftover error string after problem-only", plan="problem+json-only 415s leftover error string. Dual-read string for one release.", residual="sdk still string leftover; drop after sdk 6", vs="r3963 leftover-missing-resp-desc (problem+json vs error string leftover, not resp desc)", fetch1="https://datatracker.ietf.org/doc/html/rfc9457", fetch1_ok="application/problem+json is not leftover error strings.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch2_ok="Exclusive problem+json 415 leftover error string."),
     p(slug="leftover-error-string", domain="error-string-vs-oas-problem-json", success=False, name="errstr", stack="OpenAPI leftover error string + Java + TS", field="error", old="problem json", new="error string leftover only", fail_err="415: leftover problem+json after string-only", plan="String-only 415s leftover problem+json. Freeze problem, spec string leftover.", residual="handoff: keep problem+json or force string leftover", vs="r3963 oas-response-description-req (error string leftover, not resp desc)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch1_ok="Error strings are not problem+json.", fetch2="https://datatracker.ietf.org/doc/html/rfc9457", fetch2_ok="Exclusive error string 415 leftover problem+json.")),
    (p(slug="oas-link-request-body", domain="oas-link-body-vs-query-link", success=True, name="lnkbody", stack="OpenAPI 3.1 link requestBody + Go", field="requestBody", old="query link leftover", new="link requestBody", fail_err="400: leftover query link after link-body-only", plan="link.requestBody-only 400s leftover query link. Dual-read query for one release.", residual="sdk still query leftover; drop after sdk 5", vs="r3993 leftover-no-links (link requestBody vs query leftover, not missing links)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#link-object", fetch1_ok="requestBody on links is a runtime expression, leftover query-only links are not that.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#runtime-expressions", fetch2_ok="Exclusive link requestBody 400 leftover query."),
     p(slug="leftover-query-link", domain="query-link-vs-oas-link-body", success=False, name="qlink", stack="OpenAPI leftover query link + Java + TS", field="parameters", old="link requestBody", new="query link leftover only", fail_err="400: leftover link.requestBody after query-only", plan="Query-only 400s leftover link.requestBody. Freeze requestBody, spec query leftover.", residual="handoff: keep link requestBody or force query leftover", vs="r3993 oas-response-links-required (query leftover, not required links)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#runtime-expressions", fetch1_ok="Query-only links are not requestBody.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#link-object", fetch2_ok="Exclusive query link 400 leftover requestBody.")),
    (p(slug="oas-webhook-options", domain="oas-webhook-options-vs-webhook-trace", success=True, name="whkopt", stack="OpenAPI 3.1 webhook OPTIONS + Go", field="options", old="webhook TRACE leftover", new="webhook OPTIONS", fail_err="405: leftover webhook TRACE after OPTIONS-only", plan="Webhook-OPTIONS-only 405s leftover TRACE. Dual-accept TRACE for one release.", residual="edge still TRACE leftover; drop after edge 4", vs="r4023 leftover-webhook-head (OPTIONS vs TRACE leftover, not HEAD mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#oasWebhooks", fetch1_ok="Webhook Path Items may OPTIONS; leftover TRACE is not the contract.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#path-item-object", fetch2_ok="Exclusive webhook OPTIONS 405 leftover TRACE."),
     p(slug="leftover-webhook-trace", domain="webhook-trace-vs-oas-webhook-options", success=False, name="whktr", stack="OpenAPI leftover webhook TRACE + Java + TS", field="trace", old="webhook OPTIONS", new="webhook TRACE leftover only", fail_err="405: leftover webhook OPTIONS after TRACE-only", plan="Webhook-TRACE-only 405s leftover OPTIONS. Freeze OPTIONS, spec TRACE leftover.", residual="handoff: keep webhook OPTIONS or force TRACE leftover", vs="r4023 oas-webhook-delete (TRACE leftover, not DELETE mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#path-item-object", fetch1_ok="Webhook TRACE is not the OPTIONS-only contract.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#oasWebhooks", fetch2_ok="Exclusive webhook TRACE 405 leftover OPTIONS.")),
    (p(slug="oas-servers-variables-pattern", domain="oas-server-pattern-vs-free-host", success=True, name="srvpat", stack="OpenAPI 3.1 server variable pattern + Go", field="pattern", old="free host var leftover", new="server variable pattern", fail_err="400: leftover free-host after pattern-only", plan="Server-pattern-only 400s leftover free-host. Dual-accept free for one release.", residual="mesh still free leftover; drop after mesh 6", vs="r3867 leftover-srv-var-free (pattern vs free leftover, not enum vs free mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#server-variable-object", fetch1_ok="pattern constrains server variables, leftover free hosts fail closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#server-object", fetch2_ok="Exclusive server pattern 400 leftover free-host."),
     p(slug="leftover-free-host-var", domain="free-host-vs-oas-server-pattern", success=False, name="freehv", stack="OpenAPI leftover free host var + Java + TS", field="default", old="server variable pattern", new="free host var leftover only", fail_err="400: leftover server pattern after free-only", plan="Free-only 400s leftover server pattern. Freeze pattern, spec free leftover.", residual="handoff: keep server pattern or force free leftover", vs="r4007 leftover-default-outside-enum (free leftover, not outside-enum mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#server-object", fetch1_ok="Free host vars are not pattern.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#server-variable-object", fetch2_ok="Exclusive free-host 400 leftover pattern.")),
    (p(slug="oas-discriminator-property-required", domain="oas-disc-required-vs-optional-disc", success=True, name="discreq", stack="OpenAPI 3.1 discriminator property required + Go", field="propertyName", old="optional disc leftover", new="required discriminator property", fail_err="400: leftover optional disc after required-only", plan="Required-disc-only 400s leftover optional. Dual-omit disc for one release.", residual="sdk still optional leftover; drop after sdk 5", vs="r4007 leftover-implicit-disc (required disc vs optional leftover, not implicit mapping)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#discriminator-object", fetch1_ok="propertyName must be present and required, leftover optional disc fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive required disc 400 leftover optional."),
     p(slug="leftover-optional-disc", domain="optional-disc-vs-oas-disc-required", success=False, name="optdisc", stack="OpenAPI leftover optional discriminator + Java + TS", field="propertyName", old="required discriminator property", new="optional disc leftover only", fail_err="400: leftover required disc after optional-only", plan="Optional-only 400s leftover required disc. Freeze required, spec optional leftover.", residual="handoff: keep required disc or force optional leftover", vs="r4007 oas-discriminator-mapping-explicit (optional leftover, not mapping mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Optional leftover discriminators are not required propertyName.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#discriminator-object", fetch2_ok="Exclusive optional disc 400 leftover required.")),
    (p(slug="oas-schema-const-literal", domain="oas-const-vs-one-value-enum", success=True, name="constl", stack="OpenAPI 3.1 const + Go", field="const", old="one value enum leftover", new="schema const", fail_err="400: leftover one-value enum after const-only", plan="const-only 400s leftover one-value enum. Dual-read enum for one release.", residual="codegen still enum leftover; drop after codegen 5", vs="wrap const-status-replaces-enum (const vs one-value leftover, not status cartesian)", fetch1="https://json-schema.org/understanding-json-schema/reference/const", fetch1_ok="const is a single literal, leftover one-value enums are not that.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive const 400 leftover one-value enum."),
     p(slug="leftover-enum-one-value", domain="one-value-enum-vs-oas-const", success=False, name="enum1", stack="OpenAPI leftover one-value enum + Java + TS", field="enum", old="schema const", new="one value enum leftover only", fail_err="400: leftover const after enum-only", plan="Enum-only 400s leftover const. Freeze const, spec enum leftover.", residual="handoff: keep const or force one-value enum leftover", vs="wrap const-status-replaces-enum (one-value leftover, not status cartesian)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="One-value enums are not const.", fetch2="https://json-schema.org/understanding-json-schema/reference/const", fetch2_ok="Exclusive one-value enum 400 leftover const.")),
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
    print(json.dumps({"round": round_n, "idx": idx, "ids": [e1["id"], e2["id"]], "catalog": "r4038"}))


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
