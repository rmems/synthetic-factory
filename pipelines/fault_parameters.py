#!/usr/bin/env python3
"""Declared-parameter contract for ``neuromorphic-fault-recovery`` disturbances.

Split out of ``fault_preflight.py`` verbatim: every check that binds the
declared disturbance's *parameter block* — required/unknown names, the channel
list's shape, numeric floors, and the per-kind value rules — so a malformed
disturbance refuses instead of simulating a no-op wearing a disturbance's
name. ``fault_preflight`` re-exports :func:`_check_parameters` for callers
that imported it from there.
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
    from .fault_types import MALFORMED_KINDS, PARAMETER_SPEC
else:
    from fault_types import MALFORMED_KINDS, PARAMETER_SPEC


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
    _require_declared_parameters(kind, parameters, required)
    _refuse_unknown_parameters(kind, parameters, required, optional)
    _check_parameter_values(kind, parameters, system)

def _require_declared_parameters(
    kind: str, parameters: dict[str, Any], required: list[str]
) -> None:
    missing = [key for key in required if key not in parameters]
    if missing:
        raise oc.ContractError(
            f"{kind} needs parameters {sorted(missing)}; a missing parameter "
            "would run as a no-op"
        )

def _refuse_unknown_parameters(
    kind: str,
    parameters: dict[str, Any],
    required: list[str],
    optional: list[str],
) -> None:
    unknown = sorted(set(parameters) - set(required) - set(optional))
    if unknown:
        raise oc.ContractError(
            f"{kind} does not use parameters {unknown}; it reads "
            f"{sorted(required + optional)}"
        )

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
    _require_channel_list(kind, channels)
    _require_named_channels(kind, required, channels)

def _require_channel_list(kind: str, channels: Any) -> None:
    if not isinstance(channels, list):
        raise oc.ContractError(
            f"{kind} channels must be a list of channel names, got "
            f"{channels!r}; anything else would run as a no-op"
        )

def _require_named_channels(
    kind: str, required: list[str], channels: list[Any]
) -> None:
    if "channels" not in required:
        return
    if channels:
        return
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
    _check_peak_value(kind, parameters)
    if kind == "thermal_excursion":
        _check_thermal_peak(parameters, system)
    elif kind == "malformed_spike_burst":
        _check_malformed_burst(parameters)
    elif kind == "burst_corruption":
        _check_corruption_ratio(parameters)

def _check_peak_value(kind: str, parameters: dict[str, Any]) -> None:
    if "peak_c" not in parameters:
        return
    if oc.is_number(parameters["peak_c"]):
        return
    raise oc.ContractError(
        f"{kind} peak_c must be a finite number, got "
        f"{parameters['peak_c']!r}"
    )


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
    # The bound is strict at zero: the tick comparison can never mark an
    # event corrupt for a ratio at 0 or below, so a non-positive (or NaN)
    # ratio runs the declared disturbance as a no-op and the simulator
    # emits an authoritative `continue` for a corruption that was
    # requested but never applied.
    ratio = parameters.get("corrupt_ratio")
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
        if _violates_floor(value, floor, exclusive):
            bound = f"> {floor}" if exclusive else f">= {floor}"
            raise oc.ContractError(
                f"{kind} {key} must be a finite number {bound}, got "
                f"{value!r}; outside that range the declared "
                "disturbance cannot occur"
            )

def _violates_floor(value: Any, floor: float, exclusive: bool) -> bool:
    if not oc.is_number(value):
        return True
    if exclusive:
        return value <= floor
    return value < floor
