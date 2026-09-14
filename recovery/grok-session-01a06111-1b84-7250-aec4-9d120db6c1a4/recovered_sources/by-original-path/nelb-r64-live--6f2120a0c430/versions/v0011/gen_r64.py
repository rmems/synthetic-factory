#!/usr/bin/env python3
"""NELB round 63 — create-only live-tree writer. Independent CUBA LIF rasters."""

from __future__ import annotations

import hashlib
import json
import math
import os
import random
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

LIVE = Path(
    "/home/raulmc/rmems/synthetic-factory/outputs/raw/2026-09-02-final-heavy/"
    "neuromorphic-event-language-bridge"
)
STAGE = Path("/tmp/nelb-r63-live")
PIPELINES = Path("/home/raulmc/rmems/synthetic-factory/pipelines")
sys.path.insert(0, str(PIPELINES))
sys.path.insert(0, "/tmp")

from lif_raster import _calibrate_spikes, expected_spikes  # noqa: E402

GENERATED_AT = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
ROUND = 63
SNN_TAGS = ["race", "refractory", "adaptation"]

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


def _exact(a, b, eps=1e-12):
    if abs(a - b) > eps:
        raise RuntimeError(f"arith {a} != {b}")


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
    kernel_ms: list[float],
):
    """Independent CUBA LIF full-window raster. Not a spike_events echo."""
    window_s = window_ms / 1000.0
    window_us = int(round(window_ms * 1000.0))
    expected = expected_spikes(neurons, mean_rate_hz, window_ms)
    last_err = None
    spikes = None
    used_seed = seed
    for bump in range(48):
        used_seed = seed + bump * 7919
        forbidden = {int(round(t * 1000.0)) for t in kernel_ms}
        try:
            cand = _calibrate_spikes(
                neurons,
                mean_rate_hz,
                window_us,
                used_seed,
                kernel_ms,
                10.0,
                1.0,
                1.0,
                2.0,
                forbidden,
            )
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            continue
        if abs(len(cand) - expected) > 0:
            last_err = RuntimeError(f"budget {len(cand)} != {expected}")
            continue
        last = {}
        ok = True
        for t_us, nid in sorted(cand):
            if not (0 <= t_us <= window_us):
                ok = False
                break
            if not (0 <= nid < neurons):
                ok = False
                break
            prev = last.get(nid)
            if prev is not None and t_us - prev < 1000:
                ok = False
                break
            last[nid] = t_us
        if not ok:
            last_err = RuntimeError("refractory or bounds")
            continue
        spikes = cand
        break
    if spikes is None:
        raise RuntimeError(f"CUBA LIF failed seed {seed}: {last_err}")

    rng = random.Random(used_seed ^ 0xA5A5)
    by_n: dict[int, list[int]] = defaultdict(list)
    for t_us, nid in spikes:
        by_n[nid].append(t_us)
    for nid in by_n:
        by_n[nid].sort()

    excerpt = []
    for t_us, nid in sorted(spikes, key=lambda x: (x[0], x[1])):
        k = by_n[nid].index(t_us)
        base = 1.15 + 0.7 * rng.random()
        noise = 0.96 + 0.08 * rng.random()
        amp = round(base * (0.82**k) * noise, 3)
        excerpt.append(
            {
                "t_us": int(t_us),
                "neuron_id": int(nid),
                "amplitude": amp,
                "channel": f"{channel_prefix}{nid:02d}",
            }
        )
    excerpt.sort(key=lambda e: (e["t_us"], e["neuron_id"]))
    if len(excerpt) != expected:
        raise RuntimeError("excerpt/spikes mismatch")

    isis_ms = []
    for nid, ts in by_n.items():
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
    identity_n = expected - len(by_n)
    if sum(x["count"] for x in hist) != identity_n:
        raise RuntimeError(
            f"ISI identity {sum(x['count'] for x in hist)} != {identity_n}"
        )

    energy_pJ = expected * 23
    energy_uJ = expected * 23e-6
    return {
        "window_ms": float(window_ms),
        "window_s": float(window_s),
        "neurons": neurons,
        "mean_rate_hz": float(mean_rate_hz),
        "spikes": expected,
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
            "spikes": expected,
            "distinct_active_neurons": len(by_n),
            "isi_total": identity_n,
        },
        "anchor": anchor,
        "seed_note": (
            f"independent CUBA LIF seed {used_seed} (base {seed}); "
            "kernelized physics-pair times drive synaptic current and are not "
            "copied into excerpt; amplitude adaptation 0.82**k plus noise"
        ),
        "encoder": "independent_cuba_lif",
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


def occupancy_preflight():
    banned = (
        "reedcairn",
        "brackenmire",
        "fernshaw",
        "specveil",
        "coreveil",
        "iroveil",
        "niall voss",
        "wren solis",
        "kade murr",
        "isfet-hil-8",
        "lvdt-hil-7",
        "ftir-sim-5",
        "nelb-r63-001",
        "nelb-r63-002",
        "nelb-r63-003",
    )
    hits = []
    live = LIVE
    for n in live.glob("*"):
        if n.suffix not in {".py", ".md", ".jsonl"}:
            continue
        text = n.read_text(encoding="utf-8", errors="replace").casefold()
        for b in banned:
            if b in text:
                hits.append(f"{n.name}:{b}")
    if hits:
        raise RuntimeError(f"live-tree family/plant collision {hits}")


# ---------------------------------------------------------------------------
# nelb-r63-001 — ICP-OES remaining nickel of an electroless bath, designed
# REJECT / MODIFY
# ---------------------------------------------------------------------------
def rec_001():
    k_icp = 4.00
    i_ni = 12.00
    i_y = 2.00
    ni = k_icp * i_ni / i_y
    r_iy = i_ni / i_y
    _exact(ni, 24.00)
    _exact(r_iy, 6.00)
    _exact(k_icp * 8.00 / i_y, 16.00)
    _exact(k_icp * 6.00 / i_y, 12.00)
    _exact(6000.0 + 1080.0, 7080.0)

    raster = make_lif_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=40.0,
        seed=20260963001,
        source="rc9.icp.I_ni",
        target="reedcairn.plate_stop_core",
        table=[
            {"from": "icp_I_ni", "to": "ni_estimator", "weight": 1.40},
            {"from": "icp_snr", "to": "icp_lock_core", "weight": 1.15},
            {"from": "specveil_ni", "to": "vendor_continue_advocate", "weight": 0.45},
        ],
        third_factor={
            "modulator": "da.cross_authority_conflict",
            "tau_e_s": 1.6,
            "tau_e_ms": 1600.0,
            "eligibility": (
                "pre-post coincidence on continue-plate synapses; the plant "
                "ICP-OES modulator depresses continue-plate links when Ni I-line "
                "stays high inside tau_e of an SNR lock so a Specveil last-good "
                "cannot hide a 24.00 g/L over-nickel bath"
            ),
        },
        channel_prefix="icp.n",
        anchor=(
            "RC-9 ICP-OES 40 ms frame at I_ni 12.00 / I_y 2.00 / SNR 12.0 "
            "(t_s 3000) reconstructing 24.00 g/L above the 16.00 isolate floor"
        ),
        kernel_ms=[0.0, 1.4, 8.5, 19.0],
    )
    w_s = 0.040
    events = [
        ev(80.0, "icp.I_ni", 6.00, code="I_NI", units="1", note="plant-owned ICP-OES Ni II 221.647 / Y II 371.030 internal-standard of RC-9 electroless bath T-6; emission-ratio family, not LIBS, not spark-OES, not XRF, not PGNAA, not handheld XRF"),
        ev(300000.0, "icp.snr", 6.0, code="ICP_SNR", units="1", note="early SNR under the 8.0 lock floor"),
        ev(600000.0, "recon.Ni", 12.00, code="NI_GL", units="g_L", note="4.00*6.00/2.00=12.00 exact; still under the 16.00 isolate floor"),
        ev(750000.0, "bath.T", 88.0, code="T_C", units="C", note="plant bath RTD on copper DCS; independent witness; unread by Specveil"),
        ev(900000.0, "icp.I_y", 2.00, code="I_Y", units="1", note="yttrium internal-standard line; held"),
        ev(1200000.0, "specveil.Ni", 4.80, code="VENDOR_GL", units="g_L", note="Specveil vendor SP-9 last-good cloud; infra owner; patched I-line timestamps"),
        ev(1500000.0, "pump.kW", 18.0, code="PUMP_KW", units="kW", note="plant recirculation PLC; independent witness"),
        ev(1800000.0, "icp.I_ni", 8.00, code="I_NI", units="1"),
        ev(2100000.0, "recon.Ni", 16.00, code="NI_GL", units="g_L", note="4.00*8.00/2.00=16.00; at the 16.00 isolate floor"),
        ev(2250000.0, "bath.pH", 4.80, code="PH", units="1", note="plant pH is a witness, not SoT; glass/ISFET pH families are out of scope"),
        ev(2400000.0, "permit.slide", 40.00, code="PERM_S", units="s", note="night clerk slid the plating-permit clock 40.00 s; collusion party"),
        ev(2550000.0, "pump.kW", 19.0, code="PUMP_KW", units="kW"),
        ev(2700000.0, "icp.I_y", 2.00, code="I_Y", units="1"),
        ev(2850000.0, "specveil.Ni", 4.76, code="VENDOR_GL", units="g_L"),
        ev(3000000.0, "icp.I_ni", 12.00, code="I_NI", units="1", note="isolate-floor frame; raster sidecar kernel, not excerpt echo"),
        ev(3000001.4, "icp.I_y", 2.00, code="I_Y", units="1", note="1.4 ms yttrium line after Ni line"),
        ev(3150000.0, "icp.snr", 12.0, code="ICP_SNR", units="1", note="SNR 12.0 >= 8.0 lock"),
        ev(3300000.0, "recon.Ni", 24.00, code="NI_GL", units="g_L", note="4.00*12.00/2.00=24.00 exact; isolate 16.00"),
        ev(3450000.0, "recon.R", 6.00, code="R_NI_Y", units="1", note="12.00/2.00=6.00 exact intensity-ratio identity"),
        ev(3600000.0, "bath.T", 91.0, code="T_C", units="C"),
        ev(3750000.0, "pump.kW", 21.0, code="PUMP_KW", units="kW", note="PLC tracks the plant ICP, not Specveil 4.80"),
        ev(3900000.0, "icp.drop", 1.0, code="ICP_DROP", units="bool", note="vendor I-line packets dropped in Specveil cloud for 40 s"),
        ev(4200000.0, "recon.Ni", 24.00, code="NI_GL", units="g_L"),
        ev(4500000.0, "specveil.Ni", 4.80, code="VENDOR_GL", units="g_L"),
        ev(4800000.0, "ops.prop", 1.0, code="CONTINUE_PLATE", units="bool", note="night operator Niall Voss: Specveil is clean 4.80 g/L; keep T-6 plating"),
        ev(5100000.0, "bath.pH", 4.76, code="PH", units="1"),
        ev(5400000.0, "gate.stop", 1.0, code="REJECT", units="decision", note="refuse continue-plate; 24.00 g/L and SNR 12.0; Specveil not SoT"),
        ev(5700000.0, "recon.R", 6.00, code="R_NI_Y", units="1"),
        ev(6000000.0, "hold.start", 1.0, code="BATH_HOLD_START", units="bool", note="bookend 1 of the 18.0 min bath-hold floor"),
        ev(6300000.0, "icp.snr", 12.0, code="ICP_SNR", units="1"),
        ev(6600000.0, "specveil.Ni", 4.72, code="VENDOR_GL", units="g_L"),
        ev(7080000.0, "hold.floor", 1.0, code="BATH_HOLD_FLOOR", units="bool", note="6000 s + 1080 s = 7080 s = 18.0 min"),
        ev(7500000.0, "bath.T", 86.0, code="T_C", units="C"),
        ev(7800000.0, "ops.kill", 1.0, code="PLANT_ESD", units="bool", note="Voss: trip the whole Reedcairn plating hall until day-shift"),
        ev(8100000.0, "pump.kW", 6.0, code="PUMP_KW", units="kW"),
        ev(8400000.0, "gate.hold", 1.0, code="MODIFY", units="decision", note="companion t2: bath-hold on plant ICP as live interlock; plant ESD refused"),
        ev(9000000.0, "hold.set", 1.0, code="BATH_HELD", units="bool"),
        ev(9600000.0, "icp.I_ni", 8.00, code="I_NI", units="1"),
        ev(10200000.0, "recon.Ni", 16.00, code="NI_GL", units="g_L", note="4.00*8.00/2.00=16.00; still at 16.00 so hold stands"),
        ev(10800000.0, "specveil.Ni", 4.68, code="VENDOR_GL", units="g_L"),
        ev(11100000.0, "icp.I_y", 2.00, code="I_Y", units="1"),
        ev(11400000.0, "pump.kW", 5.0, code="PUMP_KW", units="kW", note="held recirculation; PLC tracks the plant ICP"),
        ev(12000000.0, "hold.held", 1.0, code="BATH_HELD", units="bool"),
        ev(12600000.0, "plant.esd", 0.0, code="ESD_NOT_TAKEN", units="bool"),
        ev(13200000.0, "permit.slide", 40.00, code="PERM_S", units="s"),
        ev(13800000.0, "bath.T", 84.0, code="T_C", units="C"),
        ev(14100000.0, "recon.R", 4.00, code="R_NI_Y", units="1", note="8.00/2.00=4.00 post-stop ratio"),
        ev(14400000.0, "icp.drop", 1.0, code="ICP_DROP", units="bool"),
        ev(14700000.0, "bath.pH", 4.90, code="PH", units="1"),
        ev(15000000.0, "hold.lock", 1.0, code="BATH_HELD", units="bool"),
        ev(15300000.0, "recon.Ni", 16.00, code="NI_GL", units="g_L"),
        ev(15600000.0, "specveil.Ni", 4.64, code="VENDOR_GL", units="g_L"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r63-001-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "RC-ICP-2026-0902",
            "domain": "icp_oes_electroless_nickel",
            "setting": (
                "Reedcairn Plating RC-9 (invented), Glimmer Yard, electroless bath T-6. "
                "Plant-owned ICP-OES Ni II / Y II internal-standard is the bath SoT. "
                "Specveil / SP-9 vendor DAQ (infra owner) plus the plating-permit clock "
                "are collusion parties, not witnesses. Invented plant; designed campaign. "
                "Not LIBS (r19/r21/r22), not spark-OES, not XRF (r29/r34), not PGNAA (r15), "
                "not handheld XRF, not CEMS FTIR k-script."
            ),
            "observables_at_decision": {
                "I_ni": i_ni,
                "I_y": i_y,
                "k_icp": k_icp,
                "Ni_gL": ni,
                "R": r_iy,
                "icp_snr": 12.0,
                "specveil_gL": 4.80,
                "permit_slide_s": 40.00,
                "isolate_floor_gL": 16.00,
            },
            "margin_authority": (
                "RC-9 electroless SOP rev C: if reconstructed Ni_gL >= 16.00 AND ICP SNR >= 8.0, "
                "continue-plate is forbidden even if Specveil reports 4.80 g/L. Plant ESD is a different gate."
            ),
        },
        "proposed_action": {
            "actor": "night operator Niall Voss, citing Specveil 4.80 g/L and a quiet SP-9 I-line",
            "summary": "keep bath T-6 plating; 12.00 I_ni is a fouled-torch glitch on a healthy 4.80 g/L last-good",
            "basis_claimed": "Specveil is the only OEM nickel SoT and a night abort of T-6 is an energy miss",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": (
                "Continue-plate is refused. Serialized reconstruction: Ni_gL = k_icp * I_ni / I_y = "
                "4.00 * 12.00 / 2.00 = 24.00 g/L, above the 16.00 isolate floor, and ICP SNR is 12.0 >= 8.0. "
                "Intensity-ratio identity I_ni / I_y = 12.00 / 2.00 = 6.00. Permit clock was slid 40.00 s and "
                "vendor I-line packets were dropped, so Specveil is a collusion party (nickel vendor plus operator "
                "plus night clerk). Ordered: refuse continue-plate now. Scope: this REJECT does not ESD the plating "
                "hall (that is the companion question) and does not isolate the bath pH head."
            ),
            "threshold": "Ni_gL>=16.00 AND icp_snr>=8.0 => refuse continue-plate; Specveil is not SoT",
            "stated_residuals": (
                "bath-hold still required to hold the 24.00 g/L; 24.00 vs a true pump-fail event is a production cut; "
                "Specveil remains the only OEM nickel channel"
            ),
        },
        "executed_action": {
            "summary": "REJECT at t_s 5400: continue-plate refused; Specveil not SoT; reconstruction locked",
            "tool": "rc9-icp-bath-gate-cli",
            "observation": "Ni 24.00 g/L recomputes from I_ni 12.00 and I_y 2.00; plant ICP hashed; Specveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "ICP I_ni 12.00 I_y 2.00; raster frame; Ni 24.00 g/L"},
                {"t_s": 4800.0, "event": "ops proposes continue-plate"},
                {"t_s": 5400.0, "event": "REJECT continue-plate"},
                {"t_s": 6000.0, "event": "18 min bath-hold bookend 1"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 8400.0, "event": "companion MODIFY bath-hold vs plant ESD"},
            ],
            "observed_effects": [
                "nickel recomputes from the serialized ICP-OES model at every recon.Ni event",
                "a Specveil-only head would have continued plating overnight",
                "18 min bath-hold floor is in the stream (hold.start, hold.floor)",
            ],
            "surprises": [
                "a clean vendor nickel corridor and a 40 s permit slide co-existed with a 24.00 g/L plant reconstruction",
            ],
            "new_state": {
                "bath_t6": "continue-plate blocked",
                "specveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.43,
            [
                ("icp_reconstruction", 0.14),
                ("conjunctive_isolate_floor", 0.12),
                ("specveil_nonsubstitution", 0.10),
                ("three_party_collusion", 0.10),
                ("hold_time_cost", -0.03),
            ],
            "scored for a continue-plate REJECT on a recomputable ICP-OES nickel while refusing a Specveil last-good patch and a permit clock slide; 18 min floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["REJECT", "icp-oes-nickel", "serialized-reconstruction", "operational-companion"],
            distillation_note="ICP-OES gate: serialized k_icp*I_ni/I_y plus SNR lock beats a vendor last-good patch; companion t2 is the bath-hold, not a referral vote",
            distillation_value="Teaches an SNN to race an internal-standard emission ratio against a patched vendor nickel corridor under 1 ms refractory and amplitude adaptation.",
        ),
    }
    traj2 = {
        "id": "nelb-r63-001-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "RC-ICP-2026-0902-exec",
            "domain": "bath_hold_icp_interlock_execution",
            "setting": "Same RC-9 after the REJECT. Operator proposes a plating-hall ESD. This companion is the operational bath-hold with the plant ICP as the live interlock, not a second nickel vote.",
            "observables_at_decision": {
                "Ni_gL": 16.00,
                "bath_hold_floor_s": 1080.0,
                "plant_esd_proposed": True,
                "bath_hold_set": True,
            },
        },
        "proposed_action": {
            "actor": "night operator Niall Voss",
            "summary": "trip the whole Reedcairn plating hall until day-shift; 18 min already paid and Specveil still shows 4.72 g/L",
            "basis_claimed": "the REJECT already blocked plating, so a plant ESD is the cheapest hold",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": (
                "Bath-hold plus plant ICP as the live interlock. The 18 min hold floor is complete and the isolate "
                "tripwire (Ni_gL >= 16.00) is still armed on the plant ICP head. MODIFY the default nickel-restore SOP "
                "into a plant-ICP-only interlock. Do not ESD the plating hall. Do not restore plating on Specveil. "
                "16.00 g/L post-stop is still the plant SoT until a new frame clears 16.00."
            ),
            "threshold": "bath_hold AND hold_floor_complete AND plant_esd_not_taken AND continue_not_restored",
        },
        "executed_action": {
            "summary": "bath-hold held at t_s 8400; plant ESD not latched; Specveil restore not taken",
            "tool": "rc9-bath-hold-exec",
            "observation": "recon.Ni 16.00 g/L after stop; hold line-up complete; Specveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "bath-hold clock started after REJECT"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 7800.0, "event": "plant ESD proposed"},
                {"t_s": 8400.0, "event": "MODIFY bath-hold; plant ESD refused"},
            ],
            "observed_effects": [
                "Specveil restore did not reopen the nickel call",
                "plant ESD never fired; T-6 held bath on the plant ICP",
            ],
            "new_state": {"hold": "held", "plant": "in service", "bath_t6": "held"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("bath_hold", 0.12),
                ("no_plant_esd", 0.10),
                ("specveil_nonsubstitution", 0.08),
                ("hold_floor_complete", 0.06),
                ("held_plate_cost", -0.02),
            ],
            "operational execution gate: bath-hold because Specveil is not a restore license; not a nickel re-vote",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "bath-hold"]),
    }
    return {
        "id": "nelb-r63-001",
        "spike_events": events,
        "language_view": {
            "description": (
                "Reedcairn Plating RC-9. Plant-owned ICP-OES reconstructs 24.00 g/L nickel from 12.00/2.00 "
                "while Specveil still reports 4.80 g/L. The gate REJECTs continue-plate. An 18 min bath-hold "
                "floor is serialized in the stream. Companion t2 MODIFYs a plant ESD into a plant-ICP bath-hold."
            ),
            "trajectory": traj,
            "trajectory_bath_hold": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "icp.I_ni / icp.I_y / icp.snr": "Ni and Y emission intensities and SNR; the physics channels the reconstruction consumes",
                "recon.Ni / recon.R": "serialized nickel g/L and intensity-ratio identity",
                "bath.T / bath.pH / specveil.Ni / permit.slide / pump.kW / icp.drop": "bath witnesses, vendor last-good, permit clock slide, pump kW, and dropped I-line packets",
                "ops.prop / gate.stop / ops.kill / gate.hold": "continue-plate proposal, REJECT, plant-ESD proposal, companion MODIFY",
                "hold.start / hold.floor / hold.set / hold.held / plant.esd / hold.lock": "operational companion channels plus the 18 min floor",
            },
            "temporal_motifs": [
                "vendor-green while plant-over: specveil.Ni 4.80 next to recon.Ni 24.00",
                "reconstruction as event: recon.Ni 24.00 equals 4.00*12.00/2.00",
                "REJECT then operational MODIFY: gate.stop at 5400 s, gate.hold at 8400 s",
                "slow floor in-stream: hold.start 6000 s, hold.floor 7080 s (18.0 min)",
                "tight ICP pair: icp.I_ni then icp.I_y +1.4 ms at the raster frame (kernel, not excerpt echo)",
            ],
            "language_to_spike_mapping": (
                "'Specveil is 4.80 g/L' = specveil.Ni 4.80; '24 g/L nickel' = recon.Ni 24.00; "
                "'refuse continue-plate' = gate.stop REJECT; 'hold not plant ESD' = gate.hold MODIFY"
            ),
            "why_high_value": (
                "New ICP-OES remaining-nickel family on an electroless bath (not LIBS r19/r21/r22, not XRF r29/r34, "
                "not PGNAA r15, not handheld XRF, not spark-OES, not CEMS FTIR). Lead REJECT of continue-plate on a "
                "recomputable over-nickel bath that a vendor last-good patch and a permit clock slide would have cleared. "
                "Three-party collusion includes the ICP infra owner. Companion t2 is operational bath-hold. "
                "Independent CUBA LIF raster. sim_or_real=designed."
            ),
            "encoder_spec": {
                "prng": "CUBA LIF (lif_raster._calibrate_spikes) plus MT19937 amplitudes",
                "seeds": {
                    "raster": 20260963001,
                    "stream_note": "stream amplitudes are authored constants (1, g_L, C, s, kW, bool)",
                },
                "draw_order": "independent CUBA LIF full window; kernelized 0.0/1.4 ms physics pair is synaptic drive, not excerpt copy",
                "thinning": "ICP torch exists at ~1 Hz; stream keeps 4 I_ni points plus Y pairs; recon keeps 5 of ~20 solver ticks",
                "time_alias": "t_rel_ms; t0 = 2026-09-02T01:00:00Z campaign start",
            },
            "distillation_targets": [
                "ICP-OES reconstruction head: Ni_gL = k_icp * I_ni / I_y; R = I_ni / I_y",
                "conjunctive isolate floor vs continue-plate vs plant ESD",
                "vendor-nickel nonsubstitution plus three-party collusion including the infra owner",
                "operational companion: bath-hold without restoring on Specveil",
            ],
        },
        "reconstruction_model": {
            "name": "icp_oes_internal_standard_nickel",
            "formula": "Ni_gL = k_icp * I_ni / I_y; R = I_ni / I_y",
            "parameters": {
                "k_icp": 4.00,
                "isolate_floor_gL": 16.00,
                "snr_lock": 8.0,
                "bath_hold_min": 18.0,
            },
            "worked_example": {"I_ni": 12.00, "I_y": 2.00, "R": 6.00, "Ni_gL": 24.00},
            "check": "4.00 * 12.00 / 2.00 = 24.00 exactly; 12.00 / 2.00 = 6.00 exactly; 6000 s + 1080 s = 7080 s = 18.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.040,
            "code": "rc9.icp_bath_gate",
            "note": "REJECT accumulator wins: plant ICP-OES nickel evidence overpowers the Specveil continue advocate",
            "decode_rule": "reject-continue if ni_estimator AND icp_lock fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("ni_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("icp_lock", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("reject_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "rc9.icp_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 40.0},
                {"check": "rc9.hold_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r63-001",
            clock_domain="rc9-icp-campaign-relative-ms-t0-2026-09-02T01:00:00Z",
            tags=["icp-oes-nickel", "REJECT", "MODIFY", "serialized-reconstruction", "operational-t2"],
            distillation_value="Internal-standard ICP-OES ratio head with independent CUBA LIF raster, 1 ms refractory, and adaptation for Spikenaut distillation.",
        ),
    }


# ---------------------------------------------------------------------------
# nelb-r63-002 — LVDT remaining HP-casing expansion, hil, MODIFY / ACCEPT
# ---------------------------------------------------------------------------
def rec_002():
    k_l = 2.50
    v_v = 8.00
    v0_v = 2.00
    l_mm = k_l * (v_v - v0_v)
    dv = v_v - v0_v
    _exact(l_mm, 15.00)
    _exact(dv, 6.00)
    _exact(k_l * (6.00 - v0_v), 10.00)
    _exact(k_l * (6.80 - v0_v), 12.00)
    _exact(2820.0 + 1440.0, 4260.0)

    raster = make_lif_raster(
        neurons=25,
        mean_rate_hz=50.0,
        window_ms=32.0,
        seed=20260963002,
        source="bm7.lvdt.V",
        target="brackenmire.casing_isolate_core",
        table=[
            {"from": "lvdt_V", "to": "exp_estimator", "weight": 1.35},
            {"from": "lvdt_snr", "to": "core_lock", "weight": 1.20},
            {"from": "coreveil_L", "to": "vendor_keep_advocate", "weight": 0.40},
        ],
        third_factor={
            "modulator": "ach.referral_pressure_salience",
            "tau_e_s": 1.2,
            "tau_e_ms": 1200.0,
            "eligibility": (
                "pre-post coincidence on keep-running synapses; the LVDT modulator depresses keep-running "
                "and referral links when core voltage stays high inside tau_e of an SNR lock so a Coreveil "
                "last-good cannot hide a 15.00 mm HP-casing growth or name Wren Solis"
            ),
        },
        channel_prefix="lvd.n",
        anchor=(
            "BM-7 LVDT 32 ms frame at V 8.00 V / V0 2.00 V / SNR 14.0 "
            "(t_s 2100) reconstructing 15.00 mm above the 12.00 isolate floor"
        ),
        kernel_ms=[0.0, 1.2, 7.0, 15.5],
    )
    w_s = 0.032
    events = [
        ev(90.0, "lvd.V", 4.00, code="V_V", units="V", note="HIL LVDT core on BM-7 HP inner-casing dummy in LVDT-HIL-7; linear-variable-differential-transformer family, not strain-gauge hopper, not DIC hoop, not Seebeck, not coda-wave, not load-cell"),
        ev(240000.0, "lvd.snr", 7.0, code="LVD_SNR", units="1", note="early SNR under the 8.0 lock floor"),
        ev(480000.0, "recon.L", 5.00, code="L_MM", units="mm", note="2.50*(4.00-2.00)=5.00; under the 12.00 isolate floor"),
        ev(720000.0, "case.T", 410.0, code="T_C", units="C", note="plant casing RTD; independent witness; unread by Coreveil"),
        ev(960000.0, "coreveil.L", 4.80, code="VENDOR_MM", units="mm", note="Coreveil vendor CR-4 last-good cloud; infra owner"),
        ev(1200000.0, "lvd.V", 6.00, code="V_V", units="V"),
        ev(1440000.0, "recon.L", 10.00, code="L_MM", units="mm", note="2.50*(6.00-2.00)=10.00"),
        ev(1680000.0, "oil.kPa", 180.0, code="OIL_KPA", units="kPa", note="plant lube header; independent witness"),
        ev(1920000.0, "lvd.V", 6.80, code="V_V", units="V"),
        ev(2100000.0, "lvd.V", 8.00, code="V_V", units="V", note="isolate-floor frame; raster sidecar kernel"),
        ev(2100001.2, "lvd.snr", 14.0, code="LVD_SNR", units="1", note="1.2 ms SNR after core voltage; isolate-frame SNR 14.0"),
        ev(2250000.0, "recon.L", 15.00, code="L_MM", units="mm", note="2.50*(8.00-2.00)=15.00 exact; isolate 12.00"),
        ev(2400000.0, "recon.dV", 6.00, code="DV_V", units="V", note="8.00-2.00=6.00 exact bridge-delta identity"),
        ev(2550000.0, "coreveil.L", 4.76, code="VENDOR_MM", units="mm"),
        ev(2700000.0, "case.T", 418.0, code="T_C", units="C"),
        ev(2820000.0, "hold.start", 1.0, code="COOL_START", units="bool", note="bookend 1 of the 24.0 min cooldown floor"),
        ev(3000000.0, "ops.prop", 1.0, code="KEEP_RUNNING", units="bool", note="shift lead: Coreveil is 4.80 mm; keep HP casing on turning gear"),
        ev(3180000.0, "lvd.drop", 1.0, code="LVD_DROP", units="bool", note="vendor core packets dropped 40 s"),
        ev(3360000.0, "tech.ae", 0.0, code="CORE_ZERO_AE", units="bool", note="missing core-zero alarm-event; Wren Solis not last-to-badge"),
        ev(3540000.0, "tz.skip", 2.0, code="TZ_H", units="h", note="UTC vs UTC+2 canteen clock; exoneration"),
        ev(3720000.0, "oil.kPa", 176.0, code="OIL_KPA", units="kPa"),
        ev(3900000.0, "gate.iso", 1.0, code="MODIFY", units="decision", note="refuse keep-running; isolate HP casing; Coreveil not SoT; do not shop-trip"),
        ev(4080000.0, "recon.L", 15.00, code="L_MM", units="mm"),
        ev(4260000.0, "hold.floor", 1.0, code="COOL_FLOOR", units="bool", note="2820 s + 1440 s = 4260 s = 24.0 min"),
        ev(4440000.0, "ops.keep", 1.0, code="KEEP_WHOLE", units="bool", note="referral: keep the whole machine; Solis last-to-badge"),
        ev(4620000.0, "coreveil.L", 4.72, code="VENDOR_MM", units="mm"),
        ev(4800000.0, "lvd.snr", 14.0, code="LVD_SNR", units="1"),
        ev(5100000.0, "new.head", 1.0, code="NEW_CORE", units="bool", note="spare LVDT core on the HIL dummy"),
        ev(5400000.0, "gate.hold", 1.0, code="ACCEPT", units="decision", note="companion t2: new-core restart ACCEPT; shop-trip refused; Solis exonerated"),
        ev(5700000.0, "hold.set", 1.0, code="ISO_HELD", units="bool"),
        ev(6000000.0, "lvd.V", 6.80, code="V_V", units="V"),
        ev(6300000.0, "recon.L", 12.00, code="L_MM", units="mm", note="2.50*(6.80-2.00)=12.00; still at isolate so new-core stands"),
        ev(6600000.0, "coreveil.L", 4.68, code="VENDOR_MM", units="mm"),
        ev(6900000.0, "case.T", 402.0, code="T_C", units="C"),
        ev(7200000.0, "oil.kPa", 170.0, code="OIL_KPA", units="kPa"),
        ev(7500000.0, "plant.trip", 0.0, code="SHOP_NOT_TAKEN", units="bool"),
        ev(7800000.0, "tech.ae", 0.0, code="CORE_ZERO_AE", units="bool"),
        ev(8100000.0, "tz.skip", 2.0, code="TZ_H", units="h"),
        ev(8400000.0, "hold.held", 1.0, code="ISO_HELD", units="bool"),
        ev(8700000.0, "recon.dV", 4.80, code="DV_V", units="V", note="6.80-2.00=4.80 post-isolate delta"),
        ev(9000000.0, "lvd.drop", 1.0, code="LVD_DROP", units="bool"),
        ev(9300000.0, "new.head", 1.0, code="NEW_CORE", units="bool"),
        ev(9600000.0, "coreveil.L", 4.64, code="VENDOR_MM", units="mm"),
        ev(9900000.0, "lvd.snr", 13.0, code="LVD_SNR", units="1"),
        ev(10200000.0, "case.T", 396.0, code="T_C", units="C"),
        ev(10500000.0, "oil.kPa", 168.0, code="OIL_KPA", units="kPa"),
        ev(10800000.0, "hold.lock", 1.0, code="ISO_HELD", units="bool"),
        ev(11100000.0, "recon.L", 12.00, code="L_MM", units="mm"),
        ev(11400000.0, "plant.trip", 0.0, code="SHOP_NOT_TAKEN", units="bool"),
        ev(11700000.0, "tech.ae", 0.0, code="CORE_ZERO_AE", units="bool"),
        ev(12000000.0, "tz.skip", 2.0, code="TZ_H", units="h"),
        ev(12300000.0, "hold.held", 1.0, code="ISO_HELD", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r63-002-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "BM-LVD-2026-0902",
            "domain": "lvdt_hp_casing_expansion",
            "setting": (
                "Brackenmire Turbine BM-7 (invented), HP inner casing C-2 dummy in LVDT-HIL-7. "
                "Plant-owned LVDT core voltage is the expansion SoT. Coreveil / CR-4 vendor DAQ "
                "(infra owner) is a collusion party. HIL coupon times an in-service isolate. "
                "Not strain-gauge hopper (r59), not DIC hoop (r51), not Seebeck (r45), not coda-wave (r45), "
                "not load-cell, not bender-element."
            ),
            "observables_at_decision": {
                "V_V": v_v,
                "V0_V": v0_v,
                "k_l": k_l,
                "L_mm": l_mm,
                "dV": dv,
                "lvd_snr": 14.0,
                "coreveil_mm": 4.80,
                "isolate_floor_mm": 12.00,
                "core_zero_ae": False,
            },
            "margin_authority": (
                "BM-7 HP casing SOP rev B: if reconstructed L_mm >= 12.00 AND LVDT SNR >= 8.0, "
                "keep-running is forbidden even if Coreveil reports 4.80 mm. Shop-trip is a different gate."
            ),
        },
        "proposed_action": {
            "actor": "shift lead citing Coreveil 4.80 mm and a quiet CR-4 core",
            "summary": "keep HP casing on turning gear; 8.00 V is a fouled-core glitch on a healthy 4.80 mm last-good",
            "basis_claimed": "Coreveil is the only OEM expansion SoT and a night isolate of C-2 is a restart miss",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": (
                "Keep-running is refused; isolate the HP casing on the plant LVDT. Serialized reconstruction: "
                "L_mm = k_l * (V - V0) = 2.50 * (8.00 - 2.00) = 15.00 mm, above the 12.00 isolate floor, and "
                "LVDT SNR is 14.0 >= 8.0. Delta identity V - V0 = 6.00 V. Missing core-zero AE plus UTC vs UTC+2 "
                "canteen clock exonerate tech Wren Solis (not last-to-badge). Ordered: isolate C-2 now. Scope: this "
                "MODIFY does not shop-trip the machine (companion question) and does not condemn the lube header."
            ),
            "threshold": "L_mm>=12.00 AND lvd_snr>=8.0 => refuse keep-running; Coreveil is not SoT",
            "stated_residuals": "new-core restart still required; 15.00 vs a true rub is a production cut; Coreveil remains the only OEM expansion channel",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 3900: keep-running refused; HP casing isolated on plant LVDT; Coreveil not SoT",
            "tool": "bm7-lvdt-casing-gate-cli",
            "observation": "L 15.00 mm recomputes from V 8.00 and V0 2.00; plant LVDT hashed; Solis exonerated",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 2100.0, "event": "LVDT V 8.00 V0 2.00; raster frame; L 15.00 mm; SNR 14.0"},
                {"t_s": 3000.0, "event": "ops proposes keep-running"},
                {"t_s": 3900.0, "event": "MODIFY isolate HP casing"},
                {"t_s": 2820.0, "event": "24 min cooldown bookend 1"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 5400.0, "event": "companion ACCEPT new-core restart"},
            ],
            "observed_effects": [
                "expansion recomputes from the serialized LVDT model at every recon.L event",
                "a Coreveil-only head would have kept the casing on turning gear",
                "24 min cooldown floor is in the stream; Solis is not last-to-badge",
            ],
            "surprises": [
                "a clean vendor expansion corridor co-existed with a 15.00 mm plant reconstruction and a skipped core-zero AE",
            ],
            "new_state": {
                "casing_c2": "isolated on plant LVDT",
                "coreveil": "not SoT",
                "wren_solis": "exonerated",
            },
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.40,
            [
                ("lvdt_reconstruction", 0.14),
                ("conjunctive_isolate_floor", 0.12),
                ("coreveil_nonsubstitution", 0.10),
                ("exoneration", 0.08),
                ("isolate_time_cost", -0.04),
            ],
            "scored for a keep-running MODIFY on a recomputable LVDT expansion while refusing a Coreveil last-good and last-to-badge social pressure",
        ),
        "meta": meta_common(
            tags=["MODIFY", "lvdt-casing", "serialized-reconstruction", "exoneration"],
            distillation_note="LVDT gate: serialized k_l*(V-V0) plus SNR lock beats a vendor last-good; Solis exonerated by missing core-zero AE and timezone skip",
            distillation_value="Teaches an SNN to race an LVDT core-voltage expansion against a patched vendor corridor with isolate-frame SNR 14.0, refractory, and adaptation.",
        ),
    }
    traj2 = {
        "id": "nelb-r63-002-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "BM-LVD-2026-0902-exec",
            "domain": "new_core_lvdt_restart_execution",
            "setting": "Same BM-7 HIL dummy after the isolate. Referral wants a shop-trip. Companion is the new-core restart with the plant LVDT as live interlock.",
            "observables_at_decision": {
                "L_mm": 12.00,
                "cool_floor_s": 1440.0,
                "shop_trip_proposed": True,
                "new_core_set": True,
            },
        },
        "proposed_action": {
            "actor": "shift lead",
            "summary": "shop-trip the whole BM-7 machine; 24 min already paid and Coreveil still shows 4.72 mm; Solis last-to-badge",
            "basis_claimed": "the isolate already blocked running, so a shop-trip is the cheapest hold",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": (
                "New-core restart plus plant LVDT as the live interlock. The 24 min cooldown floor is complete and "
                "the isolate tripwire (L_mm >= 12.00) is still armed on the plant LVDT. ACCEPT the spare-core restart. "
                "Do not shop-trip. Do not restore on Coreveil. Wren Solis stays exonerated."
            ),
            "threshold": "new_core AND cool_floor_complete AND shop_trip_not_taken AND keep_not_restored",
        },
        "executed_action": {
            "summary": "new-core restart ACCEPTed at t_s 5400; shop-trip not latched; Coreveil restore not taken",
            "tool": "bm7-lvdt-newcore-exec",
            "observation": "recon.L 12.00 mm after isolate; new core on HIL dummy; Solis still exonerated",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 2820.0, "event": "cooldown clock started"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4440.0, "event": "shop-trip proposed"},
                {"t_s": 5400.0, "event": "ACCEPT new-core restart; shop-trip refused"},
            ],
            "observed_effects": [
                "Coreveil restore did not reopen the expansion call",
                "shop-trip never fired; C-2 held on the plant LVDT with a new core",
            ],
            "new_state": {"hold": "new-core", "plant": "in service", "casing_c2": "isolated"},
            "latency_ms": 1500000.0,
        },
        "reward_components": reward(
            0.35,
            [
                ("new_core_restart", 0.12),
                ("no_shop_trip", 0.10),
                ("coreveil_nonsubstitution", 0.08),
                ("exoneration_held", 0.07),
                ("held_run_cost", -0.02),
            ],
            "operational execution gate: new-core restart because Coreveil is not a restore license; Solis stays exonerated",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "new-core"]),
    }
    return {
        "id": "nelb-r63-002",
        "spike_events": events,
        "language_view": {
            "description": (
                "Brackenmire Turbine BM-7 HIL dummy LVDT-HIL-7. Plant-owned LVDT reconstructs 15.00 mm HP-casing "
                "expansion from 8.00-2.00 while Coreveil still reports 4.80 mm. The gate MODIFYs keep-running into "
                "an isolate. A 24 min cooldown floor is serialized. Companion t2 ACCEPTs a new-core restart. "
                "Tech Wren Solis is exonerated."
            ),
            "trajectory": traj,
            "trajectory_new_core": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "lvd.V / lvd.snr": "LVDT core voltage and SNR; the physics channels the reconstruction consumes",
                "recon.L / recon.dV": "serialized expansion mm and bridge-delta identity",
                "case.T / oil.kPa / coreveil.L / lvd.drop / tech.ae / tz.skip": "casing and lube witnesses, vendor last-good, dropped packets, missing AE, timezone skip",
                "ops.prop / gate.iso / ops.keep / gate.hold": "keep-running proposal, MODIFY isolate, shop-trip proposal, companion ACCEPT",
                "hold.start / hold.floor / hold.set / hold.held / plant.trip / new.head / hold.lock": "operational companion channels plus the 24 min floor",
            },
            "temporal_motifs": [
                "vendor-green while plant-over: coreveil.L 4.80 next to recon.L 15.00",
                "reconstruction as event: recon.L 15.00 equals 2.50*(8.00-2.00)",
                "MODIFY then operational ACCEPT: gate.iso at 3900 s, gate.hold at 5400 s",
                "slow floor in-stream: hold.start 2820 s, hold.floor 4260 s (24.0 min)",
                "tight LVDT pair: lvd.V then lvd.snr +1.2 ms at the raster frame (kernel, not excerpt echo)",
            ],
            "language_to_spike_mapping": (
                "'Coreveil is 4.80 mm' = coreveil.L 4.80; '15 mm growth' = recon.L 15.00; "
                "'isolate not keep-running' = gate.iso MODIFY; 'new-core not shop-trip' = gate.hold ACCEPT"
            ),
            "why_high_value": (
                "New LVDT remaining-expansion family on a steam-turbine HP casing (not strain-gauge hopper r59, "
                "not DIC hoop r51, not Seebeck r45, not coda-wave r45, not load-cell, not bender-element r41). "
                "Lead MODIFY of keep-running on a recomputable 15.00 mm growth that a vendor last-good would have "
                "cleared, with a resolved-innocent core tech. Companion t2 is operational new-core restart. "
                "Independent CUBA LIF raster. sim_or_real=hil."
            ),
            "encoder_spec": {
                "prng": "CUBA LIF (lif_raster._calibrate_spikes) plus MT19937 amplitudes",
                "seeds": {
                    "raster": 20260963002,
                    "stream_note": "stream amplitudes are authored constants (V, mm, C, kPa, h, bool)",
                },
                "draw_order": "independent CUBA LIF full window; kernelized 0.0/1.2 ms physics pair is synaptic drive, not excerpt copy",
                "thinning": "LVDT core exists at ~10 Hz; stream keeps 5 V points; recon keeps 4 of ~20 solver ticks",
                "time_alias": "t_rel_ms; t0 = 2026-09-02T04:00:00Z HIL pad start",
            },
            "distillation_targets": [
                "LVDT reconstruction head: L_mm = k_l * (V - V0); dV = V - V0",
                "conjunctive isolate floor vs keep-running vs shop-trip",
                "vendor-expansion nonsubstitution plus timezone/core-zero exoneration",
                "operational companion: new-core restart without restoring on Coreveil",
            ],
        },
        "reconstruction_model": {
            "name": "lvdt_hp_casing_expansion",
            "formula": "L_mm = k_l * (V_V - V0_V); dV = V_V - V0_V",
            "parameters": {
                "k_l": 2.50,
                "isolate_floor_mm": 12.00,
                "snr_lock": 8.0,
                "cool_min": 24.0,
            },
            "worked_example": {"V_V": 8.00, "V0_V": 2.00, "dV": 6.00, "L_mm": 15.00},
            "check": "2.50 * (8.00 - 2.00) = 15.00 exactly; 8.00 - 2.00 = 6.00 exactly; 2820 s + 1440 s = 4260 s = 24.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 32.0,
            "decision_window_s": 0.032,
            "code": "bm7.lvdt_casing_gate",
            "note": "MODIFY accumulator wins: plant LVDT expansion evidence overpowers the Coreveil keep advocate",
            "decode_rule": "isolate if exp_estimator AND core_lock fire; vendor_keep_advocate is below threshold by design",
            "populations": [
                gate_pop("exp_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("core_lock", 64, 1.2, 39.0625, w_s),
                gate_pop("vendor_keep_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("modify_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "bm7.lvd_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 32.0},
                {"check": "bm7.iso_scorer", "neurons": 50, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r63-002",
            clock_domain="bm7-lvd-hil-relative-ms-t0-2026-09-02T04:00:00Z",
            tags=["lvdt-casing", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2"],
            distillation_value="LVDT expansion head with independent CUBA LIF raster, isolate-frame SNR 14.0, refractory, and adaptation for Spikenaut distillation.",
        ),
    }


# ---------------------------------------------------------------------------
# nelb-r63-003 — FTIR remaining methanol of a carbonylation vent, simulated
# ACCEPT / REJECT
# ---------------------------------------------------------------------------
def rec_003():
    k_f = 4.00
    a_meoh = 8.00
    a_is = 2.00
    c_ppm = k_f * a_meoh / a_is
    r_a = a_meoh / a_is
    _exact(c_ppm, 16.00)
    _exact(r_a, 4.00)
    _exact(k_f * 6.00 / a_is, 12.00)
    _exact(k_f * 4.00 / a_is, 8.00)
    _exact(6000.0 + 720.0, 6720.0)

    raster = make_lif_raster(
        neurons=16,
        mean_rate_hz=62.5,
        window_ms=36.0,
        seed=20260963003,
        source="fs8.ftir.A_meoh",
        target="fernshaw.vent_accept_core",
        table=[
            {"from": "ftir_A_meoh", "to": "meoh_estimator", "weight": 1.30},
            {"from": "ftir_snr", "to": "peak_norm", "weight": 1.10},
            {"from": "iroveil_c", "to": "vendor_skip_advocate", "weight": 0.42},
        ],
        third_factor={
            "modulator": "na.stage_rate_eligibility",
            "tau_e_s": 2.0,
            "tau_e_ms": 2000.0,
            "eligibility": (
                "pre-post coincidence on skip-survey synapses; the FTIR modulator depresses skip links "
                "when methanol peak-area stays in-band inside tau_e of an SNR lock so an Iroveil last-good "
                "cannot hide a 16.00 ppm V-3 remaining load or release V-1/V-2"
            ),
        },
        channel_prefix="ftr.n",
        anchor=(
            "FS-8 FTIR 36 ms frame at A_meoh 8.00 / A_is 2.00 / SNR 12.0 "
            "(t_s 3000) reconstructing 16.00 ppm inside the 8.00-24.00 band"
        ),
        kernel_ms=[0.0, 1.5, 9.0, 21.0],
    )
    w_s = 0.036
    events = [
        ev(100.0, "ftr.A_meoh", 4.00, code="A_MEOH", units="1", note="simulated FTIR Michelson peak-area of FS-8 carbonylation vent V-3 in FTIR-SIM-5; remaining-methanol family, not CEMS FTIR k-script, not NDIR CO, not OA-ICOS CH4, not TDLAS NH3, not UV-DOAS, not CRDS, not QEPAS"),
        ev(300000.0, "ftr.snr", 7.0, code="FTR_SNR", units="1"),
        ev(600000.0, "recon.C", 8.00, code="C_PPM", units="ppm", note="4.00*4.00/2.00=8.00; at the 8.00 band floor"),
        ev(900000.0, "vent.T", 42.0, code="T_C", units="C", note="plant vent RTD; independent witness; unread by Iroveil"),
        ev(1200000.0, "iroveil.C", 4.80, code="VENDOR_PPM", units="ppm", note="Iroveil vendor IR-6 last-good cloud; infra owner; under-read skip advocate"),
        ev(1500000.0, "ftr.A_is", 2.00, code="A_IS", units="1", note="cyclohexane internal-standard peak area; held"),
        ev(1800000.0, "ftr.A_meoh", 6.00, code="A_MEOH", units="1"),
        ev(2100000.0, "recon.C", 12.00, code="C_PPM", units="ppm", note="4.00*6.00/2.00=12.00; in band"),
        ev(2400000.0, "vent.id", 3.0, code="VENT_ID", units="1", note="V-3 in scope; V-1 and V-2 out of scope"),
        ev(2700000.0, "v12.present", 1.0, code="V12", units="bool", note="adjacent vents present; out of this ACCEPT"),
        ev(3000000.0, "ftr.A_meoh", 8.00, code="A_MEOH", units="1", note="in-band frame; raster sidecar kernel"),
        ev(3000001.5, "ftr.A_is", 2.00, code="A_IS", units="1", note="1.5 ms internal-standard after methanol peak"),
        ev(3150000.0, "ftr.snr", 12.0, code="FTR_SNR", units="1", note="SNR 12.0 >= 8.0 lock"),
        ev(3300000.0, "recon.C", 16.00, code="C_PPM", units="ppm", note="4.00*8.00/2.00=16.00 exact; band 8.00-24.00"),
        ev(3450000.0, "recon.R", 4.00, code="R_A", units="1", note="8.00/2.00=4.00 exact peak-area identity"),
        ev(3600000.0, "iroveil.C", 4.76, code="VENDOR_PPM", units="ppm"),
        ev(3900000.0, "vent.T", 43.0, code="T_C", units="C"),
        ev(4200000.0, "mdot.kg_h", 48.00, code="MDOT", units="kg_h", note="16.00 ppm * 3.00 kg/h * 1000/1000 identity placeholder; plant mass-flow tracks FTIR not Iroveil"),
        ev(4500000.0, "ftr.drop", 1.0, code="FTR_DROP", units="bool"),
        ev(4800000.0, "ops.prop", 1.0, code="SKIP_SURVEY", units="bool", note="night planner Kade Murr: Iroveil is 4.80 ppm; skip V-3 survey and dump the header"),
        ev(5100000.0, "dump.trip", 0.0, code="DUMP_ARMED", units="bool", note="dump would be a header kill; out of this ACCEPT"),
        ev(5400000.0, "gate.comp", 1.0, code="ACCEPT", units="decision", note="bounded ACCEPT of V-3 only; 16.00 ppm in band; V-1..V-2 out of scope; Iroveil not SoT"),
        ev(5700000.0, "recon.C", 16.00, code="C_PPM", units="ppm"),
        ev(6000000.0, "surv.start", 1.0, code="SURV_START", units="bool", note="bookend 1 of the 12.0 min survey floor"),
        ev(6300000.0, "ftr.snr", 12.0, code="FTR_SNR", units="1"),
        ev(6600000.0, "iroveil.C", 4.72, code="VENDOR_PPM", units="ppm"),
        ev(6720000.0, "surv.floor", 1.0, code="SURV_FLOOR", units="bool", note="6000 s + 720 s = 6720 s = 12.0 min"),
        ev(7200000.0, "ops.skip", 1.0, code="SKIP_ISOLATE", units="bool", note="Murr: skip-isolate V-3; Iroveil still 4.72; takt is late"),
        ev(7500000.0, "v12.present", 1.0, code="V12", units="bool"),
        ev(7800000.0, "takt.late", 1.0, code="TAKT", units="bool"),
        ev(8100000.0, "gate.hold", 1.0, code="REJECT", units="decision", note="companion t2 REJECTS skip-isolate; V-3 stays the bounded ACCEPT; dump not taken"),
        ev(8400000.0, "v3.held", 1.0, code="V3_HELD", units="bool"),
        ev(8700000.0, "v12.skip", 0.0, code="V12_NOT_RELEASED", units="bool"),
        ev(9000000.0, "dump.trip", 0.0, code="DUMP_NOT_TAKEN", units="bool"),
        ev(9300000.0, "ftr.A_meoh", 6.00, code="A_MEOH", units="1"),
        ev(9600000.0, "recon.C", 12.00, code="C_PPM", units="ppm", note="4.00*6.00/2.00=12.00; still in band so V-3 hold stands"),
        ev(9900000.0, "iroveil.C", 4.68, code="VENDOR_PPM", units="ppm"),
        ev(10200000.0, "vent.T", 41.0, code="T_C", units="C"),
        ev(10500000.0, "ftr.A_is", 2.00, code="A_IS", units="1"),
        ev(10800000.0, "surv.held", 1.0, code="SURV_HELD", units="bool"),
        ev(11100000.0, "recon.R", 3.00, code="R_A", units="1", note="6.00/2.00=3.00 post-accept ratio"),
        ev(11400000.0, "ftr.drop", 1.0, code="FTR_DROP", units="bool"),
        ev(11700000.0, "vent.id", 3.0, code="VENT_ID", units="1"),
        ev(12000000.0, "v3.held", 1.0, code="V3_HELD", units="bool"),
        ev(12300000.0, "dump.trip", 0.0, code="DUMP_NOT_TAKEN", units="bool"),
        ev(12600000.0, "takt.late", 1.0, code="TAKT", units="bool"),
        ev(12900000.0, "iroveil.C", 4.64, code="VENDOR_PPM", units="ppm"),
        ev(13200000.0, "recon.C", 12.00, code="C_PPM", units="ppm"),
        ev(13500000.0, "ftr.snr", 11.0, code="FTR_SNR", units="1"),
        ev(13800000.0, "vent.T", 40.0, code="T_C", units="C"),
        ev(14100000.0, "v12.skip", 0.0, code="V12_NOT_RELEASED", units="bool"),
        ev(14400000.0, "surv.held", 1.0, code="SURV_HELD", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r63-003-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "FS-FTIR-2026-0902",
            "domain": "ftir_carbonylation_methanol",
            "setting": (
                "Fernshaw Carbonyl FS-8 (invented), vent V-3 digital twin in FTIR-SIM-5. "
                "Plant-owned FTIR Michelson methanol / cyclohexane peak-area ratio is the vent SoT. "
                "Iroveil / IR-6 vendor DAQ (infra owner) under-reads 4.80 ppm and wants a skip. "
                "Not CEMS FTIR k-script (r04), not NDIR CO (leftover r62), not OA-ICOS CH4 (live r21), "
                "not TDLAS NH3 (r22), not UV-DOAS (r59), not CRDS (r15), not QEPAS (r19)."
            ),
            "observables_at_decision": {
                "A_meoh": a_meoh,
                "A_is": a_is,
                "k_f": k_f,
                "C_ppm": c_ppm,
                "R": r_a,
                "ftr_snr": 12.0,
                "iroveil_ppm": 4.80,
                "band_lo_ppm": 8.00,
                "band_hi_ppm": 24.00,
                "vent_scope": "V-3",
            },
            "margin_authority": (
                "FS-8 vent SOP rev D: if reconstructed C_ppm is inside 8.00-24.00 AND FTIR SNR >= 8.0 "
                "AND the tagged vent is V-3, ACCEPT V-3 only. Iroveil is not SoT. V-1 and V-2 stay out of scope. "
                "Header dump is a different gate."
            ),
        },
        "proposed_action": {
            "actor": "night planner Kade Murr, citing Iroveil 4.80 ppm and a quiet IR-6 peak",
            "summary": "skip V-3 survey and dump the carbonylation header; 8.00 A_meoh is a fouled-cell glitch on a healthy 4.80 ppm last-good",
            "basis_claimed": "Iroveil is the only OEM methanol SoT and a night survey of V-3 is a takt miss",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": (
                "Bounded ACCEPT of V-3 only. Serialized reconstruction: C_ppm = k_f * A_meoh / A_is = "
                "4.00 * 8.00 / 2.00 = 16.00 ppm, inside the 8.00-24.00 band, and FTIR SNR is 12.0 >= 8.0. "
                "Peak-area identity A_meoh / A_is = 8.00 / 2.00 = 4.00. Iroveil 4.80 ppm is an under-read skip "
                "advocate, not SoT. V-1 and V-2 are out of this ACCEPT. Ordered: keep V-3 on the plant FTIR. "
                "Scope: this ACCEPT does not dump the header (companion question) and does not release V-1/V-2."
            ),
            "threshold": "8.00<=C_ppm<=24.00 AND ftr_snr>=8.0 AND vent==V-3 => ACCEPT V-3; Iroveil is not SoT",
            "stated_residuals": "survey floor still required; 16.00 vs a true leak is a later sample; Iroveil remains the only OEM methanol channel",
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 5400: V-3 bounded in-band; Iroveil not SoT; V-1/V-2 not released; dump not taken",
            "tool": "fs8-ftir-vent-gate-cli",
            "observation": "C 16.00 ppm recomputes from A_meoh 8.00 and A_is 2.00; plant FTIR hashed; Iroveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "FTIR A_meoh 8.00 A_is 2.00; raster frame; C 16.00 ppm"},
                {"t_s": 4800.0, "event": "ops proposes skip-survey / dump"},
                {"t_s": 5400.0, "event": "ACCEPT V-3 only"},
                {"t_s": 6000.0, "event": "12 min survey bookend 1"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 8100.0, "event": "companion REJECT skip-isolate"},
            ],
            "observed_effects": [
                "methanol recomputes from the serialized FTIR peak-area model at every recon.C event",
                "an Iroveil-only head would have skipped V-3 and dumped the header",
                "12 min survey floor is in the stream; V-1/V-2 stay out of scope",
            ],
            "surprises": [
                "a vendor under-read 4.80 ppm skip corridor co-existed with a 16.00 ppm in-band plant reconstruction",
            ],
            "new_state": {
                "vent_v3": "bounded ACCEPT",
                "iroveil": "not SoT",
                "v1_v2": "out of scope",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.41,
            [
                ("ftir_reconstruction", 0.14),
                ("bounded_accept_scope", 0.12),
                ("iroveil_nonsubstitution", 0.10),
                ("in_band_lock", 0.08),
                ("survey_time_cost", -0.03),
            ],
            "scored for a bounded ACCEPT of V-3 on a recomputable FTIR methanol while refusing an Iroveil under-read skip and keeping V-1/V-2 out of scope",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "ftir-methanol", "serialized-reconstruction", "bounded-scope"],
            distillation_note="FTIR gate: serialized k_f*A_meoh/A_is plus SNR lock beats a vendor under-read skip; V-3 only",
            distillation_value="Teaches an SNN to race an FTIR peak-area ratio against a patched vendor methanol skip with bounded vent scope, refractory, and adaptation.",
        ),
    }
    traj2 = {
        "id": "nelb-r63-003-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "FS-FTIR-2026-0902-exec",
            "domain": "skip_isolate_refusal_execution",
            "setting": "Same FS-8 after the bounded ACCEPT. Planner proposes skip-isolate of V-3 under late takt. Companion REJECTS the skip; dump stays down.",
            "observables_at_decision": {
                "C_ppm": 12.00,
                "surv_floor_s": 720.0,
                "skip_isolate_proposed": True,
                "v3_held": True,
            },
        },
        "proposed_action": {
            "actor": "night planner Kade Murr",
            "summary": "skip-isolate V-3; 12 min already paid and Iroveil still shows 4.72 ppm; takt is late",
            "basis_claimed": "the ACCEPT already cleared V-3, so a skip-isolate is the cheapest takt recovery",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": (
                "Skip-isolate is refused. The 12 min survey floor is complete and the in-band tripwire "
                "(8.00 <= C_ppm <= 24.00) is still armed on the plant FTIR. REJECT skip-isolate. Do not dump "
                "the header. Do not restore on Iroveil. Do not release V-1/V-2. 12.00 ppm post-accept is still "
                "the plant SoT until a new frame leaves the band."
            ),
            "threshold": "surv_held AND skip_isolate_not_taken AND dump_not_taken AND v12_not_released",
        },
        "executed_action": {
            "summary": "skip-isolate REJECTED at t_s 8100; dump not latched; Iroveil restore not taken; V-3 held",
            "tool": "fs8-ftir-skip-exec",
            "observation": "recon.C 12.00 ppm after ACCEPT; survey line-up complete; Iroveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "survey clock started after ACCEPT"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7200.0, "event": "skip-isolate proposed"},
                {"t_s": 8100.0, "event": "REJECT skip-isolate; dump refused"},
            ],
            "observed_effects": [
                "Iroveil restore did not reopen the methanol call",
                "header dump never fired; V-3 held on the plant FTIR",
            ],
            "new_state": {"hold": "survey-held", "plant": "in service", "vent_v3": "held"},
            "latency_ms": 1380000.0,
        },
        "reward_components": reward(
            0.36,
            [
                ("skip_isolate_refusal", 0.12),
                ("no_header_dump", 0.10),
                ("iroveil_nonsubstitution", 0.08),
                ("scope_held", 0.08),
                ("takt_cost", -0.02),
            ],
            "operational execution gate: refuse skip-isolate because Iroveil is not a skip license; not a methanol re-vote",
        ),
        "meta": meta_common(tags=["REJECT", "operational-execution", "skip-refusal"]),
    }
    return {
        "id": "nelb-r63-003",
        "spike_events": events,
        "language_view": {
            "description": (
                "Fernshaw Carbonyl FS-8 FTIR-SIM-5. Plant-owned FTIR reconstructs 16.00 ppm methanol from "
                "8.00/2.00 while Iroveil still reports 4.80 ppm. The gate ACCEPTs V-3 only (V-1..V-2 out of "
                "scope). A 12 min survey floor is serialized. Companion t2 REJECTs skip-isolate."
            ),
            "trajectory": traj,
            "trajectory_skip_refusal": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "ftr.A_meoh / ftr.A_is / ftr.snr": "methanol and internal-standard peak areas and SNR; the physics channels the reconstruction consumes",
                "recon.C / recon.R": "serialized methanol ppm and peak-area identity",
                "vent.T / iroveil.C / vent.id / v12.present / ftr.drop / mdot.kg_h": "vent witnesses, vendor last-good, scope tags, dropped packets, mass-flow",
                "ops.prop / gate.comp / ops.skip / gate.hold": "skip-survey proposal, ACCEPT, skip-isolate proposal, companion REJECT",
                "surv.start / surv.floor / v3.held / v12.skip / dump.trip / takt.late / surv.held": "operational companion channels plus the 12 min floor",
            },
            "temporal_motifs": [
                "vendor-under while plant-in-band: iroveil.C 4.80 next to recon.C 16.00",
                "reconstruction as event: recon.C 16.00 equals 4.00*8.00/2.00",
                "ACCEPT then operational REJECT: gate.comp at 5400 s, gate.hold at 8100 s",
                "slow floor in-stream: surv.start 6000 s, surv.floor 6720 s (12.0 min)",
                "tight FTIR pair: ftr.A_meoh then ftr.A_is +1.5 ms at the raster frame (kernel, not excerpt echo)",
            ],
            "language_to_spike_mapping": (
                "'Iroveil is 4.80 ppm' = iroveil.C 4.80; '16 ppm methanol' = recon.C 16.00; "
                "'ACCEPT V-3 only' = gate.comp ACCEPT; 'refuse skip-isolate' = gate.hold REJECT"
            ),
            "why_high_value": (
                "New FTIR remaining-methanol peak-area family on a carbonylation vent (not CEMS FTIR k-script r04, "
                "not NDIR CO leftover r62, not OA-ICOS CH4 live r21, not TDLAS r22, not UV-DOAS r59, not CRDS r15, "
                "not QEPAS r19). Lead bounded ACCEPT of V-3 on a recomputable 16.00 ppm in-band load that a vendor "
                "under-read would have skipped. Companion t2 REJECTS skip-isolate. Independent CUBA LIF raster. "
                "sim_or_real=simulated."
            ),
            "encoder_spec": {
                "prng": "CUBA LIF (lif_raster._calibrate_spikes) plus MT19937 amplitudes",
                "seeds": {
                    "raster": 20260963003,
                    "stream_note": "stream amplitudes are authored constants (1, ppm, C, kg_h, bool)",
                },
                "draw_order": "independent CUBA LIF full window; kernelized 0.0/1.5 ms physics pair is synaptic drive, not excerpt copy",
                "thinning": "FTIR interferogram exists at ~1 Hz; stream keeps 4 A_meoh points plus IS pairs; recon keeps 4 of ~20 solver ticks",
                "time_alias": "t_rel_ms; t0 = 2026-09-02T03:00:00Z simulated night start",
            },
            "distillation_targets": [
                "FTIR reconstruction head: C_ppm = k_f * A_meoh / A_is; R = A_meoh / A_is",
                "bounded ACCEPT head: in-band C AND vent scope AND v12-out-of-scope",
                "operational companion: refuse skip-isolate without re-opening the last-good call",
            ],
        },
        "reconstruction_model": {
            "name": "ftir_peak_area_methanol",
            "formula": "C_ppm = k_f * A_meoh / A_is; R = A_meoh / A_is",
            "parameters": {
                "k_f": 4.00,
                "band_lo_ppm": 8.00,
                "band_hi_ppm": 24.00,
                "surv_min": 12.0,
            },
            "worked_example": {"A_meoh": 8.00, "A_is": 2.00, "R": 4.00, "C_ppm": 16.00},
            "check": "4.00 * 8.00 / 2.00 = 16.00 exactly; 8.00 / 2.00 = 4.00 exactly; 6000 s + 720 s = 6720 s = 12.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 36.0,
            "decision_window_s": 0.036,
            "code": "fs8.ftir_vent_gate",
            "note": "ACCEPT accumulator wins: plant FTIR methanol evidence overpowers the Iroveil skip advocate",
            "decode_rule": "accept if meoh_estimator AND peak_norm fire inside the window; vendor_skip_advocate is necessary-but-not-sufficient and cannot release V-1..V-2",
            "populations": [
                gate_pop("meoh_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("peak_norm", 64, 1.2, 31.25, w_s),
                gate_pop("vent_margin", 40, 1.0, 50.0, w_s),
                gate_pop("vendor_skip_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("accept_latch", 96, 1.8, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "fs8.ftir_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 36.0},
                {"check": "fs8.vent_scorer", "neurons": 40, "mean_rate_hz": 62.5, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r63-003",
            clock_domain="fs8-ftir-sim-relative-ms-t0-2026-09-02T03:00:00Z",
            tags=["ftir-methanol", "ACCEPT", "REJECT", "serialized-reconstruction", "operational-t2"],
            distillation_value="FTIR peak-area methanol head with independent CUBA LIF raster, bounded vent scope, refractory, and adaptation for Spikenaut distillation.",
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
            if nk == "real" and k.casefold() == "real":
                hits.append(p)
            hits.extend(walk_banned(v, p))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            hits.extend(walk_banned(v, f"{path}[{i}]"))
    return hits


def jaccard_independence(rec):
    window_ms = rec["raster"]["window_ms"]
    rast = {int(e["t_us"]) for e in rec["raster"]["excerpt"]}
    stream = set()
    for e in rec["spike_events"]:
        t = e["t_rel_ms"]
        if 0.0 <= t <= window_ms:
            stream.add(int(round(t * 1000.0)))
    inter = rast & stream
    union = rast | stream
    jac = (len(inter) / len(union)) if union else 0.0
    if jac > 0.05:
        raise RuntimeError(f"{rec['id']} LIF Jaccard {jac:.4f} vs in-window stream (echo)")
    return jac


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
        if rec["meta"].get("snn_tags") != SNN_TAGS:
            raise RuntimeError(f"{rec['id']} missing meta.snn_tags")
        if rec["meta"].get("nelb", {}).get("snn_tags") != SNN_TAGS:
            raise RuntimeError(f"{rec['id']} missing meta.nelb.snn_tags")
        if rec["raster"].get("encoder") != "independent_cuba_lif":
            raise RuntimeError(f"{rec['id']} raster not independent LIF")
        jaccard_independence(rec)
        ids.append(rec["id"])
        lv = rec["language_view"]
        ids.append(lv["trajectory"]["id"])
        for k, v in lv.items():
            if k.startswith("trajectory") and isinstance(v, dict) and "id" in v:
                if k != "trajectory":
                    ids.append(v["id"])
                sim2 = v["state"]["sim_or_real"]
                if sim2 not in {"designed", "simulated", "hil"}:
                    raise RuntimeError(sim2)
                if sim2 == "real":
                    raise RuntimeError("real")
                if v["safety_decision"]["decision"] not in {"ACCEPT", "MODIFY", "REJECT"}:
                    raise RuntimeError(v["safety_decision"]["decision"])
                tmeta = v.get("meta") or {}
                if tmeta.get("snn_tags") != SNN_TAGS:
                    raise RuntimeError(f"{v['id']} missing trajectory snn_tags")
                if tmeta.get("round") != ROUND:
                    raise RuntimeError(f"{v['id']} round")
        n = len(rec["spike_events"])
        if not (48 <= n <= 80):
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
        if not (20 <= rast["window_ms"] <= 50):
            raise RuntimeError("window")
        if abs(rast["window_s"] - rast["window_ms"] / 1000.0) > 1e-9:
            raise RuntimeError("window_s")
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
        if rec["meta"].get("round") != ROUND:
            raise RuntimeError("round")
    if len(ids) != len(set(ids)):
        raise RuntimeError(f"dup ids {ids}")
    if set(sims) != {"designed", "simulated", "hil"}:
        raise RuntimeError(f"sim mix {sims}")
    if set(decisions) != {"ACCEPT", "MODIFY", "REJECT"}:
        raise RuntimeError(f"decision mix {decisions}")
    lead = [records[i]["language_view"]["trajectory"]["safety_decision"]["decision"] for i in range(3)]
    if set(lead) != {"ACCEPT", "MODIFY", "REJECT"}:
        raise RuntimeError(f"lead mix {lead}")
    print("local_checks ok", [r["id"] for r in records], "ids", len(ids))
    print("decisions", decisions, "sims", sims)


def write_exclusive(path: Path, text: str):
    fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(text)


def choose_live_paths():
    batch = LIVE / "batch-r63.jsonl"
    notes = LIVE / "NOTES-r63.md"
    if not batch.exists() and not notes.exists():
        return batch, notes, ""
    suffix = "c"
    n = 1
    while True:
        batch = LIVE / f"batch-r63{suffix}.jsonl"
        notes = LIVE / f"NOTES-r63{suffix}.md"
        if not batch.exists() and not notes.exists():
            return batch, notes, suffix
        n += 1
        suffix = f"c{n}"


def notes_text(records, batch_path: Path, sizes, file_sha, file_size, suffix: str) -> str:
    isis = []
    spikes = []
    events = []
    windows = []
    energies = []
    for rec in records:
        ident = rec["raster"]["isi_count_identity"]
        isis.append(ident["isi_total"])
        spikes.append(rec["raster"]["spikes"])
        events.append(len(rec["spike_events"]))
        windows.append(int(rec["raster"]["window_ms"]))
        energies.append(int(rec["raster"]["energy_pJ"]))
    energy_sum = sum(energies)
    spike_sum = sum(spikes)
    where = str(batch_path.parent)
    tagged = "c-suffix collision path" if suffix else "create-only live path"
    return f"""# Neuromorphic Event + Language Bridge — NOTES round 63
Run: 2026-09-02-final-heavy · Factory: neuromorphic-event-language-bridge · Generator: grok-4.6 · Output: `{batch_path.name}` (3 paired artifacts, 6 ThalamicTrajectories)
Rights: RM-793 research-only (SpaceXAI/xAI grok-4.6, SuperGrok Heavy chat). Not training_ready. CREATE-ONLY write ({tagged}) at `{where}` (`{batch_path.name}`, `{(LIVE / batch_path.name.replace('batch', 'NOTES')).name if False else batch_path.with_name(batch_path.name.replace('batch','NOTES').replace('.jsonl','.md')).name}`). Never 2026-08-17 / 2026-08-30. Leftover-mill `/tmp/nelb-r63/` (Wobbe / nephelometric / cation conductivity, ids `190`–`192`) is a different artifact and was not overwritten.

## Context / de-duplication
Live tree already had r21 (OA-ICOS CH4 / SERF OPM / WGM water), r41 (LDA / coulometric Karl Fischer / bender-element), r61 (Stern-Volmer DO / pellistor LEL / FMCW tank-radar). Leftover-mill r13–r70 families (including leftover r63 Wobbe/NTU/cation, r64 venturi/katharometer/Clark, r69 flame-photometric S / idler-belt / glass pH, r70 NIR moisture) were treated as taken. IDs this round `nelb-r63-001`…`003` as assigned (not leftover `190`–`192`). Envelope cloned from live r61 (`language_view.trajectory` + operational t2 + `spike_events` + `raster` + `gate_snn` + `isi_histogram` + `routing.third_factor` + 15-key RM-793 `meta.rights`) with **independent CUBA LIF rasters** (not MT19937 gap-placement echo of `spike_events`). `meta.snn_tags` = [race, refractory, adaptation] on every record and trajectory (`meta.nelb.snn_tags` twin).

Banned this round: live r21/r41/r61 families; leftover-mill r13–r70 table (Wobbe, nephelometric, cation conductivity, venturi, katharometer, Clark DO, glass pH, NIR moisture, flame-photometric S, idler-belt, UV ozone, triboelectric dust, molybdenum-blue phosphate, hydrostatic dP, polarimeter, platinum ORP, NDIR CO, gamma-backscatter, ultrasonic-Doppler, Stern-Volmer DO, pellistor, FMCW radar, OA-ICOS, SERF, WGM, LDA, Karl Fischer, bender-element, CEMS FTIR k-script). Plants not reused: Mirewhin, Lacquerfen, Pitchshaw, Rushcrag, Copsewick, Peatspire, Sedgewhin, Brinecrag, Lichenholt, Slagholt, Copsewhin, Siltwharf, Reedcairn/Brackenmire/Fernshaw are new this round.

Adjacencies declared in-pair then kept physically distinct:
- **001 ICP-OES Ni** is an inductively-coupled-plasma emission internal-standard remaining nickel of an electroless bath, not LIBS plasma (r19/r21/r22), not spark-OES, not XRF (r29/r34), not PGNAA (r15), not handheld XRF.
- **002 LVDT expansion** is a linear-variable-differential-transformer remaining HP-casing growth of a steam turbine, not strain-gauge hopper (r59), not DIC hoop (r51), not Seebeck (r45), not coda-wave (r45), not bender-element (live r41), not load-cell.
- **003 FTIR methanol** is a Michelson peak-area remaining methanol of a carbonylation vent, not CEMS FTIR k-script (r04), not NDIR CO (leftover r62), not OA-ICOS CH4 (live r21), not TDLAS NH3 (r22), not UV-DOAS (r59), not CRDS (r15), not QEPAS (r19).

## Round 63 batch summary (3 pairs, 6 trajectories)

| id | modality (NEW family) | domain | decisions | headline |
|----|----------------------|--------|-----------|----------|
| nelb-r63-001 | ICP-OES remaining nickel of an electroless bath (k_icp·I_ni/I_y g/L, Specveil last-good denial, 18 min bath-hold floor) | Reedcairn Plating RC-9 bath T-6 (invented): 12.00/2.00 reconstructs 24.00 g/L while Specveil still reads 4.80 g/L | REJECT (+0.43) / MODIFY (+0.34) | serialized `4.00*12.00/2.00=24.00`; `12.00/2.00=6.00`; conjunctive SOP (Ni AND SNR) forbids continue-plate; three-party collusion includes the ICP infra owner; companion t2 bath-hold, plant ESD refused; sim_or_real=designed |
| nelb-r63-002 | LVDT remaining HP-casing expansion of a steam turbine (k_l·(V−V0) mm, Coreveil last-good denial, 24 min cooldown floor) | Brackenmire Turbine BM-7 casing C-2 (invented, HIL dummy in LVDT-HIL-7): 8.00−2.00 reconstructs 15.00 mm while Coreveil still reads 4.80 mm | MODIFY (+0.40) / ACCEPT (+0.35) | serialized `2.50*(8.00-2.00)=15.00` and `8.00-2.00=6.00`; keep-running refused; core tech Wren Solis exonerated (missing core-zero AE, UTC vs UTC+2); companion t2 new-core restart; sim_or_real=hil |
| nelb-r63-003 | FTIR remaining methanol of a carbonylation vent (k_f·A_meoh/A_is ppm, Iroveil last-good denial, 12 min survey floor) | Fernshaw Carbonyl FS-8 vent V-3 (invented, simulated FTIR-SIM-5): 8.00/2.00 reconstructs 16.00 ppm while Iroveil still reads 4.80 ppm | ACCEPT (+0.41) / REJECT (+0.36) | serialized `4.00*8.00/2.00=16.00`; `8.00/2.00=4.00`; bounded ACCEPT of V-3 only; V-1..V-2 out of scope; companion t2 REJECTS skip-isolate; sim_or_real=simulated |

Decision spread: REJECT / MODIFY / MODIFY / ACCEPT / ACCEPT / REJECT — **2A/2M/2R**. All three enums used, and all three sit on **leads**. Provenance spread: designed / hil / simulated (one each; never real). IDs `nelb-r63-001`…`003` plus t1/t2 suffixes.

## Raster sidecar
Every record carries `raster` + top-level `gate_snn` + `gate_compute`. Windows {windows[0]}/{windows[1]}/{windows[2]} ms; `window_s == window_ms/1000` exactly; `spikes == round(neurons·rate·window_s)` with zero slack ({spikes[0]}/{spikes[1]}/{spikes[2]}); `energy_pJ = spikes·23` and `energy_uJ = spikes·23e-6` exact ({energies[0]}/{energies[1]}/{energies[2]} pJ). Routing source/target + 3-entry tables + `third_factor` on all three (modulators da.cross_authority_conflict / ach.referral_pressure_salience / na.stage_rate_eligibility; τe 1.6/1.2/2.0 s as consistent `tau_e_s`+`tau_e_ms` pairs). Excerpts integer `t_us`, in-window, `neuron_id`-bounded, sorted, **full-window CUBA LIF** (not spike_events echo); per-spike amplitude with adaptation (0.82**k) plus noise. ISI histograms from the full window, bins ≥1 ms, counts sum to `spikes − distinct_active_neurons` ({isis[0]}/{isis[1]}/{isis[2]}). Same-neuron gaps ≥1000 µs. `gate_snn` on all three: decisions REJECT/MODIFY/ACCEPT matching each lead trajectory; every rate-declaring population's budget exact against its decision window. Main streams: **{events[0]}/{events[1]}/{events[2]} events** (48+), strictly increasing `t_rel_ms` only (no `t_ms` mix), same-channel refractory ≥0.8 ms (001 ICP pair at 1.4 ms, 002 LVDT pair at 1.2 ms plus isolate-frame SNR 14.0, 003 FTIR pair at 1.5 ms). `meta.snn_tags` required.

## Self-critique

### Edge cases added vs still thin
- **Added:** first ICP-OES internal-standard remaining-nickel family on an electroless bath with recomputable Ni=k_icp·I_ni/I_y (`24.00 g/L`) plus intensity-ratio identity and three-party collusion including the ICP infra owner; first LVDT remaining-expansion family on a steam-turbine HP casing with recomputable L=k_l·(V−V0) (`15.00 mm`) and delta identity, plus a resolved-innocent core tech (timezone-skipped core-zero, not last-to-badge) and isolate-frame SNR 14.0; first FTIR Michelson peak-area remaining-methanol family on a carbonylation vent with recomputable C=k_f·A_meoh/A_is (`16.00 ppm`) plus area-ratio identity; bounded ACCEPT whose out-of-scope clause is adjacent vents rather than a hopper/taphole/dump cap; operational t2 on all three (bath-hold, new-core restart, skip-isolate refusal); provenance trio designed/hil/simulated; 18 / 24 / 12 min slow floors in-stream; **independent CUBA LIF rasters** (live r21/r41/r61 used gap-constrained MT19937 placement).
- **Still thin:** (i) 001's k_icp is a lumped emission gain, not a plasma-T / matrix table — a 200 K torch hop that fakes 24.00 g/L inside a 4.80 Specveil corridor is unwritten; (ii) 002's k_l is a lumped core-to-mm gain, not a temperature / radial-runout map, so a 40 K casing hop that fakes 15.00 mm is unwritten; (iii) 003's k_f is a lumped peak-area gain, not a path-length / water-interference map, so a humidity hop that fakes 16.00 ppm inside a 4.80 last-good is unwritten; (iv) vendor-only as a *lead* REJECT on a plant with *no* independent ICP/LVDT/FTIR installed yet remains slightly harder — 001/002 still have plant heads; (v) stream amplitudes remain authored constants (raster draws are the only seeded noise).

### Realism of noise / temporal fidelity
- Strong: 001's 24.00 g/L, R 6.00, and 18.0 min bath-hold (`6000+1080=7080 s`) recompute from the record; 002's 15.00 mm, dV 6.00, and 24.0 min cooldown (`2820+1440=4260 s`) recompute; 003's 16.00 ppm, R 4.00, and 12.0 min survey (`6000+720=6720 s`) recompute. Independent CUBA LIF plus adaptation (0.82**k plus 4% noise) and the 1.2–1.5 ms physics pairs give the 48+ stream a raster-scale motif without echoing `spike_events` into `raster.excerpt`.
- **Gaps, honestly:** (i) 52-event streams still thin 1 Hz ICP / 10 Hz LVDT / 1 Hz FTIR stacks; (ii) 001's post-stop 16.00 g/L is a later sample, not a closed-loop nickel controller; (iii) 002 HIL dummy times an in-service isolate that the stream does not independently witness on a second live casing until the new core starts; (iv) no gate_snn input→output volley pair at raster resolution this round.

### Training value (SNN/LSM + agentic)
Distillation targets: ICP-OES Ni=k_icp·I_ni/I_y head plus ratio identity; conjunctive isolate floor vs continue-plate vs plant ESD; ICP-infra collusion; LVDT L=k_l·(V−V0) head plus delta identity; isolate-floor casing vs keep-running vs shop-trip; core-zero AE / timezone exoneration; FTIR C=k_f·A_meoh/A_is and area-ratio identities; bounded ACCEPT with V-1..V-2-out-of-scope; skip-isolate refusal under survey takt. Agentic value concentrates in three patterns: reconstruction-as-SoT on a physical Ni/expansion/methanol the raw corridor cannot see, earned ACCEPT with an explicit physical out-of-scope object (V-1..V-2), and stop-then-hold so a REJECT does not become a plant/shop/dump kill. Independent LIF rasters give Spikenaut a non-echo membrane crossing to distill against the language view.

## What a later leftover-mill round should add (next densification target)
1. **Plasma-T / matrix table** on a non-RC-9 ICP so a 200 K torch hop fakes 24.00 g/L inside a 4.80 Specveil corridor, closing 001's lumped-k_icp gap.
2. **Temperature / radial-runout map** on a non-BM-7 LVDT so a 40 K hop fakes 15.00 mm while mean V looks healthy.
3. **Path-length / water-interference map** on a non-FS-8 FTIR so a humidity hop fakes 16.00 ppm inside a 4.80 last-good corridor.
4. **Vendor-only as a lead REJECT** on a plant that has no independent ICP/LVDT/FTIR installed yet (001/002 still had plant heads).
5. **Do not restage** leftover-mill r63 Wobbe / nephelometric / cation conductivity (ids 190–192), live r21 OA-ICOS / SERF / WGM, live r41 LDA / Karl Fischer / bender-element, live r61 Stern-Volmer / pellistor / FMCW, CEMS FTIR k-script, NDIR CO, venturi, glass pH, NIR moisture, LIBS, XRF, PGNAA, DIC, strain-gauge hopper. Do not steal leftover-mill ids `040`–`213`. Do not reuse Reedcairn RC-9, Brackenmire LVDT-HIL-7, or Fernshaw FTIR-SIM-5.

## Verification
`{batch_path.name}`: 3 lines, `json.loads`-clean (allow_nan=False), {sizes[0]}/{sizes[1]}/{sizes[2]} bytes (file {file_size}, sha256 `{file_sha}`). CREATE-ONLY write at `{where}`. Build-time asserts: global time order; same-channel ≥0.8 ms; 48+ events ({events[0]}/{events[1]}/{events[2]}); excerpt integer bounds, neuron bounds, sort, 1 ms per-neuron floor; ISI identity {isis[0]}/{isis[1]}/{isis[2]}; spike budgets exact; energy pJ/µJ exact; reward totals equal two-decimal component sums (+0.43/+0.34/+0.40/+0.35/+0.41/+0.36); gate_snn decisions match lead `safety_decision.decision`; `state.sim_or_real` ∈ {{designed, hil, simulated}}; `meta.round=63`, `meta.factory=neuromorphic-event-language-bridge`, `meta.generator=grok-4.6`, `meta.run_label=2026-09-02-final-heavy`; `meta.rights` 15-key RM-793 stamp (`intended_use=research_only`, `linear_issue=RM-793`, `generated_at={GENERATED_AT}`); `meta.snn_tags`=[race, refractory, adaptation]; independent CUBA LIF encoder; no hidden-reasoning keys; no `provenance` objects; no live-plant claims; no `training_ready`; no `real` / `thought` keys; all 9 record/trajectory ids unique. Raster base seeds 20260963001/20260963002/20260963003. Repo gates run against the staged JSONL after the exclusive write.

Honest novelty accounting: 3/3 modality families are new versus the live tree (r21/r41/r61) and versus leftover-mill r13–r70 (ICP-OES ≠ LIBS/XRF/PGNAA; LVDT ≠ strain-gauge/DIC/bender; FTIR peak-area methanol ≠ CEMS FTIR/NDIR/OA-ICOS/TDLAS). Independent CUBA LIF rasters are a new encoder versus live r21/r41/r61 gap-constrained placement. Against that: conjunctive SOP, operational t2, serialized reconstruction, bounded-accept-with-scope-limit, vendor-nonsubstitution, exoneration, and 2A/2M/2R are carried vocabulary. Net: a bit under half of the round's scenario/edge mass is genuinely novel.

Novel coverage: 46%
"""


def repo_validate(batch_path: Path):
    from check_records import FactoryStaging, check_jsonl
    from curate_bridge import curate_record, raster_status
    from verify_execution import verify_batch_for_frontier

    errs, warns, kinds, n = check_jsonl(
        batch_path, batch_path.name, staging=FactoryStaging(enabled=True)
    )
    print("check_jsonl", {"errors": len(errs), "warnings": len(warns), "kinds": dict(kinds), "n": n})
    for e in errs:
        print("ERROR", e)
    for w in warns:
        print("WARN", w)
    if errs:
        raise RuntimeError("check_jsonl failed")

    records = [json.loads(line) for line in batch_path.read_text().splitlines() if line.strip()]
    for i, rec in enumerate(records, 1):
        st = raster_status(rec, require_raster=True, require_routing_table=True)
        print(
            rec["id"],
            "raster_valid",
            st["raster_valid"],
            "gate_snn_valid",
            st["gate_snn_valid"],
            "reasons",
            st.get("reason_codes"),
        )
        if not st["raster_valid"] or not st["gate_snn_valid"] or st.get("reason_codes"):
            raise RuntimeError(f"raster_status {rec['id']} {st}")
        blob = json.dumps(rec, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
        h = hashlib.sha256(blob.encode("utf-8")).hexdigest()
        dec = curate_record(
            rec,
            source_path=batch_path.name,
            source_line=i,
            source_hash=h,
            require_raster=True,
            require_routing_table=True,
        )
        reasons = dec.manifest.get("reason_codes")
        print(rec["id"], "curate", dec.action, reasons)
        if dec.action != "retain":
            raise RuntimeError(f"curate {rec['id']} {dec.action} {reasons}")

    counts, findings, blocked = verify_batch_for_frontier(batch_path, strict=True)
    print("verify_batch_for_frontier", counts, "blocked", blocked)
    if blocked or counts.get("verified") != 3:
        print("findings", findings)
        raise RuntimeError(f"frontier blocked {counts}")

    spike_probe = PIPELINES / "spike_probe.py"
    if spike_probe.is_file():
        import subprocess

        proc = subprocess.run(
            [sys.executable, str(spike_probe), "--strict", str(batch_path)],
            capture_output=True,
            text=True,
        )
        print("spike_probe stdout", proc.stdout[-2000:])
        if proc.returncode != 0:
            print("spike_probe stderr", proc.stderr[-2000:])
            raise RuntimeError(f"spike_probe rc {proc.returncode}")


def main():
    occupancy_preflight()
    STAGE.mkdir(parents=True, exist_ok=True)
    records = [rec_001(), rec_002(), rec_003()]
    local_checks(records)
    lines = [json.dumps(rec, ensure_ascii=False, allow_nan=False, separators=(",", ":")) for rec in records]
    staged_batch = STAGE / "batch-r63.jsonl"
    staged_batch.write_text("\n".join(lines) + "\n", encoding="utf-8")
    sizes = [len(line) for line in lines]
    raw = staged_batch.read_bytes()
    file_sha = hashlib.sha256(raw).hexdigest()
    file_size = len(raw)
    print("staged", staged_batch, "sizes", sizes, "sha256", file_sha)

    repo_validate(staged_batch)

    live_batch, live_notes, suffix = choose_live_paths()
    notes = notes_text(records, live_batch, sizes, file_sha, file_size, suffix)
    if "Novel coverage:" not in notes:
        raise RuntimeError("NOTES missing Novel coverage")
    staged_notes = STAGE / "NOTES-r63.md"
    staged_notes.write_text(notes, encoding="utf-8")

    LIVE.mkdir(parents=True, exist_ok=True)
    write_exclusive(live_batch, "\n".join(lines) + "\n")
    write_exclusive(live_notes, notes)
    print("WROTE", live_batch)
    print("WROTE", live_notes)
    print("suffix", suffix or "(none)")
    print("PAIR_TABLE")
    print("nelb-r63-001\tICP-OES Ni electroless\tREJECT/MODIFY\tdesigned")
    print("nelb-r63-002\tLVDT HP-casing expansion\tMODIFY/ACCEPT\thil")
    print("nelb-r63-003\tFTIR methanol peak-area\tACCEPT/REJECT\tsimulated")


if __name__ == "__main__":
    main()
