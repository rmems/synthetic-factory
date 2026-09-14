#!/usr/bin/env python3
"""Append unique OpenAPI-drift ACM mills starting at r4550."""
from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("acm_gen_r4486", HERE / "_gen_acm_plants_r4486.py")
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)
g = mod.g
SPEC, JS, RFC = g.SPEC, g.JS, g.RFC

# 4486 gen already filled MILLS through 4534.

def P(a, b, field, old, new, code, f1, o1, f2, o2):
    return (a, b, field, old, new, code, f1, o1, f2, o2)

g.MILLS[4550] = [
    P("oas-host-header-required", "leftover-missing-host", "Host", "missing host leftover", "Host header required", "400",
      f"{RFC}/rfc9110#name-host", "Host is required, leftover missing fails closed.",
      f"{SPEC}#parameter-object", "Exclusive Host 400 leftover missing."),
    P("oas-range-requests-bytes", "leftover-ignore-range", "Range", "ignore range leftover", "byte range requests", "400",
      f"{RFC}/rfc9110#name-range", "Range bytes must be honored, leftover ignore fails closed.",
      f"{SPEC}#parameter-object", "Exclusive Range 400 leftover ignore."),
    P("oas-accept-ranges-bytes", "leftover-no-accept-ranges", "Accept-Ranges", "no accept-ranges leftover", "Accept-Ranges bytes", "400",
      f"{RFC}/rfc9110#name-accept-ranges", "Accept-Ranges: bytes is required here, leftover missing fails closed.",
      f"{SPEC}#header-object", "Exclusive Accept-Ranges 400 leftover none."),
    P("oas-content-range-206", "leftover-200-as-partial", "Content-Range", "200 as partial leftover", "206 Content-Range", "400",
      f"{RFC}/rfc9110#name-206-partial-content", "206 needs Content-Range, leftover 200-as-partial fails closed.",
      f"{SPEC}#response-object", "Exclusive 206 400 leftover 200."),
    P("oas-if-range-conditional", "leftover-range-no-if-range", "If-Range", "range no If-Range leftover", "If-Range required", "400",
      f"{RFC}/rfc9110#name-if-range", "Range with validator needs If-Range, leftover missing fails closed.",
      f"{SPEC}#parameter-object", "Exclusive If-Range 400 leftover none."),
    P("oas-last-modified-get", "leftover-no-last-modified", "Last-Modified", "no last-modified leftover", "Last-Modified on GET", "400",
      f"{RFC}/rfc9110#name-last-modified", "GET needs Last-Modified, leftover missing fails closed.",
      f"{SPEC}#header-object", "Exclusive Last-Modified 400 leftover none."),
    P("oas-expires-http-date", "leftover-expires-delta", "Expires", "delta expires leftover", "Expires HTTP-date", "400",
      f"{RFC}/rfc9111#name-expires", "Expires is an HTTP-date, leftover delta fails closed.",
      f"{SPEC}#header-object", "Exclusive Expires date 400 leftover delta."),
    P("oas-date-header-required", "leftover-missing-date-header", "Date", "missing date leftover", "Date header required", "400",
      f"{RFC}/rfc9110#name-date", "Date is required on origin responses, leftover missing fails closed.",
      f"{SPEC}#header-object", "Exclusive Date 400 leftover missing."),
    P("oas-origin-cors-required", "leftover-no-origin-header", "Origin", "no origin leftover", "Origin header required", "400",
      f"{SPEC}#parameter-object", "CORS credentialed calls need Origin, leftover missing fails closed.",
      f"{SPEC}#header-object", "Exclusive Origin 400 leftover none."),
    P("oas-ac-allow-methods", "leftover-star-allow-methods", "Access-Control-Allow-Methods", "star methods leftover", "CORS allow methods list", "400",
      f"{SPEC}#header-object", "Allow-Methods must be explicit, leftover * fails closed.",
      f"{RFC}/rfc9110", "Exclusive methods list 400 leftover star."),
    P("oas-ac-allow-headers", "leftover-unlisted-req-headers", "Access-Control-Allow-Headers", "unlisted headers leftover", "CORS allow headers list", "400",
      f"{SPEC}#header-object", "request headers must be listed, leftover unlisted fails closed.",
      f"{RFC}/rfc9110", "Exclusive allow headers 400 leftover unlisted."),
    P("oas-ac-max-age-preflight", "leftover-preflight-no-maxage", "Access-Control-Max-Age", "no max-age leftover", "CORS max-age", "400",
      f"{SPEC}#header-object", "preflight needs Max-Age, leftover missing fails closed.",
      f"{RFC}/rfc9110", "Exclusive Max-Age 400 leftover none."),
    P("oas-hsts-preload", "leftover-no-hsts", "Strict-Transport-Security", "no hsts leftover", "HSTS preload", "400",
      f"{SPEC}#header-object", "HSTS is required, leftover missing fails closed.",
      f"{RFC}/rfc6797", "Exclusive HSTS 400 leftover none."),
    P("oas-nosniff-content-type", "leftover-no-nosniff", "X-Content-Type-Options", "no nosniff leftover", "nosniff", "400",
      f"{SPEC}#header-object", "X-Content-Type-Options: nosniff is required, leftover missing fails closed.",
      f"{RFC}/rfc9110", "Exclusive nosniff 400 leftover none."),
    P("oas-frame-options-deny", "leftover-allow-framing", "X-Frame-Options", "allow framing leftover", "X-Frame-Options DENY", "400",
      f"{SPEC}#header-object", "X-Frame-Options DENY is required, leftover allow fails closed.",
      f"{RFC}/rfc7034", "Exclusive DENY 400 leftover allow."),
    P("oas-referrer-policy-strict", "leftover-unsafe-referrer", "Referrer-Policy", "unsafe referrer leftover", "strict-origin-when-cross-origin", "400",
      f"{SPEC}#header-object", "Referrer-Policy must be strict, leftover unsafe fails closed.",
      f"{RFC}/rfc9110", "Exclusive referrer policy 400 leftover unsafe."),
]
g.MILLS[4566] = [
    P("oas-permissions-policy", "leftover-unrestricted-features", "Permissions-Policy", "unrestricted leftover", "Permissions-Policy", "400",
      f"{SPEC}#header-object", "Permissions-Policy restricts features, leftover unrestricted fails closed.",
      f"{RFC}/rfc9110", "Exclusive Permissions-Policy 400 leftover unrestricted."),
    P("oas-coop-same-origin", "leftover-no-coop", "Cross-Origin-Opener-Policy", "no coop leftover", "COOP same-origin", "400",
      f"{SPEC}#header-object", "COOP same-origin is required, leftover missing fails closed.",
      f"{RFC}/rfc9110", "Exclusive COOP 400 leftover none."),
    P("oas-coep-require-corp", "leftover-no-coep", "Cross-Origin-Embedder-Policy", "no coep leftover", "COEP require-corp", "400",
      f"{SPEC}#header-object", "COEP require-corp is required, leftover missing fails closed.",
      f"{RFC}/rfc9110", "Exclusive COEP 400 leftover none."),
    P("oas-corp-same-origin", "leftover-no-corp", "Cross-Origin-Resource-Policy", "no corp leftover", "CORP same-origin", "400",
      f"{SPEC}#header-object", "CORP same-origin is required, leftover missing fails closed.",
      f"{RFC}/rfc9110", "Exclusive CORP 400 leftover none."),
    P("oas-ref-siblings-oas31", "leftover-ref-drop-siblings", "$ref", "drop siblings leftover", "$ref siblings allowed", "400",
      f"{SPEC}#schema-object", "OAS 3.1 allows $ref siblings, leftover drop-siblings fails closed.",
      f"{JS}/schema", "Exclusive $ref siblings 400 leftover drop."),
    P("oas-license-id-xor-url", "leftover-license-id-and-url", "identifier", "id and url leftover", "license identifier xor url", "400",
      f"{SPEC}#license-object", "identifier and url are exclusive, leftover both fails closed.",
      f"{SPEC}#info-object", "Exclusive xor 400 leftover both."),
    P("oas-operation-tags-declared", "leftover-undeclared-op-tag", "tags", "undeclared tag leftover", "operation tags declared", "400",
      f"{SPEC}#operation-object", "operation tags must be declared in tags[], leftover undeclared fails closed.",
      f"{SPEC}#tag-object", "Exclusive declared tags 400 leftover undeclared."),
    P("oas-oauth2-pkce-s256", "leftover-pkce-plain", "code_challenge_method", "plain pkce leftover", "PKCE S256", "401",
      f"{RFC}/rfc7636", "PKCE S256 is required, leftover plain fails closed.",
      f"{SPEC}#oauth-flow-object", "Exclusive S256 401 leftover plain."),
    P("oas-jwks-uri-https", "leftover-jwks-http", "jwks_uri", "http jwks leftover", "jwks_uri https", "401",
      f"{RFC}/rfc7517", "jwks_uri must be https, leftover http fails closed.",
      f"{SPEC}#security-scheme-object", "Exclusive jwks https 401 leftover http."),
    P("oas-issuer-no-trailing-slash", "leftover-issuer-slash-mismatch", "issuer", "slash mismatch leftover", "issuer no trailing slash", "401",
      f"{RFC}/rfc8414", "issuer strings must match exactly, leftover slash mismatch fails closed.",
      f"{SPEC}#security-scheme-object", "Exclusive issuer 401 leftover slash."),
    P("oas-revocation-endpoint", "leftover-delete-as-revoke", "revocation_endpoint", "DELETE as revoke leftover", "token revocation endpoint", "401",
      f"{RFC}/rfc7009", "revocation_endpoint is not leftover DELETE-as-revoke.",
      f"{SPEC}#oauth-flow-object", "Exclusive revocation 401 leftover DELETE."),
    P("oas-introspection-endpoint", "leftover-decode-jwt-locally", "introspection_endpoint", "local jwt decode leftover", "token introspection", "401",
      f"{RFC}/rfc7662", "introspection_endpoint is not leftover local JWT decode.",
      f"{SPEC}#oauth-flow-object", "Exclusive introspection 401 leftover local decode."),
    P("oas-maxcontains-needs-contains", "leftover-maxcontains-alone", "maxContains", "maxContains alone leftover", "maxContains with contains", "400",
      f"{JS}/array#maxcontains", "maxContains requires contains, leftover alone fails closed.",
      f"{SPEC}#schema-object", "Exclusive maxContains+contains 400 leftover alone."),
    P("oas-mincontains-needs-contains", "leftover-mincontains-alone", "minContains", "minContains alone leftover", "minContains with contains", "400",
      f"{JS}/array#mincontains", "minContains requires contains, leftover alone fails closed.",
      f"{SPEC}#schema-object", "Exclusive minContains+contains 400 leftover alone."),
    P("oas-dynamicref-needs-anchor", "leftover-dynamicref-as-ref", "$dynamicRef", "dynamicRef as ref leftover", "$dynamicRef needs $dynamicAnchor", "400",
      f"{JS}/schema#dynamic-references", "$dynamicRef needs a $dynamicAnchor, leftover $ref fails closed.",
      f"{SPEC}#schema-object", "Exclusive $dynamicRef 400 leftover $ref."),
    P("oas-anchor-unique-resource", "leftover-duplicate-anchor", "$anchor", "duplicate anchor leftover", "$anchor unique in resource", "400",
      f"{JS}/schema#anchor", "$anchor must be unique in a resource, leftover duplicates fail closed.",
      f"{SPEC}#schema-object", "Exclusive unique $anchor 400 leftover duplicate."),
]
g.MILLS[4582] = [
    P("oas-pattern-unicode-u", "leftover-ascii-only-pattern", "pattern", "ascii pattern leftover", "unicode pattern", "400",
      f"{JS}/regular_expressions", "pattern is Unicode, leftover ASCII-only fails closed.",
      f"{SPEC}#schema-object", "Exclusive unicode pattern 400 leftover ascii."),
    P("oas-format-regex-js", "leftover-pcre-pattern", "format", "pcre leftover", "format regex ECMA", "400",
      f"{JS}/regular_expressions", "format=regex is ECMA-262, leftover PCRE fails closed.",
      f"{SPEC}#data-types", "Exclusive ECMA regex 400 leftover PCRE."),
    P("oas-xml-wrapped-scalar-ban", "leftover-wrap-scalar-xml", "wrapped", "wrap scalar leftover", "xml wrapped scalar banned", "415",
      f"{SPEC}#xml-object", "wrapped applies to arrays, leftover wrap-scalar fails closed.",
      f"{SPEC}#schema-object", "Exclusive wrapped ban 415 leftover scalar wrap."),
    P("oas-xml-attr-on-object-ban", "leftover-object-as-xml-attr", "attribute", "object as attr leftover", "xml attribute on object banned", "415",
      f"{SPEC}#xml-object", "attribute is for scalars, leftover object-as-attr fails closed.",
      f"{SPEC}#schema-object", "Exclusive attr ban 415 leftover object attr."),
    P("oas-deepobject-header-invalid", "leftover-header-deepobject", "style", "header deepObject leftover", "deepObject header invalid", "400",
      f"{SPEC}#style-values", "deepObject is query-only, leftover header deepObject fails closed.",
      f"{SPEC}#parameter-object", "Exclusive header deepObject ban 400 leftover header."),
    P("oas-matrix-query-invalid", "leftover-query-matrix-style", "style", "query matrix leftover", "matrix query invalid", "400",
      f"{SPEC}#style-values", "matrix is path-only, leftover query matrix fails closed.",
      f"{SPEC}#parameter-object", "Exclusive matrix query ban 400 leftover query."),
    P("oas-label-query-invalid", "leftover-query-label-style", "style", "query label leftover", "label query invalid", "400",
      f"{SPEC}#style-values", "label is path-only, leftover query label fails closed.",
      f"{SPEC}#parameter-object", "Exclusive label query ban 400 leftover query."),
    P("oas-form-path-invalid", "leftover-path-form-style", "style", "path form leftover", "form path invalid", "400",
      f"{SPEC}#style-values", "form is not for path, leftover path form fails closed.",
      f"{SPEC}#parameter-object", "Exclusive form path ban 400 leftover path."),
    P("oas-simple-query-invalid", "leftover-query-simple-style", "style", "query simple leftover", "simple query invalid", "400",
      f"{SPEC}#style-values", "simple is path/header, leftover query simple fails closed.",
      f"{SPEC}#parameter-object", "Exclusive simple query ban 400 leftover query."),
    P("oas-space-path-invalid", "leftover-path-space-style", "style", "path space leftover", "spaceDelimited path invalid", "400",
      f"{SPEC}#style-values", "spaceDelimited is query, leftover path space fails closed.",
      f"{SPEC}#parameter-object", "Exclusive space path ban 400 leftover path."),
    P("oas-pipe-path-invalid", "leftover-path-pipe-style", "style", "path pipe leftover", "pipeDelimited path invalid", "400",
      f"{SPEC}#style-values", "pipeDelimited is query, leftover path pipe fails closed.",
      f"{SPEC}#parameter-object", "Exclusive pipe path ban 400 leftover path."),
    P("oas-deepobject-path-invalid", "leftover-path-deepobject", "style", "path deepObject leftover", "deepObject path invalid", "400",
      f"{SPEC}#style-values", "deepObject is query, leftover path deepObject fails closed.",
      f"{SPEC}#parameter-object", "Exclusive deepObject path ban 400 leftover path."),
    P("oas-content-on-path-param", "leftover-path-schema-only-forced", "content", "schema only leftover", "path param content", "400",
      f"{SPEC}#parameter-object", "path params may use content, leftover schema-only-forced fails closed.",
      f"{SPEC}#media-type-object", "Exclusive path content 400 leftover schema only."),
    P("oas-client-creds-no-refresh", "leftover-client-creds-refresh", "refreshUrl", "client creds refresh leftover", "clientCredentials no refresh", "401",
      f"{SPEC}#oauth-flow-object", "clientCredentials has no refresh, leftover refreshUrl fails closed.",
      f"{RFC}/rfc6749#section-4.4", "Exclusive no refresh 401 leftover refresh."),
    P("oas-auth-code-offline-access", "leftover-auth-code-no-offline", "offline_access", "no offline leftover", "offline_access scope", "401",
      f"{RFC}/rfc6749", "offline_access is required for refresh, leftover missing fails closed.",
      f"{SPEC}#oauth-flow-object", "Exclusive offline_access 401 leftover none."),
    P("oas-global-security-empty-override", "leftover-cannot-clear-global-sec", "security", "cannot clear leftover", "empty security override", "401",
      f"{SPEC}#operation-object", "empty security clears global, leftover cannot-clear fails closed.",
      f"{SPEC}#security-requirement-object", "Exclusive empty override 401 leftover sticky global."),
]
g.MILLS[4598] = [
    P("oas-webhooks-plus-callbacks", "leftover-webhook-as-callback", "webhooks", "webhook as callback leftover", "webhooks plus callbacks", "400",
      f"{SPEC}#oasWebhooks", "webhooks are not leftover callbacks.",
      f"{SPEC}#callback-object", "Exclusive webhooks 400 leftover callbacks."),
    P("oas-json-schema-dialect-202012", "leftover-dialect-draft201909", "jsonSchemaDialect", "2019-09 leftover", "dialect 2020-12", "400",
      f"{SPEC}#openapi-object", "default dialect is 2020-12, leftover 2019-09 fails closed.",
      f"{JS}/schema", "Exclusive 2020-12 400 leftover 2019-09."),
    P("oas-property-names-maxlength", "leftover-unbounded-key-length", "propertyNames", "unbounded key leftover", "propertyNames maxLength", "400",
      f"{JS}/object#propertynames", "propertyNames.maxLength bounds keys, leftover unbounded fails closed.",
      f"{SPEC}#schema-object", "Exclusive key maxLength 400 leftover unbounded."),
    P("oas-pattern-properties-closed", "leftover-pattern-plus-additional", "patternProperties", "pattern plus additional leftover", "patternProperties closed", "400",
      f"{JS}/object#patternproperties", "closed patternProperties forbids leftover additional.",
      f"{SPEC}#schema-object", "Exclusive closed pattern 400 leftover additional."),
    P("oas-if-required-then-schema", "leftover-if-without-then", "then", "if without then leftover", "if requires then", "400",
      f"{JS}/conditionals", "if requires then, leftover if-only fails closed.",
      f"{SPEC}#schema-object", "Exclusive if+then 400 leftover if only."),
    P("oas-not-type-object", "leftover-not-as-enum-ban", "not", "not as enum leftover", "not type object", "400",
      f"{JS}/combining#not", "not:{type:object} is not leftover enum bans.",
      f"{SPEC}#schema-object", "Exclusive not type 400 leftover enum."),
    P("oas-oneOf-const-mapping", "leftover-oneof-unmapped-const", "oneOf", "unmapped const leftover", "oneOf const mapping", "400",
      f"{JS}/combining#oneof", "oneOf consts must map, leftover unmapped fails closed.",
      f"{SPEC}#discriminator-object", "Exclusive const mapping 400 leftover unmapped."),
    P("oas-allOf-unevaluated-false", "leftover-allof-open-merge", "unevaluatedProperties", "open allOf leftover", "allOf unevaluated false", "400",
      f"{JS}/combining#allof", "allOf plus unevaluatedProperties false closes leftover open merges.",
      f"{SPEC}#schema-object", "Exclusive closed allOf 400 leftover open."),
    P("oas-anyOf-unevaluated-false", "leftover-anyof-open-merge", "unevaluatedProperties", "open anyOf leftover", "anyOf unevaluated false", "400",
      f"{JS}/combining#anyof", "anyOf plus unevaluatedProperties false closes leftover open merges.",
      f"{SPEC}#schema-object", "Exclusive closed anyOf 400 leftover open."),
    P("oas-prefixitems-unevaluated", "leftover-tuple-open-tail-items", "unevaluatedItems", "open tuple leftover", "prefixItems unevaluatedItems", "400",
      f"{JS}/array#unevaluateditems", "prefixItems plus unevaluatedItems closes leftover open tails.",
      f"{SPEC}#schema-object", "Exclusive closed tuple 400 leftover open tail."),
    P("oas-exclusive-min-with-minimum", "leftover-both-min-keywords", "minimum", "both min leftover", "exclusiveMinimum without minimum", "400",
      f"{JS}/numeric#exclusiveminimum", "Do not pair leftover minimum with exclusiveMinimum.",
      f"{SPEC}#schema-object", "Exclusive exclusiveMinimum 400 leftover both."),
    P("oas-exclusive-max-with-maximum", "leftover-both-max-keywords", "maximum", "both max leftover", "exclusiveMaximum without maximum", "400",
      f"{JS}/numeric#exclusivemaximum", "Do not pair leftover maximum with exclusiveMaximum.",
      f"{SPEC}#schema-object", "Exclusive exclusiveMaximum 400 leftover both."),
    P("oas-default-readonly-omit", "leftover-default-on-write", "default", "default on write leftover", "readOnly default omit write", "400",
      f"{SPEC}#schema-object", "readOnly defaults are omitted on write, leftover write default fails closed.",
      f"{JS}/generic#annotation", "Exclusive omit default 400 leftover write."),
    P("oas-deprecated-needs-desc", "leftover-deprecated-no-desc", "deprecated", "deprecated no desc leftover", "deprecated with description", "400",
      f"{SPEC}#schema-object", "deprecated fields need description, leftover missing fails closed.",
      f"{JS}/generic#annotation", "Exclusive deprecated desc 400 leftover none."),
    P("oas-examples-typed-values", "leftover-examples-wrong-type", "examples", "wrong type examples leftover", "typed examples", "400",
      f"{JS}/generic#annotation", "examples must match the schema type, leftover wrong-type fails closed.",
      f"{SPEC}#schema-object", "Exclusive typed examples 400 leftover wrong type."),
    P("oas-schema-id-fragment-ok", "leftover-id-fragment-rejected", "$id", "reject fragment leftover", "$id fragment allowed", "400",
      f"{JS}/schema#id", "$id may be a fragment, leftover reject-fragment fails closed.",
      f"{SPEC}#schema-object", "Exclusive $id fragment 400 leftover reject."),
]


def main() -> None:
    hit = []
    seen = set()
    for mill, rows in g.MILLS.items():
        assert len(rows) == 16, (mill, len(rows))
        for row in rows:
            for slug in row[:2]:
                if slug in seen:
                    hit.append(("dup", slug, mill))
                seen.add(slug)
                if mill >= 4550 and slug in g.USED:
                    hit.append(("used", slug, mill))
    if hit:
        raise SystemExit(str(hit[:20]))
    g.main()


if __name__ == "__main__":
    main()
