#!/usr/bin/env python3
"""MoE-router family gap tests (tamper-and-recheck regressions).

Split out of ``test_distillation_review_gaps.py``: every test fails against
the code as it stood before the fix it names. The recurring shape is: take a
record the generator produced, tamper with one derived field, recompute
``provenance.record_sha256`` so the digest check is satisfied, and assert the
family checker still objects.
"""

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
from distill_gap_test_support import clone, rehash, teacher_recording  # noqa: E402


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
        cls.recording = teacher_recording(texts)
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
            recording = teacher_recording(["ctx"])
            key = mr.RecordedTeacherRouter.key_for("ctx")
            recording["observations"][key]["layers"][0]["layer"] = bogus
            with self.subTest(layer=bogus):
                router = mr.RecordedTeacherRouter(recording)
                with self.assertRaises(oc.OracleUnavailable) as caught:
                    router.route("ctx")
                self.assertIn("genuine integer", str(caught.exception))




