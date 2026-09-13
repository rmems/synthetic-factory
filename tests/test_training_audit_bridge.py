#!/usr/bin/env python3
"""training_audit.py's bridge event-stream classification.

event_stream_status must delegate event-shape validity (required bridge
keys, field types, one finite/consistent timestamp) to the same
check_spike_order the strict publish gate uses, and must not miscount a
missing or malformed stream as merely 'unsorted'.
"""

import sys
import tempfile
import unittest
from pathlib import Path

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from training_audit_test_helpers import thalamic, write  # noqa: E402

import training_audit  # noqa: E402


class TrainingAuditBridgeEvents(unittest.TestCase):
    def test_mixed_bridge_timestamp_keys_are_invalid(self):
        events = [
            {"channel": "a", "t_rel_ms": 120.0, "amplitude": 0.5},
            {"channel": "b", "t_ms": 90.0, "amplitude": 0.4},
        ]
        self.assertEqual(training_audit.event_stream_status(events), "invalid")

    def test_malformed_event_fields_are_invalid_even_when_timestamps_sort(self):
        """A comparable timestamp alone must not read as 'sorted': the
        schema's channel/amplitude type contract still applies (Codex #87,
        discussion_r3885768188)."""
        events = [
            {"t_rel_ms": 1.0, "channel": False, "amplitude": "bad"},
            {"t_rel_ms": 2.0, "channel": False, "amplitude": "bad"},
        ]
        self.assertEqual(training_audit.event_stream_status(events), "invalid")

    def test_a_bridge_level_clock_conflicting_with_its_events_is_invalid(self):
        """The record validator reports such a pair as multi-clock. Passing
        only the event list made this count it as 'sorted', so the audit's
        bridge-fidelity metrics contradicted its own invariant findings
        (Codex #87)."""
        events = [
            {"channel": "a", "t_rel_ms": 1.0, "amplitude": 0.5, "source_clock": "event"},
            {"channel": "b", "t_rel_ms": 2.0, "amplitude": 0.4, "source_clock": "event"},
        ]
        bridge = {"clock_id": "record", "spike_events": events}
        self.assertEqual(training_audit.event_stream_status(events, bridge), "invalid")

    def test_a_bridge_meta_clock_conflicting_with_its_events_is_invalid(self):
        events = [
            {"channel": "a", "t_rel_ms": 1.0, "amplitude": 0.5, "source_clock": "event"},
            {"channel": "b", "t_rel_ms": 2.0, "amplitude": 0.4, "source_clock": "event"},
        ]
        bridge = {"meta": {"timebase": "meta-clock"}, "spike_events": events}
        self.assertEqual(training_audit.event_stream_status(events, bridge), "invalid")

    def test_clock_identifier_cannot_spoof_the_order_error_category(self):
        marker = "spike_events not globally non-decreasing"
        events = [
            {"channel": "a", "t_rel_ms": 1.0, "amplitude": 0.5, "source_clock": "a"},
            {"channel": "b", "t_rel_ms": 2.0, "amplitude": 0.4, "source_clock": marker},
        ]
        self.assertEqual(training_audit.event_stream_status(events), "invalid")

    def test_a_bridge_clock_agreeing_with_its_events_is_still_sorted(self):
        """The enclosing declaration must not reclassify a valid stream."""
        events = [
            {"channel": "a", "t_rel_ms": 1.0, "amplitude": 0.5, "source_clock": "one"},
            {"channel": "b", "t_rel_ms": 2.0, "amplitude": 0.4, "source_clock": "one"},
        ]
        bridge = {"clock_id": "one", "spike_events": events}
        self.assertEqual(training_audit.event_stream_status(events, bridge), "sorted")

    def test_valid_events_out_of_order_are_still_unsorted(self):
        events = [
            {"channel": "a", "t_rel_ms": 2.0, "amplitude": 0.5},
            {"channel": "b", "t_rel_ms": 1.0, "amplitude": 0.4},
        ]
        self.assertEqual(training_audit.event_stream_status(events), "unsorted")

    def test_missing_bridge_stream_is_not_mislabeled_unsorted(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bridge = {
                "id": "missing-stream",
                "spike_events": [],
                "language_view": {"trajectory": thalamic("inner")},
            }
            write(root / "bridge" / "batch.jsonl", [bridge])
            report = training_audit.audit_run(root)

        self.assertEqual(report["bridge"]["missing_pairs"], 1)
        self.assertEqual(report["bridge"].get("unsorted_pairs", 0), 0)
        self.assertTrue(any("lack event streams" in item for item in report["blockers"]))


if __name__ == "__main__":
    unittest.main()
