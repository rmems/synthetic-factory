#!/usr/bin/env python3
"""Fourth leftover unique ACM catalog after r3561/r3620/r3667.

BAN wrap w131 cartesian, r3560 422-vs-400 / 207-multistatus, r3614–r3629 clones,
r3694–r3697 clones, prior leftover slugs.
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
build_episode = _b.build_episode
notes_text = _b.notes_text
published_slugs = _b.published_slugs

_spec2 = importlib.util.spec_from_file_location("acm_mill_r3620", HERE / "acm-mill-r3620.py")
_c = importlib.util.module_from_spec(_spec2)
assert _spec2.loader is not None
_spec2.loader.exec_module(_c)

_spec3 = importlib.util.spec_from_file_location("acm_mill_r3667", HERE / "acm-mill-r3667.py")
_d = importlib.util.module_from_spec(_spec3)
assert _spec3.loader is not None
_spec3.loader.exec_module(_d)

BANNED_PRIOR = (
    {p[0]["slug"] for p in _b.PAIRS}
    | {p[1]["slug"] for p in _b.PAIRS}
    | {p[0]["slug"] for p in _c.PAIRS}
    | {p[1]["slug"] for p in _c.PAIRS}
    | {p[0]["slug"] for p in _d.PAIRS}
    | {p[1]["slug"] for p in _d.PAIRS}
)

PAIRS: list[tuple[dict, dict]] = [
    (
        plant(
            slug="asyncapi3-opid-channel",
            domain="asyncapi3-vs-oas31-same-opid",
            success=True,
            name="a3opid",
            stack="AsyncAPI 3.0 + OpenAPI 3.1 + Go",
            field="operationId",
            old="OpenAPI leftover HTTP op",
            new="AsyncAPI 3 channel send same opId",
            fail_err="400: leftover HTTP GET after AsyncAPI-only same operationId",
            plan="AsyncAPI-only 400s leftover HTTP. Abandon exclusive channel; dual-bind HTTP GET for one release.",
            residual="REST SDK still HTTP; drop after sdk 3",
            vs="r3614 OAS 3.1 $ref siblings (same operationId across AsyncAPI 3 vs OAS 3.1 leftover, not $ref)",
            fetch1="https://www.asyncapi.com/docs/reference/specification/v3.0.0#operationObject",
            fetch1_ok="AsyncAPI 3 operations live on channels. leftover OpenAPI operationId is HTTP.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#operation-object",
            fetch2_ok="Sharing operationId without dual-read 400s leftover HTTP clients.",
        ),
        plant(
            slug="oas31-opid-http-leftover",
            domain="oas31-opid-http-vs-async",
            success=False,
            name="o31opid",
            stack="OpenAPI 3.1 + Java + TS",
            field="operationId",
            old="AsyncAPI leftover channel",
            new="OpenAPI 3.1 HTTP only same opId",
            fail_err="SDK unknown channel; leftover AsyncAPI bind after HTTP-only",
            plan="HTTP-only 400s leftover channel. Abandon exclusive HTTP; keep channel — gateway wants HTTP. Freeze channel, spec HTTP.",
            residual="handoff: keep channel or force HTTP; do not claim HTTP-only shipped",
            vs="r3614 OAS 3.1 $ref siblings (HTTP leftover vs AsyncAPI 3 same opId, not $ref)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#operation-object",
            fetch1_ok="OpenAPI 3.1 operationId is HTTP. leftover AsyncAPI channel is a different bind.",
            fetch2="https://www.asyncapi.com/docs/reference/specification/v3.0.0#operationObject",
            fetch2_ok="Exclusive HTTP same opId breaks leftover channel SDKs.",
        ),
    ),
    (
        plant(
            slug="cloudevents-structured-mode",
            domain="cloudevents-vs-unsigned-webhook",
            success=True,
            name="cebin",
            stack="CloudEvents 1.0 + Go + Python",
            field="ce-type",
            old="unsigned leftover webhook JSON",
            new="CloudEvents structured mode required",
            fail_err="400: leftover unsigned webhook after CloudEvents-only",
            plan="CE-only 400s leftover unsigned. Abandon exclusive CE; accept unsigned and wrap CloudEvents for one release.",
            residual="partner still unsigned; drop after partner 2",
            vs="r3614 unsigned webhook clones / NEL (CloudEvents leftover vs unsigned, not NEL)",
            fetch1="https://github.com/cloudevents/spec/blob/v1.0.2/cloudevents/spec.md",
            fetch1_ok="CloudEvents structured mode requires specversion/type/source/id. leftover unsigned webhooks omit them.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object",
            fetch2_ok="Exclusive CloudEvents 400s leftover unsigned webhook bodies.",
        ),
        plant(
            slug="unsigned-webhook-hmac-absent",
            domain="unsigned-webhook-vs-cloudevents",
            success=False,
            name="unhook",
            stack="OpenAPI 3.1 + Java + TS",
            field="X-Hub-Signature",
            old="CloudEvents leftover signed envelope",
            new="unsigned JSON webhook only",
            fail_err="400: leftover CloudEvents after unsigned-only",
            plan="unsigned-only 400s leftover CE. Abandon exclusive unsigned; keep CE — product wants unsigned. Freeze CE, spec unsigned.",
            residual="handoff: keep CE or force unsigned; do not claim unsigned shipped",
            vs="r3614 NEL / CSP report-to (unsigned webhook leftover, not NEL)",
            fetch1="https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries",
            fetch1_ok="Unsigned webhooks have no ce-type. leftover CloudEvents envelopes fail unsigned parsers.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#header-object",
            fetch2_ok="Dropping CloudEvents without dual-read 400s leftover CE producers.",
        ),
    ),
    (
        plant(
            slug="jsonapi-resource-object",
            domain="jsonapi-vs-hal-leftover",
            success=True,
            name="japi",
            stack="JSON:API 1.1 + Go + Python",
            field="data",
            old="HAL leftover _links",
            new="JSON:API data+type+id required",
            fail_err="400: leftover _links after JSON:API-only",
            plan="JSON:API-only 400s leftover HAL. Abandon exclusive data; dual-read _links for one release.",
            residual="SPA still HAL; drop after spa 4",
            vs="r3614 Collection+JSON (JSON:API leftover vs HAL, not Collection+JSON)",
            fetch1="https://jsonapi.org/format/#document-resource-objects",
            fetch1_ok="JSON:API resources use data type id. leftover HAL uses _links/_embedded.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object",
            fetch2_ok="Exclusive application/vnd.api+json 415s leftover HAL clients.",
        ),
        plant(
            slug="hal-embedded-leftover",
            domain="hal-vs-jsonapi-leftover",
            success=False,
            name="halemb",
            stack="OpenAPI 3.1 + Java + TS",
            field="_embedded",
            old="JSON:API leftover included",
            new="HAL _embedded only",
            fail_err="400: leftover included after HAL-only",
            plan="HAL-only 400s leftover included. Abandon exclusive HAL; keep included — catalog wants HAL. Freeze included, spec HAL.",
            residual="handoff: keep included or force HAL; do not claim HAL shipped",
            vs="r3614 Collection+JSON (HAL leftover vs JSON:API, not Collection+JSON)",
            fetch1="https://datatracker.ietf.org/doc/html/draft-kelly-json-hal",
            fetch1_ok="HAL uses _embedded. leftover JSON:API included is a different graph.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object",
            fetch2_ok="Exclusive HAL 415s leftover JSON:API documents.",
        ),
    ),
    (
        plant(
            slug="capnp-packed-rpc",
            domain="capnp-vs-protobuf-leftover",
            success=True,
            name="capnp",
            stack="Cap'n Proto + Go + Python",
            field="content",
            old="protobuf leftover binary",
            new="Cap'n Proto packed RPC",
            fail_err="415: leftover protobuf after capnp-only",
            plan="capnp-only 415s leftover protobuf. Abandon exclusive packed; dual-decode protobuf for one release.",
            residual="worker still protobuf; drop after worker 5",
            vs="r3614 uri-template (Cap'n Proto leftover vs protobuf, not uri-template)",
            fetch1="https://capnproto.org/encoding.html",
            fetch1_ok="Cap'n Proto packed encoding is not protobuf wire. leftover protobuf fails packed parsers.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object",
            fetch2_ok="Exclusive application/x-capnp 415s leftover protobuf bodies.",
        ),
        plant(
            slug="protobuf-wire-vs-capnp",
            domain="protobuf-vs-capnp-leftover",
            success=False,
            name="pbcap",
            stack="OpenAPI 3.1 + Java + TS",
            field="content",
            old="Cap'n Proto leftover packed",
            new="protobuf binary only",
            fail_err="415: leftover packed after protobuf-only",
            plan="protobuf-only 415s leftover packed. Abandon exclusive proto; keep packed — mesh wants proto. Freeze packed, spec proto.",
            residual="handoff: keep packed or force proto; do not claim protobuf-only shipped",
            vs="r3614 uri-template (protobuf leftover vs Cap'n Proto, not uri-template)",
            fetch1="https://protobuf.dev/programming-guides/encoding/",
            fetch1_ok="Protobuf wire is tag-length-value. leftover Cap'n Proto packed is a different layout.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object",
            fetch2_ok="Exclusive protobuf 415s leftover Cap'n Proto producers.",
        ),
    ),
    (
        plant(
            slug="flatbuffers-table-root",
            domain="flatbuffers-vs-protobuf-leftover",
            success=True,
            name="fbsroot",
            stack="FlatBuffers + Go + Python",
            field="content",
            old="protobuf leftover binary",
            new="FlatBuffers table root identifier",
            fail_err="415: leftover protobuf after fbs-only",
            plan="fbs-only 415s leftover protobuf. Abandon exclusive table; dual-decode protobuf for one release.",
            residual="edge still protobuf; drop after edge 2",
            vs="r3614 relative JSON pointer (FlatBuffers leftover vs protobuf, not JSON pointer)",
            fetch1="https://flatbuffers.dev/flatbuffers_guide_tutorial.html",
            fetch1_ok="FlatBuffers uses a file identifier and vtable. leftover protobuf is not a table root.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object",
            fetch2_ok="Exclusive application/x-flatbuffers 415s leftover protobuf.",
        ),
        plant(
            slug="protobuf-wire-vs-fbs",
            domain="protobuf-vs-flatbuffers-leftover",
            success=False,
            name="pbfbs",
            stack="OpenAPI 3.1 + Java + TS",
            field="content",
            old="FlatBuffers leftover table",
            new="protobuf binary only",
            fail_err="415: leftover table after protobuf-only",
            plan="protobuf-only 415s leftover fbs. Abandon exclusive proto; keep fbs — mobile wants proto. Freeze fbs, spec proto.",
            residual="handoff: keep fbs or force proto; do not claim protobuf-only shipped",
            vs="r3614 relative JSON pointer (protobuf leftover vs FlatBuffers, not JSON pointer)",
            fetch1="https://protobuf.dev/programming-guides/encoding/",
            fetch1_ok="Protobuf is not a FlatBuffers identifier. leftover tables fail protobuf parsers.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object",
            fetch2_ok="Exclusive protobuf 415s leftover FlatBuffers producers.",
        ),
    ),
    (
        plant(
            slug="msgpack-bin8-ext",
            domain="msgpack-vs-cbor-leftover",
            success=True,
            name="mpk",
            stack="MessagePack + Go + Python",
            field="content",
            old="CBOR leftover major-type",
            new="MessagePack bin8+ext required",
            fail_err="415: leftover CBOR after msgpack-only",
            plan="msgpack-only 415s leftover CBOR. Abandon exclusive bin8; dual-decode CBOR for one release.",
            residual="queue still CBOR; drop after queue 3",
            vs="r3697 json-seq-ldjson / r3561 application-cbor-seq (MessagePack leftover vs CBOR, not json-seq)",
            fetch1="https://github.com/msgpack/msgpack/blob/master/spec.md",
            fetch1_ok="MessagePack bin8/ext is not CBOR major types. leftover CBOR fails msgpack.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object",
            fetch2_ok="Exclusive application/msgpack 415s leftover CBOR bodies.",
        ),
        plant(
            slug="cbor-majortype-vs-msgpack",
            domain="cbor-vs-msgpack-leftover",
            success=False,
            name="cbormp",
            stack="OpenAPI 3.1 + Java + TS",
            field="content",
            old="MessagePack leftover bin8",
            new="CBOR RFC 8949 only",
            fail_err="415: leftover msgpack after CBOR-only",
            plan="CBOR-only 415s leftover msgpack. Abandon exclusive CBOR; keep msgpack — iot wants CBOR. Freeze msgpack, spec CBOR.",
            residual="handoff: keep msgpack or force CBOR; do not claim CBOR-only shipped",
            vs="r3561 application-cbor-seq (CBOR leftover vs MessagePack, not CBOR-seq)",
            fetch1="https://www.rfc-editor.org/rfc/rfc8949.html",
            fetch1_ok="CBOR major types are not MessagePack formats. leftover bin8 fails CBOR.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object",
            fetch2_ok="Exclusive application/cbor 415s leftover MessagePack producers.",
        ),
    ),
    (
        plant(
            slug="amazon-ion-binary",
            domain="ion-vs-json-leftover",
            success=True,
            name="ionbin",
            stack="Amazon Ion + Go + Python",
            field="content",
            old="JSON leftover text",
            new="Ion 1.0 binary IVM required",
            fail_err="415: leftover JSON after Ion-only",
            plan="Ion-only 415s leftover JSON. Abandon exclusive IVM; dual-read JSON for one release.",
            residual="report still JSON; drop after report 6",
            vs="r3694 twirp-error-meta (Amazon Ion leftover vs JSON, not twirp)",
            fetch1="https://amazon-ion.github.io/ion-docs/docs/binary.html",
            fetch1_ok="Ion binary starts with $ion_1_0 IVM. leftover JSON objects are not Ion binary.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object",
            fetch2_ok="Exclusive application/x-ion 415s leftover JSON.",
        ),
        plant(
            slug="json-text-vs-ion",
            domain="json-vs-ion-leftover",
            success=False,
            name="jsonion",
            stack="OpenAPI 3.1 + Java + TS",
            field="content",
            old="Ion leftover binary",
            new="application/json only",
            fail_err="415: leftover Ion after JSON-only",
            plan="JSON-only 415s leftover Ion. Abandon exclusive JSON; keep Ion — warehouse wants JSON. Freeze Ion, spec JSON.",
            residual="handoff: keep Ion or force JSON; do not claim JSON-only shipped",
            vs="r3694 twirp-error-meta (JSON leftover vs Ion, not twirp)",
            fetch1="https://www.rfc-editor.org/rfc/rfc8259.html",
            fetch1_ok="JSON text is not Ion binary. leftover IVM bytes fail JSON parsers.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object",
            fetch2_ok="Exclusive JSON 415s leftover Ion producers.",
        ),
    ),
    (
        plant(
            slug="avro-single-object-encoding",
            domain="avro-vs-protobuf-leftover",
            success=True,
            name="avrosoe",
            stack="Apache Avro + Go + Python",
            field="content",
            old="protobuf leftover binary",
            new="Avro single-object C3 01 fingerprint",
            fail_err="415: leftover protobuf after Avro-only",
            plan="Avro-only 415s leftover protobuf. Abandon exclusive SOE; dual-decode protobuf for one release.",
            residual="stream still protobuf; drop after stream 4",
            vs="r3614 $dynamicRef (Avro leftover vs protobuf, not $dynamicRef)",
            fetch1="https://avro.apache.org/docs/1.11.1/specification/#single-object-encoding",
            fetch1_ok="Avro SOE is C3 01 plus CRC-64 fingerprint. leftover protobuf is not SOE.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object",
            fetch2_ok="Exclusive avro/binary 415s leftover protobuf.",
        ),
        plant(
            slug="protobuf-wire-vs-avro",
            domain="protobuf-vs-avro-leftover",
            success=False,
            name="pbavro",
            stack="OpenAPI 3.1 + Java + TS",
            field="content",
            old="Avro leftover SOE",
            new="protobuf binary only",
            fail_err="415: leftover SOE after protobuf-only",
            plan="protobuf-only 415s leftover Avro. Abandon exclusive proto; keep Avro — kafka wants proto. Freeze Avro, spec proto.",
            residual="handoff: keep Avro or force proto; do not claim protobuf-only shipped",
            vs="r3614 $dynamicRef (protobuf leftover vs Avro, not $dynamicRef)",
            fetch1="https://protobuf.dev/programming-guides/encoding/",
            fetch1_ok="Protobuf is not Avro SOE. leftover C3 01 fails protobuf.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object",
            fetch2_ok="Exclusive protobuf 415s leftover Avro producers.",
        ),
    ),
    (
        plant(
            slug="thrift-compact-protocol",
            domain="thrift-vs-grpc-leftover",
            success=True,
            name="thc",
            stack="Apache Thrift + Go + Python",
            field="content",
            old="gRPC leftover proto+h2",
            new="Thrift compact protocol framed",
            fail_err="415: leftover gRPC after thrift-only",
            plan="thrift-only 415s leftover gRPC. Abandon exclusive compact; dual-decode gRPC for one release.",
            residual="mesh still gRPC; drop after mesh 7",
            vs="r3614 connect+proto (Thrift leftover vs gRPC, not Connect proto)",
            fetch1="https://github.com/apache/thrift/blob/master/doc/specs/thrift-compact-protocol.md",
            fetch1_ok="Thrift compact is a framed protocol. leftover gRPC protobuf+HTTP/2 is different.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object",
            fetch2_ok="Exclusive application/x-thrift 415s leftover gRPC clients.",
        ),
        plant(
            slug="grpc-proto-vs-thrift",
            domain="grpc-vs-thrift-leftover",
            success=False,
            name="grpcth",
            stack="OpenAPI 3.1 + Java + TS",
            field="content",
            old="Thrift leftover compact",
            new="gRPC application/grpc+proto",
            fail_err="415: leftover compact after gRPC-only",
            plan="gRPC-only 415s leftover thrift. Abandon exclusive gRPC; keep thrift — platform wants gRPC. Freeze thrift, spec gRPC.",
            residual="handoff: keep thrift or force gRPC; do not claim gRPC-only shipped",
            vs="r3614 connect+proto (gRPC leftover vs Thrift, not Connect)",
            fetch1="https://github.com/grpc/grpc/blob/master/doc/PROTOCOL-HTTP2.md",
            fetch1_ok="gRPC uses HTTP/2 + protobuf. leftover Thrift compact is not grpc+proto.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object",
            fetch2_ok="Exclusive gRPC 415s leftover Thrift producers.",
        ),
    ),
    (
        plant(
            slug="fhir-r5-patient-json",
            domain="fhir-r5-vs-hl7v2-leftover",
            success=True,
            name="fhir5",
            stack="FHIR R5 + Go + Python",
            field="resourceType",
            old="HL7 v2 leftover MSH|PID",
            new="FHIR R5 Patient JSON required",
            fail_err="400: leftover MSH after FHIR-only",
            plan="FHIR-only 400s leftover v2. Abandon exclusive R5; dual-read MSH|PID for one release.",
            residual="ADT still v2; drop after adt 8",
            vs="r3614 WebFinger (FHIR R5 leftover vs HL7 v2, not WebFinger)",
            fetch1="https://hl7.org/fhir/R5/patient.html",
            fetch1_ok="FHIR R5 Patient is a JSON resourceType. leftover HL7 v2 pipes are not FHIR.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object",
            fetch2_ok="Exclusive application/fhir+json 415s leftover v2 feeds.",
        ),
        plant(
            slug="hl7v2-msh-vs-fhir",
            domain="hl7v2-vs-fhir-r5-leftover",
            success=False,
            name="hl7v2",
            stack="OpenAPI 3.1 + Java + TS",
            field="MSH",
            old="FHIR leftover Patient",
            new="HL7 v2.5 MSH-12 required",
            fail_err="400: leftover Patient after v2-only",
            plan="v2-only 400s leftover FHIR. Abandon exclusive v2; keep Patient — HIS wants v2. Freeze FHIR, spec v2.",
            residual="handoff: keep FHIR or force v2; do not claim v2-only shipped",
            vs="r3614 WebFinger (HL7 v2 leftover vs FHIR R5, not WebFinger)",
            fetch1="https://www.hl7.org/implement/standards/product_brief.cfm?product_id=185",
            fetch1_ok="HL7 v2 is MSH-delimited. leftover FHIR JSON is a different clinical contract.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object",
            fetch2_ok="Exclusive x-application/hl7-v2+er7 415s leftover FHIR.",
        ),
    ),
    (
        plant(
            slug="edn-tagged-element",
            domain="edn-vs-transit-leftover",
            success=True,
            name="edntag",
            stack="EDN + Go + Python",
            field="content",
            old="Transit leftover json",
            new="EDN tagged #inst required",
            fail_err="415: leftover Transit after EDN-only",
            plan="EDN-only 415s leftover Transit. Abandon exclusive tagged; dual-read Transit for one release.",
            residual="clj still Transit; drop after clj 2",
            vs="r3695 xml-rpc-method-call (EDN leftover vs Transit, not XML-RPC)",
            fetch1="https://github.com/edn-format/edn",
            fetch1_ok="EDN tagged elements are not Transit. leftover ~# maps fail EDN readers.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object",
            fetch2_ok="Exclusive application/edn 415s leftover Transit.",
        ),
        plant(
            slug="transit-json-vs-edn",
            domain="transit-vs-edn-leftover",
            success=False,
            name="trjedn",
            stack="OpenAPI 3.1 + Java + TS",
            field="content",
            old="EDN leftover tagged",
            new="Transit-JSON only",
            fail_err="415: leftover EDN after Transit-only",
            plan="Transit-only 415s leftover EDN. Abandon exclusive Transit; keep EDN — service wants Transit. Freeze EDN, spec Transit.",
            residual="handoff: keep EDN or force Transit; do not claim Transit shipped",
            vs="r3695 xml-rpc-method-call (Transit leftover vs EDN, not XML-RPC)",
            fetch1="https://github.com/cognitect/transit-format",
            fetch1_ok="Transit-JSON uses tagged maps. leftover EDN tagged forms fail Transit.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object",
            fetch2_ok="Exclusive application/transit+json 415s leftover EDN.",
        ),
    ),
    (
        plant(
            slug="bson-document-subtype",
            domain="bson-vs-json-leftover",
            success=True,
            name="bsondoc",
            stack="BSON + Go + Python",
            field="content",
            old="JSON leftover text",
            new="BSON document subtype 0x00",
            fail_err="415: leftover JSON after BSON-only",
            plan="BSON-only 415s leftover JSON. Abandon exclusive BSON; dual-read JSON for one release.",
            residual="admin still JSON; drop after admin 3",
            vs="r3694 twirp-error-meta (BSON leftover vs JSON, not twirp)",
            fetch1="https://bsonspec.org/spec.html",
            fetch1_ok="BSON is a length-prefixed document. leftover JSON text is not BSON.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object",
            fetch2_ok="Exclusive application/bson 415s leftover JSON.",
        ),
        plant(
            slug="json-text-vs-bson",
            domain="json-vs-bson-leftover",
            success=False,
            name="jsonbs",
            stack="OpenAPI 3.1 + Java + TS",
            field="content",
            old="BSON leftover document",
            new="application/json only",
            fail_err="415: leftover BSON after JSON-only",
            plan="JSON-only 415s leftover BSON. Abandon exclusive JSON; keep BSON — mongo wants JSON. Freeze BSON, spec JSON.",
            residual="handoff: keep BSON or force JSON; do not claim JSON-only shipped",
            vs="r3694 twirp-error-meta (JSON leftover vs BSON, not twirp)",
            fetch1="https://www.rfc-editor.org/rfc/rfc8259.html",
            fetch1_ok="JSON text is not BSON. leftover length-prefixed docs fail JSON parsers.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object",
            fetch2_ok="Exclusive JSON 415s leftover BSON producers.",
        ),
    ),
    (
        plant(
            slug="yaml11-yes-bool",
            domain="yaml11-vs-yaml12-leftover",
            success=True,
            name="y11yes",
            stack="YAML 1.1 + Go + Python",
            field="enabled",
            old="YAML 1.2 leftover true-only",
            new="YAML 1.1 yes/on bool",
            fail_err="400: leftover true-only after yaml11-yes-only",
            plan="yaml11-only 400s leftover 1.2 true. Abandon exclusive yes; dual-read true for one release.",
            residual="helm still 1.2; drop after helm 1",
            vs="r3614 OAS 3.1 $ref siblings (YAML 1.1 leftover vs 1.2, not $ref)",
            fetch1="https://yaml.org/type/bool.html",
            fetch1_ok="YAML 1.1 bool includes yes/on. leftover YAML 1.2 true-only is a different schema.",
            fetch2="https://yaml.org/spec/1.2.2/",
            fetch2_ok="Switching 1.2 true-only to 1.1 yes without dual-read is breaking.",
        ),
        plant(
            slug="yaml12-true-only",
            domain="yaml12-vs-yaml11-leftover",
            success=False,
            name="y12true",
            stack="OpenAPI 3.1 + Java + TS",
            field="enabled",
            old="YAML 1.1 leftover yes",
            new="YAML 1.2 true/false only",
            fail_err="400: leftover yes after yaml12-true-only",
            plan="yaml12-only 400s leftover yes. Abandon exclusive 1.2; keep yes — k8s wants 1.2. Freeze yes, spec 1.2.",
            residual="handoff: keep yes or force true; do not claim yaml12 shipped",
            vs="r3614 OAS 3.1 $ref siblings (YAML 1.2 leftover vs 1.1, not $ref)",
            fetch1="https://yaml.org/spec/1.2.2/#1022-tag-resolution",
            fetch1_ok="YAML 1.2 JSON schema bool is true/false. leftover yes is not JSON-compatible.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types",
            fetch2_ok="Exclusive 1.2 true 400s leftover YAML 1.1 yes values.",
        ),
    ),
    (
        plant(
            slug="toml-inline-table",
            domain="toml-vs-json-leftover",
            success=True,
            name="tomlin",
            stack="TOML 1.0 + Go + Python",
            field="content",
            old="JSON leftover object",
            new="TOML inline table required",
            fail_err="415: leftover JSON after TOML-only",
            plan="TOML-only 415s leftover JSON. Abandon exclusive TOML; dual-read JSON for one release.",
            residual="cfg still JSON; drop after cfg 2",
            vs="r3694 twirp-error-meta (TOML leftover vs JSON, not twirp)",
            fetch1="https://toml.io/en/v1.0.0#inline-table",
            fetch1_ok="TOML inline tables are not JSON objects. leftover JSON fails TOML.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object",
            fetch2_ok="Exclusive application/toml 415s leftover JSON configs.",
        ),
        plant(
            slug="json-object-vs-toml",
            domain="json-vs-toml-leftover",
            success=False,
            name="jsontm",
            stack="OpenAPI 3.1 + Java + TS",
            field="content",
            old="TOML leftover table",
            new="application/json only",
            fail_err="415: leftover TOML after JSON-only",
            plan="JSON-only 415s leftover TOML. Abandon exclusive JSON; keep TOML — ops wants JSON. Freeze TOML, spec JSON.",
            residual="handoff: keep TOML or force JSON; do not claim JSON-only shipped",
            vs="r3694 twirp-error-meta (JSON leftover vs TOML, not twirp)",
            fetch1="https://www.rfc-editor.org/rfc/rfc8259.html",
            fetch1_ok="JSON objects are not TOML tables. leftover key = value fails JSON.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object",
            fetch2_ok="Exclusive JSON 415s leftover TOML producers.",
        ),
    ),
    (
        plant(
            slug="hocon-substitution",
            domain="hocon-vs-json-leftover",
            success=True,
            name="hocsub",
            stack="HOCON + Go + Python",
            field="content",
            old="JSON leftover object",
            new="HOCON ${?} substitution required",
            fail_err="415: leftover JSON after HOCON-only",
            plan="HOCON-only 415s leftover JSON. Abandon exclusive HOCON; dual-read JSON for one release.",
            residual="svc still JSON; drop after svc 5",
            vs="r3694 twirp-error-meta (HOCON leftover vs JSON, not twirp)",
            fetch1="https://github.com/lightbend/config/blob/main/HOCON.md#substitutions",
            fetch1_ok="HOCON substitutions are not JSON. leftover JSON objects fail ${} resolution.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object",
            fetch2_ok="Exclusive application/hocon 415s leftover JSON.",
        ),
        plant(
            slug="json-object-vs-hocon",
            domain="json-vs-hocon-leftover",
            success=False,
            name="jsonhc",
            stack="OpenAPI 3.1 + Java + TS",
            field="content",
            old="HOCON leftover substitution",
            new="application/json only",
            fail_err="415: leftover HOCON after JSON-only",
            plan="JSON-only 415s leftover HOCON. Abandon exclusive JSON; keep HOCON — akka wants JSON. Freeze HOCON, spec JSON.",
            residual="handoff: keep HOCON or force JSON; do not claim JSON-only shipped",
            vs="r3694 twirp-error-meta (JSON leftover vs HOCON, not twirp)",
            fetch1="https://www.rfc-editor.org/rfc/rfc8259.html",
            fetch1_ok="JSON has no ${} substitutions. leftover HOCON fails JSON parsers.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object",
            fetch2_ok="Exclusive JSON 415s leftover HOCON producers.",
        ),
    ),
    (
        plant(
            slug="smile-binary-json",
            domain="smile-vs-cbor-leftover",
            success=True,
            name="smile1",
            stack="Jackson Smile + Go + Python",
            field="content",
            old="CBOR leftover major-type",
            new="Smile :)+ binary JSON header",
            fail_err="415: leftover CBOR after Smile-only",
            plan="Smile-only 415s leftover CBOR. Abandon exclusive Smile; dual-decode CBOR for one release.",
            residual="bus still CBOR; drop after bus 4",
            vs="r3561 application-cbor-seq (Smile leftover vs CBOR, not CBOR-seq)",
            fetch1="https://github.com/FasterXML/smile-format-specification",
            fetch1_ok="Smile starts with colon-paren-plus header. leftover CBOR is not Smile.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object",
            fetch2_ok="Exclusive application/x-jackson-smile 415s leftover CBOR.",
        ),
        plant(
            slug="cbor-majortype-vs-smile",
            domain="cbor-vs-smile-leftover",
            success=False,
            name="cborsm",
            stack="OpenAPI 3.1 + Java + TS",
            field="content",
            old="Smile leftover header",
            new="CBOR RFC 8949 only",
            fail_err="415: leftover Smile after CBOR-only",
            plan="CBOR-only 415s leftover Smile. Abandon exclusive CBOR; keep Smile — kafka wants CBOR. Freeze Smile, spec CBOR.",
            residual="handoff: keep Smile or force CBOR; do not claim CBOR-only shipped",
            vs="r3561 application-cbor-seq (CBOR leftover vs Smile, not CBOR-seq)",
            fetch1="https://www.rfc-editor.org/rfc/rfc8949.html",
            fetch1_ok="CBOR is not Smile :)+. leftover Smile headers fail CBOR.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object",
            fetch2_ok="Exclusive application/cbor 415s leftover Smile producers.",
        ),
    ),
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
    batch = staging / f"batch-r{round_n:02d}.jsonl"
    notes = staging / f"NOTES-r{round_n:02d}.md"
    batch.write_text(json.dumps(e1, ensure_ascii=False) + "\n" + json.dumps(e2, ensure_ascii=False) + "\n")
    notes.write_text(notes_text(round_n, [e1, e2], [t1, t2], idx))
    print(json.dumps({"round": round_n, "idx": idx, "ids": [e1["id"], e2["id"]], "catalog": "r3698"}))


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
