#!/usr/bin/env python3
"""Deterministic relay/reflex oracle for ``neuromorphic-fault-recovery``.

Split out of ``fault_recovery.py`` verbatim: the disturbance vocabulary, the
:class:`FaultOracle` boundary, :class:`FaultResult`, the scenario/system
defaults, and :class:`RelayReflexSimulator` — the oracle that actually steps a
declared disturbance through the reflex system. Every name here is re-exported
from ``fault_recovery`` so existing call sites resolve unchanged.
"""

from __future__ import annotations

import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from oracle_grounded import distill_contract as oc  # noqa: E402
from oracle_grounded import envelope  # noqa: E402
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


def _corruption_ticks(spec: _DisturbanceSpec, system: dict[str, Any]) -> frozenset[int]:
    """Keep the existing phase, with one real event when a positive burst misses it."""
    if spec.kind != "burst_corruption" or spec.corrupt_ratio == 0:
        return frozenset()
    if not spec.affected:
        raise oc.ContractError("positive corruption requires a sampled primary channel")
    eligible = [tick for tick in range(int(system["ticks"]))
                if spec.in_window(tick * float(system["tick_ms"]))]
    if not eligible:
        raise oc.ContractError("positive corruption window contains no sampled event")
    selected = [tick for tick in eligible
                if ((tick * 7919) % 1000) / 1000.0 < spec.corrupt_ratio]
    return frozenset(selected or eligible[:1])


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
            # Selected actual ticks preserve the phase when it realises a hit.
            if tick in self.corruption_ticks:
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
        # The recorded configuration must describe the run that happened:
        # the effective system (defaults merged over the scenario's) and the
        # meter identities this oracle read its measurements from. Recording
        # only the caller's partial overrides made a default-driven outcome
        # irreproducible the moment a default changed.
        return oc.new_oracle(
            oc.OracleIdentity(
                self.name,
                oracle_type=self.oracle_type,
                implementation=self.implementation,
                version=self.version,
                authority=self.authority,
            ),
            oc.OracleRun(
                configuration={
                    "system": {**DEFAULT_SYSTEM, **dict(scenario.get("system", {}))},
                    "precedence": list(OUTCOME_PRECEDENCE),
                    "meters": _oracle_meters(self),
                }
            ),
        )

    # -- stream construction -------------------------------------------------

    @staticmethod
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
        RelayReflexSimulator._check_parameter_values(kind, parameters, system)

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
        if kind == "thermal_excursion" and float(onset) >= last_tick_ms:
            # The ramp is evaluated at fraction zero on the onset tick
            # itself, so an onset on the last tick never raises the
            # temperature; the excursion replays as an authoritative no-op.
            raise oc.ContractError(
                f"{kind} onset_ms {onset} leaves no sampled tick after the "
                f"onset (last tick at {last_tick_ms} ms); the ramp never "
                "rises and the declared excursion would run as a no-op"
            )

    @staticmethod
    def _check_sampled_window(kind: str, parameters: dict[str, Any], system: dict[str, Any]) -> None:
        """Duration-based disturbances must affect at least one actual tick."""

        if "duration_ms" not in parameters:
            return
        onset = float(parameters["onset_ms"])
        end = onset + float(parameters["duration_ms"])
        tick_ms = float(system["tick_ms"])
        if not any(onset <= tick * tick_ms < end for tick in range(system["ticks"])):
            raise oc.ContractError(f"{kind} window contains no sampled tick")

    @staticmethod
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

    @staticmethod
    def _check_parameter_values(
        kind: str, parameters: dict[str, Any], system: dict[str, Any]
    ) -> None:
        """Value ranges whose violation would also run as a silent no-op."""

        RelayReflexSimulator._check_declared_channel_list(kind, parameters)
        RelayReflexSimulator._check_parameter_floors(kind, parameters)
        if "peak_c" in parameters and not oc.is_number(parameters["peak_c"]):
            raise oc.ContractError(
                f"{kind} peak_c must be a finite number, got "
                f"{parameters['peak_c']!r}"
            )
        if kind == "thermal_excursion" and oc.is_number(parameters.get("peak_c")):
            ambient = float(system["ambient_c"])
            if float(parameters["peak_c"]) <= ambient:
                # _update_thermal keeps the running maximum with ambient, so
                # a peak at or below it never heats the relay — the declared
                # excursion replays as an authoritative no-op.
                raise oc.ContractError(
                    f"{kind} peak_c {parameters['peak_c']} must exceed the "
                    f"ambient temperature {ambient}; the relay can never "
                    "warm to it"
                )
        if kind == "malformed_spike_burst":
            RelayReflexSimulator._check_malformed_burst(parameters)
        if kind == "burst_corruption":
            RelayReflexSimulator._check_corruption_ratio(parameters)

    @staticmethod
    def _check_malformed_burst(parameters: dict[str, Any]) -> None:
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

    @staticmethod
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

    @staticmethod
    def _check_parameter_floors(kind: str, parameters: dict[str, Any]) -> None:
        """Require finite values within each disturbance parameter's domain."""

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
        required, _ = PARAMETER_SPEC[kind]
        if "channels" in required and not any(
            name in channels for name in declared
        ):
            # The tick loop visits primary channels only, so a required list
            # naming only the fallback source applies no events at all — the
            # declared channel fault replays as an authoritative no-op.
            raise oc.ContractError(
                f"{kind} channels must name at least one primary relay "
                "channel; the fallback source alone leaves the declared "
                "disturbance with nothing to affect"
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
        ambient, warn, limit, shutdown = (
            float(value) for value in thresholds
        )
        if not ambient < warn < limit < shutdown:
            raise oc.ContractError(
                "system thermal ladder must be ordered ambient < warn < "
                f"limit < shutdown, got {ambient}, {warn}, {limit}, "
                f"{shutdown}"
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
            # Unique: the healthy-channel budget counts list entries while
            # the per-channel state collapses duplicates, so ['c0'] * 4
            # reported four healthy channels from one distinct sensor and
            # replayed as an authoritative outcome.
            and len(set(channels)) == len(channels)
        ):
            raise oc.ContractError(
                "system channels must be a non-empty list of at most 32 "
                "unique channel names"
            )
        fallback = system["fallback_source"]
        if fallback is not None and not (
            isinstance(fallback, str) and fallback.strip()
        ):
            # Any truthy value used to satisfy the fallback tier, so
            # `fallback_source: 123` produced an authoritative `fallback`
            # with FALLBACK_SOURCE_ENGAGED and no named source.
            raise oc.ContractError(
                "system fallback_source must be a non-empty string or null, "
                f"got {fallback!r}"
            )
        if isinstance(fallback, str) and fallback in channels:
            # A fallback names a REDUNDANT source. Naming a primary channel
            # let a surviving primary engage as its own fallback, producing
            # an authoritative `fallback` with no redundant relay behind it.
            raise oc.ContractError(
                f"system fallback_source {fallback!r} is one of the primary "
                "channels; a fallback must be a redundant source"
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
        if system["hard_deadline_ms"] <= system["deadline_ms"]:
            raise oc.ContractError("system hard_deadline_ms must exceed deadline_ms")
        RelayReflexSimulator._check_thermal_ladder(system)
        RelayReflexSimulator._check_system_channels(system)
        if system["min_healthy_channels"] > len(system["channels"]):
            raise oc.ContractError("system min_healthy_channels exceeds primary channel count")

    def run(self, scenario: dict[str, Any], disturbance: dict[str, Any]) -> FaultResult:
        supplied_system = dict(scenario.get("system", {}))
        unknown_controls = sorted(set(supplied_system) - set(DEFAULT_SYSTEM))
        if unknown_controls:
            # A misspelled control would sit in the recorded configuration
            # while the simulator ran on the defaults — the record would
            # describe a run that never happened.
            raise oc.ContractError(
                f"scenario.system declares unknown controls "
                f"{unknown_controls}; the simulator reads "
                f"{sorted(DEFAULT_SYSTEM)}"
            )
        system = {**DEFAULT_SYSTEM, **supplied_system}
        self._check_system_controls(system)
        channels: list[str] = list(system["channels"])
        kind = disturbance.get("kind")
        if kind not in DISTURBANCES:
            raise oc.ContractError(f"unknown disturbance kind: {kind!r}")
        params = dict(disturbance.get("parameters", {}))
        self._check_parameters(kind, params, system)
        self._check_onset_within_horizon(kind, params, system)
        self._check_sampled_window(kind, params, system)
        # ``affected`` is narrowed to the relay's own channels for the tick
        # loop; ``declared`` keeps every name the disturbance claimed, so a
        # disturbance that also hits the fallback source is seen as such.
        affected = self._affected(params, channels)
        declared = self._declared_channels(kind, params, system, channels)
        spec = _DisturbanceSpec.from_parameters(kind, params, system, affected)

        missing = set(affected) if kind == "missing_channel" else set()
        live_channels = [channel for channel in channels if channel not in missing]
        if kind == "malformed_spike_burst":
            # The tick loop emits at most one malformed event per affected
            # live channel per tick, so a count beyond that capacity is a
            # recorded severity the simulation can never produce.
            capacity = int(system["ticks"]) * len(
                set(affected) & set(live_channels)
            )
            if params["malformed_count"] > capacity:
                raise oc.ContractError(
                    f"malformed_count {params['malformed_count']} exceeds the "
                    f"burst capacity {capacity} ({system['ticks']} ticks x "
                    f"{len(set(affected) & set(live_channels))} affected live "
                    "channels); the recorded severity would be silently "
                    "truncated"
                )

        state = _StreamState(system, channels, live_channels)
        state.corruption_ticks = _corruption_ticks(spec, system)
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
        if corrupt_ratio > 0 and corrupt_ratio >= float(system["corruption_quarantine_ratio"]):
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
