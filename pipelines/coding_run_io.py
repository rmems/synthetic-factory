"""Filesystem side of the coding-lane run writer.

Split out of ``curate_coding.py`` (CodeScene: Lines of Code in a Single File)
by responsibility: refusing ``outputs/raw/`` and existing destinations,
discovering a source run's JSONL files without following symlinks, and
recording the identity of every created path so a failed run removes only
what it created. ``curate_coding`` re-binds each name under its historical
private spelling, so ``curate_coding._unlink_created_file`` and friends keep
resolving, and ``curate_coding._write_new_jsonl`` stays the patched writer seam.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("coding_run_io")
    from .coding_constants import RUN_MANIFEST_FILENAME
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "coding_run_io"
    )
    from coding_constants import RUN_MANIFEST_FILENAME

_PathIdentity = tuple[int, int]
_CreatedPaths = list[tuple[Path, _PathIdentity]]


def is_under_raw(path: Path) -> bool:
    parts = path.resolve(strict=False).parts
    return any(
        parts[index : index + 2] == ("outputs", "raw")
        for index in range(len(parts) - 1)
    )


def created_file_identity(descriptor: int) -> _PathIdentity:
    metadata = os.fstat(descriptor)
    return metadata.st_dev, metadata.st_ino


def created_directory_identity(path: Path) -> _PathIdentity:
    metadata = os.lstat(path)
    return metadata.st_dev, metadata.st_ino


def unlink_created_file(path: Path, identity: _PathIdentity) -> bool:
    """Remove ``path`` only while it still names the file this process created."""
    try:
        metadata = os.lstat(path)
    except FileNotFoundError:
        return False
    if (metadata.st_dev, metadata.st_ino) != identity:
        return False
    path.unlink()
    return True


def rmdir_created_directory(path: Path, identity: _PathIdentity) -> bool:
    """Remove an empty directory only while its pathname retains our inode."""
    try:
        metadata = os.lstat(path)
    except FileNotFoundError:
        return False
    if (metadata.st_dev, metadata.st_ino) != identity:
        return False
    try:
        path.rmdir()
    except OSError:
        return False
    return True


def _assert_distinct_destinations(paths: list[Path]) -> None:
    resolved = [path.resolve(strict=False) for path in paths]
    if len(set(resolved)) != len(resolved):
        raise ValueError("output destinations must be distinct")


def _assert_fresh_destination(path: Path) -> None:
    if is_under_raw(path):
        raise ValueError(f"refusing to write inside immutable raw evidence: {path}")
    if path.exists():
        raise FileExistsError(f"refusing to replace existing destination: {path}")


def preflight_destinations(paths: list[Path]) -> None:
    """Refuse aliased destinations first, then any under ``outputs/raw/`` or already present."""
    _assert_distinct_destinations(paths)
    for path in paths:
        _assert_fresh_destination(path)


def _resolved_source_directory(source_root: Path) -> Path:
    """Resolve the declared source run, refusing a symlink or a non-directory."""
    declared = Path(os.path.abspath(source_root))
    if declared.is_symlink():
        raise ValueError(f"source run must not be a symlink: {declared}")
    try:
        resolved = declared.resolve(strict=True)
    except OSError as exc:
        raise ValueError(f"source run is not a directory: {declared}") from exc
    if not resolved.is_dir():
        raise ValueError(f"source run is not a directory: {declared}")
    return resolved


def _discover_jsonl_paths(resolved: Path) -> list[Path]:
    """Every JSONL file beneath ``resolved`` in relative-path order; no symlinks anywhere."""
    paths = []
    for path in resolved.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"source run contains a symlinked path: {path}")
        if path.is_file() and path.suffix == ".jsonl":
            paths.append(path)
    paths.sort(key=lambda jsonl_path: jsonl_path.relative_to(resolved).as_posix())
    return paths


def source_jsonl_paths(source_root: Path) -> tuple[Path, list[Path]]:
    resolved = _resolved_source_directory(source_root)
    paths = _discover_jsonl_paths(resolved)
    if not paths:
        raise ValueError(f"source run holds no JSONL files: {resolved}")
    if resolved / RUN_MANIFEST_FILENAME in paths:
        raise ValueError(
            f"source JSONL conflicts with aggregate manifest name: {RUN_MANIFEST_FILENAME}"
        )
    return resolved, paths


def new_run_destination(destination: Path, source_root: Path) -> Path:
    declared = Path(os.path.abspath(destination))
    if is_under_raw(declared):
        raise ValueError(f"refusing to write inside immutable raw evidence: {declared}")
    if os.path.lexists(declared):
        raise FileExistsError(f"refusing to replace existing destination: {declared}")
    resolved = declared.resolve(strict=False)
    if resolved == source_root or source_root in resolved.parents:
        raise ValueError(f"output directory must be outside the source run: {declared}")
    return declared


def make_output_directories(
    output_root: Path,
    source_root: Path,
    source_paths: list[Path],
    created_directories: _CreatedPaths,
) -> None:
    """Create every mirrored subdirectory, parents first, recording each one created."""
    relative_directories = {
        parent
        for source_path in source_paths
        for parent in source_path.relative_to(source_root).parents
        if parent != Path(".")
    }
    for relative in sorted(
        relative_directories,
        key=lambda relative_path: (len(relative_path.parts), relative_path.parts),
    ):
        directory = output_root / relative
        directory.mkdir()
        created_directories.append(
            (directory, created_directory_identity(directory))
        )


def rollback_created(created_files: _CreatedPaths, created_directories: _CreatedPaths) -> None:
    """Remove what this run created, newest first, without touching replaced pathnames."""
    for path, identity in reversed(created_files):
        unlink_created_file(path, identity)
    for path, identity in reversed(created_directories):
        rmdir_created_directory(path, identity)


if __package__:
    _expose_package_sibling(__name__)
