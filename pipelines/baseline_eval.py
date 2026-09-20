#!/usr/bin/env python3
"""Evaluation and escalation gate for the MoE-router baseline.

Runs the three conventional baselines on the extracted dataset, decides the
``learnable_*`` verdict, and validates loaded router records via
``validate_distill``.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

import moe_router  # noqa: E402
from oracle_grounded import distill_contract as oc  # noqa: E402
import validate_distill  # noqa: E402

if __package__:
    from .baseline_dataset import (
        BaselineError,
        Sample,
        VERDICT_LINEAR,
        VERDICT_NONLINEAR,
        VERDICT_NOT_LEARNABLE,
        split,
        standardize,
    )
    from .baseline_models import (
        logistic_baseline,
        majority_baseline,
        mlp_baseline,
    )
else:
    from baseline_dataset import (
        BaselineError,
        Sample,
        VERDICT_LINEAR,
        VERDICT_NONLINEAR,
        VERDICT_NOT_LEARNABLE,
        split,
        standardize,
    )
    from baseline_models import (
        logistic_baseline,
        majority_baseline,
        mlp_baseline,
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
    # Class space comes from the training split only: a label that appears
    # only in held-out rows must be a class the baseline was never told about,
    # not one it silently can't predict.
    labels = sorted({sample.label for sample in train})
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


