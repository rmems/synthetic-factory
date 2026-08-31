#!/usr/bin/env python3
"""Tests for the conventional baselines that gate SNN router distillation."""

import contextlib
import io
import json
import random
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

import moe_router as mr  # noqa: E402
import oracle_contract as oc  # noqa: E402
import router_baseline as rb  # noqa: E402

FAST = {"logistic_iterations": 40, "mlp_iterations": 40, "mlp_hidden": 6}


# The shape of the toy set. No caller has ever varied these three, so they
# are constants rather than parameters -- CodeScene counted five arguments.
SEPARABLE_CLASSES = 3
SEPARABLE_DIM = 6
SEPARABLE_SEED = 5


def separable_samples(count=120, noise=0.0):
    """A linearly separable toy set: one axis per class, plus optional noise."""

    rng = random.Random(SEPARABLE_SEED)
    samples = []
    for index in range(count):
        label = index % SEPARABLE_CLASSES
        features = [
            rng.gauss(0.0, noise) if noise else 0.0 for _ in range(SEPARABLE_DIM)
        ]
        features[label] += 3.0
        samples.append(rb.Sample(f"sep-{index:04d}", tuple(features), label))
    return samples


def random_label_samples(count=120, classes=3, dim=6, seed=9):
    """Features carry no signal about the label: nothing should be learnable."""

    rng = random.Random(seed)
    return [
        rb.Sample(
            f"rand-{index:04d}",
            tuple(rng.gauss(0.0, 1.0) for _ in range(dim)),
            rng.randrange(classes),
        )
        for index in range(count)
    ]


class DatasetExtraction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = mr.build_records(11, 24)

    def test_features_come_from_the_generator_and_labels_from_the_oracle(self):
        samples = rb.dataset_from_records(self.records)
        self.assertEqual(len(samples), len(self.records))
        for sample, record in zip(samples, self.records):
            self.assertEqual(
                list(sample.features), record["scenario"]["compact_input"]["features"]
            )
            self.assertEqual(sample.label, record["result"]["top1_expert"])

    def test_last_layer_target_reads_the_routing_block(self):
        samples = rb.dataset_from_records(
            self.records, target=rb.TARGET_TOP1_LAST_LAYER
        )
        for sample, record in zip(samples, self.records):
            layers = record["result"]["routing"]["layers"]
            self.assertEqual(sample.label, layers[-1]["top_k_experts"][0])

    def test_unknown_target_is_refused(self):
        with self.assertRaises(rb.BaselineError):
            rb.dataset_from_records(self.records, target="vibes")

    def test_records_without_a_compact_input_are_skipped(self):
        records = [dict(record) for record in self.records]
        records[0] = dict(records[0])
        records[0]["scenario"] = {"context": "x"}
        self.assertEqual(len(rb.dataset_from_records(records)), len(records) - 1)

    def test_inconsistent_feature_width_is_refused(self):
        records = [dict(record) for record in self.records[:4]]
        scenario = dict(records[0]["scenario"])
        compact = dict(scenario["compact_input"])
        compact["features"] = compact["features"][:-1]
        scenario["compact_input"] = compact
        records[0] = {**records[0], "scenario": scenario}
        with self.assertRaises(rb.BaselineError):
            rb.dataset_from_records(records)


class Splitting(unittest.TestCase):
    def test_split_is_deterministic_and_input_keyed(self):
        # Keyed on the compact input (not the id): stable under reordering,
        # and identical inputs can never straddle the split — an id-keyed
        # split let duplicated contexts leak labels into the holdout.
        samples = separable_samples()
        first = rb.split(samples)
        shuffled = list(samples)
        random.Random(3).shuffle(shuffled)
        second = rb.split(shuffled)
        self.assertEqual(
            sorted(s.record_id for s in first[1]),
            sorted(s.record_id for s in second[1]),
        )
        twin = rb.Sample(
            record_id="twin-of-first",
            features=samples[0].features,
            label=samples[0].label,
        )
        train, test = rb.split(samples + [twin])
        sides = {
            ("test" if any(s.record_id == rid for s in test) else "train")
            for rid in (samples[0].record_id, "twin-of-first")
        }
        self.assertEqual(len(sides), 1, "identical inputs straddled the split")

    def test_split_covers_every_sample_exactly_once(self):
        samples = separable_samples()
        train, test = rb.split(samples)
        self.assertEqual(len(train) + len(test), len(samples))
        self.assertFalse(
            {s.record_id for s in train} & {s.record_id for s in test}
        )

    def test_out_of_range_holdout_is_refused(self):
        with self.assertRaises(rb.BaselineError):
            rb.split(separable_samples(), holdout_pct=0)

    def test_standardization_is_fitted_on_train_only(self):
        train, test = rb.split(separable_samples())
        scaled_train, _, scaler = rb.standardize(train, test)
        width = len(train[0].features)
        for index in range(width):
            mean = sum(s.features[index] for s in scaled_train) / len(scaled_train)
            self.assertAlmostEqual(mean, 0.0, places=9)
        self.assertEqual(len(scaler["mean"]), width)

    def test_standardizing_an_empty_split_is_refused(self):
        with self.assertRaises(rb.BaselineError):
            rb.standardize([], [])


class Baselines(unittest.TestCase):
    def test_majority_baseline_predicts_the_most_common_label(self):
        samples = [rb.Sample(f"m-{i}", (float(i),), 0 if i < 8 else 1) for i in range(10)]
        train, test = samples[:8], samples[8:]
        report = rb.majority_baseline(train, test)
        self.assertEqual(report["predicts"], 0)

    def test_majority_baseline_refuses_an_empty_split(self):
        with self.assertRaises(rb.BaselineError):
            rb.majority_baseline([], [])

    def test_logistic_regression_learns_a_separable_target(self):
        # Noise makes every sample distinct: with noiseless prototypes each
        # class is one repeated feature vector, so the input-keyed split
        # places the whole class on a single side (identical inputs never
        # straddle) and the old pass was memorisation of duplicated inputs,
        # not generalisation to unseen points.
        report = rb.evaluate_baselines(separable_samples(noise=0.3), **FAST)
        self.assertGreater(
            report["baselines"]["logistic_regression"]["accuracy"], 0.9
        )
        self.assertEqual(report["verdict"], rb.VERDICT_LINEAR)

    def test_random_labels_are_reported_as_not_learnable(self):
        for count in (120, 300):
            with self.subTest(count=count):
                report = rb.evaluate_baselines(
                    random_label_samples(count=count), **FAST
                )
                self.assertEqual(report["verdict"], rb.VERDICT_NOT_LEARNABLE)
                self.assertLess(
                    report["lift_over_majority"], report["required_lift"]
                )

    def test_a_perfect_tiny_holdout_cannot_collapse_the_threshold(self):
        # A plug-in binomial stderr is exactly zero at accuracy 0.0 or 1.0, so
        # a two-record holdout scoring 2/2 would drop required_lift to
        # min_lift precisely where the uncertainty is greatest.
        samples = [
            rb.Sample(f"s-{index}", tuple(float((index * 37) % 11) for _ in range(3)),
                      index % 2)
            for index in range(12)
        ]
        report = rb.evaluate_baselines(
            samples, logistic_iterations=20, mlp_iterations=20, mlp_hidden=4
        )
        self.assertGreater(report["test_accuracy_stderr"], 0.0)
        self.assertEqual(report["stderr_method"], "agresti_coull")
        self.assertEqual(report["verdict"], rb.VERDICT_NOT_LEARNABLE)
        self.assertFalse(rb.escalation_gate(report)["escalate_to_snn"])

    def test_a_holdout_below_the_floor_never_escalates(self):
        samples = separable_samples(count=30)
        report = rb.evaluate_baselines(samples, min_test_records=1000, **FAST)
        self.assertEqual(report["verdict"], rb.VERDICT_NOT_LEARNABLE)
        gate = rb.escalation_gate(report)
        self.assertFalse(gate["escalate_to_snn"])
        self.assertIn("holdout", gate["reason"])

    def test_a_thin_holdout_cannot_manufacture_a_lift(self):
        # 120 random-label samples leave a ~34-record holdout, on which noise
        # alone produced a ~0.12 lift. The two-standard-error floor is what
        # keeps that from reading as a learnable target.
        report = rb.evaluate_baselines(random_label_samples(count=120), **FAST)
        self.assertGreater(report["required_lift"], report["min_lift"])
        self.assertEqual(report["verdict"], rb.VERDICT_NOT_LEARNABLE)

    def test_baselines_are_deterministic(self):
        samples = separable_samples(noise=0.4)
        first = rb.evaluate_baselines(samples, **FAST)
        second = rb.evaluate_baselines(list(samples), **FAST)
        self.assertEqual(first["baselines"], second["baselines"])

    def test_a_tiny_dataset_is_refused(self):
        with self.assertRaises(rb.BaselineError):
            rb.evaluate_baselines(separable_samples(count=4), **FAST)

    def test_a_constant_target_is_refused(self):
        samples = [
            rb.Sample(f"c-{index}", (float(index), 1.0), 0) for index in range(20)
        ]
        with self.assertRaises(rb.BaselineError):
            rb.evaluate_baselines(samples, **FAST)


class EscalationGate(unittest.TestCase):
    def test_not_learnable_blocks_escalation(self):
        gate = rb.escalation_gate(
            {"verdict": rb.VERDICT_NOT_LEARNABLE, "min_lift": 0.05,
             "best": {"accuracy": 0.31}}
        )
        self.assertFalse(gate["escalate_to_snn"])
        self.assertIn("not learnable", gate["reason"])

    def test_linear_verdict_escalates_but_names_the_number_to_beat(self):
        gate = rb.escalation_gate(
            {
                "verdict": rb.VERDICT_LINEAR,
                "baselines": {"logistic_regression": {"accuracy": 0.91}},
            }
        )
        self.assertTrue(gate["escalate_to_snn"])
        self.assertEqual(gate["must_beat"], 0.91)

    def test_nonlinear_verdict_names_the_mlp(self):
        gate = rb.escalation_gate(
            {"verdict": rb.VERDICT_NONLINEAR, "baselines": {"mlp": {"accuracy": 0.8}}}
        )
        self.assertTrue(gate["escalate_to_snn"])
        self.assertEqual(gate["must_beat"], 0.8)

    def test_an_unknown_verdict_refuses_to_escalate(self):
        gate = rb.escalation_gate({"verdict": "mystery"})
        self.assertFalse(gate["escalate_to_snn"])


class AgainstRealRouterRecords(unittest.TestCase):
    def test_the_reference_router_target_gets_a_real_verdict(self):
        records = mr.build_records(11, 120)
        samples = rb.dataset_from_records(records)
        report = rb.evaluate_baselines(samples, **FAST)
        self.assertIn(
            report["verdict"],
            {rb.VERDICT_NOT_LEARNABLE, rb.VERDICT_LINEAR, rb.VERDICT_NONLINEAR},
        )
        self.assertGreaterEqual(
            report["baselines"]["majority_class"]["accuracy"], 0.0
        )
        self.assertEqual(report["feature_dim"], mr.COMPACT_DIM + 4)


class Cli(unittest.TestCase):
    def test_evaluate_reports_and_exits_on_the_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "router.jsonl"
            oc.write_jsonl(path, mr.build_records(11, 60))
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                exit_code = rb.main(
                    ["evaluate", str(path), "--iterations", "40"]
                )
            report = json.loads(buffer.getvalue())
            self.assertIn("escalation", report)
            self.assertEqual(
                exit_code, 0 if report["escalation"]["escalate_to_snn"] else 1
            )


if __name__ == "__main__":
    unittest.main()
