#!/usr/bin/env python3
"""Git worktree, index, and gitignore evidence for mill-script inventory."""

from __future__ import annotations

import sys
from collections.abc import Sequence
from pathlib import Path

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("mill_script_inventory_git")
    from . import mill_script_inventory_schema as _schema
    from . import mill_script_inventory_ignore as _ignore
    from . import mill_script_inventory_index as _index
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "mill_script_inventory_git"
    )
    import mill_script_inventory_schema as _schema
    import mill_script_inventory_ignore as _ignore
    import mill_script_inventory_index as _index

MillScriptInventoryError = _schema.MillScriptInventoryError
_GIT_REQUIRED = "git is required for inventory scope checks"
GITIGNORE_NAME = _ignore.GITIGNORE_NAME
REPO_ROOT = Path(__file__).resolve().parents[1]
_INDEX_UNPARSEABLE = _index._INDEX_UNPARSEABLE
_INDEX_TRUNCATED = _index._INDEX_TRUNCATED
_parse_git_index = _index._parse_git_index
_merge_split_paths = _index._merge_split_paths
_ewah_decode = _index._ewah_decode
gitignore_matches = _ignore.gitignore_matches
_ignored_paths = _ignore._ignored_paths


def _resolve_gitdir_pointer(marker: Path, raw: str) -> Path:
    gitdir = Path(raw.strip())
    return gitdir if gitdir.is_absolute() else (marker.parent / gitdir).resolve()


def _gitdir_from_gitfile(marker: Path) -> Path | None:
    for line in marker.read_text(encoding="utf-8").splitlines():
        if line.startswith("gitdir:"):
            return _resolve_gitdir_pointer(marker, line.split(":", 1)[1])
    return None


def _git_dir(repo: Path) -> Path:
    marker = Path(repo).resolve() / ".git"
    if marker.is_file():
        found = _gitdir_from_gitfile(marker)
        if found is not None:
            return found
    if marker.is_dir():
        return marker
    raise MillScriptInventoryError(_GIT_REQUIRED)


def _git_available(repo: Path | None = None) -> bool:
    try:
        return (_git_dir(Path(repo or REPO_ROOT)) / "index").is_file()
    except MillScriptInventoryError:
        return False


def _require_git(repo: Path | None = None) -> None:
    if not _git_available(repo):
        raise MillScriptInventoryError(_GIT_REQUIRED)


def _read_git_index(repo: Path) -> tuple[str, ...]:
    return _index.read_index_paths(_git_dir(repo))


def _git_output(repo: Path, arguments: Sequence[str], payload: bytes | None = None) -> bytes:
    if tuple(arguments) == ("ls-files", "-z"):
        return "\0".join(tracked_paths(repo)).encode() + b"\0"
    if tuple(arguments) == ("check-ignore", "--no-index", "-z", "-v", "--stdin"):
        paths = tuple(filter(None, (payload or b"").decode().split("\0")))
        matches = gitignore_matches(repo, paths)
        chunks = [
            part
            for path in paths
            if path in matches
            for part in (*matches[path], path)
        ]
        return ("\0".join(chunks) + "\0").encode() if chunks else b""
    raise MillScriptInventoryError("inventory git helper accepts only ls-files or check-ignore")


def tracked_paths(root: Path | None = None) -> tuple[str, ...]:
    """Return git-tracked paths for inventory completeness."""

    repo = root or REPO_ROOT
    _require_git(repo)
    return _read_git_index(repo)


if __package__:
    _expose_package_sibling(__name__)
