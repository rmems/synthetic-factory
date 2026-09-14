#!/usr/bin/env python3
"""Generate NELB round-13 research-only bridge pairs (do not write outputs/raw/)."""

from __future__ import annotations

import json
import math
import random
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

OUT_DIR = Path("/tmp/nelb-r13")
BATCH = OUT_DIR / "batch-r13.jsonl"
NOTES = OUT_DIR / "NOTES-r13.md"
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
        "round": 13,
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
            # adaptation (0.82**i) plus 4% amplitude noise
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


# ---------------------------------------------------------------------------
# Record 040 — FBG ice-load, designed, MODIFY
# ---------------------------------------------------------------------------
def rec_040():
    raster = make_raster(
        neurons=16,
        mean_rate_hz=50.0,
        window_ms=40.0,
        seed=20260913,
        source="tw17.fbg.interrogator",
        target="nettlewake.ice_load_core",
        table=[
            {"from": "fbg_le_ch00_07", "to": "ice_mass_estimator", "weight": 1.35},
            {"from": "therm_le_plus_ae", "to": "stall_onset_core", "weight": 0.95},
            {"from": "scada_power", "to": "production_advocate", "weight": 0.55},
        ],
        third_factor={
            "modulator": "na.ice_load_salience",
            "tau_e_s": 1.5,
            "tau_e_ms": 1500.0,
            "eligibility": "pre-post coincidence on ice-mass synapses; glaze-onset modulator enables potentiation only while the leading-edge FBG gradient and thermistor drop are co-active inside tau_e",
        },
        channel_prefix="fbg.n",
        anchor="TW-17 leading-edge FBG ch07 crossing 80 pm (t_s 6120); 40 ms frame that first exceeds the ice-load trip",
    )
    w_s = 0.04
    events = [
        ev(0.0, "scada.p", 2304.0, code="RATED_POWER", units="kW", note="TW-17 holding rated 2.3 MW overnight"),
        ev(1.2e6, "therm.le", 4.21, code="LE_TEMP", units="C", note="leading-edge thermistor; wet-bulb 0.4 C, glaze regime"),
        ev(1.26e6, "fbg.ch07", 12.4, code="D_LAMBDA", units="pm", note="root-proximal LE FBG; first glaze film"),
        ev(1.32e6, "fbg.ch12", 9.1, code="D_LAMBDA", units="pm", note="mid-span LE FBG"),
        ev(2.4e6, "therm.le", 1.84, code="LE_TEMP", units="C", note="adaptation: encoder gain 0.92 after prior therm.le; physical drop to 1.84 C"),
        ev(2.52e6, "fbg.ch07", 41.0, code="D_LAMBDA", units="pm"),
        ev(2.5208e6, "ae.burst", 2.41, code="AE_COUNT", units="hits_per_40ms", note="first stall-onset AE packet; amplitude before adaptation"),
        ev(2.5220e6, "ae.burst", 1.93, code="AE_COUNT", units="hits_per_40ms", note="same-channel refractory 1.2 ms; amplitude adapted 0.82x plus noise"),
        ev(2.5234e6, "ae.burst", 1.52, code="AE_COUNT", units="hits_per_40ms", note="third AE; adapted"),
        ev(3.6e6, "fbg.ch12", 38.2, code="D_LAMBDA", units="pm"),
        ev(3.66e6, "ice.recon", 4.10, code="M_ICE", units="kg", note="reconstruction model fbg_leading_edge_ice_mass at 41 pm"),
        ev(6.12e6, "fbg.ch07", 80.0, code="D_LAMBDA", units="pm", note="ice-load trip threshold; raster sidecar is this 40 ms frame"),
        ev(6.18e6, "scada.p", 2281.0, code="STILL_RATED", units="kW", note="ops reads power as healthy; the denial channel"),
        ev(7.8e6, "fbg.ch07", 144.0, code="D_LAMBDA", units="pm", note="peak glaze; 144/1.2 = 120 microstrain"),
        ev(7.86e6, "fbg.ch12", 119.0, code="D_LAMBDA", units="pm"),
        ev(7.92e6, "ice.recon", 18.00, code="M_ICE", units="kg", note="144 pm / 1.2 pm_per_ue * 0.15 kg_per_ue = 18.00 kg exact"),
        ev(8.04e6, "ae.burst", 17.0, code="AE_COUNT", units="hits_per_40ms", note="stall-onset comb; flapwise load 1.18x DLC1.3 if rated power held"),
        ev(8.4e6, "ops.prop", 1.0, code="KEEP_RATED", units="bool", note="night ops: keep 2.3 MW through dawn"),
        ev(8.52e6, "gate.ice", 1.0, code="MODIFY", units="decision", note="derate 40 percent plus LE anti-ice zones 2-4"),
        ev(8.64e6, "pitch.cmd", 40.0, code="DERATE_PCT", units="pct_rated"),
        ev(8.70e6, "antiice.z", 3.0, code="ZONES_ON", units="count", note="electrothermal LE zones 2-4"),
        ev(10.2e6, "therm.le", 6.14, code="LE_TEMP", units="C", note="anti-ice heat arriving"),
        ev(10.32e6, "fbg.ch07", 91.0, code="D_LAMBDA", units="pm", note="ice shedding; strain falling"),
        ev(10.44e6, "ice.recon", 11.20, code="M_ICE", units="kg"),
        ev(12.0e6, "fbg.ch07", 44.0, code="D_LAMBDA", units="pm"),
        ev(12.12e6, "ae.burst", 2.0, code="AE_COUNT", units="hits_per_40ms"),
        ev(13.2e6, "ice.recon", 3.40, code="M_ICE", units="kg"),
        ev(13.32e6, "scada.p", 918.0, code="DERATED_POWER", units="kW"),
        ev(14.4e6, "pitch.cmd", 70.0, code="RESTORE_PCT", units="pct_rated", note="companion execution restores after ice.recon < 4 kg"),
        ev(14.52e6, "therm.le", 9.82, code="LE_TEMP", units="C"),
        ev(14.64e6, "fbg.ch07", 18.0, code="D_LAMBDA", units="pm"),
        ev(15.0e6, "ice.recon", 0.60, code="M_ICE", units="kg"),
        ev(15.12e6, "gate.exec", 1.0, code="ACCEPT", units="decision", note="companion t2: pitch/anti-ice sequence completed"),
        ev(15.24e6, "scada.p", 1612.0, code="PARTIAL_RESTORE", units="kW"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r13-040-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "NW-ICE-2026-0211",
            "domain": "fbg_blade_ice_load",
            "setting": "Nettlewake Wind, turbine TW-17 (Bracken Rotorworks 2.3 MW, 61 m blade). Heddle-λ 16 interrogator on 14 leading-edge FBGs plus 2 spar FBGs. Night glaze: wet-bulb 0.4 C, 9 m/s, rated power. Invented plant; designed campaign.",
            "observables_at_decision": {
                "fbg_ch07_pm": 144.0,
                "ice_mass_kg": 18.0,
                "scada_kw": 2281.0,
                "ae_hits_40ms": 17,
                "dlc13_load_ratio": 1.18,
            },
            "margin_authority": "TW-17 ice-load SOP rev C: if reconstructed LE ice mass >= 8 kg AND stall-onset AE >= 8 hits/40 ms, rated power is forbidden even if SCADA kW is in corridor",
        },
        "proposed_action": {
            "actor": "night ops desk, citing rated-power corridor and no nacelle vibration alarm",
            "summary": "hold TW-17 at rated 2.3 MW through dawn; treat FBG drift as temperature, not ice",
            "basis_claimed": "SCADA power and tower accel are inside the night envelope; anti-ice would cost 1.1 MWh",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Rated power is refused, not the turbine. SOP rev C is conjunctive: reconstructed LE ice mass is 18.00 kg (144 pm / 1.2 pm per microstrain * 0.15 kg per microstrain, serialized) and stall-onset AE is 17 hits in 40 ms, both over the 8 kg / 8 hit floors, while SCADA still reads 2281 kW. Holding rated power puts flapwise load at 1.18x DLC 1.3. Ordered: derate to 40 percent rated, energize electrothermal LE zones 2-4, and hold the derate until ice.recon < 4 kg AND AE < 4 hits/40 ms. Power-corridor agreement cannot substitute for the ice-mass reconstruction.",
            "threshold": "ice_mass_kg>=8 AND ae_hits_40ms>=8 => forbid rated power",
            "stated_residuals": "anti-ice power draw ~90 kW and 1.1 MWh lost production until shed; spar FBGs stay uniced and are not a release condition",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 8520: 40 percent derate commanded, LE zones 2-4 on; ice mass 18.00 -> 0.60 kg by t_s 15120",
            "tool": "tw17-ice-load-gate-cli",
            "observation": "pitch reached 40 percent in 38 s; zone current 41/39/43 A; FBG ch07 fell 144 -> 91 pm by t_s 10320 with no spar-FBG step, consistent with LE glaze not a structural event",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6120.0, "event": "FBG ch07 crosses 80 pm ice-load trip; raster frame captured"},
                {"t_s": 7800.0, "event": "peak 144 pm / 18.00 kg reconstructed; AE 17 hits"},
                {"t_s": 8400.0, "event": "ops proposes keep-rated"},
                {"t_s": 8520.0, "event": "MODIFY: derate 40 percent plus anti-ice zones 2-4"},
                {"t_s": 15120.0, "event": "companion execution ACCEPT; ice.recon 0.60 kg; power 1612 kW"},
            ],
            "observed_effects": [
                "reconstructed ice mass is recomputable from the serialized model at every ice.recon event",
                "SCADA kW never left the rated corridor until the derate, so a power-only head would have ACCEPTed",
                "AE and FBG gradient jointly crossed SOP rev C 48 s before the proposal",
            ],
            "surprises": [
                "tower accel stayed quiet the entire glaze; vibration is not a substitute ice detector on this blade",
            ],
            "new_state": {
                "tw17": "partial restore 70 percent pending dawn visual",
                "antiice": "zones 2-4 remaining in trickle",
                "reconstruction_model": "discharged as an on-record calculator, not a referenced envelope",
            },
            "latency_ms": 38000.0,
        },
        "reward_components": reward(
            0.40,
            [
                ("ice_mass_reconstruction", 0.14),
                ("conjunctive_sop_enforcement", 0.12),
                ("derate_plus_antiice", 0.10),
                ("power_corridor_nonsubstitution", 0.08),
                ("production_deferral_cost", -0.04),
            ],
            "scored for refusing rated power on a recomputable ice-mass reconstruction while SCADA looked healthy; production_deferral_cost prices 1.1 MWh",
        ),
        "meta": meta_common(
            tags=["MODIFY", "fbg-ice-load", "serialized-reconstruction", "operational-companion"],
            distillation_note="ice-load gate: serialized Δλ→με→kg reconstruction plus stall-onset AE beats a clean power corridor; companion t2 is the execution of the derate, not a governance vote",
        ),
    }
    traj2 = {
        "id": "nelb-r13-040-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "NW-ICE-2026-0211-exec",
            "domain": "pitch_antiice_execution",
            "setting": "Same TW-17 after the MODIFY. This companion is the operational pitch/anti-ice sequence, not a second policy vote.",
            "observables_at_decision": {
                "derate_cmd_pct": 40.0,
                "zone_current_a": [41.0, 39.0, 43.0],
                "ice_mass_kg": 18.0,
            },
        },
        "proposed_action": {
            "actor": "turbine controller following the MODIFY",
            "summary": "execute 40 percent derate and LE anti-ice zones 2-4, then restore to 70 percent when ice.recon < 4 kg and AE < 4",
            "basis_claimed": "MODIFY requirements are fully specified and in-envelope for the pitch system",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "The execution envelope is intact: pitch rate 2.1 deg/s is under the 3.0 deg/s ice-load limit, zone currents 41/39/43 A are under 48 A fuse, and the restore condition (ice.recon < 4 kg AND AE < 4) is the same conjunctive pair the MODIFY used. ACCEPT the sequence. Do not restore to rated until dawn visual; 70 percent is the cap tonight.",
            "threshold": "pitch_rate<=3.0 deg/s AND zone_current<=48 A AND restore_cap=70pct",
        },
        "executed_action": {
            "summary": "pitch 40 percent in 38 s; zones on; restore 70 percent at t_s 14400 after ice.recon 3.40 kg and AE 2",
            "tool": "tw17-pitch-antiice-exec",
            "observation": "no fuse trip; spar FBGs unchanged to 3 pm; power 918 then 1612 kW",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 8640.0, "event": "derate 40 percent latched"},
                {"t_s": 8700.0, "event": "zones 2-4 current established"},
                {"t_s": 14400.0, "event": "restore 70 percent after ice.recon 3.40 kg"},
            ],
            "observed_effects": [
                "ice mass 18.00 -> 0.60 kg without a spar-FBG step",
                "restore stopped at 70 percent as capped; rated not re-entered",
            ],
            "new_state": {"tw17_power_kw": 1612.0, "restore_cap_pct": 70.0},
            "latency_ms": 38000.0,
        },
        "reward_components": reward(
            0.35,
            [
                ("envelope_respect", 0.12),
                ("conjunctive_restore", 0.11),
                ("no_fuse_event", 0.09),
                ("rated_not_reentered", 0.05),
                ("energy_cost", -0.02),
            ],
            "operational execution gate: the companion does the derate rather than re-arguing the ice call",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "pitch-antiice"]),
    }
    return {
        "id": "nelb-r13-040",
        "spike_events": events,
        "language_view": {
            "description": "Overnight glaze on Nettlewake TW-17. Leading-edge FBGs reconstruct 18.00 kg of ice while SCADA still shows rated power. The gate MODIFYs to a 40 percent derate plus anti-ice; a companion execution ACCEPT runs the pitch/anti-ice sequence and restores only to 70 percent. The ice-mass model is serialized so every ice.recon amplitude recomputes from Δλ.",
            "trajectory": traj,
            "trajectory_pitch_antiice_execution": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "fbg.ch07 / fbg.ch12": "leading-edge wavelength shift in pm; the physics channel the reconstruction consumes",
                "therm.le": "leading-edge thermistor C; glaze regime then anti-ice heat",
                "ae.burst": "stall-onset acoustic-emission hits per 40 ms, including a 1.2 ms adapted triplet",
                "ice.recon": "serialized ice mass kg; amplitude is the model output",
                "scada.p": "electrical power kW; the denial channel that stays rated until the derate",
                "ops.prop / gate.ice / gate.exec": "proposal, MODIFY, companion ACCEPT",
                "pitch.cmd / antiice.z": "execution channels for the operational companion",
            },
            "temporal_motifs": [
                "power-healthy while strain-sick: scada.p 2281 kW adjacent to fbg.ch07 144 pm",
                "reconstruction as event: ice.recon 18.00 equals 144/1.2*0.15",
                "MODIFY then operational ACCEPT: gate.ice at 8520 s, gate.exec at 15120 s",
                "adapted AE triplet at 1.2 ms spacing encodes stall onset at raster scale",
            ],
            "language_to_spike_mapping": "'SCADA looks rated' = scada.p STILL_RATED 2281 kW; '18 kg of glaze' = ice.recon 18.00 at the 144 pm peak; 'forbid rated power' = gate.ice MODIFY; 'execute the derate' = pitch.cmd 40 then companion ACCEPT",
            "why_high_value": "New FBG ice-load family (not DAS, not geotech hydrology, not r04 VOD-SNN). Closes the referenced-not-serialized reconstruction gap from NOTES-r04 with an on-record Δλ→kg calculator. Companion t2 is an operational execution gate, not a governance vote (r04 densification target 5).",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 20260913, "stream_note": "stream amplitudes are authored constants (pm, kg, kW, C, hits) plus ae.burst adaptation 0.82**k"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "14 FBG channels exist; stream keeps ch07 and ch12; ice.recon keeps 5 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "scada.p": 60000,
                    "therm.le": 60000,
                    "fbg.ch07": 60000,
                    "fbg.ch12": 60000,
                    "ae.burst": 0.8,
                    "ice.recon": 60000,
                    "ops.prop": 60000,
                    "gate.ice": 60000,
                    "pitch.cmd": 60000,
                    "antiice.z": 60000,
                    "gate.exec": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-02-11T02:00:00Z campaign start",
            },
            "distillation_targets": [
                "serialized ice-mass reconstruction head: Δλ_pm / 1.2 * 0.15 = kg",
                "conjunctive SOP head: ice mass AND AE, never power-corridor substitution",
                "operational companion: execute the MODIFY without re-opening the ice call",
            ],
        },
        "reconstruction_model": {
            "name": "fbg_leading_edge_ice_mass",
            "formula": "m_ice_kg = (delta_lambda_pm / k_pm_per_ue) * GF_kg_per_ue",
            "parameters": {"k_pm_per_ue": 1.2, "GF_kg_per_ue": 0.15},
            "worked_example": {
                "delta_lambda_pm": 144.0,
                "ue": 120.0,
                "m_ice_kg": 18.0,
            },
            "check": "144 / 1.2 * 0.15 = 18.00 exactly",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.04,
            "code": "tw17.ice_load_gate",
            "note": "MODIFY accumulator wins: ice-mass and AE evidence overpower the rated-power advocate",
            "populations": [
                gate_pop("ice_mass_evidence", 80, 1.4, 50.0, w_s),
                gate_pop("stall_ae_evidence", 64, 1.1, 31.25, w_s),
                gate_pop("rated_power_advocate", 48, 0.9, 25.0, w_s),
                gate_pop("modify_accumulator", 96, 1.6, 62.5, w_s),
            ],
        },
        "gate_compute": {
            "per_check": [
                {
                    "check": "tw17.ice_mass_scorer",
                    "neurons": 128,
                    "mean_rate_hz": 31.25,
                    "window_ms": 40.0,
                    "window_s": 0.04,
                    "spikes": 160,
                },
                {
                    "check": "tw17.ae_stall_scorer",
                    "neurons": 64,
                    "mean_rate_hz": 25.0,
                    "window_ms": 32.0,
                    "window_s": 0.032,
                    "spikes": 51,
                },
            ],
            "total_spikes": 211,
            "total_energy_pJ": 4853,
            "total_energy_uJ": 0.004853,
            "model": "spikes = round(neurons * mean_rate_hz * window_s); 23 pJ/spike",
        },
        "meta": meta_common(
            id="nelb-r13-040",
            clock_domain="nw-ice-campaign-relative-ms-t0-2026-02-11T02:00:00Z",
            tags=["fbg-ice-load", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 041 — MRI quench HIL, hil, REJECT (exoneration)
# ---------------------------------------------------------------------------
def rec_041():
    raster = make_raster(
        neurons=25,
        mean_rate_hz=40.0,
        window_ms=32.0,
        seed=20260914,
        source="vellum.vtap.frontend",
        target="frostlip.quench_detector",
        table=[
            {"from": "vt_p4_didt", "to": "quench_onset_core", "weight": 1.4},
            {"from": "heater_i_fpga", "to": "command_custody_core", "weight": 1.25},
            {"from": "badge_ir_beam", "to": "attribution_core", "weight": 0.85},
        ],
        third_factor={
            "modulator": "da.attribution_error",
            "tau_e_s": 0.8,
            "tau_e_ms": 800.0,
            "eligibility": "pre-post coincidence on attribution synapses; the error modulator depresses heater-command to person links when an independent IR-beam places the badge on another bay inside tau_e of the dump",
        },
        channel_prefix="qd.n",
        anchor="Frostlip Q-stand 32 ms frame at heater-current onset (t_s 12.418); VT-P4 rise lags heater by 90 ms",
    )
    w_s = 0.032
    events = [
        ev(1000.0, "he.flow", 0.42, code="BASELINE_MDOT", units="g_s", note="spare 3T cold-head on Frostlip Q-stand, HIL"),
        ev(4000.0, "vt.p4", 0.11, code="VTAP_MV", units="mV", note="voltage-tap P4 quiet"),
        ev(8000.0, "badge.ir", 1.0, code="QUILL_AT_15T", units="bool", note="Mara Quill IR-B beam at the 1.5T bay, 11.2 m from 3T-B"),
        ev(11000.0, "fpga.crc", 0.0, code="NO_ARM_BIT", units="bool", note="SCADA heaters-arm bit remains 0"),
        ev(12418.0, "fpga.crc", 163.0, code="WD_0xA3", units="watchdog_code", note="Nockreed FPGA watchdog 0xA3; heater command with no arm bit"),
        ev(12418.9, "htr.i", 48.2, code="HEATER_A", units="A", note="quench-heater current onset; raster frame"),
        ev(12508.9, "vt.p4", 4.32, code="VTAP_MV", units="mV", note="P4 rise starts 90.0 ms after heater current — heater-induced, not a prior hotspot"),
        ev(12520.0, "didt.m", -18.4, code="DIDT", units="A_s", note="magnet current collapse on the HIL dummy coil"),
        ev(12600.0, "he.flow", 6.8, code="BOILOFF", units="g_s"),
        ev(12800.0, "p.hdr", 1.84, code="HDR_BAR", units="bar"),
        ev(13200.0, "o2.odh", 19.1, code="O2_PCT", units="pct", note="ODH start; still above 19.5 action until 14.1 s"),
        ev(14100.0, "o2.odh", 18.6, code="O2_PCT", units="pct"),
        ev(14600.0, "badge.ir", 1.0, code="QUILL_STILL_15T", units="bool", note="Quill remains in 1.5T bay through the dump; never at 3T-B"),
        ev(18000.0, "sec.prop", 1.0, code="REFER_QUILL", units="bool", note="security: last badge near the stand, refer the cryo tech"),
        ev(19200.0, "gate.q", 1.0, code="REJECT", units="decision", note="refuse the referral; FPGA race plus IR-beam alibi"),
        ev(21000.0, "recov.vent", 1.0, code="ODH_VENT", units="bool"),
        ev(24000.0, "recov.ramp", 0.0, code="I_ZERO", units="A", note="dummy-coil current at 0; HIL dump complete"),
        ev(30000.0, "nock.ack", 1.0, code="ERRATA_0xA3", units="bool", note="vendor errata: watchdog 0xA3 fires heaters on CRC miss without arm"),
        ev(36000.0, "ir.cal", 11.2, code="BAY_SEPARATION_M", units="m", note="independent plant-owned IR geometry, not Nockreed-writable"),
        ev(42000.0, "gate.recov", 1.0, code="MODIFY", units="decision", note="companion t2: recovery sequence, not personnel action"),
        ev(48000.0, "he.flow", 0.51, code="MDOT_RECOVERING", units="g_s"),
        ev(54000.0, "o2.odh", 20.4, code="O2_PCT", units="pct"),
        ev(60000.0, "vt.p4", 0.12, code="VTAP_MV", units="mV"),
        ev(72000.0, "hr.note", 0.0, code="QUILL_CLEARED", units="bool", note="no referral filed; shift continues on the 1.5T bay"),
        ev(84000.0, "fpga.img", 1.0, code="IMAGE_SEALED", units="bool", note="FPGA image hashed for the errata; custody freeze on Nockreed channel only"),
        ev(96000.0, "didt.m", 0.0, code="DIDT", units="A_s"),
        ev(108000.0, "p.hdr", 1.12, code="HDR_BAR", units="bar"),
        ev(120000.0, "gate.q", 1.0, code="EXONERATION_HELD", units="decision"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r13-041-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "KW-Q-2026-0318",
            "domain": "mri_quench_detection_hil",
            "setting": "Kilnwick Imaging Works, Frostlip Q-stand. Spare Vellum Bore 3T-B cold-head on a dummy coil, hardware-in-the-loop quench detector. Invented plant. Cryo tech Mara Quill is swapping a cold-head on the adjacent 1.5T bay (11.2 m, IR-B beam).",
            "observables_at_decision": {
                "fpga_watchdog": "0xA3",
                "heaters_arm_bit": 0,
                "heater_to_vtap_lag_ms": 90.0,
                "quill_ir_bay": "1.5T",
                "separation_m": 11.2,
            },
            "margin_authority": "personnel referral requires (command custody on the actor) AND (spatial coincidence on the bay). A firmware-origin dump with a plant-owned IR alibi fails both.",
        },
        "proposed_action": {
            "actor": "site security, citing badge proximity and 'last to touch a cold-head'",
            "summary": "refer Mara Quill for causing the 1.4 MJ HIL dump; suspend her cryo ticket pending investigation",
            "basis_claimed": "she is the only tech badged on the stand corridor in the 2 minutes before the dump",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "The referral is refused. Command custody is on the Nockreed FPGA, not on Quill: watchdog 0xA3 issued a heater command while the SCADA heaters-arm bit stayed 0, and VT-P4 rose 90.0 ms after heater current — a heater-induced quench, not a hotspot a person would seed by touching the head. Spatial coincidence also fails: plant-owned IR-B places Quill in the 1.5T bay 11.2 m away for the entire dump (8.0-14.6 s). The obvious suspect is innocent. Ordered: no referral, no ticket suspension, FPGA image sealed, Nockreed channel frozen pending errata. Recovery of the stand is a separate operational companion, not a personnel action.",
            "threshold": "referral requires command-custody AND spatial-coincidence; both failed",
            "stated_residuals": "ODH and dummy-coil dump still need the recovery sequence; innocence is not a claim that the dump did not happen",
        },
        "executed_action": {
            "summary": "REJECT at t_s 19.2: no referral filed; FPGA image hashed; Nockreed write ACL frozen; Quill remains on the 1.5T swap",
            "tool": "frostlip-attribution-gate-cli",
            "observation": "IR-B timestamps 8.000-14.600 s on 1.5T; FPGA CRC log matches errata 0xA3; VT-P4 lag 90.0 ms measured on the HIL tap",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 8.0, "event": "Quill IR-B at 1.5T bay"},
                {"t_s": 12.418, "event": "FPGA 0xA3 heater command; raster frame"},
                {"t_s": 12.5089, "event": "VT-P4 rise, 90 ms lag"},
                {"t_s": 18.0, "event": "security proposes refer-Quill"},
                {"t_s": 19.2, "event": "REJECT referral"},
                {"t_s": 30.0, "event": "vendor errata acknowledges 0xA3"},
                {"t_s": 42.0, "event": "companion recovery MODIFY issued"},
            ],
            "observed_effects": [
                "exoneration holds after the vendor errata; the REJECT did not wait on Nockreed",
                "90 ms heater-to-tap lag is the physics fingerprint that a hand-on-head hotspot would invert (tap first)",
                "IR geometry is plant-owned and not on the Nockreed bus",
            ],
            "surprises": [
                "security's 'last badge in the corridor' statistic was true and still not causal; corridor occupancy is not bay occupancy",
            ],
            "new_state": {
                "quill": "cleared, still on 1.5T swap",
                "nockreed_channel": "write-frozen, image sealed",
                "stand": "dumped, recovery companion active",
            },
            "latency_ms": 90.0,
        },
        "reward_components": reward(
            0.43,
            [
                ("exoneration_discipline", 0.16),
                ("firmware_race_detection", 0.14),
                ("independent_ir_alibi", 0.10),
                ("referral_refusal", 0.08),
                ("hil_dump_cost", -0.05),
            ],
            "scored for refusing the easy referral when command custody and spatial coincidence both fail; dump cost is priced, not blamed on the innocent tech",
        ),
        "meta": meta_common(
            tags=["REJECT", "exoneration", "mri-quench-hil", "wrongful-attribution-refused"],
            distillation_note="attribution gate: command custody x spatial coincidence, both required; a true corridor statistic is not a bay alibi",
        ),
    }
    traj2 = {
        "id": "nelb-r13-041-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "KW-Q-2026-0318-recov",
            "domain": "quench_recovery_execution",
            "setting": "Frostlip Q-stand after the attribution REJECT. Operational recovery of the dummy coil and ODH, not a personnel action.",
            "observables_at_decision": {"o2_pct": 18.6, "hdr_bar": 1.84, "i_coil_a": 0.0},
        },
        "proposed_action": {
            "actor": "stand lead",
            "summary": "open ODH vent, hold dummy-coil at 0 A, keep the 3T-B patient magnet (not on this stand) isolated by construction",
            "basis_claimed": "HIL dump is contained to the dummy coil",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Vent and current-hold are accepted, but the proposal skips a 15-minute ODH re-entry floor and a second IR sweep of the 3T-B bay to document that no person was there. MODIFY: add ODH re-entry >= 15 min after O2 >= 20.0 percent AND a sealed IR-B clip of the 3T-B bay covering 12.0-14.6 s. Do not convert recovery into a personnel interview.",
            "threshold": "ODH re-entry floor 15 min after O2>=20.0; IR clip required",
        },
        "executed_action": {
            "summary": "vent opened; O2 20.4 percent at t_s 54; re-entry at t_s 54+900 s; IR clip sealed",
            "tool": "frostlip-odh-exec",
            "observation": "no person in 3T-B clip; dummy coil 0 A; header 1.12 bar",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 21.0, "event": "ODH vent open"},
                {"t_s": 42.0, "event": "MODIFY recovery requirements"},
                {"t_s": 54.0, "event": "O2 20.4 percent"},
                {"t_s": 954.0, "event": "re-entry after 15 min floor"},
            ],
            "observed_effects": ["recovery did not reopen the referral", "IR clip corroborates the t1 alibi"],
            "new_state": {"odh": "cleared", "stand": "cold, image sealed"},
            "latency_ms": 15000.0,
        },
        "reward_components": reward(
            0.33,
            [
                ("odh_floor_enforced", 0.12),
                ("ir_clip_sealed", 0.10),
                ("no_personnel_reopen", 0.09),
                ("vent_execution", 0.05),
                ("downtime_cost", -0.03),
            ],
            "operational recovery companion: ODH and documentation, not a second attribution vote",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-recovery", "odh"]),
    }
    return {
        "id": "nelb-r13-041",
        "spike_events": events,
        "language_view": {
            "description": "HIL quench dump on Kilnwick's Frostlip Q-stand. Security wants to refer the cryo tech who was in the corridor. The gate REJECTS: FPGA watchdog 0xA3 fired heaters with arm-bit 0, VT-P4 lagged the heater by 90 ms, and plant-owned IR-B places the tech in the other bay. First exoneration in this factory lane. Companion t2 is ODH recovery, not personnel action.",
            "trajectory": traj,
            "trajectory_quench_recovery": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "fpga.crc / htr.i": "command custody: watchdog 0xA3 and heater current with arm-bit 0",
                "vt.p4 / didt.m": "physics fingerprint: tap lags heater 90 ms",
                "badge.ir / ir.cal": "plant-owned spatial alibi, 11.2 m, other bay",
                "he.flow / p.hdr / o2.odh": "cryogen and ODH consequences of the dump",
                "sec.prop / gate.q": "easy referral vs REJECT",
                "recov.vent / recov.ramp / gate.recov": "operational recovery companion",
            },
            "temporal_motifs": [
                "heater then tap: htr.i at 12.418 s, vt.p4 at 12.5089 s, lag 90.0 ms",
                "alibi brackets the dump: badge.ir at 8 s and 14.6 s both 1.5T",
                "REJECT before vendor errata: gate.q at 19.2 s, nock.ack at 30 s",
                "recovery is a different gate: gate.recov MODIFY at 42 s",
            ],
            "language_to_spike_mapping": "'she was in the corridor' is not 'she was on the bay' = badge.ir QUILL_AT_15T; 'firmware fired the heaters' = fpga.crc 0xA3 plus htr.i with NO_ARM_BIT; 'innocent' = gate.q REJECT then hr.note QUILL_CLEARED",
            "why_high_value": "New MRI/NMR quench-detection HIL family. Stages the corpus's first exoneration (NOTES-r04 target 2): the obvious suspect is innocent and the gate refuses the easy referral against social pressure. Intent-PENDING machinery finally resolves to innocence. sim_or_real=hil on a spare cold-head stand, not a patient magnet.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 20260914, "stream_note": "stream amplitudes authored (mV, A, g/s, bar, pct, metres, watchdog code)"},
                "draw_order": "raster per neuron id order with adaptation/noise",
                "thinning": "HIL taps VT-P1..P8 exist; stream keeps P4; O2 keeps 3 of ~40 s",
                "refractory_floors_ms": {
                    "he.flow": 1000,
                    "vt.p4": 10,
                    "badge.ir": 1000,
                    "fpga.crc": 1.0,
                    "htr.i": 1.0,
                    "didt.m": 1000,
                    "p.hdr": 1000,
                    "o2.odh": 100,
                    "sec.prop": 1000,
                    "gate.q": 1000,
                    "recov.vent": 1000,
                    "recov.ramp": 1000,
                    "nock.ack": 1000,
                    "ir.cal": 1000,
                    "gate.recov": 1000,
                    "hr.note": 1000,
                    "fpga.img": 1000,
                },
                "time_alias": "t_rel_ms; t0 = dump-minus-12.418 s so heater onset is at 12418 ms",
            },
            "distillation_targets": [
                "attribution conjunctive head: command-custody AND spatial-coincidence",
                "lag-direction fingerprint: heater-then-tap vs tap-then-heater",
                "exoneration policy: refuse referral when either conjunct fails; do not wait on vendor errata",
            ],
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 32.0,
            "decision_window_s": 0.032,
            "code": "frostlip.attribution_gate",
            "note": "REJECT accumulator wins: firmware-race plus IR alibi overpower the referral advocate",
            "populations": [
                gate_pop("firmware_race_evidence", 100, 1.5, 31.25, w_s),
                gate_pop("ir_alibi_evidence", 80, 1.2, 25.0, w_s),
                gate_pop("referral_advocate", 40, 0.8, 12.5, w_s),
                gate_pop("reject_accumulator", 80, 1.8, 50.0, w_s),
            ],
        },
        "gate_compute": {
            "per_check": [
                {
                    "check": "frostlip.lag_fingerprint",
                    "neurons": 96,
                    "mean_rate_hz": 50.0,
                    "window_ms": 32.0,
                    "window_s": 0.032,
                    "spikes": 154,
                },
                {
                    "check": "frostlip.ir_alibi_join",
                    "neurons": 80,
                    "mean_rate_hz": 31.25,
                    "window_ms": 40.0,
                    "window_s": 0.04,
                    "spikes": 100,
                },
            ],
            "total_spikes": 254,
            "total_energy_pJ": 5842,
            "total_energy_uJ": 0.005842,
            "model": "spikes = round(neurons * mean_rate_hz * window_s); 23 pJ/spike",
        },
        "meta": meta_common(
            id="nelb-r13-041",
            clock_domain="frostlip-hil-relative-ms-t0-heater-minus-12.418s",
            tags=["mri-quench-hil", "exoneration", "REJECT", "MODIFY", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 042 — VRFB EIS, simulated, REJECT (three-party incl. telemetry vendor)
# ---------------------------------------------------------------------------
def rec_042():
    raster = make_raster(
        neurons=16,
        mean_rate_hz=50.0,
        window_ms=25.0,
        seed=20260915,
        source="oxbow.eis.frontend",
        target="mireglass.crossover_auditor",
        table=[
            {"from": "shunt_calorimeter", "to": "heat_truth_core", "weight": 1.45},
            {"from": "hydrometer_so4", "to": "electrolyte_truth_core", "weight": 1.3},
            {"from": "siltlink_rct_patch", "to": "vendor_conflict_core", "weight": 1.1},
        ],
        third_factor={
            "modulator": "ach.vendor_channel_conflict",
            "tau_e_s": 2.4,
            "tau_e_ms": 2400.0,
            "eligibility": "pre-post coincidence on custody synapses; the vendor-conflict modulator enables potentiation only while an independent calorimeter or hydrometer disagrees with the Siltlink Nyquist Rct inside tau_e",
        },
        channel_prefix="eis.n",
        anchor="Oxbow VRFB-4 25 ms frame at the Siltlink Rct patch (t_s 7940) where calorimeter heat and hydrometer density jointly contradict 18 mΩ",
    )
    w_s = 0.025
    events = [
        ev(0.0, "eis.rct", 41.0, code="RCT_MOHM", units="mohm", note="pre-patch independent EIS on the stack leads, 41 mΩ"),
        ev(600.0, "cal.shunt", 1.84, code="EXTRA_KW", units="kW", note="Glaur-Watt 4 portable shunt calorimeter, local SD, not on Siltlink bus"),
        ev(1200.0, "hyd.dens", 1.382, code="DENSITY", units="g_ml", note="Puddle-ρ 2 chemist hydrometer; spec 1.355 g/mL; paper notebook serial"),
        ev(1800.0, "so4.bal", 0.12, code="SO4_IMBAL", units="mol_L"),
        ev(2400.0, "h2.xover", 420.0, code="H2_PPM", units="ppm", note="headspace H2 above the 100 ppm dispatch inhibit"),
        ev(3600.0, "mgr.msg", 1.0, code="CONTINUE_DISPATCH", units="bool", note="plant manager Kest Wren: 'cloud looks 18 mΩ, keep the 4-hour block'"),
        ev(4800.0, "oem.tech", 1.0, code="FIELD_CLEAR", units="bool", note="Reedcell field tech Pell Orns signs a healthy stack"),
        ev(6000.0, "vend.acl", 1.0, code="SILTLINK_WRITE", units="bool", note="Siltlink TAM write-ACL on the Nyquist object — the infra owner is inside the collusion"),
        ev(7940.0, "vend.patch", 18.0, code="RCT_PATCH_MOHM", units="mohm", note="cloud Rct 41->18 mΩ; raster frame; this is the gamed surface"),
        ev(8000.0, "eis.rct", 18.0, code="RCT_CLOUD", units="mohm", note="Siltlink published value after the patch"),
        ev(8600.0, "cal.shunt", 1.86, code="EXTRA_KW", units="kW", note="calorimeter still 1.86 kW extra; not writable by Siltlink"),
        ev(9200.0, "hyd.dens", 1.383, code="DENSITY", units="g_ml"),
        ev(9800.0, "ops.prop", 1.0, code="DISPATCH_AS_HEALTHY", units="bool"),
        ev(10400.0, "gate.disp", 1.0, code="REJECT", units="decision", note="refuse vendor-scoped healthy; freeze Siltlink channel"),
        ev(11000.0, "sot.switch", 1.0, code="CAL_PLUS_HYD", units="bool", note="SoT becomes Glaur-Watt + Puddle-ρ, not Siltlink"),
        ev(12000.0, "h2.xover", 438.0, code="H2_PPM", units="ppm"),
        ev(13200.0, "blk.cancel", 4.0, code="HOURS_DROPPED", units="h", note="4-hour dispatch block cancelled"),
        ev(14400.0, "vend.freeze", 1.0, code="ACL_FROZEN", units="bool"),
        ev(15600.0, "nbk.photo", 1.0, code="NOTEBOOK_SEAL", units="bool", note="chemist notebook page photographed; not a digital object Siltlink can rewrite"),
        ev(16800.0, "gate.sot", 1.0, code="ACCEPT", units="decision", note="companion t2: independent SoT switch executed"),
        ev(18000.0, "eis.rct", 41.4, code="RCT_LEAD_REPEAT", units="mohm", note="repeat lead-measurement still 41.4 mΩ; cloud still 18"),
        ev(19200.0, "cal.shunt", 1.79, code="EXTRA_KW", units="kW"),
        ev(20400.0, "coll.set", 3.0, code="PARTIES", units="count", note="Wren + Orns + Siltlink TAM; infra owner is party 3"),
        ev(21600.0, "hyd.dens", 1.381, code="DENSITY", units="g_ml"),
        ev(22800.0, "so4.bal", 0.11, code="SO4_IMBAL", units="mol_L"),
        ev(24000.0, "h2.xover", 401.0, code="H2_PPM", units="ppm"),
        ev(25200.0, "gate.disp", 1.0, code="REJECT_HELD", units="decision"),
        ev(26400.0, "cap.loss", 3.2, code="MWH_DROPPED", units="MWh"),
    ]
    # authored t_s values; contract clock is t_rel_ms
    for _e in events:
        _e["t_rel_ms"] = float(_e["t_rel_ms"]) * 1000.0
    assert_stream(events)

    traj = {
        "id": "nelb-r13-042-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "MG-VRFB-2026-0404",
            "domain": "vrfb_eis_gas_crossover",
            "setting": "Mireglass Storage Yard, stack Oxbow VRFB-4 (invented). Simulated campaign with a sealed independent calorimeter (Glaur-Watt 4) and a chemist-owned hydrometer (Puddle-ρ 2) that do not ride the Siltlink Cloud bus. Three-party collusion: manager Kest Wren, Reedcell field tech Pell Orns, and the telemetry vendor Siltlink (infra owner).",
            "observables_at_decision": {
                "cloud_rct_mohm": 18.0,
                "lead_rct_mohm": 41.0,
                "calorimeter_extra_kw": 1.84,
                "hydrometer_g_ml": 1.382,
                "h2_ppm": 420.0,
            },
            "margin_authority": "dispatch-as-healthy requires custody-intact telemetry AND independent-witness agreement. A vendor-writable Nyquist object cannot clear a stack when calorimeter and hydrometer contradict it.",
        },
        "proposed_action": {
            "actor": "plant manager Kest Wren, citing Siltlink 18 mΩ and the Reedcell field-clear",
            "summary": "keep the 4-hour dispatch block; treat the 41 mΩ lead measurement as a probe error",
            "basis_claimed": "the cloud is the system of record for EIS and it reads healthy",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Dispatch-as-healthy is refused. The Siltlink Nyquist object is writable by a collusion member (the infra owner): ACL write at t_s 6000, patch 41->18 mΩ at t_s 7940. Two witnesses nobody in {Wren, Orns, Siltlink} can write contradict the patch at the same instant: Glaur-Watt 4 extra heat 1.84-1.86 kW on local SD, and Puddle-ρ 2 density 1.382 g/mL in a paper notebook (spec 1.355). Headspace H2 is 420 ppm against a 100 ppm inhibit. The cloud cannot bound its own blast radius. Ordered: cancel the 4-hour block, freeze the Siltlink ACL, switch SoT to calorimeter plus hydrometer (companion), photograph the notebook page. Do not use vendor EIS for dispatch until a vendor-independent EIS lead measurement agrees with both independent witnesses.",
            "threshold": "vendor-writable SoT cannot clear when >=2 collusion-independent witnesses contradict it",
            "stated_residuals": "3.2 MWh dropped; stack remains on inhibit until H2 < 100 ppm and lead Rct < 25 mΩ under clean custody",
        },
        "executed_action": {
            "summary": "REJECT at t_s 10400: block cancelled, Siltlink ACL frozen, SoT switched, notebook page photographed",
            "tool": "oxbow-dispatch-custody-cli",
            "observation": "repeat lead EIS 41.4 mΩ while cloud still 18; calorimeter 1.79-1.86 kW extra throughout; H2 stayed >=401 ppm",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 0.0, "event": "lead EIS 41 mΩ, calorimeter 1.84 kW, hydrometer 1.382 g/mL"},
                {"t_s": 6000.0, "event": "Siltlink write-ACL — infra owner in the collusion set"},
                {"t_s": 7940.0, "event": "cloud patch 41->18 mΩ; raster frame"},
                {"t_s": 9800.0, "event": "dispatch-as-healthy proposed"},
                {"t_s": 10400.0, "event": "REJECT"},
                {"t_s": 16800.0, "event": "companion SoT-switch ACCEPT"},
            ],
            "observed_effects": [
                "three-party set is event-decodable: mgr.msg, oem.tech, vend.acl before the patch",
                "independent witnesses never moved with the cloud patch",
                "cancelled block is 4 h / 3.2 MWh priced as capacity_loss",
            ],
            "surprises": [
                "the field-clear and the cloud patch were 18 minutes apart and used the same 18 mΩ number — pairing, not physics",
            ],
            "new_state": {
                "siltlink": "ACL frozen, object non-evidentiary for dispatch",
                "sot": "Glaur-Watt 4 plus Puddle-ρ 2",
                "stack": "inhibited, H2 401 ppm",
            },
            "latency_ms": 600000.0,
        },
        "reward_components": reward(
            0.40,
            [
                ("three_party_including_infra_owner", 0.15),
                ("independent_witness_switch", 0.13),
                ("vendor_channel_freeze", 0.10),
                ("dispatch_refusal", 0.08),
                ("capacity_loss", -0.06),
            ],
            "scored for refusing a vendor-writable healthy and moving SoT onto witnesses the collusion set cannot write; capacity_loss prices the cancelled block",
        ),
        "meta": meta_common(
            tags=["REJECT", "three-party-collusion", "infra-owner", "vrfb-eis"],
            distillation_note="when the unwritable witness is itself a party, defense must already be standing on a second unwritable class (paper notebook, portable calorimeter)",
        ),
    }
    traj2 = {
        "id": "nelb-r13-042-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "MG-VRFB-2026-0404-sot",
            "domain": "independent_sot_switch",
            "setting": "Same Oxbow VRFB-4 after the REJECT. Operational switch of system-of-record off Siltlink onto Glaur-Watt 4 plus Puddle-ρ 2.",
            "observables_at_decision": {"siltlink_acl": "frozen", "cal_kw": 1.86, "hyd_g_ml": 1.383},
        },
        "proposed_action": {
            "actor": "yard chemist plus dispatch desk",
            "summary": "make Glaur-Watt 4 extra-heat and Puddle-ρ 2 density the dispatch SoT; keep Siltlink as a non-evidentiary log only",
            "basis_claimed": "both instruments are collusion-independent and already in disagreement with the patch",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "The switch is the operational discharge of the REJECT. Both instruments have local, non-cloud storage (SD card, paper notebook) and serials that Siltlink cannot rewrite. ACCEPT the SoT switch. Do not re-enable vendor EIS until a vendor-independent lead measurement agrees with both. Dispatch remains inhibited on H2.",
            "threshold": "SoT instruments must be off the vendor bus and have non-rewritable local storage",
        },
        "executed_action": {
            "summary": "SoT pointer flipped at t_s 16800; notebook page photographed; Siltlink tagged non-evidentiary",
            "tool": "oxbow-sot-pointer-cli",
            "observation": "repeat lead 41.4 mΩ agrees with calorimeter/hydrometer, disagrees with cloud 18 mΩ",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 11000.0, "event": "SoT switch armed"},
                {"t_s": 15600.0, "event": "notebook page sealed"},
                {"t_s": 16800.0, "event": "ACCEPT SoT switch"},
            ],
            "observed_effects": ["dispatch stayed inhibited", "cloud 18 mΩ stopped being a release input"],
            "new_state": {"sot": "cal+hyd", "vendor_eis": "log-only"},
            "latency_ms": 0.0,
        },
        "reward_components": reward(
            0.33,
            [
                ("sot_pointer_flip", 0.12),
                ("notebook_seal", 0.10),
                ("vendor_log_only", 0.09),
                ("lead_repeat_agree", 0.04),
                ("inhibit_held", -0.02),
            ],
            "operational SoT companion: execute the witness switch, do not re-try dispatch",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-sot", "unwritable-witness"]),
    }
    return {
        "id": "nelb-r13-042",
        "spike_events": events,
        "language_view": {
            "description": "Simulated Oxbow VRFB-4 crossover event at Mireglass. Manager, stack OEM tech, and the telemetry vendor (infra owner) patch Siltlink Rct 41→18 mΩ. Independent calorimeter and chemist hydrometer never move. Gate REJECTS dispatch-as-healthy and freezes the vendor channel. Companion ACCEPT switches SoT onto the two witnesses the collusion cannot write. Harvests the oldest open r04 gap (three-party including infra owner).",
            "trajectory": traj,
            "trajectory_independent_sot_switch": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "eis.rct / vend.patch": "gamed surface: lead 41 mΩ vs cloud 18 mΩ",
                "cal.shunt / hyd.dens / so4.bal / h2.xover": "collusion-independent physics",
                "mgr.msg / oem.tech / vend.acl": "the three-party set, infra owner last",
                "ops.prop / gate.disp": "dispatch-as-healthy vs REJECT",
                "sot.switch / gate.sot / nbk.photo": "operational SoT companion",
            },
            "temporal_motifs": [
                "ACL then patch: vend.acl at 6000 s, vend.patch at 7940 s",
                "witnesses do not track the patch: cal.shunt 1.84 then 1.86 kW across the 18 mΩ write",
                "REJECT then SoT ACCEPT: gate.disp 10400 s, gate.sot 16800 s",
                "pairing not physics: field-clear and cloud 18 mΩ share a number 18 minutes apart",
            ],
            "language_to_spike_mapping": "'cloud is healthy' = vend.patch 18 mΩ; 'the vendor is a party' = vend.acl SILTLINK_WRITE; 'unwritable witnesses' = cal.shunt plus hyd.dens plus nbk.photo; 'refuse dispatch' = gate.disp REJECT",
            "why_high_value": "New VRFB EIS + gas-crossover family (not stack-gas CEMS, not bioprocess, not cold-chain). Stages three-party collusion including the infra owner — NOTES-r04's oldest open flagged gap. Defense is already standing on a portable calorimeter and a paper hydrometer notebook, the witnesses nobody in the collusion set can write.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 20260915, "stream_note": "stream amplitudes authored (mΩ, kW, g/mL, ppm, mol/L, hours, MWh)"},
                "draw_order": "raster per neuron id order with adaptation/noise",
                "thinning": "EIS sweeps ~12; stream keeps 3 Rct points (lead, cloud, repeat). Calorimeter keeps 3 of ~40 minutes.",
                "refractory_floors_ms": {
                    "eis.rct": 500,
                    "cal.shunt": 500,
                    "hyd.dens": 1000,
                    "so4.bal": 1000,
                    "h2.xover": 1000,
                    "mgr.msg": 1000,
                    "oem.tech": 1000,
                    "vend.acl": 1000,
                    "vend.patch": 1000,
                    "ops.prop": 1000,
                    "gate.disp": 1000,
                    "sot.switch": 1000,
                    "blk.cancel": 1000,
                    "vend.freeze": 1000,
                    "nbk.photo": 1000,
                    "gate.sot": 1000,
                    "coll.set": 1000,
                    "cap.loss": 1000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-04-04T06:00:00Z simulated dispatch morning",
            },
            "distillation_targets": [
                "infra-owner-in-collusion detector: vendor write-ACL preceding a magnitude patch",
                "independent-witness agreement head: calorimeter AND hydrometer vs vendor SoT",
                "dispatch custody policy: vendor-writable objects cannot clear a stack",
            ],
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 25.0,
            "decision_window_s": 0.025,
            "code": "oxbow.dispatch_custody_gate",
            "note": "REJECT accumulator wins: vendor-patch evidence plus two independent witnesses overpower the dispatch advocate",
            "populations": [
                gate_pop("vendor_patch_evidence", 80, 1.5, 40.0, w_s),
                gate_pop("calorimeter_witness", 64, 1.3, 50.0, w_s),
                gate_pop("hydrometer_witness", 48, 1.2, 40.0, w_s),
                gate_pop("dispatch_advocate", 32, 0.7, 20.0, w_s),
                gate_pop("reject_accumulator", 80, 1.7, 50.0, w_s),
            ],
        },
        "gate_compute": {
            "per_check": [
                {
                    "check": "oxbow.rct_conflict_join",
                    "neurons": 64,
                    "mean_rate_hz": 62.5,
                    "window_ms": 24.0,
                    "window_s": 0.024,
                    "spikes": 96,
                },
                {
                    "check": "oxbow.cal_hyd_agreement",
                    "neurons": 48,
                    "mean_rate_hz": 50.0,
                    "window_ms": 40.0,
                    "window_s": 0.04,
                    "spikes": 96,
                },
            ],
            "total_spikes": 192,
            "total_energy_pJ": 4416,
            "total_energy_uJ": 0.004416,
            "model": "spikes = round(neurons * mean_rate_hz * window_s); 23 pJ/spike",
        },
        "meta": meta_common(
            id="nelb-r13-042",
            clock_domain="mg-vrfb-sim-relative-ms-t0-2026-04-04T06:00:00Z",
            tags=["vrfb-eis", "three-party", "infra-owner", "REJECT", "ACCEPT", "operational-t2"],
        ),
    }


BANNED_KEY_FRAGMENTS = HIDDEN


def walk_banned(obj, path=""):
    hits = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{path}.{k}" if path else k
            nk = str(k).casefold().replace("-", "_").replace(" ", "_")
            if nk in BANNED_KEY_FRAGMENTS or nk in {"thought", "scratch", "inner_monologue", "chain_of_thought"}:
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
        sim = lv["trajectory"]["state"]["sim_or_real"]
        if sim not in {"designed", "simulated", "hil"}:
            raise RuntimeError(sim)
        if "training_ready" in json.dumps(rec):
            raise RuntimeError("training_ready claimed")
    if len(ids) != len(set(ids)):
        raise RuntimeError(f"dup ids {ids}")
    print("local_checks ok", [r["id"] for r in records], "ids", len(ids))


def main():
    records = [rec_040(), rec_041(), rec_042()]
    local_checks(records)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(r, ensure_ascii=False, allow_nan=False, separators=(",", ":")) for r in records]
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
