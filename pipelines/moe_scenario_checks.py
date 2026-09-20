#!/usr/bin/env python3
"""Scenario checks for ``moe-router-distillation-trajectories`` records.

Split out of ``moe_check.py`` verbatim: the recorded context digest, the
compact-input shape, the feature recompute against ``featurize``, and the
scenario-context binding the teacher and replay checks are read through.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path
from typing import Any

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from oracle_grounded import distill_contract as oc  # noqa: E402
if __package__:
    from .moe_featurizer import (
        COMPACT_SUMMARY_STATS,
        FEATURIZER_ID,
        MAX_RECOMPUTE_DIM,
        compact_view,
        featurize,
    )
else:
    from moe_featurizer import (
        COMPACT_SUMMARY_STATS,
        FEATURIZER_ID,
        MAX_RECOMPUTE_DIM,
        compact_view,
        featurize,
    )


def _check_context_digest(scenario: dict[str, Any], where: str) -> list[str]:
    """The student-visible context and the digest that pins it."""

    context = scenario.get("context")
    if not isinstance(context, str) or not context.strip():
        return [f"{where}.scenario.context must be a non-empty string"]
    if scenario.get("context_sha256") != hashlib.sha256(
        context.encode("utf-8")
    ).hexdigest():
        return [f"{where}.scenario.context_sha256 does not match the context"]
    return []

def _check_compact_input(scenario: dict[str, Any], where: str) -> list[str]:
    """The compact student input the baseline is evaluated on."""

    compact = scenario.get("compact_input")
    if not isinstance(compact, dict):
        return [f"{where}.scenario.compact_input must be an object"]
    features = compact.get("features")
    if not isinstance(features, list) or not features:
        return [
            f"{where}.scenario.compact_input.features must carry the "
            "student input the baseline is evaluated on"
        ]
    if not all(oc.is_number(value) for value in features):
        # router_baseline silently skips a record whose features are not
        # finite numbers, so without this a curated corpus could contain
        # no usable student input at all.
        return [
            f"{where}.scenario.compact_input.features must be finite "
            "numbers — the baseline extractor drops anything else"
        ]
    declared = compact.get("compact_dim")
    if isinstance(declared, int) and not isinstance(declared, bool):
        expected = declared + COMPACT_SUMMARY_STATS
        if len(features) != expected:
            return [
                f"{where}.scenario.compact_input.features has "
                f"{len(features)} values but compact_dim {declared} "
                f"declares {expected}"
            ]
    return _check_compact_recompute(scenario, compact, features, where)

def _positive_dim(value: Any, floor: int) -> int | None:
    if (
        isinstance(value, int)
        and not isinstance(value, bool)
        and floor <= value <= MAX_RECOMPUTE_DIM
    ):
        return value
    return None

def _check_compact_recompute(
    scenario: dict[str, Any],
    compact: dict[str, Any],
    features: list[Any],
    where: str,
) -> list[str]:
    """The features must recompute from the context they claim to describe.

    Width and finiteness alone let a correctly rehashed record replace the
    student input with arbitrary finite values of the same length while
    ``router_baseline`` consumes them as the input paired with the teacher's
    label — a corrupted input-label pairing that could change the baseline
    and the escalation verdict. The featurizer is deterministic, so the
    validator recomputes ``compact_view(featurize(context))`` instead of
    trusting the vector.
    """

    if compact.get("featurizer") != FEATURIZER_ID:
        return [
            f"{where}.scenario.compact_input.featurizer must be "
            f"{FEATURIZER_ID!r} so the student input can be recomputed, got "
            f"{compact.get('featurizer')!r}"
        ]
    feature_dim = _positive_dim(compact.get("feature_dim"), 4)
    compact_dim = _positive_dim(compact.get("compact_dim"), 1)
    if feature_dim is None or compact_dim is None:
        return [
            f"{where}.scenario.compact_input must declare integer "
            f"feature_dim (4..{MAX_RECOMPUTE_DIM}) and compact_dim "
            f"(1..{MAX_RECOMPUTE_DIM}) so the student input can be recomputed"
        ]
    context = scenario.get("context")
    if not isinstance(context, str) or not context.strip():
        # Reported by the context-digest check; nothing to recompute from.
        return []
    expected = compact_view(featurize(context, feature_dim), compact_dim)
    if len(features) != len(expected) or any(
        abs(float(value) - target) > 1e-9
        for value, target in zip(features, expected)
    ):
        return [
            f"{where}.scenario.compact_input.features: "
            "COMPACT_INPUT_NOT_REPRODUCIBLE — the recorded features do not "
            "recompute from the context with the declared featurizer"
        ]
    return []

def _check_scenario_context(scenario: Any, where: str) -> list[str]:
    """The student-visible context, its digest, and the compact input."""

    if not isinstance(scenario, dict):
        return []
    return _check_context_digest(scenario, where) + _check_compact_input(
        scenario, where
    )
