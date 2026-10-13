"""Fail-closed branches of the facade identity and bridge lane adapters.

``compose_curated`` re-exports these adapters under the historically pinned
private names, so the tests drive them through that facade surface.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
for _path in (TESTS, TESTS.parent / "pipelines"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import compose_curated
from compose_contract import ComposeDecision
from compose_curated_context import SourceCoordinates
from compose_curated_test_support import bridge_pair

SOURCE = SourceCoordinates("neuromorphic-event-language-bridge/batch-r01.jsonl", 1, "0" * 64)


def _repaired_copy(record, line=SOURCE.line):
    return compose_curated._bridge_order_repaired_copy(
        record, source_path=SOURCE.path, source_line=line, source_sha256=SOURCE.sha256
    )


class BridgeOrderRepairTests(unittest.TestCase):
    def test_already_ordered_bridge_offers_no_repair(self):
        self.assertIsNone(_repaired_copy(bridge_pair()))

    def test_failed_bridge_probe_offers_no_repair(self):
        self.assertIsNone(_repaired_copy(bridge_pair(unsorted=True), line=0))

    def test_unordered_bridge_offers_a_globally_ordered_copy(self):
        repaired = _repaired_copy(bridge_pair(unsorted=True))

        self.assertEqual([event["t_rel_ms"] for event in repaired["spike_events"]], [1.0, 2.0, 3.0])


class BridgeStageTests(unittest.TestCase):
    def test_bridge_without_events_is_excluded(self):
        record = bridge_pair()
        record["spike_events"] = []
        stages: list = []

        decision = compose_curated._compose_bridge_stage(record, stages, SOURCE)

        self.assertIsInstance(decision, ComposeDecision)
        self.assertEqual(decision.reason_codes, ("BRIDGE_EVENT_STREAM_MISSING_OR_EMPTY",))
        self.assertEqual((stages[-1]["lane"], stages[-1]["action"]), ("bridge", "excluded"))


if __name__ == "__main__":
    unittest.main()
