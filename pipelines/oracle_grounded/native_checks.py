"""Pure consistency checks for schema-validated crate-native measurements.

These checks never execute a record's metadata. Authoritative computation is
separately reproduced through the explicitly selected local Rust executable.
"""
from __future__ import annotations

import math

from .import_twins import bind_import_twin
from .canon import PRECISION

# Each stored float can differ by half a canonical decimal unit; comparing
# derived values from already-rounded reconstructions needs at most two units.
ROUNDING_TOL = 10 ** -PRECISION

PROFILES = {
    "axon-stream-v1": (
        "spike-encoder-equivalence-pairs", "axon-encoder", "0.4.0",
        "102946f40dd55287a89aa363cd2d080a9d6195d8",
    ),
    "neuromod-lif-v1": (
        "neuron-dynamics-counterfactuals", "neuromod", "0.6.0",
        "184c80cbdad84c83042987e1b3ec6fed69578a87",
    ),
}


def _identity(record, profile):
    family, name, version, revision = PROFILES[profile]
    identity = record["result"]["measured"]["identity"]
    oracle = record["oracle"]
    findings = []
    expected = dict(crate_name=name, crate_version=version, source_revision=revision)
    for field, value in expected.items():
        if identity[field] != value:
            findings.append(f"identity.{field} does not match published profile runtime")
    if record["family"] != family:
        findings.append("native profile does not match family")
    if oracle["implementation"] != "named-runtime":
        findings.append("native profile requires named-runtime implementation")
    if oracle["configuration"].get("profile") != profile:
        findings.append("oracle configuration profile differs from scenario")
    stage_expected = dict(requested_runtime=name, version=version, runtime_commit=revision)
    stages = oracle.get("stages", [])
    if len(stages) != 1 or any(stages[0].get(k) != v for k, v in stage_expected.items()):
        findings.append("oracle stage does not identify the native profile runtime")
    return findings


def _events(times, dt_ms, count, offset=0):
    if any(not math.isfinite(t) or t < offset * dt_ms or t > (count - 1 + offset) * dt_ms for t in times):
        return ["spike time lies outside the signal window"]
    if any(not math.isclose(t / dt_ms, round(t / dt_ms), abs_tol=1e-7) for t in times):
        return ["spike times are not on the configured sampling grid"]
    if times != sorted(times):
        return ["spike times are not ordered"]
    return []


def _decoded(state, scenario, side):
    """Derive the adapter's documented reconstruction from authenticated events."""
    params = scenario["parameters"]
    dt_ms = params["sample_ms"]
    events = [[] for _ in scenario["signal"]]
    for event in state["spikes"]:
        tick = round(event["t_ms"] / dt_ms)
        if 0 <= tick < len(events):
            events[tick].append(event["polarity"])
    expected = []
    level = 0.0
    for tick_events in events:
        if side == "rate":
            level = min(1.0, len(tick_events) / (params["rate_hz"] * dt_ms / 1000.0))
        else:
            for polarity in tick_events:
                level = min(1.0, max(0.0, level + (1 if polarity else -1)
                                     * params["delta_threshold"]))
        expected.append(level)
    return expected


def _reconstruction(state, scenario, side):
    expected = _decoded(state, scenario, side)
    if any(not math.isclose(a, b, rel_tol=0.0, abs_tol=ROUNDING_TOL)
           for a, b in zip(expected, state["reconstruction"], strict=True)):
        return [f"{side}.reconstruction differs from full spike evidence"]
    if side == "rate" and any(not event["polarity"] for event in state["spikes"]):
        return ["rate spike polarity must be positive"]
    return []


def _parameters(record, profile):
    params = record["scenario"]["parameters"]
    if profile == "axon-stream-v1":
        if params["rate_hz"] * params["sample_ms"] / 1000.0 > 1:
            return ["rate probability exceeds one event per step"]
        return []
    intervention = record["intervention"]
    parameter = intervention["parameter"]
    value = params[parameter] * intervention["factor"]
    low, high = {"threshold": (0.0001, 100), "decay": (0, 1), "input_scale": (0, 100)}[parameter]
    return [] if low <= value <= high else ["intervention exceeds native parameter bounds"]


def _encoder(record):
    measured = record["result"]["measured"]
    signal = record["scenario"]["signal"]
    dt_ms = record["scenario"]["parameters"]["sample_ms"]
    findings = []
    for side in ("rate", "delta"):
        state = measured[side]
        if state["spike_count"] != len(state["spikes"]):
            findings.append(f"{side}.spike_count differs from full spike evidence")
        findings.extend(f"{side}: {message}" for message in _events(
            [event["t_ms"] for event in state["spikes"]], dt_ms, len(signal)))
        if any(event["channel"] != 0 or not isinstance(event["polarity"], bool)
               for event in state["spikes"]):
            findings.append(f"{side}: invalid channel or polarity")
        if state["spike_preview"] != state["spikes"][:24]:
            findings.append(f"{side}.spike_preview differs from first 24 events")
        if state["spike_preview_truncated"] != (len(state["spikes"]) > 24):
            findings.append(f"{side}.spike_preview_truncated differs from evidence length")
        decoded = state["reconstruction"]
        if len(decoded) != len(signal):
            findings.append(f"{side}.reconstruction length differs from signal")
            continue
        findings.extend(_reconstruction(state, record["scenario"], side))
        rmse = math.sqrt(sum((a - b) ** 2 for a, b in zip(signal, decoded, strict=True))
                         / len(signal))
        if not math.isclose(state["rmse"], rmse, rel_tol=0.0, abs_tol=ROUNDING_TOL):
            findings.append(f"{side}.rmse differs from reconstruction error")
    errors = []
    for side in ("rate", "delta"):
        decoded = _decoded(measured[side], record["scenario"], side)
        errors.append(math.sqrt(sum((a - b) ** 2 for a, b in zip(signal, decoded, strict=True))
                                / len(signal)))
    rate, delta = errors
    winner = "tie" if rate == delta else ("rate" if rate < delta else "delta")
    if measured["winner"] != winner:
        findings.append("winner differs from measured reconstruction error")
    return findings


def _neuron(record):
    measured = record["result"]["measured"]
    signal = record["scenario"]["signal"]
    dt_ms = record["scenario"]["parameters"]["dt_ms"]
    findings = []
    for side in ("before", "after"):
        state = measured[side]
        if state["spike_count"] != len(state["spikes"]):
            findings.append(f"{side}.spike_count differs from full spike evidence")
        if len(state["v_trace"]) != len(signal):
            findings.append(f"{side}.v_trace length differs from signal")
        findings.extend(f"{side}: {message}" for message in _events(
            state["spikes"], dt_ms, len(signal), offset=1))
    delta = measured["after"]["spike_count"] - measured["before"]["spike_count"]
    if measured["spike_count_delta"] != delta:
        findings.append("spike_count_delta differs from before/after measurements")
    return findings


def checks(record):
    """Return bounded findings for an already schema-validated native record."""
    profile = record["scenario"]["profile"]
    if profile not in PROFILES:
        return ["unsupported native profile"]
    findings = _identity(record, profile)
    findings.extend(_parameters(record, profile))
    if record["result"]["measured"]["profile"] != profile:
        findings.append("measurement profile differs from scenario")
    findings.extend(_encoder(record) if profile == "axon-stream-v1" else _neuron(record))
    return findings


bind_import_twin(__name__)
