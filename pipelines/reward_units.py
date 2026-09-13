#!/usr/bin/env python3
"""Arithmetic reconciliation and unit-calibration extraction."""

from __future__ import annotations

from decimal import Decimal

if __package__:
    from .reward_mapping import (
        RewardOntologyError,
        _decimal,
        _json_number,
        _numeric_capture,
    )
    from .reward_policy import (
        CANONICAL_UNIT_USD,
        DECLARED_TOTAL_KEY,
        DEFAULT_TOLERANCE,
        NESTED_COMPONENT_KEY,
        REQUIRED_SEMANTICS,
        ROUNDING_DECIMALS_FIELD,
        ROUNDING_FIELDS,
        ROUNDING_RE,
        STRUCTURED_UNIT_FIELD,
        TEXT_UNIT_FIELD,
        UNWEIGHTED_EXCLUDE,
        USD_UNIT_RE,
        WEIGHTED_CONTAINERS,
        WEIGHT_ALIASES,
        WEIGHTS_FIELD,
    )
else:
    from reward_mapping import (
        RewardOntologyError,
        _decimal,
        _json_number,
        _numeric_capture,
    )
    from reward_policy import (
        CANONICAL_UNIT_USD,
        DECLARED_TOTAL_KEY,
        DEFAULT_TOLERANCE,
        NESTED_COMPONENT_KEY,
        REQUIRED_SEMANTICS,
        ROUNDING_DECIMALS_FIELD,
        ROUNDING_FIELDS,
        ROUNDING_RE,
        STRUCTURED_UNIT_FIELD,
        TEXT_UNIT_FIELD,
        UNWEIGHTED_EXCLUDE,
        USD_UNIT_RE,
        WEIGHTED_CONTAINERS,
        WEIGHT_ALIASES,
        WEIGHTS_FIELD,
    )


def _component_value(value):
    direct = _decimal(value)
    if direct is not None:
        return direct
    if isinstance(value, dict):
        return _decimal(value.get("value"))
    return None

def _reward_tolerance(reward) -> Decimal:
    decimals = reward.get(ROUNDING_DECIMALS_FIELD)
    if isinstance(decimals, bool) or not isinstance(decimals, int) or decimals < 0:
        decimals = None
        for key in ROUNDING_FIELDS:
            text = reward.get(key)
            if not isinstance(text, str):
                continue
            match = ROUNDING_RE.search(text)
            if match:
                decimals = _numeric_capture(match, integer=True)
                break
    if decimals is None:
        return DEFAULT_TOLERANCE
    rounded = Decimal("0.5") * (Decimal(10) ** -decimals)
    return max(DEFAULT_TOLERANCE, rounded)


def _weighted_component(containers, key):
    for container in containers:
        for alias in WEIGHT_ALIASES.get(key, (key,)):
            if alias in container:
                component = _component_value(container[alias])
                if component is not None:
                    return component
    return None


def _weighted_total(reward, weights):
    containers = [reward]
    containers.extend(
        reward[key]
        for key in WEIGHTED_CONTAINERS
        if isinstance(reward.get(key), dict)
    )
    terms = []
    missing = []
    for key, raw_weight in weights.items():
        weight = _decimal(raw_weight)
        if weight is None:
            continue
        component = _weighted_component(containers, key)
        if component is None:
            missing.append(key)
        else:
            terms.append(weight * component)
    if missing or not terms:
        return None
    return sum(terms, Decimal(0))


def _unweighted_siblings(reward, nested):
    return [
        component
        for key, value in reward.items()
        if key not in UNWEIGHTED_EXCLUDE and not (nested and key == NESTED_COMPONENT_KEY)
        for component in [_component_value(value)]
        if component is not None
    ]


def _unweighted_total(reward):
    component_container = reward.get(NESTED_COMPONENT_KEY)
    nested = isinstance(component_container, dict)
    siblings = _unweighted_siblings(reward, nested)
    if nested:
        if siblings:
            # Mixed legacy layout: publish-time validation sums the direct
            # numeric siblings while this nested map declares its own
            # components. Refuse to reconcile rather than claim an arithmetic
            # verdict the publish gate contradicts.
            return None
        values = [
            component
            for component in (
                _component_value(value) for value in component_container.values()
            )
            if component is not None
        ]
    else:
        values = siblings
    if not values:
        return None
    return sum(values, Decimal(0))


def assess_arithmetic(reward, pointer):
    """Return a machine-readable, conservative total reconciliation result."""
    base = {"json_pointer": pointer}
    if not isinstance(reward, dict):
        return {**base, "status": "unsupported", "method": "non_object_reward"}

    total = _decimal(reward.get(DECLARED_TOTAL_KEY))
    if total is None:
        return {**base, "status": "unsupported", "method": "no_numeric_total"}

    weights = reward.get(WEIGHTS_FIELD)
    if isinstance(weights, dict):
        recomputed = _weighted_total(reward, weights)
        method = "declared_weighted_sum"
    else:
        recomputed = _unweighted_total(reward)
        method = "unweighted_component_sum"
    if recomputed is None:
        return {
            **base,
            "status": "unsupported",
            "method": f"{method}_unresolved",
            "source_total": _json_number(total),
        }

    difference = abs(recomputed - total)
    tolerance = _reward_tolerance(reward)
    return {
        **base,
        "status": "valid" if difference <= tolerance else "invalid",
        "method": method,
        "source_total": _json_number(total),
        "recomputed_total": _json_number(recomputed),
        "absolute_difference": _json_number(difference),
        "tolerance": _json_number(tolerance),
    }


def _normalize_calibration(calibration):
    if calibration is None:
        return None
    if not isinstance(calibration, dict):
        raise RewardOntologyError("calibration must be an object")
    unit = _decimal(calibration.get("source_unit_usd"))
    evidence_ref = calibration.get("evidence_ref")
    if unit is None or unit <= 0:
        raise RewardOntologyError("calibration source_unit_usd must be positive")
    if not isinstance(evidence_ref, str) or not evidence_ref.strip():
        raise RewardOntologyError("calibration evidence_ref must be nonempty")
    factor = calibration.get("canonical_factor")
    if factor is not None:
        factor = _decimal(factor)
        if factor is None or factor <= 0 or factor != unit / CANONICAL_UNIT_USD:
            raise RewardOntologyError("calibration canonical_factor is inconsistent")
    return {
        "source_unit_usd": unit,
        "evidence_ref": evidence_ref.strip(),
    }


normalize_calibration = _normalize_calibration


def _text_unit_usd(reward):
    units_text = reward.get(TEXT_UNIT_FIELD)
    if not isinstance(units_text, str):
        return None
    match = USD_UNIT_RE.search(units_text)
    if not match:
        return None
    return _numeric_capture(match)


def _structured_unit_usd(reward):
    if STRUCTURED_UNIT_FIELD not in reward:
        return None, None
    structured = _decimal(reward.get(STRUCTURED_UNIT_FIELD))
    if structured is None or structured <= 0:
        return None, "invalid_structured_unit_usd"
    return structured, None


def _declared_unit_usd(reward):
    if not isinstance(reward, dict):
        return None, None, "unsupported_reward_object"
    parsed = _text_unit_usd(reward)
    structured, structured_error = _structured_unit_usd(reward)
    if structured_error:
        return None, None, structured_error
    if parsed is not None and parsed <= 0:
        return None, None, "invalid_text_unit_usd"
    if structured is not None and parsed is not None and structured != parsed:
        return None, None, "conflicting_unit_declarations"
    unit = structured if structured is not None else parsed
    in_record_unit = None
    units_text = reward.get(TEXT_UNIT_FIELD)
    if (
        unit is not None
        and isinstance(units_text, str)
        and REQUIRED_SEMANTICS in units_text.lower()
    ):
        in_record_unit = unit
    return unit, in_record_unit, None


def _calibrated_unit_usd(unit, in_record_unit, calibration):
    calibrated_unit = calibration["source_unit_usd"]
    if unit is not None and unit != calibrated_unit:
        return None, "calibration_evidence_conflict", None
    if in_record_unit is not None:
        return in_record_unit, "explicit_usd_unit_calibration", "source_reward_fields"
    return (
        calibrated_unit,
        "external_calibration_evidence",
        calibration["evidence_ref"],
    )


def _extract_unit_usd(reward, calibration=None):
    """Return (USD per native unit, status) from explicit, consistent evidence."""
    unit, in_record_unit, error = _declared_unit_usd(reward)
    if error:
        return None, error, None
    calibration = _normalize_calibration(calibration)
    if unit is not None and in_record_unit is None and calibration is None:
        return None, "missing_risk_adjusted_semantics", None
    if calibration is not None:
        return _calibrated_unit_usd(unit, in_record_unit, calibration)
    if unit is None:
        return None, "missing_unit_calibration", None
    if in_record_unit is None:
        return None, "missing_risk_adjusted_semantics", None
    return in_record_unit, "explicit_usd_unit_calibration", "source_reward_fields"
