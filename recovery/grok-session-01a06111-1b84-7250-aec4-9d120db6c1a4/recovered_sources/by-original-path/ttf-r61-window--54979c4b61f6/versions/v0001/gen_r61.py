#!/usr/bin/env python3
"""Emit TTF r61 JSONL (ttf-r61-321..325) into the 2026-09-02-final-heavy window.

Create-only. Never overwrites an existing batch/NOTES. User-authorized window
path for this run; does not touch other files under outputs/raw/.
"""

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

OUT_DIR = Path(
    "/tmp/sf-window/outputs/raw/2026-09-02-final-heavy/thalamic-trajectory-factory"
)
BATCH_PATH = OUT_DIR / "batch-r61.jsonl"
NOTES_PATH = OUT_DIR / "NOTES-r61.md"
REPO = Path("/tmp/sf-window")
PIPELINES = REPO / "pipelines"

PJ_PER_SPIKE = 23
RIGHTS = OrderedDict(
    [
        ("provider", "SpaceXAI/xAI"),
        ("model", "grok-4.6"),
        ("channel", "consumer"),
        ("subscription_plan", "SuperGrok Heavy"),
        ("generation_surface", "SuperGrok Heavy chat"),
        ("generated_at", "2026-09-02T18:45:00Z"),
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
    "niobium-pentachloride-chlorinator",
    "sulfur-hexafluoride-reactor",
    "cadmium-telluride-bridgman",
    "neodymium-fluoride-electrolyzer",
    "tungsten-carbide-carburizer",
}
THIS_PLANTS = (
    "Columbic-Howe",
    "Fluorspar-Beck",
    "Bridgman-Keld",
    "Didym-Naze",
    "Cermet-Brae",
)
BANNED_DOMAINS = {
    "warehouse-amr",
    "aerial-swarm",
    "underwater-rov",
    "grid-inspection",
    "humanoid-locomotion",
    "surgical-assist",
    "industrial-assembly",
    "autonomous-driving",
}


def harvest_occupancy():
    """Prior staged batches are global occupancy. r61 window must not reuse their domains or title plants."""
    domains = set(BANNED_DOMAINS)
    plants = set()
    for path in sorted(Path("/tmp").glob("ttf-r*/batch-r*.jsonl")):
        if path.parent.name == "ttf-r61-window":
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            domains.add(rec["state"]["domain"])
            title = rec.get("title") or ""
            m = re.match(r"(?:WRONG-(?:MODIFY|REJECT) at )?([A-Za-z0-9-]+)", title)
            if m:
                plants.add(m.group(1))
    for gpath in sorted(Path("/tmp").glob("ttf-r*/*.py")):
        if gpath.parent.name in {"ttf-r61-window"}:
            continue
        txt = gpath.read_text(encoding="utf-8", errors="ignore")
        for m in re.finditer(r"(?:THIS_DOMAINS|MY_DOMAINS)\s*=\s*[\{(](.*?)[\})]", txt, re.S):
            domains.update(re.findall(r'"([^"]+)"', m.group(1)))
        for m in re.finditer(r"(?:THIS_PLANTS|MY_PLANTS)\s*=\s*\((.*?)\)", txt, re.S):
            plants.update(re.findall(r'"([^"]+)"', m.group(1)))
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


def lif_321_excerpt():
    n = 76
    dt_us = 100
    tau_m_ms = 19.0
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.91
    i_stim_peak = 2.48
    stim = (22000, 25000)
    seed = 613211
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
    take(burst, 9, label_times=(22200, 23100, 23800))
    clamp = [(t, nid) for t, nid in picked if t < 22000][:7]
    tear = [(t, nid) for t, nid in picked if t >= 22000][:9]
    picked = sorted(clamp + tear, key=lambda item: (item[0], item[1]))
    if len(picked) < 10:
        raise RuntimeError(f"LIF excerpt short: {len(picked)}")
    channels = ["lif.clamp" if t < 22000 else "lif.weep" for t, _ in picked]
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
            ("seed", 613211),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-13 carry +0.62 chlorine-feed clamp bias; stim 22-25 ms is the packed-column weep dump.",
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
            ("round", 61),
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


def record_321():
    excerpt, extra = lif_321_excerpt()
    extra = OrderedDict(extra)
    extra["abort_s"] = 780
    extra["delayed_surprise_s"] = 780
    ticks = [
        tick(2380, 0.04, -0.02, -0.02, 0.01, 0.00),
        tick(6040, 0.08, -0.04, -0.02, 0.01, -0.01),
        tick(6228, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(6840, 0.08, -0.05, -0.03, 0.02, -0.01),
        tick(22200, 0.04, -0.45, -0.03, -0.01, -0.01),
        tick(780000000, 0.02, -0.05, -0.02, 0.01, -0.01),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Niobium pentachloride chlorinator C-3 at Columbic-Howe CH-5 is already feeding "
                "42.0 kg/h of dry chlorine while the packed-bed sits at 428 C against a 390 C "
                "NbCl5-formation cap. Temperature-first cuts Cl2 to 28.0 kg/h; chlorine-first "
                "would keep 42.0 kg/h because scrubber DP 8.4 kPa is still under the 12.0 kPa "
                "flood ceiling. A packed-column weep already seated over the catch-pot does not "
                "appear on bed T or Cl2 FT until the AE dump.",
            ),
            ("domain", "niobium-pentachloride-chlorinator"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep chlorinator C-3 bed <= 390 C and finish the NbCl5 pass without dumping "
                "liquor onto the catch-pot floor.",
            ),
            ("t0_us", 1756850400000321),
            ("gate_latency_us", 720),
            ("race_window_us", 400),
            ("race_window_rel_ms", [6.0, 6.40]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "tc.bed.C 428 over 390 NbCl5-formation cap",
                                "ft.cl2.kg 42.0 with scrubber DP 8.4 under 12.0 kPa",
                            ],
                        ),
                        (
                            "semantics",
                            "Temperature-first latches chlorine clamp 42.0 -> 28.0 kg/h; "
                            "chlorine-first keeps 42.0 kg/h on a 'still under flood-ceiling' model.",
                        ),
                        (
                            "window_derivation",
                            "400 us = one packed-bed TC slot versus the chlorine-mass FT publisher "
                            "on this chlorinator skid bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 188 us vs combined jitter 64 us (TC 30 + FT 34): 2.9x over "
                            "a 2.0x trust floor. Reversing order by < 188 us inside the 400 us "
                            "window would have kept 42.0 kg/h; predicted next-sample 436 C > 390 "
                            "NbCl5-formation cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "packed-bed thermocouple lance, 2 kHz, 30 us jitter",
                    "chlorine mass-flow FT + scrubber DP, 1 kHz, 34 us jitter",
                    "column AE puck (context)",
                    "catch-pot IR (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("bed_cap_C", 390.0),
                        ("observed_bed_C", 428.0),
                        ("cl2_kg_h", 42.0),
                        ("scrubber_dp_kPa", 8.4),
                        ("scrubber_cap_kPa", 12.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Chlorinator C-3 in NbCl5 pass; Cl2 42.0 kg/h; bed 428 C.",
                    "2. Scrubber DP 8.4 kPa under 12.0 flood; weep armed.",
                    "3. Cl2-FT precursor at 1.160 ms.",
                    "4. Race window [6.000, 6.400] ms.",
                    "5. tc.bed.C 428 C at 6.040 ms (winner).",
                    "6. ft.cl2.kg 42.0 at 6.228 ms (loser by 188 us).",
                    "7. Gate at 6.840 ms: MODIFY clamp 42.0 -> 28.0 kg/h.",
                    "8. After clamp bed 384 C <= 390; DP still 8.4 kPa.",
                    "9. At 22.200 ms a packed-column weep dumps 0.5 t of liquor onto the catch-pot.",
                    "10. 13 min column re-pack (abort_s=780); named un-netted loss.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_chlorine_feed"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("cl2_kg_h", 42.0),
                        ("bed_C", 428.0),
                        ("scrubber_dp_kPa", 8.4),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("bed_C", 428.0),
                        ("bed_cap_C", 390.0),
                        ("predicted_unclamped_next_C", 436.0),
                        ("cl2_kg_h", 42.0),
                        ("scrubber_dp_kPa", 8.4),
                        ("scrubber_cap_kPa", 12.0),
                        ("race_margin_us", 188),
                        ("combined_jitter_us", 64),
                        ("abort_s", 780),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 42.0 kg/h because scrubber DP 8.4 kPa is under 12.0, treating "
                "the 428 C bed as a still-wet lance rather than an NbCl5-formation miss.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Bed 428 C won by 188 us, so the chlorinator is over the 390 C NbCl5-formation "
                "cap, not still a flood-ceiling story. Holding 42.0 kg/h predicts next-sample "
                "436 C > 390. MODIFY: Cl2 42.0 -> 28.0 kg/h. Observed after clamp 384 C <= "
                "390. A full REJECT is not indicated: a clean NbCl5 pass accepts 28.0 kg/h.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "bed_C",
                            OrderedDict(
                                [
                                    ("cap", 390.0),
                                    ("observed", 428.0),
                                    ("predicted_unclamped_next", 436.0),
                                    ("clamped_cl2_kg_h", 28.0),
                                    ("observed_after_clamp", 384.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 188),
                                    ("combined_jitter_us", 64),
                                    ("ratio", 2.94),
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
            ("name", "clamped_chlorine_feed"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("cl2_kg_h", 28.0),
                        ("bed_C", 384.0),
                        ("scrubber_dp_kPa", 8.4),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: Cl2 42.0 -> 28.0 kg/h. Process-correct vs the 390 C NbCl5-formation "
                "cap. Packed-column weep still dumps at 22.200 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held bed at 384 C. At 22.200 ms a packed-column weep "
                "already seated over the catch-pot dumped 0.5 t of liquor onto the floor. Clamp "
                "reduced dump energy; it did not prevent the dump. Partnered negative: process "
                "heads stay honest; world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("bed", "clamp executed; peak 384 C <= 390 cap"),
                        ("column", "weep dump at 22.200 ms; 0.5 t liquor"),
                        ("repair", "13 min column re-pack (abort_s=780)"),
                        ("mission", "CH-5 NbCl5 pass incomplete this cycle"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither bed T nor Cl2 FT predicted the seated packed-column weep; ae.weep.dump is a new channel at 22.200 ms, 15.360 ms after the gate, still inside the 42 ms raster.",
                    "Delayed (abort_s=780): 13 min column re-pack. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "13 min column re-pack after the packed-column weep. Safety head -0.64 "
                "prices the dump; task_progress stays +0.30 because the clamp completed.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "tc.bed.C (6.040 ms, 428 C)"),
                        ("loser", "ft.cl2.kg (6.228 ms, 42.0 kg/h)"),
                        ("margin_us", 188),
                        (
                            "counterfactual_if_reversed",
                            "Chlorine-first by < 188 us inside the 400 us window would have kept "
                            "42.0 kg/h; predicted next-sample 436 C would have missed the 390 "
                            "NbCl5-formation cap even without the weep. The MODIFY is still the "
                            "correct process. The dump is a later world charge either way, "
                            "cheaper with the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22200),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.200 ms packed-column weep (tick t_us=22200), inside "
                "the 42 ms raster. The correct MODIFY at 6.840 ms is in the same excerpt. Do "
                "not put inflection on the abort_s=780 re-pack tick.",
            ),
            ("delayed_surprise_s", 780),
        ]
    )
    spikes = [
        spike("ft.cl2.ctx", 1.160, 0.41),
        spike("tc.bed.C", 2.380, 0.58),
        spike("ft.cl2.kg", 3.910, 0.50),
        spike("tc.bed.C", 6.040, 1.31),
        spike("ft.cl2.kg", 6.228, 1.12),
        spike("ctrl.gate", 6.840, 0.97),
        spike("tc.bed.C", 8.150, 0.82),
        spike("ft.cl2.kg", 10.600, 0.64),
        spike("ctrl.gate", 14.200, 0.86),
        spike("ae.weep.dump", 22.200, 1.48),
        spike("ae.weep.dump", 24.050, 0.93),
        spike("ft.cl2.ctx", 29.700, 0.40),
        spike("tc.bed.C", 36.100, 0.55),
    ]
    ras = raster_core(
        42,
        76,
        24,
        77,
        routing(
            "thalamic-relay.ch-bed",
            "spikenaut.policy.cl2-clamp",
            [
                ("relay_bed_C", "policy_cl2_clamp", 0.68),
                ("relay_cl2_ft", "policy_cl2_hold", 0.29),
                ("relay_ae_weep", "policy_cl2_clamp", -0.42),
            ],
            "noradrenaline",
            0.04,
            "surprise-gated pre_post_stdp; NA at bed win (6.040 ms) opens a 42 ms "
            "eligibility trace that still covers the 22.200 ms packed-column weep",
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
                    pop("cl2_clamp", 50, 0.50, 200.0, 4),
                    pop("cl2_hold", 40, 0.80, 50.0, 1),
                    pop("weep_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r61-321"),
            (
                "title",
                "Columbic-Howe CH-5 / Chlorinator C-3: bed 428 C beats Cl2 42.0 kg/h by 188 us; "
                "correct MODIFY still eats an in-window packed-column weep (partnered negative total -0.48)",
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
                    "42 ms raster. total -0.48 = 0.30 + -0.64 + -0.14 + 0.04 + -0.04. Named "
                    "column re-pack (abort_s=780) is not netted into task_progress.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "niobium-pentachloride-chlorinator",
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
                    "13 min column re-pack.",
                    1,
                ),
            ),
        ]
    )


def record_322():
    ticks = [
        tick(2180, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(5510, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(5694, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(6040, -0.08, -0.10, -0.06, -0.03, 0.02),
        tick(6420, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(540000000, -0.02, -0.02, -0.02, -0.01, 0.00),
    ]
    spikes = [
        spike("enc.cycle.ctx", 1.020, 0.42),
        spike("tt.high.C", 2.180, 0.57),
        spike("tt.low.C", 3.120, 0.88),
        spike("tt.high.C", 5.510, 1.29),
        spike("tt.low.C", 5.694, 1.10),
        spike("ctrl.gate", 6.040, 0.96),
        spike("fv.quench.wall", 6.420, 1.18),
        spike("tt.high.C", 7.850, 0.80),
        spike("tt.low.C", 10.180, 0.63),
        spike("ctrl.gate", 13.400, 0.84),
        spike("enc.cycle.ctx", 18.200, 0.41),
        spike("tt.high.C", 22.000, 0.54),
        spike("fv.quench.wall", 26.200, 0.38),
    ]
    excerpt = independent_excerpt(613212, 96, 28000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Sulfur hexafluoride reactor R-3 at Fluorspar-Beck FB-7 still prints live "
                "bed-center TT-11A 248.0 C against a 220.0 C F2-conversion cap, with wall TT-11B "
                "at 186.4 C on the same vessel. High-select should bind TT-11A and MODIFY-cut F2 "
                "18.0 -> 9.4 kg/h; a weak supervisor binds the currently-losing low-select "
                "transmitter and MODIFY-closes wall-quench Q-11B 42 -> 12 percent while F2 stays 18.0.",
            ),
            ("domain", "sulfur-hexafluoride-reactor"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Cut F2 on the high-select (winning) transmitter until live bed-center stays "
                "<= 220.0 C; do not spend the cut on the currently-losing low-select wall loop.",
            ),
            ("t0_us", 1756850400000322),
            ("gate_latency_us", 540),
            ("race_window_us", 360),
            ("race_window_rel_ms", [5.4, 5.76]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "tt.high.C 248.0 C on bed-center TT-11A",
                                "tt.low.C 186.4 C on wall TT-11B losing transmitter",
                            ],
                        ),
                        (
                            "semantics",
                            "High-select-first should latch an F2 cut 18.0 -> 9.4 kg/h; "
                            "low-select-first is a false 'wall still hot' bind that closes only "
                            "the losing quench loop.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one high-select TT sample versus the low-select wall "
                            "publisher on this SF6 PLC bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 184 us vs combined jitter 60 us (high 28 + low 32). Order is "
                            "correctly high-select-first. The error is which selector leg the "
                            "MODIFY binds, not the race order.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "bed-center TT-11A, 4 Hz packet, 28 us jitter on this sample",
                    "wall TT-11B, 32 us jitter",
                    "F2 mass-flow FT (context)",
                    "wall-quench Q-11B stem (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("cap_C", 220.0),
                        ("live_high_C", 248.0),
                        ("live_low_C", 186.4),
                        ("f2_kg_h", 18.0),
                        ("quench_wall_pct", 42.0),
                        ("selector_should_be", "high"),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. R-3 in working fluorination; F2 18.0 kg/h; wall quench 42 percent armed.",
                    "2. TT-11A 248.0 > 220.0 cap; TT-11B 186.4 is the losing transmitter.",
                    "3. Low-select sampled at 3.120 ms.",
                    "4. Race window [5.400, 5.760] ms.",
                    "5. tt.high.C 248.0 C at 5.510 ms (winner).",
                    "6. tt.low.C 186.4 C at 5.694 ms (loser by 184 us).",
                    "7. Gate at 6.040 ms: WRONG MODIFY wall quench 42 -> 12 percent; F2 stays 18.0.",
                    "8. selector_leg=low; f2_kg_h unchanged 18.0; bed stays 246.2 > 220.0.",
                    "9. Conversion remains over-temperature for the rest of the pass.",
                    "10. Delayed (abort_s=540): 9 min off-spec SF6 cycle window.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_f2_feed"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("f2_kg_h", 18.0),
                        ("quench_wall_pct", 42.0),
                        ("selector_leg", "none"),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_high_C", 248.0),
                        ("cap_C", 220.0),
                        ("live_low_C", 186.4),
                        ("selected_leg", "high"),
                        ("f2_kg_h", 18.0),
                        ("quench_wall_pct", 42.0),
                        ("live_over_cap", True),
                        ("race_margin_us", 184),
                        ("combined_jitter_us", 60),
                        ("abort_s", 540),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes keeping 18.0 kg/h F2 because 248.0 C is treated as a wall-TC "
                "smear rather than a bed-center miss. Live high-select 248.0 is over the 220.0 "
                "cap; the correct gate cuts F2 on the winning transmitter.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Live high-select 248.0 C is over the 220.0 C cap, so a cut is required. A weak "
                "supervisor binds the currently-losing low-select TT-11B that lost the race and "
                "MODIFY-closes wall-quench Q-11B 42 -> 12 percent, leaving F2 at 18.0 kg/h. The "
                "wall loop is not the conversion driver. The MODIFY is plausible to a supervisor "
                "that treats high/low select as 'whichever tag last moved'.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "bed_C",
                            OrderedDict(
                                [
                                    ("cap", 220.0),
                                    ("live_high", 248.0),
                                    ("executed_f2_kg_h", 18.0),
                                    ("executed_quench_wall_pct", 12.0),
                                ]
                            ),
                        ),
                        (
                            "selector",
                            OrderedDict(
                                [
                                    ("leg_bound", "low"),
                                    ("selected_C", 186.4),
                                    ("f2_unchanged", True),
                                    ("t_gate_us", 6040),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 184),
                                    ("combined_jitter_us", 60),
                                    ("ratio", 3.07),
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
            ("name", "wall_quench_trim"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("f2_kg_h", 18.0),
                        ("quench_wall_pct", 12.0),
                        ("selector_leg", "low"),
                        ("selected_C", 186.4),
                    ]
                ),
            ),
            (
                "gate_effect",
                "WRONG MODIFY: wall quench 42 -> 12 percent; F2 left at 18.0 kg/h. Live "
                "high-select 248.0 remains over 220.0. selector_leg=low.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-modify / selector-wrong-leg. Live bed-center 248.0 stayed over the "
                "220.0 cap. The supervisor closed only the losing wall quench to 12 percent "
                "and left F2 at 18.0 kg/h. Nine minutes of off-spec SF6 cycle (abort_s=540).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("wall_quench", "trimmed; 12 percent vs filed 42"),
                        ("f2_feed", "unchanged; 18.0 kg/h still driving conversion"),
                        ("live_high_C", "246.2 C still over 220.0"),
                        ("mission", "FB-7 working pass over-temperature"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "High-select winning a 184 us race did not prevent a low-select MODIFY; reversing order would still have been a wrong bind if the supervisor keyed on the losing transmitter.",
                    "Delayed (abort_s=540): 9 min off-spec SF6 cycle window. Named un-netted loss.",
                ],
            ),
            (
                "recovery",
                "MODIFY; cut F2 18.0 -> 9.4 kg/h on the high-select (TT-11A); leave wall quench "
                "at 42 percent; bind live high-select; do not spend a conversion cut on the "
                "currently-losing low-select wall loop.",
            ),
            (
                "cost",
                OrderedDict(
                    [
                        ("actual_live_high_C", 248.0),
                        ("actual_cap_C", 220.0),
                        (
                            "wrong_edit_applied",
                            OrderedDict(
                                [
                                    ("f2_kg_h", 18.0),
                                    ("quench_wall_pct", 12.0),
                                    ("selector_leg", "low"),
                                ]
                            ),
                        ),
                        (
                            "cost",
                            "9 min off-spec SF6 cycle (task/efficiency); legal F2 cut was skipped "
                            "so live 248.0 stayed over 220.0 (safety of a false wall trim).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "tt.high.C (5.510 ms, 248.0 C)"),
                        ("loser", "tt.low.C (5.694 ms, 186.4 C)"),
                        ("margin_us", 184),
                        (
                            "counterfactual_if_reversed",
                            "Low-select-first by < 184 us would still leave live 248.0 over cap; a "
                            "correct gate binds tt.high.C to policy_f2_cut either way. The "
                            "wrong MODIFY spent the live win on a wall-quench clamp.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6040),
            (
                "reward_inflection_note",
                "Task, safety, and efficiency drop at the wrong MODIFY (6.040 ms, tick 4). "
                "The 9 min SF6 miss is delayed surprise, not the inflection.",
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
            "thalamic-relay.sf6-tt",
            "spikenaut.policy.wall-quench",
            [
                ("relay_tt_low", "policy_wall_quench", 0.74),
                ("relay_tt_high", "policy_wall_quench", 0.21),
            ],
            "acetylcholine",
            0.08,
            "sf6_selector_stdp; ACh tags the (wrong) wall_quench bind at the high-select win",
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
                    pop("wall_quench", 42, 0.45, 280.0, 4),
                    pop("f2_cut", 42, 0.90),
                    pop("high_veto", 20, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r61-322"),
            (
                "title",
                "WRONG-MODIFY at Fluorspar-Beck FB-7 / Reactor R-3: live high-select 248.0 C over "
                "cap; cut spent on losing low-select wall quench (selector-wrong-leg)",
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
                    "Wrong-modify / selector-wrong-leg. Sidecar arithmetic live_high 248.0 > 220.0 "
                    "is true and f2_kg_h stays 18.0; MODIFY bound the losing low-select. "
                    "total -0.68 = -0.22 + -0.24 + -0.18 + -0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "sulfur-hexafluoride-reactor",
                    [
                        "modify",
                        "wrong-gate",
                        "selector-wrong-leg",
                        "losing-transmitter-bound",
                        "sidecar-convictable",
                        "designed",
                    ],
                    "Teaches a probe that a correct high-select-first race can still be a wrong "
                    "gate when routing.table[0].to is policy_wall_quench and f2_kg_h is unchanged. "
                    "Convictable from live_high_C vs cap_C without SF6 fluorine kinetics.",
                    2,
                    supervisor_error_type="wrong-modify",
                ),
            ),
        ]
    )
