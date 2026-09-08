#!/usr/bin/env python3
"""Disturbance refusals for the fault-recovery family (F1).

A disturbance the simulator would run as a no-op -- a missing or unknown
parameter, a value under its floor or outside its domain, a channel list that
is not a list, empty where required, naming an unknown channel or only the
fallback source, an onset beyond the horizon, or (D7 row 2) a thermal peak
that never leaves ambient -- is refused with a coded ``FaultRefusal`` before
any state exists. The stages keep #138's order so every check sees typed
values; :func:`checked_disturbance` returns the frozen :class:`Disturbance`.
"""

from __future__ import annotations

import operator
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any

from . import envelope
from . import fault_config as config
from . import fault_vocabulary as fv
from .import_twins import bind_import_twin

Problem = tuple[bool, str, str]


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
_VALUE_RULES: tuple[tuple[str, Callable[[Any], bool], str], ...] = (
    ("peak_c", config.finite_number, "a finite number"),
    ("malformed_count", config.genuine_count_from(1), "an integer >= 1; a burst of zero events is a no-op"),
    ("malformed_kind", _is_malformed_kind, f"one of {sorted(fv.MALFORMED_KINDS)}"),
    (
        "corrupt_ratio",
        config.unit_interval,
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
    floors, value rules, onset, peak, declared names, affected narrowing.
    """
    kind, parameters = _disturbance_of(disturbance)
    fv.refuse_first(_presence_problems(kind, parameters))
    fv.refuse_first(_channel_shape_problems(kind, parameters))
    fv.refuse_first(_floor_problems(kind, parameters))
    fv.refuse_first(_value_problems(kind, parameters))
    _onset_problem(kind, parameters, system)
    _peak_problem(kind, parameters, system)
    declared = _declared_channels(kind, parameters, system)
    return Disturbance(kind, dict(parameters), _affected(kind, declared, system), declared)


bind_import_twin(__name__)
