#!/usr/bin/env python3
"""AST-extract ssl-mill-lll episode P() mills from legacy-mill-lane.

Mill scripts are read only as text through ``ast.parse``; they are never
imported or executed. Compact episode identity rows land in
``episode_pairs.jsonl`` beside ``CATALOG.json`` under this package directory.
"""

from __future__ import annotations

import ast
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ._contract import (
    FINDING_CATALOG_FIELD_INVALID,
    FINDING_CATALOG_FIELD_MISSING,
    FINDING_CATALOG_FILE_MISSING,
    FINDING_PLANTS_SHA_MISMATCH,
    bind_import_twin,
    load_strict_json,
    refuse,
    refuse_when,
)
from .catalog_mill import DEFAULT_MILL_CATALOG_DIR, sha256_bytes

EPISODE_PAIRS_FILENAME = "episode_pairs.jsonl"
EPISODE_SHAPE = "ssl-episode-p-catalog-v1"
EPISODE_MILL_SOURCE_PATHS = (
    "experiments/ssl-mill-lll-r182.py",
    "experiments/ssl-mill-lll-r190.py",
    "experiments/ssl-mill-lll-r206.py",
    "experiments/ssl-mill-lll-r286.py",
)
REQUIRED_EPISODE_HEADER_FIELDS = (
    "episode_pairs_filename",
    "episode_pairs_sha256",
    "n_episode_pair_rows_extracted",
    "n_episode_pair_rows_committed",
)

__all__ = [
    "EPISODE_MILL_SOURCE_PATHS",
    "EPISODE_PAIRS_FILENAME",
    "EPISODE_SHAPE",
    "ast_extract_episode_mill_pairs",
    "catalog_episode_mill_check",
    "load_episode_mill_catalog",
    "materialize_p_pair",
]


def _literal_str(node: ast.AST, where: str) -> str:
    refuse_when(
        not isinstance(node, ast.Constant) or not isinstance(node.value, str),
        FINDING_CATALOG_FIELD_INVALID,
        f"{where} must be a string literal",
    )
    assert isinstance(node, ast.Constant)
    return node.value


def _module_constants(tree: ast.Module) -> dict[str, Any]:
    found: dict[str, Any] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if not isinstance(target, ast.Name):
                continue
            name = target.id
            if name in {"FACTORY", "GEN", "CATALOG_FIRST"}:
                value = node.value
                if isinstance(value, ast.Constant) and isinstance(value.value, (str, int)):
                    if not isinstance(value.value, bool):
                        found[name] = value.value
    return found


def _pairs_list(tree: ast.Module) -> ast.List:
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "PAIRS":
                    refuse_when(
                        not isinstance(node.value, ast.List),
                        FINDING_CATALOG_FIELD_INVALID,
                        "PAIRS must be a list",
                    )
                    return node.value
    refuse(FINDING_CATALOG_FIELD_INVALID, "episode mill source has no PAIRS list")


def materialize_p_pair(sdk: str, leftover: str, ta: str, tb: str) -> tuple[dict[str, str], dict[str, str]]:
    """Rebuild the suc/fail dicts from ``P()`` without executing the mill."""

    ok = {
        "slug": f"{sdk}-leftover-{leftover}-reload-lll",
        "domain": f"{sdk}-leftover-leftover-leftover-{leftover}-reload",
        "seed": f"{sdk}-leftover-{leftover}-reload-lll",
        "root": f"{sdk}-lll",
        "f1": f"{sdk}-lll/reload.sh",
        "f2": f"{sdk}-lll/cert.conf",
        "token": f"TESTONLY_ssl_{sdk[:4]}_{leftover[:4]}_lll_n0t_live",
        "wrong": "copy leftover leftover leftover cert without reload",
        "right": f"reload leftover leftover leftover {sdk} after {leftover} swap",
        "ticket": ta,
        "leftover": leftover,
        "sdk": sdk,
    }
    bad = {
        "slug": f"{sdk}-drop-{leftover}-handoff-lll",
        "domain": f"{sdk}-drop-leftover-leftover-leftover-{leftover}",
        "seed": f"{sdk}-drop-{leftover}-handoff-lll",
        "root": f"{sdk}-lll",
        "f1": f"{sdk}-lll/reload.sh",
        "f2": f"{sdk}-lll/fleet.conf",
        "token": f"TESTONLY_ssl_{sdk[:4]}_drop_{leftover[:4]}_lll_n0t_live",
        "wrong": f"drop leftover leftover leftover {leftover} chain",
        "right": f"platform leftover leftover leftover {leftover} install",
        "ticket": tb,
        "platform": f"pki-plat-{sdk}",
        "leftover": leftover,
        "sdk": sdk,
    }
    return ok, bad


def ast_extract_episode_mill_pairs(source: str, *, source_path: str) -> tuple[dict[str, Any], ...]:
    """Return compact episode identity rows for one ssl-mill-lll-r* module."""

    tree = ast.parse(source, filename=source_path)
    consts = _module_constants(tree)
    factory = consts.get("FACTORY", "ssl-cert-rotation-factory")
    generator = consts.get("GEN", "grok-4.6")
    catalog_first = consts.get("CATALOG_FIRST")
    refuse_when(
        not isinstance(catalog_first, int) or isinstance(catalog_first, bool),
        FINDING_CATALOG_FIELD_INVALID,
        f"{source_path} missing int CATALOG_FIRST",
    )
    mill_id = Path(source_path).stem
    pairs_node = _pairs_list(tree)
    rows: list[dict[str, Any]] = []
    for index, item in enumerate(pairs_node.elts):
        refuse_when(
            not isinstance(item, ast.Call)
            or not isinstance(item.func, ast.Name)
            or item.func.id != "P"
            or len(item.args) != 4,
            FINDING_CATALOG_FIELD_INVALID,
            f"{source_path} PAIRS[{index}] must be P(sdk, leftover, ta, tb)",
        )
        sdk = _literal_str(item.args[0], f"{source_path} PAIRS[{index}].sdk")
        leftover = _literal_str(item.args[1], f"{source_path} PAIRS[{index}].leftover")
        ta = _literal_str(item.args[2], f"{source_path} PAIRS[{index}].ta")
        tb = _literal_str(item.args[3], f"{source_path} PAIRS[{index}].tb")
        ok, bad = materialize_p_pair(sdk, leftover, ta, tb)
        rows.append(
            {
                "mill_id": mill_id,
                "index": index,
                "round": catalog_first + index,
                "factory": factory,
                "generator": generator,
                "source": source_path,
                "shape": EPISODE_SHAPE,
                "ok": ok,
                "bad": bad,
            }
        )
    return tuple(rows)


def _require_keys(document: Mapping[str, Any], keys: tuple[str, ...], label: str) -> None:
    missing = [key for key in keys if key not in document]
    refuse_when(bool(missing), FINDING_CATALOG_FIELD_MISSING, f"{label} missing {missing}")


def load_episode_mill_catalog(
    directory: Path | None = None,
) -> tuple[Mapping[str, Any], tuple[dict[str, Any], ...]]:
    root = directory or DEFAULT_MILL_CATALOG_DIR
    catalog_path = root / "CATALOG.json"
    pairs_path = root / EPISODE_PAIRS_FILENAME
    refuse_when(not catalog_path.is_file(), FINDING_CATALOG_FILE_MISSING, f"missing {catalog_path}")
    refuse_when(not pairs_path.is_file(), FINDING_CATALOG_FILE_MISSING, f"missing {pairs_path}")
    meta = load_strict_json(catalog_path.read_text(encoding="utf-8"))
    _require_keys(meta, REQUIRED_EPISODE_HEADER_FIELDS, "CATALOG.json")
    payload = pairs_path.read_bytes()
    refuse_when(
        sha256_bytes(payload) != meta["episode_pairs_sha256"],
        FINDING_PLANTS_SHA_MISMATCH,
        f"{pairs_path} sha256 drift",
    )
    rows: list[dict[str, Any]] = []
    for line in payload.splitlines():
        if not line:
            continue
        rows.append(json.loads(line))
    refuse_when(
        len(rows) != meta["n_episode_pair_rows_committed"],
        FINDING_CATALOG_FIELD_INVALID,
        f"episode row count {len(rows)} != header {meta['n_episode_pair_rows_committed']}",
    )
    return meta, tuple(rows)


def catalog_episode_mill_check(directory: Path | None = None) -> Mapping[str, Any]:
    meta, rows = load_episode_mill_catalog(directory)
    refuse_when(
        meta["n_episode_pair_rows_extracted"] != meta["n_episode_pair_rows_committed"],
        FINDING_CATALOG_FIELD_INVALID,
        "ssl hopper episode slice is rank-1 full extract",
    )
    slugs: set[str] = set()
    for row in rows:
        refuse_when(row.get("shape") != EPISODE_SHAPE, FINDING_CATALOG_FIELD_INVALID, "episode row shape drift")
        for side in ("ok", "bad"):
            slug = row[side]["slug"]
            refuse_when(slug in slugs, FINDING_CATALOG_FIELD_INVALID, f"duplicate slug {slug!r}")
            slugs.add(slug)
    return meta


bind_import_twin(__name__)
