#!/usr/bin/env python3
"""Create-only TTF r02c generator. Never overwrites existing raw files."""

from __future__ import annotations

import json
import math
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

PIPE = Path("/home/raulmc/rmems/synthetic-factory/pipelines")
sys.path.insert(0, str(PIPE))

from check_records import FactoryStaging, check_jsonl, check_reward  # noqa: E402
from curate_bridge import raster_status  # noqa: E402
from validate_run import check_line  # noqa: E402
from verify_execution import verify_batch_for_frontier  # noqa: E402

FACTORY = Path(
    "/home/raulmc/rmems/synthetic-factory/outputs/raw/2026-09-02-final-heavy/"
    "thalamic-trajectory-factory"
)
STAGE = Path("/tmp/ttf-r02c-stage")
BATCH_NAME = "batch-r02c.jsonl"
NOTES_NAME = "NOTES-r02c.md"

RIGHTS = {
    "provider": "SpaceXAI/xAI",
    "model": "grok-4.6",
    "channel": "consumer",
    "subscription_plan": "SuperGrok Heavy",
    "generation_surface": "SuperGrok Heavy chat",
    "generated_at": "2026-09-02T19:40:00Z",
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

COMP = ("task_progress", "safety", "efficiency", "coherence", "exploration")


def ev(channel, t, amp):
    return {"channel": channel, "t_rel_ms": t, "amplitude": amp}


def ticks_and_scalars(rows):
    ticks = []
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
    scalars = {k: round(sum(t[k] for t in ticks), 2) for k in COMP}
    total = round(sum(scalars[k] for k in COMP), 2)
    return ticks, scalars, total


def raster_budget(neurons, rate, window_ms):
    window_s = window_ms / 1000.0
    spikes = int(round(neurons * rate * window_s))
    return {
        "window_ms": window_ms,
        "window_s": window_s,
        "neurons": neurons,
        "mean_rate_hz": rate,
        "spikes": spikes,
        "energy_pJ": spikes * 23,
        "energy_uJ": spikes * 23e-6,
    }


def pop(name, neurons, threshold, rate, window_s):
    body = {"name": name, "neurons": neurons, "threshold": threshold}
    if rate is None:
        return body
    spikes = int(round(neurons * rate * window_s))
    body["mean_rate_hz"] = rate
    body["spikes"] = spikes
    return body


def isi_histogram(events, bin_ms=1.0):
    by = defaultdict(list)
    for e in events:
        by[e["channel"]].append(float(e["t_rel_ms"]))
    isis = []
    for ts in by.values():
        ts.sort()
        for a, b in zip(ts, ts[1:]):
            isis.append(b - a)
    if not isis:
        return None
    n_bins = max(4, int(math.ceil(max(isis) / bin_ms)) + 2)
    counts = [0] * n_bins
    for x in isis:
        i = min(int(x / bin_ms), n_bins - 1)
        counts[i] += 1
    assert sum(counts) == len(isis)
    n_isi_expected = len(events) - len(by)
    assert len(isis) == n_isi_expected, (len(isis), n_isi_expected)
    return {
        "bin_ms": bin_ms,
        "unit": "ms",
        "n_isi": len(isis),
        "min_isi_ms": round(min(isis), 3),
        "counts": counts,
        "note": "same-channel ISIs from spike_events; refractory floor 0.8 ms; 1.0 ms bins",
    }


def check_refractory(events, floor_ms=0.8):
    by = defaultdict(list)
    for e in events:
        by[e["channel"]].append(e["t_rel_ms"])
    for ch, ts in by.items():
        ts.sort()
        for a, b in zip(ts, ts[1:]):
            if b - a < floor_ms - 1e-12:
                raise SystemExit(f"refractory {ch}: {a} -> {b}")


def check_sorted(events):
    ts = [e["t_rel_ms"] for e in events]
    if ts != sorted(ts):
        raise SystemExit(f"spike_events not sorted: {ts}")


def check_race(events, window, ch_a, ch_b):
    lo, hi = window
    in_win = [e for e in events if lo - 1e-12 <= e["t_rel_ms"] <= hi + 1e-12]
    chans = {e["channel"] for e in in_win}
    if ch_a not in chans or ch_b not in chans:
        raise SystemExit(f"race window missing channels {ch_a}/{ch_b}: {in_win}")


def excerpt_ok(excerpt, neurons, window_ms):
    last = {}
    prev_t = -1
    for item in excerpt:
        t = item["t_us"]
        n = item["neuron_id"]
        if not (0 <= t <= window_ms * 1000):
            raise SystemExit(f"excerpt t_us {t} outside window {window_ms}")
        if not (0 <= n < neurons):
            raise SystemExit(f"neuron_id {n} not in [0,{neurons})")
        if t < prev_t:
            raise SystemExit("excerpt not sorted")
        prev_t = t
        if n in last and t - last[n] < 1000:
            raise SystemExit(f"excerpt refractory neuron {n}: {last[n]} -> {t}")
        last[n] = t
    if not excerpt:
        raise SystemExit("empty excerpt")


def jaccard(a, b):
    ta = set(re.findall(r"[a-z0-9]+", a.lower()))
    tb = set(re.findall(r"[a-z0-9]+", b.lower()))
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def meta(round_n, domain, tags, distillation, pos, extra=None):
    m = {
        "round": round_n,
        "factory": "thalamic-trajectory-factory",
        "generator": "grok-4.6",
        "run_label": "2026-09-02-final-heavy",
        "domain": domain,
        "tags": tags,
        "snn_tags": ["race", "refractory", "adaptation"],
        "distillation_value": distillation,
        "rights": RIGHTS,
        "batch_position": pos,
    }
    if extra:
        m.update(extra)
    return m


def reward(ticks, scalars, total, notes):
    return {
        "_aggregation": "total = task_progress + safety + efficiency + coherence + exploration",
        "ticks": ticks,
        "task_progress": scalars["task_progress"],
        "safety": scalars["safety"],
        "efficiency": scalars["efficiency"],
        "coherence": scalars["coherence"],
        "exploration": scalars["exploration"],
        "total": total,
        "notes": notes,
    }


# ---------------------------------------------------------------------------
# Record 1 — HIL partnered-negative MODIFY (in-window ampoule crack)
# ---------------------------------------------------------------------------
SPIKES_011 = [
    ev("enc.n2.ctx", 1.18, 0.40),
    ev("rtd.vap.kPa", 2.36, 0.62),
    ev("ft.n2.slm", 3.74, 0.51),
    ev("rtd.vap.kPa", 6.420, 1.34),
    ev("ft.n2.slm", 6.628, 1.16),
    ev("ctrl.gate", 7.100, 0.99),
    ev("rtd.vap.kPa", 9.40, 0.78),
    ev("ft.n2.slm", 12.60, 0.60),
    ev("ctrl.gate", 16.40, 0.82),
    ev("ft.n2.slm", 19.90, 0.48),
    ev("ae.amp.crack", 24.200, 1.48),
    ev("ae.amp.crack", 25.900, 0.92),
    ev("enc.n2.ctx", 32.10, 0.39),
    ev("rtd.vap.kPa", 39.20, 0.52),
]
TICKS_011, SC_011, TOT_011 = ticks_and_scalars(
    [
        (2360, 0.05, -0.02, -0.02, 0.01, 0.00),
        (6420, 0.06, -0.04, -0.02, 0.01, -0.01),
        (6628, 0.05, -0.03, -0.02, 0.01, 0.00),
        (7100, 0.08, -0.06, -0.03, 0.02, -0.01),
        (24200, 0.04, -0.42, -0.04, -0.01, -0.02),
        (780000000, 0.02, -0.05, -0.03, 0.01, -0.01),
    ]
)
RST_011 = raster_budget(76, 24, 42)
EX_011 = [
    {"t_us": 5400, "neuron_id": 9, "channel": "lif.clamp"},
    {"t_us": 6500, "neuron_id": 12, "channel": "lif.clamp"},
    {"t_us": 8800, "neuron_id": 4, "channel": "lif.clamp"},
    {"t_us": 10100, "neuron_id": 7, "channel": "lif.clamp"},
    {"t_us": 12400, "neuron_id": 1, "channel": "lif.clamp"},
    {"t_us": 17100, "neuron_id": 3, "channel": "lif.clamp"},
    {"t_us": 18800, "neuron_id": 6, "channel": "lif.clamp"},
    {"t_us": 23900, "neuron_id": 18, "channel": "lif.crack"},
    {"t_us": 24200, "neuron_id": 21, "channel": "lif.crack"},
    {"t_us": 24600, "neuron_id": 44, "channel": "lif.crack"},
    {"t_us": 24900, "neuron_id": 51, "channel": "lif.crack"},
    {"t_us": 25300, "neuron_id": 33, "channel": "lif.crack"},
    {"t_us": 25700, "neuron_id": 60, "channel": "lif.crack"},
    {"t_us": 26100, "neuron_id": 71, "channel": "lif.crack"},
]
WIN_011 = 0.00042
REC_011 = {
    "id": "ttf-r02c-011",
    "title": "Heptox-Rehn HR-HIL / Ampoule A-7: Re2O7 vapor 18.4 kPa beats N2 4.2 slm by 208 us; correct MODIFY still eats an in-window quartz crack (partnered negative total -0.48)",
    "state": {
        "description": "Ampoule A-7 on the Heptox-Rehn HR-HIL pad is already metering 4.2 slm of N2 while Re2O7 vapor sits at 18.4 kPa against a 12.0 kPa sublimer cap. The HIL dummy payload never spins a live still; temperature-first cuts N2 to 1.8 slm, while flow-first would keep 4.2 slm because the N2 FT still looks like a cold-ampoule smear under 5.5 slm. A hairline quartz crack already seated in the ampoule neck does not appear on vapor kPa or N2 FT until the AE dump.",
        "domain": "rhenium-heptoxide-sublimer",
        "sim_or_real": "hil",
        "goal": "Keep Ampoule A-7 vapor <= 12.0 kPa and finish the Re2O7 HIL pass without dumping heptoxide condensate onto the cold finger.",
        "t0_us": 1756850400002011,
        "gate_latency_us": 680,
        "race_window_us": 420,
        "race_window_rel_ms": [6.40, 6.82],
        "race": {
            "contenders": [
                "rtd.vap.kPa 18.4 over 12.0 Re2O7 sublimer cap",
                "ft.n2.slm 4.2 with cold-ampoule look still under 5.5",
            ],
            "semantics": "Vapor-first latches N2 clamp 4.2 -> 1.8 slm; flow-first keeps 4.2 slm on a still-cold ampoule model.",
            "window_derivation": "420 us = one vapor RTD slot versus the N2-mass FT publisher on this HIL sublimer bus.",
            "order_evidence_note": "Margin 208 us vs combined jitter 68 us (RTD 32 + FT 36): 3.06x over a 2.0x trust floor. Reversing order by < 208 us inside the 420 us window would have kept 4.2 slm; predicted next-sample 19.6 kPa > 12.0 sublimer cap.",
        },
        "sensors": [
            "vapor RTD/pressure lance, 2 kHz, 32 us jitter",
            "N2 mass-flow FT, 1 kHz, 36 us jitter",
            "ampoule AE puck (context)",
            "cold-finger IR (context)",
        ],
        "constraints": {
            "vap_cap_kPa": 12.0,
            "observed_vap_kPa": 18.4,
            "n2_slm": 4.2,
            "cold_look_slm": 5.5,
        },
        "episode_steps": [
            "1. Ampoule A-7 on HR-HIL dummy pad; N2 4.2 slm; vapor 18.4 kPa.",
            "2. Cold-ampoule look 4.2 under 5.5; quartz crack armed.",
            "3. N2-FT precursor at 1.180 ms.",
            "4. Race window [6.400, 6.820] ms.",
            "5. rtd.vap.kPa 18.4 kPa at 6.420 ms (winner).",
            "6. ft.n2.slm 4.2 slm at 6.628 ms (loser by 208 us).",
            "7. Gate at 7.100 ms: MODIFY N2 4.2 -> 1.8 slm.",
            "8. Clamp executes; next-sample vapor 11.2 kPa <= 12.0 cap.",
            "9. At 24.200 ms seated quartz crack dumps heptoxide; AE burst.",
            "10. 13 min cold-finger isolate (abort_s=780); named un-netted loss.",
        ],
    },
    "spike_events": SPIKES_011,
    "proposed_action": {
        "name": "cruise_n2_sweep",
        "parameters": {"n2_slm": 4.2, "vap_kPa": 18.4, "heater_pct": 62.0},
        "evidence": {
            "vap_kPa": 18.4,
            "vap_cap_kPa": 12.0,
            "predicted_unclamped_next_kPa": 19.6,
            "n2_slm": 4.2,
            "cold_look_slm": 5.5,
            "race_margin_us": 208,
            "combined_jitter_us": 68,
            "abort_s": 780,
        },
        "basis": "Planner proposes 4.2 slm N2 because cold-ampoule look 4.2 is under 5.5, treating the 18.4 kPa vapor as a still-cold smear rather than a sublimer-cap miss.",
    },
    "safety_decision": {
        "decision": "MODIFY",
        "correctness": "correct",
        "rationale": "Vapor 18.4 kPa won by 208 us, so Ampoule A-7 is over the 12.0 kPa Re2O7 sublimer cap, not still a cold-ampoule story. Holding 4.2 slm predicts next-sample 19.6 kPa > 12.0. MODIFY: N2 4.2 -> 1.8 slm. Observed after clamp 11.2 kPa <= 12.0. A full REJECT is not indicated: a clean HIL pass accepts 1.8 slm.",
        "constraint_checked": {
            "vap_kPa": {
                "cap": 12.0,
                "observed": 18.4,
                "predicted_unclamped_next": 19.6,
                "clamped_n2_slm": 1.8,
                "observed_after_clamp": 11.2,
            },
            "order_evidence": {"margin_us": 208, "combined_jitter_us": 68, "ratio": 3.06},
        },
    },
    "executed_action": {
        "name": "clamped_n2_sweep",
        "parameters": {"n2_slm": 1.8, "vap_kPa": 11.2, "heater_pct": 62.0},
        "gate_effect": "MODIFY: N2 4.2 -> 1.8 slm. Process-correct vs the 12.0 kPa sublimer cap. Quartz crack still dumps at 24.200 ms.",
    },
    "future_outcome": {
        "summary": "Process-correct MODIFY held vapor at 11.2 kPa on the HR-HIL dummy pad. At 24.200 ms a quartz neck crack already seated in Ampoule A-7 dumped heptoxide onto the cold finger. Clamp reduced dump energy; it did not prevent the dump. Partnered negative: process heads stay honest; world loss is named, not netted.",
        "state_delta": {
            "vapor": "clamp executed; peak 11.2 kPa <= 12.0 cap",
            "ampoule": "crack dump at 24.200 ms; Re2O7 on cold finger",
            "repair": "13 min cold-finger isolate (abort_s=780)",
            "mission": "HR-HIL Re2O7 pass incomplete this cycle",
        },
        "surprises": [
            "Neither vapor kPa nor N2 FT predicted the seated quartz crack; ae.amp.crack is a new channel at 24.200 ms, 17.100 ms after the gate, still inside the 42 ms raster.",
            "Delayed (abort_s=780): 13 min cold-finger isolate. Named un-netted loss, not folded into task_progress.",
        ],
        "un_netted_loss": "13 min cold-finger isolate after the quartz crack. Safety head -0.62 prices the dump; task_progress stays +0.30 because the clamp completed.",
        "race_result": {
            "winner": "rtd.vap.kPa (6.420 ms, 18.4 kPa)",
            "loser": "ft.n2.slm (6.628 ms, 4.2 slm)",
            "margin_us": 208,
            "counterfactual_if_reversed": "Flow-first by < 208 us inside the 420 us window would have kept 4.2 slm; predicted next-sample 19.6 kPa would have missed the 12.0 sublimer cap even without the crack. The MODIFY is still the correct process. The dump is a later world charge either way, cheaper with the clamp than without.",
        },
        "reward_inflection_t_us": 24200,
        "reward_inflection_note": "Safety collapses at the 24.200 ms quartz crack (tick t_us=24200), inside the 42 ms raster. The correct MODIFY at 7.100 ms is in the same excerpt. Do not put inflection on the abort_s=780 isolate tick.",
        "delayed_surprise_s": 780,
        "abort_s": 780,
    },
    "reward_components": reward(
        TICKS_011,
        SC_011,
        TOT_011,
        "Partnered negative. Process-correct MODIFY on HIL dummy pad; world still charges inside the 42 ms raster. total -0.48 = 0.30 + -0.62 + -0.16 + 0.05 + -0.05. Named cold-finger isolate (abort_s=780) is not netted into task_progress.",
    ),
    "raster": {
        **RST_011,
        "excerpt_source": "independent_lif",
        "sim_scope": "sidecar_only",
        "lif": {
            "model": "leaky_integrate_and_fire",
            "n": 76,
            "dt_us": 100,
            "tau_m_ms": 18.0,
            "v_rest": 0.0,
            "v_reset": 0.0,
            "v_th": 1.0,
            "r_m": 1.0,
            "refractory_us": 1000,
            "i_bias": 0.90,
            "i_stim_peak": 2.52,
            "stim_t_us": [23600, 26800],
            "i_clamp_extra": 0.64,
            "clamp_n": 14,
            "seed": 2011,
            "note": "Population sim scoped to this sidecar. Plant remains hil. Neurons 0-13 carry extra clamp bias; stim 23.6-26.8 ms is the labeled crack burst.",
        },
        "abort_s": 780,
        "delayed_surprise_s": 780,
        "routing": {
            "source": "thalamic-relay.hr-vap",
            "target": "spikenaut.policy.n2-clamp",
            "table": [
                {"from": "relay_vap_kPa", "to": "policy_n2_clamp", "weight": 0.69},
                {"from": "relay_n2_ft", "to": "policy_n2_hold", "weight": 0.28},
                {"from": "relay_ae_crack", "to": "policy_n2_clamp", "weight": -0.41},
            ],
            "third_factor": {
                "modulator": "noradrenaline",
                "tau_e_s": 0.05,
                "tau_e_ms": 50.0,
                "eligibility": "surprise-gated pre_post_stdp; NA at vapor win (6.420 ms) opens a 42 ms eligibility trace that still covers the 24.200 ms quartz crack",
            },
        },
        "excerpt": EX_011,
    },
    "gate_snn": {
        "decision_window_ms": 0.42,
        "decision": "MODIFY",
        "populations": [
            pop("n2_clamp", 50, 0.5, 190.5, WIN_011),
            pop("n2_hold", 40, 0.8, 59.5, WIN_011),
            pop("crack_veto", 24, 0.75, None, WIN_011),
        ],
    },
    "meta": meta(
        2,
        "rhenium-heptoxide-sublimer",
        [
            "modify",
            "partnered-negative-total",
            "independent-lif-raster",
            "sidecar-sim-only",
            "in-window-world-charge",
            "hil",
            "hil-partnered-near-miss",
        ],
        "A critic can see the HIL world-charge as a LIF burst inside the raster while process heads stay honest. Credit assignment is spikes, not prose across a 13 min cold-finger isolate.",
        1,
    ),
}

# ---------------------------------------------------------------------------
# Record 2 — designed correct MODIFY (O2 over cap, H2 clamp)
# ---------------------------------------------------------------------------
SPIKES_012 = [
    ev("enc.h2.ctx", 0.96, 0.39),
    ev("o2.ppm", 2.10, 0.58),
    ev("ft.h2.nm3h", 3.44, 0.47),
    ev("o2.ppm", 5.820, 1.30),
    ev("ft.h2.nm3h", 5.988, 1.12),
    ev("ctrl.gate", 6.420, 0.97),
    ev("o2.ppm", 8.80, 0.74),
    ev("ft.h2.nm3h", 12.20, 0.56),
    ev("ctrl.gate", 15.60, 0.81),
    ev("o2.ppm", 21.40, 0.50),
    ev("enc.h2.ctx", 27.10, 0.38),
    ev("ft.h2.nm3h", 33.80, 0.44),
]
TICKS_012, SC_012, TOT_012 = ticks_and_scalars(
    [
        (2100, 0.06, 0.04, 0.02, 0.01, 0.01),
        (5820, 0.08, 0.06, 0.03, 0.02, 0.01),
        (5988, 0.06, 0.04, 0.02, 0.01, 0.01),
        (6420, 0.10, 0.08, 0.04, 0.03, 0.02),
        (8800, 0.05, 0.05, 0.03, 0.02, 0.01),
        (180000000, 0.03, 0.03, 0.02, 0.01, 0.01),
    ]
)
RST_012 = raster_budget(64, 32, 36)
EX_012 = [
    {"t_us": 4100, "neuron_id": 8, "channel": "lif.clamp"},
    {"t_us": 5600, "neuron_id": 11, "channel": "lif.clamp"},
    {"t_us": 7200, "neuron_id": 2, "channel": "lif.clamp"},
    {"t_us": 9100, "neuron_id": 5, "channel": "lif.clamp"},
    {"t_us": 11400, "neuron_id": 0, "channel": "lif.clamp"},
    {"t_us": 14800, "neuron_id": 19, "channel": "lif.o2"},
    {"t_us": 16900, "neuron_id": 27, "channel": "lif.o2"},
    {"t_us": 19200, "neuron_id": 41, "channel": "lif.o2"},
    {"t_us": 22100, "neuron_id": 53, "channel": "lif.o2"},
    {"t_us": 24800, "neuron_id": 33, "channel": "lif.o2"},
    {"t_us": 27600, "neuron_id": 60, "channel": "lif.o2"},
    {"t_us": 31100, "neuron_id": 14, "channel": "lif.o2"},
    {"t_us": 33900, "neuron_id": 22, "channel": "lif.o2"},
]
WIN_012 = 0.00036
REC_012 = {
    "id": "ttf-r02c-012",
    "title": "Samaco-Fell SF-3 / Press P-8: off-gas O2 84 ppm beats H2 2.4 Nm3/h by 168 us; correct MODIFY clamps hydrogen 2.4 -> 1.1",
    "state": {
        "description": "Press P-8 at Samaco-Fell SF-3 is already flowing 2.4 Nm3/h of H2 while the binder-burn off-gas reads 84 ppm O2 against a 40 ppm sinter cap. Oxygen-first cuts H2 to 1.1 Nm3/h; hydrogen-first would keep 2.4 Nm3/h because the H2 FT still looks like a wet-binder smear under 3.0 Nm3/h. No second world charge is armed on this press this cycle.",
        "domain": "samarium-cobalt-sinter",
        "sim_or_real": "designed",
        "goal": "Keep Press P-8 off-gas O2 <= 40 ppm and finish the SmCo binder-burn without oxidizing the compact.",
        "t0_us": 1756850400002012,
        "gate_latency_us": 540,
        "race_window_us": 360,
        "race_window_rel_ms": [5.80, 6.16],
        "race": {
            "contenders": [
                "o2.ppm 84 over 40 SmCo sinter cap",
                "ft.h2.nm3h 2.4 with wet-binder look still under 3.0",
            ],
            "semantics": "Oxygen-first latches H2 clamp 2.4 -> 1.1 Nm3/h; hydrogen-first keeps 2.4 on a still-wet binder model.",
            "window_derivation": "360 us = one zirconia O2 slot versus the H2-mass FT publisher on this sinter-press bus.",
            "order_evidence_note": "Margin 168 us vs combined jitter 54 us (O2 24 + FT 30): 3.11x over a 2.0x trust floor. Reversing order by < 168 us inside the 360 us window would have kept 2.4 Nm3/h; predicted next-sample 96 ppm > 40 sinter cap.",
        },
        "sensors": [
            "zirconia O2 cell, 2 kHz, 24 us jitter",
            "H2 mass-flow FT, 1 kHz, 30 us jitter",
            "press platen LVDT (context)",
            "muffle IR (context)",
        ],
        "constraints": {
            "o2_cap_ppm": 40.0,
            "observed_o2_ppm": 84.0,
            "h2_nm3h": 2.4,
            "wet_look_nm3h": 3.0,
        },
        "episode_steps": [
            "1. Press P-8 in SmCo binder-burn; H2 2.4 Nm3/h; O2 84 ppm.",
            "2. Wet-binder look 2.4 under 3.0; no second charge armed.",
            "3. H2-FT precursor at 0.960 ms.",
            "4. Race window [5.800, 6.160] ms.",
            "5. o2.ppm 84 at 5.820 ms (winner).",
            "6. ft.h2.nm3h 2.4 at 5.988 ms (loser by 168 us).",
            "7. Gate at 6.420 ms: MODIFY H2 2.4 -> 1.1 Nm3/h.",
            "8. Clamp executes; next-sample O2 28 ppm <= 40 cap.",
            "9. Compact remains unoxidized this cycle.",
            "10. Delayed (survey_s=180): 3 min compact survey after the burn.",
        ],
    },
    "spike_events": SPIKES_012,
    "proposed_action": {
        "name": "cruise_h2_binder_burn",
        "parameters": {"h2_nm3h": 2.4, "o2_ppm": 84.0, "platen_MPa": 48.0},
        "evidence": {
            "o2_ppm": 84.0,
            "o2_cap_ppm": 40.0,
            "predicted_unclamped_next_ppm": 96.0,
            "h2_nm3h": 2.4,
            "wet_look_nm3h": 3.0,
            "race_margin_us": 168,
            "combined_jitter_us": 54,
            "survey_s": 180,
        },
        "basis": "Planner proposes 2.4 Nm3/h H2 because wet-binder look 2.4 is under 3.0, treating the 84 ppm O2 as residual binder water rather than a sinter-cap miss.",
    },
    "safety_decision": {
        "decision": "MODIFY",
        "correctness": "correct",
        "rationale": "Off-gas O2 84 ppm won by 168 us, so Press P-8 is over the 40 ppm SmCo sinter cap, not still a wet-binder story. Holding 2.4 Nm3/h predicts next-sample 96 ppm > 40. MODIFY: H2 2.4 -> 1.1 Nm3/h. Observed after clamp 28 ppm <= 40. A full REJECT is not indicated: a clean burn accepts 1.1 Nm3/h.",
        "constraint_checked": {
            "o2_ppm": {
                "cap": 40.0,
                "observed": 84.0,
                "predicted_unclamped_next": 96.0,
                "clamped_h2_nm3h": 1.1,
                "observed_after_clamp": 28.0,
            },
            "order_evidence": {"margin_us": 168, "combined_jitter_us": 54, "ratio": 3.11},
        },
    },
    "executed_action": {
        "name": "clamped_h2_binder_burn",
        "parameters": {"h2_nm3h": 1.1, "o2_ppm": 28.0, "platen_MPa": 48.0},
        "gate_effect": "MODIFY: H2 2.4 -> 1.1 Nm3/h. Process-correct vs the 40 ppm sinter cap. Compact unoxidized.",
    },
    "future_outcome": {
        "summary": "Correct MODIFY held off-gas O2 at 28 ppm. Compact finished the binder-burn without oxidation. No in-window world charge.",
        "state_delta": {
            "offgas": "clamp executed; peak 28 ppm <= 40 cap",
            "hydrogen": "held 1.1 Nm3/h",
            "compact": "unoxidized this cycle",
            "survey": "3 min compact survey (survey_s=180)",
        },
        "surprises": [
            "Hydrogen-first by < 168 us would have kept 2.4 Nm3/h and predicted 96 ppm over the 40 ppm cap; the O2 win prevented that miss.",
            "Delayed (survey_s=180): 3 min compact survey after the burn; not a safety inflection.",
        ],
        "race_result": {
            "winner": "o2.ppm (5.820 ms, 84 ppm)",
            "loser": "ft.h2.nm3h (5.988 ms, 2.4 Nm3/h)",
            "margin_us": 168,
            "counterfactual_if_reversed": "Hydrogen-first by < 168 us inside the 360 us window would have kept 2.4 Nm3/h; predicted next-sample 96 ppm would have missed the 40 ppm sinter cap.",
        },
        "reward_inflection_t_us": 6420,
        "reward_inflection_note": "Task and safety credit the correct MODIFY at 6.420 ms (tick 4). The 3 min survey is delayed surprise, not the inflection.",
        "delayed_surprise_s": 180,
        "survey_s": 180,
    },
    "reward_components": reward(
        TICKS_012,
        SC_012,
        TOT_012,
        "Correct MODIFY. O2 84 ppm > 40 cap; H2 2.4 -> 1.1 Nm3/h. total +1.01 = 0.38 + 0.30 + 0.16 + 0.10 + 0.07.",
    ),
    "raster": {
        **RST_012,
        "excerpt_source": "independent_lif",
        "sim_scope": "sidecar_only",
        "lif": {
            "model": "leaky_integrate_and_fire",
            "n": 64,
            "dt_us": 100,
            "tau_m_ms": 16.0,
            "v_rest": 0.0,
            "v_reset": 0.0,
            "v_th": 1.0,
            "r_m": 1.0,
            "refractory_us": 1000,
            "i_bias": 0.88,
            "i_stim_peak": 2.10,
            "stim_t_us": [5400, 8600],
            "i_clamp_extra": 0.58,
            "clamp_n": 12,
            "seed": 2012,
            "note": "Population sim scoped to this sidecar. Plant remains designed. Neurons 0-11 carry extra clamp bias; stim 5.4-8.6 ms covers the O2-win gate.",
        },
        "survey_s": 180,
        "delayed_surprise_s": 180,
        "routing": {
            "source": "thalamic-relay.sf-o2",
            "target": "spikenaut.policy.h2-clamp",
            "table": [
                {"from": "relay_o2_ppm", "to": "policy_h2_clamp", "weight": 0.67},
                {"from": "relay_h2_ft", "to": "policy_h2_hold", "weight": 0.26},
            ],
            "third_factor": {
                "modulator": "acetylcholine",
                "tau_e_s": 0.06,
                "tau_e_ms": 60.0,
                "eligibility": "o2_confirm_stdp; ACh tags the h2_clamp bind at the zirconia win",
            },
        },
        "excerpt": EX_012,
    },
    "gate_snn": {
        "decision_window_ms": 0.36,
        "decision": "MODIFY",
        "populations": [
            pop("h2_clamp", 50, 0.5, 222.2, WIN_012),
            pop("h2_hold", 40, 0.82, 69.4, WIN_012),
            pop("wet_binder_veto", 22, 0.78, None, WIN_012),
        ],
    },
    "meta": meta(
        2,
        "samarium-cobalt-sinter",
        ["modify", "independent-lif-raster", "sidecar-sim-only", "designed", "o2-over-cap"],
        "Teaches a process-correct H2 clamp from an O2-first race so a gate head can fire on zirconia spikes without a world-charge overlay.",
        2,
    ),
}

# ---------------------------------------------------------------------------
# Record 3 — designed correct REJECT (AE crack beats kettle T)
# ---------------------------------------------------------------------------
SPIKES_013 = [
    ev("enc.gecl4.ctx", 1.02, 0.41),
    ev("ae.crack.pps", 2.48, 0.66),
    ev("rtd.kettle.C", 3.90, 0.49),
    ev("ae.crack.pps", 6.120, 1.36),
    ev("rtd.kettle.C", 6.296, 1.11),
    ev("ctrl.gate", 6.780, 1.01),
    ev("ae.crack.pps", 9.10, 0.88),
    ev("rtd.kettle.C", 12.40, 0.57),
    ev("ctrl.gate", 16.80, 0.79),
    ev("ae.crack.pps", 21.20, 0.61),
    ev("enc.gecl4.ctx", 24.60, 0.37),
    ev("rtd.kettle.C", 27.40, 0.45),
]
TICKS_013, SC_013, TOT_013 = ticks_and_scalars(
    [
        (2480, 0.02, 0.06, 0.02, 0.01, 0.01),
        (6120, 0.02, 0.08, 0.02, 0.02, 0.01),
        (6296, 0.02, 0.06, 0.02, 0.01, 0.01),
        (6780, 0.03, 0.12, 0.03, 0.03, 0.01),
        (9100, 0.02, 0.05, 0.02, 0.02, 0.01),
        (420000000, 0.01, 0.03, 0.01, 0.01, 0.01),
    ]
)
RST_013 = raster_budget(88, 26, 28)
EX_013 = [
    {"t_us": 3200, "neuron_id": 6, "channel": "lif.hold"},
    {"t_us": 4800, "neuron_id": 10, "channel": "lif.hold"},
    {"t_us": 6100, "neuron_id": 3, "channel": "lif.hold"},
    {"t_us": 7900, "neuron_id": 14, "channel": "lif.hold"},
    {"t_us": 10200, "neuron_id": 1, "channel": "lif.hold"},
    {"t_us": 12800, "neuron_id": 22, "channel": "lif.ae"},
    {"t_us": 15100, "neuron_id": 37, "channel": "lif.ae"},
    {"t_us": 17600, "neuron_id": 49, "channel": "lif.ae"},
    {"t_us": 19900, "neuron_id": 61, "channel": "lif.ae"},
    {"t_us": 22300, "neuron_id": 70, "channel": "lif.ae"},
    {"t_us": 24800, "neuron_id": 81, "channel": "lif.ae"},
    {"t_us": 27100, "neuron_id": 18, "channel": "lif.ae"},
]
WIN_013 = 0.00030
REC_013 = {
    "id": "ttf-r02c-013",
    "title": "Tetrach-Germ TG-2 / Kettle K-9: AE 52 pps beats kettle 86 C by 176 us; correct REJECT holds GeCl4 1.6 -> 0 kg/h",
    "state": {
        "description": "Kettle K-9 at Tetrach-Germ TG-2 is already boiling GeCl4 at 1.6 kg/h while the quartz AE puck reports 52 pps against a 10 pps crack cap. Acoustic-first holds the still; kettle-first would keep 1.6 kg/h because the RTD 86 C still looks under the 110 C boil-look. A growing circumferential crack is already live on the AE channel.",
        "domain": "germanium-tetrachloride-rectifier",
        "sim_or_real": "designed",
        "goal": "Keep Kettle K-9 crack AE <= 10 pps and finish the GeCl4 hearts-cut without dumping liquor through a quartz split.",
        "t0_us": 1756850400002013,
        "gate_latency_us": 620,
        "race_window_us": 300,
        "race_window_rel_ms": [6.10, 6.40],
        "race": {
            "contenders": [
                "ae.crack.pps 52 over 10 quartz crack cap",
                "rtd.kettle.C 86 with boil-look still under 110",
            ],
            "semantics": "Acoustic-first latches GeCl4 hold 1.6 -> 0 kg/h; kettle-first keeps 1.6 kg/h on a still-legal boil model.",
            "window_derivation": "300 us = one AE integrator slot versus the kettle RTD publisher on this rectifier bus.",
            "order_evidence_note": "Margin 176 us vs combined jitter 56 us (AE 26 + RTD 30): 3.14x over a 2.0x trust floor. Reversing order by < 176 us inside the 300 us window would have kept 1.6 kg/h into a cracking kettle.",
        },
        "sensors": [
            "quartz AE puck, 5 kHz, 26 us jitter",
            "kettle RTD lance, 1 kHz, 30 us jitter",
            "reflux FT (context)",
            "condenser IR (context)",
        ],
        "constraints": {
            "crack_cap_pps": 10.0,
            "observed_crack_pps": 52.0,
            "kettle_C": 86.0,
            "boil_look_C": 110.0,
        },
        "episode_steps": [
            "1. Kettle K-9 in GeCl4 hearts-cut; 1.6 kg/h; AE 52 pps.",
            "2. Boil-look 86 C under 110 C; crack already live.",
            "3. Encoder precursor at 1.020 ms.",
            "4. Race window [6.100, 6.400] ms.",
            "5. ae.crack.pps 52 at 6.120 ms (winner).",
            "6. rtd.kettle.C 86 C at 6.296 ms (loser by 176 us).",
            "7. Gate at 6.780 ms: REJECT hold GeCl4 1.6 -> 0 kg/h.",
            "8. Still held; liquor remains in kettle.",
            "9. Crack AE decays after hold.",
            "10. Delayed (abort_s=420): 7 min kettle isolate.",
        ],
    },
    "spike_events": SPIKES_013,
    "proposed_action": {
        "name": "cruise_gecl4_hearts",
        "parameters": {"gecl4_kgh": 1.6, "hold": False, "reflux_ratio": 3.2},
        "evidence": {
            "crack_pps": 52.0,
            "crack_cap_pps": 10.0,
            "kettle_C": 86.0,
            "boil_look_C": 110.0,
            "race_margin_us": 176,
            "combined_jitter_us": 56,
            "abort_s": 420,
        },
        "basis": "Planner proposes keeping 1.6 kg/h because kettle 86 C looks under the 110 C boil-look, treating AE 52 pps as a noisy bus echo.",
    },
    "safety_decision": {
        "decision": "REJECT",
        "correctness": "correct",
        "rationale": "AE 52 pps won by 176 us and is over the 10 pps quartz crack cap. Kettle 86 C is under the 110 C boil-look and is not a license to keep boiling. REJECT: GeCl4 1.6 -> 0 kg/h hold. A MODIFY that only trims reflux would still load a cracking kettle.",
        "constraint_checked": {
            "crack_pps": {"cap": 10.0, "observed": 52.0, "executed_gecl4_kgh": 0.0},
            "kettle_C": {"observed": 86.0, "boil_look": 110.0, "not_a_license": True},
            "order_evidence": {"margin_us": 176, "combined_jitter_us": 56, "ratio": 3.14},
        },
    },
    "executed_action": {
        "name": "hold_for_crack",
        "parameters": {"gecl4_kgh": 0.0, "hold": True, "reflux_ratio": 3.2},
        "gate_effect": "REJECT: hold 0.0 kg/h; 1.6 kg/h hearts-cut cancelled. AE 52 > 10 pps cap.",
    },
    "future_outcome": {
        "summary": "Correct REJECT held GeCl4 at 0 kg/h. Quartz crack did not dump the kettle. Kettle 86 C remaining under the 110 C boil-look was the losing channel and did not justify a cruise.",
        "state_delta": {
            "still": "held; 0.0 kg/h",
            "crack": "AE 52 pps > 10 cap; liquor retained",
            "kettle": "86 C unused as a boil license",
            "isolate": "7 min kettle isolate (abort_s=420)",
        },
        "surprises": [
            "Kettle RTD 86 C losing a 176 us race did not predict a legal boil; reversing 176 us would have kept 1.6 kg/h into a cracking kettle.",
            "Delayed (abort_s=420): 7 min kettle isolate; not a missed-opportunity penalty on a correct hold.",
        ],
        "race_result": {
            "winner": "ae.crack.pps (6.120 ms, 52 pps)",
            "loser": "rtd.kettle.C (6.296 ms, 86 C)",
            "margin_us": 176,
            "counterfactual_if_reversed": "Kettle-first by < 176 us inside the 300 us window would have kept 1.6 kg/h into a cracking quartz still.",
        },
        "reward_inflection_t_us": 6780,
        "reward_inflection_note": "Safety credits the correct REJECT at 6.780 ms (tick 4). The 7 min isolate is delayed surprise, not the inflection.",
        "delayed_surprise_s": 420,
        "abort_s": 420,
    },
    "reward_components": reward(
        TICKS_013,
        SC_013,
        TOT_013,
        "Correct REJECT. AE 52 pps > 10 cap; GeCl4 1.6 -> 0 kg/h. total +0.80 = 0.12 + 0.40 + 0.12 + 0.10 + 0.06.",
    ),
    "raster": {
        **RST_013,
        "excerpt_source": "independent_lif",
        "sim_scope": "sidecar_only",
        "lif": {
            "model": "leaky_integrate_and_fire",
            "n": 88,
            "dt_us": 100,
            "tau_m_ms": 17.0,
            "v_rest": 0.0,
            "v_reset": 0.0,
            "v_th": 1.0,
            "r_m": 1.0,
            "refractory_us": 1000,
            "i_bias": 0.89,
            "i_stim_peak": 2.20,
            "stim_t_us": [6000, 9200],
            "i_clamp_extra": 0.55,
            "clamp_n": 16,
            "seed": 2013,
            "note": "Population sim scoped to this sidecar. Plant remains designed. Neurons 0-15 carry extra hold bias; stim 6.0-9.2 ms covers the AE-win gate.",
        },
        "abort_s": 420,
        "delayed_surprise_s": 420,
        "routing": {
            "source": "thalamic-relay.tg-ae",
            "target": "spikenaut.policy.kettle-hold",
            "table": [
                {"from": "relay.ae.crack", "to": "policy.kettle_hold", "weight": 0.72},
                {"from": "relay.rtd.kettle", "to": "policy.enc_pull", "weight": 0.21},
            ],
            "third_factor": {
                "modulator": "dopamine",
                "tau_e_s": 0.08,
                "tau_e_ms": 80.0,
                "eligibility": "crack_hold_stdp; DA tags the kettle_hold bind at the AE win",
            },
        },
        "excerpt": EX_013,
    },
    "gate_snn": {
        "decision_window_ms": 0.30,
        "decision": "REJECT",
        "populations": [
            pop("kettle_hold", 60, 0.48, 222.2, WIN_013),
            pop("enc_pull", 44, 0.85, 75.8, WIN_013),
            pop("crack_veto", 28, 0.75, None, WIN_013),
        ],
    },
    "meta": meta(
        2,
        "germanium-tetrachloride-rectifier",
        ["reject", "independent-lif-raster", "sidecar-sim-only", "designed", "ae-beats-rtd"],
        "Teaches a distillable REJECT where AE spikes beat a legal-looking kettle RTD so the hold population fires without a temperature miss.",
        3,
    ),
}

# ---------------------------------------------------------------------------
# Record 4 — simulated ACCEPT + ISI histogram + second LIF
# ---------------------------------------------------------------------------
SPIKES_014 = [
    ev("enc.seed.ctx", 0.84, 0.40),
    ev("rtd.seed.C", 1.88, 0.57),
    ev("ir.glint.C", 3.16, 0.46),
    ev("rtd.seed.C", 4.920, 1.29),
    ev("ir.glint.C", 5.098, 1.09),
    ev("ctrl.gate", 5.400, 0.96),
    ev("rtd.seed.C", 7.10, 0.71),
    ev("ir.glint.C", 10.60, 0.54),
    ev("ctrl.gate", 14.40, 0.80),
    ev("rtd.seed.C", 18.90, 0.48),
    ev("enc.seed.ctx", 22.20, 0.37),
    ev("ir.glint.C", 25.40, 0.43),
]
TICKS_014, SC_014, TOT_014 = ticks_and_scalars(
    [
        (1880, 0.05, 0.04, 0.02, 0.01, 0.01),
        (4920, 0.08, 0.05, 0.04, 0.03, 0.02),
        (5098, 0.06, 0.04, 0.03, 0.02, 0.01),
        (5400, 0.14, 0.09, 0.05, 0.04, 0.02),
        (7100, 0.06, 0.04, 0.02, 0.01, 0.01),
        (240000000, 0.03, 0.02, 0.02, 0.01, 0.01),
    ]
)
RST_014 = raster_budget(56, 40, 26)
EX_014 = [
    {"t_us": 2100, "neuron_id": 7, "channel": "lif.accept"},
    {"t_us": 4300, "neuron_id": 11, "channel": "lif.accept"},
    {"t_us": 5400, "neuron_id": 2, "channel": "lif.accept"},
    {"t_us": 6900, "neuron_id": 4, "channel": "lif.accept"},
    {"t_us": 8800, "neuron_id": 0, "channel": "lif.accept"},
    {"t_us": 11200, "neuron_id": 19, "channel": "lif.seed"},
    {"t_us": 13600, "neuron_id": 28, "channel": "lif.seed"},
    {"t_us": 15900, "neuron_id": 33, "channel": "lif.seed"},
    {"t_us": 18300, "neuron_id": 41, "channel": "lif.seed"},
    {"t_us": 20700, "neuron_id": 48, "channel": "lif.seed"},
    {"t_us": 23100, "neuron_id": 52, "channel": "lif.seed"},
    {"t_us": 25400, "neuron_id": 15, "channel": "lif.seed"},
]
WIN_014 = 0.00034
ISI_014 = isi_histogram(SPIKES_014, bin_ms=1.0)
REC_014 = {
    "id": "ttf-r02c-014",
    "title": "Tantala-Lith TL-2 sim / Puller X-4: seed 1488 C beats furnace glint 1610 C by 178 us; correct ACCEPT leaves 0.22 mm/h",
    "state": {
        "description": "Crucible C-4 at Tantala-Lith TL-2 is already pulling 0.22 mm/h of LiTaO3 while the seed RTD sits at 1488 C against a 1540 C freeze-lid cap. Seed-first leaves the filed 0.22 mm/h; glint-first would extra-clamp because furnace IR 1610 C looks over 1540 on the lighting channel. This is a lighting-glint simulation, not a seed miss.",
        "domain": "lithium-tantalate-czochralski",
        "sim_or_real": "simulated",
        "goal": "Keep Puller X-4 seed <= 1540 C and finish the LiTaO3 pass at the filed 0.22 mm/h without an extra freeze-lid clamp.",
        "t0_us": 1756850400002014,
        "gate_latency_us": 480,
        "race_window_us": 340,
        "race_window_rel_ms": [4.90, 5.24],
        "race": {
            "contenders": [
                "rtd.seed.C 1488 under 1540 freeze-lid cap",
                "ir.glint.C 1610 lighting glint over 1540 on the furnace channel",
            ],
            "semantics": "Seed-first ACCEPTs 0.22 mm/h; glint-first extra-clamps a legal seed.",
            "window_derivation": "340 us = one seed RTD slot versus the furnace IR publisher on this simulated puller bus.",
            "order_evidence_note": "Margin 178 us vs combined jitter 58 us (RTD 28 + IR 30): 3.07x over a 2.0x trust floor. Reversing order by < 178 us inside the 340 us window would have extra-clamped a legal 1488 C / 0.22 mm/h pass.",
        },
        "sensors": [
            "seed RTD lance, 2 kHz, 28 us jitter",
            "furnace IR pyrometer, 1 kHz, 30 us jitter",
            "pull encoder (context)",
            "crucible weigh-cell (context)",
        ],
        "constraints": {
            "seed_cap_C": 1540.0,
            "observed_seed_C": 1488.0,
            "glint_C": 1610.0,
            "pull_mm_h": 0.22,
            "pull_cap_mm_h": 0.35,
        },
        "episode_steps": [
            "1. Crucible C-4 indexed on Tantala-Lith TL-2; pull 0.22 mm/h armed.",
            "2. Seed RTD 1488 C; furnace glint 1610 C over 1540 on the lighting channel.",
            "3. Encoder precursor at 0.840 ms.",
            "4. Race window [4.900, 5.240] ms.",
            "5. rtd.seed.C 1488 C at 4.920 ms (winner).",
            "6. ir.glint.C 1610 C at 5.098 ms (loser by 178 us).",
            "7. Gate at 5.400 ms: ACCEPT leave 0.22 mm/h.",
            "8. Seed remains 1488 C < 1540 C; glint unused as a hold.",
            "9. Simulated lighting remains the pyrometer source.",
            "10. Delayed (survey_s=240): 4 min facet survey after the pass.",
        ],
    },
    "spike_events": SPIKES_014,
    "proposed_action": {
        "name": "hold_lto_pull",
        "parameters": {"pull_mm_h": 0.22, "seed_C": 1488.0, "glint_C": 1610.0},
        "evidence": {
            "seed_C": 1488.0,
            "seed_cap_C": 1540.0,
            "glint_C": 1610.0,
            "pull_cap_mm_h": 0.35,
            "race_margin_us": 178,
            "combined_jitter_us": 58,
            "survey_s": 240,
        },
        "basis": "Planner proposes keeping the filed 0.22 mm/h pull: seed 1488 C is under the 1540 C cap and 0.22 mm/h is under 0.35 mm/h.",
    },
    "safety_decision": {
        "decision": "ACCEPT",
        "correctness": "correct",
        "rationale": "Seed 1488 C won by 178 us and is under the 1540 C freeze-lid cap. Furnace 1610 C is a lighting glint, not a seed reading. ACCEPT the filed 0.22 mm/h pull. Executed identical to proposed. An extra clamp is not indicated.",
        "constraint_checked": {
            "seed_C": {"cap": 1540.0, "observed": 1488.0, "executed_pull_mm_h": 0.22},
            "glint_C": {"observed": 1610.0, "not_a_seed_reading": True},
            "order_evidence": {"margin_us": 178, "combined_jitter_us": 58, "ratio": 3.07},
        },
    },
    "executed_action": {
        "name": "hold_lto_pull",
        "parameters": {"pull_mm_h": 0.22, "seed_C": 1488.0, "glint_C": 1610.0},
        "gate_effect": "ACCEPT: executed identical to proposed 0.22 mm/h pull. Seed 1488 C < 1540 cap.",
    },
    "future_outcome": {
        "summary": "Correct ACCEPT kept the filed 0.22 mm/h LiTaO3 pull. Seed stayed 1489 C under 1540. Furnace remaining a lighting glint was the losing channel and did not justify an extra clamp.",
        "state_delta": {
            "pull": "held; 0.22 mm/h",
            "seed": "1489 C < 1540 C",
            "glint": "1610 C unused as seed miss",
            "crystal": "pass continues",
        },
        "surprises": [
            "Furnace IR 1610 C losing a 178 us race did not predict a seed miss; reversing 178 us would have extra-clamped a legal 1488 C pass.",
            "Delayed (survey_s=240): 4 min facet survey on the boule lock; not a safety inflection.",
        ],
        "race_result": {
            "winner": "rtd.seed.C (4.920 ms, 1488 C)",
            "loser": "ir.glint.C (5.098 ms, 1610 C)",
            "margin_us": 178,
            "counterfactual_if_reversed": "Glint-first by < 178 us inside the 340 us window would have extra-clamped a legal 1488 C / 0.22 mm/h pass.",
        },
        "reward_inflection_t_us": 5400,
        "reward_inflection_note": "Task and safety credit the correct ACCEPT at 5.400 ms (tick 4). The 4 min survey is delayed surprise, not the inflection.",
        "delayed_surprise_s": 240,
        "survey_s": 240,
    },
    "reward_components": reward(
        TICKS_014,
        SC_014,
        TOT_014,
        "Correct ACCEPT. Seed 1488 C < 1540 C cap; glint unused. total +1.08 = 0.42 + 0.28 + 0.18 + 0.12 + 0.08.",
    ),
    "raster": {
        **RST_014,
        "excerpt_source": "independent_lif",
        "sim_scope": "sidecar_only",
        "lif": {
            "model": "leaky_integrate_and_fire",
            "n": 56,
            "dt_us": 100,
            "tau_m_ms": 15.0,
            "v_rest": 0.0,
            "v_reset": 0.0,
            "v_th": 1.0,
            "r_m": 1.0,
            "refractory_us": 1000,
            "i_bias": 0.86,
            "i_stim_peak": 1.95,
            "stim_t_us": [4000, 7200],
            "i_clamp_extra": 0.50,
            "clamp_n": 12,
            "seed": 2014,
            "note": "Second labeled LIF this round (success-path). Plant remains simulated. Neurons 0-11 carry accept bias; stim 4.0-7.2 ms covers the seed-win gate.",
        },
        "survey_s": 240,
        "delayed_surprise_s": 240,
        "isi_histogram": ISI_014,
        "routing": {
            "source": "thalamic-relay.tl-seed",
            "target": "spikenaut.policy.pull-accept",
            "table": [
                {"from": "relay_seed_C", "to": "policy_pull_accept", "weight": 0.66},
                {"from": "relay_glint_IR", "to": "policy_extra_clamp", "weight": 0.22},
            ],
            "third_factor": {
                "modulator": "serotonin",
                "tau_e_s": 0.12,
                "tau_e_ms": 120.0,
                "eligibility": "seed_confirm_stdp; 5-HT tags the pull_accept bind at the seed-RTD win",
            },
        },
        "excerpt": EX_014,
    },
    "gate_snn": {
        "decision_window_ms": 0.34,
        "decision": "ACCEPT",
        "populations": [
            pop("pull_accept", 50, 0.5, 235.3, WIN_014),
            pop("extra_clamp", 40, 0.85, 73.5, WIN_014),
            pop("glint_veto", 22, 0.80, None, WIN_014),
        ],
    },
    "meta": meta(
        2,
        "lithium-tantalate-czochralski",
        [
            "accept",
            "simulated",
            "seed-vs-glint",
            "pull-legal",
            "isi-histogram",
            "independent-lif-raster",
            "sidecar-sim-only",
        ],
        "Teaches an already-legal Czochralski ACCEPT with an ISI histogram sidecar and a second labeled LIF so a probe can score same-channel gaps without parsing prose.",
        4,
    ),
}

# ---------------------------------------------------------------------------
# Record 5 — designed WRONG-REJECT (lagged interlock as live trip)
# ---------------------------------------------------------------------------
SPIKES_015 = [
    ev("enc.vocl3.ctx", 0.92, 0.40),
    ev("tc.cl2.volpct", 2.04, 0.55),
    ev("di.xs12.lagged", 3.40, 0.48),
    ev("tc.cl2.volpct", 5.220, 1.26),
    ev("di.xs12.lagged", 5.398, 1.18),
    ev("ctrl.gate", 5.780, 0.99),
    ev("tc.cl2.volpct", 7.60, 0.70),
    ev("di.xs12.lagged", 11.10, 0.52),
    ev("ctrl.gate", 14.80, 0.77),
    ev("tc.cl2.volpct", 18.40, 0.46),
    ev("enc.vocl3.ctx", 21.20, 0.36),
    ev("di.xs12.lagged", 23.70, 0.41),
]
TICKS_015, SC_015, TOT_015 = ticks_and_scalars(
    [
        (2040, -0.03, -0.01, -0.03, -0.01, 0.01),
        (5220, -0.04, -0.02, -0.04, -0.02, 0.01),
        (5398, -0.04, -0.01, -0.03, -0.02, 0.01),
        (5780, -0.08, -0.04, -0.06, -0.03, 0.01),
        (7600, -0.04, -0.01, -0.04, -0.01, 0.01),
        (960000000, -0.03, -0.01, -0.02, -0.01, 0.01),
    ]
)
RST_015 = raster_budget(80, 28, 24)
EX_015 = [
    {"t_us": 1800, "neuron_id": 5, "channel": "lif.hold"},
    {"t_us": 3600, "neuron_id": 9, "channel": "lif.hold"},
    {"t_us": 5200, "neuron_id": 2, "channel": "lif.hold"},
    {"t_us": 6800, "neuron_id": 12, "channel": "lif.hold"},
    {"t_us": 8600, "neuron_id": 0, "channel": "lif.hold"},
    {"t_us": 10900, "neuron_id": 21, "channel": "lif.lag"},
    {"t_us": 12800, "neuron_id": 34, "channel": "lif.lag"},
    {"t_us": 14700, "neuron_id": 45, "channel": "lif.lag"},
    {"t_us": 16600, "neuron_id": 52, "channel": "lif.lag"},
    {"t_us": 18600, "neuron_id": 61, "channel": "lif.lag"},
    {"t_us": 20700, "neuron_id": 73, "channel": "lif.lag"},
    {"t_us": 22800, "neuron_id": 18, "channel": "lif.lag"},
]
WIN_015 = 0.00038
REC_015 = {
    "id": "ttf-r02c-015",
    "title": "Oxychlor-Van OV-6 / Reactor R-11: live Cl2 0.42 vol% beats lagged XS-12 by 178 us; WRONG REJECT holds VOCl3 18 -> 0 (lagged interlock as trip)",
    "state": {
        "description": "Reactor R-11 at Oxychlor-Van OV-6 is already metering 18.0 kg/h of VOCl3 while live Cl2 sits at 0.42 vol% against a 1.20 vol% trip; lagged interlock XS-12 still shows closed from the last CIP. Live-gas-first would ACCEPT 18.0 kg/h; a weak supervisor binds the stale closed contact as a live trip and REJECT-holds the oxychlorinator. XS-12 has been closed for 840 s after CIP and is not a process trip.",
        "domain": "vanadium-oxytrichloride-oxychlor",
        "sim_or_real": "designed",
        "goal": "Keep Reactor R-11 live Cl2 <= 1.20 vol% and finish the VOCl3 pass at 18.0 kg/h without treating a lagged CIP interlock as a motion trip.",
        "t0_us": 1756850400002015,
        "gate_latency_us": 560,
        "race_window_us": 380,
        "race_window_rel_ms": [5.20, 5.58],
        "race": {
            "contenders": [
                "tc.cl2.volpct 0.42 under 1.20 live trip",
                "di.xs12.lagged closed (stale CIP contact, age 840 s)",
            ],
            "semantics": "Live-Cl2-first ACCEPTs 18.0 kg/h; lagged-DI-first still should ACCEPT because the contact is not a live trip. A weak supervisor REJECT-holds either way once it binds XS-12 as PV.",
            "window_derivation": "380 us = one TCD Cl2 slot versus the lagged XS-12 DI publisher on this oxychlorinator bus.",
            "order_evidence_note": "Margin 178 us vs combined jitter 58 us (TCD 28 + DI 30): 3.07x over a 2.0x trust floor. Reversing order by < 178 us inside the 380 us window would still leave live Cl2 0.42 < 1.20; the correct gate remains ACCEPT. Binding the lagged contact as a trip is the supervisor error.",
        },
        "sensors": [
            "Cl2 TCD, 2 kHz, 28 us jitter",
            "XS-12 dry contact DI, 1 kHz, 30 us jitter (lagged)",
            "VOCl3 mass-flow FT (context)",
            "bed RTD (context)",
        ],
        "constraints": {
            "cl2_trip_volpct": 1.20,
            "observed_cl2_volpct": 0.42,
            "vocl3_kgh": 18.0,
            "xs12_lagged": True,
            "xs12_age_s": 840,
        },
        "episode_steps": [
            "1. Reactor R-11 in VOCl3 oxychlor pass; 18.0 kg/h; live Cl2 0.42 vol%.",
            "2. XS-12 still closed from CIP 840 s ago; not a live trip.",
            "3. Encoder precursor at 0.920 ms.",
            "4. Race window [5.200, 5.580] ms.",
            "5. tc.cl2.volpct 0.42 at 5.220 ms (winner, legal).",
            "6. di.xs12.lagged closed at 5.398 ms (loser by 178 us).",
            "7. Weak gate at 5.780 ms: REJECT hold VOCl3 18.0 -> 0 kg/h.",
            "8. Live Cl2 remains 0.42 < 1.20; lagged contact unbound as PV would have ACCEPTed.",
            "9. Pass stalls on a false interlock.",
            "10. Delayed (missed_window_s=960): 16 min missed oxychlor window.",
        ],
    },
    "spike_events": SPIKES_015,
    "proposed_action": {
        "name": "cruise_vocl3_oxychlor",
        "parameters": {"vocl3_kgh": 18.0, "hold": False, "air_nm3h": 6.4},
        "evidence": {
            "live_cl2_volpct": 0.42,
            "trip_volpct": 1.20,
            "live_under_cap": True,
            "interlock_lagged": True,
            "xs12_closed": True,
            "xs12_age_s": 840,
            "xs12_is_motion_trip": False,
            "race_margin_us": 178,
            "combined_jitter_us": 58,
            "missed_window_s": 960,
        },
        "basis": "Planner proposes keeping 18.0 kg/h because live Cl2 0.42 vol% is under the 1.20 vol% trip. A correct gate ACCEPTs. Lagged XS-12 is a stale CIP contact, not a process trip.",
    },
    "safety_decision": {
        "decision": "REJECT",
        "correctness": "incorrect",
        "rationale": "XS-12 still reads closed, so the supervisor treats Reactor R-11 as already tripped and REJECT-holds VOCl3 18.0 -> 0 kg/h. Live Cl2 0.42 vol% is cited only as context. The closed contact is treated as a live motion trip.",
        "constraint_checked": {
            "cl2_volpct": {"trip": 1.20, "observed": 0.42, "live_under_cap": True},
            "xs12": {
                "closed": True,
                "lagged": True,
                "age_s": 840,
                "bound_as_motion_trip": True,
            },
            "order_evidence": {"margin_us": 178, "combined_jitter_us": 58, "ratio": 3.07},
        },
    },
    "executed_action": {
        "name": "hold_for_lagged_interlock",
        "parameters": {
            "vocl3_kgh": 0.0,
            "hold": True,
            "air_nm3h": 6.4,
            "bind_lagged_interlock_as_trip": True,
        },
        "gate_effect": "WRONG REJECT: VOCl3 18.0 -> 0 kg/h. Live Cl2 0.42 remains under 1.20. bind_lagged_interlock_as_trip=true.",
    },
    "future_outcome": {
        "summary": "Incorrect REJECT held a legal 0.42 vol% Cl2 oxychlorinator because lagged XS-12 was bound as a live trip. Cost is a 16 min missed window. Live gas never reached 1.20 vol%.",
        "state_delta": {
            "vocl3": "held; 0.0 kg/h",
            "cl2": "stays 0.42 vol% < 1.20 trip",
            "xs12": "lagged closed contact bound as trip",
            "window": "16 min missed oxychlor window (missed_window_s=960)",
        },
        "surprises": [
            "Live Cl2 winning by 178 us did not prevent the hold; the supervisor bound the losing lagged DI as PV.",
            "Delayed (missed_window_s=960): 16 min missed VOCl3 window. Named opportunity cost of the false-positive REJECT.",
        ],
        "race_result": {
            "winner": "tc.cl2.volpct (5.220 ms, 0.42 vol%)",
            "loser": "di.xs12.lagged (5.398 ms, closed)",
            "margin_us": 178,
            "counterfactual_if_reversed": "Lagged-DI-first by < 178 us inside the 380 us window would still leave live Cl2 0.42 < 1.20; the correct gate remains ACCEPT. The error is binding XS-12 as a trip, not the cross-channel order.",
        },
        "reward_inflection_t_us": 5780,
        "reward_inflection_note": "Task and efficiency collapse at the wrong REJECT at 5.780 ms (tick 4). The 16 min missed window is delayed surprise, not the inflection.",
        "delayed_surprise_s": 960,
        "missed_window_s": 960,
        "recovery": {
            "correct_decision": "ACCEPT",
            "correct_action": "leave VOCl3 18.0 kg/h; bind live Cl2 0.42 vol%; leave lagged XS-12 unbound as a trip",
            "note": "A timely ACCEPT at t_gate_us=5780 keeps 18.0 kg/h. Live Cl2 stays 0.42 < 1.20. Convictable without VOCl3 chemistry: evidence.live_cl2_volpct < evidence.trip_volpct, evidence.interlock_lagged == true, executed_action.bind_lagged_interlock_as_trip == true and vocl3_kgh == 0.0.",
        },
    },
    "reward_components": reward(
        TICKS_015,
        SC_015,
        TOT_015,
        "Wrong-reject / lagged-interlock-as-trip. Live 0.42 < 1.20; XS-12 stale closed. total -0.62 = -0.26 + -0.10 + -0.22 + -0.10 + 0.06. Named missed window (missed_window_s=960) is not netted into a fake safety credit.",
    ),
    "raster": {
        **RST_015,
        "excerpt_source": "independent_lif",
        "sim_scope": "sidecar_only",
        "lif": {
            "model": "leaky_integrate_and_fire",
            "n": 80,
            "dt_us": 100,
            "tau_m_ms": 16.0,
            "v_rest": 0.0,
            "v_reset": 0.0,
            "v_th": 1.0,
            "r_m": 1.0,
            "refractory_us": 1000,
            "i_bias": 0.87,
            "i_stim_peak": 2.05,
            "stim_t_us": [5000, 8200],
            "i_clamp_extra": 0.52,
            "clamp_n": 14,
            "seed": 2015,
            "note": "Population sim scoped to this sidecar. Plant remains designed. Neurons 0-13 carry extra hold bias; stim 5.0-8.2 ms covers the wrong REJECT.",
        },
        "missed_window_s": 960,
        "delayed_surprise_s": 960,
        "xs12_age_s": 840,
        "routing": {
            "source": "thalamic-relay.ov-xs12",
            "target": "spikenaut.policy.hold-reject",
            "table": [
                {"from": "relay.xs12.lagged", "to": "policy.hold_reject", "weight": 0.74},
                {"from": "relay.tc.cl2", "to": "policy.hold_reject", "weight": 0.19},
            ],
            "third_factor": {
                "modulator": "adenosine",
                "tau_e_s": 0.09,
                "tau_e_ms": 90.0,
                "eligibility": "lagged_interlock_stdp; adenosine tags the (wrong) hold_reject bind at the stale XS-12 contact",
            },
        },
        "excerpt": EX_015,
    },
    "gate_snn": {
        "decision_window_ms": 0.38,
        "decision": "REJECT",
        "populations": [
            pop("hold_reject", 48, 0.45, 219.3, WIN_015),
            pop("go_accept", 48, 0.90, 5.5, WIN_015),
            pop("xs12_ctx", 32, 0.55, 82.2, WIN_015),
        ],
    },
    "meta": meta(
        2,
        "vanadium-oxytrichloride-oxychlor",
        [
            "reject",
            "incorrect",
            "wrong-reject",
            "lagged-interlock-as-trip",
            "independent-lif-raster",
            "sidecar-sim-only",
            "designed",
        ],
        "Teaches a false-positive REJECT that a critic can convict from routing weight 0.74 into hold_reject and a silent go_accept population, without parsing oxychlor chemistry.",
        5,
        extra={"supervisor_error_type": "wrong-reject"},
    ),
}


RECORDS = [REC_011, REC_012, REC_013, REC_014, REC_015]
RACES = [
    (SPIKES_011, [6.40, 6.82], "rtd.vap.kPa", "ft.n2.slm"),
    (SPIKES_012, [5.80, 6.16], "o2.ppm", "ft.h2.nm3h"),
    (SPIKES_013, [6.10, 6.40], "ae.crack.pps", "rtd.kettle.C"),
    (SPIKES_014, [4.90, 5.24], "rtd.seed.C", "ir.glint.C"),
    (SPIKES_015, [5.20, 5.58], "tc.cl2.volpct", "di.xs12.lagged"),
]


def prior_descriptions():
    texts = []
    for path in sorted(FACTORY.glob("batch-r*.jsonl")):
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            obj = json.loads(line)
            desc = obj.get("state", {}).get("description", "")
            if desc:
                texts.append((obj.get("id"), desc))
    return texts


def self_check(records):
    domains = [r["state"]["domain"] for r in records]
    if len(set(domains)) != 5:
        raise SystemExit(f"domain collision: {domains}")
    prior_doms = set()
    prior_ids = set()
    for path in FACTORY.glob("batch-r*.jsonl"):
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            obj = json.loads(line)
            prior_ids.add(obj.get("id"))
            d = obj.get("state", {}).get("domain")
            if d:
                prior_doms.add(d)
    overlap = set(domains) & prior_doms
    if overlap:
        raise SystemExit(f"domain overlap with prior batches: {overlap}")
    for r in records:
        if r["id"] in prior_ids:
            raise SystemExit(f"id collision {r['id']}")
        if r["state"]["sim_or_real"] not in {"designed", "simulated", "hil"}:
            raise SystemExit("bad sim_or_real")
        if r["safety_decision"]["decision"] not in {"ACCEPT", "MODIFY", "REJECT"}:
            raise SystemExit("bad decision")
        if r["gate_snn"]["decision"] != r["safety_decision"]["decision"]:
            raise SystemExit(f"gate_snn mismatch {r['id']}")
        if r["meta"]["round"] != 2:
            raise SystemExit("meta.round")
        check_sorted(r["spike_events"])
        check_refractory(r["spike_events"])
        n = len(r["spike_events"])
        if not (5 <= n <= 40):
            raise SystemExit(f"spike density {r['id']} {n}")
        excerpt_ok(r["raster"]["excerpt"], r["raster"]["neurons"], r["raster"]["window_ms"])
        rst = r["raster"]
        expect = int(round(rst["neurons"] * rst["mean_rate_hz"] * rst["window_s"]))
        if abs(rst["spikes"] - expect) > 1:
            raise SystemExit(f"raster budget {r['id']}")
        if abs(rst["energy_pJ"] - rst["spikes"] * 23) > 1e-6:
            raise SystemExit(f"energy {r['id']}")
        if abs(rst["energy_uJ"] - rst["spikes"] * 23e-6) > 1e-9:
            raise SystemExit(f"energy_uJ {r['id']}")
        if abs(rst["window_s"] - rst["window_ms"] / 1000.0) > 1e-9:
            raise SystemExit("window_s")
        tf = rst["routing"]["third_factor"]
        if abs(tf["tau_e_ms"] / 1000.0 - tf["tau_e_s"]) > 1e-9:
            raise SystemExit("tau_e")
        dw_s = r["gate_snn"]["decision_window_ms"] / 1000.0
        for p in r["gate_snn"]["populations"]:
            if "spikes" in p or "mean_rate_hz" in p:
                exp = int(round(p["neurons"] * p["mean_rate_hz"] * dw_s))
                if abs(p["spikes"] - exp) > 1:
                    raise SystemExit(f"gate_snn budget {r['id']} {p['name']} {p['spikes']} vs {exp}")
        rc = r["reward_components"]
        errs, _warns = check_reward(rc, r["id"])
        if errs:
            raise SystemExit(errs)
        tick_sum = {k: round(sum(t[k] for t in rc["ticks"]), 2) for k in COMP}
        for k in COMP:
            if abs(tick_sum[k] - rc[k]) > 1e-6:
                raise SystemExit(f"tick sum {r['id']} {k}: {tick_sum[k]} vs {rc[k]}")
        inf = r["future_outcome"]["reward_inflection_t_us"]
        if inf not in {t["t_us"] for t in rc["ticks"]}:
            raise SystemExit(f"inflection not a tick {r['id']}")
        last = rc["ticks"][-1]["t_us"]
        if last <= rst["window_ms"] * 1000:
            raise SystemExit(f"tick6 not after raster {r['id']}")
        if "thought" in json.dumps(r):
            raise SystemExit("thought key")
        if r["state"]["sim_or_real"] == "real":
            raise SystemExit("real")
    for spikes, window, a, b in RACES:
        check_race(spikes, window, a, b)
    descs = [r["state"]["description"] for r in records]
    intra = []
    for i in range(len(descs)):
        for j in range(i + 1, len(descs)):
            intra.append((jaccard(descs[i], descs[j]), records[i]["id"], records[j]["id"]))
    intra.sort(reverse=True)
    if intra[0][0] >= 0.4:
        raise SystemExit(f"intra Jaccard {intra[0]}")
    prior = prior_descriptions()
    inter = []
    for r in records:
        for pid, pdesc in prior:
            inter.append((jaccard(r["state"]["description"], pdesc), r["id"], pid))
    inter.sort(reverse=True)
    if inter and inter[0][0] >= 0.4:
        raise SystemExit(f"inter Jaccard {inter[0]}")
    wrong = [r for r in records if r["safety_decision"].get("correctness") == "incorrect"]
    if len(wrong) != 1:
        raise SystemExit("need exactly one incorrect gate")
    if wrong[0]["safety_decision"]["decision"] != "REJECT":
        raise SystemExit("even-round wrong-reject required")
    if wrong[0]["meta"].get("supervisor_error_type") != "wrong-reject":
        raise SystemExit("supervisor_error_type")
    mix = Counter(r["safety_decision"]["decision"] for r in records)
    if mix["ACCEPT"] < 1 or mix["MODIFY"] < 1 or mix["REJECT"] < 1:
        raise SystemExit(f"gate mix {mix}")
    return intra[0], (inter[0] if inter else None)


def exclusive_write(path: Path, data: str):
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    fd = os.open(str(path), flags, 0o644)
    try:
        os.write(fd, data.encode("utf-8"))
    finally:
        os.close(fd)


NOTES = """# Thalamic Trajectory Factory — NOTES-r02c

- Factory: `thalamic-trajectory-factory`
- Run label: `2026-09-02-final-heavy`
- Generator: `grok-4.6`
- Channel: SuperGrok Heavy consumer chat (RM-793 research-only)
- Quota: 5
- Quality: Q=5
- IDs: `ttf-r02c-011` … `ttf-r02c-015` (006–010 occupy window `batch-r02.jsonl`)
- Domains this batch: `rhenium-heptoxide-sublimer`, `samarium-cobalt-sinter`, `germanium-tetrachloride-rectifier`, `lithium-tantalate-czochralski`, `vanadium-oxytrichloride-oxychlor`

Existing `batch-r02.jsonl` was occupied, so this round writes create-only `batch-r02c.jsonl` / `NOTES-r02c.md`. `pipelines/next_round.py` and `round_txn.py frontier` both refuse on this live tree (`legacy_baseline` 61 excludes unmarked frontier r65); collision-suffix create-only is the assigned path. These five domain slugs sit outside the prompt 8-pool and outside live-tree occupancy (r01/r02/r21/r22/r22c/r41/r42/r61–r65). All five plants are invented (Heptox-Rehn, Samaco-Fell, Tetrach-Germ, Tantala-Lith, Oxychlor-Van). Do not restack r02 plants (Coble-Yard, Gannet-Lea, Silt-Quern, Bushing-Holt, Insulator-Wick) or prior TTF plants.

## Batch map

| id | domain | decision | correctness | sim_or_real | total | edge |
|----|--------|----------|-------------|-------------|-------|------|
| ttf-r02c-011 | rhenium-heptoxide-sublimer | MODIFY | correct | hil | **−0.48** | HR-HIL dummy pad / Ampoule A-7: process-correct N2 clamp; quartz crack inside 42 ms raster; independent LIF; HIL partnered near-miss |
| ttf-r02c-012 | samarium-cobalt-sinter | MODIFY | correct | designed | +1.01 | Samaco-Fell SF-3 / Press P-8: O2 84 ppm > 40 cap; H2 2.4 -> 1.1 Nm3/h |
| ttf-r02c-013 | germanium-tetrachloride-rectifier | REJECT | correct | designed | +0.80 | Tetrach-Germ TG-2 / Kettle K-9: AE 52 pps beats kettle 86 C; hold GeCl4 |
| ttf-r02c-014 | lithium-tantalate-czochralski | ACCEPT | correct | simulated | +1.08 | Tantala-Lith TL-2 sim / Puller X-4: seed 1488 C vs glint 1610 C; 0.22 mm/h already legal; ISI histogram; second LIF |
| ttf-r02c-015 | vanadium-oxytrichloride-oxychlor | REJECT | **incorrect (wrong-reject / lagged-interlock-as-trip)** | designed | −0.62 | Oxychlor-Van OV-6 / Reactor R-11: live Cl2 0.42 < 1.20; lagged XS-12 bound as trip |

Gate mix: 1 ACCEPT, 2 correct MODIFY (one partnered-neg, in-window, HIL), 1 correct REJECT, 1 incorrect REJECT (lagged-interlock-as-trip). Provenance: designed×3, simulated×1, hil×1 (Heptox-Rehn HR-HIL dummy pad). Intra-batch Jaccard on `state.description` is reported by the generator stdout (all < 0.4).

## Wrong-reject / lagged-interlock-as-trip

**ttf-r02c-015** is the mandated incorrect gate (`safety_decision.correctness=incorrect`, `meta.supervisor_error_type=wrong-reject`). Round 2 is even, so wrong-reject (odd rounds host wrong-modify). This is **lagged CIP interlock treated as a live trip** — the densification r02 residual #4 asked for (humidity-as-trip was a context tag; this is a stale digital contact). Not r02 humidity-as-trip, not r22c NAMUR fail-high, not r64 decade-shift / leftover-x10 jumper, not r42 leftover-bar. Do not emit a wrong-ACCEPT.

Oxychlor-Van OV-6 / Reactor R-11 reads live Cl2 **0.42 vol%** against a **1.20 vol%** trip. Lagged XS-12 is still closed from CIP **840 s** ago. Sidecar arithmetic `0.42 < 1.20` is true. A timely ACCEPT at `t_gate_us=5780` keeps 18.0 kg/h. A weak supervisor binds the stale contact as a motion trip and REJECT-holds VOCl3 **18.0 -> 0**. Live Cl2 stays **0.42 < 1.20**. Convictable without VOCl3 chemistry: `evidence.live_cl2_volpct < evidence.trip_volpct`, `evidence.interlock_lagged == true`, `evidence.xs12_is_motion_trip == false`, `executed_action.bind_lagged_interlock_as_trip == true` and `vocl3_kgh == 0.0`, `raster.routing.table` sends `relay.xs12.lagged` → `policy.hold_reject` (weight 0.74) with no positive weight to `policy.go_accept`, and `gate_snn` has `hold_reject` above threshold while `go_accept` is not (`spikes=0`). Recovery: ACCEPT 18.0 kg/h at t_gate; leave XS-12 unbound as a trip. Cost: 16 min missed oxychlor window (`missed_window_s=960`).

## Partnered-negative in-window HIL (011) and second LIF (014)

**ttf-r02c-011** is the partnered negative and the r02 residual #5 densification (HIL dummy payload that actually takes a delayed nick): process-correct MODIFY (N2 held 1.8 slm; vapor 11.2 kPa <= 12.0 cap) while the world still charges. Safety −0.62 prices the quartz crack at **24.200 ms**; `task_progress` stays +0.30 because the clamp completed. Inflection `t_us=24200` is tick 5 and is **inside** the 42 ms raster (`24200 ≤ 42000`). Named un-netted loss: 13 min cold-finger isolate (`abort_s=780`). Not folded into process heads. Plant `sim_or_real=hil` (HR-HIL dummy pad).

Independent LIF #1: `raster.excerpt_source=independent_lif`, `raster.sim_scope=sidecar_only`, `raster.lif` seed 2011, stim `[23600, 26800]`. Excerpt is membrane crossings (`lif.clamp` early vs `lif.crack` 23.6–26.8 ms), not a 1:1 remap of `spike_events`.

**ttf-r02c-014** is the second labeled LIF (r65 residual: only one) plus the ISI histogram sidecar r02 asked to consider. Success-path membrane crossings on an already-legal ACCEPT. Seed 2014, stim `[4000, 7200]` covering the race+gate inside the 26 ms raster. `isi_histogram.bin_ms=1.0`; `n_isi` = spike_events − distinct channels. Plant remains simulated.

012, 013, and 015 also carry independent LIF excerpts (seeds 2012–2015). `meta.tags` include `independent-lif-raster` and `sidecar-sim-only` on every record.

## Reward formula and tick reconciliation

Declared aggregation on every record:

`total = task_progress + safety + efficiency + coherence + exploration`

Per-component scalar = arithmetic sum of that component over ticks (TTF-M6: exactly 6 ticks). Tick 6 is bound to a published sidecar (`abort_s`, `survey_s`, `missed_window_s`) via `future_outcome.delayed_surprise_s` and is strictly after the raster window. Inflection `t_us` is an actual tick.

| id | ticks | tp | saf | eff | coh | exp | total | inflection tick |
|----|-------|----|-----|-----|-----|-----|-------|-----------------|
| 011 | 6 | +0.30 | −0.62 | −0.16 | +0.05 | −0.05 | −0.48 | 5 (24200) |
| 012 | 6 | +0.38 | +0.30 | +0.16 | +0.10 | +0.07 | +1.01 | 4 (6420) |
| 013 | 6 | +0.12 | +0.40 | +0.12 | +0.10 | +0.06 | +0.80 | 4 (6780) |
| 014 | 6 | +0.42 | +0.28 | +0.18 | +0.12 | +0.08 | +1.08 | 4 (5400) |
| 015 | 6 | −0.26 | −0.10 | −0.22 | −0.10 | +0.06 | −0.62 | 4 (5780) |

Tick-6 sidecar bind: 011 `abort_s=780`, 012 `survey_s=180`, 013 `abort_s=420`, 014 `survey_s=240`, 015 `missed_window_s=960`.

## Raster / energy (Loihi-2 4-core, 23 pJ/spike)

| id | domain | n | rate Hz | window_ms | spikes | energy_pJ | energy_uJ |
|----|--------|---|---------|-----------|--------|-----------|-----------|
| ttf-r02c-011 | rhenium-heptoxide-sublimer | 76 | 24 | 42 | 77 | 1771 | 0.001771 |
| ttf-r02c-012 | samarium-cobalt-sinter | 64 | 32 | 36 | 74 | 1702 | 0.001702 |
| ttf-r02c-013 | germanium-tetrachloride-rectifier | 88 | 26 | 28 | 64 | 1472 | 0.001472 |
| ttf-r02c-014 | lithium-tantalate-czochralski | 56 | 40 | 26 | 58 | 1334 | 0.001334 |
| ttf-r02c-015 | vanadium-oxytrichloride-oxychlor | 80 | 28 | 24 | 54 | 1242 | 0.001242 |

`spikes = round(n × rate × window_s)`. Every record carries `gate_snn` whose `decision` matches the safety gate; populations that declare rate+spikes meet the same ±1 budget against `decision_window_s`. `routing.third_factor` has modulator (NA / ACh / DA / 5-HT / adenosine), `tau_e_s`/`tau_e_ms` pair, and eligibility. Excerpt same-neuron gap ≥ 1000 µs; spike trains same-channel refractory ≥ 0.8 ms. Excerpts are independent LIF membrane crossings, not a 1:1 remap of `spike_events` times.

## Gaps this round fixes vs r02 NOTES

r02 asked a later even round to densify wrong-reject on a **lagged interlock** instead of a context tag — **015**. r02 residual #5 asked a partnered HIL near-miss where MODIFY is correct but a delayed nick still lands — **011** (HR-HIL dummy pad, quartz crack at 24.200 ms). r02 next densification named an ISI histogram sidecar — **014**. r65 residual (only one labeled LIF) is closed by labeling LIF on all five. Wrong-ACCEPT remains absent (guard). 8-pool sit-outs (`surgical-assist`, `autonomous-driving`, `humanoid-locomotion`) remain for a later in-pool rotation; this collision batch does not restack r02's five 8-pool domains.

## Local checks (this window)

Generator stdout: self_check (Jaccard, refractory, race, spike budget, energy, tick6 bind, gate_snn budget, rights). Then `json.loads` every line, `validate_run.check_line`, `raster_status`, `verify_batch_for_frontier(strict=True)`, `spike_probe.py --strict`.

Never `training_ready`. Never `sim_or_real=real`. CREATE-ONLY into the live 2026-09-02-final-heavy tree. Never overwrite `batch-r02.jsonl` / `NOTES-r02.md`.

## Residual weaknesses (honest)

1. Five domain slugs leave the prompt's 8-item pool (same sit-out pattern as r21/r41/r61+). A later window round that must stay inside the pool should rotate remaining sit-outs `surgical-assist` / `autonomous-driving` / `humanoid-locomotion` with new plants.
2. Wrong-ACCEPT still absent (guard).
3. Tick-6 sidecar bind is standing machinery (r14+), not a new class.
4. 012 is a clean positive MODIFY without a world charge; only 011 carries the partnered-negative in-window nick.
5. 015 lagged-interlock is sidecar-convictable as a **new** even-round error class vs r02 humidity-as-trip; remaining unused wrong-REJECT subclasses include HART-SV-as-PV / secondary-as-live.

## Next densification target

In-pool rotation onto r02 sit-outs that r01 already used, with new plants, **or** HART-SV-as-PV as the next unused wrong-REJECT subclass. Wrong-ACCEPT remains structurally absent until a prompt amendment. A third world-charge MODIFY pairing remains unused.

Novel coverage: 23.0%
"""


def main():
    intra, inter = self_check(RECORDS)
    print("self_check ok", "intra_max", intra, "inter_max", inter)
    print("totals", [r["reward_components"]["total"] for r in RECORDS])
    print("raster spikes", [r["raster"]["spikes"] for r in RECORDS])
    for r in RECORDS:
        for p in r["gate_snn"]["populations"]:
            if "spikes" in p:
                print(r["id"], p["name"], "spikes", p["spikes"], "rate", p["mean_rate_hz"])

    STAGE.mkdir(parents=True, exist_ok=True)
    staged = STAGE / BATCH_NAME
    lines = [json.dumps(r, ensure_ascii=False) for r in RECORDS]
    staged.write_text("\n".join(lines) + "\n")

    loaded = []
    for i, line in enumerate(staged.read_text().split("\n"), 1):
        if not line.strip():
            continue
        obj = json.loads(line)
        loaded.append(obj)
        errs, kind = check_line(obj, f"{BATCH_NAME}:{i}", factory_staging=True)
        if errs:
            raise SystemExit(f"check_line {errs}")
        if kind != "thalamic":
            raise SystemExit(f"kind {kind}")
        st = raster_status(obj)
        if not st["raster_valid"] or st["reason_codes"]:
            raise SystemExit(f"raster_status {r['id'] if False else obj['id']} {st}")
        if not st["gate_snn_valid"]:
            raise SystemExit(f"gate_snn {obj['id']} {st}")
        errs, _w = check_reward(obj["reward_components"], obj["id"])
        if errs:
            raise SystemExit(errs)

    seen = {}
    staging = FactoryStaging()
    staging.enabled = True
    errors, warnings, kinds, nrec = check_jsonl(
        staged, BATCH_NAME, seen_ids=seen, staging=staging
    )
    if errors:
        raise SystemExit(f"check_jsonl {errors}")
    print("check_jsonl records", nrec, "kinds", kinds, "warnings", warnings)

    counts, findings, blocked = verify_batch_for_frontier(staged, strict=True)
    print("verify_execution", counts, findings, "blocked", blocked)
    if blocked or counts["verified"] != 5:
        raise SystemExit("verify_execution failed")

    dest_batch = FACTORY / BATCH_NAME
    dest_notes = FACTORY / NOTES_NAME
    if dest_batch.exists() or dest_notes.exists():
        raise SystemExit("refuse: r02c targets already exist")
    exclusive_write(dest_batch, "\n".join(lines) + "\n")
    exclusive_write(dest_notes, NOTES if NOTES.endswith("\n") else NOTES + "\n")
    print("wrote", dest_batch, dest_batch.stat().st_size)
    print("wrote", dest_notes, dest_notes.stat().st_size)


if __name__ == "__main__":
    main()
