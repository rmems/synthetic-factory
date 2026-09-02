#!/usr/bin/env python3
"""Pinned directory identities shared by compose source and destination I/O."""

from __future__ import annotations

import ctypes
import errno
import hashlib
import os
import stat
import sys
import uuid
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("compose_destination_binding")
    from .compose_contract import ComposeError
    from .raw_tree_guard import contains_raw_segments, is_under_raw
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "compose_destination_binding"
    )
    from compose_contract import ComposeError
    from raw_tree_guard import contains_raw_segments, is_under_raw

DESTINATION_PARENT_LABEL = "destination parent"
DESTINATION_PIN_CLOSED = "destination pin was already closed"

# Compatibility callers import this symbol through ``compose_destination``.
_contains_raw_segments = contains_raw_segments
_RENAME_NOREPLACE = 1
_PRIVATE_NAME_ATTEMPTS = 8
_ATOMIC_RENAME_UNSUPPORTED = frozenset(
    {
        errno.ENOSYS,
        errno.EINVAL,
        errno.EOPNOTSUPP,
        errno.EXDEV,
    }
)


def _rename_noreplace(
    parent_descriptor: int,
    source_name: str,
    destination_name: str,
) -> None:
    """Atomically rename one sibling without replacing an existing entry."""

    libc = ctypes.CDLL(None, use_errno=True)
    renameat2 = getattr(libc, "renameat2", None)
    if renameat2 is None:
        raise OSError(errno.ENOSYS, "renameat2 is unavailable")
    renameat2.argtypes = (
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    )
    renameat2.restype = ctypes.c_int
    result = renameat2(
        parent_descriptor,
        os.fsencode(source_name),
        parent_descriptor,
        os.fsencode(destination_name),
        _RENAME_NOREPLACE,
    )
    if result != 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), source_name)


def _private_entry_name(prefix: str) -> str:
    """Return one bounded private sibling name; no-replace proves uniqueness."""

    return f".synthetic-factory-{prefix}-{uuid.uuid4().hex}"


def _entry_identity(
    parent_descriptor: int,
    name: str,
) -> tuple[int, int, int] | None:
    try:
        metadata = os.stat(
            name,
            dir_fd=parent_descriptor,
            follow_symlinks=False,
        )
    except OSError:
        return None
    return _directory_identity(metadata)


@dataclass(frozen=True)
class _OwnedEntryMove:
    """Policy and identity state for one no-replace private rename."""

    parent_descriptor: int
    name: str
    expected_identity: tuple[int, int, int]
    prefix: str
    label: str
    strict: bool

    def _rename_candidate(self, private_name: str) -> bool | None:
        try:
            _rename_noreplace(self.parent_descriptor, self.name, private_name)
        except FileExistsError:
            return False
        except FileNotFoundError:
            return None
        except OSError as exc:
            self._handle_error(exc)
            return None
        return True

    def _handle_error(self, error: OSError) -> None:
        if self.strict or error.errno in _ATOMIC_RENAME_UNSUPPORTED:
            raise ComposeError(f"{self.label}: atomic private rename failed: {error}") from error

    def _restore(self, private_name: str) -> None:
        try:
            _rename_noreplace(self.parent_descriptor, private_name, self.name)
        except OSError:
            pass

    def _authenticate(self, private_name: str) -> str | None:
        if _entry_identity(self.parent_descriptor, private_name) == self.expected_identity:
            return private_name
        self._restore(private_name)
        if self.strict:
            raise ComposeError(f"{self.label}: entry identity changed before private rename")
        return None

    def move(self) -> str | None:
        """Move the owned entry privately without deleting either identity."""

        for _attempt in range(_PRIVATE_NAME_ATTEMPTS):
            private_name = _private_entry_name(self.prefix)
            moved = self._rename_candidate(private_name)
            if moved is False:
                continue
            if moved is None:
                return None
            return self._authenticate(private_name)
        if self.strict:
            raise ComposeError(f"{self.label}: cannot allocate a private transaction name")
        return None


def _move_owned_entry(move: _OwnedEntryMove) -> str | None:
    """Keep the private seam while its state object owns the algorithm."""

    return move.move()


def _quarantine_owned_entry(
    parent_descriptor: int,
    name: str,
    expected_identity: tuple[int, int, int],
    label: str,
) -> str | None:
    """Detach an owned entry for recovery without invoking deletion syscalls."""

    return _move_owned_entry(
        _OwnedEntryMove(
            parent_descriptor,
            name,
            expected_identity,
            prefix="rollback",
            label=label,
            strict=False,
        )
    )


def _stage_owned_entry(
    parent_descriptor: int,
    name: str,
    expected_identity: tuple[int, int, int],
    label: str,
) -> str:
    """Detach the verified transaction before its final authentication."""

    staged = _move_owned_entry(
        _OwnedEntryMove(
            parent_descriptor,
            name,
            expected_identity,
            prefix="commit",
            label=label,
            strict=True,
        )
    )
    if staged is None:
        raise ComposeError(f"{label}: entry disappeared before private rename")
    return staged


def _is_under_raw(path: Path) -> bool:
    """Reject lexical raw aliases as well as symlink-resolved raw paths."""

    if _contains_raw_segments(path.parts):
        return True
    try:
        return _path_aliases_raw(path)
    except (OSError, RuntimeError) as exc:
        raise ComposeError(f"cannot resolve destination path safely: {path}") from exc


def _path_aliases_raw(path: Path) -> bool:
    return is_under_raw(path)


def _directory_observations(path: Path) -> tuple[os.stat_result, Path]:
    return path.lstat(), path.resolve(strict=True)


def _required_directory_observations(path: Path, label: str) -> tuple[os.stat_result, Path]:
    """Observe a required directory while normalizing resolution failures."""

    try:
        return _directory_observations(path)
    except FileNotFoundError as exc:
        raise ComposeError(f"{label} is missing: {path}") from exc
    except (OSError, RuntimeError) as exc:
        raise ComposeError(f"{label} cannot be resolved safely: {path}") from exc


def _require_exact_directory(path: Path, label: str) -> Path:
    """Require a real directory reached without a symlinked path alias."""

    metadata, resolved = _required_directory_observations(path, label)
    absolute = Path(os.path.abspath(path))
    if not stat.S_ISDIR(metadata.st_mode):
        raise ComposeError(f"{label} must be an exact non-symlink directory: {path}")
    if resolved != absolute:
        raise ComposeError(f"{label} must be an exact non-symlink directory: {path}")
    return resolved


def _directory_identity(metadata: os.stat_result) -> tuple[int, int, int]:
    """Identity fields that do not change when directory entries are added."""

    return metadata.st_dev, metadata.st_ino, stat.S_IFMT(metadata.st_mode)


def _fresh_directory_names(descriptor: int, label: str) -> list[str]:
    """Enumerate through a fresh open description with an offset at zero."""

    flags = (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    try:
        scan_descriptor = os.open(".", flags, dir_fd=descriptor)
    except OSError as exc:
        raise ComposeError(f"{label}: cannot open directory for enumeration") from exc
    try:
        if _directory_identity(os.fstat(scan_descriptor)) != _directory_identity(
            os.fstat(descriptor)
        ):
            raise ComposeError(f"{label}: directory identity changed before enumeration")
        return sorted(os.listdir(scan_descriptor))
    except OSError as exc:
        raise ComposeError(f"{label}: cannot enumerate directory") from exc
    finally:
        os.close(scan_descriptor)


def _require_empty_directory(descriptor: int, label: str) -> None:
    """Require a newly pinned private directory to contain no adopted bytes."""

    entries = _fresh_directory_names(descriptor, label)
    if entries:
        raise ComposeError(f"{label}: new directory was not empty when pinned")


def _require_safe_new_directory(
    descriptor: int,
    parent_descriptor: int,
    label: str,
) -> None:
    """Require expected owner/device metadata for one new private directory."""

    try:
        opened = os.fstat(descriptor)
        parent = os.fstat(parent_descriptor)
    except OSError as exc:
        raise ComposeError(f"{label}: cannot authenticate new directory") from exc
    if _directory_identity(opened)[2] != stat.S_IFDIR:
        raise ComposeError(f"{label}: new entry is not an exact directory")
    if opened.st_dev != parent.st_dev or opened.st_uid != os.geteuid():
        raise ComposeError(f"{label}: new directory has unexpected ownership metadata")


@dataclass(frozen=True)
class _TreePath:
    """Descriptor-relative name used during exact-tree capture."""

    parent_descriptor: int
    name: str
    relative_parts: tuple[str, ...]

    @property
    def relative(self) -> str:
        return PurePosixPath(*self.relative_parts).as_posix()


@dataclass(frozen=True)
class _TreeEntry:
    """One path and metadata observation from the destination tree."""

    path: _TreePath
    metadata: os.stat_result

    @property
    def relative(self) -> str:
        return self.path.relative


@dataclass
class _DestinationTreeSnapshot:
    """Exact topology and byte digests observed through pinned descriptors."""

    directories: set[str] = field(default_factory=set)
    digests: dict[str, str] = field(default_factory=dict)

    @staticmethod
    def _file_identity(metadata: os.stat_result) -> tuple[int, ...]:
        return (
            metadata.st_dev,
            metadata.st_ino,
            metadata.st_mode,
            metadata.st_nlink,
            metadata.st_size,
            metadata.st_mtime_ns,
            metadata.st_ctime_ns,
        )

    @staticmethod
    def _open(path: _TreePath, *, directory: bool) -> int:
        flags = (
            os.O_RDONLY
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(
                os,
                "O_CLOEXEC",
                0,
            )
        )
        flags |= getattr(os, "O_DIRECTORY", 0) if directory else os.O_NONBLOCK
        try:
            return os.open(path.name, flags, dir_fd=path.parent_descriptor)
        except OSError as exc:
            kind = "directory" if directory else "file"
            raise ComposeError(
                f"destination tree {kind} cannot be opened: {path.relative}"
            ) from exc

    @staticmethod
    def _metadata(path: _TreePath) -> os.stat_result:
        try:
            return os.stat(
                path.name,
                dir_fd=path.parent_descriptor,
                follow_symlinks=False,
            )
        except OSError as exc:
            raise ComposeError(
                f"destination tree entry cannot be inspected: {path.relative}"
            ) from exc

    @classmethod
    def _require_stable_file(
        cls,
        expected: os.stat_result,
        actual: os.stat_result,
        relative: str,
    ) -> None:
        if cls._file_identity(expected) != cls._file_identity(actual):
            raise ComposeError(f"destination tree file changed: {relative}")

    @staticmethod
    def _digest_file(descriptor: int) -> str:
        digest = hashlib.sha256()
        while chunk := os.read(descriptor, 1 << 20):
            digest.update(chunk)
        return digest.hexdigest()

    def _read_file(self, entry: _TreeEntry) -> str:
        """Hash one unique regular entry through a stable pinned descriptor."""

        if not stat.S_ISREG(entry.metadata.st_mode) or entry.metadata.st_nlink != 1:
            raise ComposeError(f"destination tree contains unsafe file: {entry.relative}")
        descriptor = self._open(entry.path, directory=False)
        try:
            _assert_descriptor_outside_raw(
                descriptor,
                f"destination tree file {entry.relative}",
            )
            opened = os.fstat(descriptor)
            self._require_stable_file(entry.metadata, opened, entry.relative)
            digest = self._digest_file(descriptor)
            self._require_stable_file(opened, os.fstat(descriptor), entry.relative)
            self._require_stable_file(
                opened,
                self._metadata(entry.path),
                entry.relative,
            )
            return digest
        except OSError as exc:
            raise ComposeError(f"destination tree file cannot be read: {entry.relative}") from exc
        finally:
            os.close(descriptor)

    def _scan_child_directory(self, entry: _TreeEntry) -> None:
        self.directories.add(entry.relative)
        child = self._open(entry.path, directory=True)
        try:
            opened = os.fstat(child)
            _assert_descriptor_outside_raw(
                child,
                f"destination tree directory {entry.relative}",
            )
            if _directory_identity(entry.metadata) != _directory_identity(opened):
                raise ComposeError(f"destination tree directory changed: {entry.relative}")
            self._scan_directory(child, entry.path.relative_parts)
            current = self._metadata(entry.path)
            if _directory_identity(opened) != _directory_identity(current):
                raise ComposeError(f"destination tree directory changed: {entry.relative}")
        finally:
            os.close(child)

    def _scan_directory(
        self,
        descriptor: int,
        prefix: tuple[str, ...],
    ) -> None:
        for name in _fresh_directory_names(descriptor, "destination tree"):
            path = _TreePath(descriptor, name, (*prefix, name))
            entry = _TreeEntry(path, self._metadata(path))
            if stat.S_ISDIR(entry.metadata.st_mode):
                self._scan_child_directory(entry)
            elif stat.S_ISREG(entry.metadata.st_mode):
                self.digests[entry.relative] = self._read_file(entry)
            else:
                raise ComposeError(f"destination tree contains unsafe entry: {entry.relative}")

    def capture(self, descriptor: int) -> tuple[frozenset[str], dict[str, str]]:
        self._scan_directory(descriptor, ())
        return frozenset(self.directories), self.digests


def _tree_snapshot(descriptor: int) -> tuple[frozenset[str], dict[str, str]]:
    return _DestinationTreeSnapshot().capture(descriptor)


@dataclass(frozen=True)
class DirectoryBinding:
    """The path and descriptor observations for one pinned directory."""

    metadata: os.stat_result
    opened: os.stat_result
    resolved: Path
    absolute: Path
    expected_identity: tuple[int, int, int] | None = None

    def matches(self) -> bool:
        """Whether every observation still identifies the expected directory."""

        opened_identity = _directory_identity(self.opened)
        checks = (
            stat.S_ISDIR(self.metadata.st_mode),
            stat.S_ISDIR(self.opened.st_mode),
            self.resolved == self.absolute,
            _directory_identity(self.metadata) == opened_identity,
            (self.expected_identity is None or opened_identity == self.expected_identity),
        )
        return all(checks)


def directory_binding_matches(binding: DirectoryBinding) -> bool:
    """Return whether one captured path-to-descriptor binding still holds."""

    return binding.matches()


def _verify_directory_binding(
    path: Path,
    descriptor: int,
    label: str,
    *,
    expected_identity: tuple[int, int, int] | None = None,
) -> None:
    """Require ``path`` and a pinned descriptor to name the same directory."""

    try:
        metadata, resolved = _directory_observations(path)
        binding = DirectoryBinding(
            metadata=metadata,
            opened=os.fstat(descriptor),
            resolved=resolved,
            absolute=Path(os.path.abspath(path)),
            expected_identity=expected_identity,
        )
    except (OSError, RuntimeError) as exc:
        raise ComposeError(f"{label} changed while it was pinned: {path}") from exc
    if not binding.matches():
        raise ComposeError(f"{label} changed while it was pinned: {path}")


def _descriptor_path(descriptor: int, label: str) -> Path:
    try:
        current_path = os.readlink(f"/proc/self/fd/{descriptor}")
    except OSError as exc:
        raise ComposeError(
            f"{label}: cannot verify descriptor outside immutable raw evidence"
        ) from exc
    return Path(current_path)


def _descriptor_aliases_raw(descriptor_path: Path, label: str) -> bool:
    try:
        descriptor_path.resolve(strict=True)
        descriptor_path.stat()
        return _path_aliases_raw(descriptor_path)
    except (OSError, RuntimeError) as exc:
        raise ComposeError(
            f"{label}: cannot verify descriptor outside immutable raw evidence"
        ) from exc


def _assert_descriptor_outside_raw(descriptor: int, label: str) -> None:
    """Require the kernel's current descriptor path to remain outside raw."""

    descriptor_path = _descriptor_path(descriptor, label)
    if _contains_raw_segments(tuple(descriptor_path.parts)):
        raise ComposeError(f"{label}: destination was relocated into immutable raw evidence")
    if _descriptor_aliases_raw(descriptor_path, label):
        raise ComposeError(f"{label}: destination was relocated into immutable raw evidence")


def _assert_descriptor_contained(root_descriptor: int, descriptor: int, label: str) -> None:
    """Require a pinned component to remain below its destination root."""

    try:
        root_path = Path(os.readlink(f"/proc/self/fd/{root_descriptor}"))
        current_path = Path(os.readlink(f"/proc/self/fd/{descriptor}"))
    except OSError:
        return
    if current_path == root_path:
        return
    if root_path in current_path.parents:
        return
    raise ComposeError(f"{label}: component escaped its pinned destination root")


@dataclass
class PinnedDestination:
    """A new destination held by directory descriptors until commit or cleanup."""

    path: Path
    root: Path
    parent_descriptor: int
    destination_descriptor: int
    parent_identity: tuple[int, int, int]
    destination_identity: tuple[int, int, int]
    staged_name: str | None = None
    expected_directories: set[str] = field(default_factory=set, repr=False)
    expected_digests: dict[str, str] = field(default_factory=dict, repr=False)
    closed: bool = False

    def expect_directory(self, relative: str) -> None:
        """Record one directory that may appear in the committed topology."""

        self.expected_directories.add(relative)

    def expect_file(self, relative: str, digest: str) -> None:
        """Record one exact file digest and all of its parent directories."""

        path = PurePosixPath(relative)
        for parent in reversed(path.parents):
            if parent != PurePosixPath("."):
                self.expected_directories.add(parent.as_posix())
        self.expected_digests[relative] = digest

    def _authenticate_expected_tree(self) -> None:
        directories, digests = _tree_snapshot(self.destination_descriptor)
        if directories != frozenset(self.expected_directories):
            raise ComposeError("destination tree directory set changed before commit")
        if digests != self.expected_digests:
            raise ComposeError("destination tree bytes or member set changed before commit")

    def _verify_parent(self) -> None:
        _assert_descriptor_outside_raw(
            self.parent_descriptor,
            DESTINATION_PARENT_LABEL,
        )
        _verify_directory_binding(
            self.path.parent,
            self.parent_descriptor,
            DESTINATION_PARENT_LABEL,
            expected_identity=self.parent_identity,
        )

    def _verify_staged_entry(self) -> None:
        if self.staged_name is None:
            raise ComposeError("destination is not staged for commit")
        if (
            _entry_identity(
                self.parent_descriptor,
                self.staged_name,
            )
            != self.destination_identity
        ):
            raise ComposeError("destination changed while it was pinned")
        if _directory_identity(os.fstat(self.destination_descriptor)) != (
            self.destination_identity
        ):
            raise ComposeError("destination changed while it was pinned")

    def verify_binding(self) -> None:
        """Require both descriptors to retain their original path bindings."""

        if self.closed:
            raise ComposeError(DESTINATION_PIN_CLOSED)
        _assert_descriptor_outside_raw(self.destination_descriptor, "destination")
        self._verify_parent()
        if self.staged_name is not None:
            self._verify_staged_entry()
            return
        _verify_directory_binding(
            self.path,
            self.destination_descriptor,
            "destination",
            expected_identity=self.destination_identity,
        )

    def cleanup(self) -> None:
        """Detach only this transaction; never delete a public name."""

        if self.closed:
            return
        try:
            if self.staged_name is None:
                self.staged_name = _quarantine_owned_entry(
                    self.parent_descriptor,
                    self.path.name,
                    self.destination_identity,
                    "destination rollback",
                )
        finally:
            os.close(self.destination_descriptor)
            os.close(self.parent_descriptor)
            self.closed = True

    def begin_commit(self) -> None:
        """Atomically detach the destination before final authentication."""

        if self.closed:
            raise ComposeError(DESTINATION_PIN_CLOSED)
        if self.staged_name is not None:
            self.verify_binding()
            return
        self.verify_binding()
        self.staged_name = _stage_owned_entry(
            self.parent_descriptor,
            self.path.name,
            self.destination_identity,
            "destination commit",
        )
        self._verify_staged_entry()

    def _publish_staged(self) -> None:
        if self.staged_name is None:
            raise ComposeError("destination is not staged for commit")
        staged_name = self.staged_name
        try:
            _rename_noreplace(
                self.parent_descriptor,
                staged_name,
                self.path.name,
            )
        except OSError as exc:
            raise ComposeError(f"destination publication failed: {exc}") from exc
        self.staged_name = None
        if (
            _entry_identity(
                self.parent_descriptor,
                self.path.name,
            )
            != self.destination_identity
        ):
            _quarantine_owned_entry(
                self.parent_descriptor,
                self.path.name,
                self.destination_identity,
                "destination publication rollback",
            )
            raise ComposeError("published destination identity changed")

    def finish(self) -> None:
        """Verify lexical bindings survived, then release the descriptors."""

        if self.closed:
            raise ComposeError(DESTINATION_PIN_CLOSED)
        try:
            if self.staged_name is None:
                self.begin_commit()
            self.verify_binding()
            self._authenticate_expected_tree()
            self._publish_staged()
            self._authenticate_expected_tree()
            self.verify_binding()
        except BaseException:
            self.cleanup()
            raise
        os.close(self.destination_descriptor)
        os.close(self.parent_descriptor)
        self.closed = True


def _destination_descriptor(target: int | PinnedDestination) -> int:
    """Return the root descriptor carried by a raw or fully bound target."""

    if isinstance(target, PinnedDestination):
        return target.destination_descriptor
    return target


def _verify_destination_target(target: int | PinnedDestination) -> None:
    """Reject relocation when the caller retained the complete root binding."""

    if isinstance(target, PinnedDestination):
        _assert_descriptor_outside_raw(target.destination_descriptor, "destination")
        target.verify_binding()


if __package__:
    _expose_package_sibling(__name__)
