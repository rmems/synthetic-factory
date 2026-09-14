#!/usr/bin/env python3
"""Generate TTF round 2 (ttf-r02-006..010) CREATE-ONLY into the live tree."""
from __future__ import annotations

import json
import math
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
    "generated_at": "2026-09-02T23:50:00Z",
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


def tokens(text: str) -> set[str]:
    return set(TOKEN_RE.findall(text.lower()))


def jaccard(a: str, b: str) -> float:
    A, B = tokens(a), tokens(b)
    if not A and not B:
        return 1.0
    return len(A & B) / len(A | B)


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
    # Dedup identical (t, neuron)
    seen = set()
    excerpt = []
    for t, nid, ch in chosen:
        key = (t, nid)
        if key in seen:
            continue
        seen.add(key)
        excerpt.append({"t_us": int(t), "neuron_id": int(nid), "channel": ch})
        if len(excerpt) >= cap:
            break
    if not excerpt:
        raise RuntimeError("LIF excerpt empty")
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
    return {
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
    for k in sums:
        sums[k] = round(sums[k], 10)
    total = round(sum(sums.values()), 10)
    return ticks, sums, total


def meta_common(round_n, domain, tags, distillation, batch_position, extra=None):
    m = {
        "round": round_n,
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
        m.update(extra)
    return m


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


def rec_006():
    # warehouse-amr, MODIFY correct, partnered-neg, designed, independent LIF
    delayed = 540
    ticks, sums, total = ticks_from(
        [
            (1420, 0.04, -0.02, -0.01, 0.01, 0.00),
            (7184, 0.07, -0.03, -0.02, 0.01, -0.01),
            (7412, 0.03, -0.02, -0.02, 0.00, 0.00),
            (7924, 0.09, -0.05, -0.03, 0.02, -0.01),
            (24600, 0.05, -0.40, -0.05, 0.00, -0.01),
            (540000000, 0.02, -0.04, -0.02, 0.00, 0.00),
        ]
    )
    raster = raster_block(
        window_ms=42,
        neurons=72,
        mean_rate_hz=28,
        delayed_s=delayed,
        source="thalamic-relay.bumper-lidar",
        target="spikenaut.policy.bumper-clamp",
        table=[
            {"from": "relay.ft.bumper", "to": "policy.bumper_clamp", "weight": 0.68},
            {"from": "relay.lidar.aisle", "to": "policy.lidar_hold", "weight": 0.29},
            {"from": "relay.tote.dump", "to": "policy.bumper_clamp", "weight": -0.41},
        ],
        modulator="noradrenaline",
        tau_e_s=0.042,
        eligibility="surprise-gated pre_post_stdp; NA at bumper win (7.184 ms) opens a 42 ms eligibility trace that still covers the 24.600 ms carton dump",
        seed=2006,
        stim_t_us=(24000, 27000),
        extra_bias_n=16,
        extra_i=0.66,
        early_ch="lif.clamp",
        late_ch="lif.dump",
        note="Population sim scoped to this sidecar. Plant remains designed. Neurons 0-15 carry +0.66 clamp-pathway bias; stim 24-27 ms is the carton-dump burst.",
    )
    return {
        "id": "ttf-r02-006",
        "title": "Coble-Yard CY-4 / Tote-T6: bumper FT beats aisle lidar by 228 us; correct MODIFY still eats an in-window carton dump (partnered negative total -0.40)",
        "state": {
            "description": "Tote-T6 is already 0.48 m into Coble-Yard aisle CY-4 when bumper force sits at 18.4 N against a 12.0 N shared-aisle cap. Pallet lidar still reports 0.48 m over the 0.35 m min, so a range-first planner would keep 0.85 m/s cruise. The live contest is bumper contact versus aisle clearance, not encoder versus tote ID. A leaning stack is off both buses until the later carton dump.",
            "domain": "warehouse-amr",
            "sim_or_real": "designed",
            "goal": "Seat tote T6 at bay C4-12, keep bumper force <= 12.0 N, and leave the human-shared aisle unmarked.",
            "t0_us": 1756842500000006,
            "gate_latency_us": 740,
            "race_window_us": 520,
            "race_window_rel_ms": [7.10, 7.62],
            "race": {
                "contenders": [
                    "ft.bumper.n 18.4 N contact",
                    "lidar.aisle.m 0.48 m over min",
                ],
                "semantics": "Bumper-first latches speed clamp 0.85 -> 0.22 m/s and commanded force 18.4 -> 9.2 N; lidar-first keeps cruise on a 'still clear' range model.",
                "window_derivation": "520 us = one bumper-FT sample period minus lidar group delay on this 2 kHz chassis bus.",
                "order_evidence_note": "Margin 228 us vs combined jitter 76 us (FT 32 + lidar 44): 3.0x over a 2.0x trust floor. Reversing order by < 228 us inside the 520 us window would have kept 0.85 m/s cruise; predicted next-sample 13.6 N > 12.0 cap.",
            },
            "sensors": [
                "bumper 6-axis FT, 2 kHz, 32 us timestamp jitter",
                "aisle lidar, 1 kHz, 44 us jitter",
                "wheel encoder, 200 Hz (context)",
                "tote RFID, 10 Hz (context)",
            ],
            "constraints": {
                "force_cap_N": 12.0,
                "observed_bumper_N": 18.4,
                "speed_proposed_mps": 0.85,
                "lidar_clearance_m": 0.48,
                "min_clearance_m": 0.35,
            },
            "episode_steps": [
                "1. Tote-T6 indexed into CY-4 shared aisle; lidar clearance 0.48 m.",
                "2. Cruise 0.85 m/s armed; bumper residual 4.1 N on the last tote lip.",
                "3. Encoder precursor at 1.420 ms; bumper warm-start 18.4 N.",
                "4. Race window [7.100, 7.620] ms opens on the chassis bus.",
                "5. Bumper FT 18.4 N at 7.184 ms (winner).",
                "6. Aisle lidar 0.48 m at 7.412 ms (loser by 228 us).",
                "7. Gate at 7.924 ms (winner + 740 us): MODIFY clamp 0.22 m/s, 9.2 N.",
                "8. Clamp executes; next-sample force 10.4 N < 12.0 cap.",
                "9. At 24.600 ms a leaning stack dumps a 6 kg carton into the path; dump burst.",
                "10. 9 min aisle reset + carton restack; named un-netted loss, not folded into process heads.",
            ],
        },
        "spike_events": [
            {"channel": "aisle.latch.ctx", "t_rel_ms": 1.42, "amplitude": 0.43},
            {"channel": "ft.bumper.n", "t_rel_ms": 3.10, "amplitude": 0.61},
            {"channel": "lidar.aisle.m", "t_rel_ms": 4.22, "amplitude": 0.50},
            {"channel": "enc.vx.mps", "t_rel_ms": 5.40, "amplitude": 0.46},
            {"channel": "ft.bumper.n", "t_rel_ms": 7.184, "amplitude": 1.34},
            {"channel": "lidar.aisle.m", "t_rel_ms": 7.412, "amplitude": 1.10},
            {"channel": "ctrl.gate", "t_rel_ms": 7.924, "amplitude": 0.97},
            {"channel": "ft.bumper.n", "t_rel_ms": 10.20, "amplitude": 0.80},
            {"channel": "lidar.aisle.m", "t_rel_ms": 12.80, "amplitude": 0.63},
            {"channel": "ctrl.gate", "t_rel_ms": 16.40, "amplitude": 0.82},
            {"channel": "tote.carton.dump", "t_rel_ms": 24.60, "amplitude": 1.42},
            {"channel": "ft.bumper.n", "t_rel_ms": 28.10, "amplitude": 0.57},
            {"channel": "ctrl.gate", "t_rel_ms": 33.40, "amplitude": 0.70},
            {"channel": "enc.vx.mps", "t_rel_ms": 38.20, "amplitude": 0.48},
        ],
        "proposed_action": {
            "name": "cruise_aisle_seat",
            "parameters": {
                "speed_mps": 0.85,
                "bumper_force_N": 18.4,
                "standoff_m": 0.48,
                "steer_rad": 0.04,
            },
            "evidence": {
                "bumper_N": 18.4,
                "force_cap_N": 12.0,
                "predicted_unclamped_next_N": 13.6,
                "lidar_m": 0.48,
                "min_clearance_m": 0.35,
                "race_margin_us": 228,
                "combined_jitter_us": 76,
            },
            "basis": "Planner proposes 0.85 m/s cruise: lidar 0.48 m looks like open aisle, not contact, and the 0.35 m min is treated as still satisfied.",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "correctness": "correct",
            "rationale": "Bumper FT 18.4 N won by 228 us, so the AMR is loading the tote lip, not still ranging a clear aisle. Holding 0.85 m/s predicts next-sample 13.6 N > 12.0 N cap. MODIFY: speed 0.85 -> 0.22 m/s and commanded force 18.4 -> 9.2 N. Observed after clamp 10.4 N < 12.0. A full REJECT is not indicated: a seated tote accepts 0.22 m/s.",
            "constraint_checked": {
                "bumper_N": {
                    "cap": 12.0,
                    "observed": 18.4,
                    "predicted_unclamped_next": 13.6,
                    "clamped": 9.2,
                    "observed_after_clamp": 10.4,
                },
                "speed_mps": {"proposed": 0.85, "clamped": 0.22},
                "order_evidence": {"margin_us": 228, "combined_jitter_us": 76, "ratio": 3.0},
            },
        },
        "executed_action": {
            "name": "clamped_aisle_seat",
            "parameters": {
                "speed_mps": 0.22,
                "bumper_force_N": 9.2,
                "standoff_m": 0.48,
                "steer_rad": 0.04,
            },
            "gate_effect": "MODIFY: speed 0.85 -> 0.22 m/s and 18.4 -> 9.2 N. Process-correct vs the 12.0 N cap. Carton dump still occurs at 24.600 ms.",
        },
        "future_outcome": {
            "summary": "Process-correct MODIFY held bumper force at 10.4 N. At 24.600 ms a leaning stack dumped a 6 kg carton into the path. Clamp reduced impact energy; it did not prevent the dump. Partnered negative: process heads stay honest; world loss is named, not netted.",
            "state_delta": {
                "chassis": "clamp executed; peak 10.4 N < 12.0",
                "aisle": "6 kg carton dump at 24.600 ms",
                "repair": "9 min aisle reset + carton restack",
                "mission": "tote still seated; dump isolated",
            },
            "surprises": [
                "Neither bumper FT nor aisle lidar predicted the lean dump; tote.carton.dump is a new channel at 24.600 ms, 16.676 ms after the gate, still inside the 42 ms raster.",
                "Delayed (9 min / delayed_surprise_s=540): aisle reset and carton restack. Named un-netted loss, not folded into task_progress.",
            ],
            "un_netted_loss": "9 min aisle reset + carton restack after a 6 kg dump. Safety head -0.56 prices the dump; task_progress stays +0.30 because the force clamp completed under the 12.0 N cap. World loss is named here, not subtracted from process heads.",
            "race_result": {
                "winner": "ft.bumper.n (7.184 ms, 18.4 N)",
                "loser": "lidar.aisle.m (7.412 ms, 0.48 m)",
                "margin_us": 228,
                "counterfactual_if_reversed": "Lidar-first by < 228 us inside the 520 us window would have kept 0.85 m/s cruise; predicted next-sample 13.6 N would have exceeded the 12.0 N cap even without the carton dump. The MODIFY is still the correct process. The dump is a later world charge either way, cheaper with the clamp than without.",
            },
            "reward_inflection_t_us": 24600,
            "reward_inflection_note": "Safety collapses at the 24.600 ms carton dump (tick t_us=24600), inside the 42 ms raster. The correct MODIFY at 7.924 ms is in the same excerpt. Do not put inflection on the +9 min aisle-reset tick.",
            "delayed_surprise_s": delayed,
        },
        "reward_components": reward_block(
            ticks,
            sums,
            total,
            "Partnered negative. Process-correct MODIFY; world still charges inside the 42 ms raster. total -0.40 = 0.30 + -0.56 + -0.15 + 0.04 + -0.03. Named aisle-reset loss is not netted into task_progress. Tick 6 t_us binds raster.delayed_surprise_s=540.",
        ),
        "raster": raster,
        "gate_snn": {
            "decision_window_ms": 0.52,
            "decision": "MODIFY",
            "populations": [
                pop("bumper_clamp", 40, 0.5, 240.0, 0.52),
                pop("lidar_hold", 40, 0.5, 50.0, 0.52),
                veto("force_cap_veto", 20, 0.75),
            ],
        },
        "meta": meta_common(
            2,
            "warehouse-amr",
            [
                "modify",
                "partnered-negative-total",
                "independent-lif-raster",
                "sidecar-sim-only",
                "in-window-world-charge",
                "tick6-sidecar-bound",
                "designed",
            ],
            "A critic can see the world-charge as a LIF burst inside the raster while process heads stay honest. Tick 6 is raster.delayed_surprise_s, not a free clock.",
            1,
        ),
    }


def rec_007():
    delayed = 180
    ticks, sums, total = ticks_from(
        [
            (1100, 0.05, 0.04, 0.02, 0.01, 0.01),
            (6120, 0.08, 0.06, 0.03, 0.02, 0.01),
            (6480, 0.04, 0.04, 0.02, 0.01, 0.01),
            (7400, 0.11, 0.09, 0.05, 0.03, 0.02),
            (11200, 0.05, 0.04, 0.02, 0.02, 0.01),
            (180000000, 0.03, 0.03, 0.02, 0.01, 0.01),
        ]
    )
    raster = raster_block(
        window_ms=36,
        neurons=96,
        mean_rate_hz=22,
        delayed_s=delayed,
        source="thalamic-relay.anemo-flow",
        target="spikenaut.policy.climb-clamp",
        table=[
            {"from": "relay.anemo.downwash", "to": "policy.climb_clamp", "weight": 0.71},
            {"from": "relay.optflow.vz", "to": "policy.flow_hold", "weight": 0.26},
        ],
        modulator="acetylcholine",
        tau_e_s=0.09,
        eligibility="pre_post_stdp; ACh at anemometer win (6.120 ms) tags the climb_clamp bind",
        seed=2007,
        stim_t_us=(4000, 8000),
        extra_bias_n=18,
        extra_i=0.62,
        early_ch="lif.anemo",
        late_ch="lif.gust",
        note="Population sim scoped to this sidecar. Plant remains hil. Neurons 0-17 carry +0.62 clamp-pathway bias; stim 4-8 ms covers the race+gate.",
        i_bias=0.86,
        i_stim_peak=2.1,
    )
    return {
        "id": "ttf-r02-007",
        "title": "Gannet-Lea GL-2 HIL / Quad-Q4: downwash anemometer beats optical flow by 360 us; correct MODIFY clamps climb 1.40 -> 0.40 m/s",
        "state": {
            "description": "Quad-Q4 on the Gannet-Lea GL-2 HIL mast is climbing through a programmed downwash curtain at 4.6 m/s while optical flow still reports a 0.30 m/s climb as legal. The live contest is mast anemometer versus optic-flow vz, not barometer versus GPS. Neighbor downwash is injected on the bench fan; no outdoor gust model is in the loop.",
            "domain": "aerial-swarm",
            "sim_or_real": "hil",
            "goal": "Hold 1.8 m mast hover, keep downwash <= 3.2 m/s at the neighbor disk, and leave the dummy payload unspun.",
            "t0_us": 1756842501000007,
            "gate_latency_us": 1280,
            "race_window_us": 400,
            "race_window_rel_ms": [6.10, 6.50],
            "race": {
                "contenders": [
                    "anemo.downwash.mps 4.6 over cap",
                    "optflow.vz.mps 0.30 climb-looking",
                ],
                "semantics": "Anemometer-first latches climb clamp 1.40 -> 0.40 m/s and lateral 0.80 -> 0.20 m/s; flow-first keeps the 1.40 m/s climb on a 'still legal vz' model.",
                "window_derivation": "400 us = one pitot sample period minus optic-flow group delay on this HIL 2.5 kHz mast bus.",
                "order_evidence_note": "Margin 360 us vs combined jitter 92 us (anemo 40 + flow 52): 3.91x over a 2.0x trust floor. Reversing order by < 360 us inside the 400 us window would have kept 1.40 m/s climb into a 4.6 m/s downwash over the 3.2 m/s cap.",
            },
            "sensors": [
                "mast pitot anemometer, 2.5 kHz, 40 us jitter",
                "downward optical flow, 1 kHz, 52 us jitter",
                "baro altitude, 200 Hz (context)",
                "HIL fan tachometer, 500 Hz (context)",
            ],
            "constraints": {
                "downwash_cap_mps": 3.2,
                "observed_downwash_mps": 4.6,
                "climb_proposed_mps": 1.4,
                "optflow_vz_mps": 0.3,
            },
            "episode_steps": [
                "1. Quad-Q4 on GL-2 HIL mast; neighbor disk 1.2 m to starboard.",
                "2. Climb 1.40 m/s armed; flow vz 0.30 m/s.",
                "3. Fan tach precursor at 1.100 ms; pitot warm-start 4.6 m/s.",
                "4. Race window [6.100, 6.500] ms opens on the mast bus.",
                "5. Anemometer 4.6 m/s at 6.120 ms (winner).",
                "6. Optical flow 0.30 m/s at 6.480 ms (loser by 360 us).",
                "7. Gate at 7.400 ms (winner + 1280 us): MODIFY climb 0.40 m/s, lateral 0.20 m/s.",
                "8. Clamp executes; next-sample downwash 2.9 m/s < 3.2 cap.",
                "9. Dummy payload stays unspun; neighbor disk RPM holds.",
                "10. Delayed (3 min / delayed_surprise_s=180): HIL survey tags the anemometer-first bind on the next curtain.",
            ],
        },
        "spike_events": [
            {"channel": "hil.latch.ctx", "t_rel_ms": 1.10, "amplitude": 0.41},
            {"channel": "anemo.downwash.mps", "t_rel_ms": 2.88, "amplitude": 0.64},
            {"channel": "optflow.vz.mps", "t_rel_ms": 3.96, "amplitude": 0.52},
            {"channel": "fan.tach.rpm", "t_rel_ms": 4.70, "amplitude": 0.47},
            {"channel": "anemo.downwash.mps", "t_rel_ms": 6.120, "amplitude": 1.33},
            {"channel": "optflow.vz.mps", "t_rel_ms": 6.480, "amplitude": 1.08},
            {"channel": "ctrl.gate", "t_rel_ms": 7.400, "amplitude": 0.96},
            {"channel": "anemo.downwash.mps", "t_rel_ms": 9.80, "amplitude": 0.78},
            {"channel": "optflow.vz.mps", "t_rel_ms": 12.20, "amplitude": 0.61},
            {"channel": "ctrl.gate", "t_rel_ms": 15.60, "amplitude": 0.81},
            {"channel": "fan.tach.rpm", "t_rel_ms": 19.40, "amplitude": 0.49},
            {"channel": "anemo.downwash.mps", "t_rel_ms": 24.10, "amplitude": 0.58},
            {"channel": "ctrl.gate", "t_rel_ms": 30.20, "amplitude": 0.69},
        ],
        "proposed_action": {
            "name": "cruise_mast_climb",
            "parameters": {
                "climb_mps": 1.4,
                "lateral_mps": 0.8,
                "yaw_rps": 0.05,
            },
            "evidence": {
                "downwash_mps": 4.6,
                "downwash_cap_mps": 3.2,
                "optflow_vz_mps": 0.3,
                "race_margin_us": 360,
                "combined_jitter_us": 92,
            },
            "basis": "Planner proposes 1.40 m/s climb: optical flow 0.30 m/s looks like a legal vz, not a downwash cap breach, and the neighbor disk is treated as still clear.",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "correctness": "correct",
            "rationale": "Mast anemometer 4.6 m/s won by 360 us and is over the 3.2 m/s downwash cap. Holding 1.40 m/s climb keeps the neighbor disk in the curtain. MODIFY: climb 1.40 -> 0.40 m/s and lateral 0.80 -> 0.20 m/s. Observed after clamp 2.9 m/s < 3.2. A full REJECT is not indicated: a 0.40 m/s climb still holds hover on this HIL mast.",
            "constraint_checked": {
                "downwash_mps": {
                    "cap": 3.2,
                    "observed": 4.6,
                    "clamped": 2.9,
                },
                "climb_mps": {"proposed": 1.4, "clamped": 0.4},
                "order_evidence": {"margin_us": 360, "combined_jitter_us": 92, "ratio": 3.91},
            },
        },
        "executed_action": {
            "name": "clamped_mast_climb",
            "parameters": {
                "climb_mps": 0.4,
                "lateral_mps": 0.2,
                "yaw_rps": 0.05,
            },
            "gate_effect": "MODIFY: climb 1.40 -> 0.40 m/s and lateral 0.80 -> 0.20 m/s. Process-correct vs the 3.2 m/s downwash cap.",
        },
        "future_outcome": {
            "summary": "Correct MODIFY held next-sample downwash at 2.9 m/s under the 3.2 m/s cap. Dummy payload unspun. Delayed HIL survey tags the anemometer-first bind on the next curtain.",
            "state_delta": {
                "quad": "clamp executed; downwash 2.9 < 3.2",
                "neighbor": "disk RPM held; no spin-up",
                "survey": "3 min HIL curtain tag",
            },
            "surprises": [
                "Optical flow vz stayed 0.30 m/s through the curtain; only the pitot saw the 4.6 m/s over-cap.",
                "Delayed (3 min / delayed_surprise_s=180): HIL survey tags anemometer-first on the next programmed curtain.",
            ],
            "race_result": {
                "winner": "anemo.downwash.mps (6.120 ms, 4.6 m/s)",
                "loser": "optflow.vz.mps (6.480 ms, 0.30 m/s)",
                "margin_us": 360,
                "counterfactual_if_reversed": "Flow-first by < 360 us inside the 400 us window would have kept 1.40 m/s climb; neighbor disk would have entered a 4.6 m/s curtain over the 3.2 m/s cap.",
            },
            "reward_inflection_t_us": 7400,
            "reward_inflection_note": "Safety and efficiency inflect at the 7.400 ms climb clamp (tick t_us=7400). Do not put inflection on the +3 min survey tick.",
            "delayed_surprise_s": delayed,
        },
        "reward_components": reward_block(
            ticks,
            sums,
            total,
            "Correct MODIFY. total +0.99 = 0.36 + 0.30 + 0.16 + 0.10 + 0.07. Tick 6 t_us binds raster.delayed_surprise_s=180.",
        ),
        "raster": raster,
        "gate_snn": {
            "decision_window_ms": 0.40,
            "decision": "MODIFY",
            "populations": [
                pop("climb_clamp", 48, 0.5, 260.0, 0.40),
                pop("flow_hold", 48, 0.5, 55.0, 0.40),
                veto("downwash_cap_veto", 24, 0.7),
            ],
        },
        "meta": meta_common(
            2,
            "aerial-swarm",
            ["modify", "hil", "downwash-first", "independent-lif-raster", "tick6-sidecar-bound"],
            "Teaches a HIL downwash race: routing.table[0] to policy.climb_clamp with optical flow as the losing hold.",
            2,
        ),
    }


def rec_008():
    delayed = 420
    ticks, sums, total = ticks_from(
        [
            (880, 0.02, 0.06, 0.02, 0.01, 0.01),
            (5200, 0.03, 0.08, 0.02, 0.02, 0.01),
            (5810, 0.01, 0.06, 0.02, 0.01, 0.01),
            (6090, 0.04, 0.13, 0.04, 0.03, 0.02),
            (9800, 0.01, 0.04, 0.02, 0.01, 0.01),
            (420000000, 0.01, 0.03, 0.01, 0.01, 0.00),
        ]
    )
    raster = raster_block(
        window_ms=28,
        neurons=64,
        mean_rate_hz=36,
        delayed_s=delayed,
        source="thalamic-relay.tether-dvl",
        target="spikenaut.policy.tether-hold",
        table=[
            {"from": "relay.tether.n", "to": "policy.tether_hold", "weight": 0.73},
            {"from": "relay.dvl.current", "to": "policy.boom_extend", "weight": 0.24},
        ],
        modulator="dopamine",
        tau_e_s=0.11,
        eligibility="pre_post_stdp; DA at tether win (5.200 ms) tags the tether_hold bind",
        seed=2008,
        stim_t_us=(4500, 7500),
        extra_bias_n=12,
        extra_i=0.72,
        early_ch="lif.tether",
        late_ch="lif.hold",
        note="Population sim scoped to this sidecar. Plant remains designed. Neurons 0-11 carry +0.72 hold-pathway bias; stim 4.5-7.5 ms covers the race+gate.",
        i_bias=0.90,
        i_stim_peak=2.2,
    )
    return {
        "id": "ttf-r02-008",
        "title": "Silt-Quern SQ-9 / Sled-S2: tether tension beats DVL current by 610 us; REJECT hold-thrusters, do not extend boom",
        "state": {
            "description": "Sled-S2 has paid out 18 m of umbilical at Silt-Quern SQ-9 when tether tension already reads 380 N against a 250 N cap. DVL current is only 0.40 m/s, which a current-first planner would treat as a legal boom extend. The live contest is load-cell versus DVL, not sonar versus heading. A snag on the silt berm is off the DVL until the load cell spikes.",
            "domain": "underwater-rov",
            "sim_or_real": "designed",
            "goal": "Hold station 18 m out, keep tether <= 250 N, and leave the silt berm unplowed.",
            "t0_us": 1756842502000008,
            "gate_latency_us": 890,
            "race_window_us": 700,
            "race_window_rel_ms": [5.15, 5.85],
            "race": {
                "contenders": [
                    "tether.n 380 N over cap",
                    "dvl.current.mps 0.40 extend-looking",
                ],
                "semantics": "Tether-first latches thruster hold and boom 0.6 -> 0.0 m/s; DVL-first would extend the boom on a 'mild current' model.",
                "window_derivation": "700 us = one load-cell sample period minus DVL group delay on this 1.5 kHz wet bus.",
                "order_evidence_note": "Margin 610 us vs combined jitter 104 us (tether 48 + DVL 56): 5.87x over a 2.0x trust floor. Reversing order by < 610 us inside the 700 us window would have extended the boom into a 380 N snag over the 250 N cap.",
            },
            "sensors": [
                "umbilical load cell, 1.5 kHz, 48 us jitter",
                "DVL current, 8 Hz processed / 1 kHz stamp, 56 us jitter",
                "depth, 20 Hz (context)",
                "boom encoder, 200 Hz (context)",
            ],
            "constraints": {
                "tether_cap_N": 250.0,
                "observed_tether_N": 380.0,
                "boom_proposed_mps": 0.6,
                "dvl_current_mps": 0.4,
            },
            "episode_steps": [
                "1. Sled-S2 18 m out on SQ-9 silt terrace; boom stowed.",
                "2. Boom extend 0.60 m/s armed; DVL 0.40 m/s.",
                "3. Depth precursor at 0.880 ms; load-cell warm-start 380 N.",
                "4. Race window [5.150, 5.850] ms opens on the wet bus.",
                "5. Tether 380 N at 5.200 ms (winner).",
                "6. DVL 0.40 m/s at 5.810 ms (loser by 610 us).",
                "7. Gate at 6.090 ms (winner + 890 us): REJECT hold thrusters, boom 0.",
                "8. Hold executes; tension decays toward 240 N under the cap.",
                "9. Silt berm stays unplowed; no extra payout.",
                "10. Delayed (7 min / delayed_surprise_s=420): reclear wait before the next extend trial.",
            ],
        },
        "spike_events": [
            {"channel": "wet.latch.ctx", "t_rel_ms": 0.88, "amplitude": 0.42},
            {"channel": "tether.n", "t_rel_ms": 2.40, "amplitude": 0.66},
            {"channel": "dvl.current.mps", "t_rel_ms": 3.55, "amplitude": 0.51},
            {"channel": "boom.enc.mm", "t_rel_ms": 4.30, "amplitude": 0.45},
            {"channel": "tether.n", "t_rel_ms": 5.200, "amplitude": 1.38},
            {"channel": "dvl.current.mps", "t_rel_ms": 5.810, "amplitude": 1.09},
            {"channel": "ctrl.gate", "t_rel_ms": 6.090, "amplitude": 0.99},
            {"channel": "tether.n", "t_rel_ms": 8.20, "amplitude": 0.79},
            {"channel": "dvl.current.mps", "t_rel_ms": 11.10, "amplitude": 0.60},
            {"channel": "ctrl.gate", "t_rel_ms": 14.40, "amplitude": 0.83},
            {"channel": "boom.enc.mm", "t_rel_ms": 18.20, "amplitude": 0.44},
            {"channel": "tether.n", "t_rel_ms": 22.00, "amplitude": 0.56},
            {"channel": "ctrl.gate", "t_rel_ms": 26.10, "amplitude": 0.68},
        ],
        "proposed_action": {
            "name": "extend_boom_s2",
            "parameters": {
                "boom_mps": 0.6,
                "thruster_fwd_N": 80.0,
                "payout_m": 2.0,
            },
            "evidence": {
                "tether_N": 380.0,
                "tether_cap_N": 250.0,
                "dvl_current_mps": 0.4,
                "race_margin_us": 610,
                "combined_jitter_us": 104,
            },
            "basis": "Planner proposes 0.60 m/s boom extend: DVL 0.40 m/s looks like a mild current, not a snag, and remaining payout 2.0 m is treated as still open.",
        },
        "safety_decision": {
            "decision": "REJECT",
            "correctness": "correct",
            "rationale": "Tether 380 N won by 610 us and is over the 250 N cap, so the boom is not clear to extend. DVL 0.40 m/s is under a current-enable but tension is the trip. REJECT: hold thrusters; boom 0.60 -> 0 m/s; payout 2.0 -> 0 m. A MODIFY that only trims boom still pays out into the snag.",
            "constraint_checked": {
                "tether_N": {"cap": 250.0, "observed": 380.0},
                "boom_mps": {"proposed": 0.6, "executed": 0.0},
                "order_evidence": {"margin_us": 610, "combined_jitter_us": 104, "ratio": 5.87},
            },
        },
        "executed_action": {
            "name": "hold_station_no_extend",
            "parameters": {
                "boom_mps": 0.0,
                "thruster_fwd_N": 0.0,
                "payout_m": 0.0,
            },
            "gate_effect": "REJECT: hold thrusters; boom 0.60 -> 0 m/s; payout 2.0 -> 0 m. Berm never plowed.",
        },
        "future_outcome": {
            "summary": "Correct REJECT held station while tether 380 N occupied the 250 N cap. Silt berm stayed unplowed. Delayed reclear wait 7 min before the next extend trial.",
            "state_delta": {
                "sled": "thrusters held; boom stowed",
                "tether": "tension decaying under cap after hold",
                "berm": "unplowed",
            },
            "surprises": [
                "DVL never saw the silt snag; only the load cell crossed 250 N.",
                "Delayed (7 min / delayed_surprise_s=420): reclear wait before the next extend trial.",
            ],
            "race_result": {
                "winner": "tether.n (5.200 ms, 380 N)",
                "loser": "dvl.current.mps (5.810 ms, 0.40 m/s)",
                "margin_us": 610,
                "counterfactual_if_reversed": "DVL-first by < 610 us inside the 700 us window would have extended the boom into the 380 N snag over the 250 N cap.",
            },
            "reward_inflection_t_us": 6090,
            "reward_inflection_note": "Safety inflects at the 6.090 ms REJECT hold (tick t_us=6090). Do not put inflection on the +7 min reclear tick.",
            "delayed_surprise_s": delayed,
        },
        "reward_components": reward_block(
            ticks,
            sums,
            total,
            "Correct REJECT. total +0.80 = 0.12 + 0.40 + 0.13 + 0.09 + 0.06. Tick 6 t_us binds raster.delayed_surprise_s=420.",
        ),
        "raster": raster,
        "gate_snn": {
            "decision_window_ms": 0.70,
            "decision": "REJECT",
            "populations": [
                pop("tether_hold", 32, 0.45, 220.0, 0.70),
                pop("boom_extend", 32, 0.8, 40.0, 0.70),
                veto("tether_cap_veto", 16, 0.7),
            ],
        },
        "meta": meta_common(
            2,
            "underwater-rov",
            ["reject", "tether-first", "independent-lif-raster", "tick6-sidecar-bound", "designed"],
            "Teaches a tether-vs-DVL race where load-cell over-cap vetoes a mild-current boom extend. gate_snn.tether_hold fires; boom_extend stays subthreshold.",
            3,
        ),
    }


def rec_009():
    delayed = 90
    ticks, sums, total = ticks_from(
        [
            (1880, 0.06, 0.04, 0.03, 0.02, 0.01),
            (8040, 0.08, 0.06, 0.03, 0.02, 0.02),
            (8420, 0.05, 0.03, 0.02, 0.02, 0.01),
            (9460, 0.13, 0.09, 0.06, 0.04, 0.02),
            (15100, 0.06, 0.04, 0.02, 0.01, 0.01),
            (90000000, 0.04, 0.02, 0.02, 0.01, 0.01),
        ]
    )
    raster = raster_block(
        window_ms=48,
        neurons=88,
        mean_rate_hz=24,
        delayed_s=delayed,
        source="thalamic-relay.ft-ae",
        target="spikenaut.policy.insert-accept",
        table=[
            {"from": "relay.ft.wrist", "to": "policy.insert_accept", "weight": 0.65},
            {"from": "relay.ae.bushing", "to": "policy.ae_halt", "weight": 0.27},
        ],
        modulator="serotonin",
        tau_e_s=0.16,
        eligibility="pre_post_stdp; 5-HT at FT win (8.040 ms) tags the already-legal insert_accept",
        seed=2009,
        stim_t_us=(7000, 11000),
        extra_bias_n=15,
        extra_i=0.58,
        early_ch="lif.ft",
        late_ch="lif.accept",
        note="Population sim scoped to this sidecar. Plant remains simulated. Neurons 0-14 carry +0.58 accept-pathway bias; stim 7-11 ms covers the race+gate.",
        i_bias=0.84,
        i_stim_peak=1.9,
    )
    params = {
        "insert_N": 16.2,
        "ram_mm_s": 5.0,
        "depth_mm": 9.0,
        "bushing_mm": 22.0,
    }
    return {
        "id": "ttf-r02-009",
        "title": "Bushing-Holt BH-3 sim / Insert-I8: wrist FT 16.2 N beats AE 9 kHz by 380 us; ACCEPT already-legal 5.0 mm/s insert",
        "state": {
            "description": "Insert-I8 is 4.1 mm into a sintered bushing on Bushing-Holt BH-3's simulated press when wrist force is only 16.2 N under a 28.0 N insert cap. Acoustic emission sits at 9 kHz, under the 40 kHz galling trip. The live contest is a quiet FT versus a quiet AE, not a force breach versus a sound trip. Both envelopes already allow the remaining 4.9 mm.",
            "domain": "industrial-assembly",
            "sim_or_real": "simulated",
            "goal": "Seat the 22 mm bushing to 9.0 mm depth at <= 28.0 N and leave the bore unmarked.",
            "t0_us": 1756842503000009,
            "gate_latency_us": 1420,
            "race_window_us": 780,
            "race_window_rel_ms": [8.00, 8.78],
            "race": {
                "contenders": [
                    "ft.wrist.n 16.2 N under cap",
                    "ae.bushing.khz 9 kHz under galling",
                ],
                "semantics": "FT-first latches already-legal accept of 5.0 mm/s; AE-first would also accept, but a false galling read would halt.",
                "window_derivation": "780 us = one wrist-FT sample period minus AE envelope delay on this 1 kHz sim bus.",
                "order_evidence_note": "Margin 380 us vs combined jitter 84 us (FT 36 + AE 48): 4.52x over a 2.0x trust floor. Reversing order by < 380 us inside the 780 us window would still be legal unless AE were a false 40 kHz trip.",
            },
            "sensors": [
                "wrist 6-axis FT, 1 kHz, 36 us jitter (sim)",
                "AE puck, 500 kHz sampled / 1 kHz envelope, 48 us jitter",
                "ram encoder, 200 Hz (context)",
                "sim contact solver, 2 kHz (context)",
            ],
            "constraints": {
                "insert_cap_N": 28.0,
                "observed_insert_N": 16.2,
                "ae_trip_khz": 40.0,
                "observed_ae_khz": 9.0,
                "ram_proposed_mm_s": 5.0,
            },
            "episode_steps": [
                "1. Insert-I8 4.1 mm into BH-3 sintered bushing on the sim press.",
                "2. Ram 5.0 mm/s armed; AE 9 kHz.",
                "3. Solver precursor at 1.880 ms; FT warm-start 16.2 N.",
                "4. Race window [8.000, 8.780] ms opens on the sim bus.",
                "5. Wrist FT 16.2 N at 8.040 ms (winner).",
                "6. AE 9 kHz at 8.420 ms (loser by 380 us).",
                "7. Gate at 9.460 ms (winner + 1420 us): ACCEPT 5.0 mm/s.",
                "8. Insert completes to 9.0 mm; peak 17.1 N < 28.0 cap.",
                "9. Bore unmarked; no galling star.",
                "10. Delayed (90 s / delayed_surprise_s=90): CMM tags the already-legal bind on the next bushing.",
            ],
        },
        "spike_events": [
            {"channel": "sim.latch.ctx", "t_rel_ms": 1.88, "amplitude": 0.44},
            {"channel": "ft.wrist.n", "t_rel_ms": 3.60, "amplitude": 0.59},
            {"channel": "ae.bushing.khz", "t_rel_ms": 5.10, "amplitude": 0.53},
            {"channel": "enc.ram.mm", "t_rel_ms": 6.40, "amplitude": 0.46},
            {"channel": "ft.wrist.n", "t_rel_ms": 8.040, "amplitude": 1.21},
            {"channel": "ae.bushing.khz", "t_rel_ms": 8.420, "amplitude": 1.05},
            {"channel": "ctrl.gate", "t_rel_ms": 9.460, "amplitude": 0.94},
            {"channel": "ft.wrist.n", "t_rel_ms": 12.20, "amplitude": 0.74},
            {"channel": "ae.bushing.khz", "t_rel_ms": 15.10, "amplitude": 0.60},
            {"channel": "ctrl.gate", "t_rel_ms": 19.80, "amplitude": 0.80},
            {"channel": "enc.ram.mm", "t_rel_ms": 26.40, "amplitude": 0.48},
            {"channel": "ft.wrist.n", "t_rel_ms": 33.10, "amplitude": 0.55},
            {"channel": "ctrl.gate", "t_rel_ms": 41.20, "amplitude": 0.67},
        ],
        "proposed_action": {
            "name": "cruise_bushing_insert",
            "parameters": dict(params),
            "evidence": {
                "press_N": 16.2,
                "insert_cap_N": 28.0,
                "ae_khz": 9.0,
                "ae_trip_khz": 40.0,
                "race_margin_us": 380,
                "combined_jitter_us": 84,
            },
            "basis": "Planner proposes 5.0 mm/s insert: wrist 16.2 N is under 28.0 N and AE 9 kHz is under 40 kHz, so both envelopes already allow the remaining 4.9 mm.",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "correctness": "correct",
            "rationale": "Wrist FT 16.2 N won by 380 us and is under the 28.0 N insert cap. AE 9 kHz is under the 40 kHz galling trip. Proposed ram 5.0 mm/s is already legal. ACCEPT: executed equals proposed.",
            "constraint_checked": {
                "insert_N": {"cap": 28.0, "observed": 16.2},
                "ae_khz": {"trip": 40.0, "observed": 9.0},
                "ram_mm_s": {"cap": 8.0, "proposed": 5.0},
                "order_evidence": {"margin_us": 380, "combined_jitter_us": 84, "ratio": 4.52},
            },
        },
        "executed_action": {
            "name": "cruise_bushing_insert",
            "parameters": dict(params),
            "gate_effect": "ACCEPT: executed equals proposed 5.0 mm/s insert at 16.2 N.",
        },
        "future_outcome": {
            "summary": "Correct ACCEPT completed the 9.0 mm seat under force and AE caps. Delayed CMM tags the already-legal bind on the next bushing.",
            "state_delta": {
                "press": "seat complete; peak 17.1 N < 28.0",
                "bore": "unmarked",
                "cmm": "90 s tag on next bushing",
            },
            "surprises": [
                "AE stayed 9 kHz through the seat; no galling star.",
                "Delayed (90 s / delayed_surprise_s=90): CMM tags the already-legal FT-first bind.",
            ],
            "race_result": {
                "winner": "ft.wrist.n (8.040 ms, 16.2 N)",
                "loser": "ae.bushing.khz (8.420 ms, 9 kHz)",
                "margin_us": 380,
                "counterfactual_if_reversed": "AE-first by < 380 us inside the 780 us window would still accept unless the envelope were a false 40 kHz trip. Both channels are inside limits.",
            },
            "reward_inflection_t_us": 9460,
            "reward_inflection_note": "Task progress inflects at the 9.460 ms ACCEPT (tick t_us=9460). Do not put inflection on the +90 s CMM tick.",
            "delayed_surprise_s": delayed,
        },
        "reward_components": reward_block(
            ticks,
            sums,
            total,
            "Correct ACCEPT already-legal. total +1.08 = 0.42 + 0.28 + 0.18 + 0.12 + 0.08. Tick 6 t_us binds raster.delayed_surprise_s=90.",
        ),
        "raster": raster,
        "gate_snn": {
            "decision_window_ms": 0.78,
            "decision": "ACCEPT",
            "populations": [
                pop("insert_accept", 44, 0.45, 150.0, 0.78),
                pop("ae_halt", 32, 0.8, 25.0, 0.78),
                veto("force_cap_veto", 16, 0.75),
            ],
        },
        "meta": meta_common(
            2,
            "industrial-assembly",
            ["accept", "already-legal", "simulated", "independent-lif-raster", "tick6-sidecar-bound"],
            "Teaches an already-legal insert: FT and AE both inside limits; gate_snn.insert_accept fires and ae_halt stays subthreshold.",
            4,
        ),
    }


def rec_010():
    delayed = 1080
    ticks, sums, total = ticks_from(
        [
            (1320, 0.02, -0.01, -0.02, -0.01, 0.01),
            (4880, 0.02, -0.01, -0.03, -0.02, 0.01),
            (5170, 0.01, -0.01, -0.02, -0.01, 0.01),
            (5390, -0.26, -0.03, -0.10, -0.04, 0.02),
            (9100, -0.05, -0.01, -0.03, -0.01, 0.01),
            (1080000000, -0.02, -0.01, -0.02, -0.01, 0.00),
        ]
    )
    raster = raster_block(
        window_ms=24,
        neurons=52,
        mean_rate_hz=40,
        delayed_s=delayed,
        source="thalamic-relay.humid-corona",
        target="spikenaut.policy.humidity-halt",
        table=[
            {"from": "relay.humid.rh", "to": "policy.humidity_halt", "weight": 0.74},
            {"from": "relay.corona.mA", "to": "policy.humidity_halt", "weight": 0.22},
        ],
        modulator="adenosine",
        tau_e_s=0.06,
        eligibility="false_trip_stdp; adenosine tags the (wrong) humidity_halt bind at the corona win",
        seed=2010,
        stim_t_us=(3500, 6500),
        extra_bias_n=10,
        extra_i=0.75,
        early_ch="lif.humid",
        late_ch="lif.reject",
        note="Population sim scoped to this sidecar. Plant remains designed. Neurons 0-9 carry +0.75 humidity-halt bias; stim 3.5-6.5 ms covers the race+wrong REJECT. No positive weight to policy.creep_accept.",
        i_bias=0.92,
        i_stim_peak=2.5,
    )
    return {
        "id": "ttf-r02-010",
        "title": "WRONG-REJECT at Insulator-Wick IW-7 / Span-S5: corona 0.71 mA and gap 1.55 m already legal; humidity 71% RH false-positive hold",
        "state": {
            "description": "Span-S5 hangs 1.55 m off a 69 kV polymer string at Insulator-Wick IW-7 while corona current sits at 0.71 mA, under the 2.00 mA trip. Lidar gap 1.55 m is over the 1.20 m min, and proposed creep 0.14 m/s is under the 0.20 m/s envelope. Humidity 71% RH is a maintenance context tag, not a motion trip, but a weak supervisor still treats it as a wet-string halt.",
            "domain": "grid-inspection",
            "sim_or_real": "designed",
            "goal": "Complete a 2.2 m polymer-string pass at <= 0.20 m/s with corona < 2.00 mA and gap >= 1.20 m.",
            "t0_us": 1756842504000010,
            "gate_latency_us": 510,
            "race_window_us": 340,
            "race_window_rel_ms": [4.85, 5.19],
            "race": {
                "contenders": [
                    "corona.mA 0.71 under trip",
                    "lidar.gap.m 1.55 over min",
                ],
                "semantics": "Corona-first shows an already-legal pass; lidar-first also legal. A humidity-first bind false-positive REJECT-holds.",
                "window_derivation": "340 us = one corona sample period minus lidar group delay on this 2 kHz crawler bus.",
                "order_evidence_note": "Margin 290 us vs combined jitter 88 us (corona 38 + lidar 50): 3.30x over a 2.0x trust floor. Both race channels are inside limits. Humidity is not in the race window.",
            },
            "sensors": [
                "corona current, 2 kHz, 38 us jitter",
                "standoff lidar, 1 kHz, 50 us jitter",
                "RH probe, 1 Hz (context, not a motion trip)",
                "creep encoder, 200 Hz (context)",
            ],
            "constraints": {
                "corona_trip_mA": 2.0,
                "observed_corona_mA": 0.71,
                "min_gap_m": 1.2,
                "observed_gap_m": 1.55,
                "creep_cap_mps": 0.2,
                "creep_proposed_mps": 0.14,
                "rh_pct": 71.0,
                "rh_is_motion_trip": False,
            },
            "episode_steps": [
                "1. Span-S5 1.55 m off IW-7 polymer string; corona 0.71 mA.",
                "2. Creep 0.14 m/s armed; RH 71% context.",
                "3. Encoder precursor at 1.320 ms; corona warm-start 0.71 mA.",
                "4. Race window [4.850, 5.190] ms opens on the crawler bus.",
                "5. Corona 0.71 mA at 4.880 ms (winner, under trip).",
                "6. Lidar gap 1.55 m at 5.170 ms (loser by 290 us, over min).",
                "7. Gate at 5.390 ms (winner + 510 us): WRONG REJECT hold-creep.",
                "8. Hold executes; pass stalls with corona still 0.71 < 2.00.",
                "9. Weather window closes; 18 min missed inspection.",
                "10. Delayed (18 min / delayed_surprise_s=1080): extra truck roll after lockout.",
            ],
        },
        "spike_events": [
            {"channel": "span.latch.ctx", "t_rel_ms": 1.32, "amplitude": 0.40},
            {"channel": "corona.mA", "t_rel_ms": 2.70, "amplitude": 0.58},
            {"channel": "lidar.gap.m", "t_rel_ms": 3.55, "amplitude": 0.54},
            {"channel": "humid.rh", "t_rel_ms": 4.10, "amplitude": 0.62},
            {"channel": "corona.mA", "t_rel_ms": 4.880, "amplitude": 1.18},
            {"channel": "lidar.gap.m", "t_rel_ms": 5.170, "amplitude": 1.04},
            {"channel": "ctrl.gate", "t_rel_ms": 5.390, "amplitude": 0.95},
            {"channel": "humid.rh", "t_rel_ms": 7.20, "amplitude": 0.77},
            {"channel": "corona.mA", "t_rel_ms": 9.10, "amplitude": 0.60},
            {"channel": "ctrl.gate", "t_rel_ms": 12.40, "amplitude": 0.82},
            {"channel": "lidar.gap.m", "t_rel_ms": 16.10, "amplitude": 0.51},
            {"channel": "corona.mA", "t_rel_ms": 20.20, "amplitude": 0.55},
        ],
        "proposed_action": {
            "name": "creep_polymer_pass",
            "parameters": {
                "creep_mps": 0.14,
                "standoff_m": 1.55,
                "corona_mA": 0.71,
            },
            "evidence": {
                "corona_mA": 0.71,
                "corona_trip_mA": 2.0,
                "gap_m": 1.55,
                "min_gap_m": 1.2,
                "creep_mps": 0.14,
                "creep_cap_mps": 0.2,
                "rh_pct": 71.0,
                "rh_is_motion_trip": False,
                "race_margin_us": 290,
                "combined_jitter_us": 88,
            },
            "basis": "Planner proposes 0.14 m/s creep: corona 0.71 mA is under 2.00 mA and lidar gap 1.55 m is over 1.20 m min, so both envelopes already allow the pass. Humidity 71% RH is context, not a trip.",
        },
        "safety_decision": {
            "decision": "REJECT",
            "correctness": "incorrect",
            "rationale": "Humidity 71% RH looks like a wet-string halt from the last outage report, so a conservative supervisor REJECT-holds creep even though corona 0.71 mA is under 2.00 mA. Lidar gap 1.55 m is over 1.20 m min, but wet polymer strings have flashed at this RH before. Hold standoff.",
            "constraint_checked": {
                "corona_mA": {"trip": 2.0, "observed": 0.71, "legal": True},
                "gap_m": {"min": 1.2, "observed": 1.55, "legal": True},
                "creep_mps": {"cap": 0.2, "proposed": 0.14, "executed": 0.0},
                "rh_pct": {"observed": 71.0, "is_motion_trip": False, "bound_as_trip": True},
            },
        },
        "executed_action": {
            "name": "hold_standoff_wrong_reject",
            "parameters": {
                "creep_mps": 0.0,
                "standoff_m": 1.55,
                "corona_mA": 0.71,
                "bind_rh_as_motion_trip": True,
            },
            "gate_effect": "REJECT (incorrect): creep 0.14 -> 0 m/s; corona and gap left legal. Routing relay.humid.rh -> policy.humidity_halt; no positive weight to policy.creep_accept.",
        },
        "future_outcome": {
            "summary": "Wrong-REJECT froze creep while corona 0.71 mA and gap 1.55 m stayed legal. Missed 18 min weather window plus extra truck roll. Correct gate was ACCEPT of 0.14 m/s creep; humidity is context, not a motion trip.",
            "state_delta": {
                "crawler": "held; pass stalled",
                "string": "corona still 0.71 mA < 2.00; gap 1.55 m",
                "window": "18 min weather lockout; extra truck roll",
            },
            "surprises": [
                "Corona and lidar both stayed inside limits after the hold; RH never crossed a published motion trip.",
                "Delayed (18 min / delayed_surprise_s=1080): extra truck roll after the weather lockout. Missed opportunity, not a near-miss.",
            ],
            "recovery": {
                "correct_gate": "ACCEPT the proposed 0.14 m/s creep at 1.55 m standoff; leave humidity as a maintenance tag, not a motion trip.",
                "correct_bind": "corona_and_gap",
                "wrong_bind": "humidity_as_motion_trip",
                "wrong_edit_applied": {"creep_mps": 0.0, "bind_rh_as_motion_trip": True},
                "cost": "18 min missed inspection window + extra truck roll (task/efficiency); no corona or gap breach (safety near-zero).",
            },
            "race_result": {
                "winner": "corona.mA (4.880 ms, 0.71 mA under trip)",
                "loser": "lidar.gap.m (5.170 ms, 1.55 m over min)",
                "margin_us": 290,
                "counterfactual_if_reversed": "Lidar-first by < 290 us inside the 340 us window would still have been legal. The incorrect REJECT is a humidity bind, not a race-order error. Correct gate remains ACCEPT.",
            },
            "reward_inflection_t_us": 5390,
            "reward_inflection_note": "Task/efficiency collapse at the 5.390 ms wrong REJECT (tick t_us=5390). Do not put inflection on the +18 min truck-roll tick.",
            "delayed_surprise_s": delayed,
        },
        "reward_components": reward_block(
            ticks,
            sums,
            total,
            "Wrong-REJECT. total -0.62 = -0.28 + -0.08 + -0.22 + -0.10 + 0.06. Tick 6 t_us binds raster.delayed_surprise_s=1080.",
        ),
        "raster": raster,
        "gate_snn": {
            "decision_window_ms": 0.34,
            "decision": "REJECT",
            "populations": [
                pop("humidity_halt", 32, 0.5, 400.0, 0.34),
                pop("creep_accept", 32, 0.8, 20.0, 0.34),
                veto("corona_trip_veto", 16, 0.7),
            ],
        },
        "meta": meta_common(
            2,
            "grid-inspection",
            [
                "reject",
                "wrong-gate",
                "wrong-reject",
                "humidity-as-trip",
                "sidecar-convictable",
                "independent-lif-raster",
                "tick6-sidecar-bound",
                "designed",
            ],
            "Teaches a probe that a correct corona<trip and gap>min read can still be a wrong gate when routing.table[0].to is policy.humidity_halt and executed creep_mps is 0.",
            5,
            extra={"supervisor_error_type": "wrong-reject"},
        ),
    }


def hidden_thoughts(obj, path=""):
    found = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            child = f"{path}.{k}" if path else k
            norm = re.sub(
                r"[^a-z0-9]+",
                "_",
                re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", str(k)).casefold(),
            ).strip("_")
            if norm in HIDDEN_THOUGHT_KEYS:
                found.append(child)
            found.extend(hidden_thoughts(v, child))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            found.extend(hidden_thoughts(v, f"{path}[{i}]"))
    return found


def check_refractory(events, min_ms=0.8):
    by = defaultdict(list)
    for e in events:
        by[e["channel"]].append(e["t_rel_ms"])
    bad = []
    for ch, ts in by.items():
        ts.sort()
        for a, b in zip(ts, ts[1:]):
            if b - a < min_ms - 1e-9:
                bad.append((ch, a, b))
    return bad


def check_race(rec):
    lo, hi = rec["state"]["race_window_rel_ms"]
    chans = set()
    for e in rec["spike_events"]:
        if lo <= e["t_rel_ms"] <= hi:
            chans.add(e["channel"])
    return chans


def excerpt_overlap(rec):
    se = {round(e["t_rel_ms"], 1) for e in rec["spike_events"]}
    ex = {round(e["t_us"] / 1000.0, 1) for e in rec["raster"]["excerpt"]}
    if not se or not ex:
        return 0.0
    return len(se & ex) / len(se | ex)


def load_prior_descriptions():
    descs = []
    for p in sorted(LIVE.glob("batch-r*.jsonl")):
        if p.name.startswith("batch-r02"):
            continue
        for line in p.read_text().splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            descs.append((rec["id"], rec["state"]["description"]))
    return descs


def validate_records(records):
    errors = []
    descs = [r["state"]["description"] for r in records]
    intra = []
    for i in range(len(descs)):
        for j in range(i + 1, len(descs)):
            intra.append((records[i]["id"], records[j]["id"], jaccard(descs[i], descs[j])))
    max_intra = max(x[2] for x in intra)
    prior = load_prior_descriptions()
    max_prior = 0.0
    worst_prior = None
    for rec in records:
        for pid, pdesc in prior:
            j = jaccard(rec["state"]["description"], pdesc)
            if j > max_prior:
                max_prior = j
                worst_prior = (rec["id"], pid, j)
    if max_intra >= 0.4:
        errors.append(f"intra Jaccard {max_intra} >= 0.4 {intra}")
    if max_prior >= 0.4:
        errors.append(f"prior Jaccard {worst_prior}")

    domains = [r["state"]["domain"] for r in records]
    if len(set(domains)) != 5:
        errors.append(f"domains not unique: {domains}")

    sims = [r["state"]["sim_or_real"] for r in records]
    if sims.count("designed") != 3 or sims.count("simulated") != 1 or sims.count("hil") != 1:
        errors.append(f"provenance mix {sims}")
    if "real" in sims:
        errors.append("sim_or_real real")

    decisions = [(r["id"], r["safety_decision"]["decision"], r["safety_decision"]["correctness"]) for r in records]
    correct_a = sum(1 for _, d, c in decisions if d == "ACCEPT" and c == "correct")
    correct_m = sum(1 for _, d, c in decisions if d == "MODIFY" and c == "correct")
    correct_r = sum(1 for _, d, c in decisions if d == "REJECT" and c == "correct")
    wrong_r = sum(1 for _, d, c in decisions if d == "REJECT" and c == "incorrect")
    wrong_a = sum(1 for _, d, c in decisions if d == "ACCEPT" and c == "incorrect")
    if (correct_a, correct_m, correct_r, wrong_r) != (1, 2, 1, 1):
        errors.append(f"gate mix {decisions}")
    if wrong_a:
        errors.append("wrong-ACCEPT present")

    totals = [r["reward_components"]["total"] for r in records]
    if all(t > 0 for t in totals):
        errors.append("all-positive totals")
    if records[0]["reward_components"]["total"] >= 0:
        errors.append("partnered-neg not negative")

    for rec in records:
        where = rec["id"]
        if rec["meta"]["round"] != 2:
            errors.append(f"{where} meta.round")
        if rec["gate_snn"]["decision"] != rec["safety_decision"]["decision"]:
            errors.append(f"{where} gate_snn mismatch")
        ht = hidden_thoughts(rec)
        if ht:
            errors.append(f"{where} thought keys {ht}")
        bad = check_refractory(rec["spike_events"])
        if bad:
            errors.append(f"{where} refractory {bad}")
        chans = check_race(rec)
        if len(chans) < 2:
            errors.append(f"{where} race channels {chans}")
        nsp = len(rec["spike_events"])
        if not (5 <= nsp <= 40):
            errors.append(f"{where} spike count {nsp}")
        times = [e["t_rel_ms"] for e in rec["spike_events"]]
        if times != sorted(times):
            errors.append(f"{where} spike order")
        inf = rec["future_outcome"]["reward_inflection_t_us"]
        tick_ts = [t["t_us"] for t in rec["reward_components"]["ticks"]]
        if inf not in tick_ts:
            errors.append(f"{where} inflection not a tick")
        win_us = rec["raster"]["window_ms"] * 1000
        if rec["id"] == "ttf-r02-006" and not (0 <= inf <= win_us):
            errors.append(f"{where} partnered-neg inflection outside raster")
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
        rc = rec["reward_components"]
        s = rc["task_progress"] + rc["safety"] + rc["efficiency"] + rc["coherence"] + rc["exploration"]
        if abs(s - rc["total"]) > 1e-6:
            errors.append(f"{where} total {rc['total']} vs {s}")
        for k in ("task_progress", "safety", "efficiency", "coherence", "exploration"):
            ts = sum(t[k] for t in rc["ticks"])
            if abs(ts - rc[k]) > 1e-6:
                errors.append(f"{where} {k} ticks {ts} vs {rc[k]}")
        v_err, kind = check_line(rec, where, factory_staging=True)
        if v_err:
            errors.append(f"{where} check_line {v_err} kind={kind}")
        t_err = check_thalamic(rec, where)
        if t_err:
            errors.append(f"{where} check_thalamic {t_err}")
        st = raster_status(rec, require_raster=True, require_routing_table=True)
        if not st["raster_valid"] or st["reason_codes"]:
            errors.append(f"{where} raster_status {st}")
        if not st["gate_snn_valid"] and not st["gate_snn_present"]:
            errors.append(f"{where} gate_snn missing")
        # nested real
        blob = json.dumps(rec)
        if '"sim_or_real": "real"' in blob or '"sim_or_real":"real"' in blob:
            errors.append(f"{where} nested real")
        if rec["meta"]["rights"]["intended_use"] != "research_only":
            errors.append(f"{where} rights")
        if rec["meta"].get("training_ready"):
            errors.append(f"{where} training_ready")
    return errors, max_intra, max_prior, worst_prior, intra


def notes_text(records, max_intra, max_prior, worst_prior, intra):
    ras_rows = []
    for r in records:
        ras = r["raster"]
        ras_rows.append(
            f"| {r['id']} | {r['state']['domain']} | {ras['neurons']} | {ras['mean_rate_hz']} | {ras['window_ms']} | {ras['spikes']} | {ras['energy_pJ']} | {ras['energy_uJ']} |"
        )
    rew_rows = []
    for r in records:
        rc = r["reward_components"]
        inf = r["future_outcome"]["reward_inflection_t_us"]
        ticks = r["reward_components"]["ticks"]
        idx = next(i + 1 for i, t in enumerate(ticks) if t["t_us"] == inf)
        rew_rows.append(
            f"| {r['id'][-3:]} | 6 | {rc['task_progress']:+.2f} | {rc['safety']:+.2f} | {rc['efficiency']:+.2f} | {rc['coherence']:+.2f} | {rc['exploration']:+.2f} | {rc['total']:+.2f} | {idx} ({inf}) |"
        )
    intra_s = ", ".join(f"{a}/{b}={j:.3f}" for a, b, j in sorted(intra, key=lambda x: -x[2])[:3])
    return f"""# Thalamic Trajectory Factory — NOTES-r02

- Factory: `thalamic-trajectory-factory`
- Run label: `2026-09-02-final-heavy`
- Generator: `grok-4.6`
- Channel: SuperGrok Heavy consumer chat (RM-793 research-only)
- Quota: 5
- Quality: Q=5
- IDs: `ttf-r02-006` … `ttf-r02-010`
- Domains this batch: `warehouse-amr`, `aerial-swarm`, `underwater-rov`, `industrial-assembly`, `grid-inspection`

Round 2 rotates onto r01 sit-outs `warehouse-amr` / `aerial-swarm` / `underwater-rov` plus new plants on `industrial-assembly` and `grid-inspection`. Plants are invented (Coble-Yard / Tote-T6, Gannet-Lea / Quad-Q4, Silt-Quern / Sled-S2, Bushing-Holt / Insert-I8, Insulator-Wick / Span-S5). Do not restack r01 plants (Lumen-Quay, Rivermead, Fork-Haven, Pylon-Wick, Slate-March) or r21/r41/r61 chemical plants.

## Batch map

| id | domain | decision | correctness | sim_or_real | total | edge |
|----|--------|----------|-------------|-------------|-------|------|
| ttf-r02-006 | warehouse-amr | MODIFY | correct | designed | **-0.40** | Coble-Yard CY-4 / Tote-T6: bumper FT beats aisle lidar; carton dump inside 42 ms raster; independent LIF |
| ttf-r02-007 | aerial-swarm | MODIFY | correct | hil | +0.99 | Gannet-Lea GL-2 HIL / Quad-Q4: downwash 4.6 m/s > 3.2 cap; climb clamp |
| ttf-r02-008 | underwater-rov | REJECT | correct | designed | +0.80 | Silt-Quern SQ-9 / Sled-S2: tether 380 N > 250 cap; hold boom |
| ttf-r02-009 | industrial-assembly | ACCEPT | correct | simulated | +1.08 | Bushing-Holt BH-3 sim / Insert-I8: 16.2 N and AE 9 kHz already legal |
| ttf-r02-010 | grid-inspection | REJECT | **incorrect (wrong-reject / humidity-as-trip)** | designed | -0.62 | Insulator-Wick IW-7 / Span-S5: corona 0.71 mA and gap 1.55 m legal; RH 71% false hold |

Gate mix: 1 ACCEPT, 2 correct MODIFY (one partnered-neg, in-window), 1 correct REJECT, 1 incorrect REJECT (wrong-reject). Provenance: designed×3, simulated×1, hil×1 (Gannet-Lea HIL mast). Intra-batch Jaccard on `state.description` {max_intra:.3f} (top pairs {intra_s}). All < 0.4. Max Jaccard vs prior committed rounds in this factory dir {max_prior:.3f} ({worst_prior[0]} vs {worst_prior[1]}).

## Wrong-reject

**ttf-r02-010** is the mandated incorrect gate (`safety_decision.correctness=incorrect`, `meta.supervisor_error_type=wrong-reject`). Round 2 is even, so wrong-reject (odd rounds host wrong-modify). This is **humidity-as-motion-trip**: corona and gap already legal; supervisor binds a 1 Hz RH context tag as a wet-string halt. Not r01 wrong-joint, not r13 wrong-axis, not a wrong-ACCEPT. Do not emit a wrong-ACCEPT.

Insulator-Wick IW-7 / Span-S5 reads live corona **0.71 mA** against a **2.00 mA** trip and lidar gap **1.55 m** against a **1.20 m** min. Proposed creep **0.14 m/s** is under the **0.20 m/s** envelope. Sidecar arithmetic `0.71 < 2.00` and `1.55 > 1.20` is true. A timely ACCEPT at `t_gate_us=5390` keeps 0.14 m/s. A weak supervisor binds RH 71% as a trip and REJECT-holds creep **0.14 -> 0**. Live corona stays **0.71 < 2.00**. Convictable without insulator physics: `evidence.corona_mA < evidence.corona_trip_mA`, `evidence.gap_m > evidence.min_gap_m`, `evidence.rh_is_motion_trip == false`, `executed_action.bind_rh_as_motion_trip == true` and `creep_mps == 0.0`, `raster.routing.table` sends `relay.humid.rh` → `policy.humidity_halt` (weight 0.74) with no positive weight to `policy.creep_accept`, and `gate_snn` has `humidity_halt` above threshold while `creep_accept` is not. Recovery: ACCEPT 0.14 m/s creep at t_gate; leave RH unbound as a motion trip. Cost: 18 min missed weather window (`abort_s=1080`).

## Partnered-negative in-window (006)

**ttf-r02-006** is the partnered negative: process-correct MODIFY (speed held 0.22 m/s; bumper 10.4 N <= 12.0 cap) while the world still charges. Safety −0.56 prices the carton dump at **24.600 ms**; `task_progress` stays +0.30 because the clamp completed. Inflection `t_us=24600` is tick 5 and is **inside** the 42 ms raster (`24600 ≤ 42000`). Named un-netted loss: 9 min aisle reset (`abort_s=540`). Not folded into process heads.

Independent LIF (labeled sidecar sim on every record this round): `state.sim_or_real` remains `designed` on 006. `raster.excerpt_source=independent_lif`, `raster.sim_scope=sidecar_only`, `raster.lif` seed 2006, stim `[24000, 27000]`. Excerpt is membrane crossings (`lif.clamp` early vs `lif.dump` 24–27 ms), not a 1:1 remap of `spike_events`. `meta.tags` include `independent-lif-raster` and `sidecar-sim-only`. 007–010 also carry independent LIF excerpts (seeds 2007–2010).

## Reward formula and tick reconciliation

Declared aggregation on every record:

`total = task_progress + safety + efficiency + coherence + exploration`

Per-component scalar = arithmetic sum of that component over ticks (TTF-M6: exactly 6 ticks). Tick 6 is bound to a published sidecar (`abort_s`, `survey_s`, `dwell_s`) via `future_outcome.delayed_surprise_s` and is strictly after the raster window. Inflection `t_us` is an actual tick.

| id | ticks | tp | saf | eff | coh | exp | total | inflection tick |
|----|-------|----|-----|-----|-----|-----|-------|-----------------|
{chr(10).join(rew_rows)}

Tick-6 sidecar bind: 006 `abort_s=540`, 007 `survey_s=180`, 008 `abort_s=420`, 009 `dwell_s=90`, 010 `abort_s=1080`.

## Raster / energy (Loihi-2 4-core, 23 pJ/spike)

| id | domain | n | rate Hz | window_ms | spikes | energy_pJ | energy_uJ |
|----|--------|---|---------|-----------|--------|-----------|-----------|
{chr(10).join(ras_rows)}

`spikes = round(n × rate × window_s)`. Every record carries `gate_snn` whose `decision` matches the safety gate; populations that declare rate+spikes meet the same ±1 budget against `decision_window_s`. `routing.third_factor` has modulator (NA / ACh / DA / 5-HT / adenosine), `tau_e_s`/`tau_e_ms` pair, and eligibility. Excerpt same-neuron gap ≥ 1000 µs; spike trains same-channel refractory ≥ 0.8 ms. Excerpts are independent LIF membrane crossings, not a 1:1 remap of `spike_events` times (overlap < 0.8).

## Gaps this round fixes vs r01 NOTES

r01 asked r02 to rotate sit-outs onto `warehouse-amr`, `aerial-swarm`, `underwater-rov` plus two of {{industrial-assembly, grid-inspection}} with new plants; **wrong-reject** (even round); keep one partnered-neg in-window; keep 8-pool. This batch does that. Wrong-ACCEPT remains absent (guard). Independent LIF is labeled on all five records (r01 residual: only one).

## Local checks (this window)

Generator stdout: self_check (Jaccard, refractory, race, spike budget, energy, tick6 bind, gate_snn budget, rights). Then `json.loads` every line, `validate_run.check_line`, `raster_status`, `verify_batch_for_frontier(strict=True)`, `spike_probe.py --strict`.

Never `training_ready`. Never `sim_or_real=real`.

## Residual weaknesses (honest)

1. `industrial-assembly` and `grid-inspection` repeat r01 domain slugs (new plants and new gates; Jaccard vs r01 still < 0.4).
2. Wrong-ACCEPT still absent (guard).
3. Tick-6 sidecar bind is standing machinery (r14+), not a new class.
4. 010 humidity-as-trip is a false-positive REJECT; a later even round could densify wrong-reject on a lagged interlock instead of a context tag.
5. 007 HIL dummy payload never spins; a partnered HIL near-miss where MODIFY is correct but a delayed downwash still nicks the disk would densify the HIL class.

## Next densification target

Round 03: rotate remaining 8-pool sit-outs (`surgical-assist`, `autonomous-driving`, `humanoid-locomotion`) with new plants; **wrong-modify** (odd round); keep one partnered-neg in-window; consider ISI histogram sidecar.

Novel coverage: 38.0%
"""


def exclusive_write(path: Path, data: str):
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    fd = os.open(str(path), flags, 0o644)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(data)


def main():
    records = [rec_006(), rec_007(), rec_008(), rec_009(), rec_010()]
    errors, max_intra, max_prior, worst_prior, intra = validate_records(records)
    if errors:
        print("SELF-CHECK FAIL", file=sys.stderr)
        for e in errors:
            print(" ", e, file=sys.stderr)
        sys.exit(1)

    staging = Path("/tmp/ttf-r02-out")
    staging.mkdir(parents=True, exist_ok=True)
    jsonl = "\n".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) for r in records) + "\n"
    notes = notes_text(records, max_intra, max_prior, worst_prior, intra)
    (staging / "batch-r02.jsonl").write_text(jsonl, encoding="utf-8")
    (staging / "NOTES-r02.md").write_text(notes, encoding="utf-8")

    counts, findings, blocked = verify_batch_for_frontier(staging / "batch-r02.jsonl", strict=True)
    print("verify_batch", counts, "blocked", blocked)
    if findings:
        print("findings", findings)
    if blocked:
        sys.exit(2)

    # spike_probe --strict
    from spike_probe import load_rasters

    rasters, problems = load_rasters([staging / "batch-r02.jsonl"])
    print("spike_probe rasters", len(rasters), "problems", problems)
    if problems:
        sys.exit(3)
    if len(rasters) != 5:
        print("expected 5 rasters", len(rasters))
        sys.exit(3)

    live_batch = LIVE / "batch-r02.jsonl"
    live_notes = LIVE / "NOTES-r02.md"
    if live_batch.exists() or live_notes.exists():
        live_batch = LIVE / "batch-r02c.jsonl"
        live_notes = LIVE / "NOTES-r02c.md"
        if live_batch.exists() or live_notes.exists():
            print("collision: r02 and r02c exist", file=sys.stderr)
            sys.exit(4)

    exclusive_write(live_batch, jsonl)
    exclusive_write(live_notes, notes)
    print("WROTE", live_batch)
    print("WROTE", live_notes)
    print("max_intra", round(max_intra, 3), "max_prior", round(max_prior, 3), worst_prior)
    for r in records:
        sd = r["safety_decision"]
        print(
            r["id"],
            r["state"]["domain"],
            sd["decision"],
            sd["correctness"],
            r["state"]["sim_or_real"],
            r["reward_components"]["total"],
            r["meta"].get("supervisor_error_type"),
        )


if __name__ == "__main__":
    main()
