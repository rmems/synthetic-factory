"""Pin an authenticated output parent before creating any replay directories."""

from __future__ import annotations

from contextlib import contextmanager
import os
from pathlib import Path

from ._contract import (
    CsvRefusal, FINDING_DESTINATION_INVALID, FINDING_DESTINATION_UNDER_RAW,
    bind_import_twin, is_under_raw,
)

FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC


def release_descriptor(descriptor: int) -> None:
    """Release once without replacing the publication outcome with cleanup errors."""
    try:
        os.close(descriptor)
    except OSError:
        # Linux releases the FD even on delayed close errors. Retrying can close
        # a reused descriptor; close is not a durability acknowledgement.
        pass


def _outside_raw(descriptor: int) -> Path:
    anchor = Path(f"/proc/self/fd/{descriptor}")
    _require_outside_raw(anchor)
    return anchor


def _require_outside_raw(anchor: Path) -> None:
    anchor.resolve(strict=True)
    if is_under_raw(anchor):
        raise CsvRefusal(FINDING_DESTINATION_UNDER_RAW, "pinned output parent aliases the raw tree")


def _existing_parent(parent: Path) -> tuple[int, list[str]]:
    missing = []
    while True:
        try:
            return os.open(parent, FLAGS), missing
        except FileNotFoundError:
            missing.append(parent.name)
            parent = parent.parent


def _open_child(descriptor: int, name: str) -> int:
    _outside_raw(descriptor)
    try:
        os.mkdir(name, dir_fd=descriptor)
    except FileExistsError:
        pass
    return os.open(name, FLAGS | os.O_NOFOLLOW, dir_fd=descriptor)


def _open_parent(parent: Path) -> int:
    descriptor, missing = _existing_parent(parent)
    try:
        _outside_raw(descriptor)
        for name in reversed(missing):
            child = _open_child(descriptor, name)
            release_descriptor(descriptor)
            descriptor = child
        _outside_raw(descriptor)
        return descriptor
    except BaseException:
        release_descriptor(descriptor)
        raise


def _required_parent(parent: Path) -> int:
    try:
        return _open_parent(parent)
    except (OSError, RuntimeError) as exc:
        raise CsvRefusal(FINDING_DESTINATION_INVALID, f"cannot pin output parent {parent}: {exc}") from exc


def verify_parent(destination: Path, anchor: Path) -> None:
    try:
        requested, pinned = destination.parent.stat(), anchor.stat()
    except OSError as exc:
        raise CsvRefusal(FINDING_DESTINATION_INVALID, "output parent is no longer accessible") from exc
    if (requested.st_dev, requested.st_ino) != (pinned.st_dev, pinned.st_ino):
        raise CsvRefusal(FINDING_DESTINATION_INVALID, "output parent changed during publication")
    _require_outside_raw(anchor)


@contextmanager
def pinned_parent(destination: Path):
    if is_under_raw(destination):
        raise CsvRefusal(FINDING_DESTINATION_UNDER_RAW, "output names or aliases the raw tree")
    descriptor = _required_parent(destination.parent)
    try:
        anchor = _outside_raw(descriptor)
        verify_parent(destination, anchor)
        yield anchor
    finally:
        release_descriptor(descriptor)


bind_import_twin(__name__)
