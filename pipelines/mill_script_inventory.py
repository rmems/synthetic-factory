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
import shutil
import subprocess
import sys
import tomllib
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("mill_script_inventory")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "mill_script_inventory"
    )


if __package__:
    from . import mill_script_inventory_schema as _schema
else:
    import mill_script_inventory_schema as _schema

SCHEMA_VERSION = _schema.SCHEMA_VERSION
CLASSIFICATIONS = _schema.CLASSIFICATIONS
QUALITY_SCOPES = _schema.QUALITY_SCOPES
MAX_INVENTORY_BYTES = _schema.MAX_INVENTORY_BYTES
MillScriptInventoryError = _schema.MillScriptInventoryError
load_inventory_bytes = _schema.load_inventory_bytes
IDENTIFIER_RE = re.compile(r"^[A-Za-z_]\w*$", re.ASCII)
PRODUCTION_ROOTS = ("pipelines/", "scripts/", ".claude/skills/")
REPO_ROOT = Path(__file__).resolve().parents[1]
INVENTORY_PATH = REPO_ROOT / "config" / "MILL-SCRIPT-INVENTORY.json"


def load_inventory(path: Path | None = None) -> dict:
    """Load and validate the committed mill-script inventory."""

    target = path or INVENTORY_PATH
    return load_inventory_bytes(target.read_bytes(), where=str(target))


def path_matches(path: str, pattern: str) -> bool:
    """Return whether a repo-relative path matches one inventory glob."""

    normalized = path.replace("\\", "/")
    anchored = pattern.startswith("/")
    pattern = pattern.removeprefix("/")
    if pattern.endswith("/"):
        pattern += "**"
    name = normalized.rsplit("/", 1)[-1]
    if anchored or "/" in pattern:
        return fnmatch.fnmatch(normalized, pattern)
    return fnmatch.fnmatch(name, pattern)


def matching_paths(paths: Iterable[str], patterns: Sequence[str]) -> tuple[str, ...]:
    """Return sorted unique paths that match any mill-script pattern."""

    hits = [
        path.replace("\\", "/")
        for path in paths
        if any(path_matches(path, pattern) for pattern in patterns)
    ]
    return tuple(sorted(set(hits)))


def _git_output(repo: Path, arguments: Sequence[str], payload: bytes | None = None) -> bytes:
    executable = shutil.which("git")
    if executable is None:
        raise MillScriptInventoryError("git is required for inventory scope checks")
    result = subprocess.run(
        [executable, *arguments],
        cwd=repo,
        input=payload,
        capture_output=True,
        check=False,
    )
    accepted = {"ls-files": (0,), "check-ignore": (0, 1)}[arguments[0]]
    if result.returncode not in accepted:
        raise MillScriptInventoryError(result.stderr.decode(errors="replace"))
    return result.stdout


def tracked_paths(root: Path | None = None) -> tuple[str, ...]:
    """Return git-tracked paths for inventory completeness."""

    payload = _git_output(root or REPO_ROOT, ["ls-files", "-z"])
    return tuple(filter(None, payload.decode().split("\0")))


def gitignore_matches(root: Path, paths: Iterable[str]) -> dict[str, tuple[str, str, str]]:
    """Use Git's effective ignore rules, including negation and ancestor rules."""

    payload = "\0".join(sorted(paths)).encode() + b"\0"
    output = _git_output(root, ["check-ignore", "--no-index", "-z", "-v", "--stdin"], payload)
    fields = output.decode().split("\0")[:-1]
    return {
        fields[i + 3]: (fields[i], fields[i + 1], fields[i + 2]) for i in range(0, len(fields), 4)
    }


def _ignored_paths(matches: Mapping[str, tuple[str, str, str]]) -> frozenset[str]:
    return frozenset(
        path for path, (_source, _line, rule) in matches.items() if not rule.startswith("!")
    )


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
    return tuple(path for path in matching_paths(tracked, patterns) if path not in classified)


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


def historical_paths(inventory: Mapping[str, object]) -> frozenset[str]:
    policy = inventory["historical_generator_policy"]
    return frozenset(policy["archived_paths"]) | archived_script_paths(inventory)


def archived_module_names(inventory: Mapping[str, object]) -> frozenset[str]:
    """Names derived from the full pinned archive, not illustrative examples."""

    return frozenset(filter(None, map(_stem_identifier, historical_paths(inventory))))


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
        path for path in tracked if path.endswith(".py") and path.startswith(PRODUCTION_ROOTS)
    )


def patterns_hitting(patterns: Sequence[str], paths: Iterable[str]) -> tuple[tuple[str, str], ...]:
    """Return (pattern, path) pairs where a quality glob hits a path."""

    return tuple(
        (pattern, path) for pattern in patterns for path in paths if path_matches(path, pattern)
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

    path = (root or REPO_ROOT) / ".qlty" / "qlty.toml"
    document = tomllib.loads(path.read_text(encoding="utf-8"))
    patterns = document.get("exclude_patterns", [])
    if not isinstance(patterns, list):
        raise MillScriptInventoryError("Qlty exclude_patterns must be an array")
    return tuple(_schema._require_str(pattern, "exclude_patterns") for pattern in patterns)


def _gitignore_evidence(
    anomalies: Iterable[str], matches: Mapping[str, tuple[str, str, str]]
) -> tuple[tuple[str, ...], ...]:
    return tuple((path, *matches[path]) for path in sorted(anomalies) if path in matches)


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
    gitignore_rules = gitignore_lines(repo)
    qlty_rules = qlty_exclude_patterns(repo)
    archived = historical_paths(loaded)
    matches = gitignore_matches(repo, production | archived)
    ignored = _ignored_paths(matches)
    gitignore_hits = tuple((matches[path][2], path) for path in sorted(production & ignored))
    qlty_hits = patterns_hitting(qlty_rules, production)
    missing_gitignore = tuple(
        pattern for pattern in policy["gitignore_patterns"] if pattern not in gitignore_rules
    )
    missing_qlty = tuple(
        pattern for pattern in policy["archived_exclude_patterns"] if pattern not in qlty_rules
    )
    forbidden_present = tuple(
        pattern for pattern in policy["forbidden_blanket_patterns"] if pattern in gitignore_rules
    )
    report = {
        "unclassified": unclassified,
        "gitignore_hits_on_production": gitignore_hits,
        "qlty_hits_on_production": qlty_hits,
        "missing_gitignore_patterns": missing_gitignore,
        "missing_qlty_patterns": missing_qlty,
        "forbidden_blanket_patterns_present": forbidden_present,
        "uncovered_gitignore_archived_paths": tuple(sorted(archived - ignored)),
        "uncovered_qlty_archived_paths": uncovered_paths(qlty_rules, archived),
    }
    anomalies = (production & ignored) | (archived - ignored)
    evidence = _gitignore_evidence(anomalies, matches)
    return {**report, "ok": not any(report.values()), "gitignore_rule_evidence": evidence}


def uncovered_paths(patterns: Sequence[str], paths: Iterable[str]) -> tuple[str, ...]:
    covered = {path for _pattern, path in patterns_hitting(patterns, paths)}
    return tuple(sorted(set(paths) - covered))


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
