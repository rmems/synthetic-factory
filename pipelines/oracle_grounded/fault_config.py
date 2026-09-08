#!/usr/bin/env python3
"""Relay configuration refusals for the fault-recovery family (F1).

The healthy-start, heating-only contract, enforced before any state exists:
every control in its domain, a well-formed channel list and fallback source,
and the D7 relations -- the thermal ladder ordered from ambient (row 1), the
healthy budget within the channel count (row 4), the soft deadline before the
hard one (row 5), a finite horizon (row 7) and, in the same spirit, a finite
thermal span from ambient to shutdown -- plus the row-8 refusal of
unknown ``scenario.system`` keys before the defaults merge. Missing keys are
still filled from ``DEFAULT_SYSTEM``. Held by ruling: the ``tick_ms`` versus
``stale_threshold_ms`` inequality is deliberately not enforced.
:func:`checked_system` returns the effective merged system the simulator runs
and the oracle block records.
"""

from __future__ import annotations

import copy
from collections.abc import Callable, Iterable
from typing import Any

from . import distill_vocabulary as vocab
from . import envelope
from . import fault_vocabulary as fv
from .import_twins import bind_import_twin

Problem = tuple[bool, str, str]


def finite_number(value: Any) -> bool:
    """A finite, non-boolean number (NaN, inf and bool refused)."""
    return envelope.is_number(value)


def positive_number(value: Any) -> bool:
    return envelope.is_number(value) and float(value) > 0.0


def non_negative_number(value: Any) -> bool:
    return envelope.is_number(value) and float(value) >= 0.0


def unit_interval(value: Any) -> bool:
    return envelope.is_number(value) and 0.0 <= float(value) <= 1.0


def genuine_count_from(floor: int, ceiling: int | None = None) -> Callable[[Any], bool]:
    """A predicate for a genuine (non-boolean) integer in ``[floor, ceiling]``."""

    def holds(value: Any) -> bool:
        if not vocab.is_genuine_int(value):
            return False
        return floor <= value <= (value if ceiling is None else ceiling)

    return holds


_POSITIVE_CONTROLS = (
    "tick_ms", "stale_threshold_ms", "deadline_ms",
    "hard_deadline_ms", "reflex_latency_ms", "fallback_latency_ms",
)
_THERMAL_CONTROLS = ("ambient_c", "thermal_warn_c", "thermal_limit_c", "thermal_shutdown_c")

# (key, expected text, predicate). ``reflex_saturation_ticks`` has no ceiling
# against ``ticks`` (row 10) and the quarantine ratio admits 0 (row 6).
_CONTROL_DOMAINS: tuple[tuple[str, str, Callable[[Any], bool]], ...] = (
    *((key, "a positive number", positive_number) for key in _POSITIVE_CONTROLS),
    ("jitter_tolerance_ms", "a non-negative number", non_negative_number),
    ("ticks", f"an integer in [1, {fv.MAX_TICKS}]", genuine_count_from(1, fv.MAX_TICKS)),
    ("reflex_saturation_ticks", "an integer >= 1", genuine_count_from(1)),
    ("min_healthy_channels", "an integer >= 0", genuine_count_from(0)),
    ("corruption_quarantine_ratio", "a ratio in [0, 1]", unit_interval),
    *((key, "a finite number", finite_number) for key in _THERMAL_CONTROLS),
)


def _domain_problems(system: dict[str, Any]) -> Iterable[Problem]:
    for key, expected, holds in _CONTROL_DOMAINS:
        value = system.get(key)
        yield (
            not holds(value),
            fv.FINDING_SYSTEM_CONTROL_OUT_OF_DOMAIN,
            f"system {key} must be {expected}, got {value!r}",
        )


def _all_names(channels: list[Any]) -> bool:
    return not any(vocab.missing_string(name) for name in channels)


def _bounded(channels: list[Any]) -> bool:
    return 0 < len(channels) <= fv.MAX_CHANNELS


def _unique(channels: list[Any]) -> bool:
    return len(set(channels)) == len(channels)


# Applied in order and lazily, so ``_unique`` only ever sees a list of names.
_CHANNEL_RULES = (lambda channels: isinstance(channels, list), _bounded, _all_names, _unique)


def _channel_list_problem(system: dict[str, Any]) -> None:
    """A non-empty list of at most ``MAX_CHANNELS`` unique, non-blank names."""
    channels = system.get("channels")
    fv.refuse_when(
        not all(rule(channels) for rule in _CHANNEL_RULES),
        fv.FINDING_CHANNEL_LIST_INVALID,
        f"system channels must be a non-empty list of at most {fv.MAX_CHANNELS} unique "
        f"channel names, got {channels!r}",
    )


def _is_primary(fallback: Any, channels: list[str]) -> bool:
    return isinstance(fallback, str) and fallback in channels


def _fallback_problems(system: dict[str, Any]) -> tuple[Problem, ...]:
    """Null or a non-blank string, never a primary channel (the list passed first)."""
    fallback = system.get("fallback_source")
    return (
        (
            fallback is not None and vocab.missing_string(fallback),
            fv.FINDING_FALLBACK_SOURCE_INVALID,
            f"system fallback_source must be a non-empty string or null, got {fallback!r}",
        ),
        (
            _is_primary(fallback, system["channels"]),
            fv.FINDING_FALLBACK_SOURCE_IS_PRIMARY,
            f"system fallback_source {fallback!r} is one of the primary channels; "
            "a fallback must be a redundant source",
        ),
    )


def _ladder_unordered(system: dict[str, Any]) -> bool:
    ambient, warn, limit, shutdown = (system[key] for key in _THERMAL_CONTROLS)
    return not ambient < warn < limit < shutdown


def _budget_exceeds_channels(system: dict[str, Any]) -> bool:
    return system["min_healthy_channels"] > len(system["channels"])


def _deadlines_inverted(system: dict[str, Any]) -> bool:
    return system["deadline_ms"] >= system["hard_deadline_ms"]


def _horizon_not_finite(system: dict[str, Any]) -> bool:
    return not envelope.is_number(system["tick_ms"] * system["ticks"])


def _thermal_span_not_finite(system: dict[str, Any]) -> bool:
    """The ladder's span in degrees must be representable, like the horizon in ms."""
    return not envelope.is_number(system["thermal_shutdown_c"] - system["ambient_c"])


# (code, holds, message template over the system's keys): the cross-field
# relations, evaluated only once every control is inside its domain.
_RELATIONS: tuple[tuple[str, Callable[[dict[str, Any]], bool], str], ...] = (
    (
        fv.FINDING_THERMAL_LADDER_UNORDERED,
        _ladder_unordered,
        "system thermal ladder must be ordered ambient < warn < limit < shutdown, got "
        "{ambient_c}, {thermal_warn_c}, {thermal_limit_c}, {thermal_shutdown_c}",
    ),
    (
        fv.FINDING_HEALTHY_BUDGET_EXCEEDS_CHANNELS,
        _budget_exceeds_channels,
        "system min_healthy_channels {min_healthy_channels} exceeds the channel count",
    ),
    (
        fv.FINDING_DEADLINE_ORDER_INVERTED,
        _deadlines_inverted,
        "system deadline_ms {deadline_ms} must be below hard_deadline_ms {hard_deadline_ms}",
    ),
    (
        fv.FINDING_HORIZON_NOT_FINITE,
        _horizon_not_finite,
        "system horizon tick_ms {tick_ms} x ticks {ticks} is not a finite number of ms",
    ),
    (
        fv.FINDING_SYSTEM_CONTROL_OUT_OF_DOMAIN,
        _thermal_span_not_finite,
        "system thermal span from ambient_c {ambient_c} to thermal_shutdown_c "
        "{thermal_shutdown_c} is not a finite number of degrees",
    ),
)


def _relation_problems(system: dict[str, Any]) -> Iterable[Problem]:
    for code, holds, template in _RELATIONS:
        yield holds(system), code, template.format(**system)


def check_system(system: dict[str, Any]) -> None:
    """Refuse a merged relay configuration an outcome cannot stand on.

    Domains, then the channel list, then the fallback source, then the
    relations, so every later stage sees typed values.
    """
    fv.refuse_first(_domain_problems(system))
    _channel_list_problem(system)
    fv.refuse_first(_fallback_problems(system))
    fv.refuse_first(_relation_problems(system))


def _system_of(scenario: Any) -> dict[str, Any]:
    """``scenario.system`` (absent means empty), or a coded refusal."""
    if not isinstance(scenario, dict):
        fv.refuse(fv.FINDING_INPUT_NOT_AN_OBJECT, f"scenario must be an object, got {scenario!r}")
    system = scenario.get("system", {})
    fv.refuse_when(
        not isinstance(system, dict),
        fv.FINDING_INPUT_NOT_AN_OBJECT,
        f"scenario.system must be an object, got {system!r}",
    )
    return system


def _unknown_keys(system: dict[str, Any]) -> None:
    """Row 8: ``scenario.system`` keys must be a subset of ``DEFAULT_SYSTEM``'s."""
    unknown = sorted(str(key) for key in set(system) - fv.SYSTEM_KEYS)
    fv.refuse_when(
        bool(unknown),
        fv.FINDING_SYSTEM_UNKNOWN_KEY,
        f"scenario.system carries unknown keys {unknown}; the relay reads only "
        f"{sorted(fv.SYSTEM_KEYS)}, so those values would be silently ignored",
    )


def checked_system(scenario: Any) -> dict[str, Any]:
    """The effective, validated relay configuration of ``scenario``.

    Unknown keys are refused before the merge; omitted keys are filled from
    ``DEFAULT_SYSTEM``. The result is a deep copy aliasing neither the
    scenario nor the defaults, and it is the one configuration the simulator
    runs and the oracle block records.
    """
    system = _system_of(scenario)
    _unknown_keys(system)
    merged = {**fv.default_system(), **copy.deepcopy(system)}
    check_system(merged)
    return merged


bind_import_twin(__name__)
