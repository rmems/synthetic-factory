"""Independent, fail-closed VSET oracle binder coverage."""

from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

_TESTS = Path(__file__).resolve().parent
_PIPELINES = _TESTS.parent / "pipelines"
for _path in (str(_TESTS), str(_PIPELINES)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

import verify_execution
from bind_vset_oracle import bind_vset_oracle
from vset_testutil import ACCEPT, PACK, REJECT, load_record

ACTOR = {"model": "vset-binder", "version": "1", "run_id": "binder-test-1"}


class VSetOracleBinderTests(unittest.TestCase):
    @staticmethod
    def record() -> dict:
        return load_record(ACCEPT / "issue-patch-validated.json")

    @staticmethod
    def bind(record: dict, pack=PACK):
        return bind_vset_oracle(record, pack, oracle_actor=ACTOR)

    def test_patch_proves_f2p_and_p2p_pre_and_post(self) -> None:
        record = self.record()
        evidence = self.bind(record)
        self.assertEqual(evidence["schema_version"], "oracle_bind_v1")
        self.assertEqual(evidence["status_supported"], "provisional", evidence)
        self.assertFalse(evidence["fail_to_pass"]["before"]["ok"])
        self.assertTrue(evidence["fail_to_pass"]["after"]["ok"])
        self.assertTrue(evidence["pass_to_pass"]["before"]["ok"])
        self.assertTrue(evidence["pass_to_pass"]["after"]["ok"])
        self.assertEqual(evidence["oracle_actor"], ACTOR)
        self.assertNotEqual(evidence["env_digest"], "")
        self.assertNotEqual(evidence["patched_tree_hash"], "")
        for pair_name in ("pass_to_pass", "fail_to_pass"):
            pair = evidence[pair_name]
            self.assertTrue(pair["result_hash"].startswith("sha256:"))
            for side in ("before", "after"):
                self.assertTrue(pair[side]["result_hash"].startswith("sha256:"))
                self.assertTrue(pair[side]["tests"])
        self.assertEqual(record["oracle"]["status"], "validated")

    def test_unpatched_pack_does_not_count_as_f2p(self) -> None:
        record = self.record()
        record["payload"]["patch"]["files"]["src/counter.py"] = (
            PACK / "src" / "counter.py"
        ).read_text(encoding="utf-8")
        evidence = self.bind(record)
        self.assertEqual(evidence["status_supported"], "failed")
        self.assertFalse(evidence["fail_to_pass"]["before"]["ok"])
        self.assertFalse(evidence["fail_to_pass"]["after"]["ok"])

    def test_malformed_record_fails_closed(self) -> None:
        evidence = bind_vset_oracle(None, PACK, oracle_actor=ACTOR)
        self.assertEqual(evidence["status_supported"], "unbound")
        self.assertEqual(evidence["reason"], "record must be an object")

    def test_missing_pack_suites_and_snapshot_fail_closed(self) -> None:
        record = self.record()
        self.assertEqual(self.bind(record, None)["status_supported"], "unbound")
        missing_suite = copy.deepcopy(record)
        missing_suite["oracle"].pop("hidden_tests")
        self.assertEqual(self.bind(missing_suite)["status_supported"], "unbound")
        mismatch = copy.deepcopy(record)
        mismatch["environment"]["repo_snapshot_hash"] = "sha256:" + "0" * 64
        self.assertEqual(self.bind(mismatch)["status_supported"], "unbound")

    def test_solver_claim_does_not_upgrade_status(self) -> None:
        record = load_record(REJECT / "self-certify-solver-pass.json")
        evidence = self.bind(record)
        self.assertEqual(evidence["status_supported"], "provisional")
        self.assertNotIn("validated", evidence.values())
        self.assertEqual(record["oracle"]["status"], "validated")

    def test_review_remediation_baseline_uses_initial_patch(self) -> None:
        record = load_record(ACCEPT / "review-remediation-validated.json")
        record["payload"]["initial_patch"] = copy.deepcopy(record["payload"]["revised_patch"])
        evidence = self.bind(record)
        self.assertEqual(evidence["status_supported"], "failed")
        self.assertTrue(evidence["fail_to_pass"]["before"]["ok"])

    def test_invalid_impossible_is_not_executed(self) -> None:
        record = load_record(ACCEPT / "invalid-impossible.json")
        evidence = self.bind(record)
        self.assertEqual(evidence["status_supported"], "unbound")
        self.assertEqual(record["oracle"]["status"], "invalid")
        self.assertNotIn("fail_to_pass", evidence)

    def test_oracle_actor_must_be_distinct_from_task_author_and_solver(self) -> None:
        record = self.record()
        for role in ("task_author", "solver"):
            actor = {
                key: record[role][key] for key in ("model", "version", "run_id")
            }
            with self.subTest(role=role):
                evidence = bind_vset_oracle(record, PACK, oracle_actor=actor)
                self.assertEqual(evidence["status_supported"], "unbound")
                self.assertIn(f"conflated with {role}", evidence["reason"])
        self.assertEqual(evidence["oracle_actor"], actor)

    def test_suite_result_hashes_are_deterministic(self) -> None:
        record = self.record()
        first = self.bind(record)
        second = self.bind(record)
        self.assertEqual(
            first["pass_to_pass"]["before"]["result_hash"],
            second["pass_to_pass"]["before"]["result_hash"],
        )
        self.assertEqual(
            first["fail_to_pass"]["after"]["result_hash"],
            second["fail_to_pass"]["after"]["result_hash"],
        )

    def test_normalized_run_id_conflation_fails_closed(self) -> None:
        record = self.record()
        actor = {
            "model": "independent-oracle",
            "version": "1",
            "run_id": " " + record["solver"]["run_id"] + " ",
        }
        evidence = bind_vset_oracle(record, PACK, oracle_actor=actor)
        self.assertEqual(evidence["status_supported"], "unbound")
        self.assertIn("conflated with solver", evidence["reason"])

    def test_missing_task_author_or_solver_identity_fails_closed(self) -> None:
        for role in ("task_author", "solver"):
            record = self.record()
            record.pop(role)
            with self.subTest(role=role):
                evidence = self.bind(record)
                self.assertEqual(evidence["status_supported"], "unbound")
                self.assertIn(f"invalid {role} actor identity", evidence["reason"])

    def test_suite_outside_snapshot_fails_closed(self) -> None:
        record = self.record()
        record["oracle"]["hidden_tests"] = ["__pycache__/test_hidden.py"]
        evidence = self.bind(record)
        self.assertEqual(evidence["status_supported"], "unbound")
        self.assertIn("outside the pinned pack snapshot", evidence["reason"])

    def test_vset_record_remains_inconclusive_to_verify_execution(self) -> None:
        status, _reason = verify_execution.verify_record_execution(self.record(), "vset")
        self.assertEqual(status, "inconclusive")


if __name__ == "__main__":
    unittest.main()
