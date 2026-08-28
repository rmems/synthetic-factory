"""Refuse writes that name or alias the repository's immutable raw tree."""

from __future__ import annotations

import os
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAW_OUTPUT_ROOT = REPOSITORY_ROOT / "outputs" / "raw"


def _stat_identity(path: Path) -> tuple[int, int] | None:
    try:
        state = path.stat()
    except OSError:
        return None
    return state.st_dev, state.st_ino


def _ancestor_identities(path: Path) -> set[tuple[int, int]]:
    """Device/inode identities of ``path`` and existing ancestors."""

    identities: set[tuple[int, int]] = set()
    current = Path(os.path.abspath(path))
    seen: set[Path] = set()
    while current not in seen:
        seen.add(current)
        identity = _stat_identity(current)
        if identity is not None:
            identities.add(identity)
        parent = current.parent
        if parent == current:
            break
        current = parent
    return identities


def _has_raw_tree_components(path: Path) -> bool:
    parts = path.parts
    return any(
        parts[index : index + 2] == ("outputs", "raw")
        for index in range(len(parts) - 1)
    )


def _names_raw_tree(path: Path, raw_root: Path) -> bool:
    lexical_path = Path(os.path.abspath(path))
    resolved_path = path.resolve(strict=False)
    if _has_raw_tree_components(lexical_path) or _has_raw_tree_components(
        resolved_path
    ):
        return True
    resolved_raw_root = raw_root.resolve(strict=False)
    if resolved_path == resolved_raw_root:
        return True
    return resolved_raw_root in resolved_path.parents


def _raw_directory_identities(raw_root: Path) -> set[tuple[int, int]]:
    """Inodes of the raw root and a bounded tree of its directories.

    Bind-mounting a descendant such as ``outputs/raw/run`` keeps a distinct
    pathname after ``resolve()``. Comparing only the root inode would miss it.
    """

    identities: set[tuple[int, int]] = set()
    roots = [raw_root]
    resolved = raw_root.resolve(strict=False)
    if resolved != raw_root:
        roots.append(resolved)
    for root in roots:
        ident = _stat_identity(root)
        if ident is not None:
            identities.add(ident)
        try:
            for dirpath, dirnames, _filenames in os.walk(root, followlinks=False):
                relative = Path(dirpath)
                try:
                    depth = len(relative.relative_to(root).parts)
                except ValueError:
                    depth = 0
                if depth >= 3:
                    dirnames.clear()
                    continue
                for name in dirnames:
                    ident = _stat_identity(Path(dirpath) / name)
                    if ident is not None:
                        identities.add(ident)
        except OSError:
            continue
    return identities


def is_under_raw(path: Path, raw_root: Path | None = None) -> bool:
    """Whether ``path`` names or aliases the immutable raw output tree."""

    root = DEFAULT_RAW_OUTPUT_ROOT if raw_root is None else raw_root
    if _names_raw_tree(path, root):
        return True
    raw_ids = _raw_directory_identities(root)
    if not raw_ids:
        return False
    ancestors = _ancestor_identities(path) | _ancestor_identities(path.parent)
    return bool(raw_ids & ancestors)
