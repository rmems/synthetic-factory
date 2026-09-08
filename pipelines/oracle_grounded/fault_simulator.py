#!/usr/bin/env python3
"""The deterministic tick-grid relay of the fault-recovery family (F1).

The simulator is the oracle: parent epic #76 admits a deterministic
simulator as ground truth, so :class:`RelayReflexSimulator` is authoritative.
It steps a fixed tick grid over the live channels -- a heating-only
running-max temperature, per-channel freshness and health, jitter, the
fixed-phase corruption, malformed events, saturation runs, the first degraded
tick -- and hands one frozen observation to the tier tables. Nothing here
samples randomness; :func:`corruption_phase` is the only pseudo-random element.

D7 row 9 (owner ruling): every drop starts detection at the first dropped
tick. ``DEGRADATION_SIGNS`` carries an ``events_dropped`` sign #138 lacked, so
a ``malformed_spike_burst`` of ``unknown_channel`` events -- the shape of #138's
fixture record ``fr-20260823-0015`` (count 1 on c0-c2, ``degrade_gracefully``
/ ``EVENTS_DROPPED``) -- now detects at 0.0 ms and recovers at ``tick_ms``,
where #138 reported no detection reading and a recovery of 0.0.
``sensor_loss`` drops already detected through channel health.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from . import distill_builders as builders
from . import distill_vocabulary as vocab
from . import fault_boundary as boundary
from . import fault_config as config
from . import fault_parameters as parameters
from . import fault_tiers as tiers
from . import fault_vocabulary as fv
from .import_twins import bind_import_twin


def corruption_phase(tick: int) -> float:
    """The fixed integer phase in ``[0, 1)`` a corrupt tick is decided against."""
    return ((tick * 7919) % 1000) / 1000.0


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

    @classmethod
    def from_disturbance(
        cls, disturbance: parameters.Disturbance, system: dict[str, Any]
    ) -> _DisturbanceSpec:
        """Coerce a checked disturbance; the ``> 0`` floor already ran on ``ramp_ms``."""
        params = disturbance.parameters
        return cls(
            kind=disturbance.kind,
            affected=disturbance.affected,
            onset_ms=float(params.get("onset_ms", 0.0)),
            duration_ms=float(params.get("duration_ms", 0.0)),
            jitter_ms=float(params.get("jitter_ms", 0.0)),
            corrupt_ratio=float(params.get("corrupt_ratio", 0.0)),
            malformed_count=int(params.get("malformed_count", 0)),
            malformed_kind=str(params.get("malformed_kind", "")),
            peak_c=float(params.get("peak_c", system["ambient_c"])),
            ramp_ms=float(params.get("ramp_ms", 1.0)),
            result_delay_ms=float(params.get("delay_ms", 0.0)),
        )

    def in_window(self, now_ms: float) -> bool:
        """Half-open: ``onset_ms <= now_ms < onset_ms + duration_ms``."""
        return self.onset_ms <= now_ms < self.onset_ms + self.duration_ms

    def hits(self, channel: str, active: bool) -> bool:
        return active and channel in self.affected


@dataclass(frozen=True)
class _Tick:
    index: int
    now_ms: float
    active: bool


# (name, predicate over the state and this tick's healthy count): the signs
# that start detection. ``events_dropped`` is the row-9 sign; the jitter sign
# is strict so a jitter at tolerance stays within tolerance (row 11).
DEGRADATION_SIGNS: tuple[tuple[str, Callable[[Any, int], bool]], ...] = (
    ("reduced_health", lambda state, healthy_now: healthy_now < state.channel_count),
    ("integrity_violation", lambda state, healthy_now: state.integrity_violation),
    ("corruption", lambda state, healthy_now: state.corrupt > 0),
    ("events_dropped", lambda state, healthy_now: state.dropped > 0),
    ("jitter_beyond_tolerance", lambda state, _: state.max_jitter > state.system["jitter_tolerance_ms"]),
    ("thermal_warn", lambda state, _: state.peak_temperature >= state.system["thermal_warn_c"]),
)


class _StreamState:
    """Counters the tick loop accumulates while stepping the event stream."""

    def __init__(self, system: dict[str, Any], spec: _DisturbanceSpec, live_channels: list[str]) -> None:
        self.system = system
        self.spec = spec
        self.tick_ms = float(system["tick_ms"])
        self.channel_count = len(system["channels"])
        self.live_channels = tuple(live_channels)
        # The relay assumes a fresh event on every channel at t = 0.
        self.last_fresh_ms = {channel: 0.0 for channel in system["channels"]}
        self.saturated_since: dict[str, int] = {}
        self.saturated_ticks = 0
        self.dropped = 0
        self.corrupt = 0
        self.total = 0
        self.max_staleness = 0.0
        self.max_jitter = 0.0
        self.integrity_violation = False
        self.peak_temperature = float(system["ambient_c"])
        self.worst_healthy = len(self.live_channels)
        self.detection_ms: float | None = None
        self.malformed_emitted = 0
        self.trace: list[dict[str, Any]] = []

    def step(self, index: int) -> None:
        """Advance one tick: thermal state, every live channel, detection, trace."""
        now_ms = index * self.tick_ms
        tick = _Tick(index, now_ms, self.spec.in_window(now_ms))
        self._update_thermal(tick)
        healthy_now = sum(self._channel_step(channel, tick) for channel in self.live_channels)
        self.worst_healthy = min(self.worst_healthy, healthy_now)
        if self.detection_ms is None and self._degraded_now(healthy_now):
            self.detection_ms = now_ms
        self.trace.append(
            {"t_ms": now_ms, "healthy": healthy_now, "temperature_c": round(self.peak_temperature, 3)}
        )

    def _update_thermal(self, tick: _Tick) -> None:
        """Heating-only: ramp from ambient toward the peak, kept as a running max."""
        spec = self.spec
        if spec.kind != fv.THERMAL_EXCURSION or tick.now_ms < spec.onset_ms:
            return
        ramped = min(1.0, (tick.now_ms - spec.onset_ms) / spec.ramp_ms)
        ambient = float(self.system["ambient_c"])
        self.peak_temperature = max(self.peak_temperature, ambient + ramped * (spec.peak_c - ambient))

    def _fault_hits(self, kind: str, channel: str, tick: _Tick) -> bool:
        return self.spec.kind == kind and self.spec.hits(channel, tick.active)

    def _channel_step(self, channel: str, tick: _Tick) -> bool:
        """Apply the disturbance to one channel; True when it stays healthy."""
        self.total += 1
        lost = self._fault_hits(fv.SENSOR_LOSS, channel, tick)
        stale = self._fault_hits(fv.STALE_SENSOR, channel, tick)
        self.dropped += int(lost)
        if not lost and not stale:
            self.last_fresh_ms[channel] = tick.now_ms
        _SIGNAL_FAULTS.get(self.spec.kind, _StreamState._no_signal_fault)(self, channel, tick)
        saturating = self._apply_saturation(channel, tick)
        staleness = tick.now_ms - self.last_fresh_ms[channel]
        self.max_staleness = max(self.max_staleness, staleness)
        return not any((lost, saturating, staleness > self.system["stale_threshold_ms"]))

    def _no_signal_fault(self, channel: str, tick: _Tick) -> None:
        return None

    def _note_jitter(self, channel: str, tick: _Tick) -> None:
        if self.spec.hits(channel, tick.active):
            self.max_jitter = max(self.max_jitter, abs(self.spec.jitter_ms))

    def _maybe_corrupt(self, channel: str, tick: _Tick) -> None:
        corrupt = corruption_phase(tick.index) < self.spec.corrupt_ratio
        if self.spec.hits(channel, tick.active) and corrupt:
            self.corrupt += 1

    def _apply_malformed_event(self, channel: str, tick: _Tick) -> None:
        """One malformed event per affected channel per tick from tick 0, capped.

        Integrity kinds corrupt the accepted stream; ``unknown_channel`` is
        rejected at the relay boundary and counts as a drop.
        """
        capped = self.malformed_emitted >= self.spec.malformed_count
        if channel not in self.spec.affected or capped:
            return
        self.malformed_emitted += 1
        integrity = self.spec.malformed_kind in fv.MALFORMED_INTEGRITY_KINDS
        self.integrity_violation = self.integrity_violation or integrity
        self.dropped += int(not integrity)

    def _apply_saturation(self, channel: str, tick: _Tick) -> bool:
        """The longest contiguous saturated run per channel, max over channels."""
        if not self._fault_hits(fv.TEMPORARY_SATURATION, channel, tick):
            self.saturated_since.pop(channel, None)
            return False
        since = self.saturated_since.setdefault(channel, tick.index)
        self.saturated_ticks = max(self.saturated_ticks, tick.index - since + 1)
        return True

    def _degraded_now(self, healthy_now: int) -> bool:
        return any(holds(self, healthy_now) for _, holds in DEGRADATION_SIGNS)

    def observe(self, fallback_ok: bool) -> tiers.Observation:
        return tiers.Observation(
            worst_healthy=self.worst_healthy,
            channel_count=self.channel_count,
            integrity_violation=self.integrity_violation,
            corrupt=self.corrupt,
            total=self.total,
            dropped=self.dropped,
            peak_temperature=self.peak_temperature,
            saturated_ticks=self.saturated_ticks,
            max_staleness=self.max_staleness,
            max_jitter=self.max_jitter,
            result_delay_ms=self.spec.result_delay_ms,
            fallback_ok=fallback_ok,
            detection_ms=self.detection_ms,
        )


# kind -> the per-channel signal fault it applies; other kinds apply none.
_SIGNAL_FAULTS: dict[str, Callable[[_StreamState, str, _Tick], None]] = {
    fv.EVENT_JITTER: _StreamState._note_jitter,
    fv.BURST_CORRUPTION: _StreamState._maybe_corrupt,
    fv.MALFORMED_SPIKE_BURST: _StreamState._apply_malformed_event,
}


def _result(state: _StreamState, spec: _DisturbanceSpec, decision: tiers.Decision) -> boundary.FaultResult:
    """Freeze the accumulated stream state into one FaultResult."""
    return boundary.FaultResult(
        outcome=decision.outcome,
        reason_codes=decision.reasons,
        detection_latency_ms=decision.detection_latency_ms,
        recovery_latency_ms=decision.recovery_latency_ms,
        worst_healthy_channels=state.worst_healthy,
        dropped_events=state.dropped,
        corrupt_events=state.corrupt,
        total_events=state.total,
        peak_temperature_c=round(state.peak_temperature, 3),
        max_staleness_ms=round(state.max_staleness, 3),
        max_jitter_ms=round(state.max_jitter, 3),
        saturated_ticks=state.saturated_ticks,
        integrity_violation=state.integrity_violation,
        result_delay_ms=spec.result_delay_ms,
        trace=tuple(state.trace),
    )


class RelayReflexSimulator(boundary.FaultOracle):
    """Deterministic multi-channel relay with reflex, fallback and quarantine."""

    name = fv.ORACLE_NAME
    version = fv.ORACLE_VERSION
    oracle_type = fv.ORACLE_TYPE
    authority = vocab.AUTHORITY_AUTHORITATIVE
    implementation = fv.ORACLE_IMPLEMENTATION
    meter_clock = fv.METER_CLOCK
    meter_state = fv.METER_STATE
    meter_thermal = fv.METER_THERMAL

    def oracle_block(self, scenario: dict[str, Any]) -> dict[str, Any]:
        """The oracle block, recording the effective system this engine runs."""
        identity = builders.OracleIdentity(
            self.name,
            oracle_type=self.oracle_type,
            implementation=self.implementation,
            version=self.version,
            authority=self.authority,
        )
        configuration = {
            "system": config.checked_system(scenario),
            "precedence": list(fv.OUTCOME_PRECEDENCE),
        }
        return builders.new_oracle(identity, builders.OracleRun(configuration=configuration))

    def run(self, scenario: dict[str, Any], disturbance: dict[str, Any]) -> boundary.FaultResult:
        """Check, step every tick, decide; refuses invalid input before any state exists."""
        system = config.checked_system(scenario)
        checked = parameters.checked_disturbance(disturbance, system)
        spec = _DisturbanceSpec.from_disturbance(checked, system)
        missing = set(checked.affected) if checked.kind == fv.MISSING_CHANNEL else set()
        live = [channel for channel in system["channels"] if channel not in missing]
        state = _StreamState(system, spec, live)
        for tick in range(system["ticks"]):
            state.step(tick)
        fallback_ok = tiers.fallback_available(system, missing, checked.declared)
        decision = tiers.decide(state.observe(fallback_ok), system, spec.onset_ms)
        return _result(state, spec, decision)


bind_import_twin(__name__)
