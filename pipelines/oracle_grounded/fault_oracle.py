#!/usr/bin/env python3
"""Record assembly of the fault-recovery family through the merged contract (F1).

The agent's single import::

    from oracle_grounded import fault_oracle as fo
    records = fo.build_records(20260823, 9, produced_at="2026-08-23T00:00:00.000Z")
    oc.write_jsonl(new_path, records)

Every record is UNVALIDATED: nothing here self-certifies. The oracle's meters
name the instruments behind the seven readings, the result block emits every
declared oracle-label key (``EMITTED_LABEL_KEYS == ORACLE_LABEL_KEYS``),
counts stay genuine integers, and ``produced_at`` is injectable so two builds
with the same seed and timestamp are byte-identical, digest included.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Any

from . import distill_builders as builders
from . import distill_vocabulary as vocab
from . import envelope
from . import fault_boundary as boundary
from . import fault_scenario as scenario
from . import fault_simulator as simulator
from . import fault_vocabulary as fv
from .import_twins import bind_import_twin

FaultOracle = boundary.FaultOracle
FaultResult = boundary.FaultResult
RelayReflexSimulator = simulator.RelayReflexSimulator
propose_scenarios = scenario.propose_scenarios
ORACLE_LABEL_KEYS = fv.ORACLE_LABEL_KEYS


@dataclass(frozen=True)
class OracleMeters:
    """The instruments an oracle declares behind its clock, state and thermal readings."""

    clock: str
    state: str
    thermal: str

    def of(self, role: str) -> str:
        return getattr(self, role)


def oracle_meters(engine: boundary.FaultOracle) -> OracleMeters:
    """The engine's declared meters; refused when any role is unset, so an
    injected non-simulator oracle can never inherit ``simulator_*`` provenance."""
    meters = OracleMeters(engine.meter_clock, engine.meter_state, engine.meter_thermal)
    unset = sorted(f.name for f in fields(meters) if vocab.missing_string(meters.of(f.name)))
    fv.refuse_when(
        bool(unset),
        fv.FINDING_ORACLE_METERS_UNDECLARED,
        f"oracle {engine.name!r} does not declare its measurement meters ({unset}); "
        "readings cannot be attributed to an unnamed instrument",
    )
    return meters


# (quantity, meter role, value of a result), in emission order after the
# optional detection reading. Counts are genuine ints: the merged builder
# keeps them, and mixing conventions would split canonical bytes.
_READINGS = (
    ("recovery_latency_ms", "clock", lambda result: result.recovery_latency_ms),
    ("healthy_channel_count", "state", lambda result: result.worst_healthy_channels),
    ("dropped_event_count", "state", lambda result: result.dropped_events),
    ("residual_error", "state", lambda result: round(result.residual_error, 6)),
    ("corrupt_ratio", "state", lambda result: round(result.realised_corrupt_ratio, 6)),
    ("peak_temperature_c", "thermal", lambda result: result.peak_temperature_c),
)
# quantity -> the detail built from the intervention's parameters; the
# requested corrupt ratio is recorded only when the intervention declares it.
_DETAILS = {
    "healthy_channel_count": lambda params: {"worst_case_over_run": True},
    "corrupt_ratio": lambda params: (
        {"requested": params["corrupt_ratio"]} if "corrupt_ratio" in params else None
    ),
}


def _detail(quantity: str, params: dict[str, Any]) -> dict[str, Any] | None:
    return _DETAILS.get(quantity, lambda _params: None)(params)


def result_measurements(
    result: boundary.FaultResult, intervention: dict[str, Any], meters: OracleMeters
) -> list[dict[str, Any]]:
    """The metered readings of one result; detection first, only when detected."""
    params = intervention["parameters"]
    readings = [
        builders.new_measurement(quantity, value_of(result), meters.of(role), detail=_detail(quantity, params))
        for quantity, role, value_of in _READINGS
    ]
    if result.detection_latency_ms is not None:
        detection = builders.new_measurement(
            "detection_latency_ms", result.detection_latency_ms, meters.clock
        )
        readings.insert(0, detection)
    return readings


# result key -> FaultResult attribute, for the twelve result-level labels.
_LABEL_FIELDS = (
    ("outcome", "outcome"), ("reason_codes", "reason_codes"),
    ("detection_latency_ms", "detection_latency_ms"),
    ("recovery_latency_ms", "recovery_latency_ms"),
    ("worst_healthy_channels", "worst_healthy_channels"),
    ("dropped_event_count", "dropped_events"), ("corrupt_event_count", "corrupt_events"),
    ("total_event_count", "total_events"), ("peak_temperature_c", "peak_temperature_c"),
    ("integrity_violation", "integrity_violation"),
)
_TRACE_FIELDS = ("max_staleness_ms", "max_jitter_ms", "saturated_ticks")


def _labels(result: boundary.FaultResult) -> dict[str, Any]:
    """The twelve result-level label values plus the trace summary."""
    labels: dict[str, Any] = {key: getattr(result, attr) for key, attr in _LABEL_FIELDS}
    labels["reason_codes"] = list(result.reason_codes)
    labels["outcome_label"] = fv.OUTCOME_LABELS[result.outcome]
    labels["trace_summary"] = {name: getattr(result, name) for name in _TRACE_FIELDS}
    return labels


_SENTINEL_LABELS = _labels(
    boundary.FaultResult(
        outcome=fv.OUTCOME_CONTINUE, reason_codes=(fv.REASON_WITHIN_TOLERANCE,),
        detection_latency_ms=None, recovery_latency_ms=0.0, worst_healthy_channels=0,
        dropped_events=0, corrupt_events=0, total_events=0, peak_temperature_c=0.0,
        max_staleness_ms=0.0, max_jitter_ms=0.0, saturated_ticks=0,
        integrity_violation=False, result_delay_ms=0.0,
    )
)
# Every label key a result block carries, computed once from the emitter
# itself; ``fault_vocabulary.ORACLE_LABEL_KEYS`` is asserted equal to it.
EMITTED_LABEL_KEYS = (
    frozenset(_SENTINEL_LABELS)
    | frozenset({"prediction_agreement"})
    | frozenset(_SENTINEL_LABELS["trace_summary"])
)


def prediction_agreement(prediction: dict[str, Any], outcome: str) -> str:
    return "agree" if prediction.get("predicted_outcome") == outcome else "disagree"


def oracle_result(
    result: boundary.FaultResult,
    prediction: dict[str, Any],
    intervention: dict[str, Any],
    meters: OracleMeters,
) -> dict[str, Any]:
    """The oracle-owned result block for one executed disturbance."""
    return builders.new_result(
        measurements=result_measurements(result, intervention, meters),
        prediction_agreement=prediction_agreement(prediction, result.outcome),
        **_labels(result),
    )


def _produced_at(value: Any) -> str:
    """One timestamp per batch: the caller's pinned instant, else now."""
    if value is None:
        return envelope.utc_now_iso()
    fv.refuse_when(
        not vocab.is_timestamp(value),
        fv.FINDING_PRODUCED_AT_NOT_A_TIMESTAMP,
        f"produced_at must be an ISO-8601 UTC instant, got {value!r}",
    )
    return value


@dataclass(frozen=True)
class _Batch:
    """What every record of one build shares."""

    engine: boundary.FaultOracle
    meters: OracleMeters
    generator: dict[str, Any]
    provenance: dict[str, Any]
    seed: int


def _record(batch: _Batch, proposal: dict[str, Any]) -> dict[str, Any]:
    scenario_block = proposal["scenario"]
    intervention = proposal["intervention"]
    prediction = proposal["candidate_prediction"]
    result = batch.engine.run(scenario_block, intervention)
    return builders.build_record(
        identity=builders.RecordIdentity(
            f"{fv.RECORD_ID_PREFIX}-{batch.seed}-{proposal['index']:04d}", fv.FAMILY
        ),
        proposal=builders.Proposal(
            generator=batch.generator,
            scenario=scenario_block,
            intervention=intervention,
            candidate_prediction=prediction,
        ),
        verdict=builders.Verdict(
            oracle=batch.engine.oracle_block(scenario_block),
            result=oracle_result(result, prediction, intervention, batch.meters),
        ),
        provenance=batch.provenance,
    )


def build_records(
    seed: int,
    count: int,
    *,
    produced_at: str | None = None,
    oracle: boundary.FaultOracle | None = None,
) -> list[dict[str, Any]]:
    """Run every proposed disturbance through the oracle into UNVALIDATED records.

    Ids are ``fr-{seed}-{index:04d}``. ``produced_at`` pins the provenance
    timestamp (validated as an ISO-8601 UTC instant); omitted, one
    ``utc_now_iso()`` serves the whole batch. ``oracle`` defaults to the
    simulator and must declare its meters.
    """
    proposals = scenario.propose_scenarios(seed, count)
    engine = oracle or simulator.RelayReflexSimulator()
    meters = oracle_meters(engine)
    provenance = builders.new_provenance(
        fv.PRODUCER, produced_at=_produced_at(produced_at), oracle_run=fv.ORACLE_RUN
    )
    identity = builders.GeneratorIdentity(
        fv.GENERATOR_NAME, version=fv.GENERATOR_VERSION, kind=fv.GENERATOR_KIND
    )
    batch = _Batch(engine, meters, builders.new_generator(identity, seed=seed), provenance, seed)
    return [_record(batch, proposal) for proposal in proposals]


def describe() -> dict[str, Any]:
    """The family contract as plain JSON-able data (for F2's CLI)."""
    engine = simulator.RelayReflexSimulator
    return {
        "family": fv.FAMILY,
        "schema_version": vocab.SCHEMA_VERSION,
        "disturbances": list(fv.DISTURBANCES),
        "outcomes": list(fv.OUTCOMES),
        "outcome_labels": dict(fv.OUTCOME_LABELS),
        "precedence": list(fv.OUTCOME_PRECEDENCE),
        "reason_codes": list(fv.REASON_CODES),
        "finding_codes": list(fv.FINDING_CODES),
        "oracle_label_keys": sorted(fv.ORACLE_LABEL_KEYS),
        "oracle": {
            "name": engine.name,
            "version": engine.version,
            "type": engine.oracle_type,
            "implementation": engine.implementation,
            "authority": engine.authority,
            "meters": {"clock": engine.meter_clock, "state": engine.meter_state, "thermal": engine.meter_thermal},
        },
        "generator": {"name": fv.GENERATOR_NAME, "version": fv.GENERATOR_VERSION, "kind": fv.GENERATOR_KIND},
        "default_system": fv.default_system(),
        "parameter_spec": {
            kind: {"required": list(required), "optional": list(optional)}
            for kind, (required, optional) in fv.PARAMETER_SPEC.items()
        },
        "hardware_replay": (
            "not available in this environment; a replay oracle implements FaultOracle "
            "and declares its own meters"
        ),
    }


__all__ = (
    "EMITTED_LABEL_KEYS", "FaultOracle", "FaultResult", "ORACLE_LABEL_KEYS", "OracleMeters",
    "RelayReflexSimulator", "build_records", "describe", "oracle_meters", "oracle_result",
    "prediction_agreement", "propose_scenarios", "result_measurements",
)

bind_import_twin(__name__)
