"""Exact decimal parsing shared by replay and export candidate consumers."""
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


bind_import_twin(__name__)
