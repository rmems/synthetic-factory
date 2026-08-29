#!/usr/bin/env python3
"""Tests for the MoE-router distillation family and its oracle boundary."""

import contextlib
import io
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

import moe_router as mr  # noqa: E402
import oracle_contract as oc  # noqa: E402


# A model id no checkpoint will ever have. Recordings built in these tests
# exercise the replay plumbing; their routing numbers are the reference
# router's own real computation, and no such recording is ever committed.
PLUMBING_TEACHER = "unit-test/not-a-real-moe-checkpoint"


def recording_from_reference(
    texts, *, model=PLUMBING_TEACHER, is_llm_teacher=True, run_id="r1"
):
    """Build a replay recording from routing the reference oracle really did.

    The observations are the reference router's own computed output — no
    routing decision is invented. ``model`` and ``is_llm_teacher`` describe
    what the recording *claims* to be, which is what the laundering guards in
    ``RecordedTeacherRouter.available`` are there to inspect.
    """

    reference = mr.ReferenceMoERouter()
    observations = {}
    for text in texts:
        observation = reference.route(text)
        observations[mr.RecordedTeacherRouter.key_for(text)] = observation.as_dict()
    return {
        "run_id": run_id,
        "recorded_at": "2026-08-23T00:00:00Z",
        "teacher": {
            "is_llm_teacher": is_llm_teacher,
            "model": model,
            "revision_or_checkpoint": "rev-abc123",
            "configuration_sha256": reference.fingerprint()["configuration_sha256"],
        },
        "observations": observations,
    }


class Featurisation(unittest.TestCase):
    def test_features_are_stable_across_processes(self):
        # Bucketing comes from BLAKE2b, not Python's randomised hash(). Two
        # calls in one interpreter would agree either way, so this really has
        # to cross a process boundary with hash randomisation left on.
        import os
        import subprocess

        script = (
            "import sys, json;"
            f"sys.path.insert(0, {str(REPO / 'pipelines')!r});"
            "import moe_router;"
            "print(json.dumps(moe_router.featurize('relay gate')))"
        )
        environment = dict(os.environ)
        environment.pop("PYTHONHASHSEED", None)
        outputs = set()
        for _ in range(2):
            completed = subprocess.run(
                [sys.executable, "-c", script],
                capture_output=True,
                text=True,
                check=True,
                env=environment,
            )
            outputs.add(completed.stdout.strip())
        self.assertEqual(len(outputs), 1)
        self.assertEqual(json.loads(outputs.pop()), mr.featurize("relay gate"))
        self.assertEqual(len(mr.featurize("relay gate")), mr.FEATURE_DIM)

    def test_features_are_unit_norm(self):
        features = mr.featurize("a spike burst arrived late")
        self.assertAlmostEqual(math.sqrt(sum(v * v for v in features)), 1.0, places=6)

    def test_different_text_gives_different_features(self):
        self.assertNotEqual(mr.featurize("alpha"), mr.featurize("beta"))

    def test_compact_view_is_lossy(self):
        features = mr.featurize("the relay gate held")
        compact = mr.compact_view(features)
        self.assertEqual(len(compact), mr.COMPACT_DIM + 4)
        self.assertLess(len(compact), len(features))

    def test_tiny_dim_is_refused(self):
        with self.assertRaises(oc.ContractError):
            mr.featurize("x", dim=2)

    def test_entropy_of_a_uniform_distribution_is_log_n(self):
        uniform = [0.25] * 4
        self.assertAlmostEqual(mr.entropy_nats(uniform), math.log(4), places=9)


class ReferenceRouter(unittest.TestCase):
    def setUp(self):
        self.router = mr.ReferenceMoERouter()

    def test_it_is_never_authoritative(self):
        self.assertEqual(self.router.authority, oc.AUTHORITY_REFERENCE_ONLY)
        self.assertFalse(self.router.is_llm_teacher)
        self.assertFalse(self.router.fingerprint()["is_llm_teacher"])

    def test_routing_is_deterministic(self):
        first = self.router.route("select the expert").as_dict()
        second = mr.ReferenceMoERouter().route("select the expert").as_dict()
        self.assertEqual(first, second)

    def test_a_different_gate_seed_routes_differently(self):
        other = mr.ReferenceMoERouter(seed=999)
        texts = [f"context number {index}" for index in range(20)]
        mine = [self.router.route(text).top1_expert for text in texts]
        theirs = [other.route(text).top1_expert for text in texts]
        self.assertNotEqual(mine, theirs)

    def test_top_k_matches_the_logit_ordering(self):
        observation = self.router.route("route this context")
        for layer in observation.layers:
            order = sorted(
                range(len(layer.router_logits)),
                key=lambda e: (-layer.router_logits[e], e),
            )
            self.assertEqual(list(layer.top_k_experts), order[: len(layer.top_k_experts)])

    def test_margin_is_non_negative_and_entropy_is_bounded(self):
        observation = self.router.route("bounded entropy check")
        for layer in observation.layers:
            self.assertGreaterEqual(layer.top1_top2_margin, 0.0)
            self.assertGreaterEqual(layer.routing_entropy, 0.0)
            self.assertLessEqual(
                layer.routing_entropy, math.log(self.router.num_experts) + 1e-6
            )

    def test_expert_agreement_is_a_fraction_of_layers(self):
        observation = self.router.route("agreement check")
        self.assertGreaterEqual(observation.expert_agreement, 1.0 / len(observation.layers))
        self.assertLessEqual(observation.expert_agreement, 1.0)

    def test_configuration_is_refused_when_top_k_cannot_define_a_margin(self):
        with self.assertRaises(oc.ContractError):
            mr.ReferenceMoERouter(top_k=1)
        with self.assertRaises(oc.ContractError):
            mr.ReferenceMoERouter(num_experts=2, top_k=2)


class RecordedTeacher(unittest.TestCase):
    def test_replay_returns_the_recorded_routing(self):
        text = "replayed context"
        oracle = mr.RecordedTeacherRouter(recording_from_reference([text]))
        self.assertTrue(oracle.available()[0])
        replayed = oracle.route(text).as_dict()
        self.assertEqual(replayed, mr.ReferenceMoERouter().route(text).as_dict())

    def test_unknown_context_fails_closed(self):
        oracle = mr.RecordedTeacherRouter(recording_from_reference(["known"]))
        with self.assertRaises(oc.OracleUnavailable):
            oracle.route("never recorded")

    def test_a_recording_without_a_teacher_identity_is_unavailable(self):
        recording = recording_from_reference(["x"])
        del recording["teacher"]["configuration_sha256"]
        oracle = mr.RecordedTeacherRouter(recording)
        available, detail = oracle.available()
        self.assertFalse(available)
        self.assertIn("configuration_sha256", detail)

    def test_a_recording_of_the_reference_stand_in_cannot_pose_as_a_teacher(self):
        # The laundering route: record the reference gate's real output, label
        # it a teacher, and it would become curatable teacher truth.
        recording = recording_from_reference(
            ["laundered"], model="reference_moe_router", is_llm_teacher=True
        )
        available, detail = mr.RecordedTeacherRouter(recording).available()
        self.assertFalse(available)
        self.assertIn("non-teacher stand-in", detail)

    def test_a_recording_that_does_not_declare_a_teacher_is_unavailable(self):
        recording = recording_from_reference(["quiet"], is_llm_teacher=False)
        available, detail = mr.RecordedTeacherRouter(recording).available()
        self.assertFalse(available)
        self.assertIn("is_llm_teacher", detail)

    def test_a_recording_that_omits_is_llm_teacher_is_not_assumed_to_be_one(self):
        recording = recording_from_reference(["silent"])
        del recording["teacher"]["is_llm_teacher"]
        oracle = mr.RecordedTeacherRouter(recording)
        self.assertFalse(oracle.is_llm_teacher)
        self.assertFalse(oracle.available()[0])

    def test_an_empty_recording_is_unavailable(self):
        oracle = mr.RecordedTeacherRouter(
            {"teacher": {"model": "m", "revision_or_checkpoint": "r",
                         "configuration_sha256": "s"}, "observations": {}}
        )
        self.assertFalse(oracle.available()[0])

    def test_recording_from_a_path_round_trips(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "recording.json"
            path.write_text(json.dumps(recording_from_reference(["from disk"])))
            oracle = mr.RecordedTeacherRouter.from_path(path)
            self.assertTrue(oracle.available()[0])
            self.assertTrue(oracle.route("from disk").layers)


class RealTeacherIsAbsentNotFaked(unittest.TestCase):
    def test_transformers_oracle_reports_why_it_cannot_run(self):
        oracle = mr.TransformersMoERouter("some/moe-model")
        available, detail = oracle.available()
        self.assertTrue(detail)
        if available:
            self.skipTest(
                "torch and transformers import on this host; the interesting "
                "case is the unavailable one"
            )
        self.assertRegex(detail, r"Error|No module|error")

    def test_fingerprint_is_refused_before_the_model_loads(self):
        with self.assertRaises(oc.OracleUnavailable):
            mr.TransformersMoERouter("some/moe-model").fingerprint()

    def test_build_records_refuses_an_unavailable_oracle(self):
        class DeadOracle(mr.RouterOracle):
            name = "dead"

            def available(self):
                return False, "not here"

        with self.assertRaises(oc.OracleUnavailable):
            mr.build_records(1, 1, oracle=DeadOracle())

    def test_oracles_report_lists_the_teacher_and_the_stand_in(self):
        report = mr.oracles_report()
        by_name = {entry["name"]: entry for entry in report["oracles"]}
        self.assertIn("transformers_moe_router", by_name)
        self.assertTrue(by_name["transformers_moe_router"]["is_llm_teacher"])
        self.assertFalse(by_name["reference_moe_router"]["is_llm_teacher"])
        self.assertEqual(
            by_name["reference_moe_router"]["authority"], oc.AUTHORITY_REFERENCE_ONLY
        )


class Records(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = mr.build_records(11, 20)

    def test_records_pass_the_envelope_and_family_checks(self):
        for record in self.records:
            where = record["id"]
            self.assertEqual(oc.check_envelope(record, where), [])
            self.assertEqual(oc.check_digest(record, where), [])
            self.assertEqual(mr.check_family(record, where), [])

    def test_reference_records_are_never_curation_eligible(self):
        for record in self.records:
            eligible, reasons = oc.curation_eligible(record, [])
            self.assertFalse(eligible)
            self.assertIn("ORACLE_NOT_AUTHORITATIVE:'reference_only'", reasons)

    def test_reference_records_are_not_teacher_grounded(self):
        for record in self.records:
            self.assertFalse(record["result"]["teacher_grounded"])
            self.assertFalse(record["result"]["is_llm_teacher"])

    def test_teacher_identity_is_recorded_on_every_record(self):
        for record in self.records:
            fingerprint = record["oracle"]["fingerprint"]
            for field in ("model", "revision_or_checkpoint", "configuration_sha256"):
                self.assertTrue(fingerprint[field])

    def test_compact_input_is_generator_owned_and_present(self):
        for record in self.records:
            compact = record["scenario"]["compact_input"]
            self.assertEqual(len(compact["features"]), mr.COMPACT_DIM + 4)
            self.assertEqual(oc.check_generator_oracle_separation(record, "x"), [])

    def test_contexts_span_several_domains(self):
        domains = {record["scenario"]["domain"] for record in self.records}
        self.assertGreaterEqual(len(domains), 5)

    def test_many_seeds_produce_no_contract_findings(self):
        for seed in range(1, 8):
            for record in mr.build_records(seed, 10):
                where = record["id"]
                self.assertEqual(oc.check_envelope(record, where), [])
                self.assertEqual(mr.check_family(record, where), [])

    def test_a_recorded_teacher_oracle_produces_teacher_grounded_records(self):
        texts = [
            proposal["scenario"]["context"] for proposal in mr.propose_contexts(11, 5)
        ]
        oracle = mr.RecordedTeacherRouter(recording_from_reference(texts))
        records = mr.build_records(11, 5, oracle=oracle)
        for record in records:
            self.assertEqual(mr.check_family(record, record["id"]), [])
            self.assertTrue(record["result"]["teacher_grounded"])
            self.assertEqual(oc.curation_eligible(record, []), (True, []))

    def test_a_fabricated_top1_expert_is_caught(self):
        record = dict(self.records[0])
        record = json.loads(json.dumps(record))
        layers = record["result"]["routing"]["layers"]
        wrong = (layers[-1]["top_k_experts"][0] + 3) % 8
        record["result"]["top1_expert"] = wrong
        record["result"]["routing"]["top1_expert"] = wrong
        errors = mr.check_family(record, "x")
        self.assertTrue(any("top1_expert" in error for error in errors))

    def test_a_fabricated_expert_agreement_is_caught(self):
        record = json.loads(json.dumps(self.records[0]))
        record["result"]["routing"]["expert_agreement"] = 1.0
        errors = mr.check_family(record, "x")
        self.assertTrue(any("expert_agreement" in error for error in errors))

    def test_a_measurement_that_contradicts_the_routing_is_caught(self):
        record = json.loads(json.dumps(self.records[0]))
        for item in record["result"]["measurements"]:
            if item["quantity"] == "routing_entropy":
                item["value"] = item["value"] + 0.5
        errors = mr.check_family(record, "x")
        self.assertTrue(
            any("recorded routing says" in error for error in errors)
        )


class FamilyChecks(unittest.TestCase):
    def setUp(self):
        self.record = mr.build_records(3, 1)[0]

    def test_a_tampered_context_hash_is_rejected(self):
        self.record["scenario"]["context"] = "something else entirely"
        errors = mr.check_family(self.record, "x")
        self.assertTrue(any("context_sha256" in error for error in errors))

    def test_compact_features_must_be_usable_by_the_baseline(self):
        # router_baseline silently skips a record whose features are not finite
        # numbers, so a curated corpus could otherwise hold no student input.
        for bad in ([], ["not", "numbers"], [1.0, float("nan")]):
            with self.subTest(features=bad):
                record = json.loads(json.dumps(self.record))
                record["scenario"]["compact_input"]["features"] = bad
                self.assertTrue(mr.check_family(record, "x"))

    def test_compact_features_must_match_the_declared_width(self):
        self.record["scenario"]["compact_input"]["features"].pop()
        errors = mr.check_family(self.record, "x")
        self.assertTrue(any("compact_dim" in error for error in errors))

    def test_expert_ids_are_range_checked_without_logits(self):
        # A recorded teacher may legitimately omit logits; the ids still have
        # to be real experts.
        for bogus in ([-1, 2], [0, 999], ["a", "b"]):
            with self.subTest(experts=bogus):
                record = json.loads(json.dumps(self.record))
                for layer in record["result"]["routing"]["layers"]:
                    layer["router_logits"] = None
                    layer["top_k_experts"] = bogus
                self.assertTrue(mr.check_family(record, "x"))

    def test_missing_teacher_fingerprint_is_rejected(self):
        del self.record["oracle"]["fingerprint"]
        errors = mr.check_family(self.record, "x")
        self.assertTrue(any("fingerprint" in error for error in errors))

    def test_a_blank_checkpoint_is_rejected(self):
        self.record["oracle"]["fingerprint"]["revision_or_checkpoint"] = ""
        errors = mr.check_family(self.record, "x")
        self.assertTrue(
            any("revision_or_checkpoint" in error for error in errors)
        )

    def test_claiming_a_teacher_the_oracle_is_not_is_rejected(self):
        self.record["result"]["is_llm_teacher"] = True
        errors = mr.check_family(self.record, "x")
        self.assertTrue(
            any("disagrees with the oracle fingerprint" in error for error in errors)
        )

    def test_claiming_teacher_grounding_from_a_reference_oracle_is_rejected(self):
        self.record["result"]["teacher_grounded"] = True
        errors = mr.check_family(self.record, "x")
        self.assertTrue(any("teacher_grounded" in error for error in errors))

    def test_top_k_that_contradicts_the_logits_is_rejected(self):
        layer = self.record["result"]["routing"]["layers"][0]
        layer["top_k_experts"] = list(reversed(layer["top_k_experts"]))
        errors = mr.check_family(self.record, "x")
        self.assertTrue(
            any("disagrees with router_logits" in error for error in errors)
        )

    def test_repeated_experts_are_rejected(self):
        layer = self.record["result"]["routing"]["layers"][0]
        layer["top_k_experts"] = [layer["top_k_experts"][0]] * 2
        errors = mr.check_family(self.record, "x")
        self.assertTrue(any("must not repeat an expert" in error for error in errors))

    def test_impossible_entropy_is_rejected(self):
        # With logits exposed the entropy is recomputed from them rather than
        # merely bounded by ln(num_experts), so the rejection is exact. The
        # ln() bound still covers the no-logits path in the next test.
        layer = self.record["result"]["routing"]["layers"][0]
        layer["routing_entropy"] = 99.0
        errors = mr.check_family(self.record, "x")
        self.assertTrue(
            any(
                "routing_entropy is 99.0" in error and "router_logits give" in error
                for error in errors
            ),
            errors,
        )

    def test_impossible_entropy_is_rejected_without_logits(self):
        # An oracle that exposes no logits still cannot report an entropy that
        # no distribution over its recorded expert count could produce.
        layer = self.record["result"]["routing"]["layers"][0]
        layer["router_logits"] = None
        layer["routing_entropy"] = 99.0
        errors = mr.check_family(self.record, "x")
        self.assertTrue(any("exceeds ln(" in error for error in errors))

    def test_a_plausible_entropy_without_logits_is_accepted(self):
        layer = self.record["result"]["routing"]["layers"][0]
        layer["router_logits"] = None
        layer["routing_entropy"] = 1.0
        self.assertEqual(mr.check_family(self.record, "x"), [])

    def test_negative_margin_is_rejected(self):
        layer = self.record["result"]["routing"]["layers"][0]
        layer["top1_top2_margin"] = -0.5
        errors = mr.check_family(self.record, "x")
        self.assertTrue(any("top1_top2_margin" in error for error in errors))

    def test_duplicate_layer_indices_are_rejected(self):
        layers = self.record["result"]["routing"]["layers"]
        layers[1]["layer"] = layers[0]["layer"]
        errors = mr.check_family(self.record, "x")
        self.assertTrue(any("is duplicated" in error for error in errors))

    def test_out_of_range_agreement_is_rejected(self):
        self.record["result"]["routing"]["expert_agreement"] = 1.5
        errors = mr.check_family(self.record, "x")
        self.assertTrue(any("expert_agreement" in error for error in errors))


class Cli(unittest.TestCase):
    def test_oracles_subcommand_emits_json(self):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            self.assertEqual(mr.main(["oracles"]), 0)
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload["family"], mr.FAMILY)

    def test_generate_writes_jsonl(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "batch.jsonl"
            with contextlib.redirect_stdout(io.StringIO()):
                exit_code = mr.main(
                    ["generate", "--seed", "5", "--count", "4", "--output", str(out)]
                )
            self.assertEqual(exit_code, 0)
            self.assertEqual(len(oc.read_jsonl(out)), 4)


if __name__ == "__main__":
    unittest.main()
