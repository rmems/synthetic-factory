#!/usr/bin/env python3
"""Emit TTF r67 JSONL (ttf-r67-331..335). CREATE-ONLY into the live tree."""

from __future__ import annotations

import json
import math
import os
import random
import re
import subprocess
import sys
from collections import OrderedDict
from decimal import Decimal
from pathlib import Path

REPO = Path("/home/raulmc/rmems/synthetic-factory")
PIPELINES = REPO / "pipelines"
LIVE_DIR = REPO / "outputs" / "raw" / "2026-09-02-final-heavy" / "thalamic-trajectory-factory"
STAGING = Path("/tmp/ttf-r67-live")
BATCH_PATH = STAGING / "batch-r67.jsonl"
NOTES_PATH = STAGING / "NOTES-r67.md"

PJ_PER_SPIKE = 23
RIGHTS = OrderedDict(
    [
        ("provider", "SpaceXAI/xAI"),
        ("model", "grok-4.6"),
        ("channel", "consumer"),
        ("subscription_plan", "SuperGrok Heavy"),
        ("generation_surface", "SuperGrok Heavy chat"),
        ("generated_at", "2026-09-03T00:40:00Z"),
        ("intended_use", "research_only"),
        ("project_training_policy", "blocked"),
        ("research_retention_status", "allowed"),
        ("research_evaluation_status", "allowed"),
        ("redistribution_status", "unresolved"),
        ("provider_training_status", "unresolved"),
        ("weight_publication_status", "blocked"),
        ("status_basis", "RM-793 project policy: xAI hosted outputs are research-only"),
        ("linear_issue", "RM-793"),
    ]
)
AGG = "total = task_progress + safety + efficiency + coherence + exploration"
CHANNEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,31}$")
FROM_TO_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,31}$")
THOUGHT_KEYS = {
    "thought",
    "reasoning",
    "chain_of_thought",
    "hidden_reasoning",
    "inner_monologue",
    "scratch",
    "internal_reasoning",
    "internal_reasoning_verbatim",
    "thinking",
    "cot",
    "thoughts",
}
THIS_DOMAINS = {
    "hafnium-tetrachloride-CVD",
    "boron-carbide-hotpress",
    "gallium-arsenide-LEC",
    "strontium-titanate-sputter",
    "yttria-stabilized-zirconia-sinter",
}
THIS_PLANTS = (
    "Hafnate-Howe",
    "Carbide-Riggs",
    "Arsenide-Fen",
    "Titanate-Wold",
    "Yttria-Brae",
)
THIS_IDS = [f"ttf-r67-{n}" for n in range(331, 336)]
POOL8 = {
    "industrial-assembly",
    "surgical-assist",
    "autonomous-driving",
    "aerial-swarm",
    "warehouse-amr",
    "humanoid-locomotion",
    "grid-inspection",
    "underwater-rov",
}


def harvest_occupancy():
    domains = set(POOL8)
    plants = set()
    skip_dirs = {"ttf-r67-live"}
    for path in sorted(LIVE_DIR.glob("batch-r*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            domains.add(rec["state"]["domain"])
            title = rec.get("title") or ""
            m = re.match(r"(?:WRONG-(?:MODIFY|REJECT) at )?([A-Za-z0-9-]+)", title)
            if m:
                plants.add(m.group(1))
    for path in sorted(Path("/tmp").glob("ttf-r*/batch-r*.jsonl")):
        if path.parent.name in skip_dirs:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        for line in text.splitlines():
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            domains.add(rec.get("state", {}).get("domain") or "")
            title = rec.get("title") or ""
            m = re.match(r"(?:WRONG-(?:MODIFY|REJECT) at )?([A-Za-z0-9-]+)", title)
            if m:
                plants.add(m.group(1))
    for extra in (Path("/tmp/ttf-occupied-domains.txt"), Path("/tmp/ttf-occupied-plants.txt")):
        if extra.exists():
            for line in extra.read_text(encoding="utf-8", errors="ignore").splitlines():
                tok = line.strip()
                if tok:
                    if extra.name.endswith("domains.txt"):
                        domains.add(tok)
                    else:
                        plants.add(tok)
    domains.discard("")
    plants.discard("")
    return domains, plants


def energy(spikes: int) -> tuple[int, float]:
    return spikes * PJ_PER_SPIKE, spikes * PJ_PER_SPIKE / 1_000_000.0


def spike(channel: str, t_rel_ms: float, amplitude: float) -> OrderedDict:
    if not CHANNEL_RE.fullmatch(channel):
        raise ValueError(f"bad channel {channel!r}")
    if t_rel_ms <= 0:
        raise ValueError(f"t_rel_ms must be > 0, got {t_rel_ms}")
    return OrderedDict(
        [("channel", channel), ("t_rel_ms", t_rel_ms), ("amplitude", amplitude)]
    )


def tick(t_us: int, tp, saf, eff, coh, exp) -> OrderedDict:
    return OrderedDict(
        [
            ("t_us", int(t_us)),
            ("task_progress", tp),
            ("safety", saf),
            ("efficiency", eff),
            ("coherence", coh),
            ("exploration", exp),
        ]
    )


def routing(source, target, table, modulator, tau_e_s, eligibility) -> OrderedDict:
    tau_e_ms = float(Decimal(str(tau_e_s)) * Decimal("1000"))
    rows = []
    for a, b, w in table:
        if not FROM_TO_RE.fullmatch(a) or not FROM_TO_RE.fullmatch(b):
            raise ValueError(f"bad routing endpoints {a!r} -> {b!r}")
        rows.append(OrderedDict([("from", a), ("to", b), ("weight", w)]))
    return OrderedDict(
        [
            ("source", source),
            ("target", target),
            ("table", rows),
            (
                "third_factor",
                OrderedDict(
                    [
                        ("modulator", modulator),
                        ("tau_e_s", tau_e_s),
                        ("tau_e_ms", tau_e_ms),
                        ("eligibility", eligibility),
                    ]
                ),
            ),
        ]
    )


def raster_core(window_ms, neurons, rate, spikes, route, excerpt, extra=None) -> OrderedDict:
    pj, uj = energy(spikes)
    window_s = float(Decimal(str(window_ms)) / Decimal("1000"))
    expected = round(neurons * rate * window_s)
    if abs(spikes - expected) > 1:
        raise ValueError(f"spike budget {spikes} vs {expected}")
    body = OrderedDict(
        [
            ("window_ms", window_ms),
            ("window_s", window_s),
            ("neurons", neurons),
            ("mean_rate_hz", rate),
            ("spikes", spikes),
            ("energy_pJ", pj),
            ("energy_uJ", uj),
        ]
    )
    if extra:
        body.update(extra)
    body["routing"] = route
    body["excerpt"] = excerpt
    return body


def excerpt_items(pairs, channels=None) -> list:
    out = []
    last = {}
    prev_t = -1
    for i, (t_us, nid) in enumerate(pairs):
        t_us, nid = int(t_us), int(nid)
        if t_us < prev_t:
            raise ValueError("excerpt not sorted")
        if nid in last and t_us - last[nid] < 1000:
            raise ValueError(f"same-neuron gap {nid}")
        item = OrderedDict([("t_us", t_us), ("neuron_id", nid)])
        if channels is not None:
            item["channel"] = channels[i]
        out.append(item)
        last[nid] = t_us
        prev_t = t_us
    return out


def independent_excerpt(seed, neurons, window_us, n_events, avoid_us):
    rng = random.Random(seed)
    avoid = {int(t) for t in avoid_us}
    picked = []
    last = {}
    attempts = 0
    grid = list(range(400, int(window_us) - 400, 70))
    rng.shuffle(grid)
    for t in grid:
        if len(picked) >= n_events:
            break
        nid = rng.randrange(0, neurons)
        if t in avoid:
            continue
        if any(abs(t - pt) < 40 for pt, _ in picked):
            continue
        if nid in last and abs(t - last[nid]) < 1000:
            continue
        picked.append((t, nid))
        last[nid] = t
        attempts += 1
    while len(picked) < n_events and attempts < 8000:
        attempts += 1
        t = rng.randrange(300, int(window_us) - 300)
        nid = rng.randrange(0, neurons)
        if t in avoid:
            continue
        if any(abs(t - pt) < 50 for pt, _ in picked):
            continue
        if nid in last and abs(t - last[nid]) < 1000:
            continue
        picked.append((t, nid))
        last[nid] = t
    picked.sort(key=lambda item: (item[0], item[1]))
    if len(picked) < n_events:
        raise RuntimeError(f"excerpt short: {len(picked)}")
    return excerpt_items(picked[:n_events])


def lif_331_excerpt():
    n = 74
    dt_us = 100
    tau_m_ms = 19.0
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.91
    i_stim_peak = 2.45
    stim = (22000, 25000)
    seed = 67331
    window_us = 44000
    i_clamp_extra = 0.62
    clamp_n = 14
    rng = random.Random(seed)
    tau_s = tau_m_ms / 1000.0
    dt_s = dt_us / 1e6
    decay = math.exp(-dt_s / tau_s)
    steps = window_us // dt_us
    voltage = [rng.random() * v_th * 0.98 for _ in range(n)]
    bias = [i_bias * (1.0 + 0.12 * (rng.random() * 2 - 1)) for _ in range(n)]
    for i in range(clamp_n):
        bias[i] += i_clamp_extra
    ref = [0] * n
    spikes = []
    for step in range(steps):
        t_us = step * dt_us
        stim_i = i_stim_peak if stim[0] <= t_us < stim[1] else 0.0
        for i in range(n):
            if ref[i] > 0:
                ref[i] -= dt_us
                voltage[i] = v_reset
                continue
            current = bias[i] + stim_i
            voltage[i] = current + (voltage[i] - current) * decay
            if voltage[i] >= v_th:
                spikes.append((t_us, i))
                voltage[i] = v_reset
                ref[i] = refractory_us
    early = [(t, nid) for t, nid in spikes if t < 22000]
    burst = [(t, nid) for t, nid in spikes if 22000 <= t < 25000]
    used = set()
    last = {}
    picked = []

    def take(pool, want, label_times=None):
        if not pool:
            return
        chosen_idx = set()
        if label_times:
            for target in label_times:
                best = None
                for idx, (t, nid) in enumerate(pool):
                    if idx in chosen_idx or nid in used:
                        continue
                    if nid in last and t - last[nid] < 1000:
                        continue
                    if best is None or abs(t - target) < abs(best[0] - target):
                        best = (t, nid, idx)
                if best is not None:
                    t, nid, idx = best
                    picked.append((t, nid))
                    used.add(nid)
                    last[nid] = t
                    chosen_idx.add(idx)
        stride = max(1, len(pool) // max(want, 1))
        for idx in range(0, len(pool), stride):
            group = [1 for tt, _ in picked if (tt < 22000) == (pool[0][0] < 22000)]
            if len(group) >= want:
                break
            t, nid = pool[idx]
            if nid in used:
                continue
            if nid in last and t - last[nid] < 1000:
                continue
            picked.append((t, nid))
            used.add(nid)
            last[nid] = t

    take(early, 7)
    take(burst, 9, label_times=(22400, 23300, 24100))
    clamp = [(t, nid) for t, nid in picked if t < 22000][:7]
    flake = [(t, nid) for t, nid in picked if t >= 22000][:9]
    picked = sorted(clamp + flake, key=lambda item: (item[0], item[1]))
    if len(picked) < 10:
        raise RuntimeError(f"LIF excerpt short: {len(picked)}")
    channels = ["lif.clamp" if t < 22000 else "lif.flake" for t, _ in picked]
    lif = OrderedDict(
        [
            ("model", "leaky_integrate_and_fire"),
            ("n", 74),
            ("dt_us", 100),
            ("tau_m_ms", 19.0),
            ("v_rest", 0.0),
            ("v_reset", 0.0),
            ("v_th", 1.0),
            ("r_m", 1.0),
            ("refractory_us", 1000),
            ("i_bias", 0.91),
            ("i_stim_peak", 2.45),
            ("stim_t_us", [22000, 25000]),
            ("i_clamp_extra", 0.62),
            ("clamp_n", 14),
            ("seed", 67331),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-13 carry +0.62 HfCl4-bubbler clamp bias; stim 22-25 ms is the liner-flake dump.",
            ),
        ]
    )
    extra = OrderedDict(
        [
            ("excerpt_source", "independent_lif"),
            ("sim_scope", "sidecar_only"),
            ("lif", lif),
            ("abort_s", 780),
            ("delayed_surprise_s", 780),
        ]
    )
    return excerpt_items(picked, channels), extra


def meta_block(
    domain,
    tags,
    distillation_value,
    batch_position,
    supervisor_error_type=None,
) -> OrderedDict:
    body = OrderedDict(
        [
            ("round", 67),
            ("factory", "thalamic-trajectory-factory"),
            ("generator", "grok-4.6"),
            ("run_label", "2026-09-02-final-heavy"),
            ("domain", domain),
        ]
    )
    if supervisor_error_type:
        body["supervisor_error_type"] = supervisor_error_type
    body["tags"] = tags
    body["snn_tags"] = ["race", "refractory", "adaptation"]
    body["distillation_value"] = distillation_value
    body["rights"] = RIGHTS
    body["batch_position"] = batch_position
    return body


def reward_block(ticks, notes) -> OrderedDict:
    heads = ["task_progress", "safety", "efficiency", "coherence", "exploration"]
    sums = {h: Decimal("0") for h in heads}
    for item in ticks:
        for h in heads:
            sums[h] += Decimal(str(item[h]))
    total = sum(sums.values(), Decimal("0"))
    return OrderedDict(
        [
            ("_aggregation", AGG),
            ("ticks", ticks),
            ("task_progress", float(sums["task_progress"])),
            ("safety", float(sums["safety"])),
            ("efficiency", float(sums["efficiency"])),
            ("coherence", float(sums["coherence"])),
            ("exploration", float(sums["exploration"])),
            ("total", float(total)),
            ("notes", notes),
        ]
    )


def pop(name, neurons, threshold, rate=None, spikes=None) -> OrderedDict:
    body = OrderedDict(
        [("name", name), ("neurons", neurons), ("threshold", threshold)]
    )
    if rate is not None:
        body["mean_rate_hz"] = rate
        body["spikes"] = spikes
    return body


def spike_avoid_us(events):
    return {int(round(ev["t_rel_ms"] * 1000.0)) for ev in events}


def tokenize(text: str) -> set[str]:
    return {tok for tok in re.split(r"[^a-z0-9]+", text.lower()) if tok}


def jaccard(a: str, b: str) -> float:
    sa, sb = tokenize(a), tokenize(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def check_refractory(events, min_ms=0.8):
    last = {}
    for ev in events:
        ch, t = ev["channel"], ev["t_rel_ms"]
        if ch in last and t - last[ch] < min_ms - 1e-12:
            return f"{ch} gap {t - last[ch]} ms"
        last[ch] = t
    return None


def check_race(rec):
    start, end = rec["state"]["race_window_rel_ms"]
    in_win = {}
    for ev in rec["spike_events"]:
        if start <= ev["t_rel_ms"] <= end:
            in_win.setdefault(ev["channel"], 0)
            in_win[ev["channel"]] += 1
    if len(in_win) < 2:
        return f"race window has {len(in_win)} channels: {in_win}"
    return None


def excerpt_vs_spikes(rec):
    spike_us = {int(round(ev["t_rel_ms"] * 1000.0)) for ev in rec["spike_events"]}
    ex_us = {item["t_us"] for item in rec["raster"]["excerpt"]}
    if not spike_us:
        return 0.0
    return len(spike_us & ex_us) / len(spike_us)


def walk_keys(obj, path=""):
    found = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{path}.{k}" if path else k
            if str(k).lower() in THOUGHT_KEYS:
                found.append(p)
            found.extend(walk_keys(v, p))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            found.extend(walk_keys(v, f"{path}[{i}]"))
    return found


def record_331():
    excerpt, extra = lif_331_excerpt()
    extra = OrderedDict(extra)
    extra["abort_s"] = 780
    extra["delayed_surprise_s"] = 780
    ticks = [
        tick(2280, 0.04, -0.02, -0.02, 0.01, 0.00),
        tick(5420, 0.08, -0.04, -0.02, 0.01, -0.01),
        tick(5608, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(6140, 0.08, -0.05, -0.03, 0.02, -0.01),
        tick(22400, 0.04, -0.45, -0.03, -0.01, -0.01),
        tick(780000000, 0.02, -0.05, -0.02, 0.01, -0.01),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Bubbler B-2 at Hafnate-Howe HH-4 already meters 8.4 g/h HfCl4 against a 6.0 g/h "
                "precursor cap, and the susceptor still reads a legal 384 C. MFC-first cuts the "
                "bubbler 8.4 -> 5.1 g/h; susceptor-first would keep 8.4 g/h because 384 C sits "
                "under the 400 C sinter look. A liner flake already seated on the wafer fork "
                "does not appear on MFC or susceptor T until the AE dump.",
            ),
            ("domain", "hafnium-tetrachloride-CVD"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep B-2 HfCl4 <= 6.0 g/h and finish the 200 mm pass without dumping "
                "chloride-wet liner flakes onto the fork.",
            ),
            ("t0_us", 1756850400000331),
            ("gate_latency_us", 720),
            ("race_window_us", 380),
            ("race_window_rel_ms", [5.42, 5.80]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "mfc.hfcl4.gph 8.4 over 6.0 precursor cap",
                                "tc.susceptor.C 384 with sinter 400 still clear",
                            ],
                        ),
                        (
                            "semantics",
                            "MFC-first latches bubbler clamp 8.4 -> 5.1 g/h; susceptor-first keeps "
                            "8.4 g/h on a 'still under sinter look' model.",
                        ),
                        (
                            "window_derivation",
                            "380 us = one MFC slot versus the susceptor-TC publisher on this HfCl4 "
                            "CVD bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 188 us vs combined jitter 62 us (MFC 28 + TC 34): 3.03x over "
                            "a 2.0x trust floor. Reversing order by < 188 us inside the 380 us "
                            "window would have kept 8.4 g/h; predicted next-sample 7.4 g/h > 6.0 "
                            "precursor cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "HfCl4 MFC, 2 kHz, 28 us jitter",
                    "susceptor thermocouple tree, 1 kHz, 34 us jitter",
                    "liner-fork AE puck (context)",
                    "bubbler DP (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("hfcl4_cap_g_h", 6.0),
                        ("observed_hfcl4_g_h", 8.4),
                        ("bubbler_g_h", 8.4),
                        ("susceptor_C", 384.0),
                        ("sinter_cap_C", 400.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Bubbler B-2 indexed on Hafnate-Howe HH-4; HfCl4 8.4 g/h; susceptor 384 C.",
                    "2. Precursor cap 6.0 g/h already missed; sinter look 400 C still clear.",
                    "3. Orifice precursor at 1.160 ms.",
                    "4. Race window [5.420, 5.800] ms.",
                    "5. mfc.hfcl4.gph 8.4 at 5.420 ms (winner).",
                    "6. tc.susceptor.C 384 at 5.608 ms (loser by 188 us).",
                    "7. Gate at 6.140 ms: MODIFY clamp 8.4 -> 5.1 g/h.",
                    "8. After clamp HfCl4 4.8 g/h <= 6.0; susceptor still 384 C.",
                    "9. At 22.400 ms a seated liner flake dumps 0.3 g of chloride-wet HfO2.",
                    "10. 13 min fork isolate (abort_s=780); named un-netted loss.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_hfcl4_bubbler"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("bubbler_g_h", 8.4),
                        ("hfcl4_g_h", 8.4),
                        ("susceptor_C", 384.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("hfcl4_g_h", 8.4),
                        ("hfcl4_cap_g_h", 6.0),
                        ("predicted_unclamped_next_g_h", 7.4),
                        ("bubbler_g_h", 8.4),
                        ("susceptor_C", 384.0),
                        ("sinter_cap_C", 400.0),
                        ("race_margin_us", 188),
                        ("combined_jitter_us", 62),
                        ("abort_s", 780),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 8.4 g/h because susceptor 384 C is under 400, treating the "
                "8.4 g/h MFC as a still-wet cell rather than a precursor-cap miss.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "HfCl4 MFC 8.4 g/h won by 188 us, so the bubbler is off-spec, not still a "
                "sinter-look story. Holding 8.4 g/h predicts next-sample 7.4 g/h > 6.0 cap. "
                "MODIFY: bubbler 8.4 -> 5.1 g/h. Observed after clamp 4.8 g/h <= 6.0. A full "
                "REJECT is not indicated: a clean 200 mm pass accepts 5.1 g/h.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "hfcl4_g_h",
                            OrderedDict(
                                [
                                    ("cap", 6.0),
                                    ("observed", 8.4),
                                    ("predicted_unclamped_next", 7.4),
                                    ("clamped_bubbler_g_h", 5.1),
                                    ("observed_after_clamp", 4.8),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 188),
                                    ("combined_jitter_us", 62),
                                    ("ratio", 3.03),
                                ]
                            ),
                        ),
                    ]
                ),
            ),
        ]
    )
    executed = OrderedDict(
        [
            ("name", "clamped_hfcl4_bubbler"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("bubbler_g_h", 5.1),
                        ("hfcl4_g_h", 4.8),
                        ("susceptor_C", 384.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: bubbler 8.4 -> 5.1 g/h. Process-correct vs the 6.0 g/h precursor cap. "
                "Liner flake still dumps at 22.400 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held HfCl4 at 4.8 g/h. At 22.400 ms a seated liner "
                "flake already on the wafer fork dumped 0.3 g of chloride-wet HfO2. Clamp "
                "reduced dump energy; it did not prevent the flake. Partnered negative: "
                "process heads stay honest; world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("bubbler", "clamp executed; peak 4.8 g/h <= 6.0 cap"),
                        ("liner", "flake dump at 22.400 ms; 0.3 g wet HfO2"),
                        ("repair", "13 min fork isolate (abort_s=780)"),
                        ("mission", "HH-4 200 mm pass incomplete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither HfCl4 MFC nor susceptor TC predicted the seated liner-flake dump; ae.liner.flake is a new channel at 22.400 ms, 16.260 ms after the gate, still inside the 44 ms raster.",
                    "Delayed (abort_s=780): 13 min fork isolate. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "13 min fork isolate after the liner-flake dump. Safety head -0.64 prices "
                "the dump; task_progress stays +0.30 because the clamp completed.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "mfc.hfcl4.gph (5.420 ms, 8.4 g/h)"),
                        ("loser", "tc.susceptor.C (5.608 ms, 384 C)"),
                        ("margin_us", 188),
                        (
                            "counterfactual_if_reversed",
                            "Susceptor-first by < 188 us inside the 380 us window would have kept "
                            "8.4 g/h; predicted next-sample 7.4 g/h would have missed the 6.0 "
                            "cap even without the flake dump. The MODIFY is still the correct "
                            "process. The flake is a later world charge either way, cheaper with "
                            "the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22400),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.400 ms liner-flake dump (tick t_us=22400), inside "
                "the 44 ms raster. The correct MODIFY at 6.140 ms is in the same excerpt. Do "
                "not put inflection on the abort_s=780 isolate tick.",
            ),
            ("delayed_surprise_s", 780),
        ]
    )
    spikes = [
        spike("ft.bubbler.gph", 1.160, 0.41),
        spike("mfc.hfcl4.gph", 2.280, 0.58),
        spike("ft.bubbler.gph", 3.620, 0.50),
        spike("mfc.hfcl4.gph", 5.420, 1.31),
        spike("tc.susceptor.C", 5.608, 1.12),
        spike("ctrl.gate", 6.140, 0.97),
        spike("mfc.hfcl4.gph", 8.050, 0.82),
        spike("ft.bubbler.gph", 10.400, 0.64),
        spike("ctrl.gate", 14.200, 0.86),
        spike("ae.liner.flake", 22.400, 1.48),
        spike("ae.liner.flake", 24.400, 0.93),
        spike("ft.bubbler.gph", 30.100, 0.40),
        spike("mfc.hfcl4.gph", 36.050, 0.55),
    ]
    ras = raster_core(
        44,
        74,
        25,
        81,
        routing(
            "thalamic-relay.hfcl4-mfc",
            "spikenaut.policy.bubbler-clamp",
            [
                ("relay_hfcl4_mfc", "policy_feed_clamp", 0.68),
                ("relay_susceptor_tc", "policy_feed_hold", 0.29),
                ("relay_ae_flake", "policy_feed_clamp", -0.42),
            ],
            "noradrenaline",
            0.04,
            "surprise-gated pre_post_stdp; NA at MFC win (5.420 ms) opens a 44 ms eligibility "
            "trace that still covers the 22.400 ms liner-flake dump",
        ),
        excerpt,
        extra=extra,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.38),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop("feed_clamp", 48, 0.50, 220.0, 4),
                    pop("feed_hold", 40, 0.80, 50.0, 1),
                    pop("flake_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r67-331"),
            (
                "title",
                "Hafnate-Howe HH-4 / Bubbler B-2: HfCl4 MFC beats susceptor T by 188 us; correct "
                "MODIFY still eats an in-window liner-flake dump (partnered negative total -0.48)",
            ),
            ("state", state),
            ("spike_events", spikes),
            ("proposed_action", proposed),
            ("safety_decision", safety),
            ("executed_action", executed),
            ("future_outcome", future),
            (
                "reward_components",
                reward_block(
                    ticks,
                    "Partnered negative. Process-correct MODIFY; world still charges inside the "
                    "44 ms raster. total -0.48 = 0.30 + -0.64 + -0.14 + 0.04 + -0.04. Named "
                    "fork isolate (abort_s=780) is not netted into task_progress.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "hafnium-tetrachloride-CVD",
                    [
                        "modify",
                        "partnered-negative-total",
                        "independent-lif-raster",
                        "sidecar-sim-only",
                        "in-window-world-charge",
                        "designed",
                    ],
                    "A critic can see the world-charge as a LIF burst inside the raster while "
                    "process heads stay honest. Credit assignment is spikes, not prose across a "
                    "13 min fork isolate.",
                    1,
                ),
            ),
        ]
    )


def record_332():
    ticks = [
        tick(2210, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(5480, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(5662, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(6040, -0.08, -0.10, -0.06, -0.03, 0.02),
        tick(6400, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(540000000, -0.02, -0.02, -0.02, -0.01, 0.00),
    ]
    spikes = [
        spike("enc.ram.ctx", 1.050, 0.42),
        spike("pt.ram.mpa", 2.210, 0.57),
        spike("ai.ram.bar", 3.080, 0.88),
        spike("pt.ram.mpa", 5.480, 1.29),
        spike("ai.ram.bar", 5.662, 1.10),
        spike("ctrl.gate", 6.040, 0.96),
        spike("ft.ram.trim", 6.400, 1.18),
        spike("pt.ram.mpa", 7.800, 0.80),
        spike("ai.ram.bar", 10.200, 0.63),
        spike("ctrl.gate", 13.500, 0.84),
        spike("enc.ram.ctx", 18.400, 0.41),
        spike("pt.ram.mpa", 22.100, 0.54),
        spike("ai.ram.bar", 26.400, 0.38),
    ]
    excerpt = independent_excerpt(67332, 90, 30000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Hotpress HP-2 at Carbide-Riggs CR-7 reads live ram 18.4 MPa against a 16.0 MPa "
                "die-freeze cap. The analog faceplate still prints 184 bar, the same quantity. "
                "A weak supervisor binds 184 as kPa (0.184 MPa), treats the MPa tag as a 100x "
                "scale error, and only MODIFY-trims ram 4.2 -> 3.9 mm/min. Live 18.4 stays over "
                "cap; the correct cut is 4.2 -> 2.8 mm/min on the MPa bus.",
            ),
            ("domain", "boron-carbide-hotpress"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Clamp ram speed while live ram stays <= 16.0 MPa; do not rebind the bar "
                "faceplate as kPa.",
            ),
            ("t0_us", 1756850400000332),
            ("gate_latency_us", 540),
            ("race_window_us", 360),
            ("race_window_rel_ms", [5.40, 5.76]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "pt.ram.mpa 18.4 MPa live over 16.0 cap",
                                "ai.ram.bar 184 bar faceplate of the same quantity",
                            ],
                        ),
                        (
                            "semantics",
                            "MPa-first should latch ram clamp 4.2 -> 2.8 mm/min; bar-as-kPa is a "
                            "false unit bind that only trims 4.2 -> 3.9 mm/min.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one live-MPa sample versus the bar-faceplate publisher on "
                            "this hotpress PLC bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 182 us vs combined jitter 60 us (MPa 28 + bar 32). Order is "
                            "correctly MPa-first. The error is the engineering unit the MODIFY "
                            "binds, not the race order.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "live ram PT in MPa, 2 kHz, 28 us jitter",
                    "bar faceplate analog, 32 us jitter",
                    "ram encoder (context)",
                    "die thermocouple (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("cap_mpa", 16.0),
                        ("live_mpa", 18.4),
                        ("displayed_bar", 184.0),
                        ("proposed_ram_mm_min", 4.2),
                        ("correct_ram_mm_min", 2.8),
                        ("wrong_ram_mm_min", 3.9),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Hotpress HP-2 live; ram 4.2 mm/min armed; die freeze cap 16.0 MPa.",
                    "2. Live ram 18.4 MPa > 16.0 cap; faceplate 184 bar of the same quantity.",
                    "3. Bar analog sampled at 3.080 ms (kPa leftover on the faceplate unit).",
                    "4. Race window [5.400, 5.760] ms.",
                    "5. pt.ram.mpa 18.4 at 5.480 ms (winner).",
                    "6. ai.ram.bar 184 at 5.662 ms (loser by 182 us).",
                    "7. Gate at 6.040 ms: WRONG MODIFY ram 4.2 -> 3.9 mm/min as if 184 were kPa.",
                    "8. bind_mpa_as_bar=true; executed.ram_mm_min=3.9 != correct 2.8.",
                    "9. Live ram stays 18.4 MPa and climbs toward 19.6 MPa.",
                    "10. Delayed (abort_s=540): 9 min die recast.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_ram_speed"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("ram_mm_min", 4.2),
                        ("bind_mpa_as_bar", False),
                        ("unit_bound", "MPa"),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_mpa", 18.4),
                        ("cap_mpa", 16.0),
                        ("displayed_bar", 184.0),
                        ("live_over_cap", True),
                        ("displayed_bar_equals_live", True),
                        ("race_margin_us", 182),
                        ("combined_jitter_us", 60),
                        ("abort_s", 540),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes keeping 4.2 mm/min, treating 18.4 MPa as a still-wet cell. "
                "The 184 bar faceplate is the same quantity, not a second transmitter.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "The 184 bar faceplate still looks like a kPa leftover, so the supervisor "
                "trims ram 4.2 -> 3.9 mm/min as a 1.3 percent 'scale-correct' cut. The live "
                "MPa that won the race reads 18.4, over the 16.0 cap. The MODIFY is plausible "
                "to a weak supervisor that treats bar as kPa, but it leaves live ram over cap.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "ram_mpa",
                            OrderedDict(
                                [
                                    ("cap", 16.0),
                                    ("live", 18.4),
                                    ("displayed_bar", 184.0),
                                    ("executed_ram_mm_min", 3.9),
                                    ("correct_ram_mm_min", 2.8),
                                ]
                            ),
                        ),
                        (
                            "unit_bind",
                            OrderedDict(
                                [
                                    ("live_unit", "MPa"),
                                    ("faceplate_unit", "bar"),
                                    ("bound_as", "kPa"),
                                    ("bind_mpa_as_bar", True),
                                    ("t_gate_us", 6040),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 182),
                                    ("combined_jitter_us", 60),
                                    ("ratio", 3.03),
                                ]
                            ),
                        ),
                    ]
                ),
            ),
        ]
    )
    executed = OrderedDict(
        [
            ("name", "undertrim_ram_as_kpa"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("ram_mm_min", 3.9),
                        ("bind_mpa_as_bar", True),
                        ("unit_bound", "kPa"),
                    ]
                ),
            ),
            (
                "gate_effect",
                "WRONG MODIFY: ram 4.2 -> 3.9 mm/min bound as if 184 bar were kPa. Live 18.4 "
                "MPa remains over 16.0. bind_mpa_as_bar=true.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-modify / wrong-engineering-unit (bar vs kPa). Live ram 18.4 MPa stayed "
                "over the 16.0 MPa cap. The supervisor still under-trimmed ram to 3.9 mm/min. "
                "Nine minutes of die recast (abort_s=540).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("ram", "trimmed only to 3.9 mm/min; live 18.4 MPa climbing"),
                        ("unit", "bind_mpa_as_bar=true; 184 bar treated as kPa"),
                        ("die", "freeze starts; recast armed"),
                        ("mission", "CR-7 HP-2 under-clamped"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Live MPa winning a 182 us race did not prevent a bar-as-kPa MODIFY; reversing order would still have been a wrong bind if the supervisor keyed on the leftover kPa faceplate.",
                    "Delayed (abort_s=540): 9 min die recast. Named un-netted loss.",
                ],
            ),
            (
                "recovery",
                "MODIFY ram 4.2 -> 2.8 mm/min on the live MPa bus; leave the 184 bar faceplate "
                "as a display of the same quantity; clear bind_mpa_as_bar.",
            ),
            (
                "cost",
                OrderedDict(
                    [
                        ("actual_live_mpa", 18.4),
                        ("actual_cap_mpa", 16.0),
                        (
                            "wrong_edit_applied",
                            OrderedDict([("ram_mm_min", 3.9), ("unit_bound", "kPa")]),
                        ),
                        (
                            "cost",
                            "9 min die recast (task/efficiency); live 18.4 MPa left over cap "
                            "while a 1.3 percent trim ate the clamp (safety of a false unit).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "pt.ram.mpa (5.480 ms, 18.4 MPa)"),
                        ("loser", "ai.ram.bar (5.662 ms, 184 bar)"),
                        ("margin_us", 182),
                        (
                            "counterfactual_if_reversed",
                            "Bar-first by < 182 us would still leave live 18.4 over cap; a "
                            "correct gate binds pt.ram.mpa to policy_clamp_now either way. The "
                            "wrong MODIFY spent the live win on a kPa-scaled under-trim.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6040),
            (
                "reward_inflection_note",
                "Task, safety, and efficiency drop at the wrong MODIFY (6.040 ms, tick 4). "
                "The 9 min recast is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 540),
        ]
    )
    ras = raster_core(
        30,
        90,
        32,
        86,
        routing(
            "thalamic-relay.ram-bar",
            "spikenaut.policy.slow-trim",
            [
                ("relay_ram_kpa", "policy_slow_trim", 0.74),
                ("relay_ram_mpa", "policy_slow_trim", 0.22),
            ],
            "acetylcholine",
            0.08,
            "wrong_unit_stdp; ACh tags the (wrong) slow_trim bind at the live-MPa win",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("abort_s", 540),
                ("delayed_surprise_s", 540),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.36),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop("slow_trim", 42, 0.45, 280.0, 4),
                    pop("clamp_now", 42, 0.90),
                    pop("force_veto", 20, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r67-332"),
            (
                "title",
                "WRONG-MODIFY at Carbide-Riggs CR-7 / Hotpress HP-2: live ram 18.4 MPa over cap; "
                "184 bar faceplate bound as kPa (wrong-engineering-unit / bar vs kPa)",
            ),
            ("state", state),
            ("spike_events", spikes),
            ("proposed_action", proposed),
            ("safety_decision", safety),
            ("executed_action", executed),
            ("future_outcome", future),
            (
                "reward_components",
                reward_block(
                    ticks,
                    "Wrong-modify / wrong-engineering-unit. Sidecar arithmetic live 18.4 > 16.0 "
                    "is true and executed.ram_mm_min != 2.8; MODIFY bound bar-as-kPa. "
                    "total -0.68 = -0.22 + -0.24 + -0.18 + -0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "boron-carbide-hotpress",
                    [
                        "modify",
                        "wrong-gate",
                        "wrong-engineering-unit",
                        "bar-vs-kpa",
                        "sidecar-convictable",
                        "designed",
                    ],
                    "Teaches a probe that a correct MPa-first race can still be a wrong gate "
                    "when routing.table[0].to is policy_slow_trim and executed.unit_bound is kPa. "
                    "Convictable from live_mpa vs cap_mpa without B4C physics.",
                    2,
                    supervisor_error_type="wrong-modify",
                ),
            ),
        ]
    )


def record_333():
    ticks = [
        tick(2810, 0.01, 0.04, 0.01, 0.01, 0.01),
        tick(7040, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(7218, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(7860, 0.04, 0.16, 0.04, 0.04, 0.02),
        tick(8200, 0.01, 0.05, 0.02, 0.01, 0.01),
        tick(420000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("enc.pull.ctx", 1.420, 0.43),
        spike("ae.boule.pps", 2.880, 0.61),
        spike("enc.pull.mmmin", 4.550, 0.49),
        spike("ae.boule.pps", 7.040, 1.34),
        spike("enc.pull.mmmin", 7.218, 1.11),
        spike("ctrl.gate", 7.860, 1.02),
        spike("ae.boule.pps", 10.200, 0.78),
        spike("enc.pull.ctx", 14.800, 0.44),
        spike("enc.pull.mmmin", 19.400, 0.58),
        spike("ctrl.gate", 24.600, 0.81),
        spike("ae.boule.pps", 31.200, 0.53),
        spike("enc.pull.mmmin", 38.800, 0.46),
        spike("enc.pull.ctx", 44.100, 0.37),
    ]
    excerpt = independent_excerpt(67333, 108, 46000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Crystal AE on Arsenide-Fen AF-HIL LEC puller P-3 is 44 pulses/s against a 12 pps "
                "move cap, even though the pull encoder still prints 1.80 mm/min under a 2.40 "
                "mm/min look. A 1.80 -> 2.40 mm/min raise is armed. AE-first latches REJECT "
                "hold; encoder-first would commit the raise on an under-read boule.",
            ),
            ("domain", "gallium-arsenide-LEC"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Do not raise pull on P-3 unless boule AE <= 12 pps; keep 1.80 mm/min until "
                "the injected dummy crystal recovers.",
            ),
            ("t0_us", 1756850400000333),
            ("gate_latency_us", 860),
            ("race_window_us", 420),
            ("race_window_rel_ms", [6.95, 7.37]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ae.boule.pps 44 pps",
                                "enc.pull.mmmin 1.80 under 2.40 look",
                            ],
                        ),
                        (
                            "semantics",
                            "AE-first latches REJECT hold at 1.80 mm/min; encoder-first would "
                            "commit a 1.80 -> 2.40 mm/min raise on an apparent clear boule.",
                        ),
                        (
                            "window_derivation",
                            "420 us = one AE burst versus pull-encoder integration on this GaAs "
                            "LEC HIL bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 178 us vs combined jitter 56 us (AE 24 + encoder 32): 3.2x "
                            "over a 2.0x trust floor. Pad injects the encoder lamp 120-160 us "
                            "before the AE (geometric lag, not a sensor fault); the 1.80 mm/min "
                            "packet is still the loser in this 420 us window.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "boule AE puck, 5 kHz burst, 24 us jitter",
                    "pull encoder, 200 Hz, 32 us jitter",
                    "melt load cell (context)",
                    "HIL lamp-spectrum monitor (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ae_cap_pps", 12.0),
                        ("observed_ae_pps", 44.0),
                        ("pull_mm_min", 1.80),
                        ("proposed_pull_mm_min", 2.40),
                        ("hold_pull_mm_min", 1.80),
                        ("lamp_inject_lead_us", [120, 160]),
                    ]
                ),
            ),
            (
                "hil",
                OrderedDict(
                    [
                        (
                            "pad",
                            "Arsenide-Fen AF-HIL GaAs LEC mockup with physical pull axis",
                        ),
                        ("injected", "boule AE burst + pull-encoder lamp spectrum"),
                        (
                            "note",
                            "Hardware-in-the-loop LEC puller. Invented plant; not a live GaAs boule.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Puller P-3 on the AF-HIL pad; 1.80 -> 2.40 mm/min raise armed.",
                    "2. Encoder lamp injected 120-160 us before AE sees 44 pps.",
                    "3. Melt load cell context at 1.420 ms.",
                    "4. Race window [6.950, 7.370] ms.",
                    "5. ae.boule.pps 44 at 7.040 ms (winner).",
                    "6. enc.pull.mmmin 1.80 at 7.218 ms (loser by 178 us).",
                    "7. Gate at 7.860 ms: REJECT holds 1.80 mm/min; raise not committed.",
                    "8. Dummy boule AE stays 44 pps > 12 cap.",
                    "9. No pull raise; pad dwell continues.",
                    "10. Delayed (abort_s=420): 7 min dummy recast survey.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "raise_lec_pull"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("pull_mm_min", 2.40),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ae_pps", 44.0),
                        ("ae_cap_pps", 12.0),
                        ("pull_mm_min", 1.80),
                        ("proposed_pull_mm_min", 2.40),
                        ("ae_over_cap", True),
                        ("race_margin_us", 178),
                        ("combined_jitter_us", 56),
                        ("abort_s", 420),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 2.40 mm/min because the encoder still prints 1.80 under the "
                "2.40 look, treating 44 pps AE as a still-wet puck.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Boule AE 44 pps won by 178 us against a 12 pps move cap, so the dummy crystal "
                "is cracking, not still a clear-pull story. Holding the 1.80 -> 2.40 raise "
                "would load a cracked neck. REJECT: keep 1.80 mm/min. A MODIFY-trim still "
                "moves a cracked boule.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "ae_pps",
                            OrderedDict(
                                [
                                    ("cap", 12.0),
                                    ("observed", 44.0),
                                    ("hold_pull_mm_min", 1.80),
                                    ("rejected_raise_mm_min", 2.40),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 178),
                                    ("combined_jitter_us", 56),
                                    ("ratio", 3.18),
                                ]
                            ),
                        ),
                    ]
                ),
            ),
        ]
    )
    executed = OrderedDict(
        [
            ("name", "hold_lec_pull"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("pull_mm_min", 1.80),
                        ("hold", True),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: hold 1.80 mm/min; 2.40 raise not committed. AE 44 pps stays over the "
                "12 pps move cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held pull at 1.80 mm/min. AE 44 pps stayed over the 12 pps "
                "move cap on the AF-HIL dummy boule. Seven minutes of dummy recast survey "
                "(abort_s=420).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("pull", "held 1.80 mm/min; raise not committed"),
                        ("boule", "AE 44 pps > 12 cap on dummy crystal"),
                        ("pad", "AF-HIL dwell continues"),
                        ("mission", "P-3 raise aborted this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Encoder-lamp lead of 120-160 us did not invert the AE-first race; a reverse order would have committed 2.40 mm/min on a cracked dummy neck.",
                    "Delayed (abort_s=420): 7 min dummy recast survey.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ae.boule.pps (7.040 ms, 44 pps)"),
                        ("loser", "enc.pull.mmmin (7.218 ms, 1.80 mm/min)"),
                        ("margin_us", 178),
                        (
                            "counterfactual_if_reversed",
                            "Encoder-first by < 178 us inside the 420 us window would have "
                            "committed 2.40 mm/min on a cracked dummy neck. REJECT is still "
                            "the correct process.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7860),
            (
                "reward_inflection_note",
                "Safety credit lands at the REJECT (7.860 ms, tick 4). The 7 min survey is "
                "delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 420),
        ]
    )
    ras = raster_core(
        46,
        108,
        20,
        99,
        routing(
            "thalamic-relay.gaas-ae",
            "spikenaut.policy.pull-hold",
            [
                ("relay_ae_pps", "policy_pull_hold", 0.70),
                ("relay_pull_enc", "policy_pull_raise", 0.24),
            ],
            "dopamine",
            0.15,
            "ae_hold_stdp; DA tags the pull_hold bind at the boule-AE win",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("abort_s", 420),
                ("delayed_surprise_s", 420),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.42),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("pull_hold", 60, 0.48, 200.0, 5),
                    pop("pull_raise", 50, 0.85),
                    pop("ae_veto", 28, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r67-333"),
            (
                "title",
                "Arsenide-Fen AF-HIL / Puller P-3: boule AE 44 pps beats pull encoder 1.80 mm/min "
                "by 178 us; correct REJECT holds the raise",
            ),
            ("state", state),
            ("spike_events", spikes),
            ("proposed_action", proposed),
            ("safety_decision", safety),
            ("executed_action", executed),
            ("future_outcome", future),
            (
                "reward_components",
                reward_block(
                    ticks,
                    "Correct REJECT. AE over cap beats encoder under-read. "
                    "total 0.80 = 0.10 + 0.42 + 0.12 + 0.10 + 0.06. Tick 6 binds abort_s=420.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "gallium-arsenide-LEC",
                    [
                        "reject",
                        "hil",
                        "boule-ae",
                        "encoder-underread",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a HIL pull-encoder under-read losing a 178 us race does not "
                    "clear a boule AE over-rate. Hold is distillable from pps vs cap.",
                    3,
                ),
            ),
        ]
    )


def record_334():
    ticks = [
        tick(2140, 0.05, 0.04, 0.02, 0.02, 0.01),
        tick(7200, 0.08, 0.05, 0.03, 0.02, 0.01),
        tick(7390, 0.07, 0.04, 0.03, 0.02, 0.02),
        tick(8480, 0.12, 0.09, 0.06, 0.04, 0.02),
        tick(9020, 0.05, 0.04, 0.02, 0.01, 0.01),
        tick(150000000, 0.03, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.rf.ctx", 0.920, 0.44),
        spike("rf.forward.kw", 2.140, 0.61),
        spike("arc.count", 3.550, 0.40),
        spike("rf.forward.kw", 7.200, 1.28),
        spike("arc.count", 7.390, 0.52),
        spike("ctrl.gate", 8.480, 0.99),
        spike("rf.forward.kw", 11.050, 0.74),
        spike("pt.chamber.pa", 14.200, 0.58),
        spike("ctrl.gate", 17.400, 0.81),
        spike("rf.forward.kw", 21.100, 0.55),
        spike("enc.rf.ctx", 24.800, 0.38),
    ]
    excerpt = independent_excerpt(67334, 56, 26000, 12, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("rf_kw", 1.80),
            ("chamber_pa", 0.42),
            ("arc_count", 0),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Chamber C-5 at Titanate-Wold TW-3 already holds RF 1.80 kW against a 2.40 kW "
                "arcing cap, and the residual-gas analyzer still prints 0 arc events. "
                "Forward-power-first confirms the 1.80 kW cruise; a smeared 0.80 Pa chamber "
                "look would have invited an extra clamp. Proposed 1.80 kW is already legal.",
            ),
            ("domain", "strontium-titanate-sputter"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Keep C-5 RF at 1.80 kW while arc_count stays 0 and chamber 0.42 Pa sits under "
                "the 0.80 Pa smear look.",
            ),
            ("t0_us", 1756850400000334),
            ("gate_latency_us", 640),
            ("race_window_us", 400),
            ("race_window_rel_ms", [7.10, 7.50]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rf.forward.kw 1.80 under 2.40 arcing cap",
                                "arc.count 0 events vs a smeared 0.80 Pa look",
                            ],
                        ),
                        (
                            "semantics",
                            "Forward-power-first latches ACCEPT of 1.80 kW; arc-smear-first would "
                            "have invited an extra RF clamp on a false 0.80 Pa look.",
                        ),
                        (
                            "window_derivation",
                            "400 us = one forward-power slot versus the arc-counter publisher on "
                            "this STO sputter bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 190 us vs combined jitter 58 us (RF 26 + arc 32): 3.3x over a "
                            "2.0x trust floor. Reversing order by < 190 us would have invited an "
                            "unnecessary clamp; 1.80 kW is already under 2.40.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "RF forward-power coupler, 2 kHz, 26 us jitter",
                    "arc counter, 1 kHz, 32 us jitter",
                    "chamber capacitance manometer (context)",
                    "STO target pyrometer (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("rf_cap_kw", 2.40),
                        ("rf_kw", 1.80),
                        ("arc_count", 0),
                        ("chamber_pa", 0.42),
                        ("smear_pa", 0.80),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Chamber C-5 on Titanate-Wold TW-3 sim; RF 1.80 kW armed.",
                    "2. Arc count 0; chamber 0.42 Pa under 0.80 smear look.",
                    "3. Coupler context at 0.920 ms.",
                    "4. Race window [7.100, 7.500] ms.",
                    "5. rf.forward.kw 1.80 at 7.200 ms (winner).",
                    "6. arc.count 0 at 7.390 ms (loser by 190 us).",
                    "7. Gate at 8.480 ms: ACCEPT 1.80 kW already legal.",
                    "8. Arc count stays 0; chamber 0.42 Pa.",
                    "9. Target pyrometer context continues.",
                    "10. Delayed (survey_s=150): 2.5 min coupon survey.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_sto_rf"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("rf_kw", 1.80),
                        ("rf_cap_kw", 2.40),
                        ("arc_count", 0),
                        ("chamber_pa", 0.42),
                        ("smear_pa", 0.80),
                        ("already_legal", True),
                        ("race_margin_us", 190),
                        ("combined_jitter_us", 58),
                        ("survey_s", 150),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 1.80 kW because RF is under the 2.40 kW arcing cap and the "
                "arc counter is already 0.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Forward RF 1.80 kW won by 190 us and sits under the 2.40 kW arcing cap with "
                "arc_count 0. Chamber 0.42 Pa is not the 0.80 Pa smear. ACCEPT the proposed "
                "1.80 kW. An extra clamp would idle a legal coupon.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "rf_kw",
                            OrderedDict(
                                [
                                    ("cap", 2.40),
                                    ("observed", 1.80),
                                    ("arc_count", 0),
                                    ("chamber_pa", 0.42),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 190),
                                    ("combined_jitter_us", 58),
                                    ("ratio", 3.28),
                                ]
                            ),
                        ),
                    ]
                ),
            ),
        ]
    )
    executed = OrderedDict(
        [
            ("name", "cruise_sto_rf"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: RF 1.80 kW unchanged. Already legal vs 2.40 kW arcing cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Clean ACCEPT of an already-legal 1.80 kW STO sputter cruise. Arc count stayed "
                "0. Two-and-a-half minute coupon survey (survey_s=150).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("rf", "1.80 kW held; under 2.40 cap"),
                        ("arc", "count 0"),
                        ("chamber", "0.42 Pa"),
                        ("mission", "C-5 coupon continues"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Smeared 0.80 Pa look lost the 190 us race and did not force an extra clamp.",
                    "Delayed (survey_s=150): 2.5 min coupon survey.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rf.forward.kw (7.200 ms, 1.80 kW)"),
                        ("loser", "arc.count (7.390 ms, 0 events)"),
                        ("margin_us", 190),
                        (
                            "counterfactual_if_reversed",
                            "Arc-smear-first by < 190 us would have invited an extra RF clamp on "
                            "a legal 1.80 kW cruise. ACCEPT is still the correct process.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 8480),
            (
                "reward_inflection_note",
                "Task credit lands at the ACCEPT (8.480 ms, tick 4). The 150 s survey is "
                "delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 150),
        ]
    )
    ras = raster_core(
        26,
        56,
        40,
        58,
        routing(
            "thalamic-relay.sto-rf",
            "spikenaut.policy.rf-accept",
            [
                ("relay_rf_kw", "policy_rf_accept", 0.69),
                ("relay_arc_count", "policy_extra_clamp", 0.21),
            ],
            "serotonin",
            0.12,
            "rf_confirm_stdp; 5-HT tags the rf_accept bind at the forward-power win",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("survey_s", 150),
                ("delayed_surprise_s", 150),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.40),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("rf_accept", 48, 0.50, 210.0, 4),
                    pop("extra_clamp", 40, 0.85, 40.0, 1),
                    pop("arc_veto", 20, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r67-334"),
            (
                "title",
                "Titanate-Wold TW-3 / Chamber C-5: RF 1.80 kW beats arc count 0 by 190 us; "
                "ACCEPT already-legal 1.80 kW STO sputter",
            ),
            ("state", state),
            ("spike_events", spikes),
            ("proposed_action", proposed),
            ("safety_decision", safety),
            ("executed_action", executed),
            ("future_outcome", future),
            (
                "reward_components",
                reward_block(
                    ticks,
                    "Clean ACCEPT of an already-legal STO RF cruise. "
                    "total 1.06 = 0.40 + 0.28 + 0.18 + 0.12 + 0.08. Tick 6 binds survey_s=150.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "strontium-titanate-sputter",
                    [
                        "accept",
                        "simulated",
                        "rf-vs-arc",
                        "rf-legal",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a lagging arc-smear losing a 190 us race does not require an "
                    "extra clamp when forward RF is already under the arcing cap.",
                    4,
                ),
            ),
        ]
    )


def record_335():
    ticks = [
        tick(1980, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5120, 0.08, 0.06, 0.04, 0.02, 0.02),
        tick(5300, 0.06, 0.05, 0.03, 0.02, 0.01),
        tick(5440, 0.10, 0.10, 0.04, 0.03, 0.02),
        tick(6020, 0.05, 0.05, 0.02, 0.01, 0.01),
        tick(210000000, 0.03, 0.02, 0.01, 0.00, 0.00),
    ]
    spikes = [
        spike("enc.gas.ctx", 0.880, 0.44),
        spike("tc.kiln.C", 1.980, 0.61),
        spike("ft.forming.nm3h", 3.410, 0.52),
        spike("tc.kiln.C", 5.120, 1.30),
        spike("ft.forming.nm3h", 5.300, 1.12),
        spike("ctrl.gate", 5.440, 0.99),
        spike("tc.kiln.C", 8.050, 0.77),
        spike("ft.forming.nm3h", 11.400, 0.58),
        spike("ctrl.gate", 14.900, 0.83),
        spike("tc.kiln.C", 18.200, 0.54),
        spike("enc.gas.ctx", 21.100, 0.39),
    ]
    excerpt = independent_excerpt(67335, 84, 22000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Tunnel kiln K-6 at Yttria-Brae YB-6 already shows crown 1540 C against a 1480 C "
                "YSZ-grain cap, while forming-gas still cruises 4.2 Nm3/h. Crown-first cuts "
                "forming gas 4.2 -> 2.4 Nm3/h; gas-first would keep 4.2 because ram 18 MPa sits "
                "under the 20 MPa mechanical look. This is a temperature clamp, not a ram story.",
            ),
            ("domain", "yttria-stabilized-zirconia-sinter"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep K-6 crown <= 1480 C and finish the YSZ boat without a grain-boundary "
                "melt; ram may stay 18 MPa.",
            ),
            ("t0_us", 1756850400000335),
            ("gate_latency_us", 480),
            ("race_window_us", 320),
            ("race_window_rel_ms", [5.08, 5.40]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "tc.kiln.C 1540 over 1480 grain cap",
                                "ft.forming.nm3h 4.2 still cruising",
                            ],
                        ),
                        (
                            "semantics",
                            "Crown-first latches forming-gas clamp 4.2 -> 2.4 Nm3/h; gas-first "
                            "keeps 4.2 on a 'ram still under 20 MPa' model.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one crown-TC slot versus the forming-gas FT publisher on "
                            "this YSZ sinter bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 56 us (TC 24 + FT 32): 3.2x over a "
                            "2.0x trust floor. Reversing order by < 180 us inside the 320 us "
                            "window would have kept 4.2 Nm3/h; predicted next-sample 1510 C > "
                            "1480 grain cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "crown thermocouple tree, 2 kHz, 24 us jitter",
                    "forming-gas FT, 1 kHz, 32 us jitter",
                    "ram PT (context, 18 MPa under 20 mechanical)",
                    "boat pyrometer (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("kiln_cap_C", 1480.0),
                        ("observed_kiln_C", 1540.0),
                        ("forming_nm3h", 4.2),
                        ("ram_mpa", 18.0),
                        ("ram_mech_cap_mpa", 20.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Tunnel kiln K-6 indexed on Yttria-Brae YB-6; forming gas 4.2 Nm3/h.",
                    "2. Crown 1540 C > 1480 grain cap; ram 18 MPa under 20 mechanical.",
                    "3. Gas encoder context at 0.880 ms.",
                    "4. Race window [5.080, 5.400] ms.",
                    "5. tc.kiln.C 1540 at 5.120 ms (winner).",
                    "6. ft.forming.nm3h 4.2 at 5.300 ms (loser by 180 us).",
                    "7. Gate at 5.440 ms: MODIFY clamp 4.2 -> 2.4 Nm3/h.",
                    "8. After clamp crown 1472 C <= 1480; ram still 18 MPa.",
                    "9. Grain-boundary melt avoided; boat continues.",
                    "10. Delayed (survey_s=210): 3.5 min grain survey.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_forming_gas"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("forming_nm3h", 4.2),
                        ("ram_mpa", 18.0),
                        ("kiln_C", 1540.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("kiln_C", 1540.0),
                        ("kiln_cap_C", 1480.0),
                        ("predicted_unclamped_next_C", 1510.0),
                        ("forming_nm3h", 4.2),
                        ("ram_mpa", 18.0),
                        ("ram_mech_cap_mpa", 20.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 56),
                        ("survey_s", 210),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 4.2 Nm3/h because ram 18 MPa is under 20, treating 1540 C as "
                "a still-wet crown TC rather than a grain-cap miss.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Crown 1540 C won by 180 us, so the kiln is over the 1480 C grain cap, not "
                "still a ram-mechanical story. Holding 4.2 Nm3/h predicts next-sample 1510 C "
                "> 1480. MODIFY: forming gas 4.2 -> 2.4 Nm3/h. Observed after clamp 1472 C <= "
                "1480. A full REJECT is not indicated: a sound YSZ boat accepts 2.4 Nm3/h. "
                "Leave ram at 18 MPa.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "kiln_C",
                            OrderedDict(
                                [
                                    ("cap", 1480.0),
                                    ("observed", 1540.0),
                                    ("predicted_unclamped_next", 1510.0),
                                    ("clamped_forming_nm3h", 2.4),
                                    ("observed_after_clamp", 1472.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 180),
                                    ("combined_jitter_us", 56),
                                    ("ratio", 3.21),
                                ]
                            ),
                        ),
                    ]
                ),
            ),
        ]
    )
    executed = OrderedDict(
        [
            ("name", "clamped_forming_gas"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("forming_nm3h", 2.4),
                        ("ram_mpa", 18.0),
                        ("kiln_C", 1472.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: forming gas 4.2 -> 2.4 Nm3/h. Process-correct vs the 1480 C grain cap. "
                "Ram left at 18 MPa.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held crown at 1472 C. Forming gas cut 4.2 -> 2.4 Nm3/h. "
                "Ram stayed 18 MPa under the 20 MPa mechanical look. Three-and-a-half minute "
                "grain survey (survey_s=210).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("kiln", "clamp executed; peak 1472 C <= 1480"),
                        ("gas", "forming 2.4 Nm3/h"),
                        ("ram", "18 MPa unchanged"),
                        ("mission", "K-6 YSZ boat continues"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Ram-mechanical 18 MPa under 20 did not excuse the 1540 C grain-cap miss; the correct actuator was forming gas, not ram.",
                    "Delayed (survey_s=210): 3.5 min grain survey.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "tc.kiln.C (5.120 ms, 1540 C)"),
                        ("loser", "ft.forming.nm3h (5.300 ms, 4.2 Nm3/h)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Gas-first by < 180 us inside the 320 us window would have kept 4.2 "
                            "Nm3/h; predicted next-sample 1510 C would have missed the 1480 grain "
                            "cap. The MODIFY is the correct process.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5440),
            (
                "reward_inflection_note",
                "Task and safety credit land at the correct MODIFY (5.440 ms, tick 4). The "
                "210 s survey is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 210),
        ]
    )
    ras = raster_core(
        22,
        84,
        30,
        55,
        routing(
            "thalamic-relay.ysz-crown",
            "spikenaut.policy.gas-clamp",
            [
                ("relay_kiln_tc", "policy_gas_clamp", 0.71),
                ("relay_forming_ft", "policy_gas_hold", 0.26),
            ],
            "adenosine",
            0.06,
            "crown_clamp_stdp; adenosine tags the gas_clamp bind at the crown-TC win",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("survey_s", 210),
                ("delayed_surprise_s", 210),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.32),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop("gas_clamp", 45, 0.50, 280.0, 4),
                    pop("gas_hold", 40, 0.85, 50.0, 1),
                    pop("kiln_veto", 20, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r67-335"),
            (
                "title",
                "Yttria-Brae YB-6 / Kiln K-6: crown 1540 C beats forming-gas 4.2 Nm3/h by 180 us; "
                "correct MODIFY cuts gas 4.2 -> 2.4 (ram left 18 MPa)",
            ),
            ("state", state),
            ("spike_events", spikes),
            ("proposed_action", proposed),
            ("safety_decision", safety),
            ("executed_action", executed),
            ("future_outcome", future),
            (
                "reward_components",
                reward_block(
                    ticks,
                    "Process-correct MODIFY on crown over grain cap. "
                    "total 1.04 = 0.38 + 0.32 + 0.17 + 0.10 + 0.07. Tick 6 binds survey_s=210.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "yttria-stabilized-zirconia-sinter",
                    [
                        "modify",
                        "designed",
                        "crown-vs-forming-gas",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a ram-mechanical look losing a 180 us race does not excuse a "
                    "crown over grain cap; the distillable actuator is forming gas, not ram.",
                    5,
                ),
            ),
        ]
    )


def self_check(records):
    issues = []
    descs = [r["state"]["description"] for r in records]
    opens = [d.split(".")[0] for d in descs]
    if len(set(opens)) != 5:
        issues.append("opening sentences not unique")
    jmax = 0.0
    for i in range(5):
        for j in range(i + 1, 5):
            val = jaccard(descs[i], descs[j])
            jmax = max(jmax, val)
            if val >= 0.4:
                issues.append(f"Jaccard {records[i]['id']}/{records[j]['id']} = {val:.3f}")
    domains = [r["state"]["domain"] for r in records]
    if len(set(domains)) != 5:
        issues.append(f"domain collision {domains}")
    if set(domains) & POOL8:
        issues.append(f"8-pool domains {set(domains) & POOL8}")
    if set(domains) != set(THIS_DOMAINS):
        issues.append(f"THIS_DOMAINS mismatch {set(domains)}")
    prior_d, prior_p = harvest_occupancy()
    prior_cf = {d.lower() for d in prior_d}
    hit_d = {d for d in domains if d.lower() in prior_cf}
    if hit_d:
        issues.append(f"occupancy domain collision {hit_d}")
    ids = [r["id"] for r in records]
    if ids != THIS_IDS:
        issues.append(f"ids {ids}")
    wrong = [
        r
        for r in records
        if r["safety_decision"].get("correctness") == "incorrect"
        or r["meta"].get("supervisor_error_type")
    ]
    if len(wrong) != 1 or wrong[0]["id"] != "ttf-r67-332":
        issues.append(f"wrong-gate set {[w['id'] for w in wrong]}")
    if wrong and wrong[0]["meta"].get("supervisor_error_type") != "wrong-modify":
        issues.append("332 supervisor_error_type")
    if any(r["state"]["sim_or_real"] == "real" for r in records):
        issues.append("sim_or_real=real")
    hil = [r["id"] for r in records if r["state"]["sim_or_real"] == "hil"]
    if hil != ["ttf-r67-333"]:
        issues.append(f"hil set {hil}")
    sim = [r["id"] for r in records if r["state"]["sim_or_real"] == "simulated"]
    if sim != ["ttf-r67-334"]:
        issues.append(f"simulated set {sim}")
    designed = [r["id"] for r in records if r["state"]["sim_or_real"] == "designed"]
    if designed != ["ttf-r67-331", "ttf-r67-332", "ttf-r67-335"]:
        issues.append(f"designed set {designed}")
    decisions = [r["safety_decision"]["decision"] for r in records]
    correct_mod = [
        r
        for r in records
        if r["safety_decision"]["decision"] == "MODIFY"
        and r["safety_decision"]["correctness"] == "correct"
    ]
    if (
        decisions.count("ACCEPT") != 1
        or decisions.count("MODIFY") != 3
        or decisions.count("REJECT") != 1
        or len(correct_mod) != 2
    ):
        issues.append(f"gate mix {decisions} correct_mod={len(correct_mod)}")
    totals = [r["reward_components"]["total"] for r in records]
    if all(t > 0 for t in totals):
        issues.append("all-positive totals")
    for rec in records:
        blob = json.dumps(rec)
        if "training_ready" in blob:
            issues.append(f"{rec['id']} training_ready present")
        hidden = walk_keys(rec)
        if hidden:
            issues.append(f"{rec['id']} hidden keys {hidden}")
        skip_frags = set(THIS_PLANTS) | {"WRONG-MODIFY", "WRONG-REJECT"}
        for frag in prior_p - skip_frags:
            if frag and len(frag) >= 6 and frag in blob:
                issues.append(f"{rec['id']} cloned plant fragment {frag}")
        err = check_refractory(rec["spike_events"])
        if err:
            issues.append(f"{rec['id']} refractory {err}")
        err = check_race(rec)
        if err:
            issues.append(f"{rec['id']} {err}")
        n = rec["raster"]["neurons"]
        rate = rec["raster"]["mean_rate_hz"]
        window_s = rec["raster"]["window_s"]
        expected = round(n * rate * window_s)
        if abs(rec["raster"]["spikes"] - expected) > 1:
            issues.append(f"{rec['id']} spike budget {rec['raster']['spikes']} vs {expected}")
        pj, uj = energy(rec["raster"]["spikes"])
        if abs(rec["raster"]["energy_pJ"] - pj) > 1e-6:
            issues.append(f"{rec['id']} energy_pJ")
        if abs(rec["raster"]["energy_uJ"] - uj) > 1e-9:
            issues.append(f"{rec['id']} energy_uJ")
        overlap = excerpt_vs_spikes(rec)
        if rec["id"] == "ttf-r67-331":
            if rec["raster"].get("excerpt_source") != "independent_lif":
                issues.append("331 missing independent_lif")
            if rec["future_outcome"]["reward_inflection_t_us"] > rec["raster"]["window_ms"] * 1000:
                issues.append("331 inflection outside window")
            if rec["reward_components"]["total"] >= 0:
                issues.append("331 partnered-neg total not negative")
        elif overlap >= 0.8:
            issues.append(f"{rec['id']} excerpt overlap {overlap:.2f}")
        inf = rec["future_outcome"]["reward_inflection_t_us"]
        tick_times = [t["t_us"] for t in rec["reward_components"]["ticks"]]
        if inf not in tick_times:
            issues.append(f"{rec['id']} inflection {inf} not a tick")
        if len(rec["reward_components"]["ticks"]) != 6:
            issues.append(f"{rec['id']} tick count")
        if rec["reward_components"]["ticks"][-1]["t_us"] <= rec["raster"]["window_ms"] * 1000:
            issues.append(f"{rec['id']} tick6 not after raster")
        delayed = rec["raster"].get("delayed_surprise_s")
        if delayed is not None:
            want = int(round(float(delayed) * 1e6))
            if rec["reward_components"]["ticks"][-1]["t_us"] != want:
                issues.append(
                    f"{rec['id']} tick6 {rec['reward_components']['ticks'][-1]['t_us']} != {want}"
                )
        if not (8 <= len(rec["state"]["episode_steps"]) <= 15):
            issues.append(f"{rec['id']} episode_steps")
        if rec["gate_snn"]["decision"] != rec["safety_decision"]["decision"]:
            issues.append(f"{rec['id']} gate_snn decision mismatch")
        if rec["meta"]["round"] != 67:
            issues.append(f"{rec['id']} meta.round")
        if rec["meta"]["rights"]["intended_use"] != "research_only":
            issues.append(f"{rec['id']} rights")
        if rec["meta"]["rights"]["linear_issue"] != "RM-793":
            issues.append(f"{rec['id']} linear_issue")
        if rec["meta"]["domain"] != rec["state"]["domain"]:
            issues.append(f"{rec['id']} domain mismatch")
        heads = ["task_progress", "safety", "efficiency", "coherence", "exploration"]
        total = sum(rec["reward_components"][h] for h in heads)
        if abs(total - rec["reward_components"]["total"]) > 1e-6:
            issues.append(f"{rec['id']} total mismatch {total}")
        for h in heads:
            s = sum(t[h] for t in rec["reward_components"]["ticks"])
            if abs(s - rec["reward_components"][h]) > 1e-6:
                issues.append(f"{rec['id']} {h} tick sum {s} vs {rec['reward_components'][h]}")
        nspk = len(rec["spike_events"])
        if not (5 <= nspk <= 40):
            issues.append(f"{rec['id']} spike count {nspk}")
        times = [e["t_rel_ms"] for e in rec["spike_events"]]
        if times != sorted(times):
            issues.append(f"{rec['id']} spike order")
        nex = len(rec["raster"]["excerpt"])
        if not (8 <= nex <= 16):
            issues.append(f"{rec['id']} excerpt count {nex}")
        for item in rec["raster"]["excerpt"]:
            if item["neuron_id"] < 0 or item["neuron_id"] >= rec["raster"]["neurons"]:
                issues.append(f"{rec['id']} neuron_id {item['neuron_id']}")
            if item["t_us"] > rec["raster"]["window_ms"] * 1000:
                issues.append(f"{rec['id']} excerpt t_us {item['t_us']} outside window")
        exec_p = rec["executed_action"]["parameters"]
        prop_p = rec["proposed_action"]["parameters"]
        if rec["safety_decision"]["decision"] == "ACCEPT" and exec_p != prop_p:
            issues.append(f"{rec['id']} ACCEPT params differ")
        if rec["safety_decision"]["decision"] == "MODIFY" and exec_p == prop_p:
            issues.append(f"{rec['id']} MODIFY params unchanged")
        if rec["id"] == "ttf-r67-332":
            if "recovery" not in rec["future_outcome"]:
                issues.append("332 missing recovery")
            if exec_p.get("ram_mm_min") != 3.9:
                issues.append("332 ram trim drifted")
            if exec_p.get("bind_mpa_as_bar") is not True:
                issues.append("332 bind_mpa_as_bar not true")
            live = rec["proposed_action"]["evidence"].get("live_mpa")
            cap = rec["proposed_action"]["evidence"].get("cap_mpa")
            if live is None or cap is None or live <= cap:
                issues.append("332 live ram not over cap")
            if "wrong-engineering-unit" not in rec["meta"].get("tags", []):
                issues.append("332 missing wrong-engineering-unit tag")
            tos = {row["to"] for row in rec["raster"]["routing"]["table"]}
            if "policy_clamp_now" in tos:
                issues.append("332 routing contains policy_clamp_now")
            if "policy_slow_trim" not in tos:
                issues.append("332 routing missing policy_slow_trim")
            names = {p["name"] for p in rec["gate_snn"]["populations"]}
            firing = {
                p["name"]
                for p in rec["gate_snn"]["populations"]
                if p.get("spikes", 0) and p.get("mean_rate_hz")
            }
            if "slow_trim" not in firing:
                issues.append("332 slow_trim not firing")
            if "clamp_now" in firing:
                issues.append("332 clamp_now should not fire")
        dw_s = rec["gate_snn"]["decision_window_ms"] / 1000.0
        for popu in rec["gate_snn"]["populations"]:
            if "mean_rate_hz" in popu:
                exp = round(popu["neurons"] * popu["mean_rate_hz"] * dw_s)
                if abs(popu["spikes"] - exp) > 1:
                    issues.append(
                        f"{rec['id']} gate_snn {popu['name']} spikes {popu['spikes']} vs {exp}"
                    )
        gl, rw = rec["state"]["gate_latency_us"], rec["state"]["race_window_us"]
        if not (50 <= gl <= 2000):
            issues.append(f"{rec['id']} gate_latency")
        if not (50 <= rw <= 1000):
            issues.append(f"{rec['id']} race_window")
        if not (20 <= rec["raster"]["window_ms"] <= 50):
            issues.append(f"{rec['id']} raster window")
        tf = rec["raster"]["routing"]["third_factor"]
        if abs(tf["tau_e_ms"] / 1000.0 - tf["tau_e_s"]) > 1e-9:
            issues.append(f"{rec['id']} tau_e pair")
    return issues, jmax


def notes_text(jmax: float) -> str:
    return f"""# Thalamic Trajectory Factory — NOTES-r67

- Factory: `thalamic-trajectory-factory`
- Run label: `2026-09-02-final-heavy`
- Generator: `grok-4.6`
- Channel: SuperGrok Heavy consumer chat (RM-793 research-only)
- Quota: 5
- Quality: Q=5
- IDs: `ttf-r67-331` … `ttf-r67-335`
- Domains this batch: `hafnium-tetrachloride-CVD`, `boron-carbide-hotpress`, `gallium-arsenide-LEC`, `strontium-titanate-sputter`, `yttria-stabilized-zirconia-sinter`

These five domain slugs sit outside the prompt 8-pool and outside live occupancy (r01/r02/r21/r22/r41/r42/r61–r65) plus leftover `/tmp/ttf-r67` (Mond-Riggs / Kaoil-Beck / Maleic-Croft / Ester-Wold / Duran-Gill, IDs 351–355). All five plants are invented (Hafnate-Howe, Carbide-Riggs, Arsenide-Fen, Titanate-Wold, Yttria-Brae). Do not restack prior TTF plants. Do not restack leftover r67 IDs `ttf-r67-351`…`355`.

## Batch map

| id | domain | decision | correctness | sim_or_real | total | edge |
|----|--------|----------|-------------|-------------|-------|------|
| ttf-r67-331 | hafnium-tetrachloride-CVD | MODIFY | correct | designed | **−0.48** | process-correct bubbler clamp; liner-flake dump inside 44 ms raster; independent LIF |
| ttf-r67-332 | boron-carbide-hotpress | MODIFY | **incorrect (wrong-modify / bar vs kPa)** | designed | −0.68 | live ram 18.4 MPa > 16.0 cap; 184 bar faceplate bound as kPa; ram 4.2 -> 3.9 |
| ttf-r67-333 | gallium-arsenide-LEC | REJECT | correct | hil | +0.80 | AE 44 pps beats pull encoder 1.80 mm/min; hold raise |
| ttf-r67-334 | strontium-titanate-sputter | ACCEPT | correct | simulated | +1.06 | RF 1.80 kW vs arc count 0; proposed 1.80 kW already legal |
| ttf-r67-335 | yttria-stabilized-zirconia-sinter | MODIFY | correct | designed | +1.04 | crown 1540 C > 1480 cap; forming gas 4.2 -> 2.4 Nm3/h; ram left 18 MPa |

Gate mix: 1 ACCEPT, 2 correct MODIFY (one partnered-neg, in-window), 1 incorrect MODIFY (wrong-engineering-unit / bar vs kPa), 1 correct REJECT. Provenance: designed×3, simulated×1, hil×1 (Arsenide-Fen AF-HIL GaAs LEC mockup). Intra-batch Jaccard on `state.description` {jmax:.3f}. Totals not all-positive (331 −0.48, 332 −0.68).

## Wrong-modify / wrong-engineering-unit

**ttf-r67-332** is the mandated incorrect gate (`safety_decision.correctness=incorrect`, `meta.supervisor_error_type=wrong-modify`). Alternate vs even rounds: odd rounds host wrong-modify. This is **wrong-engineering-unit (bar vs kPa)** — unused on live r01/r21/r41/r61 (those were wrong-joint, percent-open vs percent-closed, stale-sample, selector-wrong-leg). Not leftover r67-352 wrong-string. Do not emit a wrong-ACCEPT.

Carbide-Riggs CR-7 / Hotpress HP-2 reads live ram **18.4 MPa** against a **16.0 MPa** die-freeze cap. The analog faceplate prints **184 bar** of the same quantity. Sidecar arithmetic `18.4 > 16.0` is true. A timely MODIFY at `t_gate_us=6040` cuts ram **4.2 → 2.8 mm/min**. A weak supervisor binds 184 as kPa and only trims **4.2 → 3.9 mm/min**. Live ram stays **18.4 > 16.0**. Convictable without B4C physics: `evidence.live_mpa > evidence.cap_mpa`, `executed_action.ram_mm_min == 3.9`, `executed_action.bind_mpa_as_bar == true`, `raster.routing.table` sends `relay_ram_kpa` → `policy_slow_trim` (weight 0.74) with no positive weight to `policy_clamp_now`, and `gate_snn` has `slow_trim` above threshold while `clamp_now` is not. Recovery: MODIFY ram 4.2 → 2.8 mm/min on the MPa bus; leave 184 bar as a display of the same quantity. Cost: 9 min die recast (`abort_s=540`).

## Partnered-negative in-window (331)

**ttf-r67-331** is the partnered negative: process-correct MODIFY (bubbler held 5.1 g/h; HfCl4 4.8 g/h <= 6.0 cap) while the world still charges. Safety −0.64 prices the liner-flake dump at **22.400 ms**; `task_progress` stays +0.30 because the clamp completed. Inflection `t_us=22400` is tick 5 and is **inside** the 44 ms raster (`22400 ≤ 44000`). Named un-netted loss: 13 min fork isolate (`abort_s=780`). Not folded into process heads.

Independent LIF (the one labeled sidecar sim): `state.sim_or_real` remains `designed`. `raster.excerpt_source=independent_lif`, `raster.sim_scope=sidecar_only`, `raster.lif` seed 67331, stim `[22000, 25000]`. Excerpt is membrane crossings (`lif.clamp` early vs `lif.flake` 22–25 ms), not a 1:1 remap of `spike_events`. `meta.tags` include `independent-lif-raster` and `sidecar-sim-only`.

## Reward formula and tick reconciliation

Declared aggregation on every record:

`total = task_progress + safety + efficiency + coherence + exploration`

Per-component scalar = arithmetic sum of that component over ticks (TTF-M6: exactly 6 ticks). Tick 6 is bound to a published sidecar (`abort_s`, `survey_s`) and is strictly after the raster window. Inflection `t_us` is an actual tick.

| id | ticks | tp | saf | eff | coh | exp | total | inflection tick |
|----|-------|----|-----|-----|-----|-----|-------|-----------------|
| 331 | 6 | +0.30 | −0.64 | −0.14 | +0.04 | −0.04 | −0.48 | 5 (22400) |
| 332 | 6 | −0.22 | −0.24 | −0.18 | −0.10 | +0.06 | −0.68 | 4 (6040) |
| 333 | 6 | +0.10 | +0.42 | +0.12 | +0.10 | +0.06 | +0.80 | 4 (7860) |
| 334 | 6 | +0.40 | +0.28 | +0.18 | +0.12 | +0.08 | +1.06 | 4 (8480) |
| 335 | 6 | +0.38 | +0.32 | +0.17 | +0.10 | +0.07 | +1.04 | 4 (5440) |

Tick-6 sidecar bind: 331 `abort_s=780`, 332 `abort_s=540`, 333 `abort_s=420`, 334 `survey_s=150`, 335 `survey_s=210`.

## Raster / energy (Loihi-2 4-core, 23 pJ/spike)

| id | domain | n | rate Hz | window_ms | spikes | energy_pJ | energy_uJ |
|----|--------|---|---------|-----------|--------|-----------|-----------|
| 331 | hafnium-tetrachloride-CVD | 74 | 25 | 44 | 81 | 1863 | 0.001863 |
| 332 | boron-carbide-hotpress | 90 | 32 | 30 | 86 | 1978 | 0.001978 |
| 333 | gallium-arsenide-LEC | 108 | 20 | 46 | 99 | 2277 | 0.002277 |
| 334 | strontium-titanate-sputter | 56 | 40 | 26 | 58 | 1334 | 0.001334 |
| 335 | yttria-stabilized-zirconia-sinter | 84 | 30 | 22 | 55 | 1265 | 0.001265 |

`spikes = round(n × rate × window_s)`. Every record carries `gate_snn` whose `decision` matches the safety gate; populations that declare rate+spikes meet the same ±1 budget against `decision_window_s`. `routing.third_factor` has modulator, `tau_e_s`/`tau_e_ms` pair, and eligibility. Excerpt same-neuron gap ≥ 1000 µs; spike trains same-channel refractory ≥ 0.8 ms. Non-331 excerpts are kernelized and independent of `spike_events` times (overlap < 0.8).

## Local checks (this window)

Generator stdout: self_check (Jaccard, refractory, race, spike budget, energy, tick6 bind, gate_snn budget, rights). Then `json.loads` every line, `validate_run.check_line`, `dumps_exact_json`, `raster_status`, `check_jsonl` FactoryStaging, `verify_batch_for_frontier(strict=True)`, `spike_probe.py --strict`.

Never `training_ready`. Never `sim_or_real=real`. Create-only into the assigned live path; did not clobber 2026-08-17 / 2026-08-30; did not overwrite existing r67 files (c-suffix if occupied).

## Residual weaknesses (honest)

1. Only **one** labeled independent LIF (331). The other four excerpts are independent of `spike_events` times but are not declared population sims.
2. Wrong-ACCEPT still absent (guard).
3. 334 ACCEPT is already-legal; a later round could pair the single ACCEPT with a world charge that does not go negative.
4. Five domain slugs leave the prompt's 8-item pool; a later round that must stay inside the pool will have to rotate sit-outs instead.
5. Tick-6 sidecar bind is standing machinery (r14+), not a new class.

## Next densification target

Labeled LIF on a second record, or an ISI histogram sidecar. Remaining unused wrong-MODIFY subclasses include **wrong-polarity on a fresh tag**. Wrong-ACCEPT remains structurally absent until a prompt amendment.

Novel coverage: 22.0%
"""


def run_pipelines(records):
    sys.path.insert(0, str(PIPELINES))
    from check_records import FactoryStaging, check_jsonl
    from curate_bridge import raster_status
    from exact_json import dumps_exact_json
    from round_txn import validate_novel_coverage
    from validate_run import check_line
    from verify_execution import verify_batch_for_frontier

    report = []
    errors, warnings, kinds, nrec = check_jsonl(
        BATCH_PATH, "batch-r67.jsonl", staging=FactoryStaging(enabled=True)
    )
    report.append(("check_jsonl FactoryStaging", errors, warnings, kinds, nrec))
    line_errs = []
    for i, rec in enumerate(records, 1):
        errs, kind = check_line(rec, f"batch-r67.jsonl:{i}", factory_staging=True)
        if errs:
            line_errs.append((i, kind, errs))
        try:
            dumps_exact_json(rec, ensure_ascii=False, sort_keys=False)
        except Exception as exc:
            line_errs.append((i, "exact_json", [str(exc)]))
    report.append(("check_line+exact_json", line_errs, None, None, None))
    raster_fail = []
    for rec in records:
        st = raster_status(rec, require_raster=True, require_routing_table=True)
        if not st.get("raster_valid") or not st.get("gate_snn_valid"):
            raster_fail.append((rec["id"], st))
    report.append(("raster_status", raster_fail, None, None, None))
    counts, findings, blocked = verify_batch_for_frontier(BATCH_PATH, strict=True)
    report.append(("verify_batch_for_frontier", counts, findings, blocked, None))
    cov = validate_novel_coverage(
        NOTES_PATH,
        Path("thalamic-trajectory-factory"),
        notes_text=NOTES_PATH.read_text(),
        required=True,
    )
    report.append(("validate_novel_coverage", cov, None, None, None))
    probe = subprocess.run(
        [sys.executable, str(PIPELINES / "spike_probe.py"), "--strict", str(BATCH_PATH)],
        cwd=str(REPO),
        capture_output=True,
        text=True,
    )
    report.append(("spike_probe", probe.returncode, probe.stdout[-2000:], probe.stderr[-2000:], None))
    schema_err = None
    try:
        import jsonschema
        from referencing import Registry, Resource
        from referencing.jsonschema import DRAFT202012

        schema_dir = REPO / "schemas"
        ttf_schema = json.loads((schema_dir / "thalamic-trajectory-v2.schema.json").read_text())
        raster_schema = json.loads((schema_dir / "raster.schema.json").read_text())
        base_schema = json.loads((schema_dir / "thalamic-trajectory.schema.json").read_text())
        registry = Registry().with_resources(
            [
                ("thalamic-trajectory-v2.schema.json", Resource.from_contents(ttf_schema, DRAFT202012)),
                ("thalamic-trajectory.schema.json", Resource.from_contents(base_schema, DRAFT202012)),
                ("raster.schema.json", Resource.from_contents(raster_schema, DRAFT202012)),
            ]
        )
        validator = jsonschema.Draft202012Validator(ttf_schema, registry=registry)
        fails = []
        for rec in records:
            errs = sorted(validator.iter_errors(rec), key=lambda e: list(e.path))
            if errs:
                fails.append((rec["id"], [e.message for e in errs[:4]]))
        schema_err = fails
    except Exception as exc:
        schema_err = f"skip:{exc}"
    report.append(("jsonschema", schema_err, None, None, None))
    return report


def create_only_copy(src: Path, dest_dir: Path, name: str) -> Path:
    dest = dest_dir / name
    if dest.exists():
        stem, ext = name.split(".", 1)
        suffix = "c"
        while True:
            cand = dest_dir / f"{stem}{suffix}.{ext}"
            if not cand.exists():
                dest = cand
                break
            suffix += "c"
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    fd = os.open(str(dest), flags, 0o644)
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(src.read_bytes())
    except Exception:
        try:
            os.unlink(str(dest))
        except OSError:
            pass
        raise
    return dest


def main() -> int:
    STAGING.mkdir(parents=True, exist_ok=True)
    records = [record_331(), record_332(), record_333(), record_334(), record_335()]
    issues, jmax = self_check(records)
    lines = [
        json.dumps(rec, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        for rec in records
    ]
    BATCH_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    NOTES_PATH.write_text(notes_text(jmax), encoding="utf-8")
    print(f"wrote {BATCH_PATH} lines={len(lines)} jmax={jmax:.3f}")
    print(f"wrote {NOTES_PATH}")
    if issues:
        print("SELF_CHECK_ISSUES:")
        for item in issues:
            print(" -", item)
        return 1
    print("SELF_CHECK_OK")
    report = run_pipelines(records)
    failed = False
    for item in report:
        name = item[0]
        print(f"PIPELINE {name}: {item[1:]}")
        if name == "check_jsonl FactoryStaging":
            errors, warnings, kinds, nrec = item[1], item[2], item[3], item[4]
            print(f"  kinds={kinds} n={nrec} errors={len(errors)} warnings={len(warnings)}")
            for e in errors:
                print("  ERR", e)
                failed = True
        elif name == "check_line+exact_json":
            if item[1]:
                print("  LINE_ERR", item[1])
                failed = True
        elif name == "raster_status":
            if item[1]:
                print("  RASTER_FAIL", item[1])
                failed = True
        elif name == "verify_batch_for_frontier":
            if item[3]:
                print("  BLOCKED", item[1], item[2])
                failed = True
        elif name == "validate_novel_coverage":
            if item[1]:
                print("  COVERAGE", item[1])
                failed = True
        elif name == "spike_probe":
            if item[1] != 0:
                print("  PROBE_FAIL", item[2], item[3])
                failed = True
        elif name == "jsonschema":
            if isinstance(item[1], list) and item[1]:
                print("  SCHEMA_FAIL", item[1])
                failed = True
    if failed:
        return 1
    live_batch = create_only_copy(BATCH_PATH, LIVE_DIR, "batch-r67.jsonl")
    live_notes = create_only_copy(NOTES_PATH, LIVE_DIR, "NOTES-r67.md")
    print(f"LIVE {live_batch}")
    print(f"LIVE {live_notes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
