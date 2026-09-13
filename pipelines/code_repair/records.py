#!/usr/bin/env python3
"""Assembly of one candidate into an oracle-grounded envelope record.

Every section goes through the shared builders; the family adds only
vocabulary. The generator-owned sections (``scenario``, ``intervention``,
``candidate_prediction``) never carry an oracle label, the oracle-owned
``result`` carries the phases, the verdict and the bounded public evidence,
and ``provenance`` carries the pinned timestamp, the actor roles and the
lineage. A record the shared envelope or the family label policy would
refuse is never returned: it is refused here with ``RECORD_FAILS_ENVELOPE``.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

from . import catalog as cat
from . import executor as ex
from . import mutate
from . import verify
from . import vocabulary as cv
from ._contract import bind_import_twin, oc

ORACLE_COMMIT = None
ORACLE_ISOLATION = (
    "rlimits and a fresh working directory only: no filesystem or network isolation "
    "(issue #198); programs come from a pinned catalog whose selector admits stdlib-only modules"
)

__all__ = [
    "Batch", "Candidate", "ORACLE_COMMIT", "ORACLE_ISOLATION", "build_record", "candidate_seed",
    "fingerprint", "measurements", "new_batch",
]


@dataclass(frozen=True)
class Candidate:
    """Everything one record is assembled from."""

    record_id: str
    program: cat.Program
    mutation: mutate.Mutation
    repaired_text: str
    phases: verify.Phases
    verdict: verify.Verdict
    evidence: tuple[dict[str, Any], ...]
    omitted: int
    seed: int
    draw_index: int


@dataclass(frozen=True)
class Batch:
    """What every record of one run shares."""

    run_seed: int
    produced_at: str
    timeout_s: float
    harness_sha256: str
    generator: dict[str, Any]
    provenance: dict[str, Any]
    policy_sha256: str | None = None


def candidate_seed(run_seed: int, program_id: str, draw_index: int) -> int:
    """A 64-bit seed per candidate, so one record is reproducible without the batch."""

    digest = hashlib.sha256(f"{run_seed}:{program_id}:{draw_index}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


def actor(role: str, name: str, version: str) -> dict[str, str]:
    return {"role": role, "kind": cv.GENERATOR_KIND, "name": name, "version": version}


def new_batch(
    run_seed: int, produced_at: str, executor: ex.Executor, policy_sha256: str | None = None
) -> Batch:
    identity = oc.GeneratorIdentity(cv.GENERATOR_NAME, cv.GENERATOR_VERSION, cv.GENERATOR_KIND)
    actors = {
        cv.ROLE_TASK_AUTHOR: actor(cv.ROLE_TASK_AUTHOR, cv.GENERATOR_NAME, cv.GENERATOR_VERSION),
        cv.ROLE_SOLVER: actor(cv.ROLE_SOLVER, cv.SOLVER_NAME, cv.GENERATOR_VERSION),
        cv.ROLE_ORACLE_CERTIFIER: actor(
            cv.ROLE_ORACLE_CERTIFIER, cv.ORACLE_NAME, cv.ORACLE_VERSION
        ),
    }
    provenance = oc.new_provenance(
        cv.PRODUCER, produced_at=produced_at, oracle_run=cv.ORACLE_RUN,
        source_kind=cv.SOURCE_KIND, actors=actors,
    )
    generator = oc.new_generator(identity, seed=run_seed)
    return Batch(
        run_seed, produced_at, executor.timeout_s, executor.harness_sha256, generator, provenance,
        policy_sha256,
    )


def fingerprint(batch: Batch, original: ex.PhaseReport) -> dict[str, Any]:
    """The oracle's environment identity: interpreter major.minor, platform, harness, limits."""

    environment = original.environment
    version = str(environment.get("python", ""))
    return {
        "python": ".".join(version.split(".")[:2]),
        "implementation": environment.get("implementation"),
        "platform": environment.get("platform"),
        "harness_sha256": batch.harness_sha256,
        "limits_applied": environment.get("limits_applied"),
    }


def _scenario(candidate: Candidate) -> dict[str, Any]:
    program = candidate.program
    return {
        "record_kind": cv.RECORD_KIND,
        "task_specification": cv.TASK_SPECIFICATION,
        "language": cv.LANGUAGE,
        "source": {
            "program_id": program.program_id, "family": program.family,
            "upstream": dict(program.upstream), "module_sha256": program.sha256,
        },
        "broken_program": {
            "files": {cv.PROGRAM_FILENAME: candidate.mutation.mutated_text},
            "sha256": cat.sha256_text(candidate.mutation.mutated_text),
        },
        "public_tests": {
            "kind": "doctest",
            "examples": [
                {"example_id": e.example_id, "source": e.source, "want": e.want}
                for e in program.examples
            ],
        },
    }


def _intervention(candidate: Candidate) -> dict[str, Any]:
    site = candidate.mutation.site
    return {
        "kind": "ast_mutation", "operator": site.operator, "site": site.as_json(),
        "variant": site.variant, "draw_index": candidate.draw_index,
    }


def _prediction(candidate: Candidate) -> dict[str, Any]:
    return {
        "predicted_repair": {
            "files": {cv.PROGRAM_FILENAME: candidate.repaired_text},
            "sha256": cat.sha256_text(candidate.repaired_text),
        },
        "method": cv.REPAIR_METHOD,
    }


def _oracle(candidate: Candidate, batch: Batch) -> dict[str, Any]:
    program = candidate.program
    identity = oc.OracleIdentity(
        cv.ORACLE_NAME, cv.ORACLE_TYPE, cv.ORACLE_IMPLEMENTATION, cv.ORACLE_VERSION
    )
    configuration = {
        "timeout_s": batch.timeout_s,
        "limits": {
            "cpu_s": int(batch.timeout_s) + 2, "address_space_mib": cv.ADDRESS_SPACE_MIB,
            "file_size_kib": cv.FILE_SIZE_KIB,
        },
        "hidden_check": {
            "kind": program.reference.kind, "reference_function": program.reference.function,
            "reference_sha256": program.reference.sha256,
            "cases": [dict(case) for case in program.cases],
        },
        "isolation": ORACLE_ISOLATION,
    }
    environment = fingerprint(batch, candidate.phases.original)
    run = oc.OracleRun(configuration, candidate.seed, ORACLE_COMMIT, environment)
    return oc.new_oracle(identity, run)


def _suite_readings(phase: str, suite: str, rows: tuple[dict, ...]) -> list[dict[str, Any]]:
    failed = len(verify.failing_ids(rows))
    detail = {"phase": phase, "suite": suite}
    counts = (("passed_check_count", len(rows) - failed), ("failed_check_count", failed))
    return [oc.new_measurement(name, value, cv.METER, detail=detail) for name, value in counts]


def measurements(phases: verify.Phases) -> list[dict[str, Any]]:
    """Exact ordered readings shared by record assembly and pure evidence validation."""

    if not phases.original.ok:
        return []
    readings: list[dict[str, Any]] = []
    reports = ((name, getattr(phases, name)) for name in cv.PHASES)
    for phase, report in ((p, r) for p, r in reports if r is not None and r.ok):
        if phase != cv.PHASE_REFERENCE:  # the reference runs the hidden cases only
            readings += _suite_readings(phase, cv.SUITE_PUBLIC, report.public)
        readings += _suite_readings(phase, cv.SUITE_HIDDEN, report.hidden)
    return readings


def _result(candidate: Candidate) -> dict[str, Any]:
    phases = candidate.phases
    blocks = {
        cv.PHASE_ORIGINAL: verify.phase_block(phases.original),
        cv.PHASE_MUTANT: verify.phase_block(phases.mutant),
        cv.PHASE_REPAIRED: verify.phase_block(phases.repaired),
        cv.PHASE_REFERENCE: verify.phase_block(phases.reference),
        cv.PHASE_ORIGINAL_REPEAT: verify.phase_block(phases.original_repeat),
    }
    fields: dict[str, Any] = {
        "outcome": candidate.verdict.outcome,
        "reason_codes": list(candidate.verdict.reason_codes),
        "oracle_status": candidate.verdict.oracle_status,
        "phases": blocks,
        "public_failure_evidence": list(candidate.evidence),
        "public_failure_omitted": candidate.omitted,
        "broken_sha256": cat.sha256_text(candidate.mutation.mutated_text),
        "repaired_sha256": cat.sha256_text(candidate.repaired_text),
        "evidence_sha256": verify.result_hash(blocks),
    }
    if not phases.original.ok:
        # A coded reason only: the harness detail can name the volatile workdir and belongs to
        # the execution log, never to a stable record (Codex on #197).
        code = candidate.verdict.reason_codes[0] if candidate.verdict.reason_codes else ""
        reason = f"{code}: the harness could not measure the original program"
        return oc.new_result(status=oc.RESULT_ABSTAINED, abstention_reason=reason, **fields)
    return oc.new_result(measurements=measurements(phases), **fields)


def build_record(candidate: Candidate, batch: Batch) -> dict[str, Any]:
    """One built record, refused if the shared envelope or the label policy would refuse it."""

    provenance = dict(batch.provenance)
    provenance["split_lineage"] = {
        "lineage_id": candidate.program.program_id, "group_id": candidate.program.group_id,
        "split": candidate.program.split, "policy_sha256": batch.policy_sha256,
    }
    record = oc.build_record(
        identity=oc.RecordIdentity(candidate.record_id, cv.FAMILY),
        proposal=oc.Proposal(
            generator=batch.generator, scenario=_scenario(candidate),
            intervention=_intervention(candidate), candidate_prediction=_prediction(candidate),
        ),
        verdict=oc.Verdict(oracle=_oracle(candidate, batch), result=_result(candidate)),
        provenance=provenance,
    )
    findings = oc.check_envelope(record, candidate.record_id)
    findings += oc.check_oracle_label_leak(record, candidate.record_id)
    cv.refuse_when(
        bool(findings), cv.FINDING_RECORD_FAILS_ENVELOPE,
        f"the family produced a record the shared contract refuses ({len(findings)} finding(s); "
        f"first: {findings[0] if findings else ''})",
    )
    return record


bind_import_twin(__name__)
