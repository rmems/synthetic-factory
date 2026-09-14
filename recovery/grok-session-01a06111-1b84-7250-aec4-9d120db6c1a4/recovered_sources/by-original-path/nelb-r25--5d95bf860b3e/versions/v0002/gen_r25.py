#!/usr/bin/env python3
"""Generate NELB round-25 research-only bridge pairs (do not write outputs/raw/)."""

from __future__ import annotations

import json
import math
import random
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

OUT_DIR = Path("/tmp/nelb-r25")
BATCH = OUT_DIR / "batch-r25.jsonl"
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
        "round": 19,
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
# Record 058 — LIBS EAF scrap copper, designed, ACCEPT / ACCEPT
# ---------------------------------------------------------------------------
def rec_058():
    raster = make_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=32.0,
        seed=20260921,
        source="hl2.libs.hopper",
        target="hearthloom.charge_release_core",
        table=[
            {"from": "libs_Icu324", "to": "cu_estimator", "weight": 1.35},
            {"from": "libs_Ife373", "to": "fe_norm_core", "weight": 1.15},
            {"from": "last_heat_cu", "to": "last_heat_advocate", "weight": 0.55},
        ],
        third_factor={
            "modulator": "na.cu_line_salience",
            "tau_e_s": 2.0,
            "tau_e_ms": 2000.0,
            "eligibility": "pre-post coincidence on Cu-ratio synapses; the 324.75 nm modulator enables potentiation only while I_Fe373 is co-active inside tau_e so a last-heat spectrometer corridor cannot hide a Cu-bearing hopper",
        },
        channel_prefix="libs.n",
        anchor="HL-2 hopper LIBS 32 ms frame at I_Cu 8.50 / I_Fe 2.00 (t_s 3600) where reconstructed Cu first clears the 180 ppm charge tripwire",
    )
    w_s = 0.032
    events = [
        ev(0.0, "libs.Icu", 3.20, code="I_CU324", units="au", note="pre-dawn hopper LIBS; 324.75 nm Cu I line"),
        ev(600000.0, "libs.Ife", 2.00, code="I_FE373", units="au", note="373.49 nm Fe I internal standard; not fab OES endpoint"),
        ev(900000.0, "recon.cu", 64.0, code="CU_PPM", units="ppm", note="40.0*3.20/2.00 = 64.0 exact"),
        ev(1200000.0, "heat.cu_wt", 0.12, code="LAST_HEAT_WT", units="wt_pct", note="last-heat spark-OES still 0.12 wt% Cu"),
        ev(1500000.0, "eaf.MW", 0.0, code="EAF_MW", units="MW", note="furnace idle; a power corridor is not a charge license"),
        ev(1800000.0, "libs.Icu", 5.60, code="I_CU324", units="au"),
        ev(2100000.0, "libs.Ife", 2.00, code="I_FE373", units="au"),
        ev(2400000.0, "recon.cu", 112.0, code="CU_PPM", units="ppm", note="40.0*5.60/2.00 = 112.0"),
        ev(3000000.0, "hopper.t", 18.4, code="HOPPER_T", units="t"),
        ev(3600000.0, "libs.Icu", 8.50, code="I_CU324", units="au", note="charge-authorization frame; raster sidecar"),
        ev(3600001.5, "libs.Ife", 2.00, code="I_FE373", units="au", note="1.5 ms Fe-norm after Cu; same-channel floors stay 600 s"),
        ev(3900000.0, "recon.cu", 170.0, code="CU_PPM", units="ppm", note="40.0*8.50/2.00 = 170.0 exact; tripwire 180 ppm"),
        ev(4200000.0, "heat.cu_wt", 0.12, code="LAST_HEAT_WT", units="wt_pct"),
        ev(4500000.0, "eaf.MW", 0.0, code="EAF_MW", units="MW"),
        ev(4800000.0, "bale.rad", 1.0, code="RADIATOR_ON_APRON", units="bool", note="Cu-bearing radiator bale staged; out of hopper scope"),
        ev(5400000.0, "ops.prop", 1.0, code="DUMP_HOPPER_AND_BALE", units="bool", note="charge lead Bram Kett: dump hopper and the radiator bale; 324 nm is slag sparkle"),
        ev(6000000.0, "gate.charge", 1.0, code="ACCEPT", units="decision", note="bounded ACCEPT: this hopper this heat; radiator bale refused"),
        ev(6600000.0, "hopper.release", 1.0, code="RELEASE", units="bool"),
        ev(7200000.0, "belt.v", 1.40, code="V_M_S", units="m_s", note="inside 1.20-1.60 m/s envelope"),
        ev(7800000.0, "mag.on", 1.0, code="MAGNET", units="bool"),
        ev(8400000.0, "libs.lock", 170.0, code="LOCKED_CU_PPM", units="ppm"),
        ev(9000000.0, "hopper.t", 12.1, code="HOPPER_T", units="t"),
        ev(9600000.0, "belt.v", 1.38, code="V_M_S", units="m_s"),
        ev(10200000.0, "hopper.empty", 1.0, code="EMPTY", units="bool"),
        ev(10800000.0, "bale.rad", 1.0, code="RADIATOR_HELD", units="bool", note="radiator bale still on apron; not charged"),
        ev(11400000.0, "gate.exec", 1.0, code="ACCEPT", units="decision", note="companion t2: charge sequence inside envelope"),
        ev(12000000.0, "heat.cu_wt", 0.12, code="LAST_HEAT_WT", units="wt_pct"),
        ev(12600000.0, "trip.hold", 0.0, code="TRIP_PPM", units="ppm", note="peak 170 vs 250 isolate floor; isolate not taken"),
        ev(13200000.0, "recon.cu", 170.0, code="CU_PPM", units="ppm"),
        ev(13800000.0, "bale.held", 1.0, code="BALE_OUT_OF_SCOPE", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r19-058-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "HL-EAF-2026-0409",
            "domain": "libs_eaf_scrap_copper",
            "setting": "Hearthloom Steel melt shop HL-2 (invented), 90 t EAF, plant-owned 1064 nm LIBS on the scrap-charge hopper. Last-heat spark-OES is a corridor witness, not the charge SoT. Invented plant; designed campaign. Not fab OES endpoint, not LPBF melt-pool photodiodes, not CEMS.",
            "observables_at_decision": {
                "I_Cu324_au": 8.50,
                "I_Fe373_au": 2.00,
                "cu_ppm": 170.0,
                "last_heat_cu_wt_pct": 0.12,
                "radiator_bale_on_apron": 1,
                "tripwire_cu_ppm": 180.0,
            },
            "margin_authority": "HL-2 charge SOP rev C: a hopper may dump only if reconstructed Cu_ppm <= 180 AND the authorization covers this hopper this heat. A last-heat 0.12 wt% corridor cannot substitute for the LIBS ratio. Radiator bales are out of scope.",
        },
        "proposed_action": {
            "actor": "charge lead Bram Kett, citing last-heat 0.12 wt% Cu and '324 nm is slag sparkle'",
            "summary": "dump hopper HL-2-H3 and the radiator bale on the apron into heat 4417",
            "basis_claimed": "spark-OES on the previous heat is 0.12 wt% Cu and the EAF is idle-cold",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "This hopper is accepted, not the radiator bale. Serialized reconstruction: cu_ppm = 40.0 * I_Cu324 / I_Fe373 = 40.0 * 8.50 / 2.00 = 170.0, which clears the 180 ppm tripwire by 10.0 ppm. SOP rev C still forbids the Cu-bearing radiator bale: ordered dump of hopper HL-2-H3 into heat 4417 only. Explicit scope: this accept does not cover apron bales and does not authorize a second hopper without a new LIBS frame. Isolate tripwire: cu_ppm > 250.",
            "threshold": "cu_ppm<=180 AND hopper=HL-2-H3 AND heat=4417 AND radiator_bale_not_charged",
            "stated_residuals": "10.0 ppm margin is not infinite; 18.4 t of mixed scrap still carries Cu variance; last-heat spark-OES is not a hopper witness",
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 6000: hopper HL-2-H3 authorized; radiator bale held on apron; reconstruction locked as SoT",
            "tool": "hl2-libs-charge-gate-cli",
            "observation": "cu 170.0 ppm recomputes from I_Cu 8.50 and I_Fe 2.00; magnet staged; LIBS remains live as the isolate interlock",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3600.0, "event": "LIBS I_Cu 8.50; raster frame; cu 170.0 ppm"},
                {"t_s": 5400.0, "event": "ops proposes hopper plus radiator bale"},
                {"t_s": 6000.0, "event": "ACCEPT bounded hopper dump; bale refused"},
                {"t_s": 6600.0, "event": "companion charge start"},
                {"t_s": 11400.0, "event": "companion ACCEPT; hopper empty; bale held"},
            ],
            "observed_effects": [
                "Cu ppm recomputes from the serialized ratio at every recon.cu event",
                "a last-heat-only head would have dumped the radiator bale on a 0.12 wt% corridor",
                "peak cu 170.0 stayed under the 250 ppm isolate floor",
            ],
            "surprises": [
                "idle EAF MW stayed 0.0 until the dump; a power-only head would have treated idle as a license",
            ],
            "new_state": {
                "hl2_h3": "empty; charged into heat 4417",
                "radiator_bale": "held on apron",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.42,
            [
                ("libs_ratio_reconstruction", 0.15),
                ("bounded_hopper_accept", 0.12),
                ("radiator_bale_out_of_scope", 0.10),
                ("isolate_tripwire_armed", 0.08),
                ("held_bale_takt_cost", -0.03),
            ],
            "scored for an earned ACCEPT of this hopper on a recomputable LIBS Cu ratio while refusing a last-heat corridor plus radiator-bale dump",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "libs-eaf", "serialized-reconstruction", "operational-companion"],
            distillation_note="LIBS charge gate: 324/373 ratio reconstruction beats a last-heat spectrometer corridor; companion t2 dumps the hopper rather than re-arguing Cu",
        ),
    }
    traj2 = {
        "id": "nelb-r19-058-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "HL-EAF-2026-0409-exec",
            "domain": "eaf_hopper_charge_execution",
            "setting": "Same HL-2 after the bounded ACCEPT. This companion is the operational hopper dump, not a second chemistry vote.",
            "observables_at_decision": {
                "belt_m_s": 1.40,
                "speed_envelope_m_s": [1.20, 1.60],
                "cu_ppm": 170.0,
                "magnet_on": 1,
            },
        },
        "proposed_action": {
            "actor": "charge controller following the ACCEPT",
            "summary": "dump HL-2-H3 at 1.40 m/s, magnet on, LIBS live as isolate interlock, radiator bale stays on the apron",
            "basis_claimed": "ACCEPT requirements are fully specified and inside the belt envelope",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "The execution envelope is intact: belt 1.40 m/s is inside 1.20-1.60, magnet is on, and the isolate tripwire (cu_ppm > 250) is armed on the same LIBS head. ACCEPT the dump. Do not add the radiator bale at empty; 170 ppm is the hopper cap until a new frame.",
            "threshold": "speed in [1.20,1.60] m/s AND magnet_on AND isolate_tripwire_armed AND bale_not_charged",
        },
        "executed_action": {
            "summary": "hopper released t_s 6600; empty t_s 10200; peak cu 170 ppm; radiator bale held",
            "tool": "hl2-charge-exec",
            "observation": "belt 1.40 then 1.38 m/s; no isolate; bale left on apron",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6600.0, "event": "hopper released"},
                {"t_s": 10200.0, "event": "hopper empty"},
                {"t_s": 11400.0, "event": "execution ACCEPT complete"},
            ],
            "observed_effects": [
                "isolate tripwire never fired; 170 ppm vs 250 ppm floor",
                "radiator bale remained out of scope after empty",
            ],
            "new_state": {"hl2_h3": "empty", "radiator_bale": "held", "heat_4417": "charged"},
            "latency_ms": 4800000.0,
        },
        "reward_components": reward(
            0.36,
            [
                ("envelope_respect", 0.13),
                ("isolate_interlock_live", 0.11),
                ("no_bale_add", 0.09),
                ("hopper_empty_on_segment", 0.05),
                ("apron_hold_cost", -0.02),
            ],
            "operational execution gate: the companion dumps the hopper rather than re-opening the Cu call",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "eaf-charge"]),
    }
    return {
        "id": "nelb-r19-058",
        "spike_events": events,
        "language_view": {
            "description": "Hearthloom Steel HL-2. Plant-owned hopper LIBS reconstructs 170.0 ppm Cu from the 324.75/373.49 nm ratio while last-heat spark-OES still shows 0.12 wt%. The gate ACCEPTs this hopper this heat; a companion execution ACCEPT dumps the hopper inside the belt envelope and holds the radiator bale. The ratio model is serialized so every recon event recomputes.",
            "trajectory": traj,
            "trajectory_charge_execution": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "libs.Icu / libs.Ife": "Cu I 324.75 nm and Fe I 373.49 nm; the physics channels the reconstruction consumes",
                "recon.cu / libs.lock": "serialized Cu ppm",
                "heat.cu_wt / eaf.MW": "last-heat spark-OES and idle-power corridor; the denial channels that look healthy",
                "bale.rad / bale.held": "radiator bale on apron vs held out of scope",
                "ops.prop / gate.charge / gate.exec": "hopper-plus-bale proposal, bounded ACCEPT, companion ACCEPT",
                "hopper.release / belt.v / mag.on / hopper.empty": "operational companion channels",
            },
            "temporal_motifs": [
                "last-heat-healthy while hopper-Cu-present: heat.cu_wt 0.12 next to recon.cu 170.0",
                "compensation as event: recon.cu 170.0 equals 40.0*8.50/2.00",
                "ACCEPT then operational ACCEPT: gate.charge at 6000 s, gate.exec at 11400 s",
                "tight LIBS pair: libs.Icu then libs.Ife +1.5 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'324 nm is slag sparkle' = libs.Icu 8.50 next to last-heat 0.12; '170 ppm Cu' = recon.cu 170.0; 'this hopper not the bale' = gate.charge ACCEPT plus bale.held; 'execute the dump' = hopper.release then companion ACCEPT",
            "why_high_value": "New LIBS EAF-scrap family (not fab OES endpoint, not LPBF melt-pool photodiodes, not CEMS k-script). First 324/373 Cu-ratio reconstruction that can hide a Cu hopper inside a last-heat spectrometer corridor. Companion t2 is operational hopper execution. sim_or_real=designed.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 20260921, "stream_note": "stream amplitudes are authored constants (au, ppm, wt%, t, m/s, bool)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "LIBS laser exists at 10 Hz; stream keeps 4 I_Cu points; recon keeps 4 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "libs.Icu": 60000,
                    "libs.Ife": 1.5,
                    "recon.cu": 60000,
                    "heat.cu_wt": 60000,
                    "eaf.MW": 60000,
                    "hopper.t": 60000,
                    "bale.rad": 60000,
                    "ops.prop": 60000,
                    "gate.charge": 60000,
                    "hopper.release": 60000,
                    "belt.v": 60000,
                    "mag.on": 60000,
                    "libs.lock": 60000,
                    "hopper.empty": 60000,
                    "gate.exec": 60000,
                    "trip.hold": 60000,
                    "bale.held": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-04-09T05:00:00Z campaign start",
            },
            "distillation_targets": [
                "LIBS ratio reconstruction head: cu_ppm = k * I_Cu / I_Fe",
                "bounded ACCEPT head: ppm tripwire AND hopper/heat scope AND bale-out-of-scope",
                "operational companion: execute the dump without re-opening the Cu call",
            ],
        },
        "reconstruction_model": {
            "name": "libs_cu_fe_ratio_ppm",
            "formula": "cu_ppm = k_ratio * I_Cu324_au / I_Fe373_au",
            "parameters": {
                "k_ratio_ppm": 40.0,
                "tripwire_cu_ppm": 180.0,
                "isolate_cu_ppm": 250.0,
            },
            "worked_example": {
                "I_Cu324_au": 8.50,
                "I_Fe373_au": 2.00,
                "cu_ppm": 170.0,
            },
            "check": "40.0 * 8.50 / 2.00 = 170.0 exactly",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 32.0,
            "decision_window_s": 0.032,
            "code": "hl2.charge_release_gate",
            "note": "ACCEPT accumulator wins: Cu-ratio and hopper-scope evidence overpower the last-heat advocate",
            "decode_rule": "accept if cu_ratio AND fe_norm AND hopper_margin fire inside the window; last_heat_advocate is necessary-but-not-sufficient and cannot release the radiator bale",
            "populations": [
                gate_pop("cu_ratio_evidence", 80, 1.5, 50.0, w_s),
                gate_pop("fe_norm_evidence", 64, 1.2, 31.25, w_s),
                gate_pop("hopper_margin", 40, 1.0, 50.0, w_s),
                gate_pop("last_heat_advocate", 40, 0.8, 25.0, w_s),
                gate_pop("accept_latch", 96, 1.8, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "hl2.ratio_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 32.0},
                {"check": "hl2.cu_scorer", "neurons": 50, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r19-058",
            clock_domain="hl2-libs-campaign-relative-ms-t0-2026-04-09T05:00:00Z",
            tags=["libs-eaf", "ACCEPT", "ACCEPT", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 059 — QEPAS transformer DGA acetylene, simulated, MODIFY / REJECT
# ---------------------------------------------------------------------------
def rec_059():
    raster = make_raster(
        neurons=25,
        mean_rate_hz=50.0,
        window_ms=28.0,
        seed=20260922,
        source="gb7.qepas.cell",
        target="gorsebank.dga_derate_core",
        table=[
            {"from": "qepas_S", "to": "c2h2_estimator", "weight": 1.30},
            {"from": "cell_P", "to": "pressure_norm_core", "weight": 1.25},
            {"from": "gasveil_gc", "to": "vendor_continue_advocate", "weight": 0.40},
        ],
        third_factor={
            "modulator": "da.dga_class_error",
            "tau_e_s": 1.2,
            "tau_e_ms": 1200.0,
            "eligibility": "pre-post coincidence on C2H2-class synapses; the class-error modulator depresses keep-load links when photoacoustic amplitude stays high inside tau_e of a 600 mbar cell-pressure sample",
        },
        channel_prefix="qepas.n",
        anchor="GB-7 QEPAS 28 ms frame at S 12.60 mV / P 600 mbar (t_s 5400) that reconstructs 1.00 ppm C2H2 at the D2 caution floor",
    )
    w_s = 0.028
    events = [
        ev(0.0, "qepas.S", 6.30, code="S_MV", units="mV", note="sealed QEPAS cell on simulated GB-7 headspace loop"),
        ev(600000.0, "cell.P", 600.0, code="P_MBAR", units="mbar"),
        ev(1200000.0, "recon.c2h2", 0.50, code="C2H2_PPM", units="ppm", note="6.30/(0.021*600)=0.50 exact; D1"),
        ev(1800000.0, "oil.T", 62.0, code="OIL_C", units="C"),
        ev(2400000.0, "load.mva", 1.00, code="LOAD_PU", units="pu"),
        ev(3000000.0, "qepas.S", 9.45, code="S_MV", units="mV"),
        ev(3600000.0, "recon.c2h2", 0.75, code="C2H2_PPM", units="ppm", note="9.45/12.60=0.75"),
        ev(4200000.0, "gasveil.ppm", 0.16, code="VENDOR_C2H2", units="ppm", note="GasVeil vendor GC cloud; the only lab-GC SoT"),
        ev(4800000.0, "bush.T", 48.0, code="BUSHING_C", units="C", note="bushing looks cool; a thermal corridor is not a DGA license"),
        ev(5400000.0, "qepas.S", 12.60, code="S_MV", units="mV", note="D2-class frame; raster sidecar"),
        ev(5400001.3, "cell.P", 600.0, code="P_MBAR", units="mbar", note="1.3 ms pressure-norm after S"),
        ev(6600000.0, "recon.c2h2", 1.00, code="C2H2_PPM", units="ppm", note="12.60/(0.021*600)=1.00 exact; D2 floor"),
        ev(7200000.0, "gasveil.ppm", 0.18, code="VENDOR_C2H2", units="ppm"),
        ev(7800000.0, "load.mva", 1.00, code="LOAD_PU", units="pu"),
        ev(8400000.0, "oil.T", 64.0, code="OIL_C", units="C"),
        ev(9000000.0, "ops.prop", 1.0, code="KEEP_100", units="bool", note="shift chemist Ivo Sedge: keep 1.00 pu; GasVeil 0.18 ppm and bushing cool"),
        ev(9600000.0, "gate.derate", 1.0, code="MODIFY", units="decision", note="derate to 0.70 pu this bank this night; 8 h resample"),
        ev(10200000.0, "load.set", 0.70, code="LOAD_PU", units="pu"),
        ev(10800000.0, "resample.start", 1.0, code="RESAMPLE_START", units="bool", note="bookend 1 of the 8.0 h floor"),
        ev(18000000.0, "oil.T", 61.0, code="OIL_C", units="C"),
        ev(28800000.0, "oil.T", 59.0, code="OIL_C", units="C"),
        ev(39600000.0, "resample.floor", 1.0, code="RESAMPLE_FLOOR", units="bool", note="10800 s + 28800 s = 39600 s = 8.0 h"),
        ev(40200000.0, "ops.restore", 1.0, code="RESTORE_100", units="bool", note="Sedge: GasVeil still 0.17 ppm, restore 1.00 pu"),
        ev(40800000.0, "gate.hold", 1.0, code="REJECT", units="decision", note="companion t2: refuse restore; vendor GC is not SoT"),
        ev(41400000.0, "load.set", 0.70, code="LOAD_HELD", units="pu"),
        ev(42000000.0, "gasveil.ppm", 0.17, code="VENDOR_C2H2", units="ppm"),
        ev(42600000.0, "recon.c2h2", 1.02, code="C2H2_PPM", units="ppm"),
        ev(43200000.0, "gc.indep", 0.0, code="INDEP_GC", units="bool", note="zero independent lab-GC witness on site"),
        ev(43800000.0, "qepas.S", 12.85, code="S_MV", units="mV"),
        ev(44400000.0, "load.mva", 0.70, code="LOAD_HELD_PU", units="pu"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r19-059-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "GB-DGA-2026-0614",
            "domain": "qepas_transformer_dga",
            "setting": "Gorsebank Grid 400 kV bank GB-7 (invented). Simulated campaign on a sealed QEPAS cell sampling the headspace loop, with bushing temperature as an independent thermal witness. GasVeil OEM cloud is the only lab-GC SoT and is not admissible. Not stack-gas CEMS, not e-nose MOX, not nanopore.",
            "observables_at_decision": {
                "S_mV": 12.60,
                "P_mbar": 600.0,
                "c2h2_ppm": 1.00,
                "gasveil_ppm": 0.18,
                "load_pu": 1.00,
                "d2_floor_ppm": 1.00,
            },
            "margin_authority": "GB-7 DGA SOP rev A: if reconstructed C2H2_ppm >= 1.00 (IEEE C57.104 D2) AND < 2.00 (D3 trip), derate to 0.70 pu this bank this night and start an 8 h resample. A vendor GC cloud cannot keep 1.00 pu.",
        },
        "proposed_action": {
            "actor": "shift chemist Ivo Sedge, citing GasVeil 0.18 ppm and a cool bushing",
            "summary": "keep GB-7 at 1.00 pu overnight; resample on Monday day-shift",
            "basis_claimed": "GasVeil lab-GC is green and walking a derate at night is a 30 percent MVA cut",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "The bank is not tripped, and it is not left at 1.00 pu. Serialized reconstruction: c2h2_ppm = S_mV / (0.021 * P_mbar) = 12.60 / (0.021 * 600.0) = 1.00, on the D2 caution floor. Ordered: derate GB-7 to 0.70 pu this night, start the 8 h resample. GasVeil 0.18 ppm is vendor-writable lab-GC and is not an admissible keep-load witness. Scope: this MODIFY does not trip the bank (D3 is 2.00 ppm) and does not start oil processing.",
            "threshold": "c2h2_ppm>=1.00 AND c2h2_ppm<2.00 => derate 0.70 pu; 8 h resample",
            "stated_residuals": "8 h resample before any restore; 0.70 pu is a production cut; lab-GC remains unmeasured by any plant-owned channel",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 9600: 0.70 pu commanded; resample clock started; GasVeil channel not used as SoT",
            "tool": "gb7-qepas-derate-gate-cli",
            "observation": "c2h2 1.00 ppm recomputes from S 12.60 mV and P 600 mbar; QEPAS hashed; GasVeil not SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 5400.0, "event": "QEPAS S 12.60 mV; raster frame; c2h2 1.00 ppm"},
                {"t_s": 9000.0, "event": "ops proposes keep 1.00 pu"},
                {"t_s": 9600.0, "event": "MODIFY derate 0.70 pu"},
                {"t_s": 10800.0, "event": "resample bookend 1"},
                {"t_s": 39600.0, "event": "8.0 h floor"},
                {"t_s": 40800.0, "event": "companion REJECT restore"},
            ],
            "observed_effects": [
                "C2H2 recomputes from the serialized QEPAS model at every recon.c2h2 event",
                "a GasVeil-only head would have kept 1.00 pu overnight",
                "8.0 h resample floor is in the stream (resample.start, oil.T markers, resample.floor), not only in the companion timeline",
            ],
            "surprises": [
                "a cool bushing and a green vendor GC dashboard co-existed with a D2 QEPAS reconstruction",
            ],
            "new_state": {
                "gb7_load_pu": 0.70,
                "resample": "running",
                "gasveil": "not SoT",
            },
            "latency_ms": 31200000.0,
        },
        "reward_components": reward(
            0.39,
            [
                ("qepas_reconstruction", 0.14),
                ("d2_derate", 0.12),
                ("vendor_gc_nonsubstitution", 0.09),
                ("resample_floor_in_stream", 0.08),
                ("mva_derate_cost", -0.04),
            ],
            "scored for a D2 derate on a recomputable QEPAS C2H2 while refusing a vendor GC keep-load; 8 h floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["MODIFY", "qepas-dga", "serialized-reconstruction", "operational-companion"],
            distillation_note="QEPAS DGA gate: photoacoustic C2H2 reconstruction beats a green vendor GC dashboard; companion t2 refuses restore on vendor-only lab-GC",
        ),
    }
    traj2 = {
        "id": "nelb-r19-059-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "GB-DGA-2026-0614-restore",
            "domain": "vendor_only_gc_restore_refusal",
            "setting": "Same GB-7 after the derate MODIFY and the 8 h resample floor. Shift chemist proposes restoring 1.00 pu on GasVeil (the only lab-GC SoT; no independent plant GC). Operational quality gate, not a disclosure vote.",
            "observables_at_decision": {
                "gasveil_ppm": 0.17,
                "independent_gc_present": 0,
                "c2h2_ppm": 1.02,
                "load_pu": 0.70,
            },
        },
        "proposed_action": {
            "actor": "shift chemist Ivo Sedge",
            "summary": "restore 1.00 pu now that 8 h elapsed; GasVeil 0.17 ppm is in the D1 envelope",
            "basis_claimed": "the 8 h outage is already paid and GasVeil never left 0.18 ppm",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Restore is refused. Lab-GC has no plant-owned witness: gc.indep is 0, GasVeil is vendor-writable, and QEPAS still reads 1.02 ppm on the D2 floor. The gate must refuse on custody plus reconstruction, not on a magnitude fight against 0.17 ppm. Ordered: leave 0.70 pu, do not restore 1.00 pu on a vendor GC plane. Do not convert the refusal into a personnel action on Sedge.",
            "threshold": "restore-to-1.00pu requires independent lab-GC OR c2h2_ppm<0.50; neither holds",
        },
        "executed_action": {
            "summary": "REJECT at t_s 40800: 1.00 pu not restored; GasVeil not SoT; Sedge not referred",
            "tool": "gb7-gc-custody-gate-cli",
            "observation": "gc.indep stayed 0; recon.c2h2 1.02; load 0.70 pu held",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 39600.0, "event": "8.0 h resample floor marked"},
                {"t_s": 40200.0, "event": "restore 1.00 pu proposed"},
                {"t_s": 40800.0, "event": "REJECT restore; vendor-only GC"},
            ],
            "observed_effects": [
                "refusal is structural (no independent GC) plus reconstruction still D2, not a magnitude argument against 0.17 ppm",
                "derate MODIFY was not re-opened as a trip",
            ],
            "new_state": {
                "restore": "not taken",
                "load_pu": 0.70,
                "sedge": "not referred",
            },
            "latency_ms": 120000.0,
        },
        "reward_components": reward(
            0.38,
            [
                ("vendor_only_refusal", 0.14),
                ("custody_before_magnitude", 0.12),
                ("derate_held", 0.09),
                ("no_personnel_reopen", 0.07),
                ("overnight_mva_cost", -0.04),
            ],
            "operational refusal: restore dies on missing independent lab-GC plus QEPAS still D2",
        ),
        "meta": meta_common(tags=["REJECT", "operational-execution", "vendor-only-telemetry"]),
    }
    return {
        "id": "nelb-r19-059",
        "spike_events": events,
        "language_view": {
            "description": "Gorsebank Grid GB-7 simulated QEPAS cell. Photoacoustic amplitude 12.60 mV at 600 mbar reconstructs 1.00 ppm C2H2 at the D2 floor while GasVeil vendor GC still shows 0.18 ppm. The gate MODIFYs to 0.70 pu and starts an 8 h resample serialized in the stream. Companion t2 REJECTS a restore to 1.00 pu on vendor-only lab-GC with no independent GC witness.",
            "trajectory": traj,
            "trajectory_restore_refusal": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "qepas.S / cell.P": "photoacoustic amplitude and cell pressure; C2H2 inputs",
                "recon.c2h2": "serialized acetylene ppm",
                "gasveil.ppm / gc.indep": "vendor lab-GC cloud vs the missing independent GC channel",
                "load.mva / load.set": "nameplate load vs commanded derate",
                "ops.prop / gate.derate / ops.restore / gate.hold": "keep-100 proposal, MODIFY derate, restore, companion REJECT",
                "resample.start / resample.floor / oil.T": "slow resample floor bookends plus oil-temperature markers",
            },
            "temporal_motifs": [
                "vendor-green while QEPAS-D2: gasveil.ppm 0.18 next to recon.c2h2 1.00",
                "reconstruction as event: recon.c2h2 1.00 equals 12.60/(0.021*600)",
                "MODIFY then operational REJECT: gate.derate at 9600 s, gate.hold at 40800 s",
                "slow floor in-stream: resample.start 10800 s, resample.floor 39600 s (8.0 h)",
            ],
            "language_to_spike_mapping": "'GasVeil is green' = gasveil.ppm 0.18 with gc.indep 0; '1.00 ppm C2H2' = recon.c2h2 1.00; 'derate 0.70' = gate.derate MODIFY; 'do not restore' = gate.hold REJECT",
            "why_high_value": "New QEPAS transformer-DGA family (not stack-gas CEMS, not e-nose MOX, not VRFB EIS). Puts an 8.0 h resample floor in the stream. Companion t2 is a vendor-only lab-GC restore refusal. sim_or_real=simulated on a sealed cell.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 20260922, "stream_note": "stream amplitudes authored (mV, mbar, ppm, C, pu, bool)"},
                "draw_order": "raster per neuron id order with adaptation/noise",
                "thinning": "QEPAS quartz fork exists at 32 kHz; stream keeps envelope S at 5 points; oil T keeps 4 of ~8 h",
                "refractory_floors_ms": {
                    "qepas.S": 60000,
                    "cell.P": 1.3,
                    "recon.c2h2": 60000,
                    "oil.T": 60000,
                    "load.mva": 60000,
                    "gasveil.ppm": 60000,
                    "bush.T": 60000,
                    "ops.prop": 60000,
                    "gate.derate": 60000,
                    "load.set": 60000,
                    "resample.start": 60000,
                    "resample.floor": 60000,
                    "ops.restore": 60000,
                    "gate.hold": 60000,
                    "gc.indep": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-06-14T21:00:00Z simulated night start",
            },
            "distillation_targets": [
                "QEPAS reconstruction head: c2h2 = S / (k_cell * P)",
                "D2 derate vs keep-whole: floor AND not-yet-D3",
                "vendor-only restore refusal: missing independent GC is sufficient without a magnitude fight",
                "slow resample floor as events: two bookends plus oil-T markers at 8.0 h",
            ],
        },
        "reconstruction_model": {
            "name": "qepas_c2h2_from_pa_and_pressure",
            "formula": "c2h2_ppm = S_mV / (k_cell_mV_per_ppm_mbar * P_mbar)",
            "parameters": {
                "k_cell_mV_per_ppm_mbar": 0.021,
                "P_mbar": 600.0,
                "d2_floor_ppm": 1.00,
                "d3_trip_ppm": 2.00,
                "resample_h": 8.0,
            },
            "worked_example": {"S_mV": 12.60, "P_mbar": 600.0, "c2h2_ppm": 1.00},
            "check": "12.60 / (0.021 * 600.0) = 1.00 exactly; 10800 s + 28800 s = 39600 s = 8.0 h floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 28.0,
            "decision_window_s": 0.028,
            "code": "gb7.dga_derate_gate",
            "note": "MODIFY accumulator wins: QEPAS D2 evidence overpowers the vendor GC-continue advocate",
            "decode_rule": "modify-derate if c2h2_estimator AND pressure_norm fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("c2h2_estimator", 100, 1.5, 50.0, w_s),
                gate_pop("pressure_norm", 40, 1.2, 50.0, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("modify_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "gb7.qepas_scorer", "neurons": 100, "mean_rate_hz": 50.0, "window_ms": 28.0},
                {"check": "gb7.derate_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 40.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r19-059",
            clock_domain="gb7-qepas-sim-relative-ms-t0-2026-06-14T21:00:00Z",
            tags=["qepas-dga", "MODIFY", "REJECT", "vendor-only", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 060 — Lorentz-force velocimetry liquid Al, hil, REJECT / MODIFY
# ---------------------------------------------------------------------------
def rec_060():
    raster = make_raster(
        neurons=16,
        mean_rate_hz=62.5,
        window_ms=40.0,
        seed=20260923,
        source="mf9.lfv.magnet",
        target="marlfen.pour_stop_core",
        table=[
            {"from": "lfv_F", "to": "velocity_estimator", "weight": 1.40},
            {"from": "lfv_I", "to": "drive_norm_core", "weight": 1.20},
            {"from": "flowgilt_v", "to": "vendor_continue_advocate", "weight": 0.20},
        ],
        third_factor={
            "modulator": "ach.vendor_flow_conflict",
            "tau_e_s": 1.8,
            "tau_e_ms": 1800.0,
            "eligibility": "pre-post coincidence on pour-stop synapses; the vendor-flow modulator depresses keep-pour links when no independent vendor-writable velocity agrees with plant LFV inside tau_e of an oxide-carry force step",
        },
        channel_prefix="lfv.n",
        anchor="MF-9 HIL launder 40 ms frame at F_L 0.180 N / I 5.0 A (t_s 600) reconstructing 3.00 m/s above the 2.90 m/s oxide-carry floor",
    )
    w_s = 0.040
    events = [
        ev(0.0, "lfv.F", 0.108, code="F_L_N", units="N", note="HIL pit spare MF-9 launder; plant-owned Lorentz magnet pair"),
        ev(30000.0, "lfv.I", 5.0, code="I_A", units="A"),
        ev(60000.0, "recon.v", 1.80, code="V_M_S", units="m_s", note="0.108/(0.12*5.0*0.10)=1.80; freeze floor"),
        ev(180000.0, "pyro.C", 692.0, code="METAL_C", units="C", note="live-launder shadow 692 C; HIL times the pour stop"),
        ev(240000.0, "flowgilt.v", 2.15, code="VENDOR_V", units="m_s", note="FlowGilt vendor velocity cloud; the only in-launder OEM SoT"),
        ev(360000.0, "lfv.F", 0.144, code="F_L_N", units="N"),
        ev(420000.0, "recon.v", 2.40, code="V_M_S", units="m_s", note="0.144/0.060=2.40"),
        ev(480000.0, "recon.mdot", 9.60, code="T_H", units="t_h", note="4.00*2.40=9.60"),
        ev(600000.0, "lfv.F", 0.180, code="F_L_N", units="N", note="oxide-carry frame; raster sidecar"),
        ev(600001.2, "lfv.I", 5.0, code="I_A", units="A", note="1.2 ms drive-norm after F"),
        ev(720000.0, "recon.v", 3.00, code="V_M_S", units="m_s", note="0.180/(0.12*5.0*0.10)=3.00 exact; oxide floor 2.90"),
        ev(780000.0, "recon.mdot", 12.00, code="T_H", units="t_h", note="4.00*3.00=12.00 exact"),
        ev(840000.0, "flowgilt.v", 2.20, code="VENDOR_V", units="m_s", note="vendor still inside 1.80-2.90 envelope"),
        ev(960000.0, "ops.prop", 1.0, code="KEEP_12TH", units="bool", note="pour boss Len Harth: keep 12 t/h, FlowGilt 2.20 is mid-range, pyro 692 C"),
        ev(1020000.0, "gate.pour", 1.0, code="REJECT", units="decision", note="stop pour; 3.00 m/s is above oxide-carry floor; FlowGilt not SoT"),
        ev(1080000.0, "pour.stop", 1.0, code="STOP", units="bool"),
        ev(1140000.0, "heel.start", 1.0, code="HEEL_START", units="bool", note="bookend 1 of the 45 min heel-hold floor"),
        ev(1500000.0, "pyro.C", 688.0, code="METAL_C", units="C"),
        ev(2100000.0, "pyro.C", 681.0, code="METAL_C", units="C"),
        ev(2700000.0, "pyro.C", 674.0, code="METAL_C", units="C"),
        ev(3300000.0, "heel.t", 4.00, code="HEEL_T_H", units="t_h"),
        ev(3720000.0, "pyro.C", 668.0, code="METAL_C", units="C", note="45.0 min after stop (1020 s + 2700 s); floor marker"),
        ev(3780000.0, "heel.floor", 1.0, code="HEEL_FLOOR", units="bool"),
        ev(3840000.0, "ops.kill", 1.0, code="FREEZE_KILL", units="bool", note="Harth: freeze-kill the launder until Monday"),
        ev(4320000.0, "gate.heel", 1.0, code="MODIFY", units="decision", note="companion t2: heel-hold 4 t/h; freeze-kill would freeze the channel solid"),
        ev(4500000.0, "lfv.F", 0.096, code="F_L_N", units="N"),
        ev(4800000.0, "recon.v", 1.60, code="V_M_S", units="m_s", note="0.096/0.060=1.60; below freeze floor on purpose during heel"),
        ev(5100000.0, "flowgilt.v", 2.18, code="VENDOR_V", units="m_s", note="still vendor-green; still not SoT"),
        ev(5400000.0, "pour.held", 0.0, code="POUR_12", units="bool"),
        ev(5700000.0, "recon.mdot", 6.40, code="T_H", units="t_h", note="4.00*1.60=6.40 during heel taper"),
        ev(6000000.0, "heel.t", 4.00, code="HEEL_HELD", units="t_h"),
        ev(6300000.0, "pyro.C", 665.0, code="METAL_C", units="C"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r19-060-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "MF-LFV-2026-0211",
            "domain": "lfv_aluminum_launder_pour",
            "setting": "Marlfen Smelter potline MF-9 (invented), 12 t/h liquid-aluminum launder. Hardware-in-the-loop magnet pair on a spare launder section supplies the Lorentz force that times live-pour stop. Plant-owned LFV. FlowGilt vendor cloud is the only OEM in-launder velocity SoT. Not fluxgate gradiometry, not MsS T(0,1), not PMU.",
            "observables_at_decision": {
                "F_L_N": 0.180,
                "I_A": 5.0,
                "v_m_s": 3.00,
                "mdot_t_h": 12.00,
                "flowgilt_v_m_s": 2.20,
                "oxide_floor_m_s": 2.90,
            },
            "margin_authority": "MF-9 LFV SOP rev B: if reconstructed v_m_s >= 2.90 (oxide carry) OR v_m_s <= 1.80 (freeze), stop the 12 t/h pour. A vendor velocity cloud cannot keep 12 t/h.",
        },
        "proposed_action": {
            "actor": "pour boss Len Harth, citing FlowGilt 2.20 m/s in envelope and pyro 692 C",
            "summary": "keep 12 t/h through the night; oxide skim on Monday day-shift",
            "basis_claimed": "FlowGilt is mid-range and walking a stop at night freezes the heel",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Keep-pour is refused. Serialized reconstruction: v_m_s = F_L_N / (0.12 * I_A * 0.10) = 0.180 / (0.12 * 5.0 * 0.10) = 3.00, above the 2.90 m/s oxide-carry floor; mdot = 4.00 * 3.00 = 12.00 t/h. FlowGilt 2.20 m/s is vendor-writable and disagrees by 0.80 m/s; it is not an admissible keep-pour witness. Ordered: stop the 12 t/h pour now. Scope: this REJECT does not freeze-kill the launder (that is the companion question) and does not trip the potline.",
            "threshold": "v_m_s>=2.90 OR v_m_s<=1.80 => stop 12 t/h; FlowGilt is not SoT",
            "stated_residuals": "heel-hold still required to avoid a solid freeze; 12 t/h cut is a production loss; FlowGilt remains the only OEM channel",
        },
        "executed_action": {
            "summary": "REJECT at t_s 1020: 12 t/h pour stopped; FlowGilt not SoT; reconstruction locked",
            "tool": "mf9-lfv-pour-gate-cli",
            "observation": "v 3.00 m/s recomputes from F 0.180 N and I 5.0 A; HIL waveform hashed; FlowGilt channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 600.0, "event": "LFV F 0.180 N; raster frame; v 3.00 m/s"},
                {"t_s": 960.0, "event": "ops proposes keep 12 t/h"},
                {"t_s": 1020.0, "event": "REJECT stop pour"},
                {"t_s": 1140.0, "event": "heel-hold bookend 1"},
                {"t_s": 3720.0, "event": "45 min floor; metal 668 C"},
                {"t_s": 4320.0, "event": "companion MODIFY heel-hold vs freeze-kill"},
            ],
            "observed_effects": [
                "velocity recomputes from the serialized Lorentz model at every recon.v event",
                "a FlowGilt-only head would have kept 12 t/h overnight",
                "45 min heel floor is in the stream (heel.start, pyro.C 668 C, heel.floor)",
            ],
            "surprises": [
                "a mid-range vendor velocity and a liquid pyrometer co-existed with an oxide-carry LFV force",
            ],
            "new_state": {
                "mf9_pour_t_h": 0.0,
                "heel": "starting",
                "flowgilt": "not SoT",
            },
            "latency_ms": 2700000.0,
        },
        "reward_components": reward(
            0.41,
            [
                ("lfv_reconstruction", 0.14),
                ("oxide_carry_stop", 0.12),
                ("vendor_flow_nonsubstitution", 0.10),
                ("heel_floor_in_stream", 0.08),
                ("pour_cut_cost", -0.03),
            ],
            "scored for a keep-pour REJECT on a recomputable Lorentz velocity while refusing a vendor mid-range dashboard; 45 min floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["REJECT", "lfv-al", "serialized-reconstruction", "hil", "operational-companion"],
            distillation_note="LFV pour gate: Lorentz force to velocity reconstruction beats a green vendor flow dashboard; companion t2 is heel-hold execution, not a freeze-kill",
        ),
    }
    traj2 = {
        "id": "nelb-r19-060-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "MF-LFV-2026-0211-heel",
            "domain": "launder_heel_hold_execution",
            "setting": "Same MF-9 after the pour REJECT. Pour boss proposes a freeze-kill that would empty the launder solid. This companion is the operational heel-hold, not a second velocity vote.",
            "observables_at_decision": {
                "heel_t_h": 4.00,
                "pyro_C": 668.0,
                "v_m_s": 1.60,
                "proposed": "freeze_kill",
            },
        },
        "proposed_action": {
            "actor": "pour boss Len Harth",
            "summary": "freeze-kill the launder until Monday; 45 min already paid",
            "basis_claimed": "the REJECT already stopped 12 t/h, so emptying solid is the cheapest hold",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Hold a 4 t/h heel. Freeze-kill would drop metal below the 660 C liquidus on a 40 m open launder and freeze the channel solid (a restart measured in shifts, not hours). MODIFY the freeze-kill to a 4 t/h heel-hold. Do not restore 12 t/h. Do not convert the hold into a personnel action on Harth.",
            "threshold": "heel_t_h==4.00 AND pyro_C>=660 AND pour_12_not_restored",
        },
        "executed_action": {
            "summary": "heel-hold 4 t/h at t_s 4320; freeze-kill not latched; 12 t/h not restored",
            "tool": "mf9-heel-hold-exec",
            "observation": "pyro 668 then 665 C; recon.v 1.60 m/s during taper; FlowGilt still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 1140.0, "event": "heel clock started after REJECT"},
                {"t_s": 3720.0, "event": "45 min floor; 668 C"},
                {"t_s": 3840.0, "event": "freeze-kill proposed"},
                {"t_s": 4320.0, "event": "MODIFY heel-hold 4 t/h"},
            ],
            "observed_effects": [
                "freeze-kill restart cost is visible without waiting for a solid channel",
                "hold did not reopen the oxide-carry call",
            ],
            "new_state": {"heel_t_h": 4.00, "pour_12": "blocked", "freeze_kill": "not taken"},
            "latency_ms": 480000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("heel_hold", 0.12),
                ("no_freeze_kill", 0.11),
                ("no_12th_restore", 0.08),
                ("liquidus_margin", 0.06),
                ("heel_metal_cost", -0.03),
            ],
            "operational execution gate: heel-hold 4 t/h because freeze-kill freezes the channel; not a velocity re-vote",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "heel-hold"]),
    }
    return {
        "id": "nelb-r19-060",
        "spike_events": events,
        "language_view": {
            "description": "Marlfen Smelter MF-9 HIL launder. Plant-owned Lorentz-force velocimetry reconstructs 3.00 m/s (12.00 t/h) above the 2.90 m/s oxide-carry floor while FlowGilt vendor velocity still shows 2.20 m/s. The gate REJECTs keep-pour. A 45 min heel-hold floor is serialized in the stream. Companion t2 MODIFYs a freeze-kill into a 4 t/h heel-hold.",
            "trajectory": traj,
            "trajectory_heel_hold": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "lfv.F / lfv.I": "Lorentz drag force and drive current; velocity inputs",
                "recon.v / recon.mdot": "serialized velocity m/s and mass-flow t/h",
                "flowgilt.v": "vendor in-launder velocity cloud",
                "pyro.C / heel.t": "metal temperature and heel mass-flow",
                "ops.prop / gate.pour / ops.kill / gate.heel": "keep-12 proposal, REJECT stop, freeze-kill, companion MODIFY",
                "pour.stop / heel.start / heel.floor": "slow heel floor bookends plus marker",
            },
            "temporal_motifs": [
                "vendor-green while LFV-oxide: flowgilt.v 2.20 next to recon.v 3.00",
                "reconstruction as event: recon.v 3.00 equals 0.180/(0.12*5.0*0.10)",
                "REJECT then operational MODIFY: gate.pour at 1020 s, gate.heel at 4320 s",
                "slow floor in-stream: heel.start 1140 s, pyro.C 668 C at 3720 s (45.0 min), heel.floor 3780 s",
            ],
            "language_to_spike_mapping": "'FlowGilt is mid-range' = flowgilt.v 2.20; '3.00 m/s oxide carry' = recon.v 3.00; 'stop 12 t/h' = gate.pour REJECT; 'heel-hold not freeze-kill' = gate.heel MODIFY",
            "why_high_value": "New Lorentz-force velocimetry family on liquid aluminum (not fluxgate gradiometry, not MsS T(0,1) steam, not PMU). Lead REJECT of keep-pour on a recomputable velocity that a vendor dashboard would have cleared. Companion t2 is operational heel-hold. sim_or_real=hil on a spare launder.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 20260923, "stream_note": "stream amplitudes authored (N, A, m/s, t/h, C, bool)"},
                "draw_order": "raster per neuron id order with adaptation/noise",
                "thinning": "LFV force exists at 200 Hz; stream keeps 4 F points; pyro keeps 6 of ~45 min",
                "refractory_floors_ms": {
                    "lfv.F": 30000,
                    "lfv.I": 1.2,
                    "recon.v": 30000,
                    "recon.mdot": 30000,
                    "pyro.C": 60000,
                    "flowgilt.v": 60000,
                    "ops.prop": 60000,
                    "gate.pour": 60000,
                    "pour.stop": 60000,
                    "heel.start": 60000,
                    "heel.t": 60000,
                    "heel.floor": 60000,
                    "ops.kill": 60000,
                    "gate.heel": 60000,
                    "pour.held": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-02-11T22:00:00Z HIL campaign start",
            },
            "distillation_targets": [
                "LFV reconstruction head: v = F / (C * I * L); mdot = k_a * v",
                "oxide-carry stop vs keep-pour: velocity floor AND vendor-nonsubstitution",
                "operational companion: heel-hold rather than freeze-kill after the REJECT",
                "slow heel floor as events: two bookends plus a temperature marker at 45.0 min",
            ],
        },
        "reconstruction_model": {
            "name": "lfv_lorentz_velocity_and_mass_flow",
            "formula": "v_m_s = F_L_N / (C_lfv * I_A * L_m); mdot_t_h = k_a * v_m_s",
            "parameters": {
                "C_lfv": 0.12,
                "I_A": 5.0,
                "L_m": 0.10,
                "k_a_t_h_per_m_s": 4.00,
                "oxide_floor_m_s": 2.90,
                "freeze_floor_m_s": 1.80,
                "heel_floor_min": 45.0,
            },
            "worked_example": {"F_L_N": 0.180, "v_m_s": 3.00, "mdot_t_h": 12.00},
            "check": "0.180 / (0.12 * 5.0 * 0.10) = 3.00 exactly; 4.00 * 3.00 = 12.00; 1020 s + 2700 s = 3720 s = 45.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.040,
            "code": "mf9.lfv_pour_gate",
            "note": "REJECT accumulator wins: LFV oxide-carry evidence overpowers the vendor flow-continue advocate (weight 0.20)",
            "decode_rule": "reject-stop if velocity_estimator AND drive_norm fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("velocity_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("drive_norm", 64, 1.3, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("reject_latch", 96, 1.8, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "mf9.lfv_scorer", "neurons": 96, "mean_rate_hz": 50.0, "window_ms": 40.0},
                {"check": "mf9.force_scorer", "neurons": 40, "mean_rate_hz": 62.5, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r19-060",
            clock_domain="mf9-lfv-hil-relative-ms-t0-2026-02-11T22:00:00Z",
            tags=["lfv-al", "REJECT", "MODIFY", "vendor-flow", "hil", "operational-t2"],
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
        BATCH, "batch-r19.jsonl", staging=FactoryStaging(enabled=True)
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
            source_path="batch-r19.jsonl",
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
    records = [rec_058(), rec_059(), rec_060()]
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
