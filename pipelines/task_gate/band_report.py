#!/usr/bin/env python3
"""Band rows, the difficulty histogram and the files one band run writes.

A run writes four files into a brand-new directory that is staged next to its destination and
renamed into place with no replace, exactly as the task gate does: ``band-rows.jsonl`` (every
evaluated task with its band verdict), ``band-kept.jsonl`` (the in-band rows),
``seed_needed.jsonl`` (zero-pass rows, kept for teacher/procedural seeding rather than
discarded) and ``band-summary.json`` (counts and the difficulty histogram).
"""

from __future__ import annotations

import shutil
import tempfile
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import band_provenance
from . import band_vocabulary as bv
from ._contract import bind_import_twin, dumps_exact_json
from .band_contract import BandContract
from .report import check_destination, publish, write_new

__all__ = ["BandOutcome", "BandRow", "histogram", "write_band_run"]


@dataclass(frozen=True)
class BandRow:
    """One verified task with the difficulty measured for it."""

    task: Mapping[str, Any]
    generator: str
    attempts: int
    successes: int
    band: str

    def as_row(self) -> dict[str, Any]:
        row = {
            **self.task, "band_format": bv.ROW_FORMAT, "generator": self.generator,
            "attempts": self.attempts, "successes": self.successes,
            "pass_rate": self.successes / self.attempts, "band": self.band,
        }
        band_provenance.check_row(row)
        return row


def histogram(rows: Sequence[BandRow], contract: BandContract) -> list[dict[str, Any]]:
    """Task counts per success count, 0..attempts_per_task, each marked in or out of the band."""

    found = Counter(row.successes for row in rows)
    attempts = contract.attempts_per_task
    return [
        {
            "successes": n, "attempts": attempts, "pass_rate": n / attempts, "count": found[n],
            "band": contract.classify(n, attempts),
        }
        for n in range(attempts + 1)
    ]


@dataclass(frozen=True)
class BandOutcome:
    """What a finished band run produced, ready to be written."""

    rows: Sequence[BandRow]
    contract: BandContract
    meta: Mapping[str, Any]

    def with_band(self, *bands: str) -> list[dict[str, Any]]:
        return [row.as_row() for row in self.rows if row.band in bands]


def _jsonl(rows: Sequence[Mapping[str, Any]]) -> bytes:
    return "".join(dumps_exact_json(row) + "\n" for row in rows).encode("utf-8")


def _summary(outcome: BandOutcome, outputs: Mapping[str, Any]) -> dict[str, Any]:
    contract, counts = outcome.contract, Counter(row.band for row in outcome.rows)
    return {
        "format": bv.SUMMARY_FORMAT, "band": bv.BAND_FORMAT, "total": len(outcome.rows),
        "bands": {band: counts[band] for band in bv.BANDS},
        "contract": {
            "sha256": contract.sha256, "attempts_per_task": contract.attempts_per_task,
            "pass_rate_min": float(contract.pass_rate_min),
            "pass_rate_max": float(contract.pass_rate_max),
        },
        "histogram": histogram(outcome.rows, contract),
        "inputs": dict(outcome.meta), "outputs": dict(outputs),
    }


def _stage(stage: Path, outcome: BandOutcome) -> dict[str, Any]:
    files = {
        bv.ROWS_FILENAME: outcome.with_band(*bv.BANDS),
        bv.KEPT_FILENAME: outcome.with_band(bv.BAND_KEPT),
        bv.SEED_NEEDED_FILENAME: outcome.with_band(bv.BAND_SEED_NEEDED),
    }
    outputs = {
        name: {"sha256": write_new(stage / name, _jsonl(rows)), "rows": len(rows)}
        for name, rows in files.items()
    }
    summary = _summary(outcome, outputs)
    text = dumps_exact_json(summary, indent=2) + "\n"
    write_new(stage / bv.SUMMARY_FILENAME, text.encode("utf-8"))
    return summary


def write_band_run(out: Path, outcome: BandOutcome) -> dict[str, Any]:
    """Write the four files into the new destination and return the summary."""

    destination = Path(out)
    check_destination(destination)
    stage = Path(tempfile.mkdtemp(prefix=".band-stage-", dir=destination.resolve().parent))
    try:
        summary = _stage(stage, outcome)
        publish(stage, destination)
    except BaseException:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    return summary


bind_import_twin(__name__)
