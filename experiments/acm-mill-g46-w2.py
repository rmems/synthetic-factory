#!/usr/bin/env python3
"""ACM leftover unique OpenAPI-drift catalog after r3713/r3714 lll clones.

BAN wrap w131 cartesian, r3560 422-vs-400 / 207-multistatus,
r3713 smile-binary-json / cbor-majortype-vs-smile, r3714 DBC contamination,
r3715+ lll serialization clones, prior leftover slugs.
"""
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
BANNED_SLUG_NEEDLES = _b.BANNED_SLUG_NEEDLES
build_episode = _b.build_episode
notes_text = _b.notes_text
published_slugs = _b.published_slugs

BANNED_PRIOR = {p[0]["slug"] for p in _b.PAIRS} | {p[1]["slug"] for p in _b.PAIRS}
for _name in ("acm-mill-r3620.py", "acm-mill-r3667.py", "acm-mill-r3698.py"):
    _sp = importlib.util.spec_from_file_location(_name, HERE / _name)
    _m = importlib.util.module_from_spec(_sp)
    assert _sp.loader is not None
    _sp.loader.exec_module(_m)
    BANNED_PRIOR |= {p[0]["slug"] for p in _m.PAIRS} | {p[1]["slug"] for p in _m.PAIRS}

BANNED_PRIOR |= {
    "422-vs-400-validation",
    "207-multistatus-batch",
    "smile-binary-json",
    "cbor-majortype-vs-smile",
    "asyncapi-lll-ce-bind",
    "cloudevents-lll-a3-bind",
    "jsonapi-lll-type-id",
    "hal-lll-links-only",
    "capnp-lll-rpc",
    "flatbuffers-lll-vtable",
    "msgpack-lll-fixmap",
    "ion-lll-bvm",
    "avro-lll-ocf",
    "thrift-lll-compact",
    "fhir-lll-r4-json",
    "hl7-lll-v2-pipe",
    "edn-lll-tagged",
    "transit-lll-json",
    "bson-lll-oid",
    "json-lll-vs-bson",
    "yaml-lll-anchor",
    "toml-lll-table",
    "hocon-lll-sub",
    "json-lll-vs-hocon",
    "graphql-lll-schema",
    "rest-lll-vs-graphql",
    "grpc-lll-proto",
    "http-lll-vs-grpc",
    "oas31-lll-paths",
    "raml-lll-vs-oas",
    "protobuf-lll-wire",
    "json-lll-vs-protobuf",
    "soap-lll-envelope",
    "rest-lll-vs-soap",
    "xml-lll-ns",
    "json-lll-vs-xml",
}

OAS = "https://spec.openapis.org/oas/v3.1.0.html"
JS = "https://json-schema.org/understanding-json-schema/reference"
GO = "OpenAPI 3.1 + Go + Python"
JT = "OpenAPI 3.1 + Java + TS"


def ok(**kw) -> dict:
    kw.setdefault("success", True)
    kw.setdefault("stack", GO)
    return plant(**kw)


def bad(**kw) -> dict:
    kw.setdefault("success", False)
    kw.setdefault("stack", JT)
    return plant(**kw)


PAIRS: list[tuple[dict, dict]] = [
    (
        ok(slug="oas31-boolean-true", domain="boolean-true-schema-vs-empty-object", name="btrue", field="schema",
           old="empty object leftover {}", new="true boolean schema",
           fail_err="400: leftover {} after boolean-true-only",
           plan="boolean-true-only 400s leftover {}. Abandon exclusive true; dual-accept empty object schemas for one release.",
           residual="SDK still {}; drop after sdk 3",
           vs="r3561 unevaluated-properties (boolean true schema, not unevaluatedProperties)",
           fetch1=f"{JS}/generic.html#boolean-schemas",
           fetch1_ok="Boolean true accepts any instance. leftover {} is a different schema document.",
           fetch2=f"{OAS}#schema-object", fetch2_ok="OAS 3.1 boolean true 400s leftover object schemas."),
        bad(slug="empty-object-schema", domain="empty-object-vs-boolean-true", name="emptyo", field="schema",
            old="boolean true leftover", new="{} object schema only",
            fail_err="400: leftover true after empty-object-only",
            plan="empty-object-only 400s leftover true. Abandon exclusive {}; keep true — codegen wants {}. Freeze true, spec {}.",
            residual="handoff: keep true or force {}; do not claim empty-object-only shipped",
            vs="r3561 unevaluated-properties (empty object leftover vs boolean true, not unevaluatedProperties)",
            fetch1=f"{JS}/object.html", fetch1_ok="{} is an empty object schema. leftover boolean true is not.",
            fetch2=f"{OAS}#schema-object", fetch2_ok="Exclusive {} 400s leftover boolean-true documents."),
    ),
    (
        ok(slug="oas31-boolean-false", domain="boolean-false-schema-vs-not-any", name="bfalse", field="schema",
           old="not leftover any", new="false boolean schema",
           fail_err="400: leftover not:{} after boolean-false-only",
           plan="boolean-false-only 400s leftover not:{}. Abandon exclusive false; dual-accept not:{} for one release.",
           residual="validator still not:{}; drop after val 2",
           vs="r3561 json-schema-not-empty-object (boolean false, not not:{})",
           fetch1=f"{JS}/generic.html#boolean-schemas",
           fetch1_ok="Boolean false rejects every instance. leftover not:{} is a different never encoding.",
           fetch2=f"{OAS}#schema-object", fetch2_ok="Exclusive false 400s leftover not:{} documents."),
        bad(slug="not-any-schema", domain="not-any-vs-boolean-false", name="notany", field="schema",
            old="boolean false leftover", new="not: {} only",
            fail_err="400: leftover false after not-any-only",
            plan="not-any-only 400s leftover false. Abandon exclusive not; keep false — draft07 wants not. Freeze false, spec not.",
            residual="handoff: keep false or force not; do not claim not-any shipped",
            vs="r3561 json-schema-not-empty-object (not:{} leftover vs boolean false)",
            fetch1=f"{JS}/combining.html#not", fetch1_ok="not:{} rejects every instance. leftover boolean false is 2020-12.",
            fetch2=f"{OAS}#schema-object", fetch2_ok="Exclusive not:{} 400s leftover boolean-false documents."),
    ),
    (
        ok(slug="xml-prefix-ns", domain="xml-prefix-vs-unprefixed-name", name="xmlp", field="xml.prefix",
           old="unprefixed leftover name", new="xml prefix svc required",
           fail_err="400: leftover unprefixed after prefix-only",
           plan="prefix-only 400s leftover unprefixed. Abandon exclusive prefix; dual-read unprefixed for one release.",
           residual="Java still unprefixed; drop after jaxb 4",
           vs="wrap xml-name-attribute (xml prefix, not name/attribute)",
           fetch1=f"{OAS}#xml-object", fetch1_ok="xml.prefix qualifies the name. leftover unprefixed elements fail prefix-only.",
           fetch2="https://www.w3.org/TR/xml-names/", fetch2_ok="Exclusive prefix 400s leftover unprefixed XML."),
        bad(slug="xml-namespace-uri", domain="xml-namespace-vs-default-ns", name="xmln", field="xml.namespace",
            old="default ns leftover empty", new="xml namespace URI required",
            fail_err="400: leftover empty xmlns after namespace-only",
            plan="namespace-only 400s leftover empty xmlns. Abandon exclusive URI; keep empty — SOAP wants URI. Freeze empty, spec URI.",
            residual="handoff: keep empty xmlns or force URI; do not claim namespace-only shipped",
            vs="wrap xml-name-attribute (xml namespace URI, not name/attribute)",
            fetch1=f"{OAS}#xml-object", fetch1_ok="xml.namespace is a URI. leftover empty default ns is different.",
            fetch2="https://www.w3.org/TR/xml-names/", fetch2_ok="Exclusive namespace URI 400s leftover un-namespaced XML."),
    ),
    (
        ok(slug="encoding-style-form-mp", domain="encoding-style-form-vs-deep-multipart", name="encs", field="encoding.style",
           old="deep leftover object parts", new="style form for multipart",
           fail_err="400: leftover deep parts after form-style-only",
           plan="form-style-only 400s leftover deep parts. Abandon exclusive form; dual-decode deep parts for one release.",
           residual="mobile still deep; drop after mobile 6",
           vs="wrap deepobject-filter (multipart encoding.style form, not query deepObject)",
           fetch1=f"{OAS}#encoding-object", fetch1_ok="encoding.style form serializes multipart flat. leftover deep parts fail.",
           fetch2=f"{OAS}#media-type-object", fetch2_ok="Exclusive form style 400s leftover nested multipart."),
        bad(slug="encoding-explode-mp", domain="encoding-explode-vs-nonexplode-multipart", name="ence", field="encoding.explode",
            old="non-explode leftover joined", new="explode true multipart",
            fail_err="400: leftover joined after explode-only",
            plan="explode-only 400s leftover joined. Abandon exclusive explode; keep joined — gateway wants explode. Freeze joined, spec explode.",
            residual="handoff: keep joined or force explode; do not claim explode-only shipped",
            vs="r3566 explode-false-form-query (multipart encoding.explode, not query explode)",
            fetch1=f"{OAS}#encoding-object", fetch1_ok="encoding.explode true splits values. leftover joined parts fail explode-only.",
            fetch2=f"{OAS}#media-type-object", fetch2_ok="Exclusive explode 400s leftover non-exploded multipart."),
    ),
    (
        ok(slug="callback-runtime-expr", domain="callback-runtime-expr-vs-static-url", name="cbre", field="callbacks",
           old="static leftover URL", new="runtime $request.body#/cb",
           fail_err="400: leftover static URL after expr-only",
           plan="expr-only 400s leftover static URL. Abandon exclusive expr; dual-accept static callback URLs for one release.",
           residual="partner still static; drop after partner 5",
           vs="r3571 webhooks-item-rename (Path Item callback expression, not webhooks map rename)",
           fetch1=f"{OAS}#callback-object", fetch1_ok="Callback keys are runtime expressions. leftover static URLs are not.",
           fetch2=f"{OAS}#runtime-expressions", fetch2_ok="Exclusive $request expressions 400s leftover static URLs."),
        bad(slug="static-callback-url", domain="static-callback-vs-runtime-expr", name="cbst", field="callbacks",
            old="runtime leftover expression", new="static https callback only",
            fail_err="400: leftover $request after static-only",
            plan="static-only 400s leftover expr. Abandon exclusive static; keep expr — events want static. Freeze expr, spec static.",
            residual="handoff: keep expr or force static; do not claim static-callback shipped",
            vs="r3571 webhooks-item-rename (static callback leftover, not webhooks rename)",
            fetch1=f"{OAS}#callback-object", fetch1_ok="Static callback URLs are not runtime expressions.",
            fetch2=f"{OAS}#runtime-expressions", fetch2_ok="Exclusive static URLs 400s leftover expression-keyed callbacks."),
    ),
    (
        ok(slug="link-requestbody-expr", domain="link-requestbody-vs-parameters-only", name="lreq", field="links.requestBody",
           old="parameters leftover only", new="requestBody $response.body",
           fail_err="400: leftover parameters-only after requestBody-link",
           plan="requestBody-link-only 400s leftover parameters. Abandon exclusive body expr; dual-map parameters for one release.",
           residual="client still parameters; drop after client 2",
           vs="wrap link-operationid-rename (link requestBody expression, not operationId rename)",
           fetch1=f"{OAS}#link-object", fetch1_ok="Link requestBody may follow $response.body. leftover parameters-only omit it.",
           fetch2=f"{OAS}#runtime-expressions", fetch2_ok="Exclusive requestBody expr 400s leftover parameter-only links."),
        bad(slug="link-parameters-only", domain="link-parameters-vs-requestbody-expr", name="lprm", field="links.parameters",
            old="requestBody leftover expr", new="parameters map only",
            fail_err="400: leftover requestBody after parameters-only",
            plan="parameters-only 400s leftover body. Abandon exclusive parameters; keep body — BFF wants parameters. Freeze body, spec parameters.",
            residual="handoff: keep body expr or force parameters; do not claim parameters-only shipped",
            vs="wrap link-operationid-rename (link parameters leftover, not operationId rename)",
            fetch1=f"{OAS}#link-object", fetch1_ok="Link parameters map runtime names. leftover requestBody expr is different.",
            fetch2=f"{OAS}#runtime-expressions", fetch2_ok="Exclusive parameters 400s leftover requestBody links."),
    ),
    (
        ok(slug="info-tos-url", domain="info-termsofservice-url-vs-markdown", name="tos", field="info.termsOfService",
           old="markdown leftover blob", new="https terms URL required",
           fail_err="400: leftover markdown after tos-url-only",
           plan="tos-url-only 400s leftover markdown. Abandon exclusive URL; dual-read markdown ToS for one release.",
           residual="legal still markdown; drop after legal 8",
           vs="r3572 license-spdx-identifier (info.termsOfService URL, not license identifier)",
           fetch1=f"{OAS}#info-object", fetch1_ok="termsOfService MUST be a URL. leftover markdown is not a URI.",
           fetch2=f"{OAS}#info-object", fetch2_ok="Exclusive URL 400s leftover inline markdown ToS."),
        bad(slug="tos-markdown-leftover", domain="tos-markdown-vs-url", name="tosmd", field="info.termsOfService",
            old="URL leftover https", new="markdown ToS only",
            fail_err="400: leftover URL after markdown-only",
            plan="markdown-only 400s leftover URL. Abandon exclusive markdown; keep URL — portal wants markdown. Freeze URL, spec markdown.",
            residual="handoff: keep URL or force markdown; do not claim markdown-ToS shipped",
            vs="r3572 license-spdx-identifier (markdown ToS leftover, not SPDX)",
            fetch1=f"{OAS}#info-object", fetch1_ok="Inline markdown is not termsOfService. leftover URLs fail markdown-only.",
            fetch2=f"{OAS}#info-object", fetch2_ok="Exclusive markdown 400s leftover URL termsOfService."),
    ),
    (
        ok(slug="contact-url-required", domain="contact-url-vs-email-only", name="curl", field="info.contact.url",
           old="email leftover only", new="contact url required",
           fail_err="400: leftover email-only after url-required",
           plan="url-required 400s leftover email-only. Abandon exclusive URL; dual-accept email-only Contact for one release.",
           residual="support still email-only; drop after support 3",
           vs="r3572 license-spdx-identifier (Contact.url, not license)",
           fetch1=f"{OAS}#contact-object", fetch1_ok="Contact.url is a URL. leftover email-only Contact objects omit it.",
           fetch2=f"{OAS}#info-object", fetch2_ok="Exclusive Contact.url 400s leftover email-only info.contact."),
        bad(slug="contact-email-only", domain="contact-email-vs-url", name="cmail", field="info.contact.email",
            old="url leftover https", new="contact email only",
            fail_err="400: leftover url after email-only",
            plan="email-only 400s leftover url. Abandon exclusive email; keep url — CRM wants email. Freeze url, spec email.",
            residual="handoff: keep url or force email; do not claim email-only shipped",
            vs="r3572 license-spdx-identifier (Contact.email leftover, not license)",
            fetch1=f"{OAS}#contact-object", fetch1_ok="Contact.email is an email. leftover Contact.url is a different field.",
            fetch2=f"{OAS}#info-object", fetch2_ok="Exclusive email 400s leftover Contact.url publishers."),
    ),
    (
        ok(slug="components-responses-ref", domain="components-responses-ref-vs-inline", name="cref", field="responses.200",
           old="inline leftover schema", new="$ref #/components/responses/Ok",
           fail_err="400: leftover inline after components-ref-only",
           plan="components-ref-only 400s leftover inline. Abandon exclusive $ref; dual-accept inline responses for one release.",
           residual="SDK still inline; drop after sdk 7",
           vs="r3571 pathitem-component-ref (components.responses $ref, not pathItems)",
           fetch1=f"{OAS}#components-object", fetch1_ok="components.responses holds reusable Response Objects.",
           fetch2=f"{OAS}#response-object", fetch2_ok="Exclusive components $ref 400s leftover inline responses."),
        bad(slug="inline-response-schema", domain="inline-response-vs-components-ref", name="inlr", field="responses.200",
            old="components leftover $ref", new="inline response only",
            fail_err="400: leftover $ref after inline-only",
            plan="inline-only 400s leftover $ref. Abandon exclusive inline; keep $ref — bundler wants inline. Freeze $ref, spec inline.",
            residual="handoff: keep $ref or force inline; do not claim inline-only shipped",
            vs="r3571 pathitem-component-ref (inline response leftover, not pathItems)",
            fetch1=f"{OAS}#response-object", fetch1_ok="Inline responses are not components $ref.",
            fetch2=f"{OAS}#components-object", fetch2_ok="Exclusive inline 400s leftover reusable responses."),
    ),
    (
        ok(slug="oauth2-refreshurl", domain="oauth2-refreshurl-vs-tokenurl-only", name="oref", field="refreshUrl",
           old="tokenUrl leftover only", new="refreshUrl required",
           fail_err="401: leftover tokenUrl-only after refreshUrl-required",
           plan="refreshUrl-required 401s leftover tokenUrl-only. Abandon exclusive refreshUrl; dual-accept tokenUrl refresh for one release.",
           residual="mobile still tokenUrl; drop after mobile 4",
           vs="r3570 oauth2-token-exchange (OAuth refreshUrl, not token exchange)",
           fetch1=f"{OAS}#oauth-flows-object", fetch1_ok="refreshUrl is required here. leftover tokenUrl-only flows omit it.",
           fetch2="https://datatracker.ietf.org/doc/html/rfc6749#section-6", fetch2_ok="Exclusive refreshUrl 401s leftover tokenUrl-only clients."),
        bad(slug="tokenurl-only-oauth", domain="tokenurl-only-vs-refreshurl", name="otok", field="tokenUrl",
            old="refreshUrl leftover", new="tokenUrl only",
            fail_err="401: leftover refreshUrl after tokenUrl-only",
            plan="tokenUrl-only 401s leftover refreshUrl. Abandon exclusive tokenUrl; keep refreshUrl — IdP wants tokenUrl. Freeze refreshUrl, spec tokenUrl.",
            residual="handoff: keep refreshUrl or force tokenUrl; do not claim tokenUrl-only shipped",
            vs="r3570 oauth2-token-exchange (tokenUrl leftover, not token exchange)",
            fetch1=f"{OAS}#oauth-flows-object", fetch1_ok="tokenUrl is the token endpoint. leftover refreshUrl is different.",
            fetch2="https://datatracker.ietf.org/doc/html/rfc6749#section-6", fetch2_ok="Exclusive tokenUrl 401s leftover refreshUrl clients."),
    ),
    (
        ok(slug="cache-control-immutable", domain="cache-control-immutable-vs-maxage", name="ccim", field="Cache-Control",
           old="max-age leftover only", new="immutable required",
           fail_err="400: leftover max-age-only after immutable-only",
           plan="immutable-only 400s leftover max-age. Abandon exclusive immutable; dual-accept max-age for one release.",
           residual="CDN still max-age; drop after cdn 2",
           vs="r3587 ratelimit-policy-header (Cache-Control immutable, not RateLimit)",
           fetch1="https://www.rfc-editor.org/rfc/rfc8246.html", fetch1_ok="immutable means the representation will not change.",
           fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive immutable 400s leftover max-age-only caches."),
        bad(slug="max-age-only-cache", domain="maxage-vs-immutable", name="maxage", field="Cache-Control",
            old="immutable leftover", new="max-age only",
            fail_err="400: leftover immutable after max-age-only",
            plan="max-age-only 400s leftover immutable. Abandon exclusive max-age; keep immutable — edge wants max-age. Freeze immutable, spec max-age.",
            residual="handoff: keep immutable or force max-age; do not claim max-age-only shipped",
            vs="r3587 ratelimit-policy-header (max-age leftover, not RateLimit)",
            fetch1="https://www.rfc-editor.org/rfc/rfc9111.html#name-max-age", fetch1_ok="max-age is a delta-seconds freshness lifetime.",
            fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive max-age 400s leftover immutable clients."),
    ),
    (
        ok(slug="cache-status-rfc9211", domain="cache-status-vs-age-header", name="cstat", field="Cache-Status",
           old="Age leftover seconds", new="Cache-Status hit;ttl=60",
           fail_err="400: leftover Age after Cache-Status-only",
           plan="Cache-Status-only 400s leftover Age. Abandon exclusive Cache-Status; dual-read Age for one release.",
           residual="proxy still Age; drop after proxy 5",
           vs="r3587 retry-after-http-date (Cache-Status RFC 9211, not Retry-After)",
           fetch1="https://www.rfc-editor.org/rfc/rfc9211.html", fetch1_ok="Cache-Status is a structured cache response. leftover Age is delta-seconds.",
           fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive Cache-Status 400s leftover Age-only intermediaries."),
        bad(slug="age-header-only", domain="age-header-vs-cache-status", name="ageh", field="Age",
            old="Cache-Status leftover", new="Age seconds only",
            fail_err="400: leftover Cache-Status after Age-only",
            plan="Age-only 400s leftover Cache-Status. Abandon exclusive Age; keep Cache-Status — CDN wants Age. Freeze Cache-Status, spec Age.",
            residual="handoff: keep Cache-Status or force Age; do not claim Age-only shipped",
            vs="r3587 retry-after-http-date (Age leftover, not Retry-After)",
            fetch1="https://www.rfc-editor.org/rfc/rfc9111.html#name-age", fetch1_ok="Age is estimated seconds. leftover Cache-Status is different.",
            fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive Age 400s leftover Cache-Status producers."),
    ),
    (
        ok(slug="targeted-cache-control", domain="targeted-cache-control-vs-untargeted", name="tcache", field="CDN-Cache-Control",
           old="Cache-Control leftover shared", new="CDN-Cache-Control required",
           fail_err="400: leftover Cache-Control after targeted-only",
           plan="targeted-only 400s leftover Cache-Control. Abandon exclusive CDN-Cache-Control; dual-read Cache-Control for one release.",
           residual="origin still Cache-Control; drop after origin 3",
           vs="r3587 ratelimit-policy-header (targeted Cache-Control RFC 9213, not RateLimit)",
           fetch1="https://www.rfc-editor.org/rfc/rfc9213.html", fetch1_ok="CDN-Cache-Control applies to one cache. leftover Cache-Control is untargeted.",
           fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive CDN-Cache-Control 400s leftover untargeted Cache-Control."),
        bad(slug="untargeted-cache-control", domain="untargeted-vs-targeted-cache-control", name="ucache", field="Cache-Control",
            old="CDN-Cache-Control leftover", new="Cache-Control only",
            fail_err="400: leftover CDN-Cache-Control after untargeted-only",
            plan="untargeted-only 400s leftover CDN-Cache-Control. Abandon exclusive Cache-Control; keep CDN — browser wants Cache-Control. Freeze CDN, spec Cache-Control.",
            residual="handoff: keep CDN-Cache-Control or force Cache-Control; do not claim untargeted shipped",
            vs="r3587 ratelimit-policy-header (untargeted leftover, not RateLimit)",
            fetch1="https://www.rfc-editor.org/rfc/rfc9111.html#name-cache-control", fetch1_ok="Cache-Control is untargeted. leftover CDN-Cache-Control is targeted.",
            fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive Cache-Control 400s leftover targeted fields."),
    ),
    (
        ok(slug="stale-while-revalidate", domain="stale-while-revalidate-vs-must-revalidate", name="swr", field="Cache-Control",
           old="must-revalidate leftover", new="stale-while-revalidate=30",
           fail_err="400: leftover must-revalidate after swr-only",
           plan="swr-only 400s leftover must-revalidate. Abandon exclusive SWR; dual-accept must-revalidate for one release.",
           residual="app still must-revalidate; drop after app 6",
           vs="r3587 retry-after-http-date (stale-while-revalidate RFC 5861, not Retry-After)",
           fetch1="https://www.rfc-editor.org/rfc/rfc5861.html", fetch1_ok="stale-while-revalidate serves stale while revalidating.",
           fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive SWR 400s leftover must-revalidate caches."),
        bad(slug="must-revalidate-only", domain="must-revalidate-vs-stale-while-revalidate", name="mustre", field="Cache-Control",
            old="stale-while-revalidate leftover", new="must-revalidate only",
            fail_err="400: leftover swr after must-revalidate-only",
            plan="must-revalidate-only 400s leftover SWR. Abandon exclusive must-revalidate; keep SWR — compliance wants must-revalidate. Freeze SWR, spec must-revalidate.",
            residual="handoff: keep SWR or force must-revalidate; do not claim must-revalidate shipped",
            vs="r3587 retry-after-http-date (must-revalidate leftover, not Retry-After)",
            fetch1="https://www.rfc-editor.org/rfc/rfc9111.html#name-must-revalidate", fetch1_ok="must-revalidate forbids stale use after expiration.",
            fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive must-revalidate 400s leftover SWR clients."),
    ),
    (
        ok(slug="alt-svc-h3", domain="alt-svc-h3-vs-h2-alpn", name="alth3", field="Alt-Svc",
           old="h2 leftover alpn", new="h3=\":443\"; ma=86400",
           fail_err="400: leftover h2 after h3-only",
           plan="h3-only 400s leftover h2. Abandon exclusive h3; dual-advertise h2 Alt-Svc for one release.",
           residual="edge still h2; drop after edge 4",
           vs="r3577 status-308-https (Alt-Svc h3, not 308 https redirect)",
           fetch1="https://www.rfc-editor.org/rfc/rfc7838.html", fetch1_ok="Alt-Svc advertises h3. leftover h2 ALPN-only is different.",
           fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive h3 Alt-Svc 400s leftover h2-only clients."),
        bad(slug="h2-alpn-only", domain="h2-alpn-vs-alt-svc-h3", name="h2alpn", field="ALPN",
            old="h3 leftover Alt-Svc", new="h2 ALPN only",
            fail_err="400: leftover h3 after h2-only",
            plan="h2-only 400s leftover h3. Abandon exclusive h2; keep h3 — mesh wants h2. Freeze h3, spec h2.",
            residual="handoff: keep h3 or force h2; do not claim h2-only shipped",
            vs="r3577 status-308-https (h2 ALPN leftover, not 308)",
            fetch1="https://www.rfc-editor.org/rfc/rfc7301.html", fetch1_ok="ALPN h2 is not Alt-Svc h3.",
            fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive h2 400s leftover h3 Alt-Svc."),
    ),
    (
        ok(slug="priority-rfc9218", domain="priority-header-vs-urgency-query", name="prih", field="Priority",
           old="urgency leftover query", new="Priority u=1,i",
           fail_err="400: leftover urgency query after Priority-only",
           plan="Priority-only 400s leftover urgency query. Abandon exclusive Priority; dual-read urgency query for one release.",
           residual="browser still query; drop after browser 1",
           vs="r3566 explode-false-form-query (RFC 9218 Priority header, not query explode)",
           fetch1="https://www.rfc-editor.org/rfc/rfc9218.html", fetch1_ok="Priority is a structured field (u, i).",
           fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive Priority 400s leftover urgency query clients."),
        bad(slug="urgency-query-leftover", domain="urgency-query-vs-priority-header", name="urgq", field="urgency",
            old="Priority leftover header", new="urgency query only",
            fail_err="400: leftover Priority after urgency-query-only",
            plan="urgency-query-only 400s leftover Priority. Abandon exclusive query; keep Priority — HTTP/3 wants query. Freeze Priority, spec query.",
            residual="handoff: keep Priority or force urgency query; do not claim urgency-query shipped",
            vs="r3566 explode-false-form-query (urgency query leftover, not explode)",
            fetch1="https://www.rfc-editor.org/rfc/rfc9218.html", fetch1_ok="urgency as a query is not RFC 9218 Priority.",
            fetch2=f"{OAS}#parameter-object", fetch2_ok="Exclusive urgency query 400s leftover Priority headers."),
    ),
    (
        ok(slug="sf-dictionary-rfc8941", domain="structured-fields-dict-vs-unstructured", name="sfd", field="Vendor-Params",
           old="unstructured leftover k=v", new="sf Dictionary a=1, b=?0",
           fail_err="400: leftover unstructured after sf-dict-only",
           plan="sf-dict-only 400s leftover unstructured. Abandon exclusive Dictionary; dual-parse unstructured k=v for one release.",
           residual="partner still unstructured; drop after partner 9",
           vs="r3587 ratelimit-policy-header (RFC 8941 Dictionary, not RateLimit-Policy)",
           fetch1="https://www.rfc-editor.org/rfc/rfc8941.html#name-dictionaries", fetch1_ok="Dictionaries are structured fields. leftover unstructured k=v fails sf.",
           fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive sf Dictionary 400s leftover unstructured headers."),
        bad(slug="unstructured-header", domain="unstructured-vs-sf-dictionary", name="unstr", field="Vendor-Params",
            old="sf Dictionary leftover", new="unstructured k=v only",
            fail_err="400: leftover sf Dictionary after unstructured-only",
            plan="unstructured-only 400s leftover sf. Abandon exclusive unstructured; keep sf — gateway wants unstructured. Freeze sf, spec unstructured.",
            residual="handoff: keep sf Dictionary or force unstructured; do not claim unstructured shipped",
            vs="r3587 ratelimit-policy-header (unstructured leftover, not RateLimit)",
            fetch1="https://www.rfc-editor.org/rfc/rfc9110.html#name-field-values", fetch1_ok="Unstructured field values are not RFC 8941 Dictionaries.",
            fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive unstructured 400s leftover sf Dictionary producers."),
    ),
    (
        ok(slug="sf-display-string", domain="sf-display-string-vs-sf-token", name="sfds", field="Title",
           old="sf token leftover", new="sf Display String %\"...\"",
           fail_err="400: leftover token after display-string-only",
           plan="display-string-only 400s leftover token. Abandon exclusive Display String; dual-read sf tokens for one release.",
           residual="i18n still token; drop after i18n 2",
           vs="r3587 ratelimit-policy-header (RFC 9651 Display String, not RateLimit)",
           fetch1="https://www.rfc-editor.org/rfc/rfc9651.html#name-display-strings", fetch1_ok="Display Strings carry UTF-8. leftover sf tokens are ASCII.",
           fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive Display String 400s leftover sf tokens."),
        bad(slug="sf-token-only", domain="sf-token-vs-display-string", name="sftok", field="Title",
            old="Display String leftover", new="sf token only",
            fail_err="400: leftover Display String after token-only",
            plan="token-only 400s leftover Display String. Abandon exclusive token; keep Display String — l10n wants token. Freeze Display String, spec token.",
            residual="handoff: keep Display String or force token; do not claim token-only shipped",
            vs="r3587 ratelimit-policy-header (sf token leftover, not RateLimit)",
            fetch1="https://www.rfc-editor.org/rfc/rfc8941.html#name-tokens", fetch1_ok="sf tokens are ASCII. leftover Display Strings fail token parsers.",
            fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive token 400s leftover Display String producers."),
    ),
    (
        ok(slug="repr-digest-sha256", domain="repr-digest-vs-content-md5", name="rdig", field="Repr-Digest",
           old="Content-MD5 leftover", new="Repr-Digest sha-256=:...:",
           fail_err="400: leftover Content-MD5 after Repr-Digest-only",
           plan="Repr-Digest-only 400s leftover Content-MD5. Abandon exclusive Repr-Digest; dual-read Content-MD5 for one release.",
           residual="scanner still MD5; drop after scanner 4",
           vs="wrap content-digest-rfc9530 (Repr-Digest, not Content-Digest)",
           fetch1="https://www.rfc-editor.org/rfc/rfc9530.html#name-the-repr-digest-field", fetch1_ok="Repr-Digest hashes the representation. leftover Content-MD5 is different.",
           fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive Repr-Digest 400s leftover Content-MD5 clients."),
        bad(slug="content-md5-leftover", domain="content-md5-vs-repr-digest", name="cmd5", field="Content-MD5",
            old="Repr-Digest leftover", new="Content-MD5 only",
            fail_err="400: leftover Repr-Digest after Content-MD5-only",
            plan="Content-MD5-only 400s leftover Repr-Digest. Abandon exclusive MD5; keep Repr-Digest — integrity wants MD5. Freeze Repr-Digest, spec MD5.",
            residual="handoff: keep Repr-Digest or force Content-MD5; do not claim Content-MD5 shipped",
            vs="wrap content-digest-rfc9530 (Content-MD5 leftover, not Content-Digest)",
            fetch1="https://www.rfc-editor.org/rfc/rfc1864.html", fetch1_ok="Content-MD5 is a base64 MD5. leftover Repr-Digest is RFC 9530.",
            fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive Content-MD5 400s leftover Repr-Digest producers."),
    ),
    (
        ok(slug="authentication-info", domain="authentication-info-vs-www-authenticate", name="ainfo", field="Authentication-Info",
           old="WWW-Authenticate leftover", new="Authentication-Info rspauth",
           fail_err="400: leftover WWW-Authenticate after Authentication-Info-only",
           plan="Authentication-Info-only 400s leftover WWW-Authenticate. Abandon exclusive Auth-Info; dual-read WWW-Authenticate for one release.",
           residual="client still WWW-Authenticate; drop after client 5",
           vs="r3569 security-mutual-tls (Authentication-Info RFC 7615, not mTLS)",
           fetch1="https://www.rfc-editor.org/rfc/rfc7615.html", fetch1_ok="Authentication-Info carries rspauth after success.",
           fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive Authentication-Info 400s leftover WWW-Authenticate."),
        bad(slug="www-authenticate-only", domain="www-authenticate-vs-authentication-info", name="wwwauth", field="WWW-Authenticate",
            old="Authentication-Info leftover", new="WWW-Authenticate only",
            fail_err="400: leftover Authentication-Info after WWW-Authenticate-only",
            plan="WWW-Authenticate-only 400s leftover Auth-Info. Abandon exclusive WWW-Authenticate; keep Auth-Info — IdP wants WWW-Authenticate. Freeze Auth-Info, spec WWW-Authenticate.",
            residual="handoff: keep Authentication-Info or force WWW-Authenticate; do not claim WWW-Authenticate-only shipped",
            vs="r3569 security-mutual-tls (WWW-Authenticate leftover, not mTLS)",
            fetch1="https://www.rfc-editor.org/rfc/rfc9110.html#name-www-authenticate", fetch1_ok="WWW-Authenticate is a challenge. leftover Auth-Info is post-success.",
            fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive WWW-Authenticate 400s leftover Authentication-Info."),
    ),
    (
        ok(slug="content-location-uri", domain="content-location-vs-location-only", name="cloc", field="Content-Location",
           old="Location leftover only", new="Content-Location URI required",
           fail_err="400: leftover Location after Content-Location-only",
           plan="Content-Location-only 400s leftover Location. Abandon exclusive Content-Location; dual-read Location for one release.",
           residual="client still Location; drop after client 3",
           vs="r3578 status-202-location (Content-Location, not 202 Location)",
           fetch1="https://www.rfc-editor.org/rfc/rfc9110.html#name-content-location", fetch1_ok="Content-Location identifies the representation.",
           fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive Content-Location 400s leftover Location-only clients."),
        bad(slug="location-header-only", domain="location-vs-content-location", name="loch", field="Location",
            old="Content-Location leftover", new="Location only",
            fail_err="400: leftover Content-Location after Location-only",
            plan="Location-only 400s leftover Content-Location. Abandon exclusive Location; keep Content-Location — SPA wants Location. Freeze Content-Location, spec Location.",
            residual="handoff: keep Content-Location or force Location; do not claim Location-only shipped",
            vs="r3578 status-202-location (Location leftover vs Content-Location, not 202)",
            fetch1="https://www.rfc-editor.org/rfc/rfc9110.html#name-location", fetch1_ok="Location is for created/redirect. leftover Content-Location is identity.",
            fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive Location 400s leftover Content-Location producers."),
    ),
    (
        ok(slug="accept-ranges-bytes", domain="accept-ranges-bytes-vs-none", name="arng", field="Accept-Ranges",
           old="none leftover", new="Accept-Ranges bytes",
           fail_err="400: leftover none after bytes-only",
           plan="bytes-only 400s leftover none. Abandon exclusive bytes; dual-accept none for one release.",
           residual="CDN still none; drop after cdn 7",
           vs="wrap range-requests-206 (Accept-Ranges bytes, not 206 Range responses)",
           fetch1="https://www.rfc-editor.org/rfc/rfc9110.html#name-accept-ranges", fetch1_ok="Accept-Ranges: bytes advertises range support.",
           fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive bytes 400s leftover none advertisers."),
        bad(slug="no-accept-ranges", domain="accept-ranges-none-vs-bytes", name="nrng", field="Accept-Ranges",
            old="bytes leftover", new="Accept-Ranges none",
            fail_err="400: leftover bytes after none-only",
            plan="none-only 400s leftover bytes. Abandon exclusive none; keep bytes — media wants none. Freeze bytes, spec none.",
            residual="handoff: keep bytes or force none; do not claim none shipped",
            vs="wrap range-requests-206 (Accept-Ranges none leftover, not 206)",
            fetch1="https://www.rfc-editor.org/rfc/rfc9110.html#name-accept-ranges", fetch1_ok="none means ranges are not supported.",
            fetch2=f"{OAS}#header-object", fetch2_ok="Exclusive none 400s leftover bytes clients."),
    ),
    (
        ok(slug="json-schema-vocabulary", domain="json-schema-vocabulary-vs-draft07-keywords", name="vocab", field="$vocabulary",
           old="draft-07 leftover keywords", new="$vocabulary 2020-12 required",
           fail_err="400: leftover draft-07 after vocabulary-only",
           plan="vocabulary-only 400s leftover draft-07. Abandon exclusive $vocabulary; dual-accept draft-07 keywords for one release.",
           residual="generator still draft-07; drop after gen 5",
           vs="r3561 json-schema-dialect-uri ($vocabulary, not jsonSchemaDialect URI)",
           fetch1=f"{JS}/schema.html#vocabulary", fetch1_ok="$vocabulary declares keyword vocabularies. leftover draft-07 has none.",
           fetch2=f"{OAS}#schema-object", fetch2_ok="Exclusive $vocabulary 400s leftover draft-07 documents."),
        bad(slug="draft07-keywords", domain="draft07-keywords-vs-vocabulary", name="d07kw", field="definitions",
            old="$vocabulary leftover", new="draft-07 definitions only",
            fail_err="400: leftover $vocabulary after draft-07-only",
            plan="draft-07-only 400s leftover $vocabulary. Abandon exclusive draft-07; keep $vocabulary — legacy wants draft-07. Freeze $vocabulary, spec draft-07.",
            residual="handoff: keep $vocabulary or force draft-07; do not claim draft-07-only shipped",
            vs="r3561 json-schema-dialect-uri (draft-07 leftover, not jsonSchemaDialect)",
            fetch1="https://json-schema.org/draft-07/json-schema-core.html", fetch1_ok="draft-07 uses definitions. leftover $vocabulary is 2019-09+.",
            fetch2=f"{OAS}#schema-object", fetch2_ok="Exclusive draft-07 400s leftover $vocabulary documents."),
    ),
    (
        ok(slug="json-schema-comment", domain="json-schema-comment-vs-description-only", name="jcom", field="$comment",
           old="description leftover only", new="$comment required",
           fail_err="400: leftover description-only after $comment-only",
           plan="$comment-only 400s leftover description. Abandon exclusive $comment; dual-read description for one release.",
           residual="docs still description; drop after docs 2",
           vs="r3572 examples-plural-keyword ($comment, not examples)",
           fetch1=f"{JS}/generic.html#comment", fetch1_ok="$comment is for implementers. leftover description is user-facing.",
           fetch2=f"{OAS}#schema-object", fetch2_ok="Exclusive $comment 400s leftover description-only schemas."),
        bad(slug="description-only-schema", domain="description-only-vs-comment", name="desco", field="description",
            old="$comment leftover", new="description only",
            fail_err="400: leftover $comment after description-only",
            plan="description-only 400s leftover $comment. Abandon exclusive description; keep $comment — portal wants description. Freeze $comment, spec description.",
            residual="handoff: keep $comment or force description; do not claim description-only shipped",
            vs="r3572 examples-plural-keyword (description leftover, not examples)",
            fetch1=f"{JS}/generic.html#annotation", fetch1_ok="description is user annotation. leftover $comment is implementer-only.",
            fetch2=f"{OAS}#schema-object", fetch2_ok="Exclusive description 400s leftover $comment producers."),
    ),
    (
        ok(slug="json-schema-else", domain="json-schema-else-vs-if-then-no-else", name="jelse", field="else",
           old="if/then leftover no else", new="else subschema required",
           fail_err="400: leftover if/then-no-else after else-required",
           plan="else-required 400s leftover if/then. Abandon exclusive else; dual-accept missing else for one release.",
           residual="tax still no else; drop after tax 4",
           vs="r3561 json-schema-if-then-else (else required vs missing else, not if/then VAT)",
           fetch1=f"{JS}/conditionals.html", fetch1_ok="else applies when if fails. leftover if/then without else is different.",
           fetch2=f"{OAS}#schema-object", fetch2_ok="Exclusive else 400s leftover if/then-only schemas."),
        bad(slug="if-then-no-else", domain="if-then-no-else-vs-else-required", name="ithen", field="then",
            old="else leftover subschema", new="if/then no else",
            fail_err="400: leftover else after if/then-only",
            plan="if/then-only 400s leftover else. Abandon exclusive if/then; keep else — rules want if/then. Freeze else, spec if/then.",
            residual="handoff: keep else or force if/then-only; do not claim if/then-only shipped",
            vs="r3561 json-schema-if-then-else (if/then leftover without else, not VAT if/then)",
            fetch1=f"{JS}/conditionals.html", fetch1_ok="if/then without else leaves non-matching instances unconstrained.",
            fetch2=f"{OAS}#schema-object", fetch2_ok="Exclusive if/then 400s leftover else producers."),
    ),
    (
        ok(slug="json-schema-contains", domain="json-schema-contains-vs-items-only", name="jcon", field="contains",
           old="items leftover only", new="contains required element",
           fail_err="400: leftover items-only after contains-only",
           plan="contains-only 400s leftover items-only. Abandon exclusive contains; dual-accept items-only arrays for one release.",
           residual="feed still items-only; drop after feed 3",
           vs="r3561 json-schema-maxcontains (contains required, not maxContains)",
           fetch1=f"{JS}/array.html#contains", fetch1_ok="contains requires at least one matching item.",
           fetch2=f"{OAS}#schema-object", fetch2_ok="Exclusive contains 400s leftover items-only arrays."),
        bad(slug="items-only-array", domain="items-only-vs-contains", name="itemo", field="items",
            old="contains leftover", new="items only",
            fail_err="400: leftover contains after items-only",
            plan="items-only 400s leftover contains. Abandon exclusive items; keep contains — catalog wants items. Freeze contains, spec items.",
            residual="handoff: keep contains or force items-only; do not claim items-only shipped",
            vs="r3561 json-schema-maxcontains (items-only leftover, not maxContains)",
            fetch1=f"{JS}/array.html#items", fetch1_ok="items schemas every element. leftover contains is existential.",
            fetch2=f"{OAS}#schema-object", fetch2_ok="Exclusive items 400s leftover contains producers."),
    ),
    (
        ok(slug="exclusive-maximum-numeric", domain="exclusive-maximum-number-oas31", name="emax", field="cap",
           old="maximum leftover inclusive", new="exclusiveMaximum: 100",
           fail_err="400: leftover 100 after exclusiveMaximum 100",
           plan="exclusiveMaximum-only 400s leftover inclusive 100. Abandon exclusive exclusiveMaximum; dual-accept 100 for one release.",
           residual="CSV still 100; drop after csv 2",
           vs="r3562 exclusive-minimum-numeric (exclusiveMaximum, not exclusiveMinimum)",
           fetch1=f"{JS}/numeric.html#range", fetch1_ok="exclusiveMaximum 100 rejects 100. leftover maximum 100 accepts 100.",
           fetch2=f"{OAS}#data-types", fetch2_ok="OAS 3.1 numeric exclusiveMaximum is not OAS 3.0 boolean."),
        bad(slug="maximum-inclusive", domain="maximum-inclusive-vs-exclusive-maximum", name="maxin", field="cap",
            old="exclusiveMaximum leftover", new="maximum: 100 inclusive",
            fail_err="400: leftover exclusiveMaximum after maximum-only",
            plan="maximum-only 400s leftover exclusiveMaximum. Abandon exclusive maximum; keep exclusiveMaximum — billing wants maximum. Freeze exclusiveMaximum, spec maximum.",
            residual="handoff: keep exclusiveMaximum or force maximum; do not claim maximum-only shipped",
            vs="r3562 exclusive-minimum-numeric (inclusive maximum leftover, not exclusiveMinimum)",
            fetch1=f"{JS}/numeric.html#range", fetch1_ok="maximum is inclusive. leftover exclusiveMaximum rejects the bound.",
            fetch2=f"{OAS}#data-types", fetch2_ok="Exclusive maximum 400s leftover exclusiveMaximum producers."),
    ),
    (
        ok(slug="type-integer-vs-number", domain="type-integer-vs-number-leftover", name="tint", field="count",
           old="number leftover", new="type integer",
           fail_err="400: leftover 1.5 after integer-only",
           plan="integer-only 400s leftover number. Abandon exclusive integer; dual-accept number and floor for one release.",
           residual="report still number; drop after report 6",
           vs="r3581 int64-as-string-js (type integer vs number, not int64 string)",
           fetch1=f"{JS}/numeric.html#integer", fetch1_ok="integer rejects non-integral numbers. leftover type number accepts 1.5.",
           fetch2=f"{OAS}#data-types", fetch2_ok="Exclusive integer 400s leftover number clients."),
        bad(slug="number-leftover", domain="type-number-vs-integer", name="tnum", field="count",
            old="integer leftover", new="type number",
            fail_err="400: leftover integer-only after number-only",
            plan="number-only 400s leftover integer-only clients that stringify. Abandon exclusive number; keep integer — analytics wants number. Freeze integer, spec number.",
            residual="handoff: keep integer or force number; do not claim number-only shipped",
            vs="r3581 int64-as-string-js (type number leftover, not int64 string)",
            fetch1=f"{JS}/numeric.html", fetch1_ok="number allows floats. leftover integer-only serializers may reject floats.",
            fetch2=f"{OAS}#data-types", fetch2_ok="Exclusive number 400s leftover integer producers."),
    ),
    (
        ok(slug="pipe-delimited-query", domain="pipe-delimited-query-vs-comma", name="pipeq", field="ids",
           old="comma leftover form", new="style pipeDelimited",
           fail_err="400: leftover comma after pipeDelimited-only",
           plan="pipeDelimited-only 400s leftover comma. Abandon exclusive pipes; dual-read comma for one release.",
           residual="SDK still comma; drop after sdk 4",
           vs="wrap form-space-delimited (pipeDelimited query, not spaceDelimited)",
           fetch1=f"{OAS}#style-values", fetch1_ok="pipeDelimited joins with |. leftover comma form is a different style.",
           fetch2=f"{OAS}#parameter-object", fetch2_ok="Exclusive pipeDelimited 400s leftover comma clients."),
        bad(slug="comma-delimited-leftover", domain="comma-form-vs-pipe-delimited", name="commaq", field="ids",
            old="pipe leftover", new="comma form only",
            fail_err="400: leftover pipes after comma-only",
            plan="comma-only 400s leftover pipes. Abandon exclusive comma; keep pipes — filter wants comma. Freeze pipes, spec comma.",
            residual="handoff: keep pipes or force comma; do not claim comma-only shipped",
            vs="wrap form-space-delimited (comma form leftover, not spaceDelimited)",
            fetch1=f"{OAS}#style-values", fetch1_ok="form style default explode false uses comma. leftover pipes fail comma-only.",
            fetch2=f"{OAS}#parameter-object", fetch2_ok="Exclusive comma 400s leftover pipeDelimited producers."),
    ),
    (
        ok(slug="json-schema-minitems", domain="minitems-vs-empty-array-ok", name="mini", field="tags",
           old="empty array leftover ok", new="minItems 1",
           fail_err="400: leftover [] after minItems-1",
           plan="minItems-only 400s leftover []. Abandon exclusive minItems 1; dual-accept empty for one release.",
           residual="import still []; drop after import 2",
           vs="wrap mincontains-role (minItems, not minContains)",
           fetch1=f"{JS}/array.html#length", fetch1_ok="minItems 1 rejects empty arrays.",
           fetch2=f"{OAS}#schema-object", fetch2_ok="Exclusive minItems 400s leftover empty arrays."),
        bad(slug="empty-array-ok", domain="empty-array-vs-minitems", name="earrok", field="tags",
            old="minItems leftover 1", new="empty array allowed",
            fail_err="400: leftover minItems after empty-ok",
            plan="empty-ok 400s leftover minItems. Abandon exclusive empty; keep minItems — catalog wants empty. Freeze minItems, spec empty-ok.",
            residual="handoff: keep minItems or force empty-ok; do not claim empty-ok shipped",
            vs="wrap mincontains-role (empty array leftover, not minContains)",
            fetch1=f"{JS}/array.html#length", fetch1_ok="Unconstrained arrays allow []. leftover minItems 1 fails empty-ok.",
            fetch2=f"{OAS}#schema-object", fetch2_ok="Exclusive empty-ok 400s leftover minItems producers."),
    ),
    (
        ok(slug="json-schema-maxitems", domain="maxitems-vs-unbounded-array", name="maxi", field="tags",
           old="unbounded leftover", new="maxItems 8",
           fail_err="400: leftover 12 tags after maxItems-8",
           plan="maxItems-only 400s leftover unbounded. Abandon exclusive maxItems; dual-accept >8 and truncate for one release.",
           residual="bulk still unbounded; drop after bulk 5",
           vs="wrap uniqueitems-sku (maxItems, not uniqueItems)",
           fetch1=f"{JS}/array.html#length", fetch1_ok="maxItems 8 rejects longer arrays.",
           fetch2=f"{OAS}#schema-object", fetch2_ok="Exclusive maxItems 400s leftover unbounded clients."),
        bad(slug="unbounded-array", domain="unbounded-array-vs-maxitems", name="unbnda", field="tags",
            old="maxItems leftover 8", new="unbounded array",
            fail_err="400: leftover maxItems after unbounded-only",
            plan="unbounded-only 400s leftover maxItems. Abandon exclusive unbounded; keep maxItems — search wants unbounded. Freeze maxItems, spec unbounded.",
            residual="handoff: keep maxItems or force unbounded; do not claim unbounded shipped",
            vs="wrap uniqueitems-sku (unbounded leftover, not uniqueItems)",
            fetch1=f"{JS}/array.html#length", fetch1_ok="No maxItems means unbounded. leftover maxItems 8 fails unbounded-only.",
            fetch2=f"{OAS}#schema-object", fetch2_ok="Exclusive unbounded 400s leftover maxItems producers."),
    ),
    (
        ok(slug="head-no-body", domain="head-method-no-body-vs-get-body", name="hdnb", field="HEAD",
           old="GET leftover body on HEAD", new="HEAD no body required",
           fail_err="400: leftover body after HEAD-no-body",
           plan="HEAD-no-body 400s leftover GET body. Abandon exclusive empty; dual-accept framed bodies for one release then strip.",
           residual="proxy still copies GET body; drop after proxy 1",
           vs="r3578 status-204-no-body (HEAD empty body, not 204)",
           fetch1="https://www.rfc-editor.org/rfc/rfc9110.html#name-head", fetch1_ok="HEAD must not include a content body.",
           fetch2=f"{OAS}#operation-object", fetch2_ok="Exclusive HEAD no-body 400s leftover body-on-HEAD."),
        bad(slug="get-body-on-head", domain="get-body-on-head-vs-head-no-body", name="gethd", field="HEAD",
            old="empty leftover HEAD", new="GET body copied on HEAD",
            fail_err="400: leftover empty HEAD after body-copy-only",
            plan="body-copy-only 400s leftover empty HEAD. Abandon exclusive copy; keep empty — cache wants copy. Freeze empty, spec copy.",
            residual="handoff: keep empty HEAD or force body copy; do not claim body-on-HEAD shipped",
            vs="r3578 status-204-no-body (GET body on HEAD leftover, not 204)",
            fetch1="https://www.rfc-editor.org/rfc/rfc9110.html#name-head", fetch1_ok="Copying GET bodies onto HEAD violates HEAD.",
            fetch2=f"{OAS}#operation-object", fetch2_ok="Exclusive copy 400s leftover empty HEAD producers."),
    ),
]


def catalog_selfcheck() -> None:
    seen: set[str] = set()
    if len(PAIRS) < 20:
        raise SystemExit(f"catalog too small: {len(PAIRS)}")
    existing = published_slugs()
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
            if any(n.lower() in slug or n.lower() in spec["domain"] for n in BANNED_SLUG_NEEDLES):
                raise SystemExit(f"banned needle in {slug} / {spec['domain']}")
            if "variant v" in spec["plan_change"].lower():
                raise SystemExit(f"wrap tag leaked in {slug}")
            if len("Reflection: " + spec["plan_change"]) > 240:
                raise SystemExit(f"plan_change too long for {slug}: {len('Reflection: ' + spec['plan_change'])}")


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
        assert "sim_or_real" not in e
        for s in e["steps"]:
            assert 1 <= len(s["decision_basis"]) <= 240
    batch = staging / f"batch-r{round_n:02d}.jsonl"
    notes = staging / f"NOTES-r{round_n:02d}.md"
    batch.write_text(json.dumps(e1, ensure_ascii=False) + "\n" + json.dumps(e2, ensure_ascii=False) + "\n")
    notes.write_text(notes_text(round_n, [e1, e2], [t1, t2], idx))
    print(json.dumps({"round": round_n, "idx": idx, "ids": [e1["id"], e2["id"]], "catalog": "g46-w2"}))


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
