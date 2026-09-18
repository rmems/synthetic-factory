#!/usr/bin/env python3
"""Pinned KCL leftover catalog: AST extract (never execute), load, and check.

A catalog directory holds ``CATALOG.json`` and ``plants.jsonl``. Historical
mill scripts are read only as text through :func:`ast_extract_plants`. The
committed catalog pins every plant identity; twelve rows keep full bodies
and the rest are compact identity lines without pair/plant metric bodies.
"""

from __future__ import annotations

import ast
import hashlib
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ._contract import (
    BANNED_ID_TOKENS,
    CATALOG_FILENAME,
    CATALOG_FORMAT,
    CATALOG_SLICE,
    DEFAULT_CATALOG_ID,
    FINDING_PLANT_IDENTITY_ONLY,
    REPRESENTATIVE_BODY_COUNT,
    ROW_KIND_IDENTITY,
    ROW_KIND_REPRESENTATIVE,
    EXTRACT_METHOD,
    FACTORY,
    FULL_MILL_COUNTS,
    FULL_PAIR_COUNT,
    FULL_PLANT_COUNT,
    FULL_ROW_COUNT,
    FAMILY_PREFIX,
    FINDING_BANNED,
    FINDING_CATALOG_FIELD_INVALID,
    FINDING_CATALOG_FIELD_MISSING,
    FINDING_CATALOG_FILE_MISSING,
    FINDING_CATALOG_SHA256_MISMATCH,
    FINDING_FACTORY_NOT_REGISTERED,
    FINDING_MILL_NOT_FOUND,
    FINDING_PLANT_DUPLICATE,
    FINDING_PLANT_FIELD_INVALID,
    FINDING_PLANT_FIELD_MISSING,
    FINDING_PLANT_NOT_FOUND,
    FINDING_SOURCE_NOT_PARSEABLE,
    FINDING_VENDOR_PATH,
    LEGACY_COMMIT,
    LEGACY_REF,
    PAIR_KEYS,
    PLANTS_FILENAME,
    QUOTA_PER_ROUND,
    RECORD_KIND,
    ROW_KEYS,
    SHAPE_PAIR,
    SHAPE_ROW,
    SOURCE_MILLS,
    VENDOR_GLOBS,
    bind_import_twin,
    default_catalog_dir,
    load_strict_json,
    refuse,
    refuse_first,
    refuse_when,
    repo_root,
)

MILL_ID_RE = re.compile(r"^kcl_(pref|u[0-9]+|r[0-9]+)$")
SLUG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")

__all__ = [
    "Catalog",
    "Mill",
    "Plant",
    "ast_extract_plants",
    "catalog_check",
    "default_catalog_dir",
    "load_catalog",
    "refuse_vendor_paths",
    "row_to_pair",
    "sha256_bytes",
    "spec_for",
]


@dataclass(frozen=True)
class Plant:
    plant_id: str
    mill_id: str
    source: str
    base_round: int
    shape: str
    slug: str
    plant: str
    payload: Mapping[str, Any]
    row_kind: str = ROW_KIND_REPRESENTATIVE


@dataclass(frozen=True)
class Mill:
    mill_id: str
    base_round: int
    source: str
    shape: str
    plant_count: int


@dataclass(frozen=True)
class Catalog:
    catalog_id: str
    directory: Path
    factory: str
    plants_sha256: str
    plants: tuple[Plant, ...]
    mills: tuple[Mill, ...]
    meta: Mapping[str, Any]

    def plant(self, plant_id: str) -> Plant:
        for item in self.plants:
            if item.plant_id == plant_id:
                return item
        refuse(FINDING_PLANT_NOT_FOUND, f"no plant {plant_id!r} in the catalog")

    def mill_plants(self, mill_id: str) -> tuple[Plant, ...]:
        found = tuple(item for item in self.plants if item.mill_id == mill_id)
        refuse_when(not found, FINDING_MILL_NOT_FOUND, f"no mill {mill_id!r} in the catalog")
        return found


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def refuse_vendor_paths(root: Path | None = None) -> None:
    """Fail closed if a leftover mill script was copied into this package."""

    package = (root or repo_root()) / "pipelines" / "kcl"
    hits: list[str] = []
    for pattern in VENDOR_GLOBS:
        hits.extend(str(path.relative_to(package.parent.parent)) for path in package.glob(pattern))
    refuse_when(bool(hits), FINDING_VENDOR_PATH, f"vendored mill path {hits}")


def _try_const_kwargs(node: ast.Call) -> dict[str, str | int] | None:
    if node.args or any(kw.arg is None for kw in node.keywords):
        return None
    payload: dict[str, str | int] = {}
    for kw in node.keywords:
        assert kw.arg is not None
        if not isinstance(kw.value, ast.Constant) or isinstance(kw.value.value, bool):
            return None
        if not isinstance(kw.value.value, (str, int)):
            return None
        payload[kw.arg] = kw.value.value
    return payload


def _try_const_args(node: ast.Call, arity: int) -> list[str | int] | None:
    if node.keywords or len(node.args) != arity:
        return None
    values: list[str | int] = []
    for arg in node.args:
        if not isinstance(arg, ast.Constant) or isinstance(arg.value, bool):
            return None
        if not isinstance(arg.value, (str, int)):
            return None
        values.append(arg.value)
    return values


def _try_const_dict(node: ast.Dict) -> dict[str, str | int] | None:
    payload: dict[str, str | int] = {}
    for key_node, val_node in zip(node.keys, node.values):
        if not isinstance(key_node, ast.Constant) or not isinstance(key_node.value, str):
            return None
        if not isinstance(val_node, ast.Constant) or isinstance(val_node.value, bool):
            return None
        if not isinstance(val_node.value, (str, int)):
            return None
        payload[key_node.value] = val_node.value
    return payload


def _module_pairs_lists(tree: ast.AST) -> tuple[ast.List, ...]:
    lists: list[ast.List] = []
    body = getattr(tree, "body", ())
    for node in body:
        value = None
        if (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "PAIRS"
        ):
            value = node.value
        elif isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "PAIRS" for target in node.targets
        ):
            value = node.value
        if isinstance(value, ast.List):
            lists.append(value)
    return tuple(lists)


def row_to_pair(row: Mapping[str, Any]) -> dict[str, str]:
    """Expand an ``mk()`` row into the leftover ``pair()`` contract."""

    idx = int(row["idx"])
    plant = str(row["plant"])
    slug = str(row["slug"])
    field = str(row["field"])
    fail = str(row["fail"])
    fix = str(row["fix"])
    hide_key = str(row["hide_key"])
    hide_old = str(row["hide_old"])
    hide_new = str(row["hide_new"])
    crash = str(row["crash"])
    new_vs = str(row["new_vs"])
    app = plant.replace("-prod", "-api")
    hide_old_line = f"{hide_key}: {hide_old}\n"
    hide_new_line = f"{hide_key}: {hide_new}\n"
    val_key = field.split(".")[-1]
    values_fail = f"{val_key}: {fail}\n{hide_old_line}"
    values_fix = f"{val_key}: {fix}\n{hide_old_line}"
    return {
        "plant": plant,
        "app": app,
        "chart": f"{1 + (idx % 8)}.{1 + (idx % 9)}.{idx % 10}",
        "slug": slug,
        "field": field,
        "fail_val": fail,
        "fix_val": fix,
        "hide_path": hide_key,
        "hide_old": hide_old_line,
        "hide_new": hide_new_line,
        "values_fail": values_fail,
        "values_fix": values_fix,
        "tpl": f"  {val_key}: {{{{ .Values.{val_key} }}}}\n",
        "log": f"{crash} leftover {field} {fail} CrashLoop",
        "live_ok": f"{field}={fix}",
        "hide_name": f"{hide_key} {hide_new}",
        "new_vs": new_vs,
        "seed": f"leftover {field} {fail}; {crash} CrashLoop",
        "n2": f"replica n2 still {field} {fail} after git {fix}",
        "ci": (
            f"# {field} must be {fix}. Never {hide_key} {hide_new} to hide leftover {fail}."
        ),
        "handoff": (
            f"LEFTOVER: replica n2 still {field} {fail}. "
            f"Platform: delete leftover RS. No {hide_key} hide."
        ),
        "pytest_ok": (
            "test_fix\ntest_not_hide\ntest_not_clone\ntest_pods_ready\ntest_no_force\ntest_field"
        ),
        "pytest_fail": f"test_fix_all FAILED b=={fail}",
        "tmpl_test": "test_template_matches_git",
        "rs": f"k{601 + idx}",
    }


def _pair_row(
    raw: Mapping[str, Any],
    *,
    mill_id: str,
    source: str,
    base_round: int,
    index: int,
) -> dict[str, Any]:
    missing = [key for key in PAIR_KEYS if key not in raw]
    refuse_when(bool(missing), FINDING_PLANT_FIELD_MISSING, f"{source}[{index}] missing {missing}")
    payload = {key: raw[key] for key in PAIR_KEYS}
    for key in PAIR_KEYS:
        refuse_when(
            not isinstance(payload[key], str),
            FINDING_PLANT_FIELD_INVALID,
            f"{source}[{index}].{key} must be a string",
        )
        payload[key] = str(payload[key])
    refuse_when(
        not payload["plant"] or not payload["slug"],
        FINDING_PLANT_FIELD_INVALID,
        f"{source}[{index}] plant/slug",
    )
    slug = payload["slug"]
    for token in BANNED_ID_TOKENS:
        refuse_when(token in slug, FINDING_BANNED, f"{source}[{index}]: banned slug token {token!r}")
    refuse_when(not SLUG_RE.fullmatch(slug), FINDING_PLANT_FIELD_INVALID, f"{source}[{index}].slug")
    return {
        "base_round": base_round,
        "mill_id": mill_id,
        "payload": payload,
        "plant": payload["plant"],
        "plant_id": f"{mill_id}:{slug}",
        "shape": SHAPE_PAIR,
        "slug": slug,
        "source": source,
    }


def _row_row(
    values: list[str | int],
    *,
    mill_id: str,
    source: str,
    base_round: int,
    index: int,
) -> dict[str, Any]:
    refuse_when(len(values) != len(ROW_KEYS), FINDING_SOURCE_NOT_PARSEABLE, f"{source}[{index}] arity")
    payload = {key: values[offset] for offset, key in enumerate(ROW_KEYS)}
    refuse_when(
        payload["idx"] != index,
        FINDING_SOURCE_NOT_PARSEABLE,
        f"{source}[{index}] idx {payload['idx']!r} != {index}",
    )
    for key in ROW_KEYS:
        if key == "idx":
            refuse_when(
                not isinstance(payload[key], int) or isinstance(payload[key], bool),
                FINDING_PLANT_FIELD_INVALID,
                f"{source}[{index}].idx must be an int",
            )
            continue
        refuse_when(
            not isinstance(payload[key], str),
            FINDING_PLANT_FIELD_INVALID,
            f"{source}[{index}].{key} must be a string",
        )
    slug = str(payload["slug"])
    plant = str(payload["plant"])
    refuse_when(not plant or not slug, FINDING_PLANT_FIELD_INVALID, f"{source}[{index}] plant/slug")
    for token in BANNED_ID_TOKENS:
        refuse_when(token in slug, FINDING_BANNED, f"{source}[{index}]: banned slug token {token!r}")
    refuse_when(not SLUG_RE.fullmatch(slug), FINDING_PLANT_FIELD_INVALID, f"{source}[{index}].slug")
    return {
        "base_round": base_round,
        "mill_id": mill_id,
        "payload": payload,
        "plant": plant,
        "plant_id": f"{mill_id}:{slug}",
        "shape": SHAPE_ROW,
        "slug": slug,
        "source": source,
    }


def ast_extract_plants(
    source: str,
    *,
    mill_id: str,
    path: str,
    base_round: int,
    shape: str,
) -> tuple[dict[str, Any], ...]:
    """Return leftover plants from mill/plants source text. Never execute it."""

    refuse_when(not MILL_ID_RE.fullmatch(mill_id), FINDING_PLANT_FIELD_INVALID, f"mill_id {mill_id}")
    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError as exc:
        refuse(FINDING_SOURCE_NOT_PARSEABLE, f"{path} does not parse: {exc}")
    rows: list[dict[str, Any]] = []
    if shape == SHAPE_PAIR:
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
                continue
            if node.func.id != "pair":
                continue
            payload = _try_const_kwargs(node)
            if payload is None:
                continue
            rows.append(
                _pair_row(
                    payload,
                    mill_id=mill_id,
                    source=path,
                    base_round=base_round,
                    index=len(rows),
                )
            )
        for pair_list in _module_pairs_lists(tree):
            for elt in pair_list.elts:
                if not isinstance(elt, ast.Dict):
                    continue
                payload = _try_const_dict(elt)
                if payload is None:
                    continue
                rows.append(
                    _pair_row(
                        payload,
                        mill_id=mill_id,
                        source=path,
                        base_round=base_round,
                        index=len(rows),
                    )
                )
    elif shape == SHAPE_ROW:
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
                continue
            if node.func.id != "mk":
                continue
            values = _try_const_args(node, len(ROW_KEYS))
            if values is None:
                continue
            rows.append(
                _row_row(
                    values,
                    mill_id=mill_id,
                    source=path,
                    base_round=base_round,
                    index=len(rows),
                )
            )
    else:
        refuse(FINDING_SOURCE_NOT_PARSEABLE, f"{path}: unknown extract shape {shape!r}")
    refuse_when(not rows, FINDING_SOURCE_NOT_PARSEABLE, f"{path} has no extractable plants")
    seen: set[str] = set()
    for row in rows:
        refuse_when(row["plant_id"] in seen, FINDING_PLANT_DUPLICATE, f"duplicate {row['plant_id']}")
        seen.add(row["plant_id"])
    return tuple(rows)


def _require_text(value: Any, where: str, code: str) -> str:
    refuse_when(not isinstance(value, str) or not value, code, f"{where} must be a non-empty string")
    assert isinstance(value, str)
    return value


def _require_int(value: Any, where: str, code: str, minimum: int = 0) -> int:
    refuse_when(
        not isinstance(value, int) or isinstance(value, bool) or value < minimum,
        code,
        f"{where} must be an int >= {minimum}",
    )
    assert isinstance(value, int)
    return value


def _plant_from_row(row: Any, where: str) -> Plant:
    refuse_when(not isinstance(row, dict), FINDING_PLANT_FIELD_INVALID, f"{where} must be an object")
    assert isinstance(row, dict)
    mill_id = _require_text(row.get("mill_id"), f"{where}.mill_id", FINDING_PLANT_FIELD_INVALID)
    refuse_when(not MILL_ID_RE.fullmatch(mill_id), FINDING_PLANT_FIELD_INVALID, f"{where}.mill_id")
    slug = _require_text(row.get("slug"), f"{where}.slug", FINDING_PLANT_FIELD_INVALID)
    refuse_when(not SLUG_RE.fullmatch(slug), FINDING_PLANT_FIELD_INVALID, f"{where}.slug")
    plant_id = _require_text(row.get("plant_id"), f"{where}.plant_id", FINDING_PLANT_FIELD_INVALID)
    expected = f"{mill_id}:{slug}"
    refuse_when(
        plant_id != expected,
        FINDING_PLANT_FIELD_INVALID,
        f"{where}.plant_id must be {expected}",
    )
    shape = _require_text(row.get("shape"), f"{where}.shape", FINDING_PLANT_FIELD_INVALID)
    source = _require_text(row.get("source"), f"{where}.source", FINDING_PLANT_FIELD_MISSING)
    base_round = _require_int(
        row.get("base_round"), f"{where}.base_round", FINDING_PLANT_FIELD_INVALID, 1
    )
    row_kind_raw = row.get("row_kind")
    payload_raw = row.get("payload")
    if row_kind_raw is None:
        row_kind = ROW_KIND_REPRESENTATIVE
    else:
        row_kind = _require_text(row_kind_raw, f"{where}.row_kind", FINDING_PLANT_FIELD_INVALID)
        refuse_when(
            row_kind not in {ROW_KIND_REPRESENTATIVE, ROW_KIND_IDENTITY},
            FINDING_PLANT_FIELD_INVALID,
            f"{where}.row_kind",
        )
    if row_kind == ROW_KIND_IDENTITY:
        refuse_when(
            payload_raw is not None,
            FINDING_PLANT_FIELD_INVALID,
            f"{where}.payload must be omitted for identity rows",
        )
        plant_name = _require_text(row.get("plant"), f"{where}.plant", FINDING_PLANT_FIELD_MISSING)
        return Plant(
            plant_id=plant_id,
            mill_id=mill_id,
            source=source,
            base_round=base_round,
            shape=shape,
            slug=slug,
            plant=plant_name,
            payload={},
            row_kind=ROW_KIND_IDENTITY,
        )
    refuse_when(not isinstance(payload_raw, dict), FINDING_PLANT_FIELD_INVALID, f"{where}.payload")
    assert isinstance(payload_raw, dict)
    if shape == SHAPE_PAIR:
        built = _pair_row(
            payload_raw,
            mill_id=mill_id,
            source=source,
            base_round=base_round,
            index=0,
        )
    elif shape == SHAPE_ROW:
        values = [payload_raw.get(key) for key in ROW_KEYS]
        built = _row_row(
            values,  # type: ignore[arg-type]
            mill_id=mill_id,
            source=source,
            base_round=base_round,
            index=int(payload_raw.get("idx", 0)),
        )
    else:
        refuse(FINDING_PLANT_FIELD_INVALID, f"{where}.shape must be pair or row")
    return Plant(
        plant_id=built["plant_id"],
        mill_id=mill_id,
        source=built["source"],
        base_round=built["base_round"],
        shape=shape,
        slug=slug,
        plant=built["plant"],
        payload=built["payload"],
        row_kind=ROW_KIND_REPRESENTATIVE,
    )


def spec_for(plant: Plant) -> dict[str, str]:
    """Return the leftover ``pair()`` spec used by generate."""

    refuse_when(
        plant.row_kind == ROW_KIND_IDENTITY,
        FINDING_PLANT_IDENTITY_ONLY,
        f"{plant.plant_id} is an identity pin without a pair body",
    )
    if plant.shape == SHAPE_PAIR:
        return {key: str(plant.payload[key]) for key in PAIR_KEYS}
    if plant.shape == SHAPE_ROW:
        return row_to_pair(plant.payload)
    refuse(FINDING_PLANT_FIELD_INVALID, f"{plant.plant_id} has unknown shape {plant.shape}")


def _registry_factory_ids() -> set[str]:
    path = repo_root() / "config" / "FACTORY-REGISTRY.json"
    try:
        payload = load_strict_json(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        refuse(FINDING_FACTORY_NOT_REGISTERED, f"factory registry is unreadable: {exc}")
    factories = payload.get("factories") if isinstance(payload, dict) else None
    refuse_when(not isinstance(factories, list), FINDING_FACTORY_NOT_REGISTERED, "factories")
    assert isinstance(factories, list)
    return {
        row.get("path_id")
        for row in factories
        if isinstance(row, dict) and isinstance(row.get("path_id"), str)
    }


def _read_jsonl(path: Path) -> tuple[Any, ...]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        refuse(FINDING_CATALOG_FILE_MISSING, f"{path} is unreadable: {exc}")
    refuse_when(
        not text.endswith("\n") or "\r" in text,
        FINDING_CATALOG_FIELD_INVALID,
        f"{path.name} must be LF-framed jsonl",
    )
    rows = []
    for index, line in enumerate(text.splitlines(), start=1):
        refuse_when(not line, FINDING_CATALOG_FIELD_INVALID, f"{path.name}:{index} is empty")
        try:
            rows.append(load_strict_json(line))
        except ValueError as exc:
            refuse(FINDING_CATALOG_FIELD_INVALID, f"{path.name}:{index} is not strict JSON: {exc}")
    return tuple(rows)


def _mill_from_row(row: Any, where: str) -> Mill:
    refuse_when(not isinstance(row, dict), FINDING_CATALOG_FIELD_INVALID, f"{where} must be an object")
    assert isinstance(row, dict)
    mill_id = _require_text(row.get("mill_id"), f"{where}.mill_id", FINDING_CATALOG_FIELD_INVALID)
    refuse_when(not MILL_ID_RE.fullmatch(mill_id), FINDING_CATALOG_FIELD_INVALID, f"{where}.mill_id")
    return Mill(
        mill_id=mill_id,
        base_round=_require_int(
            row.get("base_round"), f"{where}.base_round", FINDING_CATALOG_FIELD_INVALID, 1
        ),
        source=_require_text(row.get("source"), f"{where}.source", FINDING_CATALOG_FIELD_INVALID),
        shape=_require_text(row.get("shape"), f"{where}.shape", FINDING_CATALOG_FIELD_INVALID),
        plant_count=_require_int(
            row.get("plant_count"), f"{where}.plant_count", FINDING_CATALOG_FIELD_INVALID, 1
        ),
    )


def load_catalog(directory: Path | None = None, *, root: Path | None = None) -> Catalog:
    """Load a catalog directory and refuse unless every pin holds."""

    catalog_dir = Path(default_catalog_dir(root) if directory is None else directory)
    meta_path = catalog_dir / CATALOG_FILENAME
    plants_path = catalog_dir / PLANTS_FILENAME
    try:
        meta = load_strict_json(meta_path.read_text(encoding="utf-8"))
    except OSError as exc:
        refuse(FINDING_CATALOG_FILE_MISSING, f"{meta_path} is unreadable: {exc}")
    except ValueError as exc:
        refuse(FINDING_CATALOG_FIELD_INVALID, f"{CATALOG_FILENAME} is not strict JSON: {exc}")
    refuse_when(not isinstance(meta, dict), FINDING_CATALOG_FIELD_INVALID, "CATALOG.json must be an object")
    assert isinstance(meta, dict)
    refuse_first(
        (
            (meta.get("format") != CATALOG_FORMAT, FINDING_CATALOG_FIELD_INVALID, "format"),
            (meta.get("factory") != FACTORY, FINDING_CATALOG_FIELD_INVALID, "factory"),
            (meta.get("mill_prefix") != FAMILY_PREFIX, FINDING_CATALOG_FIELD_INVALID, "mill_prefix"),
            (meta.get("record_kind") != RECORD_KIND, FINDING_CATALOG_FIELD_INVALID, "record_kind"),
            (
                meta.get("quota_per_round") != QUOTA_PER_ROUND,
                FINDING_CATALOG_FIELD_INVALID,
                "quota_per_round",
            ),
        )
    )
    catalog_id = _require_text(meta.get("catalog_id"), "catalog_id", FINDING_CATALOG_FIELD_INVALID)
    plant_count = _require_int(meta.get("plant_count"), "plant_count", FINDING_CATALOG_FIELD_INVALID, 1)
    full_raw = meta.get("full_plant_count", plant_count)
    full_plant_count = _require_int(full_raw, "full_plant_count", FINDING_CATALOG_FIELD_INVALID, 1)
    refuse_when(
        plant_count > full_plant_count,
        FINDING_CATALOG_FIELD_INVALID,
        f"plant_count {plant_count} exceeds full_plant_count {full_plant_count}",
    )
    slice_name = meta.get("slice")
    if full_plant_count != plant_count:
        refuse_when(
            slice_name != "representative",
            FINDING_CATALOG_FIELD_INVALID,
            "a partial plants.jsonl must set slice=representative",
        )
    elif plant_count == full_plant_count and slice_name is not None:
        refuse_when(
            slice_name != CATALOG_SLICE,
            FINDING_CATALOG_FIELD_INVALID,
            f"a full identity catalog must set slice={CATALOG_SLICE}",
        )
    plants_sha256 = _require_text(meta.get("plants_sha256"), "plants_sha256", FINDING_CATALOG_FIELD_INVALID)
    mill_rows = meta.get("mills")
    refuse_when(not isinstance(mill_rows, list), FINDING_CATALOG_FIELD_MISSING, "mills")
    assert isinstance(mill_rows, list)
    mills = tuple(_mill_from_row(row, f"mills[{index}]") for index, row in enumerate(mill_rows))
    try:
        plants_bytes = plants_path.read_bytes()
    except OSError as exc:
        refuse(FINDING_CATALOG_FILE_MISSING, f"{plants_path} is unreadable: {exc}")
    digest = sha256_bytes(plants_bytes)
    refuse_when(
        digest != plants_sha256,
        FINDING_CATALOG_SHA256_MISMATCH,
        f"{PLANTS_FILENAME} digest {digest} != catalog pin {plants_sha256}",
    )
    refuse_when(FACTORY not in _registry_factory_ids(), FINDING_FACTORY_NOT_REGISTERED, FACTORY)
    rows = _read_jsonl(plants_path)
    refuse_when(
        len(rows) != plant_count,
        FINDING_CATALOG_FIELD_INVALID,
        f"plant_count is {plant_count}, file has {len(rows)}",
    )
    plants = tuple(_plant_from_row(row, f"{PLANTS_FILENAME}:{index}") for index, row in enumerate(rows, 1))
    seen: set[str] = set()
    for plant in plants:
        refuse_when(plant.plant_id in seen, FINDING_PLANT_DUPLICATE, f"duplicate {plant.plant_id}")
        seen.add(plant.plant_id)
    by_mill: dict[str, int] = {}
    for plant in plants:
        by_mill[plant.mill_id] = by_mill.get(plant.mill_id, 0) + 1
    refuse_when(
        {mill.mill_id for mill in mills} != set(by_mill),
        FINDING_CATALOG_FIELD_INVALID,
        "catalog mills do not match plant mill_id values",
    )
    refuse_when(
        sum(mill.plant_count for mill in mills) != full_plant_count,
        FINDING_CATALOG_FIELD_INVALID,
        "mill plant_count values must sum to full_plant_count",
    )
    for mill in mills:
        committed = by_mill[mill.mill_id]
        refuse_when(
            committed < 1 or committed > mill.plant_count,
            FINDING_CATALOG_FIELD_INVALID,
            f"{mill.mill_id} committed {committed} outside 1..{mill.plant_count}",
        )
    if plant_count == full_plant_count and meta.get("slice") == CATALOG_SLICE:
        for mill in mills:
            refuse_when(
                by_mill[mill.mill_id] != mill.plant_count,
                FINDING_CATALOG_FIELD_INVALID,
                f"{mill.mill_id} identity catalog missing plants",
            )
    return Catalog(
        catalog_id=catalog_id,
        directory=catalog_dir,
        factory=FACTORY,
        plants_sha256=digest,
        plants=plants,
        mills=mills,
        meta=meta,
    )


def catalog_check(directory: Path | None = None, *, root: Path | None = None) -> Catalog:
    """Load the committed catalog, refuse vendored mill paths, re-assert pins."""

    refuse_vendor_paths(root)
    catalog = load_catalog(directory, root=root)
    source = catalog.meta.get("source")
    refuse_when(not isinstance(source, dict), FINDING_CATALOG_FIELD_MISSING, "source")
    assert isinstance(source, dict)
    refuse_first(
        (
            (source.get("ref") != LEGACY_REF, FINDING_CATALOG_FIELD_INVALID, "source.ref"),
            (source.get("commit") != LEGACY_COMMIT, FINDING_CATALOG_FIELD_INVALID, "source.commit"),
            (source.get("method") != EXTRACT_METHOD, FINDING_CATALOG_FIELD_INVALID, "source.method"),
        )
    )
    expected = [item[0] for item in SOURCE_MILLS]
    refuse_when(
        [mill.mill_id for mill in catalog.mills] != expected,
        FINDING_CATALOG_FIELD_INVALID,
        "source mill order drifted from SOURCE_MILLS",
    )
    if catalog.catalog_id == DEFAULT_CATALOG_ID:
        representative = sum(
            1 for plant in catalog.plants if plant.row_kind == ROW_KIND_REPRESENTATIVE
        )
        refuse_when(
            representative != REPRESENTATIVE_BODY_COUNT,
            FINDING_CATALOG_FIELD_INVALID,
            "representative body count",
        )
        refuse_first(
            (
                (catalog.meta.get("slice") != CATALOG_SLICE, FINDING_CATALOG_FIELD_INVALID, "slice"),
                (
                    catalog.meta.get("full_plant_count") != FULL_PLANT_COUNT,
                    FINDING_CATALOG_FIELD_INVALID,
                    "full_plant_count",
                ),
                (
                    catalog.meta.get("full_pair_count") != FULL_PAIR_COUNT,
                    FINDING_CATALOG_FIELD_INVALID,
                    "full_pair_count",
                ),
                (
                    catalog.meta.get("full_row_count") != FULL_ROW_COUNT,
                    FINDING_CATALOG_FIELD_INVALID,
                    "full_row_count",
                ),
                (
                    tuple((mill.mill_id, mill.plant_count) for mill in catalog.mills)
                    != FULL_MILL_COUNTS,
                    FINDING_CATALOG_FIELD_INVALID,
                    "mill plant_count inventory",
                ),
            )
        )
    return catalog


def document_from_plants(
    plants: tuple[dict[str, Any], ...],
    mills: tuple[Mill, ...],
    *,
    catalog_id: str = DEFAULT_CATALOG_ID,
    plants_sha256: str,
    full_plant_count: int | None = None,
    full_pair_count: int | None = None,
    full_row_count: int | None = None,
    slice_name: str | None = None,
) -> dict[str, Any]:
    """Build the CATALOG.json document for a committed or fixture catalog."""

    inventory = full_plant_count if full_plant_count is not None else len(plants)
    payload: dict[str, Any] = {
        "catalog_id": catalog_id,
        "factory": FACTORY,
        "format": CATALOG_FORMAT,
        "mill_prefix": FAMILY_PREFIX,
        "mills": [
            {
                "base_round": mill.base_round,
                "mill_id": mill.mill_id,
                "plant_count": mill.plant_count,
                "shape": mill.shape,
                "source": mill.source,
            }
            for mill in mills
        ],
        "plant_count": len(plants),
        "plants_sha256": plants_sha256,
        "quota_per_round": QUOTA_PER_ROUND,
        "record_kind": RECORD_KIND,
        "source": {
            "commit": LEGACY_COMMIT,
            "method": EXTRACT_METHOD,
            "ref": LEGACY_REF,
            "scripts": [mill.source for mill in mills],
        },
    }
    if inventory != len(plants) or slice_name is not None:
        payload["full_plant_count"] = inventory
        payload["slice"] = slice_name or CATALOG_SLICE
    if full_pair_count is not None:
        payload["full_pair_count"] = full_pair_count
    if full_row_count is not None:
        payload["full_row_count"] = full_row_count
    return payload


bind_import_twin(__name__)
