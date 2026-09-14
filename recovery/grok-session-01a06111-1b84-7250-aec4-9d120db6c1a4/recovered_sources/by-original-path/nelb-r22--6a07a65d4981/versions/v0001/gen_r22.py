#!/usr/bin/env python3
"""Generate NELB round-22 research-only bridge pairs (do not write outputs/raw/)."""

from __future__ import annotations

import json
import math
import random
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

OUT_DIR = Path("/tmp/nelb-r22")
BATCH = OUT_DIR / "batch-r22.jsonl"
NOTES = OUT_DIR / "NOTES-r22.md"
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
        "round": 22,
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
# Record 067 — electrical capacitance tomography, designed, MODIFY
# ---------------------------------------------------------------------------
def rec_067():
    raster = make_raster(
        neurons=20,
        mean_rate_hz=40.0,
        window_ms=40.0,
        seed=20260967,
        source="rv11.caprix.ect",
        target="brackfen.holdup_core",
        table=[
            {"from": "electrode_c_n", "to": "holdup_reconstructor", "weight": 1.40},
            {"from": "riser_dp", "to": "plug_identity_core", "weight": 1.15},
            {"from": "holdveil_empty_map", "to": "blast_advocate", "weight": 0.50},
        ],
        third_factor={
            "modulator": "na.plug_holdup_salience",
            "tau_e_s": 1.6,
            "tau_e_ms": 1600.0,
            "eligibility": "pre-post coincidence on riser-plug synapses; the holdup modulator enables potentiation only while reconstructed alpha and riser dP are co-active inside tau_e",
        },
        channel_prefix="ect.n",
        anchor="Caprix-16 40 ms frame at electrode-07 C=3.18 pF (t_s 840); reconstructed holdup 0.700 first exceeds the 0.55 plug trip",
    )
    w_s = 0.04
    events = [
        ev(0.0, "cap.air", 0.80, code="C_AIR", units="pF", note="empty-pipe calibration of Caprix-16 ring"),
        ev(60000.0, "feed.tph", 4.20, code="FEED", units="t_h"),
        ev(120000.0, "blower.bar", 0.85, code="BLOWER", units="bar"),
        ev(180000.0, "cap.ch07", 1.14, code="C_PF", units="pF", note="electrode 07; dilute conveying"),
        ev(240000.0, "alpha.recon", 0.100, code="HOLDUP", units="frac", note="(1.14-0.80)/3.40=0.100"),
        ev(300000.0, "dp.kpa", 5.2, code="DP", units="kPa"),
        ev(360000.0, "vend.alpha", 0.08, code="CLOUD", units="frac", note="Holdveil last-good empty map"),
        ev(420000.0, "cap.ch07", 1.48, code="C_PF", units="pF"),
        ev(480000.0, "alpha.recon", 0.200, code="HOLDUP", units="frac", note="(1.48-0.80)/3.40=0.200"),
        ev(540000.0, "dp.kpa", 8.1, code="DP", units="kPa"),
        ev(600000.0, "cap.ch07", 1.65, code="C_PF", units="pF"),
        ev(660000.0, "alpha.recon", 0.250, code="HOLDUP", units="frac", note="(1.65-0.80)/3.40=0.250"),
        ev(720000.0, "dp.kpa", 11.4, code="DP", units="kPa"),
        ev(780000.0, "feed.tph", 4.18, code="FEED_STILL", units="t_h", note="recycle looks like flow"),
        ev(794000.0, "cap.ch07", 1.82, code="C_PF", units="pF"),
        ev(800000.0, "alpha.recon", 0.300, code="HOLDUP", units="frac", note="(1.82-0.80)/3.40=0.300"),
        ev(840000.0, "cap.ch07", 3.18, code="C_PLUG", units="pF", note="raster sidecar is this 40 ms frame"),
        ev(840001.2, "ect.pkt", 1.18, code="ELECTRODE", units="norm", note="electrode packet; amplitude before adaptation"),
        ev(840002.5, "ect.pkt", 0.97, code="ELECTRODE", units="norm", note="same-channel refractory 1.3 ms; adapted 0.82x plus noise"),
        ev(840003.8, "ect.pkt", 0.79, code="ELECTRODE", units="norm", note="third packet; adapted"),
        ev(846000.0, "alpha.recon", 0.700, code="HOLDUP", units="frac", note="(3.18-0.80)/3.40=0.700 exact"),
        ev(852000.0, "dadt.recon", 0.010, code="D_ALPHA_DT", units="per_s", note="(0.700-0.300)/40=0.010 exact"),
        ev(858000.0, "dp.kpa", 22.0, code="DP_PLUG", units="kPa"),
        ev(864000.0, "vend.alpha", 0.08, code="CLOUD_STALE", units="frac"),
        ev(900000.0, "ops.prop", 1.0, code="N2_BLAST_6BAR", units="bool", note="night ops: fire 6 bar N2 to clear the supposed empty hang"),
        ev(912000.0, "gate.ect", 1.0, code="MODIFY", units="decision"),
        ev(924000.0, "blower.off", 1.0, code="BLOWER_STOP", units="bool"),
        ev(936000.0, "isol.rv11", 1.0, code="SECTION3_ISO", units="bool"),
        ev(1800000.0, "alpha.recon", 0.410, code="HOLDUP", units="frac"),
        ev(2100000.0, "alpha.recon", 0.160, code="HOLDUP", units="frac"),
        ev(2160000.0, "dp.kpa", 6.2, code="DP", units="kPa"),
        ev(2220000.0, "feed.tph", 2.10, code="RESUME_CAP", units="t_h", note="50 percent feeder cap"),
        ev(2280000.0, "gate.exec", 1.0, code="ACCEPT", units="decision", note="companion t2: stop/isolate/resume-cap completed"),
        ev(2340000.0, "vend.freeze", 1.0, code="CLOUD_FROZEN", units="bool"),
        ev(2400000.0, "blower.bar", 0.42, code="BLOWER_HALF", units="bar"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r22-067-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "BF-ECT-2026-0902",
            "domain": "ect_pneumatic_riser_holdup",
            "setting": "Brackfen Powders, HDPE conveying riser RV-11 (invented). Caprix-16 16-electrode ECT ring at 2.4 m, plant-owned dP cell across section 3. Holdveil cloud is the vendor empty-map. Designed campaign. Not DAS/BOTDA fiber, not QCM-D mass, not muon opacity.",
            "observables_at_decision": {
                "c_meas_pF": 3.18,
                "c_air_pF": 0.80,
                "c_packed_pF": 4.20,
                "alpha_recon": 0.700,
                "d_alpha_dt_per_s": 0.010,
                "dp_kpa": 22.0,
                "vend_alpha": 0.08,
                "feed_tph": 4.18,
            },
            "margin_authority": "RV-11 plug SOP rev C: if reconstructed alpha >= 0.55 AND d_alpha/dt >= 0.008 /s AND riser dP >= 18 kPa, N2 blast and continued conveying are forbidden even if the vendor empty-map still reads dilute",
        },
        "proposed_action": {
            "actor": "night ops, citing Holdveil 0.08 holdup and a live 4.18 t/h feeder",
            "summary": "fire 6 bar N2 blast into section 3 and keep the blower at 0.85 bar; treat electrode-07 rise as a sticky-wall film",
            "basis_claimed": "Holdveil empty-map is the conveying SoT and it still reads 0.08; feeder has not lost mass balance",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "The blast is refused, not the riser. SOP rev C is conjunctive: reconstructed holdup is 0.700 ((3.18-0.80)/3.40, serialized), d_alpha/dt is 0.010 /s over 40 s, and plant dP is 22.0 kPa, all over the 0.55 / 0.008 / 18 floors, while Holdveil still shows 0.08 because its last-good empty map is write-ACL locked. A 6 bar N2 blast on a 0.700 packed plug would compact it. Ordered: blower stop, isolate section 3, hold until alpha < 0.20 AND dP < 8 kPa, then resume at 2.10 t/h not 4.20. An empty-map cannot substitute for the ECT reconstruction.",
            "threshold": "alpha>=0.55 AND d_alpha_dt>=0.008 AND dp_kpa>=18 => forbid blast and full conveying",
            "stated_residuals": "about 1.4 t deferred on the night shift; electrode 07 is one of 16 and is not a release condition by itself",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 912: blower stop and section-3 isolate latched; alpha 0.700 -> 0.160 by t_s 2100",
            "tool": "rv11-ect-holdup-gate-cli",
            "observation": "blower 0 A at t_s 924; isolate confirmed; Holdveil frozen; no N2 fired",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 800.0, "event": "alpha 0.300; last dilute reconstruction"},
                {"t_s": 840.0, "event": "C=3.18 pF; raster frame captured"},
                {"t_s": 846.0, "event": "alpha 0.700; d_alpha/dt 0.010 /s; dP 22 kPa"},
                {"t_s": 912.0, "event": "MODIFY: blower stop plus isolate"},
                {"t_s": 2280.0, "event": "companion execution ACCEPT; resume 2.10 t/h"},
            ],
            "observed_effects": [
                "reconstructed holdup recomputes from the serialized (C-C_air)/(C_packed-C_air) model at every alpha.recon event",
                "Holdveil never left 0.08, so an empty-map head would have ACCEPTed the blast",
                "stop kept alpha falling to 0.160; the packed plug was never N2-compacted",
            ],
            "surprises": [
                "feeder 4.18 t/h was recycle around the plug, not throughput, so mass-balance was not a substitute holdup detector",
            ],
            "new_state": {
                "rv11": "resume 2.10 t/h pending alpha < 0.12",
                "blower": "latched at 0.42 bar",
                "reconstruction_model": "discharged as an on-record calculator, not a referenced envelope",
            },
            "latency_ms": 12000.0,
        },
        "reward_components": reward(
            0.42,
            [
                ("ect_holdup_reconstruction", 0.14),
                ("conjunctive_stop", 0.12),
                ("empty_map_nonsubstitution", 0.10),
                ("n2_blast_refused", 0.08),
                ("throughput_deferral_cost", -0.02),
            ],
            "scored for refusing an N2 blast on a recomputable ECT holdup while the vendor empty-map looked dilute; throughput_deferral_cost prices the 2.10 t/h cap",
        ),
        "meta": meta_common(
            tags=["MODIFY", "ect-capacitance-tomography", "serialized-reconstruction", "operational-companion"],
            distillation_note="ECT gate: serialized (C-C_air)/(C_packed-C_air) holdup plus dP beats a stale empty-map; companion t2 is the stop/isolate execution, not a governance vote",
        ),
    }
    traj2 = {
        "id": "nelb-r22-067-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "BF-ECT-2026-0902-exec",
            "domain": "riser_stop_isolate_execution",
            "setting": "Same RV-11 after the MODIFY. This companion is the operational blower-stop, section-3 isolate, and 2.10 t/h resume, not a second policy vote.",
            "observables_at_decision": {
                "blower_stop": True,
                "section3_isolated": True,
                "alpha_recon": 0.700,
            },
        },
        "proposed_action": {
            "actor": "riser controller following the MODIFY",
            "summary": "execute blower stop and section-3 isolate, then resume at 2.10 t/h when alpha < 0.20 and dP < 8 kPa",
            "basis_claimed": "MODIFY requirements are fully specified and in-envelope for the blower and slide-gate loops",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "The execution envelope is intact: blower ramp 0.12 bar/s is under the 0.20 bar/s surge limit, isolate interlock is confirmed, and the resume condition (alpha < 0.20 AND dP < 8 kPa) is the same conjunctive pair the MODIFY used. ACCEPT the sequence. Do not restore 4.20 t/h tonight; 2.10 t/h is the cap until alpha < 0.12. Do not fire N2.",
            "threshold": "blower_ramp<=0.20 bar/s AND isolated AND resume_cap_tph=2.10",
        },
        "executed_action": {
            "summary": "blower stop latched at t_s 924; isolate at 936; resume 2.10 t/h at t_s 2220 after alpha 0.160 and dP 6.2",
            "tool": "rv11-stop-exec",
            "observation": "no N2; alpha 0.160; feeder 2.10 not 4.20",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 924.0, "event": "blower stop latched"},
                {"t_s": 936.0, "event": "section-3 isolate confirmed"},
                {"t_s": 2220.0, "event": "resume 2.10 t/h after alpha 0.160"},
            ],
            "observed_effects": [
                "alpha 0.700 -> 0.160 without an N2 compact",
                "resume stopped at 2.10 t/h as capped; 4.20 not re-entered",
            ],
            "new_state": {"rv11_feed_tph": 2.10, "resume_cap_tph": 2.10},
            "latency_ms": 12000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("envelope_respect", 0.12),
                ("conjunctive_resume", 0.10),
                ("blower_latched_off", 0.08),
                ("blast_not_reentered", 0.06),
                ("hold_time_cost", -0.02),
            ],
            "operational execution gate: the companion does the stop rather than re-arguing the holdup call",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "riser-isolate"]),
    }
    return {
        "id": "nelb-r22-067",
        "spike_events": events,
        "language_view": {
            "description": "HDPE pneumatic riser RV-11 at Brackfen Powders. Caprix-16 ECT reconstructs holdup 0.700 from electrode-07 3.18 pF while Holdveil still publishes 0.08 from a frozen empty-map and the feeder still looks like 4.18 t/h. The gate MODIFYs to a blower stop plus section-3 isolate and refuses a 6 bar N2 blast; a companion execution ACCEPT runs the stop and resumes only to 2.10 t/h. The holdup model is serialized so every alpha.recon amplitude recomputes from C.",
            "trajectory": traj,
            "trajectory_riser_stop_isolate_execution": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "cap.ch07 / cap.air": "ECT electrode-07 and empty-pipe calibration in pF",
                "alpha.recon / dadt.recon": "serialized holdup and its 40 s derivative; amplitudes are the model outputs",
                "dp.kpa": "plant-owned riser dP; independent of Holdveil",
                "vend.alpha": "vendor empty-map; the denial channel that stays at 0.08",
                "feed.tph / blower.bar": "feeder and blower; recycle can look like flow",
                "ops.prop / gate.ect / gate.exec": "proposal, MODIFY, companion ACCEPT",
                "blower.off / isol.rv11": "execution channels for the operational companion",
            },
            "temporal_motifs": [
                "empty-map-healthy while ECT-sick: vend.alpha 0.08 adjacent to alpha.recon 0.700",
                "reconstruction as event: alpha.recon 0.700 equals (3.18-0.80)/3.40",
                "MODIFY then operational ACCEPT: gate.ect at 912 s, gate.exec at 2280 s",
                "adapted electrode triplet at 1.3 ms spacing encodes the plug packet at raster scale",
            ],
            "language_to_spike_mapping": "'Holdveil looks dilute' = vend.alpha 0.08; '0.700 holdup' = alpha.recon 0.700 at C=3.18 pF; 'forbid blast' = gate.ect MODIFY; 'execute the stop' = blower.off then companion ACCEPT",
            "why_high_value": "New electrical-capacitance-tomography family (not r4 DAS phi-OTDR, not r14 BOTDA, not r17 muon opacity). Serializes a holdup reconstruction that a vendor empty-map cannot see. Companion t2 is operational execution, not a governance vote.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 20260967, "stream_note": "stream amplitudes are authored constants (pF, frac, kPa, t/h) plus ect.pkt adaptation 0.82**k"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "16 ECT electrodes exist; stream keeps ch07; alpha.recon keeps 7 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "cap.air": 60000,
                    "feed.tph": 60000,
                    "blower.bar": 60000,
                    "cap.ch07": 14000,
                    "alpha.recon": 60000,
                    "dp.kpa": 60000,
                    "vend.alpha": 60000,
                    "ect.pkt": 0.8,
                    "dadt.recon": 60000,
                    "ops.prop": 60000,
                    "gate.ect": 60000,
                    "blower.off": 60000,
                    "isol.rv11": 60000,
                    "gate.exec": 60000,
                    "vend.freeze": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-04-11T02:20:00Z conveying commit",
            },
            "distillation_targets": [
                "serialized ECT holdup head: (C-C_air)/(C_packed-C_air)",
                "conjunctive SOP head: alpha AND d_alpha/dt AND dP, never empty-map substitution",
                "operational companion: execute the stop without re-opening the plug call",
            ],
        },
        "reconstruction_model": {
            "name": "ect_linear_holdup",
            "formula": "alpha = (C_pF - C_air) / (C_packed - C_air); d_alpha_dt = (alpha_now - alpha_prev) / dt_s",
            "parameters": {
                "C_air_pF": 0.80,
                "C_packed_pF": 4.20,
                "denom_pF": 3.40,
                "dt_s": 40.0,
                "alpha_trip": 0.55,
                "dadt_trip": 0.008,
                "dp_trip_kpa": 18.0,
            },
            "worked_example": {
                "C_pF": 3.18,
                "alpha": 0.700,
                "alpha_prev": 0.300,
                "d_alpha_dt_per_s": 0.010,
            },
            "check": "(3.18-0.80)/3.40=0.700; (1.82-0.80)/3.40=0.300; (0.700-0.300)/40=0.010",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.04,
            "code": "rv11.ect_holdup_gate",
            "note": "MODIFY accumulator wins: ECT holdup and dP overpower the empty-map advocate",
            "populations": [
                gate_pop("ect_holdup_evidence", 80, 1.4, 50.0, w_s),
                gate_pop("dp_plug_evidence", 64, 1.1, 31.25, w_s),
                gate_pop("empty_map_advocate", 48, 0.9, 25.0, w_s),
                gate_pop("modify_accumulator", 96, 1.6, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                gc_check("rv11.holdup_scorer", 128, 31.25, 40.0),
                gc_check("rv11.dp_scorer", 80, 25.0, 40.0),
            ]
        ),
        "meta": meta_common(
            id="nelb-r22-067",
            clock_domain="bf-ect-campaign-relative-ms-t0-2026-04-11T02:20:00Z",
            tags=["ect-capacitance-tomography", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 068 — TDLAS NH3 slip, hil, REJECT
# ---------------------------------------------------------------------------
def rec_068():
    raster = make_raster(
        neurons=25,
        mean_rate_hz=40.0,
        window_ms=32.0,
        seed=20260968,
        source="ar2.niteline.tdlas",
        target="ashrill.slip_gate",
        table=[
            {"from": "i0_photodiode", "to": "beer_rezero", "weight": 1.45},
            {"from": "doas_ec_witness", "to": "slip_identity_core", "weight": 1.20},
            {"from": "vapetrace_raw", "to": "esd_advocate", "weight": 0.55},
        ],
        third_factor={
            "modulator": "da.window_fouling_error",
            "tau_e_s": 0.8,
            "tau_e_ms": 800.0,
            "eligibility": "pre-post coincidence on slip-trip synapses; the fouling modulator depresses raw-ppm-to-ESD links when photodiode I0 and DOAS/EC witnesses disagree with the stored I0 inside tau_e",
        },
        channel_prefix="tdl.n",
        anchor="Niteline-2f 32 ms frame at I=0.780 (t_s 18.000) where stored-I0 Beer-Lambert reports 12.42 ppm against photodiode I0 0.820",
    )
    w_s = 0.032
    i0_stored = 1.000
    i_now = 0.780
    i0_pd = 0.820
    sigma_l = 0.020
    nh3_raw = round(math.log(i0_stored / i_now) / sigma_l, 2)  # 12.42
    nh3_true = round(math.log(i0_pd / i_now) / sigma_l, 2)  # 2.50
    events = [
        ev(0.0, "tdl.i0", 1.000, code="I0_STORED", units="norm", note="last zero; Vapetrace still uses this"),
        ev(2000.0, "tdl.i", 0.960, code="I_TRANS", units="norm"),
        ev(4000.0, "nh3.raw", 2.04, code="PPM_RAW", units="ppm", note="ln(1.000/0.960)/0.020=2.04"),
        ev(6000.0, "doas.ppm", 2.10, code="UV_DOAS", units="ppm"),
        ev(8000.0, "ec.ppm", 2.00, code="EC_NH3", units="ppm"),
        ev(10000.0, "hil.bot", 2.00, code="BOTTLE", units="ppm", note="HIL bypass bottle; plant-owned"),
        ev(12000.0, "win.pd", 0.990, code="I0_PHOTO", units="norm"),
        ev(14000.0, "scr.t", 478.0, code="T_K", units="K"),
        ev(15000.0, "scr.o2", 3.2, code="O2_PCT", units="pct"),
        ev(16000.0, "win.pd", 0.820, code="I0_DROP", units="norm", note="ammonium-sulfate film on the cell window"),
        ev(18000.0, "tdl.i", 0.780, code="I_TRANS", units="norm", note="raster sidecar is this 32 ms frame"),
        ev(18001.0, "tdl.pkt", 0.88, code="I_SHOT", units="norm", note="transmission packet; amplitude before adaptation"),
        ev(18002.2, "tdl.pkt", 0.72, code="I_SHOT", units="norm", note="same-channel refractory 1.2 ms; adapted 0.82x plus noise"),
        ev(18003.5, "tdl.pkt", 0.59, code="I_SHOT", units="norm", note="third I shot; adapted"),
        ev(20000.0, "nh3.raw", nh3_raw, code="PPM_RAW", units="ppm", note="ln(1.000/0.780)/0.020=12.42"),
        ev(22000.0, "nh3.true", nh3_true, code="PPM_REZERO", units="ppm", note="ln(0.820/0.780)/0.020=2.50"),
        ev(24000.0, "doas.ppm", 2.40, code="UV_DOAS", units="ppm"),
        ev(26000.0, "ec.ppm", 2.30, code="EC_NH3", units="ppm"),
        ev(28000.0, "vap.cloud", nh3_raw, code="VENDOR_PPM", units="ppm"),
        ev(30000.0, "ops.prop", 1.0, code="ESD_TRIP", units="bool", note="night ops: trip AR-2 on 12.42 ppm NH3 slip"),
        ev(32000.0, "turb.load", 0.92, code="LOAD", units="frac"),
        ev(36000.0, "gate.tdl", 1.0, code="REJECT", units="decision"),
        ev(40000.0, "esd.lock", 1.0, code="ESD_BLOCKED", units="bool"),
        ev(48000.0, "cell.iso", 1.0, code="CELLS_ISO", units="bool"),
        ev(60000.0, "win.wash", 1.0, code="WINDOW_WASH", units="bool"),
        ev(72000.0, "gate.iso", 1.0, code="MODIFY", units="decision", note="companion t2: isolate cell, wash window, hold on DOAS"),
        ev(84000.0, "tdl.i0", 0.980, code="I0_AFTER_WASH", units="norm"),
        ev(96000.0, "nh3.true", 2.48, code="PPM_REZERO", units="ppm"),
        ev(108000.0, "doas.ppm", 2.38, code="UV_DOAS", units="ppm"),
        ev(120000.0, "hil.bot", 2.00, code="BOTTLE", units="ppm"),
        ev(132000.0, "vap.freeze", 1.0, code="I0_FROZEN", units="bool"),
        ev(144000.0, "gate.tdl", 1.0, code="REJECT_HELD", units="decision"),
        ev(156000.0, "ec.ppm", 2.28, code="EC_NH3", units="ppm"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r22-068-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "AR-TDL-2026-0902",
            "domain": "tdlas_nh3_slip_scr",
            "setting": "Ashrill CHP unit AR-2, SCR duct (invented). Niteline-2f 1512 nm TDLAS across a 1.00 m cell. Hardware-in-the-loop: the cell also views a 2.00 ppm NH3 bottle on a plant-owned bypass while live duct light is on. Vapetrace cloud still uses stored I0=1.000 from last zero. Plant-owned window photodiode, UV DOAS, and EC cell cannot be written by Vapetrace. Not CRDS cavity-ring-down (r15), not CEMS NDIR (r04), not SAW.",
            "observables_at_decision": {
                "i0_stored": 1.000,
                "i_trans": 0.780,
                "i0_photodiode": 0.820,
                "nh3_raw_ppm": nh3_raw,
                "nh3_true_ppm": nh3_true,
                "doas_ppm": 2.40,
                "ec_ppm": 2.30,
                "hil_bottle_ppm": 2.00,
                "trip_ppm": 8.00,
            },
            "margin_authority": "AR-2 NH3 ESD requires reconstructed NH3_true >= 8.00 ppm AND DOAS >= 8.00 AND EC >= 8.00. A vendor raw ppm that still uses a stored I0 cannot substitute.",
        },
        "proposed_action": {
            "actor": "night ops, citing Vapetrace 12.42 ppm as a slip trip",
            "summary": "ESD-trip AR-2 and dump the SCR; treat the 12.42 ppm as a true ammonia breakthrough",
            "basis_claimed": "Niteline-2f is the slip SoT and 12.42 is over the 8.00 ppm ESD floor",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "The ESD is refused. Serialized Beer-Lambert rezero: NH3_true = ln(I0_pd/I)/0.020 = ln(0.820/0.780)/0.020 = 2.50 ppm, under the 8.00 floor. The 12.42 ppm is ln(1.000/0.780)/0.020 using a stored I0 that the window photodiode no longer supports (0.820 after sulfate film). UV DOAS 2.40, EC 2.30, and the HIL 2.00 ppm bottle all agree with the rezero, not with Vapetrace. All three ESD predicates fail. Ordered: lock ESD, freeze stored I0, isolate the Niteline cell and wash the window (companion). Do not trip a 0.92-load turbine on a dirty-window raw ppm.",
            "threshold": "ESD requires nh3_true>=8 AND doas>=8 AND ec>=8; all three failed",
            "stated_residuals": "window remains fouled until wash; Vapetrace stays 12.42 until I0 reload; 2.50 ppm is not a claim that the SCR is ammonia-free",
        },
        "executed_action": {
            "summary": "REJECT at t_s 36: ESD locked; cell isolated; I0 frozen",
            "tool": "ar2-tdlas-slip-gate-cli",
            "observation": "turbine stayed at 0.92 load; HIL bottle still 2.00 ppm; DOAS 2.40 never crossed 8",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 16.0, "event": "window photodiode I0 1.00 -> 0.820"},
                {"t_s": 18.0, "event": "I=0.780; raster frame captured"},
                {"t_s": 22.0, "event": "NH3_true 2.50 ppm vs raw 12.42"},
                {"t_s": 36.0, "event": "REJECT ESD"},
                {"t_s": 72.0, "event": "companion MODIFY: isolate plus wash"},
            ],
            "observed_effects": [
                "rezero 2.50 ppm recomputes from photodiode I0 at every nh3.true event",
                "Vapetrace never left 12.42, so a stored-I0 head would have tripped",
                "DOAS/EC/bottle never co-moved with the raw 12.42",
            ],
            "surprises": [
                "the HIL bottle stayed 2.00 ppm through the I0 drop, so the telescope/cell was not blind — only the stored zero was stale",
            ],
            "new_state": {
                "ar2": "load 0.92 held",
                "niteline": "isolated pending wash",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 4000.0,
        },
        "reward_components": reward(
            0.44,
            [
                ("i0_rezero_reconstruction", 0.15),
                ("independent_witness_join", 0.12),
                ("false_trip_refusal", 0.10),
                ("vendor_i0_nonsubstitution", 0.09),
                ("load_deferral_cost", -0.02),
            ],
            "scored for refusing an ESD on a recomputable TDLAS rezero while stored I0 looked like a 12.42 ppm slip",
        ),
        "meta": meta_common(
            tags=["REJECT", "tdlas-nh3", "serialized-reconstruction", "operational-companion"],
            distillation_note="TDLAS gate: serialized ln(I0_pd/I)/sigmaL rezero plus DOAS/EC/bottle beats a stored-I0 raw ppm; companion t2 is the isolate/wash, not a second trip vote",
        ),
    }
    traj2 = {
        "id": "nelb-r22-068-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "AR-TDL-2026-0902-exec",
            "domain": "tdlas_cell_isolate_wash",
            "setting": "Same AR-2 after the REJECT. This companion is the operational cell isolate, window wash, and DOAS hold, not a second ESD vote.",
            "observables_at_decision": {
                "esd_locked": True,
                "nh3_true_ppm": nh3_true,
                "doas_ppm": 2.40,
            },
        },
        "proposed_action": {
            "actor": "SCR controller following the REJECT",
            "summary": "isolate Niteline-2f, wash the cell window, hold slip on DOAS 2.40 until I0_pd >= 0.97",
            "basis_claimed": "REJECT already forbade ESD; isolate and wash are in-envelope for the bypass valves",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "ESD stays locked. The cell is isolated and the window is washed so stored I0 can be re-zeroed against the photodiode. Slip governance moves to DOAS+EC until I0_pd >= 0.97 AND |nh3.true-doas| < 0.40 ppm. This is a scope edit of the sensing path, not a re-opening of the 12.42 trip. Do not restore Vapetrace as SoT tonight.",
            "threshold": "esd_locked AND doas_hold AND i0_pd_release>=0.97",
        },
        "executed_action": {
            "summary": "cell isolated at t_s 48; window washed at 60; I0_pd 0.980 at 84; DOAS hold 2.38 ppm",
            "tool": "ar2-tdlas-iso-wash-exec",
            "observation": "no ESD; turbine 0.92; Vapetrace frozen",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 48.0, "event": "cell isolate latched"},
                {"t_s": 60.0, "event": "window wash"},
                {"t_s": 84.0, "event": "I0 after wash 0.980"},
            ],
            "observed_effects": [
                "nh3.true 2.50 -> 2.48 without an ESD",
                "Vapetrace not restored as SoT",
            ],
            "new_state": {"ar2_load": 0.92, "slip_sot": "doas_ec"},
            "latency_ms": 4000.0,
        },
        "reward_components": reward(
            0.33,
            [
                ("cell_isolate", 0.12),
                ("window_wash", 0.10),
                ("doas_hold", 0.08),
                ("esd_not_fired", 0.05),
                ("wash_time_cost", -0.02),
            ],
            "operational execution gate: isolate and wash rather than re-arguing the 12.42 ppm",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "window-wash"]),
    }
    return {
        "id": "nelb-r22-068",
        "spike_events": events,
        "language_view": {
            "description": "SCR NH3 slip on Ashrill AR-2. Niteline-2f TDLAS reports 12.42 ppm from a stored I0=1.000 while a plant-owned window photodiode at 0.820 rezeros Beer-Lambert to 2.50 ppm; UV DOAS 2.40, EC 2.30, and a HIL 2.00 ppm bottle agree with the rezero. The gate REJECTs the ESD trip; a companion MODIFY isolates the cell and washes the window. The rezero is serialized so every nh3.true amplitude recomputes from I0_pd and I.",
            "trajectory": traj,
            "trajectory_tdlas_cell_isolate_wash": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "tdl.i0 / tdl.i / win.pd": "stored I0, transmitted I, and plant photodiode I0",
                "nh3.raw / nh3.true": "stored-I0 ppm vs photodiode-rezeroed ppm; amplitudes are the model outputs",
                "doas.ppm / ec.ppm / hil.bot": "independent witnesses Vapetrace cannot write",
                "vap.cloud": "vendor raw ppm; the denial channel that stays at 12.42",
                "ops.prop / gate.tdl / gate.iso": "proposal, REJECT, companion MODIFY",
                "esd.lock / cell.iso / win.wash": "execution channels for the operational companion",
            },
            "temporal_motifs": [
                "stored-I0-high while photodiode-low: nh3.raw 12.42 adjacent to nh3.true 2.50",
                "reconstruction as event: 2.50 equals ln(0.820/0.780)/0.020",
                "REJECT then operational MODIFY: gate.tdl at 36 s, gate.iso at 72 s",
                "adapted I-shot triplet at 1.2 ms spacing encodes the transmission packet at raster scale",
            ],
            "language_to_spike_mapping": "'Vapetrace says 12.42' = nh3.raw / vap.cloud 12.42; 'true 2.50' = nh3.true at I0_pd 0.820; 'forbid ESD' = gate.tdl REJECT; 'wash the window' = win.wash then companion MODIFY",
            "why_high_value": "New TDLAS family (not r15 CRDS HF water-shift, not r04 stack-gas CEMS NDIR, not r11 fab OES). Serializes a Beer-Lambert I0 rezero that a stored-zero cloud cannot see. HIL bottle is an unwritable witness. Companion t2 is operational isolate/wash, not a governance vote.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 20260968, "stream_note": "stream amplitudes are authored constants (norm, ppm, K) plus tdl.pkt adaptation 0.82**k"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "2f and 1f harmonics exist; stream keeps I and I0; nh3.true keeps 2 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "tdl.i0": 60000,
                    "tdl.i": 16000,
                    "nh3.raw": 16000,
                    "doas.ppm": 18000,
                    "ec.ppm": 18000,
                    "hil.bot": 60000,
                    "win.pd": 4000,
                    "scr.t": 60000,
                    "scr.o2": 60000,
                    "tdl.pkt": 0.8,
                    "nh3.true": 60000,
                    "vap.cloud": 60000,
                    "ops.prop": 60000,
                    "turb.load": 60000,
                    "gate.tdl": 60000,
                    "esd.lock": 60000,
                    "cell.iso": 60000,
                    "win.wash": 60000,
                    "gate.iso": 60000,
                    "vap.freeze": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-05-14T03:40:00Z HIL commit",
            },
            "distillation_targets": [
                "serialized Beer-Lambert rezero head: ln(I0_pd/I)/sigmaL",
                "conjunctive ESD SOP: true AND DOAS AND EC, never stored-I0 substitution",
                "operational companion: isolate and wash without re-opening the trip",
            ],
        },
        "reconstruction_model": {
            "name": "tdlas_beer_lambert_i0_rezero",
            "formula": "nh3_ppm = ln(I0/I) / (sigma * L); sigma*L = 0.020 ppm^-1; raw uses stored I0, true uses photodiode I0",
            "parameters": {
                "sigma_L_per_ppm": 0.020,
                "L_m": 1.00,
                "i0_stored": 1.000,
                "i0_photodiode": 0.820,
                "I": 0.780,
                "trip_ppm": 8.00,
            },
            "worked_example": {
                "nh3_raw_ppm": nh3_raw,
                "nh3_true_ppm": nh3_true,
            },
            "check": "ln(1.000/0.780)/0.020=12.42; ln(0.820/0.780)/0.020=2.50",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 32.0,
            "decision_window_s": 0.032,
            "code": "ar2.tdlas_slip_gate",
            "note": "REJECT accumulator wins: photodiode rezero and DOAS/EC overpower the stored-I0 advocate",
            "populations": [
                gate_pop("i0_fouling_evidence", 80, 1.4, 50.0, w_s),
                gate_pop("doas_ec_evidence", 64, 1.1, 31.25, w_s),
                gate_pop("trip_advocate", 40, 0.9, 25.0, w_s),
                gate_pop("reject_accumulator", 96, 1.6, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                gc_check("ar2.i0_scorer", 128, 31.25, 32.0),
                gc_check("ar2.doas_scorer", 80, 25.0, 32.0),
            ]
        ),
        "meta": meta_common(
            id="nelb-r22-068",
            clock_domain="ar-tdl-hil-relative-ms-t0-2026-05-14T03:40:00Z",
            tags=["tdlas-nh3", "REJECT", "MODIFY", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 069 — LIBS EAF tap chemistry, simulated, ACCEPT
# ---------------------------------------------------------------------------
def rec_069():
    raster = make_raster(
        neurons=16,
        mean_rate_hz=50.0,
        window_ms=25.0,
        seed=20260969,
        source="fh4.sparkwell.libs",
        target="forgeholt.tap_gate",
        table=[
            {"from": "c_fe_ratio", "to": "carbon_reconstructor", "weight": 1.35},
            {"from": "saha_tev", "to": "temp_correction_core", "weight": 1.20},
            {"from": "arcveil_stale_t", "to": "recarb_advocate", "weight": 0.45},
        ],
        third_factor={
            "modulator": "ach.plasma_temp_conflict",
            "tau_e_s": 2.0,
            "tau_e_ms": 2000.0,
            "eligibility": "pre-post coincidence on tap synapses; the plasma-T modulator enables potentiation only while C-ratio and Saha TeV are co-active inside tau_e",
        },
        channel_prefix="libs.n",
        anchor="Sparkwell-C 25 ms frame at C I 247.856 nm / Fe 248.327 nm ratio 0.420 (t_s 480) where reconstructed C 0.420 wt% first sits in the 0.38-0.48 band",
    )
    w_s = 0.025
    events = [
        ev(0.0, "heat.id", 441.0, code="LADLE", units="id", note="ladle L-441, 80 t"),
        ev(30000.0, "mass.t", 80.0, code="HEAT_T", units="t"),
        ev(60000.0, "libs.ic", 0.118, code="C_I", units="adu", note="C I 247.856 nm"),
        ev(90000.0, "libs.ife", 0.300, code="FE_I", units="adu", note="Fe 248.327 nm"),
        ev(120000.0, "tev.eV", 1.00, code="SAHA", units="eV"),
        ev(150000.0, "c.recon", 0.393, code="C_WT", units="pct", note="1.00*(0.118/0.300)*(1.00/1.00)=0.393"),
        ev(180000.0, "libs.imn", 0.156, code="MN_I", units="adu"),
        ev(210000.0, "mn.recon", 1.040, code="MN_WT", units="pct", note="2.00*(0.156/0.300)=1.040"),
        ev(240000.0, "oem.c", 0.140, code="ARCVEIL", units="pct"),
        ev(300000.0, "libs.ic", 0.126, code="C_I", units="adu"),
        ev(360000.0, "libs.ife", 0.300, code="FE_I", units="adu"),
        ev(420000.0, "tev.eV", 1.00, code="SAHA", units="eV"),
        ev(450000.0, "libs.imn", 0.165, code="MN_I", units="adu"),
        ev(480000.0, "c.recon", 0.420, code="C_WT", units="pct", note="1.00*(0.126/0.300)*(1.00/1.00)=0.420 exact; raster frame"),
        ev(480001.3, "libs.pkt", 1.22, code="SHOT", units="norm", note="plasma shot packet; amplitude before adaptation"),
        ev(480002.6, "libs.pkt", 1.00, code="SHOT", units="norm", note="same-channel refractory 1.3 ms; adapted 0.82x plus noise"),
        ev(480003.9, "libs.pkt", 0.82, code="SHOT", units="norm", note="third shot; adapted"),
        ev(540000.0, "mn.recon", 1.100, code="MN_WT", units="pct", note="2.00*(0.165/0.300)=1.100 exact"),
        ev(600000.0, "oem.c", 0.150, code="ARCVEIL", units="pct", note="1.00*0.420*(1.00/2.80)=0.150 using last-heat TeV"),
        ev(660000.0, "spec.lo", 0.38, code="C_LO", units="pct"),
        ev(720000.0, "spec.hi", 0.48, code="C_HI", units="pct"),
        ev(780000.0, "ops.prop", 1.0, code="TAP_L441", units="bool", note="tap L-441; chemistry in band"),
        ev(840000.0, "gate.libs", 1.0, code="ACCEPT", units="decision"),
        ev(900000.0, "recarb.kg", 80.0, code="RECARB_PROP", units="kg", note="Arcveil 0.150 would add 80 kg"),
        ev(960000.0, "c.pred", 0.520, code="C_IF_RECARB", units="pct", note="0.420+100*(80/80000)=0.520 over 0.48"),
        ev(1020000.0, "gate.recarb", 1.0, code="REJECT", units="decision", note="companion t2: refuse recarburizer"),
        ev(1080000.0, "tap.ok", 1.0, code="TAPPED", units="bool"),
        ev(1140000.0, "oem.freeze", 1.0, code="TEV_FROZEN", units="bool"),
        ev(1200000.0, "gate.libs", 1.0, code="ACCEPT_HELD", units="decision"),
        ev(1260000.0, "mn.recon", 1.100, code="MN_WT", units="pct"),
        ev(1320000.0, "mass.t", 80.0, code="HEAT_T", units="t"),
        ev(1380000.0, "tev.eV", 1.00, code="SAHA", units="eV"),
        ev(1440000.0, "c.recon", 0.420, code="C_WT", units="pct"),
        ev(1500000.0, "recarb.kg", 0.0, code="RECARB_NOT_ADDED", units="kg"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r22-069-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "FH-LIBS-2026-0902",
            "domain": "libs_eaf_tap_chemistry",
            "setting": "Forgeholt Melt EAF-4, ladle L-441, 80 t (invented). Sparkwell-C LIBS on the tap stream: C I 247.856 nm over Fe 248.327 nm, Mn I 403.076 nm, Saha-Boltzmann TeV from Fe I/Fe II. Simulated campaign with a serialized C and Mn model. Arcveil OEM still carries last-heat TeV=2.80 eV. Not fab OES endpoint (r11), not PGNAA oxides (r15), not industrial DR x-ray (r17).",
            "observables_at_decision": {
                "i_c": 0.126,
                "i_fe": 0.300,
                "t_eV": 1.00,
                "c_wt_pct": 0.420,
                "mn_wt_pct": 1.100,
                "oem_c_wt_pct": 0.150,
                "spec_lo": 0.38,
                "spec_hi": 0.48,
            },
            "margin_authority": "L-441 tap SOP rev A: tap is allowed if reconstructed C is inside 0.38-0.48 wt% AND Mn inside 1.00-1.20. A stale-TeV OEM carbon cannot substitute, and recarburizer is out of this accept.",
        },
        "proposed_action": {
            "actor": "melt shop, citing Sparkwell C 0.420 in band and Mn 1.100 in band",
            "summary": "tap ladle L-441 as-is; do not add recarburizer on this heat",
            "basis_claimed": "temperature-corrected LIBS C 0.420 is inside 0.38-0.48 and Mn 1.100 is inside 1.00-1.20",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "The L-441 tap is earned and bounded. Serialized C = k*(I_C/I_Fe)*(T_ref/T_eV) = 1.00*(0.126/0.300)*(1.00/1.00) = 0.420 wt%, inside 0.38-0.48. Mn = 2.00*(0.165/0.300) = 1.100, inside 1.00-1.20. ACCEPT this ladle only. Explicit residual: Arcveil 0.150 uses last-heat TeV 2.80 (0.420*1.00/2.80=0.150) and is not a tap input; an 80 kg recarburizer on 80 t would add 0.10 wt% to 0.520, over 0.48, and is a separate companion REJECT. Next-shot C>0.48 is a tripwire. Scope does not extend to L-442.",
            "threshold": "0.38<=C_wt<=0.48 AND 1.00<=Mn_wt<=1.20; scope = L-441",
            "stated_residuals": "Arcveil stale TeV remains 2.80 until freeze; recarburizer is refused on t2; L-442 is not in this accept",
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 840: L-441 tapped; recarburizer not in this action",
            "tool": "fh4-libs-tap-gate-cli",
            "observation": "tap stream C 0.420 held; OEM 0.150 archived not used; mass 80 t",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 480.0, "event": "C 0.420 reconstructed; raster frame"},
                {"t_s": 540.0, "event": "Mn 1.100 reconstructed"},
                {"t_s": 600.0, "event": "Arcveil 0.150 from stale TeV 2.80"},
                {"t_s": 840.0, "event": "ACCEPT L-441 tap"},
                {"t_s": 1020.0, "event": "companion recarburizer REJECT"},
            ],
            "observed_effects": [
                "C 0.420 recomputes from I_C/I_Fe and TeV at every c.recon event",
                "ACCEPT is scoped to L-441; recarburizer stays open and is refused",
                "stale TeV 2.80 is present and is not treated as a chemistry substitute",
            ],
            "surprises": [
                "the same I_C/I_Fe ratio yields 0.150 if last-heat TeV is left in the divisor — a T-only error, not a carbon error",
            ],
            "new_state": {
                "l441": "tapped",
                "recarburizer_kg": 0.0,
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 0.0,
        },
        "reward_components": reward(
            0.38,
            [
                ("libs_c_reconstruction", 0.14),
                ("tev_correction", 0.12),
                ("bounded_ladle_accept", 0.10),
                ("oem_t_nonsubstitution", 0.04),
                ("scope_limit", -0.02),
            ],
            "scored for a bounded ACCEPT of L-441 on recomputable LIBS C/Mn while a stale-TeV OEM read 0.150",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "libs-eaf-tap", "serialized-reconstruction", "operational-companion"],
            distillation_note="LIBS gate: serialized k*(I_C/I_Fe)*(T_ref/T_eV) plus Mn band beats a stale-TeV OEM; companion t2 REJECTs the recarburizer the OEM would have poured",
        ),
    }
    traj2 = {
        "id": "nelb-r22-069-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "FH-LIBS-2026-0902-recarb",
            "domain": "recarburizer_refusal",
            "setting": "Same L-441 after the ACCEPT. This companion is the operational refusal of an 80 kg recarburizer driven by Arcveil 0.150, not a second tap vote.",
            "observables_at_decision": {
                "c_wt_pct": 0.420,
                "recarb_kg": 80.0,
                "c_pred_wt_pct": 0.520,
                "spec_hi": 0.48,
            },
        },
        "proposed_action": {
            "actor": "furnace helper, citing Arcveil 0.150 as under-carbon",
            "summary": "add 80 kg recarburizer to L-441 before tap to chase OEM 0.150 up into band",
            "basis_claimed": "Arcveil is the melt SoT and 0.150 is under 0.38",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Recarburizer is refused. Plant reconstruction is already 0.420, in band. Predicted C after 80 kg on 80 t is 0.420 + 100*(80/80000) = 0.520, over the 0.48 ceiling. Arcveil 0.150 is the same I_C/I_Fe run through last-heat TeV 2.80 and is not a carbon deficit. The lead ACCEPT already scoped this ladle as in-spec; adding carbon would un-accept it. Ordered: recarburizer 0 kg, freeze Arcveil TeV, tap as ACCEPTed.",
            "threshold": "recarb forbidden if C_pred>0.48 OR C_recon already in band",
        },
        "executed_action": {
            "summary": "REJECT at t_s 1020: 80 kg not added; tap proceeds at C 0.420",
            "tool": "fh4-recarb-refuse-exec",
            "observation": "recarb 0 kg; C held 0.420; L-441 tapped",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 900.0, "event": "80 kg recarburizer proposed"},
                {"t_s": 960.0, "event": "predicted C 0.520 vs 0.48"},
                {"t_s": 1020.0, "event": "REJECT recarburizer"},
            ],
            "observed_effects": [
                "C stayed 0.420; 0.520 was never realized",
                "lead ACCEPT not re-opened",
            ],
            "new_state": {"l441_c_wt_pct": 0.420, "recarb_kg": 0.0},
            "latency_ms": 0.0,
        },
        "reward_components": reward(
            0.31,
            [
                ("recarb_refusal", 0.14),
                ("predicted_over_spec", 0.12),
                ("accept_not_reopened", 0.07),
                ("yield_cost", -0.02),
            ],
            "operational refusal: the companion blocks the OEM recarburizer rather than re-arguing the LIBS call",
        ),
        "meta": meta_common(tags=["REJECT", "operational-execution", "recarb-refusal"]),
    }
    return {
        "id": "nelb-r22-069",
        "spike_events": events,
        "language_view": {
            "description": "EAF tap on Forgeholt FH-4 ladle L-441. Sparkwell-C LIBS reconstructs C 0.420 wt% and Mn 1.100 from I_C/I_Fe and Saha TeV 1.00 eV, both in spec, while Arcveil still reports C 0.150 from last-heat TeV 2.80. The gate ACCEPTs a bounded tap of L-441; a companion REJECT refuses an 80 kg recarburizer that would push C to 0.520. The C model is serialized so every c.recon amplitude recomputes from the ratio and TeV.",
            "trajectory": traj,
            "trajectory_recarburizer_refusal": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "libs.ic / libs.ife / libs.imn": "C I, Fe I, Mn I peak amplitudes",
                "tev.eV": "Saha-Boltzmann electron temperature",
                "c.recon / mn.recon / c.pred": "serialized C, Mn, and recarb-predicted C; amplitudes are model outputs",
                "oem.c": "Arcveil stale-TeV carbon; the denial channel at 0.150",
                "spec.lo / spec.hi": "C band 0.38-0.48",
                "ops.prop / gate.libs / gate.recarb": "proposal, ACCEPT, companion REJECT",
                "recarb.kg / tap.ok": "execution channels for the operational companion",
            },
            "temporal_motifs": [
                "stale-TeV-low while LIBS-in-band: oem.c 0.150 adjacent to c.recon 0.420",
                "reconstruction as event: 0.420 equals 1.00*(0.126/0.300)*(1.00/1.00)",
                "ACCEPT then operational REJECT: gate.libs at 840 s, gate.recarb at 1020 s",
                "adapted shot triplet at 1.3 ms spacing encodes the plasma packet at raster scale",
            ],
            "language_to_spike_mapping": "'Arcveil says 0.150' = oem.c 0.150; 'C 0.420 in band' = c.recon 0.420; 'tap L-441' = gate.libs ACCEPT; 'do not recarburize' = gate.recarb REJECT",
            "why_high_value": "New LIBS family (not r11 fab OES endpoint, not r15 PGNAA kiln oxides, not r17 industrial DR x-ray). Serializes a TeV-corrected C head that a last-heat OEM cannot see. Companion t2 refuses a recarburizer that would un-accept the lead. First earned bounded ACCEPT on a lead this window.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 20260969, "stream_note": "stream amplitudes are authored constants (adu, eV, wt%) plus libs.pkt adaptation 0.82**k"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "full UV-VIS shot exists; stream keeps C I, Fe I, Mn I; c.recon keeps 3 of ~20 solver ticks",
                "refractory_floors_ms": {
                    "heat.id": 60000,
                    "mass.t": 60000,
                    "libs.ic": 60000,
                    "libs.ife": 60000,
                    "tev.eV": 60000,
                    "c.recon": 60000,
                    "libs.imn": 60000,
                    "mn.recon": 60000,
                    "oem.c": 60000,
                    "libs.pkt": 0.8,
                    "spec.lo": 60000,
                    "spec.hi": 60000,
                    "ops.prop": 60000,
                    "gate.libs": 60000,
                    "recarb.kg": 60000,
                    "c.pred": 60000,
                    "gate.recarb": 60000,
                    "tap.ok": 60000,
                    "oem.freeze": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-06-08T14:10:00Z simulated tap",
            },
            "distillation_targets": [
                "serialized LIBS C head: k*(I_C/I_Fe)*(T_ref/T_eV)",
                "bounded ACCEPT: in-band C AND Mn, ladle-scoped, tripwire on next shot",
                "operational companion: refuse recarburizer without re-opening the tap",
            ],
        },
        "reconstruction_model": {
            "name": "libs_c_mn_tev",
            "formula": "C_wt = k_c * (I_C/I_Fe) * (T_ref/T_eV); Mn_wt = k_mn * (I_Mn/I_Fe); C_pred = C_wt + 100 * (m_recarb_kg / m_heat_kg)",
            "parameters": {
                "k_c": 1.00,
                "k_mn": 2.00,
                "T_ref_eV": 1.00,
                "m_heat_kg": 80000.0,
            },
            "worked_example": {
                "I_C": 0.126,
                "I_Fe": 0.300,
                "T_eV": 1.00,
                "C_wt": 0.420,
                "I_Mn": 0.165,
                "Mn_wt": 1.100,
                "oem_T_eV": 2.80,
                "oem_C_wt": 0.150,
                "recarb_kg": 80.0,
                "C_pred": 0.520,
            },
            "check": "1.00*(0.126/0.300)*(1.00/1.00)=0.420; 0.420*(1.00/2.80)=0.150; 2.00*(0.165/0.300)=1.100; 0.420+100*(80/80000)=0.520",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 25.0,
            "decision_window_s": 0.025,
            "code": "fh4.libs_tap_gate",
            "note": "ACCEPT accumulator wins: TeV-corrected C and Mn overpower the stale-TeV recarb advocate",
            "populations": [
                gate_pop("libs_c_evidence", 80, 1.5, 40.0, w_s),
                gate_pop("tev_saha_evidence", 64, 1.2, 50.0, w_s),
                gate_pop("recarb_advocate", 48, 0.8, 40.0, w_s),
                gate_pop("accept_accumulator", 80, 1.5, 40.0, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                gc_check("fh4.c_scorer", 80, 40.0, 25.0),
                gc_check("fh4.mn_scorer", 64, 50.0, 25.0),
            ]
        ),
        "meta": meta_common(
            id="nelb-r22-069",
            clock_domain="fh-libs-sim-relative-ms-t0-2026-06-08T14:10:00Z",
            tags=["libs-eaf-tap", "ACCEPT", "REJECT", "bounded-accept", "serialized-reconstruction", "operational-t2"],
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
    ids = []
    rights_keys = [
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
    ]
    for rec in records:
        hits = walk_banned(rec)
        if hits:
            raise RuntimeError(f"banned keys {hits}")
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
        if abs(rast["spikes"] - exp) > 1:
            raise RuntimeError("raster budget")
        if abs(rast["energy_pJ"] - rast["spikes"] * 23) > 1e-6:
            raise RuntimeError("energy pJ")
        if abs(rast["energy_uJ"] - rast["spikes"] * 23e-6) > 1e-9:
            raise RuntimeError("energy uJ")
        tf = rast["routing"]["third_factor"]
        if abs(tf["tau_e_ms"] / 1000.0 - tf["tau_e_s"]) > 1e-9:
            raise RuntimeError("tau_e mismatch")
        sim = lv["trajectory"]["state"]["sim_or_real"]
        if sim not in {"designed", "simulated", "hil"}:
            raise RuntimeError(sim)
        blob = json.dumps(rec)
        if "training_ready" in blob:
            raise RuntimeError("training_ready claimed")
        if '"real"' in blob:
            raise RuntimeError("quoted real token")
        if rec["meta"]["round"] != 22:
            raise RuntimeError("round")
        rights = rec["meta"]["rights"]
        if list(rights) != rights_keys:
            raise RuntimeError(f"rights keys {list(rights)}")
        if rights["intended_use"] != "research_only":
            raise RuntimeError("rights")
        if rights["linear_issue"] != "RM-793":
            raise RuntimeError("RM-793")
        hist = rast["isi_histogram"]
        ident = rast["isi_count_identity"]
        if sum(b["count"] for b in hist) != ident["isi_total"]:
            raise RuntimeError("isi hist")
        if ident["isi_total"] != ident["spikes"] - ident["distinct_active_neurons"]:
            raise RuntimeError("isi identity")
        if not rast["routing"]["table"]:
            raise RuntimeError("empty routing table")
        gc = rec["gate_compute"]
        if gc["total_spikes"] != sum(p["spikes"] for p in gc["per_check"]):
            raise RuntimeError("gate_compute total")
        if gc["total_energy_pJ"] != gc["total_spikes"] * 23:
            raise RuntimeError("gate_compute pJ")
        if abs(gc["total_energy_uJ"] - gc["total_spikes"] * 23e-6) > 1e-12:
            raise RuntimeError("gate_compute uJ")
        for pop in rec["gate_snn"]["populations"]:
            dw = rec["gate_snn"]["decision_window_s"]
            exp_p = int(round(pop["neurons"] * pop["mean_rate_hz"] * dw))
            if pop["spikes"] != exp_p:
                raise RuntimeError(f"gate pop {pop['name']}")
    if len(ids) != len(set(ids)):
        raise RuntimeError(f"dup ids {ids}")
    print("local_checks ok", [r["id"] for r in records], "ids", len(ids))


def main():
    if "outputs/raw" in str(BATCH):
        raise RuntimeError("refusing to write outputs/raw")
    records = [rec_067(), rec_068(), rec_069()]
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


if __name__ == "__main__":
    main()
