#!/usr/bin/env python3
"""Outputs of a gate run: ``tasks.jsonl``, ``summary.json`` and the new ``dedup-index.jsonl``.

A run writes into a brand-new directory that is staged next to its destination and renamed
into place, so a destination either holds all three files or does not exist. An existing
destination, one under the raw tree, or one whose parent is missing is refused before any
proposal is executed.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import tempfile
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from . import vocabulary as cv
from ._contract import bind_import_twin, dumps_exact_json, is_under_raw
from .dedup_index import PriorIndex, index_bytes
from .gate import Decision

__all__ = ["check_destination", "summarize", "write_run"]


def check_destination(out: Path) -> None:
    """Refuse a destination that exists, aliases the raw tree, or has no parent directory."""

    destination = Path(out)
    cv.refuse_when(
        is_under_raw(destination), cv.REFUSE_DESTINATION_UNDER_RAW,
        f"{destination} names or aliases the raw tree",
    )
    cv.refuse_when(
        os.path.lexists(destination), cv.REFUSE_DESTINATION_EXISTS, f"{destination} already exists",
    )
    cv.refuse_when(
        not destination.resolve().parent.is_dir(), cv.REFUSE_INPUT_INVALID,
        f"parent of {destination} is not a directory",
    )


def _rate(count: int, total: int) -> str:
    return f"{count / total:.6f}" if total else "0.000000"


def summarize(
    decisions: Sequence[Decision], meta: Mapping[str, Any], outputs: Mapping[str, Any],
) -> dict[str, Any]:
    """The verdict counts, survival rate by reason, and the inputs that fix the result."""

    total = len(decisions)
    counts = Counter(decision.verdict for decision in decisions)
    details: dict[str, Counter] = {verdict: Counter() for verdict in cv.VERDICTS}
    by_source: dict[str, Counter] = {}
    for decision in decisions:
        details[decision.verdict][decision.detail] += 1
        by_source.setdefault(decision.source or "unknown", Counter())[decision.verdict] += 1
    return {
        "format": cv.SUMMARY_FORMAT,
        "gate": cv.GATE_FORMAT,
        "total": total,
        "verdicts": {verdict: counts[verdict] for verdict in cv.VERDICTS},
        "survival_rate": _rate(counts[cv.VERDICT_KEPT], total),
        "rejection_rates": {
            verdict: _rate(counts[verdict], total) for verdict in cv.VERDICTS
            if verdict != cv.VERDICT_KEPT
        },
        "details": {verdict: dict(sorted(found.items())) for verdict, found in details.items() if found},
        "by_source": {
            source: {"total": sum(found.values()), **{v: found[v] for v in cv.VERDICTS}}
            for source, found in sorted(by_source.items())
        },
        "inputs": dict(meta),
        "outputs": dict(outputs),
    }


def _write_new(path: Path, data: bytes) -> str:
    with path.open("xb") as handle:
        handle.write(data)
    return hashlib.sha256(data).hexdigest()


def write_run(
    out: Path, decisions: Sequence[Decision], kept_rows: Mapping[str, Mapping[str, Any]],
    prior: PriorIndex, meta: Mapping[str, Any],
) -> dict[str, Any]:
    """Write the three files into the new destination and return the summary."""

    destination = Path(out)
    check_destination(destination)
    tasks = "".join(dumps_exact_json(d.as_row()) + "\n" for d in decisions).encode("utf-8")
    cumulative = {**{k: dict(v) for k, v in prior.rows.items()}, **{k: dict(v) for k, v in kept_rows.items()}}
    index = index_bytes(cumulative.values())
    stage = Path(tempfile.mkdtemp(prefix=".task-gate-stage-", dir=destination.resolve().parent))
    try:
        outputs = {
            cv.TASKS_FILENAME: {"sha256": _write_new(stage / cv.TASKS_FILENAME, tasks), "rows": len(decisions)},
            cv.INDEX_FILENAME: {
                "sha256": _write_new(stage / cv.INDEX_FILENAME, index), "keys": len(cumulative),
                "new_keys": len(kept_rows),
            },
        }
        summary = summarize(decisions, meta, outputs)
        text = dumps_exact_json(summary, indent=2) + "\n"
        _write_new(stage / cv.SUMMARY_FILENAME, text.encode("utf-8"))
        check_destination(destination)
        os.chmod(stage, 0o755)
        os.rename(stage, destination)
    except BaseException:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    return summary


bind_import_twin(__name__)
