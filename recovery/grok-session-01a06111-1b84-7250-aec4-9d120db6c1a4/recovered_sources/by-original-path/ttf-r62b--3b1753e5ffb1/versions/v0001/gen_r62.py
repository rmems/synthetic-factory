#!/usr/bin/env python3
"""Emit TTF r62 JSONL (ttf-r62-821..825) into /tmp/ttf-r62b/. Never writes outputs/raw/."""

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

OUT_DIR = Path("/tmp/ttf-r62b")
BATCH_PATH = OUT_DIR / "batch-r62.jsonl"
NOTES_PATH = OUT_DIR / "NOTES-r62.md"
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
        ("generated_at", "2026-09-02T19:20:00Z"),
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
    "bismuth-telluride-zone-melt",
    "praseodymium-fluoride-cell",
    "silicon-carbide-pvt-furnace",
    "yttrium-aluminum-garnet-puller",
    "diamond-hpht-press",
)
THIS_PLANTS = (
    "Bismite-Holt",
    "Praseo-Ness",
    "Carbopvt-Keld",
    "Yag-Fen",
    "Adamant-Beck",
)
IDS = [f"ttf-r62-{n}" for n in range(821, 826)]
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
NOVEL_COVERAGE_LINE = "Novel coverage: 16.8%"


def harvest_occupancy() -> tuple[set[str], set[str]]:
    domains: set[str] = set(PROMPT_POOL)
    plants: set[str] = set()
    skip_parents = {"ttf-r62b"}
    for path in sorted(Path("/tmp").glob("ttf-r*/batch-r*.jsonl")):
        if path.parent.name in skip_parents:
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
        if path.parent.name in skip_parents:
            continue
        try:
            txt = path.read_text(encoding="utf-8")
        except OSError:
            continue
        plants.update(PLANT_RE.findall(txt))
        match = re.search(r"Domains this batch:\s*(.*)", txt)
        if match:
            domains.update(re.findall(r"`([^`]+)`", match.group(1)))
    extra_py = []
    for glob_name in (
        "ttf-r*/gen_r*.py",
        "ttf-r*/_records.py",
        "ttf-r*/_head.py",
        "ttf-r*/_tail.py",
        "ttf-r*/records_r*.py",
        "ttf-r*/build_r*.py",
    ):
        extra_py.extend(Path("/tmp").glob(glob_name))
    for path in extra_py:
        if path.parent.name in skip_parents:
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
    occ = Path("/tmp/ttf-occupied-domains.txt")
    if occ.is_file():
        domains.update(ln.strip() for ln in occ.read_text().splitlines() if ln.strip())
    for f in Path("/tmp").glob("ttf-r*-occ-domains*.txt"):
        domains.update(ln.strip() for ln in f.read_text().splitlines() if ln.strip())
    factory = Path(
        "/home/raulmc/rmems/synthetic-factory/outputs/raw/"
        "2026-09-02-final-heavy/thalamic-trajectory-factory"
    )
    if factory.is_dir():
        for path in factory.glob("*.jsonl"):
            for line in path.read_text().splitlines():
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


def isi_histogram(events, bin_ms=0.8):
    last = {}
    isis = []
    for ev in events:
        ch, t = ev["channel"], ev["t_rel_ms"]
        if ch in last:
            gap = t - last[ch]
            if gap + 1e-12 < 0.8:
                raise ValueError(f"ISI {ch} {gap}")
            isis.append(gap)
        last[ch] = t
    if not isis:
        raise ValueError("no ISIs")
    max_bin = int(max(isis) // bin_ms)
    counts = [0] * (max_bin + 1)
    for gap in isis:
        counts[int(gap // bin_ms)] += 1
    return OrderedDict(
        [
            ("bin_ms", bin_ms),
            ("unit", "ms"),
            ("n_isi", len(isis)),
            ("min_isi_ms", round(min(isis), 4)),
            ("counts", counts),
            ("note", "same-channel ISIs from spike_events; refractory floor 0.8 ms"),
        ]
    )


def lif_821_excerpt():
    n = 76
    dt_us = 100
    tau_m_ms = 19.0
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.91
    i_stim_peak = 2.48
    stim = (22000, 25000)
    seed = 62821
    window_us = 42000
    i_clamp_extra = 0.62
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
    take(burst, 9, label_times=(22400, 23200, 24200))
    clamp = [(t, nid) for t, nid in picked if t < 22000][:7]
    crack = [(t, nid) for t, nid in picked if t >= 22000][:9]
    picked = sorted(clamp + crack, key=lambda item: (item[0], item[1]))
    if len(picked) < 8:
        raise ValueError(
            f"LIF excerpt too short {len(picked)} (early={len(early)} burst={len(burst)})"
        )
    channels = ["lif.clamp" if t < 22000 else "lif.crack" for t, _ in picked]
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
            ("stim_t_us", [22000, 25000]),
            ("i_clamp_extra", 0.62),
            ("clamp_n", 14),
            ("seed", 62821),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-13 carry +0.62 travel-clamp bias; stim 22-25 ms is the quartz-ampoule crack.",
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
            ("round", 62),
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


def record_821():
    excerpt, extra = lif_821_excerpt()
    ticks = [
        tick(2480, 0.04, -0.02, -0.02, 0.01, 0.00),
        tick(6180, 0.08, -0.04, -0.02, 0.01, -0.01),
        tick(6368, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(6900, 0.08, -0.05, -0.03, 0.02, -0.01),
        tick(22400, 0.04, -0.45, -0.03, -0.01, -0.01),
        tick(780000000, 0.02, -0.05, -0.02, 0.01, -0.01),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Horizontal zone Z-2 at Bismite-Holt BH-4 is already indexing a Bi2Te3 ampoule "
                "at 18.0 mm/h while the travelling heater sits at 628 C against a 580 C "
                "freeze-front cap. Heater-first cuts travel 18.0 -> 9.0 mm/h; encoder-first "
                "would keep 18.0 mm/h because the 1.6 mm/h look is still under a 4.0 mm/h "
                "travel look. A quartz-ampoule crack already seated at the seed does not "
                "appear on heater T or travel encoder until the AE dump.",
            ),
            ("domain", "bismuth-telluride-zone-melt"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep zone Z-2 heater <= 580 C and finish the Bi2Te3 pass without dumping "
                "the ampoule onto the seed chuck.",
            ),
            ("t0_us", 1756850400000821),
            ("gate_latency_us", 720),
            ("race_window_us", 400),
            ("race_window_rel_ms", [6.0, 6.4]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "tc.zone.C 628 over 580 freeze-front cap",
                                "enc.travel.mm 18.0 with look 1.6 under 4.0 mm/h",
                            ],
                        ),
                        (
                            "semantics",
                            "Heater-first latches travel clamp 18.0 -> 9.0 mm/h; encoder-first "
                            "keeps 18.0 mm/h on a still-under-look model.",
                        ),
                        (
                            "window_derivation",
                            "400 us = one travelling-heater TC slot versus the travel-encoder "
                            "publisher on this zone-melt skid bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 188 us vs combined jitter 64 us (TC 30 + ENC 34): 2.9x over a "
                            "2.0x trust floor. Reversing order by < 188 us inside the 400 us "
                            "window would have kept 18.0 mm/h; predicted next-sample 636 C > 580 "
                            "freeze-front cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "travelling-heater thermocouple, 2 kHz, 30 us jitter",
                    "ampoule-travel encoder, 1 kHz, 34 us jitter",
                    "quartz-ampoule AE puck (context)",
                    "seed-chuck IR (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("heater_cap_C", 580.0),
                        ("observed_heater_C", 628.0),
                        ("travel_mm_h", 18.0),
                        ("travel_look_mm_h", 1.6),
                        ("travel_look_cap_mm_h", 4.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Zone Z-2 in Bi2Te3 pass; travel 18.0 mm/h; heater 628 C.",
                    "2. Encoder look 1.6 mm/h under 4.0; ampoule crack armed.",
                    "3. Travel-encoder precursor at 1.160 ms.",
                    "4. Race window [6.000, 6.400] ms.",
                    "5. tc.zone.C 628 C at 6.180 ms (winner).",
                    "6. enc.travel.mm 18.0 at 6.368 ms (loser by 188 us).",
                    "7. Gate at 6.900 ms: MODIFY clamp 18.0 -> 9.0 mm/h.",
                    "8. After clamp heater 564 C <= 580; look still 1.6 mm/h.",
                    "9. At 22.400 ms a quartz-ampoule crack dumps seed liquor onto the chuck.",
                    "10. 13 min ampoule re-seal (abort_s=780); named un-netted loss.",
                ],
            ),
        ]
    )
    spikes = [
        spike("enc.travel.ctx", 1.16, 0.41),
        spike("tc.zone.C", 2.48, 0.58),
        spike("enc.travel.mm", 3.91, 0.50),
        spike("tc.zone.C", 6.18, 1.31),
        spike("enc.travel.mm", 6.368, 1.12),
        spike("ctrl.gate", 6.90, 0.97),
        spike("tc.zone.C", 8.15, 0.82),
        spike("enc.travel.mm", 10.6, 0.64),
        spike("ctrl.gate", 14.2, 0.86),
        spike("ae.ampoule.crack", 22.4, 1.48),
        spike("ae.ampoule.crack", 24.05, 0.93),
        spike("enc.travel.ctx", 29.7, 0.40),
        spike("tc.zone.C", 36.1, 0.55),
    ]
    proposed = OrderedDict(
        [
            ("name", "cruise_zone_travel"),
            (
                "parameters",
                OrderedDict(
                    [("travel_mm_h", 18.0), ("heater_C", 628.0), ("look_mm_h", 1.6)]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("heater_C", 628.0),
                        ("heater_cap_C", 580.0),
                        ("predicted_unclamped_next_C", 636.0),
                        ("travel_mm_h", 18.0),
                        ("look_mm_h", 1.6),
                        ("look_cap_mm_h", 4.0),
                        ("race_margin_us", 188),
                        ("combined_jitter_us", 64),
                        ("abort_s", 780),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 18.0 mm/h because encoder look 1.6 mm/h is under 4.0, "
                "treating the 628 C heater as a still-wet lance rather than a freeze-front miss.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Heater 628 C won by 188 us, so the zone is over the 580 C freeze-front cap, "
                "not still a travel-look story. Holding 18.0 mm/h predicts next-sample 636 C > 580. "
                "MODIFY: travel 18.0 -> 9.0 mm/h. Observed after clamp 564 C <= 580. A full REJECT "
                "is not indicated: a clean Bi2Te3 pass accepts 9.0 mm/h.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "heater_C",
                            OrderedDict(
                                [
                                    ("cap", 580.0),
                                    ("observed", 628.0),
                                    ("predicted_unclamped_next", 636.0),
                                    ("clamped_travel_mm_h", 9.0),
                                    ("observed_after_clamp", 564.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [("margin_us", 188), ("combined_jitter_us", 64), ("ratio", 2.94)]
                            ),
                        ),
                    ]
                ),
            ),
        ]
    )
    executed = OrderedDict(
        [
            ("name", "clamped_zone_travel"),
            (
                "parameters",
                OrderedDict(
                    [("travel_mm_h", 9.0), ("heater_C", 564.0), ("look_mm_h", 1.6)]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: travel 18.0 -> 9.0 mm/h. Process-correct vs the 580 C freeze-front cap. "
                "Quartz-ampoule crack still dumps at 22.400 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held heater at 564 C. At 22.400 ms a quartz-ampoule "
                "crack already seated at the seed dumped liquor onto the chuck. Clamp reduced "
                "dump energy; it did not prevent the dump. Partnered negative: process heads "
                "stay honest; world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("heater", "clamp executed; peak 564 C <= 580 cap"),
                        ("ampoule", "crack dump at 22.400 ms; seed liquor on chuck"),
                        ("repair", "13 min ampoule re-seal (abort_s=780)"),
                        ("mission", "BH-4 Bi2Te3 pass incomplete this cycle"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither heater T nor travel encoder predicted the seated quartz-ampoule crack; "
                    "ae.ampoule.crack is a new channel at 22.400 ms, 15.500 ms after the gate, still "
                    "inside the 42 ms raster.",
                    "Delayed (abort_s=780): 13 min ampoule re-seal. Named un-netted loss, not folded "
                    "into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "13 min ampoule re-seal after the quartz-ampoule crack. Safety head -0.64 prices "
                "the dump; task_progress stays +0.30 because the clamp completed.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "tc.zone.C (6.180 ms, 628 C)"),
                        ("loser", "enc.travel.mm (6.368 ms, 18.0 mm/h)"),
                        ("margin_us", 188),
                        (
                            "counterfactual_if_reversed",
                            "Encoder-first by < 188 us inside the 400 us window would have kept "
                            "18.0 mm/h; predicted next-sample 636 C would have missed the 580 "
                            "freeze-front cap even without the crack. The MODIFY is still the "
                            "correct process. The dump is a later world charge either way, cheaper "
                            "with the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22400),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.400 ms quartz-ampoule crack (tick t_us=22400), inside "
                "the 42 ms raster. The correct MODIFY at 6.900 ms is in the same excerpt. Do not "
                "put inflection on the abort_s=780 re-seal tick.",
            ),
            ("delayed_surprise_s", 780),
        ]
    )
    ras = raster_core(
        42,
        76,
        24,
        77,
        routing(
            "thalamic-relay.bh-heater",
            "spikenaut.policy.travel-clamp",
            [
                ("relay_heater_C", "policy_travel_clamp", 0.68),
                ("relay_travel_enc", "policy_travel_hold", 0.29),
                ("relay_ae_crack", "policy_travel_clamp", -0.42),
            ],
            "noradrenaline",
            0.04,
            "surprise-gated pre_post_stdp; NA at heater win (6.180 ms) opens a 42 ms "
            "eligibility trace that still covers the 22.400 ms quartz-ampoule crack",
        ),
        excerpt,
        extra=extra,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.4),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop("travel_clamp", 50, 0.5, 200.0, 4),
                    pop("travel_hold", 40, 0.8, 50.0, 1),
                    pop("crack_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r62-821",
        "Bismite-Holt BH-4 / Zone Z-2: heater 628 C beats travel 18.0 mm/h by 188 us; "
        "correct MODIFY still eats an in-window quartz-ampoule crack (partnered negative total -0.48)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Partnered negative. Process-correct MODIFY; world still charges inside the 42 ms raster. "
        "total -0.48 = 0.30 + -0.64 + -0.14 + 0.04 + -0.04. Named ampoule re-seal (abort_s=780) "
        "is not netted into task_progress.",
        ras,
        gate,
        "bismuth-telluride-zone-melt",
        [
            "modify",
            "partnered-negative-total",
            "independent-lif-raster",
            "sidecar-sim-only",
            "in-window-world-charge",
            "designed",
        ],
        "A critic can see the world-charge as a LIF burst inside the raster while process heads "
        "stay honest. Credit assignment is spikes, not prose across a 13 min ampoule re-seal.",
        1,
    )


def record_822():
    events = [
        spike("enc.cycle.ctx", 1.02, 0.42),
        spike("tc.bath.C", 2.18, 0.57),
        spike("ir.hood.C", 3.12, 0.88),
        spike("tc.bath.C", 5.41, 1.29),
        spike("ir.hood.C", 5.594, 1.10),
        spike("ctrl.gate", 5.98, 0.96),
        spike("fv.hold.rect", 6.42, 1.18),
        spike("tc.bath.C", 7.85, 0.80),
        spike("ir.hood.C", 10.18, 0.63),
        spike("ctrl.gate", 13.4, 0.84),
        spike("enc.cycle.ctx", 18.2, 0.41),
        spike("tc.bath.C", 22.0, 0.54),
        spike("fv.hold.rect", 26.2, 0.38),
    ]
    excerpt = independent_excerpt(62822, 96, 28000, 14, spike_avoid_us(events))
    ticks = [
        tick(2180, -0.02, -0.01, -0.03, -0.01, 0.01),
        tick(5410, -0.04, -0.02, -0.04, -0.02, 0.01),
        tick(5594, -0.04, -0.02, -0.04, -0.02, 0.01),
        tick(5980, -0.08, -0.03, -0.08, -0.04, 0.02),
        tick(6420, -0.02, -0.01, -0.03, -0.02, 0.01),
        tick(540000000, -0.02, -0.01, -0.02, -0.01, 0.00),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Molten-salt cell C-1 at Praseo-Ness PN-6 still prints live bath-center "
                "TT-21A 986.0 C against a 1080.0 C freeze-lid trip, with an 7.2 kA load already "
                "filed under the 9.0 kA rectifier ceiling. Bath-first should ACCEPT the legal "
                "load; a weak supervisor binds a leftover Kelvin offset (986.0 + 273.15 = 1259.15 C) "
                "as the live PV and REJECT-holds current to 0.0 kA.",
            ),
            ("domain", "praseodymium-fluoride-cell"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Hold the 7.2 kA load while bath stays <= 1080.0 C and current stays <= 9.0 kA; "
                "do not reject a legal PrF3 cell on a leftover K-as-C offset.",
            ),
            ("t0_us", 1756850400000822),
            ("gate_latency_us", 570),
            ("race_window_us", 360),
            ("race_window_rel_ms", [5.4, 5.76]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "tc.bath.C 986.0 C under 1080 freeze-lid",
                                "ir.hood.C 1180 C smear under 1220 look",
                            ],
                        ),
                        (
                            "semantics",
                            "Bath-first should ACCEPT the already-legal 7.2 kA load. Kelvin-offset-first "
                            "is a false 'bath 1259 C' bind that REJECT-holds the rectifier.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one bath-TC slot versus hood-IR group delay on this PrF3 PLC bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 184 us vs combined jitter 60 us (bath 28 + hood 32). Order is "
                            "correctly bath-first. The error is a leftover Kelvin offset bound as live C, "
                            "not the race order.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "bath-center TT-21A, 4 Hz packet, 28 us jitter on this sample",
                    "hood IR pyrometer, 32 us jitter",
                    "rectifier bus encoder (context)",
                    "cell DP (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("trip_C", 1080.0),
                        ("live_C", 986.0),
                        ("leftover_K_as_C", 1259.15),
                        ("kelvin_offset_K", 273.15),
                        ("current_cap_kA", 9.0),
                        ("proposed_current_kA", 7.2),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Cell C-1 in PrF3 pass; 7.2 kA load armed.",
                    "2. Bath 986.0 C under 1080 freeze-lid; leftover Kelvin tag still mapped.",
                    "3. Hood IR sampled at 3.120 ms.",
                    "4. Race window [5.400, 5.760] ms.",
                    "5. tc.bath.C 986.0 C at 5.410 ms (winner).",
                    "6. ir.hood.C 1180 C at 5.594 ms (loser by 184 us).",
                    "7. Gate at 5.980 ms: WRONG REJECT hold 7.2 -> 0.0 kA on leftover 1259.15 C.",
                    "8. kelvin_as_C=true; current 0.0; bath stays 986.0 < 1080.",
                    "9. Legal pass idles for the rest of the cycle.",
                    "10. Delayed (missed_window_s=540): 9 min missed Pr metal window.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_prf3_current"),
            (
                "parameters",
                OrderedDict(
                    [("current_kA", 7.2), ("bath_C", 986.0), ("hood_C", 1180.0), ("hold", False)]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_C", 986.0),
                        ("trip_C", 1080.0),
                        ("leftover_K_as_C", 1259.15),
                        ("kelvin_offset_K", 273.15),
                        ("current_cap_kA", 9.0),
                        ("proposed_current_kA", 7.2),
                        ("live_under_trip", True),
                        ("kelvin_as_C", False),
                        ("race_margin_us", 184),
                        ("combined_jitter_us", 60),
                        ("missed_window_s", 540),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes keeping 7.2 kA because live bath 986.0 C is under the 1080.0 C "
                "freeze-lid trip and 7.2 kA is under 9.0 kA rectifier. The leftover Kelvin map is "
                "not the live PV.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Live bath 986.0 C is under the 1080.0 C freeze-lid trip, so the 7.2 kA load is "
                "already legal. A weak supervisor binds leftover Kelvin offset 986.0 + 273.15 = "
                "1259.15 C as the live PV and REJECT-holds current 7.2 -> 0.0 kA. The Kelvin map "
                "is a unit leftover, not a freeze-lid miss. The REJECT is plausible to a supervisor "
                "that treats any tag ending in _K as a Celsius process value.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "bath_C",
                            OrderedDict(
                                [
                                    ("trip", 1080.0),
                                    ("live", 986.0),
                                    ("leftover_K_as_C", 1259.15),
                                    ("executed_current_kA", 0.0),
                                ]
                            ),
                        ),
                        (
                            "kelvin_bind",
                            OrderedDict(
                                [
                                    ("kelvin_as_C", True),
                                    ("kelvin_offset_K", 273.15),
                                    ("t_gate_us", 5980),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [("margin_us", 184), ("combined_jitter_us", 60), ("ratio", 3.07)]
                            ),
                        ),
                    ]
                ),
            ),
        ]
    )
    executed = OrderedDict(
        [
            ("name", "hold_prf3_rectifier"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("current_kA", 0.0),
                        ("bath_C", 986.0),
                        ("hood_C", 1180.0),
                        ("hold", True),
                        ("kelvin_as_C", True),
                        ("bound_C", 1259.15),
                    ]
                ),
            ),
            (
                "gate_effect",
                "WRONG REJECT: current 7.2 -> 0.0 kA. Live bath 986.0 remains under 1080.0. "
                "kelvin_as_C=true; bound_C=1259.15.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-reject / leftover-kelvin-offset. Live bath 986.0 stayed under the 1080.0 "
                "trip. The supervisor held the rectifier to 0.0 kA on a leftover K-as-C map. Nine "
                "minutes of missed Pr metal window (missed_window_s=540).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("rectifier", "held; 0.0 kA vs filed 7.2"),
                        ("bath", "986.0 C still under 1080.0"),
                        ("kelvin_tag", "leftover 1259.15 C bound as live PV"),
                        ("mission", "PN-6 working pass idled"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Bath-first winning a 184 us race did not prevent a Kelvin-offset REJECT; "
                    "reversing order would still have been a wrong bind if the supervisor keyed "
                    "on the leftover _K tag.",
                    "Delayed (missed_window_s=540): 9 min missed Pr metal window. Named un-netted loss.",
                ],
            ),
            (
                "recovery",
                "ACCEPT; leave 7.2 kA; bind live bath 986.0 C against the published 1080.0 C trip; "
                "do not add 273.15 to a Celsius RTD and treat the sum as process T.",
            ),
            (
                "cost",
                OrderedDict(
                    [
                        ("actual_live_C", 986.0),
                        ("actual_trip_C", 1080.0),
                        (
                            "wrong_edit_applied",
                            OrderedDict(
                                [
                                    ("current_kA", 0.0),
                                    ("hold", True),
                                    ("kelvin_as_C", True),
                                    ("bound_C", 1259.15),
                                ]
                            ),
                        ),
                        (
                            "cost",
                            "9 min missed Pr metal window (task/efficiency); legal 7.2 kA load was "
                            "idled so a Celsius bath under trip was treated as 1259 C (safety of a "
                            "false Kelvin hold).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "tc.bath.C (5.410 ms, 986.0 C)"),
                        ("loser", "ir.hood.C (5.594 ms, 1180 C)"),
                        ("margin_us", 184),
                        (
                            "counterfactual_if_reversed",
                            "Hood-first by < 184 us would still leave live 986.0 under trip; a "
                            "correct gate binds tc.bath.C to policy.go_accept either way. The wrong "
                            "REJECT spent the live win on a Kelvin-offset hold.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5980),
            (
                "reward_inflection_note",
                "Task, safety, and efficiency drop at the wrong REJECT (5.980 ms, tick 4). The "
                "9 min Pr miss is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 540),
        ]
    )
    ras = raster_core(
        28,
        96,
        32,
        86,
        routing(
            "thalamic-relay.prf3-tc",
            "spikenaut.policy.hold-reject",
            [
                ("relay.tc.kelvin", "policy.hold_reject", 0.74),
                ("relay.tc.liveC", "policy.hold_reject", 0.21),
            ],
            "acetylcholine",
            0.08,
            "prf3_kelvin_stdp; ACh tags the (wrong) hold_reject bind at the bath-TC win",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("missed_window_s", 540),
                ("delayed_surprise_s", 540),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.36),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("hold_reject", 42, 0.45, 280.0, 4),
                    pop("go_accept", 42, 0.9),
                    pop("kelvin_veto", 20, 0.8),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r62-822",
        "WRONG-REJECT at Praseo-Ness PN-6 / Cell C-1: live bath 986.0 C under trip; hold spent on "
        "leftover Kelvin offset 1259.15 C (leftover-kelvin-offset / K-as-C)",
        state,
        events,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Wrong-reject / leftover-kelvin-offset. Sidecar arithmetic live_C 986.0 < 1080.0 is true "
        "and current_kA goes to 0.0; REJECT bound leftover 1259.15 C. total -0.62 = -0.22 + -0.10 "
        "+ -0.24 + -0.12 + 0.06.",
        ras,
        gate,
        "praseodymium-fluoride-cell",
        [
            "reject",
            "wrong-gate",
            "leftover-kelvin-offset",
            "k-as-c",
            "sidecar-convictable",
            "designed",
        ],
        "Teaches a probe that a correct bath-first race can still be a wrong gate when "
        "routing.table[0].to is policy.hold_reject and current_kA is 0.0. Convictable from "
        "live_C vs trip_C plus leftover_K_as_C without PrF3 kinetics.",
        2,
        supervisor_error_type="wrong-reject",
    )


def record_823():
    events = [
        spike("tc.amp.ctx", 1.38, 0.43),
        spike("ae.seed.pps", 2.74, 0.61),
        spike("enc.pull.mm", 4.51, 0.49),
        spike("ae.seed.pps", 7.01, 1.34),
        spike("enc.pull.mm", 7.188, 1.11),
        spike("ctrl.gate", 7.86, 1.02),
        spike("ae.seed.pps", 10.15, 0.78),
        spike("tc.amp.ctx", 14.7, 0.44),
        spike("enc.pull.mm", 19.2, 0.58),
        spike("ctrl.gate", 24.4, 0.81),
        spike("ae.seed.pps", 31.0, 0.53),
        spike("enc.pull.mm", 38.6, 0.46),
        spike("tc.amp.ctx", 43.8, 0.37),
    ]
    excerpt = independent_excerpt(62823, 112, 46000, 15, spike_avoid_us(events))
    ticks = [
        tick(2740, 0.01, 0.04, 0.01, 0.01, 0.01),
        tick(7010, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(7188, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(7860, 0.04, 0.16, 0.04, 0.04, 0.02),
        tick(8180, 0.01, 0.05, 0.02, 0.01, 0.01),
        tick(420000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Physical-vapor-transport furnace X-3 on the Carbopvt-Keld CK-HIL pad is armed "
                "for a 0.18 mm/h SiC seed pull while a seed-crucible AE packet reads 48 pps "
                "against a 12 pps move cap. A pull encoder, lit by the pad lamp, still reads "
                "1.60 mm/h under a 4.00 mm/h travel look. AE-first latches REJECT hold; "
                "encoder-first would commit a 0.18 mm/h pull into a live crack.",
            ),
            ("domain", "silicon-carbide-pvt-furnace"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Do not pull SiC X-3 unless seed AE <= 12 pps; keep slip 0.0 mm/h until the "
                "injected crack recovers.",
            ),
            ("t0_us", 1756850400000823),
            ("gate_latency_us", 850),
            ("race_window_us", 300),
            ("race_window_rel_ms", [6.9, 7.2]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ae.seed.pps 48 pps",
                                "enc.pull.mm 1.60 mm/h under 4.00",
                            ],
                        ),
                        (
                            "semantics",
                            "AE-first latches REJECT hold 0.0 mm/h slip; encoder-first would commit "
                            "a 0.18 mm/h pull on an apparent 1.60 mm/h under-read.",
                        ),
                        (
                            "window_derivation",
                            "300 us = one seed-AE sample versus encoder integration on this SiC PVT HIL bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 178 us vs combined jitter 56 us (AE 24 + ENC 32): 3.2x over a "
                            "2.0x trust floor. Pad injects the encoder lamp 120-160 us before the AE "
                            "(geometric lag, not a sensor fault); the 1.60 mm/h packet is still the "
                            "loser in this 300 us window.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "seed AE puck, 5 kHz burst, 24 us jitter",
                    "crystal-pull encoder, 200 Hz, 32 us jitter",
                    "crucible thermocouple (context)",
                    "HIL lamp-spectrum monitor (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("crack_cap_pps", 12.0),
                        ("observed_crack_pps", 48.0),
                        ("pull_mm_h", 1.60),
                        ("pull_look_mm_h", 4.00),
                        ("proposed_slip_mm_h", 0.18),
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
                            "Carbopvt-Keld CK-HIL SiC PVT mockup with physical seed-pull axis",
                        ),
                        ("injected", "seed AE burst + encoder lamp spectrum"),
                        (
                            "note",
                            "Hardware-in-the-loop SiC PVT. Invented plant; not a live boule shop.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Furnace X-3 on the CK-HIL pad; 0.18 mm/h pull armed.",
                    "2. Encoder lamp injected 120-160 us before AE sees 48 pps.",
                    "3. Crucible-TC precursor at 1.380 ms.",
                    "4. Race window [6.900, 7.200] ms.",
                    "5. ae.seed.pps 48 pps at 7.010 ms (winner).",
                    "6. enc.pull.mm 1.60 mm/h at 7.188 ms (loser by 178 us).",
                    "7. Gate at 7.860 ms: REJECT hold 0.0 mm/h; do not pull 0.18.",
                    "8. Crack remains over 12 pps this cycle; slip cap held.",
                    "9. Seed re-seat queued on the pad.",
                    "10. Delayed (abort_s=420): 7 min seed re-mount and lamp-spectrum retune.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "lower_sic_pull"),
            (
                "parameters",
                OrderedDict(
                    [("slip_mm_h", 0.18), ("hold", False), ("encoder_authoritative", True)]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("crack_pps", 48.0),
                        ("crack_cap_pps", 12.0),
                        ("pull_mm_h", 1.60),
                        ("pull_look_mm_h", 4.00),
                        ("race_margin_us", 178),
                        ("combined_jitter_us", 56),
                        ("abort_s", 420),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes a 0.18 mm/h seed pull because encoder 1.60 mm/h looks under "
                "the 4.00 mm/h travel look, treating AE 48 pps as a noisy bus echo.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Seed AE 48 pps is over the 12 pps pull-move cap. Encoder 1.60 mm/h is a HIL "
                "lamp under-read, not a clearance. REJECT: hold 0.0 mm/h; do not commit a "
                "0.18 mm/h pull.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "crack_pps",
                            OrderedDict(
                                [("cap", 12.0), ("observed", 48.0), ("pull_mm_h", 1.60)]
                            ),
                        ),
                        (
                            "slip_mm_h",
                            OrderedDict([("proposed", 0.18), ("executed", 0.0)]),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [("margin_us", 178), ("combined_jitter_us", 56), ("ratio", 3.18)]
                            ),
                        ),
                    ]
                ),
            ),
        ]
    )
    executed = OrderedDict(
        [
            ("name", "hold_for_crack_drop"),
            (
                "parameters",
                OrderedDict(
                    [("slip_mm_h", 0.0), ("hold", True), ("encoder_authoritative", False)]
                ),
            ),
            (
                "gate_effect",
                "REJECT: hold 0.0 mm/h; 0.18 mm/h pull cancelled. AE 48 > 12 pps cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held Furnace X-3 at 0.0 mm/h slip. Crack over cap this cycle; "
                "slip cap held. Encoder apparent was not treated as an AE clearance.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("slip", "held; 0.0 mm/h"),
                        ("crack", "still over 12 pps this cycle"),
                        ("encoder", "1.60 mm/h unused as clearance"),
                        ("mission", "pull deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Geometric lag: encoder lamp was injected 120-160 us before the AE puck, yet "
                    "seed AE still won the 300 us race.",
                    "Delayed (abort_s=420): pad policy update forbids treating pull encoder mm/h "
                    "as a seed-AE substitute after a 7 min re-mount.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ae.seed.pps (7.010 ms, 48 pps)"),
                        ("loser", "enc.pull.mm (7.188 ms, 1.60 mm/h)"),
                        ("margin_us", 178),
                        (
                            "counterfactual_if_reversed",
                            "Encoder-first by < 178 us inside the 300 us window would have committed "
                            "a 0.18 mm/h pull with AE 48 > 12 pps cap. Order, not amplitude, selected "
                            "the hold.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7860),
            (
                "reward_inflection_note",
                "Safety and coherence step up at the REJECT gate (7.860 ms, tick 4) as the hold "
                "lands. The 7 min re-mount is delayed surprise bound to abort_s=420.",
            ),
            ("delayed_surprise_s", 420),
        ]
    )
    ras = raster_core(
        46,
        112,
        20,
        103,
        routing(
            "thalamic-relay.sic-ae",
            "spikenaut.policy.pull-hold",
            [
                ("relay_crack_pps", "policy_pull_hold", 0.70),
                ("relay_enc_pull", "policy_enc_pull", 0.24),
            ],
            "dopamine",
            0.15,
            "crack_hold_stdp; DA tags the pull_hold bind at the seed-AE win",
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
            ("decision_window_ms", 0.3),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("pull_hold", 70, 0.48, 250.0, 5),
                    pop("enc_pull", 50, 0.85),
                    pop("crack_veto", 28, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r62-823",
        "Carbopvt-Keld CK-HIL / Furnace X-3: seed AE 48 pps beats pull encoder 1.60 mm/h by "
        "178 us; correct REJECT holds the SiC pull",
        state,
        events,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct REJECT. Seed AE over cap beats encoder under-read. total 0.80 = 0.10 + 0.42 + "
        "0.12 + 0.10 + 0.06. Tick 6 binds abort_s=420.",
        ras,
        gate,
        "silicon-carbide-pvt-furnace",
        ["reject", "hil", "seed-ae", "encoder-underread", "tick6-sidecar-bound"],
        "Teaches that a HIL pull-encoder under-read losing a 178 us race does not clear a "
        "seed-AE over-rate. Hold is distillable from pps vs cap.",
        3,
    )


def record_824():
    events = [
        spike("enc.bus.ctx", 1.09, 0.43),
        spike("tc.melt.C", 3.18, 0.59),
        spike("ir.hood.C", 5.0, 0.50),
        spike("tc.melt.C", 8.04, 1.27),
        spike("ir.hood.C", 8.228, 1.09),
        spike("ctrl.gate", 8.48, 0.97),
        spike("tc.melt.C", 11.15, 0.78),
        spike("ir.hood.C", 14.8, 0.61),
        spike("ctrl.gate", 18.3, 0.84),
        spike("tc.melt.C", 21.9, 0.56),
        spike("enc.bus.ctx", 24.05, 0.40),
    ]
    excerpt = independent_excerpt(62824, 64, 26000, 13, spike_avoid_us(events))
    ticks = [
        tick(3180, 0.05, 0.04, 0.02, 0.01, 0.01),
        tick(8040, 0.08, 0.05, 0.04, 0.03, 0.02),
        tick(8228, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(8480, 0.12, 0.09, 0.05, 0.04, 0.02),
        tick(8940, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(150000000, 0.03, 0.02, 0.02, 0.01, 0.01),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Iridium-crucible puller P-5 at Yag-Fen YF-2 is already holding the YAG melt at "
                "1972 C under a 1990 C freeze-lid cap with a 0.48 mm/h pull already filed under "
                "the 0.80 mm/h seed ceiling. Hood-IR-first would extra-clamp a legal melt; "
                "melt-first ACCEPTS the filed 0.48 mm/h boule pass.",
            ),
            ("domain", "yttrium-aluminum-garnet-puller"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Hold the 0.48 mm/h pull while melt stays <= 1990 C and pull stays <= 0.80 mm/h; "
                "do not extra-clamp a legal YAG boule.",
            ),
            ("t0_us", 1756850400000824),
            ("gate_latency_us", 440),
            ("race_window_us", 460),
            ("race_window_rel_ms", [7.95, 8.41]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "tc.melt.C 1972 C under 1990",
                                "ir.hood.C 2040 C smear under 2080 look",
                            ],
                        ),
                        (
                            "semantics",
                            "Melt-first ACCEPTS the already-legal 0.48 mm/h pull. Hood-first would "
                            "extra-clamp because 2040 C looks under a 2080 C freeze-lid look.",
                        ),
                        (
                            "window_derivation",
                            "460 us = one melt-TC slot versus hood-IR group delay on this YAG-puller skid bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 188 us vs combined jitter 66 us (TC 32 + IR 34): 2.8x over a "
                            "2.0x trust floor. Reversing order by < 188 us inside the 460 us window "
                            "would have extra-clamped a legal 1972 C / 0.48 mm/h pass.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "iridium-crucible melt thermocouple tree, 1 kHz, 32 us jitter",
                    "hood IR pyrometer, 2 kHz, 34 us jitter",
                    "seed-pull encoder (context)",
                    "crucible DP (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("melt_cap_C", 1990.0),
                        ("observed_melt_C", 1972.0),
                        ("hood_C", 2040.0),
                        ("pull_cap_mm_h", 0.80),
                        ("proposed_pull_mm_h", 0.48),
                    ]
                ),
            ),
            (
                "simulation",
                OrderedDict(
                    [
                        (
                            "solver",
                            "1-D axial melt + Marangoni kernel, seed 62824; 6-zone YAG puller; "
                            "NOT lumped-CSTR, NOT U-RANS, NOT a wet-stand",
                        ),
                        (
                            "fidelity_limits",
                            "Rigid iridium crucible; no freeze-lid motion. Raster is kernelized "
                            "events, not an independent LIF.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Puller P-5 in pass; 0.48 mm/h pull armed.",
                    "2. Melt 1972 C under 1990 freeze-lid; pull 0.48 under 0.80 mm/h seed.",
                    "3. Bus encoder precursor at 1.090 ms.",
                    "4. Race window [7.950, 8.410] ms.",
                    "5. tc.melt.C 1972 C at 8.040 ms (winner).",
                    "6. ir.hood.C 2040 C at 8.228 ms (loser by 188 us).",
                    "7. Gate at 8.480 ms: ACCEPT 0.48 mm/h; executed identical to proposed.",
                    "8. Melt stays 1973 C < 1990; pull 0.481 mm/h < 0.80.",
                    "9. Hood remaining a shell glint did not require an extra clamp.",
                    "10. Delayed (survey_s=150): 150 s YAG lattice-fringe coupon on the seed lock.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_yag_pull"),
            (
                "parameters",
                OrderedDict(
                    [("pull_mm_h", 0.48), ("melt_C", 1972.0), ("hood_C", 2040.0)]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("melt_C", 1972.0),
                        ("melt_cap_C", 1990.0),
                        ("hood_C", 2040.0),
                        ("pull_cap_mm_h", 0.80),
                        ("race_margin_us", 188),
                        ("combined_jitter_us", 66),
                        ("survey_s", 150),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes keeping the filed 0.48 mm/h pull: melt 1972 C is under the "
                "1990 C freeze-lid cap and 0.48 mm/h is under 0.80 mm/h seed.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Melt 1972 C won by 188 us and is under the 1990 C freeze-lid cap. Hood 2040 C "
                "is a shell glint, not a freeze-lid miss. ACCEPT the filed 0.48 mm/h pull. "
                "Executed identical to proposed. An extra clamp is not indicated.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "melt_C",
                            OrderedDict(
                                [
                                    ("cap", 1990.0),
                                    ("observed", 1972.0),
                                    ("executed_pull_mm_h", 0.48),
                                ]
                            ),
                        ),
                        ("hood_C", OrderedDict([("look", 2080.0), ("observed", 2040.0)])),
                        (
                            "order_evidence",
                            OrderedDict(
                                [("margin_us", 188), ("combined_jitter_us", 66), ("ratio", 2.85)]
                            ),
                        ),
                    ]
                ),
            ),
        ]
    )
    executed = OrderedDict(
        [
            ("name", "hold_yag_pull"),
            (
                "parameters",
                OrderedDict(
                    [("pull_mm_h", 0.48), ("melt_C", 1972.0), ("hood_C", 2040.0)]
                ),
            ),
            (
                "gate_effect",
                "ACCEPT: executed identical to proposed 0.48 mm/h pull. Melt 1972 C < 1990 cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT kept the filed 0.48 mm/h YAG pull. Melt stayed 1973 C under "
                "1990 C. Hood remaining a shell glint was the losing channel and did not justify "
                "an extra clamp.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("pull", "held; 0.48 mm/h"),
                        ("melt", "1973 C < 1990 C"),
                        ("hood", "2040 C glint unused as freeze-lid miss"),
                        ("boule", "pass continues"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Hood IR 2040 C losing a 188 us race did not predict a freeze-lid miss; "
                    "reversing 188 us would have extra-clamped a legal 1972 C pass.",
                    "Delayed (survey_s=150): 150 s YAG lattice-fringe coupon on the seed lock; "
                    "not a safety inflection.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "tc.melt.C (8.040 ms, 1972 C)"),
                        ("loser", "ir.hood.C (8.228 ms, 2040 C)"),
                        ("margin_us", 188),
                        (
                            "counterfactual_if_reversed",
                            "Hood-first by < 188 us inside the 460 us window would have extra-clamped "
                            "a legal pass. Melt-first confirms the filed pull.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 8480),
            (
                "reward_inflection_note",
                "Heads rise at the ACCEPT (8.480 ms, tick 4). The 150 s YAG coupon is delayed "
                "surprise bound to survey_s=150, not the inflection.",
            ),
            ("delayed_surprise_s", 150),
        ]
    )
    ras = raster_core(
        26,
        64,
        40,
        67,
        routing(
            "thalamic-relay.yag-melt",
            "spikenaut.policy.pull-accept",
            [
                ("relay_melt_C", "policy_pull_accept", 0.66),
                ("relay_hood_IR", "policy_extra_clamp", 0.23),
            ],
            "serotonin",
            0.12,
            "melt_confirm_stdp; 5-HT tags the pull_accept bind at the melt-TC win",
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
            ("decision_window_ms", 0.46),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("pull_accept", 50, 0.5, 175.0, 4),
                    pop("extra_clamp", 40, 0.85, 40.0, 1),
                    pop("hood_veto", 22, 0.8),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r62-824",
        "Yag-Fen YF-2 / Puller P-5: melt 1972 C beats hood IR 2040 C by 188 us; ACCEPT "
        "already-legal 0.48 mm/h YAG pull",
        state,
        events,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Clean ACCEPT of an already-legal YAG pull. total 1.06 = 0.40 + 0.28 + 0.18 + 0.12 + "
        "0.08. Tick 6 binds survey_s=150.",
        ras,
        gate,
        "yttrium-aluminum-garnet-puller",
        ["accept", "simulated", "melt-vs-hood", "pull-legal", "tick6-sidecar-bound"],
        "Teaches that a lagging hood IR losing a 188 us race does not require an extra clamp "
        "when the YAG melt is already under the freeze-lid cap.",
        4,
    )


def record_825():
    events = [
        spike("enc.press.ctx", 0.86, 0.44),
        spike("tc.cell.C", 1.96, 0.61),
        spike("dp.gasket.kPa", 3.38, 0.52),
        spike("tc.cell.C", 5.08, 1.30),
        spike("dp.gasket.kPa", 5.26, 1.12),
        spike("ctrl.gate", 5.44, 0.99),
        spike("tc.cell.C", 8.02, 0.77),
        spike("dp.gasket.kPa", 11.35, 0.58),
        spike("ctrl.gate", 14.8, 0.83),
        spike("tc.cell.C", 18.1, 0.54),
        spike("enc.press.ctx", 21.05, 0.39),
    ]
    excerpt = independent_excerpt(62825, 80, 24000, 12, spike_avoid_us(events))
    ticks = [
        tick(1960, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5080, 0.08, 0.06, 0.04, 0.02, 0.02),
        tick(5260, 0.08, 0.05, 0.03, 0.02, 0.01),
        tick(5440, 0.12, 0.09, 0.06, 0.04, 0.02),
        tick(5980, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(210000000, 0.04, 0.02, 0.02, 0.01, 0.01),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Belt-type HPHT cell HP-3 at Adamant-Beck AB-8 is already holding 5.4 GPa under "
                "a 5.8 GPa anvil ceiling while the cell sits at 1380 C against a 1480 C thermal "
                "trip. Gasket-DP-first would extra-clamp a legal diamond growth; cell-TC-first "
                "ACCEPTS the filed 5.4 GPa HPHT pass.",
            ),
            ("domain", "diamond-hpht-press"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Hold the 5.4 GPa load while cell stays <= 1480 C and pressure stays <= 5.8 GPa; "
                "do not extra-clamp a legal HPHT diamond cell.",
            ),
            ("t0_us", 1756850400000825),
            ("gate_latency_us", 360),
            ("race_window_us", 320),
            ("race_window_rel_ms", [5.0, 5.32]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "tc.cell.C 1380 C under 1480",
                                "dp.gasket.kPa 8.2 smear under 7.0 look",
                            ],
                        ),
                        (
                            "semantics",
                            "Cell-TC-first ACCEPTS the already-legal 5.4 GPa load. DP-first would "
                            "extra-clamp because 8.2 kPa looks over a 7.0 kPa gasket look.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one cell-TC slot versus gasket-DP group delay on this HPHT skid bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 58 us (TC 26 + DP 32): 3.1x over a "
                            "2.0x trust floor. Reversing order by < 180 us inside the 320 us window "
                            "would have extra-clamped a legal 1380 C / 5.4 GPa pass.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "cell-crown thermocouple, 4 kHz, 26 us jitter",
                    "gasket DP transmitter, 1 kHz, 32 us jitter",
                    "anvil-load encoder (context)",
                    "end-seal IR (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("cell_trip_C", 1480.0),
                        ("observed_cell_C", 1380.0),
                        ("gasket_dp_kPa", 8.2),
                        ("press_cap_GPa", 5.8),
                        ("proposed_press_GPa", 5.4),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Cell HP-3 in pass; 5.4 GPa load armed.",
                    "2. Cell 1380 C under 1480 trip; pressure 5.4 under 5.8 GPa anvil.",
                    "3. Anvil encoder precursor at 0.860 ms.",
                    "4. Race window [5.000, 5.320] ms.",
                    "5. tc.cell.C 1380 C at 5.080 ms (winner).",
                    "6. dp.gasket.kPa 8.2 at 5.260 ms (loser by 180 us).",
                    "7. Gate at 5.440 ms: ACCEPT 5.4 GPa; executed identical to proposed.",
                    "8. Cell stays 1382 C < 1480; pressure 5.41 GPa < 5.8.",
                    "9. DP remaining a gasket glint did not require an extra clamp.",
                    "10. Delayed (dwell_s=210): 3.5 min Raman coupon on the anvil lock.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_hpht_press"),
            (
                "parameters",
                OrderedDict(
                    [("press_GPa", 5.4), ("cell_C", 1380.0), ("gasket_dp_kPa", 8.2)]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("cell_C", 1380.0),
                        ("cell_trip_C", 1480.0),
                        ("gasket_dp_kPa", 8.2),
                        ("press_cap_GPa", 5.8),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("dwell_s", 210),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes keeping the filed 5.4 GPa load: cell 1380 C is under the "
                "1480 C trip and 5.4 GPa is under 5.8 GPa anvil.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Cell 1380 C won by 180 us and is under the 1480 C trip. Gasket DP 8.2 kPa is "
                "a junction glint, not a thermal miss. ACCEPT the filed 5.4 GPa load. Executed "
                "identical to proposed. An extra clamp is not indicated.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "cell_C",
                            OrderedDict(
                                [
                                    ("trip", 1480.0),
                                    ("observed", 1380.0),
                                    ("executed_press_GPa", 5.4),
                                ]
                            ),
                        ),
                        (
                            "gasket_dp_kPa",
                            OrderedDict([("look", 7.0), ("observed", 8.2)]),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [("margin_us", 180), ("combined_jitter_us", 58), ("ratio", 3.1)]
                            ),
                        ),
                    ]
                ),
            ),
        ]
    )
    executed = OrderedDict(
        [
            ("name", "hold_hpht_press"),
            (
                "parameters",
                OrderedDict(
                    [("press_GPa", 5.4), ("cell_C", 1380.0), ("gasket_dp_kPa", 8.2)]
                ),
            ),
            (
                "gate_effect",
                "ACCEPT: executed identical to proposed 5.4 GPa load. Cell 1380 C < 1480 trip.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT kept the filed 5.4 GPa load. Cell stayed 1382 C under 1480. "
                "DP remaining a gasket glint was the losing channel and did not justify an extra clamp.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("press", "held; 5.4 GPa"),
                        ("cell", "1382 C < 1480"),
                        ("dp", "8.2 kPa glint unused as thermal miss"),
                        ("diamond", "pass continues"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Gasket DP 8.2 kPa losing a 180 us race did not predict a thermal miss; "
                    "reversing 180 us would have extra-clamped a legal 1380 C cell.",
                    "Delayed (dwell_s=210): 3.5 min Raman coupon on the anvil lock; not a safety inflection.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "tc.cell.C (5.080 ms, 1380 C)"),
                        ("loser", "dp.gasket.kPa (5.260 ms, 8.2 kPa)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "DP-first by < 180 us inside the 320 us window would have extra-clamped "
                            "a legal cell. Cell-TC-first confirms the filed load.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5440),
            (
                "reward_inflection_note",
                "Heads rise at the ACCEPT (5.440 ms, tick 4). The 3.5 min Raman coupon is delayed "
                "surprise bound to dwell_s=210, not the inflection.",
            ),
            ("delayed_surprise_s", 210),
        ]
    )
    extra = OrderedDict(
        [
            ("excerpt_source", "kernelized_events"),
            ("sim_scope", "none"),
            ("dwell_s", 210),
            ("delayed_surprise_s", 210),
            ("isi_histogram", isi_histogram(events)),
        ]
    )
    ras = raster_core(
        24,
        80,
        28,
        54,
        routing(
            "thalamic-relay.hpht-tc",
            "spikenaut.policy.press-accept",
            [
                ("relay_cell_C", "policy_press_accept", 0.69),
                ("relay_dp_gasket", "policy_extra_clamp", 0.21),
            ],
            "octopamine",
            0.05,
            "cell_confirm_stdp; octopamine tags the press_accept bind at the cell-TC win",
        ),
        excerpt,
        extra=extra,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.32),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("press_accept", 45, 0.5, 210.0, 3),
                    pop("extra_clamp", 40, 0.85, 40.0, 1),
                    pop("dp_veto", 20, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r62-825",
        "Adamant-Beck AB-8 / Press HP-3: cell 1380 C beats gasket DP 8.2 kPa by 180 us; ACCEPT "
        "already-legal 5.4 GPa HPHT load with ISI histogram sidecar",
        state,
        events,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Clean ACCEPT of an already-legal HPHT diamond load. total 1.14 = 0.44 + 0.30 + 0.20 + "
        "0.12 + 0.08. Tick 6 binds dwell_s=210. ISI histogram on same-channel spike_events.",
        ras,
        gate,
        "diamond-hpht-press",
        [
            "accept",
            "designed",
            "cell-vs-dp",
            "press-legal",
            "tick6-sidecar-bound",
            "isi-histogram",
        ],
        "Teaches that a lagging gasket DP losing a 180 us race does not require a wait when "
        "cell temperature is already under the thermal trip. ISI histogram densifies the "
        "refractory floor without a second labeled LIF.",
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
    return f"""# Thalamic Trajectory Factory — NOTES-r62

- Factory: `thalamic-trajectory-factory`
- Run label: `2026-09-02-final-heavy`
- Generator: `grok-4.6`
- Channel: SuperGrok Heavy consumer chat (RM-793 research-only)
- Quota: 5
- Quality: Q=5
- IDs: `ttf-r62-821` … `ttf-r62-825` (326–330 already occupy `/tmp/ttf-r62`; this window uses 821–825)
- Domains this batch: `bismuth-telluride-zone-melt`, `praseodymium-fluoride-cell`, `silicon-carbide-pvt-furnace`, `yttrium-aluminum-garnet-puller`, `diamond-hpht-press`

These five domain slugs sit outside the prompt 8-pool and outside staged occupancy harvested from jsonl SoT plus `/tmp/ttf-occupied-domains.txt` (including unpublished `/tmp/ttf-r62` acrylonitrile-sohio / vacuum-wash-grid / aod-argon-converter / opp-biax-tenter / formaldehyde-silver-ox). All five plants are invented (Bismite-Holt, Praseo-Ness, Carbopvt-Keld, Yag-Fen, Adamant-Beck). Do not restack prior TTF plants.

## Batch map

| id | domain | decision | correctness | sim_or_real | total | edge |
|----|--------|----------|-------------|-------------|-------|------|
| ttf-r62-821 | bismuth-telluride-zone-melt | MODIFY | correct | designed | **−0.48** | process-correct travel clamp; quartz-ampoule crack inside 42 ms raster; independent LIF |
| ttf-r62-822 | praseodymium-fluoride-cell | REJECT | **incorrect (wrong-reject / leftover-kelvin-offset)** | designed | −0.62 | live 986.0 C < 1080 trip; leftover 986+273.15=1259.15 C treated as PV |
| ttf-r62-823 | silicon-carbide-pvt-furnace | REJECT | correct | hil | +0.80 | seed AE 48 pps beats pull encoder 1.60 mm/h; hold slip |
| ttf-r62-824 | yttrium-aluminum-garnet-puller | ACCEPT | correct | simulated | +1.06 | melt 1972 C vs hood IR 2040 C; proposed 0.48 mm/h already legal |
| ttf-r62-825 | diamond-hpht-press | ACCEPT | correct | designed | +1.14 | cell 1380 C vs gasket DP 8.2 kPa; proposed 5.4 GPa already legal; ISI histogram |

Gate mix: 2 ACCEPT, 1 correct MODIFY (partnered-neg, in-window), 1 correct REJECT, 1 incorrect REJECT (leftover-kelvin-offset / K-as-C). Provenance: designed×3, simulated×1, hil×1 (Carbopvt-Keld CK-HIL SiC PVT pad). Intra-batch Jaccard on `state.description` {jmax:.3f} (< 0.4).

## Wrong-reject / leftover-kelvin-offset

**ttf-r62-822** is the mandated incorrect gate (`safety_decision.correctness=incorrect`, `meta.supervisor_error_type=wrong-reject`). Alternate vs odd rounds: even rounds host wrong-reject (r12/r14/…/r62); odd rounds host wrong-modify. Do not emit a wrong-ACCEPT. Error *class* is **leftover-kelvin-offset / K-as-C**, not r16 reticle-as-wafer, not r18 empty-tank, not r20 oscillation-as-PSV, not r22 class-transplant, not r30 stale-firmware floor, not r32 stale-peak-hold, not r34 wrong-bus, not r36 leftover-bar, not r38 loop-test-inject, not r40 setpoint-echo, not r44 ksi-shadow, not r46 kPa-as-MPa, not r52/r60/r62-draft gauge-vs-absolute, not r64 reverse-scale / inverted-4-20, not r72/r76 NAMUR fail-high, not r90/r92 type-table leftover.

Praseo-Ness PN-6 / Cell C-1 reads live bath **986.0 C** against a published **1080.0 C** freeze-lid trip. A leftover Kelvin conversion still prints **1259.15 C** (`986.0 + 273.15`). Sidecar arithmetic `986.0 < 1080.0` is true. A weak supervisor binds the Kelvin sum as live C, REJECT-holds current 7.2 → 0.0 kA, and leaves a legal PrF3 cell idle. Convictable without PrF3 kinetics: `evidence.live_C < evidence.trip_C`, `evidence.leftover_K_as_C == 1259.15`, `evidence.kelvin_offset_K == 273.15`, `evidence.kelvin_as_C == false` on the proposal / `true` on executed, `executed_action` sets `current_kA=0` / `hold=true`, `raster.routing.table` sends `relay.tc.kelvin` → `policy.hold_reject` (weight 0.74) with no positive weight to `policy.go_accept`, and `gate_snn` has `hold_reject` above threshold while `go_accept` is not. Recovery: ACCEPT; leave 7.2 kA; bind live 986.0 C. Cost: 9 min missed Pr metal window (`missed_window_s=540`).

## Partnered-negative in-window (821)

**ttf-r62-821** is the partnered negative: process-correct MODIFY (travel held 9.0 mm/h; heater 564 C <= 580 cap) while the world still charges. Safety −0.64 prices the quartz-ampoule crack at **22.400 ms**; `task_progress` stays +0.30 because the clamp completed. Inflection `t_us=22400` is tick 5 and is **inside** the 42 ms raster (`22400 ≤ 42000`). Named un-netted loss: 13 min ampoule re-seal (`abort_s=780`). Not folded into process heads.

Independent LIF (the one labeled sidecar sim): `state.sim_or_real` remains `designed`. `raster.excerpt_source=independent_lif`, `raster.sim_scope=sidecar_only`, `raster.lif` seed 62821, stim `[22000, 25000]`. Excerpt is membrane crossings (`lif.clamp` early vs `lif.crack` 22–25 ms), not a 1:1 remap of `spike_events`. `meta.tags` include `independent-lif-raster` and `sidecar-sim-only`.

## ISI histogram (825)

**ttf-r62-825** carries `raster.isi_histogram` (bin 0.8 ms, same-channel ISIs from `spike_events`, min gap ≥ 0.8 ms). Addresses the r61 densification ask for an ISI sidecar without claiming a second labeled LIF.

## Reward formula and tick reconciliation

Declared aggregation on every record:

`total = task_progress + safety + efficiency + coherence + exploration`

Per-component scalar = arithmetic sum of that component over ticks (TTF-M6: exactly 6 ticks). Tick 6 is bound to a published sidecar (`abort_s`, `missed_window_s`, `survey_s`, `dwell_s`) via `future_outcome.delayed_surprise_s` and is strictly after the raster window. Inflection `t_us` is an actual tick.

| id | ticks | tp | saf | eff | coh | exp | total | inflection tick |
|----|-------|----|-----|-----|-----|-----|-------|-----------------|
| 821 | 6 | +0.30 | −0.64 | −0.14 | +0.04 | −0.04 | −0.48 | 5 (22400) |
| 822 | 6 | −0.22 | −0.10 | −0.24 | −0.12 | +0.06 | −0.62 | 4 (5980) |
| 823 | 6 | +0.10 | +0.42 | +0.12 | +0.10 | +0.06 | +0.80 | 4 (7860) |
| 824 | 6 | +0.40 | +0.28 | +0.18 | +0.12 | +0.08 | +1.06 | 4 (8480) |
| 825 | 6 | +0.44 | +0.30 | +0.20 | +0.12 | +0.08 | +1.14 | 4 (5440) |

Tick-6 sidecar bind: 821 `abort_s=780`, 822 `missed_window_s=540`, 823 `abort_s=420`, 824 `survey_s=150`, 825 `dwell_s=210`.

## Raster / energy (Loihi-2 4-core, 23 pJ/spike)

| id | domain | n | rate Hz | window_ms | spikes | energy_pJ | energy_uJ |
|----|--------|---|---------|-----------|--------|-----------|-----------|
| 821 | bismuth-telluride-zone-melt | 76 | 24 | 42 | 77 | 1771 | 0.001771 |
| 822 | praseodymium-fluoride-cell | 96 | 32 | 28 | 86 | 1978 | 0.001978 |
| 823 | silicon-carbide-pvt-furnace | 112 | 20 | 46 | 103 | 2369 | 0.002369 |
| 824 | yttrium-aluminum-garnet-puller | 64 | 40 | 26 | 67 | 1541 | 0.001541 |
| 825 | diamond-hpht-press | 80 | 28 | 24 | 54 | 1242 | 0.001242 |

`spikes = round(n × rate × window_s)`. Every record carries `gate_snn` whose `decision` matches the safety gate; populations that declare rate+spikes meet the same ±1 budget against `decision_window_s`. `routing.third_factor` has modulator (NA / ACh / DA / 5-HT / octopamine), `tau_e_s`/`tau_e_ms` pair, and eligibility. Excerpt same-neuron gap ≥ 1000 µs; spike trains same-channel refractory ≥ 0.8 ms. Non-821 excerpts are kernelized and independent of `spike_events` times (overlap < 0.8).

## Local checks (staging, not a rewrite of other raw files)

See generator stdout: `check_jsonl` FactoryStaging, `validate_run.check_line`, `dumps_exact_json`, `raster_status`, `verify_batch_for_frontier(strict=True)`, `spike_probe.py --strict`, tick sums, refractory, Jaccard.

Never `training_ready`. Never `sim_or_real=real`. Create-only write of this round's batch/NOTES under the operator window.

## Residual weaknesses (honest)

1. Only **one** labeled independent LIF (821). 825 adds an ISI histogram but is not a second population sim.
2. Wrong-ACCEPT still absent (guard).
3. 824 and 825 are both already-legal ACCEPTs; a later round could pair one ACCEPT with a world charge that does not go negative, or drop to a single ACCEPT.
4. Five domain slugs leave the prompt's 8-item pool; a later round that must stay inside the pool will have to rotate sit-outs instead.
5. Tick-6 sidecar bind is standing machinery (r14+), not a new class.

## Next densification target

Labeled LIF on a second record. Remaining unused wrong-REJECT subclasses include **stale-setpoint / swapped-tag** and **3-wire RTD lead-resistance as temperature**. Wrong-ACCEPT remains structurally absent until a prompt amendment.

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
    if len(wrong) != 1 or wrong[0]["id"] != "ttf-r62-822":
        issues.append(f"wrong-gate set {[w['id'] for w in wrong]}")
    if any(r["state"]["sim_or_real"] == "real" for r in records):
        issues.append("sim_or_real=real")
    hil = [r["id"] for r in records if r["state"]["sim_or_real"] == "hil"]
    if hil != ["ttf-r62-823"]:
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
        if rec["id"] == "ttf-r62-821":
            if rec["raster"].get("excerpt_source") != "independent_lif":
                issues.append("821 missing independent_lif")
            if rec["future_outcome"]["reward_inflection_t_us"] > rec["raster"]["window_ms"] * 1000:
                issues.append("821 inflection outside window")
            if rec["reward_components"]["total"] >= 0:
                issues.append("821 partnered-neg total not negative")
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
        if rec["meta"]["round"] != 62:
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
        if rec["id"] == "ttf-r62-822":
            if "policy.go_accept" in table_tos:
                issues.append("822 routing has go_accept")
            if "policy.hold_reject" not in table_tos:
                issues.append("822 missing hold_reject routing")
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
        gl = rec["state"]["gate_latency_us"]
        rw = rec["state"]["race_window_us"]
        if not (50 <= gl <= 2000):
            issues.append(f"{rec['id']} gate_latency {gl}")
        if not (50 <= rw <= 1000):
            issues.append(f"{rec['id']} race_window {rw}")
    if rec["id"] == "ttf-r62-825" and "isi_histogram" not in records[-1]["raster"]:
        issues.append("825 missing isi_histogram")
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
        BATCH_PATH, "batch-r62.jsonl", staging=FactoryStaging(enabled=True)
    )
    report.append(("check_jsonl FactoryStaging", errors, warnings, kinds, nrec))
    line_errs = []
    for i, rec in enumerate(records, 1):
        errs, kind = check_line(rec, f"batch-r62.jsonl:{i}", factory_staging=True)
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
    records = [record_821(), record_822(), record_823(), record_824(), record_825()]
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
        print(f"PIPELINE {name}:")
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
            else:
                print("  ok")
        elif name == "raster_status":
            if item[1]:
                failed = True
                print("  RASTER_FAIL", item[1])
            else:
                print("  ok")
        elif name == "verify_batch_for_frontier":
            counts, findings, blocked = item[1], item[2], item[3]
            print(f"  counts={counts} blocked={blocked}")
            if blocked or counts.get("failed") or counts.get("inconclusive"):
                failed = True
                print("  FINDINGS", findings)
        elif name == "validate_novel_coverage":
            print("  ", item[1])
            if item[1]:
                failed = True
        elif name == "spike_probe":
            print("  rc", item[1])
            if item[1] != 0:
                failed = True
                print("  stdout", item[2])
                print("  stderr", item[3])
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
