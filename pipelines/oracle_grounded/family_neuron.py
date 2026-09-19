"""Neuron counterfactual family wiring and invariant checks."""

import math
from dataclasses import dataclass
from itertools import pairwise

from . import canon, generators, oracles, sim
from .family_common import DIMENSIONLESS, RATE_UNITS, ROUNDING_TOL, TIME_UNITS
from .family_common import _measurement_matches

# --------------------------------------------------------------------------
# Family 2: neuron-dynamics-counterfactuals  (oracle: neuromod)
# --------------------------------------------------------------------------

MEMBRANE_UNITS = "normalized membrane units (v_threshold = 1)"

NEURON_UNITS = {
    "spike_times_ms": TIME_UNITS,
    "first_spike_ms": TIME_UNITS,
    "last_spike_ms": TIME_UNITS,
    "mean_isi_ms": TIME_UNITS,
    "mean_rate_hz": RATE_UNITS,
    "cv_isi": DIMENSIONLESS,
    "adaptation_index": "dimensionless, last ISI / first ISI",
    "v_mean": MEMBRANE_UNITS,
    "v_max": MEMBRANE_UNITS,
    "v_min": MEMBRANE_UNITS,
    "v_trace": "normalized membrane units, sampled every v_trace_stride_ms",
    "v_trace_stride_ms": TIME_UNITS,
    "duration_ms": TIME_UNITS,
    "spike_count_delta": "spikes",
    "first_spike_shift_ms": TIME_UNITS,
}


def _intervened_parameters(baseline, intervention):
    """Apply the proposed intervention to the neuron configuration."""
    parameter = intervention["parameter"]
    updated = dict(baseline)
    if intervention["operation"] != "scale":
        raise ValueError(f"unsupported neuron intervention: {intervention['operation']}")
    updated[parameter] = (
        baseline.get(parameter, sim.NEURON_DEFAULTS[parameter]) * intervention["factor"]
    )
    return updated


def neuron_request(scenario, intervention):
    before = sim.neuron_config(scenario["baseline_parameters"])
    before["dt_ms"] = scenario["dt_ms"]
    after = _intervened_parameters(before, intervention)
    return {
        "configuration": {
            "before": before,
            "after": after,
            "intervened_parameter": intervention["parameter"],
            "trace_points": 48,
        },
        "data": {"current": generators.build_current(scenario)},
    }


def _neuron_reference(request):
    config = request["configuration"]
    current = request["data"]["current"]
    points = config["trace_points"]
    before = sim.simulate_neuron(config["before"], current, trace_points=points)
    after = sim.simulate_neuron(config["after"], current, trace_points=points)
    measured = {
        "before": before,
        "after": after,
        "delta": sim.compare_neuron_states(before, after),
    }
    return measured, NEURON_UNITS


def _neuron_oracle(environ=None):
    return oracles.bind(
        runtime="neuromod",
        identity=oracles.OracleIdentity(
            oracle_id="lif-ref",
            oracle_type="neuron-simulation",
            description=(
                "Adaptive leaky integrate-and-fire neuron with neuromodulatory gain and "
                "threshold shift, standing in for the neuromod simulation"
            ),
        ),
        reference_fn=_neuron_reference,
        environ=environ,
    )


def _neuron_propose(rng):
    scenario = generators.propose_neuron_scenario(rng)
    intervention = generators.propose_neuron_intervention(rng)
    return scenario, intervention, generators.predict_neuron_effect(intervention)


def _finite_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _neuron_delta_findings(measured):
    expected_delta = sim.compare_neuron_states(measured["before"], measured["after"])
    findings = []
    for field, expected in expected_delta.items():
        if not _measurement_matches(measured["delta"].get(field), expected):
            findings.append(
                f"delta.{field} does not match the value derived from before/after states"
            )
    return findings


def _neuron_reference_findings(record):
    if record["oracle"]["implementation"] == "named-runtime":
        return []
    measured = record["result"]["measured"]
    rerun_request = neuron_request(record["scenario"], record["intervention"])
    recomputed, _units = _neuron_reference(rerun_request)
    return [
        f"{side} does not match the rerun of the reference simulation"
        for side in ("before", "after")
        if canon.normalize(measured[side]) != canon.normalize(recomputed[side])
    ]


@dataclass(frozen=True)
class _NeuronTrial:
    """Scenario-derived trial geometry shared by the per-side checks."""

    record: dict
    steps: int
    duration_ms: float


def _neuron_summary_findings(trial, side, state):
    times = state["spike_times_ms"]
    findings = _neuron_spike_event_findings(side, times, trial.duration_ms)
    intervals = [later - earlier for earlier, later in pairwise(times)]
    mean_isi = sum(intervals) / len(intervals) if intervals else None
    expected = _neuron_expected_summary(times, intervals, mean_isi, trial.duration_ms)
    stride = max(
        1, math.ceil(trial.steps / trial.record["oracle"]["configuration"]["trace_points"])
    )
    expected["v_trace_stride_ms"] = stride * trial.record["scenario"]["dt_ms"]
    for field, value in expected.items():
        if not _measurement_matches(state.get(field), value):
            findings.append(
                f"{side}.{field} does not match the summary derived from "
                "spike_times_ms and the retained duration"
            )
    expected_trace_points = math.ceil(trial.steps / stride) if trial.steps else 0
    trace_length_valid = len(state["v_trace"]) == expected_trace_points
    if not trace_length_valid:
        findings.append(f"{side}.v_trace length does not match v_trace_stride_ms and duration_ms")
    return findings, trace_length_valid


def _neuron_spike_event_findings(side, times, duration_ms):
    findings = []
    if any(later < earlier for earlier, later in pairwise(times)):
        findings.append(f"{side}.spike_times_ms is not non-decreasing")
    if any(time_ms < 0 or time_ms >= duration_ms for time_ms in times):
        findings.append(f"{side}.spike_times_ms contains an event outside the simulated duration")
    return findings


def _isi_cv(intervals, mean_isi):
    if len(intervals) <= 1 or not mean_isi:
        return None
    variance = sum((item - mean_isi) ** 2 for item in intervals) / len(intervals)
    return math.sqrt(variance) / mean_isi


def _isi_adaptation(intervals):
    if len(intervals) < 2 or not intervals[0]:
        return None
    return intervals[-1] / intervals[0]


def _neuron_expected_summary(times, intervals, mean_isi, duration_ms):
    return {
        "spike_count": len(times),
        "first_spike_ms": times[0] if times else None,
        "last_spike_ms": times[-1] if times else None,
        "mean_rate_hz": len(times) / (duration_ms / 1000.0) if duration_ms else 0.0,
        "mean_isi_ms": mean_isi,
        "cv_isi": _isi_cv(intervals, mean_isi),
        "adaptation_index": _isi_adaptation(intervals),
        "duration_ms": duration_ms,
    }


def _v_bound_findings(side, v_min, v_max, v_mean):
    if not (_finite_number(v_min) and _finite_number(v_max)):
        return []
    findings = []
    if v_min > v_max:
        findings.append(f"{side}.v_min is greater than v_max")
    if _finite_number(v_mean) and not (v_min - ROUNDING_TOL <= v_mean <= v_max + ROUNDING_TOL):
        findings.append(f"{side}.v_mean does not lie between v_min and v_max")
    return findings


def _trace_sample_findings(side, position, sample, bounds):
    v_min, v_max = bounds
    if not _finite_number(sample):
        return [f"{side}.v_trace[{position}] is not numeric"]
    findings = []
    if _finite_number(v_min) and sample < v_min - ROUNDING_TOL:
        findings.append(f"{side}.v_trace[{position}] is below the recorded v_min")
    if _finite_number(v_max) and sample > v_max + ROUNDING_TOL:
        findings.append(f"{side}.v_trace[{position}] is above the recorded v_max")
    return findings


def _neuron_voltage_findings(side, state):
    bounds = (state.get("v_min"), state.get("v_max"))
    findings = _v_bound_findings(side, bounds[0], bounds[1], state.get("v_mean"))
    for position, sample in enumerate(state["v_trace"]):
        findings.extend(_trace_sample_findings(side, position, sample, bounds))
    return findings


def _neuron_state_findings(trial, side, state):
    findings, trace_length_valid = _neuron_summary_findings(trial, side, state)
    if trace_length_valid:
        findings.extend(_neuron_voltage_findings(side, state))
    return findings


def _neuron_intervention_findings(record):
    configuration = record["oracle"]["configuration"]
    parameter = configuration["intervened_parameter"]
    expected_parameter = sim.INTERVENTION_TARGETS[record["intervention"]["target"]]
    findings = []
    if record["intervention"]["parameter"] != expected_parameter:
        findings.append("intervention.parameter does not match intervention.target")
    changed = [
        key
        for key in configuration["before"]
        if configuration["before"][key] != configuration["after"].get(key)
    ]
    if changed != [parameter]:
        findings.append(f"intervention should change exactly {parameter!r}, but changed {changed}")
    return findings


def _neuron_checks(record):
    measured = record["result"]["measured"]
    steps = generators.neuron_sample_count(record["scenario"])
    trial = _NeuronTrial(record, steps, steps * record["scenario"]["dt_ms"])
    findings = _neuron_delta_findings(measured)
    findings.extend(_neuron_reference_findings(record))
    for side in ("before", "after"):
        findings.extend(_neuron_state_findings(trial, side, measured[side]))
    findings.extend(_neuron_intervention_findings(record))
    return findings
