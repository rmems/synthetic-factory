"""Bounded JSONL output through authenticated staging descriptors."""

import errno
import hashlib
import os
import stat
from pathlib import Path

from . import canon
from .import_twins import bind_import_twin


def _open_directory(parent_fd, name):
    return os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent_fd)


def _output_descriptor(path, root_fd):
    """Create output through pinned, non-symlink directory descriptors."""
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("staging output must be a contained relative path")
    parent = os.dup(root_fd)
    try:
        for component in path.parts[:-1]:
            try:
                os.mkdir(component, mode=0o700, dir_fd=parent)
            except FileExistsError:
                pass
            child = _open_directory(parent, component)
            os.close(parent)
            parent = child
        return os.open(
            path.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o600, dir_fd=parent,
        )
    finally:
        os.close(parent)


def write_jsonl(path, records, *, root_fd=None):
    owned_root = root_fd is None
    if owned_root:
        path.parent.mkdir(parents=True, exist_ok=True)
        root_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        path = Path(path.name)
    try:
        descriptor = _output_descriptor(path, root_fd)
        digest = hashlib.sha256()
        size = 0
        with os.fdopen(descriptor, "wb") as output:
            for item in records:
                encoded = (canon.dumps_record(item) + "\n").encode("utf-8")
                output.write(encoded)
                digest.update(encoded)
                size += len(encoded)
        return digest.hexdigest(), size
    finally:
        if owned_root:
            os.close(root_fd)


def _bounded_digest(payload, limit):
    digest = hashlib.sha256()
    remaining = limit
    while chunk := payload.read(min(65536, remaining + 1)):
        remaining -= len(chunk)
        if remaining < 0:
            raise OSError(errno.EFBIG, "staging payload exceeds the byte limit")
        digest.update(chunk)
    return digest.hexdigest()


def _file_identity(state):
    return (state.st_dev, state.st_ino, state.st_mode, state.st_size,
            state.st_mtime_ns, state.st_ctime_ns, state.st_nlink)


def _authenticated_digest(parent_fd, name, limit):
    descriptor = os.open(
        name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent_fd
    )
    with os.fdopen(descriptor, "rb") as payload:
        before = os.fstat(payload.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
            raise OSError(errno.EINVAL, "staging entry must be a singly linked regular file")
        digest = _bounded_digest(payload, limit)
        after = os.fstat(payload.fileno())
        named = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        if not (_file_identity(before) == _file_identity(after) == _file_identity(named)):
            raise OSError(errno.ESTALE, "staging entry changed during authentication")
    return digest


def _verify_staged_manifest(root_fd, expected):
    actual_digest = _authenticated_digest(root_fd, "manifest.json", len(expected))
    if actual_digest != hashlib.sha256(expected).hexdigest():
        raise OSError(errno.ESTALE, "staging manifest changed before publication")


def _verify_staged_payloads(root_fd, files, max_bytes):
    """Refuse replaced family directories or payloads before publication."""
    for relative, expected in files.items():
        path = Path(relative)
        family_fd = _open_directory(root_fd, path.parent)
        try:
            digest = _authenticated_digest(family_fd, path.name, max_bytes)
            if digest != expected["sha256"]:
                raise OSError(errno.ESTALE, "staging payload changed before publication")
        finally:
            os.close(family_fd)

    _verify_staged_membership(root_fd, files)


def _verify_directory_members(descriptor, files, directories=()):
    expected = set(files) | set(directories)
    before = os.fstat(descriptor)
    # A fresh open-file description starts at the beginning; dup() would share
    # the caller's directory offset on filesystems that retain scan position.
    scan_fd = _open_directory(descriptor, ".")
    try:
        found = _collect_directory_members(scan_fd, expected, directories)
    finally:
        os.close(scan_fd)
    if found != expected:
        raise OSError(errno.ESTALE, "staging members missing before publication")
    _require_same_directory(before, os.fstat(descriptor))


def _collect_directory_members(descriptor, expected, directories):
    found = set()
    with os.scandir(descriptor) as entries:
        for entry in entries:
            if entry.name not in expected:
                raise OSError(errno.ESTALE, "undeclared staging entry before publication")
            _verify_member_type(entry, directories)
            found.add(entry.name)
    return found


def _require_same_directory(before, after):
    if _file_identity(before) != _file_identity(after):
        raise OSError(errno.ESTALE, "staging directory changed during membership check")


def _verify_member_type(entry, directories):
    state = entry.stat(follow_symlinks=False)
    if entry.name in directories:
        valid = stat.S_ISDIR(state.st_mode)
    else:
        valid = stat.S_ISREG(state.st_mode) and state.st_nlink == 1
    if not valid:
        raise OSError(errno.EINVAL, "staging member has unexpected type or links")


def _verify_family_members(root_fd, family, names):
    descriptor = _open_directory(root_fd, family)
    try:
        _verify_directory_members(descriptor, names)
        opened = os.fstat(descriptor)
        named = os.stat(family, dir_fd=root_fd, follow_symlinks=False)
        _require_same_directory(opened, named)
    finally:
        os.close(descriptor)


def _expected_family_members(files):
    families = {}
    for relative in files:
        path = Path(relative)
        if len(path.parts) != 2:
            raise OSError(errno.EINVAL, "unexpected staging payload layout")
        if path.is_absolute() or ".." in path.parts:
            raise OSError(errno.EINVAL, "unexpected staging payload layout")
        families.setdefault(path.parts[0], set()).add(path.name)
    return families


def _verify_staged_membership(root_fd, files):
    families = _expected_family_members(files)
    before = os.fstat(root_fd)
    _verify_directory_members(root_fd, {"manifest.json"}, families)
    for family, names in families.items():
        _verify_family_members(root_fd, family, names)
    _require_same_directory(before, os.fstat(root_fd))


bind_import_twin(__name__)
