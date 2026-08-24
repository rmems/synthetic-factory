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

# Every malformed kind is the same integrity failure as far as the relay is
# concerned — the stream can no longer be trusted, so it is quarantined. The
# kind is carried through as scenario metadata, not as a severity dial.
MALFORMED_KINDS = ("non_monotonic_time", "negative_amplitude", "unknown_channel")


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

    def run(self, scenario: dict[str, Any], disturbance: dict[str, Any]) -> "FaultResult":
        raise NotImplementedError

    def oracle_block(self, scenario: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


@dataclass(frozen=True)
class FaultResult:
    """One executed disturbance: the outcome plus the state it was read from."""

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
    def _affected(parameters: dict[str, Any], channels: list[str]) -> list[str]:
        """Narrow the disturbance's declared channels to the relay's own."""

        affected = parameters.get("channels")
        if not isinstance(affected, list) or not affected:
            return []
        return [channel for channel in affected if channel in channels]

    def run(self, scenario: dict[str, Any], disturbance: dict[str, Any]) -> FaultResult:
        system = {**DEFAULT_SYSTEM, **dict(scenario.get("system", {}))}
        channels: list[str] = list(system["channels"])
        kind = disturbance.get("kind")
        if kind not in DISTURBANCES:
            raise oc.ContractError(f"unknown disturbance kind: {kind!r}")
        params = dict(disturbance.get("parameters", {}))
        # ``affected`` is narrowed to the relay's own channels for the tick
        # loop; ``declared`` keeps every name the disturbance claimed, so a
        # disturbance that also hits the fallback source is seen as such.
        affected = self._affected(params, channels)
        declared = params.get("channels")
        declared = list(declared) if isinstance(declared, list) else []
        tick_ms = float(system["tick_ms"])
        ticks = int(system["ticks"])

        missing = set(affected) if kind == "missing_channel" else set()
        live_channels = [channel for channel in channels if channel not in missing]

        last_fresh_ms = {channel: 0.0 for channel in channels}
        saturated_since: dict[str, int] = {}
        saturated_ticks = 0
        dropped = 0
        corrupt = 0
        total = 0
        max_staleness = 0.0
        max_jitter = 0.0
        integrity_violation = False
        peak_temperature = float(system["ambient_c"])
        worst_healthy = len(live_channels)
        detection_ms: float | None = None
        trace: list[dict[str, Any]] = []

        onset_ms = float(params.get("onset_ms", 0.0))
        duration_ms = float(params.get("duration_ms", 0.0))
        jitter_ms = float(params.get("jitter_ms", 0.0))
        stale_age_ms = float(params.get("stale_age_ms", 0.0))
        corrupt_ratio_target = float(params.get("corrupt_ratio", 0.0))
        malformed_count = int(params.get("malformed_count", 0))
        peak_c = float(params.get("peak_c", system["ambient_c"]))
        ramp_ms = max(float(params.get("ramp_ms", 1.0)), 1e-6)
        result_delay_ms = float(params.get("delay_ms", 0.0))
        malformed_emitted = 0

        for tick in range(ticks):
            now_ms = tick * tick_ms
            in_window = onset_ms <= now_ms < (onset_ms + duration_ms)

            if kind == "thermal_excursion" and now_ms >= onset_ms:
                ramped = min(1.0, (now_ms - onset_ms) / ramp_ms)
                temperature = system["ambient_c"] + ramped * (
                    peak_c - float(system["ambient_c"])
                )
                peak_temperature = max(peak_temperature, temperature)

            healthy_now = 0
            for channel in live_channels:
                total += 1
                lost = kind == "sensor_loss" and in_window and channel in affected
                stale = (
                    kind == "stale_sensor"
                    and channel in affected
                    and onset_ms <= now_ms < (onset_ms + stale_age_ms)
                )
                if lost:
                    dropped += 1
                elif not stale:
                    last_fresh_ms[channel] = now_ms

                if kind == "event_jitter" and channel in affected:
                    offset = jitter_ms if tick % 2 == 0 else -jitter_ms
                    max_jitter = max(max_jitter, abs(offset))

                if kind == "burst_corruption" and channel in affected and in_window:
                    # Deterministic interleave: corrupt the first
                    # ``corrupt_ratio`` share of each affected tick window.
                    if (tick % 4) / 4.0 < corrupt_ratio_target:
                        corrupt += 1

                if (
                    kind == "malformed_spike_burst"
                    and channel in affected
                    and malformed_emitted < malformed_count
                ):
                    malformed_emitted += 1
                    integrity_violation = True

                saturating = (
                    kind == "temporary_saturation" and channel in affected and in_window
                )
                if saturating:
                    saturated_since.setdefault(channel, tick)
                    saturated_ticks = max(
                        saturated_ticks, tick - saturated_since[channel] + 1
                    )
                else:
                    saturated_since.pop(channel, None)

                staleness = now_ms - last_fresh_ms[channel]
                max_staleness = max(max_staleness, staleness)

                channel_healthy = (
                    not lost
                    and staleness <= float(system["stale_threshold_ms"])
                    and not saturating
                )
                healthy_now += 1 if channel_healthy else 0

            worst_healthy = min(worst_healthy, healthy_now)

            degraded_now = (
                healthy_now < len(channels)
                or integrity_violation
                or corrupt > 0
                or max_jitter > float(system["jitter_tolerance_ms"])
                or peak_temperature >= float(system["thermal_warn_c"])
            )
            if degraded_now and detection_ms is None:
                detection_ms = now_ms
            trace.append(
                {
                    "t_ms": now_ms,
                    "healthy": healthy_now,
                    "temperature_c": round(peak_temperature, 3),
                }
            )

        if detection_ms is None and result_delay_ms > float(system["deadline_ms"]):
            # A late result is only observable once its deadline passes.
            detection_ms = float(system["deadline_ms"])

        outcome, reasons = self._decide(
            system=system,
            worst_healthy=worst_healthy,
            integrity_violation=integrity_violation,
            corrupt=corrupt,
            total=total,
            peak_temperature=peak_temperature,
            saturated_ticks=saturated_ticks,
            max_staleness=max_staleness,
            max_jitter=max_jitter,
            dropped=dropped,
            result_delay_ms=result_delay_ms,
            missing=missing,
            affected=declared,
        )
        recovery_ms = self._recovery_latency(system, outcome, detection_ms)
        return FaultResult(
            outcome=outcome,
            reason_codes=tuple(reasons),
            detection_latency_ms=detection_ms,
            recovery_latency_ms=recovery_ms,
            worst_healthy_channels=worst_healthy,
            dropped_events=dropped,
            corrupt_events=corrupt,
            total_events=total,
            peak_temperature_c=round(peak_temperature, 3),
            max_staleness_ms=round(max_staleness, 3),
            max_jitter_ms=round(max_jitter, 3),
            saturated_ticks=saturated_ticks,
            integrity_violation=integrity_violation,
            result_delay_ms=result_delay_ms,
            trace=tuple(trace),
        )

    # -- decision ------------------------------------------------------------

    @staticmethod
    def _fallback_available(system: dict[str, Any], missing: set[str], affected) -> bool:
        source = system.get("fallback_source")
        if not source:
            return False
        return source not in missing and source not in set(affected)

    def _decide(self, **state: Any) -> tuple[str, list[str]]:
        """Apply the documented precedence and return ``(outcome, reasons)``."""

        system = state["system"]
        corrupt_ratio = (
            state["corrupt"] / state["total"] if state["total"] else 0.0
        )
        fallback_ok = self._fallback_available(
            system, state["missing"], state["affected"]
        )

        reasons: list[str] = []
        if state["result_delay_ms"] >= float(system["hard_deadline_ms"]):
            reasons.append("NO_TIMELY_INPUT")
        if state["peak_temperature"] >= float(system["thermal_shutdown_c"]):
            reasons.append("THERMAL_SHUTDOWN")
        if state["worst_healthy"] < int(system["min_healthy_channels"]) and not fallback_ok:
            reasons.append("INSUFFICIENT_HEALTHY_CHANNELS_NO_FALLBACK")
        if reasons:
            return "fail_closed", reasons

        if state["integrity_violation"]:
            reasons.append("MALFORMED_STREAM_QUARANTINED")
        if corrupt_ratio >= float(system["corruption_quarantine_ratio"]):
            reasons.append("CORRUPTION_ABOVE_QUARANTINE_THRESHOLD")
        if reasons:
            return "quarantine", reasons

        if state["peak_temperature"] >= float(system["thermal_limit_c"]):
            reasons.append("THERMAL_LIMIT_REFLEX")
        if state["saturated_ticks"] >= int(system["reflex_saturation_ticks"]):
            reasons.append("SATURATION_REFLEX")
        if reasons:
            return "reflex_action", reasons

        if state["worst_healthy"] < int(system["min_healthy_channels"]) and fallback_ok:
            return "fallback", ["FALLBACK_SOURCE_ENGAGED"]

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
        if reasons:
            return "degrade_gracefully", reasons

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


def _disturbance(rng: random.Random, kind: str, channels: list[str]) -> dict[str, Any]:
    """Build one generator-proposed disturbance. Parameters only, no labels."""

    picked = rng.sample(channels, rng.randint(1, max(1, len(channels) - 1)))
    parameters: dict[str, Any] = {"channels": sorted(picked)}
    if kind == "sensor_loss":
        parameters |= {
            "onset_ms": float(rng.choice([4.0, 8.0, 12.0])),
            "duration_ms": float(rng.choice([6.0, 14.0, 30.0])),
        }
    elif kind == "stale_sensor":
        parameters |= {
            "onset_ms": float(rng.choice([2.0, 6.0])),
            "stale_age_ms": float(rng.choice([4.0, 9.0, 22.0])),
        }
    elif kind == "event_jitter":
        parameters |= {"jitter_ms": float(rng.choice([0.4, 1.2, 3.0]))}
    elif kind == "burst_corruption":
        parameters |= {
            "onset_ms": 4.0,
            "duration_ms": float(rng.choice([10.0, 40.0])),
            "corrupt_ratio": float(rng.choice([0.2, 0.5, 0.8])),
        }
    elif kind == "thermal_excursion":
        parameters |= {
            "onset_ms": 6.0,
            "ramp_ms": float(rng.choice([8.0, 20.0])),
            "peak_c": float(rng.choice([58.0, 70.0, 84.0, 96.0])),
        }
    elif kind == "missing_channel":
        parameters = {"channels": [rng.choice(channels)]}
    elif kind == "malformed_spike_burst":
        parameters |= {
            "malformed_count": rng.randint(1, 4),
            "malformed_kind": rng.choice(MALFORMED_KINDS),
        }
    elif kind == "delayed_result":
        parameters = {
            "channels": sorted(picked),
            "delay_ms": float(rng.choice([6.0, 18.0, 44.0])),
        }
    elif kind == "temporary_saturation":
        parameters |= {
            "onset_ms": 2.0,
            "duration_ms": float(rng.choice([4.0, 16.0])),
        }
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


def build_records(
    seed: int,
    count: int,
    *,
    oracle: FaultOracle | None = None,
    id_prefix: str = "fr",
) -> list[dict[str, Any]]:
    """Run every proposed disturbance through the oracle and build records."""

    engine = oracle or RelayReflexSimulator()
    generator = oc.new_generator(
        GENERATOR_NAME, version=GENERATOR_VERSION, kind="programmatic", seed=seed
    )
    records: list[dict[str, Any]] = []
    for proposal in propose_scenarios(seed, count):
        scenario = proposal["scenario"]
        intervention = proposal["intervention"]
        prediction = proposal["candidate_prediction"]
        result = engine.run(scenario, intervention)
        measurements = [
            oc.new_measurement(
                "recovery_latency_ms", result.recovery_latency_ms, "simulator_clock"
            ),
            oc.new_measurement(
                "healthy_channel_count",
                float(result.worst_healthy_channels),
                "simulator_state",
                detail={"worst_case_over_run": True},
            ),
            oc.new_measurement(
                "dropped_event_count", float(result.dropped_events), "simulator_state"
            ),
            oc.new_measurement(
                "residual_error", round(result.residual_error, 6), "simulator_state"
            ),
            oc.new_measurement(
                "peak_temperature_c", result.peak_temperature_c, "simulator_thermal_model"
            ),
        ]
        if result.detection_latency_ms is not None:
            measurements.insert(
                0,
                oc.new_measurement(
                    "detection_latency_ms",
                    result.detection_latency_ms,
                    "simulator_clock",
                ),
            )
        agreement = (
            "agree"
            if prediction["predicted_outcome"] == result.outcome
            else "disagree"
        )
        oracle_result = oc.new_result(
            measurements=measurements,
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
        records.append(
            oc.build_record(
                record_id=f"{id_prefix}-{seed}-{proposal['index']:04d}",
                family=FAMILY,
                generator=generator,
                scenario=scenario,
                intervention=intervention,
                candidate_prediction=prediction,
                oracle=engine.oracle_block(scenario),
                result=oracle_result,
                provenance=oc.new_provenance(
                    "pipelines/fault_recovery.py",
                    oracle_run="in_process_deterministic",
                ),
            )
        )
    return records


def check_family(record: dict[str, Any], where: str) -> list[str]:
    """Family checks layered on top of the shared envelope."""

    errors: list[str] = []
    intervention = record.get("intervention")
    if not isinstance(intervention, dict):
        errors.append(f"{where}.intervention must describe the proposed disturbance")
    elif intervention.get("kind") not in DISTURBANCES:
        errors.append(
            f"{where}.intervention.kind must be one of {sorted(DISTURBANCES)}, "
            f"got {intervention.get('kind')!r}"
        )
    prediction = record.get("candidate_prediction")
    if isinstance(prediction, dict):
        predicted = prediction.get("predicted_outcome")
        if predicted is not None and predicted not in OUTCOMES:
            errors.append(
                f"{where}.candidate_prediction.predicted_outcome must be one of "
                f"{sorted(OUTCOMES)}, got {predicted!r}"
            )
    result = record.get("result")
    if not isinstance(result, dict):
        return errors + [f"{where}.result must be an object"]
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
