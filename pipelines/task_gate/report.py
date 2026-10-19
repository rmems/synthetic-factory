#!/usr/bin/env python3
"""Outputs of a gate run: ``tasks.jsonl``, ``summary.json`` and the new ``dedup-index.jsonl``.

A run writes into a brand-new directory that is staged next to its destination and renamed
into place, so a destination either holds all three files or does not exist. An existing
destination, one under the raw tree, or one whose parent is missing is refused before any
proposal is executed.
"""

from __future__ import annotations

import errno
import hashlib
import os
import shutil
import tempfile
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import vocabulary as cv
from ._contract import bind_import_twin, dumps_exact_json, is_under_raw, rename_noreplace
from .dedup_index import PriorIndex, index_bytes
from .gate import Decision

__all__ = ["RunOutcome", "check_destination", "publish", "summarize", "write_new", "write_run"]


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


def _details_by_verdict(decisions: Sequence[Decision]) -> dict[str, dict[str, int]]:
    details: dict[str, Counter] = {verdict: Counter() for verdict in cv.VERDICTS}
    for decision in decisions:
        details[decision.verdict][decision.detail] += 1
    return {verdict: dict(sorted(found.items())) for verdict, found in details.items() if found}


def _counts_by_source(decisions: Sequence[Decision]) -> dict[str, dict[str, int]]:
    by_source: dict[str, Counter] = {}
    for decision in decisions:
        by_source.setdefault(decision.source or "unknown", Counter())[decision.verdict] += 1
    return {
        source: {"total": sum(found.values()), **{v: found[v] for v in cv.VERDICTS}}
        for source, found in sorted(by_source.items())
    }


def summarize(
    decisions: Sequence[Decision], meta: Mapping[str, Any], outputs: Mapping[str, Any],
) -> dict[str, Any]:
    """The verdict counts, survival rate by reason, and the inputs that fix the result."""

    total = len(decisions)
    counts = Counter(decision.verdict for decision in decisions)
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
        "details": _details_by_verdict(decisions),
        "by_source": _counts_by_source(decisions),
        "inputs": dict(meta),
        "outputs": dict(outputs),
    }


def write_new(path: Path, data: bytes) -> str:
    with path.open("xb") as handle:
        handle.write(data)
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class RunOutcome:
    """What a finished gate run produced, ready to be written."""

    decisions: Sequence[Decision]
    kept_rows: Mapping[str, Mapping[str, Any]]
    prior: PriorIndex
    meta: Mapping[str, Any]

    def cumulative_index(self) -> dict[str, dict[str, Any]]:
        """Every prior key plus this run's kept keys."""

        prior = {key: dict(row) for key, row in self.prior.rows.items()}
        return {**prior, **{key: dict(row) for key, row in self.kept_rows.items()}}

    def tasks_bytes(self) -> bytes:
        return "".join(dumps_exact_json(d.as_row()) + "\n" for d in self.decisions).encode("utf-8")


def _stage_files(stage: Path, outcome: RunOutcome) -> dict[str, Any]:
    """Write the three files into the staging directory and return the summary."""

    index = outcome.cumulative_index()
    outputs = {
        cv.TASKS_FILENAME: {
            "sha256": write_new(stage / cv.TASKS_FILENAME, outcome.tasks_bytes()),
            "rows": len(outcome.decisions),
        },
        cv.INDEX_FILENAME: {
            "sha256": write_new(stage / cv.INDEX_FILENAME, index_bytes(index.values())),
            "keys": len(index), "new_keys": len(outcome.kept_rows),
        },
    }
    summary = summarize(outcome.decisions, outcome.meta, outputs)
    write_new(stage / cv.SUMMARY_FILENAME, (dumps_exact_json(summary, indent=2) + "\n").encode("utf-8"))
    return summary


_EXISTING_ENTRY = frozenset({errno.EEXIST, errno.ENOTEMPTY})


def publish(stage: Path, destination: Path) -> None:
    """Move the stage onto the destination atomically, never replacing an existing entry.

    ``rename_noreplace`` (``renameat2`` with ``RENAME_NOREPLACE``) closes the window
    between the entry check and the rename, so a destination created by another
    writer meanwhile is refused rather than overwritten.
    """

    try:
        parent = os.open(stage.parent, os.O_RDONLY | os.O_DIRECTORY)
    except OSError as exc:
        raise cv.GateRefusal(cv.REFUSE_INPUT_INVALID, f"cannot open {stage.parent}: {exc}") from exc
    try:
        rename_noreplace(parent, stage.name, destination.name)
    except OSError as exc:
        code = cv.REFUSE_DESTINATION_EXISTS if exc.errno in _EXISTING_ENTRY else cv.REFUSE_INPUT_INVALID
        raise cv.GateRefusal(code, f"cannot publish {destination}: {exc.strerror}") from exc
    finally:
        os.close(parent)


def write_run(out: Path, outcome: RunOutcome) -> dict[str, Any]:
    """Write the three files into the new destination and return the summary."""

    destination = Path(out)
    check_destination(destination)
    stage = Path(tempfile.mkdtemp(prefix=".task-gate-stage-", dir=destination.resolve().parent))
    try:
        summary = _stage_files(stage, outcome)
        publish(stage, destination)
    except BaseException:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    return summary


bind_import_twin(__name__)
