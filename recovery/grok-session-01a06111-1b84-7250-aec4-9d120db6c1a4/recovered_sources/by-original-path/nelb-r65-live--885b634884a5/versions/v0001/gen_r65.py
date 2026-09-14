#!/usr/bin/env python3
"""Generate NELB round-2 research-only bridge pairs (create-only live write)."""

from __future__ import annotations

import json
import math
import os
import random
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, "/tmp")
from lif_raster import generate_lif_raster  # independent CUBA LIF, not a stream echo

PIPELINES = Path("/home/raulmc/rmems/synthetic-factory/pipelines")
sys.path.insert(0, str(PIPELINES))

LIVE_DIR = Path(
    "/home/raulmc/rmems/synthetic-factory/outputs/raw/2026-09-02-final-heavy/"
    "neuromorphic-event-language-bridge"
)
STAGING = Path("/tmp/nelb-r02")
BATCH_NAME = "batch-r02.jsonl"
NOTES_NAME = "NOTES-r02.md"

GENERATED_AT = "2026-09-02T20:40:00Z"

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

SNN_TAGS = ["race", "refractory", "adaptation"]

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
        "round": 2,
        "factory": "neuromorphic-event-language-bridge",
        "generator": "grok-4.6",
        "run_label": "2026-09-02-final-heavy",
        "rights": dict(RIGHTS),
        "snn_tags": list(SNN_TAGS),
    }
    m.update(extra)
    return m


def make_lif_raster(
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
    tau_m_ms: float,
):
    routing = {
        "source": source,
        "target": target,
        "table": table,
        "third_factor": third_factor,
    }
    raw = generate_lif_raster(
        neurons,
        mean_rate_hz,
        window_ms,
        seed,
        kernelized_event_times=None,
        tau_m=tau_m_ms,
        excerpt_cap=10**9,
        routing=routing,
    )
    window_ms = float(window_ms)
    window_s = window_ms / 1000.0
    spikes = int(raw["spikes"])
    excerpt = []
    rng = random.Random(seed + 17)
    by_n_count: dict[int, int] = defaultdict(int)
    for item in raw["excerpt"]:
        nid = int(item["neuron_id"])
        t_us = int(item["t_us"])
        k = by_n_count[nid]
        by_n_count[nid] += 1
        base = 1.15 + 0.7 * rng.random()
        noise = 0.96 + 0.08 * rng.random()
        amp = round(base * (0.82**k) * noise, 3)
        excerpt.append(
            {
                "t_us": t_us,
                "neuron_id": nid,
                "amplitude": amp,
                "channel": f"{channel_prefix}{nid:02d}",
            }
        )
    excerpt.sort(key=lambda e: (e["t_us"], e["neuron_id"]))
    if len(excerpt) != spikes:
        raise RuntimeError(f"LIF excerpt {len(excerpt)} != spikes {spikes}")
    if excerpt[-1]["t_us"] - excerpt[0]["t_us"] < 1000:
        raise RuntimeError("excerpt span < 1000 us")

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
        raise RuntimeError(f"ISI identity {sum(x['count'] for x in hist)} != {identity_n}")

    energy_pJ = spikes * 23
    energy_uJ = spikes * 23e-6
    if abs(float(raw["energy_pJ"]) - energy_pJ) > 1e-6:
        raise RuntimeError("LIF energy_pJ mismatch")
    if abs(float(raw["energy_uJ"]) - energy_uJ) > 1e-9:
        raise RuntimeError("LIF energy_uJ mismatch")
    expected = int(round(neurons * mean_rate_hz * window_s))
    if abs(spikes - expected) > 0:
        raise RuntimeError(f"budget {spikes} != {expected}")

    return {
        "window_ms": float(window_ms),
        "window_s": float(window_s),
        "neurons": int(neurons),
        "mean_rate_hz": float(mean_rate_hz),
        "spikes": spikes,
        "energy_pJ": energy_pJ,
        "energy_uJ": energy_uJ,
        "energy_model": "Loihi-2-class 4-core 23 pJ/spike",
        "excerpt": excerpt,
        "excerpt_amplitude_units": "normalized_membrane",
        "excerpt_is_full_window": True,
        "excerpt_span_us": int(excerpt[-1]["t_us"] - excerpt[0]["t_us"]),
        "refractory_rule_ms": 1.0,
        "isi_histogram": hist,
        "isi_source": "full_window_per_neuron_isi",
        "isi_count_identity": {
            "spikes": spikes,
            "distinct_active_neurons": len(by_n),
            "isi_total": identity_n,
        },
        "lif": {
            "model": "independent_cuba_lif",
            "tau_m_ms": float(tau_m_ms),
            "v_th": 1.0,
            "t_ref_ms": 1.0,
            "kernelized_event_times": False,
        },
        "anchor": anchor,
        "seed_note": (
            f"independent CUBA LIF MT19937 seed {seed}; tau_m {tau_m_ms} ms; "
            "not a re-encode of spike_events; amplitude adaptation 0.82**k plus noise"
        ),
        "routing": routing,
    }


def ev(t_rel_ms, channel, amplitude, **extra):
    rec = {
        "t_rel_ms": float(t_rel_ms),
        "channel": channel,
        "amplitude": float(amplitude),
    }
    rec.update(extra)
    return rec


def assert_stream(events, min_n=48, max_n=80):
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


def _exact(a, b, eps=1e-12):
    if abs(a - b) > eps:
        raise RuntimeError(f"arith {a} != {b}")


# ---------------------------------------------------------------------------
# nelb-r02-001 — CAPS remaining NO2 of a road-tunnel duct, designed, REJECT/MODIFY
# ---------------------------------------------------------------------------
def rec_001():
    k_c = 0.50
    dphi = 40.00
    phi = 48.00
    phi0 = 8.00
    _exact(phi - phi0, dphi)
    c_ppm = k_c * dphi
    _exact(c_ppm, 20.00)
    _exact(k_c * 8.00, 4.00)
    _exact(k_c * 16.00, 8.00)
    _exact(k_c * 24.00, 12.00)
    _exact(k_c * 48.00, 24.00)
    q_th = 1.20
    load = c_ppm * q_th
    _exact(load, 24.00)
    dphi_id = c_ppm / k_c
    _exact(dphi_id, 40.00)
    _exact(6000.0 + 1080.0, 7080.0)

    raster = make_lif_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=40.0,
        seed=2026090201,
        source="gw4.caps.no2",
        target="gorsewhin.duct_stop_core",
        table=[
            {"from": "caps_dphi", "to": "no2_estimator", "weight": 1.40},
            {"from": "caps_snr", "to": "caps_lock_core", "weight": 1.15},
            {"from": "capsveil_c", "to": "vendor_continue_advocate", "weight": 0.45},
        ],
        third_factor={
            "modulator": "da.caps_no2_conflict",
            "tau_e_s": 1.6,
            "tau_e_ms": 1600.0,
            "eligibility": "pre-post coincidence on continue-idle synapses; the plant CAPS modulator depresses continue-idle links when phase delay stays high inside tau_e of an SNR lock so a Capsveil last-good cannot hide a 20.00 ppm remaining-NO2 slip",
        },
        channel_prefix="caps.n",
        anchor="GW-4 CAPS 40 ms frame at Δφ 40.00 deg / SNR 12.0 (t_s 3000) reconstructing 20.00 ppm over the 12.00 isolate floor",
        tau_m_ms=10.0,
    )
    w_s = 0.040
    events = [
        ev(0.0, "caps.phi", 16.00, code="PHI_DEG", units="deg", note="plant-owned cavity-attenuated phase-shift NO2 of Gorsewhin Tunnel GW-4 duct D-6; remaining-NO2 family, not UV-DOAS SO2, not CLD NOx, not NDIR CO, not TDLAS NH3, not paramagnetic O2, not electrochemical H2S"),
        ev(180000.0, "caps.snr", 6.0, code="CAPS_SNR", units="1", note="early SNR under the 8.0 lock floor"),
        ev(360000.0, "recon.C", 4.00, code="C_PPM", units="ppm", note="0.50*8.00=4.00 exact; still under the 12.00 isolate floor"),
        ev(540000.0, "duct.T", 291.0, code="DUCT_K", units="K", note="plant duct thermocouple on copper DCS; independent witness; unread by Capsveil"),
        ev(720000.0, "capsveil.C", 2.40, code="VENDOR_PPM", units="ppm", note="Capsveil vendor CAPS-cloud; infra owner; patched transmitter timestamps"),
        ev(900000.0, "caps.phi", 24.00, code="PHI_DEG", units="deg"),
        ev(1080000.0, "recon.C", 8.00, code="C_PPM", units="ppm", note="0.50*16.00=8.00; isolate-adjacent band"),
        ev(1260000.0, "permit.slide", 40.00, code="PERM_S", units="s", note="permit clerk Briony Vale slid the NO2-slip clock 40.00 s; collusion party"),
        ev(1440000.0, "duct.T", 291.0, code="DUCT_K", units="K"),
        ev(1620000.0, "recon.dphi", 16.00, code="DPHI_DEG", units="deg", note="φ-φ0 identity at the 8.00 ppm band"),
        ev(1800000.0, "caps.phi", 32.00, code="PHI_DEG", units="deg"),
        ev(1980000.0, "recon.C", 12.00, code="C_PPM", units="ppm", note="0.50*24.00=12.00; isolate floor"),
        ev(2160000.0, "rotam.Q", 1.20, code="Q_TH", units="th", note="plant-owned duct rotameter; independent of Capsveil"),
        ev(2340000.0, "capsveil.C", 2.40, code="VENDOR_PPM", units="ppm"),
        ev(2520000.0, "caps.snr", 9.0, code="CAPS_SNR", units="1"),
        ev(2700000.0, "recon.phi0", 8.00, code="PHI0_DEG", units="deg", note="empty-cavity phase intercept used by the reconstruction"),
        ev(3000000.0, "caps.phi", 48.00, code="PHI_DEG", units="deg", note="isolate-floor frame; raster sidecar; Δφ=48.00-8.00=40.00"),
        ev(3000001.4, "caps.snr", 12.0, code="CAPS_SNR", units="1", note="1.4 ms SNR lock after φ; 12.0 >= 8.0"),
        ev(3180000.0, "recon.C", 20.00, code="C_PPM", units="ppm", note="0.50*40.00=20.00 exact; isolate 12.00, tunnel-kill 80.00"),
        ev(3360000.0, "recon.load", 24.00, code="LOAD_GH", units="g_h", note="20.00*1.20=24.00 exact NO2-load identity"),
        ev(3540000.0, "recon.dphi", 40.00, code="DPHI_DEG", units="deg", note="48.00-8.00=40.00 exact phase identity"),
        ev(3720000.0, "capsveil.drop", 1.0, code="CAP_DROP", units="bool", note="vendor CAPS packets dropped in Capsveil cloud for 40 s"),
        ev(3900000.0, "collude.clerk", 1.0, code="CLERK", units="bool"),
        ev(4080000.0, "duct.T", 290.0, code="DUCT_K", units="K", note="duct TC tracks the plant CAPS, not Capsveil 2.40"),
        ev(4260000.0, "rotam.Q", 1.20, code="Q_TH", units="th"),
        ev(4440000.0, "recon.phi0", 8.00, code="PHI0_DEG", units="deg"),
        ev(4620000.0, "capsveil.C", 2.35, code="VENDOR_PPM", units="ppm"),
        ev(4800000.0, "ops.prop", 1.0, code="CONTINUE_IDLE", units="bool", note="night operator Niall Croft: Capsveil is clean 2.40 ppm; continue D-6 idle ventilation"),
        ev(4980000.0, "recon.C", 20.00, code="C_PPM", units="ppm", note="repeat of the 20.00 ppm reconstruction as SoT"),
        ev(5400000.0, "gate.stop", 1.0, code="REJECT", units="decision", note="refuse continue-idle; 20.00 ppm and SNR 12.0; Capsveil not SoT"),
        ev(6000000.0, "damp.start", 1.0, code="DAMP_START", units="bool", note="bookend 1 of the 18.0 min damper-hold floor"),
        ev(7080000.0, "damp.floor", 1.0, code="DAMP_FLOOR", units="bool", note="6000 s + 1080 s = 7080 s = 18.0 min"),
        ev(7800000.0, "ops.kill", 1.0, code="TUNNEL_ESD", units="bool", note="Croft: ESD the whole Gorsewhin westbound until day-shift"),
        ev(8400000.0, "gate.hold", 1.0, code="MODIFY", units="decision", note="companion t2: damper-hold on plant CAPS as live interlock; tunnel ESD refused"),
        ev(9000000.0, "damplock.set", 1.0, code="DAMP_HELD", units="bool"),
        ev(9600000.0, "caps.phi", 56.00, code="PHI_DEG", units="deg"),
        ev(10200000.0, "recon.C", 24.00, code="C_PPM", units="ppm", note="0.50*48.00=24.00; still over 12.00 so damper holds"),
        ev(10800000.0, "capsveil.C", 2.30, code="VENDOR_PPM", units="ppm"),
        ev(11400000.0, "duct.T", 289.0, code="DUCT_K", units="K"),
        ev(12000000.0, "damp.held", 1.0, code="DAMP_HELD", units="bool"),
        ev(12600000.0, "unit.esd", 0.0, code="ESD_NOT_TAKEN", units="bool"),
        ev(13200000.0, "permit.slide", 40.00, code="PERM_S", units="s"),
        ev(13800000.0, "capsveil.drop", 1.0, code="CAP_DROP", units="bool"),
        ev(14400000.0, "damplock.held", 1.0, code="DAMP_HELD", units="bool"),
        ev(15000000.0, "recon.load", 28.80, code="LOAD_GH", units="g_h", note="24.00*1.20=28.80 on the post-stop frame"),
        ev(15600000.0, "rotam.Q", 1.20, code="Q_TH", units="th"),
        ev(16200000.0, "recon.dphi", 48.00, code="DPHI_DEG", units="deg", note="0.50*48.00=24.00 inverse check"),
        ev(16800000.0, "collude.clerk", 1.0, code="CLERK", units="bool"),
    ]
    assert_stream(events)
    if len(events) != 48:
        raise RuntimeError(len(events))

    traj = {
        "id": "nelb-r02-001-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "GW-CAPS-2026-0902",
            "domain": "caps_no2_road_tunnel_duct",
            "setting": "Gorsewhin Tunnel GW-4 (invented), westbound duct D-6. Plant-owned cavity-attenuated phase-shift photometer is the remaining-NO2 SoT. Capsveil vendor CAPS-cloud (infra owner) plus the NO2-slip permit clock are collusion parties, not witnesses. Invented plant; designed campaign. Not r59 UV-DOAS remaining SO2, not r52 CLD NOx, not r62 NDIR remaining CO, not r22 TDLAS NH3, not r46 paramagnetic O2, not r60 electrochemical H2S, not r21 OA-ICOS CH4.",
            "observables_at_decision": {
                "phi_deg": phi,
                "phi0_deg": phi0,
                "dphi_deg": dphi,
                "k_c": k_c,
                "C_ppm": c_ppm,
                "load_gh": load,
                "caps_snr": 12.0,
                "capsveil_ppm": 2.40,
                "permit_slide_s": 40.00,
                "isolate_floor_ppm": 12.00,
            },
            "margin_authority": "GW-4 tunnel SOP rev C: if reconstructed C_ppm >= 12.00 AND CAPS SNR >= 8.0, continue-idle is forbidden even if Capsveil reports 2.40 ppm. Tunnel ESD is a different gate. Kill tripwire is 80.00 ppm.",
        },
        "proposed_action": {
            "actor": "night tunnel operator Niall Croft, citing Capsveil 2.40 ppm and a quiet NO2 channel",
            "summary": "continue D-6 idle ventilation; 48.00 deg is lamp-age noise on a healthy NO2 slip",
            "basis_claimed": "Capsveil is the only OEM CAPS SoT and a night abort of D-6 is a traffic-nomination miss",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Continue-idle is refused. Serialized reconstruction: C_ppm = k_c * Δφ = 0.50 * 40.00 = 20.00, which is 8.00 ppm over the 12.00 isolate floor and 60.00 ppm under the 80.00 tunnel-kill tripwire, and CAPS SNR is 12.0 >= 8.0. Phase identity Δφ = φ - φ0 = 48.00 - 8.00 = 40.00; inverse Δφ = C / k_c = 20.00 / 0.50 = 40.00; NO2-load identity load = C * Q = 20.00 * 1.20 = 24.00 g/h. Permit clock was slid 40.00 s and vendor CAPS packets were dropped, so Capsveil is a collusion party (CAPS vendor plus operator plus permit clerk Briony Vale). Ordered: refuse continue-idle now. Scope: this REJECT does not ESD the westbound tube (that is the companion question) and does not isolate the duct thermocouple.",
            "threshold": "C_ppm>=12.00 AND caps_snr>=8.0 => refuse continue-idle; Capsveil is not SoT; tunnel-kill if C_ppm>=80.00",
            "stated_residuals": "damper hold still required to hold the 20.00 ppm; 20.00 vs a true 80.00 kill is a traffic cut; Capsveil remains the only OEM CAPS channel",
        },
        "executed_action": {
            "summary": "REJECT at t_s 5400: continue-idle refused; Capsveil not SoT; reconstruction locked",
            "tool": "gw4-caps-duct-gate-cli",
            "observation": "C 20.00 ppm recomputes from Δφ 40.00 deg; plant CAPS hashed; Capsveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "CAPS φ 48.00 deg; raster frame; C 20.00 ppm"},
                {"t_s": 4800.0, "event": "ops proposes continue-idle"},
                {"t_s": 5400.0, "event": "REJECT continue-idle"},
                {"t_s": 6000.0, "event": "18 min damper-hold bookend 1"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 8400.0, "event": "companion MODIFY damper-hold vs tunnel ESD"},
            ],
            "observed_effects": [
                "remaining NO2 recomputes from the serialized CAPS model at every recon.C event",
                "a Capsveil-only head would have continued D-6 overnight",
                "18 min damper-hold floor is in the stream (damp.start, damp.floor)",
            ],
            "surprises": [
                "a clean vendor 2.40 ppm corridor and a 40 s permit slide co-existed with a 20.00 ppm plant reconstruction",
            ],
            "new_state": {
                "d6": "continue-idle blocked",
                "capsveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.43,
            [
                ("caps_no2_reconstruction", 0.14),
                ("conjunctive_isolate_floor", 0.12),
                ("capsveil_nonsubstitution", 0.10),
                ("three_party_collusion", 0.10),
                ("damp_time_cost", -0.03),
            ],
            "scored for a continue-idle REJECT on a recomputable CAPS NO2 slip while refusing a Capsveil last-good patch and a permit clock slide; 18 min floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["REJECT", "caps-no2", "serialized-reconstruction", "operational-companion"],
            distillation_value="Independent LIF raster plus serialized k_c*Δφ remaining-NO2 reconstruction beats a vendor last-good; race is the 1.4 ms φ/SNR pair; refractory and adaptation are in the CUBA excerpt.",
            distillation_note="CAPS-NO2 gate: serialized k_c*Δφ plus SNR lock beats a vendor last-good patch; companion t2 is the damper-hold, not a referral vote",
        ),
    }
    traj2 = {
        "id": "nelb-r02-001-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "GW-CAPS-2026-0902-exec",
            "domain": "damper_hold_caps_no2_interlock_execution",
            "setting": "Same GW-4 after the REJECT. Operator proposes westbound-tube ESD. This companion is the operational damper-hold with the plant CAPS as the live interlock, not a second NO2 vote.",
            "observables_at_decision": {
                "C_ppm": 24.00,
                "damp_floor_s": 1080.0,
                "tunnel_esd_proposed": True,
                "damp_set": True,
            },
            "margin_authority": "GW-4 execution SOP: damper-hold on the plant CAPS interlock; tube ESD is a different gate.",
        },
        "proposed_action": {
            "actor": "night tunnel operator Niall Croft",
            "summary": "ESD the whole Gorsewhin westbound until day-shift; 18 min already paid and Capsveil still shows 2.30 ppm",
            "basis_claimed": "the REJECT already stopped D-6, so a tube kill is the cheapest hold",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Damper-hold plus plant CAPS as the live interlock. The 18 min damper floor is complete and the isolate tripwire (C_ppm >= 12.00) is still armed on the plant CAPS head. MODIFY the default Capsveil-restore SOP into a plant-CAPS-only interlock. Do not ESD the westbound tube. Do not restore idle ventilation on Capsveil. 24.00 ppm post-stop is still the plant SoT until a new frame clears 12.00.",
            "threshold": "damper_hold AND damp_floor_complete AND tunnel_esd_not_taken AND continue_not_restored",
            "stated_residuals": "D-6 stays held; Capsveil still the only OEM CAPS channel",
        },
        "executed_action": {
            "summary": "damper held at t_s 8400; tunnel ESD not latched; Capsveil restore not taken",
            "tool": "gw4-damp-exec",
            "observation": "recon.C 24.00 ppm after stop; damper line-up complete; Capsveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "damper clock started after REJECT"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 7800.0, "event": "tunnel ESD proposed"},
                {"t_s": 8400.0, "event": "MODIFY damper-hold; tunnel ESD refused"},
            ],
            "observed_effects": [
                "Capsveil restore did not reopen the NO2-slip call",
                "tunnel ESD never fired; D-6 held damper on the plant CAPS",
            ],
            "surprises": ["post-stop CAPS climbed to 24.00 ppm while Capsveil still read 2.30"],
            "new_state": {"damper": "held", "tube": "in service", "d6": "held"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("damp_hold", 0.12),
                ("no_tunnel_esd", 0.10),
                ("capsveil_nonsubstitution", 0.08),
                ("damp_floor_complete", 0.06),
                ("held_traffic_cost", -0.02),
            ],
            "operational execution gate: damper-hold because Capsveil is not a restore license; not an NO2-slip re-vote",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "damper-hold"]),
    }
    return {
        "id": "nelb-r02-001",
        "snn_tags": list(SNN_TAGS),
        "spike_events": events,
        "language_view": {
            "description": "Gorsewhin Tunnel GW-4. Plant-owned CAPS reconstructs 20.00 ppm NO2 from 0.50*40.00 while Capsveil still reports 2.40 ppm. The gate REJECTs continue-idle. An 18 min damper-hold floor is serialized in the stream. Companion t2 MODIFYs a westbound-tube ESD into a plant-CAPS damper-hold.",
            "trajectory": traj,
            "trajectory_damper_hold": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "caps.phi / caps.snr": "CAPS phase and SNR; the physics channels the reconstruction consumes",
                "recon.C / recon.load / recon.dphi / recon.phi0": "serialized remaining-NO2 ppm, load identity, and phase identity",
                "duct.T / capsveil.C / permit.slide / capsveil.drop / collude.clerk": "duct thermocouple, vendor CAPS cloud, permit clock slide, dropped packets, clerk; the denial and collusion channels",
                "ops.prop / gate.stop / ops.kill / gate.hold": "continue-idle proposal, REJECT, tunnel-ESD proposal, companion MODIFY",
                "damp.start / damp.floor / damplock.set / damp.held / unit.esd": "operational companion channels plus the 18 min floor",
            },
            "temporal_motifs": [
                "vendor-green while plant-over: capsveil.C 2.40 next to recon.C 20.00",
                "reconstruction as event: recon.C 20.00 equals 0.50*40.00",
                "REJECT then operational MODIFY: gate.stop at 5400 s, gate.hold at 8400 s",
                "slow floor in-stream: damp.start 6000 s, damp.floor 7080 s (18.0 min)",
                "tight CAPS pair: caps.phi then caps.snr +1.4 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Capsveil is 2.40 ppm' = capsveil.C 2.40; '20 ppm remaining NO2' = recon.C 20.00; 'refuse continue-idle' = gate.stop REJECT; 'damper not tube ESD' = gate.hold MODIFY",
            "why_high_value": "New cavity-attenuated phase-shift remaining-NO2 family on a road-tunnel duct (not UV-DOAS SO2, not CLD NOx, not NDIR CO, not TDLAS NH3, not OA-ICOS CH4). Lead REJECT of continue-idle on a recomputable NO2 slip that a vendor CAPS patch and a permit clock slide would have cleared. Independent CUBA LIF raster (not a stream echo). Companion t2 is operational damper-hold. sim_or_real=designed.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 2026090201, "stream_note": "stream amplitudes are authored constants; raster is independent CUBA LIF"},
                "draw_order": "independent CUBA LIF per neuron; gap-constrained times; per-spike adaptation and noise",
                "thinning": "CAPS photometer exists at ~1 Hz; stream keeps 5 φ points; recon keeps 5 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "caps.phi": 1.4,
                    "caps.snr": 1.4,
                    "recon.C": 60000,
                    "recon.load": 60000,
                    "recon.dphi": 60000,
                    "recon.phi0": 60000,
                    "duct.T": 60000,
                    "capsveil.C": 60000,
                    "permit.slide": 60000,
                    "capsveil.drop": 60000,
                    "collude.clerk": 60000,
                    "rotam.Q": 60000,
                    "ops.prop": 60000,
                    "gate.stop": 60000,
                    "damp.start": 60000,
                    "damp.floor": 60000,
                    "ops.kill": 60000,
                    "gate.hold": 60000,
                    "damplock.set": 60000,
                    "damp.held": 60000,
                    "unit.esd": 60000,
                    "damplock.held": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-09-02T01:00:00Z campaign start",
            },
            "distillation_targets": [
                "CAPS-NO2 reconstruction head: C = k_c * Δφ; Δφ = φ - φ0; load = C * Q",
                "conjunctive isolate floor vs continue-idle vs tunnel ESD",
                "vendor-CAPS nonsubstitution plus three-party collusion including the infra owner",
                "operational companion: damper-hold without restoring on Capsveil",
                "independent CUBA LIF raster with race/refractory/adaptation tags",
            ],
        },
        "reconstruction_model": {
            "name": "caps_tunnel_no2",
            "formula": "C_ppm = k_c * (phi_deg - phi0_deg); dphi_deg = phi_deg - phi0_deg; load_gh = C_ppm * Q_th",
            "parameters": {
                "k_c": 0.50,
                "phi0_deg": 8.00,
                "Q_th": 1.20,
                "isolate_floor_ppm": 12.00,
                "kill_ppm": 80.00,
                "snr_lock": 8.0,
                "damp_min": 18.0,
            },
            "worked_example": {"phi_deg": 48.00, "dphi_deg": 40.00, "C_ppm": 20.00, "load_gh": 24.00},
            "check": "0.50 * 40.00 = 20.00 exactly; 48.00 - 8.00 = 40.00 exactly; 20.00 * 1.20 = 24.00 exactly; 6000 s + 1080 s = 7080 s = 18.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.040,
            "code": "gw4.caps_duct_gate",
            "note": "REJECT accumulator wins: plant CAPS NO2 evidence overpowers the Capsveil continue advocate",
            "decode_rule": "reject-continue if no2_estimator AND caps_lock fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("no2_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("caps_lock", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("reject_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "gw4.caps_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 40.0},
                {"check": "gw4.damp_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r02-001",
            clock_domain="gw4-caps-campaign-relative-ms-t0-2026-09-02T01:00:00Z",
            tags=["caps-no2", "REJECT", "MODIFY", "serialized-reconstruction", "operational-t2", "independent-lif"],
            distillation_value="Independent LIF raster teaches race/refractory/adaptation while the language view teaches CAPS remaining-NO2 reconstruction-as-SoT.",
        ),
    }


# ---------------------------------------------------------------------------
# nelb-r02-002 — PTR-MS remaining MDI of a PU foam booth, hil, MODIFY/ACCEPT
# ---------------------------------------------------------------------------
def rec_002():
    k_p = 4.00
    i_ncps = 8.00
    c_ppb = k_p * i_ncps
    _exact(c_ppb, 32.00)
    _exact(k_p * 2.00, 8.00)
    _exact(k_p * 4.00, 16.00)
    _exact(k_p * 6.00, 24.00)
    _exact(k_p * 10.00, 40.00)
    q_th = 0.50
    mdot = c_ppb * q_th
    _exact(mdot, 16.00)
    ratio = i_ncps / 2.00
    _exact(ratio, 4.00)
    _exact(2820.0 + 1440.0, 4260.0)

    raster = make_lif_raster(
        neurons=25,
        mean_rate_hz=50.0,
        window_ms=32.0,
        seed=2026090202,
        source="bm7.ptr.mdi",
        target="brindlemere.booth_isolate_core",
        table=[
            {"from": "ptr_I", "to": "mdi_estimator", "weight": 1.35},
            {"from": "ptr_snr", "to": "source_norm_core", "weight": 1.20},
            {"from": "ptrveil_c", "to": "vendor_continue_advocate", "weight": 0.40},
        ],
        third_factor={
            "modulator": "ach.ptr_reagent_skip_salience",
            "tau_e_s": 1.2,
            "tau_e_ms": 1200.0,
            "eligibility": "pre-post coincidence on keep-booth synapses; the PTR-MS modulator depresses keep-booth and referral links when ion current stays high inside tau_e of an SNR lock so a Ptrveil last-good cannot hide 32.00 ppb MDI or name Iona Beck",
        },
        channel_prefix="ptr.n",
        anchor="BM-7 HIL coupon 32 ms frame at I 8.00 ncps / SNR 14.0 (t_s 1560) reconstructing 32.00 ppb over the 16.00 isolate floor",
        tau_m_ms=12.0,
    )
    w_s = 0.032
    events = [
        ev(0.0, "ptr.I", 2.00, code="I_NCPS", units="ncps", note="HIL PTR-MS on a dummy PU foam booth in PTR-HIL-3; remaining-MDI family, not PID VOC, not FID THC, not QEPAS, not SPR cyanide, not pellistor LEL, not UV-fluorescence OIW"),
        ev(180000.0, "ptr.snr", 9.0, code="PTR_SNR", units="1", note="early source SNR; isolate needs SNR>=12"),
        ev(360000.0, "recon.C", 8.00, code="C_PPB", units="ppb", note="4.00*2.00=8.00 exact"),
        ev(540000.0, "src.zero", 1.0, code="SRC_AE", units="bool", note="plant reagent-zero AE present on the early frame"),
        ev(720000.0, "ptrveil.C", 3.20, code="VENDOR_PPB", units="ppb", note="Ptrveil last-good MDI cloud; not admissible SoT"),
        ev(900000.0, "ptr.I", 4.00, code="I_NCPS", units="ncps"),
        ev(1080000.0, "recon.C", 16.00, code="C_PPB", units="ppb", note="4.00*4.00=16.00; at the 16.00 isolate floor"),
        ev(1260000.0, "src.zero", 0.0, code="SRC_AE", units="bool", note="missing reagent-zero AE burst; Ptrveil UTC vs plant UTC+2 skipped the zero by 120 min"),
        ev(1440000.0, "booth.Q", 0.50, code="Q_TH", units="th", note="plant-owned booth extract flow on copper fieldbus; independent of Ptrveil"),
        ev(1560000.0, "ptr.I", 8.00, code="I_NCPS", units="ncps", note="isolate-floor frame; raster sidecar"),
        ev(1560001.2, "ptr.snr", 14.0, code="PTR_SNR", units="1", note="1.2 ms source-norm after PTR ion current"),
        ev(1740000.0, "recon.C", 32.00, code="C_PPB", units="ppb", note="4.00*8.00=32.00 exact; isolate 16.00, house-dump 80.00"),
        ev(1920000.0, "recon.mdot", 16.00, code="MDOT_PPBH", units="ppb_h", note="32.00*0.50=16.00 exact; MDI-mass-rate identity"),
        ev(2100000.0, "recon.ratio", 4.00, code="I_RATIO", units="1", note="8.00/2.00=4.00 exact ion-ratio identity"),
        ev(2280000.0, "ptrveil.C", 3.20, code="VENDOR_PPB", units="ppb"),
        ev(2460000.0, "ops.prop", 1.0, code="KEEP_BOOTH_REFER", units="bool", note="night lead Della Croft: keep booth B-4 and refer PTR tech Iona Beck"),
        ev(2640000.0, "gate.isol", 1.0, code="MODIFY", units="decision", note="isolate this booth; refuse the person-referral; Ptrveil not SoT"),
        ev(2820000.0, "booth.lock", 1.0, code="BOOTH_ISOL", units="bool", note="bookend 1 of the 24.0 min new-source floor"),
        ev(3000000.0, "ptr.I", 6.00, code="I_NCPS", units="ncps"),
        ev(3180000.0, "recon.C", 24.00, code="C_PPB", units="ppb", note="4.00*6.00=24.00 still over 16.00"),
        ev(3360000.0, "src.zero", 0.0, code="SRC_AE", units="bool"),
        ev(3540000.0, "booth.Q", 0.50, code="Q_TH", units="th"),
        ev(3720000.0, "ptrveil.C", 3.10, code="VENDOR_PPB", units="ppb"),
        ev(3900000.0, "recon.mdot", 12.00, code="MDOT_PPBH", units="ppb_h", note="24.00*0.50=12.00"),
        ev(4080000.0, "recon.ratio", 3.00, code="I_RATIO", units="1"),
        ev(4260000.0, "src.floor", 1.0, code="SRC_FLOOR", units="bool", note="2820 s + 1440 s = 4260 s = 24.0 min"),
        ev(4440000.0, "ops.restart", 1.0, code="NEW_SOURCE", units="bool", note="Croft: restart B-4 on a new reagent bottle after the floor"),
        ev(4620000.0, "gate.restart", 1.0, code="ACCEPT", units="decision", note="companion t2: new-source restart of the dummy booth; keep-running refused earlier"),
        ev(4800000.0, "src.new", 1.0, code="SRC_NEW", units="bool"),
        ev(4980000.0, "ptr.I", 10.00, code="I_NCPS", units="ncps", note="post-isolate dummy still high until the new source"),
        ev(5160000.0, "recon.C", 40.00, code="C_PPB", units="ppb", note="4.00*10.00=40.00 on the pre-restart dummy"),
        ev(5340000.0, "ptrveil.C", 3.00, code="VENDOR_PPB", units="ppb"),
        ev(5520000.0, "iona.badge", 0.0, code="TECH_FAULT", units="bool", note="Iona Beck exonerated: missing reagent-zero AE plus timezone skip, not last-to-badge"),
        ev(5700000.0, "booth.lock", 1.0, code="BOOTH_ISOL", units="bool"),
        ev(5880000.0, "src.zero", 1.0, code="SRC_AE", units="bool", note="new-source reagent-zero AE present"),
        ev(6060000.0, "ptr.snr", 14.0, code="PTR_SNR", units="1"),
        ev(6240000.0, "booth.Q", 0.50, code="Q_TH", units="th"),
        ev(6420000.0, "recon.mdot", 20.00, code="MDOT_PPBH", units="ppb_h"),
        ev(6600000.0, "keep.run", 0.0, code="KEEP_REFUSED", units="bool"),
        ev(6780000.0, "ptrveil.C", 3.00, code="VENDOR_PPB", units="ppb"),
        ev(6960000.0, "src.new", 1.0, code="SRC_NEW", units="bool"),
        ev(7140000.0, "iona.badge", 0.0, code="TECH_FAULT", units="bool"),
        ev(7320000.0, "recon.ratio", 5.00, code="I_RATIO", units="1"),
        ev(7500000.0, "booth.held", 1.0, code="BOOTH_ISOL", units="bool"),
        ev(7680000.0, "ops.prop", 1.0, code="KEEP_BOOTH_REFER", units="bool"),
        ev(7860000.0, "gate.isol", 1.0, code="MODIFY", units="decision"),
        ev(8040000.0, "src.floor", 1.0, code="SRC_FLOOR", units="bool"),
        ev(8220000.0, "gate.restart", 1.0, code="ACCEPT", units="decision"),
    ]
    assert_stream(events)
    if len(events) != 48:
        raise RuntimeError(len(events))

    traj = {
        "id": "nelb-r02-002-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "BM-PTR-2026-0902",
            "domain": "ptrms_mdi_pu_foam_booth",
            "setting": "Brindlemere Foam BM-7 (invented), dummy booth B-4 in PTR-HIL-3. Plant-owned proton-transfer-reaction mass spec is the remaining-MDI SoT. Ptrveil vendor PTR-cloud is not SoT. HIL dummy; not a live plant. Not r57 PID VOC, not leftover-mill FID THC, not r19 QEPAS, not r26 SPR cyanide, not r61 pellistor LEL, not r56 UV-fluorescence OIW.",
            "observables_at_decision": {
                "I_ncps": i_ncps,
                "k_p": k_p,
                "C_ppb": c_ppb,
                "mdot_ppbh": mdot,
                "I_ratio": ratio,
                "ptr_snr": 14.0,
                "ptrveil_ppb": 3.20,
                "src_zero_ae": False,
                "isolate_floor_ppb": 16.00,
            },
            "margin_authority": "BM-7 HIL SOP rev B: if reconstructed C_ppb >= 16.00 AND PTR SNR >= 12.0, keep-booth is forbidden even if Ptrveil reports 3.20 ppb. Person-referral of the PTR tech is not a substitute isolate. Dump tripwire is 80.00 ppb.",
        },
        "proposed_action": {
            "actor": "night lead Della Croft, citing Ptrveil 3.20 ppb and a quiet ion channel",
            "summary": "keep dummy booth B-4 in service and refer PTR tech Iona Beck for a missed reagent-zero",
            "basis_claimed": "Ptrveil is the OEM SoT; Iona was last-to-badge the dummy cell",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Keep-booth is refused; isolate B-4. Serialized reconstruction: C_ppb = k_p * I = 4.00 * 8.00 = 32.00, which is 16.00 ppb over the 16.00 isolate floor and 48.00 ppb under the 80.00 dump tripwire, and PTR SNR is 14.0 >= 12.0. Ion-ratio identity I/I0 = 8.00/2.00 = 4.00; mass-rate identity mdot = C * Q = 32.00 * 0.50 = 16.00. Missing reagent-zero AE plus Ptrveil UTC vs plant UTC+2 skip the zero by 120 min, so Iona Beck is not last-to-badge-guilty. Ordered: isolate this dummy booth; do not refer the tech; Ptrveil is not SoT. Scope: this MODIFY does not dump the foam hall (that is a different gate) and does not restart until the 24 min new-source floor.",
            "threshold": "C_ppb>=16.00 AND ptr_snr>=12.0 => isolate booth; Ptrveil is not SoT; person-referral is not an isolate",
            "stated_residuals": "24 min new-source floor still required; 32.00 vs a true 80.00 dump is a production cut; Ptrveil remains the only OEM PTR channel",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 2640: B-4 isolated; Iona not referred; Ptrveil not SoT",
            "tool": "bm7-ptr-booth-gate-cli",
            "observation": "C 32.00 ppb recomputes from I 8.00 ncps; dummy booth locked; reagent-zero AE absent on the isolate frame",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 1560.0, "event": "PTR I 8.00 ncps; raster frame; C 32.00 ppb"},
                {"t_s": 2460.0, "event": "ops proposes keep-booth plus refer Iona"},
                {"t_s": 2640.0, "event": "MODIFY isolate booth; referral refused"},
                {"t_s": 2820.0, "event": "24 min new-source bookend 1"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4620.0, "event": "companion ACCEPT new-source restart"},
            ],
            "observed_effects": [
                "remaining MDI recomputes from the serialized PTR-MS model at every recon.C event",
                "a Ptrveil-only head would have kept B-4 and named Iona",
                "24 min new-source floor is in the stream (booth.lock, src.floor)",
            ],
            "surprises": [
                "timezone-skipped reagent-zero AE, not last-to-badge, was the only missing plant witness",
            ],
            "new_state": {
                "b4": "isolated",
                "iona": "exonerated",
                "ptrveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 1080000.0,
        },
        "reward_components": reward(
            0.40,
            [
                ("ptr_mdi_reconstruction", 0.14),
                ("conjunctive_isolate_floor", 0.12),
                ("ptrveil_nonsubstitution", 0.08),
                ("tech_exoneration", 0.08),
                ("isolate_time_cost", -0.02),
            ],
            "scored for an isolate MODIFY on a recomputable PTR-MS MDI slip while refusing a Ptrveil last-good and a last-to-badge referral; 24 min floor is priced as downtime",
        ),
        "meta": meta_common(
            tags=["MODIFY", "ptrms-mdi", "serialized-reconstruction", "operational-companion", "exoneration"],
            distillation_value="Independent LIF raster plus serialized k_p*I remaining-MDI reconstruction; race is the 1.2 ms I/SNR pair; refractory and adaptation are in the CUBA excerpt.",
            distillation_note="PTR-MS MDI gate: serialized k_p*I plus SNR lock beats a vendor last-good and a person-referral; companion t2 is the new-source restart",
        ),
    }
    traj2 = {
        "id": "nelb-r02-002-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "BM-PTR-2026-0902-exec",
            "domain": "new_source_ptr_mdi_restart_execution",
            "setting": "Same PTR-HIL-3 dummy after the isolate. Operator proposes a new-source restart of B-4. This companion is the operational restart, not a second MDI vote.",
            "observables_at_decision": {
                "C_ppb": 40.00,
                "src_floor_s": 1440.0,
                "src_new": True,
                "iona_fault": False,
            },
            "margin_authority": "BM-7 execution SOP: new-source restart after the 24 min floor; keep-running remains refused.",
        },
        "proposed_action": {
            "actor": "night lead Della Croft",
            "summary": "restart dummy booth B-4 on a new reagent bottle now that the 24 min floor is paid",
            "basis_claimed": "the isolate already stopped B-4; a new source is the cheapest return",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "New-source restart of the dummy booth after the 24 min floor. Keep-running stays refused. Iona remains exonerated. Ptrveil is still not SoT. ACCEPT the new-source restart of B-4 only. Do not restore the hall. Do not treat Ptrveil 3.00 ppb as a clear.",
            "threshold": "src_floor_complete AND booth_isolated AND keep_running_refused AND ptrveil_not_sot",
            "stated_residuals": "dummy still reads 40.00 ppb until the new source takes; hall stays out of scope",
        },
        "executed_action": {
            "summary": "new source accepted at t_s 4620; keep-running not restored; Iona not blamed",
            "tool": "bm7-src-exec",
            "observation": "reagent-zero AE present on the new bottle; dummy still isolated from the hall",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 2820.0, "event": "new-source clock started after isolate"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4440.0, "event": "new-source restart proposed"},
                {"t_s": 4620.0, "event": "ACCEPT new-source restart"},
            ],
            "observed_effects": [
                "Ptrveil restore did not reopen the MDI call",
                "Iona was not last-to-badge; new-source AE is present",
            ],
            "surprises": ["post-isolate dummy climbed to 40.00 ppb while Ptrveil still read 3.00"],
            "new_state": {"booth": "new-source restart", "hall": "in service", "iona": "exonerated"},
            "latency_ms": 1440000.0,
        },
        "reward_components": reward(
            0.35,
            [
                ("new_source_restart", 0.12),
                ("keep_running_refused", 0.10),
                ("ptrveil_nonsubstitution", 0.08),
                ("tech_exoneration", 0.06),
                ("held_booth_cost", -0.01),
            ],
            "operational execution gate: new-source restart because Ptrveil is not a restore license; not an MDI re-vote",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "new-source"]),
    }
    return {
        "id": "nelb-r02-002",
        "snn_tags": list(SNN_TAGS),
        "spike_events": events,
        "language_view": {
            "description": "Brindlemere Foam BM-7 HIL dummy. Plant-owned PTR-MS reconstructs 32.00 ppb MDI from 4.00*8.00 while Ptrveil still reports 3.20 ppb. The gate MODIFYs keep-booth into an isolate and refuses a last-to-badge referral of Iona Beck. A 24 min new-source floor is serialized. Companion t2 ACCEPTs the new-source restart.",
            "trajectory": traj,
            "trajectory_new_source_restart": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "ptr.I / ptr.snr": "PTR ion current and SNR; the physics channels the reconstruction consumes",
                "recon.C / recon.mdot / recon.ratio": "serialized remaining-MDI ppb, mass-rate identity, and ion-ratio identity",
                "src.zero / ptrveil.C / booth.Q / iona.badge": "reagent-zero AE, vendor PTR cloud, extract flow, tech-fault denial",
                "ops.prop / gate.isol / ops.restart / gate.restart": "keep-booth proposal, MODIFY isolate, new-source proposal, companion ACCEPT",
                "booth.lock / src.floor / src.new / booth.held / keep.run": "operational companion channels plus the 24 min floor",
            },
            "temporal_motifs": [
                "vendor-green while plant-over: ptrveil.C 3.20 next to recon.C 32.00",
                "reconstruction as event: recon.C 32.00 equals 4.00*8.00",
                "MODIFY then operational ACCEPT: gate.isol at 2640 s, gate.restart at 4620 s",
                "slow floor in-stream: booth.lock 2820 s, src.floor 4260 s (24.0 min)",
                "tight PTR pair: ptr.I then ptr.snr +1.2 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Ptrveil is 3.20 ppb' = ptrveil.C 3.20; '32 ppb remaining MDI' = recon.C 32.00; 'isolate booth' = gate.isol MODIFY; 'new-source restart' = gate.restart ACCEPT",
            "why_high_value": "New PTR-MS remaining-MDI family on a PU foam HIL dummy (not PID VOC, not FID, not QEPAS, not pellistor). Lead MODIFY isolate on a recomputable MDI slip plus timezone-exoneration of the PTR tech. Independent CUBA LIF raster. Companion t2 is operational new-source restart. sim_or_real=hil.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 2026090202, "stream_note": "stream amplitudes are authored constants; raster is independent CUBA LIF"},
                "draw_order": "independent CUBA LIF per neuron; gap-constrained times; per-spike adaptation and noise",
                "thinning": "PTR-MS exists at ~1 Hz; stream keeps 5 I points; recon keeps 5 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "ptr.I": 1.2,
                    "ptr.snr": 1.2,
                    "recon.C": 60000,
                    "recon.mdot": 60000,
                    "recon.ratio": 60000,
                    "src.zero": 60000,
                    "ptrveil.C": 60000,
                    "booth.Q": 60000,
                    "ops.prop": 60000,
                    "gate.isol": 60000,
                    "booth.lock": 60000,
                    "src.floor": 60000,
                    "ops.restart": 60000,
                    "gate.restart": 60000,
                    "src.new": 60000,
                    "iona.badge": 60000,
                    "keep.run": 60000,
                    "booth.held": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-09-02T02:00:00Z HIL coupon start",
            },
            "distillation_targets": [
                "PTR-MS MDI reconstruction head: C = k_p * I; mdot = C * Q; I/I0 ratio",
                "conjunctive isolate floor vs keep-booth vs hall dump",
                "vendor-PTR nonsubstitution plus timezone exoneration vs last-to-badge",
                "operational companion: new-source restart without restoring on Ptrveil",
                "independent CUBA LIF raster with race/refractory/adaptation tags",
            ],
        },
        "reconstruction_model": {
            "name": "ptrms_foam_mdi",
            "formula": "C_ppb = k_p * I_ncps; mdot_ppbh = C_ppb * Q_th; I_ratio = I_ncps / I0_ncps",
            "parameters": {
                "k_p": 4.00,
                "I0_ncps": 2.00,
                "Q_th": 0.50,
                "isolate_floor_ppb": 16.00,
                "dump_ppb": 80.00,
                "snr_lock": 12.0,
                "src_min": 24.0,
            },
            "worked_example": {"I_ncps": 8.00, "C_ppb": 32.00, "mdot_ppbh": 16.00, "I_ratio": 4.00},
            "check": "4.00 * 8.00 = 32.00 exactly; 32.00 * 0.50 = 16.00 exactly; 8.00 / 2.00 = 4.00 exactly; 2820 s + 1440 s = 4260 s = 24.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 32.0,
            "decision_window_s": 0.032,
            "code": "bm7.ptr_booth_gate",
            "note": "MODIFY accumulator wins: plant PTR-MS MDI evidence overpowers the Ptrveil keep advocate",
            "decode_rule": "isolate if mdi_estimator AND source_norm fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("mdi_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("source_norm", 50, 1.2, 50.0, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("modify_latch", 80, 1.6, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "bm7.ptr_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 32.0},
                {"check": "bm7.src_scorer", "neurons": 50, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r02-002",
            clock_domain="bm7-ptr-hil-relative-ms-t0-2026-09-02T02:00:00Z",
            tags=["ptrms-mdi", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2", "independent-lif", "exoneration"],
            distillation_value="Independent LIF raster teaches race/refractory/adaptation while the language view teaches PTR-MS remaining-MDI reconstruction-as-SoT plus timezone exoneration.",
        ),
    }


# ---------------------------------------------------------------------------
# nelb-r02-003 — microwave PCD remaining τ_eff of a Cz-Si brick, simulated, ACCEPT/REJECT
# ---------------------------------------------------------------------------
def rec_003():
    k_t = 0.50
    t_1e = 16.00
    tau = k_t * t_1e
    _exact(tau, 8.00)
    _exact(k_t * 40.00, 20.00)
    _exact(k_t * 24.00, 12.00)
    _exact(k_t * 12.00, 6.00)
    l2 = 64.00
    d_eff = l2 / tau
    _exact(d_eff, 8.00)
    ratio = t_1e / tau
    _exact(ratio, 2.00)
    _exact(6000.0 + 720.0, 6720.0)

    raster = make_lif_raster(
        neurons=16,
        mean_rate_hz=62.5,
        window_ms=36.0,
        seed=2026090203,
        source="qh2.pcd.tau",
        target="quartzholt.brick_accept_core",
        table=[
            {"from": "pcd_t1e", "to": "tau_estimator", "weight": 1.30},
            {"from": "pcd_snr", "to": "pcd_lock_core", "weight": 1.10},
            {"from": "pcdveil_tau", "to": "vendor_dump_advocate", "weight": 0.42},
        ],
        third_factor={
            "modulator": "na.pcd_brick_scope_eligibility",
            "tau_e_s": 2.0,
            "tau_e_ms": 2000.0,
            "eligibility": "pre-post coincidence on furnace-dump synapses; the plant PCD modulator depresses dump-all links when t_1e stays short inside tau_e of an SNR lock so a Pcdveil last-good cannot hide an 8.00 us remaining-lifetime slip on K-4 or expand the isolate past K-4",
        },
        channel_prefix="pcd.n",
        anchor="QH-2 PCD-SIM-6 36 ms frame at t_1e 16.00 us / SNR 11.0 (t_s 3000) reconstructing 8.00 us under the 12.00 isolate floor, K-4 only",
        tau_m_ms=8.0,
    )
    w_s = 0.036
    events = [
        ev(0.0, "pcd.t1e", 40.00, code="T1E_US", units="us", note="simulated microwave photoconductance-decay of Quartzholt PV QH-2 brick K-4; remaining-lifetime family, not phosphor-lifetime, not SPR, not lock-in thermography, not alanine EPR, not microwave-cavity moisture"),
        ev(180000.0, "pcd.snr", 7.0, code="PCD_SNR", units="1", note="early SNR under the 8.0 lock floor"),
        ev(360000.0, "recon.tau", 20.00, code="TAU_US", units="us", note="0.50*40.00=20.00 exact; still over the 12.00 isolate floor"),
        ev(540000.0, "brick.T", 300.0, code="BRICK_K", units="K", note="plant brick thermocouple on the simulated coupon; independent of Pcdveil"),
        ev(720000.0, "pcdveil.tau", 48.00, code="VENDOR_US", units="us", note="Pcdveil last-good lifetime cloud; healthy-looking 48.00 us; not admissible SoT"),
        ev(900000.0, "pcd.t1e", 24.00, code="T1E_US", units="us"),
        ev(1080000.0, "recon.tau", 12.00, code="TAU_US", units="us", note="0.50*24.00=12.00; at the 12.00 isolate floor"),
        ev(1260000.0, "k1.tau", 28.00, code="TAU_US", units="us", note="adjacent brick K-1 stays healthy; out of scope for this ACCEPT"),
        ev(1440000.0, "k2.tau", 26.00, code="TAU_US", units="us", note="K-2 out of scope"),
        ev(1620000.0, "k3.tau", 30.00, code="TAU_US", units="us", note="K-3 out of scope"),
        ev(1800000.0, "pcd.t1e", 20.00, code="T1E_US", units="us"),
        ev(1980000.0, "recon.tau", 10.00, code="TAU_US", units="us", note="0.50*20.00=10.00; under isolate, over dump 2.00"),
        ev(2160000.0, "recon.Deff", 6.40, code="DEFF", units="mm2_us", note="64.00/10.00=6.40"),
        ev(2340000.0, "pcdveil.tau", 48.00, code="VENDOR_US", units="us"),
        ev(2520000.0, "pcd.snr", 9.0, code="PCD_SNR", units="1"),
        ev(2700000.0, "recon.ratio", 2.00, code="T1E_RATIO", units="1", note="t_1e/τ identity holds at 2.00 by construction of k_t=0.50"),
        ev(3000000.0, "pcd.t1e", 16.00, code="T1E_US", units="us", note="isolate-floor frame; raster sidecar"),
        ev(3000001.5, "pcd.snr", 11.0, code="PCD_SNR", units="1", note="1.5 ms PCD lock after t_1e; 11.0 >= 8.0"),
        ev(3180000.0, "recon.tau", 8.00, code="TAU_US", units="us", note="0.50*16.00=8.00 exact; isolate 12.00, furnace-dump 2.00"),
        ev(3360000.0, "recon.Deff", 8.00, code="DEFF", units="mm2_us", note="64.00/8.00=8.00 exact diffusivity identity"),
        ev(3540000.0, "recon.ratio", 2.00, code="T1E_RATIO", units="1", note="16.00/8.00=2.00 exact"),
        ev(3720000.0, "pcdveil.tau", 47.50, code="VENDOR_US", units="us"),
        ev(3900000.0, "k1.tau", 28.00, code="TAU_US", units="us"),
        ev(4080000.0, "k2.tau", 26.00, code="TAU_US", units="us"),
        ev(4260000.0, "k3.tau", 30.00, code="TAU_US", units="us"),
        ev(4440000.0, "brick.T", 301.0, code="BRICK_K", units="K"),
        ev(4620000.0, "ops.prop", 1.0, code="ISOLATE_K4", units="bool", note="sim operator Cora Flint: isolate K-4 only; K-1..K-3 stay in the pull"),
        ev(4800000.0, "gate.acc", 1.0, code="ACCEPT", units="decision", note="bounded ACCEPT of K-4 isolate; furnace dump refused; Pcdveil not SoT"),
        ev(4980000.0, "k4.lock", 1.0, code="K4_ISOL", units="bool"),
        ev(6000000.0, "surv.start", 1.0, code="SURV_START", units="bool", note="bookend 1 of the 12.0 min survey floor"),
        ev(6720000.0, "surv.floor", 1.0, code="SURV_FLOOR", units="bool", note="6000 s + 720 s = 6720 s = 12.0 min"),
        ev(7200000.0, "ops.skip", 1.0, code="SKIP_SURVEY", units="bool", note="Flint: skip the remaining-brick survey; Pcdveil still 47.50 us"),
        ev(7800000.0, "gate.surv", 1.0, code="REJECT", units="decision", note="companion t2: REJECT skip-survey; K-1..K-3 stay in the survey takt"),
        ev(8400000.0, "surv.held", 1.0, code="SURV_HELD", units="bool"),
        ev(9000000.0, "pcd.t1e", 12.00, code="T1E_US", units="us"),
        ev(9600000.0, "recon.tau", 6.00, code="TAU_US", units="us", note="0.50*12.00=6.00 post-isolate on K-4; still over dump 2.00"),
        ev(10200000.0, "pcdveil.tau", 47.00, code="VENDOR_US", units="us"),
        ev(10800000.0, "k1.tau", 27.00, code="TAU_US", units="us"),
        ev(11400000.0, "k2.tau", 26.00, code="TAU_US", units="us"),
        ev(12000000.0, "k3.tau", 29.00, code="TAU_US", units="us"),
        ev(12600000.0, "furnace.dump", 0.0, code="DUMP_NOT_TAKEN", units="bool"),
        ev(13200000.0, "surv.held", 1.0, code="SURV_HELD", units="bool"),
        ev(13800000.0, "recon.Deff", 10.67, code="DEFF", units="mm2_us", note="64.00/6.00=10.666... authored 10.67"),
        ev(14400000.0, "brick.T", 302.0, code="BRICK_K", units="K"),
        ev(15000000.0, "k4.lock", 1.0, code="K4_ISOL", units="bool"),
        ev(15600000.0, "ops.skip", 1.0, code="SKIP_SURVEY", units="bool"),
        ev(16200000.0, "gate.surv", 1.0, code="REJECT", units="decision"),
        ev(16800000.0, "surv.floor", 1.0, code="SURV_FLOOR", units="bool"),
    ]
    assert_stream(events)
    if len(events) != 48:
        raise RuntimeError(len(events))

    traj = {
        "id": "nelb-r02-003-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "QH-PCD-2026-0902",
            "domain": "microwave_pcd_cz_si_brick",
            "setting": "Quartzholt PV QH-2 (invented), simulated coupon PCD-SIM-6, brick K-4. Plant-owned microwave photoconductance-decay is the remaining-lifetime SoT. Pcdveil vendor PCD-cloud is not SoT. Simulated campaign; not a live plant. Not r39 phosphor-lifetime, not r26 SPR, not r23 lock-in thermography, not leftover-mill alanine EPR, not r26 microwave-cavity moisture.",
            "observables_at_decision": {
                "t_1e_us": t_1e,
                "k_t": k_t,
                "tau_us": tau,
                "D_eff": d_eff,
                "t1e_ratio": ratio,
                "pcd_snr": 11.0,
                "pcdveil_us": 48.00,
                "k1_tau_us": 28.00,
                "k2_tau_us": 26.00,
                "k3_tau_us": 30.00,
                "isolate_floor_us": 12.00,
            },
            "margin_authority": "QH-2 brick SOP rev D: if reconstructed tau_us <= 12.00 AND PCD SNR >= 8.0, K-4 isolate is required even if Pcdveil reports 48.00 us. Furnace dump is a different gate (tau_us <= 2.00). K-1..K-3 are out of scope unless their own reconstructions cross 12.00.",
        },
        "proposed_action": {
            "actor": "sim operator Cora Flint, citing plant PCD 8.00 us on K-4 and healthy K-1..K-3",
            "summary": "isolate brick K-4 only; keep K-1..K-3 in the pull; do not dump the Cz furnace",
            "basis_claimed": "only K-4 reconstructed under 12.00 us; Pcdveil 48.00 us is not SoT but also does not license a furnace dump",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Bounded ACCEPT of K-4 isolate. Serialized reconstruction: tau_us = k_t * t_1e = 0.50 * 16.00 = 8.00, which is 4.00 us under the 12.00 isolate floor and 6.00 us over the 2.00 furnace-dump tripwire, and PCD SNR is 11.0 >= 8.0. Diffusivity identity D_eff = L^2 / tau = 64.00 / 8.00 = 8.00; t_1e/tau identity = 16.00 / 8.00 = 2.00. K-1/K-2/K-3 reconstruct 28.00/26.00/30.00 us, all over 12.00, so they stay out of scope. Pcdveil 48.00 us is a last-good denial, not a dump license and not a clear. Ordered: isolate K-4 only. Scope: this ACCEPT does not dump the furnace, does not isolate K-1..K-3, and does not skip the 12 min remaining-brick survey (that is the companion question).",
            "threshold": "tau_us<=12.00 AND pcd_snr>=8.0 => isolate that brick only; Pcdveil is not SoT; dump if tau_us<=2.00; K-1..K-3 out of scope while tau_us>12.00",
            "stated_residuals": "12 min survey still required; 8.00 vs a true 2.00 dump is a production cut; Pcdveil remains the only OEM PCD channel",
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 4800: K-4 isolated; K-1..K-3 left in the pull; Pcdveil not SoT",
            "tool": "qh2-pcd-brick-gate-cli",
            "observation": "tau 8.00 us recomputes from t_1e 16.00 us; K-4 hashed; adjacent bricks remain over 12.00 us",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "PCD t_1e 16.00 us; raster frame; tau 8.00 us"},
                {"t_s": 4620.0, "event": "ops proposes K-4 isolate"},
                {"t_s": 4800.0, "event": "ACCEPT K-4 isolate; furnace dump refused"},
                {"t_s": 6000.0, "event": "12 min survey bookend 1"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7800.0, "event": "companion REJECT skip-survey"},
            ],
            "observed_effects": [
                "remaining lifetime recomputes from the serialized PCD model at every recon.tau event",
                "a Pcdveil-only head would have left K-4 in the pull overnight",
                "12 min survey floor is in the stream (surv.start, surv.floor)",
            ],
            "surprises": [
                "a clean vendor 48.00 us corridor co-existed with an 8.00 us plant reconstruction on one brick only",
            ],
            "new_state": {
                "k4": "isolated",
                "k1_k3": "in pull",
                "pcdveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.41,
            [
                ("pcd_tau_reconstruction", 0.14),
                ("bounded_k4_scope", 0.12),
                ("pcdveil_nonsubstitution", 0.08),
                ("no_furnace_dump", 0.08),
                ("survey_time_cost", -0.01),
            ],
            "scored for a bounded ACCEPT of K-4 isolate on a recomputable microwave-PCD lifetime slip while refusing a Pcdveil last-good and a furnace dump; 12 min survey is priced as takt not as a reason to skip",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "microwave-pcd-tau", "serialized-reconstruction", "operational-companion", "bounded-scope"],
            distillation_value="Independent LIF raster plus serialized k_t*t_1e remaining-lifetime reconstruction; race is the 1.5 ms t_1e/SNR pair; refractory and adaptation are in the CUBA excerpt.",
            distillation_note="PCD-tau gate: serialized k_t*t_1e plus SNR lock beats a vendor last-good; companion t2 is the survey hold, not a dump vote",
        ),
    }
    traj2 = {
        "id": "nelb-r02-003-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "QH-PCD-2026-0902-exec",
            "domain": "remaining_brick_survey_execution",
            "setting": "Same PCD-SIM-6 after the ACCEPT. Operator proposes skip-survey because Pcdveil still shows 47 us. This companion is the operational survey hold, not a second lifetime vote.",
            "observables_at_decision": {
                "tau_us": 6.00,
                "surv_floor_s": 720.0,
                "skip_survey_proposed": True,
                "k1_tau_us": 27.00,
            },
            "margin_authority": "QH-2 execution SOP: remaining-brick survey after a K-4 isolate; skip-survey is forbidden while K-1..K-3 have not been re-measured on the plant PCD.",
        },
        "proposed_action": {
            "actor": "sim operator Cora Flint",
            "summary": "skip the remaining-brick survey; Pcdveil still 47 us and K-4 is already isolated",
            "basis_claimed": "the ACCEPT already stopped K-4, so a survey is wasted takt",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Skip-survey is refused. The 12 min survey floor is complete and K-1..K-3 have not been re-measured on the plant PCD head. Pcdveil 47 us is not a survey substitute. REJECT skip-survey. Do not dump the furnace. Do not restore K-4 on Pcdveil. 6.00 us post-isolate on K-4 is still the plant SoT until a new frame clears 12.00.",
            "threshold": "survey_hold AND surv_floor_complete AND skip_survey_not_taken AND k1k3_remeasure_required",
            "stated_residuals": "K-4 stays isolated; Pcdveil still the only OEM PCD channel",
        },
        "executed_action": {
            "summary": "survey held at t_s 7800; skip-survey not taken; furnace dump not latched",
            "tool": "qh2-surv-exec",
            "observation": "recon.tau 6.00 us after isolate; K-1..K-3 still in the survey takt; Pcdveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "survey clock started after ACCEPT"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7200.0, "event": "skip-survey proposed"},
                {"t_s": 7800.0, "event": "REJECT skip-survey"},
            ],
            "observed_effects": [
                "Pcdveil restore did not reopen the lifetime call",
                "furnace dump never fired; K-1..K-3 stayed in the survey",
            ],
            "surprises": ["post-isolate K-4 climbed to 6.00 us while Pcdveil still read 47 us"],
            "new_state": {"survey": "held", "furnace": "in service", "k4": "isolated"},
            "latency_ms": 720000.0,
        },
        "reward_components": reward(
            0.36,
            [
                ("survey_hold", 0.12),
                ("no_furnace_dump", 0.10),
                ("pcdveil_nonsubstitution", 0.08),
                ("surv_floor_complete", 0.08),
                ("held_takt_cost", -0.02),
            ],
            "operational execution gate: survey-hold because Pcdveil is not a skip license; not a lifetime re-vote",
        ),
        "meta": meta_common(tags=["REJECT", "operational-execution", "survey-hold"]),
    }
    return {
        "id": "nelb-r02-003",
        "snn_tags": list(SNN_TAGS),
        "spike_events": events,
        "language_view": {
            "description": "Quartzholt PV QH-2 simulated coupon. Plant-owned microwave PCD reconstructs 8.00 us remaining lifetime from 0.50*16.00 while Pcdveil still reports 48.00 us. The gate ACCEPTs a bounded K-4 isolate (K-1..K-3 out of scope). A 12 min survey floor is serialized. Companion t2 REJECTs skip-survey.",
            "trajectory": traj,
            "trajectory_survey_hold": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "pcd.t1e / pcd.snr": "PCD 1/e time and SNR; the physics channels the reconstruction consumes",
                "recon.tau / recon.Deff / recon.ratio": "serialized remaining lifetime, diffusivity identity, and t_1e/tau identity",
                "k1.tau / k2.tau / k3.tau / pcdveil.tau / brick.T": "adjacent-brick out-of-scope witnesses, vendor PCD cloud, brick temperature",
                "ops.prop / gate.acc / ops.skip / gate.surv": "K-4 isolate proposal, ACCEPT, skip-survey proposal, companion REJECT",
                "k4.lock / surv.start / surv.floor / surv.held / furnace.dump": "operational companion channels plus the 12 min floor",
            },
            "temporal_motifs": [
                "vendor-healthy while plant-under: pcdveil.tau 48.00 next to recon.tau 8.00",
                "reconstruction as event: recon.tau 8.00 equals 0.50*16.00",
                "ACCEPT then operational REJECT: gate.acc at 4800 s, gate.surv at 7800 s",
                "slow floor in-stream: surv.start 6000 s, surv.floor 6720 s (12.0 min)",
                "tight PCD pair: pcd.t1e then pcd.snr +1.5 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Pcdveil is 48 us' = pcdveil.tau 48.00; '8 us remaining lifetime' = recon.tau 8.00; 'isolate K-4 only' = gate.acc ACCEPT; 'do not skip survey' = gate.surv REJECT",
            "why_high_value": "New microwave photoconductance-decay remaining-lifetime family on a Cz-Si brick (not phosphor-lifetime, not SPR, not lock-in thermography, not alanine EPR). Lead bounded ACCEPT of K-4 isolate on a recomputable lifetime slip that a vendor PCD last-good would have left in the pull. Independent CUBA LIF raster. Companion t2 is operational survey-hold. sim_or_real=simulated.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 2026090203, "stream_note": "stream amplitudes are authored constants; raster is independent CUBA LIF"},
                "draw_order": "independent CUBA LIF per neuron; gap-constrained times; per-spike adaptation and noise",
                "thinning": "PCD exists at ~10 Hz; stream keeps 5 t_1e points; recon keeps 5 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "pcd.t1e": 1.5,
                    "pcd.snr": 1.5,
                    "recon.tau": 60000,
                    "recon.Deff": 60000,
                    "recon.ratio": 60000,
                    "k1.tau": 60000,
                    "k2.tau": 60000,
                    "k3.tau": 60000,
                    "pcdveil.tau": 60000,
                    "brick.T": 60000,
                    "ops.prop": 60000,
                    "gate.acc": 60000,
                    "k4.lock": 60000,
                    "surv.start": 60000,
                    "surv.floor": 60000,
                    "ops.skip": 60000,
                    "gate.surv": 60000,
                    "surv.held": 60000,
                    "furnace.dump": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-09-02T03:00:00Z simulated coupon start",
            },
            "distillation_targets": [
                "microwave-PCD reconstruction head: tau = k_t * t_1e; D_eff = L^2 / tau; t_1e/tau identity",
                "bounded ACCEPT of K-4 vs furnace dump vs skip-survey",
                "vendor-PCD nonsubstitution plus adjacent-brick out-of-scope",
                "operational companion: survey-hold without restoring on Pcdveil",
                "independent CUBA LIF raster with race/refractory/adaptation tags",
            ],
        },
        "reconstruction_model": {
            "name": "microwave_pcd_cz_si_tau",
            "formula": "tau_us = k_t * t_1e_us; D_eff = L2 / tau_us; t1e_ratio = t_1e_us / tau_us",
            "parameters": {
                "k_t": 0.50,
                "L2": 64.00,
                "isolate_floor_us": 12.00,
                "dump_us": 2.00,
                "snr_lock": 8.0,
                "surv_min": 12.0,
            },
            "worked_example": {"t_1e_us": 16.00, "tau_us": 8.00, "D_eff": 8.00, "t1e_ratio": 2.00},
            "check": "0.50 * 16.00 = 8.00 exactly; 64.00 / 8.00 = 8.00 exactly; 16.00 / 8.00 = 2.00 exactly; 6000 s + 720 s = 6720 s = 12.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 36.0,
            "decision_window_s": 0.036,
            "code": "qh2.pcd_brick_gate",
            "note": "ACCEPT accumulator wins: plant PCD lifetime evidence isolates K-4 without a furnace dump",
            "decode_rule": "accept-K4-isolate if tau_estimator AND pcd_lock fire; vendor_dump_advocate is below threshold by design",
            "populations": [
                gate_pop("tau_estimator", 80, 1.4, 50.0, w_s),
                gate_pop("pcd_lock", 50, 1.1, 50.0, w_s),
                gate_pop("vendor_dump_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("accept_latch", 64, 1.5, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "qh2.pcd_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 36.0},
                {"check": "qh2.surv_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 40.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r02-003",
            clock_domain="qh2-pcd-sim-relative-ms-t0-2026-09-02T03:00:00Z",
            tags=["microwave-pcd-tau", "ACCEPT", "REJECT", "serialized-reconstruction", "operational-t2", "independent-lif", "bounded-scope"],
            distillation_value="Independent LIF raster teaches race/refractory/adaptation while the language view teaches microwave-PCD remaining-lifetime reconstruction-as-SoT with a bounded ACCEPT.",
        ),
    }


def walk_banned(obj, path=""):
    hits = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{path}.{k}" if path else k
            nk = str(k).casefold().replace("-", "_").replace(" ", "_")
            if nk in HIDDEN or nk in {"thought", "scratch", "inner_monologue", "chain_of_thought", "real"}:
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
        blob = json.dumps(rec)
        if '"real"' in blob or "thought" in rec:
            raise RuntimeError("real/thought leaked")
        if rec["meta"]["round"] != 2:
            raise RuntimeError("meta.round")
        if rec["meta"].get("snn_tags") != SNN_TAGS:
            raise RuntimeError("snn_tags")
        if rec.get("snn_tags") != SNN_TAGS:
            raise RuntimeError("top snn_tags")
        ids.append(rec["id"])
        lv = rec["language_view"]
        ids.append(lv["trajectory"]["id"])
        for k, v in lv.items():
            if k.startswith("trajectory") and isinstance(v, dict) and "id" in v:
                if v is not lv["trajectory"]:
                    ids.append(v["id"])
                sim = v["state"]["sim_or_real"]
                if sim not in {"designed", "simulated", "hil"}:
                    raise RuntimeError(sim)
                if v["meta"]["round"] != 2:
                    raise RuntimeError("traj round")
        n = len(rec["spike_events"])
        if n < 48:
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
        if not (20 <= rast["window_ms"] <= 50):
            raise RuntimeError("window")
        if rast["excerpt_span_us"] < 1000:
            raise RuntimeError("excerpt span")
        if rast["isi_source"] != "full_window_per_neuron_isi":
            raise RuntimeError("isi source")
        tf = rast["routing"]["third_factor"]
        if abs(tf["tau_e_ms"] / 1000.0 - tf["tau_e_s"]) > 1e-9:
            raise RuntimeError("tau_e")
        if rast["lif"]["model"] != "independent_cuba_lif":
            raise RuntimeError("lif")
        ex = {e["t_us"] for e in rast["excerpt"]}
        raw_ms = {int(round(e["t_rel_ms"])) for e in rec["spike_events"]}
        if ex & raw_ms:
            raise RuntimeError("excerpt echoes stream")
        if "training_ready" in blob:
            raise RuntimeError("training_ready claimed")
        if "2026-08-17" in blob or "2026-08-30" in blob:
            raise RuntimeError("forbidden run date")
    if len(ids) != len(set(ids)):
        raise RuntimeError(f"dup ids {ids}")
    print("local_checks ok", [r["id"] for r in records], "ids", len(ids))


NOTES = """# Neuromorphic Event + Language Bridge — NOTES round 2
Run: 2026-09-02-final-heavy · Factory: neuromorphic-event-language-bridge · Generator: grok-4.6 · Output: `batch-r02.jsonl` (3 paired artifacts, 6 ThalamicTrajectories)
Rights: RM-793 research-only (SpaceXAI/xAI grok-4.6, SuperGrok Heavy chat). Not training_ready. Written create-only to `/home/raulmc/rmems/synthetic-factory/outputs/raw/2026-09-02-final-heavy/neuromorphic-event-language-bridge/` (`batch-r02.jsonl` was absent). Does not clobber 2026-08-17 or 2026-08-30 trees. IDs `nelb-r02-001`…`003` (not 2026-08-17 `nelb-r2-a*` and not 2026-08-30 `nelb-20260830-r02-a*`).

## Context / de-duplication
Live tree already held r21 (OA-ICOS CH4 / SERF OPM / WGM water), r41 (LDA / coulometric KF / bender-element Vs), r61 (Stern-Volmer DO / pellistor LEL / FMCW tank-radar). This round is **r02** as assigned. Banned this round: those nine families; 2026-08-17 r02 auditory gammatone / methane-plume crawler MOX-pellistor / DDoS telemetry; 2026-08-30 r02 geodetic total-station / RF spectrum / chemosensory e-nose; leftover-mill r13–r68 families named in those NOTES (FBG, BOTDA, QCM-D, SAW, CRDS, IFOG, transmon, hyperspectral, MEMS, muon, x-ray, optogenetic, 905 nm LiDAR, clamp-on, LIBS, QEPAS, LFV, Kaplan LDV, THz-TDS, ECT, TDLAS NH3, lock-in thermography, PAUT, EN CUI, RUS, N-16, helium RGA, FOCT, tip-timing, acoustic pyrometry, SPR, VW viscometer, MW cavity, MFL, NMR T2, nucleonic, JNT, CRNS, Coriolis, CARS, XRF, Mössbauer, GB-InSAR, ellipsometry, CTA, SPND, LII, PALS, NQR, SFRA, shearography, H-permeation, FMCW lining, GPR, mud-pulse, Barkhausen, Lamb, Pockels, PEC, confocal, OCT, DCPD, impact-echo, phosphor-lifetime, vortex-shedding, GWR, neutron-backscatter, beta-gauge, Raman, cyclotron BPM, alanine EPR, ADCP, TOFD, laser-flash, TDR, UV-DOAS, Al2O3, load-cell, electrochemical H2S, TEV PD, dielectric water-cut, Nernst zirconia, PID VOC, FID, Wobbe, venturi, katharometer, Clark DO, sonic-nozzle, sodium-ion, vibrating-tube, Ubbelohde, 60-degree gloss, RF-admittance, UV photometric ozone, triboelectric dust, molybdenum-blue phosphate). Plants not reused: Sedgewhin, Brinecrag, Lichenholt, Rushcrag, Copsewick, Peatspire, Mirewhin, Lacquerfen, Pitchshaw, Tealshaw, Gorsewhin/Brindlemere/Quartzholt are new.

Adjacencies declared in-pair then kept physically distinct:
- **001 CAPS remaining NO2** is cavity-attenuated *phase-shift* remaining nitrogen dioxide of a road-tunnel duct, not UV-DOAS SO2 (r59), not CLD NOx (r52), not NDIR CO (r62), not TDLAS NH3 (r22), not OA-ICOS CH4 (live r21), not paramagnetic O2 (r46), not electrochemical H2S (r60).
- **002 PTR-MS remaining MDI** is proton-transfer-reaction ion-count remaining methylene diphenyl diisocyanate of a PU foam HIL dummy, not PID VOC (r57), not FID THC, not QEPAS (r19), not pellistor LEL (live r61 / leftover r02 crawler), not SPR cyanide (r26), not UV-fluorescence OIW (r56).
- **003 microwave PCD remaining τ_eff** is photoconductance-decay remaining minority-carrier lifetime of a Cz-Si brick, not phosphor-lifetime (r39), not SPR (r26), not lock-in thermography (r23), not alanine EPR (leftover r41), not microwave-cavity moisture (r26).

## Round 2 batch summary (3 pairs, 6 trajectories)

| id | modality (NEW family) | domain | decisions | headline |
|----|----------------------|--------|-----------|----------|
| nelb-r02-001 | cavity-attenuated phase-shift remaining NO2 of a road-tunnel duct (k_c·Δφ ppm, Capsveil last-good denial, 18 min damper-hold floor) | Gorsewhin Tunnel GW-4 duct D-6 (invented): 0.50*40.00 reconstructs 20.00 ppm while Capsveil still reads 2.40 ppm | REJECT (+0.43) / MODIFY (+0.34) | serialized `0.50*40.00=20.00`; `48.00-8.00=40.00`; `20.00*1.20=24.00`; conjunctive SOP (C AND SNR) forbids continue-idle; three-party collusion includes the CAPS-cloud infra owner; companion t2 damper-hold, tube ESD refused; sim_or_real=designed |
| nelb-r02-002 | PTR-MS remaining MDI of a PU foam booth (k_p·I ppb, Ptrveil last-good denial, 24 min new-source floor) | Brindlemere Foam BM-7 dummy booth B-4 (invented, HIL in PTR-HIL-3): 4.00*8.00 reconstructs 32.00 ppb while Ptrveil still reads 3.20 ppb | MODIFY (+0.40) / ACCEPT (+0.35) | serialized `4.00*8.00=32.00` and `8.00/2.00=4.00`; keep-booth refused; PTR tech Iona Beck exonerated (missing reagent-zero AE, UTC vs UTC+2); companion t2 new-source restart; sim_or_real=hil |
| nelb-r02-003 | microwave photoconductance-decay remaining τ_eff of a Cz-Si brick (k_t·t_1e µs, Pcdveil last-good denial, 12 min survey floor) | Quartzholt PV QH-2 brick K-4 (invented, simulated PCD-SIM-6): 0.50*16.00 reconstructs 8.00 µs while Pcdveil still reads 48.00 µs | ACCEPT (+0.41) / REJECT (+0.36) | serialized `0.50*16.00=8.00`; `64.00/8.00=8.00`; `16.00/8.00=2.00`; bounded ACCEPT of K-4 only; K-1..K-3 out of scope; companion t2 REJECTS skip-survey; sim_or_real=simulated |

Decision spread: REJECT / MODIFY / MODIFY / ACCEPT / ACCEPT / REJECT — **2A/2M/2R**. All three enums used, and all three sit on **leads**. Provenance spread: designed / hil / simulated (one each; never real). IDs `nelb-r02-001`…`003` plus t1/t2 suffixes. `meta.round=2`. `meta.snn_tags` = [race, refractory, adaptation] on every record.

## Raster sidecar
Every record carries `raster` + top-level `gate_snn` + `gate_compute` + `snn_tags`. Windows 40/32/36 ms; `window_s == window_ms/1000` exactly; `spikes == round(neurons·rate·window_s)` with zero slack (40/40/36 at 50.0/50.0/62.5 Hz over 20/25/16 neurons); `energy_pJ = spikes·23` and `energy_uJ = spikes·23e-6` exact (920/920/828 pJ). Routing source/target + 3-entry tables + `third_factor` on all three (modulators da.caps_no2_conflict / ach.ptr_reagent_skip_salience / na.pcd_brick_scope_eligibility; τe 1.6/1.2/2.0 s as consistent `tau_e_s`+`tau_e_ms` pairs). **Independent CUBA LIF** excerpts (not a re-encode of `spike_events`; Jaccard overlap 0); integer `t_us`, in-window, `neuron_id`-bounded, sorted, full-window by construction, per-spike amplitude with adaptation (0.82**k) plus noise; excerpt span ≥ 1000 µs. ISI histograms from the **full window**, bins ≥1 ms, counts sum to `spikes − distinct_active_neurons`. Same-neuron gaps ≥1000 µs. `gate_snn` on all three: decisions REJECT/MODIFY/ACCEPT matching each lead trajectory; every rate-declaring population's budget exact against its decision window. `gate_compute.per_check` windows 32–40 ms, budgets exact. Main streams: **48/48/48 events** (48+ live-tree floor), strictly increasing `t_rel_ms` only (no `t_ms` mix), same-channel refractory ≥0.8 ms (001 CAPS pair at 1.4 ms, 002 PTR pair at 1.2 ms, 003 PCD pair at 1.5 ms).

## Self-critique

### Edge cases added vs still thin
- **Added:** first CAPS remaining-NO2 family on a road-tunnel duct with recomputable C=k_c·Δφ (`20.00 ppm`) plus phase and load identities; first PTR-MS remaining-MDI family on a PU foam HIL dummy with recomputable C=k_p·I (`32.00 ppb`) plus ion-ratio and mdot identities and a resolved-innocent PTR tech; first microwave photoconductance-decay remaining-lifetime family on a Cz-Si brick with recomputable τ=k_t·t_1e (`8.00 µs`), D_eff=L²/τ, and t_1e/τ identity, plus a bounded ACCEPT whose out-of-scope clause is adjacent bricks; independent CUBA LIF rasters (live r21/r41/r61 used gap-constrained draws); `snn_tags` on every record; 48-event streams; operational t2 on all three; provenance trio designed/hil/simulated; 18/24/12 min slow floors in-stream.
- **Still thin:** (i) 001's k_c is a lumped phase-to-ppm gain, not a pressure / humidity table — a 8 kPa hop that fakes 20.00 ppm inside a 2.40 Capsveil corridor is unwritten; (ii) 002's k_p is a lumped ion-count gain, not a reagent-depletion / humidity map, so a water-cluster hop that fakes 32.00 ppb is unwritten; (iii) 003's k_t is a lumped 1/e scale, not a temperature / surface-recombination map, so a 10 K hop that fakes 8.00 µs is unwritten; (iv) vendor-only as a *lead* REJECT on a plant with *no* independent CAPS/PTR/PCD remains slightly harder — 001/002 still have plant heads; (v) stream amplitudes remain authored constants (raster draws are the only seeded LIF noise).

### Realism of noise / temporal fidelity
- Strong: 001's 20.00 ppm, Δφ 40.00, load 24.00, and 18.0 min damper (`6000+1080=7080 s`) recompute from the record; 002's 32.00 ppb, ratio 4.00, and 24.0 min new-source (`2820+1440=4260 s`) recompute; 003's 8.00 µs, D_eff 8.00, and 12.0 min survey (`6000+720=6720 s`) recompute. Independent CUBA LIF (τm 10/12/8 ms) plus adaptation (0.82**k plus 4% noise) and the 1.2–1.5 ms physics pairs give the 48-event stream a raster-scale motif without violating 0.8 ms same-channel refractory.
- **Gaps, honestly:** (i) 48 events still thins 1 Hz CAPS / 1 Hz PTR / 10 Hz PCD stacks; (ii) 001's post-stop 24.00 ppm is a later sample, not a closed-loop damper controller; (iii) 002 HIL dummy times an in-service isolate that the stream does not independently witness on a second live booth until the new source starts; (iv) no gate_snn input→output volley pair at raster resolution this round.

### Training value (SNN/LSM + agentic)
Distillation targets: CAPS C=k_c·Δφ plus phase and load identities; conjunctive isolate floor vs continue-idle vs tube ESD; Capsveil-infra collusion; PTR C=k_p·I plus ratio/mdot identities; isolate-floor booth vs keep-whole vs hall dump; timezone exoneration; PCD τ=k_t·t_1e and D_eff identities; bounded ACCEPT with K-1..K-3-out-of-scope; skip-survey refusal under survey takt. Independent LIF rasters teach race/refractory/adaptation without echoing the language-view stream. Agentic value concentrates in three patterns: reconstruction-as-SoT on a physical NO2/MDI/lifetime load the raw corridor cannot see, earned ACCEPT with an explicit physical out-of-scope object (bricks K-1..K-3), and stop-then-hold so a REJECT does not become a tube/hall/furnace kill.

## What round 3 should add (next densification target)
1. **Pressure / humidity CAPS table** on a non-GW-4 duct so an 8 kPa hop fakes 20.00 ppm inside a 2.40 Capsveil corridor, closing 001's lumped-k_c gap.
2. **Reagent-depletion / water-cluster map** on a non-BM-7 PTR so a cluster hop fakes 32.00 ppb while mean I looks healthy.
3. **Temperature / surface-recombination map** on a non-QH-2 brick so a 10 K hop fakes 8.00 µs inside a 48 µs Pcdveil corridor.
4. **Do not restage** live r21 OA-ICOS / SERF / WGM, live r41 LDA / KF / bender-element, live r61 Stern-Volmer / pellistor / FMCW radar, 2026-08-17 r02 auditory/crawler/DDoS, 2026-08-30 r02 geodetic/RF/e-nose, or leftover-mill r13–r68 families listed above. Do not reuse ids `nelb-r02-001`…`003` or leftover-mill `040`…`207`.

## Verification
`batch-r02.jsonl`: 3 lines, `json.loads`-clean (allow_nan=False). Written create-only to the live factory dir (O_EXCL). Build-time asserts: global time order; same-channel ≥0.8 ms; 48+ events (48/48/48); excerpt integer bounds, neuron bounds, sort, 1 ms per-neuron floor, span ≥1000 µs; ISI identity from the full window; spike budgets exact; energy pJ/µJ exact; reward totals equal two-decimal component sums (+0.43/+0.34/+0.40/+0.35/+0.41/+0.36); gate_snn decisions match lead `safety_decision.decision`; `state.sim_or_real` ∈ {designed, hil, simulated}; `meta.round=2`, `meta.factory=neuromorphic-event-language-bridge`, `meta.generator=grok-4.6`, `meta.run_label=2026-09-02-final-heavy`; `meta.snn_tags` = [race, refractory, adaptation]; `meta.rights` 15-key RM-793 stamp (`intended_use=research_only`, `linear_issue=RM-793`, `generated_at=2026-09-02T20:40:00Z`); independent CUBA LIF (seeds 2026090201/2026090202/2026090203); no hidden-reasoning keys; no `provenance` objects; no live-plant claims; no `training_ready`; no 2026-08-17/2026-08-30 bytes; all 9 record/trajectory ids unique vs live r21/r41/r61.

Honest novelty accounting: 3/3 modality families are new versus the live 2026-09-02-final-heavy tree (r21/r41/r61), versus 2026-08-17 r02, versus 2026-08-30 r02, and versus leftover-mill r13–r68. Independent CUBA LIF rasters and required `snn_tags` are new density/encoder objects relative to live r21/r41/r61 gap-constrained draws. Against that: conjunctive SOP, operational t2, serialized reconstruction, bounded-accept-with-scope-limit, vendor-nonsubstitution, exoneration, and 2A/2M/2R are carried vocabulary. Net: a bit under half of the round's scenario/edge mass is genuinely novel.

Novel coverage: 46%
"""


def write_create_only(path: Path, text: str) -> Path:
    path = Path(path)
    if path.exists():
        stem, suffix = path.stem, path.suffix
        dest = path.with_name(stem + "c" + suffix)
        n = 2
        while dest.exists():
            dest = path.with_name(f"{stem}c{n}{suffix}")
            n += 1
        path = dest
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(text)
    return path


def main():
    records = [rec_001(), rec_002(), rec_003()]
    local_checks(records)
    STAGING.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(r, ensure_ascii=False, allow_nan=False, separators=(",", ":")) for r in records]
    batch_text = "\n".join(lines) + "\n"
    staging_batch = write_create_only(STAGING / BATCH_NAME, batch_text)
    staging_notes = write_create_only(STAGING / NOTES_NAME, NOTES)
    print("staged", staging_batch, staging_batch.stat().st_size)
    print("staged", staging_notes, staging_notes.stat().st_size)

    LIVE_DIR.mkdir(parents=True, exist_ok=True)
    live_batch = write_create_only(LIVE_DIR / BATCH_NAME, batch_text)
    live_notes = write_create_only(LIVE_DIR / NOTES_NAME, NOTES)
    print("LIVE", live_batch, live_batch.stat().st_size)
    print("LIVE", live_notes, live_notes.stat().st_size)
    for i, r in enumerate(records):
        print(
            r["id"],
            "events",
            len(r["spike_events"]),
            "excerpt",
            len(r["raster"]["excerpt"]),
            "spikes",
            r["raster"]["spikes"],
            "span",
            r["raster"]["excerpt_span_us"],
            "isi",
            r["raster"]["isi_count_identity"],
            "sim",
            r["language_view"]["trajectory"]["state"]["sim_or_real"],
            "dec",
            r["language_view"]["trajectory"]["safety_decision"]["decision"],
            "gate",
            r["gate_snn"]["decision"],
            "bytes",
            len(lines[i]),
        )


if __name__ == "__main__":
    main()
