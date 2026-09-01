"""Fail-closed byte snapshots for the training-readiness audit.

The audit must report on the exact regular files and bytes it authenticated.
This boundary owns tree enumeration, directory-descriptor pinning, committed
round digest checks, and validation of already-authenticated exporter bytes.
"""

from __future__ import annotations

import hashlib
import os
import stat
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Callable, Mapping

if __package__:
    from . import _expose_package_sibling, _local_sibling_module, _require_local_sibling

    if _local_sibling_module("training_audit_snapshot", allow_initializing=True):
        import training_audit_snapshot as _direct_training_audit_snapshot

        _require_local_sibling(
            _direct_training_audit_snapshot,
            "training_audit_snapshot",
        )
        del _direct_training_audit_snapshot
    from .census import enclosing_marker_root, visible_jsonl_paths
    from .round_txn import completed_manifests
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "training_audit_snapshot"
    )
    from census import enclosing_marker_root, visible_jsonl_paths
    from round_txn import completed_manifests


PINNED_DIRECTORY_FLAGS = (
    os.O_RDONLY
    | getattr(os, "O_DIRECTORY", 0)
    | getattr(os, "O_NOFOLLOW", 0)
    | getattr(os, "O_CLOEXEC", 0)
)
_ReadMember = Callable[[Path, Path], bytes]
_OpenDescriptor = Callable[..., int]
_ReadDescriptor = Callable[[int, Path], bytes]
_DigestIndex = Callable[[Path], dict[str, str]]
_ScanEntries = Callable[[Path], list[os.DirEntry]]
_ClassifyEntry = Callable[[os.DirEntry], str]
_EnumerateMembers = Callable[[Path], list[Path]]
_RequireDigest = Callable[
    [bytes, Path, Path | None, dict[Path, dict[str, str]]], None
]


@dataclass(frozen=True)
class DigestBinding:
    """Manifest lookup state for one captured member's digest binding."""

    marker_root: Path | None
    digest_cache: dict[Path, dict[str, str]]
    digest_index: _DigestIndex


def open_audit_descriptor(
    path: str | Path,
    flags: int,
    relative: Path,
    *,
    dir_fd: int | None = None,
) -> int:
    """Open one pinned component or raise the audit's bounded error."""
    try:
        if dir_fd is None:
            return os.open(path, flags)
        return os.open(path, flags, dir_fd=dir_fd)
    except OSError as exc:
        raise ValueError(
            f"audit member cannot be captured: {relative}: {exc}"
        ) from exc


def read_regular_audit_descriptor(fd: int, relative: Path) -> bytes:
    """Validate and drain the exact descriptor used for the snapshot."""
    if not stat.S_ISREG(os.fstat(fd).st_mode):
        raise ValueError(f"audit member is not an exact regular file: {relative}")
    chunks = []
    while chunk := os.read(fd, 1 << 20):
        chunks.append(chunk)
    return b"".join(chunks)


def _audit_member_identity(metadata: os.stat_result) -> tuple[int, ...]:
    """Identity and content fields that must span one legacy member read."""

    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_mode,
        metadata.st_nlink,
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
    )


def _require_audit_member_identity(
    expected: os.stat_result,
    actual: os.stat_result,
    relative: Path,
) -> None:
    """Require two observations to describe one unchanged member identity."""

    if _audit_member_identity(expected) != _audit_member_identity(actual):
        raise ValueError(f"audit member identity changed while reading: {relative}")


def read_pinned_member(
    run_dir: Path,
    relative: Path,
    *,
    open_descriptor: _OpenDescriptor = open_audit_descriptor,
    read_descriptor: _ReadDescriptor = read_regular_audit_descriptor,
) -> bytes:
    """Read a member without following a swapped path component.

    Every directory is opened relative to its pinned parent descriptor. The
    final open adds ``O_NONBLOCK`` so a swapped FIFO cannot hang the audit,
    and ``fstat`` validates the same descriptor from which bytes are read.
    """
    expected = _regular_member_metadata(run_dir / relative, relative)
    opened: list[int] = []
    try:
        current = open_descriptor(
            run_dir,
            PINNED_DIRECTORY_FLAGS,
            relative,
        )
        opened.append(current)
        for part in relative.parts[:-1]:
            current = open_descriptor(
                part,
                PINNED_DIRECTORY_FLAGS,
                relative,
                dir_fd=current,
            )
            opened.append(current)
        descriptor = open_descriptor(
            relative.name,
            os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
            relative,
            dir_fd=current,
        )
        opened.append(descriptor)
        descriptor_metadata = os.fstat(descriptor)
        _require_audit_member_identity(expected, descriptor_metadata, relative)
        payload = read_descriptor(descriptor, relative)
        _require_audit_member_identity(
            descriptor_metadata,
            os.fstat(descriptor),
            relative,
        )
        _require_audit_member_identity(
            descriptor_metadata,
            _regular_member_metadata(run_dir / relative, relative),
            relative,
        )
        return payload
    finally:
        for descriptor in opened:
            os.close(descriptor)


def _declared_digest(entry: object) -> tuple[str, str] | None:
    """Return one well-formed manifest name/digest declaration."""
    if not isinstance(entry, dict):
        return None
    name = entry.get("name")
    digest = entry.get("sha256")
    if isinstance(name, str) and isinstance(digest, str):
        return name, digest
    return None


def marker_digest_index(marker_root: Path) -> dict[str, str]:
    """Map committed artifact names to their declared round digests."""
    declarations = (
        _declared_digest(entry)
        for manifest in completed_manifests(marker_root).values()
        for entry in manifest.get("files", [])
    )
    return dict(declaration for declaration in declarations if declaration is not None)


def _committed_digest(
    relative: Path,
    binding: DigestBinding,
) -> str | None:
    """Resolve a member's declared digest, caching each marker root once."""
    if binding.marker_root is None:
        return None
    if binding.marker_root not in binding.digest_cache:
        binding.digest_cache[binding.marker_root] = binding.digest_index(
            binding.marker_root
        )
    return binding.digest_cache[binding.marker_root].get(relative.name)


def require_committed_digest(
    payload: bytes,
    relative: Path,
    marker_root: Path | None,
    digest_cache: dict[Path, dict[str, str]],
) -> None:
    """Bind captured marker-mode bytes to the digest their round committed."""
    require_bound_committed_digest(
        payload,
        relative,
        DigestBinding(marker_root, digest_cache, marker_digest_index),
    )


def require_bound_committed_digest(
    payload: bytes,
    relative: Path,
    binding: DigestBinding,
) -> None:
    """Bind captured bytes through an explicit manifest lookup boundary."""
    declared = _committed_digest(relative, binding)
    mismatched = declared is not None and hashlib.sha256(payload).hexdigest() != declared
    if mismatched:
        raise ValueError(
            f"audit member does not match its committed round digest: {relative}"
        )


def scan_audit_entries(directory: Path) -> list[os.DirEntry]:
    """List one directory in stable name order, failing closed."""
    try:
        with os.scandir(directory) as scan:
            return sorted(scan, key=lambda entry: entry.name)
    except OSError as exc:
        raise ValueError(
            f"audit tree cannot be enumerated: {directory}: {exc}"
        ) from exc


def _entry_metadata(entry: os.DirEntry) -> os.stat_result:
    """Read an entry's own metadata without following aliases."""
    try:
        return entry.stat(follow_symlinks=False)
    except OSError as exc:
        raise ValueError(
            f"audit member cannot be captured: {entry.path}: {exc}"
        ) from exc


def _require_non_alias(entry: os.DirEntry, metadata: os.stat_result) -> None:
    """Reject every symlink before the audit decides whether to descend."""
    if stat.S_ISLNK(metadata.st_mode):
        raise ValueError(f"audit tree contains a symlink alias: {entry.path}")


def classify_audit_entry(entry: os.DirEntry) -> str:
    """Classify an entry as ``descend``, ``member``, or ``ignore``."""
    metadata = _entry_metadata(entry)
    _require_non_alias(entry, metadata)
    if stat.S_ISDIR(metadata.st_mode) and not entry.name.endswith(".jsonl"):
        return "descend"
    return "member" if entry.name.endswith(".jsonl") else "ignore"


def _record_entry(
    entry: os.DirEntry,
    pending: list[Path],
    members: list[Path],
    classify_entry: _ClassifyEntry,
) -> None:
    """Apply one classified entry to the pending/member collections."""
    action = classify_entry(entry)
    if action == "descend":
        pending.append(Path(entry.path))
    elif action == "member":
        members.append(Path(entry.path))


def enumerate_run_members(
    run_dir: Path,
    *,
    scan_entries: _ScanEntries = scan_audit_entries,
    classify_entry: _ClassifyEntry = classify_audit_entry,
) -> list[Path]:
    """Enumerate all JSONL entries while refusing symlink aliases."""
    members: list[Path] = []
    pending = [Path(run_dir)]
    while pending:
        for entry in scan_entries(pending.pop()):
            _record_entry(entry, pending, members, classify_entry)
    return sorted(members)


def run_membership(
    run_dir: Path,
    *,
    enumerate_members: _EnumerateMembers = enumerate_run_members,
) -> tuple[frozenset[Path], tuple[Path, ...]]:
    """Return visible and enumerated members relative to ``run_dir``."""
    visible = frozenset(
        path.relative_to(run_dir) for path in visible_jsonl_paths(run_dir)
    )
    members = tuple(
        path.relative_to(run_dir) for path in enumerate_members(run_dir)
    )
    return visible, members


def _regular_member_metadata(path: Path, relative: Path) -> os.stat_result:
    """Return metadata only when a member is an exact regular file."""
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise ValueError(
            f"audit member cannot be captured: {relative}: {exc}"
        ) from exc
    if not stat.S_ISREG(metadata.st_mode):
        raise ValueError(f"audit member is not an exact regular file: {relative}")
    return metadata


class SnapshotCapture:
    """Descriptor and digest state for one immutable run-tree capture."""

    def __init__(
        self,
        run_dir: Path,
        visible: frozenset[Path],
        read_member: _ReadMember,
        require_digest: _RequireDigest = require_committed_digest,
    ) -> None:
        self.run_dir = run_dir
        self.visible = visible
        self.read_member = read_member
        self.require_digest = require_digest
        self.digest_cache: dict[Path, dict[str, str]] = {}

    def member(self, relative: Path) -> tuple[Path, bytes] | None:
        """Capture a visible member while validating every enumerated entry."""
        path = self.run_dir / relative
        _regular_member_metadata(path, relative)
        if relative not in self.visible:
            return None
        payload = self.read_member(self.run_dir, relative)
        self.require_digest(
            payload,
            relative,
            enclosing_marker_root(self.run_dir, path),
            self.digest_cache,
        )
        return relative, payload


def _captured_members(
    capture: SnapshotCapture,
    members: tuple[Path, ...],
) -> list[tuple[Path, bytes]]:
    """Capture every enumerated member that the transaction makes visible."""
    files = []
    for relative in members:
        captured = capture.member(relative)
        if captured is not None:
            files.append(captured)
    return files


def _require_stable_membership(
    run_dir: Path,
    expected: tuple[frozenset[Path], tuple[Path, ...]],
) -> None:
    """Reject a run tree whose membership changed during byte capture."""
    if run_membership(run_dir) != expected:
        raise ValueError("audit member set changed while capturing the run snapshot")


def capture_run_files(
    run_dir: Path,
    *,
    read_member: _ReadMember | None = None,
) -> list[tuple[Path, bytes]]:
    """Capture a stable, authenticated byte snapshot of visible JSONL files."""
    visible, members = run_membership(run_dir)
    member_reader = read_pinned_member if read_member is None else read_member
    capture = SnapshotCapture(run_dir, visible, member_reader)
    files = _captured_members(capture, members)
    _require_stable_membership(run_dir, (visible, members))
    return files


def _snapshot_path_is_unsafe(raw_relative: str, relative: PurePosixPath) -> bool:
    invalid_parts = {"", ".", ".."}.intersection(relative.parts)
    return any(
        (
            relative.is_absolute(),
            not relative.parts,
            "\0" in raw_relative,
            bool(invalid_parts),
        )
    )


def validate_snapshot_path(raw_relative: str) -> Path:
    """Return one safe relative path in the host path vocabulary."""
    if not isinstance(raw_relative, str) or not raw_relative:
        raise ValueError("audit snapshot paths must be nonempty strings")
    relative = PurePosixPath(raw_relative)
    if _snapshot_path_is_unsafe(raw_relative, relative):
        raise ValueError(f"unsafe audit snapshot path: {raw_relative!r}")
    return Path(*relative.parts)


def validate_snapshot_member(
    raw_relative: str,
    payload: bytes,
) -> tuple[Path, bytes]:
    """Validate one authenticated path and its exact payload bytes."""
    relative = validate_snapshot_path(raw_relative)
    if not isinstance(payload, bytes):
        raise TypeError(
            f"audit snapshot payload for {raw_relative!r} must be bytes"
        )
    return relative, payload


def validate_snapshot_files(
    snapshot: Mapping[str, bytes],
) -> list[tuple[Path, bytes]]:
    """Validate caller-supplied snapshot bytes into audit members."""
    return [
        validate_snapshot_member(raw_relative, payload)
        for raw_relative, payload in sorted(snapshot.items())
    ]


if __package__:
    _expose_package_sibling(__name__)
