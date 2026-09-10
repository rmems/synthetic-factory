"""One deterministic selected-membership rule for prevalidated positive records.

This is selection, not admission. Callers validate every original candidate and
filter natural ineligibility before using it. It preserves the export's sorted
ID order, exact/AST deduplication, and default six-record per-lineage cap.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Iterable

from . import lineage, vocabulary as cv
from ._contract import bind_import_twin

DEFAULT_LINEAGE_CAP = 6


def selected_records(
    records: Iterable[dict[str, Any]], *, lineage_cap: int = DEFAULT_LINEAGE_CAP,
) -> tuple[dict[str, Any], ...]:
    """Select original record objects; never rewrite IDs, payloads, or caller order."""
    if type(lineage_cap) is not int or lineage_cap < 1:
        raise ValueError("lineage_cap must be a positive integer")
    seen_exact, seen_structural = set(), set()
    per_lineage = Counter()
    selected = []
    for record in sorted(records, key=lambda r: r["id"]):
        exact = record["result"]["broken_sha256"]
        broken = record["scenario"]["broken_program"]["files"][cv.PROGRAM_FILENAME]
        structural = lineage.structure_digest(broken)
        lineage_id = record["provenance"]["split_lineage"]["lineage_id"]
        if (exact in seen_exact or structural in seen_structural
                or per_lineage[lineage_id] >= lineage_cap):
            continue
        seen_exact.add(exact)
        seen_structural.add(structural)
        per_lineage[lineage_id] += 1
        selected.append(record)
    return tuple(selected)


bind_import_twin(__name__)
