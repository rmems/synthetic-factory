#!/usr/bin/env python3
"""System-domain validation for ``neuromorphic-fault-recovery``.

Split out of ``fault_simulator.py`` verbatim: the relay-configuration checks
:class:`fault_simulator.RelayReflexSimulator` runs before stepping — control
domains, the thermal ladder, channel-list shape, and redundancy rules. Raising
``oc.ContractError`` here is how a malformed scenario fails closed instead of
simulating a record that never happened.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from oracle_grounded import distill_contract as oc  # noqa: E402

if __package__:
    from .fault_types import (
        _genuine_count_from,
        _non_negative_number,
        _positive_number,
        _unit_interval,
    )
else:
    from fault_types import (
        _genuine_count_from,
        _non_negative_number,
        _positive_number,
        _unit_interval,
    )


# Numeric relay controls and their fail-closed domains. An out-of-domain
# control silently rewrites the outcome tiers — a negative quarantine
# ratio turns every below-threshold corruption into `quarantine` — so an
# authoritative outcome may not be derived over one. Each entry is
# ``(key, expected, predicate)``; the predicate decides, the expected
# text names the domain in the refusal.
_SYSTEM_CONTROL_DOMAINS = tuple(
    [
        (key, "a positive number", _positive_number)
        for key in (
            "tick_ms",
            "stale_threshold_ms",
            "deadline_ms",
            "hard_deadline_ms",
            "reflex_latency_ms",
            "fallback_latency_ms",
        )
    ]
    + [("jitter_tolerance_ms", "a non-negative number", _non_negative_number)]
    + [
        # The tick count is bounded because the validator replays
        # untrusted scenarios: it walks every live channel for every
        # tick and keeps one trace entry per tick, so an unbounded value
        # would let one record buy an arbitrarily large replay. The
        # default run uses 24.
        ("ticks", "an integer in [1, 1000]", _genuine_count_from(1, 1000)),
        ("reflex_saturation_ticks", "an integer >= 1", _genuine_count_from(1)),
        ("min_healthy_channels", "an integer >= 0", _genuine_count_from(0)),
        ("corruption_quarantine_ratio", "a ratio in [0, 1]", _unit_interval),
    ]
)

def _check_thermal_ladder(system: dict[str, Any]) -> None:
    thresholds = [
        system["ambient_c"],
        system["thermal_warn_c"],
        system["thermal_limit_c"],
        system["thermal_shutdown_c"],
    ]
    if not all(oc.is_number(value) for value in thresholds):
        raise oc.ContractError(
            "system thermal thresholds must be finite numbers"
        )
    ambient, warn, limit, shutdown = (
        float(value) for value in thresholds
    )
    if not ambient < warn < limit < shutdown:
        raise oc.ContractError(
            "system thermal ladder must be ordered ambient < warn < "
            f"limit < shutdown, got {ambient}, {warn}, {limit}, "
            f"{shutdown}"
        )

def _usable_channel_names(channels: Any) -> bool:
    """A non-empty bounded list of distinct, non-empty channel names."""
    if not isinstance(channels, list) or not channels or len(channels) > 32:
        # Bounded for the same reason ticks is: the replay walks every
        # channel every tick. The default relay has 4.
        return False
    if not all(isinstance(name, str) and name for name in channels):
        return False
    # Unique: the healthy-channel budget counts list entries while
    # the per-channel state collapses duplicates, so ['c0'] * 4
    # reported four healthy channels from one distinct sensor and
    # replayed as an authoritative outcome.
    return len(set(channels)) == len(channels)

def _check_system_channels(system: dict[str, Any]) -> None:
    channels = system["channels"]
    if not _usable_channel_names(channels):
        raise oc.ContractError(
            "system channels must be a non-empty list of at most 32 "
            "unique channel names"
        )
    fallback = system["fallback_source"]
    if fallback is not None and not (
        isinstance(fallback, str) and fallback.strip()
    ):
        # Any truthy value used to satisfy the fallback tier, so
        # `fallback_source: 123` produced an authoritative `fallback`
        # with FALLBACK_SOURCE_ENGAGED and no named source.
        raise oc.ContractError(
            "system fallback_source must be a non-empty string or null, "
            f"got {fallback!r}"
        )
    if isinstance(fallback, str) and fallback in channels:
        # A fallback names a REDUNDANT source. Naming a primary channel
        # let a surviving primary engage as its own fallback, producing
        # an authoritative `fallback` with no redundant relay behind it.
        raise oc.ContractError(
            f"system fallback_source {fallback!r} is one of the primary "
            "channels; a fallback must be a redundant source"
        )

def _check_system_controls(system: dict[str, Any]) -> None:
    """Refuse relay thresholds an authoritative outcome cannot stand on."""

    for key, expected, valid in _SYSTEM_CONTROL_DOMAINS:
        value = system[key]
        if not valid(value):
            raise oc.ContractError(
                f"system {key} must be {expected}, got {value!r}"
            )
    if system["hard_deadline_ms"] <= system["deadline_ms"]:
        raise oc.ContractError("system hard_deadline_ms must exceed deadline_ms")
    _check_thermal_ladder(system)
    _check_system_channels(system)
    if system["min_healthy_channels"] > len(system["channels"]):
        raise oc.ContractError("system min_healthy_channels exceeds primary channel count")
