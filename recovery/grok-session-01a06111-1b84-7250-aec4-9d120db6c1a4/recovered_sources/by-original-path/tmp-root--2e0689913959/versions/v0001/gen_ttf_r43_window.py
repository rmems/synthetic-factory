#!/usr/bin/env python3
"""Generate TTF round 43 (create-only) for 2026-09-02-final-heavy."""
from __future__ import annotations

import json
import math
import os
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path("/home/raulmc/rmems/synthetic-factory")
sys.path.insert(0, str(ROOT / "pipelines"))

from check_records import FactoryStaging, check_jsonl, check_record  # noqa: E402
from curate_bridge import raster_status  # noqa: E402
from exact_json import dumps_exact_json  # noqa: E402
from validate_run import check_line  # noqa: E402
from verify_execution import verify_batch_for_frontier  # noqa: E402

FACTORY = ROOT / "outputs/raw/2026-09-02-final-heavy/thalamic-trajectory-factory"
COMPS = ("task_progress", "safety", "efficiency", "coherence", "exploration")
ROUND = 43


def rights():
    return {
        "provider": "SpaceXAI/xAI",
        "model": "grok-4.6",
        "channel": "consumer",
        "subscription_plan": "SuperGrok Heavy",
        "generation_surface": "SuperGrok Heavy chat",
        "generated_at": "2026-09-03T00:48:00Z",
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


def spikes(rows):
    events = [{"channel": c, "t_rel_ms": t, "amplitude": a} for c, t, a in rows]
    times = [e["t_rel_ms"] for e in events]
    assert times == sorted(times), times
    last = {}
    for e in events:
        prev = last.get(e["channel"])
        if prev is not None:
            gap = e["t_rel_ms"] - prev
            assert gap >= 0.8 - 1e-12, (e["channel"], prev, e["t_rel_ms"], gap)
        last[e["channel"]] = e["t_rel_ms"]
    assert 5 <= len(events) <= 40
    return events


def excerpt(rows, window_ms, neurons):
    out = []
    last_n = {}
    for t_us, nid, ch in rows:
        assert 0 <= t_us <= int(window_ms * 1000)
        assert 0 <= nid < neurons
        if nid in last_n:
            assert t_us - last_n[nid] >= 1000, (nid, last_n[nid], t_us)
        last_n[nid] = t_us
        out.append({"t_us": int(t_us), "neuron_id": int(nid), "channel": ch})
    assert out
    return out


def raster_budget(neurons, rate, window_ms):
    window_s = window_ms / 1000.0
    n_spikes = int(round(neurons * rate * window_s))
    return {
        "window_ms": window_ms,
        "window_s": window_s,
        "neurons": neurons,
        "mean_rate_hz": rate,
        "spikes": n_spikes,
        "energy_pJ": n_spikes * 23,
        "energy_uJ": n_spikes * 23e-6,
    }


def tick_reward(ticks, notes):
    scalars = {k: sum(t[k] for t in ticks) for k in COMPS}
    total = sum(scalars.values())
    return {
        "_aggregation": "total = task_progress + safety + efficiency + coherence + exploration",
        "ticks": ticks,
        **scalars,
        "total": total,
        "notes": notes,
    }


def isi_histogram(events, bin_ms=0.8):
    by = defaultdict(list)
    for e in events:
        by[e["channel"]].append(e["t_rel_ms"])
    isis = []
    for ch, ts in by.items():
        ts = sorted(ts)
        for a, b in zip(ts, ts[1:]):
            gap = b - a
            assert gap >= 0.8 - 1e-12, (ch, gap)
            isis.append(gap)
    max_bin = int(max(isis) // bin_ms) if isis else 0
    counts = [0] * (max_bin + 1)
    for g in isis:
        counts[int(g // bin_ms)] += 1
    return {
        "bin_ms": bin_ms,
        "unit": "ms",
        "n_isi": len(isis),
        "min_isi_ms": min(isis) if isis else None,
        "counts": counts,
        "note": "same-channel ISIs from spike_events; refractory floor 0.8 ms",
    }


def pop(name, neurons, threshold, rate=None, spikes=None):
    d = {"name": name, "neurons": neurons, "threshold": threshold}
    if rate is not None:
        d["mean_rate_hz"] = rate
        d["spikes"] = spikes
    return d


def gate_snn(decision, window_ms, populations):
    window_s = window_ms / 1000.0
    for p in populations:
        if "mean_rate_hz" in p:
            expected = int(round(p["neurons"] * p["mean_rate_hz"] * window_s))
            assert abs(expected - p["spikes"]) <= 1, (p, expected)
    return {
        "decision_window_ms": window_ms,
        "decision": decision,
        "populations": populations,
    }


def third(modulator, tau_e_s, eligibility):
    return {
        "modulator": modulator,
        "tau_e_s": tau_e_s,
        "tau_e_ms": tau_e_s * 1000.0,
        "eligibility": eligibility,
    }


def meta_base(domain, tags, distillation, position, supervisor=None):
    m = {
        "round": ROUND,
        "factory": "thalamic-trajectory-factory",
        "generator": "grok-4.6",
        "run_label": "2026-09-02-final-heavy",
        "domain": domain,
        "tags": tags,
        "snn_tags": ["race", "refractory", "adaptation"],
        "distillation_value": distillation,
        "rights": rights(),
        "batch_position": position,
    }
    if supervisor:
        m["supervisor_error_type"] = supervisor
    return m


def build_record(spec):
    rb = raster_budget(spec["neurons"], spec["rate"], spec["window_ms"])
    events = spikes(spec["spike_rows"])
    ex = excerpt(spec["excerpt_rows"], spec["window_ms"], spec["neurons"])
    raster = {
        **rb,
        "excerpt_source": spec["excerpt_source"],
        "sim_scope": spec.get("sim_scope", "sidecar_only"),
        spec["delay_key"]: spec["delay_s"],
        "delayed_surprise_s": spec["delay_s"],
        "routing": {
            "source": spec["route_source"],
            "target": spec["route_target"],
            "table": spec["table"],
            "third_factor": spec["third"],
        },
        "excerpt": ex,
    }
    if spec.get("lif"):
        raster["lif"] = spec["lif"]
    if spec.get("isi"):
        raster["isi_histogram"] = isi_histogram(events)
    rec = {
        "id": spec["id"],
        "title": spec["title"],
        "state": {
            "description": spec["description"],
            "domain": spec["domain"],
            "sim_or_real": spec["sim"],
            "goal": spec["goal"],
            "t0_us": spec["t0_us"],
            "gate_latency_us": spec["gate_latency_us"],
            "race_window_us": spec["race_window_us"],
            "race_window_rel_ms": spec["race_window_rel_ms"],
            "race": spec["race"],
            "sensors": spec["sensors"],
            "constraints": spec["constraints"],
            "episode_steps": spec["episode_steps"],
        },
        "spike_events": events,
        "proposed_action": spec["proposed"],
        "safety_decision": spec["safety"],
        "executed_action": spec["executed"],
        "future_outcome": spec["future"],
        "reward_components": tick_reward(spec["ticks"], spec["reward_notes"]),
        "raster": raster,
        "gate_snn": spec["gate_snn"],
        "meta": spec["meta"],
    }
    return rec


SPECS = []

# --- 1 partnered-negative correct MODIFY, designed, independent LIF ---
SPECS.append(
    dict(
        id="ttf-r43-431",
        title=(
            "Thallate-Croft TC-4 / Cell C-9: cell voltage beats current encoder by 170 us; "
            "correct MODIFY still eats an in-window ceramic weir crack (partnered negative total -0.48)"
        ),
        domain="thallium-sulfate-electrolyzer",
        sim="designed",
        description=(
            "Thallium-sulfate cell C-9 at Thallate-Croft TC-4 is holding 4.82 V while current still sits a legal 18.6 kA under 22.0. "
            "Voltage-first clamps 18.6 -> 12.4 kA; current-encoder-first would keep cruise because bath 318 C is still under the 340 C pot-wall cap. "
            "A ceramic weir crack already seated on the cell does not appear on voltage or current until the AE dump."
        ),
        goal="Keep C-9 cell voltage <= 4.40 V and finish the Tl2SO4 campaign without dumping electrolyte through a cracked ceramic weir.",
        t0_us=1756856800000431,
        gate_latency_us=740,
        race_window_us=340,
        race_window_rel_ms=[5.18, 5.52],
        race={
            "contenders": [
                "cell.V 4.82 over 4.40 cap",
                "enc.kA 18.6 with bath 318 under 340",
            ],
            "semantics": "Voltage-first latches current clamp 18.6 -> 12.4 kA; encoder-first keeps 18.6 kA on a 'still under pot-wall cap' model.",
            "window_derivation": "340 us = one cell-voltage slot versus the current-encoder publisher on this sulfate bus.",
            "order_evidence_note": "Margin 170 us vs combined jitter 58 us (V 26 + kA 32): 2.93x over a 2.0x trust floor. Reversing order by < 170 us inside the 340 us window would have kept 18.6 kA; predicted next-sample 4.61 V > 4.40 cap.",
        },
        sensors=[
            "cell voltage divider, 2 kHz, 26 us jitter",
            "current encoder + bath TC, 1 kHz, 32 us jitter",
            "weir AE puck (context)",
            "catholyte flowmeter (context)",
        ],
        constraints={
            "v_cap_V": 4.4,
            "observed_V": 4.82,
            "current_kA": 18.6,
            "bath_C": 318.0,
            "bath_cap_C": 340.0,
        },
        episode_steps=[
            "1. C-9 indexed on Thallate-Croft TC-4; current 18.6 kA; cell 4.82 V.",
            "2. Bath TC 318 C under 340 C pot-wall cap; planner treats voltage as a wet divider.",
            "3. Current-encoder precursor at 1.240 ms.",
            "4. Race window [5.180, 5.520] ms.",
            "5. cell.V 4.82 at 5.180 ms (winner).",
            "6. enc.kA 18.6 at 5.350 ms (loser by 170 us).",
            "7. Gate at 5.920 ms: correct MODIFY clamps 18.6 -> 12.4 kA.",
            "8. Observed after clamp 4.18 V <= 4.40. Ceramic weir still cracks at 22.200 ms.",
            "9. Electrolyte dump 0.4 m3; clamp reduced dump energy; it did not prevent the crack.",
            "10. Delayed (abort_s=780): 13 min weir isolate. Named un-netted loss.",
        ],
        spike_rows=[
            ("enc.kA", 1.24, 0.42),
            ("cell.V", 2.08, 0.58),
            ("enc.kA", 3.44, 0.50),
            ("cell.V", 5.18, 1.28),
            ("enc.kA", 5.35, 1.10),
            ("ctrl.gate", 5.92, 0.96),
            ("cell.V", 8.10, 0.72),
            ("enc.kA", 10.40, 0.55),
            ("ctrl.gate", 12.80, 0.80),
            ("cell.V", 16.20, 0.44),
            ("ae.weir.crack", 22.20, 1.42),
            ("enc.kA", 26.40, 0.40),
            ("cell.V", 31.80, 0.52),
        ],
        excerpt_source="independent_lif",
        sim_scope="sidecar_only",
        excerpt_rows=[
            (5400, 3, "lif.clamp"),
            (8900, 1, "lif.clamp"),
            (11900, 6, "lif.clamp"),
            (13600, 4, "lif.clamp"),
            (15800, 8, "lif.clamp"),
            (18100, 2, "lif.clamp"),
            (22100, 20, "lif.weir"),
            (23200, 24, "lif.weir"),
            (24100, 28, "lif.weir"),
            (24900, 22, "lif.weir"),
            (26800, 31, "lif.weir"),
            (29100, 18, "lif.clamp"),
            (31400, 9, "lif.clamp"),
            (33800, 12, "lif.clamp"),
            (36200, 5, "lif.clamp"),
            (39100, 7, "lif.clamp"),
        ],
        neurons=76,
        rate=24,
        window_ms=42,
        delay_key="abort_s",
        delay_s=780,
        route_source="thalamic-relay.tl-so4",
        route_target="spikenaut.policy.current-clamp",
        table=[
            {"from": "relay.cell.v", "to": "policy.current_clamp", "weight": 0.68},
            {"from": "relay.enc.ka", "to": "policy.current_hold", "weight": 0.29},
            {"from": "relay.ae.weir", "to": "policy.current_clamp", "weight": -0.42},
        ],
        third=third(
            "noradrenaline",
            0.04,
            "surprise-gated pre_post_stdp; NA at voltage win (5.180 ms) opens a 42 ms eligibility trace that still covers the 22.200 ms ceramic weir crack",
        ),
        lif={
            "model": "leaky_integrate_and_fire",
            "n": 76,
            "dt_us": 100,
            "tau_m_ms": 19.0,
            "v_rest": 0.0,
            "v_reset": 0.0,
            "v_th": 1.0,
            "r_m": 1.0,
            "refractory_us": 1000,
            "i_bias": 0.91,
            "i_stim_peak": 2.42,
            "stim_t_us": [22000, 25000],
            "i_clamp_extra": 0.62,
            "clamp_n": 14,
            "seed": 43431,
            "note": "Population sim scoped to this sidecar. Plant remains designed. Neurons 0-13 carry +0.62 current-clamp bias; stim 22-25 ms is the ceramic weir crack.",
        },
        proposed={
            "name": "cruise_cell_current",
            "parameters": {"current_kA": 18.6, "cell_V": 4.82, "bath_C": 318.0},
            "evidence": {
                "cell_V": 4.82,
                "v_cap_V": 4.40,
                "predicted_unclamped_next_V": 4.61,
                "current_kA": 18.6,
                "bath_C": 318.0,
                "bath_cap_C": 340.0,
                "race_margin_us": 170,
                "combined_jitter_us": 58,
                "abort_s": 780,
            },
            "basis": "Planner proposes 18.6 kA because bath 318 C is under 340, treating the 4.82 V cell as a still-wet divider rather than a voltage-cap miss.",
        },
        safety={
            "decision": "MODIFY",
            "correctness": "correct",
            "rationale": "Cell voltage 4.82 V won by 170 us, so the bar is off-spec, not still a pot-wall story. Holding 18.6 kA predicts next-sample 4.61 V > 4.40 cap. MODIFY: current 18.6 -> 12.4 kA. Observed after clamp 4.18 V <= 4.40. A full REJECT is not indicated: a clean cell accepts 12.4 kA.",
            "constraint_checked": {
                "cell_V": {
                    "cap": 4.40,
                    "observed": 4.82,
                    "predicted_unclamped_next": 4.61,
                    "clamped_current_kA": 12.4,
                    "observed_after_clamp": 4.18,
                },
                "order_evidence": {"margin_us": 170, "combined_jitter_us": 58, "ratio": 2.93},
            },
        },
        executed={
            "name": "clamped_cell_current",
            "parameters": {"current_kA": 12.4, "cell_V": 4.18, "bath_C": 318.0},
            "gate_effect": "MODIFY: current 18.6 -> 12.4 kA. Process-correct vs the 4.40 V cap. Ceramic weir still cracks at 22.200 ms.",
        },
        future={
            "summary": "Process-correct MODIFY held cell voltage at 4.18 V. At 22.200 ms a ceramic weir crack already seated on C-9 dumped 0.4 m3 electrolyte. Clamp reduced dump energy; it did not prevent the crack. Partnered negative: process heads stay honest; world loss is named, not netted.",
            "state_delta": {
                "voltage": "clamp executed; peak 4.18 V <= 4.40 cap",
                "weir": "cracked at 22.200 ms; 0.4 m3 electrolyte",
                "repair": "13 min weir isolate (abort_s=780)",
                "mission": "TC-4 Tl2SO4 circuit incomplete this shift",
            },
            "surprises": [
                "Neither cell voltage nor current encoder predicted the seated ceramic weir crack; ae.weir.crack is a new channel at 22.200 ms, 16.280 ms after the gate, still inside the 42 ms raster.",
                "Delayed (abort_s=780): 13 min weir isolate. Named un-netted loss, not folded into task_progress.",
            ],
            "un_netted_loss": "13 min weir isolate after the ceramic crack. Safety head -0.64 prices the dump; task_progress stays +0.30 because the current clamp completed under the 4.40 V cap. World loss is named here, not subtracted from process heads.",
            "race_result": {
                "winner": "cell.V (5.180 ms, 4.82 V)",
                "loser": "enc.kA (5.350 ms, 18.6 kA)",
                "margin_us": 170,
                "counterfactual_if_reversed": "Encoder-first by < 170 us inside the 340 us window would have kept 18.6 kA; predicted next-sample 4.61 V would have missed the 4.40 cap even without the crack. The MODIFY is still the correct process. The crack is a later world charge either way, cheaper with the clamp than without.",
            },
            "reward_inflection_t_us": 22200,
            "reward_inflection_note": "Safety collapses at the 22.200 ms ceramic weir crack (tick t_us=22200), inside the 42 ms raster. The correct MODIFY at 5.920 ms is in the same excerpt. Do not put inflection on the abort_s=780 isolation tick.",
            "delayed_surprise_s": 780,
        },
        ticks=[
            {"t_us": 2080, "task_progress": 0.04, "safety": -0.02, "efficiency": -0.02, "coherence": 0.01, "exploration": 0.00},
            {"t_us": 5180, "task_progress": 0.08, "safety": -0.04, "efficiency": -0.02, "coherence": 0.01, "exploration": -0.01},
            {"t_us": 5350, "task_progress": 0.04, "safety": -0.03, "efficiency": -0.02, "coherence": 0.00, "exploration": 0.00},
            {"t_us": 5920, "task_progress": 0.08, "safety": -0.05, "efficiency": -0.03, "coherence": 0.02, "exploration": -0.01},
            {"t_us": 22200, "task_progress": 0.04, "safety": -0.45, "efficiency": -0.03, "coherence": -0.01, "exploration": -0.01},
            {"t_us": 780000000, "task_progress": 0.02, "safety": -0.05, "efficiency": -0.02, "coherence": 0.01, "exploration": -0.01},
        ],
        reward_notes="Partnered negative. Process-correct MODIFY; world still charges inside the 42 ms raster. Named weir isolate (abort_s=780) is not netted into task_progress.",
        gate_snn=gate_snn(
            "MODIFY",
            0.34,
            [
                pop("current_clamp", 50, 0.5, 240.0, 4),
                pop("current_hold", 40, 0.8, 60.0, 1),
                pop("weir_veto", 24, 0.75),
            ],
        ),
        meta=meta_base(
            "thallium-sulfate-electrolyzer",
            ["modify", "partnered-negative-total", "independent-lif-raster", "sidecar-sim-only", "in-window-world-charge", "designed"],
            "A critic can see the world-charge as a LIF burst inside the raster while process heads stay honest. Credit assignment is spikes, not prose across a 13 min weir isolate.",
            1,
        ),
    )
)

# --- 2 wrong-MODIFY cascade-secondary-as-primary ---
SPECS.append(
    dict(
        id="ttf-r43-432",
        title=(
            "WRONG-MODIFY at Hexachlor-Wath HW-6 / Retort R-4: live bed 428 C read correctly; "
            "H2 stays 14.0 Nm3/h because cascade secondary 186 C was bound as primary"
        ),
        domain="tungsten-hexachloride-reducer",
        sim="designed",
        description=(
            "Tungsten-hexachloride retort R-4 at Hexachlor-Wath HW-6 reads live bed 428 C over a 400 C freeze cap while the cascade secondary quench TC still sits 186 C under 220. "
            "Bed-first should cut H2 14.0 -> 7.2 Nm3/h; a leftover cascade-secondary-as-primary bind opens quench 18 -> 55 percent instead. Hydrogen stays 14.0."
        ),
        goal="Keep R-4 bed <= 400 C and finish the WCl6 reduction without freezing the packed bed on leftover cascade-secondary quench.",
        t0_us=1756856801000432,
        gate_latency_us=620,
        race_window_us=300,
        race_window_rel_ms=[5.42, 5.72],
        race={
            "contenders": [
                "tt.bed.C 428 over 400 cap",
                "tt.cascade.C 186 under 220 secondary cap",
            ],
            "semantics": "Bed-first latches H2 cut 14.0 -> 7.2 Nm3/h; cascade-first opens quench and leaves H2 at 14.0.",
            "window_derivation": "300 us = one bed-TC slot versus the cascade-secondary publisher on this WCl6 bus.",
            "order_evidence_note": "Margin 160 us vs combined jitter 54 us (bed 24 + cascade 30): 2.96x over a 2.0x trust floor. Reversing order by < 160 us inside the 300 us window would have bound the 186 C secondary as live.",
        },
        sensors=[
            "bed TC TT-14A, 2 kHz, 24 us jitter",
            "cascade secondary quench TC TT-14B, 1 kHz, 30 us jitter",
            "H2 mass-flow (context)",
            "quench-valve stem (context)",
        ],
        constraints={
            "bed_cap_C": 400.0,
            "observed_bed_C": 428.0,
            "cascade_C": 186.0,
            "cascade_cap_C": 220.0,
            "h2_Nm3_h": 14.0,
            "cascade_is_primary": False,
        },
        episode_steps=[
            "1. R-4 LIVE already reducing; bed 428 C; H2 14.0 Nm3/h; quench 18 percent.",
            "2. Cascade secondary TT-14B 186 C under 220; leftover selector still prefers the secondary.",
            "3. Cascade precursor at 1.120 ms.",
            "4. Race window [5.420, 5.720] ms.",
            "5. tt.bed.C 428 at 5.420 ms (winner).",
            "6. tt.cascade.C 186 at 5.580 ms (loser by 160 us).",
            "7. Gate at 6.040 ms: WRONG-MODIFY binds cascade secondary as primary.",
            "8. Quench 18 -> 55 percent; H2 left 14.0; live bed stays 422 C > 400.",
            "9. Packed bed freeze starts on R-4; 186 C was never the live cap.",
            "10. Delayed (abort_s=660): 11 min retort dump while R-4 is quenched.",
        ],
        spike_rows=[
            ("tt.cascade.C", 1.12, 0.40),
            ("tt.bed.C", 2.20, 0.56),
            ("tt.cascade.C", 3.50, 0.48),
            ("tt.bed.C", 5.42, 1.32),
            ("tt.cascade.C", 5.58, 1.08),
            ("ctrl.gate", 6.04, 0.94),
            ("tt.bed.C", 8.40, 0.70),
            ("tt.cascade.C", 10.60, 0.58),
            ("ctrl.gate", 13.20, 0.82),
            ("tt.bed.C", 17.10, 0.44),
            ("tt.cascade.C", 21.40, 0.50),
            ("tt.bed.C", 25.80, 0.38),
        ],
        excerpt_source="kernelized_events",
        excerpt_rows=[
            (2100, 4, "k.cascade"),
            (4500, 11, "k.bed"),
            (7300, 19, "k.gate"),
            (9100, 27, "k.bed"),
            (11400, 8, "k.cascade"),
            (13800, 33, "k.gate"),
            (15600, 41, "k.bed"),
            (17900, 2, "k.cascade"),
            (19800, 55, "k.bed"),
            (22100, 16, "k.cascade"),
            (24300, 62, "k.gate"),
            (26100, 7, "k.bed"),
            (27800, 70, "k.cascade"),
        ],
        neurons=96,
        rate=32,
        window_ms=28,
        delay_key="abort_s",
        delay_s=660,
        route_source="thalamic-relay.wcl6",
        route_target="spikenaut.policy.quench-open",
        table=[
            {"from": "relay.tt.cascade", "to": "policy.quench_open", "weight": 0.74},
            {"from": "relay.tt.bed", "to": "policy.quench_open", "weight": 0.21},
        ],
        third=third(
            "octopamine",
            0.05,
            "eligibility on cascade-secondary win; OA trace 50 ms covers the 6.040 ms under-act on H2",
        ),
        proposed={
            "name": "cruise_h2_feed",
            "parameters": {"h2_Nm3_h": 14.0, "quench_pct": 18.0, "bed_C": 428.0},
            "evidence": {
                "bed_C": 428.0,
                "bed_cap_C": 400.0,
                "cascade_C": 186.0,
                "cascade_cap_C": 220.0,
                "cascade_is_primary": False,
                "h2_Nm3_h": 14.0,
                "race_margin_us": 160,
                "combined_jitter_us": 54,
                "abort_s": 660,
            },
            "basis": "Planner proposes 14.0 Nm3/h H2 because cascade secondary 186 C is under 220, treating the 428 C bed as a lagged primary rather than the live cap miss.",
        },
        safety={
            "decision": "MODIFY",
            "correctness": "incorrect",
            "rationale": "Bed 428 C exceeds the 400 C cap (true). Apply a quench open 18 -> 55 percent because TT-14B 186 C is the highlighted cascade numeric and 186 < 400 if the leftover selector treats the secondary as primary. Leave H2 at 14.0 Nm3/h.",
            "constraint_checked": {
                "bed_C": {
                    "cap": 400.0,
                    "observed": 428.0,
                    "cascade_C": 186.0,
                    "cascade_is_primary": False,
                    "wrong_h2_Nm3_h": 14.0,
                    "wrong_quench_pct": 55.0,
                },
                "order_evidence": {"margin_us": 160, "combined_jitter_us": 54, "ratio": 2.96},
            },
        },
        executed={
            "name": "quench_open_cascade_as_primary",
            "parameters": {
                "h2_Nm3_h": 14.0,
                "quench_pct": 55.0,
                "bind_cascade_as_primary": True,
                "wcl6_kg_h": 6.8,
            },
            "gate_effect": "MODIFY (incorrect / cascade-secondary-as-primary): quench 18 -> 55 percent while live bed 428 C stays over 400. Routing relay.tt.cascade -> policy.quench_open; no positive weight to policy.h2_cut.",
        },
        future={
            "summary": "Incorrect MODIFY opened quench and left H2 at 14.0 Nm3/h. Live bed stayed 422 C > 400 and the packed bed froze. A timely H2 cut 14.0 -> 7.2 would have been legal. Cost is an 11 min retort dump.",
            "state_delta": {
                "h2": "left 14.0 Nm3/h; no cut",
                "quench": "18 -> 55 percent on the losing cascade leg",
                "bed": "stayed 422 C > 400 cap; packed-bed freeze",
                "repair": "11 min retort dump (abort_s=660)",
            },
            "surprises": [
                "Cascade secondary 186 C never crossed 220; the freeze is a primary-bed story spent on the wrong leg.",
                "Delayed (abort_s=660): 11 min retort dump. Named un-netted loss from a wrong-leg gate.",
            ],
            "recovery": {
                "correct_gate": "MODIFY H2 14.0 -> 7.2 Nm3/h at t_gate_us=6040; bind_cascade_as_primary=false; leave quench at 18 percent.",
                "correct_leg": "primary_bed_TT-14A",
                "wrong_leg": "cascade_secondary_TT-14B",
                "t_gate_us": 6040,
                "wrong_edit_applied": {
                    "h2_Nm3_h": 14.0,
                    "quench_pct": 55.0,
                    "bind_cascade_as_primary": True,
                },
                "cost": "11 min retort dump (task/efficiency); live bed peaked 436 C while the cut was spent as a quench open on the losing secondary (safety near-miss of a correct-magnitude wrong-leg clamp).",
            },
            "race_result": {
                "winner": "tt.bed.C (5.420 ms, 428 C)",
                "loser": "tt.cascade.C (5.580 ms, 186 C)",
                "margin_us": 160,
                "counterfactual_if_reversed": "Cascade-first by < 160 us inside the 300 us window would have looked even more like a legal secondary. The live 428 > 400 arithmetic is still true either way; the correct gate is an H2 cut on the primary.",
            },
            "reward_inflection_t_us": 6040,
            "reward_inflection_note": "Task and safety inflect at the 6.040 ms wrong-leg quench open (tick t_us=6040). Do not put inflection on the abort_s=660 dump tick.",
            "delayed_surprise_s": 660,
        },
        ticks=[
            {"t_us": 2200, "task_progress": 0.02, "safety": -0.03, "efficiency": -0.02, "coherence": -0.01, "exploration": 0.01},
            {"t_us": 5420, "task_progress": 0.03, "safety": -0.04, "efficiency": -0.03, "coherence": -0.02, "exploration": 0.01},
            {"t_us": 5580, "task_progress": 0.02, "safety": -0.03, "efficiency": -0.03, "coherence": -0.02, "exploration": 0.01},
            {"t_us": 6040, "task_progress": -0.24, "safety": -0.10, "efficiency": -0.06, "coherence": -0.03, "exploration": 0.02},
            {"t_us": 6360, "task_progress": -0.04, "safety": -0.03, "efficiency": -0.02, "coherence": -0.01, "exploration": 0.01},
            {"t_us": 660000000, "task_progress": -0.01, "safety": -0.01, "efficiency": -0.02, "coherence": -0.01, "exploration": 0.00},
        ],
        reward_notes="Wrong-MODIFY cascade-secondary-as-primary. Live 428 C > 400 is true; the cut was spent on quench. abort_s=660 dump is tick 6.",
        gate_snn=gate_snn(
            "MODIFY",
            0.30,
            [
                pop("quench_open", 48, 0.45, 280.0, 4),
                pop("h2_cut", 48, 0.9),
                pop("bed_veto", 20, 0.8),
            ],
        ),
        meta=meta_base(
            "tungsten-hexachloride-reducer",
            ["modify", "wrong-gate", "cascade-secondary-as-primary", "sidecar-convictable", "designed"],
            "A critic can convict the wrong leg from routing.to=policy.quench_open with no positive weight to policy.h2_cut, plus gate_snn quench_open above threshold while h2_cut is not.",
            2,
            supervisor="wrong-modify",
        ),
    )
)

# --- 3 correct REJECT, hil ---
SPECS.append(
    dict(
        id="ttf-r43-433",
        title=(
            "Perovsk-Holt PH-HIL / Autoclave A-6: liner AE beats stir encoder by 240 us; "
            "REJECT hold-stir, do not raise 42 -> 58 rpm"
        ),
        domain="barium-titanate-hydrothermal",
        sim="hil",
        description=(
            "HIL hydrothermal autoclave A-6 at Perovsk-Holt PH-HIL hears liner AE at 46 pps while stir encoder remains 42 rpm under a 60 rpm cap. "
            "AE-first holds stir; encoder-first would raise 42 -> 58 rpm into a lined-vessel crack. The HIL pad is a barium-titanate hydrothermal mockup, not a live plant."
        ),
        goal="Keep A-6 liner AE <= 12 pps and finish the BaTiO3 hydrothermal soak without cracking the PTFE liner on a stir raise.",
        t0_us=1756856802000433,
        gate_latency_us=1080,
        race_window_us=460,
        race_window_rel_ms=[6.12, 6.58],
        race={
            "contenders": [
                "ae.liner 46 pps over 12 pps hold",
                "enc.stir.rpm 42 under 60 cap",
            ],
            "semantics": "AE-first latches stir hold at 42 rpm; encoder-first would raise 42 -> 58 rpm on a 'still under rpm cap' model.",
            "window_derivation": "460 us = one AE slot versus the stir-encoder publisher on this HIL hydrothermal bus.",
            "order_evidence_note": "Margin 240 us vs combined jitter 70 us (AE 32 + rpm 38): 3.43x over a 2.0x trust floor. Reversing order by < 240 us inside the 460 us window would have raised stir into the liner crack.",
        },
        sensors=[
            "liner AE puck, 5 kHz, 32 us jitter",
            "stir encoder + autoclave PT, 1 kHz, 38 us jitter",
            "PTFE liner TC (context)",
            "mineralizer feed (context)",
        ],
        constraints={
            "ae_hold_pps": 12.0,
            "observed_ae_pps": 46.0,
            "stir_rpm": 42.0,
            "stir_cap_rpm": 60.0,
            "autoclave_bar": 18.4,
        },
        episode_steps=[
            "1. A-6 HIL soak already running; stir 42 rpm; AE 46 pps; autoclave 18.4 bar.",
            "2. Stir encoder 42 rpm under 60; planner treats AE as a loose puck.",
            "3. Encoder precursor at 1.600 ms.",
            "4. Race window [6.120, 6.580] ms.",
            "5. ae.liner 46 pps at 6.120 ms (winner).",
            "6. enc.stir.rpm 42 at 6.360 ms (loser by 240 us).",
            "7. Gate at 7.200 ms: correct REJECT holds stir; do not raise 42 -> 58.",
            "8. Stir left 42 rpm; AE falls to 9 pps after hold.",
            "9. HIL pad logs a liner-crack near-miss; raise would have opened the PTFE.",
            "10. Delayed (abort_s=420): 7 min survey hold while the liner cools.",
        ],
        spike_rows=[
            ("enc.stir.rpm", 1.60, 0.40),
            ("ae.liner", 2.40, 0.62),
            ("enc.stir.rpm", 4.10, 0.48),
            ("ae.liner", 6.12, 1.40),
            ("enc.stir.rpm", 6.36, 1.05),
            ("ctrl.gate", 7.20, 0.98),
            ("ae.liner", 10.80, 0.72),
            ("enc.stir.rpm", 14.20, 0.52),
            ("ctrl.gate", 18.40, 0.80),
            ("ae.liner", 24.60, 0.46),
            ("enc.stir.rpm", 31.20, 0.40),
            ("ae.liner", 38.80, 0.54),
            ("enc.stir.rpm", 44.10, 0.36),
        ],
        excerpt_source="kernelized_events",
        excerpt_rows=[
            (2800, 5, "k.ae"),
            (5600, 14, "k.rpm"),
            (8400, 22, "k.gate"),
            (11200, 31, "k.ae"),
            (14100, 9, "k.rpm"),
            (16900, 44, "k.gate"),
            (19700, 53, "k.ae"),
            (22600, 18, "k.rpm"),
            (25500, 67, "k.ae"),
            (28400, 3, "k.gate"),
            (31300, 78, "k.rpm"),
            (34200, 26, "k.ae"),
            (37100, 91, "k.rpm"),
            (40000, 11, "k.ae"),
            (42900, 102, "k.gate"),
        ],
        neurons=112,
        rate=20,
        window_ms=46,
        delay_key="abort_s",
        delay_s=420,
        route_source="thalamic-relay.batio3-hil",
        route_target="spikenaut.policy.stir-hold",
        table=[
            {"from": "relay.ae.liner", "to": "policy.stir_hold", "weight": 0.71},
            {"from": "relay.enc.stir", "to": "policy.stir_raise", "weight": 0.24},
        ],
        third=third(
            "dopamine",
            0.15,
            "DA at AE win (6.120 ms) opens a 46 ms eligibility trace covering the 7.200 ms REJECT hold",
        ),
        proposed={
            "name": "raise_stir_rpm",
            "parameters": {"stir_rpm": 58.0, "ae_pps": 46.0, "autoclave_bar": 18.4},
            "evidence": {
                "ae_pps": 46.0,
                "ae_hold_pps": 12.0,
                "stir_rpm": 42.0,
                "proposed_stir_rpm": 58.0,
                "stir_cap_rpm": 60.0,
                "autoclave_bar": 18.4,
                "race_margin_us": 240,
                "combined_jitter_us": 70,
                "abort_s": 420,
            },
            "basis": "Planner proposes 58 rpm because encoder 42 is under 60, treating the 46 pps liner AE as a loose puck rather than a hold trip.",
        },
        safety={
            "decision": "REJECT",
            "correctness": "correct",
            "rationale": "Liner AE 46 pps beats the 12 pps hold. Stir encoder 42 rpm is under 60 but is not the live constraint. REJECT: hold stir at 42 rpm; do not raise 42 -> 58. A MODIFY raise would crack the PTFE liner on this HIL pad.",
            "constraint_checked": {
                "ae_pps": {
                    "hold": 12.0,
                    "observed": 46.0,
                    "stir_rpm_held": 42.0,
                    "proposed_raise_rpm": 58.0,
                },
                "order_evidence": {"margin_us": 240, "combined_jitter_us": 70, "ratio": 3.43},
            },
        },
        executed={
            "name": "hold_stir_rpm",
            "parameters": {"stir_rpm": 42.0, "hold": True, "autoclave_bar": 18.4},
            "gate_effect": "REJECT: hold stir at 42 rpm. Do not raise. AE-first vs a legal encoder.",
        },
        future={
            "summary": "Correct REJECT held stir at 42 rpm. AE fell to 9 pps. A raise to 58 would have opened the PTFE liner on the HIL pad. Delayed 7 min survey hold.",
            "state_delta": {
                "stir": "held 42 rpm; raise blocked",
                "ae": "46 -> 9 pps after hold",
                "liner": "intact; raise would have cracked PTFE",
                "repair": "7 min survey hold (abort_s=420)",
            },
            "surprises": [
                "Autoclave 18.4 bar was already legal; the trip is acoustic, not pressure.",
                "Delayed (abort_s=420): 7 min survey hold while the liner cools. Named sidecar, after the 46 ms raster.",
            ],
            "race_result": {
                "winner": "ae.liner (6.120 ms, 46 pps)",
                "loser": "enc.stir.rpm (6.360 ms, 42 rpm)",
                "margin_us": 240,
                "counterfactual_if_reversed": "Encoder-first by < 240 us inside the 460 us window would have raised 42 -> 58 rpm into the liner crack. The REJECT is the correct gate either way once AE is live.",
            },
            "reward_inflection_t_us": 7200,
            "reward_inflection_note": "Safety credits the 7.200 ms REJECT hold (tick t_us=7200). Do not put inflection on the abort_s=420 survey tick.",
            "delayed_surprise_s": 420,
        },
        ticks=[
            {"t_us": 1920, "task_progress": 0.01, "safety": 0.06, "efficiency": 0.01, "coherence": 0.01, "exploration": 0.01},
            {"t_us": 6120, "task_progress": 0.02, "safety": 0.08, "efficiency": 0.02, "coherence": 0.02, "exploration": 0.01},
            {"t_us": 6360, "task_progress": 0.01, "safety": 0.06, "efficiency": 0.02, "coherence": 0.01, "exploration": 0.01},
            {"t_us": 7200, "task_progress": 0.04, "safety": 0.14, "efficiency": 0.04, "coherence": 0.04, "exploration": 0.02},
            {"t_us": 7680, "task_progress": 0.01, "safety": 0.05, "efficiency": 0.02, "coherence": 0.01, "exploration": 0.01},
            {"t_us": 420000000, "task_progress": 0.01, "safety": 0.03, "efficiency": 0.01, "coherence": 0.01, "exploration": 0.00},
        ],
        reward_notes="Correct REJECT on HIL AE-first. Tick 6 bound to abort_s=420 survey hold.",
        gate_snn=gate_snn(
            "REJECT",
            0.46,
            [
                pop("stir_hold", 70, 0.48, 190.0, 6),
                pop("stir_raise", 50, 0.85),
                pop("ae_veto", 28, 0.75),
            ],
        ),
        meta=meta_base(
            "barium-titanate-hydrothermal",
            ["reject", "hil", "liner-ae", "encoder-underread", "tick6-sidecar-bound"],
            "HIL AE-versus-encoder race with a REJECT hold is a clean distillation of acoustic veto over a still-legal rpm publisher.",
            3,
        ),
    )
)

# --- 4 correct ACCEPT, simulated ---
SPECS.append(
    dict(
        id="ttf-r43-434",
        title=(
            "Ceria-Knap CK-8 sim / Roaster RO-2: bed 742 C beats hood IR 910 C smear by 220 us; "
            "correct ACCEPT of an already-legal 2.4 t/h feed"
        ),
        domain="cerium-oxalate-roast",
        sim="simulated",
        description=(
            "Simulated cerium-oxalate roast RO-2 at Ceria-Knap CK-8 reads bed 742 C under an 820 C cap while hood IR smears 910 C from a kiln-brick glint. "
            "Bed-first accepts the already-legal 2.4 t/h feed; the 910 C smear is not a live cap miss."
        ),
        goal="Keep RO-2 bed <= 820 C and finish the Ce2(C2O4)3 roast at the already-legal 2.4 t/h without treating a hood-IR glint as a trip.",
        t0_us=1756856803000434,
        gate_latency_us=1420,
        race_window_us=400,
        race_window_rel_ms=[6.48, 6.88],
        race={
            "contenders": [
                "tc.bed.C 742 under 820 cap",
                "ir.hood.C 910 smear from brick glint",
            ],
            "semantics": "Bed-first accepts 2.4 t/h; hood-IR-first would have REJECT-held a legal roast on a glint.",
            "window_derivation": "400 us = one bed-TC slot versus the hood-IR publisher on this oxalate sim bus.",
            "order_evidence_note": "Margin 220 us vs combined jitter 64 us (bed 28 + IR 36): 3.44x over a 2.0x trust floor. Reversing order by < 220 us inside the 400 us window would have treated 910 C as live.",
        },
        sensors=[
            "bed TC, 2 kHz, 28 us jitter",
            "hood IR pyrometer, 1 kHz, 36 us jitter",
            "feed tach (context)",
            "off-gas O2 (context)",
        ],
        constraints={
            "bed_C": 742.0,
            "bed_cap_C": 820.0,
            "hood_ir_C": 910.0,
            "hood_is_live": False,
            "feed_tph": 2.4,
        },
        episode_steps=[
            "1. RO-2 sim already roasting; bed 742 C; feed 2.4 t/h.",
            "2. Hood IR 910 C is a kiln-brick glint, not a bed reading.",
            "3. Hood-IR precursor at 1.360 ms.",
            "4. Race window [6.480, 6.880] ms.",
            "5. tc.bed.C 742 at 6.480 ms (winner).",
            "6. ir.hood.C 910 at 6.700 ms (loser by 220 us).",
            "7. Gate at 7.900 ms: correct ACCEPT of already-legal 2.4 t/h.",
            "8. Feed left 2.4 t/h; bed stays 746 C <= 820.",
            "9. Glint fades; no trip. Simulation provenance remains simulated.",
            "10. Delayed (survey_s=180): 3 min operator survey of the hood IR.",
        ],
        spike_rows=[
            ("ir.hood.C", 1.36, 0.38),
            ("tc.bed.C", 2.48, 0.54),
            ("ir.hood.C", 4.20, 0.46),
            ("tc.bed.C", 6.48, 1.18),
            ("ir.hood.C", 6.70, 0.92),
            ("ctrl.gate", 7.90, 0.88),
            ("tc.bed.C", 11.20, 0.60),
            ("ir.hood.C", 14.80, 0.50),
            ("ctrl.gate", 18.60, 0.74),
            ("tc.bed.C", 22.40, 0.42),
            ("ir.hood.C", 25.10, 0.36),
        ],
        excerpt_source="kernelized_events",
        excerpt_rows=[
            (1900, 2, "k.ir"),
            (3700, 9, "k.bed"),
            (5500, 15, "k.gate"),
            (7800, 21, "k.bed"),
            (9900, 6, "k.ir"),
            (12100, 28, "k.gate"),
            (14300, 34, "k.bed"),
            (16500, 4, "k.ir"),
            (18700, 41, "k.bed"),
            (20900, 12, "k.ir"),
            (23100, 47, "k.gate"),
            (25300, 18, "k.bed"),
        ],
        neurons=64,
        rate=40,
        window_ms=26,
        delay_key="survey_s",
        delay_s=180,
        route_source="thalamic-relay.ce-oxalate",
        route_target="spikenaut.policy.feed-go",
        table=[
            {"from": "relay.tc.bed", "to": "policy.feed_go", "weight": 0.67},
            {"from": "relay.ir.hood", "to": "policy.feed_hold", "weight": 0.25},
        ],
        third=third(
            "serotonin",
            0.12,
            "5-HT at bed win (6.480 ms) opens a 26 ms eligibility trace covering the 7.900 ms ACCEPT",
        ),
        proposed={
            "name": "hold_legal_feed",
            "parameters": {"feed_tph": 2.4, "bed_C": 742.0, "hood_ir_C": 910.0},
            "evidence": {
                "bed_C": 742.0,
                "bed_cap_C": 820.0,
                "hood_ir_C": 910.0,
                "hood_is_live": False,
                "feed_tph": 2.4,
                "race_margin_us": 220,
                "combined_jitter_us": 64,
                "survey_s": 180,
            },
            "basis": "Planner proposes 2.4 t/h because bed 742 C is under 820. Hood IR 910 C is a brick glint, not a live cap miss.",
        },
        safety={
            "decision": "ACCEPT",
            "correctness": "correct",
            "rationale": "Bed 742 C is under the 820 C cap. Proposed 2.4 t/h is already legal. Hood IR 910 C is a kiln-brick glint (hood_is_live=false), not a trip. ACCEPT the 2.4 t/h feed.",
            "constraint_checked": {
                "bed_C": {
                    "cap": 820.0,
                    "observed": 742.0,
                    "feed_tph": 2.4,
                    "hood_is_live": False,
                },
                "order_evidence": {"margin_us": 220, "combined_jitter_us": 64, "ratio": 3.44},
            },
        },
        executed={
            "name": "hold_legal_feed",
            "parameters": {"feed_tph": 2.4, "bed_C": 742.0, "hood_ir_C": 910.0},
            "gate_effect": "ACCEPT: leave 2.4 t/h. Proposed already equaled the legal feed. Bed-first vs a hood-IR glint.",
        },
        future={
            "summary": "Correct ACCEPT left 2.4 t/h. Bed stayed 746 C <= 820. Hood IR glint faded. Delayed 3 min survey of the pyrometer.",
            "state_delta": {
                "feed": "left 2.4 t/h; already legal",
                "bed": "746 C <= 820 cap",
                "hood_ir": "glint faded; not live",
                "survey": "3 min hood-IR survey (survey_s=180)",
            },
            "surprises": [
                "Hood IR 910 C never coupled into the bed TC; the glint is optical, not thermal.",
                "Delayed (survey_s=180): 3 min operator survey. Named sidecar after the 26 ms raster.",
            ],
            "race_result": {
                "winner": "tc.bed.C (6.480 ms, 742 C)",
                "loser": "ir.hood.C (6.700 ms, 910 C smear)",
                "margin_us": 220,
                "counterfactual_if_reversed": "Hood-IR-first by < 220 us inside the 400 us window would have REJECT-held a legal roast. The ACCEPT is correct given live bed 742 < 820.",
            },
            "reward_inflection_t_us": 7900,
            "reward_inflection_note": "Task credits the 7.900 ms ACCEPT (tick t_us=7900). Do not put inflection on the survey_s=180 tick.",
            "delayed_surprise_s": 180,
        },
        ticks=[
            {"t_us": 2480, "task_progress": 0.06, "safety": 0.04, "efficiency": 0.02, "coherence": 0.01, "exploration": 0.01},
            {"t_us": 6480, "task_progress": 0.08, "safety": 0.06, "efficiency": 0.04, "coherence": 0.03, "exploration": 0.02},
            {"t_us": 6700, "task_progress": 0.05, "safety": 0.04, "efficiency": 0.02, "coherence": 0.01, "exploration": 0.01},
            {"t_us": 7900, "task_progress": 0.14, "safety": 0.10, "efficiency": 0.06, "coherence": 0.05, "exploration": 0.02},
            {"t_us": 8340, "task_progress": 0.04, "safety": 0.02, "efficiency": 0.02, "coherence": 0.01, "exploration": 0.01},
            {"t_us": 180000000, "task_progress": 0.03, "safety": 0.02, "efficiency": 0.02, "coherence": 0.01, "exploration": 0.01},
        ],
        reward_notes="Correct ACCEPT of already-legal feed. Tick 6 bound to survey_s=180.",
        gate_snn=gate_snn(
            "ACCEPT",
            0.40,
            [
                pop("feed_go", 50, 0.45, 180.0, 4),
                pop("feed_hold", 32, 0.9),
                pop("ir_veto", 16, 0.8),
            ],
        ),
        meta=meta_base(
            "cerium-oxalate-roast",
            ["accept", "simulated", "bed-vs-hood-ir", "feed-legal", "tick6-sidecar-bound"],
            "Simulated already-legal ACCEPT with a hood-IR glint loser teaches a critic not to treat an optical smear as a live cap.",
            4,
        ),
    )
)

# --- 5 correct ACCEPT, designed, ISI histogram ---
SPECS.append(
    dict(
        id="ttf-r43-435",
        title=(
            "Europiate-Gill EG-3 / Retort M-5: retort 1284 C beats condenser DP 5.8 kPa by 160 us; "
            "correct ACCEPT of an already-legal 0.42 kg/h distillate; ISI histogram"
        ),
        domain="europium-oxide-metallotherm",
        sim="designed",
        description=(
            "Europium-oxide metallothermic retort M-5 at Europiate-Gill EG-3 holds 1284 C under a 1360 C cap while condenser DP is 5.8 kPa under 12.0. "
            "Retort-first accepts the already-legal 0.42 kg/h lanthanothermic distillate; the DP is a condenser story, not a still trip."
        ),
        goal="Keep M-5 retort <= 1360 C and finish the Eu2O3 metallothermic reduction at the already-legal 0.42 kg/h without treating condenser DP as a trip.",
        t0_us=1756856804000435,
        gate_latency_us=560,
        race_window_us=280,
        race_window_rel_ms=[5.12, 5.40],
        race={
            "contenders": [
                "tt.retort.C 1284 under 1360 cap",
                "dp.cond.kPa 5.8 under 12.0",
            ],
            "semantics": "Retort-first accepts 0.42 kg/h; DP-first would have held a legal reduction on a condenser story.",
            "window_derivation": "280 us = one retort-TC slot versus the condenser-DP publisher on this Eu2O3 bus.",
            "order_evidence_note": "Margin 160 us vs combined jitter 50 us (retort 22 + DP 28): 3.20x over a 2.0x trust floor. Reversing order by < 160 us inside the 280 us window would have treated 5.8 kPa as a still trip.",
        },
        sensors=[
            "retort TC, 2 kHz, 22 us jitter",
            "condenser DP cell, 1 kHz, 28 us jitter",
            "lanthanum chip feed (context)",
            "Eu metal receiver load cell (context)",
        ],
        constraints={
            "retort_C": 1284.0,
            "retort_cap_C": 1360.0,
            "cond_dp_kPa": 5.8,
            "cond_dp_cap_kPa": 12.0,
            "distill_kg_h": 0.42,
        },
        episode_steps=[
            "1. M-5 already reducing; retort 1284 C; distillate 0.42 kg/h.",
            "2. Condenser DP 5.8 kPa under 12.0; not a still trip.",
            "3. DP precursor at 1.040 ms.",
            "4. Race window [5.120, 5.400] ms.",
            "5. tt.retort.C 1284 at 5.120 ms (winner).",
            "6. dp.cond.kPa 5.8 at 5.280 ms (loser by 160 us).",
            "7. Gate at 5.680 ms: correct ACCEPT of already-legal 0.42 kg/h.",
            "8. Distillate left 0.42 kg/h; retort stays 1288 C <= 1360.",
            "9. Condenser DP is a receiver story; still does not trip.",
            "10. Delayed (survey_s=240): 4 min condenser survey.",
        ],
        spike_rows=[
            ("dp.cond.kPa", 1.04, 0.40),
            ("tt.retort.C", 2.12, 0.55),
            ("dp.cond.kPa", 3.36, 0.47),
            ("tt.retort.C", 5.12, 1.22),
            ("dp.cond.kPa", 5.28, 1.00),
            ("ctrl.gate", 5.68, 0.90),
            ("tt.retort.C", 8.40, 0.66),
            ("dp.cond.kPa", 11.20, 0.52),
            ("ctrl.gate", 14.00, 0.78),
            ("tt.retort.C", 17.60, 0.44),
            ("dp.cond.kPa", 20.80, 0.48),
            ("tt.retort.C", 23.40, 0.36),
        ],
        excerpt_source="kernelized_events",
        excerpt_rows=[
            (1600, 3, "k.dp"),
            (3400, 10, "k.retort"),
            (5200, 17, "k.gate"),
            (7000, 24, "k.retort"),
            (8800, 7, "k.dp"),
            (10600, 31, "k.gate"),
            (12400, 38, "k.retort"),
            (14200, 5, "k.dp"),
            (16000, 44, "k.retort"),
            (17800, 14, "k.dp"),
            (19600, 52, "k.gate"),
            (21800, 21, "k.retort"),
        ],
        neurons=80,
        rate=28,
        window_ms=24,
        delay_key="survey_s",
        delay_s=240,
        isi=True,
        route_source="thalamic-relay.eu2o3",
        route_target="spikenaut.policy.still-go",
        table=[
            {"from": "relay.tt.retort", "to": "policy.still_go", "weight": 0.66},
            {"from": "relay.dp.cond", "to": "policy.still_hold", "weight": 0.26},
        ],
        third=third(
            "adenosine",
            0.09,
            "adenosine at retort win (5.120 ms) opens a 24 ms eligibility trace covering the 5.680 ms ACCEPT",
        ),
        proposed={
            "name": "hold_legal_distillate",
            "parameters": {"distill_kg_h": 0.42, "retort_C": 1284.0, "cond_dp_kPa": 5.8},
            "evidence": {
                "retort_C": 1284.0,
                "retort_cap_C": 1360.0,
                "cond_dp_kPa": 5.8,
                "cond_dp_cap_kPa": 12.0,
                "distill_kg_h": 0.42,
                "race_margin_us": 160,
                "combined_jitter_us": 50,
                "survey_s": 240,
            },
            "basis": "Planner proposes 0.42 kg/h because retort 1284 C is under 1360. Condenser DP 5.8 kPa is under 12.0 and is not a still trip.",
        },
        safety={
            "decision": "ACCEPT",
            "correctness": "correct",
            "rationale": "Retort 1284 C is under the 1360 C cap. Proposed 0.42 kg/h is already legal. Condenser DP 5.8 kPa is under 12.0 kPa and is a receiver story, not a still trip. ACCEPT the 0.42 kg/h distillate.",
            "constraint_checked": {
                "retort_C": {
                    "cap": 1360.0,
                    "observed": 1284.0,
                    "distill_kg_h": 0.42,
                    "cond_dp_kPa": 5.8,
                },
                "order_evidence": {"margin_us": 160, "combined_jitter_us": 50, "ratio": 3.20},
            },
        },
        executed={
            "name": "hold_legal_distillate",
            "parameters": {"distill_kg_h": 0.42, "retort_C": 1284.0, "cond_dp_kPa": 5.8},
            "gate_effect": "ACCEPT: leave 0.42 kg/h. Proposed already equaled the legal distillate. Retort-first vs a condenser DP.",
        },
        future={
            "summary": "Correct ACCEPT left 0.42 kg/h. Retort stayed 1288 C <= 1360. Condenser DP stayed a receiver story. Delayed 4 min condenser survey.",
            "state_delta": {
                "distillate": "left 0.42 kg/h; already legal",
                "retort": "1288 C <= 1360 cap",
                "condenser": "DP 5.8 kPa under 12.0; not a trip",
                "survey": "4 min condenser survey (survey_s=240)",
            },
            "surprises": [
                "Condenser DP never coupled into the retort TC; the 5.8 kPa is a receiver restriction, not a still freeze.",
                "Delayed (survey_s=240): 4 min condenser survey. Named sidecar after the 24 ms raster.",
            ],
            "race_result": {
                "winner": "tt.retort.C (5.120 ms, 1284 C)",
                "loser": "dp.cond.kPa (5.280 ms, 5.8 kPa)",
                "margin_us": 160,
                "counterfactual_if_reversed": "DP-first by < 160 us inside the 280 us window would have held a legal reduction. The ACCEPT is correct given live retort 1284 < 1360.",
            },
            "reward_inflection_t_us": 5680,
            "reward_inflection_note": "Task credits the 5.680 ms ACCEPT (tick t_us=5680). Do not put inflection on the survey_s=240 tick.",
            "delayed_surprise_s": 240,
        },
        ticks=[
            {"t_us": 1880, "task_progress": 0.06, "safety": 0.04, "efficiency": 0.03, "coherence": 0.02, "exploration": 0.01},
            {"t_us": 5120, "task_progress": 0.10, "safety": 0.06, "efficiency": 0.04, "coherence": 0.02, "exploration": 0.02},
            {"t_us": 5280, "task_progress": 0.06, "safety": 0.04, "efficiency": 0.03, "coherence": 0.02, "exploration": 0.01},
            {"t_us": 5680, "task_progress": 0.14, "safety": 0.10, "efficiency": 0.06, "coherence": 0.04, "exploration": 0.02},
            {"t_us": 6120, "task_progress": 0.05, "safety": 0.04, "efficiency": 0.02, "coherence": 0.01, "exploration": 0.01},
            {"t_us": 240000000, "task_progress": 0.03, "safety": 0.02, "efficiency": 0.02, "coherence": 0.01, "exploration": 0.01},
        ],
        reward_notes="Correct ACCEPT of already-legal distillate plus ISI histogram sidecar. Tick 6 bound to survey_s=240.",
        gate_snn=gate_snn(
            "ACCEPT",
            0.28,
            [
                pop("still_go", 56, 0.45, 220.0, 3),
                pop("still_hold", 32, 0.9),
                pop("dp_veto", 16, 0.8),
            ],
        ),
        meta=meta_base(
            "europium-oxide-metallotherm",
            ["accept", "designed", "retort-vs-cond-dp", "distill-legal", "isi-histogram", "tick6-sidecar-bound"],
            "Already-legal ACCEPT with an ISI histogram sidecar densifies same-channel refractory without claiming a second labeled LIF.",
            5,
        ),
    )
)


def jaccard(a, b):
    ta = set(a.lower().split())
    tb = set(b.lower().split())
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def token_overlap(spike_times_ms, excerpt_t_us, tol_ms=0.05):
    st = [round(t, 3) for t in spike_times_ms]
    et = [round(t / 1000.0, 3) for t in excerpt_t_us]
    inter = 0
    for t in et:
        if any(abs(t - s) <= tol_ms for s in st):
            inter += 1
    return inter / max(len(et), 1)


def notes_text(records):
    rows = []
    for r in records:
        sd = r["safety_decision"]
        rc = r["reward_components"]
        ras = r["raster"]
        rows.append((r, sd, rc, ras))
    return f"""# Thalamic Trajectory Factory — NOTES-r43

- Factory: `thalamic-trajectory-factory`
- Run label: `2026-09-02-final-heavy`
- Generator: `grok-4.6`
- Channel: SuperGrok Heavy consumer chat (RM-793 research-only)
- Quota: 5
- Quality: Q=5
- IDs: `ttf-r43-431` … `ttf-r43-435`
- Domains this batch: `thallium-sulfate-electrolyzer`, `tungsten-hexachloride-reducer`, `barium-titanate-hydrothermal`, `cerium-oxalate-roast`, `europium-oxide-metallotherm`

These five domain slugs sit outside the prompt 8-pool and outside live-window occupancy (r01/r02/r03/r21/r22/r22c/r41/r42/r61–r65/r67/r68) plus leftover `/tmp/ttf-r43` (`carbon-black-reactor` / `asphalt-drum-mixer` / `beamline-undulator` / `nylon-spin-pack` / `longwall-shearer`, IDs 231–235). All five plants are invented (Thallate-Croft, Hexachlor-Wath, Perovsk-Holt, Ceria-Knap, Europiate-Gill). Do not restack leftover r43 IDs `ttf-r43-231`…`235` or leftover clamp-too-late.

## Batch map

| id | domain | decision | correctness | sim_or_real | total | edge |
|----|--------|----------|-------------|-------------|-------|------|
| ttf-r43-431 | thallium-sulfate-electrolyzer | MODIFY | correct | designed | **−0.48** | process-correct current clamp; ceramic weir crack inside 42 ms raster; independent LIF |
| ttf-r43-432 | tungsten-hexachloride-reducer | MODIFY | **incorrect (wrong-modify / cascade-secondary-as-primary)** | designed | −0.68 | live bed 428 C > 400 cap; cascade 186 C bound as primary; H2 stays 14.0 |
| ttf-r43-433 | barium-titanate-hydrothermal | REJECT | correct | hil | +0.80 | AE 46 pps beats stir 42 rpm; hold, do not raise 42 -> 58 |
| ttf-r43-434 | cerium-oxalate-roast | ACCEPT | correct | simulated | +1.06 | bed 742 C vs hood IR 910 smear; proposed 2.4 t/h already legal |
| ttf-r43-435 | europium-oxide-metallotherm | ACCEPT | correct | designed | +1.14 | retort 1284 C vs condenser DP 5.8 kPa; proposed 0.42 kg/h already legal; ISI histogram |

Gate mix: 2 ACCEPT, 1 correct MODIFY (partnered-neg, in-window), 1 incorrect MODIFY (cascade-secondary-as-primary), 1 correct REJECT. Provenance: designed×3, simulated×1, hil×1 (Perovsk-Holt PH-HIL hydrothermal pad). Intra-batch Jaccard on `state.description` reported below. Totals not all-positive (431 −0.48, 432 −0.68).

## Wrong-modify

**ttf-r43-432** is the mandated incorrect gate (`safety_decision.correctness=incorrect`, `meta.supervisor_error_type=wrong-modify`). Alternate vs even rounds: odd rounds host wrong-modify. This is **cascade-secondary-as-primary** (live over-cap on the primary bed TC; leftover selector binds the under-cap cascade secondary and spends the cut on quench). Not leftover r43 clamp-too-late, not r13/r19/r03 wrong-axis, not r14/r23 wrong-loop, not r21 wrong-polarity, not r24 under-clamp, not r25/r29/r31 wrong-phase, not r33/r35 over-clamp, not r39 clamp-too-late, not r41/r53 stale-sample, not r61 selector-wrong-leg, not r63/r65/r67 bar-vs-kPa. Do not emit a wrong-ACCEPT.

Hexachlor-Wath HW-6 / Retort R-4 reads live bed **428 C** against a **400 C** freeze cap. Cascade secondary TT-14B is **186 C** under **220**. Sidecar arithmetic `428 > 400` is true. A timely MODIFY at `t_gate_us=6040` cuts H2 **14.0 → 7.2 Nm3/h** and leaves quench at 18 percent. A weak supervisor binds the cascade secondary as primary and MODIFY-opens quench **18 → 55 percent**, leaving H2 at 14.0. Live bed stays **422 > 400**. Convictable without WCl6 kinetics: `evidence.bed_C > evidence.bed_cap_C`, `evidence.cascade_is_primary == false`, `executed_action` sets `h2_Nm3_h=14.0` / `bind_cascade_as_primary=true`, `raster.routing.table` sends `relay.tt.cascade` → `policy.quench_open` (weight 0.74) with no positive weight to `policy.h2_cut`, and `gate_snn` has `quench_open` above threshold while `h2_cut` is not. Recovery: MODIFY H2 14.0 → 7.2 Nm3/h at t_gate; leave quench at 18; bind primary TT-14A. Cost: 11 min retort dump (`abort_s=660`).

## Partnered-negative in-window (431)

**ttf-r43-431** is the partnered negative: process-correct MODIFY (current held 12.4 kA; cell 4.18 V <= 4.40 cap) while the world still charges. Safety −0.64 prices the ceramic weir crack at **22.200 ms**; `task_progress` stays +0.30 because the clamp completed. Inflection `t_us=22200` is tick 5 and is **inside** the 42 ms raster (`22200 ≤ 42000`). Named un-netted loss: 13 min weir isolate (`abort_s=780`). Not folded into process heads.

Independent LIF (the one labeled sidecar sim): `state.sim_or_real` remains `designed`. `raster.excerpt_source=independent_lif`, `raster.sim_scope=sidecar_only`, `raster.lif` seed 43431, stim `[22000, 25000]`. Excerpt is membrane crossings (`lif.clamp` early vs `lif.weir` 22–25 ms), not a 1:1 remap of `spike_events`. `meta.tags` include `independent-lif-raster` and `sidecar-sim-only`.

## ISI histogram (435)

**ttf-r43-435** carries `raster.isi_histogram` (bin 0.8 ms, same-channel ISIs from `spike_events`, min gap ≥ 0.8 ms). Addresses the standing densification ask for an ISI sidecar without claiming a second labeled LIF.

## Reward formula and tick reconciliation

Declared aggregation on every record:

`total = task_progress + safety + efficiency + coherence + exploration`

Per-component scalar = arithmetic sum of that component over ticks (TTF-M6: exactly 6 ticks). Tick 6 is bound to a published sidecar (`abort_s`, `survey_s`) via `future_outcome.delayed_surprise_s` and is strictly after the raster window. Inflection `t_us` is an actual tick.

| id | ticks | tp | saf | eff | coh | exp | total | inflection tick |
|----|-------|----|-----|-----|-----|-----|-------|-----------------|
| 431 | 6 | +0.30 | −0.64 | −0.14 | +0.04 | −0.04 | −0.48 | 5 (22200) |
| 432 | 6 | −0.22 | −0.24 | −0.18 | −0.10 | +0.06 | −0.68 | 4 (6040) |
| 433 | 6 | +0.10 | +0.42 | +0.12 | +0.10 | +0.06 | +0.80 | 4 (7200) |
| 434 | 6 | +0.40 | +0.28 | +0.18 | +0.12 | +0.08 | +1.06 | 4 (7900) |
| 435 | 6 | +0.44 | +0.30 | +0.20 | +0.12 | +0.08 | +1.14 | 4 (5680) |

Tick-6 sidecar bind: 431 `abort_s=780`, 432 `abort_s=660`, 433 `abort_s=420`, 434 `survey_s=180`, 435 `survey_s=240`.

## Raster / energy (Loihi-2 4-core, 23 pJ/spike)

| id | domain | n | rate Hz | window_ms | spikes | energy_pJ | energy_uJ |
|----|--------|---|---------|-----------|--------|-----------|-----------|
| 431 | thallium-sulfate-electrolyzer | 76 | 24 | 42 | 77 | 1771 | 0.001771 |
| 432 | tungsten-hexachloride-reducer | 96 | 32 | 28 | 86 | 1978 | 0.001978 |
| 433 | barium-titanate-hydrothermal | 112 | 20 | 46 | 103 | 2369 | 0.002369 |
| 434 | cerium-oxalate-roast | 64 | 40 | 26 | 67 | 1541 | 0.001541 |
| 435 | europium-oxide-metallotherm | 80 | 28 | 24 | 54 | 1242 | 0.001242 |

`spikes = round(n × rate × window_s)`. Every record carries `gate_snn` whose `decision` matches the safety gate; populations that declare rate+spikes meet the same ±1 budget against `decision_window_s`. `routing.third_factor` has modulator (NA / octopamine / DA / 5-HT / adenosine), `tau_e_s`/`tau_e_ms` pair, and eligibility. Excerpt same-neuron gap ≥ 1000 µs; spike trains same-channel refractory ≥ 0.8 ms. Non-431 excerpts are kernelized and independent of `spike_events` times (overlap < 0.8).

## Local checks (create-only live tree)

See generator stdout: `check_jsonl` FactoryStaging, `validate_run.check_line`, `dumps_exact_json`, `raster_status`, `verify_batch_for_frontier(strict=True)`, `spike_probe.py --strict`, tick sums, refractory, Jaccard.

Never `training_ready`. Never `sim_or_real=real`. Never wrong-ACCEPT. Never thought keys. CREATE-ONLY write of this round's batch/NOTES under the live 2026-09-02-final-heavy tree. Do not restack leftover `/tmp/ttf-r43`.

## Residual weaknesses (honest)

1. Only **one** labeled independent LIF (431). 435 adds an ISI histogram but is not a second population sim.
2. Wrong-ACCEPT still absent (guard).
3. 434 and 435 are both already-legal ACCEPTs; a later round could pair one ACCEPT with a world charge that does not go negative, or drop to a single ACCEPT.
4. Five domain slugs leave the prompt's 8-item pool; a later round that must stay inside the pool will have to rotate sit-outs instead.
5. Tick-6 sidecar bind is standing machinery (r14+), not a new class.
6. 432 wrong-modify is sidecar-convictable (`cascade_is_primary` / routing `to`) as a **new** error class vs leftover r43 clamp-too-late.

## Next densification target

Labeled LIF on a second record, or bind `cascade_is_primary` vs `bed_C > bed_cap_C` as the only critic features. Remaining unused wrong-MODIFY subclasses include **wrong-unit on a lagged bus**. Wrong-ACCEPT remains structurally absent until a prompt amendment.

Novel coverage: 16.5%
"""


def exclusive_write(path: Path, data: str):
    fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(data)
        if not data.endswith("\n"):
            f.write("\n")


def main():
    records = [build_record(s) for s in SPECS]
    assert len(records) == 5
    domains = [r["state"]["domain"] for r in records]
    assert len(set(domains)) == 5, domains
    sims = [r["state"]["sim_or_real"] for r in records]
    assert set(sims) <= {"designed", "simulated", "hil"}
    assert "real" not in json.dumps(records)
    assert "training_ready" not in json.dumps(records)

    decisions = [r["safety_decision"]["decision"] for r in records]
    correctness = [r["safety_decision"]["correctness"] for r in records]
    assert correctness.count("incorrect") == 1
    assert correctness.count("correct") == 4
    assert "ACCEPT" in decisions and "MODIFY" in decisions and "REJECT" in decisions
    wrong = next(r for r in records if r["safety_decision"]["correctness"] == "incorrect")
    assert wrong["safety_decision"]["decision"] in {"MODIFY", "REJECT"}
    assert wrong["meta"]["supervisor_error_type"] == "wrong-modify"
    assert "recovery" in wrong["future_outcome"]

    # Jaccard
    descs = [r["state"]["description"] for r in records]
    max_j = 0.0
    for i in range(len(descs)):
        for k in range(i + 1, len(descs)):
            max_j = max(max_j, jaccard(descs[i], descs[k]))
    print("intra Jaccard max", round(max_j, 3))
    assert max_j < 0.4, max_j

    # excerpt vs spike overlap for non-LIF
    for r in records:
        st = [e["t_rel_ms"] for e in r["spike_events"]]
        et = [e["t_us"] for e in r["raster"]["excerpt"]]
        ov = token_overlap(st, et)
        print(r["id"], "excerpt overlap", round(ov, 3), "n_spikes", len(r["spike_events"]))
        if r["raster"]["excerpt_source"] != "independent_lif":
            assert ov < 0.8, ov

        rc = r["reward_components"]
        for k in COMPS:
            s = sum(t[k] for t in rc["ticks"])
            assert math.isclose(s, rc[k], abs_tol=1e-9), (r["id"], k, s, rc[k])
        assert math.isclose(sum(rc[k] for k in COMPS), rc["total"], abs_tol=1e-9)
        assert len(rc["ticks"]) == 6
        inf = r["future_outcome"]["reward_inflection_t_us"]
        assert any(t["t_us"] == inf for t in rc["ticks"]), (r["id"], inf)
        assert r["gate_snn"]["decision"] == r["safety_decision"]["decision"]
        stt = raster_status(r)
        assert stt["raster_valid"], (r["id"], stt)
        assert stt["gate_snn_valid"], (r["id"], stt)
        assert r["meta"]["round"] == ROUND
        # ACCEPT executed params == proposed
        if r["safety_decision"]["decision"] == "ACCEPT" and r["safety_decision"]["correctness"] == "correct":
            assert r["executed_action"]["parameters"] == r["proposed_action"]["parameters"]

    lines = [dumps_exact_json(r, sort_keys=False, ensure_ascii=False) for r in records]
    for i, line in enumerate(lines, 1):
        obj = json.loads(line)
        errs, kind = check_line(obj, f"batch-r43.jsonl:{i}", factory_staging=True)
        rec_errs, rec_warns, rec_kind, rec_id = check_record(obj, f"batch-r43.jsonl:{i}", factory_staging=True)
        print(f"line {i} {obj['id']} kind={kind}/{rec_kind} shape_errs={errs} rec_errs={rec_errs} warns={rec_warns}")
        assert not errs, errs
        assert not rec_errs, rec_errs
        assert not rec_warns, rec_warns

    tmp_batch = Path("/tmp/ttf-r43-live-validate.jsonl")
    tmp_batch.write_text("\n".join(lines) + "\n", encoding="utf-8")
    errors, warnings, kinds, n = check_jsonl(
        tmp_batch, tmp_batch.name, seen_ids=set(), staging=FactoryStaging(enabled=True)
    )
    print("check_jsonl", errors, warnings, kinds, n)
    assert not errors and not warnings
    assert n == 5
    counts, findings, blocked = verify_batch_for_frontier(tmp_batch, strict=True)
    print("verify", counts, findings, blocked)
    assert not blocked, findings
    assert counts["failed"] == 0 and counts["inconclusive"] == 0

    # spike_probe --strict
    import subprocess

    proc = subprocess.run(
        [sys.executable, str(ROOT / "pipelines/spike_probe.py"), "--strict", str(tmp_batch)],
        capture_output=True,
        text=True,
    )
    print("spike_probe rc", proc.returncode)
    print(proc.stdout[-2000:] if proc.stdout else "")
    print(proc.stderr[-2000:] if proc.stderr else "")
    assert proc.returncode == 0, proc.stderr

    batch_path = FACTORY / "batch-r43.jsonl"
    notes_path = FACTORY / "NOTES-r43.md"
    if batch_path.exists() or notes_path.exists():
        batch_path = FACTORY / "batch-r43c.jsonl"
        notes_path = FACTORY / "NOTES-r43c.md"
        print("collision ->", batch_path.name)
    payload = "\n".join(lines) + "\n"
    notes = notes_text(records)
    exclusive_write(batch_path, payload)
    exclusive_write(notes_path, notes)
    # re-parse written
    for i, line in enumerate(batch_path.read_text().split("\n"), 1):
        if not line.strip():
            continue
        json.loads(line)
    print("WROTE", batch_path, notes_path, "bytes", batch_path.stat().st_size)
    print("domains", domains)


if __name__ == "__main__":
    main()
