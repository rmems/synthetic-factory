#!/usr/bin/env python3
"""In-process git index and gitignore evidence for mill-script inventory.

The evidence is split by responsibility: ``mill_script_inventory_gitdir``
locates the git directory and reads its config, ``mill_script_inventory_gitglob``
translates one gitignore glob, ``mill_script_inventory_gitignore`` applies the
nested ignore rules, and ``mill_script_inventory_gitindex`` reads the index.
This module keeps the inventory's entry points and the two git commands it
emulates in process.
"""

from __future__ import annotations

import sys
from collections.abc import Sequence
from pathlib import Path

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("mill_script_inventory_git")
    from . import mill_script_inventory_gitdir as _gitdir
    from . import mill_script_inventory_gitignore as _gitignore
    from . import mill_script_inventory_gitindex as _gitindex
    from . import mill_script_inventory_schema as _schema
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "mill_script_inventory_git"
    )
    import mill_script_inventory_gitdir as _gitdir
    import mill_script_inventory_gitignore as _gitignore
    import mill_script_inventory_gitindex as _gitindex
    import mill_script_inventory_schema as _schema

MillScriptInventoryError = _schema.MillScriptInventoryError
_GIT_REQUIRED = _gitdir._GIT_REQUIRED
GITIGNORE_NAME = _gitignore.GITIGNORE_NAME
REPO_ROOT = Path(__file__).resolve().parents[1]

_git_dir = _gitdir._git_dir
gitignore_matches = _gitignore.gitignore_matches
_ignored_paths = _gitignore._ignored_paths
_parse_git_index = _gitindex._parse_git_index
_merge_split_paths = _gitindex._merge_split_paths
_ewah_decode = _gitindex._ewah_decode
_read_git_index = _gitindex._read_git_index


def _git_available(repo: Path | None = None) -> bool:
    try:
        return (_git_dir(Path(repo or REPO_ROOT)) / "index").is_file()
    except MillScriptInventoryError:
        return False


def _require_git(repo: Path | None = None) -> None:
    if not _git_available(repo):
        raise MillScriptInventoryError(_GIT_REQUIRED)


def _ls_files_output(repo: Path) -> bytes:
    return "\0".join(tracked_paths(repo)).encode() + b"\0"


def _check_ignore_output(repo: Path, payload: bytes | None) -> bytes:
    paths = tuple(filter(None, (payload or b"").decode().split("\0")))
    matches = gitignore_matches(repo, paths)
    chunks: list[str] = []
    for path in paths:
        hit = matches.get(path)
        if hit is None:
            continue
        chunks.extend((*hit, path))
    if not chunks:
        return b""
    return ("\0".join(chunks) + "\0").encode()


def _git_output(repo: Path, arguments: Sequence[str], payload: bytes | None = None) -> bytes:
    command = tuple(arguments)
    if command == ("ls-files", "-z"):
        return _ls_files_output(repo)
    if command == ("check-ignore", "--no-index", "-z", "-v", "--stdin"):
        return _check_ignore_output(repo, payload)
    raise MillScriptInventoryError("inventory git helper accepts only ls-files or check-ignore")


def tracked_paths(root: Path | None = None) -> tuple[str, ...]:
    """Return git-tracked paths for inventory completeness."""

    repo = root or REPO_ROOT
    _require_git(repo)
    return _read_git_index(repo)


if __package__:
    _expose_package_sibling(__name__)
