#!/usr/bin/env python3
"""Filesystem safety for compose: exact source reads, pinned destination writes.

Split out of ``compose_curated.py`` by responsibility. Nothing here decides
curation; it reads source members without symlink or hard-link aliases,
creates one brand-new destination behind pinned descriptors, and writes new
files without ever resolving a component another process could swap.
"""

from __future__ import annotations

import os
import shutil
import stat
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from compose_contract import ComposeError, sha256_hex  # noqa: E402
from round_txn import committed_jsonl_paths, marker_mode_path  # noqa: E402

def _contains_raw_segments(parts: tuple[str, ...]) -> bool:
    return any(
        parts[index : index + 2] == ("outputs", "raw") for index in range(len(parts) - 1)
    )


def _is_under_raw(path: Path) -> bool:
    """Reject lexical raw aliases as well as symlink-resolved raw paths."""

    return _contains_raw_segments(path.parts) or _contains_raw_segments(
        path.resolve(strict=False).parts
    )


def _require_exact_directory(path: Path, label: str) -> Path:
    """Require a real directory reached without a symlinked path alias."""

    try:
        metadata = path.lstat()
        resolved = path.resolve(strict=True)
    except FileNotFoundError as exc:
        raise ComposeError(f"{label} is missing: {path}") from exc
    absolute = Path(os.path.abspath(path))
    if not stat.S_ISDIR(metadata.st_mode) or resolved != absolute:
        raise ComposeError(f"{label} must be an exact non-symlink directory: {path}")
    return resolved


def _directory_identity(metadata: os.stat_result) -> tuple[int, int, int]:
    """Identity fields that do not change when directory entries are added."""

    return metadata.st_dev, metadata.st_ino, stat.S_IFMT(metadata.st_mode)


def _directory_binding_matches(
    metadata: os.stat_result,
    opened: os.stat_result,
    resolved: Path,
    absolute: Path,
    expected_identity: tuple[int, int, int] | None,
) -> bool:
    """Whether a path and its pinned descriptor still name one directory."""

    if not stat.S_ISDIR(metadata.st_mode) or not stat.S_ISDIR(opened.st_mode):
        return False
    if resolved != absolute:
        return False
    opened_identity = _directory_identity(opened)
    if _directory_identity(metadata) != opened_identity:
        return False
    return expected_identity is None or opened_identity == expected_identity


def _verify_directory_binding(
    path: Path,
    descriptor: int,
    label: str,
    *,
    expected_identity: tuple[int, int, int] | None = None,
) -> None:
    """Require ``path`` and a pinned descriptor to name the same directory."""

    try:
        metadata = path.lstat()
        resolved = path.resolve(strict=True)
        opened = os.fstat(descriptor)
    except (FileNotFoundError, OSError) as exc:
        raise ComposeError(f"{label} changed while it was pinned: {path}") from exc

    if not _directory_binding_matches(
        metadata,
        opened,
        resolved,
        Path(os.path.abspath(path)),
        expected_identity,
    ):
        raise ComposeError(f"{label} changed while it was pinned: {path}")


@dataclass
class PinnedDestination:
    """A new destination held by directory descriptors until commit or cleanup."""

    path: Path
    root: Path
    parent_descriptor: int
    destination_descriptor: int
    parent_identity: tuple[int, int, int]
    destination_identity: tuple[int, int, int]
    closed: bool = False

    def _entry_is_ours(self) -> bool:
        try:
            current = os.stat(
                self.path.name,
                dir_fd=self.parent_descriptor,
                follow_symlinks=False,
            )
        except (FileNotFoundError, OSError):
            return False
        return (
            stat.S_ISDIR(current.st_mode)
            and _directory_identity(current) == self.destination_identity
        )

    def cleanup(self) -> None:
        """Remove only the directory created through the pinned parent."""

        if self.closed:
            return
        os.close(self.destination_descriptor)
        if self._entry_is_ours():
            shutil.rmtree(
                self.path.name,
                ignore_errors=True,
                dir_fd=self.parent_descriptor,
            )
        os.close(self.parent_descriptor)
        self.closed = True

    def finish(self) -> None:
        """Verify the lexical bindings survived, then release the descriptors."""

        if self.closed:
            raise ComposeError("destination pin was already closed")
        try:
            _verify_directory_binding(
                self.path.parent,
                self.parent_descriptor,
                "destination parent",
                expected_identity=self.parent_identity,
            )
            _verify_directory_binding(
                self.path,
                self.destination_descriptor,
                "destination",
                expected_identity=self.destination_identity,
            )
        except BaseException:
            self.cleanup()
            raise
        os.close(self.destination_descriptor)
        os.close(self.parent_descriptor)
        self.closed = True


def _validated_member_relative(raw_path: Any, label: str) -> PurePosixPath:
    """Reject anything that is not a plain, in-tree POSIX relative path."""

    if not isinstance(raw_path, str) or not raw_path or "\\" in raw_path:
        raise ComposeError(f"{label}: path must be a nonempty POSIX string")
    relative = PurePosixPath(raw_path)
    if (
        relative.as_posix() != raw_path
        or relative.is_absolute()
        or any(part in {"", ".", ".."} for part in relative.parts)
    ):
        raise ComposeError(f"{label}: unsafe relative path {raw_path!r}")
    return relative


def _assert_unaliased_regular_member(
    metadata: os.stat_result, *, label: str, raw_path: Any
) -> None:
    """A source member must be exactly one regular file, not an alias of one."""

    if not stat.S_ISREG(metadata.st_mode):
        raise ComposeError(f"{label}: source member is not a regular file: {raw_path}")
    if metadata.st_nlink != 1:
        raise ComposeError(f"{label}: hard-link aliases are not accepted: {raw_path}")


def _source_member_path(root: Path, raw_path: Any, label: str) -> Path:
    """Resolve one exact regular source member without aliases or tree escape."""

    relative = _validated_member_relative(raw_path, label)
    root_resolved = root.resolve(strict=True)
    candidate = root_resolved.joinpath(*relative.parts)
    try:
        resolved = candidate.resolve(strict=True)
        metadata = candidate.lstat()
    except FileNotFoundError as exc:
        raise ComposeError(f"{label}: source member is missing: {raw_path}") from exc
    expected = root_resolved.joinpath(*relative.parts)
    if resolved != expected or root_resolved not in resolved.parents:
        raise ComposeError(f"{label}: source member is a symlink alias: {raw_path}")
    _assert_unaliased_regular_member(metadata, label=label, raw_path=raw_path)
    return candidate


def _stable_file_identity(metadata: os.stat_result) -> tuple[int, ...]:
    """Fields that must remain stable while one source member is read."""

    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_mode,
        metadata.st_nlink,
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
    )


def _drain_descriptor(descriptor: int) -> bytes:
    """Read one already-pinned descriptor to EOF without re-opening it."""

    chunks: list[bytes] = []
    while True:
        chunk = os.read(descriptor, 1024 * 1024)
        if not chunk:
            break
        chunks.append(chunk)
    return b"".join(chunks)


def _assert_opened_source_identity(
    before: os.stat_result, opened: os.stat_result, label: str
) -> None:
    """The descriptor we hold must be the file we stat-ed by path."""

    if not stat.S_ISREG(opened.st_mode):
        raise ComposeError(f"{label}: opened identity is not a regular file")
    if opened.st_nlink != 1:
        raise ComposeError(f"{label}: hard-link aliases are not accepted")
    if _stable_file_identity(before) != _stable_file_identity(opened):
        raise ComposeError(f"{label}: source identity changed while opening")


def _assert_source_path_unchanged(
    path: Path,
    root: Path,
    raw_path: Any,
    opened_after: os.stat_result | None,
    label: str,
) -> None:
    """After the read the path must still name that same unaliased file."""

    try:
        after = path.lstat()
    except FileNotFoundError as exc:
        raise ComposeError(f"{label}: source member disappeared while reading") from exc
    if opened_after is None or _stable_file_identity(after) != _stable_file_identity(
        opened_after
    ):
        raise ComposeError(f"{label}: source path identity changed while reading")
    expected = root.resolve(strict=True).joinpath(*PurePosixPath(str(raw_path)).parts)
    if path.resolve(strict=True) != expected:
        raise ComposeError(f"{label}: source path became a symlink alias while reading")


def _read_exact_regular_file(root: Path, raw_path: Any, label: str) -> tuple[Path, bytes]:
    """Read one unique source file through a pinned descriptor."""

    path = _source_member_path(root, raw_path, label)
    before = path.lstat()
    # O_NONBLOCK keeps a member swapped for a FIFO from hanging the open;
    # the identity check below then rejects it. Regular reads ignore the flag.
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | os.O_NONBLOCK
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise ComposeError(f"{label}: cannot open exact source file: {exc}") from exc

    try:
        opened_before = os.fstat(descriptor)
        _assert_opened_source_identity(before, opened_before, label)
        payload = _drain_descriptor(descriptor)
        opened_after = os.fstat(descriptor)
        if _stable_file_identity(opened_before) != _stable_file_identity(opened_after):
            raise ComposeError(f"{label}: source identity changed while reading")
    finally:
        os.close(descriptor)

    _assert_source_path_unchanged(path, root, raw_path, opened_after, label)
    return path, payload


def _open_pinned_child(
    name: str, parent_descriptor: int, label: str
) -> tuple[os.stat_result, int]:
    """Stat and open one child through its already-pinned parent descriptor."""

    try:
        before = os.stat(name, dir_fd=parent_descriptor, follow_symlinks=False)
        # O_NONBLOCK keeps a child swapped for a FIFO from hanging the open;
        # ``_read_pinned_child_bytes`` then rejects the opened identity.
        descriptor = os.open(
            name,
            os.O_RDONLY
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_CLOEXEC", 0)
            | os.O_NONBLOCK,
            dir_fd=parent_descriptor,
        )
    except OSError as exc:
        raise ComposeError(f"{label}: cannot open exact source file: {exc}") from exc
    return before, descriptor


def _read_pinned_child_bytes(
    name: str,
    parent_descriptor: int,
    file_descriptor: int,
    before: os.stat_result,
    label: str,
) -> bytes:
    """Read the opened child, proving its identity held across the read."""

    opened_before = os.fstat(file_descriptor)
    _assert_opened_source_identity(before, opened_before, label)
    payload = _drain_descriptor(file_descriptor)
    opened_after = os.fstat(file_descriptor)
    after = os.stat(name, dir_fd=parent_descriptor, follow_symlinks=False)
    if (
        _stable_file_identity(opened_before) != _stable_file_identity(opened_after)
        or _stable_file_identity(after) != _stable_file_identity(opened_after)
    ):
        raise ComposeError(f"{label}: source identity changed while reading")
    return payload


def _read_exact_child_file(parent: Path, name: str, label: str) -> tuple[Path, bytes]:
    """Read one direct child while its exact parent directory remains pinned."""

    parent = _require_exact_directory(parent, f"{label} parent")
    expected_parent_identity = _directory_identity(parent.lstat())
    directory_flags = (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    try:
        parent_descriptor = os.open(parent, directory_flags)
    except OSError as exc:
        raise ComposeError(f"{label} parent changed while it was pinned: {parent}") from exc

    file_descriptor: int | None = None
    try:
        # The parent identity is proved before the child is opened and again
        # after it is read, so a swapped directory cannot slip a different
        # file into the same name mid-read.
        _verify_directory_binding(
            parent,
            parent_descriptor,
            f"{label} parent",
            expected_identity=expected_parent_identity,
        )
        before, file_descriptor = _open_pinned_child(name, parent_descriptor, label)
        payload = _read_pinned_child_bytes(
            name, parent_descriptor, file_descriptor, before, label
        )
        _verify_directory_binding(
            parent,
            parent_descriptor,
            f"{label} parent",
            expected_identity=expected_parent_identity,
        )
        return parent / name, payload
    finally:
        if file_descriptor is not None:
            os.close(file_descriptor)
        os.close(parent_descriptor)


def _scan_source_directory(directory: Path) -> list[Any]:
    """List one source directory in a stable, name-sorted order."""

    try:
        with os.scandir(directory) as scan:
            return sorted(scan, key=lambda entry: entry.name)
    except OSError as exc:
        raise ComposeError(
            f"cannot enumerate source directory {directory}: {exc}"
        ) from exc


def _source_entry_metadata(entry: Any, path: Path) -> os.stat_result:
    """Stat one source entry without following, or accepting, an alias."""

    try:
        metadata = entry.stat(follow_symlinks=False)
    except OSError as exc:
        raise ComposeError(f"cannot inspect source member {path}: {exc}") from exc
    if stat.S_ISLNK(metadata.st_mode):
        raise ComposeError(f"source tree contains a symlink alias: {path}")
    return metadata


def _collect_source_directory(
    root: Path, directory: Path, members: list[str]
) -> list[Path]:
    """Append this directory's JSONL members; return its child directories."""

    child_directories: list[Path] = []
    for entry in _scan_source_directory(directory):
        path = Path(entry.path)
        metadata = _source_entry_metadata(entry, path)
        if entry.name.endswith(".jsonl"):
            relative = path.relative_to(root).as_posix()
            _source_member_path(root, relative, f"compose source {relative}")
            members.append(relative)
            continue
        if stat.S_ISDIR(metadata.st_mode):
            child_directories.append(path)
            continue
    return child_directories


def _round_visible_members(root: Path, members: list[str]) -> list[str]:
    """Keep only members the round-transaction contract exposes.

    Legacy factories without marker mode stay fully visible. Once an
    enclosing factory has entered marker mode, only the batches its committed
    round manifests name may contribute — the same visibility census and the
    training audit apply — so an uncommitted batch can neither compose into a
    ``training_ready`` tree nor authenticate through the export replay.
    """

    marker_roots: dict[Path, Path | None] = {}
    committed: dict[Path, set[Path]] = {}

    def enclosing_marker_root(parent: Path) -> Path | None:
        visited = []
        current = parent
        while True:
            if current in marker_roots:
                found = marker_roots[current]
                break
            visited.append(current)
            if marker_mode_path(current) is not None:
                found = current
                break
            if current == root or current.parent == current:
                found = None
                break
            current = current.parent
        for directory in visited:
            marker_roots[directory] = found
        return found

    visible: list[str] = []
    for relative in members:
        path = root.joinpath(*PurePosixPath(relative).parts)
        marker_root = enclosing_marker_root(path.parent)
        if marker_root is None:
            visible.append(relative)
            continue
        if marker_root not in committed:
            committed[marker_root] = {
                candidate.resolve()
                for candidate in committed_jsonl_paths(marker_root)
            }
        if path.resolve() in committed[marker_root]:
            visible.append(relative)
    return visible


def source_jsonl_members(root: Path) -> tuple[str, ...]:
    """Enumerate a source tree without silently following filesystem aliases."""

    root = _require_exact_directory(root, "source run")
    members: list[str] = []
    pending = [root]
    while pending:
        directory = pending.pop()
        if _require_exact_directory(directory, "source directory") != directory:
            raise ComposeError(f"source directory identity changed: {directory}")
        pending.extend(
            reversed(_collect_source_directory(root, directory, members))
        )
    return tuple(sorted(_round_visible_members(root, members)))


def _assert_destination_disjoint(
    resolved_source: Path, resolved_destination: Path
) -> None:
    """The destination may neither be, contain, nor sit inside the source run."""

    if resolved_source == resolved_destination:
        raise ComposeError("destination cannot replace the source run")
    if resolved_source in resolved_destination.parents:
        raise ComposeError("destination cannot be written inside the source run")
    if resolved_destination in resolved_source.parents:
        raise ComposeError("destination cannot contain the source run")


def _assert_new_destination(
    source_run: Path, destination: Path
) -> tuple[Path, tuple[int, int, int]]:
    if os.path.lexists(destination):
        raise ComposeError(f"refusing to overwrite an existing destination: {destination}")
    if _is_under_raw(destination):
        raise ComposeError(f"refusing to write inside immutable raw evidence: {destination}")
    _assert_destination_disjoint(
        source_run.resolve(), destination.resolve(strict=False)
    )
    parent = _require_exact_directory(destination.parent, "destination parent")
    return parent, _directory_identity(parent.lstat())


def _refuse_existing_destination(parent_descriptor: int, destination: Path) -> None:
    """Refuse a destination name that already exists under the pinned parent."""

    try:
        os.stat(
            destination.name,
            dir_fd=parent_descriptor,
            follow_symlinks=False,
        )
    except FileNotFoundError:
        return
    raise ComposeError(
        f"refusing to overwrite an existing destination: {destination}"
    )


def _pinned_root_path(destination_descriptor: int) -> Path:
    """Return the descriptor-addressed root every later write goes through."""

    root = Path(f"/proc/self/fd/{destination_descriptor}")
    if not root.is_dir():
        raise ComposeError("pinned destination descriptor is not path-addressable")
    return root


def _discard_created_destination(
    parent_descriptor: int,
    destination: Path,
    created_identity: tuple[int, int, int],
) -> None:
    """Remove a partly created destination, but only the one we created."""

    try:
        current = os.stat(
            destination.name,
            dir_fd=parent_descriptor,
            follow_symlinks=False,
        )
    except (FileNotFoundError, OSError):
        current = None
    if current is not None and _directory_identity(current) == created_identity:
        shutil.rmtree(
            destination.name,
            ignore_errors=True,
            dir_fd=parent_descriptor,
        )


def create_pinned_destination(
    source_run: Path, destination: Path
) -> PinnedDestination:
    """Create one exclusive destination relative to a pinned parent descriptor."""

    parent, expected_parent_identity = _assert_new_destination(
        source_run, destination
    )
    destination = Path(os.path.abspath(destination))
    flags = (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    parent_descriptor = os.open(parent, flags)
    destination_descriptor: int | None = None
    created_identity: tuple[int, int, int] | None = None
    try:
        _verify_directory_binding(
            parent,
            parent_descriptor,
            "destination parent",
            expected_identity=expected_parent_identity,
        )
        _refuse_existing_destination(parent_descriptor, destination)
        _assert_descriptor_outside_raw(parent_descriptor, "destination parent")
        os.mkdir(destination.name, 0o755, dir_fd=parent_descriptor)
        created = os.stat(
            destination.name,
            dir_fd=parent_descriptor,
            follow_symlinks=False,
        )
        created_identity = _directory_identity(created)
        if not stat.S_ISDIR(created.st_mode):
            raise ComposeError(f"new destination is not a directory: {destination}")
        destination_descriptor = os.open(
            destination.name,
            flags,
            dir_fd=parent_descriptor,
        )
        if _directory_identity(os.fstat(destination_descriptor)) != created_identity:
            raise ComposeError("destination identity changed while opening")
        return PinnedDestination(
            path=destination,
            root=_pinned_root_path(destination_descriptor),
            parent_descriptor=parent_descriptor,
            destination_descriptor=destination_descriptor,
            parent_identity=expected_parent_identity,
            destination_identity=created_identity,
        )
    except BaseException:
        if destination_descriptor is not None:
            os.close(destination_descriptor)
        if created_identity is not None:
            _discard_created_destination(
                parent_descriptor, destination, created_identity
            )
        os.close(parent_descriptor)
        raise


def _destination_write_parts(relative: Any, label: str) -> tuple[str, ...]:
    """Validate one destination-relative POSIX path used for a new file."""

    raw = relative.as_posix() if isinstance(relative, PurePosixPath) else relative
    if not isinstance(raw, str) or not raw or "\\" in raw:
        raise ComposeError(f"{label}: destination path must be a nonempty POSIX string")
    candidate = PurePosixPath(raw)
    non_canonical = candidate.as_posix() != raw or candidate.is_absolute()
    if non_canonical or any(part in {"", ".", ".."} for part in candidate.parts):
        raise ComposeError(f"{label}: unsafe destination path {raw!r}")
    return candidate.parts


def _open_pinned_child_directory(
    parent_descriptor: int, name: str, label: str
) -> int:
    """Create or reuse one child directory and pin it without following links.

    ``mkdir`` and the matching ``open`` are two syscalls, so a same-user
    process can replace the new child with a symlink in between.  Opening the
    component relative to its pinned parent with ``O_NOFOLLOW`` refuses that
    swap outright, and comparing the opened identity against the directory
    entry refuses a swap that lands between the two calls.
    """

    flags = (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    try:
        os.mkdir(name, 0o755, dir_fd=parent_descriptor)
    except FileExistsError:
        pass
    except OSError as exc:
        raise ComposeError(
            f"{label}: cannot create directory component {name!r}: {exc}"
        ) from exc
    try:
        descriptor = os.open(name, flags, dir_fd=parent_descriptor)
    except OSError as exc:
        raise ComposeError(
            f"{label}: directory component {name!r} is not an exact directory"
        ) from exc
    try:
        _verify_pinned_child(descriptor, parent_descriptor, name, label)
    except BaseException:
        os.close(descriptor)
        raise
    return descriptor


def _assert_descriptor_contained(
    root_descriptor: int, descriptor: int, label: str
) -> None:
    """Require a pinned component to remain below its pinned destination root.

    Descriptor-relative traversal follows an opened directory after a same-user
    rename.  That is useful for race-free identity checks, but without this
    containment check a renamed child could receive later components outside
    the destination tree.  Linux exposes the kernel's current bindings through
    ``/proc/self/fd``; on platforms without procfs the open-time guarantees
    remain the available fallback.
    """

    try:
        root_path = Path(os.readlink(f"/proc/self/fd/{root_descriptor}"))
        current_path = Path(os.readlink(f"/proc/self/fd/{descriptor}"))
    except OSError:  # pragma: no cover - non-procfs platforms
        return
    if current_path != root_path and root_path not in current_path.parents:
        raise ComposeError(f"{label}: component escaped its pinned destination root")


def _verify_pinned_child(
    descriptor: int, parent_descriptor: int, name: str, label: str
) -> None:
    """Require the opened child and its directory entry to be one directory."""

    entry = os.stat(name, dir_fd=parent_descriptor, follow_symlinks=False)
    opened = os.fstat(descriptor)
    entries_diverge = not stat.S_ISDIR(entry.st_mode) or not stat.S_ISDIR(
        opened.st_mode
    )
    if entries_diverge or _directory_identity(entry) != _directory_identity(opened):
        raise ComposeError(
            f"{label}: directory component {name!r} changed while it was pinned"
        )


def _create_pinned_new_directory(
    parent_descriptor: int, name: str, label: str
) -> None:
    """Create one child directory through its checked pinned parent.

    A same-user rename can move the pinned destination — and every descriptor
    under it — into ``outputs/raw`` after it was opened, so a ``mkdir``
    resolved through the descriptor would create directories inside immutable
    raw evidence. Refuse from the kernel's view of the descriptor first, then
    create and verify the component descriptor-relative, exactly like the
    pinned leaf writer.
    """

    _assert_descriptor_outside_raw(parent_descriptor, label)
    os.close(_open_pinned_child_directory(parent_descriptor, name, label))


def write_pinned_new_bytes(
    root_descriptor: int, relative: Any, payload: bytes, label: str = "destination"
) -> str:
    """Create one new file under a pinned root, pinning every component.

    Every intermediate directory is created and reopened relative to the
    descriptor above it, so no component of the write path is ever resolved
    through a name that another process can swap for a symlink.  The final
    file is created exclusively and never follows a link either, which keeps
    derived output from escaping into the immutable ``outputs/raw/`` tree.
    """

    parts = _destination_write_parts(relative, label)
    opened: list[int] = []
    current = root_descriptor
    try:
        for name in parts[:-1]:
            _assert_descriptor_contained(root_descriptor, current, label)
            _assert_descriptor_outside_raw(current, label)
            current = _open_pinned_child_directory(current, name, label)
            opened.append(current)
            _assert_descriptor_contained(root_descriptor, current, label)
        leaf = parts[-1]
        _assert_descriptor_contained(root_descriptor, current, label)
        _assert_descriptor_outside_raw(current, label)
        flags = (
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_CLOEXEC", 0)
        )
        try:
            descriptor = os.open(leaf, flags, 0o644, dir_fd=current)
        except OSError as exc:
            raise ComposeError(
                f"{label}: cannot create new file {parts[-1]!r}: {exc}"
            ) from exc
        try:
            _assert_descriptor_contained(root_descriptor, descriptor, label)
            written = 0
            while written < len(payload):
                written += os.write(descriptor, payload[written:])
            # A same-user rename can move the opened destination — and every
            # descriptor under it — into ``outputs/raw`` after the open. The
            # descriptor's current path is authoritative: refuse, and remove
            # the leaf through its pinned parent so nothing lands in raw.
            _assert_descriptor_contained(root_descriptor, descriptor, label)
            _assert_descriptor_outside_raw(descriptor, label)
        except BaseException:
            try:
                os.unlink(leaf, dir_fd=current)
            except OSError:
                pass
            raise
        finally:
            os.close(descriptor)
    finally:
        for descriptor in reversed(opened):
            os.close(descriptor)
    return sha256_hex(payload)


def _assert_descriptor_outside_raw(descriptor: int, label: str) -> None:
    """The pinned component must still live outside immutable raw evidence.

    Descriptor-relative opens keep following a directory that a same-user
    process renames, so an opened destination could be relocated under
    ``outputs/raw`` between its open and a leaf write. The kernel's view of
    the descriptor's current path is authoritative; where it is unavailable,
    the open-time guarantees still hold.
    """

    try:
        current_path = os.readlink(f"/proc/self/fd/{descriptor}")
    except OSError:  # pragma: no cover - non-procfs platforms
        return
    if _contains_raw_segments(tuple(PurePosixPath(current_path).parts)):
        raise ComposeError(
            f"{label}: destination was relocated into immutable raw evidence"
        )


def _write_new_text(root_descriptor: int, relative: Any, text: str) -> str:
    """Create one new destination file exclusively and hash its bytes."""

    return write_pinned_new_bytes(
        root_descriptor,
        relative,
        text.encode("utf-8"),
        f"destination {relative}",
    )
