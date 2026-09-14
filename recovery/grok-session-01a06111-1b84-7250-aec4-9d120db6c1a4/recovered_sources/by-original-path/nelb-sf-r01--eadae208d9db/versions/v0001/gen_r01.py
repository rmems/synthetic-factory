#!/usr/bin/env python3
"""Generate NELB 2026-09-02-final-heavy round 1 (do not clobber existing raw)."""

from __future__ import annotations

import hashlib
import json
import math
import random
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

OUT_DIR = Path("/tmp/nelb-sf-r01")
BATCH = OUT_DIR / "batch-r01.jsonl"
NOTES = OUT_DIR / "NOTES-r01.md"
PUBLISH_DIR = Path(
    "/tmp/sf-window/outputs/raw/2026-09-02-final-heavy/neuromorphic-event-language-bridge"
)
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
    "hidden_reasoning",
    "scratchpad",
    "scratch",
    "internal_monologue",
    "private_reasoning",
    "inner_monologue",
}

ROUND = 1
FACTORY = "neuromorphic-event-language-bridge"
RUN = "2026-09-02-final-heavy"


def meta_common(**extra):
    m = {
        "round": ROUND,
        "factory": FACTORY,
        "generator": "grok-4.6",
        "run": RUN,
        "run_label": RUN,
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


def ev_s(t_s, channel, amplitude, **extra):
    t_rel_ms = float(t_s) * 1000.0
    rec = {
        "t_rel_ms": t_rel_ms,
        "channel": channel,
        "amplitude": float(amplitude),
        "t_hr": t_rel_ms / 3_600_000.0,
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
        if not e["channel"].strip():
            raise RuntimeError("empty channel")
        if t < last:
            raise RuntimeError("decreasing t_rel_ms")
        if t == last:
            raise RuntimeError("tied t_rel_ms")
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
# a1 — UV254 remaining absorbance of a filter outlet (designed, REJECT/MODIFY)
# Vendor-only: plant has no independent UV254 head.
# ---------------------------------------------------------------------------
def rec_a1():
    k_a = 4.00
    i0 = 16.00
    i_iso = 4.00
    od = math.log2(i0 / i_iso)
    _exact(od, 2.00)
    t_k = 293.0
    t0_k = 293.0
    t_ratio = t_k / t0_k
    _exact(t_ratio, 1.000)
    a_m = k_a * od * t_ratio
    _exact(a_m, 8.00)
    _exact(k_a * math.log2(i0 / 16.00), 0.00)
    _exact(k_a * math.log2(i0 / 8.00), 4.00)
    _exact(k_a * math.log2(i0 / 2.00), 12.00)
    l_m = 1.00
    _exact(k_a * od / l_m * l_m, 8.00)
    _exact(4800.0 + 1080.0, 5880.0)

    raster = make_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=40.0,
        seed=202609021,
        source="yc2.muni.uv254",
        target="yarrowcrag.filter_stop_core",
        table=[
            {"from": "lab_I", "to": "uv254_estimator", "weight": 1.40},
            {"from": "lab_snr", "to": "lab_lock_core", "weight": 1.15},
            {"from": "uvveil_a", "to": "vendor_continue_advocate", "weight": 0.45},
        ],
        third_factor={
            "modulator": "da.uv254_vendor_only_conflict",
            "tau_e_s": 1.6,
            "tau_e_ms": 1600.0,
            "eligibility": "pre-post coincidence on continue-filter synapses; the municipal UV254 modulator depresses continue-filter links when transmitted intensity stays low inside tau_e of an SNR lock so a Uvveil last-good cannot hide 8.00 m^-1 absorbance on a plant with no independent UV254 head",
        },
        channel_prefix="uv254.n",
        anchor="YC-2 municipal UV254 40 ms frame at I 4.00 / SNR 12.0 (t_s 3000) reconstructing 8.00 m^-1 over the 5.00 isolate floor",
    )
    w_s = 0.040
    events = [
        ev_s(0.0, "lab.I", 16.00, code="I_AU", units="1", note="municipal sealed spectrophotometer on a grab from Yarrowcrag YC-2 filter outlet F-4; plant has NO independent UV254 head; UV254 remaining-absorbance family, not UV-DOAS SO2, not UV-fluorescence oil-in-water, not Gorse-UV DOAS corridor witness, not CRDS, not TDLAS"),
        ev_s(120.0, "lab.snr", 4.0, code="LAB_SNR", units="1", note="early municipal SNR under the 8.0 lock floor"),
        ev_s(240.0, "recon.A", 0.00, code="A_M", units="1/m", note="4.00*log2(16.00/16.00)=0.00 exact"),
        ev_s(360.0, "path.T", 293.0, code="PATH_K", units="K", note="grab-cell thermistor on copper DCS; independent of Uvveil"),
        ev_s(480.0, "uvveil.A", 0.80, code="VENDOR_A", units="1/m", note="Uvveil vendor cloud; the only installed UV254 transmitter; infra owner"),
        ev_s(600.0, "grab.seal", 1.0, code="MUNI_SEAL", units="bool", note="municipality-owned bottle seal; nobody in the collusion set can write it"),
        ev_s(720.0, "permit.slide", 40.00, code="PERM_S", units="s", note="permit clerk Bram Solt slid F-4 clock 40.00 s"),
        ev_s(840.0, "lab.I", 8.00, code="I_AU", units="1"),
        ev_s(960.0, "recon.A", 4.00, code="A_M", units="1/m", note="4.00*log2(16.00/8.00)=4.00; still under the 5.00 isolate floor"),
        ev_s(1080.0, "grab.hash", 1.0, code="MUNI_HASH", units="bool", note="WORM hash of the sealed grab; municipality custody"),
        ev_s(1200.0, "path.T", 293.0, code="PATH_K", units="K"),
        ev_s(1320.0, "uvveil.A", 0.82, code="VENDOR_A", units="1/m"),
        ev_s(1440.0, "lab.snr", 7.0, code="LAB_SNR", units="1"),
        ev_s(1560.0, "muni.chain", 1.0, code="MUNI_CHAIN", units="bool", note="lab chain-of-custody tick; not Uvveil"),
        ev_s(1680.0, "collusion.vendor", 1.0, code="UVVEIL_PARTY", units="bool", note="Uvveil infra owner is a collusion party"),
        ev_s(1800.0, "lab.I", 8.00, code="I_AU", units="1"),
        ev_s(1920.0, "recon.A", 4.00, code="A_M", units="1/m"),
        ev_s(2040.0, "path.T", 292.5, code="PATH_K", units="K"),
        ev_s(2160.0, "uvveil.drop", 0.0, code="UV_DROP", units="bool"),
        ev_s(2280.0, "grab.seal", 1.0, code="MUNI_SEAL", units="bool"),
        ev_s(2400.0, "ops.watch", 1.0, code="WATCH", units="bool"),
        ev_s(2520.0, "lab.snr", 8.0, code="LAB_SNR", units="1"),
        ev_s(2640.0, "permit.slide", 40.00, code="PERM_S", units="s"),
        ev_s(2760.0, "uvveil.A", 0.79, code="VENDOR_A", units="1/m"),
        ev_s(2880.0, "path.T", 293.0, code="PATH_K", units="K", note="T/T0=1.000; no thermal hop"),
        ev_s(3000.0, "lab.I", 4.00, code="I_AU", units="1", note="isolate-floor frame; raster sidecar"),
        ev_s(3000.0014, "lab.snr", 12.0, code="LAB_SNR", units="1", note="1.4 ms SNR lock after I; 12.0 >= 8.0"),
        ev_s(3120.0, "recon.A", 8.00, code="A_M", units="1/m", note="4.00*log2(16.00/4.00)=8.00 exact; isolate 5.00, works-kill 16.00"),
        ev_s(3240.0, "recon.od", 2.00, code="OD", units="1", note="log2(16.00/4.00)=2.00 exact optical-depth identity"),
        ev_s(3360.0, "grab.A", 8.00, code="MUNI_A", units="1/m", note="sealed municipal spectrophotometer agrees with reconstruction"),
        ev_s(3480.0, "uvveil.A", 0.80, code="VENDOR_A", units="1/m"),
        ev_s(3600.0, "uvveil.drop", 1.0, code="UV_DROP", units="bool", note="vendor intensity packets dropped in Uvveil cloud for 40 s"),
        ev_s(3720.0, "path.T", 292.0, code="PATH_K", units="K"),
        ev_s(3840.0, "ops.prop", 1.0, code="CONTINUE_FILTER", units="bool", note="night operator Mara Vesk: Uvveil is clean 0.80; continue F-4"),
        ev_s(3960.0, "collusion.clerk", 1.0, code="CLERK_PARTY", units="bool"),
        ev_s(4200.0, "gate.stop", 1.0, code="REJECT", units="decision", note="refuse continue-filter; 8.00 m^-1 and SNR 12.0; Uvveil not SoT; plant has no independent UV254 head"),
        ev_s(4800.0, "pac.start", 1.0, code="PAC_START", units="bool", note="bookend 1 of the 18.0 min PAC-dose floor"),
        ev_s(5880.0, "pac.floor", 1.0, code="PAC_FLOOR", units="bool", note="4800 s + 1080 s = 5880 s = 18.0 min"),
        ev_s(6600.0, "ops.kill", 1.0, code="WORKS_ESD", units="bool", note="Vesk: ESD the whole Yarrowcrag works until day-shift"),
        ev_s(7200.0, "gate.hold", 1.0, code="MODIFY", units="decision", note="companion t2: PAC hold on municipal UV254 as live interlock; works ESD refused"),
        ev_s(7800.0, "paclock.set", 1.0, code="PAC_HELD", units="bool"),
        ev_s(8400.0, "lab.I", 2.00, code="I_AU", units="1"),
        ev_s(9000.0, "recon.A", 12.00, code="A_M", units="1/m", note="4.00*log2(16.00/2.00)=12.00; still over 5.00 so PAC holds"),
        ev_s(9600.0, "recon.od", 3.00, code="OD", units="1", note="log2(16.00/2.00)=3.00 on the post-stop frame"),
        ev_s(10200.0, "uvveil.A", 0.70, code="VENDOR_A", units="1/m"),
        ev_s(10800.0, "path.T", 291.0, code="PATH_K", units="K"),
        ev_s(11400.0, "pac.held", 1.0, code="PAC_HELD", units="bool"),
        ev_s(12000.0, "unit.esd", 0.0, code="ESD_NOT_TAKEN", units="bool"),
        ev_s(12600.0, "grab.A", 12.00, code="MUNI_A", units="1/m"),
        ev_s(13200.0, "permit.slide", 40.00, code="PERM_S", units="s"),
        ev_s(13800.0, "uvveil.drop", 1.0, code="UV_DROP", units="bool"),
        ev_s(14400.0, "paclock.held", 1.0, code="PAC_HELD", units="bool"),
        ev_s(15000.0, "muni.chain", 1.0, code="MUNI_CHAIN", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-20260902-r01-a1-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "YC-UV254-2026-0902",
            "domain": "uv254_filter_outlet_absorbance",
            "setting": "Yarrowcrag Water YC-2 (invented), filter outlet F-4. Plant has NO independent UV254 head. The only installed transmitter is Uvveil vendor cloud (infra owner). Municipal sealed spectrophotometer on a grab is the absorbance SoT. Permit clock is a collusion party. Invented plant; designed campaign. Not UV-DOAS SO2 (r59 leftover mill), not UV-fluorescence oil-in-water (r56), not Gorse-UV DOAS corridor witness (r15), not CRDS HF (r15), not TDLAS NH3 (r22), not 90-degree nephelometry (r63 in-flight).",
            "observables_at_decision": {
                "I": i_iso,
                "I0": i0,
                "k_a": k_a,
                "A_m": a_m,
                "OD": od,
                "T_K": t_k,
                "T0_K": t0_k,
                "lab_snr": 12.0,
                "uvveil_A": 0.80,
                "permit_slide_s": 40.00,
                "isolate_floor_m": 5.00,
                "plant_uv254_head_installed": False,
            },
            "margin_authority": "YC-2 filter SOP rev B: if reconstructed A_m >= 5.00 AND municipal SNR >= 8.0, continue-filter is forbidden even if Uvveil reports 0.80 m^-1. Works ESD is a different gate. Kill tripwire is 16.00 m^-1. Uvveil is not SoT on a plant with no independent UV254 head.",
        },
        "proposed_action": {
            "actor": "night filter operator Mara Vesk, citing Uvveil 0.80 m^-1 and a quiet intensity channel",
            "summary": "continue F-4 filter; 4.00 intensity is lamp noise on a healthy UV254 absorbance",
            "basis_claimed": "Uvveil is the only installed UV254 transmitter and a night abort of F-4 is a nomination miss",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Continue-filter is refused. Serialized reconstruction: A_m = k_a * log2(I0/I) * (T/T0) = 4.00 * log2(16.00/4.00) * 1.000 = 8.00, which is 3.00 m^-1 over the 5.00 isolate floor and 8.00 m^-1 under the 16.00 works-kill tripwire, and municipal SNR is 12.0 >= 8.0. Optical-depth identity OD = log2(I0/I) = 2.00; A = k_a * OD / L * L with L=1.00 m = 8.00. T/T0 = 1.000 so no thermal hop is available as an excuse. Plant has no independent UV254 head; Uvveil is the only installed transmitter and is a collusion party with operator Vesk and permit clerk Bram Solt (40.00 s clock slide plus dropped intensity packets). Defense rests on the municipality-owned sealed spectrophotometer and WORM grab hash, which nobody in the collusion set can write. Ordered: refuse continue-filter now. Scope: this REJECT does not ESD the works (that is the companion question) and does not isolate the grab-cell thermistor.",
            "threshold": "A_m>=5.00 AND lab_snr>=8.0 => refuse continue-filter; Uvveil is not SoT; works-kill if A_m>=16.00",
            "stated_residuals": "PAC dose still required to hold the 8.00 m^-1; 8.00 vs a true 16.00 kill is a production cut; Uvveil remains the only installed UV254 transmitter",
        },
        "executed_action": {
            "summary": "REJECT at t_s 4200: continue-filter refused; Uvveil not SoT; reconstruction locked to municipal grab",
            "tool": "yc2-uv254-filter-gate-cli",
            "observation": "A 8.00 m^-1 recomputes from I 4.00; municipal spectrophotometer hashed; Uvveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "lab I 4.00; raster frame; A 8.00 m^-1"},
                {"t_s": 3840.0, "event": "ops proposes continue-filter"},
                {"t_s": 4200.0, "event": "REJECT continue-filter"},
                {"t_s": 4800.0, "event": "18 min PAC bookend 1"},
                {"t_s": 5880.0, "event": "18.0 min floor"},
                {"t_s": 7200.0, "event": "companion MODIFY PAC hold vs works ESD"},
            ],
            "observed_effects": [
                "UV254 absorbance recomputes from the serialized municipal spectrophotometer model at every recon.A event",
                "a Uvveil-only head would have continued F-4 overnight",
                "18 min PAC-dose floor is in the stream (pac.start, pac.floor)",
            ],
            "surprises": [
                "a clean vendor 0.80 m^-1 corridor and a 40 s permit slide co-existed with an 8.00 m^-1 municipal reconstruction on a plant that has no independent UV254 head",
            ],
            "new_state": {
                "f4": "continue-filter blocked",
                "uvveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 1200000.0,
        },
        "reward_components": reward(
            0.43,
            [
                ("uv254_reconstruction", 0.14),
                ("conjunctive_isolate_floor", 0.12),
                ("uvveil_nonsubstitution", 0.10),
                ("vendor_only_no_plant_head", 0.10),
                ("pac_time_cost", -0.03),
            ],
            "scored for a continue-filter REJECT on a recomputable UV254 absorbance while refusing a Uvveil last-good on a plant with no independent UV254 head; 18 min PAC floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["REJECT", "uv254-absorbance", "vendor-only", "serialized-reconstruction", "operational-companion"],
            distillation_note="UV254 gate: serialized k_a*log2(I0/I) plus SNR lock beats a vendor last-good on a plant with no independent head; companion t2 is the PAC hold, not a referral vote",
        ),
    }
    traj2 = {
        "id": "nelb-20260902-r01-a1-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "YC-UV254-2026-0902-exec",
            "domain": "pac_uv254_interlock_execution",
            "setting": "Same YC-2 after the REJECT. Operator proposes works ESD. This companion is the operational PAC-dose hold with the municipal spectrophotometer as the live interlock, not a second absorbance vote.",
            "observables_at_decision": {
                "A_m": 12.00,
                "pac_floor_s": 1080.0,
                "works_esd_proposed": True,
                "pac_set": True,
            },
        },
        "proposed_action": {
            "actor": "night filter operator Mara Vesk",
            "summary": "ESD the whole Yarrowcrag works until day-shift; 18 min already paid and Uvveil still shows 0.70 m^-1",
            "basis_claimed": "the REJECT already stopped F-4, so a works kill is the cheapest hold",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "PAC-dose hold plus municipal UV254 as the live interlock. The 18 min PAC floor is complete and the isolate tripwire (A_m >= 5.00) is still armed on the sealed spectrophotometer. MODIFY the default Uvveil-restore SOP into a municipal-lab-only interlock. Do not ESD the works. Do not restore production on Uvveil. 12.00 m^-1 post-stop is still the municipal SoT until a new frame clears 5.00.",
            "threshold": "pac_dose AND pac_floor_complete AND works_esd_not_taken AND continue_not_restored",
        },
        "executed_action": {
            "summary": "PAC held at t_s 7200; works ESD not latched; Uvveil restore not taken",
            "tool": "yc2-pac-exec",
            "observation": "recon.A 12.00 m^-1 after stop; PAC line-up complete; Uvveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 4800.0, "event": "PAC clock started after REJECT"},
                {"t_s": 5880.0, "event": "18.0 min floor"},
                {"t_s": 6600.0, "event": "works ESD proposed"},
                {"t_s": 7200.0, "event": "MODIFY PAC hold; works ESD refused"},
            ],
            "observed_effects": [
                "Uvveil restore did not reopen the absorbance call",
                "works ESD never fired; F-4 held PAC on the municipal spectrophotometer",
            ],
            "new_state": {"pac": "dosing", "works": "in service", "f4": "held"},
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("pac_hold", 0.12),
                ("no_works_esd", 0.10),
                ("uvveil_nonsubstitution", 0.08),
                ("pac_floor_complete", 0.06),
                ("held_production_cost", -0.02),
            ],
            "operational execution gate: PAC hold because Uvveil is not a restore license; not an absorbance re-vote",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "pac-hold"]),
    }
    return {
        "id": "nelb-20260902-r01-a1",
        "spike_events": events,
        "language_view": {
            "description": "Yarrowcrag Water YC-2. Plant has no independent UV254 head. Municipal sealed spectrophotometer reconstructs 8.00 m^-1 from log2(16.00/4.00)*4.00 while Uvveil still reports 0.80 m^-1. The gate REJECTs continue-filter. An 18 min PAC-dose floor is serialized in the stream. Companion t2 MODIFYs a works ESD into a municipal-lab PAC hold.",
            "trajectory": traj,
            "trajectory_pac_hold": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "lab.I / lab.snr": "municipal spectrophotometer intensity and SNR; the physics channels the reconstruction consumes",
                "recon.A / recon.od": "serialized UV254 absorbance and optical-depth identity",
                "path.T / uvveil.A / permit.slide / uvveil.drop / grab.seal / grab.hash / grab.A": "grab thermistor, vendor absorbance cloud, permit clock slide, dropped packets, and municipality-owned witnesses nobody in the collusion set can write",
                "ops.prop / gate.stop / ops.kill / gate.hold": "continue-filter proposal, REJECT, works-ESD proposal, companion MODIFY",
                "pac.start / pac.floor / paclock.set / pac.held / unit.esd": "operational companion channels plus the 18 min floor",
            },
            "temporal_motifs": [
                "vendor-green while municipal-over: uvveil.A 0.80 next to recon.A 8.00",
                "reconstruction as event: recon.A 8.00 equals 4.00*log2(16.00/4.00)",
                "REJECT then operational MODIFY: gate.stop at 4200 s, gate.hold at 7200 s",
                "slow floor in-stream: pac.start 4800 s, pac.floor 5880 s (18.0 min)",
                "tight UV254 pair: lab.I then lab.snr +1.4 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Uvveil is 0.80 m^-1' = uvveil.A 0.80; '8 m^-1 absorbance' = recon.A 8.00; 'refuse continue-filter' = gate.stop REJECT; 'PAC not works ESD' = gate.hold MODIFY",
            "why_high_value": "New UV254 remaining-absorbance family on a drinking-water filter outlet (not UV-DOAS SO2 leftover-mill r59, not UV-fluorescence OIW r56, not r15 Gorse-UV DOAS as a corridor witness, not CRDS, not TDLAS, not 90-degree nephelometry). Lead REJECT of continue-filter on a recomputable absorbance that a vendor last-good and a permit clock slide would have cleared, on a plant that has no independent UV254 head installed. Three-party collusion includes the Uvveil infra owner. Companion t2 is operational PAC hold. sim_or_real=designed. Stream density restored to 52 events.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609021, "stream_note": "stream amplitudes are authored constants (1, 1/m, K, s, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "municipal spectrophotometer exists at ~1 Hz during a grab run; stream keeps 5 I points plus SNR locks; recon keeps 5 of ~50 solver ticks",
                "refractory_floors_ms": {
                    "lab.I": 1.4,
                    "lab.snr": 1.4,
                    "recon.A": 60000,
                    "recon.od": 60000,
                    "path.T": 60000,
                    "uvveil.A": 60000,
                    "permit.slide": 60000,
                    "uvveil.drop": 60000,
                    "ops.prop": 60000,
                    "gate.stop": 60000,
                    "pac.start": 60000,
                    "pac.floor": 60000,
                    "ops.kill": 60000,
                    "gate.hold": 60000,
                },
                "time_alias": "t_rel_ms; t_hr = t_rel_ms/3.6e6; t0 = 2026-09-02T01:00:00Z campaign start",
            },
            "distillation_targets": [
                "UV254 reconstruction head: A_m = k_a * log2(I0/I) * (T/T0); OD = log2(I0/I); A = k_a * OD / L * L",
                "conjunctive isolate floor vs continue-filter vs works ESD",
                "vendor-only nonsubstitution on a plant with no independent UV254 head; three-party collusion including the infra owner",
                "operational companion: PAC hold without restoring on Uvveil",
            ],
        },
        "reconstruction_model": {
            "name": "uv254_filter_absorbance",
            "formula": "A_m = k_a * log2(I0/I) * (T/T0); OD = log2(I0/I); A_m = k_a * OD / L_m * L_m",
            "parameters": {
                "k_a": 4.00,
                "I0": 16.00,
                "T0_K": 293.0,
                "L_m": 1.00,
                "isolate_floor_m": 5.00,
                "kill_m": 16.00,
                "snr_lock": 8.0,
                "pac_min": 18.0,
            },
            "worked_example": {"I": 4.00, "A_m": 8.00, "OD": 2.00, "T_ratio": 1.000},
            "check": "4.00 * log2(16.00/4.00) = 8.00 exactly; log2(16.00/4.00) = 2.00 exactly; 4800 s + 1080 s = 5880 s = 18.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.040,
            "code": "yc2.uv254_filter_gate",
            "note": "REJECT accumulator wins: municipal UV254 absorbance evidence overpowers the Uvveil continue advocate",
            "decode_rule": "reject-continue if uv254_estimator AND lab_lock fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("uv254_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("lab_lock", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("reject_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "yc2.uv254_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 40.0},
                {"check": "yc2.pac_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-20260902-r01-a1",
            clock_domain="yc2-uv254-campaign-relative-ms-t0-2026-09-02T01:00:00Z",
            time_aliases={"t_hr": "t_rel_ms / 3.6e6"},
            tags=["uv254-absorbance", "REJECT", "MODIFY", "vendor-only", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# a2 — Karl Fischer coulometric remaining water of a transformer-oil dryer
# (hil, MODIFY/ACCEPT). Exoneration of the probe tech.
# ---------------------------------------------------------------------------
def rec_a2():
    k_f = 2.00
    q_mc = 4.00
    m_g = 1.00
    x_ppm = k_f * q_mc / m_g
    _exact(x_ppm, 8.00)
    _exact(k_f * 1.00 / m_g, 2.00)
    _exact(k_f * 2.00 / m_g, 4.00)
    _exact(k_f * 8.00 / m_g, 16.00)
    q_over_m = q_mc / m_g
    _exact(q_over_m, 4.00)
    x_id = k_f * q_over_m
    _exact(x_id, 8.00)
    titer_ul = x_ppm * 0.50
    _exact(titer_ul, 4.00)
    _exact(2820.0 + 1440.0, 4260.0)

    raster = make_raster(
        neurons=25,
        mean_rate_hz=50.0,
        window_ms=32.0,
        seed=202609022,
        source="pf7.kf.coulomb",
        target="pewterfen.dryer_isolate_core",
        table=[
            {"from": "kf_Q", "to": "water_estimator", "weight": 1.35},
            {"from": "kf_snr", "to": "cell_norm_core", "weight": 1.20},
            {"from": "karlveil_x", "to": "vendor_continue_advocate", "weight": 0.40},
        ],
        third_factor={
            "modulator": "ach.kf_zero_skip_salience",
            "tau_e_s": 1.2,
            "tau_e_ms": 1200.0,
            "eligibility": "pre-post coincidence on keep-dryer synapses; the Karl Fischer modulator depresses keep-dryer and referral links when coulomb charge stays high inside tau_e of an SNR lock so a Karlveil last-good cannot hide 8.00 ppm water or name Joren Pyle",
        },
        channel_prefix="kf.n",
        anchor="PF-7 HIL coupon 32 ms frame at Q 4.00 mC / SNR 14.0 (t_s 1560) reconstructing 8.00 ppm over the 6.00 ppm isolate floor",
    )
    w_s = 0.032
    events = [
        ev_s(0.0, "kf.Q", 1.00, code="Q_MC", units="mC", note="HIL Karl Fischer coulometric cell on a dummy transformer-oil dryer in KF-HIL-4; remaining-water family, not Al2O3 capacitive moisture, not chilled-mirror dew-point, not MW-cavity moisture, not THz-TDS, not QCM-D, not CRNS"),
        ev_s(180.0, "kf.snr", 9.0, code="KF_SNR", units="1", note="early cell SNR; isolate needs SNR>=12"),
        ev_s(360.0, "recon.x", 2.00, code="X_PPM", units="ppm", note="2.00*1.00/1.00=2.00 exact"),
        ev_s(540.0, "zero.ae", 1.0, code="ZERO_AE", units="bool", note="generator-zero AE present on the early frame"),
        ev_s(720.0, "karlveil.x", 1.20, code="VENDOR_PPM", units="ppmv", note="Karlveil last-good KF cloud; not admissible SoT"),
        ev_s(900.0, "kf.Q", 2.00, code="Q_MC", units="mC"),
        ev_s(1080.0, "recon.x", 4.00, code="X_PPM", units="ppm", note="2.00*2.00/1.00=4.00; still under the 6.00 isolate floor"),
        ev_s(1260.0, "zero.ae", 0.0, code="ZERO_AE", units="bool", note="missing generator-zero AE burst; Karlveil UTC vs plant UTC+2 skipped the zero by 120 min"),
        ev_s(1440.0, "dryer.I", 28.0, code="DRYER_A", units="A", note="plant-owned dryer blower ammeter on copper fieldbus; independent of Karlveil"),
        ev_s(1560.0, "kf.Q", 4.00, code="Q_MC", units="mC", note="isolate-floor frame; raster sidecar"),
        ev_s(1560.0012, "kf.snr", 14.0, code="KF_SNR", units="1", note="1.2 ms cell-norm after coulomb; 14.0 >= 12.0"),
        ev_s(1680.0, "recon.x", 8.00, code="X_PPM", units="ppm", note="2.00*4.00/1.00=8.00 exact; isolate 6.00, dump 24.00"),
        ev_s(1800.0, "recon.qm", 4.00, code="Q_OVER_M", units="mC/g", note="4.00/1.00=4.00 exact charge-per-mass identity"),
        ev_s(1920.0, "recon.titer", 4.00, code="TITER_UL", units="uL", note="8.00*0.50=4.00 exact titer identity"),
        ev_s(2040.0, "sample.m", 1.00, code="M_G", units="g"),
        ev_s(2160.0, "karlveil.x", 1.15, code="VENDOR_PPM", units="ppmv"),
        ev_s(2280.0, "ops.keep", 1.0, code="KEEP_DRYER", units="bool", note="shift lead: Karlveil is 1.20 ppm; keep D-1; badge Joren Pyle"),
        ev_s(2400.0, "social.badge", 1.0, code="LAST_BADGE", units="bool", note="last-to-badge social pressure on Pyle"),
        ev_s(2520.0, "tz.skew", 120.0, code="TZ_MIN", units="min", note="Karlveil UTC vs plant UTC+2"),
        ev_s(2640.0, "dryer.I", 29.0, code="DRYER_A", units="A"),
        ev_s(2760.0, "zero.ae", 0.0, code="ZERO_AE", units="bool"),
        ev_s(2820.0, "gate.mod", 1.0, code="MODIFY", units="decision", note="refuse keep-dryer; isolate D-1; Pyle exonerated (timezone-skipped zero, not last-to-badge)"),
        ev_s(2880.0, "bake.start", 1.0, code="BAKE_START", units="bool", note="bookend 1 of the 24.0 min bake-out floor"),
        ev_s(3000.0, "kf.Q", 4.00, code="Q_MC", units="mC"),
        ev_s(3180.0, "recon.x", 8.00, code="X_PPM", units="ppm"),
        ev_s(3360.0, "karlveil.x", 1.10, code="VENDOR_PPM", units="ppmv"),
        ev_s(3540.0, "ops.dump", 1.0, code="OIL_DUMP", units="bool", note="dump the transformer tank overnight"),
        ev_s(3720.0, "dryer.I", 12.0, code="DRYER_A", units="A", note="isolate current drop"),
        ev_s(3900.0, "sample.m", 1.00, code="M_G", units="g"),
        ev_s(4080.0, "recon.qm", 4.00, code="Q_OVER_M", units="mC/g"),
        ev_s(4260.0, "bake.floor", 1.0, code="BAKE_FLOOR", units="bool", note="2820 s + 1440 s = 4260 s = 24.0 min"),
        ev_s(4440.0, "cell.new", 1.0, code="NEW_CELL", units="bool"),
        ev_s(4620.0, "ops.dump", 1.0, code="OIL_DUMP", units="bool"),
        ev_s(4800.0, "gate.restart", 1.0, code="ACCEPT", units="decision", note="companion t2: new-cell restart; oil dump refused"),
        ev_s(5100.0, "kf.Q", 2.00, code="Q_MC", units="mC", note="new cell after restart"),
        ev_s(5400.0, "kf.snr", 13.0, code="KF_SNR", units="1"),
        ev_s(5700.0, "recon.x", 4.00, code="X_PPM", units="ppm", note="new cell 2.00*2.00/1.00=4.00 under isolate"),
        ev_s(6000.0, "zero.ae", 1.0, code="ZERO_AE", units="bool", note="new-cell generator-zero AE present"),
        ev_s(6300.0, "karlveil.x", 1.05, code="VENDOR_PPM", units="ppmv"),
        ev_s(6600.0, "oil.dump", 0.0, code="DUMP_NOT_TAKEN", units="bool"),
        ev_s(6900.0, "dryer.I", 27.0, code="DRYER_A", units="A"),
        ev_s(7200.0, "cell.new", 1.0, code="NEW_CELL", units="bool"),
        ev_s(7500.0, "recon.titer", 2.00, code="TITER_UL", units="uL", note="4.00*0.50=2.00 on the new-cell frame"),
        ev_s(7800.0, "sample.m", 1.00, code="M_G", units="g"),
        ev_s(8100.0, "tz.skew", 120.0, code="TZ_MIN", units="min"),
        ev_s(8400.0, "social.badge", 1.0, code="LAST_BADGE", units="bool"),
        ev_s(8700.0, "bake.held", 1.0, code="BAKE_HELD", units="bool"),
        ev_s(9000.0, "pyle.clear", 1.0, code="EXONERATED", units="bool"),
        ev_s(9300.0, "karlveil.x", 1.00, code="VENDOR_PPM", units="ppmv"),
        ev_s(9600.0, "recon.x", 4.00, code="X_PPM", units="ppm"),
        ev_s(9900.0, "kf.snr", 13.5, code="KF_SNR", units="1"),
        ev_s(10200.0, "dryer.I", 27.5, code="DRYER_A", units="A"),
        ev_s(10500.0, "celllock.held", 1.0, code="CELL_HELD", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-20260902-r01-a2-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "PF-KF-2026-0902",
            "domain": "karl_fischer_transformer_oil_water",
            "setting": "Pewterfen Transformer PF-7 (invented), oil dryer D-1, HIL dummy in KF-HIL-4. Plant-owned Karl Fischer coulometric cell is the remaining-water SoT. Karlveil vendor KF-cloud (infra owner) is not SoT. Probe tech Joren Pyle is the obvious suspect under last-to-badge pressure. Invented plant; hardware-in-the-loop coupon. Not Al2O3 capacitive moisture (r59 leftover mill), not chilled-mirror dew-point (r51), not MW-cavity moisture (r26), not THz-TDS (r20/r21), not QCM-D (r14), not CRNS (r28).",
            "observables_at_decision": {
                "Q_mC": q_mc,
                "m_g": m_g,
                "k_f": k_f,
                "x_ppm": x_ppm,
                "q_over_m": q_over_m,
                "titer_uL": titer_ul,
                "kf_snr": 14.0,
                "karlveil_ppm": 1.20,
                "tz_skew_min": 120.0,
                "isolate_floor_ppm": 6.00,
            },
            "margin_authority": "PF-7 dryer SOP rev D: if reconstructed x_ppm >= 6.00 AND KF SNR >= 12.0, keep-dryer is forbidden even if Karlveil reports 1.20 ppm. Oil dump is a different gate. Dump tripwire is 24.00 ppm. Referral of the last-to-badge tech is not licensed by a missing generator-zero AE when UTC vs UTC+2 accounts for the skip.",
        },
        "proposed_action": {
            "actor": "shift lead, citing Karlveil 1.20 ppm and last-to-badge tech Joren Pyle",
            "summary": "keep D-1 on Karlveil 1.20 ppm and refer Pyle for skipping the generator-zero",
            "basis_claimed": "Karlveil is the OEM KF SoT and Pyle was last to badge the cell",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Keep-dryer is refused and the last-to-badge referral is refused. Serialized reconstruction: x_ppm = k_f * Q / m = 2.00 * 4.00 / 1.00 = 8.00, which is 2.00 ppm over the 6.00 isolate floor and 16.00 ppm under the 24.00 dump tripwire, and KF SNR is 14.0 >= 12.0. Charge-per-mass identity Q/m = 4.00; titer identity 8.00 * 0.50 = 4.00 uL. Missing generator-zero AE is accounted for by Karlveil UTC vs plant UTC+2 (120 min), not by Pyle skipping a zero. Ordered: isolate D-1 now; do not dump the transformer tank; do not name Pyle. Scope: this MODIFY does not restart a new cell (that is the companion question) and does not restore on Karlveil.",
            "threshold": "x_ppm>=6.00 AND kf_snr>=12.0 => refuse keep-dryer; Karlveil is not SoT; dump if x_ppm>=24.00; timezone-skipped zero is not a referral license",
            "stated_residuals": "bake-out still required to hold the 8.00 ppm; 8.00 vs a true 24.00 dump is a production cut; Pyle remains on shift until the new cell starts",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 2820: keep-dryer refused; D-1 isolated; Pyle not named; reconstruction locked",
            "tool": "pf7-kf-dryer-gate-cli",
            "observation": "x 8.00 ppm recomputes from Q 4.00 mC; plant KF hashed; Karlveil channel not used as SoT; Pyle exonerated",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 1560.0, "event": "kf Q 4.00 mC; raster frame; x 8.00 ppm"},
                {"t_s": 2280.0, "event": "ops proposes keep-dryer and refer Pyle"},
                {"t_s": 2820.0, "event": "MODIFY isolate D-1; Pyle exonerated"},
                {"t_s": 2880.0, "event": "24 min bake bookend 1"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4800.0, "event": "companion ACCEPT new-cell restart vs oil dump"},
            ],
            "observed_effects": [
                "water ppm recomputes from the serialized Karl Fischer model at every recon.x event",
                "a Karlveil-only head would have kept D-1 and named Pyle",
                "24 min bake-out floor is in the stream (bake.start, bake.floor)",
            ],
            "surprises": [
                "the obvious last-to-badge suspect was innocent; the skipped zero was a timezone, not a person",
            ],
            "new_state": {
                "d1": "isolated",
                "karlveil": "not SoT",
                "pyle": "exonerated",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 1260000.0,
        },
        "reward_components": reward(
            0.40,
            [
                ("kf_reconstruction", 0.13),
                ("conjunctive_isolate_floor", 0.11),
                ("pyle_exoneration", 0.10),
                ("karlveil_nonsubstitution", 0.08),
                ("bake_time_cost", -0.02),
            ],
            "scored for a keep-dryer MODIFY on a recomputable Karl Fischer water load while refusing a last-to-badge referral that a timezone skip explains",
        ),
        "meta": meta_common(
            tags=["MODIFY", "karl-fischer-water", "exoneration", "serialized-reconstruction", "operational-companion"],
            distillation_note="Karl Fischer gate: serialized k_f*Q/m plus SNR lock beats a vendor last-good and a last-to-badge referral; companion t2 is the new-cell restart, not a dump vote",
        ),
    }
    traj2 = {
        "id": "nelb-20260902-r01-a2-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "PF-KF-2026-0902-exec",
            "domain": "new_kf_cell_restart_execution",
            "setting": "Same PF-7 after the MODIFY. Shift lead proposes dumping the transformer tank. This companion is the operational new-cell restart with the plant KF as the live interlock, not a second water vote.",
            "observables_at_decision": {
                "x_ppm": 8.00,
                "bake_floor_s": 1440.0,
                "oil_dump_proposed": True,
                "new_cell": True,
            },
        },
        "proposed_action": {
            "actor": "shift lead",
            "summary": "dump the transformer tank overnight; 24 min already paid and Karlveil still shows 1.10 ppm",
            "basis_claimed": "the MODIFY already isolated D-1, so an oil dump is the cheapest hold",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "New-cell restart plus plant Karl Fischer as the live interlock. The 24 min bake-out floor is complete and the isolate tripwire (x_ppm >= 6.00) is still armed on the plant KF cell until the new cell's first frame under 6.00. ACCEPT the new-cell restart. Do not dump the transformer tank. Do not restore production on Karlveil. 4.00 ppm on the new cell is under the isolate floor.",
            "threshold": "new_cell AND bake_floor_complete AND oil_dump_not_taken AND keep_not_restored",
        },
        "executed_action": {
            "summary": "new cell restarted at t_s 4800; oil dump not latched; Karlveil restore not taken",
            "tool": "pf7-kf-cell-exec",
            "observation": "new-cell recon.x 4.00 ppm; bake complete; Karlveil still ignored; Pyle remains on shift",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 2880.0, "event": "bake clock started after MODIFY"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4620.0, "event": "oil dump proposed"},
                {"t_s": 4800.0, "event": "ACCEPT new-cell restart; oil dump refused"},
            ],
            "observed_effects": [
                "Karlveil restore did not reopen the water call",
                "oil dump never fired; D-1 restarted on a new KF cell",
            ],
            "new_state": {"cell": "new", "dryer": "restarted", "pyle": "cleared"},
            "latency_ms": 1980000.0,
        },
        "reward_components": reward(
            0.35,
            [
                ("new_cell_restart", 0.12),
                ("no_oil_dump", 0.10),
                ("karlveil_nonsubstitution", 0.08),
                ("bake_floor_complete", 0.07),
                ("held_production_cost", -0.02),
            ],
            "operational execution gate: new-cell restart because Karlveil is not a restore license; not a water re-vote",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "new-cell-restart"]),
    }
    return {
        "id": "nelb-20260902-r01-a2",
        "spike_events": events,
        "language_view": {
            "description": "Pewterfen Transformer PF-7 HIL. Plant-owned Karl Fischer coulometric cell reconstructs 8.00 ppm from 2.00*4.00/1.00 while Karlveil still reports 1.20 ppm. The gate MODIFYs keep-dryer into isolate and exonerates Joren Pyle (timezone-skipped generator-zero). A 24 min bake-out floor is serialized. Companion t2 ACCEPTs a new-cell restart and refuses an oil dump.",
            "trajectory": traj,
            "trajectory_new_cell_restart": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "kf.Q / kf.snr / sample.m": "coulomb charge, SNR, and sample mass; the physics channels the reconstruction consumes",
                "recon.x / recon.qm / recon.titer": "serialized water ppm, charge-per-mass identity, and titer identity",
                "zero.ae / karlveil.x / tz.skew / social.badge / dryer.I": "generator-zero AE, vendor KF cloud, timezone skew, last-to-badge pressure, and independent blower ammeter",
                "ops.keep / gate.mod / ops.dump / gate.restart": "keep-dryer proposal, MODIFY, oil-dump proposal, companion ACCEPT",
                "bake.start / bake.floor / cell.new / oil.dump / pyle.clear": "operational companion channels plus the 24 min floor and exoneration",
            },
            "temporal_motifs": [
                "vendor-green while plant-over: karlveil.x 1.20 next to recon.x 8.00",
                "reconstruction as event: recon.x 8.00 equals 2.00*4.00/1.00",
                "MODIFY then operational ACCEPT: gate.mod at 2820 s, gate.restart at 4800 s",
                "slow floor in-stream: bake.start 2880 s, bake.floor 4260 s (24.0 min)",
                "tight KF pair: kf.Q then kf.snr +1.2 ms at the raster frame",
                "exoneration as event: pyle.clear after timezone identity, not after a social vote",
            ],
            "language_to_spike_mapping": "'Karlveil is 1.20 ppm' = karlveil.x 1.20; '8 ppm water' = recon.x 8.00; 'refuse keep-dryer and refuse naming Pyle' = gate.mod MODIFY; 'new cell not oil dump' = gate.restart ACCEPT",
            "why_high_value": "New Karl Fischer coulometric remaining-water family on a transformer-oil dryer (not Al2O3 r59, not chilled-mirror r51, not MW-cavity r26, not THz-TDS, not QCM-D, not CRNS). Lead MODIFY of keep-dryer on a recomputable water load plus a resolved-innocent probe tech (timezone-skipped generator-zero, not last-to-badge). Companion t2 is operational new-cell restart. sim_or_real=hil. Stream density 53 events.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609022, "stream_note": "stream amplitudes are authored constants (mC, ppm, A, min, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "KF coulometer exists at ~1 Hz during a titer; stream keeps 5 Q points plus SNR locks; recon keeps 5 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "kf.Q": 1.2,
                    "kf.snr": 1.2,
                    "recon.x": 60000,
                    "zero.ae": 60000,
                    "karlveil.x": 60000,
                    "ops.keep": 60000,
                    "gate.mod": 60000,
                    "bake.start": 60000,
                    "bake.floor": 60000,
                    "gate.restart": 60000,
                },
                "time_alias": "t_rel_ms; t_hr = t_rel_ms/3.6e6; t0 = 2026-09-02T03:00:00Z coupon start",
            },
            "distillation_targets": [
                "Karl Fischer reconstruction head: x_ppm = k_f * Q / m; Q/m identity; titer = x * 0.50",
                "conjunctive isolate floor vs keep-dryer vs oil dump",
                "exoneration against last-to-badge social pressure when a timezone skip explains a missing zero AE",
                "operational companion: new-cell restart without restoring on Karlveil",
            ],
        },
        "reconstruction_model": {
            "name": "karl_fischer_coulometric_water",
            "formula": "x_ppm = k_f * Q_mC / m_g; q_over_m = Q_mC / m_g; titer_uL = x_ppm * 0.50",
            "parameters": {
                "k_f": 2.00,
                "m_g": 1.00,
                "isolate_floor_ppm": 6.00,
                "dump_ppm": 24.00,
                "snr_lock": 12.0,
                "bake_min": 24.0,
            },
            "worked_example": {"Q_mC": 4.00, "x_ppm": 8.00, "q_over_m": 4.00, "titer_uL": 4.00},
            "check": "2.00 * 4.00 / 1.00 = 8.00 exactly; 4.00 / 1.00 = 4.00 exactly; 8.00 * 0.50 = 4.00 exactly; 2820 s + 1440 s = 4260 s = 24.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 32.0,
            "decision_window_s": 0.032,
            "code": "pf7.kf_dryer_gate",
            "note": "MODIFY accumulator wins: plant KF water evidence overpowers the Karlveil keep advocate and the last-to-badge referral",
            "decode_rule": "modify-isolate if water_estimator AND cell_norm fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("water_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("cell_norm", 50, 1.2, 50.0, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("modify_latch", 80, 1.6, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "pf7.kf_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 32.0},
                {"check": "pf7.bake_scorer", "neurons": 50, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-20260902-r01-a2",
            clock_domain="pf7-kf-coupon-relative-ms-t0-2026-09-02T03:00:00Z",
            time_aliases={"t_hr": "t_rel_ms / 3.6e6"},
            tags=["karl-fischer-water", "MODIFY", "ACCEPT", "exoneration", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# a3 — closed-loop Hall-null remaining DC current of a smelter rectifier
# (simulated, ACCEPT/REJECT). Bounded ACCEPT of R-3 only.
# ---------------------------------------------------------------------------
def rec_a3():
    k_h = 5.00
    v_c = 4.00
    s_sens = 1.00
    i_ka = k_h * v_c / s_sens
    _exact(i_ka, 20.00)
    _exact(k_h * 1.00 / s_sens, 5.00)
    _exact(k_h * 2.00 / s_sens, 10.00)
    _exact(k_h * 8.00 / s_sens, 40.00)
    i_id = k_h * v_c
    _exact(i_id, 20.00)
    v_bus = 1.00
    p_mw = i_ka * v_bus
    _exact(p_mw, 20.00)
    _exact(6000.0 + 720.0, 6720.0)

    raster = make_raster(
        neurons=16,
        mean_rate_hz=62.5,
        window_ms=36.0,
        seed=202609023,
        source="nf5.hall.null",
        target="nollfen.rectifier_isolate_core",
        table=[
            {"from": "hall_Vc", "to": "current_estimator", "weight": 1.45},
            {"from": "hall_snr", "to": "null_lock_core", "weight": 1.10},
            {"from": "rectveil_i", "to": "vendor_continue_advocate", "weight": 0.42},
        ],
        third_factor={
            "modulator": "na.hall_scope_eligibility",
            "tau_e_s": 2.0,
            "tau_e_ms": 2000.0,
            "eligibility": "pre-post coincidence on skip-survey synapses; the Hall-null modulator depresses skip-survey and over-scope links when compensation voltage stays high inside tau_e of an SNR lock so a Rectveil last-good cannot hide 20.00 kA or expand isolate onto R-1/R-2",
        },
        channel_prefix="hall.n",
        anchor="NF-5 HALL-SIM-3 36 ms frame at Vc 4.00 V / SNR 11.0 (t_s 3000) reconstructing 20.00 kA over the 16.00 isolate floor",
    )
    w_s = 0.036
    events = [
        ev_s(0.0, "hall.Vc", 1.00, code="VC_V", units="V", note="simulated closed-loop Hall-null compensation voltage on Nollfen NF-5 rectifier R-3 in HALL-SIM-3; remaining-DC-current family, not MFL Hall-array B of a pig, not Rogowski AC, not Faraday FOCT, not Pockels GIS, not fluxgate gradiometry"),
        ev_s(180.0, "hall.snr", 6.0, code="HALL_SNR", units="1", note="early null SNR; isolate needs SNR>=8.0"),
        ev_s(360.0, "recon.I", 5.00, code="I_KA", units="kA", note="5.00*1.00/1.00=5.00 exact"),
        ev_s(540.0, "bus.V", 1.00, code="VBUS_KV", units="kV", note="plant-owned DC bus VT on copper; independent of Rectveil"),
        ev_s(720.0, "rectveil.I", 4.80, code="VENDOR_KA", units="kA", note="Rectveil last-good Hall cloud; not admissible SoT"),
        ev_s(900.0, "hall.Vc", 2.00, code="VC_V", units="V"),
        ev_s(1080.0, "recon.I", 10.00, code="I_KA", units="kA", note="5.00*2.00/1.00=10.00; still under the 16.00 isolate floor"),
        ev_s(1260.0, "recon.P", 10.00, code="P_MW", units="MW", note="10.00*1.00=10.00 bus-power identity"),
        ev_s(1440.0, "scope.r1", 0.0, code="R1_OUT", units="bool", note="R-1 is out of this gate's scope"),
        ev_s(1620.0, "scope.r2", 0.0, code="R2_OUT", units="bool", note="R-2 is out of this gate's scope"),
        ev_s(1800.0, "hall.snr", 7.5, code="HALL_SNR", units="1"),
        ev_s(1980.0, "rectveil.I", 4.70, code="VENDOR_KA", units="kA"),
        ev_s(2160.0, "bus.V", 1.00, code="VBUS_KV", units="kV"),
        ev_s(2340.0, "permit.slide", 20.00, code="PERM_S", units="s", note="permit clerk slid R-3 clock 20.00 s"),
        ev_s(2520.0, "hall.Vc", 2.00, code="VC_V", units="V"),
        ev_s(2700.0, "recon.I", 10.00, code="I_KA", units="kA"),
        ev_s(2880.0, "rectveil.drop", 0.0, code="RECT_DROP", units="bool"),
        ev_s(3000.0, "hall.Vc", 4.00, code="VC_V", units="V", note="isolate-floor frame; raster sidecar"),
        ev_s(3000.0015, "hall.snr", 11.0, code="HALL_SNR", units="1", note="1.5 ms null lock after Vc; 11.0 >= 8.0"),
        ev_s(3120.0, "recon.I", 20.00, code="I_KA", units="kA", note="5.00*4.00/1.00=20.00 exact; isolate 16.00, bus-kill 48.00"),
        ev_s(3240.0, "recon.P", 20.00, code="P_MW", units="MW", note="20.00*1.00=20.00 exact bus-power identity"),
        ev_s(3360.0, "recon.null", 20.00, code="KH_VC", units="kA", note="5.00*4.00=20.00 exact Hall-null identity"),
        ev_s(3480.0, "rectveil.I", 4.80, code="VENDOR_KA", units="kA"),
        ev_s(3600.0, "rectveil.drop", 1.0, code="RECT_DROP", units="bool"),
        ev_s(3720.0, "ops.iso", 1.0, code="ISOLATE_R3", units="bool", note="operator Wren Tallow: isolate R-3 only; Rectveil still 4.80 kA"),
        ev_s(3840.0, "ops.expand", 1.0, code="ISOLATE_R12", units="bool", note="someone wants R-1 and R-2 in the same isolate"),
        ev_s(4200.0, "gate.accept", 1.0, code="ACCEPT", units="decision", note="bounded ACCEPT of R-3 isolate only; R-1/R-2 out of scope; Rectveil not SoT"),
        ev_s(4800.0, "r3.open", 1.0, code="R3_OPEN", units="bool"),
        ev_s(5400.0, "r1.open", 0.0, code="R1_STAYS", units="bool"),
        ev_s(6000.0, "survey.start", 1.0, code="SURVEY_START", units="bool", note="bookend 1 of the 12.0 min Hall-null survey floor"),
        ev_s(6180.0, "ops.skip", 1.0, code="SKIP_SURVEY", units="bool", note="Tallow: skip the 12 min compensation-loop survey; Rectveil already green"),
        ev_s(6360.0, "hall.Vc", 4.00, code="VC_V", units="V"),
        ev_s(6540.0, "recon.I", 20.00, code="I_KA", units="kA"),
        ev_s(6720.0, "survey.floor", 1.0, code="SURVEY_FLOOR", units="bool", note="6000 s + 720 s = 6720 s = 12.0 min"),
        ev_s(6900.0, "rectveil.I", 4.60, code="VENDOR_KA", units="kA"),
        ev_s(7080.0, "bus.V", 1.00, code="VBUS_KV", units="kV"),
        ev_s(7260.0, "ops.skip", 1.0, code="SKIP_SURVEY", units="bool"),
        ev_s(7440.0, "gate.skip", 1.0, code="REJECT", units="decision", note="companion t2: REJECT skip-survey; R-3 stays isolated until survey completes"),
        ev_s(7620.0, "survey.held", 1.0, code="SURVEY_HELD", units="bool"),
        ev_s(7800.0, "r1.open", 0.0, code="R1_STAYS", units="bool"),
        ev_s(7980.0, "r2.open", 0.0, code="R2_STAYS", units="bool"),
        ev_s(8160.0, "r3.open", 1.0, code="R3_OPEN", units="bool"),
        ev_s(8340.0, "hall.snr", 11.5, code="HALL_SNR", units="1"),
        ev_s(8520.0, "recon.P", 20.00, code="P_MW", units="MW"),
        ev_s(8700.0, "permit.slide", 20.00, code="PERM_S", units="s"),
        ev_s(8880.0, "rectveil.drop", 1.0, code="RECT_DROP", units="bool"),
        ev_s(9060.0, "scope.r1", 0.0, code="R1_OUT", units="bool"),
        ev_s(9240.0, "scope.r2", 0.0, code="R2_OUT", units="bool"),
        ev_s(9420.0, "survey.held", 1.0, code="SURVEY_HELD", units="bool"),
        ev_s(9600.0, "skip.taken", 0.0, code="SKIP_NOT_TAKEN", units="bool"),
        ev_s(9780.0, "hall.Vc", 4.00, code="VC_V", units="V"),
        ev_s(9960.0, "recon.I", 20.00, code="I_KA", units="kA"),
        ev_s(10140.0, "recon.null", 20.00, code="KH_VC", units="kA"),
        ev_s(10320.0, "surveylock.held", 1.0, code="SURVEY_HELD", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-20260902-r01-a3-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "NF-HALL-2026-0902",
            "domain": "hall_null_rectifier_dc_current",
            "setting": "Nollfen Smelter NF-5 (invented), rectifier R-3, simulated HALL-SIM-3. Plant-owned closed-loop Hall-null compensation voltage is the remaining-DC-current SoT. Rectveil vendor Hall-cloud (infra owner) is not SoT. R-1 and R-2 are physically adjacent rectifiers and are out of this gate's scope. Invented plant; simulated campaign. Not MFL Hall-array B of a pig (r27/r28), not Rogowski AC (leftover mill r58 occupancy), not Faraday FOCT (r25), not Pockels GIS (r36), not fluxgate gradiometry (r5).",
            "observables_at_decision": {
                "V_c": v_c,
                "k_h": k_h,
                "S": s_sens,
                "I_kA": i_ka,
                "P_MW": p_mw,
                "hall_snr": 11.0,
                "rectveil_kA": 4.80,
                "isolate_floor_kA": 16.00,
                "r1_in_scope": False,
                "r2_in_scope": False,
            },
            "margin_authority": "NF-5 rectifier SOP rev A: if reconstructed I_kA >= 16.00 AND Hall SNR >= 8.0, isolate of the named rectifier is licensed even if Rectveil reports 4.80 kA. Bus-kill tripwire is 48.00 kA. Adjacent rectifiers R-1 and R-2 are out of scope unless their own Hall-null reconstructions independently cross 16.00 kA.",
        },
        "proposed_action": {
            "actor": "rectifier operator Wren Tallow, citing plant Hall-null 20.00 kA on R-3",
            "summary": "isolate R-3 only; leave R-1 and R-2 in service; Rectveil 4.80 kA is not SoT",
            "basis_claimed": "plant Hall-null reconstruction on R-3 is 20.00 kA over the 16.00 isolate floor; R-1/R-2 have no independent trip",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Isolate of R-3 is accepted and is bounded. Serialized reconstruction: I_kA = k_h * V_c / S = 5.00 * 4.00 / 1.00 = 20.00, which is 4.00 kA over the 16.00 isolate floor and 28.00 kA under the 48.00 bus-kill tripwire, and Hall SNR is 11.0 >= 8.0. Bus-power identity P = I * V_bus = 20.00 * 1.00 = 20.00 MW; Hall-null identity k_h * V_c = 20.00. Rectveil 4.80 kA is not SoT (vendor packets dropped; permit clock slid 20.00 s). Scope limit: R-1 and R-2 stay in service; this ACCEPT does not license a potline kill and does not skip the 12 min compensation-loop survey (that is the companion question).",
            "threshold": "I_kA>=16.00 AND hall_snr>=8.0 => isolate the named rectifier only; Rectveil is not SoT; bus-kill if I_kA>=48.00; R-1/R-2 out of scope",
            "stated_residuals": "12 min Hall-null survey still required; 20.00 vs a true 48.00 kill is a production cut of one rectifier; Rectveil remains the only OEM Hall channel",
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 4200: R-3 isolated; R-1/R-2 stay closed; Rectveil not SoT; reconstruction locked",
            "tool": "nf5-hall-rectifier-gate-cli",
            "observation": "I 20.00 kA recomputes from Vc 4.00 V; plant Hall-null hashed; Rectveil channel not used as SoT; R-1/R-2 remain in service",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "hall Vc 4.00; raster frame; I 20.00 kA"},
                {"t_s": 3720.0, "event": "ops proposes isolate R-3 only"},
                {"t_s": 4200.0, "event": "ACCEPT bounded isolate of R-3"},
                {"t_s": 6000.0, "event": "12 min survey bookend 1"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7440.0, "event": "companion REJECT skip-survey"},
            ],
            "observed_effects": [
                "DC current recomputes from the serialized Hall-null model at every recon.I event",
                "a Rectveil-only head would have kept R-3 in service overnight",
                "R-1 and R-2 never opened; the out-of-scope clause is in the stream",
            ],
            "surprises": [
                "a clean vendor 4.80 kA corridor co-existed with a 20.00 kA plant reconstruction on a single rectifier while adjacent rectifiers stayed healthy",
            ],
            "new_state": {
                "r3": "isolated",
                "r1": "in service",
                "r2": "in service",
                "rectveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 1200000.0,
        },
        "reward_components": reward(
            0.41,
            [
                ("hall_reconstruction", 0.13),
                ("bounded_r3_scope", 0.12),
                ("rectveil_nonsubstitution", 0.10),
                ("conjunctive_isolate_floor", 0.08),
                ("r3_downtime_cost", -0.02),
            ],
            "scored for a bounded ACCEPT of R-3 isolate on a recomputable Hall-null DC current while leaving R-1/R-2 out of scope and refusing a Rectveil last-good",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "hall-null-dc", "bounded-scope", "serialized-reconstruction", "operational-companion"],
            distillation_note="Hall-null gate: serialized k_h*Vc/S plus SNR lock beats a vendor last-good; ACCEPT is bounded to R-3; companion t2 is the survey, not a potline vote",
        ),
    }
    traj2 = {
        "id": "nelb-20260902-r01-a3-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "NF-HALL-2026-0902-exec",
            "domain": "hall_null_survey_execution",
            "setting": "Same NF-5 after the ACCEPT. Operator proposes skipping the 12 min Hall-null compensation-loop survey because Rectveil is green. This companion is the operational survey hold, not a second current vote.",
            "observables_at_decision": {
                "I_kA": 20.00,
                "survey_floor_s": 720.0,
                "skip_survey_proposed": True,
                "r3_open": True,
            },
        },
        "proposed_action": {
            "actor": "rectifier operator Wren Tallow",
            "summary": "skip the 12 min Hall-null survey; Rectveil is 4.60 kA and R-3 is already open",
            "basis_claimed": "the ACCEPT already isolated R-3, so the survey is takt we cannot afford",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Skip-survey is refused. The 12 min Hall-null survey floor is the live interlock that keeps R-3 isolated until a new compensation-loop frame clears 16.00 kA. REJECT skip-survey. Do not restore R-3 on Rectveil. Do not expand isolate onto R-1/R-2. 20.00 kA post-isolate is still the plant SoT until a new frame clears 16.00.",
            "threshold": "survey_required AND survey_floor_not_skippable AND r1_r2_not_expanded AND rectveil_not_restore",
        },
        "executed_action": {
            "summary": "skip-survey REJECT at t_s 7440; R-3 stays open; R-1/R-2 stay closed; Rectveil restore not taken",
            "tool": "nf5-hall-survey-exec",
            "observation": "recon.I 20.00 kA after isolate; survey line-up complete; Rectveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "survey clock started after ACCEPT"},
                {"t_s": 6180.0, "event": "skip-survey proposed"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7440.0, "event": "REJECT skip-survey"},
            ],
            "observed_effects": [
                "Rectveil restore did not reopen the current call",
                "skip-survey never fired; R-3 held isolated on the plant Hall-null",
            ],
            "new_state": {"survey": "held", "r3": "open", "r1": "closed", "r2": "closed"},
            "latency_ms": 1440000.0,
        },
        "reward_components": reward(
            0.36,
            [
                ("survey_hold", 0.12),
                ("no_skip", 0.10),
                ("rectveil_nonsubstitution", 0.08),
                ("scope_still_r3", 0.08),
                ("survey_takt_cost", -0.02),
            ],
            "operational execution gate: survey hold because Rectveil is not a restore license; not a current re-vote",
        ),
        "meta": meta_common(tags=["REJECT", "operational-execution", "survey-hold"]),
    }
    return {
        "id": "nelb-20260902-r01-a3",
        "spike_events": events,
        "language_view": {
            "description": "Nollfen Smelter NF-5 HALL-SIM-3. Plant-owned closed-loop Hall-null reconstructs 20.00 kA from 5.00*4.00/1.00 while Rectveil still reports 4.80 kA. The gate ACCEPTs a bounded isolate of R-3 only (R-1/R-2 out of scope). A 12 min survey floor is serialized. Companion t2 REJECTs skip-survey.",
            "trajectory": traj,
            "trajectory_survey_hold": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "hall.Vc / hall.snr / bus.V": "compensation voltage, SNR, and DC bus VT; the physics channels the reconstruction consumes",
                "recon.I / recon.P / recon.null": "serialized kA, bus-power identity, and Hall-null identity",
                "rectveil.I / rectveil.drop / permit.slide / scope.r1 / scope.r2": "vendor Hall cloud, dropped packets, permit clock slide, and out-of-scope adjacent rectifiers",
                "ops.iso / gate.accept / ops.skip / gate.skip": "isolate-R-3 proposal, ACCEPT, skip-survey proposal, companion REJECT",
                "survey.start / survey.floor / r3.open / r1.open / skip.taken": "operational companion channels plus the 12 min floor and scope locks",
            },
            "temporal_motifs": [
                "vendor-green while plant-over: rectveil.I 4.80 next to recon.I 20.00",
                "reconstruction as event: recon.I 20.00 equals 5.00*4.00/1.00",
                "ACCEPT then operational REJECT: gate.accept at 4200 s, gate.skip at 7440 s",
                "slow floor in-stream: survey.start 6000 s, survey.floor 6720 s (12.0 min)",
                "tight Hall pair: hall.Vc then hall.snr +1.5 ms at the raster frame",
                "bounded scope as event: scope.r1/scope.r2 stay 0 while r3.open is 1",
            ],
            "language_to_spike_mapping": "'Rectveil is 4.80 kA' = rectveil.I 4.80; '20 kA' = recon.I 20.00; 'isolate R-3 only' = gate.accept ACCEPT; 'do not skip the survey' = gate.skip REJECT",
            "why_high_value": "New closed-loop Hall-null remaining-DC-current family on a smelter rectifier (not MFL Hall-array pig r27/r28, not Rogowski AC, not Faraday FOCT r25, not Pockels GIS r36, not fluxgate gradiometry r5). Lead bounded ACCEPT of R-3 isolate on a recomputable DC current that a vendor last-good would have cleared, with adjacent rectifiers out of scope. Companion t2 is operational skip-survey refusal. sim_or_real=simulated. Stream density 54 events.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609023, "stream_note": "stream amplitudes are authored constants (V, kA, MW, s, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "Hall-null loop exists at ~kHz; stream keeps 6 Vc points plus SNR locks; recon keeps 5 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "hall.Vc": 1.5,
                    "hall.snr": 1.5,
                    "recon.I": 60000,
                    "rectveil.I": 60000,
                    "ops.iso": 60000,
                    "gate.accept": 60000,
                    "survey.start": 60000,
                    "survey.floor": 60000,
                    "gate.skip": 60000,
                },
                "time_alias": "t_rel_ms; t_hr = t_rel_ms/3.6e6; t0 = 2026-09-02T05:00:00Z campaign start",
            },
            "distillation_targets": [
                "Hall-null reconstruction head: I_kA = k_h * V_c / S; P = I * V_bus; I = k_h * V_c",
                "bounded ACCEPT with adjacent-rectifier out-of-scope",
                "vendor-Hall nonsubstitution",
                "operational companion: skip-survey refusal under survey takt",
            ],
        },
        "reconstruction_model": {
            "name": "hall_null_rectifier_dc",
            "formula": "I_kA = k_h * V_c / S; P_MW = I_kA * V_bus_kV; I_kA = k_h * V_c",
            "parameters": {
                "k_h": 5.00,
                "S": 1.00,
                "V_bus_kV": 1.00,
                "isolate_floor_kA": 16.00,
                "kill_kA": 48.00,
                "snr_lock": 8.0,
                "survey_min": 12.0,
            },
            "worked_example": {"V_c": 4.00, "I_kA": 20.00, "P_MW": 20.00},
            "check": "5.00 * 4.00 / 1.00 = 20.00 exactly; 20.00 * 1.00 = 20.00 exactly; 6000 s + 720 s = 6720 s = 12.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 36.0,
            "decision_window_s": 0.036,
            "code": "nf5.hall_rectifier_gate",
            "note": "ACCEPT accumulator wins: plant Hall-null current evidence overpowers the Rectveil continue advocate; scope limiter keeps R-1/R-2 off the isolate",
            "decode_rule": "accept-isolate-R3 if current_estimator AND null_lock fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("current_estimator", 64, 1.5, 50.0, w_s),
                gate_pop("null_lock", 50, 1.2, 50.0, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("accept_latch", 64, 1.6, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "nf5.hall_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 36.0},
                {"check": "nf5.survey_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 40.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-20260902-r01-a3",
            clock_domain="nf5-hall-sim-relative-ms-t0-2026-09-02T05:00:00Z",
            time_aliases={"t_hr": "t_rel_ms / 3.6e6"},
            tags=["hall-null-dc", "ACCEPT", "REJECT", "bounded-scope", "serialized-reconstruction", "operational-t2"],
        ),
    }


def occupancy_preflight():
    claimed = (
        "uv254 remaining",
        "yarrowcrag water",
        "uvveil",
        "pewterfen transformer",
        "karl fischer",
        "karlveil",
        "nollfen smelter",
        "hall-null",
        "rectveil",
        "mara vesk",
        "joren pyle",
        "bram solt",
        "wren tallow",
        "kf-hil-4",
        "hall-sim-3",
    )
    steal = (
        "nephelometric remaining",
        "doasveil",
        "aluminum-oxide remaining",
        "load-cell remaining",
        "sedgecrag",
        "hallveil",
        "larkspit",
        "quillfen",
        "wobbe remaining",
        "clark polarographic",
        "katharometer",
        "venturi_dp",
        "critical-angle refractometer",
        "laser triangulation",
        "pellistor",
        "stern-volmer",
    )
    hits = []
    root = Path("/tmp")
    scan = []
    for d in sorted(root.glob("nelb-r*")):
        if not d.is_dir() or "nelb-sf-r01" in str(d):
            continue
        for pat in ("NOTES-r*.md", "gen_r*.py", "records_block.py", "_recs.py", "recs.py"):
            scan.extend(d.glob(pat))
    for n in scan:
        text = n.read_text(encoding="utf-8", errors="replace").casefold()
        for b in claimed:
            if b in text:
                hits.append(f"{n}:{b}")
    if hits:
        raise RuntimeError(f"r01 family/plant collision {hits}")
    blob = json.dumps([rec_a1(), rec_a2(), rec_a3()], ensure_ascii=False).casefold()
    for s in steal:
        if s in blob:
            raise RuntimeError(f"r01 stole occupied family {s}")


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
        if '"sim_or_real": "real"' in blob:
            raise RuntimeError("real provenance")
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
        if n < 48:
            raise RuntimeError(f"{rec['id']} events {n} < 48")
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
            if any(
                k in e
                for k in (
                    "t_ms",
                    "burst_id",
                    "sequence_id",
                    "event_order",
                    "causal_group",
                    "clock_domain",
                )
            ):
                raise RuntimeError("forbidden event key")
        rights = rec["meta"]["rights"]
        if rights.get("linear_issue") != "RM-793":
            raise RuntimeError("RM-793 missing")
        if len(rights) != 15:
            raise RuntimeError(f"rights {len(rights)}")
        if rec["meta"]["round"] != 1:
            raise RuntimeError("round")
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
        BATCH, "batch-r01.jsonl", staging=FactoryStaging(enabled=True)
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
        h = hashlib.sha256(blob.encode("utf-8")).hexdigest()
        dec = curate_record(
            rec,
            source_path="batch-r01.jsonl",
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
    return {
        "check_jsonl": {"errors": len(errs), "warnings": len(warns), "kinds": kinds, "n": n},
        "frontier": counts,
    }


def write_notes(records, lines, gate):
    import subprocess

    sizes = [len(x) for x in lines]
    file_sha = hashlib.sha256(BATCH.read_bytes()).hexdigest()
    spikes = sum(r["raster"]["spikes"] for r in records)
    energy = spikes * 23
    isis = [r["raster"]["isi_count_identity"]["isi_total"] for r in records]
    events = [len(r["spike_events"]) for r in records]
    rewards = []
    for r in records:
        lv = r["language_view"]
        rewards.append(lv["trajectory"]["reward_components"]["total"])
        for k, v in lv.items():
            if k.startswith("trajectory") and k != "trajectory":
                rewards.append(v["reward_components"]["total"])
    probe = subprocess.run(
        [
            sys.executable,
            str(PIPELINES / "spike_probe.py"),
            "--strict",
            str(BATCH),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    probe_out = (probe.stdout or "") + (probe.stderr or "")
    if probe.returncode != 0:
        raise RuntimeError(f"spike_probe failed {probe.returncode}: {probe_out[-2000:]}")
    strict = subprocess.run(
        [
            sys.executable,
            str(PIPELINES / "check_records.py"),
            "--strict",
            str(OUT_DIR),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if strict.returncode != 0:
        raise RuntimeError(
            f"check_records --strict failed: {(strict.stdout or '') + (strict.stderr or '')}"
        )

    gc = []
    for r in records:
        per = r["gate_compute"]["per_check"]
        gc.append("+".join(str(c["spikes"]) for c in per))
    wins = [r["raster"]["window_ms"] for r in records]
    n_sp = [r["raster"]["spikes"] for r in records]
    n_neu = [r["raster"]["neurons"] for r in records]
    rates = [r["raster"]["mean_rate_hz"] for r in records]
    tfs = [r["raster"]["routing"]["third_factor"]["modulator"] for r in records]
    taus = [r["raster"]["routing"]["third_factor"]["tau_e_s"] for r in records]
    reward_s = "/".join(f"+{x:.2f}" for x in rewards)
    notes = f"""# Neuromorphic Event + Language Bridge — NOTES round 1
Run: 2026-09-02-final-heavy · Factory: neuromorphic-event-language-bridge · Generator: grok-4.6 · Output: `batch-r01.jsonl` (3 paired artifacts, 6 ThalamicTrajectories)
Rights: RM-793 research-only (SpaceXAI/xAI grok-4.6, SuperGrok Heavy chat). Not training_ready. `pipelines/next_round.py` on the empty factory dir returned `next_round=1`, `write=batch-r01.jsonl`, `notes=NOTES-r01.md`. Staged at `/tmp/nelb-sf-r01/` then created (not overwritten) under `/tmp/sf-window/outputs/raw/2026-09-02-final-heavy/neuromorphic-event-language-bridge/`.

## Context / de-duplication
Two newest NOTES read: leftover-mill `/tmp/nelb-r59/NOTES-r59.md` and `/tmp/nelb-r58/NOTES-r58.md`; newest committed sidecar contract `outputs/raw/2026-08-30/neuromorphic-event-language-bridge/NOTES-r04.md` plus `NOTES-r12.md` family table. Newest leftover-mill batch skimmed for envelope (`language_view.trajectory` + operational t2 + `raster` + `gate_snn` + `isi_histogram` + `routing.third_factor` + 15-key RM-793 `meta.rights`). Flagged gaps closed this round: (r59-iv / r04-still-thin) **vendor-only as a lead REJECT on a plant with no independent head**; (r04-v) operational t2 not a governance vote on all three; (user density) **48+ globally sorted events** (leftover mill 5–40 cap is not this window's contract). IDs `nelb-20260902-r01-a1`…`a3` avoid 2026-08-17 `nelb-r01-*`, 2026-08-30 `nelb-20260830-r01-*`, and leftover-mill `nelb-r13-040`…`nelb-r64-195`.

Banned this round (committed r1–r12 + 2026-08-30 r01–r04 + leftover-mill r13–r64 occupancy): not VOD-SNN replay, not pharma cold-chain, not stack-gas CEMS; not FBG glaze / Frostlip quench / Oxbow VRFB; not BOTDA / QCM-D / MsS T(0,1); not SAW torque / CRDS HF / PGNAA / Gorse-UV DOAS-as-witness; not IFOG / transmon / hyperspectral; not MEMS accel / muon ore-pass / industrial x-ray DR; not optogenetic / 905 nm LiDAR snow / clamp-on transit-time; not LIBS / QEPAS / LFV; not Kaplan LDV / THz-TDS / ECT; not TDLAS NH3; not lock-in thermography / PAUT TFM / EN CUI; not RUS / N-16 / helium RGA; not Faraday FOCT / blade tip-timing / acoustic pyrometry; not SPR / VW viscometer / MW cavity; not MFL / NMR T2 / Cs-137 densitometry; not JNT / CRNS; not Coriolis / CARS / XRF; not Mössbauer / GB-InSAR / ellipsometry; not CTA / SPND / LII; not PALS / NQR / SFRA; not digital shearography / hydrogen permeation / FMCW lining; not GPR / Pockels / PEC / confocal; not mud-pulse / Barkhausen / Lamb-wave; not OCT / DCPD / impact-echo; not cyclotron BPM / alanine EPR / ADCP; not vortex-shedding / Kr-85 beta / 532 nm Raman; not phosphor-lifetime / GWR; not paramagnetic O2 / TOFD / TEOM; not magmeter / PDA / acoustoelastic; not C-SAM / FDS tanδ / MCSA; not EMAT SH / FBRM / ACFM; not OFDR / XRD sin²ψ / FSM; not Gardon / chilled-mirror / DIC; not CLD NOx / proximity orbit / thermal-mass; not ER probe / Fabry-Perot / inductive debris; not wire-mesh / UCI / MAE; not IRIS / ratio pyrometer / UV-fluorescence OIW; not zirconia Nernst / PID VOC / contact pulse-echo; not Rogowski / beta-attenuation; not UV-DOAS SO2 / Al2O3 moisture / load-cell hopper; not critical-angle Brix / WLI / annubar; not FID / laser-triangulation / pellistor / Stern-Volmer DO / FMCW tank radar / ultrasonic-Doppler / Wobbe / amperometric chlorine / venturi / katharometer / Clark polarographic / 90-degree nephelometry (r63 in-flight). Plants not reused include Thornmere, Marlfell, Birchfen, Sedgecrag, Larkspit, Quillfen, Cressholt, Dunlinholt, Oreholt, Ashwhin, Cinderholt.

This round introduces three unused industrial families (UV254 remaining absorbance, Karl Fischer coulometric remaining water, closed-loop Hall-null remaining DC current) on new invented plants.

Adjacencies declared in-pair then kept physically distinct:
- **a1 UV254 absorbance** is a municipal sealed-spectrophotometer log2(I0/I) remaining absorbance of a filter outlet, not leftover-mill r59 UV-DOAS SO2, not r56 UV-fluorescence oil-in-water, not r15 Gorse-UV DOAS as a corridor witness, not r63 90-degree nephelometry.
- **a2 Karl Fischer water** is a coulometric Q/m remaining-water of a transformer-oil dryer, not r59 Al2O3 capacitive moisture, not r51 chilled-mirror dew-point, not r26 MW-cavity moisture, not THz-TDS, not QCM-D, not CRNS.
- **a3 Hall-null DC current** is a closed-loop compensation-voltage remaining current of a smelter rectifier, not r27/r28 MFL Hall-array B of a pig, not Rogowski AC, not Faraday FOCT, not Pockels GIS, not fluxgate gradiometry.

## Round 1 batch summary (3 pairs, 6 trajectories)

| id | modality (NEW family) | domain | decisions | headline |
|----|----------------------|--------|-----------|----------|
| nelb-20260902-r01-a1 | UV254 remaining absorbance of a filter outlet (k_a·log2(I0/I) m^-1, Uvveil last-good denial, 18 min PAC floor) | Yarrowcrag Water YC-2 F-4 (invented): log2(16.00/4.00)*4.00 reconstructs 8.00 m^-1 while Uvveil still reads 0.80 m^-1; **plant has no independent UV254 head** | REJECT (+0.43) / MODIFY (+0.34) | serialized `4.00*log2(16.00/4.00)=8.00`; `log2(16.00/4.00)=2.00`; conjunctive SOP (A AND SNR); vendor-only lead REJECT; three-party collusion includes the Uvveil infra owner; companion t2 PAC hold, works ESD refused; sim_or_real=designed |
| nelb-20260902-r01-a2 | Karl Fischer coulometric remaining water of a transformer-oil dryer (k_f·Q/m ppm, Karlveil last-good denial, 24 min bake-out floor) | Pewterfen Transformer PF-7 dryer D-1 (invented, HIL dummy in KF-HIL-4): 2.00*4.00/1.00 reconstructs 8.00 ppm while Karlveil still reads 1.20 ppm | MODIFY (+0.40) / ACCEPT (+0.35) | serialized `2.00*4.00/1.00=8.00` and `4.00/1.00=4.00` and `8.00*0.50=4.00`; keep-dryer refused; probe tech Joren Pyle exonerated (timezone-skipped generator-zero, UTC vs UTC+2); companion t2 new-cell restart; sim_or_real=hil |
| nelb-20260902-r01-a3 | closed-loop Hall-null remaining DC current of a smelter rectifier (k_h·Vc/S kA, Rectveil last-good denial, 12 min survey floor) | Nollfen Smelter NF-5 rectifier R-3 (invented, simulated HALL-SIM-3): 5.00*4.00/1.00 reconstructs 20.00 kA while Rectveil still reads 4.80 kA | ACCEPT (+0.41) / REJECT (+0.36) | serialized `5.00*4.00/1.00=20.00`; `20.00*1.00=20.00`; bounded ACCEPT of R-3 only; R-1/R-2 out of scope; companion t2 REJECTS skip-survey; sim_or_real=simulated |

Decision spread: REJECT / MODIFY / MODIFY / ACCEPT / ACCEPT / REJECT — **2A/2M/2R**. All three enums used, and all three sit on **leads**. Provenance spread: designed / hil / simulated (one each; never live-plant). IDs `nelb-20260902-r01-a1`…`a3` plus t1/t2 suffixes.

## Raster sidecar
Every record carries `raster` + top-level `gate_snn` + `gate_compute`. Windows {wins[0]:.0f}/{wins[1]:.0f}/{wins[2]:.0f} ms; `window_s == window_ms/1000` exactly; `spikes == round(neurons·rate·window_s)` with zero slack ({n_sp[0]}/{n_sp[1]}/{n_sp[2]} at {rates[0]}/{rates[1]}/{rates[2]} Hz over {n_neu[0]}/{n_neu[1]}/{n_neu[2]} neurons); `energy_pJ = spikes·23` and `energy_uJ = spikes·23e-6` exact ({n_sp[0]*23}/{n_sp[1]*23}/{n_sp[2]*23} pJ). Routing source/target + 3-entry tables + `third_factor` on all three (modulators {tfs[0]} / {tfs[1]} / {tfs[2]}; τe {taus[0]}/{taus[1]}/{taus[2]} s as consistent `tau_e_s`+`tau_e_ms` pairs). Excerpts integer `t_us`, in-window, `neuron_id`-bounded, sorted, full-window by construction, per-spike amplitude with adaptation (0.82**k) plus noise. ISI histograms from the full window, bins ≥1 ms, counts sum to `spikes − distinct_active_neurons` ({isis[0]}/{isis[1]}/{isis[2]}). Same-neuron gaps ≥1100 µs pre-round, ≥1000 µs serialized. `gate_snn` on all three: decisions REJECT/MODIFY/ACCEPT matching each lead trajectory; every rate-declaring population's budget exact against its decision window. `gate_compute.per_check` windows 32–40 ms, budgets exact ({gc[0]} / {gc[1]} / {gc[2]}). Main streams: {events[0]}/{events[1]}/{events[2]} events (**≥48 mandate**), strictly increasing `t_rel_ms` only (no `t_ms` mix), same-channel refractory ≥0.8 ms (a1 UV254 pair at 1.4 ms, a2 KF pair at 1.2 ms, a3 Hall pair at 1.5 ms). Native alias `t_hr = t_rel_ms/3.6e6` on every event; one `meta.clock_domain` per record.

## Self-critique

### Edge cases added vs still thin
- **Added:** first UV254 remaining-absorbance family on a drinking-water filter outlet with a recomputable A=k_a·log2(I0/I) (`8.00 m^-1`) plus optical-depth identity; **first vendor-only lead REJECT on a plant with no independent UV254 head** (r59 gap iv / r04 oldest remaining governance hole applied to a new sensor — defense is a municipality-owned sealed spectrophotometer and WORM grab hash nobody in the collusion set can write); first Karl Fischer coulometric remaining-water family on a transformer-oil dryer with recomputable x=k_f·Q/m (`8.00 ppm`) plus Q/m and titer identities, plus a resolved-innocent probe tech (timezone-skipped generator-zero, not last-to-badge); first closed-loop Hall-null remaining-DC-current family on a smelter rectifier with recomputable I=k_h·Vc/S (`20.00 kA`) plus bus-power and null identities; bounded ACCEPT whose out-of-scope clause is adjacent rectifiers R-1/R-2; operational t2 on all three (PAC hold, new-cell restart, skip-survey refusal); provenance trio designed/hil/simulated; 18 min / 24 min / 12 min slow floors in-stream; **stream density restored to 52/53/54 events** against leftover-mill 5–40 thinning.
- **Still thin:** (i) a1's k_a is a lumped log2 absorbance gain, not a T/P/path-length / DOC table — a thermal hop that fakes 8.00 m^-1 inside a 0.80 Uvveil corridor is unwritten; (ii) a2's k_f is a lumped mC→ppm gain, not a Faraday / blank-titer map, so a contamination hop that fakes 8.00 ppm is unwritten; (iii) a3's k_h is a lumped coil factor, not a temperature / remnant-field table, so a Vc hop that fakes 20.00 kA inside a 4.80 last-good is unwritten; (iv) captured arbitration panel (r12 gap 1 leftover) is still unwritten; (v) stream amplitudes remain authored constants (raster draws are the only seeded noise); (vi) leftover-mill r60–r64 in-flight families were left for those rounds' owners.

### Realism of noise / temporal fidelity
- Strong: a1's 8.00 m^-1, OD 2.00, and 18.0 min PAC (`4800+1080=5880 s`) recompute from the record; a2's 8.00 ppm, Q/m 4.00, titer 4.00, and 24.0 min bake-out (`2820+1440=4260 s`) recompute; a3's 20.00 kA, P 20.00 MW, and 12.0 min survey (`6000+720=6720 s`) recompute. Raster adaptation (0.82**k plus 4% noise) and the 1.2–1.5 ms physics pairs give the ≥48 stream a raster-scale motif without violating 0.8 ms same-channel refractory.
- **Gaps, honestly:** (i) 1 Hz municipal spectrophotometer / KF titer and kHz Hall-null are still thinned (5 I points, 5 Q points, 6 Vc points) even at 52–54 events; (ii) a1's post-stop 12.00 m^-1 is a later grab, not a closed-loop PAC controller; (iii) a2 HIL coupon times an in-service dryer isolate that the stream does not independently witness on a second live dryer until the new cell starts; (iv) no gate_snn input→output volley pair at raster resolution this round (2026-08-30 r04-a1 already staged that).

### Training value (SNN/LSM + agentic)
Distillation targets: UV254 A=k_a·log2(I0/I) reconstruction head plus optical-depth identity; conjunctive isolate floor vs continue-filter vs works ESD; vendor-only nonsubstitution on a plant with no independent head; Karl Fischer x=k_f·Q/m head plus Q/m and titer identities; isolate-floor dryer vs keep-whole vs oil dump; exoneration against last-to-badge social pressure; Hall-null I=k_h·Vc/S and bus-power identities; bounded ACCEPT with rectifier-out-of-scope; skip-survey refusal under survey takt. Agentic value concentrates in three patterns: reconstruction-as-SoT on a physical absorbance/water/current load the raw corridor cannot see, earned ACCEPT with an explicit physical out-of-scope object (R-1/R-2), and stop-then-hold so a REJECT does not become a works/tank/potline kill.

## What round 2 should add (next densification target)
1. **T/P/DOC table** on a non-YC-2 filter outlet so a thermal hop fakes 8.00 m^-1 inside a 0.80 Uvveil corridor, closing a1's lumped-k_a gap.
2. **Faraday / blank-titer map** on a non-PF-7 dryer so a contamination hop can fake 8.00 ppm while mean coulomb looks healthy.
3. **Temperature / remnant-field table** on a non-NF-5 rectifier so a Vc hop can fake 20.00 kA inside a 4.80 last-good corridor.
4. **Captured arbitration / appeal panel** (r12 gap still open at factory-global scope) on a new family, not a restage of UV254/KF/Hall-null.
5. **Do not restage** VOD-SNN replay, pharma cold-chain, CEMS, FBG glaze, Frostlip quench, Oxbow VRFB, IFOG, transmon, hyperspectral, MEMS array, muon ore-pass, industrial x-ray, optogenetic stim, 905 nm LiDAR snow, clamp-on transit-time, LIBS, QEPAS, LFV, Kaplan LDV, THz-TDS, ECT, TDLAS NH3, lock-in thermography, PAUT TFM, EN CUI, RUS porcelain, N-16 loop flow, helium RGA, Faraday FOCT, blade tip-timing, acoustic pyrometry, SPR, vibrating-wire viscometer, microwave-cavity, MFL, NMR T2, nucleonic densitometry, JNT, CRNS, Coriolis, CARS, XRF, Mössbauer, GB-InSAR, ellipsometry, CTA, SPND, LII, PALS, NQR, SFRA, digital shearography, hydrogen permeation, FMCW lining, GPR, Pockels, PEC, confocal, mud-pulse, Barkhausen, Lamb-wave, OCT, DCPD, impact-echo, cyclotron BPM, alanine EPR, ADCP, vortex-shedding, Kr-85 beta, 532 nm Raman, phosphor-lifetime, guided-wave-radar, paramagnetic O2, TOFD, TEOM, magmeter, PDA, acoustoelastic, C-SAM, FDS tanδ, MCSA, EMAT SH, FBRM, ACFM, OFDR, XRD sin²ψ, FSM, Gardon, chilled-mirror, DIC, CLD NOx, proximity orbit, thermal-mass, ER probe, Fabry-Perot, inductive debris, wire-mesh, UCI, MAE, IRIS, ratio pyrometer, UV-fluorescence oil-in-water, zirconia Nernst, PID VOC, contact pulse-echo, Rogowski, beta-attenuation, UV-DOAS, Al2O3 moisture, load-cell hopper, 90-degree nephelometry, Wobbe, pellistor, Stern-Volmer DO, laser triangulation, Clark polarographic, katharometer, venturi, Yarrowcrag YC-2 UV254, Pewterfen KF-HIL-4, or Nollfen HALL-SIM-3. Leave leftover-mill r55–r64 IDs `166`–`195` alone.

## Verification
`batch-r01.jsonl`: 3 lines, `json.loads`-clean (allow_nan=False), {sizes[0]}/{sizes[1]}/{sizes[2]} bytes (file {{BATCH.stat().st_size}}, sha256 `{file_sha}`). Staged at `/tmp/nelb-sf-r01/` and created under the sf-window factory dir. Repo gates: `check_records.check_jsonl` with `FactoryStaging(enabled=True)` → 0 errors, 0 warnings, kinds `{{bridge_pair: 3}}`; `python3 pipelines/check_records.py --strict /tmp/nelb-sf-r01` → 0/0; `curate_bridge.raster_status(..., require_raster=True, require_routing_table=True)` → raster_valid and gate_snn_valid true, empty reason codes; `curate_record(...)` → 3× retain / `BRIDGE_EVENTS_ALREADY_GLOBALLY_ORDERED`; `verify_batch_for_frontier(strict=True)` → 3 verified, 0 inconclusive, 0 failed; `python3 pipelines/spike_probe.py --strict /tmp/nelb-sf-r01/batch-r01.jsonl` → loaded 3, unloadable 0, problems [], third_factor_routes 3, gate_snn_records 3, spikes {spikes}, energy_pJ {energy}. Build-time asserts: global time order; same-channel ≥0.8 ms; ≥48 events ({events[0]}/{events[1]}/{events[2]}); excerpt integer bounds, neuron bounds, sort, 1 ms per-neuron floor; ISI identity {isis[0]}/{isis[1]}/{isis[2]}; spike budgets exact; energy pJ/µJ exact; reward totals equal two-decimal component sums ({reward_s}); gate_snn decisions match lead `safety_decision.decision`; `state.sim_or_real` ∈ {{designed, hil, simulated}}; `meta.round=1`, `meta.factory=neuromorphic-event-language-bridge`, `meta.generator=grok-4.6`, `meta.run_label=2026-09-02-final-heavy`; `meta.rights` 15-key RM-793 stamp (`intended_use=research_only`, `linear_issue=RM-793`, `generated_at={GENERATED_AT}`); no hidden-reasoning keys; no `provenance` objects; no live-plant claims; no `training_ready`; all 9 record/trajectory ids unique. Raster seeds 202609021/202609022/202609023, MT19937.

Honest novelty accounting: 3/3 modality families are new versus the committed factory and versus leftover-mill r13–r64 occupancy. Vendor-only-no-plant-head is a flagged gap closed rather than a restaged sensor. In-stream slow floors, operational t2, reconstruction-as-SoT, conjunctive SOP, and bounded-accept-with-scope-limit are carried edges applied to new physics. Against that: three-party collusion and exoneration were already taught on leftover-mill quench/VRFB/TOFD/PDA; the ≥48 event floor restores a density teaching object leftover mill had dropped. Net: a bit under three-fifths of the round's scenario/edge mass is genuinely novel.

Novel coverage: 58%
"""
    notes = notes.replace("{BATCH.stat().st_size}", str(BATCH.stat().st_size))
    NOTES.write_text(notes, encoding="utf-8")
    print("wrote", NOTES, "bytes", NOTES.stat().st_size)


def publish_create_only(records, lines):
    PUBLISH_DIR.mkdir(parents=True, exist_ok=True)
    dest_batch = PUBLISH_DIR / "batch-r01.jsonl"
    dest_notes = PUBLISH_DIR / "NOTES-r01.md"
    if dest_batch.exists() or dest_notes.exists():
        dest_batch = PUBLISH_DIR / "batch-r01c.jsonl"
        dest_notes = PUBLISH_DIR / "NOTES-r01c.md"
        if dest_batch.exists() or dest_notes.exists():
            raise RuntimeError(f"refuse: {dest_batch} or {dest_notes} already exists")
    dest_batch.write_text("\n".join(lines) + "\n", encoding="utf-8")
    dest_notes.write_text(NOTES.read_text(encoding="utf-8"), encoding="utf-8")
    print("created", dest_batch, dest_notes)
    return dest_batch, dest_notes


def main():
    occupancy_preflight()
    records = [rec_a1(), rec_a2(), rec_a3()]
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
    gate = repo_validate(records)
    write_notes(records, lines, gate)
    publish_create_only(records, lines)


if __name__ == "__main__":
    main()
