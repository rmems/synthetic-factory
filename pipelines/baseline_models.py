#!/usr/bin/env python3
"""Deterministic classical models for the MoE-router baseline gate.

Majority-class, multinomial logistic regression, and a one-hidden-layer
MLP — stdlib only, all seeded."""

from __future__ import annotations

import math
import random
import sys
from pathlib import Path
from typing import Any

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from oracle_grounded import distill_contract as oc  # noqa: E402

if __package__:
    from .baseline_dataset import BaselineError, Sample, split
else:
    from baseline_dataset import BaselineError, Sample, split

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


def _linear_scores(
    weights: list[list[float]], bias: list[float], features: tuple[float, ...]
) -> list[float]:
    return [
        sum(w * x for w, x in zip(row, features)) + offset
        for row, offset in zip(weights, bias)
    ]


def _argmax_label(scores: list[float], labels: list[int]) -> int:
    return labels[max(range(len(labels)), key=lambda idx: (scores[idx], -idx))]


def _accumulate_outer(
    errors: list[float],
    inputs: tuple[float, ...] | list[float],
    grad_rows: list[list[float]],
    grad_bias: list[float],
) -> None:
    """Add ``error * input`` outer-product terms into the gradient rows."""

    for c, error in enumerate(errors):
        if not error:
            continue
        row = grad_rows[c]
        for i, value in enumerate(inputs):
            row[i] += error * value
        grad_bias[c] += error


def _prediction_errors(
    scores: list[float], target_index: int
) -> list[float]:
    """Softmax probabilities with the target subtracted: dLoss/dLogit."""

    errors = _softmax(scores)
    errors[target_index] -= 1.0
    return errors


def _model_report(
    name: str,
    predict,
    train: list[Sample],
    test: list[Sample],
    **hyper: Any,
) -> dict[str, Any]:
    truth = [sample.label for sample in test]
    return {
        "model": name,
        "accuracy": round(_accuracy([predict(s) for s in test], truth), 6),
        "train_accuracy": round(
            _accuracy([predict(s) for s in train], [s.label for s in train]), 6
        ),
        **hyper,
    }


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
            scores = _linear_scores(weights, bias, sample.features)
            errors = _prediction_errors(scores, index_of[sample.label])
            _accumulate_outer(errors, sample.features, grad_w, grad_b)
        for c in range(classes):
            row = weights[c]
            grad_row = grad_w[c]
            for i in range(width):
                row[i] -= learning_rate * (grad_row[i] * scale + l2 * row[i])
            bias[c] -= learning_rate * grad_b[c] * scale

    def predict(example: Sample) -> int:
        return _argmax_label(_linear_scores(weights, bias, example.features), labels)

    return _model_report(
        "logistic_regression",
        predict,
        train,
        test,
        iterations=iterations,
        learning_rate=learning_rate,
        l2=l2,
    )


class _Mlp:
    """One tanh hidden layer + softmax output, seeded exactly as before."""

    def __init__(self, width: int, hidden: int, classes: int, seed: int) -> None:
        rng = random.Random(seed)  # nosec B311 - reproducible model initialisation
        limit = math.sqrt(6.0 / (width + hidden))
        self.w1 = [
            [rng.uniform(-limit, limit) for _ in range(width)] for _ in range(hidden)
        ]
        self.b1 = [0.0] * hidden
        limit2 = math.sqrt(6.0 / (hidden + classes))
        self.w2 = [
            [rng.uniform(-limit2, limit2) for _ in range(hidden)]
            for _ in range(classes)
        ]
        self.b2 = [0.0] * classes
        self.width = width
        self.hidden = hidden
        self.classes = classes

    def forward(self, features: tuple[float, ...]) -> tuple[list[float], list[float]]:
        hidden_pre = _linear_scores(self.w1, self.b1, features)
        activated = [math.tanh(value) for value in hidden_pre]
        logits = [
            sum(w * a for w, a in zip(row, activated)) + offset
            for row, offset in zip(self.w2, self.b2)
        ]
        return activated, logits

    def _hidden_errors(
        self, delta_out: list[float], activated: list[float]
    ) -> list[float]:
        errors: list[float] = []
        for h in range(self.hidden):
            upstream = sum(
                delta_out[c] * self.w2[c][h] for c in range(self.classes)
            )
            errors.append(upstream * (1.0 - activated[h] * activated[h]))
        return errors

    def train_epoch(
        self, train: list[Sample], index_of: dict[int, int],
        learning_rate: float, scale: float,
    ) -> None:
        gw1 = [[0.0] * self.width for _ in range(self.hidden)]
        gb1 = [0.0] * self.hidden
        gw2 = [[0.0] * self.hidden for _ in range(self.classes)]
        gb2 = [0.0] * self.classes
        for sample in train:
            activated, logits = self.forward(sample.features)
            delta_out = _prediction_errors(logits, index_of[sample.label])
            _accumulate_outer(delta_out, activated, gw2, gb2)
            _accumulate_outer(
                self._hidden_errors(delta_out, activated), sample.features, gw1, gb1
            )
        self._descend(self.w2, self.b2, gw2, gb2, learning_rate, scale)
        self._descend(self.w1, self.b1, gw1, gb1, learning_rate, scale)

    @staticmethod
    def _descend(
        weights: list[list[float]], bias: list[float],
        grad_rows: list[list[float]], grad_bias: list[float],
        learning_rate: float, scale: float,
    ) -> None:
        for row, grad_row in zip(weights, grad_rows):
            for i, gradient in enumerate(grad_row):
                row[i] -= learning_rate * gradient * scale
        for c, gradient in enumerate(grad_bias):
            bias[c] -= learning_rate * gradient * scale


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
    model = _Mlp(len(train[0].features), hidden, len(labels), seed)
    scale = 1.0 / len(train)
    for _ in range(iterations):
        model.train_epoch(train, index_of, learning_rate, scale)

    def predict(example: Sample) -> int:
        _, scores = model.forward(example.features)
        return _argmax_label(scores, labels)

    return _model_report(
        "mlp",
        predict,
        train,
        test,
        hidden=hidden,
        iterations=iterations,
        learning_rate=learning_rate,
        seed=seed,
    )


