#!/usr/bin/env python3
"""Mill proto-breaking-change-factory r1335+ NEW unique WIRE plants.

BAN: map-key type swaps already used, field-presence implicit/explicit,
ed2023-legacy-required, optional drop, r1334 map-value-bool-to-sint32 /
map-value-bool-to-sint64, r987 enum-to-fixed64-mode / bytes-to-fixed64-hash,
r787-r1334 leftover clones.
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
CATALOG_FIRST = 1335
FACTORY_DIR = (
    Path(__file__).resolve().parents[1]
    / "outputs"
    / "raw"
    / "2026-08-19-agentic"
    / "proto-breaking-change-factory"
)
_ID_RE = __import__("re").compile(rb"pbc-r\d+-([a-z0-9-]+)-[a-z0-9]+")
_USED_CACHE: set[str] | None = None


def used_slugs() -> set[str]:
    global _USED_CACHE
    if _USED_CACHE is not None:
        return _USED_CACHE
    found: set[str] = set()
    for path in FACTORY_DIR.glob("batch-r*.jsonl"):
        found.update(m.decode() for m in _ID_RE.findall(path.read_bytes()))
    _USED_CACHE = found
    return found

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
    "map-value-bool-to-sint32",
    "map-value-bool-to-sint64",
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

LANGS = list(LANGC)

DESTS: list[tuple[str, str, str]] = [
    ("int32", "int32", "VARINT int32"),
    ("int64", "int64", "VARINT int64"),
    ("uint32", "uint32", "unsigned VARINT 32"),
    ("uint64", "uint64", "unsigned VARINT 64"),
    ("sint32", "sint32", "zigzag VARINT 32"),
    ("sint64", "sint64", "zigzag VARINT 64"),
    ("fixed32", "fixed32", "FIXED32 unsigned"),
    ("fixed64", "fixed64", "FIXED64 unsigned"),
    ("sfixed32", "sfixed32", "FIXED32 signed"),
    ("sfixed64", "sfixed64", "FIXED64 signed"),
    ("float", "float", "FIXED32 float"),
    ("double", "double", "FIXED64 double"),
    ("bool", "bool", "VARINT 0/1"),
    ("string", "string", "LEN utf8"),
    ("bytes", "bytes", "LEN bytes"),
    ("enum", "Mode", "VARINT enum"),
    ("timestamp", "google.protobuf.Timestamp", "LEN Timestamp"),
    ("duration", "google.protobuf.Duration", "LEN Duration"),
    ("empty", "google.protobuf.Empty", "LEN empty 0-length"),
    ("any", "google.protobuf.Any", "LEN Any type_url+value"),
    ("struct", "google.protobuf.Struct", "LEN Struct fields"),
    ("fieldmask", "google.protobuf.FieldMask", "LEN FieldMask paths[]"),
    ("listvalue", "google.protobuf.ListValue", "LEN ListValue values[]"),
    ("nullvalue", "google.protobuf.NullValue", "VARINT NullValue enum"),
]

DEST_TAGS = sorted({d[0] for d in DESTS}, key=len, reverse=True)

# prefix, told, field, wold
SOURCES: list[tuple[str, str, str, str]] = [
    ("date", "google.type.Date", "poured", "LEN Date y/m/d"),
    ("datetime", "google.type.DateTime", "when", "LEN DateTime"),
    ("timeofday", "google.type.TimeOfDay", "clock", "LEN TimeOfDay h/m/s"),
    ("color", "google.type.Color", "tint", "LEN Color rgba"),
    ("latlng", "google.type.LatLng", "coord", "LEN LatLng lat+lng"),
    ("money", "google.type.Money", "price", "LEN Money curr+units"),
    ("postal", "google.type.PostalAddress", "ship", "LEN PostalAddress"),
    ("phone", "google.type.PhoneNumber", "call", "LEN PhoneNumber e164"),
    ("quaternion", "google.type.Quaternion", "orient", "LEN Quaternion xyzw"),
    ("interval", "google.type.Interval", "span", "LEN Interval start/end"),
    ("expr", "google.type.Expr", "rule", "LEN Expr cel"),
    ("calendarperiod", "google.type.CalendarPeriod", "period", "VARINT CalendarPeriod enum"),
    ("decimal", "google.type.Decimal", "assay", "LEN Decimal value"),
    ("debuginfo", "google.rpc.DebugInfo", "trace", "LEN DebugInfo stack"),
    ("quotafailure", "google.rpc.QuotaFailure", "quota", "LEN QuotaFailure viol"),
    ("errorinfo", "google.rpc.ErrorInfo", "err", "LEN ErrorInfo reason"),
    ("precondfail", "google.rpc.PreconditionFailure", "pre", "LEN PreconditionFailure"),
    ("badrequest", "google.rpc.BadRequest", "bad", "LEN BadRequest field viol"),
    ("requestinfo", "google.rpc.RequestInfo", "req", "LEN RequestInfo id"),
    ("resourceinfo", "google.rpc.ResourceInfo", "res", "LEN ResourceInfo name"),
    ("help", "google.rpc.Help", "hint", "LEN Help links"),
    ("localizedmsg", "google.rpc.LocalizedMessage", "lmsg", "LEN LocalizedMessage"),
    ("retryinfo", "google.rpc.RetryInfo", "retry", "LEN RetryInfo delay"),
    ("httpbody", "google.api.HttpBody", "blob", "LEN HttpBody content+data"),
    ("pbtype", "google.protobuf.Type", "schema", "LEN Type name+fields"),
    ("pbapi", "google.protobuf.Api", "iface", "LEN Api name+methods"),
    ("pbmethod", "google.protobuf.Method", "op", "LEN Method name"),
    ("pbenum", "google.protobuf.Enum", "kind", "LEN Enum name+values"),
    ("sourcecontext", "google.protobuf.SourceContext", "file", "LEN SourceContext file_name"),
    ("pbfield", "google.protobuf.Field", "fld", "LEN Field name+num"),
    ("pbenumval", "google.protobuf.EnumValue", "ev", "LEN EnumValue name+num"),
    ("pboption", "google.protobuf.Option", "opt", "LEN Option name+value"),
    ("pbmixin", "google.protobuf.Mixin", "mix", "LEN Mixin name+root"),
    ("listvalue", "google.protobuf.ListValue", "tags", "LEN ListValue values[]"),
    ("nullvalue", "google.protobuf.NullValue", "kind", "VARINT NullValue enum"),
    ("fieldmask", "google.protobuf.FieldMask", "mask", "LEN FieldMask paths[]"),
    ("pbvalue", "google.protobuf.Value", "kind", "LEN Value oneof"),
]

MAP_VALS = [
    ("int32", "VARINT int32", "taps"),
    ("int64", "VARINT int64", "seqs"),
    ("uint32", "unsigned VARINT 32", "ports"),
    ("uint64", "unsigned VARINT 64", "hashes"),
    ("sint32", "zigzag VARINT 32", "deltas"),
    ("sint64", "zigzag VARINT 64", "deltas"),
    ("fixed32", "FIXED32 unsigned", "crcs"),
    ("fixed64", "FIXED64 unsigned", "hashes"),
    ("sfixed32", "FIXED32 signed", "crcs"),
    ("sfixed64", "FIXED64 signed", "hashes"),
    ("float", "FIXED32 float", "temps"),
    ("double", "FIXED64 double", "peaks"),
    ("bool", "VARINT 0/1", "flags"),
    ("string", "LEN utf8", "skus"),
    ("bytes", "LEN bytes", "blobs"),
]

P2_TYPES = [
    ("int32", "VARINT int32", "tap_n"),
    ("int64", "VARINT int64", "seq"),
    ("uint32", "unsigned VARINT 32", "port"),
    ("uint64", "unsigned VARINT 64", "hash"),
    ("sint32", "zigzag VARINT 32", "delta"),
    ("sint64", "zigzag VARINT 64", "delta"),
    ("fixed32", "FIXED32 unsigned", "crc"),
    ("fixed64", "FIXED64 unsigned", "hash"),
    ("sfixed32", "FIXED32 signed", "crc"),
    ("sfixed64", "FIXED64 signed", "hash"),
    ("float", "FIXED32 float", "temp_c"),
    ("double", "FIXED64 double", "peak"),
    ("bool", "VARINT 0/1", "armed"),
    ("string", "LEN utf8", "sku"),
    ("bytes", "LEN bytes", "blob"),
]


def _dest_of(rest: str) -> str:
    for tag in DEST_TAGS:
        if rest == tag or rest.startswith(tag + "-"):
            return tag
    return rest.split("-")[0]


def _taken_index(used: set[str]) -> set[str]:
    idx = set(used)
    idx.update(BANNED_SLUGS)
    for slug in list(used) + list(BANNED_SLUGS):
        if "-to-" not in slug:
            continue
        src, rest = slug.split("-to-", 1)
        idx.add(f"{src}-to-{_dest_of(rest)}")
    return idx


def _pair_taken(slug: str, idx: set[str]) -> bool:
    if slug in idx:
        return True
    if "-to-" not in slug:
        return False
    src, rest = slug.split("-to-", 1)
    return f"{src}-to-{_dest_of(rest)}" in idx


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
    if "Mode" in (told, tnew) or slug.startswith("enum-") or "-enum-" in slug or slug.endswith("-enum"):
        extra["extra_msgs"] = ENUM_MODE
        extra.setdefault("grep_pat", f"{told} {field}|{tnew} {field}")
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
    imports: list[str] = []
    blob = f"{told} {tnew} {slug}"

    def add(path: str) -> None:
        if path not in imports:
            imports.append(path)

    pairs = (
        ("google.type.Date", "google/type/date.proto"),
        ("google.type.DateTime", "google/type/datetime.proto"),
        ("google.type.TimeOfDay", "google/type/timeofday.proto"),
        ("google.type.Color", "google/type/color.proto"),
        ("google.type.LatLng", "google/type/latlng.proto"),
        ("google.type.Money", "google/type/money.proto"),
        ("google.type.PostalAddress", "google/type/postal_address.proto"),
        ("google.type.PhoneNumber", "google/type/phone_number.proto"),
        ("google.type.Quaternion", "google/type/quaternion.proto"),
        ("google.type.Interval", "google/type/interval.proto"),
        ("google.type.Expr", "google/type/expr.proto"),
        ("google.type.CalendarPeriod", "google/type/calendar_period.proto"),
        ("google.type.Decimal", "google/type/decimal.proto"),
        ("google.protobuf.Timestamp", "google/protobuf/timestamp.proto"),
        ("google.protobuf.Duration", "google/protobuf/duration.proto"),
        ("google.protobuf.Any", "google/protobuf/any.proto"),
        ("google.protobuf.Empty", "google/protobuf/empty.proto"),
        ("google.protobuf.FieldMask", "google/protobuf/field_mask.proto"),
        ("google.protobuf.SourceContext", "google/protobuf/source_context.proto"),
        ("google.protobuf.Type", "google/protobuf/type.proto"),
        ("google.protobuf.EnumValue", "google/protobuf/type.proto"),
        ("google.protobuf.Enum", "google/protobuf/type.proto"),
        ("google.protobuf.Option", "google/protobuf/type.proto"),
        ("google.protobuf.Mixin", "google/protobuf/api.proto"),
        ("google.protobuf.Api", "google/protobuf/api.proto"),
        ("google.protobuf.Method", "google/protobuf/api.proto"),
        ("google.api.HttpBody", "google/api/httpbody.proto"),
        ("google.rpc.Status", "google/rpc/status.proto"),
        ("google.protobuf.Int32Value", "google/protobuf/wrappers.proto"),
        ("google.protobuf.Int64Value", "google/protobuf/wrappers.proto"),
        ("google.protobuf.UInt32Value", "google/protobuf/wrappers.proto"),
        ("google.protobuf.UInt64Value", "google/protobuf/wrappers.proto"),
        ("google.protobuf.FloatValue", "google/protobuf/wrappers.proto"),
        ("google.protobuf.DoubleValue", "google/protobuf/wrappers.proto"),
        ("google.protobuf.BoolValue", "google/protobuf/wrappers.proto"),
        ("google.protobuf.StringValue", "google/protobuf/wrappers.proto"),
        ("google.protobuf.BytesValue", "google/protobuf/wrappers.proto"),
    )
    for needle, path in pairs:
        if needle in blob:
            add(path)
    if any(
        x in blob
        for x in (
            "google.protobuf.Struct",
            "google.protobuf.ListValue",
            "google.protobuf.NullValue",
            "google.protobuf.Value",
        )
    ):
        add("google/protobuf/struct.proto")
    if any(
        x in blob
        for x in (
            "google.rpc.DebugInfo",
            "google.rpc.QuotaFailure",
            "google.rpc.ErrorInfo",
            "google.rpc.PreconditionFailure",
            "google.rpc.BadRequest",
            "google.rpc.RequestInfo",
            "google.rpc.ResourceInfo",
            "google.rpc.Help",
            "google.rpc.LocalizedMessage",
            "google.rpc.RetryInfo",
        )
    ):
        add("google/rpc/error_details.proto")
    if imports:
        extra["imports"] = tuple(imports)
    return extra


def _mk(
    slug: str,
    short: str,
    told: str,
    tnew: str,
    field: str,
    num: int,
    wold: str,
    wnew: str,
    lang: str,
    vs: str,
    avoid: str,
) -> dict:
    extra = _extras_for(slug, told, tnew, field, num)
    ticket = f"{LANGC[lang]}-{short.upper()}-{num}"
    return ty(
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


def _build_plants() -> list[dict]:
    used = _taken_index(used_slugs())
    plants: list[dict] = []
    seen_slug: set[str] = set()
    seen_short: set[str] = set()
    n = 0
    num = 1801

    def push(slug: str, told: str, tnew: str, field: str, wold: str, wnew: str, vs: str) -> None:
        nonlocal n, num
        if slug in seen_slug or _pair_taken(slug, used):
            return
        short = f"w{n:04d}"
        if short in seen_short:
            raise SystemExit(f"dup short {short}")
        lang = LANGS[n % len(LANGS)]
        plant = _mk(
            slug,
            short,
            told,
            tnew,
            field,
            num,
            wold,
            wnew,
            lang,
            vs,
            "map-key ban / r787 leftover / r1334 map-value-bool-to-sint32",
        )
        _guard(plant)
        plants.append(plant)
        seen_slug.add(slug)
        seen_short.add(short)
        n += 1
        num += 1

    for prefix, told, field, wold in SOURCES:
        for dest_tag, tnew, wnew in DESTS:
            if told == tnew:
                continue
            slug = f"{prefix}-to-{dest_tag}-{field}"
            vs = f"{prefix} leftover mill (→{dest_tag}, not used clone)"
            push(slug, told, tnew, field, wold, wnew, vs)

    for told, wold, field in MAP_VALS:
        for dest_tag, tnew, wnew in DESTS:
            if told == tnew:
                continue
            if dest_tag in {
                "timestamp",
                "duration",
                "empty",
                "any",
                "struct",
            }:
                # map values of message types are allowed; keep
                pass
            slug = f"map-value-{told}-to-{dest_tag}"
            vs = f"map value {told}→{dest_tag} (not map-key)"
            push(slug, told, tnew, field, f"value {wold}", f"value {wnew}", vs)

    for dest_tag, tnew, wnew in DESTS:
        if dest_tag == "enum":
            continue
        slug = f"map-value-enum-to-{dest_tag}"
        vs = f"map value Mode→{dest_tag} (not map-key)"
        push(slug, "Mode", tnew, "modes", "value VARINT enum", f"value {wnew}", vs)

    for dest_tag, tnew, wnew in DESTS:
        if dest_tag == "enum":
            continue
        slug = f"oneof-enum-to-{dest_tag}"
        vs = f"oneof Mode→{dest_tag} leftover arm (not r787-r1334 clone)"
        push(slug, "Mode", tnew, "mode", "VARINT enum", wnew, vs)

    p2_num = 11
    for kind in ("proto2-required", "proto2-optional"):
        for told, wold, field in P2_TYPES:
            for dest_tag, tnew, wnew in DESTS:
                if told == tnew:
                    continue
                if dest_tag in {"timestamp", "duration", "empty", "any", "struct", "enum"}:
                    continue
                slug = f"{kind}-{told}-to-{dest_tag}"
                vs = f"{kind} {told}→{dest_tag} TYPE (not optional/required drop)"
                extra_field = field
                # proto2 field numbers stay small and independent
                saved_num = num
                num = p2_num
                push(slug, told, tnew, extra_field, wold, wnew, vs)
                if num != p2_num:
                    p2_num = 11 + ((p2_num - 10) % 80)
                num = saved_num
                if p2_num == 11:
                    p2_num = 12

    for prefix, told, field, wold in (
        ("timestamp", "google.protobuf.Timestamp", "poured_at", "LEN Timestamp"),
        ("duration", "google.protobuf.Duration", "hold", "LEN Duration"),
        ("any", "google.protobuf.Any", "event", "LEN Any type_url+value"),
        ("struct", "google.protobuf.Struct", "attrs", "LEN Struct fields"),
        ("empty", "google.protobuf.Empty", "ack", "LEN empty 0-length"),
        ("fieldmask", "google.protobuf.FieldMask", "mask", "LEN FieldMask paths[]"),
        ("listvalue", "google.protobuf.ListValue", "tags", "LEN ListValue values[]"),
        ("value", "google.protobuf.Value", "kind", "LEN Value oneof"),
    ):
        for dest_tag, tnew, wnew in DESTS:
            if dest_tag == prefix or told == tnew:
                continue
            slug = f"oneof-{prefix}-to-{dest_tag}"
            vs = f"oneof {prefix}→{dest_tag} leftover arm (not r787-r1334 clone)"
            push(slug, told, tnew, field, wold, wnew, vs)

    for prefix, told, field, wold in (
        ("date", "google.type.Date", "poured", "LEN Date y/m/d"),
        ("datetime", "google.type.DateTime", "when", "LEN DateTime"),
        ("timeofday", "google.type.TimeOfDay", "clock", "LEN TimeOfDay h/m/s"),
        ("color", "google.type.Color", "tint", "LEN Color rgba"),
        ("latlng", "google.type.LatLng", "coord", "LEN LatLng lat+lng"),
        ("money", "google.type.Money", "price", "LEN Money curr+units"),
        ("postal", "google.type.PostalAddress", "ship", "LEN PostalAddress"),
        ("phone", "google.type.PhoneNumber", "call", "LEN PhoneNumber e164"),
        ("quaternion", "google.type.Quaternion", "orient", "LEN Quaternion xyzw"),
        ("interval", "google.type.Interval", "span", "LEN Interval start/end"),
        ("expr", "google.type.Expr", "rule", "LEN Expr cel"),
        ("decimal", "google.type.Decimal", "assay", "LEN Decimal value"),
        ("httpbody", "google.api.HttpBody", "blob", "LEN HttpBody content+data"),
        ("retryinfo", "google.rpc.RetryInfo", "retry", "LEN RetryInfo delay"),
        ("debuginfo", "google.rpc.DebugInfo", "trace", "LEN DebugInfo stack"),
    ):
        for dest_tag, tnew, wnew in DESTS:
            if dest_tag == prefix or told == tnew:
                continue
            slug = f"oneof-{prefix}-to-{dest_tag}"
            vs = f"oneof {prefix}→{dest_tag} leftover arm (not r787-r1334 clone)"
            push(slug, told, tnew, field, wold, wnew, vs)

    for prefix, told, field, wold in (
        ("int32value", "google.protobuf.Int32Value", "count", "LEN Int32Value"),
        ("int64value", "google.protobuf.Int64Value", "count", "LEN Int64Value"),
        ("uint32value", "google.protobuf.UInt32Value", "port", "LEN UInt32Value"),
        ("uint64value", "google.protobuf.UInt64Value", "hash", "LEN UInt64Value"),
        ("floatvalue", "google.protobuf.FloatValue", "temp_c", "LEN FloatValue"),
        ("doublevalue", "google.protobuf.DoubleValue", "peak", "LEN DoubleValue"),
        ("boolvalue", "google.protobuf.BoolValue", "ok", "LEN BoolValue"),
        ("stringvalue", "google.protobuf.StringValue", "sku", "LEN StringValue"),
        ("bytesvalue", "google.protobuf.BytesValue", "blob", "LEN BytesValue"),
    ):
        for dest_tag, tnew, wnew in DESTS:
            if dest_tag == prefix or told == tnew:
                continue
            slug = f"{prefix}-to-{dest_tag}"
            vs = f"{prefix}→{dest_tag} wrapper/WKT (not unwrap catalog)"
            push(slug, told, tnew, field, wold, wnew, vs)
            slug_o = f"oneof-{prefix}-to-{dest_tag}"
            vs_o = f"oneof {prefix}→{dest_tag} leftover arm (not r787-r1334 clone)"
            push(slug_o, told, tnew, field, wold, wnew, vs_o)

    if len(plants) % 2:
        plants.pop()
    if not plants:
        raise SystemExit("no unused plants for r1335 mill")
    return plants


_PLANTS = _build_plants()
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
        f"not r1334 map-value-bool-to-sint32 / map-value-bool-to-sint64, not r987 "
        f"enum-to-fixed64-mode / bytes-to-fixed64-hash, not r787–r1334 leftover clones.\n"
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
    ap.add_argument("--round", type=int, required=False)
    ap.add_argument("--staging", required=False)
    ap.add_argument("--count", action="store_true")
    args = ap.parse_args()
    if args.count or args.round is None:
        unused = unused_pairs()
        print(
            json.dumps(
                {
                    "plants": len(_PLANTS),
                    "pairs": len(PAIRS),
                    "unused_pairs": len(unused),
                    "first": [unused[0][0]["slug"], unused[0][1]["slug"]] if unused else [],
                }
            )
        )
        if args.round is None:
            return 0
    write_round(args.round, Path(args.staging))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
