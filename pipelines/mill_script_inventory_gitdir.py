"""Locate a repository's git directory and read its ``core.ignorecase`` setting."""

from __future__ import annotations

import sys
from pathlib import Path

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("mill_script_inventory_gitdir")
    from . import mill_script_inventory_schema as _schema
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "mill_script_inventory_gitdir"
    )
    import mill_script_inventory_schema as _schema

MillScriptInventoryError = _schema.MillScriptInventoryError
GIT_REQUIRED = "git is required for inventory scope checks"


def _resolve_gitdir_pointer(marker: Path, raw: str) -> Path:
    gitdir = Path(raw.strip())
    return gitdir if gitdir.is_absolute() else (marker.parent / gitdir).resolve()


def _gitdir_from_gitfile(marker: Path) -> Path | None:
    for line in marker.read_text(encoding="utf-8").splitlines():
        if line.startswith("gitdir:"):
            return _resolve_gitdir_pointer(marker, line.split(":", 1)[1])
    return None


def git_dir(repo: Path) -> Path:
    marker = Path(repo).resolve() / ".git"
    if marker.is_file():
        found = _gitdir_from_gitfile(marker)
        if found is not None:
            return found
    if marker.is_dir():
        return marker
    raise MillScriptInventoryError(GIT_REQUIRED)


def _truthy(value: str) -> bool:
    return value.lower() in {"true", "yes", "on", "1"}


def _git_config_file(gitdir: Path) -> Path:
    marker = gitdir / "commondir"
    if not marker.is_file():
        return gitdir / "config"
    raw = marker.read_text(encoding="utf-8").splitlines()[0].strip()
    common = Path(raw)
    if not common.is_absolute():
        common = (gitdir / common).resolve()
    return common / "config"


def _config_pairs(path: Path) -> tuple[tuple[str, str], ...]:
    if not path.is_file():
        return ()
    pairs: list[tuple[str, str]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].split(";", 1)[0].strip()
        if "=" in line:
            key, value = line.split("=", 1)
            pairs.append((key.strip().lower(), value.strip()))
    return tuple(pairs)


def core_ignore_case(root: Path) -> bool:
    try:
        pairs = _config_pairs(_git_config_file(git_dir(root)))
    except MillScriptInventoryError:
        return False
    return any(key == "ignorecase" and _truthy(value) for key, value in pairs)


if __package__:
    _expose_package_sibling(__name__)
