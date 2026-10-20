"""Shared evidence construction for code-repair admission regressions."""

from __future__ import annotations

import atexit
import functools
import hashlib
import shutil
import tempfile
from pathlib import Path

from tests.code_repair_test_support import REPO, envelope, fixture, generate, oc
from tests.test_curate_identity import identity as ci
from code_repair import catalog, records, validation, verify

REAL_CATALOG = REPO / "catalogs/python-repair-v1"
REAL_SEED, REAL_COUNT, REAL_PRODUCED_AT = 20260907, 12, "2026-09-09T00:00:00.000Z"
PROCEDURAL_FACTORY = "python-function-repair-factory"
RAW_RUN = Path("outputs/raw/2099-01-01")


def restamp(record):
    """Recompute the envelope digest after a deliberate test mutation."""
    record["provenance"]["record_sha256"] = envelope.record_digest(record)


def passing_rows(record, suite):
    """Iterate retained passing observations across the phases that ran."""
    phases = (phase for phase in record["result"]["phases"].values() if phase is not None)
    return (row for phase in phases for row in phase[suite] if row["status"] == "pass")


def restamp_evidence(record, *, refresh_public_evidence=False):
    """Restamp every emitter-owned digest after a coherent evidence mutation."""

    result = record["result"]
    for block in result["phases"].values():
        if block is not None:
            block["sha256"] = catalog.sha256_text(oc.canonical_json(
                [block["public"], block["hidden"]]
            ))
    phases = verify.phases_from_blocks(result["phases"])
    result["measurements"] = records.measurements(phases)
    if refresh_public_evidence:
        scenario = record["scenario"]
        examples = catalog.examples_of(
            scenario["broken_program"]["files"]["program.py"],
            scenario["source"]["upstream"]["function"],
        )
        evidence, omitted = verify.public_evidence(phases.mutant, examples)
        result["public_failure_evidence"] = evidence
        result["public_failure_omitted"] = omitted
    result["evidence_sha256"] = verify.result_hash(result["phases"])
    restamp(record)


def validate_captured_run(run, candidates, *, trusted_catalog=None):
    """Bind a candidate sequence to one run and invoke the real run validator."""
    payload = "".join(oc.canonical_json(record) + "\n" for record in candidates).encode()
    run["candidates_sha256"] = hashlib.sha256(payload).hexdigest()
    return validation.validate_run(
        run,
        candidates,
        catalog=fixture() if trusted_catalog is None else trusted_catalog,
        candidates_sha256=run["candidates_sha256"],
    )


def _process_scratch(prefix):
    """A temporary directory that lives until the test process exits."""

    root = Path(tempfile.mkdtemp(prefix=prefix))
    atexit.register(shutil.rmtree, root, True)
    return root


@functools.cache
def sealed_real_run():
    """One real-catalog generation per process, as ``(root, run_dir)``.

    The run is deterministic for its pinned seed, count and stamp, so every
    class that only reads it shares one copy instead of re-executing the
    catalog. Callers must not write under ``root``; copy the run first.
    """

    root = _process_scratch("admission-real-evidence-")
    run_dir = root / "generated"
    generate.run(generate.RunRequest(
        REAL_CATALOG, run_dir, REAL_SEED, REAL_COUNT, REAL_PRODUCED_AT,
    ))
    return root, run_dir


@functools.cache
def sealed_published_factory():
    """One real publication of :func:`sealed_real_run` per process (read-only)."""

    # Imported here so modules that never publish keep their import graph unchanged.
    from code_repair import publication

    factory = _process_scratch("procedural-published-") / RAW_RUN / PROCEDURAL_FACTORY
    factory.mkdir(parents=True)
    publication.publish_run(publication.PublishRequest(sealed_real_run()[1], factory, 1))
    return factory


def copy_published_factory(run_root):
    """A private copy of the sealed published round, at ``run_root/<factory>``."""

    factory = Path(run_root) / PROCEDURAL_FACTORY
    factory.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(sealed_published_factory(), factory)
    return factory


def build_generated_admission_evidence():
    """The sealed real-catalog evidence: shared run, private records, registry row."""

    root, run_dir = sealed_real_run()
    records = [
        record for _, record in oc.read_jsonl(run_dir / generate.CANDIDATES_FILENAME)
    ]
    row = ci.load_registry().by_path_id[PROCEDURAL_FACTORY]
    return root, run_dir, records, row
