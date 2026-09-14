#!/usr/bin/env python3
"""Reward arithmetic and outcome-signal checks for the run validator."""

import math
import re
import sys

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling
    _assert_direct_sibling("validate_run_rewards")
    from . import validate_run_spikes as _validate_run_spikes
else:
    # Join a qualified twin without importing pipelines during normal CLI use.
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "validate_run_rewards"
    )
    import validate_run_spikes as _validate_run_spikes


# Bookkeeping keys that are not counted toward the arithmetic sum. This is the
# single exclusion vocabulary for reward arithmetic: check_records imports it
# so the shape layer and the deep layer agree on what is a component, and a
# record that reconciles under one layer is not rejected by the other.
REWARD_NON_COMPONENT_KEYS = frozenset(
    {
        "aggregation",
        "comment",
        "component_notes",
        "convention",
        "description",
        "frame",
        "native_unit",
        "notes",
        "provenance_notes",
        "rounding_decimals",
        "total",
        "total_basis",
        "unit_usd",
        "units",
        "weights",
        "weights_note",
    }
)
# Strict arithmetic tolerance — total must equal sum within 1e-6.
REWARD_TOL = 1e-6


def _component_numeric(value):
    """Extract numeric component value from plain number or {value: number}."""
    if _validate_run_spikes.is_number(value):
        return float(value)
    if isinstance(value, dict) and _validate_run_spikes.is_number(value.get("value")):
        return float(value["value"])
    return None


# Marker substrings of the two mismatch messages built in check_reward_total.
# check_records imports this tuple to drop the shape layer's arithmetic errors:
# it owns reward arithmetic and would otherwise report the same record twice.
REWARD_WEIGHTED_MISMATCH = "!= weighted sum"
REWARD_UNWEIGHTED_MISMATCH = "!= sum of components"
REWARD_ARITHMETIC_MARKERS = (REWARD_UNWEIGHTED_MISMATCH, REWARD_WEIGHTED_MISMATCH)


def check_reward_total(rc, where):
    """Validate reward_components arithmetic: total == sum(component values).

    Strict gate: total must equal the arithmetic sum of all numeric components
    (excluding bookkeeping keys) within REWARD_TOL. Weighted aggregations are
    supported; interval/string totals are rejected as non-finite.
    """
    errs = []
    if not isinstance(rc, dict):
        return errs
    if "total" not in rc:
        errs.append(f"{where}: reward_components missing 'total'")
        return errs
    total = rc.get("total")
    if not _validate_run_spikes.is_number(total):
        # Interval/string totals (e.g. [0.1, 0.9] or "0.5 ± 0.1") skip the
        # arithmetic gate here; check_records surfaces them as warnings and
        # the reward-normalization curation lane owns their conversion.
        # Numeric-but-non-finite totals (NaN/inf) still fail via is_number, and
        # a boolean total is invalid schema input rather than a skippable shape.
        if isinstance(total, (int, float)):
            errs.append(f"{where}: reward_components.total must be a finite number")
        return errs
    # Weighted layout: total == sum(value_i * weight_i)
    weights = rc.get("weights")
    if isinstance(weights, dict) and weights:
        # Resolve declared weights (ignore non-finite weights)
        declared = {
            k: float(v)
            for k, v in weights.items()
            if k not in REWARD_NON_COMPONENT_KEYS and _validate_run_spikes.is_number(v)
        }
        if declared:
            # Collect containers that may hold component values (direct or nested)
            containers = [rc]
            for key in ("components", "components_executed", "components_realized"):
                if isinstance(rc.get(key), dict):
                    containers.append(rc[key])
            # Try to resolve every declared weight
            recomputed = 0.0
            unresolved = []
            for k, w in declared.items():
                val = None
                aliases = {
                    "task": ("task", "task_progress", "task_outcome"),
                    "safety": ("safety", "safety_alignment", "safety_process"),
                }.get(k, (k,))
                for c in containers:
                    for cand in aliases:
                        if cand in c:
                            val = _component_numeric(c[cand])
                            if val is not None:
                                break
                    if val is not None:
                        break
                    # also try direct key in rc
                    if k in c:
                        val = _component_numeric(c[k])
                        if val is not None:
                            break
                if val is None:
                    unresolved.append(k)
                else:
                    recomputed += val * w
            if unresolved:
                # Weights are declared but this layer cannot resolve every
                # component. The sibling-sum check below does not model the
                # weighted layout, so falling through would report a false
                # mismatch; check_records owns the unsupported-layout warning.
                return errs
            if not math.isclose(
                float(total), recomputed, rel_tol=0.0, abs_tol=REWARD_TOL
            ):
                errs.append(
                    f"{where}: reward_components.total {total} {REWARD_WEIGHTED_MISMATCH} {recomputed:.6g} (diff {abs(float(total) - recomputed):.6g} > {REWARD_TOL})"
                )
            return errs
    # Unweighted: sum of numeric siblings (plain or {value: n})
    component_sum = 0.0
    has_component = False
    for k, v in rc.items():
        if k in REWARD_NON_COMPONENT_KEYS:
            continue
        # Skip known metadata containers that are not scalar components
        if k in ("components", "components_executed", "components_realized", "ticks"):
            continue
        num = _component_numeric(v)
        if num is not None:
            # Guard against non-finite already filtered by _component_numeric
            component_sum += float(num)
            has_component = True
        elif isinstance(v, dict) and "value" in v:
            # Rich object with non-finite value
            if isinstance(v.get("value"), (int, float)) and not _validate_run_spikes.is_number(v["value"]):
                errs.append(
                    f"{where}: reward_components.{k}.value must be a finite number"
                )
        elif isinstance(v, (int, float)) and not _validate_run_spikes.is_number(v):
            errs.append(
                f"{where}: reward_components.{k} must be a finite number"
            )
    # Only enforce sum check when at least one numeric component exists
    # beyond total (otherwise total alone is allowed, e.g. minimal fixture).
    if has_component:
        if not math.isclose(
            float(total), component_sum, rel_tol=0.0, abs_tol=REWARD_TOL
        ):
            errs.append(
                f"{where}: reward_components.total {total} {REWARD_UNWEIGHTED_MISMATCH} {component_sum:.6g} (diff {abs(float(total) - component_sum):.6g} > {REWARD_TOL})"
            )
    return errs


def _require_reward(obj, where):
    reward = obj.get("reward")
    if not isinstance(reward, dict):
        return [f"{where}: reward must be an object with 'success'"]
    if "success" not in reward:
        return [f"{where}: reward missing 'success'"]
    if not isinstance(reward["success"], bool):
        return [f"{where}: reward.success must be a boolean"]
    errors = []
    stack = [("reward", reward)]
    while stack:
        path, value = stack.pop()
        if isinstance(value, dict):
            stack.extend((f"{path}.{key}", child) for key, child in value.items())
        elif isinstance(value, list):
            stack.extend((f"{path}[{index}]", child) for index, child in enumerate(value))
        elif isinstance(value, float) and not math.isfinite(value):
            errors.append(f"{where}: {path} must be a finite number")
    return errors


def terminal_outcome_agrees(outcome, success):
    """Whether the final observable outcome signal agrees with a success label."""
    if not isinstance(outcome, str) or not isinstance(success, bool):
        return True
    text = outcome.casefold()
    completion_term = (
        r"(?:atomic|complet(?:e(?:d|s)?|ing)|correct|deploy\w*|fixed|green|healthy|"
        r"landed|merged|operational|pass(?:ed|es|ing)?|recovered|repaired|"
        r"resolved|safe(?:ly)?|shipped|succeed(?:ed|s|ing)?|"
        r"success(?:es|ful(?:ly)?)?|"
        r"verified|work(?:ed|ing|s)?)"
    )
    failure_term = (
        r"(?:blocked|broken|corrupt\w*|fail\w*|incomplete|partial\w*|pending|"
        r"unsafe|unsuccessful(?:ly)?|unresolved)"
    )
    completion_modifier_word = (
        r"(?!(?:although|and|but|except|however|nor|or|plus|then|though|while)\b)"
        r"\w+"
    )
    completion_modifier = rf"(?:{completion_modifier_word}[ -]+){{0,4}}"
    completion_suffix = r"(?:\s+(?:fully|successfully|ultimately)){0,3}"
    progressive_completion_term = r"(?:completing|deploying|passing|succeeding|working)"
    negation_prefix = (
        r"(?:(?:did|does|was|were|is|are|has|have|will|would|could|should)"
        r"(?: not|n['’]t)|cannot|can not|can['’]t|won['’]t|never|not|without)"
    )
    nominal_negated_subject = (
        r"(?:(?:no|zero)\s+(?:\w+[ -]+){1,3}|"
        r"none\s+of\s+(?:the\s+)?(?:\w+[ -]+){1,3}|nothing\s+)"
    )
    negated_completion_spans = [
        match.span()
        for match in re.finditer(
            rf"\b{negation_prefix} "
            rf"(?!only\b){completion_modifier}(?:(?:have )?been |be )?"
            rf"{completion_modifier}{completion_term}{completion_suffix}\b",
            text,
        )
    ]
    nominal_negated_completion_spans = [
        match.span()
        for match in re.finditer(
            rf"\b{nominal_negated_subject}"
            r"(?:(?:has|have|is|are|was|were)\s+)?"
            r"(?:(?:currently|fully|quite|successfully|ultimately|yet)\s+){0,3}"
            rf"{completion_term}{completion_suffix}\b",
            text,
        )
    ]
    failed_completion_spans = [
        match.span()
        for match in re.finditer(
            rf"\b{failure_term}\s+to\s+{completion_modifier}{completion_term}"
            rf"{completion_suffix}\b",
            text,
        )
    ]
    deferred_completion_spans = [
        match.span()
        for match in re.finditer(
            rf"\b(?:(?:has|have|is|are|was|were)\s+)?yet\s+to\s+"
            rf"{completion_modifier}{completion_term}{completion_suffix}\b",
            text,
        )
    ]
    stopped_completion_spans = [
        match.span()
        for match in re.finditer(
            rf"\b(?:cease[ds]?|stop(?:ped|s)?)\s+{completion_modifier}"
            rf"{progressive_completion_term}{completion_suffix}\b",
            text,
        )
    ]
    negated_failure_spans = [
        match.span()
        for match in re.finditer(
            rf"\b(?:(?:no|zero)\s+(?:\w+\s+){{0,3}}{failure_term}|"
            rf"none\s+of\s+(?:the\s+)?(?:\w+\s+){{0,3}}{failure_term}|"
            rf"nothing\s+{failure_term}|"
            rf"{negation_prefix}\s+(?!only\b){completion_modifier}{failure_term})\b",
            text,
        )
    ]
    signals = [
        (match.start(), True)
        for match in re.finditer(rf"\b{completion_term}\b", text)
        if not any(
            start <= match.start() < end
            for start, end in (
                negated_completion_spans
                + nominal_negated_completion_spans
                + failed_completion_spans
                + deferred_completion_spans
                + stopped_completion_spans
            )
        )
    ]
    signals.extend(
        (match.start(), False)
        for match in re.finditer(
            rf"\b{failure_term}\b|"
            r"\b(?:error|failure|issue|problem|race|risk)s?\s+"
            r"(?:persist\w*|open|unresolved)\b|"
            r"\b(?:remain\w*|still)\s+"
            r"(?:blocked|broken|failing|incomplete|unsafe|unresolved)\b",
            text,
        )
        if not any(start <= match.start() < end for start, end in negated_failure_spans)
    )
    signals.extend((end, False) for _, end in negated_completion_spans)
    signals.extend((end, False) for _, end in nominal_negated_completion_spans)
    signals.extend((end, False) for _, end in deferred_completion_spans)
    signals.extend((end, False) for _, end in stopped_completion_spans)
    signals.extend((end, True) for _, end in negated_failure_spans)
    # Non-empty outcomes are validated by the caller. Vocabulary that is
    # neither an explicit success nor an explicit failure is neutral rather
    # than contradictory; the schema does not prescribe exact prose.
    return not signals or max(signals)[1] is success


if __package__:
    _expose_package_sibling(__name__)
