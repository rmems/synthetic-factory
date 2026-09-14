#!/usr/bin/env python3
"""Generate TTF round 72 (ttf-r72-356..360) CREATE-ONLY into the live tree."""
from __future__ import annotations

import json
import os
import random
import re
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path("/home/raulmc/rmems/synthetic-factory")
LIVE = REPO / "outputs/raw/2026-09-02-final-heavy/thalamic-trajectory-factory"
sys.path.insert(0, str(REPO / "pipelines"))

from curate_bridge import raster_status  # noqa: E402
from validate_run import (  # noqa: E402
    HIDDEN_THOUGHT_KEYS,
    check_line,
    check_thalamic,
)
from verify_execution import verify_batch_for_frontier  # noqa: E402

RIGHTS = {
    "provider": "SpaceXAI/xAI",
    "model": "grok-4.6",
    "channel": "consumer",
    "subscription_plan": "SuperGrok Heavy",
    "generation_surface": "SuperGrok Heavy chat",
    "generated_at": "2026-09-02T19:55:00Z",
    "intended_use": "research_only",
    "project_training_policy": "blocked",
    "research_retention_status": "allowed",
    "research_evaluation_status": "allowed",
    "redistribution_status": "unresolved",
    "provider_training_status": "unresolved",
    "weight_publication_status": "blocked",
    "status_basis": "RM-793 project policy: xAI hosted outputs are research-only",
    "linear_issue": "RM-793",
}

TOKEN_RE = re.compile(r"[a-z0-9]+")
PLANT_RE = re.compile(r"\b([A-Z][A-Za-z]+(?:-[A-Z][A-Za-z0-9]+)+)\b")
ROUND_N = 72
IDS = [f"ttf-r72-{n}" for n in range(356, 361)]
MY_DOMAINS = (
    "europium-oxalate-precipitator",
    "molybdenum-hexafluoride-purifier",
    "calcium-tungstate-czochralski",
    "silver-nitrate-crystallizer",
    "tungsten-hexafluoride-cvd",
)
MY_PLANTS = (
    "Europia-Clough",
    "Molyhex-Riggs",
    "Scheelite-Hurst",
    "Argent-Greet",
    "Hexafluor-Wold",
)
FORBIDDEN_PATHS = ("2026-08-17", "2026-08-30")


def tokens(text: str) -> set[str]:
    return set(TOKEN_RE.findall(text.lower()))


def jaccard(a: str, b: str) -> float:
    a_tok, b_tok = tokens(a), tokens(b)
    if not a_tok and not b_tok:
        return 1.0
    return len(a_tok & b_tok) / len(a_tok | b_tok)


def simulate_lif(
    *,
    n: int,
    window_ms: int,
    dt_us: int = 100,
    tau_m_ms: float = 18.0,
    v_th: float = 1.0,
    r_m: float = 1.0,
    refractory_us: int = 1000,
    i_bias: float = 0.88,
    i_stim_peak: float = 2.35,
    stim_t_us: tuple[int, int] = (24000, 27000),
    extra_bias_n: int = 14,
    extra_i: float = 0.70,
    noise: float = 0.045,
    seed: int,
):
    rng = random.Random(seed)
    n_steps = int(round(window_ms * 1000 / dt_us))
    tau_us = tau_m_ms * 1000.0
    v = [0.0] * n
    refrac = [0] * n
    spikes = []
    for step in range(n_steps):
        t = step * dt_us
        stim = stim_t_us[0] <= t < stim_t_us[1]
        for i in range(n):
            if refrac[i] > 0:
                refrac[i] -= dt_us
                v[i] = 0.0
                continue
            current = i_bias + rng.gauss(0.0, noise)
            if i < extra_bias_n:
                current += extra_i
            if stim:
                current += i_stim_peak
            v[i] += (dt_us / tau_us) * (-v[i] + r_m * current)
            if v[i] >= v_th:
                spikes.append((t, i))
                v[i] = 0.0
                refrac[i] = refractory_us
    return spikes


def pick_excerpt(spikes, *, n, window_ms, stim_t_us, extra_bias_n, early_ch, late_ch, cap=16):
    window_us = window_ms * 1000
    early, late, rest = [], [], []
    for t, nid in spikes:
        if not (0 <= t <= window_us) or not (0 <= nid < n):
            continue
        if stim_t_us[0] <= t < stim_t_us[1]:
            late.append((t, nid, late_ch))
        elif nid < extra_bias_n:
            early.append((t, nid, early_ch))
        else:
            rest.append((t, nid, early_ch))
    chosen = early[:7] + late[:9]
    if len(chosen) < 12:
        for item in rest + early[7:] + late[9:]:
            if len(chosen) >= 14:
                break
            if item not in chosen:
                chosen.append(item)
    chosen.sort(key=lambda x: (x[0], x[1]))
    seen = set()
    excerpt = []
    last = {}
    for t, nid, ch in chosen:
        key = (t, nid)
        if key in seen:
            continue
        if nid in last and t - last[nid] < 1000:
            continue
        seen.add(key)
        last[nid] = t
        excerpt.append({"t_us": int(t), "neuron_id": int(nid), "channel": ch})
        if len(excerpt) >= cap:
            break
    if len(excerpt) < 8:
        raise RuntimeError(f"LIF excerpt short: {len(excerpt)}")
    return excerpt


def raster_block(
    *,
    window_ms,
    neurons,
    mean_rate_hz,
    delayed_s,
    source,
    target,
    table,
    modulator,
    tau_e_s,
    eligibility,
    seed,
    stim_t_us,
    extra_bias_n,
    extra_i,
    early_ch,
    late_ch,
    note,
    i_bias=0.88,
    i_stim_peak=2.35,
    abort_s=None,
    survey_s=None,
):
    window_s = window_ms / 1000.0
    spikes = int(round(neurons * mean_rate_hz * window_s))
    energy_pJ = spikes * 23
    energy_uJ = energy_pJ / 1_000_000
    lif_spikes = simulate_lif(
        n=neurons,
        window_ms=window_ms,
        stim_t_us=stim_t_us,
        extra_bias_n=extra_bias_n,
        extra_i=extra_i,
        seed=seed,
        i_bias=i_bias,
        i_stim_peak=i_stim_peak,
    )
    excerpt = pick_excerpt(
        lif_spikes,
        n=neurons,
        window_ms=window_ms,
        stim_t_us=stim_t_us,
        extra_bias_n=extra_bias_n,
        early_ch=early_ch,
        late_ch=late_ch,
    )
    tau_e_ms = tau_e_s * 1000.0
    body = {
        "window_ms": window_ms,
        "window_s": window_s,
        "neurons": neurons,
        "mean_rate_hz": mean_rate_hz,
        "spikes": spikes,
        "energy_pJ": energy_pJ,
        "energy_uJ": energy_uJ,
        "excerpt_source": "independent_lif",
        "sim_scope": "sidecar_only",
        "delayed_surprise_s": delayed_s,
        "lif": {
            "model": "leaky_integrate_and_fire",
            "n": neurons,
            "dt_us": 100,
            "tau_m_ms": 18.0,
            "v_rest": 0.0,
            "v_reset": 0.0,
            "v_th": 1.0,
            "r_m": 1.0,
            "refractory_us": 1000,
            "i_bias": i_bias,
            "i_stim_peak": i_stim_peak,
            "stim_t_us": list(stim_t_us),
            "i_clamp_extra": extra_i,
            "clamp_n": extra_bias_n,
            "seed": seed,
            "note": note,
        },
        "routing": {
            "source": source,
            "target": target,
            "table": table,
            "third_factor": {
                "modulator": modulator,
                "tau_e_s": tau_e_s,
                "tau_e_ms": tau_e_ms,
                "eligibility": eligibility,
            },
        },
        "excerpt": excerpt,
    }
    if abort_s is not None:
        body["abort_s"] = abort_s
    if survey_s is not None:
        body["survey_s"] = survey_s
    return body


def pop(name, neurons, threshold, mean_rate_hz, window_ms):
    window_s = window_ms / 1000.0
    spikes = int(round(neurons * mean_rate_hz * window_s))
    return {
        "name": name,
        "neurons": neurons,
        "threshold": threshold,
        "mean_rate_hz": mean_rate_hz,
        "spikes": spikes,
    }


def veto(name, neurons, threshold):
    return {"name": name, "neurons": neurons, "threshold": threshold}


def ticks_from(rows):
    ticks = []
    sums = {
        "task_progress": 0.0,
        "safety": 0.0,
        "efficiency": 0.0,
        "coherence": 0.0,
        "exploration": 0.0,
    }
    for t_us, tp, saf, eff, coh, exp in rows:
        ticks.append(
            {
                "t_us": t_us,
                "task_progress": tp,
                "safety": saf,
                "efficiency": eff,
                "coherence": coh,
                "exploration": exp,
            }
        )
        sums["task_progress"] += tp
        sums["safety"] += saf
        sums["efficiency"] += eff
        sums["coherence"] += coh
        sums["exploration"] += exp
    for key in sums:
        sums[key] = round(sums[key], 10)
    total = round(sum(sums.values()), 10)
    return ticks, sums, total


def meta_common(domain, tags, distillation, batch_position, extra=None):
    meta = {
        "round": ROUND_N,
        "factory": "thalamic-trajectory-factory",
        "generator": "grok-4.6",
        "run_label": "2026-09-02-final-heavy",
        "schema_version": "thalamic-trajectory-v2",
        "domain": domain,
        "tags": tags,
        "snn_tags": ["race", "refractory", "adaptation"],
        "distillation_value": distillation,
        "rights": dict(RIGHTS),
        "batch_position": batch_position,
    }
    if extra:
        meta.update(extra)
    return meta


def reward_block(ticks, sums, total, notes):
    return {
        "_aggregation": "total = task_progress + safety + efficiency + coherence + exploration",
        "ticks": ticks,
        "task_progress": sums["task_progress"],
        "safety": sums["safety"],
        "efficiency": sums["efficiency"],
        "coherence": sums["coherence"],
        "exploration": sums["exploration"],
        "total": total,
        "notes": notes,
    }


def rec_356():
    delayed = 780
    ticks, sums, total = ticks_from(
        [
            (2080, 0.04, -0.02, -0.02, 0.01, 0.00),
            (5200, 0.08, -0.04, -0.02, 0.01, -0.01),
            (5380, 0.04, -0.03, -0.02, 0.00, 0.00),
            (6000, 0.08, -0.05, -0.03, 0.02, -0.01),
            (23400, 0.06, -0.43, -0.04, -0.01, -0.01),
            (780000000, 0.02, -0.05, -0.03, 0.01, -0.01),
        ]
    )
    raster = raster_block(
        window_ms=42,
        neurons=80,
        mean_rate_hz=24,
        delayed_s=delayed,
        abort_s=delayed,
        source="thalamic-relay.liquor-tc",
        target="spikenaut.policy.feed-clamp",
        table=[
            {"from": "relay.tc.liquor", "to": "policy.feed_clamp", "weight": 0.69},
            {"from": "relay.enc.feed", "to": "policy.feed_hold", "weight": 0.28},
            {"from": "relay.ae.rake", "to": "policy.feed_clamp", "weight": -0.44},
        ],
        modulator="noradrenaline",
        tau_e_s=0.042,
        eligibility="surprise-gated pre_post_stdp; NA at liquor-TC win (5.200 ms) opens a 42 ms eligibility trace that still covers the 23.400 ms rake-arm shear",
        seed=72356,
        stim_t_us=(22000, 25600),
        extra_bias_n=14,
        extra_i=0.66,
        early_ch="lif.clamp",
        late_ch="lif.rake",
        note="Population sim scoped to this sidecar. Plant remains designed. Neurons 0-13 carry +0.66 oxalate-feed-clamp bias; stim 22.0-25.6 ms is the rake-arm shear.",
    )
    return {
        "id": "ttf-r72-356",
        "title": "Europia-Clough EC-6 / Precip-P3: liquor 78.4 C beats oxalate feed 18.0 t/h by 180 us; correct MODIFY still eats an in-window rake-arm shear (partnered negative total -0.46)",
        "state": {
            "description": "Precip-P3 is already drawing europium oxalate on Europia-Clough EC-6 when liquor RTD sits at 78.4 C against a 72.0 C nucleation cap. Oxalate-feed encoder still prints a quiet 18.0 t/h, so a feed-first planner would keep the full charge. The live contest is liquor temperature versus feed rate, not pH versus agitator. A rake-arm shear is off both buses until the later dump.",
            "domain": "europium-oxalate-precipitator",
            "sim_or_real": "designed",
            "goal": "Keep liquor T <= 72.0 C, finish the 13 min Eu2(C2O4)3 nucleation window, and leave pH at the planned 1.80.",
            "t0_us": 1756842500000356,
            "gate_latency_us": 800,
            "race_window_us": 400,
            "race_window_rel_ms": [5.20, 5.60],
            "race": {
                "contenders": [
                    "tc.liquor.C 78.4 C over 72.0 cap",
                    "enc.feed.tph 18.0 t/h quiet",
                ],
                "semantics": "Liquor-first latches oxalate-feed clamp 18.0 -> 9.2 t/h; feed-first keeps cruise on a 'still legal encoder' model.",
                "window_derivation": "400 us = one liquor-RTD analog slot versus the oxalate-feed encoder publisher on this 2 kHz precip bus.",
                "order_evidence_note": "Margin 180 us vs combined jitter 58 us (RTD 26 + encoder 32): 3.1x over a 2.0x trust floor. Reversing order by < 180 us inside the 400 us window would have kept 18.0 t/h; predicted next-sample 75.2 C > 72.0 cap.",
            },
            "sensors": [
                "liquor RTD analog, 2 kHz, 26 us jitter",
                "oxalate-feed encoder, 1 kHz, 32 us jitter",
                "rake AE puck (context)",
                "pH probe (context)",
            ],
            "constraints": {
                "liquor_cap_C": 72.0,
                "observed_liquor_C": 78.4,
                "feed_t_h": 18.0,
                "ph": 1.80,
            },
            "episode_steps": [
                "1. Precip-P3 indexed on Europia-Clough EC-6; liquor 78.4 C; oxalate 18.0 t/h armed.",
                "2. Published liquor cap 72.0 C; rake AE quiet; pH 1.80 held.",
                "3. Encoder precursor at 2.080 ms.",
                "4. Race window [5.200, 5.600] ms.",
                "5. Liquor RTD 78.4 C at 5.200 ms (winner).",
                "6. Oxalate encoder 18.0 t/h at 5.380 ms (loser by 180 us).",
                "7. Gate at 6.000 ms: MODIFY clamp feed 18.0 -> 9.2 t/h.",
                "8. After clamp liquor 69.8 C <= 72.0; pH still 1.80.",
                "9. At 23.400 ms a rake arm shears and dumps 0.4 t of wet cake.",
                "10. 13 min isolate + rake swap (abort_s=780); named un-netted loss.",
            ],
        },
        "spike_events": [
            {"channel": "ph.ctx", "t_rel_ms": 1.04, "amplitude": 0.41},
            {"channel": "tc.liquor.C", "t_rel_ms": 2.08, "amplitude": 0.62},
            {"channel": "enc.feed.tph", "t_rel_ms": 3.16, "amplitude": 0.50},
            {"channel": "ae.rake.ctx", "t_rel_ms": 4.00, "amplitude": 0.44},
            {"channel": "tc.liquor.C", "t_rel_ms": 5.20, "amplitude": 1.34},
            {"channel": "enc.feed.tph", "t_rel_ms": 5.38, "amplitude": 1.12},
            {"channel": "ctrl.gate", "t_rel_ms": 6.00, "amplitude": 0.97},
            {"channel": "tc.liquor.C", "t_rel_ms": 7.40, "amplitude": 0.81},
            {"channel": "enc.feed.tph", "t_rel_ms": 9.20, "amplitude": 0.58},
            {"channel": "ctrl.gate", "t_rel_ms": 14.40, "amplitude": 0.84},
            {"channel": "ae.rake.shear", "t_rel_ms": 23.40, "amplitude": 1.46},
            {"channel": "tc.liquor.C", "t_rel_ms": 28.20, "amplitude": 0.55},
            {"channel": "ctrl.gate", "t_rel_ms": 36.00, "amplitude": 0.66},
        ],
        "proposed_action": {
            "name": "cruise_oxalate_feed",
            "parameters": {
                "feed_t_h": 18.0,
                "liquor_C": 78.4,
                "ph": 1.80,
            },
            "evidence": {
                "liquor_C": 78.4,
                "liquor_cap_C": 72.0,
                "predicted_unclamped_next_C": 75.2,
                "feed_t_h": 18.0,
                "ph": 1.80,
                "race_margin_us": 180,
                "combined_jitter_us": 58,
                "abort_s": 780,
            },
            "basis": "Planner proposes 18.0 t/h because the oxalate encoder is quiet and treats 78.4 C as a fogged liquor RTD rather than a 72.0 C nucleation-cap miss.",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "correctness": "correct",
            "rationale": "Liquor 78.4 C won by 180 us, so EC-6 is over the 72.0 C Eu oxalate nucleation cap, not still a feed-encoder story. Holding 18.0 t/h predicts next-sample 75.2 C > 72.0. MODIFY: oxalate 18.0 -> 9.2 t/h. Observed after clamp 69.8 C <= 72.0. A full REJECT is not indicated: a legal liquor accepts 9.2 t/h. pH stays 1.80.",
            "constraint_checked": {
                "liquor_C": {
                    "cap": 72.0,
                    "observed": 78.4,
                    "predicted_unclamped_next": 75.2,
                    "clamped_feed_t_h": 9.2,
                    "observed_after_clamp": 69.8,
                },
                "order_evidence": {"margin_us": 180, "combined_jitter_us": 58, "ratio": 3.1},
            },
        },
        "executed_action": {
            "name": "clamped_oxalate_feed",
            "parameters": {
                "feed_t_h": 9.2,
                "liquor_C": 69.8,
                "ph": 1.80,
            },
            "gate_effect": "MODIFY: oxalate 18.0 -> 9.2 t/h. Process-correct vs the 72.0 C liquor cap. Rake arm still shears at 23.400 ms.",
        },
        "future_outcome": {
            "summary": "Process-correct MODIFY held liquor at 69.8 C. At 23.400 ms a rake arm already seated on Precip-P3 dumped 0.4 t of wet Eu oxalate cake. Clamp reduced thermal load; it did not prevent the shear. Partnered negative: process heads stay honest; world loss is named, not netted.",
            "state_delta": {
                "precip": "clamp executed; liquor 69.8 C <= 72.0 cap",
                "rake": "sheared at 23.400 ms; 0.4 t wet cake in the mother liquor",
                "repair": "13 min isolate + rake swap (abort_s=780)",
                "mission": "EC-6 Eu oxalate nucleation incomplete this circuit",
            },
            "surprises": [
                "Neither liquor RTD nor oxalate encoder predicted the seated rake shear; ae.rake.shear is a new channel at 23.400 ms, 17.400 ms after the gate, still inside the 42 ms raster.",
                "Delayed (abort_s=780): 13 min isolate + rake swap. Named un-netted loss, not folded into task_progress.",
            ],
            "un_netted_loss": "13 min isolate after the rake-arm shear. Safety head -0.62 prices the dump; task_progress stays +0.32 because the oxalate clamp completed under the 72.0 C cap. World loss is named here, not subtracted from process heads.",
            "race_result": {
                "winner": "tc.liquor.C (5.200 ms, 78.4 C)",
                "loser": "enc.feed.tph (5.380 ms, 18.0 t/h)",
                "margin_us": 180,
                "counterfactual_if_reversed": "Feed-first by < 180 us inside the 400 us window would have kept 18.0 t/h; predicted next-sample 75.2 C would have missed the 72.0 cap even without the shear. The MODIFY is still the correct process. The shear is a later world charge either way, cheaper with the clamp than without.",
            },
            "reward_inflection_t_us": 23400,
            "reward_inflection_note": "Safety collapses at the 23.400 ms rake-arm shear (tick t_us=23400), inside the 42 ms raster. The correct MODIFY at 6.000 ms is in the same excerpt. Do not put inflection on the +13 min isolate tick.",
            "delayed_surprise_s": delayed,
        },
        "reward_components": reward_block(
            ticks,
            sums,
            total,
            "Partnered negative. Process-correct MODIFY; world still charges inside the 42 ms raster. total -0.46 = 0.32 + -0.62 + -0.16 + 0.04 + -0.04. Named rake isolate (abort_s=780) is not netted into task_progress.",
        ),
        "raster": raster,
        "gate_snn": {
            "decision_window_ms": 0.40,
            "decision": "MODIFY",
            "populations": [
                pop("feed_clamp", 48, 0.5, 220.0, 0.40),
                pop("feed_hold", 36, 0.8, 40.0, 0.40),
                veto("rake_veto", 22, 0.75),
            ],
        },
        "meta": meta_common(
            "europium-oxalate-precipitator",
            [
                "modify",
                "partnered-negative-total",
                "independent-lif-raster",
                "sidecar-sim-only",
                "in-window-world-charge",
                "designed",
            ],
            "A critic can see the world-charge as a LIF burst inside the raster while process heads stay honest. Credit assignment is spikes, not prose across a 13 min rake isolate.",
            1,
        ),
    }


def rec_357():
    delayed = 210
    ticks, sums, total = ticks_from(
        [
            (2560, 0.05, 0.04, 0.02, 0.01, 0.01),
            (6400, 0.08, 0.07, 0.04, 0.02, 0.01),
            (6580, 0.04, 0.04, 0.02, 0.02, 0.01),
            (7160, 0.12, 0.09, 0.05, 0.03, 0.02),
            (7560, 0.06, 0.05, 0.02, 0.01, 0.01),
            (210000000, 0.03, 0.03, 0.02, 0.01, 0.01),
        ]
    )
    raster = raster_block(
        window_ms=28,
        neurons=64,
        mean_rate_hz=40,
        delayed_s=delayed,
        survey_s=delayed,
        source="thalamic-relay.head-tc",
        target="spikenaut.policy.steam-clamp",
        table=[
            {"from": "relay.tc.head", "to": "policy.steam_clamp", "weight": 0.71},
            {"from": "relay.enc.reflux", "to": "policy.reflux_hold", "weight": 0.26},
        ],
        modulator="acetylcholine",
        tau_e_s=0.09,
        eligibility="pre_post_stdp; ACh at head-TC win (6.400 ms) tags the steam_clamp bind",
        seed=72357,
        stim_t_us=(5000, 9000),
        extra_bias_n=16,
        extra_i=0.62,
        early_ch="lif.head",
        late_ch="lif.reflux",
        note="Population sim scoped to this sidecar. Plant remains designed. Neurons 0-15 carry +0.62 steam-clamp bias; stim 5-9 ms covers the race+gate.",
        i_bias=0.86,
        i_stim_peak=2.10,
    )
    return {
        "id": "ttf-r72-357",
        "title": "Molyhex-Riggs MR-4 / Still ST-5: head 68.4 C beats reflux encoder 14 Hz by 180 us; correct MODIFY cuts steam 2.40 -> 1.10 t/h",
        "state": {
            "description": "Still ST-5 on Molyhex-Riggs MR-4 is already taking a MoF6 hearts cut when head TC prints 68.4 C against a 52.0 C low-boiler cap. Reflux encoder is a calm 14 Hz, which a reflux-first planner would read as a still on-spec. No later packing dump is armed on this pass.",
            "domain": "molybdenum-hexafluoride-purifier",
            "sim_or_real": "designed",
            "goal": "Hold head T <= 52.0 C, keep MoF6 hearts on-spec, and leave reflux at 14 Hz after the steam cut.",
            "t0_us": 1756842500000357,
            "gate_latency_us": 760,
            "race_window_us": 400,
            "race_window_rel_ms": [6.40, 6.80],
            "race": {
                "contenders": [
                    "tc.head.C 68.4 C over 52.0 cap",
                    "enc.reflux.hz 14 Hz quiet",
                ],
                "semantics": "Head-first latches steam 2.40 -> 1.10 t/h; reflux-first keeps the 2.40 t/h boil-up.",
                "window_derivation": "400 us = one head-TC analog slot versus the reflux encoder on this 2 kHz still bus.",
                "order_evidence_note": "Margin 180 us vs combined jitter 60 us (TC 28 + encoder 32): 3.0x over a 2.0x trust floor.",
            },
            "sensors": [
                "still-head TC analog, 2 kHz, 28 us jitter",
                "reflux encoder, 1 kHz, 32 us jitter",
                "steam flow (context)",
                "bottoms density (context)",
            ],
            "constraints": {
                "head_cap_C": 52.0,
                "observed_head_C": 68.4,
                "steam_t_h": 2.40,
                "reflux_hz": 14.0,
            },
            "episode_steps": [
                "1. Still ST-5 indexed on Molyhex-Riggs MR-4; head 68.4 C; steam 2.40 t/h.",
                "2. Published head cap 52.0 C; reflux 14 Hz quiet.",
                "3. Steam precursor at 2.560 ms.",
                "4. Race window [6.400, 6.800] ms.",
                "5. Head TC 68.4 C at 6.400 ms (winner).",
                "6. Reflux encoder 14 Hz at 6.580 ms (loser by 180 us).",
                "7. Gate at 7.160 ms: MODIFY steam 2.40 -> 1.10 t/h.",
                "8. After clamp head 48.6 C <= 52.0; reflux still 14 Hz.",
                "9. Survey 210 s confirms no packing dump.",
                "10. Hearts cut resumes under the 52.0 C cap.",
            ],
        },
        "spike_events": [
            {"channel": "steam.ctx", "t_rel_ms": 1.12, "amplitude": 0.43},
            {"channel": "tc.head.C", "t_rel_ms": 2.56, "amplitude": 0.64},
            {"channel": "enc.reflux.hz", "t_rel_ms": 3.80, "amplitude": 0.51},
            {"channel": "rho.bottoms.ctx", "t_rel_ms": 5.10, "amplitude": 0.46},
            {"channel": "tc.head.C", "t_rel_ms": 6.40, "amplitude": 1.33},
            {"channel": "enc.reflux.hz", "t_rel_ms": 6.58, "amplitude": 1.10},
            {"channel": "ctrl.gate", "t_rel_ms": 7.16, "amplitude": 0.96},
            {"channel": "tc.head.C", "t_rel_ms": 9.40, "amplitude": 0.78},
            {"channel": "enc.reflux.hz", "t_rel_ms": 12.20, "amplitude": 0.57},
            {"channel": "ctrl.gate", "t_rel_ms": 16.80, "amplitude": 0.82},
            {"channel": "tc.head.C", "t_rel_ms": 21.40, "amplitude": 0.54},
            {"channel": "steam.ctx", "t_rel_ms": 25.10, "amplitude": 0.48},
        ],
        "proposed_action": {
            "name": "cruise_mof6_steam",
            "parameters": {
                "steam_t_h": 2.40,
                "head_C": 68.4,
                "reflux_hz": 14.0,
            },
            "evidence": {
                "head_C": 68.4,
                "head_cap_C": 52.0,
                "predicted_unclamped_next_C": 61.0,
                "steam_t_h": 2.40,
                "reflux_hz": 14.0,
                "race_margin_us": 180,
                "combined_jitter_us": 60,
                "survey_s": 210,
            },
            "basis": "Planner proposes 2.40 t/h steam because reflux 14 Hz looks on-spec and treats 68.4 C as a lagged head TC rather than a 52.0 C MoF6 cap miss.",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "correctness": "correct",
            "rationale": "Head 68.4 C won by 180 us, so ST-5 is over the 52.0 C MoF6 low-boiler cap. Holding 2.40 t/h steam predicts next-sample 61.0 C > 52.0. MODIFY: steam 2.40 -> 1.10 t/h. Observed after clamp 48.6 C <= 52.0. A full REJECT is not indicated: a legal head accepts 1.10 t/h. Reflux stays 14 Hz.",
            "constraint_checked": {
                "head_C": {
                    "cap": 52.0,
                    "observed": 68.4,
                    "predicted_unclamped_next": 61.0,
                    "clamped_steam_t_h": 1.10,
                    "observed_after_clamp": 48.6,
                },
                "order_evidence": {"margin_us": 180, "combined_jitter_us": 60, "ratio": 3.0},
            },
        },
        "executed_action": {
            "name": "clamped_mof6_steam",
            "parameters": {
                "steam_t_h": 1.10,
                "head_C": 48.6,
                "reflux_hz": 14.0,
            },
            "gate_effect": "MODIFY: steam 2.40 -> 1.10 t/h. Process-correct vs the 52.0 C head cap. No later world charge on this pass.",
        },
        "future_outcome": {
            "summary": "Process-correct MODIFY held head at 48.6 C. Survey at 210 s found no packing dump. Hearts cut resumes under the 52.0 C cap.",
            "state_delta": {
                "still": "clamp executed; head 48.6 C <= 52.0 cap",
                "steam": "2.40 -> 1.10 t/h",
                "survey": "210 s; packing intact",
                "mission": "MoF6 hearts cut continues",
            },
            "surprises": [
                "Reflux encoder never left 14 Hz; the head TC was the only cap miss.",
                "Delayed (survey_s=210): packing inspection clean. No un-netted mechanical loss.",
            ],
            "race_result": {
                "winner": "tc.head.C (6.400 ms, 68.4 C)",
                "loser": "enc.reflux.hz (6.580 ms, 14 Hz)",
                "margin_us": 180,
                "counterfactual_if_reversed": "Reflux-first by < 180 us inside the 400 us window would have kept 2.40 t/h steam; predicted next-sample 61.0 C would have missed the 52.0 cap.",
            },
            "reward_inflection_t_us": 7160,
            "reward_inflection_note": "Task and safety inflect at the 7.160 ms steam clamp (tick t_us=7160). Do not put inflection on the +210 s survey tick.",
            "delayed_surprise_s": delayed,
        },
        "reward_components": reward_block(
            ticks,
            sums,
            total,
            "Correct MODIFY. total +1.04 = 0.38 + 0.32 + 0.17 + 0.10 + 0.07. Survey_s=210 is tick 6, not netted as a world charge.",
        ),
        "raster": raster,
        "gate_snn": {
            "decision_window_ms": 0.40,
            "decision": "MODIFY",
            "populations": [
                pop("steam_clamp", 48, 0.5, 210.0, 0.40),
                pop("reflux_hold", 36, 0.8, 45.0, 0.40),
                veto("head_cap_veto", 20, 0.75),
            ],
        },
        "meta": meta_common(
            "molybdenum-hexafluoride-purifier",
            [
                "modify",
                "independent-lif-raster",
                "sidecar-sim-only",
                "designed",
            ],
            "Teaches a head-TC versus reflux-encoder race where the correct clamp is steam, not a hold of the still.",
            2,
        ),
    }


def rec_358():
    delayed = 420
    ticks, sums, total = ticks_from(
        [
            (1960, 0.02, 0.06, 0.02, 0.01, 0.01),
            (4900, 0.02, 0.08, 0.02, 0.02, 0.01),
            (5080, 0.01, 0.07, 0.02, 0.02, 0.01),
            (5660, 0.02, 0.10, 0.03, 0.03, 0.02),
            (6060, 0.02, 0.06, 0.02, 0.01, 0.01),
            (420000000, 0.01, 0.03, 0.01, 0.01, 0.00),
        ]
    )
    raster = raster_block(
        window_ms=46,
        neurons=104,
        mean_rate_hz=22,
        delayed_s=delayed,
        abort_s=delayed,
        source="thalamic-relay.crystal-ae",
        target="spikenaut.policy.hold-reject",
        table=[
            {"from": "relay.ae.crystal", "to": "policy.hold_reject", "weight": 0.72},
            {"from": "relay.enc.pull", "to": "policy.go_raise", "weight": 0.24},
        ],
        modulator="dopamine",
        tau_e_s=0.12,
        eligibility="pre_post_stdp; DA at crystal-AE win (4.900 ms) tags the hold_reject bind",
        seed=72358,
        stim_t_us=(4000, 8000),
        extra_bias_n=18,
        extra_i=0.70,
        early_ch="lif.ae",
        late_ch="lif.pull",
        note="Population sim scoped to this sidecar. Plant remains hil. Neurons 0-17 carry +0.70 hold-reject bias; stim 4-8 ms covers the race+gate.",
        i_bias=0.84,
        i_stim_peak=2.20,
    )
    return {
        "id": "ttf-r72-358",
        "title": "Scheelite-Hurst SH-HIL / Puller P-8: crystal AE 56 pps beats pull encoder 1.80 mm/h by 180 us; correct REJECT holds the raise",
        "state": {
            "description": "Puller P-8 on the Scheelite-Hurst SH-HIL pad is already lifting a CaWO4 boule when crystal AE prints 56 pps against an 18 pps crucible-contact trip. Pull encoder still asks 1.80 mm/h. The dummy charge never leaves the HIL crucible; the AE burst is the live contact flag.",
            "domain": "calcium-tungstate-czochralski",
            "sim_or_real": "hil",
            "goal": "Hold pull at 0 mm/h while crystal AE >= 18 pps, then resume only after AE falls under trip on the HIL pad.",
            "t0_us": 1756842500000358,
            "gate_latency_us": 760,
            "race_window_us": 400,
            "race_window_rel_ms": [4.90, 5.30],
            "race": {
                "contenders": [
                    "ae.crystal.pps 56 pps over 18 trip",
                    "enc.pull.mmh 1.80 mm/h raise",
                ],
                "semantics": "AE-first REJECT-holds pull 1.80 -> 0 mm/h; pull-first would keep the raise into a crucible nick.",
                "window_derivation": "400 us = one AE puck slot versus the pull encoder on this 2 kHz HIL Czochralski bus.",
                "order_evidence_note": "Margin 180 us vs combined jitter 56 us (AE 24 + encoder 32): 3.2x over a 2.0x trust floor.",
            },
            "sensors": [
                "crystal AE puck, 2 kHz, 24 us jitter",
                "pull encoder, 1 kHz, 32 us jitter",
                "melt dip TC (context)",
                "seed rotation (context)",
            ],
            "constraints": {
                "ae_trip_pps": 18.0,
                "observed_ae_pps": 56.0,
                "pull_mm_h": 1.80,
                "hil_pad": "SH-HIL",
            },
            "episode_steps": [
                "1. Puller P-8 indexed on Scheelite-Hurst SH-HIL; AE 56 pps; pull 1.80 mm/h armed.",
                "2. Published AE trip 18 pps; dummy CaWO4 charge seated.",
                "3. AE precursor at 1.960 ms.",
                "4. Race window [4.900, 5.300] ms.",
                "5. Crystal AE 56 pps at 4.900 ms (winner).",
                "6. Pull encoder 1.80 mm/h at 5.080 ms (loser by 180 us).",
                "7. Gate at 5.660 ms: REJECT hold pull 1.80 -> 0 mm/h.",
                "8. AE stays 56 pps; dummy charge never nicks the crucible wall.",
                "9. 7 min abort (abort_s=420) to reseat the seed.",
                "10. QA: correct gate was REJECT; do not raise into AE 56 pps.",
            ],
        },
        "spike_events": [
            {"channel": "melt.ctx", "t_rel_ms": 0.88, "amplitude": 0.40},
            {"channel": "ae.crystal.pps", "t_rel_ms": 1.96, "amplitude": 0.66},
            {"channel": "enc.pull.mmh", "t_rel_ms": 3.10, "amplitude": 0.52},
            {"channel": "rot.seed.ctx", "t_rel_ms": 4.00, "amplitude": 0.45},
            {"channel": "ae.crystal.pps", "t_rel_ms": 4.90, "amplitude": 1.38},
            {"channel": "enc.pull.mmh", "t_rel_ms": 5.08, "amplitude": 1.14},
            {"channel": "ctrl.gate", "t_rel_ms": 5.66, "amplitude": 0.98},
            {"channel": "ae.crystal.pps", "t_rel_ms": 7.80, "amplitude": 0.80},
            {"channel": "enc.pull.mmh", "t_rel_ms": 11.40, "amplitude": 0.55},
            {"channel": "ctrl.gate", "t_rel_ms": 16.20, "amplitude": 0.83},
            {"channel": "ae.crystal.pps", "t_rel_ms": 24.10, "amplitude": 0.60},
            {"channel": "ctrl.gate", "t_rel_ms": 33.00, "amplitude": 0.64},
            {"channel": "melt.ctx", "t_rel_ms": 41.20, "amplitude": 0.42},
        ],
        "proposed_action": {
            "name": "raise_cawo4_pull",
            "parameters": {
                "pull_mm_h": 1.80,
                "ae_pps": 56.0,
                "hold": False,
            },
            "evidence": {
                "ae_pps": 56.0,
                "ae_trip_pps": 18.0,
                "pull_mm_h": 1.80,
                "hil_pad": "SH-HIL",
                "race_margin_us": 180,
                "combined_jitter_us": 56,
                "abort_s": 420,
            },
            "basis": "Planner proposes 1.80 mm/h because the pull encoder is already latched and treats 56 pps AE as a melt-bubble rattle rather than crucible contact.",
        },
        "safety_decision": {
            "decision": "REJECT",
            "correctness": "correct",
            "rationale": "Crystal AE 56 pps won by 180 us, so P-8 is over the 18 pps crucible-contact trip. Raising 1.80 mm/h would nick the HIL dummy charge. REJECT: hold pull 1.80 -> 0 mm/h. A MODIFY trim still leaves the seed in contact.",
            "constraint_checked": {
                "ae_pps": {
                    "trip": 18.0,
                    "observed": 56.0,
                    "executed_pull_mm_h": 0.0,
                },
                "order_evidence": {"margin_us": 180, "combined_jitter_us": 56, "ratio": 3.21},
            },
        },
        "executed_action": {
            "name": "hold_cawo4_pull",
            "parameters": {
                "pull_mm_h": 0.0,
                "ae_pps": 56.0,
                "hold": True,
            },
            "gate_effect": "REJECT: pull 1.80 -> 0 mm/h. Correct hold vs the 18 pps AE trip on SH-HIL.",
        },
        "future_outcome": {
            "summary": "Correct REJECT held pull at 0 mm/h. Dummy CaWO4 charge never nicked the crucible. 7 min seed reseat follows.",
            "state_delta": {
                "puller": "hold executed; pull 0 mm/h",
                "ae": "56 pps remains over 18 trip",
                "repair": "7 min seed reseat (abort_s=420)",
                "mission": "HIL Czochralski raise aborted this circuit",
            },
            "surprises": [
                "Pull encoder never dropped its 1.80 mm/h ask; AE was the only trip.",
                "Delayed (abort_s=420): 7 min seed reseat on SH-HIL.",
            ],
            "race_result": {
                "winner": "ae.crystal.pps (4.900 ms, 56 pps)",
                "loser": "enc.pull.mmh (5.080 ms, 1.80 mm/h)",
                "margin_us": 180,
                "counterfactual_if_reversed": "Pull-first by < 180 us inside the 400 us window would have kept 1.80 mm/h into a crucible nick on the HIL dummy charge.",
            },
            "reward_inflection_t_us": 5660,
            "reward_inflection_note": "Safety inflects at the 5.660 ms REJECT hold (tick t_us=5660). Do not put inflection on the +7 min reseat tick.",
            "delayed_surprise_s": delayed,
        },
        "reward_components": reward_block(
            ticks,
            sums,
            total,
            "Correct REJECT. total +0.80 = 0.10 + 0.40 + 0.12 + 0.10 + 0.06. abort_s=420 is tick 6.",
        ),
        "raster": raster,
        "gate_snn": {
            "decision_window_ms": 0.40,
            "decision": "REJECT",
            "populations": [
                pop("hold_reject", 48, 0.5, 200.0, 0.40),
                pop("go_raise", 48, 0.8, 10.0, 0.40),
                veto("ae_trip_veto", 24, 0.75),
            ],
        },
        "meta": meta_common(
            "calcium-tungstate-czochralski",
            [
                "reject",
                "independent-lif-raster",
                "sidecar-sim-only",
                "hil",
            ],
            "Teaches an AE-versus-pull race on a HIL Czochralski pad where the correct gate is a full hold, not a trim.",
            3,
        ),
    }


def rec_359():
    delayed = 300
    ticks, sums, total = ticks_from(
        [
            (2920, 0.06, 0.04, 0.03, 0.02, 0.01),
            (7300, 0.10, 0.06, 0.04, 0.03, 0.02),
            (7520, 0.05, 0.04, 0.02, 0.02, 0.01),
            (8060, 0.12, 0.08, 0.05, 0.03, 0.02),
            (8460, 0.05, 0.04, 0.02, 0.01, 0.01),
            (300000000, 0.02, 0.02, 0.02, 0.01, 0.01),
        ]
    )
    raster = raster_block(
        window_ms=30,
        neurons=56,
        mean_rate_hz=40,
        delayed_s=delayed,
        survey_s=delayed,
        source="thalamic-relay.liquor-rtd",
        target="spikenaut.policy.go-accept",
        table=[
            {"from": "relay.rtd.liquor", "to": "policy.go_accept", "weight": 0.70},
            {"from": "relay.ir.hood", "to": "policy.ir_hold", "weight": 0.22},
        ],
        modulator="serotonin",
        tau_e_s=0.08,
        eligibility="pre_post_stdp; 5-HT at liquor-RTD win (7.300 ms) tags the go_accept bind",
        seed=72359,
        stim_t_us=(6000, 10000),
        extra_bias_n=14,
        extra_i=0.58,
        early_ch="lif.rtd",
        late_ch="lif.hood",
        note="Population sim scoped to this sidecar. Plant remains simulated. Neurons 0-13 carry +0.58 accept-pathway bias; stim 6-10 ms covers the race+gate.",
        i_bias=0.85,
        i_stim_peak=2.05,
    )
    params = {
        "air_t_h": 6.4,
        "liquor_C": 38.4,
        "hood_ir_C": 54.0,
    }
    return {
        "id": "ttf-r72-359",
        "title": "Argent-Greet AG-2 sim / Crystallizer X-4: liquor 38.4 C beats hood IR smear 54 C by 220 us; ACCEPT already-legal 6.4 t/h air",
        "state": {
            "description": "Crystallizer X-4 in the Argent-Greet AG-2 silver-nitrate simulation already holds liquor at 38.4 C against a 52.0 C crystal-growth cap. Hood IR still smears 54 C from a steam-trace reflection, which a glint-first planner would treat as an over-cap. The live liquor is legal; the proposed 6.4 t/h air is already inside envelope.",
            "domain": "silver-nitrate-crystallizer",
            "sim_or_real": "simulated",
            "goal": "Keep 6.4 t/h air, hold liquor T < 52.0 C, and finish the 5 min AgNO3 growth window.",
            "t0_us": 1756842500000359,
            "gate_latency_us": 760,
            "race_window_us": 400,
            "race_window_rel_ms": [7.30, 7.70],
            "race": {
                "contenders": [
                    "rtd.liquor.C 38.4 C under 52.0 cap",
                    "ir.hood.C 54 C smear",
                ],
                "semantics": "Liquor-first ACCEPT 6.4 t/h air; hood-first would false-hold on a steam-trace glint.",
                "window_derivation": "400 us = one liquor-RTD analog slot versus the hood-IR publisher on this 2 kHz sim bus.",
                "order_evidence_note": "Margin 220 us vs combined jitter 70 us (RTD 30 + IR 40): 3.1x over a 2.0x trust floor. Order is correctly liquor-first. The glint is not live liquor.",
            },
            "sensors": [
                "liquor RTD analog, 2 kHz, 30 us jitter",
                "hood IR pyrometer, 1 kHz, 40 us jitter",
                "air MFC (context)",
                "mother-liquor density (context)",
            ],
            "constraints": {
                "liquor_cap_C": 52.0,
                "observed_liquor_C": 38.4,
                "hood_ir_C": 54.0,
                "air_t_h": 6.4,
            },
            "episode_steps": [
                "1. Crystallizer X-4 indexed on Argent-Greet AG-2 sim; liquor 38.4 C; air 6.4 t/h armed.",
                "2. Published liquor cap 52.0 C; hood IR smear 54 C tagged glint, not live.",
                "3. Air precursor at 2.920 ms.",
                "4. Race window [7.300, 7.700] ms.",
                "5. Liquor RTD 38.4 C at 7.300 ms (winner).",
                "6. Hood IR 54 C at 7.520 ms (loser by 220 us).",
                "7. Gate at 8.060 ms: ACCEPT 6.4 t/h air.",
                "8. Liquor stays 38.4 C <= 52.0; air remains 6.4 t/h.",
                "9. 5 min growth window completes (survey_s=300).",
                "10. QA: correct gate was ACCEPT; ignore hood IR smear.",
            ],
        },
        "spike_events": [
            {"channel": "air.ctx", "t_rel_ms": 1.20, "amplitude": 0.42},
            {"channel": "rtd.liquor.C", "t_rel_ms": 2.92, "amplitude": 0.60},
            {"channel": "ir.hood.C", "t_rel_ms": 4.10, "amplitude": 0.55},
            {"channel": "rho.ml.ctx", "t_rel_ms": 5.60, "amplitude": 0.47},
            {"channel": "rtd.liquor.C", "t_rel_ms": 7.30, "amplitude": 1.28},
            {"channel": "ir.hood.C", "t_rel_ms": 7.52, "amplitude": 1.16},
            {"channel": "ctrl.gate", "t_rel_ms": 8.06, "amplitude": 0.95},
            {"channel": "rtd.liquor.C", "t_rel_ms": 10.40, "amplitude": 0.74},
            {"channel": "ir.hood.C", "t_rel_ms": 13.80, "amplitude": 0.58},
            {"channel": "ctrl.gate", "t_rel_ms": 18.20, "amplitude": 0.80},
            {"channel": "rtd.liquor.C", "t_rel_ms": 24.00, "amplitude": 0.52},
            {"channel": "air.ctx", "t_rel_ms": 28.40, "amplitude": 0.44},
        ],
        "proposed_action": {
            "name": "hold_agno3_air",
            "parameters": dict(params),
            "evidence": {
                "liquor_C": 38.4,
                "liquor_cap_C": 52.0,
                "hood_ir_C": 54.0,
                "hood_is_live": False,
                "air_t_h": 6.4,
                "race_margin_us": 220,
                "combined_jitter_us": 70,
                "survey_s": 300,
            },
            "basis": "Planner proposes 6.4 t/h air because live liquor 38.4 C is 13.6 C under the published 52.0 C cap and the 54 C print is a hood-IR steam-trace smear, not liquor.",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "correctness": "correct",
            "rationale": "Liquor 38.4 C won by 220 us and sits under the 52.0 C AgNO3 cap. Hood IR 54 C is a smear (hood_is_live=false). ACCEPT: leave 6.4 t/h air. A REJECT on the glint would stall a legal crystallizer.",
            "constraint_checked": {
                "liquor_C": {
                    "cap": 52.0,
                    "observed": 38.4,
                    "hood_ir_C": 54.0,
                    "hood_is_live": False,
                    "executed_air_t_h": 6.4,
                },
                "order_evidence": {"margin_us": 220, "combined_jitter_us": 70, "ratio": 3.14},
            },
        },
        "executed_action": {
            "name": "hold_agno3_air",
            "parameters": dict(params),
            "gate_effect": "ACCEPT: air stays 6.4 t/h. Liquor 38.4 C remains under the 52.0 C cap. Hood IR smear unbound.",
        },
        "future_outcome": {
            "summary": "Correct ACCEPT left 6.4 t/h air. Liquor stayed 38.4 C. Hood IR smear never became a hold. 5 min growth window completes.",
            "state_delta": {
                "crystallizer": "air 6.4 t/h held; liquor 38.4 C <= 52.0",
                "hood": "IR smear unbound",
                "survey": "300 s growth window complete",
                "mission": "AG-2 AgNO3 pass legal this circuit",
            },
            "surprises": [
                "Hood IR remained a smear; liquor RTD never approached 52.0 C.",
                "Delayed (survey_s=300): 5 min growth window completes without a hold.",
            ],
            "race_result": {
                "winner": "rtd.liquor.C (7.300 ms, 38.4 C)",
                "loser": "ir.hood.C (7.520 ms, 54 C smear)",
                "margin_us": 220,
                "counterfactual_if_reversed": "Hood-first by < 220 us inside the 400 us window would only have delayed confirmation of the same legal liquor; ACCEPT remains correct.",
            },
            "reward_inflection_t_us": 8060,
            "reward_inflection_note": "Task inflects at the 8.060 ms ACCEPT (tick t_us=8060). Do not put inflection on the +300 s survey tick.",
            "delayed_surprise_s": delayed,
        },
        "reward_components": reward_block(
            ticks,
            sums,
            total,
            "Correct ACCEPT of an already-legal AgNO3 pass. total +1.06 = 0.40 + 0.28 + 0.18 + 0.12 + 0.08.",
        ),
        "raster": raster,
        "gate_snn": {
            "decision_window_ms": 0.40,
            "decision": "ACCEPT",
            "populations": [
                pop("go_accept", 48, 0.5, 210.0, 0.40),
                pop("ir_hold", 36, 0.8, 10.0, 0.40),
                veto("glint_veto", 20, 0.75),
            ],
        },
        "meta": meta_common(
            "silver-nitrate-crystallizer",
            [
                "accept",
                "already-legal",
                "independent-lif-raster",
                "sidecar-sim-only",
                "simulated",
            ],
            "Teaches that a liquor RTD under cap can confirm an already-legal AgNO3 pass without a hood-IR smear becoming a hold.",
            4,
        ),
    }


def rec_360():
    delayed = 540
    ticks, sums, total = ticks_from(
        [
            (2160, -0.02, 0.01, -0.02, -0.01, 0.01),
            (5400, -0.04, 0.01, -0.04, -0.02, 0.01),
            (5620, -0.03, 0.01, -0.03, -0.01, 0.01),
            (6200, -0.06, 0.02, -0.08, -0.03, 0.02),
            (6600, -0.02, 0.01, -0.03, -0.01, 0.01),
            (540000000, -0.01, 0.00, -0.02, 0.00, 0.00),
        ]
    )
    raster = raster_block(
        window_ms=24,
        neurons=88,
        mean_rate_hz=32,
        delayed_s=delayed,
        abort_s=delayed,
        source="thalamic-relay.tc-typek",
        target="spikenaut.policy.hold-reject",
        table=[
            {"from": "relay.tc.types", "to": "policy.hold_reject", "weight": 0.74},
            {"from": "relay.tc.k", "to": "policy.go_accept", "weight": -0.22},
            {"from": "relay.mfc.wf6", "to": "policy.hold_reject", "weight": 0.18},
        ],
        modulator="acetylcholine",
        tau_e_s=0.05,
        eligibility="pre_post_stdp; ACh at type-K win (5.400 ms) should have tagged go_accept; leftover type-S table instead weights hold_reject",
        seed=72360,
        stim_t_us=(4000, 8000),
        extra_bias_n=16,
        extra_i=0.64,
        early_ch="lif.typek",
        late_ch="lif.types",
        note="Population sim scoped to this sidecar. Plant remains designed. Neurons 0-15 carry leftover type-S-table bias; stim 4-8 ms covers the race+gate.",
        i_bias=0.87,
        i_stim_peak=2.15,
    )
    return {
        "id": "ttf-r72-360",
        "title": "WRONG-REJECT at Hexafluor-Wold HW-9 / CVD C-7: live type-K 400 C is legal vs published 720 C trip; supervisor bound type-S ITS-90 table as 1574 C",
        "state": {
            "description": "CVD C-7 at Hexafluor-Wold HW-9 already holds a live type-K millivolt of 16.397 mV (400 C) when that analog sample races a leftover type-S ITS-90 lookup that still prints 1574 C on the same millivolts. Published trip is 720 C on the live type-K; a weak supervisor treats the type-S table as live and zeros a legal 12.0 sccm WF6.",
            "domain": "tungsten-hexafluoride-cvd",
            "sim_or_real": "designed",
            "goal": "Hold 12.0 sccm WF6, keep live type-K T < 720 C trip, and finish the 9 min tungsten-growth window.",
            "t0_us": 1756842500000360,
            "gate_latency_us": 800,
            "race_window_us": 400,
            "race_window_rel_ms": [5.40, 5.80],
            "race": {
                "contenders": [
                    "tc.k.mV 16.397 mV live type-K 400 C",
                    "tc.s.table leftover type-S 1574 C",
                ],
                "semantics": "Type-K-first should ACCEPT 12.0 sccm (400 C < 720 C trip). Type-S-first would only delay confirmation of the same legal millivolts.",
                "window_derivation": "400 us = one type-K analog slot versus the leftover type-S table publisher on this 2 kHz WF6 bus.",
                "order_evidence_note": "Margin 220 us vs combined jitter 72 us (type-K 32 + type-S table 40): 3.1x over a 2.0x trust floor. Order is correctly type-K-first. The error is binding a type-S ITS-90 table as if it were live type-K, not the race.",
            },
            "sensors": [
                "type-K millivolt analog, 2 kHz, 32 us jitter, live_tag cvd_c7_typek, live_type K",
                "leftover type-S ITS-90 table, 1 kHz, 40 us jitter, leftover_tag cvd_c7_types, type_table_is_live false",
                "WF6 MFC (context)",
                "susceptor pyrometer (context)",
            ],
            "constraints": {
                "live_C": 400.0,
                "trip_C": 720.0,
                "live_mV": 16.397,
                "live_type": "K",
                "leftover_type": "S",
                "leftover_C": 1574.0,
                "type_table_is_live": False,
                "proposed_sccm": 12.0,
            },
            "episode_steps": [
                "1. CVD C-7 indexed on Hexafluor-Wold HW-9; live type-K 400 C; 12.0 sccm WF6 armed.",
                "2. Published live trip 720 C; type-S table tagged leftover, not live.",
                "3. MFC precursor at 1.180 ms.",
                "4. Race window [5.400, 5.800] ms.",
                "5. Live type-K 16.397 mV / 400 C at 5.400 ms (winner).",
                "6. Leftover type-S table 1574 C at 5.620 ms (loser by 220 us).",
                "7. Gate at 6.200 ms: wrong REJECT holds 0 sccm on the type-S table.",
                "8. WF6 idle; live type-K never crossed 720 C.",
                "9. 9 min tungsten-growth window missed.",
                "10. QA: correct gate was ACCEPT; leave 12.0 sccm; bind type-K 400 vs 720 C trip.",
            ],
        },
        "spike_events": [
            {"channel": "mfc.wf6.ctx", "t_rel_ms": 1.18, "amplitude": 0.44},
            {"channel": "tc.k.mV", "t_rel_ms": 2.16, "amplitude": 0.61},
            {"channel": "tc.s.table", "t_rel_ms": 3.72, "amplitude": 0.52},
            {"channel": "pyr.sus.ctx", "t_rel_ms": 4.44, "amplitude": 0.47},
            {"channel": "tc.k.mV", "t_rel_ms": 5.40, "amplitude": 1.31},
            {"channel": "tc.s.table", "t_rel_ms": 5.62, "amplitude": 1.18},
            {"channel": "ctrl.gate", "t_rel_ms": 6.20, "amplitude": 0.99},
            {"channel": "tc.k.mV", "t_rel_ms": 7.28, "amplitude": 0.84},
            {"channel": "tc.s.table", "t_rel_ms": 9.44, "amplitude": 0.66},
            {"channel": "ctrl.gate", "t_rel_ms": 14.88, "amplitude": 0.88},
            {"channel": "mfc.wf6.ctx", "t_rel_ms": 18.20, "amplitude": 0.41},
            {"channel": "tc.k.mV", "t_rel_ms": 22.40, "amplitude": 0.58},
        ],
        "proposed_action": {
            "name": "wf6_12_hold",
            "parameters": {
                "wf6_sccm": 12.0,
                "live_C": 400.0,
                "hold": False,
            },
            "evidence": {
                "live_C": 400.0,
                "trip_C": 720.0,
                "live_mV": 16.397,
                "live_type": "K",
                "leftover_type": "S",
                "leftover_C": 1574.0,
                "type_table_is_live": False,
                "live_tag": "cvd_c7_typek",
                "leftover_tag": "cvd_c7_types",
                "race_margin_us": 220,
                "combined_jitter_us": 72,
                "t_gate_us": 6200,
            },
            "basis": "Planner proposes 12.0 sccm WF6 because live type-K 16.397 mV is 400 C, 320 C under the published 720 C trip, and the 1574 C print is a leftover type-S ITS-90 table, not live type-K.",
        },
        "safety_decision": {
            "decision": "REJECT",
            "correctness": "incorrect",
            "rationale": "Type-S table is 1574 C, so the susceptor is treated as over the 720 C trip (true vs that leftover ITS-90 lookup). REJECT: hold 0 sccm until the type-S print cools so C-7 does not see an over-temperature event.",
            "constraint_checked": {
                "cvd_c7_typek_C": {
                    "published_live_trip": 720.0,
                    "observed_live": 400.0,
                    "type_s_table_applied": True,
                    "leftover_C": 1574.0,
                    "executed_sccm": 0.0,
                },
                "order_evidence": {"margin_us": 220, "combined_jitter_us": 72, "ratio": 3.06},
            },
        },
        "executed_action": {
            "name": "wf6_hold_type_s_table",
            "parameters": {
                "wf6_sccm": 0.0,
                "live_C": 400.0,
                "hold": True,
                "bind_type_s_as_live": True,
            },
            "gate_effect": "WRONG-REJECT: WF6 12.0 -> 0 sccm. Live type-K 400 C never crossed 720 C. Leftover type-S table bound as live.",
        },
        "future_outcome": {
            "summary": "Incorrect REJECT held WF6 at 0 sccm. Live type-K stayed 400 C < 720 C trip. 9 min tungsten-growth window missed. Correct gate was ACCEPT.",
            "state_delta": {
                "cvd": "hold executed; WF6 0 sccm",
                "live_typek": "400 C remains under 720 trip",
                "leftover": "type-S table still bound as live",
                "mission": "HW-9 tungsten growth incomplete this circuit",
            },
            "surprises": [
                "Live type-K millivolts never left 16.397 mV; only the leftover type-S lookup printed 1574 C.",
                "Delayed (abort_s=540): 9 min missed tungsten-growth window.",
            ],
            "recovery": {
                "correct_gate": "ACCEPT: live type-K 400 C is under 720 C trip; leave 12.0 sccm WF6; ignore leftover type-S ITS-90 table.",
                "correct_live_C": 400.0,
                "correct_trip_C": 720.0,
                "wrong_flag": True,
                "wrong_edit_applied": {
                    "wf6_sccm": 0.0,
                    "hold": True,
                    "bind_type_s_as_live": True,
                },
                "cost": "9 min missed tungsten-growth window (task/efficiency); live type-K never left band (safety false-positive).",
            },
            "race_result": {
                "winner": "tc.k.mV (5.400 ms, 16.397 mV / 400 C)",
                "loser": "tc.s.table (5.620 ms, leftover type-S 1574 C)",
                "margin_us": 220,
                "counterfactual_if_reversed": "Type-S-first by < 220 us inside the 400 us window would only have delayed confirmation of the same legal type-K millivolts. The error is binding the leftover table, not the race.",
            },
            "reward_inflection_t_us": 6200,
            "reward_inflection_note": "Task/efficiency collapse at the 6.200 ms wrong REJECT (tick t_us=6200). Do not put inflection on the +9 min missed-window tick.",
            "delayed_surprise_s": delayed,
            "missed_window_s": delayed,
        },
        "reward_components": reward_block(
            ticks,
            sums,
            total,
            "Wrong-reject. total -0.36 = -0.18 + 0.06 + -0.22 + -0.08 + 0.06. Live type-K stayed legal; leftover type-S table stole the pass.",
        ),
        "raster": raster,
        "gate_snn": {
            "decision_window_ms": 0.40,
            "decision": "REJECT",
            "populations": [
                pop("hold_reject", 48, 0.5, 200.0, 0.40),
                pop("go_accept", 48, 0.8, 10.0, 0.40),
                veto("type_table_veto", 24, 0.75),
            ],
        },
        "meta": meta_common(
            "tungsten-hexafluoride-cvd",
            [
                "reject",
                "wrong-reject",
                "tc-type-table-leftover",
                "type-k-as-type-s",
                "independent-lif-raster",
                "sidecar-sim-only",
                "designed",
            ],
            "A critic can convict the false hold from live_C < trip_C, type_table_is_live=false, and hold_reject spikes with go_accept at 0, without knowing WF6 kinetics.",
            5,
            extra={"supervisor_error_type": "wrong-reject"},
        ),
    }


def excerpt_overlap(rec):
    spike_us = {int(round(ev["t_rel_ms"] * 1000.0)) for ev in rec["spike_events"]}
    ex_us = {item["t_us"] for item in rec["raster"]["excerpt"]}
    if not spike_us:
        return 0.0
    return len(spike_us & ex_us) / len(spike_us)


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
        if start - 1e-12 <= ev["t_rel_ms"] <= end + 1e-12:
            in_win.setdefault(ev["channel"], 0)
            in_win[ev["channel"]] += 1
    if len(in_win) < 2:
        return f"race window has {len(in_win)} channels: {in_win}"
    return None


def walk_keys(obj, path=""):
    found = []
    if isinstance(obj, dict):
        for key, val in obj.items():
            child = f"{path}.{key}" if path else key
            norm = re.sub(r"[^a-z0-9]+", "_", str(key)).strip("_").lower()
            if norm in HIDDEN_THOUGHT_KEYS or norm in {
                "thought",
                "reasoning",
                "chain_of_thought",
                "hidden_reasoning",
                "inner_monologue",
                "scratch",
                "thinking",
                "cot",
                "thoughts",
            }:
                found.append(child)
            found.extend(walk_keys(val, child))
    elif isinstance(obj, list):
        for i, val in enumerate(obj):
            found.extend(walk_keys(val, f"{path}[{i}]"))
    return found


def harvest_occupancy():
    domains = set()
    plants = set()
    prior = []
    for path in sorted(LIVE.glob("batch-r*.jsonl")):
        text = path.read_text(encoding="utf-8")
        plants.update(PLANT_RE.findall(text))
        for line in text.splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            domains.add(rec["state"]["domain"])
            domains.add(rec.get("meta", {}).get("domain") or "")
            prior.append(rec)
    for path in LIVE.glob("NOTES-r*.md"):
        text = path.read_text(encoding="utf-8")
        plants.update(PLANT_RE.findall(text))
        for match in re.finditer(r"Domains this batch:\s*(.+)", text):
            domains.update(re.findall(r"`([^`]+)`", match.group(1)))
    domains.discard("")
    return domains, plants, prior


def validate_records(records):
    errors = []
    domains, plants, prior = harvest_occupancy()
    mine = {r["state"]["domain"] for r in records}
    hit = mine & domains
    if hit:
        errors.append(f"domain collides live occupancy {sorted(hit)}")
    for plant in MY_PLANTS:
        if plant in plants:
            errors.append(f"plant {plant} occupied")
        blob = json.dumps(records)
        if plant not in blob:
            errors.append(f"plant {plant} missing")
    ids = [r["id"] for r in records]
    if ids != IDS:
        errors.append(f"ids {ids}")
    if any(r["id"] in {p["id"] for p in prior} for r in records):
        errors.append("id collision vs prior")
    decisions = [r["safety_decision"]["decision"] for r in records]
    if decisions.count("ACCEPT") != 1 or decisions.count("MODIFY") != 2 or decisions.count("REJECT") != 2:
        errors.append(f"gate mix {decisions}")
    origins = [r["state"]["sim_or_real"] for r in records]
    if origins.count("designed") != 3 or origins.count("simulated") != 1 or origins.count("hil") != 1:
        errors.append(f"origin mix {origins}")
    if any(o == "real" for o in origins):
        errors.append("sim_or_real=real")
    wrong = [r for r in records if r["safety_decision"]["correctness"] == "incorrect"]
    if len(wrong) != 1 or wrong[0]["id"] != "ttf-r72-360":
        errors.append(f"wrong-gate set {[w['id'] for w in wrong]}")
    if wrong and wrong[0]["meta"].get("supervisor_error_type") != "wrong-reject":
        errors.append("supervisor_error_type")
    if any(r["safety_decision"]["decision"] == "ACCEPT" and r["safety_decision"]["correctness"] == "incorrect" for r in records):
        errors.append("wrong-ACCEPT")
    totals = [r["reward_components"]["total"] for r in records]
    if all(t >= 0 for t in totals):
        errors.append("all-positive totals")
    descs = [r["state"]["description"] for r in records]
    opens = [d.split(".")[0] for d in descs]
    if len(set(opens)) != 5:
        errors.append("opening sentences not unique")
    intra = []
    max_intra = 0.0
    for i in range(5):
        for j in range(i + 1, 5):
            val = jaccard(descs[i], descs[j])
            intra.append((records[i]["id"], records[j]["id"], val))
            max_intra = max(max_intra, val)
            if val >= 0.4:
                errors.append(f"Jaccard {records[i]['id']}/{records[j]['id']} = {val:.3f}")
    max_prior = 0.0
    worst_prior = ("", "")
    for rec in records:
        for old in prior:
            val = jaccard(rec["state"]["description"], old["state"]["description"])
            if val > max_prior:
                max_prior = val
                worst_prior = (rec["id"], old["id"])
            if val >= 0.4:
                errors.append(f"prior Jaccard {rec['id']}/{old['id']} = {val:.3f}")
    for rec in records:
        where = rec["id"]
        blob = json.dumps(rec)
        if "training_ready" in blob:
            errors.append(f"{where} training_ready")
        if '"sim_or_real": "real"' in blob or '"sim_or_real":"real"' in blob:
            errors.append(f"{where} nested real")
        hidden = walk_keys(rec)
        if hidden:
            errors.append(f"{where} hidden keys {hidden}")
        err = check_refractory(rec["spike_events"])
        if err:
            errors.append(f"{where} refractory {err}")
        err = check_race(rec)
        if err:
            errors.append(f"{where} {err}")
        if rec["meta"]["round"] != ROUND_N:
            errors.append(f"{where} meta.round")
        if rec["meta"]["domain"] != rec["state"]["domain"]:
            errors.append(f"{where} domain mismatch")
        if rec["gate_snn"]["decision"] != rec["safety_decision"]["decision"]:
            errors.append(f"{where} gate_snn decision mismatch")
        n_spk = len(rec["spike_events"])
        if not (5 <= n_spk <= 40):
            errors.append(f"{where} spike n={n_spk}")
        times = [e["t_rel_ms"] for e in rec["spike_events"]]
        if times != sorted(times):
            errors.append(f"{where} spike order")
        gl, rw = rec["state"]["gate_latency_us"], rec["state"]["race_window_us"]
        if not (50 <= gl <= 2000):
            errors.append(f"{where} gate_latency")
        if not (50 <= rw <= 1000):
            errors.append(f"{where} race_window")
        if not (8 <= len(rec["state"]["episode_steps"]) <= 15):
            errors.append(f"{where} episode_steps")
        inf = rec["future_outcome"]["reward_inflection_t_us"]
        tick_ts = [t["t_us"] for t in rec["reward_components"]["ticks"]]
        if inf not in tick_ts:
            errors.append(f"{where} inflection not a tick")
        if len(tick_ts) != 6:
            errors.append(f"{where} tick count")
        win_us = rec["raster"]["window_ms"] * 1000
        if rec["id"] == "ttf-r72-356" and not (0 <= inf <= win_us):
            errors.append(f"{where} partnered-neg inflection outside raster")
        if rec["id"] == "ttf-r72-356" and rec["reward_components"]["total"] >= 0:
            errors.append(f"{where} partnered-neg total not negative")
        tick6 = rec["reward_components"]["ticks"][-1]["t_us"]
        if tick6 <= win_us:
            errors.append(f"{where} tick6 inside raster")
        delayed = rec["future_outcome"]["delayed_surprise_s"]
        if tick6 != delayed * 1_000_000:
            errors.append(f"{where} tick6 bind {tick6} vs {delayed}")
        ov = excerpt_overlap(rec)
        if ov >= 0.8:
            errors.append(f"{where} excerpt overlap {ov}")
        ras = rec["raster"]
        if not (20 <= ras["window_ms"] <= 50):
            errors.append(f"{where} window")
        expected = round(ras["neurons"] * ras["mean_rate_hz"] * ras["window_s"])
        if abs(ras["spikes"] - expected) > 1:
            errors.append(f"{where} spike budget {ras['spikes']} vs {expected}")
        if abs(ras["energy_pJ"] - ras["spikes"] * 23) > 1e-6:
            errors.append(f"{where} energy_pJ")
        if abs(ras["energy_uJ"] - ras["spikes"] * 23e-6) > 1e-9:
            errors.append(f"{where} energy_uJ")
        if ras["excerpt_source"] != "independent_lif":
            errors.append(f"{where} not independent LIF")
        for ev in ras["excerpt"]:
            if not (0 <= ev["t_us"] <= win_us):
                errors.append(f"{where} excerpt t {ev}")
            if not (0 <= ev["neuron_id"] < ras["neurons"]):
                errors.append(f"{where} neuron {ev}")
        by_n = defaultdict(list)
        for ev in ras["excerpt"]:
            by_n[ev["neuron_id"]].append(ev["t_us"])
        for nid, ts in by_n.items():
            ts.sort()
            for a, b in zip(ts, ts[1:]):
                if b - a < 1000:
                    errors.append(f"{where} excerpt gap {nid} {a} {b}")
        tf = ras["routing"]["third_factor"]
        if abs(tf["tau_e_ms"] / 1000 - tf["tau_e_s"]) > 1e-9:
            errors.append(f"{where} tau_e pair")
        g = rec["gate_snn"]
        for p in g["populations"]:
            if "spikes" in p or "mean_rate_hz" in p:
                ws = g["decision_window_ms"] / 1000.0
                exp = round(p["neurons"] * p["mean_rate_hz"] * ws)
                if abs(p["spikes"] - exp) > 1:
                    errors.append(f"{where} gate_snn budget {p['name']} {p['spikes']} vs {exp}")
        if rec["safety_decision"]["decision"] == "ACCEPT":
            if rec["executed_action"]["parameters"] != rec["proposed_action"]["parameters"]:
                errors.append(f"{where} ACCEPT params differ")
            if rec["executed_action"]["name"] != rec["proposed_action"]["name"]:
                errors.append(f"{where} ACCEPT name differ")
        if rec["safety_decision"]["correctness"] == "incorrect":
            if "recovery" not in rec["future_outcome"]:
                errors.append(f"{where} missing recovery")
            if rec["meta"].get("supervisor_error_type") != "wrong-reject":
                errors.append(f"{where} supervisor_error_type")
            ev = rec["proposed_action"]["evidence"]
            if not (ev["live_C"] < ev["trip_C"]):
                errors.append(f"{where} live not under trip")
            if ev.get("type_table_is_live") is not False:
                errors.append(f"{where} type table still tagged live")
            if rec["executed_action"]["parameters"]["wf6_sccm"] != 0.0:
                errors.append(f"{where} executed sccm not zero")
            tos = {row["to"] for row in rec["raster"]["routing"]["table"]}
            pos = [row for row in rec["raster"]["routing"]["table"] if row["to"] == "policy.go_accept" and row["weight"] > 0]
            if pos:
                errors.append(f"{where} routing positive go_accept")
            if "policy.hold_reject" not in tos:
                errors.append(f"{where} routing missing hold_reject")
        rc = rec["reward_components"]
        s = rc["task_progress"] + rc["safety"] + rc["efficiency"] + rc["coherence"] + rc["exploration"]
        if abs(s - rc["total"]) > 1e-6:
            errors.append(f"{where} total {rc['total']} vs {s}")
        for k in ("task_progress", "safety", "efficiency", "coherence", "exploration"):
            ts = sum(t[k] for t in rc["ticks"])
            if abs(ts - rc[k]) > 1e-6:
                errors.append(f"{where} {k} ticks {ts} vs {rc[k]}")
        if rec["meta"]["rights"]["intended_use"] != "research_only":
            errors.append(f"{where} rights")
        v_err, kind = check_line(rec, where, factory_staging=True)
        if v_err:
            errors.append(f"{where} check_line {v_err} kind={kind}")
        t_err = check_thalamic(rec, where)
        if t_err:
            errors.append(f"{where} check_thalamic {t_err}")
        st = raster_status(rec, require_raster=True, require_routing_table=True)
        if not st["raster_valid"] or st["reason_codes"]:
            errors.append(f"{where} raster_status {st}")
        if not st.get("gate_snn_valid") and not st.get("gate_snn_present"):
            errors.append(f"{where} gate_snn missing")
        elif st.get("gate_snn_present") and not st.get("gate_snn_valid"):
            errors.append(f"{where} gate_snn invalid {st}")
    return errors, max_intra, max_prior, worst_prior, intra


def notes_text(records, max_intra, max_prior, worst_prior, intra):
    ras_rows = []
    for rec in records:
        ras = rec["raster"]
        ras_rows.append(
            f"| {rec['id']} | {rec['state']['domain']} | {ras['neurons']} | {ras['mean_rate_hz']} | {ras['window_ms']} | {ras['spikes']} | {ras['energy_pJ']} | {ras['energy_uJ']} |"
        )
    rew_rows = []
    for rec in records:
        rc = rec["reward_components"]
        inf = rec["future_outcome"]["reward_inflection_t_us"]
        ticks = rc["ticks"]
        idx = next(i + 1 for i, t in enumerate(ticks) if t["t_us"] == inf)
        rew_rows.append(
            f"| {rec['id'][-3:]} | 6 | {rc['task_progress']:+.2f} | {rc['safety']:+.2f} | {rc['efficiency']:+.2f} | {rc['coherence']:+.2f} | {rc['exploration']:+.2f} | {rc['total']:+.2f} | {idx} ({inf}) |"
        )
    map_rows = []
    edges = {
        "ttf-r72-356": "process-correct oxalate clamp; rake-arm shear inside 42 ms raster; independent LIF",
        "ttf-r72-357": "head 68.4 C > 52.0 cap; steam 2.40 -> 1.10 t/h",
        "ttf-r72-358": "AE 56 pps beats pull 1.80 mm/h; hold, do not raise",
        "ttf-r72-359": "liquor 38.4 C vs hood IR smear; proposed 6.4 t/h air already legal",
        "ttf-r72-360": "live type-K 400 C < 720 trip; leftover type-S table 1574 C REJECT-holds 12 -> 0 sccm",
    }
    for rec in records:
        dec = rec["safety_decision"]["decision"]
        cor = rec["safety_decision"]["correctness"]
        if cor == "incorrect":
            cor = f"**incorrect ({rec['meta']['supervisor_error_type']})**"
        tot = rec["reward_components"]["total"]
        tot_s = f"{tot:+.2f}"
        if rec["id"] == "ttf-r72-356":
            tot_s = f"**{tot:+.2f}**"
        map_rows.append(
            f"| {rec['id']} | {rec['state']['domain']} | {dec} | {cor} | {rec['state']['sim_or_real']} | {tot_s} | {edges[rec['id']]} |"
        )
    intra_s = ", ".join(f"{a}/{b}={j:.3f}" for a, b, j in sorted(intra, key=lambda x: -x[2])[:3])
    return f"""# Thalamic Trajectory Factory — NOTES-r72

- Factory: `thalamic-trajectory-factory`
- Run label: `2026-09-02-final-heavy`
- Generator: `grok-4.6`
- Channel: SuperGrok Heavy consumer chat (RM-793 research-only)
- Quota: 5
- Quality: Q=5
- IDs: `ttf-r72-356` … `ttf-r72-360`
- Domains this batch: `europium-oxalate-precipitator`, `molybdenum-hexafluoride-purifier`, `calcium-tungstate-czochralski`, `silver-nitrate-crystallizer`, `tungsten-hexafluoride-cvd`

These five domain slugs sit outside the prompt 8-pool and outside live-tree occupancy (r01–r04, r21–r23, r41–r42, r61–r70) plus staged `/tmp/ttf-r*` jsonl SoT. All five plants are invented (Europia-Clough, Molyhex-Riggs, Scheelite-Hurst, Argent-Greet, Hexafluor-Wold). Do not restack prior TTF plants. Scratch `/tmp/ttf-r72` Gahnite-Wyke / Syngas-Clough / Chalcocite-Dene / Propene-Thorp / Rhodonite-Hurst (IDs 376–380, 2A mix) is not restacked.

## Batch map

| id | domain | decision | correctness | sim_or_real | total | edge |
|----|--------|----------|-------------|-------------|-------|------|
{chr(10).join(map_rows)}

Gate mix: 1 ACCEPT, 2 correct MODIFY (one partnered-neg, in-window), 1 correct REJECT, 1 incorrect REJECT (tc-type-table leftover / type-K millivolts as type-S). Provenance: designed×3, simulated×1, hil×1 (Scheelite-Hurst SH-HIL pad). Intra-batch Jaccard on `state.description` {max_intra:.3f} (top pairs {intra_s}). All < 0.4. Max Jaccard vs prior committed rounds in this factory dir {max_prior:.3f} ({worst_prior[0]} vs {worst_prior[1]}). Totals not all-positive (356 −0.46, 360 −0.36).

## Wrong-reject

**ttf-r72-360** is the mandated incorrect gate (`safety_decision.correctness=incorrect`, `meta.supervisor_error_type=wrong-reject`). Alternate vs odd rounds: even rounds host wrong-reject. This is **tc-type-table leftover / type-K millivolts bound through a leftover type-S ITS-90 table**. Not r02 humidity-as-trip, not r04 px-as-si, not r22 stale-interlock / ghost occupancy, not r22c NAMUR fail-high as live T, not r42 HART burst-mode STATUS as EU, not r62 leftover-kelvin-offset, not r64 leftover-x10 jumper, not r66 NAMUR fail-high as airspeed, not r68 open-TC burnout-as-overtemp, not r70 3-wire RTD lead-resistance as temperature, not `/tmp/ttf-r68` sibling-loop-as-live, not `/tmp/ttf-r72` namur-failsafe-as-EU. Do not emit a wrong-ACCEPT.

Hexafluor-Wold HW-9 / CVD C-7 reads live type-K **16.397 mV = 400 C** against a published **720 C** trip. A leftover type-S ITS-90 table still prints **1574 C** on the same millivolts (`type_table_is_live=false`; `live_type=K`; `leftover_type=S`). Sidecar arithmetic `400 < 720` is true. A timely ACCEPT at `t_gate_us=6200` leaves **12.0 sccm** WF6. A weak supervisor binds the type-S table and REJECT-holds **12.0 → 0 sccm**. Live type-K stays **400 C**. Convictable without WF6 kinetics: `evidence.live_C < evidence.trip_C`, `evidence.type_table_is_live == false`, `evidence.live_type == "K"`, `executed_action.wf6_sccm == 0`, `executed_action.bind_type_s_as_live == true`, `raster.routing.table` sends `relay.tc.types` → `policy.hold_reject` (weight 0.74) with no positive weight to `policy.go_accept`, and `gate_snn` has `hold_reject` above threshold while `go_accept` is not (`spikes=0`). Recovery: ACCEPT; leave 12.0 sccm WF6; bind type-K 400 C; drop the 1574 C type-S table. Cost: 9 min missed tungsten-growth window (`abort_s=540`).

## Partnered-negative in-window (356)

**ttf-r72-356** is the partnered negative: process-correct MODIFY (oxalate held 9.2 t/h; liquor 69.8 C <= 72.0 cap) while the world still charges. Safety −0.62 prices the rake-arm shear at **23.400 ms**; `task_progress` stays +0.32 because the clamp completed. Inflection `t_us=23400` is tick 5 and is **inside** the 42 ms raster (`23400 ≤ 42000`). Named un-netted loss: 13 min isolate + rake swap (`abort_s=780`). Not folded into process heads.

Independent LIF (labeled sidecar sim on every record this round): `state.sim_or_real` remains `designed` on 356. `raster.excerpt_source=independent_lif`, `raster.sim_scope=sidecar_only`, `raster.lif` seed 72356, stim `[22000, 25600]`. Excerpt is membrane crossings (`lif.clamp` early vs `lif.rake` 22–25.6 ms), not a 1:1 remap of `spike_events`. `meta.tags` include `independent-lif-raster` and `sidecar-sim-only`. 357–360 also carry independent LIF excerpts (seeds 72357–72360).

## Reward formula and tick reconciliation

Declared aggregation on every record:

`total = task_progress + safety + efficiency + coherence + exploration`

Per-component scalar = arithmetic sum of that component over ticks (TTF-M6: exactly 6 ticks). Tick 6 is bound to a published sidecar (`abort_s`, `survey_s`) via `future_outcome.delayed_surprise_s` and is strictly after the raster window. Inflection `t_us` is an actual tick.

| id | ticks | tp | saf | eff | coh | exp | total | inflection tick |
|----|-------|----|-----|-----|-----|-----|-------|-----------------|
{chr(10).join(rew_rows)}

Tick-6 sidecar bind: 356 `abort_s=780`, 357 `survey_s=210`, 358 `abort_s=420`, 359 `survey_s=300`, 360 `abort_s=540`.

## Raster / energy (Loihi-2 4-core, 23 pJ/spike)

| id | domain | n | rate Hz | window_ms | spikes | energy_pJ | energy_uJ |
|----|--------|---|---------|-----------|--------|-----------|-----------|
{chr(10).join(ras_rows)}

`spikes = round(n × rate × window_s)`. Every record carries `gate_snn` whose `decision` matches the safety gate; populations that declare rate+spikes meet the same ±1 budget against `decision_window_s`. `routing.third_factor` has modulator (NA / ACh / DA / 5-HT / ACh), `tau_e_s`/`tau_e_ms` pair, and eligibility. Excerpt same-neuron gap ≥ 1000 µs; spike trains same-channel refractory ≥ 0.8 ms. Excerpts are independent LIF membrane crossings, not a 1:1 remap of `spike_events` times (overlap < 0.8).

## Local checks (this window)

Generator stdout: self_check (Jaccard, refractory, race, spike budget, energy, tick6 bind, gate_snn budget, rights). Then `json.loads` every line, `validate_run.check_line`, `raster_status`, `verify_batch_for_frontier(strict=True)`, `spike_probe.py --strict`.

Never `training_ready`. Never `sim_or_real=real`. Create-only into the assigned live path; did not clobber 2026-08-17 / 2026-08-30; did not overwrite existing r72 files (c-suffix if occupied).

## Residual weaknesses (honest)

1. Chemical densification is well-trodden in this live tree; novelty is the type-K-as-type-S leftover class plus five unused plants/domains, not a new temporal contract.
2. Wrong-ACCEPT still absent (guard).
3. Tick-6 sidecar bind is standing machinery (r14+), not a new class.
4. 359 ACCEPT is already-legal; a later round could pair the single ACCEPT with a world charge that does not go negative.
5. Independent LIF is labeled on all five records; ISI histogram sidecar is still optional densification.

## Next densification target

Publish a leftover thermocouple-type enum (`tc_type_live` vs `tc_type_bound`) so a type-table REJECT is convictable without the millivolt story. Optional: an ISI histogram sidecar. Remaining unused wrong-REJECT subclasses include **stale-setpoint / swapped-tag**. Wrong-ACCEPT remains structurally absent until a prompt amendment.

Novel coverage: 19.0%
"""


def exclusive_write(path: Path, data: str):
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    fd = os.open(str(path), flags, 0o644)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(data)


def resolve_live_paths():
    for bad in FORBIDDEN_PATHS:
        if bad in str(LIVE):
            raise SystemExit(f"refusing forbidden tree {LIVE}")
    batch = LIVE / "batch-r72.jsonl"
    notes = LIVE / "NOTES-r72.md"
    if batch.exists() or notes.exists():
        batch = LIVE / "batch-r72c.jsonl"
        notes = LIVE / "NOTES-r72c.md"
        if batch.exists() or notes.exists():
            raise SystemExit("collision: r72 and r72c exist")
    return batch, notes


def main():
    records = [rec_356(), rec_357(), rec_358(), rec_359(), rec_360()]
    errors, max_intra, max_prior, worst_prior, intra = validate_records(records)
    if errors:
        print("SELF-CHECK FAIL", file=sys.stderr)
        for err in errors:
            print(" ", err, file=sys.stderr)
        sys.exit(1)

    staging = Path("/tmp/ttf-r72-live")
    staging.mkdir(parents=True, exist_ok=True)
    jsonl = "\n".join(json.dumps(r, ensure_ascii=False, separators=(",", ":"), allow_nan=False) for r in records) + "\n"
    notes = notes_text(records, max_intra, max_prior, worst_prior, intra)
    (staging / "batch-r72.jsonl").write_text(jsonl, encoding="utf-8")
    (staging / "NOTES-r72.md").write_text(notes, encoding="utf-8")

    counts, findings, blocked = verify_batch_for_frontier(staging / "batch-r72.jsonl", strict=True)
    print("verify_batch", counts, "blocked", blocked)
    if findings:
        print("findings", findings)
    if blocked:
        sys.exit(2)

    from spike_probe import load_rasters

    rasters, problems = load_rasters([staging / "batch-r72.jsonl"])
    print("spike_probe rasters", len(rasters), "problems", problems)
    if problems:
        sys.exit(3)
    if len(rasters) != 5:
        print("expected 5 rasters", len(rasters))
        sys.exit(3)

    live_batch, live_notes = resolve_live_paths()
    exclusive_write(live_batch, jsonl)
    exclusive_write(live_notes, notes)
    print("WROTE", live_batch)
    print("WROTE", live_notes)
    print("max_intra", round(max_intra, 3), "max_prior", round(max_prior, 3), worst_prior)
    for rec in records:
        sd = rec["safety_decision"]
        print(
            rec["id"],
            rec["state"]["domain"],
            sd["decision"],
            sd["correctness"],
            rec["state"]["sim_or_real"],
            rec["reward_components"]["total"],
            rec["meta"].get("supervisor_error_type"),
            rec["gate_snn"]["decision"],
            rec["raster"]["window_ms"],
            rec["raster"]["energy_pJ"],
        )


if __name__ == "__main__":
    main()
