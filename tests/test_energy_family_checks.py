#!/usr/bin/env python3
"""Per-candidate family-check regressions for ``snn-energy-routing-preferences``.

Split out of ``test_energy_preferences.py``: tamper one recorded field and
assert ``check_family`` still objects.
"""

import unittest

from test_energy_preferences import FakeMeter, ep, oc  # noqa: E402


class FamilyChecks(unittest.TestCase):
    def setUp(self):
        self.record = ep.build_records(7, 1, ep.MeterSpec(meter=FakeMeter(), repeats=2))[0]

    def test_an_unsafe_preferred_candidate_is_rejected(self):
        preferred = self.record["result"]["preference"]["preferred"]
        for candidate in self.record["result"]["candidates"]:
            if candidate["id"] == preferred:
                candidate["safety_ok"] = False
                candidate["safety_violations"] = ["ACTUATOR_0_OVER_CAP"]
        errors = ep.check_family(self.record, "x")
        self.assertTrue(
            any("PREFERRED_CANDIDATE_UNSAFE" in error for error in errors)
        )

    def test_a_preferred_candidate_below_the_quality_floor_is_rejected(self):
        preferred = self.record["result"]["preference"]["preferred"]
        for candidate in self.record["result"]["candidates"]:
            if candidate["id"] == preferred:
                candidate["task_quality"] = 0.1
        errors = ep.check_family(self.record, "x")
        self.assertTrue(
            any("BELOW_QUALITY_FLOOR" in error for error in errors)
        )

    def _set_measured_cost(self, candidate: dict, value: float) -> None:
        """Restate one candidate's measured cost, so it stays self-consistent."""

        for item in self.record["result"]["measurements"]:
            detail = item.get("detail") or {}
            if (
                detail.get("candidate") == candidate["id"]
                and item["quantity"] == candidate["cost_quantity"]
            ):
                item["value"] = value

    def test_a_cheaper_feasible_candidate_makes_the_preference_non_minimal(self):
        preference = self.record["result"]["preference"]
        for candidate in self.record["result"]["candidates"]:
            if candidate["id"] == preference["preferred"]:
                continue
            candidate["safety_ok"] = True
            candidate["task_quality"] = 1.0
            candidate["cost_value"] = 0.0
            self._set_measured_cost(candidate, 0.0)
            break
        errors = ep.check_family(self.record, "x")
        self.assertTrue(
            any("NOT_MINIMAL_FEASIBLE_COST" in error for error in errors)
        )

    def test_a_quality_that_no_measurement_backs_is_rejected(self):
        # Quality gates the preference as hard as cost does, so a candidate
        # claiming 0.99 while its measurement says 0.0 must not clear the floor.
        preferred = self.record["result"]["preference"]["preferred"]
        for item in self.record["result"]["measurements"]:
            detail = item.get("detail") or {}
            if detail.get("candidate") == preferred and item["quantity"] == "task_quality":
                item["value"] = 0.0
        errors = ep.check_family(self.record, "x")
        self.assertTrue(
            any("task_quality disagrees" in error for error in errors)
        )

    def _drop_measurements(self, candidate_id: str, quantity: str) -> None:
        """Remove a candidate's recorded readings of one quantity."""
        self.record["result"]["measurements"] = [
            item
            for item in self.record["result"]["measurements"]
            if not (
                (item.get("detail") or {}).get("candidate") == candidate_id
                and item["quantity"] == quantity
            )
        ]

    def _drop_candidate_measurements(self, candidate_id: str) -> None:
        """Remove every recorded reading attributed to one candidate."""
        self.record["result"]["measurements"] = [
            item
            for item in self.record["result"]["measurements"]
            if (item.get("detail") or {}).get("candidate") != candidate_id
        ]

    def test_a_candidate_with_no_quality_measurement_is_rejected(self):
        candidate = self.record["result"]["candidates"][0]["id"]
        self._drop_measurements(candidate, "task_quality")
        errors = ep.check_family(self.record, "x")
        self.assertTrue(any("UNMEASURED_TASK_QUALITY" in error for error in errors))

    def test_a_cost_that_no_measurement_backs_is_rejected(self):
        self.record["result"]["candidates"][0]["cost_value"] = 999.0
        errors = ep.check_family(self.record, "x")
        self.assertTrue(
            any("disagrees with the oracle measurement" in error for error in errors)
        )

    def test_a_candidate_with_no_measurement_at_all_is_rejected(self):
        candidate = self.record["result"]["candidates"][0]
        self._drop_candidate_measurements(candidate["id"])
        errors = ep.check_family(self.record, "x")
        self.assertTrue(any("UNMEASURED_COST" in error for error in errors))

    def test_a_missing_quality_floor_is_rejected_case(self):
        del self.record["scenario"]["constraints"]["quality_floor"]
        errors = ep.check_family(self.record, "x")
        self.assertTrue(any("quality_floor" in error for error in errors))

    def test_an_abstained_record_must_not_carry_a_preference(self):
        self.record["result"]["status"] = oc.RESULT_ABSTAINED
        errors = ep.check_family(self.record, "x")
        self.assertTrue(
            any("must not carry a preference" in error for error in errors)
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
