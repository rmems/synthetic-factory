#!/usr/bin/env python3
"""Fault-family contract for ``neuromorphic-fault-recovery``.

Split out of ``fault_simulator.py`` verbatim: the disturbance/outcome
vocabulary and parameter contract, :class:`FaultOracle` +
:class:`FaultResult` record shapes, the ``_DisturbanceSpec`` + corruption-tick
selection, the numeric coercions the validators share, ``_oracle_meters`` and
``describe``. Re-exported through ``fault_simulator`` / ``fault_recovery`` so
call sites resolve unchanged.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from oracle_grounded import distill_contract as oc  # noqa: E402
from oracle_grounded import fault_vocabulary  # noqa: E402


FAMILY = "neuromorphic-fault-recovery"
GENERATOR_NAME = "fault-scenario-generator"
GENERATOR_VERSION = "1.0.0"
ORACLE_NAME = "relay-reflex-sim"
ORACLE_VERSION = "1.0.0"
ORACLE_IMPLEMENTATION = "pipelines/fault_recovery.py:RelayReflexSimulator"

# The nine disturbances named in issue #78.
DISTURBANCES = (
    "sensor_loss",
    "stale_sensor",
    "event_jitter",
    "burst_corruption",
    "thermal_excursion",
    "missing_channel",
    "malformed_spike_burst",
    "delayed_result",
    "temporary_saturation",
)

# The six outcomes named in issue #78, canonicalised to snake_case. The prose
# spelling from the issue is preserved in OUTCOME_LABELS and mirrored into the
# record as ``result.outcome_label`` so the vocabulary stays traceable.
OUTCOMES = (
    "continue",
    "degrade_gracefully",
    "fallback",
    "reflex_action",
    "quarantine",
    "fail_closed",
)

OUTCOME_LABELS = {
    "continue": "continue",
    "degrade_gracefully": "degrade gracefully",
    "fallback": "fallback",
    "reflex_action": "reflex action",
    "quarantine": "quarantine",
    "fail_closed": "fail closed",
}

# Outcome precedence, most protective first. The simulator evaluates rules in
# this order and stops at the first match.
OUTCOME_PRECEDENCE = (
    "fail_closed",
    "quarantine",
    "reflex_action",
    "fallback",
    "degrade_gracefully",
    "continue",
)

MALFORMED_KINDS = ("non_monotonic_time", "negative_amplitude", "unknown_channel")

# A malformed burst is not one failure. Times that go backwards and amplitudes
# that go negative are corruption *inside* an accepted stream — the relay
# cannot tell which events to trust, so the stream is quarantined. Events tagged
# with a channel the relay does not know are rejected at the boundary instead:
# nothing trusted was corrupted, so they count as drops.
MALFORMED_INTEGRITY_KINDS = frozenset({"non_monotonic_time", "negative_amplitude"})

# Parameters each disturbance consumes. Validated on every run, because a
# parameter the simulator silently ignores turns a scenario into a no-op that
# still looks like a disturbance in the record.
PARAMETER_SPEC: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "sensor_loss": (("channels", "onset_ms", "duration_ms"), ()),
    "stale_sensor": (("channels", "onset_ms", "duration_ms"), ()),
    "event_jitter": (("channels", "onset_ms", "duration_ms", "jitter_ms"), ()),
    "burst_corruption": (
        ("channels", "onset_ms", "duration_ms", "corrupt_ratio"),
        (),
    ),
    "thermal_excursion": (("onset_ms", "ramp_ms", "peak_c"), ("channels",)),
    "missing_channel": (("channels",), ()),
    "malformed_spike_burst": (
        ("channels", "malformed_count", "malformed_kind"),
        (),
    ),
    "delayed_result": (("delay_ms",), ("channels",)),
    "temporary_saturation": (("channels", "onset_ms", "duration_ms"), ()),
}


class FaultOracle:
    """Boundary a fault-recovery oracle must implement.

    ``RelayReflexSimulator`` is the deterministic reference. A hardware replay
    oracle would implement the same two methods and declare its own
    fingerprint; it is not available in this environment.
    """

    name = "abstract"
    version = "0"
    oracle_type = "deterministic_simulator"
    authority = oc.AUTHORITY_AUTHORITATIVE
    implementation = "pipelines/fault_recovery.py:FaultOracle"

    # Meter identities for the measurements ``build_records`` derives from a
    # result. Only the oracle that actually ran knows what measured its
    # readings — a hardware replay attributing its latencies to
    # ``simulator_clock`` would be false provenance — so every concrete
    # oracle must declare its own meters. ``build_records`` fails closed when
    # these are unset.
    meter_clock: str | None = None
    meter_state: str | None = None
    meter_thermal: str | None = None

    def run(self, scenario: dict[str, Any], disturbance: dict[str, Any]) -> "FaultResult":
        raise NotImplementedError

    def oracle_block(self, scenario: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


@dataclass(frozen=True)
class FaultResult:
    """One executed disturbance: the outcome plus the state it was read from."""

    outcome: str
    reason_codes: tuple[str, ...]
    # Both latencies are relative to the disturbance onset, not to the start of
    # the run, so identical faults at different onsets carry identical labels.
    detection_latency_ms: float | None
    recovery_latency_ms: float
    worst_healthy_channels: int
    dropped_events: int
    corrupt_events: int
    total_events: int
    peak_temperature_c: float
    max_staleness_ms: float
    max_jitter_ms: float
    saturated_ticks: int
    integrity_violation: bool
    result_delay_ms: float
    trace: tuple[dict[str, Any], ...] = field(default=())

    @property
    def realised_corrupt_ratio(self) -> float:
        """Corrupted share of the event stream the simulator actually applied.

        The generator asks for a ``corrupt_ratio``; the tick grid can only
        approximate it. Recording what landed keeps the label honest about the
        severity that was simulated rather than the one that was requested.
        """

        if self.total_events <= 0:
            return 0.0
        return self.corrupt_events / self.total_events

    @property
    def residual_error(self) -> float:
        if self.total_events <= 0:
            return 0.0
        return (self.corrupt_events + self.dropped_events) / self.total_events


# The shared vocabulary module owns the default relay system; this pipeline's
# DEFAULT_SYSTEM is a copy so call sites never share a mutable dict.
DEFAULT_SYSTEM: dict[str, Any] = dict(fault_vocabulary.DEFAULT_SYSTEM)


@dataclass(frozen=True)
class _DisturbanceSpec:
    """The coerced numeric parameters one simulated disturbance consumes."""

    kind: str
    affected: tuple[str, ...]
    onset_ms: float
    duration_ms: float
    jitter_ms: float
    corrupt_ratio: float
    malformed_count: int
    malformed_kind: str
    peak_c: float
    ramp_ms: float
    result_delay_ms: float

    def in_window(self, now_ms: float) -> bool:
        return self.onset_ms <= now_ms < (self.onset_ms + self.duration_ms)


def _spec_from_parameters(
    kind: str,
    params: dict[str, Any],
    system: dict[str, Any],
    affected: list[str],
) -> _DisturbanceSpec:
    return _DisturbanceSpec(
        kind=kind,
        affected=tuple(affected),
        onset_ms=float(params.get("onset_ms", 0.0)),
        duration_ms=float(params.get("duration_ms", 0.0)),
        jitter_ms=float(params.get("jitter_ms", 0.0)),
        corrupt_ratio=float(params.get("corrupt_ratio", 0.0)),
        malformed_count=int(params.get("malformed_count", 0)),
        malformed_kind=str(params.get("malformed_kind") or ""),
        peak_c=float(params.get("peak_c", system["ambient_c"])),
        ramp_ms=max(float(params.get("ramp_ms", 1.0)), 1e-6),
        result_delay_ms=float(params.get("delay_ms", 0.0)),
    )


def _phase_hit(tick: int, corrupt_ratio: float) -> bool:
    return ((tick * 7919) % 1000) / 1000.0 < corrupt_ratio


def _corruption_ticks(spec: _DisturbanceSpec, system: dict[str, Any]) -> frozenset[int]:
    """Keep the existing phase, with one real event when a positive burst misses it."""
    eligible = _corruption_window(spec, system)
    selected = [tick for tick in eligible if _phase_hit(tick, spec.corrupt_ratio)]
    if selected:
        return frozenset(selected)
    return frozenset(eligible[:1])


def _corruption_window(spec: _DisturbanceSpec, system: dict[str, Any]) -> list[int]:
    """The in-window ticks, with fail-closed guards on the burst declaration."""

    if spec.kind != "burst_corruption" or spec.corrupt_ratio == 0:
        return []
    if not spec.affected:
        raise oc.ContractError("positive corruption requires a sampled primary channel")
    eligible = _windowed_ticks(
        spec, int(system["ticks"]), float(system["tick_ms"])
    )
    if not eligible:
        raise oc.ContractError("positive corruption window contains no sampled event")
    return eligible


def _windowed_ticks(spec: _DisturbanceSpec, ticks: int, tick_ms: float) -> list[int]:
    return [tick for tick in range(ticks) if spec.in_window(tick * tick_ms)]




def _positive_number(value: Any) -> bool:
    return oc.is_number(value) and float(value) > 0.0


def _non_negative_number(value: Any) -> bool:
    return oc.is_number(value) and float(value) >= 0.0


def _unit_interval(value: Any) -> bool:
    return oc.is_number(value) and 0.0 <= float(value) <= 1.0


def _genuine_count(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _genuine_count_from(floor: int, ceiling: int | None = None):
    """A predicate for a genuine (non-boolean) integer >= ``floor``.

    ``ceiling`` bounds the value inclusively when given — the validator
    replays untrusted scenarios, so unbounded loop controls would let one
    record buy an arbitrarily large replay workload.
    """

    def _valid(value: Any) -> bool:
        return (
            isinstance(value, int)
            and not isinstance(value, bool)
            and value >= floor
            and (ceiling is None or value <= ceiling)
        )

    return _valid



def _oracle_meters(engine: FaultOracle) -> dict[str, str]:
    """The meter identities the oracle declares for its readings.

    Hard-coding ``simulator_*`` here would stamp false measurement provenance
    onto every record an injected non-simulator oracle (a hardware replay)
    produced, so an oracle that does not declare its meters is refused.
    """

    meters = {
        "clock": engine.meter_clock,
        "state": engine.meter_state,
        "thermal": engine.meter_thermal,
    }
    unset = sorted(
        role
        for role, meter in meters.items()
        if not isinstance(meter, str) or not meter.strip()
    )
    if unset:
        raise oc.ContractError(
            f"oracle {engine.name!r} does not declare its measurement meters "
            f"({unset}); readings cannot be attributed to an unnamed instrument"
        )
    return meters

def describe() -> dict[str, Any]:
    """Machine-readable summary of the family contract."""

    return {
        "family": FAMILY,
        "disturbances": list(DISTURBANCES),
        "outcomes": list(OUTCOMES),
        "outcome_labels": dict(OUTCOME_LABELS),
        "precedence": list(OUTCOME_PRECEDENCE),
        "oracle": {
            "name": ORACLE_NAME,
            "type": "deterministic_simulator",
            "implementation": ORACLE_IMPLEMENTATION,
            "authority": oc.AUTHORITY_AUTHORITATIVE,
            "hardware_replay": "not available in this environment",
        },
        "default_system": dict(DEFAULT_SYSTEM),
    }
