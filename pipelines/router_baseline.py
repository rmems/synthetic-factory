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

import moe_router  # noqa: E402
from oracle_grounded import distill_contract as oc  # noqa: E402
import validate_distill  # noqa: E402

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
    sampled_ids: set[str] = set()
    for record in records:
        sample = _record_sample(record, target)
        if sample is None:
            continue
        if sample.record_id in sampled_ids:
            # The id is the record's identity: two rows sharing one cannot
            # be attributed, weighted, or audited separately.
            raise BaselineError(
                f"duplicate record id {sample.record_id!r}; a corpus cannot "
                "carry the same record twice"
            )
        sampled_ids.add(sample.record_id)
        samples.append(sample)
    if samples:
        width = len(samples[0].features)
        if any(len(sample.features) != width for sample in samples):
            raise BaselineError("compact inputs have inconsistent width")
    return samples


def _record_sample(record: Any, target: str) -> Sample | None:
    """One record's (id, compact input, label), or None if it has no sample."""

    if not isinstance(record, dict):
        return None
    record_id = record.get("id")
    if not isinstance(record_id, str) or not record_id:
        # The id is the sample's identity for duplicate refusal and
        # attribution; a record without one has no usable sample.
        return None
    scenario = record.get("scenario")
    result = record.get("result")
    if not isinstance(scenario, dict) or not isinstance(result, dict):
        return None
    if result.get("status") != oc.RESULT_MEASURED:
        # An abstained result's routing fields are outcomes the oracle
        # explicitly declined to stand behind; they must never become labels.
        return None
    features = _compact_features(scenario)
    if features is None:
        return None
    label = _target_label(result, target)
    if label is None:
        return None
    return Sample(record_id=record_id, features=features, label=label)


def _compact_features(scenario: dict[str, Any]) -> tuple[float, ...] | None:
    compact = scenario.get("compact_input")
    if not isinstance(compact, dict):
        return None
    features = compact.get("features")
    if not isinstance(features, list) or not features:
        return None
    if not all(oc.is_number(value) for value in features):
        return None
    return tuple(float(value) for value in features)


def _genuine_int(value: Any) -> int | None:
    return int(value) if isinstance(value, int) and not isinstance(value, bool) else None


def _last_layer_top1(result: dict[str, Any]) -> int | None:
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
    return _genuine_int(experts[0])


def _target_label(result: dict[str, Any], target: str) -> int | None:
    if target == TARGET_TOP1:
        return _genuine_int(result.get("top1_expert"))
    return _last_layer_top1(result)


def split(
    samples: list[Sample], holdout_pct: int = 30
) -> tuple[list[Sample], list[Sample]]:
    """Deterministic train/test split keyed on the compact input.

    Hashing the input keeps the split stable when records are appended or
    reordered, so a baseline number is reproducible from the corpus alone —
    and it puts samples with identical compact inputs on the same side.
    Keying on the record id let duplicated contexts straddle the split, so
    the holdout scored exact input-label pairs the model had memorised from
    training and the escalation verdict was inflated by leakage (on the
    committed fixture it read learnable_nonlinear where the leak-free
    corpus supports learnable_linear).
    """

    if not 1 <= holdout_pct <= 90:
        raise BaselineError("holdout_pct must be between 1 and 90")
    train: list[Sample] = []
    test: list[Sample] = []
    for sample in samples:
        key = ",".join(repr(value) for value in sample.features)
        digest = hashlib.blake2b(key.encode("utf-8"), digest_size=8).digest()
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
        if error == 0.0:
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
        rng = random.Random(seed)
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


def _significance_floor(
    accuracy: float, test_count: int, min_lift: float
) -> tuple[float, float]:
    """(stderr, required_lift) — the floor a lift must clear to mean anything.

    A small holdout can manufacture a lift out of noise. Require the lift to
    clear two standard errors of the test accuracy as well as ``min_lift``,
    so a thin split reports "not learnable" instead of a flattering number.

    The standard error uses the Agresti-Coull adjusted proportion rather than
    the plug-in one. A plug-in estimate collapses to exactly zero when a tiny
    holdout happens to score 0.0 or 1.0 — dropping the threshold to
    ``min_lift`` precisely where the uncertainty is greatest — so two records
    scoring 2/2 would read as a learnable target.
    """

    adjusted = (accuracy * test_count + 2.0) / (test_count + 4.0)
    stderr = math.sqrt(adjusted * (1.0 - adjusted) / (test_count + 4.0))
    return stderr, round(max(min_lift, 2.0 * stderr), 6)


def _verdict(
    *,
    lift: float,
    required_lift: float,
    test_count: int,
    min_test_records: int,
    mlp_accuracy: float,
    logistic_accuracy: float,
    nonlinear_margin: float,
) -> str:
    if test_count < min_test_records:
        return VERDICT_NOT_LEARNABLE
    if lift < required_lift:
        return VERDICT_NOT_LEARNABLE
    if mlp_accuracy > logistic_accuracy + nonlinear_margin:
        return VERDICT_NONLINEAR
    return VERDICT_LINEAR


# Decision knobs that must be positive genuine integers, and why an
# out-of-domain value fakes the gate rather than merely misconfiguring it.
_POSITIVE_INT_KNOBS = (
    ("logistic_iterations", "zero training epochs would publish untrained baselines"),
    ("mlp_iterations", "zero training epochs would publish untrained baselines"),
    ("mlp_hidden", "a widthless MLP publishes a bias-only model as an MLP"),
    (
        "min_test_records",
        "a non-positive minimum disables the small-holdout safeguard",
    ),
)

# Decision thresholds that must be finite and non-negative. NaN survives
# ``max()`` and defeats every comparison against it, and a negative margin
# lets an MLP that trails the logistic model read as meaningfully nonlinear.
_THRESHOLD_KNOBS = ("min_lift", "nonlinear_margin")


def _check_evaluation_knobs(knobs: dict[str, Any]) -> None:
    """Refuse evaluation knobs that would fake or defeat the gate.

    argparse accepts ``--min-lift nan``: NaN survives ``max(min_lift, 2 *
    stderr)`` and every ``lift < required_lift`` comparison against it is
    false, so a large-enough holdout could emit a learnable verdict (and
    non-standard JSON carrying NaN) no finite threshold would grant. The
    remaining decision parameters are held to their domains for the same
    reason: an out-of-domain value does not misconfigure the gate, it
    quietly replaces the documented decision with a different one.
    """

    for name in _THRESHOLD_KNOBS:
        value = knobs[name]
        if not oc.is_number(value) or value < 0.0:
            raise BaselineError(
                f"{name} must be a finite non-negative number, got {value!r}"
            )
    for name, consequence in _POSITIVE_INT_KNOBS:
        value = knobs[name]
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            raise BaselineError(
                f"{name} must be a positive integer, got {value!r} — "
                f"{consequence}"
            )


def evaluate_baselines(
    samples: list[Sample],
    *,
    holdout_pct: int = 30,
    logistic_iterations: int = 120,
    mlp_iterations: int = 120,
    mlp_hidden: int = 12,
    min_lift: float = 0.05,
    min_test_records: int = 20,
    nonlinear_margin: float = 0.03,
) -> dict[str, Any]:
    """Run every conventional baseline and return a comparable report."""

    _check_evaluation_knobs(
        {
            "min_lift": min_lift,
            "nonlinear_margin": nonlinear_margin,
            "logistic_iterations": logistic_iterations,
            "mlp_iterations": mlp_iterations,
            "mlp_hidden": mlp_hidden,
            "min_test_records": min_test_records,
        }
    )
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
    stderr, required_lift = _significance_floor(best["accuracy"], len(test), min_lift)
    verdict = _verdict(
        lift=lift,
        required_lift=required_lift,
        test_count=len(test),
        min_test_records=min_test_records,
        mlp_accuracy=mlp["accuracy"],
        logistic_accuracy=logistic["accuracy"],
        nonlinear_margin=nonlinear_margin,
    )
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
        "min_test_records": min_test_records,
        "test_accuracy_stderr": round(stderr, 6),
        "stderr_method": "agresti_coull",
        "required_lift": required_lift,
        "verdict": verdict,
    }


def _threshold_accuracy(report: dict[str, Any]) -> float | None:
    """The accuracy an SNN student has to beat: the best baseline that ran.

    Prefers ``report["best"]``, which ``evaluate_baselines`` always sets, and
    otherwise takes the maximum over whatever baselines the report carries.
    Never a single named model: a ``learnable_linear`` verdict only says the
    MLP failed to clear ``nonlinear_margin``, not that it lost, so naming the
    logistic accuracy would publish a threshold an SNN could meet while
    underperforming a baseline that had already been evaluated.
    """

    accuracies: list[float] = []
    best = report.get("best")
    if isinstance(best, dict) and isinstance(best.get("accuracy"), (int, float)):
        accuracies.append(float(best["accuracy"]))
    baselines = report.get("baselines")
    if isinstance(baselines, dict):
        for entry in baselines.values():
            if isinstance(entry, dict) and isinstance(
                entry.get("accuracy"), (int, float)
            ):
                accuracies.append(float(entry["accuracy"]))
    return max(accuracies) if accuracies else None


def escalation_gate(report: dict[str, Any]) -> dict[str, Any]:
    """Decide whether an SNN router student is justified by the baselines."""

    verdict = report.get("verdict")
    if verdict == VERDICT_NOT_LEARNABLE:
        return {
            "escalate_to_snn": False,
            "verdict": verdict,
            "reason": (
                (
                    f"the holdout is {report.get('test')} records, below the "
                    f"{report.get('min_test_records')} needed for a baseline "
                    "number to mean anything"
                )
                if (report.get("test") or 0) < (report.get("min_test_records") or 0)
                else (
                    "no conventional baseline beat the majority class by "
                    f"{report.get('required_lift', report.get('min_lift'))} "
                    "(max of min_lift and two Agresti-Coull standard errors of "
                    "the test accuracy)"
                )
            )
            + " — the target is not learnable from these compact inputs, so an "
            "SNN student is not justified",
            "must_beat": _threshold_accuracy(report),
        }
    if verdict == VERDICT_LINEAR:
        return {
            "escalate_to_snn": True,
            "verdict": verdict,
            "reason": (
                "a linear model already predicts the router; an SNN student is "
                "only justified if it beats the best conventional baseline"
            ),
            # `learnable_linear` only means the MLP did not clear
            # `nonlinear_margin`, not that it lost. Reporting the logistic
            # accuracy here would let an SNN satisfy the published threshold
            # while losing to a baseline that had already been run — which is
            # the whole point of running baselines first.
            "must_beat": _threshold_accuracy(report),
        }
    if verdict == VERDICT_NONLINEAR:
        return {
            "escalate_to_snn": True,
            "verdict": verdict,
            "reason": (
                "the MLP is meaningfully ahead of the linear model, so there is "
                "non-linear structure a richer student could exploit"
            ),
            "must_beat": _threshold_accuracy(report),
        }
    return {
        "escalate_to_snn": False,
        "verdict": verdict,
        "reason": "unknown verdict; refusing to escalate",
        "must_beat": None,
    }


def _record_gate_problems(obj: dict[str, Any], where: str) -> list[str]:
    """The gate findings one parsed record contributes beyond check_record."""

    problems: list[str] = []
    if obj.get("family") != moe_router.FAMILY:
        problems.append(
            f"{where}: family {obj.get('family')!r} is not "
            f"{moe_router.FAMILY!r}"
        )
    result = obj.get("result")
    status = result.get("status") if isinstance(result, dict) else None
    if status != oc.RESULT_MEASURED:
        # A valid record can honestly abstain, but its routing fields are
        # outcomes the oracle declined to produce. Refuse loudly rather than
        # let dataset_from_records drop it silently — the operator should see
        # the abstentions and filter deliberately.
        problems.append(
            f"{where}: result.status is {status!r} — the baseline "
            "only evaluates measured router results"
        )
    return problems


def _clean_router_records(path: str) -> list[dict[str, Any]]:
    """CLI gate: every input line must be a clean router-family record.

    The reported accuracies and the SNN escalation verdict are computed from
    whatever this file contains. A tampered record — a stale digest, a family
    finding, a relabelled ``top1_expert`` — that still *looks* router-shaped
    would silently move those numbers, so the evaluation is refused rather
    than computed over unvalidated rows.
    """

    problems: list[str] = []
    records: list[dict[str, Any]] = []
    # Streamed: the raw file is never buffered whole beside the parsed rows.
    for lineno, obj in oc.iter_jsonl(path):
        where = f"{path}:{lineno}"
        if obj is None:
            problems.append(f"{where}: JSON parse failure")
            continue
        errors = validate_distill.check_record(obj, where)
        if isinstance(obj, dict):
            problems.extend(_record_gate_problems(obj, where))
            records.append(obj)
        problems.extend(errors)
    if problems:
        shown = "; ".join(problems[:5])
        more = f" (+{len(problems) - 5} more)" if len(problems) > 5 else ""
        raise BaselineError(
            f"input is not a clean router-family corpus: {shown}{more}"
        )
    return records


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
        records = _clean_router_records(args.records)
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
