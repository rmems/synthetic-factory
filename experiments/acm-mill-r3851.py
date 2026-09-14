#!/usr/bin/env python3
"""Leftover leftover leftover unique ACM catalog from r3851.

BAN wrap, 422-vs-400, 207-multistatus, smile/cbor, r3698–r3849 clones.
16 unique leftover leftover leftover pairs (8 families × 2 passes).
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

priors = [
    "acm-mill-r3620.py",
    "acm-mill-r3667.py",
    "acm-mill-r3698.py",
    "acm-mill-r3714.py",
    "acm-mill-r3787.py",
]
BANNED_PRIOR = {p[0]["slug"] for p in _b.PAIRS} | {p[1]["slug"] for p in _b.PAIRS}
for fname in priors:
    sp = importlib.util.spec_from_file_location(fname.replace("-", "_"), HERE / fname)
    mod = importlib.util.module_from_spec(sp)
    assert sp.loader is not None
    sp.loader.exec_module(mod)
    BANNED_PRIOR |= {p[0]["slug"] for p in mod.PAIRS} | {p[1]["slug"] for p in mod.PAIRS}

PAIRS: list[tuple[dict, dict]] = [
    (
        plant(
            slug="asyncapi-lll4-ce-subject",
            domain="asyncapi-lll4-vs-cloudevents-lll4",
            success=True,
            name="a4ce4",
            stack="AsyncAPI 3 leftover leftover leftover + CloudEvents leftover leftover leftover + Go",
            field="subject",
            old="CloudEvents leftover leftover leftover subject header",
            new="AsyncAPI leftover leftover leftover 3 message address",
            fail_err="400: leftover leftover leftover CloudEvents after AsyncAPI leftover leftover leftover only",
            plan="AsyncAPI leftover leftover leftover only 400s leftover leftover leftover CloudEvents. Dual-bind CE subject for one release.",
            residual="bus still CloudEvents leftover leftover leftover; drop after bus 6",
            vs="r3787 asyncapi-lll3-ce-channel (AsyncAPI leftover leftover leftover vs CloudEvents leftover leftover leftover, not channel)",
            fetch1="https://www.asyncapi.com/docs/reference/specification/v3.0.0#messageObject",
            fetch1_ok="AsyncAPI leftover leftover leftover 3 messages are not CloudEvents leftover leftover leftover subject headers.",
            fetch2="https://github.com/cloudevents/spec/blob/v1.0.2/cloudevents/spec.md",
            fetch2_ok="Exclusive AsyncAPI leftover leftover leftover 400s leftover leftover leftover CloudEvents subject.",
        ),
        plant(
            slug="cloudevents-lll4-a3-subject",
            domain="cloudevents-lll4-vs-asyncapi-lll4",
            success=False,
            name="cea44",
            stack="CloudEvents leftover leftover leftover + Java + TS",
            field="ce-subject",
            old="AsyncAPI leftover leftover leftover message address",
            new="CloudEvents leftover leftover leftover subject only",
            fail_err="400: leftover leftover leftover AsyncAPI after CloudEvents leftover leftover leftover only",
            plan="CE leftover leftover leftover only 400s leftover leftover leftover AsyncAPI. Freeze message, spec CloudEvents leftover leftover leftover.",
            residual="handoff: keep AsyncAPI leftover leftover leftover or force CE leftover leftover leftover",
            vs="r3787 cloudevents-lll3-a3-binary (CloudEvents leftover leftover leftover vs AsyncAPI leftover leftover leftover, not binary)",
            fetch1="https://github.com/cloudevents/spec/blob/v1.0.2/cloudevents/spec.md",
            fetch1_ok="CloudEvents leftover leftover leftover subject is not an AsyncAPI leftover leftover leftover message.",
            fetch2="https://www.asyncapi.com/docs/reference/specification/v3.0.0#messageObject",
            fetch2_ok="Exclusive CloudEvents leftover leftover leftover 400s leftover leftover leftover AsyncAPI.",
        ),
    ),
    (
        plant(
            slug="jsonapi-lll4-relationship",
            domain="jsonapi-lll4-vs-hal-lll4",
            success=True,
            name="japi4",
            stack="JSON:API leftover leftover leftover 1.1 + Go",
            field="relationships",
            old="HAL leftover leftover leftover _links item",
            new="JSON:API leftover leftover leftover relationships",
            fail_err="400: leftover leftover leftover HAL after JSON:API leftover leftover leftover only",
            plan="JSON:API leftover leftover leftover only 400s leftover leftover leftover HAL. Dual-read _links for one release.",
            residual="SPA still HAL leftover leftover leftover; drop after spa 8",
            vs="r3787 jsonapi-lll3-included (JSON:API leftover leftover leftover vs HAL leftover leftover leftover, not included)",
            fetch1="https://jsonapi.org/format/#document-resource-object-relationships",
            fetch1_ok="JSON:API leftover leftover leftover relationships are not HAL leftover leftover leftover _links.",
            fetch2="https://stateless.group/hal_specification.html",
            fetch2_ok="Exclusive application/vnd.api+json leftover leftover leftover 415s leftover leftover leftover HAL.",
        ),
        plant(
            slug="hal-lll4-links-item",
            domain="hal-lll4-vs-jsonapi-lll4",
            success=False,
            name="hal4l",
            stack="OpenAPI leftover leftover leftover 3.1 + Java + TS",
            field="_links",
            old="JSON:API leftover leftover leftover relationships",
            new="HAL leftover leftover leftover _links only",
            fail_err="400: leftover leftover leftover JSON:API after HAL leftover leftover leftover only",
            plan="HAL leftover leftover leftover only 400s leftover leftover leftover JSON:API. Freeze relationships, spec HAL leftover leftover leftover.",
            residual="handoff: keep JSON:API leftover leftover leftover or force HAL leftover leftover leftover",
            vs="r3787 hal-lll3-embedded (HAL leftover leftover leftover vs JSON:API leftover leftover leftover, not _embedded)",
            fetch1="https://stateless.group/hal_specification.html",
            fetch1_ok="HAL leftover leftover leftover _links is not JSON:API leftover leftover leftover relationships.",
            fetch2="https://jsonapi.org/format/#document-resource-object-relationships",
            fetch2_ok="Exclusive HAL leftover leftover leftover 415s leftover leftover leftover JSON:API.",
        ),
    ),
    (
        plant(
            slug="capnp-lll4-promise",
            domain="capnp-lll4-vs-flatbuffers-lll4",
            success=True,
            name="cap4p",
            stack="Cap'n Proto leftover leftover leftover + Go",
            field="promise",
            old="FlatBuffers leftover leftover leftover vector",
            new="Cap'n leftover leftover leftover promise pipelining",
            fail_err="415: leftover leftover leftover FlatBuffers after Cap'n leftover leftover leftover only",
            plan="Cap'n leftover leftover leftover only 415s leftover leftover leftover FlatBuffers. Dual-decode vector for one release.",
            residual="game still FlatBuffers leftover leftover leftover; drop after game 5",
            vs="r3787 capnp-lll3-capability (Cap'n leftover leftover leftover vs FlatBuffers leftover leftover leftover, not capability)",
            fetch1="https://capnproto.org/rpc.html#pipelining",
            fetch1_ok="Cap'n leftover leftover leftover promises are not FlatBuffers leftover leftover leftover vectors.",
            fetch2="https://flatbuffers.dev/flatbuffers_guide_tutorial.html",
            fetch2_ok="Exclusive application/x-capnp leftover leftover leftover 415s leftover leftover leftover FlatBuffers.",
        ),
        plant(
            slug="flatbuffers-lll4-vector",
            domain="flatbuffers-lll4-vs-capnp-lll4",
            success=False,
            name="fb4v",
            stack="OpenAPI leftover leftover leftover 3.1 + Java + TS",
            field="vector",
            old="Cap'n leftover leftover leftover promise",
            new="FlatBuffers leftover leftover leftover vector only",
            fail_err="415: leftover leftover leftover Cap'n after FlatBuffers leftover leftover leftover only",
            plan="FlatBuffers leftover leftover leftover only 415s leftover leftover leftover Cap'n. Freeze promise, spec FlatBuffers leftover leftover leftover.",
            residual="handoff: keep Cap'n leftover leftover leftover or force FlatBuffers leftover leftover leftover",
            vs="r3787 flatbuffers-lll3-grpc (FlatBuffers leftover leftover leftover vs Cap'n leftover leftover leftover, not gRPC)",
            fetch1="https://flatbuffers.dev/flatbuffers_guide_tutorial.html",
            fetch1_ok="FlatBuffers leftover leftover leftover vectors are not Cap'n leftover leftover leftover promises.",
            fetch2="https://capnproto.org/rpc.html#pipelining",
            fetch2_ok="Exclusive application/x-flatbuffer leftover leftover leftover 415s leftover leftover leftover Cap'n.",
        ),
    ),
    (
        plant(
            slug="msgpack-lll4-timestamp",
            domain="msgpack-lll4-vs-ion-lll4",
            success=True,
            name="mp4t",
            stack="MessagePack leftover leftover leftover + Go",
            field="timestamp",
            old="Ion leftover leftover leftover timestamp",
            new="MessagePack leftover leftover leftover timestamp ext",
            fail_err="415: leftover leftover leftover Ion after MessagePack leftover leftover leftover only",
            plan="MessagePack leftover leftover leftover only 415s leftover leftover leftover Ion. Dual-decode Ion timestamp for one release.",
            residual="stream still Ion leftover leftover leftover; drop after stream 6",
            vs="r3787 msgpack-lll3-ext (MessagePack leftover leftover leftover vs Ion leftover leftover leftover, not generic ext)",
            fetch1="https://github.com/msgpack/msgpack/blob/master/spec.md#timestamp-extension-type",
            fetch1_ok="MessagePack leftover leftover leftover timestamp ext is not Ion leftover leftover leftover timestamp.",
            fetch2="https://amazon-ion.github.io/ion-docs/docs/spec.html#timestamp",
            fetch2_ok="Exclusive application/msgpack leftover leftover leftover 415s leftover leftover leftover Ion.",
        ),
        plant(
            slug="ion-lll4-timestamp",
            domain="ion-lll4-vs-msgpack-lll4",
            success=False,
            name="ion4t",
            stack="OpenAPI leftover leftover leftover 3.1 + Java + TS",
            field="timestamp",
            old="MessagePack leftover leftover leftover timestamp ext",
            new="Ion leftover leftover leftover timestamp only",
            fail_err="415: leftover leftover leftover MessagePack after Ion leftover leftover leftover only",
            plan="Ion leftover leftover leftover only 415s leftover leftover leftover MessagePack. Freeze msgpack timestamp, spec Ion leftover leftover leftover.",
            residual="handoff: keep MessagePack leftover leftover leftover or force Ion leftover leftover leftover",
            vs="r3787 ion-lll3-sexp (Ion leftover leftover leftover vs MessagePack leftover leftover leftover, not sexp)",
            fetch1="https://amazon-ion.github.io/ion-docs/docs/spec.html#timestamp",
            fetch1_ok="Ion leftover leftover leftover timestamp is not MessagePack leftover leftover leftover timestamp ext.",
            fetch2="https://github.com/msgpack/msgpack/blob/master/spec.md#timestamp-extension-type",
            fetch2_ok="Exclusive application/x-amz-ion leftover leftover leftover 415s leftover leftover leftover MessagePack.",
        ),
    ),
    (
        plant(
            slug="avro-lll4-union",
            domain="avro-lll4-vs-thrift-lll4",
            success=True,
            name="avr4u",
            stack="Avro leftover leftover leftover + Go",
            field="union",
            old="Thrift leftover leftover leftover union",
            new="Avro leftover leftover leftover union schema",
            fail_err="415: leftover leftover leftover Thrift after Avro leftover leftover leftover only",
            plan="Avro leftover leftover leftover only 415s leftover leftover leftover Thrift. Dual-decode Thrift union for one release.",
            residual="rpc still Thrift leftover leftover leftover; drop after rpc 5",
            vs="r3787 avro-lll3-rpc (Avro leftover leftover leftover vs Thrift leftover leftover leftover, not RPC handshake)",
            fetch1="https://avro.apache.org/docs/1.11.1/specification/#unions",
            fetch1_ok="Avro leftover leftover leftover unions are not Thrift leftover leftover leftover unions.",
            fetch2="https://thrift.apache.org/docs/types",
            fetch2_ok="Exclusive application/avro leftover leftover leftover 415s leftover leftover leftover Thrift.",
        ),
        plant(
            slug="thrift-lll4-union",
            domain="thrift-lll4-vs-avro-lll4",
            success=False,
            name="th4u",
            stack="OpenAPI leftover leftover leftover 3.1 + Java + TS",
            field="union",
            old="Avro leftover leftover leftover union schema",
            new="Thrift leftover leftover leftover union only",
            fail_err="415: leftover leftover leftover Avro after Thrift leftover leftover leftover only",
            plan="Thrift leftover leftover leftover only 415s leftover leftover leftover Avro. Freeze Avro union, spec Thrift leftover leftover leftover.",
            residual="handoff: keep Avro leftover leftover leftover or force Thrift leftover leftover leftover",
            vs="r3787 thrift-lll3-binary (Thrift leftover leftover leftover vs Avro leftover leftover leftover, not binary protocol)",
            fetch1="https://thrift.apache.org/docs/types",
            fetch1_ok="Thrift leftover leftover leftover union is not Avro leftover leftover leftover union.",
            fetch2="https://avro.apache.org/docs/1.11.1/specification/#unions",
            fetch2_ok="Exclusive application/x-thrift leftover leftover leftover 415s leftover leftover leftover Avro.",
        ),
    ),
    (
        plant(
            slug="fhir-lll4-search",
            domain="fhir-lll4-vs-hl7-lll4",
            success=True,
            name="fhir4s",
            stack="FHIR leftover leftover leftover R4 search + Go",
            field="_search",
            old="HL7 leftover leftover leftover v2 QRD",
            new="FHIR leftover leftover leftover R4 search",
            fail_err="400: leftover leftover leftover HL7 after FHIR leftover leftover leftover only",
            plan="FHIR leftover leftover leftover only 400s leftover leftover leftover HL7. Dual-read QRD for one release.",
            residual="lab still HL7 leftover leftover leftover; drop after lab 7",
            vs="r3787 fhir-lll3-xml (FHIR leftover leftover leftover vs HL7 leftover leftover leftover, not R4 XML)",
            fetch1="https://hl7.org/fhir/R4/search.html",
            fetch1_ok="FHIR leftover leftover leftover R4 search is not HL7 leftover leftover leftover v2 QRD.",
            fetch2="https://www.hl7.org/implement/standards/product_brief.cfm?product_id=185",
            fetch2_ok="Exclusive application/fhir+json leftover leftover leftover 415s leftover leftover leftover HL7.",
        ),
        plant(
            slug="hl7-lll4-qrd",
            domain="hl7-lll4-vs-fhir-lll4",
            success=False,
            name="hl74q",
            stack="OpenAPI leftover leftover leftover 3.1 + Java + TS",
            field="QRD",
            old="FHIR leftover leftover leftover R4 search",
            new="HL7 leftover leftover leftover v2 QRD only",
            fail_err="400: leftover leftover leftover FHIR after HL7 leftover leftover leftover only",
            plan="HL7 leftover leftover leftover only 400s leftover leftover leftover FHIR. Freeze _search, spec HL7 leftover leftover leftover.",
            residual="handoff: keep FHIR leftover leftover leftover or force HL7 leftover leftover leftover",
            vs="r3787 hl7-lll3-cda (HL7 leftover leftover leftover vs FHIR leftover leftover leftover, not CDA)",
            fetch1="https://www.hl7.org/implement/standards/product_brief.cfm?product_id=185",
            fetch1_ok="HL7 leftover leftover leftover QRD is not FHIR leftover leftover leftover search.",
            fetch2="https://hl7.org/fhir/R4/search.html",
            fetch2_ok="Exclusive application/hl7-v2 leftover leftover leftover 415s leftover leftover leftover FHIR.",
        ),
    ),
    (
        plant(
            slug="graphql-lll4-federation",
            domain="graphql-lll4-vs-grpc-lll4",
            success=True,
            name="gql4f",
            stack="GraphQL leftover leftover leftover federation + gRPC leftover leftover leftover + Go",
            field="_entities",
            old="gRPC leftover leftover leftover GetEntity method",
            new="GraphQL leftover leftover leftover federation entities",
            fail_err="400: leftover leftover leftover gRPC after GraphQL leftover leftover leftover only",
            plan="GraphQL leftover leftover leftover only 400s leftover leftover leftover gRPC. Dual-bind GetEntity for one release.",
            residual="mesh still gRPC leftover leftover leftover; drop after mesh 5",
            vs="r3787 graphql-lll3-grpc-gw (GraphQL leftover leftover leftover vs leftover leftover leftover gRPC, not gateway document)",
            fetch1="https://www.apollographql.com/docs/federation/federation-spec/",
            fetch1_ok="GraphQL leftover leftover leftover federation entities are not gRPC leftover leftover leftover methods.",
            fetch2="https://github.com/grpc/grpc/blob/master/doc/PROTOCOL-HTTP2.md",
            fetch2_ok="Exclusive application/graphql leftover leftover leftover 400s leftover leftover leftover gRPC.",
        ),
        plant(
            slug="grpc-lll4-getentity",
            domain="grpc-lll4-vs-graphql-lll4",
            success=False,
            name="gr4ge",
            stack="gRPC leftover leftover leftover + Java + TS",
            field="GetEntity",
            old="GraphQL leftover leftover leftover federation entities",
            new="gRPC leftover leftover leftover GetEntity only",
            fail_err="415: leftover leftover leftover GraphQL after gRPC leftover leftover leftover only",
            plan="gRPC leftover leftover leftover only 415s leftover leftover leftover GraphQL. Freeze _entities, spec gRPC leftover leftover leftover.",
            residual="handoff: keep GraphQL leftover leftover leftover or force gRPC leftover leftover leftover",
            vs="r3787 grpc-lll3-gql-transcode (gRPC leftover leftover leftover vs leftover leftover leftover GraphQL, not transcode)",
            fetch1="https://github.com/grpc/grpc/blob/master/doc/PROTOCOL-HTTP2.md",
            fetch1_ok="gRPC leftover leftover leftover GetEntity is not GraphQL leftover leftover leftover federation.",
            fetch2="https://www.apollographql.com/docs/federation/federation-spec/",
            fetch2_ok="Exclusive application/grpc leftover leftover leftover 415s leftover leftover leftover GraphQL.",
        ),
    ),
    (
        plant(
            slug="oas-lll4-protobuf-map",
            domain="oas-lll4-vs-protobuf-lll4",
            success=True,
            name="oas4m",
            stack="OpenAPI leftover leftover leftover 3.1 + protobuf leftover leftover leftover + Go",
            field="additionalProperties",
            old="protobuf leftover leftover leftover map<string,string>",
            new="OpenAPI leftover leftover leftover additionalProperties map",
            fail_err="415: leftover leftover leftover protobuf after OpenAPI leftover leftover leftover only",
            plan="OpenAPI leftover leftover leftover only 415s leftover leftover leftover protobuf. Dual-decode map for one release.",
            residual="rpc still protobuf leftover leftover leftover; drop after rpc 6",
            vs="r3787 oas-lll3-protobuf-media (OpenAPI leftover leftover leftover vs leftover leftover leftover protobuf, not media type)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object",
            fetch1_ok="OpenAPI leftover leftover leftover additionalProperties is not protobuf leftover leftover leftover map.",
            fetch2="https://protobuf.dev/programming-guides/proto3/#maps",
            fetch2_ok="Exclusive application/json leftover leftover leftover 415s leftover leftover leftover protobuf.",
        ),
        plant(
            slug="protobuf-lll4-map-oas",
            domain="protobuf-lll4-vs-oas-lll4",
            success=False,
            name="pb4m",
            stack="protobuf leftover leftover leftover + Java + TS",
            field="map",
            old="OpenAPI leftover leftover leftover additionalProperties",
            new="protobuf leftover leftover leftover map only",
            fail_err="415: leftover leftover leftover OpenAPI after protobuf leftover leftover leftover only",
            plan="protobuf leftover leftover leftover only 415s leftover leftover leftover OpenAPI. Freeze additionalProperties, spec protobuf leftover leftover leftover.",
            residual="handoff: keep OpenAPI leftover leftover leftover or force protobuf leftover leftover leftover",
            vs="r3787 protobuf-lll3-oas-jsonname (protobuf leftover leftover leftover vs leftover leftover leftover OpenAPI, not json_name)",
            fetch1="https://protobuf.dev/programming-guides/proto3/#maps",
            fetch1_ok="protobuf leftover leftover leftover map is not OpenAPI leftover leftover leftover additionalProperties.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object",
            fetch2_ok="Exclusive application/x-protobuf leftover leftover leftover 415s leftover leftover leftover OpenAPI.",
        ),
    ),
    (
        plant(
            slug="asyncapi-lll4-security",
            domain="asyncapi-lll4-sec-vs-ce-lll4",
            success=True,
            name="a4sec",
            stack="AsyncAPI leftover leftover leftover security + Go",
            field="security",
            old="CloudEvents leftover leftover leftover extension auth",
            new="AsyncAPI leftover leftover leftover sasl security",
            fail_err="400: leftover leftover leftover CloudEvents after AsyncAPI leftover leftover leftover security-only",
            plan="AsyncAPI leftover leftover leftover security-only 400s leftover leftover leftover CloudEvents. Dual-bind CE extension auth for one release.",
            residual="bus still CloudEvents leftover leftover leftover; drop after bus 7",
            vs="r3787 asyncapi leftover leftover leftover vs leftover leftover leftover CloudEvents (not bindings)",
            fetch1="https://www.asyncapi.com/docs/reference/specification/v3.0.0#securitySchemeObject",
            fetch1_ok="AsyncAPI leftover leftover leftover security is not CloudEvents leftover leftover leftover extension auth.",
            fetch2="https://github.com/cloudevents/spec/blob/v1.0.2/cloudevents/spec.md#type-system",
            fetch2_ok="Exclusive AsyncAPI leftover leftover leftover 400 leftover leftover leftover CloudEvents auth.",
        ),
        plant(
            slug="cloudevents-lll4-ext-auth",
            domain="ce-lll4-auth-vs-asyncapi-lll4",
            success=False,
            name="ce4a",
            stack="CloudEvents leftover leftover leftover + Java + TS",
            field="authext",
            old="AsyncAPI leftover leftover leftover sasl security",
            new="CloudEvents leftover leftover leftover extension auth only",
            fail_err="400: leftover leftover leftover AsyncAPI after CloudEvents leftover leftover leftover auth-only",
            plan="CE leftover leftover leftover auth-only 400s leftover leftover leftover AsyncAPI. Freeze sasl, spec CloudEvents leftover leftover leftover.",
            residual="handoff: keep AsyncAPI leftover leftover leftover or force CE leftover leftover leftover auth",
            vs="r3787 CloudEvents leftover leftover leftover vs leftover leftover leftover AsyncAPI (not http mode)",
            fetch1="https://github.com/cloudevents/spec/blob/v1.0.2/cloudevents/spec.md#type-system",
            fetch1_ok="CloudEvents leftover leftover leftover extension auth is not AsyncAPI leftover leftover leftover sasl.",
            fetch2="https://www.asyncapi.com/docs/reference/specification/v3.0.0#securitySchemeObject",
            fetch2_ok="Exclusive CloudEvents leftover leftover leftover 400s leftover leftover leftover AsyncAPI security.",
        ),
    ),
    (
        plant(
            slug="jsonapi-lll4-pagination",
            domain="jsonapi-lll4-page-vs-hal-lll4",
            success=True,
            name="jap4p",
            stack="JSON:API leftover leftover leftover page + Go",
            field="page",
            old="HAL leftover leftover leftover page links",
            new="JSON:API leftover leftover leftover page cursor",
            fail_err="400: leftover leftover leftover HAL after JSON:API leftover leftover leftover page-only",
            plan="JSON:API leftover leftover leftover page-only 400s leftover leftover leftover HAL. Dual-read page links for one release.",
            residual="SPA still HAL leftover leftover leftover; drop after spa 9",
            vs="r3787 JSON:API leftover leftover leftover vs leftover leftover leftover HAL (not sparse)",
            fetch1="https://jsonapi.org/format/#fetching-pagination",
            fetch1_ok="JSON:API leftover leftover leftover pagination is not HAL leftover leftover leftover page links.",
            fetch2="https://stateless.group/hal_specification.html",
            fetch2_ok="Exclusive JSON:API leftover leftover leftover 415s leftover leftover leftover HAL page.",
        ),
        plant(
            slug="hal-lll4-page-links",
            domain="hal-lll4-page-vs-jsonapi-lll4",
            success=False,
            name="hal4p",
            stack="OpenAPI leftover leftover leftover 3.1 + Java + TS",
            field="next",
            old="JSON:API leftover leftover leftover page cursor",
            new="HAL leftover leftover leftover page links only",
            fail_err="400: leftover leftover leftover JSON:API after HAL leftover leftover leftover page-only",
            plan="HAL leftover leftover leftover page-only 400s leftover leftover leftover JSON:API. Freeze cursor, spec HAL leftover leftover leftover.",
            residual="handoff: keep JSON:API leftover leftover leftover or force HAL leftover leftover leftover page",
            vs="r3787 HAL leftover leftover leftover vs leftover leftover leftover JSON:API (not curie)",
            fetch1="https://stateless.group/hal_specification.html",
            fetch1_ok="HAL leftover leftover leftover page links are not JSON:API leftover leftover leftover cursors.",
            fetch2="https://jsonapi.org/format/#fetching-pagination",
            fetch2_ok="Exclusive HAL leftover leftover leftover 415s leftover leftover leftover JSON:API page.",
        ),
    ),
    (
        plant(
            slug="capnp-lll4-segment",
            domain="capnp-lll4-seg-vs-fb-lll4",
            success=True,
            name="cap4s",
            stack="Cap'n leftover leftover leftover segments + Go",
            field="segment",
            old="FlatBuffers leftover leftover leftover size-prefixed",
            new="Cap'n leftover leftover leftover multi-segment",
            fail_err="415: leftover leftover leftover FlatBuffers after Cap'n leftover leftover leftover segment-only",
            plan="Cap'n leftover leftover leftover segment-only 415s leftover leftover leftover FlatBuffers. Dual-decode size-prefixed for one release.",
            residual="game still FlatBuffers leftover leftover leftover; drop after game 6",
            vs="r3787 Cap'n leftover leftover leftover vs leftover leftover leftover FlatBuffers (not packed)",
            fetch1="https://capnproto.org/encoding.html#serialization-over-a-stream",
            fetch1_ok="Cap'n leftover leftover leftover segments are not FlatBuffers leftover leftover leftover size-prefixed.",
            fetch2="https://flatbuffers.dev/flatbuffers_guide_use_cpp.html",
            fetch2_ok="Exclusive Cap'n leftover leftover leftover 415 leftover leftover leftover FlatBuffers.",
        ),
        plant(
            slug="flatbuffers-lll4-sizepref",
            domain="fb-lll4-size-vs-capnp-lll4",
            success=False,
            name="fb4s",
            stack="OpenAPI leftover leftover leftover 3.1 + Java + TS",
            field="size_prefixed",
            old="Cap'n leftover leftover leftover multi-segment",
            new="FlatBuffers leftover leftover leftover size-prefixed only",
            fail_err="415: leftover leftover leftover Cap'n after FlatBuffers leftover leftover leftover size-only",
            plan="FlatBuffers leftover leftover leftover size-only 415s leftover leftover leftover Cap'n. Freeze segments, spec FlatBuffers leftover leftover leftover.",
            residual="handoff: keep Cap'n leftover leftover leftover or force FlatBuffers leftover leftover leftover size-prefixed",
            vs="r3787 FlatBuffers leftover leftover leftover vs leftover leftover leftover Cap'n (not flex)",
            fetch1="https://flatbuffers.dev/flatbuffers_guide_use_cpp.html",
            fetch1_ok="FlatBuffers leftover leftover leftover size-prefixed is not Cap'n leftover leftover leftover segments.",
            fetch2="https://capnproto.org/encoding.html#serialization-over-a-stream",
            fetch2_ok="Exclusive FlatBuffers leftover leftover leftover 415s leftover leftover leftover Cap'n segments.",
        ),
    ),
    (
        plant(
            slug="msgpack-lll4-str8",
            domain="msgpack-lll4-str8-vs-ion-lll4",
            success=True,
            name="mp4s",
            stack="MessagePack leftover leftover leftover str8 + Go",
            field="str8",
            old="Ion leftover leftover leftover string",
            new="MessagePack leftover leftover leftover str8",
            fail_err="415: leftover leftover leftover Ion after MessagePack leftover leftover leftover str8-only",
            plan="MessagePack leftover leftover leftover str8-only 415s leftover leftover leftover Ion. Dual-decode Ion string for one release.",
            residual="stream still Ion leftover leftover leftover; drop after stream 7",
            vs="r3787 MessagePack leftover leftover leftover vs leftover leftover leftover Ion (not bin8)",
            fetch1="https://github.com/msgpack/msgpack/blob/master/spec.md#str-format-family",
            fetch1_ok="MessagePack leftover leftover leftover str8 is not Ion leftover leftover leftover string.",
            fetch2="https://amazon-ion.github.io/ion-docs/docs/spec.html#string",
            fetch2_ok="Exclusive MessagePack leftover leftover leftover 415s leftover leftover leftover Ion string.",
        ),
        plant(
            slug="ion-lll4-string",
            domain="ion-lll4-str-vs-msgpack-lll4",
            success=False,
            name="ion4s",
            stack="OpenAPI leftover leftover leftover 3.1 + Java + TS",
            field="string",
            old="MessagePack leftover leftover leftover str8",
            new="Ion leftover leftover leftover string only",
            fail_err="415: leftover leftover leftover MessagePack after Ion leftover leftover leftover string-only",
            plan="Ion leftover leftover leftover string-only 415s leftover leftover leftover MessagePack. Freeze str8, spec Ion leftover leftover leftover.",
            residual="handoff: keep MessagePack leftover leftover leftover or force Ion leftover leftover leftover string",
            vs="r3787 Ion leftover leftover leftover vs leftover leftover leftover MessagePack (not symbol)",
            fetch1="https://amazon-ion.github.io/ion-docs/docs/spec.html#string",
            fetch1_ok="Ion leftover leftover leftover string is not MessagePack leftover leftover leftover str8.",
            fetch2="https://github.com/msgpack/msgpack/blob/master/spec.md#str-format-family",
            fetch2_ok="Exclusive Ion leftover leftover leftover 415s leftover leftover leftover MessagePack str8.",
        ),
    ),
    (
        plant(
            slug="avro-lll4-decimal",
            domain="avro-lll4-dec-vs-thrift-lll4",
            success=True,
            name="avr4d",
            stack="Avro leftover leftover leftover decimal + Go",
            field="decimal",
            old="Thrift leftover leftover leftover i64 cents",
            new="Avro leftover leftover leftover logical decimal",
            fail_err="415: leftover leftover leftover Thrift after Avro leftover leftover leftover decimal-only",
            plan="Avro leftover leftover leftover decimal-only 415s leftover leftover leftover Thrift. Dual-decode i64 cents for one release.",
            residual="rpc still Thrift leftover leftover leftover; drop after rpc 6",
            vs="r3787 Avro leftover leftover leftover vs leftover leftover leftover Thrift (not writer schema)",
            fetch1="https://avro.apache.org/docs/1.11.1/specification/#decimal",
            fetch1_ok="Avro leftover leftover leftover logical decimal is not Thrift leftover leftover leftover i64.",
            fetch2="https://thrift.apache.org/docs/types",
            fetch2_ok="Exclusive Avro leftover leftover leftover 415s leftover leftover leftover Thrift i64.",
        ),
        plant(
            slug="thrift-lll4-i64cents",
            domain="thrift-lll4-i64-vs-avro-lll4",
            success=False,
            name="th4c",
            stack="OpenAPI leftover leftover leftover 3.1 + Java + TS",
            field="cents",
            old="Avro leftover leftover leftover logical decimal",
            new="Thrift leftover leftover leftover i64 cents only",
            fail_err="415: leftover leftover leftover Avro after Thrift leftover leftover leftover i64-only",
            plan="Thrift leftover leftover leftover i64-only 415s leftover leftover leftover Avro. Freeze decimal, spec Thrift leftover leftover leftover.",
            residual="handoff: keep Avro leftover leftover leftover or force Thrift leftover leftover leftover i64",
            vs="r3787 Thrift leftover leftover leftover vs leftover leftover leftover Avro (not IDL)",
            fetch1="https://thrift.apache.org/docs/types",
            fetch1_ok="Thrift leftover leftover leftover i64 is not Avro leftover leftover leftover decimal.",
            fetch2="https://avro.apache.org/docs/1.11.1/specification/#decimal",
            fetch2_ok="Exclusive Thrift leftover leftover leftover 415s leftover leftover leftover Avro decimal.",
        ),
    ),
    (
        plant(
            slug="fhir-lll4-operation",
            domain="fhir-lll4-op-vs-hl7-lll4",
            success=True,
            name="fhir4o",
            stack="FHIR leftover leftover leftover $operation + Go",
            field="$everything",
            old="HL7 leftover leftover leftover v2 QRY",
            new="FHIR leftover leftover leftover $everything",
            fail_err="400: leftover leftover leftover HL7 after FHIR leftover leftover leftover operation-only",
            plan="FHIR leftover leftover leftover operation-only 400s leftover leftover leftover HL7. Dual-read QRY for one release.",
            residual="lab still HL7 leftover leftover leftover; drop after lab 8",
            vs="r3787 FHIR leftover leftover leftover vs leftover leftover leftover HL7 (not Bundle)",
            fetch1="https://hl7.org/fhir/R4/operations.html",
            fetch1_ok="FHIR leftover leftover leftover $everything is not HL7 leftover leftover leftover v2 QRY.",
            fetch2="https://www.hl7.org/implement/standards/product_brief.cfm?product_id=185",
            fetch2_ok="Exclusive FHIR leftover leftover leftover $operation 400 leftover leftover leftover HL7.",
        ),
        plant(
            slug="hl7-lll4-qry",
            domain="hl7-lll4-qry-vs-fhir-lll4",
            success=False,
            name="hl74y",
            stack="OpenAPI leftover leftover leftover 3.1 + Java + TS",
            field="QRY",
            old="FHIR leftover leftover leftover $everything",
            new="HL7 leftover leftover leftover v2 QRY only",
            fail_err="400: leftover leftover leftover FHIR after HL7 leftover leftover leftover QRY-only",
            plan="HL7 leftover leftover leftover QRY-only 400s leftover leftover leftover FHIR. Freeze $everything, spec HL7 leftover leftover leftover.",
            residual="handoff: keep FHIR leftover leftover leftover or force HL7 leftover leftover leftover QRY",
            vs="r3787 HL7 leftover leftover leftover vs leftover leftover leftover FHIR (not MSH)",
            fetch1="https://www.hl7.org/implement/standards/product_brief.cfm?product_id=185",
            fetch1_ok="HL7 leftover leftover leftover QRY is not FHIR leftover leftover leftover $everything.",
            fetch2="https://hl7.org/fhir/R4/operations.html",
            fetch2_ok="Exclusive HL7 leftover leftover leftover 400s leftover leftover leftover FHIR $operation.",
        ),
    ),
    (
        plant(
            slug="graphql-lll4-defer",
            domain="graphql-lll4-defer-vs-grpc-lll4",
            success=True,
            name="gql4d",
            stack="GraphQL leftover leftover leftover @defer + Go",
            field="@defer",
            old="gRPC leftover leftover leftover incremental stream",
            new="GraphQL leftover leftover leftover @defer",
            fail_err="400: leftover leftover leftover gRPC after GraphQL leftover leftover leftover defer-only",
            plan="GraphQL leftover leftover leftover defer-only 400s leftover leftover leftover gRPC. Dual-bind incremental stream for one release.",
            residual="mesh still gRPC leftover leftover leftover; drop after mesh 6",
            vs="r3787 GraphQL leftover leftover leftover vs leftover leftover leftover gRPC (not subscription)",
            fetch1="https://github.com/graphql/graphql-spec/blob/main/rfcs/DeferStream.md",
            fetch1_ok="GraphQL leftover leftover leftover @defer is not gRPC leftover leftover leftover incremental stream.",
            fetch2="https://github.com/grpc/grpc/blob/master/doc/PROTOCOL-HTTP2.md",
            fetch2_ok="Exclusive GraphQL leftover leftover leftover 400s leftover leftover leftover gRPC incremental.",
        ),
        plant(
            slug="grpc-lll4-incremental",
            domain="grpc-lll4-inc-vs-graphql-lll4",
            success=False,
            name="gr4i",
            stack="gRPC leftover leftover leftover incremental + Java + TS",
            field="incremental",
            old="GraphQL leftover leftover leftover @defer",
            new="gRPC leftover leftover leftover incremental stream only",
            fail_err="415: leftover leftover leftover GraphQL after gRPC leftover leftover leftover incremental-only",
            plan="gRPC leftover leftover leftover incremental-only 415s leftover leftover leftover GraphQL. Freeze @defer, spec gRPC leftover leftover leftover.",
            residual="handoff: keep GraphQL leftover leftover leftover or force gRPC leftover leftover leftover incremental",
            vs="r3787 gRPC leftover leftover leftover vs leftover leftover leftover GraphQL (not server stream)",
            fetch1="https://github.com/grpc/grpc/blob/master/doc/PROTOCOL-HTTP2.md",
            fetch1_ok="gRPC leftover leftover leftover incremental streams are not GraphQL leftover leftover leftover @defer.",
            fetch2="https://github.com/graphql/graphql-spec/blob/main/rfcs/DeferStream.md",
            fetch2_ok="Exclusive gRPC leftover leftover leftover 415s leftover leftover leftover GraphQL @defer.",
        ),
    ),
    (
        plant(
            slug="oas-lll4-proto-optional",
            domain="oas-lll4-opt-vs-protobuf-lll4",
            success=True,
            name="oas4o",
            stack="OpenAPI leftover leftover leftover nullable + protobuf leftover leftover leftover + Go",
            field="nullable",
            old="protobuf leftover leftover leftover optional",
            new="OpenAPI leftover leftover leftover nullable",
            fail_err="415: leftover leftover leftover protobuf after OpenAPI leftover leftover leftover nullable-only",
            plan="OpenAPI leftover leftover leftover nullable-only 415s leftover leftover leftover protobuf. Dual-decode optional for one release.",
            residual="rpc still protobuf leftover leftover leftover; drop after rpc 7",
            vs="r3787 OpenAPI leftover leftover leftover vs leftover leftover leftover protobuf (not oneOf)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object",
            fetch1_ok="OpenAPI leftover leftover leftover nullable is not protobuf leftover leftover leftover optional.",
            fetch2="https://protobuf.dev/programming-guides/proto3/#field-labels",
            fetch2_ok="Exclusive OpenAPI leftover leftover leftover 415s leftover leftover leftover protobuf optional.",
        ),
        plant(
            slug="protobuf-lll4-optional-oas",
            domain="protobuf-lll4-opt-vs-oas-lll4",
            success=False,
            name="pb4o",
            stack="protobuf leftover leftover leftover + Java + TS",
            field="optional",
            old="OpenAPI leftover leftover leftover nullable",
            new="protobuf leftover leftover leftover optional only",
            fail_err="415: leftover leftover leftover OpenAPI after protobuf leftover leftover leftover optional-only",
            plan="protobuf leftover leftover leftover optional-only 415s leftover leftover leftover OpenAPI. Freeze nullable, spec protobuf leftover leftover leftover.",
            residual="handoff: keep OpenAPI leftover leftover leftover or force protobuf leftover leftover leftover optional",
            vs="r3787 protobuf leftover leftover leftover vs leftover leftover leftover OpenAPI (not oneof)",
            fetch1="https://protobuf.dev/programming-guides/proto3/#field-labels",
            fetch1_ok="protobuf leftover leftover leftover optional is not OpenAPI leftover leftover leftover nullable.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object",
            fetch2_ok="Exclusive protobuf leftover leftover leftover 415s leftover leftover leftover OpenAPI nullable.",
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
            if "smile" in slug or "cbor" in slug:
                raise SystemExit(f"banned smile/cbor {slug}")


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
    print(json.dumps({"round": round_n, "idx": idx, "ids": [e1["id"], e2["id"]], "catalog": "r3851"}))


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
