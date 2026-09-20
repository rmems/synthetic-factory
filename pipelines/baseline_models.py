#!/usr/bin/env python3
"""Deterministic classical models for the MoE-router baseline gate.

Majority-class, multinomial logistic regression, and a one-hidden-layer
MLP — stdlib only, all seeded."""

from __future__ import annotations

import math
import random
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

if __package__:
    from .baseline_dataset import BaselineError, Sample
else:
    from baseline_dataset import BaselineError, Sample

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
    splits: tuple[list[Sample], list[Sample]],
    **hyper: Any,
) -> dict[str, Any]:
    train, test = splits
    truth = [sample.label for sample in test]
    return {
        "model": name,
        "accuracy": round(_accuracy([predict(s) for s in test], truth), 6),
        "train_accuracy": round(
            _accuracy([predict(s) for s in train], [s.label for s in train]), 6
        ),
        **hyper,
    }


@dataclass(frozen=True)
class LogisticHyper:
    """Full-batch descent knobs for the logistic baseline."""

    iterations: int = 120
    learning_rate: float = 0.5
    l2: float = 1e-4


def _logistic_epoch(
    params: tuple[list[list[float]], list[float]],
    train: list[Sample],
    index_of: dict[int, int],
    grads: tuple[list[list[float]], list[float]],
) -> None:
    """Accumulate one pass of softmax cross-entropy gradients."""

    weights, bias = params
    grad_w, grad_b = grads
    for sample in train:
        scores = _linear_scores(weights, bias, sample.features)
        errors = _prediction_errors(scores, index_of[sample.label])
        _accumulate_outer(errors, sample.features, grad_w, grad_b)


def _logistic_descend(
    params: tuple[list[list[float]], list[float]],
    grads: tuple[list[list[float]], list[float]],
    hyper: LogisticHyper,
    scale: float,
) -> None:
    """Apply the averaged gradient plus the l2 weight decay in place."""

    weights, bias = params
    grad_w, grad_b = grads
    for row, grad_row in zip(weights, grad_w):
        for i, gradient in enumerate(grad_row):
            row[i] -= hyper.learning_rate * (gradient * scale + hyper.l2 * row[i])
    for c, gradient in enumerate(grad_b):
        bias[c] -= hyper.learning_rate * gradient * scale


def _train_logistic(
    train: list[Sample], index_of: dict[int, int], hyper: LogisticHyper
) -> tuple[list[list[float]], list[float]]:
    classes = len(index_of)
    width = len(train[0].features)
    params = ([[0.0] * width for _ in range(classes)], [0.0] * classes)
    scale = 1.0 / len(train)
    for _ in range(hyper.iterations):
        grads = ([[0.0] * width for _ in range(classes)], [0.0] * classes)
        _logistic_epoch(params, train, index_of, grads)
        _logistic_descend(params, grads, hyper, scale)
    return params


def logistic_baseline(
    train: list[Sample],
    test: list[Sample],
    labels: list[int],
    hyper: LogisticHyper = LogisticHyper(),
) -> dict[str, Any]:
    """Multinomial logistic regression by deterministic full-batch descent."""

    index_of = {label: index for index, label in enumerate(labels)}
    weights, bias = _train_logistic(train, index_of, hyper)

    def predict(example: Sample) -> int:
        return _argmax_label(_linear_scores(weights, bias, example.features), labels)

    return _model_report(
        "logistic_regression", predict, (train, test), **asdict(hyper)
    )


@dataclass(frozen=True)
class _MlpShape:
    """Layer widths of the MLP baseline: input, hidden, output."""

    width: int
    hidden: int
    classes: int


class _Mlp:
    """One tanh hidden layer + softmax output, seeded exactly as before."""

    def __init__(self, shape: _MlpShape, seed: int) -> None:
        width, hidden, classes = shape.width, shape.hidden, shape.classes
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
        self, train: list[Sample], index_of: dict[int, int], step: float
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
        self._descend((self.w2, self.b2), (gw2, gb2), step)
        self._descend((self.w1, self.b1), (gw1, gb1), step)

    @staticmethod
    def _descend(
        params: tuple[list[list[float]], list[float]],
        grads: tuple[list[list[float]], list[float]],
        step: float,
    ) -> None:
        weights, bias = params
        grad_rows, grad_bias = grads
        for row, grad_row in zip(weights, grad_rows):
            for i, gradient in enumerate(grad_row):
                row[i] -= step * gradient
        for c, gradient in enumerate(grad_bias):
            bias[c] -= step * gradient


@dataclass(frozen=True)
class MlpHyper:
    """Hidden width, descent knobs and seed for the MLP baseline."""

    hidden: int = 12
    iterations: int = 120
    learning_rate: float = 0.3
    seed: int = 17


def mlp_baseline(
    train: list[Sample],
    test: list[Sample],
    labels: list[int],
    hyper: MlpHyper = MlpHyper(),
) -> dict[str, Any]:
    """One tanh hidden layer, softmax output, deterministic full-batch descent."""

    index_of = {label: index for index, label in enumerate(labels)}
    model = _Mlp(
        _MlpShape(len(train[0].features), hyper.hidden, len(labels)), hyper.seed
    )
    step = hyper.learning_rate / len(train)
    for _ in range(hyper.iterations):
        model.train_epoch(train, index_of, step)

    def predict(example: Sample) -> int:
        _, scores = model.forward(example.features)
        return _argmax_label(scores, labels)

    return _model_report("mlp", predict, (train, test), **asdict(hyper))


