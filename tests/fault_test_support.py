#!/usr/bin/env python3
"""Shared surface for the ``test_fault_*`` modules (issue #191, F1).

The contract facade and the five fault modules under the flat spelling,
scenario and disturbance factories, a ``run()`` shortcut, the pinned
timestamp, the coded-refusal assertion, a policy guard and a memoised
record corpus -- carried once so the direct test modules stay small and
qlty's duplication smells stay silent.
"""

import copy
import functools
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from coded_refusal_test_support import coded_refusal
from distill_contract_test_support import REPO, envelope, oc
from oracle_grounded import fault_config, fault_oracle, fault_scenario, fault_simulator, fault_vocabulary

PINNED_AT = "2026-08-23T00:00:00.000Z"
SEED = 20260823
FAULT_MODULES = ("fault_vocabulary", "fault_config", "fault_scenario", "fault_simulator", "fault_oracle")

__all__ = (
    "FAULT_MODULES", "PINNED_AT", "REPO", "SEED", "contract_findings", "disturbance",
    "ensure_policy", "envelope", "fault_config", "fault_oracle", "fault_scenario",
    "fault_simulator", "fault_vocabulary", "oc", "records", "refusal", "run", "scenario",
)


def scenario(**system_overrides):
    """A full scenario over ``default_system()`` with the given controls replaced."""

    system = fault_vocabulary.default_system()
    system.update(system_overrides)
    return {"system": system, "mission": fault_vocabulary.MISSION, "disturbance_kind": "sensor_loss"}


def disturbance(kind, **parameters):
    return {"kind": kind, "parameters": parameters}


def run(kind, system=None, **parameters):
    """One verdict from a fresh simulator over deep-copied input."""

    engine = fault_simulator.RelayReflexSimulator()
    proposal = scenario(**(system or {}))
    proposal["disturbance_kind"] = kind
    return engine.run(copy.deepcopy(proposal), copy.deepcopy(disturbance(kind, **parameters)))


def refusal(case, code, *fragments):
    """Assert a ``FaultRefusal`` carrying exactly ``code`` and every prose fragment."""

    return coded_refusal(
        case, fault_vocabulary.FaultRefusal, fault_vocabulary.FINDING_CODE_SET,
        fault_vocabulary.REASON_CODE_SET, code, *fragments,
    )


def ensure_policy():
    """Re-declare the family's policy (idempotent) for tests that run the leak check."""

    oc.declare_oracle_labels(fault_vocabulary.FAMILY, fault_vocabulary.ORACLE_LABEL_KEYS)


@functools.lru_cache(maxsize=None)
def records(seed=SEED, count=36, produced_at=PINNED_AT):
    """A memoised record corpus; callers deep-copy before tampering."""

    return fault_oracle.build_records(seed, count, produced_at=produced_at)


def contract_findings(record):
    """Every contract check the family's records must pass with nothing to report."""

    where = record.get("id", "record")
    return (
        oc.check_envelope(record, where)
        + oc.check_digest(record, where)
        + oc.check_measurements(record, where)
        + oc.check_no_theoretical_energy_claim(record, where)
        + oc.check_oracle_label_leak(record, where)
    )
