#!/usr/bin/env python3
"""Focused tests for deterministic Bridge timing curation."""

from __future__ import annotations

import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

import curate_bridge  # noqa: E402


def event(time, channel, **extra):
    value = {"channel": channel, "t_rel_ms": time, "amplitude": 0.5}
    value.update(extra)
    return value


def bridge(events, record_id="bridge-fixture"):
    return {
        "id": record_id,
        "spike_events": events,
        "language_view": {"trajectory": {"state": {"episode_id": record_id}}},
    }


def decide(record):
    raw = json.dumps(record, ensure_ascii=False).encode("utf-8")
    return curate_bridge.curate_record(
        record,
        source_path="bridge/batch-r02.jsonl",
        source_line=1,
        source_hash=hashlib.sha256(raw).hexdigest(),
        source_file_hash="f" * 64,
    )


class BridgeTimingCuration(unittest.TestCase):
    def test_single_relative_clock_is_stably_sorted_with_full_evidence(self):
        source = bridge(
            [
                event(2.0, "late"),
                event(1.0, "tie-first"),
                event(1.0, "tie-second"),
            ]
        )
        before = copy.deepcopy(source)

        decision = decide(source)

        self.assertEqual(decision.action, "repair")
        self.assertEqual(source, before, "curation must not mutate its input")
        self.assertEqual(
            [item["channel"] for item in decision.output_record["spike_events"]],
            ["tie-first", "tie-second", "late"],
        )
        manifest = decision.manifest
        self.assertEqual(manifest["source_path"], "bridge/batch-r02.jsonl")
        self.assertEqual(manifest["source_line"], 1)
        self.assertEqual(manifest["source_file_hash"], "f" * 64)
        self.assertEqual(manifest["action"], "repair")
        self.assertEqual(
            manifest["reason_codes"],
            [curate_bridge.REASON_REPAIRED],
        )
        evidence = manifest["evidence"]
        self.assertEqual(evidence["event_time_key"], "t_rel_ms")
        self.assertEqual(evidence["clock_scope"], "record_relative_global")
        self.assertEqual(evidence["stable_sort_permutation"], [1, 2, 0])
        self.assertEqual(evidence["moved_event_count"], 3)
        self.assertTrue(evidence["stable_ties_preserved"])
        self.assertEqual(len(evidence["adjacent_descents_before"]), 1)
        self.assertEqual(evidence["adjacent_descents_after"], [])
        self.assertNotEqual(
            evidence["original_event_order_hash"],
            evidence["output_event_order_hash"],
        )
        self.assertEqual(
            manifest["output_hash"],
            curate_bridge.sha256_hex(
                curate_bridge.canonical_json_bytes(decision.output_record)
            ),
        )

    def test_transform_is_deterministic_and_record_output_is_idempotent(self):
        source = bridge([event(3, "c"), event(1, "a"), event(2, "b")])

        first = decide(source)
        second = decide(source)
        reapplied = decide(first.output_record)

        self.assertEqual(first, second)
        self.assertEqual(reapplied.action, "retain")
        self.assertEqual(reapplied.output_record, first.output_record)
        self.assertEqual(
            reapplied.manifest["output_hash"], first.manifest["output_hash"]
        )

    def test_already_sorted_stream_is_retained_without_rewriting(self):
        source = bridge([event(1, "a"), event(1, "b"), event(2, "c")])

        decision = decide(source)

        self.assertEqual(decision.action, "retain")
        self.assertEqual(decision.output_record, source)
        self.assertEqual(
            decision.manifest["reason_codes"],
            [curate_bridge.REASON_RETAINED],
        )
        self.assertEqual(
            decision.manifest["evidence"]["stable_sort_permutation"],
            [0, 1, 2],
        )

    def test_mixed_timestamp_keys_are_quarantined(self):
        source = bridge(
            [
                event(2, "relative"),
                {"channel": "absolute", "t_ms": 1, "amplitude": 0.5},
            ]
        )

        decision = decide(source)

        self.assertEqual(decision.action, "quarantine")
        self.assertIsNone(decision.output_record)
        self.assertEqual(decision.quarantine_record, source)
        self.assertIn(
            curate_bridge.REASON_MIXED_TIME_KEYS,
            decision.manifest["reason_codes"],
        )
        self.assertFalse(decision.manifest["evidence"]["repair_eligible"])

    def test_multiple_declared_clock_domains_are_quarantined(self):
        source = bridge(
            [
                event(2, "a", clock_id="sensor-a"),
                event(1, "b", clock_id="sensor-b"),
            ]
        )

        decision = decide(source)

        self.assertEqual(decision.action, "quarantine")
        self.assertIn(
            curate_bridge.REASON_MULTIPLE_CLOCKS,
            decision.manifest["reason_codes"],
        )
        self.assertEqual(
            decision.manifest["evidence"]["declared_clock_domains"],
            ['clock_id="sensor-a"', 'clock_id="sensor-b"'],
        )

    def test_explicit_causal_or_sequence_order_is_quarantined(self):
        source = bridge(
            [
                event(2, "effect", caused_by="cause"),
                event(1, "cause", sequence_index=0),
            ]
        )

        decision = decide(source)

        self.assertEqual(decision.action, "quarantine")
        self.assertIn(
            curate_bridge.REASON_EXPLICIT_ORDER,
            decision.manifest["reason_codes"],
        )
        self.assertEqual(
            decision.manifest["evidence"]["explicit_order_fields"],
            ["caused_by", "sequence_index"],
        )

    def test_sorted_explicit_causal_order_is_retained_unchanged(self):
        source = bridge(
            [
                event(1, "cause", sequence_index=0),
                event(2, "effect", caused_by="cause"),
            ]
        )

        decision = decide(source)

        self.assertEqual(decision.action, "retain")
        self.assertEqual(decision.output_record, source)
        self.assertEqual(
            decision.manifest["evidence"]["explicit_order_fields"],
            ["caused_by", "sequence_index"],
        )

    def test_invalid_or_negative_times_are_quarantined(self):
        nonfinite = bridge([event(2, "a"), event(float("inf"), "b")])
        negative = bridge([event(2, "a"), event(-1, "b")])

        nonfinite_decision = decide(nonfinite)
        negative_decision = decide(negative)

        self.assertIn(
            curate_bridge.REASON_INVALID_TIME,
            nonfinite_decision.manifest["reason_codes"],
        )
        self.assertIn(
            curate_bridge.REASON_NEGATIVE_RELATIVE_TIME,
            negative_decision.manifest["reason_codes"],
        )
        self.assertEqual(nonfinite_decision.action, "quarantine")
        self.assertEqual(negative_decision.action, "quarantine")

    def test_jsonl_reader_preserves_exact_source_line_and_file_hashes(self):
        first = bridge([event(2, "é-late"), event(1, "early")], "one")
        second = bridge([event(1, "only")], "two")
        first_bytes = json.dumps(first, ensure_ascii=False).encode("utf-8")
        second_bytes = json.dumps(second, ensure_ascii=False).encode("utf-8")
        raw = first_bytes + b"\r\n" + second_bytes + b"\n"

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "bridge" / "batch-r02.jsonl"
            source.parent.mkdir()
            source.write_bytes(raw)

            decisions = curate_bridge.curate_jsonl(source, source_root=root)

        self.assertEqual([item.action for item in decisions], ["repair", "retain"])
        self.assertEqual(
            [item.manifest["source_line"] for item in decisions],
            [1, 2],
        )
        self.assertEqual(
            [item.manifest["source_path"] for item in decisions],
            ["bridge/batch-r02.jsonl", "bridge/batch-r02.jsonl"],
        )
        self.assertEqual(
            decisions[0].manifest["source_hash"],
            hashlib.sha256(first_bytes).hexdigest(),
        )
        self.assertEqual(
            decisions[1].manifest["source_hash"],
            hashlib.sha256(second_bytes).hexdigest(),
        )
        self.assertTrue(
            all(
                item.manifest["source_file_hash"] == hashlib.sha256(raw).hexdigest()
                for item in decisions
            )
        )

    def test_invalid_json_and_utf8_are_quarantined_with_exact_hashes(self):
        invalid_json = b'{"spike_events": [}\n'
        invalid_utf8 = b'{"id":"bad-\xff"}\n'

        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "bad.jsonl"
            source.write_bytes(invalid_json + invalid_utf8)
            decisions = curate_bridge.curate_jsonl(source)

        self.assertEqual(
            [item.action for item in decisions], ["quarantine", "quarantine"]
        )
        self.assertEqual(
            decisions[0].manifest["reason_codes"],
            [curate_bridge.REASON_INVALID_JSON],
        )
        self.assertEqual(
            decisions[1].manifest["reason_codes"],
            [curate_bridge.REASON_INVALID_UTF8],
        )
        self.assertEqual(
            decisions[0].manifest["source_hash"],
            hashlib.sha256(invalid_json.rstrip(b"\n")).hexdigest(),
        )
        self.assertEqual(
            decisions[1].manifest["source_hash"],
            hashlib.sha256(invalid_utf8.rstrip(b"\n")).hexdigest(),
        )

    def test_nonstandard_json_numeric_constant_is_source_quarantined(self):
        invalid_numeric = b'{"spike_events":[{"t_rel_ms":NaN}]}\n'

        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "nan.jsonl"
            source.write_bytes(invalid_numeric)
            decision = curate_bridge.curate_jsonl(source)[0]

        self.assertEqual(decision.action, "quarantine")
        self.assertEqual(
            decision.manifest["reason_codes"],
            [curate_bridge.REASON_INVALID_JSON],
        )
        self.assertIn(
            "non-standard JSON numeric constant",
            decision.manifest["evidence"]["parse_error"],
        )

    def test_missing_top_level_id_is_left_for_identity_lane(self):
        source = bridge([event(2, "b"), event(1, "a")])
        del source["id"]

        decision = decide(source)

        self.assertEqual(decision.action, "repair")
        self.assertIsNone(decision.manifest["output_id"])
        self.assertEqual(
            decision.manifest["output_id_status"], "pending_identity_transform"
        )
        self.assertEqual(decision.manifest["source_record_locator"], "bridge-fixture")


if __name__ == "__main__":
    unittest.main()
