#!/usr/bin/env python3
"""Exact numeric primitives shared by Bridge raster validators."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

if __package__:
    from . import _expose_package_sibling, _local_sibling_module
    if _local_sibling_module("curate_bridge_raster_numbers", allow_initializing=True) is not None:
        import curate_bridge_raster_numbers as _direct_curate_bridge_raster_numbers
        del _direct_curate_bridge_raster_numbers
    from .exact_json import (
        exact_fraction,
        exact_json_integer,
        json_integer_is_bounded,
        json_number_from_fraction,
    )
else:
    from exact_json import (
        exact_fraction,
        exact_json_integer,
        json_integer_is_bounded,
        json_number_from_fraction,
    )


REASON_RASTER_SPIKE_BUDGET = "BRIDGE_SPIKE_BUDGET_MISMATCH"


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


def _is_exact_finite_number(value: Any) -> bool:
    """Return whether a JSON number is finite under the exact contract."""

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    if isinstance(value, int) and not json_integer_is_bounded(value):
        return False
    return exact_fraction(value) is not None


def _nonnegative_json_integer(value: Any) -> int | None:
    """Return a non-negative integer represented by one bounded JSON number.

    JSON Schema treats finite integral-valued numbers such as ``800.0`` and
    ``8e2`` as integers. Python's decoder represents those spellings as
    ``float``, so schema-integer raster fields must normalize them explicitly.
    """

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    integer = exact_json_integer(value)
    if integer is None or not json_integer_is_bounded(integer):
        return None
    return integer if integer >= 0 else None


def _expected_spikes(neurons: Any, mean_rate_hz: Any, window_s: Any) -> int | None:
    normalized_neurons = _nonnegative_json_integer(neurons)
    if normalized_neurons is None:
        return None
    rate_float = _finite_float(mean_rate_hz)
    window_float = _finite_float(window_s)
    rate = exact_fraction(mean_rate_hz)
    window = exact_fraction(window_s)
    if any(value is None for value in (rate_float, window_float, rate, window)):
        return None
    scale = rate_float * window_float
    if not math.isfinite(scale):
        return None
    try:
        # Keep the validated population exact and interpret both factors using
        # their JSON-decimal spellings. Float conversion can erase spike units
        # above 2**53 or magnify the approximation of 0.1 into a false defect.
        return round(rate * window * normalized_neurons)
    except (OverflowError, ValueError):
        return None


def _raster_spike_budget(
    raster: dict[str, Any],
    window_s: Any | None,
    reason_codes: list[str],
    evidence: dict[str, Any],
) -> tuple[Any, Any, bool]:
    neurons = _nonnegative_json_integer(raster.get("neurons"))
    rate = raster.get("mean_rate_hz")
    spikes = _nonnegative_json_integer(raster.get("spikes"))
    fields = (
        (
            "raster_neurons",
            "raster_neurons_valid",
            neurons,
            neurons is not None and neurons > 0,
        ),
        ("raster_rate_hz", "raster_rate_valid", rate, _positive_number(rate)),
        ("raster_spikes", "raster_spikes_valid", spikes, spikes is not None),
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
    expected = _expected_spikes(neurons, rate, window_s)
    evidence["raster_expected_spikes"] = expected
    evidence["raster_spike_budget_tolerance"] = 1
    valid = expected is not None and abs(spikes - expected) <= 1
    evidence["raster_spike_budget_valid"] = valid
    if not valid:
        reason_codes.append(REASON_RASTER_SPIKE_BUDGET)
    return neurons, spikes, True


def _spike_energy(spikes: int, per_spike: float | int) -> float | int | None:
    spike_fraction = exact_fraction(spikes)
    per_spike_fraction = exact_fraction(per_spike)
    if spike_fraction is None or per_spike_fraction is None:
        return None
    try:
        return json_number_from_fraction(spike_fraction * per_spike_fraction)
    except (OverflowError, ValueError):
        return None


def _raster_energy_field(
    value: Any,
    expected: float | int | None,
    tolerance: float,
) -> bool:
    if expected is None or not _is_exact_finite_number(expected):
        return False
    if not _is_exact_finite_number(value):
        return False
    value_fraction = exact_fraction(value)
    expected_fraction = exact_fraction(expected)
    tolerance_fraction = exact_fraction(tolerance)
    if any(
        item is None
        for item in (value_fraction, expected_fraction, tolerance_fraction)
    ):
        return False
    if value_fraction < 0:
        return False
    return abs(value_fraction - expected_fraction) <= tolerance_fraction


def _positive_number(value: Any) -> bool:
    fraction = exact_fraction(value)
    return _is_finite_number(value) and fraction is not None and fraction > 0


def _positive_int(value: object) -> bool:
    integer = _nonnegative_json_integer(value)
    return integer is not None and integer > 0


def _nonnegative_int(value: object) -> bool:
    return _nonnegative_json_integer(value) is not None


def _nonblank_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _valid_routing_entry(entry: Any) -> bool:
    if not isinstance(entry, dict):
        return False
    if not _nonblank_text(entry.get("from")):
        return False
    if not _nonblank_text(entry.get("to")):
        return False
    return _is_finite_number(entry.get("weight"))


if __package__:
    _expose_package_sibling(__name__)
