#!/usr/bin/env python3
"""Dataset extraction for the MoE-router baseline gate.

Turns validated moe-router distillation records into labelled ``Sample``s,
splits them deterministically, and standardises compact features."""

from __future__ import annotations

import hashlib
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from oracle_grounded import distill_contract as oc  # noqa: E402

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
        if sample is not None:
            _append_new_sample(samples, sampled_ids, sample)
    _check_consistent_width(samples)
    return samples


def _append_new_sample(
    samples: list[Sample], sampled_ids: set[str], sample: Sample
) -> None:
    if sample.record_id in sampled_ids:
        # The id is the record's identity: two rows sharing one cannot
        # be attributed, weighted, or audited separately.
        raise BaselineError(
            f"duplicate record id {sample.record_id!r}; a corpus cannot "
            "carry the same record twice"
        )
    sampled_ids.add(sample.record_id)
    samples.append(sample)


def _check_consistent_width(samples: list[Sample]) -> None:
    if not samples:
        return
    width = len(samples[0].features)
    if any(len(sample.features) != width for sample in samples):
        raise BaselineError("compact inputs have inconsistent width")


def _record_sample(record: Any, target: str) -> Sample | None:
    """One record's (id, compact input, label), or None if it has no sample."""

    fields = _record_fields(record)
    if fields is None:
        return None
    record_id, scenario, result = fields
    if result.get("status") != oc.RESULT_MEASURED:
        # An abstained result's routing fields are outcomes the oracle
        # explicitly declined to stand behind; they must never become labels.
        return None
    features = _compact_features(scenario)
    label = _target_label(result, target) if features is not None else None
    if features is None or label is None:
        return None
    return Sample(record_id=record_id, features=features, label=label)


def _record_fields(record: Any) -> tuple[str, dict[str, Any], dict[str, Any]] | None:
    """The (id, scenario, result) of a record that could carry a sample."""

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
    return record_id, scenario, result


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
        # Signed zeros are the same model input and must share a split key.
        key = ",".join(repr(value if value else 0.0) for value in sample.features)
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
    variances = _feature_scales(train, width, means)

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


def _feature_scales(
    train: list[Sample], width: int, means: list[float]
) -> list[float]:
    """Per-feature stddev fitted on the training split (1.0 for constants)."""

    scales = []
    for i in range(width):
        total = sum((sample.features[i] - means[i]) ** 2 for sample in train)
        scales.append(math.sqrt(total / len(train)) or 1.0)
    return scales


