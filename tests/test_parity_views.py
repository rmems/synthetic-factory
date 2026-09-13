"""Tests for pipelines/oracle_grounded/parity_views.py -- the training-view gate."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from parity_contract_support import WHERE, contract, make_record, make_view  # noqa: E402


class TrainingViews(unittest.TestCase):
    def test_built_view_passes_its_own_check(self):
        record = make_record()
        self.assertEqual(
            contract.training_view_errors(record, make_view(record), WHERE), []
        )

    def test_mismatch_verdict_sets_parity_failed(self):
        record = make_record()
        record["result"]["verdict"] = contract.VERDICT_MISMATCH
        record["result"]["reason_codes"] = ["ACTION_DISAGREEMENT"]
        view = make_view(record)
        self.assertTrue(view["parity_failed"])
        self.assertEqual(contract.training_view_errors(record, view, WHERE), [])

    def test_inconclusive_is_not_a_pass(self):
        record = make_record()
        record["result"]["verdict"] = contract.VERDICT_INCONCLUSIVE
        self.assertTrue(make_view(record)["parity_failed"])

    def test_unsupported_is_not_a_pass(self):
        record = make_record()
        record["result"]["verdict"] = contract.VERDICT_UNSUPPORTED
        self.assertTrue(make_view(record)["parity_failed"])

    def test_relabelled_verdict_is_rejected(self):
        record = make_record()
        record["result"]["verdict"] = contract.VERDICT_MISMATCH
        view = make_view(record, verdict=contract.VERDICT_MATCH)
        errors = contract.training_view_errors(record, view, WHERE)
        self.assertTrue(any("TRAINING_VIEW_HIDES_FAILURE" in error for error in errors))

    def test_view_identity_must_match_its_paired_source_record(self):
        record = make_record()
        for key, value in (
            ("id", "another-record"),
            ("record_kind", contract.KIND_NIR_EQUIVALENCE),
            ("dataset", "another-dataset"),
        ):
            with self.subTest(key=key):
                view = make_view(record)
                view[key] = value
                errors = contract.training_view_errors(record, view, WHERE)
                self.assertTrue(
                    any(f"view {key} must exactly match" in error for error in errors),
                    errors,
                )

    def test_softened_failure_flag_is_rejected(self):
        record = make_record()
        record["result"]["verdict"] = contract.VERDICT_MISMATCH
        view = make_view(record, parity_failed=False)
        errors = contract.training_view_errors(record, view, WHERE)
        self.assertTrue(any("parity_failed must be True" in error for error in errors))

    def test_dropped_reason_codes_are_rejected(self):
        record = make_record()
        record["result"]["reason_codes"] = ["ACTION_DISAGREEMENT", "MEMBRANE_DIVERGENCE"]
        view = make_view(record, reason_codes=["ACTION_DISAGREEMENT"])
        errors = contract.training_view_errors(record, view, WHERE)
        self.assertTrue(any("exactly match" in error for error in errors))

    def test_added_reason_codes_are_rejected_even_when_known(self):
        record = make_record()
        view = make_view(record, reason_codes=["ACTION_DISAGREEMENT"])
        errors = contract.training_view_errors(record, view, WHERE)
        self.assertTrue(any("exactly match" in error for error in errors), errors)

    def test_fabricated_reason_code_is_rejected(self):
        record = make_record()
        view = make_view(record, reason_codes=["FABRICATED_VIEW_REASON"])
        errors = contract.training_view_errors(record, view, WHERE)
        self.assertTrue(any("unknown reason code" in error for error in errors), errors)

    def test_view_must_name_its_execution_targets(self):
        record = make_record()
        view = make_view(record, execution_targets=[])
        errors = contract.training_view_errors(record, view, WHERE)
        self.assertTrue(any("execution targets" in error for error in errors))

    def test_view_may_not_relabel_its_execution_target(self):
        record = make_record()
        view = make_view(record, execution_targets=["fpga_hardware"])
        errors = contract.training_view_errors(record, view, WHERE)
        self.assertTrue(any("exactly match" in error for error in errors), errors)

    def test_view_must_carry_evidence_digests(self):
        record = make_record()
        view = make_view(record, evidence_digests=[])
        errors = contract.training_view_errors(record, view, WHERE)
        self.assertTrue(any("RESULT_DIGEST_UNLINKED" in error for error in errors))

    def test_view_may_not_substitute_fabricated_evidence_digests(self):
        record = make_record()
        view = make_view(record, evidence_digests=["sha256:fabricated"])
        errors = contract.training_view_errors(record, view, WHERE)
        self.assertTrue(any("exactly match" in error for error in errors), errors)

    def test_malformed_reason_code_containers_report_instead_of_crashing(self):
        for value in (None, "ACTION_DISAGREEMENT", [None]):
            with self.subTest(value=value):
                record = make_record()
                record["result"]["reason_codes"] = value
                view = make_view(record)
                errors = contract.training_view_errors(record, view, WHERE)
                self.assertTrue(any("reason_codes" in error for error in errors), errors)

    def test_view_must_stay_oracle_backed(self):
        record = make_record()
        view = make_view(record, oracle_backed=False)
        errors = contract.training_view_errors(record, view, WHERE)
        self.assertTrue(any("RESULT_NOT_ORACLE_BACKED" in error for error in errors))

    def test_unavailable_oracle_makes_the_view_incomplete(self):
        # `parity_failed: false` means the oracles that ran agreed. It does not
        # mean the intended oracles ran, and a consumer must be able to tell.
        record = make_record()
        record["result"]["reason_codes"] = ["ORACLE_UNAVAILABLE"]
        view = make_view(record)
        self.assertFalse(view["parity_failed"])
        self.assertFalse(view["oracle_complete"])
        self.assertEqual(contract.training_view_errors(record, view, WHERE), [])

    def test_fully_executed_record_yields_a_complete_view(self):
        view = make_view(make_record())
        self.assertTrue(view["oracle_complete"])

    def test_unhashable_reason_codes_are_reported_not_raised(self):
        # A persisted `reason_codes: [[]]` (or [{}]) must surface as the
        # malformed-field findings, not abort view construction with a
        # TypeError from hashing an unhashable entry.
        for malformed in ([[]], [{}]):
            with self.subTest(malformed=malformed):
                self.assertTrue(contract.oracle_is_complete(malformed))
                record = make_record()
                record["result"]["reason_codes"] = malformed
                view = make_view(record)
                errors = contract.training_view_errors(record, view, WHERE)
                self.assertTrue(
                    any("reason_codes" in error for error in errors), errors
                )

    def test_overstating_oracle_completeness_is_rejected(self):
        record = make_record()
        record["result"]["reason_codes"] = ["ORACLE_UNAVAILABLE"]
        view = make_view(record, oracle_complete=True)
        errors = contract.training_view_errors(record, view, WHERE)
        self.assertTrue(any("oracle_complete" in error for error in errors))

    def test_unrederivable_deployment_makes_the_view_incomplete(self):
        record = make_record()
        record["result"]["reason_codes"] = ["DEPLOYMENT_TRACE_NOT_REDERIVABLE"]
        view = make_view(record)
        self.assertFalse(view["parity_failed"])
        self.assertFalse(view["oracle_complete"])
        self.assertEqual(contract.training_view_errors(record, view, WHERE), [])
        overstated = make_view(record, oracle_complete=True)
        errors = contract.training_view_errors(record, overstated, WHERE)
        self.assertTrue(any("oracle_complete" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
