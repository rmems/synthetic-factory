#!/usr/bin/env python3
"""Conventional-baseline gate gap tests.

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



import fault_recovery as fr
import moe_router as mr
import router_baseline as rb
from oracle_grounded import distill_contract as oc  # noqa: E402
from distill_gap_test_support import clone, rehash  # noqa: E402

class BaselineGaps(unittest.TestCase):
    """router_baseline.py"""

    def test_records_without_a_valid_id_are_skipped_not_keyed_as_none(self):
        # str(None) used to give every id-less record the literal id "None",
        # so they all hashed into one train/test bucket.
        records = mr.build_records(11, 4)
        broken = clone(records[0])
        del broken["id"]
        samples = rb.dataset_from_records([broken] + records[1:])
        self.assertEqual(len(samples), len(records) - 1)
        self.assertNotIn("None", {sample.record_id for sample in samples})

    def test_duplicate_record_ids_are_refused(self):
        records = mr.build_records(11, 4)
        input_records = records + [clone(records[0])]
        with self.assertRaises(rb.BaselineError):
            rb.dataset_from_records(input_records)

    def test_the_cli_refuses_a_corpus_with_a_tampered_record(self):
        import contextlib
        import io

        records = mr.build_records(11, 30)
        tampered = clone(records[0])
        tampered["result"]["top1_expert"] = (
            int(tampered["result"]["top1_expert"]) + 1
        ) % 8
        rehash(tampered)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "router.jsonl"
            oc.write_jsonl(path, records[1:] + [tampered])
            stderr = io.StringIO()
            with contextlib.redirect_stdout(io.StringIO()):
                with contextlib.redirect_stderr(stderr):
                    exit_code = rb.main(["evaluate", str(path), "--iterations", "5"])
            self.assertEqual(exit_code, 2)
            self.assertIn("not a clean router-family corpus", stderr.getvalue())

    def test_the_cli_refuses_a_non_router_family_record(self):
        import contextlib
        import io

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "mixed.jsonl"
            oc.write_jsonl(path, mr.build_records(11, 10) + fr.build_records(3, 1))
            with contextlib.redirect_stdout(io.StringIO()):
                with contextlib.redirect_stderr(io.StringIO()):
                    exit_code = rb.main(["evaluate", str(path), "--iterations", "5"])
            self.assertEqual(exit_code, 2)

    def test_a_linear_verdict_must_beat_the_best_baseline(self):
        # The MLP can lead the linear model without clearing nonlinear_margin.
        # Reporting the lower logistic accuracy would let an SNN "pass" while
        # losing to a baseline that was already run.
        report = {
            "verdict": rb.VERDICT_LINEAR,
            "baselines": {
                "logistic_regression": {"model": "logistic_regression", "accuracy": 0.80},
                "mlp": {"model": "mlp", "accuracy": 0.84},
            },
            "best": {"model": "mlp", "accuracy": 0.84},
        }
        gate = rb.escalation_gate(report)
        self.assertTrue(gate["escalate_to_snn"])
        self.assertEqual(gate["must_beat"], 0.84)




class FourthRoundBaselineGaps(unittest.TestCase):
    """router_baseline.py — the fourth review pass."""

    def test_iteration_counts_must_be_positive_integers(self):
        # `--iterations 0` trained neither advertised baseline yet still
        # published their initial predictions into the escalation gate.
        for kwargs in (
            {"logistic_iterations": 0},
            {"mlp_iterations": -3},
            {"logistic_iterations": True},
        ):
            with self.subTest(**kwargs):
                with self.assertRaises(rb.BaselineError) as caught:
                    rb.evaluate_baselines([], **kwargs)
                self.assertIn("positive integer", str(caught.exception))




