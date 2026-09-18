#!/usr/bin/env python3
"""Pinned wsr catalog: AST extract, JSONL load, and check.

The catalog lives at ``pipelines/wsr/CATALOG.json`` with pair bodies in
``pipelines/wsr/pairs.jsonl`` (compact, one object per line). Pair dicts are
AST-extracted from legacy mills on ``legacy-mill-lane``; mills are never
vendored and are never executed.
"""

from __future__ import annotations

import ast
import hashlib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any

from ._contract import (
    BANNED_SLUGS,
    BANNED_SLUG_TOKENS,
    FACTORY,
    FAMILY_PREFIX,
    FINDING_CATALOG_BANNED,
    FINDING_CATALOG_DUPLICATE,
    FINDING_CATALOG_FIELD_INVALID,
    FINDING_CATALOG_FIELD_MISSING,
    FINDING_CATALOG_NOT_AN_OBJECT,
    FINDING_CATALOG_PAIR_COUNT,
    FINDING_CATALOG_PLANT,
    FINDING_CATALOG_SCHEMA,
    GENERATOR,
    LEFTOVER3_N_ROUNDS,
    LEFTOVER3_START_ROUND,
    LEGACY_COMMIT,
    LEGACY_MILL,
    LEGACY_MILL_SHA256,
    LEGACY_PLANTS,
    LEGACY_PLANTS_SHA256,
    LLL_COMMIT,
    LLL_MILL,
    LLL_MILL_SHA256,
    LLL_N_ROUNDS,
    LLL_START_ROUND,
    N_ROUNDS,
    PAIRS_FILENAME,
    PAIRS_SHA256,
    QUOTA_PER_ROUND,
    REFUSED_MILL,
    SCHEMA_ID,
    START_ROUND,
    bind_import_twin,
    default_catalog_path,
    load_strict_json,
    refuse,
    refuse_first,
    refuse_when,
)

PLANT_CALLS = frozenset(("_p",))
MAPPING_PLANT_KEYS = frozenset(
    {
        "slug",
        "fail",
        "mod",
        "drop",
        "stack",
        "idf",
        "evf",
        "naive",
        "bound",
        "dropk",
        "doc",
        "doc2",
        "domain",
        "ticket",
        "test_ok",
        "test_fail",
        "short",
        "dshort",
    }
)
MILL_KEYS = frozenset(
    {
        "mill_id",
        "source_format",
        "source_path",
        "source_commit",
        "source_sha256",
        "start_round",
        "n_rounds",
    }
)
ROW_KEYS = frozenset({"mill_id", "source_format", "round"})
SHARED_PLANT_FIELDS = (
    "slug",
    "goal",
    "plan",
    "mod",
    "test_fn",
    "src_body",
    "test_body",
    "grep_pat",
    "grep_hit",
    "fail_msg",
    "first_old",
    "first_new",
    "first_obs",
    "still_msg",
    "reread_obs",
    "plan_change",
    "fix_new",
    "fix_obs",
    "docs_url",
    "docs_ok",
    "docs_url2",
    "docs_ok2",
    "outcome",
    "domain",
    "stack",
    "seed",
    "residual",
)
OK_REQUIRED = SHARED_PLANT_FIELDS + ("coverage",)
BAD_REQUIRED = SHARED_PLANT_FIELDS + ("ticket", "ticket_why", "coverage")

__all__ = [
    "Catalog",
    "Pair",
    "ast_extract_catalog",
    "ast_extract_mapping_pairs",
    "ast_extract_mill_constants",
    "ast_extract_pairs",
    "catalog_check",
    "load_catalog",
    "sha256_text",
]


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _literal(node: ast.AST, where: str) -> str | int:
    if isinstance(node, ast.Constant) and isinstance(node.value, (str, int)) and not isinstance(
        node.value, bool
    ):
        return node.value
    refuse(FINDING_CATALOG_PLANT, f"{where}: plant values must be str or int literals")


def _const_set(node: ast.AST, where: str) -> frozenset[str]:
    refuse_when(
        not isinstance(node, ast.Set),
        FINDING_CATALOG_PLANT,
        f"{where} must be a set of string literals",
    )
    assert isinstance(node, ast.Set)
    values: list[str] = []
    for index, item in enumerate(node.elts):
        value = _literal(item, f"{where}[{index}]")
        refuse_when(not isinstance(value, str), FINDING_CATALOG_PLANT, f"{where}[{index}]")
        values.append(value)
    return frozenset(values)


def _call_kwargs(node: ast.AST, where: str) -> dict[str, str | int]:
    refuse_when(
        not isinstance(node, ast.Call)
        or not isinstance(node.func, ast.Name)
        or node.func.id not in PLANT_CALLS
        or node.args
        or any(kw.arg is None for kw in node.keywords),
        FINDING_CATALOG_PLANT,
        f"{where}: expected _p(**kwargs)",
    )
    assert isinstance(node, ast.Call)
    plant: dict[str, str | int] = {}
    for index, kw in enumerate(node.keywords):
        assert kw.arg is not None
        plant[kw.arg] = _literal(kw.value, f"{where}.{kw.arg}#{index}")
    return plant


def _pairs_node(tree: ast.Module) -> ast.AST:
    for node in tree.body:
        if isinstance(node, ast.Assign):
            names = [t.id for t in node.targets if isinstance(t, ast.Name)]
            if "PAIRS" in names:
                return node.value
    refuse(FINDING_CATALOG_PLANT, "plants source has no PAIRS assignment")


def ast_extract_pairs(source: str) -> tuple[tuple[dict[str, str | int], dict[str, str | int]], ...]:
    """Return leftover-event pairs from the mill module, via AST only."""

    tree = ast.parse(source)
    payload = _pairs_node(tree)
    refuse_when(
        not isinstance(payload, (ast.List, ast.Tuple)),
        FINDING_CATALOG_PLANT,
        "PAIRS must be a list or tuple of (ok, bad) tuples",
    )
    assert isinstance(payload, (ast.List, ast.Tuple))
    pairs: list[tuple[dict[str, str | int], dict[str, str | int]]] = []
    for index, item in enumerate(payload.elts):
        refuse_when(
            not isinstance(item, (ast.Tuple, ast.List)) or len(item.elts) != 2,
            FINDING_CATALOG_PLANT,
            f"PAIRS[{index}] must be an (ok, bad) pair",
        )
        assert isinstance(item, (ast.Tuple, ast.List))
        ok = _call_kwargs(item.elts[0], f"PAIRS[{index}].ok")
        bad = _call_kwargs(item.elts[1], f"PAIRS[{index}].bad")
        pairs.append((ok, bad))
    return tuple(pairs)


def _call_dict(node: ast.AST, where: str) -> dict[str, str | int]:
    refuse_when(
        not isinstance(node, ast.Call)
        or not isinstance(node.func, ast.Name)
        or node.func.id != "dict"
        or node.args
        or any(kw.arg is None for kw in node.keywords),
        FINDING_CATALOG_PLANT,
        f"{where}: expected dict(**kwargs)",
    )
    assert isinstance(node, ast.Call)
    plant: dict[str, str | int] = {}
    for index, kw in enumerate(node.keywords):
        assert kw.arg is not None
        plant[kw.arg] = _literal(kw.value, f"{where}.{kw.arg}#{index}")
    return plant


def ast_extract_mapping_pairs(source: str) -> tuple[dict[str, str | int], ...]:
    """Return mapping-v1 plants from ``PAIRS = [dict(...), ...]`` via AST only."""

    refuse_when(REFUSED_MILL in source, FINDING_CATALOG_BANNED, f"refusing hopper mill {REFUSED_MILL!r}")
    tree = ast.parse(source)
    payload = _pairs_node(tree)
    refuse_when(
        not isinstance(payload, ast.List),
        FINDING_CATALOG_PLANT,
        "PAIRS must be a list of dict(...) plants",
    )
    assert isinstance(payload, ast.List)
    plants: list[dict[str, str | int]] = []
    for index, item in enumerate(payload.elts):
        plant = _call_dict(item, f"PAIRS[{index}]")
        missing = sorted(MAPPING_PLANT_KEYS.difference(plant))
        refuse_when(
            bool(missing),
            FINDING_CATALOG_FIELD_MISSING,
            f"PAIRS[{index}] missing {missing}",
        )
        plants.append(plant)
    return tuple(plants)


def ast_extract_start_round(source: str) -> int:
    """Read ``build_pair(41 + i, ...)`` from ``self_check`` without executing it."""

    tree = ast.parse(source)
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef) or node.name != "self_check":
            continue
        for child in ast.walk(node):
            if (
                isinstance(child, ast.Call)
                and isinstance(child.func, ast.Name)
                and child.func.id == "build_pair"
                and child.args
                and isinstance(child.args[0], ast.BinOp)
                and isinstance(child.args[0].op, ast.Add)
                and isinstance(child.args[0].left, ast.Constant)
                and isinstance(child.args[0].left.value, int)
                and not isinstance(child.args[0].left.value, bool)
            ):
                return child.args[0].left.value
    refuse(FINDING_CATALOG_PLANT, "self_check has no build_pair(START + i) call")


def ast_extract_mill_constants(source: str) -> dict[str, object]:
    """Return FACTORY/PREFIX/GENERATOR/BANNED_SLUGS/START from the mill AST."""

    tree = ast.parse(source)
    found: dict[str, object] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        names = [t.id for t in node.targets if isinstance(t, ast.Name)]
        for name in names:
            if name in {"FACTORY", "PREFIX", "GENERATOR"}:
                found[name] = _literal(node.value, name)
            elif name == "BANNED_SLUGS":
                found[name] = _const_set(node.value, name)
    found["START"] = ast_extract_start_round(source)
    needed = ("FACTORY", "PREFIX", "GENERATOR", "BANNED_SLUGS")
    missing = [name for name in needed if name not in found]
    refuse_when(bool(missing), FINDING_CATALOG_PLANT, f"mill source missing {missing}")
    return found


def ast_extract_catalog(
    plants_source: str,
    mill_source: str,
    *,
    plants_sha256: str | None = None,
    mill_sha256: str | None = None,
    commit: str = LEGACY_COMMIT,
) -> dict[str, Any]:
    """Build the catalog document from leftover mill source text."""

    constants = ast_extract_mill_constants(mill_source)
    pairs = ast_extract_pairs(plants_source)
    refuse_first(
        (
            (
                constants["FACTORY"] != FACTORY,
                FINDING_CATALOG_SCHEMA,
                f"mill FACTORY must be {FACTORY!r}",
            ),
            (
                constants["PREFIX"] != FAMILY_PREFIX,
                FINDING_CATALOG_SCHEMA,
                f"mill PREFIX must be {FAMILY_PREFIX!r}",
            ),
            (
                constants["GENERATOR"] != GENERATOR,
                FINDING_CATALOG_SCHEMA,
                f"mill GENERATOR must be {GENERATOR!r}",
            ),
            (
                constants["START"] != LEFTOVER3_START_ROUND,
                FINDING_CATALOG_SCHEMA,
                f"mill START must be {LEFTOVER3_START_ROUND}",
            ),
            (
                constants["BANNED_SLUGS"] != BANNED_SLUGS,
                FINDING_CATALOG_SCHEMA,
                "mill BANNED_SLUGS drifted from the reviewed set",
            ),
            (
                len(pairs) != LEFTOVER3_N_ROUNDS,
                FINDING_CATALOG_PAIR_COUNT,
                f"need {LEFTOVER3_N_ROUNDS} pairs, got {len(pairs)}",
            ),
        )
    )
    document = {
        "schema_id": SCHEMA_ID,
        "family_prefix": FAMILY_PREFIX,
        "factory": FACTORY,
        "generator": GENERATOR,
        "start_round": LEFTOVER3_START_ROUND,
        "n_rounds": LEFTOVER3_N_ROUNDS,
        "quota_per_round": QUOTA_PER_ROUND,
        "source": {
            "lane": "legacy-mill-lane",
            "commit": commit,
            "plants": LEGACY_PLANTS,
            "mill": LEGACY_MILL,
            "plants_sha256": plants_sha256 or sha256_text(plants_source),
            "mill_sha256": mill_sha256 or sha256_text(mill_source),
        },
        "pairs": [
            {"round": START_ROUND + index, "ok": ok, "bad": bad}
            for index, (ok, bad) in enumerate(pairs)
        ],
    }
    _validate_leftover3_document(document)
    return document


def _validate_leftover3_document(raw: object) -> dict[str, Any]:
    document = _require_object(raw, "catalog")
    pairs_raw = _require_field(document, "pairs", "catalog")
    refuse_when(not isinstance(pairs_raw, list), FINDING_CATALOG_FIELD_INVALID, "pairs must be a list")
    assert isinstance(pairs_raw, list)
    for index, entry in enumerate(pairs_raw):
        item = _require_object(entry, f"pairs[{index}]")
        _plant(item.get("ok"), OK_REQUIRED, f"pairs[{index}].ok")
        _plant(item.get("bad"), BAD_REQUIRED, f"pairs[{index}].bad")
    return document


@dataclass(frozen=True)
class Pair:
    round_n: int
    mill_id: str
    source_format: str
    ok: Mapping[str, Any]
    bad: Mapping[str, Any]
    plant: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class Catalog:
    path: Path
    family_prefix: str
    factory: str
    generator: str
    start_round: int
    n_rounds: int
    quota_per_round: int
    source: Mapping[str, Any]
    pairs: tuple[Pair, ...]

    def pair_for_round(self, round_n: int) -> Pair:
        for pair in self.pairs:
            if pair.round_n == round_n:
                return pair
        refuse(FINDING_CATALOG_FIELD_INVALID, f"no pair for round {round_n}")


def _require_object(raw: object, where: str) -> dict[str, Any]:
    refuse_when(
        not isinstance(raw, dict),
        FINDING_CATALOG_NOT_AN_OBJECT,
        f"{where} must be an object",
    )
    assert isinstance(raw, dict)
    return raw


def _require_str(raw: object, where: str) -> str:
    refuse_when(
        not isinstance(raw, str) or not raw,
        FINDING_CATALOG_FIELD_INVALID,
        f"{where} must be a non-empty string",
    )
    assert isinstance(raw, str)
    return raw


def _require_int(raw: object, where: str) -> int:
    refuse_when(
        not isinstance(raw, int) or isinstance(raw, bool),
        FINDING_CATALOG_FIELD_INVALID,
        f"{where} must be an integer",
    )
    assert isinstance(raw, int)
    return raw


def _require_field(mapping: dict[str, Any], key: str, where: str) -> Any:
    refuse_when(key not in mapping, FINDING_CATALOG_FIELD_MISSING, f"{where}.{key} is missing")
    return mapping[key]


def _plant(raw: object, required: tuple[str, ...], where: str) -> Mapping[str, Any]:
    plant = _require_object(raw, where)
    for key in required:
        _require_field(plant, key, where)
        if key == "coverage":
            coverage = _require_int(plant[key], f"{where}.coverage")
            refuse_when(
                not 0 <= coverage <= 100,
                FINDING_CATALOG_FIELD_INVALID,
                f"{where}.coverage must be in 0..100",
            )
        else:
            _require_str(plant[key], f"{where}.{key}")
    first_old = plant["first_old"]
    src_body = plant["src_body"]
    refuse_when(
        not isinstance(first_old, str)
        or not isinstance(src_body, str)
        or first_old not in src_body,
        FINDING_CATALOG_PLANT,
        f"{where}: first_old is not in src_body",
    )
    return MappingProxyType(dict(plant))


def _unique(name: str, values: list[str]) -> None:
    refuse_when(
        len(set(values)) != len(values),
        FINDING_CATALOG_DUPLICATE,
        f"duplicate {name}: {values}",
    )


def _reject_banned(slug: str, where: str) -> None:
    refuse_when(slug in BANNED_SLUGS, FINDING_CATALOG_BANNED, f"{where} slug is banned {slug!r}")
    lowered = slug.lower()
    for token in BANNED_SLUG_TOKENS:
        refuse_when(
            token in lowered,
            FINDING_CATALOG_BANNED,
            f"{where} slug carries banned {token!r}",
        )


def _validate_header(raw: object) -> dict[str, Any]:
    document = _require_object(raw, "catalog")
    refuse_first(
        (
            (
                document.get("schema_id") != SCHEMA_ID,
                FINDING_CATALOG_SCHEMA,
                f"schema_id must be {SCHEMA_ID!r}",
            ),
            (
                document.get("family_prefix") != FAMILY_PREFIX,
                FINDING_CATALOG_SCHEMA,
                f"family_prefix must be {FAMILY_PREFIX!r}",
            ),
            (
                document.get("factory") != FACTORY,
                FINDING_CATALOG_SCHEMA,
                f"factory must be {FACTORY!r}",
            ),
            (
                document.get("generator") != GENERATOR,
                FINDING_CATALOG_SCHEMA,
                f"generator must be {GENERATOR!r}",
            ),
        )
    )
    quota = _require_int(_require_field(document, "quota_per_round", "catalog"), "quota_per_round")
    refuse_when(
        quota != QUOTA_PER_ROUND,
        FINDING_CATALOG_SCHEMA,
        f"quota_per_round must be {QUOTA_PER_ROUND}",
    )
    pairs_file = _require_str(_require_field(document, "pairs_file", "catalog"), "pairs_file")
    refuse_when(
        pairs_file != PAIRS_FILENAME,
        FINDING_CATALOG_SCHEMA,
        f"pairs_file must be {PAIRS_FILENAME!r}",
    )
    pairs_sha = _require_str(_require_field(document, "pairs_sha256", "catalog"), "pairs_sha256")
    refuse_when(
        pairs_sha != PAIRS_SHA256,
        FINDING_CATALOG_SCHEMA,
        "pairs_sha256 drifted from the committed pairs.jsonl bytes",
    )
    mills_raw = _require_field(document, "mills", "catalog")
    refuse_when(not isinstance(mills_raw, list), FINDING_CATALOG_FIELD_INVALID, "mills must be a list")
    assert isinstance(mills_raw, list)
    refuse_when(len(mills_raw) != 2, FINDING_CATALOG_PAIR_COUNT, "expected two committed mills")
    mills: list[dict[str, Any]] = []
    for index, entry in enumerate(mills_raw):
        mill = _require_object(entry, f"mills[{index}]")
        for key in MILL_KEYS:
            _require_field(mill, key, f"mills[{index}]")
        mills.append(mill)
    return document


def _mill_lookup(mills: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(mill["mill_id"]): mill for mill in mills}


def _pair_from_row(row: dict[str, Any], *, mills: dict[str, dict[str, Any]], index: int) -> Pair:
    where = f"pairs.jsonl:{index + 1}"
    for key in ROW_KEYS:
        _require_field(row, key, where)
    mill_id = _require_str(row["mill_id"], f"{where}.mill_id")
    source_format = _require_str(row["source_format"], f"{where}.source_format")
    refuse_when(
        mill_id not in mills,
        FINDING_CATALOG_SCHEMA,
        f"{where} unknown mill_id {mill_id!r}",
    )
    mill = mills[mill_id]
    refuse_when(
        source_format != mill["source_format"],
        FINDING_CATALOG_SCHEMA,
        f"{where} source_format mismatch for {mill_id}",
    )
    round_n = _require_int(row["round"], f"{where}.round")
    start = _require_int(mill["start_round"], f"mills[{mill_id}].start_round")
    n_rounds = _require_int(mill["n_rounds"], f"mills[{mill_id}].n_rounds")
    refuse_when(
        not start <= round_n < start + n_rounds,
        FINDING_CATALOG_FIELD_INVALID,
        f"{where} round {round_n} outside {mill_id} span",
    )
    if source_format == "leftover3-v1":
        ok = _plant(row.get("ok"), OK_REQUIRED, f"{where}.ok")
        bad = _plant(row.get("bad"), BAD_REQUIRED, f"{where}.bad")
        for plant, label in ((ok, "ok"), (bad, "bad")):
            _reject_banned(str(plant["slug"]), f"{where}.{label}")
        return Pair(
            round_n=round_n,
            mill_id=mill_id,
            source_format=source_format,
            ok=ok,
            bad=bad,
            plant=None,
        )
    if source_format == "mapping-v1":
        plant_raw = _require_object(row.get("plant"), f"{where}.plant")
        for key in MAPPING_PLANT_KEYS:
            _require_field(plant_raw, key, f"{where}.plant")
            _require_str(plant_raw[key], f"{where}.plant.{key}")
        _reject_banned(str(plant_raw["slug"]), f"{where}.plant")
        _reject_banned(str(plant_raw["fail"]), f"{where}.plant.fail")
        return Pair(
            round_n=round_n,
            mill_id=mill_id,
            source_format=source_format,
            ok=MappingProxyType({}),
            bad=MappingProxyType({}),
            plant=MappingProxyType(dict(plant_raw)),
        )
    refuse(FINDING_CATALOG_SCHEMA, f"{where} unsupported source_format {source_format!r}")


def _load_pairs_jsonl(path: Path, *, mills: list[dict[str, Any]]) -> tuple[Pair, ...]:
    text = path.read_text(encoding="utf-8")
    refuse_when(
        sha256_text(text) != PAIRS_SHA256,
        FINDING_CATALOG_SCHEMA,
        "pairs.jsonl bytes drifted from pairs_sha256 pin",
    )
    lookup = _mill_lookup(mills)
    pairs: list[Pair] = []
    slugs: list[str] = []
    mods: list[str] = []
    tickets: list[str] = []
    for index, line in enumerate(text.splitlines()):
        if not line.strip():
            continue
        row = _require_object(load_strict_json(line), f"pairs.jsonl:{index + 1}")
        pair = _pair_from_row(row, mills=lookup, index=index)
        pairs.append(pair)
        if pair.source_format == "leftover3-v1":
            slugs.extend((str(pair.ok["slug"]), str(pair.bad["slug"])))
            mods.extend((str(pair.ok["mod"]), str(pair.bad["mod"])))
            tickets.append(str(pair.bad["ticket"]))
        else:
            assert pair.plant is not None
            slugs.extend((str(pair.plant["slug"]), str(pair.plant["fail"])))
            mods.extend((str(pair.plant["mod"]), str(pair.plant["drop"])))
            tickets.append(str(pair.plant["ticket"]))
    refuse_when(
        len(pairs) != N_ROUNDS,
        FINDING_CATALOG_PAIR_COUNT,
        f"need {N_ROUNDS} pair rows, got {len(pairs)}",
    )
    _unique("slugs", slugs)
    _unique("mods", mods)
    _unique("tickets", tickets)
    return tuple(sorted(pairs, key=lambda item: item.round_n))


def load_catalog(path: Path | None = None, *, root: Path | None = None) -> Catalog:
    catalog_path = (path or default_catalog_path(root)).resolve()
    document = _validate_header(load_strict_json(catalog_path.read_text(encoding="utf-8")))
    mills_raw = document["mills"]
    assert isinstance(mills_raw, list)
    pairs_path = catalog_path.with_name(PAIRS_FILENAME)
    refuse_when(
        not pairs_path.is_file(),
        FINDING_CATALOG_FIELD_MISSING,
        f"missing pairs file {pairs_path}",
    )
    pairs = _load_pairs_jsonl(pairs_path, mills=mills_raw)
    return Catalog(
        path=catalog_path,
        family_prefix=FAMILY_PREFIX,
        factory=FACTORY,
        generator=GENERATOR,
        start_round=START_ROUND,
        n_rounds=N_ROUNDS,
        quota_per_round=QUOTA_PER_ROUND,
        source=MappingProxyType({"mills": mills_raw, "pairs_sha256": PAIRS_SHA256}),
        pairs=pairs,
    )


def catalog_check(path: Path | None = None, *, root: Path | None = None) -> Catalog:
    """Load the committed catalog and re-assert mill pins."""

    catalog = load_catalog(path, root=root)
    mills = _mill_lookup(list(catalog.source["mills"]))
    r41 = mills["wsr_r41_leftover3"]
    r89 = mills["wsr_r89_lll"]
    refuse_first(
        (
            (
                r41.get("source_path") != LEGACY_MILL,
                FINDING_CATALOG_SCHEMA,
                "wsr_r41_leftover3 source_path drifted",
            ),
            (
                r41.get("source_commit") != LEGACY_COMMIT,
                FINDING_CATALOG_SCHEMA,
                "wsr_r41_leftover3 source_commit drifted",
            ),
            (
                r41.get("source_sha256") != LEGACY_MILL_SHA256,
                FINDING_CATALOG_SCHEMA,
                "wsr_r41_leftover3 source_sha256 drifted",
            ),
            (
                int(r41["start_round"]) != LEFTOVER3_START_ROUND,
                FINDING_CATALOG_SCHEMA,
                "wsr_r41_leftover3 start_round drifted",
            ),
            (
                int(r41["n_rounds"]) != LEFTOVER3_N_ROUNDS,
                FINDING_CATALOG_SCHEMA,
                "wsr_r41_leftover3 n_rounds drifted",
            ),
            (
                r89.get("source_path") != LLL_MILL,
                FINDING_CATALOG_SCHEMA,
                "wsr_r89_lll source_path drifted",
            ),
            (
                r89.get("source_path") == REFUSED_MILL,
                FINDING_CATALOG_BANNED,
                f"refusing hopper mill {REFUSED_MILL!r}",
            ),
            (
                r89.get("source_commit") != LLL_COMMIT,
                FINDING_CATALOG_SCHEMA,
                "wsr_r89_lll source_commit drifted",
            ),
            (
                r89.get("source_sha256") != LLL_MILL_SHA256,
                FINDING_CATALOG_SCHEMA,
                "wsr_r89_lll source_sha256 drifted",
            ),
            (
                int(r89["start_round"]) != LLL_START_ROUND,
                FINDING_CATALOG_SCHEMA,
                "wsr_r89_lll start_round drifted",
            ),
            (
                int(r89["n_rounds"]) != LLL_N_ROUNDS,
                FINDING_CATALOG_SCHEMA,
                "wsr_r89_lll n_rounds drifted",
            ),
        )
    )
    return catalog


bind_import_twin(__name__)
