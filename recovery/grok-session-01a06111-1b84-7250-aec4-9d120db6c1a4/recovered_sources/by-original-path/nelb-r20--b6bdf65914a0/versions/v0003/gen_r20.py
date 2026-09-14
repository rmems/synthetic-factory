#!/usr/bin/env python3
"""Generate NELB round-20 research-only bridge pairs (do not write outputs/raw/)."""

from __future__ import annotations

import json
import math
import random
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

OUT_DIR = Path("/tmp/nelb-r20")
BATCH = OUT_DIR / "batch-r20.jsonl"
NOTES = OUT_DIR / "NOTES-r20.md"
PIPELINES = Path("/home/raulmc/rmems/synthetic-factory/pipelines")
sys.path.insert(0, str(PIPELINES))

GENERATED_AT = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

RIGHTS = {
    "provider": "SpaceXAI/xAI",
    "model": "grok-4.6",
    "channel": "consumer",
    "subscription_plan": "SuperGrok Heavy",
    "generation_surface": "SuperGrok Heavy chat",
    "generated_at": GENERATED_AT,
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
RIGHTS_KEYS = (
    "provider",
    "model",
    "channel",
    "subscription_plan",
    "generation_surface",
    "generated_at",
    "intended_use",
    "project_training_policy",
    "research_retention_status",
    "research_evaluation_status",
    "redistribution_status",
    "provider_training_status",
    "weight_publication_status",
    "status_basis",
    "linear_issue",
)

HIDDEN = {
    "thought",
    "thoughts",
    "reasoning",
    "chain_of_thought",
    "hidden_thought",
    "hidden_reasoning",
    "scratchpad",
    "scratch",
    "internal_monologue",
    "private_reasoning",
    "inner_monologue",
}


def meta_common(**extra):
    m = {
        "round": 20,
        "factory": "neuromorphic-event-language-bridge",
        "generator": "grok-4.6",
        "run_label": "2026-09-02-final-heavy",
        "rights": dict(RIGHTS),
    }
    m.update(extra)
    return m


def make_raster(
    *,
    neurons: int,
    mean_rate_hz: float,
    window_ms: float,
    seed: int,
    source: str,
    target: str,
    table: list,
    third_factor: dict,
    channel_prefix: str,
    anchor: str,
):
    window_s = window_ms / 1000.0
    spikes = int(round(neurons * mean_rate_hz * window_s))
    window_us = int(round(window_ms * 1000))
    rng = random.Random(seed)
    n_active = min(neurons, spikes)
    extra = spikes - n_active
    counts = [1] * n_active + [0] * (neurons - n_active)
    for i in range(extra):
        counts[i % n_active] += 1

    excerpt = []
    for nid, c in enumerate(counts):
        if c == 0:
            continue
        first_max = window_us - 1100 * (c - 1) - 250
        t = rng.randint(120, max(120, first_max))
        times = [t]
        for k in range(1, c):
            min_t = times[-1] + 1100
            slack = window_us - 1100 * (c - 1 - k) - 80
            hi = min(slack, times[-1] + rng.choice([1300, 1800, 2400, 3700, 5200, 7400]))
            if hi < min_t:
                hi = min_t
            if min_t > window_us:
                raise RuntimeError(f"placement overflow neuron {nid}")
            t2 = rng.randint(min_t, hi) if hi > min_t else min_t
            t2 = min(t2, window_us)
            times.append(t2)
        base = 1.15 + 0.7 * rng.random()
        for i, tu in enumerate(times):
            noise = 0.96 + 0.08 * rng.random()
            amp = round(base * (0.82**i) * noise, 3)
            excerpt.append(
                {
                    "t_us": int(tu),
                    "neuron_id": nid,
                    "amplitude": amp,
                    "channel": f"{channel_prefix}{nid:02d}",
                }
            )
    excerpt.sort(key=lambda e: (e["t_us"], e["neuron_id"]))

    by_n = defaultdict(list)
    for e in excerpt:
        by_n[e["neuron_id"]].append(e["t_us"])
    isis_ms = []
    for nid, ts in by_n.items():
        ts = sorted(ts)
        for a, b in zip(ts, ts[1:]):
            gap = b - a
            if gap < 1000:
                raise RuntimeError(f"refractory fail n{nid} {gap} us")
            isis_ms.append(gap / 1000.0)

    edges = [1.0, 2.0, 4.0, 8.0, 16.0, float(window_ms) + 1e-9]
    counts_h = [0] * (len(edges) - 1)
    for isi in isis_ms:
        if isi < 1.0 - 1e-12:
            raise RuntimeError(f"ISI {isi} < 1 ms")
        placed = False
        for i in range(len(edges) - 1):
            if edges[i] <= isi < edges[i + 1]:
                counts_h[i] += 1
                placed = True
                break
        if not placed:
            counts_h[-1] += 1
    hist = []
    for i, c in enumerate(counts_h):
        if c <= 0:
            continue
        hi = window_ms if i == len(counts_h) - 1 else edges[i + 1]
        hist.append({"lo_ms": edges[i], "hi_ms": hi, "count": c})
    identity_n = spikes - len(by_n)
    if sum(x["count"] for x in hist) != identity_n:
        raise RuntimeError(
            f"ISI identity {sum(x['count'] for x in hist)} != {identity_n}"
        )
    if len(excerpt) != spikes:
        raise RuntimeError("excerpt/spikes mismatch")

    energy_pJ = spikes * 23
    energy_uJ = spikes * 23e-6
    return {
        "window_ms": float(window_ms),
        "window_s": float(window_s),
        "neurons": neurons,
        "mean_rate_hz": float(mean_rate_hz),
        "spikes": spikes,
        "energy_pJ": energy_pJ,
        "energy_uJ": energy_uJ,
        "energy_model": "Loihi-2-class 4-core 23 pJ/spike",
        "excerpt": excerpt,
        "excerpt_amplitude_units": "normalized_membrane",
        "excerpt_is_full_window": True,
        "refractory_rule_ms": 1.0,
        "isi_histogram": hist,
        "isi_source": "full_window_per_neuron_isi",
        "isi_count_identity": {
            "spikes": spikes,
            "distinct_active_neurons": len(by_n),
            "isi_total": identity_n,
        },
        "anchor": anchor,
        "seed_note": f"MT19937 seed {seed}; per-neuron id order; gap-constrained times; amplitude adaptation 0.82**k plus noise",
        "routing": {
            "source": source,
            "target": target,
            "table": table,
            "third_factor": third_factor,
        },
    }


def ev(t_rel_ms, channel, amplitude, **extra):
    rec = {
        "t_rel_ms": float(t_rel_ms),
        "channel": channel,
        "amplitude": float(amplitude),
    }
    rec.update(extra)
    return rec


def assert_stream(events, min_n=5, max_n=40):
    if not (min_n <= len(events) <= max_n):
        raise RuntimeError(f"event count {len(events)} not in {min_n}-{max_n}")
    last = -1.0
    last_ch = {}
    for e in events:
        if "t_ms" in e:
            raise RuntimeError("t_ms alias forbidden this round")
        t = e["t_rel_ms"]
        if not math.isfinite(t) or not math.isfinite(e["amplitude"]):
            raise RuntimeError("non-finite")
        if not e["channel"]:
            raise RuntimeError("empty channel")
        if t <= last:
            raise RuntimeError("non-strict t_rel_ms")
        last = t
        prev = last_ch.get(e["channel"])
        if prev is not None and (t - prev) < 0.8:
            raise RuntimeError(f"refractory {e['channel']} {t-prev}")
        last_ch[e["channel"]] = t


def reward(total, components, notes):
    s = 0.0
    out = {
        "aggregation": "unweighted sum of the named scalar components; two-decimal components; total = exact sum",
        "rounding_decimals": 2,
    }
    for k, v in components:
        out[k] = v
        s += v
    out["total"] = total
    if abs(s - total) > 1e-12:
        raise RuntimeError(f"reward {s} != {total}")
    out["notes"] = notes
    return out


def gate_pop(name, neurons, threshold, mean_rate_hz, window_s, **extra):
    spikes = int(round(neurons * mean_rate_hz * window_s))
    d = {
        "name": name,
        "neurons": neurons,
        "threshold": threshold,
        "mean_rate_hz": float(mean_rate_hz),
        "spikes": spikes,
    }
    d.update(extra)
    return d


def gc_check(name, neurons, mean_rate_hz, window_ms):
    window_s = window_ms / 1000.0
    spikes = int(round(neurons * mean_rate_hz * window_s))
    return {
        "check": name,
        "neurons": neurons,
        "mean_rate_hz": float(mean_rate_hz),
        "window_ms": float(window_ms),
        "window_s": float(window_s),
        "spikes": spikes,
    }


def gate_compute(checks):
    total = sum(c["spikes"] for c in checks)
    return {
        "per_check": checks,
        "total_spikes": total,
        "total_energy_pJ": total * 23,
        "total_energy_uJ": total * 23e-6,
        "model": "spikes = round(neurons * mean_rate_hz * window_s); 23 pJ/spike",
    }


# ---------------------------------------------------------------------------
# Record 061 — laser Doppler vibrometry, designed, MODIFY
# ---------------------------------------------------------------------------
def rec_061():
    raster = make_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=40.0,
        seed=20260961,
        source="kg4.ldv.tip_a",
        target="mossgill.flap_core",
        table=[
            {"from": "doppler_shift", "to": "tip_velocity_estimator", "weight": 1.40},
            {"from": "campbell_margin", "to": "islanding_interlock", "weight": 1.15},
            {"from": "housing_scada", "to": "rated_mw_advocate", "weight": 0.45},
        ],
        third_factor={
            "modulator": "na.tip_flap_salience",
            "tau_e_s": 1.6,
            "tau_e_ms": 1600.0,
            "eligibility": "pre-post coincidence on flap synapses; the modulator enables potentiation only while reconstructed tip velocity and remaining Campbell margin are co-active inside tau_e",
        },
        channel_prefix="ldv.n",
        anchor="KG-4 LDV 40 ms frame at f_d 12.50 kHz (t_s 840); first flap-band trip sample",
    )
    w_s = 0.04
    events = [
        ev(0.0, "unit.mw", 2.30, code="MW_RATED", units="MW", note="Mossgill KG-4 Kaplan on 2.30 MW rated"),
        ev(60000.0, "rpm.n", 187.5, code="RPM", units="rpm", note="grid-tied sync; 187.5 rpm"),
        ev(120000.0, "blade.n", 8.0, code="BLADES", units="count"),
        ev(180000.0, "flap.f", 25.00, code="FLAP_HZ", units="Hz", note="8*187.5/60=25.00 blade-pass; 1st flap sits at 27.00 Hz"),
        ev(240000.0, "ldv.lam", 800.0, code="LAMBDA_NM", units="nm"),
        ev(300000.0, "gate.pos", 100.0, code="WICKET_PCT", units="pct"),
        ev(360000.0, "ldv.fd", 4.20, code="FD_KHZ", units="kHz"),
        ev(420000.0, "ldv.v", 1.68, code="V_MM_S", units="mm_s", note="800e-9*4200/2=0.00168 m/s"),
        ev(480000.0, "scada.v", 1.80, code="HOUSING_MM_S", units="mm_s", note="under 2.00 housing alarm"),
        ev(540000.0, "ops.island", 1.0, code="ARMED", units="bool", note="night islanding overspeed to 108 percent"),
        ev(600000.0, "over.pct", 108.0, code="TEST_PCT", units="pct"),
        ev(660000.0, "camp.mgn", 8.00, code="PCT_SPEED", units="pct", note="(202.5-187.5)/187.5=0.080"),
        ev(840000.0, "ldv.fd", 12.50, code="FD_TRIP", units="kHz", note="raster sidecar is this 40 ms frame"),
        ev(840001.2, "ldv.burst", 5.00, code="V_MM_S", units="mm_s", note="tip velocity burst"),
        ev(840002.4, "ldv.burst", 4.10, code="V_MM_S", units="mm_s", note="same-channel 1.2 ms; adapted 0.82x plus noise"),
        ev(840003.7, "ldv.burst", 3.36, code="V_MM_S", units="mm_s", note="third burst 1.3 ms; adapted"),
        ev(846000.0, "v.recon", 5.00, code="V_MM_S", units="mm_s", note="800e-9*12500/2=0.00500 m/s exact"),
        ev(852000.0, "camp.mgn", 8.00, code="PCT_SPEED", units="pct", note="8.00 vs 12.00 floor"),
        ev(858000.0, "ops.prop", 1.0, code="KEEP_RATED", units="bool", note="night operator: housing is quiet, run the islanding test"),
        ev(912000.0, "gate.ldv", 1.0, code="MODIFY", units="decision"),
        ev(924000.0, "gate.cmd", 72.0, code="WICKET_PCT", units="pct"),
        ev(936000.0, "hold.cmd", 1.0, code="ISLAND_HOLD", units="bool"),
        ev(1800000.0, "ldv.fd", 8.00, code="FD_KHZ", units="kHz"),
        ev(1860000.0, "v.recon", 3.20, code="V_MM_S", units="mm_s", note="800e-9*8000/2=0.00320 m/s"),
        ev(2016000.0, "hold.floor", 1.0, code="T18MIN", units="bool", note="936 s + 1080 s hydraulic settle"),
        ev(2040000.0, "oil.T", 41.0, code="HYD_C", units="C"),
        ev(2100000.0, "camp.mgn", 8.00, code="PCT_SPEED", units="pct", note="rpm still 187.5 on grid; coincidence still at 108 percent"),
        ev(2160000.0, "spd.cap", 80.0, code="RESTORE_CAP", units="pct"),
        ev(2220000.0, "gate.exec", 1.0, code="ACCEPT", units="decision", note="companion t2: 72 percent gate plus islanding hold executed"),
        ev(2280000.0, "gate.pos", 72.0, code="WICKET_PCT", units="pct"),
        ev(2340000.0, "v.recon", 3.12, code="V_MM_S", units="mm_s"),
        ev(2400000.0, "unit.mw", 1.656, code="MW_NOW", units="MW", note="0.72*2.30=1.656"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r20-061-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "MG-LDV-2026-0421",
            "domain": "ldv_kaplan_flap_hold",
            "setting": "Mossgill Hydro, unit KG-4, 2.30 MW Kaplan (invented). Fiber LDV (800.0 nm) on blade-A tip; housing accelerometer is the SCADA SoT. Night islanding overspeed to 108 percent is armed. Invented plant; designed campaign. Not MEMS housing array (r17 KT-6), not fluxgate (r5), not FBG strain (r13).",
            "observables_at_decision": {
                "lambda_nm": 800.0,
                "f_d_kHz": 12.50,
                "v_recon_mm_s": 5.00,
                "housing_scada_mm_s": 1.80,
                "rpm": 187.5,
                "blade_pass_Hz": 25.00,
                "flap_Hz": 27.00,
                "remaining_campbell_pct": 8.00,
                "wicket_pct": 100.0,
            },
            "margin_authority": "KG-4 islanding SOP rev C: if reconstructed tip velocity >= 4.00 mm/s AND remaining Campbell percent-speed < 12.0, 100 percent gate and islanding overspeed are both forbidden even if the housing accelerometer is still under 2.00 mm/s",
        },
        "proposed_action": {
            "actor": "night operator, citing a quiet housing channel and a committed islanding slot",
            "summary": "keep 100 percent wicket gate and run the 108 percent islanding overspeed; treat the LDV tip channel as a noisy optical spare",
            "basis_claimed": "SCADA housing is 1.80 mm/s, under the 2.00 mm/s alarm; unit is grid-tied at 187.5 rpm",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Islanding is refused, not the unit. SOP rev C is conjunctive: reconstructed tip velocity is 5.00 mm/s (800e-9*12500/2, serialized) and remaining Campbell margin is 8.00 percent-speed ((202.5-187.5)/187.5), both over the 4.00 mm/s / 12.0 percent floors, while housing SCADA still reads 1.80. Ordered: hold the islanding breaker, drop wicket gate to 72 percent (grid-tied rpm stays 187.5), hold 18 min for hydraulic oil, then restore only to 80 percent until v.recon < 3.00 mm/s. A quiet housing accelerometer cannot substitute for the tip LDV reconstruction.",
            "threshold": "v_recon_mm_s>=4.00 AND remaining_campbell_pct<12.0 => forbid 100 percent gate and islanding",
            "stated_residuals": "72 percent gate costs 0.644 MW tonight; coincidence at 202.5 rpm is unchanged while grid-tied; speckle dropout that could fake a quiet tip is unwritten",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 912: islanding hold latched, wicket 100 -> 72 percent; v.recon 5.00 -> 3.20 by t_s 1860",
            "tool": "kg4-ldv-flap-gate-cli",
            "observation": "breaker stay-latched; hydraulic oil 41 C at the 18 min floor; reconstructed velocity 5.00 -> 3.20 mm/s; housing stayed 1.80",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 540.0, "event": "islanding overspeed armed"},
                {"t_s": 840.0, "event": "LDV f_d 12.50 kHz flap-band trip; raster frame captured"},
                {"t_s": 852.0, "event": "remaining Campbell 8.00 percent-speed vs 12.0 floor"},
                {"t_s": 912.0, "event": "MODIFY: 72 percent gate plus islanding hold"},
                {"t_s": 2016.0, "event": "18 min hydraulic floor in-stream"},
                {"t_s": 2220.0, "event": "companion execution ACCEPT; restore cap 80 percent"},
            ],
            "observed_effects": [
                "tip velocity recomputes from lambda*f_d/2 at every v.recon event",
                "housing SCADA never crossed 2.00 mm/s, so a housing-only head would have ACCEPTed islanding",
                "grid-tied rpm stayed 187.5; 72 percent gate cut hydraulic excitation, not speed",
            ],
            "surprises": [
                "blade-pass at rated already sits 2.00 Hz under 1st flap, so the 108 percent test is a coincidence approach rather than a far overspeed",
            ],
            "new_state": {
                "kg4": "wicket 72 percent, restore cap 80 percent pending v.recon < 3.00",
                "islanding_breaker": "stay-latched",
                "reconstruction_model": "discharged as an on-record calculator, not a referenced envelope",
            },
            "latency_ms": 12000.0,
        },
        "reward_components": reward(
            0.41,
            [
                ("ldv_reconstruction", 0.14),
                ("conjunctive_campbell", 0.12),
                ("housing_nonsubstitution", 0.10),
                ("islanding_hold", 0.07),
                ("mw_deferral_cost", -0.02),
            ],
            "scored for refusing islanding on a recomputable tip velocity while housing SCADA looked quiet; mw_deferral_cost prices the 72 percent gate",
        ),
        "meta": meta_common(
            tags=["MODIFY", "ldv-kaplan", "serialized-reconstruction", "operational-companion"],
            distillation_note="LDV gate: serialized lambda*f_d/2 plus remaining Campbell beats a quiet housing accelerometer; companion t2 is the 72 percent gate / islanding-hold execution, not a governance vote",
        ),
    }
    traj2 = {
        "id": "nelb-r20-061-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "MG-LDV-2026-0421-exec",
            "domain": "wicket_hold_execution",
            "setting": "Same KG-4 after the MODIFY. This companion is the operational 72 percent gate, islanding stay-latch, and 80 percent restore cap, not a second policy vote.",
            "observables_at_decision": {
                "wicket_cmd_pct": 72.0,
                "islanding_hold": True,
                "v_recon_mm_s": 5.00,
                "oil_C": 38.0,
            },
        },
        "proposed_action": {
            "actor": "unit controller following the MODIFY",
            "summary": "execute 72 percent wicket and islanding hold, then restore only to 80 percent when v.recon < 3.00 after the 18 min oil floor",
            "basis_claimed": "MODIFY requirements are fully specified and in-envelope for the wicket servos",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "The execution envelope is intact: wicket slew 2.1 percent/s is under 3.0, oil 38 C is under 55, islanding stay-latch is already true, and the restore cap is 80 percent not 100. ACCEPT the sequence. Do not re-arm islanding tonight; 80 percent is the cap until v.recon < 3.00 mm/s.",
            "threshold": "slew_pct_s<=3.0 AND oil_C<=55 AND restore_cap_pct=80",
        },
        "executed_action": {
            "summary": "wicket 72 percent latched at t_s 924; islanding hold; restore cap 80 percent at t_s 2160 after v.recon 3.20",
            "tool": "kg4-wicket-exec",
            "observation": "no breaker open; mw 1.656; speed still 187.5 rpm",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 924.0, "event": "wicket 72 percent latched"},
                {"t_s": 936.0, "event": "islanding hold latched"},
                {"t_s": 2016.0, "event": "18 min hydraulic floor"},
                {"t_s": 2220.0, "event": "companion ACCEPT; restore cap 80 percent"},
            ],
            "observed_effects": [
                "v 5.00 -> 3.20 mm/s without leaving grid-tied rpm",
                "restore stopped at 80 percent as capped; 100 percent not re-entered",
            ],
            "new_state": {"wicket_pct": 72.0, "restore_cap_pct": 80.0},
            "latency_ms": 12000.0,
        },
        "reward_components": reward(
            0.33,
            [
                ("envelope_respect", 0.12),
                ("wicket_72", 0.10),
                ("restore_cap_80", 0.08),
                ("islanding_not_rearmed", 0.05),
                ("hold_time_cost", -0.02),
            ],
            "operational execution gate: the companion does the wicket cut rather than re-arguing the LDV call",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "wicket-hold"]),
    }
    return {
        "id": "nelb-r20-061",
        "spike_events": events,
        "language_view": {
            "description": "Fiber LDV on Mossgill KG-4 Kaplan tip. f_d 12.50 kHz reconstructs 5.00 mm/s while housing SCADA still reads 1.80; remaining Campbell margin is 8.00 percent-speed vs a 12.0 floor with a 108 percent islanding test armed. The gate MODIFYs to 72 percent wicket plus islanding hold; a companion execution ACCEPT runs the cut and caps restore at 80 percent. The velocity model is serialized so every v.recon amplitude recomputes from lambda*f_d/2.",
            "trajectory": traj,
            "trajectory_wicket_hold_execution": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "ldv.fd / ldv.burst / v.recon": "Doppler physics and serialized tip velocity",
                "scada.v": "denial channel: quiet housing accelerometer",
                "flap.f / camp.mgn / over.pct": "Campbell coincidence arithmetic",
                "ops.prop / gate.ldv / gate.exec": "proposal, MODIFY, companion ACCEPT",
                "gate.cmd / hold.cmd / spd.cap": "execution channels for the operational companion",
            },
            "temporal_motifs": [
                "housing-quiet while tip-sick: scada.v 1.80 adjacent to v.recon 5.00",
                "reconstruction as event: v.recon 5.00 equals 800e-9*12500/2 in mm/s",
                "MODIFY then operational ACCEPT: gate.ldv at 912 s, gate.exec at 2220 s",
                "adapted tip-velocity triplet at 1.2/1.3 ms encodes the flap-band trip at raster scale",
                "18 min hydraulic floor as hold.floor bookend at 2016 s",
            ],
            "language_to_spike_mapping": "'housing is quiet' = scada.v 1.80; '5.00 mm/s tip' = v.recon; 'forbid islanding' = gate.ldv MODIFY; 'execute the cut' = gate.cmd then companion ACCEPT",
            "why_high_value": "New laser-Doppler-vibrometry family (not r17 MEMS housing array, not r5 fluxgate, not r13 FBG glaze strain, not r7 vestibular). Serializes a tip-velocity reconstruction that a housing accelerometer cannot see. Companion t2 is operational execution, not a governance vote.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 20260961, "stream_note": "stream amplitudes are authored constants (kHz, mm/s, rpm, MW, pct) plus ldv.burst adaptation 0.82**k"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "fiber LDV exists on blades A-H; stream keeps blade A; v.recon keeps 3 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "unit.mw": 60000,
                    "rpm.n": 60000,
                    "blade.n": 60000,
                    "flap.f": 60000,
                    "ldv.lam": 60000,
                    "gate.pos": 60000,
                    "ldv.fd": 60000,
                    "ldv.v": 60000,
                    "scada.v": 60000,
                    "ops.island": 60000,
                    "over.pct": 60000,
                    "camp.mgn": 60000,
                    "ldv.burst": 0.8,
                    "v.recon": 60000,
                    "ops.prop": 60000,
                    "gate.ldv": 60000,
                    "gate.cmd": 60000,
                    "hold.cmd": 60000,
                    "hold.floor": 60000,
                    "oil.T": 60000,
                    "spd.cap": 60000,
                    "gate.exec": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-04-21T02:00:00Z night islanding commit",
            },
            "distillation_targets": [
                "serialized LDV reconstruction head: v = lambda * f_d / 2",
                "conjunctive SOP head: tip velocity AND remaining Campbell, never housing substitution",
                "operational companion: execute the wicket cut without re-opening the flap call",
            ],
        },
        "reconstruction_model": {
            "name": "ldv_tip_velocity_campbell",
            "formula": "v_m_s = lambda_m * f_d_Hz / 2; v_mm_s = 1000 * v_m_s; blade_pass_Hz = n_blade * rpm / 60; n_coin_rpm = flap_Hz / n_blade * 60; remaining_campbell_pct = 100 * (n_coin_rpm / rpm - 1)",
            "parameters": {
                "lambda_m": 800e-9,
                "n_blade": 8.0,
                "rpm": 187.5,
                "flap_Hz": 27.00,
                "v_trip_mm_s": 4.00,
                "campbell_floor_pct": 12.0,
            },
            "worked_example": {
                "f_d_Hz": 12500.0,
                "v_mm_s": 5.00,
                "blade_pass_Hz": 25.00,
                "n_coin_rpm": 202.5,
                "remaining_campbell_pct": 8.00,
                "f_d_hold_Hz": 8000.0,
                "v_hold_mm_s": 3.20,
            },
            "check": "800e-9*12500/2=0.00500; 8*187.5/60=25.00; 27.00/8*60=202.5; (202.5-187.5)/187.5=0.080; 800e-9*8000/2=0.00320",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.04,
            "code": "kg4.ldv_flap_gate",
            "note": "MODIFY accumulator wins: tip-velocity plus Campbell evidence overpower the rated-MW advocate",
            "populations": [
                gate_pop("ldv_evidence", 80, 1.4, 50.0, w_s),
                gate_pop("campbell_evidence", 64, 1.1, 31.25, w_s),
                gate_pop("rated_mw_advocate", 48, 0.9, 25.0, w_s),
                gate_pop("modify_accumulator", 96, 1.6, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                gc_check("kg4.ldv_scorer", 128, 31.25, 40.0),
                gc_check("kg4.campbell_projector", 80, 25.0, 40.0),
            ]
        ),
        "meta": meta_common(
            id="nelb-r20-061",
            clock_domain="mg-ldv-campaign-relative-ms-t0-2026-04-21T02:00:00Z",
            tags=["ldv-kaplan", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 062 — THz-TDS radome coupon, hil, REJECT (vendor-only THz SoT)
# ---------------------------------------------------------------------------
def rec_062():
    raster = make_raster(
        neurons=25,
        mean_rate_hz=40.0,
        window_ms=32.0,
        seed=20260962,
        source="thzhil4.tds.echo",
        target="thornwick.moisture_core",
        table=[
            {"from": "gravimetric_mass", "to": "moisture_estimator", "weight": 1.45},
            {"from": "coupon_micrometer", "to": "thickness_witness", "weight": 1.10},
            {"from": "vendor_tof", "to": "fly_advocate", "weight": 0.40},
        ],
        third_factor={
            "modulator": "da.moisture_index_error",
            "tau_e_s": 0.8,
            "tau_e_ms": 800.0,
            "eligibility": "pre-post coincidence on moisture synapses; the modulator enables potentiation only while gravimetric percent and implied n are co-active inside tau_e",
        },
        channel_prefix="thz.n",
        anchor="THz-HIL-4 32 ms frame at wet TOF 108.00 ps (t_s 21660); vendor still holds 90.00 ps last-good",
    )
    w_s = 0.032
    events = [
        ev(0.0, "hil.lock", 1.0, code="HIL_LOCK", units="bool", note="Thornwick GH-9 humidity chamber; cyanate-ester radome coupon"),
        ev(60000.0, "chamber.rh", 85.0, code="RH_PCT", units="pct"),
        ev(120000.0, "chamber.T", 40.0, code="C", units="C"),
        ev(180000.0, "c.light", 0.300, code="MM_PER_PS", units="mm_ps"),
        ev(240000.0, "coup.d", 9.00, code="MM", units="mm", note="plant-owned micrometer; vendor cannot write"),
        ev(300000.0, "m0.g", 12.00, code="G", units="g", note="dry coupon mass"),
        ev(360000.0, "thz.n0", 1.50, code="N_DRY", units="1"),
        ev(420000.0, "k.m", 0.050, code="DN_PER_PCT", units="1"),
        ev(480000.0, "tg.C", 78.0, code="TG_C", units="C"),
        ev(540000.0, "thz.dt", 90.00, code="PS", units="ps", note="2*1.50*9.00/0.300=90.00 dry"),
        ev(600000.0, "soak.start", 1.0, code="SOAK", units="bool"),
        ev(22200000.0, "soak.6h", 1.0, code="SOAK_END", units="bool", note="600 s + 21600 s"),
        ev(22260000.0, "m.now", 12.72, code="G", units="g", note="gravimetric; vendor cannot write the scale"),
        ev(22320000.0, "thz.dt", 90.00, code="PS_FROZEN", units="ps", note="CloudCoat last-good still 90.00; raster is the gravimetric frame"),
        ev(22320001.2, "thz.echo", 1.50, code="N_FROZEN", units="1", note="vendor n freeze"),
        ev(22320002.4, "thz.echo", 1.23, code="N_FROZEN", units="1", note="1.2 ms; adapted"),
        ev(22320003.7, "thz.echo", 1.01, code="N_FROZEN", units="1", note="1.3 ms; adapted"),
        ev(22380000.0, "moist.pct", 6.00, code="PCT", units="pct", note="(12.72-12.00)/12.00=0.060"),
        ev(22440000.0, "n.recon", 1.80, code="N", units="1", note="1.50+0.050*6.00=1.80"),
        ev(22500000.0, "dt.impl", 108.00, code="PS", units="ps", note="2*1.80*9.00/0.300=108.00; CloudCoat does not show this"),
        ev(22560000.0, "d.app", 10.80, code="MM", units="mm", note="if frozen n=1.50 were applied to 108 ps"),
        ev(22620000.0, "vend.acl", 1.0, code="WRITE", units="bool", note="CloudCoat write-ACL then freeze"),
        ev(22680000.0, "ops.prop", 1.0, code="FLY", units="bool"),
        ev(22740000.0, "gate.thz", 1.0, code="REJECT", units="decision"),
        ev(22800000.0, "bake.cmd", 1.0, code="BAKE", units="bool"),
        ev(22860000.0, "bake.T", 60.0, code="C", units="C", note="60 not 80; Tg 78 C"),
        ev(37260000.0, "bake.floor", 1.0, code="T4H", units="bool", note="22860 s + 14400 s"),
        ev(37320000.0, "m.now", 12.05, code="G", units="g"),
        ev(37380000.0, "moist.pct", 0.42, code="PCT", units="pct", note="(12.05-12.00)/12.00=0.00417 ~ 0.42 after rounding two decimals on (12.05-12.00)/12*100"),
        ev(37440000.0, "n.recon", 1.52, code="N", units="1"),
        ev(37500000.0, "gate.exec", 1.0, code="MODIFY", units="decision", note="companion: 60 C bake not 80 C"),
        ev(37560000.0, "coup.d", 9.00, code="MM", units="mm"),
    ]
    assert_stream(events)
    # moisture after bake: (12.05-12.00)/12.00*100 = 0.4167 -> author 0.42

    traj = {
        "id": "nelb-r20-062-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "TW-THZ-2026-0318",
            "domain": "thz_tds_radome_moisture",
            "setting": "Thornwick Composites, hangar GH-9, coupon stand THz-HIL-4 in an 85 percent RH chamber (invented). CloudCoat is the only THz-TDS SoT (vendor write-ACL). Plant-owned micrometer and gravimetric scale do not ride the CloudCoat bus. Hardware-in-the-loop: humidity chamber plus coupon, not a flying radome. Not QEPAS (r19), not CRDS (r15), not CEMS (r04), not Raman DTS (r14).",
            "observables_at_decision": {
                "d_mm": 9.00,
                "m0_g": 12.00,
                "m_now_g": 12.72,
                "moisture_pct": 6.00,
                "n_recon": 1.80,
                "dt_implied_ps": 108.00,
                "dt_vendor_ps": 90.00,
                "n_vendor": 1.50,
            },
            "margin_authority": "GH-9 flight-release SOP rev A: if gravimetric moisture >= 4.00 percent OR implied n >= 1.70, flight-release is forbidden even if CloudCoat still reports the dry 90.00 ps last-good. CloudCoat is vendor-only; no independent THz exists.",
        },
        "proposed_action": {
            "actor": "hangar lead, citing a green CloudCoat dashboard and a morning slot",
            "summary": "release the radome; 9.00 mm coupon thickness is unchanged and CloudCoat n is still 1.50",
            "basis_claimed": "vendor THz last-good is the dry 90.00 ps / 1.50 n pair; micrometer still 9.00 mm",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Flight-release is refused. CloudCoat is the only THz and it froze 90.00 ps after a write-ACL, but the plant gravimetric scale the vendor cannot write moved 12.00 -> 12.72 g, moisture 6.00 percent ((12.72-12.00)/12.00). Implied n is 1.50+0.050*6.00=1.80 and implied TOF is 2*1.80*9.00/0.300=108.00 ps. SOP rev A is conjunctive on moisture OR implied n; both fire. A 9.00 mm micrometer cannot substitute for moisture, and a vendor-only THz cannot clear a scale the vendor cannot write. Ordered: no fly, 4 h bake at 60 C (Tg 78 C), re-weigh, do not restore CloudCoat as SoT.",
            "threshold": "moisture_pct>=4.00 OR n_implied>=1.70 => forbid flight-release",
            "stated_residuals": "no independent THz is installed, so n is implied from gravimetric plus k_m rather than measured; a T-dependent k_m that could hide 6 percent inside a 40 C soak is unwritten",
        },
        "executed_action": {
            "summary": "REJECT at t_s 22740: fly slot cancelled; bake 60 C latched",
            "tool": "tw-thz-moisture-gate-cli",
            "observation": "CloudCoat still 90.00 ps; scale 12.72 g; coupon not scrapped",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 600.0, "event": "humidity soak start"},
                {"t_s": 22200.0, "event": "6 h soak end; mass 12.72 g"},
                {"t_s": 22500.0, "event": "implied TOF 108.00 ps vs vendor 90.00"},
                {"t_s": 22740.0, "event": "REJECT flight-release"},
                {"t_s": 37260.0, "event": "4 h bake floor in-stream"},
                {"t_s": 37500.0, "event": "companion MODIFY: 60 C not 80 C executed"},
            ],
            "observed_effects": [
                "moisture recomputes from (m-m0)/m0 at every moist.pct event",
                "vendor TOF never left 90.00 ps, so a CloudCoat-only head would have ACCEPTed fly",
                "micrometer stayed 9.00 mm; thickness is not a moisture witness",
            ],
            "surprises": [
                "implied 108.00 ps is a reconstruction the vendor bus cannot display; the teaching object is the absence of CloudCoat co-movement with the scale",
            ],
            "new_state": {
                "radome": "grounded pending re-weigh < 4.00 percent",
                "cloudcoat": "demoted; not SoT",
                "bake": "60 C latched",
            },
            "latency_ms": 18000.0,
        },
        "reward_components": reward(
            0.43,
            [
                ("gravimetric_reconstruction", 0.14),
                ("vendor_only_thz_refusal", 0.12),
                ("implied_n_identity", 0.10),
                ("micrometer_nonsubstitution", 0.09),
                ("slot_deferral_cost", -0.02),
            ],
            "scored for refusing flight-release on a recomputable gravimetric moisture while vendor-only THz looked dry",
        ),
        "meta": meta_common(
            tags=["REJECT", "thz-tds", "vendor-only-sot", "serialized-reconstruction", "operational-companion"],
            distillation_note="THz-TDS gate: vendor-only TOF cannot clear a plant scale; implied n and TOF are serialized from moisture; companion t2 is the Tg-limited bake, not a governance vote",
        ),
    }
    traj2 = {
        "id": "nelb-r20-062-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "TW-THZ-2026-0318-exec",
            "domain": "coupon_bake_execution",
            "setting": "Same THz-HIL-4 after the REJECT. This companion is the operational 4 h bake at 60 C (not 80 C), not a second fly vote.",
            "observables_at_decision": {
                "bake_cmd": True,
                "tg_C": 78.0,
                "proposed_bake_C": 80.0,
                "m_now_g": 12.72,
            },
        },
        "proposed_action": {
            "actor": "chamber tech following the REJECT, proposing 80 C to finish before the afternoon slot",
            "summary": "bake at 80 C for 2 h instead of 60 C for 4 h",
            "basis_claimed": "faster dry-out; coupon is already wet",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "80 C is refused. Tg is 78 C; 80 C is over Tg and can freeze moisture into a skin. Ordered: 60 C for 4 h, re-weigh, re-THz only as a witness not SoT. The 4 h floor is in the stream. Do not restore CloudCoat as SoT even if n.recon returns to 1.52.",
            "threshold": "bake_C < tg_C - 15 AND bake_s >= 14400",
        },
        "executed_action": {
            "summary": "60 C bake latched at t_s 22860; 4 h floor at t_s 37260; mass 12.72 -> 12.05 g",
            "tool": "tw-hil-bake-exec",
            "observation": "no 80 C; moist 6.00 -> 0.42 percent; CloudCoat still demoted",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 22800.0, "event": "bake command"},
                {"t_s": 22860.0, "event": "60 C latched (80 C refused)"},
                {"t_s": 37260.0, "event": "4 h bake floor"},
                {"t_s": 37500.0, "event": "companion MODIFY recorded"},
            ],
            "observed_effects": [
                "mass 12.72 -> 12.05 g without crossing Tg",
                "CloudCoat remains demoted after the bake",
            ],
            "new_state": {"bake_C": 60.0, "cloudcoat_sot": False},
            "latency_ms": 18000.0,
        },
        "reward_components": reward(
            0.32,
            [
                ("tg_respect", 0.12),
                ("bake_60_not_80", 0.10),
                ("reweigh_required", 0.08),
                ("coupon_not_scrapped", 0.04),
                ("bake_time_cost", -0.02),
            ],
            "operational execution gate: the companion does the Tg-limited bake rather than re-arguing the fly call",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "tg-limited-bake"]),
    }
    return {
        "id": "nelb-r20-062",
        "spike_events": events,
        "language_view": {
            "description": "HIL THz-TDS coupon at Thornwick GH-9. CloudCoat (vendor-only THz) freezes 90.00 ps / n=1.50 after a write-ACL while the plant scale the vendor cannot write moves 12.00 -> 12.72 g (moisture 6.00 percent). Implied n 1.80 and implied TOF 108.00 ps are serialized from the scale. The gate REJECTS flight-release; companion t2 MODIFYs a 60 C bake (not 80 C, Tg 78 C) with a 4 h floor in the stream.",
            "trajectory": traj,
            "trajectory_bake_tg_limit": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "m0.g / m.now / moist.pct": "gravimetric physics; serialized moisture",
                "n.recon / dt.impl": "implied optical index and TOF from moisture plus k_m",
                "thz.dt / thz.echo / vend.acl": "vendor-only THz freeze after write-ACL",
                "coup.d": "micrometer; unwritable but not a moisture witness",
                "ops.prop / gate.thz / gate.exec": "fly proposal, REJECT, companion MODIFY",
                "bake.cmd / bake.T / bake.floor": "Tg-limited bake companion",
            },
            "temporal_motifs": [
                "vendor-dry while scale-wet: thz.dt 90.00 adjacent to moist.pct 6.00",
                "reconstruction as event: n.recon 1.80 equals 1.50+0.050*6.00; dt.impl 108.00 equals 2*1.80*9.00/0.300",
                "REJECT then operational MODIFY: gate.thz at 22740 s, gate.exec at 37500 s",
                "adapted vendor-echo triplet at 1.2/1.3 ms encodes the freeze at raster scale",
                "6 h soak and 4 h bake floors as soak.6h / bake.floor bookends",
            ],
            "language_to_spike_mapping": "'CloudCoat is green' = thz.dt 90.00 last-good; '6 percent wet' = moist.pct; 'implied 108 ps' = dt.impl; 'forbid fly' = gate.thz REJECT; 'bake at 60 not 80' = bake.T then companion MODIFY",
            "why_high_value": "New THz-TDS family (not r19 QEPAS DGA, not r15 CRDS HF, not r14 Raman DTS on BOTDA, not r04 CEMS). First vendor-only THz SoT as a lead REJECT: no independent THz exists; defense rests on a gravimetric scale the vendor cannot write. Companion t2 is operational Tg-limited bake, not a governance vote.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 20260962, "stream_note": "stream amplitudes authored (ps, g, mm, pct, C) plus thz.echo adaptation 0.82**k"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "THz-TDS waveform exists; stream keeps one echo TOF; gravimetric keeps 3 mass points of a 6 h soak",
                "refractory_floors_ms": {
                    "hil.lock": 60000,
                    "chamber.rh": 60000,
                    "chamber.T": 60000,
                    "c.light": 60000,
                    "coup.d": 60000,
                    "m0.g": 60000,
                    "thz.n0": 60000,
                    "k.m": 60000,
                    "tg.C": 60000,
                    "thz.dt": 60000,
                    "soak.start": 60000,
                    "soak.6h": 60000,
                    "m.now": 60000,
                    "thz.echo": 0.8,
                    "moist.pct": 60000,
                    "n.recon": 60000,
                    "dt.impl": 60000,
                    "d.app": 60000,
                    "vend.acl": 60000,
                    "ops.prop": 60000,
                    "gate.thz": 60000,
                    "bake.cmd": 60000,
                    "bake.T": 60000,
                    "bake.floor": 60000,
                    "gate.exec": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-03-18T18:00:00Z HIL soak commit",
            },
            "distillation_targets": [
                "serialized gravimetric moisture head: (m-m0)/m0",
                "implied n and TOF: n=n0+k_m*moisture; dt=2*n*d/c",
                "vendor-only THz refusal on a lead: missing independent THz is sufficient when an unwritable scale already fires",
                "operational companion: Tg-limited bake without re-opening the fly call",
            ],
        },
        "reconstruction_model": {
            "name": "thz_gravimetric_implied_tof",
            "formula": "moisture = (m - m0) / m0; n = n0 + k_m * moisture_pct; dt_ps = 2 * n * d_mm / c_mm_per_ps",
            "parameters": {
                "m0_g": 12.00,
                "d_mm": 9.00,
                "n0": 1.50,
                "k_m": 0.050,
                "c_mm_per_ps": 0.300,
                "moisture_floor_pct": 4.00,
            },
            "worked_example": {
                "m_g": 12.72,
                "moisture_pct": 6.00,
                "n": 1.80,
                "dt_implied_ps": 108.00,
                "dt_vendor_ps": 90.00,
                "d_app_mm": 10.80,
            },
            "check": "(12.72-12.00)/12.00=0.060; 1.50+0.050*6.00=1.80; 2*1.80*9.00/0.300=108.00; 0.300*108/(2*1.50)=10.80",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 32.0,
            "decision_window_s": 0.032,
            "code": "tw.thz_moisture_gate",
            "note": "REJECT accumulator wins: gravimetric moisture plus implied-n evidence overpower the fly advocate; vendor THz is unreachable as SoT",
            "populations": [
                gate_pop("gravimetric_evidence", 80, 1.5, 50.0, w_s),
                gate_pop("implied_n_evidence", 64, 1.2, 31.25, w_s),
                gate_pop("fly_advocate", 40, 0.8, 25.0, w_s),
                gate_pop("reject_accumulator", 80, 1.6, 50.0, w_s),
                {
                    "name": "vendor_thz_admissible",
                    "neurons": 16,
                    "threshold": 12.0,
                    "role": "asymmetric_null_zero_weight",
                    "note": "asymmetric-null: vendor-only THz cannot fire the admissible population",
                },
            ],
        },
        "gate_compute": gate_compute(
            [
                gc_check("tw.moisture_scorer", 100, 50.0, 32.0),
                gc_check("tw.implied_n_scorer", 80, 31.25, 32.0),
            ]
        ),
        "meta": meta_common(
            id="nelb-r20-062",
            clock_domain="tw-thz-hil-relative-ms-t0-2026-03-18T18:00:00Z",
            tags=["thz-tds", "REJECT", "MODIFY", "vendor-only-sot", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 063 — electrical capacitance tomography, simulated, ACCEPT (bounded)
# ---------------------------------------------------------------------------
def rec_063():
    raster = make_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=28.0,
        seed=20260963,
        source="pw4.ect.wall",
        target="polderwick.inventory_core",
        table=[
            {"from": "wall_capacitance", "to": "voidage_estimator", "weight": 1.20},
            {"from": "riser_dp", "to": "inventory_witness", "weight": 1.40},
            {"from": "mft_advocate", "to": "trip_advocate", "weight": 0.50},
        ],
        third_factor={
            "modulator": "ach.inventory_conflict",
            "tau_e_s": 2.2,
            "tau_e_ms": 2200.0,
            "eligibility": "pre-post coincidence on inventory synapses; the modulator enables potentiation only while core voidage and riser dP are co-active inside tau_e",
        },
        channel_prefix="ect.n",
        anchor="PW-4 ECT 28 ms frame at C_wall 1.32 pF (t_s 720); wall voidage 0.92 vs healthy core 0.52",
    )
    w_s = 0.028
    events = [
        ev(0.0, "unit.load", 0.82, code="PU", units="pu", note="Polderwick CFB PW-4 at 0.82 pu"),
        ev(60000.0, "pa.w", 10.00, code="KG_S", units="kg_s"),
        ev(120000.0, "ect.cp", 5.00, code="PF", units="pF", note="packed-bed calibration"),
        ev(180000.0, "ect.cg", 1.00, code="PF", units="pF", note="gas calibration"),
        ev(240000.0, "g.ser", 10.0, code="M_S2", units="m_s2", note="serialized g=10 for the plant model"),
        ev(300000.0, "rho.p", 250.0, code="KG_M3", units="kg_m3"),
        ev(360000.0, "H.riser", 10.0, code="M", units="m"),
        ev(420000.0, "ect.cw", 1.32, code="PF", units="pF"),
        ev(480000.0, "ect.cc", 2.92, code="PF", units="pF"),
        ev(540000.0, "eps.w", 0.92, code="VOID", units="1", note="(5.00-1.32)/4.00=0.92"),
        ev(600000.0, "eps.c", 0.52, code="VOID", units="1", note="(5.00-2.92)/4.00=0.52"),
        ev(720000.0, "ect.cw", 1.32, code="WALL_FRAME", units="pF", note="raster sidecar is this 28 ms frame"),
        ev(720001.1, "ect.ring", 0.92, code="VOID", units="1"),
        ev(720002.3, "ect.ring", 0.75, code="VOID", units="1", note="1.2 ms; adapted"),
        ev(720003.6, "ect.ring", 0.62, code="VOID", units="1", note="1.3 ms; adapted"),
        ev(780000.0, "eps.avg", 0.680, code="VOID", units="1", note="0.60*0.52+0.40*0.92=0.680"),
        ev(840000.0, "dp.recon", 8.00, code="KPA", units="kPa", note="250*10*10*0.320/1000=8.00"),
        ev(900000.0, "dp.kpa", 8.00, code="KPA", units="kPa"),
        ev(960000.0, "ops.prop", 1.0, code="MFT", units="bool", note="board: wall 0.92 looks like an empty riser"),
        ev(1020000.0, "gate.ect", 1.0, code="ACCEPT", units="decision"),
        ev(1080000.0, "pa.cmd", 9.20, code="KG_S", units="kg_s", note="8 percent cut; 10.00-0.80=9.20"),
        ev(1140000.0, "oil.prop", 1.0, code="SUPPORT", units="bool"),
        ev(1200000.0, "gate.scope", 1.0, code="REJECT", units="decision", note="companion: oil-support out of scope"),
        ev(1800000.0, "settle.floor", 1.0, code="T12MIN", units="bool", note="1080 s + 720 s"),
        ev(1860000.0, "ect.cw", 1.56, code="PF", units="pF", note="0.86=(5.00-C)/4.00 => C=1.56"),
        ev(1920000.0, "eps.w", 0.86, code="VOID", units="1", note="0.92-0.075*0.80=0.86"),
        ev(1980000.0, "dp.kpa", 8.40, code="KPA", units="kPa"),
        ev(2040000.0, "eps.c", 0.50, code="VOID", units="1"),
        ev(2100000.0, "pa.w", 9.20, code="KG_S", units="kg_s"),
        ev(2160000.0, "gate.exec", 1.0, code="REJECT", units="decision"),
        ev(2220000.0, "trip.dp", 6.50, code="KPA_FLOOR", units="kPa"),
        ev(2280000.0, "unit.load", 0.78, code="PU", units="pu"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r20-063-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "PW-ECT-2026-0506",
            "domain": "ect_cfb_inventory",
            "setting": "Polderwick Station, CFB PW-4 (invented), simulated 8-electrode ECT on the riser. Wall voidage 0.92 looks empty to an annulus-only head; core 0.52 and dP 8.00 kPa say inventory is intact. Invented plant; simulated campaign. Not clamp-on ultrasonic flow (r18), not LFV (r19), not water-distribution hydraulics (r03), not PMU (r5).",
            "observables_at_decision": {
                "C_wall_pF": 1.32,
                "C_core_pF": 2.92,
                "eps_wall": 0.92,
                "eps_core": 0.52,
                "eps_avg": 0.680,
                "dp_kPa": 8.00,
                "pa_kg_s": 10.00,
            },
            "margin_authority": "PW-4 MFT SOP rev B: master fuel trip if dP < 6.50 kPa OR eps_core > 0.70 (lost inventory / empty core). Wall voidage alone is not a trip. A bounded primary-air cut is in-envelope when dP is inside 6.50-10.0 and eps_core <= 0.70.",
        },
        "proposed_action": {
            "actor": "shift supervisor, citing wall ECT 0.92 as an empty riser",
            "summary": "master fuel trip now; wall looks empty and a trip is cheaper than a slump",
            "basis_claimed": "annulus ECT 0.92 exceeds the informal 0.90 empty-riser folklore; oil-support is available",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "MFT is refused, not the diagnosis. SOP rev B trips on dP OR core voidage, not wall: dP recomputes 250*10*10*0.320=8000 Pa = 8.00 kPa (inside 6.50-10.0) and eps_core is 0.52 (under 0.70). Wall 0.92 is the normal CFB annulus. Ordered bounded ACCEPT: cut primary air 10.00 -> 9.20 kg/s (8 percent), tripwire dP < 6.50 OR eps_core > 0.70, no oil-support, 12 min settle floor. An annulus-only empty-riser head cannot substitute for core ECT plus dP inventory.",
            "threshold": "dp_kPa>=6.50 AND eps_core<=0.70 => MFT forbidden; PA cut 8 percent in-envelope",
            "stated_residuals": "ACCEPT is scoped to this PA cut and this shift; a metal-riser short that collapses C independently of voidage is unwritten; oil-support is out of scope (companion)",
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 1020: PA 10.00 -> 9.20 kg/s; MFT not armed; tripwire latched",
            "tool": "pw4-ect-inventory-gate-cli",
            "observation": "dP 8.00 kPa held; eps_core 0.52; wall later 0.86 after the cut",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 720.0, "event": "wall C 1.32 pF raster frame; eps_wall 0.92"},
                {"t_s": 840.0, "event": "dP reconstruction 8.00 kPa"},
                {"t_s": 1020.0, "event": "bounded ACCEPT: 8 percent PA cut, not MFT"},
                {"t_s": 1800.0, "event": "12 min settle floor in-stream"},
                {"t_s": 1920.0, "event": "eps_wall 0.86 after cut (0.92-0.075*0.80)"},
                {"t_s": 2160.0, "event": "companion REJECT of oil-support"},
            ],
            "observed_effects": [
                "voidage recomputes from (C_p-C)/(C_p-C_g) at every eps event",
                "dP recomputes from rho*g*H*(1-eps_avg) and never left the 6.50-10.0 band",
                "wall 0.92 -> 0.86 after the PA cut; core stayed dense",
            ],
            "surprises": [
                "the folklore 0.90 wall-empty trip would have MFTed a healthy CFB annulus",
            ],
            "new_state": {
                "pw4": "PA 9.20 kg/s, MFT not armed, tripwire live",
                "oil_support": "out of scope",
            },
            "latency_ms": 10000.0,
        },
        "reward_components": reward(
            0.39,
            [
                ("dp_inventory", 0.14),
                ("core_voidage_head", 0.12),
                ("wall_is_not_empty", 0.10),
                ("bounded_pa_cut", 0.05),
                ("tripwire", 0.04),
                ("derate_cost", -0.06),
            ],
            "scored for an earned bounded ACCEPT of an 8 percent PA cut on recomputable inventory while an annulus-only head wanted MFT",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "ect-cfb", "serialized-reconstruction", "bounded-accept", "operational-companion"],
            distillation_note="ECT gate: serialized (C_p-C)/(C_p-C_g) plus dP inventory beats a wall-empty MFT; companion t2 refuses oil-support without re-opening the voidage call",
        ),
    }
    traj2 = {
        "id": "nelb-r20-063-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "PW-ECT-2026-0506-exec",
            "domain": "pa_cut_scope",
            "setting": "Same PW-4 after the bounded ACCEPT. This companion is the operational PA-cut scope: execute 9.20 kg/s, refuse oil-support, not a second inventory vote.",
            "observables_at_decision": {
                "pa_cmd_kg_s": 9.20,
                "oil_proposed": True,
                "dp_kPa": 8.00,
                "eps_core": 0.52,
            },
        },
        "proposed_action": {
            "actor": "boiler operator following the ACCEPT, adding oil-support 'for margin'",
            "summary": "cut PA to 9.20 kg/s and light oil-support at 0.8 t/h",
            "basis_claimed": "oil-support is a standard CFB crutch when wall ECT looks high",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Oil-support is out of scope of the lead ACCEPT. The lead bound is PA 9.20 kg/s plus a dP/core tripwire; oil-support would mask a true inventory loss and is not a substitute control. Execute the PA cut only. Do not re-open the MFT call.",
            "threshold": "scope = PA cut 8 percent AND tripwire; oil_support = out_of_scope",
        },
        "executed_action": {
            "summary": "PA 9.20 kg/s at t_s 1080; oil-support not lit; 12 min settle floor at t_s 1800",
            "tool": "pw4-pa-exec",
            "observation": "eps_wall 0.92 -> 0.86; dP 8.00 -> 8.40 kPa; oil flow 0",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 1080.0, "event": "PA 9.20 kg/s"},
                {"t_s": 1200.0, "event": "oil-support REJECT"},
                {"t_s": 1800.0, "event": "12 min settle floor"},
                {"t_s": 2160.0, "event": "companion REJECT recorded"},
            ],
            "observed_effects": [
                "wall voidage dropped 0.06 without oil",
                "tripwire never fired (dP 8.40, eps_core 0.50)",
            ],
            "new_state": {"pa_kg_s": 9.20, "oil_support": False},
            "latency_ms": 10000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("scope_discipline", 0.14),
                ("pa_only", 0.10),
                ("oil_support_refused", 0.08),
                ("tripwire_held", 0.04),
                ("delay_cost", -0.02),
            ],
            "operational scope gate: the companion refuses oil-support rather than re-arguing the inventory call",
        ),
        "meta": meta_common(tags=["REJECT", "operational-execution", "pa-cut-scope"]),
    }
    return {
        "id": "nelb-r20-063",
        "spike_events": events,
        "language_view": {
            "description": "Simulated 8-electrode ECT on Polderwick CFB PW-4. Wall voidage 0.92 looks like an empty riser while core 0.52 and dP 8.00 kPa (250*10*10*0.320) say inventory is intact. The gate ACCEPTs a bounded 8 percent primary-air cut (10.00 -> 9.20 kg/s) with a dP/core tripwire, not an MFT. Companion t2 REJECTS oil-support as out of scope. Voidage and dP are serialized so every eps and dp.recon amplitude recomputes from C and (1-eps_avg).",
            "trajectory": traj,
            "trajectory_oil_support_refusal": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "ect.cw / ect.cc / eps.w / eps.c": "ECT physics; serialized voidage (C_p-C)/(C_p-C_g)",
                "dp.recon / dp.kpa": "inventory witness from rho*g*H*(1-eps_avg)",
                "ops.prop / gate.ect": "MFT proposal vs bounded ACCEPT",
                "pa.cmd / oil.prop / gate.scope / gate.exec": "operational PA-cut companion and oil-support refusal",
            },
            "temporal_motifs": [
                "wall-empty while core-healthy: eps.w 0.92 adjacent to eps.c 0.52 and dp.recon 8.00",
                "reconstruction as event: eps.w 0.92 equals (5.00-1.32)/4.00; dp.recon 8.00 equals 250*10*10*0.320/1000",
                "ACCEPT then operational REJECT: gate.ect at 1020 s, gate.scope at 1200 s",
                "adapted wall-ring triplet at 1.2/1.3 ms encodes the annulus sample at raster scale",
                "12 min settle floor as settle.floor bookend at 1800 s",
            ],
            "language_to_spike_mapping": "'riser looks empty' = eps.w 0.92; 'inventory intact' = dp.recon 8.00 plus eps.c 0.52; 'not MFT' = gate.ect ACCEPT; 'no oil' = gate.scope REJECT",
            "why_high_value": "New electrical-capacitance-tomography family (not r18 clamp-on transit-time, not r19 LFV aluminum, not r03 water-distribution, not r5 PMU). First earned bounded ACCEPT on a CFB inventory reconstruction that an annulus-only MFT would have tripped. Companion t2 is operational scope refusal, not a governance vote.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 20260963, "stream_note": "stream amplitudes authored (pF, voidage, kPa, kg/s) plus ect.ring adaptation 0.82**k"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "8-electrode ECT exists; stream keeps wall and core mean C; dP keeps 3 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "unit.load": 60000,
                    "pa.w": 60000,
                    "ect.cp": 60000,
                    "ect.cg": 60000,
                    "g.ser": 60000,
                    "rho.p": 60000,
                    "H.riser": 60000,
                    "ect.cw": 60000,
                    "ect.cc": 60000,
                    "eps.w": 60000,
                    "eps.c": 60000,
                    "ect.ring": 0.8,
                    "eps.avg": 60000,
                    "dp.recon": 60000,
                    "dp.kpa": 60000,
                    "ops.prop": 60000,
                    "gate.ect": 60000,
                    "pa.cmd": 60000,
                    "oil.prop": 60000,
                    "gate.scope": 60000,
                    "settle.floor": 60000,
                    "gate.exec": 60000,
                    "trip.dp": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-05-06T09:10:00Z simulated load hold",
            },
            "distillation_targets": [
                "serialized ECT voidage head: (C_p-C)/(C_p-C_g)",
                "dP inventory head: rho*g*H*(1-eps_avg) with g_ser=10",
                "wall-is-not-empty head: require core voidage AND dP vs annulus folklore",
                "bounded ACCEPT: PA cut + tripwire, not an unbounded yes",
                "operational companion: refuse oil-support without re-opening the inventory call",
            ],
        },
        "reconstruction_model": {
            "name": "ect_voidage_dp_inventory",
            "formula": "eps = (C_p - C) / (C_p - C_g); eps_avg = 0.60*eps_core + 0.40*eps_wall; dP_Pa = rho_p * g_ser * H * (1 - eps_avg); eps_wall_after = eps_wall - k_pa * dPA",
            "parameters": {
                "C_p_pF": 5.00,
                "C_g_pF": 1.00,
                "rho_p": 250.0,
                "g_ser": 10.0,
                "H_m": 10.0,
                "k_pa": 0.075,
                "dPA_kg_s": 0.80,
                "dp_floor_kPa": 6.50,
                "eps_core_trip": 0.70,
            },
            "worked_example": {
                "C_wall_pF": 1.32,
                "C_core_pF": 2.92,
                "eps_wall": 0.92,
                "eps_core": 0.52,
                "eps_avg": 0.680,
                "dP_kPa": 8.00,
                "eps_wall_after": 0.86,
                "C_wall_after_pF": 1.56,
            },
            "check": "(5.00-1.32)/4.00=0.92; (5.00-2.92)/4.00=0.52; 0.60*0.52+0.40*0.92=0.680; 250*10*10*0.320=8000; 0.92-0.075*0.80=0.86; (5.00-1.56)/4.00=0.86",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 28.0,
            "decision_window_s": 0.028,
            "code": "pw4.ect_inventory_gate",
            "note": "ACCEPT accumulator wins: dP inventory plus core voidage overpower the MFT advocate",
            "populations": [
                gate_pop("dp_inventory_evidence", 80, 1.3, 50.0, w_s),
                gate_pop("core_voidage_evidence", 64, 1.1, 40.0, w_s),
                gate_pop("mft_advocate", 40, 0.8, 25.0, w_s),
                gate_pop("accept_accumulator", 80, 1.5, 50.0, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                gc_check("pw4.dp_scorer", 80, 50.0, 28.0),
                gc_check("pw4.core_scorer", 64, 50.0, 28.0),
            ]
        ),
        "meta": meta_common(
            id="nelb-r20-063",
            clock_domain="pw-ect-sim-relative-ms-t0-2026-05-06T09:10:00Z",
            tags=["ect-cfb", "ACCEPT", "REJECT", "bounded-accept", "serialized-reconstruction", "operational-t2"],
        ),
    }


def walk_banned(obj, path=""):
    hits = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{path}.{k}" if path else k
            nk = str(k).casefold().replace("-", "_").replace(" ", "_")
            if nk in HIDDEN:
                hits.append(p)
            hits.extend(walk_banned(v, p))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            hits.extend(walk_banned(v, f"{path}[{i}]"))
    return hits


def local_checks(records):
    if tuple(RIGHTS.keys()) != RIGHTS_KEYS:
        raise RuntimeError("RM-793 rights key set/order mismatch")
    ids = []
    sims = []
    for rec in records:
        hits = walk_banned(rec)
        if hits:
            raise RuntimeError(f"banned keys {hits}")
        rights = rec["meta"]["rights"]
        if tuple(rights.keys()) != RIGHTS_KEYS:
            raise RuntimeError(f"{rec['id']} rights keys")
        if len(rights) != 15:
            raise RuntimeError("rights not 15")
        if rights["intended_use"] != "research_only" or rights["linear_issue"] != "RM-793":
            raise RuntimeError(f"{rec['id']} rights values")
        if "RM-793" not in rights["status_basis"]:
            raise RuntimeError("status_basis")
        ids.append(rec["id"])
        lv = rec["language_view"]
        ids.append(lv["trajectory"]["id"])
        for k, v in lv.items():
            if k.startswith("trajectory_") and isinstance(v, dict) and "id" in v:
                ids.append(v["id"])
        n = len(rec["spike_events"])
        if not (5 <= n <= 40):
            raise RuntimeError(f"{rec['id']} events {n}")
        gdec = rec["gate_snn"]["decision"]
        tdec = lv["trajectory"]["safety_decision"]["decision"]
        if gdec != tdec:
            raise RuntimeError(f"gate {gdec} != traj {tdec}")
        rast = rec["raster"]
        exp = int(round(rast["neurons"] * rast["mean_rate_hz"] * rast["window_s"]))
        if abs(rast["spikes"] - exp) > 0:
            raise RuntimeError("raster budget")
        if abs(rast["energy_pJ"] - rast["spikes"] * 23) > 1e-6:
            raise RuntimeError("energy pJ")
        if abs(rast["energy_uJ"] - rast["spikes"] * 23e-6) > 1e-9:
            raise RuntimeError("energy uJ")
        tf = rast["routing"]["third_factor"]
        if abs(tf["tau_e_ms"] / 1000.0 - tf["tau_e_s"]) > 1e-9:
            raise RuntimeError("tau pair")
        isi = rast["isi_count_identity"]
        if isi["isi_total"] != isi["spikes"] - isi["distinct_active_neurons"]:
            raise RuntimeError("isi identity")
        if sum(b["count"] for b in rast["isi_histogram"]) != isi["isi_total"]:
            raise RuntimeError("isi hist sum")
        if not rast["routing"]["table"]:
            raise RuntimeError("empty routing table")
        sim = lv["trajectory"]["state"]["sim_or_real"]
        if sim not in {"designed", "simulated", "hil"}:
            raise RuntimeError(sim)
        sims.append(sim)
        blob = json.dumps(rec)
        if "training_ready" in blob:
            raise RuntimeError("training_ready claimed")
        if '"real"' in blob:
            raise RuntimeError("quoted real token")
        if rec["meta"]["round"] != 20:
            raise RuntimeError("round")
        gc = rec["gate_compute"]
        if gc["total_spikes"] != sum(p["spikes"] for p in gc["per_check"]):
            raise RuntimeError("gate_compute total")
        if gc["total_energy_pJ"] != gc["total_spikes"] * 23:
            raise RuntimeError("gate_compute pJ")
        if abs(gc["total_energy_uJ"] - gc["total_spikes"] * 23e-6) > 1e-12:
            raise RuntimeError("gate_compute uJ")
        dw = rec["gate_snn"]
        if abs(dw["decision_window_ms"] / 1000.0 - dw["decision_window_s"]) > 1e-9:
            raise RuntimeError("decision window pair")
        for pop in dw["populations"]:
            if "mean_rate_hz" in pop or "spikes" in pop:
                exp_p = int(round(pop["neurons"] * pop["mean_rate_hz"] * dw["decision_window_s"]))
                if pop["spikes"] != exp_p:
                    raise RuntimeError(f"gate pop {pop['name']}")
        for tkey, tval in lv.items():
            if not isinstance(tval, dict) or "reward_components" not in tval:
                continue
            rc = tval["reward_components"]
            s = 0.0
            for k, v in rc.items():
                if k in {"aggregation", "rounding_decimals", "notes", "total"}:
                    continue
                if isinstance(v, (int, float)):
                    s += v
            if abs(s - rc["total"]) > 1e-12:
                raise RuntimeError(f"reward {tval['id']} {s} != {rc['total']}")
    if len(ids) != len(set(ids)):
        raise RuntimeError(f"dup ids {ids}")
    if set(sims) != {"designed", "simulated", "hil"}:
        raise RuntimeError(f"provenance set {sims}")
    print("local_checks ok", [r["id"] for r in records], "ids", len(ids), "sims", sims)


def write_notes(records, lines, gate_lines):
    rows = []
    decisions = []
    for rec in records:
        lv = rec["language_view"]
        t1 = lv["trajectory"]
        t2 = next(v for k, v in lv.items() if k.startswith("trajectory_"))
        d1 = t1["safety_decision"]["decision"]
        d2 = t2["safety_decision"]["decision"]
        decisions.extend([d1, d2])
        r1 = t1["reward_components"]["total"]
        r2 = t2["reward_components"]["total"]
        rast = rec["raster"]
        rows.append(
            {
                "id": rec["id"],
                "d1": d1,
                "d2": d2,
                "r1": r1,
                "r2": r2,
                "sim": t1["state"]["sim_or_real"],
                "events": len(rec["spike_events"]),
                "window": rast["window_ms"],
                "neurons": rast["neurons"],
                "rate": rast["mean_rate_hz"],
                "spikes": rast["spikes"],
                "isi": rast["isi_count_identity"]["isi_total"],
                "mod": rast["routing"]["third_factor"]["modulator"],
                "tau": rast["routing"]["third_factor"]["tau_e_s"],
                "bytes": len(json.dumps(rec, ensure_ascii=False, allow_nan=False, separators=(",", ":"))),
            }
        )
    na = decisions.count("ACCEPT")
    nm = decisions.count("MODIFY")
    nr = decisions.count("REJECT")
    notes = f"""# Neuromorphic Event + Language Bridge — NOTES round 20
Run: 2026-09-02-final-heavy · Factory: neuromorphic-event-language-bridge · Generator: grok-4.6 · Output: `batch-r20.jsonl` (3 paired artifacts, 6 ThalamicTrajectories)
Rights: RM-793 research-only (SpaceXAI/xAI grok-4.6, SuperGrok Heavy chat). Not training_ready. Do not publish into `outputs/raw/` from this generator; operator uses `pipelines/round_txn.py`. Staged only at `/tmp/nelb-r20/`.

## Context / de-duplication
Prior corpus read: 2026-08-17 r1–r12 family table; 2026-08-30 NOTES-r01–r04; staged `/tmp/nelb-r13`…`/tmp/nelb-r19` NOTES (r16 IFOG / transmon / hyperspectral; r17 MEMS accel / muon ore-pass / industrial x-ray; r18 optogenetic stim / 905 nm LiDAR snow / clamp-on transit-time; r19 LIBS / QEPAS / LFV). Pair shape from r13–r17 (`language_view.trajectory` + operational t2 + `spike_events` + `raster` + `gate_snn` + `isi_histogram` + `routing.third_factor` + 15-key RM-793 `meta.rights`).

Banned this round: r13 FBG glaze / MRI-quench / VRFB EIS; r14 BOTDA / QCM-D / MsS T(0,1); r15 SAW torque / CRDS HF / PGNAA; r16 IFOG / transmon readout / hyperspectral crop; r17 MEMS array / muon tomography / industrial x-ray; r18 optogenetic photovoltaic comb / 905 nm LiDAR snow / ultrasonic clamp-on; r19 LIBS Cu-ratio / QEPAS C2H2 / Lorentz-force velocimetry; r04 VOD-SNN / pharma cold-chain / CEMS; 2026-08-30 r01–r03 including dry-cask muon and LPBF melt-pool; r1–r12 table (DVS, cochlea, SPAD ToF, DAS, PMU, e-skin, vestibular, atomic clocks, tokamak, nanopore, VLF, QEC, GW, SOFAR, neutrino, fab OES, space weather, pulsar TOA, eddy covariance, flow cytometry). Unused r13-holes/premises sketches (cyclotron BPM/BLM, Co-60 alanine EPR, ADCP ice-jam, mud-pulse, Barkhausen, Lamb-wave) were not restaged.

r19 leftover 1 asked for vendor-only as a **lead REJECT** with no independent twin instrument. 062 harvests that on THz-TDS: CloudCoat is the only THz; defense is a gravimetric scale the vendor cannot write.

## Round 20 batch summary (3 pairs, 6 trajectories)

| id | modality (NEW family) | domain | decisions | headline |
|----|----------------------|--------|-----------|----------|
| nelb-r20-061 | laser Doppler vibrometry (800.0 nm fiber LDV on a Kaplan tip; serialized v=λ f_d/2; Campbell remaining-margin) | Mossgill Hydro KG-4 (invented 2.30 MW): tip 5.00 mm/s at f_d 12.50 kHz while housing SCADA still reads 1.80; remaining Campbell 8.00 percent-speed vs 12.0 floor, 108 percent islanding armed | MODIFY (+0.41) / ACCEPT (+0.33) | serialized `800e-9*12500/2=0.00500`; `(202.5-187.5)/187.5=0.080`; conjunctive SOP (tip velocity AND Campbell) forbids 100 percent gate and islanding; companion t2 is operational 72 percent wicket plus islanding hold, restore capped at 80 percent |
| nelb-r20-062 | terahertz time-domain spectroscopy (THz-TDS) of a radome coupon (gravimetric moisture → implied n and TOF; vendor-only CloudCoat THz) | Thornwick Composites GH-9, stand THz-HIL-4 (invented, HIL): scale 12.00 → 12.72 g reconstructs 6.00 percent moisture and implied 108.00 ps while CloudCoat freezes 90.00 ps / n=1.50 | REJECT (+0.43) / MODIFY (+0.32) | vendor-only THz as a **lead REJECT** (r19 leftover): no independent THz exists; `(12.72-12.00)/12.00=0.060`, `1.50+0.050*6.00=1.80`, `2*1.80*9.00/0.300=108.00`; micrometer stays 9.00 mm and cannot substitute; companion t2 is a Tg-limited 60 C bake (not 80 C), 4 h floor in-stream; sim_or_real=hil |
| nelb-r20-063 | electrical capacitance tomography (ECT) of a CFB riser (serialized ε=(C_p−C)/(C_p−C_g), dP=ρ g H (1−ε_avg)) | Polderwick Station CFB PW-4 (invented, simulated): wall ε 0.92 looks empty; core 0.52 and dP 8.00 kPa say inventory is intact | ACCEPT (+0.39) / REJECT (+0.34) | earned bounded ACCEPT on a lead: `(5.00-1.32)/4.00=0.92`, `(5.00-2.92)/4.00=0.52`, `250*10*10*0.320=8000`; MFT folklore refused; 8 percent PA cut 10.00 → 9.20 kg/s plus dP/core tripwire; companion t2 REJECTS oil-support as out of scope; sim_or_real=simulated |

Decision spread: MODIFY / ACCEPT / REJECT / MODIFY / ACCEPT / REJECT — **{na}A/{nm}M/{nr}R**. All three enums used, and all three sit on **leads**. Provenance spread: designed / hil / simulated (one each; never real). IDs `nelb-r20-061`…`063` plus t1/t2 suffixes.

## Raster sidecar
Every record carries `raster` + top-level `gate_snn` + `gate_compute`. Windows {rows[0]['window']:.0f}/{rows[1]['window']:.0f}/{rows[2]['window']:.0f} ms; `window_s == window_ms/1000` exactly; `spikes == round(neurons·rate·window_s)` with zero slack ({rows[0]['spikes']}/{rows[1]['spikes']}/{rows[2]['spikes']} at {rows[0]['rate']:.1f}/{rows[1]['rate']:.1f}/{rows[2]['rate']:.1f} Hz over {rows[0]['neurons']}/{rows[1]['neurons']}/{rows[2]['neurons']} neurons); `energy_pJ = spikes·23` and `energy_uJ = spikes·23e-6` exact. Routing source/target + 3-entry tables + `third_factor` on all three (modulators {rows[0]['mod']} / {rows[1]['mod']} / {rows[2]['mod']}; τe {rows[0]['tau']}/{rows[1]['tau']}/{rows[2]['tau']} s as consistent `tau_e_s`+`tau_e_ms` pairs). Excerpts integer `t_us`, in-window, `neuron_id`-bounded, sorted, full-window by construction, per-spike amplitude with adaptation (0.82**k) plus noise. ISI histograms from the full window, bins ≥1 ms, counts sum to `spikes − distinct_active_neurons` ({rows[0]['isi']}/{rows[1]['isi']}/{rows[2]['isi']}). Same-neuron gaps ≥1100 µs pre-round, ≥1000 µs serialized. `gate_snn` on all three: decisions MODIFY/REJECT/ACCEPT matching each lead; 062 carries the zero-rate unreachable `vendor_thz_admissible` population (asymmetric-null on the vendor-only channel). `gate_compute.per_check` windows 28–40 ms, budgets exact. Main streams: {rows[0]['events']}/{rows[1]['events']}/{rows[2]['events']} events (inside the 5–40 cap), strictly increasing `t_rel_ms` only (no `t_ms` mix), same-channel refractory ≥0.8 ms (061 LDV triplet at 1.2/1.3 ms, 062 vendor-echo triplet, 063 wall-ring triplet).

## Self-critique

### Edge cases added vs still thin
- **Added:** first fiber-LDV Kaplan-tip family; first THz-TDS radome-moisture family; first ECT CFB-riser family; vendor-only THz as a **lead REJECT** with no independent THz (r19 leftover 1, harder than 059's t2 GC refusal); gravimetric scale as the unwritable witness; implied n/TOF reconstruction the vendor bus cannot display; earned bounded ACCEPT on a CFB inventory reconstruction that an annulus-only MFT would have tripped; 18 min / 4 h / 12 min recovery floors in-stream; provenance trio designed/hil/simulated; operational t2 on all three (wicket hold, Tg-limited bake, oil-support refusal).
- **Still thin:** (i) 062 still has *a* plant witness (the scale) — a hangar whose only sensor is CloudCoat, so the gate must refuse on custody structure before any scale exists, is harder; (ii) 061 LDV assumes a single-mode 800 nm fiber and a linear v(f_d) — speckle dropout that could fake a quiet tip is unwritten; (iii) 063 voidage is a two-region (wall/core) mean, not a full 8-electrode inversion; a metal-riser short that collapses C independently of voidage is unwritten; (iv) stream amplitudes remain authored constants (raster draws are the only seeded noise); (v) r04's 90-day poison-class audit close-out and FBG Δλ(T) on a non-TW-17 blade remain untouched.

### Realism of noise / temporal fidelity
- Strong: 061's 5.00 mm/s and 8.00 percent-speed recompute from the record; 062's 6.00 percent / 1.80 / 108.00 ps recompute from the scale; 063's 0.92 / 0.52 / 8.00 kPa recompute from C and dP. Raster adaptation (0.82**k plus 4 percent noise) and 1.2–1.3 ms triplets give each 5–40 stream a raster-scale motif without violating 0.8 ms same-channel refractory.
- **Gaps, honestly:** (i) 5–40 cap forces heavy thinning (LDV kHz carrier kept as envelope f_d; THz picosecond waveform kept as one TOF; ECT 8 electrodes kept as two mean C); (ii) 062's 6 h soak and 4 h bake are bookends, not dense humidity streams; (iii) 061's 18 min hydraulic floor is two bookends plus one oil-T; (iv) no gate_snn input→output volley pair at raster resolution this round (r04-a1 already staged that).

### Training value (SNN/LSM + agentic)
Distillation targets: serialized LDV v=λ f_d/2; conjunctive Campbell SOP that a quiet housing accelerometer cannot substitute for; gravimetric moisture head; implied n/TOF from k_m; vendor-only THz refusal on a lead; Tg-limited bake companion; ECT voidage head; dP inventory head; wall-is-not-empty vs annulus folklore; bounded ACCEPT with PA-cut + tripwire; operational companions that execute or refuse scope without re-opening the physics call. Agentic value concentrates in three patterns: reconstruction-as-SoT on a physical error the raw SCADA channel cannot see, refuse when the infra/vendor can write the only optical SoT, and bind an ACCEPT so an annulus folklore trip does not calcify.

## What round 21 should add (next densification target)
1. **Custody-only THz refusal:** restage 062's leftover where even the gravimetric scale rides the colluding vendor, so the gate must refuse with *only* a write-ACL / missing-independent-instrument structure.
2. **LDV speckle dropout** that can hide a 5.00 mm/s tip inside a quiet 1.8 mm/s envelope, forcing housing+Campbell jointly with the reconstruction.
3. **ECT metal-riser short** that collapses C independently of voidage, closing 063's two-region-mean gap.
4. **Do not restage** VOD-SNN replay, pharma cold-chain, stack-gas CEMS, FBG glaze, Frostlip quench, Oxbow VRFB, IFOG, transmon, hyperspectral, MEMS array, muon ore-pass, industrial x-ray, optogenetic stim, 905 nm LiDAR snow, clamp-on transit-time, LIBS HL-2, QEPAS GB-7, LFV MF-9, Mossgill LDV KG-4, Thornwick THz-HIL-4, or Polderwick ECT PW-4.

## Verification
`batch-r20.jsonl`: 3 lines, `json.loads`-clean (allow_nan=False), ~{rows[0]['bytes']/1024:.1f}/{rows[1]['bytes']/1024:.1f}/{rows[2]['bytes']/1024:.1f} KB. Staged at `/tmp/nelb-r20/` only. {gate_lines} Build-time asserts: global strict time order; same-channel ≥0.8 ms; 5–40 events ({rows[0]['events']}/{rows[1]['events']}/{rows[2]['events']}); excerpt integer bounds, neuron bounds, sort, 1 ms per-neuron floor; ISI identity {rows[0]['isi']}/{rows[1]['isi']}/{rows[2]['isi']}; spike budgets exact; energy pJ/µJ exact; reward totals equal two-decimal component sums (+0.41/+0.33/+0.43/+0.32/+0.39/+0.34); gate_snn decisions match lead `safety_decision.decision`; `state.sim_or_real` ∈ {{designed, hil, simulated}}; `meta.round=20`, `meta.factory=neuromorphic-event-language-bridge`, `meta.generator=grok-4.6`, `meta.run_label=2026-09-02-final-heavy`; `meta.rights` 15-key RM-793 stamp, `intended_use=research_only`; no hidden-reasoning keys; no `provenance` objects; no 'real' claims; no `training_ready`; all 9 record/trajectory ids unique. Raster seeds 20260961/20260962/20260963, MT19937.

Honest novelty accounting: 3/3 modality families are new versus the committed factory and versus staged r13–r19. Vendor-only as a lead REJECT, implied-TOF reconstruction, and wall-vs-core inventory split are new edges. Against that: conjunctive SOP, operational t2, serialized reconstruction, bounded ACCEPT, and process-vs-cost reward splits are carried vocabulary; the 5–40 cap is a density constraint; 19 prior rounds already taught custody/governance. Net: a bit under two-fifths of the round's scenario/edge mass is genuinely novel.

Novel coverage: 37%
"""
    NOTES.write_text(notes, encoding="utf-8")
    print("wrote", NOTES, "bytes", NOTES.stat().st_size)


def repo_gates(records):
    chunks = []
    from check_records import FactoryStaging, check_jsonl

    errs, warns, kinds, n = check_jsonl(
        BATCH, "batch-r20.jsonl", staging=FactoryStaging(enabled=True)
    )
    chunks.append(
        f"`check_records.check_jsonl` with `FactoryStaging(enabled=True)` → {len(errs)} errors, {len(warns)} warnings, kinds `{kinds}` (n={n})"
    )
    if errs:
        raise RuntimeError(f"check_jsonl errors {errs[:5]}")

    import curate_bridge

    for rec in records:
        st = curate_bridge.raster_status(
            rec, require_raster=True, require_routing_table=True
        )
        if not st["raster_valid"] or not st["gate_snn_valid"] or st["reason_codes"]:
            raise RuntimeError(f"raster_status {rec['id']} {st}")
        if not st["third_factor_present"]:
            raise RuntimeError(f"third_factor missing {rec['id']}")
    chunks.append(
        "`curate_bridge.raster_status(..., require_raster=True, require_routing_table=True)` → raster_valid and gate_snn_valid true, empty reason codes, `third_factor_present` true on all three"
    )

    decisions = curate_bridge.curate_jsonl(
        BATCH, require_raster=True, require_routing_table=True
    )
    reasons = [
        (d.manifest.get("reason_codes") or [None])[0] for d in decisions
    ]
    if any(d.action != "retain" for d in decisions):
        raise RuntimeError(f"curate_jsonl {[d.action for d in decisions]} {reasons}")
    chunks.append(
        f"`curate_jsonl(...)` → {len(decisions)}× retain / `{reasons[0] if reasons else ''}`"
    )

    from verify_execution_shapes import verify_record_execution
    from verify_execution import verify_batch_for_frontier

    for rec in records:
        status, reason = verify_record_execution(rec, rec["id"])
        if status != "verified":
            raise RuntimeError(f"verify_record_execution {rec['id']} {status} {reason}")
    chunks.append("`verify_record_execution` → 3× verified")
    counts, findings, blocked = verify_batch_for_frontier(BATCH, strict=True)
    if blocked or counts.get("failed") or counts.get("inconclusive"):
        raise RuntimeError(f"frontier {counts} {findings}")
    chunks.append(
        f"`verify_batch_for_frontier(strict=True)` → {counts.get('verified')} verified, {counts.get('inconclusive')} inconclusive, {counts.get('failed')} failed, blocked {blocked}"
    )

    import spike_probe

    rasters, problems = spike_probe.load_rasters([str(BATCH)])
    summary = spike_probe.summarize(rasters, problems)
    if problems:
        raise RuntimeError(f"spike_probe {problems}")
    chunks.append(
        f"`python3 pipelines/spike_probe.py --strict {BATCH}` → loaded {len(rasters)}, unloadable 0, problems [], gate_snn_records {summary.get('gate_snn_records')}, third_factor_routes {summary.get('third_factor_routes')}"
    )
    return "; ".join(chunks) + "."


def main():
    if "outputs/raw" in str(BATCH):
        raise RuntimeError("refusing to write outputs/raw")
    records = [rec_061(), rec_062(), rec_063()]
    local_checks(records)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        json.dumps(r, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
        for r in records
    ]
    BATCH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote", BATCH, "bytes", BATCH.stat().st_size, "lines", len(lines))
    for i, r in enumerate(records):
        print(
            r["id"],
            "events",
            len(r["spike_events"]),
            "excerpt",
            len(r["raster"]["excerpt"]),
            "spikes",
            r["raster"]["spikes"],
            "isi",
            r["raster"]["isi_count_identity"],
            "sim",
            r["language_view"]["trajectory"]["state"]["sim_or_real"],
            "dec",
            r["language_view"]["trajectory"]["safety_decision"]["decision"],
            "bytes",
            len(lines[i]),
        )
    gate_lines = repo_gates(records)
    write_notes(records, lines, gate_lines)


if __name__ == "__main__":
    main()
