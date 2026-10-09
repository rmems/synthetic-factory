#!/usr/bin/env python3
"""A run directory's files: ``RUN.json`` and the ``candidates.jsonl`` it vouches for.

``load_records`` reads a run the way every gate must: the manifest is strict
JSON, the candidates' bytes match its digest, each line is one object, and
the loaded ids are exactly the ordered inventory the manifest's rows name.
``check_drawn`` then binds that inventory to the record ids the header's own
draw produces from the loaded catalog, so a manifest cannot name records
its draw never produced.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from . import generate
from . import vocabulary as cv
from ._contract import bind_import_twin, load_strict_json, sha256_bytes
from .generate import CANDIDATES_FILENAME, RUN_FILENAME

__all__ = ["CANDIDATES_FILENAME", "RUN_FILENAME", "check_drawn", "load_records", "run_summary"]


def run_summary(run_dir: Path) -> Mapping[str, Any]:
    """The run's RUN.json as a strict-JSON object; a missing or malformed one is a refusal."""
    run_file = run_dir / RUN_FILENAME
    cv.refuse_when(not run_file.is_file(), cv.FINDING_RUN_FILE_MISSING, f"missing {RUN_FILENAME}")
    try:
        summary = load_strict_json(run_file.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise cv.ToolWorldRefusal(
            cv.FINDING_RUN_FILE_INVALID, f"{RUN_FILENAME} is not strict JSON ({exc})"
        ) from exc
    cv.refuse_when(
        not isinstance(summary, Mapping),
        cv.FINDING_RUN_FILE_INVALID,
        f"{RUN_FILENAME} must be an object",
    )
    return summary


def _candidate_lines(run_dir: Path, summary: Mapping[str, Any]) -> list[str]:
    candidates = run_dir / CANDIDATES_FILENAME
    cv.refuse_when(
        not candidates.is_file(), cv.FINDING_RUN_FILE_MISSING, f"missing {CANDIDATES_FILENAME}"
    )
    payload = candidates.read_bytes()
    cv.refuse_when(
        summary.get("candidates_sha256") != sha256_bytes(payload),
        cv.FINDING_RUN_SHA_MISMATCH,
        f"{CANDIDATES_FILENAME} bytes do not match RUN.json candidates_sha256",
    )
    try:
        return payload.decode("utf-8").splitlines()
    except UnicodeDecodeError as exc:
        raise cv.ToolWorldRefusal(
            cv.FINDING_RECORD_MALFORMED, f"{CANDIDATES_FILENAME} is not UTF-8 ({exc.reason})"
        )


def _parse_record(line: str, number: int) -> Mapping[str, Any]:
    try:
        record = load_strict_json(line)
    except ValueError as exc:
        raise cv.ToolWorldRefusal(
            cv.FINDING_RECORD_MALFORMED, f"line {number} is not strict JSON ({exc})"
        ) from exc
    cv.refuse_when(
        not isinstance(record, Mapping),
        cv.FINDING_RECORD_MALFORMED,
        f"line {number} is not an object",
    )
    return record


def _row_ids(rows: Any) -> list[str] | None:
    """The ids the manifest rows name, in order, or ``None`` when a row cannot name one."""
    if not isinstance(rows, list):
        return None
    ids = [row.get("id") if isinstance(row, Mapping) else None for row in rows]
    named = [record_id for record_id in ids if isinstance(record_id, str)]
    return named if len(named) == len(ids) else None


def _inventory(summary: Mapping[str, Any]) -> list[str]:
    """The record ids RUN.json names in ``rows``: at least one, counted by ``records``."""
    ids = _row_ids(summary.get("rows"))
    if ids is None:
        raise cv.ToolWorldRefusal(
            cv.FINDING_RUN_FILE_INVALID,
            f"{RUN_FILENAME} rows must be a list of objects each naming a string id",
        )
    declared = summary.get("records")
    cv.refuse_first(
        (
            (
                not cv.is_genuine_int(declared) or declared != len(ids),
                cv.FINDING_RUN_FILE_INVALID,
                f"{RUN_FILENAME} records must count its rows: {cv.shown(declared)} for {len(ids)}",
            ),
            (not ids, cv.FINDING_RUN_FILE_INVALID, f"{RUN_FILENAME} names no records"),
        )
    )
    return ids


def _first_disagreement(found: list[Any], expected: list[str]) -> int:
    """The 1-based position where two id lists first differ, or the one past the shorter list."""
    for number, (one, two) in enumerate(zip(found, expected, strict=False), 1):
        if one != two:
            return number
    return min(len(found), len(expected)) + 1


def _check_inventory(loaded: list[Mapping[str, Any]], inventory: list[str]) -> None:
    """The candidates are exactly the records RUN.json names, in its order."""
    found = [record.get("id") for record in loaded]
    if found != inventory:
        raise cv.ToolWorldRefusal(
            cv.FINDING_RUN_INVENTORY_MISMATCH,
            f"{CANDIDATES_FILENAME} record {_first_disagreement(found, inventory)} is not the "
            f"record {RUN_FILENAME} names there ({len(found)} held, {len(inventory)} named)",
        )


def check_drawn(summary: Mapping[str, Any], catalog: Any) -> None:
    """RUN.json's rows name exactly the records its own header draws from the catalog."""
    named = _inventory(summary)
    drawn = generate.expected_ids(catalog, summary)
    if named != drawn:
        raise cv.ToolWorldRefusal(
            cv.FINDING_RUN_INVENTORY_MISMATCH,
            f"{RUN_FILENAME} row {_first_disagreement(named, drawn)} does not name the record "
            f"its header draws there ({len(named)} named, {len(drawn)} drawn)",
        )


def load_records(run_dir: Path) -> list[Mapping[str, Any]]:
    """Every candidate of a run, as RUN.json vouches for the bytes and names the records in order.

    A candidates file whose bytes, count, or ordered ids disagree with the
    manifest is refused; ``replay_run`` then binds the manifest's rows to the
    record ids the header's own draw produces.
    """
    run_dir = Path(run_dir)
    candidates = run_dir / CANDIDATES_FILENAME
    cv.refuse_when(
        not candidates.is_file(), cv.FINDING_RUN_FILE_MISSING, f"missing {CANDIDATES_FILENAME}"
    )
    summary = run_summary(run_dir)
    lines = _candidate_lines(run_dir, summary)
    inventory = _inventory(summary)
    loaded = [_parse_record(line, number) for number, line in enumerate(lines, 1) if line.strip()]
    _check_inventory(loaded, inventory)
    return loaded


bind_import_twin(__name__)
