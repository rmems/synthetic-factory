"""Family 2: neuron-dynamics-counterfactuals  (oracle: neuromod).

The same input current is played through a neuron before and after one
parameter intervention; the record keeps both spike summaries, the retained
voltage trace, and the delta between them. The checks re-derive every summary
statistic from the stored spike times, and a reference record is additionally
authenticated by re-running the reference simulation.
"""

import math
from itertools import pairwise

from . import canon, generators, oracles, sim
from .family_common import (
    DIMENSIONLESS,
    RATE_UNITS,
    ROUNDING_TOL,
    TIME_UNITS,
    _guess,
    _measurement_matches,
)

NEURON_UNITS = {
    "spike_times_ms": TIME_UNITS,
    "first_spike_ms": TIME_UNITS,
    "last_spike_ms": TIME_UNITS,
    "mean_isi_ms": TIME_UNITS,
    "mean_rate_hz": RATE_UNITS,
    "cv_isi": DIMENSIONLESS,
    "adaptation_index": "dimensionless, last ISI / first ISI",
    "v_mean": "normalized membrane units (v_threshold = 1)",
    "v_max": "normalized membrane units (v_threshold = 1)",
    "v_min": "normalized membrane units (v_threshold = 1)",
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
    intervention = generators.propose_neuron_intervention(rng, scenario)
    return scenario, intervention, generators.predict_neuron_effect(scenario, intervention)


def _neuron_window(record):
    """(steps, duration_ms) of the simulation the scenario describes."""
    steps = generators.neuron_sample_count(record["scenario"])
    return steps, steps * record["scenario"]["dt_ms"]


def _finite_voltage(value):
    """A retained voltage statistic that is a real, finite number."""
    if isinstance(value, bool):
        return False
    return isinstance(value, (int, float)) and math.isfinite(value)


def _neuron_delta_findings(measured, findings):
    expected_delta = sim.compare_neuron_states(measured["before"], measured["after"])
    for field, expected in expected_delta.items():
        if not _measurement_matches(measured["delta"].get(field), expected):
            findings.append(
                f"delta.{field} does not match the value derived from before/after states"
            )


def _neuron_rerun_findings(record, measured, findings):
    """Authenticate a reference record against a re-run of the reference.

    The per-field checks only require each retained trace sample to fall
    within its own retained extrema -- a fully forged but internally
    consistent trace would pass. A reference record's before/after states are
    reproducible from oracle.configuration alone, so rerun the reference and
    compare directly. Named-runtime results are authenticated through their
    own reproduction path instead.
    """
    rerun_request = neuron_request(record["scenario"], record["intervention"])
    recomputed, _units = _neuron_reference(rerun_request)
    for side in ("before", "after"):
        if canon.normalize(measured[side]) != canon.normalize(recomputed[side]):
            findings.append(f"{side} does not match the rerun of the reference simulation")


def _neuron_cv_isi(intervals, mean_isi):
    if len(intervals) > 1 and mean_isi:
        variance = sum((item - mean_isi) ** 2 for item in intervals) / len(intervals)
        return math.sqrt(variance) / mean_isi
    return None


def _neuron_expected_summary(times, duration_ms):
    """The summary statistics the stored spike times dictate."""
    intervals = [later - earlier for earlier, later in pairwise(times)]
    mean_isi = sum(intervals) / len(intervals) if intervals else None
    return {
        "spike_count": len(times),
        "first_spike_ms": times[0] if times else None,
        "last_spike_ms": times[-1] if times else None,
        "mean_rate_hz": len(times) / (duration_ms / 1000.0) if duration_ms else 0.0,
        "mean_isi_ms": mean_isi,
        "cv_isi": _neuron_cv_isi(intervals, mean_isi),
        "adaptation_index": (
            intervals[-1] / intervals[0] if len(intervals) >= 2 and intervals[0] else None
        ),
        "duration_ms": duration_ms,
    }


def _neuron_summary_findings(record, side, state, findings):
    steps, duration_ms = _neuron_window(record)
    expected = _neuron_expected_summary(state["spike_times_ms"], duration_ms)
    stride = max(
        1,
        math.ceil(steps / record["oracle"]["configuration"]["trace_points"]),
    )
    expected["v_trace_stride_ms"] = stride * record["scenario"]["dt_ms"]
    for field, value in expected.items():
        if not _measurement_matches(state.get(field), value):
            findings.append(
                f"{side}.{field} does not match the summary derived from "
                "spike_times_ms and the retained duration"
            )
    expected_trace_points = math.ceil(steps / stride) if steps else 0
    if len(state["v_trace"]) != expected_trace_points:
        findings.append(
            f"{side}.v_trace length does not match v_trace_stride_ms and duration_ms"
        )


def _within_recorded_bounds(value, low, high):
    return low - ROUNDING_TOL <= value <= high + ROUNDING_TOL


def _neuron_voltage_findings(side, state, findings):
    v_min = state.get("v_min")
    v_max = state.get("v_max")
    v_mean = state.get("v_mean")
    bounds_known = _finite_voltage(v_min) and _finite_voltage(v_max)
    if bounds_known and v_min > v_max:
        findings.append(f"{side}.v_min is greater than v_max")
    mean_known = bounds_known and _finite_voltage(v_mean)
    if mean_known and not _within_recorded_bounds(v_mean, v_min, v_max):
        findings.append(f"{side}.v_mean does not lie between v_min and v_max")
    for position, sample in enumerate(state["v_trace"]):
        if not _finite_voltage(sample):
            findings.append(f"{side}.v_trace[{position}] is not numeric")
            continue
        if _finite_voltage(v_min) and sample < v_min - ROUNDING_TOL:
            findings.append(f"{side}.v_trace[{position}] is below the recorded v_min")
        if _finite_voltage(v_max) and sample > v_max + ROUNDING_TOL:
            findings.append(f"{side}.v_trace[{position}] is above the recorded v_max")


def _neuron_side_findings(record, side, state, findings):
    _steps, duration_ms = _neuron_window(record)
    times = state["spike_times_ms"]
    if any(later < earlier for earlier, later in pairwise(times)):
        findings.append(f"{side}.spike_times_ms is not non-decreasing")
    if any(time_ms < 0 or time_ms >= duration_ms for time_ms in times):
        findings.append(
            f"{side}.spike_times_ms contains an event outside the simulated duration"
        )
    _neuron_summary_findings(record, side, state, findings)
    _neuron_voltage_findings(side, state, findings)


def _neuron_intervention_findings(record, findings):
    configuration = record["oracle"]["configuration"]
    parameter = configuration["intervened_parameter"]
    expected_parameter = sim.INTERVENTION_TARGETS[record["intervention"]["target"]]
    if record["intervention"]["parameter"] != expected_parameter:
        findings.append("intervention.parameter does not match intervention.target")
    changed = [
        key
        for key in configuration["before"]
        if configuration["before"][key] != configuration["after"].get(key)
    ]
    if changed != [parameter]:
        findings.append(f"intervention should change exactly {parameter!r}, but changed {changed}")


def _neuron_checks(record):
    measured = record["result"]["measured"]
    findings = []
    _neuron_delta_findings(measured, findings)
    if record["oracle"]["implementation"] != "named-runtime":
        _neuron_rerun_findings(record, measured, findings)
    for side, state in (("before", measured["before"]), ("after", measured["after"])):
        _neuron_side_findings(record, side, state, findings)
    _neuron_intervention_findings(record, findings)
    return findings


def _score_neuron(record):
    predicted = _guess(record, "predicted_direction")
    if predicted is None:
        return None
    return predicted == record["result"]["measured"]["delta"]["direction"]
