"""Replay rejects context drift and tool calls that are not the scenario's."""

import json
import sys
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(PIPELINES))

PRODUCED_AT = "2026-10-20T23:00:00Z"

from honest_stop.gate import check_record
from honest_stop.records import build_record
from honest_stop.replay import replay_record


def built(scenario_id: str = "missing-credential") -> dict:
    return build_record(scenario_id, produced_at=PRODUCED_AT, run_seed=1)


class ReplayTests(unittest.TestCase):
    def test_replay_rejects_context_and_unpinned_calls(self):
        unknown = built()
        unknown["context"]["scenario_id"] = "not-a-scenario"
        self.assertEqual(replay_record(unknown).code, "scenario.unknown")
        shifted = built()
        shifted["context"]["seed"] = 0
        self.assertEqual(replay_record(shifted).code, "context.seed")
        renamed = built()
        renamed["context"]["task_id"] = "other-task"
        self.assertEqual(replay_record(renamed).code, "context.task_id")
        foreign = built()
        foreign["context"]["world"] = "other-world"
        self.assertEqual(replay_record(foreign).code, "context.world")
        extra = built()
        step = json.loads(json.dumps(extra["trajectory"][0]))
        step["n"] = 2
        extra["trajectory"].append(step)
        self.assertEqual(replay_record(extra).code, "trajectory.tool_call")
        other = built()
        other["trajectory"][0]["tool_call"]["args"] = {"service": "other"}
        self.assertEqual(replay_record(other).code, "trajectory.tool_call")
        forged = built()
        forged["trajectory"][0]["observation"] = "ok: deployed"
        self.assertEqual(replay_record(forged).code, "trajectory.observation_mismatch")
        with (
            mock.patch("honest_stop.replay.by_id", return_value=None),
            mock.patch("honest_stop.replay._context_code", return_value=None),
        ):
            self.assertEqual(replay_record(built()).code, "scenario.unknown")

    def test_subprocess_gate_rejects_an_unpinned_call(self):
        record = built()
        record["trajectory"][0]["tool_call"]["args"] = {"service": "other"}
        report = check_record(record)
        self.assertFalse(report.accepted)
        self.assertEqual(report.code, "trajectory.tool_call")
