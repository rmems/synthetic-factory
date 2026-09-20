#!/usr/bin/env python3
"""Disturbance/system preflight for ``neuromorphic-fault-recovery``.

Split out of ``fault_simulator.py`` verbatim: the validation pass
:class:`fault_simulator.RelayReflexSimulator` runs before stepping — the
declared-parameter contract, onset/window bounds, channel-list shape, thermal
ladder, and system-channel/control checks. Raising ``oc.ContractError`` here
is how a malformed scenario fails closed instead of simulating a record that
never happened.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from oracle_grounded import distill_contract as oc  # noqa: E402

if __package__:
    from .fault_types import MALFORMED_KINDS, PARAMETER_SPEC
else:
    from fault_types import MALFORMED_KINDS, PARAMETER_SPEC

if TYPE_CHECKING:
    if __package__:
        from .fault_types import _DisturbanceSpec
    else:
        from fault_types import _DisturbanceSpec


def _check_parameters(
    kind: str, parameters: dict[str, Any], system: dict[str, Any]
) -> None:
    """Refuse a disturbance this simulator would silently ignore.

    Missing parameters used to default to zero, so a plausible-looking
    disturbance could run as a no-op and still be recorded as a scenario.
    An unexpected parameter is refused for the same reason: writing
    ``duration_ms`` where the kind reads ``stale_age_ms`` should be an
    error, not a quietly discarded intention.
    """

    required, optional = PARAMETER_SPEC[kind]
    missing = [key for key in required if key not in parameters]
    if missing:
        raise oc.ContractError(
            f"{kind} needs parameters {sorted(missing)}; a missing parameter "
            "would run as a no-op"
        )
    unknown = sorted(set(parameters) - set(required) - set(optional))
    if unknown:
        raise oc.ContractError(
            f"{kind} does not use parameters {unknown}; it reads "
            f"{sorted(required + optional)}"
        )
    _check_parameter_values(kind, parameters, system)

# Numeric parameter floors. A value outside these cannot produce the
# declared disturbance — a negative duration never opens the active
# window, a non-positive jitter or delay perturbs nothing — so the run
# would be a no-op wearing a disturbance's name.
_PARAMETER_FLOORS: tuple[tuple[str, float, bool], ...] = (
    ("onset_ms", 0.0, False),
    ("duration_ms", 0.0, True),
    ("jitter_ms", 0.0, True),
    ("ramp_ms", 0.0, True),
    ("delay_ms", 0.0, True),
)

def _check_onset_within_horizon(
    kind: str, parameters: dict[str, Any], system: dict[str, Any]
) -> None:
    """The declared onset must fall inside the simulated window.

    The non-negative floor alone let ``onset_ms`` sit at or beyond the
    last observable tick, so the active window never opened and a
    declared fault replayed as an authoritative ``continue`` — a no-op
    wearing a disturbance's name, bounded by the recorded horizon rather
    than by any fixed constant.
    """

    onset = parameters.get("onset_ms")
    if not oc.is_number(onset):
        return
    last_tick_ms = (int(system["ticks"]) - 1) * float(system["tick_ms"])
    if float(onset) > last_tick_ms:
        raise oc.ContractError(
            f"{kind} onset_ms {onset} is beyond the last simulated tick "
            f"at {last_tick_ms} ms ({system['ticks']} ticks x "
            f"{system['tick_ms']} ms); the declared disturbance would "
            "never occur"
        )
    if kind == "thermal_excursion" and float(onset) >= last_tick_ms:
        # The ramp is evaluated at fraction zero on the onset tick
        # itself, so an onset on the last tick never raises the
        # temperature; the excursion replays as an authoritative no-op.
        raise oc.ContractError(
            f"{kind} onset_ms {onset} leaves no sampled tick after the "
            f"onset (last tick at {last_tick_ms} ms); the ramp never "
            "rises and the declared excursion would run as a no-op"
        )

def _check_sampled_window(kind: str, parameters: dict[str, Any], system: dict[str, Any]) -> None:
    """Duration-based disturbances must affect at least one actual tick."""

    if "duration_ms" not in parameters:
        return
    onset = float(parameters["onset_ms"])
    end = onset + float(parameters["duration_ms"])
    tick_ms = float(system["tick_ms"])
    if not any(onset <= tick * tick_ms < end for tick in range(system["ticks"])):
        raise oc.ContractError(f"{kind} window contains no sampled tick")

def _check_declared_channel_list(kind: str, parameters: dict[str, Any]) -> None:
    """A declared channel list must be a list, and non-empty where required.

    ``channels: []`` (or a non-list) narrowed to no affected channels, so
    ``sensor_loss``, ``event_jitter``, ``temporary_saturation`` and
    ``malformed_spike_burst`` applied no fault at all and the replayed
    no-op produced an authoritative ``continue``/``WITHIN_TOLERANCE``
    label for a disturbance that was never simulated.
    """

    required, _ = PARAMETER_SPEC[kind]
    if "channels" not in parameters:
        return
    channels = parameters["channels"]
    if not isinstance(channels, list):
        raise oc.ContractError(
            f"{kind} channels must be a list of channel names, got "
            f"{channels!r}; anything else would run as a no-op"
        )
    if "channels" in required and not channels:
        raise oc.ContractError(
            f"{kind} channels must name at least one channel; an empty "
            "list would run the declared disturbance as a no-op"
        )

def _check_parameter_values(
    kind: str, parameters: dict[str, Any], system: dict[str, Any]
) -> None:
    """Value ranges whose violation would also run as a silent no-op."""

    _check_declared_channel_list(kind, parameters)
    _check_parameter_floors(kind, parameters)
    if "peak_c" in parameters and not oc.is_number(parameters["peak_c"]):
        raise oc.ContractError(
            f"{kind} peak_c must be a finite number, got "
            f"{parameters['peak_c']!r}"
        )
    if kind == "thermal_excursion":
        _check_thermal_peak(parameters, system)
    if kind == "malformed_spike_burst":
        _check_malformed_burst(parameters)
    if kind == "burst_corruption":
        _check_corruption_ratio(parameters)


def _check_thermal_peak(parameters: dict[str, Any], system: dict[str, Any]) -> None:
    if not oc.is_number(parameters.get("peak_c")):
        return
    ambient = float(system["ambient_c"])
    if float(parameters["peak_c"]) <= ambient:
        # _update_thermal keeps the running maximum with ambient, so
        # a peak at or below it never heats the relay — the declared
        # excursion replays as an authoritative no-op.
        raise oc.ContractError(
            f"thermal_excursion peak_c {parameters['peak_c']} must exceed the "
            f"ambient temperature {ambient}; the relay can never "
            "warm to it"
        )


def _check_touches_primary(kind: str, declared: list[str], channels: list[str]) -> None:
    if any(name in channels for name in declared):
        return
    # The tick loop visits primary channels only, so a required list
    # naming only the fallback source applies no events at all — the
    # declared channel fault replays as an authoritative no-op.
    raise oc.ContractError(
        f"{kind} channels must name at least one primary relay "
        "channel; the fallback source alone leaves the declared "
        "disturbance with nothing to affect"
    )

def _check_malformed_burst(parameters: dict[str, Any]) -> None:
    count = parameters.get("malformed_count")
    if not oc.is_genuine_int(count) or count < 1:
        raise oc.ContractError(
            f"malformed_count must be an integer >= 1, got {count!r}; "
            "a burst of zero events is a no-op"
        )
    # The tick loop branches on this value. A typo used to fall through
    # to the `unknown_channel` arm, so `negative_amplitdue` became a
    # dropped event and produced `degrade_gracefully` — an authoritative
    # label for a disturbance the simulator never defined.
    variant = parameters.get("malformed_kind")
    if not oc.is_enum_value(variant, MALFORMED_KINDS):
        raise oc.ContractError(
            f"malformed_kind must be one of {sorted(MALFORMED_KINDS)}, "
            f"got {variant!r}"
        )

def _check_corruption_ratio(parameters: dict[str, Any]) -> None:
    # The tick comparison can never mark an event corrupt for a ratio
    # below 0, so a negative (or NaN) ratio runs the declared
    # disturbance as a no-op and the simulator emits an authoritative
    # `continue` for a corruption that was requested but never applied.
    ratio = parameters.get("corrupt_ratio")
    # The bound is strict at zero: the tick comparison marks no event
    # corrupt for a ratio of 0, so a zero ratio also runs the declared
    # disturbance as a no-op and earns an authoritative `continue`.
    if not oc.is_number(ratio) or not 0.0 < float(ratio) <= 1.0:
        raise oc.ContractError(
            f"corrupt_ratio must be a finite number in (0, 1], got "
            f"{ratio!r}; outside that range the declared corruption "
            "cannot be applied"
        )

def _check_parameter_floors(kind: str, parameters: dict[str, Any]) -> None:
    """Require finite values within each disturbance parameter's domain."""

    for key, floor, exclusive in _PARAMETER_FLOORS:
        if key not in parameters:
            continue
        value = parameters[key]
        if not oc.is_number(value) or (
            value <= floor if exclusive else value < floor
        ):
            raise oc.ContractError(
                f"{kind} {key} must be a finite number "
                f"{'>' if exclusive else '>='} {floor}, got {value!r}; "
                "outside that range the declared disturbance cannot occur"
            )

def _affected(parameters: dict[str, Any], channels: list[str]) -> list[str]:
    """Narrow the disturbance's declared channels to the relay's own."""

    affected = parameters.get("channels")
    if not isinstance(affected, list) or not affected:
        return []
    return [channel for channel in affected if channel in channels]

def _declared_channels(
    kind: str,
    parameters: dict[str, Any],
    system: dict[str, Any],
    channels: list[str],
) -> list[str]:
    """Every channel name the disturbance claims, all of them known.

    A declared channel the relay does not know cannot be silently narrowed
    away: the whole disturbance (or part of it) would run as a no-op while
    the record still claims it was simulated, and the no-op replays as an
    authoritative ``continue``. The only names a disturbance may touch are
    the relay's own channels and the fallback source.
    """

    declared = parameters.get("channels")
    declared = list(declared) if isinstance(declared, list) else []
    known = _known_channel_names(system, channels)
    unknown_names = _unknown_channel_names(declared, known)
    if unknown_names:
        raise oc.ContractError(
            f"{kind} declares unknown channels {unknown_names}; this relay "
            f"reads {sorted(known)} — an unknown name would run as a no-op"
        )
    required, _ = PARAMETER_SPEC[kind]
    if "channels" in required:
        _check_touches_primary(kind, declared, channels)
    return declared


def _known_channel_names(system: dict[str, Any], channels: list[str]) -> set[str]:
    known = set(channels)
    fallback_source = system.get("fallback_source")
    if fallback_source:
        known.add(fallback_source)
    return known


def _unknown_channel_names(declared: list[Any], known: set[str]) -> list[str]:
    return sorted(
        str(name)
        for name in declared
        if not isinstance(name, str) or name not in known
    )

def _detection_latency_ms(
    detection_ms: float | None, spec: "_DisturbanceSpec", system: dict[str, Any]
) -> float | None:
    if detection_ms is None and spec.result_delay_ms > float(system["deadline_ms"]):
        # A late result is only observable once its deadline passes.
        detection_ms = float(system["deadline_ms"])

    # Latency is measured from the disturbance, not from the start of the
    # run. Otherwise two identical faults beginning at 4 ms and 12 ms get
    # labels 8 ms apart despite identical post-onset behaviour, and the
    # target learns the arbitrary pre-fault idle time.
    if detection_ms is not None:
        detection_ms = round(max(detection_ms - spec.onset_ms, 0.0), 3)
    return detection_ms
