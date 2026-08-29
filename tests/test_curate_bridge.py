#!/usr/bin/env python3
"""Focused tests for deterministic Bridge timing curation."""

from __future__ import annotations

import contextlib
import copy
import hashlib
import io
import json
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

import check_records  # noqa: E402
import curate_bridge  # noqa: E402
import curate_gate  # noqa: E402
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


def raster_sidecars():
    """The committed raster + gate-as-SNN sidecars, as a producer emits them."""

    record = gate_snn_fixture()
    return {"raster": record["raster"], "gate_snn": record["gate_snn"]}


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


class BridgeMaterialization(unittest.TestCase):
    def _source_tree(self, root):
        first = root / "factory-a" / "batch-r01.jsonl"
        second = root / "factory-b" / "batch-r02.jsonl"
        first.parent.mkdir(parents=True)
        second.parent.mkdir(parents=True)
        # The materialized tree is gate-compatible, so its retained and
        # repaired records carry the raster sidecar that publication, the
        # training audit, and the distillation probe all require.
        retained = {**bridge([event(1, "already")], "retain"), **raster_sidecars()}
        repaired = {
            **bridge([event(2, "late"), event(1, "early")], "repair"),
            **raster_sidecars(),
        }
        first.write_text(
            "\n".join((json.dumps(retained), json.dumps(repaired), "")),
            encoding="utf-8",
        )
        second.write_text(
            json.dumps({"id": "quarantine", "not_bridge": True}) + "\n",
            encoding="utf-8",
        )
        return first, second

    def test_cli_materializes_a_gate_compatible_multi_file_lane_tree(self):
        with tempfile.TemporaryDirectory() as td:
            temporary = Path(td)
            source_root = temporary / "source"
            output = temporary / "lane-bridge"
            sources = self._source_tree(source_root)
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = curate_bridge.main(
                    [
                        "--source-root",
                        str(source_root),
                        "--out-dir",
                        str(output),
                        *(str(path) for path in sources),
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertEqual(json.loads(stdout.getvalue())["records"], 3)
            manifest_path = output / curate_bridge.MANIFEST_NAME
            entries = [
                json.loads(line)
                for line in manifest_path.read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual(
                [entry["action"] for entry in entries],
                ["retain", "repair", "quarantine"],
            )
            self.assertTrue((output / "factory-a" / "batch-r01.jsonl").is_file())
            self.assertFalse((output / "factory-b" / "batch-r02.jsonl").exists())

            lane = {
                "order": 1,
                "bead": "sf-c5l.1",
                "transform": curate_bridge.TRANSFORM_NAME,
                "version": curate_bridge.TRANSFORM_VERSION,
                "outputs_dir": output,
                "manifest_path": manifest_path,
                "manifest_format": "jsonl",
                "artifacts": [],
            }
            prepared = curate_gate._prepare_lane(
                lane,
                curate_gate._load_source_records(source_root),
            )

        self.assertEqual(len(prepared["entries"]), 3)
        self.assertEqual(len(prepared["records"]), 2)
        self.assertEqual(
            {record["output_id"] for record in prepared["records"]},
            {"retain", "repair"},
        )

    def test_materialization_refuses_clobber_and_preserves_existing_tree(self):
        with tempfile.TemporaryDirectory() as td:
            temporary = Path(td)
            source_root = temporary / "source"
            sources = self._source_tree(source_root)
            output = temporary / "lane-bridge"
            output.mkdir()
            marker = output / "owned-by-someone-else"
            marker.write_text("preserve", encoding="utf-8")

            with self.assertRaisesRegex(
                curate_bridge.BridgeCurationError, "already exists"
            ):
                curate_bridge.materialize_paths(
                    sources,
                    source_root=source_root,
                    output_dir=output,
                )

            self.assertEqual(marker.read_text(encoding="utf-8"), "preserve")
            self.assertEqual(sorted(path.name for path in output.iterdir()), [marker.name])

    def test_materialization_refuses_raw_destination_and_symlink_source(self):
        with tempfile.TemporaryDirectory() as td:
            temporary = Path(td)
            source_root = temporary / "source"
            sources = self._source_tree(source_root)
            raw_parent = temporary / "outputs" / "raw" / "run"
            raw_parent.mkdir(parents=True)
            with self.assertRaisesRegex(
                curate_bridge.BridgeCurationError, "immutable raw evidence"
            ):
                curate_bridge.materialize_paths(
                    sources,
                    source_root=source_root,
                    output_dir=raw_parent / "lane-bridge",
                )

            linked = source_root / "linked.jsonl"
            linked.symlink_to(sources[0])
            with self.assertRaisesRegex(
                curate_bridge.BridgeCurationError, "real JSONL file"
            ):
                curate_bridge.materialize_paths(
                    [linked],
                    source_root=source_root,
                    output_dir=temporary / "linked-output",
                )

    def test_materialize_paths_in_process_and_rejects_unsafe_layout(self):
        with tempfile.TemporaryDirectory() as td:
            temporary = Path(td)
            source_root = temporary / "source"
            sources = self._source_tree(source_root)
            output = temporary / "lane-bridge"
            decisions = curate_bridge.materialize_paths(
                sources,
                source_root=source_root,
                output_dir=output,
            )
            self.assertEqual(len(decisions), 3)
            self.assertTrue((output / curate_bridge.MANIFEST_NAME).is_file())

            with self.assertRaisesRegex(curate_bridge.BridgeCurationError, "real directory"):
                curate_bridge.materialize_paths(
                    sources,
                    source_root=sources[0],
                    output_dir=temporary / "out-file-root",
                )
            with self.assertRaisesRegex(curate_bridge.BridgeCurationError, "at least one"):
                curate_bridge.materialize_paths(
                    [],
                    source_root=source_root,
                    output_dir=temporary / "out-empty",
                )
            with self.assertRaisesRegex(curate_bridge.BridgeCurationError, "inside source_root"):
                curate_bridge.materialize_paths(
                    sources,
                    source_root=source_root,
                    output_dir=source_root / "nested-out",
                )
            with self.assertRaisesRegex(curate_bridge.BridgeCurationError, "end in .jsonl"):
                curate_bridge.materialize_paths(
                    sources,
                    source_root=source_root,
                    output_dir=temporary / "out-manifest",
                    manifest_name="manifest.json",
                )
            outside = temporary / "outside.jsonl"
            outside.write_text("{}\n", encoding="utf-8")
            with self.assertRaisesRegex(curate_bridge.BridgeCurationError, "outside source_root"):
                curate_bridge.materialize_paths(
                    [outside],
                    source_root=source_root,
                    output_dir=temporary / "out-outside",
                )
            with self.assertRaisesRegex(curate_bridge.BridgeCurationError, "safe relative path"):
                curate_bridge._safe_relative_path("../escape.jsonl", label="manifest_name")


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
            self.assertEqual(
                decision.manifest["source_record_locator"], f"nelb-r02-00{line}"
            )
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

        self.assertEqual(
            [item.action for item in decisions], ["retain", "repair", "repair"]
        )
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
            self.assertEqual(
                decision.manifest["source_record_locator"], f"nelb-r03-00{line}"
            )

    def test_ambiguous_timing_fixtures_quarantine_with_recoverable_records(self):
        decisions = fixture_decisions(QUARANTINE_FIXTURE)
        source_lines = (FIXTURES / QUARANTINE_FIXTURE).read_text(
            encoding="utf-8"
        ).splitlines()

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
                self.assertEqual(
                    decision.manifest["evidence"]["adjacent_descents_after"], []
                )

    def test_source_hashes_match_exact_fixture_bytes_and_inputs_stay_unchanged(self):
        for name in (R02_FIXTURE, R03_FIXTURE, QUARANTINE_FIXTURE):
            path = FIXTURES / name
            raw_before = path.read_bytes()
            decisions = fixture_decisions(name)
            self.assertEqual(
                path.read_bytes(), raw_before, "curation must not mutate its source"
            )
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
                self.assertEqual(
                    len(check_records.check_spikes(events, f"{name}:{line}")), 1
                )

    def test_retained_and_repaired_outputs_pass_the_audit_predicate(self):
        for name in (R02_FIXTURE, R03_FIXTURE):
            for decision in fixture_decisions(name):
                events = decision.output_record["spike_events"]
                where = f"{name}:{decision.manifest['source_line']}"
                self.assertEqual(
                    training_audit.event_stream_status(events), "sorted", where
                )
                self.assertEqual(check_records.check_spikes(events, where), [])


def gate_snn_fixture():
    """The committed raster + third-factor + gate-as-SNN reference record."""

    line = (FIXTURES / "bridge_gate_snn.jsonl").read_text(encoding="utf-8").splitlines()[0]
    return json.loads(line)


class RasterAndGateSnnCuration(unittest.TestCase):
    """The sidecar contract SNN distillation depends on.

    ``curate_bridge`` owns the spike arithmetic (20-50 ms window,
    ``spikes = round(neurons * rate * window_s)``, 23 pJ/spike) for every
    consumer, so these tests pin the reason codes and the shared summary the
    training audit and the distillation probe read.
    """

    def test_reference_record_curates_clean_with_full_raster_evidence(self):
        decision = decide(gate_snn_fixture())
        self.assertEqual(decision.action, "retain")
        evidence = decision.manifest["evidence"]["raster"]
        self.assertTrue(evidence["raster_spike_budget_valid"])
        self.assertTrue(evidence["raster_energy_pJ_valid"])
        self.assertTrue(evidence["raster_energy_uJ_valid"])
        self.assertEqual(evidence["raster_routing_table_entries"], 2)
        self.assertTrue(evidence["raster_third_factor_valid"])
        self.assertEqual(evidence["raster_third_factor_tau_e_s"], 2.0)
        self.assertTrue(evidence["gate_snn_valid"])
        self.assertEqual(evidence["gate_snn_total_neurons"], 128)

    def test_missing_raster_quarantines_only_when_required(self):
        record = bridge([event(1.0, "a"), event(2.0, "b")])
        self.assertEqual(decide(record).action, "retain")

        raw = json.dumps(record, ensure_ascii=False).encode("utf-8")
        strict = curate_bridge.curate_record(
            record,
            source_path="bridge/batch-r02.jsonl",
            source_line=1,
            source_hash=hashlib.sha256(raw).hexdigest(),
            require_raster=True,
        )
        self.assertEqual(strict.action, "quarantine")
        self.assertIn(
            curate_bridge.REASON_RASTER_MISSING, strict.manifest["reason_codes"]
        )

    def test_spike_product_mismatch_is_quarantined(self):
        record = gate_snn_fixture()
        record["raster"]["spikes"] = 500
        decision = decide(record)
        self.assertEqual(decision.action, "quarantine")
        self.assertIn(
            curate_bridge.REASON_RASTER_SPIKE_BUDGET, decision.manifest["reason_codes"]
        )

    def test_malformed_third_factor_routing_is_quarantined(self):
        for third_factor in (
            {"modulator": "dopamine"},
            {"modulator": "dopamine", "tau_e_s": 2.0},
            {"modulator": "", "tau_e_s": 2.0, "eligibility": "pre_post_stdp"},
            {"modulator": "dopamine", "tau_e_s": 0, "eligibility": "pre_post_stdp"},
            {"modulator": "dopamine", "tau_e_s": 2.0, "eligibility": ""},
            "dopamine",
        ):
            with self.subTest(third_factor=third_factor):
                record = gate_snn_fixture()
                record["raster"]["routing"]["third_factor"] = third_factor
                decision = decide(record)
                self.assertEqual(decision.action, "quarantine")
                self.assertIn(
                    curate_bridge.REASON_THIRD_FACTOR_INVALID,
                    decision.manifest["reason_codes"],
                )

    def test_missing_third_factor_routing_is_quarantined(self):
        record = gate_snn_fixture()
        del record["raster"]["routing"]["third_factor"]

        decision = decide(record)

        self.assertEqual(decision.action, "quarantine")
        self.assertIn(
            curate_bridge.REASON_THIRD_FACTOR_INVALID,
            decision.manifest["reason_codes"],
        )
        evidence = decision.manifest["evidence"]["raster"]
        self.assertFalse(evidence["raster_third_factor_present"])

    def test_only_valid_routing_objects_count_toward_coverage(self):
        record = gate_snn_fixture()
        record["raster"]["routing"]["table"].extend(
            ["not-a-route", {"from": "", "to": "gate"}]
        )

        decision = decide(record)

        self.assertEqual(decision.action, "quarantine")
        self.assertIn(
            curate_bridge.REASON_RASTER_ROUTING, decision.manifest["reason_codes"]
        )
        evidence = decision.manifest["evidence"]["raster"]
        self.assertEqual(evidence["raster_routing_table_declared_entries"], 4)
        self.assertEqual(evidence["raster_routing_table_entries"], 2)
        self.assertEqual(evidence["raster_routing_table_invalid_indices"], [2, 3])

    def test_tau_e_ms_alias_is_accepted(self):
        record = gate_snn_fixture()
        record["raster"]["routing"]["third_factor"] = {
            "modulator": "dopamine",
            "tau_e_ms": 2000,
            "eligibility": "pre_post_stdp",
        }
        decision = decide(record)
        self.assertEqual(decision.action, "retain")
        evidence = decision.manifest["evidence"]["raster"]
        self.assertEqual(evidence["raster_third_factor_tau_e_s"], 2.0)

    def test_gate_snn_spec_defects_are_quarantined(self):
        broken = (
            {"decision_window_ms": 25, "populations": []},
            {
                "decision_window_ms": 25,
                "populations": [{"name": "g", "neurons": 0, "threshold": 1.0}],
            },
            {"decision_window_ms": 25, "populations": [{"name": "g", "neurons": 8}]},
            {"populations": [{"name": "g", "neurons": 8, "threshold": 1.0}]},
        )
        for spec in broken:
            with self.subTest(spec=spec):
                record = gate_snn_fixture()
                record["gate_snn"] = spec
                decision = decide(record)
                self.assertEqual(decision.action, "quarantine")
                self.assertIn(
                    curate_bridge.REASON_GATE_SNN_INVALID,
                    decision.manifest["reason_codes"],
                )

    def test_gate_snn_population_spike_budget_is_enforced(self):
        record = gate_snn_fixture()
        record["gate_snn"]["populations"][0]["spikes"] = 999
        decision = decide(record)
        self.assertEqual(decision.action, "quarantine")
        self.assertIn(
            curate_bridge.REASON_RASTER_SPIKE_BUDGET, decision.manifest["reason_codes"]
        )

    def test_gate_snn_window_aliases_must_agree(self):
        record = gate_snn_fixture()
        record["gate_snn"]["decision_window_s"] = 0.030

        decision = decide(record)

        self.assertEqual(decision.action, "quarantine")
        self.assertIn(
            curate_bridge.REASON_GATE_SNN_INVALID, decision.manifest["reason_codes"]
        )
        evidence = decision.manifest["evidence"]["raster"]
        self.assertFalse(evidence["gate_snn_decision_window_consistent"])

    def test_declared_nonnumeric_raster_fields_are_quarantined(self):
        for field, value, reason in (
            ("window_s", "bogus", curate_bridge.REASON_RASTER_WINDOW),
            ("energy_uJ", "bogus", curate_bridge.REASON_RASTER_ENERGY),
            ("energy_pJ", "bogus", curate_bridge.REASON_RASTER_ENERGY),
        ):
            with self.subTest(field=field):
                record = gate_snn_fixture()
                record["raster"][field] = value
                decision = decide(record)
                self.assertEqual(decision.action, "quarantine")
                self.assertIn(reason, decision.manifest["reason_codes"])

    def test_overflowing_gate_spike_product_is_quarantined(self):
        record = gate_snn_fixture()
        record["gate_snn"]["decision_window_ms"] = 1e308
        record["gate_snn"]["decision_window_s"] = 1e308 / 1000.0
        record["gate_snn"]["populations"][0]["mean_rate_hz"] = 1e308
        record["gate_snn"]["populations"][0]["spikes"] = 1

        decision = decide(record)

        self.assertEqual(decision.action, "quarantine")
        self.assertIn(
            curate_bridge.REASON_GATE_SNN_INVALID, decision.manifest["reason_codes"]
        )

    def test_gate_snn_population_budget_shape_rejects_nonpositive_values(self):
        mutations = (
            ("mean_rate_hz", 0),
            ("mean_rate_hz", -1),
            ("spikes", -1),
        )
        for key, value in mutations:
            with self.subTest(key=key, value=value):
                record = gate_snn_fixture()
                record["gate_snn"]["populations"][0][key] = value

                decision = decide(record)

                self.assertEqual(decision.action, "quarantine")
                self.assertIn(
                    curate_bridge.REASON_GATE_SNN_INVALID,
                    decision.manifest["reason_codes"],
                )

    def test_gate_snn_decision_is_required_and_matches_safety_decision(self):
        for decision in (None, "REJECT"):
            with self.subTest(decision=decision):
                record = gate_snn_fixture()
                if decision is None:
                    del record["gate_snn"]["decision"]
                else:
                    record["gate_snn"]["decision"] = decision

                result = decide(record)

                self.assertEqual(result.action, "quarantine")
                self.assertIn(
                    curate_bridge.REASON_GATE_SNN_INVALID,
                    result.manifest["reason_codes"],
                )
                evidence = result.manifest["evidence"]["raster"]
                self.assertFalse(evidence["gate_snn_decision_valid"])

    def test_gate_snn_is_found_under_every_supported_carrier(self):
        spec = gate_snn_fixture()["gate_snn"]
        carriers = {
            "gate_snn": lambda record: record,
            "meta.gate_snn": lambda record: record.setdefault("meta", {}),
            "language_view.trajectory.gate_snn": (
                lambda record: record["language_view"]["trajectory"]
            ),
            "language_view.trajectory.safety_decision.gate_snn": (
                lambda record: record["language_view"]["trajectory"]["safety_decision"]
            ),
        }
        for location, container in carriers.items():
            with self.subTest(location=location):
                record = gate_snn_fixture()
                del record["gate_snn"]
                container(record)["gate_snn"] = copy.deepcopy(spec)
                found_location, found = curate_bridge.gate_snn_sidecar(record)
                self.assertEqual(found_location, location)
                self.assertEqual(found, spec)

    def test_raster_status_summarizes_without_reading_prose(self):
        status = curate_bridge.raster_status(gate_snn_fixture())
        self.assertTrue(status["bridge_record"])
        self.assertTrue(status["raster_valid"])
        self.assertEqual(status["raster_location"], "raster")
        self.assertEqual(status["routing_table_entries"], 2)
        self.assertTrue(status["third_factor_present"])
        self.assertTrue(status["gate_snn_present"])
        self.assertTrue(status["gate_snn_valid"])
        self.assertEqual(status["spikes"], 123)
        self.assertEqual(status["reason_codes"], [])

    def test_raster_status_reports_a_non_bridge_record_as_out_of_scope(self):
        malformed = (
            {"id": "not-a-bridge"},
            {"spike_events": [], "language_view": "not-an-object"},
            {"spike_events": [], "language_view": {"trajectory": "not-an-object"}},
        )
        for record in malformed:
            with self.subTest(record=record):
                status = curate_bridge.raster_status(record)
                self.assertFalse(status["bridge_record"])
                self.assertFalse(status["raster_present"])
                self.assertEqual(status["reason_codes"], [])

    def test_raster_status_reports_missing_sidecars(self):
        status = curate_bridge.raster_status(bridge([event(1.0, "a")]))
        self.assertTrue(status["bridge_record"])
        self.assertFalse(status["raster_present"])
        self.assertFalse(status["gate_snn_present"])
        self.assertEqual(
            status["reason_codes"], [curate_bridge.REASON_RASTER_MISSING]
        )


class RasterSchemaParity(unittest.TestCase):
    """Every runtime-supported sidecar carrier shares one schema definition."""

    def setUp(self):
        self.schema = json.loads(RASTER_SCHEMA.read_text(encoding="utf-8"))

    def test_nested_gate_snn_carriers_reference_the_canonical_definition(self):
        trajectory = self.schema["properties"]["language_view"]["properties"][
            "trajectory"
        ]["properties"]

        self.assertEqual(trajectory["gate_snn"], {"$ref": "#/$defs/gate_snn"})
        self.assertEqual(
            trajectory["safety_decision"]["properties"]["gate_snn"],
            {"$ref": "#/$defs/gate_snn"},
        )

    def test_nested_gate_compute_carriers_reference_the_canonical_definition(self):
        """Every carrier ``_gate_compute_sidecar`` accepts is schema-constrained.

        The nested carriers used to be unconstrained: ``additionalProperties``
        is enabled on the trajectory objects, so a malformed nested compute
        block passed the published schema and was only rejected later by the
        runtime publication validator.
        """

        ref = {"$ref": "#/$defs/gate_compute"}
        trajectory = self.schema["properties"]["language_view"]["properties"][
            "trajectory"
        ]["properties"]

        self.assertEqual(self.schema["properties"]["gate_compute"], ref)
        self.assertEqual(trajectory["gate_compute"], ref)
        self.assertEqual(trajectory["safety_decision"]["properties"]["gate_compute"], ref)
        self.assertIn("per_check", self.schema["$defs"]["gate_compute"]["properties"])

        # The definition must cover exactly the carriers the runtime resolves.
        for location in (
            "gate_compute",
            "language_view.trajectory.gate_compute",
            "language_view.trajectory.safety_decision.gate_compute",
        ):
            with self.subTest(location=location):
                record = gate_snn_fixture()
                record.pop("gate_compute", None)
                target = record
                for key in location.split(".")[:-1]:
                    target = target.setdefault(key, {})
                target["gate_compute"] = {"per_check": []}

                found, _value = curate_bridge._gate_compute_sidecar(record)

                self.assertEqual(found, location)
                node = self.schema["properties"]
                for key in location.split("."):
                    node = node[key]
                    node = node.get("properties", node)
                self.assertEqual(node, ref)

    def test_schema_requires_nonblank_routing_endpoints_like_the_validator(self):
        """A blank ``from``/``to`` must fail the schema, not just the runtime.

        ``_validate_raster`` rejects an entry whose endpoints are blank after
        trimming, so a producer that validated against this schema and then
        failed publication would have followed every documented instruction.
        """

        table_entry = self.schema["$defs"]["raster"]["properties"]["routing"][
            "properties"
        ]["table"]["items"]

        # minLength alone stops "" but not "   ", and the runtime trims before
        # it checks, so the endpoints carry the same \S pattern the gate
        # decision uses.  Checked through the schema's own keywords: this
        # suite runs on the standard library alone.
        for endpoint in ("from", "to"):
            for blank in ("", "   ", "\t\n"):
                with self.subTest(endpoint=endpoint, value=repr(blank)):
                    keywords = table_entry["properties"][endpoint]
                    record = gate_snn_fixture()
                    entry = {"from": "a", "to": "b"}
                    entry[endpoint] = blank
                    record["raster"]["routing"]["table"] = [entry]

                    status = curate_bridge.raster_status(record)

                    self.assertFalse(status["raster_valid"])
                    self.assertIn(
                        curate_bridge.REASON_RASTER_ROUTING, status["reason_codes"]
                    )
                    self.assertTrue(
                        len(blank) < keywords["minLength"]
                        or re.compile(keywords["pattern"]).search(blank) is None,
                        "schema must reject what the runtime validator rejects",
                    )

        for endpoint in ("from", "to"):
            with self.subTest(endpoint=endpoint, value="accepted"):
                keywords = table_entry["properties"][endpoint]
                self.assertGreaterEqual(len("thalamus"), keywords["minLength"])
                self.assertIsNotNone(
                    re.compile(keywords["pattern"]).search("thalamus")
                )

    def test_schema_pins_the_runtime_gate_and_routing_requirements(self):
        gate = self.schema["$defs"]["gate_snn"]
        raster = self.schema["$defs"]["raster"]
        routing = raster["properties"]["routing"]
        table_entry = routing["properties"]["table"]["items"]

        self.assertEqual(gate["required"], ["decision", "populations"])
        self.assertIn("third_factor", routing["required"])
        self.assertEqual(
            routing["properties"]["third_factor"]["required"],
            ["modulator", "eligibility"],
        )
        self.assertEqual(table_entry["required"], ["from", "to"])
        population = gate["properties"]["populations"]["items"]
        self.assertTrue(population["allOf"])

    def test_schema_rejects_a_blank_gate_decision_like_the_validator_does(self):
        """The published schema is the producer contract; it must not be looser.

        ``_validate_gate_snn`` refuses a blank or whitespace-only decision, so
        a producer that validated against this schema and then failed
        publication would have followed every documented instruction.  Checked
        against the schema's own keywords rather than through a JSON Schema
        library: this suite runs on the standard library alone.
        """

        decision = self.schema["$defs"]["gate_snn"]["properties"]["decision"]
        self.assertEqual(decision["type"], "string")
        self.assertGreaterEqual(decision["minLength"], 1)
        # JSON Schema "pattern" is an unanchored search, like re.search.
        pattern = re.compile(decision["pattern"])
        gate = {
            "decision_window_ms": 10,
            "populations": [{"name": "p", "neurons": 4, "threshold": 0.5}],
        }

        for blank in ("", "   ", "\t\n"):
            with self.subTest(decision=repr(blank)):
                reason_codes: list[str] = []
                curate_bridge._validate_gate_snn(
                    {**gate, "decision": blank},
                    reason_codes=reason_codes,
                    evidence={},
                )
                self.assertIn(curate_bridge.REASON_GATE_SNN_INVALID, reason_codes)
                self.assertTrue(
                    len(blank) < decision["minLength"] or pattern.search(blank) is None,
                    "schema must reject what the runtime validator rejects",
                )

        accepted: list[str] = []
        curate_bridge._validate_gate_snn(
            {**gate, "decision": "ACCEPT"}, reason_codes=accepted, evidence={}
        )
        self.assertEqual(accepted, [])
        self.assertGreaterEqual(len("ACCEPT"), decision["minLength"])
        self.assertIsNotNone(pattern.search("ACCEPT"))


class RasterArithmeticReviewFollowUps(unittest.TestCase):
    """Spike-arithmetic holes the PR #94 review found in the shared validator.

    Every downstream consumer — the curator, the publish gate, the training
    audit and the distillation probe — reads ``raster_status``, so a budget
    the validator cannot evaluate has to surface as a reason code rather than
    as an exception or as a silently accepted record.
    """

    def test_unrepresentable_spike_count_is_a_budget_defect_not_an_overflow(self):
        record = gate_snn_fixture()
        record["raster"]["spikes"] = 10**400
        record["raster"]["energy_uJ"] = 1.0

        status = curate_bridge.raster_status(record)

        self.assertFalse(status["raster_valid"])
        self.assertIn(
            curate_bridge.REASON_RASTER_SPIKE_BUDGET, status["reason_codes"]
        )

    def test_unrepresentable_energy_evidence_stays_json_serializable(self):
        record = gate_snn_fixture()
        record["raster"]["spikes"] = 10**400
        record["raster"]["energy_pJ"] = 1.0
        record["raster"]["energy_uJ"] = 1.0

        decision = decide(record)

        self.assertEqual(decision.action, "quarantine")
        json.dumps(decision.manifest, allow_nan=False)

    def test_gate_compute_totals_survive_an_unrepresentable_spike_sum(self):
        record = gate_snn_fixture()
        record["gate_compute"] = {
            "per_check": [
                {
                    "neurons": 4,
                    "mean_rate_hz": 10.0,
                    "window_s": 0.05,
                    "spikes": 10**400,
                }
            ],
            "total_energy_uJ": 1.0,
        }

        status = curate_bridge.raster_status(record)

        self.assertFalse(status["raster_valid"])
        json.dumps(status["evidence"], allow_nan=False)

    def test_a_malformed_declared_gate_compute_carrier_is_not_skipped(self):
        record = gate_snn_fixture()
        record["gate_compute"] = "bad"
        record["language_view"]["trajectory"]["gate_compute"] = {
            "per_check": [
                {"neurons": 2, "mean_rate_hz": 10.0, "window_s": 0.05, "spikes": 1}
            ]
        }

        self.assertEqual(
            curate_bridge._gate_compute_sidecar(record), ("gate_compute", "bad")
        )
        status = curate_bridge.raster_status(record)

        self.assertFalse(status["raster_valid"])
        self.assertIn(
            curate_bridge.REASON_RASTER_SPIKE_BUDGET, status["reason_codes"]
        )

    def test_gate_compute_budget_operands_must_be_physically_positive(self):
        for check in (
            {"neurons": -2, "mean_rate_hz": -3.0, "window_s": 1.0, "spikes": 6},
            {"neurons": 0, "mean_rate_hz": 10.0, "window_s": 0.05, "spikes": 0},
            {"neurons": 4, "mean_rate_hz": 10.0, "window_s": -0.05, "spikes": -2},
        ):
            with self.subTest(check=check):
                record = gate_snn_fixture()
                record["gate_compute"] = {"per_check": [check]}

                status = curate_bridge.raster_status(record)

                self.assertFalse(status["raster_valid"])
                self.assertIn(
                    curate_bridge.REASON_RASTER_SPIKE_BUDGET,
                    status["reason_codes"],
                )

    def test_a_well_formed_gate_compute_budget_still_passes(self):
        record = gate_snn_fixture()
        record["gate_compute"] = {
            "per_check": [
                {"neurons": 4, "mean_rate_hz": 10.0, "window_s": 0.05, "spikes": 2}
            ],
            "total_energy_pJ": 2 * curate_bridge.RASTER_ENERGY_PJ_PER_SPIKE,
        }

        status = curate_bridge.raster_status(record)

        self.assertTrue(status["raster_valid"], status["reason_codes"])
        self.assertTrue(status["evidence"]["gate_compute_spike_budget_valid"])

    def test_conflicting_eligibility_time_aliases_are_rejected(self):
        record = gate_snn_fixture()
        record["raster"]["routing"]["third_factor"]["tau_e_ms"] = 1

        status = curate_bridge.raster_status(record)

        self.assertFalse(status["raster_valid"])
        self.assertIn(
            curate_bridge.REASON_THIRD_FACTOR_INVALID, status["reason_codes"]
        )

    def test_agreeing_eligibility_time_aliases_stay_valid(self):
        record = gate_snn_fixture()
        record["raster"]["routing"]["third_factor"]["tau_e_ms"] = 2000

        status = curate_bridge.raster_status(record)

        self.assertTrue(status["raster_valid"], status["reason_codes"])
        self.assertEqual(status["evidence"]["raster_third_factor_tau_e_s"], 2.0)


class MaterializedLaneRequiresRasters(unittest.TestCase):
    """``--out-dir`` publishes a *gate-compatible* tree, so it must gate.

    The publication, audit and probe contracts all reject a Bridge record with
    no raster sidecar; materializing one into the tree this module advertises
    as gate-compatible would hand a downstream distillation run a record every
    other layer refuses.
    """

    def source_tree(self, root, records):
        source_root = Path(root) / "raw"
        batch = source_root / "neuromorphic-event-language-bridge" / "batch-r02.jsonl"
        batch.parent.mkdir(parents=True)
        batch.write_text(
            "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
            encoding="utf-8",
        )
        return source_root, batch

    def test_materialized_tree_quarantines_a_raster_less_record(self):
        with tempfile.TemporaryDirectory() as td:
            records = [bridge([event(1.0, "a"), event(2.0, "b")], "no-raster")]
            source_root, batch = self.source_tree(td, records)
            out_dir = Path(td) / "lane"

            decisions = curate_bridge.materialize_paths(
                [batch], source_root=source_root, output_dir=out_dir
            )

            self.assertEqual([d.action for d in decisions], ["quarantine"])
            self.assertIn(
                curate_bridge.REASON_RASTER_MISSING, decisions[0].manifest["reason_codes"]
            )
            self.assertFalse(
                (out_dir / "neuromorphic-event-language-bridge" / "batch-r02.jsonl").exists()
            )

    def test_materialized_tree_keeps_a_raster_backed_record(self):
        with tempfile.TemporaryDirectory() as td:
            source_root, batch = self.source_tree(td, [gate_snn_fixture()])
            out_dir = Path(td) / "lane"

            decisions = curate_bridge.materialize_paths(
                [batch], source_root=source_root, output_dir=out_dir
            )

            self.assertEqual([d.action for d in decisions], ["retain"])
            self.assertTrue(
                (out_dir / "neuromorphic-event-language-bridge" / "batch-r02.jsonl").exists()
            )

    def test_the_pure_decision_api_still_defaults_to_lenient(self):
        with tempfile.TemporaryDirectory() as td:
            records = [bridge([event(1.0, "a"), event(2.0, "b")], "no-raster")]
            _source_root, batch = self.source_tree(td, records)

            self.assertEqual(
                [d.action for d in curate_bridge.curate_jsonl(batch)], ["retain"]
            )
            self.assertEqual(
                [
                    d.action
                    for d in curate_bridge.curate_jsonl(batch, require_raster=True)
                ],
                ["quarantine"],
            )


def zero_spike_record():
    """The reference record retuned to a legitimately zero-spike raster.

    ``round(1 * 1.0 * 0.02)`` is 0, so the budget, the 23 pJ/spike energy and
    both declared totals are all exactly zero -- the case where an
    absolute-tolerance comparison alone would accept a negative energy.
    """

    record = gate_snn_fixture()
    record["raster"].update(
        {
            "neurons": 1,
            "mean_rate_hz": 1.0,
            "window_ms": 20,
            "window_s": 0.02,
            "spikes": 0,
            "energy_pJ": 0,
            "energy_uJ": 0,
            "excerpt": [{"t_ms": 5.0, "neuron_id": 0}],
        }
    )
    return record


class DeclaredNullCarriersAndEnergyBounds(unittest.TestCase):
    """PR #94 review follow-ups on the shared sidecar/energy contract.

    Two holes the earlier carrier-precedence and overflow fixes left open:
    an explicit ``null`` sidecar was read as an absence rather than as a
    declaration, and the energy tolerance accepted small negative values
    whenever the expected energy was zero.
    """

    def test_a_declared_null_raster_does_not_fall_through_to_meta(self):
        record = gate_snn_fixture()
        record["meta"] = {"raster": copy.deepcopy(record["raster"])}
        record["raster"] = None

        location, value = curate_bridge.raster_sidecar(record)

        self.assertEqual(location, "raster")
        self.assertIsNone(value)
        status = curate_bridge.raster_status(record)
        self.assertFalse(status["raster_valid"])
        self.assertIn(curate_bridge.REASON_RASTER_EXCERPT, status["reason_codes"])

    def test_a_declared_null_gate_snn_does_not_fall_through_to_meta(self):
        record = gate_snn_fixture()
        record["meta"] = {"gate_snn": copy.deepcopy(record["gate_snn"])}
        record["gate_snn"] = None

        location, value = curate_bridge.gate_snn_sidecar(record)

        self.assertEqual(location, "gate_snn")
        self.assertIsNone(value)
        status = curate_bridge.raster_status(record)
        self.assertFalse(status["raster_valid"])
        self.assertIn(curate_bridge.REASON_GATE_SNN_INVALID, status["reason_codes"])

    def test_a_declared_null_gate_compute_does_not_fall_through_to_nested(self):
        record = gate_snn_fixture()
        record["gate_compute"] = None
        record["language_view"]["trajectory"]["gate_compute"] = {
            "per_check": [
                {"neurons": 2, "mean_rate_hz": 10.0, "window_s": 0.05, "spikes": 1}
            ]
        }

        location, value = curate_bridge._gate_compute_sidecar(record)

        self.assertEqual(location, "gate_compute")
        self.assertIsNone(value)
        status = curate_bridge.raster_status(record)
        self.assertFalse(status["raster_valid"])
        self.assertIn(
            curate_bridge.REASON_RASTER_SPIKE_BUDGET, status["reason_codes"]
        )

    def test_a_declared_non_array_per_check_container_fails_validation(self):
        for per_check in ("bad", 7, {"neurons": 2}, None):
            with self.subTest(per_check=per_check):
                record = gate_snn_fixture()
                record["gate_compute"] = {"per_check": per_check}

                status = curate_bridge.raster_status(record)

                self.assertFalse(status["raster_valid"])
                self.assertIn(
                    curate_bridge.REASON_RASTER_SPIKE_BUDGET,
                    status["reason_codes"],
                )

    def test_an_absent_per_check_block_stays_optional(self):
        record = gate_snn_fixture()
        record["gate_compute"] = {}

        status = curate_bridge.raster_status(record)

        self.assertTrue(status["raster_valid"])

    def test_negative_declared_raster_energy_is_rejected_inside_tolerance(self):
        for key, value in (("energy_pJ", -5e-7), ("energy_uJ", -5e-10)):
            with self.subTest(key=key):
                record = zero_spike_record()
                record["raster"][key] = value

                status = curate_bridge.raster_status(record)

                self.assertFalse(status["raster_valid"])
                self.assertIn(
                    curate_bridge.REASON_RASTER_ENERGY, status["reason_codes"]
                )

    def test_negative_declared_gate_compute_totals_are_rejected(self):
        for key, value in (("total_energy_pJ", -5e-7), ("total_energy_uJ", -5e-10)):
            with self.subTest(key=key):
                record = gate_snn_fixture()
                record["gate_compute"] = {
                    "per_check": [
                        {
                            "neurons": 1,
                            "mean_rate_hz": 1.0,
                            "window_s": 0.02,
                            "spikes": 0,
                        }
                    ],
                    key: value,
                }

                status = curate_bridge.raster_status(record)

                self.assertFalse(status["raster_valid"])
                self.assertIn(
                    curate_bridge.REASON_RASTER_ENERGY, status["reason_codes"]
                )

    def test_zero_energy_on_a_zero_spike_raster_still_validates(self):
        record = zero_spike_record()

        status = curate_bridge.raster_status(record)

        self.assertTrue(status["raster_valid"])


if __name__ == "__main__":
    unittest.main()
