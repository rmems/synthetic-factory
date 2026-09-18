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
import os
import sys
import tempfile
import tomllib
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path, PurePosixPath

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("mill_script_inventory")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "mill_script_inventory"
    )


if __package__:
    from . import mill_script_inventory_schema as _schema
    from .mill_script_inventory_families import (
        expected_family_owners, family_owner_findings, production_family_paths,
    )
else:
    import mill_script_inventory_schema as _schema
    from mill_script_inventory_families import (
        expected_family_owners, family_owner_findings, production_family_paths,
    )

SCHEMA_VERSION = _schema.SCHEMA_VERSION
CLASSIFICATIONS = _schema.CLASSIFICATIONS
QUALITY_SCOPES = _schema.QUALITY_SCOPES
MAX_INVENTORY_BYTES = _schema.MAX_INVENTORY_BYTES
MillScriptInventoryError = _schema.MillScriptInventoryError
load_inventory_bytes = _schema.load_inventory_bytes
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


def _git_available() -> bool:
    return Path("/usr/bin/git").is_file()


def _require_git() -> None:
    if not _git_available():
        raise MillScriptInventoryError("git is required for inventory scope checks")


def _git_env(repo: Path) -> dict[str, str]:
    root = str(Path(repo).resolve())
    env = dict(os.environ)
    env["GIT_WORK_TREE"] = root
    env["GIT_DIR"] = str(Path(root) / ".git")
    return env


def _read_pipe(fd: int) -> bytes:
    chunks: list[bytes] = []
    while True:
        chunk = os.read(fd, 65536)
        if not chunk:
            return b"".join(chunks)
        chunks.append(chunk)


def _close_fds(*fds: int) -> None:
    for fd in fds:
        os.close(fd)


def _git_stdio():
    out_r, out_w = os.pipe()
    err_r, err_w = os.pipe()
    actions = [
        (os.POSIX_SPAWN_DUP2, out_w, 1),
        (os.POSIX_SPAWN_DUP2, err_w, 2),
        (os.POSIX_SPAWN_CLOSE, out_r),
        (os.POSIX_SPAWN_CLOSE, err_r),
    ]
    if out_w not in (1, 2):
        actions.append((os.POSIX_SPAWN_CLOSE, out_w))
    if err_w not in (1, 2):
        actions.append((os.POSIX_SPAWN_CLOSE, err_w))
    return out_r, out_w, err_r, err_w, actions


def _finish_git(pid: int, out_r: int, err_r: int, accepted: tuple[int, ...]) -> bytes:
    stderr = b""
    try:
        stdout = _read_pipe(out_r)
        stderr = _read_pipe(err_r)
    finally:
        _close_fds(out_r, err_r)
        _pid, status = os.waitpid(pid, 0)
    returncode = os.waitstatus_to_exitcode(status)
    if returncode not in accepted:
        raise MillScriptInventoryError(stderr.decode(errors="replace"))
    return stdout


def _spawn_git(repo: Path, argv: Sequence[str], extra_actions=()) -> tuple[int, int, int]:
    out_r, out_w, err_r, err_w, actions = _git_stdio()
    actions.extend(extra_actions)
    try:
        pid = os.posix_spawn(
            "/usr/bin/git",
            ["/usr/bin/git", *argv],
            _git_env(repo),
            file_actions=actions,
        )
    except OSError as exc:
        _close_fds(out_r, out_w, err_r, err_w)
        raise MillScriptInventoryError(str(exc)) from exc
    _close_fds(out_w, err_w)
    return pid, out_r, err_r


def _git_ls_files(repo: Path) -> bytes:
    _require_git()
    pid, out_r, err_r = _spawn_git(repo, ("ls-files", "-z"))
    return _finish_git(pid, out_r, err_r, (0,))


def _payload_stdin(payload: bytes) -> tuple[int, str]:
    fd, name = tempfile.mkstemp()
    try:
        os.write(fd, payload)
        os.close(fd)
        fd = -1
        return os.open(name, os.O_RDONLY), name
    except OSError:
        if fd >= 0:
            os.close(fd)
        os.unlink(name)
        raise


def _git_check_ignore(repo: Path, payload: bytes) -> bytes:
    _require_git()
    stdin_fd, name = _payload_stdin(payload)
    extra = [(os.POSIX_SPAWN_DUP2, stdin_fd, 0)]
    if stdin_fd != 0:
        extra.append((os.POSIX_SPAWN_CLOSE, stdin_fd))
    try:
        try:
            pid, out_r, err_r = _spawn_git(repo, ("check-ignore", "--no-index", "-z", "-v", "--stdin"), extra)
        finally:
            os.close(stdin_fd)
        return _finish_git(pid, out_r, err_r, (0, 1))
    finally:
        os.unlink(name)


def _git_output(repo: Path, arguments: Sequence[str], payload: bytes | None = None) -> bytes:
    if tuple(arguments) == ("ls-files", "-z"):
        return _git_ls_files(repo)
    if tuple(arguments) == ("check-ignore", "--no-index", "-z", "-v", "--stdin"):
        return _git_check_ignore(repo, b"" if payload is None else payload)
    raise MillScriptInventoryError("inventory git helper accepts only ls-files or check-ignore")


def tracked_paths(root: Path | None = None) -> tuple[str, ...]:
    """Return git-tracked paths for inventory completeness."""

    payload = _git_ls_files(root or REPO_ROOT)
    return tuple(filter(None, payload.decode().split("\0")))


def gitignore_matches(root: Path, paths: Iterable[str]) -> dict[str, tuple[str, str, str]]:
    """Use Git's effective ignore rules, including negation and ancestor rules."""

    payload = "\0".join(sorted(paths)).encode() + b"\0"
    output = _git_check_ignore(root, payload)
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


def _module_basename(path: str) -> str | None:
    module = PurePosixPath(path)
    if module.suffix != ".py":
        return None
    return module.parent.name if module.stem == "__init__" else module.stem


def historical_paths(inventory: Mapping[str, object]) -> frozenset[str]:
    policy = inventory["historical_generator_policy"]
    return frozenset(policy["archived_paths"]) | archived_script_paths(inventory)


def archived_module_names(inventory: Mapping[str, object]) -> frozenset[str]:
    """Names derived from the full pinned archive, not illustrative examples."""

    paths = historical_paths(inventory)
    stems = frozenset(filter(None, map(_module_basename, paths)))
    qualified = frozenset(filter(None, map(_qualified_module, paths)))
    canonical = {
        row["owner"].removeprefix("pipelines/")
        for row in inventory["mill_families"]
        if row["classification"] == "production"
    }
    return (stems - canonical) | qualified


def _qualified_module(path: str) -> str | None:
    if not path.endswith(".py"):
        return None
    parts = path.removesuffix(".py").split("/")
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _import_targets(node: ast.AST) -> tuple[str, ...]:
    if isinstance(node, ast.Import):
        return tuple(alias.name for alias in node.names)
    if isinstance(node, ast.ImportFrom):
        return _from_import_targets(node)
    return ()


def _from_import_targets(node: ast.ImportFrom) -> tuple[str, ...]:
    names = tuple(alias.name for alias in node.names)
    if node.module is None:
        return names
    return (node.module, *names, *(f"{node.module}.{name}" for name in names))


def _dynamic_import_functions(tree: ast.AST) -> frozenset[str]:
    functions = {"__import__", "builtins.__import__", "importlib.import_module"}
    for node in ast.walk(tree):
        functions.update(_import_function_aliases(node))
    return frozenset(functions)


def _aliased_importlib_names(node: ast.Import) -> tuple[str, ...]:
    modules = {"importlib": "import_module", "builtins": "__import__"}
    return tuple(
        f"{alias.asname or alias.name}.{modules[alias.name]}"
        for alias in node.names
        if alias.name in modules
    )


def _aliased_from_import_names(node: ast.ImportFrom) -> tuple[str, ...]:
    modules = {"importlib": "import_module", "builtins": "__import__"}
    if node.module not in modules:
        return ()
    expected = modules[node.module]
    return tuple(alias.asname or alias.name for alias in node.names if alias.name == expected)


def _import_function_aliases(node: ast.AST) -> tuple[str, ...]:
    if isinstance(node, ast.Import):
        return _aliased_importlib_names(node)
    if isinstance(node, ast.ImportFrom):
        return _aliased_from_import_names(node)
    return ()


def _call_string_argument(node: ast.Call) -> tuple[str, ...]:
    arguments = node.args[:1] or [item.value for item in node.keywords if item.arg == "name"]
    return tuple(
        argument.value
        for argument in arguments
        if isinstance(argument, ast.Constant) and isinstance(argument.value, str)
    )


def _dynamic_import_targets(node: ast.AST, functions: frozenset[str]) -> tuple[str, ...]:
    if not isinstance(node, ast.Call):
        return ()
    if ast.unparse(node.func) not in functions:
        return ()
    return _call_string_argument(node)


def imported_module_names(source: str) -> frozenset[str]:
    """Return every imported module name, including dotted forms."""

    tree = ast.parse(source)
    names = {name for node in ast.walk(tree) for name in _import_targets(node) if name}
    functions = _dynamic_import_functions(tree)
    names.update(target for node in ast.walk(tree) for target in _dynamic_import_targets(node, functions))
    names.update(part for name in tuple(names) for part in name.split("."))
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


def _policy_findings(
    policy: Mapping, gitignore_rules: Sequence[str], qlty_rules: Sequence[str]
) -> dict:
    return {
        "missing_gitignore_patterns": tuple(
            pattern for pattern in policy["gitignore_patterns"] if pattern not in gitignore_rules
        ),
        "missing_qlty_patterns": tuple(
            pattern for pattern in policy["archived_exclude_patterns"] if pattern not in qlty_rules
        ),
        "forbidden_blanket_patterns_present": tuple(
            pattern
            for pattern in policy["forbidden_blanket_patterns"]
            if pattern in gitignore_rules
        ),
    }


def _gitignore_hits(paths: Iterable[str], matches: Mapping[str, tuple[str, str, str]]) -> tuple:
    return tuple((matches[path][2], path) for path in sorted(paths))


def _retained_experiments(tracked: Sequence[str], archived: frozenset[str]) -> frozenset[str]:
    return frozenset(path for path in tracked if path.startswith("experiments/")) - archived


def production_inventory_paths(tracked: Sequence[str]) -> frozenset[str]:
    """Keep the tracked validator and its split runtime modules in quality scope."""
    return frozenset(path for path in tracked if path_matches(path, "pipelines/mill_script_inventory*.py"))


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
    production = (production_script_paths(loaded)
                  | production_family_paths(loaded["mill_families"], listed)
                  | production_inventory_paths(listed))
    policy = loaded["quality_policy"]
    if not isinstance(policy, Mapping):
        raise MillScriptInventoryError("quality_policy must be an object")
    gitignore_rules = gitignore_lines(repo)
    qlty_rules = qlty_exclude_patterns(repo)
    archived = historical_paths(loaded)
    retained = _retained_experiments(listed, archived)
    matches = gitignore_matches(repo, production | archived | retained)
    ignored = _ignored_paths(matches)
    gitignore_hits = _gitignore_hits(production & ignored, matches)
    qlty_hits = patterns_hitting(qlty_rules, production)
    report = {
        "unclassified": unclassified,
        "archive_provenance_mismatch": not _schema.archive_provenance_matches(loaded["historical_generator_policy"]),
        "gitignore_hits_on_production": gitignore_hits,
        "qlty_hits_on_production": qlty_hits,
        "gitignore_hits_on_retained_experiments": _gitignore_hits(retained & ignored, matches),
        "qlty_hits_on_retained_experiments": patterns_hitting(qlty_rules, retained),
        "unmatched_archived_paths": uncovered_paths(loaded["match_patterns"], archived),
        "missing_or_invalid_family_owners": family_owner_findings(
            loaded["mill_families"], expected_family_owners(archived, listed)
        ),
        **_policy_findings(policy, gitignore_rules, qlty_rules),
        "uncovered_gitignore_archived_paths": tuple(sorted(archived - ignored)),
        "uncovered_qlty_archived_paths": uncovered_paths(qlty_rules, archived),
    }
    anomalies = ((production | retained) & ignored) | (archived - ignored)
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
