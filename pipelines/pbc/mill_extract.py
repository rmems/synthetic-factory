#!/usr/bin/env python3
"""AST-only extract of PBC burst pairs from legacy-mill-lane mill sources."""

from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

if __package__:
    from . import _contract
    from . import generate as gen
else:
    _ROOT = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(_ROOT / "pipelines"))
    import pbc.generate as gen  # type: ignore[no-redef]

SOURCE_REF = "813f93f1969c1c4421e5663492e9663739efa642"
LEGACY = f"origin/legacy-mill-lane"
ENUM_MODE = 'enum Mode { MODE_UNSPECIFIED = 0; MODE_LIVE = 1; MODE_IDLE = 2; }\n'

MILL_SOURCES: tuple[tuple[str, str, int, str], ...] = (
    ("pbc_r701", "experiments/pbc-mill-r701.py", 701, "pairs"),
    ("pbc_r731", "experiments/pbc-mill-r731.py", 731, "pairs"),
    ("pbc_r751", "experiments/pbc-mill-r751.py", 751, "pairs"),
    ("pbc_r803", "experiments/pbc-mill-r803.py", 803, "pairs"),
    ("pbc_r966", "experiments/pbc-mill-r966.py", 966, "pairs"),
    ("pbc_r988", "experiments/pbc-mill-r988.py", 988, "raw988"),
    ("pbc_r2535", "experiments/pbc-mill-r2535.py", 2535, "build2535"),
)

MILL_NOTES: dict[str, tuple[str, str]] = {
    "pbc_r701": ("", ""),
    "pbc_r731": ("", ""),
    "pbc_r751": ("", ""),
    "pbc_r803": ("", ""),
    "pbc_r966": ("", ""),
    "pbc_r988": (
        ", not r987 enum-to-fixed64-mode / bytes-to-fixed64-hash, "
        "not r787–r987 leftover clones",
        "",
    ),
    "pbc_r2535": (
        ", not r1334 map-value-bool-to-sint32 / map-value-bool-to-sint64, "
        "not r987 enum-to-fixed64-mode / bytes-to-fixed64-hash, "
        "not r787–r2534 leftover clones, not r1335 bytesvalue-to-listvalue / "
        "bytesvalue-to-nullvalue wrapper leftovers",
        "- Contract evidence: protobuf wire incompatibility on field tag; "
        "additive migration reserves the number; verify compatible check after "
        "restore.\n",
    ),
}

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


def _legacy_text(path: str) -> str:
    return subprocess.check_output(["git", "show", f"{LEGACY}:{path}"], text=True)


def _const(node: ast.AST, where: str) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Tuple):
        return tuple(_const(elt, where) for elt in node.elts)
    if isinstance(node, ast.List):
        return [_const(elt, where) for elt in node.elts]
    if isinstance(node, ast.Set):
        return {_const(elt, where) for elt in node.elts}
    raise ValueError(f"{where}: not a constant literal")


def _plant_from_call(node: ast.Call, where: str) -> dict[str, Any]:
    if node.args:
        raise ValueError(f"{where}: plant()/ty() must use keywords only")
    func = node.func
    if not isinstance(func, ast.Name) or func.id not in {"plant", "ty"}:
        raise ValueError(f"{where}: expected plant() or ty()")
    kwargs: dict[str, Any] = {}
    for kw in node.keywords:
        if kw.arg is None:
            raise ValueError(f"{where}: invalid **kwargs")
        kwargs[kw.arg] = _const(kw.value, f"{where}.{kw.arg}")
    if func.id == "ty":
        return _ty(**kwargs)
    return gen.plant(**kwargs)


def _ty(
    slug: str,
    short: str,
    told: str,
    tnew: str,
    field: str,
    num: int,
    wold: str,
    wnew: str,
    lang: str,
    ticket: str,
    vs: str,
    avoid: str,
    **extra: object,
) -> dict[str, Any]:
    syntax = str(extra.pop("syntax", 'syntax = "proto3";'))
    buf_rule = str(extra.pop("buf_rule", "FIELD_TYPE / WIRE"))
    freeze = str(extra.pop("freeze", f"{lang} freeze {told} vs {tnew} on {field}"))
    json_name = str(extra.pop("json_name", field + "X"))
    debug = str(extra.pop("debug", "debug_" + short))
    compat = str(extra.pop("compat", f"Dual-read {field} as {told} or {tnew}"))
    grep_pat = str(extra.pop("grep_pat", f"{told} {field}|{tnew} {field}"))
    goal_bit = str(
        extra.pop("goal_bit", f"{told} {field}={num} → {tnew} so freeze {wold} fails")
    )
    dead_desc = str(extra.pop("dead_desc", f"json_name {json_name} as a wire/type substitute"))
    decl_old = str(extra.pop("decl_old", f"{told} {field} = {num};"))
    decl_new = str(extra.pop("decl_new", f"{tnew} {field} = {num};"))
    return gen.plant(
        slug=slug,
        short=short,
        decl_old=decl_old,
        decl_new=decl_new,
        syntax=syntax,
        buf_rule=buf_rule,
        wire_old=wold,
        wire_new=wnew,
        freeze=freeze,
        ticket=ticket,
        lang=lang,
        vs=vs,
        avoid=avoid,
        json_name=json_name,
        debug=debug,
        compat=compat,
        grep_pat=grep_pat,
        goal_bit=goal_bit,
        dead_desc=dead_desc,
        **extra,
    )


def _pairs_node(tree: ast.Module) -> ast.AST:
    for node in tree.body:
        if isinstance(node, ast.Assign):
            names = [t.id for t in node.targets if isinstance(t, ast.Name)]
            if "PAIRS" in names:
                return node.value
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id == "PAIRS" and node.value is not None:
                return node.value
    raise ValueError("no PAIRS assignment")


def _named_constant(tree: ast.Module, name: str) -> Any:
    for node in tree.body:
        if isinstance(node, ast.Assign):
            names = [t.id for t in node.targets if isinstance(t, ast.Name)]
            if name in names:
                return _const(node.value, name)
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id == name and node.value is not None:
                return _const(node.value, name)
    raise ValueError(f"no {name} assignment")


def extract_pairs_list(source: str) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    tree = ast.parse(source)
    payload = _pairs_node(tree)
    if not isinstance(payload, (ast.List, ast.Tuple)):
        raise ValueError("PAIRS must be list or tuple")
    pairs: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for index, item in enumerate(payload.elts):
        if not isinstance(item, (ast.Tuple, ast.List)) or len(item.elts) != 2:
            raise ValueError(f"PAIRS[{index}] must be (ok, bad)")
        ok = _plant_from_call(item.elts[0], f"PAIRS[{index}].ok")
        bad = _plant_from_call(item.elts[1], f"PAIRS[{index}].bad")
        pairs.append((ok, bad))
    return pairs


def _extras_for_r988(slug: str, told: str, tnew: str, field: str, num: int) -> dict[str, Any]:
    extra: dict[str, Any] = {}
    if (
        "Mode" in (told, tnew)
        or slug.startswith("enum-")
        or "-enum-" in slug
        or slug.endswith("-enum-mode")
        or slug.endswith("-enum-port")
        or slug.endswith("-enum-hash")
        or slug.endswith("-enum-crc")
        or slug.endswith("-enum-temp")
        or slug.endswith("-enum-peak")
        or slug.endswith("-enum-armed")
        or slug.endswith("-enum-delta")
        or slug.endswith("-enum-blob")
    ):
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
    imports: list[str] = []
    blob = f"{told} {tnew} {slug}"
    for needle, path in (
        ("Timestamp", "google/protobuf/timestamp.proto"),
        ("Duration", "google/protobuf/duration.proto"),
        ("protobuf.Any", "google/protobuf/any.proto"),
        ("google.protobuf.Any", "google/protobuf/any.proto"),
        ("Struct", "google/protobuf/struct.proto"),
        ("ListValue", "google/protobuf/struct.proto"),
        ("NullValue", "google/protobuf/struct.proto"),
        ("protobuf.Value", "google/protobuf/struct.proto"),
        ("google.protobuf.Value", "google/protobuf/struct.proto"),
        ("Empty", "google/protobuf/empty.proto"),
        ("FieldMask", "google/protobuf/field_mask.proto"),
        ("SourceContext", "google/protobuf/source_context.proto"),
        ("HttpBody", "google/api/httpbody.proto"),
        ("RetryInfo", "google/rpc/error_details.proto"),
        ("TimeZone", "google/type/datetime.proto"),
        ("DayOfWeek", "google/type/dayofweek.proto"),
        ("type.Month", "google/type/month.proto"),
        ("google.type.Month", "google/type/month.proto"),
        ("Fraction", "google/type/fraction.proto"),
        ("LocalizedText", "google/type/localized_text.proto"),
    ):
        if needle in blob and path not in imports:
            imports.append(path)
    if "Value" in blob and "wrappers" not in slug and any(
        token in blob
        for token in (
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
        extra["imports"] = tuple(imports)
    return extra


def extract_r988_pairs(source: str) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    tree = ast.parse(source)
    raw = _named_constant(tree, "RAW")
    if not isinstance(raw, str):
        raise ValueError("RAW must be a string")
    plants: list[dict[str, Any]] = []
    for line in raw.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("|")
        if len(parts) != 11:
            raise ValueError(f"bad RAW row: {line!r}")
        slug, short, told, tnew, field, num_s, wold, wnew, lang, vs, avoid = parts
        num = int(num_s)
        extra = _extras_for_r988(slug, told, tnew, field, num)
        ticket = f"{LANGC[lang]}-{short.upper()}-{num}"
        plants.append(
            _ty(slug, short, told, tnew, field, num, wold, wnew, lang, ticket, vs, avoid, **extra)
        )
    if len(plants) % 2:
        raise ValueError(f"odd plant count {len(plants)}")
    return [(plants[i], plants[i + 1]) for i in range(0, len(plants), 2)]


def _extras_for_r2535(slug: str, told: str, tnew: str, field: str, num: int) -> dict[str, Any]:
    extra: dict[str, Any] = {"field_num": num}
    if "Mode" in (told, tnew) or slug.endswith("-enum") or "-to-enum" in slug:
        extra["extra_msgs"] = ENUM_MODE
        extra.setdefault("grep_pat", f"{told} {field}|{tnew} {field}")
    if slug.startswith("proto2-required-"):
        extra["syntax"] = 'syntax = "proto2";'
        extra["decl_old"] = f"required {told} {field} = {num};"
        extra["decl_new"] = f"required {tnew} {field} = {num};"
        extra["grep_pat"] = f"required {told} {field}|required {tnew} {field}"
        extra["buf_rule"] = "FIELD_TYPE / WIRE"
    if slug.startswith("proto2-optional-"):
        extra["syntax"] = 'syntax = "proto2";'
        extra["decl_old"] = f"optional {told} {field} = {num};"
        extra["decl_new"] = f"optional {tnew} {field} = {num};"
        extra["grep_pat"] = f"optional {told} {field}|optional {tnew} {field}"
        extra["buf_rule"] = "FIELD_TYPE / WIRE"
    imports: list[str] = []
    blob = f"{told} {tnew} {slug}"
    for needle, path in (
        ("google.protobuf.Timestamp", "google/protobuf/timestamp.proto"),
        ("google.protobuf.Duration", "google/protobuf/duration.proto"),
        ("google.protobuf.Any", "google/protobuf/any.proto"),
        ("google.protobuf.Empty", "google/protobuf/empty.proto"),
    ):
        if needle in blob and path not in imports:
            imports.append(path)
    if "google.protobuf.Struct" in blob:
        imports.append("google/protobuf/struct.proto")
    if imports:
        extra["imports"] = tuple(imports)
    return extra


def extract_r2535_pairs(source: str) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    tree = ast.parse(source)
    p2_types = _named_constant(tree, "P2_TYPES")
    wkt_dests = _named_constant(tree, "WKT_DESTS")
    langs = list(LANGC)
    plants: list[dict[str, Any]] = []
    seen_slug: set[str] = set()
    n = 0
    num = 61
    avoid = (
        "map-key ban / r787 leftover / r1334 map-value-bool-to-sint32 / "
        "r1335 wrapper leftover"
    )

    def push(slug: str, told: str, tnew: str, field: str, wold: str, wnew: str, vs: str) -> None:
        nonlocal n, num
        if slug in seen_slug:
            return
        short = f"z{n:04d}"
        lang = langs[n % len(langs)]
        extra = _extras_for_r2535(slug, told, tnew, field, num)
        ticket = f"{LANGC[lang]}-{short.upper()}-{num}"
        plants.append(
            _ty(slug, short, told, tnew, field, num, wold, wnew, lang, ticket, vs, avoid, **extra)
        )
        seen_slug.add(slug)
        n += 1
        num += 1

    for told, wold, field in p2_types:
        for dest_tag, tnew, wnew in wkt_dests:
            if told == tnew:
                continue
            vs = (
                f"proto2 {told}→{dest_tag} TYPE (r1335 skipped WKT dest; "
                f"not optional/required drop)"
            )
            push(f"proto2-required-{told}-to-{dest_tag}", told, tnew, field, wold, wnew, vs)
            push(f"proto2-optional-{told}-to-{dest_tag}", told, tnew, field, wold, wnew, vs)
    if len(plants) % 2:
        plants.pop()
    if not plants:
        raise ValueError("no r2535 plants")
    return [(plants[i], plants[i + 1]) for i in range(0, len(plants), 2)]


def extract_mill(mill_id: str, source_path: str, kind: str) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    text = _legacy_text(source_path)
    ast.parse(text)
    if kind == "pairs":
        return extract_pairs_list(text)
    if kind == "raw988":
        return extract_r988_pairs(text)
    if kind == "build2535":
        return extract_r2535_pairs(text)
    raise ValueError(f"unknown extract kind {kind!r}")


def _plant_json(plant: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in plant.items():
        if key == "imports" and isinstance(value, tuple):
            out[key] = list(value)
        elif value == "" and key.startswith("dead_"):
            continue
        elif value == () and key == "imports":
            continue
        else:
            out[key] = value
    return out


def pair_row(
    mill_id: str,
    catalog_first: int,
    full_n_rounds: int,
    ok: dict[str, Any],
    bad: dict[str, Any],
) -> dict[str, Any]:
    notes_extra, notes_footer = MILL_NOTES.get(mill_id, ("", ""))
    return {
        "mill_id": mill_id,
        "catalog_first": catalog_first,
        "start": catalog_first,
        "full_n_rounds": full_n_rounds,
        "notes_extra": notes_extra,
        "notes_footer": notes_footer,
        "ok": _plant_json(ok),
        "bad": _plant_json(bad),
    }


def build_plants_jsonl() -> str:
    rows: list[dict[str, Any]] = []
    counts: dict[str, int] = {}
    for mill_id, source_path, catalog_first, kind in MILL_SOURCES:
        pairs = extract_mill(mill_id, source_path, kind)
        counts[mill_id] = len(pairs)
        for ok, bad in pairs:
            rows.append(pair_row(mill_id, catalog_first, len(pairs), ok, bad))
    expected = 533
    if len(rows) != expected:
        raise SystemExit(f"expected {expected} catalog rows, got {len(rows)}: {counts}")
    lines = [json.dumps(row, separators=(",", ":"), ensure_ascii=False) for row in rows]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    out_path = Path(__file__).resolve().parent / "plants.jsonl"
    if argv and argv[0] == "--stdout":
        sys.stdout.write(build_plants_jsonl())
        return 0
    out_path.write_text(build_plants_jsonl(), encoding="utf-8")
    print(f"wrote {out_path} ({out_path.read_text().count(chr(10))} lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

if __package__:
    _contract.bind_import_twin(__name__)
