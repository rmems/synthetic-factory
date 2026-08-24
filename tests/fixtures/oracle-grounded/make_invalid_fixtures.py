#!/usr/bin/env python3
"""Regenerate the invalid fixtures by mutating records from the golden run.

Each fixture is one accepted record with exactly one thing wrong, tagged with a
`_defect` key naming what was broken. `tests/test_oracle_grounded_cli.py` asserts
that every defect is still caught and that the finding mentions the right thing,
so this file is the record of *how* each defect was constructed.

Run it after changing the record envelope, then re-run the tests:

    python3 tests/fixtures/oracle-grounded/make_invalid_fixtures.py
    python3 -m unittest discover -s tests -p 'test_*.py' -q

Not a test module: unittest discovery only picks up `test_*.py`.
"""

import copy
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / "pipelines"))

from oracle_grounded import canon  # noqa: E402
from oracle_grounded import families  # noqa: E402

GOLDEN = HERE / "golden-r01"
OUT = HERE / "invalid"


def load(family, verdict="accepted"):
    path = GOLDEN / family / f"{verdict}-r01.jsonl"
    import json

    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def emit(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(canon.dumps_record(item) + "\n" for item in records), encoding="utf-8"
    )
    print(f"wrote {path.relative_to(REPO)} ({len(records)} records)")


def mutate(source, defect, apply_defect):
    item = copy.deepcopy(source)
    item["_defect"] = defect
    apply_defect(item)
    return item


def main():
    encoder = load(families.ENCODER_FAMILY)[0]
    neuron = load(families.NEURON_FAMILY)[0]
    mesh = load(families.MESH_FAMILY)[0]
    credit = load(families.CREDIT_FAMILY)[0]
    memory_rejected = load(families.MEMORY_FAMILY, "rejected")[0]

    def drop_result(item):
        item["result"] = {}

    def misattribute(item):
        item["result"]["produced_by"] = "some-other-oracle"
        item["result_hash"] = canon.digest(item["result"])

    def stale_hash(item):
        # Change a measurement without restamping result_hash.
        item["result"]["measured"]["retention_margin"] += 0.5

    def unknown_commit(item):
        item["oracle"]["commit"] = "unknown"

    def no_module_digest(item):
        item["oracle"]["module_digest"] = ""

    def claims_publishable(item):
        item["validation"]["publishable"] = True
        item["validation"]["publishable_reason"] = "measured by axon-encoder"

    def empty_measurement(item):
        item["result"]["measured"] = {}
        item["result_hash"] = canon.digest(item["result"])

    def no_stages(item):
        item["oracle"]["stages"] = []

    def claims_named_runtime(item):
        item["oracle"]["implementation"] = "named-runtime"
        item["oracle"]["authority"] = "measured-runtime"
        item["oracle"]["runtime_bound"] = True

    emit(
        OUT / "invalid-oracle.jsonl",
        [
            mutate(encoder, "missing_result", drop_result),
            mutate(encoder, "result_not_attributed_to_declared_oracle", misattribute),
            mutate(encoder, "result_hash_does_not_cover_result", stale_hash),
            mutate(neuron, "oracle_commit_unknown", unknown_commit),
            mutate(neuron, "oracle_module_digest_missing", no_module_digest),
            mutate(mesh, "reference_oracle_claims_publishable", claims_publishable),
            mutate(mesh, "empty_measurement", empty_measurement),
            mutate(credit, "no_executed_stages", no_stages),
            mutate(
                credit, "reference_run_relabelled_as_named_runtime", claims_named_runtime
            ),
        ],
    )

    def reserved_key(item):
        item["scenario"]["measured"] = {"information_retention": 1.0}

    def tampered_proposal(item):
        item["scenario"]["sample_count"] += 1

    def claims_authority(item):
        item["generator"]["authoritative"] = True

    def guess_posing_as_truth(item):
        item["candidate_prediction"]["kind"] = "ground_truth"

    def empty_scenario(item):
        item["scenario"] = {}

    def relabelled_accepted(item):
        item["validation"]["status"] = "accepted"
        item["validation"]["reasons"] = []

    def reason_rewritten(item):
        item["validation"]["reasons"] = ["looks fine to me"]

    emit(
        OUT / "malformed-generator.jsonl",
        [
            mutate(encoder, "generator_authored_a_measurement_key", reserved_key),
            mutate(encoder, "scenario_edited_after_proposal_hash", tampered_proposal),
            mutate(neuron, "generator_claims_authority", claims_authority),
            mutate(
                neuron,
                "candidate_prediction_posing_as_ground_truth",
                guess_posing_as_truth,
            ),
            mutate(mesh, "empty_scenario", empty_scenario),
            mutate(
                memory_rejected, "failing_record_relabelled_accepted", relabelled_accepted
            ),
            mutate(memory_rejected, "rejection_reason_rewritten", reason_rewritten),
        ],
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
