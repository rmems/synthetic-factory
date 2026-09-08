#!/usr/bin/env python3
"""Record assembly of the fault-recovery family through the merged contract (F1).

The agent's single import::

    from oracle_grounded import fault_oracle as fo
    records = fo.build_records(20260823, 9, produced_at="2026-08-23T00:00:00.000Z")
    oc.write_jsonl(new_path, records)

Every record is UNVALIDATED: nothing here self-certifies. The oracle's meters
name the instruments behind the seven readings, the result block emits every
declared oracle-label key (``EMITTED_LABEL_KEYS == ORACLE_LABEL_KEYS``; the
``continue`` shape is ``detection_latency_ms: null`` with no detection
reading), counts stay genuine integers, and ``produced_at`` is injectable so
two builds with the same seed and timestamp are byte-identical. An injected
oracle sees private copies of the proposal and its verdict passes
:func:`checked_result`. ``__all__`` is the agent surface; the emitters below
it take checked inputs and are importable by name.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any

from . import distill_blocks as blocks
from . import distill_builders as builders
from . import distill_vocabulary as vocab
from . import envelope
from . import fault_config as config
from . import fault_scenario as scenario
from . import fault_simulator as simulator
from . import fault_vocabulary as fv
from .import_twins import bind_import_twin

FaultOracle = simulator.FaultOracle
FaultResult = simulator.FaultResult
RelayReflexSimulator = simulator.RelayReflexSimulator
propose_scenarios = scenario.propose_scenarios
checked_system = config.checked_system
checked_disturbance = config.checked_disturbance
ORACLE_LABEL_KEYS = fv.ORACLE_LABEL_KEYS


@dataclass(frozen=True)
class OracleMeters:
    """The instruments an oracle declares behind its clock, state and thermal
    readings, and which of those roles model rather than measure."""

    clock: str
    state: str
    thermal: str
    modeled: frozenset[str] = frozenset()

    def of(self, role: str) -> str:
        return getattr(self, role)

    def measured(self, role: str) -> bool:
        return role not in self.modeled


def _fault_oracle(engine: Any) -> simulator.FaultOracle:
    """The engine itself, or a coded refusal when it is not a ``FaultOracle``."""
    fv.refuse_when(
        not isinstance(engine, simulator.FaultOracle),
        fv.FINDING_INPUT_NOT_AN_OBJECT,
        f"oracle must implement FaultOracle, got {fv.shown(engine)}",
    )
    return engine


METER_ROLES = ("clock", "state", "thermal")


def oracle_meters(engine: Any) -> OracleMeters:
    """The engine's declared meters; refused when the engine is not a
    ``FaultOracle`` or any role is unset, so an injected non-simulator oracle
    can never inherit ``simulator_*`` provenance."""
    engine = _fault_oracle(engine)
    meters = OracleMeters(
        engine.meter_clock, engine.meter_state, engine.meter_thermal, frozenset(engine.modeled_roles)
    )
    unset = sorted(role for role in METER_ROLES if vocab.missing_string(meters.of(role)))
    fv.refuse_when(
        bool(unset),
        fv.FINDING_ORACLE_METERS_UNDECLARED,
        f"oracle {engine.name!r} does not declare its measurement meters ({unset}); "
        "readings cannot be attributed to an unnamed instrument",
    )
    return meters


def oracle_run_of(engine: Any) -> str:
    """The engine's declared run descriptor for ``provenance.oracle_run``; refused
    when the engine is not a ``FaultOracle`` or the descriptor is unset, so a
    hardware replay or recorded measurement is never stamped as the simulator's
    in-process deterministic run."""
    engine = _fault_oracle(engine)
    fv.refuse_when(
        vocab.missing_string(engine.oracle_run),
        fv.FINDING_ORACLE_RUN_UNDECLARED,
        f"oracle {engine.name!r} does not declare oracle_run; provenance cannot describe "
        "how its results are produced",
    )
    return engine.oracle_run


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
    result: simulator.FaultResult, intervention: dict[str, Any], meters: OracleMeters
) -> list[dict[str, Any]]:
    """The metered readings of a checked result and intervention; detection
    first, only when detected."""
    params = intervention["parameters"]
    readings = [
        builders.new_measurement(
            quantity, value_of(result), meters.of(role),
            detail=_detail(quantity, params), measured=meters.measured(role),
        )
        for quantity, role, value_of in _READINGS
    ]
    if result.detection_latency_ms is not None:
        detection = builders.new_measurement(
            "detection_latency_ms", result.detection_latency_ms, meters.clock, measured=meters.measured("clock")
        )
        readings.insert(0, detection)
    return readings


# result key -> FaultResult attribute, for the result-level labels beside
# ``outcome_label``, ``prediction_agreement`` and ``trace_summary``.
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
# Every label key a result block carries, computed from the emitter's own
# tables; ``fault_vocabulary.ORACLE_LABEL_KEYS`` is asserted equal to it.
EMITTED_LABEL_KEYS = (
    frozenset(key for key, _ in _LABEL_FIELDS)
    | frozenset({"outcome_label", "prediction_agreement", "trace_summary"})
    | frozenset(_TRACE_FIELDS)
)


def _labels(result: simulator.FaultResult) -> dict[str, Any]:
    """The result-level label values plus the trace summary."""
    labels: dict[str, Any] = {key: getattr(result, attr) for key, attr in _LABEL_FIELDS}
    labels["reason_codes"] = list(result.reason_codes)
    labels["outcome_label"] = fv.OUTCOME_LABELS[result.outcome]
    labels["trace_summary"] = {name: getattr(result, name) for name in _TRACE_FIELDS}
    return labels


def prediction_agreement(prediction: dict[str, Any], outcome: str) -> str:
    """``agree`` when a checked proposal's ``candidate_prediction`` named the outcome."""
    return "agree" if prediction.get("predicted_outcome") == outcome else "disagree"


def oracle_result(
    result: simulator.FaultResult,
    prediction: dict[str, Any],
    intervention: dict[str, Any],
    meters: OracleMeters,
) -> dict[str, Any]:
    """The oracle-owned result block for one checked result and proposal."""
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
        f"produced_at must be an ISO-8601 UTC instant, got {fv.shown(value)}",
    )
    return value


@dataclass(frozen=True)
class _Batch:
    """What every record of one build shares."""

    engine: simulator.FaultOracle
    meters: OracleMeters
    generator: dict[str, Any]
    provenance: dict[str, Any]
    seed: int


def _verdict(batch: _Batch, proposal: dict[str, Any]) -> builders.Verdict:
    """The oracle runs on private copies of the proposal, so an engine that
    rewrites its input cannot launder the generator's sections; its result
    must sit inside the family vocabulary."""
    scenario_block = copy.deepcopy(proposal["scenario"])
    intervention = copy.deepcopy(proposal["intervention"])
    system = config.checked_system(proposal["scenario"])
    result = simulator.checked_result(batch.engine.run(scenario_block, intervention), system)
    return builders.Verdict(
        oracle=batch.engine.oracle_block(copy.deepcopy(proposal["scenario"])),
        result=oracle_result(result, proposal["candidate_prediction"], proposal["intervention"], batch.meters),
    )


def _record(batch: _Batch, proposal: dict[str, Any]) -> dict[str, Any]:
    """One built record, refused if the shared envelope would refuse it.

    The simulator's records pass by construction; the check is what keeps an
    injected oracle's block or verdict from reaching a file already known to
    fail validation. No validation stamp is written: the record stays
    unvalidated.
    """
    record_id = f"{fv.RECORD_ID_PREFIX}-{batch.seed}-{proposal['index']:04d}"
    record = builders.build_record(
        identity=builders.RecordIdentity(record_id, fv.FAMILY),
        proposal=builders.Proposal(
            generator=batch.generator,
            scenario=proposal["scenario"],
            intervention=proposal["intervention"],
            candidate_prediction=proposal["candidate_prediction"],
        ),
        verdict=_verdict(batch, proposal),
        provenance=batch.provenance,
    )
    findings = blocks.check_envelope(record, record_id)
    fv.refuse_when(
        bool(findings),
        fv.FINDING_RECORD_FAILS_ENVELOPE,
        f"the oracle {batch.engine.name!r} produced a record the shared envelope refuses "
        f"({len(findings)} finding(s); first: {findings[0] if findings else ''})",
    )
    return record


def build_records(
    seed: int,
    count: int,
    *,
    produced_at: str | None = None,
    oracle: simulator.FaultOracle | None = None,
) -> list[dict[str, Any]]:
    """Run every proposed disturbance through the oracle into UNVALIDATED records.

    Ids are ``fr-{seed}-{index:04d}``. ``produced_at`` pins the provenance
    timestamp (validated as an ISO-8601 UTC instant); omitted, one
    ``utc_now_iso()`` serves the whole batch. ``oracle`` defaults to the
    simulator and must implement ``FaultOracle`` and declare its meters and
    its ``oracle_run`` (stamped into every record's provenance). The
    cheap refusals run before a single proposal is drawn, and ``count`` is
    bounded by ``MAX_COUNT``.
    """
    stamp = _produced_at(produced_at)
    engine = simulator.RelayReflexSimulator() if oracle is None else oracle
    meters = oracle_meters(engine)
    oracle_run = oracle_run_of(engine)
    proposals = scenario.propose_scenarios(seed, count)
    provenance = builders.new_provenance(fv.PRODUCER, produced_at=stamp, oracle_run=oracle_run)
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
            "modeled_roles": sorted(engine.modeled_roles),
            "run": engine.oracle_run,
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


# The agent surface: every name refuses malformed input with a coded
# ``FaultRefusal``. The lower-level emitters take checked inputs.
__all__ = (
    "EMITTED_LABEL_KEYS", "FaultOracle", "FaultResult", "ORACLE_LABEL_KEYS", "OracleMeters",
    "RelayReflexSimulator", "build_records", "checked_disturbance", "checked_system", "describe",
    "oracle_meters", "oracle_run_of", "propose_scenarios",
)

bind_import_twin(__name__)
