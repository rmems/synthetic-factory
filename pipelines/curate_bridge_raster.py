#!/usr/bin/env python3
"""Fail-closed raster, spike-gate, routing, and energy validation."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


RASTER_WINDOW_MIN_MS = 20
RASTER_WINDOW_MAX_MS = 50
RASTER_ENERGY_PJ_PER_SPIKE = 23
RASTER_ENERGY_UJ_PER_SPIKE = 23e-6
REASON_RASTER_WINDOW = "BRIDGE_RASTER_WINDOW_INVALID"
REASON_RASTER_SPIKE_BUDGET = "BRIDGE_SPIKE_BUDGET_MISMATCH"
REASON_RASTER_ENERGY = "BRIDGE_ENERGY_MISMATCH"
REASON_RASTER_ROUTING = "BRIDGE_RASTER_ROUTING_MISSING"
REASON_RASTER_EXCERPT = "BRIDGE_RASTER_EXCERPT_INVALID"
REASON_THIRD_FACTOR_INVALID = "BRIDGE_THIRD_FACTOR_ROUTING_INVALID"
REASON_GATE_SNN_INVALID = "BRIDGE_GATE_SNN_SPEC_INVALID"


def _finite_float(value: Any) -> float | None:
    try:
        result = float(value)
    except (OverflowError, TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _is_finite_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and _finite_float(value) is not None
    )


def _expected_spikes(neurons: int, mean_rate_hz: float, window_s: float) -> int | None:
    try:
        product = float(neurons) * float(mean_rate_hz) * float(window_s)
    except OverflowError:
        return None
    if not math.isfinite(product):
        return None
    try:
        return int(round(product))
    except (OverflowError, ValueError):
        return None


def _spike_energy(spikes: int, per_spike: float) -> float | None:
    count = _finite_float(spikes)
    if count is None:
        return None
    return _finite_float(count * per_spike)


@dataclass(frozen=True)
class _PositiveAliases:
    """Presence-aware positive aliases expressed in the primary unit."""

    primary: Any
    alias: Any
    primary_declared: bool
    alias_declared: bool
    valid: bool
    consistent: bool


@dataclass(frozen=True)
class _ValidationState:
    """Mutable validation accumulators passed as one bounded argument."""

    reason_codes: list[str]
    evidence: dict[str, Any]


def _alias_pair_valid(aliases: _PositiveAliases) -> bool:
    return all((aliases.valid, aliases.consistent))


def _validation_state(reason_codes: list[str], evidence: dict[str, Any]) -> _ValidationState:
    return _ValidationState(reason_codes, evidence)


def _positive_number(value: Any) -> bool:
    return _is_finite_number(value) and float(value) > 0


def _positive_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _nonnegative_int(value: Any) -> bool:
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and value >= 0
        and _finite_float(value) is not None
    )


def _nonnegative_json_integer(value: Any) -> int | None:
    """Return the integer value represented by one JSON number.

    JSON Schema treats finite integral-valued numbers such as ``800.0`` and
    ``8e2`` as integers.  Python's JSON decoder represents those spellings as
    ``float``, so excerpt validation must normalize them explicitly to stay in
    lockstep with the published schema.
    """

    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value >= 0 else None
    if not isinstance(value, float):
        return None
    if not math.isfinite(value):
        return None
    if not value.is_integer():
        return None
    integer = int(value)
    return integer if integer >= 0 else None


def _nonblank_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _positive_aliases(
    container: dict[str, Any], primary_key: str, alias_key: str, *, alias_scale: float
) -> _PositiveAliases:
    """Resolve two positive aliases without treating explicit null as absent."""

    primary_declared = primary_key in container
    alias_declared = alias_key in container
    primary = container.get(primary_key)
    alias = container.get(alias_key)
    if not primary_declared and _positive_number(alias):
        primary = float(alias) * alias_scale
    if not alias_declared and _positive_number(primary):
        alias = float(primary) / alias_scale
    valid = _positive_number(primary) and _positive_number(alias)
    consistent = valid and abs(float(primary) - float(alias) * alias_scale) <= 1e-9
    return _PositiveAliases(primary, alias, primary_declared, alias_declared, valid, consistent)


def _record_alias_derivation(
    aliases: _PositiveAliases,
    *,
    primary_evidence_key: str,
    alias_evidence_key: str,
    evidence: dict[str, Any],
) -> None:
    if aliases.primary_declared:
        if not aliases.alias_declared and aliases.valid:
            evidence[alias_evidence_key] = aliases.alias
        return
    if aliases.alias_declared and aliases.valid:
        evidence[primary_evidence_key] = aliases.primary


def _mark_invalid(
    reason_codes: list[str], evidence: dict[str, Any], reason: str, evidence_key: str
) -> None:
    reason_codes.append(reason)
    evidence[evidence_key] = False


def _validate_third_factor(
    third_factor: Any, *, reason_codes: list[str], evidence: dict[str, Any]
) -> None:
    """Validate one population's neuromodulatory routing entry."""

    evidence["raster_third_factor_present"] = True
    if not isinstance(third_factor, dict):
        reason_codes.append(REASON_THIRD_FACTOR_INVALID)
        evidence["raster_third_factor_valid"] = False
        evidence["raster_third_factor_error"] = "third_factor must be an object"
        return
    modulator = third_factor.get("modulator")
    tau = _positive_aliases(third_factor, "tau_e_s", "tau_e_ms", alias_scale=0.001)
    _record_alias_derivation(
        tau,
        primary_evidence_key="raster_third_factor_tau_e_s_derived",
        alias_evidence_key="raster_third_factor_tau_e_ms_derived",
        evidence=evidence,
    )
    if tau.primary_declared and tau.alias_declared:
        evidence["raster_third_factor_tau_consistent"] = tau.consistent
    eligibility = third_factor.get("eligibility")
    valid = all((_nonblank_text(modulator), _nonblank_text(eligibility), _alias_pair_valid(tau)))
    if not valid:
        _mark_invalid(
            reason_codes, evidence, REASON_THIRD_FACTOR_INVALID, "raster_third_factor_valid"
        )
        return
    evidence["raster_third_factor_valid"] = True
    evidence["raster_third_factor_modulator"] = modulator
    evidence["raster_third_factor_tau_e_s"] = float(tau.primary)
    evidence["raster_third_factor_eligibility"] = eligibility.strip()


def _raster_window(
    raster: dict[str, Any], reason_codes: list[str], evidence: dict[str, Any]
) -> tuple[float | None, float | None, bool]:
    window = _positive_aliases(raster, "window_s", "window_ms", alias_scale=0.001)
    invalid_declared = [
        evidence_key
        for declared, value, evidence_key in (
            (window.primary_declared, window.primary, "raster_declared_window_s_valid"),
            (window.alias_declared, window.alias, "raster_declared_window_ms_valid"),
        )
        if declared and not _is_finite_number(value)
    ]
    for evidence_key in invalid_declared:
        _mark_invalid(reason_codes, evidence, REASON_RASTER_WINDOW, evidence_key)
    _record_alias_derivation(
        window,
        primary_evidence_key="raster_window_s_derived",
        alias_evidence_key="raster_window_ms_derived",
        evidence=evidence,
    )
    in_range = window.valid and (
        RASTER_WINDOW_MIN_MS - 1e-9 <= float(window.alias) <= RASTER_WINDOW_MAX_MS + 1e-9
    )
    valid = in_range and window.consistent
    evidence["raster_window_ms"] = window.alias
    evidence["raster_window_valid"] = valid
    evidence["raster_window_consistent"] = bool(window.consistent)
    if not valid:
        reason_codes.append(REASON_RASTER_WINDOW)
        return None, None, False
    evidence["raster_window_ms"] = float(window.alias)
    evidence["raster_window_s"] = float(window.primary)
    return float(window.primary), float(window.alias), True


def _raster_spike_budget(
    raster: dict[str, Any],
    window_s: float | None,
    reason_codes: list[str],
    evidence: dict[str, Any],
) -> tuple[Any, Any, bool]:
    neurons = raster.get("neurons")
    rate = raster.get("mean_rate_hz")
    spikes = raster.get("spikes")
    fields = (
        ("raster_neurons", "raster_neurons_valid", neurons, _positive_int(neurons)),
        ("raster_rate_hz", "raster_rate_valid", _finite_float(rate), _positive_number(rate)),
        ("raster_spikes", "raster_spikes_valid", spikes, _nonnegative_int(spikes)),
    )
    for value_key, valid_key, value, valid in fields:
        evidence[valid_key] = valid
        if valid:
            evidence[value_key] = value
    validity = tuple(field[3] for field in fields)
    reason_codes.extend([REASON_RASTER_SPIKE_BUDGET] * validity.count(False))
    ready = all((*validity, window_s is not None))
    if not ready:
        return neurons, spikes, False
    expected = _expected_spikes(neurons, float(rate), window_s)
    evidence["raster_expected_spikes"] = expected
    evidence["raster_spike_budget_tolerance"] = 1
    valid = expected is not None and abs(spikes - expected) <= 1
    evidence["raster_spike_budget_valid"] = valid
    if not valid:
        reason_codes.append(REASON_RASTER_SPIKE_BUDGET)
    return neurons, spikes, True


def _raster_energy_field(
    value: Any,
    expected: float | int | None,
    tolerance: float,
) -> bool:
    return (
        expected is not None
        and _is_finite_number(value)
        and float(value) >= 0
        and abs(float(value) - float(expected)) <= tolerance
    )


def _invalid_declared_energy_keys(raster: dict[str, Any]) -> list[str]:
    declared = (
        ("energy_pJ", "raster_declared_energy_pJ_valid"),
        ("energy_uJ", "raster_declared_energy_uJ_valid"),
    )
    return [
        evidence_key
        for key, evidence_key in declared
        if all((key in raster, not _is_finite_number(raster.get(key))))
    ]


def _raster_energy_checks(spikes: Any) -> tuple[tuple[Any, ...], ...]:
    expected_pj = spikes * RASTER_ENERGY_PJ_PER_SPIKE
    comparable_pj = _finite_float(expected_pj)
    expected_uj = _spike_energy(spikes, RASTER_ENERGY_UJ_PER_SPIKE)
    return (
        (
            "energy_pJ",
            comparable_pj,
            1e-6,
            "raster_expected_energy_pJ",
            expected_pj if comparable_pj is not None else None,
            "raster_energy_pJ_valid",
        ),
        (
            "energy_uJ",
            expected_uj,
            1e-9,
            "raster_expected_energy_uJ",
            expected_uj,
            "raster_energy_uJ_valid",
        ),
    )


def _validate_raster_energy(
    raster: dict[str, Any],
    spikes: Any,
    budget_ready: bool,
    state: _ValidationState,
) -> None:
    for evidence_key in _invalid_declared_energy_keys(raster):
        _mark_invalid(
            state.reason_codes,
            state.evidence,
            REASON_RASTER_ENERGY,
            evidence_key,
        )
    if not budget_ready:
        return
    checks = _raster_energy_checks(spikes)
    results = [
        (
            expected_key,
            expected_value,
            evidence_key,
            _raster_energy_field(raster[key], expected, tolerance),
        )
        for key, expected, tolerance, expected_key, expected_value, evidence_key in checks
        if all((key in raster, _is_finite_number(raster.get(key))))
    ]
    for expected_key, expected_value, evidence_key, valid in results:
        state.evidence[expected_key] = expected_value
        state.evidence[evidence_key] = valid
    invalid_count = sum(not result[3] for result in results)
    state.reason_codes.extend([REASON_RASTER_ENERGY] * invalid_count)


def _valid_routing_entry(entry: Any) -> bool:
    if not isinstance(entry, dict):
        return False
    if not _nonblank_text(entry.get("from")):
        return False
    if not _nonblank_text(entry.get("to")):
        return False
    return _is_finite_number(entry.get("weight"))


def _routing_table(table: Any) -> tuple[list[dict[str, Any]], list[int]]:
    if isinstance(table, list):
        valid = [entry for entry in table if _valid_routing_entry(entry)]
        invalid = [index for index, entry in enumerate(table) if not _valid_routing_entry(entry)]
        return valid, invalid
    return [], [0] if table is not None else []


def _routing_endpoints_valid(routing: dict[str, Any]) -> bool:
    return all(
        (
            _nonblank_text(routing.get("source")),
            _nonblank_text(routing.get("target")),
        )
    )


def _validate_routing_third_factor(routing: dict[str, Any], state: _ValidationState) -> None:
    if "third_factor" in routing:
        _validate_third_factor(
            routing["third_factor"],
            reason_codes=state.reason_codes,
            evidence=state.evidence,
        )
        return
    _mark_invalid(
        state.reason_codes,
        state.evidence,
        REASON_THIRD_FACTOR_INVALID,
        "raster_third_factor_valid",
    )
    state.evidence["raster_third_factor_present"] = False


def _validate_raster_routing(
    routing: Any,
    require_routing_table: bool,
    reason_codes: list[str],
    evidence: dict[str, Any],
) -> None:
    if not isinstance(routing, dict):
        reason_codes.append(REASON_RASTER_ROUTING)
        evidence["raster_routing_present"] = False
        return
    state = _validation_state(reason_codes, evidence)
    evidence["raster_routing_present"] = True
    endpoints_valid = _routing_endpoints_valid(routing)
    evidence["raster_routing_valid"] = endpoints_valid
    if not endpoints_valid:
        reason_codes.append(REASON_RASTER_ROUTING)
    table = routing.get("table")
    valid_entries, invalid_indices = _routing_table(table)
    evidence["raster_routing_table_entries"] = len(valid_entries)
    evidence["raster_routing_table_declared_entries"] = len(table) if isinstance(table, list) else 0
    if require_routing_table and not valid_entries:
        _mark_invalid(reason_codes, evidence, REASON_RASTER_ROUTING, "raster_routing_table_valid")
    if invalid_indices:
        reason_codes.append(REASON_RASTER_ROUTING)
        evidence["raster_routing_table_invalid_indices"] = invalid_indices
    _validate_routing_third_factor(routing, state)


def _timestamp_within_raster_window(timestamp: Any, window_ms: float | None) -> bool:
    timestamp_us = _nonnegative_json_integer(timestamp)
    if timestamp_us is None:
        return False
    window_us = window_ms * 1000 if window_ms is not None else None
    if window_us is None:
        return True
    return timestamp_us <= window_us + 1e-9


def _neuron_within_population(neuron_id: Any, neurons: Any) -> bool:
    normalized_neuron = _nonnegative_json_integer(neuron_id)
    if normalized_neuron is None:
        return False
    if not _positive_int(neurons):
        return True
    return normalized_neuron < neurons


def _valid_excerpt_item(item: Any, window_ms: float | None, neurons: Any) -> bool:
    if not isinstance(item, dict):
        return False
    return all(
        (
            _timestamp_within_raster_window(item.get("t_us"), window_ms),
            _neuron_within_population(item.get("neuron_id"), neurons),
            "channel" not in item or isinstance(item["channel"], str),
        )
    )


def _validate_raster_excerpt(
    excerpt: Any,
    window_ms: float | None,
    neurons: Any,
    state: _ValidationState,
) -> None:
    if not isinstance(excerpt, list) or not excerpt:
        _mark_invalid(
            state.reason_codes,
            state.evidence,
            REASON_RASTER_EXCERPT,
            "raster_excerpt_valid",
        )
        return
    bad = [
        index
        for index, item in enumerate(excerpt)
        if not _valid_excerpt_item(item, window_ms, neurons)
    ]
    state.evidence["raster_excerpt_count"] = len(excerpt)
    state.evidence["raster_excerpt_valid"] = not bad
    if bad:
        state.reason_codes.append(REASON_RASTER_EXCERPT)
        state.evidence["raster_excerpt_invalid_indices"] = bad


def _validate_raster(
    raster: Any,
    *,
    reason_codes: list[str],
    evidence: dict[str, Any],
    require_routing_table: bool = False,
) -> None:
    """Validate a 20-50 ms raster using focused fail-closed checks."""

    if not isinstance(raster, dict):
        reason_codes.append(REASON_RASTER_EXCERPT)
        evidence["raster_error"] = "raster must be an object"
        evidence["raster_present"] = False
        return
    evidence["raster_present"] = True
    state = _validation_state(reason_codes, evidence)
    window_s, window_ms, _ = _raster_window(raster, reason_codes, evidence)
    neurons, spikes, budget_ready = _raster_spike_budget(raster, window_s, reason_codes, evidence)
    _validate_raster_energy(raster, spikes, budget_ready, state)
    _validate_raster_routing(raster.get("routing"), require_routing_table, reason_codes, evidence)
    _validate_raster_excerpt(raster.get("excerpt"), window_ms, neurons, state)
