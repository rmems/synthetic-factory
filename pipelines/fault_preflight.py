#!/usr/bin/env python3
"""Disturbance/system preflight for ``neuromorphic-fault-recovery``.

Split out of ``fault_simulator.py`` verbatim: the validation pass
:class:`fault_simulator.RelayReflexSimulator` runs before stepping — onset and
sampled-window bounds against the simulated horizon, the declared-channel
identity rules, and detection-latency accounting. The declared-parameter
contract lives in ``fault_parameters``. Raising
``oc.ContractError`` is how a malformed scenario fails closed instead of
simulating a record that never happened.
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
    from .fault_types import PARAMETER_SPEC
else:
    from fault_types import PARAMETER_SPEC

if TYPE_CHECKING:
    if __package__:
        from .fault_types import _DisturbanceSpec
    else:
        from fault_types import _DisturbanceSpec


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
    if kind != "thermal_excursion":
        return
    if float(onset) >= last_tick_ms:
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

def _affected(parameters: dict[str, Any], channels: list[str]) -> list[str]:
    """Narrow the disturbance's declared channels to the relay's own."""

    affected = parameters.get("channels")
    if not isinstance(affected, list):
        return []
    if not affected:
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
    if detection_ms is None:
        if spec.result_delay_ms > float(system["deadline_ms"]):
            # A late result is only observable once its deadline passes.
            detection_ms = float(system["deadline_ms"])

    # Latency is measured from the disturbance, not from the start of the
    # run. Otherwise two identical faults beginning at 4 ms and 12 ms get
    # labels 8 ms apart despite identical post-onset behaviour, and the
    # target learns the arbitrary pre-fault idle time.
    if detection_ms is not None:
        detection_ms = round(max(detection_ms - spec.onset_ms, 0.0), 3)
    return detection_ms
