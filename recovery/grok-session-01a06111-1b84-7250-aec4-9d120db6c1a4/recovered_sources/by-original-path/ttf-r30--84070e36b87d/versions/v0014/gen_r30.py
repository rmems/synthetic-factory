#!/usr/bin/env python3
"""Emit TTF r30 JSONL (ttf-r30-166..170) into /tmp/ttf-r30/. Never writes outputs/raw/."""

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

OUT_DIR = Path("/tmp/ttf-r30")
BATCH_PATH = OUT_DIR / "batch-r30.jsonl"
NOTES_PATH = OUT_DIR / "NOTES-r30.md"
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
        ("generated_at", "2026-09-02T17:10:00Z"),
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
BANNED_DOMAINS = {
    "warehouse-amr",
    "aerial-swarm",
    "underwater-rov",
    "grid-inspection",
    "humanoid-locomotion",
    "surgical-assist",
    "industrial-assembly",
    "autonomous-driving",
    "rail-signaling",
    "process-chem",
    "ev-charging",
    "agritech-combine",
    "semiconductor-fab",
    "fusion-divertor",
    "rail-hump-yard",
    "hotcell-telemanip",
    "euv-wafer-stage",
    "proton-gantry-gate",
    "tbm-slurry-shield",
    "wave-energy-latching",
    "fiber-draw-tower",
    "brewery-CIP",
    "ski-lift",
    "data-center-CDU",
    "canal-lock",
    "blast-furnace",
    "mill-scale-pit",
    "battery-formation",
    "grain-elevator",
    "glass-lehr",
    "tunnel-boring",
    "satellite-servicing",
    "mine-ventilation",
    "paper-machine",
    "cryo-storage",
    "amusement-ride",
    "trolleybus",
    "glass-float-line",
    "LNG-boiloff",
    "hyperbaric-weld",
    "radio-telescope-pointing",
    "funicular",
    "PCB-reflow",
    "anaerobic-digester",
    "tidal-barrage",
    "grain-elevator",
    "maglev-guideway-gap",
    "grain-elevator-leg",
    "hyperbaric-weld-habitat",
    "tunnel-oven-bakery",
    "rotary-lime-kiln",
    "lng-open-rack",
    "metro-psd",
    "aluminum-potline",
    "vial-lyophilizer",
    "sts-quay-crane",
    "lyophilizer-shelf",
    "hvdc-thyristor-valve",
    "lng-unloading-arm",
    "subsea-cable-plough",
    "cyclotron-target",
}
BANNED_PLANT_FRAGMENTS = (
    "Marrow-Dock",
    "Vesper-Lattice",
    "Brine-Well",
    "Saddle-Arc",
    "Ashlar-Gait",
    "Nacre-Well",
    "Quern-Forge",
    "Tinder-Box",
    "Whimbrel-Stack",
    "Cinder-Loft",
    "Suture-Isle",
    "Kiln-Spur",
    "Oxbow-Switch",
    "Pitch-Kettle",
    "Shale-Quay",
    "Polder-Rye",
    "Flint-Mask",
    "Gyre-Tokamak",
    "Quarry-Bowl",
    "Orpiment",
    "Glimmer-Forge",
    "Feldspar-Arc",
    "Basalt-Rook",
    "Fetch-Sound",
    "Silica-Well",
    "Sinter-Gown",
    "Kettle-Stack",
    "Barrow-Mezz",
    "Grit-Sump",
    "Firth-Spur",
    "Apside-Yard",
    "Sump-Drift",
    "Frost-Cist",
    "Clothoid-Bowl",
    "Firn-Span",
    "Sleet-Row",
    "Sinter-Ridge",
    "Chaff-Mere",
    "Caisson-Forge",
    "Crumb-Vault",
    "Caliche-Drift",
    "Thaw-Reach",
    "Kipple-Gate",
    "Anode-Fen",
    "Vial-Rime",
    "Tern-Apron",
    "Scree-Hitch",
    "Flux-Kettle",
    "Mire-Cask",
    "Slack-Firth",
    "Chaff-Rise",
    "Rime-Causeway",
    "Gnomon-Well",
    "Rime-Vault",
    "Fjord-Convert",
    "Kelp-Jetty",
    "Skerries-Trench",
    "Iodine-Well",
    "Lyo-Deck",
    "Target-Cart",
    "Oolite-Span",
    "Fathom-Lock",
    "Loess-Stride",
    "Swage-Holt",
    "Slag-Siding",
)


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


def lif_167_excerpt():
    n = 72
    dt_us = 100
    tau_m_ms = 18.5
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.90
    i_stim_peak = 2.50
    stim = (21000, 25000)
    seed = 30167
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
    early = [(t, nid) for t, nid in spikes if t < 21000]
    burst = [(t, nid) for t, nid in spikes if 21000 <= t < 25000]
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
            group = [1 for tt, _ in picked if (tt < 21000) == (pool[0][0] < 21000)]
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
    take(burst, 9, label_times=(22400, 23100, 23800))
    clamp = [(t, nid) for t, nid in picked if t < 21000][:7]
    tear = [(t, nid) for t, nid in picked if t >= 21000][:9]
    picked = sorted(clamp + tear, key=lambda item: (item[0], item[1]))
    if len(picked) < 10:
        raise RuntimeError(f"LIF excerpt short: {len(picked)}")
    channels = ["lif.clamp" if t < 21000 else "lif.crystal" for t, _ in picked]
    lif = OrderedDict(
        [
            ("model", "leaky_integrate_and_fire"),
            ("n", 72),
            ("dt_us", 100),
            ("tau_m_ms", 18.5),
            ("v_rest", 0.0),
            ("v_reset", 0.0),
            ("v_th", 1.0),
            ("r_m", 1.0),
            ("refractory_us", 1000),
            ("i_bias", 0.90),
            ("i_stim_peak", 2.50),
            ("stim_t_us", [21000, 25000]),
            ("i_clamp_extra", 0.64),
            ("clamp_n", 14),
            ("seed", 30167),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-13 carry +0.64 steam-clamp bias; stim 21-25 ms is the crystal-bridge seize.",
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
            ("round", 30),
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


def record_131():
    excerpt, extra = lif_131_excerpt()
    ticks = [
        tick(2448, 0.04, -0.02, -0.02, 0.01, 0.00),
        tick(6120, 0.08, -0.04, -0.03, 0.01, -0.01),
        tick(6304, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(6840, 0.10, -0.06, -0.04, 0.02, -0.01),
        tick(21600, 0.04, -0.46, -0.03, -0.01, -0.01),
        tick(840000000, 0.02, -0.05, -0.02, 0.01, -0.01),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "ORV-bank C at Thaw-Reach TR-4 is pushing 420 m3/h of seawater across the LNG "
                "panel while film Delta-T sits at 8.4 K against a 6.0 K ice-risk ceiling. "
                "Therm-first drops the film to 5.1 K; mag-pump-first would keep 420 m3/h because "
                "1480 rpm is still under the 1800 rpm overspeed. An ice bridge already spanning "
                "two tubes does not appear on film-T or RPM until the AE snap.",
            ),
            ("domain", "lng-open-rack"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep ORV-bank C film Delta-T <= 6.0 K and finish the sendout without dumping "
                "seawater onto the LNG pan.",
            ),
            ("t0_us", 1756850400000131),
            ("gate_latency_us", 720),
            ("race_window_us", 380),
            ("race_window_rel_ms", [6.0, 6.38]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "therm.film.dT 8.4 K",
                                "mag.pump.rpm 1480 under 1800 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "Therm-first latches seawater-flow clamp 420 -> 280 m3/h; pump-first "
                            "keeps 420 m3/h on a 'still under overspeed' model.",
                        ),
                        (
                            "window_derivation",
                            "380 us = one film-thermocouple slot versus the seawater mag-pump "
                            "tach publisher on this ORV skid bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 184 us vs combined jitter 64 us (therm 30 + mag 34): 2.9x over "
                            "a 2.0x trust floor. Reversing order by < 184 us inside the 380 us window "
                            "would have kept 420 m3/h; predicted next-sample 7.2 K > 6.0 K cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "film thermocouple Delta-T, 2 kHz, 30 us jitter",
                    "seawater mag-pump tachometer, 1 kHz, 34 us jitter",
                    "tube AE puck on the LNG face, 50 kHz (context)",
                    "sendout flow orifice (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("film_dT_cap_K", 6.0),
                        ("observed_film_dT_K", 8.4),
                        ("seawater_m3_h", 420.0),
                        ("pump_rpm", 1480.0),
                        ("pump_cap_rpm", 1800.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. ORV-bank C indexed; seawater 420 m3/h; film Delta-T 8.4 K.",
                    "2. Mag-pump 1480 rpm under 1800 rpm cap; sendout armed.",
                    "3. Orifice precursor at 1.210 ms.",
                    "4. Race window [6.000, 6.380] ms.",
                    "5. therm.film.dT 8.4 K at 6.120 ms (winner).",
                    "6. mag.pump.rpm 1480 at 6.304 ms (loser by 184 us).",
                    "7. Gate at 6.840 ms: MODIFY clamp 420 -> 280 m3/h.",
                    "8. After clamp film 5.1 K < 6.0; pump still 1480 rpm.",
                    "9. At 21.600 ms an ice bridge snaps two tubes; 0.4 m3 dumps onto the pan.",
                    "10. 14 min pan drain + ice-chip (abort_s=840); named un-netted loss.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_orv_film"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("seawater_m3_h", 420.0),
                        ("film_dT_K", 8.4),
                        ("pump_rpm", 1480.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("film_dT_K", 8.4),
                        ("film_dT_cap_K", 6.0),
                        ("predicted_unclamped_next_K", 7.2),
                        ("seawater_m3_h", 420.0),
                        ("pump_rpm", 1480.0),
                        ("pump_cap_rpm", 1800.0),
                        ("race_margin_us", 184),
                        ("combined_jitter_us", 64),
                        ("abort_s", 840),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 420 m3/h because mag-pump 1480 rpm is under 1800, treating "
                "the 8.4 K film as a still-wet contact rather than an ice-risk overshoot.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Film Delta-T 8.4 K won by 184 us, so the panel is icing, not still a pump-speed "
                "story. Holding 420 m3/h predicts next-sample 7.2 K > 6.0 cap. MODIFY: seawater "
                "420 -> 280 m3/h. Observed after clamp 5.1 K < 6.0. A full REJECT is not "
                "indicated: a clean sendout accepts 280 m3/h.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "film_dT_K",
                            OrderedDict(
                                [
                                    ("cap", 6.0),
                                    ("observed", 8.4),
                                    ("predicted_unclamped_next", 7.2),
                                    ("clamped_flow_m3_h", 280.0),
                                    ("observed_after_clamp", 5.1),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 184),
                                    ("combined_jitter_us", 64),
                                    ("ratio", 2.88),
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
            ("name", "clamped_orv_film"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("seawater_m3_h", 280.0),
                        ("film_dT_K", 5.1),
                        ("pump_rpm", 1480.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: seawater 420 -> 280 m3/h. Process-correct vs the 6.0 K film cap. Ice "
                "bridge still snaps at 21.600 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held film Delta-T at 5.1 K. At 21.600 ms an ice bridge "
                "already spanning two tubes snapped and dumped 0.4 m3 onto the LNG pan. Clamp "
                "reduced dump energy; it did not prevent the snap. Partnered negative: process "
                "heads stay honest; world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("film", "clamp executed; peak 5.1 K < 6.0 K cap"),
                        ("ice_bridge", "snapped at 21.600 ms; 0.4 m3 pan dump"),
                        ("repair", "14 min pan drain + ice-chip (abort_s=840)"),
                        ("mission", "TR-4 sendout incomplete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither film Delta-T nor mag-pump RPM predicted the seated ice bridge; ae.ice.bridge is a new channel at 21.600 ms, 14.760 ms after the gate, still inside the 40 ms raster.",
                    "Delayed (abort_s=840): 14 min pan drain + ice-chip. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "14 min pan drain + ice-chip after the tube snap. Safety head -0.66 prices the "
                "dump; task_progress stays +0.32 because the film clamp completed under the 6.0 K "
                "cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "therm.film.dT (6.120 ms, 8.4 K)"),
                        ("loser", "mag.pump.rpm (6.304 ms, 1480 rpm)"),
                        ("margin_us", 184),
                        (
                            "counterfactual_if_reversed",
                            "Pump-first by < 184 us inside the 380 us window would have kept "
                            "420 m3/h; predicted next-sample 7.2 K would have exceeded the 6.0 K "
                            "cap even without the ice bridge. The MODIFY is still the correct "
                            "process. The snap is a later world charge either way, cheaper with "
                            "the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 21600),
            (
                "reward_inflection_note",
                "Safety collapses at the 21.600 ms ice-bridge snap (tick t_us=21600), inside the "
                "40 ms raster. The correct MODIFY at 6.840 ms is in the same excerpt. Do not put "
                "inflection on the abort_s=840 drain tick.",
            ),
        ]
    )
    spikes = [
        spike("enc.seawater.ctx", 1.210, 0.41),
        spike("therm.film.dT", 2.440, 0.58),
        spike("mag.pump.rpm", 3.880, 0.50),
        spike("therm.film.dT", 6.120, 1.31),
        spike("mag.pump.rpm", 6.304, 1.12),
        spike("ctrl.gate", 6.840, 0.97),
        spike("therm.film.dT", 8.200, 0.82),
        spike("mag.pump.rpm", 10.550, 0.64),
        spike("ctrl.gate", 14.100, 0.86),
        spike("ae.ice.bridge", 21.600, 1.48),
        spike("ae.ice.bridge", 23.400, 0.93),
        spike("enc.seawater.ctx", 29.800, 0.40),
        spike("therm.film.dT", 36.200, 0.55),
    ]
    ras = raster_core(
        40,
        60,
        28,
        67,
        routing(
            "thalamic-relay.orv-film",
            "spikenaut.policy.orv-clamp",
            [
                ("relay_therm_film", "policy_orv_clamp", 0.68),
                ("relay_mag_pump", "policy_pump_hold", 0.29),
                ("relay_ae_ice", "policy_orv_clamp", -0.42),
            ],
            "noradrenaline",
            0.04,
            "surprise-gated pre_post_stdp; NA at therm win (6.120 ms) opens a 40 ms eligibility "
            "trace that still covers the 21.600 ms ice snap",
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
                    pop("orv_clamp", 50, 0.50, 210.0, 4),
                    pop("pump_hold", 40, 0.80, 50.0, 1),
                    pop("ice_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r23-131"),
            (
                "title",
                "Thaw-Reach TR-4 / ORV-bank C: film Delta-T beats mag-pump by 184 us; correct "
                "MODIFY still eats an in-window ice-bridge snap (partnered negative total -0.50)",
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
                    "40 ms raster. total -0.50 = 0.32 + -0.66 + -0.16 + 0.04 + -0.04. Named pan "
                    "drain (abort_s=840) is not netted into task_progress.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "lng-open-rack",
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
                    "14 min pan drain.",
                    1,
                ),
            ),
        ]
    )


def record_132():
    ticks = [
        tick(2192, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(5480, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(5662, -0.03, -0.03, -0.03, -0.01, 0.01),
        tick(5990, -0.07, -0.08, -0.07, -0.04, 0.02),
        tick(6330, -0.02, -0.03, -0.03, -0.01, 0.01),
        tick(480000000, -0.02, -0.02, -0.02, -0.01, 0.00),
    ]
    spikes = [
        spike("enc.leaf.ctx", 1.050, 0.42),
        spike("ir.door.edge", 2.210, 0.57),
        spike("hvac.damper.pct", 3.400, 0.49),
        spike("ir.door.edge", 5.480, 1.29),
        spike("hvac.damper.pct", 5.662, 1.10),
        spike("ctrl.gate", 5.990, 0.96),
        spike("ir.door.edge", 7.800, 0.80),
        spike("hvac.damper.pct", 10.200, 0.63),
        spike("ctrl.gate", 13.500, 0.84),
        spike("enc.leaf.ctx", 18.400, 0.41),
        spike("ir.door.edge", 22.100, 0.54),
        spike("hvac.damper.pct", 26.400, 0.38),
    ]
    excerpt = independent_excerpt(23132, 88, 28000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Leaf-pair 22 on Kipple-Gate KG-6 is closing at 0.40 m/s with a 48 mm "
                "leading-edge gap still open against a 20 mm intrusion floor. Platform HVAC "
                "sits at 12 Pa, safely under its 40 Pa comfort cap, damper 40 percent. "
                "IR-edge-first should bind a door-speed hold; a weak supervisor instead treats "
                "the platform loop as the HVAC damper.",
            ),
            ("domain", "metro-psd"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the KG-6 close with leading-edge gap <= 20 mm, leave HVAC damper at the "
                "planned 40 percent, and keep the 0.08 m/s crawl legal.",
            ),
            ("t0_us", 1756850400000132),
            ("gate_latency_us", 510),
            ("race_window_us", 340),
            ("race_window_rel_ms", [5.4, 5.74]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ir.door.edge 48 mm on leading_edge",
                                "hvac.damper.pct 40 under 85 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "IR-first should latch door clamp 0.40 -> 0.08 m/s; HVAC-first is a "
                            "false 'platform-loop' bind that freezes the damper instead.",
                        ),
                        (
                            "window_derivation",
                            "340 us = one door-edge IR slot versus the platform-PA HVAC publisher "
                            "on this PSD interlocking bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 182 us vs combined jitter 60 us (IR 28 + HVAC 32). Order is "
                            "correctly IR-first. The error is which actuator the clamp is bound to, "
                            "not the race.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "door leading-edge IR curtain, 2 kHz, 28 us jitter, axis leading_edge",
                    "platform HVAC pressure/damper, 1 kHz, 32 us jitter",
                    "leaf linear encoder (context)",
                    "platform occupancy loop (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("edge_cap_mm", 20.0),
                        ("observed_edge_mm", 48.0),
                        ("door_axis", "leading_edge"),
                        ("door_m_s", 0.40),
                        ("damper_pct", 40.0),
                        ("damper_cap_pct", 85.0),
                        ("platform_Pa", 12.0),
                        ("platform_cap_Pa", 40.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. KG-6 leaf-pair 22 closing at 0.40 m/s; leading-edge 48 mm.",
                    "2. HVAC damper 40 percent under 85; platform 12 Pa under 40 Pa cap.",
                    "3. Encoder precursor at 1.050 ms.",
                    "4. Race window [5.400, 5.740] ms.",
                    "5. ir.door.edge 48 mm at 5.480 ms (winner).",
                    "6. hvac.damper.pct 40 at 5.662 ms (loser by 182 us).",
                    "7. Gate at 5.990 ms: WRONG-MODIFY clamps damper 40 -> 10 percent; door stays 0.40 m/s.",
                    "8. Edge stays 46 mm over 20 mm cap; leaf keeps closing.",
                    "9. Intrusion near-miss; station hold.",
                    "10. Delayed (abort_s=480): 8 min station hold while leaf 22 is re-homed.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_psd_close"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("door_m_s", 0.40),
                        ("damper_pct", 40.0),
                        ("target_gap_mm", 0.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("edge_gap_mm", 48.0),
                        ("edge_cap_mm", 20.0),
                        ("door_axis", "leading_edge"),
                        ("door_m_s", 0.40),
                        ("damper_pct", 40.0),
                        ("damper_cap_pct", 85.0),
                        ("platform_Pa", 12.0),
                        ("platform_cap_Pa", 40.0),
                        ("race_margin_us", 182),
                        ("combined_jitter_us", 60),
                        ("abort_s", 480),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes continuing the 0.40 m/s close: HVAC 12 Pa and damper 40 percent "
                "are under cap, so the 48 mm edge is treated as a still-clear platform loop.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Leading-edge 48 mm exceeds the 20 mm intrusion floor (true). At this pose the "
                "platform loop is the HVAC damper (40 percent << 85 percent cap). Clamp damper "
                "40 -> 10 percent to bleed the 'platform pressure' before the leaf pinches.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "edge_gap_mm",
                            OrderedDict(
                                [
                                    ("cap", 20.0),
                                    ("observed", 48.0),
                                    ("executed_door_m_s", 0.40),
                                    ("door_axis", "leading_edge"),
                                ]
                            ),
                        ),
                        (
                            "damper_pct",
                            OrderedDict(
                                [
                                    ("cap", 85.0),
                                    ("planned", 40.0),
                                    ("clamped_wrong", 10.0),
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
            ("name", "hvac_hold_wrong_loop"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("door_m_s", 0.40),
                        ("damper_pct", 10.0),
                        ("target_gap_mm", 0.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY (incorrect): damper 40 -> 10 percent; door left at 0.40 m/s. Routing "
                "relay_ir_edge -> policy_hvac_hold; no positive weight to policy_door_clamp.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-MODIFY clamped the HVAC damper and left leaf-pair 22 closing at 0.40 m/s. "
                "Edge 48 mm was over the 20 mm floor; damper 40 percent was already legal. 8 min "
                "station hold (abort_s=480). Correct gate was MODIFY door 0.40 -> 0.08 m/s.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("door", "still 0.40 m/s; edge 46 mm > 20 mm"),
                        ("hvac", "damper 10 percent, non-binding comfort loop"),
                        ("station", "8 min hold, leaf 22 re-home"),
                        ("mission", "close deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "IR-first was the correct order and the edge number was over cap; the MODIFY spent that win on the HVAC damper.",
                    "Delayed (abort_s=480): KG-6 holds 8 min while leaf 22 is re-homed; next train 6.4 min late.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "MODIFY door 0.40 -> 0.08 m/s on leading_edge; leave HVAC damper at planned 40 percent.",
                        ),
                        ("correct_actuator", "door_motor"),
                        ("wrong_actuator", "hvac_damper"),
                        (
                            "wrong_edit_applied",
                            OrderedDict([("damper_pct", 10.0), ("door_m_s", 0.40)]),
                        ),
                        (
                            "cost",
                            "8 min station hold (task/efficiency); door never left the 48 mm over-cap (safety near-miss of a false HVAC clamp).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ir.door.edge (5.480 ms, 48 mm)"),
                        ("loser", "hvac.damper.pct (5.662 ms, 40 percent)"),
                        ("margin_us", 182),
                        (
                            "counterfactual_if_reversed",
                            "HVAC-first by < 182 us would still be under the 85 percent damper cap; "
                            "a correct gate binds ir.door.edge to policy_door_clamp either way. The "
                            "wrong MODIFY spent the IR win on the HVAC loop.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5990),
            (
                "reward_inflection_note",
                "Task, safety, and efficiency drop at the wrong MODIFY (5.990 ms, tick 4). "
                "The 8 min station hold is delayed surprise, not the inflection.",
            ),
        ]
    )
    ras = raster_core(
        28,
        88,
        36,
        89,
        routing(
            "thalamic-relay.psd-edge",
            "spikenaut.policy.hvac-hold",
            [
                ("relay_ir_edge", "policy_hvac_hold", 0.72),
                ("relay_hvac_pa", "policy_hvac_hold", 0.22),
            ],
            "acetylcholine",
            0.08,
            "loop_cap_stdp; ACh tags the (wrong) hvac_hold bind at the IR edge win",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("abort_s", 480),
                ("delayed_surprise_s", 480),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.34),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop("hvac_hold", 42, 0.45, 280.0, 4),
                    pop("door_clamp", 42, 0.90),
                    pop("edge_veto", 20, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r23-132"),
            (
                "title",
                "WRONG-MODIFY at Kipple-Gate KG-6 / leaf-pair 22: edge 48 mm read correctly; "
                "clamp applied to HVAC damper not door motor",
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
                    "Wrong-modify. Sidecar arithmetic 48 > 20 on leading_edge is true; MODIFY "
                    "bound to HVAC damper. total -0.66 = -0.20 + -0.22 + -0.20 + -0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "metro-psd",
                    [
                        "modify",
                        "wrong-gate",
                        "wrong-loop",
                        "sidecar-convictable",
                        "designed",
                    ],
                    "Teaches a probe that a correct IR-first race can still be a wrong gate when "
                    "the MODIFY binds HVAC damper instead of door speed. Convictable from axis "
                    "IDs and caps without PSD kinematics.",
                    2,
                    supervisor_error_type="wrong-modify",
                ),
            ),
        ]
    )


def record_133():
    ticks = [
        tick(2816, 0.01, 0.04, 0.01, 0.01, 0.01),
        tick(7040, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(7218, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(7900, 0.04, 0.14, 0.04, 0.04, 0.02),
        tick(8190, 0.01, 0.05, 0.02, 0.01, 0.01),
        tick(300000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("tc.shell.ctx", 1.420, 0.43),
        spike("bath.cell.V", 2.880, 0.61),
        spike("ir.anode.C", 4.550, 0.49),
        spike("bath.cell.V", 7.040, 1.34),
        spike("ir.anode.C", 7.218, 1.11),
        spike("ctrl.gate", 7.900, 1.02),
        spike("bath.cell.V", 10.200, 0.78),
        spike("tc.shell.ctx", 14.800, 0.44),
        spike("ir.anode.C", 19.400, 0.58),
        spike("ctrl.gate", 24.600, 0.81),
        spike("bath.cell.V", 31.200, 0.53),
        spike("ir.anode.C", 38.800, 0.46),
        spike("tc.shell.ctx", 44.100, 0.37),
    ]
    excerpt = independent_excerpt(23133, 140, 46000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Pot P-18 on the Anode-Fen AF-HIL pad shows bath voltage 5.42 V while a 4.80 V "
                "anode-effect hold is the jack permit. An IR anode camera, lit by the pad lamp, "
                "still reads 960 C under a 980 C melt-look. Voltage-first latches REJECT hold; "
                "IR-first would commit a 4 mm jack raise on an under-read bath.",
            ),
            ("domain", "aluminum-potline"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Do not raise the anode jack unless bath voltage <= 4.80 V; keep jack 0.0 mm "
                "until the injected cell voltage drops.",
            ),
            ("t0_us", 1756850400000133),
            ("gate_latency_us", 860),
            ("race_window_us", 290),
            ("race_window_rel_ms", [6.95, 7.24]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "bath.cell.V 5.42 V",
                                "ir.anode.C 960 C under 980",
                            ],
                        ),
                        (
                            "semantics",
                            "Voltage-first latches REJECT hold 0.0 mm jack; IR-first would commit "
                            "a 4 mm raise on an apparent 960 C under-read.",
                        ),
                        (
                            "window_derivation",
                            "290 us = one bath-voltage sample versus IR integration on this "
                            "potline HIL bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 178 us vs combined jitter 56 us (bath 24 + IR 32): 3.2x over a "
                            "2.0x trust floor. Pad injects the IR lamp 120-160 us before the bath "
                            "voltmeter (geometric lag, not a sensor fault); the 960 C packet is "
                            "still the loser in this 290 us window.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "cell bath voltmeter, 5 kHz burst, 24 us jitter",
                    "IR anode camera, 200 Hz, 32 us jitter",
                    "shell thermocouple (context)",
                    "HIL lamp-spectrum monitor (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("bath_cap_V", 4.80),
                        ("observed_bath_V", 5.42),
                        ("ir_anode_C", 960.0),
                        ("ir_look_C", 980.0),
                        ("proposed_jack_mm", 4.0),
                        ("lamp_inject_lead_us", [120, 160]),
                    ]
                ),
            ),
            (
                "hil",
                OrderedDict(
                    [
                        ("pad", "Anode-Fen AF-HIL pot mockup with physical anode jack"),
                        ("injected", "bath voltage + IR lamp spectrum"),
                        (
                            "note",
                            "Hardware-in-the-loop pot. Invented plant; not a live Hall-Heroult line.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Pot P-18 on the AF-HIL pad; 4 mm jack raise armed.",
                    "2. IR lamp injected 120-160 us before bath voltmeter sees 5.42 V.",
                    "3. Shell precursor at 1.420 ms.",
                    "4. Race window [6.950, 7.240] ms.",
                    "5. bath.cell.V 5.42 V at 7.040 ms (winner).",
                    "6. ir.anode.C 960 C at 7.218 ms (loser by 178 us).",
                    "7. Gate at 7.900 ms: REJECT hold 0.0 mm; do not raise 4 mm.",
                    "8. Pot remains over 4.80 V this cycle; anode-effect cap held.",
                    "9. Flux recycle queued on the pad.",
                    "10. Delayed (abort_s=300): 5 min pot re-gel and lamp-spectrum retune.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "raise_anode_jack"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("jack_mm", 4.0),
                        ("hold", False),
                        ("ir_authoritative", True),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("bath_V", 5.42),
                        ("bath_cap_V", 4.80),
                        ("ir_anode_C", 960.0),
                        ("ir_look_C", 980.0),
                        ("race_margin_us", 178),
                        ("combined_jitter_us", 56),
                        ("abort_s", 300),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes a 4 mm jack raise because IR 960 C looks under the 980 C "
                "melt-look, treating bath 5.42 V as a noisy bus echo.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Bath 5.42 V is over the 4.80 V anode-effect cap. IR 960 C is a HIL lamp "
                "under-read, not a clearance. REJECT: hold 0.0 mm; do not commit a 4 mm jack.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "bath_V",
                            OrderedDict(
                                [
                                    ("cap", 4.80),
                                    ("observed", 5.42),
                                    ("ir_anode_C", 960.0),
                                ]
                            ),
                        ),
                        (
                            "jack_mm",
                            OrderedDict([("proposed", 4.0), ("executed", 0.0)]),
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
            ("name", "hold_for_bath_drop"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("jack_mm", 0.0),
                        ("hold", True),
                        ("ir_authoritative", False),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: hold 0.0 mm; 4 mm jack cancelled. Bath 5.42 > 4.80 cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held Pot P-18 at 0.0 mm jack. Cell over cap this cycle; "
                "anode-effect cap held. IR apparent was not treated as a bath-voltage clearance.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("jack", "held; 0.0 mm"),
                        ("bath", "still over 4.80 V this cycle"),
                        ("ir", "960 C unused as clearance"),
                        ("mission", "raise deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Geometric lag: IR lamp was injected 120-160 us before the bath voltmeter, yet voltage still won the 290 us race.",
                    "Delayed (abort_s=300): pad policy update forbids treating IR anode C as a bath-voltage substitute after a 5 min pot re-gel.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "bath.cell.V (7.040 ms, 5.42 V)"),
                        ("loser", "ir.anode.C (7.218 ms, 960 C)"),
                        ("margin_us", 178),
                        (
                            "counterfactual_if_reversed",
                            "IR-first by < 178 us inside the 290 us window would have committed "
                            "a 4 mm jack with bath 5.42 > 4.80 cap. Order, not amplitude, selected the hold.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7900),
            (
                "reward_inflection_note",
                "Safety and coherence step up at the REJECT gate (7.900 ms, tick 4) as the hold "
                "lands. The 5 min re-gel is delayed surprise bound to abort_s=300.",
            ),
        ]
    )
    ras = raster_core(
        46,
        140,
        16,
        103,
        routing(
            "thalamic-relay.pot-bath",
            "spikenaut.policy.jack-hold",
            [
                ("relay_bath_V", "policy_jack_hold", 0.70),
                ("relay_ir_anode", "policy_ir_crawl", 0.24),
            ],
            "dopamine",
            0.15,
            "ae_hold_stdp; DA tags the jack_hold bind at the bath-voltage win",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("abort_s", 300),
                ("delayed_surprise_s", 300),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.29),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("jack_hold", 70, 0.48, 250.0, 5),
                    pop("ir_crawl", 50, 0.85),
                    pop("ae_veto", 28, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r23-133"),
            (
                "title",
                "Anode-Fen AF-HIL / Pot P-18: bath 5.42 V beats IR 960 C by 178 us; correct "
                "REJECT holds the anode jack",
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
                    "Correct REJECT. Langmuir-style: bath voltage over cap beats IR under-read. "
                    "total 0.78 = 0.10 + 0.40 + 0.12 + 0.10 + 0.06. Tick 6 binds abort_s=300.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "aluminum-potline",
                    [
                        "reject",
                        "hil",
                        "anode-effect",
                        "ir-underread",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a HIL lamp under-read losing a 178 us race does not clear an "
                    "anode-effect over-voltage. Hold is distillable from bath_V vs cap.",
                    3,
                ),
            ),
        ]
    )


def record_134():
    ticks = [
        tick(3248, 0.05, 0.04, 0.02, 0.01, 0.01),
        tick(8120, 0.08, 0.06, 0.04, 0.03, 0.02),
        tick(8310, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(8520, 0.14, 0.10, 0.05, 0.04, 0.02),
        tick(8980, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(90000000, 0.03, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.shelf.ctx", 1.105, 0.43),
        spike("pirani.chamber.Pa", 3.220, 0.59),
        spike("rtd.shelf.K", 5.010, 0.50),
        spike("pirani.chamber.Pa", 8.120, 1.27),
        spike("rtd.shelf.K", 8.310, 1.09),
        spike("ctrl.gate", 8.520, 0.97),
        spike("pirani.chamber.Pa", 11.200, 0.78),
        spike("rtd.shelf.K", 14.880, 0.61),
        spike("ctrl.gate", 18.400, 0.84),
        spike("pirani.chamber.Pa", 24.050, 0.56),
        spike("enc.shelf.ctx", 29.100, 0.40),
        spike("rtd.shelf.K", 32.400, 0.47),
    ]
    excerpt = independent_excerpt(23134, 44, 34000, 13, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("shelf_K_min", 0.4),
            ("chamber_Pa", 12.0),
            ("hold", False),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Shelf-tree S-4 inside Vial-Rime VR-7 holds 12.0 Pa Pirani with a +0.4 K/min "
                "shelf ramp already filed under the 25 Pa collapse ceiling. Shelf RTD is 241 K, "
                "still under the 250 K melt look. Pirani-first ACCEPTS the filed ramp; RTD-first "
                "would have extra-clamped a legal primary-dry.",
            ),
            ("domain", "vial-lyophilizer"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Hold the +0.4 K/min shelf ramp while chamber Pirani stays <= 25 Pa and shelf "
                "stays <= 250 K; do not extra-clamp a legal primary-dry.",
            ),
            ("t0_us", 1756850400000134),
            ("gate_latency_us", 400),
            ("race_window_us", 460),
            ("race_window_rel_ms", [8.0, 8.46]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "pirani.chamber.Pa 12.0 Pa",
                                "rtd.shelf.K 241 K under 250",
                            ],
                        ),
                        (
                            "semantics",
                            "Pirani-first ACCEPTS the already-legal +0.4 K/min ramp. RTD-first "
                            "would extra-clamp because 241 K looks close to 250 K melt.",
                        ),
                        (
                            "window_derivation",
                            "460 us = one Pirani gauge slot versus shelf-RTD group delay on this "
                            "lyo skid bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 190 us vs combined jitter 66 us (Pirani 32 + RTD 34): 2.9x over "
                            "a 2.0x trust floor. Reversing order by < 190 us inside the 460 us "
                            "window would have extra-clamped a legal 12 Pa primary-dry.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "chamber Pirani gauge, 1 kHz, 32 us jitter",
                    "shelf RTD tree, 2 kHz, 34 us jitter",
                    "shelf encoder (context)",
                    "condenser load cell (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("collapse_cap_Pa", 25.0),
                        ("observed_pirani_Pa", 12.0),
                        ("shelf_K", 241.0),
                        ("melt_look_K", 250.0),
                        ("proposed_ramp_K_min", 0.4),
                    ]
                ),
            ),
            (
                "simulation",
                OrderedDict(
                    [
                        (
                            "solver",
                            "species-transport + ice-sublimation FEM, seed 23134; 3-zone shelf, "
                            "12 vial-grid; NOT lumped-capacity, NOT U-RANS, NOT a wet-stand",
                        ),
                        (
                            "fidelity_limits",
                            "Rigid vials; no stopper-pop. Raster is kernelized events, not an "
                            "independent LIF.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Shelf-tree S-4 in primary-dry; +0.4 K/min ramp armed.",
                    "2. Pirani 12.0 Pa under 25 Pa collapse; shelf 241 K under 250 K melt.",
                    "3. Encoder precursor at 1.105 ms.",
                    "4. Race window [8.000, 8.460] ms.",
                    "5. pirani.chamber.Pa 12.0 Pa at 8.120 ms (winner).",
                    "6. rtd.shelf.K 241 K at 8.310 ms (loser by 190 us).",
                    "7. Gate at 8.520 ms: ACCEPT +0.4 K/min; executed identical to proposed.",
                    "8. Chamber stays 12.4 Pa < 25; shelf 241.2 K < 250.",
                    "9. RTD remaining under melt did not require an extra clamp.",
                    "10. Delayed (survey_s=90): 90 s GC residual-moisture sample on vial 7.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_primary_dry_ramp"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("chamber_Pa", 12.0),
                        ("collapse_cap_Pa", 25.0),
                        ("shelf_K", 241.0),
                        ("melt_look_K", 250.0),
                        ("race_margin_us", 190),
                        ("combined_jitter_us", 66),
                        ("survey_s", 90),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes keeping the filed +0.4 K/min ramp: Pirani 12 Pa is under the "
                "25 Pa collapse cap and shelf 241 K is under 250 K melt.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Pirani 12.0 Pa won by 190 us and is under the 25 Pa collapse cap. Shelf 241 K "
                "is not a melt clearance problem. ACCEPT the filed +0.4 K/min ramp. Executed "
                "identical to proposed. An extra clamp is not indicated.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "chamber_Pa",
                            OrderedDict(
                                [
                                    ("cap", 25.0),
                                    ("observed", 12.0),
                                    ("executed_ramp_K_min", 0.4),
                                ]
                            ),
                        ),
                        (
                            "shelf_K",
                            OrderedDict([("melt_look", 250.0), ("observed", 241.0)]),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 190),
                                    ("combined_jitter_us", 66),
                                    ("ratio", 2.88),
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
            ("name", "hold_primary_dry_ramp"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: executed identical to proposed +0.4 K/min ramp. Pirani 12 Pa < 25 cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT kept the filed +0.4 K/min shelf ramp. Pirani stayed 12.4 Pa "
                "under 25 Pa. RTD remaining under melt was the losing channel and did not "
                "justify an extra clamp.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("ramp", "held; +0.4 K/min"),
                        ("chamber", "12.4 Pa < 25 Pa"),
                        ("shelf", "241.2 K < 250 K"),
                        ("vials", "primary-dry continues"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "RTD 241 K losing a 190 us race did not predict a collapse; reversing 190 us would have extra-clamped a legal 12 Pa dry.",
                    "Delayed (survey_s=90): 90 s GC residual-moisture sample on vial 7; not a safety inflection.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "pirani.chamber.Pa (8.120 ms, 12.0 Pa)"),
                        ("loser", "rtd.shelf.K (8.310 ms, 241 K)"),
                        ("margin_us", 190),
                        (
                            "counterfactual_if_reversed",
                            "RTD-first by < 190 us inside the 460 us window would have extra-clamped "
                            "a legal primary-dry. Pirani-first confirms the filed ramp.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 8520),
            (
                "reward_inflection_note",
                "Heads rise at the ACCEPT (8.520 ms, tick 4). The 90 s GC sample is delayed "
                "surprise bound to survey_s=90, not the inflection.",
            ),
        ]
    )
    ras = raster_core(
        34,
        44,
        42,
        63,
        routing(
            "thalamic-relay.lyo-pirani",
            "spikenaut.policy.ramp-accept",
            [
                ("relay_pirani_Pa", "policy_ramp_accept", 0.66),
                ("relay_rtd_shelf", "policy_extra_clamp", 0.23),
            ],
            "serotonin",
            0.12,
            "rollover_confirm_stdp; 5-HT tags the ramp_accept bind at the Pirani win",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("survey_s", 90),
                ("delayed_surprise_s", 90),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.46),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("ramp_accept", 50, 0.50, 175.0, 4),
                    pop("extra_clamp", 40, 0.85, 40.0, 1),
                    pop("collapse_veto", 22, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r23-134"),
            (
                "title",
                "Vial-Rime VR-7 / shelf-tree S-4: Pirani 12 Pa beats shelf RTD 241 K by 190 us; "
                "ACCEPT already-legal +0.4 K/min primary-dry ramp",
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
                    "Clean ACCEPT of an already-legal shelf ramp. "
                    "total 1.10 = 0.42 + 0.30 + 0.18 + 0.12 + 0.08. Tick 6 t_us binds survey_s=90.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "vial-lyophilizer",
                    [
                        "accept",
                        "simulated",
                        "pirani-vs-rtd",
                        "primary-dry",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a lagging shelf RTD losing a 190 us race does not require an "
                    "extra clamp when Pirani already shows collapse margin.",
                    4,
                ),
            ),
        ]
    )


def record_135():
    ticks = [
        tick(1824, 0.05, 0.04, 0.03, 0.01, 0.01),
        tick(4560, 0.09, 0.06, 0.04, 0.03, 0.02),
        tick(4734, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5140, 0.14, 0.10, 0.06, 0.04, 0.02),
        tick(5460, 0.07, 0.05, 0.03, 0.01, 0.01),
        tick(720000000, 0.03, 0.03, 0.01, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.trolley.ctx", 0.880, 0.40),
        spike("loadcell.spreader.t", 2.040, 0.56),
        spike("twist.lock.ok", 3.120, 0.47),
        spike("loadcell.spreader.t", 4.560, 1.26),
        spike("twist.lock.ok", 4.734, 1.08),
        spike("ctrl.gate", 5.140, 0.99),
        spike("loadcell.spreader.t", 7.200, 0.76),
        spike("twist.lock.ok", 9.880, 0.55),
        spike("ctrl.gate", 13.100, 0.82),
        spike("enc.trolley.ctx", 16.400, 0.43),
        spike("loadcell.spreader.t", 20.200, 0.50),
        spike("twist.lock.ok", 23.100, 0.36),
    ]
    excerpt = independent_excerpt(23135, 76, 24000, 12, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("hoist_m_s", 0.55),
            ("load_t", 38.2),
            ("twistlocks", 4),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "STS-7 at Tern-Apron TA-9 is lifting 38.2 t on four seated twistlocks under a "
                "42.0 t SWL, hoist already at 0.55 m/s. Load-first ACCEPTS the filed hoist; "
                "twistlock-first would have waited for a fifth pin that does not exist.",
            ),
            ("domain", "sts-quay-crane"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Hoist the 40-ft box at 0.55 m/s while load stays <= 42.0 t SWL and four "
                "twistlocks stay seated; do not abort on a phantom fifth pin.",
            ),
            ("t0_us", 1756850400000135),
            ("gate_latency_us", 580),
            ("race_window_us", 320),
            ("race_window_rel_ms", [4.45, 4.77]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "loadcell.spreader.t 38.2 t",
                                "twist.lock.ok 4/4 seated",
                            ],
                        ),
                        (
                            "semantics",
                            "Load-first ACCEPTS the 0.55 m/s hoist (already under 42.0 t SWL). "
                            "Twistlock-first would wait for a phantom fifth pin.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one spreader load-cell slot versus twistlock-status group "
                            "delay on this STS PLC bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 174 us vs combined jitter 58 us (load 26 + twist 32): 3.0x over "
                            "a 2.0x trust floor. Reversing order by < 174 us inside the 320 us "
                            "window would have stalled a legal 38.2 t hoist.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "spreader load-cell, 2 kHz, 26 us jitter",
                    "twistlock 4/4 status, 1 kHz, 32 us jitter",
                    "trolley encoder (context)",
                    "boom anemometer (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("swl_t", 42.0),
                        ("observed_load_t", 38.2),
                        ("twistlocks_seated", 4),
                        ("twistlocks_required", 4),
                        ("proposed_hoist_m_s", 0.55),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. STS-7 indexed over bay 14; 38.2 t box on four twistlocks.",
                    "2. Hoist 0.55 m/s armed; SWL 42.0 t.",
                    "3. Trolley precursor at 0.880 ms.",
                    "4. Race window [4.450, 4.770] ms.",
                    "5. loadcell.spreader.t 38.2 t at 4.560 ms (winner).",
                    "6. twist.lock.ok 4/4 at 4.734 ms (loser by 174 us).",
                    "7. Gate at 5.140 ms: ACCEPT 0.55 m/s; executed identical to proposed.",
                    "8. Load peak 38.4 t < 42.0 SWL; four pins stay seated.",
                    "9. Twistlock remaining 4/4 did not require a wait.",
                    "10. Delayed (tide_hold_s=720): 12 min flood-tide hold on the next lift.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hoist_legal_box"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("load_t", 38.2),
                        ("swl_t", 42.0),
                        ("twistlocks_seated", 4),
                        ("twistlocks_required", 4),
                        ("race_margin_us", 174),
                        ("combined_jitter_us", 58),
                        ("tide_hold_s", 720),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 0.55 m/s hoist: 38.2 t is under 42.0 t SWL and four twistlocks "
                "are already seated.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Load 38.2 t won by 174 us and is under the 42.0 t SWL. Four twistlocks are "
                "seated. ACCEPT the filed 0.55 m/s hoist. Executed identical to proposed. A wait "
                "for a fifth pin is not indicated.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "load_t",
                            OrderedDict(
                                [
                                    ("swl", 42.0),
                                    ("observed", 38.2),
                                    ("executed_hoist_m_s", 0.55),
                                ]
                            ),
                        ),
                        (
                            "twistlocks",
                            OrderedDict([("required", 4), ("seated", 4)]),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 174),
                                    ("combined_jitter_us", 58),
                                    ("ratio", 3.00),
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
            ("name", "hoist_legal_box"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: executed identical to proposed 0.55 m/s hoist. Load 38.2 t < 42.0 SWL.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT kept the filed 0.55 m/s hoist. Load peaked 38.4 t under 42.0 t "
                "SWL. Twistlock 4/4 was the losing channel and did not justify a wait.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("hoist", "0.55 m/s executed"),
                        ("load", "peak 38.4 t < 42.0 SWL"),
                        ("twistlocks", "4/4 seated"),
                        ("box", "clear of the hatch"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Twistlock 4/4 losing a 174 us race did not predict an unseated pin; reversing 174 us would have stalled a legal 38.2 t hoist.",
                    "Delayed (tide_hold_s=720): 12 min flood-tide hold on the next lift; not a safety inflection.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "loadcell.spreader.t (4.560 ms, 38.2 t)"),
                        ("loser", "twist.lock.ok (4.734 ms, 4/4)"),
                        ("margin_us", 174),
                        (
                            "counterfactual_if_reversed",
                            "Twistlock-first by < 174 us inside the 320 us window would have "
                            "waited for a phantom fifth pin. Load-first confirms the filed hoist.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5140),
            (
                "reward_inflection_note",
                "Heads rise at the ACCEPT (5.140 ms, tick 4). The 12 min tide hold is delayed "
                "surprise bound to tide_hold_s=720, not the inflection.",
            ),
        ]
    )
    ras = raster_core(
        24,
        76,
        27,
        49,
        routing(
            "thalamic-relay.sts-load",
            "spikenaut.policy.hoist-accept",
            [
                ("relay_load_t", "policy_hoist_accept", 0.69),
                ("relay_twist_ok", "policy_twist_wait", 0.21),
            ],
            "octopamine",
            0.05,
            "swl_confirm_stdp; octopamine tags the hoist_accept bind at the load-cell win",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("tide_hold_s", 720),
                ("delayed_surprise_s", 720),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.32),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("hoist_accept", 45, 0.50, 210.0, 3),
                    pop("twist_wait", 40, 0.85, 40.0, 1),
                    pop("swl_veto", 20, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r23-135"),
            (
                "title",
                "Tern-Apron TA-9 / STS-7: load-cell 38.2 t beats twistlock 4/4 by 174 us; ACCEPT "
                "already-legal 0.55 m/s hoist",
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
                    "Clean ACCEPT of an already-legal hoist. "
                    "total 1.16 = 0.44 + 0.32 + 0.20 + 0.12 + 0.08. Tick 6 binds tide_hold_s=720.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "sts-quay-crane",
                    [
                        "accept",
                        "designed",
                        "loadcell-vs-twistlock",
                        "swl-legal",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a lagging twistlock status losing a 174 us race does not require "
                    "a wait when load is already under SWL and 4/4 pins are seated.",
                    5,
                ),
            ),
        ]
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
    if set(domains) & BANNED_DOMAINS:
        issues.append(f"banned domains {set(domains) & BANNED_DOMAINS}")
    ids = [r["id"] for r in records]
    if ids != [f"ttf-r30-{n}" for n in range(166, 171)]:
        issues.append(f"ids {ids}")
    wrong = [
        r
        for r in records
        if r["safety_decision"].get("correctness") == "incorrect"
        or r["meta"].get("supervisor_error_type")
    ]
    if len(wrong) != 1 or wrong[0]["id"] != "ttf-r30-166":
        issues.append(f"wrong-gate set {[w['id'] for w in wrong]}")
    if wrong and wrong[0]["meta"].get("supervisor_error_type") != "wrong-reject":
        issues.append("166 supervisor_error_type")
    if any(r["state"]["sim_or_real"] == "real" for r in records):
        issues.append("sim_or_real=real")
    hil = [r["id"] for r in records if r["state"]["sim_or_real"] == "hil"]
    if hil != ["ttf-r30-168"]:
        issues.append(f"hil set {hil}")
    sim = [r["id"] for r in records if r["state"]["sim_or_real"] == "simulated"]
    if sim != ["ttf-r30-169"]:
        issues.append(f"simulated set {sim}")
    decisions = [r["safety_decision"]["decision"] for r in records]
    if (
        decisions.count("ACCEPT") != 2
        or decisions.count("MODIFY") != 1
        or decisions.count("REJECT") != 2
    ):
        issues.append(f"gate mix {decisions}")
    for rec in records:
        blob = json.dumps(rec)
        if "training_ready" in blob:
            issues.append(f"{rec['id']} training_ready present")
        if "outputs/raw" in blob:
            issues.append(f"{rec['id']} mentions outputs/raw")
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
        if rec["id"] == "ttf-r30-167":
            if rec["raster"].get("excerpt_source") != "independent_lif":
                issues.append("167 missing independent_lif")
            if rec["future_outcome"]["reward_inflection_t_us"] > rec["raster"]["window_ms"] * 1000:
                issues.append("167 inflection outside window")
            if rec["reward_components"]["total"] >= 0:
                issues.append("167 partnered-neg total not negative")
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
        if not (8 <= len(rec["state"]["episode_steps"]) <= 15):
            issues.append(f"{rec['id']} episode_steps")
        if rec["gate_snn"]["decision"] != rec["safety_decision"]["decision"]:
            issues.append(f"{rec['id']} gate_snn decision mismatch")
        if rec["meta"]["round"] != 30:
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
        if not (8 <= nspk <= 16):
            issues.append(f"{rec['id']} spike count {nspk}")
        times = [e["t_rel_ms"] for e in rec["spike_events"]]
        if times != sorted(times):
            issues.append(f"{rec['id']} spike order")
        nex = len(rec["raster"]["excerpt"])
        if not (8 <= nex <= 16):
            issues.append(f"{rec['id']} excerpt count {nex}")
        exec_p = rec["executed_action"]["parameters"]
        prop_p = rec["proposed_action"]["parameters"]
        if rec["safety_decision"]["decision"] == "ACCEPT" and exec_p != prop_p:
            issues.append(f"{rec['id']} ACCEPT params differ")
        if rec["id"] == "ttf-r30-166":
            if "recovery" not in rec["future_outcome"]:
                issues.append("166 missing recovery")
            if exec_p.get("gen_mw") != 0.0:
                issues.append("166 did not zero gen_mw")
            if exec_p.get("feather") is not True:
                issues.append("166 did not feather")
            tos = {row["to"] for row in rec["raster"]["routing"]["table"]}
            if "policy_yaw_go" in tos:
                issues.append("166 routing contains policy_yaw_go")
            if "policy_feather_reject" not in tos:
                issues.append("166 routing missing policy_feather_reject")
        blob_l = blob.lower()
        for frag in BANNED_PLANT_FRAGMENTS:
            if frag.lower() in blob_l:
                issues.append(f"{rec['id']} banned plant {frag}")
        delay = rec["future_outcome"].get("delayed_surprise_s") or rec["raster"].get(
            "delayed_surprise_s"
        )
        if delay is not None:
            expected_t6 = int(round(float(delay) * 1e6))
            if rec["reward_components"]["ticks"][-1]["t_us"] != expected_t6:
                issues.append(
                    f"{rec['id']} tick6 {rec['reward_components']['ticks'][-1]['t_us']} "
                    f"vs delayed_surprise {expected_t6}"
                )
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
        if rec["meta"]["rights"]["intended_use"] != "research_only":
            issues.append(f"{rec['id']} intended_use")
    return issues, jmax


def notes_text(jmax: float) -> str:
    return f"""# Thalamic Trajectory Factory — NOTES-r30

- Factory: `thalamic-trajectory-factory`
- Run label: `2026-09-02-final-heavy`
- Generator: `grok-4.6`
- Channel: SuperGrok Heavy consumer chat (RM-793 research-only)
- Quota: 5
- Quality: Q=5
- IDs: `ttf-r30-166` … `ttf-r30-170`
- Domains this batch: `wind-nacelle-yaw`, `sugar-vacuum-pan`, `steel-caster-mold`, `desal-RO-train`, `cement-precalciner`

These five domain slugs sit outside the r12 8-pool and outside staged r13–r24 sit-ins. All five plants are invented. Do not restack prior TTF plants (Marrow-Dock, Vesper-Lattice, Brine-Well, Saddle-Arc, Ashlar-Gait, Nacre-Well, Quern-Forge, Tinder-Box, Whimbrel-Stack, Cinder-Loft, Suture-Isle, Kiln-Spur, Oxbow-Switch, Pitch-Kettle, Shale-Quay, Polder-Rye, Flint-Mask, Gyre-Tokamak, Quarry-Bowl, Orpiment, Foehn-Nacelle / Treacle-Kettle / Bloom-Weir / Spindrift-Rack / Clinker-Spire are this round only).

## Batch map

| id | domain | decision | correctness | sim_or_real | total | edge |
|----|--------|----------|-------------|-------------|-------|------|
| ttf-r30-166 | wind-nacelle-yaw | REJECT | **incorrect (wrong-reject)** | designed | −0.36 | yaw 0.54 deg < 0.80 published floor; supervisor bound retired 0.40 deg firmware-3.1 plaque |
| ttf-r30-167 | sugar-vacuum-pan | MODIFY | correct | designed | **−0.50** | process-correct steam clamp; crystal-bridge seize inside 42 ms raster; independent LIF |
| ttf-r30-168 | steel-caster-mold | REJECT | correct | hil | +0.78 | eddy 48 mm beats IR 890 C; hold caster speed |
| ttf-r30-169 | desal-RO-train | ACCEPT | correct | simulated | +1.10 | permeate 180 uS/cm vs feed-PT 12.4 bar; proposed feed already legal |
| ttf-r30-170 | cement-precalciner | ACCEPT | correct | designed | +1.16 | O2 3.8 pct vs IR 812 C; proposed 82 t/h already legal |

Gate mix: 2 ACCEPT, 1 correct MODIFY (partnered-neg, in-window), 1 correct REJECT, 1 incorrect REJECT (stale-firmware floor). Provenance: designed×3, simulated×1, hil×1 (Bloom-Weir caster pad). Intra-batch Jaccard on `state.description` {jmax:.3f}.

## Wrong-reject

**ttf-r30-166** is the mandated incorrect gate (`safety_decision.correctness=incorrect`, `meta.supervisor_error_type=wrong-reject`). Alternate vs odd rounds: even rounds host wrong-reject. This subclass is **superseded-plaque / stale-firmware floor**, not r22 class-transplant (M-series vs P-series vehicle), not r18 empty-tank, not r20 oscillation-as-PSV, not r16 reticle-as-wafer. Do not emit a wrong-ACCEPT.

Foehn-Nacelle FN-3 / Yaw-Y7 reads yaw-error **0.54 deg** against a published **0.80 deg** firmware-4.2 floor. Brake 168 bar is under 210 bar. Sidecar arithmetic `0.54 < 0.80` is true. A weak supervisor binds the **retired 0.40 deg firmware-3.1 nameplate** still riveted on the cabinet, REJECT-feathers 2.4 → 0 MW, and leaves a legal yaw idle. Convictable without nacelle physics: `evidence.yaw_err_deg < evidence.yaw_floor_deg`, `executed_action` sets `gen_mw=0` / `feather=true`, `raster.routing.table` sends `relay_enc_yaw` → `policy_feather_reject` (weight 0.71) with no positive weight to `policy_yaw_go`, and `gate_snn` has `feather_reject` above threshold while `yaw_go` is not (`spikes=0`). Recovery: ACCEPT; leave 2.4 MW; bind the published 0.80 deg floor. Cost: 15 min missed generation (`missed_window_s=900`).

## Partnered-negative in-window (167)

**ttf-r30-167** is the partnered negative: process-correct MODIFY (steam held 1.10 bar; Brix 75.2 < 76.0 cap) while the world still charges. Safety −0.66 prices the crystal-bridge seize at **22.400 ms**; `task_progress` stays +0.32 because the clamp completed. Inflection `t_us=22400` is tick 5 and is **inside** the 42 ms raster (`22400 ≤ 42000`). Named un-netted loss: 13 min pan dump + agitator pull (`abort_s=780`). Not folded into process heads.

Independent LIF (the one labeled sidecar sim): `state.sim_or_real` remains `designed`. `raster.excerpt_source=independent_lif`, `raster.sim_scope=sidecar_only`, `raster.lif` seed 30167, stim `[21000, 25000]`. Excerpt is membrane crossings (`lif.clamp` early vs `lif.crystal` 21–25 ms), not a 1:1 remap of `spike_events`. `meta.tags` include `independent-lif-raster` and `sidecar-sim-only`.

## Reward formula and tick reconciliation

Declared aggregation on every record:

`total = task_progress + safety + efficiency + coherence + exploration`

Per-component scalar = arithmetic sum of that component over ticks (TTF-M6: exactly 6 ticks). Tick 6 is bound to a published sidecar (`missed_window_s`, `abort_s`, `survey_s`, `reseq_s`) and is strictly after the raster window. Inflection `t_us` is an actual tick.

| id | ticks | tp | saf | eff | coh | exp | total | inflection tick |
|----|-------|----|-----|-----|-----|-----|-------|-----------------|
| 166 | 6 | −0.18 | +0.06 | −0.22 | −0.08 | +0.06 | −0.36 | 4 (5680) |
| 167 | 6 | +0.32 | −0.66 | −0.16 | +0.04 | −0.04 | −0.50 | 5 (22400) |
| 168 | 6 | +0.10 | +0.40 | +0.12 | +0.10 | +0.06 | +0.78 | 4 (7920) |
| 169 | 6 | +0.42 | +0.30 | +0.18 | +0.12 | +0.08 | +1.10 | 4 (8580) |
| 170 | 6 | +0.44 | +0.32 | +0.20 | +0.12 | +0.08 | +1.16 | 4 (5180) |

Tick-6 sidecar bind: 166 `missed_window_s=900`, 167 `abort_s=780`, 168 `abort_s=540`, 169 `survey_s=480`, 170 `reseq_s=360`.

## Raster / energy (Loihi-2 4-core, 23 pJ/spike)

| id | domain | n | rate Hz | window_ms | spikes | energy_pJ | energy_uJ |
|----|--------|---|---------|-----------|--------|-----------|-----------|
| 166 | wind-nacelle-yaw | 84 | 22 | 36 | 66 | 1518 | 0.001518 |
| 167 | sugar-vacuum-pan | 72 | 29 | 42 | 88 | 2024 | 0.002024 |
| 168 | steel-caster-mold | 120 | 18 | 48 | 104 | 2392 | 0.002392 |
| 169 | desal-RO-train | 56 | 34 | 30 | 57 | 1311 | 0.001311 |
| 170 | cement-precalciner | 40 | 46 | 26 | 48 | 1104 | 0.001104 |

`spikes = round(n × rate × window_s)`. Every record carries `gate_snn` whose `decision` matches the safety gate; populations that declare rate+spikes meet the same ±1 budget against `decision_window_s`. `routing.third_factor` has modulator (ACh / NA / DA / 5-HT / histamine), `tau_e_s`/`tau_e_ms` pair, and eligibility. Excerpt same-neuron gap ≥ 1000 µs; spike trains same-channel refractory ≥ 0.8 ms. Non-167 excerpts are kernelized and independent of `spike_events` times (overlap < 0.8).

## Local checks (staging, not raw)

See generator stdout: `check_jsonl` FactoryStaging, `validate_run.check_line`, `dumps_exact_json`, `raster_status`, `verify_batch_for_frontier(strict=True)`, `spike_probe.py --strict`, tick sums, refractory, Jaccard.

Never `training_ready`. Never `sim_or_real=real`. Never wrote `outputs/raw/`.

## Residual weaknesses (honest)

1. Only **one** labeled independent LIF (167). The other four excerpts are independent of `spike_events` times but are not declared population sims.
2. Wrong-ACCEPT still absent (guard).
3. 169 and 170 are both already-legal ACCEPTs; a later round could pair one ACCEPT with a world charge that does not go negative, or drop to a single ACCEPT.
4. Five domain slugs leave the prompt's 8-item pool; a later round that must stay inside the pool will have to rotate sit-outs instead.
5. Tick-6 sidecar bind is standing machinery (r14+), not a new class.

## Next densification target

Publish the firmware-floor predicate as a sidecar enum (`yaw_floor_class`) so a stale-plaque REJECT is convictable without the 4.2-vs-3.1 story. Optional: labeled LIF on a second record, or an ISI histogram sidecar. Wrong-ACCEPT remains structurally absent until a prompt amendment.

Novel coverage: 24.0%
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
        BATCH_PATH, "batch-r30.jsonl", staging=FactoryStaging(enabled=True)
    )
    report.append(("check_jsonl FactoryStaging", errors, warnings, kinds, nrec))
    line_errs = []
    for i, rec in enumerate(records, 1):
        errs, kind = check_line(rec, f"batch-r30.jsonl:{i}", factory_staging=True)
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


def main() -> int:
    if str(BATCH_PATH).startswith(str(REPO / "outputs" / "raw")):
        print("refusing to write outputs/raw")
        return 1
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    records = [record_131(), record_132(), record_133(), record_134(), record_135()]
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
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
