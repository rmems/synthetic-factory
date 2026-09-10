#!/usr/bin/env python3
"""Replay: every positive record re-executed with the pinned catalog and harness.

Recomputing digests and re-deriving verdicts from stored rows proves a
record is self-consistent, not that the execution happened: a forgery whose
rows, hashes and verdict were all rewritten together passes every stored
check. Replay is the only evidence that survives such a forgery. For each
accepted, validated record it binds the program to the catalog's pinned text,
the harness on disk to the fingerprint and the recorded mutation to the actual
edit, then runs the original, the broken and the repaired module afresh
and demands the same rows, the same hashes and the same verdict. Records that
are not positive (rejected, abstained, provisional) are listed as not replayed
by natural ineligibility. Fresh evidence also binds the implementation, platform,
applied limits and public prompt evidence. ``REPLAY.json`` is an audit artifact;
admission must invoke fresh replay with a trusted catalog, not trust a stored report.
The volatile timings go to a separate log.
"""

from __future__ import annotations

import hashlib
import json
import platform
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import catalog as cat
from . import executor as ex
from . import generate
from . import mutate
from . import record_validation as validation
from . import verify
from . import views
from . import vocabulary as cv
from ._contract import bind_import_twin, is_under_raw, load_strict_json, oc

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
    return {"record_id": record.get("id"), "status": "replayed", "code": code, "detail": detail}


def _hidden_check_moved(record: dict[str, Any], program: cat.Program) -> bool:
    """The record's stored oracle configuration must be the catalog's cases and reference."""

    stored = record["oracle"]["configuration"]["hidden_check"]
    reference = program.reference
    pinned = {
        "kind": reference.kind, "reference_function": reference.function,
        "reference_sha256": reference.sha256, "cases": list(program.cases),
    }
    return {key: stored.get(key) for key in pinned} != pinned


def _catalog_drift(record: dict[str, Any], catalog: cat.Catalog) -> str | None:
    """Why the catalog is no longer the record's program, or None."""

    source = record["scenario"]["source"]
    program_id = source["program_id"]
    program = next((p for p in catalog.programs if p.program_id == program_id), None)
    if program is None or program.sha256 != source["module_sha256"]:
        return "the catalog does not pin this program"
    if program.upstream != source["upstream"]:
        return "the program's upstream identity moved"
    if _hidden_check_moved(record, program):
        return "the hidden cases or reference moved"
    expected_lineage = {
        "lineage_id": program.program_id, "group_id": program.group_id, "split": program.split,
        "policy_sha256": None if catalog.split_policy is None else catalog.split_policy.sha256,
    }
    if record["provenance"].get("split_lineage") != expected_lineage:
        return "the program's lineage, group or split moved"
    return None


def _drift(record: dict[str, Any], catalog: cat.Catalog, executor: ex.Executor) -> dict | None:
    """The catalog, harness or interpreter no longer being the record's, as an entry."""

    moved = _catalog_drift(record, catalog)
    if moved is not None:
        return _entry(record, cv.REPLAY_CATALOG_DRIFT, moved)
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
    intervention = record["intervention"]
    matches = [site for site in mutate.sites(program.text, program.function, program.want_kind)
               if site.operator == intervention.get("operator")
               and site.variant == intervention.get("variant")
               and site.as_json() == intervention.get("site")]
    if intervention.get("kind") != "ast_mutation" or len(matches) != 1:
        return _entry(record, cv.REPLAY_TEXT_MISMATCH, "intervention is not a catalog mutation site")
    site = matches[0]
    if (mutate.apply(program.text, site) != broken or mutate.repair(broken, site) != repaired
            or mutate.verify(program.text, broken, site, program.function) is not None):
        return _entry(record, cv.REPLAY_TEXT_MISMATCH, "intervention does not reproduce mutant")
    return broken, repaired


@dataclass(frozen=True)
class _Subject:
    """One positive record bound to its pinned program and its two texts."""

    label: str
    program: cat.Program
    broken: str
    repaired: str


def _fresh_phases(subject: _Subject, executor: ex.Executor) -> verify.Phases:
    """Both originals, mutant, repair and pinned reference executed afresh."""

    program, label = subject.program, subject.label
    original = executor.run(program.job(f"{cv.PHASE_ORIGINAL}:{label}"))
    repeated = executor.run(program.job(f"{cv.PHASE_ORIGINAL_REPEAT}:{label}"))
    reference = None
    if program.reference.certifying:
        reference = executor.run(program.reference_job(f"{cv.PHASE_REFERENCE}:{label}"))
    return verify.Phases(
        original,
        executor.run(program.job(f"{cv.PHASE_MUTANT}:{label}", subject.broken)),
        executor.run(program.job(f"{cv.PHASE_REPAIRED}:{label}", subject.repaired)),
        reference,
        repeated,
    )


def _compare(
    record: dict[str, Any], program: cat.Program, phases: verify.Phases, repaired: str
) -> dict[str, Any]:
    """Fresh rows, hashes and verdict against the stored ones; the first divergence decides."""

    result = record["result"]
    environment = phases.original.environment
    fingerprint = record["oracle"]["fingerprint"]
    fresh = {key: environment.get(key) for key in ("implementation", "platform", "limits_applied")}
    fresh["python"] = ".".join(str(environment.get("python", "")).split(".")[:2])
    if any(fingerprint.get(key) != value for key, value in fresh.items()):
        return _entry(record, cv.REPLAY_ENVIRONMENT_DRIFT, "fresh execution environment differs")
    public = {"kind": "doctest", "examples": [
        {"example_id": e.example_id, "source": e.source, "want": e.want} for e in program.examples
    ]}
    evidence, omitted = verify.public_evidence(phases.mutant, program.examples)
    if (record["scenario"].get("public_tests") != public
            or result.get("public_failure_evidence") != evidence
            or result.get("public_failure_omitted") != omitted):
        return _entry(record, cv.REPLAY_ROWS_MISMATCH, "fresh public examples or evidence differ")
    blocks = {name: verify.phase_block(getattr(phases, name)) for name in cv.PHASES}
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
    entry["record_sha256"] = record["provenance"]["record_sha256"]
    entry["source_sha256"] = program.sha256
    entry["broken_sha256"] = result["broken_sha256"]
    entry["repaired_sha256"] = result["repaired_sha256"]
    entry["harness_sha256"] = fingerprint["harness_sha256"]
    return entry


def replay_record(
    record: dict[str, Any], catalog: cat.Catalog, executor: ex.Executor
) -> dict[str, Any]:
    """One record's replay entry; naturally ineligible records are listed, never executed.

    A record that *claims* to be a positive but fails the contract or its digest is a
    failed entry, never natural ineligibility (Greptile and Codex on #202).
    """

    result = record.get("result") if isinstance(record.get("result"), dict) else {}
    claims_positive = (
        result.get("outcome") == cv.OUTCOME_ACCEPTED
        and result.get("oracle_status") == cv.STATUS_VALIDATED
        and result.get("status") == oc.RESULT_MEASURED
    )
    if not claims_positive:
        return {
            "record_id": record.get("id"), "status": "not_replayed",
            "reason": "natural ineligibility",
            "outcome": result.get("outcome"), "oracle_status": result.get("oracle_status"),
        }
    where = str(record.get("id", "record"))
    if oc.check_envelope(record, where) or oc.check_digest(record, where):
        return _entry(record, cv.REPLAY_HASH_MISMATCH, "claims a positive but fails the contract")
    try:
        validation.validate_shape(record)
        eligible, _ = oc.curation_eligible(record, oc.check_oracle_label_leak(record, where))
        if not eligible:
            return _entry(record, cv.REPLAY_HASH_MISMATCH, "claims a positive but fails curation")
        if not _record_identity_matches(record, catalog):
            return _entry(record, cv.REPLAY_RECORD_MALFORMED, "record identity or generator version differs")
        return _replay_positive(record, catalog, executor)
    except (cv.RepairRefusal, KeyError, TypeError, ValueError, AttributeError) as exc:
        return _entry(record, cv.REPLAY_RECORD_MALFORMED, f"{type(exc).__name__} while reading")


def _record_identity_matches(record: dict[str, Any], catalog: cat.Catalog) -> bool:
    generator = record["generator"]
    seed, index = generator["seed"], record["intervention"]["draw_index"]
    catalog_digest = cat.sha256_text(oc.canonical_json([catalog.catalog_id, catalog.programs_sha256]))
    return (
        generator.get("name") == cv.GENERATOR_NAME and generator.get("version") == cv.GENERATOR_VERSION
        and type(seed) is int and 0 <= seed <= cv.MAX_SEED
        and type(index) is int and 0 <= index < cv.MAX_COUNT
        and record["id"] == f"{cv.RECORD_ID_PREFIX}-{catalog_digest}-{seed}-{index:05d}"
    )


def _replay_positive(record: dict[str, Any], catalog: cat.Catalog, executor: ex.Executor) -> dict:
    drift = _drift(record, catalog, executor)
    if drift is not None:
        return drift
    program = catalog.program(record["scenario"]["source"]["program_id"])
    texts = _texts(record, program)
    if isinstance(texts, dict):
        return texts
    broken, repaired = texts
    if not validation.verdict_matches(record):
        return _entry(record, cv.REPLAY_VERDICT_MISMATCH, "stored evidence fails protocol verdict bindings")
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


def _run_identity(run_dir: Path) -> dict[str, Any]:
    """What binds this replay to one run: the candidates' bytes and RUN.json's pins."""

    candidates = run_dir / generate.CANDIDATES_FILENAME
    run_file = run_dir / generate.RUN_FILENAME
    cv.refuse_when(not run_file.is_file(), cv.FINDING_RUN_FILE_MISSING, f"{run_file} is missing")
    try:
        summary = load_strict_json(run_file.read_text(encoding="utf-8"))
    except ValueError as exc:
        message = f"{run_file} is not JSON"
        raise cv.RepairRefusal(cv.FINDING_RECORD_MALFORMED, message) from exc
    cv.refuse_when(
        not isinstance(summary, dict), cv.FINDING_RECORD_MALFORMED,
        f"{run_file} is not a run summary",
    )
    cv.refuse_when(
        summary.get("format") != generate.RUN_FORMAT
        or summary.get("generator") != {"name": cv.GENERATOR_NAME, "version": cv.GENERATOR_VERSION},
        cv.FINDING_RECORD_MALFORMED, "run or generator version is unsupported; regenerate legacy runs",
    )
    candidates_digest = hashlib.sha256(candidates.read_bytes()).hexdigest()
    cv.refuse_when(
        summary.get("candidates_sha256") != candidates_digest,
        cv.FINDING_RECORD_MALFORMED,
        "candidates digest is missing or differs from generation; regenerate old unpinned runs",
    )
    count = summary.get("records")
    cv.refuse_when(
        type(count) is not int or count != len(_records(run_dir)),
        cv.FINDING_RECORD_MALFORMED, "candidates count differs from generation",
    )
    from .run_validation import run_identity
    try:
        return run_identity(summary, candidates_digest)
    except (KeyError, TypeError) as exc:
        raise cv.RepairRefusal(cv.FINDING_RECORD_MALFORMED, "malformed run identity") from exc


def _catalog_bound(identity: dict[str, Any], catalog: cat.Catalog) -> bool:
    """The supplied catalog is the one the run pinned (Greptile, CodeAnt and Codex on #202)."""

    pinned = identity["catalog"]
    return (
        pinned["catalog_id"] == catalog.catalog_id
        and pinned["programs_sha256"] == catalog.programs_sha256
    )


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
    identity = _run_identity(Path(request.run_dir))
    cv.refuse_when(
        not _catalog_bound(identity, catalog), cv.FINDING_REPLAY_CATALOG_UNBOUND,
        "the run pinned another catalog (id or programs digest differ)",
    )
    engine = ex.Executor(timeout_s=request.timeout_s) if executor is None else executor
    entries = [replay_record(record, catalog, engine) for record in _records(Path(request.run_dir))]
    summary = {"run_identity": identity, **_summary(request, catalog, engine, entries)}
    out = Path(request.out_dir)
    out.mkdir(parents=True, exist_ok=False)
    oc.write_jsonl(out / REPLAY_LOG_FILENAME, engine.log)
    with open(out / REPLAY_FILENAME, "x", encoding="utf-8") as handle:
        handle.write(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    return summary


bind_import_twin(__name__)
