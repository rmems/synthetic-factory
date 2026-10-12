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

    return _fold_module(tree, _LiteralPairsRebuild())


def _fold_module(tree: ast.AST, scan: Any) -> dict[str, Any] | None:
    """Feed each top-level statement to ``scan``; None as soon as one refuses the shape."""

    for node in getattr(tree, "body", ()):
        if not scan.apply(node):
            return None
    return scan.record()


class _LiteralPairsRebuild:
    """Replays r609's module-level ``PAIRS`` edits in source order."""

    def __init__(self) -> None:
        self.pairs: list[Any] | None = None
        self.extras: dict[str, list[Any]] = {}
        self.drop: set[Any] | None = None
        self.saw_filter = False

    def apply(self, node: ast.stmt) -> bool:
        names = assignment_names(node)
        _, value = assignment_of(node)
        if "PAIRS" in names and isinstance(value, ast.List):
            return self._assign_pairs(value)
        if "PAIRS" in names and isinstance(value, ast.ListComp):
            return self._filter_pairs(value)
        if "_DROP_SUCCESS" in names and value is not None:
            return self._assign_drop(value)
        return self._apply_extra_or_extend(node, names, value)

    def _apply_extra_or_extend(
        self, node: ast.stmt, names: tuple[str, ...], value: ast.AST | None
    ) -> bool:
        extra_name = next((name for name in names if name.startswith("_EXTRA")), None)
        if extra_name is not None and isinstance(value, ast.List):
            return self._assign_extra(extra_name, value)
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            return self._extend_pairs(node.value)
        return True

    def _assign_pairs(self, value: ast.List) -> bool:
        resolved = literal_value(value)
        if not isinstance(resolved, list):
            return False
        self.pairs = resolved
        return True

    def _filter_pairs(self, value: ast.ListComp) -> bool:
        if self.pairs is None or self.drop is None:
            return False
        if not _is_drop_listcomp(value):
            return False
        drop = self.drop
        self.pairs = [
            pair
            for pair in self.pairs
            if _pair_identity(pair)["success_slug"] not in drop
        ]
        self.saw_filter = True
        return True

    def _assign_drop(self, value: ast.AST) -> bool:
        resolved = literal_value(value)
        if not isinstance(resolved, set):
            return False
        self.drop = resolved
        return True

    def _assign_extra(self, name: str, value: ast.List) -> bool:
        resolved = literal_value(value)
        if not isinstance(resolved, list):
            return False
        self.extras[name] = resolved
        return True

    def _extend_pairs(self, call: ast.Call) -> bool:
        """``PAIRS.extend(_EXTRA...)``; any other top-level call is ignored."""

        if not _is_pairs_extend(call):
            return True
        src_name = _single_name_arg(call)
        if self.pairs is None or src_name is None:
            return False
        if src_name not in self.extras:
            return False
        self.pairs.extend(self.extras[src_name])
        return True

    def record(self) -> dict[str, Any] | None:
        if self.pairs is None or self.drop is None:
            return None
        if not self.saw_filter:
            return None
        rows = [_pair_identity(pair) for pair in self.pairs]
        if not rows or any(row["success_slug"] is None for row in rows):
            return None
        return _rows_record(SHAPE_LITERAL, rows)


def _is_pairs_extend(call: ast.Call) -> bool:
    func = call.func
    if not isinstance(func, ast.Attribute) or func.attr != "extend":
        return False
    return isinstance(func.value, ast.Name) and func.value.id == "PAIRS"


def _single_name_arg(call: ast.Call) -> str | None:
    if len(call.args) != 1 or not isinstance(call.args[0], ast.Name):
        return None
    return call.args[0].id


def _is_drop_listcomp(node: ast.ListComp) -> bool:
    if len(node.generators) != 1:
        return False
    gen = node.generators[0]
    return _yields_its_target(node, gen) and _filters_pairs_by_not_in(gen)


def _yields_its_target(node: ast.ListComp, gen: ast.comprehension) -> bool:
    if not isinstance(node.elt, ast.Name) or not isinstance(gen.target, ast.Name):
        return False
    return node.elt.id == gen.target.id


def _filters_pairs_by_not_in(gen: ast.comprehension) -> bool:
    if not isinstance(gen.iter, ast.Name) or gen.iter.id != "PAIRS":
        return False
    if len(gen.ifs) != 1:
        return False
    test = gen.ifs[0]
    return isinstance(test, ast.Compare) and isinstance(test.ops[0], ast.NotIn)


def _assigned_nonempty_list(node: ast.stmt, wanted: str) -> ast.List | None:
    """The value of a top-level ``wanted = [...]`` with at least one element."""

    name, value = assignment_of(node)
    if name != wanted or not isinstance(value, ast.List):
        return None
    return value if value.elts else None


def _collect_or_none(items, convert) -> list[Any] | None:
    """``convert`` every item, or None as soon as one item does not convert."""

    out: list[Any] = []
    for item in items:
        converted = convert(item)
        if converted is None:
            return None
        out.append(converted)
    return out


def _suc_fail_list(tree: ast.AST) -> dict[str, Any] | None:
    for node in getattr(tree, "body", ()):
        value = _assigned_nonempty_list(node, "PAIRS")
        if value is None or not all(_is_suc_fail_tuple(elt) for elt in value.elts):
            continue
        rows = [_suc_fail_identity(elt) for elt in value.elts]
        if rows and rows[0]["success_slug"]:
            return _rows_record(SHAPE_SUC_FAIL, rows)
    return None


def _leftover_pair_list(tree: ast.AST) -> dict[str, Any] | None:
    for node in getattr(tree, "body", ()):
        value = _assigned_nonempty_list(node, "PAIRS")
        if value is None or not all(call_name(elt) == "leftover_pair" for elt in value.elts):
            continue
        rows = _collect_or_none(value.elts, _leftover_pair_identity)
        return None if rows is None else _rows_record(SHAPE_LEFTOVER, rows)
    return None


def _leftover_pair_identity(node: ast.AST) -> dict[str, Any] | None:
    kwargs = call_kwargs(node)
    if kwargs is None or not {"s", "fs"}.issubset(kwargs):
        return None
    return _gem_handoff_row(kwargs["s"], kwargs["fs"], kwargs.get("g"))


def _gem_handoff_row(success_slug: Any, fail_slug: Any, gem: Any) -> dict[str, Any]:
    """Pair identity whose plants are the ``{gem}-prod`` / ``{gem}-jobs`` services."""

    return {
        "success_slug": success_slug,
        "fail_slug": fail_slug,
        "success_plant": f"{gem}-prod" if isinstance(gem, str) else None,
        "fail_plant": f"{gem}-jobs" if isinstance(gem, str) else None,
        "fail_handoff": True,
    }


def _keep_extend(tree: ast.AST) -> dict[str, Any] | None:
    return _fold_module(tree, _KeepExtendScan())


class _KeepExtendScan:
    """``KEEP`` slug set, an empty ``PAIRS``, and ``_EXTRA*`` lists of ``(_suc, _fail)``."""

    def __init__(self) -> None:
        self.keep: set[str] | None = None
        self.extra_rows: list[dict[str, Any]] = []
        self.saw_empty_pairs = False

    def apply(self, node: ast.stmt) -> bool:
        name, value = assignment_of(node)
        if name == "KEEP" and value is not None:
            self.keep = _literal_str_set(value)
            return self.keep is not None
        if name == "PAIRS" and _is_empty_list(value):
            self.saw_empty_pairs = True
            return True
        if _is_extra_name(name) and isinstance(value, ast.List):
            return self._extend_extras(value.elts)
        return True

    def _extend_extras(self, elts: list[ast.expr]) -> bool:
        if not all(_is_suc_fail_tuple(elt) for elt in elts):
            return False
        self.extra_rows.extend(_suc_fail_identity(elt) for elt in elts)
        return True

    def record(self) -> dict[str, Any] | None:
        if self.keep is None or not self.saw_empty_pairs:
            return None
        if not self.extra_rows:
            return None
        keep, extra_rows = self.keep, self.extra_rows
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


def _is_empty_list(value: ast.AST | None) -> bool:
    return isinstance(value, ast.List) and not value.elts


def _is_extra_name(name: str | None) -> bool:
    return name is not None and name.startswith("_EXTRA")


def _literal_str_set(value: ast.AST) -> set[str] | None:
    resolved = literal_value(value)
    if not isinstance(resolved, set) or not all(isinstance(item, str) for item in resolved):
        return None
    return {str(item) for item in resolved}


def _k8s_cli_tables(tree: ast.AST) -> dict[str, Any] | None:
    return _fold_module(tree, _K8sCliScan())


class _K8sCliScan:
    """``K8S`` rows plus either a ``CLI_SPEC`` table or a ``CLI`` list of ``file_pair``."""

    def __init__(self) -> None:
        self.k8s: list[Any] | None = None
        self.cli_spec: list[Any] | None = None
        self.cli_rows: list[dict[str, Any]] | None = None

    def apply(self, node: ast.stmt) -> bool:
        name, value = assignment_of(node)
        if name == "K8S" and value is not None:
            self.k8s = _nonempty_literal_list(value)
            return self.k8s is not None
        if name == "CLI_SPEC" and value is not None:
            self.cli_spec = _nonempty_literal_list(value)
            return self.cli_spec is not None
        if name == "CLI":
            elts = _file_pair_elts(value)
            if elts is not None:
                return self._assign_cli_rows(elts)
        return True

    def _assign_cli_rows(self, elts: list[ast.expr]) -> bool:
        rows = _collect_or_none(elts, _file_pair_identity)
        if rows is None:
            return False
        self.cli_rows = rows
        return True

    def record(self) -> dict[str, Any] | None:
        if self.k8s is None:
            return None
        k8s_rows = [_k8s_identity(row) for row in self.k8s]
        if self.cli_spec is not None:
            cli_ident = [_cli_spec_identity(row) for row in self.cli_spec]
            return _rows_record(SHAPE_K8S_CLI_SPEC, k8s_rows + cli_ident)
        if self.cli_rows is not None:
            return _rows_record(SHAPE_K8S_FILE, k8s_rows + self.cli_rows)
        return None


def _nonempty_literal_list(value: ast.AST) -> list[Any] | None:
    resolved = literal_value(value)
    if not isinstance(resolved, list) or not resolved:
        return None
    return resolved


def _file_pair_elts(value: ast.AST | None) -> list[ast.expr] | None:
    """The elements of a non-empty list made only of ``file_pair(...)`` calls."""

    if not isinstance(value, ast.List) or not value.elts:
        return None
    if not all(call_name(elt) == "file_pair" for elt in value.elts):
        return None
    return value.elts


def _file_pair_identity(node: ast.AST) -> dict[str, Any] | None:
    kwargs = call_kwargs(node)
    if kwargs is None or "s" not in kwargs:
        return None
    slug = kwargs["s"]
    return _gem_handoff_row(slug, slug.replace("-vs-old", "-old-leftover"), kwargs.get("g"))


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
