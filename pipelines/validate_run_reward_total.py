#!/usr/bin/env python3
"""Reward-total reconciliation: weighted and dispatched total checks."""

import math
import sys

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling
    _assert_direct_sibling("validate_run_reward_total")
    from . import validate_run_rewards as _validate_run_rewards
    from . import validate_run_spikes as _validate_run_spikes
else:
    # Join a qualified twin without importing pipelines during normal CLI use.
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "validate_run_reward_total"
    )
    import validate_run_rewards as _validate_run_rewards
    import validate_run_spikes as _validate_run_spikes


def _declared_weights(rc, settings):
    """Resolve declared weights, ignoring non-finite weights."""
    weights = rc.get("weights")
    if not isinstance(weights, dict) or not weights:
        return {}
    return {
        k: float(v)
        for k, v in weights.items()
        if k not in settings.non_component_keys
        and _validate_run_spikes.is_number(v)
    }


def _search_weight_container(container, key, aliases):
    """Find one weight's numeric value inside a single container."""
    for candidate in aliases:
        if candidate in container:
            value = _validate_run_rewards.component_numeric(container[candidate])
            if value is not None:
                return value
    # also try direct key in rc
    if key in container:
        return _validate_run_rewards.component_numeric(container[key])
    return None


def _weight_containers(rc):
    """Collect the containers that may hold component values."""
    containers = [rc]
    for name in ("components", "components_executed", "components_realized"):
        if isinstance(rc.get(name), dict):
            containers.append(rc[name])
    return containers


def _resolve_weighted_value(rc, key):
    """Find one declared weight's component value across the containers."""
    aliases = {
        "task": ("task", "task_progress", "task_outcome"),
        "safety": ("safety", "safety_alignment", "safety_process"),
    }.get(key, (key,))
    for container in _weight_containers(rc):
        value = _search_weight_container(container, key, aliases)
        if value is not None:
            return value
    return None


def _weighted_errors(rc, declared, where, settings):
    """Validate the weighted layout against the recomputed weighted sum."""
    total = rc["total"]
    tol = settings.tolerance
    recomputed = 0.0
    unresolved = []
    for key, weight in declared.items():
        value = _resolve_weighted_value(rc, key)
        if value is None:
            unresolved.append(key)
        else:
            recomputed += value * weight
    if unresolved:
        # Weights are declared but this layer cannot resolve every
        # component. The sibling-sum check does not model the weighted
        # layout, so falling through would report a false mismatch;
        # check_records owns the unsupported-layout warning.
        return []
    if not math.isclose(float(total), recomputed, rel_tol=0.0, abs_tol=tol):
        return [
            f"{where}: reward_components.total {total} {_validate_run_rewards.REWARD_WEIGHTED_MISMATCH} {recomputed:.6g} (diff {abs(float(total) - recomputed):.6g} > {tol})"
        ]
    return []


def check_reward_total(rc, where, settings=None):
    """Validate reward_components arithmetic: total == sum(component values).

    Strict gate: total must equal the arithmetic sum of all numeric components
    (excluding bookkeeping keys) within REWARD_TOL. Weighted aggregations are
    supported; interval/string totals are rejected as non-finite.

    ``settings`` (a validate_run_rewards.RewardSettings) defaults to that
    module's REWARD_TOL and REWARD_NON_COMPONENT_KEYS; the validate_run facade
    passes its own live bindings so rebinding the facade-level compatibility
    names keeps affecting validation, exactly as when the check lived inline.
    """
    settings = _validate_run_rewards.default_settings() if settings is None else settings
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
    declared = _declared_weights(rc, settings)
    if declared:
        # Weighted layout: total == sum(value_i * weight_i). A declared
        # weighted layout owns the verdict; the sibling-sum check below does
        # not model it.
        return _weighted_errors(rc, declared, where, settings)
    # Unweighted: sum of numeric siblings (plain or {value: n}).
    return _validate_run_rewards.unweighted_errors(rc, total, where, settings)


if __package__:
    _expose_package_sibling(__name__)
