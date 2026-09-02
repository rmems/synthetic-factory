#!/usr/bin/env python3
"""No-replace renames and private owned-entry moves for pinned destinations."""

from __future__ import annotations

import ctypes
import errno
import os
import sys
import uuid
from dataclasses import dataclass

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("compose_destination_rename")
    from .compose_contract import ComposeError
    from .compose_destination_directory import _directory_identity
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "compose_destination_rename"
    )
    from compose_contract import ComposeError
    from compose_destination_directory import _directory_identity

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


if __package__:
    _expose_package_sibling(__name__)
