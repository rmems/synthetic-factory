"""Serialize the view files and write them into a brand-new destination, or refuse.

Rows are serialized through ``exact_json`` one per line; ``VIEWS.json`` carries
the per-family counts, the refused record ids with their codes, the digest of
every authenticated source file the rows were projected from, and the digest
of every file written. The destination must not exist and must not name or
alias ``outputs/raw/``. It is reserved with a single ``mkdir`` (losing that
race is the existing-destination refusal), every file is created exclusively,
and a failed write removes only the files this call created.
"""

from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path
from typing import Any

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("oracle_text_view_output")
    from . import oracle_text_view_vocabulary as tv
    from .exact_json import dumps_exact_json
    from .raw_tree_guard import is_under_raw
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "oracle_text_view_output"
    )
    import oracle_text_view_vocabulary as tv
    from exact_json import dumps_exact_json
    from raw_tree_guard import is_under_raw

__all__ = ["check_destination", "jsonl_bytes", "summary_bytes", "view_files", "write_new_tree"]


def check_destination(out: Path) -> None:
    """Refuse a destination that names the raw tree or already exists."""

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


def _remove_created(out: Path, created: list[Path]) -> None:
    for path in created:
        try:
            path.unlink()
        except OSError:
            continue
    try:
        out.rmdir()
    except OSError:
        return


def _reserve(out: Path) -> None:
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.mkdir()
    except FileExistsError as exc:
        raise tv.TextViewRefusal(
            tv.FINDING_DESTINATION_EXISTS, f"the destination already exists: {out.name}"
        ) from exc
    except OSError as exc:
        raise tv.TextViewRefusal(
            tv.FINDING_DESTINATION_WRITE_FAILED,
            f"cannot create the destination: {type(exc).__name__}",
        ) from exc


def _create(path: Path, data: bytes, created: list[Path]) -> None:
    with path.open("xb") as handle:
        created.append(path)
        handle.write(data)


def write_new_tree(out: Path, files: dict[str, bytes]) -> None:
    """Reserve ``out`` and create each file in it exclusively; nothing is replaced."""

    check_destination(out)
    _reserve(out)
    created: list[Path] = []
    for name, data in files.items():
        try:
            _create(out / name, data, created)
        except OSError as exc:
            _remove_created(out, created)
            raise tv.TextViewRefusal(
                tv.FINDING_DESTINATION_WRITE_FAILED,
                f"writing {name} failed: {type(exc).__name__}",
            ) from exc


if __package__:
    _expose_package_sibling(__name__)
