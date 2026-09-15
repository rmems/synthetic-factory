#!/usr/bin/env python3
"""Reviewed mill-script inventory: classify, guard, and quality-scope policy.

``config/MILL-SCRIPT-INVENTORY.json`` is loaded at import (policy is data).
Every tracked path matching the inventory's ``match_patterns`` must already
be classified. Historical leftover generators stay on
``origin/legacy-mill-lane``; production mill modules stay in quality scope.

Usage: python3 pipelines/mill_script_inventory.py [--check]
"""

from __future__ import annotations

import argparse
import ast
import fnmatch
import json
import re
import subprocess
import sys
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("mill_script_inventory")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "mill_script_inventory"
    )


SCHEMA_VERSION = "mill-script-inventory-v1"
CLASSIFICATIONS = frozenset(
    {
        "production",
        "retained_historical_generator",
        "removable_duplicate",
    }
)
QUALITY_SCOPES = frozenset({"production", "archived"})
MAX_INVENTORY_BYTES = 256_000
IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
PRODUCTION_ROOTS = ("pipelines/", "scripts/", ".claude/skills/")

REPO_ROOT = Path(__file__).resolve().parents[1]
INVENTORY_PATH = REPO_ROOT / "config" / "MILL-SCRIPT-INVENTORY.json"


class MillScriptInventoryError(Exception):
    """Fail-closed inventory or guard refusal."""


def _reject_duplicate_keys(pairs: list[tuple[object, object]]) -> dict:
    seen: dict[object, object] = {}
    for key, value in pairs:
        if key in seen:
            raise MillScriptInventoryError(f"duplicate key {key!r}")
        seen[key] = value
    return seen


def _require_mapping(value: object, where: str) -> dict:
    if not isinstance(value, dict):
        raise MillScriptInventoryError(f"{where} must be an object")
    return value


def _require_str(value: object, where: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MillScriptInventoryError(f"{where} must be a nonempty string")
    return value


def _require_str_list(value: object, where: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise MillScriptInventoryError(f"{where} must be a nonempty array of strings")
    return tuple(_require_str(item, f"{where}[{index}]") for index, item in enumerate(value))


def _require_path(value: object, where: str) -> str:
    path = _require_str(value, where).replace("\\", "/")
    if path.startswith("/") or path.startswith("../") or "/../" in path or path == "..":
        raise MillScriptInventoryError(f"{where} must be a repo-relative path")
    return path


def _validate_script(entry: object, index: int) -> dict:
    row = _require_mapping(entry, f"scripts[{index}]")
    classification = _require_str(row.get("classification"), f"scripts[{index}].classification")
    if classification not in CLASSIFICATIONS:
        raise MillScriptInventoryError(
            f"scripts[{index}].classification must be one of {sorted(CLASSIFICATIONS)}"
        )
    scope = _require_str(row.get("quality_scope"), f"scripts[{index}].quality_scope")
    if scope not in QUALITY_SCOPES:
        raise MillScriptInventoryError(
            f"scripts[{index}].quality_scope must be one of {sorted(QUALITY_SCOPES)}"
        )
    if classification == "production" and scope != "production":
        raise MillScriptInventoryError(
            f"scripts[{index}]: production classification requires quality_scope production"
        )
    if classification != "production" and scope != "archived":
        raise MillScriptInventoryError(
            f"scripts[{index}]: archived classifications require quality_scope archived"
        )
    replacement = row.get("canonical_replacement")
    if replacement is not None:
        _require_str(replacement, f"scripts[{index}].canonical_replacement")
    return {
        "path": _require_path(row.get("path"), f"scripts[{index}].path"),
        "classification": classification,
        "owner": _require_str(row.get("owner"), f"scripts[{index}].owner"),
        "status": _require_str(row.get("status"), f"scripts[{index}].status"),
        "canonical_replacement": replacement,
        "quality_scope": scope,
        "provenance": _require_str(row.get("provenance"), f"scripts[{index}].provenance"),
    }


def _validate_family(entry: object, index: int) -> dict:
    row = _require_mapping(entry, f"mill_families[{index}]")
    classification = _require_str(
        row.get("classification"), f"mill_families[{index}].classification"
    )
    if classification not in CLASSIFICATIONS:
        raise MillScriptInventoryError(
            f"mill_families[{index}].classification must be one of {sorted(CLASSIFICATIONS)}"
        )
    return {
        "family": _require_str(row.get("family"), f"mill_families[{index}].family"),
        "owner": _require_str(row.get("owner"), f"mill_families[{index}].owner"),
        "classification": classification,
        "provenance": _require_str(row.get("provenance"), f"mill_families[{index}].provenance"),
    }


def _validate_historical_policy(value: object) -> dict:
    row = _require_mapping(value, "historical_generator_policy")
    classification = _require_str(
        row.get("classification"), "historical_generator_policy.classification"
    )
    if classification != "retained_historical_generator":
        raise MillScriptInventoryError(
            "historical_generator_policy.classification must be retained_historical_generator"
        )
    scope = _require_str(row.get("quality_scope"), "historical_generator_policy.quality_scope")
    if scope != "archived":
        raise MillScriptInventoryError(
            "historical_generator_policy.quality_scope must be archived"
        )
    return {
        "classification": classification,
        "status": _require_str(row.get("status"), "historical_generator_policy.status"),
        "quality_scope": scope,
        "canonical_owner": _require_str(
            row.get("canonical_owner"), "historical_generator_policy.canonical_owner"
        ),
        "canonical_replacement": _require_str(
            row.get("canonical_replacement"),
            "historical_generator_policy.canonical_replacement",
        ),
        "provenance_ref": _require_str(
            row.get("provenance_ref"), "historical_generator_policy.provenance_ref"
        ),
        "location": _require_str(row.get("location"), "historical_generator_policy.location"),
        "example_paths": _require_str_list(
            row.get("example_paths"), "historical_generator_policy.example_paths"
        ),
        "notes": _require_str(row.get("notes"), "historical_generator_policy.notes"),
    }


def _validate_quality_policy(value: object) -> dict:
    row = _require_mapping(value, "quality_policy")
    return {
        "historical_ref": _require_str(row.get("historical_ref"), "quality_policy.historical_ref"),
        "gitignore_patterns": _require_str_list(
            row.get("gitignore_patterns"), "quality_policy.gitignore_patterns"
        ),
        "archived_exclude_patterns": _require_str_list(
            row.get("archived_exclude_patterns"),
            "quality_policy.archived_exclude_patterns",
        ),
        "forbidden_blanket_patterns": _require_str_list(
            row.get("forbidden_blanket_patterns"),
            "quality_policy.forbidden_blanket_patterns",
        ),
    }


def load_inventory_bytes(payload: bytes, *, where: str = "mill-script inventory") -> dict:
    """Strictly decode and validate mill-script inventory bytes."""

    if not isinstance(payload, bytes):
        raise MillScriptInventoryError(f"{where} must be bytes")
    if len(payload) > MAX_INVENTORY_BYTES:
        raise MillScriptInventoryError(f"{where} exceeds {MAX_INVENTORY_BYTES} bytes")
    try:
        document = json.loads(payload.decode("utf-8"), object_pairs_hook=_reject_duplicate_keys)
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        raise MillScriptInventoryError(f"{where}: invalid JSON: {exc}") from exc
    mapping = _require_mapping(document, where)
    version = _require_str(mapping.get("schema_version"), "schema_version")
    if version != SCHEMA_VERSION:
        raise MillScriptInventoryError(f"schema_version must be {SCHEMA_VERSION}")
    scripts = mapping.get("scripts")
    if not isinstance(scripts, list) or not scripts:
        raise MillScriptInventoryError("scripts must be a nonempty array")
    families = mapping.get("mill_families")
    if not isinstance(families, list) or not families:
        raise MillScriptInventoryError("mill_families must be a nonempty array")
    validated_scripts = tuple(_validate_script(entry, index) for index, entry in enumerate(scripts))
    paths = [row["path"] for row in validated_scripts]
    if len(paths) != len(set(paths)):
        raise MillScriptInventoryError("scripts paths must be unique")
    return {
        "schema_version": version,
        "notes": _require_str(mapping.get("notes"), "notes"),
        "match_patterns": _require_str_list(mapping.get("match_patterns"), "match_patterns"),
        "scripts": validated_scripts,
        "historical_generator_policy": _validate_historical_policy(
            mapping.get("historical_generator_policy")
        ),
        "mill_families": tuple(
            _validate_family(entry, index) for index, entry in enumerate(families)
        ),
        "quality_policy": _validate_quality_policy(mapping.get("quality_policy")),
    }


def load_inventory(path: Path | None = None) -> dict:
    """Load and validate the committed mill-script inventory."""

    target = path or INVENTORY_PATH
    return load_inventory_bytes(target.read_bytes(), where=str(target))


def path_matches(path: str, pattern: str) -> bool:
    """Return whether a repo-relative path matches one inventory glob."""

    normalized = path.replace("\\", "/")
    name = normalized.rsplit("/", 1)[-1]
    return fnmatch.fnmatch(normalized, pattern) or fnmatch.fnmatch(name, pattern)


def matching_paths(paths: Iterable[str], patterns: Sequence[str]) -> tuple[str, ...]:
    """Return sorted unique paths that match any mill-script pattern."""

    hits = [
        path.replace("\\", "/")
        for path in paths
        if any(path_matches(path, pattern) for pattern in patterns)
    ]
    return tuple(sorted(set(hits)))


def tracked_paths(root: Path | None = None) -> tuple[str, ...]:
    """Return git-tracked paths for inventory completeness."""

    repo = root or REPO_ROOT
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=repo,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return tuple(item.replace("\\", "/") for item in result.stdout.decode().split("\0") if item)


def script_index(inventory: Mapping[str, object]) -> dict[str, dict]:
    """Map inventory script path to the classified row."""

    rows = inventory["scripts"]
    if not isinstance(rows, (list, tuple)):
        raise MillScriptInventoryError("scripts must be an array")
    return {row["path"]: row for row in rows}


def unclassified_paths(tracked: Sequence[str], inventory: Mapping[str, object]) -> tuple[str, ...]:
    """Return matching tracked paths missing from the inventory."""

    patterns = inventory["match_patterns"]
    if not isinstance(patterns, (list, tuple)):
        raise MillScriptInventoryError("match_patterns must be an array")
    classified = script_index(inventory)
    return tuple(
        path for path in matching_paths(tracked, patterns) if path not in classified
    )


def production_script_paths(inventory: Mapping[str, object]) -> frozenset[str]:
    """Return inventory paths that remain in production quality scope."""

    return frozenset(
        row["path"]
        for row in script_index(inventory).values()
        if row["quality_scope"] == "production"
    )


def archived_script_paths(inventory: Mapping[str, object]) -> frozenset[str]:
    """Return inventory paths excluded from production quality scope."""

    return frozenset(
        row["path"]
        for row in script_index(inventory).values()
        if row["quality_scope"] == "archived"
    )


def _stem_identifier(path: str) -> str | None:
    name = path.replace("\\", "/").rsplit("/", 1)[-1]
    if not name.endswith(".py"):
        return None
    stem = name[:-3]
    if IDENTIFIER_RE.fullmatch(stem):
        return stem
    return None


def archived_module_names(inventory: Mapping[str, object]) -> frozenset[str]:
    """Importable module names that would reach archived mill generators."""

    names = {name for path in archived_script_paths(inventory) if (name := _stem_identifier(path))}
    policy = inventory["historical_generator_policy"]
    if not isinstance(policy, Mapping):
        raise MillScriptInventoryError("historical_generator_policy must be an object")
    for path in policy["example_paths"]:
        name = _stem_identifier(str(path))
        if name is not None:
            names.add(name)
    return frozenset(names)


def imported_module_names(source: str) -> frozenset[str]:
    """Return every imported module name, including dotted forms."""

    tree = ast.parse(source)
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name)
                names.add(alias.name.split(".", 1)[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
            names.add(node.module.split(".", 1)[0])
    return frozenset(names)


def archived_import_hits(source: str, archived_names: Iterable[str]) -> tuple[str, ...]:
    """Return archived mill-module names imported by one source file."""

    imported = imported_module_names(source)
    blocked = frozenset(archived_names)
    hits = set(imported & blocked)
    if "experiments" in imported:
        hits.add("experiments")
    return tuple(sorted(hits))


def production_python_paths(tracked: Sequence[str]) -> tuple[str, ...]:
    """Tracked Python files under production roots."""

    return tuple(
        path
        for path in tracked
        if path.endswith(".py") and path.startswith(PRODUCTION_ROOTS)
    )


def patterns_hitting(patterns: Sequence[str], paths: Iterable[str]) -> tuple[tuple[str, str], ...]:
    """Return (pattern, path) pairs where a quality glob hits a path."""

    return tuple(
        (pattern, path)
        for pattern in patterns
        for path in paths
        if path_matches(path, pattern)
    )


def gitignore_lines(root: Path | None = None) -> tuple[str, ...]:
    """Return non-comment gitignore rules from the repository root."""

    text = (root or REPO_ROOT).joinpath(".gitignore").read_text(encoding="utf-8")
    rules = []
    for raw in text.splitlines():
        stripped = raw.strip()
        if stripped and not stripped.startswith("#"):
            rules.append(stripped)
    return tuple(rules)


def qlty_exclude_patterns(root: Path | None = None) -> tuple[str, ...]:
    """Return exclude_patterns strings from ``.qlty/qlty.toml``."""

    text = (root or REPO_ROOT).joinpath(".qlty", "qlty.toml").read_text(encoding="utf-8")
    block = text.split("exclude_patterns = [", 1)[1].split("]", 1)[0]
    return tuple(
        line.split("\"", 2)[1]
        for line in block.splitlines()
        if "\"" in line
    )


def check_inventory(
    root: Path | None = None,
    inventory: Mapping[str, object] | None = None,
    tracked: Sequence[str] | None = None,
) -> dict:
    """Return a machine-readable completeness and quality-scope report."""

    repo = root or REPO_ROOT
    loaded = dict(inventory) if inventory is not None else load_inventory()
    listed = tracked if tracked is not None else tracked_paths(repo)
    unclassified = unclassified_paths(listed, loaded)
    production = production_script_paths(loaded)
    policy = loaded["quality_policy"]
    if not isinstance(policy, Mapping):
        raise MillScriptInventoryError("quality_policy must be an object")
    gitignore_hits = patterns_hitting(policy["gitignore_patterns"], production)
    qlty_hits = patterns_hitting(policy["archived_exclude_patterns"], production)
    missing_gitignore = tuple(
        pattern
        for pattern in policy["gitignore_patterns"]
        if pattern not in gitignore_lines(repo)
    )
    missing_qlty = tuple(
        pattern
        for pattern in policy["archived_exclude_patterns"]
        if pattern not in qlty_exclude_patterns(repo)
    )
    forbidden_present = tuple(
        pattern
        for pattern in policy["forbidden_blanket_patterns"]
        if pattern in gitignore_lines(repo)
    )
    return {
        "unclassified": unclassified,
        "gitignore_hits_on_production": gitignore_hits,
        "qlty_hits_on_production": qlty_hits,
        "missing_gitignore_patterns": missing_gitignore,
        "missing_qlty_patterns": missing_qlty,
        "forbidden_blanket_patterns_present": forbidden_present,
        "ok": not (
            unclassified
            or gitignore_hits
            or qlty_hits
            or missing_gitignore
            or missing_qlty
            or forbidden_present
        ),
    }


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail closed when a matching tracked script is unclassified",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Print the inventory or fail closed on an unclassified mill script."""

    args = _parse_args(argv)
    report = check_inventory()
    json.dump(report, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    if args.check and not report["ok"]:
        return 1
    return 0


INVENTORY_BYTES = INVENTORY_PATH.read_bytes()
INVENTORY = load_inventory_bytes(INVENTORY_BYTES)


if __package__:
    _expose_package_sibling(__name__)


if __name__ == "__main__":
    raise SystemExit(main())
