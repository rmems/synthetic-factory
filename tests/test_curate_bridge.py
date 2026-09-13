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

import check_records  # noqa: E402
import curate_bridge  # noqa: E402
from exact_json import parse_finite_json_float  # noqa: E402
import training_audit  # noqa: E402

FIXTURES = REPO / "tests" / "fixtures"
RASTER_SCHEMA = REPO / "schemas" / "raster.schema.json"
R02_FIXTURE = "bridge-r02-defects.jsonl"
R03_FIXTURE = "bridge-r03-defects.jsonl"
QUARANTINE_FIXTURE = "bridge-quarantine.jsonl"


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
    def test_event_preflight_quarantines_an_empty_bridge_stream(self):
        helper = getattr(curate_bridge, "_bridge_event_preflight", None)
        self.assertIsNotNone(helper, "bridge shape exits need one preflight boundary")

        events, reason_codes, evidence = helper(bridge([]))

        self.assertIsNone(events)
        self.assertEqual(reason_codes, [curate_bridge.REASON_EMPTY_STREAM])
        self.assertEqual(evidence, {"event_count": 0})

    def test_source_hash_remains_a_required_keyword(self):
        with self.assertRaisesRegex(TypeError, "source_hash"):
            curate_bridge.curate_record(
                bridge([]),
                source_path="bridge/batch-r02.jsonl",
                source_line=1,
            )

    @staticmethod
    def _literal_timing_decision(left: str, right: str):
        payload = (
            '{"id":"exact-order","spike_events":['
            f'{{"channel":"left","t_rel_ms":{left},"amplitude":0.5}},'
            f'{{"channel":"right","t_rel_ms":{right},"amplitude":0.5}}],'
            '"language_view":{"trajectory":{"state":{"episode_id":"exact-order"}}}}'
        )
        record = json.loads(payload, parse_float=parse_finite_json_float)
        return curate_bridge.curate_record(
            record,
            source_path="bridge/exact.jsonl",
            source_line=1,
            source_hash=hashlib.sha256(payload.encode("utf-8")).hexdigest(),
            source_file_hash="f" * 64,
        )

    def test_decimal_tokens_drive_ordering_without_float_rounding(self):
        descending = self._literal_timing_decision("1.0000000000000001", "1.0")

        self.assertEqual(descending.action, "repair")
        self.assertEqual(
            descending.manifest["evidence"]["stable_sort_permutation"],
            [1, 0],
        )
        self.assertEqual(
            [event["channel"] for event in descending.output_record["spike_events"]],
            ["right", "left"],
        )
        encoded = curate_bridge.canonical_json_bytes(descending.output_record).decode()
        self.assertIn('"t_rel_ms":1.0000000000000001', encoded)

        tied = self._literal_timing_decision("1.0", "1.00")
        self.assertEqual(tied.action, "retain")
        self.assertEqual(tied.manifest["evidence"]["stable_sort_permutation"], [0, 1])

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
            curate_bridge.sha256_hex(curate_bridge.canonical_json_bytes(decision.output_record)),
        )

    def test_transform_is_deterministic_and_record_output_is_idempotent(self):
        source = bridge([event(3, "c"), event(1, "a"), event(2, "b")])

        first = decide(source)
        second = decide(source)
        reapplied = decide(first.output_record)

        self.assertEqual(first, second)
        self.assertEqual(reapplied.action, "retain")
        self.assertEqual(reapplied.output_record, first.output_record)
        self.assertEqual(reapplied.manifest["output_hash"], first.manifest["output_hash"])

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

    def test_exact_numeric_clock_domains_are_not_rounded_together(self):
        """Exact JSON clock identifiers must not collapse through ``float``."""
        events = json.loads(
            "["
            '{"channel":"a","t_rel_ms":2.0,"amplitude":0.5,"clock_id":1.0},'
            '{"channel":"b","t_rel_ms":1.0,"amplitude":0.5,'
            '"clock_id":1.0000000000000001}'
            "]",
            parse_float=parse_finite_json_float,
        )

        decision = decide(bridge(events))

        self.assertEqual(decision.action, "quarantine")
        self.assertIn(
            curate_bridge.REASON_MULTIPLE_CLOCKS,
            decision.manifest["reason_codes"],
        )
        self.assertEqual(
            decision.manifest["evidence"]["declared_clock_domains"],
            ["clock_id=1.0", "clock_id=1.0000000000000001"],
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

        self.assertEqual([item.action for item in decisions], ["quarantine", "quarantine"])
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

    def test_exponent_overflow_and_lone_surrogate_are_source_quarantined(self):
        sources = (
            b'{"id":"overflow","extra":1e999}\n',
            b'{"id":"surrogate","extra":"\\ud800"}\n',
        )

        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "invalid-scalars.jsonl"
            source.write_bytes(b"".join(sources))
            decisions = curate_bridge.curate_jsonl(source)

        self.assertEqual([decision.action for decision in decisions], ["quarantine"] * 2)
        self.assertEqual(
            [decision.manifest["reason_codes"] for decision in decisions],
            [[curate_bridge.REASON_INVALID_JSON]] * 2,
        )
        self.assertIn("non-finite JSON number", decisions[0].manifest["evidence"]["parse_error"])
        self.assertIn(
            "unpaired UTF-16 surrogate",
            decisions[1].manifest["evidence"]["parse_error"],
        )

    def test_missing_top_level_id_is_left_for_identity_lane(self):
        source = bridge([event(2, "b"), event(1, "a")])
        del source["id"]

        decision = decide(source)

        self.assertEqual(decision.action, "repair")
        self.assertIsNone(decision.manifest["output_id"])
        self.assertEqual(decision.manifest["output_id_status"], "pending_identity_transform")
        self.assertEqual(decision.manifest["source_record_locator"], "bridge-fixture")

    def test_legacy_meta_id_is_a_supported_source_locator(self):
        source = bridge([event(1, "a")])
        del source["id"]
        del source["language_view"]["trajectory"]["state"]["episode_id"]
        source["meta"] = {"id": "legacy-meta-id"}

        decision = decide(source)

        self.assertEqual(decision.manifest["source_record_locator"], "legacy-meta-id")

    def test_nested_episode_locator_keeps_precedence_over_legacy_meta_id(self):
        source = bridge([event(1, "a")])
        del source["id"]
        source["meta"] = {"id": "legacy-meta-id"}

        decision = decide(source)

        self.assertEqual(decision.manifest["source_record_locator"], "bridge-fixture")

    def test_jsonl_framing_preserves_unicode_line_separators_inside_strings(self):
        record = bridge([event(1, "line\u2028separator\u2029payload")], "unicode-lines")
        payload = json.dumps(record, ensure_ascii=False).encode("utf-8") + b"\r\n"

        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "batch.jsonl"
            source.write_bytes(payload)
            decisions = curate_bridge.curate_jsonl(source)

        self.assertEqual(len(decisions), 1)
        self.assertEqual(decisions[0].action, "retain")
        self.assertEqual(
            decisions[0].output_record["spike_events"][0]["channel"],
            "line\u2028separator\u2029payload",
        )
        self.assertEqual(
            decisions[0].manifest["source_hash"],
            hashlib.sha256(payload[:-2]).hexdigest(),
        )


def fixture_decisions(name):
    return curate_bridge.curate_jsonl(FIXTURES / name, source_root=FIXTURES)


def event_times(events):
    return [event[key] for event in events for key in ("t_rel_ms", "t_ms") if key in event]


class BridgeKnownDefectRegression(unittest.TestCase):
    """Bind the five documented r02-r03 defect streams to deterministic decisions.

    The raw run tree is immutable and absent from this checkout, so the five
    failures recorded in outputs/cleaned/2026-08-17/CHECK.md (batch-r02.jsonl
    lines 1-3, batch-r03.jsonl lines 2-3) are reconstructed as checked-in
    fixtures that mirror the real file layout line-for-line.
    """

    def test_r02_lines_1_to_3_are_deterministically_repaired(self):
        decisions = fixture_decisions(R02_FIXTURE)

        self.assertEqual([item.action for item in decisions], ["repair"] * 3)
        for line, decision in enumerate(decisions, 1):
            self.assertEqual(
                decision.manifest["reason_codes"],
                [curate_bridge.REASON_REPAIRED],
            )
            self.assertEqual(decision.manifest["source_path"], R02_FIXTURE)
            self.assertEqual(decision.manifest["source_line"], line)
            self.assertEqual(decision.manifest["source_record_locator"], f"nelb-r02-00{line}")
            self.assertEqual(decision.manifest["evidence"]["event_time_key"], "t_rel_ms")
            self.assertTrue(decision.manifest["evidence"]["repair_eligible"])

    def test_r02_line_2_repairs_the_mox_channel_humidity_artifact(self):
        source_events = json.loads(
            (FIXTURES / R02_FIXTURE).read_text(encoding="utf-8").splitlines()[1]
        )["spike_events"]
        source_times = {
            event["event_kind"]: event["t_rel_ms"]
            for event in source_events
            if event["channel"] == "mox_snO2_ch4"
        }
        self.assertEqual(source_times["humidity_artifact"], 7300.0)
        self.assertEqual(source_times["saturation"], 28900.0)
        self.assertGreater(
            [event["event_kind"] for event in source_events].index("humidity_artifact"),
            [event["event_kind"] for event in source_events].index("saturation"),
            "fixture must reproduce the documented within-channel violation",
        )

        decision = fixture_decisions(R02_FIXTURE)[1]

        repaired = decision.output_record["spike_events"]
        kinds = [event["event_kind"] for event in repaired]
        self.assertLess(kinds.index("humidity_artifact"), kinds.index("saturation"))
        times = event_times(repaired)
        self.assertEqual(times, sorted(times))

    def test_r03_line_1_is_retained_and_lines_2_to_3_are_repaired(self):
        decisions = fixture_decisions(R03_FIXTURE)

        self.assertEqual([item.action for item in decisions], ["retain", "repair", "repair"])
        self.assertEqual(
            decisions[0].manifest["reason_codes"],
            [curate_bridge.REASON_RETAINED],
        )
        source_line_1 = json.loads(
            (FIXTURES / R03_FIXTURE).read_text(encoding="utf-8").splitlines()[0]
        )
        self.assertEqual(decisions[0].output_record, source_line_1)
        for line, decision in zip((2, 3), decisions[1:]):
            self.assertEqual(
                decision.manifest["reason_codes"],
                [curate_bridge.REASON_REPAIRED],
            )
            self.assertEqual(decision.manifest["source_line"], line)
            self.assertEqual(decision.manifest["source_record_locator"], f"nelb-r03-00{line}")

    def test_ambiguous_timing_fixtures_quarantine_with_recoverable_records(self):
        decisions = fixture_decisions(QUARANTINE_FIXTURE)
        source_lines = (FIXTURES / QUARANTINE_FIXTURE).read_text(encoding="utf-8").splitlines()

        self.assertEqual([item.action for item in decisions], ["quarantine"] * 3)
        expected_reasons = (
            curate_bridge.REASON_MIXED_TIME_KEYS,
            curate_bridge.REASON_MULTIPLE_CLOCKS,
            curate_bridge.REASON_EXPLICIT_ORDER,
        )
        for decision, reason, raw_line in zip(decisions, expected_reasons, source_lines):
            self.assertIn(reason, decision.manifest["reason_codes"])
            self.assertIsNone(decision.output_record)
            self.assertEqual(decision.quarantine_record, json.loads(raw_line))
            self.assertFalse(decision.manifest["evidence"]["repair_eligible"])

    def test_fixture_decisions_are_deterministic_and_repairs_are_idempotent(self):
        for name in (R02_FIXTURE, R03_FIXTURE, QUARANTINE_FIXTURE):
            first = fixture_decisions(name)
            second = fixture_decisions(name)
            self.assertEqual(first, second, name)
            for decision in first:
                if decision.action != "repair":
                    continue
                reapplied = curate_bridge.curate_record(
                    decision.output_record,
                    source_path=decision.manifest["source_path"],
                    source_line=decision.manifest["source_line"],
                    source_hash=decision.manifest["source_hash"],
                    source_file_hash=decision.manifest["source_file_hash"],
                )
                self.assertEqual(reapplied.action, "retain")
                self.assertEqual(reapplied.output_record, decision.output_record)
                self.assertEqual(
                    reapplied.manifest["output_hash"],
                    decision.manifest["output_hash"],
                )

    def test_retained_and_repaired_streams_are_globally_non_decreasing(self):
        for name in (R02_FIXTURE, R03_FIXTURE):
            for decision in fixture_decisions(name):
                self.assertIn(decision.action, ("retain", "repair"))
                times = event_times(decision.output_record["spike_events"])
                self.assertEqual(times, sorted(times), decision.manifest["source_line"])
                self.assertEqual(decision.manifest["evidence"]["adjacent_descents_after"], [])

    def test_source_hashes_match_exact_fixture_bytes_and_inputs_stay_unchanged(self):
        for name in (R02_FIXTURE, R03_FIXTURE, QUARANTINE_FIXTURE):
            path = FIXTURES / name
            raw_before = path.read_bytes()
            decisions = fixture_decisions(name)
            self.assertEqual(path.read_bytes(), raw_before, "curation must not mutate its source")
            file_hash = hashlib.sha256(raw_before).hexdigest()
            for line, (decision, record_bytes) in enumerate(
                zip(decisions, raw_before.splitlines()), 1
            ):
                self.assertEqual(decision.manifest["source_line"], line)
                self.assertEqual(decision.manifest["source_path"], name)
                self.assertEqual(
                    decision.manifest["source_hash"],
                    hashlib.sha256(record_bytes).hexdigest(),
                )
                self.assertEqual(decision.manifest["source_file_hash"], file_hash)


class BridgeStrictAuditAlignment(unittest.TestCase):
    """Repaired decision outputs must satisfy the shared strict-audit predicate.

    Decision-output level only: the compose-and-materialize integration is
    owned by sf-c5l.7 and deliberately not exercised here.
    """

    def test_fixture_defect_streams_actually_trip_the_audit_predicate(self):
        for name, defective_lines in ((R02_FIXTURE, (1, 2, 3)), (R03_FIXTURE, (2, 3))):
            raw_lines = (FIXTURES / name).read_text(encoding="utf-8").splitlines()
            for line in defective_lines:
                events = json.loads(raw_lines[line - 1])["spike_events"]
                self.assertEqual(
                    training_audit.event_stream_status(events),
                    "unsorted",
                    f"{name}:{line}",
                )
                self.assertEqual(len(check_records.check_spikes(events, f"{name}:{line}")), 1)

    def test_retained_and_repaired_outputs_pass_the_audit_predicate(self):
        for name in (R02_FIXTURE, R03_FIXTURE):
            for decision in fixture_decisions(name):
                events = decision.output_record["spike_events"]
                where = f"{name}:{decision.manifest['source_line']}"
                self.assertEqual(training_audit.event_stream_status(events), "sorted", where)
                self.assertEqual(check_records.check_spikes(events, where), [])


def gate_snn_fixture():
    """The committed raster + third-factor + gate-as-SNN reference record."""

    line = (FIXTURES / "bridge_gate_snn.jsonl").read_text(encoding="utf-8").splitlines()[0]
    return json.loads(line)


if __name__ == "__main__":
    unittest.main()
