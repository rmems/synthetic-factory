#!/usr/bin/env python3
"""AST-extract ``CATALOG`` / ``PAIRS`` from a DPR mill source.

Reads mill text through :func:`ast.parse` only. Constructor calls
(``OK`` / ``FAIL`` / ``okp`` / ``failp``) are lowered to literals; the mill
publisher, ``round_txn``, and hopper scripts are never imported or executed.
"""

from __future__ import annotations

import ast
import hashlib
import json
import re
from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .vocabulary import (
    CATALOG_ASSIGNMENT_NAMES,
    CATALOG_FILENAME,
    CATALOG_SCHEMA_ID,
    CATALOG_SLICE,
    FACTORY,
    GENERATOR,
    HOPPER_NAME_NEEDLES,
    KIND_GEN,
    KIND_HOPPER,
    KIND_LOOP,
    KIND_PAIRS,
    KIND_PLANTS,
    LEGACY_REF,
    LEFTOVER_PLANT_KEYS,
    PAIR_CTOR_NAMES,
    PAIRS_FILENAME,
    PLANTS_FILENAME,
    PRESERVE_COMMIT,
    REPRESENTATIVE_PAIR_POLICY,
)

_ROUND_RE = re.compile(r"r(\d+)")


class DprExtractError(ValueError):
    """A mill source is not a constant catalog (or is an excluded hopper)."""


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def mill_id_for_path(path: str) -> str:
    return Path(path).stem


def catalog_first_from_name(path: str) -> int | None:
    match = _ROUND_RE.search(Path(path).name)
    return int(match.group(1)) if match else None


def is_hopper_path(path: str) -> bool:
    name = Path(path).name.lower()
    return any(needle in name for needle in HOPPER_NAME_NEEDLES)


def _jsonable(value: Any) -> Any:
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    return value


def _dict_items(node: ast.Dict) -> list[tuple[ast.expr, ast.expr]]:
    """The key and value nodes of a dict literal; ``**`` unpacking refuses before any is read."""

    items: list[tuple[ast.expr, ast.expr]] = []
    for key, value in zip(node.keys, node.values):
        if key is None:
            raise DprExtractError("catalog dict uses unpacking")
        items.append((key, value))
    return items


def _signed(node: ast.AST) -> ast.UnaryOp:
    """A unary minus or plus; any other node is not a constant."""

    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
        return node
    raise DprExtractError(f"catalog node is not a constant ({type(node).__name__})")


def _const_eval(node: ast.AST) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        return [_const_eval(item) for item in node.elts]
    if isinstance(node, ast.Dict):
        return {_const_eval(key): _const_eval(value) for key, value in _dict_items(node)}
    signed = _signed(node)
    operand = _const_eval(signed.operand)
    return -operand if isinstance(signed.op, ast.USub) else +operand


def _assignment_names(node: ast.stmt) -> list[str]:
    if isinstance(node, ast.Assign):
        return [target.id for target in node.targets if isinstance(target, ast.Name)]
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        return [node.target.id]
    return []


def _assignment_value(node: ast.stmt) -> ast.AST | None:
    if isinstance(node, ast.Assign):
        return node.value
    if isinstance(node, ast.AnnAssign):
        return node.value
    return None


def extract_catalog_nodes(source: str, *, filename: str = "<dpr-mill>") -> dict[str, ast.AST]:
    """Top-level catalog assignments as AST nodes. Never evaluates them."""

    try:
        tree = ast.parse(source, filename=filename)
    except SyntaxError as exc:
        raise DprExtractError(f"{filename} does not parse: {exc}") from exc
    found: dict[str, ast.AST] = {}
    for node in tree.body:
        names = _assignment_names(node)
        value = _assignment_value(node)
        if value is None:
            continue
        for name in names:
            if name in CATALOG_ASSIGNMENT_NAMES:
                found[name] = value
    return found


def _literal_or_none(node: ast.AST) -> Any | None:
    try:
        return _const_eval(node)
    except DprExtractError:
        return None


def _ctor_call(node: ast.AST) -> tuple[ast.Call, str]:
    """A pair side's call and constructor name, refused unless it is a plain known call."""

    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
        raise DprExtractError(f"pair side is not a constructor call ({type(node).__name__})")
    ctor = node.func.id
    if ctor not in PAIR_CTOR_NAMES:
        raise DprExtractError(f"pair side uses unknown constructor {ctor!r}")
    if any(isinstance(arg, ast.Starred) for arg in node.args):
        raise DprExtractError(f"{ctor}() uses starred arguments")
    if any(keyword.arg is None for keyword in node.keywords):
        raise DprExtractError(f"{ctor}() uses keyword unpacking")
    return node, ctor


def _extract_ctor(node: ast.AST) -> dict[str, Any]:
    call, ctor = _ctor_call(node)
    row: dict[str, Any] = {"ctor": ctor}
    if call.args:
        row["args"] = [_const_eval(arg) for arg in call.args]
    if call.keywords:
        row["kwargs"] = {keyword.arg: _const_eval(keyword.value) for keyword in call.keywords}
    if "args" not in row and "kwargs" not in row:
        raise DprExtractError(f"{ctor}() has no arguments")
    return row


def _ctor_slug(side: Mapping[str, Any]) -> str:
    kwargs = side.get("kwargs")
    if isinstance(kwargs, dict) and isinstance(kwargs.get("slug"), str) and kwargs["slug"]:
        return kwargs["slug"]
    args = side.get("args")
    if isinstance(args, list) and args and isinstance(args[0], str) and args[0]:
        return args[0]
    raise DprExtractError("pair side has no slug")


def _pair_from_tuple(node: ast.AST) -> dict[str, Any]:
    if not isinstance(node, ast.Tuple) or len(node.elts) != 2:
        raise DprExtractError("PAIRS row is not an (ok, fail) tuple")
    ok = _extract_ctor(node.elts[0])
    fail = _extract_ctor(node.elts[1])
    return {
        "ok": ok,
        "fail": fail,
        "slug": _ctor_slug(ok),
        "fail_slug": _ctor_slug(fail),
    }


def _list_rows(node: ast.AST) -> list[ast.AST]:
    if not isinstance(node, ast.List):
        raise DprExtractError("catalog assignment is not a list literal")
    return list(node.elts)


def _catalog_list_name(nodes: Mapping[str, ast.AST]) -> str:
    for name in ("NEW_PAIRS", "MORE", "PAIRS", "CATALOG"):
        value = nodes.get(name)
        if value is None:
            continue
        if name == "PAIRS" and not isinstance(value, ast.List):
            continue
        if isinstance(value, ast.List):
            return name
    raise DprExtractError("source has no list-literal CATALOG / PAIRS / NEW_PAIRS / MORE")


def _assigned_values(tree: ast.Module, name: str) -> Iterator[ast.AST]:
    """Values of top-level ``=`` assignments that bind ``name``, in source order."""

    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
            yield node.value


def _str_constant(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _joined_path_operand(value: ast.AST) -> str | None:
    if not isinstance(value, ast.BinOp) or not isinstance(value.op, ast.Div):
        return None
    return _str_constant(value.right)


def _path_call_operand(value: ast.AST) -> str | None:
    if not isinstance(value, ast.Call) or not isinstance(value.func, ast.Name):
        return None
    if value.func.id != "Path" or len(value.args) != 1:
        return None
    return _str_constant(value.args[0])


def _first_operand(source: str, name: str, operand: Callable[[ast.AST], str | None]) -> str | None:
    for value in _assigned_values(ast.parse(source), name):
        text = operand(value)
        if text is not None:
            return text
    return None


def extract_joined_path_constant(source: str, name: str) -> str | None:
    """``NAME = <expr> / "relative/path"`` → the string operand, if that is the shape."""

    return _first_operand(source, name, _joined_path_operand)


def extract_call_path_constant(source: str, name: str) -> str | None:
    """``NAME = Path("/tmp/dpr_mill_rNNNN.py")`` → the string operand."""

    return _first_operand(source, name, _path_call_operand)


def _refuse_hopper(path: str) -> None:
    if is_hopper_path(path):
        raise DprExtractError(f"{path} is an lrd hopper; excluded from the dpr catalog")


@dataclass(frozen=True)
class _MillText:
    """One mill source file's identity: where it lives, its bytes, and its named round."""

    path: str
    mill_id: str
    blob_sha: str
    payload: bytes
    named_first: int | None

    def identity(self) -> dict[str, Any]:
        return {
            "mill_id": self.mill_id,
            "path": self.path,
            "blob_sha": self.blob_sha,
            "sha256": sha256_bytes(self.payload),
        }


def extract_mill_catalog(
    source: str,
    *,
    path: str,
    blob_sha: str = "",
) -> dict[str, Any]:
    """Structured catalog extract for one mill source file. Never execs."""

    _refuse_hopper(path)
    payload = source.encode()
    nodes = extract_catalog_nodes(source, filename=path)
    mill = _MillText(
        path=path,
        mill_id=mill_id_for_path(path),
        blob_sha=blob_sha,
        payload=payload,
        named_first=catalog_first_from_name(path),
    )
    list_name = _catalog_list_name(nodes)
    if list_name == "CATALOG":
        return _plants_record(nodes, mill)
    return _pairs_record(nodes, list_name, mill)


def _optional_int(nodes: Mapping[str, ast.AST], name: str) -> int | None:
    node = nodes.get(name)
    if node is None:
        return None
    value = _literal_or_none(node)
    if type(value) is int:
        return value
    return None


def _optional_text(nodes: Mapping[str, ast.AST], name: str) -> str | None:
    node = nodes.get(name)
    if node is None:
        return None
    value = _literal_or_none(node)
    return value if isinstance(value, str) and value else None


def _refuse_bad_plant_rows(plants: list[Any], path: str) -> None:
    for index, row in enumerate(plants):
        if not isinstance(row, dict):
            raise DprExtractError(f"{path}: CATALOG[{index}] is not a dict")
        missing = [key for key in LEFTOVER_PLANT_KEYS if key not in row]
        if missing:
            raise DprExtractError(f"{path}: CATALOG[{index}] missing {missing}")
        if not isinstance(row["slug"], str) or not row["slug"]:
            raise DprExtractError(f"{path}: CATALOG[{index}].slug is empty")


def _plants_generator(nodes: Mapping[str, ast.AST]) -> str:
    return _optional_text(nodes, "GEN") or _optional_text(nodes, "GENERATOR") or GENERATOR


def _plants_record(nodes: Mapping[str, ast.AST], mill: _MillText) -> dict[str, Any]:
    path = mill.path
    plants = [_jsonable(_const_eval(item)) for item in _list_rows(nodes["CATALOG"])]
    if not plants:
        raise DprExtractError(f"{path}: CATALOG is empty")
    _refuse_bad_plant_rows(plants, path)
    factory = _optional_text(nodes, "FACTORY") or FACTORY
    generator = _plants_generator(nodes)
    return {
        **mill.identity(),
        "kind": KIND_PLANTS,
        "catalog_first": mill.named_first,
        "n_rows": len(plants),
        "max_rounds": _optional_int(nodes, "MAX_ROUNDS"),
        "first_slug": plants[0]["slug"],
        "last_slug": plants[-1]["slug"],
        "generator": generator,
        "factory": factory,
        "plants": plants,
    }


def _pairs_record(
    nodes: Mapping[str, ast.AST], list_name: str, mill: _MillText
) -> dict[str, Any]:
    pairs = [_jsonable(_pair_from_tuple(item)) for item in _list_rows(nodes[list_name])]
    if not pairs:
        raise DprExtractError(f"{mill.path}: {list_name} is empty")
    catalog_first = _optional_int(nodes, "START") or mill.named_first
    generator = _optional_text(nodes, "GENERATOR") or GENERATOR
    return {
        **mill.identity(),
        "kind": KIND_PAIRS,
        "list_name": list_name,
        "catalog_first": catalog_first,
        "n_rows": len(pairs),
        "first_slug": pairs[0]["slug"],
        "last_slug": pairs[-1]["slug"],
        "generator": generator,
        "factory": FACTORY,
        "pairs": pairs,
    }


def mill_header(mill: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in mill.items() if key not in {"pairs", "plants"}}


def is_representative_pair_row(row: Mapping[str, Any]) -> bool:
    return "ok" in row


def compact_deferred_pair(mill_id: str, path: str, pair: Mapping[str, Any]) -> dict[str, str]:
    return {
        "fail_slug": pair["fail_slug"],
        "mill_id": mill_id,
        "path": path,
        "slug": pair["slug"],
    }


def _deferred_pairs(mill: Mapping[str, Any]) -> list[Any]:
    """The pairs a mill defers: none under "all", the interior under "ends", else every pair."""

    policy = REPRESENTATIVE_PAIR_POLICY.get(mill["mill_id"])
    if policy == "all":
        return []
    pairs = list(mill.get("pairs") or ())
    if policy != "ends":
        return pairs
    return pairs[1:-1] if len(pairs) > 2 else []


def select_deferred_pair_rows(mills: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    ordered = sorted(
        (mill for mill in mills if mill.get("kind") == KIND_PAIRS),
        key=lambda mill: (mill.get("catalog_first") or 0, mill["mill_id"]),
    )
    rows: list[dict[str, Any]] = []
    for mill in ordered:
        for pair in _deferred_pairs(mill):
            rows.append(compact_deferred_pair(mill["mill_id"], mill["path"], pair))
    return rows


def select_representative_pair_rows(mills: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for mill in mills:
        if mill.get("kind") != KIND_PAIRS:
            continue
        pairs = list(mill.get("pairs") or ())
        policy = REPRESENTATIVE_PAIR_POLICY.get(mill["mill_id"])
        if policy == "all":
            selected = pairs
        elif policy == "ends":
            selected = [pairs[0], pairs[-1]] if len(pairs) > 1 else pairs
        else:
            continue
        rows.extend({"mill_id": mill["mill_id"], **pair} for pair in selected)
    return rows


def select_representative_plant_rows(mills: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for mill in mills:
        if mill.get("kind") != KIND_PLANTS:
            continue
        rows.extend({"mill_id": mill["mill_id"], **plant} for plant in mill.get("plants") or ())
    return rows


def catalog_document(mills: list[dict[str, Any]]) -> dict[str, Any]:
    pair_rows = sum(mill["n_rows"] for mill in mills if mill["kind"] == KIND_PAIRS)
    plant_rows = sum(mill["n_rows"] for mill in mills if mill["kind"] == KIND_PLANTS)
    committed_plants = select_representative_plant_rows(mills)
    committed_pairs = len(select_representative_pair_rows(mills)) + len(
        select_deferred_pair_rows(mills)
    )
    return {
        "schema": CATALOG_SCHEMA_ID,
        "slice": CATALOG_SLICE,
        "source_ref": LEGACY_REF,
        "preserve_commit": PRESERVE_COMMIT,
        "factory": FACTORY,
        "generator": GENERATOR,
        "n_mills": len(mills),
        "n_pair_rows": pair_rows,
        "n_plant_rows": plant_rows,
        "committed_pair_rows": committed_pairs,
        "committed_plant_rows": len(committed_plants),
        "excluded_kinds": [KIND_HOPPER, KIND_LOOP, KIND_GEN],
        "mills": {mill["mill_id"]: mill_header(mill) for mill in mills},
    }


def dumps_catalog(document: Mapping[str, Any]) -> str:
    return json.dumps(document, ensure_ascii=True, indent=2, sort_keys=True) + "\n"


def dumps_jsonl(rows: Sequence[Mapping[str, Any]]) -> str:
    lines = [
        json.dumps(row, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
        for row in rows
    ]
    return "\n".join(lines) + ("\n" if lines else "")


def catalog_json_path(package_dir: Path | None = None) -> Path:
    root = package_dir if package_dir is not None else Path(__file__).resolve().parent
    return root / CATALOG_FILENAME


def plants_jsonl_path(package_dir: Path | None = None) -> Path:
    root = package_dir if package_dir is not None else Path(__file__).resolve().parent
    return root / PLANTS_FILENAME


def pairs_jsonl_path(package_dir: Path | None = None) -> Path:
    root = package_dir if package_dir is not None else Path(__file__).resolve().parent
    return root / PAIRS_FILENAME


def write_catalog_document(mills: list[dict[str, Any]], package_dir: Path | None = None) -> Path:
    destination = catalog_json_path(package_dir)
    destination.write_text(dumps_catalog(catalog_document(mills)), encoding="utf-8")
    plants_jsonl_path(package_dir).write_text(
        dumps_jsonl(select_representative_plant_rows(mills)), encoding="utf-8"
    )
    pairs_jsonl_path(package_dir).write_text(
        dumps_jsonl(select_representative_pair_rows(mills)), encoding="utf-8"
    )
    return destination
