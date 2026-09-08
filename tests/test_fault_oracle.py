#!/usr/bin/env python3
"""Direct tests of ``fault_oracle``: record assembly through the contract,
the closed label surface, measurement conventions, ``produced_at`` pinning
and byte identity, meter provenance and oracle injection, the JSONL round
trip and ``describe()``."""

import copy
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fault_test_support import (
    PINNED_AT,
    SEED,
    contract_findings,
    ensure_policy,
    envelope,
    fault_oracle as fo,
    fault_scenario,
    fault_simulator,
    fault_vocabulary as fv,
    oc,
    records,
    refusal,
)


def measurements_of(record):
    return {item["quantity"]: item for item in record["result"]["measurements"]}


class BenchReplay(fault_simulator.RelayReflexSimulator):
    meter_clock = "bench_replay_clock"
    meter_state = "bench_replay_state"
    meter_thermal = "bench_replay_thermal_probe"


class ReferenceOnly(fault_simulator.RelayReflexSimulator):
    authority = oc.AUTHORITY_REFERENCE_ONLY


class RecordCorpus(unittest.TestCase):
    def setUp(self):
        ensure_policy()

    def test_every_record_passes_the_contract_and_is_curation_eligible(self):
        corpus = records()
        self.assertEqual(len(corpus), 36)
        for record in corpus:
            with self.subTest(record=record["id"]):
                self.assertEqual(contract_findings(record), [])
                self.assertEqual(oc.curation_eligible(record, []), (True, []))
        self.assertEqual(oc.curation_eligible(corpus[0], ["x"]), (False, ["VALIDATION_FINDINGS:1"]))
        for seed in range(1, 11):
            self.assertEqual([contract_findings(r) for r in records(seed, 9)], [[]] * 9)

    def test_ids_stamps_outcomes_and_agreement(self):
        corpus = records()
        self.assertEqual([r["id"] for r in corpus][:2], ["fr-20260823-0000", "fr-20260823-0001"])
        self.assertEqual(len({r["id"] for r in corpus}), 36)
        self.assertEqual({r["result"]["outcome"] for r in corpus}, set(fv.OUTCOMES))
        for record in corpus:
            self.assertEqual(record["validation"], oc.unvalidated())
            self.assertEqual((record["generator"]["seed"], record["generator"]["authority"]), (SEED, "propose_only"))
        agreement = {r["result"]["prediction_agreement"] for r in corpus}
        self.assertEqual(agreement, {"agree", "disagree"})
        for record in corpus:
            expected = record["candidate_prediction"]["predicted_outcome"] == record["result"]["outcome"]
            self.assertEqual(record["result"]["prediction_agreement"] == "agree", expected)

    def test_the_label_surface_is_closed(self):
        for record in records():
            result = record["result"]
            with self.subTest(record=record["id"]):
                surface = (set(result) - {"status", "measurements"}) | set(result["trace_summary"])
                self.assertEqual(surface, fv.ORACLE_LABEL_KEYS)
                self.assertEqual(set(result["trace_summary"]), fv.TRACE_SUMMARY_KEYS)
                quantities = [m["quantity"] for m in result["measurements"]]
                if result["outcome"] == "continue":
                    self.assertIsNone(result["detection_latency_ms"])
                    self.assertEqual(len(quantities), 6)
                else:
                    self.assertEqual((len(quantities), quantities[0]), (7, "detection_latency_ms"))


class MeasurementConventions(unittest.TestCase):
    def test_counts_are_genuine_integers_and_ratios_six_places(self):
        for record in records():
            readings = measurements_of(record)
            with self.subTest(record=record["id"]):
                for count in ("healthy_channel_count", "dropped_event_count"):
                    self.assertIsInstance(readings[count]["value"], int)
                    self.assertNotIn(".", oc.canonical_json(readings[count]["value"]))
                for ratio in ("residual_error", "corrupt_ratio"):
                    self.assertEqual(round(readings[ratio]["value"], 6), readings[ratio]["value"])
                self.assertGreaterEqual(readings["recovery_latency_ms"]["value"], 0.0)
                self.assertEqual(readings["healthy_channel_count"]["detail"], {"worst_case_over_run": True})

    def test_meters_follow_the_roles_and_the_requested_ratio_is_kind_specific(self):
        meters = {"clock": fv.METER_CLOCK, "state": fv.METER_STATE, "thermal": fv.METER_THERMAL}
        for record in records():
            readings = measurements_of(record)
            with self.subTest(record=record["id"]):
                for quantity, item in readings.items():
                    self.assertEqual(item["meter"], meters[fv.QUANTITY_METER_ROLES[quantity]])
                requested = readings["corrupt_ratio"].get("detail")
                if record["intervention"]["kind"] == "burst_corruption":
                    self.assertEqual(requested, {"requested": record["intervention"]["parameters"]["corrupt_ratio"]})
                else:
                    self.assertIsNone(requested)


class Reproducibility(unittest.TestCase):
    def test_a_pinned_produced_at_makes_two_builds_byte_identical(self):
        first = fo.build_records(SEED, 18, produced_at=PINNED_AT)
        second = fo.build_records(SEED, 18, produced_at=PINNED_AT)
        self.assertEqual([oc.canonical_json(r) for r in first], [oc.canonical_json(r) for r in second])
        self.assertEqual(first[0]["provenance"]["produced_at"], PINNED_AT)
        later = fo.build_records(SEED, 18, produced_at="2026-08-24T00:00:00.000Z")
        for before, after in zip(first, later):
            self.assertNotEqual(before["provenance"]["record_sha256"], after["provenance"]["record_sha256"])

    def test_unpinned_builds_differ_only_in_the_stamp_and_the_digest(self):
        first, second = fo.build_records(SEED, 2), fo.build_records(SEED, 2)
        for before, after in zip(first, second):
            self.assertTrue(envelope.ISO_8601_RE.match(before["provenance"]["produced_at"]))
            for record in (before, after):
                record["provenance"].pop("produced_at")
                record["provenance"].pop("record_sha256")
            self.assertEqual(before, after)

    def test_a_produced_at_that_is_not_an_instant_is_refused_up_front(self):
        for stamp in ("2026-02-30T00:00:00Z", "yesterday", 5):
            with self.subTest(stamp=stamp), refusal(self, fv.FINDING_PRODUCED_AT_NOT_A_TIMESTAMP, "produced_at"):
                fo.build_records(SEED, 1, produced_at=stamp)


class OracleInjection(unittest.TestCase):
    def test_an_injected_oracle_keeps_its_own_meters(self):
        for record in fo.build_records(3, 9, produced_at=PINNED_AT, oracle=BenchReplay()):
            meters = {item["meter"] for item in record["result"]["measurements"]}
            self.assertEqual(meters, {"bench_replay_clock", "bench_replay_state", "bench_replay_thermal_probe"})

    def test_an_oracle_without_meters_is_refused(self):
        with refusal(self, fv.FINDING_ORACLE_METERS_UNDECLARED, "measurement meters", "clock", "state", "thermal"):
            fo.build_records(3, 1, oracle=fo.FaultOracle())

    def test_a_reference_only_oracle_is_refused_by_the_curation_gate_not_by_f1(self):
        ensure_policy()
        record = fo.build_records(3, 1, produced_at=PINNED_AT, oracle=ReferenceOnly())[0]
        self.assertEqual(contract_findings(record), [])
        eligible, reasons = oc.curation_eligible(record, [])
        self.assertFalse(eligible)
        self.assertTrue(reasons[0].startswith("ORACLE_NOT_AUTHORITATIVE"), reasons)


class JsonlRoundTrip(unittest.TestCase):
    def test_write_read_and_the_writer_refusals(self):
        corpus = copy.deepcopy(records(SEED, 4))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "batch-r01.jsonl"
            self.assertEqual(oc.write_jsonl(path, corpus), 4)
            read = [record for _, record in oc.read_jsonl(path)]
            self.assertEqual([oc.canonical_json(r) for r in read], [oc.canonical_json(r) for r in corpus])
            with self.assertRaises(oc.ContractError):
                oc.write_jsonl(path, corpus)
            raw = Path(tmp) / "outputs" / "raw" / "new-run" / "batch-r01.jsonl"
            with self.assertRaises(oc.ContractError):
                oc.write_jsonl(raw, corpus)
            self.assertFalse((Path(tmp) / "outputs").exists())


class Identity(unittest.TestCase):
    def test_provenance_and_oracle_literals_and_re_exports(self):
        record = records()[0]
        self.assertEqual(record["provenance"]["producer"], fv.PRODUCER)
        self.assertEqual(record["provenance"]["oracle_run"], fv.ORACLE_RUN)
        self.assertEqual(record["oracle"]["implementation"], fv.ORACLE_IMPLEMENTATION)
        self.assertIs(fo.RelayReflexSimulator, fault_simulator.RelayReflexSimulator)
        self.assertIs(fo.propose_scenarios, fault_scenario.propose_scenarios)

    def test_describe_is_plain_canonical_data(self):
        described = fo.describe()
        expected = {
            "family", "schema_version", "disturbances", "outcomes", "outcome_labels", "precedence",
            "reason_codes", "finding_codes", "oracle_label_keys", "oracle", "generator",
            "default_system", "parameter_spec", "hardware_replay",
        }
        self.assertEqual(set(described), expected)
        self.assertEqual(described["oracle"]["authority"], "authoritative")
        self.assertEqual(described["oracle_label_keys"], sorted(fv.ORACLE_LABEL_KEYS))
        self.assertIn(fv.FAMILY, oc.canonical_json(described))

