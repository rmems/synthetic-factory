#!/usr/bin/env python3
"""AST-only extract of PBC burst pairs from legacy-mill-lane mill sources."""

from __future__ import annotations

import ast
import json
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any, TypeGuard

if __package__:
    from . import _contract
    from . import generate as gen
else:
    _ROOT = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(_ROOT / "pipelines"))
    import pbc.generate as gen  # type: ignore[no-redef]

SOURCE_REF = "813f93f1969c1c4421e5663492e9663739efa642"
LEGACY = "origin/legacy-mill-lane"
ENUM_MODE = 'enum Mode { MODE_UNSPECIFIED = 0; MODE_LIVE = 1; MODE_IDLE = 2; }\n'

MILL_SOURCES: tuple[tuple[str, str, int, str], ...] = (
    ("pbc_r701", "experiments/pbc-mill-r701.py", 701, "pairs"),
    ("pbc_r731", "experiments/pbc-mill-r731.py", 731, "pairs"),
    ("pbc_r751", "experiments/pbc-mill-r751.py", 751, "pairs"),
    ("pbc_r787", "experiments/pbc-mill-r787.py", 787, "pairs"),
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
    for ref in (SOURCE_REF, LEGACY):
        try:
            return subprocess.check_output(["git", "show", f"{ref}:{path}"], text=True)
        except subprocess.CalledProcessError:
            continue
    raise FileNotFoundError(f"git show failed for {path} at {SOURCE_REF} and {LEGACY}")


def _const(node: ast.AST, where: str, *, env: dict[str, Any] | None = None) -> Any:
    # Recursion stays here, so a `+` / list / set level costs one frame and a tuple level
    # two (``_const_tuple`` is the frame its generator cost), as before the helpers were
    # split out. The other helpers below never recurse.
    if isinstance(node, ast.Constant):
        return node.value
    if _is_concatenation(node):
        left = _const(node.left, where, env=env)
        return _concatenated(left, _const(node.right, where, env=env), where)
    if isinstance(node, ast.Tuple):
        return _const_tuple(node, where, env)
    if isinstance(node, (ast.List, ast.Set)):
        return (
            [_const(elt, where, env=env) for elt in node.elts]
            if isinstance(node, ast.List)
            else {_const(elt, where, env=env) for elt in node.elts}
        )
    return _bound_name(node, where, env)


def _const_tuple(node: ast.Tuple, where: str, env: dict[str, Any] | None) -> tuple[Any, ...]:
    return tuple([_const(elt, where, env=env) for elt in node.elts])


def _is_concatenation(node: ast.AST) -> TypeGuard[ast.BinOp]:
    return isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add)


def _concatenated(left: Any, right: Any, where: str) -> str:
    if isinstance(left, str) and isinstance(right, str):
        return left + right
    raise ValueError(f"{where}: not a constant literal")


def _bound_name(node: ast.AST, where: str, env: dict[str, Any] | None) -> Any:
    """A name bound in ``env``; any other node is not a constant literal."""

    names = env if env is not None else {}
    if isinstance(node, ast.Name) and node.id in names:
        return names[node.id]
    raise ValueError(f"{where}: not a constant literal")


def _simple_assignment(node: ast.stmt) -> tuple[str | None, ast.AST | None]:
    """Return the first plain-name target of a module-level assignment and its value."""

    if isinstance(node, ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name):
                return target.id, node.value
        return None, None
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        return node.target.id, node.value
    return None, None


def _string_constant_env(tree: ast.Module) -> dict[str, Any]:
    env: dict[str, Any] = {}
    for node in tree.body:
        name, value = _simple_assignment(node)
        if name is None or value is None:
            continue
        try:
            env[name] = _const(value, name, env=env)
        except ValueError:
            continue
    return env


_TY_POS = (
    "slug",
    "short",
    "told",
    "tnew",
    "field",
    "num",
    "wold",
    "wnew",
    "lang",
    "ticket",
    "vs",
    "avoid",
)


def _positional_kwargs(
    func_id: str, args: list[ast.expr], where: str, env: dict[str, Any] | None
) -> dict[str, Any]:
    kwargs: dict[str, Any] = {}
    if not args:
        return kwargs
    if func_id != "ty":
        raise ValueError(f"{where}: plant()/ty() must use keywords only")
    for index, arg in enumerate(args):
        if index >= len(_TY_POS):
            raise ValueError(f"{where}: too many positional args for ty()")
        kwargs[_TY_POS[index]] = _const(arg, f"{where}.{_TY_POS[index]}", env=env)
    return kwargs


def _plant_from_call(node: ast.Call, where: str, *, env: dict[str, Any] | None = None) -> dict[str, Any]:
    func = node.func
    if not isinstance(func, ast.Name) or func.id not in {"plant", "ty"}:
        raise ValueError(f"{where}: expected plant() or ty()")
    kwargs = _positional_kwargs(func.id, node.args, where, env)
    for kw in node.keywords:
        if kw.arg is None:
            raise ValueError(f"{where}: invalid **kwargs")
        kwargs[kw.arg] = _const(kw.value, f"{where}.{kw.arg}", env=env)
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


def _assignment_value(node: ast.stmt, name: str) -> ast.AST | None:
    if isinstance(node, ast.Assign):
        names = [t.id for t in node.targets if isinstance(t, ast.Name)]
        return node.value if name in names else None
    if not isinstance(node, ast.AnnAssign) or not isinstance(node.target, ast.Name):
        return None
    return node.value if node.target.id == name else None


def _assigned_value(tree: ast.Module, name: str) -> ast.AST | None:
    """Value of the first module-level ``name = ...`` / ``name: T = ...`` assignment."""

    for node in tree.body:
        value = _assignment_value(node, name)
        if value is not None:
            return value
    return None


def _pairs_node(tree: ast.Module) -> ast.AST:
    value = _assigned_value(tree, "PAIRS")
    if value is None:
        raise ValueError("no PAIRS assignment")
    return value


def _named_constant(tree: ast.Module, name: str) -> Any:
    value = _assigned_value(tree, name)
    if value is None:
        raise ValueError(f"no {name} assignment")
    return _const(value, name)


def extract_pairs_list(source: str) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    tree = ast.parse(source)
    env = _string_constant_env(tree)
    payload = _pairs_node(tree)
    if not isinstance(payload, (ast.List, ast.Tuple)):
        raise ValueError("PAIRS must be list or tuple")
    pairs: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for index, item in enumerate(payload.elts):
        if not isinstance(item, (ast.Tuple, ast.List)) or len(item.elts) != 2:
            raise ValueError(f"PAIRS[{index}] must be (ok, bad)")
        ok = _plant_from_call(item.elts[0], f"PAIRS[{index}].ok", env=env)
        bad = _plant_from_call(item.elts[1], f"PAIRS[{index}].bad", env=env)
        pairs.append((ok, bad))
    return pairs


_ShapeRules = tuple[tuple[tuple[str, str, str], tuple[tuple[str, str], ...]], ...]

_R988_ENUM_SUFFIXES = (
    "-enum-mode",
    "-enum-port",
    "-enum-hash",
    "-enum-crc",
    "-enum-temp",
    "-enum-peak",
    "-enum-armed",
    "-enum-delta",
    "-enum-blob",
)


def _proto2_label_rule(label: str) -> tuple[tuple[str, str], ...]:
    return (
        ("syntax", 'syntax = "proto2";'),
        ("decl_old", label + " {told} {field} = {num};"),
        ("decl_new", label + " {tnew} {field} = {num};"),
        ("grep_pat", label + " {told} {field}|" + label + " {tnew} {field}"),
    )


# (prefix, substring, suffix) -> ordered str.format field templates. Rules apply in
# order, so a later matching rule overwrites an earlier one key by key, exactly as the
# mill's sequential ifs did.
_R988_SHAPE_RULES: _ShapeRules = (
    (("singular-", "repeated", ""), (("buf_rule", "FIELD_CARDINALITY / WIRE"),)),
    (
        ("repeated-", "", "-singular"),
        (
            ("buf_rule", "FIELD_CARDINALITY / WIRE"),
            ("decl_old", "{told} {field} = {num};"),
            ("decl_new", "{tnew} {field} = {num};"),
        ),
    ),
    (
        ("map-value-", "", ""),
        (
            ("buf_rule", "MAP_VALUE_TYPE / WIRE"),
            ("decl_old", "map<string, {told}> {field} = {num};"),
            ("decl_new", "map<string, {tnew}> {field} = {num};"),
            ("grep_pat", "map<string, {told}>|map<string, {tnew}>|{field}"),
        ),
    ),
    (
        ("oneof-", "", ""),
        (
            ("decl_old", "oneof body {{ {told} {field} = {num}; }}"),
            ("decl_new", "oneof body {{ {tnew} {field} = {num}; }}"),
            ("grep_pat", "oneof body|{told} {field}|{tnew} {field}"),
        ),
    ),
    (
        ("rpc-", "", ""),
        (
            ("buf_rule", "RPC_STREAMING / WIRE"),
            ("grep_pat", "{told}|{tnew}"),
            ("goal_bit", "{told} → {tnew} so freeze {slug} frames fail"),
        ),
    ),
    (("proto2-required-", "", ""), _proto2_label_rule("required")),
    (("proto2-optional-", "", ""), _proto2_label_rule("optional")),
)

_R988_IMPORT_NEEDLES: tuple[tuple[str, str], ...] = (
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
)

_WRAPPER_TYPES = (
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


def _is_r988_enum(slug: str, told: str, tnew: str) -> bool:
    return any(
        (
            "Mode" in (told, tnew),
            slug.startswith("enum-"),
            "-enum-" in slug,
            slug.endswith(_R988_ENUM_SUFFIXES),
        )
    )


def _mark_enum(extra: dict[str, Any], told: str, tnew: str, field: str) -> None:
    extra["extra_msgs"] = ENUM_MODE
    extra.setdefault("grep_pat", f"{told} {field}|{tnew} {field}")


def _apply_shape_rules(extra: dict[str, Any], rules: _ShapeRules, fields: dict[str, Any]) -> None:
    slug = fields["slug"]
    for (prefix, middle, suffix), assignments in rules:
        if not all((slug.startswith(prefix), middle in slug, slug.endswith(suffix))):
            continue
        for key, template in assignments:
            extra[key] = template.format(**fields)


def _needle_imports(blob: str, needles: tuple[tuple[str, str], ...]) -> list[str]:
    imports: list[str] = []
    for needle, path in needles:
        if needle in blob and path not in imports:
            imports.append(path)
    return imports


def _needs_wrappers(blob: str, slug: str) -> bool:
    if "Value" not in blob or "wrappers" in slug:
        return False
    return any(token in blob for token in _WRAPPER_TYPES)


def _set_imports(extra: dict[str, Any], imports: list[str]) -> None:
    if imports:
        extra["imports"] = tuple(imports)


def _extras_for_r988(slug: str, told: str, tnew: str, field: str, num: int) -> dict[str, Any]:
    extra: dict[str, Any] = {}
    if _is_r988_enum(slug, told, tnew):
        _mark_enum(extra, told, tnew, field)
    # The mill also re-sets extra_msgs = ENUM_MODE for a oneof- slug with a Mode type; the
    # enum check above has already set that key to the same value, so it is not repeated.
    fields = {"slug": slug, "told": told, "tnew": tnew, "field": field, "num": num}
    _apply_shape_rules(extra, _R988_SHAPE_RULES, fields)
    blob = f"{told} {tnew} {slug}"
    imports = _needle_imports(blob, _R988_IMPORT_NEEDLES)
    if _needs_wrappers(blob, slug):
        imports.append("google/protobuf/wrappers.proto")
    _set_imports(extra, imports)
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


_R2535_SHAPE_RULES: _ShapeRules = (
    (
        ("proto2-required-", "", ""),
        (*_proto2_label_rule("required"), ("buf_rule", "FIELD_TYPE / WIRE")),
    ),
    (
        ("proto2-optional-", "", ""),
        (*_proto2_label_rule("optional"), ("buf_rule", "FIELD_TYPE / WIRE")),
    ),
)

_R2535_IMPORT_NEEDLES: tuple[tuple[str, str], ...] = (
    ("google.protobuf.Timestamp", "google/protobuf/timestamp.proto"),
    ("google.protobuf.Duration", "google/protobuf/duration.proto"),
    ("google.protobuf.Any", "google/protobuf/any.proto"),
    ("google.protobuf.Empty", "google/protobuf/empty.proto"),
)

_R2535_AVOID = (
    "map-key ban / r787 leftover / r1334 map-value-bool-to-sint32 / "
    "r1335 wrapper leftover"
)


def _is_r2535_enum(slug: str, told: str, tnew: str) -> bool:
    return any(("Mode" in (told, tnew), slug.endswith("-enum"), "-to-enum" in slug))


def _extras_for_r2535(slug: str, told: str, tnew: str, field: str, num: int) -> dict[str, Any]:
    extra: dict[str, Any] = {"field_num": num}
    if _is_r2535_enum(slug, told, tnew):
        _mark_enum(extra, told, tnew, field)
    fields = {"slug": slug, "told": told, "tnew": tnew, "field": field, "num": num}
    _apply_shape_rules(extra, _R2535_SHAPE_RULES, fields)
    blob = f"{told} {tnew} {slug}"
    imports = _needle_imports(blob, _R2535_IMPORT_NEEDLES)
    if "google.protobuf.Struct" in blob:
        imports.append("google/protobuf/struct.proto")
    _set_imports(extra, imports)
    return extra


def _r2535_candidates(p2_types: Any, wkt_dests: Any) -> Iterator[tuple[str, ...]]:
    """Yield ``(slug, told, tnew, field, wold, wnew, vs)`` in the mill's push order."""

    for told, wold, field in p2_types:
        for dest_tag, tnew, wnew in wkt_dests:
            if told == tnew:
                continue
            vs = (
                f"proto2 {told}→{dest_tag} TYPE (r1335 skipped WKT dest; "
                f"not optional/required drop)"
            )
            yield f"proto2-required-{told}-to-{dest_tag}", told, tnew, field, wold, wnew, vs
            yield f"proto2-optional-{told}-to-{dest_tag}", told, tnew, field, wold, wnew, vs


def extract_r2535_pairs(source: str) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    tree = ast.parse(source)
    p2_types = _named_constant(tree, "P2_TYPES")
    wkt_dests = _named_constant(tree, "WKT_DESTS")
    langs = list(LANGC)
    plants: list[dict[str, Any]] = []
    seen_slug: set[str] = set()
    for slug, told, tnew, field, wold, wnew, vs in _r2535_candidates(p2_types, wkt_dests):
        if slug in seen_slug:
            continue
        # One plant per accepted slug, so the mill's push counter n is len(plants).
        n = len(plants)
        num = 61 + n
        short = f"z{n:04d}"
        lang = langs[n % len(langs)]
        extra = _extras_for_r2535(slug, told, tnew, field, num)
        ticket = f"{LANGC[lang]}-{short.upper()}-{num}"
        plants.append(
            _ty(slug, short, told, tnew, field, num, wold, wnew, lang, ticket, vs, _R2535_AVOID, **extra)
        )
        seen_slug.add(slug)
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
    start: int,
) -> dict[str, Any]:
    notes_extra, notes_footer = MILL_NOTES.get(mill_id, ("", ""))
    return {
        "mill_id": mill_id,
        "catalog_first": catalog_first,
        "start": start,
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
        for offset, (ok, bad) in enumerate(pairs):
            rows.append(
                pair_row(mill_id, catalog_first, len(pairs), ok, bad, catalog_first + offset)
            )
    expected = 708
    if len(rows) != expected:
        raise SystemExit(f"expected {expected} catalog rows, got {len(rows)}: {counts}")
    lines = [json.dumps(row, separators=(",", ":"), ensure_ascii=False) for row in rows]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    out_path = Path(__file__).resolve().parent / "plants.jsonl"
    if argv and argv[0] == "--stdout":
        sys.stdout.write(build_plants_jsonl())
        return 0
    out_path.write_text(build_plants_jsonl(), encoding="utf-8", newline="")
    print(f"wrote {out_path} ({out_path.read_text().count(chr(10))} lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

if __package__:
    _contract.bind_import_twin(__name__)
