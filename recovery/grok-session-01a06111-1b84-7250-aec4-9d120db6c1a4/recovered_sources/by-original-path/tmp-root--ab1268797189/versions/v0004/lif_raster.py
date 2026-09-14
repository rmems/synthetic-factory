#!/usr/bin/env python3
"""Current-based LIF raster generator for TTF r13.

Excerpts are membrane threshold crossings of a CUBA LIF population, not a
re-encode of spike_events. Optional kernelized event times become exponential
synaptic current; they are never copied into raster.excerpt.

Stdlib only. Does not write outputs/raw/.
"""

from __future__ import annotations

import json
import math
import random
import sys
from typing import Any, Iterable, Mapping, Sequence

PJ_PER_SPIKE = 23
UJ_PER_SPIKE = 23 / 1_000_000
WINDOW_MS_MIN = 20
WINDOW_MS_MAX = 50
REFRACTORY_MS = 1.0
EXCERPT_CAP = 16
DT_US = 50
ENERGY_PJ_TOL = 1e-6
ENERGY_UJ_TOL = 1e-9
WINDOW_S_TOL = 1e-9
SPIKE_BUDGET_TOL = 1
SAME_NEURON_GAP_US = 1000

# r12 published budgets (neurons, mean_rate_hz, window_ms). Excerpt times in
# /tmp/batch-r12.jsonl were t_rel_ms*1000 copies of spike_events; this generator
# must not reproduce that coupling.
R12_BUDGETS: tuple[tuple[str, int, float, float], ...] = (
    ("ttf-r12-076", 64, 40.0, 25.0),
    ("ttf-r12-077", 128, 25.0, 40.0),
    ("ttf-r12-078", 32, 50.0, 20.0),
    ("ttf-r12-079", 96, 30.0, 32.0),
    ("ttf-r12-080", 48, 35.0, 28.0),
)

# New r13 candidates: distinct (n, rate, window) triples, still 20-50 ms.
R13_CANDIDATE_BUDGETS: tuple[tuple[str, int, float, float], ...] = (
    ("ttf-r13-c1", 80, 22.0, 45.0),
    ("ttf-r13-c2", 40, 38.0, 24.0),
    ("ttf-r13-c3", 104, 16.0, 48.0),
)

DEFAULT_ROUTING: dict[str, Any] = {
    "source": "thalamic_relay_cuba_lif",
    "target": "spikenaut_policy",
    "table": [{"from": "relay_lif", "to": "policy_gate", "weight": 0.5}],
    "third_factor": {
        "modulator": "acetylcholine",
        "tau_e_s": 0.25,
        "tau_e_ms": 250.0,
        "eligibility": "pre_post_stdp",
    },
}

# Fallback kernel times from ttf-r12-076 spike_events if the sidecar JSONL is absent.
_R12_076_KERNEL_MS: tuple[float, ...] = (
    1.088,
    2.410,
    3.226,
    4.018,
    5.184,
    5.361,
    5.374,
    6.410,
    8.205,
    11.740,
    13.102,
)


def expected_spikes(neurons: int, mean_rate_hz: float, window_ms: float) -> int:
    """Contract budget: round(neurons * mean_rate_hz * window_s)."""

    return round(neurons * mean_rate_hz * (window_ms / 1000.0))


def _as_int(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"expected a number, got {type(value).__name__}")
    if int(value) != value:
        raise ValueError(f"expected an integer-valued number, got {value!r}")
    return int(value)


def _finite(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"expected a number, got {type(value).__name__}")
    out = float(value)
    if not math.isfinite(out):
        raise ValueError(f"expected a finite number, got {value!r}")
    return out


def _rheobase_current(rate_hz: float, tau_m_s: float, v_th: float, t_ref_s: float) -> float:
    """Constant current that yields `rate_hz` for a deterministic CUBA LIF."""

    isi = 1.0 / rate_hz
    if isi <= t_ref_s + 1e-9:
        isi = t_ref_s + 1e-4
    ratio = math.exp((isi - t_ref_s) / tau_m_s)
    return ratio * v_th / (ratio - 1.0)


def _parse_kernel_times_ms(raw: Iterable[Any] | None, window_ms: float) -> list[float]:
    """Accept ms numbers, us numbers > 2*window_ms, or {t_rel_ms|t_ms|t_us}."""

    if raw is None:
        return []
    times: list[float] = []
    for item in raw:
        if isinstance(item, Mapping):
            if "t_rel_ms" in item:
                t_ms = _finite(item["t_rel_ms"])
            elif "t_ms" in item:
                t_ms = _finite(item["t_ms"])
            elif "t_us" in item:
                t_ms = _finite(item["t_us"]) / 1000.0
            else:
                continue
        else:
            value = _finite(item)
            t_ms = value / 1000.0 if value > window_ms * 2.0 else value
        if 0.0 <= t_ms <= window_ms:
            times.append(t_ms)
    times.sort()
    return times


def _first_passage_us(
    voltage: float,
    current: float,
    v_th: float,
    tau_m_s: float,
    t0_us: int,
    window_us: int,
) -> int | None:
    """Closed-form CUBA time-to-threshold from `voltage` under constant current."""

    if current <= v_th + 1e-12:
        return None
    denom = current - voltage
    if denom <= 0.0:
        return int(t0_us) if t0_us <= window_us else None
    arg = (current - v_th) / denom
    if arg <= 0.0:
        return None
    t_us = int(round(t0_us + (-tau_m_s * math.log(arg)) * 1_000_000.0))
    if t_us < t0_us:
        t_us = t0_us
    if t_us > window_us:
        return None
    return t_us


def _simulate_cuba(
    neurons: int,
    mean_rate_hz: float,
    window_us: int,
    seed: int,
    i_scale: float,
    kernel_ms: Sequence[float],
    tau_m_ms: float,
    v_th: float,
    t_ref_ms: float,
    tau_syn_ms: float,
) -> tuple[list[tuple[int, int]], list[float], list[float], list[int | None]]:
    """Euler CUBA LIF. RNG is frozen in `seed`; only `i_scale` changes the drive."""

    rng = random.Random(seed)
    tau_m_s = tau_m_ms / 1000.0
    t_ref_s = t_ref_ms / 1000.0
    tau_syn_s = tau_syn_ms / 1000.0
    dt_s = DT_US / 1_000_000.0
    steps = window_us // DT_US
    i0 = _rheobase_current(mean_rate_hz, tau_m_s, v_th, t_ref_s) * i_scale
    voltage = [rng.random() * v_th * 0.98 for _ in range(neurons)]
    bias = [i0 * (1.0 + 0.04 * (rng.random() - 0.5) * 2.0) for _ in range(neurons)]
    i_syn = [0.0] * neurons
    ref_left = [0.0] * neurons
    last_spike = [None] * neurons  # type: list[int | None]
    n_proj = max(4, neurons // 8)
    projections: list[tuple[float, list[tuple[int, float]]]] = []
    for t_ms in kernel_ms:
        hits = rng.sample(range(neurons), min(n_proj, neurons))
        weights = [(idx, 0.4 + 0.4 * rng.random()) for idx in hits]
        projections.append((t_ms / 1000.0, weights))
    spikes: list[tuple[int, int]] = []
    k_idx = 0
    decay_s = math.exp(-dt_s / tau_syn_s)
    decay_m = math.exp(-dt_s / tau_m_s)
    t_s = 0.0
    for step in range(steps):
        t_us = step * DT_US
        while k_idx < len(projections) and projections[k_idx][0] <= t_s + 1e-12:
            for idx, weight in projections[k_idx][1]:
                i_syn[idx] += weight
            k_idx += 1
        for idx in range(neurons):
            if ref_left[idx] > 0.0:
                ref_left[idx] -= dt_s
                voltage[idx] = 0.0
                i_syn[idx] *= decay_s
                continue
            i_syn[idx] *= decay_s
            current = bias[idx] + i_syn[idx]
            voltage[idx] = current + (voltage[idx] - current) * decay_m
            if voltage[idx] >= v_th:
                spikes.append((t_us, idx))
                last_spike[idx] = t_us
                voltage[idx] = 0.0
                ref_left[idx] = t_ref_s
        t_s += dt_s
    return spikes, voltage, bias, last_spike


def _fits_refractory(
    neuron_id: int,
    t_us: int,
    last_by_neuron: Mapping[int, int],
    gap_us: int = SAME_NEURON_GAP_US,
) -> bool:
    prev = last_by_neuron.get(neuron_id)
    return prev is None or t_us - prev >= gap_us


def _pad_trim_to_budget(
    spikes: list[tuple[int, int]],
    expected: int,
    neurons: int,
    window_us: int,
    voltage: Sequence[float],
    bias: Sequence[float],
    last_spike: Sequence[int | None],
    v_th: float,
    tau_m_ms: float,
    t_ref_ms: float,
    forbidden_us: set[int],
) -> list[tuple[int, int]]:
    """Keep times LIF-derived; only add/drop to land on the ±1 spike budget."""

    spikes = sorted(set(spikes), key=lambda item: (item[0], item[1]))
    if abs(len(spikes) - expected) <= SPIKE_BUDGET_TOL:
        return spikes
    if len(spikes) > expected + SPIKE_BUDGET_TOL:
        keep = expected if expected > 0 else 1
        return spikes[:keep]

    tau_m_s = tau_m_ms / 1000.0
    t_ref_us = int(round(t_ref_ms * 1000.0))
    occupied = {(t_us, nid) for t_us, nid in spikes}
    last_by_neuron = {nid: t_us for t_us, nid in spikes}
    last_times: list[int | None] = list(last_spike)
    order = sorted(range(neurons), key=lambda nid: voltage[nid], reverse=True)
    guard = 0
    while len(spikes) < expected and guard < neurons * 8:
        guard += 1
        added = False
        for nid in order:
            prev = last_times[nid] if last_times[nid] is not None else last_by_neuron.get(nid)
            t0 = 0 if prev is None else prev + t_ref_us
            v0 = 0.0 if prev is not None else voltage[nid]
            t_us = _first_passage_us(v0, bias[nid], v_th, tau_m_s, t0, window_us)
            if t_us is None:
                continue
            if t_us in forbidden_us:
                t_us += DT_US
            if t_us > window_us or (t_us, nid) in occupied:
                continue
            if not _fits_refractory(nid, t_us, last_by_neuron):
                continue
            spikes.append((t_us, nid))
            occupied.add((t_us, nid))
            last_by_neuron[nid] = t_us
            last_times[nid] = t_us
            added = True
            if len(spikes) >= expected:
                break
        if not added:
            break
    spikes = sorted(set(spikes), key=lambda item: (item[0], item[1]))
    if len(spikes) > expected + SPIKE_BUDGET_TOL:
        spikes = spikes[:expected]
    return spikes


def _calibrate_spikes(
    neurons: int,
    mean_rate_hz: float,
    window_us: int,
    seed: int,
    kernel_ms: Sequence[float],
    tau_m_ms: float,
    v_th: float,
    t_ref_ms: float,
    tau_syn_ms: float,
    forbidden_us: set[int],
) -> list[tuple[int, int]]:
    expected = expected_spikes(neurons, mean_rate_hz, window_us / 1000.0)
    lo, hi = 0.8, 3.0
    best: list[tuple[int, int]] = []
    best_state: tuple[list[float], list[float], list[int | None]] | None = None
    best_err = 10**9
    scale = 1.0
    for _ in range(14):
        scale = (lo + hi) / 2.0
        spikes, voltage, bias, last_spike = _simulate_cuba(
            neurons,
            mean_rate_hz,
            window_us,
            seed,
            scale,
            kernel_ms,
            tau_m_ms,
            v_th,
            t_ref_ms,
            tau_syn_ms,
        )
        err = abs(len(spikes) - expected)
        if err < best_err:
            best, best_err, best_state = spikes, err, (voltage, bias, last_spike)
        if err <= SPIKE_BUDGET_TOL:
            return sorted(spikes, key=lambda item: (item[0], item[1]))
        if len(spikes) < expected:
            lo = scale
        else:
            hi = scale
    voltage, bias, last_spike = best_state or ([0.0] * neurons, [v_th + 0.2] * neurons, [None] * neurons)
    return _pad_trim_to_budget(
        best,
        expected,
        neurons,
        window_us,
        voltage,
        bias,
        last_spike,
        v_th,
        tau_m_ms,
        t_ref_ms,
        forbidden_us,
    )


def _select_excerpt(
    spikes: Sequence[tuple[int, int]],
    cap: int,
    forbidden_us: set[int],
    window_us: int,
    neurons: int,
) -> list[dict[str, int]]:
    usable = [(t_us, nid) for t_us, nid in spikes if t_us not in forbidden_us]
    if not usable:
        usable = list(spikes)
    usable = [
        (t_us, nid)
        for t_us, nid in usable
        if 0 <= t_us <= window_us and 0 <= nid < neurons
    ]
    usable.sort(key=lambda item: (item[0], item[1]))
    if not usable:
        raise RuntimeError("CUBA LIF produced no in-window spikes for excerpt")
    if len(usable) > cap:
        if cap <= 1:
            usable = [usable[len(usable) // 2]]
        else:
            picked: list[tuple[int, int]] = []
            seen: set[int] = set()
            for i in range(cap):
                idx = int(round(i * (len(usable) - 1) / (cap - 1)))
                if idx not in seen:
                    seen.add(idx)
                    picked.append(usable[idx])
            usable = picked
    last: dict[int, int] = {}
    excerpt: list[dict[str, int]] = []
    for t_us, nid in usable:
        if not _fits_refractory(nid, t_us, last):
            continue
        excerpt.append({"t_us": int(t_us), "neuron_id": int(nid)})
        last[nid] = t_us
    if not excerpt:
        t_us, nid = usable[0]
        excerpt = [{"t_us": int(t_us), "neuron_id": int(nid)}]
    return excerpt


def generate_lif_raster(
    neurons: int,
    mean_rate_hz: float,
    window_ms: float,
    seed: int,
    kernelized_event_times: Iterable[Any] | None = None,
    *,
    tau_m: float = 10.0,
    v_th: float = 1.0,
    refractory_ms: float = REFRACTORY_MS,
    tau_syn_ms: float = 2.0,
    excerpt_cap: int = EXCERPT_CAP,
    routing: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Simulate a current-based LIF population and emit a contract raster dict.

    `tau_m` is the membrane time constant in milliseconds. `kernelized_event_times`
    are optional synaptic-current injection times (ms, or dicts with t_rel_ms/t_us);
    they drive the membrane and are excluded from the excerpt when possible.
    """

    neurons = _as_int(neurons)
    mean_rate_hz = _finite(mean_rate_hz)
    window_ms = _finite(window_ms)
    seed = _as_int(seed)
    if neurons < 1:
        raise ValueError("neurons must be >= 1")
    if mean_rate_hz <= 0.0:
        raise ValueError("mean_rate_hz must be > 0")
    if not (WINDOW_MS_MIN <= window_ms <= WINDOW_MS_MAX):
        raise ValueError(f"window_ms must be in [{WINDOW_MS_MIN}, {WINDOW_MS_MAX}]")
    if refractory_ms <= 0.0:
        raise ValueError("refractory must be positive")
    window_us = int(round(window_ms * 1000.0))
    kernel_ms = _parse_kernel_times_ms(kernelized_event_times, window_ms)
    forbidden_us = {int(round(t_ms * 1000.0)) for t_ms in kernel_ms}
    spikes = _calibrate_spikes(
        neurons,
        mean_rate_hz,
        window_us,
        seed,
        kernel_ms,
        tau_m,
        v_th,
        refractory_ms,
        tau_syn_ms,
        forbidden_us,
    )
    n_spikes = len(spikes)
    expected = expected_spikes(neurons, mean_rate_hz, window_ms)
    if abs(n_spikes - expected) > SPIKE_BUDGET_TOL:
        raise RuntimeError(
            f"LIF spike count {n_spikes} outside ±{SPIKE_BUDGET_TOL} of budget {expected}"
        )
    excerpt = _select_excerpt(spikes, excerpt_cap, forbidden_us, window_us, neurons)
    route = json.loads(json.dumps(DEFAULT_ROUTING if routing is None else dict(routing)))
    window_ms_out: int | float = int(window_ms) if window_ms == int(window_ms) else window_ms
    return {
        "window_ms": window_ms_out,
        "window_s": window_ms_out / 1000.0,
        "neurons": neurons,
        "mean_rate_hz": mean_rate_hz if mean_rate_hz != int(mean_rate_hz) else int(mean_rate_hz),
        "spikes": n_spikes,
        "energy_pJ": n_spikes * PJ_PER_SPIKE,
        "energy_uJ": n_spikes * UJ_PER_SPIKE,
        "routing": route,
        "excerpt": excerpt,
    }


def raster_issues(
    raster: Mapping[str, Any],
    *,
    kernelized_event_times: Iterable[Any] | None = None,
) -> list[str]:
    """Return contract violations; empty means the raster is usable for TTF r13."""

    issues: list[str] = []
    try:
        window_ms = _finite(raster["window_ms"])
        window_s = _finite(raster["window_s"])
        neurons = _as_int(raster["neurons"])
        rate = _finite(raster["mean_rate_hz"])
        spikes = _as_int(raster["spikes"])
        energy_pj = _finite(raster["energy_pJ"])
        energy_uj = _finite(raster["energy_uJ"])
        excerpt = raster["excerpt"]
    except (KeyError, TypeError, ValueError) as exc:
        return [f"missing or invalid raster field: {exc}"]
    if not (WINDOW_MS_MIN <= window_ms <= WINDOW_MS_MAX):
        issues.append(f"window_ms {window_ms} outside {WINDOW_MS_MIN}-{WINDOW_MS_MAX}")
    if abs(window_s - window_ms / 1000.0) > WINDOW_S_TOL:
        issues.append(f"window_s {window_s} != window_ms/1000")
    expected = expected_spikes(neurons, rate, window_ms)
    if abs(spikes - expected) > SPIKE_BUDGET_TOL:
        issues.append(f"spikes {spikes} vs budget {expected}")
    if abs(energy_pj - spikes * PJ_PER_SPIKE) > ENERGY_PJ_TOL:
        issues.append("energy_pJ != spikes*23")
    if abs(energy_uj - spikes * UJ_PER_SPIKE) > ENERGY_UJ_TOL:
        issues.append("energy_uJ != spikes*23e-6")
    if not isinstance(excerpt, list) or not excerpt:
        issues.append("excerpt empty")
        return issues
    prev_t = -1
    last: dict[int, int] = {}
    window_us = window_ms * 1000.0
    for item in excerpt:
        if not isinstance(item, Mapping):
            issues.append("excerpt item not an object")
            continue
        try:
            t_us = _as_int(item["t_us"])
            nid = _as_int(item["neuron_id"])
        except (KeyError, TypeError, ValueError) as exc:
            issues.append(f"excerpt field: {exc}")
            continue
        if t_us < prev_t:
            issues.append("excerpt not sorted by t_us")
        if t_us != item["t_us"]:
            issues.append(f"t_us {item['t_us']!r} is not an integer")
        if not (0 <= t_us <= window_us):
            issues.append(f"t_us {t_us} outside window")
        if not (0 <= nid < neurons):
            issues.append(f"neuron_id {nid} out of range")
        if nid in last and t_us - last[nid] < SAME_NEURON_GAP_US:
            issues.append(f"same-neuron gap {nid}: {t_us - last[nid]} us")
        last[nid] = t_us
        prev_t = t_us
    kernel_ms = _parse_kernel_times_ms(kernelized_event_times, window_ms)
    if kernel_ms:
        kernel_us = {int(round(t * 1000.0)) for t in kernel_ms}
        excerpt_us = {int(item["t_us"]) for item in excerpt if isinstance(item, Mapping) and "t_us" in item}
        overlap = kernel_us & excerpt_us
        if kernel_us and overlap == kernel_us:
            issues.append("excerpt re-encodes every kernelized event time")
        elif kernel_us and len(overlap) / len(kernel_us) >= 0.8:
            issues.append(
                f"excerpt overlaps {len(overlap)}/{len(kernel_us)} kernel times (re-encode)"
            )
    routing = raster.get("routing")
    if not isinstance(routing, Mapping):
        issues.append("routing missing")
    else:
        table = routing.get("table")
        third = routing.get("third_factor")
        if not routing.get("source") or not routing.get("target"):
            issues.append("routing source/target blank")
        if not isinstance(table, list) or not table:
            issues.append("routing.table empty")
        if not isinstance(third, Mapping):
            issues.append("third_factor missing")
        else:
            tau_s = third.get("tau_e_s")
            tau_ms = third.get("tau_e_ms")
            if tau_s is not None and tau_ms is not None:
                if abs(_finite(tau_ms) / 1000.0 - _finite(tau_s)) > WINDOW_S_TOL:
                    issues.append("tau_e_ms/1000 != tau_e_s")
    return issues


def load_r12_kernels(path: str = "/tmp/batch-r12.jsonl") -> dict[str, list[float]]:
    """Load spike_events times per r12 id for independence checks."""

    kernels: dict[str, list[float]] = {}
    try:
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                rec_id = rec.get("id")
                events = rec.get("spike_events") or []
                times = []
                for event in events:
                    if isinstance(event, Mapping) and "t_rel_ms" in event:
                        times.append(float(event["t_rel_ms"]))
                if rec_id and times:
                    kernels[str(rec_id)] = times
    except OSError:
        kernels["ttf-r12-076"] = list(_R12_076_KERNEL_MS)
    return kernels


def _check_budget(
    label: str,
    neurons: int,
    rate: float,
    window_ms: float,
    seed: int,
    kernels: Iterable[Any] | None,
) -> tuple[bool, str, dict[str, Any]]:
    raster = generate_lif_raster(neurons, rate, window_ms, seed, kernels)
    issues = raster_issues(raster, kernelized_event_times=kernels)
    expected = expected_spikes(neurons, rate, window_ms)
    overlap_n = 0
    if kernels:
        kernel_us = {int(round(t * 1000.0)) for t in _parse_kernel_times_ms(kernels, window_ms)}
        excerpt_us = {int(item["t_us"]) for item in raster["excerpt"]}
        overlap_n = len(kernel_us & excerpt_us)
    status = "PASS" if not issues else "FAIL"
    detail = (
        f"{label} n={neurons} rate={rate:g} window_ms={window_ms:g} "
        f"spikes={raster['spikes']} budget={expected} excerpt={len(raster['excerpt'])} "
        f"kernel_overlap={overlap_n} {status}"
    )
    if issues:
        detail += " :: " + "; ".join(issues)
    return not issues, detail, raster


def self_check(stream: Any = None) -> int:
    """Print PASS/FAIL for five r12 budgets and three r13 candidate budgets."""

    out = sys.stdout if stream is None else stream
    kernels_by_id = load_r12_kernels()
    fallback = list(_R12_076_KERNEL_MS)
    ok = True
    lines: list[str] = []
    for offset, (label, neurons, rate, window_ms) in enumerate(R12_BUDGETS):
        kernels = kernels_by_id.get(label, fallback)
        passed, detail, _raster = _check_budget(
            label, neurons, rate, window_ms, seed=13000 + offset, kernels=kernels
        )
        ok = ok and passed
        lines.append(detail)
    for offset, (label, neurons, rate, window_ms) in enumerate(R13_CANDIDATE_BUDGETS):
        passed, detail, _raster = _check_budget(
            label, neurons, rate, window_ms, seed=13100 + offset, kernels=None
        )
        ok = ok and passed
        lines.append(detail)
    for line in lines:
        print(line, file=out)
    print("ALL PASS" if ok else "ALL FAIL", file=out)
    return 0 if ok else 1


def sample_raster(seed: int = 13064) -> dict[str, Any]:
    """n=64, 40 Hz, 25 ms — r12-076 budget with an independent LIF excerpt."""

    return generate_lif_raster(64, 40, 25, seed)


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--sample" in args:
        print(json.dumps(sample_raster(), indent=2, sort_keys=False))
        args = [item for item in args if item != "--sample"]
        if not args:
            return 0
    return self_check()


if __name__ == "__main__":
    raise SystemExit(main())
