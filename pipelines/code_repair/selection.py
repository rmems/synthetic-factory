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
    return tuple(record for record, code in selection_decisions(records, lineage_cap=lineage_cap)
                 if code is None)


def selection_decisions(records: Iterable[dict[str, Any]], *, lineage_cap=DEFAULT_LINEAGE_CAP):
    """Yield every positive in canonical order with its optional exclusion disposition."""
    _validate_cap(lineage_cap)
    seen_exact, seen_structural = set(), set()
    per_lineage = Counter()
    for record in sorted(records, key=lambda r: r["id"]):
        exact = record["result"]["broken_sha256"]
        broken = record["scenario"]["broken_program"]["files"][cv.PROGRAM_FILENAME]
        structural = lineage.structure_digest(broken)
        lineage_id = record["provenance"]["split_lineage"]["lineage_id"]
        code = None
        if exact in seen_exact:
            code = cv.EXPORT_DUPLICATE_EXACT
        elif structural in seen_structural:
            code = cv.EXPORT_DUPLICATE_STRUCTURAL
        elif per_lineage[lineage_id] >= lineage_cap:
            code = cv.EXPORT_LINEAGE_CAP_APPLIED
        else:
            seen_exact.add(exact)
            seen_structural.add(structural)
            per_lineage[lineage_id] += 1
        yield record, code


def _validate_cap(lineage_cap):
    # Exact int rejects bool and subclasses at the selection boundary.
    if type(lineage_cap) is not int or lineage_cap < 1:  # pylint: disable=unidiomatic-typecheck
        raise ValueError("lineage_cap must be a positive integer")


bind_import_twin(__name__)
