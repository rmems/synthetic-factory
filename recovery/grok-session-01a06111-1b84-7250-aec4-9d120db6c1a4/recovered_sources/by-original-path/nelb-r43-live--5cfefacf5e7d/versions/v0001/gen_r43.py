#!/usr/bin/env python3
"""NELB round 43 — create-only live-tree writer. Independent CUBA LIF rasters.

Assigned window round is 43 (batch-r43.jsonl was absent). Does not steal
leftover-mill /tmp/nelb-r43/ (cyclotron BPM / alanine EPR / ADCP, ids 130–132)
and does not touch ROUND-r64.reserved.json.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import random
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, "/tmp")
from lif_raster import generate_lif_raster  # independent CUBA LIF, not a stream echo

PIPELINES = Path("/home/raulmc/rmems/synthetic-factory/pipelines")
sys.path.insert(0, str(PIPELINES))

LIVE_DIR = Path(
    "/home/raulmc/rmems/synthetic-factory/outputs/raw/2026-09-02-final-heavy/"
    "neuromorphic-event-language-bridge"
)
STAGING = Path("/tmp/nelb-r43-live")
BATCH_NAME = "batch-r43.jsonl"
NOTES_NAME = "NOTES-r43.md"
ROUND = 43
GENERATED_AT = "2026-09-03T00:48:00Z"

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
        "round": ROUND,
        "factory": "neuromorphic-event-language-bridge",
        "generator": "grok-4.6",
        "run_label": "2026-09-02-final-heavy",
        "rights": dict(RIGHTS),
        "snn_tags": list(SNN_TAGS),
        "nelb": {"snn_tags": list(SNN_TAGS)},
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
    last_err = None
    raw = None
    used_seed = seed
    for bump in range(48):
        used_seed = seed + bump * 7919
        try:
            cand = generate_lif_raster(
                neurons,
                mean_rate_hz,
                window_ms,
                used_seed,
                kernelized_event_times=None,
                tau_m=tau_m_ms,
                excerpt_cap=10**9,
                routing=routing,
            )
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            continue
        expected = int(round(neurons * mean_rate_hz * (window_ms / 1000.0)))
        if abs(int(cand["spikes"]) - expected) > 0:
            last_err = RuntimeError(f"budget {cand['spikes']} != {expected}")
            continue
        if len(cand["excerpt"]) != expected:
            last_err = RuntimeError("excerpt cap missed full window")
            continue
        raw = cand
        break
    if raw is None:
        raise RuntimeError(f"CUBA LIF failed seed {seed}: {last_err}")

    window_ms = float(window_ms)
    window_s = window_ms / 1000.0
    spikes = int(raw["spikes"])
    excerpt = []
    rng = random.Random(used_seed + 17)
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
            f"independent CUBA LIF MT19937 seed {used_seed} (base {seed}); "
            f"tau_m {tau_m_ms} ms; not a re-encode of spike_events; "
            "amplitude adaptation 0.82**k plus noise"
        ),
        "encoder": "independent_cuba_lif",
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
        if t <= last:
            raise RuntimeError("non-increasing t_rel_ms")
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
# nelb-r43-a1 — combustion-IR remaining carbon of a BOF heat, designed,
# REJECT / MODIFY
# ---------------------------------------------------------------------------
def rec_a1():
    k_c = 0.50
    a_co2 = 8.00
    m_g = 2.00
    c_wt = k_c * a_co2 / m_g
    r_am = a_co2 / m_g
    _exact(c_wt, 2.00)
    _exact(r_am, 4.00)
    _exact(k_c * 4.00 / m_g, 1.00)
    _exact(k_c * 6.00 / m_g, 1.50)
    _exact(k_c * 10.00 / m_g, 2.50)
    _exact(6000.0 + 1080.0, 7080.0)

    raster = make_lif_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=40.0,
        seed=2026090431,
        source="sf8.leco.A_co2",
        target="slagfen.tap_stop_core",
        table=[
            {"from": "leco_A_co2", "to": "carbon_estimator", "weight": 1.40},
            {"from": "leco_snr", "to": "leco_lock_core", "weight": 1.15},
            {"from": "carbveil_c", "to": "vendor_continue_advocate", "weight": 0.45},
        ],
        third_factor={
            "modulator": "da.leco_carbon_conflict",
            "tau_e_s": 1.6,
            "tau_e_ms": 1600.0,
            "eligibility": (
                "pre-post coincidence on continue-tap synapses; the plant "
                "combustion-IR modulator depresses continue-tap links when CO2 "
                "peak-area stays high inside tau_e of an SNR lock so a Carbveil "
                "last-good cannot hide a 2.00 wt% remaining-carbon heat"
            ),
        },
        channel_prefix="leco.n",
        anchor=(
            "SF-8 combustion-IR 40 ms frame at A_co2 8.00 / m 2.00 / SNR 12.0 "
            "(t_s 3000) reconstructing 2.00 wt% over the 1.60 isolate floor"
        ),
        tau_m_ms=10.0,
    )
    w_s = 0.040
    events = [
        ev(80.0, "leco.A", 4.00, code="A_CO2", units="1", note="plant-owned combustion-IR remaining carbon of Slagfen Steel SF-8 BOF B-2; LECO-style CO2 peak-area family, not NDIR stack CO, not FTIR methanol, not spark-OES, not ICP-OES, not CEMS k-script"),
        ev(300000.0, "leco.snr", 6.0, code="LECO_SNR", units="1", note="early SNR under the 8.0 lock floor"),
        ev(600000.0, "recon.C", 1.00, code="C_WT", units="wt_pct", note="0.50*4.00/2.00=1.00 exact; still under the 1.60 isolate floor"),
        ev(750000.0, "bath.T", 1640.0, code="T_C", units="C", note="plant BOF bath thermocouple on copper DCS; independent witness; unread by Carbveil"),
        ev(900000.0, "leco.m", 2.00, code="M_G", units="g", note="coupon mass; held"),
        ev(1200000.0, "carbveil.C", 0.48, code="VENDOR_WT", units="wt_pct", note="Carbveil vendor LECO-cloud; infra owner; patched CO2 timestamps"),
        ev(1500000.0, "lance.kW", 18.0, code="LANCE_KW", units="kW", note="plant oxygen-lance PLC; independent witness"),
        ev(1800000.0, "leco.A", 6.00, code="A_CO2", units="1"),
        ev(2100000.0, "recon.C", 1.50, code="C_WT", units="wt_pct", note="0.50*6.00/2.00=1.50; isolate-adjacent band"),
        ev(2250000.0, "bath.O", 480.0, code="O_PPM", units="ppm", note="plant EMF oxygen is a witness, not SoT; Nernst-zirconia gas families are out of scope"),
        ev(2400000.0, "permit.slide", 40.00, code="PERM_S", units="s", note="night clerk Sable Quinn slid the tap-permit clock 40.00 s; collusion party"),
        ev(2550000.0, "lance.kW", 19.0, code="LANCE_KW", units="kW"),
        ev(2700000.0, "leco.m", 2.00, code="M_G", units="g"),
        ev(2850000.0, "carbveil.C", 0.46, code="VENDOR_WT", units="wt_pct"),
        ev(3000000.0, "leco.A", 8.00, code="A_CO2", units="1", note="isolate-floor frame; raster sidecar"),
        ev(3000001.4, "leco.m", 2.00, code="M_G", units="g", note="1.4 ms coupon mass after CO2 peak-area"),
        ev(3150000.0, "leco.snr", 12.0, code="LECO_SNR", units="1", note="SNR 12.0 >= 8.0 lock"),
        ev(3300000.0, "recon.C", 2.00, code="C_WT", units="wt_pct", note="0.50*8.00/2.00=2.00 exact; isolate 1.60, furnace-kill 4.00"),
        ev(3450000.0, "recon.R", 4.00, code="R_A_M", units="1", note="8.00/2.00=4.00 exact area-to-mass identity"),
        ev(3600000.0, "bath.T", 1644.0, code="T_C", units="C"),
        ev(3750000.0, "lance.kW", 21.0, code="LANCE_KW", units="kW", note="PLC tracks the plant combustion-IR, not Carbveil 0.48"),
        ev(3900000.0, "leco.drop", 1.0, code="LECO_DROP", units="bool", note="vendor CO2 packets dropped in Carbveil cloud for 40 s"),
        ev(4200000.0, "recon.C", 2.00, code="C_WT", units="wt_pct"),
        ev(4500000.0, "carbveil.C", 0.48, code="VENDOR_WT", units="wt_pct"),
        ev(4800000.0, "ops.prop", 1.0, code="CONTINUE_TAP", units="bool", note="night operator Merrick Holm: Carbveil is clean 0.48 wt%; keep B-2 tapping"),
        ev(5100000.0, "bath.O", 476.0, code="O_PPM", units="ppm"),
        ev(5400000.0, "gate.stop", 1.0, code="REJECT", units="decision", note="refuse continue-tap; 2.00 wt% and SNR 12.0; Carbveil not SoT"),
        ev(5700000.0, "recon.R", 4.00, code="R_A_M", units="1"),
        ev(6000000.0, "hold.start", 1.0, code="TAP_HOLD_START", units="bool", note="bookend 1 of the 18.0 min tap-hold floor"),
        ev(6300000.0, "leco.snr", 12.0, code="LECO_SNR", units="1"),
        ev(6600000.0, "carbveil.C", 0.44, code="VENDOR_WT", units="wt_pct"),
        ev(7080000.0, "hold.floor", 1.0, code="TAP_HOLD_FLOOR", units="bool", note="6000 s + 1080 s = 7080 s = 18.0 min"),
        ev(7500000.0, "bath.T", 1636.0, code="T_C", units="C"),
        ev(7800000.0, "ops.kill", 1.0, code="FURNACE_ESD", units="bool", note="Holm: trip the whole Slagfen BOF hall until day-shift"),
        ev(8100000.0, "lance.kW", 6.0, code="LANCE_KW", units="kW"),
        ev(8400000.0, "gate.hold", 1.0, code="MODIFY", units="decision", note="companion t2: tap-hold on plant combustion-IR as live interlock; furnace ESD refused"),
        ev(8700000.0, "hold.set", 1.0, code="TAP_HELD", units="bool"),
        ev(9000000.0, "leco.A", 10.00, code="A_CO2", units="1"),
        ev(9600000.0, "recon.C", 2.50, code="C_WT", units="wt_pct", note="0.50*10.00/2.00=2.50; still over 1.60 so tap-hold stays"),
        ev(10200000.0, "carbveil.C", 0.42, code="VENDOR_WT", units="wt_pct"),
        ev(10800000.0, "bath.T", 1632.0, code="T_C", units="C"),
        ev(11400000.0, "hold.held", 1.0, code="TAP_HELD", units="bool"),
        ev(12000000.0, "furnace.esd", 0.0, code="ESD_NOT_TAKEN", units="bool"),
        ev(12600000.0, "permit.slide", 40.00, code="PERM_S", units="s"),
        ev(13200000.0, "leco.drop", 1.0, code="LECO_DROP", units="bool"),
        ev(13800000.0, "hold.lock", 1.0, code="TAP_HELD", units="bool"),
        ev(14400000.0, "recon.R", 5.00, code="R_A_M", units="1", note="10.00/2.00=5.00 on the post-stop frame"),
        ev(15000000.0, "lance.kW", 6.0, code="LANCE_KW", units="kW"),
        ev(15600000.0, "collude.clerk", 1.0, code="CLERK", units="bool"),
        ev(16200000.0, "leco.m", 2.00, code="M_G", units="g"),
        ev(16800000.0, "hold.held", 1.0, code="TAP_HELD", units="bool"),
        ev(17400000.0, "carbveil.C", 0.40, code="VENDOR_WT", units="wt_pct"),
    ]
    assert_stream(events)
    if len(events) != 52:
        raise RuntimeError(len(events))

    traj = {
        "id": "nelb-r43-a1-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "SF-LECO-2026-0902",
            "domain": "combustion_ir_bof_carbon",
            "setting": "Slagfen Steel SF-8 (invented), BOF B-2. Plant-owned combustion-IR remaining-carbon (LECO-style CO2 peak-area / coupon mass) is the heat SoT. Carbveil vendor LECO-cloud (infra owner) plus the tap-permit clock are collusion parties, not witnesses. Invented plant; designed campaign. Not leftover-mill NDIR remaining CO, not live r63 FTIR methanol, not spark-OES, not ICP-OES nickel, not CEMS k-script.",
            "observables_at_decision": {
                "A_co2": a_co2,
                "m_g": m_g,
                "k_c": k_c,
                "C_wt": c_wt,
                "R_A_m": r_am,
                "leco_snr": 12.0,
                "carbveil_wt": 0.48,
                "permit_slide_s": 40.00,
                "isolate_floor_wt": 1.60,
            },
            "margin_authority": "SF-8 BOF SOP rev C: if reconstructed C_wt >= 1.60 AND combustion-IR SNR >= 8.0, continue-tap is forbidden even if Carbveil reports 0.48 wt%. Furnace ESD is a different gate. Kill tripwire is 4.00 wt%.",
        },
        "proposed_action": {
            "actor": "night operator Merrick Holm, citing Carbveil 0.48 wt% and a quiet CO2 channel",
            "summary": "keep B-2 tapping; 8.00 CO2 area is a fouled-crucible glitch on a healthy 0.48 wt% last-good",
            "basis_claimed": "Carbveil is the only OEM carbon SoT and a night abort of B-2 is a heat-nomination miss",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Continue-tap is refused. Serialized reconstruction: C_wt = k_c * A_co2 / m = 0.50 * 8.00 / 2.00 = 2.00 wt%, which is 0.40 wt% over the 1.60 isolate floor and 2.00 wt% under the 4.00 furnace-kill tripwire, and combustion-IR SNR is 12.0 >= 8.0. Area-to-mass identity A/m = 8.00 / 2.00 = 4.00. Permit clock was slid 40.00 s and vendor CO2 packets were dropped, so Carbveil is a collusion party (carbon vendor plus operator plus night clerk Sable Quinn). Ordered: refuse continue-tap now. Scope: this REJECT does not ESD the BOF hall (that is the companion question) and does not isolate the bath-oxygen EMF head.",
            "threshold": "C_wt>=1.60 AND leco_snr>=8.0 => refuse continue-tap; Carbveil is not SoT; furnace-kill if C_wt>=4.00",
            "stated_residuals": "tap-hold still required to hold the 2.00 wt%; 2.00 vs a true 4.00 kill is a production cut; Carbveil remains the only OEM carbon channel",
        },
        "executed_action": {
            "summary": "REJECT at t_s 5400: continue-tap refused; Carbveil not SoT; reconstruction locked",
            "tool": "sf8-leco-tap-gate-cli",
            "observation": "C 2.00 wt% recomputes from A_co2 8.00 and m 2.00; plant combustion-IR hashed; Carbveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "LECO A 8.00 m 2.00; raster frame; C 2.00 wt%"},
                {"t_s": 4800.0, "event": "ops proposes continue-tap"},
                {"t_s": 5400.0, "event": "REJECT continue-tap"},
                {"t_s": 6000.0, "event": "18 min tap-hold bookend 1"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 8400.0, "event": "companion MODIFY tap-hold vs furnace ESD"},
            ],
            "observed_effects": [
                "remaining carbon recomputes from the serialized combustion-IR model at every recon.C event",
                "a Carbveil-only head would have continued tapping overnight",
                "18 min tap-hold floor is in the stream (hold.start, hold.floor)",
            ],
            "surprises": [
                "a clean vendor 0.48 wt% corridor and a 40 s permit slide co-existed with a 2.00 wt% plant reconstruction",
            ],
            "new_state": {
                "b2": "continue-tap blocked",
                "carbveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.43,
            [
                ("leco_carbon_reconstruction", 0.14),
                ("conjunctive_isolate_floor", 0.12),
                ("carbveil_nonsubstitution", 0.10),
                ("three_party_collusion", 0.10),
                ("hold_time_cost", -0.03),
            ],
            "scored for a continue-tap REJECT on a recomputable combustion-IR carbon while refusing a Carbveil last-good patch and a permit clock slide; 18 min floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["REJECT", "combustion-ir-carbon", "serialized-reconstruction", "operational-companion"],
            distillation_value="Independent LIF raster plus serialized k_c*A/m remaining-carbon reconstruction beats a vendor last-good; race is the 1.4 ms A/m pair; refractory and adaptation are in the CUBA excerpt.",
            distillation_note="combustion-IR carbon gate: serialized k_c*A/m plus SNR lock beats a vendor last-good patch; companion t2 is the tap-hold, not a referral vote",
        ),
    }
    traj2 = {
        "id": "nelb-r43-a1-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "SF-LECO-2026-0902-exec",
            "domain": "tap_hold_combustion_ir_interlock_execution",
            "setting": "Same SF-8 after the REJECT. Operator proposes BOF-hall ESD. This companion is the operational tap-hold with the plant combustion-IR as the live interlock, not a second carbon vote.",
            "observables_at_decision": {
                "C_wt": 2.50,
                "hold_floor_s": 1080.0,
                "furnace_esd_proposed": True,
                "hold_set": True,
            },
            "margin_authority": "SF-8 execution SOP: tap-hold on the plant combustion-IR interlock; furnace ESD is a different gate.",
        },
        "proposed_action": {
            "actor": "night operator Merrick Holm",
            "summary": "ESD the whole Slagfen BOF hall until day-shift; 18 min already paid and Carbveil still shows 0.42 wt%",
            "basis_claimed": "the REJECT already stopped B-2, so a hall kill is the cheapest hold",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Tap-hold plus plant combustion-IR as the live interlock. The 18 min tap-hold floor is complete and the isolate tripwire (C_wt >= 1.60) is still armed on the plant combustion-IR head. MODIFY the default Carbveil-restore SOP into a plant-LECO-only interlock. Do not ESD the BOF hall. Do not restore tapping on Carbveil. 2.50 wt% post-stop is still the plant SoT until a new frame clears 1.60.",
            "threshold": "tap_hold AND hold_floor_complete AND furnace_esd_not_taken AND continue_not_restored",
            "stated_residuals": "B-2 stays held; Carbveil still the only OEM carbon channel",
        },
        "executed_action": {
            "summary": "tap-hold held at t_s 8400; furnace ESD not latched; Carbveil restore not taken",
            "tool": "sf8-tap-hold-exec",
            "observation": "recon.C 2.50 wt% after stop; hold line-up complete; Carbveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "tap-hold clock started after REJECT"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 7800.0, "event": "furnace ESD proposed"},
                {"t_s": 8400.0, "event": "MODIFY tap-hold; furnace ESD refused"},
            ],
            "observed_effects": [
                "Carbveil restore did not reopen the carbon call",
                "furnace ESD never fired; B-2 held tap on the plant combustion-IR",
            ],
            "surprises": ["post-stop combustion-IR climbed to 2.50 wt% while Carbveil still read 0.42"],
            "new_state": {"tap": "held", "hall": "in service", "b2": "held"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("tap_hold", 0.12),
                ("no_furnace_esd", 0.10),
                ("carbveil_nonsubstitution", 0.08),
                ("hold_floor_complete", 0.06),
                ("held_heat_cost", -0.02),
            ],
            "operational execution gate: tap-hold because Carbveil is not a restore license; not a carbon re-vote",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "tap-hold"]),
    }
    return {
        "id": "nelb-r43-a1",
        "snn_tags": list(SNN_TAGS),
        "spike_events": events,
        "language_view": {
            "description": "Slagfen Steel SF-8. Plant-owned combustion-IR reconstructs 2.00 wt% carbon from 0.50*8.00/2.00 while Carbveil still reports 0.48 wt%. The gate REJECTs continue-tap. An 18 min tap-hold floor is serialized in the stream. Companion t2 MODIFYs a BOF-hall ESD into a plant-LECO tap-hold.",
            "trajectory": traj,
            "trajectory_tap_hold": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "leco.A / leco.m / leco.snr": "CO2 peak-area, coupon mass, and SNR; the physics channels the reconstruction consumes",
                "recon.C / recon.R": "serialized remaining-carbon wt% and area-to-mass identity",
                "bath.T / bath.O / carbveil.C / permit.slide / lance.kW / leco.drop / collude.clerk": "bath witnesses, vendor last-good, permit clock slide, lance kW, dropped packets, clerk",
                "ops.prop / gate.stop / ops.kill / gate.hold": "continue-tap proposal, REJECT, furnace-ESD proposal, companion MODIFY",
                "hold.start / hold.floor / hold.set / hold.held / furnace.esd / hold.lock": "operational companion channels plus the 18 min floor",
            },
            "temporal_motifs": [
                "vendor-green while plant-over: carbveil.C 0.48 next to recon.C 2.00",
                "reconstruction as event: recon.C 2.00 equals 0.50*8.00/2.00",
                "REJECT then operational MODIFY: gate.stop at 5400 s, gate.hold at 8400 s",
                "slow floor in-stream: hold.start 6000 s, hold.floor 7080 s (18.0 min)",
                "tight LECO pair: leco.A then leco.m +1.4 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Carbveil is 0.48 wt%' = carbveil.C 0.48; '2.00 wt% remaining carbon' = recon.C 2.00; 'refuse continue-tap' = gate.stop REJECT; 'hold not furnace ESD' = gate.hold MODIFY",
            "why_high_value": "New combustion-IR remaining-carbon family on a BOF heat (not NDIR CO, not FTIR methanol, not spark-OES, not ICP-OES, not CEMS). Lead REJECT of continue-tap on a recomputable over-carbon heat that a vendor last-good patch and a permit clock slide would have cleared. Three-party collusion includes the LECO infra owner. Independent CUBA LIF raster. Companion t2 is operational tap-hold. sim_or_real=designed.",
            "encoder_spec": {
                "prng": "CUBA LIF (lif_raster.generate_lif_raster) plus MT19937 amplitudes",
                "seeds": {
                    "raster": 2026090431,
                    "stream_note": "stream amplitudes are authored constants; raster is independent CUBA LIF",
                },
                "draw_order": "independent CUBA LIF full window; 1.4 ms physics pair is stream motif, not excerpt copy",
                "thinning": "combustion-IR exists at ~0.2 Hz; stream keeps 5 A points plus mass pairs; recon keeps 5 of ~20 solver ticks",
                "time_alias": "t_rel_ms; t0 = 2026-09-02T01:00:00Z campaign start",
            },
            "distillation_targets": [
                "combustion-IR reconstruction head: C_wt = k_c * A_co2 / m; R = A / m",
                "conjunctive isolate floor vs continue-tap vs furnace ESD",
                "vendor-LECO nonsubstitution plus three-party collusion including the infra owner",
                "operational companion: tap-hold without restoring on Carbveil",
                "independent CUBA LIF raster with race/refractory/adaptation tags",
            ],
        },
        "reconstruction_model": {
            "name": "combustion_ir_bof_carbon",
            "formula": "C_wt = k_c * A_co2 / m_g; R = A_co2 / m_g",
            "parameters": {
                "k_c": 0.50,
                "isolate_floor_wt": 1.60,
                "kill_wt": 4.00,
                "snr_lock": 8.0,
                "tap_hold_min": 18.0,
            },
            "worked_example": {"A_co2": 8.00, "m_g": 2.00, "R": 4.00, "C_wt": 2.00},
            "check": "0.50 * 8.00 / 2.00 = 2.00 exactly; 8.00 / 2.00 = 4.00 exactly; 6000 s + 1080 s = 7080 s = 18.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.040,
            "code": "sf8.leco_tap_gate",
            "note": "REJECT accumulator wins: plant combustion-IR carbon evidence overpowers the Carbveil continue advocate",
            "decode_rule": "reject-continue if carbon_estimator AND leco_lock fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("carbon_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("leco_lock", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("reject_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "sf8.leco_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 40.0},
                {"check": "sf8.hold_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r43-a1",
            clock_domain="sf8-leco-campaign-relative-ms-t0-2026-09-02T01:00:00Z",
            tags=["combustion-ir-carbon", "REJECT", "MODIFY", "serialized-reconstruction", "operational-t2", "independent-lif"],
            distillation_value="Independent LIF raster teaches race/refractory/adaptation while the language view teaches combustion-IR remaining-carbon reconstruction-as-SoT.",
        ),
    }


# ---------------------------------------------------------------------------
# nelb-r43-a2 — Hall-effect remaining DC of a potline bus, hil, MODIFY / ACCEPT
# ---------------------------------------------------------------------------
def rec_a2():
    k_h = 4.00
    v_h = 8.00
    b_t = 2.00
    i_ka = k_h * v_h / b_t
    r_vb = v_h / b_t
    _exact(i_ka, 16.00)
    _exact(r_vb, 4.00)
    _exact(k_h * 2.00 / b_t, 4.00)
    _exact(k_h * 4.00 / b_t, 8.00)
    _exact(k_h * 6.00 / b_t, 12.00)
    _exact(k_h * 10.00 / b_t, 20.00)
    v_bus = 0.50
    p_mw = i_ka * v_bus
    _exact(p_mw, 8.00)
    _exact(2820.0 + 1440.0, 4260.0)

    raster = make_lif_raster(
        neurons=25,
        mean_rate_hz=50.0,
        window_ms=32.0,
        seed=2026090432,
        source="cr5.hall.Vh",
        target="culmride.bus_isolate_core",
        table=[
            {"from": "hall_Vh", "to": "current_estimator", "weight": 1.35},
            {"from": "hall_snr", "to": "magnet_norm_core", "weight": 1.20},
            {"from": "hallveil_i", "to": "vendor_continue_advocate", "weight": 0.40},
        ],
        third_factor={
            "modulator": "ach.hall_zero_skip_salience",
            "tau_e_s": 1.2,
            "tau_e_ms": 1200.0,
            "eligibility": (
                "pre-post coincidence on keep-bus synapses; the Hall-effect "
                "modulator depresses keep-bus and referral links when Hall "
                "voltage stays high inside tau_e of an SNR lock so a Hallveil "
                "last-good cannot hide 16.00 kA or name Perrin Ash"
            ),
        },
        channel_prefix="hall.n",
        anchor=(
            "CR-5 HIL coupon 32 ms frame at Vh 8.00 mV / B 2.00 T / SNR 14.0 "
            "(t_s 1560) reconstructing 16.00 kA over the 12.00 isolate floor"
        ),
        tau_m_ms=12.0,
    )
    w_s = 0.032
    events = [
        ev(90.0, "hall.Vh", 2.00, code="VH_MV", units="mV", note="HIL Hall-effect remaining DC of Culmride Smelter CR-5 dummy potline bus B-3 in HALL-HIL-5; semiconductor Hall-clamp family, not Faraday FOCT, not Rogowski, not SERF OPM, not leftover-mill LFV Al, not API-670 proximity"),
        ev(180000.0, "hall.snr", 9.0, code="HALL_SNR", units="1", note="early magnet SNR; isolate needs SNR>=12"),
        ev(360000.0, "recon.I", 4.00, code="I_KA", units="kA", note="4.00*2.00/2.00=4.00 exact"),
        ev(540000.0, "mag.zero", 1.0, code="MAG_AE", units="bool", note="plant magnet-zero AE present on the early frame"),
        ev(720000.0, "hallveil.I", 2.40, code="VENDOR_KA", units="kA", note="Hallveil last-good DC-cloud; not admissible SoT"),
        ev(900000.0, "hall.Vh", 4.00, code="VH_MV", units="mV"),
        ev(1080000.0, "recon.I", 8.00, code="I_KA", units="kA", note="4.00*4.00/2.00=8.00; isolate-adjacent band"),
        ev(1260000.0, "mag.zero", 0.0, code="MAG_AE", units="bool", note="missing magnet-zero AE burst; Hallveil UTC vs plant UTC+2 skipped the zero by 120 min"),
        ev(1440000.0, "hall.B", 2.00, code="B_T", units="T", note="plant-owned clamp magnet on copper fieldbus; independent of Hallveil"),
        ev(1560000.0, "hall.Vh", 8.00, code="VH_MV", units="mV", note="isolate-floor frame; raster sidecar"),
        ev(1560001.2, "hall.snr", 14.0, code="HALL_SNR", units="1", note="1.2 ms magnet-norm after Hall voltage"),
        ev(1740000.0, "recon.I", 16.00, code="I_KA", units="kA", note="4.00*8.00/2.00=16.00 exact; isolate 12.00, potline-trip 40.00"),
        ev(1920000.0, "recon.P", 8.00, code="P_MW", units="MW", note="16.00*0.50=8.00 exact bus-power identity"),
        ev(2100000.0, "recon.R", 4.00, code="R_VH_B", units="mV_T", note="8.00/2.00=4.00 exact Vh/B identity"),
        ev(2280000.0, "hallveil.I", 2.40, code="VENDOR_KA", units="kA"),
        ev(2460000.0, "ops.prop", 1.0, code="KEEP_BUS_REFER", units="bool", note="night lead Tove Larch: keep dummy bus B-3 and refer Hall tech Perrin Ash"),
        ev(2640000.0, "gate.isol", 1.0, code="MODIFY", units="decision", note="isolate this bus; refuse the person-referral; Hallveil not SoT"),
        ev(2820000.0, "bus.lock", 1.0, code="BUS_ISOL", units="bool", note="bookend 1 of the 24.0 min new-magnet floor"),
        ev(3000000.0, "hall.Vh", 6.00, code="VH_MV", units="mV"),
        ev(3180000.0, "recon.I", 12.00, code="I_KA", units="kA", note="4.00*6.00/2.00=12.00 still at the isolate floor"),
        ev(3360000.0, "mag.zero", 0.0, code="MAG_AE", units="bool"),
        ev(3540000.0, "hall.B", 2.00, code="B_T", units="T"),
        ev(3720000.0, "hallveil.I", 2.30, code="VENDOR_KA", units="kA"),
        ev(3900000.0, "recon.P", 6.00, code="P_MW", units="MW", note="12.00*0.50=6.00"),
        ev(4080000.0, "recon.R", 3.00, code="R_VH_B", units="mV_T"),
        ev(4260000.0, "mag.floor", 1.0, code="MAG_FLOOR", units="bool", note="2820 s + 1440 s = 4260 s = 24.0 min"),
        ev(4440000.0, "ops.restart", 1.0, code="NEW_MAGNET", units="bool", note="Larch: restart B-3 on a new Hall clamp after the floor"),
        ev(4620000.0, "gate.restart", 1.0, code="ACCEPT", units="decision", note="companion t2: new-magnet restart of the dummy bus; keep-running refused earlier"),
        ev(4800000.0, "mag.new", 1.0, code="MAG_NEW", units="bool"),
        ev(4980000.0, "hall.Vh", 10.00, code="VH_MV", units="mV", note="post-isolate dummy still high until the new clamp"),
        ev(5160000.0, "recon.I", 20.00, code="I_KA", units="kA", note="4.00*10.00/2.00=20.00 on the pre-restart dummy"),
        ev(5340000.0, "hallveil.I", 2.20, code="VENDOR_KA", units="kA"),
        ev(5520000.0, "perrin.badge", 0.0, code="TECH_FAULT", units="bool", note="Perrin Ash exonerated: missing magnet-zero AE plus timezone skip, not last-to-badge"),
        ev(5700000.0, "bus.lock", 1.0, code="BUS_ISOL", units="bool"),
        ev(5880000.0, "mag.zero", 1.0, code="MAG_AE", units="bool", note="new-magnet zero AE present"),
        ev(6060000.0, "hall.snr", 14.0, code="HALL_SNR", units="1"),
        ev(6240000.0, "hall.B", 2.00, code="B_T", units="T"),
        ev(6420000.0, "recon.P", 10.00, code="P_MW", units="MW"),
        ev(6600000.0, "keep.run", 0.0, code="KEEP_REFUSED", units="bool"),
        ev(6780000.0, "hallveil.I", 2.20, code="VENDOR_KA", units="kA"),
        ev(6960000.0, "mag.new", 1.0, code="MAG_NEW", units="bool"),
        ev(7140000.0, "perrin.badge", 0.0, code="TECH_FAULT", units="bool"),
        ev(7320000.0, "recon.R", 5.00, code="R_VH_B", units="mV_T"),
        ev(7500000.0, "bus.held", 1.0, code="BUS_ISOL", units="bool"),
        ev(7680000.0, "ops.prop", 1.0, code="KEEP_BUS_REFER", units="bool"),
        ev(7860000.0, "gate.isol", 1.0, code="MODIFY", units="decision"),
        ev(8040000.0, "mag.floor", 1.0, code="MAG_FLOOR", units="bool"),
        ev(8220000.0, "gate.restart", 1.0, code="ACCEPT", units="decision"),
        ev(8400000.0, "bus.V", 0.50, code="V_KV", units="kV", note="plant bus drop used by the P=I*V identity; unread by Hallveil"),
        ev(8580000.0, "recon.P", 8.00, code="P_MW", units="MW"),
        ev(8760000.0, "hall.snr", 14.0, code="HALL_SNR", units="1"),
        ev(8940000.0, "bus.held", 1.0, code="BUS_ISOL", units="bool"),
    ]
    assert_stream(events)
    if len(events) != 52:
        raise RuntimeError(len(events))

    traj = {
        "id": "nelb-r43-a2-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "CR-HALL-2026-0902",
            "domain": "hall_effect_potline_dc",
            "setting": "Culmride Smelter CR-5 (invented), dummy potline bus B-3 in HALL-HIL-5. Plant-owned semiconductor Hall-effect clamp is the remaining-DC SoT. Hallveil vendor Hall-cloud is not SoT. HIL dummy; not a live plant. Not r25 Faraday FOCT, not leftover-mill Rogowski, not live r21 SERF OPM, not leftover-mill r19 LFV Al, not r52 API-670 proximity.",
            "observables_at_decision": {
                "Vh_mV": v_h,
                "B_T": b_t,
                "k_h": k_h,
                "I_kA": i_ka,
                "R_Vh_B": r_vb,
                "P_MW": p_mw,
                "hall_snr": 14.0,
                "hallveil_kA": 2.40,
                "mag_zero_ae": False,
                "isolate_floor_kA": 12.00,
            },
            "margin_authority": "CR-5 HIL SOP rev B: if reconstructed I_kA >= 12.00 AND Hall SNR >= 12.0, keep-bus is forbidden even if Hallveil reports 2.40 kA. Person-referral of the Hall tech is not a substitute isolate. Potline-trip tripwire is 40.00 kA.",
        },
        "proposed_action": {
            "actor": "night lead Tove Larch, citing Hallveil 2.40 kA and a quiet Hall channel",
            "summary": "keep dummy bus B-3 in service and refer Hall tech Perrin Ash for a missed magnet-zero",
            "basis_claimed": "Hallveil is the OEM SoT; Perrin was last-to-badge the dummy clamp",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Keep-bus is refused; isolate B-3. Serialized reconstruction: I_kA = k_h * Vh / B = 4.00 * 8.00 / 2.00 = 16.00, which is 4.00 kA over the 12.00 isolate floor and 24.00 kA under the 40.00 potline-trip tripwire, and Hall SNR is 14.0 >= 12.0. Vh/B identity = 8.00 / 2.00 = 4.00; bus-power identity P = I * V_bus = 16.00 * 0.50 = 8.00 MW. Missing magnet-zero AE plus Hallveil UTC vs plant UTC+2 skip the zero by 120 min, so Perrin Ash is not last-to-badge-guilty. Ordered: isolate this dummy bus; do not refer the tech; Hallveil is not SoT. Scope: this MODIFY does not trip the potline (that is a different gate) and does not restart until the 24 min new-magnet floor.",
            "threshold": "I_kA>=12.00 AND hall_snr>=12.0 => isolate bus; Hallveil is not SoT; person-referral is not an isolate",
            "stated_residuals": "24 min new-magnet floor still required; 16.00 vs a true 40.00 trip is a production cut; Hallveil remains the only OEM Hall channel",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 2640: B-3 isolated; Perrin not referred; Hallveil not SoT",
            "tool": "cr5-hall-bus-gate-cli",
            "observation": "I 16.00 kA recomputes from Vh 8.00 mV and B 2.00 T; dummy bus locked; magnet-zero AE absent on the isolate frame",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 1560.0, "event": "Hall Vh 8.00 mV; raster frame; I 16.00 kA"},
                {"t_s": 2460.0, "event": "ops proposes keep-bus plus refer Perrin"},
                {"t_s": 2640.0, "event": "MODIFY isolate bus; referral refused"},
                {"t_s": 2820.0, "event": "24 min new-magnet bookend 1"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4620.0, "event": "companion ACCEPT new-magnet restart"},
            ],
            "observed_effects": [
                "remaining DC recomputes from the serialized Hall-effect model at every recon.I event",
                "a Hallveil-only head would have kept B-3 and named Perrin",
                "24 min new-magnet floor is in the stream (bus.lock, mag.floor)",
            ],
            "surprises": [
                "timezone-skipped magnet-zero AE, not last-to-badge, was the only missing plant witness",
            ],
            "new_state": {
                "b3": "isolated",
                "perrin": "exonerated",
                "hallveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 1080000.0,
        },
        "reward_components": reward(
            0.40,
            [
                ("hall_dc_reconstruction", 0.14),
                ("conjunctive_isolate_floor", 0.12),
                ("hallveil_nonsubstitution", 0.08),
                ("tech_exoneration", 0.08),
                ("isolate_time_cost", -0.02),
            ],
            "scored for an isolate MODIFY on a recomputable Hall-effect DC slip while refusing a Hallveil last-good and a last-to-badge referral; 24 min floor is priced as downtime",
        ),
        "meta": meta_common(
            tags=["MODIFY", "hall-effect-dc", "serialized-reconstruction", "operational-companion", "exoneration"],
            distillation_value="Independent LIF raster plus serialized k_h*Vh/B remaining-DC reconstruction; race is the 1.2 ms Vh/SNR pair; refractory and adaptation are in the CUBA excerpt.",
            distillation_note="Hall-effect DC gate: serialized k_h*Vh/B plus SNR lock beats a vendor last-good and a person-referral; companion t2 is the new-magnet restart",
        ),
    }
    traj2 = {
        "id": "nelb-r43-a2-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "CR-HALL-2026-0902-exec",
            "domain": "new_magnet_hall_dc_restart_execution",
            "setting": "Same HALL-HIL-5 dummy after the isolate. Operator proposes a new-magnet restart of B-3. This companion is the operational restart, not a second DC vote.",
            "observables_at_decision": {
                "I_kA": 20.00,
                "mag_floor_s": 1440.0,
                "mag_new": True,
                "perrin_fault": False,
            },
            "margin_authority": "CR-5 execution SOP: new-magnet restart after the 24 min floor; keep-running remains refused.",
        },
        "proposed_action": {
            "actor": "night lead Tove Larch",
            "summary": "restart dummy bus B-3 on a new Hall clamp now that the 24 min floor is paid",
            "basis_claimed": "the isolate already stopped B-3; a new magnet is the cheapest return",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "New-magnet restart of the dummy bus after the 24 min floor. Keep-running stays refused. Perrin remains exonerated. Hallveil is still not SoT. ACCEPT the new-magnet restart of B-3 only. Do not trip the potline. Do not treat Hallveil 2.20 kA as a clear.",
            "threshold": "mag_floor_complete AND bus_isolated AND keep_running_refused AND hallveil_not_sot",
            "stated_residuals": "dummy still reads 20.00 kA until the new clamp takes; potline stays out of scope",
        },
        "executed_action": {
            "summary": "new magnet accepted at t_s 4620; keep-running not restored; Perrin not blamed",
            "tool": "cr5-mag-exec",
            "observation": "magnet-zero AE present on the new clamp; dummy still isolated from the potline",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 2820.0, "event": "new-magnet clock started after isolate"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4440.0, "event": "new-magnet restart proposed"},
                {"t_s": 4620.0, "event": "ACCEPT new-magnet restart"},
            ],
            "observed_effects": [
                "Hallveil restore did not reopen the DC call",
                "Perrin was not last-to-badge; new-magnet AE is present",
            ],
            "surprises": ["post-isolate dummy climbed to 20.00 kA while Hallveil still read 2.20"],
            "new_state": {"bus": "new-magnet restart", "potline": "in service", "perrin": "exonerated"},
            "latency_ms": 1440000.0,
        },
        "reward_components": reward(
            0.35,
            [
                ("new_magnet_restart", 0.12),
                ("keep_running_refused", 0.10),
                ("hallveil_nonsubstitution", 0.08),
                ("tech_exoneration", 0.06),
                ("held_bus_cost", -0.01),
            ],
            "operational execution gate: new-magnet restart because Hallveil is not a restore license; not a DC re-vote",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "new-magnet"]),
    }
    return {
        "id": "nelb-r43-a2",
        "snn_tags": list(SNN_TAGS),
        "spike_events": events,
        "language_view": {
            "description": "Culmride Smelter CR-5 HIL dummy. Plant-owned Hall-effect clamp reconstructs 16.00 kA from 4.00*8.00/2.00 while Hallveil still reports 2.40 kA. The gate MODIFYs keep-bus into an isolate and refuses a last-to-badge referral of Perrin Ash. A 24 min new-magnet floor is serialized. Companion t2 ACCEPTs the new-magnet restart.",
            "trajectory": traj,
            "trajectory_new_magnet_restart": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "hall.Vh / hall.B / hall.snr": "Hall voltage, clamp B, and SNR; the physics channels the reconstruction consumes",
                "recon.I / recon.P / recon.R": "serialized remaining-DC kA, bus-power identity, and Vh/B identity",
                "mag.zero / hallveil.I / bus.V / perrin.badge": "magnet-zero AE, vendor Hall cloud, bus drop, tech-fault denial",
                "ops.prop / gate.isol / ops.restart / gate.restart": "keep-bus proposal, MODIFY isolate, new-magnet proposal, companion ACCEPT",
                "bus.lock / mag.floor / mag.new / bus.held / keep.run": "operational companion channels plus the 24 min floor",
            },
            "temporal_motifs": [
                "vendor-green while plant-over: hallveil.I 2.40 next to recon.I 16.00",
                "reconstruction as event: recon.I 16.00 equals 4.00*8.00/2.00",
                "MODIFY then operational ACCEPT: gate.isol at 2640 s, gate.restart at 4620 s",
                "slow floor in-stream: bus.lock 2820 s, mag.floor 4260 s (24.0 min)",
                "tight Hall pair: hall.Vh then hall.snr +1.2 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Hallveil is 2.40 kA' = hallveil.I 2.40; '16 kA remaining DC' = recon.I 16.00; 'isolate bus' = gate.isol MODIFY; 'new-magnet restart' = gate.restart ACCEPT",
            "why_high_value": "New Hall-effect remaining-DC family on a potline HIL dummy (not Faraday FOCT, not Rogowski, not SERF OPM, not leftover-mill LFV Al). Lead MODIFY isolate on a recomputable DC slip plus timezone-exoneration of the Hall tech. Independent CUBA LIF raster. Companion t2 is operational new-magnet restart. sim_or_real=hil.",
            "encoder_spec": {
                "prng": "CUBA LIF (lif_raster.generate_lif_raster) plus MT19937 amplitudes",
                "seeds": {
                    "raster": 2026090432,
                    "stream_note": "stream amplitudes are authored constants; raster is independent CUBA LIF",
                },
                "draw_order": "independent CUBA LIF full window; 1.2 ms physics pair is stream motif, not excerpt copy",
                "thinning": "Hall clamp exists at ~10 Hz; stream keeps 5 Vh points; recon keeps 5 of ~40 solver ticks",
                "time_alias": "t_rel_ms; t0 = 2026-09-02T02:00:00Z HIL coupon start",
            },
            "distillation_targets": [
                "Hall-effect DC reconstruction head: I = k_h * Vh / B; P = I * V_bus; Vh/B identity",
                "conjunctive isolate floor vs keep-bus vs potline trip",
                "vendor-Hall nonsubstitution plus timezone exoneration vs last-to-badge",
                "operational companion: new-magnet restart without restoring on Hallveil",
                "independent CUBA LIF raster with race/refractory/adaptation tags",
            ],
        },
        "reconstruction_model": {
            "name": "hall_effect_potline_dc",
            "formula": "I_kA = k_h * Vh_mV / B_T; R = Vh_mV / B_T; P_MW = I_kA * V_bus_kV",
            "parameters": {
                "k_h": 4.00,
                "B_T": 2.00,
                "V_bus_kV": 0.50,
                "isolate_floor_kA": 12.00,
                "trip_kA": 40.00,
                "snr_lock": 12.0,
                "mag_min": 24.0,
            },
            "worked_example": {"Vh_mV": 8.00, "I_kA": 16.00, "P_MW": 8.00, "R": 4.00},
            "check": "4.00 * 8.00 / 2.00 = 16.00 exactly; 8.00 / 2.00 = 4.00 exactly; 16.00 * 0.50 = 8.00 exactly; 2820 s + 1440 s = 4260 s = 24.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 32.0,
            "decision_window_s": 0.032,
            "code": "cr5.hall_bus_gate",
            "note": "MODIFY accumulator wins: plant Hall-effect DC evidence overpowers the Hallveil keep advocate",
            "decode_rule": "isolate if current_estimator AND magnet_norm fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("current_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("magnet_norm", 50, 1.2, 50.0, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("modify_latch", 80, 1.6, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "cr5.hall_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 32.0},
                {"check": "cr5.mag_scorer", "neurons": 50, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r43-a2",
            clock_domain="cr5-hall-hil-relative-ms-t0-2026-09-02T02:00:00Z",
            tags=["hall-effect-dc", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2", "independent-lif", "exoneration"],
            distillation_value="Independent LIF raster teaches race/refractory/adaptation while the language view teaches Hall-effect remaining-DC reconstruction-as-SoT plus timezone exoneration.",
        ),
    }


# ---------------------------------------------------------------------------
# nelb-r43-a3 — impulse-excitation remaining E of a kiln setter, simulated,
# ACCEPT / REJECT
# ---------------------------------------------------------------------------
def rec_a3():
    k_e = 0.050
    f_khz = 20.00
    e_gpa = k_e * (f_khz ** 2)
    _exact(e_gpa, 20.00)
    _exact(k_e * (24.00 ** 2), 28.80)
    _exact(k_e * (18.00 ** 2), 16.20)
    _exact(k_e * (16.00 ** 2), 12.80)
    nu = 0.25
    g_gpa = e_gpa / (2.0 * (1.0 + nu))
    _exact(g_gpa, 8.00)
    f2 = f_khz ** 2
    _exact(f2, 400.00)
    _exact(6000.0 + 720.0, 6720.0)

    raster = make_lif_raster(
        neurons=16,
        mean_rate_hz=62.5,
        window_ms=36.0,
        seed=2026090433,
        source="mh3.iet.f",
        target="marlholt.setter_accept_core",
        table=[
            {"from": "iet_f", "to": "E_estimator", "weight": 1.30},
            {"from": "iet_snr", "to": "iet_lock_core", "weight": 1.10},
            {"from": "setveil_e", "to": "vendor_dump_advocate", "weight": 0.42},
        ],
        third_factor={
            "modulator": "na.iet_setter_scope_eligibility",
            "tau_e_s": 2.0,
            "tau_e_ms": 2000.0,
            "eligibility": (
                "pre-post coincidence on kiln-dump synapses; the plant IET "
                "modulator depresses dump-all links when tap frequency stays "
                "low inside tau_e of an SNR lock so a Setveil last-good cannot "
                "hide a 20.00 GPa remaining-modulus slip on S-4 or expand the "
                "isolate past S-4"
            ),
        },
        channel_prefix="iet.n",
        anchor=(
            "MH-3 IET-SIM-4 36 ms frame at f 20.00 kHz / SNR 11.0 (t_s 3000) "
            "reconstructing 20.00 GPa under the 24.00 isolate floor, S-4 only"
        ),
        tau_m_ms=8.0,
    )
    w_s = 0.036
    events = [
        ev(100.0, "iet.f", 24.00, code="F_KHZ", units="kHz", note="simulated impulse-excitation remaining Young's modulus of Marlholt Kiln MH-3 setter S-4 in IET-SIM-4; tap-and-listen bar family, not RUS porcelain, not SFRA, not acoustic pyrometry, not bender-element Vs, not resonant-ultrasound spectroscopy"),
        ev(180000.0, "iet.snr", 7.0, code="IET_SNR", units="1", note="early SNR under the 8.0 lock floor"),
        ev(360000.0, "recon.E", 28.80, code="E_GPA", units="GPa", note="0.050*24.00^2=28.80 exact; still over the 24.00 isolate floor"),
        ev(540000.0, "set.T", 300.0, code="SET_K", units="K", note="plant setter thermocouple on the simulated coupon; independent of Setveil"),
        ev(720000.0, "setveil.E", 48.00, code="VENDOR_GPA", units="GPa", note="Setveil last-good modulus cloud; healthy-looking 48.00 GPa; not admissible SoT"),
        ev(900000.0, "iet.f", 22.00, code="F_KHZ", units="kHz"),
        ev(1080000.0, "recon.E", 24.20, code="E_GPA", units="GPa", note="0.050*22.00^2=24.20; isolate-adjacent band"),
        ev(1260000.0, "s1.E", 40.00, code="E_GPA", units="GPa", note="adjacent setter S-1 stays healthy; out of scope for this ACCEPT"),
        ev(1440000.0, "s2.E", 38.00, code="E_GPA", units="GPa", note="S-2 out of scope"),
        ev(1620000.0, "s3.E", 42.00, code="E_GPA", units="GPa", note="S-3 out of scope"),
        ev(1800000.0, "iet.f", 18.00, code="F_KHZ", units="kHz"),
        ev(1980000.0, "recon.E", 16.20, code="E_GPA", units="GPa", note="0.050*18.00^2=16.20; under isolate 24.00, over dump 8.00"),
        ev(2160000.0, "recon.G", 6.48, code="G_GPA", units="GPa", note="16.20/(2*1.25)=6.48"),
        ev(2340000.0, "setveil.E", 48.00, code="VENDOR_GPA", units="GPa"),
        ev(2520000.0, "iet.snr", 9.0, code="IET_SNR", units="1"),
        ev(2700000.0, "recon.f2", 324.00, code="F2", units="kHz2", note="18.00^2=324.00"),
        ev(3000000.0, "iet.f", 20.00, code="F_KHZ", units="kHz", note="isolate-floor frame; raster sidecar"),
        ev(3000001.5, "iet.snr", 11.0, code="IET_SNR", units="1", note="1.5 ms IET lock after f; 11.0 >= 8.0"),
        ev(3180000.0, "recon.E", 20.00, code="E_GPA", units="GPa", note="0.050*20.00^2=20.00 exact; isolate 24.00, kiln-dump 8.00"),
        ev(3360000.0, "recon.G", 8.00, code="G_GPA", units="GPa", note="20.00/(2*(1+0.25))=8.00 exact shear identity"),
        ev(3540000.0, "recon.f2", 400.00, code="F2", units="kHz2", note="20.00^2=400.00 exact"),
        ev(3720000.0, "setveil.E", 47.50, code="VENDOR_GPA", units="GPa"),
        ev(3900000.0, "s1.E", 40.00, code="E_GPA", units="GPa"),
        ev(4080000.0, "s2.E", 38.00, code="E_GPA", units="GPa"),
        ev(4260000.0, "s3.E", 42.00, code="E_GPA", units="GPa"),
        ev(4440000.0, "set.T", 301.0, code="SET_K", units="K"),
        ev(4620000.0, "ops.prop", 1.0, code="ISOLATE_S4", units="bool", note="sim operator Edda Moss: isolate S-4 only; S-1..S-3 stay in the set"),
        ev(4800000.0, "gate.acc", 1.0, code="ACCEPT", units="decision", note="bounded ACCEPT of S-4 isolate; kiln dump refused; Setveil not SoT"),
        ev(4980000.0, "s4.lock", 1.0, code="S4_ISOL", units="bool"),
        ev(6000000.0, "surv.start", 1.0, code="SURV_START", units="bool", note="bookend 1 of the 12.0 min survey floor"),
        ev(6720000.0, "surv.floor", 1.0, code="SURV_FLOOR", units="bool", note="6000 s + 720 s = 6720 s = 12.0 min"),
        ev(7200000.0, "ops.skip", 1.0, code="SKIP_SURVEY", units="bool", note="Moss: skip the remaining-setter survey; Setveil still 47.50 GPa"),
        ev(7800000.0, "gate.surv", 1.0, code="REJECT", units="decision", note="companion t2: REJECT skip-survey; S-1..S-3 stay in the survey takt"),
        ev(8400000.0, "surv.held", 1.0, code="SURV_HELD", units="bool"),
        ev(9000000.0, "iet.f", 16.00, code="F_KHZ", units="kHz"),
        ev(9600000.0, "recon.E", 12.80, code="E_GPA", units="GPa", note="0.050*16.00^2=12.80 post-isolate on S-4; still over dump 8.00"),
        ev(10200000.0, "setveil.E", 47.00, code="VENDOR_GPA", units="GPa"),
        ev(10800000.0, "s1.E", 39.00, code="E_GPA", units="GPa"),
        ev(11400000.0, "s2.E", 38.00, code="E_GPA", units="GPa"),
        ev(12000000.0, "s3.E", 41.00, code="E_GPA", units="GPa"),
        ev(12600000.0, "kiln.dump", 0.0, code="DUMP_NOT_TAKEN", units="bool"),
        ev(13200000.0, "surv.held", 1.0, code="SURV_HELD", units="bool"),
        ev(13800000.0, "recon.G", 5.12, code="G_GPA", units="GPa", note="12.80/(2*1.25)=5.12"),
        ev(14400000.0, "set.T", 302.0, code="SET_K", units="K"),
        ev(15000000.0, "s4.lock", 1.0, code="S4_ISOL", units="bool"),
        ev(15600000.0, "ops.skip", 1.0, code="SKIP_SURVEY", units="bool"),
        ev(16200000.0, "gate.surv", 1.0, code="REJECT", units="decision"),
        ev(16800000.0, "surv.floor", 1.0, code="SURV_FLOOR", units="bool"),
        ev(17400000.0, "recon.f2", 256.00, code="F2", units="kHz2", note="16.00^2=256.00"),
        ev(18000000.0, "iet.snr", 11.0, code="IET_SNR", units="1"),
        ev(18600000.0, "s1.E", 39.00, code="E_GPA", units="GPa"),
        ev(19200000.0, "surv.held", 1.0, code="SURV_HELD", units="bool"),
    ]
    assert_stream(events)
    if len(events) != 52:
        raise RuntimeError(len(events))

    traj = {
        "id": "nelb-r43-a3-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "MH-IET-2026-0902",
            "domain": "impulse_excitation_kiln_setter",
            "setting": "Marlholt Kiln MH-3 (invented), simulated coupon IET-SIM-4, setter S-4. Plant-owned impulse-excitation tap-and-listen is the remaining-modulus SoT. Setveil vendor IET-cloud is not SoT. Simulated campaign; not a live plant. Not leftover-mill RUS porcelain, not SFRA, not acoustic pyrometry, not live r41 bender-element Vs.",
            "observables_at_decision": {
                "f_kHz": f_khz,
                "k_e": k_e,
                "E_GPa": e_gpa,
                "G_GPa": g_gpa,
                "f2": f2,
                "iet_snr": 11.0,
                "setveil_GPa": 48.00,
                "s1_E_GPa": 40.00,
                "s2_E_GPa": 38.00,
                "s3_E_GPa": 42.00,
                "isolate_floor_GPa": 24.00,
            },
            "margin_authority": "MH-3 setter SOP rev D: if reconstructed E_GPa <= 24.00 AND IET SNR >= 8.0, S-4 isolate is required even if Setveil reports 48.00 GPa. Kiln dump is a different gate (E_GPa <= 8.00). S-1..S-3 are out of scope unless their own reconstructions cross 24.00.",
        },
        "proposed_action": {
            "actor": "sim operator Edda Moss, citing plant IET 20.00 GPa on S-4 and healthy S-1..S-3",
            "summary": "isolate setter S-4 only; keep S-1..S-3 in the set; do not dump the kiln",
            "basis_claimed": "only S-4 reconstructed under 24.00 GPa; Setveil 48.00 GPa is not SoT but also does not license a kiln dump",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Bounded ACCEPT of S-4 isolate. Serialized reconstruction: E_GPa = k_e * f^2 = 0.050 * 20.00^2 = 20.00, which is 4.00 GPa under the 24.00 isolate floor and 12.00 GPa over the 8.00 kiln-dump tripwire, and IET SNR is 11.0 >= 8.0. Shear identity G = E / (2(1+nu)) = 20.00 / 2.50 = 8.00; f^2 identity = 20.00^2 = 400.00. S-1/S-2/S-3 reconstruct 40.00/38.00/42.00 GPa, all over 24.00, so they stay out of scope. Setveil 48.00 GPa is a last-good denial, not a dump license and not a clear. Ordered: isolate S-4 only. Scope: this ACCEPT does not dump the kiln, does not isolate S-1..S-3, and does not skip the 12 min remaining-setter survey (that is the companion question).",
            "threshold": "E_GPa<=24.00 AND iet_snr>=8.0 => isolate that setter only; Setveil is not SoT; dump if E_GPa<=8.00; S-1..S-3 out of scope while E_GPa>24.00",
            "stated_residuals": "12 min survey still required; 20.00 vs a true 8.00 dump is a production cut; Setveil remains the only OEM IET channel",
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 4800: S-4 isolated; S-1..S-3 left in the set; Setveil not SoT",
            "tool": "mh3-iet-setter-gate-cli",
            "observation": "E 20.00 GPa recomputes from f 20.00 kHz; S-4 hashed; adjacent setters remain over 24.00 GPa",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "IET f 20.00 kHz; raster frame; E 20.00 GPa"},
                {"t_s": 4620.0, "event": "ops proposes S-4 isolate"},
                {"t_s": 4800.0, "event": "ACCEPT S-4 isolate; kiln dump refused"},
                {"t_s": 6000.0, "event": "12 min survey bookend 1"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7800.0, "event": "companion REJECT skip-survey"},
            ],
            "observed_effects": [
                "remaining modulus recomputes from the serialized IET model at every recon.E event",
                "a Setveil-only head would have left S-4 in the set overnight",
                "12 min survey floor is in the stream (surv.start, surv.floor)",
            ],
            "surprises": [
                "a clean vendor 48.00 GPa corridor co-existed with a 20.00 GPa plant reconstruction on one setter only",
            ],
            "new_state": {
                "s4": "isolated",
                "s1_s3": "in set",
                "setveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.41,
            [
                ("iet_E_reconstruction", 0.14),
                ("bounded_s4_scope", 0.12),
                ("setveil_nonsubstitution", 0.08),
                ("no_kiln_dump", 0.08),
                ("survey_time_cost", -0.01),
            ],
            "scored for a bounded ACCEPT of S-4 isolate on a recomputable impulse-excitation modulus slip while refusing a Setveil last-good and a kiln dump; 12 min survey is priced as takt not as a reason to skip",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "impulse-excitation-E", "serialized-reconstruction", "operational-companion", "bounded-scope"],
            distillation_value="Independent LIF raster plus serialized k_e*f^2 remaining-modulus reconstruction; race is the 1.5 ms f/SNR pair; refractory and adaptation are in the CUBA excerpt.",
            distillation_note="IET-E gate: serialized k_e*f^2 plus SNR lock beats a vendor last-good; companion t2 is the survey hold, not a dump vote",
        ),
    }
    traj2 = {
        "id": "nelb-r43-a3-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "MH-IET-2026-0902-exec",
            "domain": "remaining_setter_survey_execution",
            "setting": "Same IET-SIM-4 after the ACCEPT. Operator proposes skip-survey because Setveil still shows 47 GPa. This companion is the operational survey hold, not a second modulus vote.",
            "observables_at_decision": {
                "E_GPa": 12.80,
                "surv_floor_s": 720.0,
                "skip_survey_proposed": True,
                "s1_E_GPa": 39.00,
            },
            "margin_authority": "MH-3 execution SOP: remaining-setter survey after an S-4 isolate; skip-survey is forbidden while S-1..S-3 have not been re-measured on the plant IET.",
        },
        "proposed_action": {
            "actor": "sim operator Edda Moss",
            "summary": "skip the remaining-setter survey; Setveil still 47 GPa and S-4 is already isolated",
            "basis_claimed": "the ACCEPT already stopped S-4, so a survey is wasted takt",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Skip-survey is refused. The 12 min survey floor is complete and S-1..S-3 have not been re-measured on the plant IET head. Setveil 47 GPa is not a survey substitute. REJECT skip-survey. Do not dump the kiln. Do not restore S-4 on Setveil. 12.80 GPa post-isolate on S-4 is still the plant SoT until a new frame clears 24.00.",
            "threshold": "survey_hold AND surv_floor_complete AND skip_survey_not_taken AND s1s3_remeasure_required",
            "stated_residuals": "S-4 stays isolated; Setveil still the only OEM IET channel",
        },
        "executed_action": {
            "summary": "survey held at t_s 7800; skip-survey not taken; kiln dump not latched",
            "tool": "mh3-surv-exec",
            "observation": "recon.E 12.80 GPa after isolate; S-1..S-3 still in the survey takt; Setveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "survey clock started after ACCEPT"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7200.0, "event": "skip-survey proposed"},
                {"t_s": 7800.0, "event": "REJECT skip-survey"},
            ],
            "observed_effects": [
                "Setveil restore did not reopen the modulus call",
                "kiln dump never fired; S-1..S-3 stayed in the survey",
            ],
            "surprises": ["post-isolate S-4 dropped to 12.80 GPa while Setveil still read 47 GPa"],
            "new_state": {"survey": "held", "kiln": "in service", "s4": "isolated"},
            "latency_ms": 720000.0,
        },
        "reward_components": reward(
            0.36,
            [
                ("survey_hold", 0.12),
                ("no_kiln_dump", 0.10),
                ("setveil_nonsubstitution", 0.08),
                ("surv_floor_complete", 0.08),
                ("held_takt_cost", -0.02),
            ],
            "operational execution gate: survey-hold because Setveil is not a skip license; not a modulus re-vote",
        ),
        "meta": meta_common(tags=["REJECT", "operational-execution", "survey-hold"]),
    }
    return {
        "id": "nelb-r43-a3",
        "snn_tags": list(SNN_TAGS),
        "spike_events": events,
        "language_view": {
            "description": "Marlholt Kiln MH-3 simulated coupon. Plant-owned impulse-excitation reconstructs 20.00 GPa remaining modulus from 0.050*20.00^2 while Setveil still reports 48.00 GPa. The gate ACCEPTs a bounded S-4 isolate (S-1..S-3 out of scope). A 12 min survey floor is serialized. Companion t2 REJECTs skip-survey.",
            "trajectory": traj,
            "trajectory_survey_hold": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "iet.f / iet.snr": "IET tap frequency and SNR; the physics channels the reconstruction consumes",
                "recon.E / recon.G / recon.f2": "serialized remaining modulus, shear identity, and f^2 identity",
                "s1.E / s2.E / s3.E / setveil.E / set.T": "adjacent-setter out-of-scope witnesses, vendor IET cloud, setter temperature",
                "ops.prop / gate.acc / ops.skip / gate.surv": "S-4 isolate proposal, ACCEPT, skip-survey proposal, companion REJECT",
                "s4.lock / surv.start / surv.floor / surv.held / kiln.dump": "operational companion channels plus the 12 min floor",
            },
            "temporal_motifs": [
                "vendor-healthy while plant-under: setveil.E 48.00 next to recon.E 20.00",
                "reconstruction as event: recon.E 20.00 equals 0.050*20.00^2",
                "ACCEPT then operational REJECT: gate.acc at 4800 s, gate.surv at 7800 s",
                "slow floor in-stream: surv.start 6000 s, surv.floor 6720 s (12.0 min)",
                "tight IET pair: iet.f then iet.snr +1.5 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Setveil is 48 GPa' = setveil.E 48.00; '20 GPa remaining modulus' = recon.E 20.00; 'isolate S-4 only' = gate.acc ACCEPT; 'do not skip survey' = gate.surv REJECT",
            "why_high_value": "New impulse-excitation remaining-modulus family on a kiln setter (not RUS porcelain, not SFRA, not acoustic pyrometry, not bender-element). Lead bounded ACCEPT of S-4 isolate on a recomputable modulus slip that a vendor IET last-good would have left in the set. Independent CUBA LIF raster. Companion t2 is operational survey-hold. sim_or_real=simulated.",
            "encoder_spec": {
                "prng": "CUBA LIF (lif_raster.generate_lif_raster) plus MT19937 amplitudes",
                "seeds": {
                    "raster": 2026090433,
                    "stream_note": "stream amplitudes are authored constants; raster is independent CUBA LIF",
                },
                "draw_order": "independent CUBA LIF full window; 1.5 ms physics pair is stream motif, not excerpt copy",
                "thinning": "IET exists at ~10 Hz; stream keeps 5 f points; recon keeps 5 of ~40 solver ticks",
                "time_alias": "t_rel_ms; t0 = 2026-09-02T03:00:00Z simulated coupon start",
            },
            "distillation_targets": [
                "impulse-excitation reconstruction head: E = k_e * f^2; G = E/(2(1+nu)); f^2 identity",
                "bounded ACCEPT of S-4 vs kiln dump vs skip-survey",
                "vendor-IET nonsubstitution plus adjacent-setter out-of-scope",
                "operational companion: survey-hold without restoring on Setveil",
                "independent CUBA LIF raster with race/refractory/adaptation tags",
            ],
        },
        "reconstruction_model": {
            "name": "impulse_excitation_kiln_setter_E",
            "formula": "E_GPa = k_e * f_kHz^2; G_GPa = E_GPa / (2*(1+nu)); f2 = f_kHz^2",
            "parameters": {
                "k_e": 0.050,
                "nu": 0.25,
                "isolate_floor_GPa": 24.00,
                "dump_GPa": 8.00,
                "snr_lock": 8.0,
                "surv_min": 12.0,
            },
            "worked_example": {"f_kHz": 20.00, "E_GPa": 20.00, "G_GPa": 8.00, "f2": 400.00},
            "check": "0.050 * 20.00^2 = 20.00 exactly; 20.00 / 2.50 = 8.00 exactly; 20.00^2 = 400.00 exactly; 6000 s + 720 s = 6720 s = 12.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 36.0,
            "decision_window_s": 0.036,
            "code": "mh3.iet_setter_gate",
            "note": "ACCEPT accumulator wins: plant IET modulus evidence isolates S-4 without a kiln dump",
            "decode_rule": "accept-S4-isolate if E_estimator AND iet_lock fire; vendor_dump_advocate is below threshold by design",
            "populations": [
                gate_pop("E_estimator", 80, 1.4, 50.0, w_s),
                gate_pop("iet_lock", 50, 1.1, 50.0, w_s),
                gate_pop("vendor_dump_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("accept_latch", 64, 1.5, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "mh3.iet_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 36.0},
                {"check": "mh3.surv_scorer", "neurons": 40, "mean_rate_hz": 62.5, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r43-a3",
            clock_domain="mh3-iet-sim-relative-ms-t0-2026-09-02T03:00:00Z",
            tags=["impulse-excitation-E", "ACCEPT", "REJECT", "serialized-reconstruction", "operational-t2", "independent-lif", "bounded-scope"],
            distillation_value="Independent LIF raster teaches race/refractory/adaptation while the language view teaches impulse-excitation remaining-modulus reconstruction-as-SoT with a bounded ACCEPT.",
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
            if nk == "real":
                hits.append(p)
            if nk == "provenance":
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
        if '"real"' in blob:
            raise RuntimeError("real leaked")
        if rec["meta"]["round"] != ROUND:
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
                if v["meta"]["round"] != ROUND:
                    raise RuntimeError("traj round")
                rc = v["reward_components"]
                skip = {
                    "aggregation",
                    "component_notes",
                    "convention",
                    "frame",
                    "native_unit",
                    "notes",
                    "provenance_notes",
                    "rounding_decimals",
                    "total",
                    "total_basis",
                    "unit_usd",
                    "units",
                    "weights",
                }
                s = sum(val for key, val in rc.items() if key not in skip and isinstance(val, (int, float)) and not isinstance(val, bool))
                if abs(s - rc["total"]) > 1e-9:
                    raise RuntimeError(f"reward {s} != {rc['total']}")
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
        if abs(rast["window_s"] - rast["window_ms"] / 1000.0) > 1e-9:
            raise RuntimeError("window_s")
        ex_us = {e["t_us"] for e in rast["excerpt"]}
        raw_ms_as_us = {int(round(e["t_rel_ms"] * 1000.0)) for e in rec["spike_events"] if e["t_rel_ms"] <= rast["window_ms"]}
        if ex_us & raw_ms_as_us:
            raise RuntimeError("excerpt echoes in-window stream times")
        if "training_ready" in blob:
            raise RuntimeError("training_ready claimed")
        banned_ids = ("nelb-r43-130", "nelb-r43-131", "nelb-r43-132", "Thornveil", "Saltmere", "Greylock")
        for b in banned_ids:
            if b in blob:
                raise RuntimeError(f"leftover collision {b}")
    if len(ids) != len(set(ids)):
        raise RuntimeError(f"dup ids {ids}")
    if len(ids) != 9:
        raise RuntimeError(f"expected 9 ids, got {ids}")
    print("local_checks ok", [r["id"] for r in records], "ids", len(ids))


def write_create_only(path: Path, text: str) -> Path:
    path = Path(path)
    if path.exists():
        raise FileExistsError(f"refuse overwrite {path}")
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(text)
    return path


def main():
    records = [rec_a1(), rec_a2(), rec_a3()]
    local_checks(records)
    STAGING.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(r, ensure_ascii=False, allow_nan=False, separators=(",", ":")) for r in records]
    for line in lines:
        json.loads(line)
    batch_text = "\n".join(lines) + "\n"
    staging_batch = write_create_only(STAGING / BATCH_NAME, batch_text)
    print("staged", staging_batch, staging_batch.stat().st_size)
    print("sha256", hashlib.sha256(batch_text.encode()).hexdigest())
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
