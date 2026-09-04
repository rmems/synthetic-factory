"""Family 1 oracle: spike encoders (stand-in for ``axon-encoder``).

Four deterministic encode/decode pairs — rate, latency, delta, temporal —
plus the measurement harness that runs an encoding against a signal and the
comparison that lets the measurements, not the generator, pick a winner.
Every function is pure and deterministic: same inputs, same floats.
"""

import math

from .sim_core import ENERGY_PJ_PER_SPIKE, clamp, pearson, rmse

ENCODINGS = ("rate", "latency", "delta", "temporal")

ENCODER_DEFAULTS = {
    "sample_ms": 10.0,
    "substeps": 8,
    "max_rate_hz": 800.0,
    "latency_span": 0.9,
    "latency_floor": 0.02,
    "delta_theta": 0.125,
    "delta_init": 0.5,
    "temporal_bins": 8,
    "excerpt_spikes": 24,
}


def encoder_config(overrides=None):
    config = dict(ENCODER_DEFAULTS)
    if overrides:
        config.update(overrides)
    return config


def encode_rate(signal, config):
    """Delta-sigma rate code: one channel, spike count proportional to value.

    A leaky accumulator is charged by ``value`` each micro-step and emits a
    spike whenever it crosses 1.0, carrying the remainder forward. This is
    deterministic where a Poisson rate code would not be.
    """
    sample_ms = config["sample_ms"]
    substeps = int(config["substeps"])
    micro_ms = sample_ms / substeps
    gain = config["max_rate_hz"] * micro_ms / 1000.0
    accumulator = 0.0
    spikes = []
    for index, raw in enumerate(signal):
        value = clamp(raw, 0.0, 1.0)
        for step in range(substeps):
            accumulator += value * gain
            if accumulator >= 1.0:
                accumulator -= 1.0
                spikes.append({"channel": "rate", "t_ms": index * sample_ms + step * micro_ms})
    return spikes


def decode_rate(spikes, sample_count, config):
    sample_ms = config["sample_ms"]
    per_sample = config["max_rate_hz"] * sample_ms / 1000.0
    counts = [0] * sample_count
    for spike in spikes:
        index = int(spike["t_ms"] // sample_ms)
        if 0 <= index < sample_count:
            counts[index] += 1
    return [clamp(count / per_sample, 0.0, 1.0) for count in counts]


def encode_latency(signal, config):
    """Time-to-first-spike: a larger value spikes earlier inside its window."""
    sample_ms = config["sample_ms"]
    span = config["latency_span"]
    floor = config["latency_floor"]
    spikes = []
    for index, raw in enumerate(signal):
        value = clamp(raw, 0.0, 1.0)
        if value < floor:
            continue
        offset = (1.0 - value) * sample_ms * span
        spikes.append({"channel": "latency", "t_ms": index * sample_ms + offset})
    return spikes


def decode_latency(spikes, sample_count, config):
    sample_ms = config["sample_ms"]
    span = config["latency_span"]
    decoded = [0.0] * sample_count
    seen = [False] * sample_count
    for spike in spikes:
        index = int(spike["t_ms"] // sample_ms)
        if not (0 <= index < sample_count) or seen[index]:
            continue
        seen[index] = True
        offset = spike["t_ms"] - index * sample_ms
        decoded[index] = clamp(1.0 - offset / (sample_ms * span), 0.0, 1.0)
    return decoded


def encode_delta(signal, config):
    """ON/OFF change code: spikes only when the value moves by a threshold."""
    sample_ms = config["sample_ms"]
    theta = config["delta_theta"]
    reference = config["delta_init"]
    spikes = []
    for index, raw in enumerate(signal):
        value = clamp(raw, 0.0, 1.0)
        guard = 0
        while value - reference >= theta and guard < 16:
            reference += theta
            spikes.append({"channel": "delta_on", "t_ms": index * sample_ms})
            guard += 1
        while reference - value >= theta and guard < 16:
            reference -= theta
            spikes.append({"channel": "delta_off", "t_ms": index * sample_ms})
            guard += 1
    return spikes


def _channels_by_sample(spikes, sample_count, sample_ms):
    """Group spike channel labels by the sample window each spike lands in."""
    by_sample = [[] for _ in range(sample_count)]
    for spike in spikes:
        index = int(spike["t_ms"] // sample_ms)
        if 0 <= index < sample_count:
            by_sample[index].append(spike["channel"])
    return by_sample


def decode_delta(spikes, sample_count, config):
    theta = config["delta_theta"]
    level = config["delta_init"]
    by_sample = _channels_by_sample(spikes, sample_count, config["sample_ms"])
    decoded = []
    for channels in by_sample:
        for channel in channels:
            level += theta if channel == "delta_on" else -theta
        decoded.append(clamp(level, 0.0, 1.0))
    return decoded


def encode_temporal(signal, config):
    """Phase code: a reference spike plus a phase spike whose lag is the value."""
    sample_ms = config["sample_ms"]
    bins = int(config["temporal_bins"])
    bin_ms = sample_ms / bins
    spikes = []
    for index, raw in enumerate(signal):
        value = clamp(raw, 0.0, 1.0)
        base = index * sample_ms
        phase = int(math.floor(value * (bins - 1) + 0.5))
        spikes.append({"channel": "temporal_ref", "t_ms": base})
        spikes.append({"channel": "temporal_phase", "t_ms": base + phase * bin_ms})
    return spikes


def _phase_sample_index(spike, sample_ms, sample_count):
    """The sample window a phase spike lands in; None for any other spike."""
    if spike["channel"] != "temporal_phase":
        return None
    index = int(spike["t_ms"] // sample_ms)
    if not (0 <= index < sample_count):
        return None
    return index


def decode_temporal(spikes, sample_count, config):
    sample_ms = config["sample_ms"]
    bins = int(config["temporal_bins"])
    bin_ms = sample_ms / bins
    decoded = [0.0] * sample_count
    for spike in spikes:
        index = _phase_sample_index(spike, sample_ms, sample_count)
        if index is None:
            continue
        phase = round((spike["t_ms"] - index * sample_ms) / bin_ms)
        decoded[index] = clamp(phase / (bins - 1), 0.0, 1.0)
    return decoded


_ENCODERS = {
    "rate": (encode_rate, decode_rate),
    "latency": (encode_latency, decode_latency),
    "delta": (encode_delta, decode_delta),
    "temporal": (encode_temporal, decode_temporal),
}


def run_encoder(signal, encoding, config):
    """Encode, decode, and measure one encoding family against the signal."""
    if encoding not in _ENCODERS:
        raise ValueError(f"unknown encoding: {encoding}")
    encode, decode = _ENCODERS[encoding]
    spikes = encode(signal, config)
    spikes.sort(key=lambda item: (item["t_ms"], item["channel"]))
    decoded = decode(spikes, len(signal), config)
    errors = [abs(a - b) for a, b in zip(signal, decoded, strict=True)]
    error = rmse(signal, decoded)
    retention = clamp(1.0 - error, 0.0, 1.0)
    count = len(spikes)
    excerpt = spikes[: int(config["excerpt_spikes"])]
    duration_ms = len(signal) * config["sample_ms"]
    return {
        "encoding": encoding,
        "spike_count": count,
        "channels": sorted({spike["channel"] for spike in spikes}),
        "mean_rate_hz": (count / (duration_ms / 1000.0)) if duration_ms else 0.0,
        "energy_pJ": count * ENERGY_PJ_PER_SPIKE,
        "rmse": error,
        "max_abs_error": max(errors) if errors else 0.0,
        "mean_abs_error": (sum(errors) / len(errors)) if errors else 0.0,
        "pearson_r": pearson(signal, decoded),
        "information_retention": retention,
        "retention_per_spike": (retention / count) if count else None,
        "reconstruction": decoded,
        "representation_excerpt": excerpt,
        "representation_excerpt_truncated": count > len(excerpt),
        "spike_train_digest": None,  # filled in by the adapter over the full train
        "spikes": spikes,
    }


def _encoding_winner(gap, spike_counts, encodings, tie_epsilon):
    """Winner and basis, from the retention gap with a spike-count tiebreak."""
    encoding_a, encoding_b = encodings
    count_a, count_b = spike_counts
    if abs(gap) >= tie_epsilon:
        winner = encoding_a if gap > 0 else encoding_b
        return winner, "information_retention"
    if count_a != count_b:
        winner = encoding_a if count_a < count_b else encoding_b
        return winner, "spike_count_tiebreak"
    return None, "tie"


def compare_encodings(signal, encodings, config, tie_epsilon=0.005):
    """Run two encodings on one signal and let the measurements pick a winner.

    ``encodings`` is the ``(encoding_a, encoding_b)`` pair to race.
    """
    encoding_a, encoding_b = encodings
    left = run_encoder(signal, encoding_a, config)
    right = run_encoder(signal, encoding_b, config)
    gap = left["information_retention"] - right["information_retention"]
    winner, basis = _encoding_winner(
        gap, (left["spike_count"], right["spike_count"]), encodings, tie_epsilon
    )
    return {
        "a": left,
        "b": right,
        "winner": winner,
        "winner_basis": basis,
        "retention_margin": gap,
        "energy_margin_pJ": left["energy_pJ"] - right["energy_pJ"],
        "tie_epsilon": tie_epsilon,
    }
