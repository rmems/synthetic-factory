#!/usr/bin/env python3
"""Reward arithmetic and outcome-signal checks for the run validator."""

import math
import sys
from typing import NamedTuple

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling
    _assert_direct_sibling("validate_run_rewards")
    from . import validate_run_outcomes as _validate_run_outcomes
    from . import validate_run_spikes as _validate_run_spikes
else:
    # Join a qualified twin without importing pipelines during normal CLI use.
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "validate_run_rewards"
    )
    import validate_run_outcomes as _validate_run_outcomes
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


class RewardSettings(NamedTuple):
    """The arithmetic tolerance and bookkeeping vocabulary one check runs under.

    The validate_run facade builds this from its own live REWARD_TOL and
    REWARD_NON_COMPONENT_KEYS bindings, so rebinding either compatibility
    name there keeps affecting validation exactly as when the check lived
    inline. Siblings default to this module's bindings via
    :func:`default_settings`.
    """

    tolerance: float
    non_component_keys: frozenset


def default_settings():
    """This module's own settings, read at call time so patches here flow too."""
    return RewardSettings(REWARD_TOL, REWARD_NON_COMPONENT_KEYS)


def component_numeric(value):
    """Extract numeric component value from plain number or {value: number}."""
    if isinstance(value, dict):
        value = value.get("value")
    return float(value) if _validate_run_spikes.is_number(value) else None


# Metadata containers that are never scalar components; the sibling-sum loops
# skip these alongside the shared bookkeeping vocabulary above.
_SCALAR_CONTAINER_KEYS = frozenset(
    {"components", "components_executed", "components_realized", "ticks"}
)


def _scalar_items(rc, settings):
    """Yield the (key, value) pairs eligible as scalar arithmetic components."""
    skip = settings.non_component_keys | _SCALAR_CONTAINER_KEYS
    for k, v in rc.items():
        if k in skip:
            continue
        yield k, v


# Marker substrings of the two mismatch messages built in check_reward_total.
# check_records imports this tuple to drop the shape layer's arithmetic errors:
# it owns reward arithmetic and would otherwise report the same record twice.
REWARD_WEIGHTED_MISMATCH = "!= weighted sum"
REWARD_UNWEIGHTED_MISMATCH = "!= sum of components"
REWARD_ARITHMETIC_MARKERS = (REWARD_UNWEIGHTED_MISMATCH, REWARD_WEIGHTED_MISMATCH)


# Total reconciliation (weighted layouts plus dispatch) lives in
# validate_run_reward_total.check_reward_total; the helpers below serve it
# and check_records' arithmetic-error dedup.


def _sibling_component_sum(rc, settings):
    """Sum the numeric sibling components, skipping bookkeeping keys."""
    component_sum = 0.0
    has_component = False
    for _, v in _scalar_items(rc, settings):
        num = component_numeric(v)
        if num is not None:
            component_sum += num
            has_component = True
    return component_sum, has_component


def _nonfinite_component_error(key, value, where):
    """Report one non-finite component, or None when it is valid."""
    if component_numeric(value) is not None:
        return None
    if isinstance(value, dict) and "value" in value:
        target, suffix = value.get("value"), ".value"
    else:
        target, suffix = value, ""
    if isinstance(target, (int, float)) and not _validate_run_spikes.is_number(target):
        return f"{where}: reward_components.{key}{suffix} must be a finite number"
    return None


def _unweighted_mismatch(rc, total, where, settings):
    """Report the sibling-sum mismatch, if the layout has components."""
    component_sum, has_component = _sibling_component_sum(rc, settings)
    # Only enforce sum check when at least one numeric component exists
    # beyond total (otherwise total alone is allowed, e.g. minimal fixture).
    if not has_component:
        return []
    tol = settings.tolerance
    if math.isclose(float(total), component_sum, rel_tol=0.0, abs_tol=tol):
        return []
    return [
        f"{where}: reward_components.total {total} {REWARD_UNWEIGHTED_MISMATCH} {component_sum:.6g} (diff {abs(float(total) - component_sum):.6g} > {tol})"
    ]


def unweighted_errors(rc, total, where, settings=None):
    """Validate the unweighted layout against the sum of sibling components.

    ``settings`` defaults to this module's :func:`default_settings`;
    validate_run_reward_total threads the facade's live settings through.
    """
    settings = default_settings() if settings is None else settings
    errs = []
    for k, v in _scalar_items(rc, settings):
        error = _nonfinite_component_error(k, v, where)
        if error is not None:
            errs.append(error)
    return errs + _unweighted_mismatch(rc, total, where, settings)


def _container_children(path, value):
    """Child path/value pairs for one container node, else no children."""
    if isinstance(value, dict):
        return [(f"{path}.{key}", child) for key, child in value.items()]
    if isinstance(value, list):
        return [(f"{path}[{index}]", child) for index, child in enumerate(value)]
    return []


def _finite_number_errors(reward, where):
    """Walk one reward tree and report every non-finite float by path."""
    errors = []
    stack = [("reward", reward)]
    while stack:
        path, value = stack.pop()
        if isinstance(value, float) and not math.isfinite(value):
            errors.append(f"{where}: {path} must be a finite number")
        else:
            stack.extend(_container_children(path, value))
    return errors


def require_reward(obj, where):
    reward = obj.get("reward")
    if not isinstance(reward, dict):
        return [f"{where}: reward must be an object with 'success'"]
    if "success" not in reward:
        return [f"{where}: reward missing 'success'"]
    if not isinstance(reward["success"], bool):
        return [f"{where}: reward.success must be a boolean"]
    return _finite_number_errors(reward, where)


# Observable outcome signals live in validate_run_outcomes; the arithmetic
# sibling rebinds the entry point so existing callers keep resolving
# validate_run_rewards.terminal_outcome_agrees unchanged.
terminal_outcome_agrees = _validate_run_outcomes.terminal_outcome_agrees


if __package__:
    _expose_package_sibling(__name__)
