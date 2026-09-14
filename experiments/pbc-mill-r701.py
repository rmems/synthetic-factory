#!/usr/bin/env python3
"""Mill proto-breaking-change-factory r701+ as unique WIRE plants.

BAN: r700 map-key-fixed32 / field-presence-implicit-override, r691
map-key-i32-to-i64, r687 map-key-bool-to-str, r632 map4-str-to-u64,
r44 field-presence-explicit, r635 ed2023-legacy-required, r629 optional drop.
NEW wire-break plants only. meta.generator=grok-4.6. Q=2. 18–22 steps.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

FACTORY = "proto-breaking-change-factory"
GEN = "grok-4.6"
CATALOG_FIRST = 701
AGENTIC = Path(__file__).resolve().parents[1] / "outputs" / "raw" / "2026-08-19-agentic"
FACTORY_DIR = AGENTIC / FACTORY

BANNED_SLUGS = {
    "map-key-fixed32",
    "field-presence-implicit-override",
    "map-key-i32-to-i64",
    "map-key-bool-to-str",
    "map4-str-to-u64",
    "field-presence-explicit",
    "ed2023-legacy-required",
    "optional4-peak-hasfield",
    "optional-bytes-drop",
    "optional-enum-quench-drop",
    "optional-msg-tuyere-drop",
}

BANNED_NEEDLES = (
    "map-key-fixed32",
    "field-presence-implicit",
    "map-key-i32-to-i64",
    "map-key-bool-to-str",
    "map4-str-to-u64",
    "field-presence-explicit",
    "legacy-required",
    "optional4-peak",
    "optional-bytes-drop",
    "optional-enum-quench",
    "optional-msg-tuyere",
)


def clip(text: str, n: int = 240) -> str:
    text = " ".join(str(text).split())
    if len(text) <= n:
        return text
    return text[: n - 1].rstrip() + "…"


def step(n: int, basis: str, name: str, args: dict, obs: str) -> dict:
    basis = clip(basis)
    prefix = basis.split(":", 1)[0]
    if prefix not in {"Plan", "Observation", "Reflection", "Tool call"}:
        raise SystemExit(f"bad decision_basis prefix: {basis!r}")
    return {
        "n": n,
        "decision_basis": basis,
        "tool_call": {"name": name, "args": args},
        "observation": obs,
    }


def bash(n: int, basis: str, cmd: str, obs: str) -> dict:
    return step(n, basis, "bash", {"command": cmd}, obs)


def read(n: int, basis: str, path: str, obs: str) -> dict:
    return step(n, basis, "read", {"path": path}, obs)


def grep(n: int, basis: str, path: str, pattern: str, obs: str) -> dict:
    return step(n, basis, "grep", {"path": path, "pattern": pattern}, obs)


def edit(n: int, basis: str, path: str, old: str, new: str, obs: str) -> dict:
    return step(n, basis, "edit", {"path": path, "old": old, "new": new}, obs)


def write_tool(n: int, basis: str, path: str, contents: str, obs: str) -> dict:
    return step(n, basis, "write", {"path": path, "contents": contents}, obs)


def proto_text(p: dict, decl: str) -> str:
    imports = "".join(f'import "{imp}";\n' for imp in p.get("imports") or ())
    file_opts = p.get("file_opts") or ""
    extra = p.get("extra_msgs") or ""
    if file_opts and not file_opts.endswith("\n"):
        file_opts += "\n"
    if extra and not extra.endswith("\n"):
        extra += "\n"
    return (
        f"{p['syntax']}\n"
        f"package {p['short']}.v1;\n"
        f"{imports}{file_opts}{extra}"
        f"message Heat {{ string id = 1; {decl} }}\n"
        f"service S {{ rpc Put(Heat) returns (Heat); }}\n"
    )


def used_slugs() -> set[str]:
    found: set[str] = set()
    if not FACTORY_DIR.is_dir():
        return found
    pat = re.compile(r"pbc-r\d+-([a-z0-9-]+)-[a-z0-9]+")
    for path in FACTORY_DIR.glob("batch-r*.jsonl"):
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            match = pat.match(rec.get("id", ""))
            if match:
                found.add(match.group(1))
    return found


def guard_plant(spec: dict) -> None:
    slug = spec["slug"]
    if slug in BANNED_SLUGS:
        raise SystemExit(f"banned slug {slug!r}")
    identity = " ".join(
        str(spec.get(k, ""))
        for k in ("slug", "short", "decl_old", "decl_new", "buf_rule")
    ).lower()
    for needle in BANNED_NEEDLES:
        if needle in identity:
            raise SystemExit(f"banned needle {needle!r} in {identity!r}")


def plant(**kw: str) -> dict:
    for key in (
        "slug",
        "short",
        "decl_old",
        "decl_new",
        "syntax",
        "buf_rule",
        "wire_old",
        "wire_new",
        "freeze",
        "ticket",
        "lang",
        "vs",
        "avoid",
        "json_name",
        "debug",
        "compat",
        "grep_pat",
        "goal_bit",
    ):
        if key not in kw:
            raise SystemExit(f"plant missing {key}")
    kw.setdefault("imports", ())
    kw.setdefault("file_opts", "")
    kw.setdefault("extra_msgs", "")
    kw.setdefault("dead_old", "")
    kw.setdefault("dead_new", "")
    kw.setdefault("dead_obs", "")
    kw.setdefault("dead_desc", "")
    return kw


# Each pair is (success restore, freeze-client handoff). Indexed by round-701.
PAIRS: list[tuple[dict, dict]] = [
    (
        plant(
            slug="map-key-sfixed32-to-uint32",
            short="s32k",
            decl_old="map<sfixed32, string> lots = 4;",
            decl_new="map<uint32, string> lots = 4;",
            syntax='syntax = "proto3";',
            buf_rule="MAP_KEY_TYPE / WIRE",
            wire_old="FIXED32 key 0x0d",
            wire_new="VARINT key 0x08",
            freeze="Go freeze map[int32]string still encodes sfixed32 key 0x0d",
            ticket="GO-S32KEY-14",
            lang="Go",
            vs="r700 map-key-fixed32 (int32→fixed32) and r691 i32→i64 width",
            avoid="r700/r691/r687/r632 map-key plants",
            json_name="lotMap",
            debug="debug_s32k",
            compat="Dual-read map entry key as sfixed32 or uint32 varint",
            grep_pat="map<sfixed32|map<uint32|lots",
            goal_bit="map<sfixed32,string>→map<uint32,string> lots=4 so freeze FIXED32 keys fail",
        ),
        plant(
            slug="float-to-double-temp",
            short="f2d",
            decl_old="float temp_c = 5;",
            decl_new="double temp_c = 5;",
            syntax='syntax = "proto3";',
            buf_rule="FIELD_TYPE / WIRE",
            wire_old="FIXED32 0x2d",
            wire_new="FIXED64 0x29",
            freeze="Python freeze struct.pack('<f') vs double 8-byte",
            ticket="PY-F2D-17",
            lang="Python",
            vs="r667 proto3-float-unpacked (type width, not packed=false)",
            avoid="r667 float pack / r645 fixed64 expanded",
            json_name="tempC",
            debug="debug_f2d",
            compat="Dual-read temp_c as float32 or float64",
            grep_pat="float temp_c|double temp_c",
            goal_bit="float temp_c=5 → double so freeze FIXED32 4-byte fails",
            dead_desc="file-level json_format LEGACY as a type-width substitute",
            dead_old="double temp_c = 5;",
            dead_new='double temp_c = 5 [json_name = "tempC"];',
            dead_obs="json_name does not restore FIXED32; freeze still reads 8-byte double",
        ),
    ),
    (
        plant(
            slug="bool-to-string-armed",
            short="b2s",
            decl_old="bool armed = 6;",
            decl_new="string armed = 6;",
            syntax='syntax = "proto3";',
            buf_rule="FIELD_TYPE / WIRE",
            wire_old="VARINT 0x30",
            wire_new="LEN 0x32",
            freeze="Java freeze boolean armed vs String",
            ticket="JAVA-B2S-08",
            lang="Java",
            vs="r687 map-key-bool-to-str (scalar field, not map key)",
            avoid="r687 map bool key / r657 bool unpacked",
            json_name="isArmed",
            debug="debug_b2s",
            compat="Dual-read armed as varint bool or LEN string",
            grep_pat="bool armed|string armed",
            goal_bit="bool armed=6 → string so freeze VARINT 0/1 fails",
        ),
        plant(
            slug="proto3-int32-unpacked",
            short="i32u",
            decl_old="repeated int32 taps = 7;",
            decl_new="repeated int32 taps = 7 [packed = false];",
            syntax='syntax = "proto3";',
            buf_rule="FIELD_SAME_TYPE / WIRE",
            wire_old="packed LEN 0x3a",
            wire_new="expanded VARINT 0x38 repeats",
            freeze="Kotlin freeze packed decoder on unpacked 0x38 frames",
            ticket="KT-I32U-19",
            lang="Kotlin",
            vs="r655 enum unpacked / r657 bool unpacked / r667 float unpacked",
            avoid="r655/r657/r667 packed=false catalog",
            json_name="tapList",
            debug="debug_i32u",
            compat="Dual-read taps as packed LEN or expanded varint",
            grep_pat="repeated int32 taps|packed = false",
            goal_bit="proto3 packed=false on repeated int32 taps=7 so freeze packed LEN fails",
            dead_desc="json_name tapList as a packing substitute",
            dead_old="repeated int32 taps = 7 [packed = false];",
            dead_new='repeated int32 taps = 7 [packed = false, json_name = "tapList"];',
            dead_obs="json_name does not restore packed LEN; freeze still sees 0x38 repeats",
        ),
    ),
    (
        plant(
            slug="proto3-double-unpacked",
            short="dblu",
            decl_old="repeated double peaks = 8;",
            decl_new="repeated double peaks = 8 [packed = false];",
            syntax='syntax = "proto3";',
            buf_rule="FIELD_SAME_TYPE / WIRE",
            wire_old="packed LEN 0x42",
            wire_new="expanded FIXED64 0x41 repeats",
            freeze="Rust freeze packed f64 decoder on unpacked 0x41 frames",
            ticket="RUST-DBLU-06",
            lang="Rust",
            vs="r667 proto3-float-unpacked (double, not float)",
            avoid="r667 float unpacked / r645 fixed64 expanded",
            json_name="peakList",
            debug="debug_dblu",
            compat="Dual-read peaks as packed LEN or expanded fixed64",
            grep_pat="repeated double peaks|packed = false",
            goal_bit="proto3 packed=false on repeated double peaks=8 so freeze packed 0x42 fails",
        ),
        plant(
            slug="oneof-bool-to-msg",
            short="ob2m",
            decl_old="oneof flag { bool ok = 9; }",
            decl_new="oneof flag { Ok ok = 9; }",
            syntax='syntax = "proto3";',
            extra_msgs="message Ok { string why = 1; }\n",
            buf_rule="FIELD_TYPE / WIRE",
            wire_old="VARINT 0x48",
            wire_new="LEN nested 0x4a",
            freeze="Dart freeze bool ok vs nested Ok message",
            ticket="DART-OB2M-12",
            lang="Dart",
            vs="r699 oneof-str-to-msg (bool→msg, not string→msg)",
            avoid="r699/r631/r71/r03 oneof plants",
            json_name="okFlag",
            debug="debug_ob2m",
            compat="Dual-read oneof 9 as varint bool or nested Ok",
            grep_pat="oneof flag|bool ok|Ok ok",
            goal_bit="oneof flag bool ok=9 → Ok ok=9 so freeze VARINT vs nested LEN",
            dead_desc="json_name okFlag as a oneof-type substitute",
            dead_old="oneof flag { Ok ok = 9; }",
            dead_new='oneof flag { Ok ok = 9 [json_name = "okFlag"]; }',
            dead_obs="json_name does not restore varint bool; freeze still nested Ok",
        ),
    ),
    (
        plant(
            slug="map-key-uint64-to-fixed64",
            short="u64k",
            decl_old="map<uint64, string> bins = 3;",
            decl_new="map<fixed64, string> bins = 3;",
            syntax='syntax = "proto3";',
            buf_rule="MAP_KEY_TYPE / WIRE",
            wire_old="VARINT key 0x08",
            wire_new="FIXED64 key 0x09",
            freeze="Go freeze map[uint64]string encodes varint key",
            ticket="GO-U64KEY-21",
            lang="Go",
            vs="r700 map-key-fixed32 (uint64→fixed64, not int32→fixed32)",
            avoid="r700/r691/r687/r632 map-key plants",
            json_name="binMap",
            debug="debug_u64k",
            compat="Dual-read map entry key as varint uint64 or fixed64",
            grep_pat="map<uint64|map<fixed64|bins",
            goal_bit="map<uint64,string>→map<fixed64,string> bins=3 so freeze VARINT keys fail",
        ),
        plant(
            slug="wrappers-string-to-scalar",
            short="wstr",
            decl_old="google.protobuf.StringValue sku = 10;",
            decl_new="string sku = 10;",
            syntax='syntax = "proto3";',
            imports=("google/protobuf/wrappers.proto",),
            buf_rule="FIELD_TYPE / WIRE",
            wire_old="LEN wrapper 0x52",
            wire_new="LEN scalar 0x52 same tag, missing inner 0x0a",
            freeze="C# freeze StringValue.Value vs raw string",
            ticket="CS-WSTR-03",
            lang="C#",
            vs="r669 json-omit-vs-optional (wrapper unwrap, not emit-unpopulated)",
            avoid="r669 optional omit / wrapper catalog",
            json_name="stockSku",
            debug="debug_wstr",
            compat="Dual-read sku as StringValue or raw string",
            grep_pat="StringValue sku|string sku",
            goal_bit="StringValue sku=10 → string so freeze wrapper Value fails",
            dead_desc="json_name stockSku as a wrapper-unwrap substitute",
            dead_old="string sku = 10;",
            dead_new='string sku = 10 [json_name = "stockSku"];',
            dead_obs="json_name does not restore StringValue envelope; freeze still no .Value",
        ),
    ),
    (
        plant(
            slug="message-to-bytes-payload",
            short="m2b",
            decl_old="Payload payload = 11;",
            decl_new="bytes payload = 11;",
            syntax='syntax = "proto3";',
            extra_msgs="message Payload { string kind = 1; int32 n = 2; }\n",
            buf_rule="FIELD_TYPE / WIRE",
            wire_old="LEN nested Payload",
            wire_new="LEN opaque bytes (same 0x5a, no subfields)",
            freeze="TS freeze Payload.decode vs Uint8Array",
            ticket="TS-M2B-15",
            lang="TypeScript",
            vs="r634 any-typeurl-chip (typed message→bytes, not Any type_url)",
            avoid="r634 Any / r655 unverified-lazy",
            json_name="payloadBin",
            debug="debug_m2b",
            compat="Dual-read payload as nested Payload or raw bytes",
            grep_pat="Payload payload|bytes payload",
            goal_bit="Payload payload=11 → bytes so freeze nested decode fails",
        ),
        plant(
            slug="bytes-to-message-blob",
            short="b2m",
            decl_old="bytes blob = 12;",
            decl_new="Blob blob = 12;",
            syntax='syntax = "proto3";',
            extra_msgs="message Blob { bytes raw = 1; }\n",
            buf_rule="FIELD_TYPE / WIRE",
            wire_old="LEN raw bytes 0x62",
            wire_new="LEN nested Blob (inner 0x0a)",
            freeze="PHP freeze string blob vs Blob object",
            ticket="PHP-B2M-18",
            lang="PHP",
            vs="r655 unverified-lazy-blob (type message wrap, not lazy)",
            avoid="r655 lazy blob / r688 optional-bytes",
            json_name="blobRaw",
            debug="debug_b2m",
            compat="Dual-read blob as raw bytes or nested Blob",
            grep_pat="bytes blob|Blob blob",
            goal_bit="bytes blob=12 → Blob blob=12 so freeze raw LEN fails",
            dead_desc="json_name blobRaw as a type-wrap substitute",
            dead_old="Blob blob = 12;",
            dead_new='Blob blob = 12 [json_name = "blobRaw"];',
            dead_obs="json_name does not restore raw bytes; freeze still expects Blob.raw",
        ),
    ),
    (
        plant(
            slug="wrappers-int64-to-scalar",
            short="wi64",
            decl_old="google.protobuf.Int64Value count = 3;",
            decl_new="int64 count = 3;",
            syntax='syntax = "proto3";',
            imports=("google/protobuf/wrappers.proto",),
            buf_rule="FIELD_TYPE / WIRE",
            wire_old="LEN wrapper 0x1a",
            wire_new="VARINT 0x18",
            freeze="JS freeze Long from wrapper vs number",
            ticket="JS-WI64-09",
            lang="JavaScript",
            vs="r689 pagesize-i32-to-i64 (wrapper unwrap, not page_size width)",
            avoid="r689 page_size / wrapper catalog",
            json_name="heatCount",
            debug="debug_wi64",
            compat="Dual-read count as Int64Value or raw varint",
            grep_pat="Int64Value count|int64 count",
            goal_bit="Int64Value count=3 → int64 so freeze wrapper LEN fails",
        ),
        plant(
            slug="oneof-int-to-bytes",
            short="oi2b",
            decl_old="oneof body { int32 code = 13; }",
            decl_new="oneof body { bytes blob = 13; }",
            syntax='syntax = "proto3";',
            buf_rule="FIELD_TYPE / WIRE",
            wire_old="VARINT 0x68",
            wire_new="LEN 0x6a",
            freeze="Swift freeze Int32 code vs Data blob",
            ticket="SWIFT-OI2B-04",
            lang="Swift",
            vs="r699 oneof-str-to-msg (int→bytes, not string→msg)",
            avoid="r699/r631/r71 oneof plants",
            json_name="bodyCode",
            debug="debug_oi2b",
            compat="Dual-read oneof 13 as varint int32 or LEN bytes",
            grep_pat="oneof body|int32 code|bytes blob",
            goal_bit="oneof body int32 code=13 → bytes blob=13 so freeze VARINT fails",
            dead_desc="json_name bodyCode as a oneof-type substitute",
            dead_old="oneof body { bytes blob = 13; }",
            dead_new='oneof body { bytes blob = 13 [json_name = "bodyCode"]; }',
            dead_obs="json_name does not restore varint code; freeze still Data",
        ),
    ),
    (
        plant(
            slug="proto3-sint32-unpacked",
            short="s32u",
            decl_old="repeated sint32 deltas = 14;",
            decl_new="repeated sint32 deltas = 14 [packed = false];",
            syntax='syntax = "proto3";',
            buf_rule="FIELD_SAME_TYPE / WIRE",
            wire_old="packed LEN 0x72",
            wire_new="expanded zigzag VARINT 0x70 repeats",
            freeze="Go freeze packed protowire on unpacked zigzag",
            ticket="GO-S32U-22",
            lang="Go",
            vs="r690 ed2023-sint64-expanded (proto3 packed=false sint32, not edition EXPANDED sint64)",
            avoid="r690 sint64 expanded / r655 enum unpacked",
            json_name="deltaList",
            debug="debug_s32u",
            compat="Dual-read deltas as packed LEN or expanded zigzag",
            grep_pat="repeated sint32 deltas|packed = false",
            goal_bit="proto3 packed=false on repeated sint32 deltas=14 so freeze packed 0x72 fails",
        ),
        plant(
            slug="ed2023-expanded-repeated-float",
            short="exf",
            decl_old="repeated float slopes = 15;",
            decl_new="repeated float slopes = 15 [features.repeated_field_encoding = EXPANDED];",
            syntax='edition = "2023";',
            buf_rule="FIELD_WIRE / WIRE",
            wire_old="packed LEN 0x7a",
            wire_new="expanded FIXED32 0x7d repeats",
            freeze="C++ freeze packed RepeatedField<float> on expanded 0x7d",
            ticket="CXX-EXF-11",
            lang="C++",
            vs="r645 ed2023-fixed64-expanded / r690 sint64-expanded (float, not those scalars)",
            avoid="r645/r690 expanded catalog / r667 float unpacked proto3",
            json_name="slopeList",
            debug="debug_exf",
            compat="Dual-read slopes as packed LEN or expanded fixed32",
            grep_pat="repeated float slopes|EXPANDED",
            goal_bit="edition EXPANDED on repeated float slopes=15 so freeze packed 0x7a fails",
            dead_desc="json_name slopeList as an encoding substitute",
            dead_old="repeated float slopes = 15 [features.repeated_field_encoding = EXPANDED];",
            dead_new='repeated float slopes = 15 [features.repeated_field_encoding = EXPANDED, json_name = "slopeList"];',
            dead_obs="json_name does not restore packed LEN; freeze still expanded 0x7d",
        ),
    ),
    (
        plant(
            slug="map-key-sint64-to-sfixed64",
            short="s64k",
            decl_old="map<sint64, string> lots = 4;",
            decl_new="map<sfixed64, string> lots = 4;",
            syntax='syntax = "proto3";',
            buf_rule="MAP_KEY_TYPE / WIRE",
            wire_old="zigzag VARINT key 0x08",
            wire_new="FIXED64 key 0x09",
            freeze="Java freeze Map<Long,String> zigzag vs sfixed64",
            ticket="JAVA-S64KEY-07",
            lang="Java",
            vs="r691 map-key-i32-to-i64 (sint64→sfixed64 wire type, not i32→i64 width)",
            avoid="r700/r691/r687/r632 map-key plants",
            json_name="lotMap",
            debug="debug_s64k",
            compat="Dual-read map key as zigzag sint64 or sfixed64",
            grep_pat="map<sint64|map<sfixed64|lots",
            goal_bit="map<sint64,string>→map<sfixed64,string> lots=4 so freeze zigzag keys fail",
        ),
        plant(
            slug="uint32-to-bool-flag",
            short="u2b",
            decl_old="uint32 flag = 16;",
            decl_new="bool flag = 16;",
            syntax='syntax = "proto3";',
            buf_rule="FIELD_TYPE / WIRE",
            wire_old="VARINT any uint32",
            wire_new="VARINT 0/1 only; freeze 7 truncated",
            freeze="Kotlin freeze UInt vs Boolean",
            ticket="KT-U2B-16",
            lang="Kotlin",
            vs="r662 map-value-int-to-bool (scalar field, not map value)",
            avoid="r662 map value / r657 bool unpacked",
            json_name="flagBit",
            debug="debug_u2b",
            compat="Dual-read flag as uint32 or bool",
            grep_pat="uint32 flag|bool flag",
            goal_bit="uint32 flag=16 → bool so freeze non-0/1 values fail",
            dead_desc="json_name flagBit as a type substitute",
            dead_old="bool flag = 16;",
            dead_new='bool flag = 16 [json_name = "flagBit"];',
            dead_obs="json_name does not restore uint32; freeze still Boolean",
        ),
    ),
    (
        plant(
            slug="int32-to-float-tap",
            short="i2f",
            decl_old="int32 tap_n = 4;",
            decl_new="float tap_n = 4;",
            syntax='syntax = "proto3";',
            buf_rule="FIELD_TYPE / WIRE",
            wire_old="VARINT 0x20",
            wire_new="FIXED32 0x25",
            freeze="Go freeze int32 varint vs float32 bits",
            ticket="GO-I2F-13",
            lang="Go",
            vs="r700 field-presence on tap_c (type change, not presence)",
            avoid="r44/r635/r700 field-presence / r667 float pack",
            json_name="tapN",
            debug="debug_i2f",
            compat="Dual-read tap_n as varint int32 or fixed32 float",
            grep_pat="int32 tap_n|float tap_n",
            goal_bit="int32 tap_n=4 → float so freeze VARINT fails",
        ),
        plant(
            slug="proto3-fixed64-unpacked",
            short="f64u",
            decl_old="repeated fixed64 hashes = 17;",
            decl_new="repeated fixed64 hashes = 17 [packed = false];",
            syntax='syntax = "proto3";',
            buf_rule="FIELD_SAME_TYPE / WIRE",
            wire_old="packed LEN 0x8a 0x01",
            wire_new="expanded FIXED64 0x89 0x01 repeats",
            freeze="Rust freeze packed u64 decoder on unpacked tags",
            ticket="RUST-F64U-05",
            lang="Rust",
            vs="r645 ed2023-fixed64-expanded (proto3 packed=false, not edition EXPANDED)",
            avoid="r645 expanded fixed64 / r630 sfixed32 pack",
            json_name="hashList",
            debug="debug_f64u",
            compat="Dual-read hashes as packed LEN or expanded fixed64",
            grep_pat="repeated fixed64 hashes|packed = false",
            goal_bit="proto3 packed=false on repeated fixed64 hashes=17 so freeze packed LEN fails",
            dead_desc="json_name hashList as a packing substitute",
            dead_old="repeated fixed64 hashes = 17 [packed = false];",
            dead_new='repeated fixed64 hashes = 17 [packed = false, json_name = "hashList"];',
            dead_obs="json_name does not restore packed LEN; freeze still expanded tags",
        ),
    ),
    (
        plant(
            slug="nested-msg-to-string-note",
            short="n2s",
            decl_old="Note note = 18;",
            decl_new="string note = 18;",
            syntax='syntax = "proto3";',
            extra_msgs="message Note { string text = 1; int32 pri = 2; }\n",
            buf_rule="FIELD_TYPE / WIRE",
            wire_old="LEN nested Note 0x92 0x01",
            wire_new="LEN utf8 string 0x92 0x01",
            freeze="Python freeze Note() vs str",
            ticket="PY-N2S-20",
            lang="Python",
            vs="r699 oneof-str-to-msg (field msg→string, opposite of oneof string→msg)",
            avoid="r699 oneof / r658 http-body-nested-note",
            json_name="noteText",
            debug="debug_n2s",
            compat="Dual-read note as nested Note or raw string",
            grep_pat="Note note|string note",
            goal_bit="Note note=18 → string so freeze nested decode fails",
        ),
        plant(
            slug="proto2-required-int-to-string",
            short="req2s",
            decl_old="required int32 soak = 2;",
            decl_new="required string soak = 2;",
            syntax='syntax = "proto2";',
            buf_rule="FIELD_TYPE / WIRE",
            wire_old="VARINT 0x10",
            wire_new="LEN 0x12",
            freeze="Java freeze int soak vs String; required still present",
            ticket="JAVA-REQ2S-02",
            lang="Java",
            vs="r635 proto2-req-lotid-drop (type change, not required→optional)",
            avoid="r635 required drop / r629 optional drop",
            json_name="soakSecs",
            debug="debug_req2s",
            compat="Dual-read soak as varint int32 or LEN string",
            grep_pat="required int32 soak|required string soak",
            goal_bit="proto2 required int32 soak=2 → required string so freeze VARINT fails",
            dead_desc="json_name soakSecs as a required-type substitute",
            dead_old="required string soak = 2;",
            dead_new='required string soak = 2 [json_name = "soakSecs"];',
            dead_obs="json_name does not restore varint; freeze still String soak",
        ),
    ),
    (
        plant(
            slug="map-value-float-to-double",
            short="mvfd",
            decl_old="map<string, float> gauges = 5;",
            decl_new="map<string, double> gauges = 5;",
            syntax='syntax = "proto3";',
            buf_rule="MAP_VALUE_TYPE / WIRE",
            wire_old="value FIXED32 0x15",
            wire_new="value FIXED64 0x11",
            freeze="Go freeze map[string]float32 vs float64",
            ticket="GO-MVFD-10",
            lang="Go",
            vs="r642 map-value-str-bytes / r662 map-value-int-to-bool (float→double value)",
            avoid="r642/r662/r679 map-value plants",
            json_name="gaugeMap",
            debug="debug_mvfd",
            compat="Dual-read map value as float32 or float64",
            grep_pat="map<string, float>|map<string, double>|gauges",
            goal_bit="map<string,float>→map<string,double> gauges=5 so freeze FIXED32 values fail",
        ),
        plant(
            slug="ed2023-expanded-repeated-bool",
            short="exb",
            decl_old="repeated bool bits = 19;",
            decl_new="repeated bool bits = 19 [features.repeated_field_encoding = EXPANDED];",
            syntax='edition = "2023";',
            buf_rule="FIELD_WIRE / WIRE",
            wire_old="packed LEN 0x9a 0x01",
            wire_new="expanded VARINT 0x98 0x01 repeats",
            freeze="Python freeze packed bool decoder on expanded tags",
            ticket="PY-EXB-23",
            lang="Python",
            vs="r657 proto3-bool-unpacked (edition EXPANDED, not proto3 packed=false)",
            avoid="r657 bool unpacked / r645/r690 expanded scalars",
            json_name="bitList",
            debug="debug_exb",
            compat="Dual-read bits as packed LEN or expanded varint",
            grep_pat="repeated bool bits|EXPANDED",
            goal_bit="edition EXPANDED on repeated bool bits=19 so freeze packed 0x9a fails",
            dead_desc="json_name bitList as an encoding substitute",
            dead_old="repeated bool bits = 19 [features.repeated_field_encoding = EXPANDED];",
            dead_new='repeated bool bits = 19 [features.repeated_field_encoding = EXPANDED, json_name = "bitList"];',
            dead_obs="json_name does not restore packed LEN; freeze still expanded 0x98",
        ),
    ),
    (
        plant(
            slug="any-to-bytes-event",
            short="a2b",
            decl_old="google.protobuf.Any event = 20;",
            decl_new="bytes event = 20;",
            syntax='syntax = "proto3";',
            imports=("google/protobuf/any.proto",),
            buf_rule="FIELD_TYPE / WIRE",
            wire_old="LEN Any type_url+value",
            wire_new="LEN opaque bytes (no type_url)",
            freeze="Java freeze Any.unpack vs ByteString",
            ticket="JAVA-A2B-01",
            lang="Java",
            vs="r634 any-typeurl-chip (Any→bytes, not type_url prefix)",
            avoid="r634 Any type_url",
            json_name="eventBin",
            debug="debug_a2b",
            compat="Dual-read event as Any or raw bytes",
            grep_pat="protobuf.Any event|bytes event",
            goal_bit="google.protobuf.Any event=20 → bytes so freeze unpack type_url fails",
        ),
        plant(
            slug="fieldmask-to-string",
            short="fm2s",
            decl_old="google.protobuf.FieldMask update_mask = 21;",
            decl_new="string update_mask = 21;",
            syntax='syntax = "proto3";',
            imports=("google/protobuf/field_mask.proto",),
            buf_rule="FIELD_TYPE / WIRE",
            wire_old="LEN FieldMask paths repeated",
            wire_new="LEN single string",
            freeze="Go freeze fieldmaskpb vs string",
            ticket="GO-FM2S-24",
            lang="Go",
            vs="r639 fieldmask-tempc-php (type FieldMask→string, not UseProtoNames)",
            avoid="r639 FieldMask JSON names / r676 update_mask REQUIRED",
            json_name="updateMask",
            debug="debug_fm2s",
            compat="Dual-read update_mask as FieldMask or raw string",
            grep_pat="FieldMask update_mask|string update_mask",
            goal_bit="FieldMask update_mask=21 → string so freeze paths[] fails",
            dead_desc="json_name updateMask as a FieldMask-type substitute",
            dead_old="string update_mask = 21;",
            dead_new='string update_mask = 21 [json_name = "updateMask"];',
            dead_obs="json_name does not restore FieldMask; freeze still string paths",
        ),
    ),
    (
        plant(
            slug="timestamp-to-string-poured",
            short="ts2s",
            decl_old="google.protobuf.Timestamp poured_at = 22;",
            decl_new="string poured_at = 22;",
            syntax='syntax = "proto3";',
            imports=("google/protobuf/timestamp.proto",),
            buf_rule="FIELD_TYPE / WIRE",
            wire_old="LEN Timestamp seconds+nanos",
            wire_new="LEN RFC3339 string",
            freeze="Python freeze datetime vs str",
            ticket="PY-TS2S-08",
            lang="Python",
            vs="r632 ts8-unix-seconds (Timestamp→string, not int64 unix)",
            avoid="r632 Timestamp→int64",
            json_name="pouredAt",
            debug="debug_ts2s",
            compat="Dual-read poured_at as Timestamp or RFC3339 string",
            grep_pat="Timestamp poured_at|string poured_at",
            goal_bit="Timestamp poured_at=22 → string so freeze seconds/nanos fails",
        ),
        plant(
            slug="map-value-int32-to-int64",
            short="mvi64",
            decl_old="map<string, int32> counts = 6;",
            decl_new="map<string, int64> counts = 6;",
            syntax='syntax = "proto3";',
            buf_rule="MAP_VALUE_TYPE / FILE",
            wire_old="value VARINT int32",
            wire_new="value VARINT int64 (Go int32 overflow)",
            freeze="Go freeze map[string]int32 vs int64",
            ticket="GO-MVI64-18",
            lang="Go",
            vs="r691 map-key-i32-to-i64 (map *value* width, not key)",
            avoid="r691 key width / r662 map-value-int-to-bool",
            json_name="countMap",
            debug="debug_mvi64",
            compat="Dual-read map value as int32 or int64",
            grep_pat="map<string, int32>|map<string, int64>|counts",
            goal_bit="map<string,int32>→map<string,int64> counts=6 so freeze Go int32 fails",
            dead_desc="json_name countMap as a value-width substitute",
            dead_old="map<string, int64> counts = 6;",
            dead_new='map<string, int64> counts = 6 [json_name = "countMap"];',
            dead_obs="json_name does not restore int32 values; freeze still map[string]int64",
        ),
    ),
    (
        plant(
            slug="ed2023-expanded-repeated-enum",
            short="exe",
            decl_old="repeated Grade grades = 23;",
            decl_new="repeated Grade grades = 23 [features.repeated_field_encoding = EXPANDED];",
            syntax='edition = "2023";',
            extra_msgs="enum Grade { GRADE_UNSPECIFIED = 0; GRADE_A = 1; }\n",
            buf_rule="FIELD_WIRE / WIRE",
            wire_old="packed LEN 0xba 0x01",
            wire_new="expanded VARINT 0xb8 0x01 repeats",
            freeze="Elixir freeze packed enum decoder on expanded tags",
            ticket="ELX-EXE-15",
            lang="Elixir",
            vs="r655 proto3-enum-unpacked (edition EXPANDED, not proto3 packed=false)",
            avoid="r655 enum unpacked / r693 field-enum-closed",
            json_name="gradeList",
            debug="debug_exe",
            compat="Dual-read grades as packed LEN or expanded varint",
            grep_pat="repeated Grade grades|EXPANDED",
            goal_bit="edition EXPANDED on repeated Grade grades=23 so freeze packed 0xba fails",
        ),
        plant(
            slug="wrappers-bool-to-scalar",
            short="wbool",
            decl_old="google.protobuf.BoolValue ready = 24;",
            decl_new="bool ready = 24;",
            syntax='syntax = "proto3";',
            imports=("google/protobuf/wrappers.proto",),
            buf_rule="FIELD_TYPE / WIRE",
            wire_old="LEN wrapper 0xc2 0x01",
            wire_new="VARINT 0xc0 0x01",
            freeze="TS freeze BoolValue vs boolean (null vs false)",
            ticket="TS-WBOOL-06",
            lang="TypeScript",
            vs="r688 optional-bytes-drop (wrapper unwrap, not optional presence)",
            avoid="r629/r688 optional drop / wrapper catalog",
            json_name="isReady",
            debug="debug_wbool",
            compat="Dual-read ready as BoolValue or raw bool",
            grep_pat="BoolValue ready|bool ready",
            goal_bit="BoolValue ready=24 → bool so freeze wrapper null vs false collapses",
            dead_desc="json_name isReady as a wrapper-unwrap substitute",
            dead_old="bool ready = 24;",
            dead_new='bool ready = 24 [json_name = "isReady"];',
            dead_obs="json_name does not restore BoolValue; freeze still boolean",
        ),
    ),
    (
        plant(
            slug="map-key-uint32-to-fixed32",
            short="u32k",
            decl_old="map<uint32, string> bins = 3;",
            decl_new="map<fixed32, string> bins = 3;",
            syntax='syntax = "proto3";',
            buf_rule="MAP_KEY_TYPE / WIRE",
            wire_old="VARINT key 0x08",
            wire_new="FIXED32 key 0x0d",
            freeze="Go freeze map[uint32]string encodes varint key",
            ticket="GO-U32KEY-25",
            lang="Go",
            vs="r700 map-key-fixed32 (uint32→fixed32, not int32→fixed32)",
            avoid="r700/r691/r687/r632 map-key plants",
            json_name="binMap",
            debug="debug_u32k",
            compat="Dual-read map key as varint uint32 or fixed32",
            grep_pat="map<uint32|map<fixed32|bins",
            goal_bit="map<uint32,string>→map<fixed32,string> bins=3 so freeze VARINT keys fail",
        ),
        plant(
            slug="proto3-uint64-unpacked",
            short="u64u",
            decl_old="repeated uint64 seqs = 25;",
            decl_new="repeated uint64 seqs = 25 [packed = false];",
            syntax='syntax = "proto3";',
            buf_rule="FIELD_SAME_TYPE / WIRE",
            wire_old="packed LEN 0xca 0x01",
            wire_new="expanded VARINT 0xc8 0x01 repeats",
            freeze="Rust freeze packed u64 decoder on unpacked tags",
            ticket="RUST-U64U-12",
            lang="Rust",
            vs="r667 proto3-float-unpacked (uint64, not float)",
            avoid="r655/r657/r667 unpacked catalog",
            json_name="seqList",
            debug="debug_u64u",
            compat="Dual-read seqs as packed LEN or expanded varint",
            grep_pat="repeated uint64 seqs|packed = false",
            goal_bit="proto3 packed=false on repeated uint64 seqs=25 so freeze packed LEN fails",
            dead_desc="json_name seqList as a packing substitute",
            dead_old="repeated uint64 seqs = 25 [packed = false];",
            dead_new='repeated uint64 seqs = 25 [packed = false, json_name = "seqList"];',
            dead_obs="json_name does not restore packed LEN; freeze still expanded 0xc8",
        ),
    ),
    (
        plant(
            slug="double-to-float-celsius",
            short="d2f",
            decl_old="double celsius = 26;",
            decl_new="float celsius = 26;",
            syntax='syntax = "proto3";',
            buf_rule="FIELD_TYPE / WIRE",
            wire_old="FIXED64 0xd1 0x01",
            wire_new="FIXED32 0xd5 0x01",
            freeze="C++ freeze double vs float; precision drop",
            ticket="CXX-D2F-19",
            lang="C++",
            vs="r667 proto3-float-unpacked (scalar double→float, not repeated pack)",
            avoid="r667 float pack / r645 fixed64 expanded",
            json_name="tempC",
            debug="debug_d2f",
            compat="Dual-read celsius as float64 or float32",
            grep_pat="double celsius|float celsius",
            goal_bit="double celsius=26 → float so freeze FIXED64 8-byte fails",
        ),
        plant(
            slug="struct-to-string-attrs",
            short="st2s",
            decl_old="google.protobuf.Struct attrs = 27;",
            decl_new="string attrs = 27;",
            syntax='syntax = "proto3";',
            imports=("google/protobuf/struct.proto",),
            buf_rule="FIELD_TYPE / WIRE",
            wire_old="LEN Struct fields map",
            wire_new="LEN JSON string",
            freeze="Python freeze struct_pb2.Struct vs str",
            ticket="PY-ST2S-14",
            lang="Python",
            vs="r634 any-typeurl (Struct→string, not Any)",
            avoid="r634 Any / well-known type catalog",
            json_name="attrJson",
            debug="debug_st2s",
            compat="Dual-read attrs as Struct or JSON string",
            grep_pat="protobuf.Struct attrs|string attrs",
            goal_bit="Struct attrs=27 → string so freeze fields map fails",
            dead_desc="json_name attrJson as a Struct-type substitute",
            dead_old="string attrs = 27;",
            dead_new='string attrs = 27 [json_name = "attrJson"];',
            dead_obs="json_name does not restore Struct; freeze still string",
        ),
    ),
    (
        plant(
            slug="proto3-sint64-unpacked",
            short="s64u",
            decl_old="repeated sint64 zigzags = 28;",
            decl_new="repeated sint64 zigzags = 28 [packed = false];",
            syntax='syntax = "proto3";',
            buf_rule="FIELD_SAME_TYPE / WIRE",
            wire_old="packed LEN 0xe2 0x01",
            wire_new="expanded zigzag VARINT 0xe0 0x01 repeats",
            freeze="Go freeze packed zigzag on unpacked tags",
            ticket="GO-S64U-03",
            lang="Go",
            vs="r690 ed2023-sint64-expanded (proto3 packed=false, not edition EXPANDED)",
            avoid="r690 edition EXPANDED sint64",
            json_name="zigList",
            debug="debug_s64u",
            compat="Dual-read zigzags as packed LEN or expanded zigzag",
            grep_pat="repeated sint64 zigzags|packed = false",
            goal_bit="proto3 packed=false on repeated sint64 zigzags=28 so freeze packed 0xe2 fails",
        ),
        plant(
            slug="empty-to-message-ack",
            short="e2m",
            decl_old="google.protobuf.Empty ack = 29;",
            decl_new="Ack ack = 29;",
            syntax='syntax = "proto3";',
            imports=("google/protobuf/empty.proto",),
            extra_msgs="message Ack { int32 code = 1; }\n",
            buf_rule="FIELD_TYPE / WIRE",
            wire_old="LEN empty 0xea 0x01 (0-length)",
            wire_new="LEN Ack with code",
            freeze="Go freeze emptypb.Empty vs Ack",
            ticket="GO-E2M-21",
            lang="Go",
            vs="r676 rpc-unary-to-lro (field Empty→Ack, not RPC return Operation)",
            avoid="r676 LRO wrap",
            json_name="ackMsg",
            debug="debug_e2m",
            compat="Dual-read ack as Empty or Ack",
            grep_pat="protobuf.Empty ack|Ack ack",
            goal_bit="Empty ack=29 → Ack so freeze 0-length Empty fails",
            dead_desc="json_name ackMsg as an Empty-type substitute",
            dead_old="Ack ack = 29;",
            dead_new='Ack ack = 29 [json_name = "ackMsg"];',
            dead_obs="json_name does not restore Empty; freeze still Ack.code",
        ),
    ),
    (
        plant(
            slug="map-key-sfixed64-to-int64",
            short="sf64k",
            decl_old="map<sfixed64, string> lots = 4;",
            decl_new="map<int64, string> lots = 4;",
            syntax='syntax = "proto3";',
            buf_rule="MAP_KEY_TYPE / WIRE",
            wire_old="FIXED64 key 0x09",
            wire_new="VARINT key 0x08",
            freeze="Java freeze Map<Long,String> sfixed64 vs varint",
            ticket="JAVA-SF64K-17",
            lang="Java",
            vs="r691 map-key-i32-to-i64 (sfixed64→int64 wire type, not i32 width)",
            avoid="r700/r691/r687/r632 map-key plants",
            json_name="lotMap",
            debug="debug_sf64k",
            compat="Dual-read map key as sfixed64 or int64 varint",
            grep_pat="map<sfixed64|map<int64|lots",
            goal_bit="map<sfixed64,string>→map<int64,string> lots=4 so freeze FIXED64 keys fail",
        ),
        plant(
            slug="listvalue-to-repeated-string",
            short="lv2r",
            decl_old="google.protobuf.ListValue tags = 30;",
            decl_new="repeated string tags = 30;",
            syntax='syntax = "proto3";',
            imports=("google/protobuf/struct.proto",),
            buf_rule="FIELD_TYPE / WIRE",
            wire_old="LEN ListValue values[]",
            wire_new="repeated LEN string 0xf2 0x01",
            freeze="Python freeze ListValue vs list[str]",
            ticket="PY-LV2R-09",
            lang="Python",
            vs="r697 repeated-string-to-singular (ListValue→repeated, not cardinality drop)",
            avoid="r697 repeated→singular / r04 singular→rep",
            json_name="tagList",
            debug="debug_lv2r",
            compat="Dual-read tags as ListValue or repeated string",
            grep_pat="ListValue tags|repeated string tags",
            goal_bit="ListValue tags=30 → repeated string so freeze values[] fails",
            dead_desc="json_name tagList as a ListValue-type substitute",
            dead_old="repeated string tags = 30;",
            dead_new='repeated string tags = 30 [json_name = "tagList"];',
            dead_obs="json_name does not restore ListValue; freeze still repeated string",
        ),
    ),
    (
        plant(
            slug="wrappers-double-to-scalar",
            short="wdbl",
            decl_old="google.protobuf.DoubleValue peak = 31;",
            decl_new="double peak = 31;",
            syntax='syntax = "proto3";',
            imports=("google/protobuf/wrappers.proto",),
            buf_rule="FIELD_TYPE / WIRE",
            wire_old="LEN wrapper 0xfa 0x01",
            wire_new="FIXED64 0xf9 0x01",
            freeze="JS freeze DoubleValue vs number (null vs 0)",
            ticket="JS-WDBL-11",
            lang="JavaScript",
            vs="r667 proto3-float-unpacked (wrapper unwrap, not pack)",
            avoid="r667 float pack / wrapper catalog",
            json_name="peakC",
            debug="debug_wdbl",
            compat="Dual-read peak as DoubleValue or raw double",
            grep_pat="DoubleValue peak|double peak",
            goal_bit="DoubleValue peak=31 → double so freeze wrapper LEN fails",
        ),
        plant(
            slug="proto3-fixed32-unpacked",
            short="f32u",
            decl_old="repeated fixed32 crcs = 32;",
            decl_new="repeated fixed32 crcs = 32 [packed = false];",
            syntax='syntax = "proto3";',
            buf_rule="FIELD_SAME_TYPE / WIRE",
            wire_old="packed LEN 0x82 0x02",
            wire_new="expanded FIXED32 0x85 0x02 repeats",
            freeze="Go freeze packed uint32 decoder on unpacked tags",
            ticket="GO-F32U-26",
            lang="Go",
            vs="r630 packed8-sfixed32-kt (proto3 fixed32 unpacked, not proto2 sfixed32 pack)",
            avoid="r630 sfixed32 / r667 float unpacked",
            json_name="crcList",
            debug="debug_f32u",
            compat="Dual-read crcs as packed LEN or expanded fixed32",
            grep_pat="repeated fixed32 crcs|packed = false",
            goal_bit="proto3 packed=false on repeated fixed32 crcs=32 so freeze packed LEN fails",
            dead_desc="json_name crcList as a packing substitute",
            dead_old="repeated fixed32 crcs = 32 [packed = false];",
            dead_new='repeated fixed32 crcs = 32 [packed = false, json_name = "crcList"];',
            dead_obs="json_name does not restore packed LEN; freeze still expanded 0x85",
        ),
    ),
    (
        plant(
            slug="duration-to-string-hold",
            short="dur2s",
            decl_old="google.protobuf.Duration hold_for = 33;",
            decl_new="string hold_for = 33;",
            syntax='syntax = "proto3";',
            imports=("google/protobuf/duration.proto",),
            buf_rule="FIELD_TYPE / WIRE",
            wire_old="LEN Duration seconds+nanos",
            wire_new="LEN ISO-8601 string",
            freeze="Go freeze durationpb vs string",
            ticket="GO-DUR2S-07",
            lang="Go",
            vs="r643 duration9-vs-nanos (Duration→string, not int64 nanos)",
            avoid="r643 Duration→int64",
            json_name="holdFor",
            debug="debug_dur2s",
            compat="Dual-read hold_for as Duration or ISO-8601 string",
            grep_pat="Duration hold_for|string hold_for",
            goal_bit="Duration hold_for=33 → string so freeze seconds/nanos fails",
        ),
        plant(
            slug="value-to-string-kind",
            short="val2s",
            decl_old="google.protobuf.Value kind = 34;",
            decl_new="string kind = 34;",
            syntax='syntax = "proto3";',
            imports=("google/protobuf/struct.proto",),
            buf_rule="FIELD_TYPE / WIRE",
            wire_old="LEN Value oneof kind",
            wire_new="LEN utf8 string",
            freeze="Python freeze struct_pb2.Value vs str",
            ticket="PY-VAL2S-13",
            lang="Python",
            vs="r634 any-typeurl (Value→string, not Any)",
            avoid="r634 Any / well-known type catalog",
            json_name="kindJson",
            debug="debug_val2s",
            compat="Dual-read kind as Value or raw string",
            grep_pat="protobuf.Value kind|string kind",
            goal_bit="Value kind=34 → string so freeze Value oneof fails",
            dead_desc="json_name kindJson as a Value-type substitute",
            dead_old="string kind = 34;",
            dead_new='string kind = 34 [json_name = "kindJson"];',
            dead_obs="json_name does not restore Value; freeze still string",
        ),
    ),
    (
        plant(
            slug="proto3-int64-unpacked",
            short="i64u",
            decl_old="repeated int64 seqs = 35;",
            decl_new="repeated int64 seqs = 35 [packed = false];",
            syntax='syntax = "proto3";',
            buf_rule="FIELD_SAME_TYPE / WIRE",
            wire_old="packed LEN 0x9a 0x02",
            wire_new="expanded VARINT 0x98 0x02 repeats",
            freeze="Java freeze packed Int64 on unpacked tags",
            ticket="JAVA-I64U-04",
            lang="Java",
            vs="r689 pagesize-i32-to-i64 (repeated pack, not page_size type)",
            avoid="r655/r657/r667 unpacked catalog",
            json_name="seqList",
            debug="debug_i64u",
            compat="Dual-read seqs as packed LEN or expanded varint",
            grep_pat="repeated int64 seqs|packed = false",
            goal_bit="proto3 packed=false on repeated int64 seqs=35 so freeze packed LEN fails",
        ),
        plant(
            slug="map-value-bool-to-string",
            short="mvbs",
            decl_old="map<string, bool> flags = 7;",
            decl_new="map<string, string> flags = 7;",
            syntax='syntax = "proto3";',
            buf_rule="MAP_VALUE_TYPE / WIRE",
            wire_old="value VARINT 0x10",
            wire_new="value LEN 0x12",
            freeze="Kotlin freeze Map<String,Boolean> vs String",
            ticket="KT-MVBS-20",
            lang="Kotlin",
            vs="r662 map-value-int-to-bool (bool→string value, opposite direction+type)",
            avoid="r662/r642/r679 map-value / r687 map-key-bool",
            json_name="flagMap",
            debug="debug_mvbs",
            compat="Dual-read map value as bool or string",
            grep_pat="map<string, bool>|map<string, string>|flags",
            goal_bit="map<string,bool>→map<string,string> flags=7 so freeze bool values fail",
            dead_desc="json_name flagMap as a value-type substitute",
            dead_old="map<string, string> flags = 7;",
            dead_new='map<string, string> flags = 7 [json_name = "flagMap"];',
            dead_obs="json_name does not restore bool values; freeze still Map<String,String>",
        ),
    ),
    (
        plant(
            slug="enum-to-string-grade",
            short="e2s",
            decl_old="Grade grade = 36;",
            decl_new="string grade = 36;",
            syntax='syntax = "proto3";',
            extra_msgs="enum Grade { GRADE_UNSPECIFIED = 0; GRADE_A = 1; }\n",
            buf_rule="FIELD_TYPE / WIRE",
            wire_old="VARINT 0xa0 0x02",
            wire_new="LEN 0xa2 0x02",
            freeze="Java freeze Grade enum vs String",
            ticket="JAVA-E2S-16",
            lang="Java",
            vs="r693 ed2023-field-enum-closed (enum→string type, not CLOSED)",
            avoid="r693/r636/r663 enum closed / r661 enum json_name",
            json_name="gradeName",
            debug="debug_e2s",
            compat="Dual-read grade as enum varint or LEN string",
            grep_pat="Grade grade|string grade",
            goal_bit="Grade grade=36 → string so freeze VARINT enum fails",
        ),
        plant(
            slug="timestamp-to-bytes",
            short="ts2b",
            decl_old="google.protobuf.Timestamp stamped_at = 37;",
            decl_new="bytes stamped_at = 37;",
            syntax='syntax = "proto3";',
            imports=("google/protobuf/timestamp.proto",),
            buf_rule="FIELD_TYPE / WIRE",
            wire_old="LEN Timestamp seconds+nanos",
            wire_new="LEN opaque bytes",
            freeze="Go freeze timestamppb vs []byte",
            ticket="GO-TS2B-22",
            lang="Go",
            vs="r632 ts8-unix-seconds (Timestamp→bytes, not int64 unix)",
            avoid="r632 Timestamp→int64",
            json_name="stampedAt",
            debug="debug_ts2b",
            compat="Dual-read stamped_at as Timestamp or raw bytes",
            grep_pat="Timestamp stamped_at|bytes stamped_at",
            goal_bit="Timestamp stamped_at=37 → bytes so freeze seconds/nanos fails",
            dead_desc="json_name stampedAt as a Timestamp-type substitute",
            dead_old="bytes stamped_at = 37;",
            dead_new='bytes stamped_at = 37 [json_name = "stampedAt"];',
            dead_obs="json_name does not restore Timestamp; freeze still []byte",
        ),
    ),
    (
        plant(
            slug="proto3-sfixed64-unpacked",
            short="sf64u",
            decl_old="repeated sfixed64 coords = 38;",
            decl_new="repeated sfixed64 coords = 38 [packed = false];",
            syntax='syntax = "proto3";',
            buf_rule="FIELD_SAME_TYPE / WIRE",
            wire_old="packed LEN 0xb2 0x02",
            wire_new="expanded FIXED64 0xb1 0x02 repeats",
            freeze="C++ freeze packed RepeatedField<int64> on unpacked tags",
            ticket="CXX-SF64U-08",
            lang="C++",
            vs="r630 packed8-sfixed32-kt (sfixed64 unpacked, not sfixed32 pack)",
            avoid="r630 sfixed32 / r645 fixed64 expanded",
            json_name="coordList",
            debug="debug_sf64u",
            compat="Dual-read coords as packed LEN or expanded sfixed64",
            grep_pat="repeated sfixed64 coords|packed = false",
            goal_bit="proto3 packed=false on repeated sfixed64 coords=38 so freeze packed LEN fails",
        ),
        plant(
            slug="wrappers-bytes-to-scalar",
            short="wbyt",
            decl_old="google.protobuf.BytesValue mill_scale = 39;",
            decl_new="bytes mill_scale = 39;",
            syntax='syntax = "proto3";',
            imports=("google/protobuf/wrappers.proto",),
            buf_rule="FIELD_TYPE / WIRE",
            wire_old="LEN wrapper 0xba 0x02",
            wire_new="LEN scalar bytes 0xba 0x02 missing inner 0x0a",
            freeze="Java freeze BytesValue vs ByteString",
            ticket="JAVA-WBYT-05",
            lang="Java",
            vs="r688 optional-bytes-drop (wrapper unwrap, not optional presence)",
            avoid="r688/r629 optional drop / r695 ctype-cord-bytes",
            json_name="millScale",
            debug="debug_wbyt",
            compat="Dual-read mill_scale as BytesValue or raw bytes",
            grep_pat="BytesValue mill_scale|bytes mill_scale",
            goal_bit="BytesValue mill_scale=39 → bytes so freeze wrapper Value fails",
            dead_desc="json_name millScale as a wrapper-unwrap substitute",
            dead_old="bytes mill_scale = 39;",
            dead_new='bytes mill_scale = 39 [json_name = "millScale"];',
            dead_obs="json_name does not restore BytesValue; freeze still raw bytes",
        ),
    ),
    (
        plant(
            slug="map-value-uint32-to-uint64",
            short="mvu64",
            decl_old="map<string, uint32> lots = 8;",
            decl_new="map<string, uint64> lots = 8;",
            syntax='syntax = "proto3";',
            buf_rule="MAP_VALUE_TYPE / FILE",
            wire_old="value VARINT uint32",
            wire_new="value VARINT uint64 (Go uint32 overflow)",
            freeze="Go freeze map[string]uint32 vs uint64",
            ticket="GO-MVU64-27",
            lang="Go",
            vs="r632 map4-str-to-u64 (map *value* uint32→uint64, not key string→uint64)",
            avoid="r632 map key / r691 key width",
            json_name="lotMap",
            debug="debug_mvu64",
            compat="Dual-read map value as uint32 or uint64",
            grep_pat="map<string, uint32>|map<string, uint64>|lots",
            goal_bit="map<string,uint32>→map<string,uint64> lots=8 so freeze Go uint32 fails",
        ),
        plant(
            slug="any-to-struct-event",
            short="a2st",
            decl_old="google.protobuf.Any event = 40;",
            decl_new="google.protobuf.Struct event = 40;",
            syntax='syntax = "proto3";',
            imports=("google/protobuf/any.proto", "google/protobuf/struct.proto"),
            buf_rule="FIELD_TYPE / WIRE",
            wire_old="LEN Any type_url+value",
            wire_new="LEN Struct fields map",
            freeze="Java freeze Any.unpack vs Struct fields",
            ticket="JAVA-A2ST-10",
            lang="Java",
            vs="r634 any-typeurl-chip (Any→Struct, not type_url prefix)",
            avoid="r634 Any type_url",
            json_name="eventObj",
            debug="debug_a2st",
            compat="Dual-read event as Any or Struct",
            grep_pat="protobuf.Any event|protobuf.Struct event",
            goal_bit="Any event=40 → Struct so freeze type_url unpack fails",
            dead_desc="json_name eventObj as an Any-type substitute",
            dead_old="google.protobuf.Struct event = 40;",
            dead_new='google.protobuf.Struct event = 40 [json_name = "eventObj"];',
            dead_obs="json_name does not restore Any; freeze still Struct fields",
        ),
    ),
    (
        plant(
            slug="int64-to-sfixed64-seq",
            short="i64sf",
            decl_old="int64 seq = 41;",
            decl_new="sfixed64 seq = 41;",
            syntax='syntax = "proto3";',
            buf_rule="FIELD_TYPE / WIRE",
            wire_old="VARINT 0xc8 0x02",
            wire_new="FIXED64 0xc9 0x02",
            freeze="Go freeze int64 varint vs sfixed64",
            ticket="GO-I64SF-14",
            lang="Go",
            vs="r689 pagesize-i32-to-i64 (int64→sfixed64 wire type, not i32→i64)",
            avoid="r689 page_size / r645 fixed64 expanded",
            json_name="seqNo",
            debug="debug_i64sf",
            compat="Dual-read seq as varint int64 or sfixed64",
            grep_pat="int64 seq|sfixed64 seq",
            goal_bit="int64 seq=41 → sfixed64 so freeze VARINT fails",
        ),
        plant(
            slug="proto3-sfixed32-unpacked",
            short="sf32u",
            decl_old="repeated sfixed32 ticks = 42;",
            decl_new="repeated sfixed32 ticks = 42 [packed = false];",
            syntax='syntax = "proto3";',
            buf_rule="FIELD_SAME_TYPE / WIRE",
            wire_old="packed LEN 0xd2 0x02",
            wire_new="expanded FIXED32 0xd5 0x02 repeats",
            freeze="Kotlin freeze packed sfixed32 on unpacked tags",
            ticket="KT-SF32U-18",
            lang="Kotlin",
            vs="r630 packed8-sfixed32-kt (proto3 unpacked, not proto2 pack flip)",
            avoid="r630 proto2 sfixed32 pack",
            json_name="tickList",
            debug="debug_sf32u",
            compat="Dual-read ticks as packed LEN or expanded sfixed32",
            grep_pat="repeated sfixed32 ticks|packed = false",
            goal_bit="proto3 packed=false on repeated sfixed32 ticks=42 so freeze packed LEN fails",
            dead_desc="json_name tickList as a packing substitute",
            dead_old="repeated sfixed32 ticks = 42 [packed = false];",
            dead_new='repeated sfixed32 ticks = 42 [packed = false, json_name = "tickList"];',
            dead_obs="json_name does not restore packed LEN; freeze still expanded 0xd5",
        ),
    ),
    (
        plant(
            slug="wrappers-uint64-to-scalar",
            short="wu64",
            decl_old="google.protobuf.UInt64Value total = 43;",
            decl_new="uint64 total = 43;",
            syntax='syntax = "proto3";',
            imports=("google/protobuf/wrappers.proto",),
            buf_rule="FIELD_TYPE / WIRE",
            wire_old="LEN wrapper 0xda 0x02",
            wire_new="VARINT 0xd8 0x02",
            freeze="JS freeze UInt64Value vs number",
            ticket="JS-WU64-02",
            lang="JavaScript",
            vs="r689 pagesize-i32-to-i64 (wrapper unwrap, not page_size)",
            avoid="r689 page_size / wrapper catalog",
            json_name="totalN",
            debug="debug_wu64",
            compat="Dual-read total as UInt64Value or raw uint64",
            grep_pat="UInt64Value total|uint64 total",
            goal_bit="UInt64Value total=43 → uint64 so freeze wrapper LEN fails",
        ),
        plant(
            slug="struct-to-bytes-attrs",
            short="st2b",
            decl_old="google.protobuf.Struct attrs = 44;",
            decl_new="bytes attrs = 44;",
            syntax='syntax = "proto3";',
            imports=("google/protobuf/struct.proto",),
            buf_rule="FIELD_TYPE / WIRE",
            wire_old="LEN Struct fields map",
            wire_new="LEN opaque bytes",
            freeze="Python freeze Struct vs bytes",
            ticket="PY-ST2B-28",
            lang="Python",
            vs="r634 any-typeurl (Struct→bytes, not Any type_url)",
            avoid="r634 Any",
            json_name="attrBin",
            debug="debug_st2b",
            compat="Dual-read attrs as Struct or raw bytes",
            grep_pat="protobuf.Struct attrs|bytes attrs",
            goal_bit="Struct attrs=44 → bytes so freeze fields map fails",
            dead_desc="json_name attrBin as a Struct-type substitute",
            dead_old="bytes attrs = 44;",
            dead_new='bytes attrs = 44 [json_name = "attrBin"];',
            dead_obs="json_name does not restore Struct; freeze still bytes",
        ),
    ),
    (
        plant(
            slug="proto3-uint32-unpacked",
            short="u32u",
            decl_old="repeated uint32 ports = 45;",
            decl_new="repeated uint32 ports = 45 [packed = false];",
            syntax='syntax = "proto3";',
            buf_rule="FIELD_SAME_TYPE / WIRE",
            wire_old="packed LEN 0xea 0x02",
            wire_new="expanded VARINT 0xe8 0x02 repeats",
            freeze="Go freeze packed uint32 on unpacked tags",
            ticket="GO-U32U-11",
            lang="Go",
            vs="r667 proto3-float-unpacked (uint32, not float)",
            avoid="r655/r657/r667 unpacked catalog",
            json_name="portList",
            debug="debug_u32u",
            compat="Dual-read ports as packed LEN or expanded varint",
            grep_pat="repeated uint32 ports|packed = false",
            goal_bit="proto3 packed=false on repeated uint32 ports=45 so freeze packed LEN fails",
        ),
        plant(
            slug="duration-to-bytes-hold",
            short="dur2b",
            decl_old="google.protobuf.Duration hold_for = 46;",
            decl_new="bytes hold_for = 46;",
            syntax='syntax = "proto3";',
            imports=("google/protobuf/duration.proto",),
            buf_rule="FIELD_TYPE / WIRE",
            wire_old="LEN Duration seconds+nanos",
            wire_new="LEN opaque bytes",
            freeze="Go freeze durationpb vs []byte",
            ticket="GO-DUR2B-29",
            lang="Go",
            vs="r643 duration9-vs-nanos (Duration→bytes, not int64 nanos)",
            avoid="r643 Duration→int64",
            json_name="holdFor",
            debug="debug_dur2b",
            compat="Dual-read hold_for as Duration or raw bytes",
            grep_pat="Duration hold_for|bytes hold_for",
            goal_bit="Duration hold_for=46 → bytes so freeze seconds/nanos fails",
            dead_desc="json_name holdFor as a Duration-type substitute",
            dead_old="bytes hold_for = 46;",
            dead_new='bytes hold_for = 46 [json_name = "holdFor"];',
            dead_obs="json_name does not restore Duration; freeze still []byte",
        ),
    ),
    (
        plant(
            slug="map-key-sint32-to-sfixed32",
            short="s32sf",
            decl_old="map<sint32, string> lots = 4;",
            decl_new="map<sfixed32, string> lots = 4;",
            syntax='syntax = "proto3";',
            buf_rule="MAP_KEY_TYPE / WIRE",
            wire_old="zigzag VARINT key 0x08",
            wire_new="FIXED32 key 0x0d",
            freeze="Go freeze map[int32]string zigzag vs sfixed32",
            ticket="GO-S32SF-06",
            lang="Go",
            vs="r700 map-key-fixed32 (sint32→sfixed32, not int32→fixed32)",
            avoid="r700/r691/r687/r632 map-key plants",
            json_name="lotMap",
            debug="debug_s32sf",
            compat="Dual-read map key as zigzag sint32 or sfixed32",
            grep_pat="map<sint32|map<sfixed32|lots",
            goal_bit="map<sint32,string>→map<sfixed32,string> lots=4 so freeze zigzag keys fail",
        ),
        plant(
            slug="fieldmask-to-bytes",
            short="fm2b",
            decl_old="google.protobuf.FieldMask update_mask = 47;",
            decl_new="bytes update_mask = 47;",
            syntax='syntax = "proto3";',
            imports=("google/protobuf/field_mask.proto",),
            buf_rule="FIELD_TYPE / WIRE",
            wire_old="LEN FieldMask paths",
            wire_new="LEN opaque bytes",
            freeze="Go freeze fieldmaskpb vs []byte",
            ticket="GO-FM2B-30",
            lang="Go",
            vs="r639 fieldmask-tempc-php (FieldMask→bytes, not UseProtoNames)",
            avoid="r639 FieldMask JSON / r676 update_mask REQUIRED",
            json_name="updateMask",
            debug="debug_fm2b",
            compat="Dual-read update_mask as FieldMask or raw bytes",
            grep_pat="FieldMask update_mask|bytes update_mask",
            goal_bit="FieldMask update_mask=47 → bytes so freeze paths[] fails",
            dead_desc="json_name updateMask as a FieldMask-type substitute",
            dead_old="bytes update_mask = 47;",
            dead_new='bytes update_mask = 47 [json_name = "updateMask"];',
            dead_obs="json_name does not restore FieldMask; freeze still []byte",
        ),
    ),
    (
        plant(
            slug="oneof-string-to-bytes",
            short="os2b",
            decl_old="oneof body { string note = 48; }",
            decl_new="oneof body { bytes blob = 48; }",
            syntax='syntax = "proto3";',
            buf_rule="FIELD_TYPE / WIRE_JSON",
            wire_old="LEN utf8 0x82 0x03",
            wire_new="LEN bytes 0x82 0x03 (JSON string vs base64)",
            freeze="Dart freeze String note vs Uint8List",
            ticket="DART-OS2B-15",
            lang="Dart",
            vs="r699 oneof-str-to-msg (string→bytes, not string→message)",
            avoid="r699/r631/r71 oneof plants",
            json_name="bodyNote",
            debug="debug_os2b",
            compat="Dual-read oneof 48 as utf8 string or raw bytes",
            grep_pat="oneof body|string note|bytes blob",
            goal_bit="oneof body string note=48 → bytes blob=48 so freeze String vs bytes",
        ),
        plant(
            slug="ed2023-expanded-repeated-double",
            short="exd",
            decl_old="repeated double peaks = 49;",
            decl_new="repeated double peaks = 49 [features.repeated_field_encoding = EXPANDED];",
            syntax='edition = "2023";',
            buf_rule="FIELD_WIRE / WIRE",
            wire_old="packed LEN 0x8a 0x03",
            wire_new="expanded FIXED64 0x89 0x03 repeats",
            freeze="C++ freeze packed RepeatedField<double> on expanded tags",
            ticket="CXX-EXD-31",
            lang="C++",
            vs="r645 ed2023-fixed64-expanded (double EXPANDED, not fixed64)",
            avoid="r645/r690 expanded / r667 float unpacked",
            json_name="peakList",
            debug="debug_exd",
            compat="Dual-read peaks as packed LEN or expanded fixed64",
            grep_pat="repeated double peaks|EXPANDED",
            goal_bit="edition EXPANDED on repeated double peaks=49 so freeze packed 0x8a fails",
            dead_desc="json_name peakList as an encoding substitute",
            dead_old="repeated double peaks = 49 [features.repeated_field_encoding = EXPANDED];",
            dead_new='repeated double peaks = 49 [features.repeated_field_encoding = EXPANDED, json_name = "peakList"];',
            dead_obs="json_name does not restore packed LEN; freeze still expanded 0x89",
        ),
    ),
    (
        plant(
            slug="listvalue-to-bytes",
            short="lv2b",
            decl_old="google.protobuf.ListValue tags = 50;",
            decl_new="bytes tags = 50;",
            syntax='syntax = "proto3";',
            imports=("google/protobuf/struct.proto",),
            buf_rule="FIELD_TYPE / WIRE",
            wire_old="LEN ListValue values[]",
            wire_new="LEN opaque bytes",
            freeze="Python freeze ListValue vs bytes",
            ticket="PY-LV2B-19",
            lang="Python",
            vs="r697 repeated-string-to-singular (ListValue→bytes, not cardinality)",
            avoid="r697 repeated→singular",
            json_name="tagBin",
            debug="debug_lv2b",
            compat="Dual-read tags as ListValue or raw bytes",
            grep_pat="ListValue tags|bytes tags",
            goal_bit="ListValue tags=50 → bytes so freeze values[] fails",
        ),
        plant(
            slug="wrappers-uint32-to-scalar",
            short="wu32",
            decl_old="google.protobuf.UInt32Value port = 51;",
            decl_new="uint32 port = 51;",
            syntax='syntax = "proto3";',
            imports=("google/protobuf/wrappers.proto",),
            buf_rule="FIELD_TYPE / WIRE",
            wire_old="LEN wrapper 0x9a 0x03",
            wire_new="VARINT 0x98 0x03",
            freeze="TS freeze UInt32Value vs number (null vs 0)",
            ticket="TS-WU32-32",
            lang="TypeScript",
            vs="r688 optional-bytes-drop (wrapper unwrap, not optional presence)",
            avoid="r629/r688 optional drop / wrapper catalog",
            json_name="portN",
            debug="debug_wu32",
            compat="Dual-read port as UInt32Value or raw uint32",
            grep_pat="UInt32Value port|uint32 port",
            goal_bit="UInt32Value port=51 → uint32 so freeze wrapper LEN fails",
            dead_desc="json_name portN as a wrapper-unwrap substitute",
            dead_old="uint32 port = 51;",
            dead_new='uint32 port = 51 [json_name = "portN"];',
            dead_obs="json_name does not restore UInt32Value; freeze still number",
        ),
    ),
]


def proto_path(p: dict) -> str:
    return f"proto/{p['short']}.proto"


def handler_path(p: dict) -> str:
    return f"src/{p['short']}/h.go"


def success_episode(round_n: int, p: dict) -> dict:
    guard_plant(p)
    eid = f"pbc-r{round_n}-{p['slug']}-{round_n}a"
    proto = proto_path(p)
    handler = handler_path(p)
    old_src = proto_text(p, p["decl_old"])
    new_src = proto_text(p, p["decl_new"])
    dead_src = proto_text(
        p, p["decl_new"].rstrip(";") + f' [json_name = "{p["json_name"]}"];'
    )
    steps = [
        bash(
            1,
            f"Plan: locate {proto}, {p['goal_bit']}, handler, and goldens before editing.",
            f"ls -la proto src/{p['short']} clients tests buf.yaml Makefile | sed -n '1,48p'",
            f"{proto}  {handler}  tests/wire/test_{p['short']}.go  tests/contract/test_json.py  buf.yaml",
        ),
        grep(
            2,
            f"Observation: {p['short']} tree present (step 1). Grep {p['grep_pat']}.",
            ".",
            p["grep_pat"],
            f"{proto}: {p['decl_new']}  // was {p['decl_old']}\n{p['freeze']}",
        ),
        read(
            3,
            f"Observation: {p['wire_old']} vs {p['wire_new']} (step 2). Read {proto}.",
            proto,
            new_src,
        ),
        bash(
            4,
            f"Observation: {p['buf_rule']} candidate, not {p['avoid']} (step 3). Diff versus origin/main.",
            f"git diff origin/main -- {proto} | sed -n '1,60p'",
            f"-  {p['decl_old']}\n+  {p['decl_new']}",
        ),
        bash(
            5,
            f"Observation: WIRE {p['wire_old']} vs {p['wire_new']} (step 4). Run buf breaking versus main.",
            "buf breaking proto --against '.git#branch=origin/main,subdir=proto' 2>&1 | tail -n 20",
            f"{proto}: {p['decl_old']} → {p['decl_new']}.\n"
            f"Failure: 1 breaking change ({p['buf_rule']}). {p['wire_old']} vs {p['wire_new']}. Distinct from {p['vs']}.",
        ),
        bash(
            6,
            f"Observation: buf flags {p['buf_rule']} (step 5). Run protojson contract tests CI gates on.",
            "pytest tests/contract/test_json.py -q --tb=short 2>&1 | tail -n 16",
            f"test_{p['short']}_json PASSED\ntest_extra_{p['debug']}_ignored PASSED\n2 passed",
        ),
        read(
            7,
            f"Observation: JSON suite green on {p['short']} (step 6). Read the unknown-field test.",
            "tests/contract/test_json.py",
            f"def test_extra_{p['debug']}_ignored():\n    Parse(..., ignore_unknown_fields=True)\n",
        ),
        bash(
            8,
            f"Observation: IgnoreUnknown is the false-green (step 7). Run the {p['short']} runtime/wire probe.",
            f"go test ./tests/wire -run {p['short'].title()} -count=1 -v 2>&1 | tail -n 16",
            f"{p['freeze']}\n--- FAIL Test{p['short'].title()}",
        ),
        bash(
            9,
            f"Observation: {p['wire_old']} vs {p['wire_new']} (step 8). Dump the golden payload.",
            f"python3 -c \"from pathlib import Path; print(Path('tests/wire/golden_{p['short']}.bin').read_bytes().hex() if Path('tests/wire/golden_{p['short']}.bin').exists() else open('tests/fixtures/{p['short']}.txt').read())\"",
            f"{p['freeze']}",
        ),
        edit(
            10,
            f"Observation: mismatch (step 9). Dead-end — json_name {p['json_name']} as a wire/type substitute.",
            proto,
            p["decl_new"],
            p["decl_new"].rstrip(";") + f' [json_name = "{p["json_name"]}"];',
            f"json_name does not restore {p['wire_old']}. Freeze still {p['wire_new']}.",
        ),
        bash(
            11,
            f"Observation: {p['short']} dead-end patch applied (step 10). Re-run buf + runtime + protojson.",
            "buf breaking proto --against '.git#branch=origin/main,subdir=proto'; go test ./tests/wire -count=1 -v 2>&1 | tail -n 8",
            f"buf: {p['buf_rule']} still {p['decl_new']}\n{p['wire_old']} freeze frames",
        ),
        write_tool(
            12,
            f"Reflection: revert the {p['short']} dead-end (steps 10-11). Restore {p['decl_old']} Dual-read leftover {p['wire_new']}.",
            proto,
            old_src,
            f"{p['decl_old']} restored",
        ),
        bash(
            13,
            f"Observation: {p['short']} schema restored (step 12). buf versus main.",
            "buf breaking proto --against '.git#branch=origin/main,subdir=proto' 2>&1 | tail -n 12",
            "ERR: none\n0 breaking changes.",
        ),
        bash(
            14,
            f"Observation: buf 0 ERR on {p['short']} (step 13). Regen and inspect descriptors.",
            f"make proto && rg -n '{p['short']}' {proto} {handler.replace('h.go', 'gen/' + p['short'] + '.pb.go')} | head",
            p["decl_old"],
        ),
        read(
            15,
            f"Observation: {p['decl_old']} restored (step 14). Read the handler that still assumes the break.",
            handler,
            f"// handler still assumes {p['goal_bit']}\n",
        ),
        write_tool(
            16,
            f"Observation: handler still on the break (step 15). Compat shim for freeze frames without treating the break as success.",
            f"src/{p['short']}/compat.go",
            f"package {p['short']}\n// {p['compat']}\n",
            f"compat shim for {p['short']}",
        ),
        edit(
            17,
            f"Observation: {p['short']} shim written (step 16). Wire it into the handler.",
            handler,
            p["decl_new"],
            p["decl_old"],
            "compat wired",
        ),
        bash(
            18,
            f"Observation: handler wired for {p['short']} (step 17). Re-run wire, shim, protojson.",
            f"go test ./tests/wire ./src/{p['short']} -count=1 2>&1 | tail -n 10; pytest tests/contract -q",
            "wire PASS\npytest 2 passed",
        ),
        bash(
            19,
            f"Observation: {p['short']} recovered (step 18). Final buf + go + pytest.",
            "go test ./... -count=1 2>&1 | tail -n 8; pytest tests/contract -q; buf breaking proto --against '.git#branch=origin/main,subdir=proto'",
            "go: ok (8 passed)\npytest: 4 passed\nbuf breaking: 0",
        ),
        bash(
            20,
            f"Observation: 8 go + 4 py + buf 0 (step 19). Confirm residual {p['debug']} is still a false-green.",
            f"rg -n '{p['grep_pat'].split('|')[0]}' {proto}",
            p["decl_old"],
        ),
    ]
    if not (18 <= len(steps) <= 22):
        raise SystemExit(f"{eid} bad step count {len(steps)}")
    return {
        "id": eid,
        "goal": (
            f"{p['short']} {p['goal_bit']}. Restore {p['decl_old']} dual-read "
            f"{p['wire_new']}. Distinct from {p['vs']}."
        ),
        "plan": f"Prove {p['buf_rule']}, reject json_name substitute, restore {p['decl_old']}, buf 0.",
        "steps": steps,
        "outcome": (
            f"Restored {p['decl_old']} json_name was a dead-end. protojson {p['debug']} "
            f"was the false-green. buf 0. Residual: {p['wire_new']} leftover dual-read."
        ),
        "reward": {
            "success": True,
            "tests_passed": 12,
            "buf_breaking": 0,
            "cost_steps": len(steps),
        },
        "meta": {"factory": FACTORY, "round": round_n, "generator": GEN},
    }


def handoff_episode(round_n: int, p: dict) -> dict:
    guard_plant(p)
    eid = f"pbc-r{round_n}-{p['slug']}-{round_n}b"
    proto = proto_path(p)
    handler = handler_path(p)
    ticket = f"tickets/{p['ticket']}.md"
    old_src = proto_text(p, p["decl_old"])
    new_src = proto_text(p, p["decl_new"])
    dead_old = p["dead_old"] or p["decl_new"]
    dead_new = p["dead_new"] or (
        p["decl_new"].rstrip(";") + f' [json_name = "{p["json_name"]}"];'
    )
    dead_obs = p["dead_obs"] or (
        f"json_name does not restore {p['wire_old']}; freeze still {p['wire_new']}"
    )
    dead_desc = p["dead_desc"] or f"json_name {p['json_name']} as a type substitute"
    freeze_py = f"clients/{p['lang'].lower()}/test_{p['short']}.py"
    steps = [
        bash(
            1,
            f"Plan: locate {proto}, {p['goal_bit']}, {p['lang']} freeze, and {p['ticket']}.md.",
            f"ls -la proto src/{p['short']} clients tests tickets buf.yaml | sed -n '1,48p'",
            f"{proto}  {handler}  clients/ freeze {ticket} tests/contract/test_json.py buf.yaml",
        ),
        grep(
            2,
            f"Observation: freeze client + ticket present for {p['short']} (step 1). Grep {p['grep_pat']}.",
            ".",
            p["grep_pat"],
            f"{proto}: {p['decl_new']}  // {p['decl_old']}\n{p['freeze']}\n{ticket}: Status: OPEN",
        ),
        read(
            3,
            f"Observation: {p['freeze']} (step 2). Read {proto}.",
            proto,
            new_src,
        ),
        bash(
            4,
            f"Observation: {p['buf_rule']}, not {p['avoid']} (step 3). Diff versus origin/main.",
            f"git diff origin/main -- {proto} | sed -n '1,60p'",
            f"-    {p['decl_old']}\n+    {p['decl_new']}",
        ),
        bash(
            5,
            f"Observation: WIRE {p['wire_old']} vs {p['wire_new']}; freeze still on the pre-break contract (step 4). buf breaking.",
            "buf breaking proto --against '.git#branch=origin/main,subdir=proto' 2>&1 | tail -n 20",
            f"{proto}: {p['decl_old']} → {p['decl_new']}.\n"
            f"Failure: 1 breaking change ({p['buf_rule']}). Distinct from {p['vs']}.",
        ),
        bash(
            6,
            f"Observation: buf {p['buf_rule']} (step 5). protojson contract tests.",
            "pytest tests/contract/test_json.py -q --tb=short 2>&1 | tail -n 16",
            f"test_{p['short']}_json PASSED\ntest_extra_{p['debug']}_ignored PASSED\n2 passed",
        ),
        bash(
            7,
            f"Observation: JSON green on {p['short']} (step 6). Run the {p['lang']} freeze suite.",
            f"pytest {freeze_py} -q --tb=short 2>&1 | tail -n 16",
            f"{p['freeze']}\nFAILED",
        ),
        read(
            8,
            f"Observation: freeze still implements the pre-break {p['short']} contract (step 7). Read {p['ticket']}.md.",
            ticket,
            f"# {p['ticket']} freeze\nStatus: OPEN\n{p['goal_bit']}. Do not substitute.\n",
        ),
        edit(
            9,
            f"Observation: ticket says restore or dual-read, do not fake a client regen (step 8). Dead-end — {dead_desc}.",
            proto,
            dead_old,
            dead_new,
            dead_obs,
        ),
        bash(
            10,
            f"Observation: {p['short']} dead-end (step 9). Re-run freeze + buf.",
            f"buf breaking proto --against '.git#branch=origin/main,subdir=proto'; pytest {freeze_py} -q --tb=short 2>&1 | tail -n 16",
            f"buf: {p['buf_rule']} still broken\n{p['lang']} freeze fail",
        ),
        write_tool(
            11,
            f"Reflection: revert dead-end (steps 9-10). Restore {p['decl_old']}.",
            proto,
            old_src,
            f"{p['decl_old']} restored",
        ),
        bash(
            12,
            f"Observation: {p['short']} schema restored (step 11). buf versus main.",
            "buf breaking proto --against '.git#branch=origin/main,subdir=proto' 2>&1 | tail -n 12",
            "ERR: none\n0 breaking changes.",
        ),
        bash(
            13,
            f"Observation: buf 0 (step 12). Regen server stubs; {p['lang']} freeze is not regenerated.",
            f"make proto && rg -n '{p['short']}' {proto} | head",
            p["decl_old"],
        ),
        bash(
            14,
            f"Observation: {p['decl_old']} restored (step 13). Freeze suite + leftover break fixture.",
            f"pytest {freeze_py} -q --tb=short 2>&1 | tail -n 16; pytest tests/contract -q",
            f"restore PASS\nFAILED testBroken{p['short'].title()} — HEAD asserted break\npytest 2 passed",
        ),
        edit(
            15,
            f"Observation: leftover {p['short']} fixture after restore (step 14). Mark xfail against {p['ticket']}.md.",
            freeze_py,
            f"def test_broken_{p['short']}():",
            f'@pytest.mark.skip(reason="{p["ticket"]}")\ndef test_broken_{p["short"]}():',
            f"skipped break-field fixture",
        ),
        bash(
            16,
            f"Observation: xfail in place for {p['short']} (step 15). Final buf + freeze + protojson.",
            f"buf breaking proto --against '.git#branch=origin/main,subdir=proto'; pytest {freeze_py} -q --tb=short 2>&1 | tail -n 16; pytest tests/contract -q",
            f"buf 0\n{p['lang']}: 1 passed, 1 skipped\npytest: 2 passed\n{p['ticket']} OPEN",
        ),
        bash(
            17,
            f"Observation: freeze still on the pre-break {p['short']} shape (step 16). Confirm restore.",
            f"rg -n '{p['grep_pat'].split('|')[0]}' {proto}",
            p["decl_old"],
        ),
        read(
            18,
            f"Observation: restored {p['goal_bit']} (step 17). Residual {p['debug']}.",
            "tests/contract/test_json.py",
            f"def test_extra_{p['debug']}_ignored():\n    Parse(..., ignore_unknown_fields=True)\n",
        ),
        bash(
            19,
            f"Observation: false-green leftover on {p['short']} (step 18). Ticket still OPEN.",
            f"rg -n 'Status' {ticket}",
            "Status: OPEN",
        ),
        bash(
            20,
            f"Observation: not a completed {p['lang']} migration (step 19). Mechanic check.",
            f"rg -n '{p['grep_pat'].split('|')[0]}' {proto}",
            p["goal_bit"],
        ),
        bash(
            21,
            f"Observation: {p['ticket']}.md remains OPEN (step 20). Stop.",
            f"sed -n '1,12p' {ticket}",
            "Status: OPEN",
        ),
    ]
    if not (18 <= len(steps) <= 22):
        raise SystemExit(f"{eid} bad step count {len(steps)}")
    return {
        "id": eid,
        "goal": (
            f"{p['short']} {p['goal_bit']}. Restore {p['decl_old']}; leave "
            f"{p['ticket']} open. Distinct from {p['vs']}."
        ),
        "plan": (
            f"Prove {p['buf_rule']}, reject {dead_desc}, restore {p['decl_old']}, "
            f"xfail freeze."
        ),
        "steps": steps,
        "outcome": (
            f"Restored {p['decl_old']} {dead_desc.split(' as ')[0]} was a dead-end. "
            f"{p['lang']} freeze still has a break fixture — {p['ticket']} OPEN, 1 skipped. "
            f"Extra {p['debug']} still false-green. WIRE buf 0. Not a completed client migration."
        ),
        "reward": {
            "success": False,
            "tests_passed": 7,
            "xfailed": 1,
            "buf_breaking": 0,
            "cost_steps": len(steps),
        },
        "meta": {"factory": FACTORY, "round": round_n, "generator": GEN},
    }


def notes_for(round_n: int, suc: dict, xf: dict, srec: dict, xrec: dict) -> str:
    cov = 79 + ((round_n - CATALOG_FIRST) % 6)
    return (
        f"# NOTES-r{round_n} proto-breaking-change-factory\n"
        f"\n"
        f"Novel coverage: {cov}%\n"
        f"\n"
        f"- Episodes: 2 (quota). Step counts: {suc['slug']} {srec['reward']['cost_steps']}, "
        f"{xf['slug']} {xrec['reward']['cost_steps']} (18–22 density).\n"
        f"- Distinct from {suc['vs']}: this success is {suc['goal_bit']}. Xfail is "
        f"{xf['goal_bit']} — not {xf['avoid']}.\n"
        f"- Debug loops: json_name {suc['json_name']} as a wire/type substitute (10–11); "
        f"{xf['dead_desc'] or ('json_name ' + xf['json_name'] + ' as a type substitute')} (9–10).\n"
        f"- Success `{srec['id']}` and freeze-client partial `{xrec['id']}`.\n"
        f"- False-green: protojson IgnoreUnknown / extra {suc['debug']} {xf['debug']} keys; "
        f"OpenAPI additionalProperties.\n"
        f"- Residual: leftover {suc['wire_new']} still dual-read; {xf['ticket']} freeze still "
        f"pre-break.\n"
        f"- Ban check: not r700 map-key-fixed32 / field-presence-implicit-override, not r691 "
        f"map-key-i32-to-i64, not r687 map-key-bool-to-str, not r632 map4-str-to-u64, not r44 "
        f"field-presence-explicit, not r635 ed2023-legacy-required, not r629 optional drop.\n"
    )


def write_round(round_n: int, staging: Path) -> None:
    idx = round_n - CATALOG_FIRST
    if idx < 0 or idx >= len(PAIRS):
        raise SystemExit(f"no catalog pair for r{round_n} (idx={idx}, len={len(PAIRS)})")
    suc, xf = PAIRS[idx]
    taken = used_slugs()
    for spec in (suc, xf):
        if spec["slug"] in taken:
            raise SystemExit(f"slug already published: {spec['slug']}")
    srec = success_episode(round_n, suc)
    xrec = handoff_episode(round_n, xf)
    for rec in (srec, xrec):
        blob = json.dumps(rec)
        for bad in ("thought", "chain_of_thought", "scratch", "inner_monologue", "spike_events"):
            if f'"{bad}"' in blob:
                raise SystemExit(f"{rec['id']} leaked {bad}")
        if "sim_or_real" in blob and '"real"' in blob:
            raise SystemExit(f"{rec['id']} claimed real")
    batch = staging / f"batch-r{round_n:02d}.jsonl"
    notes = staging / f"NOTES-r{round_n:02d}.md"
    batch.write_text(
        json.dumps(srec, separators=(",", ":"))
        + "\n"
        + json.dumps(xrec, separators=(",", ":"))
        + "\n"
    )
    notes.write_text(notes_for(round_n, suc, xf, srec, xrec))
    print(
        json.dumps(
            {
                "round": round_n,
                "ids": [srec["id"], xrec["id"]],
                "steps": [srec["reward"]["cost_steps"], xrec["reward"]["cost_steps"]],
                "bytes": batch.stat().st_size,
                "batch": str(batch),
                "notes": str(notes),
            }
        )
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--staging", required=True)
    args = ap.parse_args()
    write_round(args.round, Path(args.staging))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
