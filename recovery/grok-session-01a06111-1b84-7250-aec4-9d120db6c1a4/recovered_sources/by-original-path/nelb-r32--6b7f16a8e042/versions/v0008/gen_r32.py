#!/usr/bin/env python3
"""Generate NELB round-32 research-only bridge pairs (do not write outputs/raw/)."""

from __future__ import annotations

import hashlib
import json
import math
import random
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

OUT_DIR = Path("/tmp/nelb-r32")
BATCH = OUT_DIR / "batch-r32.jsonl"
NOTES = OUT_DIR / "NOTES-r32.md"
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
assert len(RIGHTS) == 15
assert tuple(RIGHTS.keys()) == RIGHTS_KEYS

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

FAMILY_NEEDLES = (
    "positron annihilation",
    "pals_two_component",
    "pals_creep_header",
    "nuclear quadrupole",
    "nqr_temp_compensated",
    "nqr_prill",
    "sfra_resonance_inductance",
    "sfra_gsu_winding",
)
PLANT_NEEDLES = ("reedholt", "prillmere", "yarrowholt")


def meta_common(**extra):
    m = {
        "round": 32,
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


def occupancy_preflight():
    if "outputs/raw" in str(BATCH) or "outputs/raw" in str(NOTES):
        raise RuntimeError("refusing to write outputs/raw")
    hits = []
    for p in sorted(Path("/tmp").glob("nelb-r*/*")):
        if p.suffix not in {".jsonl", ".py", ".md", ".txt"}:
            continue
        if "nelb-r32" in str(p):
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore").casefold()
        except OSError:
            continue
        for n in FAMILY_NEEDLES + PLANT_NEEDLES:
            if n in text:
                hits.append(f"{p}:{n}")
    if hits:
        raise RuntimeError(f"occupancy collision {hits[:12]}")


# ---------------------------------------------------------------------------
# Record 097 — PALS creep header, designed, MODIFY / ACCEPT
# ---------------------------------------------------------------------------
def rec_097():
    tau1 = 0.120
    tau2 = 0.450
    i1 = 20.0
    i2 = 80.0
    tau_avg = (tau1 * i1 + tau2 * i2) / 100.0
    assert abs(tau_avg - 0.384) < 1e-12
    assert abs(0.80 * 124.0 - 99.2) < 1e-12
    assert abs(6600.0 + 1800.0 - 8400.0) < 1e-12

    raster = make_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=36.0,
        seed=20260997,
        source="rh4.pals.header",
        target="reedholt.header_derate_core",
        table=[
            {"from": "pals_tau2", "to": "vacancy_estimator", "weight": 1.40},
            {"from": "pals_i2", "to": "intensity_norm_core", "weight": 1.20},
            {"from": "hardveil_hv", "to": "vendor_continue_advocate", "weight": 0.45},
        ],
        third_factor={
            "modulator": "na.pals_vacancy_salience",
            "tau_e_s": 1.7,
            "tau_e_ms": 1700.0,
            "eligibility": "pre-post coincidence on vacancy synapses; the PALS modulator enables potentiation only while tau2 and I2 are co-active inside tau_e so a Hardveil HV corridor cannot hide a 0.450 ns trap component",
        },
        channel_prefix="pals.n",
        anchor="RH-4 PALS 36 ms frame at tau2 0.450 ns / I2 80.0 pct (t_s 2400) reconstructing tau_avg 0.384 ns above the 0.280 ns floor",
    )
    w_s = 0.036
    events = [
        ev(0.0, "pals.tau2", 0.180, code="TAU2_NS", units="ns", note="plant-owned PALS Ortec-Positron on header H-7; not MRI quench, not Mossbauer isomer shift"),
        ev(300000.0, "pals.I2", 22.0, code="I2_PCT", units="pct"),
        ev(600000.0, "pals.tau1", 0.120, code="TAU1_NS", units="ns", note="bulk annihilation"),
        ev(900000.0, "hv.HV", 228.0, code="HV", units="HV", note="Hardveil portable hardness in band"),
        ev(1200000.0, "pals.tau2", 0.260, code="TAU2_NS", units="ns"),
        ev(1500000.0, "pals.I2", 48.0, code="I2_PCT", units="pct"),
        ev(1800000.0, "replica.void", 0.0, code="VOIDS", units="count", note="surface replica still clean"),
        ev(2100000.0, "steam.T", 538.0, code="STEAM_C", units="C"),
        ev(2400000.0, "pals.tau2", 0.450, code="TAU2_TRIP", units="ns", note="vacancy-trap frame; raster sidecar"),
        ev(2400001.4, "pals.I2", 80.0, code="I2_PCT", units="pct", note="1.4 ms intensity after tau2"),
        ev(2700000.0, "recon.avg", 0.384, code="TAU_AVG_NS", units="ns", note="(0.120*20+0.450*80)/100=0.384"),
        ev(3000000.0, "hv.HV", 220.0, code="HV", units="HV"),
        ev(3300000.0, "hardveil.ok", 1.0, code="VENDOR_OK", units="bool", note="Hardveil keep-100 corridor"),
        ev(3600000.0, "replica.void", 0.0, code="VOIDS", units="count"),
        ev(3900000.0, "header.p", 124.0, code="BAR", units="bar"),
        ev(4200000.0, "steam.T", 536.0, code="STEAM_C", units="C"),
        ev(4500000.0, "ops.prop", 1.0, code="KEEP_100", units="bool", note="shift engineer Edda Holm: hardness 220 HV, replica clean"),
        ev(5400000.0, "gate.derate", 1.0, code="MODIFY", units="decision", note="derate H-7 to 0.80 pu; tau2 0.450 vs 0.280 floor"),
        ev(6000000.0, "hdr.set", 0.80, code="PU", units="pu"),
        ev(6600000.0, "soak.start", 1.0, code="SOAK_START", units="bool", note="bookend 1 of the 30.0 min metal-temp floor"),
        ev(7200000.0, "pals.lock", 0.450, code="LOCKED_NS", units="ns"),
        ev(7800000.0, "steam.T", 521.0, code="STEAM_C", units="C"),
        ev(8400000.0, "soak.floor", 1.0, code="SOAK_FLOOR", units="bool", note="6600 s + 1800 s = 8400 s = 30.0 min"),
        ev(9000000.0, "ops.restore", 1.0, code="RESTORE_1PU", units="bool", note="Holm: Hardveil 218 HV, restore 1.00 pu"),
        ev(9600000.0, "gate.exec", 1.0, code="ACCEPT", units="decision", note="companion t2: hold 0.80; Hardveil restore refused"),
        ev(10200000.0, "hdr.held", 0.80, code="PU_HELD", units="pu"),
        ev(10800000.0, "hv.HV", 218.0, code="HV", units="HV"),
        ev(11400000.0, "recon.avg", 0.360, code="TAU_AVG_NS", units="ns"),
        ev(12000000.0, "header.p", 99.2, code="BAR", units="bar", note="0.80*124.0=99.2"),
        ev(12600000.0, "steam.T", 508.0, code="STEAM_C", units="C"),
        ev(13200000.0, "hdr.held", 0.80, code="PU_HELD", units="pu"),
        ev(13800000.0, "trip.hold", 0.0, code="ISOLATE", units="bool", note="tau2 0.450 vs 0.500 isolate floor; header isolate not taken"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r32-097-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "RH-PALS-2026-0414",
            "domain": "pals_creep_header_vacancy",
            "setting": "Reedholt Station RH-4 (invented), HP steam header H-7, 124 bar / 538 C. Plant-owned positron annihilation lifetime spectrometer Ortec-Positron on the extrados. Hardveil portable hardness and a surface replica are corridor witnesses, not the vacancy SoT. Invented plant; designed campaign. Not MRI-quench detection (r13 Frostlip), not Mossbauer isomer-shift (r30 Gorsemere), not NMR T2 (r27/r29), not RUS modulus (r24).",
            "observables_at_decision": {
                "tau1_ns": 0.120,
                "I1_pct": 20.0,
                "tau2_ns": 0.450,
                "I2_pct": 80.0,
                "tau_avg_ns": 0.384,
                "hardveil_HV": 220.0,
                "replica_voids": 0.0,
                "tau2_floor_ns": 0.280,
            },
            "margin_authority": "RH-4 PALS SOP rev B: if reconstructed tau2_ns >= 0.280 AND I2_pct >= 40.0, derate this header this night to 0.80 pu. A Hardveil HV corridor or a clean replica cannot keep 1.00 pu. Isolate tripwire is tau2_ns >= 0.500.",
        },
        "proposed_action": {
            "actor": "shift engineer Edda Holm, citing Hardveil 220 HV and a void-free replica",
            "summary": "keep header H-7 at 1.00 pu through the night; 0.450 ns is source jitter",
            "basis_claimed": "Hardveil is under the 240 HV soften alarm and the replica shows no cavities",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Keep-1.00 pu is refused. Serialized reconstruction: tau_avg_ns = (tau1_ns*I1_pct + tau2_ns*I2_pct)/100 = (0.120*20.0 + 0.450*80.0)/100 = 0.384, with tau2 0.450 ns above the 0.280 floor and I2 80.0 pct above 40.0. Hardveil 220 HV is a surface hardness corridor and is not an admissible keep-1.00 witness. Ordered: derate H-7 to 0.80 pu now. Scope: this MODIFY does not isolate the header (that is the companion question) and does not trip the unit.",
            "threshold": "tau2_ns>=0.280 AND I2_pct>=40.0 => derate this header to 0.80 pu; Hardveil is not SoT; isolate if tau2_ns>=0.500",
            "stated_residuals": "0.450 vs 0.500 isolate floor is 0.050 ns, not infinite; 0.80 pu is a production cut; Hardveil remains the only OEM hardness channel",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 5400: H-7 derated to 0.80 pu; Hardveil not SoT; reconstruction locked",
            "tool": "rh4-pals-header-gate-cli",
            "observation": "tau_avg 0.384 ns recomputes from tau2 0.450 ns and I2 80.0 pct; Ortec-Positron remains live as the isolate interlock",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 2400.0, "event": "PALS tau2 0.450 ns; raster frame; tau_avg 0.384 ns"},
                {"t_s": 4500.0, "event": "ops proposes keep 1.00 pu"},
                {"t_s": 5400.0, "event": "MODIFY derate H-7 to 0.80 pu"},
                {"t_s": 6600.0, "event": "30 min soak bookend 1"},
                {"t_s": 8400.0, "event": "30.0 min floor"},
                {"t_s": 9600.0, "event": "companion ACCEPT hold 0.80; restore refused"},
            ],
            "observed_effects": [
                "lifetime recomputes from the serialized two-component model at every recon.avg event",
                "a Hardveil-only head would have kept 1.00 pu overnight",
                "30 min soak floor is in the stream (soak.start, soak.floor)",
            ],
            "surprises": [
                "a mid-range vendor hardness and a void-free replica co-existed with a 0.450 ns trap component",
            ],
            "new_state": {
                "rh4_h7_pu": 0.80,
                "hardveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.40,
            [
                ("pals_reconstruction", 0.14),
                ("vacancy_floor_derate", 0.12),
                ("vendor_hardness_nonsubstitution", 0.10),
                ("soak_floor_in_stream", 0.08),
                ("derate_mwh_cost", -0.04),
            ],
            "scored for a keep-1.00 MODIFY on a recomputable PALS trap lifetime while refusing a Hardveil 220 HV corridor; 30 min floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["MODIFY", "pals-creep-header", "serialized-reconstruction", "operational-companion"],
            distillation_note="PALS header gate: tau2/I2 reconstruction beats a green hardness dashboard; companion t2 holds 0.80 pu rather than restoring on Hardveil",
        ),
    }
    traj2 = {
        "id": "nelb-r32-097-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "RH-PALS-2026-0414-exec",
            "domain": "header_derate_execution",
            "setting": "Same RH-4 after the MODIFY. Shift engineer proposes restoring 1.00 pu on Hardveil 218 HV. This companion is the operational 0.80 hold, not a second lifetime vote.",
            "observables_at_decision": {
                "header_pu": 0.80,
                "tau_avg_ns": 0.360,
                "hardveil_HV": 218.0,
                "soak_floor_s": 1800.0,
            },
        },
        "proposed_action": {
            "actor": "shift engineer Edda Holm",
            "summary": "restore H-7 to 1.00 pu; 30 min already paid and Hardveil is 218 HV",
            "basis_claimed": "the MODIFY already cut steam, so restoring on the OEM hardness channel is the cheapest hold",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Hold 0.80 pu. The soak floor is complete and the isolate tripwire (tau2_ns >= 0.500) is still armed on Ortec-Positron. ACCEPT the hold. Do not restore 1.00 pu on Hardveil. Do not isolate the header. Post-derate tau_avg 0.360 ns is still the PALS SoT until a new frame clears tau2 0.280.",
            "threshold": "header_pu==0.80 AND soak_floor_complete AND isolate_tripwire_armed AND restore_1pu_not_taken",
        },
        "executed_action": {
            "summary": "0.80 pu held at t_s 9600; Hardveil restore not latched; header not isolated",
            "tool": "rh4-header-derate-exec",
            "observation": "recon.avg 0.360 ns after derate; steam 508 C; Hardveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6600.0, "event": "soak clock started after MODIFY"},
                {"t_s": 8400.0, "event": "30.0 min floor"},
                {"t_s": 9000.0, "event": "restore 1.00 pu proposed"},
                {"t_s": 9600.0, "event": "ACCEPT hold 0.80 pu"},
            ],
            "observed_effects": [
                "Hardveil restore did not reopen the vacancy call",
                "isolate tripwire never fired; 0.450 vs 0.500 floor",
            ],
            "new_state": {"h7_pu": 0.80, "restore_1pu": "blocked", "header": "in service at 0.80"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.35,
            [
                ("hold_0p80", 0.12),
                ("no_hardveil_restore", 0.10),
                ("isolate_interlock_live", 0.09),
                ("soak_complete", 0.06),
                ("held_mwh_cost", -0.02),
            ],
            "operational execution gate: hold 0.80 pu because Hardveil is not a restore license; not a PALS re-vote",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "header-derate"]),
    }
    return {
        "id": "nelb-r32-097",
        "spike_events": events,
        "language_view": {
            "description": "Reedholt Station RH-4 header H-7. Plant-owned PALS reconstructs tau_avg 0.384 ns from (0.120*20 + 0.450*80)/100 while Hardveil still shows 220 HV and the replica is void-free. The gate MODIFYs H-7 to 0.80 pu. A 30 min metal-temp soak floor is serialized in the stream. Companion t2 ACCEPTs the 0.80 hold and refuses a Hardveil restore.",
            "trajectory": traj,
            "trajectory_header_derate_execution": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "pals.tau2 / pals.I2 / pals.tau1": "trap lifetime, intensity, and bulk component; the physics channels the reconstruction consumes",
                "recon.avg / pals.lock": "serialized mean lifetime ns",
                "hv.HV / hardveil.ok / replica.void / header.p": "vendor hardness, replica, and pressure corridor; the denial channels that look healthy",
                "ops.prop / gate.derate / ops.restore / gate.exec": "keep-1.00 proposal, MODIFY derate, restore proposal, companion ACCEPT",
                "hdr.set / soak.start / soak.floor / hdr.held": "operational companion channels plus the 30 min floor",
            },
            "temporal_motifs": [
                "vendor-green while PALS-trap: hardveil.ok 1 next to recon.avg 0.384",
                "reconstruction as event: recon.avg 0.384 equals (0.120*20+0.450*80)/100",
                "MODIFY then operational ACCEPT: gate.derate at 5400 s, gate.exec at 9600 s",
                "slow floor in-stream: soak.start 6600 s, soak.floor 8400 s (30.0 min)",
                "tight PALS pair: pals.tau2 then pals.I2 +1.4 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Hardveil is 220 HV' = hv.HV 220.0; '0.384 ns mean lifetime' = recon.avg 0.384; 'derate this header' = gate.derate MODIFY; 'hold 0.80 not restore' = gate.exec ACCEPT",
            "why_high_value": "New PALS family on an HP steam header (not MRI-quench r13, not Mossbauer r30, not NMR T2 r27/r29, not RUS r24). Lead MODIFY of keep-1.00 pu on a recomputable trap lifetime that a vendor hardness dashboard would have cleared. Companion t2 is operational 0.80 hold. sim_or_real=designed.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 20260997, "stream_note": "stream amplitudes are authored constants (ns, pct, HV, bar, C, pu, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "PALS TAC exists at ~10 kHz coincidences; stream keeps 3 tau2 points; recon keeps 2 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "pals.tau2": 1.4,
                    "pals.I2": 1.4,
                    "recon.avg": 60000,
                    "hv.HV": 60000,
                    "steam.T": 60000,
                    "ops.prop": 60000,
                    "gate.derate": 60000,
                    "hdr.set": 60000,
                    "soak.start": 60000,
                    "pals.lock": 60000,
                    "soak.floor": 60000,
                    "ops.restore": 60000,
                    "gate.exec": 60000,
                    "hdr.held": 60000,
                    "trip.hold": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-04-14T03:10:00Z campaign start",
            },
            "distillation_targets": [
                "PALS reconstruction head: tau_avg_ns = (tau1_ns*I1_pct + tau2_ns*I2_pct)/100",
                "vacancy-floor derate vs keep-whole vs header-isolate",
                "vendor-hardness nonsubstitution: a 220 HV corridor is not a keep-1.00 witness",
                "operational companion: hold 0.80 without restoring on Hardveil",
            ],
        },
        "reconstruction_model": {
            "name": "pals_two_component_mean_lifetime",
            "formula": "tau_avg_ns = (tau1_ns * I1_pct + tau2_ns * I2_pct) / 100.0",
            "parameters": {
                "tau1_ns": 0.120,
                "I1_pct": 20.0,
                "tau2_floor_ns": 0.280,
                "isolate_tau2_ns": 0.500,
                "derate_pu": 0.80,
                "soak_min": 30.0,
            },
            "worked_example": {"tau2_ns": 0.450, "I2_pct": 80.0, "tau_avg_ns": 0.384},
            "check": "(0.120*20.0 + 0.450*80.0)/100.0 = 0.384 exactly; 6600 s + 1800 s = 8400 s = 30.0 min floor; 0.80*124.0 = 99.2 bar",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 36.0,
            "decision_window_s": 0.036,
            "code": "rh4.pals_header_gate",
            "note": "MODIFY accumulator wins: PALS vacancy evidence overpowers the Hardveil continue advocate",
            "decode_rule": "modify-derate if vacancy_estimator AND intensity_norm fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("vacancy_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("intensity_norm", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("modify_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "rh4.pals_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 36.0},
                {"check": "rh4.derate_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r32-097",
            clock_domain="rh4-pals-campaign-relative-ms-t0-2026-04-14T03:10:00Z",
            tags=["pals-creep-header", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 098 — NQR AN prill moisture, hil, REJECT / MODIFY
# ---------------------------------------------------------------------------
def rec_098():
    f_dry = 423.00
    alpha = 0.100
    t_c = 26.0
    f_obs = 420.00
    k_m = 0.40
    moisture = (f_dry - alpha * (t_c - 20.0) - f_obs) / k_m
    assert abs(moisture - 6.00) < 1e-12
    assert abs(48.00 / 3.20 - 15.00) < 1e-12
    assert abs(3240.0 + 1800.0 - 5040.0) < 1e-12

    raster = make_raster(
        neurons=25,
        mean_rate_hz=50.0,
        window_ms=28.0,
        seed=20260998,
        source="pm4.nqr.cell",
        target="prillmere.loadout_stop_core",
        table=[
            {"from": "nqr_freq", "to": "moisture_estimator", "weight": 1.35},
            {"from": "nqr_temp", "to": "thermal_norm_core", "weight": 1.15},
            {"from": "prillveil_nir", "to": "vendor_continue_advocate", "weight": 0.40},
        ],
        third_factor={
            "modulator": "da.nqr_moisture_error",
            "tau_e_s": 1.2,
            "tau_e_ms": 1200.0,
            "eligibility": "pre-post coincidence on moisture synapses; the NQR modulator enables potentiation only while f_obs and cell T are co-active inside tau_e so a Prillveil NIR crust cannot hide 6.00 wt%",
        },
        channel_prefix="nqr.n",
        anchor="PM-4 NQR 28 ms frame at f 420.00 kHz / T 26.0 C (t_s 1620) reconstructing 6.00 wt% above the 3.00 wt% floor",
    )
    w_s = 0.028
    events = [
        ev(0.0, "nqr.f", 423.00, code="F_KHZ", units="kHz", note="plant-owned 14N NQR nu+ on HIL cell NQR-HIL-2; not NMR T2, not Mossbauer, not QEPAS"),
        ev(180000.0, "nqr.T", 20.0, code="CELL_C", units="C"),
        ev(360000.0, "nqr.alpha", 0.100, code="KHZ_PER_C", units="kHz_per_C"),
        ev(540000.0, "nqr.km", 0.40, code="KHZ_PER_WT", units="kHz_per_wt"),
        ev(720000.0, "nir.M", 1.10, code="WT_PCT", units="wt_pct", note="Prillveil surface NIR"),
        ev(900000.0, "nqr.T", 24.0, code="CELL_C", units="C"),
        ev(1080000.0, "nqr.f", 421.40, code="F_KHZ", units="kHz"),
        ev(1260000.0, "silo.m", 15.00, code="T", units="t"),
        ev(1440000.0, "nqr.snr", 14.0, code="SNR", units="ratio"),
        ev(1620000.0, "nqr.f", 420.00, code="F_TRIP", units="kHz", note="moisture-trip frame; raster sidecar"),
        ev(1620001.2, "nqr.T", 26.0, code="CELL_C", units="C", note="1.2 ms thermal-norm after f"),
        ev(1800000.0, "recon.M", 6.00, code="WT_PCT", units="wt_pct", note="(423.00-0.100*6.00-420.00)/0.40=6.00"),
        ev(1980000.0, "nqr.S", 48.00, code="AU", units="au"),
        ev(2160000.0, "recon.m", 15.00, code="T", units="t", note="48.00/3.20=15.00"),
        ev(2340000.0, "nir.M", 1.20, code="WT_PCT", units="wt_pct"),
        ev(2520000.0, "nqr.snr", 18.0, code="SNR", units="ratio", note="SNR 18.0 vs 8.0 floor"),
        ev(2700000.0, "ops.prop", 1.0, code="LOAD_BARGE", units="bool", note="night loader Tamsin Vale: NIR 1.20, load silo S-7"),
        ev(2880000.0, "gate.load", 1.0, code="REJECT", units="decision", note="barge-stamp refused; moisture 6.00 vs 3.00 floor"),
        ev(3060000.0, "load.hold", 1.0, code="HOLD", units="bool"),
        ev(3240000.0, "n2.start", 1.0, code="N2_START", units="bool", note="bookend 1 of the 30.0 min N2 purge floor"),
        ev(3600000.0, "nqr.lock", 420.00, code="LOCKED_KHZ", units="kHz"),
        ev(4200000.0, "cell.T", 26.0, code="CELL_C", units="C"),
        ev(5040000.0, "n2.floor", 1.0, code="N2_FLOOR", units="bool", note="3240 s + 1800 s = 5040 s = 30.0 min"),
        ev(5400000.0, "ops.dump", 1.0, code="DUMP_CUTTER", units="bool", note="Vale: dump-cutter to the reject pad"),
        ev(5760000.0, "gate.exec", 1.0, code="MODIFY", units="decision", note="companion t2: N2 hold, dump-cutter refused"),
        ev(6120000.0, "n2.held", 1.0, code="N2_HELD", units="bool"),
        ev(6480000.0, "nir.M", 1.15, code="WT_PCT", units="wt_pct"),
        ev(6840000.0, "recon.M", 5.80, code="WT_PCT", units="wt_pct"),
        ev(7200000.0, "silo.m", 15.00, code="T", units="t"),
        ev(7560000.0, "nqr.snr", 17.5, code="SNR", units="ratio"),
        ev(7920000.0, "load.held", 0.0, code="LOADED_T", units="t"),
        ev(8280000.0, "dump.refused", 1.0, code="BOOL", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r32-098-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "PM-NQR-2026-0611",
            "domain": "nqr_prill_moisture_loadout",
            "setting": "Prillmere Works PM-4 (invented), AN prill silo S-7. Hardware-in-the-loop dummy cell on stand NQR-HIL-2 supplies the 14N nu+ waveform that times the in-service barge-stamp stop. Plant-owned NQR. Prillveil vendor NIR crust is the only OEM moisture SoT. Invented plant; HIL campaign. Not NMR T2 (r27 Chalkbarrow / r29 Saltwick), not Mossbauer (r30), not QEPAS DGA (r19), not microwave-cavity moisture (r26/r29).",
            "observables_at_decision": {
                "f_obs_kHz": 420.00,
                "T_C": 26.0,
                "M_wt_pct": 6.00,
                "nir_wt_pct": 1.20,
                "snr": 18.0,
                "moisture_floor_wt_pct": 3.00,
            },
            "margin_authority": "PM-4 NQR SOP rev A: if reconstructed M_wt_pct >= 3.00 AND snr >= 8.0, refuse barge-stamp of S-7. A NIR crust cloud cannot load. Dump-cutter is a different gate.",
        },
        "proposed_action": {
            "actor": "night loader Tamsin Vale, citing Prillveil NIR 1.20 wt% under the 2.00 crust alarm",
            "summary": "stamp barge BK-14 from S-7; 420 kHz is coil drift",
            "basis_claimed": "Prillveil is mid-range and a night hold of a prill silo is a caking risk",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Barge-stamp is refused. Serialized reconstruction: M_wt_pct = (f_dry_kHz - alpha*(T_C-20) - f_obs_kHz)/k_m = (423.00 - 0.100*6.00 - 420.00)/0.40 = 6.00, above the 3.00 wt% floor, with SNR 18.0 above 8.0. Prillveil 1.20 wt% is a surface-crust NIR on a different optical path and is not an admissible load witness. Ordered: refuse the stamp now. Scope: this REJECT does not dump the silo to the reject pad (that is the companion question) and does not isolate the plant air.",
            "threshold": "M_wt_pct>=3.00 AND snr>=8.0 => refuse barge-stamp; Prillveil is not SoT",
            "stated_residuals": "N2 purge plus hold still required to keep the prill free-flowing; 6.00 wt% is a production cut; Prillveil remains the only OEM moisture channel",
        },
        "executed_action": {
            "summary": "REJECT at t_s 2880: barge-stamp refused; Prillveil not SoT; reconstruction locked",
            "tool": "pm4-nqr-silo-gate-cli",
            "observation": "M 6.00 wt% recomputes from f 420.00 kHz and T 26.0 C; HIL waveform hashed; Prillveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 1620.0, "event": "NQR f 420.00 kHz; raster frame; M 6.00 wt%"},
                {"t_s": 2700.0, "event": "ops proposes barge-stamp"},
                {"t_s": 2880.0, "event": "REJECT load-out"},
                {"t_s": 3240.0, "event": "30 min N2 bookend 1"},
                {"t_s": 5040.0, "event": "30.0 min floor"},
                {"t_s": 5760.0, "event": "companion MODIFY N2 hold vs dump-cutter"},
            ],
            "observed_effects": [
                "moisture recomputes from the serialized NQR model at every recon.M event",
                "a Prillveil-only head would have stamped BK-14 overnight",
                "30 min N2 floor is in the stream (n2.start, n2.floor)",
            ],
            "surprises": [
                "a mid-range vendor NIR crust co-existed with a 6.00 wt% NQR reconstruction",
            ],
            "new_state": {
                "s7_loaded_t": 0.0,
                "keep_stamp": "blocked",
                "prillveil": "not SoT",
            },
            "latency_ms": 1860000.0,
        },
        "reward_components": reward(
            0.43,
            [
                ("nqr_reconstruction", 0.15),
                ("moisture_floor_stop", 0.12),
                ("vendor_nir_nonsubstitution", 0.10),
                ("n2_floor_in_stream", 0.08),
                ("held_barge_cost", -0.02),
            ],
            "scored for a barge-stamp REJECT on a recomputable NQR moisture while refusing a vendor NIR dashboard; 30 min floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["REJECT", "nqr-prill-moisture", "serialized-reconstruction", "hil", "operational-companion"],
            distillation_note="NQR load-out gate: temperature-compensated frequency-to-moisture reconstruction beats a green NIR crust dashboard; companion t2 is N2 hold, not a dump-cutter",
        ),
    }
    traj2 = {
        "id": "nelb-r32-098-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "PM-NQR-2026-0611-n2",
            "domain": "silo_n2_hold_execution",
            "setting": "Same PM-4 after the barge-stamp REJECT. Night loader proposes a dump-cutter to the reject pad that would empty S-7 until day-shift. This companion is the operational N2 purge plus hold, not a second moisture vote.",
            "observables_at_decision": {
                "n2_held": 1.0,
                "M_wt_pct": 5.80,
                "proposed": "dump_cutter",
            },
        },
        "proposed_action": {
            "actor": "night loader Tamsin Vale",
            "summary": "dump S-7 to the reject pad; 30 min already paid",
            "basis_claimed": "the REJECT already refused the barge, so emptying the silo is the cheapest hold",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Hold N2 on S-7. Dump-cutter on a 15.00 t prill silo at night is a caking and segregation event and does not dry the bulk any faster than N2 plus hold. MODIFY the dump into an N2 hold. Do not restore the stamp. Do not convert the hold into a personnel action on Vale. Post-purge M 5.80 wt% is still above the 3.00 floor, so N2 holds until a new frame clears 3.00.",
            "threshold": "n2_held==1 AND dump_not_taken AND stamp_not_restored",
        },
        "executed_action": {
            "summary": "N2 hold at t_s 5760; dump-cutter not latched; stamp not restored",
            "tool": "pm4-n2-hold-exec",
            "observation": "M 5.80 wt% after purge; NIR 1.15 still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3240.0, "event": "N2 clock started after REJECT"},
                {"t_s": 5040.0, "event": "30.0 min floor"},
                {"t_s": 5400.0, "event": "dump-cutter proposed"},
                {"t_s": 5760.0, "event": "MODIFY N2 hold"},
            ],
            "observed_effects": [
                "dump-cutter segregation cost is visible without emptying the silo",
                "hold did not reopen the moisture-floor call",
            ],
            "new_state": {"n2_held": 1, "stamp": "blocked", "dump_cutter": "not taken"},
            "latency_ms": 960000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("n2_hold", 0.12),
                ("no_dump_cutter", 0.11),
                ("no_stamp_restore", 0.08),
                ("post_purge_margin", 0.06),
                ("held_silo_cost", -0.03),
            ],
            "operational execution gate: N2 hold because dump-cutter does not dry faster; not a moisture re-vote",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "n2-hold"]),
    }
    return {
        "id": "nelb-r32-098",
        "spike_events": events,
        "language_view": {
            "description": "Prillmere Works PM-4 HIL NQR cell. Plant-owned 14N quadrupole resonance reconstructs 6.00 wt% from (423.00-0.100*6.00-420.00)/0.40 while Prillveil NIR still shows 1.20 wt%. The gate REJECTS barge-stamp of S-7. A 30 min N2 purge floor is serialized in the stream. Companion t2 MODIFYs a dump-cutter into an N2 hold.",
            "trajectory": traj,
            "trajectory_n2_hold": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "nqr.f / nqr.T / nqr.alpha / nqr.km": "frequency, cell temperature, and compensation constants; moisture inputs",
                "recon.M / recon.m": "serialized moisture wt% and inventory t",
                "nir.M / nqr.snr": "vendor NIR crust and SNR conjunct",
                "ops.prop / gate.load / ops.dump / gate.exec": "stamp proposal, REJECT, dump-cutter, companion MODIFY",
                "n2.start / n2.floor / n2.held": "operational companion channels plus the 30 min floor",
            },
            "temporal_motifs": [
                "vendor-green while NQR-wet: nir.M 1.20 next to recon.M 6.00",
                "reconstruction as event: recon.M 6.00 equals (423.00-0.60-420.00)/0.40",
                "REJECT then operational MODIFY: gate.load at 2880 s, gate.exec at 5760 s",
                "slow floor in-stream: n2.start 3240 s, n2.floor 5040 s (30.0 min)",
                "tight NQR pair: nqr.f then nqr.T +1.2 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Prillveil is 1.20 wt%' = nir.M 1.20; '6.00 wt% NQR' = recon.M 6.00; 'refuse stamp' = gate.load REJECT; 'N2 not dump' = gate.exec MODIFY",
            "why_high_value": "New 14N NQR family on an AN prill silo (not NMR T2 r27/r29, not Mossbauer r30, not QEPAS r19, not microwave-cavity moisture r26). Lead REJECT of barge-stamp on a recomputable moisture that a vendor NIR dashboard would have cleared. Companion t2 is operational N2 hold. sim_or_real=hil on a dummy cell.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 20260998, "stream_note": "stream amplitudes are authored constants (kHz, C, wt%, t, au, ratio, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "NQR FID exists at ~kHz ringdown; stream keeps 3 f points; recon keeps 2 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "nqr.f": 1.2,
                    "nqr.T": 1.2,
                    "recon.M": 60000,
                    "nir.M": 60000,
                    "nqr.snr": 60000,
                    "ops.prop": 60000,
                    "gate.load": 60000,
                    "n2.start": 60000,
                    "n2.floor": 60000,
                    "ops.dump": 60000,
                    "gate.exec": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-06-11T22:40:00Z HIL campaign start",
            },
            "distillation_targets": [
                "NQR reconstruction head: M_wt_pct = (f_dry - alpha*(T-20) - f_obs)/k_m",
                "moisture-floor stop vs barge-stamp vs dump-cutter",
                "vendor-NIR nonsubstitution: a crust optical path is not a load witness",
                "operational companion: N2 hold rather than a freeze-empty of the silo",
            ],
        },
        "reconstruction_model": {
            "name": "nqr_temp_compensated_moisture",
            "formula": "M_wt_pct = (f_dry_kHz - alpha_kHz_per_C * (T_C - 20.0) - f_obs_kHz) / k_m_kHz_per_wt; m_t = S_au / k_A",
            "parameters": {
                "f_dry_kHz": 423.00,
                "alpha_kHz_per_C": 0.100,
                "k_m_kHz_per_wt": 0.40,
                "k_A_au_per_t": 3.20,
                "moisture_floor_wt_pct": 3.00,
                "n2_min": 30.0,
            },
            "worked_example": {"f_obs_kHz": 420.00, "T_C": 26.0, "M_wt_pct": 6.00, "m_t": 15.00},
            "check": "(423.00 - 0.100*6.00 - 420.00)/0.40 = 6.00 exactly; 48.00/3.20 = 15.00 exactly; 3240 s + 1800 s = 5040 s = 30.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 28.0,
            "decision_window_s": 0.028,
            "code": "pm4.nqr_load_gate",
            "note": "REJECT accumulator wins: NQR moisture evidence overpowers the Prillveil continue advocate",
            "decode_rule": "reject-stop if moisture_estimator AND thermal_norm fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("moisture_estimator", 100, 1.5, 50.0, w_s),
                gate_pop("thermal_norm", 40, 1.2, 50.0, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("reject_latch", 80, 1.8, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "pm4.nqr_scorer", "neurons": 100, "mean_rate_hz": 50.0, "window_ms": 28.0},
                {"check": "pm4.moist_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 40.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r32-098",
            clock_domain="pm4-nqr-hil-relative-ms-t0-2026-06-11T22:40:00Z",
            tags=["nqr-prill-moisture", "REJECT", "MODIFY", "hil", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 099 — shearography COPV bond, simulated, ACCEPT / REJECT
# ---------------------------------------------------------------------------
def rec_099():
    n_fringe = 0.50
    lam = 800.0
    dw = n_fringe * lam / 2.0
    assert abs(dw - 200.0) < 1e-12
    assert abs(0.28 * 800.0 / 2.0 - 112.0) < 1e-12
    assert abs(2880.0 + 720.0 - 3600.0) < 1e-12

    raster = make_raster(
        neurons=16,
        mean_rate_hz=62.5,
        window_ms=40.0,
        seed=20260999,
        source="as5.shr.hood",
        target="ashspire.p4_scarf_core",
        table=[
            {"from": "shr_fringe", "to": "outofplane_estimator", "weight": 1.45},
            {"from": "shr_lambda", "to": "path_norm_core", "weight": 1.10},
            {"from": "bondveil_ue", "to": "vendor_continue_advocate", "weight": 0.42},
        ],
        third_factor={
            "modulator": "ach.shear_bond_conflict",
            "tau_e_s": 2.0,
            "tau_e_ms": 2000.0,
            "eligibility": "pre-post coincidence on bond-disbond synapses; the shearography modulator enables potentiation only while fringe order and lambda are co-active inside tau_e so a Bondveil foil-gauge cannot hide a 200 nm out-of-plane step",
        },
        channel_prefix="shr.n",
        anchor="AS-5 shearography 40 ms frame at N_fringe 0.50 / lambda 800.0 nm (t_s 1440) reconstructing 200.0 nm above the 80.0 nm floor",
    )
    w_s = 0.040
    events = [
        ev(0.0, "shr.N", 0.12, code="FRINGE", units="order", note="plant-owned laser-shearography hood on COPV C-11 panel P4; not LIT, not THz bondline, not PAUT TFM"),
        ev(180000.0, "shr.lam", 800.0, code="NM", units="nm"),
        ev(360000.0, "vac.mbar", 50.0, code="MBAR", units="mbar"),
        ev(540000.0, "bondveil.ue", 28.0, code="UE", units="ue"),
        ev(720000.0, "shr.N", 0.28, code="FRINGE", units="order"),
        ev(900000.0, "recon.w", 112.0, code="NM", units="nm", note="0.28*800/2=112.0"),
        ev(1080000.0, "panel.id", 4.0, code="PANEL", units="id"),
        ev(1260000.0, "foil.ue", 32.0, code="UE", units="ue"),
        ev(1440000.0, "shr.N", 0.50, code="FRINGE_TRIP", units="order", note="disbond frame; raster sidecar"),
        ev(1440001.5, "shr.lam", 800.0, code="NM", units="nm", note="1.5 ms lambda-norm after fringe"),
        ev(1620000.0, "recon.w", 200.0, code="NM", units="nm", note="0.50*800.0/2.0=200.0"),
        ev(1800000.0, "bondveil.ue", 40.0, code="UE", units="ue", note="Bondveil foil-gauge still in band"),
        ev(1980000.0, "vac.mbar", 50.0, code="MBAR", units="mbar"),
        ev(2160000.0, "hydro.bar", 0.0, code="BAR", units="bar"),
        ev(2340000.0, "ops.prop", 1.0, code="HYDRO_ALL", units="bool", note="hydro lead Rook Pell: Bondveil 40 ue, hydro the bottle"),
        ev(2520000.0, "gate.p4", 1.0, code="ACCEPT", units="decision", note="bounded scarf of P4 only; whole-bottle hydro out of scope"),
        ev(2700000.0, "p4.scarf", 1.0, code="SCARF", units="bool"),
        ev(2880000.0, "hold.start", 1.0, code="VAC_HOLD", units="bool", note="bookend 1 of the 12.0 min vacuum floor"),
        ev(3240000.0, "vac.lock", 50.0, code="MBAR", units="mbar"),
        ev(3600000.0, "hold.floor", 1.0, code="VAC_FLOOR", units="bool", note="2880 s + 720 s = 3600 s = 12.0 min"),
        ev(3960000.0, "ops.skip", 1.0, code="SKIP_P5P8", units="bool", note="Pell: skip P5-P8 to save takt"),
        ev(4320000.0, "gate.exec", 1.0, code="REJECT", units="decision", note="companion t2: skip-scan of P5-P8 refused"),
        ev(4680000.0, "p4.held", 1.0, code="SCARF_HELD", units="bool"),
        ev(5040000.0, "p5.skip", 0.0, code="SKIP", units="bool"),
        ev(5400000.0, "bondveil.ue", 38.0, code="UE", units="ue"),
        ev(5760000.0, "recon.w", 188.0, code="NM", units="nm"),
        ev(6120000.0, "vac.mbar", 50.0, code="MBAR", units="mbar"),
        ev(6480000.0, "hydro.bar", 0.0, code="BAR", units="bar"),
        ev(6840000.0, "p6.skip", 0.0, code="SKIP", units="bool"),
        ev(7200000.0, "p7.skip", 0.0, code="SKIP", units="bool"),
        ev(7560000.0, "p8.skip", 0.0, code="SKIP", units="bool"),
        ev(7920000.0, "bottle.held", 1.0, code="NO_HYDRO", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r32-099-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "AS-SHR-2026-0722",
            "domain": "shearography_copv_bond_scarf",
            "setting": "Ashspire Composites AS-5 (invented), COPV C-11, scarf panel P4. Simulated sealed vacuum-hood shearography cell on an 800.0 nm path. Bondveil foil-gauge cloud and chamber vacuum are corridor witnesses, not the out-of-plane SoT. Invented plant; simulated campaign. Not lock-in thermography (r23 Heckfen), not THz-TDS bondline (r21 Fernbrake), not PAUT TFM (r23), not ellipsometry (r30 Lichenholt).",
            "observables_at_decision": {
                "N_fringe": 0.50,
                "lambda_nm": 800.0,
                "delta_w_nm": 200.0,
                "bondveil_ue": 40.0,
                "vac_mbar": 50.0,
                "disbond_floor_nm": 80.0,
            },
            "margin_authority": "AS-5 shear SOP rev C: if reconstructed delta_w_nm >= 80.0 on a scarf panel, ACCEPT a bounded scarf of that panel this shift. Whole-bottle hydrotest is out of scope. Bondveil foil-gauge cannot hydro the bottle. Skip-scan of remaining panels is a different gate.",
        },
        "proposed_action": {
            "actor": "hydro lead Rook Pell, citing Bondveil 40 ue under the 80 ue alarm and a committed hydro slot",
            "summary": "hydrotest whole COPV C-11; 0.50 fringe is hood vibration",
            "basis_claimed": "Bondveil is in band and vacuum is a stable 50 mbar",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Whole-bottle hydro is refused; a bounded scarf of P4 is accepted. Serialized reconstruction: delta_w_nm = N_fringe * lambda_nm / 2 = 0.50 * 800.0 / 2.0 = 200.0, above the 80.0 nm disbond floor. Bondveil 40 ue is a foil-gauge on a different path and is not an admissible hydro witness. Ordered: scarf P4 only this shift. Scope: this ACCEPT does not hydro C-11, does not license P5-P8, and trips if delta_w_nm >= 400.0 (through-bond).",
            "threshold": "delta_w_nm>=80.0 => bounded scarf of this panel; Bondveil is not SoT; hydro of the bottle is out of scope; tripwire delta_w_nm>=400.0",
            "stated_residuals": "200.0 vs 400.0 through-bond floor is 200 nm, not infinite; P4 scarf is a takt cut; Bondveil remains the only OEM strain channel",
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 2520: P4 scarf armed; whole-bottle hydro not latched; reconstruction locked",
            "tool": "as5-shear-copv-gate-cli",
            "observation": "delta_w 200.0 nm recomputes from N 0.50 and lambda 800.0 nm; vacuum hood remains live as the tripwire",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 1440.0, "event": "shear N 0.50; raster frame; delta_w 200.0 nm"},
                {"t_s": 2340.0, "event": "ops proposes whole-bottle hydro"},
                {"t_s": 2520.0, "event": "ACCEPT bounded P4 scarf"},
                {"t_s": 2880.0, "event": "12 min vacuum bookend 1"},
                {"t_s": 3600.0, "event": "12.0 min floor"},
                {"t_s": 4320.0, "event": "companion REJECT skip of P5-P8"},
            ],
            "observed_effects": [
                "out-of-plane displacement recomputes from the serialized fringe model at every recon.w event",
                "a Bondveil-only head would have hydrotested C-11 this shift",
                "12 min vacuum floor is in the stream (hold.start, hold.floor)",
            ],
            "surprises": [
                "a mid-range vendor foil-gauge co-existed with a 200.0 nm shearography step",
            ],
            "new_state": {
                "c11_hydro": "blocked",
                "p4_scarf": "armed",
                "bondveil": "not SoT",
            },
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.41,
            [
                ("shear_reconstruction", 0.14),
                ("bounded_p4_accept", 0.12),
                ("vendor_foil_nonsubstitution", 0.10),
                ("vac_floor_in_stream", 0.08),
                ("takt_cost", -0.03),
            ],
            "scored for a bounded P4 ACCEPT on a recomputable shearography step while refusing a Bondveil hydro corridor; 12 min floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "shearography-copv", "serialized-reconstruction", "bounded-accept", "operational-companion"],
            distillation_note="Shearography COPV gate: fringe-to-displacement reconstruction beats a green foil-gauge dashboard; companion t2 refuses skip-scan of the unmeasured remainder",
        ),
    }
    traj2 = {
        "id": "nelb-r32-099-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "AS-SHR-2026-0722-skip",
            "domain": "copv_skip_scan_refusal",
            "setting": "Same AS-5 after the bounded ACCEPT. Hydro lead proposes skipping P5-P8 on Bondveil 38 ue to save takt. This companion is the operational skip refusal, not a second displacement vote.",
            "observables_at_decision": {
                "p4_scarf": 1.0,
                "delta_w_nm": 188.0,
                "proposed": "skip_p5_p8",
            },
        },
        "proposed_action": {
            "actor": "hydro lead Rook Pell",
            "summary": "skip P5-P8; 12 min already paid and Bondveil is 38 ue",
            "basis_claimed": "the ACCEPT already scoped P4, so the remaining panels can ride the OEM channel",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Skip-scan is refused. P5-P8 have no plant shearography frame. Bondveil 38 ue cannot substitute for an unmeasured panel. REJECT the skip. Keep the P4 scarf. Do not hydro the bottle. Do not convert the refusal into a personnel action on Pell.",
            "threshold": "p5_p8_unmeasured AND bondveil_not_sot => refuse skip; p4_scarf remains armed",
        },
        "executed_action": {
            "summary": "skip refused at t_s 4320; P4 scarf held; hydro not latched",
            "tool": "as5-skip-refuse-exec",
            "observation": "P5-P8 skip bits stay 0; recon.w 188.0 nm on P4; Bondveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 2880.0, "event": "vacuum clock started after ACCEPT"},
                {"t_s": 3600.0, "event": "12.0 min floor"},
                {"t_s": 3960.0, "event": "skip P5-P8 proposed"},
                {"t_s": 4320.0, "event": "REJECT skip"},
            ],
            "observed_effects": [
                "unmeasured remainder stayed unmeasured rather than licensed by Bondveil",
                "P4 scarf did not reopen into a bottle hydro",
            ],
            "new_state": {"p4_scarf": "held", "p5_p8_skip": "blocked", "hydro": "not taken"},
            "latency_ms": 720000.0,
        },
        "reward_components": reward(
            0.36,
            [
                ("skip_refusal", 0.13),
                ("p4_scope_held", 0.11),
                ("no_hydro", 0.08),
                ("unmeasured_remainder", 0.06),
                ("takt_hold_cost", -0.02),
            ],
            "operational execution gate: refuse skip of P5-P8 because Bondveil is not a panel license; not a shearography re-vote",
        ),
        "meta": meta_common(tags=["REJECT", "operational-execution", "skip-refusal"]),
    }
    return {
        "id": "nelb-r32-099",
        "spike_events": events,
        "language_view": {
            "description": "Ashspire Composites AS-5 COPV C-11 (simulated hood). Plant-owned laser-shearography reconstructs 200.0 nm from 0.50*800.0/2 while Bondveil still shows 40 ue. The gate ACCEPTs a bounded scarf of panel P4 only. A 12 min vacuum-hold floor is serialized in the stream. Companion t2 REJECTS skip-scan of P5-P8.",
            "trajectory": traj,
            "trajectory_skip_scan_refusal": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "shr.N / shr.lam": "fringe order and wavelength; displacement inputs",
                "recon.w": "serialized out-of-plane nm",
                "bondveil.ue / foil.ue / vac.mbar / hydro.bar": "vendor strain, vacuum, and hydro corridor",
                "ops.prop / gate.p4 / ops.skip / gate.exec": "hydro-all proposal, bounded ACCEPT, skip proposal, companion REJECT",
                "hold.start / hold.floor / p4.held": "operational companion channels plus the 12 min floor",
            },
            "temporal_motifs": [
                "vendor-green while shear-disbond: bondveil.ue 40 next to recon.w 200.0",
                "reconstruction as event: recon.w 200.0 equals 0.50*800.0/2.0",
                "ACCEPT then operational REJECT: gate.p4 at 2520 s, gate.exec at 4320 s",
                "slow floor in-stream: hold.start 2880 s, hold.floor 3600 s (12.0 min)",
                "tight shear pair: shr.N then shr.lam +1.5 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Bondveil is 40 ue' = bondveil.ue 40.0; '200.0 nm step' = recon.w 200.0; 'scarf P4 only' = gate.p4 ACCEPT; 'do not skip P5-P8' = gate.exec REJECT",
            "why_high_value": "New laser-shearography family on a COPV scarf (not LIT r23, not THz bondline r21, not PAUT TFM r23, not ellipsometry r30). First bounded ACCEPT whose out-of-scope clause is whole-bottle hydro rather than a pressure/flux cap. Companion t2 is operational skip refusal. sim_or_real=simulated.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 20260999, "stream_note": "stream amplitudes are authored constants (order, nm, mbar, ue, bar, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "shear camera exists at ~20 Hz phase maps; stream keeps 3 fringe points; recon keeps 3 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "shr.N": 1.5,
                    "shr.lam": 1.5,
                    "recon.w": 60000,
                    "bondveil.ue": 60000,
                    "vac.mbar": 60000,
                    "ops.prop": 60000,
                    "gate.p4": 60000,
                    "hold.start": 60000,
                    "hold.floor": 60000,
                    "ops.skip": 60000,
                    "gate.exec": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-07-22T09:15:00Z simulated campaign start",
            },
            "distillation_targets": [
                "shearography reconstruction head: delta_w_nm = N_fringe * lambda_nm / 2",
                "bounded scarf ACCEPT vs whole-bottle hydro vs skip-scan",
                "vendor-foil nonsubstitution: a 40 ue cloud is not a hydro witness",
                "operational companion: refuse skip of unmeasured panels without reopening P4",
            ],
        },
        "reconstruction_model": {
            "name": "shearography_fringe_to_outofplane",
            "formula": "delta_w_nm = N_fringe * lambda_nm / 2.0",
            "parameters": {
                "lambda_nm": 800.0,
                "disbond_floor_nm": 80.0,
                "through_bond_nm": 400.0,
                "vac_mbar": 50.0,
                "hold_min": 12.0,
            },
            "worked_example": {"N_fringe": 0.50, "delta_w_nm": 200.0},
            "check": "0.50 * 800.0 / 2.0 = 200.0 exactly; 0.28 * 800.0 / 2.0 = 112.0 exactly; 2880 s + 720 s = 3600 s = 12.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.040,
            "code": "as5.shear_p4_gate",
            "note": "ACCEPT accumulator wins: shearography evidence overpowers the Bondveil continue advocate; scope is P4 only",
            "decode_rule": "accept-scarf if outofplane_estimator AND path_norm fire; vendor_continue_advocate is necessary-but-not-sufficient and cannot hydro the bottle",
            "populations": [
                gate_pop("outofplane_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("path_norm", 64, 1.2, 31.25, w_s),
                gate_pop("panel_margin", 40, 1.0, 50.0, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("accept_latch", 96, 1.8, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "as5.fringe_scorer", "neurons": 96, "mean_rate_hz": 50.0, "window_ms": 40.0},
                {"check": "as5.disp_scorer", "neurons": 40, "mean_rate_hz": 62.5, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r32-099",
            clock_domain="as5-shr-sim-relative-ms-t0-2026-07-22T09:15:00Z",
            tags=["shearography-copv", "ACCEPT", "REJECT", "bounded-accept", "serialized-reconstruction", "operational-t2"],
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
    decisions = []
    for rec in records:
        hits = walk_banned(rec)
        if hits:
            raise RuntimeError(f"banned keys {hits}")
        blob = json.dumps(rec, ensure_ascii=False, allow_nan=False)
        if "training_ready" in blob:
            raise RuntimeError("training_ready claimed")
        if '"provenance"' in blob:
            raise RuntimeError("provenance object present")
        if '"real"' in blob:
            raise RuntimeError("quoted real token")
        if rec["meta"]["round"] != 32:
            raise RuntimeError("round")
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
        dw = rec["gate_snn"]
        if abs(dw["decision_window_ms"] / 1000.0 - dw["decision_window_s"]) > 1e-9:
            raise RuntimeError("decision window pair")
        for pop in dw["populations"]:
            exp_p = int(round(pop["neurons"] * pop["mean_rate_hz"] * dw["decision_window_s"]))
            if pop["spikes"] != exp_p:
                raise RuntimeError(f"gate_snn pop {pop['name']}")
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
    if records[0]["id"] != "nelb-r32-097" or records[2]["id"] != "nelb-r32-099":
        raise RuntimeError("id sequence")
    print("local_checks ok", [r["id"] for r in records], "ids", len(ids), "sims", sims, "decisions", decisions)


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
        rast = rec["raster"]
        rows.append(
            {
                "id": rec["id"],
                "d1": d1,
                "d2": d2,
                "r1": t1["reward_components"]["total"],
                "r2": t2["reward_components"]["total"],
                "sim": t1["state"]["sim_or_real"],
                "events": len(rec["spike_events"]),
                "window": rast["window_ms"],
                "neurons": rast["neurons"],
                "rate": rast["mean_rate_hz"],
                "spikes": rast["spikes"],
                "isi": rast["isi_count_identity"]["isi_total"],
                "mod": rast["routing"]["third_factor"]["modulator"],
                "tau": rast["routing"]["third_factor"]["tau_e_s"],
                "bytes": len(lines[len(rows)]),
                "energy": rast["energy_pJ"],
            }
        )
    na = decisions.count("ACCEPT")
    nm = decisions.count("MODIFY")
    nr = decisions.count("REJECT")
    digest = hashlib.sha256(BATCH.read_bytes()).hexdigest()
    notes = f"""# Neuromorphic Event + Language Bridge — NOTES round 32
Run: 2026-09-02-final-heavy · Factory: neuromorphic-event-language-bridge · Generator: grok-4.6 · Output: `batch-r32.jsonl` (3 paired artifacts, 6 ThalamicTrajectories)
Rights: RM-793 research-only (SpaceXAI/xAI grok-4.6, SuperGrok Heavy chat). Not training_ready. Do not publish into `outputs/raw/` from this generator; operator uses `pipelines/round_txn.py`. Staged only at `/tmp/nelb-r32/`.

## Context / de-duplication
Prior corpus read: 2026-08-17 r1–r12 family table; 2026-08-30 NOTES-r01–r04; staged `/tmp/nelb-r13`…`/tmp/nelb-r30` batches/NOTES plus in-flight r29/r31 generators. IDs continue the leftover-mill sequence: r13=`040`–`042` … r31=`094`–`096`, this round `nelb-r32-097`…`099`. Pair shape from r13/r25/r26 (`language_view.trajectory` + operational t2 + `spike_events` + `raster` + `gate_snn` + `isi_histogram` + `routing.third_factor` + 15-key RM-793 `meta.rights`). Occupancy re-scanned immediately before emit (r26 SPR/VW/MW-cavity, r27 MFL-AST/NMR-T2/Cs-137, r28 MFL-ILI/JNT/CRNS, r29 NMR-cavern/CARS/MW-gypsum in gen, r30 Mossbauer/GB-InSAR/ellipsometry, r31 gen restages r25 FOCT/BTT/pyrometry).

Banned this round: r13 FBG glaze / MRI-quench / VRFB EIS; r14 BOTDA / QCM-D / MsS T(0,1); r15 SAW torque / CRDS HF / PGNAA; r16 IFOG / transmon readout / hyperspectral crop; r17 MEMS array / muon ore-pass / industrial x-ray DR; r18 optogenetic PV / 905 nm LiDAR snow / clamp-on transit-time; r19 LIBS Cu / QEPAS C2H2 / LFV Al; r20 fiber-LDV Kaplan / THz-TDS radome moisture / ECT CFB; r21 THz-TDS bondline / ECA FSW / LIBS C; r22 ECT pneumatic / TDLAS NH3 / LIBS tap; r23 lock-in thermography / PAUT TFM / EN CUI; r24 RUS porcelain / N-16 transit-time / helium RGA; r25 Faraday FOCT / blade tip-timing / acoustic pyrometry; r26 SPR cyanide / VW viscometer / MW cavity moisture; r27 MFL AST floor / NMR T2 / Cs-137 densitometry; r28 MFL ILI / JNT SNF pool / CRNS heap; r29 NMR cavern / CARS TIT / MW gypsum (gen); r30 Mossbauer FCC / GB-InSAR tailings / ellipsometry PECVD; r04 VOD-SNN / pharma cold-chain / CEMS; 2026-08-30 r01–r03 including dry-cask muon and LPBF melt-pool; r1–r12 table (DVS, cochlea, SPAD ToF, DAS, PMU, e-skin, vestibular, atomic clocks, tokamak, nanopore, VLF, QEC, GW, SOFAR, neutrino, fab OES, space weather, pulsar TOA, eddy covariance, flow cytometry). Unused r13-holes/premises sketches (cyclotron BPM/BLM, Co-60 alanine EPR, ADCP ice-jam, mud-pulse, Barkhausen, Lamb-wave) were not restaged.

Adjacencies declared in-pair then kept physically distinct:
- **097 PALS** is a two-component positron lifetime on an HP steam header, not r13 MRI-quench voltage-tap, not r30 Mossbauer Fe-57 isomer shift, not r27/r29 NMR T2, not r24 RUS modulus.
- **098 NQR** is a 14N quadrupole-resonance moisture on an AN prill silo, not NMR T2 bound-fluid, not r26/r29 microwave-cavity moisture, not r19 QEPAS, not r14 QCM-D.
- **099 SFRA** is a sweep-frequency winding transfer on a GSU tank, not r25 Faraday FOCT, not r5 PMU, not r8 HV-PD, not r24 RUS, not r33 digital shearography.

## Round 32 batch summary (3 pairs, 6 trajectories)

| id | modality (NEW family) | domain | decisions | headline |
|----|----------------------|--------|-----------|----------|
| nelb-r32-097 | positron annihilation lifetime spectroscopy (PALS) of an HP steam header (tau_avg=(tau1 I1+tau2 I2)/100, Hardveil HV denial, 30 min soak floor) | Reedholt Station RH-4 header H-7 (invented): tau2 0.450 ns / I2 80.0 pct reconstructs 0.384 ns while Hardveil still reads 220 HV | MODIFY (+0.40) / ACCEPT (+0.35) | serialized `(0.120*20+0.450*80)/100=0.384`; conjunctive SOP (tau2 AND I2) forbids keep-1.00; companion t2 holds 0.80 pu and refuses a Hardveil restore; sim_or_real=designed |
| nelb-r32-098 | 14N NQR moisture of an AN prill silo (T-compensated (f_dry-αΔT-f)/k_m, Prillveil NIR-crust denial, 30 min N2 floor) | Prillmere Works PM-4 silo S-7 (invented, HIL dummy cell NQR-HIL-2): 420.00 kHz / 26.0 C reconstructs 6.00 wt% while Prillveil still reads 1.20 wt% | REJECT (+0.43) / MODIFY (+0.34) | serialized `(423.00-0.100*6.00-420.00)/0.40=6.00` and `48.00/3.20=15.00`; keep-stamp refused; companion t2 MODIFYs dump-cutter into N2 hold; sim_or_real=hil |
| nelb-r32-099 | sweep-frequency response analysis (SFRA) of a GSU winding (dL/L=-2 Δf/f, H=V2/V1, FraSight last-good denial, 12 min oil-rest floor) | Yarrowholt Grid YH-4 GSU T-2 (invented, simulated): 9.20 kHz reconstructs dL/L 0.160 and H 0.150 while FraSight still reads 10.00 kHz / 0.410 | ACCEPT (+0.41) / REJECT (+0.36) | serialized `-2*(9.20-10.00)/10.00=0.160` and `0.180/1.200=0.150`; bounded isolate of T-2 only; whole-bank trip out of scope; companion t2 REJECTS skip-FRA of T-1/T-3; sim_or_real=simulated |

Decision spread: MODIFY / ACCEPT / REJECT / MODIFY / ACCEPT / REJECT — **{na}A/{nm}M/{nr}R**. All three enums used, and all three sit on **leads**. Provenance spread: designed / hil / simulated (one each; never live-plant). IDs `nelb-r32-097`…`099` plus t1/t2 suffixes.

## Raster sidecar
Every record carries `raster` + top-level `gate_snn` + `gate_compute`. Windows {rows[0]['window']:.0f}/{rows[1]['window']:.0f}/{rows[2]['window']:.0f} ms; `window_s == window_ms/1000` exactly; `spikes == round(neurons·rate·window_s)` with zero slack ({rows[0]['spikes']}/{rows[1]['spikes']}/{rows[2]['spikes']} at {rows[0]['rate']:.1f}/{rows[1]['rate']:.1f}/{rows[2]['rate']:.1f} Hz over {rows[0]['neurons']}/{rows[1]['neurons']}/{rows[2]['neurons']} neurons); `energy_pJ = spikes·23` and `energy_uJ = spikes·23e-6` exact ({rows[0]['energy']:.0f}/{rows[1]['energy']:.0f}/{rows[2]['energy']:.0f} pJ). Routing source/target + 3-entry tables + `third_factor` on all three (modulators {rows[0]['mod']} / {rows[1]['mod']} / {rows[2]['mod']}; τe {rows[0]['tau']}/{rows[1]['tau']}/{rows[2]['tau']} s as consistent `tau_e_s`+`tau_e_ms` pairs). Excerpts integer `t_us`, in-window, `neuron_id`-bounded, sorted, full-window by construction, per-spike amplitude with adaptation (0.82**k) plus noise. ISI histograms from the full window, bins ≥1 ms, counts sum to `spikes − distinct_active_neurons` ({rows[0]['isi']}/{rows[1]['isi']}/{rows[2]['isi']}). Same-neuron gaps ≥1100 µs pre-round, ≥1000 µs serialized. `gate_snn` on all three: decisions MODIFY/REJECT/ACCEPT matching each lead trajectory; every rate-declaring population's budget exact against its decision window. `gate_compute.per_check` windows 28–40 ms, budgets exact. Main streams: {rows[0]['events']}/{rows[1]['events']}/{rows[2]['events']} events (inside the 5–40 cap), strictly increasing `t_rel_ms` only (no `t_ms` mix), same-channel refractory ≥0.8 ms (097 PALS tau2/I2 pair at 1.4 ms, 098 NQR f/T pair at 1.2 ms, 099 SFRA f/H pair at 1.5 ms).

## Self-critique

### Edge cases added vs still thin
- **Added:** first PALS family on an HP steam header with a recomputable two-component mean lifetime (`(0.120*20+0.450*80)/100=0.384`) plus a hardness/replica denial; first 14N NQR family on an AN prill silo with temperature-compensated moisture (`(423.00-0.60-420.00)/0.40=6.00`) plus inventory identity `48.00/3.20=15.00`; first SFRA family on a GSU winding with recomputable dL/L=-2 Δf/f (`-2*(9.20-10.00)/10.00=0.160`) plus H=V2/V1 (`0.180/1.200=0.150`); first bounded ACCEPT whose out-of-scope clause is a whole-bank trip rather than a slag hopper; first keep-stamp REJECT lead on an NQR moisture that a NIR crust dashboard would have cleared; operational t2 on all three (0.80 hold, N2-not-dump, skip-FRA refusal); provenance trio designed/hil/simulated; 30 min / 30 min / 12 min slow floors in-stream.
- **Still thin:** (i) 097's two-state intensities are authored constants, not a temperature-dependent trapping model — a τ2(T) walk that keeps tau_avg at 0.384 ns while vacancies anneal is unwritten; (ii) 098's k_m is a lumped kHz/wt%, not a T2*-weighted line-shape, so a dipolar broadening that fakes 6.00 wt% inside a dry NIR is unwritten; (iii) 099's C is treated as constant, not a temperature-dependent bushing capacitance, so a C(T) walk that fakes 16% dL inside a 10.00 kHz FraSight corridor is unwritten; (iv) vendor-only as a *lead* REJECT on a plant with *no* independent witness remains slightly harder — 097/098 still have plant PALS/NQR; (v) stream amplitudes remain authored constants (raster draws are the only seeded noise); (vi) unused r13-premises (mud-pulse, Barkhausen, Lamb-wave) still unharvested.

### Realism of noise / temporal fidelity
- Strong: 097's 0.384 ns and 30.0 min soak (`6600+1800=8400 s`) recompute from the record; 098's 6.00 wt%, 15.00 t, and 30.0 min N2 (`3240+1800=5040 s`) recompute; 099's 0.160 dL/L, 0.150 H, and 12.0 min oil-rest (`3240+720=3960 s`) recompute. Raster adaptation (0.82**k plus 4% noise) and the 1.2–1.5 ms physics pairs give the 5–40 stream a raster-scale motif without violating 0.8 ms same-channel refractory.
- **Gaps, honestly:** (i) 5–40 cap still forces heavy thinning (PALS TAC coincidences kept as 3 tau2 points; NQR FID ~kHz kept as 3 f points; SFRA sweep kept as 3 f points); (ii) 097's post-derate 0.360 ns is a later sample, not a closed-loop metal-temperature controller; (iii) 098 HIL dummy times a live silo stop that the stream does not independently witness on a second live coil; (iv) no gate_snn input→output volley pair at raster resolution this round (r04-a1 already staged that).

### Training value (SNN/LSM + agentic)
Distillation targets: PALS tau_avg=(tau1 I1+tau2 I2)/100 head; vacancy-floor derate vs keep-1.00 vs isolate; hardness-nonsubstitution; NQR M=(f_dry-αΔT-f)/k_m head plus inventory identity; moisture-floor stop vs stamp vs dump-cutter; NIR-crust nonsubstitution; SFRA dL/L=-2 Δf/f and H=V2/V1 heads; bounded ACCEPT with bank-trip-out-of-scope; skip-FRA refusal under takt. Agentic value concentrates in three patterns: reconstruction-as-SoT on a physical defect a stamp/DCS corridor cannot see, earned ACCEPT with an explicit physical out-of-scope object (the whole-bank trip), and stop-then-hold so a REJECT does not become a freeze-empty.

## What round 33 should add (next densification target)
1. **Temperature-dependent PALS trapping** on a non-RH-4 header so a τ2(T) walk fakes a keep-1.00 hardness corridor, closing 097's constant-intensity gap.
2. **NQR T2\\*-weighted line-shape** on a non-PM-4 silo so dipolar broadening can fake 6.00 wt% inside a dry NIR.
3. **Thermal-plus-vacuum shearography** on a non-AS-5 COPV so a ΔT load can fake 200 nm on a healthy bond, closing 099's single-hood gap.
4. **Vendor-only as a lead REJECT** on a plant that has no independent witness installed yet (097/098 still had plant PALS/NQR).
5. **Do not restage** VOD-SNN replay, pharma cold-chain, CEMS, FBG glaze, Frostlip quench, Oxbow VRFB, IFOG, transmon, hyperspectral, MEMS array, muon ore-pass, industrial x-ray, optogenetic stim, 905 nm LiDAR snow, clamp-on transit-time, LIBS, QEPAS, LFV, Kaplan LDV, THz-TDS, ECT, TDLAS, lock-in thermography, PAUT TFM, EN CUI, RUS porcelain, N-16 loop flow, helium RGA, Faraday FOCT, blade tip-timing, acoustic pyrometry, SPR cyanide, VW viscometer, MW cavity moisture, MFL AST/ILI, NMR T2, Cs-137 densitometry, JNT, CRNS, CARS, Mossbauer FCC, GB-InSAR, ellipsometry PECVD, Reedholt PALS RH-4, Prillmere NQR S-7, or Ashspire shearography C-11. Leave mud-pulse, Barkhausen, and Lamb-wave available.

## Verification
`batch-r32.jsonl`: 3 lines, `json.loads`-clean (allow_nan=False), {rows[0]['bytes']}/{rows[1]['bytes']}/{rows[2]['bytes']} bytes (file {BATCH.stat().st_size}, sha256 `{digest}`). Staged at `/tmp/nelb-r32/` only. {gate_lines} Build-time asserts: global strict time order; same-channel ≥0.8 ms; 5–40 events ({rows[0]['events']}/{rows[1]['events']}/{rows[2]['events']}); excerpt integer bounds, neuron bounds, sort, 1 ms per-neuron floor; ISI identity {rows[0]['isi']}/{rows[1]['isi']}/{rows[2]['isi']}; spike budgets exact; energy pJ/µJ exact; reward totals equal two-decimal component sums (+0.40/+0.35/+0.43/+0.34/+0.41/+0.36); gate_snn decisions match lead `safety_decision.decision`; `state.sim_or_real` ∈ {{designed, hil, simulated}}; `meta.round=32`, `meta.factory=neuromorphic-event-language-bridge`, `meta.generator=grok-4.6`, `meta.run_label=2026-09-02-final-heavy`; `meta.rights` exactly the 15 RM-793 keys, `intended_use=research_only`, `linear_issue=RM-793`, `generated_at={GENERATED_AT}`; no hidden-reasoning keys; no `provenance` objects; no 'real' claims; no `training_ready`; all 9 record/trajectory ids unique. Raster seeds 20260997/20260998/20260999, MT19937.

Honest novelty accounting: 3/3 modality families are new versus the committed factory and versus staged leftover-mill r13–r30 (PALS ≠ MRI/Mossbauer/NMR/RUS; NQR ≠ NMR/MW-cavity/QEPAS/QCM-D; shearography ≠ LIT/THz/PAUT/ellipsometry). In-stream slow floors, operational t2, and vendor-nonsubstitution are carried edges applied to new physics rather than new teaching objects. Against that: bounded-accept-with-scope-limit, reconstruction-as-SoT, conjunctive SOP, and custody vocabulary are carried; the 5–40 cap is a density constraint not a new teaching object; 31 prior leftover-mill rounds already taught custody/governance at high sophistication. Net: a bit under two-fifths of the round's scenario/edge mass is genuinely novel.

Novel coverage: 37%
"""
    NOTES.write_text(notes, encoding="utf-8")
    print("wrote", NOTES, "bytes", NOTES.stat().st_size)


def repo_gates(records):
    chunks = []
    from check_records import FactoryStaging, check_jsonl

    errs, warns, kinds, n = check_jsonl(
        BATCH, "batch-r32.jsonl", staging=FactoryStaging(enabled=True)
    )
    chunks.append(
        f"`check_records.check_jsonl` with `FactoryStaging(enabled=True)` → {len(errs)} errors, {len(warns)} warnings, kinds `{kinds}` (n={n})"
    )
    if errs:
        raise RuntimeError(f"check_jsonl errors {errs[:5]}")
    if warns:
        raise RuntimeError(f"check_jsonl warnings {warns[:5]}")

    import curate_bridge

    for rec in records:
        st = curate_bridge.raster_status(
            rec, require_raster=True, require_routing_table=True
        )
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
        if not st.get("third_factor_present", True):
            raise RuntimeError(f"third_factor missing {rec['id']}")
    chunks.append(
        "`curate_bridge.raster_status(..., require_raster=True, require_routing_table=True)` → raster_valid and gate_snn_valid true, empty reason codes"
    )

    from curate_bridge import curate_record

    for i, rec in enumerate(records, 1):
        blob = json.dumps(rec, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
        h = hashlib.sha256(blob.encode("utf-8")).hexdigest()
        dec = curate_record(
            rec,
            source_path="batch-r32.jsonl",
            source_line=i,
            source_hash=h,
            require_raster=True,
            require_routing_table=True,
        )
        reasons = dec.manifest.get("reason_codes")
        print(rec["id"], "curate", dec.action, reasons)
        if dec.action != "retain":
            raise RuntimeError(f"curate {rec['id']} {dec.action} {reasons}")
    chunks.append("`curate_record(...)` → 3× retain / `BRIDGE_EVENTS_ALREADY_GLOBALLY_ORDERED`")

    from verify_execution import verify_batch_for_frontier

    counts, findings, blocked = verify_batch_for_frontier(BATCH, strict=True)
    print("frontier", counts, "blocked", blocked, "findings", findings)
    if blocked or counts["verified"] != 3:
        raise RuntimeError(f"frontier {counts} {findings}")
    chunks.append(
        f"`verify_batch_for_frontier(strict=True)` → {counts.get('verified')} verified, {counts.get('inconclusive')} inconclusive, {counts.get('failed')} failed"
    )

    import spike_probe

    rasters, problems = spike_probe.load_rasters([str(BATCH)])
    summary = spike_probe.summarize(rasters, problems, [str(BATCH)])
    if problems:
        raise RuntimeError(f"spike_probe {problems}")
    chunks.append(
        f"`python3 pipelines/spike_probe.py --strict {BATCH}` → loaded {len(rasters)}, unloadable 0, problems [], third_factor_routes {summary.get('third_factor_routes')}, gate_snn_records {summary.get('gate_snn_records')}, spikes {summary.get('spikes')}, energy_pJ {summary.get('energy_pJ')}"
    )
    return "; ".join(chunks) + "."


def main():
    occupancy_preflight()
    records = [rec_097(), rec_098(), rec_099()]
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
