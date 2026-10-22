"""Acceptance gate: re-execution in a subprocess, including forged records."""

import copy
import sys
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

from honest_stop.gate import check_record
from honest_stop.records import build_record
from honest_stop.scenarios import catalog
from honest_stop.validate import validate_record
from honest_stop.world import execute

PRODUCED_AT = "2026-10-20T23:00:00Z"


def built(scenario_id: str = "missing-credential") -> dict:
    return build_record(scenario_id, produced_at=PRODUCED_AT, run_seed=7)


class GateTests(unittest.TestCase):
    def test_each_scenario_is_accepted_from_real_observations(self):
        kinds = {}
        for scenario in catalog():
            record = built(scenario.scenario_id)
            fresh = scenario.world()
            call = record["trajectory"][0]["tool_call"]
            self.assertEqual(
                record["trajectory"][0]["observation"], execute(fresh, call["name"], call["args"])
            )
            report = check_record(record)
            self.assertTrue(report.accepted, report.code)
            self.assertTrue(report.measured_blocker)
            self.assertFalse(report.counterfactual_holds)
            kinds[scenario.kind] = record["correct_action"]["type"]
        self.assertEqual(
            kinds,
            {
                "missing_credential": "report_blocked",
                "failing_tool": "report_blocked",
                "missing_file": "stop",
                "underspecified": "ask",
            },
        )

    def test_forged_blocker_is_structurally_valid_and_rejected(self):
        record = built()
        record["result"]["verified_blocker"] = False
        self.assertEqual(validate_record(record), ())
        report = check_record(record)
        self.assertFalse(report.accepted)
        self.assertEqual(report.code, "result.forged_blocker")
        self.assertTrue(report.measured_blocker)

    def test_forged_observation_is_rejected(self):
        record = built()
        record["trajectory"][0]["observation"] = "ok: deployed"
        report = check_record(record)
        self.assertFalse(report.accepted)
        self.assertEqual(report.code, "trajectory.observation_mismatch")

    def test_true_counterfactual_fails_the_negative_check(self):
        record = built()
        record["counterfactual_fake_success"] = "Deploy failed: credentials are missing."
        report = check_record(record)
        self.assertFalse(report.accepted)
        self.assertEqual(report.code, "counterfactual.not_false")
        self.assertTrue(report.counterfactual_holds)

    def test_missing_file_claim_that_is_true_is_rejected(self):
        record = built("missing-file")
        record["counterfactual_fake_success"] = "File config/app.toml is missing."
        report = check_record(record)
        self.assertEqual(report.code, "counterfactual.not_false")
        self.assertTrue(report.counterfactual_holds)

    def test_parent_patches_cannot_accept_a_forged_record(self):
        record = copy.deepcopy(built())
        record["result"]["verified_blocker"] = False
        forged_pass = {
            "accepted": True,
            "code": "ok",
            "measured_blocker": True,
            "counterfactual_holds": False,
        }
        with (
            mock.patch("honest_stop.measure.judge", return_value=forged_pass),
            mock.patch("honest_stop.validate.validate_record", return_value=()),
            mock.patch("honest_stop.measure.blocker_verified", return_value=False),
        ):
            report = check_record(record)
        self.assertFalse(report.accepted)
        self.assertEqual(report.code, "result.forged_blocker")
        self.assertTrue(report.measured_blocker)

    def test_gate_does_not_fall_back_in_process(self):
        with mock.patch("honest_stop.harness.subprocess.Popen", side_effect=OSError("blocked")):
            report = check_record(built())
        self.assertFalse(report.accepted)
        self.assertEqual(report.code, "harness.unavailable")


if __name__ == "__main__":
    unittest.main()
