"""Serialize the view files and write them into a brand-new destination, or refuse.

Rows are serialized through ``exact_json`` one per line; ``VIEWS.json`` carries
the per-family counts, the refused record ids with their codes, the digest of
every authenticated source file the rows were projected from, and the digest of
every file written.

The destination must not name or alias ``outputs/raw/``. ``check_destination``
is an early, advisory refusal so a run is not read for nothing; the reservation
itself is authoritative. The parent is opened once, the destination is created
with a single ``mkdir`` through that descriptor (losing that race is the
existing-destination refusal), and the new directory is opened without
following links and checked again against the raw tree through its open
descriptor. Every file is then created exclusively through that pinned
descriptor, so replacing any path component after reservation cannot redirect a
write. A failed write removes only the entries this call created.
"""

from __future__ import annotations

import hashlib
import os
from contextlib import suppress
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import vocabulary as tv
from ._contract import bind_import_twin, dumps_exact_json, is_under_raw

__all__ = [
    "check_destination", "file_entries", "jsonl_bytes", "summary_bytes", "view_files",
    "write_new_tree",
]

_DIRECTORY_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
_FILE_FLAGS = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC
_DIRECTORY_MODE = 0o755
_FILE_MODE = 0o644


def check_destination(out: Path) -> None:
    """Refuse a destination that names the raw tree or already exists (advisory)."""

    tv.refuse_first(
        (
            (is_under_raw(out), tv.FINDING_DESTINATION_UNDER_RAW,
             "the destination names or aliases outputs/raw/"),
            (os.path.lexists(out), tv.FINDING_DESTINATION_EXISTS,
             f"the destination already exists: {out.name}"),
        )
    )


def jsonl_bytes(rows: list[dict[str, Any]]) -> bytes:
    """One exact-JSON row per line, in the order the rows were rendered."""

    return "".join(dumps_exact_json(row, sort_keys=False) + "\n" for row in rows).encode("utf-8")


def view_files(rows: dict[str, dict[str, list[dict[str, Any]]]]) -> dict[str, bytes]:
    """``<family>.<kind>.jsonl`` for every family and row kind, empty files included."""

    return {
        f"{family}.{kind}.jsonl": jsonl_bytes(by_kind[kind])
        for family, by_kind in rows.items()
        for kind in tv.ROW_KINDS
    }


def file_entries(files: dict[str, bytes]) -> dict[str, dict[str, Any]]:
    return {
        name: {
            "bytes": len(data),
            "rows": data.count(b"\n"),
            "sha256": hashlib.sha256(data).hexdigest(),
        }
        for name, data in files.items()
    }


def summary_bytes(summary: dict[str, Any]) -> bytes:
    return (dumps_exact_json(summary, sort_keys=True, indent=2) + "\n").encode("utf-8")


@dataclass
class _Reservation:
    """The pinned parent and new directory descriptors, and what this call created."""

    parent: int
    name: str
    directory: int = -1
    created: list[str] = field(default_factory=list)


def _write_failed(what: str, exc: OSError) -> tv.TextViewRefusal:
    return tv.TextViewRefusal(
        tv.FINDING_DESTINATION_WRITE_FAILED, f"{what} failed: {type(exc).__name__}"
    )


def _open_parent(parent: Path) -> int:
    try:
        parent.mkdir(parents=True, exist_ok=True)
        return os.open(parent, _DIRECTORY_FLAGS)
    except OSError as exc:
        raise _write_failed("opening the destination's parent", exc) from exc


def _make_directory(reservation: _Reservation) -> None:
    try:
        os.mkdir(reservation.name, _DIRECTORY_MODE, dir_fd=reservation.parent)
    except FileExistsError as exc:
        raise tv.TextViewRefusal(
            tv.FINDING_DESTINATION_EXISTS, f"the destination already exists: {reservation.name}"
        ) from exc
    except OSError as exc:
        raise _write_failed("creating the destination", exc) from exc


def _pinned_path(descriptor: int) -> Path:
    return Path(os.readlink(f"/proc/self/fd/{descriptor}"))


def _open_directory(reservation: _Reservation) -> None:
    try:
        reservation.directory = os.open(
            reservation.name, _DIRECTORY_FLAGS, dir_fd=reservation.parent
        )
        pinned = _pinned_path(reservation.directory)
    except OSError as exc:
        raise _write_failed("opening the reserved destination", exc) from exc
    tv.refuse_when(
        is_under_raw(pinned), tv.FINDING_DESTINATION_UNDER_RAW,
        "the reserved destination resolves into outputs/raw/",
    )


def _create(reservation: _Reservation, name: str, data: bytes) -> None:
    descriptor = os.open(name, _FILE_FLAGS, _FILE_MODE, dir_fd=reservation.directory)
    reservation.created.append(name)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(data)


def _roll_back(reservation: _Reservation) -> None:
    """Remove only the files and the directory this call created, through its descriptors."""

    for name in reservation.created:
        with suppress(OSError):
            os.unlink(name, dir_fd=reservation.directory)
    with suppress(OSError):
        os.rmdir(reservation.name, dir_fd=reservation.parent)


def _close(reservation: _Reservation) -> None:
    for descriptor in (reservation.directory, reservation.parent):
        if descriptor >= 0:
            os.close(descriptor)


def _fill(reservation: _Reservation, files: dict[str, bytes]) -> None:
    _open_directory(reservation)
    try:
        for name, data in files.items():
            _create(reservation, name, data)
    except FileExistsError as exc:
        raise tv.TextViewRefusal(
            tv.FINDING_DESTINATION_EXISTS, "another writer created an entry in the destination"
        ) from exc
    except OSError as exc:
        raise _write_failed("writing the view files", exc) from exc


def _populate(reservation: _Reservation, files: dict[str, bytes]) -> None:
    """Fill the reserved directory; any failure, an interrupt included, rolls it back."""

    _make_directory(reservation)
    try:
        _fill(reservation, files)
    except BaseException:
        _roll_back(reservation)
        raise


def write_new_tree(out: Path, files: dict[str, bytes]) -> None:
    """Reserve ``out`` and create each file in it exclusively; nothing is replaced."""

    tv.refuse_when(
        is_under_raw(out), tv.FINDING_DESTINATION_UNDER_RAW,
        "the destination names or aliases outputs/raw/",
    )
    reservation = _Reservation(_open_parent(out.parent), out.name)
    try:
        _populate(reservation, files)
    finally:
        _close(reservation)


bind_import_twin(__name__)
