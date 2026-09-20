#!/usr/bin/env python3
"""Deterministic relay/reflex oracle for ``neuromorphic-fault-recovery``.

Split out of ``fault_recovery.py`` verbatim: :class:`RelayReflexSimulator` —
the oracle that steps a declared disturbance through the reflex system — plus
the run/decide/latency reasoning that labels each scenario's outcome. The
family vocabulary and contract shapes live in ``fault_types``, the tick loop's
stream state in ``fault_stream``, and the preflight validators in
``fault_preflight``. Every name here is re-exported from ``fault_recovery`` so
existing call sites resolve unchanged.
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
    from .fault_preflight import (
        _affected,
        _check_onset_within_horizon,
        _check_parameters,
        _check_sampled_window,
        _declared_channels,
        _detection_latency_ms,
    )
    from .fault_system import _check_system_controls
    from .fault_stream import (
        _result_from_state,
        _StreamState,
        _StreamVerdict,
    )
    from .fault_types import (
        DEFAULT_SYSTEM,
        DISTURBANCES,
        ORACLE_IMPLEMENTATION,
        ORACLE_NAME,
        ORACLE_VERSION,
        OUTCOME_PRECEDENCE,
        FaultOracle,
        FaultResult,
        _corruption_ticks,
        _oracle_meters,
        _spec_from_parameters,
    )
else:
    from fault_preflight import (
        _affected,
        _check_onset_within_horizon,
        _check_parameters,
        _check_sampled_window,
        _declared_channels,
        _detection_latency_ms,
    )
    from fault_system import _check_system_controls
    from fault_stream import (
        _result_from_state,
        _StreamState,
        _StreamVerdict,
    )
    from fault_types import (
        DEFAULT_SYSTEM,
        DISTURBANCES,
        ORACLE_IMPLEMENTATION,
        ORACLE_NAME,
        ORACLE_VERSION,
        OUTCOME_PRECEDENCE,
        FaultOracle,
        FaultResult,
        _corruption_ticks,
        _oracle_meters,
        _spec_from_parameters,
    )


def _check_burst_capacity(
    kind: str, params: dict[str, Any], system: dict[str, Any], live_affected: set[str]
) -> None:
    if kind != "malformed_spike_burst":
        return
    # The tick loop emits at most one malformed event per affected
    # live channel per tick, so a count beyond that capacity is a
    # recorded severity the simulation can never produce.
    capacity = int(system["ticks"]) * len(live_affected)
    if params["malformed_count"] > capacity:
        raise oc.ContractError(
            f"malformed_count {params['malformed_count']} exceeds the "
            f"burst capacity {capacity} ({system['ticks']} ticks x "
            f"{len(live_affected)} affected live "
            "channels); the recorded severity would be silently "
            "truncated"
        )


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
        _check_system_controls(system)
        channels: list[str] = list(system["channels"])
        kind = disturbance.get("kind")
        if kind not in DISTURBANCES:
            raise oc.ContractError(f"unknown disturbance kind: {kind!r}")
        params = dict(disturbance.get("parameters", {}))
        _check_parameters(kind, params, system)
        _check_onset_within_horizon(kind, params, system)
        _check_sampled_window(kind, params, system)
        # ``affected`` is narrowed to the relay's own channels for the tick
        # loop; ``declared`` keeps every name the disturbance claimed, so a
        # disturbance that also hits the fallback source is seen as such.
        affected = _affected(params, channels)
        declared = _declared_channels(kind, params, system, channels)
        spec = _spec_from_parameters(kind, params, system, affected)

        missing = set(affected) if kind == "missing_channel" else set()
        live_channels = [channel for channel in channels if channel not in missing]
        _check_burst_capacity(
            kind, params, system, set(affected) & set(live_channels)
        )

        state = _StreamState(system, channels, live_channels)
        state.corruption_ticks = _corruption_ticks(spec, system)
        tick_ms = float(system["tick_ms"])
        for tick in range(int(system["ticks"])):
            state.step(spec, tick, tick_ms)

        detection_ms = _detection_latency_ms(state.detection_ms, spec, system)
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
        return _result_from_state(
            state, spec, _StreamVerdict(outcome, reasons, detection_ms, recovery_ms)
        )

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
        checks = (
            (
                state["max_staleness"] > float(system["stale_threshold_ms"]),
                "STALE_BEYOND_THRESHOLD",
            ),
            (
                state["max_jitter"] > float(system["jitter_tolerance_ms"]),
                "JITTER_BEYOND_TOLERANCE",
            ),
            (state["dropped"] > 0, "EVENTS_DROPPED"),
            (corrupt_ratio > 0.0, "CORRUPTION_BELOW_QUARANTINE_THRESHOLD"),
            (
                state["peak_temperature"] >= float(system["thermal_warn_c"]),
                "THERMAL_WARN",
            ),
            (
                state["result_delay_ms"] > float(system["deadline_ms"]),
                "RESULT_PAST_DEADLINE",
            ),
            (
                state["worst_healthy"] < len(system["channels"]),
                "REDUCED_CHANNEL_SET",
            ),
        )
        return [reason for hit, reason in checks if hit]

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
