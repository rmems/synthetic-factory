#!/usr/bin/env python3
"""Emit TTF r52 JSONL (ttf-r52-276..280) into /tmp/ttf-r52/. Never writes outputs/raw/."""

from __future__ import annotations

import json
import math
import random
import re
import subprocess
import sys
from collections import OrderedDict
from decimal import Decimal
from pathlib import Path

OUT_DIR = Path("/tmp/ttf-r52")
BATCH_PATH = OUT_DIR / "batch-r52.jsonl"
NOTES_PATH = OUT_DIR / "NOTES-r52.md"
REPO = Path("/home/raulmc/rmems/synthetic-factory")
PIPELINES = REPO / "pipelines"

PJ_PER_SPIKE = 23
RIGHTS = OrderedDict(
    [
        ("provider", "SpaceXAI/xAI"),
        ("model", "grok-4.6"),
        ("channel", "consumer"),
        ("subscription_plan", "SuperGrok Heavy"),
        ("generation_surface", "SuperGrok Heavy chat"),
        ("generated_at", "2026-09-02T17:30:00Z"),
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
PLANT_RE = re.compile(r"\b([A-Z][A-Za-z]+(?:-[A-Z][A-Za-z0-9]+)+)\b")
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
THIS_DOMAINS = (
    "phosphoric-attack-tank",
    "hydrocracker-reactor",
    "green-anode-press",
    "continuous-anneal-line",
    "nitric-acid-absorber",
)
THIS_PLANTS = (
    "Apatite-Vale",
    "Gasoil-Brae",
    "Green-Anode-Naze",
    "Recryst-Holt",
    "Ostwald-Gill",
)
IDS = [f"ttf-r52-{n}" for n in range(276, 281)]
PROMPT_POOL = {
    "warehouse-amr",
    "aerial-swarm",
    "underwater-rov",
    "grid-inspection",
    "humanoid-locomotion",
    "surgical-assist",
    "industrial-assembly",
    "autonomous-driving",
}
NOVEL_COVERAGE_LINE = "Novel coverage: 21.0%"


def harvest_occupancy() -> tuple[set[str], set[str]]:
    domains: set[str] = set(PROMPT_POOL)
    plants: set[str] = set()
    for path in sorted(Path("/tmp").glob("ttf-r*/batch-r*.jsonl")):
        if path.parent.name == "ttf-r52":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        for line in text.splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            st = rec.get("state") or {}
            meta = rec.get("meta") or {}
            if isinstance(st.get("domain"), str):
                domains.add(st["domain"])
            if isinstance(meta.get("domain"), str):
                domains.add(meta["domain"])
            plants.update(PLANT_RE.findall(json.dumps(rec)))
    for path in sorted(Path("/tmp").glob("ttf-r*/NOTES-r*.md")):
        if path.parent.name == "ttf-r52":
            continue
        try:
            txt = path.read_text(encoding="utf-8")
        except OSError:
            continue
        plants.update(PLANT_RE.findall(txt))
        match = re.search(r"Domains this batch:\s*(.*)", txt)
        if match:
            domains.update(re.findall(r"`([^`]+)`", match.group(1)))
    for path in sorted(Path("/tmp").glob("ttf-r*/gen_r*.py")) + sorted(
        Path("/tmp").glob("ttf-r*/_records.py")
    ):
        if "r52" in path.name or path.parent.name == "ttf-r52":
            continue
        try:
            txt = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        domains.update(re.findall(r'\("domain",\s*"([^"]+)"\)', txt))
        match = re.search(
            r"(THIS_DOMAINS|MY_DOMAINS)\s*=\s*[\{(](.*?)[\})]", txt, re.S
        )
        if match:
            domains.update(re.findall(r'"([^"]+)"', match.group(2)))
        match = re.search(
            r"(THIS_PLANTS|MY_PLANTS)\s*=\s*[\{(](.*?)[\})]", txt, re.S
        )
        if match:
            plants.update(re.findall(r'"([^"]+)"', match.group(2)))
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
    return OrderedDict(
        [
            ("source", source),
            ("target", target),
            (
                "table",
                [
                    OrderedDict([("from", a), ("to", b), ("weight", w)])
                    for a, b, w in table
                ],
            ),
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


def spike_avoid_us(events):
    return {int(round(ev["t_rel_ms"] * 1000.0)) for ev in events}


def lif_276_excerpt():
    n = 76
    dt_us = 100
    tau_m_ms = 19.0
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.91
    i_stim_peak = 2.48
    stim = (21400, 24800)
    seed = 52276
    window_us = 42000
    i_clamp_extra = 0.64
    clamp_n = 14
    rng = random.Random(seed)
    tau_s = tau_m_ms / 1000.0
    dt_s = dt_us / 1e6
    decay = math.exp(-dt_s / tau_s)
    steps = window_us // dt_us
    voltage = [rng.random() * v_th * 0.97 for _ in range(n)]
    bias = [i_bias * (1.0 + 0.13 * (rng.random() * 2 - 1)) for _ in range(n)]
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
    early = [(t, nid) for t, nid in spikes if t < 21400]
    burst = [(t, nid) for t, nid in spikes if 21400 <= t < 24800]
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
            group = [1 for tt, _ in picked if (tt < 21400) == (pool[0][0] < 21400)]
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
    take(burst, 9, label_times=(22600, 23300, 24200))
    clamp = [(t, nid) for t, nid in picked if t < 21400][:7]
    blister = [(t, nid) for t, nid in picked if t >= 21400][:9]
    picked = sorted(clamp + blister, key=lambda item: (item[0], item[1]))
    if len(picked) < 8:
        raise ValueError(
            f"LIF excerpt too short {len(picked)} (early={len(early)} burst={len(burst)})"
        )
    channels = ["lif.clamp" if t < 21400 else "lif.blister" for t, _ in picked]
    lif = OrderedDict(
        [
            ("model", "leaky_integrate_and_fire"),
            ("n", 76),
            ("dt_us", 100),
            ("tau_m_ms", 19.0),
            ("v_rest", 0.0),
            ("v_reset", 0.0),
            ("v_th", 1.0),
            ("r_m", 1.0),
            ("refractory_us", 1000),
            ("i_bias", 0.91),
            ("i_stim_peak", 2.48),
            ("stim_t_us", [21400, 24800]),
            ("i_clamp_extra", 0.64),
            ("clamp_n", 14),
            ("seed", 52276),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-13 carry +0.64 steam-clamp bias; stim 21.4-24.8 ms is the rubber-lining blister.",
            ),
        ]
    )
    extra = OrderedDict(
        [
            ("excerpt_source", "independent_lif"),
            ("sim_scope", "sidecar_only"),
            ("lif", lif),
            ("abort_s", 840),
            ("delayed_surprise_s", 840),
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
            ("round", 52),
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


def wrap_record(
    rid,
    title,
    state,
    spikes,
    proposed,
    safety,
    executed,
    future,
    ticks,
    notes,
    ras,
    gate,
    domain,
    tags,
    distillation,
    batch_position,
    supervisor_error_type=None,
):
    return OrderedDict(
        [
            ("id", rid),
            ("title", title),
            ("state", state),
            ("spike_events", spikes),
            ("proposed_action", proposed),
            ("safety_decision", safety),
            ("executed_action", executed),
            ("future_outcome", future),
            ("reward_components", reward_block(ticks, notes)),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    domain,
                    tags,
                    distillation,
                    batch_position,
                    supervisor_error_type=supervisor_error_type,
                ),
            ),
        ]
    )


def record_276():
    excerpt, extra = lif_276_excerpt()
    ticks = [
        tick(2140, 0.04, -0.02, -0.02, 0.01, 0.00),
        tick(6140, 0.07, -0.04, -0.03, 0.01, -0.01),
        tick(6348, 0.05, -0.03, -0.02, 0.00, 0.00),
        tick(6960, 0.08, -0.06, -0.03, 0.02, -0.01),
        tick(22600, 0.04, -0.40, -0.04, -0.01, -0.02),
        tick(840000000, 0.02, -0.05, -0.02, 0.01, -0.01),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Attack-T3 at Apatite-Vale AV-6 is already steaming 4.8 t/h into a 88.4 C "
                "gypsum-acid slurry against an 85.0 C rubber-lining cap. A lining-first latch "
                "clamps the steam; a feed-first story would keep the 4.8 t/h cruise. Stored "
                "blister strain in the rubber lining is not yet an observable of either race channel.",
            ),
            ("domain", "phosphoric-attack-tank"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the AV-6 wet-process attack, keep lining temperature <= 85.0 C, and "
                "leave the rubber membrane unmarked.",
            ),
            ("t0_us", 1756850400000276),
            ("gate_latency_us", 820),
            ("race_window_us", 400),
            ("race_window_rel_ms", [6.10, 6.50]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.attack.C 88.4 C pulse",
                                "ft.steam.tph 4.8 t/h cruise",
                            ],
                        ),
                        (
                            "semantics",
                            "Lining-first latches steam 4.8 -> 3.1 t/h; feed-first keeps "
                            "cruise on a still-cooling lining model.",
                        ),
                        (
                            "window_derivation",
                            "400 us = one 2 kHz lining-RTD sample minus steam-orifice group "
                            "delay on this attack-tank bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 208 us vs combined jitter ~64 us (lining 30 + steam 34): 3.2x over "
                            "a 2.0x trust floor. Reversing order by < 208 us inside the 400 us window "
                            "would have kept 4.8 t/h cruise; predicted next-sample 86.6 C > 85.0 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "attack-tank lining RTD, 2 kHz, 30 us timestamp jitter",
                    "steam-orifice FT, 1 kHz, 34 us jitter",
                    "rubber-lining AE puck (context until the blister)",
                    "gypsum-filter DP (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("lining_cap_C", 85.0),
                        ("observed_lining_C", 88.4),
                        ("proposed_steam_tph", 4.8),
                        ("phosphate_feed_tph", 12.6),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Attack-T3 indexed on Apatite-Vale AV-6; steam armed at 4.8 t/h.",
                    "2. Cruise 4.8 t/h; lining 88.4 C against 85.0 C rubber-lining cap.",
                    "3. Steam precursor at 1.140 ms; lining warm-start 88.4 C.",
                    "4. Race window [6.100, 6.500] ms opens on the attack-tank bus.",
                    "5. rtd.attack.C 88.4 C at 6.140 ms (winner).",
                    "6. ft.steam.tph 4.8 t/h at 6.348 ms (loser by 208 us).",
                    "7. Gate at 6.960 ms (winner + 820 us): MODIFY clamp 4.8 -> 3.1 t/h.",
                    "8. Clamp executes; next-sample lining 83.6 C < 85.0 cap.",
                    "9. At 22.600 ms stored strain still blisters a 18 mm rubber lining; AE burst.",
                    "10. Tank isolate 14 min (abort_s=840); named un-netted loss, not folded into process heads.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_steam_48"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("steam_tph", 4.8),
                        ("phosphate_feed_tph", 12.6),
                        ("slurry_pct", 38.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("lining_C", 88.4),
                        ("lining_cap_C", 85.0),
                        ("predicted_unclamped_next_C", 86.6),
                        ("steam_tph", 4.8),
                        ("race_margin_us", 208),
                        ("combined_jitter_us", 64),
                        ("abort_s", 840),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 4.8 t/h cruise: 88.4 C looks like a gypsum-filter spike, not "
                "lining contact, and T3 volume is treated as still open.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Lining 88.4 C won by 208 us, so the rubber is loading heat, not still cooling. "
                "Holding 4.8 t/h predicts next-sample 86.6 C > 85.0 cap. MODIFY: steam 4.8 -> 3.1 t/h. "
                "Observed after clamp 83.6 C < 85.0. A full REJECT is not indicated: a sound attack "
                "pass accepts 3.1 t/h.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "lining_C",
                            OrderedDict(
                                [
                                    ("cap", 85.0),
                                    ("observed", 88.4),
                                    ("predicted_unclamped_next", 86.6),
                                    ("clamped_steam_tph", 3.1),
                                    ("observed_after_clamp", 83.6),
                                ]
                            ),
                        ),
                        (
                            "steam_tph",
                            OrderedDict([("proposed", 4.8), ("clamped", 3.1)]),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 208),
                                    ("combined_jitter_us", 64),
                                    ("ratio", 3.25),
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
            ("name", "clamped_steam_31"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("steam_tph", 3.1),
                        ("phosphate_feed_tph", 12.6),
                        ("slurry_pct", 38.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: steam 4.8 -> 3.1 t/h. Process-correct vs the 85.0 C rubber-lining "
                "cap. Lining blister still occurs at 22.600 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held lining at 83.6 C. At 22.600 ms stored strain "
                "in the rubber lining still blistered an 18 mm patch. Clamp reduced dump energy; "
                "it did not prevent the split. Partnered negative: process heads stay honest; "
                "world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("steam", "clamp executed; peak 83.6 C < 85.0"),
                        ("lining", "18 mm blister at 22.600 ms"),
                        ("repair", "14 min tank isolate (abort_s=840)"),
                        ("mission", "AV-6 attack pass incomplete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither lining RTD nor steam FT predicted the blister charge; ae.lining.blister is a new channel at 22.600 ms, 15.640 ms after the gate, still inside the 42 ms raster.",
                    "Delayed (abort_s=840): 14 min tank isolate. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "14 min tank isolate after an 18 mm rubber-lining blister. Safety head -0.60 "
                "prices the split; task_progress stays +0.30 because the steam clamp completed "
                "under the 85.0 C cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.attack.C (6.140 ms, 88.4 C)"),
                        ("loser", "ft.steam.tph (6.348 ms, 4.8 t/h)"),
                        ("margin_us", 208),
                        (
                            "counterfactual_if_reversed",
                            "Feed-first by < 208 us inside the 400 us window would have kept "
                            "4.8 t/h cruise; predicted next-sample 86.6 C would have exceeded "
                            "the 85.0 cap even without the blister charge. The MODIFY is still the "
                            "correct process. The blister is a later world charge either way, "
                            "cheaper with the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22600),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.600 ms rubber-lining blister (tick t_us=22600), inside "
                "the 42 ms raster. The correct MODIFY at 6.960 ms is in the same excerpt. Do "
                "not put inflection on the abort_s=840 isolate tick.",
            ),
            ("delayed_surprise_s", 840.0),
            ("abort_s", 840),
        ]
    )
    spikes = [
        spike("enc.steam.ctx", 1.140, 0.42),
        spike("rtd.attack.C", 2.140, 0.61),
        spike("ft.steam.tph", 3.620, 0.50),
        spike("rtd.attack.C", 6.140, 1.32),
        spike("ft.steam.tph", 6.348, 1.14),
        spike("ctrl.gate", 6.960, 0.98),
        spike("rtd.attack.C", 8.420, 0.80),
        spike("ft.steam.tph", 11.200, 0.62),
        spike("ctrl.gate", 14.880, 0.84),
        spike("ae.lining.blister", 22.600, 1.46),
        spike("ae.lining.blister", 24.410, 0.91),
        spike("enc.steam.ctx", 31.200, 0.41),
        spike("rtd.attack.C", 38.100, 0.53),
    ]
    ras = raster_core(
        42,
        76,
        26,
        83,
        routing(
            "thalamic-relay.attack-lining",
            "spikenaut.policy.steam-clamp",
            [
                ("relay.rtd.lining", "policy.steam_clamp", 0.66),
                ("relay.ft.steam", "policy.steam_hold", 0.30),
                ("relay.ae.blister", "policy.steam_clamp", -0.45),
            ],
            "noradrenaline",
            0.05,
            "surprise-gated pre_post_stdp; NA at lining win (6.140 ms) opens a 50 ms "
            "eligibility trace that still covers the 22.600 ms rubber-lining blister",
        ),
        excerpt,
        extra=extra,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.40),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop("steam_clamp", 40, 0.50, 250.0, 4),
                    pop("steam_hold", 40, 0.50, 62.5, 1),
                    pop("lining_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r52-276",
        "Apatite-Vale AV-6 / Attack-T3: lining 88.4 C beats steam-feed by 208 us; correct "
        "MODIFY still eats an in-window rubber-lining blister (partnered negative total -0.47)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Partnered negative. Process-correct MODIFY; world still charges inside the "
        "42 ms raster. total -0.47 = 0.30 + -0.60 + -0.16 + 0.04 + -0.05. Named tank "
        "isolate (abort_s=840) is not netted into task_progress.",
        ras,
        gate,
        "phosphoric-attack-tank",
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
        "14 min tank isolate.",
        1,
    )


def record_277():
    ticks = [
        tick(1680, -0.02, -0.01, -0.02, -0.01, 0.01),
        tick(4260, -0.04, -0.02, -0.04, -0.02, 0.01),
        tick(4418, -0.03, -0.01, -0.03, -0.02, 0.01),
        tick(4960, -0.07, -0.04, -0.09, -0.05, 0.02),
        tick(6820, -0.02, -0.01, -0.02, -0.01, 0.01),
        tick(1080000000, -0.02, -0.01, -0.02, -0.01, 0.00),
    ]
    spikes = [
        spike("dp.recycle.ctx", 0.840, 0.40),
        spike("rtd.bed.C", 1.680, 0.58),
        spike("hist.lag.C", 2.440, 0.51),
        spike("rtd.bed.C", 4.260, 1.32),
        spike("hist.lag.C", 4.418, 1.15),
        spike("ctrl.gate", 4.960, 1.00),
        spike("rtd.bed.C", 6.820, 0.74),
        spike("hist.lag.C", 8.200, 0.61),
        spike("ctrl.gate", 12.100, 0.82),
        spike("dp.recycle.ctx", 16.400, 0.42),
        spike("rtd.bed.C", 20.800, 0.53),
        spike("hist.lag.C", 23.400, 0.47),
    ]
    excerpt = independent_excerpt(52277, 92, 24000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Converter-C7 on Syngas-Brae SB-4 is holding recycle at 38.0 t/h with live bed "
                "218.0 C against a 235.0 C trip. A historian tag still prints 248.0 C from a "
                "42 s lagged sample. Live-first should ACCEPT the recycle; a weak supervisor "
                "that binds the lagged historian as live will REJECT a legal loop.",
            ),
            ("domain", "methanol-synthesis-loop"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep 38.0 t/h recycle on C7 while live bed stays <= 235.0 C; do not spend a "
                "42 s historian lag on the compressor hold.",
            ),
            ("t0_us", 1756850400000277),
            ("gate_latency_us", 700),
            ("race_window_us", 320),
            ("race_window_rel_ms", [4.20, 4.52]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.bed.C 218.0 C live",
                                "hist.lag.C 248.0 C lagged 42 s",
                            ],
                        ),
                        (
                            "semantics",
                            "Live-first should ACCEPT 38.0 t/h (218.0 C < 235.0 C trip). "
                            "Lag-first tempts a weak supervisor to treat 248.0 C as the live bed.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one bed-RTD sample minus historian-publisher group delay "
                            "on this synthesis-loop bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 158 us vs combined jitter ~56 us (bed 24 + hist 32): 2.8x over "
                            "a 2.0x trust floor. Order is correctly live-first. The error is binding "
                            "a 42 s lagged sample as live, not the race.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "converter bed RTD, 4 kHz, 24 us jitter",
                    "historian lagged tag, 1 kHz, 32 us jitter, lag_s=42",
                    "recycle differential pressure (context)",
                    "make-up syngas FT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("bed_trip_C", 235.0),
                        ("live_bed_C", 218.0),
                        ("lagged_bed_C", 248.0),
                        ("lag_s", 42),
                        ("proposed_recycle_tph", 38.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Converter-C7 latched on Syngas-Brae SB-4; recycle 38.0 t/h armed.",
                    "2. Live bed 218.0 C; historian still prints 248.0 C with lag_s=42.",
                    "3. Recycle-dp precursor at 0.840 ms.",
                    "4. Race window [4.200, 4.520] ms.",
                    "5. rtd.bed.C 218.0 C at 4.260 ms (winner).",
                    "6. hist.lag.C 248.0 C at 4.418 ms (loser by 158 us).",
                    "7. Gate at 4.960 ms: REJECT hold 0.0 t/h (incorrect).",
                    "8. Legal recycle cancelled; live bed still 218.0 C < 235.0 C trip.",
                    "9. Lagged tag remains a historian sample, not a live PV.",
                    "10. Delayed missed_window_s=1080 (18 min methanol-quality window) while the loop waits.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "recycle_38"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("recycle_tph", 38.0),
                        ("hold", False),
                        ("pv_source", "live_rtd"),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_bed_C", 218.0),
                        ("bed_trip_C", 235.0),
                        ("lagged_bed_C", 248.0),
                        ("lag_s", 42),
                        ("lag_fresh", False),
                        ("pv_live", True),
                        ("proposed_recycle_tph", 38.0),
                        ("race_margin_us", 158),
                        ("combined_jitter_us", 56),
                        ("missed_window_s", 1080),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 38.0 t/h recycle because live bed 218.0 C is under the "
                "235.0 C trip; 248.0 C is a 42 s historian lag, not a live PV.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Historian 248.0 C is over the 235.0 C trip (true vs that lagged sample). REJECT: "
                "hold recycle 0.0 t/h until the tag recovers under 235.0 C so the converter does "
                "not see an over-temperature event.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "bed_C",
                            OrderedDict(
                                [
                                    ("published_live_trip", 235.0),
                                    ("observed_live", 218.0),
                                    ("historian_lagged", 248.0),
                                    ("lag_s", 42),
                                    ("executed_recycle_tph", 0.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 158),
                                    ("combined_jitter_us", 56),
                                    ("ratio", 2.82),
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
            ("name", "recycle_hold_lagged"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("recycle_tph", 0.0),
                        ("hold", True),
                        ("pv_source", "historian_lag"),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT (incorrect): recycle 38.0 -> 0.0 t/h. Routing relay.hist.lag -> "
                "policy.hold_reject; no positive weight to policy.go_accept. Live 218.0 C never "
                "violated the 235.0 C trip.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-REJECT froze C7 at 0.0 t/h while live bed stayed 218.0 C under the "
                "235.0 C trip. 18 min methanol-quality window missed. Correct gate was ACCEPT of "
                "the already-legal 38.0 t/h recycle.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("recycle", "held at 0.0 t/h; 38.0 t/h abandoned"),
                        ("live_bed_C", "still 218.0 C, under 235.0 C published trip"),
                        ("loop", "18 min methanol-quality window missed"),
                        ("historian", "42 s lag false positive, not a live over-temp"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "The 248.0 C reading is a 42 s lagged historian sample, not a published live trip.",
                    "Delayed (missed_window_s=1080): sister converter C8 ran the same 38.0 t/h quality window after QA rebound the live trip; C7's slot was already gone.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "ACCEPT: live 218.0 C < published 235.0 C trip; leave 38.0 t/h.",
                        ),
                        ("correct_trip_C", 235.0),
                        ("wrong_lagged_C", 248.0),
                        ("wrong_lag_s", 42),
                        (
                            "wrong_edit_applied",
                            OrderedDict([("recycle_tph", 0.0), ("hold", True)]),
                        ),
                        (
                            "cost",
                            "18 min missed methanol-quality window (task/efficiency); live bed never over trip (safety false-positive).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.bed.C (4.260 ms, 218.0 C live)"),
                        ("loser", "hist.lag.C (4.418 ms, 248.0 C lag_s=42)"),
                        ("margin_us", 158),
                        (
                            "counterfactual_if_reversed",
                            "Lag-first by < 158 us would still show live 218.0 C < 235.0 C. A "
                            "correct gate ACCEPTs either way. The wrong REJECT spent the live win "
                            "on a 42 s historian sample.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 4960),
            (
                "reward_inflection_note",
                "Task and efficiency drop at the wrong REJECT (4.960 ms, tick 4). The 18 min "
                "missed window is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 1080.0),
            ("missed_window_s", 1080),
        ]
    )
    ras = raster_core(
        24,
        92,
        34,
        75,
        routing(
            "relay.hist.lag",
            "policy.hold_reject",
            [
                ("relay.hist.lag", "policy.hold_reject", 0.74),
                ("relay.rtd.bed", "policy.hold_reject", 0.20),
            ],
            "acetylcholine",
            0.06,
            "stale_sample_stdp; ACh tags the (wrong) hold_reject bind at the lagged historian",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("missed_window_s", 1080),
                ("delayed_surprise_s", 1080),
                ("lag_s", 42),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.32),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("hold_reject", 48, 0.50, 260.4, 4),
                    pop("go_accept", 48, 0.80, 6.5, 0),
                    pop("lag_ctx", 32, 0.55, 97.7, 1),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r52-277",
        "WRONG-REJECT at Syngas-Brae SB-4 / Converter-C7: live bed 218.0 C < 235.0 C trip; "
        "supervisor bound a 42 s lagged historian 248.0 C as live",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Wrong-reject. Sidecar arithmetic 218.0 < 235.0 is true; clamp bound to a "
        "42 s lagged 248.0 C historian sample. total -0.58 = -0.20 + -0.10 + -0.22 + -0.12 + 0.06.",
        ras,
        gate,
        "methanol-synthesis-loop",
        [
            "reject",
            "wrong-gate",
            "stale-sample-as-live",
            "lagged-historian",
            "sidecar-convictable",
            "designed",
        ],
        "Teaches a probe that a correct live<trip read can still be a wrong gate when "
        "routing.table[0].to is policy.hold_reject and executed recycle is zeroed.",
        2,
        supervisor_error_type="wrong-reject",
    )


def record_278():
    ticks = [
        tick(2480, 0.01, 0.05, 0.01, 0.01, 0.01),
        tick(5720, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(5894, 0.02, 0.07, 0.02, 0.02, 0.01),
        tick(6560, 0.03, 0.12, 0.04, 0.03, 0.02),
        tick(8840, 0.01, 0.05, 0.02, 0.01, 0.01),
        tick(540000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("ir.flue.ctx", 1.280, 0.43),
        spike("ae.pack.pps", 2.480, 0.62),
        spike("ir.flue.C", 4.020, 0.49),
        spike("ae.pack.pps", 5.720, 1.35),
        spike("ir.flue.C", 5.894, 1.12),
        spike("ctrl.gate", 6.560, 1.03),
        spike("ae.pack.pps", 8.840, 0.77),
        spike("ir.flue.ctx", 13.100, 0.44),
        spike("ir.flue.C", 17.200, 0.58),
        spike("ctrl.gate", 22.400, 0.81),
        spike("ae.pack.pps", 28.600, 0.50),
        spike("ir.flue.C", 34.800, 0.46),
        spike("ae.pack.ctx", 38.200, 0.40),
    ]
    excerpt = independent_excerpt(52278, 108, 40000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Pit-P12 on Green-Anode-Naze GAN-HIL is armed for a 1.60 t/h pitch inject while "
                "packing AE sits at 46 pps against a 12 pps crack floor. A flue IR, lit by the "
                "pad lamp spectrum, still reports 1188 C under a 1250 C fire cap. AE-first holds "
                "the inject; flue-first would commit 1.60 t/h into a packing split.",
            ),
            ("domain", "anode-baking-furnace"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Inject pitch on P12 only if packing AE stays <= 12 pps; otherwise hold so a "
                "cracked packing is not fed at 1.60 t/h.",
            ),
            ("t0_us", 1756850400000278),
            ("gate_latency_us", 840),
            ("race_window_us", 400),
            ("race_window_rel_ms", [5.68, 6.08]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ae.pack.pps 46 pps packing crack",
                                "ir.flue.C 1188 C pad-lamp glint",
                            ],
                        ),
                        (
                            "semantics",
                            "AE-first latches pitch hold 1.60 -> 0 t/h; flue-first would commit "
                            "1.60 t/h on a still-legal 1188 C fire-cap story.",
                        ),
                        (
                            "window_derivation",
                            "400 us = one packing-AE slot versus flue-IR decode on this HIL bake-pit bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 174 us vs combined jitter ~62 us (AE 28 + IR 34): 2.8x over "
                            "a 2.0x trust floor. Reversing order by < 174 us inside the 400 us "
                            "window would have committed 1.60 t/h into a 46 pps packing crack.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "packing AE puck, 5 kHz, 28 us jitter",
                    "flue IR camera, 200 Hz, 34 us jitter",
                    "pit-wall thermocouple (context)",
                    "pitch-header FT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ae_crack_floor_pps", 12.0),
                        ("observed_ae_pps", 46.0),
                        ("flue_cap_C", 1250.0),
                        ("observed_flue_C", 1188.0),
                        ("proposed_pitch_tph", 1.60),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Pit-P12 indexed on Green-Anode-Naze GAN-HIL; pitch 1.60 t/h armed.",
                    "2. Flue IR 1188 C under 1250 C fire cap; packing AE already 46 pps.",
                    "3. Flue-context precursor at 1.280 ms.",
                    "4. Race window [5.680, 6.080] ms.",
                    "5. ae.pack.pps 46 pps at 5.720 ms (winner).",
                    "6. ir.flue.C 1188 C at 5.894 ms (loser by 174 us).",
                    "7. Gate at 6.560 ms: REJECT hold pitch 0 t/h.",
                    "8. Inject cancelled; packing crack not fed.",
                    "9. HIL pad lamp spectrum remains the flue glint source.",
                    "10. Delayed (abort_s=540): 9 min pit re-pack before the next fire.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "pitch_inject_160"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("pitch_tph", 1.60),
                        ("hold", False),
                        ("pit", "P12"),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ae_pps", 46.0),
                        ("ae_crack_floor_pps", 12.0),
                        ("flue_C", 1188.0),
                        ("flue_cap_C", 1250.0),
                        ("race_margin_us", 174),
                        ("combined_jitter_us", 62),
                        ("abort_s", 540),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 1.60 t/h pitch because flue 1188 C is under the 1250 C fire "
                "cap and treats the AE puck as packing noise.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Packing AE 46 pps won by 174 us, so the packing is cracking, not still quiet. "
                "46 pps > 12 pps floor. REJECT: hold pitch 1.60 -> 0 t/h. Flue 1188 C < 1250 C "
                "does not license the inject once AE is over floor.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "packing_ae_pps",
                            OrderedDict(
                                [
                                    ("floor", 12.0),
                                    ("observed", 46.0),
                                    ("executed_pitch_tph", 0.0),
                                ]
                            ),
                        ),
                        (
                            "flue_C",
                            OrderedDict(
                                [
                                    ("cap", 1250.0),
                                    ("observed", 1188.0),
                                    ("does_not_license_inject", True),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 174),
                                    ("combined_jitter_us", 62),
                                    ("ratio", 2.81),
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
            ("name", "pitch_hold"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("pitch_tph", 0.0),
                        ("hold", True),
                        ("pit", "P12"),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT (correct): pitch 1.60 -> 0 t/h. Routing relay.ae.pack -> "
                "policy.pack_hold. Packing crack is not fed.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held P12 at 0 t/h pitch. AE 46 pps beat flue 1188 C; packing "
                "was already over the 12 pps crack floor. 9 min re-pack follows (abort_s=540).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("pitch", "held at 0 t/h; 1.60 t/h abandoned"),
                        ("packing", "46 pps crack not fed"),
                        ("flue", "1188 C still under 1250 C fire cap"),
                        ("pit", "9 min re-pack queued"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Flue IR 1188 C was a HIL pad-lamp glint, not a fire-cap exceedance.",
                    "Delayed (abort_s=540): 9 min pit re-pack before the next fire on GAN-HIL.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ae.pack.pps (5.720 ms, 46 pps)"),
                        ("loser", "ir.flue.C (5.894 ms, 1188 C)"),
                        ("margin_us", 174),
                        (
                            "counterfactual_if_reversed",
                            "Flue-first by < 174 us would have committed 1.60 t/h into a packing "
                            "already at 46 pps. The REJECT is still the correct process; AE is the "
                            "licensing channel, not flue IR.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6560),
            (
                "reward_inflection_note",
                "Safety and task credit the correct REJECT at 6.560 ms (tick 4). The 9 min "
                "re-pack is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 540.0),
            ("abort_s", 540),
        ]
    )
    ras = raster_core(
        40,
        108,
        21,
        91,
        routing(
            "thalamic-relay.packing-ae",
            "spikenaut.policy.pitch-hold",
            [
                ("relay.ae.pack", "policy.pack_hold", 0.68),
                ("relay.ir.flue", "policy.pack_commit", 0.28),
                ("relay.ae.pack", "policy.pack_hold", 0.12),
            ],
            "dopamine",
            0.07,
            "ae_floor_stdp; DA at packing win (5.720 ms) opens a 70 ms eligibility trace",
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
            ("decision_window_ms", 0.40),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("pack_hold", 52, 0.50, 240.4, 5),
                    pop("pack_commit", 52, 0.50, 48.1, 1),
                    pop("ae_veto", 28, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r52-278",
        "Green-Anode-Naze GAN-HIL / Pit-P12: packing AE 46 pps beats flue 1188 C; correct "
        "REJECT holds the pitch inject",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct REJECT. AE 46 pps > 12 pps floor beats a legal flue IR. "
        "total +0.78 = 0.10 + 0.40 + 0.12 + 0.10 + 0.06.",
        ras,
        gate,
        "anode-baking-furnace",
        ["reject", "hil", "packing-ae", "anode-bake", "correct-gate"],
        "Teaches a packing-AE vs flue-glint race on a HIL bake pit: the crack floor, not the "
        "fire cap, licenses the pitch inject.",
        3,
    )


def record_279():
    ticks = [
        tick(1620, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(3840, 0.09, 0.07, 0.04, 0.03, 0.02),
        tick(3962, 0.07, 0.06, 0.03, 0.02, 0.01),
        tick(4380, 0.12, 0.10, 0.05, 0.03, 0.02),
        tick(6240, 0.06, 0.04, 0.02, 0.02, 0.01),
        tick(300000000, 0.04, 0.03, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.line.ctx", 0.920, 0.41),
        spike("rtd.strip.C", 1.620, 0.58),
        spike("ir.pyro.glint", 2.880, 0.47),
        spike("rtd.strip.C", 3.840, 1.28),
        spike("ir.pyro.glint", 3.962, 1.10),
        spike("ctrl.gate", 4.380, 0.97),
        spike("rtd.strip.C", 6.240, 0.72),
        spike("enc.line.ctx", 9.800, 0.44),
        spike("ir.pyro.glint", 13.400, 0.55),
        spike("ctrl.gate", 17.200, 0.80),
        spike("rtd.strip.C", 20.100, 0.49),
        spike("enc.line.ctx", 21.600, 0.38),
    ]
    excerpt = independent_excerpt(52279, 80, 22000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Furnace-F4 of Recryst-Holt RH-9 is already at 718 C strip while a pyrometer "
                "glint still reports 762 against a 780 C scale cap the strip RTD has not crossed. "
                "Strip-first should ACCEPT 180 m/min; glint-first would invent a hold on an "
                "already-legal continuous-anneal pass.",
            ),
            ("domain", "continuous-anneal-line"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Run RH-9 at 180 m/min while strip RTD stays <= 780 C; do not spend a pyrometer "
                "lighting glint on the line hold.",
            ),
            ("t0_us", 1756850400000279),
            ("gate_latency_us", 540),
            ("race_window_us", 280),
            ("race_window_rel_ms", [3.80, 4.08]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.strip.C 718 C live",
                                "ir.pyro.glint 762 C lighting glint",
                            ],
                        ),
                        (
                            "semantics",
                            "Strip-first should ACCEPT 180 m/min (718 C < 780 C cap). "
                            "Glint-first would hold on a simulated lighting spike.",
                        ),
                        (
                            "window_derivation",
                            "280 us = one strip-RTD sample versus pyrometer decode on this "
                            "anneal-line bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 122 us vs combined jitter ~48 us (strip 22 + pyro 26): 2.5x over "
                            "a 2.0x trust floor. Reversing order by < 122 us inside the 280 us "
                            "window would have invented a hold on an already-legal 718 C strip.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "strip RTD, 4 kHz, 22 us jitter",
                    "furnace pyrometer, 200 Hz, 26 us jitter",
                    "line-speed encoder (context)",
                    "dew-point probe (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("strip_cap_C", 780.0),
                        ("observed_strip_C", 718.0),
                        ("pyro_glint_C", 762.0),
                        ("proposed_speed_m_min", 180.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Furnace-F4 indexed on Recryst-Holt RH-9; line 180 m/min armed.",
                    "2. Strip RTD 718 C; pyrometer glint 762 C under 780 C scale cap.",
                    "3. Encoder precursor at 0.920 ms.",
                    "4. Race window [3.800, 4.080] ms.",
                    "5. rtd.strip.C 718 C at 3.840 ms (winner).",
                    "6. ir.pyro.glint 762 C at 3.962 ms (loser by 122 us).",
                    "7. Gate at 4.380 ms: ACCEPT leave 180 m/min.",
                    "8. Strip remains 718 C < 780 C; glint unused as a hold.",
                    "9. Simulated lighting remains the pyrometer source.",
                    "10. Delayed (survey_hold_s=300): 5 min hardness survey after the pass.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "anneal_180"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("speed_m_min", 180.0),
                        ("hold", False),
                        ("h2_pct", 4.2),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("strip_C", 718.0),
                        ("strip_cap_C", 780.0),
                        ("pyro_glint_C", 762.0),
                        ("proposed_speed_m_min", 180.0),
                        ("race_margin_us", 122),
                        ("combined_jitter_us", 48),
                        ("survey_hold_s", 300),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 180 m/min because strip 718 C is under the 780 C scale cap; "
                "762 C is a lighting glint, not a strip temperature.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Strip 718 C won by 122 us and sits 62 C under the 780 C cap. Pyrometer 762 C "
                "is a lighting glint, not a strip reading. ACCEPT: leave 180 m/min. A hold would "
                "idle a legal anneal pass.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "strip_C",
                            OrderedDict(
                                [
                                    ("cap", 780.0),
                                    ("observed", 718.0),
                                    ("executed_speed_m_min", 180.0),
                                ]
                            ),
                        ),
                        (
                            "pyro_glint_C",
                            OrderedDict(
                                [
                                    ("observed", 762.0),
                                    ("not_a_strip_reading", True),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 122),
                                    ("combined_jitter_us", 48),
                                    ("ratio", 2.54),
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
            ("name", "anneal_180"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("speed_m_min", 180.0),
                        ("hold", False),
                        ("h2_pct", 4.2),
                    ]
                ),
            ),
            (
                "gate_effect",
                "ACCEPT: leave 180 m/min. Routing relay.rtd.strip -> policy.strip_go. "
                "Pyrometer glint unused as a hold.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left RH-9 at 180 m/min. Strip 718 C beat pyrometer glint 762 C; "
                "the 780 C cap was never crossed. 5 min hardness survey follows (survey_hold_s=300).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("line", "180 m/min held as proposed"),
                        ("strip", "718 C < 780 C cap"),
                        ("pyrometer", "762 C glint unused"),
                        ("survey", "5 min hardness survey queued"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Pyrometer 762 C was a simulated lighting glint, not a strip over-cap.",
                    "Delayed (survey_hold_s=300): 5 min hardness survey after the pass on RH-9.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.strip.C (3.840 ms, 718 C)"),
                        ("loser", "ir.pyro.glint (3.962 ms, 762 C)"),
                        ("margin_us", 122),
                        (
                            "counterfactual_if_reversed",
                            "Glint-first by < 122 us would still be a lighting spike under the "
                            "780 C cap; a correct gate ACCEPTs either way. Reversing would only "
                            "have delayed confirmation of the same legal strip.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 4380),
            (
                "reward_inflection_note",
                "Task and safety credit the correct ACCEPT at 4.380 ms (tick 4). The 5 min "
                "survey is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 300.0),
            ("survey_hold_s", 300),
        ]
    )
    ras = raster_core(
        22,
        80,
        34,
        60,
        routing(
            "thalamic-relay.strip-rtd",
            "spikenaut.policy.anneal-go",
            [
                ("relay.rtd.strip", "policy.strip_go", 0.70),
                ("relay.ir.pyro", "policy.glint_hold", 0.22),
                ("relay.rtd.strip", "policy.strip_go", 0.10),
            ],
            "serotonin",
            0.04,
            "already_legal_stdp; 5-HT at strip win (3.840 ms) tags the go bind",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("survey_hold_s", 300),
                ("delayed_surprise_s", 300),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.28),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("strip_go", 40, 0.50, 267.9, 3),
                    pop("glint_hold", 40, 0.80, 8.9, 0),
                    pop("cap_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r52-279",
        "Recryst-Holt RH-9 / Furnace-F4: strip 718 C beats pyrometer glint; correct ACCEPT "
        "of an already-legal 180 m/min (total +1.16)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT. Strip 718 C < 780 C cap; pyrometer glint unused. "
        "total +1.16 = 0.44 + 0.34 + 0.18 + 0.12 + 0.08.",
        ras,
        gate,
        "continuous-anneal-line",
        ["accept", "simulated-lighting", "strip-vs-glint", "anneal", "simulated"],
        "Teaches that a pyrometer lighting glint can lose to a legal strip RTD inside a "
        "280 us window; reversing 122 us would have invented a hold on an already-legal line.",
        4,
    )


def record_280():
    ticks = [
        tick(1960, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(5120, 0.09, 0.06, 0.04, 0.03, 0.02),
        tick(5286, 0.07, 0.05, 0.03, 0.02, 0.01),
        tick(5740, 0.12, 0.09, 0.06, 0.03, 0.02),
        tick(8120, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(360000000, 0.04, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("ft.abs.ctx", 1.080, 0.42),
        spike("an.tail.pct", 1.960, 0.59),
        spike("rtd.cooler.C", 3.440, 0.48),
        spike("an.tail.pct", 5.120, 1.30),
        spike("rtd.cooler.C", 5.286, 1.11),
        spike("ctrl.gate", 5.740, 0.99),
        spike("an.tail.pct", 8.120, 0.74),
        spike("rtd.cooler.C", 11.600, 0.56),
        spike("ctrl.gate", 15.400, 0.82),
        spike("ft.abs.ctx", 19.200, 0.43),
        spike("an.tail.pct", 22.800, 0.51),
        spike("rtd.cooler.C", 23.700, 0.40),
    ]
    excerpt = independent_excerpt(52280, 56, 24000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Tower-T8 at Ostwald-Gill OG-5 is absorbing at 1.85 bar with tail NOx 0.18 percent "
                "against a 0.40 percent cap. Cooler RTD sits at 18 C under a 35 C jacket cap. "
                "Tail-first should ACCEPT the 1.85 bar already-legal set; cooler-first would only "
                "delay confirmation of the same legal absorber.",
            ),
            ("domain", "nitric-acid-absorber"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Hold 1.85 bar on T8 while tail NOx stays <= 0.40 percent and cooler <= 35 C.",
            ),
            ("t0_us", 1756850400000280),
            ("gate_latency_us", 620),
            ("race_window_us", 360),
            ("race_window_rel_ms", [5.08, 5.44]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "an.tail.pct 0.18 percent NOx",
                                "rtd.cooler.C 18 C jacket",
                            ],
                        ),
                        (
                            "semantics",
                            "Tail-first should ACCEPT 1.85 bar (0.18 percent < 0.40 percent cap). "
                            "Cooler-first would only delay confirmation of the same legal absorber.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one tail-analyzer slot versus cooler-RTD group delay on this "
                            "absorber bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 166 us vs combined jitter ~58 us (tail 26 + cooler 32): 2.9x over "
                            "a 2.0x trust floor. Reversing order by < 166 us inside the 360 us "
                            "window would still show both channels under cap; ACCEPT either way.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "tail NOx analyzer, 2 kHz, 26 us jitter",
                    "cooler jacket RTD, 1 kHz, 32 us jitter",
                    "absorber PT (context)",
                    "weak-acid FT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("tail_cap_pct", 0.40),
                        ("observed_tail_pct", 0.18),
                        ("cooler_cap_C", 35.0),
                        ("observed_cooler_C", 18.0),
                        ("proposed_bar", 1.85),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Tower-T8 indexed on Ostwald-Gill OG-5; absorber 1.85 bar armed.",
                    "2. Tail NOx 0.18 percent; cooler 18 C under 35 C jacket cap.",
                    "3. Absorber-FT precursor at 1.080 ms.",
                    "4. Race window [5.080, 5.440] ms.",
                    "5. an.tail.pct 0.18 percent at 5.120 ms (winner).",
                    "6. rtd.cooler.C 18 C at 5.286 ms (loser by 166 us).",
                    "7. Gate at 5.740 ms: ACCEPT leave 1.85 bar.",
                    "8. Tail remains 0.18 percent < 0.40 percent; cooler unused as a hold.",
                    "9. Weak-acid sendout continues.",
                    "10. Delayed (dwell_s=360): 6 min stack-survey dwell after the pass.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "absorber_185"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("pressure_bar", 1.85),
                        ("hold", False),
                        ("weak_acid_tph", 22.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("tail_pct", 0.18),
                        ("tail_cap_pct", 0.40),
                        ("cooler_C", 18.0),
                        ("cooler_cap_C", 35.0),
                        ("proposed_bar", 1.85),
                        ("race_margin_us", 166),
                        ("combined_jitter_us", 58),
                        ("dwell_s", 360),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 1.85 bar because tail NOx 0.18 percent is under the 0.40 percent "
                "cap and cooler 18 C is under the 35 C jacket cap.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Tail 0.18 percent won by 166 us and sits under the 0.40 percent cap. Cooler 18 C "
                "is under 35 C. ACCEPT: leave 1.85 bar. A hold would idle a legal Ostwald absorber.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "tail_pct",
                            OrderedDict(
                                [
                                    ("cap", 0.40),
                                    ("observed", 0.18),
                                    ("executed_bar", 1.85),
                                ]
                            ),
                        ),
                        (
                            "cooler_C",
                            OrderedDict(
                                [
                                    ("cap", 35.0),
                                    ("observed", 18.0),
                                    ("under_cap", True),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 166),
                                    ("combined_jitter_us", 58),
                                    ("ratio", 2.86),
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
            ("name", "absorber_185"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("pressure_bar", 1.85),
                        ("hold", False),
                        ("weak_acid_tph", 22.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "ACCEPT: leave 1.85 bar. Routing relay.an.tail -> policy.abs_go. "
                "Cooler unused as a hold.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left T8 at 1.85 bar. Tail 0.18 percent beat cooler 18 C; both "
                "caps held. 6 min stack-survey dwell follows (dwell_s=360).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("absorber", "1.85 bar held as proposed"),
                        ("tail", "0.18 percent < 0.40 percent cap"),
                        ("cooler", "18 C < 35 C cap"),
                        ("survey", "6 min stack-survey dwell queued"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Cooler 18 C was never a trip; it only lost the race to a legal tail analyzer.",
                    "Delayed (dwell_s=360): 6 min stack-survey dwell after the pass on OG-5.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "an.tail.pct (5.120 ms, 0.18 percent)"),
                        ("loser", "rtd.cooler.C (5.286 ms, 18 C)"),
                        ("margin_us", 166),
                        (
                            "counterfactual_if_reversed",
                            "Cooler-first by < 166 us would still be under 35 C; a correct gate "
                            "ACCEPTs either way. Reversing would only have delayed confirmation of "
                            "the same legal absorber.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5740),
            (
                "reward_inflection_note",
                "Task and safety credit the correct ACCEPT at 5.740 ms (tick 4). The 6 min "
                "dwell is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 360.0),
            ("dwell_s", 360),
        ]
    )
    ras = raster_core(
        24,
        56,
        40,
        54,
        routing(
            "thalamic-relay.tail-nox",
            "spikenaut.policy.absorber-go",
            [
                ("relay.an.tail", "policy.abs_go", 0.69),
                ("relay.rtd.cooler", "policy.cool_hold", 0.24),
                ("relay.an.tail", "policy.abs_go", 0.11),
            ],
            "adenosine",
            0.08,
            "already_legal_stdp; adenosine at tail win (5.120 ms) tags the go bind",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("dwell_s", 360),
                ("delayed_surprise_s", 360),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.36),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("abs_go", 36, 0.50, 231.5, 3),
                    pop("cool_hold", 36, 0.80, 7.7, 0),
                    pop("nox_veto", 20, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r52-280",
        "Ostwald-Gill OG-5 / Tower-T8: tail NOx 0.18 percent beats cooler 18 C; correct ACCEPT "
        "of an already-legal 1.85 bar (total +1.14)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT. Tail 0.18 percent < 0.40 percent cap; cooler unused. "
        "total +1.14 = 0.44 + 0.30 + 0.20 + 0.12 + 0.08.",
        ras,
        gate,
        "nitric-acid-absorber",
        ["accept", "designed", "nox-tail", "already-legal", "absorber"],
        "Teaches an already-legal Ostwald absorber: both tail NOx and cooler jacket sit under "
        "cap; race order only confirms the ACCEPT.",
        5,
    )


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


def notes_text(jmax: float) -> str:
    return f"""# Thalamic Trajectory Factory — NOTES-r52

- Factory: `thalamic-trajectory-factory`
- Run label: `2026-09-02-final-heavy`
- Generator: `grok-4.6`
- Channel: SuperGrok Heavy consumer chat (RM-793 research-only)
- Quota: 5
- Quality: Q=5
- IDs: `ttf-r52-276` … `ttf-r52-280`
- Domains this batch: `phosphoric-attack-tank`, `hydrocracker-reactor`, `green-anode-press`, `continuous-anneal-line`, `nitric-acid-absorber`

These five domain slugs sit outside the prompt 8-pool and outside staged r13–r55 occupancy (jsonl SoT, including r49 methanol-synthesis-loop / RH-degasser, r51 anode-bake-furnace / methanol-converter, r53 alkylation-contactor / anode-bake, r55 sulfuric-contact-bed / kamyr). All five plants are invented. Do not restack prior TTF plants. Apatite-Vale / Gasoil-Brae / Green-Anode-Naze / Recryst-Holt / Ostwald-Gill are this round only.

## Batch map

| id | domain | decision | correctness | sim_or_real | total | edge |
|----|--------|----------|-------------|-------------|-------|------|
| ttf-r52-276 | phosphoric-attack-tank | MODIFY | correct | designed | **−0.47** | process-correct steam clamp; rubber-lining blister inside 42 ms raster; independent LIF |
| ttf-r52-277 | hydrocracker-reactor | REJECT | **incorrect (wrong-reject)** | designed | −0.58 | live drum 8.40 bar(g) < 9.00 cap; supervisor treats 9.41 bar(a) as bar(g) |
| ttf-r52-278 | green-anode-press | REJECT | correct | hil | +0.78 | mold AE 46 pps beats platen 118 C; hold ram |
| ttf-r52-279 | continuous-anneal-line | ACCEPT | correct | simulated | +1.16 | strip 718 C vs pyro glint 762; proposed 180 m/min already legal |
| ttf-r52-280 | nitric-acid-absorber | ACCEPT | correct | designed | +1.14 | tail NOx 0.18 pct vs cooler 18 C; proposed 1.85 bar already legal |

Gate mix: 2 ACCEPT, 1 correct MODIFY (partnered-neg, in-window), 1 correct REJECT, 1 incorrect REJECT (gauge-vs-absolute). Provenance: designed×3, simulated×1, hil×1 (Green-Anode-Naze GAN-HIL press pad). Intra-batch Jaccard on `state.description` {jmax:.3f} (< 0.4).

## Wrong-reject

**ttf-r52-277** is the mandated incorrect gate (`safety_decision.correctness=incorrect`, `meta.supervisor_error_type=wrong-reject`). Alternate vs odd rounds: even rounds host wrong-reject (r12/r14/…/r38/r44/r52); odd rounds host wrong-modify. Do not emit a wrong-ACCEPT. Error *class* is **stale-sample-as-live / lagged-historian**, not r16 reticle-as-wafer, not r18 empty-tank, not r20 oscillation-as-PSV, not r22 class-transplant, not r30 stale-firmware floor, not r32 stale-peak-hold, not r34 wrong-bus, not r36 unit-mismatch leftover-bar, not r38 loop-test-inject, not r44 wrong-unit-shadow.

Syngas-Brae SB-4 / Converter-C7 reads live bed `218.0 C` against a published **235.0 C** trip. A historian tag still prints **248.0 C** with `lag_s=42`. Sidecar arithmetic `218.0 < 235.0` is true. A weak supervisor binds the lagged sample as live, REJECT-holds recycle 38.0 → 0.0 t/h, and leaves a legal loop idle. Convictable without methanol physics: `evidence.live_bed_C < evidence.bed_trip_C`, `evidence.lag_s == 42`, `evidence.lag_fresh == false`, `executed_action` sets `recycle_tph=0` / `hold=true`, `raster.routing.table` sends `relay.hist.lag` → `policy.hold_reject` (weight 0.74) with no positive weight to `policy.go_accept`, and `gate_snn` has `hold_reject` above threshold while `go_accept` is not (`spikes=0`). Recovery: ACCEPT; leave 38.0 t/h; bind the published live 235.0 C trip. Cost: 18 min missed methanol-quality window (`missed_window_s=1080`).

## Partnered-negative in-window (276)

**ttf-r52-276** is the partnered negative: process-correct MODIFY (steam held 3.1 t/h; lining 83.6 C < 85.0 cap) while the world still charges. Safety −0.60 prices the 18 mm rubber-lining blister at **22.600 ms**; `task_progress` stays +0.30 because the clamp completed. Inflection `t_us=22600` is tick 5 and is **inside** the 42 ms raster (`22600 ≤ 42000`). Named un-netted loss: 14 min tank isolate (`abort_s=840`). Not folded into process heads.

Independent LIF (the one labeled sidecar sim): `state.sim_or_real` remains `designed`. `raster.excerpt_source=independent_lif`, `raster.sim_scope=sidecar_only`, `raster.lif` seed 52276, stim `[21400, 24800]`. Excerpt is membrane crossings (`lif.clamp` early vs `lif.blister` 21.4–24.8 ms), not a 1:1 remap of `spike_events`. `meta.tags` include `independent-lif-raster` and `sidecar-sim-only`.

## Reward formula and tick reconciliation

Declared aggregation on every record:

`total = task_progress + safety + efficiency + coherence + exploration`

Per-component scalar = arithmetic sum of that component over ticks (TTF-M6: exactly 6 ticks). Tick 6 is bound to a published sidecar (`abort_s`, `missed_window_s`, `survey_hold_s`, `dwell_s`) via `future_outcome.delayed_surprise_s` and is strictly after the raster window. Inflection `t_us` is an actual tick.

| id | ticks | tp | saf | eff | coh | exp | total | inflection tick |
|----|-------|----|-----|-----|-----|-----|-------|-----------------|
| 276 | 6 | +0.30 | −0.60 | −0.16 | +0.04 | −0.05 | −0.47 | 5 (22600) |
| 277 | 6 | −0.20 | −0.10 | −0.22 | −0.12 | +0.06 | −0.58 | 4 (4960) |
| 278 | 6 | +0.10 | +0.40 | +0.12 | +0.10 | +0.06 | +0.78 | 4 (6560) |
| 279 | 6 | +0.44 | +0.34 | +0.18 | +0.12 | +0.08 | +1.16 | 4 (4380) |
| 280 | 6 | +0.44 | +0.30 | +0.20 | +0.12 | +0.08 | +1.14 | 4 (5740) |

Tick-6 sidecar bind: 276 `abort_s=840`, 277 `missed_window_s=1080`, 278 `abort_s=540`, 279 `survey_hold_s=300`, 280 `dwell_s=360`.

## Raster / energy (Loihi-2 4-core, 23 pJ/spike)

| id | domain | n | rate Hz | window_ms | spikes | energy_pJ | energy_uJ |
|----|--------|---|---------|-----------|--------|-----------|-----------|
| 276 | phosphoric-attack-tank | 76 | 26 | 42 | 83 | 1909 | 0.001909 |
| 277 | methanol-synthesis-loop | 92 | 34 | 24 | 75 | 1725 | 0.001725 |
| 278 | anode-baking-furnace | 108 | 21 | 40 | 91 | 2093 | 0.002093 |
| 279 | continuous-anneal-line | 80 | 34 | 22 | 60 | 1380 | 0.001380 |
| 280 | nitric-acid-absorber | 56 | 40 | 24 | 54 | 1242 | 0.001242 |

`spikes = round(n × rate × window_s)`. Every record carries `gate_snn` whose `decision` matches the safety gate; populations that declare rate+spikes meet the same ±1 budget against `decision_window_s`. `routing.third_factor` has modulator (NA / ACh / DA / 5-HT / adenosine), `tau_e_s`/`tau_e_ms` pair, and eligibility. Excerpt same-neuron gap ≥ 1000 µs; spike trains same-channel refractory ≥ 0.8 ms. Non-276 excerpts are kernelized and independent of `spike_events` times (overlap < 0.8).

## Local checks (staging, not raw)

See generator stdout: `check_jsonl` FactoryStaging, `validate_run.check_line`, `dumps_exact_json`, `raster_status`, `verify_batch_for_frontier(strict=True)`, `spike_probe.py --strict`, tick sums, refractory, Jaccard.

Never `training_ready`. Never `sim_or_real=real`. Never wrote `outputs/raw/`.

## Residual weaknesses (honest)

1. Only **one** labeled independent LIF (276). The other four excerpts are independent of `spike_events` times but are not declared population sims.
2. Wrong-ACCEPT still absent (guard).
3. Tick-6 sidecar bind is standing machinery (r14+), not a new class.
4. Five domain slugs leave the prompt's 8-item pool; a later round that must stay inside the pool will have to rotate sit-outs instead.
5. 277 wrong-reject is sidecar-convictable (routing `to` / lag_s / lag_fresh) as a **new** error class (stale-sample-as-live) vs r32 stale-peak, r38 loop-test, r44 unit-shadow.
6. 279 and 280 are both already-legal ACCEPTs; a later round could pair an ACCEPT with a world charge that does not go negative.

## Next densification target

Labeled LIF on a second record, or an ISI histogram sidecar. Remaining unused wrong-REJECT subclasses include **sign-convention / gauge-vs-absolute**. Wrong-ACCEPT remains structurally absent until a prompt amendment.

{NOVEL_COVERAGE_LINE}
"""


def self_check(records, notes: str):
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
    if tuple(domains) != THIS_DOMAINS:
        issues.append(f"domain order {domains}")
    prior_domains, prior_plants = harvest_occupancy()
    if set(domains) & prior_domains:
        issues.append(f"restacked domains {set(domains) & prior_domains}")
    blob_all = "\n".join(json.dumps(r) for r in records)
    for plant in THIS_PLANTS:
        if plant not in blob_all:
            issues.append(f"missing plant {plant}")
        if plant in prior_plants:
            issues.append(f"restacked plant {plant}")
    wrong = [
        r
        for r in records
        if r["safety_decision"].get("correctness") == "incorrect"
        or r["meta"].get("supervisor_error_type")
    ]
    if len(wrong) != 1 or wrong[0]["id"] != "ttf-r52-277":
        issues.append(f"wrong-gate set {[w['id'] for w in wrong]}")
    if any(r["state"]["sim_or_real"] == "real" for r in records):
        issues.append("sim_or_real=real")
    hil = [r["id"] for r in records if r["state"]["sim_or_real"] == "hil"]
    if hil != ["ttf-r52-278"]:
        issues.append(f"hil set {hil}")
    decisions = [r["safety_decision"]["decision"] for r in records]
    if (
        decisions.count("ACCEPT") != 2
        or decisions.count("MODIFY") != 1
        or decisions.count("REJECT") != 2
    ):
        issues.append(f"gate mix {decisions}")
    if [r["id"] for r in records] != IDS:
        issues.append(f"ids {[r['id'] for r in records]}")
    for rec in records:
        blob = json.dumps(rec)
        if "training_ready" in blob:
            issues.append(f"{rec['id']} training_ready present")
        hidden = walk_keys(rec)
        if hidden:
            issues.append(f"{rec['id']} hidden keys {hidden}")
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
        overlap = excerpt_vs_spikes(rec)
        if rec["id"] == "ttf-r52-276":
            if rec["raster"].get("excerpt_source") != "independent_lif":
                issues.append("276 missing independent_lif")
            if rec["future_outcome"]["reward_inflection_t_us"] > rec["raster"]["window_ms"] * 1000:
                issues.append("276 inflection outside window")
            if rec["reward_components"]["total"] >= 0:
                issues.append("276 partnered-neg total not negative")
        elif overlap >= 0.8:
            issues.append(f"{rec['id']} excerpt overlap {overlap:.2f}")
        inf = rec["future_outcome"]["reward_inflection_t_us"]
        tick_times = [t["t_us"] for t in rec["reward_components"]["ticks"]]
        if inf not in tick_times:
            issues.append(f"{rec['id']} inflection {inf} not a tick")
        if len(rec["reward_components"]["ticks"]) != 6:
            issues.append(f"{rec['id']} tick count")
        delayed = rec["future_outcome"].get("delayed_surprise_s")
        if delayed is None:
            issues.append(f"{rec['id']} missing delayed_surprise_s")
        else:
            tick6 = rec["reward_components"]["ticks"][5]["t_us"]
            if tick6 != int(round(float(delayed) * 1e6)):
                issues.append(f"{rec['id']} tick6 {tick6} vs delayed {delayed}")
            if tick6 <= rec["raster"]["window_ms"] * 1000:
                issues.append(f"{rec['id']} tick6 inside raster")
        if not (8 <= len(rec["state"]["episode_steps"]) <= 15):
            issues.append(f"{rec['id']} episode_steps")
        if rec["gate_snn"]["decision"] != rec["safety_decision"]["decision"]:
            issues.append(f"{rec['id']} gate_snn decision mismatch")
        if rec["meta"]["round"] != 52:
            issues.append(f"{rec['id']} meta.round")
        if rec["meta"]["rights"]["intended_use"] != "research_only":
            issues.append(f"{rec['id']} rights")
        if rec["meta"]["rights"]["linear_issue"] != "RM-793":
            issues.append(f"{rec['id']} RM-793")
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
        exec_p = rec["executed_action"]["parameters"]
        prop_p = rec["proposed_action"]["parameters"]
        if rec["safety_decision"]["decision"] == "ACCEPT" and exec_p != prop_p:
            issues.append(f"{rec['id']} ACCEPT params differ")
        dw_s = rec["gate_snn"]["decision_window_ms"] / 1000.0
        for popu in rec["gate_snn"]["populations"]:
            if "mean_rate_hz" in popu:
                exp = round(popu["neurons"] * popu["mean_rate_hz"] * dw_s)
                if abs(popu["spikes"] - exp) > 1:
                    issues.append(
                        f"{rec['id']} gate_snn {popu['name']} spikes {popu['spikes']} vs {exp}"
                    )
        if not (8 <= len(rec["raster"]["excerpt"]) <= 16):
            issues.append(f"{rec['id']} excerpt n={len(rec['raster']['excerpt'])}")
        if rec["state"]["sim_or_real"] not in {"designed", "simulated", "hil"}:
            issues.append(f"{rec['id']} provenance")
        table_tos = {row["to"] for row in rec["raster"]["routing"]["table"]}
        if rec["id"] == "ttf-r52-277":
            if "policy.go_accept" in table_tos:
                issues.append("277 routing has go_accept")
            if "policy.hold_reject" not in table_tos:
                issues.append("277 missing hold_reject routing")
        win_ms = rec["raster"]["window_ms"]
        if not (20 <= win_ms <= 50):
            issues.append(f"{rec['id']} window_ms {win_ms}")
        for item in rec["raster"]["excerpt"]:
            if not (0 <= item["t_us"] <= win_ms * 1000):
                issues.append(f"{rec['id']} excerpt t_us {item['t_us']}")
            if not (0 <= item["neuron_id"] < rec["raster"]["neurons"]):
                issues.append(f"{rec['id']} neuron_id {item['neuron_id']}")
        tf = rec["raster"]["routing"]["third_factor"]
        tau_pair = abs(tf["tau_e_ms"] / 1000.0 - tf["tau_e_s"])
        if tau_pair > 1e-9:
            issues.append(f"{rec['id']} tau_e pair {tf}")
        pj_ok = abs(rec["raster"]["energy_pJ"] - rec["raster"]["spikes"] * 23) > 1e-6
        uj_ok = abs(rec["raster"]["energy_uJ"] - rec["raster"]["spikes"] * 23e-6) > 1e-9
        if pj_ok or uj_ok:
            issues.append(f"{rec['id']} energy")
    notes_hits = [ln for ln in notes.splitlines() if ln.strip().lower().startswith("novel coverage")]
    if notes_hits != [NOVEL_COVERAGE_LINE]:
        issues.append(f"novel coverage lines {notes_hits}")
    return issues, jmax


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
        BATCH_PATH, "batch-r52.jsonl", staging=FactoryStaging(enabled=True)
    )
    report.append(("check_jsonl FactoryStaging", errors, warnings, kinds, nrec))
    line_errs = []
    for i, rec in enumerate(records, 1):
        errs, kind = check_line(rec, f"batch-r52.jsonl:{i}", factory_staging=True)
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
    return report


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    records = [record_276(), record_277(), record_278(), record_279(), record_280()]
    # jmax needed for notes; compute once
    descs = [r["state"]["description"] for r in records]
    jmax = 0.0
    for i in range(5):
        for j in range(i + 1, 5):
            jmax = max(jmax, jaccard(descs[i], descs[j]))
    notes = notes_text(jmax)
    issues, jmax2 = self_check(records, notes)
    jmax = max(jmax, jmax2)
    notes = notes_text(jmax)
    issues, _ = self_check(records, notes)
    lines = [
        json.dumps(rec, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        for rec in records
    ]
    BATCH_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    NOTES_PATH.write_text(notes, encoding="utf-8")
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
            for w in warnings[:20]:
                print("  WARN", w)
        elif name == "check_line+exact_json":
            if item[1]:
                failed = True
                print("  LINE_ERRS", item[1])
        elif name == "raster_status":
            if item[1]:
                failed = True
                print("  RASTER_FAIL", item[1])
        elif name == "verify_batch_for_frontier":
            print("  counts", item[1], "blocked", item[3])
            if item[3]:
                failed = True
                print("  FINDINGS", item[2])
        elif name == "validate_novel_coverage":
            if item[1]:
                failed = True
        elif name == "spike_probe":
            if item[1] != 0:
                failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
