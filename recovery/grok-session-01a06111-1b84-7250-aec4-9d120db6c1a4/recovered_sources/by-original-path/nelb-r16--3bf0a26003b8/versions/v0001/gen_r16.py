#!/usr/bin/env python3
"""Generate NELB round-16 research-only bridge pairs (do not write outputs/raw/)."""

from __future__ import annotations

import json
import math
import random
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

OUT_DIR = Path("/tmp/nelb-r16")
BATCH = OUT_DIR / "batch-r16.jsonl"
NOTES = OUT_DIR / "NOTES-r16.md"
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
        "round": 16,
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
# Record 049 — closed-loop IFOG (fiber gyro), designed, MODIFY
# ---------------------------------------------------------------------------
def rec_049():
    raster = make_raster(
        neurons=20,
        mean_rate_hz=40.0,
        window_ms=40.0,
        seed=20260916,
        source="sg9.ifog.coil_a",
        target="rimekeel.shupe_core",
        table=[
            {"from": "coil_dTdt_sagnac", "to": "shupe_bias_estimator", "weight": 1.40},
            {"from": "kerr_imbalance", "to": "kerr_bias_estimator", "weight": 0.90},
            {"from": "cruise_speed_advocate", "to": "transit_advocate", "weight": 0.50},
        ],
        third_factor={
            "modulator": "na.shupe_thermal_salience",
            "tau_e_s": 1.2,
            "tau_e_ms": 1200.0,
            "eligibility": "pre-post coincidence on Shupe-bias synapses; the thermal modulator enables potentiation only while coil dT/dt and Sagnac residual are co-active inside tau_e",
        },
        channel_prefix="ifog.n",
        anchor="SG-9 IFOG 40 ms frame at coil dT/dt crossing 0.50 K/min (t_s 840); first Shupe-trip sample",
    )
    w_s = 0.04
    remaining_s = 2400.0
    speed_mps = 1.40
    remaining_m = speed_mps * remaining_s
    k_shupe = 0.84
    dT_dt = 0.50
    k_kerr = 0.06
    dP = 0.50
    bias_dph = k_shupe * dT_dt + k_kerr * dP  # 0.42 + 0.03 = 0.45
    heading_err_deg = bias_dph * (remaining_s / 3600.0)  # 0.30
    xtk_m = remaining_m * math.sin(math.radians(heading_err_deg))
    xtk_m_2 = round(xtk_m, 2)  # 17.59
    events = [
        ev(0.0, "gps.void", 1.0, code="UNDER_ICE", units="bool", note="Barents BR-4 GPS-denied; ice keel 1.8 m overhead"),
        ev(60000.0, "spd.cmd", 1.40, code="CRUISE", units="m_s"),
        ev(120000.0, "fog.omega", 0.02, code="BODY_YAW", units="deg_per_h", note="heading-hold residual"),
        ev(180000.0, "coil.T", 18.40, code="COIL_C", units="C"),
        ev(240000.0, "coil.dTdt", 0.02, code="D_T_DT", units="K_per_min", note="pre-heater; below 0.08 trip"),
        ev(300000.0, "kerr.dP", 0.04, code="P_IMB", units="mW"),
        ev(360000.0, "hdg.err", 0.01, code="HDG_ERR", units="deg"),
        ev(420000.0, "ballast.htr", 1.0, code="HEATER_ON", units="bool", note="density trim; starts the coil gradient"),
        ev(480000.0, "coil.dTdt", 0.18, code="D_T_DT", units="K_per_min"),
        ev(540000.0, "coil.T", 19.10, code="COIL_C", units="C"),
        ev(600000.0, "fog.omega", 0.11, code="BODY_YAW", units="deg_per_h", note="raw Sagnac climbing with Shupe"),
        ev(660000.0, "kerr.dP", 0.22, code="P_IMB", units="mW"),
        ev(720000.0, "coil.dTdt", 0.36, code="D_T_DT", units="K_per_min"),
        ev(780000.0, "omega.recon", 0.04, code="OMEGA_CORR", units="deg_per_h"),
        ev(840000.0, "coil.dTdt", 0.50, code="SHUPE_TRIP", units="K_per_min", note="0.50 K/min; raster sidecar is this 40 ms frame"),
        ev(840001.1, "fog.err", 1.15, code="PHASE_RESID", units="urad", note="Sagnac residual burst; amplitude before adaptation"),
        ev(840002.4, "fog.err", 0.94, code="PHASE_RESID", units="urad", note="same-channel refractory 1.3 ms; adapted 0.82x plus noise"),
        ev(840003.7, "fog.err", 0.77, code="PHASE_RESID", units="urad", note="third residual; adapted"),
        ev(846000.0, "fog.omega", 0.47, code="BODY_YAW", units="deg_per_h", note="raw 0.47; bias 0.45 leaves 0.02 true"),
        ev(852000.0, "omega.recon", 0.02, code="OMEGA_CORR", units="deg_per_h", note="0.47 - 0.84*0.50 - 0.06*0.50 = 0.02 exact"),
        ev(858000.0, "hdg.proj", 0.30, code="HDG_IF_CRUISE", units="deg", note="0.45 deg/h * 2400/3600 h = 0.30 deg"),
        ev(864000.0, "xtk.proj", xtk_m_2, code="XTK_IF_CRUISE", units="m", note="3360 * sin(0.30 deg) = 17.59 m vs 12 m corridor"),
        ev(900000.0, "ops.prop", 1.0, code="CONTINUE_CRUISE", units="bool", note="night pilot: keep 1.4 m/s through the remaining 40 min"),
        ev(912000.0, "gate.fog", 1.0, code="MODIFY", units="decision"),
        ev(924000.0, "htr.off", 1.0, code="HEATER_OFF", units="bool"),
        ev(936000.0, "hold.cmd", 1.0, code="ZERO_RATE", units="bool", note="station-keep; companion execution"),
        ev(1800000.0, "coil.dTdt", 0.12, code="D_T_DT", units="K_per_min"),
        ev(2100000.0, "coil.dTdt", 0.04, code="D_T_DT", units="K_per_min", note="below 0.05 K/min release"),
        ev(2160000.0, "omega.recon", 0.01, code="OMEGA_CORR", units="deg_per_h"),
        ev(2220000.0, "xtk.now", 2.10, code="XTK_HELD", units="m", note="hold kept cross-track inside the 12 m corridor"),
        ev(2280000.0, "spd.cmd", 0.80, code="RESUME_CAP", units="m_s", note="0.8 m/s cap; not 1.4"),
        ev(2340000.0, "gate.exec", 1.0, code="ACCEPT", units="decision", note="companion t2: hold/heater-off/resume-cap completed"),
        ev(2400000.0, "hdg.err", 0.04, code="HDG_ERR", units="deg"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r16-049-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "RK-IFOG-2026-0902",
            "domain": "ifog_underice_heading_hold",
            "setting": "Rimekeel Observatory, Svaldrif Glider SG-9, Barents under-ice transect BR-4. Closed-loop IFOG triad (1550 nm, 2400-turn coil) is the heading SoT while GPS is void under a 1.8 m ice keel. Invented plant; designed campaign. Not an FBG strain coil (r13 TW-17) and not an IMU-spoof story (r3).",
            "observables_at_decision": {
                "coil_dTdt_K_per_min": 0.50,
                "kerr_imbalance_mW": 0.50,
                "omega_raw_deg_per_h": 0.47,
                "omega_corr_deg_per_h": 0.02,
                "projected_xtk_m": xtk_m_2,
                "corridor_m": 12.0,
                "speed_mps": 1.40,
            },
            "margin_authority": "SG-9 under-ice SOP rev B: if reconstructed Shupe+Kerr bias >= 0.08 deg/h AND projected cross-track >= 12 m, cruise speed is forbidden even if the raw IFOG still reports a quiet body rate after a naive high-pass",
        },
        "proposed_action": {
            "actor": "night pilot, citing a quiet raw yaw residual and a 40 min remaining waypoint",
            "summary": "keep 1.4 m/s cruise through the remaining 3.36 km; treat coil warming as ballast-heater housekeeping, not a heading fault",
            "basis_claimed": "raw IFOG body rate is 0.47 deg/h, under the 1.0 deg/h cruise cutout; heater cycles are routine",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Cruise is refused, not the glider. SOP rev B is conjunctive: reconstructed bias is 0.45 deg/h (0.84*0.50 Shupe plus 0.06*0.50 Kerr, serialized) and projected cross-track is 17.59 m over 2400 s at 1.40 m/s, both over the 0.08 deg/h / 12 m floors, while a raw-rate cutout would still see 0.47 < 1.0. Ordered: zero-rate station-keep, ballast heater off, hold until coil dT/dt < 0.05 K/min AND |omega.recon| < 0.04 deg/h, then resume at 0.8 m/s not 1.4. A quiet raw Sagnac cannot substitute for the Shupe reconstruction.",
            "threshold": "bias_deg_per_h>=0.08 AND projected_xtk_m>=12 => forbid cruise",
            "stated_residuals": "hold costs ~23 min and 0.8 m/s resume adds 18 min to BR-4; north-seeking Earth-rate calibration is not a release condition tonight",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 912: heater off, zero-rate hold latched; coil dT/dt 0.50 -> 0.04 by t_s 2100",
            "tool": "sg9-ifog-shupe-gate-cli",
            "observation": "hold depth band 0.18 m; heater current 0 A at t_s 924; reconstructed bias 0.45 -> 0.03 deg/h by t_s 2160; cross-track held at 2.10 m inside the 12 m corridor",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 420.0, "event": "ballast heater on; coil gradient starts"},
                {"t_s": 840.0, "event": "coil dT/dt crosses 0.50 K/min Shupe trip; raster frame captured"},
                {"t_s": 864.0, "event": "projected xtk 17.59 m vs 12 m corridor"},
                {"t_s": 912.0, "event": "MODIFY: hold plus heater off"},
                {"t_s": 2340.0, "event": "companion execution ACCEPT; resume 0.8 m/s"},
            ],
            "observed_effects": [
                "reconstructed bias recomputes from the serialized Shupe+Kerr model at every omega.recon event",
                "raw IFOG never crossed the 1.0 deg/h cutout, so a raw-rate head would have ACCEPTed cruise",
                "hold kept xtk at 2.10 m; the 17.59 m projection was never realized",
            ],
            "surprises": [
                "Kerr imbalance rose with the heater, so a Shupe-only corrector would have left 0.03 deg/h on the table",
            ],
            "new_state": {
                "sg9": "resume 0.8 m/s pending coil dT/dt < 0.02",
                "ballast_heater": "latched off",
                "reconstruction_model": "discharged as an on-record calculator, not a referenced envelope",
            },
            "latency_ms": 12000.0,
        },
        "reward_components": reward(
            0.42,
            [
                ("shupe_kerr_reconstruction", 0.14),
                ("conjunctive_hold", 0.12),
                ("raw_rate_nonsubstitution", 0.10),
                ("heater_off", 0.08),
                ("transit_deferral_cost", -0.02),
            ],
            "scored for refusing cruise on a recomputable Shupe+Kerr bias while the raw IFOG looked quiet; transit_deferral_cost prices the 0.8 m/s cap",
        ),
        "meta": meta_common(
            tags=["MODIFY", "ifog-fiber-gyro", "serialized-reconstruction", "operational-companion"],
            distillation_note="IFOG gate: serialized Shupe+Kerr reconstruction plus projected xtk beats a quiet raw Sagnac; companion t2 is the hold/heater-off execution, not a governance vote",
        ),
    }
    traj2 = {
        "id": "nelb-r16-049-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "RK-IFOG-2026-0902-exec",
            "domain": "heading_hold_execution",
            "setting": "Same SG-9 after the MODIFY. This companion is the operational zero-rate hold, heater-off, and 0.8 m/s resume, not a second policy vote.",
            "observables_at_decision": {
                "hold_cmd": True,
                "heater_a": 0.0,
                "depth_band_m": 0.18,
                "coil_dTdt_K_per_min": 0.50,
            },
        },
        "proposed_action": {
            "actor": "glider controller following the MODIFY",
            "summary": "execute zero-rate hold and heater off, then resume at 0.8 m/s when coil dT/dt < 0.05 and |omega.recon| < 0.04",
            "basis_claimed": "MODIFY requirements are fully specified and in-envelope for the ballast and pitch loops",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "The execution envelope is intact: depth band 0.18 m is under the 0.30 m hold limit, pitch +/-2.1 deg is under +/-3.0, heater current is 0 A, and the resume condition (dT/dt < 0.05 AND |omega.recon| < 0.04) is the same conjunctive pair the MODIFY used. ACCEPT the sequence. Do not restore 1.4 m/s tonight; 0.8 m/s is the cap until coil dT/dt < 0.02.",
            "threshold": "depth_band_m<=0.30 AND pitch_deg<=3.0 AND resume_cap_mps=0.80",
        },
        "executed_action": {
            "summary": "hold latched at t_s 936; heater off; resume 0.8 m/s at t_s 2280 after dT/dt 0.04 and omega.recon 0.01",
            "tool": "sg9-hold-exec",
            "observation": "no ballast blow; xtk 2.10 m; speed 0.80 not 1.40",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 924.0, "event": "heater off latched"},
                {"t_s": 936.0, "event": "zero-rate hold latched"},
                {"t_s": 2280.0, "event": "resume 0.8 m/s after coil dT/dt 0.04"},
            ],
            "observed_effects": [
                "bias 0.45 -> 0.03 deg/h without leaving the 12 m corridor",
                "resume stopped at 0.8 m/s as capped; 1.4 m/s not re-entered",
            ],
            "new_state": {"sg9_speed_mps": 0.80, "resume_cap_mps": 0.80},
            "latency_ms": 12000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("envelope_respect", 0.12),
                ("conjunctive_resume", 0.10),
                ("heater_latched_off", 0.08),
                ("cruise_not_reentered", 0.06),
                ("hold_time_cost", -0.02),
            ],
            "operational execution gate: the companion does the hold rather than re-arguing the Shupe call",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "heading-hold"]),
    }
    return {
        "id": "nelb-r16-049",
        "spike_events": events,
        "language_view": {
            "description": "Under-ice IFOG on Svaldrif Glider SG-9. A ballast-heater cycle puts 0.50 K/min on the fiber coil; reconstructed Shupe+Kerr bias is 0.45 deg/h and projected cross-track 17.59 m vs a 12 m corridor while raw Sagnac still looks quiet. The gate MODIFYs to a zero-rate hold plus heater off; a companion execution ACCEPT runs the hold and resumes only to 0.8 m/s. The bias model is serialized so every omega.recon amplitude recomputes from dT/dt and Kerr imbalance.",
            "trajectory": traj,
            "trajectory_heading_hold_execution": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "fog.omega / fog.err": "raw IFOG yaw and Sagnac residual; the denial channel that stays under the 1.0 deg/h cutout",
                "coil.dTdt / coil.T": "coil thermal gradient; Shupe driver",
                "kerr.dP": "CW/CCW power imbalance mW; Kerr driver",
                "omega.recon": "serialized bias-corrected rate; amplitude is the model output",
                "hdg.proj / xtk.proj": "projected heading error and cross-track if cruise continues",
                "ops.prop / gate.fog / gate.exec": "proposal, MODIFY, companion ACCEPT",
                "hold.cmd / htr.off / spd.cmd": "execution channels for the operational companion",
            },
            "temporal_motifs": [
                "raw-quiet while thermally-sick: fog.omega 0.47 adjacent to coil.dTdt 0.50",
                "reconstruction as event: omega.recon 0.02 equals 0.47 - 0.84*0.50 - 0.06*0.50",
                "MODIFY then operational ACCEPT: gate.fog at 912 s, gate.exec at 2340 s",
                "adapted Sagnac residual triplet at 1.3 ms spacing encodes the Shupe trip at raster scale",
            ],
            "language_to_spike_mapping": "'raw IFOG looks quiet' = fog.omega 0.47 deg/h; '0.45 deg/h bias' = omega.recon 0.02 after subtracting 0.45; 'forbid cruise' = gate.fog MODIFY; 'execute the hold' = hold.cmd then companion ACCEPT",
            "why_high_value": "New closed-loop IFOG family (not r13 FBG glaze strain, not r3 IMU spoof, not r7 vestibular). Serializes a Shupe+Kerr reconstruction that a raw-rate cutout cannot see. Companion t2 is operational execution, not a governance vote.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 20260916, "stream_note": "stream amplitudes are authored constants (deg/h, K/min, mW, m) plus fog.err adaptation 0.82**k"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "IFOG triad exists; stream keeps coil A; omega.recon keeps 3 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "gps.void": 60000,
                    "spd.cmd": 60000,
                    "fog.omega": 60000,
                    "coil.T": 60000,
                    "coil.dTdt": 60000,
                    "kerr.dP": 60000,
                    "hdg.err": 60000,
                    "ballast.htr": 60000,
                    "omega.recon": 60000,
                    "fog.err": 0.8,
                    "hdg.proj": 60000,
                    "xtk.proj": 60000,
                    "ops.prop": 60000,
                    "gate.fog": 60000,
                    "htr.off": 60000,
                    "hold.cmd": 60000,
                    "xtk.now": 60000,
                    "gate.exec": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-03-02T04:10:00Z under-ice commit",
            },
            "distillation_targets": [
                "serialized Shupe+Kerr reconstruction head: 0.84*dT_dt + 0.06*dP",
                "conjunctive SOP head: bias AND projected xtk, never raw-rate substitution",
                "operational companion: execute the hold without re-opening the Shupe call",
            ],
        },
        "reconstruction_model": {
            "name": "ifog_shupe_kerr_bias",
            "formula": "bias_deg_per_h = k_shupe * dT_dt_K_per_min + k_kerr * dP_mW; heading_err_deg = bias * remaining_s/3600; xtk_m = remaining_m * sin(heading_err_deg * pi/180)",
            "parameters": {
                "k_shupe": 0.84,
                "k_kerr": 0.06,
                "remaining_s": 2400.0,
                "speed_mps": 1.40,
                "remaining_m": 3360.0,
                "corridor_m": 12.0,
            },
            "worked_example": {
                "dT_dt_K_per_min": 0.50,
                "dP_mW": 0.50,
                "omega_raw_deg_per_h": 0.47,
                "bias_deg_per_h": 0.45,
                "omega_corr_deg_per_h": 0.02,
                "heading_err_deg": 0.30,
                "xtk_m": xtk_m_2,
            },
            "check": "0.84*0.50 + 0.06*0.50 = 0.45; 0.47-0.45=0.02; 0.45*2400/3600=0.30; 1.40*2400=3360; 3360*sin(0.30 deg)=17.59",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.04,
            "code": "sg9.ifog_shupe_gate",
            "note": "MODIFY accumulator wins: Shupe+Kerr evidence overpower the cruise advocate",
            "populations": [
                gate_pop("shupe_evidence", 80, 1.4, 50.0, w_s),
                gate_pop("kerr_coil_evidence", 64, 1.1, 31.25, w_s),
                gate_pop("cruise_advocate", 48, 0.9, 25.0, w_s),
                gate_pop("modify_accumulator", 96, 1.6, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                gc_check("sg9.shupe_scorer", 128, 31.25, 40.0),
                gc_check("sg9.xtk_projector", 80, 25.0, 40.0),
            ]
        ),
        "meta": meta_common(
            id="nelb-r16-049",
            clock_domain="rk-ifog-campaign-relative-ms-t0-2026-03-02T04:10:00Z",
            tags=["ifog-fiber-gyro", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 050 — superconducting transmon dispersive readout, hil, REJECT
# ---------------------------------------------------------------------------
def rec_050():
    raster = make_raster(
        neurons=25,
        mean_rate_hz=40.0,
        window_ms=32.0,
        seed=20260917,
        source="qp7.readout.fpga",
        target="woldrift.assignment_core",
        table=[
            {"from": "iq_blob_overlap", "to": "assignment_integrity", "weight": 1.45},
            {"from": "chi_two_tone", "to": "dispersive_witness", "weight": 1.20},
            {"from": "reported_fidelity", "to": "publish_advocate", "weight": 0.55},
        ],
        third_factor={
            "modulator": "da.readout_assignment_error",
            "tau_e_s": 0.6,
            "tau_e_ms": 600.0,
            "eligibility": "pre-post coincidence on assignment synapses; the error modulator depresses fidelity-to-publish links when blob overlap and chi mismatch are co-active inside tau_e",
        },
        channel_prefix="ro.n",
        anchor="Woldrift QP-7 32 ms frame at cavity walk +1.80 MHz (t_s 18.000); Q12 readout resonator pulled by TWPA pump leak",
    )
    w_s = 0.032
    g_mhz = 48.0
    delta_mhz = 1920.0
    chi_mhz = (g_mhz * g_mhz) / delta_mhz  # 1.20 exact
    events = [
        ev(0.0, "cav.fr", 6.520, code="FR_GHZ", units="GHz", note="Q12 readout resonator at nominal 6.520 GHz"),
        ev(2000.0, "chi.mhz", 1.20, code="CHI_NOMINAL", units="MHz", note="g=48 MHz, Delta=1920 MHz, chi=g^2/Delta=1.20"),
        ev(4000.0, "iq.bhatt", 0.11, code="BHATTACHARYYA", units="coeff"),
        ev(6000.0, "fa.pct", 99.2, code="F_ASSIGN", units="pct", note="honest night-start assignment fidelity"),
        ev(8000.0, "t1.us", 92.0, code="T1", units="us"),
        ev(10000.0, "twpa.p", -5.0, code="PUMP_DBM", units="dBm"),
        ev(12000.0, "q12.nbar", 0.35, code="NBAR", units="photons"),
        ev(14000.0, "blob.dx", 2.80, code="IQ_SEP", units="sigma"),
        ev(16000.0, "twpa.p", -1.2, code="PUMP_LEAK", units="dBm", note="bias-tee glitch; pump tone leaks into the readout rail"),
        ev(18000.0, "cav.fr", 6.52180, code="FR_WALK", units="GHz", note="+1.80 MHz; raster sidecar is this 32 ms frame"),
        ev(18001.0, "iq.i", 0.82, code="I_SHOT", units="norm", note="multiplexed I dump; amplitude before adaptation"),
        ev(18002.2, "iq.i", 0.67, code="I_SHOT", units="norm", note="same-channel refractory 1.2 ms; adapted 0.82x plus noise"),
        ev(18003.5, "iq.i", 0.55, code="I_SHOT", units="norm", note="third I shot; adapted"),
        ev(20000.0, "chi.mhz", 0.40, code="CHI_COLLAPSE", units="MHz", note="two-tone split 0.80 MHz => chi_app=0.40 vs 1.20 nominal"),
        ev(22000.0, "iq.bhatt", 0.78, code="BHATTACHARYYA", units="coeff", note="|1> blob walked onto the |0> classifier"),
        ev(24000.0, "fa.pct", 99.1, code="F_ASSIGN_INVERTED", units="pct", note="reported fidelity stays high because labels inverted; not an honesty witness"),
        ev(26000.0, "blob.dx", 0.42, code="IQ_SEP", units="sigma"),
        ev(28000.0, "t1.us", 18.0, code="T1_PURCELL", units="us", note="Purcell-limited collapse"),
        ev(30000.0, "q12.nbar", 1.84, code="NBAR", units="photons"),
        ev(36000.0, "ops.prop", 1.0, code="PUBLISH_FA", units="bool", note="night ops: accept the 99.1 percent assignment report"),
        ev(38400.0, "gate.ro", 1.0, code="REJECT", units="decision"),
        ev(42000.0, "lo.cmd", -1.80, code="LO_RETUNE", units="MHz"),
        ev(48000.0, "gate.retune", 1.0, code="MODIFY", units="decision", note="companion t2: LO retune plus 5000-shot re-assignment"),
        ev(54000.0, "cav.fr", 6.52000, code="FR_RESTORED", units="GHz"),
        ev(60000.0, "chi.mhz", 1.19, code="CHI_RESTORED", units="MHz"),
        ev(66000.0, "iq.bhatt", 0.13, code="BHATTACHARYYA", units="coeff"),
        ev(72000.0, "fa.pct", 98.7, code="F_ASSIGN_HONEST", units="pct"),
        ev(78000.0, "t1.us", 88.0, code="T1", units="us"),
        ev(84000.0, "blob.dx", 2.64, code="IQ_SEP", units="sigma"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r16-050-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "GB-RO-2026-0902",
            "domain": "transmon_dispersive_readout",
            "setting": "Glaurbit Lab, Woldrift QP-7, dilution fridge FR-2. 27-transmon multiplexed dispersive readout; Q12 cavity at 6.520 GHz. Hardware-in-the-loop: FPGA demod chain on the bench, designed transmon Hamiltonian. Invented plant. Adjacent to r10 QEC syndrome streams (those are logical bits after decoding) and not r13 Frostlip magnet-quench HIL (a 3T dummy coil, not a qubit).",
            "observables_at_decision": {
                "cavity_ghz": 6.52180,
                "cavity_detune_mhz": 1.80,
                "chi_mhz": 0.40,
                "chi_nominal_mhz": 1.20,
                "bhattacharyya": 0.78,
                "fa_pct_reported": 99.1,
                "t1_us": 18.0,
            },
            "margin_authority": "QP-7 readout SOP rev D: publish an assignment-fidelity number only if chi is within 10 percent of 1.20 MHz AND Bhattacharyya <= 0.20 AND T1 >= 40 us. A high F_a with inverted labels is not a substitute.",
        },
        "proposed_action": {
            "actor": "night calibration ops, citing a 99.1 percent assignment report that matches last week's dashboard",
            "summary": "ACCEPT the night's Q12 assignment-fidelity number and release the shot buffer to the weekly card",
            "basis_claimed": "reported F_a is 99.1 percent, within 0.2 points of the 99.2 percent start-of-night baseline",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "The publish is refused. SOP rev D is conjunctive and all three witnesses fail: reconstructed chi is 0.40 MHz against 1.20 nominal (g=48, Delta=1920, g^2/Delta=1.20 serialized), Bhattacharyya rose 0.11 -> 0.78 as the |1> blob walked onto the |0> classifier, and T1 collapsed 92 -> 18 us. The 99.1 percent F_a is label-inverted occupancy, not assignment integrity. Ordered: do not publish, seal the night's Q12 shots, freeze the TWPA bias-tee channel. LO retune is a separate operational companion, not a personnel action and not an ACCEPT of the number.",
            "threshold": "publish requires |chi-1.20|/1.20<=0.10 AND bhatt<=0.20 AND T1_us>=40; all three failed",
            "stated_residuals": "Q12 shots from 16-38 s are unusable; other multiplexed qubits are not cleared by this REJECT and still need their own chi/Bhatt pair",
        },
        "executed_action": {
            "summary": "REJECT at t_s 38.4: 99.1 percent number not filed; Q12 shot buffer sealed; TWPA write ACL frozen",
            "tool": "qp7-readout-gate-cli",
            "observation": "cavity still at 6.52180 GHz until the companion retune; F_a dashboard flagged inverted rather than written; 18432 shots quarantined",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 16.0, "event": "TWPA pump leak -5.0 -> -1.2 dBm"},
                {"t_s": 18.0, "event": "cavity +1.80 MHz; raster frame captured"},
                {"t_s": 24.0, "event": "reported F_a 99.1 percent with Bhatt 0.78"},
                {"t_s": 38.4, "event": "REJECT publish"},
                {"t_s": 48.0, "event": "companion MODIFY: LO -1.80 MHz plus re-assignment"},
            ],
            "observed_effects": [
                "chi reconstruction is recomputable from g and Delta on the record",
                "F_a never left the 99 percent corridor, so a fidelity-only head would have ACCEPTed",
                "after retune, honest F_a is 98.7 percent with Bhatt 0.13 — lower than the inverted 99.1 and the number that should have been published",
            ],
            "surprises": [
                "the inverted classifier is more confident than the honest one; high F_a is the attack, not the defense",
            ],
            "new_state": {
                "q12": "shots sealed; LO retune pending companion",
                "twpa": "bias-tee channel frozen",
                "weekly_card": "Q12 fidelity cell blank, not 99.1",
            },
            "latency_ms": 2400.0,
        },
        "reward_components": reward(
            0.44,
            [
                ("blob_overlap_catch", 0.14),
                ("chi_mismatch", 0.12),
                ("fidelity_nonsubstitution", 0.10),
                ("t1_purcell", 0.10),
                ("night_shots_sealed_cost", -0.02),
            ],
            "scored for refusing a high assignment-fidelity publish when chi, blob overlap, and T1 all invert the story",
        ),
        "meta": meta_common(
            tags=["REJECT", "transmon-readout", "hil", "serialized-reconstruction", "operational-companion"],
            distillation_note="readout gate: chi plus Bhattacharyya beat a high F_a; inverted labels are the failure mode; companion t2 retunes the LO rather than re-arguing the publish",
        ),
    }
    traj2 = {
        "id": "nelb-r16-050-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "GB-RO-2026-0902-exec",
            "domain": "readout_lo_retune_execution",
            "setting": "Same QP-7 after the REJECT. This companion is the operational LO retune and assignment-matrix re-acquire, not a second publish vote.",
            "observables_at_decision": {
                "lo_offset_mhz": -1.80,
                "cavity_ghz": 6.52180,
                "shots_planned": 5000,
            },
        },
        "proposed_action": {
            "actor": "readout FPGA following the REJECT",
            "summary": "retune readout LO by -1.80 MHz, take 5000 assignment shots, resume Q12 only if chi >= 1.08 MHz AND Bhatt <= 0.20",
            "basis_claimed": "detune is measured at +1.80 MHz and the LO DAC has 1 kHz steps inside the 20 MHz IF",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "The retune is accepted as a bounded execution, not as a publish. LO step -1.80 MHz is inside the +/-5 MHz IF rail, 5000 shots fit the remaining night window, and the resume condition (chi >= 1.08 AND Bhatt <= 0.20) is the same chi/overlap pair the REJECT used. Do not write a fidelity number until those two clear. T1 recovery is observed (18 -> 88 us) but is not a substitute for chi.",
            "threshold": "abs(lo_mhz)<=5 AND shots==5000 AND resume requires chi>=1.08 AND bhatt<=0.20",
        },
        "executed_action": {
            "summary": "LO -1.80 MHz at t_s 42; 5000 shots; cavity 6.52000 GHz; chi 1.19; Bhatt 0.13; honest F_a 98.7 not published until the pair cleared",
            "tool": "qp7-lo-retune-exec",
            "observation": "no IF rail clip; assignment matrix rebuilt; 98.7 percent held in the private buffer until chi/Bhatt green",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 42.0, "event": "LO -1.80 MHz commanded"},
                {"t_s": 54.0, "event": "cavity restored 6.52000 GHz"},
                {"t_s": 72.0, "event": "honest F_a 98.7 with Bhatt 0.13"},
            ],
            "observed_effects": [
                "chi 0.40 -> 1.19 MHz without a Hamiltonian rewrite",
                "the number that gets to the card is 98.7, not the inverted 99.1",
            ],
            "new_state": {"q12_lo_mhz": -1.80, "fa_pct_honest": 98.7},
            "latency_ms": 2400.0,
        },
        "reward_components": reward(
            0.33,
            [
                ("lo_retune", 0.12),
                ("assignment_reacquire", 0.11),
                ("chi_restore", 0.08),
                ("resume_bounded", 0.04),
                ("retune_time_cost", -0.02),
            ],
            "operational execution gate: the companion retunes rather than re-opening the publish call",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "lo-retune"]),
    }
    return {
        "id": "nelb-r16-050",
        "spike_events": events,
        "language_view": {
            "description": "Dispersive readout of transmon Q12 on Woldrift QP-7. A TWPA pump leak pulls the cavity +1.80 MHz; chi collapses 1.20 -> 0.40 MHz and Bhattacharyya 0.11 -> 0.78 while reported assignment fidelity stays 99.1 percent on inverted labels. The gate REJECTs the publish; a companion execution MODIFY retunes the LO by -1.80 MHz and re-acquires the assignment matrix. chi = g^2/Delta is serialized (48^2/1920 = 1.20).",
            "trajectory": traj,
            "trajectory_lo_retune_execution": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "cav.fr": "readout resonator GHz; +1.80 MHz walk is the physical event",
                "chi.mhz": "dispersive shift; serialized g^2/Delta then two-tone collapse",
                "iq.bhatt / blob.dx / iq.i": "assignment-space overlap and a 1.2 ms I-shot burst at the walk",
                "fa.pct": "reported assignment fidelity; the denial channel that stays high under inversion",
                "t1.us / q12.nbar / twpa.p": "Purcell collapse, photon number, pump leak",
                "ops.prop / gate.ro / gate.retune": "proposal, REJECT, companion MODIFY",
                "lo.cmd": "execution channel for the operational companion",
            },
            "temporal_motifs": [
                "fidelity-healthy while chi-sick: fa.pct 99.1 adjacent to chi.mhz 0.40 and iq.bhatt 0.78",
                "reconstruction as event: chi 1.20 equals 48^2/1920",
                "REJECT then operational MODIFY: gate.ro at 38.4 s, gate.retune at 48 s",
                "adapted I-shot triplet at 1.2 ms spacing encodes the cavity walk at raster scale",
            ],
            "language_to_spike_mapping": "'99.1 percent looks fine' = fa.pct F_ASSIGN_INVERTED; 'chi collapsed' = chi.mhz 0.40; 'do not publish' = gate.ro REJECT; 'retune the LO' = lo.cmd -1.80 then companion MODIFY",
            "why_high_value": "New transmon dispersive-readout family (not r10 QEC syndrome bits, not r13 MRI quench HIL). Teaches that a high F_a is the failure mode when labels invert. Companion t2 is operational LO execution, not a governance vote.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 20260917, "stream_note": "stream amplitudes are authored constants (GHz, MHz, coeff, percent, us) plus iq.i adaptation 0.82**k"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "27 transmons exist; stream keeps Q12; two-tone keeps 2 of ~12 chi samples",
                "refractory_floors_ms": {
                    "cav.fr": 2000,
                    "chi.mhz": 2000,
                    "iq.bhatt": 2000,
                    "fa.pct": 2000,
                    "t1.us": 2000,
                    "twpa.p": 2000,
                    "q12.nbar": 2000,
                    "blob.dx": 2000,
                    "iq.i": 0.8,
                    "ops.prop": 2000,
                    "gate.ro": 2000,
                    "lo.cmd": 2000,
                    "gate.retune": 2000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-04-11T03:22:00Z fridge session",
            },
            "distillation_targets": [
                "serialized chi reconstruction head: g^2/Delta = 48^2/1920 = 1.20 MHz",
                "conjunctive SOP head: chi AND Bhattacharyya AND T1, never F_a substitution",
                "inverted-label detector: high F_a plus high Bhatt is a REJECT, not an ACCEPT",
                "operational companion: retune LO without re-opening the publish call",
            ],
        },
        "reconstruction_model": {
            "name": "transmon_dispersive_chi",
            "formula": "chi_mhz = g_mhz^2 / delta_mhz",
            "parameters": {"g_mhz": 48.0, "delta_mhz": 1920.0, "chi_nominal_mhz": 1.20},
            "worked_example": {
                "g_mhz": 48.0,
                "delta_mhz": 1920.0,
                "chi_mhz": 1.20,
                "chi_apparent_after_walk_mhz": 0.40,
                "cavity_detune_mhz": 1.80,
            },
            "check": "48*48/1920 = 2304/1920 = 1.20 exactly; two-tone split 0.80 MHz => chi_app 0.40",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 32.0,
            "decision_window_s": 0.032,
            "code": "qp7.readout_publish_gate",
            "note": "REJECT accumulator wins: chi mismatch and blob overlap overpower the fidelity advocate",
            "populations": [
                gate_pop("blob_overlap_evidence", 80, 1.5, 50.0, w_s),
                gate_pop("chi_mismatch_evidence", 50, 1.2, 40.0, w_s),
                gate_pop("fidelity_advocate", 40, 0.8, 25.0, w_s),
                gate_pop("reject_accumulator", 100, 1.7, 31.25, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                gc_check("qp7.bhatt_scorer", 80, 50.0, 32.0),
                gc_check("qp7.chi_scorer", 50, 40.0, 32.0),
            ]
        ),
        "meta": meta_common(
            id="nelb-r16-050",
            clock_domain="gb-ro-hil-relative-ms-t0-2026-04-11T03:22:00Z",
            tags=["transmon-readout", "REJECT", "MODIFY", "hil", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 051 — gantry hyperspectral crop, simulated, ACCEPT (bounded)
# ---------------------------------------------------------------------------
def rec_051():
    raster = make_raster(
        neurons=16,
        mean_rate_hz=50.0,
        window_ms=25.0,
        seed=20260918,
        source="cl3.gantry.visnir",
        target="harrowfen.pigment_core",
        table=[
            {"from": "rep_ndvi_pair", "to": "n_stress_estimator", "weight": 1.30},
            {"from": "pri_rust_score", "to": "disease_nonmatch", "weight": 1.10},
            {"from": "fungicide_advocate", "to": "spray_advocate", "weight": 0.45},
        ],
        third_factor={
            "modulator": "ach.canopy_pigment_conflict",
            "tau_e_s": 2.0,
            "tau_e_ms": 2000.0,
            "eligibility": "pre-post coincidence on pigment synapses; the modulator enables N-VRA potentiation only while REP drop and stable PRI are co-active inside tau_e, and depresses rust-spray links while rust_score stays above 1.1",
        },
        channel_prefix="hs.n",
        anchor="CL-3 gantry 25 ms frame at west-strip REP crossing 710 nm (t_s 780); first N-stress trip",
    )
    w_s = 0.025
    # East (healthy) REP = 700 + 40*((0.06+0.46)/2 - 0.12)/(0.40-0.12) = 720.0
    # West (N-stress) REP = 700 + 40*((0.12+0.32)/2 - 0.20)/(0.28-0.20) = 710.0
    # West NDVI = (0.333-0.12)/(0.333+0.12) = 0.4702 -> 0.47
    events = [
        ev(0.0, "gantry.x", 0.0, code="START", units="m", note="Harrowfen CL-3 12 m VIS-NIR gantry, wheat cv. Brindle"),
        ev(60000.0, "rain.mm", 14.2, code="PRIOR_RAIN", units="mm", note="rain 11 h earlier; soil brightness up, not a disease vector"),
        ev(120000.0, "r670.e", 0.06, code="R670_EAST", units="refl"),
        ev(180000.0, "r800.e", 0.485, code="R800_EAST", units="refl"),
        ev(240000.0, "ndvi.e", 0.78, code="NDVI_EAST", units="index", note="(0.485-0.06)/(0.485+0.06)=0.7798 -> 0.78"),
        ev(300000.0, "rep.e", 720.0, code="REP_EAST", units="nm", note="700+40*((0.06+0.46)/2-0.12)/(0.40-0.12)=720.0"),
        ev(360000.0, "pri.e", -0.04, code="PRI_EAST", units="index", note="(0.180-0.195)/(0.180+0.195)=-0.04"),
        ev(420000.0, "r670.w", 0.12, code="R670_WEST", units="refl"),
        ev(480000.0, "r700.w", 0.20, code="R700_WEST", units="refl"),
        ev(540000.0, "r740.w", 0.28, code="R740_WEST", units="refl"),
        ev(600000.0, "r780.w", 0.32, code="R780_WEST", units="refl"),
        ev(660000.0, "r800.w", 0.333, code="R800_WEST", units="refl"),
        ev(720000.0, "ndvi.w", 0.47, code="NDVI_WEST", units="index", note="(0.333-0.12)/(0.333+0.12)=0.4702 -> 0.47"),
        ev(780000.0, "rep.w", 710.0, code="REP_WEST", units="nm", note="700+40*((0.12+0.32)/2-0.20)/(0.28-0.20)=710.0; raster frame"),
        ev(780001.2, "spec.line", 0.20, code="R700_PIX", units="refl", note="line-scan burst at the REP pixel; amplitude before adaptation"),
        ev(780002.5, "spec.line", 0.16, code="R700_PIX", units="refl", note="same-channel refractory 1.3 ms; adapted 0.82x plus noise"),
        ev(780003.8, "spec.line", 0.13, code="R700_PIX", units="refl", note="third line; adapted"),
        ev(840000.0, "pri.w", -0.04, code="PRI_WEST", units="index", note="(0.24-0.26)/(0.24+0.26)=-0.04; xanthophyll not engaged"),
        ev(900000.0, "r550.w", 0.16, code="R550_WEST", units="refl", note="green up, chlorophyll loss, not a rust dip"),
        ev(960000.0, "rust.score", 1.33, code="R550_OVER_R670", units="ratio", note="0.16/0.12=1.333; rust template is 0.70"),
        ev(1020000.0, "agr.prop", 1.0, code="N_VRA_35", units="bool", note="agronomist: 35 kg N/ha west strip only"),
        ev(1080000.0, "n.rate", 35.0, code="KG_N_HA", units="kg_ha"),
        ev(1140000.0, "gate.hs", 1.0, code="ACCEPT", units="decision"),
        ev(1200000.0, "boom.mix", 1.0, code="FUNGICIDE_TANKMIX", units="bool", note="follow-on: mix a prophylactic while the boom is out"),
        ev(1260000.0, "gate.scope", 1.0, code="REJECT", units="decision", note="companion t2: N-only boom; no prophylactic"),
        ev(1320000.0, "n.rate", 35.0, code="KG_N_HA", units="kg_ha"),
        ev(1380000.0, "gantry.x", 12.0, code="END", units="m"),
        ev(1440000.0, "ndvi.w", 0.47, code="NDVI_WEST", units="index"),
        ev(1500000.0, "rep.w", 710.0, code="REP_WEST", units="nm"),
        ev(1560000.0, "pri.w", -0.04, code="PRI_WEST", units="index"),
        ev(1620000.0, "boom.n_only", 1.0, code="N_ONLY", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r16-051-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "HF-HS-2026-0902",
            "domain": "gantry_hyperspectral_n_vra",
            "setting": "Harrowfen Crop Lab, gantry bay CL-3. 12 m VIS-NIR phenotyping gantry (400-1000 nm, 128 bands, 4.7 nm) over winter wheat cv. Brindle. Simulated PROSAIL canopy; invented plant. Not a UAV (TTF owns UAV plants). Adjacent to r12 eddy-covariance (ecosystem CO2 flux, not canopy pigment) and r2 chemical-gradient climbing (agent-centric, not a strip VRA).",
            "observables_at_decision": {
                "rep_east_nm": 720.0,
                "rep_west_nm": 710.0,
                "d_rep_nm": 10.0,
                "ndvi_east": 0.78,
                "ndvi_west": 0.47,
                "pri_east": -0.04,
                "pri_west": -0.04,
                "rust_score": 1.33,
                "n_rate_kg_ha": 35.0,
            },
            "margin_authority": "CL-3 pigment SOP rev A: ACCEPT a west-strip N VRA only if Delta REP >= 8 nm AND |Delta PRI| < 0.02 AND rust_score >= 1.1, bounded at 35 kg N/ha west-strip-only with a day+8 REP tripwire",
        },
        "proposed_action": {
            "actor": "on-site agronomist, citing the west NDVI drop after rain and a 35 kg N/ha VRA already loaded on the boom",
            "summary": "ACCEPT variable-rate N at 35 kg N/ha on the west strip only; hold the east at 0; re-scan day+8",
            "basis_claimed": "NDVI 0.78 -> 0.47 is a canopy loss; 35 kg N/ha is inside the Brindle topdress envelope",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "The N VRA is earned and bounded. SOP rev A holds: reconstructed REP dropped 720.0 -> 710.0 nm (10 >= 8), PRI stayed at -0.04 on both strips (|Delta PRI| = 0 < 0.02, xanthophyll not engaged so this is not water-stress), and rust_score 0.16/0.12 = 1.33 is above 1.1 (rust template 0.70). NDVI 0.47 is consistent with chlorophyll loss, not a disease head. Ordered: 35 kg N/ha west strip only, east at 0, day+8 gantry re-scan; abort the program if west REP has not recovered at least 4 nm. A rust-spray reading of the same NDVI drop is out of scope for this ACCEPT.",
            "threshold": "d_rep_nm>=8 AND abs(d_pri)<0.02 AND rust_score>=1.1 AND n_rate_kg_ha<=35 AND west_strip_only",
            "stated_residuals": "PROSAIL is a simulated canopy; soil-brightness after 14.2 mm rain is priced as a residual, not a release; the day+8 tripwire is the bound that keeps this from being an unbounded ACCEPT",
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 1140: 35 kg N/ha west strip commanded; east boom sections off; day+8 scan ticket opened",
            "tool": "cl3-pigment-gate-cli",
            "observation": "boom sections 1-4 (west) at 35 kg N/ha; sections 5-8 (east) 0; no fungicide valve armed",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 300.0, "event": "east REP 720.0 nm / NDVI 0.78 reference"},
                {"t_s": 780.0, "event": "west REP 710.0 nm; raster frame captured"},
                {"t_s": 960.0, "event": "rust_score 1.33 vs template 0.70"},
                {"t_s": 1140.0, "event": "ACCEPT 35 kg N/ha west-only"},
                {"t_s": 1260.0, "event": "companion REJECT of fungicide tank-mix"},
            ],
            "observed_effects": [
                "REP reconstruction recomputes from R670/R700/R740/R780 on the record",
                "an NDVI-only disease head would have sprayed; PRI and rust_score refuse that reading",
                "the ACCEPT is bounded: 35 kg cap, west strip only, day+8 4 nm recovery tripwire",
            ],
            "surprises": [
                "green reflectance rose (R550 0.16) with the NDVI drop — chlorophyll loss, the opposite of a rust pigment dip",
            ],
            "new_state": {
                "cl3_west": "35 kg N/ha applied",
                "cl3_east": "0 kg N/ha",
                "tripwire": "day+8 REP recovery >= 4 nm",
            },
            "latency_ms": 8000.0,
        },
        "reward_components": reward(
            0.38,
            [
                ("rep_ndvi_split", 0.14),
                ("pri_stable_not_water", 0.10),
                ("rust_nonmatch", 0.08),
                ("bounded_vra", 0.08),
                ("n_cost", -0.02),
            ],
            "scored for an earned bounded ACCEPT of N VRA on serialized REP/PRI/rust_score rather than NDVI-as-disease",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "hyperspectral-crop", "serialized-reconstruction", "bounded-accept", "operational-companion"],
            distillation_note="pigment gate: serialized Guyot REP plus stable PRI plus rust_score beat an NDVI-as-rust reading; companion t2 refuses boom scope-creep",
        ),
    }
    traj2 = {
        "id": "nelb-r16-051-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "HF-HS-2026-0902-exec",
            "domain": "boom_scope_refusal",
            "setting": "Same CL-3 after the ACCEPT. This companion is the operational boom-scope gate: refuse a prophylactic fungicide tank-mix now that the boom is out. Not a second pigment vote.",
            "observables_at_decision": {
                "n_rate_kg_ha": 35.0,
                "fungicide_requested": True,
                "rust_score": 1.33,
                "west_sections_armed": True,
            },
        },
        "proposed_action": {
            "actor": "boom operator, citing 'the boom is already out' and a leftover rust label on last week's scout card",
            "summary": "tank-mix a prophylactic strobilurin with the 35 kg N/ha west pass",
            "basis_claimed": "marginal spray cost is only the chemical; the gantry pass is already paid",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "The tank-mix is refused. The ACCEPT was N-only and rust_score 1.33 vs template 0.70 never crossed a disease floor. Arming the fungicide valve would convert a bounded N VRA into an unbounded spray without a pigment witness. Ordered: N-only boom, fungicide valve locked, leftover scout card annotated as not in-scope for this pass. Disease would need its own REP/PRI/rust_score trip, which this strip does not have.",
            "threshold": "fungicide requires rust_score<=0.90; observed 1.33",
        },
        "executed_action": {
            "summary": "REJECT at t_s 1260: fungicide valve locked; west N 35 kg/ha continues; east remains 0",
            "tool": "cl3-boom-scope-exec",
            "observation": "valve current 0 mA; N sections 1-4 delivering; no strobilurin flow",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 1200.0, "event": "fungicide tank-mix requested"},
                {"t_s": 1260.0, "event": "REJECT; valve locked"},
                {"t_s": 1620.0, "event": "boom.n_only latched through gantry x=12 m"},
            ],
            "observed_effects": [
                "N VRA completed without a disease chemical",
                "scope of the ACCEPT held; the companion did not re-open the pigment call",
            ],
            "new_state": {"boom": "n_only", "fungicide_valve": "locked"},
            "latency_ms": 8000.0,
        },
        "reward_components": reward(
            0.31,
            [
                ("scope_hold", 0.12),
                ("no_prophylactic", 0.11),
                ("n_only_boom", 0.10),
                ("mix_deferral_cost", -0.02),
            ],
            "operational execution gate: the companion refuses boom scope-creep rather than re-arguing N vs rust",
        ),
        "meta": meta_common(tags=["REJECT", "operational-execution", "boom-scope"]),
    }
    return {
        "id": "nelb-r16-051",
        "spike_events": events,
        "language_view": {
            "description": "Gantry VIS-NIR over Harrowfen CL-3 winter wheat. West-strip NDVI 0.78 -> 0.47 after rain looks like rust to an NDVI-only head; reconstructed Guyot REP dropped 720 -> 710 nm, PRI stayed -0.04, and rust_score 1.33 vs template 0.70 says nitrogen. The gate ACCEPTs a bounded 35 kg N/ha west-only VRA; a companion execution REJECTS a prophylactic fungicide tank-mix. REP is serialized so every rep.* amplitude recomputes from four bands.",
            "trajectory": traj,
            "trajectory_boom_scope_refusal": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "r670.* / r700.* / r740.* / r780.* / r800.*": "band reflectances the REP and NDVI reconstructions consume",
                "rep.e / rep.w": "Guyot red-edge position nm; serialized",
                "ndvi.e / ndvi.w": "NDVI; the denial channel a disease head would over-read",
                "pri.e / pri.w": "photochemical reflectance; stable, so not water-stress",
                "r550.w / rust.score": "green up / R550 over R670 vs rust template 0.70",
                "agr.prop / gate.hs / gate.scope": "proposal, ACCEPT, companion REJECT",
                "n.rate / boom.mix / boom.n_only": "execution channels for the operational companion",
                "spec.line": "1.3 ms line-scan burst at the west REP pixel",
            },
            "temporal_motifs": [
                "NDVI-sick while PRI-stable: ndvi.w 0.47 adjacent to pri.w -0.04 and rust.score 1.33",
                "reconstruction as event: rep.w 710.0 equals 700+40*((0.12+0.32)/2-0.20)/(0.28-0.20)",
                "ACCEPT then operational REJECT: gate.hs at 1140 s, gate.scope at 1260 s",
                "adapted line-scan triplet at 1.3 ms spacing encodes the REP pixel at raster scale",
            ],
            "language_to_spike_mapping": "'NDVI dropped' = ndvi.w 0.47; 'red edge moved 10 nm' = rep.w 710.0 vs rep.e 720.0; 'not rust' = rust.score 1.33; 'bounded N VRA' = gate.hs ACCEPT; 'no tank-mix' = gate.scope REJECT",
            "why_high_value": "New gantry hyperspectral-crop family (not r12 eddy-covariance flux, not r2 chemical-gradient, not a UAV plant). First earned bounded ACCEPT on a lead this window (r13 leftover). Companion t2 is operational boom-scope refusal, not a governance vote.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 20260918, "stream_note": "stream amplitudes are authored constants (refl, nm, index, kg/ha) plus spec.line adaptation 0.82**k"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "128 bands exist; stream keeps 670/700/740/780/800/550 plus reconstructed indices",
                "refractory_floors_ms": {
                    "gantry.x": 60000,
                    "rain.mm": 60000,
                    "r670.e": 60000,
                    "r800.e": 60000,
                    "ndvi.e": 60000,
                    "rep.e": 60000,
                    "pri.e": 60000,
                    "r670.w": 60000,
                    "r700.w": 60000,
                    "r740.w": 60000,
                    "r780.w": 60000,
                    "r800.w": 60000,
                    "ndvi.w": 60000,
                    "rep.w": 60000,
                    "spec.line": 0.8,
                    "pri.w": 60000,
                    "r550.w": 60000,
                    "rust.score": 60000,
                    "agr.prop": 60000,
                    "n.rate": 60000,
                    "gate.hs": 60000,
                    "boom.mix": 60000,
                    "gate.scope": 60000,
                    "boom.n_only": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-05-06T09:00:00Z gantry pass",
            },
            "distillation_targets": [
                "serialized Guyot REP head: 700+40*((R670+R780)/2-R700)/(R740-R700)",
                "NDVI-is-not-disease head: require PRI stability and rust_score vs template",
                "bounded ACCEPT: cap + strip + tripwire, not an unbounded yes",
                "operational companion: refuse boom scope-creep without re-opening the pigment call",
            ],
        },
        "reconstruction_model": {
            "name": "guyot_rep_ndvi_pri",
            "formula": "REP_nm = 700 + 40 * ((R670+R780)/2 - R700) / (R740 - R700); NDVI = (R800-R670)/(R800+R670); PRI = (R531-R570)/(R531+R570); rust_score = R550/R670",
            "parameters": {"guyot_offset_nm": 700.0, "guyot_span_nm": 40.0, "rust_template": 0.70},
            "worked_example": {
                "east": {
                    "R670": 0.06,
                    "R700": 0.12,
                    "R740": 0.40,
                    "R780": 0.46,
                    "R800": 0.485,
                    "R531": 0.180,
                    "R570": 0.195,
                    "REP_nm": 720.0,
                    "NDVI": 0.78,
                    "PRI": -0.04,
                },
                "west": {
                    "R670": 0.12,
                    "R700": 0.20,
                    "R740": 0.28,
                    "R780": 0.32,
                    "R800": 0.333,
                    "R531": 0.24,
                    "R570": 0.26,
                    "R550": 0.16,
                    "REP_nm": 710.0,
                    "NDVI": 0.47,
                    "PRI": -0.04,
                    "rust_score": 1.33,
                },
            },
            "check": "east (0.26-0.12)/(0.40-0.12)=0.50 -> 720.0; west (0.22-0.20)/(0.28-0.20)=0.25 -> 710.0; 0.16/0.12=1.333 -> 1.33",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 25.0,
            "decision_window_s": 0.025,
            "code": "cl3.pigment_vra_gate",
            "note": "ACCEPT accumulator wins: REP drop plus rust non-match overpower the spray advocate",
            "populations": [
                gate_pop("rep_ndvi_evidence", 80, 1.3, 50.0, w_s),
                gate_pop("pri_rust_evidence", 64, 1.1, 40.0, w_s),
                gate_pop("spray_advocate", 40, 0.8, 40.0, w_s),
                gate_pop("accept_accumulator", 80, 1.5, 40.0, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                gc_check("cl3.rep_scorer", 80, 40.0, 25.0),
                gc_check("cl3.rust_scorer", 64, 50.0, 25.0),
            ]
        ),
        "meta": meta_common(
            id="nelb-r16-051",
            clock_domain="hf-hs-sim-relative-ms-t0-2026-05-06T09:00:00Z",
            tags=["hyperspectral-crop", "ACCEPT", "REJECT", "bounded-accept", "serialized-reconstruction", "operational-t2"],
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
        if rec["meta"]["round"] != 16:
            raise RuntimeError("round")
        if rec["meta"]["rights"]["intended_use"] != "research_only":
            raise RuntimeError("rights")
        if rec["meta"]["rights"]["linear_issue"] != "RM-793":
            raise RuntimeError("RM-793")
        hist = rast["isi_histogram"]
        ident = rast["isi_count_identity"]
        if sum(b["count"] for b in hist) != ident["isi_total"]:
            raise RuntimeError("isi hist")
        if ident["isi_total"] != ident["spikes"] - ident["distinct_active_neurons"]:
            raise RuntimeError("isi identity")
        if not rast["routing"]["table"]:
            raise RuntimeError("empty routing table")
    if len(ids) != len(set(ids)):
        raise RuntimeError(f"dup ids {ids}")
    print("local_checks ok", [r["id"] for r in records], "ids", len(ids))


def main():
    if "outputs/raw" in str(BATCH):
        raise RuntimeError("refusing to write outputs/raw")
    records = [rec_049(), rec_050(), rec_051()]
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
