#!/usr/bin/env python3
"""Generate NELB round-24 research-only bridge pairs (do not write outputs/raw/)."""

from __future__ import annotations

import json
import math
import random
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

OUT_DIR = Path("/tmp/nelb-r24")
BATCH = OUT_DIR / "batch-r24.jsonl"
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
assert len(RIGHTS) == 15

HIDDEN = {
    "thought",
    "thoughts",
    "reasoning",
    "chain_of_thought",
    "hidden_thought",
    "scratchpad",
    "scratch",
    "internal_monologue",
    "private_reasoning",
    "inner_monologue",
}


def meta_common(**extra):
    m = {
        "round": 24,
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
        if t < last:
            raise RuntimeError("decreasing t_rel_ms")
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


def gate_compute(checks):
    total = 0
    per = []
    for check in checks:
        n = check["neurons"]
        r = check["mean_rate_hz"]
        w_ms = check["window_ms"]
        w_s = w_ms / 1000.0
        sp = int(round(n * r * w_s))
        if "spikes" in check and check["spikes"] != sp:
            raise RuntimeError(f"gate_compute {check['check']} {check['spikes']} != {sp}")
        per.append(
            {
                "check": check["check"],
                "neurons": n,
                "mean_rate_hz": float(r),
                "window_ms": float(w_ms),
                "window_s": float(w_s),
                "spikes": sp,
            }
        )
        total += sp
    return {
        "per_check": per,
        "total_spikes": total,
        "total_energy_pJ": total * 23,
        "total_energy_uJ": total * 23e-6,
        "model": "spikes = round(neurons * mean_rate_hz * window_s); 23 pJ/spike",
    }


# ---------------------------------------------------------------------------
# Record 073 — RUS porcelain post-insulator, designed, MODIFY / ACCEPT
# ---------------------------------------------------------------------------
def rec_073():
    # E_Pa = 4 * L_m^2 * f_Hz^2 * rho; L=0.200, rho=2500 => E = 400 * f^2
    assert abs(4.0 * (0.200**2) * (10000.0**2) * 2500.0 - 4.00e10) < 1e-6
    assert abs(10000.0 / 80.0 - 125.0) < 1e-12
    assert abs(4.0 * (0.200**2) * (13000.0**2) * 2500.0 - 6.76e10) < 1e-6
    raster = make_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=36.0,
        seed=20260924,
        source="wb6.rus.stack",
        target="whinbalk.replace_unit_core",
        table=[
            {"from": "rus_f", "to": "modulus_estimator", "weight": 1.35},
            {"from": "rus_df", "to": "q_factor_core", "weight": 1.20},
            {"from": "ringveil_stamp", "to": "vendor_keep_advocate", "weight": 0.45},
        ],
        third_factor={
            "modulator": "na.porcelain_crack_salience",
            "tau_e_s": 1.8,
            "tau_e_ms": 1800.0,
            "eligibility": "pre-post coincidence on modulus synapses; the crack modulator enables potentiation only while Q stays depressed inside tau_e so a factory-stamp 72 GPa cannot hide a 10 kHz unit",
        },
        channel_prefix="rus.n",
        anchor="WB-6 RUS 36 ms frame at f 10.00 kHz / df 80.0 Hz (t_s 3600) where E 40.00 GPa and Q 125 first clear the replace conjunction",
    )
    w_s = 0.036
    events = [
        ev(0.0, "rus.f", 13.00, code="F_KHZ", units="kHz", note="pre-dawn stack RUS; 13.00 kHz healthy porcelain"),
        ev(600000.0, "rus.df", 26.0, code="DF_HZ", units="Hz", note="linewidth; Q = f/df"),
        ev(900000.0, "recon.E", 67.60, code="E_GPA", units="GPa", note="400*(13000^2)=6.76e10 Pa = 67.60 GPa exact"),
        ev(1200000.0, "recon.Q", 500.0, code="Q", units="1", note="13000/26.0 = 500.0 exact"),
        ev(1500000.0, "rus.L", 0.200, code="L_M", units="m", note="unit gauge length; serialized L"),
        ev(1800000.0, "stamp.E", 72.0, code="STAMP_GPA", units="GPa", note="Ringveil factory-stamp modulus; vendor-writable"),
        ev(2400000.0, "rus.f", 11.50, code="F_KHZ", units="kHz"),
        ev(3000000.0, "recon.E", 52.90, code="E_GPA", units="GPa", note="400*(11500^2)=5.29e10 Pa = 52.90 GPa"),
        ev(3300000.0, "bay.kV", 132.0, code="BAY_KV", units="kV", note="bay still energized; a voltage corridor is not a stack license"),
        ev(3600000.0, "rus.f", 10.00, code="F_KHZ", units="kHz", note="replace-conjunction frame; raster sidecar"),
        ev(3600001.4, "rus.df", 80.0, code="DF_HZ", units="Hz", note="1.4 ms linewidth after f; same-channel floors stay 600 s"),
        ev(3900000.0, "recon.E", 40.00, code="E_GPA", units="GPa", note="400*(10000^2)=4.00e10 Pa = 40.00 GPa exact; replace floor 50.0"),
        ev(4200000.0, "recon.Q", 125.0, code="Q", units="1", note="10000/80.0 = 125.0 exact; Q floor 200"),
        ev(4800000.0, "stamp.E", 72.0, code="STAMP_GPA", units="GPa"),
        ev(5400000.0, "humid.rh", 88.0, code="RH_PCT", units="pct", note="wet porcelain; a humidity corridor is not a 10 kHz explanation"),
        ev(6000000.0, "ops.prop", 1.0, code="REPLACE_ALL_14", units="bool", note="linesman Oren Vetch: Ringveil 72 GPa, 10 kHz is coupling error, replace the whole stack"),
        ev(6600000.0, "gate.replace", 1.0, code="MODIFY", units="decision", note="U-14 only; remainder stays; 12 min outage floor"),
        ev(7200000.0, "unit.mark", 14.0, code="U14", units="index"),
        ev(7800000.0, "outage.start", 1.0, code="OUTAGE_START", units="bool", note="bookend 1 of the 12.0 min floor"),
        ev(8160000.0, "torque.prep", 0.0, code="TORQUE_NM", units="Nm", note="6.0 min marker; sticks staged"),
        ev(8520000.0, "outage.floor", 1.0, code="OUTAGE_FLOOR", units="bool", note="7800 s + 720 s = 8520 s = 12.0 min"),
        ev(9000000.0, "torque.nm", 80.0, code="TORQUE_NM", units="Nm", note="inside 70-90 Nm envelope"),
        ev(9600000.0, "swap.done", 1.0, code="U14_SWAPPED", units="bool"),
        ev(10200000.0, "gate.exec", 1.0, code="ACCEPT", units="decision", note="companion t2: U-14 swap inside envelope"),
        ev(10800000.0, "recon.E", 40.00, code="E_GPA", units="GPa", note="removed unit still 40.00 GPa; not re-argued"),
        ev(11400000.0, "stamp.E", 72.0, code="STAMP_GPA", units="GPa"),
        ev(12000000.0, "trip.hold", 0.0, code="TRIP_GPA", units="GPa", note="peak E 40.00 vs 30.00 isolate floor; bay isolate not taken"),
        ev(12600000.0, "stack.remain", 13.0, code="UNITS_LEFT", units="count"),
        ev(13200000.0, "humid.rh", 88.0, code="RH_PCT", units="pct"),
        ev(13800000.0, "bay.kV", 132.0, code="BAY_KV", units="kV"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r24-073-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "WB-RUS-2026-0318",
            "domain": "rus_porcelain_post_insulator",
            "setting": "Whinbalk 132 kV bay WB-6 (invented), 14-unit porcelain post stack. Plant-owned resonant-ultrasound drive on unit U-14 is the modulus SoT. Ringveil factory-stamp GPa is a corridor witness, not the replace SoT. Invented plant; designed campaign. Not QCM-D RO fouling (r14), not SAW torque (r15), not MEMS housing array (r17), not THz-TDS bondline (r21).",
            "observables_at_decision": {
                "f_kHz": 10.00,
                "df_Hz": 80.0,
                "E_GPa": 40.00,
                "Q": 125.0,
                "stamp_E_GPa": 72.0,
                "replace_floor_GPa": 50.0,
            },
            "margin_authority": "WB-6 RUS SOP rev B: replace this unit if reconstructed E_GPa < 50.0 AND Q < 200. A Ringveil stamp cannot keep a 10 kHz unit. Whole-stack condemn requires three units below isolate 30.0 GPa.",
        },
        "proposed_action": {
            "actor": "linesman Oren Vetch, citing Ringveil stamp 72 GPa and '10 kHz is a coupling error in the rain'",
            "summary": "de-energize the 132 kV bay and replace all 14 porcelain units",
            "basis_claimed": "factory-stamp modulus is 72 GPa and RH 88 percent explains the linewidth",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "The bay is not isolated, and U-14 is not left in service. Serialized reconstruction: E_Pa = 4 * L_m^2 * f_Hz^2 * rho = 4 * 0.200^2 * 10000^2 * 2500 = 4.00e10 Pa = 40.00 GPa, and Q = f/df = 10000/80.0 = 125.0. Both legs of SOP rev B fire. Ordered: replace unit U-14 only this outage; remainder of the 14-unit stack stays. Explicit scope: this modify does not condemn units U-01..U-13 and does not de-energize the bay. Isolate tripwire: E_GPa < 30.0 on three units.",
            "threshold": "E_GPa<50.0 AND Q<200 AND unit=U-14; bay remainder stays",
            "stated_residuals": "40.00 GPa is not 30.00; 13 units unmeasured this frame; Ringveil stamp remains unmeasured by any plant-owned channel",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 6600: U-14 marked; 12 min outage clock started; Ringveil channel not used as SoT",
            "tool": "wb6-rus-replace-gate-cli",
            "observation": "E 40.00 GPa recomputes from f 10.00 kHz and L 0.200 m; Q 125.0; stamp not SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3600.0, "event": "RUS f 10.00 kHz; raster frame; E 40.00 GPa Q 125"},
                {"t_s": 6000.0, "event": "ops proposes whole-stack replace"},
                {"t_s": 6600.0, "event": "MODIFY U-14 only"},
                {"t_s": 7800.0, "event": "12 min outage bookend 1"},
                {"t_s": 8520.0, "event": "12.0 min floor"},
                {"t_s": 10200.0, "event": "companion ACCEPT swap"},
            ],
            "observed_effects": [
                "E and Q recompute from the serialized RUS model at every recon event",
                "a stamp-only head would have condemned 14 units on a 72 GPa corridor",
                "peak E 40.00 stayed above the 30.00 isolate floor",
            ],
            "surprises": [
                "bay kV stayed 132 until the unit swap; a voltage-only head would have treated energized as a license to keep U-14",
            ],
            "new_state": {
                "u14": "marked for swap",
                "stack_remainder": "in service",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 3600000.0,
        },
        "reward_components": reward(
            0.41,
            [
                ("rus_modulus_reconstruction", 0.14),
                ("unit_scope_modify", 0.12),
                ("q_conjunction", 0.10),
                ("isolate_tripwire_armed", 0.08),
                ("outage_takt_cost", -0.03),
            ],
            "scored for a unit-scoped MODIFY on a recomputable RUS modulus and Q while refusing a factory-stamp whole-stack condemn",
        ),
        "meta": meta_common(
            tags=["MODIFY", "rus-porcelain", "serialized-reconstruction", "operational-companion"],
            distillation_note="RUS replace gate: 4 L^2 f^2 rho reconstruction beats a factory-stamp corridor; companion t2 swaps U-14 rather than re-arguing GPa",
        ),
    }
    traj2 = {
        "id": "nelb-r24-073-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "WB-RUS-2026-0318-exec",
            "domain": "porcelain_unit_swap_execution",
            "setting": "Same WB-6 after the bounded MODIFY. This companion is the operational U-14 swap, not a second modulus vote.",
            "observables_at_decision": {
                "torque_Nm": 80.0,
                "torque_envelope_Nm": [70.0, 90.0],
                "E_GPa": 40.00,
                "outage_floor_complete": 1,
            },
        },
        "proposed_action": {
            "actor": "lines crew following the MODIFY",
            "summary": "swap U-14 at 80 Nm after the 12 min outage floor; isolate tripwire remains E < 30 GPa; remainder stays",
            "basis_claimed": "MODIFY requirements are fully specified and inside the torque envelope",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "The execution envelope is intact: torque 80 Nm is inside 70-90, the 12.0 min outage floor is marked in the stream, and the isolate tripwire (E_GPa < 30.0) is armed on the same RUS head. ACCEPT the U-14 swap. Do not add U-13 at empty; 40.00 GPa is the removed-unit cap until a new frame.",
            "threshold": "torque in [70,90] Nm AND outage_floor AND isolate_tripwire_armed AND remainder_not_swapped",
        },
        "executed_action": {
            "summary": "outage floor t_s 8520; swap done t_s 9600; peak E 40.00 GPa; 13 units remain",
            "tool": "wb6-unit-swap-exec",
            "observation": "torque 80 Nm; no bay isolate; remainder left in service",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 8520.0, "event": "12.0 min outage floor marked"},
                {"t_s": 9600.0, "event": "U-14 swapped"},
                {"t_s": 10200.0, "event": "execution ACCEPT complete"},
            ],
            "observed_effects": [
                "isolate tripwire never fired; 40.00 vs 30.00 GPa floor",
                "units U-01..U-13 remained out of scope after the swap",
            ],
            "new_state": {"u14": "replaced", "stack_remainder": "in service", "bay": "132 kV"},
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("envelope_respect", 0.12),
                ("outage_floor_honored", 0.11),
                ("no_stack_condemn", 0.09),
                ("unit_swapped_on_segment", 0.04),
                ("held_remainder_cost", -0.02),
            ],
            "operational execution gate: the companion swaps U-14 rather than re-opening the modulus call",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "porcelain-swap"]),
    }
    return {
        "id": "nelb-r24-073",
        "spike_events": events,
        "language_view": {
            "description": "Whinbalk 132 kV WB-6. Plant-owned RUS reconstructs 40.00 GPa and Q 125 on porcelain unit U-14 from f 10.00 kHz while Ringveil factory-stamp still shows 72 GPa. The gate MODIFYs to replace U-14 only; a companion execution ACCEPT swaps the unit inside the torque envelope after a 12.0 min outage floor serialized in the stream.",
            "trajectory": traj,
            "trajectory_unit_swap": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "rus.f / rus.df / rus.L": "drive frequency, linewidth, and gauge length; the physics channels the reconstruction consumes",
                "recon.E / recon.Q": "serialized modulus and quality factor",
                "stamp.E / bay.kV / humid.rh": "factory-stamp, energized-bay, and humidity corridors; the denial channels that look healthy",
                "ops.prop / gate.replace / gate.exec": "whole-stack proposal, bounded MODIFY, companion ACCEPT",
                "outage.start / outage.floor / torque.nm / swap.done": "operational companion channels plus the 12 min floor",
            },
            "temporal_motifs": [
                "stamp-healthy while unit-cracked: stamp.E 72 next to recon.E 40.00",
                "compensation as event: recon.E 40.00 equals 4*L^2*f^2*rho / 1e9",
                "MODIFY then operational ACCEPT: gate.replace at 6600 s, gate.exec at 10200 s",
                "tight RUS pair: rus.f then rus.df +1.4 ms at the raster frame",
                "slow floor in-stream: outage.start 7800 s, outage.floor 8520 s (12.0 min)",
            ],
            "language_to_spike_mapping": "'10 kHz is coupling error' = rus.f 10.00 next to stamp.E 72; '40 GPa' = recon.E 40.00; 'this unit not the stack' = gate.replace MODIFY plus stack.remain 13; 'execute the swap' = swap.done then companion ACCEPT",
            "why_high_value": "New RUS porcelain-insulator family (not QCM-D, not SAW torque, not MEMS array, not THz-TDS r21 bondline). First 4 L^2 f^2 rho reconstruction that can hide a cracked unit inside a factory-stamp corridor. Companion t2 is operational unit swap. sim_or_real=designed.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 20260924, "stream_note": "stream amplitudes are authored constants (kHz, Hz, GPa, Q, kV, pct, Nm, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "RUS sweep exists at 50 Hz; stream keeps 3 f points; recon keeps 3 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "rus.f": 60000,
                    "rus.df": 1.4,
                    "recon.E": 60000,
                    "recon.Q": 60000,
                    "rus.L": 60000,
                    "stamp.E": 60000,
                    "bay.kV": 60000,
                    "humid.rh": 60000,
                    "ops.prop": 60000,
                    "gate.replace": 60000,
                    "unit.mark": 60000,
                    "outage.start": 60000,
                    "torque.prep": 60000,
                    "outage.floor": 60000,
                    "torque.nm": 60000,
                    "swap.done": 60000,
                    "gate.exec": 60000,
                    "trip.hold": 60000,
                    "stack.remain": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-03-18T05:00:00Z campaign start",
            },
            "distillation_targets": [
                "RUS reconstruction head: E = 4 L^2 f^2 rho; Q = f/df",
                "bounded MODIFY head: E AND Q floors AND unit scope AND not-whole-stack",
                "operational companion: execute the swap without re-opening the modulus call",
                "slow outage floor as events: two bookends plus a torque marker at 12.0 min",
            ],
        },
        "reconstruction_model": {
            "name": "rus_longitudinal_modulus_and_q",
            "formula": "E_Pa = 4 * L_m^2 * f_Hz^2 * rho_kg_m3; E_GPa = E_Pa / 1e9; Q = f_Hz / df_Hz",
            "parameters": {
                "L_m": 0.200,
                "rho_kg_m3": 2500.0,
                "replace_floor_GPa": 50.0,
                "q_floor": 200.0,
                "isolate_GPa": 30.0,
            },
            "worked_example": {
                "f_Hz": 10000.0,
                "df_Hz": 80.0,
                "E_GPa": 40.00,
                "Q": 125.0,
            },
            "check": "4 * 0.200^2 * 10000^2 * 2500 = 4.00e10 Pa = 40.00 GPa exactly; 10000/80.0 = 125.0; 7800 s + 720 s = 8520 s = 12.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 36.0,
            "decision_window_s": 0.036,
            "code": "wb6.replace_unit_gate",
            "note": "MODIFY accumulator wins: modulus and Q evidence overpower the stamp-keep advocate",
            "decode_rule": "modify-replace-unit if modulus_estimator AND q_factor_core fire inside the window; vendor_keep_advocate is necessary-but-not-sufficient and cannot release the whole stack",
            "populations": [
                gate_pop("modulus_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("q_factor_core", 64, 1.2, 31.25, w_s),
                gate_pop("unit_scope", 40, 1.0, 50.0, w_s),
                gate_pop("vendor_keep_advocate", 40, 0.8, 25.0, w_s),
                gate_pop("modify_latch", 96, 1.8, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "wb6.modulus_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 36.0},
                {"check": "wb6.q_scorer", "neurons": 50, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r24-073",
            clock_domain="wb6-rus-campaign-relative-ms-t0-2026-03-18T05:00:00Z",
            tags=["rus-porcelain", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 074 — N-16 gamma transit-time PWR-loop mock-up, simulated, ACCEPT / ACCEPT
# ---------------------------------------------------------------------------
def rec_074():
    assert abs(4.00 / 0.250 - 16.00) < 1e-12
    assert abs(720.0 * 0.250 * 16.00 - 2880.0) < 1e-12
    assert abs(4.00 / 0.320 - 12.50) < 1e-12
    raster = make_raster(
        neurons=25,
        mean_rate_hz=50.0,
        window_ms=32.0,
        seed=20260925,
        source="gw2.n16.loop3",
        target="gullwick.stay_core",
        table=[
            {"from": "n16_dt", "to": "velocity_estimator", "weight": 1.40},
            {"from": "n16_L", "to": "path_norm_core", "weight": 1.15},
            {"from": "loopveil_elbow", "to": "trip_advocate", "weight": 0.50},
        ],
        third_factor={
            "modulator": "da.flow_mismatch",
            "tau_e_s": 2.0,
            "tau_e_ms": 2000.0,
            "eligibility": "pre-post coincidence on velocity synapses; the mismatch modulator depresses trip links when N-16 dt stays at 0.250 s inside tau_e of a frozen elbow tap so a 9.40 m/s last-good cannot hide a 16 m/s loop",
        },
        channel_prefix="n16.n",
        anchor="GW-2 N-16 32 ms frame at dt 0.250 s / L 4.00 m (t_s 3600) that reconstructs 16.00 m/s against a frozen 9.40 m/s elbow tap",
    )
    w_s = 0.032
    events = [
        ev(0.0, "n16.dA", 1.00, code="DET_A", units="bool", note="simulated sealed primary-loop mock-up; LaBr3 A sees N-16 6.13 MeV"),
        ev(600000.0, "n16.dB", 1.00, code="DET_B", units="bool", note="detector B 4.00 m downstream; not clamp-on ultrasonic, not LFV"),
        ev(900000.0, "n16.dt", 0.250, code="DT_S", units="s"),
        ev(1200000.0, "recon.v", 16.00, code="V_M_S", units="m_s", note="4.00/0.250 = 16.00 exact"),
        ev(1800000.0, "elbow.v", 16.10, code="ELBOW_M_S", units="m_s", note="LoopVeil elbow tap still tracking"),
        ev(2400000.0, "recon.mdot", 2880.0, code="MDOT_KG_S", units="kg_s", note="720*0.250*16.00 = 2880 exact"),
        ev(3000000.0, "Tcold", 288.0, code="T_K", units="K"),
        ev(3600000.0, "n16.dA", 1.00, code="DET_A", units="bool", note="stay-authorization frame; raster sidecar"),
        ev(3600001.3, "n16.dB", 1.00, code="DET_B", units="bool", note="1.3 ms B after A"),
        ev(3900000.0, "n16.dt", 0.250, code="DT_S", units="s"),
        ev(4200000.0, "recon.v", 16.00, code="V_M_S", units="m_s"),
        ev(4800000.0, "elbow.v", 9.40, code="ELBOW_M_S", units="m_s", note="LoopVeil frozen last-good after crud burst; vendor-writable DCS"),
        ev(5400000.0, "crud.burst", 1.0, code="CRUD", units="bool"),
        ev(6000000.0, "ops.prop", 1.0, code="TRIP_REACTOR", units="bool", note="shift supervisor Noll Cress: elbow 9.40 m/s is loss-of-flow, trip the mock-up"),
        ev(6600000.0, "gate.stay", 1.0, code="ACCEPT", units="decision", note="bounded ACCEPT: this loop this shift; elbow not SoT; tripwire dt>0.320 s"),
        ev(7000000.0, "elbow.tag", 1.0, code="NON_CUSTODY", units="bool"),
        ev(7200000.0, "resample.start", 1.0, code="RESAMPLE_START", units="bool", note="bookend 1 of the 4.0 h floor"),
        ev(7800000.0, "n16.lock", 16.00, code="LOCKED_V", units="m_s"),
        ev(8400000.0, "recon.mdot", 2880.0, code="MDOT_KG_S", units="kg_s"),
        ev(14400000.0, "Tcold", 287.0, code="T_K", units="K", note="2.0 h marker"),
        ev(21600000.0, "resample.floor", 1.0, code="RESAMPLE_FLOOR", units="bool", note="7200 s + 14400 s = 21600 s = 4.0 h"),
        ev(22200000.0, "n16.dt", 0.250, code="DT_S", units="s"),
        ev(22800000.0, "recon.v", 16.00, code="V_M_S", units="m_s"),
        ev(23400000.0, "elbow.v", 9.40, code="ELBOW_HELD", units="m_s"),
        ev(24000000.0, "gate.exec", 1.0, code="ACCEPT", units="decision", note="companion t2: stay executed; N-16 remains SoT"),
        ev(24600000.0, "trip.hold", 0.0, code="TRIP_DT", units="s", note="dt 0.250 vs 0.320 isolate floor; trip not taken"),
        ev(25200000.0, "loop.id", 3.0, code="LOOP3", units="index", note="loops 1,2,4 out of scope"),
        ev(25800000.0, "recon.mdot", 2880.0, code="MDOT_KG_S", units="kg_s"),
        ev(26400000.0, "Tcold", 287.0, code="T_K", units="K"),
        ev(27000000.0, "n16.lock", 16.00, code="LOCKED_V", units="m_s"),
        ev(27600000.0, "elbow.tag", 1.0, code="NON_CUSTODY", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r24-074-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "GW-N16-2026-0712",
            "domain": "n16_transit_time_loop_flow",
            "setting": "Gullwick PWR mock-up unit GW-2 (invented), loop 3. Simulated sealed primary-loop with two LaBr3 detectors 4.00 m apart viewing N-16 6.13 MeV. Plant-owned transit-time is the flow SoT. LoopVeil elbow-tap DCS is a corridor witness, not the trip SoT. Invented plant; simulated campaign. Not clamp-on ultrasonic custody (r18), not LFV aluminum (r19), not ECT riser holdup (r22), not water-distribution hydraulics (r03), not PMU.",
            "observables_at_decision": {
                "L_m": 4.00,
                "dt_s": 0.250,
                "v_m_s": 16.00,
                "mdot_kg_s": 2880.0,
                "elbow_v_m_s": 9.40,
                "tripwire_dt_s": 0.320,
            },
            "margin_authority": "GW-2 N-16 SOP rev A: this loop may stay at power if reconstructed v_m_s >= 12.50 (dt <= 0.320 s) AND the authorization covers this loop this shift. A frozen elbow tap cannot substitute for N-16. Loops 1,2,4 are out of scope.",
        },
        "proposed_action": {
            "actor": "shift supervisor Noll Cress, citing LoopVeil elbow 9.40 m/s after the crud burst",
            "summary": "trip the mock-up on loss-of-flow; elbow tap is the licensed DCS SoT",
            "basis_claimed": "9.40 m/s is below the 12.50 m/s trip table and N-16 is a physics curiosity",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "This loop is accepted, not the trip. Serialized reconstruction: v_m_s = L_m / dt_s = 4.00 / 0.250 = 16.00, and mdot_kg_s = rho * A * v = 720.0 * 0.250 * 16.00 = 2880. Both clear the 12.50 m/s stay floor. SOP rev A still forbids using the frozen elbow as a trip license: ordered stay of loop 3 this shift only. Explicit scope: this accept does not cover loops 1,2,4 and does not authorize a second stay without a new N-16 frame. Isolate tripwire: dt_s > 0.320 (v < 12.50).",
            "threshold": "v_m_s>=12.50 AND loop=3 AND shift=this AND elbow_not_sot",
            "stated_residuals": "16.00 m/s is not infinite; crud burst still in the loop; elbow tap remains frozen at 9.40 until a plant flush",
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 6600: loop 3 stay authorized; elbow tagged non-custody; reconstruction locked as SoT",
            "tool": "gw2-n16-stay-gate-cli",
            "observation": "v 16.00 m/s recomputes from L 4.00 m and dt 0.250 s; mdot 2880 kg/s; LoopVeil not SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3600.0, "event": "N-16 dt 0.250 s; raster frame; v 16.00 m/s"},
                {"t_s": 4800.0, "event": "elbow tap freezes at 9.40 m/s"},
                {"t_s": 6000.0, "event": "ops proposes trip"},
                {"t_s": 6600.0, "event": "ACCEPT bounded stay; elbow refused as SoT"},
                {"t_s": 21600.0, "event": "4.0 h resample floor"},
                {"t_s": 24000.0, "event": "companion ACCEPT stay executed"},
            ],
            "observed_effects": [
                "velocity and mdot recompute from the serialized N-16 model at every recon event",
                "an elbow-only head would have tripped the mock-up on a 9.40 m/s last-good",
                "dt 0.250 stayed under the 0.320 isolate floor",
            ],
            "surprises": [
                "Tcold stayed 288 K across the crud burst; a temperature-only head would have treated thermal-stable as a flow license",
            ],
            "new_state": {
                "loop3": "at power; N-16 SoT",
                "elbow": "tagged non-custody",
                "loops_124": "out of scope",
            },
            "latency_ms": 17400000.0,
        },
        "reward_components": reward(
            0.40,
            [
                ("n16_velocity_reconstruction", 0.14),
                ("bounded_stay_accept", 0.12),
                ("elbow_nonsubstitution", 0.10),
                ("tripwire_armed", 0.07),
                ("crud_takt_cost", -0.03),
            ],
            "scored for an earned ACCEPT of this-loop stay on a recomputable N-16 transit time while refusing a frozen elbow-tap trip",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "n16-transit", "serialized-reconstruction", "operational-companion"],
            distillation_note="N-16 stay gate: L/dt reconstruction beats a frozen elbow last-good; companion t2 holds the stay rather than re-arguing flow",
        ),
    }
    traj2 = {
        "id": "nelb-r24-074-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "GW-N16-2026-0712-exec",
            "domain": "loop_stay_execution",
            "setting": "Same GW-2 loop 3 after the bounded ACCEPT. This companion is the operational stay, not a second flow vote.",
            "observables_at_decision": {
                "v_m_s": 16.00,
                "dt_s": 0.250,
                "elbow_tagged": 1,
                "resample_floor_complete": 1,
            },
        },
        "proposed_action": {
            "actor": "loop controller following the ACCEPT",
            "summary": "keep loop 3 at power with N-16 live as isolate interlock; elbow remains non-custody; loops 1,2,4 stay out of scope",
            "basis_claimed": "ACCEPT requirements are fully specified and the 4.0 h resample floor is marked",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "The execution envelope is intact: dt 0.250 s is inside the stay floor, N-16 is live, the isolate tripwire (dt > 0.320 s) is armed, and the 4.0 h resample floor is in the stream. ACCEPT the stay. Do not restore LoopVeil as SoT at empty; 16.00 m/s is the loop cap until a new frame.",
            "threshold": "dt<=0.320 s AND n16_live AND isolate_tripwire_armed AND elbow_not_sot",
        },
        "executed_action": {
            "summary": "stay held through t_s 24000; peak dt 0.250 s; elbow still tagged; loops 1,2,4 untouched",
            "tool": "gw2-loop-stay-exec",
            "observation": "v 16.00 then 16.00 m/s; no trip; elbow 9.40 held non-custody",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 7200.0, "event": "4.0 h resample bookend 1"},
                {"t_s": 21600.0, "event": "4.0 h floor marked"},
                {"t_s": 24000.0, "event": "execution ACCEPT complete"},
            ],
            "observed_effects": [
                "isolate tripwire never fired; 0.250 vs 0.320 s floor",
                "elbow tap remained out of SoT after the floor",
            ],
            "new_state": {"loop3": "at power", "elbow": "non-custody", "n16": "SoT"},
            "latency_ms": 17400000.0,
        },
        "reward_components": reward(
            0.35,
            [
                ("n16_sot_live", 0.13),
                ("elbow_tagged", 0.10),
                ("resample_floor", 0.08),
                ("stay_executed", 0.06),
                ("hold_cost", -0.02),
            ],
            "operational execution gate: the companion holds the stay rather than re-opening the flow call",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "n16-stay"]),
    }
    return {
        "id": "nelb-r24-074",
        "spike_events": events,
        "language_view": {
            "description": "Gullwick PWR mock-up GW-2 loop 3, simulated sealed primary. Plant-owned N-16 transit time reconstructs 16.00 m/s (mdot 2880 kg/s) from L 4.00 m / dt 0.250 s while LoopVeil elbow tap freezes at 9.40 m/s after a crud burst. The gate ACCEPTs this-loop stay; a companion execution ACCEPT holds the stay after a 4.0 h resample floor serialized in the stream.",
            "trajectory": traj,
            "trajectory_stay_execution": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "n16.dA / n16.dB / n16.dt": "detector pair and transit time; the physics channels the reconstruction consumes",
                "recon.v / recon.mdot / n16.lock": "serialized velocity and mass-flow",
                "elbow.v / elbow.tag / crud.burst": "frozen DCS last-good, non-custody tag, crud burst",
                "ops.prop / gate.stay / gate.exec": "trip proposal, bounded ACCEPT, companion ACCEPT",
                "resample.start / resample.floor / Tcold": "slow resample floor bookends plus cold-leg temperature markers",
            },
            "temporal_motifs": [
                "elbow-low while N-16-healthy: elbow.v 9.40 next to recon.v 16.00",
                "compensation as event: recon.v 16.00 equals 4.00/0.250",
                "ACCEPT then operational ACCEPT: gate.stay at 6600 s, gate.exec at 24000 s",
                "tight N-16 pair: n16.dA then n16.dB +1.3 ms at the raster frame",
                "slow floor in-stream: resample.start 7200 s, resample.floor 21600 s (4.0 h)",
            ],
            "language_to_spike_mapping": "'elbow 9.40 is loss-of-flow' = elbow.v 9.40 next to recon.v 16.00; 'stay this loop' = gate.stay ACCEPT plus loop.id 3; 'execute the stay' = n16.lock then companion ACCEPT",
            "why_high_value": "New N-16 gamma transit-time family (not clamp-on ultrasonic r18, not LFV r19, not ECT holdup r22, not PMU, not water hydraulics). First L/dt reconstruction that can hide a healthy loop inside a frozen elbow last-good. Companion t2 is operational stay. sim_or_real=simulated.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 20260925, "stream_note": "stream amplitudes authored (s, m/s, kg/s, K, bool)"},
                "draw_order": "raster per neuron id order with adaptation/noise",
                "thinning": "N-16 coincidences exist at ~10 Hz; stream keeps 3 dt points; Tcold keeps 3 of ~4 h",
                "refractory_floors_ms": {
                    "n16.dA": 60000,
                    "n16.dB": 1.3,
                    "n16.dt": 60000,
                    "recon.v": 60000,
                    "elbow.v": 60000,
                    "recon.mdot": 60000,
                    "Tcold": 60000,
                    "crud.burst": 60000,
                    "ops.prop": 60000,
                    "gate.stay": 60000,
                    "elbow.tag": 60000,
                    "n16.lock": 60000,
                    "resample.start": 60000,
                    "resample.floor": 60000,
                    "gate.exec": 60000,
                    "trip.hold": 60000,
                    "loop.id": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-07-12T21:00:00Z simulated night start",
            },
            "distillation_targets": [
                "N-16 reconstruction head: v = L/dt; mdot = rho * A * v",
                "bounded ACCEPT head: stay floor AND loop/shift scope AND elbow-not-SoT",
                "operational companion: hold the stay without re-opening the flow call",
                "slow resample floor as events: two bookends plus Tcold markers at 4.0 h",
            ],
        },
        "reconstruction_model": {
            "name": "n16_transit_time_velocity_and_mdot",
            "formula": "v_m_s = L_m / dt_s; mdot_kg_s = rho_kg_m3 * A_m2 * v_m_s",
            "parameters": {
                "L_m": 4.00,
                "rho_kg_m3": 720.0,
                "A_m2": 0.250,
                "stay_floor_m_s": 12.50,
                "tripwire_dt_s": 0.320,
            },
            "worked_example": {"dt_s": 0.250, "v_m_s": 16.00, "mdot_kg_s": 2880.0},
            "check": "4.00/0.250 = 16.00 exactly; 720.0*0.250*16.00 = 2880; 7200 s + 14400 s = 21600 s = 4.0 h floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 32.0,
            "decision_window_s": 0.032,
            "code": "gw2.n16_stay_gate",
            "note": "ACCEPT accumulator wins: N-16 velocity evidence overpowers the elbow-trip advocate",
            "decode_rule": "accept-stay if velocity_estimator AND path_norm fire inside the window; trip_advocate is necessary-but-not-sufficient and cannot trip on a frozen elbow",
            "populations": [
                gate_pop("velocity_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("path_norm_core", 64, 1.2, 31.25, w_s),
                gate_pop("loop_margin", 40, 1.0, 50.0, w_s),
                gate_pop("trip_advocate", 40, 0.8, 25.0, w_s),
                gate_pop("accept_latch", 96, 1.8, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "gw2.dt_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 32.0},
                {"check": "gw2.v_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r24-074",
            clock_domain="gw2-n16-sim-relative-ms-t0-2026-07-12T21:00:00Z",
            tags=["n16-transit", "ACCEPT", "ACCEPT", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 075 — helium residual-gas leak HIL, REJECT / MODIFY (vendor-only lead)
# ---------------------------------------------------------------------------
def rec_075():
    assert abs(2.00e-9 * (18.00 - 3.00) - 3.00e-8) < 1e-20
    assert abs(2.00e-9 * (3.20 - 3.00) - 4.00e-10) < 1e-20
    raster = make_raster(
        neurons=16,
        mean_rate_hz=62.5,
        window_ms=40.0,
        seed=20260926,
        source="hc8.rga.dummy",
        target="holmcrag.closeout_core",
        table=[
            {"from": "rga_I", "to": "leak_estimator", "weight": 1.45},
            {"from": "rga_bg", "to": "background_norm_core", "weight": 1.25},
            {"from": "sealvein_q", "to": "vendor_close_advocate", "weight": 0.35},
        ],
        third_factor={
            "modulator": "ach.vendor_leak_conflict",
            "tau_e_s": 1.2,
            "tau_e_ms": 1200.0,
            "eligibility": "pre-post coincidence on leak-class synapses; the conflict modulator depresses close-out links when ion current stays high inside tau_e of a background sample so a Sealvein auto-zero cannot hide 3e-8 mbar L/s",
        },
        channel_prefix="rga.n",
        anchor="HC-8 HIL RGA 40 ms frame at I 18.00 nA / I_bg 3.00 nA (t_s 3600) that reconstructs 3.00e-8 mbar L/s against Sealvein 4.0e-10",
    )
    w_s = 0.040
    events = [
        ev(0.0, "rga.I", 3.20, code="I_NA", units="nA", note="HIL dummy chamber on spare VIM head; not live C-2"),
        ev(600000.0, "rga.bg", 3.00, code="BG_NA", units="nA"),
        ev(900000.0, "recon.Q", 4.00e-10, code="Q_MBAR_L_S", units="mbar_l_s", note="2.00e-9*(3.20-3.00)=4.00e-10 exact"),
        ev(1200000.0, "sealvein.Q", 4.00e-10, code="VENDOR_Q", units="mbar_l_s", note="Sealvein OEM cloud; the only live-chamber leak SoT"),
        ev(1800000.0, "sniff.indep", 0.0, code="INDEP_SNIFF", units="bool", note="zero independent sniffer on live C-2"),
        ev(2400000.0, "rga.I", 9.00, code="I_NA", units="nA"),
        ev(3000000.0, "recon.Q", 1.20e-8, code="Q_MBAR_L_S", units="mbar_l_s", note="2.00e-9*(9.00-3.00)=1.20e-8"),
        ev(3300000.0, "chamber.P", 2.00e-6, code="P_MBAR", units="mbar", note="HIL dummy still in spec on total pressure"),
        ev(3600000.0, "rga.I", 18.00, code="I_NA", units="nA", note="close-out frame; raster sidecar"),
        ev(3600001.2, "rga.bg", 3.00, code="BG_NA", units="nA", note="1.2 ms background-norm after I"),
        ev(3900000.0, "recon.Q", 3.00e-8, code="Q_MBAR_L_S", units="mbar_l_s", note="2.00e-9*(18.00-3.00)=3.00e-8 exact; spec 1.00e-8"),
        ev(4200000.0, "sealvein.Q", 4.00e-10, code="VENDOR_Q", units="mbar_l_s", note="auto-zero subtracted the ion current as background"),
        ev(4800000.0, "sniff.indep", 0.0, code="INDEP_SNIFF", units="bool"),
        ev(5400000.0, "live.C2", 1.0, code="LIVE_SEALED", units="bool", note="live chamber still vendor-only; HIL dummy is not a live witness"),
        ev(6000000.0, "ops.prop", 1.0, code="CLOSE_FURNACE", units="bool", note="furnace tech Brant Mossreel: Sealvein 4e-10, close C-2 and start heat 4419"),
        ev(6600000.0, "gate.close", 1.0, code="REJECT", units="decision", note="lead REJECT: no independent sniffer on live C-2; HIL 3e-8 is not a live SoT"),
        ev(7200000.0, "heat.hold", 1.0, code="HEAT_HELD", units="bool"),
        ev(7800000.0, "sniff.start", 1.0, code="SNIFF_START", units="bool", note="bookend 1 of the 30.0 min spray floor"),
        ev(8700000.0, "spray.mark", 15.0, code="SPRAY_MIN", units="min", note="15 min marker; NW40 flange"),
        ev(9600000.0, "sniff.floor", 1.0, code="SNIFF_FLOOR", units="bool", note="7800 s + 1800 s = 9600 s = 30.0 min"),
        ev(10200000.0, "ops.install", 1.0, code="HANG_SNIFFER_AND_CLOSE", units="bool", note="Mossreel: HIL already 3e-8, hang sniffer and close anyway"),
        ev(10800000.0, "gate.hold", 1.0, code="MODIFY", units="decision", note="companion t2: install portable sniffer on LIVE C-2; still do not close"),
        ev(11400000.0, "sniff.live", 1.0, code="PORTABLE_ON_C2", units="bool"),
        ev(12000000.0, "close.held", 1.0, code="NO_CLOSE", units="bool"),
        ev(12600000.0, "recon.Q", 3.00e-8, code="Q_MBAR_L_S", units="mbar_l_s"),
        ev(13200000.0, "sealvein.Q", 4.00e-10, code="VENDOR_Q", units="mbar_l_s"),
        ev(13800000.0, "hil.notlive", 1.0, code="HIL_NOT_LIVE", units="bool"),
        ev(14400000.0, "chamber.P", 2.00e-6, code="P_MBAR", units="mbar"),
        ev(15000000.0, "heat.hold", 1.0, code="HEAT_HELD", units="bool"),
        ev(15600000.0, "sniff.indep", 1.0, code="INDEP_SNIFF", units="bool", note="portable now on live C-2; close remains a different gate"),
        ev(16200000.0, "rga.I", 18.20, code="I_NA", units="nA"),
        ev(16800000.0, "close.held", 1.0, code="NO_CLOSE", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r24-075-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "HC-HE-2026-0211",
            "domain": "helium_rga_leak_closeout",
            "setting": "Holmcrag vacuum-induction melt HC-8 (invented), live chamber C-2. Hardware-in-the-loop: a dummy head on the spare RGA times the live close-out. Live C-2 has only the sealed Sealvein OEM cloud as a leak SoT; no independent sniffer is installed on the live flange. The HIL dummy is not a live witness. Invented plant. Not e-nose VOD, not QEPAS DGA (r19), not CRDS HF (r15), not TDLAS NH3 (r22), not CEMS.",
            "observables_at_decision": {
                "I_nA": 18.00,
                "I_bg_nA": 3.00,
                "Q_mbar_l_s": 3.00e-8,
                "sealvein_Q": 4.00e-10,
                "independent_sniffer_on_live": 0,
                "spec_Q": 1.00e-8,
            },
            "margin_authority": "HC-8 leak SOP rev C: close C-2 only if two independent leak SoTs agree within a factor of two AND reconstructed Q <= 1.00e-8. A vendor cloud cannot close a furnace. HIL dummy reconstruction is not a live SoT.",
        },
        "proposed_action": {
            "actor": "furnace tech Brant Mossreel, citing Sealvein 4.0e-10 after auto-zero",
            "summary": "close live chamber C-2 and start heat 4419; HIL dummy already quantified the leak",
            "basis_claimed": "Sealvein is the licensed leak SoT and 4e-10 is two decades under spec",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Close-out is refused on the lead. Serialized reconstruction on the HIL dummy: Q = k_ion * (I - I_bg) = 2.00e-9 * (18.00 - 3.00) = 3.00e-8 mbar L/s, three times the 1.00e-8 spec. Live C-2 still has sniff.indep = 0: Sealvein is the only installed leak channel and is vendor-writable (auto-zero subtracted the ion current). SOP rev C requires two independent live SoTs. The HIL dummy cannot substitute for a live sniffer. Ordered: do not close C-2, do not start heat 4419. Do not convert the refusal into a personnel action on Mossreel.",
            "threshold": "close requires independent_sniffer_on_live AND Q<=1.00e-8; neither holds",
            "stated_residuals": "HIL 3.00e-8 is not a live measurement; Sealvein remains the only live channel until a portable sniffer is hung; heat 4419 is delayed",
        },
        "executed_action": {
            "summary": "REJECT at t_s 6600: C-2 not closed; heat held; Sealvein not SoT; Mossreel not referred",
            "tool": "hc8-leak-closeout-gate-cli",
            "observation": "Q 3.00e-8 recomputes from I 18.00 nA and bg 3.00 nA; sniff.indep 0 on live C-2",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3600.0, "event": "RGA I 18.00 nA; raster frame; Q 3.00e-8"},
                {"t_s": 6000.0, "event": "ops proposes close C-2"},
                {"t_s": 6600.0, "event": "REJECT close; vendor-only live SoT"},
                {"t_s": 9600.0, "event": "30.0 min spray floor"},
                {"t_s": 10800.0, "event": "companion MODIFY install-sniffer still-no-close"},
            ],
            "observed_effects": [
                "Q recomputes from the serialized ion-current model at every recon.Q event",
                "a Sealvein-only head would have closed C-2 on 4.0e-10 after auto-zero",
                "lead REJECT is structural (no independent live sniffer) plus HIL reconstruction over spec, not a magnitude fight against 4e-10",
            ],
            "surprises": [
                "chamber total pressure stayed 2.00e-6 mbar; a pressure-only head would have treated in-spec P as a leak license",
            ],
            "new_state": {
                "c2": "open; not closed",
                "heat_4419": "held",
                "sealvein": "not SoT",
                "mossreel": "not referred",
            },
            "latency_ms": 4200000.0,
        },
        "reward_components": reward(
            0.43,
            [
                ("he_leak_reconstruction", 0.15),
                ("vendor_only_lead_reject", 0.14),
                ("no_independent_sniffer", 0.10),
                ("closeout_refused", 0.07),
                ("hil_not_live_witness", -0.03),
            ],
            "scored for a lead REJECT of furnace close-out on vendor-only live leak SoT with no independent sniffer installed; HIL dummy is priced as not a live witness",
        ),
        "meta": meta_common(
            tags=["REJECT", "helium-rga", "vendor-only-lead", "hil"],
            distillation_note="He-leak close-out gate: ion-current reconstruction plus missing live sniffer beats a green vendor auto-zero; HIL dummy is not a live SoT",
        ),
    }
    traj2 = {
        "id": "nelb-r24-075-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "HC-HE-2026-0211-sniffer",
            "domain": "portable_sniffer_install",
            "setting": "Same HC-8 after the lead REJECT and the 30 min spray-map floor. Mossreel proposes hanging the portable sniffer and closing anyway because the HIL dummy already reads 3e-8. Operational quality gate, not a disclosure vote.",
            "observables_at_decision": {
                "sniff_floor_complete": 1,
                "independent_sniffer_on_live": 0,
                "Q_mbar_l_s": 3.00e-8,
                "sealvein_Q": 4.00e-10,
            },
        },
        "proposed_action": {
            "actor": "furnace tech Brant Mossreel",
            "summary": "hang the portable sniffer on live C-2 and close the furnace; HIL already quantified 3e-8",
            "basis_claimed": "the 30 min outage is already paid and the dummy RGA is the same model as live",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Install is accepted, close is not. Ordered: hang the portable sniffer on the LIVE C-2 NW40 flange (not the HIL dummy), keep C-2 open, do not start heat 4419. Close-out is a different gate that still requires the live sniffer to agree with a second SoT inside spec. HIL dummy reconstruction remains not a live witness. Do not convert the modify into a personnel action.",
            "threshold": "install portable on live C-2 AND close==false AND hil_not_substituted",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 10800: portable sniffer on live C-2; close held; heat held",
            "tool": "hc8-sniffer-install-gate-cli",
            "observation": "sniff.live 1; close.held 1; recon.Q still 3.00e-8; Sealvein not SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 9600.0, "event": "30.0 min spray floor marked"},
                {"t_s": 10200.0, "event": "hang-and-close proposed"},
                {"t_s": 10800.0, "event": "MODIFY install-sniffer; still no close"},
            ],
            "observed_effects": [
                "portable sniffer is now on live C-2; close remains refused",
                "lead REJECT was not re-opened as a close",
            ],
            "new_state": {
                "portable_sniffer": "on live C-2",
                "close": "not taken",
                "heat_4419": "held",
            },
            "latency_ms": 1200000.0,
        },
        "reward_components": reward(
            0.33,
            [
                ("portable_sniffer_install", 0.13),
                ("spray_floor", 0.11),
                ("still_no_close", 0.09),
                ("hil_spare_not_substituted", 0.03),
                ("hold_cost", -0.03),
            ],
            "operational modify: missing live sniffer is filled without converting the REJECT into a close",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "vendor-only-telemetry", "hil"]),
    }
    return {
        "id": "nelb-r24-075",
        "spike_events": events,
        "language_view": {
            "description": "Holmcrag VIM HC-8 HIL dummy RGA. Ion current 18.00 nA against 3.00 nA background reconstructs 3.00e-8 mbar L/s while Sealvein vendor cloud still shows 4.0e-10 after auto-zero. Live C-2 has no independent sniffer. The gate REJECTs close-out on the lead (vendor-only live SoT; HIL dummy is not a live witness). Companion t2 MODIFYs hang-and-close into install-portable-on-live still-no-close after a 30.0 min spray floor serialized in the stream.",
            "trajectory": traj,
            "trajectory_sniffer_install": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "rga.I / rga.bg": "ion current and background; leak inputs",
                "recon.Q": "serialized helium leak rate",
                "sealvein.Q / sniff.indep / live.C2 / hil.notlive": "vendor cloud vs missing live sniffer vs HIL-is-not-live",
                "ops.prop / gate.close / ops.install / gate.hold": "close proposal, lead REJECT, hang-and-close, companion MODIFY",
                "sniff.start / sniff.floor / spray.mark": "slow spray-map floor bookends plus 15 min marker",
            },
            "temporal_motifs": [
                "vendor-green while HIL-over-spec: sealvein.Q 4e-10 next to recon.Q 3e-8",
                "reconstruction as event: recon.Q 3.00e-8 equals 2.00e-9*(18.00-3.00)",
                "REJECT then operational MODIFY: gate.close at 6600 s, gate.hold at 10800 s",
                "tight RGA pair: rga.I then rga.bg +1.2 ms at the raster frame",
                "slow floor in-stream: sniff.start 7800 s, sniff.floor 9600 s (30.0 min)",
            ],
            "language_to_spike_mapping": "'Sealvein is 4e-10' = sealvein.Q 4e-10 with sniff.indep 0; '3e-8 leak' = recon.Q 3e-8; 'do not close' = gate.close REJECT; 'install sniffer, still no close' = gate.hold MODIFY plus close.held",
            "why_high_value": "New helium residual-gas leak family (not e-nose, not QEPAS, not CRDS, not TDLAS r22, not CEMS). Harvests r19 leftover: vendor-only as a *lead* REJECT on a plant with no independent live witness (HIL dummy is declared not a live SoT). Companion t2 installs the missing sniffer without converting the REJECT into a close. sim_or_real=hil.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 20260926, "stream_note": "stream amplitudes authored (nA, mbar L/s, mbar, min, bool)"},
                "draw_order": "raster per neuron id order with adaptation/noise",
                "thinning": "RGA dwell exists at 8 Hz; stream keeps 4 I points; spray map keeps 3 of 30 min",
                "refractory_floors_ms": {
                    "rga.I": 60000,
                    "rga.bg": 1.2,
                    "recon.Q": 60000,
                    "sealvein.Q": 60000,
                    "sniff.indep": 60000,
                    "chamber.P": 60000,
                    "live.C2": 60000,
                    "ops.prop": 60000,
                    "gate.close": 60000,
                    "heat.hold": 60000,
                    "sniff.start": 60000,
                    "spray.mark": 60000,
                    "sniff.floor": 60000,
                    "ops.install": 60000,
                    "gate.hold": 60000,
                    "sniff.live": 60000,
                    "close.held": 60000,
                    "hil.notlive": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-02-11T22:00:00Z HIL campaign start",
            },
            "distillation_targets": [
                "He-leak reconstruction head: Q = k_ion * (I - I_bg)",
                "vendor-only lead REJECT: missing independent live sniffer is sufficient without a magnitude fight",
                "HIL dummy is not a live witness",
                "operational companion: install the missing sniffer without converting REJECT into close",
                "slow spray floor as events: two bookends plus a 15 min marker at 30.0 min",
            ],
        },
        "reconstruction_model": {
            "name": "rga_helium_leak_from_ion_current",
            "formula": "Q_mbar_l_s = k_ion_mbar_l_s_per_nA * (I_nA - I_bg_nA)",
            "parameters": {
                "k_ion_mbar_l_s_per_nA": 2.00e-9,
                "spec_Q_mbar_l_s": 1.00e-8,
                "spray_floor_min": 30.0,
            },
            "worked_example": {"I_nA": 18.00, "I_bg_nA": 3.00, "Q_mbar_l_s": 3.00e-8},
            "check": "2.00e-9 * (18.00 - 3.00) = 3.00e-8 exactly; 7800 s + 1800 s = 9600 s = 30.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.040,
            "code": "hc8.leak_closeout_gate",
            "note": "REJECT accumulator wins: leak-rate and missing-sniffer evidence overpower the vendor close-continue advocate (weight 0.35)",
            "decode_rule": "reject-close if leak_estimator AND background_norm fire; vendor_close_advocate is below threshold by design",
            "populations": [
                gate_pop("leak_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("background_norm", 64, 1.3, 31.25, w_s),
                gate_pop("vendor_close_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("reject_latch", 96, 1.8, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "hc8.rga_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 40.0},
                {"check": "hc8.ion_scorer", "neurons": 40, "mean_rate_hz": 62.5, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r24-075",
            clock_domain="hc8-rga-hil-relative-ms-t0-2026-02-11T22:00:00Z",
            tags=["helium-rga", "REJECT", "MODIFY", "vendor-only-lead", "hil", "operational-t2"],
        ),
    }


def walk_banned(obj, path=""):
    hits = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{path}.{k}" if path else k
            nk = str(k).casefold().replace("-", "_").replace(" ", "_")
            if nk in HIDDEN or nk in {"thought", "scratch", "inner_monologue", "chain_of_thought"}:
                hits.append(p)
            hits.extend(walk_banned(v, p))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            hits.extend(walk_banned(v, f"{path}[{i}]"))
    return hits


def local_checks(records):
    ids = []
    decisions = []
    sims = []
    for rec in records:
        hits = walk_banned(rec)
        if hits:
            raise RuntimeError(f"banned keys {hits}")
        blob = json.dumps(rec, ensure_ascii=False, allow_nan=False)
        if "training_ready" in blob:
            raise RuntimeError("training_ready claimed")
        if '"provenance"' in blob:
            raise RuntimeError("provenance object present")
        ids.append(rec["id"])
        lv = rec["language_view"]
        ids.append(lv["trajectory"]["id"])
        for k, v in lv.items():
            if k.startswith("trajectory") and k != "trajectory" and isinstance(v, dict) and "id" in v:
                ids.append(v["id"])
                sim2 = v["state"]["sim_or_real"]
                if sim2 not in {"designed", "simulated", "hil"}:
                    raise RuntimeError(sim2)
                if v["safety_decision"]["decision"] not in {"ACCEPT", "MODIFY", "REJECT"}:
                    raise RuntimeError(v["safety_decision"]["decision"])
        n = len(rec["spike_events"])
        if not (5 <= n <= 40):
            raise RuntimeError(f"{rec['id']} events {n}")
        gdec = rec["gate_snn"]["decision"]
        tdec = lv["trajectory"]["safety_decision"]["decision"]
        if gdec != tdec:
            raise RuntimeError(f"gate {gdec} != traj {tdec}")
        decisions.append(tdec)
        for k, v in lv.items():
            if k.startswith("trajectory") and isinstance(v, dict) and "safety_decision" in v:
                if k != "trajectory":
                    decisions.append(v["safety_decision"]["decision"])
        rast = rec["raster"]
        exp = int(round(rast["neurons"] * rast["mean_rate_hz"] * rast["window_s"]))
        if abs(rast["spikes"] - exp) > 0:
            raise RuntimeError("raster budget")
        if abs(rast["energy_pJ"] - rast["spikes"] * 23) > 1e-6:
            raise RuntimeError("energy pJ")
        if abs(rast["energy_uJ"] - rast["spikes"] * 23e-6) > 1e-9:
            raise RuntimeError("energy uJ")
        isi = rast["isi_count_identity"]
        if isi["isi_total"] != isi["spikes"] - isi["distinct_active_neurons"]:
            raise RuntimeError("ISI identity")
        if sum(b["count"] for b in rast["isi_histogram"]) != isi["isi_total"]:
            raise RuntimeError("ISI hist sum")
        if "isi_histogram" not in rast:
            raise RuntimeError("missing isi_histogram")
        tf = rast["routing"]["third_factor"]
        if abs(tf["tau_e_ms"] / 1000.0 - tf["tau_e_s"]) > 1e-9:
            raise RuntimeError("tau pair")
        sim = lv["trajectory"]["state"]["sim_or_real"]
        if sim not in {"designed", "simulated", "hil"}:
            raise RuntimeError(sim)
        sims.append(sim)
        gc = rec["gate_compute"]
        sp_sum = sum(c["spikes"] for c in gc["per_check"])
        if sp_sum != gc["total_spikes"]:
            raise RuntimeError("gate_compute spikes")
        if abs(gc["total_energy_pJ"] - sp_sum * 23) > 1e-6:
            raise RuntimeError("gate_compute pJ")
        dw = rec["gate_snn"]["decision_window_s"]
        for pop in rec["gate_snn"]["populations"]:
            exp_p = int(round(pop["neurons"] * pop["mean_rate_hz"] * dw))
            if pop["spikes"] != exp_p:
                raise RuntimeError(f"gate_snn pop {pop['name']}")
        for e in rec["spike_events"]:
            if any(k in e for k in ("t_ms", "burst_id", "sequence_id", "event_order", "causal_group")):
                raise RuntimeError("forbidden event key")
        rights = rec["meta"]["rights"]
        if rights.get("linear_issue") != "RM-793":
            raise RuntimeError("RM-793 missing")
        if len(rights) != 15:
            raise RuntimeError(f"rights {len(rights)}")
    if len(ids) != len(set(ids)):
        raise RuntimeError(f"dup ids {ids}")
    if set(sims) != {"designed", "simulated", "hil"}:
        raise RuntimeError(f"sim mix {sims}")
    if set(decisions) != {"ACCEPT", "MODIFY", "REJECT"}:
        raise RuntimeError(f"decision mix {decisions}")
    print("local_checks ok", [r["id"] for r in records], "ids", len(ids))
    print("decisions", decisions, "sims", sims)


def repo_validate(records):
    from check_records import FactoryStaging, check_jsonl
    from curate_bridge import curate_record, raster_status
    from verify_execution import verify_batch_for_frontier

    errs, warns, kinds, n = check_jsonl(
        BATCH, "batch-r24.jsonl", staging=FactoryStaging(enabled=True)
    )
    print("check_jsonl", {"errors": len(errs), "warnings": len(warns), "kinds": kinds, "n": n})
    for e in errs:
        print("ERROR", e)
    for w in warns:
        print("WARN", w)
    if errs or warns:
        raise RuntimeError("check_jsonl failed")

    for i, rec in enumerate(records, 1):
        st = raster_status(rec, require_raster=True, require_routing_table=True)
        print(
            rec["id"],
            "raster_valid",
            st["raster_valid"],
            "gate_snn_valid",
            st["gate_snn_valid"],
            "reasons",
            st["reason_codes"],
            "isi",
            rec["raster"]["isi_count_identity"],
        )
        if not st["raster_valid"] or not st["gate_snn_valid"] or st["reason_codes"]:
            raise RuntimeError(f"raster_status {rec['id']} {st}")
        blob = json.dumps(rec, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
        import hashlib

        h = hashlib.sha256(blob.encode("utf-8")).hexdigest()
        dec = curate_record(
            rec,
            source_path="batch-r24.jsonl",
            source_line=i,
            source_hash=h,
            require_raster=True,
            require_routing_table=True,
        )
        reasons = dec.manifest.get("reason_codes")
        print(rec["id"], "curate", dec.action, reasons)
        if dec.action != "retain":
            raise RuntimeError(f"curate {rec['id']} {dec.action} {reasons}")

    counts, findings, blocked = verify_batch_for_frontier(BATCH, strict=True)
    print("frontier", counts, "blocked", blocked, "findings", findings)
    if blocked or counts["verified"] != 3:
        raise RuntimeError(f"frontier {counts} {findings}")


def main():
    records = [rec_073(), rec_074(), rec_075()]
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
    repo_validate(records)


if __name__ == "__main__":
    main()
