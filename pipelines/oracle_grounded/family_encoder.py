"""Spike-encoder family wiring and invariant checks."""

from . import canon, generators, oracles, sim
from .family_common import DIMENSIONLESS, ENERGY_UNITS, RATE_UNITS, TIME_UNITS
from .family_common import _measurement_matches

# --------------------------------------------------------------------------
# Family 1: spike-encoder-equivalence-pairs  (oracle: axon-encoder)
# --------------------------------------------------------------------------

SENSOR_UNITS = "normalized sensor units"

ENCODER_UNITS = {
    "spike_count": "spikes",
    "mean_rate_hz": RATE_UNITS,
    "energy_pJ": ENERGY_UNITS,
    "rmse": SENSOR_UNITS,
    "mean_abs_error": SENSOR_UNITS,
    "max_abs_error": SENSOR_UNITS,
    "pearson_r": DIMENSIONLESS,
    "information_retention": "dimensionless, 1 - rmse clipped to [0, 1]",
    "retention_per_spike": "retention per spike",
    "representation_excerpt.t_ms": TIME_UNITS,
    "retention_margin": "dimensionless, retention(a) - retention(b)",
    "energy_margin_pJ": ENERGY_UNITS,
}


def _trim_encoding(measured):
    """Swap the full spike train for a digest; keep a bounded excerpt."""
    trimmed = dict(measured)
    spikes = trimmed.pop("spikes")
    trimmed["spike_train_digest"] = canon.digest(spikes)
    return trimmed


def encoder_request(scenario, intervention):
    del intervention  # this family perturbs the sensor, not the oracle
    return {
        "configuration": {
            "encoder": sim.encoder_config(
                {
                    "sample_ms": scenario["sample_ms"],
                    "excerpt_spikes": 24,
                }
            ),
            "tie_epsilon": 0.005,
            "encoding_pair": list(scenario["encoding_pair"]),
        },
        "data": {"signal": list(scenario["signal"])},
    }


def _encoder_reference(request):
    config = request["configuration"]
    pair = config["encoding_pair"]
    comparison = sim.compare_encodings(
        request["data"]["signal"],
        (pair[0], pair[1]),
        config["encoder"],
        tie_epsilon=config["tie_epsilon"],
    )
    measured = {
        "encoding_a": _trim_encoding(comparison["a"]),
        "encoding_b": _trim_encoding(comparison["b"]),
        "winner": comparison["winner"],
        "winner_basis": comparison["winner_basis"],
        "retention_margin": comparison["retention_margin"],
        "energy_margin_pJ": comparison["energy_margin_pJ"],
    }
    return measured, ENCODER_UNITS


def _encoder_oracle(environ=None):
    return oracles.bind(
        runtime="axon-encoder",
        identity=oracles.OracleIdentity(
            oracle_id="encoder-ref",
            oracle_type="spike-encoder",
            description=(
                "Deterministic rate / latency / delta / temporal encoders with matched "
                "decoders, standing in for axon-encoder"
            ),
        ),
        reference_fn=_encoder_reference,
        environ=environ,
    )


def _encoder_propose(rng):
    scenario = generators.propose_encoder_scenario(rng)
    return scenario, None, generators.predict_encoder_winner(scenario)


def _encoding_shape_findings(record, side, expected_encoding):
    state = record["result"]["measured"][side]
    findings = []
    if state["encoding"] != expected_encoding:
        findings.append(
            f"{side}.encoding {state['encoding']!r} does not match "
            f"scenario.encoding_pair ({expected_encoding!r})"
        )
    retention = state["information_retention"]
    if not 0.0 <= retention <= 1.0:
        findings.append(f"{side}.information_retention out of range: {retention}")
    if state["spike_count"] < 0:
        findings.append(f"{side}.spike_count is negative")
    return findings


def _reconstruction_gate_findings(record, side, scenario):
    decoded = record["result"]["measured"][side]["reconstruction"]
    if len(decoded) not in (scenario["sample_count"], len(scenario["signal"])):
        return [f"{side}.reconstruction length does not match the scenario"]
    if scenario["sample_count"] != len(scenario["signal"]):
        return ["scenario.sample_count does not match signal length"]
    return []


def _reconstruction_derived(scenario, state):
    decoded = state["reconstruction"]
    errors = [
        abs(actual - reconstructed)
        for actual, reconstructed in zip(scenario["signal"], decoded, strict=True)
    ]
    expected_rmse = sim.rmse(scenario["signal"], decoded)
    retention = sim.clamp(1.0 - expected_rmse, 0.0, 1.0)
    elapsed_s = scenario["sample_count"] * scenario["sample_ms"] / 1000.0
    return {
        "rmse": expected_rmse,
        "mean_abs_error": sum(errors) / len(errors) if errors else 0.0,
        "max_abs_error": max(errors) if errors else 0.0,
        "pearson_r": sim.pearson(scenario["signal"], decoded),
        "information_retention": retention,
        "mean_rate_hz": state["spike_count"] / elapsed_s if elapsed_s > 0 else None,
        "energy_pJ": state["spike_count"] * sim.ENERGY_PJ_PER_SPIKE,
        "retention_per_spike": retention / state["spike_count"] if state["spike_count"] else None,
    }


def _encoding_summary_findings(record, side, expected_encoding):
    scenario = record["scenario"]
    findings = _encoding_shape_findings(record, side, expected_encoding)
    gate = _reconstruction_gate_findings(record, side, scenario)
    if gate:
        findings.extend(gate)
        return findings
    state = record["result"]["measured"][side]
    for field, expected in _reconstruction_derived(scenario, state).items():
        if not _measurement_matches(state.get(field), expected):
            findings.append(
                f"{side}.{field} does not match the value derived from "
                "the signal, reconstruction, and spike count"
            )
    return findings


def _encoding_excerpt_findings(record, side):
    state = record["result"]["measured"][side]
    scenario = record["scenario"]
    excerpt = state["representation_excerpt"]
    excerpt_limit = int(record["oracle"]["configuration"]["encoder"]["excerpt_spikes"])
    if len(excerpt) > excerpt_limit:
        return [f"{side}.representation_excerpt exceeds the configured excerpt bound"], True
    findings = []
    if len(excerpt) > state["spike_count"]:
        findings.append(f"{side}.representation_excerpt exceeds spike_count")
    duration_ms = scenario["sample_count"] * scenario["sample_ms"]
    known_channels = set(state["channels"])
    for position, event in enumerate(excerpt):
        if event["channel"] not in known_channels:
            findings.append(f"{side}.representation_excerpt[{position}] names an unknown channel")
        if not 0 <= event["t_ms"] < duration_ms:
            findings.append(
                f"{side}.representation_excerpt[{position}].t_ms lies outside "
                "the encoded signal window"
            )
    expected_truncated = state["spike_count"] > len(excerpt)
    if state.get("representation_excerpt_truncated") is not expected_truncated:
        findings.append(
            f"{side}.representation_excerpt_truncated does not match "
            "spike_count and the retained excerpt"
        )
    return findings, False


def _reference_encoding_findings(record, side, expected_encoding):
    if record["oracle"]["implementation"] == "named-runtime":
        return []
    state = record["result"]["measured"][side]
    scenario = record["scenario"]
    encoder_config = record["oracle"]["configuration"]["encoder"]
    recomputed = sim.run_encoder(scenario["signal"], expected_encoding, encoder_config)
    expected_excerpt = recomputed["spikes"][: int(encoder_config["excerpt_spikes"])]
    findings = []
    if canon.normalize(state["representation_excerpt"]) != canon.normalize(expected_excerpt):
        findings.append(
            f"{side}.representation_excerpt is not the prefix of the recomputed spike train"
        )
    if state.get("spike_train_digest") != canon.digest(recomputed["spikes"]):
        findings.append(f"{side}.spike_train_digest does not match the recomputed spike train")
    if canon.normalize(state.get("reconstruction")) != canon.normalize(recomputed["reconstruction"]):
        findings.append(f"{side}.reconstruction does not match the recomputed decode")
    if state.get("spike_count") != recomputed["spike_count"]:
        findings.append(f"{side}.spike_count does not match the recomputed encode")
    return findings


def _expected_winner_decision(measured, pair, tie_epsilon):
    """The (winner_basis, winner) the measured retentions and counts imply."""
    retention_gap = (
        measured["encoding_a"]["information_retention"]
        - measured["encoding_b"]["information_retention"]
    )
    if abs(retention_gap) >= tie_epsilon:
        return "information_retention", (pair[0] if retention_gap > 0 else pair[1])
    if measured["encoding_a"]["spike_count"] != measured["encoding_b"]["spike_count"]:
        return "spike_count_tiebreak", min(
            pair,
            key=lambda encoding: measured[
                "encoding_a" if encoding == pair[0] else "encoding_b"
            ]["spike_count"],
        )
    return "tie", None


def _encoder_winner_findings(record):
    measured = record["result"]["measured"]
    pair = record["scenario"]["encoding_pair"]
    retention_gap = (
        measured["encoding_a"]["information_retention"]
        - measured["encoding_b"]["information_retention"]
    )
    findings = []
    if not _measurement_matches(measured["retention_margin"], retention_gap):
        findings.append("retention_margin does not match the two measured retentions")
    energy_gap = measured["encoding_a"]["energy_pJ"] - measured["encoding_b"]["energy_pJ"]
    if not _measurement_matches(measured["energy_margin_pJ"], energy_gap):
        findings.append("energy_margin_pJ does not match the two measured energies")
    expected_basis, expected_winner = _expected_winner_decision(
        measured, pair, record["oracle"]["configuration"]["tie_epsilon"]
    )
    if measured["winner_basis"] != expected_basis:
        findings.append(
            f"winner_basis {measured['winner_basis']!r} does not match the measured "
            f"retention and spike counts ({expected_basis!r})"
        )
    if measured["winner"] != expected_winner:
        findings.append(
            f"winner {measured['winner']!r} does not match the measured {expected_basis} decision"
        )
    return findings


def _encoder_checks(record):
    measured = record["result"]["measured"]
    scenario = record["scenario"]
    pair = scenario["encoding_pair"]
    findings = []
    winner = measured["winner"]
    if winner is not None and winner not in pair:
        findings.append(f"winner {winner!r} is not one of the compared encodings {pair}")
    if len(scenario["signal"]) != scenario["sample_count"]:
        findings.append("scenario.signal length does not match scenario.sample_count")
    for side, expected_encoding in zip(("encoding_a", "encoding_b"), pair, strict=True):
        findings.extend(_encoding_summary_findings(record, side, expected_encoding))
        excerpt_findings, oversized = _encoding_excerpt_findings(record, side)
        findings.extend(excerpt_findings)
        if not oversized:
            findings.extend(_reference_encoding_findings(record, side, expected_encoding))
    findings.extend(_encoder_winner_findings(record))
    return findings
