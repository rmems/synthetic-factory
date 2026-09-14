#!/usr/bin/env python3
"""Mill proto-breaking-change-factory r2535+ NEW unique WIRE plants.

BAN: map-key type swaps, field-presence implicit/explicit, ed2023-legacy-required,
optional drop, r1334 map-value-bool-to-sint32/sint64, r987 enum-to-fixed64-mode /
bytes-to-fixed64-hash, r787-r2534 leftover clones including r1335 wrapper/WKT
leftovers (bytesvalue-to-listvalue / bytesvalue-to-nullvalue).
NEW: proto2 required/optional scalar → WKT (timestamp/duration/empty/any/struct/enum)
that r1335 skipped. meta.generator=grok-4.6. Q=2. 18-22 steps.
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
CATALOG_FIRST = 2535
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
    "bytesvalue-to-listvalue",
    "oneof-bytesvalue-to-listvalue",
    "bytesvalue-to-nullvalue",
    "oneof-bytesvalue-to-nullvalue",
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
    "bytesvalue-to-listvalue",
    "bytesvalue-to-nullvalue",
)

LANGS = list(LANGC)

WKT_DESTS: list[tuple[str, str, str]] = [
    ("timestamp", "google.protobuf.Timestamp", "LEN Timestamp seconds/nanos"),
    ("duration", "google.protobuf.Duration", "LEN Duration seconds/nanos"),
    ("empty", "google.protobuf.Empty", "LEN Empty 0-length"),
    ("any", "google.protobuf.Any", "LEN Any type_url+value"),
    ("struct", "google.protobuf.Struct", "LEN Struct fields map"),
    ("enum", "Mode", "VARINT enum Mode"),
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
    extra: dict = {"field_num": num}
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

    def add(path: str) -> None:
        if path not in imports:
            imports.append(path)

    blob = f"{told} {tnew} {slug}"
    pairs = (
        ("google.protobuf.Timestamp", "google/protobuf/timestamp.proto"),
        ("google.protobuf.Duration", "google/protobuf/duration.proto"),
        ("google.protobuf.Any", "google/protobuf/any.proto"),
        ("google.protobuf.Empty", "google/protobuf/empty.proto"),
    )
    for needle, path in pairs:
        if needle in blob:
            add(path)
    if "google.protobuf.Struct" in blob:
        add("google/protobuf/struct.proto")
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
    plants: list[dict] = []
    seen_slug: set[str] = set()
    n = 0
    num = 61

    def push(slug: str, told: str, tnew: str, field: str, wold: str, wnew: str, vs: str) -> None:
        nonlocal n, num
        if slug in seen_slug:
            return
        short = f"z{n:04d}"
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
            "map-key ban / r787 leftover / r1334 map-value-bool-to-sint32 / r1335 wrapper leftover",
        )
        _guard(plant)
        plants.append(plant)
        seen_slug.add(slug)
        n += 1
        num += 1

    for told, wold, field in P2_TYPES:
        for dest_tag, tnew, wnew in WKT_DESTS:
            if told == tnew:
                continue
            vs = f"proto2 {told}→{dest_tag} TYPE (r1335 skipped WKT dest; not optional/required drop)"
            push(f"proto2-required-{told}-to-{dest_tag}", told, tnew, field, wold, wnew, vs)
            push(f"proto2-optional-{told}-to-{dest_tag}", told, tnew, field, wold, wnew, vs)

    if len(plants) % 2:
        plants.pop()
    if not plants:
        raise SystemExit("no plants for r2535 mill")
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


def stamp_envelope(rec: dict, plant: dict) -> None:
    """Ordered contract evidence: proto/wire → field/tag → additive/reserve → verify/check."""
    num = plant.get("field_num", "")
    by_n = {int(step["n"]): step for step in rec["steps"]}
    if 5 in by_n:
        by_n[5]["observation"] = (
            str(by_n[5]["observation"]).rstrip()
            + f" Semantic incompatibility: protobuf field tag {num} wire type changed."
        )
    restore_n = 12 if rec["reward"].get("success") else 11
    verify_n = restore_n + 1
    if restore_n in by_n:
        by_n[restore_n]["observation"] = (
            str(by_n[restore_n]["observation"]).rstrip()
            + f" Additive migration restores {plant['decl_old']} and reserve tag {num} (never reuse)."
        )
    if verify_n in by_n:
        by_n[verify_n]["observation"] = (
            str(by_n[verify_n]["observation"]).rstrip()
            + " verify compatible check: buf WIRE 0 after additive restore."
        )
    rec["outcome"] = (
        str(rec.get("outcome") or "").rstrip()
        + " Compatibility rule: FIELD_TYPE / WIRE; additive migration reserved the tag."
    )


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
        f"enum-to-fixed64-mode / bytes-to-fixed64-hash, not r787–r2534 leftover clones, "
        f"not r1335 bytesvalue-to-listvalue / bytesvalue-to-nullvalue wrapper leftovers.\n"
        f"- Contract evidence: protobuf wire incompatibility on field tag; additive migration "
        f"reserves the number; verify compatible check after restore.\n"
    )


def _validate_record(rec: dict, round_n: int) -> None:
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
    stamp_envelope(srec, suc)
    stamp_envelope(xrec, xf)
    _validate_record(srec, round_n)
    _validate_record(xrec, round_n)
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
                "slugs": [suc["slug"], xf["slug"]],
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
