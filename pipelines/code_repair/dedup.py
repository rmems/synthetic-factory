"""The cross-run duplicate report: a read-only selection manifest over stacked runs.

Generation skips ``DUPLICATE_MUTANT_IN_RUN`` and the export deduplicates
within one run; neither sees a second seed. This module takes run directories
in keep-first order, binds each ``candidates.jsonl`` to the
``candidates_sha256`` its ``RUN.json`` pins and re-checks every record's
integrity as the export does, catalog aside (a run failing either is refused),
keeps only positive records and reports every positive that repeats
a kept positive of an earlier run under three codes: the same broken bytes, the
same canonical structure (the export's own digest) or the same mutation site of
the same original module bytes. Within a run the order is sorted record id, as in the
export; duplicates inside one run stay the export's selection to decide, so a
single run never reports anything. The manifest (``code-repair-dedup/1``) lists
the kept ids and, per dropped record, the index of the run it came from, the
kept id it repeats and the code. Nothing is written into any run directory; the
manifest goes to a brand-new file when one is named.
"""

from __future__ import annotations

import hashlib
from collections import Counter
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import generate, run_validation, selection, validation, views
from . import vocabulary as cv
from ._contract import bind_import_twin, dumps_exact_json, is_under_raw
from .candidate_io import load_candidate_records, load_run_summary

DEDUP_FORMAT = "code-repair-dedup/1"

__all__ = [
    "DEDUP_FORMAT", "Decision", "DedupRequest", "LoadedRun", "decisions", "load_run",
    "manifest_of", "report",
]

_Keys = tuple[tuple[str, Any], ...]


@dataclass(frozen=True)
class DedupRequest:
    """Run directories in keep-first order and an optional brand-new manifest file."""

    run_dirs: tuple[Path, ...]
    out: Path | None = None


@dataclass(frozen=True)
class LoadedRun:
    """One run's bound inputs: its summary, every record and the positives in id order."""

    path: Path
    run: dict[str, Any]
    records: list[dict[str, Any]]
    candidates_sha256: str
    positives: list[dict[str, Any]]

    def entry(self) -> dict[str, Any]:
        return {
            "path": str(self.path), "candidates_sha256": self.candidates_sha256,
            "records": len(self.records), "positives": len(self.positives),
        }


@dataclass(frozen=True)
class Decision:
    """One positive in processing order; ``code`` is None when it is kept."""

    run: int
    record: dict[str, Any]
    duplicate_of: str | None = None
    code: str | None = None


def _inside_a_run(out: Path, run_dirs: Sequence[Path]) -> bool:
    destination = Path(out).resolve()
    return any(destination.is_relative_to(Path(run_dir).resolve()) for run_dir in run_dirs)


def _check_request(request: DedupRequest) -> None:
    """Every cheap refusal before a run is read, so a bad destination costs nothing."""

    out = request.out
    cv.refuse_first((
        (not request.run_dirs, cv.FINDING_RUN_FILE_MISSING,
         "at least one run directory is required"),
        (out is not None and is_under_raw(Path(out)), cv.FINDING_DESTINATION_UNDER_RAW,
         f"{cv.shown(out)} names or aliases the raw tree"),
        (out is not None and _inside_a_run(out, request.run_dirs),
         cv.FINDING_DESTINATION_INSIDE_RUN,
         f"{cv.shown(out)} would write into a run directory; the report is read-only"),
        (out is not None and Path(out).exists(), cv.FINDING_DESTINATION_EXISTS,
         f"{cv.shown(out)} already exists"),
    ))


def load_run(run_dir: Path) -> LoadedRun:
    """One run through the bound readers; refused when RUN.json does not pin its candidates."""

    run_dir = Path(run_dir)
    candidates = run_dir / generate.CANDIDATES_FILENAME
    run_file = run_dir / generate.RUN_FILENAME
    cv.refuse_first((
        (not candidates.is_file(), cv.FINDING_RUN_FILE_MISSING,
         f"{cv.shown(candidates)} is missing"),
        (not run_file.is_file(), cv.FINDING_RUN_FILE_MISSING, f"{cv.shown(run_file)} is missing"),
    ))
    run = load_run_summary(run_file.read_bytes())
    candidate_bytes = candidates.read_bytes()
    digest = hashlib.sha256(candidate_bytes).hexdigest()
    cv.refuse_when(
        not run_validation.candidates_bound(run, digest), cv.FINDING_EXPORT_INTEGRITY,
        f"{cv.shown(run_dir)}: {cv.EXPORT_RUN_SUMMARY_MISMATCH} (RUN.json candidates_sha256 "
        "does not bind candidates.jsonl)",
    )
    records = load_candidate_records(candidate_bytes)
    _refuse_repeated_ids(run_dir, records)
    _refuse_failing_records(run_dir, records)
    positives = sorted((r for r in records if views.is_positive(r)), key=lambda r: r["id"])
    return LoadedRun(run_dir, run, records, digest, positives)


def _refuse_repeated_ids(run_dir: Path, records: list[dict[str, Any]]) -> None:
    """The run-wide id uniqueness ``validate_run`` demands: a repeated id refuses the run.

    Two candidates under one id would make a kept and a dropped entry of that id name
    different records; the manifest could not say which.
    """

    present = Counter(record["id"] for record in records if "id" in record)
    repeated = sorted(identity for identity, n in present.items() if n > 1)
    cv.refuse_when(
        bool(repeated), cv.FINDING_EXPORT_INTEGRITY,
        f"{cv.shown(run_dir)}: record ids repeat within the run: {cv.shown(repeated)}",
    )


def _refuse_failing_records(run_dir: Path, records: list[dict[str, Any]]) -> None:
    """The export's per-record integrity check, catalog aside: one failure refuses the run.

    ``views.is_positive`` alone accepts a rehashed record whose stored failure evidence no
    longer matches its rows; such a record must not claim a key a later run is judged by.
    """

    for record in records:
        findings = validation.validate_record(record)
        if findings:
            raise cv.RepairRefusal(
                cv.FINDING_EXPORT_INTEGRITY,
                f"{cv.shown(run_dir)}: record {cv.shown(record.get('id'))} fails integrity "
                f"({cv.shown(findings[0])})",
            )


def _keys(record: dict[str, Any]) -> _Keys:
    """``(code, key)`` per duplicate code, in the order the codes are tried.

    Only positives get here: their shape is validated and their broken module parses
    (its doctests are read from it), so every key exists.
    """

    scenario, intervention = record["scenario"], record["intervention"]
    site = intervention["site"]
    return (
        (cv.DEDUP_DUPLICATE_EXACT, scenario["broken_program"]["sha256"]),
        (cv.DEDUP_DUPLICATE_STRUCTURAL, selection.structural_digest(record)),
        (cv.DEDUP_DUPLICATE_SITE, (
            scenario["source"]["program_id"], scenario["source"]["module_sha256"],
            intervention["operator"], intervention["variant"],
            site["start_byte"], site["end_byte"], site["replacement_text"],
        )),
    )


_Seen = dict[str, dict[Any, str]]
_Judged = list[tuple[Decision, _Keys]]


def _judge(seen: _Seen, index: int, record: dict[str, Any]) -> tuple[Decision, _Keys]:
    """The record's decision against keys already claimed, and its own keys."""

    keys = _keys(record)
    earlier = ((seen[code][key], code) for code, key in keys if key in seen[code])
    duplicate_of, code = next(earlier, (None, None))
    return Decision(index, record, duplicate_of, code), keys


def _claim(seen: _Seen, judged: _Judged) -> None:
    """Kept records claim their keys; the first kept claimant of a key keeps it."""

    kept = ((decision.record["id"], keys) for decision, keys in judged if decision.code is None)
    for identity, keys in kept:
        for code, key in keys:
            seen[code].setdefault(key, identity)


def decisions(runs: Sequence[LoadedRun]) -> Iterator[Decision]:
    """Keep-first over run order, then sorted id, against kept positives of earlier runs.

    A run's kept records claim their keys only once the whole run is judged, so two
    positives of one run never meet here.
    """

    seen: _Seen = {code: {} for code in cv.DEDUP_CODES}
    for index, loaded in enumerate(runs):
        judged = [_judge(seen, index, record) for record in loaded.positives]
        yield from (decision for decision, _ in judged)
        _claim(seen, judged)


def _refuse_id_collisions(kept: list[str]) -> None:
    """Two kept records with one id would make ``duplicate_of`` ambiguous: refuse."""

    collisions = sorted(identity for identity, n in Counter(kept).items() if n > 1)
    cv.refuse_when(
        bool(collisions), cv.FINDING_EXPORT_INTEGRITY,
        f"record ids name more than one kept candidate: {cv.shown(collisions)}",
    )


def manifest_of(runs: Sequence[LoadedRun]) -> dict[str, Any]:
    """The deterministic selection manifest over already-loaded runs."""

    kept: list[str] = []
    dropped: list[dict[str, Any]] = []
    by_code = dict.fromkeys(cv.DEDUP_CODES, 0)
    for decision in decisions(runs):
        if decision.code is None:
            kept.append(decision.record["id"])
            continue
        by_code[decision.code] += 1
        dropped.append({
            "id": decision.record["id"], "run": decision.run,
            "duplicate_of": decision.duplicate_of, "code": decision.code,
        })
    _refuse_id_collisions(kept)
    return {
        "format": DEDUP_FORMAT,
        "runs": [loaded.entry() for loaded in runs],
        "kept": kept,
        "dropped": dropped,
        "counts": {
            "runs": len(runs),
            "records": sum(len(loaded.records) for loaded in runs),
            "positives": sum(len(loaded.positives) for loaded in runs),
            "kept": len(kept), "dropped": len(dropped), "by_code": by_code,
        },
    }


def _write(out: Path, manifest: dict[str, Any]) -> None:
    """The manifest as a brand-new file; exclusive creation refuses a racing writer."""

    text = dumps_exact_json(manifest, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("x", encoding="utf-8") as handle:
        handle.write(text)


def report(request: DedupRequest) -> dict[str, Any]:
    """The manifest over the runs in order, written to ``request.out`` when one is named."""

    _check_request(request)
    runs = [load_run(path) for path in request.run_dirs]
    manifest = manifest_of(runs)
    if request.out is not None:
        _write(Path(request.out), manifest)
    return manifest


bind_import_twin(__name__)
