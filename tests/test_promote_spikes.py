#!/usr/bin/env python3
"""Focused tests for promotion-time spike-stream sorting."""

import json
import sys
import unittest
from pathlib import Path

PIPELINES = Path(__file__).resolve().parents[1] / "pipelines"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
sys.path.insert(0, str(PIPELINES))

import promote  # noqa: E402


def _record():
    return {
        "state": {
            "sim_or_real": "real (production … actions live)",
            "domain": "test",
        },
        "proposed_action": {"action_type": "noop"},
        "safety_decision": {"decision": "ACCEPT", "rationale": "ok"},
        "executed_action": {"action_type": "noop"},
        "future_outcome": {"success": "full"},
        "reward_components": {"task_progress": 0.4, "safety": 0.6, "total": 1.0},
        "meta": {"id": "t-001"},
    }


class TestPromoteSpikeSorting(unittest.TestCase):
    def _assert_ambiguous_stream_unchanged(self, events):
        rec = _record()
        rec["spike_events"] = events
        original = json.loads(json.dumps(events))
        out = promote.promote_record(rec)
        self.assertEqual(out["spike_events"], original)
        self.assertNotIn("spike_events_resorted", out.get("meta", {}))

    def test_unsorted_spikes_are_sorted_and_flagged(self):
        rec = json.loads((FIXTURES / "bad-spikes.jsonl").read_text().splitlines()[0])
        out = promote.promote_record(rec)
        times = [event["t_rel_ms"] for event in out["spike_events"]]
        self.assertEqual(times, sorted(times))
        self.assertTrue(out["meta"]["spike_events_resorted"])

    def test_already_sorted_spikes_not_flagged(self):
        rec = _record()
        rec["spike_events"] = [
            {"channel": "a", "t_ms": 1.0},
            {"channel": "b", "t_ms": 2.0},
        ]
        out = promote.promote_record(rec)
        self.assertNotIn("spike_events_resorted", out.get("meta", {}))
        self.assertEqual(
            [event.get("t_rel_ms") or event.get("t_ms") for event in out["spike_events"]],
            [1.0, 2.0],
        )

    def test_mixed_timestamp_keys_are_not_resorted_as_one_clock(self):
        rec = _record()
        rec["spike_events"] = [
            {"channel": "a", "t_rel_ms": 120.0},
            {"channel": "b", "t_ms": 90.0},
        ]
        out = promote.promote_record(rec)
        self.assertEqual(
            [event.get("t_rel_ms") or event.get("t_ms") for event in out["spike_events"]],
            [120.0, 90.0],
        )
        self.assertNotIn("spike_events_resorted", out.get("meta", {}))

    def test_events_declaring_two_clocks_are_not_resorted(self):
        """Separate declared clocks are not a sortable timeline."""
        rec = _record()
        rec["spike_events"] = [
            {"channel": "a", "t_rel_ms": 2, "clock_id": "a"},
            {"channel": "b", "t_rel_ms": 1, "clock_id": "b"},
        ]
        out = promote.promote_record(rec)
        self.assertEqual([event["t_rel_ms"] for event in out["spike_events"]], [2, 1])
        self.assertNotIn("spike_events_resorted", out.get("meta", {}))

    def test_a_clock_declared_on_the_record_blocks_an_event_clock_resort(self):
        rec = _record()
        rec["clock_id"] = "record-clock"
        rec["spike_events"] = [
            {"channel": "a", "t_rel_ms": 2, "source_clock": "event-clock"},
            {"channel": "b", "t_rel_ms": 1, "source_clock": "event-clock"},
        ]
        out = promote.promote_record(rec)
        self.assertEqual([event["t_rel_ms"] for event in out["spike_events"]], [2, 1])
        self.assertNotIn("spike_events_resorted", out.get("meta", {}))

    def test_one_declared_clock_domain_is_still_resorted(self):
        rec = _record()
        rec["spike_events"] = [
            {"channel": "a", "t_rel_ms": 2, "clock_id": "same"},
            {"channel": "b", "t_rel_ms": 1, "clock_id": "same"},
        ]
        out = promote.promote_record(rec)
        self.assertEqual([event["t_rel_ms"] for event in out["spike_events"]], [1, 2])
        self.assertTrue(out["meta"]["spike_events_resorted"])

    def test_aliased_clock_fields_naming_one_domain_are_still_resorted(self):
        rec = _record()
        rec["spike_events"] = [
            {"channel": "a", "t_rel_ms": 2, "clock_id": "same"},
            {"channel": "b", "t_rel_ms": 1, "timebase": "same"},
        ]
        out = promote.promote_record(rec)
        self.assertEqual([event["t_rel_ms"] for event in out["spike_events"]], [1, 2])
        self.assertTrue(out["meta"]["spike_events_resorted"])

    def test_large_integer_timestamp_order_is_resorted_without_precision_loss(self):
        rec = _record()
        rec["spike_events"] = [
            {"channel": "a", "t_rel_ms": 9007199254740993},
            {"channel": "b", "t_rel_ms": 9007199254740992},
        ]
        out = promote.promote_record(rec)
        self.assertEqual(
            [event["t_rel_ms"] for event in out["spike_events"]],
            [9007199254740992, 9007199254740993],
        )
        self.assertTrue(out["meta"]["spike_events_resorted"])

    def test_dual_key_event_is_not_moved_to_the_end_of_an_inverted_stream(self):
        self._assert_ambiguous_stream_unchanged(
            [
                {"channel": "a", "t_rel_ms": 10.0, "t_ms": 99.0},
                {"channel": "b", "t_rel_ms": 5.0},
                {"channel": "c", "t_rel_ms": 1.0},
            ]
        )

    def test_non_object_event_blocks_resort_of_an_inverted_stream(self):
        self._assert_ambiguous_stream_unchanged(
            [
                "not-an-event",
                {"channel": "b", "t_rel_ms": 5.0},
                {"channel": "c", "t_rel_ms": 1.0},
            ]
        )


if __name__ == "__main__":
    unittest.main()
