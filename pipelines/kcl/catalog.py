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
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypeGuard

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


def _is_literal_scalar(node: ast.AST) -> bool:
    if not isinstance(node, ast.Constant) or isinstance(node.value, bool):
        return False
    return isinstance(node.value, (str, int))


def _try_const_kwargs(node: ast.Call) -> dict[str, str | int] | None:
    if node.args or any(kw.arg is None for kw in node.keywords):
        return None
    payload: dict[str, str | int] = {}
    for kw in node.keywords:
        assert kw.arg is not None
        if not _is_literal_scalar(kw.value):
            return None
        payload[kw.arg] = kw.value.value
    return payload


def _try_const_args(node: ast.Call, arity: int) -> list[str | int] | None:
    if node.keywords or len(node.args) != arity:
        return None
    values: list[str | int] = []
    for arg in node.args:
        if not _is_literal_scalar(arg):
            return None
        values.append(arg.value)
    return values


def _try_const_dict(node: ast.Dict) -> dict[str, str | int] | None:
    payload: dict[str, str | int] = {}
    for key_node, val_node in zip(node.keys, node.values):
        if not isinstance(key_node, ast.Constant) or not isinstance(key_node.value, str):
            return None
        if not _is_literal_scalar(val_node):
            return None
        payload[key_node.value] = val_node.value
    return payload


def _is_pairs_name(target: ast.AST) -> bool:
    return isinstance(target, ast.Name) and target.id == "PAIRS"


def _pairs_value(node: ast.AST) -> ast.AST | None:
    """Return the value of a module-level ``PAIRS = ...`` / ``PAIRS: T = ...``."""

    if isinstance(node, ast.AnnAssign):
        return node.value if _is_pairs_name(node.target) else None
    if isinstance(node, ast.Assign) and any(_is_pairs_name(target) for target in node.targets):
        return node.value
    return None


def _module_pairs_lists(tree: ast.AST) -> tuple[ast.List, ...]:
    values = (_pairs_value(node) for node in getattr(tree, "body", ()))
    return tuple(value for value in values if isinstance(value, ast.List))


def row_to_pair(row: Mapping[str, Any]) -> dict[str, str]:
    """Expand an ``mk()`` row into the leftover ``pair()`` contract."""

    idx = int(row["idx"])
    text = {key: str(row[key]) for key in ROW_KEYS if key != "idx"}
    return {**_row_pair_chart(idx, text), **_row_pair_story(idx, text)}


def _row_pair_chart(idx: int, text: Mapping[str, str]) -> dict[str, str]:
    """The chart half of an expanded row: identity, values, and template."""

    plant, field, hide_key = text["plant"], text["field"], text["hide_key"]
    hide_old_line = f"{hide_key}: {text['hide_old']}\n"
    val_key = field.split(".")[-1]
    return {
        "plant": plant,
        "app": plant.replace("-prod", "-api"),
        "chart": f"{1 + (idx % 8)}.{1 + (idx % 9)}.{idx % 10}",
        "slug": text["slug"],
        "field": field,
        "fail_val": text["fail"],
        "fix_val": text["fix"],
        "hide_path": hide_key,
        "hide_old": hide_old_line,
        "hide_new": f"{hide_key}: {text['hide_new']}\n",
        "values_fail": f"{val_key}: {text['fail']}\n{hide_old_line}",
        "values_fix": f"{val_key}: {text['fix']}\n{hide_old_line}",
        "tpl": f"  {val_key}: {{{{ .Values.{val_key} }}}}\n",
    }


def _row_pair_story(idx: int, text: Mapping[str, str]) -> dict[str, str]:
    """The narrative half of an expanded row: logs, seeds, CI, and handoff."""

    field, fail, fix = text["field"], text["fail"], text["fix"]
    hide_key, hide_new, crash = text["hide_key"], text["hide_new"], text["crash"]
    return {
        "log": f"{crash} leftover {field} {fail} CrashLoop",
        "live_ok": f"{field}={fix}",
        "hide_name": f"{hide_key} {hide_new}",
        "new_vs": text["new_vs"],
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


def _refuse_bad_identity(plant: str, slug: str, where: str) -> None:
    refuse_when(not plant or not slug, FINDING_PLANT_FIELD_INVALID, f"{where} plant/slug")
    for token in BANNED_ID_TOKENS:
        refuse_when(token in slug, FINDING_BANNED, f"{where}: banned slug token {token!r}")
    refuse_when(not SLUG_RE.fullmatch(slug), FINDING_PLANT_FIELD_INVALID, f"{where}.slug")


def _extracted_row(
    shape: str, payload: dict[str, Any], origin: Mapping[str, Any]
) -> dict[str, Any]:
    """One checked plant row; ``origin`` carries ``mill_id``/``source``/``base_round``."""

    mill_id = origin["mill_id"]
    slug = payload["slug"]
    return {
        "base_round": origin["base_round"],
        "mill_id": mill_id,
        "payload": payload,
        "plant": payload["plant"],
        "plant_id": f"{mill_id}:{slug}",
        "shape": shape,
        "slug": slug,
        "source": origin["source"],
    }


def _pair_row(raw: Mapping[str, Any], origin: Mapping[str, Any], index: int) -> dict[str, Any]:
    where = f"{origin['source']}[{index}]"
    missing = [key for key in PAIR_KEYS if key not in raw]
    refuse_when(bool(missing), FINDING_PLANT_FIELD_MISSING, f"{where} missing {missing}")
    payload = {key: raw[key] for key in PAIR_KEYS}
    for key in PAIR_KEYS:
        refuse_when(
            not isinstance(payload[key], str),
            FINDING_PLANT_FIELD_INVALID,
            f"{where}.{key} must be a string",
        )
        payload[key] = str(payload[key])
    _refuse_bad_identity(payload["plant"], payload["slug"], where)
    return _extracted_row(SHAPE_PAIR, payload, origin)


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _refuse_row_value_types(payload: Mapping[str, Any], where: str) -> None:
    for key in ROW_KEYS:
        if key == "idx":
            refuse_when(
                not _is_int(payload[key]),
                FINDING_PLANT_FIELD_INVALID,
                f"{where}.idx must be an int",
            )
            continue
        refuse_when(
            not isinstance(payload[key], str),
            FINDING_PLANT_FIELD_INVALID,
            f"{where}.{key} must be a string",
        )


def _row_row(values: list[str | int], origin: Mapping[str, Any], index: int) -> dict[str, Any]:
    where = f"{origin['source']}[{index}]"
    refuse_when(len(values) != len(ROW_KEYS), FINDING_SOURCE_NOT_PARSEABLE, f"{where} arity")
    payload = {key: values[offset] for offset, key in enumerate(ROW_KEYS)}
    refuse_when(
        payload["idx"] != index,
        FINDING_SOURCE_NOT_PARSEABLE,
        f"{where} idx {payload['idx']!r} != {index}",
    )
    _refuse_row_value_types(payload, where)
    _refuse_bad_identity(str(payload["plant"]), str(payload["slug"]), where)
    return _extracted_row(SHAPE_ROW, payload, origin)


def _parse_source(source: str, path: str) -> ast.AST:
    try:
        return ast.parse(source, filename=path)
    except SyntaxError as exc:
        refuse(FINDING_SOURCE_NOT_PARSEABLE, f"{path} does not parse: {exc}")


def _is_call_to(node: ast.AST, name: str) -> TypeGuard[ast.Call]:
    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
        return False
    return node.func.id == name


def _calls_to(tree: ast.AST, name: str) -> Iterator[ast.Call]:
    return (node for node in ast.walk(tree) if _is_call_to(node, name))


def _pair_payloads(tree: ast.AST) -> Iterator[dict[str, str | int]]:
    """Literal ``pair(**kwargs)`` calls, then literal dicts in module ``PAIRS`` lists."""

    for node in _calls_to(tree, "pair"):
        payload = _try_const_kwargs(node)
        if payload is not None:
            yield payload
    for pair_list in _module_pairs_lists(tree):
        for elt in pair_list.elts:
            payload = _try_const_dict(elt) if isinstance(elt, ast.Dict) else None
            if payload is not None:
                yield payload


def _extract_pair_rows(tree: ast.AST, origin: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for payload in _pair_payloads(tree):
        rows.append(_pair_row(payload, origin, len(rows)))
    return rows


def _extract_mk_rows(tree: ast.AST, origin: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for node in _calls_to(tree, "mk"):
        values = _try_const_args(node, len(ROW_KEYS))
        if values is not None:
            rows.append(_row_row(values, origin, len(rows)))
    return rows


def _refuse_duplicate_plant_ids(plant_ids: Iterable[str]) -> None:
    seen: set[str] = set()
    for plant_id in plant_ids:
        refuse_when(plant_id in seen, FINDING_PLANT_DUPLICATE, f"duplicate {plant_id}")
        seen.add(plant_id)


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
    tree = _parse_source(source, path)
    origin = {"mill_id": mill_id, "source": path, "base_round": base_round}
    refuse_when(
        shape not in (SHAPE_PAIR, SHAPE_ROW),
        FINDING_SOURCE_NOT_PARSEABLE,
        f"{path}: unknown extract shape {shape!r}",
    )
    if shape == SHAPE_PAIR:
        rows = _extract_pair_rows(tree, origin)
    else:
        rows = _extract_mk_rows(tree, origin)
    refuse_when(not rows, FINDING_SOURCE_NOT_PARSEABLE, f"{path} has no extractable plants")
    _refuse_duplicate_plant_ids(row["plant_id"] for row in rows)
    return tuple(rows)


def _require_text(value: Any, where: str, code: str) -> str:
    refuse_when(not isinstance(value, str) or not value, code, f"{where} must be a non-empty string")
    assert isinstance(value, str)
    return value


def _require_int(value: Any, where: str, code: str, minimum: int = 0) -> int:
    refuse_when(
        not _is_int(value) or value < minimum,
        code,
        f"{where} must be an int >= {minimum}",
    )
    assert isinstance(value, int)
    return value


def _plant_fields(row: dict[str, Any], where: str) -> dict[str, Any]:
    """The checked identity and origin fields every committed plant row carries."""

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
    return {
        "plant_id": plant_id,
        "mill_id": mill_id,
        "source": source,
        "base_round": base_round,
        "shape": shape,
        "slug": slug,
    }


def _plant_row_kind(row_kind_raw: Any, where: str) -> str:
    if row_kind_raw is None:
        return ROW_KIND_REPRESENTATIVE
    row_kind = _require_text(row_kind_raw, f"{where}.row_kind", FINDING_PLANT_FIELD_INVALID)
    refuse_when(
        row_kind not in {ROW_KIND_REPRESENTATIVE, ROW_KIND_IDENTITY},
        FINDING_PLANT_FIELD_INVALID,
        f"{where}.row_kind",
    )
    return row_kind


def _identity_plant(row: dict[str, Any], fields: Mapping[str, Any], where: str) -> Plant:
    refuse_when(
        row.get("payload") is not None,
        FINDING_PLANT_FIELD_INVALID,
        f"{where}.payload must be omitted for identity rows",
    )
    plant_name = _require_text(row.get("plant"), f"{where}.plant", FINDING_PLANT_FIELD_MISSING)
    return Plant(**fields, plant=plant_name, payload={}, row_kind=ROW_KIND_IDENTITY)


def _body_row(payload_raw: dict[str, Any], fields: Mapping[str, Any], where: str) -> dict[str, Any]:
    """Re-check a representative body through the same extract contract as the source."""

    shape = fields["shape"]
    if shape == SHAPE_PAIR:
        return _pair_row(payload_raw, fields, 0)
    refuse_when(
        shape != SHAPE_ROW, FINDING_PLANT_FIELD_INVALID, f"{where}.shape must be pair or row"
    )
    values = [payload_raw.get(key) for key in ROW_KEYS]
    return _row_row(values, fields, int(payload_raw.get("idx", 0)))  # type: ignore[arg-type]


def _representative_plant(payload_raw: Any, fields: Mapping[str, Any], where: str) -> Plant:
    refuse_when(not isinstance(payload_raw, dict), FINDING_PLANT_FIELD_INVALID, f"{where}.payload")
    assert isinstance(payload_raw, dict)
    built = _body_row(payload_raw, fields, where)
    return Plant(
        plant_id=built["plant_id"],
        mill_id=fields["mill_id"],
        source=built["source"],
        base_round=built["base_round"],
        shape=fields["shape"],
        slug=fields["slug"],
        plant=built["plant"],
        payload=built["payload"],
        row_kind=ROW_KIND_REPRESENTATIVE,
    )


def _plant_from_row(row: Any, where: str) -> Plant:
    refuse_when(not isinstance(row, dict), FINDING_PLANT_FIELD_INVALID, f"{where} must be an object")
    assert isinstance(row, dict)
    fields = _plant_fields(row, where)
    row_kind = _plant_row_kind(row.get("row_kind"), where)
    if row_kind == ROW_KIND_IDENTITY:
        return _identity_plant(row, fields, where)
    return _representative_plant(row.get("payload"), fields, where)


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


def _read_catalog_meta(meta_path: Path) -> dict[str, Any]:
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
    return meta


def _refuse_slice(slice_name: Any, plant_count: int, full_plant_count: int) -> None:
    if full_plant_count != plant_count:
        refuse_when(
            slice_name != "representative",
            FINDING_CATALOG_FIELD_INVALID,
            "a partial plants.jsonl must set slice=representative",
        )
    elif slice_name is not None:
        refuse_when(
            slice_name != CATALOG_SLICE,
            FINDING_CATALOG_FIELD_INVALID,
            f"a full identity catalog must set slice={CATALOG_SLICE}",
        )


def _catalog_counts(meta: Mapping[str, Any]) -> tuple[str, int, int]:
    """Return ``(catalog_id, plant_count, full_plant_count)`` once the slice agrees."""

    catalog_id = _require_text(meta.get("catalog_id"), "catalog_id", FINDING_CATALOG_FIELD_INVALID)
    plant_count = _require_int(meta.get("plant_count"), "plant_count", FINDING_CATALOG_FIELD_INVALID, 1)
    full_raw = meta.get("full_plant_count", plant_count)
    full_plant_count = _require_int(full_raw, "full_plant_count", FINDING_CATALOG_FIELD_INVALID, 1)
    refuse_when(
        plant_count > full_plant_count,
        FINDING_CATALOG_FIELD_INVALID,
        f"plant_count {plant_count} exceeds full_plant_count {full_plant_count}",
    )
    _refuse_slice(meta.get("slice"), plant_count, full_plant_count)
    return catalog_id, plant_count, full_plant_count


def _catalog_mills(meta: Mapping[str, Any]) -> tuple[Mill, ...]:
    mill_rows = meta.get("mills")
    refuse_when(not isinstance(mill_rows, list), FINDING_CATALOG_FIELD_MISSING, "mills")
    assert isinstance(mill_rows, list)
    return tuple(_mill_from_row(row, f"mills[{index}]") for index, row in enumerate(mill_rows))


def _pinned_digest(plants_path: Path, plants_sha256: str) -> str:
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
    return digest


def _catalog_plants(plants_path: Path, plant_count: int) -> tuple[Plant, ...]:
    rows = _read_jsonl(plants_path)
    refuse_when(
        len(rows) != plant_count,
        FINDING_CATALOG_FIELD_INVALID,
        f"plant_count is {plant_count}, file has {len(rows)}",
    )
    plants = tuple(_plant_from_row(row, f"{PLANTS_FILENAME}:{index}") for index, row in enumerate(rows, 1))
    _refuse_duplicate_plant_ids(plant.plant_id for plant in plants)
    return plants


def _plants_per_mill(plants: tuple[Plant, ...]) -> dict[str, int]:
    by_mill: dict[str, int] = {}
    for plant in plants:
        by_mill[plant.mill_id] = by_mill.get(plant.mill_id, 0) + 1
    return by_mill


def _refuse_mill_inventory(
    mills: tuple[Mill, ...],
    plants: tuple[Plant, ...],
    full_plant_count: int,
    identity_catalog: bool,
) -> None:
    by_mill = _plants_per_mill(plants)
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
    if identity_catalog:
        for mill in mills:
            refuse_when(
                by_mill[mill.mill_id] != mill.plant_count,
                FINDING_CATALOG_FIELD_INVALID,
                f"{mill.mill_id} identity catalog missing plants",
            )


def load_catalog(directory: Path | None = None, *, root: Path | None = None) -> Catalog:
    """Load a catalog directory and refuse unless every pin holds."""

    catalog_dir = Path(default_catalog_dir(root) if directory is None else directory)
    plants_path = catalog_dir / PLANTS_FILENAME
    meta = _read_catalog_meta(catalog_dir / CATALOG_FILENAME)
    catalog_id, plant_count, full_plant_count = _catalog_counts(meta)
    plants_sha256 = _require_text(meta.get("plants_sha256"), "plants_sha256", FINDING_CATALOG_FIELD_INVALID)
    mills = _catalog_mills(meta)
    digest = _pinned_digest(plants_path, plants_sha256)
    refuse_when(FACTORY not in _registry_factory_ids(), FINDING_FACTORY_NOT_REGISTERED, FACTORY)
    plants = _catalog_plants(plants_path, plant_count)
    identity_catalog = plant_count == full_plant_count and meta.get("slice") == CATALOG_SLICE
    _refuse_mill_inventory(mills, plants, full_plant_count, identity_catalog)
    return Catalog(
        catalog_id=catalog_id,
        directory=catalog_dir,
        factory=FACTORY,
        plants_sha256=digest,
        plants=plants,
        mills=mills,
        meta=meta,
    )


def _refuse_source_pins(meta: Mapping[str, Any]) -> None:
    source = meta.get("source")
    refuse_when(not isinstance(source, dict), FINDING_CATALOG_FIELD_MISSING, "source")
    assert isinstance(source, dict)
    refuse_first(
        (
            (source.get("ref") != LEGACY_REF, FINDING_CATALOG_FIELD_INVALID, "source.ref"),
            (source.get("commit") != LEGACY_COMMIT, FINDING_CATALOG_FIELD_INVALID, "source.commit"),
            (source.get("method") != EXTRACT_METHOD, FINDING_CATALOG_FIELD_INVALID, "source.method"),
        )
    )


def _refuse_default_inventory(catalog: Catalog) -> None:
    """The committed default catalog must keep its exact slice and full inventory."""

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


def catalog_check(directory: Path | None = None, *, root: Path | None = None) -> Catalog:
    """Load the committed catalog, refuse vendored mill paths, re-assert pins."""

    refuse_vendor_paths(root)
    catalog = load_catalog(directory, root=root)
    _refuse_source_pins(catalog.meta)
    expected = [item[0] for item in SOURCE_MILLS]
    refuse_when(
        [mill.mill_id for mill in catalog.mills] != expected,
        FINDING_CATALOG_FIELD_INVALID,
        "source mill order drifted from SOURCE_MILLS",
    )
    if catalog.catalog_id == DEFAULT_CATALOG_ID:
        _refuse_default_inventory(catalog)
    return catalog


def _mill_documents(mills: tuple[Mill, ...]) -> list[dict[str, Any]]:
    return [
        {
            "base_round": mill.base_round,
            "mill_id": mill.mill_id,
            "plant_count": mill.plant_count,
            "shape": mill.shape,
            "source": mill.source,
        }
        for mill in mills
    ]


def _source_document(mills: tuple[Mill, ...]) -> dict[str, Any]:
    return {
        "commit": LEGACY_COMMIT,
        "method": EXTRACT_METHOD,
        "ref": LEGACY_REF,
        "scripts": [mill.source for mill in mills],
    }


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
        "mills": _mill_documents(mills),
        "plant_count": len(plants),
        "plants_sha256": plants_sha256,
        "quota_per_round": QUOTA_PER_ROUND,
        "record_kind": RECORD_KIND,
        "source": _source_document(mills),
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
