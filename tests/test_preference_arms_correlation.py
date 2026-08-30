#!/usr/bin/env python3
"""Every way a copied or near-verbatim arm tries to fake independence."""

import copy
import unittest

from preference_arms_support import (  # noqa: E402
    assert_blocked_copy,
    GATE_LABEL_ONLY,
    NEAR_VERBATIM,
    TWO_SESSION_ROUND,
    check,
    first,
    run_cli,
)
import preference_arms  # noqa: E402


class CorrelatedArmsAreBlocked(unittest.TestCase):
    def test_verbatim_restatement_of_the_rejected_arm(self):
        scan = preference_arms.scan_source(NEAR_VERBATIM)
        self.assertTrue(scan.blocked)
        decision = scan.decisions[0]
        self.assertEqual(decision.arm_distance, 0.0)
        self.assertTrue(decision.same_context)
        self.assertEqual(decision.isolation, "two-session")
        self.assertEqual(
            decision.reason_codes,
            (
                preference_arms.REASON_OBSERVABLES_IDENTICAL,
                preference_arms.REASON_NEAR_VERBATIM,
            ),
        )

    def test_gate_label_only_repair(self):
        scan = preference_arms.scan_source(GATE_LABEL_ONLY)
        self.assertTrue(scan.blocked)
        decision = scan.decisions[0]
        self.assertEqual(decision.arm_distance, 0.0)
        self.assertLessEqual(decision.arm_distance, preference_arms.DEFAULT_MIN_ARM_DISTANCE)
        self.assertIn(preference_arms.REASON_NEAR_VERBATIM, decision.reason_codes)
        self.assertIn(preference_arms.REASON_LABEL_ONLY_COPY, decision.reason_codes)

    def test_short_label_only_copy_is_blocked_even_above_the_lexical_floor(self):
        record = copy.deepcopy(first(TWO_SESSION_ROUND))
        for name, decision_label in (("chosen", "REJECT"), ("rejected", "ACCEPT")):
            arm = record[name]
            record[name] = {
                "id": arm["id"],
                "state": arm["state"],
                "proposed_action": arm["proposed_action"],
                "safety_decision": {
                    "decision": decision_label,
                    "rationale": "same bounded rationale",
                },
                "meta": arm["meta"],
            }
        decision = check(record)
        self.assertEqual(decision.arm_distance, 0.0)
        self.assertIn(preference_arms.REASON_LABEL_ONLY_COPY, decision.reason_codes)

    def test_reward_relabeling_cannot_turn_a_label_copy_into_independence(self):
        record = copy.deepcopy(first(GATE_LABEL_ONLY))
        chosen_reward = record["chosen"]["reward_components"]
        chosen_reward["task_progress"] += 0.1
        chosen_reward["total"] += 0.1

        decision = check(record)

        self.assertEqual(decision.arm_distance, 0.0)
        self.assertIn(preference_arms.REASON_NEAR_VERBATIM, decision.reason_codes)

    def test_timestamp_only_spike_edit_cannot_establish_independence(self):
        record = copy.deepcopy(first(TWO_SESSION_ROUND))
        record["chosen"] = copy.deepcopy(record["rejected"])
        record["chosen"]["spike_events"][0]["t_rel_ms"] += 0.01

        decision = check(record)

        self.assertIn(
            preference_arms.REASON_OBSERVABLES_IDENTICAL,
            decision.reason_codes,
        )

    def test_spike_unit_change_remains_a_machine_observable_delta(self):
        record = copy.deepcopy(first(TWO_SESSION_ROUND))
        record["chosen"] = copy.deepcopy(record["rejected"])
        record["chosen"]["spike_events"][0]["unit"] = "clearance_confirmed"

        deltas = preference_arms.machine_observable_deltas(
            record["chosen"],
            record["rejected"],
        )

        self.assertIn("spike_events.[].unit", deltas)

    def test_event_kind_change_remains_a_machine_observable_delta(self):
        record = copy.deepcopy(first(TWO_SESSION_ROUND))
        record["chosen"] = copy.deepcopy(record["rejected"])
        record["chosen"]["spike_events"] = [
            {
                "channel": "wm_slot_0",
                "event_kind": "load",
                "t_rel_ms": 40.0,
                "amplitude": 0.6,
            }
        ]
        record["rejected"]["spike_events"] = [
            {
                "channel": "wm_slot_0",
                "event_kind": "unload",
                "t_rel_ms": 40.0,
                "amplitude": 0.6,
            }
        ]

        deltas = preference_arms.machine_observable_deltas(
            record["chosen"],
            record["rejected"],
        )

        self.assertIn("spike_events.[].event_kind", deltas)
        decision = check(record)
        self.assertNotIn(
            preference_arms.REASON_OBSERVABLES_IDENTICAL,
            decision.reason_codes,
        )

    def test_arbitrary_nested_scalar_is_not_observable(self):
        record = copy.deepcopy(first(NEAR_VERBATIM))
        record["chosen"] = copy.deepcopy(record["rejected"])
        record["chosen"]["executed_action"]["nonce"] = 1
        record["rejected"]["executed_action"]["nonce"] = 0

        decision = check(record)

        self.assertEqual(decision.arm_distance, 0.0)
        self.assertIn(preference_arms.REASON_OBSERVABLES_IDENTICAL, decision.reason_codes)

    def test_one_sided_spike_insertion_cannot_shift_aligned_evidence(self):
        for insertion in (0, 1, 3):
            with self.subTest(insertion=insertion):
                record = copy.deepcopy(first(TWO_SESSION_ROUND))
                record["chosen"] = copy.deepcopy(record["rejected"])
                record["chosen"]["spike_events"].insert(
                    insertion,
                    {"t": 0.25, "unit": "inserted_only", "amplitude": 0.5},
                )

                decision = check(record)

                self.assertEqual(decision.arm_distance, 0.0)
                self.assertIn(
                    preference_arms.REASON_OBSERVABLES_IDENTICAL,
                    decision.reason_codes,
                )

    def test_duplicate_spike_insertion_cancels_as_an_unordered_multiset(self):
        record = copy.deepcopy(first(TWO_SESSION_ROUND))
        record["chosen"] = copy.deepcopy(record["rejected"])
        record["chosen"]["spike_events"].insert(
            1,
            copy.deepcopy(record["chosen"]["spike_events"][0]),
        )

        decision = check(record)

        self.assertEqual(decision.arm_distance, 0.0)
        self.assertIn(preference_arms.REASON_OBSERVABLES_IDENTICAL, decision.reason_codes)

    def test_approved_numeric_metric_remains_observable(self):
        record = copy.deepcopy(first(TWO_SESSION_ROUND))
        record["chosen"] = copy.deepcopy(record["rejected"])
        record["chosen"]["future_outcome"]["latency_ms"] = 20
        record["rejected"]["future_outcome"]["latency_ms"] = 200

        decision = check(record)

        self.assertGreater(decision.arm_distance, preference_arms.DEFAULT_MIN_ARM_DISTANCE)
        self.assertNotIn(
            preference_arms.REASON_OBSERVABLES_IDENTICAL,
            decision.reason_codes,
        )

    def test_boolean_values_cannot_impersonate_a_numeric_metric(self):
        record = copy.deepcopy(first(NEAR_VERBATIM))
        record["chosen"]["future_outcome"]["latency_ms"] = True
        record["rejected"]["future_outcome"]["latency_ms"] = False

        decision = check(record)

        self.assertTrue(decision.blocked)
        self.assertEqual(decision.arm_distance, 0.0)
        self.assertIn(preference_arms.REASON_OBSERVABLES_IDENTICAL, decision.reason_codes)

    def test_oversized_unordered_evidence_fails_closed(self):
        record = copy.deepcopy(first(TWO_SESSION_ROUND))
        record["chosen"] = copy.deepcopy(record["rejected"])
        events = [
            {"t": index / 1000, "unit": f"event_{index}", "amplitude": 0.5}
            for index in range(preference_arms.MAX_ALIGNMENT_LIST_ITEMS + 1)
        ]
        record["chosen"]["spike_events"] = copy.deepcopy(events)
        record["rejected"]["spike_events"] = copy.deepcopy(events)

        decision = check(record)

        self.assertIn(preference_arms.REASON_LIST_ALIGNMENT, decision.reason_codes)

    def test_unicode_machine_identifiers_are_observable(self):
        record = copy.deepcopy(first(TWO_SESSION_ROUND))
        record["chosen"] = copy.deepcopy(record["rejected"])
        record["chosen"]["executed_action"]["action"] = "停止"
        record["rejected"]["executed_action"]["action"] = "继续"
        record["chosen"]["future_outcome"]["outcome"] = "安全完成"
        record["rejected"]["future_outcome"]["outcome"] = "发生事故"

        decision = check(record)

        self.assertNotIn(
            preference_arms.REASON_OBSERVABLES_IDENTICAL,
            decision.reason_codes,
        )
        self.assertEqual(decision.reason_codes, ())

    def test_mixed_script_identifier_cannot_unlock_narrative_padding(self):
        record = copy.deepcopy(first(GATE_LABEL_ONLY))
        record["chosen"]["executed_action"]["action"] = "pᎪss"
        record["rejected"]["executed_action"]["action"] = "pass"
        record["chosen"]["executed_action"]["padding"] = (
            "alpha beta gamma delta epsilon zeta eta theta iota kappa"
        )

        decision = check(record)

        self.assertIn(
            preference_arms.REASON_OBSERVABLES_IDENTICAL,
            decision.reason_codes,
        )

    def test_unknown_extension_padding_is_blocked_and_cannot_add_distance(self):
        record = copy.deepcopy(first(GATE_LABEL_ONLY))
        record["chosen"]["padding"] = (
            "unrelated filler alpha beta gamma delta epsilon zeta eta theta"
        )

        assert_blocked_copy(self, record, preference_arms.REASON_EXTENSION_FIELDS)

    def test_nested_behavior_padding_cannot_establish_independence(self):
        record = copy.deepcopy(first(GATE_LABEL_ONLY))
        record["chosen"]["executed_action"]["padding"] = (
            "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda"
        )

        assert_blocked_copy(self, record, preference_arms.REASON_OBSERVABLES_IDENTICAL)

    def test_case_only_identifier_edit_cannot_unlock_nested_padding(self):
        record = copy.deepcopy(first(GATE_LABEL_ONLY))
        record["chosen"]["executed_action"]["padding"] = (
            "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda"
        )
        action = record["chosen"]["executed_action"]["action"]
        record["chosen"]["executed_action"]["action"] = action.upper()

        assert_blocked_copy(
            self,
            record,
            preference_arms.REASON_OBSERVABLES_IDENTICAL,
            preference_arms.REASON_NEAR_VERBATIM,
        )

    def test_punctuation_only_identifier_edit_cannot_unlock_nested_padding(self):
        record = copy.deepcopy(first(GATE_LABEL_ONLY))
        record["chosen"]["executed_action"]["padding"] = (
            "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda"
        )
        record["chosen"]["executed_action"]["action"] += "/"

        assert_blocked_copy(
            self,
            record,
            preference_arms.REASON_OBSERVABLES_IDENTICAL,
            preference_arms.REASON_NEAR_VERBATIM,
        )

    def test_safety_rationale_padding_cannot_establish_independence(self):
        record = copy.deepcopy(first(GATE_LABEL_ONLY))
        record["chosen"]["safety_decision"]["rationale"] += (
            " alpha beta gamma delta epsilon zeta eta theta iota kappa"
        )

        assert_blocked_copy(self, record, preference_arms.REASON_OBSERVABLES_IDENTICAL)

    def test_cross_script_homoglyph_does_not_inflate_copy_distance(self):
        record = copy.deepcopy(first(GATE_LABEL_ONLY))
        action = record["chosen"]["executed_action"]["action"]
        record["chosen"]["executed_action"]["action"] = action.replace("v", "ν", 1)

        assert_blocked_copy(
            self,
            record,
            preference_arms.REASON_NEAR_VERBATIM,
            preference_arms.REASON_OBSERVABLES_IDENTICAL,
        )

    def test_cyrillic_palochka_does_not_inflate_copy_distance(self):
        record = copy.deepcopy(first(GATE_LABEL_ONLY))
        action = record["chosen"]["executed_action"]["action"]
        record["chosen"]["executed_action"]["action"] = action.replace("l", "ӏ", 1)

        assert_blocked_copy(self, record, preference_arms.REASON_OBSERVABLES_IDENTICAL)

    def test_invisible_format_marks_do_not_inflate_copy_distance(self):
        record = copy.deepcopy(first(NEAR_VERBATIM))
        chosen = copy.deepcopy(record["rejected"])
        action = chosen["executed_action"]["action"]
        chosen["executed_action"]["action"] = "\u200d".join(action)
        record["chosen"] = chosen

        assert_blocked_copy(
            self,
            record,
            preference_arms.REASON_NEAR_VERBATIM,
            preference_arms.REASON_OBSERVABLES_IDENTICAL,
        )

    def test_cli_exits_nonzero_on_a_blocked_pair(self):
        code, _, err = run_cli(["scan", str(NEAR_VERBATIM)])
        self.assertEqual(code, 1)
        self.assertIn("arm gate: FAIL", err)

    def test_empty_arm_contrast_is_blocked(self):
        record = copy.deepcopy(first(TWO_SESSION_ROUND))
        record["chosen"] = {
            "id": record["chosen"]["id"],
            "state": record["chosen"]["state"],
            "proposed_action": record["chosen"]["proposed_action"],
            "meta": record["chosen"]["meta"],
        }
        decision = check(record)
        self.assertIn(preference_arms.REASON_CONTRAST_EMPTY, decision.reason_codes)

if __name__ == "__main__":
    unittest.main()
