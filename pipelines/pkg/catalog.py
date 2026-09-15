#!/usr/bin/env python3
"""PKG plant catalog: AST extract plus compact ``plants.jsonl``.

``plants_from_source`` walks legacy mill scripts as text (``ast.parse``
only, ``exec: false``). The committed catalog is the ok/fail identity
extract from ``origin/legacy-mill-lane`` (r163–r196 in this slice).
Mill scripts, loop drivers, attest-wave / leftover3 / licrep mills, and
the demoted r98–r162 digest/lock-yank twins are not vendored.
"""

from __future__ import annotations

import ast
import hashlib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

if __name__.startswith("pipelines."):
    from ..tag_jsonutil import load_strict_json
else:
    from tag_jsonutil import load_strict_json

from ._contract import (
    CATALOG_FILENAME,
    CATALOG_FORMAT,
    CATALOG_ID,
    FACTORY,
    FINDING_AST_NOT_A_PLANT,
    FINDING_CATALOG_EMPTY,
    FINDING_CATALOG_FILE_MISSING,
    FINDING_CATALOG_PAIR_STRIDE,
    FINDING_CATALOG_SHA256_MISMATCH,
    FINDING_DUPLICATE_ID,
    FINDING_FIELD_INVALID,
    FINDING_FIELD_MISSING,
    FINDING_PAIR_OUT_OF_DOMAIN,
    FINDING_ROUND_OUT_OF_DOMAIN,
    GENERATOR,
    PLANTS_FILENAME,
    QUOTA_PER_ROUND,
    SOURCE_COMMIT,
    SOURCE_REF,
    bind_import_twin,
    refuse,
    refuse_first,
    refuse_when,
    shown,
)

ID_PREFIX = "pkg"
SOURCE_NAME = "pkg-mill-r163.py"
OK_KINDS = frozenset({
    "cosign_reusable",
    "oidc_publisher",
    "bottle_rebuild",
    "nix_nar",
    "gpg_portal",
    "nuget_snupkg",
})
FAIL_KIND = "fail_leftover"
ROLES = frozenset({"ok", "fail"})
PLANT_FIELDS = (
    "record_id",
    "source_round",
    "index",
    "role",
    "kind",
    "slug",
    "plant",
    "seed",
    "first",
    "change",
    "term",
    "leftover",
    "goal",
    "plan",
    "source_name",
)
__all__ = [
    "CATALOG_ID",
    "FAIL_KIND",
    "FACTORY",
    "GENERATOR",
    "ID_PREFIX",
    "OK_KINDS",
    "PLANT_FIELDS",
    "QUOTA_PER_ROUND",
    "SOURCE_NAME",
    "WAVE_ROUNDS",
    "Catalog",
    "Plant",
    "catalog_check",
    "load_catalog",
    "plant_from_mapping",
    "plants_for_round",
    "plants_from_source",
]


@dataclass(frozen=True)
class Plant:
    """One AST-extracted PKG identity. Full mill payloads stay out."""

    record_id: str
    source_round: int
    index: int
    role: str
    kind: str
    slug: str
    plant: str
    seed: str
    first: str
    change: str
    term: str
    leftover: str
    goal: str
    plan: str
    source_name: str

    def as_mapping(self) -> dict[str, Any]:
        return {field: getattr(self, field) for field in PLANT_FIELDS}


@dataclass(frozen=True)
class Catalog:
    catalog_id: str
    plants: tuple[Plant, ...]

    def plant(self, record_id: str) -> Plant:
        for item in self.plants:
            if item.record_id == record_id:
                return item
        refuse(FINDING_FIELD_INVALID, f"no plant {shown(record_id)} in the catalog")


def _literal(node: ast.AST) -> Any:
    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError, SyntaxError) as exc:
        refuse(FINDING_AST_NOT_A_PLANT, f"catalog argument is not a literal: {exc}")


def _optional_literal(node: ast.AST) -> Any:
    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError, SyntaxError):
        return None


def _text(value: Any) -> str:
    return value if isinstance(value, str) else ""


def _catalog_first(tree: ast.Module) -> int:
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if isinstance(target, ast.Name) and target.id == "CATALOG_FIRST":
            value = _optional_literal(node.value)
            refuse_when(
                type(value) is not int or value < 1,
                FINDING_AST_NOT_A_PLANT,
                f"CATALOG_FIRST must be a positive int, got {shown(value)}",
            )
            return value
    return 1


def _pairs_function(tree: ast.Module) -> ast.FunctionDef | None:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "_pairs":
            return node
    return None


def _returned_list(fn: ast.FunctionDef) -> ast.List | None:
    for stmt in reversed(fn.body):
        if isinstance(stmt, ast.Return) and isinstance(stmt.value, ast.List):
            return stmt.value
    return None


def _module_pairs_list(tree: ast.Module) -> ast.List | None:
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if isinstance(target, ast.Name) and target.id == "PAIRS":
            if isinstance(node.value, ast.List):
                return node.value
    return None


def _pair_elts(tree: ast.Module) -> list[ast.Tuple]:
    fn = _pairs_function(tree)
    listed = _returned_list(fn) if fn is not None else None
    if listed is None:
        listed = _module_pairs_list(tree)
    refuse_when(listed is None, FINDING_AST_NOT_A_PLANT, "source has no _pairs() list")
    rows: list[ast.Tuple] = []
    for elt in listed.elts:
        refuse_when(
            not isinstance(elt, ast.Tuple) or len(elt.elts) != 4,
            FINDING_AST_NOT_A_PLANT,
            "each catalog row must be a 4-tuple (ok_kind, ok, fail_kind, fail)",
        )
        rows.append(elt)
    return rows


def _spec_strings(node: ast.AST) -> dict[str, str]:
    refuse_when(not isinstance(node, ast.Dict), FINDING_AST_NOT_A_PLANT, "spec must be a dict")
    out: dict[str, str] = {}
    for key_node, value_node in zip(node.keys, node.values):
        if not isinstance(key_node, ast.Constant) or not isinstance(key_node.value, str):
            continue
        resolved = _optional_literal(value_node)
        if isinstance(resolved, str):
            out[key_node.value] = resolved
    return out


def _kind_name(node: ast.AST) -> str:
    value = _literal(node)
    refuse_when(not isinstance(value, str) or not value, FINDING_AST_NOT_A_PLANT, "kind must be a string")
    return value


def _require_plant_fields(values: Mapping[str, Any], where: str) -> dict[str, Any]:
    missing = [field for field in PLANT_FIELDS if field not in values]
    refuse_when(bool(missing), FINDING_FIELD_MISSING, f"{where} missing {missing}")
    checked: dict[str, Any] = {}
    for field in PLANT_FIELDS:
        value = values[field]
        if field == "source_round":
            refuse_when(
                type(value) is not int or value < 1,
                FINDING_FIELD_INVALID,
                f"{where}.source_round must be a positive int, got {shown(value)}",
            )
            checked[field] = value
            continue
        if field == "index":
            refuse_when(
                type(value) is not int or value not in (1, 2),
                FINDING_FIELD_INVALID,
                f"{where}.index must be 1 or 2, got {shown(value)}",
            )
            checked[field] = value
            continue
        refuse_when(
            not isinstance(value, str),
            FINDING_FIELD_INVALID,
            f"{where}.{field} must be a string, got {shown(value)}",
        )
        if field in ("leftover", "goal", "plan"):
            checked[field] = value
            continue
        refuse_when(
            not value,
            FINDING_FIELD_INVALID,
            f"{where}.{field} must be a non-empty string, got {shown(value)}",
        )
        checked[field] = value
    refuse_when(
        checked["role"] not in ROLES,
        FINDING_FIELD_INVALID,
        f"{where}.role must be ok or fail, got {shown(checked['role'])}",
    )
    if checked["role"] == "ok":
        refuse_when(
            checked["kind"] not in OK_KINDS,
            FINDING_FIELD_INVALID,
            f"{where}.kind {shown(checked['kind'])} is not an ok builder",
        )
    else:
        refuse_when(
            checked["kind"] != FAIL_KIND,
            FINDING_FIELD_INVALID,
            f"{where}.kind must be {FAIL_KIND}, got {shown(checked['kind'])}",
        )
    expected = f"pkg-r{checked['source_round']}-{checked['slug']}"
    refuse_when(
        checked["record_id"] != expected,
        FINDING_FIELD_INVALID,
        f"{where}.record_id must be {expected}, got {shown(checked['record_id'])}",
    )
    return checked


def plant_from_mapping(values: Mapping[str, Any], where: str = "plant") -> Plant:
    """Validate one mapping (AST row or JSON) into a frozen plant."""

    return Plant(**_require_plant_fields(values, where))


def _check_unique(plants: tuple[Plant, ...]) -> None:
    seen_ids: set[str] = set()
    seen_slugs: set[str] = set()
    for item in plants:
        refuse_when(item.record_id in seen_ids, FINDING_DUPLICATE_ID, f"duplicate id {item.record_id}")
        refuse_when(item.slug in seen_slugs, FINDING_DUPLICATE_ID, f"duplicate slug {item.slug}")
        seen_ids.add(item.record_id)
        seen_slugs.add(item.slug)


def _draft(
    round_n: int,
    index: int,
    role: str,
    kind: str,
    spec: Mapping[str, str],
    source_name: str,
) -> dict[str, Any]:
    slug = spec.get("slug", "")
    return {
        "record_id": f"pkg-r{round_n}-{slug}",
        "source_round": round_n,
        "index": index,
        "role": role,
        "kind": kind,
        "slug": slug,
        "plant": spec.get("plant", ""),
        "seed": spec.get("seed", ""),
        "first": spec.get("first", ""),
        "change": spec.get("change", ""),
        "term": spec.get("term", ""),
        "leftover": spec.get("leftover", ""),
        "goal": spec.get("goal", ""),
        "plan": spec.get("plan", ""),
        "source_name": source_name,
    }


def plants_from_source(text: str, source_name: str = SOURCE_NAME) -> tuple[Plant, ...]:
    """AST-extract ok/fail 4-tuples. Never executes the mill."""

    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        refuse(FINDING_AST_NOT_A_PLANT, f"mill source is not parseable: {exc}")
    first = _catalog_first(tree)
    ordered: list[Plant] = []
    for offset, elt in enumerate(_pair_elts(tree)):
        round_n = first + offset
        ok_kind = _kind_name(elt.elts[0])
        fail_kind = _kind_name(elt.elts[2])
        ok_spec = _spec_strings(elt.elts[1])
        fail_spec = _spec_strings(elt.elts[3])
        ordered.append(
            plant_from_mapping(
                _draft(round_n, 1, "ok", ok_kind, ok_spec, source_name),
                f"ok r{round_n}",
            )
        )
        ordered.append(
            plant_from_mapping(
                _draft(round_n, 2, "fail", fail_kind, fail_spec, source_name),
                f"fail r{round_n}",
            )
        )
    refuse_when(not ordered, FINDING_CATALOG_EMPTY, "extracted catalog is empty")
    plants = tuple(ordered)
    _check_unique(plants)
    return plants


def catalog_check(plants: tuple[Plant, ...] | None = None) -> dict[str, Any]:
    items = load_catalog().plants if plants is None else plants
    refuse_when(not items, FINDING_CATALOG_EMPTY, "catalog is empty")
    _check_unique(items)
    rounds = tuple(sorted({plant.source_round for plant in items}))
    refuse_when(not rounds, FINDING_CATALOG_EMPTY, "catalog has no rounds")
    for rnd in rounds:
        chunk = tuple(plant for plant in items if plant.source_round == rnd)
        refuse_when(
            len(chunk) != QUOTA_PER_ROUND,
            FINDING_CATALOG_PAIR_STRIDE,
            f"r{rnd} has {len(chunk)} plants, not {QUOTA_PER_ROUND}",
        )
        refuse_when(
            (chunk[0].role, chunk[1].role) != ("ok", "fail"),
            FINDING_CATALOG_PAIR_STRIDE,
            f"r{rnd} must be ok then fail",
        )
    return {
        "status": "ok",
        "catalog_id": CATALOG_ID,
        "plants": len(items),
        "pairs": len(items) // QUOTA_PER_ROUND,
        "rounds": list(rounds),
        "first_round": rounds[0],
        "last_round": rounds[-1],
        "factory": FACTORY,
        "generator": GENERATOR,
    }


def plants_for_round(round_n: int, plants: tuple[Plant, ...] | None = None) -> tuple[Plant, ...]:
    items = load_catalog().plants if plants is None else plants
    rounds = tuple(sorted({plant.source_round for plant in items}))
    refuse_first(
        (
            (
                type(round_n) is not int,
                FINDING_ROUND_OUT_OF_DOMAIN,
                f"round must be an int, got {shown(round_n)}",
            ),
            (
                type(round_n) is int and round_n not in rounds,
                FINDING_ROUND_OUT_OF_DOMAIN,
                f"round must be one of {list(rounds)}, got {shown(round_n)}",
            ),
        )
    )
    chunk = tuple(plant for plant in items if plant.source_round == round_n)
    refuse_when(
        len(chunk) != QUOTA_PER_ROUND,
        FINDING_PAIR_OUT_OF_DOMAIN,
        f"no plant pair for r{round_n}",
    )
    return chunk


def default_catalog_dir() -> Path:
    return Path(__file__).resolve().parent


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _read_jsonl(path: Path) -> tuple[Any, ...]:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        refuse(FINDING_CATALOG_FILE_MISSING, f"{path} is unreadable: {exc}")
    refuse_when(
        not raw.endswith("\n") or "\r" in raw,
        FINDING_FIELD_INVALID,
        f"{PLANTS_FILENAME} must be LF-framed jsonl",
    )
    rows: list[Any] = []
    for index, line in enumerate(raw.splitlines(), start=1):
        refuse_when(not line, FINDING_FIELD_INVALID, f"{PLANTS_FILENAME}:{index} is empty")
        try:
            rows.append(load_strict_json(line))
        except ValueError as exc:
            refuse(FINDING_FIELD_INVALID, f"{PLANTS_FILENAME}:{index} is not strict JSON: {exc}")
    return tuple(rows)


def _load_meta(catalog_dir: Path) -> dict[str, Any]:
    meta_path = catalog_dir / CATALOG_FILENAME
    try:
        meta = load_strict_json(meta_path.read_text(encoding="utf-8"))
    except OSError as exc:
        refuse(FINDING_CATALOG_FILE_MISSING, f"{meta_path} is unreadable: {exc}")
    except ValueError as exc:
        refuse(FINDING_FIELD_INVALID, f"{CATALOG_FILENAME} is not strict JSON: {exc}")
    refuse_when(not isinstance(meta, dict), FINDING_FIELD_INVALID, "CATALOG.json must be an object")
    return meta


def _plants_from_directory(catalog_dir: Path) -> tuple[Plant, ...]:
    meta = _load_meta(catalog_dir)
    refuse_first(
        (
            (meta.get("catalog_format") != CATALOG_FORMAT, FINDING_FIELD_INVALID, "catalog_format"),
            (meta.get("catalog_id") != CATALOG_ID, FINDING_FIELD_INVALID, "catalog_id"),
            (meta.get("factory") != FACTORY, FINDING_FIELD_INVALID, "factory"),
            (meta.get("generator") != GENERATOR, FINDING_FIELD_INVALID, "generator"),
            (meta.get("source_ref") != SOURCE_REF, FINDING_FIELD_INVALID, "source_ref"),
            (meta.get("source_commit") != SOURCE_COMMIT, FINDING_FIELD_INVALID, "source_commit"),
        )
    )
    plants_sha256 = meta.get("plants_sha256")
    refuse_when(
        not isinstance(plants_sha256, str) or not plants_sha256,
        FINDING_FIELD_INVALID,
        "plants_sha256 must be a non-empty string",
    )
    plants_path = catalog_dir / PLANTS_FILENAME
    try:
        plants_bytes = plants_path.read_bytes()
    except OSError as exc:
        refuse(FINDING_CATALOG_FILE_MISSING, f"{plants_path} is unreadable: {exc}")
    digest = _sha256_bytes(plants_bytes)
    refuse_when(
        digest != plants_sha256,
        FINDING_CATALOG_SHA256_MISMATCH,
        f"{PLANTS_FILENAME} digest {digest} != catalog pin {plants_sha256}",
    )
    rows = _read_jsonl(plants_path)
    plants = tuple(
        plant_from_mapping(row, f"{PLANTS_FILENAME}:{index}")
        for index, row in enumerate(rows, start=1)
    )
    refuse_when(not plants, FINDING_CATALOG_EMPTY, "plants.jsonl is empty")
    _check_unique(plants)
    return plants


def _load_committed_plants() -> tuple[Plant, ...]:
    return _plants_from_directory(default_catalog_dir())


_CATALOG = Catalog(CATALOG_ID, _load_committed_plants())
WAVE_ROUNDS = tuple(sorted({plant.source_round for plant in _CATALOG.plants}))


def load_catalog() -> Catalog:
    return _CATALOG


bind_import_twin(__name__)
