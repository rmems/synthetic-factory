"""Measured preferences bind their displayed task and physical instrument."""

import copy
import unittest

from test_energy_preferences import FakeMeter, ep, oc


class PreferenceProvenance(unittest.TestCase):
    def setUp(self):
        self.record = ep.build_records(7, 1, meter=FakeMeter(), repeats=2)[0]

    def test_rehashed_coherent_cost_meter_substitution_is_refused(self):
        changed = copy.deepcopy(self.record)
        for candidate in changed["result"]["candidates"]:
            candidate["cost_meter"] = "unrelated_instrument"
        for measurement in changed["result"]["measurements"]:
            if measurement["quantity"] == changed["result"]["cost_quantity"]:
                measurement["meter"] = "unrelated_instrument"
        changed["provenance"]["record_sha256"] = oc.record_digest(changed)
        errors = ep.check_family(changed, "test")
        self.assertTrue(any("fingerprint.meter" in error for error in errors), errors)

    def test_changed_or_missing_visible_objective_is_refused(self):
        for objective in ("maximise measured cost", None):
            changed = copy.deepcopy(self.record)
            changed["scenario"]["objective"] = objective
            changed["provenance"]["record_sha256"] = oc.record_digest(changed)
            with self.subTest(objective=objective):
                errors = ep.check_family(changed, "test")
                self.assertTrue(any("scenario.objective" in error for error in errors), errors)
