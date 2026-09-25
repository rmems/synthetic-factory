#!/usr/bin/env python3
"""MoE-router family gap tests (tamper-and-recheck regressions).

Split out of ``test_distillation_review_gaps.py``: every test fails against
the code as it stood before the fix it names. The recurring shape is: take a
record the generator produced, tamper with one derived field, recompute
``provenance.record_sha256`` so the digest check is satisfied, and assert the
family checker still objects.
"""

import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))



import moe_router as mr  # noqa: E402


from oracle_grounded import distill_contract as oc  # noqa: E402
from distill_gap_test_support import clone, rehash, teacher_recording  # noqa: E402


class RecordedRouterGaps(unittest.TestCase):
    """moe_router.py: replayed recordings fail closed, ids stay bounded."""

    def _oracle_with_layer(self, layer: dict) -> mr.RecordedTeacherRouter:
        recording = teacher_recording(["ctx"])
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
        recording = teacher_recording(["ctx"])
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
        oracle = mr.RecordedTeacherRouter(teacher_recording(texts))
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



class RouterTrajectoryGaps(unittest.TestCase):
    """moe_router.py: checkpoints, widths and trajectories stay bound."""

    @classmethod
    def setUpClass(cls):
        texts = [
            proposal["scenario"]["context"]
            for proposal in mr.propose_contexts(11, 1)
        ]
        oracle = mr.RecordedTeacherRouter(teacher_recording(texts))
        cls.teacher_record = mr.build_records(11, 1, oracle=oracle)[0]
        cls.reference_record = mr.build_records(11, 1)[0]

    def test_a_mutable_recording_revision_is_refused_at_the_boundary(self):
        recording = teacher_recording(["ctx"])
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




