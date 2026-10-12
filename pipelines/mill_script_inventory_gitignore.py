"""Load nested ``.gitignore`` rules and apply Git's last-match-wins evaluation."""

from __future__ import annotations

import re
import sys
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("mill_script_inventory_gitignore")
    from . import mill_script_inventory_gitdir as _gitdir
    from . import mill_script_inventory_gitglob as _gitglob
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "mill_script_inventory_gitignore"
    )
    import mill_script_inventory_gitdir as _gitdir
    import mill_script_inventory_gitglob as _gitglob

GITIGNORE_NAME = ".gitignore"
_core_ignore_case = _gitdir._core_ignore_case
_wildcard_regex = _gitglob._wildcard_regex


def _collect_ignore_files(root: Path, paths: Iterable[str]) -> tuple[tuple[str, Path], ...]:
    files: dict[str, Path] = {"": Path(root) / GITIGNORE_NAME}
    for candidate in paths:
        relative = Path(candidate.replace("\\", "/")).parent
        while relative != Path("."):
            files[f"{relative.as_posix()}/"] = Path(root) / relative / GITIGNORE_NAME
            relative = relative.parent
    return tuple((scope, path) for scope, path in sorted(files.items()) if path.is_file())


def _parse_ignore_file(
    path: Path, source: str, flags: int = 0
) -> tuple[tuple[str, str, str, re.Pattern[str]], ...]:
    rules: list[tuple[str, str, str, re.Pattern[str]]] = []
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        pattern = line.removeprefix("!")
        rules.append((source, str(number), line, _wildcard_regex(pattern, flags)))
    return tuple(rules)


def _scope_relative(path: str, scope: str, flags: int = 0) -> str | None:
    if not scope:
        return path
    haystack, needle = path, scope
    if flags & re.IGNORECASE:
        haystack, needle = path.lower(), scope.lower()
    if haystack.startswith(needle):
        return path[len(scope):]
    return None


def _load_ignore_rules(
    root: Path, paths: Iterable[str]
) -> tuple[tuple[str, str, str, str, re.Pattern[str]], ...]:
    flags = re.IGNORECASE if _core_ignore_case(root) else 0
    rules: list[tuple[str, str, str, str, re.Pattern[str]]] = []
    for scope, path in _collect_ignore_files(root, paths):
        parsed = _parse_ignore_file(path, f"{scope}{GITIGNORE_NAME}", flags)
        rules.extend((scope, source, line, original, regex) for source, line, original, regex in parsed)
    return tuple(rules)


def _path_prefixes(path: str) -> tuple[str, ...]:
    parts = path.split("/")
    return tuple("/".join(parts[:index]) for index in range(1, len(parts) + 1))


def _matching_prefix(
    prefixes: Sequence[str], scope: str, regex: re.Pattern[str], directory_only: bool
) -> str | None:
    keys = prefixes[:-1] if directory_only else prefixes
    for prefix in keys:
        relative = _scope_relative(prefix, scope, regex.flags)
        if relative is not None and regex.search(relative):
            return prefix
    return None


def _parent_excluded(path: str, excluded: Sequence[str]) -> bool:
    return any(path == folder or path.startswith(f"{folder}/") for folder in excluded)


def _apply_ignore_hit(
    state: tuple[tuple[str, str, str] | None, tuple[str, ...], str],
    hit: str | None,
    rule: tuple[str, str, str],
) -> tuple[tuple[str, str, str] | None, tuple[str, ...], str]:
    if hit is None:
        return state
    excluded, normalized = state[1], state[2]
    source, line, original = rule
    if not original.startswith("!"):
        extra = (hit,) if hit != normalized else ()
        return (source, line, original), excluded + extra, normalized
    if _parent_excluded(normalized, excluded):
        return state
    return (source, line, original), excluded, normalized


def _last_ignore_hit(
    path: str,
    rules: Sequence[tuple[str, str, str, str, re.Pattern[str]]],
) -> tuple[str, str, str] | None:
    normalized = path.replace("\\", "/")
    prefixes = _path_prefixes(normalized)
    state: tuple[tuple[str, str, str] | None, tuple[str, ...], str] = (None, (), normalized)
    for scope, source, line, original, regex in rules:
        hit = _matching_prefix(prefixes, scope, regex, original.removeprefix("!").endswith("/"))
        state = _apply_ignore_hit(state, hit, (source, line, original))
    return state[0]


def gitignore_matches(root: Path, paths: Iterable[str]) -> dict[str, tuple[str, str, str]]:
    """Use Git's effective ignore rules, including nested, negated, and ancestor rules."""

    candidates = tuple(paths)
    rules = _load_ignore_rules(root, candidates)
    matches: dict[str, tuple[str, str, str]] = {}
    for candidate in candidates:
        hit = _last_ignore_hit(candidate, rules)
        if hit is not None:
            matches[candidate] = hit
    return matches


def _ignored_paths(matches: Mapping[str, tuple[str, str, str]]) -> frozenset[str]:
    return frozenset(
        path for path, (_source, _line, rule) in matches.items() if not rule.startswith("!")
    )


if __package__:
    _expose_package_sibling(__name__)
