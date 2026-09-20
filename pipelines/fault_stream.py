#!/usr/bin/env python3
"""Per-tick event stream for ``neuromorphic-fault-recovery``.

Split out of ``fault_simulator.py`` verbatim: ``_Tick`` context,
:class:`_StreamState` — the counter/trace accumulator the disturbance steps
through — ``_StreamVerdict``, and ``_result_from_state``, the freeze into the
:class:`fault_types.FaultResult` record shape.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

if __package__:
    from .fault_types import (
        FaultResult,
        MALFORMED_INTEGRITY_KINDS,
        _DisturbanceSpec,
    )
else:
    from fault_types import (
        FaultResult,
        MALFORMED_INTEGRITY_KINDS,
        _DisturbanceSpec,
    )


@dataclass(frozen=True)
class _Tick:
    """Where one stream step lands: index, wall time, and window membership."""

    tick: int
    now_ms: float
    in_window: bool


class _StreamState:
    """Counters the tick loop accumulates while stepping the event stream."""

    def __init__(
        self,
        system: dict[str, Any],
        channels: list[str],
        live_channels: list[str],
    ) -> None:
        self.system = system
        self.channel_count = len(channels)
        self.live_channels = live_channels
        self.last_fresh_ms = {channel: 0.0 for channel in channels}
        self.saturated_since: dict[str, int] = {}
        self.saturated_ticks = 0
        self.dropped = 0
        self.corrupt = 0
        self.corruption_ticks: frozenset[int] = frozenset()
        self.total = 0
        self.max_staleness = 0.0
        self.max_jitter = 0.0
        self.integrity_violation = False
        self.peak_temperature = float(system["ambient_c"])
        self.worst_healthy = len(live_channels)
        self.detection_ms: float | None = None
        self.malformed_emitted = 0
        self.trace: list[dict[str, Any]] = []

    def step(self, spec: _DisturbanceSpec, tick: int, tick_ms: float) -> None:
        """Advance one tick: thermal state, every live channel, detection."""

        now_ms = tick * tick_ms
        tick_ctx = _Tick(tick=tick, now_ms=now_ms, in_window=spec.in_window(now_ms))
        self._update_thermal(spec, now_ms)
        healthy_now = 0
        for channel in self.live_channels:
            healthy = self._channel_step(spec, channel, tick_ctx)
            healthy_now += 1 if healthy else 0
        self.worst_healthy = min(self.worst_healthy, healthy_now)
        if self._degraded_now(healthy_now) and self.detection_ms is None:
            self.detection_ms = now_ms
        self.trace.append(
            {
                "t_ms": now_ms,
                "healthy": healthy_now,
                "temperature_c": round(self.peak_temperature, 3),
            }
        )

    def _update_thermal(self, spec: _DisturbanceSpec, now_ms: float) -> None:
        if spec.kind == "thermal_excursion" and now_ms >= spec.onset_ms:
            ramped = min(1.0, (now_ms - spec.onset_ms) / spec.ramp_ms)
            temperature = self.system["ambient_c"] + ramped * (
                spec.peak_c - float(self.system["ambient_c"])
            )
            self.peak_temperature = max(self.peak_temperature, temperature)

    def _channel_step(
        self, spec: _DisturbanceSpec, channel: str, tick: _Tick
    ) -> bool:
        """Apply the disturbance to one channel; True when it stays healthy."""

        self.total += 1
        lost = (
            spec.kind == "sensor_loss"
            and tick.in_window
            and channel in spec.affected
        )
        stale = (
            spec.kind == "stale_sensor"
            and channel in spec.affected
            and tick.in_window
        )
        if lost:
            self.dropped += 1
        elif not stale:
            self.last_fresh_ms[channel] = tick.now_ms

        self._apply_signal_faults(spec, channel, tick)
        saturating = self._apply_saturation(spec, channel, tick)

        staleness = tick.now_ms - self.last_fresh_ms[channel]
        self.max_staleness = max(self.max_staleness, staleness)
        return (
            not lost
            and staleness <= float(self.system["stale_threshold_ms"])
            and not saturating
        )

    def _apply_signal_faults(
        self, spec: _DisturbanceSpec, channel: str, tick: _Tick
    ) -> None:
        in_window = tick.in_window
        if spec.kind == "event_jitter" and channel in spec.affected and in_window:
            self.max_jitter = max(self.max_jitter, abs(spec.jitter_ms))

        if spec.kind == "burst_corruption" and channel in spec.affected and in_window:
            # Selected actual ticks preserve the phase when it realises a hit.
            if tick.tick in self.corruption_ticks:
                self.corrupt += 1

        if spec.kind == "malformed_spike_burst" and channel in spec.affected:
            self._apply_malformed_event(spec)

    def _apply_malformed_event(self, spec: _DisturbanceSpec) -> None:
        if self.malformed_emitted >= spec.malformed_count:
            return
        self.malformed_emitted += 1
        if spec.malformed_kind in MALFORMED_INTEGRITY_KINDS:
            self.integrity_violation = True
        else:
            # Rejected at the relay boundary rather than trusted and
            # later found corrupt.
            self.dropped += 1

    def _apply_saturation(
        self, spec: _DisturbanceSpec, channel: str, tick: _Tick
    ) -> bool:
        saturating = (
            spec.kind == "temporary_saturation"
            and channel in spec.affected
            and tick.in_window
        )
        if saturating:
            self.saturated_since.setdefault(channel, tick.tick)
            self.saturated_ticks = max(
                self.saturated_ticks, tick.tick - self.saturated_since[channel] + 1
            )
        else:
            self.saturated_since.pop(channel, None)
        return saturating

    def _degraded_now(self, healthy_now: int) -> bool:
        violations = (
            self.integrity_violation,
            self.corrupt > 0,
            self.max_jitter > float(self.system["jitter_tolerance_ms"]),
            self.peak_temperature >= float(self.system["thermal_warn_c"]),
        )
        return healthy_now < self.channel_count or any(violations)


@dataclass(frozen=True)
class _StreamVerdict:
    """The outcome and latencies the run is labelled with."""

    outcome: str
    reasons: list[str]
    detection_ms: float | None
    recovery_ms: float


def _result_from_state(
    state: _StreamState, spec: _DisturbanceSpec, verdict: _StreamVerdict
) -> FaultResult:
    """Freeze the accumulated stream state into one FaultResult."""

    return FaultResult(
        outcome=verdict.outcome,
        reason_codes=tuple(verdict.reasons),
        detection_latency_ms=verdict.detection_ms,
        recovery_latency_ms=verdict.recovery_ms,
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


