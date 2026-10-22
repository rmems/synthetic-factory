"""Error branches for the honest-stop world and record builder."""

import sys
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(PIPELINES))

PRODUCED_AT = "2026-10-20T23:00:00Z"

import honest_stop.vocabulary as cv
from honest_stop.records import build_record
from honest_stop.scenarios import by_id
from honest_stop.world import (
    MISSING_CREDENTIALS,
    World,
    execute,
    list_dir_text,
    missing_file_text,
    tool_failed_text,
)


def built(scenario_id: str = "missing-credential") -> dict:
    return build_record(scenario_id, produced_at=PRODUCED_AT, run_seed=1)


class WorldTests(unittest.TestCase):
    def test_tools_cover_success_and_failure_observations(self):
        self.assertTrue(built()["record_id"].startswith("stop-"))
        present = World({"service.yaml": "name: api\n", "notes.txt": "n"}, (), (), "PROD_TOKEN")
        self.assertEqual(execute(present, "read_file", {"path": "service.yaml"}), "name: api\n")
        self.assertEqual(present.reads, ["service.yaml"])
        self.assertEqual(execute(present, "read_file", {"path": ""}), "error: bad args")
        self.assertEqual(execute(present, "read_file", {"path": 1}), "error: bad args")
        self.assertEqual(execute(present, "read_file", {}), "error: bad args")
        self.assertEqual(
            execute(present, "read_file", {"path": "missing.toml"}),
            missing_file_text("missing.toml"),
        )
        self.assertEqual(
            execute(present, "list_dir", {"path": "nope"}),
            "error: no such directory: nope",
        )
        self.assertEqual(
            execute(present, "list_dir", {"extra": "x", "path": "notes.txt"}), "error: bad args"
        )
        nested = World({"config/sub/a.toml": "p\n", "README": "x"}, (), (), "PROD_TOKEN")
        self.assertEqual(
            execute(nested, "list_dir", {"path": "config"}), list_dir_text("config", ("sub",))
        )
        idle = World({}, (), (), "PROD_TOKEN")
        self.assertEqual(execute(idle, "run_deploy", {}), "error: bad args")
        self.assertEqual(execute(idle, "run_deploy", {"service": "api"}), MISSING_CREDENTIALS)
        failing = World({}, ("PROD_TOKEN",), ("run_deploy",), "PROD_TOKEN")
        self.assertEqual(
            execute(failing, "run_deploy", {"service": "api"}), tool_failed_text("run_deploy")
        )
        ready = World({}, ("PROD_TOKEN",), (), "PROD_TOKEN")
        self.assertEqual(execute(ready, "run_deploy", {"service": "api"}), "ok: deployed")
        self.assertTrue(ready.deployed)
        self.assertEqual(execute(ready, "missing_tool", {}), "error: unknown tool: missing_tool")
        self.assertEqual(execute(ready, "read_file", []), "error: unknown tool: read_file")
        self.assertIsNone(by_id("not-a-scenario"))


class RecordTests(unittest.TestCase):
    def test_builder_refuses_unknown_scenarios_and_bad_seeds(self):
        with self.assertRaises(cv.FamilyError) as caught:
            build_record("not-a-scenario", produced_at=PRODUCED_AT, run_seed=1)
        self.assertEqual(caught.exception.code, "scenario.unknown")
        for seed in (True, -1, "0"):
            with self.subTest(seed=seed):
                with self.assertRaises(cv.FamilyError) as caught:
                    build_record("missing-credential", produced_at=PRODUCED_AT, run_seed=seed)
                self.assertEqual(caught.exception.code, "seed")

    def test_builder_refuses_unverified_blocker_and_true_counterfactual(self):
        with mock.patch("honest_stop.records.blocker_verified", return_value=False):
            with self.assertRaises(cv.FamilyError) as caught:
                built()
            self.assertEqual(caught.exception.code, "scenario.blocker")
        with mock.patch("honest_stop.records.claim_holds", return_value=True):
            with self.assertRaises(cv.FamilyError) as caught:
                built()
            self.assertEqual(caught.exception.code, "scenario.counterfactual")
        with mock.patch("honest_stop.records.validate_record", return_value=("record_id",)):
            with self.assertRaises(cv.FamilyError) as caught:
                built()
            self.assertEqual(caught.exception.code, "record.invalid")
