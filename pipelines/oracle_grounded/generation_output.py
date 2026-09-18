"""Bounded JSONL output through authenticated staging descriptors."""

import errno
import hashlib
import os
import stat
from pathlib import Path

from . import canon
from .import_twins import bind_import_twin


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
            child = os.open(
                component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent
            )
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


def _verify_staged_manifest(root_fd, expected):
    descriptor = os.open(
        "manifest.json", os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=root_fd
    )
    with os.fdopen(descriptor, "rb") as manifest:
        state = os.fstat(manifest.fileno())
        if not stat.S_ISREG(state.st_mode) or state.st_size != len(expected):
            raise OSError(errno.ESTALE, "staging manifest type or size changed")
        actual_digest = _bounded_digest(manifest, len(expected))
    if actual_digest != hashlib.sha256(expected).hexdigest():
        raise OSError(errno.ESTALE, "staging manifest changed before publication")


def _verify_staged_payloads(root_fd, files, max_bytes):
    """Refuse replaced family directories or payloads before publication."""
    for relative, expected in files.items():
        path = Path(relative)
        family_fd = os.open(
            path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=root_fd
        )
        try:
            descriptor = os.open(
                path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=family_fd
            )
            with os.fdopen(descriptor, "rb") as payload:
                if not stat.S_ISREG(os.fstat(payload.fileno()).st_mode):
                    raise OSError(errno.EINVAL, "staging payload is not a regular file")
                digest = _bounded_digest(payload, max_bytes)
            if digest != expected["sha256"]:
                raise OSError(errno.ESTALE, "staging payload changed before publication")
        finally:
            os.close(family_fd)


bind_import_twin(__name__)
