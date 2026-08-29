#!/usr/bin/env python3
"""VSET actor-provenance contract and oracle fixtures (#154 / #155)."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "vset"
PACK = FIXTURES / "repo-pack-counter"
ACCEPT = FIXTURES / "records" / "accept"
REJECT = FIXTURES / "records" / "reject"
VALIDATE = PIPELINES / "validate_vset.py"

sys.path.insert(0, str(PIPELINES))
import record_kind  # noqa: E402
import validate_vset as vset  # noqa: E402
from curate_coding import contains_hidden_reasoning_key  # noqa: E402


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _codes(errors) -> list[str]:
    return [item.code for item in errors]


def _cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VALIDATE), *args],
        cwd=str(REPO),
        capture_output=True,
        text=True,
    )


class ActorProvenanceContractTests(unittest.TestCase):
    def test_accepted_validated_issue_patch_passes(self):
        errors = vset.validate_record(_load(ACCEPT / "issue-patch-validated.json"))
        self.assertEqual(_codes(errors), [])

    def test_provisional_and_invalid_are_first_class_outcomes(self):
        for name in ("provisional.json", "invalid-impossible.json"):
            with self.subTest(name=name):
                record = _load(ACCEPT / name)
                errors = vset.validate_record(record)
                self.assertEqual(_codes(errors), [])
                self.assertIn(record["oracle"]["status"], {"provisional", "invalid"})
                self.assertEqual(record["curation"]["decision"], "measure")

    def test_review_remediation_requires_explicit_reviewer(self):
        ok = _load(ACCEPT / "review-remediation-validated.json")
        self.assertEqual(_codes(vset.validate_record(ok)), [])
        self.assertIsInstance(ok["reviewer"], dict)
        missing = _load(REJECT / "missing-reviewer-when-required.json")
        codes = _codes(vset.validate_record(missing))
        self.assertIn("vset.reviewer_required", codes)

    def test_issue_patch_reviewer_is_optional(self):
        record = _load(ACCEPT / "issue-patch-validated.json")
        self.assertNotIn("reviewer", record)
        self.assertEqual(_codes(vset.validate_record(record)), [])

    def test_task_author_and_solver_cannot_share_a_run(self):
        record = _load(ACCEPT / "issue-patch-validated.json")
        record["solver"]["run_id"] = record["task_author"]["run_id"]
        self.assertIn("vset.actors_conflated", _codes(vset.validate_record(record)))

    def test_missing_solver_fails_closed(self):
        record = _load(REJECT / "missing-actor-role.json")
        self.assertNotIn("solver", record)
        self.assertIn("vset.missing_actor_role", _codes(vset.validate_record(record)))

    def test_solver_success_does_not_self_certify_validated(self):
        record = _load(REJECT / "self-certify-solver-pass.json")
        self.assertEqual(record["solver"]["outcome"], "success")
        self.assertEqual(record["oracle"]["status"], "validated")
        codes = _codes(vset.validate_record(record))
        self.assertIn("vset.oracle_self_certified", codes)

    def test_source_kind_masquerade_fails_closed(self):
        record = _load(REJECT / "source-kind-masquerade.json")
        self.assertEqual(record["source_kind"], "synthetic")
        codes = _codes(vset.validate_record(record))
        self.assertIn("vset.source_kind_masquerade", codes)

    def test_real_public_engineering_cannot_wear_a_vset_pack(self):
        record = _load(ACCEPT / "provisional.json")
        record["source_kind"] = "real_public_engineering"
        codes = _codes(vset.validate_record(record))
        self.assertIn("vset.source_kind_masquerade", codes)

    def test_accept_requires_synthetic_and_validated_oracle(self):
        record = _load(ACCEPT / "provisional.json")
        record["curation"]["decision"] = "accept"
        codes = _codes(vset.validate_record(record))
        self.assertIn("vset.accept_requires_validated_oracle", codes)

    def test_training_view_rejects_hidden_reasoning(self):
        record = _load(REJECT / "hidden-reasoning-in-training-view.json")
        self.assertTrue(contains_hidden_reasoning_key(record["training_view"]))
        codes = _codes(vset.validate_record(record))
        self.assertIn("vset.hidden_reasoning_in_training_view", codes)

    def test_accepted_training_view_is_clean_while_raw_trace_may_keep_thought(self):
        record = _load(ACCEPT / "issue-patch-validated.json")
        self.assertFalse(contains_hidden_reasoning_key(record["training_view"]))
        self.assertIn("thought", record["trace"])
        self.assertEqual(_codes(vset.validate_record(record)), [])

    def test_new_model_occupies_an_existing_role_without_schema_change(self):
        record = _load(ACCEPT / "issue-patch-validated.json")
        record["solver"]["model"] = "gpt-5.6-sol"
        record["solver"]["version"] = "2026-08-28"
        record["task_author"]["model"] = "muse-spark-1.2"
        self.assertEqual(_codes(vset.validate_record(record)), [])

    def test_registry_version_is_the_reviewed_factory_table(self):
        pin = vset.registry_pin()
        self.assertEqual(pin["schema_version"], "factory-registry-v0.1")
        record = _load(ACCEPT / "issue-patch-validated.json")
        self.assertEqual(
            record["release"]["factory_contract_version"], pin["schema_version"]
        )
        stamped = copy.deepcopy(record)
        stamped["release"]["factory_registry_sha256"] = pin["sha256"]
        self.assertEqual(
            _codes(vset.validate_record(stamped, require_registry_sha=True)), []
        )
        stamped["release"]["factory_registry_sha256"] = "sha256:" + ("ab" * 32)
        self.assertIn(
            "vset.release_contract_mismatch",
            _codes(vset.validate_record(stamped, require_registry_sha=True)),
        )

    def test_vset_payload_is_not_an_identity_kind(self):
        record = _load(ACCEPT / "issue-patch-validated.json")
        self.assertEqual(record_kind.classify_kind(record), "unknown")


class OracleExecutionTests(unittest.TestCase):
    def test_pack_snapshot_matches_accepted_fixtures(self):
        digest = vset.pack_snapshot_hash(PACK)
        for path in sorted(ACCEPT.glob("*.json")):
            record = _load(path)
            self.assertEqual(record["environment"]["repo_snapshot_hash"], digest, path.name)

    def test_validated_issue_patch_oracle_executes(self):
        record = _load(ACCEPT / "issue-patch-validated.json")
        errors, execution = vset.validate_record_with_oracle(record, PACK)
        self.assertEqual(_codes(errors), [])
        self.assertIsNotNone(execution)
        assert execution is not None
        self.assertTrue(execution["reference"]["ok"])
        self.assertTrue(execution["hidden"]["ok"])

    def test_validated_review_and_recovery_oracles_execute(self):
        for name in (
            "review-remediation-validated.json",
            "failure-recovery-validated.json",
        ):
            with self.subTest(name=name):
                errors, execution = vset.validate_record_with_oracle(
                    _load(ACCEPT / name), PACK
                )
                self.assertEqual(_codes(errors), [])
                self.assertTrue(execution["reference"]["ok"])
                self.assertTrue(execution["hidden"]["ok"])

    def test_provisional_runs_reference_without_claiming_validated(self):
        record = _load(ACCEPT / "provisional.json")
        errors, execution = vset.validate_record_with_oracle(record, PACK)
        self.assertEqual(_codes(errors), [])
        self.assertTrue(execution["reference"]["ok"])
        self.assertIsNone(execution["hidden"])
        self.assertEqual(record["oracle"]["status"], "provisional")

    def test_invalid_impossible_is_measured_without_self_certifying(self):
        record = _load(ACCEPT / "invalid-impossible.json")
        errors, execution = vset.validate_record_with_oracle(record, PACK)
        self.assertEqual(_codes(errors), [])
        self.assertIsNone(execution)
        self.assertEqual(record["curation"]["reason_codes"], ["vset.impossible_task"])

    def test_unpatched_hidden_tests_fail_and_cannot_validate(self):
        record = _load(ACCEPT / "issue-patch-validated.json")
        del record["payload"]["patch"]
        errors, execution = vset.validate_record_with_oracle(record, PACK)
        self.assertIn("vset.oracle_execution_mismatch", _codes(errors))
        self.assertFalse(execution["hidden"]["ok"])

    def test_hidden_pass_is_meaningless_when_oracle_is_self_certified(self):
        record = _load(REJECT / "self-certify-solver-pass.json")
        errors, execution = vset.validate_record_with_oracle(record, PACK)
        codes = _codes(errors)
        self.assertIn("vset.oracle_self_certified", codes)
        self.assertTrue(execution["hidden"]["ok"])

    def test_wrong_result_hash_fails_closed(self):
        record = _load(ACCEPT / "issue-patch-validated.json")
        record["oracle"]["result_hash"] = "sha256:" + ("cd" * 32)
        errors, _execution = vset.validate_record_with_oracle(record, PACK)
        self.assertIn("vset.oracle_execution_mismatch", _codes(errors))


class ValidateVsetCliTests(unittest.TestCase):
    def test_accept_directory_exits_zero(self):
        result = _cli(str(ACCEPT))
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ok"])

    def test_reject_directory_exits_nonzero(self):
        result = _cli(str(REJECT))
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("ERROR:", result.stderr)

    def test_oracle_cli_validates_the_accepted_issue_patch(self):
        result = _cli(
            "--oracle",
            "--pack",
            str(PACK),
            str(ACCEPT / "issue-patch-validated.json"),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["records"][0]["oracle_execution"]["hidden_ok"])


if __name__ == "__main__":
    unittest.main()
