#!/usr/bin/env python3
"""Conventional baselines for MoE router distillation, run before any SNN.

Issue #78 is explicit: before an SNN student is used for router distillation,
at least one simple conventional baseline — a linear model and/or a small MLP —
must be evaluated on the same compact inputs. If the target is not learnable
from those inputs, escalating to an SNN for novelty is not justified.

This module is that gate. Everything is standard library: a majority-class
baseline, multinomial logistic regression, and a one-hidden-layer MLP, all
deterministic given a seed.

``escalation_gate`` turns the report into a decision:

``not_learnable_from_compact_inputs``
    No baseline beats the majority class by ``min_lift``. Do not escalate.
``learnable_linear``
    A linear model already predicts the router. An SNN is only justified if it
    beats this number, not because it is more interesting.
``learnable_nonlinear``
    The MLP is meaningfully ahead of the linear model, so there is non-linear
    structure a richer student could exploit.

CLI::

    python3 pipelines/router_baseline.py evaluate <records.jsonl> --json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

import oracle_contract as oc  # noqa: E402

TARGET_TOP1 = "top1_expert"
TARGET_TOP1_LAST_LAYER = "top1_expert_last_layer"
TARGETS = (TARGET_TOP1, TARGET_TOP1_LAST_LAYER)

VERDICT_NOT_LEARNABLE = "not_learnable_from_compact_inputs"
VERDICT_LINEAR = "learnable_linear"
VERDICT_NONLINEAR = "learnable_nonlinear"


class BaselineError(ValueError):
    """Raised when a dataset cannot support a baseline evaluation."""


@dataclass(frozen=True)
class Sample:
    """One student example: a compact input and the router's own choice."""

    record_id: str
    features: tuple[float, ...]
    label: int


def dataset_from_records(
    records: list[dict[str, Any]], target: str = TARGET_TOP1
) -> list[Sample]:
    """Extract (compact input, router label) pairs from oracle-grounded records.

    Inputs come from the generator-owned ``scenario.compact_input.features``;
    labels come from the oracle-owned ``result``. The split of ownership is the
    point: the student never sees a label the generator wrote.
    """

    if target not in TARGETS:
        raise BaselineError(f"unknown target: {target!r}")
    samples: list[Sample] = []
    for record in records:
        if not isinstance(record, dict):
            continue
        scenario = record.get("scenario")
        result = record.get("result")
        if not isinstance(scenario, dict) or not isinstance(result, dict):
            continue
        compact = scenario.get("compact_input")
        if not isinstance(compact, dict):
            continue
        features = compact.get("features")
        if not isinstance(features, list) or not features:
            continue
        if not all(oc.is_number(value) for value in features):
            continue
        label = _target_label(result, target)
        if label is None:
            continue
        samples.append(
            Sample(
                record_id=str(record.get("id")),
                features=tuple(float(value) for value in features),
                label=label,
            )
        )
    if samples:
        width = len(samples[0].features)
        if any(len(sample.features) != width for sample in samples):
            raise BaselineError("compact inputs have inconsistent width")
    return samples


def _target_label(result: dict[str, Any], target: str) -> int | None:
    if target == TARGET_TOP1:
        value = result.get("top1_expert")
        return int(value) if isinstance(value, int) and not isinstance(value, bool) else None
    routing = result.get("routing")
    if not isinstance(routing, dict):
        return None
    layers = routing.get("layers")
    if not isinstance(layers, list) or not layers:
        return None
    last = layers[-1]
    if not isinstance(last, dict):
        return None
    experts = last.get("top_k_experts")
    if not isinstance(experts, list) or not experts:
        return None
    top = experts[0]
    return int(top) if isinstance(top, int) and not isinstance(top, bool) else None


def split(
    samples: list[Sample], holdout_pct: int = 30
) -> tuple[list[Sample], list[Sample]]:
    """Deterministic train/test split keyed on the record id.

    Hashing the id keeps the split stable when records are appended or
    reordered, so a baseline number is reproducible from the corpus alone.
    """

    if not 1 <= holdout_pct <= 90:
        raise BaselineError("holdout_pct must be between 1 and 90")
    train: list[Sample] = []
    test: list[Sample] = []
    for sample in samples:
        digest = hashlib.blake2b(
            sample.record_id.encode("utf-8"), digest_size=8
        ).digest()
        bucket = int.from_bytes(digest[:4], "big") % 100
        (test if bucket < holdout_pct else train).append(sample)
    return train, test


def standardize(
    train: list[Sample], test: list[Sample]
) -> tuple[list[Sample], list[Sample], dict[str, list[float]]]:
    """Zero-mean unit-variance scaling fitted on the training split only."""

    if not train:
        raise BaselineError("cannot standardize an empty training split")
    width = len(train[0].features)
    means = [
        sum(sample.features[i] for sample in train) / len(train) for i in range(width)
    ]
    variances = []
    for i in range(width):
        total = sum((sample.features[i] - means[i]) ** 2 for sample in train)
        variances.append(math.sqrt(total / len(train)) or 1.0)

    def apply(rows: list[Sample]) -> list[Sample]:
        return [
            Sample(
                record_id=sample.record_id,
                features=tuple(
                    (value - mean) / scale
                    for value, mean, scale in zip(sample.features, means, variances)
                ),
                label=sample.label,
            )
            for sample in rows
        ]

    return apply(train), apply(test), {"mean": means, "scale": variances}


def _accuracy(predictions: list[int], truth: list[int]) -> float:
    if not truth:
        return 0.0
    hits = sum(1 for a, b in zip(predictions, truth) if a == b)
    return hits / len(truth)


def majority_baseline(train: list[Sample], test: list[Sample]) -> dict[str, Any]:
    """Predict the most frequent training label for everything."""

    counts: dict[int, int] = {}
    for sample in train:
        counts[sample.label] = counts.get(sample.label, 0) + 1
    if not counts:
        raise BaselineError("cannot fit a majority baseline on an empty split")
    predicted = min(counts.items(), key=lambda item: (-item[1], item[0]))[0]
    truth = [sample.label for sample in test]
    return {
        "model": "majority_class",
        "accuracy": round(_accuracy([predicted] * len(truth), truth), 6),
        "predicts": predicted,
        "train_support": counts[predicted],
    }


def _softmax(values: list[float]) -> list[float]:
    peak = max(values)
    exponentials = [math.exp(value - peak) for value in values]
    total = sum(exponentials)
    return [value / total for value in exponentials]


def logistic_baseline(
    train: list[Sample],
    test: list[Sample],
    labels: list[int],
    *,
    iterations: int = 120,
    learning_rate: float = 0.5,
    l2: float = 1e-4,
) -> dict[str, Any]:
    """Multinomial logistic regression by deterministic full-batch descent."""

    index_of = {label: index for index, label in enumerate(labels)}
    classes = len(labels)
    width = len(train[0].features)
    weights = [[0.0] * width for _ in range(classes)]
    bias = [0.0] * classes
    scale = 1.0 / len(train)

    for _ in range(iterations):
        grad_w = [[0.0] * width for _ in range(classes)]
        grad_b = [0.0] * classes
        for sample in train:
            logits = [
                sum(w * x for w, x in zip(weights[c], sample.features)) + bias[c]
                for c in range(classes)
            ]
            probabilities = _softmax(logits)
            probabilities[index_of[sample.label]] -= 1.0
            for c in range(classes):
                error = probabilities[c]
                if error == 0.0:
                    continue
                row = grad_w[c]
                for i, value in enumerate(sample.features):
                    row[i] += error * value
                grad_b[c] += error
        for c in range(classes):
            row = weights[c]
            grad_row = grad_w[c]
            for i in range(width):
                row[i] -= learning_rate * (grad_row[i] * scale + l2 * row[i])
            bias[c] -= learning_rate * grad_b[c] * scale

    def predict(sample: Sample) -> int:
        logits = [
            sum(w * x for w, x in zip(weights[c], sample.features)) + bias[c]
            for c in range(classes)
        ]
        return labels[max(range(classes), key=lambda c: (logits[c], -c))]

    truth = [sample.label for sample in test]
    return {
        "model": "logistic_regression",
        "accuracy": round(_accuracy([predict(s) for s in test], truth), 6),
        "train_accuracy": round(
            _accuracy([predict(s) for s in train], [s.label for s in train]), 6
        ),
        "iterations": iterations,
        "learning_rate": learning_rate,
        "l2": l2,
    }


def mlp_baseline(
    train: list[Sample],
    test: list[Sample],
    labels: list[int],
    *,
    hidden: int = 12,
    iterations: int = 120,
    learning_rate: float = 0.3,
    seed: int = 17,
) -> dict[str, Any]:
    """One tanh hidden layer, softmax output, deterministic full-batch descent."""

    index_of = {label: index for index, label in enumerate(labels)}
    classes = len(labels)
    width = len(train[0].features)
    rng = random.Random(seed)
    limit = math.sqrt(6.0 / (width + hidden))
    w1 = [[rng.uniform(-limit, limit) for _ in range(width)] for _ in range(hidden)]
    b1 = [0.0] * hidden
    limit2 = math.sqrt(6.0 / (hidden + classes))
    w2 = [[rng.uniform(-limit2, limit2) for _ in range(hidden)] for _ in range(classes)]
    b2 = [0.0] * classes
    scale = 1.0 / len(train)

    def forward(features: tuple[float, ...]) -> tuple[list[float], list[float]]:
        hidden_pre = [
            sum(w * x for w, x in zip(w1[h], features)) + b1[h] for h in range(hidden)
        ]
        activated = [math.tanh(value) for value in hidden_pre]
        logits = [
            sum(w * a for w, a in zip(w2[c], activated)) + b2[c] for c in range(classes)
        ]
        return activated, logits

    for _ in range(iterations):
        gw1 = [[0.0] * width for _ in range(hidden)]
        gb1 = [0.0] * hidden
        gw2 = [[0.0] * hidden for _ in range(classes)]
        gb2 = [0.0] * classes
        for sample in train:
            activated, logits = forward(sample.features)
            delta_out = _softmax(logits)
            delta_out[index_of[sample.label]] -= 1.0
            for c in range(classes):
                error = delta_out[c]
                if error == 0.0:
                    continue
                row = gw2[c]
                for h in range(hidden):
                    row[h] += error * activated[h]
                gb2[c] += error
            for h in range(hidden):
                upstream = sum(delta_out[c] * w2[c][h] for c in range(classes))
                delta_hidden = upstream * (1.0 - activated[h] * activated[h])
                if delta_hidden == 0.0:
                    continue
                row = gw1[h]
                for i, value in enumerate(sample.features):
                    row[i] += delta_hidden * value
                gb1[h] += delta_hidden
        for c in range(classes):
            for h in range(hidden):
                w2[c][h] -= learning_rate * gw2[c][h] * scale
            b2[c] -= learning_rate * gb2[c] * scale
        for h in range(hidden):
            for i in range(width):
                w1[h][i] -= learning_rate * gw1[h][i] * scale
            b1[h] -= learning_rate * gb1[h] * scale

    def predict(sample: Sample) -> int:
        _, logits = forward(sample.features)
        return labels[max(range(classes), key=lambda c: (logits[c], -c))]

    truth = [sample.label for sample in test]
    return {
        "model": "mlp",
        "accuracy": round(_accuracy([predict(s) for s in test], truth), 6),
        "train_accuracy": round(
            _accuracy([predict(s) for s in train], [s.label for s in train]), 6
        ),
        "hidden": hidden,
        "iterations": iterations,
        "learning_rate": learning_rate,
        "seed": seed,
    }


def evaluate_baselines(
    samples: list[Sample],
    *,
    holdout_pct: int = 30,
    logistic_iterations: int = 120,
    mlp_iterations: int = 120,
    mlp_hidden: int = 12,
    min_lift: float = 0.05,
    nonlinear_margin: float = 0.03,
) -> dict[str, Any]:
    """Run every conventional baseline and return a comparable report."""

    if len(samples) < 8:
        raise BaselineError("need at least 8 samples to evaluate a baseline")
    train, test = split(samples, holdout_pct=holdout_pct)
    if not train or not test:
        raise BaselineError(
            f"degenerate split: {len(train)} train / {len(test)} test — "
            "adjust holdout_pct or add records"
        )
    scaled_train, scaled_test, scaler = standardize(train, test)
    labels = sorted({sample.label for sample in samples})
    if len(labels) < 2:
        raise BaselineError("router labels are constant; nothing to distil")

    majority = majority_baseline(train, test)
    logistic = logistic_baseline(
        scaled_train, scaled_test, labels, iterations=logistic_iterations
    )
    mlp = mlp_baseline(
        scaled_train, scaled_test, labels, hidden=mlp_hidden, iterations=mlp_iterations
    )

    trained = [logistic, mlp]
    best = max(trained, key=lambda item: (item["accuracy"], item["model"]))
    lift = round(best["accuracy"] - majority["accuracy"], 6)
    # A small holdout can manufacture a lift out of noise. Require the lift to
    # clear two binomial standard errors of the test accuracy as well as
    # ``min_lift``, so a thin split reports "not learnable" instead of a
    # flattering number.
    accuracy = best["accuracy"]
    stderr = math.sqrt(max(accuracy * (1.0 - accuracy), 0.0) / len(test))
    required_lift = round(max(min_lift, 2.0 * stderr), 6)
    if lift < required_lift:
        verdict = VERDICT_NOT_LEARNABLE
    elif mlp["accuracy"] > logistic["accuracy"] + nonlinear_margin:
        verdict = VERDICT_NONLINEAR
    else:
        verdict = VERDICT_LINEAR
    return {
        "samples": len(samples),
        "train": len(train),
        "test": len(test),
        "classes": labels,
        "feature_dim": len(samples[0].features),
        "holdout_pct": holdout_pct,
        "scaler": {"fitted_on": "train", "dim": len(scaler["mean"])},
        "baselines": {
            "majority_class": majority,
            "logistic_regression": logistic,
            "mlp": mlp,
        },
        "best": {"model": best["model"], "accuracy": best["accuracy"]},
        "lift_over_majority": lift,
        "min_lift": min_lift,
        "test_accuracy_stderr": round(stderr, 6),
        "required_lift": required_lift,
        "verdict": verdict,
    }


def escalation_gate(report: dict[str, Any]) -> dict[str, Any]:
    """Decide whether an SNN router student is justified by the baselines."""

    verdict = report.get("verdict")
    if verdict == VERDICT_NOT_LEARNABLE:
        return {
            "escalate_to_snn": False,
            "verdict": verdict,
            "reason": (
                "no conventional baseline beat the majority class by "
                f"{report.get('required_lift', report.get('min_lift'))} "
                "(max of min_lift and two binomial standard errors of the test "
                "accuracy) — the target is not learnable from these compact "
                "inputs, so an SNN student is not justified"
            ),
            "must_beat": report.get("best", {}).get("accuracy"),
        }
    if verdict == VERDICT_LINEAR:
        return {
            "escalate_to_snn": True,
            "verdict": verdict,
            "reason": (
                "a linear model already predicts the router; an SNN student is "
                "only justified if it beats that accuracy"
            ),
            "must_beat": report.get("baselines", {})
            .get("logistic_regression", {})
            .get("accuracy"),
        }
    if verdict == VERDICT_NONLINEAR:
        return {
            "escalate_to_snn": True,
            "verdict": verdict,
            "reason": (
                "the MLP is meaningfully ahead of the linear model, so there is "
                "non-linear structure a richer student could exploit"
            ),
            "must_beat": report.get("baselines", {}).get("mlp", {}).get("accuracy"),
        }
    return {
        "escalate_to_snn": False,
        "verdict": verdict,
        "reason": "unknown verdict; refusing to escalate",
        "must_beat": None,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    evaluate = sub.add_parser("evaluate", help="run the conventional baselines")
    evaluate.add_argument("records", help="router-distillation JSONL")
    evaluate.add_argument("--target", default=TARGET_TOP1, choices=list(TARGETS))
    evaluate.add_argument("--holdout-pct", type=int, default=30)
    evaluate.add_argument("--iterations", type=int, default=120)
    evaluate.add_argument("--min-lift", type=float, default=0.05)

    args = parser.parse_args(argv)
    try:
        records = [obj for _, obj in oc.read_jsonl(args.records) if isinstance(obj, dict)]
        samples = dataset_from_records(records, target=args.target)
        report = evaluate_baselines(
            samples,
            holdout_pct=args.holdout_pct,
            logistic_iterations=args.iterations,
            mlp_iterations=args.iterations,
            min_lift=args.min_lift,
        )
    except BaselineError as exc:
        print(json.dumps({"error": str(exc)}, indent=2), file=sys.stderr)
        return 2
    report["target"] = args.target
    report["escalation"] = escalation_gate(report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["escalation"]["escalate_to_snn"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
