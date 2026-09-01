#!/usr/bin/env python3
"""Fail-closed raster, spike-gate, routing, and energy validation."""

from __future__ import annotations

from fractions import Fraction
from typing import Any

if __package__:
    from . import _expose_package_sibling, _local_sibling_module
    if _local_sibling_module("curate_bridge_raster", allow_initializing=True) is not None:
        import curate_bridge_raster as _direct_curate_bridge_raster
        del _direct_curate_bridge_raster
    from .curate_bridge_raster_numbers import (
        REASON_RASTER_SPIKE_BUDGET as _NUMERIC_REASON_RASTER_SPIKE_BUDGET,
        _PositiveAliases,
        _ValidationState,
        _alias_pair_valid,
        _expected_spikes as _numeric_expected_spikes,
        _finite_float as _numeric_finite_float,
        _is_exact_finite_number,
        _is_finite_number,
        _nonblank_text,
        _nonnegative_int as _numeric_nonnegative_int,
        _nonnegative_json_integer,
        _positive_int as _numeric_positive_int,
        _positive_number,
        _raster_energy_field,
        _raster_spike_budget,
        _spike_energy,
        _valid_routing_entry,
        _validation_state,
    )
    from .exact_json import exact_fraction, json_number_from_fraction
else:
    from curate_bridge_raster_numbers import (
        REASON_RASTER_SPIKE_BUDGET as _NUMERIC_REASON_RASTER_SPIKE_BUDGET,
        _PositiveAliases,
        _ValidationState,
        _alias_pair_valid,
        _expected_spikes as _numeric_expected_spikes,
        _finite_float as _numeric_finite_float,
        _is_exact_finite_number,
        _is_finite_number,
        _nonblank_text,
        _nonnegative_int as _numeric_nonnegative_int,
        _nonnegative_json_integer,
        _positive_int as _numeric_positive_int,
        _positive_number,
        _raster_energy_field,
        _raster_spike_budget,
        _spike_energy,
        _valid_routing_entry,
        _validation_state,
    )
    from exact_json import exact_fraction, json_number_from_fraction

# Compatibility exports used by the public Bridge facade and gate validators.
REASON_RASTER_SPIKE_BUDGET = _NUMERIC_REASON_RASTER_SPIKE_BUDGET
_expected_spikes = _numeric_expected_spikes
_finite_float = _numeric_finite_float
_nonnegative_int = _numeric_nonnegative_int
_positive_int = _numeric_positive_int


RASTER_WINDOW_MIN_MS = 20
RASTER_WINDOW_MAX_MS = 50
RASTER_ENERGY_PJ_PER_SPIKE = 23
RASTER_ENERGY_UJ_PER_SPIKE = 23e-6
REASON_RASTER_WINDOW = "BRIDGE_RASTER_WINDOW_INVALID"
REASON_RASTER_ENERGY = "BRIDGE_ENERGY_MISMATCH"
REASON_RASTER_ROUTING = "BRIDGE_RASTER_ROUTING_MISSING"
REASON_RASTER_EXCERPT = "BRIDGE_RASTER_EXCERPT_INVALID"
REASON_THIRD_FACTOR_INVALID = "BRIDGE_THIRD_FACTOR_ROUTING_INVALID"
REASON_GATE_SNN_INVALID = "BRIDGE_GATE_SNN_SPEC_INVALID"


def _positive_aliases(
    container: dict[str, Any], primary_key: str, alias_key: str, *, alias_scale: float
) -> _PositiveAliases:
    """Resolve two positive aliases without treating explicit null as absent."""

    primary_declared = primary_key in container
    alias_declared = alias_key in container
    primary = container.get(primary_key)
    alias = container.get(alias_key)
    scale = exact_fraction(alias_scale)
    if scale is None or scale <= 0:
        return _PositiveAliases(primary, alias, primary_declared, alias_declared, False, False)
    primary = _derive_positive_alias(primary_declared, primary, alias, scale)
    alias = _derive_positive_alias(alias_declared, alias, primary, 1 / scale)
    valid = _positive_number(primary) and _positive_number(alias)
    primary_fraction = exact_fraction(primary)
    alias_fraction = exact_fraction(alias)
    consistent = (
        valid
        and primary_fraction is not None
        and alias_fraction is not None
        and abs(primary_fraction - alias_fraction * scale) <= Fraction(1, 10**9)
    )
    return _PositiveAliases(primary, alias, primary_declared, alias_declared, valid, consistent)


def _derive_positive_alias(
    declared: bool,
    current: Any,
    source: Any,
    scale: Fraction,
) -> Any:
    """Derive only a missing alias while preserving explicit null values."""

    if declared or not _positive_number(source):
        return current
    source_fraction = exact_fraction(source)
    if source_fraction is None:
        return current
    derived = source_fraction * scale
    try:
        return json_number_from_fraction(derived)
    except (ValueError, OverflowError):
        return current


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
    evidence["raster_third_factor_tau_e_s"] = tau.primary
    evidence["raster_third_factor_eligibility"] = eligibility.strip()


def _raster_window(
    raster: dict[str, Any], reason_codes: list[str], evidence: dict[str, Any]
) -> tuple[Any | None, Any | None, bool]:
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
    primary_fraction = exact_fraction(window.primary)
    alias_fraction = exact_fraction(window.alias)
    in_range = window.valid and all(
        (
            alias_fraction is not None,
            primary_fraction is not None,
            RASTER_WINDOW_MIN_MS <= alias_fraction <= RASTER_WINDOW_MAX_MS,
            Fraction(RASTER_WINDOW_MIN_MS, 1000)
            <= primary_fraction
            <= Fraction(RASTER_WINDOW_MAX_MS, 1000),
        )
    )
    valid = in_range and window.consistent
    evidence["raster_window_ms"] = window.alias
    evidence["raster_window_valid"] = valid
    evidence["raster_window_consistent"] = bool(window.consistent)
    if not valid:
        reason_codes.append(REASON_RASTER_WINDOW)
        return None, None, False
    evidence["raster_window_ms"] = window.alias
    evidence["raster_window_s"] = window.primary
    return window.primary, window.alias, True


def _invalid_declared_energy_keys(raster: dict[str, Any]) -> list[str]:
    declared = (
        ("energy_pJ", "raster_declared_energy_pJ_valid"),
        ("energy_uJ", "raster_declared_energy_uJ_valid"),
    )
    return [
        evidence_key
        for key, evidence_key in declared
        if all((key in raster, not _is_exact_finite_number(raster.get(key))))
    ]


def _raster_energy_checks(spikes: Any) -> tuple[tuple[Any, ...], ...]:
    expected_pj = _spike_energy(spikes, RASTER_ENERGY_PJ_PER_SPIKE)
    expected_uj = _spike_energy(spikes, RASTER_ENERGY_UJ_PER_SPIKE)
    return (
        (
            "energy_pJ",
            expected_pj,
            1e-6,
            "raster_expected_energy_pJ",
            expected_pj,
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
        if all((key in raster, _is_exact_finite_number(raster.get(key))))
    ]
    for expected_key, expected_value, evidence_key, valid in results:
        state.evidence[expected_key] = expected_value
        state.evidence[evidence_key] = valid
    invalid_count = sum(not result[3] for result in results)
    state.reason_codes.extend([REASON_RASTER_ENERGY] * invalid_count)


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


def _timestamp_within_raster_window(timestamp: Any, window_ms: Any | None) -> bool:
    timestamp_us = _nonnegative_json_integer(timestamp)
    if timestamp_us is None:
        return False
    window = exact_fraction(window_ms)
    if window_ms is None:
        return True
    if window is None:
        return False
    return Fraction(timestamp_us) <= window * 1000


def _neuron_within_population(neuron_id: Any, neurons: Any) -> bool:
    normalized_neuron = _nonnegative_json_integer(neuron_id)
    if normalized_neuron is None:
        return False
    population_size = _nonnegative_json_integer(neurons)
    if population_size is None or population_size <= 0:
        return True
    return normalized_neuron < population_size


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


if __package__:
    _expose_package_sibling(__name__)
