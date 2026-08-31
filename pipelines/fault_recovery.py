#!/usr/bin/env python3
"""``neuromorphic-fault-recovery`` generator + deterministic relay oracle.

Issue #78. A generator proposes a disturbance against a bounded relay/reflex
system and may attach a *prediction*. The label comes from actually stepping
the disturbance through a deterministic simulator, never from the prediction.

The simulator is the oracle. Parent epic #76 explicitly admits a deterministic
simulator as ground truth, so records from ``RelayReflexSimulator`` carry
``oracle.authority = "authoritative"``. Hardware replay would slot in behind
the same :class:`FaultOracle` boundary; it is not available here.

Disturbance vocabulary and outcome vocabulary are the ones written in #78.

CLI::

    python3 pipelines/fault_recovery.py generate --count 12 --seed 20260823 \
        --output <new.jsonl>
    python3 pipelines/fault_recovery.py describe --json
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

import oracle_contract as oc  # noqa: E402

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


DEFAULT_SYSTEM = {
    "channels": ["c0", "c1", "c2", "c3"],
    "tick_ms": 2.0,
    "ticks": 24,
    "min_healthy_channels": 3,
    "stale_threshold_ms": 8.0,
    "jitter_tolerance_ms": 1.5,
    "ambient_c": 38.0,
    "thermal_warn_c": 62.0,
    "thermal_limit_c": 78.0,
    "thermal_shutdown_c": 92.0,
    "reflex_saturation_ticks": 4,
    "corruption_quarantine_ratio": 0.25,
    "deadline_ms": 12.0,
    "hard_deadline_ms": 40.0,
    "reflex_latency_ms": 1.0,
    "fallback_latency_ms": 4.0,
    "fallback_source": "redundant_relay_b",
}


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
    def from_parameters(
        cls,
        kind: str,
        params: dict[str, Any],
        system: dict[str, Any],
        affected: list[str],
    ) -> "_DisturbanceSpec":
        return cls(
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

    def in_window(self, now_ms: float) -> bool:
        return self.onset_ms <= now_ms < (self.onset_ms + self.duration_ms)


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
        in_window = spec.in_window(now_ms)
        self._update_thermal(spec, now_ms)
        healthy_now = 0
        for channel in self.live_channels:
            healthy = self._channel_step(spec, channel, tick, now_ms, in_window)
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
        self,
        spec: _DisturbanceSpec,
        channel: str,
        tick: int,
        now_ms: float,
        in_window: bool,
    ) -> bool:
        """Apply the disturbance to one channel; True when it stays healthy."""

        self.total += 1
        lost = spec.kind == "sensor_loss" and in_window and channel in spec.affected
        stale = spec.kind == "stale_sensor" and channel in spec.affected and in_window
        if lost:
            self.dropped += 1
        elif not stale:
            self.last_fresh_ms[channel] = now_ms

        self._apply_signal_faults(spec, channel, tick, in_window)
        saturating = self._apply_saturation(spec, channel, tick, in_window)

        staleness = now_ms - self.last_fresh_ms[channel]
        self.max_staleness = max(self.max_staleness, staleness)
        return (
            not lost
            and staleness <= float(self.system["stale_threshold_ms"])
            and not saturating
        )

    def _apply_signal_faults(
        self, spec: _DisturbanceSpec, channel: str, tick: int, in_window: bool
    ) -> None:
        if spec.kind == "event_jitter" and channel in spec.affected and in_window:
            self.max_jitter = max(self.max_jitter, abs(spec.jitter_ms))

        if spec.kind == "burst_corruption" and channel in spec.affected and in_window:
            # Deterministic pseudo-random phase, fine enough that the
            # realised corruption tracks the requested ratio instead of
            # snapping to quarters.
            if ((tick * 7919) % 1000) / 1000.0 < spec.corrupt_ratio:
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
        self, spec: _DisturbanceSpec, channel: str, tick: int, in_window: bool
    ) -> bool:
        saturating = (
            spec.kind == "temporary_saturation"
            and channel in spec.affected
            and in_window
        )
        if saturating:
            self.saturated_since.setdefault(channel, tick)
            self.saturated_ticks = max(
                self.saturated_ticks, tick - self.saturated_since[channel] + 1
            )
        else:
            self.saturated_since.pop(channel, None)
        return saturating

    def _degraded_now(self, healthy_now: int) -> bool:
        return (
            healthy_now < self.channel_count
            or self.integrity_violation
            or self.corrupt > 0
            or self.max_jitter > float(self.system["jitter_tolerance_ms"])
            or self.peak_temperature >= float(self.system["thermal_warn_c"])
        )


def _result_from_state(
    state: _StreamState,
    spec: _DisturbanceSpec,
    outcome: str,
    reasons: list[str],
    detection_ms: float | None,
    recovery_ms: float,
) -> FaultResult:
    """Freeze the accumulated stream state into one FaultResult."""

    return FaultResult(
        outcome=outcome,
        reason_codes=tuple(reasons),
        detection_latency_ms=detection_ms,
        recovery_latency_ms=recovery_ms,
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


def _positive_number(value: Any) -> bool:
    return oc.is_number(value) and float(value) > 0.0


def _non_negative_number(value: Any) -> bool:
    return oc.is_number(value) and float(value) >= 0.0


def _unit_interval(value: Any) -> bool:
    return oc.is_number(value) and 0.0 <= float(value) <= 1.0


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


class RelayReflexSimulator(FaultOracle):
    """Deterministic multi-channel relay with reflex, fallback and quarantine.

    The simulator steps a fixed tick grid, applies the disturbance to the
    per-channel event stream and thermal state, then selects an outcome by the
    documented precedence. Nothing here samples randomness: given the same
    scenario and disturbance it produces the same result on any machine.
    """

    name = ORACLE_NAME
    version = ORACLE_VERSION
    oracle_type = "deterministic_simulator"
    authority = oc.AUTHORITY_AUTHORITATIVE
    implementation = ORACLE_IMPLEMENTATION
    meter_clock = "simulator_clock"
    meter_state = "simulator_state"
    meter_thermal = "simulator_thermal_model"

    def oracle_block(self, scenario: dict[str, Any]) -> dict[str, Any]:
        return oc.new_oracle(
            self.name,
            oracle_type=self.oracle_type,
            implementation=self.implementation,
            version=self.version,
            authority=self.authority,
            configuration={
                "system": dict(scenario.get("system", {})),
                "precedence": list(OUTCOME_PRECEDENCE),
            },
            seed=None,
            commit=None,
        )

    # -- stream construction -------------------------------------------------

    @staticmethod
    def _check_parameters(kind: str, parameters: dict[str, Any]) -> None:
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
        RelayReflexSimulator._check_parameter_values(kind, parameters)

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

    @staticmethod
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

    @staticmethod
    def _check_parameter_values(kind: str, parameters: dict[str, Any]) -> None:
        """Value ranges whose violation would also run as a silent no-op."""

        for key, floor, exclusive in RelayReflexSimulator._PARAMETER_FLOORS:
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
        if "peak_c" in parameters and not oc.is_number(parameters["peak_c"]):
            raise oc.ContractError(
                f"{kind} peak_c must be a finite number, got "
                f"{parameters['peak_c']!r}"
            )
        if kind == "malformed_spike_burst":
            count = parameters.get("malformed_count")
            if not isinstance(count, int) or isinstance(count, bool) or count < 1:
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
        if kind == "burst_corruption":
            # The tick comparison can never mark an event corrupt for a ratio
            # below 0, so a negative (or NaN) ratio runs the declared
            # disturbance as a no-op and the simulator emits an authoritative
            # `continue` for a corruption that was requested but never applied.
            ratio = parameters.get("corrupt_ratio")
            if not oc.is_number(ratio) or not 0.0 <= float(ratio) <= 1.0:
                raise oc.ContractError(
                    f"corrupt_ratio must be a finite number in [0, 1], got "
                    f"{ratio!r}; outside that range the declared corruption "
                    "cannot be applied"
                )

    @staticmethod
    def _affected(parameters: dict[str, Any], channels: list[str]) -> list[str]:
        """Narrow the disturbance's declared channels to the relay's own."""

        affected = parameters.get("channels")
        if not isinstance(affected, list) or not affected:
            return []
        return [channel for channel in affected if channel in channels]

    @staticmethod
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
        known = set(channels)
        fallback_source = system.get("fallback_source")
        if fallback_source:
            known.add(fallback_source)
        unknown_names = sorted(
            str(name)
            for name in declared
            if not (isinstance(name, str) and name in known)
        )
        if unknown_names:
            raise oc.ContractError(
                f"{kind} declares unknown channels {unknown_names}; this relay "
                f"reads {sorted(known)} — an unknown name would run as a no-op"
            )
        return declared

    @staticmethod
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

    # Numeric relay controls and their fail-closed domains. An out-of-domain
    # control silently rewrites the outcome tiers — a negative quarantine
    # ratio turns every below-threshold corruption into `quarantine` — so an
    # authoritative outcome may not be derived over one. Each entry is
    # ``(key, expected, predicate)``; the predicate decides, the expected
    # text names the domain in the refusal.
    _SYSTEM_CONTROL_DOMAINS = tuple(
        [
            (key, "a positive number", _positive_number)
            for key in (
                "tick_ms",
                "stale_threshold_ms",
                "deadline_ms",
                "hard_deadline_ms",
                "reflex_latency_ms",
                "fallback_latency_ms",
            )
        ]
        + [("jitter_tolerance_ms", "a non-negative number", _non_negative_number)]
        + [
            # The tick count is bounded because the validator replays
            # untrusted scenarios: it walks every live channel for every
            # tick and keeps one trace entry per tick, so an unbounded value
            # would let one record buy an arbitrarily large replay. The
            # default run uses 24.
            ("ticks", "an integer in [1, 1000]", _genuine_count_from(1, 1000)),
            ("reflex_saturation_ticks", "an integer >= 1", _genuine_count_from(1)),
            ("min_healthy_channels", "an integer >= 0", _genuine_count_from(0)),
            ("corruption_quarantine_ratio", "a ratio in [0, 1]", _unit_interval),
        ]
    )

    @staticmethod
    def _check_thermal_ladder(system: dict[str, Any]) -> None:
        thresholds = [
            system["ambient_c"],
            system["thermal_warn_c"],
            system["thermal_limit_c"],
            system["thermal_shutdown_c"],
        ]
        if not all(oc.is_number(value) for value in thresholds):
            raise oc.ContractError(
                "system thermal thresholds must be finite numbers"
            )
        warn, limit, shutdown = (float(value) for value in thresholds[1:])
        if not warn < limit < shutdown:
            raise oc.ContractError(
                "system thermal ladder must be ordered warn < limit < "
                f"shutdown, got {warn}, {limit}, {shutdown}"
            )

    @staticmethod
    def _check_system_channels(system: dict[str, Any]) -> None:
        channels = system["channels"]
        if not (
            isinstance(channels, list)
            and channels
            # Bounded for the same reason ticks is: the replay walks every
            # channel every tick. The default relay has 4.
            and len(channels) <= 32
            and all(isinstance(name, str) and name for name in channels)
        ):
            raise oc.ContractError(
                "system channels must be a non-empty list of at most 32 "
                "channel names"
            )

    @staticmethod
    def _check_system_controls(system: dict[str, Any]) -> None:
        """Refuse relay thresholds an authoritative outcome cannot stand on."""

        for key, expected, valid in RelayReflexSimulator._SYSTEM_CONTROL_DOMAINS:
            value = system[key]
            if not valid(value):
                raise oc.ContractError(
                    f"system {key} must be {expected}, got {value!r}"
                )
        RelayReflexSimulator._check_thermal_ladder(system)
        RelayReflexSimulator._check_system_channels(system)

    def run(self, scenario: dict[str, Any], disturbance: dict[str, Any]) -> FaultResult:
        system = {**DEFAULT_SYSTEM, **dict(scenario.get("system", {}))}
        self._check_system_controls(system)
        channels: list[str] = list(system["channels"])
        kind = disturbance.get("kind")
        if kind not in DISTURBANCES:
            raise oc.ContractError(f"unknown disturbance kind: {kind!r}")
        params = dict(disturbance.get("parameters", {}))
        self._check_parameters(kind, params)
        self._check_onset_within_horizon(kind, params, system)
        # ``affected`` is narrowed to the relay's own channels for the tick
        # loop; ``declared`` keeps every name the disturbance claimed, so a
        # disturbance that also hits the fallback source is seen as such.
        affected = self._affected(params, channels)
        declared = self._declared_channels(kind, params, system, channels)
        spec = _DisturbanceSpec.from_parameters(kind, params, system, affected)

        missing = set(affected) if kind == "missing_channel" else set()
        live_channels = [channel for channel in channels if channel not in missing]

        state = _StreamState(system, channels, live_channels)
        tick_ms = float(system["tick_ms"])
        for tick in range(int(system["ticks"])):
            state.step(spec, tick, tick_ms)

        detection_ms = self._detection_latency_ms(state.detection_ms, spec, system)
        outcome, reasons = self._decide(
            system=system,
            worst_healthy=state.worst_healthy,
            integrity_violation=state.integrity_violation,
            corrupt=state.corrupt,
            total=state.total,
            peak_temperature=state.peak_temperature,
            saturated_ticks=state.saturated_ticks,
            max_staleness=state.max_staleness,
            max_jitter=state.max_jitter,
            dropped=state.dropped,
            result_delay_ms=spec.result_delay_ms,
            missing=missing,
            affected=declared,
        )
        recovery_ms = self._recovery_latency(system, outcome, detection_ms)
        return _result_from_state(state, spec, outcome, reasons, detection_ms, recovery_ms)

    # -- decision ------------------------------------------------------------

    @staticmethod
    def _fallback_available(system: dict[str, Any], missing: set[str], affected) -> bool:
        source = system.get("fallback_source")
        if not source:
            return False
        return source not in missing and source not in set(affected)

    @staticmethod
    def _fail_closed_reasons(
        system: dict[str, Any], state: dict[str, Any], fallback_ok: bool
    ) -> list[str]:
        reasons: list[str] = []
        if state["result_delay_ms"] >= float(system["hard_deadline_ms"]):
            reasons.append("NO_TIMELY_INPUT")
        if state["peak_temperature"] >= float(system["thermal_shutdown_c"]):
            reasons.append("THERMAL_SHUTDOWN")
        if state["worst_healthy"] < int(system["min_healthy_channels"]) and not fallback_ok:
            reasons.append("INSUFFICIENT_HEALTHY_CHANNELS_NO_FALLBACK")
        return reasons

    @staticmethod
    def _quarantine_reasons(
        system: dict[str, Any], state: dict[str, Any], corrupt_ratio: float
    ) -> list[str]:
        reasons: list[str] = []
        if state["integrity_violation"]:
            reasons.append("MALFORMED_STREAM_QUARANTINED")
        if corrupt_ratio >= float(system["corruption_quarantine_ratio"]):
            reasons.append("CORRUPTION_ABOVE_QUARANTINE_THRESHOLD")
        return reasons

    @staticmethod
    def _reflex_reasons(system: dict[str, Any], state: dict[str, Any]) -> list[str]:
        reasons: list[str] = []
        if state["peak_temperature"] >= float(system["thermal_limit_c"]):
            reasons.append("THERMAL_LIMIT_REFLEX")
        if state["saturated_ticks"] >= int(system["reflex_saturation_ticks"]):
            reasons.append("SATURATION_REFLEX")
        return reasons

    @staticmethod
    def _fallback_reasons(
        system: dict[str, Any], state: dict[str, Any], fallback_ok: bool
    ) -> list[str]:
        if state["worst_healthy"] < int(system["min_healthy_channels"]) and fallback_ok:
            return ["FALLBACK_SOURCE_ENGAGED"]
        return []

    @staticmethod
    def _degrade_reasons(
        system: dict[str, Any], state: dict[str, Any], corrupt_ratio: float
    ) -> list[str]:
        reasons: list[str] = []
        if state["max_staleness"] > float(system["stale_threshold_ms"]):
            reasons.append("STALE_BEYOND_THRESHOLD")
        if state["max_jitter"] > float(system["jitter_tolerance_ms"]):
            reasons.append("JITTER_BEYOND_TOLERANCE")
        if state["dropped"] > 0:
            reasons.append("EVENTS_DROPPED")
        if corrupt_ratio > 0.0:
            reasons.append("CORRUPTION_BELOW_QUARANTINE_THRESHOLD")
        if state["peak_temperature"] >= float(system["thermal_warn_c"]):
            reasons.append("THERMAL_WARN")
        if state["result_delay_ms"] > float(system["deadline_ms"]):
            reasons.append("RESULT_PAST_DEADLINE")
        if state["worst_healthy"] < len(system["channels"]):
            reasons.append("REDUCED_CHANNEL_SET")
        return reasons

    def _decide(self, **state: Any) -> tuple[str, list[str]]:
        """Apply the documented precedence and return ``(outcome, reasons)``.

        Each tier's reason helper is pure, so evaluating the tiers in
        precedence order and stopping at the first non-empty one is exactly
        the original first-match rule.
        """

        system = state["system"]
        corrupt_ratio = (
            state["corrupt"] / state["total"] if state["total"] else 0.0
        )
        fallback_ok = self._fallback_available(
            system, state["missing"], state["affected"]
        )
        tiers: tuple[tuple[str, list[str]], ...] = (
            ("fail_closed", self._fail_closed_reasons(system, state, fallback_ok)),
            ("quarantine", self._quarantine_reasons(system, state, corrupt_ratio)),
            ("reflex_action", self._reflex_reasons(system, state)),
            ("fallback", self._fallback_reasons(system, state, fallback_ok)),
            (
                "degrade_gracefully",
                self._degrade_reasons(system, state, corrupt_ratio),
            ),
        )
        for outcome, reasons in tiers:
            if reasons:
                return outcome, reasons
        return "continue", ["WITHIN_TOLERANCE"]

    @staticmethod
    def _recovery_latency(
        system: dict[str, Any], outcome: str, detection_ms: float | None
    ) -> float:
        if outcome == "continue" or detection_ms is None:
            return 0.0
        extra = {
            "reflex_action": float(system["reflex_latency_ms"]),
            "fallback": float(system["fallback_latency_ms"]),
            "quarantine": float(system["reflex_latency_ms"]),
            "fail_closed": float(system["reflex_latency_ms"]),
            "degrade_gracefully": float(system["tick_ms"]),
        }[outcome]
        return round(detection_ms + extra, 3)


# -- generator ---------------------------------------------------------------

# A deliberately shallow prediction: it keys only on the disturbance kind and
# ignores severity, so the corpus contains real generator/oracle disagreements.
PREDICTION_BY_KIND = {
    "sensor_loss": "fallback",
    "stale_sensor": "degrade_gracefully",
    "event_jitter": "continue",
    "burst_corruption": "quarantine",
    "thermal_excursion": "reflex_action",
    "missing_channel": "degrade_gracefully",
    "malformed_spike_burst": "quarantine",
    "delayed_result": "fallback",
    "temporary_saturation": "degrade_gracefully",
}


# kind -> (rng, channels, picked) -> parameters. The rng draws inside each
# builder happen in the same order the old if/elif chain made them, so every
# seed keeps producing the identical proposal stream.
_DISTURBANCE_BUILDERS: dict[str, Any] = {
    "sensor_loss": lambda rng, channels, picked: {
        "channels": sorted(picked),
        "onset_ms": float(rng.choice([4.0, 8.0, 12.0])),
        "duration_ms": float(rng.choice([6.0, 14.0, 30.0])),
    },
    "stale_sensor": lambda rng, channels, picked: {
        "channels": sorted(picked),
        "onset_ms": float(rng.choice([2.0, 6.0])),
        "duration_ms": float(rng.choice([4.0, 9.0, 22.0])),
    },
    "event_jitter": lambda rng, channels, picked: {
        "channels": sorted(picked),
        "onset_ms": 2.0,
        "duration_ms": float(rng.choice([10.0, 40.0])),
        "jitter_ms": float(rng.choice([0.4, 1.2, 3.0])),
    },
    "burst_corruption": lambda rng, channels, picked: {
        "channels": sorted(picked),
        "onset_ms": 4.0,
        "duration_ms": float(rng.choice([10.0, 40.0])),
        "corrupt_ratio": float(rng.choice([0.2, 0.5, 0.8])),
    },
    "thermal_excursion": lambda rng, channels, picked: {
        "channels": sorted(picked),
        "onset_ms": 6.0,
        "ramp_ms": float(rng.choice([8.0, 20.0])),
        "peak_c": float(rng.choice([58.0, 70.0, 84.0, 96.0])),
    },
    "missing_channel": lambda rng, channels, picked: {
        "channels": [rng.choice(channels)],
    },
    "malformed_spike_burst": lambda rng, channels, picked: {
        "channels": sorted(picked),
        "malformed_count": rng.randint(1, 4),
        "malformed_kind": rng.choice(MALFORMED_KINDS),
    },
    "delayed_result": lambda rng, channels, picked: {
        "channels": sorted(picked),
        "delay_ms": float(rng.choice([6.0, 18.0, 44.0])),
    },
    "temporary_saturation": lambda rng, channels, picked: {
        "channels": sorted(picked),
        "onset_ms": 2.0,
        "duration_ms": float(rng.choice([4.0, 16.0])),
    },
}


def _disturbance(rng: random.Random, kind: str, channels: list[str]) -> dict[str, Any]:
    """Build one generator-proposed disturbance. Parameters only, no labels."""

    picked = rng.sample(channels, rng.randint(1, max(1, len(channels) - 1)))
    parameters = _DISTURBANCE_BUILDERS[kind](rng, channels, picked)
    return {"kind": kind, "parameters": parameters}


def propose_scenarios(seed: int, count: int) -> list[dict[str, Any]]:
    """Generator side: scenarios, disturbances and shallow predictions."""

    if count < 1:
        raise oc.ContractError("count must be >= 1")
    rng = random.Random(seed)
    proposals: list[dict[str, Any]] = []
    for index in range(count):
        kind = DISTURBANCES[index % len(DISTURBANCES)]
        system = dict(DEFAULT_SYSTEM)
        system["min_healthy_channels"] = rng.choice([2, 3])
        if rng.random() < 0.2:
            system["fallback_source"] = None
        channels = list(system["channels"])
        disturbance = _disturbance(rng, kind, channels)
        predicted = PREDICTION_BY_KIND[kind]
        proposals.append(
            {
                "index": index,
                "scenario": {
                    "system": system,
                    "mission": "keep the relay loop inside its safety envelope",
                    "disturbance_kind": kind,
                },
                "intervention": disturbance,
                "candidate_prediction": {
                    "predicted_outcome": predicted,
                    "predicted_outcome_label": OUTCOME_LABELS[predicted],
                    "method": "kind-keyed lookup that ignores severity",
                    "confidence": 0.5,
                },
            }
        )
    return proposals


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


def _result_measurements(
    result: FaultResult, intervention: dict[str, Any], meters: dict[str, str]
) -> list[dict[str, Any]]:
    """The oracle-side measurements one executed disturbance yields."""

    measurements = [
        oc.new_measurement(
            "recovery_latency_ms", result.recovery_latency_ms, meters["clock"]
        ),
        oc.new_measurement(
            "healthy_channel_count",
            float(result.worst_healthy_channels),
            meters["state"],
            detail={"worst_case_over_run": True},
        ),
        oc.new_measurement(
            "dropped_event_count", float(result.dropped_events), meters["state"]
        ),
        oc.new_measurement(
            "residual_error", round(result.residual_error, 6), meters["state"]
        ),
        oc.new_measurement(
            "corrupt_ratio",
            round(result.realised_corrupt_ratio, 6),
            meters["state"],
            detail={"requested": intervention["parameters"].get("corrupt_ratio")},
        ),
        oc.new_measurement(
            "peak_temperature_c", result.peak_temperature_c, meters["thermal"]
        ),
    ]
    if result.detection_latency_ms is not None:
        measurements.insert(
            0,
            oc.new_measurement(
                "detection_latency_ms", result.detection_latency_ms, meters["clock"]
            ),
        )
    return measurements


def _oracle_result(
    result: FaultResult, intervention: dict[str, Any], prediction: dict[str, Any],
    meters: dict[str, str],
) -> dict[str, Any]:
    """The oracle-owned result block for one executed disturbance."""

    agreement = (
        "agree" if prediction["predicted_outcome"] == result.outcome else "disagree"
    )
    return oc.new_result(
        measurements=_result_measurements(result, intervention, meters),
        outcome=result.outcome,
        outcome_label=OUTCOME_LABELS[result.outcome],
        reason_codes=list(result.reason_codes),
        prediction_agreement=agreement,
        integrity_violation=result.integrity_violation,
        trace_summary={
            "ticks": len(result.trace),
            "max_staleness_ms": result.max_staleness_ms,
            "max_jitter_ms": result.max_jitter_ms,
            "saturated_ticks": result.saturated_ticks,
        },
    )


def build_records(
    seed: int,
    count: int,
    *,
    oracle: FaultOracle | None = None,
    id_prefix: str = "fr",
) -> list[dict[str, Any]]:
    """Run every proposed disturbance through the oracle and build records."""

    engine = oracle or RelayReflexSimulator()
    meters = _oracle_meters(engine)
    generator = oc.new_generator(
        GENERATOR_NAME, version=GENERATOR_VERSION, kind="programmatic", seed=seed
    )
    records: list[dict[str, Any]] = []
    for proposal in propose_scenarios(seed, count):
        scenario = proposal["scenario"]
        intervention = proposal["intervention"]
        prediction = proposal["candidate_prediction"]
        result = engine.run(scenario, intervention)
        records.append(
            oc.build_record(
                record_id=f"{id_prefix}-{seed}-{proposal['index']:04d}",
                family=FAMILY,
                generator=generator,
                scenario=scenario,
                intervention=intervention,
                candidate_prediction=prediction,
                oracle=engine.oracle_block(scenario),
                result=_oracle_result(result, intervention, prediction, meters),
                provenance=oc.new_provenance(
                    "pipelines/fault_recovery.py",
                    oracle_run="in_process_deterministic",
                ),
            )
        )
    return records


# Quantities the simulator derives from the run. Each maps to the value a
# replay produces, so a tampered latency target is caught the same way a
# tampered outcome is.
def _derived_measurements(result: "FaultResult") -> dict[str, float | None]:
    return {
        "detection_latency_ms": result.detection_latency_ms,
        "recovery_latency_ms": result.recovery_latency_ms,
        "healthy_channel_count": float(result.worst_healthy_channels),
        "dropped_event_count": float(result.dropped_events),
        "residual_error": round(result.residual_error, 6),
        "corrupt_ratio": round(result.realised_corrupt_ratio, 6),
        "peak_temperature_c": result.peak_temperature_c,
    }


def _check_replay_labels(result: dict[str, Any], replay: Any, where: str) -> list[str]:
    """The recorded label, reasons and integrity flag against the replay."""

    errors: list[str] = []
    if result.get("outcome") != replay.outcome:
        errors.append(
            f"{where}.result.outcome: OUTCOME_NOT_REPRODUCIBLE — recorded "
            f"{result.get('outcome')!r} but re-running the simulator over this "
            f"scenario yields {replay.outcome!r}"
        )
    recorded_reasons = result.get("reason_codes")
    if isinstance(recorded_reasons, list) and sorted(
        str(reason) for reason in recorded_reasons
    ) != sorted(replay.reason_codes):
        errors.append(
            f"{where}.result.reason_codes: OUTCOME_NOT_REPRODUCIBLE — recorded "
            f"{sorted(str(r) for r in recorded_reasons)} but the simulator "
            f"reports {sorted(replay.reason_codes)}"
        )
    integrity = result.get("integrity_violation")
    if not isinstance(integrity, bool):
        # The flag is replay-derived, so its absence is a finding, not a
        # reason to skip the comparison: deleting it was all it took for a
        # malformed-spike record to lose its `true` integrity signal and
        # stay curation-eligible.
        errors.append(
            f"{where}.result.integrity_violation must be a boolean — the "
            f"simulator replay reports {replay.integrity_violation}"
        )
    elif integrity is not replay.integrity_violation:
        errors.append(
            f"{where}.result.integrity_violation: OUTCOME_NOT_REPRODUCIBLE — "
            f"recorded {integrity} but the simulator "
            f"reports {replay.integrity_violation}"
        )
    return errors


def _check_replay_measurements(
    result: dict[str, Any], replay: Any, where: str
) -> list[str]:
    """The recorded measurements against the ones the replay derives."""

    errors: list[str] = []
    expected = _derived_measurements(replay)
    measurements = result.get("measurements")
    # Presence first: validating only the readings that remain would let a
    # record delete the replay-derived latencies, counts and ratios wholesale
    # and keep a single surviving reading as its "measured" result.
    recorded_quantities = {
        item.get("quantity")
        for item in (measurements if isinstance(measurements, list) else [])
        if isinstance(item, dict) and isinstance(item.get("quantity"), str)
    }
    missing = sorted(
        quantity
        for quantity, target in expected.items()
        if target is not None and quantity not in recorded_quantities
    )
    if missing:
        errors.append(
            f"{where}.result: OUTCOME_NOT_REPRODUCIBLE — the replay derives "
            f"measurements {missing} that the record does not carry"
        )
    for item in measurements if isinstance(measurements, list) else []:
        if not isinstance(item, dict):
            continue
        quantity = item.get("quantity")
        if not oc.is_enum_value(quantity, expected):
            continue
        target = expected[quantity]
        if target is None:
            # The replay derives no such value — a `detection_latency_ms` on
            # a run with no detection is a fabricated oracle-attributed
            # target, not a reading to skip.
            errors.append(
                f"{where}.result: OUTCOME_NOT_REPRODUCIBLE — the record "
                f"carries {quantity} but the replay derives no such "
                "measurement"
            )
            continue
        if not oc.is_number(item.get("value")):
            continue
        if abs(float(item["value"]) - float(target)) > 1e-6:
            errors.append(
                f"{where}.result: OUTCOME_NOT_REPRODUCIBLE — measured "
                f"{quantity} is {item['value']} but the simulator derives "
                f"{target}"
            )
    return errors


def _replayable_blocks(
    record: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]] | None:
    """The scenario/intervention/result of a record this oracle can replay."""

    oracle = record.get("oracle")
    if not isinstance(oracle, dict):
        return None
    if oracle.get("name") != ORACLE_NAME or oracle.get("type") != "deterministic_simulator":
        return None
    scenario = record.get("scenario")
    intervention = record.get("intervention")
    result = record.get("result")
    if not (
        isinstance(scenario, dict)
        and isinstance(intervention, dict)
        and isinstance(result, dict)
    ):
        return None
    return scenario, intervention, result


def _recheck_deterministic_outcome(record: dict[str, Any], where: str) -> list[str]:
    """Re-run the simulator and compare, for records it produced.

    The scenario and the intervention fully determine this oracle's answer, so
    the label is reproducible rather than merely unfalsifiable. Without this,
    editing ``result.outcome`` to another vocabulary member, updating its prose
    label and reason code, and recomputing the digest produces a record that
    validates clean and is curated as authoritative ground truth.

    Only the in-process simulator is re-run. A hardware replay oracle is not
    reproducible here, and silently "correcting" its labels to the simulator's
    would be worse than not checking.
    """

    blocks = _replayable_blocks(record)
    if blocks is None:
        return []
    scenario, intervention, result = blocks
    try:
        replay = RelayReflexSimulator().run(scenario, intervention)
    except (oc.ContractError, KeyError, TypeError, ValueError) as exc:
        return [
            f"{where}.result: OUTCOME_NOT_REPRODUCIBLE — the recorded scenario "
            f"and intervention do not run on {ORACLE_NAME}: {exc}"
        ]
    return _check_replay_labels(result, replay, where) + _check_replay_measurements(
        result, replay, where
    )


def _check_intervention_parameters(
    kind: str, parameters: Any, where: str
) -> list[str]:
    """The parameter set this disturbance kind requires, and nothing extra."""

    if not isinstance(parameters, dict):
        return [f"{where}.intervention.parameters must be an object"]
    errors: list[str] = []
    required, optional = PARAMETER_SPEC[kind]
    missing = [key for key in required if key not in parameters]
    if missing:
        errors.append(
            f"{where}.intervention.parameters: {kind} requires {sorted(missing)}"
        )
    unknown = sorted(set(parameters) - set(required) - set(optional))
    if unknown:
        errors.append(
            f"{where}.intervention.parameters: {kind} does not use {unknown}"
        )
    return errors


def _check_disturbance_kind_match(
    record: dict[str, Any], kind: str, where: str
) -> list[str]:
    """The scenario is what the student sees; the intervention is what was simulated.

    If they name different faults, the record pairs one fault's description
    with another fault's label.
    """

    scenario = record.get("scenario")
    if not isinstance(scenario, dict):
        return []
    if "disturbance_kind" not in scenario:
        # Absence is a finding, not a pass: deleting the field left the
        # student-visible scenario no longer identifying the fault whose
        # outcome the intervention simulated.
        return [
            f"{where}.scenario.disturbance_kind must be present and name "
            f"the simulated fault ({kind!r})"
        ]
    declared = scenario.get("disturbance_kind")
    if declared != kind:
        return [
            f"{where}.scenario.disturbance_kind: DISTURBANCE_KIND_MISMATCH "
            f"— the scenario presents {declared!r} but the label was "
            f"produced by simulating {kind!r}"
        ]
    return []


def _check_intervention(record: dict[str, Any], where: str) -> list[str]:
    """The proposed disturbance, its parameters, and the scenario that names it."""

    intervention = record.get("intervention")
    if not isinstance(intervention, dict):
        return [f"{where}.intervention must describe the proposed disturbance"]
    kind = intervention.get("kind")
    if kind not in DISTURBANCES:
        return [
            f"{where}.intervention.kind must be one of {sorted(DISTURBANCES)}, "
            f"got {kind!r}"
        ]
    errors = _check_intervention_parameters(
        kind, intervention.get("parameters"), where
    )
    errors += _check_disturbance_kind_match(record, kind, where)
    return errors


def _check_candidate_prediction(record: dict[str, Any], where: str) -> list[str]:
    """The student's proposed outcome, when the record carries one."""

    errors: list[str] = []
    prediction = record.get("candidate_prediction")
    if isinstance(prediction, dict):
        predicted = prediction.get("predicted_outcome")
        if predicted is not None and predicted not in OUTCOMES:
            errors.append(
                f"{where}.candidate_prediction.predicted_outcome must be one of "
                f"{sorted(OUTCOMES)}, got {predicted!r}"
            )
    return errors


def _check_outcome(result: dict[str, Any], where: str) -> list[str]:
    """The recorded outcome, its prose label, and the reasons behind it."""

    errors: list[str] = []
    outcome = result.get("outcome")
    if outcome not in OUTCOMES:
        errors.append(
            f"{where}.result.outcome must be one of {sorted(OUTCOMES)}, got {outcome!r}"
        )
    else:
        label = result.get("outcome_label")
        if label is not None and label != OUTCOME_LABELS[outcome]:
            errors.append(
                f"{where}.result.outcome_label must be {OUTCOME_LABELS[outcome]!r}"
            )
    reasons = result.get("reason_codes")
    if not isinstance(reasons, list) or not reasons:
        errors.append(
            f"{where}.result.reason_codes must be a non-empty array — every fault "
            "outcome needs an explicit reason"
        )
    return errors


def _check_prediction_agreement(record: dict[str, Any], where: str) -> list[str]:
    """``result.prediction_agreement`` is derived, not an independent fact.

    Flipping it to ``"agree"`` would corrupt every disagreement analysis while
    the replay still reproduced the outcome, so it is recomputed from the
    prediction and the outcome instead of being trusted.
    """

    result = record.get("result")
    if not isinstance(result, dict):
        return []
    if "prediction_agreement" not in result:
        # The field is derived, so its absence is a finding, not a pass:
        # deleting it made the record silently disappear from the
        # disagreement analyses this emitted field supports.
        return [
            f"{where}.result.prediction_agreement must be present — it is "
            "derived from the prediction and the outcome"
        ]
    agreement = result.get("prediction_agreement")
    if agreement not in ("agree", "disagree"):
        return [
            f"{where}.result.prediction_agreement must be 'agree' or "
            f"'disagree', got {agreement!r}"
        ]
    prediction = record.get("candidate_prediction")
    predicted = (
        prediction.get("predicted_outcome") if isinstance(prediction, dict) else None
    )
    outcome = result.get("outcome")
    if not isinstance(predicted, str):
        # An agreement label without the prediction it grades is arbitrary:
        # deleting candidate_prediction (or just predicted_outcome) used to
        # skip the derivation check while the label stayed curation-eligible.
        return [
            f"{where}.result.prediction_agreement is recorded but "
            "candidate_prediction.predicted_outcome is missing — an "
            "agreement label needs the prediction it grades"
        ]
    if not oc.is_enum_value(outcome, OUTCOMES):
        return []
    expected = "agree" if predicted == outcome else "disagree"
    if agreement != expected:
        return [
            f"{where}.result.prediction_agreement is {agreement!r} but the "
            f"prediction {predicted!r} against outcome {outcome!r} yields "
            f"{expected!r}"
        ]
    return []


def _check_oracle_configuration_binding(
    record: dict[str, Any], where: str
) -> list[str]:
    """The oracle block must describe the configuration behind its label.

    The replay reads only ``scenario.system``, so a rewritten or deleted
    ``oracle.configuration.system`` stayed validation-clean while the
    authoritative oracle block no longer described the run that produced its
    label — breaking reproducibility and provenance audits.
    """

    oracle = record.get("oracle")
    if not isinstance(oracle, dict) or oracle.get("name") != ORACLE_NAME or (
        oracle.get("type") != "deterministic_simulator"
    ):
        return []
    scenario = record.get("scenario")
    recorded_system = scenario.get("system", {}) if isinstance(scenario, dict) else {}
    configuration = oracle.get("configuration")
    if not isinstance(configuration, dict):
        return [
            f"{where}.oracle.configuration must record the simulator's "
            "system and precedence"
        ]
    errors: list[str] = []
    if configuration.get("system") != recorded_system:
        errors.append(
            f"{where}.oracle.configuration.system does not match "
            "scenario.system — the oracle block must describe the "
            "configuration that produced its label"
        )
    if configuration.get("precedence") != list(OUTCOME_PRECEDENCE):
        errors.append(
            f"{where}.oracle.configuration.precedence must be the canonical "
            f"outcome precedence {list(OUTCOME_PRECEDENCE)}"
        )
    return errors


def check_family(record: dict[str, Any], where: str) -> list[str]:
    """Family checks layered on top of the shared envelope."""

    errors = _check_intervention(record, where)
    errors += _check_candidate_prediction(record, where)
    result = record.get("result")
    if not isinstance(result, dict):
        return errors + [f"{where}.result must be an object"]
    errors += _check_outcome(result, where)
    errors += _check_prediction_agreement(record, where)
    errors += _check_oracle_configuration_binding(record, where)
    errors += _recheck_deterministic_outcome(record, where)
    return errors


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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    generate = sub.add_parser("generate", help="propose disturbances and run the oracle")
    generate.add_argument("--seed", type=int, default=20260823)
    generate.add_argument("--count", type=int, default=9)
    generate.add_argument("--output", help="destination JSONL (must not exist)")

    sub.add_parser("describe", help="print the family contract")

    args = parser.parse_args(argv)
    if args.command == "describe":
        print(json.dumps(describe(), indent=2, sort_keys=True))
        return 0

    records = build_records(args.seed, args.count)
    if args.output:
        written = oc.write_jsonl(args.output, records)
        print(json.dumps({"written": written, "output": args.output}, indent=2))
    else:
        for record in records:
            print(oc.canonical_json(record))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
