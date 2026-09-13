#!/usr/bin/env python3
"""The reviewed observable vocabulary, and how the distance metric weighs it.

The gate blocks a pair whose arms are too close, so both directions are
defects: a real behavioral contrast that scores below the floor blocks work
that should publish, and a representational difference that scores above it
publishes a copy. These regressions pin one case of each.
"""

import unittest

from preference_arms_support import check  # noqa: E402
import preference_arms  # noqa: E402


FLOOR = preference_arms.DEFAULT_MIN_ARM_DISTANCE


def _spike_stream(count):
    return [{"unit": f"unit_{index}", "channel": f"ch_{index}"} for index in range(count)]


class EstablishedIdentifiersAreInTheVocabulary(unittest.TestCase):
    """``action_type`` is how this repository has always named an action."""

    def test_action_type_is_a_reviewed_identifier_path(self):
        self.assertIn(
            ("executed_action", "action_type"),
            preference_arms.MACHINE_IDENTIFIER_PATHS,
        )

    def test_hazard_avoided_is_a_reviewed_identifier_path(self):
        self.assertIn(
            ("future_outcome", "hazard_avoided"),
            preference_arms.MACHINE_IDENTIFIER_PATHS,
        )

    def test_action_type_contrast_is_observable(self):
        chosen = {
            "executed_action": {"action_type": "hold"},
            "future_outcome": {"hazard_avoided": "sensor_blind_advance"},
        }
        rejected = {
            "executed_action": {"action_type": "proceed"},
            "future_outcome": {"hazard_avoided": "none"},
        }
        self.assertEqual(
            preference_arms.machine_observable_deltas(chosen, rejected),
            ("executed_action.action_type", "future_outcome.hazard_avoided"),
        )
        self.assertGreater(preference_arms.arm_distance(chosen, rejected), FLOOR)


class SharedTelemetryDoesNotDiluteContrast(unittest.TestCase):
    """A long unchanged spike stream must not outvote a changed action."""

    def _pair(self, spikes):
        chosen = {
            "executed_action": {"action": "proceed"},
            "spike_events": _spike_stream(spikes),
        }
        rejected = {
            "executed_action": {"action": "hold"},
            "spike_events": _spike_stream(spikes),
        }
        return chosen, rejected

    def test_long_shared_stream_keeps_the_contrast_above_the_floor(self):
        for spikes in (0, 1, 8, 40, 120):
            with self.subTest(spikes=spikes):
                chosen, rejected = self._pair(spikes)
                self.assertEqual(
                    preference_arms.machine_observable_deltas(chosen, rejected),
                    ("executed_action.action",),
                )
                self.assertGreater(preference_arms.arm_distance(chosen, rejected), FLOOR)

    def test_distance_does_not_decay_as_shared_telemetry_grows(self):
        short = preference_arms.arm_distance(*self._pair(1))
        long = preference_arms.arm_distance(*self._pair(120))
        self.assertEqual(short, long)

    def test_the_gate_publishes_the_contrasting_pair(self):
        chosen, rejected = self._pair(40)
        decision = check(
            {
                "chosen": {
                    **chosen,
                    "state": {"site": "alpha"},
                    "proposed_action": {"action": "advance"},
                },
                "rejected": {
                    **rejected,
                    "state": {"site": "alpha"},
                    "proposed_action": {"action": "advance"},
                },
                "meta": {"isolation": preference_arms.TWO_SESSION},
            }
        )
        self.assertNotIn(preference_arms.REASON_NEAR_VERBATIM, decision.reason_codes)
        self.assertNotIn(preference_arms.REASON_OBSERVABLES_IDENTICAL, decision.reason_codes)

    def test_a_wholly_copied_pair_is_still_blocked(self):
        arm = {
            "executed_action": {"action": "hold"},
            "spike_events": _spike_stream(40),
        }
        self.assertEqual(preference_arms.arm_distance(arm, dict(arm)), 0.0)


class RepresentationalDifferencesAreNotDeltas(unittest.TestCase):
    """Float noise and script swaps are spellings, not behavior."""

    def test_machine_precision_noise_is_not_a_delta(self):
        noisy = (
            (1.8, 1.8000000000000003),
            (0.1 + 0.2, 0.3),
            (4200.0, 4200.000000000001),
        )
        for left_value, right_value in noisy:
            with self.subTest(left=left_value, right=right_value):
                left = {"executed_action": {"speed_mps": left_value}}
                right = {"executed_action": {"speed_mps": right_value}}
                self.assertEqual(preference_arms.machine_observable_deltas(left, right), ())
                self.assertEqual(preference_arms.arm_distance(left, right), 0.0)

    def test_a_real_numeric_change_is_still_a_delta(self):
        left = {"executed_action": {"speed_mps": 1.8}}
        right = {"executed_action": {"speed_mps": 1.81}}
        self.assertEqual(
            preference_arms.machine_observable_deltas(left, right),
            ("executed_action.speed_mps",),
        )

    def test_cross_script_identifier_swap_is_not_a_delta(self):
        # U+0501 CYRILLIC SMALL LETTER KOMI DE renders as a Latin ``d``.
        left = {"executed_action": {"action": "hold"}, "future_outcome": {"result": "d"}}
        right = {"executed_action": {"action": "hold"}, "future_outcome": {"result": "ԁ"}}
        self.assertEqual(preference_arms.machine_observable_deltas(left, right), ())
        self.assertEqual(preference_arms.arm_distance(left, right), 0.0)

    def test_same_script_identifiers_still_contrast(self):
        left = {"future_outcome": {"result": "clear"}}
        right = {"future_outcome": {"result": "blocked"}}
        self.assertEqual(
            preference_arms.machine_observable_deltas(left, right),
            ("future_outcome.result",),
        )


if __name__ == "__main__":
    unittest.main()
