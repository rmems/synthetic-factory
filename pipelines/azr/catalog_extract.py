#!/usr/bin/env python3
"""AST-extract AZR catalog identity from a mill or plant source.

Evaluates only literals and constructor keyword arguments. Does not import,
compile, or exec mill publishers, so ``azr-mill*.py`` stay off this branch.
"""

from __future__ import annotations

import ast
import hashlib
import json
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .catalog_ast import (
    UNSET,
    add_identities,
    assignment_of,
    call_name,
    extract_joined_path_assignment,
    extract_spec_paths,
    function_named,
    identity_kwargs,
    literal_value,
    normalize_experiments_path,
    tip_slug_asserts,
)
from .vocabulary import (
    CATALOG_FILENAME,
    CATALOG_SCHEMA_ID,
    FACTORY,
    GENERATOR,
    KIND_PAIRS,
    KIND_PLANTS,
    LEGACY_REF,
    PAIR_IDENTITY_KEYS,
    PAIR_ROW_KEYS,
    PAIRS_FILENAME,
    PRESERVE_COMMIT,
    SHAPE_IDOR_BFLA,
    SHAPE_IDOR_BFLA_COMPOSE,
    SHAPE_LITERAL,
    SHAPE_NEW_PLUS_KEEP,
    SHAPE_PLANTS_ZIP,
    SHAPE_SLICE,
    SLICE_ID,
    SLICE_MILL_ID,
)

_ROUND_RE = re.compile(r"r(\d+)")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def mill_id_for_path(path: str) -> str:
    return Path(path).stem


def catalog_first_from_name(path: str) -> int | None:
    match = _ROUND_RE.search(Path(path).stem)
    return int(match.group(1)) if match else None


def _module_constants(tree: ast.AST) -> dict[str, Any]:
    env: dict[str, Any] = {}
    for node in getattr(tree, "body", ()):
        name, value = assignment_of(node)
        if name is None or value is None:
            continue
        resolved = literal_value(value, env)
        if resolved is not UNSET:
            env[name] = resolved
    return env


def _list_assignment(tree: ast.AST, name: str) -> ast.List | None:
    for node in getattr(tree, "body", ()):
        assigned, value = assignment_of(node)
        if assigned == name and isinstance(value, ast.List):
            return value
    return None


def _identity_list(elts: list[ast.AST]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for elt in elts:
        kwargs = identity_kwargs(elt)
        if kwargs is None or "slug" not in kwargs:
            raise ValueError("catalog row is not a literal slug identity")
        rows.append(kwargs)
    return rows


def _pair_identity(pair: Any) -> dict[str, Any]:
    if not isinstance(pair, (tuple, list)) or len(pair) != 2:
        return {
            "success_slug": None,
            "fail_slug": None,
            "success_plant": None,
            "fail_plant": None,
            "fail_handoff": False,
        }
    success, fail = pair
    if not isinstance(success, dict) or not isinstance(fail, dict):
        return {
            "success_slug": None,
            "fail_slug": None,
            "success_plant": None,
            "fail_plant": None,
            "fail_handoff": False,
        }
    return {
        "success_slug": success.get("slug"),
        "fail_slug": fail.get("slug"),
        "success_plant": success.get("plant"),
        "fail_plant": fail.get("plant"),
        "fail_handoff": bool(fail.get("handoff")),
    }


def _row_identity(success: Mapping[str, Any], fail: Mapping[str, Any] | None) -> dict[str, Any]:
    return {
        "success_slug": success.get("slug"),
        "fail_slug": None if fail is None else fail.get("slug"),
        "success_plant": success.get("plant"),
        "fail_plant": None if fail is None else fail.get("plant"),
        "fail_handoff": bool(fail.get("handoff")) if fail is not None else True,
    }


def _rows_record(shape: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows or rows[0]["success_slug"] is None:
        raise ValueError(f"{shape} catalog has no success slugs")
    return {
        "shape": shape,
        "n_rows": len(rows),
        "first_slug": rows[0]["success_slug"],
        "last_slug": rows[-1]["success_slug"],
        "first_fail_slug": rows[0].get("fail_slug"),
        "last_fail_slug": rows[-1].get("fail_slug"),
        "pairs": rows,
    }


def _plant_filename(name: str) -> str:
    return normalize_experiments_path(name.replace("_", "-") + ".py")


def extra_plant_paths(tree: ast.AST) -> tuple[str, ...]:
    paths: list[str] = []
    for node in ast.walk(tree):
        if call_name(node) != "_load_extra" or not node.args:
            continue
        arg = node.args[0]
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            paths.append(_plant_filename(arg.value))
    return tuple(paths)


def extract_plant_catalog(
    source: str,
    *,
    path: str,
    blob_sha: str = "",
) -> dict[str, Any]:
    """Identity extract for an ``azr-plants-*.py`` catalog module."""

    payload = source.encode()
    tree = ast.parse(source, filename=path)
    idors: list[dict[str, Any]] = []
    bflas: list[dict[str, Any]] = []
    idor_list = _list_assignment(tree, "EXTRA_IDOR_ROWS")
    if idor_list is not None:
        idors = _identity_list(idor_list.elts)
    bfla_list = _list_assignment(tree, "BFLA_ROWS")
    if bfla_list is not None:
        bflas = _identity_list(bfla_list.elts)
    else:
        extra = function_named(tree, "extra_bflas")
        if extra is not None:
            bflas = add_identities(extra)
    if not idors:
        raise ValueError(f"{path} has no EXTRA_IDOR_ROWS catalog")
    if bflas and len(bflas) != len(idors):
        raise ValueError(f"{path}: idor {len(idors)} != bfla {len(bflas)}")
    return {
        "mill_id": mill_id_for_path(path),
        "path": path,
        "blob_sha": blob_sha,
        "sha256": sha256_bytes(payload),
        "kind": KIND_PLANTS,
        "catalog_first": catalog_first_from_name(path),
        "n_rows": len(idors),
        "first_slug": idors[0]["slug"],
        "last_slug": idors[-1]["slug"],
        "first_fail_slug": bflas[0]["slug"] if bflas else None,
        "last_fail_slug": bflas[-1]["slug"] if bflas else None,
        "idors": idors,
        "bflas": bflas,
    }


def _require_plant(
    plants: Mapping[str, str] | None,
    path: str,
    *,
    mill_path: str,
) -> dict[str, Any]:
    if not plants or path not in plants:
        raise ValueError(f"{mill_path} needs companion plant {path}")
    return extract_plant_catalog(plants[path], path=path)


def _literal_pairs(tree: ast.AST) -> dict[str, Any] | None:
    node = _list_assignment(tree, "PAIRS")
    if node is None or not node.elts:
        return None
    resolved = literal_value(node)
    if not isinstance(resolved, list) or not resolved:
        return None
    if not all(isinstance(row, (tuple, list)) and len(row) == 2 for row in resolved):
        return None
    rows = [_pair_identity(row) for row in resolved]
    if rows[0]["success_slug"] is None:
        return None
    return _rows_record(SHAPE_LITERAL, rows)


def _new_plus_keep(tree: ast.AST) -> dict[str, Any] | None:
    node = _list_assignment(tree, "NEW_PAIRS")
    if node is None or not node.elts:
        return None
    resolved = literal_value(node)
    if not isinstance(resolved, list) or not resolved:
        return None
    new_rows = [_pair_identity(row) for row in resolved]
    keep_slug = _jackson_keep_slug(tree)
    keep_fail = None
    constants = _module_constants(tree)
    keep = constants.get("KEEP_FROM_UNUSED")
    if isinstance(keep, set):
        others = [item for item in keep if item != keep_slug]
        if len(others) == 1:
            keep_fail = others[0]
    keep_row = {
        "success_slug": keep_slug or "jackson-isadmin-missing-jsonignore",
        "fail_slug": keep_fail,
        "success_plant": None,
        "fail_plant": None,
        "fail_handoff": False,
    }
    return _rows_record(SHAPE_NEW_PLUS_KEEP, [keep_row, *new_rows])


def _jackson_keep_slug(tree: ast.AST) -> str | None:
    func = function_named(tree, "jackson_opa_pair")
    if func is None:
        return None
    for node in ast.walk(func):
        if not isinstance(node, ast.Compare) or not node.comparators:
            continue
        if not isinstance(node.comparators[0], ast.Constant):
            continue
        if isinstance(node.comparators[0].value, str):
            return node.comparators[0].value
    return None


def _idor_bfla_own(tree: ast.AST) -> tuple[list[dict[str, Any]], list[dict[str, Any]]] | None:
    idor_list = _list_assignment(tree, "IDOR_ROWS")
    if idor_list is None or not idor_list.elts:
        return None
    idors = _identity_list(idor_list.elts)
    bflas: list[dict[str, Any]] = []
    func = function_named(tree, "_bflas")
    if func is not None:
        bflas = add_identities(func)
    if bflas and len(bflas) != len(idors):
        raise ValueError(f"IDOR_ROWS {len(idors)} != _bflas {len(bflas)}")
    return idors, bflas


def _compose_idor_bfla(
    tree: ast.AST,
    *,
    path: str,
    plants: Mapping[str, str] | None,
) -> dict[str, Any] | None:
    own = _idor_bfla_own(tree)
    extras = extra_plant_paths(tree)
    if own is None:
        return None
    idors, bflas = own
    extra_rows: list[dict[str, Any]] = []
    for plant_path in extras:
        plant = _require_plant(plants, plant_path, mill_path=path)
        extra_idors = plant["idors"]
        extra_bflas = plant["bflas"]
        extra_rows.extend(
            _row_identity(success, extra_bflas[index] if index < len(extra_bflas) else None)
            for index, success in enumerate(extra_idors)
        )
        idors = [*idors, *extra_idors]
        bflas = [*bflas, *extra_bflas]
    if extras:
        if len(idors) != len(bflas):
            raise ValueError(f"{path}: composed idor {len(idors)} != bfla {len(bflas)}")
        rows = [_row_identity(success, bflas[index]) for index, success in enumerate(idors)]
        record = _rows_record(SHAPE_IDOR_BFLA_COMPOSE, rows)
        record["n_own_rows"] = len(own[0])
        record["extra_plant_paths"] = list(extras)
        return record
    rows = [_row_identity(success, bflas[index] if index < len(bflas) else None) for index, success in enumerate(idors)]
    return _rows_record(SHAPE_IDOR_BFLA, rows)


def _companion_plant_path(source: str, tree: ast.AST) -> str | None:
    for item in extract_spec_paths(source):
        name = Path(item).name
        if name.startswith("azr-plants-"):
            return item
    return None


def _zip_from_plant(
    source: str,
    tree: ast.AST,
    *,
    path: str,
    plants: Mapping[str, str] | None,
) -> dict[str, Any] | None:
    plant_path = _companion_plant_path(source, tree)
    if plant_path is None:
        return None
    if plants is None or plant_path not in plants:
        tips = tip_slug_asserts(tree)
        if not tips.get("success") and "leftover3" not in Path(path).name:
            return None
        record = {
            "shape": SHAPE_PLANTS_ZIP,
            "n_rows": None,
            "first_slug": tips.get("success"),
            "last_slug": None,
            "first_fail_slug": tips.get("fail"),
            "last_fail_slug": None,
            "pairs": [],
            "companion_path": plant_path,
        }
        return record
    plant = extract_plant_catalog(plants[plant_path], path=plant_path)
    rows = [
        _row_identity(success, plant["bflas"][index] if index < len(plant["bflas"]) else None)
        for index, success in enumerate(plant["idors"])
    ]
    record = _rows_record(SHAPE_PLANTS_ZIP, rows)
    record["companion_path"] = plant_path
    tips = tip_slug_asserts(tree)
    if tips.get("success") and tips["success"] != record["first_slug"]:
        raise ValueError(f"{path} tip slug {tips['success']} != {record['first_slug']}")
    if tips.get("fail") and tips["fail"] != record["first_fail_slug"]:
        raise ValueError(f"{path} fail tip {tips['fail']} != {record['first_fail_slug']}")
    return record


def _slice_record(
    tree: ast.AST,
    *,
    path: str,
    plants: Mapping[str, str] | None,
) -> dict[str, Any] | None:
    for node in getattr(tree, "body", ()):
        name, value = assignment_of(node)
        if name != "PAIRS" or not isinstance(value, ast.Subscript):
            continue
        tips = tip_slug_asserts(tree)
        plant_path = "experiments/azr-plants-r1285.py"
        if plants and plant_path in plants:
            plant = extract_plant_catalog(plants[plant_path], path=plant_path)
            rows = [
                _row_identity(success, plant["bflas"][index] if index < len(plant["bflas"]) else None)
                for index, success in enumerate(plant["idors"])
            ]
            record = _rows_record(SHAPE_SLICE, rows)
        else:
            if not tips.get("success"):
                return None
            record = {
                "shape": SHAPE_SLICE,
                "n_rows": None,
                "first_slug": tips.get("success"),
                "last_slug": None,
                "first_fail_slug": tips.get("fail"),
                "last_fail_slug": None,
                "pairs": [],
            }
        record["companion_path"] = plant_path
        if tips.get("success") and record["first_slug"] not in {None, tips["success"]}:
            raise ValueError(f"{path} slice tip drifted")
        return record
    return None


def extract_mill_catalog(
    source: str,
    *,
    path: str,
    blob_sha: str = "",
    plants: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Structured catalog extract for one mill source file."""

    payload = source.encode()
    tree = ast.parse(source, filename=path)
    mill_id = mill_id_for_path(path)
    constants = _module_constants(tree)
    factory = constants.get("FACTORY", FACTORY)
    generator = constants.get("GEN", GENERATOR)
    catalog_first = constants.get("CATALOG_FIRST")
    if not isinstance(catalog_first, int):
        catalog_first = catalog_first_from_name(path)
    record = _extract_shape(source, tree, path=path, plants=plants)
    record.update(
        {
            "mill_id": mill_id,
            "path": path,
            "blob_sha": blob_sha,
            "sha256": sha256_bytes(payload),
            "kind": KIND_PAIRS,
            "catalog_first": catalog_first,
            "generator": generator,
            "factory": factory,
        }
    )
    return record


def _extract_shape(
    source: str,
    tree: ast.AST,
    *,
    path: str,
    plants: Mapping[str, str] | None,
) -> dict[str, Any]:
    rebuilt = _literal_pairs(tree)
    if rebuilt is not None:
        return rebuilt
    keep = _new_plus_keep(tree)
    if keep is not None:
        return keep
    composed = _compose_idor_bfla(tree, path=path, plants=plants)
    if composed is not None:
        return composed
    sliced = _slice_record(tree, path=path, plants=plants)
    if sliced is not None:
        return sliced
    zipped = _zip_from_plant(source, tree, path=path, plants=plants)
    if zipped is not None:
        return zipped
    raise ValueError(f"{path} has no extractable AZR catalog assignment")


def extract_companion_path(source: str) -> str | None:
    """``MILL`` / ``OUT`` joined-path constant, else first mill/plant spec path."""

    for name in ("MILL", "OUT"):
        found = extract_joined_path_assignment(source, name)
        if found is not None:
            return found
    for item in extract_spec_paths(source):
        stem = Path(item).name
        if stem.startswith(("azr-mill-", "azr-plants-")):
            return item
    return None


def mill_summary(record: Mapping[str, Any], *, include_pairs: bool) -> dict[str, Any]:
    """Catalog mill row: identity plus optional compact pair list."""

    summary = {
        "mill_id": record["mill_id"],
        "path": record["path"],
        "blob_sha": record["blob_sha"],
        "sha256": record["sha256"],
        "kind": record["kind"],
        "shape": record["shape"],
        "catalog_first": record["catalog_first"],
        "n_rows": record["n_rows"],
        "first_slug": record["first_slug"],
        "last_slug": record["last_slug"],
        "first_fail_slug": record.get("first_fail_slug"),
        "last_fail_slug": record.get("last_fail_slug"),
        "generator": record["generator"],
        "factory": record["factory"],
    }
    if record.get("companion_path"):
        summary["companion_path"] = record["companion_path"]
    if record.get("extra_plant_paths"):
        summary["extra_plant_paths"] = list(record["extra_plant_paths"])
    if record.get("n_own_rows") is not None:
        summary["n_own_rows"] = record["n_own_rows"]
    if include_pairs:
        summary["pairs"] = list(record.get("pairs") or ())
    return summary


def catalog_document(mills: list[dict[str, Any]]) -> dict[str, Any]:
    pair_rows = sum(int(mill["n_rows"] or 0) for mill in mills)
    return {
        "schema": CATALOG_SCHEMA_ID,
        "source_ref": LEGACY_REF,
        "preserve_commit": PRESERVE_COMMIT,
        "factory": FACTORY,
        "generator": GENERATOR,
        "slice": SLICE_ID,
        "n_mills": len(mills),
        "n_pair_rows": pair_rows,
        "mills": {mill["mill_id"]: mill for mill in mills},
    }


def dumps_catalog(document: Mapping[str, Any]) -> str:
    return json.dumps(document, ensure_ascii=True, indent=2, sort_keys=True) + "\n"


def catalog_json_path(package_dir: Path | None = None) -> Path:
    root = package_dir if package_dir is not None else Path(__file__).resolve().parent
    return root / CATALOG_FILENAME


def pairs_jsonl_path(package_dir: Path | None = None) -> Path:
    root = package_dir if package_dir is not None else Path(__file__).resolve().parent
    return root / PAIRS_FILENAME


def pair_identity(pair: Mapping[str, Any]) -> dict[str, Any]:
    """Compact identity shared by the r1181 header rows and ``pairs.jsonl``."""

    return {key: pair.get(key) for key in PAIR_IDENTITY_KEYS}


def pair_jsonl_row(
    mill_id: str, path: str, index: int, pair: Mapping[str, Any]
) -> dict[str, Any]:
    row = pair_identity(pair)
    row["i"] = index
    row["mill_id"] = mill_id
    row["path"] = path
    return row


def deferred_pair_rows(records: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """JSONL rows for every mill except the r1181 first slice, catalog order."""

    ordered = sorted(
        (record for record in records if not is_slice_mill(record["mill_id"])),
        key=lambda record: (record["catalog_first"], record["mill_id"]),
    )
    rows: list[dict[str, Any]] = []
    for record in ordered:
        for index, pair in enumerate(record["pairs"]):
            rows.append(pair_jsonl_row(record["mill_id"], record["path"], index, pair))
    return rows


def dumps_pairs_jsonl(rows: list[Mapping[str, Any]]) -> str:
    """One identity per line. No pretty indent. Trailing newline. No CR."""

    lines = [
        json.dumps(row, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
        for row in rows
    ]
    return "\n".join(lines) + "\n"


def load_pair_rows(path: Path | None = None) -> list[dict[str, Any]]:
    destination = path if path is not None else pairs_jsonl_path()
    try:
        text = destination.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"cannot load AZR pairs {destination}: {exc}") from exc
    if "\r" in text or not text.endswith("\n"):
        raise ValueError(f"{destination.name} must be LF-framed jsonl")
    rows: list[dict[str, Any]] = []
    for index, line in enumerate(text.splitlines(), start=1):
        if not line:
            raise ValueError(f"{destination.name}:{index} is empty")
        if line.startswith((" ", "\t")):
            raise ValueError(f"{destination.name}:{index} is not compact")
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{destination.name}:{index} is not JSON: {exc}") from exc
        if not isinstance(row, dict) or set(row) != set(PAIR_ROW_KEYS):
            raise ValueError(f"{destination.name}:{index} keys differ")
        rows.append(row)
    if not rows:
        raise ValueError(f"{destination.name} must contain deferred pair identities")
    return rows


def is_slice_mill(mill_id: str) -> bool:
    return mill_id == SLICE_MILL_ID


def write_catalog_document(document: Mapping[str, Any], path: Path | None = None) -> Path:
    destination = path if path is not None else catalog_json_path()
    destination.write_text(dumps_catalog(document), encoding="utf-8")
    return destination
