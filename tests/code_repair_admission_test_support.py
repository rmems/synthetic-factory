"""Shared evidence construction for code-repair admission regressions."""

from __future__ import annotations

import hashlib
import tempfile
from pathlib import Path

from tests.code_repair_test_support import REPO, envelope, fixture, generate, oc
from tests.test_curate_identity import identity as ci
from code_repair import catalog, records, validation, verify


def restamp(record):
    """Recompute the envelope digest after a deliberate test mutation."""
    record["provenance"]["record_sha256"] = envelope.record_digest(record)


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


def build_generated_admission_evidence(test_case):
    """Build and attach the sealed real-catalog evidence for a test class."""

    scratch = tempfile.TemporaryDirectory(prefix="admission-real-evidence-")
    root = Path(scratch.name)
    test_case.addClassCleanup(scratch.cleanup)
    run_dir = root / "generated"
    generate.run(
        generate.RunRequest(
            REPO / "catalogs/python-repair-v1",
            run_dir,
            20260908,
            12,
            "2026-09-09T00:00:00.000Z",
        )
    )
    records = [
        record for _, record in oc.read_jsonl(run_dir / generate.CANDIDATES_FILENAME)
    ]
    row = ci.load_registry().by_path_id["python-function-repair-factory"]
    return root, run_dir, records, row
