#!/usr/bin/env python3
"""Unique OpenAPI-drift ACM catalog r4358. Fast slug load."""
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
    (p(slug="oas-schema-content-encoding-b64", domain="oas-schema-content-encoding-b64-vs-leftover-raw-unicode-blob", success=True, name="07abfd", stack="OpenAPI 3.1 contentEncoding + Go", field="contentEncoding", old="raw unicode leftover", new="contentEncoding base64", fail_err="415: leftover raw unicode leftover after contentEncoding base64-only", plan="contentEncoding base64-only 415s leftover raw unicode leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (contentEncoding base64 vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/non_json_data#contentencoding", fetch1_ok="contentEncoding base64 is not leftover raw unicode blobs.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="Exclusive contentEncoding 415 leftover raw unicode."),
     p(slug="leftover-raw-unicode-blob", domain="leftover-raw-unicode-blob-vs-oas-schema-content-encoding-b64", success=False, name="52404d", stack="OpenAPI leftover contentEncoding + Java + TS", field="contentEncoding", old="contentEncoding base64", new="raw unicode leftover only", fail_err="415: leftover contentEncoding base64 after raw unicode leftover-only", plan="raw unicode leftover-only 415s leftover contentEncoding base64. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (raw unicode leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="Exclusive contentEncoding 415 leftover raw unicode.", fetch2="https://json-schema.org/understanding-json-schema/reference/non_json_data#contentencoding", fetch2_ok="contentEncoding base64 is not leftover raw unicode blobs.")),
    (p(slug="oas-schema-content-schema-ref", domain="oas-schema-content-schema-ref-vs-leftover-untyped-encoded-payload", success=True, name="3a11fd", stack="OpenAPI 3.1 contentSchema + Go", field="contentSchema", old="untyped encoded leftover", new="contentSchema ref", fail_err="400: leftover untyped encoded leftover after contentSchema ref-only", plan="contentSchema ref-only 400s leftover untyped encoded leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (contentSchema ref vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/non_json_data#contentschema", fetch1_ok="contentSchema validates decoded payload, leftover untyped fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive contentSchema 400 leftover untyped."),
     p(slug="leftover-untyped-encoded-payload", domain="leftover-untyped-encoded-payload-vs-oas-schema-content-schema-ref", success=False, name="4622c6", stack="OpenAPI leftover contentSchema + Java + TS", field="contentSchema", old="contentSchema ref", new="untyped encoded leftover only", fail_err="400: leftover contentSchema ref after untyped encoded leftover-only", plan="untyped encoded leftover-only 400s leftover contentSchema ref. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (untyped encoded leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive contentSchema 400 leftover untyped.", fetch2="https://json-schema.org/understanding-json-schema/reference/non_json_data#contentschema", fetch2_ok="contentSchema validates decoded payload, leftover untyped fails closed.")),
    (p(slug="oas-schema-dynamic-ref", domain="oas-schema-dynamic-ref-vs-leftover-static-ref-only", success=True, name="262287", stack="OpenAPI 3.1 $dynamicRef + Go", field="$dynamicRef", old="static ref leftover", new="$dynamicRef", fail_err="400: leftover static ref leftover after $dynamicRef-only", plan="$dynamicRef-only 400s leftover static ref leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv ($dynamicRef vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/schema#dynamic-references", fetch1_ok="$dynamicRef is not leftover static $ref only.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive $dynamicRef 400 leftover static ref."),
     p(slug="leftover-static-ref-only", domain="leftover-static-ref-only-vs-oas-schema-dynamic-ref", success=False, name="881fd0", stack="OpenAPI leftover $dynamicRef + Java + TS", field="$dynamicRef", old="$dynamicRef", new="static ref leftover only", fail_err="400: leftover $dynamicRef after static ref leftover-only", plan="static ref leftover-only 400s leftover $dynamicRef. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (static ref leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive $dynamicRef 400 leftover static ref.", fetch2="https://json-schema.org/understanding-json-schema/reference/schema#dynamic-references", fetch2_ok="$dynamicRef is not leftover static $ref only.")),
    (p(slug="oas-schema-defs-reuse", domain="oas-schema-defs-reuse-vs-leftover-inline-subschema-only", success=True, name="fef609", stack="OpenAPI 3.1 $defs + Go", field="$defs", old="inline subschema leftover", new="$defs reuse", fail_err="400: leftover inline subschema leftover after $defs reuse-only", plan="$defs reuse-only 400s leftover inline subschema leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv ($defs reuse vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/schema#defs", fetch1_ok="$defs reuses subschemas, leftover inline-only fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive $defs 400 leftover inline."),
     p(slug="leftover-inline-subschema-only", domain="leftover-inline-subschema-only-vs-oas-schema-defs-reuse", success=False, name="15b683", stack="OpenAPI leftover $defs + Java + TS", field="$defs", old="$defs reuse", new="inline subschema leftover only", fail_err="400: leftover $defs reuse after inline subschema leftover-only", plan="inline subschema leftover-only 400s leftover $defs reuse. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (inline subschema leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive $defs 400 leftover inline.", fetch2="https://json-schema.org/understanding-json-schema/reference/schema#defs", fetch2_ok="$defs reuses subschemas, leftover inline-only fails closed.")),
    (p(slug="oas-dependent-required-keys", domain="oas-dependent-required-keys-vs-leftover-manual-required-pair", success=True, name="934a9b", stack="OpenAPI 3.1 dependentRequired + Go", field="dependentRequired", old="manual required leftover", new="dependentRequired keys", fail_err="400: leftover manual required leftover after dependentRequired keys-only", plan="dependentRequired keys-only 400s leftover manual required leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (dependentRequired keys vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/object#dependentrequired", fetch1_ok="dependentRequired pairs keys, leftover manual required fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive dependentRequired 400 leftover manual."),
     p(slug="leftover-manual-required-pair", domain="leftover-manual-required-pair-vs-oas-dependent-required-keys", success=False, name="1570f1", stack="OpenAPI leftover dependentRequired + Java + TS", field="dependentRequired", old="dependentRequired keys", new="manual required leftover only", fail_err="400: leftover dependentRequired keys after manual required leftover-only", plan="manual required leftover-only 400s leftover dependentRequired keys. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (manual required leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive dependentRequired 400 leftover manual.", fetch2="https://json-schema.org/understanding-json-schema/reference/object#dependentrequired", fetch2_ok="dependentRequired pairs keys, leftover manual required fails closed.")),
    (p(slug="oas-info-ver-semver", domain="oas-info-ver-semver-vs-leftover-freeform-version", success=True, name="f8ffac", stack="OpenAPI 3.1 version + Go", field="version", old="freeform version leftover", new="semver info version", fail_err="400: leftover freeform version leftover after semver info version-only", plan="semver info version-only 400s leftover freeform version leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (semver info version vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#info-object", fetch1_ok="info.version should be semver, leftover freeform fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#openapi-object", fetch2_ok="Exclusive semver 400 leftover freeform."),
     p(slug="leftover-freeform-version", domain="leftover-freeform-version-vs-oas-info-ver-semver", success=False, name="0bfe09", stack="OpenAPI leftover version + Java + TS", field="version", old="semver info version", new="freeform version leftover only", fail_err="400: leftover semver info version after freeform version leftover-only", plan="freeform version leftover-only 400s leftover semver info version. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (freeform version leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#openapi-object", fetch1_ok="Exclusive semver 400 leftover freeform.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#info-object", fetch2_ok="info.version should be semver, leftover freeform fails closed.")),
    (p(slug="oas-root-openapi-31", domain="oas-root-openapi-31-vs-leftover-openapi-30-root", success=True, name="7aac2a", stack="OpenAPI 3.1 openapi + Go", field="openapi", old="openapi 3.0 leftover", new="openapi 3.1 root", fail_err="400: leftover openapi 3.0 leftover after openapi 3.1 root-only", plan="openapi 3.1 root-only 400s leftover openapi 3.0 leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (openapi 3.1 root vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#versions", fetch1_ok="openapi 3.1.0 is not leftover 3.0.3 root.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#openapi-object", fetch2_ok="Exclusive 3.1 400 leftover 3.0."),
     p(slug="leftover-openapi-30-root", domain="leftover-openapi-30-root-vs-oas-root-openapi-31", success=False, name="058cce", stack="OpenAPI leftover openapi + Java + TS", field="openapi", old="openapi 3.1 root", new="openapi 3.0 leftover only", fail_err="400: leftover openapi 3.1 root after openapi 3.0 leftover-only", plan="openapi 3.0 leftover-only 400s leftover openapi 3.1 root. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (openapi 3.0 leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#openapi-object", fetch1_ok="Exclusive 3.1 400 leftover 3.0.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#versions", fetch2_ok="openapi 3.1.0 is not leftover 3.0.3 root.")),
    (p(slug="oas-paths-nonempty-root", domain="oas-paths-nonempty-root-vs-leftover-empty-paths-map", success=True, name="f4b31a", stack="OpenAPI 3.1 paths + Go", field="paths", old="empty paths leftover", new="nonempty paths", fail_err="400: leftover empty paths leftover after nonempty paths-only", plan="nonempty paths-only 400s leftover empty paths leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (nonempty paths vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#paths-object", fetch1_ok="paths must be nonempty, leftover empty map fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#openapi-object", fetch2_ok="Exclusive nonempty paths 400 leftover empty."),
     p(slug="leftover-empty-paths-map", domain="leftover-empty-paths-map-vs-oas-paths-nonempty-root", success=False, name="e1b02d", stack="OpenAPI leftover paths + Java + TS", field="paths", old="nonempty paths", new="empty paths leftover only", fail_err="400: leftover nonempty paths after empty paths leftover-only", plan="empty paths leftover-only 400s leftover nonempty paths. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (empty paths leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#openapi-object", fetch1_ok="Exclusive nonempty paths 400 leftover empty.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#paths-object", fetch2_ok="paths must be nonempty, leftover empty map fails closed.")),
    (p(slug="oas-opid-globally-unique", domain="oas-opid-globally-unique-vs-leftover-repeated-opid", success=True, name="87ca45", stack="OpenAPI 3.1 operationId + Go", field="operationId", old="repeated opid leftover", new="globally unique operationId", fail_err="400: leftover repeated opid leftover after globally unique operationId-only", plan="globally unique operationId-only 400s leftover repeated opid leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (globally unique operationId vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch1_ok="operationId must be unique, leftover repeats fail closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#paths-object", fetch2_ok="Exclusive unique opid 400 leftover repeat."),
     p(slug="leftover-repeated-opid", domain="leftover-repeated-opid-vs-oas-opid-globally-unique", success=False, name="c40864", stack="OpenAPI leftover operationId + Java + TS", field="operationId", old="globally unique operationId", new="repeated opid leftover only", fail_err="400: leftover globally unique operationId after repeated opid leftover-only", plan="repeated opid leftover-only 400s leftover globally unique operationId. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (repeated opid leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#paths-object", fetch1_ok="Exclusive unique opid 400 leftover repeat.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch2_ok="operationId must be unique, leftover repeats fail closed.")),
    (p(slug="oas-parameter-name-required", domain="oas-parameter-name-required-vs-leftover-anonymous-param", success=True, name="6b23ac", stack="OpenAPI 3.1 name + Go", field="name", old="anonymous param leftover", new="parameter name required", fail_err="400: leftover anonymous param leftover after parameter name required-only", plan="parameter name required-only 400s leftover anonymous param leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (parameter name required vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="parameter.name is required, leftover anonymous fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch2_ok="Exclusive param name 400 leftover anonymous."),
     p(slug="leftover-anonymous-param", domain="leftover-anonymous-param-vs-oas-parameter-name-required", success=False, name="7a303f", stack="OpenAPI leftover name + Java + TS", field="name", old="parameter name required", new="anonymous param leftover only", fail_err="400: leftover parameter name required after anonymous param leftover-only", plan="anonymous param leftover-only 400s leftover parameter name required. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (anonymous param leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch1_ok="Exclusive param name 400 leftover anonymous.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="parameter.name is required, leftover anonymous fails closed.")),
    (p(slug="oas-in-path-required", domain="oas-in-path-required-vs-leftover-path-param-optional", success=True, name="e03c54", stack="OpenAPI 3.1 required + Go", field="required", old="optional path leftover", new="path param required", fail_err="400: leftover optional path leftover after path param required-only", plan="path param required-only 400s leftover optional path leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (path param required vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="Path parameters are always required, leftover optional fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#path-templating", fetch2_ok="Exclusive path required 400 leftover optional."),
     p(slug="leftover-path-param-optional", domain="leftover-path-param-optional-vs-oas-in-path-required", success=False, name="ceb1e9", stack="OpenAPI leftover required + Java + TS", field="required", old="path param required", new="optional path leftover only", fail_err="400: leftover path param required after optional path leftover-only", plan="optional path leftover-only 400s leftover path param required. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (optional path leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#path-templating", fetch1_ok="Exclusive path required 400 leftover optional.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="Path parameters are always required, leftover optional fails closed.")),
    (p(slug="oas-path-template-bind", domain="oas-path-template-bind-vs-leftover-unbound-path-param", success=True, name="5c8e50", stack="OpenAPI 3.1 name + Go", field="name", old="unbound path leftover", new="path template bind", fail_err="400: leftover unbound path leftover after path template bind-only", plan="path template bind-only 400s leftover unbound path leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (path template bind vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#path-templating", fetch1_ok="Path template params must bind, leftover unbound fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#paths-object", fetch2_ok="Exclusive path bind 400 leftover unbound."),
     p(slug="leftover-unbound-path-param", domain="leftover-unbound-path-param-vs-oas-path-template-bind", success=False, name="aa646c", stack="OpenAPI leftover name + Java + TS", field="name", old="path template bind", new="unbound path leftover only", fail_err="400: leftover path template bind after unbound path leftover-only", plan="unbound path leftover-only 400s leftover path template bind. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (unbound path leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#paths-object", fetch1_ok="Exclusive path bind 400 leftover unbound.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#path-templating", fetch2_ok="Path template params must bind, leftover unbound fails closed.")),
    (p(slug="oas-http-bearer-jwt", domain="oas-http-bearer-jwt-vs-leftover-opaque-bearer-token", success=True, name="60b509", stack="OpenAPI 3.1 bearerFormat + Go", field="bearerFormat", old="opaque bearer leftover", new="bearerFormat JWT", fail_err="401: leftover opaque bearer leftover after bearerFormat JWT-only", plan="bearerFormat JWT-only 401s leftover opaque bearer leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (bearerFormat JWT vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch1_ok="bearerFormat JWT is not leftover opaque tokens.", fetch2="https://datatracker.ietf.org/doc/html/rfc7519", fetch2_ok="Exclusive JWT bearer 401 leftover opaque."),
     p(slug="leftover-opaque-bearer-token", domain="leftover-opaque-bearer-token-vs-oas-http-bearer-jwt", success=False, name="5db87f", stack="OpenAPI leftover bearerFormat + Java + TS", field="bearerFormat", old="bearerFormat JWT", new="opaque bearer leftover only", fail_err="401: leftover bearerFormat JWT after opaque bearer leftover-only", plan="opaque bearer leftover-only 401s leftover bearerFormat JWT. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (opaque bearer leftover leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc7519", fetch1_ok="Exclusive JWT bearer 401 leftover opaque.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch2_ok="bearerFormat JWT is not leftover opaque tokens.")),
    (p(slug="oas-oauth2-implicit-banned", domain="oas-oauth2-implicit-banned-vs-leftover-implicit-hash-token", success=True, name="6c4f6e", stack="OpenAPI 3.1 implicit + Go", field="implicit", old="implicit hash leftover", new="implicit flow banned", fail_err="401: leftover implicit hash leftover after implicit flow banned-only", plan="implicit flow banned-only 401s leftover implicit hash leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (implicit flow banned vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#oauth-flows-object", fetch1_ok="Implicit flow is banned here, leftover hash tokens fail closed.", fetch2="https://datatracker.ietf.org/doc/html/rfc6749#section-4.2", fetch2_ok="Exclusive implicit ban 401 leftover hash."),
     p(slug="leftover-implicit-hash-token", domain="leftover-implicit-hash-token-vs-oas-oauth2-implicit-banned", success=False, name="e1b94f", stack="OpenAPI leftover implicit + Java + TS", field="implicit", old="implicit flow banned", new="implicit hash leftover only", fail_err="401: leftover implicit flow banned after implicit hash leftover-only", plan="implicit hash leftover-only 401s leftover implicit flow banned. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (implicit hash leftover leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc6749#section-4.2", fetch1_ok="Exclusive implicit ban 401 leftover hash.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#oauth-flows-object", fetch2_ok="Implicit flow is banned here, leftover hash tokens fail closed.")),
    (p(slug="oas-response-headers-map", domain="oas-response-headers-map-vs-leftover-headers-in-body", success=True, name="15d4a1", stack="OpenAPI 3.1 headers + Go", field="headers", old="headers in body leftover", new="response headers map", fail_err="400: leftover headers in body leftover after response headers map-only", plan="response headers map-only 400s leftover headers in body leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (response headers map vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#response-object", fetch1_ok="response.headers is not leftover headers-in-body.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch2_ok="Exclusive response headers 400 leftover body."),
     p(slug="leftover-headers-in-body", domain="leftover-headers-in-body-vs-oas-response-headers-map", success=False, name="613ef5", stack="OpenAPI leftover headers + Java + TS", field="headers", old="response headers map", new="headers in body leftover only", fail_err="400: leftover response headers map after headers in body leftover-only", plan="headers in body leftover-only 400s leftover response headers map. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (headers in body leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch1_ok="Exclusive response headers 400 leftover body.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#response-object", fetch2_ok="response.headers is not leftover headers-in-body.")),
    (p(slug="oas-object-required-keys", domain="oas-object-required-keys-vs-leftover-all-optional-object", success=True, name="212f5e", stack="OpenAPI 3.1 required + Go", field="required", old="all optional leftover", new="object required keys", fail_err="400: leftover all optional leftover after object required keys-only", plan="object required keys-only 400s leftover all optional leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (object required keys vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/object#required-properties", fetch1_ok="required keys must be present, leftover all-optional fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive required keys 400 leftover all optional."),
     p(slug="leftover-all-optional-object", domain="leftover-all-optional-object-vs-oas-object-required-keys", success=False, name="d162ad", stack="OpenAPI leftover required + Java + TS", field="required", old="object required keys", new="all optional leftover only", fail_err="400: leftover object required keys after all optional leftover-only", plan="all optional leftover-only 400s leftover object required keys. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (all optional leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive required keys 400 leftover all optional.", fetch2="https://json-schema.org/understanding-json-schema/reference/object#required-properties", fetch2_ok="required keys must be present, leftover all-optional fails closed.")),
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
    print(json.dumps({"round": round_n, "idx": idx, "ids": [e1["id"], e2["id"]], "catalog": "r4358"}))


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
