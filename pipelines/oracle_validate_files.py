"""Authenticated byte capture for oracle-run validation.

Everything the validator later reasons about is captured here exactly once,
through pinned file descriptors that refuse symlinks, hard links, and
mid-read swaps. A file that cannot be captured faithfully is a finding, not
a fallback: validation fails closed on the bytes it could not authenticate.

This module also owns the run-wide limits and the strict JSON reader, so the
capture layer and the record layer agree on what "too big" and "ambiguous"
mean.
"""

import json
import math
import os
import stat
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

MAX_MANIFEST_BYTES = 8 * 1024 * 1024
MAX_JSONL_BYTES = 64 * 1024 * 1024
MAX_RUN_FILES = 10_000
MAX_RUN_ENTRIES = 20_000
MAX_RUN_DEPTH = 32
MAX_RUN_BYTES = 128 * 1024 * 1024
MAX_RUN_RECORDS = 100_000
MAX_ROUND = 99_999_999
READ_CHUNK_BYTES = 1024 * 1024


def _cli_settings():
    """The ``oracle_validate`` facade module, resolved at call time.

    The CLI re-exports the run limits and the snapshot capture; tests pin
    behaviour by patching those names on the facade, so the walk consults
    them through the facade instead of binding import-time copies.
    """
    import oracle_validate

    return oracle_validate


class DuplicateJsonKey(ValueError):
    """A JSON object repeated a key and was therefore ambiguous."""


def _object_from_pairs(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise DuplicateJsonKey(f"duplicate JSON key {key!r}")
        value[key] = item
    return value


def _reject_constant(value):
    raise ValueError(f"non-finite JSON token {value!r}")


def _parse_finite_float(text):
    """parse_constant only sees the bare NaN/Infinity tokens; a numeric
    literal that merely overflows to inf (1e400) must be refused here."""
    parsed = float(text)
    if not math.isfinite(parsed):
        raise ValueError(f"JSON numeric literal is not finitely representable: {text}")
    return parsed


def strict_json_loads(text):
    value = json.loads(
        text,
        object_pairs_hook=_object_from_pairs,
        parse_constant=_reject_constant,
        parse_float=_parse_finite_float,
    )
    return value


@dataclass(frozen=True)
class FileSnapshot:
    """One authenticated regular file captured exactly once."""

    path: Path
    relative: str
    body: bytes | bytearray
    device: int
    inode: int


def _manifest_path_text_ok(value):
    """Whether a manifest path is a plain nonempty string without backslashes."""
    if not isinstance(value, str) or not value:
        return False
    return "\\" not in value


def _manifest_path_shape_ok(path, value):
    """Whether an already-parsed manifest path is relative, plain, and JSONL."""
    if path.is_absolute():
        return False
    if any(part in ("", ".", "..") for part in path.parts):
        return False
    return path.as_posix() == value and path.suffix == ".jsonl"


def _safe_manifest_path(value):
    if not _manifest_path_text_ok(value):
        return None
    path = PurePosixPath(value)
    if not _manifest_path_shape_ok(path, value):
        return None
    return path


def _plain_int(value, *, minimum=None, maximum=None):
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and (minimum is None or value >= minimum)
        and (maximum is None or value <= maximum)
    )


def _open_beneath(root_fd, relative):
    """Open one regular-file candidate without following any path component."""
    parts = PurePosixPath(relative).parts
    if not parts or any(part in ("", ".", "..") for part in parts):
        raise ValueError("snapshot path is not a safe relative path")
    directory_fd = os.dup(root_fd)
    directory_flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        for part in parts[:-1]:
            next_fd = os.open(part, directory_flags, dir_fd=directory_fd)
            os.close(directory_fd)
            directory_fd = next_fd
        file_flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
        return os.open(parts[-1], file_flags, dir_fd=directory_fd)
    finally:
        os.close(directory_fd)


def _stat_identity(status):
    """The fields that must not change while a file's bytes are captured."""
    return (
        status.st_dev,
        status.st_ino,
        status.st_size,
        status.st_mtime_ns,
        status.st_ctime_ns,
        status.st_nlink,
    )


def _stat_identity_with_mode(status):
    """``_stat_identity`` plus the mode, for the pre-read enumeration check."""
    return (
        status.st_dev,
        status.st_ino,
        status.st_mode,
        status.st_size,
        status.st_mtime_ns,
        status.st_ctime_ns,
        status.st_nlink,
    )


def _read_within_limit(descriptor, limit):
    """Read a descriptor to EOF, refusing anything past ``limit`` bytes."""
    body = bytearray()
    captured = 0
    while True:
        chunk = os.read(descriptor, min(READ_CHUNK_BYTES, limit + 1 - captured))
        if not chunk:
            break
        try:
            body.extend(chunk)
        except MemoryError as exc:
            raise ValueError("snapshot allocation exceeded available memory") from exc
        captured += len(chunk)
        if captured > limit:
            raise ValueError(f"file exceeds the {limit}-byte snapshot limit")
    return body


def _capture_pinned_body(descriptor, limit, expected_stat):
    """Read one pinned descriptor, proving its identity before the read."""
    before = os.fstat(descriptor)
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
        raise ValueError("opened object is not a singly linked regular file")
    if _stat_identity_with_mode(before) != _stat_identity_with_mode(expected_stat):
        raise ValueError("file changed after run-tree enumeration")
    body = _read_within_limit(descriptor, limit)
    return body, before, os.fstat(descriptor)


@dataclass(frozen=True)
class _CapturePin:
    """The byte limit and pre-enumeration identity one capture must honour."""

    limit: int
    expected_stat: object


def _snapshot_regular_file(root_fd, path, relative, pin):
    """Capture one root-relative path once and detect identity or byte changes."""
    path = Path(path)
    if pin.expected_stat.st_size > pin.limit:
        raise ValueError(f"file exceeds the {pin.limit}-byte snapshot limit")
    descriptor = _open_beneath(root_fd, relative)
    try:
        body, before, after = _capture_pinned_body(descriptor, pin.limit, pin.expected_stat)
    finally:
        os.close(descriptor)
    if _stat_identity(before) != _stat_identity(after):
        raise ValueError("file changed while its bytes were captured")
    if len(body) != after.st_size:
        raise ValueError("captured byte count does not match the regular-file size")
    return FileSnapshot(
        path=path,
        relative=relative,
        body=body,
        device=after.st_dev,
        inode=after.st_ino,
    )


@dataclass
class _RunTreeWalk:
    """Accumulated state for one depth-first run-tree enumeration.

    ``stack`` owns an open descriptor per queued directory; the caller is
    responsible for closing whatever remains on it.
    """

    root: Path
    stack: list = field(default_factory=list)
    files: dict = field(default_factory=dict)
    errors: list = field(default_factory=list)
    entries_seen: int = 0
    bytes_seen: int = 0
    directory_fd: int = -1

    def report(self, relative, message):
        """Record one finding against a run-relative path."""
        self.errors.append(f"{self.root / relative}: {message}")


def _record_regular_file(entry_stat, relative, walk):
    """Record one regular file. True when a run-wide limit halts the walk."""
    limits = _cli_settings()
    if entry_stat.st_nlink != 1:
        walk.report(relative, "hard-linked files are not allowed in a run")
    walk.files[relative] = (walk.root / relative, entry_stat)
    walk.bytes_seen += entry_stat.st_size
    if walk.bytes_seen > limits.MAX_RUN_BYTES:
        walk.errors.append(
            f"{walk.root}: run exceeds the {limits.MAX_RUN_BYTES}-byte snapshot limit"
        )
        return True
    if len(walk.files) > limits.MAX_RUN_FILES:
        walk.errors.append(f"{walk.root}: run contains more than {limits.MAX_RUN_FILES} files")
        return True
    return False


def _push_subdirectory(entry, entry_stat, relative_path, walk):
    """Open a child directory without following links and queue it."""
    relative = relative_path.as_posix()
    depth_cap = _cli_settings().MAX_RUN_DEPTH
    if len(relative_path.parts) > depth_cap:
        walk.report(relative, f"run nesting exceeds {depth_cap} directories")
        return
    flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        child_fd = os.open(entry.name, flags, dir_fd=walk.directory_fd)
        child_stat = os.fstat(child_fd)
    except OSError as exc:
        walk.report(relative, f"could not open directory safely: {type(exc).__name__}")
        return
    if (child_stat.st_dev, child_stat.st_ino) != (entry_stat.st_dev, entry_stat.st_ino):
        os.close(child_fd)
        walk.report(relative, "directory changed during enumeration")
        return
    walk.stack.append((relative_path, child_fd))


def _scan_entry(entry, relative_path, walk):
    """Classify one directory entry. True when a run-wide limit halts the walk."""
    relative = relative_path.as_posix()
    try:
        entry_stat = entry.stat(follow_symlinks=False)
    except OSError as exc:
        walk.report(relative, f"could not inspect entry: {type(exc).__name__}")
        return False
    if stat.S_ISLNK(entry_stat.st_mode):
        walk.report(relative, "symbolic links are not allowed in a run")
        return False
    if stat.S_ISDIR(entry_stat.st_mode):
        _push_subdirectory(entry, entry_stat, relative_path, walk)
        return False
    if stat.S_ISREG(entry_stat.st_mode):
        return _record_regular_file(entry_stat, relative, walk)
    walk.report(relative, "only regular files and directories are allowed")
    return False


def _drain_entries(directory_fd, walk):
    """Drain one directory iterator under the run-wide entry cap.

    Enforce the entry cap while draining the iterator: sorting first would
    materialize an untrusted directory of arbitrary size before the cap
    could refuse it, so the walk never holds more than the cap allows.
    """
    entry_cap = _cli_settings().MAX_RUN_ENTRIES
    entries = []
    with os.scandir(directory_fd) as iterator:
        for entry in iterator:
            walk.entries_seen += 1
            if walk.entries_seen > entry_cap:
                walk.errors.append(f"{walk.root}: run contains more than {entry_cap} entries")
                return entries, True
            entries.append(entry)
    return entries, False


def _scan_directory(prefix, directory_fd, walk):
    """Scan one directory level. True when a run-wide limit halts the walk."""
    walk.directory_fd = directory_fd
    entries, halted = _drain_entries(directory_fd, walk)
    if halted:
        return True
    entries.sort(key=lambda item: item.name)
    for entry in entries:
        if _scan_entry(entry, prefix / entry.name, walk):
            return True
    return False


def _enumerate_run_files(run_dir, root_fd):
    """List one opened run tree without following directory links."""
    walk = _RunTreeWalk(root=Path(run_dir))
    walk.stack.append((PurePosixPath(), os.dup(root_fd)))
    try:
        while walk.stack:
            prefix, directory_fd = walk.stack.pop()
            halted = False
            try:
                halted = _scan_directory(prefix, directory_fd, walk)
            except OSError as exc:
                walk.errors.append(
                    f"{walk.root / prefix}: could not enumerate directory: {type(exc).__name__}"
                )
            finally:
                os.close(directory_fd)
            if halted:
                return walk.files, walk.errors
    finally:
        for _prefix, descriptor in walk.stack:
            os.close(descriptor)
    return walk.files, walk.errors


def _open_run_root(run_dir):
    """Open and pin a real run directory without accepting a root symlink."""
    root = Path(run_dir)
    before = os.lstat(root)
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISDIR(before.st_mode):
        raise ValueError("run directory must be a real directory, not a link")
    flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    descriptor = os.open(root, flags)
    opened = os.fstat(descriptor)
    if (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
        os.close(descriptor)
        raise ValueError("run directory changed while it was opened")
    return descriptor
