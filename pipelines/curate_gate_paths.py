#!/usr/bin/env python3
"""Path confinement and atomic publication for the curation integration gate.

Split out of ``curate_gate.py`` (CodeScene: Lines of Code in a Single File) by
responsibility; every name is re-exported from ``curate_gate`` so existing
``curate_gate.X`` call sites resolve unchanged.

Every resolver here refuses a symlinked path component *before* resolving, so a
link cannot be laundered into a legitimate-looking absolute path. The two
repository roots (``_REPO`` and ``RAW_OUTPUT_ROOT``) arrive as explicit
parameters rather than module globals: they stay patchable on the ``curate_gate``
facade, and the redirection stays visible at the call site.
"""

from __future__ import annotations

import ctypes
import errno
import os
import sys
from pathlib import Path
from typing import Any, NamedTuple, Sequence

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("curate_gate_paths")
    from . import curate_gate_contract as _contract
    from . import curate_gate_digest as _digest
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "curate_gate_paths"
    )
    _PIPELINES = Path(__file__).resolve().parent
    if str(_PIPELINES) not in sys.path:
        sys.path.insert(0, str(_PIPELINES))
    import curate_gate_contract as _contract
    import curate_gate_digest as _digest

GOVERNANCE_DIRNAME = _contract.GOVERNANCE_DIRNAME
GateError = _contract.GateError
_tree_snapshot = _digest._tree_snapshot


def _resolve_declared_path(base: Path, value: str, label: str) -> Path:
    """Resolve one plan-relative path without erasing symlink evidence."""
    declared = Path(value)
    if declared.is_absolute() or ".." in declared.parts:
        raise GateError(f"{label} must stay within the plan directory: {value!r}")

    walked = base
    for part in declared.parts:
        if part in {"", "."}:
            continue
        walked = walked / part
        if walked.is_symlink():
            raise GateError(f"{label} contains a symlinked path component: {walked}")

    resolved = (base / declared).resolve()
    if resolved != base and base not in resolved.parents:
        raise GateError(f"{label} resolves outside the plan directory: {resolved}")
    return resolved


class RepoRoots(NamedTuple):
    """The two repository roots a plan-relative source path is resolved against.

    Both stay owned by ``curate_gate`` so that redirecting the gate at a
    temporary repository stays visible at the facade call site.
    """

    repo_root: Path
    raw_output_root: Path


def _resolve_source_run_path(
    plan_dir: Path,
    value: str,
    label: str,
    roots: RepoRoots,
) -> Path:
    """Resolve a source tree without making the documented raw path ambiguous."""
    repo_root, raw_output_root = roots
    declared = Path(value)
    if declared.is_absolute() or ".." in declared.parts:
        raise GateError(
            f"{label} must be plan-relative or repository-relative beneath outputs/raw: {value!r}"
        )

    parts = tuple(part for part in declared.parts if part not in {"", "."})
    if not parts:
        raise GateError(f"{label} must name a directory")

    repository_raw = len(parts) >= 2 and parts[:2] == ("outputs", "raw")
    root = repo_root if repository_raw else plan_dir
    walked = root
    for part in parts:
        walked = walked / part
        if walked.is_symlink():
            raise GateError(f"{label} contains a symlinked path component: {walked}")

    resolved = (root / Path(*parts)).resolve()
    allowed_root = raw_output_root if repository_raw else plan_dir
    if resolved != allowed_root and allowed_root not in resolved.parents:
        scope = "outputs/raw" if repository_raw else "the plan directory"
        raise GateError(f"{label} resolves outside {scope}: {resolved}")
    return resolved


def _lane_manifest_format(path: Path, label: str) -> str:
    """Return the only two evidence formats understood by promotion."""
    if path.suffix == ".json":
        return "json"
    if path.suffix == ".jsonl":
        return "jsonl"
    raise GateError(f"{label} must end in .json or .jsonl: {path}")


def _relative_artifact_destination(value: Any, label: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise GateError(f"{label} must be a non-empty relative path")
    destination = Path(value)
    if destination.is_absolute() or ".." in destination.parts:
        raise GateError(f"{label} must stay within its governance directory: {value!r}")
    parts = tuple(part for part in destination.parts if part not in {"", "."})
    if not parts:
        raise GateError(f"{label} must name a file")
    return Path(*parts)


def _normalized_output_path(value: Any, label: str) -> str:
    path = _relative_artifact_destination(value, label)
    if path.suffix != ".jsonl" or path.parts[0] == GOVERNANCE_DIRNAME:
        raise GateError(f"{label} must identify a corpus JSONL path")
    return path.as_posix()


def _assert_new_destination(destination: Path, label: str, raw_output_root: Path) -> Path:
    declared = Path(os.path.abspath(destination))
    if os.path.lexists(declared):
        raise GateError(f"refusing to overwrite an existing {label}: {declared}")
    resolved = declared.resolve(strict=False)
    if resolved == raw_output_root or raw_output_root in resolved.parents:
        raise GateError(f"refusing to write {label} beneath immutable raw output: {declared}")
    return resolved


def _assert_disjoint_trees(
    source: Path,
    destination: Path,
    *,
    source_label: str = "cleaned",
    destination_label: str = "curated",
) -> None:
    source = source.resolve(strict=False)
    destination = destination.resolve(strict=False)
    if source == destination or source in destination.parents or destination in source.parents:
        raise GateError(
            f"{source_label} and {destination_label} must be disjoint after symlink "
            f"resolution: {source_label}={source}, {destination_label}={destination}"
        )


def _rename_noreplace(
    source: Path,
    destination: Path,
    label: str,
    expected_tree: Sequence[dict[str, Any]],
) -> None:
    """Atomically publish one directory while refusing an existing pathname."""
    source = Path(source)
    destination = Path(destination)
    if _tree_snapshot(source) != list(expected_tree):
        raise GateError(f"{label} staging tree changed after final validation")
    if os.name == "nt":
        try:
            source.rename(destination)
        except FileExistsError as exc:
            raise GateError(f"refusing to overwrite an existing {label}: {destination}") from exc
        except OSError as exc:
            raise GateError(f"cannot publish {label} {destination}: {exc}") from exc
        return

    libc = ctypes.CDLL(None, use_errno=True)
    renameat2 = getattr(libc, "renameat2", None)
    if renameat2 is None:
        raise GateError("atomic no-replace publication is unavailable on this platform")
    renameat2.argtypes = [
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    ]
    renameat2.restype = ctypes.c_int
    at_fdcwd = -100
    rename_noreplace = 1
    result = renameat2(
        at_fdcwd,
        os.fsencode(source),
        at_fdcwd,
        os.fsencode(destination),
        rename_noreplace,
    )
    if result == 0:
        return
    error = ctypes.get_errno()
    if error in {errno.EEXIST, errno.ENOTEMPTY}:
        raise GateError(f"refusing to overwrite an existing {label}: {destination}")
    raise GateError(f"cannot atomically publish {label} {destination}: {os.strerror(error)}")


def _logical_source_path(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GateError(f"{label} must be a non-empty source path")
    path = Path(value)
    parts = path.parts
    raw_roots = [
        index for index in range(len(parts) - 1) if parts[index : index + 2] == ("outputs", "raw")
    ]
    if raw_roots:
        raw_index = raw_roots[-1] + 1
        if len(parts) <= raw_index + 2:
            raise GateError(f"{label} does not identify a record below outputs/raw")
        parts = parts[raw_index + 2 :]
    elif path.is_absolute():
        raise GateError(f"{label} must be relative or identify a path below outputs/raw")
    parts = tuple(part for part in parts if part not in {"", "."})
    if not parts or ".." in parts:
        raise GateError(f"{label} is not a safe logical source path: {value!r}")
    return Path(*parts).as_posix()


def _assert_no_symlink(root: Path, path: Path, label: str) -> None:
    walked = root
    for part in path.relative_to(root).parts:
        walked = walked / part
        if walked.is_symlink():
            raise GateError(f"{label} contains a symlinked path: {walked}")


def _snapshot_bytes(source: Path, root: Path, label: str) -> bytes:
    if source.is_symlink() or not source.is_file():
        raise GateError(f"{label} must be a regular, non-symlink file: {source}")
    _assert_no_symlink(root, source, label)
    try:
        return source.read_bytes()
    except OSError as exc:
        raise GateError(f"cannot snapshot {label} {source}: {exc}") from exc


if __package__:
    _expose_package_sibling(__name__)
