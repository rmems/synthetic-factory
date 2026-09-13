#!/usr/bin/env python3
"""The arm-distance metric and the two-session round that clears the gate."""

import copy
import tempfile
import unittest
from pathlib import Path

from preference_arms_support import (  # noqa: E402
    REPO,
    TWO_SESSION_ROUND,
    check,
    first,
    load,
    run_cli,
)
import preference_arms  # noqa: E402
import training_audit  # noqa: E402


class ArmDistanceMetric(unittest.TestCase):
    def test_default_floor_is_owned_by_the_lexical_gate(self):
        self.assertEqual(preference_arms.DEFAULT_MIN_ARM_DISTANCE, 0.03)
        self.assertNotIn(
            "DEFAULT_EMBEDDING_THRESHOLD",
            (REPO / "pipelines" / "preference_arms.py").read_text(),
        )

    def test_shared_context_and_bookkeeping_do_not_create_distance(self):
        arm = {
            "id": "pair-chosen",
            "state": {"sim_or_real": "designed", "site": "alpha"},
            "proposed_action": {"action": "hold"},
            "safety_decision": {"decision": "MODIFY", "rationale": "bounded window"},
            "meta": {"tags": ["chosen"]},
        }
        twin = copy.deepcopy(arm)
        twin["id"] = "pair-rejected"
        twin["state"] = {"sim_or_real": "designed", "site": "omega"}
        twin["proposed_action"] = {"action": "release"}
        twin["meta"] = {"tags": ["rejected", "extra"]}
        self.assertEqual(preference_arms.arm_distance(arm, twin), 0.0)

    def test_observable_numeric_leaves_stay_atomic(self):
        left = {"future_outcome": {"latency_ms": 20}}
        right = {"future_outcome": {"latency_ms": 200}}
        self.assertGreater(preference_arms.arm_distance(left, right), 0.0)

    def test_equal_numeric_spellings_do_not_manufacture_distance(self):
        for left_value, right_value in ((0, 0.0), (-0.0, 0.0), (20, 20.0)):
            with self.subTest(left=left_value, right=right_value):
                left = {"future_outcome": {"latency_ms": left_value}}
                right = {"future_outcome": {"latency_ms": right_value}}
                self.assertEqual(preference_arms.arm_distance(left, right), 0.0)
                self.assertEqual(preference_arms.machine_observable_deltas(left, right), ())

    def test_observable_paths_require_their_declared_scalar_type(self):
        invalid_pairs = (
            ("latency_ms", True, False),
            ("estop", 1, 0),
            ("near_miss", "yes", "no"),
        )
        for key, left_value, right_value in invalid_pairs:
            with self.subTest(key=key):
                left = {"future_outcome": {key: left_value}}
                right = {"future_outcome": {key: right_value}}
                self.assertEqual(preference_arms.arm_distance(left, right), 0.0)
                self.assertEqual(preference_arms.machine_observable_deltas(left, right), ())

    def test_per_arm_goal_is_known_bookkeeping_not_contrast(self):
        left = {"goal": "restore service", "future_outcome": {"status": "recovered"}}
        right = {"goal": "delete production", "future_outcome": {"status": "recovered"}}
        self.assertEqual(preference_arms.arm_distance(left, right), 0.0)

        record = copy.deepcopy(first(TWO_SESSION_ROUND))
        record["chosen"]["goal"] = "restore service"
        record["rejected"]["goal"] = "restore service"
        self.assertNotIn(preference_arms.REASON_EXTENSION_FIELDS, check(record).reason_codes)

    def test_one_sided_nested_values_do_not_contribute_distance(self):
        left = {"executed_action": {"action": "validate"}}
        right = copy.deepcopy(left)
        left["executed_action"]["padding"] = "alpha beta gamma delta epsilon"
        self.assertEqual(preference_arms.arm_distance(left, right), 0.0)

    def test_list_order_is_not_a_difference(self):
        left = {"spike_events": ["alpha", "omega"]}
        right = {"spike_events": ["omega", "alpha"]}
        self.assertEqual(preference_arms.arm_distance(left, right), 0.0)

    def test_unapproved_wordless_strings_do_not_create_distance(self):
        left = {"future_outcome": {"incident": "—"}}
        right = {"future_outcome": {"incident": "…"}}
        self.assertEqual(preference_arms.arm_distance(left, right), 0.0)
        self.assertEqual(preference_arms.arm_distance(left, copy.deepcopy(left)), 0.0)

    def test_empty_contrast_surfaces_are_degenerate_not_distant(self):
        bare = {"state": {"sim_or_real": "designed"}, "meta": {}}
        self.assertEqual(preference_arms.arm_distance(bare, copy.deepcopy(bare)), 0.0)

    def test_cosine_similarity_is_clamped_and_symmetric(self):
        record = first(TWO_SESSION_ROUND)
        left = preference_arms.arm_terms(record["chosen"])
        right = preference_arms.arm_terms(record["rejected"])
        forward = preference_arms.cosine_similarity(left, right)
        backward = preference_arms.cosine_similarity(right, left)
        self.assertAlmostEqual(forward, backward, places=12)
        self.assertGreaterEqual(forward, 0.0)
        self.assertLessEqual(forward, 1.0)

    def test_unapproved_unspaced_unicode_narrative_is_ignored(self):
        shared = "保持制动直到传感器确认安全并且现场操作员明确批准恢复运行" * 4
        changed = shared.replace("安全", "危险", 1)
        distance = preference_arms.arm_distance(
            {"future_outcome": {"summary": shared}},
            {"future_outcome": {"summary": changed}},
        )
        self.assertEqual(distance, 0.0)

    def test_accent_only_edits_do_not_manufacture_arm_independence(self):
        self.assertEqual(
            preference_arms.arm_distance(
                {"future_outcome": {"summary": "mantén la acción segura"}},
                {"future_outcome": {"summary": "manten la accion segura"}},
            ),
            0.0,
        )

    def test_programmatic_distance_floor_rejects_non_finite_or_out_of_range_values(self):
        record = first(TWO_SESSION_ROUND)
        for value in (float("nan"), float("inf"), -0.01, 1.0, True, "0.03"):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "arm-distance floor"):
                    check(record, min_distance=value)


class TwoSessionRoundClearsTheGate(unittest.TestCase):
    def test_scan_passes_with_independent_arms_and_attestation(self):
        scan = preference_arms.scan_source(TWO_SESSION_ROUND)
        self.assertFalse(scan.blocked)
        self.assertEqual(scan.summary["preference_pairs"], 3)
        self.assertEqual(scan.summary["blocked_pairs"], 0)
        self.assertEqual(scan.summary["independent_pairs"], 3)
        self.assertEqual(scan.summary["two_session_pairs"], 3)
        self.assertEqual(scan.summary["context_purity_pct"], 100.0)
        self.assertEqual(scan.summary["reason_codes"], {})
        self.assertGreater(
            scan.summary["observed_min_arm_distance"],
            preference_arms.DEFAULT_MIN_ARM_DISTANCE,
        )
        self.assertTrue(all(d.isolation == "two-session" for d in scan.decisions))

    def test_cli_exits_zero_and_reports_the_pass(self):
        code, out, err = run_cli(["scan", str(TWO_SESSION_ROUND)])
        self.assertEqual(code, 0)
        self.assertIn("arm gate: PASS", err)
        self.assertIn("Blocked: 0", out)

    def test_every_fixture_pair_has_a_shared_machine_observable_delta(self):
        for record in load(TWO_SESSION_ROUND):
            with self.subTest(record=record["id"]):
                self.assertTrue(
                    preference_arms.machine_observable_deltas(
                        record["chosen"],
                        record["rejected"],
                    )
                )

    def test_strict_audit_reports_full_preference_purity(self):
        with tempfile.TemporaryDirectory() as td:
            run_dir = Path(td) / "run"
            factory = run_dir / "failure-as-fuel-preference-cascade"
            factory.mkdir(parents=True)
            (factory / "batch-r11.jsonl").write_bytes(TWO_SESSION_ROUND.read_bytes())
            report = training_audit.audit_run(run_dir)
        self.assertEqual(report["preferences"]["pairs"], 3)
        self.assertEqual(report["preferences"]["same_context"], 3)
        self.assertEqual(report["preferences"]["context_purity_pct"], 100.0)
        self.assertEqual(report["blockers"], [])

    def test_tighter_floor_is_honored(self):
        # The committed round scores 0.93-0.95 now that each observable path
        # is weighted equally, so the floor that demonstrates the flag is
        # honored has to sit above that rather than at the 0.9 the pooled
        # term vector used to leave room under.
        scan = preference_arms.scan_source(
            TWO_SESSION_ROUND, preference_arms.GatePolicy(min_distance=0.99)
        )
        self.assertTrue(scan.blocked)
        self.assertEqual(scan.summary["blocked_pairs"], 3)
        self.assertEqual(
            scan.summary["reason_codes"],
            {preference_arms.REASON_NEAR_VERBATIM: 3},
        )
        code, _, _ = run_cli(["scan", str(TWO_SESSION_ROUND), "--min-distance", "0.99"])
        self.assertEqual(code, 1)

if __name__ == "__main__":
    unittest.main()
