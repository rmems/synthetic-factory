"""Refuse writes that name or alias the repository's immutable raw tree."""

from __future__ import annotations

import os
import sys
from contextlib import suppress
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAW_OUTPUT_ROOT = REPOSITORY_ROOT / "outputs" / "raw"


def _stat_path(path: Path) -> os.stat_result | None:
    state = None
    with suppress(OSError):
        state = path.stat()
    return state


def _stat_identity(path: Path) -> tuple[int, int] | None:
    state = _stat_path(path)
    if state is None:
        return None
    return state.st_dev, state.st_ino


def _iter_ancestors(path: Path):
    current = Path(os.path.abspath(path))
    seen: set[Path] = set()
    while current not in seen:
        seen.add(current)
        yield current
        parent = current.parent
        if parent == current:
            return
        current = parent


def _ancestor_identities(path: Path) -> set[tuple[int, int]]:
    """Device/inode identities of ``path`` and existing ancestors."""

    identities: set[tuple[int, int]] = set()
    for current in _iter_ancestors(path):
        identity = _stat_identity(current)
        if identity is not None:
            identities.add(identity)
    return identities


def contains_raw_segments(parts: tuple[str, ...]) -> bool:
    """Return whether path components contain the immutable raw-tree pair."""

    return any(
        parts[index : index + 2] == ("outputs", "raw")
        for index in range(len(parts) - 1)
    )


def _has_raw_tree_components(path: Path) -> bool:
    return contains_raw_segments(path.parts)


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


def _path_is_within(inner: Path, outer: Path) -> bool:
    if inner == outer:
        return True
    try:
        inner.relative_to(outer)
    except ValueError:
        return False
    return True


def _unescape_mount_field(value: str) -> str:
    return (
        value.replace("\\040", " ")
        .replace("\\011", "\t")
        .replace("\\012", "\n")
        .replace("\\134", "\\")
    )


def _parse_mountinfo_line(line: str) -> tuple[Path, Path, str] | None:
    if " - " not in line:
        return None
    left, _right = line.split(" - ", 1)
    fields = left.split()
    if len(fields) < 5:
        return None
    device = fields[2]
    root_in_fs = Path(_unescape_mount_field(fields[3]))
    mountpoint = Path(_unescape_mount_field(fields[4]))
    return mountpoint, root_in_fs, device


def _read_mountinfo() -> tuple[tuple[Path, Path, str], ...]:
    """Return ``(mountpoint, root-in-fs, device)`` rows from Linux mountinfo."""

    try:
        text = Path("/proc/self/mountinfo").read_text(encoding="utf-8")
    except OSError:
        return ()
    pairs: list[tuple[Path, Path, str]] = []
    for line in text.splitlines():
        parsed = _parse_mountinfo_line(line)
        if parsed is not None:
            pairs.append(parsed)
    return tuple(pairs)


def _host_source_paths(
    root_in_fs: Path,
    device: str,
    mounts: tuple[tuple[Path, Path, str], ...],
) -> tuple[Path, ...]:
    """Map a mountinfo root onto every covering view in this namespace."""

    matches: list[Path] = []
    for mountpoint, other_root, other_device in mounts:
        if other_device != device:
            continue
        try:
            relative = root_in_fs.relative_to(other_root)
        except ValueError:
            continue
        matches.append(mountpoint / relative)
    return tuple(matches) if matches else (root_in_fs,)


def _host_source_path(
    root_in_fs: Path,
    device: str,
    mounts: tuple[tuple[Path, Path, str], ...],
) -> Path:
    """Map a mountinfo root onto this process's path namespace."""

    return _host_source_paths(root_in_fs, device, mounts)[0]


def _shares_root_inode(path: Path, raw_root: Path) -> bool:
    raw_ids = {
        ident
        for ident in (
            _stat_identity(raw_root),
            _stat_identity(raw_root.resolve(strict=False)),
        )
        if ident is not None
    }
    if not raw_ids:
        return False
    ancestors = _ancestor_identities(path) | _ancestor_identities(path.parent)
    return bool(raw_ids & ancestors)


def _dest_uses_mount(path: Path, mountpoint: Path) -> bool:
    ancestors = set(_iter_ancestors(path)) | set(_iter_ancestors(path.parent))
    if mountpoint in ancestors:
        return True
    mount_id = _stat_identity(mountpoint)
    if mount_id is None:
        return False
    return mount_id in _ancestor_identities(path) or mount_id in _ancestor_identities(
        path.parent
    )


def _bind_mount_hits_raw(path: Path, raw_root: Path) -> bool:
    resolved_raw = raw_root.resolve(strict=False)
    mounts = _read_mountinfo()
    for mountpoint, root_in_fs, device in mounts:
        sources = _host_source_paths(root_in_fs, device, mounts)
        if not any(
            _path_is_within(source, raw_root) or _path_is_within(source, resolved_raw)
            for source in sources
        ):
            continue
        if _dest_uses_mount(path, mountpoint):
            return True
    return False


def is_under_raw(path: Path, raw_root: Path | None = None) -> bool:
    """Whether ``path`` names or aliases the immutable raw output tree."""

    root = DEFAULT_RAW_OUTPUT_ROOT if raw_root is None else raw_root
    if _names_raw_tree(path, root):
        return True
    if _shares_root_inode(path, root):
        return True
    return _bind_mount_hits_raw(path, root)


if __package__:
    from . import _expose_package_sibling, _local_sibling_module, _require_local_sibling

    if _local_sibling_module("raw_tree_guard", allow_initializing=True):
        import raw_tree_guard as _direct_raw_tree_guard

        _require_local_sibling(_direct_raw_tree_guard, "raw_tree_guard")
        del _direct_raw_tree_guard
    _expose_package_sibling(__name__)
else:
    _package = sys.modules.get("pipelines")
    getattr(_package, "_join_package_sibling", lambda name: None)("raw_tree_guard")
    _current = sys.modules[__name__]
    _local = getattr(_package, "_local_sibling_module", lambda *args, **kwargs: None)(
        "raw_tree_guard",
        allow_initializing=True,
    )
    if _local is _current:
        sys.modules.setdefault("pipelines.raw_tree_guard", _current)
        setattr(_package, "raw_tree_guard", _current)
    del _current, _local, _package
