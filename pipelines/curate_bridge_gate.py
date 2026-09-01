#!/usr/bin/env python3
"""Spike-implemented gate and declared gate-compute validation."""

from __future__ import annotations

from typing import Any

if __package__:
    from . import _expose_package_sibling, _local_sibling_module
    if _local_sibling_module("curate_bridge_gate", allow_initializing=True) is not None:
        import curate_bridge_gate as _direct_curate_bridge_gate
        del _direct_curate_bridge_gate
    from .exact_json import json_integer_is_bounded
    from .curate_bridge_raster import (
        RASTER_ENERGY_PJ_PER_SPIKE,
        RASTER_ENERGY_UJ_PER_SPIKE,
        REASON_GATE_SNN_INVALID,
        REASON_RASTER_ENERGY,
        REASON_RASTER_SPIKE_BUDGET,
        _PositiveAliases,
        _ValidationState,
        _alias_pair_valid,
        _expected_spikes,
        _is_finite_number,
        _nonblank_text,
        _nonnegative_int,
        _nonnegative_json_integer,
        _positive_aliases,
        _positive_int,
        _raster_energy_field,
        _record_alias_derivation,
        _spike_energy,
        _validation_state,
    )
else:
    from exact_json import json_integer_is_bounded
    from curate_bridge_raster import (
        RASTER_ENERGY_PJ_PER_SPIKE,
        RASTER_ENERGY_UJ_PER_SPIKE,
        REASON_GATE_SNN_INVALID,
        REASON_RASTER_ENERGY,
        REASON_RASTER_SPIKE_BUDGET,
        _PositiveAliases,
        _ValidationState,
        _alias_pair_valid,
        _expected_spikes,
        _is_finite_number,
        _nonblank_text,
        _nonnegative_int,
        _nonnegative_json_integer,
        _positive_aliases,
        _positive_int,
        _raster_energy_field,
        _record_alias_derivation,
        _spike_energy,
        _validation_state,
    )


_NO_EXPECTED_DECISION = object()


def _rate_aliases(container: dict[str, Any]) -> _PositiveAliases:
    return _positive_aliases(container, "mean_rate_hz", "rate_hz", alias_scale=1.0)


def _compute_window_aliases(container: dict[str, Any]) -> _PositiveAliases:
    return _positive_aliases(container, "window_s", "window_ms", alias_scale=0.001)


def _decision_window_aliases(container: dict[str, Any]) -> _PositiveAliases:
    return _positive_aliases(
        container,
        "decision_window_s",
        "decision_window_ms",
        alias_scale=0.001,
    )


def _gate_shape_valid(
    neurons: Any, rate: _PositiveAliases, window: _PositiveAliases, spikes: Any
) -> bool:
    return all(
        (
            _positive_int(neurons),
            _alias_pair_valid(rate),
            _alias_pair_valid(window),
            _nonnegative_int(spikes),
        )
    )


def _append_mismatch(bucket: list[dict[str, Any]], index: int, expected: Any, actual: Any) -> None:
    bucket.append({"index": index, "expected": expected, "actual": actual})


def _gate_window(spec: dict[str, Any], evidence: dict[str, Any]) -> tuple[Any | None, bool]:
    window = _decision_window_aliases(spec)
    _record_alias_derivation(
        window,
        primary_evidence_key="gate_snn_decision_window_s_derived",
        alias_evidence_key="gate_snn_decision_window_ms_derived",
        evidence=evidence,
    )
    valid = _alias_pair_valid(window)
    evidence["gate_snn_decision_window_valid"] = valid
    evidence["gate_snn_decision_window_consistent"] = bool(window.consistent)
    if not valid:
        return None, False
    evidence["gate_snn_decision_window_ms"] = window.alias
    evidence["gate_snn_decision_window_s"] = window.primary
    return window.primary, True


def _gate_decision(
    spec: dict[str, Any],
    expected_decision: str | None | object,
    evidence: dict[str, Any],
) -> bool:
    decision = spec.get("decision")
    if not _nonblank_text(decision):
        evidence["gate_snn_decision_valid"] = False
        return False
    normalized = decision.strip().upper()
    evidence["gate_snn_decision"] = normalized
    if expected_decision is _NO_EXPECTED_DECISION:
        evidence["gate_snn_decision_valid"] = True
        return True
    if expected_decision is None:
        evidence["gate_snn_decision_valid"] = False
        return False
    expected = expected_decision.strip().upper()
    evidence["gate_snn_expected_decision"] = expected
    evidence["gate_snn_decision_valid"] = normalized == expected
    return normalized == expected


def _gate_population_neurons(population: Any) -> int | None:
    if not isinstance(population, dict):
        return None
    if not _nonblank_text(population.get("name")):
        return None
    neurons = _nonnegative_json_integer(population.get("neurons"))
    if neurons is None or neurons <= 0:
        return None
    if not _is_finite_number(population.get("threshold")):
        return None
    return neurons


def _gate_population_budget(
    population: dict[str, Any], neurons: int, window_s: Any | None
) -> tuple[str, int | None]:
    """Return ``(absent|invalid|valid, expected_spikes)``."""

    rate = _rate_aliases(population)
    rate_declared = rate.primary_declared or rate.alias_declared
    spikes_declared = "spikes" in population
    if not rate_declared and not spikes_declared:
        return "absent", None
    spikes = population.get("spikes")
    ready = all(
        (
            rate_declared,
            spikes_declared,
            _alias_pair_valid(rate),
            _nonnegative_int(spikes),
            window_s is not None,
        )
    )
    if not ready:
        return "invalid", None
    expected = _expected_spikes(neurons, rate.primary, window_s)
    if expected is None:
        return "invalid", None
    return "valid", expected


def _gate_population(
    population: Any,
    index: int,
    window_s: Any | None,
    state: _ValidationState,
) -> tuple[bool, bool, int]:
    """Return ``(valid, malformed, neurons)`` for one gate population."""

    neurons = _gate_population_neurons(population)
    if neurons is None:
        return False, True, 0
    budget, expected = _gate_population_budget(population, neurons, window_s)
    return _gate_population_budget_outcome(
        population,
        index,
        state,
        (budget, expected, neurons),
    )


def _gate_population_budget_outcome(
    population: dict[str, Any],
    index: int,
    state: _ValidationState,
    outcome: tuple[str, int | None, int],
) -> tuple[bool, bool, int]:
    budget, expected, neurons = outcome
    if budget == "absent":
        return True, False, neurons
    if budget == "invalid":
        return False, True, neurons
    spikes = _nonnegative_json_integer(population["spikes"])
    if spikes is None:
        return False, True, neurons
    if abs(spikes - expected) <= 1:
        return True, False, neurons
    state.reason_codes.append(REASON_RASTER_SPIKE_BUDGET)
    _append_mismatch(
        state.evidence.setdefault("gate_snn_spike_mismatches", []),
        index,
        expected,
        spikes,
    )
    return False, False, neurons


def _gate_population_list(populations: Any, state: _ValidationState) -> list[Any] | None:
    items = populations if isinstance(populations, list) else []
    if items:
        return items
    state.reason_codes.append(REASON_GATE_SNN_INVALID)
    state.evidence["gate_snn_populations_valid"] = False
    state.evidence["gate_snn_population_count"] = len(items)
    return None


def _gate_population_results(
    populations: list[Any], window_s: float | None, state: _ValidationState
) -> list[tuple[bool, bool, int]]:
    return [
        _gate_population(population, index, window_s, state)
        for index, population in enumerate(populations)
    ]


def _malformed_population_indices(results: list[tuple[bool, bool, int]]) -> list[int]:
    return [index for index, (_, malformed, _) in enumerate(results) if malformed]


def _gate_populations(
    populations: Any,
    window_s: float | None,
    *,
    reason_codes: list[str],
    evidence: dict[str, Any],
) -> bool:
    state = _validation_state(reason_codes, evidence)
    population_list = _gate_population_list(populations, state)
    if population_list is None:
        return False
    results = _gate_population_results(population_list, window_s, state)
    bad = _malformed_population_indices(results)
    if bad:
        reason_codes.append(REASON_GATE_SNN_INVALID)
        evidence["gate_snn_invalid_population_indices"] = bad
    evidence["gate_snn_population_count"] = len(population_list)
    populations_valid = all(result[0] for result in results)
    total_neurons = sum(result[2] for result in results)
    total_valid = not bad and json_integer_is_bounded(total_neurons)
    evidence["gate_snn_total_neurons_valid"] = total_valid
    if not total_valid:
        reason_codes.append(REASON_GATE_SNN_INVALID)
        evidence["gate_snn_populations_valid"] = False
        return False
    evidence["gate_snn_total_neurons"] = total_neurons
    evidence["gate_snn_populations_valid"] = populations_valid
    return populations_valid


def _validate_gate_snn(
    spec: Any,
    *,
    reason_codes: list[str],
    evidence: dict[str, Any],
    expected_decision: str | None | object = _NO_EXPECTED_DECISION,
) -> None:
    """Validate a spike gate through small fail-closed contract checks."""

    evidence["gate_snn_present"] = True
    if not isinstance(spec, dict):
        reason_codes.append(REASON_GATE_SNN_INVALID)
        evidence["gate_snn_valid"] = False
        evidence["gate_snn_error"] = "gate_snn must be an object"
        return
    window_s, window_valid = _gate_window(spec, evidence)
    decision_valid = _gate_decision(spec, expected_decision, evidence)
    populations_valid = _gate_populations(
        spec.get("populations"), window_s, reason_codes=reason_codes, evidence=evidence
    )
    if not window_valid or not decision_valid:
        reason_codes.append(REASON_GATE_SNN_INVALID)
    evidence["gate_snn_valid"] = window_valid and decision_valid and populations_valid


def _gate_check(
    check: Any,
    index: int,
    *,
    reason_codes: list[str],
    evidence: dict[str, Any],
) -> bool:
    if not isinstance(check, dict):
        return _invalid_gate_check(index, reason_codes, evidence)
    rate = _rate_aliases(check)
    window = _compute_window_aliases(check)
    neurons = check.get("neurons")
    spikes = _nonnegative_json_integer(check.get("spikes"))
    shape_valid = _gate_shape_valid(neurons, rate, window, spikes)
    if not shape_valid:
        return _invalid_gate_check(index, reason_codes, evidence)
    expected = _expected_spikes(neurons, rate.primary, window.primary)
    if expected is not None and abs(spikes - expected) <= 1:
        return True
    _append_mismatch(
        evidence.setdefault("gate_compute_spike_mismatches", []), index, expected, spikes
    )
    reason_codes.append(REASON_RASTER_SPIKE_BUDGET)
    return False


def _invalid_gate_check(index: int, reason_codes: list[str], evidence: dict[str, Any]) -> bool:
    evidence.setdefault("gate_compute_invalid_check_indices", []).append(index)
    reason_codes.append(REASON_RASTER_SPIKE_BUDGET)
    return False


def _total_gate_spikes(checks: list[Any]) -> tuple[int | None, bool]:
    normalized = [
        _nonnegative_json_integer(check.get("spikes"))
        if isinstance(check, dict)
        else None
        for check in checks
    ]
    if any(spikes is None for spikes in normalized):
        return None, False
    total = sum(normalized)
    return (total, True) if json_integer_is_bounded(total) else (None, False)


def _validate_gate_checks(
    gate_compute: dict[str, Any],
    reason_codes: list[str],
    evidence: dict[str, Any],
) -> int | None:
    per_check = gate_compute.get("per_check")
    if "per_check" in gate_compute and not isinstance(per_check, list):
        reason_codes.append(REASON_RASTER_SPIKE_BUDGET)
        evidence["gate_compute_error"] = "per_check must be an array"
        evidence["gate_compute_spike_budget_valid"] = False
        return None
    checks = per_check if isinstance(per_check, list) else []
    if checks:
        results = [
            _gate_check(
                check,
                index,
                reason_codes=reason_codes,
                evidence=evidence,
            )
            for index, check in enumerate(checks)
        ]
        evidence["gate_compute_spike_budget_valid"] = all(results)
    total_spikes, total_valid = _total_gate_spikes(checks)
    evidence["gate_compute_total_spikes_valid"] = total_valid
    if not total_valid:
        reason_codes.append(REASON_RASTER_SPIKE_BUDGET)
        evidence["gate_compute_spike_budget_valid"] = False
        return None
    evidence["gate_compute_total_spikes"] = total_spikes
    return total_spikes


def _validate_gate_energy(
    gate_compute: dict[str, Any],
    total_spikes: int | None,
    reason_codes: list[str],
    evidence: dict[str, Any],
) -> None:
    checks = (
        ("total_energy_uJ", RASTER_ENERGY_UJ_PER_SPIKE, 1e-9),
        ("total_energy_pJ", RASTER_ENERGY_PJ_PER_SPIKE, 1e-6),
    )
    results = []
    for key, per_spike, tolerance in checks:
        if key not in gate_compute:
            continue
        expected = _spike_energy(total_spikes, per_spike) if total_spikes is not None else None
        valid = _raster_energy_field(gate_compute[key], expected, tolerance)
        results.append(valid)
        if not valid:
            reason_codes.append(REASON_RASTER_ENERGY)
    if results:
        evidence["gate_compute_energy_valid"] = all(results)


def _validate_gate_compute(
    gate_compute: Any,
    *,
    reason_codes: list[str],
    evidence: dict[str, Any],
) -> None:
    """Validate per-check spike arithmetic and every declared energy total."""

    evidence["gate_compute_present"] = True
    if not isinstance(gate_compute, dict):
        reason_codes.append(REASON_RASTER_SPIKE_BUDGET)
        evidence["gate_compute_error"] = "gate_compute must be an object"
        evidence["gate_compute_spike_budget_valid"] = False
        return
    total_spikes = _validate_gate_checks(gate_compute, reason_codes, evidence)
    _validate_gate_energy(gate_compute, total_spikes, reason_codes, evidence)


if __package__:
    _expose_package_sibling(__name__)
