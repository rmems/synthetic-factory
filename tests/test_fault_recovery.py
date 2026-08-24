#!/usr/bin/env python3
"""Tests for the fault-recovery generator and its deterministic relay oracle."""

import copy
import sys
import unittest
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

import fault_recovery as fr  # noqa: E402
import oracle_contract as oc  # noqa: E402


def scenario(**system):
    merged = dict(fr.DEFAULT_SYSTEM)
    merged.update(system)
    return {"system": merged, "mission": "unit test"}


def disturbance(kind, **parameters):
    return {"kind": kind, "parameters": parameters}


class VocabularyMatchesTheIssue(unittest.TestCase):
    def test_nine_named_disturbances(self):
        # The nine disturbances written in issue #78, canonicalised to
        # snake_case. Spelled out here so a silent vocabulary drift fails.
        issue_wording = [
            "sensor loss",
            "stale sensor",
            "event jitter",
            "burst corruption",
            "thermal excursion",
            "missing channel",
            "malformed spike burst",
            "delayed result",
            "temporary saturation",
        ]
        self.assertEqual(
            sorted(fr.DISTURBANCES),
            sorted(text.replace(" ", "_") for text in issue_wording),
        )

    def test_six_named_outcomes_keep_their_prose_spelling(self):
        self.assertEqual(
            sorted(fr.OUTCOME_LABELS.values()),
            sorted(
                [
                    "continue",
                    "degrade gracefully",
                    "fallback",
                    "reflex action",
                    "quarantine",
                    "fail closed",
                ]
            ),
        )
        self.assertEqual(sorted(fr.OUTCOMES), sorted(fr.OUTCOME_LABELS))

    def test_precedence_covers_every_outcome_exactly_once(self):
        self.assertEqual(sorted(fr.OUTCOME_PRECEDENCE), sorted(fr.OUTCOMES))
        self.assertEqual(len(set(fr.OUTCOME_PRECEDENCE)), len(fr.OUTCOMES))


class SimulatorRules(unittest.TestCase):
    def setUp(self):
        self.sim = fr.RelayReflexSimulator()

    def test_benign_jitter_continues(self):
        result = self.sim.run(
            scenario(), disturbance("event_jitter", channels=["c0"], jitter_ms=0.4)
        )
        self.assertEqual(result.outcome, "continue")
        self.assertEqual(result.reason_codes, ("WITHIN_TOLERANCE",))

    def test_jitter_beyond_tolerance_degrades(self):
        result = self.sim.run(
            scenario(), disturbance("event_jitter", channels=["c0"], jitter_ms=3.0)
        )
        self.assertEqual(result.outcome, "degrade_gracefully")
        self.assertIn("JITTER_BEYOND_TOLERANCE", result.reason_codes)

    def test_thermal_ladder_walks_warn_limit_shutdown(self):
        ladder = {58.0: "continue", 70.0: "degrade_gracefully",
                  84.0: "reflex_action", 96.0: "fail_closed"}
        for peak, expected in ladder.items():
            with self.subTest(peak=peak):
                result = self.sim.run(
                    scenario(),
                    disturbance(
                        "thermal_excursion", channels=["c0"], onset_ms=2.0,
                        ramp_ms=8.0, peak_c=peak,
                    ),
                )
                self.assertEqual(result.outcome, expected)

    def test_malformed_burst_quarantines(self):
        result = self.sim.run(
            scenario(),
            disturbance(
                "malformed_spike_burst", channels=["c1"], malformed_count=2,
                malformed_kind="negative_amplitude",
            ),
        )
        self.assertEqual(result.outcome, "quarantine")
        self.assertIn("MALFORMED_STREAM_QUARANTINED", result.reason_codes)
        self.assertTrue(result.integrity_violation)

    def test_late_result_past_hard_deadline_fails_closed(self):
        result = self.sim.run(
            scenario(), disturbance("delayed_result", channels=["c0"], delay_ms=44.0)
        )
        self.assertEqual(result.outcome, "fail_closed")
        self.assertIn("NO_TIMELY_INPUT", result.reason_codes)

    def test_late_result_inside_hard_deadline_degrades(self):
        result = self.sim.run(
            scenario(), disturbance("delayed_result", channels=["c0"], delay_ms=18.0)
        )
        self.assertEqual(result.outcome, "degrade_gracefully")
        self.assertIn("RESULT_PAST_DEADLINE", result.reason_codes)
        self.assertGreater(result.recovery_latency_ms, 0.0)

    def test_channel_loss_uses_the_fallback_when_one_exists(self):
        loss = disturbance(
            "sensor_loss", channels=["c0", "c1"], onset_ms=4.0, duration_ms=14.0
        )
        result = self.sim.run(scenario(min_healthy_channels=3), loss)
        self.assertEqual(result.outcome, "fallback")
        self.assertIn("FALLBACK_SOURCE_ENGAGED", result.reason_codes)

    def test_same_loss_fails_closed_without_a_fallback(self):
        loss = disturbance(
            "sensor_loss", channels=["c0", "c1"], onset_ms=4.0, duration_ms=14.0
        )
        result = self.sim.run(
            scenario(min_healthy_channels=3, fallback_source=None), loss
        )
        self.assertEqual(result.outcome, "fail_closed")
        self.assertIn("INSUFFICIENT_HEALTHY_CHANNELS_NO_FALLBACK", result.reason_codes)

    def test_a_fallback_that_is_itself_affected_is_not_usable(self):
        loss = disturbance(
            "sensor_loss",
            channels=["c0", "c1", "relay_b"],
            onset_ms=4.0,
            duration_ms=14.0,
        )
        result = self.sim.run(
            scenario(min_healthy_channels=3, fallback_source="relay_b"), loss
        )
        self.assertEqual(result.outcome, "fail_closed")

    def test_saturation_held_past_the_reflex_window_triggers_a_reflex(self):
        result = self.sim.run(
            scenario(min_healthy_channels=2),
            disturbance(
                "temporary_saturation", channels=["c0"], onset_ms=2.0, duration_ms=16.0
            ),
        )
        self.assertEqual(result.outcome, "reflex_action")
        self.assertIn("SATURATION_REFLEX", result.reason_codes)

    def test_heavy_corruption_quarantines_and_light_corruption_degrades(self):
        heavy = self.sim.run(
            scenario(),
            disturbance(
                "burst_corruption", channels=["c0", "c1"], onset_ms=2.0,
                duration_ms=44.0, corrupt_ratio=0.9,
            ),
        )
        self.assertEqual(heavy.outcome, "quarantine")
        light = self.sim.run(
            scenario(),
            disturbance(
                "burst_corruption", channels=["c0"], onset_ms=2.0,
                duration_ms=8.0, corrupt_ratio=0.2,
            ),
        )
        self.assertEqual(light.outcome, "degrade_gracefully")

    def test_missing_channel_reduces_the_set_but_keeps_running(self):
        result = self.sim.run(
            scenario(min_healthy_channels=3), disturbance("missing_channel", channels=["c3"])
        )
        self.assertEqual(result.outcome, "degrade_gracefully")
        self.assertIn("REDUCED_CHANNEL_SET", result.reason_codes)
        self.assertEqual(result.worst_healthy_channels, 3)

    def test_stale_beyond_threshold_is_detected(self):
        result = self.sim.run(
            scenario(min_healthy_channels=2),
            disturbance("stale_sensor", channels=["c0"], onset_ms=2.0, stale_age_ms=22.0),
        )
        self.assertGreater(
            result.max_staleness_ms, fr.DEFAULT_SYSTEM["stale_threshold_ms"]
        )
        self.assertNotEqual(result.outcome, "continue")

    def test_unknown_disturbance_is_refused(self):
        with self.assertRaises(oc.ContractError):
            self.sim.run(scenario(), disturbance("gremlins"))

    def test_simulator_is_deterministic(self):
        run = disturbance(
            "burst_corruption", channels=["c0"], onset_ms=2.0, duration_ms=20.0,
            corrupt_ratio=0.5,
        )
        first = self.sim.run(scenario(), copy.deepcopy(run))
        second = fr.RelayReflexSimulator().run(scenario(), copy.deepcopy(run))
        self.assertEqual(first, second)


class GeneratorProposesOnly(unittest.TestCase):
    def test_proposals_carry_no_oracle_fields(self):
        for proposal in fr.propose_scenarios(4, 9):
            record = {
                "scenario": proposal["scenario"],
                "intervention": proposal["intervention"],
                "candidate_prediction": proposal["candidate_prediction"],
            }
            self.assertEqual(oc.check_generator_oracle_separation(record, "p"), [])

    def test_prediction_is_shallow_enough_to_disagree(self):
        records = fr.build_records(20260823, 36)
        agreement = Counter(
            record["result"]["prediction_agreement"] for record in records
        )
        self.assertGreater(agreement["disagree"], 0)
        self.assertGreater(agreement["agree"], 0)

    def test_prediction_never_becomes_the_label(self):
        records = fr.build_records(20260823, 18)
        disagreeing = [
            record
            for record in records
            if record["result"]["prediction_agreement"] == "disagree"
        ]
        self.assertTrue(disagreeing)
        for record in disagreeing:
            self.assertNotEqual(
                record["candidate_prediction"]["predicted_outcome"],
                record["result"]["outcome"],
            )

    def test_count_must_be_positive(self):
        with self.assertRaises(oc.ContractError):
            fr.propose_scenarios(1, 0)


class RecordsAreContractual(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = fr.build_records(20260823, 36)

    def test_every_record_passes_envelope_digest_and_family_checks(self):
        for record in self.records:
            where = record["id"]
            self.assertEqual(oc.check_envelope(record, where), [])
            self.assertEqual(oc.check_digest(record, where), [])
            self.assertEqual(fr.check_family(record, where), [])

    def test_every_outcome_in_the_vocabulary_is_reachable(self):
        seen = {record["result"]["outcome"] for record in self.records}
        self.assertEqual(seen, set(fr.OUTCOMES))

    def test_every_record_has_an_explicit_reason(self):
        for record in self.records:
            self.assertTrue(record["result"]["reason_codes"])

    def test_records_are_curation_eligible_once_validated(self):
        stamped = oc.stamp_validation(
            self.records[0], validator="v", version="1", findings=[]
        )
        self.assertEqual(oc.curation_eligible(stamped), (True, []))

    def test_ids_are_unique(self):
        ids = [record["id"] for record in self.records]
        self.assertEqual(len(ids), len(set(ids)))

    def test_many_seeds_produce_no_contract_findings(self):
        # A single seed can pass by luck. Sweep enough scenario shapes that a
        # decision-rule regression has somewhere to show up.
        seen = set()
        for seed in range(1, 11):
            for record in fr.build_records(seed, 9):
                where = record["id"]
                self.assertEqual(oc.check_envelope(record, where), [])
                self.assertEqual(fr.check_family(record, where), [])
                seen.add(record["result"]["outcome"])
        self.assertEqual(seen, set(fr.OUTCOMES))


class FamilyChecks(unittest.TestCase):
    def setUp(self):
        self.record = fr.build_records(3, 1)[0]

    def test_unknown_outcome_is_rejected(self):
        self.record["result"]["outcome"] = "vibe_check"
        self.assertTrue(fr.check_family(self.record, "x"))

    def test_label_must_match_the_canonical_outcome(self):
        self.record["result"]["outcome_label"] = "fail closed"
        self.record["result"]["outcome"] = "continue"
        errors = fr.check_family(self.record, "x")
        self.assertTrue(any("outcome_label" in error for error in errors))

    def test_empty_reason_codes_are_rejected(self):
        self.record["result"]["reason_codes"] = []
        errors = fr.check_family(self.record, "x")
        self.assertTrue(any("reason_codes" in error for error in errors))

    def test_unknown_disturbance_kind_is_rejected(self):
        self.record["intervention"]["kind"] = "gremlins"
        errors = fr.check_family(self.record, "x")
        self.assertTrue(any("intervention.kind" in error for error in errors))

    def test_prediction_outside_the_vocabulary_is_rejected(self):
        self.record["candidate_prediction"]["predicted_outcome"] = "panic"
        errors = fr.check_family(self.record, "x")
        self.assertTrue(any("predicted_outcome" in error for error in errors))


class Cli(unittest.TestCase):
    def test_describe_reports_the_contract(self):
        described = fr.describe()
        self.assertEqual(described["family"], fr.FAMILY)
        self.assertEqual(described["outcomes"], list(fr.OUTCOMES))
        self.assertEqual(described["oracle"]["authority"], oc.AUTHORITY_AUTHORITATIVE)

    def test_generate_writes_jsonl(self):
        import contextlib
        import io
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "batch.jsonl"
            with contextlib.redirect_stdout(io.StringIO()):
                exit_code = fr.main(
                    ["generate", "--seed", "5", "--count", "3", "--output", str(out)]
                )
            self.assertEqual(exit_code, 0)
            self.assertEqual(len(oc.read_jsonl(out)), 3)


if __name__ == "__main__":
    unittest.main()
