"""Exact decimal parsing shared by replay, export and dedup run consumers."""
from __future__ import annotations

from typing import Any

from . import generate, vocabulary as cv
from ._contract import bind_import_twin, load_strict_json, oc


def load_candidate_records(data: bytes) -> list[dict[str, Any]]:
    records = []
    for lineno, raw in enumerate(data.split(b"\n"), 1):
        if not raw.strip():
            continue
        try:
            record = load_strict_json(raw.decode("utf-8").strip())
            oc.canonical_json(record).encode("utf-8")
        except (ValueError, RecursionError) as exc:
            raise cv.RepairRefusal(cv.FINDING_RECORD_MALFORMED,
                                   f"{generate.CANDIDATES_FILENAME}:{lineno} is not a record") from exc
        cv.refuse_when(
            not isinstance(record, dict), cv.FINDING_RECORD_MALFORMED,
            f"{generate.CANDIDATES_FILENAME}:{lineno} is not a record",
        )
        records.append(record)
    return records


def load_run_summary(data: bytes) -> dict[str, Any]:
    """``RUN.json`` with exact decimals; refused unless it is a code-repair run summary."""
    try:
        metadata = load_strict_json(data)
    except (ValueError, RecursionError) as exc:
        raise cv.RepairRefusal(
            cv.FINDING_RUN_FILE_MISSING, f"RUN.json is not JSON: {cv.shown(exc)}"
        ) from exc
    cv.refuse_when(
        not isinstance(metadata, dict) or metadata.get("format") != generate.RUN_FORMAT,
        cv.FINDING_RUN_FILE_MISSING, "RUN.json is not a code-repair metadata summary",
    )
    return metadata


bind_import_twin(__name__)
