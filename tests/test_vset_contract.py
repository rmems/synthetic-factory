#!/usr/bin/env python3
"""VSET actor-provenance contract tests (#154)."""

from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from vset_testutil import (  # noqa: E402
    ACCEPT,
    PIPELINES,
    REJECT,
    codes as _codes,
    load_record as _load,
    vset,
)

if str(PIPELINES) not in sys.path:
    sys.path.insert(0, str(PIPELINES))
import record_kind  # noqa: E402
from curate_coding import contains_hidden_reasoning_key  # noqa: E402


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

    def test_forged_oracle_certifier_identity_fields_fail_closed(self):
        fixture = _load(REJECT / "forged-oracle-certifier-version.json")
        self.assertEqual(fixture["oracle"]["kind"], "deterministic_fixture_reference")
        self.assertEqual(fixture["oracle"]["status"], "validated")
        self.assertEqual(fixture["oracle"]["certifier"], fixture["solver"]["version"])
        self.assertIn("vset.oracle_self_certified", _codes(vset.validate_record(fixture)))

        record = _load(ACCEPT / "issue-patch-validated.json")
        record["oracle"]["certifier"] = "Solver"
        self.assertIn("vset.oracle_self_certified", _codes(vset.validate_record(record)))

        record = _load(ACCEPT / "issue-patch-validated.json")
        record["oracle"]["certifier"] = record["solver"]["tool_policy"]
        self.assertIn("vset.oracle_self_certified", _codes(vset.validate_record(record)))

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

    def test_identity_unresolved_provenance_is_not_an_actor_gap(self):
        record = _load(ACCEPT / "provisional.json")
        record["curation"]["reason_codes"] = [vset.IDENTITY_UNRESOLVED_PROVENANCE]
        self.assertIn(
            "vset.identity_reason_collision", _codes(vset.validate_record(record))
        )
        self.assertIn("identity.unresolved_provenance", vset.__doc__)
        self.assertNotIn(
            vset.IDENTITY_UNRESOLVED_PROVENANCE,
            ("vset.missing_actor_role", "vset.reviewer_required"),
        )


if __name__ == "__main__":
    unittest.main()
