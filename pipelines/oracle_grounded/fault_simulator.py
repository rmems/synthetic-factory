#!/usr/bin/env python3
"""The oracle boundary, the deterministic tick-grid relay and its decision (F1).

:class:`FaultOracle` is the interface a hardware-replay adapter subclasses,
:class:`FaultResult` the frozen verdict and :func:`checked_result` the
vocabulary gate on any verdict an injected oracle returns. The simulator is
the oracle (parent epic #76 admits a deterministic simulator as ground
truth): :class:`RelayReflexSimulator` steps a fixed tick grid over the live
channels and hands one frozen :class:`Observation` to the tier tables, which
in ``OUTCOME_PRECEDENCE`` order hold one ``(reason code, predicate)`` row per
reason; the first tier with a fired reason decides and reports every fired
reason, nothing fired is ``continue`` / ``WITHIN_TOLERANCE`` (D7 row 11), and
the corruption tier needs actual corruption beside the ratio threshold (row
6). Nothing samples randomness; :func:`corruption_phase` is the only
pseudo-random element.

D7 row 9 (owner ruling): every drop starts detection at the first dropped
tick. ``DEGRADATION_SIGNS`` carries the ``events_dropped`` sign #138 lacked,
so a ``malformed_spike_burst`` of ``unknown_channel`` events -- the shape of
#138's fixture record ``fr-20260823-0015`` -- now detects at 0.0 ms and
recovers at ``tick_ms`` where #138 reported no detection and recovery 0.0.
Sanctioned re-split point: past about forty functions the tier tables
(``Observation`` through ``decide``) come back out as ``fault_tiers``.
"""

from __future__ import annotations

from collections.abc import Callable, Container
from dataclasses import dataclass, field
from typing import Any

from . import distill_builders as builders
from . import distill_vocabulary as vocab
from . import envelope
from . import fault_config as config
from . import fault_vocabulary as fv
from .import_twins import bind_import_twin


@dataclass(frozen=True)
class FaultResult:
    """One executed disturbance: the outcome plus the state it was read from.

    Both latencies are relative to the disturbance onset, so identical faults
    at different onsets carry identical labels; ``detection_latency_ms`` is
    ``None`` only for a ``continue`` outcome.
    """

    outcome: str
    reason_codes: tuple[str, ...]
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
        """The corrupted share the tick grid actually applied (0.0 for no events)."""
        if self.total_events <= 0:
            return 0.0
        return self.corrupt_events / self.total_events

    @property
    def residual_error(self) -> float:
        """Corrupt plus dropped events over the total (0.0 for no events)."""
        if self.total_events <= 0:
            return 0.0
        return (self.corrupt_events + self.dropped_events) / self.total_events

    @property
    def ticks(self) -> int:
        return len(self.trace)


class FaultOracle:
    """Boundary a fault-recovery oracle must implement.

    The meters name the instruments behind the readings ``fault_oracle``
    derives; they default to unset so a hardware replay cannot inherit the
    simulator's provenance (``fault_oracle`` refuses undeclared meters). The
    abstract ``run`` and ``oracle_block`` raise ``NotImplementedError``: a
    subclass that declares meters but no engine is a programming error, not
    a data refusal.
    """

    name = "abstract"
    version = "0"
    oracle_type = fv.ORACLE_TYPE
    authority = vocab.AUTHORITY_AUTHORITATIVE
    implementation = fv.BOUNDARY_IMPLEMENTATION
    meter_clock: str | None = None
    meter_state: str | None = None
    meter_thermal: str | None = None

    def run(self, scenario: dict[str, Any], disturbance: dict[str, Any]) -> FaultResult:
        raise NotImplementedError

    def oracle_block(self, scenario: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


def _declared_reasons(codes: Any) -> bool:
    """A non-empty tuple whose every member is a declared reason code (strings only)."""
    if not isinstance(codes, tuple) or not codes:
        return False
    return all(isinstance(code, str) and code in fv.REASON_CODE_SET for code in codes)


def _non_negative_number(value: Any) -> bool:
    return envelope.is_number(value) and value >= 0


def _optional_number(value: Any) -> bool:
    """A detection latency: absent, or a finite non-negative number of ms."""
    return value is None or _non_negative_number(value)


def _count(value: Any) -> bool:
    return vocab.is_genuine_int(value) and value >= 0


_COUNT_FIELDS = (
    "worst_healthy_channels", "dropped_events", "corrupt_events", "total_events", "saturated_ticks",
)
# Durations are non-negative milliseconds; a temperature may sit below zero.
_DURATION_FIELDS = ("recovery_latency_ms", "max_staleness_ms", "max_jitter_ms", "result_delay_ms")
_NUMBER_FIELDS = ("peak_temperature_c",)
# (field, predicate, expected text): the family vocabulary every verdict must
# fit before it becomes a label, whichever oracle returned it.
_RESULT_RULES: tuple[tuple[str, config.Predicate, str], ...] = (
    ("outcome", lambda value: value in fv.OUTCOMES, "one of the family's outcomes"),
    ("reason_codes", _declared_reasons, "a non-empty tuple of declared reason codes"),
    ("detection_latency_ms", _optional_number, "a finite non-negative number of ms or None"),
    ("integrity_violation", lambda value: isinstance(value, bool), "a boolean"),
    *((name, _count, "a non-negative integer") for name in _COUNT_FIELDS),
    *((name, _non_negative_number, "a finite non-negative number of ms") for name in _DURATION_FIELDS),
    *((name, envelope.is_number, "a finite number") for name in _NUMBER_FIELDS),
)


def _result_problems(result: FaultResult):
    for name, holds, expected in _RESULT_RULES:
        value = getattr(result, name)
        # A foreign reason tuple is not echoed: the finding carries one code only.
        shown = "" if name == "reason_codes" else f", got {value!r}"
        yield (
            not holds(value),
            fv.FINDING_ORACLE_RESULT_OUT_OF_VOCABULARY,
            f"oracle result {name} must be {expected}{shown}",
        )


def checked_result(result: Any) -> FaultResult:
    """A verdict inside the family vocabulary: the type, the outcome, declared
    reason codes, genuine counts and finite readings, then the cross-field
    consistency the simulator itself keeps (reasons from the outcome's tier,
    detection exactly for non-continue outcomes, counts within the total);
    anything else is refused before it can become a label."""
    fv.refuse_when(
        not isinstance(result, FaultResult),
        fv.FINDING_ORACLE_RESULT_OUT_OF_VOCABULARY,
        f"an oracle must return a FaultResult, got {result!r}",
    )
    fv.refuse_first(_result_problems(result))
    fv.refuse_first(_verdict_problems(result))
    return result


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
# outcome -> the reason codes its tier can emit; a verdict from any oracle
# must draw its reasons from the tier of the outcome it reports.
_TIER_REASONS = {outcome: frozenset(code for code, _ in rules) for outcome, rules in TIERS}
_TIER_REASONS[fv.OUTCOME_CONTINUE] = frozenset(CONTINUE_REASONS)


def _reasons_fit_outcome(result: FaultResult) -> bool:
    return set(result.reason_codes) <= _TIER_REASONS[result.outcome]


def _detection_fits_outcome(result: FaultResult) -> bool:
    return (result.detection_latency_ms is None) == (result.outcome == fv.OUTCOME_CONTINUE)


def _counts_fit_total(result: FaultResult) -> bool:
    return result.corrupt_events + result.dropped_events <= result.total_events


def _recovery_follows_detection(result: FaultResult) -> bool:
    """Recovery is onset-relative like detection: zero for continue, else never before it."""
    if result.outcome == fv.OUTCOME_CONTINUE:
        return result.recovery_latency_ms == 0.0
    return result.recovery_latency_ms >= result.detection_latency_ms


# (predicate over a field-valid result, what it guarantees): the consistency
# the simulator keeps by construction, required of every oracle's verdict.
_VERDICT_RULES = (
    (_reasons_fit_outcome, "reason codes must all belong to the tier of the reported outcome "
                           "(continue carries exactly the within-tolerance reason)"),
    (_detection_fits_outcome, "detection_latency_ms must be None exactly when the outcome is continue"),
    (_counts_fit_total, "corrupt_events plus dropped_events must not exceed total_events"),
    (_recovery_follows_detection, "recovery_latency_ms must be 0.0 for continue and never precede "
                                  "detection_latency_ms otherwise"),
)


def _verdict_problems(result: FaultResult):
    for holds, guarantee in _VERDICT_RULES:
        # The reasons are not echoed: a finding carries one finding code and no reason code.
        yield (
            not holds(result),
            fv.FINDING_ORACLE_RESULT_OUT_OF_VOCABULARY,
            f"oracle result {result.outcome!r}: {guarantee}",
        )
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
    def from_disturbance(cls, disturbance: config.Disturbance, system: dict[str, Any]) -> _DisturbanceSpec:
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

    def observe(self, fallback_ok: bool) -> Observation:
        return Observation(
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


def _result(state: _StreamState, spec: _DisturbanceSpec, decision: Decision) -> FaultResult:
    """Freeze the accumulated stream state into one FaultResult."""
    return FaultResult(
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


class RelayReflexSimulator(FaultOracle):
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

    def run(self, scenario: dict[str, Any], disturbance: dict[str, Any]) -> FaultResult:
        """Check, step every tick, decide; refuses invalid input before any state exists."""
        system = config.checked_system(scenario)
        checked = config.checked_disturbance(disturbance, system)
        spec = _DisturbanceSpec.from_disturbance(checked, system)
        missing = set(checked.affected) if checked.kind == fv.MISSING_CHANNEL else set()
        live = [channel for channel in system["channels"] if channel not in missing]
        state = _StreamState(system, spec, live)
        for tick in range(system["ticks"]):
            state.step(tick)
        fallback_ok = fallback_available(system, missing, checked.declared)
        decision = decide(state.observe(fallback_ok), system, spec.onset_ms)
        return _result(state, spec, decision)


bind_import_twin(__name__)
