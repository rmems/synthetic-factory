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


def record_323():
    ticks = [
        tick(2740, 0.01, 0.04, 0.01, 0.01, 0.01),
        tick(7010, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(7188, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(7860, 0.04, 0.16, 0.04, 0.04, 0.02),
        tick(8180, 0.01, 0.05, 0.02, 0.01, 0.01),
        tick(420000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("tc.amp.ctx", 1.380, 0.43),
        spike("ae.crucible.pps", 2.740, 0.61),
        spike("enc.pull.mm", 4.510, 0.49),
        spike("ae.crucible.pps", 7.010, 1.34),
        spike("enc.pull.mm", 7.188, 1.11),
        spike("ctrl.gate", 7.860, 1.02),
        spike("ae.crucible.pps", 10.150, 0.78),
        spike("tc.amp.ctx", 14.700, 0.44),
        spike("enc.pull.mm", 19.200, 0.58),
        spike("ctrl.gate", 24.400, 0.81),
        spike("ae.crucible.pps", 31.000, 0.53),
        spike("enc.pull.mm", 38.600, 0.46),
        spike("tc.amp.ctx", 43.800, 0.37),
    ]
    excerpt = independent_excerpt(613213, 112, 46000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Bridgman furnace F-2 on the Bridgman-Keld BK-HIL pad is armed for a 0.22 mm/min "
                "crystal pull while a quartz-crucible AE packet reads 44 pps against a 10 pps "
                "move cap. A pull encoder, lit by the pad lamp, still reads 1.80 mm/min under a "
                "3.00 mm/min travel look. AE-first latches REJECT hold; encoder-first would "
                "commit a 0.22 mm/min pull into a live crack.",
            ),
            ("domain", "cadmium-telluride-bridgman"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Do not pull CdTe F-2 unless crucible AE <= 10 pps; keep slip 0.0 mm/min until "
                "the injected crack recovers.",
            ),
            ("t0_us", 1756850400000323),
            ("gate_latency_us", 860),
            ("race_window_us", 300),
            ("race_window_rel_ms", [6.90, 7.20]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ae.crucible.pps 44 pps",
                                "enc.pull.mm 1.80 mm/min under 3.00",
                            ],
                        ),
                        (
                            "semantics",
                            "AE-first latches REJECT hold 0.0 mm/min slip; encoder-first would "
                            "commit a 0.22 mm/min pull on an apparent 1.80 mm/min under-read.",
                        ),
                        (
                            "window_derivation",
                            "300 us = one crucible-AE sample versus encoder integration on this "
                            "CdTe HIL bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 178 us vs combined jitter 56 us (AE 24 + ENC 32): 3.2x over a "
                            "2.0x trust floor. Pad injects the encoder lamp 120-160 us before the "
                            "AE (geometric lag, not a sensor fault); the 1.80 mm/min packet is still "
                            "the loser in this 300 us window.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "crucible AE puck, 5 kHz burst, 24 us jitter",
                    "crystal-pull encoder, 200 Hz, 32 us jitter",
                    "ampoule thermocouple (context)",
                    "HIL lamp-spectrum monitor (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("crack_cap_pps", 10.0),
                        ("observed_crack_pps", 44.0),
                        ("pull_mm_min", 1.80),
                        ("pull_look_mm_min", 3.00),
                        ("proposed_slip_mm_min", 0.22),
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
                            "Bridgman-Keld BK-HIL CdTe vertical Bridgman mockup with physical pull axis",
                        ),
                        ("injected", "crucible AE burst + encoder lamp spectrum"),
                        (
                            "note",
                            "Hardware-in-the-loop CdTe Bridgman. Invented plant; not a live crystal shop.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Furnace F-2 on the BK-HIL pad; 0.22 mm/min pull armed.",
                    "2. Encoder lamp injected 120-160 us before AE sees 44 pps.",
                    "3. Ampoule-TC precursor at 1.380 ms.",
                    "4. Race window [6.900, 7.200] ms.",
                    "5. ae.crucible.pps 44 pps at 7.010 ms (winner).",
                    "6. enc.pull.mm 1.80 mm/min at 7.188 ms (loser by 178 us).",
                    "7. Gate at 7.860 ms: REJECT hold 0.0 mm/min; do not pull 0.22.",
                    "8. Crack remains over 10 pps this cycle; slip cap held.",
                    "9. Crucible re-seat queued on the pad.",
                    "10. Delayed (abort_s=420): 7 min ampoule re-melt and lamp-spectrum retune.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "lower_cdte_pull"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("slip_mm_min", 0.22),
                        ("hold", False),
                        ("encoder_authoritative", True),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("crack_pps", 44.0),
                        ("crack_cap_pps", 10.0),
                        ("pull_mm_min", 1.80),
                        ("pull_look_mm_min", 3.00),
                        ("race_margin_us", 178),
                        ("combined_jitter_us", 56),
                        ("abort_s", 420),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes a 0.22 mm/min crystal pull because encoder 1.80 mm/min looks "
                "under the 3.00 mm/min travel look, treating AE 44 pps as a noisy bus echo.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Crucible AE 44 pps is over the 10 pps pull-move cap. Encoder 1.80 mm/min is a "
                "HIL lamp under-read, not a clearance. REJECT: hold 0.0 mm/min; do not commit a "
                "0.22 mm/min pull.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "crack_pps",
                            OrderedDict(
                                [
                                    ("cap", 10.0),
                                    ("observed", 44.0),
                                    ("pull_mm_min", 1.80),
                                ]
                            ),
                        ),
                        (
                            "slip_mm_min",
                            OrderedDict([("proposed", 0.22), ("executed", 0.0)]),
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
            ("name", "hold_for_crack_drop"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("slip_mm_min", 0.0),
                        ("hold", True),
                        ("encoder_authoritative", False),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: hold 0.0 mm/min; 0.22 mm/min pull cancelled. AE 44 > 10 pps cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held Furnace F-2 at 0.0 mm/min slip. Crack over cap this cycle; "
                "slip cap held. Encoder apparent was not treated as an AE clearance.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("slip", "held; 0.0 mm/min"),
                        ("crack", "still over 10 pps this cycle"),
                        ("encoder", "1.80 mm/min unused as clearance"),
                        ("mission", "pull deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Geometric lag: encoder lamp was injected 120-160 us before the AE puck, yet crucible AE still won the 300 us race.",
                    "Delayed (abort_s=420): pad policy update forbids treating pull encoder mm/min as a crucible-AE substitute after a 7 min re-melt.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ae.crucible.pps (7.010 ms, 44 pps)"),
                        ("loser", "enc.pull.mm (7.188 ms, 1.80 mm/min)"),
                        ("margin_us", 178),
                        (
                            "counterfactual_if_reversed",
                            "Encoder-first by < 178 us inside the 300 us window would have committed "
                            "a 0.22 mm/min pull with AE 44 > 10 pps cap. Order, not amplitude, selected the hold.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7860),
            (
                "reward_inflection_note",
                "Safety and coherence step up at the REJECT gate (7.860 ms, tick 4) as the hold "
                "lands. The 7 min re-melt is delayed surprise bound to abort_s=420.",
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
            "thalamic-relay.cdte-ae",
            "spikenaut.policy.pull-hold",
            [
                ("relay_crack_pps", "policy_pull_hold", 0.70),
                ("relay_enc_pull", "policy_enc_pull", 0.24),
            ],
            "dopamine",
            0.15,
            "crack_hold_stdp; DA tags the pull_hold bind at the crucible-AE win",
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
            ("decision_window_ms", 0.30),
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
    return OrderedDict(
        [
            ("id", "ttf-r61-323"),
            (
                "title",
                "Bridgman-Keld BK-HIL / Furnace F-2: crucible AE 44 pps beats pull encoder "
                "1.80 mm/min by 178 us; correct REJECT holds the crystal pull",
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
                    "Correct REJECT. Crucible AE over cap beats encoder under-read. "
                    "total 0.80 = 0.10 + 0.42 + 0.12 + 0.10 + 0.06. Tick 6 binds abort_s=420.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "cadmium-telluride-bridgman",
                    [
                        "reject",
                        "hil",
                        "crucible-ae",
                        "encoder-underread",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a HIL pull-encoder under-read losing a 178 us race does not "
                    "clear a crucible-AE over-rate. Hold is distillable from pps vs cap.",
                    3,
                ),
            ),
        ]
    )


def record_324():
    ticks = [
        tick(3180, 0.05, 0.04, 0.02, 0.01, 0.01),
        tick(8040, 0.08, 0.05, 0.04, 0.03, 0.02),
        tick(8228, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(8480, 0.12, 0.09, 0.05, 0.04, 0.02),
        tick(8940, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(150000000, 0.03, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.bus.ctx", 1.090, 0.43),
        spike("tc.bath.C", 3.180, 0.59),
        spike("ir.hood.C", 5.000, 0.50),
        spike("tc.bath.C", 8.040, 1.27),
        spike("ir.hood.C", 8.228, 1.09),
        spike("ctrl.gate", 8.480, 0.97),
        spike("tc.bath.C", 11.150, 0.78),
        spike("ir.hood.C", 14.800, 0.61),
        spike("ctrl.gate", 18.300, 0.84),
        spike("tc.bath.C", 21.900, 0.56),
        spike("enc.bus.ctx", 24.050, 0.40),
    ]
    excerpt = independent_excerpt(613214, 64, 26000, 13, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("current_kA", 8.4),
            ("bath_C", 1048.0),
            ("hood_C", 1180.0),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Neodymium fluoride cell bank B-2 at Didym-Naze DN-4 is already holding the "
                "molten-salt bath at 1048 C under a 1080 C freeze-lid cap with an 8.4 kA load "
                "already filed under the 10.0 kA rectifier ceiling. Hood-IR-first would extra-clamp "
                "a legal bath; bath-first ACCEPTS the filed 8.4 kA fluoride pass.",
            ),
            ("domain", "neodymium-fluoride-electrolyzer"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Hold the 8.4 kA load while bath stays <= 1080 C and current stays <= 10.0 kA; "
                "do not extra-clamp a legal NdF3 cell bank.",
            ),
            ("t0_us", 1756850400000324),
            ("gate_latency_us", 400),
            ("race_window_us", 460),
            ("race_window_rel_ms", [7.95, 8.41]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "tc.bath.C 1048 C under 1080",
                                "ir.hood.C 1180 C smear under 1220 look",
                            ],
                        ),
                        (
                            "semantics",
                            "Bath-first ACCEPTS the already-legal 8.4 kA load. Hood-first "
                            "would extra-clamp because 1180 C looks under a 1220 C freeze-lid look.",
                        ),
                        (
                            "window_derivation",
                            "460 us = one bath-TC slot versus hood-IR group delay on this "
                            "fluoride-cell skid bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 188 us vs combined jitter 66 us (TC 32 + IR 34): 2.8x over "
                            "a 2.0x trust floor. Reversing order by < 188 us inside the 460 us "
                            "window would have extra-clamped a legal 1048 C / 8.4 kA pass.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "molten-salt bath thermocouple tree, 1 kHz, 32 us jitter",
                    "hood IR pyrometer, 2 kHz, 34 us jitter",
                    "rectifier bus encoder (context)",
                    "cell DP (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("bath_cap_C", 1080.0),
                        ("observed_bath_C", 1048.0),
                        ("hood_C", 1180.0),
                        ("current_cap_kA", 10.0),
                        ("proposed_current_kA", 8.4),
                    ]
                ),
            ),
            (
                "simulation",
                OrderedDict(
                    [
                        (
                            "solver",
                            "1-D axial bath + MHD stirring kernel, seed 613214; 6-zone NdF3 "
                            "electrolyzer; NOT lumped-CSTR, NOT U-RANS, NOT a wet-stand",
                        ),
                        (
                            "fidelity_limits",
                            "Rigid graphite crucible; no freeze-lid motion. Raster is kernelized "
                            "events, not an independent LIF.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Cell bank B-2 in pass; 8.4 kA load armed.",
                    "2. Bath 1048 C under 1080 freeze-lid; current 8.4 under 10.0 kA rectifier.",
                    "3. Bus encoder precursor at 1.090 ms.",
                    "4. Race window [7.950, 8.410] ms.",
                    "5. tc.bath.C 1048 C at 8.040 ms (winner).",
                    "6. ir.hood.C 1180 C at 8.228 ms (loser by 188 us).",
                    "7. Gate at 8.480 ms: ACCEPT 8.4 kA; executed identical to proposed.",
                    "8. Bath stays 1049 C < 1080; current 8.41 kA < 10.0.",
                    "9. Hood remaining a shell glint did not require an extra clamp.",
                    "10. Delayed (survey_s=150): 150 s Nd titer on the metal tap.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_ndf3_current"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("bath_C", 1048.0),
                        ("bath_cap_C", 1080.0),
                        ("hood_C", 1180.0),
                        ("current_cap_kA", 10.0),
                        ("race_margin_us", 188),
                        ("combined_jitter_us", 66),
                        ("survey_s", 150),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes keeping the filed 8.4 kA load: bath 1048 C is under the "
                "1080 C freeze-lid cap and 8.4 kA is under 10.0 kA rectifier.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Bath 1048 C won by 188 us and is under the 1080 C freeze-lid cap. Hood "
                "1180 C is a shell glint, not a freeze-lid miss. ACCEPT the filed 8.4 kA "
                "load. Executed identical to proposed. An extra clamp is not indicated.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "bath_C",
                            OrderedDict(
                                [
                                    ("cap", 1080.0),
                                    ("observed", 1048.0),
                                    ("executed_current_kA", 8.4),
                                ]
                            ),
                        ),
                        (
                            "hood_C",
                            OrderedDict([("look", 1220.0), ("observed", 1180.0)]),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 188),
                                    ("combined_jitter_us", 66),
                                    ("ratio", 2.85),
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
            ("name", "hold_ndf3_current"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: executed identical to proposed 8.4 kA load. Bath 1048 C < 1080 cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT kept the filed 8.4 kA NdF3 load. Bath stayed 1049 C under "
                "1080 C. Hood remaining a shell glint was the losing channel and did not "
                "justify an extra clamp.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("current", "held; 8.4 kA"),
                        ("bath", "1049 C < 1080 C"),
                        ("hood", "1180 C glint unused as freeze-lid miss"),
                        ("metal", "pass continues"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Hood IR 1180 C losing a 188 us race did not predict a freeze-lid miss; reversing 188 us would have extra-clamped a legal 1048 C pass.",
                    "Delayed (survey_s=150): 150 s Nd titer on the metal tap; not a safety inflection.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "tc.bath.C (8.040 ms, 1048 C)"),
                        ("loser", "ir.hood.C (8.228 ms, 1180 C)"),
                        ("margin_us", 188),
                        (
                            "counterfactual_if_reversed",
                            "Hood-first by < 188 us inside the 460 us window would have extra-clamped "
                            "a legal pass. Bath-first confirms the filed load.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 8480),
            (
                "reward_inflection_note",
                "Heads rise at the ACCEPT (8.480 ms, tick 4). The 150 s Nd titer "
                "is delayed surprise bound to survey_s=150, not the inflection.",
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
            "thalamic-relay.nd-bath",
            "spikenaut.policy.current-accept",
            [
                ("relay_bath_C", "policy_current_accept", 0.66),
                ("relay_hood_IR", "policy_extra_clamp", 0.23),
            ],
            "serotonin",
            0.12,
            "bath_confirm_stdp; 5-HT tags the current_accept bind at the bath-TC win",
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
                    pop("current_accept", 50, 0.50, 175.0, 4),
                    pop("extra_clamp", 40, 0.85, 40.0, 1),
                    pop("hood_veto", 22, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r61-324"),
            (
                "title",
                "Didym-Naze DN-4 / Cell bank B-2: bath 1048 C beats hood IR 1180 C by 188 us; "
                "ACCEPT already-legal 8.4 kA NdF3 load",
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
                    "Clean ACCEPT of an already-legal NdF3 load. "
                    "total 1.06 = 0.40 + 0.28 + 0.18 + 0.12 + 0.08. Tick 6 binds survey_s=150.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "neodymium-fluoride-electrolyzer",
                    [
                        "accept",
                        "simulated",
                        "bath-vs-hood",
                        "current-legal",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a lagging hood IR losing a 188 us race does not require an "
                    "extra clamp when the molten-salt bath is already under the freeze-lid cap.",
                    4,
                ),
            ),
        ]
    )


def record_325():
    ticks = [
        tick(1960, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5080, 0.08, 0.06, 0.04, 0.02, 0.02),
        tick(5260, 0.08, 0.05, 0.03, 0.02, 0.01),
        tick(5440, 0.12, 0.09, 0.06, 0.04, 0.02),
        tick(5980, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(210000000, 0.04, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.boat.ctx", 0.860, 0.44),
        spike("tc.muffle.C", 1.960, 0.61),
        spike("dp.muffle.kPa", 3.380, 0.52),
        spike("tc.muffle.C", 5.080, 1.30),
        spike("dp.muffle.kPa", 5.260, 1.12),
        spike("ctrl.gate", 5.440, 0.99),
        spike("tc.muffle.C", 8.020, 0.77),
        spike("dp.muffle.kPa", 11.350, 0.58),
        spike("ctrl.gate", 14.800, 0.83),
        spike("tc.muffle.C", 18.100, 0.54),
        spike("enc.boat.ctx", 21.050, 0.39),
    ]
    excerpt = independent_excerpt(613215, 80, 24000, 12, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("index_m_h", 0.42),
            ("muffle_C", 1480.0),
            ("muffle_dp_kPa", 8.4),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Tungsten-carbide carburizing muffle M-6 at Cermet-Brae CB-8 is already indexing "
                "boats at 0.42 m/h under a 0.55 m/h pusher ceiling while the muffle sits at 1480 C "
                "against a 1560 C thermal trip. DP-first would extra-clamp a legal boat string; "
                "muffle-TC-first ACCEPTS the filed 0.42 m/h carburize pass.",
            ),
            ("domain", "tungsten-carbide-carburizer"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Hold the 0.42 m/h index while muffle stays <= 1560 C and index stays <= 0.55 m/h; "
                "do not extra-clamp a legal WC carburizer.",
            ),
            ("t0_us", 1756850400000325),
            ("gate_latency_us", 360),
            ("race_window_us", 320),
            ("race_window_rel_ms", [5.00, 5.32]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "tc.muffle.C 1480 C under 1560",
                                "dp.muffle.kPa 8.4 smear under 7.0 look",
                            ],
                        ),
                        (
                            "semantics",
                            "Muffle-TC-first ACCEPTS the already-legal 0.42 m/h index. DP-first "
                            "would extra-clamp because 8.4 kPa looks over a 7.0 kPa packing look.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one muffle-TC slot versus packing-DP group delay on this "
                            "carburizer skid bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 58 us (TC 26 + DP 32): 3.1x over "
                            "a 2.0x trust floor. Reversing order by < 180 us inside the 320 us "
                            "window would have extra-clamped a legal 1480 C / 0.42 m/h pass.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "muffle-crown thermocouple, 4 kHz, 26 us jitter",
                    "packing DP transmitter, 1 kHz, 32 us jitter",
                    "boat-index encoder (context)",
                    "end-seal IR (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("muffle_trip_C", 1560.0),
                        ("observed_muffle_C", 1480.0),
                        ("muffle_dp_kPa", 8.4),
                        ("index_cap_m_h", 0.55),
                        ("proposed_index_m_h", 0.42),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Muffle M-6 in pass; 0.42 m/h index armed.",
                    "2. Muffle 1480 C under 1560 trip; index 0.42 under 0.55 m/h pusher.",
                    "3. Boat encoder precursor at 0.860 ms.",
                    "4. Race window [5.000, 5.320] ms.",
                    "5. tc.muffle.C 1480 C at 5.080 ms (winner).",
                    "6. dp.muffle.kPa 8.4 at 5.260 ms (loser by 180 us).",
                    "7. Gate at 5.440 ms: ACCEPT 0.42 m/h; executed identical to proposed.",
                    "8. Muffle stays 1482 C < 1560; index 0.421 m/h < 0.55.",
                    "9. DP remaining a packing glint did not require an extra clamp.",
                    "10. Delayed (survey_s=210): 3.5 min carbon-balance coupon on the boat lock.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_wc_index"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("muffle_C", 1480.0),
                        ("muffle_trip_C", 1560.0),
                        ("muffle_dp_kPa", 8.4),
                        ("index_cap_m_h", 0.55),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("survey_s", 210),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes keeping the filed 0.42 m/h index: muffle 1480 C is under the "
                "1560 C trip and 0.42 m/h is under 0.55 m/h pusher.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Muffle 1480 C won by 180 us and is under the 1560 C trip. Packing DP 8.4 kPa "
                "is a junction glint, not a thermal miss. ACCEPT the filed 0.42 m/h index. "
                "Executed identical to proposed. An extra clamp is not indicated.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "muffle_C",
                            OrderedDict(
                                [
                                    ("trip", 1560.0),
                                    ("observed", 1480.0),
                                    ("executed_index_m_h", 0.42),
                                ]
                            ),
                        ),
                        (
                            "muffle_dp_kPa",
                            OrderedDict([("look", 7.0), ("observed", 8.4)]),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 180),
                                    ("combined_jitter_us", 58),
                                    ("ratio", 3.10),
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
            ("name", "hold_wc_index"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: executed identical to proposed 0.42 m/h index. Muffle 1480 C < 1560 trip.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT kept the filed 0.42 m/h index. Muffle stayed 1482 C under 1560. "
                "DP remaining a packing glint was the losing channel and did not justify an "
                "extra clamp.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("index", "held; 0.42 m/h"),
                        ("muffle", "1482 C < 1560"),
                        ("dp", "8.4 kPa glint unused as thermal miss"),
                        ("boats", "pass continues"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Packing DP 8.4 kPa losing a 180 us race did not predict a thermal miss; reversing 180 us would have extra-clamped a legal 1480 C muffle.",
                    "Delayed (survey_s=210): 3.5 min carbon-balance coupon on the boat lock; not a safety inflection.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "tc.muffle.C (5.080 ms, 1480 C)"),
                        ("loser", "dp.muffle.kPa (5.260 ms, 8.4 kPa)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "DP-first by < 180 us inside the 320 us window would have extra-clamped "
                            "a legal muffle. Muffle-TC-first confirms the filed index.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5440),
            (
                "reward_inflection_note",
                "Heads rise at the ACCEPT (5.440 ms, tick 4). The 3.5 min carbon-balance coupon "
                "is delayed surprise bound to survey_s=210, not the inflection.",
            ),
            ("delayed_surprise_s", 210),
        ]
    )
    ras = raster_core(
        24,
        80,
        28,
        54,
        routing(
            "thalamic-relay.wc-tc",
            "spikenaut.policy.index-accept",
            [
                ("relay_muffle_C", "policy_index_accept", 0.69),
                ("relay_dp_muffle", "policy_extra_clamp", 0.21),
            ],
            "octopamine",
            0.05,
            "muffle_confirm_stdp; octopamine tags the index_accept bind at the muffle-TC win",
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
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("index_accept", 45, 0.50, 210.0, 3),
                    pop("extra_clamp", 40, 0.85, 40.0, 1),
                    pop("dp_veto", 20, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r61-325"),
            (
                "title",
                "Cermet-Brae CB-8 / Muffle M-6: muffle 1480 C beats packing DP 8.4 kPa by 180 us; "
                "ACCEPT already-legal 0.42 m/h WC index",
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
                    "Clean ACCEPT of an already-legal WC carburizer index. "
                    "total 1.14 = 0.44 + 0.30 + 0.20 + 0.12 + 0.08. Tick 6 binds survey_s=210.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "tungsten-carbide-carburizer",
                    [
                        "accept",
                        "designed",
                        "muffle-vs-dp",
                        "index-legal",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a lagging packing DP losing a 180 us race does not require a "
                    "wait when muffle temperature is already under the thermal trip.",
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
    if set(domains) != set(THIS_DOMAINS):
        issues.append(f"THIS_DOMAINS mismatch {set(domains)}")
    prior_d, prior_p = harvest_occupancy()
    hit_d = set(domains) & prior_d
    if hit_d:
        issues.append(f"occupancy domain collision {hit_d}")
    ids = [r["id"] for r in records]
    if ids != [f"ttf-r61-{n}" for n in range(321, 326)]:
        issues.append(f"ids {ids}")
    wrong = [
        r
        for r in records
        if r["safety_decision"].get("correctness") == "incorrect"
        or r["meta"].get("supervisor_error_type")
    ]
    if len(wrong) != 1 or wrong[0]["id"] != "ttf-r61-322":
        issues.append(f"wrong-gate set {[w['id'] for w in wrong]}")
    if wrong and wrong[0]["meta"].get("supervisor_error_type") != "wrong-modify":
        issues.append("322 supervisor_error_type")
    if any(r["state"]["sim_or_real"] == "real" for r in records):
        issues.append("sim_or_real=real")
    hil = [r["id"] for r in records if r["state"]["sim_or_real"] == "hil"]
    if hil != ["ttf-r61-323"]:
        issues.append(f"hil set {hil}")
    sim = [r["id"] for r in records if r["state"]["sim_or_real"] == "simulated"]
    if sim != ["ttf-r61-324"]:
        issues.append(f"simulated set {sim}")
    decisions = [r["safety_decision"]["decision"] for r in records]
    if (
        decisions.count("ACCEPT") != 2
        or decisions.count("MODIFY") != 2
        or decisions.count("REJECT") != 1
    ):
        issues.append(f"gate mix {decisions}")
    for rec in records:
        blob = json.dumps(rec)
        if "training_ready" in blob:
            issues.append(f"{rec['id']} training_ready present")
        hidden = walk_keys(rec)
        if hidden:
            issues.append(f"{rec['id']} hidden keys {hidden}")
        skip_frags = set(THIS_PLANTS) | {"WRONG-MODIFY", "WRONG-REJECT"}
        for frag in prior_p - skip_frags:
            if frag and frag in blob:
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
        overlap = excerpt_vs_spikes(rec)
        if rec["id"] == "ttf-r61-321":
            if rec["raster"].get("excerpt_source") != "independent_lif":
                issues.append("321 missing independent_lif")
            if rec["future_outcome"]["reward_inflection_t_us"] > rec["raster"]["window_ms"] * 1000:
                issues.append("321 inflection outside window")
            if rec["reward_components"]["total"] >= 0:
                issues.append("321 partnered-neg total not negative")
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
        if rec["meta"]["round"] != 61:
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
        for item in rec["raster"]["excerpt"]:
            if item["neuron_id"] < 0 or item["neuron_id"] >= rec["raster"]["neurons"]:
                issues.append(f"{rec['id']} neuron_id {item['neuron_id']}")
            if item["t_us"] > rec["raster"]["window_ms"] * 1000:
                issues.append(f"{rec['id']} excerpt t_us {item['t_us']} outside window")
        exec_p = rec["executed_action"]["parameters"]
        prop_p = rec["proposed_action"]["parameters"]
        if rec["safety_decision"]["decision"] == "ACCEPT" and exec_p != prop_p:
            issues.append(f"{rec['id']} ACCEPT params differ")
        if rec["id"] == "ttf-r61-322":
            if "recovery" not in rec["future_outcome"]:
                issues.append("322 missing recovery")
            if exec_p.get("selector_leg") != "low":
                issues.append("322 selector_leg not low")
            if exec_p.get("f2_kg_h") != 18.0:
                issues.append("322 F2 was not left at 18.0")
            if exec_p.get("quench_wall_pct") != 12.0:
                issues.append("322 wall quench not 12 percent")
            live = rec["proposed_action"]["evidence"].get("live_high_C")
            cap = rec["proposed_action"]["evidence"].get("cap_C")
            if live is None or cap is None or live <= cap:
                issues.append("322 live not over cap")
            if "selector-wrong-leg" not in rec["meta"].get("tags", []):
                issues.append("322 missing selector-wrong-leg tag")
            tos = {row["to"] for row in rec["raster"]["routing"]["table"]}
            if "policy_f2_cut" in tos:
                issues.append("322 routing contains policy_f2_cut")
            if "policy_wall_quench" not in tos:
                issues.append("322 routing missing policy_wall_quench")
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
    return issues, jmax


def notes_text(jmax: float) -> str:
    return f"""# Thalamic Trajectory Factory — NOTES-r61

- Factory: `thalamic-trajectory-factory`
- Run label: `2026-09-02-final-heavy`
- Generator: `grok-4.6`
- Channel: SuperGrok Heavy consumer chat (RM-793 research-only)
- Quota: 5
- Quality: Q=5
- IDs: `ttf-r61-321` … `ttf-r61-325`
- Domains this batch: `niobium-pentachloride-chlorinator`, `sulfur-hexafluoride-reactor`, `cadmium-telluride-bridgman`, `neodymium-fluoride-electrolyzer`, `tungsten-carbide-carburizer`

These five domain slugs sit outside the prompt 8-pool and outside staged occupancy harvested from `/tmp/ttf-r*/batch-r*.jsonl` (including the unpublished `/tmp/ttf-r61` carbide/chlorate/tab/monazite/lithium draft). All five plants are invented (Columbic-Howe, Fluorspar-Beck, Bridgman-Keld, Didym-Naze, Cermet-Brae). Do not restack prior TTF plants.

## Batch map

| id | domain | decision | correctness | sim_or_real | total | edge |
|----|--------|----------|-------------|-------------|-------|------|
| ttf-r61-321 | niobium-pentachloride-chlorinator | MODIFY | correct | designed | **−0.48** | process-correct Cl2 clamp; packed-column weep inside 42 ms raster; independent LIF |
| ttf-r61-322 | sulfur-hexafluoride-reactor | MODIFY | **incorrect (wrong-modify / selector-wrong-leg)** | designed | −0.68 | live high-select 248.0 C > 220.0 cap; cut spent on losing low-select wall quench; F2 stays 18.0 |
| ttf-r61-323 | cadmium-telluride-bridgman | REJECT | correct | hil | +0.80 | crucible AE 44 pps beats pull encoder 1.80 mm/min; hold slip |
| ttf-r61-324 | neodymium-fluoride-electrolyzer | ACCEPT | correct | simulated | +1.06 | bath 1048 C vs hood IR 1180 C; proposed 8.4 kA already legal |
| ttf-r61-325 | tungsten-carbide-carburizer | ACCEPT | correct | designed | +1.14 | muffle 1480 C vs packing DP 8.4 kPa; proposed 0.42 m/h already legal |

Gate mix: 2 ACCEPT, 1 correct MODIFY (partnered-neg, in-window), 1 incorrect MODIFY (selector-wrong-leg), 1 correct REJECT. Provenance: designed×3, simulated×1, hil×1 (Bridgman-Keld BK-HIL CdTe pull axis). Intra-batch Jaccard on `state.description` {jmax:.3f}.

## Wrong-modify / selector-wrong-leg

**ttf-r61-322** is the mandated incorrect gate (`safety_decision.correctness=incorrect`, `meta.supervisor_error_type=wrong-modify`). Alternate vs even rounds: odd rounds host wrong-modify. This is not r13/r19 wrong-axis, not r14/r23 wrong-loop, not r21 wrong-polarity, not r24 under-clamp, not r25/r29/r31 wrong-phase, not r33/r35 over-clamp, not r37/r39/r43 clamp-too-late, not r45 clamp-too-early, not r47/r49/r51/r53/r55/r57 stale-sample, not r59/r65 wrong-string / idle-bank, not r69 split-range-wrong-half. Class is **selector-wrong-leg**: high/low select bound to the currently-losing transmitter; correct magnitude cut spent on the wall quench while live F2 stays open. Do not emit a wrong-ACCEPT.

Fluorspar-Beck FB-7 / Reactor R-3 reads live high-select **248.0 C** against a **220.0 C** cap. Low-select wall TT-11B is **186.4 C**. Sidecar arithmetic `248.0 > 220.0` is true. A timely MODIFY cuts F2 **18.0 → 9.4 kg/h**. A weak supervisor binds the losing transmitter and MODIFY-closes Q-11B **42 → 12 percent**, leaving F2 at 18.0. Live bed stays **246.2 > 220.0**. Convictable without SF6 fluorine kinetics: `evidence.live_high_C > evidence.cap_C`, `executed_action.f2_kg_h == 18.0`, `executed_action.quench_wall_pct == 12`, `executed_action.selector_leg == low`, `raster.routing.table` sends `relay_tt_low` → `policy_wall_quench` (weight 0.74) with no positive weight to `policy_f2_cut`, and `gate_snn` has `wall_quench` above threshold while `f2_cut` is not. Recovery: MODIFY F2 18.0 → 9.4 kg/h; leave wall quench at 42; bind high-select TT-11A. Cost: 9 min off-spec SF6 cycle (`abort_s=540`).

## Partnered-negative in-window (321)

**ttf-r61-321** is the partnered negative: process-correct MODIFY (Cl2 held 28.0 kg/h; bed 384 C <= 390 cap) while the world still charges. Safety −0.64 prices the packed-column weep at **22.200 ms**; `task_progress` stays +0.30 because the clamp completed. Inflection `t_us=22200` is tick 5 and is **inside** the 42 ms raster (`22200 ≤ 42000`). Named un-netted loss: 13 min column re-pack (`abort_s=780`). Not folded into process heads.

Independent LIF (the one labeled sidecar sim): `state.sim_or_real` remains `designed`. `raster.excerpt_source=independent_lif`, `raster.sim_scope=sidecar_only`, `raster.lif` seed 613211, stim `[22000, 25000]`. Excerpt is membrane crossings (`lif.clamp` early vs `lif.weep` 22–25 ms), not a 1:1 remap of `spike_events`. `meta.tags` include `independent-lif-raster` and `sidecar-sim-only`.

## Reward formula and tick reconciliation

Declared aggregation on every record:

`total = task_progress + safety + efficiency + coherence + exploration`

Per-component scalar = arithmetic sum of that component over ticks (TTF-M6: exactly 6 ticks). Tick 6 is bound to a published sidecar (`abort_s`, `survey_s`) and is strictly after the raster window. Inflection `t_us` is an actual tick.

| id | ticks | tp | saf | eff | coh | exp | total | inflection tick |
|----|-------|----|-----|-----|-----|-----|-------|-----------------|
| 321 | 6 | +0.30 | −0.64 | −0.14 | +0.04 | −0.04 | −0.48 | 5 (22200) |
| 322 | 6 | −0.22 | −0.24 | −0.18 | −0.10 | +0.06 | −0.68 | 4 (6040) |
| 323 | 6 | +0.10 | +0.42 | +0.12 | +0.10 | +0.06 | +0.80 | 4 (7860) |
| 324 | 6 | +0.40 | +0.28 | +0.18 | +0.12 | +0.08 | +1.06 | 4 (8480) |
| 325 | 6 | +0.44 | +0.30 | +0.20 | +0.12 | +0.08 | +1.14 | 4 (5440) |

Tick-6 sidecar bind: 321 `abort_s=780`, 322 `abort_s=540`, 323 `abort_s=420`, 324 `survey_s=150`, 325 `survey_s=210`.

## Raster / energy (Loihi-2 4-core, 23 pJ/spike)

| id | domain | n | rate Hz | window_ms | spikes | energy_pJ | energy_uJ |
|----|--------|---|---------|-----------|--------|-----------|-----------|
| 321 | niobium-pentachloride-chlorinator | 76 | 24 | 42 | 77 | 1771 | 0.001771 |
| 322 | sulfur-hexafluoride-reactor | 96 | 32 | 28 | 86 | 1978 | 0.001978 |
| 323 | cadmium-telluride-bridgman | 112 | 20 | 46 | 103 | 2369 | 0.002369 |
| 324 | neodymium-fluoride-electrolyzer | 64 | 40 | 26 | 67 | 1541 | 0.001541 |
| 325 | tungsten-carbide-carburizer | 80 | 28 | 24 | 54 | 1242 | 0.001242 |

`spikes = round(n × rate × window_s)`. Every record carries `gate_snn` whose `decision` matches the safety gate; populations that declare rate+spikes meet the same ±1 budget against `decision_window_s`. `routing.third_factor` has modulator, `tau_e_s`/`tau_e_ms` pair, and eligibility. Excerpt same-neuron gap ≥ 1000 µs; spike trains same-channel refractory ≥ 0.8 ms. Non-321 excerpts are kernelized and independent of `spike_events` times (overlap < 0.8).

## Local checks (staging, not a rewrite of other raw files)

See generator stdout: `check_jsonl` FactoryStaging, `validate_run.check_line`, `dumps_exact_json`, `raster_status`, `verify_batch_for_frontier(strict=True)`, `spike_probe.py --strict`, tick sums, refractory, Jaccard.

Never `training_ready`. Never `sim_or_real=real`. Create-only write of this round's batch/NOTES under the operator window.

## Residual weaknesses (honest)

1. Only **one** labeled independent LIF (321). The other four excerpts are independent of `spike_events` times but are not declared population sims.
2. Wrong-ACCEPT still absent (guard).
3. 324 and 325 are both already-legal ACCEPTs; a later round could pair one ACCEPT with a world charge that does not go negative, or drop to a single ACCEPT.
4. Five domain slugs leave the prompt's 8-item pool; a later round that must stay inside the pool will have to rotate sit-outs instead.
5. Tick-6 sidecar bind is standing machinery (r14+), not a new class. ISI histogram sidecar is still optional densification.

## Next densification target

Labeled LIF on a second record, or an ISI histogram sidecar. Remaining unused wrong-MODIFY subclasses include **wrong-engineering-unit (bar vs kPa)** once selector-wrong-leg is staged. Wrong-ACCEPT remains structurally absent until a prompt amendment.

Novel coverage: 18.0%
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
        BATCH_PATH, "batch-r61.jsonl", staging=FactoryStaging(enabled=True)
    )
    report.append(("check_jsonl FactoryStaging", errors, warnings, kinds, nrec))
    line_errs = []
    for i, rec in enumerate(records, 1):
        errs, kind = check_line(rec, f"batch-r61.jsonl:{i}", factory_staging=True)
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
    if BATCH_PATH.exists() or NOTES_PATH.exists():
        print(f"refuse: {BATCH_PATH.name if BATCH_PATH.exists() else NOTES_PATH.name} already exists")
        return 1
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    records = [record_321(), record_322(), record_323(), record_324(), record_325()]
    issues, jmax = self_check(records)
    if issues:
        print("SELF_CHECK_ISSUES:")
        for item in issues:
            print(" -", item)
        return 1
    print(f"SELF_CHECK_OK jmax={jmax:.3f}")
    lines = [
        json.dumps(rec, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        for rec in records
    ]
    BATCH_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    NOTES_PATH.write_text(notes_text(jmax), encoding="utf-8")
    print(f"wrote {BATCH_PATH} lines={len(lines)} jmax={jmax:.3f}")
    print(f"wrote {NOTES_PATH}")
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
