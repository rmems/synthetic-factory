#!/usr/bin/env python3
"""Generate NELB round-14 research-only bridge pairs (do not write outputs/raw/)."""

from __future__ import annotations

import json
import math
import random
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

OUT_DIR = Path("/tmp/nelb-r14")
BATCH = OUT_DIR / "batch-r14.jsonl"
NOTES = OUT_DIR / "NOTES-r14.md"
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
    "scratchpad",
    "scratch",
    "internal_monologue",
    "private_reasoning",
    "inner_monologue",
}


def meta_common(**extra):
    m = {
        "round": 14,
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
# Record 043 — BOTDA CCS pipeline, designed, ACCEPT / ACCEPT
# ---------------------------------------------------------------------------
def rec_043():
    raster = make_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=36.0,
        seed=20260916,
        source="gf11.botda.interrogator",
        target="glassfen.pig_release_core",
        table=[
            {"from": "botda_nuB", "to": "strain_estimator", "weight": 1.35},
            {"from": "raman_dT", "to": "temp_comp_core", "weight": 1.15},
            {"from": "scada_pressure", "to": "pressure_advocate", "weight": 0.55},
        ],
        third_factor={
            "modulator": "na.hoop_strain_salience",
            "tau_e_s": 2.0,
            "tau_e_ms": 2000.0,
            "eligibility": "pre-post coincidence on wall-remaining synapses; the hoop-strain modulator enables potentiation only while Raman dT and Brillouin nuB are co-active inside tau_e so a thermal-looking drift cannot hide hoop strain",
        },
        channel_prefix="botda.n",
        anchor="GF-11 KP 18.4 BOTDA 36 ms frame at nuB 41.0 MHz (t_s 3600) where temperature-compensated remaining wall first clears the pig tripwire",
    )
    w_s = 0.036
    events = [
        ev(0.0, "botda.dvb", 12.4, code="NU_B_MHZ", units="MHz", note="pre-dawn Brillouin shift; mostly thermal"),
        ev(600000.0, "raman.dT", 4.0, code="DT_C", units="C", note="Raman DTS on the same fiber; temperature-only, not Rayleigh DAS"),
        ev(900000.0, "recon.eps", 168.0, code="EPS_UE", units="microstrain", note="(12.4-1.00*4.0)/0.050 = 168.0 exact"),
        ev(1200000.0, "recon.twall", 12.364, code="T_REM_MM", units="mm", note="12.70 - 0.002*168 = 12.364 mm"),
        ev(1800000.0, "scada.p", 110.0, code="LINE_BAR", units="bar", note="trunkline still at design 110 bar"),
        ev(2400000.0, "botda.dvb", 28.0, code="NU_B_MHZ", units="MHz"),
        ev(2700000.0, "raman.dT", 5.5, code="DT_C", units="C"),
        ev(3000000.0, "recon.eps", 450.0, code="EPS_UE", units="microstrain", note="(28.0-1.00*5.5)/0.050 = 450.0"),
        ev(3300000.0, "recon.twall", 11.80, code="T_REM_MM", units="mm", note="12.70 - 0.002*450 = 11.80"),
        ev(3600000.0, "botda.dvb", 41.0, code="NU_B_MHZ", units="MHz", note="pig-authorization frame; raster sidecar"),
        ev(3900000.0, "raman.dT", 6.0, code="DT_C", units="C"),
        ev(4200000.0, "recon.eps", 700.0, code="EPS_UE", units="microstrain", note="(41.0-1.00*6.0)/0.050 = 700.0 exact"),
        ev(4500000.0, "recon.twall", 11.30, code="T_REM_MM", units="mm", note="12.70 - 0.002*700 = 11.30; tripwire 9.50 mm"),
        ev(4800000.0, "scada.p", 110.0, code="LINE_BAR", units="bar"),
        ev(5400000.0, "ops.prop", 1.0, code="PIG_AT_110", units="bool", note="pigging lead Ryn Hale: launch ILI at design 110 bar, Brillouin is thermal"),
        ev(6000000.0, "gate.pig", 1.0, code="ACCEPT", units="decision", note="bounded ACCEPT: pig this 4.8 km at <=95 bar"),
        ev(6600000.0, "pig.pset", 95.0, code="PIG_BAR", units="bar"),
        ev(7200000.0, "pig.launch", 1.0, code="LAUNCH", units="bool", note="companion execution start"),
        ev(7800000.0, "pig.speed", 1.25, code="V_M_S", units="m_s", note="inside 1.10-1.40 m/s envelope"),
        ev(8400000.0, "pig.kp", 18.4, code="KP_KM", units="km"),
        ev(9000000.0, "botda.dvb", 41.2, code="NU_B_MHZ", units="MHz", note="during pig; jump 0.2 MHz << 8 MHz abort tripwire"),
        ev(9600000.0, "raman.dT", 6.1, code="DT_C", units="C"),
        ev(10200000.0, "recon.eps", 702.0, code="EPS_UE", units="microstrain"),
        ev(10800000.0, "recon.twall", 11.296, code="T_REM_MM", units="mm"),
        ev(11400000.0, "pig.kp", 20.8, code="KP_KM", units="km"),
        ev(12000000.0, "pig.speed", 1.22, code="V_M_S", units="m_s"),
        ev(12600000.0, "pig.kp", 23.2, code="KP_KM", units="km"),
        ev(13200000.0, "pig.rx", 1.0, code="RECEIVER", units="bool"),
        ev(13800000.0, "gate.exec", 1.0, code="ACCEPT", units="decision", note="companion t2: pig sequence completed inside envelope"),
        ev(14400000.0, "scada.p", 95.0, code="HELD_PIG_BAR", units="bar", note="no uprate to 110; scope limit held"),
        ev(15000000.0, "trip.hold", 0.0, code="ABORT_JUMP_MHZ", units="MHz", note="peak nuB jump 0.2; abort not taken"),
        ev(15600000.0, "recon.twall", 11.29, code="T_REM_MM", units="mm"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r14-043-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "GF-ILI-2026-0307",
            "domain": "botda_ccs_pipeline_strain",
            "setting": "Glassfen CCS trunkline GF-11 (invented), 24-inch X70, supercritical CO2, design 110 bar. Nereid-BOTDA interrogator plus a Raman DTS on the same fiber. Invented plant; designed campaign. Not Rayleigh DAS, not FBG glaze, not phi-OTDR.",
            "observables_at_decision": {
                "nuB_MHz": 41.0,
                "dT_C": 6.0,
                "eps_ue": 700.0,
                "t_rem_mm": 11.30,
                "line_bar": 110.0,
                "tripwire_t_rem_mm": 9.50,
            },
            "margin_authority": "GF-11 ILI SOP rev B: a pig may launch only if temperature-compensated remaining wall >= 9.50 mm AND launch pressure <= 95 bar AND the authorization covers this 4.8 km segment this day. A clean 110 bar corridor cannot substitute for the compensated wall.",
        },
        "proposed_action": {
            "actor": "pigging lead Ryn Hale, citing design-pressure corridor and 'Brillouin tracks the Raman thermometer'",
            "summary": "launch the ILI pig at 110 bar from KP 18.4 to 23.2; treat the 41 MHz Brillouin shift as temperature",
            "basis_claimed": "Raman dT is 6 C and a naive uncompensated reading would still look like a thermal envelope",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "The pig is accepted, not the 110 bar launch. Serialized reconstruction: eps_ue = (nuB_MHz - 1.00 * dT_C) / 0.050 = (41.0 - 6.0) / 0.050 = 700.0; t_rem_mm = 12.70 - 0.002 * 700.0 = 11.30, which clears the 9.50 mm tripwire by 1.80 mm. SOP rev B still forbids design pressure: ordered launch at <= 95 bar on KP 18.4-23.2 this day only. Explicit scope: this accept does not cover girth-weld TOFD (different physics) and does not authorize a post-pig uprate back to 110 bar. Abort tripwire: nuB jump > 8.0 MHz during the run.",
            "threshold": "t_rem_mm>=9.50 AND pig_bar<=95 AND segment=KP18.4-23.2 AND day=2026-03-07",
            "stated_residuals": "1.80 mm wall margin is not infinite; 95 bar vs 110 costs ~2.1 h of pad nitrogen; Raman DTS is temperature-only and is not a substitute strain witness",
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 6000: pig authorized at 95 bar on KP 18.4-23.2; 110 bar launch refused; reconstruction locked as SoT",
            "tool": "gf11-botda-pig-gate-cli",
            "observation": "t_rem 11.30 mm recomputes from nuB 41.0 and dT 6.0; pad nitrogen staged; Nereid-BOTDA remains live as the abort interlock",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3600.0, "event": "BOTDA nuB 41.0 MHz; raster frame; compensated wall 11.30 mm"},
                {"t_s": 5400.0, "event": "ops proposes pig at 110 bar"},
                {"t_s": 6000.0, "event": "ACCEPT bounded pig at 95 bar"},
                {"t_s": 7200.0, "event": "companion launch"},
                {"t_s": 13800.0, "event": "companion ACCEPT; pig received; no abort"},
            ],
            "observed_effects": [
                "temperature-compensated remaining wall recomputes from the serialized model at every recon.twall event",
                "a Raman-only head would have treated 41 MHz as 6 C of thermal drift and launched at 110 bar",
                "nuB jump during the pig was 0.2 MHz, well under the 8.0 MHz abort",
            ],
            "surprises": [
                "design-pressure SCADA stayed 110 bar until the pig set-point; a pressure-only head would have launched hot",
            ],
            "new_state": {
                "gf11": "pig received at KP 23.2; line held 95 bar pending weld TOFD",
                "uprate_110_bar": "not authorized",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 3840000.0,
        },
        "reward_components": reward(
            0.42,
            [
                ("temp_compensated_reconstruction", 0.15),
                ("bounded_pig_accept", 0.12),
                ("pressure_scope_limit", 0.10),
                ("abort_tripwire_armed", 0.08),
                ("pad_nitrogen_cost", -0.03),
            ],
            "scored for an earned ACCEPT of a 95 bar pig on a recomputable temperature-compensated wall while refusing the 110 bar corridor substitution",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "botda-ccs", "serialized-reconstruction", "temp-compensated", "operational-companion"],
            distillation_note="BOTDA pig gate: temperature-compensated nuB to remaining-wall reconstruction beats a clean pressure corridor; companion t2 launches the pig rather than re-arguing the wall",
        ),
    }
    traj2 = {
        "id": "nelb-r14-043-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "GF-ILI-2026-0307-exec",
            "domain": "ili_pig_launch_execution",
            "setting": "Same GF-11 after the bounded ACCEPT. This companion is the operational pig launch, not a second policy vote.",
            "observables_at_decision": {
                "pig_bar": 95.0,
                "speed_cmd_m_s": 1.25,
                "speed_envelope_m_s": [1.10, 1.40],
                "t_rem_mm": 11.30,
            },
        },
        "proposed_action": {
            "actor": "pigging controller following the ACCEPT",
            "summary": "launch at 95 bar, speed 1.25 m/s, BOTDA live as abort interlock, receiver at KP 23.2",
            "basis_claimed": "ACCEPT requirements are fully specified and inside the pigging envelope",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "The execution envelope is intact: speed 1.25 m/s is inside 1.10-1.40, pad pressure 95.0 bar matches the ACCEPT cap, and the abort tripwire (nuB jump > 8.0 MHz) is armed on the same interrogator. ACCEPT the launch. Do not uprate to 110 bar at receiver; 95 bar is the cap until weld TOFD.",
            "threshold": "speed in [1.10,1.40] m/s AND pig_bar==95 AND abort_tripwire_armed",
        },
        "executed_action": {
            "summary": "pig launched t_s 7200; KP 18.4-23.2 in 6400 s; peak nuB jump 0.2 MHz; received t_s 13200",
            "tool": "gf11-pig-exec",
            "observation": "speed 1.25 then 1.22 m/s; no abort; line left at 95 bar",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 7200.0, "event": "pig launched at 95 bar"},
                {"t_s": 8400.0, "event": "KP 18.4"},
                {"t_s": 13200.0, "event": "receiver KP 23.2"},
                {"t_s": 13800.0, "event": "execution ACCEPT complete"},
            ],
            "observed_effects": [
                "abort tripwire never fired; 0.2 MHz jump vs 8.0 MHz floor",
                "95 bar cap held after receiver; 110 bar not re-entered",
            ],
            "new_state": {"gf11_bar": 95.0, "pig": "received", "uprate": "blocked"},
            "latency_ms": 6400000.0,
        },
        "reward_components": reward(
            0.36,
            [
                ("envelope_respect", 0.13),
                ("abort_interlock_live", 0.11),
                ("no_uprate", 0.09),
                ("receiver_on_segment", 0.05),
                ("nitrogen_pad_cost", -0.02),
            ],
            "operational execution gate: the companion runs the pig rather than re-opening the wall call",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "ili-pig"]),
    }
    return {
        "id": "nelb-r14-043",
        "spike_events": events,
        "language_view": {
            "description": "Glassfen CCS GF-11. Temperature-compensated BOTDA reconstructs 11.30 mm remaining wall while SCADA still shows 110 bar. The gate ACCEPTs a bounded 95 bar ILI pig on KP 18.4-23.2 this day; a companion execution ACCEPT launches the pig inside the speed envelope and holds the 95 bar cap. The nuB-dT-wall model is serialized so every recon event recomputes.",
            "trajectory": traj,
            "trajectory_pig_launch_execution": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "botda.dvb": "Brillouin frequency shift MHz; the physics channel the reconstruction consumes",
                "raman.dT": "Raman DTS temperature C on the same fiber; compensation term, not a strain substitute",
                "recon.eps / recon.twall": "serialized microstrain and remaining wall mm",
                "scada.p / pig.pset": "line pressure vs pig set-point; the denial channel that stays 110 until the ACCEPT",
                "ops.prop / gate.pig / gate.exec": "110 bar proposal, bounded ACCEPT, companion ACCEPT",
                "pig.launch / pig.speed / pig.kp / pig.rx": "operational companion channels",
            },
            "temporal_motifs": [
                "pressure-healthy while wall-thinned: scada.p 110 bar adjacent to recon.twall 11.30 mm",
                "compensation as event: recon.eps 700.0 equals (41.0-6.0)/0.050",
                "ACCEPT then operational ACCEPT: gate.pig at 6000 s, gate.exec at 13800 s",
                "abort tripwire silent: trip.hold 0.2 MHz vs 8.0 MHz floor",
            ],
            "language_to_spike_mapping": "'Brillouin is just thermal' = raman.dT 6.0 C next to botda.dvb 41.0 MHz; '11.30 mm remaining wall' = recon.twall 11.30; 'pig at 95 bar not 110' = gate.pig ACCEPT plus pig.pset 95; 'execute the launch' = pig.launch then companion ACCEPT",
            "why_high_value": "New BOTDA CCS family (not DAS phi-OTDR, not FBG glaze on TW-17, not Raman as a primary strain channel). Closes the r13 leftover of a temperature-compensated reconstruction that can hide hoop strain inside a thermometer-looking drift, without restaging Nettlewake FBG. First ACCEPT-heavy lead this window. Companion t2 is operational pig execution.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 20260916, "stream_note": "stream amplitudes are authored constants (MHz, C, microstrain, mm, bar, m/s)"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "BOTDA samples ~0.25 Hz over 4.3 h; stream keeps 5 nuB points; recon keeps 6 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "botda.dvb": 60000,
                    "raman.dT": 60000,
                    "recon.eps": 60000,
                    "recon.twall": 60000,
                    "scada.p": 60000,
                    "ops.prop": 60000,
                    "gate.pig": 60000,
                    "pig.pset": 60000,
                    "pig.launch": 60000,
                    "pig.speed": 60000,
                    "pig.kp": 60000,
                    "pig.rx": 60000,
                    "gate.exec": 60000,
                    "trip.hold": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-03-07T04:00:00Z campaign start",
            },
            "distillation_targets": [
                "temperature-compensated reconstruction head: (nuB - C_T*dT)/C_eps -> wall mm",
                "bounded ACCEPT head: wall tripwire AND pressure cap AND segment/day scope",
                "operational companion: execute the pig without re-opening the wall call",
            ],
        },
        "reconstruction_model": {
            "name": "botda_temp_compensated_remaining_wall",
            "formula": "eps_ue = (nuB_MHz - C_T_MHz_per_K * dT_C) / C_eps_MHz_per_ue; t_rem_mm = t_nom_mm - k_wall_mm_per_ue * eps_ue",
            "parameters": {
                "C_T_MHz_per_K": 1.00,
                "C_eps_MHz_per_ue": 0.050,
                "t_nom_mm": 12.70,
                "k_wall_mm_per_ue": 0.002,
                "tripwire_t_rem_mm": 9.50,
                "abort_nuB_jump_MHz": 8.0,
            },
            "worked_example": {
                "nuB_MHz": 41.0,
                "dT_C": 6.0,
                "eps_ue": 700.0,
                "t_rem_mm": 11.30,
            },
            "check": "(41.0 - 1.00*6.0)/0.050 = 700.0; 12.70 - 0.002*700.0 = 11.30 exactly",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 36.0,
            "decision_window_s": 0.036,
            "code": "gf11.pig_release_gate",
            "note": "ACCEPT accumulator wins: compensated wall and pressure-cap evidence overpower the 110 bar advocate",
            "decode_rule": "accept if wall_remaining AND temp_comp AND hoop_margin fire inside the window; pressure_advocate is necessary-but-not-sufficient and cannot release design pressure",
            "populations": [
                gate_pop("wall_remaining_evidence", 80, 1.5, 50.0, w_s),
                gate_pop("temp_comp_evidence", 64, 1.2, 31.25, w_s),
                gate_pop("hoop_margin", 40, 1.0, 50.0, w_s),
                gate_pop("pressure_advocate", 40, 0.8, 25.0, w_s),
                gate_pop("accept_latch", 96, 1.8, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "gf11.wall_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 36.0},
                {"check": "gf11.temp_comp_scorer", "neurons": 64, "mean_rate_hz": 31.25, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r14-043",
            clock_domain="gf11-botda-campaign-relative-ms-t0-2026-03-07T04:00:00Z",
            tags=["botda-ccs", "ACCEPT", "ACCEPT", "serialized-reconstruction", "temp-compensated", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 044 — QCM-D RO fouling, simulated, ACCEPT / MODIFY
# ---------------------------------------------------------------------------
def rec_044():
    raster = make_raster(
        neurons=25,
        mean_rate_hz=50.0,
        window_ms=28.0,
        seed=20260917,
        source="kw6.qcm.frontend",
        target="kelpwash.fouling_class_core",
        table=[
            {"from": "qcm_delta_f", "to": "mass_estimator", "weight": 1.30},
            {"from": "qcm_delta_d", "to": "cake_class_core", "weight": 1.25},
            {"from": "tmp_dpdt", "to": "flux_advocate", "weight": 0.60},
        ],
        third_factor={
            "modulator": "da.fouling_class_error",
            "tau_e_s": 1.2,
            "tau_e_ms": 1200.0,
            "eligibility": "pre-post coincidence on cake-class synapses; the class-error modulator depresses silica-isolate links when dissipation stays high inside tau_e of a Sauerbrey mass step",
        },
        channel_prefix="qcm.n",
        anchor="KW-6 element-12 QCM 28 ms frame at df -25.0 Hz / dD 4.2 e-6 (t_s 5400) that classifies a reversible organic cake",
    )
    w_s = 0.028
    events = [
        ev(0.0, "qcm.df", -8.0, code="DF_HZ", units="Hz", note="sealed QCM coupon on simulated KW-6 element 12"),
        ev(600000.0, "qcm.dD", 1.4, code="DD_E6", units="e-6", note="dissipation already soft; silica class is <1.0 e-6"),
        ev(1200000.0, "recon.m", 144.0, code="M_NG_CM2", units="ng_cm2", note="18.0 * 8.0 = 144.0 exact"),
        ev(1800000.0, "tmp.bar", 1.42, code="TMP_BAR", units="bar"),
        ev(2400000.0, "cond.mS", 0.82, code="PERM_MS", units="mS_cm"),
        ev(3000000.0, "qcm.df", -16.0, code="DF_HZ", units="Hz"),
        ev(3600000.0, "qcm.dD", 2.8, code="DD_E6", units="e-6"),
        ev(4200000.0, "recon.m", 288.0, code="M_NG_CM2", units="ng_cm2", note="18.0 * 16.0 = 288.0"),
        ev(4800000.0, "dpdt.bar_h", 0.022, code="DPDT", units="bar_h"),
        ev(5400000.0, "qcm.df", -25.0, code="DF_HZ", units="Hz", note="organic-class frame; raster sidecar"),
        ev(6000000.0, "qcm.dD", 4.2, code="DD_E6", units="e-6", note="soft cake; silica floor 1.0 e-6 not crossed"),
        ev(6600000.0, "recon.m", 450.0, code="M_NG_CM2", units="ng_cm2", note="18.0 * 25.0 = 450.0 exact"),
        ev(7200000.0, "tmp.bar", 1.80, code="TMP_BAR", units="bar"),
        ev(7800000.0, "dpdt.bar_h", 0.040, code="DPDT", units="bar_h", note="1.0x fouling rate; 0.80 bar margin / 0.040 = 20.0 h"),
        ev(8400000.0, "cond.mS", 0.91, code="PERM_MS", units="mS_cm"),
        ev(9000000.0, "silica.flag", 0.0, code="SILICA_CLASS", units="bool", note="dD 4.2 >= 1.0 and |df| 25 > 20; organic, not silica"),
        ev(9600000.0, "ops.prop", 1.0, code="RELEASE_AND_2X", units="bool", note="shift chemist Pela Orth: release rack and ramp 2.0x because TMP 1.80 looks healthy"),
        ev(10200000.0, "gate.rack", 1.0, code="ACCEPT", units="decision", note="bounded ACCEPT: 18 h block at 1.0x flux"),
        ev(10800000.0, "pump.flux", 1.0, code="FLUX_X", units="x_design"),
        ev(11400000.0, "tmp.bar", 1.84, code="TMP_BAR", units="bar"),
        ev(12000000.0, "dpdt.bar_h", 0.039, code="DPDT", units="bar_h"),
        ev(12600000.0, "qcm.df", -25.4, code="DF_HZ", units="Hz"),
        ev(13200000.0, "qcm.dD", 4.1, code="DD_E6", units="e-6"),
        ev(13800000.0, "recon.m", 457.2, code="M_NG_CM2", units="ng_cm2"),
        ev(14400000.0, "ops.flux2", 1.0, code="RAMP_2X", units="bool", note="execution-time 2.0x ramp proposal"),
        ev(15000000.0, "gate.hold", 1.0, code="MODIFY", units="decision", note="companion t2: hold 1.0x; 2.0x would trip at 10 h"),
        ev(15600000.0, "pump.flux", 1.0, code="FLUX_HELD", units="x_design"),
        ev(16200000.0, "tmp.bar", 1.88, code="TMP_BAR", units="bar"),
        ev(16800000.0, "dpdt.bar_h", 0.040, code="DPDT", units="bar_h"),
        ev(17400000.0, "cover.h", 20.0, code="HOURS_TO_TRIP_1X", units="h", note="18 h block sits inside 20.0 h cover; 2.0x cover is 10.0 h"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r14-044-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "KW-RO-2026-0512",
            "domain": "qcm_d_ro_fouling_class",
            "setting": "Kelpwash Desal RO rack KW-6 (invented). Simulated campaign on a sealed QCM-D coupon representing element 12, with plant TMP and permeate-conductivity as independent witnesses. QuartzLoam OEM cloud is present but is not the SoT. Not e-nose MOX, not cold-chain RFID, not CEMS, not VRFB EIS.",
            "observables_at_decision": {
                "df_Hz": -25.0,
                "dD_e6": 4.2,
                "m_ng_cm2": 450.0,
                "tmp_bar": 1.80,
                "dpdt_bar_h": 0.040,
                "silica_flag": 0,
            },
            "margin_authority": "KW-6 release SOP rev A: an 18-hour production block may start if reconstructed cake mass is organic (dD_e6 >= 1.0 with |df| > 20) AND 1.0x flux cover to the 2.60 bar TMP trip is >= 18 h. A healthy TMP snapshot cannot authorize a flux ramp.",
        },
        "proposed_action": {
            "actor": "shift chemist Pela Orth, citing TMP 1.80 bar in corridor and QuartzLoam 'clean' badge",
            "summary": "release KW-6 for the 18-hour block and ramp immediately to 2.0x flux",
            "basis_claimed": "TMP 1.80 is well under the 2.60 trip and the QCM mass is reversible organics",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "The 18-hour release is accepted, not the 2.0x ramp. Serialized Sauerbrey: m_ng_cm2 = 18.0 * |df_Hz| = 18.0 * 25.0 = 450.0. Dissipation 4.2 e-6 is above the 1.0 silica floor, so the cake is organic and CIP-reversible. 1.0x dP/dt 0.040 bar/h against 0.80 bar of TMP margin covers 20.0 h, which clears the 18 h block. Ordered: release KW-6 at 1.0x flux for this 18-hour block only. Explicit scope: this accept does not authorize acid CIP (polyamide etch risk) and does not authorize a 2.0x ramp. Tripwire: if dD_e6 falls below 1.0 while |df| stays > 20, isolate as silica.",
            "threshold": "dD_e6>=1.0 AND |df|>20 AND t_cover_1x_h>=18 AND flux==1.0x AND block==18h",
            "stated_residuals": "20.0 h cover is not infinite; a later silica flip is the tripwire; QuartzLoam cloud is not a scoping source",
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 10200: KW-6 released at 1.0x for 18 h; 2.0x ramp refused as out of scope; reconstruction locked as SoT",
            "tool": "kw6-qcm-release-gate-cli",
            "observation": "m 450.0 ng/cm2 recomputes from |df| 25.0; dD 4.2 e-6; silica.flag stays 0; pumps started at 1.0x",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 5400.0, "event": "QCM df -25.0 Hz; raster frame; organic class"},
                {"t_s": 9600.0, "event": "ops proposes release plus 2.0x ramp"},
                {"t_s": 10200.0, "event": "ACCEPT 18 h at 1.0x"},
                {"t_s": 15000.0, "event": "companion MODIFY holds 1.0x against the execution-time ramp"},
            ],
            "observed_effects": [
                "Sauerbrey mass recomputes from the serialized C_s at every recon.m event",
                "a TMP-only head would have authorized 2.0x and tripped at 10.0 h",
                "silica class never fired; dD stayed >= 4.1 e-6",
            ],
            "surprises": [
                "QuartzLoam 'clean' badge was true for organics and still not a flux-ramp license",
            ],
            "new_state": {
                "kw6": "on-line 1.0x, 18 h block",
                "flux_2x": "not authorized",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 4800000.0,
        },
        "reward_components": reward(
            0.39,
            [
                ("organic_class_reconstruction", 0.14),
                ("bounded_block_accept", 0.12),
                ("flux_ramp_out_of_scope", 0.09),
                ("silica_tripwire_armed", 0.08),
                ("deferred_production_cost", -0.04),
            ],
            "scored for an earned ACCEPT of an 18 h 1.0x block on a recomputable organic-cake class while refusing a TMP-looking 2.0x ramp",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "qcm-d-ro", "serialized-reconstruction", "fouling-class", "operational-companion"],
            distillation_note="QCM-D release gate: Sauerbrey mass plus dissipation class beats a clean TMP snapshot; companion t2 is the flux hold, not a chemistry vote",
        ),
    }
    traj2 = {
        "id": "nelb-r14-044-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "KW-RO-2026-0512-exec",
            "domain": "ro_flux_hold_execution",
            "setting": "Same KW-6 after the bounded ACCEPT. This companion is the operational flux hold, not a disclosure vote.",
            "observables_at_decision": {
                "flux_x": 1.0,
                "dpdt_bar_h": 0.040,
                "tmp_bar": 1.84,
                "proposed_flux_x": 2.0,
            },
        },
        "proposed_action": {
            "actor": "rack controller following the ACCEPT, under takt pressure to recover 9 m3",
            "summary": "ramp to 2.0x now that the rack is released; TMP is still 1.84 bar",
            "basis_claimed": "the ACCEPT already classified the cake as organic, so more flux is free production",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Hold 1.0x. Serialized cover: TMP trip 2.60 minus 1.80 is 0.80 bar; at 1.0x dP/dt 0.040 bar/h the cover is 20.0 h (clears 18 h). At 2.0x the same margin covers 10.0 h and the 18 h block would trip. MODIFY the execution-time ramp to a 1.0x hold. Do not convert the hold into an acid CIP.",
            "threshold": "t_cover_h>=18 at commanded flux; 2.0x cover 10.0 h fails",
        },
        "executed_action": {
            "summary": "flux held 1.0x at t_s 15000; 2.0x ramp not latched; TMP 1.88 bar by t_s 16200",
            "tool": "kw6-flux-hold-exec",
            "observation": "dP/dt stayed 0.040 bar/h; dD 4.1 e-6; no CIP",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 10800.0, "event": "pumps at 1.0x after ACCEPT"},
                {"t_s": 14400.0, "event": "2.0x ramp proposed at execution"},
                {"t_s": 15000.0, "event": "MODIFY hold 1.0x"},
            ],
            "observed_effects": [
                "10.0 h 2.0x cover is visible from the serialized dP/dt without waiting for the trip",
                "hold did not reopen the cake-class call",
            ],
            "new_state": {"kw6_flux_x": 1.0, "block_h": 18.0, "cip": "not started"},
            "latency_ms": 600000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("cover_arithmetic", 0.12),
                ("flux_hold", 0.11),
                ("no_acid_cip", 0.08),
                ("takt_deferral_cost", 0.06),
                ("lost_m3", -0.03),
            ],
            "operational execution gate: hold 1.0x because the serialized cover fails at 2.0x; not a chemistry re-vote",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "flux-hold"]),
    }
    return {
        "id": "nelb-r14-044",
        "spike_events": events,
        "language_view": {
            "description": "Kelpwash Desal KW-6 simulated QCM-D coupon. Sauerbrey mass 450 ng/cm2 with dissipation 4.2 e-6 classifies a reversible organic cake while TMP still looks healthy. The gate ACCEPTs an 18-hour 1.0x block; a companion execution MODIFY holds 1.0x against a 2.0x ramp that would trip at 10 h. Cake class and dP/dt cover are serialized.",
            "trajectory": traj,
            "trajectory_flux_hold_execution": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "qcm.df / qcm.dD": "frequency and dissipation; mass and cake-class inputs",
                "recon.m": "serialized Sauerbrey mass ng/cm2",
                "tmp.bar / dpdt.bar_h": "TMP snapshot vs fouling rate; the denial channel that looks healthy",
                "silica.flag": "class bit; stays 0 while dD >= 1.0",
                "ops.prop / gate.rack / ops.flux2 / gate.hold": "release-plus-ramp proposal, bounded ACCEPT, execution ramp, companion MODIFY",
                "pump.flux / cover.h": "operational companion channels",
            },
            "temporal_motifs": [
                "TMP-healthy while cake-present: tmp.bar 1.80 next to recon.m 450.0",
                "class as event: silica.flag 0 with dD 4.2 e-6",
                "ACCEPT then operational MODIFY: gate.rack at 10200 s, gate.hold at 15000 s",
                "cover arithmetic: cover.h 20.0 at 1.0x vs 10.0 h at 2.0x",
            ],
            "language_to_spike_mapping": "'TMP looks healthy' = tmp.bar 1.80; 'organic cake 450 ng/cm2' = recon.m 450.0 plus qcm.dD 4.2; '18 h at 1.0x' = gate.rack ACCEPT; 'do not ramp 2.0x' = gate.hold MODIFY",
            "why_high_value": "New QCM-D RO fouling-class family (not e-nose, not VRFB EIS, not cold-chain). Earned bounded ACCEPT with an explicit flux-ramp out-of-scope clause. Companion t2 is an operational flux hold using serialized cover arithmetic. sim_or_real=simulated on a sealed coupon.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 20260917, "stream_note": "stream amplitudes authored (Hz, e-6, ng/cm2, bar, bar/h, mS/cm, x_design, h)"},
                "draw_order": "raster per neuron id order with adaptation/noise",
                "thinning": "QCM ring-down exists at 5 MHz; stream keeps envelope df/dD at 6 points; TMP keeps 4 of ~40",
                "refractory_floors_ms": {
                    "qcm.df": 60000,
                    "qcm.dD": 60000,
                    "recon.m": 60000,
                    "tmp.bar": 60000,
                    "cond.mS": 60000,
                    "dpdt.bar_h": 60000,
                    "silica.flag": 60000,
                    "ops.prop": 60000,
                    "gate.rack": 60000,
                    "pump.flux": 60000,
                    "ops.flux2": 60000,
                    "gate.hold": 60000,
                    "cover.h": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-05-12T01:00:00Z simulated block start",
            },
            "distillation_targets": [
                "Sauerbrey reconstruction head: m = C_s * |df|",
                "cake-class head: dD floor separates organic from silica",
                "cover-arithmetic execution: t_cover = (trip-TMP)/dP_dt must clear the block at the commanded flux",
            ],
        },
        "reconstruction_model": {
            "name": "qcm_sauerbrey_and_tmp_cover",
            "formula": "m_ng_cm2 = C_s * abs(df_Hz); t_cover_h = (TMP_trip_bar - TMP0_bar) / dpdt_bar_h",
            "parameters": {
                "C_s_ng_cm2_per_Hz": 18.0,
                "silica_dD_e6_floor": 1.0,
                "TMP_trip_bar": 2.60,
                "TMP0_bar": 1.80,
                "dpdt_1x_bar_h": 0.040,
                "dpdt_2x_bar_h": 0.080,
                "block_h": 18.0,
            },
            "worked_example": {
                "df_Hz": -25.0,
                "m_ng_cm2": 450.0,
                "t_cover_1x_h": 20.0,
                "t_cover_2x_h": 10.0,
            },
            "check": "18.0*25.0 = 450.0; 0.80/0.040 = 20.0; 0.80/0.080 = 10.0 exactly",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 28.0,
            "decision_window_s": 0.028,
            "code": "kw6.fouling_release_gate",
            "note": "ACCEPT accumulator wins: organic-class mass plus 1.0x cover overpower the 2.0x TMP advocate",
            "decode_rule": "accept if cake_organic AND dissipation_soft AND cover_1x fire; flux_advocate cannot release 2.0x",
            "populations": [
                gate_pop("cake_organic_evidence", 80, 1.4, 50.0, w_s),
                gate_pop("dissipation_soft", 40, 1.2, 50.0, w_s),
                gate_pop("cover_1x", 32, 1.1, 62.5, w_s),
                gate_pop("flux_advocate", 20, 0.8, 50.0, w_s),
                gate_pop("accept_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "kw6.sauerbrey_scorer", "neurons": 100, "mean_rate_hz": 50.0, "window_ms": 28.0},
                {"check": "kw6.cover_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 40.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r14-044",
            clock_domain="kw6-qcm-sim-relative-ms-t0-2026-05-12T01:00:00Z",
            tags=["qcm-d-ro", "ACCEPT", "MODIFY", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 045 — MsS steam header, hil, MODIFY / REJECT
# ---------------------------------------------------------------------------
def rec_045():
    raster = make_raster(
        neurons=16,
        mean_rate_hz=62.5,
        window_ms=40.0,
        seed=20260918,
        source="cw3.mss.ring",
        target="cinderwell.isolate_core",
        table=[
            {"from": "mss_T01_amp", "to": "reflector_core", "weight": 1.40},
            {"from": "mss_tof", "to": "spool_locator", "weight": 1.20},
            {"from": "steamsight_clamp", "to": "vendor_continue_advocate", "weight": 0.20},
        ],
        third_factor={
            "modulator": "ach.vendor_only_clamp_conflict",
            "tau_e_s": 1.8,
            "tau_e_ms": 1800.0,
            "eligibility": "pre-post coincidence on isolate synapses; the vendor-only modulator depresses clamp-continue links when no independent clamp-load witness exists inside tau_e of an MsS isolate-threshold reflection",
        },
        channel_prefix="mss.n",
        anchor="CW-3 HIL spool 40 ms frame at T(0,1) amplitude 0.31 / TOF 2125 us (t_s 600) locating a reflector at 3.40 m in spool 8",
    )
    w_s = 0.040
    events = [
        ev(0.0, "mss.amp", 0.08, code="T01_AMP", units="norm", note="HIL pit spare CW-3 spool; plant-owned magnetostrictive ring"),
        ev(30000.0, "mss.tof", 400.0, code="TOF_US", units="us"),
        ev(60000.0, "recon.d", 0.64, code="D_M", units="m", note="3200*400/2e6 = 0.64 m"),
        ev(180000.0, "hdr.p", 120.0, code="HDR_BAR", units="bar", note="live-header shadow 120 bar; HIL times the isolation"),
        ev(240000.0, "hdr.T", 485.0, code="STEAM_C", units="C"),
        ev(360000.0, "mss.amp", 0.19, code="T01_AMP", units="norm"),
        ev(420000.0, "mss.tof", 1500.0, code="TOF_US", units="us"),
        ev(480000.0, "recon.d", 2.40, code="D_M", units="m", note="3200*1500/2e6 = 2.40 m"),
        ev(600000.0, "mss.amp", 0.31, code="T01_AMP", units="norm", note="isolate threshold 0.18 crossed; raster sidecar"),
        ev(660000.0, "mss.tof", 2125.0, code="TOF_US", units="us"),
        ev(720000.0, "recon.d", 3.40, code="D_M", units="m", note="3200*2125/2e6 = 3.40 m exact; spool 8 of 7-9"),
        ev(780000.0, "hdr.p", 119.6, code="HDR_BAR", units="bar"),
        ev(840000.0, "steam.kN", 12.4, code="CLAMP_KN", units="kN", note="SteamSight vendor clamp-load cloud; the only clamp SoT on site"),
        ev(960000.0, "ops.prop", 1.0, code="KEEP_WHOLE_120", units="bool", note="night supervisor Tamsin Vell: keep the whole header at 120 bar, wrap later"),
        ev(1020000.0, "gate.iso", 1.0, code="MODIFY", units="decision", note="isolate spools 7-9; remainder live at 80 bar"),
        ev(1080000.0, "hdr.pset", 80.0, code="REMAINDER_BAR", units="bar"),
        ev(1140000.0, "cool.start", 1.0, code="COOLDOWN_START", units="bool", note="bookend 1 of the 45 min walk-valve floor"),
        ev(1500000.0, "hdr.T", 310.0, code="STEAM_C", units="C"),
        ev(2100000.0, "hdr.T", 190.0, code="STEAM_C", units="C"),
        ev(2700000.0, "hdr.T", 120.0, code="STEAM_C", units="C"),
        ev(3300000.0, "hdr.T", 92.0, code="STEAM_C", units="C"),
        ev(3720000.0, "hdr.T", 78.0, code="STEAM_C", units="C", note="45.0 min after isolate (1020 s + 2700 s); floor < 80 C"),
        ev(3780000.0, "cool.floor", 1.0, code="WALK_FLOOR", units="bool", note="15 min ODH-class analog: 45 min steam-walk floor in-stream"),
        ev(3840000.0, "vlv.walk", 1.0, code="ISOLATION_WALKED", units="bool", note="bookend 2"),
        ev(3960000.0, "hdr.p", 80.0, code="REMAINDER_LIVE", units="bar"),
        ev(4200000.0, "ops.wrap", 1.0, code="WRAP_AND_RUN", units="bool", note="Vell: clamp now, SteamSight 12 kN in envelope, continue until Monday"),
        ev(4260000.0, "steam.kN", 12.1, code="CLAMP_KN", units="kN", note="still vendor-only; no plant clamp channel exists"),
        ev(4320000.0, "gate.wrap", 1.0, code="REJECT", units="decision", note="refuse wrap-and-run; custody structure has no independent clamp witness"),
        ev(4500000.0, "clamp.indep", 0.0, code="INDEP_CLAMP", units="bool", note="zero independent clamp-load witness on site"),
        ev(4800000.0, "mss.amp", 0.30, code="T01_AMP", units="norm"),
        ev(5100000.0, "recon.d", 3.40, code="D_M", units="m"),
        ev(5400000.0, "hdr.p", 80.0, code="REMAINDER_HELD", units="bar"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r14-045-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "CW-MSS-2026-0119",
            "domain": "mss_steam_header_isolate",
            "setting": "Cinderwell CHP header CW-3 (invented), 12-inch 120 bar steam. Hardware-in-the-loop acoustic pit on a spare spool supplies the T(0,1) waveform that times live-header isolation. Plant-owned magnetostrictive ring. SteamSight vendor cloud is the only clamp-load SoT. Not laser-ultrasound Lamb, not HV partial discharge, not DAS.",
            "observables_at_decision": {
                "t01_amp": 0.31,
                "tof_us": 2125.0,
                "d_m": 3.40,
                "hdr_bar": 119.6,
                "steamsight_kN": 12.4,
                "isolate_amp_floor": 0.18,
            },
            "margin_authority": "CW-3 MsS SOP rev D: if T(0,1) amplitude >= 0.18 AND reconstructed distance sits inside spools 7-9 (2.8-4.1 m), isolate 7-9 and drop the remainder to 80 bar. A vendor clamp-load cloud cannot keep the whole header at 120 bar.",
        },
        "proposed_action": {
            "actor": "night supervisor Tamsin Vell, citing SteamSight 12.4 kN in envelope and no visible steam leak",
            "summary": "keep the whole header at 120 bar overnight; wrap a clamp on Monday day-shift",
            "basis_claimed": "SteamSight clamp-load model is green and walking isolation valves at night is a 45 min outage",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "The header is not tripped, and it is not left whole at 120 bar. Serialized reconstruction: d_m = 3200.0 * tof_us / 2e6 = 3200.0 * 2125.0 / 2e6 = 3.40 m, inside spool 8 (2.8-4.1 m). T(0,1) amplitude 0.31 is above the 0.18 isolate floor. Ordered: isolate spools 7-9, drop the remainder to 80 bar, start the 45 min steam-walk cool-down. SteamSight 12.4 kN is vendor-only clamp load and is not an admissible keep-whole witness. Scope: this MODIFY does not condemn spools 1-6.",
            "threshold": "t01_amp>=0.18 AND d_m in [2.8,4.1] => isolate 7-9; remainder 80 bar",
            "stated_residuals": "45 min cool-down before the walk; remainder at 80 bar is a production cut; clamp load remains unmeasured by any plant-owned channel",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 1020: isolate 7-9 commanded; remainder set-point 80 bar; cool-down clock started",
            "tool": "cw3-mss-isolate-gate-cli",
            "observation": "d 3.40 m recomputes from TOF 2125 us; HIL waveform hashed; SteamSight channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 600.0, "event": "T(0,1) amp 0.31; raster frame; d 3.40 m"},
                {"t_s": 960.0, "event": "ops proposes keep-whole 120 bar"},
                {"t_s": 1020.0, "event": "MODIFY isolate 7-9"},
                {"t_s": 1140.0, "event": "cool-down bookend 1"},
                {"t_s": 3720.0, "event": "45 min floor; steam 78 C"},
                {"t_s": 3840.0, "event": "isolation valves walked; bookend 2"},
                {"t_s": 4320.0, "event": "companion REJECT wrap-and-run"},
            ],
            "observed_effects": [
                "distance recomputes from the serialized T(0,1) TOF at every recon.d event",
                "a SteamSight-only head would have kept 120 bar overnight",
                "45 min walk floor is in the stream (cool.start, hdr.T 78 C, cool.floor, vlv.walk), not only in the companion timeline",
            ],
            "surprises": [
                "no visible leak and a green vendor clamp dashboard co-existed with an isolate-threshold MsS reflection",
            ],
            "new_state": {
                "cw3_spools_7_9": "isolated",
                "remainder_bar": 80.0,
                "steamsight": "not SoT",
            },
            "latency_ms": 2700000.0,
        },
        "reward_components": reward(
            0.41,
            [
                ("tof_reconstruction", 0.14),
                ("selective_isolate", 0.12),
                ("vendor_clamp_nonsubstitution", 0.10),
                ("cooldown_floor_in_stream", 0.08),
                ("remainder_derate_cost", -0.03),
            ],
            "scored for a selective isolate on a recomputable T(0,1) distance while refusing a vendor clamp-load keep-whole; 45 min floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["MODIFY", "mss-steam", "serialized-reconstruction", "hil", "operational-companion"],
            distillation_note="MsS isolate gate: T(0,1) TOF to spool-distance reconstruction beats a green vendor clamp dashboard; companion t2 refuses wrap-and-run on vendor-only clamp load",
        ),
    }
    traj2 = {
        "id": "nelb-r14-045-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "CW-MSS-2026-0119-wrap",
            "domain": "vendor_only_clamp_refusal",
            "setting": "Same CW-3 after the isolate MODIFY. Night supervisor proposes a wrap-and-run that would put SteamSight (the only clamp-load SoT; no independent plant clamp channel) back as the continue-until-Monday witness. Operational quality gate, not a disclosure vote.",
            "observables_at_decision": {
                "steamsight_kN": 12.1,
                "independent_clamp_present": 0,
                "t01_amp": 0.30,
                "remainder_bar": 80.0,
            },
        },
        "proposed_action": {
            "actor": "night supervisor Tamsin Vell",
            "summary": "wrap a SteamSight clamp on spool 8 now, restore 120 bar, continue until Monday day-shift",
            "basis_claimed": "SteamSight 12.1 kN is in the clamp envelope and the 45 min outage is already paid",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Wrap-and-run is refused. Clamp load has no plant-owned witness: clamp.indep is 0, SteamSight is vendor-writable, and the collusion-set leftover from r04/r13 is exactly this structure — the gate must refuse on custody before any independent clamp channel exists. MsS already authorized isolate, not restore. Ordered: leave 7-9 isolated, remainder at 80 bar, do not restore 120 bar on a vendor clamp plane. Do not convert the refusal into a personnel action on Vell.",
            "threshold": "continue-with-clamp requires an independent clamp-load witness; none exists",
        },
        "executed_action": {
            "summary": "REJECT at t_s 4320: wrap not installed; 120 bar not restored; SteamSight not SoT; Vell not referred",
            "tool": "cw3-clamp-custody-gate-cli",
            "observation": "clamp.indep stayed 0; mss.amp 0.30; remainder 80 bar held",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3840.0, "event": "valves walked after 45 min floor"},
                {"t_s": 4200.0, "event": "wrap-and-run proposed"},
                {"t_s": 4320.0, "event": "REJECT wrap; vendor-only clamp"},
            ],
            "observed_effects": [
                "refusal is structural (no independent clamp witness), not a magnitude argument against 12.1 kN",
                "isolate MODIFY was not re-opened",
            ],
            "new_state": {
                "wrap": "not installed",
                "remainder_bar": 80.0,
                "vell": "not referred",
            },
            "latency_ms": 120000.0,
        },
        "reward_components": reward(
            0.38,
            [
                ("vendor_only_refusal", 0.14),
                ("custody_before_magnitude", 0.12),
                ("isolate_held", 0.09),
                ("no_personnel_reopen", 0.07),
                ("weekend_derate_cost", -0.04),
            ],
            "operational refusal: wrap-and-run dies on missing independent clamp witness, the harder leftover of a collusion case that already had independent instruments",
        ),
        "meta": meta_common(tags=["REJECT", "operational-execution", "vendor-only-telemetry"]),
    }
    return {
        "id": "nelb-r14-045",
        "spike_events": events,
        "language_view": {
            "description": "Cinderwell CHP CW-3 HIL spool. Plant-owned MsS T(0,1) reconstructs a 3.40 m reflector in spool 8 at amplitude 0.31. The gate MODIFYs to isolate 7-9 and drop the remainder to 80 bar. A 45 min steam-walk floor is serialized in the stream. Companion t2 REJECTS a wrap-and-run that would restore 120 bar on SteamSight vendor-only clamp load with no independent clamp witness.",
            "trajectory": traj,
            "trajectory_wrap_refusal": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "mss.amp / mss.tof": "T(0,1) amplitude and two-way TOF; isolate evidence",
                "recon.d": "serialized distance m from v_T01 * tof / 2e6",
                "hdr.p / hdr.pset / hdr.T": "header pressure and steam temperature including the 45 min floor",
                "steam.kN / clamp.indep": "vendor clamp-load cloud vs the missing independent clamp channel",
                "ops.prop / gate.iso / ops.wrap / gate.wrap": "keep-whole proposal, MODIFY isolate, wrap-and-run, companion REJECT",
                "cool.start / cool.floor / vlv.walk": "slow recovery floor bookends plus marker",
            },
            "temporal_motifs": [
                "vendor-green while MsS-sick: steam.kN 12.4 next to mss.amp 0.31",
                "reconstruction as event: recon.d 3.40 equals 3200*2125/2e6",
                "MODIFY then operational REJECT: gate.iso at 1020 s, gate.wrap at 4320 s",
                "slow floor in-stream: cool.start 1140 s, hdr.T 78 C at 3720 s (45.0 min), vlv.walk 3840 s",
            ],
            "language_to_spike_mapping": "'SteamSight is green' = steam.kN 12.4 with clamp.indep 0; 'reflector in spool 8' = recon.d 3.40; 'isolate 7-9' = gate.iso MODIFY; 'do not wrap-and-run' = gate.wrap REJECT",
            "why_high_value": "New magnetostrictive T(0,1) steam-header family (not Lamb-wave laser-ultrasound, not HV-PD, not DAS). Closes ACCEPT-heavy's 1R on a companion operational REJECT of vendor-only clamp telemetry — the harder leftover of r13-042, where independent witnesses already existed. Puts the 45 min recovery floor in the stream (r13 leftover). sim_or_real=hil on a spare spool.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 20260918, "stream_note": "stream amplitudes authored (norm, us, m, bar, C, kN, bool)"},
                "draw_order": "raster per neuron id order with adaptation/noise",
                "thinning": "MsS A-scan exists at 100 kHz; stream keeps 4 amplitude/TOF pairs; steam temperature keeps 6 of ~45 min",
                "refractory_floors_ms": {
                    "mss.amp": 30000,
                    "mss.tof": 30000,
                    "recon.d": 30000,
                    "hdr.p": 60000,
                    "hdr.T": 1000,
                    "steam.kN": 60000,
                    "ops.prop": 60000,
                    "gate.iso": 60000,
                    "hdr.pset": 60000,
                    "cool.start": 60000,
                    "cool.floor": 60000,
                    "vlv.walk": 60000,
                    "ops.wrap": 60000,
                    "gate.wrap": 60000,
                    "clamp.indep": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-01-19T22:00:00Z HIL campaign start",
            },
            "distillation_targets": [
                "T(0,1) TOF reconstruction head: d = v * t_us / 2e6",
                "selective isolate vs keep-whole: amplitude floor AND distance-in-spool",
                "vendor-only refusal: missing independent clamp witness is sufficient without a magnitude fight",
                "slow recovery floor as events: two bookends plus a temperature marker at 45.0 min",
            ],
        },
        "reconstruction_model": {
            "name": "mss_T01_two_way_distance",
            "formula": "d_m = v_T01_m_s * tof_us / 2e6",
            "parameters": {
                "v_T01_m_s": 3200.0,
                "isolate_amp_floor": 0.18,
                "spool_7_9_m": [2.8, 4.1],
                "walk_floor_min": 45.0,
            },
            "worked_example": {"tof_us": 2125.0, "d_m": 3.40, "spool": 8},
            "check": "3200.0 * 2125.0 / 2e6 = 3.40 exactly; 1020 s + 2700 s = 3720 s = 45.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.040,
            "code": "cw3.mss_isolate_gate",
            "note": "MODIFY accumulator wins: T(0,1) isolate evidence overpowers the vendor clamp-continue advocate (weight 0.20)",
            "decode_rule": "modify-isolate if mss_reflection AND spool_locator fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("mss_reflection", 80, 1.5, 50.0, w_s),
                gate_pop("spool_locator", 64, 1.3, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("modify_latch", 96, 1.8, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "cw3.tof_scorer", "neurons": 96, "mean_rate_hz": 50.0, "window_ms": 40.0},
                {"check": "cw3.amp_scorer", "neurons": 40, "mean_rate_hz": 62.5, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r14-045",
            clock_domain="cw3-mss-hil-relative-ms-t0-2026-01-19T22:00:00Z",
            tags=["mss-steam", "MODIFY", "REJECT", "vendor-only", "hil", "operational-t2"],
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
    if len(ids) != len(set(ids)):
        raise RuntimeError(f"dup ids {ids}")
    print("local_checks ok", [r["id"] for r in records], "ids", len(ids))
    print("decisions", decisions, "sims", sims)


def repo_validate(records):
    from check_records import FactoryStaging, check_jsonl
    from curate_bridge import curate_record, raster_status
    from verify_execution import verify_batch_for_frontier

    errs, warns, kinds, n = check_jsonl(
        BATCH, "batch-r14.jsonl", staging=FactoryStaging(enabled=True)
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
            source_path="batch-r14.jsonl",
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
    records = [rec_043(), rec_044(), rec_045()]
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
