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

    python3 pipelines/router_baseline.py evaluate <records.jsonl>


This module is the stable entry point and compatibility facade. The
implementation is split into responsibility-named siblings:

* ``baseline_dataset.py`` -- record → ``Sample`` extraction, split, standardise.
* ``baseline_models.py`` -- majority / logistic / MLP baseline models.
* ``baseline_eval.py`` -- evaluation report, escalation gate, record loading.

Every public name any of them defines is re-exported here, so existing
``import router_baseline`` call sites resolve unchanged.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

if __package__:
    from .baseline_dataset import (
        TARGETS,
        TARGET_TOP1,
        TARGET_TOP1_LAST_LAYER,
        VERDICT_LINEAR,
        VERDICT_NONLINEAR,
        VERDICT_NOT_LEARNABLE,
        BaselineError,
        Sample,
        dataset_from_records,
        split,
        standardize,
        _compact_features,
        _genuine_int,
        _last_layer_top1,
        _record_sample,
        _target_label,
    )
    from .baseline_models import (
        logistic_baseline,
        majority_baseline,
        mlp_baseline,
        _model_report,
    )
    from .baseline_eval import (
        escalation_gate,
        evaluate_baselines,
        _check_evaluation_knobs,
        _clean_router_records,
        _record_gate_problems,
        _threshold_accuracy,
        _verdict,
    )
else:
    from baseline_dataset import (
        TARGETS,
        TARGET_TOP1,
        TARGET_TOP1_LAST_LAYER,
        VERDICT_LINEAR,
        VERDICT_NONLINEAR,
        VERDICT_NOT_LEARNABLE,
        BaselineError,
        Sample,
        dataset_from_records,
        split,
        standardize,
        _compact_features,
        _genuine_int,
        _last_layer_top1,
        _record_sample,
        _target_label,
    )
    from baseline_models import (
        logistic_baseline,
        majority_baseline,
        mlp_baseline,
        _model_report,
    )
    from baseline_eval import (
        escalation_gate,
        evaluate_baselines,
        _check_evaluation_knobs,
        _clean_router_records,
        _record_gate_problems,
        _threshold_accuracy,
        _verdict,
    )


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
