#!/usr/bin/env python3
"""Generator side of ``neuromorphic-fault-recovery``: scenario proposals and
record assembly.

Split out of ``fault_recovery.py`` verbatim: :func:`propose_scenarios` builds
the generator-owned scenario, :func:`build_records` runs the oracle and
attaches its measurements and replay hints. Every name here is re-exported
from ``fault_recovery`` so existing call sites resolve unchanged.
"""

from __future__ import annotations

import random
import sys
from pathlib import Path
from typing import Any

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from oracle_grounded import distill_contract as oc  # noqa: E402

if __package__:
    from .fault_simulator import RelayReflexSimulator
    from .fault_types import (
        DEFAULT_SYSTEM,
        DISTURBANCES,
        FAMILY,
        GENERATOR_NAME,
        GENERATOR_VERSION,
        MALFORMED_KINDS,
        OUTCOME_LABELS,
        FaultOracle,
        FaultResult,
        _oracle_meters,
    )
else:
    from fault_simulator import RelayReflexSimulator
    from fault_types import (
        DEFAULT_SYSTEM,
        DISTURBANCES,
        FAMILY,
        GENERATOR_NAME,
        GENERATOR_VERSION,
        MALFORMED_KINDS,
        OUTCOME_LABELS,
        FaultOracle,
        FaultResult,
        _oracle_meters,
    )


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
    rng = random.Random(seed)  # nosec B311 - reproducible dataset generation
    proposals: list[dict[str, Any]] = []
    for index in range(count):
        kind = DISTURBANCES[index % len(DISTURBANCES)]
        system = dict(DEFAULT_SYSTEM)
        system["min_healthy_channels"] = rng.choice([2, 3])  # NOSONAR - seeded data generation
        if rng.random() < 0.2:  # NOSONAR - seeded data generation
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
            result.worst_healthy_channels,
            meters["state"],
            detail={"worst_case_over_run": True},
        ),
        oc.new_measurement(
            "dropped_event_count", result.dropped_events, meters["state"]
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


def _trace_summary(result: FaultResult) -> dict[str, int | float]:
    return {
        "ticks": len(result.trace),
        "max_staleness_ms": result.max_staleness_ms,
        "max_jitter_ms": result.max_jitter_ms,
        "saturated_ticks": result.saturated_ticks,
    }


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
        trace_summary=_trace_summary(result),
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
        oc.GeneratorIdentity(GENERATOR_NAME, version=GENERATOR_VERSION, kind="programmatic"),
        seed=seed,
    )
    records: list[dict[str, Any]] = []
    for proposal in propose_scenarios(seed, count):
        scenario = proposal["scenario"]
        intervention = proposal["intervention"]
        prediction = proposal["candidate_prediction"]
        result = engine.run(scenario, intervention)
        records.append(
            oc.build_record(
                identity=oc.RecordIdentity(
                    f"{id_prefix}-{seed}-{proposal['index']:04d}", FAMILY
                ),
                proposal=oc.Proposal(
                    generator=generator,
                    scenario=scenario,
                    intervention=intervention,
                    candidate_prediction=prediction,
                ),
                verdict=oc.Verdict(
                    oracle=engine.oracle_block(scenario),
                    result=_oracle_result(result, intervention, prediction, meters),
                ),
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
def _derived_measurements(result: "FaultResult") -> dict[str, int | float | None]:
    return {
        "detection_latency_ms": result.detection_latency_ms,
        "recovery_latency_ms": result.recovery_latency_ms,
        "healthy_channel_count": result.worst_healthy_channels,
        "dropped_event_count": result.dropped_events,
        "residual_error": round(result.residual_error, 6),
        "corrupt_ratio": round(result.realised_corrupt_ratio, 6),
        "peak_temperature_c": result.peak_temperature_c,
    }
