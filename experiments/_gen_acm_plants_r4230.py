#!/usr/bin/env python3
"""Emit unique OpenAPI-drift ACM mill files starting at r4230."""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
USED = set()
SLUG_RE = re.compile(r'slug="([^"]+)"')
SKIP_MILL = re.compile(r"acm-mill-r(\d+)\.py")
for path in HERE.glob("acm-mill-r*.py"):
    m = SKIP_MILL.fullmatch(path.name)
    if m and int(m.group(1)) >= 4230:
        continue
    USED.update(SLUG_RE.findall(path.read_text(errors="ignore")))
SEED_RE = re.compile(r"seed=([a-z0-9-]+)")
FACTORY = HERE.parent / "outputs" / "raw" / "2026-08-19-agentic" / "api-contract-migration-factory"
NOTES_N = re.compile(r"NOTES-r(\d+)\.md")
if FACTORY.is_dir():
    for path in FACTORY.glob("NOTES-r*.md"):
        nm = NOTES_N.fullmatch(path.name)
        if nm and int(nm.group(1)) >= 4230:
            continue
        try:
            USED.update(SEED_RE.findall(path.read_text(errors="ignore")))
        except OSError:
            pass

SPEC = "https://spec.openapis.org/oas/v3.1.0.html"
JS = "https://json-schema.org/understanding-json-schema/reference"
RFC = "https://datatracker.ietf.org/doc/html"

# (a_slug, b_slug, field, old, new, code, fetch1, ok1, fetch2, ok2)
# vs is derived.
MILLS: dict[int, list[tuple[str, str, str, str, str, str, str, str, str, str]]] = {
    4230: [
        ("oas-root-jsonschemadialect-uri", "leftover-implicit-draft2020", "jsonSchemaDialect", "implicit draft leftover", "root jsonSchemaDialect", "400",
         f"{SPEC}#openapi-object", "jsonSchemaDialect sets the default dialect, leftover implicit fails closed.",
         f"{JS}/schema", "Exclusive dialect 400 leftover implicit."),
        ("oas-schema-prefixitems-tuple", "leftover-items-array-tuple", "prefixItems", "items tuple leftover", "prefixItems tuple", "400",
         f"{JS}/array#tuple-validation", "prefixItems is positional tuple validation, leftover items-as-tuple fails closed.",
         f"{SPEC}#schema-object", "Exclusive prefixItems 400 leftover items tuple."),
        ("oas-unevaluated-items-false", "leftover-open-tuple-tail", "unevaluatedItems", "open tuple tail leftover", "unevaluatedItems false", "400",
         f"{JS}/array#unevaluateditems", "unevaluatedItems false closes leftover tuple tails.",
         f"{SPEC}#schema-object", "Exclusive unevaluatedItems 400 leftover open tail."),
        ("oas-schema-content-media-type", "leftover-untyped-encoded-blob", "contentMediaType", "untyped encoded leftover", "contentMediaType", "415",
         f"{JS}/non_json_data#contentmediatype", "contentMediaType names the decoded type, leftover untyped blobs fail closed.",
         f"{SPEC}#data-types", "Exclusive contentMediaType 415 leftover untyped blob."),
        ("oas-schema-dynamic-anchor", "leftover-static-anchor-only", "$dynamicAnchor", "static anchor leftover", "$dynamicAnchor", "400",
         f"{JS}/schema#dynamic-references", "$dynamicAnchor is not leftover static $anchor only.",
         f"{SPEC}#schema-object", "Exclusive $dynamicAnchor 400 leftover static."),
        ("oas-schema-externaldocs-url", "leftover-schema-no-docs", "externalDocs", "schema no docs leftover", "schema externalDocs url", "400",
         f"{SPEC}#external-documentation-object", "Schema externalDocs.url is required when present, leftover missing fails closed.",
         f"{SPEC}#schema-object", "Exclusive schema docs 400 leftover none."),
        ("oas-parameter-allow-reserved", "leftover-always-percent-encode", "allowReserved", "always percent leftover", "allowReserved true", "400",
         f"{SPEC}#parameter-object", "allowReserved lets RFC3986 reserved chars through, leftover always-encode fails closed.",
         f"{RFC}/rfc3986", "Exclusive allowReserved 400 leftover percent-all."),
        ("oas-schema-exclusive-min-number", "leftover-exclusive-min-boolean", "exclusiveMinimum", "boolean exclusiveMinimum leftover", "numeric exclusiveMinimum", "400",
         f"{JS}/numeric#exclusiveminimum", "JSON Schema 2020-12 exclusiveMinimum is a number, leftover OAS 3.0 boolean fails closed.",
         f"{SPEC}#data-types", "Exclusive numeric exclusiveMinimum 400 leftover boolean."),
        ("oas-type-null-union", "leftover-nullable-true-flag", "type", "nullable true leftover", "type null union", "400",
         f"{SPEC}#data-types", "OAS 3.1 uses type union with null, leftover nullable true fails closed.",
         f"{JS}/null", "Exclusive type null union 400 leftover nullable."),
        ("oas-json-schema-const-value", "leftover-single-enum-member", "const", "single enum leftover", "schema const", "400",
         f"{JS}/generic#const", "const is a single literal, leftover enum-of-one is not that.",
         f"{SPEC}#schema-object", "Exclusive const 400 leftover singleton enum."),
        ("oas-http-bearer-format", "leftover-unformatted-bearer", "bearerFormat", "unformatted bearer leftover", "bearerFormat", "401",
         f"{SPEC}#security-scheme-object", "bearerFormat documents the token, leftover unformatted fails closed.",
         f"{RFC}/rfc6750", "Exclusive bearerFormat 401 leftover unformatted."),
        ("oas-encoding-allow-reserved", "leftover-encoding-pct-all", "allowReserved", "encoding percent leftover", "encoding allowReserved", "415",
         f"{SPEC}#encoding-object", "encoding.allowReserved is not leftover percent-encode-all parts.",
         f"{RFC}/rfc3986", "Exclusive encoding allowReserved 415 leftover percent-all."),
        ("oas-link-opref-pointer", "leftover-link-opid-only", "operationRef", "operationId only leftover", "link operationRef", "400",
         f"{SPEC}#link-object", "operationRef is a runtime pointer, leftover operationId-only is not that.",
         f"{SPEC}#runtime-expressions", "Exclusive operationRef 400 leftover opid only."),
        ("oas-path-head-method", "leftover-get-as-head", "head", "GET as HEAD leftover", "HEAD method", "400",
         f"{SPEC}#path-item-object", "HEAD is a distinct operation, leftover GET-as-HEAD fails closed.",
         f"{RFC}/rfc9110#name-head", "Exclusive HEAD 400 leftover GET-as-HEAD."),
        ("oas-oauth2-password-flow", "leftover-ropc-query-token", "password", "ROPC query leftover", "oauth2 password flow", "401",
         f"{SPEC}#oauth-flow-object", "password flow uses tokenUrl, leftover query-token ROPC fails closed.",
         f"{RFC}/rfc6749#section-4.3", "Exclusive password flow 401 leftover query token."),
        ("oas-security-oidc-url", "leftover-issuer-only-oidc", "openIdConnectUrl", "issuer only leftover", "openIdConnectUrl", "401",
         f"{SPEC}#security-scheme-object", "openIdConnectUrl is the discovery document, leftover issuer-only fails closed.",
         f"{RFC}/rfc8414", "Exclusive OIDC url 401 leftover issuer."),
    ],
    4246: [
        ("oas-schema-readonly-omit-write", "leftover-write-echo-readonly", "readOnly", "write echo leftover", "readOnly omit write", "400",
         f"{SPEC}#schema-object", "readOnly properties must be omitted on write, leftover echo fails closed.",
         f"{JS}/object", "Exclusive readOnly omit 400 leftover write echo."),
        ("oas-schema-deprecated-true", "leftover-ship-deprecated-field", "deprecated", "ship deprecated leftover", "schema deprecated true", "400",
         f"{SPEC}#schema-object", "deprecated true must not ship as live, leftover still-shipped fails closed.",
         f"{JS}/generic#annotation", "Exclusive deprecated 400 leftover shipped field."),
        ("oas-media-single-example", "leftover-examples-map-forced", "example", "examples map leftover", "media example", "400",
         f"{SPEC}#media-type-object", "example is a single value, leftover examples-map-only is not that.",
         f"{SPEC}#example-object", "Exclusive media example 400 leftover examples map."),
        ("oas-query-explode-false-obj", "leftover-query-explode-obj", "explode", "explode object leftover", "query explode false", "400",
         f"{SPEC}#style-values", "explode false serializes objects as one param, leftover explode fails closed.",
         f"{SPEC}#parameter-object", "Exclusive explode false 400 leftover explode obj."),
        ("oas-query-style-space-delim", "leftover-query-space-csv", "style", "space csv leftover", "spaceDelimited query", "400",
         f"{SPEC}#style-values", "spaceDelimited is not leftover comma-joined spaces.",
         f"{SPEC}#parameter-object", "Exclusive spaceDelimited 400 leftover space csv."),
        ("oas-info-terms-uri-https", "leftover-tos-plaintext", "termsOfService", "plaintext tos leftover", "termsOfService https uri", "400",
         f"{SPEC}#info-object", "termsOfService must be a URI, leftover plaintext fails closed.",
         f"{RFC}/rfc3986", "Exclusive tos uri 400 leftover plaintext."),
        ("oas-xml-attr-ns-uri", "leftover-xml-attr-bare", "namespace", "bare xml attr leftover", "xml attr namespace", "415",
         f"{SPEC}#xml-object", "xml.namespace on attributes is not leftover bare attrs.",
         f"{SPEC}#schema-object", "Exclusive xml attr ns 415 leftover bare."),
        ("oas-schema-anyof-closed-set", "leftover-typeless-union", "anyOf", "typeless union leftover", "anyOf closed set", "400",
         f"{JS}/combining#anyof", "anyOf is a closed alternative set, leftover typeless union fails closed.",
         f"{SPEC}#schema-object", "Exclusive anyOf 400 leftover typeless."),
        ("oas-schema-allof-merge-req", "leftover-partial-allof-req", "allOf", "partial allOf leftover", "allOf merge required", "400",
         f"{JS}/combining#allof", "allOf merges required, leftover partial allOf fails closed.",
         f"{SPEC}#schema-object", "Exclusive allOf merge 400 leftover partial."),
        ("oas-cb-components-reuse", "leftover-inline-cb-only", "callbacks", "inline callback leftover", "components callbacks reuse", "400",
         f"{SPEC}#components-object", "components.callbacks reuse Callback Objects, leftover inline-only is not that.",
         f"{SPEC}#callback-object", "Exclusive components callbacks 400 leftover inline."),
        ("oas-patch-json-merge-patch", "leftover-put-for-patch", "patch", "PUT as PATCH leftover", "JSON merge PATCH", "400",
         f"{SPEC}#path-item-object", "PATCH is merge/patch, leftover PUT-as-PATCH fails closed.",
         f"{RFC}/rfc7396", "Exclusive merge PATCH 400 leftover PUT."),
        ("oas-schema-ifthen-else", "leftover-oneof-conditional", "if", "oneOf conditional leftover", "if then else", "400",
         f"{JS}/conditionals", "if/then/else is not leftover oneOf-as-conditional.",
         f"{SPEC}#schema-object", "Exclusive if/then/else 400 leftover oneOf."),
        ("oas-object-max-properties", "leftover-object-key-unbounded", "maxProperties", "unbounded keys leftover", "maxProperties", "400",
         f"{JS}/object#maxproperties", "maxProperties bounds object keys, leftover unbounded fails closed.",
         f"{SPEC}#schema-object", "Exclusive maxProperties 400 leftover unbounded keys."),
        ("oas-object-min-properties", "leftover-zero-key-object", "minProperties", "zero key leftover", "minProperties", "400",
         f"{JS}/object#minproperties", "minProperties rejects empty objects, leftover zero-key fails closed.",
         f"{SPEC}#schema-object", "Exclusive minProperties 400 leftover empty object."),
        ("oas-object-property-names", "leftover-any-object-key", "propertyNames", "any key leftover", "propertyNames schema", "400",
         f"{JS}/object#propertynames", "propertyNames constrains keys, leftover any-key fails closed.",
         f"{SPEC}#schema-object", "Exclusive propertyNames 400 leftover any key."),
        ("oas-format-uuid-rfc4122", "leftover-guid-braces", "format", "braced guid leftover", "format uuid rfc4122", "400",
         f"{JS}/string#uuid", "format=uuid is RFC4122, leftover braced GUIDs fail closed.",
         f"{RFC}/rfc4122", "Exclusive uuid 400 leftover braced guid."),
    ],
    4262: [
        ("oas-json-schema-id-uri", "leftover-unanchored-schema", "$id", "unanchored leftover", "schema $id uri", "400",
         f"{JS}/schema#id", "$id identifies the schema resource, leftover unanchored fails closed.",
         f"{SPEC}#schema-object", "Exclusive $id 400 leftover unanchored."),
        ("oas-json-schema-schema-uri", "leftover-implicit-schema-draft", "$schema", "implicit draft leftover", "$schema uri", "400",
         f"{JS}/schema#schema", "$schema names the dialect, leftover implicit fails closed.",
         f"{SPEC}#schema-object", "Exclusive $schema 400 leftover implicit."),
        ("oas-operation-deprecated-flag", "leftover-ship-deprecated-op", "deprecated", "ship deprecated op leftover", "operation deprecated", "400",
         f"{SPEC}#operation-object", "deprecated operations must not ship as live, leftover still-shipped fails closed.",
         f"{SPEC}#path-item-object", "Exclusive op deprecated 400 leftover live op."),
        ("oas-response-desc-required", "leftover-blank-response-desc", "description", "blank response leftover", "response description", "400",
         f"{SPEC}#response-object", "response.description is required, leftover blank fails closed.",
         f"{SPEC}#responses-object", "Exclusive response desc 400 leftover blank."),
        ("oas-info-desc-required", "leftover-empty-info-desc", "description", "empty info leftover", "info description", "400",
         f"{SPEC}#info-object", "info.description documents the API, leftover empty fails closed.",
         f"{SPEC}#openapi-object", "Exclusive info desc 400 leftover empty."),
        ("oas-contact-name-required", "leftover-email-only-contact", "name", "email only leftover", "contact name", "400",
         f"{SPEC}#contact-object", "contact.name is required with contact, leftover email-only fails closed.",
         f"{SPEC}#info-object", "Exclusive contact name 400 leftover email only."),
        ("oas-license-url-https", "leftover-license-name-only", "url", "license name leftover", "license url https", "400",
         f"{SPEC}#license-object", "license.url must be https when present, leftover name-only fails closed.",
         f"{SPEC}#info-object", "Exclusive license url 400 leftover name only."),
        ("oas-server-desc-required", "leftover-bare-server-url", "description", "bare server leftover", "server description", "400",
         f"{SPEC}#server-object", "server.description documents the target, leftover bare url fails closed.",
         f"{SPEC}#oasServers", "Exclusive server desc 400 leftover bare."),
        ("oas-path-item-summary-req", "leftover-path-no-summary", "summary", "path no summary leftover", "pathItem summary", "400",
         f"{SPEC}#path-item-object", "pathItem.summary is not leftover unnamed paths.",
         f"{SPEC}#paths-object", "Exclusive path summary 400 leftover none."),
        ("oas-pathitem-desc-required", "leftover-path-no-desc", "description", "path no desc leftover", "pathItem description", "400",
         f"{SPEC}#path-item-object", "pathItem.description documents the resource, leftover missing fails closed.",
         f"{SPEC}#paths-object", "Exclusive path desc 400 leftover none."),
        ("oas-operation-tags-nonempty", "leftover-untagged-operation", "tags", "untagged leftover", "operation tags nonempty", "400",
         f"{SPEC}#operation-object", "operation.tags must be nonempty, leftover untagged fails closed.",
         f"{SPEC}#tag-object", "Exclusive op tags 400 leftover untagged."),
        ("oas-jsonschema-examples-arr", "leftover-single-example-only", "examples", "single example leftover", "schema examples array", "400",
         f"{JS}/generic#annotation", "JSON Schema examples is an array, leftover single example fails closed.",
         f"{SPEC}#schema-object", "Exclusive examples array 400 leftover single."),
        ("oas-schema-not-keyword", "leftover-enum-exclusion", "not", "enum exclusion leftover", "schema not", "400",
         f"{JS}/combining#not", "not negates a schema, leftover enum-exclusion is not that.",
         f"{SPEC}#schema-object", "Exclusive not 400 leftover enum exclusion."),
        ("oas-media-schema-required", "leftover-schemaless-media", "schema", "schemaless media leftover", "media schema required", "400",
         f"{SPEC}#media-type-object", "media.schema is required, leftover schemaless fails closed.",
         f"{SPEC}#schema-object", "Exclusive media schema 400 leftover schemaless."),
        ("oas-header-schema-required", "leftover-header-no-schema", "schema", "header no schema leftover", "header schema required", "400",
         f"{SPEC}#header-object", "header.schema or content is required, leftover untyped fails closed.",
         f"{SPEC}#parameter-object", "Exclusive header schema 400 leftover untyped."),
        ("oas-parameter-schema-or-content", "leftover-bare-parameter", "schema", "bare parameter leftover", "parameter schema or content", "400",
         f"{SPEC}#parameter-object", "A parameter needs schema or content, leftover bare fails closed.",
         f"{SPEC}#media-type-object", "Exclusive param schema 400 leftover bare."),
    ],
    4278: [
        ("oas-xml-name-override-elem", "leftover-json-key-as-xml", "name", "json key xml leftover", "xml name override", "415",
         f"{SPEC}#xml-object", "xml.name overrides the JSON key, leftover key-as-xml fails closed.",
         f"{SPEC}#schema-object", "Exclusive xml name 415 leftover json key."),
        ("oas-discriminator-property", "leftover-implicit-type-field", "propertyName", "implicit type leftover", "discriminator propertyName", "400",
         f"{SPEC}#discriminator-object", "propertyName is required, leftover implicit type fields fail closed.",
         f"{SPEC}#schema-object", "Exclusive discriminator 400 leftover implicit."),
        ("oas-encoding-content-type-xml", "leftover-json-part-as-xml", "contentType", "json part xml leftover", "encoding contentType xml", "415",
         f"{SPEC}#encoding-object", "encoding.contentType xml is not leftover JSON parts labeled xml.",
         f"{SPEC}#media-type-object", "Exclusive encoding xml 415 leftover json part."),
        ("oas-callback-runtime-expr", "leftover-fixed-callback-href", "expression", "fixed callback leftover", "callback runtime expr", "400",
         f"{SPEC}#callback-object", "Callback keys are runtime expressions, leftover fixed hrefs fail closed.",
         f"{SPEC}#runtime-expressions", "Exclusive callback expr 400 leftover fixed href."),
        ("oas-webhook-path-item-post", "leftover-webhook-get-only", "post", "webhook GET leftover", "webhook POST pathItem", "400",
         f"{SPEC}#oasWebhooks", "Webhook path items typically POST, leftover GET-only fails closed.",
         f"{SPEC}#path-item-object", "Exclusive webhook POST 400 leftover GET."),
        ("oas-components-responses-ref", "leftover-inline-response-only", "responses", "inline response leftover", "components responses ref", "400",
         f"{SPEC}#components-object", "components.responses reuse, leftover inline-only is not that.",
         f"{SPEC}#response-object", "Exclusive components responses 400 leftover inline."),
        ("oas-security-empty-optional", "leftover-always-require-auth", "security", "always auth leftover", "empty security optional", "401",
         f"{SPEC}#security-requirement-object", "Empty security makes the op optional-auth, leftover always-require fails closed.",
         f"{SPEC}#operation-object", "Exclusive optional security 401 leftover always auth."),
        ("oas-api-key-cookie-name", "leftover-api-key-header-only", "in", "header apikey leftover", "apiKey cookie name", "401",
         f"{SPEC}#security-scheme-object", "apiKey in cookie is not leftover header-only keys.",
         f"{SPEC}#security-requirement-object", "Exclusive cookie apikey 401 leftover header."),
        ("oas-format-uriref-relative", "leftover-absolute-uri-only", "format", "absolute uri leftover", "format uri-reference", "400",
         f"{JS}/string#resource-identifiers", "format=uri-reference allows relative, leftover absolute-only fails closed.",
         f"{RFC}/rfc3986", "Exclusive uri-reference 400 leftover absolute."),
        ("oas-format-idn-hostname", "leftover-ascii-hostname-only", "format", "ascii hostname leftover", "format idn-hostname", "400",
         f"{JS}/string#idn-hostname", "idn-hostname is U-label, leftover ASCII-only fails closed.",
         f"{SPEC}#data-types", "Exclusive idn-hostname 400 leftover ascii."),
        ("oas-format-ipv4-strict", "leftover-dotted-quad-string", "format", "dotted quad leftover", "format ipv4", "400",
         f"{JS}/string#ipv4", "format=ipv4 is RFC2673, leftover dotted strings fail closed.",
         f"{SPEC}#data-types", "Exclusive ipv4 400 leftover dotted quad."),
        ("oas-schema-pattern-js", "leftover-posix-ere", "pattern", "posix ere leftover", "ECMA pattern", "400",
         f"{JS}/regular_expressions", "pattern is ECMA-262, leftover POSIX ERE fails closed.",
         f"{SPEC}#schema-object", "Exclusive ECMA pattern 400 leftover POSIX."),
        ("oas-additional-properties-false", "leftover-ignore-unknown-keys", "additionalProperties", "ignore unknown leftover", "additionalProperties false", "400",
         f"{JS}/object#additionalproperties", "additionalProperties false rejects unknown keys, leftover ignore fails closed.",
         f"{SPEC}#schema-object", "Exclusive additionalProperties false 400 leftover ignore."),
        ("oas-schema-contains-item", "leftover-unvalidated-array-elem", "contains", "unvalidated elem leftover", "schema contains", "400",
         f"{JS}/array#contains", "contains validates at least one item, leftover unvalidated fails closed.",
         f"{SPEC}#schema-object", "Exclusive contains 400 leftover unvalidated."),
        ("oas-unique-items-true", "leftover-duplicate-array-ok", "uniqueItems", "duplicate array leftover", "uniqueItems true", "400",
         f"{JS}/array#uniqueitems", "uniqueItems true rejects duplicates, leftover duplicates fail closed.",
         f"{SPEC}#schema-object", "Exclusive uniqueItems 400 leftover dups."),
        ("oas-operation-callbacks-map", "leftover-poll-instead-callback", "callbacks", "poll leftover", "operation callbacks map", "400",
         f"{SPEC}#operation-object", "operation.callbacks is not leftover client polling.",
         f"{SPEC}#callback-object", "Exclusive callbacks 400 leftover poll."),
    ],
    4294: [
        ("oas-schema-default-typed", "leftover-default-wrong-type", "default", "wrong type default leftover", "typed default", "400",
         f"{JS}/generic#annotation", "default must match the schema type, leftover wrong-type fails closed.",
         f"{SPEC}#schema-object", "Exclusive typed default 400 leftover wrong type."),
        ("oas-op-summary-required", "leftover-opid-as-summary", "summary", "opid as summary leftover", "operation summary", "400",
         f"{SPEC}#operation-object", "summary is human text, leftover operationId-as-summary fails closed.",
         f"{SPEC}#path-item-object", "Exclusive op summary 400 leftover opid."),
        ("oas-parameter-desc-required", "leftover-undocumented-param", "description", "undocumented param leftover", "parameter description", "400",
         f"{SPEC}#parameter-object", "parameter.description is required here, leftover undocumented fails closed.",
         f"{SPEC}#operation-object", "Exclusive param desc 400 leftover undocumented."),
        ("oas-request-body-description", "leftover-body-no-desc", "description", "body no desc leftover", "requestBody description", "400",
         f"{SPEC}#request-body-object", "requestBody.description documents the payload, leftover missing fails closed.",
         f"{SPEC}#media-type-object", "Exclusive body desc 400 leftover none."),
        ("oas-format-time-rfc3339", "leftover-hhmm-time", "format", "hhmm time leftover", "format time rfc3339", "400",
         f"{JS}/string#dates-and-times", "format=time is RFC3339, leftover HHMM fails closed.",
         f"{RFC}/rfc3339", "Exclusive time 400 leftover hhmm."),
        ("oas-format-date-rfc3339", "leftover-us-slash-date", "format", "us slash date leftover", "format date rfc3339", "400",
         f"{JS}/string#dates-and-times", "format=date is full-date, leftover US slashes fail closed.",
         f"{RFC}/rfc3339", "Exclusive date 400 leftover us slash."),
        ("oas-schema-min-items-n", "leftover-empty-array-ok", "minItems", "empty array leftover", "minItems", "400",
         f"{JS}/array#minitems", "minItems rejects empty arrays, leftover empty-ok fails closed.",
         f"{SPEC}#schema-object", "Exclusive minItems 400 leftover empty array."),
        ("oas-schema-max-items-n", "leftover-unbounded-array-len", "maxItems", "unbounded array leftover", "maxItems", "400",
         f"{JS}/array#maxitems", "maxItems bounds arrays, leftover unbounded fails closed.",
         f"{SPEC}#schema-object", "Exclusive maxItems 400 leftover unbounded."),
        ("oas-xml-wrapped-array-true", "leftover-xml-array-unwrapped", "wrapped", "unwrapped xml leftover", "xml wrapped true", "415",
         f"{SPEC}#xml-object", "xml.wrapped true wraps arrays, leftover unwrapped fails closed.",
         f"{SPEC}#schema-object", "Exclusive xml wrapped 415 leftover unwrapped."),
        ("oas-components-links-reuse", "leftover-inline-link-only", "links", "inline link leftover", "components links reuse", "400",
         f"{SPEC}#components-object", "components.links reuse Link Objects, leftover inline-only is not that.",
         f"{SPEC}#link-object", "Exclusive components links 400 leftover inline."),
        ("oas-op-security-override", "leftover-root-security-only", "security", "root security leftover", "operation security override", "401",
         f"{SPEC}#operation-object", "operation.security overrides root, leftover root-only fails closed.",
         f"{SPEC}#security-requirement-object", "Exclusive op security 401 leftover root."),
        ("oas-header-content-media", "leftover-header-schema-only", "content", "header schema leftover", "header content media", "400",
         f"{SPEC}#header-object", "header.content is mutually exclusive with schema, leftover schema-only fails closed.",
         f"{SPEC}#media-type-object", "Exclusive header content 400 leftover schema."),
        ("oas-cookie-required-true", "leftover-optional-cookie", "required", "optional cookie leftover", "cookie required true", "400",
         f"{SPEC}#parameter-object", "required cookie parameters cannot be leftover optional.",
         f"{SPEC}#header-object", "Exclusive cookie required 400 leftover optional."),
        ("oas-options-method-explicit", "leftover-implicit-options", "options", "implicit OPTIONS leftover", "OPTIONS method", "400",
         f"{SPEC}#path-item-object", "OPTIONS is a distinct operation, leftover implicit fails closed.",
         f"{RFC}/rfc9110#name-options", "Exclusive OPTIONS 400 leftover implicit."),
        ("oas-schema-writeonly-omit-read", "leftover-echo-writeonly-on-read", "writeOnly", "echo writeOnly leftover", "writeOnly omit read", "400",
         f"{SPEC}#schema-object", "writeOnly must be omitted on read, leftover echo fails closed.",
         f"{JS}/object", "Exclusive writeOnly omit 400 leftover echo."),
        ("oas-format-password-mask", "leftover-plaintext-secret", "format", "plaintext secret leftover", "format password", "400",
         f"{SPEC}#data-types", "format=password is a hint to mask, leftover plaintext fails closed.",
         f"{JS}/string", "Exclusive password 400 leftover plaintext."),
    ],
    4310: [
        ("oas-format-byte-rfc4648", "leftover-hex-as-byte", "format", "hex as byte leftover", "format byte rfc4648", "400",
         f"{SPEC}#data-types", "format=byte is base64, leftover hex fails closed.",
         f"{RFC}/rfc4648", "Exclusive byte 400 leftover hex."),
        ("oas-tag-name-unique", "leftover-duplicate-tag-name", "name", "duplicate tag leftover", "unique tag name", "400",
         f"{SPEC}#tag-object", "tag names must be unique, leftover duplicates fail closed.",
         f"{SPEC}#tags", "Exclusive unique tag 400 leftover duplicate."),
        ("oas-servers-https-required", "leftover-plain-http-server", "url", "plain http leftover", "https server url", "400",
         f"{SPEC}#server-object", "Production servers must be https, leftover http fails closed.",
         f"{RFC}/rfc9110", "Exclusive https server 400 leftover http."),
        ("oas-schema-enum-typed", "leftover-enum-untyped", "enum", "untyped enum leftover", "typed enum", "400",
         f"{JS}/generic#enumerated-values", "enum values must match type, leftover untyped fails closed.",
         f"{SPEC}#schema-object", "Exclusive typed enum 400 leftover untyped."),
        ("oas-oneof-with-discriminator", "leftover-oneof-no-disc", "discriminator", "oneof no disc leftover", "oneOf discriminator", "400",
         f"{SPEC}#discriminator-object", "oneOf payloads need a discriminator, leftover none fails closed.",
         f"{JS}/combining#oneof", "Exclusive oneOf disc 400 leftover none."),
        ("oas-link-param-runtime-expr", "leftover-hardcoded-link-param", "parameters", "hardcoded link leftover", "link param runtime expr", "400",
         f"{SPEC}#link-object", "link.parameters use runtime expressions, leftover hardcoded fails closed.",
         f"{SPEC}#runtime-expressions", "Exclusive link expr 400 leftover hardcoded."),
        ("oas-oauth2-client-credentials", "leftover-password-as-clientcreds", "clientCredentials", "password as client leftover", "clientCredentials flow", "401",
         f"{SPEC}#oauth-flows-object", "clientCredentials is not leftover password-as-client.",
         f"{RFC}/rfc6749#section-4.4", "Exclusive client creds 401 leftover password."),
        ("oas-oauth2-refresh-token-url", "leftover-token-url-as-refresh", "refreshUrl", "tokenUrl as refresh leftover", "oauth2 refreshUrl", "401",
         f"{SPEC}#oauth-flow-object", "refreshUrl is distinct from tokenUrl, leftover reuse fails closed.",
         f"{RFC}/rfc6749#section-6", "Exclusive refreshUrl 401 leftover tokenUrl."),
        ("oas-schema-min-contains-n", "leftover-contains-without-min", "minContains", "contains no min leftover", "minContains", "400",
         f"{JS}/array#mincontains", "minContains bounds contains matches, leftover unbounded fails closed.",
         f"{SPEC}#schema-object", "Exclusive minContains 400 leftover no min."),
        ("oas-schema-max-contains-n", "leftover-unlimited-contains", "maxContains", "unlimited contains leftover", "maxContains", "400",
         f"{JS}/array#maxcontains", "maxContains caps contains matches, leftover unlimited fails closed.",
         f"{SPEC}#schema-object", "Exclusive maxContains 400 leftover unlimited."),
        ("oas-dependent-schemas-map", "leftover-if-then-schema", "dependentSchemas", "if-then leftover", "dependentSchemas", "400",
         f"{JS}/conditionals#dependentschemas", "dependentSchemas is not leftover if/then.",
         f"{SPEC}#schema-object", "Exclusive dependentSchemas 400 leftover if-then."),
        ("oas-pattern-properties-map", "leftover-additional-as-pattern", "patternProperties", "additional as pattern leftover", "patternProperties", "400",
         f"{JS}/object#patternproperties", "patternProperties is not leftover additionalProperties.",
         f"{SPEC}#schema-object", "Exclusive patternProperties 400 leftover additional."),
        ("oas-items-false-closed-tuple", "leftover-open-items-schema", "items", "open items leftover", "items false closed tuple", "400",
         f"{JS}/array#items", "items false forbids leftover tuple tails.",
         f"{SPEC}#schema-object", "Exclusive items false 400 leftover open items."),
        ("oas-type-integer-exclusive", "leftover-json-number-as-int", "type", "json number leftover", "type integer exclusive", "400",
         f"{JS}/numeric#integer", "type=integer rejects leftover JSON numbers with fractions.",
         f"{SPEC}#data-types", "Exclusive integer 400 leftover json number."),
        ("oas-format-float-ieee", "leftover-decimal-as-float", "format", "decimal as float leftover", "format float ieee", "400",
         f"{SPEC}#data-types", "format=float is IEEE-754 binary32, leftover decimal fails closed.",
         f"{JS}/numeric", "Exclusive float 400 leftover decimal."),
        ("oas-format-double-ieee", "leftover-float-as-double", "format", "float as double leftover", "format double ieee", "400",
         f"{SPEC}#data-types", "format=double is binary64, leftover float-as-double fails closed.",
         f"{JS}/numeric", "Exclusive double 400 leftover float."),
    ],
    4326: [
        ("oas-schema-comment-keyword", "leftover-description-as-comment", "$comment", "description as comment leftover", "$comment keyword", "400",
         f"{JS}/generic#annotation", "$comment is not leftover description-as-comment.",
         f"{SPEC}#schema-object", "Exclusive $comment 400 leftover description."),
        ("oas-schema-anchor-id", "leftover-name-as-anchor", "$anchor", "name as anchor leftover", "schema $anchor", "400",
         f"{JS}/schema#anchor", "$anchor is a plain name, leftover title-as-anchor fails closed.",
         f"{SPEC}#schema-object", "Exclusive $anchor 400 leftover name."),
        ("oas-vocabulary-required", "leftover-unconstrained-vocab", "$vocabulary", "unconstrained vocab leftover", "$vocabulary required", "400",
         f"{JS}/schema#vocabulary", "$vocabulary declares required vocabs, leftover unconstrained fails closed.",
         f"{SPEC}#schema-object", "Exclusive $vocabulary 400 leftover unconstrained."),
        ("oas-format-uri-template-expr", "leftover-printf-url-template", "format", "printf url leftover", "format uri-template", "400",
         f"{JS}/string#resource-identifiers", "format=uri-template is RFC6570, leftover sprintf fails closed.",
         f"{RFC}/rfc6570", "Exclusive uri-template 400 leftover sprintf."),
        ("oas-relative-json-pointer", "leftover-absolute-pointer-only", "format", "absolute pointer leftover", "relative json pointer", "400",
         f"{JS}/string#json-pointer", "relative JSON pointer is not leftover absolute-only pointers.",
         f"{RFC}/rfc6901", "Exclusive relative pointer 400 leftover absolute."),
        ("oas-format-iri-absolute", "leftover-uri-as-iri", "format", "uri as iri leftover", "format iri", "400",
         f"{JS}/string#resource-identifiers", "format=iri is RFC3987, leftover URI-as-IRI fails closed.",
         f"{SPEC}#data-types", "Exclusive iri 400 leftover uri."),
        ("oas-format-duration-iso8601", "leftover-seconds-int-duration", "format", "seconds int leftover", "format duration iso8601", "400",
         f"{JS}/string#dates-and-times", "format=duration is ISO8601, leftover integer seconds fail closed.",
         f"{SPEC}#data-types", "Exclusive duration 400 leftover seconds."),
        ("oas-format-ipv6-strict", "leftover-ipv4-mapped-ipv6", "format", "v4 mapped leftover", "format ipv6", "400",
         f"{JS}/string#ipv6", "format=ipv6 is RFC4291, leftover v4-mapped fails closed.",
         f"{SPEC}#data-types", "Exclusive ipv6 400 leftover v4-mapped."),
        ("oas-format-hostname-ldh", "leftover-underscore-hostname", "format", "underscore host leftover", "format hostname ldh", "400",
         f"{JS}/string#hostname", "format=hostname is LDH labels, leftover underscores fail closed.",
         f"{SPEC}#data-types", "Exclusive hostname 400 leftover underscore."),
        ("oas-parameter-style-matrix-explode", "leftover-semicolon-path-csv", "style", "semicolon csv leftover", "matrix explode path", "400",
         f"{SPEC}#style-values", "style=matrix explode is not leftover semicolon csv.",
         f"{SPEC}#parameter-object", "Exclusive matrix explode 400 leftover semicolon csv."),
        ("oas-parameter-style-label-explode", "leftover-dot-path-csv", "style", "dot csv leftover", "label explode path", "400",
         f"{SPEC}#style-values", "style=label explode is not leftover dot csv.",
         f"{SPEC}#parameter-object", "Exclusive label explode 400 leftover dot csv."),
        ("oas-cookie-style-form-explode", "leftover-cookie-csv", "style", "cookie csv leftover", "cookie form explode", "400",
         f"{SPEC}#style-values", "cookie style=form explode is not leftover cookie csv.",
         f"{SPEC}#parameter-object", "Exclusive cookie explode 400 leftover csv."),
        ("oas-header-style-simple-explode", "leftover-header-csv", "style", "header csv leftover", "header simple explode", "400",
         f"{SPEC}#style-values", "header style=simple explode is not leftover header csv.",
         f"{SPEC}#header-object", "Exclusive header explode 400 leftover csv."),
        ("oas-deepobject-query-explode", "leftover-bracket-query", "style", "bracket query leftover", "deepObject explode", "400",
         f"{SPEC}#style-values", "deepObject explode is not leftover bracket query.",
         f"{SPEC}#parameter-object", "Exclusive deepObject 400 leftover bracket."),
        ("oas-query-form-explode-true", "leftover-query-repeated-csv", "explode", "repeated csv leftover", "query form explode true", "400",
         f"{SPEC}#style-values", "form explode true repeats keys, leftover csv fails closed.",
         f"{SPEC}#parameter-object", "Exclusive form explode 400 leftover repeated csv."),
        ("oas-response-304-no-body", "leftover-304-with-body", "content", "304 body leftover", "304 no body", "400",
         f"{SPEC}#response-object", "304 MUST NOT include a body, leftover bodies fail closed.",
         f"{RFC}/rfc9110#name-304-not-modified", "Exclusive 304 empty 400 leftover body."),
    ],
    4342: [
        ("oas-webhook-servers-item", "leftover-webhook-root-server-only", "servers", "root webhook leftover", "webhook servers", "400",
         f"{SPEC}#oasWebhooks", "webhook servers override root, leftover root-only fails closed.",
         f"{SPEC}#server-object", "Exclusive webhook servers 400 leftover root."),
        ("oas-operation-external-docs-url", "leftover-op-no-external-docs", "externalDocs", "op no docs leftover", "operation externalDocs", "400",
         f"{SPEC}#operation-object", "operation.externalDocs.url is required when present, leftover missing fails closed.",
         f"{SPEC}#external-documentation-object", "Exclusive op docs 400 leftover none."),
        ("oas-tag-external-docs-url", "leftover-tag-no-docs", "externalDocs", "tag no docs leftover", "tag externalDocs", "400",
         f"{SPEC}#tag-object", "tag.externalDocs.url is required when present, leftover missing fails closed.",
         f"{SPEC}#external-documentation-object", "Exclusive tag docs 400 leftover none."),
        ("oas-info-license-url-https", "leftover-license-http-url", "url", "http license leftover", "license url https", "400",
         f"{SPEC}#license-object", "license.url must be https, leftover http fails closed.",
         f"{SPEC}#info-object", "Exclusive license https 400 leftover http."),
        ("oas-contact-url-https", "leftover-contact-http-url", "url", "http contact leftover", "contact url https", "400",
         f"{SPEC}#contact-object", "contact.url must be https, leftover http fails closed.",
         f"{SPEC}#info-object", "Exclusive contact https 400 leftover http."),
        ("oas-schema-title-nonempty", "leftover-schema-missing-title", "title", "untitled leftover", "schema title nonempty", "400",
         f"{JS}/generic#annotation", "title must be nonempty, leftover untitled fails closed.",
         f"{SPEC}#schema-object", "Exclusive title 400 leftover untitled."),
        ("oas-xml-attr-flag-true", "leftover-xml-element-only", "attribute", "element only leftover", "xml attribute true", "415",
         f"{SPEC}#xml-object", "xml.attribute true is not leftover element-only mapping.",
         f"{SPEC}#schema-object", "Exclusive xml attribute 415 leftover element."),
        ("oas-xml-wrapped-flag-false", "leftover-always-wrap-xml", "wrapped", "always wrap leftover", "xml wrapped false", "415",
         f"{SPEC}#xml-object", "xml.wrapped false is not leftover always-wrap.",
         f"{SPEC}#schema-object", "Exclusive wrapped false 415 leftover always wrap."),
        ("oas-security-api-key-query", "leftover-api-key-header-forced", "in", "header forced leftover", "apiKey in query", "401",
         f"{SPEC}#security-scheme-object", "apiKey in query is not leftover header-forced keys.",
         f"{SPEC}#security-requirement-object", "Exclusive query apikey 401 leftover header."),
        ("oas-oauth2-auth-code-pkce", "leftover-auth-code-no-pkce", "authorizationCode", "no pkce leftover", "auth code PKCE", "401",
         f"{SPEC}#oauth-flow-object", "authorizationCode with PKCE is not leftover code without PKCE.",
         f"{RFC}/rfc7636", "Exclusive PKCE 401 leftover no pkce."),
        ("oas-openid-connect-url-https", "leftover-oidc-discovery-http", "openIdConnectUrl", "http discovery leftover", "OIDC url https", "401",
         f"{SPEC}#security-scheme-object", "openIdConnectUrl must be https, leftover http fails closed.",
         f"{RFC}/rfc8414", "Exclusive OIDC https 401 leftover http."),
        ("oas-mutualtls-required-op", "leftover-optional-client-cert", "mutualTLS", "optional cert leftover", "mutualTLS required", "401",
         f"{SPEC}#security-scheme-object", "mutualTLS required is not leftover optional client cert.",
         f"{SPEC}#security-requirement-object", "Exclusive mutualTLS 401 leftover optional cert."),
        ("oas-components-path-items-ref", "leftover-inline-path-item", "pathItems", "inline path leftover", "components pathItems ref", "400",
         f"{SPEC}#components-object", "components.pathItems reuse, leftover inline-only is not that.",
         f"{SPEC}#path-item-object", "Exclusive pathItems 400 leftover inline."),
        ("oas-request-body-required-true", "leftover-optional-json-body", "required", "optional body leftover", "requestBody required true", "400",
         f"{SPEC}#request-body-object", "required true rejects leftover optional JSON bodies.",
         f"{SPEC}#operation-object", "Exclusive required body 400 leftover optional."),
        ("oas-encoding-headers-required", "leftover-multipart-part-no-hdr", "headers", "part no headers leftover", "encoding headers required", "415",
         f"{SPEC}#encoding-object", "encoding.headers are required here, leftover missing fails closed.",
         f"{SPEC}#header-object", "Exclusive encoding headers 415 leftover none."),
        ("oas-callback-expression-header", "leftover-callback-path-only", "expression", "path only leftover", "callback header expr", "400",
         f"{SPEC}#runtime-expressions", "Callback expressions may use headers, leftover path-only fails closed.",
         f"{SPEC}#callback-object", "Exclusive header expr 400 leftover path only."),
    ],
    4358: [
        ("oas-schema-content-encoding-b64", "leftover-raw-unicode-blob", "contentEncoding", "raw unicode leftover", "contentEncoding base64", "415",
         f"{JS}/non_json_data#contentencoding", "contentEncoding base64 is not leftover raw unicode blobs.",
         f"{SPEC}#data-types", "Exclusive contentEncoding 415 leftover raw unicode."),
        ("oas-schema-content-schema-ref", "leftover-untyped-encoded-payload", "contentSchema", "untyped encoded leftover", "contentSchema ref", "400",
         f"{JS}/non_json_data#contentschema", "contentSchema validates decoded payload, leftover untyped fails closed.",
         f"{SPEC}#schema-object", "Exclusive contentSchema 400 leftover untyped."),
        ("oas-schema-dynamic-ref", "leftover-static-ref-only", "$dynamicRef", "static ref leftover", "$dynamicRef", "400",
         f"{JS}/schema#dynamic-references", "$dynamicRef is not leftover static $ref only.",
         f"{SPEC}#schema-object", "Exclusive $dynamicRef 400 leftover static ref."),
        ("oas-schema-defs-reuse", "leftover-inline-subschema-only", "$defs", "inline subschema leftover", "$defs reuse", "400",
         f"{JS}/schema#defs", "$defs reuses subschemas, leftover inline-only fails closed.",
         f"{SPEC}#schema-object", "Exclusive $defs 400 leftover inline."),
        ("oas-dependent-required-keys", "leftover-manual-required-pair", "dependentRequired", "manual required leftover", "dependentRequired keys", "400",
         f"{JS}/object#dependentrequired", "dependentRequired pairs keys, leftover manual required fails closed.",
         f"{SPEC}#schema-object", "Exclusive dependentRequired 400 leftover manual."),
        ("oas-info-ver-semver", "leftover-freeform-version", "version", "freeform version leftover", "semver info version", "400",
         f"{SPEC}#info-object", "info.version should be semver, leftover freeform fails closed.",
         f"{SPEC}#openapi-object", "Exclusive semver 400 leftover freeform."),
        ("oas-root-openapi-31", "leftover-openapi-30-root", "openapi", "openapi 3.0 leftover", "openapi 3.1 root", "400",
         f"{SPEC}#versions", "openapi 3.1.0 is not leftover 3.0.3 root.",
         f"{SPEC}#openapi-object", "Exclusive 3.1 400 leftover 3.0."),
        ("oas-paths-nonempty-root", "leftover-empty-paths-map", "paths", "empty paths leftover", "nonempty paths", "400",
         f"{SPEC}#paths-object", "paths must be nonempty, leftover empty map fails closed.",
         f"{SPEC}#openapi-object", "Exclusive nonempty paths 400 leftover empty."),
        ("oas-opid-globally-unique", "leftover-repeated-opid", "operationId", "repeated opid leftover", "globally unique operationId", "400",
         f"{SPEC}#operation-object", "operationId must be unique, leftover repeats fail closed.",
         f"{SPEC}#paths-object", "Exclusive unique opid 400 leftover repeat."),
        ("oas-parameter-name-required", "leftover-anonymous-param", "name", "anonymous param leftover", "parameter name required", "400",
         f"{SPEC}#parameter-object", "parameter.name is required, leftover anonymous fails closed.",
         f"{SPEC}#operation-object", "Exclusive param name 400 leftover anonymous."),
        ("oas-in-path-required", "leftover-path-param-optional", "required", "optional path leftover", "path param required", "400",
         f"{SPEC}#parameter-object", "Path parameters are always required, leftover optional fails closed.",
         f"{SPEC}#path-templating", "Exclusive path required 400 leftover optional."),
        ("oas-path-template-bind", "leftover-unbound-path-param", "name", "unbound path leftover", "path template bind", "400",
         f"{SPEC}#path-templating", "Path template params must bind, leftover unbound fails closed.",
         f"{SPEC}#paths-object", "Exclusive path bind 400 leftover unbound."),
        ("oas-http-bearer-jwt", "leftover-opaque-bearer-token", "bearerFormat", "opaque bearer leftover", "bearerFormat JWT", "401",
         f"{SPEC}#security-scheme-object", "bearerFormat JWT is not leftover opaque tokens.",
         f"{RFC}/rfc7519", "Exclusive JWT bearer 401 leftover opaque."),
        ("oas-oauth2-implicit-banned", "leftover-implicit-hash-token", "implicit", "implicit hash leftover", "implicit flow banned", "401",
         f"{SPEC}#oauth-flows-object", "Implicit flow is banned here, leftover hash tokens fail closed.",
         f"{RFC}/rfc6749#section-4.2", "Exclusive implicit ban 401 leftover hash."),
        ("oas-response-headers-map", "leftover-headers-in-body", "headers", "headers in body leftover", "response headers map", "400",
         f"{SPEC}#response-object", "response.headers is not leftover headers-in-body.",
         f"{SPEC}#header-object", "Exclusive response headers 400 leftover body."),
        ("oas-object-required-keys", "leftover-all-optional-object", "required", "all optional leftover", "object required keys", "400",
         f"{JS}/object#required-properties", "required keys must be present, leftover all-optional fails closed.",
         f"{SPEC}#schema-object", "Exclusive required keys 400 leftover all optional."),
    ],
    4374: [
        ("oas-schema-min-length-str", "leftover-empty-str-ok", "minLength", "empty str leftover", "minLength string", "400",
         f"{JS}/string#length", "minLength rejects empty strings, leftover empty-ok fails closed.",
         f"{SPEC}#schema-object", "Exclusive minLength 400 leftover empty str."),
        ("oas-schema-max-length-str", "leftover-unbounded-str-len", "maxLength", "unbounded str leftover", "maxLength string", "400",
         f"{JS}/string#length", "maxLength bounds strings, leftover unbounded fails closed.",
         f"{SPEC}#schema-object", "Exclusive maxLength 400 leftover unbounded str."),
        ("oas-schema-multiple-of-n", "leftover-any-number-step", "multipleOf", "any step leftover", "multipleOf", "400",
         f"{JS}/numeric#multiples", "multipleOf constrains steps, leftover any-step fails closed.",
         f"{SPEC}#schema-object", "Exclusive multipleOf 400 leftover any step."),
        ("oas-exclusive-max-number", "leftover-exclusive-max-boolean", "exclusiveMaximum", "boolean exclusiveMaximum leftover", "numeric exclusiveMaximum", "400",
         f"{JS}/numeric#exclusivemaximum", "exclusiveMaximum is a number, leftover OAS 3.0 boolean fails closed.",
         f"{SPEC}#data-types", "Exclusive numeric exclusiveMaximum 400 leftover boolean."),
        ("oas-type-array-items-req", "leftover-untyped-array-elem", "items", "untyped array leftover", "array items required", "400",
         f"{JS}/array#items", "array items schema is required, leftover untyped fails closed.",
         f"{SPEC}#schema-object", "Exclusive array items 400 leftover untyped."),
        ("oas-examples-example-mutex", "leftover-both-example-keys", "examples", "both example keys leftover", "example xor examples", "400",
         f"{SPEC}#media-type-object", "example and examples are mutually exclusive, leftover both fails closed.",
         f"{SPEC}#example-object", "Exclusive xor 400 leftover both keys."),
        ("oas-components-params-ref", "leftover-inline-param-only", "parameters", "inline param leftover", "components parameters ref", "400",
         f"{SPEC}#components-object", "components.parameters reuse, leftover inline-only is not that.",
         f"{SPEC}#parameter-object", "Exclusive components params 400 leftover inline."),
        ("oas-components-headers-ref", "leftover-inline-header-only", "headers", "inline header leftover", "components headers ref", "400",
         f"{SPEC}#components-object", "components.headers reuse, leftover inline-only is not that.",
         f"{SPEC}#header-object", "Exclusive components headers 400 leftover inline."),
        ("oas-path-item-dollar-ref", "leftover-duplicated-path-item", "$ref", "duplicated path leftover", "pathItem $ref", "400",
         f"{SPEC}#path-item-object", "Path Item $ref reuses paths, leftover duplicates fail closed.",
         f"{SPEC}#paths-object", "Exclusive path $ref 400 leftover duplicate."),
        ("oas-trace-method-disabled", "leftover-trace-enabled", "trace", "TRACE enabled leftover", "TRACE disabled", "400",
         f"{SPEC}#path-item-object", "TRACE is disabled here, leftover TRACE fails closed.",
         f"{RFC}/rfc9110#name-trace", "Exclusive TRACE off 400 leftover enabled."),
        ("oas-connect-method-absent", "leftover-connect-tunnel", "connect", "CONNECT leftover", "CONNECT absent", "400",
         f"{SPEC}#path-item-object", "CONNECT is not an OAS method, leftover CONNECT fails closed.",
         f"{RFC}/rfc9110#name-connect", "Exclusive CONNECT absent 400 leftover tunnel."),
        ("oas-tag-desc-nonempty", "leftover-tag-without-desc", "description", "tag name only leftover", "tag description nonempty", "400",
         f"{SPEC}#tag-object", "tag.description must be nonempty, leftover name-only fails closed.",
         f"{SPEC}#tags", "Exclusive tag desc 400 leftover name only."),
        ("oas-external-docs-https", "leftover-docs-relative-url", "url", "relative docs leftover", "externalDocs https", "400",
         f"{SPEC}#external-documentation-object", "externalDocs.url must be https, leftover relative fails closed.",
         f"{SPEC}#openapi-object", "Exclusive docs https 400 leftover relative."),
        ("oas-callback-servers-item", "leftover-callback-root-server", "servers", "callback root leftover", "callback servers", "400",
         f"{SPEC}#callback-object", "callback servers override root, leftover root-only fails closed.",
         f"{SPEC}#server-object", "Exclusive callback servers 400 leftover root."),
        ("oas-oauth2-scopes-object", "leftover-scope-csv-string", "scopes", "scope csv leftover", "oauth2 scopes object", "401",
         f"{SPEC}#oauth-flow-object", "scopes is a map, leftover csv string fails closed.",
         f"{RFC}/rfc6749", "Exclusive scopes map 401 leftover csv."),
        ("oas-digest-http-auth", "leftover-basic-as-digest-auth", "scheme", "basic as digest leftover", "HTTP digest", "401",
         f"{SPEC}#security-scheme-object", "HTTP digest is not leftover basic-as-digest.",
         f"{RFC}/rfc7616", "Exclusive digest 401 leftover basic."),
    ],
    4390: [
        ("oas-prefixitems-plus-items", "leftover-tuple-as-open-list", "prefixItems", "open list leftover", "prefixItems plus items", "400",
         f"{JS}/array#tuple-validation", "prefixItems plus items closes leftover open lists.",
         f"{SPEC}#schema-object", "Exclusive prefixItems+items 400 leftover open list."),
        ("oas-property-names-pattern", "leftover-any-key-charset", "propertyNames", "any key charset leftover", "propertyNames pattern", "400",
         f"{JS}/object#propertynames", "propertyNames.pattern constrains keys, leftover any-charset fails closed.",
         f"{SPEC}#schema-object", "Exclusive propertyNames pattern 400 leftover any charset."),
        ("oas-default-const-agree", "leftover-default-vs-const", "default", "default vs const leftover", "default agrees const", "400",
         f"{JS}/generic#const", "default must agree with const, leftover mismatch fails closed.",
         f"{SPEC}#schema-object", "Exclusive default=const 400 leftover mismatch."),
        ("oas-schema-else-branch", "leftover-if-then-no-else", "else", "if-then no else leftover", "if then else", "400",
         f"{JS}/conditionals", "else is required with if/then here, leftover missing else fails closed.",
         f"{SPEC}#schema-object", "Exclusive else 400 leftover no else."),
        ("oas-webhook-header-param", "leftover-webhook-query-only", "parameters", "webhook query leftover", "webhook header param", "400",
         f"{SPEC}#oasWebhooks", "Webhook header params are not leftover query-only.",
         f"{SPEC}#parameter-object", "Exclusive webhook header 400 leftover query."),
        ("oas-callback-put-op", "leftover-callback-post-only", "put", "callback POST leftover", "callback PUT", "400",
         f"{SPEC}#callback-object", "Callback PUT is distinct, leftover POST-only fails closed.",
         f"{SPEC}#path-item-object", "Exclusive callback PUT 400 leftover POST."),
        ("oas-link-requestbody-expr", "leftover-link-no-request-body", "requestBody", "link no body leftover", "link requestBody expr", "400",
         f"{SPEC}#link-object", "link.requestBody is a runtime expression, leftover missing fails closed.",
         f"{SPEC}#runtime-expressions", "Exclusive link body 400 leftover none."),
        ("oas-header-required-response", "leftover-resp-header-optional", "required", "optional resp header leftover", "response header required", "400",
         f"{SPEC}#header-object", "required response headers cannot be leftover optional.",
         f"{SPEC}#response-object", "Exclusive header required 400 leftover optional."),
        ("oas-encoding-style-form-part", "leftover-part-as-json-blob", "style", "json part leftover", "encoding style form", "415",
         f"{SPEC}#encoding-object", "encoding.style form is not leftover JSON parts.",
         f"{SPEC}#style-values", "Exclusive encoding form 415 leftover json part."),
        ("oas-encoding-explode-mpart", "leftover-multipart-csv-part", "explode", "multipart csv leftover", "encoding explode multipart", "415",
         f"{SPEC}#encoding-object", "encoding.explode on multipart is not leftover csv parts.",
         f"{SPEC}#media-type-object", "Exclusive encoding explode 415 leftover csv."),
        ("oas-cookie-allow-reserved", "leftover-cookie-percent-all", "allowReserved", "cookie percent leftover", "cookie allowReserved", "400",
         f"{SPEC}#parameter-object", "cookie allowReserved is not leftover percent-all cookies.",
         f"{RFC}/rfc3986", "Exclusive cookie allowReserved 400 leftover percent."),
        ("oas-query-allow-empty-value", "leftover-drop-empty-query-param", "allowEmptyValue", "drop empty leftover", "query allowEmptyValue", "400",
         f"{SPEC}#parameter-object", "allowEmptyValue on query is not leftover drop-empty.",
         f"{SPEC}#style-values", "Exclusive allowEmptyValue 400 leftover drop empty."),
        ("oas-api-key-header-name", "leftover-x-api-key-query", "in", "query apikey leftover", "apiKey header name", "401",
         f"{SPEC}#security-scheme-object", "apiKey in header is not leftover query x-api-key.",
         f"{SPEC}#security-requirement-object", "Exclusive header apikey 401 leftover query."),
        ("oas-negotiate-http-auth", "leftover-ntlm-auth-header", "scheme", "ntlm leftover", "HTTP Negotiate", "401",
         f"{SPEC}#security-scheme-object", "HTTP Negotiate is not leftover NTLM headers.",
         f"{RFC}/rfc4559", "Exclusive Negotiate 401 leftover NTLM."),
        ("oas-contact-email-rfc5322", "leftover-contact-unformatted", "email", "unformatted contact leftover", "contact email rfc5322", "400",
         f"{SPEC}#contact-object", "contact.email is RFC5322, leftover unformatted fails closed.",
         f"{SPEC}#info-object", "Exclusive contact email 400 leftover unformatted."),
        ("oas-operation-servers-https", "leftover-op-http-server", "servers", "op http leftover", "operation https servers", "400",
         f"{SPEC}#operation-object", "operation.servers must be https, leftover http fails closed.",
         f"{SPEC}#server-object", "Exclusive op https 400 leftover http."),
    ],
    4406: [
        ("oas-schema-read-only-flag", "leftover-writable-identifier", "readOnly", "writable id leftover", "readOnly true", "400",
         f"{SPEC}#schema-object", "readOnly identifiers cannot be leftover writable.",
         f"{JS}/object", "Exclusive readOnly 400 leftover writable id."),
        ("oas-schema-write-only-flag", "leftover-readable-secret-field", "writeOnly", "readable secret leftover", "writeOnly true", "400",
         f"{SPEC}#schema-object", "writeOnly secrets cannot be leftover readable.",
         f"{JS}/object", "Exclusive writeOnly 400 leftover readable secret."),
        ("oas-format-binary-octet", "leftover-utf8-as-binary", "format", "utf8 as binary leftover", "format binary octet", "415",
         f"{SPEC}#data-types", "format=binary is octets, leftover utf8 fails closed.",
         f"{SPEC}#schema-object", "Exclusive binary 415 leftover utf8."),
        ("oas-format-int32-range", "leftover-int32-overflow", "format", "int32 overflow leftover", "format int32 range", "400",
         f"{SPEC}#data-types", "int32 must fit 32-bit, leftover overflow fails closed.",
         f"{JS}/numeric", "Exclusive int32 range 400 leftover overflow."),
        ("oas-format-int64-string", "leftover-int64-as-js-number", "format", "js number int64 leftover", "int64 as string", "400",
         f"{SPEC}#data-types", "int64 over 2^53 is a string, leftover JS number fails closed.",
         f"{JS}/numeric", "Exclusive int64 string 400 leftover js number."),
        ("oas-param-content-json-header", "leftover-header-as-string-schema", "content", "string header leftover", "header content json", "400",
         f"{SPEC}#parameter-object", "header content json is not leftover string schema headers.",
         f"{SPEC}#media-type-object", "Exclusive header json content 400 leftover string."),
        ("oas-components-examples-value", "leftover-externalvalue-only", "value", "externalValue leftover", "example value", "400",
         f"{SPEC}#example-object", "example.value is not leftover externalValue-only.",
         f"{SPEC}#components-object", "Exclusive example value 400 leftover externalValue."),
        ("oas-security-schemes-ref", "leftover-inline-security-scheme", "securitySchemes", "inline scheme leftover", "components securitySchemes ref", "401",
         f"{SPEC}#components-object", "components.securitySchemes reuse, leftover inline-only is not that.",
         f"{SPEC}#security-scheme-object", "Exclusive securitySchemes 401 leftover inline."),
        ("oas-allof-with-discriminator", "leftover-allof-untyped-merge", "discriminator", "untyped allOf leftover", "allOf discriminator", "400",
         f"{SPEC}#discriminator-object", "allOf plus discriminator is not leftover untyped merge.",
         f"{JS}/combining#allof", "Exclusive allOf disc 400 leftover untyped."),
        ("oas-anyof-null-member", "leftover-anyof-null-only", "anyOf", "anyOf null only leftover", "anyOf includes null", "400",
         f"{JS}/combining#anyof", "anyOf may include null as a member, leftover null-only fails closed.",
         f"{SPEC}#schema-object", "Exclusive anyOf null member 400 leftover null only."),
        ("oas-contains-min-one", "leftover-contains-may-miss", "contains", "contains may miss leftover", "contains min one", "400",
         f"{JS}/array#contains", "contains requires at least one match, leftover miss fails closed.",
         f"{SPEC}#schema-object", "Exclusive contains min one 400 leftover miss."),
        ("oas-unique-contains-items", "leftover-contains-duplicate-ok", "uniqueItems", "contains dups leftover", "unique contains items", "400",
         f"{JS}/array#uniqueitems", "contains matches still honor uniqueItems, leftover dups fail closed.",
         f"{SPEC}#schema-object", "Exclusive unique contains 400 leftover dups."),
        ("oas-dependent-required-xor", "leftover-independent-required", "dependentRequired", "independent required leftover", "dependentRequired xor", "400",
         f"{JS}/object#dependentrequired", "dependentRequired xor pairing is not leftover independent required.",
         f"{SPEC}#schema-object", "Exclusive xor required 400 leftover independent."),
        ("oas-min-properties-one", "leftover-empty-map-ok", "minProperties", "empty map leftover", "minProperties 1", "400",
         f"{JS}/object#minproperties", "minProperties 1 rejects empty maps, leftover empty-ok fails closed.",
         f"{SPEC}#schema-object", "Exclusive minProperties 1 400 leftover empty map."),
        ("oas-max-properties-one", "leftover-multi-key-map", "maxProperties", "multi key leftover", "maxProperties 1", "400",
         f"{JS}/object#maxproperties", "maxProperties 1 rejects multi-key maps, leftover multi fails closed.",
         f"{SPEC}#schema-object", "Exclusive maxProperties 1 400 leftover multi key."),
        ("oas-items-schema-required", "leftover-untyped-list-elem", "items", "untyped list leftover", "items schema required", "400",
         f"{JS}/array#items", "items schema is required for lists, leftover untyped fails closed.",
         f"{SPEC}#schema-object", "Exclusive items schema 400 leftover untyped list."),
    ],
    4422: [
        ("oas-webhook-delete-op", "leftover-webhook-post-forced", "delete", "webhook POST leftover", "webhook DELETE", "400",
         f"{SPEC}#oasWebhooks", "Webhook DELETE is distinct, leftover POST-forced fails closed.",
         f"{SPEC}#path-item-object", "Exclusive webhook DELETE 400 leftover POST."),
        ("oas-path-item-parameters", "leftover-op-params-only", "parameters", "op params leftover", "pathItem parameters", "400",
         f"{SPEC}#path-item-object", "pathItem.parameters apply to all ops, leftover op-only fails closed.",
         f"{SPEC}#parameter-object", "Exclusive path params 400 leftover op only."),
        ("oas-op-parameters-override", "leftover-path-params-only", "parameters", "path params leftover", "operation parameters override", "400",
         f"{SPEC}#operation-object", "operation.parameters override path, leftover path-only fails closed.",
         f"{SPEC}#parameter-object", "Exclusive op params 400 leftover path only."),
        ("oas-response-default-catch", "leftover-no-default-response", "default", "listed status leftover", "response default", "400",
         f"{SPEC}#responses-object", "default catches unlisted statuses, leftover listed-only fails closed.",
         f"{SPEC}#response-object", "Exclusive default response 400 leftover listed."),
        ("oas-status-201-location", "leftover-created-no-location", "headers", "201 no location leftover", "201 Location header", "400",
         f"{SPEC}#response-object", "201 SHOULD include Location, leftover missing fails closed.",
         f"{RFC}/rfc9110#name-201-created", "Exclusive 201 Location 400 leftover none."),
        ("oas-status-202-accepted", "leftover-202-with-entity-body", "content", "202 entity leftover", "202 accepted empty", "400",
         f"{SPEC}#response-object", "202 accepted here has no entity, leftover body fails closed.",
         f"{RFC}/rfc9110#name-202-accepted", "Exclusive 202 empty 400 leftover entity."),
        ("oas-status-409-conflict", "leftover-400-as-conflict", "409", "400 as conflict leftover", "409 conflict", "409",
         f"{SPEC}#responses-object", "409 is conflict, leftover 400-as-conflict fails closed.",
         f"{RFC}/rfc9110#name-409-conflict", "Exclusive 409  leftover 400."),
        ("oas-status-410-gone", "leftover-404-as-gone", "410", "404 as gone leftover", "410 gone", "410",
         f"{SPEC}#responses-object", "410 is gone, leftover 404-as-gone fails closed.",
         f"{RFC}/rfc9110#name-410-gone", "Exclusive 410 leftover 404."),
        ("oas-status-415-unsupported", "leftover-400-as-unsupported", "415", "400 as unsupported leftover", "415 unsupported media", "415",
         f"{SPEC}#responses-object", "415 is unsupported media, leftover 400-as-415 fails closed.",
         f"{RFC}/rfc9110#name-415-unsupported-media-type", "Exclusive 415 leftover 400."),
        ("oas-status-429-problem", "leftover-503-as-ratelimit", "429", "503 as ratelimit leftover", "429 problem details", "429",
         f"{SPEC}#response-object", "429 is rate limit, leftover 503-as-429 fails closed.",
         f"{RFC}/rfc6585#section-4", "Exclusive 429 leftover 503."),
        ("oas-problem-details-json", "leftover-plaintext-error", "content", "plaintext error leftover", "problem+json", "400",
         f"{RFC}/rfc9457", "application/problem+json is not leftover plaintext errors.",
         f"{SPEC}#media-type-object", "Exclusive problem+json 400 leftover plaintext."),
        ("oas-content-type-problem", "leftover-error-as-json-object", "contentType", "json object error leftover", "problem content-type", "400",
         f"{RFC}/rfc9457", "problem+json content-type is not leftover generic JSON errors.",
         f"{SPEC}#media-type-object", "Exclusive problem type 400 leftover json object."),
        ("oas-accept-required-header", "leftover-untyped-accept", "Accept", "untyped Accept leftover", "Accept header required", "400",
         f"{SPEC}#parameter-object", "required Accept header is not leftover untyped Accept.",
         f"{RFC}/rfc9110#name-accept", "Exclusive Accept 400 leftover untyped."),
        ("oas-idempotency-key-header", "leftover-replay-without-key", "Idempotency-Key", "replay leftover", "Idempotency-Key header", "400",
         f"{SPEC}#header-object", "Idempotency-Key is required on write, leftover replay fails closed.",
         f"{SPEC}#operation-object", "Exclusive idempotency key 400 leftover replay."),
        ("oas-etag-response-header", "leftover-no-etag-on-get", "ETag", "no etag leftover", "ETag response header", "400",
         f"{SPEC}#header-object", "GET responses need ETag, leftover missing fails closed.",
         f"{RFC}/rfc9110#name-etag", "Exclusive ETag 400 leftover none."),
        ("oas-if-match-required", "leftover-put-without-if-match", "If-Match", "PUT no If-Match leftover", "If-Match required", "412",
         f"{SPEC}#parameter-object", "PUT requires If-Match, leftover missing fails closed.",
         f"{RFC}/rfc9110#name-if-match", "Exclusive If-Match 412 leftover none."),
    ],
    4438: [
        ("oas-json-merge-patch-media", "leftover-json-patch-as-merge", "contentType", "json patch as merge leftover", "merge-patch+json", "415",
         f"{RFC}/rfc7396", "application/merge-patch+json is not leftover json-patch.",
         f"{SPEC}#media-type-object", "Exclusive merge-patch 415 leftover json-patch."),
        ("oas-json-patch-media", "leftover-merge-as-json-patch", "contentType", "merge as patch leftover", "json-patch+json", "415",
         f"{RFC}/rfc6902", "application/json-patch+json is not leftover merge-patch.",
         f"{SPEC}#media-type-object", "Exclusive json-patch 415 leftover merge."),
        ("oas-multipart-form-data", "leftover-urlencoded-as-multipart", "contentType", "urlencoded as multipart leftover", "multipart form-data", "415",
         f"{SPEC}#media-type-object", "multipart/form-data is not leftover urlencoded.",
         f"{SPEC}#encoding-object", "Exclusive multipart 415 leftover urlencoded."),
        ("oas-urlencoded-form", "leftover-json-as-form", "contentType", "json as form leftover", "urlencoded form", "415",
         f"{SPEC}#media-type-object", "application/x-www-form-urlencoded is not leftover JSON.",
         f"{SPEC}#encoding-object", "Exclusive urlencoded 415 leftover json."),
        ("oas-octet-stream-body", "leftover-base64-in-json-body", "contentType", "base64 json leftover", "octet-stream body", "415",
         f"{SPEC}#media-type-object", "application/octet-stream is not leftover base64-in-JSON.",
         f"{SPEC}#data-types", "Exclusive octet-stream 415 leftover base64 json."),
        ("oas-text-plain-body", "leftover-json-string-as-text", "contentType", "json string leftover", "text/plain body", "415",
         f"{SPEC}#media-type-object", "text/plain is not leftover JSON string bodies.",
         f"{SPEC}#schema-object", "Exclusive text/plain 415 leftover json string."),
        ("oas-xml-app-media", "leftover-text-xml-media", "contentType", "text xml leftover", "application/xml", "415",
         f"{SPEC}#media-type-object", "application/xml is not leftover text/xml.",
         f"{SPEC}#xml-object", "Exclusive application/xml 415 leftover text/xml."),
        ("oas-json-schema-2020-12", "leftover-draft7-schema", "$schema", "draft7 leftover", "JSON Schema 2020-12", "400",
         f"{JS}/schema", "2020-12 dialect is not leftover draft-07.",
         f"{SPEC}#schema-object", "Exclusive 2020-12 400 leftover draft7."),
        ("oas-additional-items-removed", "leftover-additional-items-keyword", "additionalItems", "additionalItems leftover", "additionalItems removed", "400",
         f"{JS}/array#additionalitems", "OAS 3.1 dropped additionalItems, leftover keyword fails closed.",
         f"{SPEC}#schema-object", "Exclusive additionalItems removed 400 leftover keyword."),
        ("oas-nullable-keyword-removed", "leftover-nullable-oas30", "nullable", "nullable oas30 leftover", "nullable removed", "400",
         f"{SPEC}#data-types", "OAS 3.1 removed nullable, leftover keyword fails closed.",
         f"{JS}/null", "Exclusive nullable removed 400 leftover oas30."),
        ("oas-example-vs-examples-param", "leftover-param-both-examples", "examples", "param both leftover", "param example xor examples", "400",
         f"{SPEC}#parameter-object", "parameter example and examples are exclusive, leftover both fails closed.",
         f"{SPEC}#example-object", "Exclusive param xor 400 leftover both."),
        ("oas-style-deepobject-cookie", "leftover-cookie-bracket-keys", "style", "cookie bracket leftover", "cookie deepObject", "400",
         f"{SPEC}#style-values", "deepObject on cookie is not leftover bracket keys.",
         f"{SPEC}#parameter-object", "Exclusive cookie deepObject 400 leftover bracket."),
        ("oas-allowemptyvalue-query", "leftover-query-omit-blank", "allowEmptyValue", "omit blank leftover", "query allowEmptyValue", "400",
         f"{SPEC}#parameter-object", "query allowEmptyValue is not leftover omit-blank.",
         f"{SPEC}#style-values", "Exclusive query empty 400 leftover omit blank."),
        ("oas-header-deprecated-flag", "leftover-live-deprecated-header", "deprecated", "live deprecated leftover", "header deprecated", "400",
         f"{SPEC}#header-object", "deprecated headers must not ship live, leftover still-live fails closed.",
         f"{SPEC}#parameter-object", "Exclusive header deprecated 400 leftover live."),
        ("oas-param-explode-path-false", "leftover-path-explode-true", "explode", "path explode leftover", "path explode false", "400",
         f"{SPEC}#style-values", "path explode false is not leftover explode true.",
         f"{SPEC}#parameter-object", "Exclusive path explode false 400 leftover true."),
        ("oas-server-variable-pattern", "leftover-server-var-unbounded", "pattern", "unbounded server var leftover", "server var pattern", "400",
         f"{SPEC}#server-variable-object", "server variable pattern bounds values, leftover unbounded fails closed.",
         f"{SPEC}#server-object", "Exclusive server pattern 400 leftover unbounded."),
    ],
    4454: [
        ("oas-webhook-trace-absent", "leftover-webhook-trace-enabled", "trace", "webhook TRACE leftover", "webhook TRACE absent", "400",
         f"{SPEC}#oasWebhooks", "Webhook TRACE is absent here, leftover TRACE fails closed.",
         f"{SPEC}#path-item-object", "Exclusive webhook TRACE off 400 leftover enabled."),
        ("oas-components-pathitems-param", "leftover-pathitem-no-params", "parameters", "pathItem no params leftover", "components pathItems params", "400",
         f"{SPEC}#components-object", "Reusable pathItems can carry parameters, leftover none fails closed.",
         f"{SPEC}#path-item-object", "Exclusive pathItems params 400 leftover none."),
        ("oas-security-optional-and-required", "leftover-mixed-security-wrong", "security", "mixed security leftover", "optional and required security", "401",
         f"{SPEC}#security-requirement-object", "Optional {} plus required schemes is not leftover mixed wrong.",
         f"{SPEC}#operation-object", "Exclusive optional+required 401 leftover mixed."),
        ("oas-oauth2-device-code", "leftover-device-as-password", "deviceAuthorization", "device as password leftover", "device code flow", "401",
         f"{RFC}/rfc8628", "Device code flow is not leftover password-as-device.",
         f"{SPEC}#oauth-flows-object", "Exclusive device code 401 leftover password."),
        ("oas-mtls-plus-bearer", "leftover-mtls-only-or-bearer", "security", "mtls xor bearer leftover", "mutualTLS plus bearer", "401",
         f"{SPEC}#security-requirement-object", "AND of mutualTLS plus bearer is not leftover xor.",
         f"{SPEC}#security-scheme-object", "Exclusive mtls+bearer 401 leftover xor."),
        ("oas-api-key-query-name", "leftover-api-key-as-bearer", "in", "apikey as bearer leftover", "apiKey query name", "401",
         f"{SPEC}#security-scheme-object", "apiKey in query is not leftover bearer.",
         f"{SPEC}#security-requirement-object", "Exclusive query apikey 401 leftover bearer."),
        ("oas-cookie-api-key-httponly", "leftover-readable-apikey-cookie", "in", "readable cookie leftover", "HttpOnly apiKey cookie", "401",
         f"{SPEC}#security-scheme-object", "apiKey cookie must be HttpOnly, leftover readable fails closed.",
         f"{SPEC}#parameter-object", "Exclusive HttpOnly cookie 401 leftover readable."),
        ("oas-schema-id-absolute-uri", "leftover-relative-schema-id", "$id", "relative $id leftover", "$id absolute uri", "400",
         f"{JS}/schema#id", "$id should be an absolute URI, leftover relative fails closed.",
         f"{SPEC}#schema-object", "Exclusive absolute $id 400 leftover relative."),
        ("oas-anchor-plain-name", "leftover-anchor-as-pointer", "$anchor", "anchor as pointer leftover", "$anchor plain name", "400",
         f"{JS}/schema#anchor", "$anchor is a plain name, leftover pointer-as-anchor fails closed.",
         f"{SPEC}#schema-object", "Exclusive $anchor name 400 leftover pointer."),
        ("oas-dynamicanchor-scope", "leftover-dynamic-as-static-id", "$dynamicAnchor", "dynamic as static leftover", "$dynamicAnchor scope", "400",
         f"{JS}/schema#dynamic-references", "$dynamicAnchor is dynamic scope, leftover static $id fails closed.",
         f"{SPEC}#schema-object", "Exclusive $dynamicAnchor 400 leftover static."),
        ("oas-vocabulary-boolean-true", "leftover-vocab-ignored", "$vocabulary", "vocab ignored leftover", "$vocabulary true", "400",
         f"{JS}/schema#vocabulary", "$vocabulary true requires the vocab, leftover ignored fails closed.",
         f"{SPEC}#schema-object", "Exclusive $vocabulary true 400 leftover ignored."),
        ("oas-comment-non-validating", "leftover-comment-as-description", "$comment", "comment as description leftover", "$comment non-validating", "400",
         f"{JS}/generic#annotation", "$comment does not validate, leftover description-as-comment fails closed.",
         f"{SPEC}#schema-object", "Exclusive $comment 400 leftover description."),
        ("oas-unevaluated-props-schema", "leftover-additional-as-unevaluated", "unevaluatedProperties", "additional as unevaluated leftover", "unevaluatedProperties schema", "400",
         f"{JS}/object#unevaluatedproperties", "unevaluatedProperties is not leftover additionalProperties.",
         f"{SPEC}#schema-object", "Exclusive unevaluatedProperties 400 leftover additional."),
        ("oas-unevaluated-items-schema", "leftover-items-as-unevaluated", "unevaluatedItems", "items as unevaluated leftover", "unevaluatedItems schema", "400",
         f"{JS}/array#unevaluateditems", "unevaluatedItems is not leftover items.",
         f"{SPEC}#schema-object", "Exclusive unevaluatedItems schema 400 leftover items."),
        ("oas-contains-max-one", "leftover-contains-many-ok", "maxContains", "many contains leftover", "maxContains 1", "400",
         f"{JS}/array#maxcontains", "maxContains 1 rejects many matches, leftover many-ok fails closed.",
         f"{SPEC}#schema-object", "Exclusive maxContains 1 400 leftover many."),
        ("oas-prefixitems-len-match", "leftover-tuple-length-open", "prefixItems", "open tuple leftover", "prefixItems length match", "400",
         f"{JS}/array#tuple-validation", "prefixItems length must match, leftover open length fails closed.",
         f"{SPEC}#schema-object", "Exclusive prefixItems length 400 leftover open."),
    ],
    4470: [
        ("oas-request-body-multipart-enc", "leftover-multipart-no-encoding", "encoding", "multipart no encoding leftover", "multipart encoding map", "415",
         f"{SPEC}#encoding-object", "multipart encoding is required here, leftover missing fails closed.",
         f"{SPEC}#request-body-object", "Exclusive multipart encoding 415 leftover none."),
        ("oas-callback-timeout-hint", "leftover-sync-callback-wait", "timeout", "sync wait leftover", "callback timeout hint", "400",
         f"{SPEC}#callback-object", "Callback timeout is a hint, leftover sync-wait fails closed.",
         f"{SPEC}#operation-object", "Exclusive callback timeout 400 leftover sync wait."),
        ("oas-link-opid-xor-opref", "leftover-link-both-opid-opref", "operationRef", "both opid opref leftover", "operationId xor operationRef", "400",
         f"{SPEC}#link-object", "operationId and operationRef are exclusive, leftover both fails closed.",
         f"{SPEC}#runtime-expressions", "Exclusive xor 400 leftover both."),
        ("oas-response-link-array", "leftover-single-link-only", "links", "single link leftover", "response links map", "400",
         f"{SPEC}#response-object", "links is a map of named links, leftover single-only fails closed.",
         f"{SPEC}#link-object", "Exclusive links map 400 leftover single."),
        ("oas-header-style-simple-path", "leftover-header-form-style", "style", "header form leftover", "header style simple", "400",
         f"{SPEC}#style-values", "headers use style=simple, leftover form fails closed.",
         f"{SPEC}#header-object", "Exclusive header simple 400 leftover form."),
        ("oas-query-style-pipe-delim", "leftover-query-pipe-as-csv", "style", "pipe as csv leftover", "query pipeDelimited", "400",
         f"{SPEC}#style-values", "pipeDelimited query is not leftover csv with pipes.",
         f"{SPEC}#parameter-object", "Exclusive pipeDelimited 400 leftover csv."),
        ("oas-path-style-simple-explode", "leftover-path-comma-no-explode", "explode", "comma no explode leftover", "path simple explode", "400",
         f"{SPEC}#style-values", "path simple explode is not leftover comma without explode.",
         f"{SPEC}#parameter-object", "Exclusive path explode 400 leftover comma."),
        ("oas-matrix-path-no-explode", "leftover-matrix-explode-forced", "explode", "matrix explode leftover", "matrix explode false", "400",
         f"{SPEC}#style-values", "matrix explode false is not leftover explode-forced.",
         f"{SPEC}#parameter-object", "Exclusive matrix no explode 400 leftover forced."),
        ("oas-label-path-no-explode", "leftover-label-explode-forced", "explode", "label explode leftover", "label explode false", "400",
         f"{SPEC}#style-values", "label explode false is not leftover explode-forced.",
         f"{SPEC}#parameter-object", "Exclusive label no explode 400 leftover forced."),
        ("oas-form-query-no-explode", "leftover-form-always-explode", "explode", "always explode leftover", "form explode false", "400",
         f"{SPEC}#style-values", "form explode false is not leftover always-explode.",
         f"{SPEC}#parameter-object", "Exclusive form no explode 400 leftover always."),
        ("oas-space-delim-no-explode", "leftover-space-as-csv", "explode", "space csv leftover", "spaceDelimited no explode", "400",
         f"{SPEC}#style-values", "spaceDelimited explode false is not leftover space-as-csv.",
         f"{SPEC}#parameter-object", "Exclusive space no explode 400 leftover csv."),
        ("oas-pipe-delim-no-explode", "leftover-pipe-as-form", "explode", "pipe as form leftover", "pipeDelimited no explode", "400",
         f"{SPEC}#style-values", "pipeDelimited explode false is not leftover pipe-as-form.",
         f"{SPEC}#parameter-object", "Exclusive pipe no explode 400 leftover form."),
        ("oas-deepobject-requires-explode", "leftover-deepobject-no-explode", "explode", "deepObject no explode leftover", "deepObject explode true", "400",
         f"{SPEC}#style-values", "deepObject requires explode true, leftover false fails closed.",
         f"{SPEC}#parameter-object", "Exclusive deepObject explode 400 leftover false."),
        ("oas-content-param-no-style", "leftover-content-plus-style", "style", "content plus style leftover", "content param no style", "400",
         f"{SPEC}#parameter-object", "content parameters omit style, leftover style fails closed.",
         f"{SPEC}#media-type-object", "Exclusive content no style 400 leftover style."),
        ("oas-schema-xor-content-param", "leftover-param-schema-and-content", "content", "schema and content leftover", "schema xor content", "400",
         f"{SPEC}#parameter-object", "schema and content are exclusive, leftover both fails closed.",
         f"{SPEC}#media-type-object", "Exclusive xor 400 leftover both."),
        ("oas-media-example-xor-examples", "leftover-media-example-and-examples", "examples", "example and examples leftover", "media example xor examples", "400",
         f"{SPEC}#media-type-object", "media example and examples are exclusive, leftover both fails closed.",
         f"{SPEC}#example-object", "Exclusive media xor 400 leftover both."),
    ],
}


HEAD = '''#!/usr/bin/env python3
"""Unique OpenAPI-drift ACM catalog {catalog}. Fast slug load."""
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
BANNED_PRIOR |= {{
    "oas-allowemptyvalue-header", "leftover-omit-header-empty",
    "oas-lll4-proto-optional", "protobuf-lll4-optional-oas",
    "accept-language-bcp47", "iso639-language",
    "smile-binary-json", "cbor-majortype-vs-smile",
    "422-vs-400-validation", "207-multistatus-batch",
}}


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
'''

TAIL = '''
]


def catalog_selfcheck() -> None:
    seen: set[str] = set()
    if len(PAIRS) < 12:
        raise SystemExit(f"catalog too small: {{len(PAIRS)}}")
    for a, b in PAIRS:
        if not a["success"] or b["success"]:
            raise SystemExit(f"pair must be success+fail: {{a['slug']}} / {{b['slug']}}")
        for spec in (a, b):
            slug = spec["slug"]
            if slug in seen or slug in BANNED_PRIOR:
                raise SystemExit(f"duplicate or prior slug {{slug}}")
            seen.add(slug)
            if "w131" in slug or "422-vs-400" in slug or "207-multistatus" in slug:
                raise SystemExit(f"banned {{slug}}")
            if "smile" in slug or "cbor" in slug:
                raise SystemExit(f"banned smile/cbor {{slug}}")
            if "lll4" in slug or "accept-language" in slug or "iso639" in slug:
                raise SystemExit(f"banned prior plant {{slug}}")
            if "allowemptyvalue-header" in slug or "omit-header-empty" in slug:
                raise SystemExit(f"banned r4006 plant {{slug}}")


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
            raise SystemExit(f"slug {{spec['slug']}} already published")
    e1 = build_episode(round_n, t1)
    e2 = build_episode(round_n, t2)
    for e in (e1, e2):
        blob = json.dumps(e)
        for banned in BANNED_BLOB:
            if f'"{{banned}}"' in blob:
                raise SystemExit(f"banned key {{banned}}")
        assert e["meta"]["generator"] == GEN
        assert len(e["steps"]) == 16
        assert "[variant" not in e["goal"] and "-w131" not in e["id"]
        assert e["id"].startswith(f"acm-r{{round_n:04d}}-")
    batch = staging / f"batch-r{{round_n:02d}}.jsonl"
    notes = staging / f"NOTES-r{{round_n:02d}}.md"
    batch.write_text(json.dumps(e1, ensure_ascii=False) + "\\n" + json.dumps(e2, ensure_ascii=False) + "\\n")
    notes.write_text(notes_text(round_n, [e1, e2], [t1, t2], idx))
    print(json.dumps({{"round": round_n, "idx": idx, "ids": [e1["id"], e2["id"]], "catalog": "{catalog}"}}))


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
'''


def pname(slug: str) -> str:
    return hashlib.sha1(slug.encode()).hexdigest()[:6]


def emit_pair(row: tuple[str, str, str, str, str, str, str, str, str, str]) -> str:
    a, b, field, old, new, code, f1, o1, f2, o2 = row
    na, nb = pname(a), pname(b)
    vs_a = f"r4214 leftover-encoding-csv ({new} vs leftover, not encoding mill)"
    vs_b = f"r4214 oas-encoding-style-pipe ({old} leftover, not encoding mill)"
    fa = (
        f'    (p(slug="{a}", domain="{a}-vs-{b}", success=True, name="{na}", '
        f'stack="OpenAPI 3.1 {field} + Go", field="{field}", old="{old}", new="{new}", '
        f'fail_err="{code}: leftover {old} after {new}-only", '
        f'plan="{new}-only {code}s leftover {old}. Dual-read leftover for one release.", '
        f'residual="compat leftover; drop after window 5", vs="{vs_a}", '
        f'fetch1="{f1}", fetch1_ok="{o1}", fetch2="{f2}", fetch2_ok="{o2}"),\n'
        f'     p(slug="{b}", domain="{b}-vs-{a}", success=False, name="{nb}", '
        f'stack="OpenAPI leftover {field} + Java + TS", field="{field}", old="{new}", new="{old} only", '
        f'fail_err="{code}: leftover {new} after {old}-only", '
        f'plan="{old}-only {code}s leftover {new}. Freeze new, spec leftover.", '
        f'residual="handoff: keep new or force leftover", vs="{vs_b}", '
        f'fetch1="{f2}", fetch1_ok="{o2}", fetch2="{f1}", fetch2_ok="{o1}")),'
    )
    return fa


def main() -> None:
    all_slugs: list[str] = []
    for mill, rows in MILLS.items():
        assert len(rows) == 16, (mill, len(rows))
        for row in rows:
            all_slugs.extend(row[:2])
    dups = [s for s in all_slugs if all_slugs.count(s) > 1]
    if dups:
        raise SystemExit(f"internal dups {sorted(set(dups))}")
    hit = [s for s in all_slugs if s in USED]
    if hit:
        raise SystemExit(f"used collisions {hit}")
    for mill, rows in MILLS.items():
        catalog = f"r{mill}"
        body = "\n".join(emit_pair(r) for r in rows)
        text = HEAD.format(catalog=catalog) + body + TAIL.format(catalog=catalog)
        dest = HERE / f"acm-mill-r{mill}.py"
        dest.write_text(text)
        print(f"wrote {dest.name} pairs={len(rows)}")
    print("slugs", len(all_slugs))


if __name__ == "__main__":
    main()
