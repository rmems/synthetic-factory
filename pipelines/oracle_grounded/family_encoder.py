"""Family 1: spike-encoder-equivalence-pairs  (oracle: axon-encoder).

Two encodings of the same sensor signal are measured side by side; the record
keeps the reconstruction fidelity, spike economy, and the winner decision. The
checks re-derive every retained metric from the stored signal and
reconstruction, and a reference record is additionally authenticated by
re-running the reference encoder.
"""

from . import canon, generators, oracles, sim
from .family_common import (
    DIMENSIONLESS,
    ENERGY_UNITS,
    RATE_UNITS,
    TIME_UNITS,
    _guess,
    _measurement_matches,
)

ENCODER_UNITS = {
    "spike_count": "spikes",
    "mean_rate_hz": RATE_UNITS,
    "energy_pJ": ENERGY_UNITS,
    "rmse": "normalized sensor units",
    "mean_abs_error": "normalized sensor units",
    "max_abs_error": "normalized sensor units",
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


def encoder_request(scenario, _intervention):
    # This family perturbs the sensor, not the oracle, so the intervention
    # never reaches the request.
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
        pair[0],
        pair[1],
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


def _encoder_derived_metrics(scenario, state, decoded):
    """Metrics a stored side must satisfy given its signal and reconstruction."""
    errors = [
        abs(actual - reconstructed)
        for actual, reconstructed in zip(scenario["signal"], decoded, strict=True)
    ]
    expected_rmse = sim.rmse(scenario["signal"], decoded)
    return {
        "rmse": expected_rmse,
        "mean_abs_error": sum(errors) / len(errors) if errors else 0.0,
        "max_abs_error": max(errors) if errors else 0.0,
        "pearson_r": sim.pearson(scenario["signal"], decoded),
        "information_retention": sim.clamp(1.0 - expected_rmse, 0.0, 1.0),
        "mean_rate_hz": state["spike_count"]
        / ((scenario["sample_count"] * scenario["sample_ms"]) / 1000.0),
        "energy_pJ": state["spike_count"] * sim.ENERGY_PJ_PER_SPIKE,
        "retention_per_spike": (
            sim.clamp(1.0 - expected_rmse, 0.0, 1.0) / state["spike_count"]
            if state["spike_count"]
            else None
        ),
    }


def _encoder_reconstruction_findings(scenario, side, state, findings):
    decoded = state["reconstruction"]
    if len(decoded) != scenario["sample_count"]:
        findings.append(f"{side}.reconstruction length does not match sample_count")
        return
    derived = _encoder_derived_metrics(scenario, state, decoded)
    for field, expected in derived.items():
        if not _measurement_matches(state.get(field), expected):
            findings.append(
                f"{side}.{field} does not match the value derived from "
                "the signal, reconstruction, and spike count"
            )


def _encoder_excerpt_findings(scenario, side, state, findings):
    excerpt = state["representation_excerpt"]
    if len(excerpt) > state["spike_count"]:
        findings.append(f"{side}.representation_excerpt exceeds spike_count")
    duration_ms = scenario["sample_count"] * scenario["sample_ms"]
    # Set membership keeps this loop linear: both arrays are untrusted
    # and unbounded up to the validator's file limit, so a list scan per
    # event would be quadratic on malformed input.
    known_channels = set(state["channels"])
    for position, event in enumerate(excerpt):
        if event["channel"] not in known_channels:
            findings.append(
                f"{side}.representation_excerpt[{position}] names an unknown channel"
            )
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


def _encoder_recompute_findings(record, side, expected_encoding, findings):
    """Authenticate a reference side against a re-run of the reference encoder."""
    scenario = record["scenario"]
    state = record["result"]["measured"][side]
    encoder_config = record["oracle"]["configuration"]["encoder"]
    recomputed = sim.run_encoder(scenario["signal"], expected_encoding, encoder_config)
    expected_excerpt = recomputed["spikes"][: int(encoder_config["excerpt_spikes"])]
    excerpt = state["representation_excerpt"]
    if canon.normalize(excerpt) != canon.normalize(expected_excerpt):
        findings.append(
            f"{side}.representation_excerpt is not the prefix of the "
            "recomputed spike train"
        )
    if state.get("spike_train_digest") != canon.digest(recomputed["spikes"]):
        findings.append(
            f"{side}.spike_train_digest does not match the recomputed spike train"
        )
    # The checks above authenticate the spike train through its excerpt
    # prefix and digest, but the derived metrics only prove the stored
    # reconstruction and metrics are *self*-consistent, not that they came
    # from this signal. Compare against the recomputed decode directly so a
    # self-consistent edit to the decoded training target cannot pass.
    if canon.normalize(state.get("reconstruction")) != canon.normalize(
        recomputed["reconstruction"]
    ):
        findings.append(f"{side}.reconstruction does not match the recomputed decode")
    if state.get("spike_count") != recomputed["spike_count"]:
        findings.append(f"{side}.spike_count does not match the recomputed encode")


def _encoder_side_findings(record, side, expected_encoding, findings):
    scenario = record["scenario"]
    state = record["result"]["measured"][side]
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
    _encoder_reconstruction_findings(scenario, side, state, findings)
    _encoder_excerpt_findings(scenario, side, state, findings)
    # A named runtime is measured through its own reproduction path
    # (``record.reproduce``, which replays through the actual bound adapter)
    # precisely because its spike timing or floating-point behavior is not
    # required to agree with this Python reference; only a reference-
    # implementation record is authenticated by rerunning the reference here.
    if record["oracle"]["implementation"] != "named-runtime":
        _encoder_recompute_findings(record, side, expected_encoding, findings)


def _encoder_margin_findings(measured, findings):
    retention_gap = (
        measured["encoding_a"]["information_retention"]
        - measured["encoding_b"]["information_retention"]
    )
    if not _measurement_matches(measured["retention_margin"], retention_gap):
        findings.append("retention_margin does not match the two measured retentions")
    energy_gap = measured["encoding_a"]["energy_pJ"] - measured["encoding_b"]["energy_pJ"]
    if not _measurement_matches(measured["energy_margin_pJ"], energy_gap):
        findings.append("energy_margin_pJ does not match the two measured energies")


def _encoder_expected_decision(measured, pair, tie_epsilon):
    """The winner and basis the measured retentions and spike counts dictate."""
    retention_gap = (
        measured["encoding_a"]["information_retention"]
        - measured["encoding_b"]["information_retention"]
    )
    if abs(retention_gap) >= tie_epsilon:
        return "information_retention", pair[0] if retention_gap > 0 else pair[1]
    count_a = measured["encoding_a"]["spike_count"]
    count_b = measured["encoding_b"]["spike_count"]
    if count_a != count_b:
        return "spike_count_tiebreak", pair[0] if count_a < count_b else pair[1]
    return "tie", None


def _encoder_winner_findings(record, pair, findings):
    measured = record["result"]["measured"]
    tie_epsilon = record["oracle"]["configuration"]["tie_epsilon"]
    expected_basis, expected_winner = _encoder_expected_decision(measured, pair, tie_epsilon)
    if measured["winner_basis"] != expected_basis:
        findings.append(
            f"winner_basis {measured['winner_basis']!r} does not match the measured "
            f"retention and spike counts ({expected_basis!r})"
        )
    if measured["winner"] != expected_winner:
        findings.append(
            f"winner {measured['winner']!r} does not match the measured "
            f"{expected_basis} decision"
        )


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
        _encoder_side_findings(record, side, expected_encoding, findings)
    _encoder_margin_findings(measured, findings)
    _encoder_winner_findings(record, pair, findings)
    return findings


def _score_encoder(record):
    predicted = _guess(record, "predicted_winner")
    return None if predicted is None else predicted == record["result"]["measured"]["winner"]
