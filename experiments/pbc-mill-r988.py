#!/usr/bin/env python3
"""Mill proto-breaking-change-factory r988+ NEW unique WIRE plants.

BAN: map-key type swaps already used, field-presence implicit/explicit,
ed2023-legacy-required, optional drop, r987 enum-to-fixed64-mode /
bytes-to-fixed64-hash, r787-r987 leftover clones.
NEW wire-break plants only. meta.generator=grok-4.6. Q=2. 18-22 steps.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("pbc_mill_r787", HERE / "pbc-mill-r787.py")
_r787 = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_r787)

ty = _r787.ty
ENUM_MODE = _r787.ENUM_MODE
success_episode = _r787.success_episode
handoff_episode = _r787.handoff_episode
used_slugs = _r787.used_slugs
CATALOG_FIRST = 988

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
    "map-key-uint32-to-int32",
    "enum-to-fixed64-mode",
    "bytes-to-fixed64-hash",
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
    "enum-to-fixed64-mode",
    "bytes-to-fixed64-hash",
)

LANGC = {
    "Go": "GO",
    "Python": "PY",
    "Java": "JAVA",
    "Rust": "RUST",
    "Kotlin": "KT",
    "TypeScript": "TS",
    "C++": "CXX",
    "Swift": "SWIFT",
    "Dart": "DART",
    "C#": "CS",
}

# slug|short|told|tnew|field|num|wold|wnew|lang|vs|avoid
RAW = r"""
int32-to-uint64-tap|i32u64|int32|uint64|tap_n|901|VARINT int32|unsigned VARINT 64|Go|r767 int32-to-uint32-tap (int32→uint64, not uint32)|r767 i2u / r987 leftover
int64-to-int32-seq|i64i32|int64|int32|seq|902|VARINT int64|VARINT int32 trunc|Python|r772 int64-to-uint64-seq (int64→int32 narrow, not unsigned)|r772 i64u / r987 leftover
int64-to-uint32-seq|i64u32|int64|uint32|seq|903|VARINT int64|unsigned VARINT 32 trunc|Java|r772 int64-to-uint64-seq (int64→uint32 narrow)|r772 i64u / r987 leftover
int64-to-sint32-seq|i64s32|int64|sint32|seq|904|VARINT int64|zigzag VARINT 32|Rust|r741 int32-to-sint32-tap (int64→sint32, not int32)|r741 i2s32 / r987 leftover
int64-to-sint64-seq|i64s64|int64|sint64|seq|905|VARINT int64|zigzag VARINT 64|Go|r737 sint64-to-int64-zigzag (opposite)|r737 s64i / r987 leftover
int64-to-fixed32-seq|i64f32|int64|fixed32|seq|906|VARINT int64|FIXED32 trunc|Kotlin|r801 int32-to-fixed32-tap (int64→fixed32, not int32)|r801 i32f32 / r987 leftover
int64-to-fixed64-seq|i64f64|int64|fixed64|seq|907|VARINT int64|FIXED64 unsigned bits|Go|r725 int64-to-sfixed64-seq (int64→fixed64 unsigned, not sfixed64)|r725 i64sf / r987 leftover
int64-to-bool-seq|i64bl|int64|bool|seq|908|VARINT int64|VARINT 0/1|Python|r779 int32-to-bool-flag (int64→bool, not int32)|r779 i2b / r987 leftover
int64-to-enum-mode|i64en|int64|Mode|mode|909|VARINT int64|VARINT enum|Java|r735 enum-to-int32-grade (int64→enum, not int32)|r735 e2i / r987 leftover
uint32-to-int64-port|u32i64|uint32|int64|port|910|unsigned VARINT 32|signed VARINT 64|Go|r776 uint32-to-uint64-port (uint32→int64 signed, not uint64)|r776 u2u64 / r987 leftover
uint32-to-sint64-port|u32s64|uint32|sint64|port|911|unsigned VARINT 32|zigzag VARINT 64|TypeScript|r303 uint32-to-sint32-port (uint32→sint64, not sint32)|r303 u2s32 / r987 leftover
uint32-to-enum-port|u32en|uint32|Mode|mode|912|unsigned VARINT|VARINT enum|C++|r735 enum-to-int32-grade (uint32→enum, not int32)|r735 e2i / r987 leftover
uint64-to-int32-hash|u64i32|uint64|int32|hash|913|unsigned VARINT 64|VARINT int32 trunc|Go|r217 uint64-to-int64-seq (uint64→int32 narrow)|r217 u64i / r987 leftover
uint64-to-uint32-hash|u64u32|uint64|uint32|hash|914|unsigned VARINT 64|unsigned VARINT 32 trunc|Python|r776 uint32-to-uint64-port (opposite)|r776 u2u64 / r987 leftover
uint64-to-sint32-hash|u64s32|uint64|sint32|hash|915|unsigned VARINT 64|zigzag VARINT 32|Rust|r304 uint64-to-sint64-seq (uint64→sint32 narrow)|r304 u2s64 / r987 leftover
uint64-to-fixed32-hash|u64f32|uint64|fixed32|hash|916|unsigned VARINT 64|FIXED32 trunc|Go|r769 uint64-to-fixed64-seq (uint64→fixed32, not fixed64)|r769 u2f64 / r987 leftover
uint64-to-bool-hash|u64bl|uint64|bool|hash|917|unsigned VARINT 64|VARINT 0/1|Swift|r708 uint32-to-bool-flag (uint64→bool, not uint32)|r708 u2b / r987 leftover
uint64-to-enum-hash|u64en|uint64|Mode|mode|918|unsigned VARINT 64|VARINT enum|Java|r735 enum-to-int32-grade (uint64→enum)|r735 e2i / r987 leftover
sint32-to-int64-delta|s32i64|sint32|int64|delta|919|zigzag VARINT 32|VARINT int64|Go|r212 sint32-to-sint64-delta (sint32→int64, not sint64)|r212 s32w / r987 leftover
sint32-to-uint32-delta|s32u32|sint32|uint32|delta|920|zigzag VARINT|unsigned VARINT|Kotlin|r703 sint32-to-uint64-delta (sint32→uint32, not uint64)|r703 s32u64 / r987 leftover
sint32-to-fixed32-delta|s32f32|sint32|fixed32|delta|921|zigzag VARINT|FIXED32 unsigned|Go|r210 sint32-to-sfixed32-delta (sint32→fixed32 unsigned, not sfixed32)|r210 s32sf / r987 leftover
sint32-to-fixed64-delta|s32f64|sint32|fixed64|delta|922|zigzag VARINT 32|FIXED64|Python|r210 sint32-to-sfixed32-delta (sint32→fixed64, not sfixed32)|r210 s32sf / r987 leftover
sint32-to-sfixed64-delta|s32sf64|sint32|sfixed64|delta|923|zigzag VARINT 32|FIXED64 signed|Go|r211 sint64-to-sfixed64-delta (sint32→sfixed64, not sint64)|r211 s64sf / r987 leftover
sint32-to-bool-delta|s32bl|sint32|bool|delta|924|zigzag VARINT|VARINT 0/1|Dart|r230 enum-to-bool-mode (sint32→bool, not enum)|r230 e2b / r987 leftover
sint32-to-enum-delta|s32en|sint32|Mode|mode|925|zigzag VARINT|VARINT enum|Java|r302 enum-to-sint32-mode (opposite)|r302 e2s32 / r987 leftover
sint64-to-int32-delta|s64i32|sint64|int32|delta|926|zigzag VARINT 64|VARINT int32 trunc|Go|r737 sint64-to-int64-zigzag (sint64→int32 narrow)|r737 s64i / r987 leftover
sint64-to-uint64-delta|s64u64|sint64|uint64|delta|927|zigzag VARINT 64|unsigned VARINT 64|Rust|r304 uint64-to-sint64-seq (opposite)|r304 u2s64 / r987 leftover
sint64-to-sint32-delta|s64s32|sint64|sint32|delta|928|zigzag VARINT 64|zigzag VARINT 32 trunc|Go|r212 sint32-to-sint64-delta (opposite)|r212 s32w / r987 leftover
sint64-to-fixed32-delta|s64f32|sint64|fixed32|delta|929|zigzag VARINT 64|FIXED32 trunc|Python|r211 sint64-to-sfixed64-delta (sint64→fixed32, not sfixed64)|r211 s64sf / r987 leftover
sint64-to-fixed64-delta|s64f64|sint64|fixed64|delta|930|zigzag VARINT 64|FIXED64 unsigned|Go|r211 sint64-to-sfixed64-delta (sint64→fixed64 unsigned)|r211 s64sf / r987 leftover
sint64-to-sfixed32-delta|s64sf32|sint64|sfixed32|delta|931|zigzag VARINT 64|FIXED32 signed trunc|C++|r210 sint32-to-sfixed32-delta (sint64→sfixed32, not sint32)|r210 s32sf / r987 leftover
sint64-to-bool-delta|s64bl|sint64|bool|delta|932|zigzag VARINT 64|VARINT 0/1|Go|r512 bool-to-sint64 (opposite family)|r512 b2s64 / r987 leftover
sint64-to-enum-delta|s64en|sint64|Mode|mode|933|zigzag VARINT 64|VARINT enum|Kotlin|r302 enum-to-sint32-mode (sint64→enum, not enum→sint32)|r302 e2s32 / r987 leftover
fixed32-to-int32-crc|f32i32|fixed32|int32|crc|934|FIXED32 unsigned|VARINT int32|Go|r215 fixed32-to-uint32-crc (fixed32→int32 signed, not uint32)|r215 f32u / r987 leftover
fixed32-to-uint64-crc|f32u64|fixed32|uint64|crc|935|FIXED32 unsigned|unsigned VARINT 64|Python|r216 fixed64-to-uint64-hash (fixed32→uint64, not fixed64)|r216 f64u / r987 leftover
fixed32-to-fixed64-crc|f32f64|fixed32|fixed64|crc|936|FIXED32 4-byte|FIXED64 8-byte|Go|r802 uint32-to-fixed64-port (fixed32→fixed64 width)|r802 u32f64 / r987 leftover
fixed32-to-sfixed32-crc|f32sf32|fixed32|sfixed32|crc|937|FIXED32 unsigned bits|FIXED32 signed bits|Java|r747 sfixed32-to-fixed32-crc (opposite)|r747 sf2f / r987 leftover
fixed32-to-sfixed64-crc|f32sf64|fixed32|sfixed64|crc|938|FIXED32 unsigned|FIXED64 signed|Go|r404 int32-to-sfixed64-tap (fixed32→sfixed64)|r404 i32sf64 / r987 leftover
fixed32-to-double-crc|f32dbl|fixed32|double|crc|939|FIXED32 unsigned bits|FIXED64 float bits|Rust|r771 fixed32-to-float-crc (fixed32→double, not float)|r771 f32f / r987 leftover
fixed32-to-bool-crc|f32bl|fixed32|bool|crc|940|FIXED32 unsigned|VARINT 0/1|Go|r409 bool-to-fixed32-armed (opposite)|r409 b2f32 / r987 leftover
fixed32-to-enum-crc|f32en|fixed32|Mode|mode|941|FIXED32 unsigned|VARINT enum|TypeScript|r709 enum-to-fixed32-mode (opposite)|r709 e2f32 / r987 leftover
fixed64-to-int64-hash|f64i64|fixed64|int64|hash|942|FIXED64 unsigned|VARINT int64|Go|r216 fixed64-to-uint64-hash (fixed64→int64 signed, not uint64)|r216 f64u / r987 leftover
fixed64-to-uint32-hash|f64u32|fixed64|uint32|hash|943|FIXED64 unsigned|unsigned VARINT 32 trunc|Python|r216 fixed64-to-uint64-hash (fixed64→uint32 narrow)|r216 f64u / r987 leftover
fixed64-to-sint64-hash|f64s64|fixed64|sint64|hash|944|FIXED64 unsigned|zigzag VARINT 64|Go|r805 fixed64-to-sint32-hash (fixed64→sint64, not sint32)|r805 f64s32 / r987 leftover
fixed64-to-fixed32-hash|f64f32|fixed64|fixed32|hash|945|FIXED64 8-byte|FIXED32 4-byte trunc|C#|r936 fixed32-to-fixed64-crc (opposite)|fixed32-to-fixed64-crc / r987 leftover
fixed64-to-sfixed32-hash|f64sf32|fixed64|sfixed32|hash|946|FIXED64 unsigned|FIXED32 signed trunc|Go|r804 sfixed64-to-int32-hash (fixed64→sfixed32)|r804 sf64i32 / r987 leftover
fixed64-to-sfixed64-hash|f64sf64|fixed64|sfixed64|hash|947|FIXED64 unsigned bits|FIXED64 signed bits|Java|r221 double-to-sfixed64-peak (fixed64 bits→sfixed64, not double)|r221 d2sf / r987 leftover
fixed64-to-float-hash|f64flt|fixed64|float|hash|948|FIXED64 unsigned|FIXED32 float|Go|r219 double-to-fixed64-peak (fixed64→float, not double→fixed64)|r219 d2f64 / r987 leftover
fixed64-to-bool-hash|f64bl|fixed64|bool|hash|949|FIXED64 unsigned|VARINT 0/1|Kotlin|r409 bool-to-fixed32-armed (fixed64→bool, not bool→fixed32)|r409 b2f32 / r987 leftover
fixed64-to-enum-hash|f64en|fixed64|Mode|mode|950|FIXED64 unsigned|VARINT enum|Go|r987 enum-to-fixed64-mode (opposite direction; not that plant)|r987 e2f64 / r709 e2f32
sfixed32-to-uint64-crc|sf32u64|sfixed32|uint64|crc|951|FIXED32 signed|unsigned VARINT 64|Python|r781 sfixed32-to-int32-crc (sfixed32→uint64, not int32)|r781 sf32i / r987 leftover
sfixed32-to-sint64-crc|sf32s64|sfixed32|sint64|crc|952|FIXED32 signed|zigzag VARINT 64|Go|r305 sfixed32-to-sint32-crc (sfixed32→sint64, not sint32)|r305 sf2s32 / r987 leftover
sfixed32-to-fixed64-crc|sf32f64|sfixed32|fixed64|crc|953|FIXED32 signed|FIXED64 unsigned|Rust|r747 sfixed32-to-fixed32-crc (sfixed32→fixed64)|r747 sf2f / r987 leftover
sfixed32-to-sfixed64-crc|sf32sf64|sfixed32|sfixed64|crc|954|FIXED32 signed|FIXED64 signed|Go|r404 int32-to-sfixed64-tap (sfixed32→sfixed64 width)|r404 i32sf64 / r987 leftover
sfixed32-to-double-crc|sf32dbl|sfixed32|double|crc|955|FIXED32 signed bits|FIXED64 float|Java|r213 sfixed32-to-float-crc (sfixed32→double, not float)|r213 sf32f / r987 leftover
sfixed32-to-bool-crc|sf32bl|sfixed32|bool|crc|956|FIXED32 signed|VARINT 0/1|Go|r767 bool-to-int32-armed (sfixed32→bool)|r767 b2i / r987 leftover
sfixed32-to-enum-crc|sf32en|sfixed32|Mode|mode|957|FIXED32 signed|VARINT enum|Swift|r612 enum-to-sfixed32-mode (opposite)|r612 e2sf32 / r987 leftover
sfixed64-to-uint32-hash|sf64u32|sfixed64|uint32|hash|958|FIXED64 signed|unsigned VARINT 32 trunc|Go|r804 sfixed64-to-int32-hash (sfixed64→uint32, not int32)|r804 sf64i32 / r987 leftover
sfixed64-to-sint32-hash|sf64s32|sfixed64|sint32|hash|959|FIXED64 signed|zigzag VARINT 32|Python|r804 sfixed64-to-int32-hash (sfixed64→sint32 zigzag)|r804 sf64i32 / r987 leftover
sfixed64-to-sint64-hash|sf64s64|sfixed64|sint64|hash|960|FIXED64 signed|zigzag VARINT 64|Go|r211 sint64-to-sfixed64-delta (opposite)|r211 s64sf / r987 leftover
sfixed64-to-fixed32-hash|sf64f32|sfixed64|fixed32|hash|961|FIXED64 signed|FIXED32 unsigned trunc|C++|r747 sfixed32-to-fixed32-crc (sfixed64→fixed32)|r747 sf2f / r987 leftover
sfixed64-to-fixed64-hash|sf64f64|sfixed64|fixed64|hash|962|FIXED64 signed bits|FIXED64 unsigned bits|Go|fixed64-to-sfixed64-hash (opposite)|f64sf64 / r987 leftover
sfixed64-to-float-hash|sf64flt|sfixed64|float|hash|963|FIXED64 signed|FIXED32 float|Kotlin|r214 sfixed64-to-double-hash (sfixed64→float, not double)|r214 sf64d / r987 leftover
sfixed64-to-bool-hash|sf64bl|sfixed64|bool|hash|964|FIXED64 signed|VARINT 0/1|Go|r408 bool-to-double-armed (sfixed64→bool, not bool→double)|r408 b2d / r987 leftover
sfixed64-to-enum-hash|sf64en|sfixed64|Mode|mode|965|FIXED64 signed|VARINT enum|Java|r987 enum-to-fixed64-mode (sfixed64 signed, not unsigned fixed64)|r987 e2f64 / r612 e2sf32
float-to-sint64-temp|f2s64|float|sint64|temp_c|966|FIXED32 float|zigzag VARINT 64|Go|r410 sint32-to-float-delta (float→sint64, not sint32→float)|r410 s32f / r987 leftover
float-to-fixed64-temp|f2f64|float|fixed64|temp_c|967|FIXED32 float|FIXED64 unsigned|Python|r218 float-to-fixed32-temp (float→fixed64, not fixed32)|r218 f2f32 / r987 leftover
float-to-bool-temp|f2bl|float|bool|temp_c|968|FIXED32 float|VARINT 0/1|Go|r407 bool-to-float-armed (opposite)|r407 b2f / r987 leftover
float-to-enum-temp|f2en|float|Mode|mode|969|FIXED32 float|VARINT enum|Rust|r421 enum-to-float-mode (opposite)|r421 e2f / r987 leftover
double-to-sint32-peak|d2s32|double|sint32|peak|970|FIXED64 double|zigzag VARINT 32|Go|r411 sint64-to-double-delta (double→sint32 narrow)|r411 s64d / r987 leftover
double-to-fixed32-peak|d2f32|double|fixed32|peak|971|FIXED64 double|FIXED32 unsigned trunc|Java|r219 double-to-fixed64-peak (double→fixed32, not fixed64)|r219 d2f64 / r987 leftover
double-to-bool-peak|d2bl|double|bool|peak|972|FIXED64 double|VARINT 0/1|Go|r408 bool-to-double-armed (opposite)|r408 b2d / r987 leftover
double-to-enum-peak|d2en|double|Mode|mode|973|FIXED64 double|VARINT enum|TypeScript|r421 enum-to-float-mode (double→enum, not enum→float)|r421 e2f / r987 leftover
bool-to-int64-armed|b2i64|bool|int64|armed|974|VARINT 0/1|VARINT int64|Go|r767 bool-to-int32-armed (bool→int64, not int32)|r767 b2i / r987 leftover
bool-to-enum-armed|b2en|bool|Mode|mode|975|VARINT 0/1|VARINT enum|Python|r230 enum-to-bool-mode (opposite)|r230 e2b / r987 leftover
string-to-int64-sku|s2i64|string|int64|sku|976|LEN utf8|VARINT int64|Go|r227 string-to-int32-sku (string→int64, not int32)|r227 s2i32 / r987 leftover
string-to-double-sku|s2dbl|string|double|sku|977|LEN utf8|FIXED64 double|Java|r229 string-to-float-temp (string→double, not float)|r229 s2f / r987 leftover
bytes-to-sint64-blob|b2s64|bytes|sint64|blob|978|LEN bytes|zigzag VARINT 64|Go|r431 bytes-to-sint32-delta (bytes→sint64, not sint32)|r431 b2s32 / r987 leftover
bytes-to-enum-blob|byen|bytes|Mode|mode|979|LEN bytes|VARINT enum|Kotlin|r420 enum-to-bytes-mode (opposite)|r420 e2by / r987 leftover
enum-to-int64-mode|e2i64|Mode|int64|mode|980|VARINT enum|VARINT int64|Go|r735 enum-to-int32-grade (enum→int64, not int32)|r735 e2i / r987 leftover
enum-to-uint64-mode|e2u64|Mode|uint64|mode|981|VARINT enum|unsigned VARINT 64|Python|r987 enum-to-fixed64-mode (enum→uint64 varint, not fixed64)|r987 e2f64 / r735 e2i
enum-to-sint64-mode|e2s64|Mode|sint64|mode|982|VARINT enum|zigzag VARINT 64|Go|r302 enum-to-sint32-mode (enum→sint64, not sint32)|r302 e2s32 / r987 leftover
enum-to-sfixed64-mode|e2sf64|Mode|sfixed64|mode|983|VARINT enum|FIXED64 signed|Java|r612 enum-to-sfixed32-mode (enum→sfixed64, not sfixed32)|r612 e2sf32 / r987 e2f64
singular-int64-to-repeated|i64rep|int64|repeated int64|seq|984|singular VARINT|packed LEN repeated|Go|r300 singular-int32-to-repeated (int64 cardinality, not int32)|r300 i2rep / unpacked catalog
singular-uint64-to-repeated|u64rep|uint64|repeated uint64|hash|985|singular VARINT|packed LEN repeated|Python|r730 singular-uint32-to-repeated (uint64, not uint32)|r730 u32rep / unpacked catalog
singular-sint32-to-repeated|s32rep|sint32|repeated sint32|delta|986|singular zigzag|packed zigzag LEN|Go|r300 singular-int32-to-repeated (sint32 zigzag, not int32)|r300 i2rep / r987 leftover
singular-sint64-to-repeated|s64rep|sint64|repeated sint64|delta|987|singular zigzag 64|packed zigzag LEN|Rust|singular-sint32-to-repeated (sint64, not sint32)|s32rep / unpacked catalog
singular-fixed32-to-repeated|f32rep|fixed32|repeated fixed32|crc|988|singular FIXED32|packed FIXED32 LEN|Go|r300 singular-int32-to-repeated (fixed32, not int32)|r300 i2rep / unpacked catalog
singular-fixed64-to-repeated|f64rep|fixed64|repeated fixed64|hash|989|singular FIXED64|packed FIXED64 LEN|Java|singular-fixed32-to-repeated (fixed64, not fixed32)|f32rep / unpacked catalog
singular-sfixed32-to-repeated|sf32rep|sfixed32|repeated sfixed32|crc|990|singular FIXED32 signed|packed sfixed32 LEN|Go|singular-fixed32-to-repeated (sfixed32 signed, not unsigned)|f32rep / unpacked catalog
singular-sfixed64-to-repeated|sf64rep|sfixed64|repeated sfixed64|hash|991|singular FIXED64 signed|packed sfixed64 LEN|Python|singular-fixed64-to-repeated (sfixed64 signed)|f64rep / unpacked catalog
singular-timestamp-to-repeated|tsrep|google.protobuf.Timestamp|repeated google.protobuf.Timestamp|poured_at|992|singular LEN Timestamp|repeated LEN Timestamp|Go|r299 singular-string-to-repeated (Timestamp WKT, not string)|r299 s2rep / r987 leftover
singular-duration-to-repeated|durrep|google.protobuf.Duration|repeated google.protobuf.Duration|hold|993|singular LEN Duration|repeated LEN Duration|TypeScript|singular-timestamp-to-repeated (Duration, not Timestamp)|tsrep / unpacked catalog
singular-any-to-repeated|anyrep|google.protobuf.Any|repeated google.protobuf.Any|event|994|singular LEN Any|repeated LEN Any|Go|singular-timestamp-to-repeated (Any, not Timestamp)|tsrep / r712 any-to-bytes
singular-struct-to-repeated|strep|google.protobuf.Struct|repeated google.protobuf.Struct|attrs|995|singular LEN Struct|repeated LEN Struct|Python|singular-any-to-repeated (Struct, not Any)|anyrep / r716 struct-to-string
repeated-int64-to-singular|rep64s|repeated int64|int64|seq|996|packed LEN repeated|singular VARINT|Go|r697 repeated-int32-to-singular (int64, not int32)|r697 r2s / unpacked catalog
repeated-uint64-to-singular|repu64s|repeated uint64|uint64|hash|997|packed LEN repeated|singular VARINT|C++|repeated-int64-to-singular (uint64, not int64)|rep64s / unpacked catalog
repeated-sint32-to-singular|reps32s|repeated sint32|sint32|delta|998|packed zigzag LEN|singular zigzag|Go|r697 repeated-int32-to-singular (sint32 zigzag, not int32)|r697 r2s / unpacked catalog
repeated-fixed32-to-singular|repf32s|repeated fixed32|fixed32|crc|999|packed FIXED32 LEN|singular FIXED32|Java|repeated-sint32-to-singular (fixed32, not sint32)|reps32s / unpacked catalog
timezone-to-string-zone|tz2s|google.type.TimeZone|string|zone|1001|LEN TimeZone id+version|LEN utf8|Go|r255 date-to-string-poured (type.TimeZone, not Date)|r255 dt2s / r987 leftover
dayofweek-to-string-dow|dow2s|google.type.DayOfWeek|string|dow|1002|VARINT DayOfWeek enum|LEN utf8|Python|r267 calendarperiod-to-string (DayOfWeek, not CalendarPeriod)|r267 cp2s / r987 leftover
month-to-int32-cal|mo2i|google.type.Month|int32|cal|1003|VARINT Month enum|VARINT int32|Go|r267 calendarperiod-to-int32 (Month, not CalendarPeriod)|r267 cp2i / r987 leftover
fraction-to-string-ratio|fr2s|google.type.Fraction|string|ratio|1004|LEN Fraction num/den|LEN utf8|Java|r263 decimal-to-string-assay (Fraction, not Decimal)|r263 dec2s / r987 leftover
localizedtext-to-string-label|lt2s|google.type.LocalizedText|string|label|1005|LEN LocalizedText text+lang|LEN utf8|Go|r965 localizedmsg-to-string (type.LocalizedText, not rpc.LocalizedMessage)|r965 locmsg / r987 leftover
timezone-to-bytes-zone|tz2b|google.type.TimeZone|bytes|zone|1006|LEN TimeZone|LEN opaque bytes|Rust|timezone-to-string-zone (TimeZone→bytes, not string)|tz2s / r987 leftover
dayofweek-to-int32-dow|dow2i|google.type.DayOfWeek|int32|dow|1007|VARINT DayOfWeek|VARINT int32|Go|dayofweek-to-string-dow (DayOfWeek→int32, not string)|dow2s / r987 leftover
month-to-string-cal|mo2s|google.type.Month|string|cal|1008|VARINT Month enum|LEN utf8|Python|month-to-int32-cal (Month→string, not int32)|mo2i / r987 leftover
fraction-to-double-ratio|fr2d|google.type.Fraction|double|ratio|1009|LEN Fraction|FIXED64 double|Go|fraction-to-string-ratio (Fraction→double, not string)|fr2s / r987 leftover
localizedtext-to-bytes-label|lt2b|google.type.LocalizedText|bytes|label|1010|LEN LocalizedText|LEN opaque bytes|TypeScript|localizedtext-to-string-label (LocalizedText→bytes)|lt2s / r987 leftover
timezone-to-struct-zone|tz2st|google.type.TimeZone|google.protobuf.Struct|zone|1011|LEN TimeZone|LEN Struct fields|Go|timezone-to-string-zone (TimeZone→Struct, not string)|tz2s / r716 struct-to-string
dayofweek-to-bool-dow|dow2b|google.type.DayOfWeek|bool|dow|1012|VARINT DayOfWeek|VARINT 0/1|Java|dayofweek-to-string-dow (DayOfWeek→bool)|dow2s / r230 e2b
month-to-sint32-cal|mo2s32|google.type.Month|sint32|cal|1013|VARINT Month enum|zigzag VARINT|Go|month-to-int32-cal (Month→sint32 zigzag)|mo2i / r987 leftover
fraction-to-bytes-ratio|fr2b|google.type.Fraction|bytes|ratio|1014|LEN Fraction|LEN opaque bytes|Python|fraction-to-string-ratio (Fraction→bytes)|fr2s / r987 leftover
localizedtext-to-struct-label|lt2st|google.type.LocalizedText|google.protobuf.Struct|label|1015|LEN LocalizedText|LEN Struct|Go|localizedtext-to-string-label (LocalizedText→Struct)|lt2s / r716 st2s
dayofweek-to-fixed32-dow|dow2f32|google.type.DayOfWeek|fixed32|dow|1016|VARINT DayOfWeek|FIXED32|C++|dayofweek-to-int32-dow (DayOfWeek→fixed32)|dow2i / r709 e2f32
int32value-to-string-count|i32v2s|google.protobuf.Int32Value|string|count|1017|LEN Int32Value|LEN utf8|Go|r313 int32value-to-int64value (Int32Value→string, not Int64Value)|r313 i32v64 / r731 unwrap
int64value-to-bytes-count|i64v2b|google.protobuf.Int64Value|bytes|count|1018|LEN Int64Value|LEN bytes|Python|r317 bytesvalue-to-string-blob (Int64Value→bytes, not BytesValue unwrap)|r317 bv2s / r706 unwrap
uint32value-to-int32value|u32v32v|google.protobuf.UInt32Value|google.protobuf.Int32Value|port|1019|LEN UInt32Value|LEN Int32Value|Go|r318 uint32value-to-string-port (UInt32Value→Int32Value, not string)|r318 u32v2s / r730 unwrap
uint64value-to-int64value|u64v64v|google.protobuf.UInt64Value|google.protobuf.Int64Value|hash|1020|LEN UInt64Value|LEN Int64Value|Java|uint32value-to-int32value (64-bit wrappers)|u32v32v / r726 unwrap
floatvalue-to-int32value|fv2i32v|google.protobuf.FloatValue|google.protobuf.Int32Value|temp_c|1021|LEN FloatValue|LEN Int32Value|Go|r314 floatvalue-to-doublevalue (FloatValue→Int32Value, not DoubleValue)|r314 fv2dv / r738 unwrap
doublevalue-to-int64value|dv2i64v|google.protobuf.DoubleValue|google.protobuf.Int64Value|peak|1022|LEN DoubleValue|LEN Int64Value|Kotlin|r316 doublevalue-to-stringvalue (DoubleValue→Int64Value, not StringValue)|r316 dv2sv / r719 unwrap
boolvalue-to-bytesvalue|bv2byv|google.protobuf.BoolValue|google.protobuf.BytesValue|ok|1023|LEN BoolValue|LEN BytesValue|Go|r315 boolvalue-to-stringvalue (BoolValue→BytesValue, not StringValue)|r315 bv2sv / r714 unwrap
stringvalue-to-boolvalue|sv2blv|google.protobuf.StringValue|google.protobuf.BoolValue|ok|1024|LEN StringValue|LEN BoolValue|Python|r315 boolvalue-to-stringvalue (opposite)|r315 bv2sv / r704 unwrap
int32value-to-bytesvalue|i32v2bv|google.protobuf.Int32Value|google.protobuf.BytesValue|count|1025|LEN Int32Value|LEN BytesValue|Go|int32value-to-string-count (Int32Value→BytesValue, not string)|i32v2s / r731 unwrap
uint32value-to-boolvalue|u32v2bl|google.protobuf.UInt32Value|google.protobuf.BoolValue|port|1026|LEN UInt32Value|LEN BoolValue|Dart|r318 uint32value-to-string-port (UInt32Value→BoolValue)|r318 u32v2s / r730 unwrap
int64value-to-doublevalue|i64v2dv|google.protobuf.Int64Value|google.protobuf.DoubleValue|count|1027|LEN Int64Value|LEN DoubleValue|Go|doublevalue-to-int64value (opposite)|dv2i64v / r706 unwrap
floatvalue-to-bytesvalue|fv2bv|google.protobuf.FloatValue|google.protobuf.BytesValue|temp_c|1028|LEN FloatValue|LEN BytesValue|Java|floatvalue-to-int32value (FloatValue→BytesValue)|fv2i32v / r738 unwrap
proto2-required-fixed32-to-uint32|p2f32u|fixed32|uint32|crc|2|FIXED32 unsigned|VARINT uint32|Java|r215 fixed32-to-uint32-crc (proto2 required, not proto3)|r215 f32u / optional drop
proto2-required-fixed64-to-uint64|p2f64u|fixed64|uint64|hash|3|FIXED64 unsigned|VARINT uint64|Go|r216 fixed64-to-uint64-hash (proto2 required)|r216 f64u / optional drop
proto2-required-sint64-to-int64|p2s64i|sint64|int64|soak|2|zigzag VARINT 64|VARINT int64|Python|r737 sint64-to-int64-zigzag (proto2 required)|r737 s64i / optional drop
proto2-required-sfixed64-to-int64|p2sf64i|sfixed64|int64|hash|4|FIXED64 signed|VARINT int64|Go|r778 sfixed64-to-int64-seq (proto2 required)|r778 sf2i / optional drop
proto2-optional-uint32-to-int32|p2ou32i|uint32|int32|port|5|unsigned VARINT|signed VARINT|Java|r782 uint32-to-int32-port (proto2 optional TYPE, not optional drop)|r782 u2i / r629 optional drop
proto2-optional-sint32-to-int32|p2os32i|sint32|int32|delta|6|zigzag VARINT|VARINT int32|Go|r732 sint32-to-int32-zigzag (proto2 optional TYPE, not drop)|r732 s2i / r629 optional drop
proto2-optional-fixed32-to-float|p2of32f|fixed32|float|crc|7|FIXED32 unsigned bits|FIXED32 float bits|C++|r771 fixed32-to-float-crc (proto2 optional TYPE, not drop)|r771 f32f / r629 optional drop
proto2-optional-sfixed32-to-int32|p2osf32|sfixed32|int32|crc|8|FIXED32 signed|VARINT int32|Go|r781 sfixed32-to-int32-crc (proto2 optional TYPE, not drop)|r781 sf32i / r629 optional drop
proto2-required-fixed32-to-bytes|p2f32b|fixed32|bytes|crc|2|FIXED32 unsigned|LEN bytes|Python|r416 fixed32-to-bytes-crc (proto2 required)|r416 f32b / optional drop
proto2-required-sint64-to-string|p2s64s|sint64|string|soak|3|zigzag VARINT 64|LEN utf8|Java|r412 sint32-to-string-delta (proto2 required sint64)|r412 s32s / optional drop
proto2-optional-double-to-float|p2od2f|double|float|temp_c|9|FIXED64 double|FIXED32 float|Go|r716 double-to-float-celsius (proto2 optional TYPE, not drop)|r716 d2f / r629 optional drop
proto2-optional-bool-to-int32|p2ob2i|bool|int32|armed|10|VARINT 0/1|VARINT int32|Kotlin|r767 bool-to-int32-armed (proto2 optional TYPE, not drop)|r767 b2i / r629 optional drop
oneof-int32-to-int64|oi32i64|int32|int64|tap_n|1031|VARINT int32|VARINT int64|Go|r775 int32-to-int64-tap (oneof arm, not scalar)|r775 i2i64 / r706 oneof-int-to-bytes
oneof-int32-to-string|oi32s|int32|string|tap_n|1032|VARINT int32|LEN utf8|Python|r207 int32-to-string-tap (oneof arm)|r207 i32s / r757 oneof-i32-to-str
oneof-int32-to-bytes|oi32b|int32|bytes|tap_n|1033|VARINT int32|LEN bytes|Go|r208 int32-to-bytes-tap (oneof arm)|r208 i32b / r706 oneof-int-to-bytes
oneof-int32-to-bool|oi32bl|int32|bool|tap_n|1034|VARINT int32|VARINT 0/1|Java|r779 int32-to-bool-flag (oneof arm)|r779 i2b / r703 oneof-bool-to-msg
oneof-int64-to-string|oi64s|int64|string|seq|1035|VARINT int64|LEN utf8|Go|r201 int64-to-string-seq (oneof arm)|r201 i64s / r280 oneof-int64-to-uint64
oneof-int64-to-bytes|oi64b|int64|bytes|seq|1036|VARINT int64|LEN bytes|Rust|r209 int64-to-bytes-seq (oneof arm)|r209 i64b / r706 oneof-int-to-bytes
oneof-int64-to-double|oi64d|int64|double|seq|1037|VARINT int64|FIXED64 double|Go|r401 int64-to-double-seq (oneof arm)|r401 i64d / r280 oi64u
oneof-string-to-int32|os2i32|string|int32|sku|1038|LEN utf8|VARINT int32|Python|r227 string-to-int32-sku (oneof arm)|r227 s2i32 / r729 oneof-string-to-bytes
oneof-enum-to-string|oe2s|Mode|string|mode|1039|VARINT enum|LEN utf8|Go|r722 enum-to-string-grade (oneof arm)|r722 e2s / r274 oneof-enum-to-msg
oneof-enum-to-int32|oe2i|Mode|int32|mode|1040|VARINT enum|VARINT int32|Java|r735 enum-to-int32-grade (oneof arm)|r735 e2i / r756 oneof-enum-to-int
oneof-float-to-string|of2s|float|string|temp_c|1041|FIXED32 float|LEN utf8|Go|r204 float-to-string-temp (oneof arm)|r204 f2s / r272 oneof-float-to-double
oneof-fixed32-to-uint32|of32u|fixed32|uint32|crc|1042|FIXED32|VARINT uint32|C#|r215 fixed32-to-uint32-crc (oneof arm)|r215 f32u / r727 oneof-uint32-to-fixed32
oneof-sfixed64-to-double|osf64d|sfixed64|double|hash|1043|FIXED64 signed bits|FIXED64 float bits|Go|r214 sfixed64-to-double-hash (oneof arm)|r214 sf64d / r987 leftover
oneof-sint32-to-int32|os32i|sint32|int32|delta|1044|zigzag VARINT|VARINT int32|Python|r732 sint32-to-int32-zigzag (oneof arm)|r732 s2i / r412 oneof-sint32-to-string
oneof-uint64-to-string|ou64s|uint64|string|hash|1045|unsigned VARINT|LEN utf8|Go|r203 uint64-to-string-hash (oneof arm)|r203 u64s / r280 oneof-int64-to-uint64
oneof-bytes-to-int32|ob2i32|bytes|int32|blob|1046|LEN bytes|VARINT int32|Swift|r426 bytes-to-int32-tap (oneof arm)|r426 b2i32 / r706 oneof-int-to-bytes
rpc-unary-to-server-stream|u2ss|rpc Watch(Heat) returns (Heat)|rpc Watch(Heat) returns (stream Heat)|watch|1047|unary frames|server-stream frames|Go|r978 client-stream-to-unary-ingest (unary→server-stream, not client-stream→unary)|r978 cs2u / r676 unary-to-lro
rpc-server-stream-to-bidi|ss2bi|rpc Watch(Heat) returns (stream Heat)|rpc Watch(stream Heat) returns (stream Heat)|watch|1048|server-stream|bidi stream|TypeScript|rpc-unary-to-server-stream (server-stream→bidi)|u2ss / r978 cs2u
rpc-bidi-to-unary|bi2u|rpc Chat(stream Heat) returns (stream Heat)|rpc Chat(Heat) returns (Heat)|chat|1049|bidi stream frames|unary single Heat|Go|r978 client-stream-to-unary-ingest (bidi→unary, not client-stream→unary)|r978 cs2u / r676 LRO
rpc-client-stream-to-server-stream|cs2ss|rpc Ingest(stream Heat) returns (Heat)|rpc Ingest(Heat) returns (stream Heat)|ingest|1050|client-stream request|server-stream response|Python|r978 client-stream-to-unary-ingest (client-stream→server-stream, not unary)|r978 cs2u / u2ss
map-value-sint64-to-string|mvs64s|sint64|string|deltas|14|value zigzag VARINT|value LEN utf8|Go|r728 map-value-sint32-to-string (sint64 values, not sint32)|r728 mvs32s / map-key ban
map-value-sfixed32-to-int32|mvsf32i|sfixed32|int32|crcs|15|value FIXED32 signed|value VARINT|Java|r781 sfixed32-to-int32-crc (map value, not scalar)|r781 sf32i / map-key ban
map-value-fixed64-to-string|mvf64s|fixed64|string|hashes|16|value FIXED64|value LEN utf8|Go|r417 fixed64-to-string-hash (map value)|r417 f64s / map-key ban
map-value-int64-to-bytes|mvi64b|int64|bytes|seqs|17|value VARINT|value LEN bytes|Python|r281 map-value-int64-to-string (int64→bytes, not string)|r281 mvi64s / map-key ban
map-value-double-to-int64|mvd2i64|double|int64|peaks|18|value FIXED64|value VARINT|Go|r734 double-to-int64-peak (map value)|r734 d2i / map-key ban
map-value-bytes-to-int32|mvb2i|bytes|int32|blobs|19|value LEN bytes|value VARINT|Rust|r426 bytes-to-int32-tap (map value)|r426 b2i32 / map-key ban
sourcecontext-to-string-file|sc2s|google.protobuf.SourceContext|string|file|1051|LEN SourceContext file_name|LEN utf8|Go|r710 nested-msg-to-string-note (SourceContext, not Note)|r710 n2s / r987 leftover
nullvalue-to-string-kind|nv2s|google.protobuf.NullValue|string|kind|1052|VARINT NullValue enum|LEN utf8|Python|r720 value-to-string-kind (NullValue enum, not Value message)|r720 v2s / r987 leftover
retryinfo-to-int64-delay|ri2i|google.rpc.RetryInfo|int64|retry|1053|LEN RetryInfo retry_delay Duration|VARINT nanos|Go|retryinfo-to-duration (RetryInfo message→int64, not Duration field)|retryinfo-to-duration / rpc star-to-string
sourcecontext-to-bytes-file|sc2b|google.protobuf.SourceContext|bytes|file|1054|LEN SourceContext|LEN opaque bytes|Java|sourcecontext-to-string-file (SourceContext→bytes)|sc2s / r705 m2b
nullvalue-to-int32-kind|nv2i|google.protobuf.NullValue|int32|kind|1055|VARINT NullValue|VARINT int32|Go|nullvalue-to-string-kind (NullValue→int32)|nv2s / r735 e2i
retryinfo-to-bytes-delay|ri2b|google.rpc.RetryInfo|bytes|retry|1056|LEN RetryInfo|LEN opaque bytes|TypeScript|retryinfo-to-int64-delay (RetryInfo→bytes, not int64)|ri2i / rpc star-to-string
fieldmask-to-int32|fm2i|google.protobuf.FieldMask|int32|mask|1057|LEN FieldMask paths[]|VARINT int32|Go|r712 fieldmask-to-string (FieldMask→int32, not string)|r712 fm2s / r728 fm2b
any-to-uint32-event|any2u32|google.protobuf.Any|uint32|event|1058|LEN Any type_url+value|unsigned VARINT|Python|r712 any-to-bytes-event (Any→uint32, not bytes)|r712 a2b / r987 leftover
empty-to-uint64-ack|emu64|google.protobuf.Empty|uint64|ack|1059|LEN empty 0-length|unsigned VARINT 64|Go|r248 empty-to-int32-ack (Empty→uint64, not int32)|r248 e2i / r769 e2s
duration-to-uint32-hold|dur2u32|google.protobuf.Duration|uint32|hold|1060|LEN Duration|unsigned VARINT 32|Java|r249 duration-to-int64-hold (Duration→uint32, not int64)|r249 dur2i / r720 d2s
timestamp-to-uint32-unix|ts2u32|google.protobuf.Timestamp|uint32|poured_at|1061|LEN Timestamp|unsigned VARINT 32 trunc|Go|r250 timestamp-to-int64-unix (Timestamp→uint32, not int64)|r250 ts2i / r713 ts2s
struct-to-int64-attrs|st2i64|google.protobuf.Struct|int64|attrs|1062|LEN Struct fields|VARINT int64|Python|r716 struct-to-string-attrs (Struct→int64, not string)|r716 st2s / r987 leftover
listvalue-to-uint64-tags|lv2u64|google.protobuf.ListValue|uint64|tags|1063|LEN ListValue values[]|unsigned VARINT 64|Go|r734 listvalue-to-int32-tags (ListValue→uint64, not int32)|r734 lv2i / r768 lv2s
value-to-sint32-kind|val2s32|google.protobuf.Value|sint32|kind|1064|LEN Value oneof|zigzag VARINT|Rust|r441 value-to-bool-kind (Value→sint32, not bool)|r441 val2b / r720 v2s
httpbody-to-struct-blob|hb2st|google.api.HttpBody|google.protobuf.Struct|blob|1065|LEN HttpBody content_type+data|LEN Struct fields|Go|r981 httpbody-to-bytes-blob (HttpBody→Struct, not bytes)|r981 h2b / r972 hex
sourcecontext-to-empty-file|sc2e|google.protobuf.SourceContext|google.protobuf.Empty|file|1066|LEN SourceContext|LEN empty 0-length|Java|sourcecontext-to-string-file (SourceContext→Empty)|sc2s / r717 empty-to-message
nullvalue-to-bool-kind|nv2b|google.protobuf.NullValue|bool|kind|1067|VARINT NullValue|VARINT 0/1|Go|nullvalue-to-int32-kind (NullValue→bool, not int32)|nv2i / r230 e2b
singular-empty-to-repeated|z000|google.protobuf.Empty|repeated google.protobuf.Empty|ack|1101|singular LEN empty 0-length|repeated LEN empty 0-length|Go|singular-int32-to-repeated (empty cardinality, not int32)|i2rep / unpacked catalog
repeated-empty-to-singular|z001|repeated google.protobuf.Empty|google.protobuf.Empty|ack|1102|repeated LEN empty 0-length|singular LEN empty 0-length|Python|repeated-int32-to-singular (empty cardinality, not int32)|r697 r2s / unpacked catalog
singular-fieldmask-to-repeated|z002|google.protobuf.FieldMask|repeated google.protobuf.FieldMask|mask|1103|singular LEN FieldMask paths[]|repeated LEN FieldMask paths[]|Python|singular-int32-to-repeated (fieldmask cardinality, not int32)|i2rep / unpacked catalog
repeated-fieldmask-to-singular|z003|repeated google.protobuf.FieldMask|google.protobuf.FieldMask|mask|1104|repeated LEN FieldMask paths[]|singular LEN FieldMask paths[]|Java|repeated-int32-to-singular (fieldmask cardinality, not int32)|r697 r2s / unpacked catalog
singular-value-to-repeated|z004|google.protobuf.Value|repeated google.protobuf.Value|kind|1105|singular LEN Value oneof|repeated LEN Value oneof|Java|singular-int32-to-repeated (value cardinality, not int32)|i2rep / unpacked catalog
repeated-value-to-singular|z005|repeated google.protobuf.Value|google.protobuf.Value|kind|1106|repeated LEN Value oneof|singular LEN Value oneof|Rust|repeated-int32-to-singular (value cardinality, not int32)|r697 r2s / unpacked catalog
singular-listvalue-to-repeated|z006|google.protobuf.ListValue|repeated google.protobuf.ListValue|tags|1107|singular LEN ListValue values[]|repeated LEN ListValue values[]|Rust|singular-int32-to-repeated (listvalue cardinality, not int32)|i2rep / unpacked catalog
repeated-listvalue-to-singular|z007|repeated google.protobuf.ListValue|google.protobuf.ListValue|tags|1108|repeated LEN ListValue values[]|singular LEN ListValue values[]|Kotlin|repeated-int32-to-singular (listvalue cardinality, not int32)|r697 r2s / unpacked catalog
singular-uint32-to-repeated|z008|uint32|repeated uint32|port|1109|singular unsigned VARINT 32|repeated unsigned VARINT 32|Kotlin|singular-int32-to-repeated (uint32 cardinality, not int32)|i2rep / unpacked catalog
repeated-uint32-to-singular|z009|repeated uint32|uint32|port|1110|repeated unsigned VARINT 32|singular unsigned VARINT 32|TypeScript|repeated-int32-to-singular (uint32 cardinality, not int32)|r697 r2s / unpacked catalog
repeated-sint64-to-singular|z010|repeated sint64|sint64|delta|1112|repeated zigzag VARINT 64|singular zigzag VARINT 64|C++|repeated-int32-to-singular (sint64 cardinality, not int32)|r697 r2s / unpacked catalog
repeated-fixed64-to-singular|z011|repeated fixed64|fixed64|hash|1114|repeated FIXED64 unsigned|singular FIXED64 unsigned|Swift|repeated-int32-to-singular (fixed64 cardinality, not int32)|r697 r2s / unpacked catalog
repeated-sfixed32-to-singular|z012|repeated sfixed32|sfixed32|crc|1116|repeated FIXED32 signed|singular FIXED32 signed|Dart|repeated-int32-to-singular (sfixed32 cardinality, not int32)|r697 r2s / unpacked catalog
repeated-sfixed64-to-singular|z013|repeated sfixed64|sfixed64|hash|1118|repeated FIXED64 signed|singular FIXED64 signed|C#|repeated-int32-to-singular (sfixed64 cardinality, not int32)|r697 r2s / unpacked catalog
singular-float-to-repeated|z014|float|repeated float|temp_c|1119|singular FIXED32 float|repeated FIXED32 float|C#|singular-int32-to-repeated (float cardinality, not int32)|i2rep / unpacked catalog
repeated-float-to-singular|z015|repeated float|float|temp_c|1120|repeated FIXED32 float|singular FIXED32 float|Go|repeated-int32-to-singular (float cardinality, not int32)|r697 r2s / unpacked catalog
singular-double-to-repeated|z016|double|repeated double|peak|1121|singular FIXED64 double|repeated FIXED64 double|Go|singular-int32-to-repeated (double cardinality, not int32)|i2rep / unpacked catalog
repeated-double-to-singular|z017|repeated double|double|peak|1122|repeated FIXED64 double|singular FIXED64 double|Python|repeated-int32-to-singular (double cardinality, not int32)|r697 r2s / unpacked catalog
singular-bool-to-repeated|z018|bool|repeated bool|armed|1123|singular VARINT 0/1|repeated VARINT 0/1|Python|singular-int32-to-repeated (bool cardinality, not int32)|i2rep / unpacked catalog
repeated-bool-to-singular|z019|repeated bool|bool|armed|1124|repeated VARINT 0/1|singular VARINT 0/1|Java|repeated-int32-to-singular (bool cardinality, not int32)|r697 r2s / unpacked catalog
singular-bytes-to-repeated|z020|bytes|repeated bytes|blob|1125|singular LEN bytes|repeated LEN bytes|Java|singular-int32-to-repeated (bytes cardinality, not int32)|i2rep / unpacked catalog
repeated-bytes-to-singular|z021|repeated bytes|bytes|blob|1126|repeated LEN bytes|singular LEN bytes|Rust|repeated-int32-to-singular (bytes cardinality, not int32)|r697 r2s / unpacked catalog
singular-enum-to-repeated|z022|Mode|repeated Mode|mode|1127|singular VARINT enum|repeated VARINT enum|Rust|singular-int32-to-repeated (enum cardinality, not int32)|i2rep / unpacked catalog
repeated-enum-to-singular|z023|repeated Mode|Mode|mode|1128|repeated VARINT enum|singular VARINT enum|Kotlin|repeated-int32-to-singular (enum cardinality, not int32)|r697 r2s / unpacked catalog
repeated-timestamp-to-singular|z024|repeated google.protobuf.Timestamp|google.protobuf.Timestamp|poured_at|1129|repeated LEN Timestamp|singular LEN Timestamp|Go|singular-timestamp-to-repeated (opposite cardinality)|stirep / unpacked catalog
repeated-duration-to-singular|z025|repeated google.protobuf.Duration|google.protobuf.Duration|hold|1130|repeated LEN Duration|singular LEN Duration|Python|singular-duration-to-repeated (opposite cardinality)|sdurep / unpacked catalog
repeated-any-to-singular|z026|repeated google.protobuf.Any|google.protobuf.Any|event|1131|repeated LEN Any type_url+value|singular LEN Any type_url+value|Java|singular-any-to-repeated (opposite cardinality)|sanrep / unpacked catalog
repeated-struct-to-singular|z027|repeated google.protobuf.Struct|google.protobuf.Struct|attrs|1132|repeated LEN Struct fields|singular LEN Struct fields|Rust|singular-struct-to-repeated (opposite cardinality)|sstrep / unpacked catalog
timezone-to-int64|z028|google.type.TimeZone|int64|zone|1133|LEN TimeZone id+version|VARINT int64|Go|timezone leftover mill (→int64, not string clone)|r787 leftover / r987 leftover
timezone-to-duration|z029|google.type.TimeZone|google.protobuf.Duration|zone|1134|LEN TimeZone id+version|LEN Duration|Python|timezone leftover mill (→duration, not string clone)|r787 leftover / r987 leftover
timezone-to-empty|z030|google.type.TimeZone|google.protobuf.Empty|zone|1135|LEN TimeZone id+version|LEN empty 0-length|Java|timezone leftover mill (→empty, not string clone)|r787 leftover / r987 leftover
timezone-to-timestamp|z031|google.type.TimeZone|google.protobuf.Timestamp|zone|1136|LEN TimeZone id+version|LEN Timestamp|Rust|timezone leftover mill (→timestamp, not string clone)|r787 leftover / r987 leftover
timezone-to-float|z032|google.type.TimeZone|float|zone|1137|LEN TimeZone id+version|FIXED32 float|Kotlin|timezone leftover mill (→float, not string clone)|r787 leftover / r987 leftover
timezone-to-uint32|z033|google.type.TimeZone|uint32|zone|1138|LEN TimeZone id+version|unsigned VARINT 32|TypeScript|timezone leftover mill (→uint32, not string clone)|r787 leftover / r987 leftover
timezone-to-bool|z034|google.type.TimeZone|bool|zone|1139|LEN TimeZone id+version|VARINT 0/1|C++|timezone leftover mill (→bool, not string clone)|r787 leftover / r987 leftover
dayofweek-to-bytes|z035|google.type.DayOfWeek|bytes|dow|1140|VARINT DayOfWeek enum|LEN bytes|Swift|dayofweek leftover mill (→bytes, not string clone)|r787 leftover / r987 leftover
dayofweek-to-sint32|z036|google.type.DayOfWeek|sint32|dow|1141|VARINT DayOfWeek enum|zigzag VARINT 32|Dart|dayofweek leftover mill (→sint32, not string clone)|r787 leftover / r987 leftover
dayofweek-to-uint32|z037|google.type.DayOfWeek|uint32|dow|1142|VARINT DayOfWeek enum|unsigned VARINT 32|C#|dayofweek leftover mill (→uint32, not string clone)|r787 leftover / r987 leftover
dayofweek-to-double|z038|google.type.DayOfWeek|double|dow|1143|VARINT DayOfWeek enum|FIXED64 double|Go|dayofweek leftover mill (→double, not string clone)|r787 leftover / r987 leftover
dayofweek-to-fixed64|z039|google.type.DayOfWeek|fixed64|dow|1144|VARINT DayOfWeek enum|FIXED64 unsigned|Python|dayofweek leftover mill (→fixed64, not string clone)|r787 leftover / r987 leftover
dayofweek-to-sint64|z040|google.type.DayOfWeek|sint64|dow|1145|VARINT DayOfWeek enum|zigzag VARINT 64|Java|dayofweek leftover mill (→sint64, not string clone)|r787 leftover / r987 leftover
dayofweek-to-empty|z041|google.type.DayOfWeek|google.protobuf.Empty|dow|1146|VARINT DayOfWeek enum|LEN empty 0-length|Rust|dayofweek leftover mill (→empty, not string clone)|r787 leftover / r987 leftover
month-to-bytes|z042|google.type.Month|bytes|cal|1147|VARINT Month enum|LEN bytes|Kotlin|month leftover mill (→bytes, not string clone)|r787 leftover / r987 leftover
month-to-bool|z043|google.type.Month|bool|cal|1148|VARINT Month enum|VARINT 0/1|TypeScript|month leftover mill (→bool, not string clone)|r787 leftover / r987 leftover
month-to-fixed32|z044|google.type.Month|fixed32|cal|1149|VARINT Month enum|FIXED32 unsigned|C++|month leftover mill (→fixed32, not string clone)|r787 leftover / r987 leftover
month-to-uint32|z045|google.type.Month|uint32|cal|1150|VARINT Month enum|unsigned VARINT 32|Swift|month leftover mill (→uint32, not string clone)|r787 leftover / r987 leftover
month-to-sint64|z046|google.type.Month|sint64|cal|1151|VARINT Month enum|zigzag VARINT 64|Dart|month leftover mill (→sint64, not string clone)|r787 leftover / r987 leftover
month-to-double|z047|google.type.Month|double|cal|1152|VARINT Month enum|FIXED64 double|C#|month leftover mill (→double, not string clone)|r787 leftover / r987 leftover
month-to-empty|z048|google.type.Month|google.protobuf.Empty|cal|1153|VARINT Month enum|LEN empty 0-length|Go|month leftover mill (→empty, not string clone)|r787 leftover / r987 leftover
fraction-to-int64|z049|google.type.Fraction|int64|ratio|1154|LEN Fraction num/den|VARINT int64|Python|fraction leftover mill (→int64, not string clone)|r787 leftover / r987 leftover
fraction-to-float|z050|google.type.Fraction|float|ratio|1155|LEN Fraction num/den|FIXED32 float|Java|fraction leftover mill (→float, not string clone)|r787 leftover / r987 leftover
fraction-to-struct|z051|google.type.Fraction|google.protobuf.Struct|ratio|1156|LEN Fraction num/den|LEN Struct fields|Rust|fraction leftover mill (→struct, not string clone)|r787 leftover / r987 leftover
fraction-to-empty|z052|google.type.Fraction|google.protobuf.Empty|ratio|1157|LEN Fraction num/den|LEN empty 0-length|Kotlin|fraction leftover mill (→empty, not string clone)|r787 leftover / r987 leftover
fraction-to-uint64|z053|google.type.Fraction|uint64|ratio|1158|LEN Fraction num/den|unsigned VARINT 64|TypeScript|fraction leftover mill (→uint64, not string clone)|r787 leftover / r987 leftover
fraction-to-sint32|z054|google.type.Fraction|sint32|ratio|1159|LEN Fraction num/den|zigzag VARINT 32|C++|fraction leftover mill (→sint32, not string clone)|r787 leftover / r987 leftover
fraction-to-bool|z055|google.type.Fraction|bool|ratio|1160|LEN Fraction num/den|VARINT 0/1|Swift|fraction leftover mill (→bool, not string clone)|r787 leftover / r987 leftover
localizedtext-to-any|z056|google.type.LocalizedText|google.protobuf.Any|label|1161|LEN LocalizedText text+lang|LEN Any type_url+value|Dart|localizedtext leftover mill (→any, not string clone)|r787 leftover / r987 leftover
localizedtext-to-duration|z057|google.type.LocalizedText|google.protobuf.Duration|label|1162|LEN LocalizedText text+lang|LEN Duration|C#|localizedtext leftover mill (→duration, not string clone)|r787 leftover / r987 leftover
localizedtext-to-int32|z058|google.type.LocalizedText|int32|label|1163|LEN LocalizedText text+lang|VARINT int32|Go|localizedtext leftover mill (→int32, not string clone)|r787 leftover / r987 leftover
localizedtext-to-empty|z059|google.type.LocalizedText|google.protobuf.Empty|label|1164|LEN LocalizedText text+lang|LEN empty 0-length|Python|localizedtext leftover mill (→empty, not string clone)|r787 leftover / r987 leftover
localizedtext-to-timestamp|z060|google.type.LocalizedText|google.protobuf.Timestamp|label|1165|LEN LocalizedText text+lang|LEN Timestamp|Java|localizedtext leftover mill (→timestamp, not string clone)|r787 leftover / r987 leftover
localizedtext-to-uint64|z061|google.type.LocalizedText|uint64|label|1166|LEN LocalizedText text+lang|unsigned VARINT 64|Rust|localizedtext leftover mill (→uint64, not string clone)|r787 leftover / r987 leftover
localizedtext-to-bool|z062|google.type.LocalizedText|bool|label|1167|LEN LocalizedText text+lang|VARINT 0/1|Kotlin|localizedtext leftover mill (→bool, not string clone)|r787 leftover / r987 leftover
timestamp-to-uint64-x|z063|google.protobuf.Timestamp|uint64|poured_at|1168|LEN Timestamp|unsigned VARINT 64|Go|timestamp→uint64 leftover WKT (not r787-r987 clone)|r787 leftover / r987 leftover
timestamp-to-sint32-x|z064|google.protobuf.Timestamp|sint32|poured_at|1169|LEN Timestamp|zigzag VARINT 32|Python|timestamp→sint32 leftover WKT (not r787-r987 clone)|r787 leftover / r987 leftover
timestamp-to-float-x|z065|google.protobuf.Timestamp|float|poured_at|1170|LEN Timestamp|FIXED32 float|Java|timestamp→float leftover WKT (not r787-r987 clone)|r787 leftover / r987 leftover
timestamp-to-bool-x|z066|google.protobuf.Timestamp|bool|poured_at|1171|LEN Timestamp|VARINT 0/1|Rust|timestamp→bool leftover WKT (not r787-r987 clone)|r787 leftover / r987 leftover
timestamp-to-sfixed64-x|z067|google.protobuf.Timestamp|sfixed64|poured_at|1172|LEN Timestamp|FIXED64 signed|Kotlin|timestamp→sfixed64 leftover WKT (not r787-r987 clone)|r787 leftover / r987 leftover
timestamp-to-fixed32-x|z068|google.protobuf.Timestamp|fixed32|poured_at|1173|LEN Timestamp|FIXED32 unsigned|TypeScript|timestamp→fixed32 leftover WKT (not r787-r987 clone)|r787 leftover / r987 leftover
duration-to-uint64-x|z069|google.protobuf.Duration|uint64|hold|1174|LEN Duration|unsigned VARINT 64|C++|duration→uint64 leftover WKT (not r787-r987 clone)|r787 leftover / r987 leftover
duration-to-bool-x|z070|google.protobuf.Duration|bool|hold|1175|LEN Duration|VARINT 0/1|Swift|duration→bool leftover WKT (not r787-r987 clone)|r787 leftover / r987 leftover
duration-to-sint32-x|z071|google.protobuf.Duration|sint32|hold|1176|LEN Duration|zigzag VARINT 32|Dart|duration→sint32 leftover WKT (not r787-r987 clone)|r787 leftover / r987 leftover
duration-to-float-x|z072|google.protobuf.Duration|float|hold|1177|LEN Duration|FIXED32 float|C#|duration→float leftover WKT (not r787-r987 clone)|r787 leftover / r987 leftover
duration-to-sfixed32-x|z073|google.protobuf.Duration|sfixed32|hold|1178|LEN Duration|FIXED32 signed|Go|duration→sfixed32 leftover WKT (not r787-r987 clone)|r787 leftover / r987 leftover
duration-to-bytes-x|z074|google.protobuf.Duration|bytes|hold|1179|LEN Duration|LEN bytes|Python|duration→bytes leftover WKT (not r787-r987 clone)|r787 leftover / r987 leftover
any-to-int32-x|z075|google.protobuf.Any|int32|event|1180|LEN Any type_url+value|VARINT int32|Java|any→int32 leftover WKT (not r787-r987 clone)|r787 leftover / r987 leftover
any-to-uint64-x|z076|google.protobuf.Any|uint64|event|1181|LEN Any type_url+value|unsigned VARINT 64|Rust|any→uint64 leftover WKT (not r787-r987 clone)|r787 leftover / r987 leftover
any-to-double-x|z077|google.protobuf.Any|double|event|1182|LEN Any type_url+value|FIXED64 double|Kotlin|any→double leftover WKT (not r787-r987 clone)|r787 leftover / r987 leftover
any-to-bool-x|z078|google.protobuf.Any|bool|event|1183|LEN Any type_url+value|VARINT 0/1|TypeScript|any→bool leftover WKT (not r787-r987 clone)|r787 leftover / r987 leftover
any-to-sint32-x|z079|google.protobuf.Any|sint32|event|1184|LEN Any type_url+value|zigzag VARINT 32|C++|any→sint32 leftover WKT (not r787-r987 clone)|r787 leftover / r987 leftover
any-to-fixed32-x|z080|google.protobuf.Any|fixed32|event|1185|LEN Any type_url+value|FIXED32 unsigned|Swift|any→fixed32 leftover WKT (not r787-r987 clone)|r787 leftover / r987 leftover
struct-to-uint32-x|z081|google.protobuf.Struct|uint32|attrs|1186|LEN Struct fields|unsigned VARINT 32|Dart|struct→uint32 leftover WKT (not r787-r987 clone)|r787 leftover / r987 leftover
struct-to-float-x|z082|google.protobuf.Struct|float|attrs|1187|LEN Struct fields|FIXED32 float|C#|struct→float leftover WKT (not r787-r987 clone)|r787 leftover / r987 leftover
struct-to-int32-x|z083|google.protobuf.Struct|int32|attrs|1188|LEN Struct fields|VARINT int32|Go|struct→int32 leftover WKT (not r787-r987 clone)|r787 leftover / r987 leftover
struct-to-bool-x|z084|google.protobuf.Struct|bool|attrs|1189|LEN Struct fields|VARINT 0/1|Python|struct→bool leftover WKT (not r787-r987 clone)|r787 leftover / r987 leftover
struct-to-uint64-x|z085|google.protobuf.Struct|uint64|attrs|1190|LEN Struct fields|unsigned VARINT 64|Java|struct→uint64 leftover WKT (not r787-r987 clone)|r787 leftover / r987 leftover
struct-to-sint64-x|z086|google.protobuf.Struct|sint64|attrs|1191|LEN Struct fields|zigzag VARINT 64|Rust|struct→sint64 leftover WKT (not r787-r987 clone)|r787 leftover / r987 leftover
empty-to-sint64-x|z087|google.protobuf.Empty|sint64|ack|1192|LEN empty 0-length|zigzag VARINT 64|Kotlin|empty→sint64 leftover WKT (not r787-r987 clone)|r787 leftover / r987 leftover
empty-to-fixed64-x|z088|google.protobuf.Empty|fixed64|ack|1193|LEN empty 0-length|FIXED64 unsigned|TypeScript|empty→fixed64 leftover WKT (not r787-r987 clone)|r787 leftover / r987 leftover
empty-to-uint32-x|z089|google.protobuf.Empty|uint32|ack|1194|LEN empty 0-length|unsigned VARINT 32|C++|empty→uint32 leftover WKT (not r787-r987 clone)|r787 leftover / r987 leftover
empty-to-sint32-x|z090|google.protobuf.Empty|sint32|ack|1195|LEN empty 0-length|zigzag VARINT 32|Swift|empty→sint32 leftover WKT (not r787-r987 clone)|r787 leftover / r987 leftover
empty-to-sfixed64-x|z091|google.protobuf.Empty|sfixed64|ack|1196|LEN empty 0-length|FIXED64 signed|Dart|empty→sfixed64 leftover WKT (not r787-r987 clone)|r787 leftover / r987 leftover
empty-to-float-x|z092|google.protobuf.Empty|float|ack|1197|LEN empty 0-length|FIXED32 float|C#|empty→float leftover WKT (not r787-r987 clone)|r787 leftover / r987 leftover
fieldmask-to-uint32-x|z093|google.protobuf.FieldMask|uint32|mask|1198|LEN FieldMask paths[]|unsigned VARINT 32|Go|fieldmask→uint32 leftover WKT (not r787-r987 clone)|r787 leftover / r987 leftover
fieldmask-to-float-x|z094|google.protobuf.FieldMask|float|mask|1199|LEN FieldMask paths[]|FIXED32 float|Python|fieldmask→float leftover WKT (not r787-r987 clone)|r787 leftover / r987 leftover
fieldmask-to-bool-x|z095|google.protobuf.FieldMask|bool|mask|1200|LEN FieldMask paths[]|VARINT 0/1|Java|fieldmask→bool leftover WKT (not r787-r987 clone)|r787 leftover / r987 leftover
fieldmask-to-uint64-x|z096|google.protobuf.FieldMask|uint64|mask|1201|LEN FieldMask paths[]|unsigned VARINT 64|Rust|fieldmask→uint64 leftover WKT (not r787-r987 clone)|r787 leftover / r987 leftover
fieldmask-to-sint32-x|z097|google.protobuf.FieldMask|sint32|mask|1202|LEN FieldMask paths[]|zigzag VARINT 32|Kotlin|fieldmask→sint32 leftover WKT (not r787-r987 clone)|r787 leftover / r987 leftover
fieldmask-to-double-x|z098|google.protobuf.FieldMask|double|mask|1203|LEN FieldMask paths[]|FIXED64 double|TypeScript|fieldmask→double leftover WKT (not r787-r987 clone)|r787 leftover / r987 leftover
listvalue-to-sint64-x|z099|google.protobuf.ListValue|sint64|tags|1204|LEN ListValue values[]|zigzag VARINT 64|C++|listvalue→sint64 leftover WKT (not r787-r987 clone)|r787 leftover / r987 leftover
listvalue-to-uint32-x|z100|google.protobuf.ListValue|uint32|tags|1205|LEN ListValue values[]|unsigned VARINT 32|Swift|listvalue→uint32 leftover WKT (not r787-r987 clone)|r787 leftover / r987 leftover
listvalue-to-bool-x|z101|google.protobuf.ListValue|bool|tags|1206|LEN ListValue values[]|VARINT 0/1|Dart|listvalue→bool leftover WKT (not r787-r987 clone)|r787 leftover / r987 leftover
listvalue-to-float-x|z102|google.protobuf.ListValue|float|tags|1207|LEN ListValue values[]|FIXED32 float|C#|listvalue→float leftover WKT (not r787-r987 clone)|r787 leftover / r987 leftover
listvalue-to-sint32-x|z103|google.protobuf.ListValue|sint32|tags|1208|LEN ListValue values[]|zigzag VARINT 32|Go|listvalue→sint32 leftover WKT (not r787-r987 clone)|r787 leftover / r987 leftover
listvalue-to-fixed64-x|z104|google.protobuf.ListValue|fixed64|tags|1209|LEN ListValue values[]|FIXED64 unsigned|Python|listvalue→fixed64 leftover WKT (not r787-r987 clone)|r787 leftover / r987 leftover
value-to-uint64-x|z105|google.protobuf.Value|uint64|kind|1210|LEN Value oneof|unsigned VARINT 64|Java|value→uint64 leftover WKT (not r787-r987 clone)|r787 leftover / r987 leftover
value-to-fixed32-x|z106|google.protobuf.Value|fixed32|kind|1211|LEN Value oneof|FIXED32 unsigned|Rust|value→fixed32 leftover WKT (not r787-r987 clone)|r787 leftover / r987 leftover
value-to-sint64-x|z107|google.protobuf.Value|sint64|kind|1212|LEN Value oneof|zigzag VARINT 64|Kotlin|value→sint64 leftover WKT (not r787-r987 clone)|r787 leftover / r987 leftover
value-to-uint32-x|z108|google.protobuf.Value|uint32|kind|1213|LEN Value oneof|unsigned VARINT 32|TypeScript|value→uint32 leftover WKT (not r787-r987 clone)|r787 leftover / r987 leftover
value-to-double-x|z109|google.protobuf.Value|double|kind|1214|LEN Value oneof|FIXED64 double|C++|value→double leftover WKT (not r787-r987 clone)|r787 leftover / r987 leftover
value-to-bytes-x|z110|google.protobuf.Value|bytes|kind|1215|LEN Value oneof|LEN bytes|Swift|value→bytes leftover WKT (not r787-r987 clone)|r787 leftover / r987 leftover
int32value-to-uint32value|z111|google.protobuf.Int32Value|google.protobuf.UInt32Value|count|1216|LEN Int32Value|LEN UInt32Value|Go|int32value→uint32value wrapper-to-wrapper (not unwrap catalog)|wrapper unwrap / r987 leftover
int32value-to-boolvalue|z112|google.protobuf.Int32Value|google.protobuf.BoolValue|count|1217|LEN Int32Value|LEN BoolValue|Python|int32value→boolvalue wrapper-to-wrapper (not unwrap catalog)|wrapper unwrap / r987 leftover
int32value-to-doublevalue|z113|google.protobuf.Int32Value|google.protobuf.DoubleValue|count|1218|LEN Int32Value|LEN DoubleValue|Java|int32value→doublevalue wrapper-to-wrapper (not unwrap catalog)|wrapper unwrap / r987 leftover
int64value-to-uint64value|z114|google.protobuf.Int64Value|google.protobuf.UInt64Value|count|1219|LEN Int64Value|LEN UInt64Value|Rust|int64value→uint64value wrapper-to-wrapper (not unwrap catalog)|wrapper unwrap / r987 leftover
int64value-to-boolvalue|z115|google.protobuf.Int64Value|google.protobuf.BoolValue|count|1220|LEN Int64Value|LEN BoolValue|Kotlin|int64value→boolvalue wrapper-to-wrapper (not unwrap catalog)|wrapper unwrap / r987 leftover
int64value-to-floatvalue|z116|google.protobuf.Int64Value|google.protobuf.FloatValue|count|1221|LEN Int64Value|LEN FloatValue|TypeScript|int64value→floatvalue wrapper-to-wrapper (not unwrap catalog)|wrapper unwrap / r987 leftover
uint32value-to-uint64value|z117|google.protobuf.UInt32Value|google.protobuf.UInt64Value|port|1222|LEN UInt32Value|LEN UInt64Value|C++|uint32value→uint64value wrapper-to-wrapper (not unwrap catalog)|wrapper unwrap / r987 leftover
uint32value-to-stringvalue|z118|google.protobuf.UInt32Value|google.protobuf.StringValue|port|1223|LEN UInt32Value|LEN StringValue|Swift|uint32value→stringvalue wrapper-to-wrapper (not unwrap catalog)|wrapper unwrap / r987 leftover
uint32value-to-bytesvalue|z119|google.protobuf.UInt32Value|google.protobuf.BytesValue|port|1224|LEN UInt32Value|LEN BytesValue|Dart|uint32value→bytesvalue wrapper-to-wrapper (not unwrap catalog)|wrapper unwrap / r987 leftover
uint64value-to-stringvalue|z120|google.protobuf.UInt64Value|google.protobuf.StringValue|hash|1225|LEN UInt64Value|LEN StringValue|C#|uint64value→stringvalue wrapper-to-wrapper (not unwrap catalog)|wrapper unwrap / r987 leftover
uint64value-to-bytesvalue|z121|google.protobuf.UInt64Value|google.protobuf.BytesValue|hash|1226|LEN UInt64Value|LEN BytesValue|Go|uint64value→bytesvalue wrapper-to-wrapper (not unwrap catalog)|wrapper unwrap / r987 leftover
uint64value-to-boolvalue|z122|google.protobuf.UInt64Value|google.protobuf.BoolValue|hash|1227|LEN UInt64Value|LEN BoolValue|Python|uint64value→boolvalue wrapper-to-wrapper (not unwrap catalog)|wrapper unwrap / r987 leftover
floatvalue-to-boolvalue|z123|google.protobuf.FloatValue|google.protobuf.BoolValue|temp_c|1228|LEN FloatValue|LEN BoolValue|Java|floatvalue→boolvalue wrapper-to-wrapper (not unwrap catalog)|wrapper unwrap / r987 leftover
floatvalue-to-uint32value|z124|google.protobuf.FloatValue|google.protobuf.UInt32Value|temp_c|1229|LEN FloatValue|LEN UInt32Value|Rust|floatvalue→uint32value wrapper-to-wrapper (not unwrap catalog)|wrapper unwrap / r987 leftover
doublevalue-to-bytesvalue|z125|google.protobuf.DoubleValue|google.protobuf.BytesValue|peak|1230|LEN DoubleValue|LEN BytesValue|Kotlin|doublevalue→bytesvalue wrapper-to-wrapper (not unwrap catalog)|wrapper unwrap / r987 leftover
doublevalue-to-boolvalue|z126|google.protobuf.DoubleValue|google.protobuf.BoolValue|peak|1231|LEN DoubleValue|LEN BoolValue|TypeScript|doublevalue→boolvalue wrapper-to-wrapper (not unwrap catalog)|wrapper unwrap / r987 leftover
boolvalue-to-int64value|z127|google.protobuf.BoolValue|google.protobuf.Int64Value|ok|1232|LEN BoolValue|LEN Int64Value|C++|boolvalue→int64value wrapper-to-wrapper (not unwrap catalog)|wrapper unwrap / r987 leftover
boolvalue-to-uint32value|z128|google.protobuf.BoolValue|google.protobuf.UInt32Value|ok|1233|LEN BoolValue|LEN UInt32Value|Swift|boolvalue→uint32value wrapper-to-wrapper (not unwrap catalog)|wrapper unwrap / r987 leftover
stringvalue-to-int64value|z129|google.protobuf.StringValue|google.protobuf.Int64Value|sku|1234|LEN StringValue|LEN Int64Value|Dart|stringvalue→int64value wrapper-to-wrapper (not unwrap catalog)|wrapper unwrap / r987 leftover
stringvalue-to-uint64value|z130|google.protobuf.StringValue|google.protobuf.UInt64Value|sku|1235|LEN StringValue|LEN UInt64Value|C#|stringvalue→uint64value wrapper-to-wrapper (not unwrap catalog)|wrapper unwrap / r987 leftover
stringvalue-to-floatvalue|z131|google.protobuf.StringValue|google.protobuf.FloatValue|sku|1236|LEN StringValue|LEN FloatValue|Go|stringvalue→floatvalue wrapper-to-wrapper (not unwrap catalog)|wrapper unwrap / r987 leftover
bytesvalue-to-int32value|z132|google.protobuf.BytesValue|google.protobuf.Int32Value|blob|1237|LEN BytesValue|LEN Int32Value|Python|bytesvalue→int32value wrapper-to-wrapper (not unwrap catalog)|wrapper unwrap / r987 leftover
bytesvalue-to-int64value|z133|google.protobuf.BytesValue|google.protobuf.Int64Value|blob|1238|LEN BytesValue|LEN Int64Value|Java|bytesvalue→int64value wrapper-to-wrapper (not unwrap catalog)|wrapper unwrap / r987 leftover
bytesvalue-to-boolvalue|z134|google.protobuf.BytesValue|google.protobuf.BoolValue|blob|1239|LEN BytesValue|LEN BoolValue|Rust|bytesvalue→boolvalue wrapper-to-wrapper (not unwrap catalog)|wrapper unwrap / r987 leftover
oneof-int32-to-uint32|z135|int32|uint32|tap_n|1240|VARINT int32|unsigned VARINT 32|Go|oneof int32→uint32 (arm type, not scalar clone)|r787 leftover / r987 leftover
oneof-int32-to-uint64|z136|int32|uint64|tap_n|1241|VARINT int32|unsigned VARINT 64|Python|oneof int32→uint64 (arm type, not scalar clone)|r787 leftover / r987 leftover
oneof-int32-to-sint32|z137|int32|sint32|tap_n|1242|VARINT int32|zigzag VARINT 32|Java|oneof int32→sint32 (arm type, not scalar clone)|r787 leftover / r987 leftover
oneof-int32-to-fixed32|z138|int32|fixed32|tap_n|1243|VARINT int32|FIXED32 unsigned|Rust|oneof int32→fixed32 (arm type, not scalar clone)|r787 leftover / r987 leftover
oneof-int64-to-int32|z139|int64|int32|seq|1244|VARINT int64|VARINT int32|Kotlin|oneof int64→int32 (arm type, not scalar clone)|r787 leftover / r987 leftover
oneof-int64-to-uint32|z140|int64|uint32|seq|1245|VARINT int64|unsigned VARINT 32|TypeScript|oneof int64→uint32 (arm type, not scalar clone)|r787 leftover / r987 leftover
oneof-int64-to-sint64|z141|int64|sint64|seq|1246|VARINT int64|zigzag VARINT 64|C++|oneof int64→sint64 (arm type, not scalar clone)|r787 leftover / r987 leftover
oneof-int64-to-fixed64|z142|int64|fixed64|seq|1247|VARINT int64|FIXED64 unsigned|Swift|oneof int64→fixed64 (arm type, not scalar clone)|r787 leftover / r987 leftover
oneof-uint32-to-int32|z143|uint32|int32|port|1248|unsigned VARINT 32|VARINT int32|Dart|oneof uint32→int32 (arm type, not scalar clone)|r787 leftover / r987 leftover
oneof-uint32-to-uint64|z144|uint32|uint64|port|1249|unsigned VARINT 32|unsigned VARINT 64|C#|oneof uint32→uint64 (arm type, not scalar clone)|r787 leftover / r987 leftover
oneof-uint32-to-bool|z145|uint32|bool|port|1250|unsigned VARINT 32|VARINT 0/1|Go|oneof uint32→bool (arm type, not scalar clone)|r787 leftover / r987 leftover
oneof-uint32-to-bytes|z146|uint32|bytes|port|1251|unsigned VARINT 32|LEN bytes|Python|oneof uint32→bytes (arm type, not scalar clone)|r787 leftover / r987 leftover
oneof-uint64-to-int32|z147|uint64|int32|hash|1252|unsigned VARINT 64|VARINT int32|Java|oneof uint64→int32 (arm type, not scalar clone)|r787 leftover / r987 leftover
oneof-uint64-to-sint64|z148|uint64|sint64|hash|1253|unsigned VARINT 64|zigzag VARINT 64|Rust|oneof uint64→sint64 (arm type, not scalar clone)|r787 leftover / r987 leftover
oneof-uint64-to-fixed64|z149|uint64|fixed64|hash|1254|unsigned VARINT 64|FIXED64 unsigned|Kotlin|oneof uint64→fixed64 (arm type, not scalar clone)|r787 leftover / r987 leftover
oneof-uint64-to-bool|z150|uint64|bool|hash|1255|unsigned VARINT 64|VARINT 0/1|TypeScript|oneof uint64→bool (arm type, not scalar clone)|r787 leftover / r987 leftover
oneof-sint32-to-sint64|z151|sint32|sint64|delta|1256|zigzag VARINT 32|zigzag VARINT 64|C++|oneof sint32→sint64 (arm type, not scalar clone)|r787 leftover / r987 leftover
oneof-sint32-to-float|z152|sint32|float|delta|1257|zigzag VARINT 32|FIXED32 float|Swift|oneof sint32→float (arm type, not scalar clone)|r787 leftover / r987 leftover
oneof-sint32-to-bytes|z153|sint32|bytes|delta|1258|zigzag VARINT 32|LEN bytes|Dart|oneof sint32→bytes (arm type, not scalar clone)|r787 leftover / r987 leftover
oneof-sint32-to-bool|z154|sint32|bool|delta|1259|zigzag VARINT 32|VARINT 0/1|C#|oneof sint32→bool (arm type, not scalar clone)|r787 leftover / r987 leftover
oneof-sint64-to-int64|z155|sint64|int64|delta|1260|zigzag VARINT 64|VARINT int64|Go|oneof sint64→int64 (arm type, not scalar clone)|r787 leftover / r987 leftover
oneof-sint64-to-uint64|z156|sint64|uint64|delta|1261|zigzag VARINT 64|unsigned VARINT 64|Python|oneof sint64→uint64 (arm type, not scalar clone)|r787 leftover / r987 leftover
oneof-sint64-to-double|z157|sint64|double|delta|1262|zigzag VARINT 64|FIXED64 double|Java|oneof sint64→double (arm type, not scalar clone)|r787 leftover / r987 leftover
oneof-sint64-to-string|z158|sint64|string|delta|1263|zigzag VARINT 64|LEN utf8|Rust|oneof sint64→string (arm type, not scalar clone)|r787 leftover / r987 leftover
oneof-fixed32-to-fixed64|z159|fixed32|fixed64|crc|1264|FIXED32 unsigned|FIXED64 unsigned|Kotlin|oneof fixed32→fixed64 (arm type, not scalar clone)|r787 leftover / r987 leftover
oneof-fixed32-to-float|z160|fixed32|float|crc|1265|FIXED32 unsigned|FIXED32 float|TypeScript|oneof fixed32→float (arm type, not scalar clone)|r787 leftover / r987 leftover
oneof-fixed32-to-bytes|z161|fixed32|bytes|crc|1266|FIXED32 unsigned|LEN bytes|C++|oneof fixed32→bytes (arm type, not scalar clone)|r787 leftover / r987 leftover
oneof-fixed32-to-bool|z162|fixed32|bool|crc|1267|FIXED32 unsigned|VARINT 0/1|Swift|oneof fixed32→bool (arm type, not scalar clone)|r787 leftover / r987 leftover
oneof-fixed64-to-double|z163|fixed64|double|hash|1268|FIXED64 unsigned|FIXED64 double|Dart|oneof fixed64→double (arm type, not scalar clone)|r787 leftover / r987 leftover
oneof-fixed64-to-int64|z164|fixed64|int64|hash|1269|FIXED64 unsigned|VARINT int64|C#|oneof fixed64→int64 (arm type, not scalar clone)|r787 leftover / r987 leftover
oneof-fixed64-to-bytes|z165|fixed64|bytes|hash|1270|FIXED64 unsigned|LEN bytes|Go|oneof fixed64→bytes (arm type, not scalar clone)|r787 leftover / r987 leftover
oneof-fixed64-to-bool|z166|fixed64|bool|hash|1271|FIXED64 unsigned|VARINT 0/1|Python|oneof fixed64→bool (arm type, not scalar clone)|r787 leftover / r987 leftover
oneof-float-to-int32|z167|float|int32|temp_c|1272|FIXED32 float|VARINT int32|Java|oneof float→int32 (arm type, not scalar clone)|r787 leftover / r987 leftover
oneof-float-to-uint32|z168|float|uint32|temp_c|1273|FIXED32 float|unsigned VARINT 32|Rust|oneof float→uint32 (arm type, not scalar clone)|r787 leftover / r987 leftover
oneof-float-to-bool|z169|float|bool|temp_c|1274|FIXED32 float|VARINT 0/1|Kotlin|oneof float→bool (arm type, not scalar clone)|r787 leftover / r987 leftover
oneof-float-to-bytes|z170|float|bytes|temp_c|1275|FIXED32 float|LEN bytes|TypeScript|oneof float→bytes (arm type, not scalar clone)|r787 leftover / r987 leftover
oneof-double-to-int64|z171|double|int64|peak|1276|FIXED64 double|VARINT int64|C++|oneof double→int64 (arm type, not scalar clone)|r787 leftover / r987 leftover
oneof-double-to-uint64|z172|double|uint64|peak|1277|FIXED64 double|unsigned VARINT 64|Swift|oneof double→uint64 (arm type, not scalar clone)|r787 leftover / r987 leftover
oneof-double-to-bool|z173|double|bool|peak|1278|FIXED64 double|VARINT 0/1|Dart|oneof double→bool (arm type, not scalar clone)|r787 leftover / r987 leftover
oneof-double-to-bytes|z174|double|bytes|peak|1279|FIXED64 double|LEN bytes|C#|oneof double→bytes (arm type, not scalar clone)|r787 leftover / r987 leftover
oneof-bool-to-int32|z175|bool|int32|armed|1280|VARINT 0/1|VARINT int32|Go|oneof bool→int32 (arm type, not scalar clone)|r787 leftover / r987 leftover
oneof-bool-to-uint64|z176|bool|uint64|armed|1281|VARINT 0/1|unsigned VARINT 64|Python|oneof bool→uint64 (arm type, not scalar clone)|r787 leftover / r987 leftover
oneof-bool-to-float|z177|bool|float|armed|1282|VARINT 0/1|FIXED32 float|Java|oneof bool→float (arm type, not scalar clone)|r787 leftover / r987 leftover
oneof-bool-to-string|z178|bool|string|armed|1283|VARINT 0/1|LEN utf8|Rust|oneof bool→string (arm type, not scalar clone)|r787 leftover / r987 leftover
oneof-string-to-uint32|z179|string|uint32|sku|1284|LEN utf8|unsigned VARINT 32|Kotlin|oneof string→uint32 (arm type, not scalar clone)|r787 leftover / r987 leftover
oneof-string-to-int64|z180|string|int64|sku|1285|LEN utf8|VARINT int64|TypeScript|oneof string→int64 (arm type, not scalar clone)|r787 leftover / r987 leftover
oneof-string-to-float|z181|string|float|sku|1286|LEN utf8|FIXED32 float|C++|oneof string→float (arm type, not scalar clone)|r787 leftover / r987 leftover
oneof-string-to-bool|z182|string|bool|sku|1287|LEN utf8|VARINT 0/1|Swift|oneof string→bool (arm type, not scalar clone)|r787 leftover / r987 leftover
oneof-bytes-to-uint32|z183|bytes|uint32|blob|1288|LEN bytes|unsigned VARINT 32|Dart|oneof bytes→uint32 (arm type, not scalar clone)|r787 leftover / r987 leftover
oneof-bytes-to-int64|z184|bytes|int64|blob|1289|LEN bytes|VARINT int64|C#|oneof bytes→int64 (arm type, not scalar clone)|r787 leftover / r987 leftover
oneof-bytes-to-float|z185|bytes|float|blob|1290|LEN bytes|FIXED32 float|Go|oneof bytes→float (arm type, not scalar clone)|r787 leftover / r987 leftover
oneof-bytes-to-bool|z186|bytes|bool|blob|1291|LEN bytes|VARINT 0/1|Python|oneof bytes→bool (arm type, not scalar clone)|r787 leftover / r987 leftover
map-value-int32-to-uint32|z187|int32|uint32|taps|1292|value VARINT int32|value unsigned VARINT 32|Go|map value int32→uint32 (not map-key ban)|map-key ban / r787 leftover
map-value-int32-to-uint64|z188|int32|uint64|taps|1293|value VARINT int32|value unsigned VARINT 64|Python|map value int32→uint64 (not map-key ban)|map-key ban / r787 leftover
map-value-int32-to-sint32|z189|int32|sint32|taps|1294|value VARINT int32|value zigzag VARINT 32|Java|map value int32→sint32 (not map-key ban)|map-key ban / r787 leftover
map-value-int32-to-float|z190|int32|float|taps|1295|value VARINT int32|value FIXED32 float|Rust|map value int32→float (not map-key ban)|map-key ban / r787 leftover
map-value-int64-to-uint32|z191|int64|uint32|seqs|1296|value VARINT int64|value unsigned VARINT 32|Kotlin|map value int64→uint32 (not map-key ban)|map-key ban / r787 leftover
map-value-int64-to-sint64|z192|int64|sint64|seqs|1297|value VARINT int64|value zigzag VARINT 64|TypeScript|map value int64→sint64 (not map-key ban)|map-key ban / r787 leftover
map-value-int64-to-fixed64|z193|int64|fixed64|seqs|1298|value VARINT int64|value FIXED64 unsigned|C++|map value int64→fixed64 (not map-key ban)|map-key ban / r787 leftover
map-value-int64-to-bool|z194|int64|bool|seqs|1299|value VARINT int64|value VARINT 0/1|Swift|map value int64→bool (not map-key ban)|map-key ban / r787 leftover
map-value-uint32-to-int64|z195|uint32|int64|ports|1300|value unsigned VARINT 32|value VARINT int64|Dart|map value uint32→int64 (not map-key ban)|map-key ban / r787 leftover
map-value-uint32-to-sint32|z196|uint32|sint32|ports|1301|value unsigned VARINT 32|value zigzag VARINT 32|C#|map value uint32→sint32 (not map-key ban)|map-key ban / r787 leftover
map-value-uint32-to-float|z197|uint32|float|ports|1302|value unsigned VARINT 32|value FIXED32 float|Go|map value uint32→float (not map-key ban)|map-key ban / r787 leftover
map-value-uint32-to-bool|z198|uint32|bool|ports|1303|value unsigned VARINT 32|value VARINT 0/1|Python|map value uint32→bool (not map-key ban)|map-key ban / r787 leftover
map-value-uint64-to-int32|z199|uint64|int32|hashes|1304|value unsigned VARINT 64|value VARINT int32|Java|map value uint64→int32 (not map-key ban)|map-key ban / r787 leftover
map-value-uint64-to-sint32|z200|uint64|sint32|hashes|1305|value unsigned VARINT 64|value zigzag VARINT 32|Rust|map value uint64→sint32 (not map-key ban)|map-key ban / r787 leftover
map-value-uint64-to-float|z201|uint64|float|hashes|1306|value unsigned VARINT 64|value FIXED32 float|Kotlin|map value uint64→float (not map-key ban)|map-key ban / r787 leftover
map-value-uint64-to-bool|z202|uint64|bool|hashes|1307|value unsigned VARINT 64|value VARINT 0/1|TypeScript|map value uint64→bool (not map-key ban)|map-key ban / r787 leftover
map-value-sint32-to-uint32|z203|sint32|uint32|deltas|1308|value zigzag VARINT 32|value unsigned VARINT 32|C++|map value sint32→uint32 (not map-key ban)|map-key ban / r787 leftover
map-value-sint32-to-int64|z204|sint32|int64|deltas|1309|value zigzag VARINT 32|value VARINT int64|Swift|map value sint32→int64 (not map-key ban)|map-key ban / r787 leftover
map-value-sint32-to-float|z205|sint32|float|deltas|1310|value zigzag VARINT 32|value FIXED32 float|Dart|map value sint32→float (not map-key ban)|map-key ban / r787 leftover
map-value-sint32-to-bytes|z206|sint32|bytes|deltas|1311|value zigzag VARINT 32|value LEN bytes|C#|map value sint32→bytes (not map-key ban)|map-key ban / r787 leftover
map-value-sint64-to-uint32|z207|sint64|uint32|deltas|1312|value zigzag VARINT 64|value unsigned VARINT 32|Go|map value sint64→uint32 (not map-key ban)|map-key ban / r787 leftover
map-value-sint64-to-float|z208|sint64|float|deltas|1313|value zigzag VARINT 64|value FIXED32 float|Python|map value sint64→float (not map-key ban)|map-key ban / r787 leftover
map-value-sint64-to-bool|z209|sint64|bool|deltas|1314|value zigzag VARINT 64|value VARINT 0/1|Java|map value sint64→bool (not map-key ban)|map-key ban / r787 leftover
map-value-sint64-to-bytes|z210|sint64|bytes|deltas|1315|value zigzag VARINT 64|value LEN bytes|Rust|map value sint64→bytes (not map-key ban)|map-key ban / r787 leftover
map-value-fixed32-to-int32|z211|fixed32|int32|crcs|1316|value FIXED32 unsigned|value VARINT int32|Kotlin|map value fixed32→int32 (not map-key ban)|map-key ban / r787 leftover
map-value-fixed32-to-uint64|z212|fixed32|uint64|crcs|1317|value FIXED32 unsigned|value unsigned VARINT 64|TypeScript|map value fixed32→uint64 (not map-key ban)|map-key ban / r787 leftover
map-value-fixed32-to-bool|z213|fixed32|bool|crcs|1318|value FIXED32 unsigned|value VARINT 0/1|C++|map value fixed32→bool (not map-key ban)|map-key ban / r787 leftover
map-value-fixed32-to-bytes|z214|fixed32|bytes|crcs|1319|value FIXED32 unsigned|value LEN bytes|Swift|map value fixed32→bytes (not map-key ban)|map-key ban / r787 leftover
map-value-fixed64-to-int32|z215|fixed64|int32|hashes|1320|value FIXED64 unsigned|value VARINT int32|Dart|map value fixed64→int32 (not map-key ban)|map-key ban / r787 leftover
map-value-fixed64-to-uint32|z216|fixed64|uint32|hashes|1321|value FIXED64 unsigned|value unsigned VARINT 32|C#|map value fixed64→uint32 (not map-key ban)|map-key ban / r787 leftover
map-value-fixed64-to-bool|z217|fixed64|bool|hashes|1322|value FIXED64 unsigned|value VARINT 0/1|Go|map value fixed64→bool (not map-key ban)|map-key ban / r787 leftover
map-value-fixed64-to-int64|z218|fixed64|int64|hashes|1323|value FIXED64 unsigned|value VARINT int64|Python|map value fixed64→int64 (not map-key ban)|map-key ban / r787 leftover
map-value-float-to-uint32|z219|float|uint32|temps|1324|value FIXED32 float|value unsigned VARINT 32|Java|map value float→uint32 (not map-key ban)|map-key ban / r787 leftover
map-value-float-to-int64|z220|float|int64|temps|1325|value FIXED32 float|value VARINT int64|Rust|map value float→int64 (not map-key ban)|map-key ban / r787 leftover
map-value-float-to-bool|z221|float|bool|temps|1326|value FIXED32 float|value VARINT 0/1|Kotlin|map value float→bool (not map-key ban)|map-key ban / r787 leftover
map-value-float-to-bytes|z222|float|bytes|temps|1327|value FIXED32 float|value LEN bytes|TypeScript|map value float→bytes (not map-key ban)|map-key ban / r787 leftover
map-value-double-to-uint32|z223|double|uint32|peaks|1328|value FIXED64 double|value unsigned VARINT 32|C++|map value double→uint32 (not map-key ban)|map-key ban / r787 leftover
map-value-double-to-int32|z224|double|int32|peaks|1329|value FIXED64 double|value VARINT int32|Swift|map value double→int32 (not map-key ban)|map-key ban / r787 leftover
map-value-double-to-bool|z225|double|bool|peaks|1330|value FIXED64 double|value VARINT 0/1|Dart|map value double→bool (not map-key ban)|map-key ban / r787 leftover
map-value-double-to-bytes|z226|double|bytes|peaks|1331|value FIXED64 double|value LEN bytes|C#|map value double→bytes (not map-key ban)|map-key ban / r787 leftover
map-value-bool-to-uint32|z227|bool|uint32|flags|1332|value VARINT 0/1|value unsigned VARINT 32|Go|map value bool→uint32 (not map-key ban)|map-key ban / r787 leftover
map-value-bool-to-int64|z228|bool|int64|flags|1333|value VARINT 0/1|value VARINT int64|Python|map value bool→int64 (not map-key ban)|map-key ban / r787 leftover
map-value-bool-to-float|z229|bool|float|flags|1334|value VARINT 0/1|value FIXED32 float|Java|map value bool→float (not map-key ban)|map-key ban / r787 leftover
map-value-bool-to-string|z230|bool|string|flags|1335|value VARINT 0/1|value LEN utf8|Rust|map value bool→string (not map-key ban)|map-key ban / r787 leftover
map-value-string-to-uint32|z231|string|uint32|skus|1336|value LEN utf8|value unsigned VARINT 32|Kotlin|map value string→uint32 (not map-key ban)|map-key ban / r787 leftover
map-value-string-to-int64|z232|string|int64|skus|1337|value LEN utf8|value VARINT int64|TypeScript|map value string→int64 (not map-key ban)|map-key ban / r787 leftover
map-value-string-to-float|z233|string|float|skus|1338|value LEN utf8|value FIXED32 float|C++|map value string→float (not map-key ban)|map-key ban / r787 leftover
map-value-string-to-bool|z234|string|bool|skus|1339|value LEN utf8|value VARINT 0/1|Swift|map value string→bool (not map-key ban)|map-key ban / r787 leftover
map-value-bytes-to-uint32|z235|bytes|uint32|blobs|1340|value LEN bytes|value unsigned VARINT 32|Dart|map value bytes→uint32 (not map-key ban)|map-key ban / r787 leftover
map-value-bytes-to-int64|z236|bytes|int64|blobs|1341|value LEN bytes|value VARINT int64|C#|map value bytes→int64 (not map-key ban)|map-key ban / r787 leftover
map-value-bytes-to-float|z237|bytes|float|blobs|1342|value LEN bytes|value FIXED32 float|Go|map value bytes→float (not map-key ban)|map-key ban / r787 leftover
map-value-bytes-to-bool|z238|bytes|bool|blobs|1343|value LEN bytes|value VARINT 0/1|Python|map value bytes→bool (not map-key ban)|map-key ban / r787 leftover
proto2-required-int32-to-int64|z239|int32|int64|tap_n|2|VARINT int32|VARINT int64|Go|proto2 required int32→int64 TYPE (not optional/required drop)|r629 optional drop / r635 legacy-required
proto2-required-int32-to-uint32|z240|int32|uint32|tap_n|3|VARINT int32|unsigned VARINT 32|Python|proto2 required int32→uint32 TYPE (not optional/required drop)|r629 optional drop / r635 legacy-required
proto2-required-int32-to-bytes|z241|int32|bytes|tap_n|4|VARINT int32|LEN bytes|Java|proto2 required int32→bytes TYPE (not optional/required drop)|r629 optional drop / r635 legacy-required
proto2-required-int64-to-uint32|z242|int64|uint32|seq|5|VARINT int64|unsigned VARINT 32|Rust|proto2 required int64→uint32 TYPE (not optional/required drop)|r629 optional drop / r635 legacy-required
proto2-required-int64-to-fixed64|z243|int64|fixed64|seq|6|VARINT int64|FIXED64 unsigned|Kotlin|proto2 required int64→fixed64 TYPE (not optional/required drop)|r629 optional drop / r635 legacy-required
proto2-required-int64-to-bool|z244|int64|bool|seq|7|VARINT int64|VARINT 0/1|TypeScript|proto2 required int64→bool TYPE (not optional/required drop)|r629 optional drop / r635 legacy-required
proto2-required-uint32-to-fixed32|z245|uint32|fixed32|port|8|unsigned VARINT 32|FIXED32 unsigned|C++|proto2 required uint32→fixed32 TYPE (not optional/required drop)|r629 optional drop / r635 legacy-required
proto2-required-uint32-to-string|z246|uint32|string|port|9|unsigned VARINT 32|LEN utf8|Swift|proto2 required uint32→string TYPE (not optional/required drop)|r629 optional drop / r635 legacy-required
proto2-required-uint64-to-fixed64|z247|uint64|fixed64|hash|2|unsigned VARINT 64|FIXED64 unsigned|Dart|proto2 required uint64→fixed64 TYPE (not optional/required drop)|r629 optional drop / r635 legacy-required
proto2-required-sint32-to-sint64|z248|sint32|sint64|delta|3|zigzag VARINT 32|zigzag VARINT 64|C#|proto2 required sint32→sint64 TYPE (not optional/required drop)|r629 optional drop / r635 legacy-required
proto2-required-sint32-to-bytes|z249|sint32|bytes|delta|4|zigzag VARINT 32|LEN bytes|Go|proto2 required sint32→bytes TYPE (not optional/required drop)|r629 optional drop / r635 legacy-required
proto2-required-sint64-to-fixed64|z250|sint64|fixed64|delta|5|zigzag VARINT 64|FIXED64 unsigned|Python|proto2 required sint64→fixed64 TYPE (not optional/required drop)|r629 optional drop / r635 legacy-required
proto2-required-fixed32-to-int64|z251|fixed32|int64|crc|6|FIXED32 unsigned|VARINT int64|Java|proto2 required fixed32→int64 TYPE (not optional/required drop)|r629 optional drop / r635 legacy-required
proto2-required-fixed64-to-int32|z252|fixed64|int32|hash|7|FIXED64 unsigned|VARINT int32|Rust|proto2 required fixed64→int32 TYPE (not optional/required drop)|r629 optional drop / r635 legacy-required
proto2-required-sfixed32-to-sfixed64|z253|sfixed32|sfixed64|crc|8|FIXED32 signed|FIXED64 signed|Kotlin|proto2 required sfixed32→sfixed64 TYPE (not optional/required drop)|r629 optional drop / r635 legacy-required
proto2-required-float-to-int32|z254|float|int32|temp_c|9|FIXED32 float|VARINT int32|TypeScript|proto2 required float→int32 TYPE (not optional/required drop)|r629 optional drop / r635 legacy-required
proto2-required-double-to-int64|z255|double|int64|peak|2|FIXED64 double|VARINT int64|C++|proto2 required double→int64 TYPE (not optional/required drop)|r629 optional drop / r635 legacy-required
proto2-required-bool-to-bytes|z256|bool|bytes|armed|3|VARINT 0/1|LEN bytes|Swift|proto2 required bool→bytes TYPE (not optional/required drop)|r629 optional drop / r635 legacy-required
proto2-optional-int32-to-int64|z257|int32|int64|tap_n|4|VARINT int32|VARINT int64|Dart|proto2 optional int32→int64 TYPE (not optional/required drop)|r629 optional drop / r635 legacy-required
proto2-optional-int32-to-uint32|z258|int32|uint32|tap_n|5|VARINT int32|unsigned VARINT 32|C#|proto2 optional int32→uint32 TYPE (not optional/required drop)|r629 optional drop / r635 legacy-required
proto2-optional-int32-to-bytes|z259|int32|bytes|tap_n|6|VARINT int32|LEN bytes|Go|proto2 optional int32→bytes TYPE (not optional/required drop)|r629 optional drop / r635 legacy-required
proto2-optional-int64-to-uint32|z260|int64|uint32|seq|7|VARINT int64|unsigned VARINT 32|Python|proto2 optional int64→uint32 TYPE (not optional/required drop)|r629 optional drop / r635 legacy-required
proto2-optional-int64-to-fixed64|z261|int64|fixed64|seq|8|VARINT int64|FIXED64 unsigned|Java|proto2 optional int64→fixed64 TYPE (not optional/required drop)|r629 optional drop / r635 legacy-required
proto2-optional-uint32-to-fixed32|z262|uint32|fixed32|port|9|unsigned VARINT 32|FIXED32 unsigned|Rust|proto2 optional uint32→fixed32 TYPE (not optional/required drop)|r629 optional drop / r635 legacy-required
proto2-optional-uint64-to-string|z263|uint64|string|hash|2|unsigned VARINT 64|LEN utf8|Kotlin|proto2 optional uint64→string TYPE (not optional/required drop)|r629 optional drop / r635 legacy-required
proto2-optional-sint32-to-sint64|z264|sint32|sint64|delta|3|zigzag VARINT 32|zigzag VARINT 64|TypeScript|proto2 optional sint32→sint64 TYPE (not optional/required drop)|r629 optional drop / r635 legacy-required
proto2-optional-sint64-to-string|z265|sint64|string|delta|4|zigzag VARINT 64|LEN utf8|C++|proto2 optional sint64→string TYPE (not optional/required drop)|r629 optional drop / r635 legacy-required
proto2-optional-fixed64-to-double|z266|fixed64|double|hash|5|FIXED64 unsigned|FIXED64 double|Swift|proto2 optional fixed64→double TYPE (not optional/required drop)|r629 optional drop / r635 legacy-required
proto2-optional-sfixed64-to-int64|z267|sfixed64|int64|hash|6|FIXED64 signed|VARINT int64|Dart|proto2 optional sfixed64→int64 TYPE (not optional/required drop)|r629 optional drop / r635 legacy-required
proto2-optional-float-to-int64|z268|float|int64|temp_c|7|FIXED32 float|VARINT int64|C#|proto2 optional float→int64 TYPE (not optional/required drop)|r629 optional drop / r635 legacy-required
proto2-optional-double-to-int32|z269|double|int32|peak|8|FIXED64 double|VARINT int32|Go|proto2 optional double→int32 TYPE (not optional/required drop)|r629 optional drop / r635 legacy-required
proto2-optional-bool-to-bytes|z270|bool|bytes|armed|9|VARINT 0/1|LEN bytes|Python|proto2 optional bool→bytes TYPE (not optional/required drop)|r629 optional drop / r635 legacy-required
proto2-optional-string-to-int32|z271|string|int32|sku|2|LEN utf8|VARINT int32|Java|proto2 optional string→int32 TYPE (not optional/required drop)|r629 optional drop / r635 legacy-required
rpc-server-stream-to-client-stream|z272|rpc Watch(Heat) returns (stream Heat)|rpc Watch(stream Heat) returns (Heat)|watch|1344|server-stream|client-stream|Go|rpc-server-stream-to-bidi (server-stream→client-stream, not bidi)|ss2bi / r978 cs2u
rpc-server-stream-to-unary-watch|z273|rpc Watch(Heat) returns (stream Heat)|rpc Watch(Heat) returns (Heat)|watch|1345|server-stream|unary|Python|rpc-unary-to-server-stream (opposite)|u2ss / r978 cs2u
rpc-unary-to-server-stream-list|z274|rpc List(Heat) returns (Heat)|rpc List(Heat) returns (stream Heat)|list|1346|unary List|server-stream List|Java|rpc-unary-to-server-stream (List method, not Watch)|u2ss / r676 LRO
rpc-bidi-to-unary-watch|z275|rpc Watch(stream Heat) returns (stream Heat)|rpc Watch(Heat) returns (Heat)|watch|1347|bidi Watch|unary Watch|Rust|rpc-bidi-to-unary (Watch, not Chat)|bi2u / r978 cs2u
oneof-int32-to-sint64|y400|int32|sint64|tap_n|1405|VARINT int32|zigzag VARINT 64|Kotlin|oneof int32→sint64 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-int32-to-fixed64|y401|int32|fixed64|tap_n|1407|VARINT int32|FIXED64 unsigned|C++|oneof int32→fixed64 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-int32-to-sfixed32|y402|int32|sfixed32|tap_n|1408|VARINT int32|FIXED32 signed|Swift|oneof int32→sfixed32 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-int32-to-sfixed64|y403|int32|sfixed64|tap_n|1409|VARINT int32|FIXED64 signed|Dart|oneof int32→sfixed64 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-int32-to-float|y404|int32|float|tap_n|1410|VARINT int32|FIXED32 float|C#|oneof int32→float leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-int32-to-double|y405|int32|double|tap_n|1411|VARINT int32|FIXED64 double|Go|oneof int32→double leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-int64-to-sint32|y406|int64|sint32|seq|1418|VARINT int64|zigzag VARINT 32|Swift|oneof int64→sint32 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-int64-to-fixed32|y407|int64|fixed32|seq|1420|VARINT int64|FIXED32 unsigned|C#|oneof int64→fixed32 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-int64-to-sfixed32|y408|int64|sfixed32|seq|1422|VARINT int64|FIXED32 signed|Python|oneof int64→sfixed32 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-int64-to-sfixed64|y409|int64|sfixed64|seq|1423|VARINT int64|FIXED64 signed|Java|oneof int64→sfixed64 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-int64-to-float|y410|int64|float|seq|1424|VARINT int64|FIXED32 float|Rust|oneof int64→float leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-int64-to-bool|y411|int64|bool|seq|1426|VARINT int64|VARINT 0/1|TypeScript|oneof int64→bool leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-uint32-to-int64|y412|uint32|int64|port|1430|unsigned VARINT 32|VARINT int64|C#|oneof uint32→int64 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-uint32-to-sint32|y413|uint32|sint32|port|1432|unsigned VARINT 32|zigzag VARINT 32|Python|oneof uint32→sint32 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-uint32-to-sint64|y414|uint32|sint64|port|1433|unsigned VARINT 32|zigzag VARINT 64|Java|oneof uint32→sint64 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-uint32-to-fixed64|y415|uint32|fixed64|port|1435|unsigned VARINT 32|FIXED64 unsigned|Kotlin|oneof uint32→fixed64 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-uint32-to-sfixed32|y416|uint32|sfixed32|port|1436|unsigned VARINT 32|FIXED32 signed|TypeScript|oneof uint32→sfixed32 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-uint32-to-sfixed64|y417|uint32|sfixed64|port|1437|unsigned VARINT 32|FIXED64 signed|C++|oneof uint32→sfixed64 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-uint32-to-float|y418|uint32|float|port|1438|unsigned VARINT 32|FIXED32 float|Swift|oneof uint32→float leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-uint32-to-double|y419|uint32|double|port|1439|unsigned VARINT 32|FIXED64 double|Dart|oneof uint32→double leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-uint64-to-int64|y420|uint64|int64|hash|1444|unsigned VARINT 64|VARINT int64|Rust|oneof uint64→int64 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-uint64-to-uint32|y421|uint64|uint32|hash|1445|unsigned VARINT 64|unsigned VARINT 32|Kotlin|oneof uint64→uint32 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-uint64-to-sint32|y422|uint64|sint32|hash|1446|unsigned VARINT 64|zigzag VARINT 32|TypeScript|oneof uint64→sint32 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-uint64-to-fixed32|y423|uint64|fixed32|hash|1448|unsigned VARINT 64|FIXED32 unsigned|Swift|oneof uint64→fixed32 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-uint64-to-sfixed32|y424|uint64|sfixed32|hash|1450|unsigned VARINT 64|FIXED32 signed|C#|oneof uint64→sfixed32 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-uint64-to-sfixed64|y425|uint64|sfixed64|hash|1451|unsigned VARINT 64|FIXED64 signed|Go|oneof uint64→sfixed64 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-uint64-to-float|y426|uint64|float|hash|1452|unsigned VARINT 64|FIXED32 float|Python|oneof uint64→float leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-uint64-to-double|y427|uint64|double|hash|1453|unsigned VARINT 64|FIXED64 double|Java|oneof uint64→double leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-sint32-to-int64|y428|sint32|int64|delta|1458|zigzag VARINT 32|VARINT int64|Swift|oneof sint32→int64 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-sint32-to-uint32|y429|sint32|uint32|delta|1459|zigzag VARINT 32|unsigned VARINT 32|Dart|oneof sint32→uint32 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-sint32-to-uint64|y430|sint32|uint64|delta|1460|zigzag VARINT 32|unsigned VARINT 64|C#|oneof sint32→uint64 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-sint32-to-fixed32|y431|sint32|fixed32|delta|1462|zigzag VARINT 32|FIXED32 unsigned|Python|oneof sint32→fixed32 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-sint32-to-fixed64|y432|sint32|fixed64|delta|1463|zigzag VARINT 32|FIXED64 unsigned|Java|oneof sint32→fixed64 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-sint32-to-sfixed32|y433|sint32|sfixed32|delta|1464|zigzag VARINT 32|FIXED32 signed|Rust|oneof sint32→sfixed32 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-sint32-to-sfixed64|y434|sint32|sfixed64|delta|1465|zigzag VARINT 32|FIXED64 signed|Kotlin|oneof sint32→sfixed64 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-sint32-to-double|y435|sint32|double|delta|1467|zigzag VARINT 32|FIXED64 double|C++|oneof sint32→double leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-sint64-to-int32|y436|sint64|int32|delta|1471|zigzag VARINT 64|VARINT int32|Go|oneof sint64→int32 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-sint64-to-uint32|y437|sint64|uint32|delta|1473|zigzag VARINT 64|unsigned VARINT 32|Java|oneof sint64→uint32 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-sint64-to-sint32|y438|sint64|sint32|delta|1475|zigzag VARINT 64|zigzag VARINT 32|Kotlin|oneof sint64→sint32 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-sint64-to-fixed32|y439|sint64|fixed32|delta|1476|zigzag VARINT 64|FIXED32 unsigned|TypeScript|oneof sint64→fixed32 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-sint64-to-fixed64|y440|sint64|fixed64|delta|1477|zigzag VARINT 64|FIXED64 unsigned|C++|oneof sint64→fixed64 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-sint64-to-sfixed32|y441|sint64|sfixed32|delta|1478|zigzag VARINT 64|FIXED32 signed|Swift|oneof sint64→sfixed32 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-sint64-to-sfixed64|y442|sint64|sfixed64|delta|1479|zigzag VARINT 64|FIXED64 signed|Dart|oneof sint64→sfixed64 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-sint64-to-float|y443|sint64|float|delta|1480|zigzag VARINT 64|FIXED32 float|C#|oneof sint64→float leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-sint64-to-bool|y444|sint64|bool|delta|1482|zigzag VARINT 64|VARINT 0/1|Python|oneof sint64→bool leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-fixed32-to-int32|y445|fixed32|int32|crc|1485|FIXED32 unsigned|VARINT int32|Kotlin|oneof fixed32→int32 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-fixed32-to-int64|y446|fixed32|int64|crc|1486|FIXED32 unsigned|VARINT int64|TypeScript|oneof fixed32→int64 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-fixed32-to-uint64|y447|fixed32|uint64|crc|1488|FIXED32 unsigned|unsigned VARINT 64|Swift|oneof fixed32→uint64 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-fixed32-to-sint32|y448|fixed32|sint32|crc|1489|FIXED32 unsigned|zigzag VARINT 32|Dart|oneof fixed32→sint32 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-fixed32-to-sint64|y449|fixed32|sint64|crc|1490|FIXED32 unsigned|zigzag VARINT 64|C#|oneof fixed32→sint64 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-fixed32-to-sfixed32|y450|fixed32|sfixed32|crc|1492|FIXED32 unsigned|FIXED32 signed|Python|oneof fixed32→sfixed32 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-fixed32-to-sfixed64|y451|fixed32|sfixed64|crc|1493|FIXED32 unsigned|FIXED64 signed|Java|oneof fixed32→sfixed64 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-fixed32-to-double|y452|fixed32|double|crc|1495|FIXED32 unsigned|FIXED64 double|Kotlin|oneof fixed32→double leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-fixed32-to-string|y453|fixed32|string|crc|1497|FIXED32 unsigned|LEN utf8|C++|oneof fixed32→string leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-fixed64-to-int32|y454|fixed64|int32|hash|1499|FIXED64 unsigned|VARINT int32|Dart|oneof fixed64→int32 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-fixed64-to-uint32|y455|fixed64|uint32|hash|1501|FIXED64 unsigned|unsigned VARINT 32|Go|oneof fixed64→uint32 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-fixed64-to-sint32|y456|fixed64|sint32|hash|1503|FIXED64 unsigned|zigzag VARINT 32|Java|oneof fixed64→sint32 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-fixed64-to-sint64|y457|fixed64|sint64|hash|1504|FIXED64 unsigned|zigzag VARINT 64|Rust|oneof fixed64→sint64 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-fixed64-to-fixed32|y458|fixed64|fixed32|hash|1505|FIXED64 unsigned|FIXED32 unsigned|Kotlin|oneof fixed64→fixed32 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-fixed64-to-sfixed32|y459|fixed64|sfixed32|hash|1506|FIXED64 unsigned|FIXED32 signed|TypeScript|oneof fixed64→sfixed32 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-fixed64-to-sfixed64|y460|fixed64|sfixed64|hash|1507|FIXED64 unsigned|FIXED64 signed|C++|oneof fixed64→sfixed64 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-fixed64-to-float|y461|fixed64|float|hash|1508|FIXED64 unsigned|FIXED32 float|Swift|oneof fixed64→float leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-fixed64-to-string|y462|fixed64|string|hash|1511|FIXED64 unsigned|LEN utf8|Go|oneof fixed64→string leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-sfixed32-to-int32|y463|sfixed32|int32|crc|1513|FIXED32 signed|VARINT int32|Java|oneof sfixed32→int32 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-sfixed32-to-int64|y464|sfixed32|int64|crc|1514|FIXED32 signed|VARINT int64|Rust|oneof sfixed32→int64 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-sfixed32-to-uint32|y465|sfixed32|uint32|crc|1515|FIXED32 signed|unsigned VARINT 32|Kotlin|oneof sfixed32→uint32 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-sfixed32-to-uint64|y466|sfixed32|uint64|crc|1516|FIXED32 signed|unsigned VARINT 64|TypeScript|oneof sfixed32→uint64 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-sfixed32-to-sint32|y467|sfixed32|sint32|crc|1517|FIXED32 signed|zigzag VARINT 32|C++|oneof sfixed32→sint32 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-sfixed32-to-sint64|y468|sfixed32|sint64|crc|1518|FIXED32 signed|zigzag VARINT 64|Swift|oneof sfixed32→sint64 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-sfixed32-to-fixed32|y469|sfixed32|fixed32|crc|1519|FIXED32 signed|FIXED32 unsigned|Dart|oneof sfixed32→fixed32 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-sfixed32-to-fixed64|y470|sfixed32|fixed64|crc|1520|FIXED32 signed|FIXED64 unsigned|C#|oneof sfixed32→fixed64 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-sfixed32-to-sfixed64|y471|sfixed32|sfixed64|crc|1521|FIXED32 signed|FIXED64 signed|Go|oneof sfixed32→sfixed64 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-sfixed32-to-double|y472|sfixed32|double|crc|1523|FIXED32 signed|FIXED64 double|Java|oneof sfixed32→double leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-sfixed32-to-bool|y473|sfixed32|bool|crc|1524|FIXED32 signed|VARINT 0/1|Rust|oneof sfixed32→bool leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-sfixed32-to-string|y474|sfixed32|string|crc|1525|FIXED32 signed|LEN utf8|Kotlin|oneof sfixed32→string leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-sfixed32-to-bytes|y475|sfixed32|bytes|crc|1526|FIXED32 signed|LEN bytes|TypeScript|oneof sfixed32→bytes leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-sfixed64-to-int32|y476|sfixed64|int32|hash|1527|FIXED64 signed|VARINT int32|C++|oneof sfixed64→int32 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-sfixed64-to-int64|y477|sfixed64|int64|hash|1528|FIXED64 signed|VARINT int64|Swift|oneof sfixed64→int64 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-sfixed64-to-uint32|y478|sfixed64|uint32|hash|1529|FIXED64 signed|unsigned VARINT 32|Dart|oneof sfixed64→uint32 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-sfixed64-to-uint64|y479|sfixed64|uint64|hash|1530|FIXED64 signed|unsigned VARINT 64|C#|oneof sfixed64→uint64 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-sfixed64-to-sint32|y480|sfixed64|sint32|hash|1531|FIXED64 signed|zigzag VARINT 32|Go|oneof sfixed64→sint32 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-sfixed64-to-sint64|y481|sfixed64|sint64|hash|1532|FIXED64 signed|zigzag VARINT 64|Python|oneof sfixed64→sint64 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-sfixed64-to-fixed32|y482|sfixed64|fixed32|hash|1533|FIXED64 signed|FIXED32 unsigned|Java|oneof sfixed64→fixed32 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-sfixed64-to-fixed64|y483|sfixed64|fixed64|hash|1534|FIXED64 signed|FIXED64 unsigned|Rust|oneof sfixed64→fixed64 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-sfixed64-to-sfixed32|y484|sfixed64|sfixed32|hash|1535|FIXED64 signed|FIXED32 signed|Kotlin|oneof sfixed64→sfixed32 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-sfixed64-to-float|y485|sfixed64|float|hash|1536|FIXED64 signed|FIXED32 float|TypeScript|oneof sfixed64→float leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-sfixed64-to-bool|y486|sfixed64|bool|hash|1538|FIXED64 signed|VARINT 0/1|Swift|oneof sfixed64→bool leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-sfixed64-to-string|y487|sfixed64|string|hash|1539|FIXED64 signed|LEN utf8|Dart|oneof sfixed64→string leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-sfixed64-to-bytes|y488|sfixed64|bytes|hash|1540|FIXED64 signed|LEN bytes|C#|oneof sfixed64→bytes leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-float-to-int64|y489|float|int64|temp_c|1542|FIXED32 float|VARINT int64|Python|oneof float→int64 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-float-to-uint64|y490|float|uint64|temp_c|1544|FIXED32 float|unsigned VARINT 64|Rust|oneof float→uint64 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-float-to-sint32|y491|float|sint32|temp_c|1545|FIXED32 float|zigzag VARINT 32|Kotlin|oneof float→sint32 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-float-to-sint64|y492|float|sint64|temp_c|1546|FIXED32 float|zigzag VARINT 64|TypeScript|oneof float→sint64 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-float-to-fixed32|y493|float|fixed32|temp_c|1547|FIXED32 float|FIXED32 unsigned|C++|oneof float→fixed32 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-float-to-fixed64|y494|float|fixed64|temp_c|1548|FIXED32 float|FIXED64 unsigned|Swift|oneof float→fixed64 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-float-to-sfixed32|y495|float|sfixed32|temp_c|1549|FIXED32 float|FIXED32 signed|Dart|oneof float→sfixed32 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-float-to-sfixed64|y496|float|sfixed64|temp_c|1550|FIXED32 float|FIXED64 signed|C#|oneof float→sfixed64 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-double-to-int32|y497|double|int32|peak|1555|FIXED64 double|VARINT int32|Kotlin|oneof double→int32 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-double-to-uint32|y498|double|uint32|peak|1557|FIXED64 double|unsigned VARINT 32|C++|oneof double→uint32 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-double-to-sint32|y499|double|sint32|peak|1559|FIXED64 double|zigzag VARINT 32|Dart|oneof double→sint32 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-double-to-sint64|y500|double|sint64|peak|1560|FIXED64 double|zigzag VARINT 64|C#|oneof double→sint64 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-double-to-fixed32|y501|double|fixed32|peak|1561|FIXED64 double|FIXED32 unsigned|Go|oneof double→fixed32 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-double-to-fixed64|y502|double|fixed64|peak|1562|FIXED64 double|FIXED64 unsigned|Python|oneof double→fixed64 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-double-to-sfixed32|y503|double|sfixed32|peak|1563|FIXED64 double|FIXED32 signed|Java|oneof double→sfixed32 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-double-to-sfixed64|y504|double|sfixed64|peak|1564|FIXED64 double|FIXED64 signed|Rust|oneof double→sfixed64 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-double-to-float|y505|double|float|peak|1565|FIXED64 double|FIXED32 float|Kotlin|oneof double→float leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-bool-to-int64|y506|bool|int64|armed|1570|VARINT 0/1|VARINT int64|C#|oneof bool→int64 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-bool-to-sint32|y507|bool|sint32|armed|1573|VARINT 0/1|zigzag VARINT 32|Java|oneof bool→sint32 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-bool-to-sint64|y508|bool|sint64|armed|1574|VARINT 0/1|zigzag VARINT 64|Rust|oneof bool→sint64 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-bool-to-fixed32|y509|bool|fixed32|armed|1575|VARINT 0/1|FIXED32 unsigned|Kotlin|oneof bool→fixed32 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-bool-to-fixed64|y510|bool|fixed64|armed|1576|VARINT 0/1|FIXED64 unsigned|TypeScript|oneof bool→fixed64 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-bool-to-sfixed32|y511|bool|sfixed32|armed|1577|VARINT 0/1|FIXED32 signed|C++|oneof bool→sfixed32 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-bool-to-sfixed64|y512|bool|sfixed64|armed|1578|VARINT 0/1|FIXED64 signed|Swift|oneof bool→sfixed64 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-bool-to-double|y513|bool|double|armed|1580|VARINT 0/1|FIXED64 double|C#|oneof bool→double leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-bool-to-bytes|y514|bool|bytes|armed|1582|VARINT 0/1|LEN bytes|Python|oneof bool→bytes leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-string-to-uint64|y515|string|uint64|sku|1586|LEN utf8|unsigned VARINT 64|TypeScript|oneof string→uint64 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-string-to-sint32|y516|string|sint32|sku|1587|LEN utf8|zigzag VARINT 32|C++|oneof string→sint32 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-string-to-sint64|y517|string|sint64|sku|1588|LEN utf8|zigzag VARINT 64|Swift|oneof string→sint64 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-string-to-fixed32|y518|string|fixed32|sku|1589|LEN utf8|FIXED32 unsigned|Dart|oneof string→fixed32 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-string-to-fixed64|y519|string|fixed64|sku|1590|LEN utf8|FIXED64 unsigned|C#|oneof string→fixed64 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-string-to-sfixed32|y520|string|sfixed32|sku|1591|LEN utf8|FIXED32 signed|Go|oneof string→sfixed32 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-string-to-sfixed64|y521|string|sfixed64|sku|1592|LEN utf8|FIXED64 signed|Python|oneof string→sfixed64 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-string-to-double|y522|string|double|sku|1594|LEN utf8|FIXED64 double|Rust|oneof string→double leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-bytes-to-uint64|y523|bytes|uint64|blob|1600|LEN bytes|unsigned VARINT 64|C#|oneof bytes→uint64 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-bytes-to-sint32|y524|bytes|sint32|blob|1601|LEN bytes|zigzag VARINT 32|Go|oneof bytes→sint32 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-bytes-to-sint64|y525|bytes|sint64|blob|1602|LEN bytes|zigzag VARINT 64|Python|oneof bytes→sint64 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-bytes-to-fixed32|y526|bytes|fixed32|blob|1603|LEN bytes|FIXED32 unsigned|Java|oneof bytes→fixed32 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-bytes-to-fixed64|y527|bytes|fixed64|blob|1604|LEN bytes|FIXED64 unsigned|Rust|oneof bytes→fixed64 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-bytes-to-sfixed32|y528|bytes|sfixed32|blob|1605|LEN bytes|FIXED32 signed|Kotlin|oneof bytes→sfixed32 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-bytes-to-sfixed64|y529|bytes|sfixed64|blob|1606|LEN bytes|FIXED64 signed|TypeScript|oneof bytes→sfixed64 leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
oneof-bytes-to-double|y530|bytes|double|blob|1608|LEN bytes|FIXED64 double|Swift|oneof bytes→double leftover arm (not r787-r987 clone)|r787 leftover / r987 leftover
map-value-int32-to-sint64|y531|int32|sint64|taps|1615|value VARINT int32|value zigzag VARINT 64|Kotlin|map value int32→sint64 (not map-key)|map-key ban / r787 leftover
map-value-int32-to-fixed32|y532|int32|fixed32|taps|1616|value VARINT int32|value FIXED32 unsigned|TypeScript|map value int32→fixed32 (not map-key)|map-key ban / r787 leftover
map-value-int32-to-fixed64|y533|int32|fixed64|taps|1617|value VARINT int32|value FIXED64 unsigned|C++|map value int32→fixed64 (not map-key)|map-key ban / r787 leftover
map-value-int32-to-sfixed32|y534|int32|sfixed32|taps|1618|value VARINT int32|value FIXED32 signed|Swift|map value int32→sfixed32 (not map-key)|map-key ban / r787 leftover
map-value-int32-to-sfixed64|y535|int32|sfixed64|taps|1619|value VARINT int32|value FIXED64 signed|Dart|map value int32→sfixed64 (not map-key)|map-key ban / r787 leftover
map-value-int32-to-double|y536|int32|double|taps|1621|value VARINT int32|value FIXED64 double|Go|map value int32→double (not map-key)|map-key ban / r787 leftover
map-value-int32-to-bool|y537|int32|bool|taps|1622|value VARINT int32|value VARINT 0/1|Python|map value int32→bool (not map-key)|map-key ban / r787 leftover
map-value-int32-to-bytes|y538|int32|bytes|taps|1624|value VARINT int32|value LEN bytes|Rust|map value int32→bytes (not map-key)|map-key ban / r787 leftover
map-value-int64-to-int32|y539|int64|int32|seqs|1625|value VARINT int64|value VARINT int32|Kotlin|map value int64→int32 (not map-key)|map-key ban / r787 leftover
map-value-int64-to-uint64|y540|int64|uint64|seqs|1627|value VARINT int64|value unsigned VARINT 64|C++|map value int64→uint64 (not map-key)|map-key ban / r787 leftover
map-value-int64-to-sint32|y541|int64|sint32|seqs|1628|value VARINT int64|value zigzag VARINT 32|Swift|map value int64→sint32 (not map-key)|map-key ban / r787 leftover
map-value-int64-to-fixed32|y542|int64|fixed32|seqs|1630|value VARINT int64|value FIXED32 unsigned|C#|map value int64→fixed32 (not map-key)|map-key ban / r787 leftover
map-value-int64-to-sfixed32|y543|int64|sfixed32|seqs|1632|value VARINT int64|value FIXED32 signed|Python|map value int64→sfixed32 (not map-key)|map-key ban / r787 leftover
map-value-int64-to-sfixed64|y544|int64|sfixed64|seqs|1633|value VARINT int64|value FIXED64 signed|Java|map value int64→sfixed64 (not map-key)|map-key ban / r787 leftover
map-value-int64-to-float|y545|int64|float|seqs|1634|value VARINT int64|value FIXED32 float|Rust|map value int64→float (not map-key)|map-key ban / r787 leftover
map-value-int64-to-double|y546|int64|double|seqs|1635|value VARINT int64|value FIXED64 double|Kotlin|map value int64→double (not map-key)|map-key ban / r787 leftover
map-value-uint32-to-int32|y547|uint32|int32|ports|1639|value unsigned VARINT 32|value VARINT int32|Dart|map value uint32→int32 (not map-key)|map-key ban / r787 leftover
map-value-uint32-to-sint64|y548|uint32|sint64|ports|1643|value unsigned VARINT 32|value zigzag VARINT 64|Java|map value uint32→sint64 (not map-key)|map-key ban / r787 leftover
map-value-uint32-to-fixed32|y549|uint32|fixed32|ports|1644|value unsigned VARINT 32|value FIXED32 unsigned|Rust|map value uint32→fixed32 (not map-key)|map-key ban / r787 leftover
map-value-uint32-to-fixed64|y550|uint32|fixed64|ports|1645|value unsigned VARINT 32|value FIXED64 unsigned|Kotlin|map value uint32→fixed64 (not map-key)|map-key ban / r787 leftover
map-value-uint32-to-sfixed32|y551|uint32|sfixed32|ports|1646|value unsigned VARINT 32|value FIXED32 signed|TypeScript|map value uint32→sfixed32 (not map-key)|map-key ban / r787 leftover
map-value-uint32-to-sfixed64|y552|uint32|sfixed64|ports|1647|value unsigned VARINT 32|value FIXED64 signed|C++|map value uint32→sfixed64 (not map-key)|map-key ban / r787 leftover
map-value-uint32-to-double|y553|uint32|double|ports|1649|value unsigned VARINT 32|value FIXED64 double|Dart|map value uint32→double (not map-key)|map-key ban / r787 leftover
map-value-uint64-to-int64|y554|uint64|int64|hashes|1654|value unsigned VARINT 64|value VARINT int64|Rust|map value uint64→int64 (not map-key)|map-key ban / r787 leftover
map-value-uint64-to-uint32|y555|uint64|uint32|hashes|1655|value unsigned VARINT 64|value unsigned VARINT 32|Kotlin|map value uint64→uint32 (not map-key)|map-key ban / r787 leftover
map-value-uint64-to-sint64|y556|uint64|sint64|hashes|1657|value unsigned VARINT 64|value zigzag VARINT 64|C++|map value uint64→sint64 (not map-key)|map-key ban / r787 leftover
map-value-uint64-to-fixed32|y557|uint64|fixed32|hashes|1658|value unsigned VARINT 64|value FIXED32 unsigned|Swift|map value uint64→fixed32 (not map-key)|map-key ban / r787 leftover
map-value-uint64-to-fixed64|y558|uint64|fixed64|hashes|1659|value unsigned VARINT 64|value FIXED64 unsigned|Dart|map value uint64→fixed64 (not map-key)|map-key ban / r787 leftover
map-value-uint64-to-sfixed32|y559|uint64|sfixed32|hashes|1660|value unsigned VARINT 64|value FIXED32 signed|C#|map value uint64→sfixed32 (not map-key)|map-key ban / r787 leftover
map-value-uint64-to-sfixed64|y560|uint64|sfixed64|hashes|1661|value unsigned VARINT 64|value FIXED64 signed|Go|map value uint64→sfixed64 (not map-key)|map-key ban / r787 leftover
map-value-uint64-to-double|y561|uint64|double|hashes|1663|value unsigned VARINT 64|value FIXED64 double|Java|map value uint64→double (not map-key)|map-key ban / r787 leftover
map-value-uint64-to-string|y562|uint64|string|hashes|1665|value unsigned VARINT 64|value LEN utf8|Kotlin|map value uint64→string (not map-key)|map-key ban / r787 leftover
map-value-sint32-to-uint64|y563|sint32|uint64|deltas|1670|value zigzag VARINT 32|value unsigned VARINT 64|C#|map value sint32→uint64 (not map-key)|map-key ban / r787 leftover
map-value-sint32-to-sint64|y564|sint32|sint64|deltas|1671|value zigzag VARINT 32|value zigzag VARINT 64|Go|map value sint32→sint64 (not map-key)|map-key ban / r787 leftover
map-value-sint32-to-fixed32|y565|sint32|fixed32|deltas|1672|value zigzag VARINT 32|value FIXED32 unsigned|Python|map value sint32→fixed32 (not map-key)|map-key ban / r787 leftover
map-value-sint32-to-fixed64|y566|sint32|fixed64|deltas|1673|value zigzag VARINT 32|value FIXED64 unsigned|Java|map value sint32→fixed64 (not map-key)|map-key ban / r787 leftover
map-value-sint32-to-sfixed32|y567|sint32|sfixed32|deltas|1674|value zigzag VARINT 32|value FIXED32 signed|Rust|map value sint32→sfixed32 (not map-key)|map-key ban / r787 leftover
map-value-sint32-to-sfixed64|y568|sint32|sfixed64|deltas|1675|value zigzag VARINT 32|value FIXED64 signed|Kotlin|map value sint32→sfixed64 (not map-key)|map-key ban / r787 leftover
map-value-sint32-to-double|y569|sint32|double|deltas|1677|value zigzag VARINT 32|value FIXED64 double|C++|map value sint32→double (not map-key)|map-key ban / r787 leftover
map-value-sint32-to-bool|y570|sint32|bool|deltas|1678|value zigzag VARINT 32|value VARINT 0/1|Swift|map value sint32→bool (not map-key)|map-key ban / r787 leftover
map-value-sint64-to-int32|y571|sint64|int32|deltas|1681|value zigzag VARINT 64|value VARINT int32|Go|map value sint64→int32 (not map-key)|map-key ban / r787 leftover
map-value-sint64-to-uint64|y572|sint64|uint64|deltas|1684|value zigzag VARINT 64|value unsigned VARINT 64|Rust|map value sint64→uint64 (not map-key)|map-key ban / r787 leftover
map-value-sint64-to-sint32|y573|sint64|sint32|deltas|1685|value zigzag VARINT 64|value zigzag VARINT 32|Kotlin|map value sint64→sint32 (not map-key)|map-key ban / r787 leftover
map-value-sint64-to-fixed32|y574|sint64|fixed32|deltas|1686|value zigzag VARINT 64|value FIXED32 unsigned|TypeScript|map value sint64→fixed32 (not map-key)|map-key ban / r787 leftover
map-value-sint64-to-fixed64|y575|sint64|fixed64|deltas|1687|value zigzag VARINT 64|value FIXED64 unsigned|C++|map value sint64→fixed64 (not map-key)|map-key ban / r787 leftover
map-value-sint64-to-sfixed32|y576|sint64|sfixed32|deltas|1688|value zigzag VARINT 64|value FIXED32 signed|Swift|map value sint64→sfixed32 (not map-key)|map-key ban / r787 leftover
map-value-sint64-to-sfixed64|y577|sint64|sfixed64|deltas|1689|value zigzag VARINT 64|value FIXED64 signed|Dart|map value sint64→sfixed64 (not map-key)|map-key ban / r787 leftover
map-value-sint64-to-double|y578|sint64|double|deltas|1691|value zigzag VARINT 64|value FIXED64 double|Go|map value sint64→double (not map-key)|map-key ban / r787 leftover
map-value-fixed32-to-int64|y579|fixed32|int64|crcs|1696|value FIXED32 unsigned|value VARINT int64|TypeScript|map value fixed32→int64 (not map-key)|map-key ban / r787 leftover
map-value-fixed32-to-uint32|y580|fixed32|uint32|crcs|1697|value FIXED32 unsigned|value unsigned VARINT 32|C++|map value fixed32→uint32 (not map-key)|map-key ban / r787 leftover
map-value-fixed32-to-sint32|y581|fixed32|sint32|crcs|1699|value FIXED32 unsigned|value zigzag VARINT 32|Dart|map value fixed32→sint32 (not map-key)|map-key ban / r787 leftover
map-value-fixed32-to-sint64|y582|fixed32|sint64|crcs|1700|value FIXED32 unsigned|value zigzag VARINT 64|C#|map value fixed32→sint64 (not map-key)|map-key ban / r787 leftover
map-value-fixed32-to-fixed64|y583|fixed32|fixed64|crcs|1701|value FIXED32 unsigned|value FIXED64 unsigned|Go|map value fixed32→fixed64 (not map-key)|map-key ban / r787 leftover
map-value-fixed32-to-sfixed32|y584|fixed32|sfixed32|crcs|1702|value FIXED32 unsigned|value FIXED32 signed|Python|map value fixed32→sfixed32 (not map-key)|map-key ban / r787 leftover
map-value-fixed32-to-sfixed64|y585|fixed32|sfixed64|crcs|1703|value FIXED32 unsigned|value FIXED64 signed|Java|map value fixed32→sfixed64 (not map-key)|map-key ban / r787 leftover
map-value-fixed32-to-double|y586|fixed32|double|crcs|1705|value FIXED32 unsigned|value FIXED64 double|Kotlin|map value fixed32→double (not map-key)|map-key ban / r787 leftover
map-value-fixed32-to-string|y587|fixed32|string|crcs|1707|value FIXED32 unsigned|value LEN utf8|C++|map value fixed32→string (not map-key)|map-key ban / r787 leftover
map-value-fixed64-to-uint64|y588|fixed64|uint64|hashes|1712|value FIXED64 unsigned|value unsigned VARINT 64|Python|map value fixed64→uint64 (not map-key)|map-key ban / r787 leftover
map-value-fixed64-to-sint32|y589|fixed64|sint32|hashes|1713|value FIXED64 unsigned|value zigzag VARINT 32|Java|map value fixed64→sint32 (not map-key)|map-key ban / r787 leftover
map-value-fixed64-to-sint64|y590|fixed64|sint64|hashes|1714|value FIXED64 unsigned|value zigzag VARINT 64|Rust|map value fixed64→sint64 (not map-key)|map-key ban / r787 leftover
map-value-fixed64-to-fixed32|y591|fixed64|fixed32|hashes|1715|value FIXED64 unsigned|value FIXED32 unsigned|Kotlin|map value fixed64→fixed32 (not map-key)|map-key ban / r787 leftover
map-value-fixed64-to-sfixed32|y592|fixed64|sfixed32|hashes|1716|value FIXED64 unsigned|value FIXED32 signed|TypeScript|map value fixed64→sfixed32 (not map-key)|map-key ban / r787 leftover
map-value-fixed64-to-sfixed64|y593|fixed64|sfixed64|hashes|1717|value FIXED64 unsigned|value FIXED64 signed|C++|map value fixed64→sfixed64 (not map-key)|map-key ban / r787 leftover
map-value-fixed64-to-float|y594|fixed64|float|hashes|1718|value FIXED64 unsigned|value FIXED32 float|Swift|map value fixed64→float (not map-key)|map-key ban / r787 leftover
map-value-fixed64-to-bytes|y595|fixed64|bytes|hashes|1722|value FIXED64 unsigned|value LEN bytes|Python|map value fixed64→bytes (not map-key)|map-key ban / r787 leftover
map-value-sfixed32-to-int64|y596|sfixed32|int64|crcs|1724|value FIXED32 signed|value VARINT int64|Rust|map value sfixed32→int64 (not map-key)|map-key ban / r787 leftover
map-value-sfixed32-to-uint32|y597|sfixed32|uint32|crcs|1725|value FIXED32 signed|value unsigned VARINT 32|Kotlin|map value sfixed32→uint32 (not map-key)|map-key ban / r787 leftover
map-value-sfixed32-to-uint64|y598|sfixed32|uint64|crcs|1726|value FIXED32 signed|value unsigned VARINT 64|TypeScript|map value sfixed32→uint64 (not map-key)|map-key ban / r787 leftover
map-value-sfixed32-to-sint32|y599|sfixed32|sint32|crcs|1727|value FIXED32 signed|value zigzag VARINT 32|C++|map value sfixed32→sint32 (not map-key)|map-key ban / r787 leftover
map-value-sfixed32-to-sint64|y600|sfixed32|sint64|crcs|1728|value FIXED32 signed|value zigzag VARINT 64|Swift|map value sfixed32→sint64 (not map-key)|map-key ban / r787 leftover
map-value-sfixed32-to-fixed32|y601|sfixed32|fixed32|crcs|1729|value FIXED32 signed|value FIXED32 unsigned|Dart|map value sfixed32→fixed32 (not map-key)|map-key ban / r787 leftover
map-value-sfixed32-to-fixed64|y602|sfixed32|fixed64|crcs|1730|value FIXED32 signed|value FIXED64 unsigned|C#|map value sfixed32→fixed64 (not map-key)|map-key ban / r787 leftover
map-value-sfixed32-to-sfixed64|y603|sfixed32|sfixed64|crcs|1731|value FIXED32 signed|value FIXED64 signed|Go|map value sfixed32→sfixed64 (not map-key)|map-key ban / r787 leftover
map-value-sfixed32-to-float|y604|sfixed32|float|crcs|1732|value FIXED32 signed|value FIXED32 float|Python|map value sfixed32→float (not map-key)|map-key ban / r787 leftover
map-value-sfixed32-to-double|y605|sfixed32|double|crcs|1733|value FIXED32 signed|value FIXED64 double|Java|map value sfixed32→double (not map-key)|map-key ban / r787 leftover
map-value-sfixed32-to-bool|y606|sfixed32|bool|crcs|1734|value FIXED32 signed|value VARINT 0/1|Rust|map value sfixed32→bool (not map-key)|map-key ban / r787 leftover
map-value-sfixed32-to-string|y607|sfixed32|string|crcs|1735|value FIXED32 signed|value LEN utf8|Kotlin|map value sfixed32→string (not map-key)|map-key ban / r787 leftover
map-value-sfixed32-to-bytes|y608|sfixed32|bytes|crcs|1736|value FIXED32 signed|value LEN bytes|TypeScript|map value sfixed32→bytes (not map-key)|map-key ban / r787 leftover
map-value-sfixed64-to-int32|y609|sfixed64|int32|hashes|1737|value FIXED64 signed|value VARINT int32|C++|map value sfixed64→int32 (not map-key)|map-key ban / r787 leftover
map-value-sfixed64-to-int64|y610|sfixed64|int64|hashes|1738|value FIXED64 signed|value VARINT int64|Swift|map value sfixed64→int64 (not map-key)|map-key ban / r787 leftover
map-value-sfixed64-to-uint32|y611|sfixed64|uint32|hashes|1739|value FIXED64 signed|value unsigned VARINT 32|Dart|map value sfixed64→uint32 (not map-key)|map-key ban / r787 leftover
map-value-sfixed64-to-uint64|y612|sfixed64|uint64|hashes|1740|value FIXED64 signed|value unsigned VARINT 64|C#|map value sfixed64→uint64 (not map-key)|map-key ban / r787 leftover
map-value-sfixed64-to-sint32|y613|sfixed64|sint32|hashes|1741|value FIXED64 signed|value zigzag VARINT 32|Go|map value sfixed64→sint32 (not map-key)|map-key ban / r787 leftover
map-value-sfixed64-to-sint64|y614|sfixed64|sint64|hashes|1742|value FIXED64 signed|value zigzag VARINT 64|Python|map value sfixed64→sint64 (not map-key)|map-key ban / r787 leftover
map-value-sfixed64-to-fixed32|y615|sfixed64|fixed32|hashes|1743|value FIXED64 signed|value FIXED32 unsigned|Java|map value sfixed64→fixed32 (not map-key)|map-key ban / r787 leftover
map-value-sfixed64-to-fixed64|y616|sfixed64|fixed64|hashes|1744|value FIXED64 signed|value FIXED64 unsigned|Rust|map value sfixed64→fixed64 (not map-key)|map-key ban / r787 leftover
map-value-sfixed64-to-sfixed32|y617|sfixed64|sfixed32|hashes|1745|value FIXED64 signed|value FIXED32 signed|Kotlin|map value sfixed64→sfixed32 (not map-key)|map-key ban / r787 leftover
map-value-sfixed64-to-float|y618|sfixed64|float|hashes|1746|value FIXED64 signed|value FIXED32 float|TypeScript|map value sfixed64→float (not map-key)|map-key ban / r787 leftover
map-value-sfixed64-to-bool|y619|sfixed64|bool|hashes|1748|value FIXED64 signed|value VARINT 0/1|Swift|map value sfixed64→bool (not map-key)|map-key ban / r787 leftover
map-value-sfixed64-to-string|y620|sfixed64|string|hashes|1749|value FIXED64 signed|value LEN utf8|Dart|map value sfixed64→string (not map-key)|map-key ban / r787 leftover
map-value-sfixed64-to-bytes|y621|sfixed64|bytes|hashes|1750|value FIXED64 signed|value LEN bytes|C#|map value sfixed64→bytes (not map-key)|map-key ban / r787 leftover
map-value-float-to-uint64|y622|float|uint64|temps|1754|value FIXED32 float|value unsigned VARINT 64|Rust|map value float→uint64 (not map-key)|map-key ban / r787 leftover
map-value-float-to-sint32|y623|float|sint32|temps|1755|value FIXED32 float|value zigzag VARINT 32|Kotlin|map value float→sint32 (not map-key)|map-key ban / r787 leftover
map-value-float-to-sint64|y624|float|sint64|temps|1756|value FIXED32 float|value zigzag VARINT 64|TypeScript|map value float→sint64 (not map-key)|map-key ban / r787 leftover
map-value-float-to-fixed32|y625|float|fixed32|temps|1757|value FIXED32 float|value FIXED32 unsigned|C++|map value float→fixed32 (not map-key)|map-key ban / r787 leftover
map-value-float-to-fixed64|y626|float|fixed64|temps|1758|value FIXED32 float|value FIXED64 unsigned|Swift|map value float→fixed64 (not map-key)|map-key ban / r787 leftover
map-value-float-to-sfixed32|y627|float|sfixed32|temps|1759|value FIXED32 float|value FIXED32 signed|Dart|map value float→sfixed32 (not map-key)|map-key ban / r787 leftover
map-value-float-to-sfixed64|y628|float|sfixed64|temps|1760|value FIXED32 float|value FIXED64 signed|C#|map value float→sfixed64 (not map-key)|map-key ban / r787 leftover
map-value-float-to-string|y629|float|string|temps|1763|value FIXED32 float|value LEN utf8|Java|map value float→string (not map-key)|map-key ban / r787 leftover
map-value-double-to-uint64|y630|double|uint64|peaks|1768|value FIXED64 double|value unsigned VARINT 64|Swift|map value double→uint64 (not map-key)|map-key ban / r787 leftover
map-value-double-to-sint32|y631|double|sint32|peaks|1769|value FIXED64 double|value zigzag VARINT 32|Dart|map value double→sint32 (not map-key)|map-key ban / r787 leftover
map-value-double-to-sint64|y632|double|sint64|peaks|1770|value FIXED64 double|value zigzag VARINT 64|C#|map value double→sint64 (not map-key)|map-key ban / r787 leftover
map-value-double-to-fixed32|y633|double|fixed32|peaks|1771|value FIXED64 double|value FIXED32 unsigned|Go|map value double→fixed32 (not map-key)|map-key ban / r787 leftover
map-value-double-to-fixed64|y634|double|fixed64|peaks|1772|value FIXED64 double|value FIXED64 unsigned|Python|map value double→fixed64 (not map-key)|map-key ban / r787 leftover
map-value-double-to-sfixed32|y635|double|sfixed32|peaks|1773|value FIXED64 double|value FIXED32 signed|Java|map value double→sfixed32 (not map-key)|map-key ban / r787 leftover
map-value-double-to-sfixed64|y636|double|sfixed64|peaks|1774|value FIXED64 double|value FIXED64 signed|Rust|map value double→sfixed64 (not map-key)|map-key ban / r787 leftover
map-value-bool-to-uint64|y637|bool|uint64|flags|1782|value VARINT 0/1|value unsigned VARINT 64|Python|map value bool→uint64 (not map-key)|map-key ban / r787 leftover
map-value-bool-to-sint32|y638|bool|sint32|flags|1783|value VARINT 0/1|value zigzag VARINT 32|Java|map value bool→sint32 (not map-key)|map-key ban / r787 leftover
map-value-bool-to-sint64|y639|bool|sint64|flags|1784|value VARINT 0/1|value zigzag VARINT 64|Rust|map value bool→sint64 (not map-key)|map-key ban / r787 leftover
"""


def _guard(spec: dict) -> None:
    slug = spec["slug"]
    if slug in BANNED_SLUGS:
        raise SystemExit(f"banned slug {slug!r}")
    if slug.startswith("map-key-"):
        raise SystemExit(f"map-key type swap banned this mill: {slug!r}")
    identity = " ".join(
        str(spec.get(k, ""))
        for k in ("slug", "short", "decl_old", "decl_new", "buf_rule")
    ).lower()
    for needle in BANNED_NEEDLES:
        if needle in identity:
            raise SystemExit(f"banned needle {needle!r} in {identity!r}")


def _extras_for(slug: str, told: str, tnew: str, field: str, num: int) -> dict:
    extra: dict = {}
    if "Mode" in (told, tnew) or slug.startswith("enum-") or "-enum-" in slug or slug.endswith("-enum-mode") or slug.endswith("-enum-port") or slug.endswith("-enum-hash") or slug.endswith("-enum-crc") or slug.endswith("-enum-temp") or slug.endswith("-enum-peak") or slug.endswith("-enum-armed") or slug.endswith("-enum-delta") or slug.endswith("-enum-blob"):
        extra["extra_msgs"] = ENUM_MODE
        extra.setdefault("grep_pat", f"{told} {field}|{tnew} {field}")
    if slug.startswith("singular-") and "repeated" in slug:
        extra["buf_rule"] = "FIELD_CARDINALITY / WIRE"
    if slug.startswith("repeated-") and slug.endswith("-singular"):
        extra["buf_rule"] = "FIELD_CARDINALITY / WIRE"
        extra["decl_old"] = f"{told} {field} = {num};"
        extra["decl_new"] = f"{tnew} {field} = {num};"
    if slug.startswith("map-value-"):
        extra["buf_rule"] = "MAP_VALUE_TYPE / WIRE"
        extra["decl_old"] = f"map<string, {told}> {field} = {num};"
        extra["decl_new"] = f"map<string, {tnew}> {field} = {num};"
        extra["grep_pat"] = f"map<string, {told}>|map<string, {tnew}>|{field}"
    if slug.startswith("oneof-"):
        extra["decl_old"] = f"oneof body {{ {told} {field} = {num}; }}"
        extra["decl_new"] = f"oneof body {{ {tnew} {field} = {num}; }}"
        extra["grep_pat"] = f"oneof body|{told} {field}|{tnew} {field}"
        if "Mode" in (told, tnew):
            extra["extra_msgs"] = ENUM_MODE
    if slug.startswith("rpc-"):
        extra["buf_rule"] = "RPC_STREAMING / WIRE"
        extra["decl_old"] = told if told.startswith("rpc ") else extra.get("decl_old")
        extra["decl_new"] = tnew if tnew.startswith("rpc ") else extra.get("decl_new")
        extra["grep_pat"] = f"{told}|{tnew}"
        extra["goal_bit"] = f"{told} → {tnew} so freeze {slug} frames fail"
    if slug.startswith("proto2-required-"):
        extra["syntax"] = 'syntax = "proto2";'
        extra["decl_old"] = f"required {told} {field} = {num};"
        extra["decl_new"] = f"required {tnew} {field} = {num};"
        extra["grep_pat"] = f"required {told} {field}|required {tnew} {field}"
    if slug.startswith("proto2-optional-"):
        extra["syntax"] = 'syntax = "proto2";'
        extra["decl_old"] = f"optional {told} {field} = {num};"
        extra["decl_new"] = f"optional {tnew} {field} = {num};"
        extra["grep_pat"] = f"optional {told} {field}|optional {tnew} {field}"
    imports = []
    blob = f"{told} {tnew} {slug}"
    if "Timestamp" in blob:
        imports.append("google/protobuf/timestamp.proto")
    if "Duration" in blob:
        imports.append("google/protobuf/duration.proto")
    if "protobuf.Any" in blob or "google.protobuf.Any" in blob:
        imports.append("google/protobuf/any.proto")
    if "Struct" in blob or "ListValue" in blob or "NullValue" in blob or (
        "protobuf.Value" in blob or "google.protobuf.Value" in blob
    ):
        imports.append("google/protobuf/struct.proto")
    if "Empty" in blob:
        imports.append("google/protobuf/empty.proto")
    if "FieldMask" in blob:
        imports.append("google/protobuf/field_mask.proto")
    if "SourceContext" in blob:
        imports.append("google/protobuf/source_context.proto")
    if "HttpBody" in blob:
        imports.append("google/api/httpbody.proto")
    if "RetryInfo" in blob:
        imports.append("google/rpc/error_details.proto")
    if "TimeZone" in blob:
        imports.append("google/type/datetime.proto")
    if "DayOfWeek" in blob:
        imports.append("google/type/dayofweek.proto")
    if "type.Month" in blob or "google.type.Month" in blob:
        imports.append("google/type/month.proto")
    if "Fraction" in blob:
        imports.append("google/type/fraction.proto")
    if "LocalizedText" in blob:
        imports.append("google/type/localized_text.proto")
    if "Value" in blob and "wrappers" not in slug and any(
        x in blob
        for x in (
            "Int32Value",
            "Int64Value",
            "UInt32Value",
            "UInt64Value",
            "FloatValue",
            "DoubleValue",
            "BoolValue",
            "StringValue",
            "BytesValue",
        )
    ):
        imports.append("google/protobuf/wrappers.proto")
    if imports:
        # preserve order, unique
        seen = []
        for imp in imports:
            if imp not in seen:
                seen.append(imp)
        extra["imports"] = tuple(seen)
    return extra


def _parse_rows() -> list[dict]:
    plants = []
    seen_slug = set()
    seen_short = set()
    for line in RAW.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("|")
        if len(parts) != 11:
            raise SystemExit(f"bad row cols={len(parts)}: {line!r}")
        slug, short, told, tnew, field, num_s, wold, wnew, lang, vs, avoid = parts
        num = int(num_s)
        if slug in seen_slug:
            raise SystemExit(f"dup slug {slug}")
        if short in seen_short:
            raise SystemExit(f"dup short {short}")
        seen_slug.add(slug)
        seen_short.add(short)
        extra = _extras_for(slug, told, tnew, field, num)
        ticket = f"{LANGC[lang]}-{short.upper()}-{num}"
        plants.append(
            ty(
                slug,
                short,
                told,
                tnew,
                field,
                num,
                wold,
                wnew,
                lang,
                ticket,
                vs,
                avoid,
                **extra,
            )
        )
    return plants


_PLANTS = _parse_rows()
if len(_PLANTS) % 2:
    raise SystemExit(f"odd plant count {len(_PLANTS)}")
PAIRS: list[tuple[dict, dict]] = [
    (_PLANTS[i], _PLANTS[i + 1]) for i in range(0, len(_PLANTS), 2)
]


def unused_pairs() -> list[tuple[dict, dict]]:
    taken = used_slugs()
    out = []
    seen = set()
    for suc, xf in PAIRS:
        _guard(suc)
        _guard(xf)
        if suc["slug"] in taken or xf["slug"] in taken:
            continue
        if suc["slug"] == xf["slug"]:
            raise SystemExit(f"pair slug collision {suc['slug']}")
        if suc["slug"] in seen or xf["slug"] in seen:
            raise SystemExit(f"catalog duplicate {suc['slug']} {xf['slug']}")
        seen.add(suc["slug"])
        seen.add(xf["slug"])
        out.append((suc, xf))
    return out


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
        f"field-presence-explicit, not r635 ed2023-legacy-required, not r629 optional drop, "
        f"not r987 enum-to-fixed64-mode / bytes-to-fixed64-hash, not r787–r987 leftover clones.\n"
    )


def write_round(round_n: int, staging: Path) -> None:
    unused = unused_pairs()
    if not unused:
        raise SystemExit(f"no unused catalog pair for r{round_n}")
    suc, xf = unused[0]
    taken = used_slugs()
    for spec in (suc, xf):
        _guard(spec)
        if spec["slug"] in taken:
            raise SystemExit(f"slug already published: {spec['slug']}")
        if spec["slug"] in BANNED_SLUGS:
            raise SystemExit(f"banned slug {spec['slug']!r}")
    srec = success_episode(round_n, suc)
    xrec = handoff_episode(round_n, xf)
    for rec in (srec, xrec):
        blob = json.dumps(rec)
        for bad in (
            "thought",
            "chain_of_thought",
            "scratch",
            "inner_monologue",
            "spike_events",
        ):
            if f'"{bad}"' in blob:
                raise SystemExit(f"{rec['id']} leaked {bad}")
        if "sim_or_real" in blob and '"real"' in blob:
            raise SystemExit(f"{rec['id']} claimed real")
        steps = rec["steps"]
        if not (18 <= len(steps) <= 22):
            raise SystemExit(f"{rec['id']} bad step count {len(steps)}")
        if rec["meta"].get("generator") != "grok-4.6":
            raise SystemExit(f"{rec['id']} bad generator")
        if rec["meta"].get("round") != round_n:
            raise SystemExit(f"{rec['id']} round mismatch")
        if rec["meta"].get("factory") != "proto-breaking-change-factory":
            raise SystemExit(f"{rec['id']} bad factory")
    staging = Path(staging)
    batch = staging / f"batch-r{round_n:02d}.jsonl"
    notes = staging / f"NOTES-r{round_n:02d}.md"
    batch.write_text(
        json.dumps(srec, separators=(",", ":"))
        + "\n"
        + json.dumps(xrec, separators=(",", ":"))
        + "\n"
    )
    notes.write_text(notes_for(round_n, suc, xf, srec, xrec))
    if "Novel coverage:" not in notes.read_text():
        raise SystemExit("notes missing Novel coverage")
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
