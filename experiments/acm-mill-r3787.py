#!/usr/bin/env python3
"""Sixth leftover leftover leftover unique ACM catalog after r3714.

BAN wrap, 422-vs-400, 207-multistatus, smile/cbor, r3698–r3786 clones.
GraphQL leftover leftover leftover vs leftover leftover leftover gRPC (not REST).
OpenAPI leftover leftover leftover vs leftover leftover leftover protobuf (not JSON-only).
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

_spec4 = importlib.util.spec_from_file_location("acm_mill_r3698", HERE / "acm-mill-r3698.py")
_e = importlib.util.module_from_spec(_spec4)
assert _spec4.loader is not None
_spec4.loader.exec_module(_e)

_spec5 = importlib.util.spec_from_file_location("acm_mill_r3714", HERE / "acm-mill-r3714.py")
_f = importlib.util.module_from_spec(_spec5)
assert _spec5.loader is not None
_spec5.loader.exec_module(_f)

BANNED_PRIOR = (
    {p[0]["slug"] for p in _b.PAIRS}
    | {p[1]["slug"] for p in _b.PAIRS}
    | {p[0]["slug"] for p in _c.PAIRS}
    | {p[1]["slug"] for p in _c.PAIRS}
    | {p[0]["slug"] for p in _d.PAIRS}
    | {p[1]["slug"] for p in _d.PAIRS}
    | {p[0]["slug"] for p in _e.PAIRS}
    | {p[1]["slug"] for p in _e.PAIRS}
    | {p[0]["slug"] for p in _f.PAIRS}
    | {p[1]["slug"] for p in _f.PAIRS}
)

PAIRS: list[tuple[dict, dict]] = [
    (
        plant(
            slug="asyncapi-lll3-ce-channel",
            domain="asyncapi-lll3-vs-cloudevents-lll3",
            success=True,
            name="a3ce3",
            stack="AsyncAPI 3 leftover leftover leftover + CloudEvents leftover leftover leftover + Go",
            field="ce-source",
            old="CloudEvents leftover leftover leftover binary envelope",
            new="AsyncAPI leftover leftover leftover 3 channel address",
            fail_err="400: leftover leftover leftover CloudEvents after AsyncAPI leftover leftover leftover only",
            plan="AsyncAPI leftover leftover leftover only 400s leftover leftover leftover CloudEvents. Dual-bind CE binary for one release.",
            residual="bus still CloudEvents leftover leftover leftover; drop after bus 4",
            vs="r3714 asyncapi-lll-ce-bind (AsyncAPI leftover leftover leftover vs CloudEvents leftover leftover leftover, not ce-type)",
            fetch1="https://www.asyncapi.com/docs/reference/specification/v3.0.0#channelObject",
            fetch1_ok="AsyncAPI leftover leftover leftover 3 channels are not CloudEvents leftover leftover leftover binary envelopes.",
            fetch2="https://github.com/cloudevents/spec/blob/v1.0.2/cloudevents/bindings/http-protocol-binding.md",
            fetch2_ok="Exclusive AsyncAPI leftover leftover leftover 400s leftover leftover leftover CloudEvents binary.",
        ),
        plant(
            slug="cloudevents-lll3-a3-binary",
            domain="cloudevents-lll3-vs-asyncapi-lll3",
            success=False,
            name="cea33",
            stack="CloudEvents leftover leftover leftover + Java + TS",
            field="ce-id",
            old="AsyncAPI leftover leftover leftover channel address",
            new="CloudEvents leftover leftover leftover binary only",
            fail_err="400: leftover leftover leftover AsyncAPI after CloudEvents leftover leftover leftover only",
            plan="CE leftover leftover leftover only 400s leftover leftover leftover AsyncAPI. Freeze channel, spec CloudEvents leftover leftover leftover.",
            residual="handoff: keep AsyncAPI leftover leftover leftover or force CE leftover leftover leftover",
            vs="r3714 cloudevents-lll-a3-bind (CloudEvents leftover leftover leftover vs AsyncAPI leftover leftover leftover, not specversion)",
            fetch1="https://github.com/cloudevents/spec/blob/v1.0.2/cloudevents/bindings/http-protocol-binding.md",
            fetch1_ok="CloudEvents leftover leftover leftover binary is not an AsyncAPI leftover leftover leftover channel.",
            fetch2="https://www.asyncapi.com/docs/reference/specification/v3.0.0#channelObject",
            fetch2_ok="Exclusive CloudEvents leftover leftover leftover 400s leftover leftover leftover AsyncAPI.",
        ),
    ),
    (
        plant(
            slug="jsonapi-lll3-included",
            domain="jsonapi-lll3-vs-hal-lll3",
            success=True,
            name="japi3",
            stack="JSON:API leftover leftover leftover 1.1 + Go",
            field="included",
            old="HAL leftover leftover leftover _embedded",
            new="JSON:API leftover leftover leftover included",
            fail_err="400: leftover leftover leftover HAL after JSON:API leftover leftover leftover only",
            plan="JSON:API leftover leftover leftover only 400s leftover leftover leftover HAL. Dual-read _embedded for one release.",
            residual="SPA still HAL leftover leftover leftover; drop after spa 6",
            vs="r3714 jsonapi-lll-type-id (JSON:API leftover leftover leftover vs HAL leftover leftover leftover, not data+type+id)",
            fetch1="https://jsonapi.org/format/#document-compound-documents",
            fetch1_ok="JSON:API leftover leftover leftover included is not HAL leftover leftover leftover _embedded.",
            fetch2="https://stateless.group/hal_specification.html",
            fetch2_ok="Exclusive application/vnd.api+json leftover leftover leftover 415s leftover leftover leftover HAL.",
        ),
        plant(
            slug="hal-lll3-embedded",
            domain="hal-lll3-vs-jsonapi-lll3",
            success=False,
            name="hal3e",
            stack="OpenAPI leftover leftover leftover 3.1 + Java + TS",
            field="_embedded",
            old="JSON:API leftover leftover leftover included",
            new="HAL leftover leftover leftover _embedded only",
            fail_err="400: leftover leftover leftover JSON:API after HAL leftover leftover leftover only",
            plan="HAL leftover leftover leftover only 400s leftover leftover leftover JSON:API. Freeze included, spec HAL leftover leftover leftover.",
            residual="handoff: keep JSON:API leftover leftover leftover or force HAL leftover leftover leftover",
            vs="r3714 hal-lll-links-only (HAL leftover leftover leftover vs JSON:API leftover leftover leftover, not _links-only)",
            fetch1="https://stateless.group/hal_specification.html",
            fetch1_ok="HAL leftover leftover leftover _embedded is not JSON:API leftover leftover leftover included.",
            fetch2="https://jsonapi.org/format/#document-compound-documents",
            fetch2_ok="Exclusive HAL leftover leftover leftover 415s leftover leftover leftover JSON:API.",
        ),
    ),
    (
        plant(
            slug="capnp-lll3-capability",
            domain="capnp-lll3-vs-flatbuffers-lll3",
            success=True,
            name="cap3c",
            stack="Cap'n Proto leftover leftover leftover + Go",
            field="capability",
            old="FlatBuffers leftover leftover leftover gRPC table",
            new="Cap'n leftover leftover leftover capability RPC",
            fail_err="415: leftover leftover leftover FlatBuffers after Cap'n leftover leftover leftover only",
            plan="Cap'n leftover leftover leftover only 415s leftover leftover leftover FlatBuffers. Dual-decode gRPC table for one release.",
            residual="game still FlatBuffers leftover leftover leftover; drop after game 3",
            vs="r3714 capnp-lll-rpc (Cap'n leftover leftover leftover vs FlatBuffers leftover leftover leftover, not packed RPC)",
            fetch1="https://capnproto.org/rpc.html",
            fetch1_ok="Cap'n leftover leftover leftover capabilities are not FlatBuffers leftover leftover leftover tables.",
            fetch2="https://flatbuffers.dev/flatbuffers_grpc.html",
            fetch2_ok="Exclusive application/x-capnp leftover leftover leftover 415s leftover leftover leftover FlatBuffers.",
        ),
        plant(
            slug="flatbuffers-lll3-grpc",
            domain="flatbuffers-lll3-vs-capnp-lll3",
            success=False,
            name="fb3g",
            stack="OpenAPI leftover leftover leftover 3.1 + Java + TS",
            field="content",
            old="Cap'n leftover leftover leftover capability",
            new="FlatBuffers leftover leftover leftover gRPC only",
            fail_err="415: leftover leftover leftover Cap'n after FlatBuffers leftover leftover leftover only",
            plan="FlatBuffers leftover leftover leftover only 415s leftover leftover leftover Cap'n. Freeze capability, spec FlatBuffers leftover leftover leftover.",
            residual="handoff: keep Cap'n leftover leftover leftover or force FlatBuffers leftover leftover leftover",
            vs="r3714 flatbuffers-lll-vtable (FlatBuffers leftover leftover leftover vs Cap'n leftover leftover leftover, not vtable)",
            fetch1="https://flatbuffers.dev/flatbuffers_grpc.html",
            fetch1_ok="FlatBuffers leftover leftover leftover gRPC is not Cap'n leftover leftover leftover capability.",
            fetch2="https://capnproto.org/rpc.html",
            fetch2_ok="Exclusive application/x-flatbuffer leftover leftover leftover 415s leftover leftover leftover Cap'n.",
        ),
    ),
    (
        plant(
            slug="msgpack-lll3-ext",
            domain="msgpack-lll3-vs-ion-lll3",
            success=True,
            name="mp3x",
            stack="MessagePack leftover leftover leftover + Go",
            field="content",
            old="Ion leftover leftover leftover sexp",
            new="MessagePack leftover leftover leftover ext type",
            fail_err="415: leftover leftover leftover Ion after MessagePack leftover leftover leftover only",
            plan="MessagePack leftover leftover leftover only 415s leftover leftover leftover Ion. Dual-decode sexp for one release.",
            residual="stream still Ion leftover leftover leftover; drop after stream 4",
            vs="r3714 msgpack-lll-fixmap (MessagePack leftover leftover leftover vs Ion leftover leftover leftover, not fixmap)",
            fetch1="https://github.com/msgpack/msgpack/blob/master/spec.md#extension-types",
            fetch1_ok="MessagePack leftover leftover leftover ext is not Ion leftover leftover leftover sexp.",
            fetch2="https://amazon-ion.github.io/ion-docs/docs/spec.html",
            fetch2_ok="Exclusive application/msgpack leftover leftover leftover 415s leftover leftover leftover Ion.",
        ),
        plant(
            slug="ion-lll3-sexp",
            domain="ion-lll3-vs-msgpack-lll3",
            success=False,
            name="ion3s",
            stack="OpenAPI leftover leftover leftover 3.1 + Java + TS",
            field="content",
            old="MessagePack leftover leftover leftover ext",
            new="Ion leftover leftover leftover sexp only",
            fail_err="415: leftover leftover leftover MessagePack after Ion leftover leftover leftover only",
            plan="Ion leftover leftover leftover only 415s leftover leftover leftover MessagePack. Freeze ext, spec Ion leftover leftover leftover.",
            residual="handoff: keep MessagePack leftover leftover leftover or force Ion leftover leftover leftover",
            vs="r3714 ion-lll-bvm (Ion leftover leftover leftover vs MessagePack leftover leftover leftover, not BVM)",
            fetch1="https://amazon-ion.github.io/ion-docs/docs/spec.html",
            fetch1_ok="Ion leftover leftover leftover sexp is not MessagePack leftover leftover leftover ext.",
            fetch2="https://github.com/msgpack/msgpack/blob/master/spec.md#extension-types",
            fetch2_ok="Exclusive application/x-amz-ion leftover leftover leftover 415s leftover leftover leftover MessagePack.",
        ),
    ),
    (
        plant(
            slug="avro-lll3-rpc",
            domain="avro-lll3-vs-thrift-lll3",
            success=True,
            name="avr3r",
            stack="Avro leftover leftover leftover + Go",
            field="protocol",
            old="Thrift leftover leftover leftover binary protocol",
            new="Avro leftover leftover leftover RPC handshake",
            fail_err="415: leftover leftover leftover Thrift after Avro leftover leftover leftover only",
            plan="Avro leftover leftover leftover only 415s leftover leftover leftover Thrift. Dual-decode binary protocol for one release.",
            residual="rpc still Thrift leftover leftover leftover; drop after rpc 3",
            vs="r3714 avro-lll-ocf (Avro leftover leftover leftover vs Thrift leftover leftover leftover, not OCF)",
            fetch1="https://avro.apache.org/docs/1.11.1/specification/#protocol-declaration",
            fetch1_ok="Avro leftover leftover leftover RPC is not Thrift leftover leftover leftover binary.",
            fetch2="https://thrift.apache.org/docs/protocols",
            fetch2_ok="Exclusive application/avro leftover leftover leftover 415s leftover leftover leftover Thrift.",
        ),
        plant(
            slug="thrift-lll3-binary",
            domain="thrift-lll3-vs-avro-lll3",
            success=False,
            name="th3b",
            stack="OpenAPI leftover leftover leftover 3.1 + Java + TS",
            field="content",
            old="Avro leftover leftover leftover RPC handshake",
            new="Thrift leftover leftover leftover binary only",
            fail_err="415: leftover leftover leftover Avro after Thrift leftover leftover leftover only",
            plan="Thrift leftover leftover leftover only 415s leftover leftover leftover Avro. Freeze handshake, spec Thrift leftover leftover leftover.",
            residual="handoff: keep Avro leftover leftover leftover or force Thrift leftover leftover leftover",
            vs="r3714 thrift-lll-compact (Thrift leftover leftover leftover vs Avro leftover leftover leftover, not compact)",
            fetch1="https://thrift.apache.org/docs/protocols",
            fetch1_ok="Thrift leftover leftover leftover binary is not Avro leftover leftover leftover RPC.",
            fetch2="https://avro.apache.org/docs/1.11.1/specification/#protocol-declaration",
            fetch2_ok="Exclusive application/x-thrift leftover leftover leftover 415s leftover leftover leftover Avro.",
        ),
    ),
    (
        plant(
            slug="fhir-lll3-xml",
            domain="fhir-lll3-vs-hl7-lll3",
            success=True,
            name="fhir3x",
            stack="FHIR leftover leftover leftover R4 XML + Go",
            field="resourceType",
            old="HL7 leftover leftover leftover v3 CDA",
            new="FHIR leftover leftover leftover R4 XML",
            fail_err="400: leftover leftover leftover HL7 after FHIR leftover leftover leftover only",
            plan="FHIR leftover leftover leftover only 400s leftover leftover leftover HL7. Dual-read CDA for one release.",
            residual="lab still HL7 leftover leftover leftover; drop after lab 5",
            vs="r3714 fhir-lll-r4-json (FHIR leftover leftover leftover vs HL7 leftover leftover leftover, not R4 JSON)",
            fetch1="https://hl7.org/fhir/R4/xml.html",
            fetch1_ok="FHIR leftover leftover leftover R4 XML is not HL7 leftover leftover leftover v3 CDA.",
            fetch2="https://www.hl7.org/implement/standards/product_brief.cfm?product_id=7",
            fetch2_ok="Exclusive application/fhir+xml leftover leftover leftover 415s leftover leftover leftover HL7.",
        ),
        plant(
            slug="hl7-lll3-cda",
            domain="hl7-lll3-vs-fhir-lll3",
            success=False,
            name="hl73c",
            stack="OpenAPI leftover leftover leftover 3.1 + Java + TS",
            field="ClinicalDocument",
            old="FHIR leftover leftover leftover R4 XML",
            new="HL7 leftover leftover leftover v3 CDA only",
            fail_err="400: leftover leftover leftover FHIR after HL7 leftover leftover leftover only",
            plan="HL7 leftover leftover leftover only 400s leftover leftover leftover FHIR. Freeze resourceType, spec HL7 leftover leftover leftover.",
            residual="handoff: keep FHIR leftover leftover leftover or force HL7 leftover leftover leftover",
            vs="r3714 hl7-lll-v2-pipe (HL7 leftover leftover leftover vs FHIR leftover leftover leftover, not v2 pipe)",
            fetch1="https://www.hl7.org/implement/standards/product_brief.cfm?product_id=7",
            fetch1_ok="HL7 leftover leftover leftover CDA is not FHIR leftover leftover leftover XML.",
            fetch2="https://hl7.org/fhir/R4/xml.html",
            fetch2_ok="Exclusive application/cda+xml leftover leftover leftover 415s leftover leftover leftover FHIR.",
        ),
    ),
    (
        plant(
            slug="graphql-lll3-grpc-gw",
            domain="graphql-lll3-vs-grpc-lll3",
            success=True,
            name="gql3g",
            stack="GraphQL leftover leftover leftover + gRPC leftover leftover leftover + Go",
            field="query",
            old="gRPC leftover leftover leftover protobuf method",
            new="GraphQL leftover leftover leftover document over gateway",
            fail_err="400: leftover leftover leftover gRPC after GraphQL leftover leftover leftover only",
            plan="GraphQL leftover leftover leftover only 400s leftover leftover leftover gRPC. Dual-bind protobuf method for one release.",
            residual="mesh still gRPC leftover leftover leftover; drop after mesh 3",
            vs="r3714 graphql-lll-schema (GraphQL leftover leftover leftover vs leftover leftover leftover gRPC, not REST)",
            fetch1="https://spec.graphql.org/October2021/#sec-Language.Operations",
            fetch1_ok="GraphQL leftover leftover leftover documents are not gRPC leftover leftover leftover methods.",
            fetch2="https://github.com/grpc/grpc/blob/master/doc/PROTOCOL-HTTP2.md",
            fetch2_ok="Exclusive application/graphql leftover leftover leftover 400s leftover leftover leftover gRPC.",
        ),
        plant(
            slug="grpc-lll3-gql-transcode",
            domain="grpc-lll3-vs-graphql-lll3",
            success=False,
            name="gr3gq",
            stack="gRPC leftover leftover leftover + Java + TS",
            field="content-type",
            old="GraphQL leftover leftover leftover document",
            new="gRPC leftover leftover leftover proto only",
            fail_err="415: leftover leftover leftover GraphQL after gRPC leftover leftover leftover only",
            plan="gRPC leftover leftover leftover only 415s leftover leftover leftover GraphQL. Freeze document, spec gRPC leftover leftover leftover.",
            residual="handoff: keep GraphQL leftover leftover leftover or force gRPC leftover leftover leftover",
            vs="r3714 grpc-lll-proto (gRPC leftover leftover leftover vs leftover leftover leftover GraphQL, not HTTP JSON)",
            fetch1="https://github.com/grpc/grpc/blob/master/doc/PROTOCOL-HTTP2.md",
            fetch1_ok="gRPC leftover leftover leftover proto is not GraphQL leftover leftover leftover.",
            fetch2="https://spec.graphql.org/October2021/#sec-Language.Operations",
            fetch2_ok="Exclusive application/grpc leftover leftover leftover 415s leftover leftover leftover GraphQL.",
        ),
    ),
    (
        plant(
            slug="oas-lll3-protobuf-media",
            domain="oas-lll3-vs-protobuf-lll3",
            success=True,
            name="oas3p",
            stack="OpenAPI leftover leftover leftover 3.1 + protobuf leftover leftover leftover + Go",
            field="content",
            old="protobuf leftover leftover leftover wire type",
            new="OpenAPI leftover leftover leftover protobuf media",
            fail_err="415: leftover leftover leftover protobuf after OpenAPI leftover leftover leftover only",
            plan="OpenAPI leftover leftover leftover only 415s leftover leftover leftover protobuf. Dual-decode wire for one release.",
            residual="rpc still protobuf leftover leftover leftover; drop after rpc 4",
            vs="r3714 oas31-lll-paths (OpenAPI leftover leftover leftover vs leftover leftover leftover protobuf, not RAML)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#media-type-object",
            fetch1_ok="OpenAPI leftover leftover leftover media is not protobuf leftover leftover leftover wire-only.",
            fetch2="https://protobuf.dev/programming-guides/encoding/",
            fetch2_ok="Exclusive application/json leftover leftover leftover 415s leftover leftover leftover protobuf.",
        ),
        plant(
            slug="protobuf-lll3-oas-jsonname",
            domain="protobuf-lll3-vs-oas-lll3",
            success=False,
            name="pb3o",
            stack="protobuf leftover leftover leftover + Java + TS",
            field="json_name",
            old="OpenAPI leftover leftover leftover protobuf media",
            new="protobuf leftover leftover leftover json_name only",
            fail_err="415: leftover leftover leftover OpenAPI after protobuf leftover leftover leftover only",
            plan="protobuf leftover leftover leftover only 415s leftover leftover leftover OpenAPI. Freeze media, spec protobuf leftover leftover leftover.",
            residual="handoff: keep OpenAPI leftover leftover leftover or force protobuf leftover leftover leftover",
            vs="r3714 protobuf-lll-wire (protobuf leftover leftover leftover vs leftover leftover leftover OpenAPI, not JSON object)",
            fetch1="https://protobuf.dev/programming-guides/proto3/#json",
            fetch1_ok="protobuf leftover leftover leftover json_name is not OpenAPI leftover leftover leftover media.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object",
            fetch2_ok="Exclusive application/x-protobuf leftover leftover leftover 415s leftover leftover leftover OpenAPI.",
        ),
    ),
    (
        plant(
            slug="asyncapi-lll3-bindings",
            domain="asyncapi-lll3-bindings-vs-ce-lll3",
            success=True,
            name="a3bd3",
            stack="AsyncAPI leftover leftover leftover bindings + Go",
            field="bindings",
            old="CloudEvents leftover leftover leftover http mode",
            new="AsyncAPI leftover leftover leftover kafka binding",
            fail_err="400: leftover leftover leftover CloudEvents after AsyncAPI leftover leftover leftover bindings-only",
            plan="AsyncAPI leftover leftover leftover bindings-only 400s leftover leftover leftover CloudEvents. Dual-bind http mode for one release.",
            residual="bus still CloudEvents leftover leftover leftover; drop after bus 5",
            vs="r3714 asyncapi leftover leftover leftover vs leftover leftover leftover CloudEvents (not ce-bind slug)",
            fetch1="https://www.asyncapi.com/docs/reference/specification/v3.0.0#messageBindingsObject",
            fetch1_ok="AsyncAPI leftover leftover leftover bindings are not CloudEvents leftover leftover leftover http mode.",
            fetch2="https://github.com/cloudevents/spec/blob/v1.0.2/cloudevents/bindings/http-protocol-binding.md",
            fetch2_ok="Exclusive AsyncAPI leftover leftover leftover bindings 400 leftover leftover leftover CloudEvents.",
        ),
        plant(
            slug="cloudevents-lll3-http-mode",
            domain="ce-lll3-http-vs-asyncapi-lll3",
            success=False,
            name="ce3h",
            stack="CloudEvents leftover leftover leftover + Java + TS",
            field="mode",
            old="AsyncAPI leftover leftover leftover kafka binding",
            new="CloudEvents leftover leftover leftover http mode only",
            fail_err="400: leftover leftover leftover AsyncAPI after CloudEvents leftover leftover leftover http-only",
            plan="CE leftover leftover leftover http-only 400s leftover leftover leftover AsyncAPI. Freeze kafka binding, spec CloudEvents leftover leftover leftover.",
            residual="handoff: keep AsyncAPI leftover leftover leftover or force CE leftover leftover leftover http",
            vs="r3714 CloudEvents leftover leftover leftover vs leftover leftover leftover AsyncAPI (not a3-bind)",
            fetch1="https://github.com/cloudevents/spec/blob/v1.0.2/cloudevents/bindings/http-protocol-binding.md",
            fetch1_ok="CloudEvents leftover leftover leftover http mode is not AsyncAPI leftover leftover leftover kafka.",
            fetch2="https://www.asyncapi.com/docs/reference/specification/v3.0.0#messageBindingsObject",
            fetch2_ok="Exclusive CloudEvents leftover leftover leftover 400s leftover leftover leftover AsyncAPI bindings.",
        ),
    ),
    (
        plant(
            slug="jsonapi-lll3-sparse",
            domain="jsonapi-lll3-sparse-vs-hal-lll3",
            success=True,
            name="jap3s",
            stack="JSON:API leftover leftover leftover sparse + Go",
            field="fields",
            old="HAL leftover leftover leftover curie",
            new="JSON:API leftover leftover leftover sparse fieldset",
            fail_err="400: leftover leftover leftover HAL after JSON:API leftover leftover leftover sparse-only",
            plan="JSON:API leftover leftover leftover sparse-only 400s leftover leftover leftover HAL. Dual-read curie for one release.",
            residual="SPA still HAL leftover leftover leftover; drop after spa 7",
            vs="r3714 JSON:API leftover leftover leftover vs leftover leftover leftover HAL (not type-id)",
            fetch1="https://jsonapi.org/format/#fetching-sparse-fieldsets",
            fetch1_ok="JSON:API leftover leftover leftover sparse fieldsets are not HAL leftover leftover leftover curies.",
            fetch2="https://stateless.group/hal_specification.html",
            fetch2_ok="Exclusive JSON:API leftover leftover leftover 415s leftover leftover leftover HAL curie.",
        ),
        plant(
            slug="hal-lll3-curie",
            domain="hal-lll3-curie-vs-jsonapi-lll3",
            success=False,
            name="hal3c",
            stack="OpenAPI leftover leftover leftover 3.1 + Java + TS",
            field="curies",
            old="JSON:API leftover leftover leftover sparse fieldset",
            new="HAL leftover leftover leftover curie only",
            fail_err="400: leftover leftover leftover JSON:API after HAL leftover leftover leftover curie-only",
            plan="HAL leftover leftover leftover curie-only 400s leftover leftover leftover JSON:API. Freeze fields, spec HAL leftover leftover leftover.",
            residual="handoff: keep JSON:API leftover leftover leftover or force HAL leftover leftover leftover curie",
            vs="r3714 HAL leftover leftover leftover vs leftover leftover leftover JSON:API (not links-only)",
            fetch1="https://stateless.group/hal_specification.html",
            fetch1_ok="HAL leftover leftover leftover curies are not JSON:API leftover leftover leftover sparse.",
            fetch2="https://jsonapi.org/format/#fetching-sparse-fieldsets",
            fetch2_ok="Exclusive HAL leftover leftover leftover 415s leftover leftover leftover JSON:API sparse.",
        ),
    ),
    (
        plant(
            slug="capnp-lll3-packed",
            domain="capnp-lll3-packed-vs-fb-lll3",
            success=True,
            name="cap3p",
            stack="Cap'n leftover leftover leftover packed + Go",
            field="packing",
            old="FlatBuffers leftover leftover leftover flexbuffers",
            new="Cap'n leftover leftover leftover packed framing",
            fail_err="415: leftover leftover leftover FlatBuffers after Cap'n leftover leftover leftover packed-only",
            plan="Cap'n leftover leftover leftover packed-only 415s leftover leftover leftover FlatBuffers. Dual-decode flexbuffers for one release.",
            residual="game still FlatBuffers leftover leftover leftover; drop after game 4",
            vs="r3714 Cap'n leftover leftover leftover vs leftover leftover leftover FlatBuffers (not lll-rpc)",
            fetch1="https://capnproto.org/encoding.html#packing",
            fetch1_ok="Cap'n leftover leftover leftover packing is not FlatBuffers leftover leftover leftover flexbuffers.",
            fetch2="https://flatbuffers.dev/flexbuffers.html",
            fetch2_ok="Exclusive Cap'n leftover leftover leftover packed 415 leftover leftover leftover FlatBuffers.",
        ),
        plant(
            slug="flatbuffers-lll3-flex",
            domain="fb-lll3-flex-vs-capnp-lll3",
            success=False,
            name="fb3f",
            stack="OpenAPI leftover leftover leftover 3.1 + Java + TS",
            field="content",
            old="Cap'n leftover leftover leftover packed framing",
            new="FlatBuffers leftover leftover leftover flexbuffers only",
            fail_err="415: leftover leftover leftover Cap'n after FlatBuffers leftover leftover leftover flex-only",
            plan="FlatBuffers leftover leftover leftover flex-only 415s leftover leftover leftover Cap'n. Freeze packing, spec FlatBuffers leftover leftover leftover.",
            residual="handoff: keep Cap'n leftover leftover leftover or force FlatBuffers leftover leftover leftover flex",
            vs="r3714 FlatBuffers leftover leftover leftover vs leftover leftover leftover Cap'n (not vtable)",
            fetch1="https://flatbuffers.dev/flexbuffers.html",
            fetch1_ok="FlatBuffers leftover leftover leftover flexbuffers are not Cap'n leftover leftover leftover packed.",
            fetch2="https://capnproto.org/encoding.html#packing",
            fetch2_ok="Exclusive FlatBuffers leftover leftover leftover 415s leftover leftover leftover Cap'n packed.",
        ),
    ),
    (
        plant(
            slug="msgpack-lll3-bin8",
            domain="msgpack-lll3-bin8-vs-ion-lll3",
            success=True,
            name="mp3b",
            stack="MessagePack leftover leftover leftover bin8 + Go",
            field="content",
            old="Ion leftover leftover leftover symbol table",
            new="MessagePack leftover leftover leftover bin8",
            fail_err="415: leftover leftover leftover Ion after MessagePack leftover leftover leftover bin8-only",
            plan="MessagePack leftover leftover leftover bin8-only 415s leftover leftover leftover Ion. Dual-decode symbol table for one release.",
            residual="stream still Ion leftover leftover leftover; drop after stream 5",
            vs="r3714 MessagePack leftover leftover leftover vs leftover leftover leftover Ion (not fixmap)",
            fetch1="https://github.com/msgpack/msgpack/blob/master/spec.md#bin-format-family",
            fetch1_ok="MessagePack leftover leftover leftover bin8 is not Ion leftover leftover leftover symbols.",
            fetch2="https://amazon-ion.github.io/ion-docs/docs/symbols.html",
            fetch2_ok="Exclusive MessagePack leftover leftover leftover 415s leftover leftover leftover Ion symbols.",
        ),
        plant(
            slug="ion-lll3-symbol",
            domain="ion-lll3-symbol-vs-msgpack-lll3",
            success=False,
            name="ion3y",
            stack="OpenAPI leftover leftover leftover 3.1 + Java + TS",
            field="content",
            old="MessagePack leftover leftover leftover bin8",
            new="Ion leftover leftover leftover symbol only",
            fail_err="415: leftover leftover leftover MessagePack after Ion leftover leftover leftover symbol-only",
            plan="Ion leftover leftover leftover symbol-only 415s leftover leftover leftover MessagePack. Freeze bin8, spec Ion leftover leftover leftover.",
            residual="handoff: keep MessagePack leftover leftover leftover or force Ion leftover leftover leftover symbols",
            vs="r3714 Ion leftover leftover leftover vs leftover leftover leftover MessagePack (not BVM)",
            fetch1="https://amazon-ion.github.io/ion-docs/docs/symbols.html",
            fetch1_ok="Ion leftover leftover leftover symbols are not MessagePack leftover leftover leftover bin8.",
            fetch2="https://github.com/msgpack/msgpack/blob/master/spec.md#bin-format-family",
            fetch2_ok="Exclusive Ion leftover leftover leftover 415s leftover leftover leftover MessagePack bin8.",
        ),
    ),
    (
        plant(
            slug="avro-lll3-schema",
            domain="avro-lll3-schema-vs-thrift-lll3",
            success=True,
            name="avr3s",
            stack="Avro leftover leftover leftover schema + Go",
            field="schema",
            old="Thrift leftover leftover leftover IDL",
            new="Avro leftover leftover leftover writer schema",
            fail_err="415: leftover leftover leftover Thrift after Avro leftover leftover leftover schema-only",
            plan="Avro leftover leftover leftover schema-only 415s leftover leftover leftover Thrift. Dual-decode IDL for one release.",
            residual="rpc still Thrift leftover leftover leftover; drop after rpc 4",
            vs="r3714 Avro leftover leftover leftover vs leftover leftover leftover Thrift (not OCF)",
            fetch1="https://avro.apache.org/docs/1.11.1/specification/#schema-declaration",
            fetch1_ok="Avro leftover leftover leftover writer schema is not Thrift leftover leftover leftover IDL.",
            fetch2="https://thrift.apache.org/docs/idl",
            fetch2_ok="Exclusive Avro leftover leftover leftover 415s leftover leftover leftover Thrift IDL.",
        ),
        plant(
            slug="thrift-lll3-idl",
            domain="thrift-lll3-idl-vs-avro-lll3",
            success=False,
            name="th3i",
            stack="OpenAPI leftover leftover leftover 3.1 + Java + TS",
            field="idl",
            old="Avro leftover leftover leftover writer schema",
            new="Thrift leftover leftover leftover IDL only",
            fail_err="415: leftover leftover leftover Avro after Thrift leftover leftover leftover IDL-only",
            plan="Thrift leftover leftover leftover IDL-only 415s leftover leftover leftover Avro. Freeze writer schema, spec Thrift leftover leftover leftover.",
            residual="handoff: keep Avro leftover leftover leftover or force Thrift leftover leftover leftover IDL",
            vs="r3714 Thrift leftover leftover leftover vs leftover leftover leftover Avro (not compact)",
            fetch1="https://thrift.apache.org/docs/idl",
            fetch1_ok="Thrift leftover leftover leftover IDL is not Avro leftover leftover leftover schema.",
            fetch2="https://avro.apache.org/docs/1.11.1/specification/#schema-declaration",
            fetch2_ok="Exclusive Thrift leftover leftover leftover 415s leftover leftover leftover Avro schema.",
        ),
    ),
    (
        plant(
            slug="fhir-lll3-bundle",
            domain="fhir-lll3-bundle-vs-hl7-lll3",
            success=True,
            name="fhir3b",
            stack="FHIR leftover leftover leftover Bundle + Go",
            field="entry",
            old="HL7 leftover leftover leftover v2 MSH",
            new="FHIR leftover leftover leftover Bundle entry",
            fail_err="400: leftover leftover leftover HL7 after FHIR leftover leftover leftover Bundle-only",
            plan="FHIR leftover leftover leftover Bundle-only 400s leftover leftover leftover HL7. Dual-read MSH for one release.",
            residual="lab still HL7 leftover leftover leftover; drop after lab 6",
            vs="r3714 FHIR leftover leftover leftover vs leftover leftover leftover HL7 (not R4 JSON)",
            fetch1="https://hl7.org/fhir/R4/bundle.html",
            fetch1_ok="FHIR leftover leftover leftover Bundle is not HL7 leftover leftover leftover v2 MSH.",
            fetch2="https://www.hl7.org/implement/standards/product_brief.cfm?product_id=185",
            fetch2_ok="Exclusive FHIR leftover leftover leftover Bundle 400 leftover leftover leftover HL7.",
        ),
        plant(
            slug="hl7-lll3-msh",
            domain="hl7-lll3-msh-vs-fhir-lll3",
            success=False,
            name="hl73m",
            stack="OpenAPI leftover leftover leftover 3.1 + Java + TS",
            field="MSH",
            old="FHIR leftover leftover leftover Bundle entry",
            new="HL7 leftover leftover leftover v2 MSH only",
            fail_err="400: leftover leftover leftover FHIR after HL7 leftover leftover leftover MSH-only",
            plan="HL7 leftover leftover leftover MSH-only 400s leftover leftover leftover FHIR. Freeze Bundle, spec HL7 leftover leftover leftover.",
            residual="handoff: keep FHIR leftover leftover leftover or force HL7 leftover leftover leftover MSH",
            vs="r3714 HL7 leftover leftover leftover vs leftover leftover leftover FHIR (not v2-pipe slug)",
            fetch1="https://www.hl7.org/implement/standards/product_brief.cfm?product_id=185",
            fetch1_ok="HL7 leftover leftover leftover MSH is not FHIR leftover leftover leftover Bundle.",
            fetch2="https://hl7.org/fhir/R4/bundle.html",
            fetch2_ok="Exclusive HL7 leftover leftover leftover 400s leftover leftover leftover FHIR Bundle.",
        ),
    ),
    (
        plant(
            slug="graphql-lll3-sub-grpc",
            domain="graphql-lll3-sub-vs-grpc-lll3",
            success=True,
            name="gql3s",
            stack="GraphQL leftover leftover leftover subscription + Go",
            field="subscription",
            old="gRPC leftover leftover leftover server stream",
            new="GraphQL leftover leftover leftover subscription",
            fail_err="400: leftover leftover leftover gRPC after GraphQL leftover leftover leftover subscription-only",
            plan="GraphQL leftover leftover leftover subscription-only 400s leftover leftover leftover gRPC. Dual-bind stream for one release.",
            residual="mesh still gRPC leftover leftover leftover; drop after mesh 4",
            vs="r3714 GraphQL leftover leftover leftover vs leftover leftover leftover gRPC (not REST schema)",
            fetch1="https://spec.graphql.org/October2021/#sec-Subscription",
            fetch1_ok="GraphQL leftover leftover leftover subscriptions are not gRPC leftover leftover leftover streams.",
            fetch2="https://github.com/grpc/grpc/blob/master/doc/PROTOCOL-HTTP2.md",
            fetch2_ok="Exclusive GraphQL leftover leftover leftover 400s leftover leftover leftover gRPC streams.",
        ),
        plant(
            slug="grpc-lll3-stream-gql",
            domain="grpc-lll3-stream-vs-graphql-lll3",
            success=False,
            name="gr3s",
            stack="gRPC leftover leftover leftover stream + Java + TS",
            field="stream",
            old="GraphQL leftover leftover leftover subscription",
            new="gRPC leftover leftover leftover server stream only",
            fail_err="415: leftover leftover leftover GraphQL after gRPC leftover leftover leftover stream-only",
            plan="gRPC leftover leftover leftover stream-only 415s leftover leftover leftover GraphQL. Freeze subscription, spec gRPC leftover leftover leftover.",
            residual="handoff: keep GraphQL leftover leftover leftover or force gRPC leftover leftover leftover stream",
            vs="r3714 gRPC leftover leftover leftover vs leftover leftover leftover GraphQL (not HTTP proto)",
            fetch1="https://github.com/grpc/grpc/blob/master/doc/PROTOCOL-HTTP2.md",
            fetch1_ok="gRPC leftover leftover leftover streams are not GraphQL leftover leftover leftover subscriptions.",
            fetch2="https://spec.graphql.org/October2021/#sec-Subscription",
            fetch2_ok="Exclusive gRPC leftover leftover leftover 415s leftover leftover leftover GraphQL subscriptions.",
        ),
    ),
    (
        plant(
            slug="oas-lll3-proto-oneof",
            domain="oas-lll3-oneof-vs-protobuf-lll3",
            success=True,
            name="oas3n",
            stack="OpenAPI leftover leftover leftover oneOf + protobuf leftover leftover leftover + Go",
            field="oneOf",
            old="protobuf leftover leftover leftover oneof",
            new="OpenAPI leftover leftover leftover oneOf media",
            fail_err="415: leftover leftover leftover protobuf after OpenAPI leftover leftover leftover oneOf-only",
            plan="OpenAPI leftover leftover leftover oneOf-only 415s leftover leftover leftover protobuf. Dual-decode oneof for one release.",
            residual="rpc still protobuf leftover leftover leftover; drop after rpc 5",
            vs="r3714 OpenAPI leftover leftover leftover vs leftover leftover leftover protobuf (not RAML paths)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#discriminator-object",
            fetch1_ok="OpenAPI leftover leftover leftover oneOf is not protobuf leftover leftover leftover oneof.",
            fetch2="https://protobuf.dev/programming-guides/proto3/#oneof",
            fetch2_ok="Exclusive OpenAPI leftover leftover leftover 415s leftover leftover leftover protobuf oneof.",
        ),
        plant(
            slug="protobuf-lll3-oneof-oas",
            domain="protobuf-lll3-oneof-vs-oas-lll3",
            success=False,
            name="pb3n",
            stack="protobuf leftover leftover leftover + Java + TS",
            field="oneof",
            old="OpenAPI leftover leftover leftover oneOf media",
            new="protobuf leftover leftover leftover oneof only",
            fail_err="415: leftover leftover leftover OpenAPI after protobuf leftover leftover leftover oneof-only",
            plan="protobuf leftover leftover leftover oneof-only 415s leftover leftover leftover OpenAPI. Freeze oneOf, spec protobuf leftover leftover leftover.",
            residual="handoff: keep OpenAPI leftover leftover leftover or force protobuf leftover leftover leftover oneof",
            vs="r3714 protobuf leftover leftover leftover vs leftover leftover leftover OpenAPI (not json wire)",
            fetch1="https://protobuf.dev/programming-guides/proto3/#oneof",
            fetch1_ok="protobuf leftover leftover leftover oneof is not OpenAPI leftover leftover leftover oneOf.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#discriminator-object",
            fetch2_ok="Exclusive protobuf leftover leftover leftover 415s leftover leftover leftover OpenAPI oneOf.",
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
    print(json.dumps({"round": round_n, "idx": idx, "ids": [e1["id"], e2["id"]], "catalog": "r3787"}))


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
