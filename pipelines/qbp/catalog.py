#!/usr/bin/env python3
"""Pinned qbp leftover catalog: AST extract, load, and check.

Pair constructor args are AST-extracted from ``qbp-mill*.py`` (via the plants
path each mill names) on ``legacy-mill-lane``. Mill scripts are never vendored
or executed. Load raises and stops the run when the committed catalog drifts.
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
    BAN,
    FACTORY,
    FAMILY_PREFIX,
    FINDING_CATALOG_BANNED,
    FINDING_CATALOG_DUPLICATE,
    FINDING_CATALOG_FIELD_INVALID,
    FINDING_CATALOG_FIELD_MISSING,
    FINDING_CATALOG_MILL,
    FINDING_CATALOG_NOT_AN_OBJECT,
    FINDING_CATALOG_PAIR_COUNT,
    FINDING_CATALOG_PLANT,
    FINDING_CATALOG_SCHEMA,
    FINDING_PAIRS_SHA_MISMATCH,
    GENERATOR,
    LEGACY_COMMIT,
    LEGACY_LANE,
    MILL_SOURCES,
    N_MILLS,
    N_PAIRS,
    PAIRS_FILENAME,
    QUOTA_PER_ROUND,
    SCHEMA_ID,
    bind_import_twin,
    default_catalog_path,
    default_pairs_path,
    load_pair_json,
    load_strict_json,
    refuse,
    refuse_first,
    refuse_when,
)
from .plants import BAD_ARG_NAMES, OK_ARG_NAMES, expand_bad, expand_ok

PLANT_CALLS = frozenset(("_ok", "_bad"))

__all__ = [
    "Catalog",
    "Mill",
    "Pair",
    "ast_extract_catalog",
    "ast_extract_mill",
    "ast_extract_plants",
    "catalog_check",
    "load_catalog",
    "sha256_text",
]


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _literal(node: ast.AST, where: str) -> Any:
    if isinstance(node, ast.Constant) and isinstance(node.value, (str, int, float, bool)):
        return node.value
    if isinstance(node, ast.Constant) and node.value is None:
        return None
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
        value = _literal(node.operand, where)
        refuse_when(
            not isinstance(value, (int, float)) or isinstance(value, bool),
            FINDING_CATALOG_PLANT,
            f"{where}: unary operand must be a number",
        )
        return -value if isinstance(node.op, ast.USub) else value
    if isinstance(node, ast.Dict):
        out: dict[Any, Any] = {}
        for key, value in zip(node.keys, node.values, strict=True):
            refuse_when(key is None, FINDING_CATALOG_PLANT, f"{where}: starred dict")
            out[_literal(key, where)] = _literal(value, where)
        return out
    if isinstance(node, ast.List):
        return [_literal(elt, f"{where}[]") for elt in node.elts]
    if isinstance(node, ast.Tuple):
        return [_literal(elt, f"{where}()") for elt in node.elts]
    if isinstance(node, ast.Set):
        return [_literal(elt, where) for elt in node.elts]
    refuse(FINDING_CATALOG_PLANT, f"{where}: unsupported {type(node).__name__}")


def _assign_map(tree: ast.Module) -> dict[str, ast.AST]:
    found: dict[str, ast.AST] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    found[target.id] = node.value
    return found


def _plants_path(tree: ast.Module) -> str:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", "")
        if name != "SourceFileLoader" or len(node.args) < 2:
            continue
        path_node = node.args[1]
        if (
            isinstance(path_node, ast.Call)
            and isinstance(path_node.func, ast.Name)
            and path_node.func.id == "str"
            and path_node.args
        ):
            joined = path_node.args[0]
            if isinstance(joined, ast.BinOp) and isinstance(joined.op, ast.Div):
                if isinstance(joined.right, ast.Constant) and isinstance(joined.right.value, str):
                    return joined.right.value
    refuse(FINDING_CATALOG_MILL, "mill source has no SourceFileLoader plants path")


def _ctor_row(node: ast.AST, names: tuple[str, ...], where: str) -> dict[str, Any]:
    refuse_when(
        not isinstance(node, ast.Call)
        or not isinstance(node.func, ast.Name)
        or node.func.id not in PLANT_CALLS
        or len(node.args) != len(names),
        FINDING_CATALOG_PLANT,
        f"{where}: expected {node.func.id if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) else 'call'}"
        f"({len(names)} positional args)",
    )
    assert isinstance(node, ast.Call)
    row = {name: _literal(arg, f"{where}.{name}") for name, arg in zip(names, node.args, strict=True)}
    for keyword in node.keywords:
        refuse_when(
            keyword.arg != "extra_fix",
            FINDING_CATALOG_PLANT,
            f"{where}: unexpected keyword {keyword.arg!r}",
        )
        row["extra_fix"] = _literal(keyword.value, f"{where}.extra_fix")
    return row


def ast_extract_mill(source: str) -> dict[str, Any]:
    """Return FACTORY/PREFIX/BAN and the plants filename from a mill module."""

    tree = ast.parse(source)
    assigns = _assign_map(tree)
    missing = [name for name in ("FACTORY", "PREFIX", "BAN") if name not in assigns]
    refuse_when(bool(missing), FINDING_CATALOG_MILL, f"mill source missing {missing}")
    factory = _literal(assigns["FACTORY"], "FACTORY")
    prefix = _literal(assigns["PREFIX"], "PREFIX")
    ban = _literal(assigns["BAN"], "BAN")
    refuse_when(
        factory != FACTORY or prefix != FAMILY_PREFIX,
        FINDING_CATALOG_SCHEMA,
        f"mill identity {factory!r}/{prefix!r} is not {FACTORY}/{FAMILY_PREFIX}",
    )
    refuse_when(set(ban) != set(BAN), FINDING_CATALOG_BANNED, f"mill BAN drifted: {ban}")
    plants = _plants_path(tree)
    return {
        "factory": factory,
        "prefix": prefix,
        "ban": sorted(BAN),
        "plants": f"experiments/{plants}",
    }


def ast_extract_plants(source: str) -> dict[str, Any]:
    """Return CATALOG_FIRST and constructor-arg pairs from a plants module."""

    tree = ast.parse(source)
    assigns = _assign_map(tree)
    refuse_when("CATALOG_FIRST" not in assigns or "PAIRS" not in assigns, FINDING_CATALOG_PLANT, "plants source missing CATALOG_FIRST/PAIRS")
    first = _literal(assigns["CATALOG_FIRST"], "CATALOG_FIRST")
    refuse_when(not isinstance(first, int) or isinstance(first, bool), FINDING_CATALOG_PLANT, "CATALOG_FIRST must be an int")
    payload = assigns["PAIRS"]
    refuse_when(not isinstance(payload, ast.List), FINDING_CATALOG_PLANT, "PAIRS must be a list")
    pairs: list[dict[str, Any]] = []
    for index, item in enumerate(payload.elts):
        refuse_when(
            not isinstance(item, (ast.Tuple, ast.List)) or len(item.elts) != 2,
            FINDING_CATALOG_PLANT,
            f"PAIRS[{index}] must be an (ok, bad) pair",
        )
        assert isinstance(item, (ast.Tuple, ast.List))
        pairs.append(
            {
                "round": first + index,
                "ok": _ctor_row(item.elts[0], OK_ARG_NAMES, f"PAIRS[{index}].ok"),
                "bad": _ctor_row(item.elts[1], BAD_ARG_NAMES, f"PAIRS[{index}].bad"),
            }
        )
    return {"catalog_first": first, "n_pairs": len(pairs), "pairs": pairs}


def ast_extract_catalog(
    mill_sources: Mapping[str, str],
    plants_sources: Mapping[str, str],
    *,
    commit: str = LEGACY_COMMIT,
) -> dict[str, Any]:
    """Build the catalog document from mill/plants source text (AST only)."""

    mills: list[dict[str, Any]] = []
    pairs: list[dict[str, Any]] = []
    for mill_id, path, mill_sha, plants_path, plants_sha, catalog_first, n_pairs in MILL_SOURCES:
        refuse_when(path not in mill_sources, FINDING_CATALOG_MILL, f"missing mill source {path}")
        refuse_when(
            plants_path not in plants_sources,
            FINDING_CATALOG_MILL,
            f"missing plants source {plants_path}",
        )
        mill_text = mill_sources[path]
        plants_text = plants_sources[plants_path]
        refuse_first(
            (
                (sha256_text(mill_text) != mill_sha, FINDING_CATALOG_SCHEMA, f"{path} sha256 drifted"),
                (
                    sha256_text(plants_text) != plants_sha,
                    FINDING_CATALOG_SCHEMA,
                    f"{plants_path} sha256 drifted",
                ),
            )
        )
        extracted_mill = ast_extract_mill(mill_text)
        refuse_when(
            extracted_mill["plants"] != plants_path,
            FINDING_CATALOG_MILL,
            f"{path} plants pointer {extracted_mill['plants']!r} != {plants_path!r}",
        )
        extracted_plants = ast_extract_plants(plants_text)
        refuse_when(
            extracted_plants["catalog_first"] != catalog_first
            or extracted_plants["n_pairs"] != n_pairs,
            FINDING_CATALOG_PAIR_COUNT,
            f"{path} catalog window {extracted_plants['catalog_first']}+{extracted_plants['n_pairs']}",
        )
        mills.append(
            {
                "mill_id": mill_id,
                "path": path,
                "sha256": mill_sha,
                "plants": plants_path,
                "plants_sha256": plants_sha,
                "catalog_first": catalog_first,
                "n_pairs": n_pairs,
                "ban": sorted(BAN),
            }
        )
        for row in extracted_plants["pairs"]:
            pairs.append({"mill_id": mill_id, **row})
    document = {
        "schema_id": SCHEMA_ID,
        "family_prefix": FAMILY_PREFIX,
        "factory": FACTORY,
        "generator": GENERATOR,
        "quota_per_round": QUOTA_PER_ROUND,
        "n_mills": len(mills),
        "n_pairs": len(pairs),
        "pairs_filename": PAIRS_FILENAME,
        "source": {"lane": LEGACY_LANE, "commit": commit},
        "mills": mills,
        "pairs": pairs,
    }
    _validate_counts(document)
    return document


@dataclass(frozen=True)
class Pair:
    mill_id: str
    round_n: int
    ok_args: Mapping[str, Any]
    bad_args: Mapping[str, Any]
    ok: Mapping[str, Any]
    bad: Mapping[str, Any]


@dataclass(frozen=True)
class Mill:
    mill_id: str
    path: str
    sha256: str
    plants: str
    plants_sha256: str
    catalog_first: int
    n_pairs: int


@dataclass(frozen=True)
class Catalog:
    path: Path
    pairs_path: Path
    family_prefix: str
    factory: str
    generator: str
    source: Mapping[str, Any]
    mills: tuple[Mill, ...]
    pairs: tuple[Pair, ...]
    pairs_sha256: str

    def pairs_for_mill(self, mill_id: str) -> tuple[Pair, ...]:
        selected = tuple(pair for pair in self.pairs if pair.mill_id == mill_id)
        refuse_when(not selected, FINDING_CATALOG_MILL, f"unknown mill {mill_id}")
        return selected


def _require_object(raw: object, where: str) -> dict[str, Any]:
    refuse_when(not isinstance(raw, dict), FINDING_CATALOG_NOT_AN_OBJECT, f"{where} must be an object")
    assert isinstance(raw, dict)
    return raw


def _require_str(raw: object, where: str) -> str:
    refuse_when(not isinstance(raw, str) or not raw, FINDING_CATALOG_FIELD_INVALID, f"{where} must be a non-empty string")
    assert isinstance(raw, str)
    return raw


def _require_int(raw: object, where: str) -> int:
    refuse_when(not isinstance(raw, int) or isinstance(raw, bool), FINDING_CATALOG_FIELD_INVALID, f"{where} must be an integer")
    assert isinstance(raw, int)
    return raw


def _require_field(mapping: dict[str, Any], key: str, where: str) -> Any:
    refuse_when(key not in mapping, FINDING_CATALOG_FIELD_MISSING, f"{where}.{key} is missing")
    return mapping[key]


def _ctor_args(raw: object, names: tuple[str, ...], where: str) -> dict[str, Any]:
    row = _require_object(raw, where)
    out: dict[str, Any] = {}
    for name in names:
        out[name] = _require_field(row, name, where)
    if "extra_fix" in row:
        refuse_when(not isinstance(row["extra_fix"], dict), FINDING_CATALOG_FIELD_INVALID, f"{where}.extra_fix must be an object")
        out["extra_fix"] = row["extra_fix"]
    _require_str(out["slug"], f"{where}.slug")
    return out


def _unique(name: str, values: list[str]) -> None:
    refuse_when(len(set(values)) != len(values), FINDING_CATALOG_DUPLICATE, f"duplicate {name}: {values}")


def _reject_banned(slug: str, where: str) -> None:
    refuse_when(slug in BAN, FINDING_CATALOG_BANNED, f"{where} slug is banned: {slug}")


def _validate_counts(document: Mapping[str, Any]) -> None:
    refuse_first(
        (
            (document.get("schema_id") != SCHEMA_ID, FINDING_CATALOG_SCHEMA, f"schema_id must be {SCHEMA_ID!r}"),
            (document.get("family_prefix") != FAMILY_PREFIX, FINDING_CATALOG_SCHEMA, f"family_prefix must be {FAMILY_PREFIX!r}"),
            (document.get("factory") != FACTORY, FINDING_CATALOG_SCHEMA, f"factory must be {FACTORY!r}"),
            (document.get("generator") != GENERATOR, FINDING_CATALOG_SCHEMA, f"generator must be {GENERATOR!r}"),
            (document.get("n_mills") != N_MILLS, FINDING_CATALOG_PAIR_COUNT, f"n_mills must be {N_MILLS}"),
            (document.get("n_pairs") != N_PAIRS, FINDING_CATALOG_PAIR_COUNT, f"n_pairs must be {N_PAIRS}"),
        )
    )


def _validate_document(meta: object, pair_rows: list[dict[str, Any]], digest: str) -> dict[str, Any]:
    document = _require_object(meta, "catalog")
    _validate_counts(document)
    refuse_when(
        document.get("pairs_sha256") != digest,
        FINDING_PAIRS_SHA_MISMATCH,
        f"pairs.jsonl sha256 {digest} != pinned {document.get('pairs_sha256')}",
    )
    mills_raw = _require_field(document, "mills", "catalog")
    refuse_when(not isinstance(mills_raw, list) or len(mills_raw) != N_MILLS, FINDING_CATALOG_PAIR_COUNT, "mills must list the six qbp-mill* extracts")
    assert isinstance(mills_raw, list)
    slugs: list[str] = []
    mods: list[str] = []
    tickets: list[str] = []
    domains: list[str] = []
    mill_ids: list[str] = []
    for index, (raw, pinned) in enumerate(zip(mills_raw, MILL_SOURCES, strict=True)):
        mill_id, path, mill_sha, plants_path, plants_sha, catalog_first, n_pairs = pinned
        item = _require_object(raw, f"mills[{index}]")
        refuse_first(
            (
                (item.get("mill_id") != mill_id, FINDING_CATALOG_MILL, f"mills[{index}].mill_id must be {mill_id}"),
                (item.get("path") != path, FINDING_CATALOG_MILL, f"mills[{index}].path must be {path}"),
                (item.get("sha256") != mill_sha, FINDING_CATALOG_SCHEMA, f"mills[{index}].sha256 drifted"),
                (item.get("plants") != plants_path, FINDING_CATALOG_MILL, f"mills[{index}].plants drifted"),
                (item.get("plants_sha256") != plants_sha, FINDING_CATALOG_SCHEMA, f"mills[{index}].plants_sha256 drifted"),
                (item.get("catalog_first") != catalog_first, FINDING_CATALOG_SCHEMA, f"mills[{index}].catalog_first drifted"),
                (item.get("n_pairs") != n_pairs, FINDING_CATALOG_PAIR_COUNT, f"mills[{index}].n_pairs drifted"),
            )
        )
        mill_ids.append(mill_id)
    refuse_when(len(pair_rows) != N_PAIRS, FINDING_CATALOG_PAIR_COUNT, f"need {N_PAIRS} pair rows, got {len(pair_rows)}")
    expected_windows = {row[0]: (row[5], row[6]) for row in MILL_SOURCES}
    seen: dict[str, int] = {mill_id: 0 for mill_id in mill_ids}
    for index, entry in enumerate(pair_rows):
        item = _require_object(entry, f"pairs[{index}]")
        mill_id = _require_str(_require_field(item, "mill_id", f"pairs[{index}]"), f"pairs[{index}].mill_id")
        refuse_when(mill_id not in expected_windows, FINDING_CATALOG_MILL, f"pairs[{index}] unknown mill {mill_id}")
        first, n_pairs = expected_windows[mill_id]
        offset = seen[mill_id]
        round_n = _require_int(_require_field(item, "round", f"pairs[{index}]"), f"pairs[{index}].round")
        refuse_when(round_n != first + offset, FINDING_CATALOG_FIELD_INVALID, f"pairs[{index}].round must be {first + offset}")
        seen[mill_id] = offset + 1
        ok = _ctor_args(item.get("ok"), OK_ARG_NAMES, f"pairs[{index}].ok")
        bad = _ctor_args(item.get("bad"), BAD_ARG_NAMES, f"pairs[{index}].bad")
        for plant, label in ((ok, "ok"), (bad, "bad")):
            slug = str(plant["slug"])
            _reject_banned(slug, f"pairs[{index}].{label}")
            slugs.append(slug)
            mods.append(str(plant["mod"]))
            domains.append(str(plant["domain"]))
        tickets.append(str(bad["ticket"]))
        plant_ok = expand_ok(ok)
        plant_bad = expand_bad(bad)
        refuse_when(plant_ok["first_old"] not in plant_ok["src_body"], FINDING_CATALOG_PLANT, f"pairs[{index}].ok first_old not in src_body")
        refuse_when(plant_bad["first_old"] not in plant_bad["src_body"], FINDING_CATALOG_PLANT, f"pairs[{index}].bad first_old not in src_body")
    refuse_when(seen != {mill_id: expected_windows[mill_id][1] for mill_id in mill_ids}, FINDING_CATALOG_PAIR_COUNT, f"pair counts drifted: {seen}")
    _unique("slugs", slugs)
    _unique("mods", mods)
    _unique("tickets", tickets)
    _unique("domains", domains)
    source = _require_object(_require_field(document, "source", "catalog"), "source")
    refuse_when(source.get("lane") != LEGACY_LANE, FINDING_CATALOG_SCHEMA, "source.lane drifted")
    refuse_when(source.get("commit") != LEGACY_COMMIT, FINDING_CATALOG_SCHEMA, "source.commit drifted")
    return document


def _read_pair_rows(path: Path) -> tuple[list[dict[str, Any]], str]:
    payload = path.read_bytes()
    rows = []
    for lineno, line in enumerate(payload.decode("utf-8").splitlines(), start=1):
        if not line:
            continue
        row = load_pair_json(line)
        refuse_when(not isinstance(row, dict), FINDING_CATALOG_NOT_AN_OBJECT, f"{path}:{lineno} is not an object")
        rows.append(row)
    return rows, sha256_bytes(payload)


def load_catalog(path: Path | None = None, *, root: Path | None = None) -> Catalog:
    catalog_path = (path or default_catalog_path(root)).resolve()
    pairs_path = default_pairs_path(catalog_path)
    refuse_when(not catalog_path.is_file(), FINDING_CATALOG_FIELD_MISSING, f"missing {catalog_path}")
    refuse_when(not pairs_path.is_file(), FINDING_CATALOG_FIELD_MISSING, f"missing {pairs_path}")
    pair_rows, digest = _read_pair_rows(pairs_path)
    document = _validate_document(load_strict_json(catalog_path.read_text(encoding="utf-8")), pair_rows, digest)
    mills = tuple(
        Mill(
            mill_id=str(item["mill_id"]),
            path=str(item["path"]),
            sha256=str(item["sha256"]),
            plants=str(item["plants"]),
            plants_sha256=str(item["plants_sha256"]),
            catalog_first=int(item["catalog_first"]),
            n_pairs=int(item["n_pairs"]),
        )
        for item in document["mills"]
    )
    pairs = tuple(
        Pair(
            mill_id=str(entry["mill_id"]),
            round_n=int(entry["round"]),
            ok_args=MappingProxyType(_ctor_args(entry["ok"], OK_ARG_NAMES, f"pairs[{index}].ok")),
            bad_args=MappingProxyType(_ctor_args(entry["bad"], BAD_ARG_NAMES, f"pairs[{index}].bad")),
            ok=MappingProxyType(expand_ok(entry["ok"])),
            bad=MappingProxyType(expand_bad(entry["bad"])),
        )
        for index, entry in enumerate(pair_rows)
    )
    return Catalog(
        path=catalog_path,
        pairs_path=pairs_path,
        family_prefix=FAMILY_PREFIX,
        factory=FACTORY,
        generator=GENERATOR,
        source=MappingProxyType(dict(document["source"])),
        mills=mills,
        pairs=pairs,
        pairs_sha256=digest,
    )


def catalog_check(path: Path | None = None, *, root: Path | None = None) -> Catalog:
    """Load the committed catalog and re-assert the leftover-mill contract."""

    catalog = load_catalog(path, root=root)
    refuse_when(len(catalog.mills) != N_MILLS, FINDING_CATALOG_PAIR_COUNT, "mill count drifted")
    refuse_when(len(catalog.pairs) != N_PAIRS, FINDING_CATALOG_PAIR_COUNT, "pair count drifted")
    return catalog


bind_import_twin(__name__)
