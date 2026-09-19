"""Temporal-memory family wiring and invariant checks."""

import sys

from . import generators, oracles, sim
from .family_memory_checks import MemoryChecks
from .family_common import ENERGY_UNITS, TIME_UNITS

# --------------------------------------------------------------------------
# Family 5: temporal-memory-spike-challenges  (oracle: recurrent SNN)
# --------------------------------------------------------------------------

MEMORY_UNITS = {
    "response": "output identity: A, B, or none",
    "response_latency_ms": TIME_UNITS,
    "output_spike_counts": "spikes",
    "memory_spike_counts": "spikes",
    "latch_last_spike_ms": TIME_UNITS,
    "duration_ms": TIME_UNITS,
    "energy_pJ": ENERGY_UNITS,
    "retention_horizon_ms": TIME_UNITS,
}

# How far a distractor is displaced when testing distractor invariance.
DISTRACTOR_SHIFT_MS = 7.0


def _memory_ablation_changed(baseline, trial):
    """True when an ablation changes the categorical response or latch state.

    A forgotten cue can leave both trials at ``response='none'`` while the
    retained latch still disagrees. Categorical equality alone would hide
    that temporal effect; identical none/none with identical latch state
    remains a measured forgetting case and is not dependence.
    """
    return (
        trial.get("response") != baseline.get("response")
        or bool(trial.get("state_retained_at_probe"))
        != bool(baseline.get("state_retained_at_probe"))
    )


def memory_request(scenario, intervention):
    del intervention
    config = sim.memory_config(scenario["network_variant"])
    return {
        "configuration": config,
        "data": {
            "task": {
                "cue": scenario["cue"],
                "cue_ms": scenario["cue_ms"],
                "probe_ms": scenario["probe_ms"],
                "distractor_ms": list(scenario["distractor_ms"]),
                "reset_ms": scenario["reset_ms"],
            }
        },
    }


def _shift_distractors(task):
    """Move every distractor later, keeping it strictly inside the delay."""
    limit = task["probe_ms"] - 5.0
    shifted = []
    for time_ms in task["distractor_ms"]:
        moved = time_ms + DISTRACTOR_SHIFT_MS
        if moved >= limit:
            moved = max(task["cue_ms"] + 5.0, time_ms - DISTRACTOR_SHIFT_MS)
        shifted.append(moved)
    return sorted(shifted)


def _memory_trial_task(scenario, name):
    """Rebuild the stored trial that produced one baseline or control measurement."""
    task = {
        "cue": scenario["cue"],
        "cue_ms": scenario["cue_ms"],
        "probe_ms": scenario["probe_ms"],
        "distractor_ms": list(scenario["distractor_ms"]),
        "reset_ms": scenario["reset_ms"],
    }
    if name == "baseline":
        return task
    if name == "cue_ablation":
        return dict(task, cue=None)
    if name == "reset_ablation":
        return dict(task, reset_ms=None)
    if name == "distractor_swap":
        return dict(task, distractor_ms=_shift_distractors(task))
    return None


def _memory_reference(request):
    config = request["configuration"]
    task = request["data"]["task"]
    baseline = sim.run_memory_task(task, config)

    probes = {}
    ablated = dict(task, cue=None)
    probes["cue_ablation"] = sim.run_memory_task(ablated, config)
    if task.get("reset_ms") is not None:
        no_reset = dict(task, reset_ms=None)
        probes["reset_ablation"] = sim.run_memory_task(no_reset, config)
    if task["distractor_ms"]:
        swapped = dict(task, distractor_ms=_shift_distractors(task))
        probes["distractor_swap"] = sim.run_memory_task(swapped, config)

    differing = sorted(
        name
        for name, result in probes.items()
        if name != "distractor_swap" and _memory_ablation_changed(baseline, result)
    )
    measured = {
        "baseline": baseline,
        "probes": probes,
        "temporal_dependence": {
            "demonstrated": bool(differing),
            "changed_by": differing,
            "method": (
                "re-ran the same network with the cue removed (and, when present, "
                "with the reset removed); a record counts as temporally dependent "
                "only if that changes the measured response or retained latch state"
            ),
        },
        "distractor_invariant": (
            probes["distractor_swap"]["response"] == baseline["response"]
            if "distractor_swap" in probes
            else None
        ),
        "delay_ms": task["probe_ms"] - task["cue_ms"],
    }
    return measured, MEMORY_UNITS


def _memory_oracle(environ=None):
    return oracles.bind(
        runtime="recurrent-snn",
        identity=oracles.OracleIdentity(
            oracle_id="rsnn-ref",
            oracle_type="recurrent-snn",
            description=(
                "Two mutually inhibiting delay loops read out through a probe gate; "
                "retention is limited by the loops' own spike-frequency adaptation"
            ),
        ),
        reference_fn=_memory_reference,
        environ=environ,
    )


def _memory_propose(rng):
    scenario = generators.propose_memory_scenario(rng)
    return scenario, None, generators.predict_memory_response(scenario)



















_FAMILY_MEMORY_CHECKS = MemoryChecks(sys.modules[__name__])
_memory_accounting_findings = _FAMILY_MEMORY_CHECKS._memory_accounting_findings
_memory_checks = _FAMILY_MEMORY_CHECKS._memory_checks
_memory_control_findings = _FAMILY_MEMORY_CHECKS._memory_control_findings
_memory_replay_findings = _FAMILY_MEMORY_CHECKS._memory_replay_findings
_memory_response_findings = _FAMILY_MEMORY_CHECKS._memory_response_findings
_memory_scenario_findings = _FAMILY_MEMORY_CHECKS._memory_scenario_findings
_memory_shape_findings = _FAMILY_MEMORY_CHECKS._memory_shape_findings
_memory_trial_findings = _FAMILY_MEMORY_CHECKS._memory_trial_findings
