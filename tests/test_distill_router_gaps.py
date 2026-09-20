#!/usr/bin/env python3
"""MoE-router family gap tests (tamper-and-recheck regressions).

Split out of ``test_distillation_review_gaps.py``: every test fails against
the code as it stood before the fix it names. The recurring shape is: take a
record the generator produced, tamper with one derived field, recompute
``provenance.record_sha256`` so the digest check is satisfied, and assert the
family checker still objects.
"""

import math
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))



import moe_router as mr  # noqa: E402
import router_baseline as rb  # noqa: E402
import validate_distill as vd  # noqa: E402
from oracle_grounded import distill_contract as oc  # noqa: E402
from distill_gap_test_support import clone, rehash  # noqa: E402

class RouterGaps(unittest.TestCase):
    """moe_router.py"""

    @classmethod
    def setUpClass(cls):
        cls.records = mr.build_records(11, 3, oracle=mr.ReferenceMoERouter())

    def record(self) -> dict:
        return clone(self.records[0])

    def test_an_untampered_router_record_still_validates(self):
        for record in self.records:
            with self.subTest(record=record["id"]):
                self.assertEqual(mr.check_family(record, "x"), [])

    def test_the_margin_is_recomputed_from_the_logits(self):
        record = self.record()
        layer = record["result"]["routing"]["layers"][0]
        self.assertIsInstance(layer.get("router_logits"), list)
        layer["top1_top2_margin"] = float(layer["top1_top2_margin"]) + 0.5
        rehash(record)
        errors = mr.check_family(record, "x")
        self.assertTrue(
            any("top1_top2_margin" in error for error in errors),
            f"a fabricated margin passed: {errors}",
        )

    def test_the_entropy_is_recomputed_from_the_logits(self):
        record = self.record()
        layer = record["result"]["routing"]["layers"][0]
        experts = len(layer["router_logits"])
        # Below ln(num_experts), so only a recomputation catches it.
        layer["routing_entropy"] = round(math.log(experts) * 0.5, 6)
        rehash(record)
        errors = mr.check_family(record, "x")
        self.assertTrue(
            any("routing_entropy" in error for error in errors),
            f"a fabricated entropy passed: {errors}",
        )

    def test_routing_layers_must_be_in_model_order(self):
        record = self.record()
        layers = record["result"]["routing"]["layers"]
        self.assertGreater(len(layers), 1)
        record["result"]["routing"]["layers"] = [layers[-1]] + layers[:-1]
        rehash(record)
        errors = mr.check_family(record, "x")
        self.assertTrue(
            any("model order" in error for error in errors),
            f"out-of-order routing layers passed: {errors}",
        )

    def test_a_malformed_configuration_digest_is_rejected(self):
        record = self.record()
        record["oracle"]["fingerprint"]["configuration_sha256"] = "not-a-digest"
        rehash(record)
        errors = mr.check_family(record, "x")
        self.assertTrue(
            any("configuration_sha256" in error for error in errors),
            f"a malformed configuration digest passed: {errors}",
        )

    def test_a_reference_router_needs_at_least_one_layer(self):
        for num_layers in (0, -1):
            with self.subTest(num_layers=num_layers):
                with self.assertRaises(oc.ContractError):
                    mr.GateShape(num_layers=num_layers)

    def test_a_mutable_teacher_revision_is_refused(self):
        # A branch name is not a checkpoint: the same name can serve different
        # weights tomorrow, and configuration_sha256 only covers the config.
        commit = "a" * 40
        self.assertEqual(mr.resolve_checkpoint(commit, None), commit)
        self.assertEqual(mr.resolve_checkpoint("main", commit), commit)
        with self.assertRaises(oc.OracleUnavailable):
            mr.resolve_checkpoint("main", None)
        with self.assertRaises(oc.OracleUnavailable):
            mr.resolve_checkpoint(None, None)


def _teacher_recording(texts):
    """A replay recording of routing the reference oracle really computed."""

    reference = mr.ReferenceMoERouter()
    return {
        "run_id": "gap-r1",
        "recorded_at": "2026-08-23T00:00:00Z",
        "teacher": {
            "is_llm_teacher": True,
            "model": "unit-test/not-a-real-moe-checkpoint",
            "revision_or_checkpoint": "1234567890abcdef1234567890abcdef12345678",
            "configuration_sha256": reference.fingerprint()["configuration_sha256"],
            "num_local_experts": reference.num_experts,
            "num_experts_per_tok": reference.top_k,
            "num_layers": reference.num_layers,
        },
        "observations": {
            mr.RecordedTeacherRouter.key_for(text): reference.route(text).as_dict()
            for text in texts
        },
    }


class RecordedRouterGaps(unittest.TestCase):
    """moe_router.py: replayed recordings fail closed, ids stay bounded."""

    def _oracle_with_layer(self, layer: dict) -> mr.RecordedTeacherRouter:
        recording = _teacher_recording(["ctx"])
        key = mr.RecordedTeacherRouter.key_for("ctx")
        recording["observations"][key]["layers"][0].update(layer)
        return mr.RecordedTeacherRouter(recording)

    def test_an_empty_top_k_fails_closed_not_with_index_error(self):
        # `_summarise` used to raise IndexError out of the oracle boundary.
        oracle = self._oracle_with_layer({"top_k_experts": []})
        with self.assertRaises(oc.OracleUnavailable):
            oracle.route("ctx")

    def test_recorded_expert_ids_are_not_coerced_case(self):
        # int() quietly turned `true` into 1 and 3.7 into 3, letting invalid
        # expert identifiers into the replayed observation.
        for bogus in ([True, 1], [3.7, 1], ["2", 1]):
            with self.subTest(experts=bogus):
                oracle = self._oracle_with_layer({"top_k_experts": bogus})
                with self.assertRaises(oc.OracleUnavailable):
                    oracle.route("ctx")

    def test_recorded_logits_must_be_finite_numbers(self):
        oracle = self._oracle_with_layer({"router_logits": ["1.0", 2.0]})
        with self.assertRaises(oc.OracleUnavailable):
            oracle.route("ctx")

    def test_a_recording_without_an_expert_count_is_unavailable(self):
        recording = _teacher_recording(["ctx"])
        del recording["teacher"]["num_local_experts"]
        available, detail = mr.RecordedTeacherRouter(recording).available()
        self.assertFalse(available)
        self.assertIn("num_local_experts", detail)

    def test_an_authoritative_record_must_declare_its_expert_count(self):
        # Without a declared count the range check was disabled: a recording
        # with no logits could carry ids like [-1, 999] into curation.
        texts = [
            proposal["scenario"]["context"]
            for proposal in mr.propose_contexts(11, 1)
        ]
        oracle = mr.RecordedTeacherRouter(_teacher_recording(texts))
        record = clone(mr.build_records(11, 1, oracle=oracle)[0])
        self.assertEqual(mr.check_family(record, "x"), [])
        del record["oracle"]["fingerprint"]["num_local_experts"]
        rehash(record)
        errors = mr.check_family(record, "x")
        self.assertTrue(
            any("num_local_experts" in error for error in errors),
            f"an authoritative record without an expert count passed: {errors}",
        )

    def test_a_reference_only_record_needs_no_declared_count(self):
        record = clone(mr.build_records(11, 1)[0])
        del record["oracle"]["fingerprint"]["num_local_experts"]
        rehash(record)
        errors = [
            error
            for error in mr.check_family(record, "x")
            if "num_local_experts" in error
        ]
        self.assertEqual(errors, [])


class RouterRecomputeGaps(unittest.TestCase):
    """moe_router.py: reference-routed records are verified by recomputation."""

    def test_a_result_copied_from_another_context_is_rejected(self):
        # check_record used to verify only internal consistency, so a whole
        # result block copied across rows (with a fresh provenance digest)
        # passed while labelling a context it was never routed for.
        record = clone(mr.build_records(11, 1)[0])
        other = mr.build_records(7, 1)[0]
        record["result"] = other["result"]
        rehash(record)
        errors = mr.check_family(record, "x")
        self.assertTrue(
            any("REFERENCE_RECOMPUTE_MISMATCH" in error for error in errors),
            errors,
        )

    def test_unmodified_reference_records_recompute_cleanly(self):
        for record in mr.build_records(11, 2):
            self.assertEqual(mr.check_family(clone(record), "x"), [])

    def test_unbounded_declared_dimensions_are_refused_not_computed(self):
        record = clone(mr.build_records(11, 1)[0])
        record["oracle"]["configuration"]["feature_dim"] = 10**9
        rehash(record)
        errors = mr.check_family(record, "x")
        self.assertTrue(
            any("recomputable" in error for error in errors),
            errors,
        )

    def test_recorded_teacher_records_are_not_recomputed(self):
        # The deterministic recompute is scoped to the reference
        # implementation; a recorded teacher's routing is intentionally not
        # reproducible here.
        texts = [
            proposal["scenario"]["context"]
            for proposal in mr.propose_contexts(11, 1)
        ]
        oracle = mr.RecordedTeacherRouter(_teacher_recording(texts))
        record = clone(mr.build_records(11, 1, oracle=oracle)[0])
        errors = [
            error
            for error in mr.check_family(record, "x")
            if "REFERENCE_RECOMPUTE_MISMATCH" in error
        ]
        self.assertEqual(errors, [])


class RouterTrajectoryGaps(unittest.TestCase):
    """moe_router.py: checkpoints, widths and trajectories stay bound."""

    @classmethod
    def setUpClass(cls):
        texts = [
            proposal["scenario"]["context"]
            for proposal in mr.propose_contexts(11, 1)
        ]
        oracle = mr.RecordedTeacherRouter(_teacher_recording(texts))
        cls.teacher_record = mr.build_records(11, 1, oracle=oracle)[0]
        cls.reference_record = mr.build_records(11, 1)[0]

    def test_a_mutable_recording_revision_is_refused_at_the_boundary(self):
        recording = _teacher_recording(["ctx"])
        recording["teacher"]["revision_or_checkpoint"] = "main"
        available, detail = mr.RecordedTeacherRouter(recording).available()
        self.assertFalse(available)
        self.assertIn("mutable revision", detail)

    def test_an_authoritative_record_must_pin_an_immutable_checkpoint(self):
        record = clone(self.teacher_record)
        self.assertEqual(mr.check_family(record, "x"), [])
        record["oracle"]["fingerprint"]["revision_or_checkpoint"] = "main"
        rehash(record)
        errors = mr.check_family(record, "x")
        self.assertTrue(
            any("revision_or_checkpoint" in error for error in errors),
            f"a mutable authoritative checkpoint passed: {errors}",
        )

    def test_the_declared_top_k_width_is_enforced(self):
        record = clone(self.teacher_record)
        layer = record["result"]["routing"]["layers"][0]
        logits = layer["router_logits"]
        top3 = sorted(range(len(logits)), key=lambda e: (-logits[e], e))[:3]
        layer["top_k_experts"] = top3
        rehash(record)
        errors = mr.check_family(record, "x")
        self.assertTrue(
            any("num_experts_per_tok" in error for error in errors),
            f"a wider top-k than the teacher declares passed: {errors}",
        )

    def _drop_layers(self, keep: list[int]) -> dict:
        from collections import Counter

        record = clone(self.reference_record)
        layers = [record["result"]["routing"]["layers"][i] for i in keep]
        record["result"]["routing"]["layers"] = layers
        tops = [layer["top_k_experts"][0] for layer in layers]
        modal, count = Counter(tops).most_common(1)[0]
        record["result"]["top1_expert"] = modal
        record["result"]["routing"]["top1_expert"] = modal
        agreement = round(count / len(tops), 6)
        record["result"]["routing"]["expert_agreement"] = agreement
        last = layers[-1]
        for item in record["result"]["measurements"]:
            if item["quantity"] == "top1_top2_margin":
                item["value"] = last["top1_top2_margin"]
                item["detail"]["layer"] = last["layer"]
            if item["quantity"] == "routing_entropy":
                item["value"] = last["routing_entropy"]
                item["detail"]["layer"] = last["layer"]
            if item["quantity"] == "expert_agreement":
                item["value"] = agreement
                item["detail"]["across_layers"] = len(layers)
        return rehash(record)

    def test_a_gapped_layer_trajectory_is_rejected(self):
        record = self._drop_layers([0, 2])
        errors = mr.check_family(record, "x")
        self.assertTrue(
            any("contiguously" in error for error in errors),
            f"a gapped layer trajectory passed: {errors}",
        )

    def test_a_dropped_suffix_is_rejected_when_the_count_is_declared(self):
        record = self._drop_layers([0, 1])
        errors = mr.check_family(record, "x")
        self.assertTrue(
            any("num_layers" in error for error in errors),
            f"a suffix-dropped trajectory passed: {errors}",
        )

    def test_laundering_cannot_hide_behind_a_renamed_fingerprint_model(self):
        # Renaming fingerprint.model used to be enough: the oracle's own
        # name/type/implementation still said reference_moe_router, but only
        # the fingerprint string was checked.
        record = clone(self.reference_record)
        record["oracle"]["authority"] = oc.AUTHORITY_AUTHORITATIVE
        record["oracle"]["fingerprint"]["model"] = "totally-legit-teacher"
        record["oracle"]["fingerprint"]["is_llm_teacher"] = True
        record["oracle"]["fingerprint"]["revision_or_checkpoint"] = "a" * 40
        record["result"]["is_llm_teacher"] = True
        record["result"]["teacher_grounded"] = True
        rehash(record)
        errors = mr.check_family(record, "x")
        self.assertTrue(
            any("LAUNDERED_REFERENCE_ORACLE" in error for error in errors),
            f"a laundered reference oracle passed: {errors}",
        )


class RouterTieBreakGaps(unittest.TestCase):
    """moe_router.py: serialisation rounding must not reject honest top-k."""

    LOGITS = [2.0, 2.0, 1.0, 0.5, 0.4, 0.3, 0.2, 0.1]

    def _layer(self, experts):
        return {
            "layer": 0,
            "top_k_experts": experts,
            "router_logits": list(self.LOGITS),
            "top1_top2_margin": 0.0,
            "routing_entropy": 1.0,
        }

    def test_either_side_of_a_rounded_tie_is_accepted(self):
        # The stored logits are rounded to six places, so a teacher that
        # ordered by full precision can put the higher id first over values
        # that round together; demanding the id-ordered tie-break rejected
        # honest records.
        for experts in ([0, 1], [1, 0]):
            with self.subTest(experts=experts):
                self.assertEqual(
                    mr._check_layer_logits(self._layer(experts), "x"), []
                )

    def test_a_strictly_smaller_logit_still_cannot_be_top_k(self):
        for experts in ([2, 0], [0, 2], [7, 1]):
            with self.subTest(experts=experts):
                self.assertTrue(
                    mr._check_layer_logits(self._layer(experts), "x")
                )

    def test_out_of_range_ids_still_disagree_with_the_logits(self):
        self.assertTrue(mr._check_layer_logits(self._layer([-1, 0]), "x"))


class CompactInputGaps(unittest.TestCase):
    """moe_router.py: the student input must recompute from the context."""

    def setUp(self):
        self.record = clone(mr.build_records(3, 1)[0])

    def test_tampered_compact_features_are_caught(self):
        # Same width, all finite — only recomputation can catch it, and
        # router_baseline would otherwise train on a corrupted input-label
        # pairing.
        features = self.record["scenario"]["compact_input"]["features"]
        features[0] = float(features[0]) + 0.25
        rehash(self.record)
        errors = mr.check_family(self.record, "x")
        self.assertTrue(
            any("COMPACT_INPUT_NOT_REPRODUCIBLE" in error for error in errors),
            f"tampered compact features passed: {errors}",
        )

    def test_an_unknown_featurizer_cannot_dodge_recomputation(self):
        self.record["scenario"]["compact_input"]["featurizer"] = "custom/9.9.9"
        rehash(self.record)
        errors = mr.check_family(self.record, "x")
        self.assertTrue(
            any("featurizer" in error for error in errors),
            f"an unknown featurizer passed: {errors}",
        )

    def test_missing_dims_cannot_dodge_recomputation(self):
        del self.record["scenario"]["compact_input"]["feature_dim"]
        rehash(self.record)
        errors = mr.check_family(self.record, "x")
        self.assertTrue(
            any("feature_dim" in error for error in errors),
            f"a record without a declared feature_dim passed: {errors}",
        )

    def test_an_absurd_feature_dim_is_a_finding_not_an_allocation(self):
        # Recomputation must not be a memory amplifier: a declared dimension
        # of a few billion gets a finding, never a bucket allocation.
        self.record["scenario"]["compact_input"]["feature_dim"] = 10**12
        rehash(self.record)
        errors = mr.check_family(self.record, "x")
        self.assertTrue(
            any("feature_dim" in error for error in errors),
            f"an absurd feature_dim passed: {errors}",
        )




class ThirdRoundRouterGaps(unittest.TestCase):
    """moe_router.py and router_baseline.py — the third review pass."""

    @classmethod
    def setUpClass(cls):
        cls.records = mr.build_records(20260823, 8)

    def test_a_boolean_top1_label_cannot_impersonate_expert_0_or_1(self):
        # False == 0 and True == 1, so a JSON boolean passed the modal
        # equality checks while router_baseline._genuine_int rejected it and
        # silently dropped the sample — a cleanly validating record could
        # skew the baseline by vanishing from it.
        record = next(
            clone(r) for r in self.records if r["result"]["top1_expert"] in (0, 1)
        )
        flag = bool(record["result"]["top1_expert"])
        record["result"]["top1_expert"] = flag
        record["result"]["routing"]["top1_expert"] = flag
        rehash(record)
        errors = mr.check_family(record, "x")
        self.assertEqual(
            sum("genuine integer expert id" in e for e in errors), 2, errors
        )
        self.assertIsNone(rb._target_label(record["result"], rb.TARGET_TOP1))

    def test_promised_router_measurements_cannot_be_dropped(self):
        # The reconciliation loop only validated the readings present, so a
        # record could delete promised compact targets and stay
        # curation-eligible after a rehash.
        for missing in ("routing_entropy", "expert_agreement", "top1_top2_margin"):
            record = clone(self.records[0])
            record["result"]["measurements"] = [
                item
                for item in record["result"]["measurements"]
                if item.get("quantity") != missing
            ]
            rehash(record)
            with self.subTest(missing=missing):
                errors = mr.check_family(record, "x")
                self.assertTrue(
                    any(f"must record {missing}" in e for e in errors),
                    f"dropping {missing} passed: {errors}",
                )

    def test_the_baseline_refuses_an_abstained_router_result(self):
        record = clone(self.records[1])
        record["result"]["status"] = "abstained"
        record["result"]["abstention_reason"] = "teacher unavailable for this batch"
        rehash(record)
        # The record is valid — an oracle may honestly abstain —
        self.assertEqual(vd.check_record(record, "x"), [])
        # — but its routing fields must never become labels ...
        self.assertEqual(rb.dataset_from_records([record]), [])
        # ... and the CLI gate refuses loudly instead of filtering silently.
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "records.jsonl"
            path.write_text(oc.canonical_json(record) + "\n", encoding="utf-8")
            with self.assertRaises(rb.BaselineError) as caught:
                rb._clean_router_records(str(path))
        self.assertIn(
            "only evaluates measured router results", str(caught.exception)
        )

    def test_min_lift_must_be_finite_and_non_negative(self):
        # argparse accepts `--min-lift nan`; NaN survived the max() floor and
        # made every lift comparison false, so a large holdout could emit a
        # learnable verdict no finite threshold would grant.
        for bad in (float("nan"), float("inf"), -0.05):
            with self.subTest(min_lift=bad):
                knobs = rb.EvaluationKnobs(min_lift=bad)
                with self.assertRaises(rb.BaselineError) as caught:
                    rb.evaluate_baselines([], knobs)
                self.assertIn("min_lift", str(caught.exception))




class FourthRoundRouterGaps(unittest.TestCase):
    """moe_router.py — the fourth review pass."""

    @classmethod
    def setUpClass(cls):
        texts = [p["scenario"]["context"] for p in mr.propose_contexts(11, 2)]
        cls.recording = _teacher_recording(texts)
        oracle = mr.RecordedTeacherRouter(cls.recording)
        cls.teacher_records = mr.build_records(11, 2, oracle=oracle)

    def test_an_authoritative_router_must_declare_top_k_and_layers(self):
        # Both equality checks were conditional on the declaration being
        # present, so deleting the field freed the recorded trajectory from
        # the teacher configuration while staying curation-eligible.
        for field in ("num_experts_per_tok", "num_layers"):
            record = clone(self.teacher_records[0])
            del record["oracle"]["fingerprint"][field]
            rehash(record)
            with self.subTest(field=field):
                errors = mr.check_family(record, "x")
                self.assertTrue(
                    any(
                        f"{field} must declare a positive value" in e
                        for e in errors
                    ),
                    f"an authoritative record without {field} passed: {errors}",
                )

    def test_a_reference_only_record_needs_no_declared_widths(self):
        record = clone(mr.build_records(11, 1)[0])
        del record["oracle"]["fingerprint"]["num_experts_per_tok"]
        del record["oracle"]["fingerprint"]["num_layers"]
        rehash(record)
        errors = [
            e
            for e in mr.check_family(record, "x")
            if "must declare a positive value" in e
        ]
        self.assertEqual(errors, [])

    def test_a_recording_without_declared_widths_is_refused(self):
        for field in ("num_experts_per_tok", "num_layers"):
            recording = clone(self.recording)
            del recording["teacher"][field]
            with self.subTest(field=field):
                ok, detail = mr.RecordedTeacherRouter(recording).available()
                self.assertFalse(ok)
                self.assertIn(field, detail)

    def test_truncated_router_logits_are_rejected(self):
        # A shortened array still containing the selected ids passed the
        # ordering check while changing the entropy and logit targets.
        record, index = next(
            (clone(candidate), i)
            for candidate in self.teacher_records
            # Not the last layer: its summaries feed result.measurements.
            for i, lay in enumerate(candidate["result"]["routing"]["layers"][:-1])
            if max(lay["top_k_experts"]) + 1 < len(lay["router_logits"])
        )
        layer = record["result"]["routing"]["layers"][index]
        keep = max(layer["top_k_experts"]) + 1
        layer["router_logits"] = layer["router_logits"][:keep]
        values = [float(v) for v in layer["router_logits"]]
        ordered = sorted(values, reverse=True)
        layer["top1_top2_margin"] = round(ordered[0] - ordered[1], 6)
        layer["routing_entropy"] = round(
            mr.entropy_nats(mr.softmax(values)), 6
        )
        rehash(record)
        errors = mr.check_family(record, "x")
        self.assertTrue(
            any("router_logits lists" in e for e in errors),
            f"a truncated logit distribution passed: {errors}",
        )




class FifthRoundRouterGaps(unittest.TestCase):
    """moe_router.py — fifth pass."""

    @classmethod
    def setUpClass(cls):
        cls.records = mr.build_records(20260823, 2)

    def test_a_promised_target_marked_unmeasured_is_not_reconciled(self):
        # `measured: false` on a promised compact target still counted as
        # reconciled, publishing a modelled value as a grounded router
        # measurement.
        record = clone(self.records[0])
        for item in record["result"]["measurements"]:
            if item["quantity"] == "routing_entropy":
                item["measured"] = False
        rehash(record)
        errors = mr.check_family(record, "x")
        self.assertTrue(
            any(
                "must record routing_entropy as a measured numeric reading" in e
                for e in errors
            ),
            f"an unmeasured promised target passed: {errors}",
        )

    def test_an_unhashable_quantity_is_a_finding_not_a_typeerror(self):
        record = clone(self.records[1])
        record["result"]["measurements"][0]["quantity"] = ["routing_entropy"]
        rehash(record)
        errors = mr.check_family(record, "x")  # must not raise
        self.assertTrue(errors, "a malformed quantity produced no finding")
        self.assertTrue(
            any("unknown quantity" in e for e in vd.check_record(record, "x")),
            "the shared checker no longer flags the malformed item",
        )

    def test_recorded_layer_indices_are_not_coerced(self):
        # int() silently rewrote 0.9 to 0 and True to 1, normalising
        # malformed recording metadata into a validation-clean trajectory.
        for bogus in (0.9, True, "0"):
            recording = _teacher_recording(["ctx"])
            key = mr.RecordedTeacherRouter.key_for("ctx")
            recording["observations"][key]["layers"][0]["layer"] = bogus
            with self.subTest(layer=bogus):
                router = mr.RecordedTeacherRouter(recording)
                with self.assertRaises(oc.OracleUnavailable) as caught:
                    router.route("ctx")
                self.assertIn("genuine integer", str(caught.exception))




class RouterConfigurationGaps(unittest.TestCase):
    """moe_router.py: configuration, fingerprint and compact input agree."""

    @classmethod
    def setUpClass(cls):
        cls.record = mr.build_records(3, 1)[0]

    def test_a_configuration_disagreeing_with_the_fingerprint_is_a_finding(
        self,
    ):
        for key in ("num_experts", "num_layers", "top_k"):
            with self.subTest(key=key):
                record = clone(self.record)
                record["oracle"]["configuration"][key] += 1
                rehash(record)
                errors = mr.check_family(record, "x")
                self.assertTrue(
                    any(f"configuration.{key}" in error for error in errors),
                    f"a {key} drift passed: {errors}",
                )

    def test_a_compact_input_at_the_wrong_width_is_a_finding(self):
        record = clone(self.record)
        record["scenario"]["compact_input"]["feature_dim"] = 8
        rehash(record)
        errors = mr.check_family(record, "x")
        self.assertTrue(
            any("feature_dim" in error for error in errors),
            f"a wrong compact width passed: {errors}",
        )

    def test_a_measurement_attributed_to_the_wrong_layer_is_a_finding(self):
        # top1_top2_margin and routing_entropy summarise the last layer; an
        # honest value attributed to the wrong layer still lies about where
        # in the trajectory it was read.
        record = clone(self.record)
        for item in record["result"]["measurements"]:
            if item["quantity"] == "top1_top2_margin":
                item["detail"]["layer"] = 0
        rehash(record)
        errors = mr.check_family(record, "x")
        self.assertTrue(
            any("attributed to layer" in error for error in errors),
            f"a misattributed last-layer measurement passed: {errors}",
        )

    def test_a_non_default_gate_width_produces_a_matching_compact_input(self):
        record = mr.build_records(
            3, 1, oracle=mr.ReferenceMoERouter(shape=mr.GateShape(dim=8))
        )[0]
        compact = record["scenario"]["compact_input"]
        self.assertEqual(compact["feature_dim"], 8)
        self.assertEqual(mr.check_family(record, "x"), [])




