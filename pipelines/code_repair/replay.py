#!/usr/bin/env python3
"""Replay: every positive record re-executed with the pinned catalog and harness.

Recomputing digests and re-deriving verdicts from stored rows proves a
record is self-consistent, not that the execution happened: a forgery whose
rows, hashes and verdict were all rewritten together passes every stored
check. Replay is the only evidence that survives such a forgery. For each
accepted, validated record it binds the program to the catalog's pinned text,
the harness on disk to the fingerprint, the interpreter to the recorded
major.minor, then runs the original, the broken and the repaired module afresh
and demands the same rows, the same hashes and the same verdict. Records that
are not positive (rejected, abstained, provisional) are listed as not replayed
by natural ineligibility and never fail a replay. Admission needs a passing
``REPLAY.json``; the volatile timings go to a separate log.
"""

from __future__ import annotations

import json
import platform
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import catalog as cat
from . import executor as ex
from . import generate
from . import verify
from . import views
from . import vocabulary as cv
from ._contract import bind_import_twin, is_under_raw, oc

REPLAY_FILENAME = "REPLAY.json"
REPLAY_LOG_FILENAME = "replay-log.jsonl"
REPLAY_FORMAT = "code-repair-replay/1"

__all__ = [
    "REPLAY_FILENAME", "REPLAY_FORMAT", "REPLAY_LOG_FILENAME", "ReplayRequest", "replay_record",
    "run",
]


@dataclass(frozen=True)
class ReplayRequest:
    run_dir: Path
    catalog_dir: Path
    out_dir: Path
    timeout_s: float = cv.DEFAULT_TIMEOUT_S


def _entry(record: dict[str, Any], code: str, detail: str = "") -> dict[str, Any]:
    return {"record_id": record["id"], "status": "replayed", "code": code, "detail": detail}


def _drift(record: dict[str, Any], catalog: cat.Catalog, executor: ex.Executor) -> dict | None:
    """The catalog, harness or interpreter no longer being the record's, as an entry."""

    source = record["scenario"]["source"]
    program_id = source["program_id"]
    program = next((p for p in catalog.programs if p.program_id == program_id), None)
    if program is None or program.sha256 != source["module_sha256"]:
        return _entry(record, cv.REPLAY_CATALOG_DRIFT, "the catalog does not pin this program")
    if program.upstream != source["upstream"]:
        return _entry(record, cv.REPLAY_CATALOG_DRIFT, "the program's upstream identity moved")
    fingerprint = record["oracle"].get("fingerprint") or {}
    if fingerprint.get("harness_sha256") != executor.harness_sha256:
        return _entry(record, cv.REPLAY_HARNESS_DRIFT, "the harness on disk differs")
    interpreter = ".".join(platform.python_version().split(".")[:2])
    if fingerprint.get("python") != interpreter:
        return _entry(record, cv.REPLAY_ENVIRONMENT_DRIFT, f"recorded {fingerprint.get('python')}")
    return None


def _texts(record: dict[str, Any], program: cat.Program) -> tuple[str, str] | dict[str, Any]:
    """The broken and repaired texts, bound to their digests and to the pinned original."""

    result = record["result"]
    broken = str(record["scenario"]["broken_program"]["files"][cv.PROGRAM_FILENAME])
    repaired = views.completion_of(record)
    if cat.sha256_text(broken) != result["broken_sha256"]:
        return _entry(record, cv.REPLAY_TEXT_MISMATCH, "broken text does not match its digest")
    if cat.sha256_text(repaired) != result["repaired_sha256"]:
        return _entry(record, cv.REPLAY_TEXT_MISMATCH, "repaired text does not match its digest")
    if repaired != program.text:
        return _entry(record, cv.REPLAY_TEXT_MISMATCH, "the repair is not the pinned original")
    return broken, repaired


@dataclass(frozen=True)
class _Subject:
    """One positive record bound to its pinned program and its two texts."""

    label: str
    program: cat.Program
    broken: str
    repaired: str


def _fresh_phases(subject: _Subject, executor: ex.Executor) -> verify.Phases:
    program, label = subject.program, subject.label
    return verify.Phases(
        executor.run(program.job(f"{cv.PHASE_ORIGINAL}:{label}")),
        executor.run(program.job(f"{cv.PHASE_MUTANT}:{label}", subject.broken)),
        executor.run(program.job(f"{cv.PHASE_REPAIRED}:{label}", subject.repaired)),
    )


def _compare(
    record: dict[str, Any], program: cat.Program, phases: verify.Phases, repaired: str
) -> dict[str, Any]:
    """Fresh rows, hashes and verdict against the stored ones; the first divergence decides."""

    result = record["result"]
    blocks = {
        cv.PHASE_ORIGINAL: verify.phase_block(phases.original),
        cv.PHASE_MUTANT: verify.phase_block(phases.mutant),
        cv.PHASE_REPAIRED: verify.phase_block(phases.repaired),
    }
    if blocks != result["phases"]:
        differing = [name for name in blocks if blocks[name] != result["phases"].get(name)]
        detail = "fresh rows differ in " + ", ".join(differing)
        return _entry(record, cv.REPLAY_ROWS_MISMATCH, detail)
    if verify.result_hash(blocks) != result["evidence_sha256"]:
        return _entry(record, cv.REPLAY_HASH_MISMATCH, "evidence digest does not match rows")
    if oc.check_digest(record, record["id"]):
        return _entry(record, cv.REPLAY_HASH_MISMATCH, "record digest does not match content")
    context = verify.DecisionContext(
        program.reference.kind, repaired == program.text,
        verify.tests_tampered(program.examples, repaired, program.function), len(program.cases),
    )
    verdict = verify.decide(phases, context)
    stored = (result["outcome"], list(result["reason_codes"]), result["oracle_status"])
    if (verdict.outcome, list(verdict.reason_codes), verdict.oracle_status) != stored:
        return _entry(record, cv.REPLAY_VERDICT_MISMATCH, f"fresh verdict {verdict.outcome}")
    entry = _entry(record, cv.REPLAY_PASSED)
    entry["fresh_evidence_sha256"] = verify.result_hash(blocks)
    return entry


def replay_record(
    record: dict[str, Any], catalog: cat.Catalog, executor: ex.Executor
) -> dict[str, Any]:
    """One record's replay entry; non-positive records are listed, never executed."""

    if not views.is_positive(record):
        result = record.get("result") if isinstance(record.get("result"), dict) else {}
        return {
            "record_id": record.get("id"), "status": "not_replayed",
            "reason": "natural ineligibility",
            "outcome": result.get("outcome"), "oracle_status": result.get("oracle_status"),
        }
    drift = _drift(record, catalog, executor)
    if drift is not None:
        return drift
    program = catalog.program(record["scenario"]["source"]["program_id"])
    texts = _texts(record, program)
    if isinstance(texts, dict):
        return texts
    broken, repaired = texts
    phases = _fresh_phases(_Subject(record["id"], program, broken, repaired), executor)
    return _compare(record, program, phases, repaired)


def _check_request(request: ReplayRequest) -> None:
    candidates = Path(request.run_dir) / generate.CANDIDATES_FILENAME
    cv.refuse_first((
        (not candidates.is_file(), cv.FINDING_RUN_FILE_MISSING, f"{candidates} is missing"),
        (is_under_raw(Path(request.out_dir)), cv.FINDING_DESTINATION_UNDER_RAW,
         f"{request.out_dir} names or aliases the raw tree"),
        (Path(request.out_dir).exists(), cv.FINDING_DESTINATION_EXISTS,
         f"{request.out_dir} already exists"),
    ))


def _records(run_dir: Path) -> list[dict[str, Any]]:
    loaded = []
    for lineno, record in oc.iter_jsonl(run_dir / generate.CANDIDATES_FILENAME):
        cv.refuse_when(
            not isinstance(record, dict), cv.FINDING_RECORD_MALFORMED,
            f"{generate.CANDIDATES_FILENAME}:{lineno} is not a record",
        )
        loaded.append(record)
    return loaded


def _status(replayed: int, failed: int) -> str:
    if failed:
        return "failed"
    return "passed" if replayed else "nothing_to_replay"


def _summary(
    request: ReplayRequest, catalog: cat.Catalog, executor: ex.Executor,
    entries: list[dict[str, Any]],
) -> dict[str, Any]:
    replayed = [e for e in entries if e["status"] == "replayed"]
    by_code = Counter(e["code"] for e in replayed)
    failed = sum(n for code, n in by_code.items() if code != cv.REPLAY_PASSED)
    return {
        "format": REPLAY_FORMAT, "family": cv.FAMILY, "run": Path(request.run_dir).name,
        "catalog": {"catalog_id": catalog.catalog_id, "programs_sha256": catalog.programs_sha256},
        "harness_sha256": executor.harness_sha256,
        "interpreter": ".".join(platform.python_version().split(".")[:2]),
        "status": _status(len(replayed), failed),
        "counts": {
            "records": len(entries), "positives": len(replayed),
            "passed": by_code[cv.REPLAY_PASSED],
            "failed": failed, "not_replayed": len(entries) - len(replayed),
            "failed_by_code": {
                c: n for c, n in sorted(by_code.items()) if c != cv.REPLAY_PASSED
            },
        },
        "records": sorted(entries, key=lambda e: str(e["record_id"])),
    }


def run(request: ReplayRequest, executor: ex.Executor | None = None) -> dict[str, Any]:
    """Replay every positive record of a run; write REPLAY.json and the volatile log."""

    _check_request(request)
    catalog = cat.load_catalog(request.catalog_dir)
    engine = ex.Executor(timeout_s=request.timeout_s) if executor is None else executor
    entries = [replay_record(record, catalog, engine) for record in _records(Path(request.run_dir))]
    summary = _summary(request, catalog, engine, entries)
    out = Path(request.out_dir)
    out.mkdir(parents=True, exist_ok=False)
    oc.write_jsonl(out / REPLAY_LOG_FILENAME, engine.log)
    with open(out / REPLAY_FILENAME, "x", encoding="utf-8") as handle:
        handle.write(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    return summary


bind_import_twin(__name__)
