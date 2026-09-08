#!/usr/bin/env python3
"""The run engine: seeded candidates from a pinned catalog into a new run directory.

One :class:`rng.DrawStream` per run draws, for every candidate index, a
program (among those with sites and under the per-program cap), a site and its
variant; the mutant is verified before it runs; the original phase is executed
once per program and shared; the repaired phase runs only when no earlier rule
has already rejected the candidate. Every executed candidate becomes a record
(accepted or rejected); generator-side non-proposals are counted in
``RUN.json`` and never written as records. The run directory holds
``candidates.jsonl`` (stable bytes for a pinned ``produced_at``), ``RUN.json``
and ``execution-log.jsonl`` (both volatile: wall clocks, exit codes).
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import catalog as cat
from . import executor as ex
from . import mutate
from . import records
from . import verify
from . import vocabulary as cv
from ._contract import bind_import_twin, envelope, is_under_raw, oc, rng, vocab

CANDIDATES_FILENAME = "candidates.jsonl"
RUN_FILENAME = "RUN.json"
LOG_FILENAME = "execution-log.jsonl"
RUN_FORMAT = "code-repair-run/1"

__all__ = ["CANDIDATES_FILENAME", "LOG_FILENAME", "RUN_FILENAME", "RunRequest", "run"]


@dataclass(frozen=True)
class RunRequest:
    catalog_dir: Path
    out_dir: Path
    seed: int
    count: int
    produced_at: str | None = None
    timeout_s: float = cv.DEFAULT_TIMEOUT_S
    per_program_cap: int = cv.DEFAULT_PER_PROGRAM_CAP


@dataclass(frozen=True)
class _Draft:
    """A verified mutant about to be executed."""

    program: cat.Program
    record_id: str
    mutation: mutate.Mutation
    repaired: str


@dataclass
class _State:
    """The mutable accumulators of one run."""

    catalog: cat.Catalog
    executor: ex.Executor
    batch: records.Batch
    stream: rng.DrawStream
    sites: dict[str, tuple[mutate.Site, ...]]
    cap: int
    records: list[dict[str, Any]] = field(default_factory=list)
    skips: Counter = field(default_factory=Counter)
    reasons: Counter = field(default_factory=Counter)
    per_program: Counter = field(default_factory=Counter)
    originals: dict[str, ex.PhaseReport] = field(default_factory=dict)
    seen: set[tuple[str, str]] = field(default_factory=set)


def _check_request(request: RunRequest) -> str:
    """Every cheap refusal before a catalog is read; returns the pinned or fresh stamp."""

    seed = request.seed
    cv.refuse_first((
        (not vocab.is_genuine_int(seed), cv.FINDING_SEED_NOT_AN_INTEGER,
         f"seed must be an integer, got {cv.shown(seed)}"),
        (vocab.is_genuine_int(seed) and not 0 <= seed <= cv.MAX_SEED, cv.FINDING_SEED_OUT_OF_DOMAIN,
         f"seed must lie in [0, {cv.MAX_SEED}] (a 64-bit integer), got {cv.shown(seed)}"),
        (not vocab.is_genuine_int(request.count) or not 1 <= request.count <= cv.MAX_COUNT,
         cv.FINDING_COUNT_OUT_OF_DOMAIN,
         f"count must be an integer in [1, {cv.MAX_COUNT}], got {cv.shown(request.count)}"),
        (not vocab.is_genuine_int(request.per_program_cap)
         or not 1 <= request.per_program_cap <= cv.MAX_PER_PROGRAM_CAP,
         cv.FINDING_CAP_OUT_OF_DOMAIN,
         f"per_program_cap must be an integer in [1, {cv.MAX_PER_PROGRAM_CAP}], "
         f"got {cv.shown(request.per_program_cap)}"),
        (request.produced_at is not None and not vocab.is_timestamp(request.produced_at),
         cv.FINDING_PRODUCED_AT_NOT_A_TIMESTAMP,
         f"produced_at must be an ISO-8601 UTC instant, got {cv.shown(request.produced_at)}"),
    ))
    _check_destination(Path(request.out_dir))
    return envelope.utc_now_iso() if request.produced_at is None else request.produced_at


def _check_destination(out_dir: Path) -> None:
    cv.refuse_first((
        (is_under_raw(out_dir), cv.FINDING_DESTINATION_UNDER_RAW,
         f"{out_dir} names or aliases the raw tree"),
        (out_dir.exists(), cv.FINDING_DESTINATION_EXISTS, f"{out_dir} already exists"),
    ))


def _original(state: _State, program: cat.Program) -> ex.PhaseReport:
    if program.program_id not in state.originals:
        label = f"{cv.PHASE_ORIGINAL}:{program.program_id}"
        state.originals[program.program_id] = state.executor.run(program.job(label))
    return state.originals[program.program_id]


def _draw_program(state: _State) -> cat.Program | None:
    """A program with sites and room under the cap, or None when every one is exhausted."""

    eligible = [
        p for p in state.catalog.programs
        if state.sites[p.program_id] and state.per_program[p.program_id] < state.cap
    ]
    return state.stream.choice(eligible) if eligible else None


def _candidate(state: _State, program: cat.Program, index: int) -> records.Candidate | str:
    """One executed candidate, or the skip code of a non-proposal."""

    site = mutate.choose(state.stream, state.sites[program.program_id])
    mutated = mutate.apply(program.text, site)
    skip = mutate.verify(program.text, mutated, site, program.function)
    if skip is not None:
        return skip
    key = (program.program_id, cat.sha256_text(mutated))
    if key in state.seen:
        return cv.SKIP_DUPLICATE_MUTANT_IN_RUN
    state.seen.add(key)
    record_id = f"{cv.RECORD_ID_PREFIX}-{state.batch.run_seed}-{index:05d}"
    mutation = mutate.Mutation(site, program.text, mutated)
    repaired = mutate.repair(mutated, site)
    phases, context = _execute(state, _Draft(program, record_id, mutation, repaired))
    verdict = verify.decide(phases, context)
    evidence, omitted = verify.public_evidence(phases.mutant, program.examples)
    seed = records.candidate_seed(state.batch.run_seed, program.program_id, index)
    return records.Candidate(
        record_id, program, mutation, repaired, phases, verdict, tuple(evidence), omitted, seed,
        index,
    )


def _execute(state: _State, draft: _Draft) -> tuple[verify.Phases, verify.DecisionContext]:
    """The three phases: the repaired one only when no earlier rule rejects."""

    program, record_id = draft.program, draft.record_id
    mutation, repaired = draft.mutation, draft.repaired
    tampered = verify.tests_tampered(program.examples, repaired, program.function)
    context = verify.DecisionContext(
        program.reference.kind, repaired == program.text, tampered, len(program.cases)
    )
    phases = verify.Phases(_original(state, program))
    if verify.pre_repair_problem(phases, context) in (None, cv.REASON_MUTANT_HARNESS_ERROR):
        # The original passed (the only way past its rules with no mutant yet): run the mutant.
        mutant_job = program.job(f"{cv.PHASE_MUTANT}:{record_id}", mutation.mutated_text)
        phases = verify.Phases(phases.original, state.executor.run(mutant_job))
    if verify.pre_repair_problem(phases, context) is None:
        repaired_job = program.job(f"{cv.PHASE_REPAIRED}:{record_id}", repaired)
        repaired_report = state.executor.run(repaired_job)
        phases = verify.Phases(phases.original, phases.mutant, repaired_report)
    return phases, context


def _summary(request: RunRequest, state: _State, stamp: str) -> dict[str, Any]:
    outcomes = Counter(record["result"]["outcome"] for record in state.records)
    statuses = Counter(record["result"]["oracle_status"] for record in state.records)
    return {
        "format": RUN_FORMAT,
        "family": cv.FAMILY,
        "catalog": {
            "catalog_id": state.catalog.catalog_id,
            "programs_sha256": state.catalog.programs_sha256,
            "program_count": len(state.catalog.programs),
        },
        "generator": {"name": cv.GENERATOR_NAME, "version": cv.GENERATOR_VERSION},
        "harness_sha256": state.executor.harness_sha256,
        "seed": request.seed, "count": request.count, "produced_at": stamp,
        "timeout_s": state.executor.timeout_s, "per_program_cap": state.cap,
        "records": len(state.records),
        "outcomes": dict(sorted(outcomes.items())),
        "oracle_statuses": dict(sorted(statuses.items())),
        "reasons": dict(sorted(state.reasons.items())),
        "skips": dict(sorted(state.skips.items())),
        "programs": {
            p.program_id: {
                "sites": len(state.sites[p.program_id]),
                "records": state.per_program[p.program_id],
            }
            for p in state.catalog.programs
        },
    }


def _write(out_dir: Path, state: _State, summary: dict[str, Any]) -> None:
    out_dir.mkdir(parents=True, exist_ok=False)
    oc.write_jsonl(out_dir / CANDIDATES_FILENAME, state.records)
    oc.write_jsonl(out_dir / LOG_FILENAME, state.executor.log)
    with open(out_dir / RUN_FILENAME, "x", encoding="utf-8") as handle:
        handle.write(json.dumps(summary, indent=2, sort_keys=True) + "\n")


def run(request: RunRequest, executor: ex.Executor | None = None) -> dict[str, Any]:
    """Generate ``request.count`` candidates into ``request.out_dir``; returns the summary."""

    stamp = _check_request(request)
    catalog = cat.load_catalog(request.catalog_dir)
    engine = ex.Executor(timeout_s=request.timeout_s) if executor is None else executor
    sites = {p.program_id: mutate.sites(p.text, p.function) for p in catalog.programs}
    batch = records.new_batch(request.seed, stamp, engine)
    stream = rng.DrawStream(request.seed)
    state = _State(catalog, engine, batch, stream, sites, request.per_program_cap)
    state.skips[cv.SKIP_MUTATION_NO_SITES] = sum(1 for s in sites.values() if not s)
    for index in range(request.count):
        program = _draw_program(state)
        if program is None:
            state.skips[cv.SKIP_PROGRAM_CAP_EXHAUSTED] += request.count - index
            break
        outcome = _candidate(state, program, index)
        if isinstance(outcome, str):
            state.skips[outcome] += 1
            continue
        state.records.append(records.build_record(outcome, state.batch))
        state.per_program[program.program_id] += 1
        state.reasons.update(outcome.verdict.reason_codes)
    summary = _summary(request, state, stamp)
    _write(Path(request.out_dir), state, summary)
    return summary


bind_import_twin(__name__)
