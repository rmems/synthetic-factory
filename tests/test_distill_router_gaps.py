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
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))



import moe_router as mr  # noqa: E402


from oracle_grounded import distill_contract as oc  # noqa: E402
from distill_gap_test_support import clone, rehash, teacher_recording  # noqa: E402


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
        oracle = mr.RecordedTeacherRouter(teacher_recording(texts))
        record = clone(mr.build_records(11, 1, oracle=oracle)[0])
        errors = [
            error
            for error in mr.check_family(record, "x")
            if "REFERENCE_RECOMPUTE_MISMATCH" in error
        ]
        self.assertEqual(errors, [])



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




