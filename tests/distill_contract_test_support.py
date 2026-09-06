#!/usr/bin/env python3
"""Shared surface for the distillation-contract test modules.

The direct tests of ``pipelines/oracle_grounded/distill_*`` are split by
responsibility -- ``test_distill_envelope`` (the record blocks, builders and
the generator/oracle separation), ``test_distill_measurements`` (measurement
checks and the energy-claim scan), ``test_distill_labels`` (family-owned
oracle-label policies), ``test_distill_jsonl`` (JSONL I/O),
``test_distill_curation`` (stamps and the curation gate) and
``test_distill_contract`` (the facade, the schema and the import forms). This
module carries what they share once: the ``sys.path`` bootstrap, the contract
and envelope imports, the minimal record every module tampers with, and the
fixtures the energy and label tests reuse.

Test discovery runs with ``-s tests``, so the modules import this one by its
bare name, the same way the other ``*_test_support`` modules are reached.
"""

import copy
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

from oracle_grounded import distill_contract as oc  # noqa: E402
from oracle_grounded import envelope  # noqa: E402

SCHEMA_PATH = REPO / "schemas" / "oracle-grounded-record.schema.json"

ENERGY_LABELS = frozenset(
    {"preferred", "feasible", "over", "cost_value", "decision_rule",
     "cheaper_but_constraint_violating"}
)
FAULT_LABELS = frozenset({"trace_summary", "max_staleness_ms", "saturated_ticks"})

__all__ = [
    "ENERGY_LABELS",
    "FAULT_LABELS",
    "REPO",
    "SCHEMA_PATH",
    "envelope",
    "measured_energy_reading",
    "minimal_record",
    "oc",
]


def minimal_record(**overrides):
    record = oc.build_record(
        identity=oc.RecordIdentity("rec-1", "neuromorphic-fault-recovery"),
        proposal=oc.Proposal(
            generator=oc.new_generator(oc.GeneratorIdentity("gen", version="1.0.0"), seed=3),
            scenario={"mission": "bounded fixture"},
            intervention={"kind": "sensor_loss", "parameters": {"channels": ["c0"]}},
            candidate_prediction={"predicted_outcome": "fallback", "confidence": 0.5},
        ),
        verdict=oc.Verdict(
            oracle=oc.new_oracle(
                oc.OracleIdentity(
                    "sim",
                    oracle_type="deterministic_simulator",
                    implementation="pipelines/fault_recovery.py:RelayReflexSimulator",
                    version="1.0.0",
                )
            ),
            result=oc.new_result(
                measurements=[
                    oc.new_measurement("recovery_latency_ms", 4.0, "simulator_clock")
                ],
                outcome="fallback",
                reason_codes=["FALLBACK_SOURCE_ENGAGED"],
            ),
        ),
        provenance=oc.new_provenance("unit-test"),
    )
    record.update(copy.deepcopy(overrides))
    return record


def measured_energy_reading(value: float = 8.0) -> dict:
    return oc.new_measurement("energy_j", value, "intel_rapl_powercap")
