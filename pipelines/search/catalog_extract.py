#!/usr/bin/env python3
"""AST-extract search leftover-mill catalog identity from a mill source.

Evaluates only literal catalog assignments (``FACTORY``, ``GEN``,
``CATALOG_FIRST``, ``N_ROUNDS``, ``HOP``, ``PAIRS``). Does not import, compile,
or exec the leftover3 / leftover-lll publishers, so those scripts stay off
this branch.
"""

from __future__ import annotations

import ast
import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .catalog_ast import UNSET, assignment_of, literal_value, module_docstring
from .vocabulary import (
    CATALOG_FILENAME,
    CATALOG_SCHEMA_ID,
    FACTORY,
    GENERATOR,
    KIND_LEFTOVER_PAIRS,
    LEGACY_REF,
    PRESERVE_COMMIT,
    SHAPE_PAIR_6TUPLES,
    SLICE_ID,
)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def mill_id_for_path(path: str) -> str:
    return Path(path).stem


def extract_mill_catalog(
    source: str,
    *,
    path: str,
    blob_sha: str = "",
) -> dict[str, Any]:
    """Structured catalog extract for one leftover-mill source file."""

    payload = source.encode()
    tree = ast.parse(source, filename=path)
    mill_id = mill_id_for_path(path)
    constants = _module_constants(tree)
    factory = constants.get("FACTORY", FACTORY)
    generator = constants.get("GEN", GENERATOR)
    catalog_first = constants.get("CATALOG_FIRST")
    n_rounds = constants.get("N_ROUNDS")
    hops = constants.get("HOP")
    pairs_raw = constants.get("PAIRS")
    if not isinstance(factory, str) or not factory:
        raise ValueError(f"{path} FACTORY is not a non-empty string")
    if not isinstance(generator, str) or not generator:
        raise ValueError(f"{path} GEN is not a non-empty string")
    if not isinstance(catalog_first, int):
        raise ValueError(f"{path} CATALOG_FIRST is not an int")
    if not isinstance(n_rounds, int) or n_rounds < 1:
        raise ValueError(f"{path} N_ROUNDS is not a positive int")
    if not _is_factory_list(hops):
        raise ValueError(f"{path} HOP is not a literal list of factory slugs")
    rows = _pair_rows(pairs_raw, path=path)
    if len(rows) != n_rounds:
        raise ValueError(f"{path} N_ROUNDS={n_rounds} disagrees with {len(rows)} pairs")
    return {
        "mill_id": mill_id,
        "path": path,
        "blob_sha": blob_sha,
        "sha256": sha256_bytes(payload),
        "kind": KIND_LEFTOVER_PAIRS,
        "shape": SHAPE_PAIR_6TUPLES,
        "catalog_first": catalog_first,
        "n_rounds": n_rounds,
        "n_rows": len(rows),
        "n_hops": len(hops),
        "first_slug": rows[0]["success_slug"],
        "last_slug": rows[-1]["success_slug"],
        "generator": generator,
        "factory": factory,
        "hops": list(hops),
        "doc_first_line": _first_line(module_docstring(tree)),
        "pairs": rows,
    }


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


def _is_factory_list(value: Any) -> bool:
    if not isinstance(value, list) or not value:
        return False
    return all(isinstance(item, str) and item.endswith("-factory") for item in value)


def _pair_rows(pairs_raw: Any, *, path: str) -> list[dict[str, Any]]:
    if not isinstance(pairs_raw, list) or not pairs_raw:
        raise ValueError(f"{path} PAIRS is not a non-empty literal list")
    rows: list[dict[str, Any]] = []
    for index, pair in enumerate(pairs_raw):
        if not isinstance(pair, (tuple, list)) or len(pair) != 2:
            raise ValueError(f"{path} PAIRS[{index}] is not a 2-tuple")
        success, fail = pair
        if not _is_six_strings(success) or not _is_six_strings(fail):
            raise ValueError(f"{path} PAIRS[{index}] arms are not 6-string tuples")
        rows.append(
            {
                "success_slug": success[0],
                "fail_slug": fail[0],
                "success_engine": success[1],
                "fail_engine": fail[1],
                "success_wrong": success[2],
                "fail_wrong": fail[2],
                "success_fix": success[3],
                "fail_leftover": fail[3],
                "success_ticket": success[4],
                "fail_ticket": fail[4],
                "success_url": success[5],
                "fail_url": fail[5],
                "fail_handoff": True,
            }
        )
    return rows


def _is_six_strings(arm: Any) -> bool:
    return (
        isinstance(arm, (tuple, list))
        and len(arm) == 6
        and all(isinstance(item, str) and item for item in arm)
    )


def _first_line(doc: str) -> str:
    for line in doc.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def mill_summary(record: Mapping[str, Any], *, include_pairs: bool) -> dict[str, Any]:
    """Catalog mill row: identity plus optional pair list."""

    summary = {
        "mill_id": record["mill_id"],
        "path": record["path"],
        "blob_sha": record["blob_sha"],
        "sha256": record["sha256"],
        "kind": record["kind"],
        "shape": record["shape"],
        "catalog_first": record["catalog_first"],
        "n_rounds": record["n_rounds"],
        "n_rows": record["n_rows"],
        "n_hops": record["n_hops"],
        "first_slug": record["first_slug"],
        "last_slug": record["last_slug"],
        "generator": record["generator"],
        "factory": record["factory"],
        "hops": list(record["hops"]),
        "doc_first_line": record["doc_first_line"],
    }
    if include_pairs:
        summary["pairs"] = list(record.get("pairs") or ())
    return summary


def catalog_document(mills: list[dict[str, Any]]) -> dict[str, Any]:
    pair_rows = sum(mill["n_rows"] for mill in mills)
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


def write_catalog_document(document: Mapping[str, Any], path: Path | None = None) -> Path:
    destination = path if path is not None else catalog_json_path()
    destination.write_text(dumps_catalog(document), encoding="utf-8")
    return destination
