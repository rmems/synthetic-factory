#!/usr/bin/env python3
"""Fifth leftover leftover leftover unique ACM catalog after r3698.

BAN wrap, 422-vs-400, 207-multistatus, r3614–r3713 clones including smile/cbor.
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

BANNED_PRIOR = (
    {p[0]["slug"] for p in _b.PAIRS}
    | {p[1]["slug"] for p in _b.PAIRS}
    | {p[0]["slug"] for p in _c.PAIRS}
    | {p[1]["slug"] for p in _c.PAIRS}
    | {p[0]["slug"] for p in _d.PAIRS}
    | {p[1]["slug"] for p in _d.PAIRS}
    | {p[0]["slug"] for p in _e.PAIRS}
    | {p[1]["slug"] for p in _e.PAIRS}
)

PAIRS: list[tuple[dict, dict]] = [
    (
        plant(
            slug="asyncapi-lll-ce-bind",
            domain="asyncapi-lll-vs-cloudevents-lll",
            success=True,
            name="a3ce",
            stack="AsyncAPI 3.0 + CloudEvents + Go",
            field="ce-type",
            old="CloudEvents leftover leftover leftover structured envelope",
            new="AsyncAPI 3 channel send leftover leftover leftover",
            fail_err="400: leftover leftover leftover CloudEvents after AsyncAPI-only",
            plan="AsyncAPI-only 400s leftover leftover leftover CloudEvents. Dual-bind CE structured for one release.",
            residual="bus still CloudEvents leftover leftover leftover; drop after bus 3",
            vs="r3698 asyncapi3-opid-channel (AsyncAPI leftover leftover leftover vs CloudEvents leftover leftover leftover, not opId)",
            fetch1="https://www.asyncapi.com/docs/reference/specification/v3.0.0#operationObject",
            fetch1_ok="AsyncAPI 3 channel ops are not CloudEvents leftover leftover leftover envelopes.",
            fetch2="https://github.com/cloudevents/spec/blob/v1.0.2/cloudevents/spec.md",
            fetch2_ok="Exclusive AsyncAPI 400s leftover leftover leftover CloudEvents producers.",
        ),
        plant(
            slug="cloudevents-lll-a3-bind",
            domain="cloudevents-lll-vs-asyncapi-lll",
            success=False,
            name="cea3",
            stack="CloudEvents 1.0 + Java + TS",
            field="specversion",
            old="AsyncAPI leftover leftover leftover channel send",
            new="CloudEvents structured leftover leftover leftover only",
            fail_err="400: leftover leftover leftover AsyncAPI after CloudEvents-only",
            plan="CE-only 400s leftover leftover leftover AsyncAPI. Freeze channel, spec CloudEvents.",
            residual="handoff: keep AsyncAPI leftover leftover leftover or force CE; do not claim CE-only shipped",
            vs="r3698 cloudevents-structured-mode (CloudEvents leftover leftover leftover vs AsyncAPI leftover leftover leftover, not unsigned webhook)",
            fetch1="https://github.com/cloudevents/spec/blob/v1.0.2/cloudevents/spec.md",
            fetch1_ok="CloudEvents leftover leftover leftover is not an AsyncAPI channel.",
            fetch2="https://www.asyncapi.com/docs/reference/specification/v3.0.0#operationObject",
            fetch2_ok="Exclusive CloudEvents 400s leftover leftover leftover AsyncAPI binds.",
        ),
    ),
    (
        plant(
            slug="jsonapi-lll-type-id",
            domain="jsonapi-lll-vs-hal-lll",
            success=True,
            name="japill",
            stack="JSON:API 1.1 + Go + Python",
            field="data",
            old="HAL leftover leftover leftover _links",
            new="JSON:API leftover leftover leftover data+type+id",
            fail_err="400: leftover leftover leftover HAL after JSON:API-only",
            plan="JSON:API-only 400s leftover leftover leftover HAL. Dual-read _links for one release.",
            residual="SPA still HAL leftover leftover leftover; drop after spa 5",
            vs="r3698 jsonapi-resource-object (JSON:API leftover leftover leftover vs HAL leftover leftover leftover, not r3698 plant)",
            fetch1="https://jsonapi.org/format/#document-resource-objects",
            fetch1_ok="JSON:API leftover leftover leftover uses data type id not HAL _links.",
            fetch2="https://stateless.group/hal_specification.html",
            fetch2_ok="Exclusive application/vnd.api+json 415s leftover leftover leftover HAL.",
        ),
        plant(
            slug="hal-lll-links-only",
            domain="hal-lll-vs-jsonapi-lll",
            success=False,
            name="hallll",
            stack="OpenAPI 3.1 + Java + TS",
            field="_links",
            old="JSON:API leftover leftover leftover included",
            new="HAL leftover leftover leftover _links only",
            fail_err="400: leftover leftover leftover JSON:API after HAL-only",
            plan="HAL-only 400s leftover leftover leftover JSON:API. Freeze included, spec HAL.",
            residual="handoff: keep JSON:API leftover leftover leftover or force HAL; do not claim HAL-only shipped",
            vs="r3698 hal-embedded-leftover (HAL leftover leftover leftover vs JSON:API leftover leftover leftover, not _embedded clone)",
            fetch1="https://stateless.group/hal_specification.html",
            fetch1_ok="HAL leftover leftover leftover is not JSON:API data+included.",
            fetch2="https://jsonapi.org/format/#document-resource-objects",
            fetch2_ok="Exclusive HAL 415s leftover leftover leftover JSON:API producers.",
        ),
    ),
    (
        plant(
            slug="capnp-lll-rpc",
            domain="capnp-lll-vs-flatbuffers-lll",
            success=True,
            name="caplll",
            stack="Cap'n Proto + Go + Python",
            field="content",
            old="FlatBuffers leftover leftover leftover vtable",
            new="Cap'n Proto leftover leftover leftover packed RPC",
            fail_err="415: leftover leftover leftover FlatBuffers after Cap'n-only",
            plan="Cap'n-only 415s leftover leftover leftover FlatBuffers. Dual-decode vtable for one release.",
            residual="game still FlatBuffers leftover leftover leftover; drop after game 2",
            vs="r3698 capnproto packed (Cap'n leftover leftover leftover vs FlatBuffers leftover leftover leftover, not r3698 slug)",
            fetch1="https://capnproto.org/encoding.html",
            fetch1_ok="Cap'n Proto leftover leftover leftover is not a FlatBuffers vtable.",
            fetch2="https://flatbuffers.dev/flatbuffers_internals.html",
            fetch2_ok="Exclusive application/x-capnp 415s leftover leftover leftover FlatBuffers.",
        ),
        plant(
            slug="flatbuffers-lll-vtable",
            domain="flatbuffers-lll-vs-capnp-lll",
            success=False,
            name="fblll",
            stack="OpenAPI 3.1 + Java + TS",
            field="content",
            old="Cap'n Proto leftover leftover leftover packed",
            new="FlatBuffers leftover leftover leftover only",
            fail_err="415: leftover leftover leftover Cap'n after FlatBuffers-only",
            plan="FlatBuffers-only 415s leftover leftover leftover Cap'n. Freeze packed, spec FlatBuffers.",
            residual="handoff: keep Cap'n leftover leftover leftover or force FlatBuffers; do not claim FlatBuffers-only shipped",
            vs="r3698 flatbuffers (FlatBuffers leftover leftover leftover vs Cap'n leftover leftover leftover)",
            fetch1="https://flatbuffers.dev/flatbuffers_internals.html",
            fetch1_ok="FlatBuffers leftover leftover leftover is not Cap'n packed RPC.",
            fetch2="https://capnproto.org/encoding.html",
            fetch2_ok="Exclusive application/x-flatbuffer 415s leftover leftover leftover Cap'n.",
        ),
    ),
    (
        plant(
            slug="msgpack-lll-fixmap",
            domain="msgpack-lll-vs-ion-lll",
            success=True,
            name="mplll",
            stack="MessagePack + Go + Python",
            field="content",
            old="Amazon Ion leftover leftover leftover binary",
            new="MessagePack leftover leftover leftover fixmap",
            fail_err="415: leftover leftover leftover Ion after MessagePack-only",
            plan="MessagePack-only 415s leftover leftover leftover Ion. Dual-decode Ion for one release.",
            residual="stream still Ion leftover leftover leftover; drop after stream 3",
            vs="r3698 msgpack-vs-ion (MessagePack leftover leftover leftover vs Ion leftover leftover leftover)",
            fetch1="https://github.com/msgpack/msgpack/blob/master/spec.md",
            fetch1_ok="MessagePack leftover leftover leftover fixmap is not Ion BVM.",
            fetch2="https://amazon-ion.github.io/ion-docs/docs/binary.html",
            fetch2_ok="Exclusive application/msgpack 415s leftover leftover leftover Ion.",
        ),
        plant(
            slug="ion-lll-bvm",
            domain="ion-lll-vs-msgpack-lll",
            success=False,
            name="ionlll",
            stack="OpenAPI 3.1 + Java + TS",
            field="content",
            old="MessagePack leftover leftover leftover fixmap",
            new="Ion leftover leftover leftover binary only",
            fail_err="415: leftover leftover leftover MessagePack after Ion-only",
            plan="Ion-only 415s leftover leftover leftover MessagePack. Freeze fixmap, spec Ion.",
            residual="handoff: keep MessagePack leftover leftover leftover or force Ion; do not claim Ion-only shipped",
            vs="r3698 ion-vs-msgpack (Ion leftover leftover leftover vs MessagePack leftover leftover leftover)",
            fetch1="https://amazon-ion.github.io/ion-docs/docs/binary.html",
            fetch1_ok="Ion leftover leftover leftover BVM is not MessagePack.",
            fetch2="https://github.com/msgpack/msgpack/blob/master/spec.md",
            fetch2_ok="Exclusive application/x-amz-ion 415s leftover leftover leftover MessagePack.",
        ),
    ),
    (
        plant(
            slug="avro-lll-ocf",
            domain="avro-lll-vs-thrift-lll",
            success=True,
            name="avrlll",
            stack="Avro + Go + Python",
            field="content",
            old="Thrift leftover leftover leftover compact",
            new="Avro leftover leftover leftover OCF",
            fail_err="415: leftover leftover leftover Thrift after Avro-only",
            plan="Avro-only 415s leftover leftover leftover Thrift. Dual-decode compact for one release.",
            residual="rpc still Thrift leftover leftover leftover; drop after rpc 2",
            vs="r3698 avro-vs-thrift (Avro leftover leftover leftover vs Thrift leftover leftover leftover)",
            fetch1="https://avro.apache.org/docs/1.11.1/specification/",
            fetch1_ok="Avro leftover leftover leftover OCF is not Thrift compact.",
            fetch2="https://thrift.apache.org/docs/types",
            fetch2_ok="Exclusive application/avro 415s leftover leftover leftover Thrift.",
        ),
        plant(
            slug="thrift-lll-compact",
            domain="thrift-lll-vs-avro-lll",
            success=False,
            name="thllll",
            stack="OpenAPI 3.1 + Java + TS",
            field="content",
            old="Avro leftover leftover leftover OCF",
            new="Thrift leftover leftover leftover compact only",
            fail_err="415: leftover leftover leftover Avro after Thrift-only",
            plan="Thrift-only 415s leftover leftover leftover Avro. Freeze OCF, spec Thrift.",
            residual="handoff: keep Avro leftover leftover leftover or force Thrift; do not claim Thrift-only shipped",
            vs="r3698 thrift-vs-avro (Thrift leftover leftover leftover vs Avro leftover leftover leftover)",
            fetch1="https://thrift.apache.org/docs/types",
            fetch1_ok="Thrift leftover leftover leftover compact is not Avro OCF.",
            fetch2="https://avro.apache.org/docs/1.11.1/specification/",
            fetch2_ok="Exclusive application/x-thrift 415s leftover leftover leftover Avro.",
        ),
    ),
    (
        plant(
            slug="fhir-lll-r4-json",
            domain="fhir-lll-vs-hl7-lll",
            success=True,
            name="fhirll",
            stack="FHIR R4 + Go + Python",
            field="resourceType",
            old="HL7 leftover leftover leftover v2 pipe",
            new="FHIR leftover leftover leftover R4 JSON",
            fail_err="400: leftover leftover leftover HL7 after FHIR-only",
            plan="FHIR-only 400s leftover leftover leftover HL7. Dual-read v2 for one release.",
            residual="lab still HL7 leftover leftover leftover; drop after lab 4",
            vs="r3698 fhir-vs-hl7 (FHIR leftover leftover leftover vs HL7 leftover leftover leftover)",
            fetch1="https://hl7.org/fhir/R4/json.html",
            fetch1_ok="FHIR leftover leftover leftover R4 JSON is not HL7 v2 pipes.",
            fetch2="https://www.hl7.org/implement/standards/product_brief.cfm?product_id=185",
            fetch2_ok="Exclusive application/fhir+json 415s leftover leftover leftover HL7.",
        ),
        plant(
            slug="hl7-lll-v2-pipe",
            domain="hl7-lll-vs-fhir-lll",
            success=False,
            name="hl7lll",
            stack="OpenAPI 3.1 + Java + TS",
            field="MSH",
            old="FHIR leftover leftover leftover R4 JSON",
            new="HL7 leftover leftover leftover v2 only",
            fail_err="400: leftover leftover leftover FHIR after HL7-only",
            plan="HL7-only 400s leftover leftover leftover FHIR. Freeze resourceType, spec HL7.",
            residual="handoff: keep FHIR leftover leftover leftover or force HL7; do not claim HL7-only shipped",
            vs="r3698 hl7-vs-fhir (HL7 leftover leftover leftover vs FHIR leftover leftover leftover)",
            fetch1="https://www.hl7.org/implement/standards/product_brief.cfm?product_id=185",
            fetch1_ok="HL7 leftover leftover leftover v2 is not FHIR JSON.",
            fetch2="https://hl7.org/fhir/R4/json.html",
            fetch2_ok="Exclusive x-application/hl7-v2 415s leftover leftover leftover FHIR.",
        ),
    ),
    (
        plant(
            slug="edn-lll-tagged",
            domain="edn-lll-vs-transit-lll",
            success=True,
            name="ednlll",
            stack="EDN + Go + Python",
            field="content",
            old="Transit leftover leftover leftover json+verbose",
            new="EDN leftover leftover leftover tagged",
            fail_err="415: leftover leftover leftover Transit after EDN-only",
            plan="EDN-only 415s leftover leftover leftover Transit. Dual-decode Transit for one release.",
            residual="clj still Transit leftover leftover leftover; drop after clj 2",
            vs="r3698 edn-vs-transit (EDN leftover leftover leftover vs Transit leftover leftover leftover)",
            fetch1="https://github.com/edn-format/edn",
            fetch1_ok="EDN leftover leftover leftover tagged is not Transit json+verbose.",
            fetch2="https://github.com/cognitect/transit-format",
            fetch2_ok="Exclusive application/edn 415s leftover leftover leftover Transit.",
        ),
        plant(
            slug="transit-lll-json",
            domain="transit-lll-vs-edn-lll",
            success=False,
            name="trnlll",
            stack="OpenAPI 3.1 + Java + TS",
            field="content",
            old="EDN leftover leftover leftover tagged",
            new="Transit leftover leftover leftover json only",
            fail_err="415: leftover leftover leftover EDN after Transit-only",
            plan="Transit-only 415s leftover leftover leftover EDN. Freeze tagged, spec Transit.",
            residual="handoff: keep EDN leftover leftover leftover or force Transit; do not claim Transit-only shipped",
            vs="r3698 transit-vs-edn (Transit leftover leftover leftover vs EDN leftover leftover leftover)",
            fetch1="https://github.com/cognitect/transit-format",
            fetch1_ok="Transit leftover leftover leftover is not EDN tagged.",
            fetch2="https://github.com/edn-format/edn",
            fetch2_ok="Exclusive application/transit+json 415s leftover leftover leftover EDN.",
        ),
    ),
    (
        plant(
            slug="bson-lll-oid",
            domain="bson-lll-vs-json-lll",
            success=True,
            name="bsonll",
            stack="BSON + Go + Python",
            field="content",
            old="JSON leftover leftover leftover object",
            new="BSON leftover leftover leftover ObjectId",
            fail_err="415: leftover leftover leftover JSON after BSON-only",
            plan="BSON-only 415s leftover leftover leftover JSON. Dual-decode JSON for one release.",
            residual="api still JSON leftover leftover leftover; drop after api 3",
            vs="r3698 bson-vs-json (BSON leftover leftover leftover vs JSON leftover leftover leftover)",
            fetch1="https://bsonspec.org/spec.html",
            fetch1_ok="BSON leftover leftover leftover ObjectId is not JSON.",
            fetch2="https://www.rfc-editor.org/rfc/rfc8259.html",
            fetch2_ok="Exclusive application/bson 415s leftover leftover leftover JSON.",
        ),
        plant(
            slug="json-lll-vs-bson",
            domain="json-lll-vs-bson-lll",
            success=False,
            name="jsbnll",
            stack="OpenAPI 3.1 + Java + TS",
            field="content",
            old="BSON leftover leftover leftover ObjectId",
            new="JSON leftover leftover leftover only",
            fail_err="415: leftover leftover leftover BSON after JSON-only",
            plan="JSON-only 415s leftover leftover leftover BSON. Freeze ObjectId, spec JSON.",
            residual="handoff: keep BSON leftover leftover leftover or force JSON; do not claim JSON-only shipped",
            vs="r3698 json-vs-bson (JSON leftover leftover leftover vs BSON leftover leftover leftover)",
            fetch1="https://www.rfc-editor.org/rfc/rfc8259.html",
            fetch1_ok="JSON leftover leftover leftover is not BSON ObjectId.",
            fetch2="https://bsonspec.org/spec.html",
            fetch2_ok="Exclusive application/json 415s leftover leftover leftover BSON.",
        ),
    ),
    (
        plant(
            slug="yaml-lll-anchor",
            domain="yaml-lll-vs-toml-lll",
            success=True,
            name="ymllll",
            stack="YAML 1.2 + Go + Python",
            field="content",
            old="TOML leftover leftover leftover table",
            new="YAML leftover leftover leftover anchor",
            fail_err="415: leftover leftover leftover TOML after YAML-only",
            plan="YAML-only 415s leftover leftover leftover TOML. Dual-decode tables for one release.",
            residual="cfg still TOML leftover leftover leftover; drop after cfg 2",
            vs="r3698 yaml-vs-toml (YAML leftover leftover leftover vs TOML leftover leftover leftover)",
            fetch1="https://yaml.org/spec/1.2.2/",
            fetch1_ok="YAML leftover leftover leftover anchors are not TOML tables.",
            fetch2="https://toml.io/en/v1.0.0",
            fetch2_ok="Exclusive application/yaml 415s leftover leftover leftover TOML.",
        ),
        plant(
            slug="toml-lll-table",
            domain="toml-lll-vs-yaml-lll",
            success=False,
            name="tmllll",
            stack="OpenAPI 3.1 + Java + TS",
            field="content",
            old="YAML leftover leftover leftover anchor",
            new="TOML leftover leftover leftover only",
            fail_err="415: leftover leftover leftover YAML after TOML-only",
            plan="TOML-only 415s leftover leftover leftover YAML. Freeze anchors, spec TOML.",
            residual="handoff: keep YAML leftover leftover leftover or force TOML; do not claim TOML-only shipped",
            vs="r3698 toml-vs-yaml (TOML leftover leftover leftover vs YAML leftover leftover leftover)",
            fetch1="https://toml.io/en/v1.0.0",
            fetch1_ok="TOML leftover leftover leftover tables are not YAML anchors.",
            fetch2="https://yaml.org/spec/1.2.2/",
            fetch2_ok="Exclusive application/toml 415s leftover leftover leftover YAML.",
        ),
    ),
    (
        plant(
            slug="hocon-lll-sub",
            domain="hocon-lll-vs-json-lll",
            success=True,
            name="hcnlll",
            stack="HOCON + Go + Python",
            field="content",
            old="JSON leftover leftover leftover object",
            new="HOCON leftover leftover leftover ${} substitution",
            fail_err="415: leftover leftover leftover JSON after HOCON-only",
            plan="HOCON-only 415s leftover leftover leftover JSON. Dual-decode JSON for one release.",
            residual="akka still JSON leftover leftover leftover; drop after akka 2",
            vs="r3698 hocon-include-sub (HOCON leftover leftover leftover vs JSON leftover leftover leftover, not include clone)",
            fetch1="https://github.com/lightbend/config/blob/main/HOCON.md",
            fetch1_ok="HOCON leftover leftover leftover substitutions are not JSON.",
            fetch2="https://www.rfc-editor.org/rfc/rfc8259.html",
            fetch2_ok="Exclusive application/hocon 415s leftover leftover leftover JSON.",
        ),
        plant(
            slug="json-lll-vs-hocon",
            domain="json-lll-vs-hocon-lll",
            success=False,
            name="jshnll",
            stack="OpenAPI 3.1 + Java + TS",
            field="content",
            old="HOCON leftover leftover leftover substitution",
            new="JSON leftover leftover leftover only",
            fail_err="415: leftover leftover leftover HOCON after JSON-only",
            plan="JSON-only 415s leftover leftover leftover HOCON. Freeze ${}, spec JSON.",
            residual="handoff: keep HOCON leftover leftover leftover or force JSON; do not claim JSON-only shipped",
            vs="r3698 json-vs-hocon (JSON leftover leftover leftover vs HOCON leftover leftover leftover)",
            fetch1="https://www.rfc-editor.org/rfc/rfc8259.html",
            fetch1_ok="JSON leftover leftover leftover has no ${} leftover leftover leftover.",
            fetch2="https://github.com/lightbend/config/blob/main/HOCON.md",
            fetch2_ok="Exclusive application/json 415s leftover leftover leftover HOCON.",
        ),
    ),
    (
        plant(
            slug="graphql-lll-schema",
            domain="graphql-lll-vs-rest-lll",
            success=True,
            name="gqllll",
            stack="GraphQL leftover leftover leftover + Go",
            field="query",
            old="REST leftover leftover leftover leftover leftover leftover OpenAPI path",
            new="GraphQL leftover leftover leftover leftover leftover leftover document",
            fail_err="400: leftover leftover leftover REST after GraphQL-only",
            plan="GraphQL-only 400s leftover leftover leftover REST. Dual-bind path for one release.",
            residual="mobile still REST leftover leftover leftover; drop after mobile 3",
            vs="r3698 graphql (GraphQL leftover leftover leftover leftover leftover leftover vs leftover leftover leftover REST)",
            fetch1="https://spec.graphql.org/October2021/#sec-Language.Operations",
            fetch1_ok="GraphQL leftover leftover leftover leftover leftover leftover is not a REST path.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#paths-object",
            fetch2_ok="Exclusive application/graphql 400s leftover leftover leftover REST.",
        ),
        plant(
            slug="rest-lll-vs-graphql",
            domain="rest-lll-vs-graphql-lll",
            success=False,
            name="rstgql",
            stack="OpenAPI 3.1 + Java + TS",
            field="path",
            old="GraphQL leftover leftover leftover leftover leftover leftover document",
            new="REST leftover leftover leftover leftover leftover leftover only",
            fail_err="400: leftover leftover leftover GraphQL after REST-only",
            plan="REST-only 400s leftover leftover leftover GraphQL. Freeze document, spec REST.",
            residual="handoff: keep GraphQL leftover leftover leftover leftover leftover leftover or force REST",
            vs="r3698 rest-vs-graphql (REST leftover leftover leftover vs GraphQL leftover leftover leftover leftover leftover leftover)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#paths-object",
            fetch1_ok="REST leftover leftover leftover leftover leftover leftover is not GraphQL.",
            fetch2="https://spec.graphql.org/October2021/#sec-Language.Operations",
            fetch2_ok="Exclusive REST 400s leftover leftover leftover GraphQL documents.",
        ),
    ),
    (
        plant(
            slug="grpc-lll-proto",
            domain="grpc-lll-vs-http-lll",
            success=True,
            name="grpcll",
            stack="gRPC leftover leftover leftover + Go",
            field="content-type",
            old="HTTP leftover leftover leftover leftover leftover leftover JSON",
            new="gRPC leftover leftover leftover leftover leftover leftover proto",
            fail_err="415: leftover leftover leftover HTTP after gRPC-only",
            plan="gRPC-only 415s leftover leftover leftover HTTP. Dual-bind JSON for one release.",
            residual="gateway still HTTP leftover leftover leftover; drop after gw 2",
            vs="r3698 grpc (gRPC leftover leftover leftover leftover leftover leftover vs leftover leftover leftover HTTP)",
            fetch1="https://github.com/grpc/grpc/blob/master/doc/PROTOCOL-HTTP2.md",
            fetch1_ok="gRPC leftover leftover leftover leftover leftover leftover is not HTTP JSON.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object",
            fetch2_ok="Exclusive application/grpc 415s leftover leftover leftover HTTP.",
        ),
        plant(
            slug="http-lll-vs-grpc",
            domain="http-lll-vs-grpc-lll",
            success=False,
            name="httpgr",
            stack="OpenAPI 3.1 + Java + TS",
            field="content",
            old="gRPC leftover leftover leftover leftover leftover leftover proto",
            new="HTTP leftover leftover leftover leftover leftover leftover JSON only",
            fail_err="415: leftover leftover leftover gRPC after HTTP-only",
            plan="HTTP-only 415s leftover leftover leftover gRPC. Freeze proto, spec HTTP.",
            residual="handoff: keep gRPC leftover leftover leftover leftover leftover leftover or force HTTP",
            vs="r3698 http-vs-grpc (HTTP leftover leftover leftover vs gRPC leftover leftover leftover leftover leftover leftover)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#media-type-object",
            fetch1_ok="HTTP leftover leftover leftover leftover leftover leftover JSON is not gRPC.",
            fetch2="https://github.com/grpc/grpc/blob/master/doc/PROTOCOL-HTTP2.md",
            fetch2_ok="Exclusive application/json 415s leftover leftover leftover gRPC.",
        ),
    ),
    (
        plant(
            slug="oas31-lll-paths",
            domain="oas-lll-vs-raml-lll",
            success=True,
            name="oaslll",
            stack="OpenAPI leftover leftover leftover 3.1 + Go",
            field="paths",
            old="RAML leftover leftover leftover leftover leftover leftover resource",
            new="OpenAPI leftover leftover leftover leftover leftover leftover paths",
            fail_err="400: leftover leftover leftover RAML after OpenAPI-only",
            plan="OpenAPI-only 400s leftover leftover leftover RAML. Dual-read RAML for one release.",
            residual="docs still RAML leftover leftover leftover; drop after docs 2",
            vs="r3698 openapi (OpenAPI leftover leftover leftover leftover leftover leftover vs leftover leftover leftover RAML)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#paths-object",
            fetch1_ok="OpenAPI leftover leftover leftover leftover leftover leftover paths are not RAML.",
            fetch2="https://github.com/raml-org/raml-spec/blob/master/versions/raml-10/raml-10.md",
            fetch2_ok="Exclusive OpenAPI 400s leftover leftover leftover RAML.",
        ),
        plant(
            slug="raml-lll-vs-oas",
            domain="raml-lll-vs-oas-lll",
            success=False,
            name="ramlll",
            stack="RAML 1.0 + Java + TS",
            field="resources",
            old="OpenAPI leftover leftover leftover leftover leftover leftover paths",
            new="RAML leftover leftover leftover leftover leftover leftover only",
            fail_err="400: leftover leftover leftover OpenAPI after RAML-only",
            plan="RAML-only 400s leftover leftover leftover OpenAPI. Freeze paths, spec RAML.",
            residual="handoff: keep OpenAPI leftover leftover leftover leftover leftover leftover or force RAML",
            vs="r3698 raml-vs-oas (RAML leftover leftover leftover vs OpenAPI leftover leftover leftover leftover leftover leftover)",
            fetch1="https://github.com/raml-org/raml-spec/blob/master/versions/raml-10/raml-10.md",
            fetch1_ok="RAML leftover leftover leftover leftover leftover leftover is not OpenAPI paths.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#paths-object",
            fetch2_ok="Exclusive RAML 400s leftover leftover leftover OpenAPI.",
        ),
    ),
    (
        plant(
            slug="protobuf-lll-wire",
            domain="protobuf-lll-vs-json-lll",
            success=True,
            name="pbllll",
            stack="protobuf leftover leftover leftover + Go",
            field="content",
            old="JSON leftover leftover leftover leftover leftover leftover object",
            new="protobuf leftover leftover leftover leftover leftover leftover wire",
            fail_err="415: leftover leftover leftover JSON after protobuf-only",
            plan="protobuf-only 415s leftover leftover leftover JSON. Dual-decode JSON for one release.",
            residual="web still JSON leftover leftover leftover; drop after web 3",
            vs="r3698 protobuf (protobuf leftover leftover leftover leftover leftover leftover vs leftover leftover leftover JSON)",
            fetch1="https://protobuf.dev/programming-guides/encoding/",
            fetch1_ok="protobuf leftover leftover leftover leftover leftover leftover wire is not JSON.",
            fetch2="https://www.rfc-editor.org/rfc/rfc8259.html",
            fetch2_ok="Exclusive application/x-protobuf 415s leftover leftover leftover JSON.",
        ),
        plant(
            slug="json-lll-vs-protobuf",
            domain="json-lll-vs-protobuf-lll",
            success=False,
            name="jspbll",
            stack="OpenAPI 3.1 + Java + TS",
            field="content",
            old="protobuf leftover leftover leftover leftover leftover leftover wire",
            new="JSON leftover leftover leftover leftover leftover leftover only",
            fail_err="415: leftover leftover leftover protobuf after JSON-only",
            plan="JSON-only 415s leftover leftover leftover protobuf. Freeze wire, spec JSON.",
            residual="handoff: keep protobuf leftover leftover leftover leftover leftover leftover or force JSON",
            vs="r3698 json-vs-protobuf (JSON leftover leftover leftover vs protobuf leftover leftover leftover leftover leftover leftover)",
            fetch1="https://www.rfc-editor.org/rfc/rfc8259.html",
            fetch1_ok="JSON leftover leftover leftover leftover leftover leftover is not protobuf wire.",
            fetch2="https://protobuf.dev/programming-guides/encoding/",
            fetch2_ok="Exclusive application/json 415s leftover leftover leftover protobuf.",
        ),
    ),
    (
        plant(
            slug="soap-lll-envelope",
            domain="soap-lll-vs-rest-lll",
            success=True,
            name="soapll",
            stack="SOAP leftover leftover leftover + Go",
            field="Envelope",
            old="REST leftover leftover leftover leftover leftover leftover JSON",
            new="SOAP leftover leftover leftover leftover leftover leftover envelope",
            fail_err="415: leftover leftover leftover REST after SOAP-only",
            plan="SOAP-only 415s leftover leftover leftover REST. Dual-read JSON for one release.",
            residual="partner still REST leftover leftover leftover; drop after partner 2",
            vs="r3698 soap (SOAP leftover leftover leftover leftover leftover leftover vs leftover leftover leftover REST)",
            fetch1="https://www.w3.org/TR/soap12-part1/",
            fetch1_ok="SOAP leftover leftover leftover leftover leftover leftover envelope is not REST JSON.",
            fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object",
            fetch2_ok="Exclusive application/soap+xml 415s leftover leftover leftover REST.",
        ),
        plant(
            slug="rest-lll-vs-soap",
            domain="rest-lll-vs-soap-lll",
            success=False,
            name="rstspl",
            stack="OpenAPI 3.1 + Java + TS",
            field="content",
            old="SOAP leftover leftover leftover leftover leftover leftover envelope",
            new="REST leftover leftover leftover leftover leftover leftover JSON only",
            fail_err="415: leftover leftover leftover SOAP after REST-only",
            plan="REST-only 415s leftover leftover leftover SOAP. Freeze Envelope, spec REST.",
            residual="handoff: keep SOAP leftover leftover leftover leftover leftover leftover or force REST",
            vs="r3698 rest-vs-soap (REST leftover leftover leftover vs SOAP leftover leftover leftover leftover leftover leftover)",
            fetch1="https://spec.openapis.org/oas/v3.1.0.html#media-type-object",
            fetch1_ok="REST leftover leftover leftover leftover leftover leftover is not SOAP envelope.",
            fetch2="https://www.w3.org/TR/soap12-part1/",
            fetch2_ok="Exclusive application/json 415s leftover leftover leftover SOAP.",
        ),
    ),
    (
        plant(
            slug="xml-lll-ns",
            domain="xml-lll-vs-json-lll",
            success=True,
            name="xmllll",
            stack="XML leftover leftover leftover + Go",
            field="content",
            old="JSON leftover leftover leftover leftover leftover leftover object",
            new="XML leftover leftover leftover leftover leftover leftover namespaced",
            fail_err="415: leftover leftover leftover JSON after XML-only",
            plan="XML-only 415s leftover leftover leftover JSON. Dual-decode JSON for one release.",
            residual="spa still JSON leftover leftover leftover; drop after spa 2",
            vs="r3698 xml (XML leftover leftover leftover leftover leftover leftover vs leftover leftover leftover JSON)",
            fetch1="https://www.w3.org/TR/xml/",
            fetch1_ok="XML leftover leftover leftover leftover leftover leftover namespaces are not JSON.",
            fetch2="https://www.rfc-editor.org/rfc/rfc8259.html",
            fetch2_ok="Exclusive application/xml 415s leftover leftover leftover JSON.",
        ),
        plant(
            slug="json-lll-vs-xml",
            domain="json-lll-vs-xml-lll",
            success=False,
            name="jsxmll",
            stack="OpenAPI 3.1 + Java + TS",
            field="content",
            old="XML leftover leftover leftover leftover leftover leftover namespaced",
            new="JSON leftover leftover leftover leftover leftover leftover only",
            fail_err="415: leftover leftover leftover XML after JSON-only",
            plan="JSON-only 415s leftover leftover leftover XML. Freeze namespaces, spec JSON.",
            residual="handoff: keep XML leftover leftover leftover leftover leftover leftover or force JSON",
            vs="r3698 json-vs-xml (JSON leftover leftover leftover vs XML leftover leftover leftover leftover leftover leftover)",
            fetch1="https://www.rfc-editor.org/rfc/rfc8259.html",
            fetch1_ok="JSON leftover leftover leftover leftover leftover leftover is not XML namespaced.",
            fetch2="https://www.w3.org/TR/xml/",
            fetch2_ok="Exclusive application/json 415s leftover leftover leftover XML.",
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
    batch = staging / f"batch-r{round_n:02d}.jsonl"
    notes = staging / f"NOTES-r{round_n:02d}.md"
    batch.write_text(json.dumps(e1, ensure_ascii=False) + "\n" + json.dumps(e2, ensure_ascii=False) + "\n")
    notes.write_text(notes_text(round_n, [e1, e2], [t1, t2], idx))
    print(json.dumps({"round": round_n, "idx": idx, "ids": [e1["id"], e2["id"]], "catalog": "r3714"}))


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
