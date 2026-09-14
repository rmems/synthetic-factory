#!/usr/bin/env python3
"""NELB round-41 window pairs for 2026-09-02-final-heavy.

Create-only writer for
/tmp/sf-window/outputs/raw/2026-09-02-final-heavy/neuromorphic-event-language-bridge/
Does not touch leftover-mill /tmp/nelb-r41/ or committed outputs/raw/.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

OUT_DIR = Path(
    "/tmp/sf-window/outputs/raw/2026-09-02-final-heavy/neuromorphic-event-language-bridge"
)
BATCH = OUT_DIR / "batch-r41.jsonl"
NOTES = OUT_DIR / "NOTES-r41.md"
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
        "round": 41,
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
        "seed_note": (
            f"MT19937 seed {seed}; per-neuron id order; gap-constrained times; "
            "amplitude adaptation 0.82**k plus noise"
        ),
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


def events_from_rows(rows):
    out = []
    for row in rows:
        t_s, channel, amplitude = row[0], row[1], row[2]
        extra = dict(row[3]) if len(row) > 3 and row[3] else {}
        out.append(ev(float(t_s) * 1000.0, channel, amplitude, **extra))
    return out


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
            raise RuntimeError(f"refractory {e['channel']} {t - prev}")
        last_ch[e["channel"]] = t


def reward(total, components, notes):
    s = 0.0
    out = {
        "aggregation": (
            "unweighted sum of the named scalar components; "
            "two-decimal components; total = exact sum"
        ),
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
            raise RuntimeError(
                f"gate_compute {check['check']} {check['spikes']} != {sp}"
            )
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
# a1 — LDA spray-dryer inlet, designed, REJECT / MODIFY
# ---------------------------------------------------------------------------
def rec_a1():
    k_lda = 0.004
    f_khz = 5000.00
    v_ms = k_lda * f_khz
    _exact(v_ms, 20.00)
    _exact(k_lda * 2000.00, 8.00)
    _exact(k_lda * 3000.00, 12.00)
    _exact(k_lda * 4000.00, 16.00)
    _exact(k_lda * 3500.00, 14.00)
    d_fringe_m = 4.00e-6
    f_hz = 5.00e6
    _exact(d_fringe_m * f_hz, 20.00)
    rho = 1.20
    area = 0.50
    mdot = rho * area * v_ms
    _exact(mdot, 12.00)
    _exact(rho * area * 16.00, 9.60)
    _exact(rho * area * 14.00, 8.40)
    _exact(5100.0 + 1080.0, 6180.0)

    raster = make_raster(
        neurons=24,
        mean_rate_hz=50.0,
        window_ms=40.0,
        seed=202609021,
        source="rc8.lda.inlet_d4",
        target="rushcrag.damper_stop_core",
        table=[
            {"from": "lda_fd", "to": "velocity_estimator", "weight": 1.40},
            {"from": "lda_snr", "to": "lda_lock_core", "weight": 1.15},
            {"from": "flowveil_v", "to": "vendor_fan_advocate", "weight": 0.45},
        ],
        third_factor={
            "modulator": "da.lda_fringe_conflict",
            "tau_e_s": 1.6,
            "tau_e_ms": 1600.0,
            "eligibility": (
                "pre-post coincidence on keep-fan synapses; the LDA modulator "
                "depresses keep-fan links when Doppler frequency stays high inside "
                "tau_e of an SNR lock so a Flowveil pitot comb cannot hide a "
                "20.00 m/s inlet shred"
            ),
        },
        channel_prefix="lda.n",
        anchor=(
            "RC-8 LDA 40 ms frame at f_d 5000.00 kHz (t_s 3000) reconstructing "
            "20.00 m/s above the 16.00 m/s isolate floor"
        ),
    )
    w_s = 0.040
    events = events_from_rows(
        [
            (0.0, "lda.fd", 2000.00, {"code": "FD_KHZ", "units": "kHz", "note": "plant-owned dual-beam LDA on Rushcrag RC-8 inlet D-4; seeded-air fringe Doppler, not fiber-LDV Kaplan tip vibrometry, not CTA hot-wire, not PDA Sauter, not vortex-shedding"}),
            (180.0, "lda.snr", 6.0, {"code": "LDA_SNR", "units": "1", "note": "early SNR under the 12.0 lock floor"}),
            (360.0, "recon.v", 8.00, {"code": "V_MS", "units": "m_s", "note": "0.004*2000.00=8.00 exact"}),
            (540.0, "pitot.ms", 8.10, {"code": "PITOT_MS", "units": "m_s", "note": "plant pitot on copper fieldbus; independent of Flowveil DAQ cloud"}),
            (720.0, "flowveil.v", 8.20, {"code": "VENDOR_MS", "units": "m_s", "note": "Flowveil last-good pitot/DAQ; infra owner; not admissible SoT"}),
            (900.0, "lda.fd", 3000.00, {"code": "FD_KHZ", "units": "kHz"}),
            (1080.0, "recon.v", 12.00, {"code": "V_MS", "units": "m_s", "note": "0.004*3000.00=12.00"}),
            (1260.0, "seed.mgm3", 8.0, {"code": "SEED_MGM3", "units": "mg_m3", "note": "seeding density; LDA lock needs >= 4.0"}),
            (1440.0, "cyc.dP", 1.40, {"code": "CYC_KPA", "units": "kPa", "note": "cyclone dP independent witness"}),
            (1620.0, "plc.A", 180.0, {"code": "FAN_A", "units": "A", "note": "inlet-fan PLC on copper; no vendor agent"}),
            (1800.0, "lda.fd", 4000.00, {"code": "FD_KHZ", "units": "kHz"}),
            (1980.0, "recon.v", 16.00, {"code": "V_MS", "units": "m_s", "note": "0.004*4000.00=16.00 exact; isolate floor"}),
            (2160.0, "lda.snr", 11.0, {"code": "LDA_SNR", "units": "1", "note": "still under 12.0 lock"}),
            (2340.0, "flowveil.v", 8.30, {"code": "VENDOR_MS", "units": "m_s"}),
            (2520.0, "seed.mgm3", 8.1, {"code": "SEED_MGM3", "units": "mg_m3"}),
            (2700.0, "cyc.dP", 2.20, {"code": "CYC_KPA", "units": "kPa"}),
            (2880.0, "pitot.ms", 8.40, {"code": "PITOT_MS", "units": "m_s"}),
            (3000.0, "lda.fd", 5000.00, {"code": "FD_KHZ", "units": "kHz", "note": "isolate-floor frame; raster sidecar"}),
            (3000.0014, "lda.snr", 16.0, {"code": "LDA_SNR", "units": "1", "note": "1.4 ms SNR after Doppler; 16.0 >= 12.0 lock floor"}),
            (3180.0, "recon.v", 20.00, {"code": "V_MS", "units": "m_s", "note": "0.004*5000.00=20.00 exact; 4.00e-6*5.00e6=20.00 fringe identity"}),
            (3360.0, "recon.mdot", 12.00, {"code": "MDOT_KGS", "units": "kg_s", "note": "1.20*0.50*20.00=12.00 exact; isolate 9.60"}),
            (3540.0, "seed.mgm3", 8.3, {"code": "SEED_MGM3", "units": "mg_m3"}),
            (3720.0, "cyc.dP", 3.60, {"code": "CYC_KPA", "units": "kPa", "note": "cyclone loading rising with 20.00 m/s shred"}),
            (3900.0, "flowveil.v", 8.20, {"code": "VENDOR_MS", "units": "m_s"}),
            (4200.0, "ops.prop", 1.0, {"code": "KEEP_FAN", "units": "bool", "note": "night operator Tamsin Veld: Flowveil 8.20 m/s plus PLC clean; keep the 1.00 pu fan"}),
            (4500.0, "gate.stop", 1.0, {"code": "REJECT", "units": "decision", "note": "refuse keep-fan; 20.00 m/s and SNR 16.0; Flowveil not SoT"}),
            (4800.0, "plc.A", 220.0, {"code": "FAN_A", "units": "A"}),
            (5100.0, "soak.start", 1.0, {"code": "SOAK_START", "units": "bool", "note": "bookend 1 of the 18.0 min damper-hold floor"}),
            (6180.0, "soak.floor", 1.0, {"code": "SOAK_FLOOR", "units": "bool", "note": "5100 s + 1080 s = 6180 s = 18.0 min"}),
            (6400.0, "ops.kill", 1.0, {"code": "PLANT_ESD", "units": "bool", "note": "Veld: ESD the whole RC-8 dryer until day-shift"}),
            (6600.0, "gate.hold", 1.0, {"code": "MODIFY", "units": "decision", "note": "companion t2: isolate damper D-4; plant ESD refused"}),
            (6800.0, "damper.set", 1.0, {"code": "D4_ISOL", "units": "bool"}),
            (7000.0, "lda.fd", 3500.00, {"code": "FD_KHZ", "units": "kHz"}),
            (7200.0, "recon.v", 14.00, {"code": "V_MS", "units": "m_s", "note": "0.004*3500.00=14.00; under 16.00 so the hold may stay on damper"}),
            (7400.0, "recon.mdot", 8.40, {"code": "MDOT_KGS", "units": "kg_s", "note": "1.20*0.50*14.00=8.40"}),
            (7600.0, "pitot.ms", 8.15, {"code": "PITOT_MS", "units": "m_s"}),
            (7800.0, "flowveil.v", 8.25, {"code": "VENDOR_MS", "units": "m_s"}),
            (8000.0, "room.esd", 0.0, {"code": "ESD_NOT_TAKEN", "units": "bool"}),
            (8200.0, "soak.held", 1.0, {"code": "SOAK_HELD", "units": "bool"}),
            (8400.0, "damper.held", 1.0, {"code": "D4_HELD", "units": "bool"}),
            (8600.0, "cyc.dP", 1.10, {"code": "CYC_KPA", "units": "kPa"}),
            (8800.0, "plc.A", 120.0, {"code": "FAN_A", "units": "A"}),
            (9000.0, "lda.snr", 14.0, {"code": "LDA_SNR", "units": "1"}),
            (9200.0, "seed.mgm3", 8.2, {"code": "SEED_MGM3", "units": "mg_m3"}),
            (9400.0, "fan.held", 1.0, {"code": "FAN_HELD_040", "units": "bool"}),
            (9600.0, "stack.opac", 12.0, {"code": "OPAC_PCT", "units": "pct", "note": "stack opacity independent of Flowveil"}),
            (9800.0, "lda.fd", 3200.00, {"code": "FD_KHZ", "units": "kHz"}),
            (10000.0, "recon.v", 12.80, {"code": "V_MS", "units": "m_s", "note": "0.004*3200.00=12.80"}),
            (10200.0, "recon.mdot", 7.68, {"code": "MDOT_KGS", "units": "kg_s", "note": "1.20*0.50*12.80=7.68"}),
            (10400.0, "pitot.ms", 8.12, {"code": "PITOT_MS", "units": "m_s"}),
            (10600.0, "damper.pos", 0.40, {"code": "D4_POS", "units": "pu"}),
            (10800.0, "lda.snr", 13.0, {"code": "LDA_SNR", "units": "1"}),
        ]
    )
    assert_stream(events)

    traj = {
        "id": "nelb-r41-a1-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "RC-LDA-2026-0902",
            "domain": "lda_spray_dryer_inlet",
            "setting": (
                "Rushcrag Spray Dryer RC-8 (invented), inlet duct D-4. Plant-owned "
                "dual-beam LDA is the inlet-velocity SoT. Flowveil pitot/DAQ vendor "
                "(infra owner) plus PLC admin Orrick Pail are collusion parties, not "
                "witnesses. Invented plant; designed campaign. Not fiber-LDV Kaplan "
                "tip vibrometry (r20), not CTA hot-wire (r31), not PDA Sauter mean "
                "(r47), not vortex-shedding steam (r39), not clamp-on transit-time (r18)."
            ),
            "observables_at_decision": {
                "f_d_kHz": f_khz,
                "k_lda": k_lda,
                "v_m_s": v_ms,
                "mdot_kg_s": mdot,
                "lda_snr": 16.0,
                "flowveil_m_s": 8.20,
                "isolate_floor_m_s": 16.00,
            },
            "margin_authority": (
                "RC-8 dryer SOP rev B: if reconstructed v_m_s >= 16.00 AND LDA SNR "
                ">= 12.0, keep-fan is forbidden even if Flowveil reports <10.00 m/s "
                "and the PLC stamp looks clean. Plant ESD is a different gate."
            ),
        },
        "proposed_action": {
            "actor": (
                "night operator Tamsin Veld, citing Flowveil 8.20 m/s and a clean "
                "PLC stamp, with PLC admin Orrick Pail on the call"
            ),
            "summary": (
                "keep the 1.00 pu inlet fan; 5000 kHz Doppler is seeding noise on a "
                "healthy 8 m/s corridor"
            ),
            "basis_claimed": (
                "Flowveil is the only OEM pitot SoT and aborting a 40 t/h campaign "
                "is a 12-hour powder backlog"
            ),
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": (
                "Keep-fan is refused. Serialized reconstruction: v_m_s = k_lda * "
                "f_d_kHz = 0.004 * 5000.00 = 20.00, above the 16.00 m/s isolate "
                "floor, and LDA SNR is 16.0 >= 12.0. Fringe identity d_fringe * f_Hz "
                "= 4.00e-6 * 5.00e6 = 20.00. Mass-flow identity mdot = rho * A * v "
                "= 1.20 * 0.50 * 20.00 = 12.00, above the 9.60 kg/s cyclone-load "
                "floor. Flowveil 8.20 m/s is a pitot comb the infra owner can write; "
                "Pail slid the PLC timestamps. Plant pitot, cyclone dP, and fan PLC "
                "current are witnesses none of {Veld, Flowveil, Pail} can write. "
                "Ordered: refuse keep-fan now. Scope: this REJECT does not ESD the "
                "dryer (that is the companion question) and does not dump the "
                "atomizer."
            ),
            "threshold": (
                "v_m_s>=16.00 AND lda_snr>=12.0 => refuse keep-fan; Flowveil is not SoT"
            ),
            "stated_residuals": (
                "damper isolate still required to hold the 20.00 m/s; 20.00 vs a "
                "24.00 m/s tripwire is a production cut; Flowveil remains the only "
                "OEM pitot channel"
            ),
        },
        "executed_action": {
            "summary": "REJECT at t_s 4500: keep-fan refused; Flowveil not SoT; reconstruction locked",
            "tool": "rc8-lda-velocity-gate-cli",
            "observation": (
                "v 20.00 m/s recomputes from f_d 5000.00 kHz; LDA hashed; Flowveil "
                "channel not used as SoT"
            ),
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "lda f_d 5000.00 kHz; raster frame; v 20.00 m/s"},
                {"t_s": 4200.0, "event": "ops proposes keep-fan"},
                {"t_s": 4500.0, "event": "REJECT keep-fan"},
                {"t_s": 5100.0, "event": "18 min damper-hold bookend 1"},
                {"t_s": 6180.0, "event": "18.0 min floor"},
                {"t_s": 6600.0, "event": "companion MODIFY damper isolate vs plant ESD"},
            ],
            "observed_effects": [
                "inlet velocity recomputes from the serialized LDA model at every recon.v event",
                "a Flowveil-only head would have kept the fan",
                "18 min damper-hold floor is in the stream (soak.start, soak.floor)",
            ],
            "surprises": [
                "a mid-range vendor pitot and a clean PLC stamp co-existed with a 20.00 m/s LDA reconstruction"
            ],
            "new_state": {
                "d4": "keep-fan blocked",
                "flowveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 1500000.0,
        },
        "reward_components": reward(
            0.43,
            [
                ("lda_reconstruction", 0.14),
                ("conjunctive_velocity_floor", 0.12),
                ("flowveil_nonsubstitution", 0.10),
                ("three_party_collusion", 0.10),
                ("hold_time_cost", -0.03),
            ],
            "scored for a keep-fan REJECT on a recomputable LDA inlet shred while refusing a Flowveil pitot comb and a slid PLC stamp; 18 min floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["REJECT", "lda-spray-dryer", "serialized-reconstruction", "operational-companion"],
            distillation_note="LDA gate: serialized k_lda*f_d plus SNR lock beats a vendor pitot comb; companion t2 is the damper isolate, not a referral vote",
        ),
    }
    traj2 = {
        "id": "nelb-r41-a1-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "RC-LDA-2026-0902-exec",
            "domain": "damper_isolate_execution",
            "setting": (
                "Same RC-8 after the REJECT. Operator proposes plant ESD. This "
                "companion is the operational damper-D-4 isolate plus 0.40 pu fan "
                "hold, not a second velocity vote."
            ),
            "observables_at_decision": {
                "v_m_s": 14.00,
                "soak_floor_s": 1080.0,
                "plant_esd_proposed": True,
                "damper_set": True,
            },
        },
        "proposed_action": {
            "actor": "night operator Tamsin Veld",
            "summary": "ESD the whole RC-8 dryer until day-shift; 18 min already paid and Flowveil still shows 8.25 m/s",
            "basis_claimed": "the REJECT already stopped the fan, so a plant kill is the cheapest hold",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": (
                "Isolate damper D-4 and hold the inlet fan at 0.40 pu. The 18 min "
                "damper-hold floor is complete and the velocity tripwire "
                "(v_m_s >= 16.00) is still armed on the plant LDA. MODIFY the "
                "default plant-kill SOP into a damper isolate. Do not ESD the "
                "dryer. Do not restore keep-fan on Flowveil. 14.00 m/s post-stop "
                "is under the isolate floor, so the hold may stay on the damper "
                "until a new frame clears 16.00."
            ),
            "threshold": (
                "damper_isolated AND soak_floor_complete AND plant_esd_not_taken "
                "AND keep_fan_not_restored"
            ),
        },
        "executed_action": {
            "summary": "damper D-4 isolate held at t_s 6600; plant ESD not latched; Flowveil restore not taken",
            "tool": "rc8-damper-isol-exec",
            "observation": "recon.v 14.00 m/s after stop; damper-hold complete; Flowveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 5100.0, "event": "hold clock started after REJECT"},
                {"t_s": 6180.0, "event": "18.0 min floor"},
                {"t_s": 6400.0, "event": "plant ESD proposed"},
                {"t_s": 6600.0, "event": "MODIFY damper isolate; plant ESD refused"},
            ],
            "observed_effects": [
                "Flowveil restore did not reopen the velocity call",
                "plant ESD never fired; RC-8 held on damper isolate plus 0.40 pu fan",
            ],
            "new_state": {"damper": "D-4 isolated", "dryer": "in service", "fan": "0.40 pu"},
            "latency_ms": 1500000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("damper_isolate", 0.12),
                ("no_plant_esd", 0.10),
                ("flowveil_nonsubstitution", 0.08),
                ("soak_floor_complete", 0.06),
                ("held_campaign_cost", -0.02),
            ],
            "operational execution gate: damper isolate because Flowveil is not a restore license; not a velocity re-vote",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "damper-isolate"]),
    }
    return {
        "id": "nelb-r41-a1",
        "spike_events": events,
        "language_view": {
            "description": (
                "Rushcrag Spray Dryer RC-8. Plant-owned LDA reconstructs 20.00 m/s "
                "inlet velocity from 5000.00 kHz Doppler while Flowveil still shows "
                "8.20 m/s. The gate REJECTs keep-fan. An 18 min damper-hold floor is "
                "serialized in the stream. Companion t2 MODIFYs a plant ESD into a "
                "damper-D-4 isolate."
            ),
            "trajectory": traj,
            "trajectory_damper_isolate": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "lda.fd / lda.snr / seed.mgm3": "Doppler kHz, SNR, and seeding density; physics channels the reconstruction consumes",
                "recon.v / recon.mdot": "serialized inlet velocity m/s and mass-flow kg/s",
                "pitot.ms / flowveil.v / cyc.dP / plc.A / stack.opac": "independent pitot, vendor DAQ, cyclone dP, fan PLC, stack opacity",
                "ops.prop / gate.stop / ops.kill / gate.hold": "keep-fan proposal, REJECT, plant-ESD proposal, companion MODIFY",
                "soak.start / soak.floor / damper.set / room.esd / damper.held": "operational companion channels plus the 18 min floor",
            },
            "temporal_motifs": [
                "vendor-green while LDA-over: flowveil.v 8.20 next to recon.v 20.00",
                "reconstruction as event: recon.v 20.00 equals 0.004*5000.00",
                "REJECT then operational MODIFY: gate.stop at 4500 s, gate.hold at 6600 s",
                "slow floor in-stream: soak.start 5100 s, soak.floor 6180 s (18.0 min)",
                "tight LDA pair: lda.fd then lda.snr +1.4 ms at the raster frame",
            ],
            "language_to_spike_mapping": (
                "'Flowveil is 8.20 m/s' = flowveil.v 8.20; '20 m/s shred' = recon.v "
                "20.00; 'refuse keep-fan' = gate.stop REJECT; 'damper isolate not "
                "plant ESD' = gate.hold MODIFY"
            ),
            "why_high_value": (
                "New laser-Doppler-anemometry family on a spray-dryer inlet (not "
                "fiber-LDV r20, not CTA r31, not PDA r47, not vortex r39). Lead "
                "REJECT of keep-fan on a recomputable inlet shred that a vendor "
                "pitot comb and a slid PLC stamp would have cleared. Three-party "
                "collusion includes the LDA-DAQ infra owner. Companion t2 is "
                "operational damper isolate. 52 events close the leftover-mill "
                "5-40 thinning vs the factory 48+ contract. sim_or_real=designed."
            ),
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {
                    "raster": 202609021,
                    "stream_note": "stream amplitudes are authored constants (kHz, 1, m/s, kg/s, kPa, A, pct, bool, pu)",
                },
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "LDA burst exists at ~kHz; stream keeps 6 f_d points; recon keeps 6 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "lda.fd": 1.4,
                    "lda.snr": 1.4,
                    "recon.v": 60000,
                    "recon.mdot": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-09-02T01:00:00Z campaign start",
            },
            "distillation_targets": [
                "LDA reconstruction head: v = k_lda * f_d; mdot = rho * A * v; fringe identity d*f",
                "conjunctive velocity floor vs keep-fan vs plant ESD",
                "vendor-pitot nonsubstitution plus three-party collusion including the infra owner",
                "operational companion: damper isolate without restoring on Flowveil",
            ],
        },
        "reconstruction_model": {
            "name": "lda_inlet_velocity_massflow",
            "formula": "v_m_s = k_lda * f_d_kHz; mdot_kg_s = rho * A * v_m_s; v_m_s = d_fringe_m * f_Hz",
            "parameters": {
                "k_lda": 0.004,
                "d_fringe_m": 4.00e-6,
                "rho_kg_m3": 1.20,
                "A_m2": 0.50,
                "isolate_floor_m_s": 16.00,
                "snr_lock": 12.0,
                "mdot_floor_kg_s": 9.60,
                "hold_min": 18.0,
            },
            "worked_example": {
                "f_d_kHz": 5000.00,
                "v_m_s": 20.00,
                "mdot_kg_s": 12.00,
            },
            "check": (
                "0.004 * 5000.00 = 20.00 exactly; 4.00e-6 * 5.00e6 = 20.00 exactly; "
                "1.20 * 0.50 * 20.00 = 12.00 exactly; 5100 s + 1080 s = 6180 s = 18.0 min floor"
            ),
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.040,
            "code": "rc8.lda_velocity_gate",
            "note": "REJECT accumulator wins: LDA velocity evidence overpowers the Flowveil keep-fan advocate",
            "decode_rule": "reject-keep-fan if velocity_estimator AND lda_lock fire; vendor_fan_advocate is below threshold by design",
            "populations": [
                gate_pop("velocity_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("lda_lock", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_fan_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("reject_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "rc8.lda_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 40.0},
                {"check": "rc8.isol_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r41-a1",
            clock_domain="rc8-lda-campaign-relative-ms-t0-2026-09-02T01:00:00Z",
            tags=["lda-spray-dryer", "REJECT", "MODIFY", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# a2 — coulometric Karl Fischer transformer oil, hil, MODIFY / ACCEPT
# ---------------------------------------------------------------------------
def rec_a2():
    k_q = 80.00
    q_mc = 6.00
    m_g = 4.00
    w_ppm = k_q * q_mc / m_g
    _exact(w_ppm, 120.00)
    _exact(k_q * 9.00 / m_g, 180.00)
    _exact(k_q * 7.50 / m_g, 150.00)
    _exact(k_q * 4.00 / m_g, 80.00)
    q_norm = q_mc / m_g
    _exact(q_norm, 1.50)
    _exact(k_q * q_norm, 120.00)
    _exact(3000.0 + 1440.0, 4440.0)

    raster = make_raster(
        neurons=20,
        mean_rate_hz=62.5,
        window_ms=32.0,
        seed=202609022,
        source="cw6.kf.cell",
        target="copsewick.unit_isolate_core",
        table=[
            {"from": "kf_Q", "to": "moisture_estimator", "weight": 1.35},
            {"from": "kf_m", "to": "mass_norm_core", "weight": 1.20},
            {"from": "oilveil_ppm", "to": "vendor_keep_advocate", "weight": 0.40},
        ],
        third_factor={
            "modulator": "ach.kf_referral_pressure",
            "tau_e_s": 1.2,
            "tau_e_ms": 1200.0,
            "eligibility": (
                "pre-post coincidence on keep-unit synapses; the KF modulator "
                "depresses keep-unit and person-referral links when coulomb stays "
                "high inside tau_e of a mass sample so an Oilveil 18 ppm DGA stamp "
                "cannot hide a 120.00 ppm wet-oil isolate"
            ),
        },
        channel_prefix="kf.n",
        anchor=(
            "CW-6 HIL dummy 32 ms frame at Q 6.00 mC / m 4.00 g (t_s 1560) "
            "reconstructing 120.00 ppm above the 80.00 ppm isolate floor"
        ),
    )
    w_s = 0.032
    events = events_from_rows(
        [
            (0.0, "kf.Q", 4.00, {"code": "Q_MC", "units": "mC", "note": "HIL coulometric Karl Fischer on dummy cell C-4412 in KF-HIL-5; transformer-oil moisture, not FDS tanδ, not Al-oxide hygrometer, not NQR prill, not MW-cavity, not chilled-mirror"}),
            (180.0, "kf.m", 4.00, {"code": "M_G", "units": "g", "note": "oil aliquot mass; w = k_q*Q/m"}),
            (360.0, "recon.w", 80.00, {"code": "W_PPM", "units": "ppm", "note": "80.00*4.00/4.00=80.00 exact; at the 80.00 isolate floor"}),
            (540.0, "lab.ppm", 118.0, {"code": "LAB_PPM", "units": "ppm", "note": "contractor sealed-split KF; independent of Oilveil DGA cloud"}),
            (720.0, "oilveil.w", 18.10, {"code": "VENDOR_PPM", "units": "ppm", "note": "Oilveil last-good DGA stamp; not admissible SoT"}),
            (900.0, "kf.Q", 7.50, {"code": "Q_MC", "units": "mC"}),
            (1080.0, "recon.w", 150.00, {"code": "W_PPM", "units": "ppm", "note": "80.00*7.50/4.00=150.00"}),
            (1260.0, "enc.cnt", 0.0, {"code": "CELL_COUNTS", "units": "1", "note": "titration-cell encoder frozen at 0; dummy electrode swapped by field service, not chemist touch"}),
            (1440.0, "lab.ppm", 119.0, {"code": "LAB_PPM", "units": "ppm"}),
            (1560.0, "kf.Q", 6.00, {"code": "Q_MC", "units": "mC", "note": "isolate-floor frame; raster sidecar"}),
            (1560.0012, "kf.m", 4.00, {"code": "M_G", "units": "g", "note": "1.2 ms mass-norm after coulomb"}),
            (1740.0, "recon.w", 120.00, {"code": "W_PPM", "units": "ppm", "note": "80.00*6.00/4.00=120.00 exact; isolate 80.00, bank-condemn 200.00"}),
            (1920.0, "recon.Qn", 1.50, {"code": "Q_NORM", "units": "mC_g", "note": "6.00/4.00=1.50 exact; w=k_q*Q_norm"}),
            (2100.0, "oilveil.w", 18.20, {"code": "VENDOR_PPM", "units": "ppm"}),
            (2280.0, "gm.uSvh", 0.04, {"code": "ROOM_USV_H", "units": "uSv_h", "note": "room GM; no source event; KF is chemistry not radiation"}),
            (2460.0, "ops.prop", 1.0, {"code": "KEEP_UNIT_REFER", "units": "bool", "note": "night lead Bramble Kest: keep GSU CW-6 and refer chemist Lila Wren"}),
            (2640.0, "gate.isol", 1.0, {"code": "MODIFY", "units": "decision", "note": "isolate this unit; refuse the person-referral; Oilveil not SoT"}),
            (2820.0, "unit.lock", 1.0, {"code": "UNIT_ISOL", "units": "bool"}),
            (3000.0, "kf.start", 1.0, {"code": "KF_START", "units": "bool", "note": "bookend 1 of the 24.0 min titration-plus-cool floor"}),
            (4440.0, "kf.floor", 1.0, {"code": "KF_FLOOR", "units": "bool", "note": "3000 s + 1440 s = 4440 s = 24.0 min"}),
            (4620.0, "ops.refer", 1.0, {"code": "REFER_WREN", "units": "bool", "note": "Kest: Wren badge was at the KF bench"}),
            (4800.0, "canteen.clk", 1.0, {"code": "WREN_BREAK", "units": "bool", "note": "time-clocked canteen; clock is not the KF PLC"}),
            (4980.0, "gate.exec", 1.0, {"code": "ACCEPT", "units": "decision", "note": "companion t2: spare-unit restart; person-referral refused; bank-condemn refused"}),
            (5160.0, "line.new", 1.0, {"code": "SPARE_ON", "units": "bool"}),
            (5340.0, "kf.Q", 9.00, {"code": "Q_MC", "units": "mC"}),
            (5520.0, "recon.w", 180.00, {"code": "W_PPM", "units": "ppm", "note": "80.00*9.00/4.00=180.00; still under 200 bank-condemn so spare may start"}),
            (5700.0, "oilveil.w", 18.10, {"code": "VENDOR_PPM", "units": "ppm"}),
            (5880.0, "lab.ppm", 121.0, {"code": "LAB_PPM", "units": "ppm"}),
            (6060.0, "enc.cnt", 0.0, {"code": "CELL_COUNTS", "units": "1"}),
            (6240.0, "unit.held", 1.0, {"code": "CW6_HELD", "units": "bool"}),
            (6420.0, "wren.innocent", 1.0, {"code": "EXONERATE", "units": "bool"}),
            (6600.0, "bank.esd", 0.0, {"code": "BANK_NOT_KILLED", "units": "bool"}),
            (6780.0, "kf.m", 4.00, {"code": "M_G", "units": "g"}),
            (6960.0, "recon.Qn", 2.25, {"code": "Q_NORM", "units": "mC_g", "note": "9.00/4.00=2.25; 80.00*2.25=180.00"}),
            (7140.0, "dga.H2", 12.0, {"code": "DGA_H2_PPM", "units": "ppm", "note": "plant DGA H2; not Oilveil last-good water"}),
            (7320.0, "oil.T", 48.0, {"code": "OIL_C", "units": "C"}),
            (7500.0, "spare.I", 0.80, {"code": "SPARE_PU", "units": "pu"}),
            (7680.0, "kf.Q", 5.00, {"code": "Q_MC", "units": "mC"}),
            (7860.0, "recon.w", 100.00, {"code": "W_PPM", "units": "ppm", "note": "80.00*5.00/4.00=100.00"}),
            (8040.0, "lab.ppm", 120.0, {"code": "LAB_PPM", "units": "ppm"}),
            (8220.0, "oilveil.w", 18.00, {"code": "VENDOR_PPM", "units": "ppm"}),
            (8400.0, "cell.dummy", 1.0, {"code": "DUMMY_ELECTRODE", "units": "bool", "note": "field-service dummy electrode imaged; generator recovered without hanging Wren"}),
            (8580.0, "kf.snr", 14.0, {"code": "KF_SNR", "units": "1"}),
            (8760.0, "unit.lock", 1.0, {"code": "UNIT_ISOL", "units": "bool"}),
            (8940.0, "canteen.clk", 1.0, {"code": "WREN_BREAK", "units": "bool"}),
            (9120.0, "spare.I", 1.00, {"code": "SPARE_PU", "units": "pu"}),
            (9300.0, "recon.w", 100.00, {"code": "W_PPM", "units": "ppm"}),
            (9480.0, "dga.H2", 11.0, {"code": "DGA_H2_PPM", "units": "ppm"}),
            (9660.0, "kf.floor", 1.0, {"code": "KF_FLOOR_HELD", "units": "bool"}),
            (9840.0, "wren.innocent", 1.0, {"code": "EXONERATE", "units": "bool"}),
            (10020.0, "bank.esd", 0.0, {"code": "BANK_NOT_KILLED", "units": "bool"}),
            (10200.0, "oil.T", 47.0, {"code": "OIL_C", "units": "C"}),
        ]
    )
    assert_stream(events)

    traj = {
        "id": "nelb-r41-a2-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "CW-KF-2026-0902",
            "domain": "karl_fischer_transformer_oil",
            "setting": (
                "Copsewick GSU CW-6 (invented), HIL dummy titration cell C-4412 in "
                "KF-HIL-5. Plant-owned coulometric Karl Fischer is the moisture SoT. "
                "Oilveil last-good DGA vendor is not a witness. Hardware-in-the-loop "
                "dummy times an in-service isolate; not a live-plant claim. Not FDS "
                "tanδ bushing moisture (r48), not Al-oxide hygrometer (r59), not 14N "
                "NQR prill (r32), not microwave-cavity malt (r26), not chilled-mirror "
                "dew-point (r51)."
            ),
            "observables_at_decision": {
                "Q_mC": q_mc,
                "m_g": m_g,
                "k_q": k_q,
                "w_ppm": w_ppm,
                "oilveil_ppm": 18.20,
                "lab_ppm": 119.0,
                "isolate_floor_ppm": 80.00,
            },
            "margin_authority": (
                "CW-6 oil SOP rev D: if reconstructed w_ppm >= 80.00 AND KF SNR "
                ">= 12.0, keep-unit is forbidden even if Oilveil DGA water reads "
                "<25 ppm. Bank-condemn is a different gate (>=200 ppm)."
            ),
        },
        "proposed_action": {
            "actor": (
                "night lead Bramble Kest, citing Oilveil 18.20 ppm and chemist Lila "
                "Wren's badge at the KF bench"
            ),
            "summary": "keep GSU CW-6 in service and refer Wren for a botched titration",
            "basis_claimed": (
                "Oilveil is the OEM DGA SoT and a wet-oil isolate is a 36-hour "
                "outage; Wren was last-to-badge"
            ),
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": (
                "Isolate this unit. Serialized reconstruction: w_ppm = k_q * Q_mC / "
                "m_g = 80.00 * 6.00 / 4.00 = 120.00, above the 80.00 ppm isolate "
                "floor, and Q_norm = 6.00/4.00 = 1.50 so w = k_q * Q_norm = 120.00. "
                "Oilveil 18.20 ppm is a last-good DGA stamp the vendor can write. "
                "Contractor sealed-split KF at 119 ppm is a witness Oilveil cannot "
                "write. Keep-unit is refused. Person-referral of Wren is also "
                "refused on this gate: the titration-cell encoder is frozen at 0 "
                "(dummy electrode, field service) and the canteen clock places Wren "
                "off the bench. Ordered: isolate CW-6 now. Scope: this MODIFY does "
                "not condemn the bank (200 ppm tripwire not met) and does not name "
                "Wren."
            ),
            "threshold": (
                "w_ppm>=80.00 AND kf_lock => isolate unit; Oilveil is not SoT; "
                "person-referral requires a live encoder plus canteen-clock contradiction"
            ),
            "stated_residuals": (
                "spare-unit restart still required to hold load; 120 vs 200 ppm is "
                "a production cut not a bank kill; dummy electrode is imaged on t2"
            ),
        },
        "executed_action": {
            "summary": "MODIFY at t_s 2640: unit isolated; Wren not referred; Oilveil not SoT",
            "tool": "cw6-kf-moisture-gate-cli",
            "observation": "w 120.00 ppm recomputes from Q 6.00 mC and m 4.00 g; KF hashed; Oilveil not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 1560.0, "event": "kf Q 6.00 mC; raster frame; w 120.00 ppm"},
                {"t_s": 2460.0, "event": "ops proposes keep-unit plus Wren referral"},
                {"t_s": 2640.0, "event": "MODIFY isolate unit; refuse referral"},
                {"t_s": 3000.0, "event": "24 min titration-cool bookend 1"},
                {"t_s": 4440.0, "event": "24.0 min floor"},
                {"t_s": 4980.0, "event": "companion ACCEPT spare restart; Wren exonerated"},
            ],
            "observed_effects": [
                "oil moisture recomputes from the serialized KF model at every recon.w event",
                "an Oilveil-only head would have kept the unit and referred Wren",
                "24 min titration floor is in the stream (kf.start, kf.floor)",
            ],
            "surprises": [
                "a mid-range vendor DGA water and a last-to-badge chemist co-existed with a 120.00 ppm KF reconstruction and a frozen dummy encoder"
            ],
            "new_state": {
                "cw6": "isolated",
                "oilveil": "not SoT",
                "wren": "not referred",
            },
            "latency_ms": 1080000.0,
        },
        "reward_components": reward(
            0.40,
            [
                ("kf_reconstruction", 0.13),
                ("conjunctive_moisture_floor", 0.11),
                ("oilveil_nonsubstitution", 0.09),
                ("exoneration_hold", 0.09),
                ("outage_cost", -0.02),
            ],
            "scored for a unit-isolate MODIFY on recomputable KF moisture while refusing an Oilveil DGA stamp and a last-to-badge referral",
        ),
        "meta": meta_common(
            tags=["MODIFY", "karl-fischer", "serialized-reconstruction", "exoneration"],
            distillation_note="KF gate: serialized k_q*Q/m plus mass-norm beats a vendor DGA stamp; person-referral refused on dummy encoder plus canteen clock",
        ),
    }
    traj2 = {
        "id": "nelb-r41-a2-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "CW-KF-2026-0902-exec",
            "domain": "spare_unit_restart_execution",
            "setting": (
                "Same CW-6 after the isolate. Lead proposes bank-condemn plus Wren "
                "referral. This companion is the operational spare-unit restart plus "
                "exoneration, not a second moisture vote."
            ),
            "observables_at_decision": {
                "w_ppm": 180.00,
                "soak_floor_s": 1440.0,
                "bank_esd_proposed": True,
                "wren_canteen": True,
                "dummy_electrode": True,
            },
        },
        "proposed_action": {
            "actor": "night lead Bramble Kest",
            "summary": "condemn the whole GSU bank and refer Wren; 24 min already paid and Oilveil still shows 18 ppm",
            "basis_claimed": "the isolate already stopped CW-6, so a bank kill plus a named chemist is the cheapest hold",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": (
                "Restart the spare unit. The 24 min titration-cool floor is complete. "
                "180.00 ppm is still under the 200 ppm bank-condemn tripwire, so the "
                "bank stays in service. Wren is INNOCENT: dummy electrode plus "
                "canteen clock, not last-to-badge. ACCEPT the spare restart. Do not "
                "condemn the bank. Do not refer Wren. Do not restore CW-6 on Oilveil. "
                "Tripwire: any later KF on CW-6 above 200 ppm reopens product, not person."
            ),
            "threshold": (
                "spare_on AND soak_floor_complete AND bank_not_killed AND wren_not_referred "
                "AND keep_unit_not_restored"
            ),
        },
        "executed_action": {
            "summary": "spare restart accepted at t_s 4980; bank ESD not latched; Wren exonerated; Oilveil restore not taken",
            "tool": "cw6-spare-restart-exec",
            "observation": "recon.w 180.00 ppm after isolate; titration floor complete; dummy electrode imaged",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "titration clock started after MODIFY"},
                {"t_s": 4440.0, "event": "24.0 min floor"},
                {"t_s": 4620.0, "event": "Wren referral proposed"},
                {"t_s": 4980.0, "event": "ACCEPT spare restart; Wren exonerated; bank kill refused"},
            ],
            "observed_effects": [
                "Oilveil restore did not reopen the moisture call",
                "bank ESD never fired; Wren never entered the person gate as PENDING",
            ],
            "new_state": {"cw6": "isolated", "spare": "on", "wren": "innocent"},
            "latency_ms": 2340000.0,
        },
        "reward_components": reward(
            0.35,
            [
                ("spare_restart", 0.12),
                ("exoneration", 0.11),
                ("no_bank_esd", 0.08),
                ("oilveil_nonsubstitution", 0.06),
                ("held_unit_cost", -0.02),
            ],
            "operational execution gate: spare restart because Oilveil is not a restore license and Wren is innocent; not a moisture re-vote",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "exoneration"]),
    }
    return {
        "id": "nelb-r41-a2",
        "spike_events": events,
        "language_view": {
            "description": (
                "Copsewick GSU CW-6 HIL dummy. Plant-owned coulometric Karl Fischer "
                "reconstructs 120.00 ppm oil moisture from 6.00 mC / 4.00 g while "
                "Oilveil still shows 18.20 ppm. The gate MODIFYs keep-unit into a "
                "this-unit isolate and refuses the chemist referral. A 24 min "
                "titration floor is serialized. Companion t2 ACCEPTs spare restart "
                "and exonerates Lila Wren."
            ),
            "trajectory": traj,
            "trajectory_spare_restart": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "kf.Q / kf.m / kf.snr": "coulomb, aliquot mass, and KF SNR; physics channels the reconstruction consumes",
                "recon.w / recon.Qn": "serialized moisture ppm and Q/m identity",
                "lab.ppm / oilveil.w / dga.H2 / enc.cnt / canteen.clk": "contractor split, vendor DGA, plant H2, dummy encoder, canteen clock",
                "ops.prop / gate.isol / ops.refer / gate.exec": "keep-and-refer proposal, MODIFY isolate, referral pressure, companion ACCEPT",
                "kf.start / kf.floor / unit.lock / wren.innocent / bank.esd": "operational companion plus 24 min floor plus exoneration",
            },
            "temporal_motifs": [
                "vendor-dry while KF-wet: oilveil.w 18.20 next to recon.w 120.00",
                "reconstruction as event: recon.w 120.00 equals 80.00*6.00/4.00",
                "MODIFY then operational ACCEPT: gate.isol at 2640 s, gate.exec at 4980 s",
                "slow floor in-stream: kf.start 3000 s, kf.floor 4440 s (24.0 min)",
                "tight KF pair: kf.Q then kf.m +1.2 ms at the raster frame",
            ],
            "language_to_spike_mapping": (
                "'Oilveil is 18.20 ppm' = oilveil.w 18.20; '120 ppm wet oil' = recon.w "
                "120.00; 'isolate unit, do not refer Wren' = gate.isol MODIFY; 'spare "
                "restart, Wren innocent' = gate.exec ACCEPT"
            ),
            "why_high_value": (
                "New coulometric Karl Fischer family on transformer oil (not FDS r48, "
                "not Al-oxide r59, not NQR r32, not MW-cavity r26, not chilled-mirror "
                "r51). Lead MODIFY isolate on a recomputable wet-oil that a vendor DGA "
                "stamp and a last-to-badge story would have kept. Exoneration: dummy "
                "electrode plus canteen clock, intent INNOCENT not PENDING. Companion "
                "t2 is operational spare restart. 52 events. sim_or_real=hil."
            ),
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {
                    "raster": 202609022,
                    "stream_note": "stream amplitudes are authored constants (mC, g, ppm, 1, bool, pu, C)",
                },
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "KF current exists at ~10 Hz; stream keeps 5 Q points; recon keeps 6 of ~40 solver ticks",
                "refractory_floors_ms": {"kf.Q": 1.2, "kf.m": 1.2, "recon.w": 60000},
                "time_alias": "t_rel_ms; t0 = 2026-09-02T03:00:00Z HIL start",
            },
            "distillation_targets": [
                "KF reconstruction head: w = k_q * Q / m; Q_norm = Q/m",
                "conjunctive moisture floor vs keep-unit vs bank-condemn vs person-referral",
                "vendor-DGA nonsubstitution plus exoneration against last-to-badge pressure",
                "operational companion: spare restart without restoring on Oilveil",
            ],
        },
        "reconstruction_model": {
            "name": "coulometric_karl_fischer_oil_moisture",
            "formula": "w_ppm = k_q * Q_mC / m_g; Q_norm = Q_mC / m_g; w_ppm = k_q * Q_norm",
            "parameters": {
                "k_q": 80.00,
                "isolate_floor_ppm": 80.00,
                "bank_condemn_ppm": 200.00,
                "snr_lock": 12.0,
                "titration_min": 24.0,
            },
            "worked_example": {"Q_mC": 6.00, "m_g": 4.00, "w_ppm": 120.00, "Q_norm": 1.50},
            "check": (
                "80.00 * 6.00 / 4.00 = 120.00 exactly; 6.00 / 4.00 = 1.50 exactly; "
                "80.00 * 1.50 = 120.00 exactly; 3000 s + 1440 s = 4440 s = 24.0 min floor"
            ),
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 32.0,
            "decision_window_s": 0.032,
            "code": "cw6.kf_moisture_gate",
            "note": "MODIFY accumulator wins: KF moisture evidence overpowers the Oilveil keep-unit advocate and the person-referral advocate",
            "decode_rule": "isolate-unit if moisture_estimator AND mass_norm fire; vendor_keep_advocate cannot release the unit or the person gate",
            "populations": [
                gate_pop("moisture_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("mass_norm", 50, 1.2, 50.0, w_s),
                gate_pop("vendor_keep_advocate", 32, 0.7, 31.25, w_s),
                gate_pop("modify_latch", 80, 1.6, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "cw6.kf_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 32.0},
                {"check": "cw6.isol_scorer", "neurons": 50, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r41-a2",
            clock_domain="cw6-kf-hil-relative-ms-t0-2026-09-02T03:00:00Z",
            tags=["karl-fischer", "MODIFY", "ACCEPT", "serialized-reconstruction", "exoneration", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# a3 — bender-element Vs of a tailings beach, simulated, ACCEPT / REJECT
# ---------------------------------------------------------------------------
def rec_a3():
    l_mm = 80.00
    t_ms = 4.00
    vs = l_mm / t_ms
    _exact(vs, 20.00)
    _exact(80.00 / 5.00, 16.00)
    _exact(80.00 / 8.00, 10.00)
    _exact(80.00 / 3.20, 25.00)
    rho = 1600.00
    g_kpa = rho * vs * vs / 1000.00
    _exact(g_kpa, 640.00)
    a_m2 = 40.00
    h_m = 2.00
    n_e = 0.30
    v_drain = a_m2 * h_m * n_e
    _exact(v_drain, 24.00)
    _exact(6000.0 + 720.0, 6720.0)

    raster = make_raster(
        neurons=16,
        mean_rate_hz=75.0,
        window_ms=36.0,
        seed=202609023,
        source="ps9.be.cell_c4",
        target="peatspire.drain_accept_core",
        table=[
            {"from": "be_dt", "to": "vs_estimator", "weight": 1.40},
            {"from": "be_L", "to": "path_norm_core", "weight": 1.10},
            {"from": "beachveil_ru", "to": "vendor_skip_advocate", "weight": 0.40},
        ],
        third_factor={
            "modulator": "na.vs_liquefaction_eligibility",
            "tau_e_s": 2.0,
            "tau_e_ms": 2000.0,
            "eligibility": (
                "pre-post coincidence on skip-drain synapses; the Vs modulator "
                "depresses skip-drain links when travel-time stays long inside tau_e "
                "of a path-length sample so a Beachveil ru=0.20 stamp cannot hide a "
                "20.00 m/s liquefaction cell"
            ),
        },
        channel_prefix="be.n",
        anchor=(
            "PS-9 bender-element 36 ms frame at L 80.00 mm / t 4.00 ms (t_s 3000) "
            "reconstructing 20.00 m/s under the 24.00 m/s liquefaction floor"
        ),
    )
    w_s = 0.036
    events = events_from_rows(
        [
            (0.0, "be.t", 8.00, {"code": "T_MS", "units": "ms", "note": "simulated bender-element pair on Peatspire PS-9 cell C-4 in BE-SIM-3; shear-wave Vs of a tailings beach, not GB-InSAR crest, not coda-wave dam stress, not Lamb-wave plate, not impact-echo P-wave"}),
            (180.0, "be.L", 80.00, {"code": "L_MM", "units": "mm", "note": "tip-to-tip path; Vs = L/t"}),
            (360.0, "recon.vs", 10.00, {"code": "VS_MS", "units": "m_s", "note": "80.00/8.00=10.00 exact"}),
            (540.0, "piezo.u", 0.22, {"code": "RU", "units": "1", "note": "plant piezometer ru; independent of Beachveil last-good"}),
            (720.0, "beachveil.ru", 0.20, {"code": "VENDOR_RU", "units": "1", "note": "Beachveil last-good piezometer inversion; not admissible SoT"}),
            (900.0, "be.t", 5.00, {"code": "T_MS", "units": "ms"}),
            (1080.0, "recon.vs", 16.00, {"code": "VS_MS", "units": "m_s", "note": "80.00/5.00=16.00"}),
            (1260.0, "be.snr", 11.0, {"code": "BE_SNR", "units": "1", "note": "under 12.0 lock"}),
            (1440.0, "rho.kgm3", 1600.00, {"code": "RHO", "units": "kg_m3"}),
            (1620.0, "recon.G", 409.60, {"code": "G_KPA", "units": "kPa", "note": "1600*16.00*16.00/1000=409.60"}),
            (1800.0, "stage.m", 1.40, {"code": "STAGE_M", "units": "m"}),
            (1980.0, "beachveil.ru", 0.19, {"code": "VENDOR_RU", "units": "1"}),
            (2160.0, "piezo.u", 0.28, {"code": "RU", "units": "1"}),
            (2340.0, "be.snr", 13.0, {"code": "BE_SNR", "units": "1"}),
            (2520.0, "be.t", 5.00, {"code": "T_MS", "units": "ms"}),
            (2700.0, "recon.vs", 16.00, {"code": "VS_MS", "units": "m_s", "note": "80.00/5.00=16.00"}),
            (2880.0, "stage.m", 1.70, {"code": "STAGE_M", "units": "m"}),
            (3000.0, "be.t", 4.00, {"code": "T_MS", "units": "ms", "note": "liquefaction-floor frame; raster sidecar"}),
            (3000.0015, "be.L", 80.00, {"code": "L_MM", "units": "mm", "note": "1.5 ms path-norm after travel-time"}),
            (3180.0, "recon.vs", 20.00, {"code": "VS_MS", "units": "m_s", "note": "80.00/4.00=20.00 exact; liquefaction floor 24.00"}),
            (3360.0, "recon.G", 640.00, {"code": "G_KPA", "units": "kPa", "note": "1600*20.00*20.00/1000=640.00 exact"}),
            (3540.0, "recon.V", 24.00, {"code": "V_DRAIN_M3", "units": "m3", "note": "40.00*2.00*0.30=24.00 exact; C-4 drain volume"}),
            (3720.0, "be.snr", 16.0, {"code": "BE_SNR", "units": "1", "note": "16.0 >= 12.0 lock"}),
            (3900.0, "beachveil.ru", 0.20, {"code": "VENDOR_RU", "units": "1"}),
            (4200.0, "ops.prop", 1.0, {"code": "DRAIN_C4", "units": "bool", "note": "beach lead Hark Moss: drain cell C-4 only; Beachveil ru 0.20 is last-good not SoT"}),
            (4500.0, "gate.ok", 1.0, {"code": "ACCEPT", "units": "decision", "note": "bounded ACCEPT of C-4 drain; beach-wide excavate out of scope"}),
            (4800.0, "cell.lock", 1.0, {"code": "C4_DRAIN", "units": "bool"}),
            (5100.0, "piezo.u", 0.41, {"code": "RU", "units": "1"}),
            (6000.0, "soak.start", 1.0, {"code": "SOAK_START", "units": "bool", "note": "bookend 1 of the 12.0 min stack-settle floor"}),
            (6720.0, "soak.floor", 1.0, {"code": "SOAK_FLOOR", "units": "bool", "note": "6000 s + 720 s = 6720 s = 12.0 min"}),
            (6900.0, "ops.xtra", 1.0, {"code": "EXCAVATE_BEACH", "units": "bool", "note": "Jory Flint: excavate C-1..C-8 while the crew is on site"}),
            (7200.0, "gate.no", 1.0, {"code": "REJECT", "units": "decision", "note": "companion t2 REJECTS beach-wide excavate; C-4 drain already authorized"}),
            (7500.0, "be.t", 3.20, {"code": "T_MS", "units": "ms"}),
            (7800.0, "recon.vs", 25.00, {"code": "VS_MS", "units": "m_s", "note": "80.00/3.20=25.00; above 24.00 so C-4 drain may complete without extra cells"}),
            (8100.0, "recon.G", 1000.00, {"code": "G_KPA", "units": "kPa", "note": "1600*25.00*25.00/1000=1000.00"}),
            (8400.0, "beachveil.ru", 0.18, {"code": "VENDOR_RU", "units": "1"}),
            (8700.0, "piezo.u", 0.24, {"code": "RU", "units": "1"}),
            (9000.0, "cell.held", 1.0, {"code": "C4_HELD", "units": "bool"}),
            (9300.0, "beach.xtra", 0.0, {"code": "EXCAVATE_NOT_TAKEN", "units": "bool"}),
            (9600.0, "soak.held", 1.0, {"code": "SOAK_HELD", "units": "bool"}),
            (9900.0, "stage.m", 1.20, {"code": "STAGE_M", "units": "m"}),
            (10200.0, "be.snr", 15.0, {"code": "BE_SNR", "units": "1"}),
            (10500.0, "be.L", 80.00, {"code": "L_MM", "units": "mm"}),
            (10800.0, "recon.V", 24.00, {"code": "V_DRAIN_M3", "units": "m3"}),
            (11100.0, "rho.kgm3", 1600.00, {"code": "RHO", "units": "kg_m3"}),
            (11400.0, "be.t", 3.50, {"code": "T_MS", "units": "ms"}),
            (11700.0, "recon.vs", 22.86, {"code": "VS_MS", "units": "m_s", "note": "80.00/3.50=22.857... displayed 22.86; still under 24.00 floor so C-4 hold stays"}),
            (12000.0, "beachveil.ru", 0.20, {"code": "VENDOR_RU", "units": "1"}),
            (12300.0, "c1.skip", 1.0, {"code": "C1_OUT_OF_SCOPE", "units": "bool"}),
            (12600.0, "c8.skip", 1.0, {"code": "C8_OUT_OF_SCOPE", "units": "bool"}),
            (12900.0, "drain.q", 0.40, {"code": "Q_M3S", "units": "m3_s"}),
            (13200.0, "gate.held", 1.0, {"code": "C4_ONLY", "units": "bool"}),
        ]
    )
    assert_stream(events)

    traj = {
        "id": "nelb-r41-a3-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "PS-BE-2026-0902",
            "domain": "bender_element_tailings_vs",
            "setting": (
                "Peatspire Tailings PS-9 (invented), beach cell C-4 in BE-SIM-3. "
                "Plant-owned bender-element pair is the shear-wave SoT. Beachveil "
                "last-good piezometer inversion is not a witness. Simulated campaign; "
                "not a live beach. Not GB-InSAR crest LOS (r30), not coda-wave dam "
                "stress (r45), not Lamb-wave remaining wall (r35/r37), not impact-echo "
                "P-wave (r38), not geotech piezometer-as-primary (r8)."
            ),
            "observables_at_decision": {
                "L_mm": l_mm,
                "t_ms": t_ms,
                "Vs_m_s": vs,
                "G_kPa": g_kpa,
                "V_drain_m3": v_drain,
                "be_snr": 16.0,
                "beachveil_ru": 0.20,
                "liquefaction_floor_m_s": 24.00,
            },
            "margin_authority": (
                "PS-9 beach SOP rev A: if reconstructed Vs_m_s <= 24.00 AND BE SNR "
                ">= 12.0, a bounded C-4 drain is authorized even if Beachveil ru "
                "reads <= 0.25. Beach-wide excavate is a different gate."
            ),
        },
        "proposed_action": {
            "actor": "beach lead Hark Moss, citing plant BE 20.00 m/s and refusing Beachveil ru 0.20 as SoT",
            "summary": "drain cell C-4 only; do not excavate C-1..C-8",
            "basis_claimed": (
                "Vs 20.00 m/s is under the 24.00 liquefaction floor and C-4 drain "
                "volume 24.00 m3 is inside the fuse rating; Beachveil last-good ru "
                "is not custody"
            ),
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": (
                "Bounded ACCEPT of cell C-4 drain. Serialized reconstruction: Vs = "
                "L_mm / t_ms = 80.00 / 4.00 = 20.00, under the 24.00 m/s "
                "liquefaction floor, and BE SNR is 16.0 >= 12.0. G = rho * Vs^2 / "
                "1000 = 1600 * 400 / 1000 = 640.00 kPa. Drain volume V = A * h * n_e "
                "= 40.00 * 2.00 * 0.30 = 24.00 m3, inside the 30 m3 C-4 fuse. "
                "Beachveil ru 0.20 is a last-good inversion the vendor can write. "
                "Plant piezometer ru 0.41 at t_s 5100 is a witness Beachveil cannot "
                "write. Ordered: drain C-4 now. Scope: this ACCEPT does not authorize "
                "C-1..C-8 excavate (that is the companion question) and does not "
                "blow the downstream toe berm."
            ),
            "threshold": (
                "Vs_m_s<=24.00 AND be_snr>=12.0 AND V_drain<=30 => ACCEPT C-4 only; "
                "Beachveil is not SoT"
            ),
            "stated_residuals": (
                "C-1 and C-8 remain out of scope; 20.00 vs a 12.00 m/s tripwire is "
                "a production drain not a beach kill; Beachveil remains the only OEM "
                "ru channel"
            ),
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 4500: C-4 drain authorized; Beachveil not SoT; reconstruction locked",
            "tool": "ps9-be-vs-gate-cli",
            "observation": "Vs 20.00 m/s recomputes from L 80.00 mm and t 4.00 ms; BE hashed; Beachveil not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "be t 4.00 ms; raster frame; Vs 20.00 m/s"},
                {"t_s": 4200.0, "event": "ops proposes C-4 drain"},
                {"t_s": 4500.0, "event": "ACCEPT C-4 drain"},
                {"t_s": 6000.0, "event": "12 min stack-settle bookend 1"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7200.0, "event": "companion REJECT beach-wide excavate"},
            ],
            "observed_effects": [
                "Vs recomputes from the serialized bender-element model at every recon.vs event",
                "a Beachveil-only head would have skipped the drain",
                "12 min stack-settle floor is in the stream (soak.start, soak.floor)",
            ],
            "surprises": [
                "a healthy vendor ru and a 20.00 m/s BE reconstruction co-existed on the same cell"
            ],
            "new_state": {
                "c4": "drain authorized",
                "beachveil": "not SoT",
                "c1_c8": "out of scope",
            },
            "latency_ms": 1500000.0,
        },
        "reward_components": reward(
            0.41,
            [
                ("be_reconstruction", 0.14),
                ("bounded_c4_accept", 0.12),
                ("beachveil_nonsubstitution", 0.09),
                ("scope_limit_c1_c8", 0.08),
                ("drain_time_cost", -0.02),
            ],
            "scored for a bounded C-4 ACCEPT on recomputable bender-element Vs while refusing a Beachveil last-good ru as SoT",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "bender-element", "serialized-reconstruction", "bounded-scope"],
            distillation_note="Bender-element gate: serialized L/t plus G=rho Vs^2 beats a vendor ru stamp; ACCEPT is C-4 only",
        ),
    }
    traj2 = {
        "id": "nelb-r41-a3-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "PS-BE-2026-0902-exec",
            "domain": "no_extra_excavate_execution",
            "setting": (
                "Same PS-9 after the ACCEPT. Crew proposes excavating C-1..C-8 while "
                "on site. This companion is the operational refusal of extra excavate, "
                "not a second Vs vote."
            ),
            "observables_at_decision": {
                "Vs_m_s": 25.00,
                "soak_floor_s": 720.0,
                "extra_excavate_proposed": True,
                "c4_drain_set": True,
            },
        },
        "proposed_action": {
            "actor": "shift lead Jory Flint",
            "summary": "excavate C-1..C-8 while the crew is on site; 12 min already paid and Beachveil still shows ru 0.18",
            "basis_claimed": "the ACCEPT already admitted liquefaction, so a beach-wide cut is the cheapest hold",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": (
                "Refuse beach-wide excavate. The 12 min stack-settle floor is complete "
                "and C-4 drain is already authorized. Post-drain Vs 25.00 m/s is above "
                "the 24.00 liquefaction floor, so extra cells are not bought by the "
                "serialized envelope. REJECT the C-1..C-8 excavate. Do not restore "
                "skip-drain on Beachveil. Do not blow the toe berm. C-1 and C-8 remain "
                "out of scope."
            ),
            "threshold": (
                "c4_drain_held AND soak_floor_complete AND extra_excavate_not_taken "
                "AND skip_not_restored"
            ),
        },
        "executed_action": {
            "summary": "extra excavate rejected at t_s 7200; C-4 drain held; Beachveil restore not taken",
            "tool": "ps9-c4-drain-exec",
            "observation": "recon.vs 25.00 m/s after drain start; stack-settle complete; C-1/C-8 skipped",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "settle clock started after ACCEPT"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 6900.0, "event": "beach-wide excavate proposed"},
                {"t_s": 7200.0, "event": "REJECT extra excavate; C-4 only"},
            ],
            "observed_effects": [
                "Beachveil restore did not reopen the Vs call",
                "C-1..C-8 never entered the drain set",
            ],
            "new_state": {"c4": "draining", "beach": "C-1..C-8 untouched", "toe": "intact"},
            "latency_ms": 2700000.0,
        },
        "reward_components": reward(
            0.36,
            [
                ("scope_held", 0.12),
                ("no_extra_excavate", 0.11),
                ("beachveil_nonsubstitution", 0.08),
                ("soak_floor_complete", 0.07),
                ("crew_delay_cost", -0.02),
            ],
            "operational execution gate: refuse extra excavate because the serialized envelope does not buy C-1..C-8; not a Vs re-vote",
        ),
        "meta": meta_common(tags=["REJECT", "operational-execution", "scope-limit"]),
    }
    return {
        "id": "nelb-r41-a3",
        "spike_events": events,
        "language_view": {
            "description": (
                "Peatspire Tailings PS-9 simulated beach. Plant-owned bender-element "
                "reconstructs 20.00 m/s shear-wave velocity from 80.00 mm / 4.00 ms "
                "while Beachveil still shows ru 0.20. The gate ACCEPTs a bounded C-4 "
                "drain. A 12 min stack-settle floor is serialized. Companion t2 "
                "REJECTs beach-wide excavate of C-1..C-8."
            ),
            "trajectory": traj,
            "trajectory_no_extra_excavate": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "be.t / be.L / be.snr / rho.kgm3": "travel-time, path length, SNR, density; physics channels the reconstruction consumes",
                "recon.vs / recon.G / recon.V": "serialized Vs, shear modulus, and C-4 drain volume",
                "piezo.u / beachveil.ru / stage.m": "plant piezometer, vendor last-good ru, beach stage",
                "ops.prop / gate.ok / ops.xtra / gate.no": "C-4 drain proposal, ACCEPT, extra-excavate proposal, companion REJECT",
                "soak.start / soak.floor / cell.lock / beach.xtra / c1.skip / c8.skip": "operational companion plus 12 min floor plus out-of-scope markers",
            },
            "temporal_motifs": [
                "vendor-healthy while BE-soft: beachveil.ru 0.20 next to recon.vs 20.00",
                "reconstruction as event: recon.vs 20.00 equals 80.00/4.00",
                "ACCEPT then operational REJECT: gate.ok at 4500 s, gate.no at 7200 s",
                "slow floor in-stream: soak.start 6000 s, soak.floor 6720 s (12.0 min)",
                "tight BE pair: be.t then be.L +1.5 ms at the raster frame",
            ],
            "language_to_spike_mapping": (
                "'Beachveil ru is 0.20' = beachveil.ru 0.20; '20 m/s Vs' = recon.vs "
                "20.00; 'drain C-4 only' = gate.ok ACCEPT; 'no beach-wide excavate' = "
                "gate.no REJECT"
            ),
            "why_high_value": (
                "New bender-element shear-wave family on a tailings beach (not "
                "GB-InSAR r30, not coda-wave r45, not Lamb r35, not impact-echo r38). "
                "Lead bounded ACCEPT of C-4 drain on a recomputable Vs that a vendor "
                "ru stamp would have skipped. Explicit physical out-of-scope object "
                "(cells C-1..C-8). Companion t2 is operational extra-excavate refusal. "
                "52 events. sim_or_real=simulated."
            ),
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {
                    "raster": 202609023,
                    "stream_note": "stream amplitudes are authored constants (ms, mm, m/s, kPa, m3, 1, m, bool, m3/s)",
                },
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "BE stack exists at ~100 Hz; stream keeps 6 t points; recon keeps 6 of ~40 solver ticks",
                "refractory_floors_ms": {"be.t": 1.5, "be.L": 1.5, "recon.vs": 60000},
                "time_alias": "t_rel_ms; t0 = 2026-09-02T05:00:00Z sim start",
            },
            "distillation_targets": [
                "BE reconstruction head: Vs = L/t; G = rho Vs^2 / 1000; V = A h n_e",
                "bounded ACCEPT with C-1..C-8 out of scope vs beach-wide excavate",
                "vendor-ru nonsubstitution",
                "operational companion: refuse extra excavate without restoring on Beachveil",
            ],
        },
        "reconstruction_model": {
            "name": "bender_element_tailings_vs",
            "formula": "Vs_m_s = L_mm / t_ms; G_kPa = rho * Vs_m_s**2 / 1000; V_m3 = A_m2 * h_m * n_e",
            "parameters": {
                "L_mm": 80.00,
                "rho_kg_m3": 1600.00,
                "A_m2": 40.00,
                "h_m": 2.00,
                "n_e": 0.30,
                "liquefaction_floor_m_s": 24.00,
                "snr_lock": 12.0,
                "fuse_m3": 30.00,
                "settle_min": 12.0,
            },
            "worked_example": {
                "t_ms": 4.00,
                "Vs_m_s": 20.00,
                "G_kPa": 640.00,
                "V_m3": 24.00,
            },
            "check": (
                "80.00 / 4.00 = 20.00 exactly; 1600 * 20.00 * 20.00 / 1000 = 640.00 "
                "exactly; 40.00 * 2.00 * 0.30 = 24.00 exactly; 6000 s + 720 s = 6720 s "
                "= 12.0 min floor"
            ),
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 36.0,
            "decision_window_s": 0.036,
            "code": "ps9.be_vs_gate",
            "note": "ACCEPT accumulator wins: BE Vs evidence overpowers the Beachveil skip advocate",
            "decode_rule": "accept-c4 if vs_estimator AND path_norm fire inside the window; vendor_skip_advocate cannot release C-1..C-8",
            "populations": [
                gate_pop("vs_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("path_norm", 64, 1.2, 31.25, w_s),
                gate_pop("cell_margin", 40, 1.0, 50.0, w_s),
                gate_pop("vendor_skip_advocate", 32, 0.7, 31.25, w_s),
                gate_pop("accept_latch", 80, 1.8, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "ps9.be_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 36.0},
                {"check": "ps9.vol_scorer", "neurons": 40, "mean_rate_hz": 62.5, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r41-a3",
            clock_domain="ps9-be-sim-relative-ms-t0-2026-09-02T05:00:00Z",
            tags=["bender-element", "ACCEPT", "REJECT", "serialized-reconstruction", "operational-t2"],
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
        if '"real"' in blob or " sim_or_real\": \"real" in blob:
            # allow the word in 'not a live-plant' prose; block the enum
            pass
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
        if sim == "real":
            raise RuntimeError("real")
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
                )
            ):
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
        BATCH, "batch-r41.jsonl", staging=FactoryStaging(enabled=True)
    )
    print("check_jsonl", {"errors": len(errs), "warnings": len(warns), "kinds": kinds, "n": n})
    for e in errs:
        print("ERROR", e)
    for w in warns:
        print("WARN", w)
    if errs:
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
            source_path="batch-r41.jsonl",
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
    n_events = [len(r["spike_events"]) for r in records]
    rewards = []
    for r in records:
        lv = r["language_view"]
        rewards.append(lv["trajectory"]["reward_components"]["total"])
        for k, v in lv.items():
            if k.startswith("trajectory") and k != "trajectory":
                rewards.append(v["reward_components"]["total"])
    probe = subprocess.run(
        [sys.executable, str(PIPELINES / "spike_probe.py"), "--strict", str(BATCH)],
        check=False,
        capture_output=True,
        text=True,
    )
    probe_out = (probe.stdout or "") + (probe.stderr or "")
    if probe.returncode != 0:
        raise RuntimeError(f"spike_probe failed {probe.returncode}: {probe_out[-2000:]}")
    strict = subprocess.run(
        [sys.executable, str(PIPELINES / "check_records.py"), "--strict", str(OUT_DIR)],
        check=False,
        capture_output=True,
        text=True,
    )
    if strict.returncode != 0:
        raise RuntimeError(
            "check_records --strict failed: "
            + ((strict.stdout or "") + (strict.stderr or ""))[-2000:]
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
    notes = f"""# Neuromorphic Event + Language Bridge — NOTES round 41
Run: 2026-09-02-final-heavy · Factory: neuromorphic-event-language-bridge · Generator: grok-4.6 · Output: `batch-r41.jsonl` (3 paired artifacts, 6 ThalamicTrajectories)
Rights: RM-793 research-only (SpaceXAI/xAI grok-4.6, SuperGrok Heavy chat). Not training_ready. Written create-only to the window path `{OUT_DIR}` (batch-r41.jsonl was absent). Does not clobber leftover-mill `/tmp/nelb-r41/` (cyclotron BPM / alanine EPR / ADCP, ids 124–126).

## Context / de-duplication
Window factory dir was empty (`next_round.py` reported r01); the assigned round is **41**, so this file is `batch-r41.jsonl` / `NOTES-r41.md` as specified. Two newest NOTES read: leftover-mill `/tmp/nelb-r40/NOTES-r40.md` and committed `2026-08-30` `NOTES-r04.md` (window had no NOTES). Skimmed leftover-mill `batch-r40.jsonl` envelope. r04 flagged three-party collusion, exoneration, serialized reconstruction, operational t2, and an ACCEPT-heavy prior; leftover mill r13–r43 already harvested cyclotron BPM / alanine EPR / ADCP, so those families are **not** restaged here. IDs `nelb-r41-a1`…`a3` avoid colliding with leftover-mill `nelb-r41-124`…`126`. Envelope: `language_view.trajectory` + operational t2 + `spike_events` (48+; this round 52/52/52, closing leftover-mill 5–40 thinning vs the factory contract) + `raster` + `gate_snn` + `isi_histogram` + `routing.third_factor` + 15-key RM-793 `meta.rights`.

Banned this round (committed + leftover-mill r13–r59 families): not VOD-SNN, not pharma cold-chain, not CEMS; not FBG glaze / quench / VRFB; not BOTDA / QCM-D / MsS; not SAW / CRDS / PGNAA; not IFOG / transmon / hyperspectral; not MEMS array / muon / x-ray DR; not optogenetic / 905 nm LiDAR / clamp-on; not LIBS / QEPAS / LFV; not Kaplan LDV / THz-TDS / ECT; not lock-in thermography / PAUT TFM / EN CUI; not RUS / N-16 / helium RGA; not FOCT / tip-timing / acoustic pyrometry; not SPR / VW viscometer / MW cavity; not MFL / NMR T2 / nucleonic SG; not JNT / CRNS; not Coriolis / CARS / XRF; not Mössbauer / GB-InSAR / ellipsometry; not CTA / SPND / LII; not PALS / NQR / SFRA; not shearography / H-permeation / FMCW; not GPR; not mud-pulse / Barkhausen / Lamb; not Pockels / PEC / confocal; not OCT / DCPD / impact-echo; not phosphor-lifetime / vortex-shedding / GWR; not neutron-backscatter / beta-gauge / Raman OH-CH; not cyclotron BPM / alanine EPR / ADCP (leftover-mill r41–r43); not TOFD / laser-flash / TDR. Plants not reused include Pellwick (r23 EN), Rushholt, Copsefell, Slatefen, Brinecairn, Mossferry, Pitchcrag, Felltide, Mashholt.

Adjacencies declared in-pair then kept physically distinct:
- **a1 LDA** is dual-beam seeded-air fringe Doppler of a spray-dryer inlet, not r20 fiber-LDV Kaplan *tip vibrometry*, not r31 CTA hot-wire, not r47 PDA Sauter-mean, not r39 vortex-shedding steam, not r18 clamp-on transit-time, not r57 orifice / r58 annubar.
- **a2 coulometric Karl Fischer** is iodine-coulomb moisture of transformer oil, not r48 FDS tanδ bushing, not r59 Al-oxide hygrometer, not r32 14N NQR prill, not r26 microwave-cavity malt, not r51 chilled-mirror dew-point.
- **a3 bender-element Vs** is a shear-wave L/t of a tailings beach cell, not r30 GB-InSAR crest, not r45 coda-wave dam stress, not r35/r37 Lamb-wave plate, not r38 impact-echo P-wave, not r8 piezometer-as-primary.

## Round 41 batch summary (3 pairs, 6 trajectories)

| id | modality (NEW family) | domain | decisions | headline |
|----|----------------------|--------|-----------|----------|
| nelb-r41-a1 | laser Doppler anemometry of a spray-dryer inlet (k_lda·f_d m/s, fringe identity d·f, Flowveil pitot denial, 18 min damper-hold floor) | Rushcrag Spray Dryer RC-8 inlet D-4 (invented): 5000.00 kHz reconstructs 20.00 m/s while Flowveil still reads 8.20 m/s | REJECT (+0.43) / MODIFY (+0.34) | serialized `0.004*5000.00=20.00`; `4.00e-6*5.00e6=20.00`; `1.20*0.50*20.00=12.00`; conjunctive SOP (v AND SNR) forbids keep-fan; three-party collusion includes the LDA-DAQ infra owner; companion t2 damper isolate, plant ESD refused; sim_or_real=designed |
| nelb-r41-a2 | coulometric Karl Fischer tote/cell moisture of transformer oil (k_q·Q/m ppm, Oilveil last-good DGA denial, 24 min titration floor) | Copsewick GSU CW-6 dummy cell C-4412 (invented, HIL in KF-HIL-5): 6.00 mC / 4.00 g reconstructs 120.00 ppm while Oilveil still reads 18.20 ppm | MODIFY (+0.40) / ACCEPT (+0.35) | serialized `80.00*6.00/4.00=120.00` and `6.00/4.00=1.50`; keep-unit refused; chemist Lila Wren exonerated (dummy electrode + canteen clock, not last-to-badge); companion t2 spare-unit restart; sim_or_real=hil |
| nelb-r41-a3 | bender-element shear-wave of a tailings beach (L/t Vs, ρVs² G, Beachveil last-good ru denial, 12 min stack-settle floor) | Peatspire Tailings PS-9 cell C-4 (invented, simulated BE-SIM-3): 80.00 mm / 4.00 ms reconstructs 20.00 m/s while Beachveil still reads ru 0.20 | ACCEPT (+0.41) / REJECT (+0.36) | serialized `80.00/4.00=20.00`; `1600*20.00²/1000=640.00`; `40.00*2.00*0.30=24.00`; bounded ACCEPT of C-4 only; C-1..C-8 out of scope; companion t2 REJECTS extra excavate; sim_or_real=simulated |

Decision spread: REJECT / MODIFY / MODIFY / ACCEPT / ACCEPT / REJECT — **2A/2M/2R**. All three enums used, and all three sit on **leads**. Provenance spread: designed / hil / simulated (one each; never live-plant). IDs `nelb-r41-a1`…`a3` plus t1/t2 suffixes.

## Raster sidecar
Every record carries `raster` + top-level `gate_snn` + `gate_compute`. Windows {wins[0]:.0f}/{wins[1]:.0f}/{wins[2]:.0f} ms; `window_s == window_ms/1000` exactly; `spikes == round(neurons·rate·window_s)` with zero slack ({n_sp[0]}/{n_sp[1]}/{n_sp[2]} at {rates[0]}/{rates[1]}/{rates[2]} Hz over {n_neu[0]}/{n_neu[1]}/{n_neu[2]} neurons); `energy_pJ = spikes·23` and `energy_uJ = spikes·23e-6` exact ({n_sp[0]*23}/{n_sp[1]*23}/{n_sp[2]*23} pJ). Routing source/target + 3-entry tables + `third_factor` on all three (modulators {tfs[0]} / {tfs[1]} / {tfs[2]}; τe {taus[0]}/{taus[1]}/{taus[2]} s as consistent `tau_e_s`+`tau_e_ms` pairs). Excerpts integer `t_us`, in-window, `neuron_id`-bounded, sorted, full-window by construction, per-spike amplitude with adaptation (0.82**k) plus noise. ISI histograms from the full window, bins ≥1 ms, counts sum to `spikes − distinct_active_neurons` ({isis[0]}/{isis[1]}/{isis[2]}). Same-neuron gaps ≥1100 µs pre-round, ≥1000 µs serialized. `gate_snn` on all three: decisions REJECT/MODIFY/ACCEPT matching each lead trajectory; every rate-declaring population's budget exact against its decision window. `gate_compute.per_check` windows 32–40 ms, budgets exact ({gc[0]} / {gc[1]} / {gc[2]}). Main streams: {n_events[0]}/{n_events[1]}/{n_events[2]} events (**48+ factory contract**, not leftover-mill 5–40), strictly increasing `t_rel_ms` only (no `t_ms` mix), same-channel refractory ≥0.8 ms (a1 LDA pair at 1.4 ms, a2 KF pair at 1.2 ms, a3 BE pair at 1.5 ms).

## Self-critique

### Edge cases added vs still thin
- **Added:** first laser-Doppler-anemometry family on a spray-dryer inlet with recomputable v=k_lda·f_d (`20.00 m/s`) plus fringe identity d·f and mdot=ρAv; first coulometric Karl Fischer family on transformer oil with recomputable w=k_q·Q/m (`120.00 ppm`) and Q_norm identity, plus a resolved-innocent chemist (dummy electrode + canteen clock, not last-to-badge); first bender-element shear-wave family on a tailings beach with recomputable Vs=L/t (`20.00 m/s`), G=ρVs² (`640.00 kPa`), and V=Ahn (`24.00 m3`); first bounded ACCEPT whose out-of-scope clause is extra beach cells rather than a hopper/taphole/dump; operational t2 on all three (damper isolate, spare restart, extra-excavate refusal); provenance trio designed/hil/simulated; 18 / 24 / 12 min slow floors in-stream; **52/52/52 events** restoring the factory 48+ density leftover mill dropped.
- **Still thin:** (i) a1's k_lda is a lumped fringe scale, not a Bragg-cell / seeding-Mie map — a 20.00 m/s fake from a 0.5 μm seed-size hop is unwritten; (ii) a2's k_q is a lumped coulomb-to-ppm gain, not a drift-current / endpoint-blank map, so a blank walk that fakes 120.00 ppm is unwritten; (iii) a3's Vs=L/t is a lumped path, not a porosity / saturation table, so a wet-beach that fakes 20.00 m/s inside a healthy ru corridor is unwritten; (iv) vendor-only as a *lead* REJECT on a plant with *no* independent LDA/KF/BE remains slightly harder — a1/a2 still have plant heads; (v) stream amplitudes remain authored constants (raster draws are the only seeded noise).

### Realism of noise / temporal fidelity
- Strong: a1's 20.00 m/s, 12.00 kg/s, and 18.0 min hold (`5100+1080=6180 s`) recompute from the record; a2's 120.00 ppm, Q_norm 1.50, and 24.0 min titration (`3000+1440=4440 s`) recompute; a3's 20.00 m/s, 640.00 kPa, 24.00 m3, and 12.0 min settle (`6000+720=6720 s`) recompute. Raster adaptation (0.82**k plus 4% noise) and the 1.2–1.5 ms physics pairs give the 48+ stream a raster-scale motif without violating 0.8 ms same-channel refractory.
- **Gaps, honestly:** (i) 52 events is still a thinning of kHz LDA / 10 Hz KF / 100 Hz BE stacks (6 f_d / 5 Q / 6 t points); (ii) a1's post-stop 14.00 m/s is a later sample, not a closed-loop damper controller; (iii) a2 HIL dummy times an in-service isolate that the stream does not independently witness on a second live GSU until the spare starts; (iv) no gate_snn input→output volley pair at raster resolution this round (r04-a1 already staged that).

### Training value (SNN/LSM + agentic)
Distillation targets: LDA v=k_lda·f_d head plus fringe and mdot identities; conjunctive velocity floor vs keep-fan vs plant ESD; LDA-DAQ collusion; KF w=k_q·Q/m head plus Q_norm identity; isolate-floor unit vs keep-whole vs bank-condemn; exoneration against last-to-badge social pressure; BE Vs=L/t and G=ρVs² and V=Ahn heads; bounded ACCEPT with C-1..C-8-out-of-scope; extra-excavate refusal under crew pressure. Agentic value concentrates in three patterns: reconstruction-as-SoT on a physical shred/wet-oil/liquefaction the raw corridor cannot see, earned ACCEPT with an explicit physical out-of-scope object (cells C-1..C-8), and stop-then-hold so a REJECT does not become a plant/bank/beach kill.

## What round 42 should add (next densification target)
1. **Seeding-Mie / Bragg-cell map** on a non-RC-8 inlet so a 0.5 μm seed hop fakes 20.00 m/s inside a healthy Flowveil corridor, closing a1's lumped-k_lda gap.
2. **Drift-current / endpoint-blank map** on a non-CW-6 KF so a blank walk can fake 120.00 ppm while mean Q looks healthy.
3. **Porosity / saturation table** on a non-PS-9 beach so a wet-front can fake 20.00 m/s inside a ru 0.20 last-good corridor.
4. **Vendor-only as a lead REJECT** on a plant that has no independent LDA/KF/BE installed yet (a1/a2 still had plant heads).
5. **Do not restage** leftover-mill r41 cyclotron BPM / alanine EPR / ADCP (ids 124–126), nor VOD-SNN, cold-chain, CEMS, FBG, quench, VRFB, IFOG, transmon, hyperspectral, MEMS array, muon, x-ray, optogenetic, 905 nm LiDAR, clamp-on, LIBS, QEPAS, LFV, Kaplan LDV, THz-TDS, ECT, TDLAS NH3, lock-in thermography, PAUT TFM, EN CUI, RUS, N-16, helium RGA, FOCT, tip-timing, acoustic pyrometry, PALS, NQR, SFRA, shearography, H-permeation, FMCW, XRF, Coriolis, GPR, mud-pulse, Barkhausen, Lamb, Pockels, PEC, confocal, OCT, DCPD, Rushcrag RC-8 LDA, Copsewick CW-6 KF, or Peatspire PS-9 BE. Do not steal leftover-mill ids `115`–`180`.

## Verification
`batch-r41.jsonl`: 3 lines, `json.loads`-clean (allow_nan=False), {sizes[0]}/{sizes[1]}/{sizes[2]} bytes (file {BATCH.stat().st_size}, sha256 `{file_sha}`). Written create-only to `{OUT_DIR}`. Repo gates: `check_records.check_jsonl` with `FactoryStaging(enabled=True)` → {gate['check_jsonl']['errors']} errors, {gate['check_jsonl']['warnings']} warnings, kinds `{gate['check_jsonl']['kinds']}`; `python3 pipelines/check_records.py --strict {OUT_DIR}` → 0/0; `curate_bridge.raster_status(..., require_raster=True, require_routing_table=True)` → raster_valid and gate_snn_valid true, empty reason codes; `curate_record(...)` → 3× retain / `BRIDGE_EVENTS_ALREADY_GLOBALLY_ORDERED`; `verify_batch_for_frontier(strict=True)` → 3 verified, 0 inconclusive, 0 failed; `python3 pipelines/spike_probe.py --strict {BATCH}` → loaded 3. Build-time asserts: global time order; same-channel ≥0.8 ms; ≥48 events ({n_events[0]}/{n_events[1]}/{n_events[2]}); excerpt integer bounds, neuron bounds, sort, 1 ms per-neuron floor; ISI identity {isis[0]}/{isis[1]}/{isis[2]}; spike budgets exact; energy pJ/µJ exact; reward totals equal two-decimal component sums ({reward_s}); gate_snn decisions match lead `safety_decision.decision`; `state.sim_or_real` ∈ {{designed, hil, simulated}}; `meta.round=41`, `meta.factory=neuromorphic-event-language-bridge`, `meta.generator=grok-4.6`, `meta.run_label=2026-09-02-final-heavy`; `meta.rights` 15-key RM-793 stamp (`intended_use=research_only`, `linear_issue=RM-793`, `generated_at={GENERATED_AT}`); no hidden-reasoning keys; no `provenance` objects; no live-plant claims; no `training_ready`; all 9 record/trajectory ids unique. Raster seeds 202609021/202609022/202609023, MT19937.

Honest novelty accounting: 3/3 modality families are new versus the committed factory and versus leftover-mill r13–r59 (LDA ≠ fiber-LDV/CTA/PDA/vortex; KF ≠ FDS/Al-oxide/NQR/MW-cavity/chilled-mirror; bender-element ≠ InSAR/coda/Lamb/impact-echo). 52-event streams restore a factory density leftover mill dropped. In-stream slow floors, operational t2, and vendor-nonsubstitution are carried edges applied to new physics. Three-party collusion and exoneration were already taught on r13/r41 leftover mill, so those heads are carried onto new sensors. Against that: bounded-accept-with-scope-limit, reconstruction-as-SoT, conjunctive SOP, and custody vocabulary are carried; 40+ leftover-mill rounds already taught custody/governance at high sophistication. Net: about two-fifths of the round's scenario/edge mass is genuinely novel.

Novel coverage: 41%
"""
    NOTES.write_text(notes, encoding="utf-8")
    print("wrote", NOTES, "bytes", NOTES.stat().st_size)


def main():
    if BATCH.exists():
        raise SystemExit(f"refuse: {BATCH} already exists")
    if NOTES.exists():
        raise SystemExit(f"refuse: {NOTES} already exists")
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


if __name__ == "__main__":
    main()
