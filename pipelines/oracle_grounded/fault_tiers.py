#!/usr/bin/env python3
"""The outcome decision of the fault-recovery family as data (F1).

The tick loop yields one frozen :class:`Observation`; the tier tables, in
``OUTCOME_PRECEDENCE`` order, hold one ``(reason code, predicate)`` row per
reason; the first tier with a fired reason decides and reports every fired
reason in table order; nothing fired is ``continue`` / ``WITHIN_TOLERANCE``
(D7 row 11). Row 6 lives in the quarantine row: the corruption tier needs
actual corruption beside the ratio threshold, so a zero threshold on a clean
stream is a policy, not a verdict.
"""

from __future__ import annotations

from collections.abc import Callable, Container
from dataclasses import dataclass
from typing import Any

from . import fault_vocabulary as fv
from .import_twins import bind_import_twin


@dataclass(frozen=True)
class Observation:
    """What the tick loop saw over the whole run."""

    worst_healthy: int
    channel_count: int
    integrity_violation: bool
    corrupt: int
    total: int
    dropped: int
    peak_temperature: float
    saturated_ticks: int
    max_staleness: float
    max_jitter: float
    result_delay_ms: float
    fallback_ok: bool
    # Absolute run time of the first degraded tick, or None.
    detection_ms: float | None

    @property
    def corrupt_ratio(self) -> float:
        """The unrounded corrupted share the decision uses (0.0 for no events)."""
        if self.total <= 0:
            return 0.0
        return self.corrupt / self.total


@dataclass(frozen=True)
class Decision:
    outcome: str
    reasons: tuple[str, ...]
    detection_latency_ms: float | None
    recovery_latency_ms: float


def fallback_available(system: dict[str, Any], missing: Container[str], declared: Any) -> bool:
    """A named fallback source that is neither missing nor touched by the disturbance."""
    source = system.get("fallback_source")
    return bool(source) and source not in (set(missing) | set(declared))


def _budget_short(observation: Observation, system: dict[str, Any]) -> bool:
    return observation.worst_healthy < system["min_healthy_channels"]


Rule = tuple[str, Callable[[Observation, dict[str, Any]], bool]]

_FAIL_CLOSED: tuple[Rule, ...] = (
    (fv.REASON_NO_TIMELY_INPUT, lambda o, s: o.result_delay_ms >= s["hard_deadline_ms"]),
    (fv.REASON_THERMAL_SHUTDOWN, lambda o, s: o.peak_temperature >= s["thermal_shutdown_c"]),
    (
        fv.REASON_INSUFFICIENT_HEALTHY_CHANNELS_NO_FALLBACK,
        lambda o, s: _budget_short(o, s) and not o.fallback_ok,
    ),
)
_QUARANTINE: tuple[Rule, ...] = (
    (fv.REASON_MALFORMED_STREAM_QUARANTINED, lambda o, s: o.integrity_violation),
    (
        fv.REASON_CORRUPTION_ABOVE_QUARANTINE_THRESHOLD,
        lambda o, s: o.corrupt > 0 and o.corrupt_ratio >= s["corruption_quarantine_ratio"],
    ),
)
_REFLEX: tuple[Rule, ...] = (
    (fv.REASON_THERMAL_LIMIT_REFLEX, lambda o, s: o.peak_temperature >= s["thermal_limit_c"]),
    (fv.REASON_SATURATION_REFLEX, lambda o, s: o.saturated_ticks >= s["reflex_saturation_ticks"]),
)
_FALLBACK: tuple[Rule, ...] = (
    (fv.REASON_FALLBACK_SOURCE_ENGAGED, lambda o, s: _budget_short(o, s) and o.fallback_ok),
)
_DEGRADE: tuple[Rule, ...] = (
    (fv.REASON_STALE_BEYOND_THRESHOLD, lambda o, s: o.max_staleness > s["stale_threshold_ms"]),
    (fv.REASON_JITTER_BEYOND_TOLERANCE, lambda o, s: o.max_jitter > s["jitter_tolerance_ms"]),
    (fv.REASON_EVENTS_DROPPED, lambda o, s: o.dropped > 0),
    (fv.REASON_CORRUPTION_BELOW_QUARANTINE_THRESHOLD, lambda o, s: o.corrupt_ratio > 0.0),
    (fv.REASON_THERMAL_WARN, lambda o, s: o.peak_temperature >= s["thermal_warn_c"]),
    (fv.REASON_RESULT_PAST_DEADLINE, lambda o, s: o.result_delay_ms > s["deadline_ms"]),
    (fv.REASON_REDUCED_CHANNEL_SET, lambda o, s: o.worst_healthy < o.channel_count),
)
TIERS: tuple[tuple[str, tuple[Rule, ...]], ...] = (
    (fv.OUTCOME_FAIL_CLOSED, _FAIL_CLOSED),
    (fv.OUTCOME_QUARANTINE, _QUARANTINE),
    (fv.OUTCOME_REFLEX, _REFLEX),
    (fv.OUTCOME_FALLBACK, _FALLBACK),
    (fv.OUTCOME_DEGRADE, _DEGRADE),
)
CONTINUE_REASONS = (fv.REASON_WITHIN_TOLERANCE,)
# outcome -> the system control added to the detection time for recovery.
RECOVERY_EXTRA = {
    fv.OUTCOME_REFLEX: "reflex_latency_ms",
    fv.OUTCOME_QUARANTINE: "reflex_latency_ms",
    fv.OUTCOME_FAIL_CLOSED: "reflex_latency_ms",
    fv.OUTCOME_FALLBACK: "fallback_latency_ms",
    fv.OUTCOME_DEGRADE: "tick_ms",
}


def _fired(rules: tuple[Rule, ...], observation: Observation, system: dict[str, Any]):
    return tuple(code for code, holds in rules if holds(observation, system))


def select_outcome(observation: Observation, system: dict[str, Any]) -> tuple[str, tuple[str, ...]]:
    """The first tier with a fired reason, with every reason it fired, else continue."""
    for outcome, rules in TIERS:
        reasons = _fired(rules, observation, system)
        if reasons:
            return outcome, reasons
    return fv.OUTCOME_CONTINUE, CONTINUE_REASONS


def detection_latency_ms(observation: Observation, onset_ms: float, system: dict[str, Any]) -> float | None:
    """Onset-relative detection, 3 dp; a late result detects at the soft deadline."""
    detected = observation.detection_ms
    if detected is None and observation.result_delay_ms > system["deadline_ms"]:
        detected = float(system["deadline_ms"])
    if detected is None:
        return None
    return round(max(detected - onset_ms, 0.0), 3)


def recovery_latency_ms(system: dict[str, Any], outcome: str, detection_ms: float | None) -> float:
    """0.0 for continue (or nothing detected), else detection plus the tier's latency."""
    if detection_ms is None or outcome == fv.OUTCOME_CONTINUE:
        return 0.0
    return round(detection_ms + system[RECOVERY_EXTRA[outcome]], 3)


def decide(observation: Observation, system: dict[str, Any], onset_ms: float) -> Decision:
    """Outcome, reasons and both onset-relative latencies for one observation."""
    outcome, reasons = select_outcome(observation, system)
    detection = detection_latency_ms(observation, onset_ms, system)
    return Decision(outcome, reasons, detection, recovery_latency_ms(system, outcome, detection))


bind_import_twin(__name__)
