#!/usr/bin/env python3
"""AST-extract IAC catalog identity from a mill source.

Evaluates only literal catalog assignments and constructor keyword arguments.
Does not import, compile, or exec the mill publisher, so ``iac-mill*.py``
stay off this branch.
"""

from __future__ import annotations

import ast
import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .catalog_ast import (
    UNSET,
    assignment_names,
    assignment_of,
    call_kwargs,
    call_name,
    extract_joined_path_assignment,
    literal_value,
)
from .vocabulary import (
    CATALOG_FILENAME,
    CATALOG_SCHEMA_ID,
    FACTORY,
    GENERATOR,
    KIND_PAIRS,
    LEGACY_REF,
    PRESERVE_COMMIT,
    SLICE_ID,
)

SHAPE_LITERAL = "pairs-literal"
SHAPE_SUC_FAIL = "pairs-suc-fail"
SHAPE_KEEP_EXTEND = "pairs-keep-extend"
SHAPE_LEFTOVER = "leftover-pair"
SHAPE_K8S_FILE = "k8s-file"
SHAPE_K8S_CLI_SPEC = "k8s-cli-spec"


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def mill_id_for_path(path: str) -> str:
    return Path(path).stem


def catalog_first_from_name(path: str) -> int | None:
    stem = Path(path).stem
    marker = stem.rsplit("-r", 1)
    if len(marker) != 2 or not marker[1].isdigit():
        return None
    return int(marker[1])


def extract_mill_catalog(
    source: str,
    *,
    path: str,
    blob_sha: str = "",
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
    record = _extract_shape(tree, path=path)
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


def _extract_shape(tree: ast.AST, *, path: str) -> dict[str, Any]:
    rebuilt = _rebuild_literal_pairs(tree)
    if rebuilt is not None:
        return rebuilt
    leftover = _leftover_pair_list(tree)
    if leftover is not None:
        return leftover
    suc_fail = _suc_fail_list(tree)
    if suc_fail is not None:
        return suc_fail
    keep_extend = _keep_extend(tree)
    if keep_extend is not None:
        return keep_extend
    tables = _k8s_cli_tables(tree)
    if tables is not None:
        return tables
    raise ValueError(f"{path} has no extractable IAC catalog assignment")


def _rebuild_literal_pairs(tree: ast.AST) -> dict[str, Any] | None:
    """r609: literal ``PAIRS``, drop-by-slug listcomp, then ``_EXTRA*`` extends."""

    pairs: list[Any] | None = None
    extras: dict[str, list[Any]] = {}
    drop: set[Any] | None = None
    saw_filter = False
    for node in getattr(tree, "body", ()):
        names = assignment_names(node)
        _, value = assignment_of(node)
        if "PAIRS" in names and isinstance(value, ast.List):
            resolved = literal_value(value)
            if not isinstance(resolved, list):
                return None
            pairs = resolved
            continue
        if "PAIRS" in names and isinstance(value, ast.ListComp):
            if pairs is None or drop is None or not _is_drop_listcomp(value):
                return None
            pairs = [
                pair
                for pair in pairs
                if _pair_identity(pair)["success_slug"] not in drop
            ]
            saw_filter = True
            continue
        if "_DROP_SUCCESS" in names and value is not None:
            resolved = literal_value(value)
            if not isinstance(resolved, set):
                return None
            drop = resolved
            continue
        extra_name = next((name for name in names if name.startswith("_EXTRA")), None)
        if extra_name is not None and isinstance(value, ast.List):
            resolved = literal_value(value)
            if not isinstance(resolved, list):
                return None
            extras[extra_name] = resolved
            continue
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            call = node.value
            if not isinstance(call.func, ast.Attribute) or call.func.attr != "extend":
                continue
            if not isinstance(call.func.value, ast.Name) or call.func.value.id != "PAIRS":
                continue
            if pairs is None or len(call.args) != 1 or not isinstance(call.args[0], ast.Name):
                return None
            src_name = call.args[0].id
            if src_name not in extras:
                return None
            pairs.extend(extras[src_name])
    if pairs is None or not saw_filter or drop is None:
        return None
    rows = [_pair_identity(pair) for pair in pairs]
    if not rows or any(row["success_slug"] is None for row in rows):
        return None
    return _rows_record(SHAPE_LITERAL, rows)


def _is_drop_listcomp(node: ast.ListComp) -> bool:
    if len(node.generators) != 1:
        return False
    gen = node.generators[0]
    if not isinstance(node.elt, ast.Name) or not isinstance(gen.target, ast.Name):
        return False
    if node.elt.id != gen.target.id or not isinstance(gen.iter, ast.Name):
        return False
    if gen.iter.id != "PAIRS" or len(gen.ifs) != 1:
        return False
    test = gen.ifs[0]
    return isinstance(test, ast.Compare) and isinstance(test.ops[0], ast.NotIn)


def _suc_fail_list(tree: ast.AST) -> dict[str, Any] | None:
    for node in getattr(tree, "body", ()):
        name, value = assignment_of(node)
        if name != "PAIRS" or not isinstance(value, ast.List) or not value.elts:
            continue
        if not all(_is_suc_fail_tuple(elt) for elt in value.elts):
            continue
        rows = [_suc_fail_identity(elt) for elt in value.elts]
        if rows and rows[0]["success_slug"]:
            return _rows_record(SHAPE_SUC_FAIL, rows)
    return None


def _leftover_pair_list(tree: ast.AST) -> dict[str, Any] | None:
    for node in getattr(tree, "body", ()):
        name, value = assignment_of(node)
        if name != "PAIRS" or not isinstance(value, ast.List) or not value.elts:
            continue
        if not all(call_name(elt) == "leftover_pair" for elt in value.elts):
            continue
        rows = []
        for elt in value.elts:
            kwargs = call_kwargs(elt)
            if kwargs is None or "s" not in kwargs or "fs" not in kwargs:
                return None
            gem = kwargs.get("g")
            rows.append(
                {
                    "success_slug": kwargs["s"],
                    "fail_slug": kwargs["fs"],
                    "success_plant": f"{gem}-prod" if isinstance(gem, str) else None,
                    "fail_plant": f"{gem}-jobs" if isinstance(gem, str) else None,
                    "fail_handoff": True,
                }
            )
        return _rows_record(SHAPE_LEFTOVER, rows)
    return None


def _keep_extend(tree: ast.AST) -> dict[str, Any] | None:
    keep: set[str] | None = None
    extra_rows: list[dict[str, Any]] = []
    saw_empty_pairs = False
    for node in getattr(tree, "body", ()):
        name, value = assignment_of(node)
        if name == "KEEP" and value is not None:
            resolved = literal_value(value)
            if not isinstance(resolved, set) or not all(isinstance(item, str) for item in resolved):
                return None
            keep = {str(item) for item in resolved}
            continue
        if name == "PAIRS" and isinstance(value, ast.List) and not value.elts:
            saw_empty_pairs = True
            continue
        if name is not None and name.startswith("_EXTRA") and isinstance(value, ast.List):
            if not all(_is_suc_fail_tuple(elt) for elt in value.elts):
                return None
            extra_rows.extend(_suc_fail_identity(elt) for elt in value.elts)
    if keep is None or not saw_empty_pairs or not extra_rows:
        return None
    return {
        "shape": SHAPE_KEEP_EXTEND,
        "n_rows": len(keep) + len(extra_rows),
        "n_keep": len(keep),
        "n_extra": len(extra_rows),
        "keep_slugs": sorted(keep),
        "first_slug": extra_rows[0]["success_slug"],
        "last_slug": extra_rows[-1]["success_slug"],
        "pairs": extra_rows,
    }


def _k8s_cli_tables(tree: ast.AST) -> dict[str, Any] | None:
    k8s: list[Any] | None = None
    cli_spec: list[Any] | None = None
    cli_rows: list[dict[str, Any]] | None = None
    for node in getattr(tree, "body", ()):
        name, value = assignment_of(node)
        if name == "K8S" and value is not None:
            resolved = literal_value(value)
            if not isinstance(resolved, list) or not resolved:
                return None
            k8s = resolved
            continue
        if name == "CLI_SPEC" and value is not None:
            resolved = literal_value(value)
            if not isinstance(resolved, list) or not resolved:
                return None
            cli_spec = resolved
            continue
        if name == "CLI" and isinstance(value, ast.List) and value.elts:
            if all(call_name(elt) == "file_pair" for elt in value.elts):
                rows = []
                for elt in value.elts:
                    kwargs = call_kwargs(elt)
                    if kwargs is None or "s" not in kwargs:
                        return None
                    rows.append(
                        {
                            "success_slug": kwargs["s"],
                            "fail_slug": kwargs["s"].replace("-vs-old", "-old-leftover"),
                            "success_plant": (
                                f"{kwargs['g']}-prod" if isinstance(kwargs.get("g"), str) else None
                            ),
                            "fail_plant": (
                                f"{kwargs['g']}-jobs" if isinstance(kwargs.get("g"), str) else None
                            ),
                            "fail_handoff": True,
                        }
                    )
                cli_rows = rows
    if k8s is None:
        return None
    k8s_rows = [_k8s_identity(row) for row in k8s]
    if cli_spec is not None:
        cli_ident = [_cli_spec_identity(row) for row in cli_spec]
        rows = k8s_rows + cli_ident
        return _rows_record(SHAPE_K8S_CLI_SPEC, rows)
    if cli_rows is not None:
        rows = k8s_rows + cli_rows
        return _rows_record(SHAPE_K8S_FILE, rows)
    return None


def _is_suc_fail_tuple(node: ast.AST) -> bool:
    if not isinstance(node, ast.Tuple) or len(node.elts) != 2:
        return False
    return call_name(node.elts[0]) == "_suc" and call_name(node.elts[1]) == "_fail"


def _suc_fail_identity(node: ast.AST) -> dict[str, Any]:
    assert isinstance(node, ast.Tuple)
    success = call_kwargs(node.elts[0]) or {}
    fail = call_kwargs(node.elts[1]) or {}
    return {
        "success_slug": success.get("slug"),
        "fail_slug": fail.get("slug"),
        "success_plant": success.get("plant"),
        "fail_plant": fail.get("plant"),
        "fail_handoff": bool(fail.get("handoff")),
    }


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


def _k8s_identity(row: Any) -> dict[str, Any]:
    if not isinstance(row, (tuple, list)) or len(row) < 2:
        return {
            "success_slug": None,
            "fail_slug": None,
            "success_plant": None,
            "fail_plant": None,
            "fail_handoff": True,
        }
    slug = row[0]
    gem = row[1]
    return {
        "success_slug": slug,
        "fail_slug": slug.replace("-vs-old", "-old-leftover") if isinstance(slug, str) else None,
        "success_plant": f"{gem}-prod" if isinstance(gem, str) else None,
        "fail_plant": f"{gem}-jobs" if isinstance(gem, str) else None,
        "fail_handoff": True,
    }


def _cli_spec_identity(row: Any) -> dict[str, Any]:
    if not isinstance(row, dict):
        return {
            "success_slug": None,
            "fail_slug": None,
            "success_plant": None,
            "fail_plant": None,
            "fail_handoff": True,
        }
    slug = row.get("s")
    gem = row.get("g")
    return {
        "success_slug": slug,
        "fail_slug": slug.replace("-vs-old", "-old-leftover") if isinstance(slug, str) else None,
        "success_plant": f"{gem}-prod" if isinstance(gem, str) else None,
        "fail_plant": f"{gem}-jobs" if isinstance(gem, str) else None,
        "fail_handoff": True,
    }


def _rows_record(shape: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "shape": shape,
        "n_rows": len(rows),
        "first_slug": rows[0]["success_slug"],
        "last_slug": rows[-1]["success_slug"],
        "pairs": rows,
    }


def extract_companion_path(source: str) -> str | None:
    """``MILL`` or ``OUT`` joined-path constant from a loop / plant-gen script."""

    for name in ("MILL", "OUT"):
        found = extract_joined_path_assignment(source, name)
        if found is not None:
            return found
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
        "generator": record["generator"],
        "factory": record["factory"],
    }
    if record["shape"] == SHAPE_KEEP_EXTEND:
        summary["n_keep"] = record["n_keep"]
        summary["n_extra"] = record["n_extra"]
        summary["keep_slugs"] = list(record["keep_slugs"])
    if include_pairs:
        summary["pairs"] = list(record.get("pairs") or ())
    return summary


def catalog_document(
    mills: list[dict[str, Any]],
    *,
    archives: Mapping[str, Mapping[str, Any]] | None = None,
    plant_digests: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    pair_rows = sum(mill["n_rows"] for mill in mills)
    document: dict[str, Any] = {
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
    for key, block in (archives or {}).items():
        document[key] = dict(block)
    for key, digest in (plant_digests or {}).items():
        document[key] = digest
    return document


def dumps_catalog(document: Mapping[str, Any]) -> str:
    return json.dumps(document, ensure_ascii=True, indent=2, sort_keys=True) + "\n"


def catalog_json_path(package_dir: Path | None = None) -> Path:
    root = package_dir if package_dir is not None else Path(__file__).resolve().parent
    return root / CATALOG_FILENAME


def write_catalog_document(document: Mapping[str, Any], path: Path | None = None) -> Path:
    destination = path if path is not None else catalog_json_path()
    destination.write_text(dumps_catalog(document), encoding="utf-8")
    return destination
