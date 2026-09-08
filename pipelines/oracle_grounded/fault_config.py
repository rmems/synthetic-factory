#!/usr/bin/env python3
"""Every refusal of the fault-recovery family that runs before any state exists (F1).

The relay system: each control in its domain, the channel list and fallback
source, the D7 relations (row 1 the ladder ordered from ambient, row 4 the
budget within the channel count, row 5 the soft deadline first, row 7 a
finite horizon and a finite thermal span) and row 8's refusal of unknown
``scenario.system`` keys before the defaults merge (omitted keys are filled;
``tick_ms`` versus ``stale_threshold_ms`` is held by ruling). The
disturbance: shape and kind, presence, channel shape, floors, value domains,
onset, a window holding a tick, row 2's peak above ambient, declared names,
relay narrowing and burst capacity, in #138's order. :func:`checked_system`
is the one configuration the simulator runs and the oracle block records.
"""

from __future__ import annotations

import copy
import math
import operator
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any

from . import distill_vocabulary as vocab
from . import envelope
from . import fault_vocabulary as fv
from .import_twins import bind_import_twin

Problem = tuple[bool, str, str]
Predicate = Callable[[Any], bool]


def finite_number(value: Any) -> bool:
    """A finite, non-boolean number (NaN, inf and bool refused)."""
    return envelope.is_number(value)


def positive_number(value: Any) -> bool:
    return envelope.is_number(value) and float(value) > 0.0


def non_negative_number(value: Any) -> bool:
    return envelope.is_number(value) and float(value) >= 0.0


def unit_interval(value: Any) -> bool:
    return envelope.is_number(value) and 0.0 <= float(value) <= 1.0


def genuine_count_from(floor: int, ceiling: int | None = None) -> Predicate:
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
_CONTROL_DOMAINS: tuple[tuple[str, str, Predicate], ...] = (
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
    (fv.FINDING_THERMAL_LADDER_UNORDERED, _ladder_unordered,
     "system thermal ladder must be ordered ambient < warn < limit < shutdown, got "
     "{ambient_c}, {thermal_warn_c}, {thermal_limit_c}, {thermal_shutdown_c}"),
    (fv.FINDING_HEALTHY_BUDGET_EXCEEDS_CHANNELS, _budget_exceeds_channels,
     "system min_healthy_channels {min_healthy_channels} exceeds the channel count"),
    (fv.FINDING_DEADLINE_ORDER_INVERTED, _deadlines_inverted,
     "system deadline_ms {deadline_ms} must be below hard_deadline_ms {hard_deadline_ms}"),
    (fv.FINDING_HORIZON_NOT_FINITE, _horizon_not_finite,
     "system horizon tick_ms {tick_ms} x ticks {ticks} is not a finite number of ms"),
    (fv.FINDING_SYSTEM_CONTROL_OUT_OF_DOMAIN, _thermal_span_not_finite,
     "system thermal span from ambient_c {ambient_c} to thermal_shutdown_c "
     "{thermal_shutdown_c} is not a finite number of degrees"),
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


@dataclass(frozen=True)
class Disturbance:
    """One checked disturbance.

    ``affected`` holds the declared names that are relay channels (the
    tick-loop set); ``declared`` every declared name, fallback source
    included (the fallback-availability set). Duplicates inside a
    disturbance's own list are accepted, as in #138.
    """

    kind: str
    parameters: dict[str, Any]
    affected: tuple[str, ...]
    declared: tuple[str, ...]


def _requires_channels(kind: str) -> bool:
    return "channels" in fv.PARAMETER_SPEC[kind][0]


def _effective_system(system: Any) -> None:
    """The system must be the full configuration ``checked_system`` returned."""
    fv.refuse_when(
        not isinstance(system, dict) or not fv.SYSTEM_KEYS <= set(system),
        fv.FINDING_INPUT_NOT_AN_OBJECT,
        f"system must be the effective configuration from checked_system, got {system!r}",
    )


def _disturbance_of(disturbance: Any) -> tuple[str, dict[str, Any]]:
    """``(kind, parameters)`` of a disturbance object, or a coded refusal."""
    if not isinstance(disturbance, dict):
        fv.refuse(fv.FINDING_INPUT_NOT_AN_OBJECT, f"disturbance must be an object, got {disturbance!r}")
    parameters = disturbance.get("parameters", {})
    kind = disturbance.get("kind")
    fv.refuse_first(
        (
            (
                not isinstance(parameters, dict),
                fv.FINDING_INPUT_NOT_AN_OBJECT,
                f"disturbance.parameters must be an object, got {parameters!r}",
            ),
            (
                not envelope.is_enum_value(kind, fv.DISTURBANCES),
                fv.FINDING_DISTURBANCE_KIND_UNKNOWN,
                f"unknown disturbance kind: {kind!r}",
            ),
        )
    )
    return kind, parameters


def _presence_problems(kind: str, parameters: dict[str, Any]) -> tuple[Problem, ...]:
    """Every required parameter present, nothing the kind does not read."""
    required, optional = fv.PARAMETER_SPEC[kind]
    missing = sorted(key for key in required if key not in parameters)
    unknown = sorted(str(key) for key in set(parameters) - set(required) - set(optional))
    return (
        (
            bool(missing),
            fv.FINDING_PARAMETER_MISSING,
            f"{kind} needs parameters {missing}; a missing parameter would run as a no-op",
        ),
        (
            bool(unknown),
            fv.FINDING_PARAMETER_UNKNOWN,
            f"{kind} does not use parameters {unknown}; it reads {sorted(required + optional)}",
        ),
    )


def _channel_shape_problems(kind: str, parameters: dict[str, Any]) -> tuple[Problem, ...]:
    """``channels`` must be a list, non-empty where the kind requires it."""
    if "channels" not in parameters:
        return ()
    channels = parameters["channels"]
    return (
        (
            not isinstance(channels, list),
            fv.FINDING_CHANNELS_NOT_A_LIST,
            f"{kind} channels must be a list of channel names, got {channels!r}; "
            "anything else would run as a no-op",
        ),
        (
            _requires_channels(kind) and channels == [],
            fv.FINDING_CHANNELS_EMPTY,
            f"{kind} channels must name at least one channel; an empty list would run "
            "the declared disturbance as a no-op",
        ),
    )


# (key, floor, exclusive): below the floor the declared disturbance cannot occur.
_FLOORS = (
    ("onset_ms", 0.0, False), ("duration_ms", 0.0, True), ("jitter_ms", 0.0, True),
    ("ramp_ms", 0.0, True), ("delay_ms", 0.0, True),
)
_ABOVE_FLOOR = {True: operator.gt, False: operator.ge}
_FLOOR_SIGN = {True: ">", False: ">="}


def _floor_holds(value: Any, floor: float, exclusive: bool) -> bool:
    return envelope.is_number(value) and _ABOVE_FLOOR[exclusive](value, floor)


def _floor_problems(kind: str, parameters: dict[str, Any]) -> Iterable[Problem]:
    for key, floor, exclusive in _FLOORS:
        if key in parameters:
            value = parameters[key]
            yield (
                not _floor_holds(value, floor, exclusive),
                fv.FINDING_PARAMETER_OUT_OF_DOMAIN,
                f"{kind} {key} must be a finite number {_FLOOR_SIGN[exclusive]} {floor}, got "
                f"{value!r}; outside that range the declared disturbance cannot occur",
            )


def _is_malformed_kind(value: Any) -> bool:
    return envelope.is_enum_value(value, fv.MALFORMED_KINDS)


# (key, predicate, expected text): per-kind value domains over the keys
# present. ``malformed_kind`` is an enum because the tick loop branches on it.
_VALUE_RULES: tuple[tuple[str, Predicate, str], ...] = (
    ("peak_c", finite_number, "a finite number"),
    ("malformed_count", genuine_count_from(1), "an integer >= 1; a burst of zero events is a no-op"),
    ("malformed_kind", _is_malformed_kind, f"one of {sorted(fv.MALFORMED_KINDS)}"),
    (
        "corrupt_ratio",
        unit_interval,
        "a finite number in [0, 1]; outside that range the declared corruption cannot be applied",
    ),
)


def _value_problems(kind: str, parameters: dict[str, Any]) -> Iterable[Problem]:
    for key, holds, expected in _VALUE_RULES:
        if key in parameters:
            value = parameters[key]
            yield (
                not holds(value),
                fv.FINDING_PARAMETER_OUT_OF_DOMAIN,
                f"{kind} {key} must be {expected}, got {value!r}",
            )


def _onset_problem(kind: str, parameters: dict[str, Any], system: dict[str, Any]) -> None:
    """The onset must fall on or before the last simulated tick (floors ran first)."""
    if "onset_ms" not in parameters:
        return
    onset = parameters["onset_ms"]
    last_tick_ms = (system["ticks"] - 1) * system["tick_ms"]
    fv.refuse_when(
        onset > last_tick_ms,
        fv.FINDING_ONSET_BEYOND_HORIZON,
        f"{kind} onset_ms {onset} is beyond the last simulated tick at {last_tick_ms} ms "
        f"({system['ticks']} ticks x {system['tick_ms']} ms); the declared disturbance "
        "would never occur",
    )


def _window_problem(kind: str, parameters: dict[str, Any], system: dict[str, Any]) -> None:
    """The half-open window ``[onset, onset + duration)`` must contain a simulated tick.

    The onset check keeps the onset on the grid's span; a window shorter than
    the gap to the next tick would still run as a no-op and be labelled as if
    the disturbance had happened (row 12's class).
    """
    if "duration_ms" not in parameters or "onset_ms" not in parameters:
        return
    onset, duration, tick_ms = parameters["onset_ms"], parameters["duration_ms"], system["tick_ms"]
    first = math.ceil(onset / tick_ms)
    applied = first < system["ticks"] and first * tick_ms < onset + duration
    fv.refuse_when(
        not applied,
        fv.FINDING_DISTURBANCE_WINDOW_EMPTY,
        f"{kind} window [{onset}, {onset + duration}) ms contains no simulated tick on the "
        f"{tick_ms} ms grid; the declared disturbance would never be applied",
    )


def _capacity_problem(
    kind: str, parameters: dict[str, Any], affected: tuple[str, ...], system: dict[str, Any]
) -> None:
    """A malformed burst emits at most one event per distinct affected channel per tick.

    The simulator visits each live channel once per tick, so a name declared
    twice adds no capacity.
    """
    if kind != fv.MALFORMED_SPIKE_BURST:
        return
    live = len(set(affected))
    capacity = system["ticks"] * live
    count = parameters["malformed_count"]
    fv.refuse_when(
        count > capacity,
        fv.FINDING_PARAMETER_OUT_OF_DOMAIN,
        f"{kind} malformed_count {count} exceeds the run's capacity of {capacity} events "
        f"({system['ticks']} ticks x {live} distinct affected channels); the burst would be "
        "silently truncated",
    )


def _peak_problem(kind: str, parameters: dict[str, Any], system: dict[str, Any]) -> None:
    """Row 2: a thermal excursion must peak above ambient (value rules ran first).

    The span ``peak_c - ambient_c`` must also be a finite number: the ramp
    computes ``ambient + fraction * span``, and two individually finite
    controls whose difference overflows would yield an infinite temperature
    trace and reading (the row-7 horizon guard, applied to degrees).
    """
    if kind != fv.THERMAL_EXCURSION:
        return
    peak, ambient = parameters["peak_c"], system["ambient_c"]
    fv.refuse_first(
        (
            (
                peak <= ambient,
                fv.FINDING_PEAK_NOT_ABOVE_AMBIENT,
                f"{kind} peak_c {peak!r} is not above ambient_c {ambient!r}; a heating-only "
                "excursion that never leaves ambient would run as a no-op",
            ),
            (
                not envelope.is_number(peak - ambient),
                fv.FINDING_PARAMETER_OUT_OF_DOMAIN,
                f"{kind} peak_c {peak!r} minus ambient_c {ambient!r} is not a finite span "
                "of degrees; the ramp would produce an infinite temperature",
            ),
        )
    )


def _known_names(system: dict[str, Any]) -> set[str]:
    known = set(system["channels"])
    if system.get("fallback_source"):
        known.add(system["fallback_source"])
    return known


def _is_known(name: Any, known: set[str]) -> bool:
    return isinstance(name, str) and name in known


def _declared_channels(kind: str, parameters: dict[str, Any], system: dict[str, Any]) -> tuple[str, ...]:
    """Every declared name, each a relay channel or the fallback source."""
    declared = parameters.get("channels", [])
    known = _known_names(system)
    unknown = sorted(str(name) for name in declared if not _is_known(name, known))
    fv.refuse_when(
        bool(unknown),
        fv.FINDING_CHANNEL_UNKNOWN,
        f"{kind} declares unknown channels {unknown}; this relay reads {sorted(known)} "
        "-- an unknown name would run as a no-op",
    )
    return tuple(declared)


def _affected(kind: str, declared: tuple[str, ...], system: dict[str, Any]) -> tuple[str, ...]:
    """The relay's own channels among the declared; a required list may not narrow to none."""
    relay = set(system["channels"])
    affected = tuple(name for name in declared if name in relay)
    fv.refuse_when(
        _requires_channels(kind) and not affected,
        fv.FINDING_CHANNELS_NO_RELAY_CHANNEL,
        f"{kind} channels {list(declared)} names only the fallback source; "
        "the declared disturbance would run as a no-op",
    )
    return affected


def checked_disturbance(disturbance: Any, system: dict[str, Any]) -> Disturbance:
    """The checked disturbance against an effective system (``checked_system``).

    Stage order, kept from #138: shape and kind, presence, channel shape,
    floors, value rules, onset, window, peak, declared names, affected
    narrowing, burst capacity.
    """
    _effective_system(system)
    kind, parameters = _disturbance_of(disturbance)
    fv.refuse_first(_presence_problems(kind, parameters))
    fv.refuse_first(_channel_shape_problems(kind, parameters))
    fv.refuse_first(_floor_problems(kind, parameters))
    fv.refuse_first(_value_problems(kind, parameters))
    _onset_problem(kind, parameters, system)
    _window_problem(kind, parameters, system)
    _peak_problem(kind, parameters, system)
    declared = _declared_channels(kind, parameters, system)
    affected = _affected(kind, declared, system)
    _capacity_problem(kind, parameters, affected, system)
    return Disturbance(kind, dict(parameters), affected, declared)


bind_import_twin(__name__)
