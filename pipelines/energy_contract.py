#!/usr/bin/env python3
"""Shared constants and predicates for ``snn-energy-routing-preferences``.

Split out of ``energy_preferences.py`` verbatim: the family identity, the
decision rule and safety envelope, the oracle-label policy, and the replay
ceilings that generator and validator both enforce. Every name here is
re-exported from ``energy_preferences`` so existing call sites resolve
unchanged.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from oracle_grounded import distill_contract as oc  # noqa: E402


FAMILY = "snn-energy-routing-preferences"
GENERATOR_NAME = "equivalent-policy-generator"
GENERATOR_VERSION = "1.0.0"


DECISION_RULE = "min_measured_cost_subject_to_quality_and_safety"

# The policy implementations a workload key names. Bump this whenever a
# policy's algorithm changes: a recorded cost is only valid for the workload
# it was taken over, and a silently different implementation under the same
# key would attach an old reading to a new workload.
POLICY_SUITE_VERSION = "1.0.0"

DEFAULT_FINE_STEPS = 48
DEFAULT_COARSE_STEPS = 8

ABSTAIN_NO_FEASIBLE = "NO_CANDIDATE_SATISFIES_QUALITY_AND_SAFETY_CONSTRAINTS"
ABSTAIN_NO_MEASUREMENT = "NO_MEASURED_COST_AVAILABLE"

# The one safety envelope this family's oracle enforces. Validated verbatim:
# a scenario describing a different rule to the student than the one the
# labels were derived under would pair one decision rule's description with
# another's outcomes.
PREFERENCE_OBJECTIVE = "minimise measured cost subject to quality and safety"
SAFETY_ENVELOPE = "0 <= x_i <= cap_i and sum(x_i) == demand"

# The costs this family's decision rule may minimise: measured joules, or the
# documented CPU-time fallback. Any other registered quantity (a latency, a
# temperature) is a different optimisation wearing this family's name.
SUPPORTED_COST_QUANTITIES = frozenset({"energy_j", "cpu_time_s"})

# Oracle-label policy (D2): the preference keys only this family's oracle may
# write. Any of them inside a generator-owned section is a label leak.
ORACLE_LABEL_POLICY = oc.declare_oracle_labels(
    FAMILY,
    {
        "preference",
        "preferred",
        "over",
        "feasible",
        "cheaper_but_constraint_violating",
        "decision_rule",
        "cost_value",
        "cost_quantity",
        "cost_is_energy",
        "meter_probe",
        "reference_objective",
        "abstain_reason",
    },
)


# Solver-step ceiling for replaying a recorded grid search. The validator
# replays untrusted scenarios, and the grid walk visits O(steps^3)
# allocations of the four-actuator task, so an unbounded recorded resolution
# would let one record buy an arbitrarily large replay. The builder defaults
# are 48 and 8.
MAX_REPLAY_STEPS = 128
MAX_ACTUATORS = 4


# The oracle type each of this module's meter implementations produces. A
# live meter measures during the run; a replay meter hands back a cost that
# was recorded elsewhere — stamping the wrong type erases that distinction.
_ORACLE_TYPE_BY_IMPLEMENTATION = {
    "pipelines/energy_preferences.py:ProcessResourceMeter": "measured_execution",
    "pipelines/energy_preferences.py:RaplEnergyMeter": "measured_execution",
    "pipelines/energy_preferences.py:RecordedEnergyMeter": "recorded_measurement",
}


def _genuine_int_at_least(value: Any, floor: int) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= floor


QUALITY_TOLERANCE = 2e-6

