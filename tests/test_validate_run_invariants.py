#!/usr/bin/env python3
"""Single-field record invariants the shape layer enforces on a thalamic
record: reward-total arithmetic, provenance vocabulary, and meta.round.
"""

import copy
import sys
import unittest
from pathlib import Path
from unittest import mock

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from validate_run_test_helpers import TINY_THALAMIC, _run_with_record  # noqa: E402
import validate_run  # noqa: E402


class ValidateRewardTotal(unittest.TestCase):
    def test_reward_total_reconciles(self):
        rec = copy.deepcopy(TINY_THALAMIC)
        rec["reward_components"] = {"task": 0.4, "safety": 0.3, "total": 0.7}
        result = _run_with_record(rec)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_reward_total_mismatch_fails(self):
        rec = copy.deepcopy(TINY_THALAMIC)
        rec["reward_components"] = {"task": 0.4, "safety": 0.3, "total": 0.9}
        result = _run_with_record(rec)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("reward_components.total", result.stderr)
        self.assertIn("sum of components", result.stderr)

    def test_reward_total_non_finite_fails(self):
        rec = copy.deepcopy(TINY_THALAMIC)
        rec["reward_components"] = {"task": 0.4, "total": float("inf")}
        result = _run_with_record(rec)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("non-standard JSON numeric constant Infinity", result.stderr)

    def test_reward_total_ignores_bookkeeping_keys(self):
        rec = copy.deepcopy(TINY_THALAMIC)
        rec["reward_components"] = {
            "task": 0.5,
            "weights_note": "not counted",
            "total": 0.5,
        }
        result = _run_with_record(rec)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_reward_total_zero_with_no_components(self):
        rec = copy.deepcopy(TINY_THALAMIC)
        rec["reward_components"] = {"total": 0.0}
        result = _run_with_record(rec)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_reward_total_boolean_fails(self):
        rec = copy.deepcopy(TINY_THALAMIC)
        rec["reward_components"] = {"task": 0.4, "total": True}
        result = _run_with_record(rec)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("reward_components.total", result.stderr)
        self.assertIn("finite", result.stderr)

    def test_reward_metadata_keys_are_not_components(self):
        # Same exclusion vocabulary as check_records: numeric bookkeeping keys
        # must not be summed as reward components.
        rec = copy.deepcopy(TINY_THALAMIC)
        rec["reward_components"] = {
            "task": 0.4,
            "safety": 0.6,
            "unit_usd": 10000,
            "rounding_decimals": 3,
            "total": 1.0,
        }
        result = _run_with_record(rec)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_unresolved_weighted_layout_is_not_rechecked_unweighted(self):
        # Declared weights whose components this layer cannot resolve must not
        # fall through to the sibling-sum check (that produced false errors).
        rec = copy.deepcopy(TINY_THALAMIC)
        rec["reward_components"] = {
            "task": 1.0,
            "weights": {"task": 0.5, "mystery": 0.5},
            "total": 0.5,
        }
        result = _run_with_record(rec)
        self.assertEqual(result.returncode, 0, result.stderr)


class ValidateProvenanceStrict(unittest.TestCase):
    def test_state_vocabulary_rebinding_changes_parent_provenance_gate(self):
        with mock.patch.object(
            validate_run,
            "ALLOWED_SIM_OR_REAL",
            frozenset({"declared"}),
        ):
            self.assertEqual(
                validate_run.check_provenance(
                    {"state": {"sim_or_real": "declared"}}, "record"
                ),
                [],
            )
            self.assertEqual(
                validate_run.check_provenance(
                    {"state": {"sim_or_real": "designed"}}, "record"
                ),
                [
                    "record: state.sim_or_real must be one of ['declared']",
                ],
            )

    def test_kind_vocabulary_rebinding_changes_parent_provenance_gate(self):
        with mock.patch.object(
            validate_run,
            "ALLOWED_PROVENANCE_KIND",
            frozenset({"declared"}),
        ):
            self.assertEqual(
                validate_run.check_provenance(
                    {"provenance": {"kind": "declared"}}, "record"
                ),
                [],
            )
            self.assertEqual(
                validate_run.check_provenance(
                    {"provenance": {"kind": "designed"}}, "record"
                ),
                [
                    "record: provenance.kind must be one of ['declared']",
                ],
            )

    def test_provenance_valid_kinds(self):
        for kind in ["designed", "simulated", "hil", "unknown"]:
            rec = copy.deepcopy(TINY_THALAMIC)
            rec["provenance"] = {"kind": kind}
            result = _run_with_record(rec)
            self.assertEqual(result.returncode, 0, f"kind={kind} {result.stderr}")

    def test_provenance_invalid_kind_fails(self):
        rec = copy.deepcopy(TINY_THALAMIC)
        rec["provenance"] = {"kind": "real"}
        result = _run_with_record(rec)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("provenance.kind", result.stderr)

    def test_state_sim_or_real_must_be_valid(self):
        rec = copy.deepcopy(TINY_THALAMIC)
        rec["state"]["sim_or_real"] = "real"
        result = _run_with_record(rec)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("sim_or_real", result.stderr)

    def test_state_sim_or_real_valid(self):
        for v in ["designed", "simulated", "hil"]:
            rec = copy.deepcopy(TINY_THALAMIC)
            rec["state"]["sim_or_real"] = v
            result = _run_with_record(rec)
            self.assertEqual(result.returncode, 0, f"sim_or_real={v} {result.stderr}")

    def test_provenance_claimed_wrong_type_fails(self):
        rec = copy.deepcopy(TINY_THALAMIC)
        rec["provenance"] = {"kind": "designed", "claimed": 123}
        result = _run_with_record(rec)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("provenance.claimed", result.stderr)


class ValidateMetaRound(unittest.TestCase):
    def test_meta_round_present(self):
        rec = copy.deepcopy(TINY_THALAMIC)
        rec["meta"] = {"round": 2}
        result = _run_with_record(rec)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_meta_missing_fails(self):
        rec = copy.deepcopy(TINY_THALAMIC)
        rec.pop("meta", None)
        result = _run_with_record(rec)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("meta", result.stderr)
        # One violation, one error: an absent meta is reported by the
        # required-key check only; check_meta_round no longer adds a second
        # error for the same missing field.
        self.assertEqual(result.stderr.strip().count("ERROR:"), 1, result.stderr)

    def test_one_violation_reports_exactly_one_error(self):
        cases = {
            "real provenance": lambda r: r.__setitem__("state", {"sim_or_real": "real"}),
            "invalid provenance": lambda r: r.__setitem__("state", {"sim_or_real": "bogus"}),
            "meta wrong type": lambda r: r.__setitem__("meta", "not-an-object"),
            "reward wrong type": lambda r: r.__setitem__("reward_components", "not-an-object"),
        }
        for label, mutate in cases.items():
            with self.subTest(case=label):
                rec = copy.deepcopy(TINY_THALAMIC)
                mutate(rec)
                result = _run_with_record(rec)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertEqual(
                    result.stderr.strip().count("ERROR:"), 1, f"{label}: {result.stderr}"
                )

    def test_meta_round_not_integer_fails(self):
        rec = copy.deepcopy(TINY_THALAMIC)
        rec["meta"] = {"round": "2"}
        result = _run_with_record(rec)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("meta.round", result.stderr)

    def test_meta_round_zero_fails(self):
        rec = copy.deepcopy(TINY_THALAMIC)
        rec["meta"] = {"round": 0}
        result = _run_with_record(rec)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("meta.round", result.stderr)

    def test_meta_round_bool_rejected(self):
        rec = copy.deepcopy(TINY_THALAMIC)
        rec["meta"] = {"round": True}
        result = _run_with_record(rec)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("meta.round", result.stderr)


class ValidationIsTotalOverDecodedJson(unittest.TestCase):
    """Codex #97 P2: unhashable JSON values must report invalid, never raise.

    ``x not in frozenset`` raises ``TypeError`` for a list or object value,
    which crashed the validator (and rolled back a whole compose destination)
    instead of reporting the field as invalid.
    """

    def test_unhashable_safety_decision_reports_invalid(self):
        rec = copy.deepcopy(TINY_THALAMIC)
        rec["safety_decision"] = {"decision": [], "rationale": "test fixture"}
        result = _run_with_record(rec)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn(
            "safety_decision.decision must be ACCEPT|MODIFY|REJECT",
            result.stdout + result.stderr,
        )
        self.assertNotIn("Traceback", result.stderr)

    def test_unhashable_provenance_kind_reports_invalid(self):
        rec = copy.deepcopy(TINY_THALAMIC)
        rec["provenance"] = {"kind": [], "claimed": "designed"}
        result = _run_with_record(rec)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("provenance.kind must be one of", result.stdout + result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_unhashable_state_provenance_reports_invalid(self):
        rec = copy.deepcopy(TINY_THALAMIC)
        rec["state"]["sim_or_real"] = {"designed": True}
        result = _run_with_record(rec)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("state.sim_or_real must be one of", result.stdout + result.stderr)
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
