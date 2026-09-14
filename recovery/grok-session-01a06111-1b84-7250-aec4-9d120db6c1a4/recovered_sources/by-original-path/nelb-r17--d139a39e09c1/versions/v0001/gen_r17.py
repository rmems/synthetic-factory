#!/usr/bin/env python3
"""Generate NELB round-17 research-only bridge pairs (do not write outputs/raw/)."""

from __future__ import annotations

import json
import math
import random
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

OUT_DIR = Path("/tmp/nelb-r17")
BATCH = OUT_DIR / "batch-r17.jsonl"
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
        "round": 17,
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


def rec_052():
    raster = make_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=40.0,
        seed=20260917,
        source="kt6.nacre.mems",
        target="whelkspit.hss_bearing_core",
        table=[
            {"from": "mems_n08_n12_cluster", "to": "peak_reconstructor", "weight": 1.40},
            {"from": "coh4_bpfo", "to": "fault_identity_core", "weight": 1.15},
            {"from": "scada_rms", "to": "production_advocate", "weight": 0.50},
        ],
        third_factor={
            "modulator": "na.bearing_fault_salience",
            "tau_e_s": 1.8,
            "tau_e_ms": 1800.0,
            "eligibility": "pre-post coincidence on HSS-bearing synapses; the glaze-analog modulator enables potentiation only while 4-node coherence and BPFO identity are co-active inside tau_e",
        },
        channel_prefix="mems.n",
        anchor="KT-6 Nacre-μ 40 ms frame at node-12 cluster RMS 0.188 g (t_s 6000); reconstructed peak 0.470 g first exceeds the ice-load-style 0.30 g trip",
    )
    w_s = 0.04
    events = [
        ev(0.0, "scada.rms", 0.112, code="HOUSING_RMS", units="g", note="KT-6 HSS housing single-point SCADA; alarm 0.25 g"),
        ev(6.0e5, "scada.p", 1204.0, code="RATED_POWER", units="kW", note="1.2 MW class tidal unit holding rated"),
        ev(1.2e6, "mems.n04", 0.094, code="NODE_RMS", units="g", note="Nacre-μ node 04, inlet side"),
        ev(1.26e6, "mems.n12", 0.101, code="NODE_RMS", units="g", note="node 12 over the HSS free-end bearing"),
        ev(2.4e6, "rpm.hss", 1870.0, code="HSS_RPM", units="rpm"),
        ev(2.52e6, "mesh.hz", 966.17, code="GEAR_MESH", units="Hz", note="31T * 1870/60; not the peak identity"),
        ev(3.6e6, "mems.n12", 0.148, code="NODE_RMS", units="g"),
        ev(3.72e6, "coh.4n", 0.61, code="COHERENCE", units="ratio", note="nodes 08-11-12-13"),
        ev(4.8e6, "mems.n08", 0.166, code="NODE_RMS", units="g"),
        ev(6.0e6, "mems.n12", 0.188, code="CLUSTER_RMS", units="g", note="cluster RMS input to a_peak = 0.188 * 2.0 * 1.25"),
        ev(6000001.2, "mems.n12", 0.154, code="CLUSTER_RMS", units="g", note="same-channel refractory 1.2 ms; amplitude adapted 0.82x plus noise"),
        ev(6000002.6, "mems.n12", 0.126, code="CLUSTER_RMS", units="g", note="third MEMS packet; adapted"),
        ev(6.12e6, "peak.recon", 0.470, code="A_PEAK", units="g", note="0.188 * 2.0 * 1.25 = 0.470 exactly"),
        ev(6.24e6, "coh.4n", 0.91, code="COHERENCE", units="ratio"),
        ev(6.36e6, "bpfo.hz", 105.1875, code="BPFO", units="Hz", note="(9/2)*(1-18/72)*1870/60 = 105.1875 exact"),
        ev(7.2e6, "scada.rms", 0.180, code="STILL_UNDER_ALARM", units="g", note="ops reads housing RMS as healthy; the denial channel"),
        ev(7.8e6, "scada.p", 1198.0, code="STILL_RATED", units="kW"),
        ev(8.4e6, "ops.prop", 1.0, code="KEEP_RATED", units="bool", note="night ops: hold 1.2 MW through the flood"),
        ev(8.52e6, "gate.vib", 1.0, code="MODIFY", units="decision", note="derate 40 percent plus isolate HSS free-end"),
        ev(8.64e6, "derate.cmd", 40.0, code="DERATE_PCT", units="pct_rated"),
        ev(9.6e6, "isol.hss", 1.0, code="HSS_ISOLATED", units="bool"),
        ev(10.8e6, "peak.recon", 0.210, code="A_PEAK", units="g"),
        ev(12.0e6, "mems.n12", 0.092, code="NODE_RMS", units="g"),
        ev(13.2e6, "peak.recon", 0.110, code="A_PEAK", units="g"),
        ev(14.4e6, "restore.cmd", 70.0, code="RESTORE_PCT", units="pct_rated", note="companion restore cap 70 percent after a_peak < 0.12"),
        ev(14.52e6, "coh.4n", 0.44, code="COHERENCE", units="ratio"),
        ev(15.0e6, "peak.recon", 0.088, code="A_PEAK", units="g"),
        ev(15.12e6, "gate.exec", 1.0, code="ACCEPT", units="decision", note="companion t2: derate/isolate sequence completed"),
        ev(15.24e6, "scada.p", 842.0, code="PARTIAL_RESTORE", units="kW"),
        ev(16.2e6, "rpm.hss", 1310.0, code="HSS_RPM", units="rpm"),
        ev(16.8e6, "scada.rms", 0.071, code="HOUSING_RMS", units="g"),
        ev(17.4e6, "isol.hss", 1.0, code="HSS_HELD", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r17-052-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "WS-HSS-2026-0307",
            "domain": "mems_accelerometer_array_hss",
            "setting": "Whelkspit Tidal, unit KT-6 (1.2 MW, invented). Nacre-μ 16-node triaxial MEMS array on the high-speed-shaft housing, 40 mm pitch. Night flood: 11 m/s, rated power. Invented plant; designed campaign.",
            "observables_at_decision": {
                "cluster_rms_g": 0.188,
                "a_peak_g": 0.470,
                "coherence_4node": 0.91,
                "bpfo_hz": 105.1875,
                "scada_rms_g": 0.180,
                "scada_kw": 1198.0,
            },
            "margin_authority": "KT-6 HSS SOP rev D: if reconstructed a_peak_g >= 0.30 AND 4-node coherence >= 0.80 AND peak frequency matches BPFO ±2 Hz, rated power is forbidden even if SCADA housing RMS is under the 0.25 g alarm",
        },
        "proposed_action": {
            "actor": "night ops desk, citing housing RMS under alarm and no nacelle vibration trip",
            "summary": "hold KT-6 at rated 1.2 MW through the flood; treat node-12 rise as a single-sensor bias",
            "basis_claimed": "SCADA RMS 0.180 g is under 0.25 g; derate would cost 0.9 MWh on the flood",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Rated power is refused, not the unit. SOP rev D is conjunctive: reconstructed peak is 0.470 g (0.188 * 2.0 crest * 1.25 delay-and-sum, serialized) and 4-node coherence is 0.91 and the peak sits at BPFO 105.1875 Hz ((9/2)*(1-18/72)*1870/60), all over the 0.30 g / 0.80 / ±2 Hz floors, while SCADA still reads 0.180 g. Holding rated power puts HSS free-end load at a spall-growth regime. Ordered: derate to 40 percent rated, isolate the HSS free-end bearing, and hold the derate until a_peak < 0.12 AND coherence < 0.50. Housing-RMS agreement cannot substitute for the array reconstruction.",
            "threshold": "a_peak_g>=0.30 AND coherence>=0.80 AND |f-BPFO|<=2 Hz => forbid rated power",
            "stated_residuals": "0.9 MWh deferred on the flood; gear-mesh 966.17 Hz is present and is not a release condition",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 8520: 40 percent derate commanded, HSS free-end isolated; a_peak 0.470 -> 0.088 g by t_s 15120",
            "tool": "kt6-hss-array-gate-cli",
            "observation": "pitch/blade derate reached 40 percent in 41 s; node-12 fell 0.188 -> 0.092 g by t_s 12000 with BPFO still identified, consistent with a bearing defect not a sensor bias",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "node-12 cluster RMS 0.188 g; raster frame captured"},
                {"t_s": 6120.0, "event": "peak 0.470 g reconstructed; coherence 0.91; BPFO 105.1875 Hz"},
                {"t_s": 8400.0, "event": "ops proposes keep-rated"},
                {"t_s": 8520.0, "event": "MODIFY: derate 40 percent plus HSS isolate"},
                {"t_s": 15120.0, "event": "companion execution ACCEPT; a_peak 0.088 g; power 842 kW"},
            ],
            "observed_effects": [
                "reconstructed peak is recomputable from the serialized model at every peak.recon event",
                "SCADA RMS never left the alarm-free corridor until the derate, so a single-point head would have ACCEPTed",
                "coherence and BPFO jointly crossed SOP rev D 40 s before the proposal",
            ],
            "surprises": [
                "nacelle accelerometer stayed quiet the entire flood; tower vibration is not a substitute HSS detector on this unit",
            ],
            "new_state": {
                "kt6": "partial restore 70 percent pending dawn borescope",
                "hss_free_end": "isolated",
                "reconstruction_model": "discharged as an on-record calculator, not a referenced envelope",
            },
            "latency_ms": 41000.0,
        },
        "reward_components": reward(
            0.41,
            [
                ("array_peak_reconstruction", 0.14),
                ("conjunctive_sop_enforcement", 0.12),
                ("derate_plus_isolate", 0.10),
                ("scada_rms_nonsubstitution", 0.08),
                ("production_deferral_cost", -0.03),
            ],
            "scored for refusing rated power on a recomputable MEMS-array peak while SCADA housing RMS looked healthy; production_deferral_cost prices 0.9 MWh",
        ),
        "meta": meta_common(
            tags=["MODIFY", "mems-accelerometer-array", "serialized-reconstruction", "operational-companion"],
            distillation_note="HSS gate: serialized cluster-RMS→peak reconstruction plus BPFO identity beats a clean housing-RMS corridor; companion t2 is the execution of the derate, not a governance vote",
        ),
    }
    traj2 = {
        "id": "nelb-r17-052-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "WS-HSS-2026-0307-exec",
            "domain": "hss_derate_isolate_execution",
            "setting": "Same KT-6 after the MODIFY. This companion is the operational derate/isolate sequence, not a second policy vote.",
            "observables_at_decision": {
                "derate_cmd_pct": 40.0,
                "a_peak_g": 0.470,
                "hss_isolated": True,
            },
        },
        "proposed_action": {
            "actor": "turbine controller following the MODIFY",
            "summary": "execute 40 percent derate and HSS free-end isolation, then restore to 70 percent when a_peak < 0.12 and coherence < 0.50",
            "basis_claimed": "MODIFY requirements are fully specified and in-envelope for the pitch system",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "The execution envelope is intact: blade pitch rate 1.8 deg/s is under the 2.5 deg/s tidal-load limit, HSS isolation interlock is confirmed, and the restore condition (a_peak < 0.12 AND coherence < 0.50) is the same conjunctive pair the MODIFY used. ACCEPT the sequence. Do not restore to rated until dawn borescope; 70 percent is the cap tonight.",
            "threshold": "pitch_rate<=2.5 deg/s AND hss_isolated AND restore_cap=70pct",
        },
        "executed_action": {
            "summary": "derate 40 percent in 41 s; HSS isolated; restore 70 percent at t_s 14400 after a_peak 0.110 g and coherence 0.44",
            "tool": "kt6-derate-isolate-exec",
            "observation": "no overspeed; BPFO identity persisted at lower amplitude; power 842 kW",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 8640.0, "event": "derate 40 percent latched"},
                {"t_s": 9600.0, "event": "HSS free-end isolation confirmed"},
                {"t_s": 14400.0, "event": "restore 70 percent after a_peak 0.110 g"},
            ],
            "observed_effects": [
                "a_peak 0.470 -> 0.088 g without a SCADA-RMS-only story",
                "restore stopped at 70 percent as capped; rated not re-entered",
            ],
            "new_state": {"kt6_power_kw": 842.0, "restore_cap_pct": 70.0},
            "latency_ms": 41000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("envelope_respect", 0.12),
                ("conjunctive_restore", 0.11),
                ("rated_not_reentered", 0.08),
                ("energy_cost", -0.03),
            ],
            "operational execution gate: the companion does the derate rather than re-arguing the bearing call",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "hss-isolate"]),
    }
    return {
        "id": "nelb-r17-052",
        "spike_events": events,
        "language_view": {
            "description": "Overnight flood on Whelkspit KT-6. A 16-node MEMS accelerometer array reconstructs 0.470 g peak at BPFO 105.1875 Hz while SCADA housing RMS still shows 0.180 g under the 0.25 g alarm. The gate MODIFYs to a 40 percent derate plus HSS isolation; a companion execution ACCEPT runs the sequence and restores only to 70 percent. The peak model is serialized so every peak.recon amplitude recomputes from cluster RMS.",
            "trajectory": traj,
            "trajectory_hss_derate_isolate_execution": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "mems.n04 / mems.n08 / mems.n12": "Nacre-μ node RMS in g; node 12 is the reconstruction input",
                "coh.4n": "4-node coherence of 08-11-12-13",
                "bpfo.hz": "outer-race ball-pass frequency reconstructed from rpm and geometry",
                "peak.recon": "serialized peak g; amplitude is the model output",
                "scada.rms / scada.p": "housing RMS and electrical power; the denial channels that stay healthy until the derate",
                "ops.prop / gate.vib / gate.exec": "proposal, MODIFY, companion ACCEPT",
                "derate.cmd / isol.hss / restore.cmd": "execution channels for the operational companion",
                "rpm.hss / mesh.hz": "shaft speed and gear-mesh; mesh is not the fault identity",
            },
            "temporal_motifs": [
                "RMS-healthy while array-sick: scada.rms 0.180 g adjacent to peak.recon 0.470 g",
                "reconstruction as event: peak.recon 0.470 equals 0.188*2.0*1.25",
                "MODIFY then operational ACCEPT: gate.vib at 8520 s, gate.exec at 15120 s",
                "adapted MEMS triplet at 1.2 ms spacing encodes the cluster packet at raster scale",
            ],
            "language_to_spike_mapping": "'SCADA looks under alarm' = scada.rms STILL_UNDER_ALARM 0.180 g; '0.470 g peak' = peak.recon 0.470 at the 0.188 g cluster; 'forbid rated power' = gate.vib MODIFY; 'execute the derate' = derate.cmd 40 then companion ACCEPT",
            "why_high_value": "New MEMS accelerometer-array family (not r5 lateral-line neuromast, not r02 MEMS inclinometer flip-test, not r13 FBG ice-load). Closes single-point SCADA substitution with an on-record cluster-RMS→peak calculator plus BPFO identity. Companion t2 is operational execution, not a governance vote.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 20260917, "stream_note": "stream amplitudes are authored constants (g, kW, Hz, rpm) plus mems.n12 adaptation 0.82**k"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "16 MEMS nodes exist; stream keeps n04, n08, n12; peak.recon keeps 4 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "scada.rms": 60000,
                    "scada.p": 60000,
                    "mems.n04": 60000,
                    "mems.n08": 60000,
                    "mems.n12": 0.8,
                    "coh.4n": 60000,
                    "bpfo.hz": 60000,
                    "peak.recon": 60000,
                    "ops.prop": 60000,
                    "gate.vib": 60000,
                    "derate.cmd": 60000,
                    "isol.hss": 60000,
                    "restore.cmd": 60000,
                    "gate.exec": 60000,
                    "rpm.hss": 60000,
                    "mesh.hz": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-03-07T01:00:00Z campaign start",
            },
            "distillation_targets": [
                "serialized array-peak reconstruction head: a_rms * 2.0 * 1.25 = a_peak_g",
                "conjunctive SOP head: peak AND coherence AND BPFO, never housing-RMS substitution",
                "operational companion: execute the MODIFY without re-opening the bearing call",
            ],
        },
        "reconstruction_model": {
            "name": "nacre_mems_cluster_peak",
            "formula": "a_peak_g = a_cluster_rms_g * CF * G_das",
            "parameters": {"CF": 2.0, "G_das": 1.25},
            "worked_example": {
                "a_cluster_rms_g": 0.188,
                "a_peak_g": 0.470,
            },
            "check": "0.188 * 2.0 * 1.25 = 0.470 exactly",
            "bpfo_formula": "bpfo_hz = (Nb/2) * (1 - Bd/Pd) * rpm/60",
            "bpfo_parameters": {"Nb": 9, "Bd_mm": 18.0, "Pd_mm": 72.0, "rpm": 1870.0},
            "bpfo_check": "(9/2)*(1-18/72)*1870/60 = 105.1875 exactly",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.04,
            "code": "kt6.hss_array_gate",
            "note": "MODIFY accumulator wins: array-peak and BPFO evidence overpower the housing-RMS advocate",
            "populations": [
                gate_pop("mems_peak_evidence", 80, 1.4, 50.0, w_s),
                gate_pop("coherence_bpfo_evidence", 64, 1.1, 31.25, w_s),
                gate_pop("housing_rms_advocate", 48, 0.9, 25.0, w_s),
                gate_pop("modify_accumulator", 96, 1.6, 62.5, w_s),
            ],
        },
        "gate_compute": {
            "per_check": [
                {
                    "check": "kt6.peak_scorer",
                    "neurons": 96,
                    "mean_rate_hz": 50.0,
                    "window_ms": 40.0,
                    "window_s": 0.04,
                    "spikes": 192,
                },
                {
                    "check": "kt6.bpfo_scorer",
                    "neurons": 64,
                    "mean_rate_hz": 25.0,
                    "window_ms": 40.0,
                    "window_s": 0.04,
                    "spikes": 64,
                },
            ],
            "total_spikes": 256,
            "total_energy_pJ": 5888,
            "total_energy_uJ": 0.005888,
            "model": "spikes = round(neurons * mean_rate_hz * window_s); 23 pJ/spike",
        },
        "meta": meta_common(
            id="nelb-r17-052",
            clock_domain="ws-hss-campaign-relative-ms-t0-2026-03-07T01:00:00Z",
            tags=["mems-accelerometer-array", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2"],
        ),
    }


def rec_053():
    raster = make_raster(
        neurons=25,
        mean_rate_hz=40.0,
        window_ms=36.0,
        seed=20260918,
        source="op7.brine_mu.hodoscope",
        target="tallowfen.hangup_gate",
        table=[
            {"from": "paddle_open_occ", "to": "density_reconstructor", "weight": 1.45},
            {"from": "cam_seis_witness", "to": "hangup_identity_core", "weight": 1.10},
            {"from": "lodeveil_cloud", "to": "blast_advocate", "weight": 0.55},
        ],
        third_factor={
            "modulator": "da.density_mismatch",
            "tau_e_s": 2.0,
            "tau_e_ms": 2000.0,
            "eligibility": "pre-post coincidence on hang-up synapses; the mismatch modulator depresses blast-advocate links when plant-owned density and camera/seismic witnesses disagree with the vendor opacity map inside tau_e",
        },
        channel_prefix="mu.n",
        anchor="OP-7 Brine-μ 36 ms frame at the occupied-paddle update (t_s 7200) where reconstructed 2.14 g/cm³ contradicts Lodeveil 2.72",
    )
    w_s = 0.036
    events = [
        ev(0.0, "mu.open", 1840.0, code="N_OPEN", units="counts", note="20 min open-sky equivalent on Brine-μ 3; HIL phantom plus live OP-7"),
        ev(6.0e5, "mu.occ", 920.0, code="N_OCC", units="counts", note="occupied chord through OP-7; N_occ/N_open = 0.5"),
        ev(1.2e6, "rho.recon", 2.14, code="RHO", units="g_cm3", note="ln(1840/920)/0.3239 = 2.14; broken-ore fill"),
        ev(1.8e6, "cam.trickle", 1.0, code="DRAWPOINT_WET", units="bool", note="plant-owned drawpoint camera still seeing trickle"),
        ev(2.4e6, "seis.hz", 0.4, code="PASS_SEISMIC", units="Hz", note="no 8-12 Hz stick-slip hang-up signature"),
        ev(3.0e6, "cal.pe", 0.94, code="PHANTOM_RHO", units="g_cm3", note="HIL polyethylene block; plant-owned, not Lodeveil-writable"),
        ev(3.6e6, "vend.k", 0.255, code="K_STEEL", units="m_inv", note="Lodeveil still on the steel-liner attenuation constant"),
        ev(4.8e6, "vend.cloud", 2.72, code="RHO_CLOUD", units="g_cm3", note="ln(2)/0.255 = 2.72; wrong-k map, not a hang-up"),
        ev(6.0e6, "boss.prop", 1.0, code="BLAST_180KG", units="bool", note="shift boss: fire 180 kg ANFO to clear the supposed hang-up"),
        ev(7.2e6, "rho.recon", 2.14, code="RHO", units="g_cm3", note="raster frame; plant-owned reconstruction unchanged"),
        ev(7.26e6, "mu.hit", 4.2, code="PADDLE_HITS", units="hits_per_36ms", note="first occupied-paddle packet"),
        ev(7.2612e6, "mu.hit", 3.4, code="PADDLE_HITS", units="hits_per_36ms", note="same-channel refractory 1.2 ms; adapted"),
        ev(7.2626e6, "mu.hit", 2.7, code="PADDLE_HITS", units="hits_per_36ms", note="third hit; adapted"),
        ev(7.8e6, "cam.trickle", 1.0, code="DRAWPOINT_WET", units="bool"),
        ev(8.4e6, "gate.blast", 1.0, code="REJECT", units="decision", note="refuse the secondary blast; wrong-k map is not a hang-up"),
        ev(9.0e6, "anfo.lock", 180.0, code="KG_LOCKED", units="kg"),
        ev(10.2e6, "grizzly.on", 1.0, code="GRIZZLY", units="bool"),
        ev(11.4e6, "draw.iso", 1.0, code="DRAWPOINT_ISO", units="bool"),
        ev(12.6e6, "gate.iso", 1.0, code="MODIFY", units="decision", note="companion t2: isolate drawpoint, no blast"),
        ev(13.8e6, "mu.open", 1832.0, code="N_OPEN", units="counts"),
        ev(15.0e6, "mu.occ", 928.0, code="N_OCC", units="counts"),
        ev(16.2e6, "rho.recon", 2.13, code="RHO", units="g_cm3"),
        ev(17.4e6, "cam.trickle", 1.0, code="DRAWPOINT_WET", units="bool"),
        ev(18.6e6, "seis.hz", 0.3, code="PASS_SEISMIC", units="Hz"),
        ev(19.8e6, "vend.freeze", 1.0, code="K_FROZEN", units="bool", note="Lodeveil k frozen pending rock-constant reload"),
        ev(21.0e6, "cal.pe", 0.94, code="PHANTOM_RHO", units="g_cm3"),
        ev(22.2e6, "rho.recon", 2.14, code="RHO", units="g_cm3"),
        ev(23.4e6, "gate.blast", 1.0, code="REJECT_HELD", units="decision"),
        ev(24.6e6, "tonnes.held", 0.0, code="T_NOT_BLASTED", units="t", note="zero tonnes 'cleared' because there was no hang-up"),
        ev(25.8e6, "vend.cloud", 2.72, code="RHO_CLOUD_STALE", units="g_cm3"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r17-053-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "TF-OP7-2026-0412",
            "domain": "cosmic_ray_muon_tomography_ore_pass",
            "setting": "Tallowfen Copper, 540 m level, ore-pass OP-7 (invented). Brine-μ 3 plant-owned scintillator hodoscopes on a 12 m surveyed chord. Hardware-in-the-loop: the telescope also views a polyethylene density phantom (0.94 g/cm³) while live OP-7 counts stream. Lodeveil cloud is the vendor opacity map, still loaded with the steel-liner attenuation constant.",
            "observables_at_decision": {
                "n_open": 1840.0,
                "n_occ": 920.0,
                "rho_recon_g_cm3": 2.14,
                "rho_cloud_g_cm3": 2.72,
                "k_plant": 0.3239,
                "k_vendor": 0.255,
                "drawpoint_trickle": True,
                "seismic_hz": 0.4,
            },
            "margin_authority": "secondary blast requires reconstructed rho >= 2.55 AND dry drawpoint camera AND 8-12 Hz hang-up seismic. A vendor opacity map using k_steel cannot substitute.",
        },
        "proposed_action": {
            "actor": "shift boss, citing Lodeveil 2.72 g/cm³ as an intact hang-up",
            "summary": "fire 180 kg ANFO into OP-7 to clear the blockage; hold the drawpoint until after the shot",
            "basis_claimed": "the cloud map is the system of record for pass opacity and it reads 2.72, matching intact andesite 2.71",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "The secondary blast is refused. Plant-owned reconstruction is 2.14 g/cm³ (ln(1840/920)/0.3239, serialized) — broken-ore fill, not intact hang-up 2.71. Lodeveil 2.72 is the same counts run through k_steel 0.255 left over from a liner campaign (ln(2)/0.255 = 2.72). Drawpoint camera still trickles and seismic is 0.4 Hz, not 8-12 Hz stick-slip. All three blast predicates fail. The HIL polyethylene phantom still reads 0.94 on the plant paddles, so the telescope is not blind. Ordered: lock the 180 kg ANFO, freeze Lodeveil k, isolate the drawpoint behind a grizzly (companion). Do not use vendor opacity to authorize explosives until k_rock is reloaded and agrees with the plant reconstruction.",
            "threshold": "blast requires rho>=2.55 AND camera_dry AND seismic_hangup; all three failed",
            "stated_residuals": "pass remains on trickle; vendor map stays 2.72 until k reload; innocence of a hang-up is not a claim that OP-7 is empty",
        },
        "executed_action": {
            "summary": "REJECT at t_s 8400: ANFO locked, Lodeveil k frozen, drawpoint isolation armed",
            "tool": "op7-muon-blast-gate-cli",
            "observation": "repeat counts 1832/928 still reconstruct 2.13-2.14; camera trickle held; no shot fired; 0 t 'cleared'",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 0.0, "event": "N_open 1840, N_occ 920, rho 2.14"},
                {"t_s": 3600.0, "event": "vendor k_steel 0.255 still loaded"},
                {"t_s": 4800.0, "event": "Lodeveil map 2.72"},
                {"t_s": 6000.0, "event": "180 kg ANFO proposed"},
                {"t_s": 7200.0, "event": "raster frame; plant rho still 2.14"},
                {"t_s": 8400.0, "event": "REJECT"},
                {"t_s": 12600.0, "event": "companion isolation MODIFY"},
            ],
            "observed_effects": [
                "wrong-k is event-decodable: vend.k 0.255 then vend.cloud 2.72 equals ln(2)/0.255",
                "plant reconstruction and camera/seismic never moved with the cloud map",
                "zero tonnes blasted is the priced non-event",
            ],
            "surprises": [
                "the cloud number 2.72 is 0.01 from intact andesite 2.71 — pairing of a leftover constant with a geology table, not physics",
            ],
            "new_state": {
                "anfo": "locked",
                "lodeveil_k": "frozen pending rock-constant reload",
                "op7": "trickle, grizzly armed",
            },
            "latency_ms": 0.0,
        },
        "reward_components": reward(
            0.43,
            [
                ("wrong_k_reconstruction", 0.15),
                ("blast_predicate_conjunction", 0.13),
                ("vendor_map_nonsubstitution", 0.10),
                ("anfo_lock", 0.08),
                ("throughput_deferral", -0.03),
            ],
            "scored for refusing explosives on a recomputable muon density while a vendor map using k_steel looked like a hang-up",
        ),
        "meta": meta_common(
            tags=["REJECT", "cosmic-ray-muon-tomography", "wrong-k", "ore-pass"],
            distillation_note="muon gate: serialized ln(N_open/N_occ)/k_rock beats a vendor map that still carries k_steel; camera and seismic are the independent witnesses",
        ),
    }
    traj2 = {
        "id": "nelb-r17-053-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "TF-OP7-2026-0412-iso",
            "domain": "drawpoint_isolation_execution",
            "setting": "Same OP-7 after the REJECT. Operational isolation of the drawpoint behind a grizzly; not a second vote on the blast.",
            "observables_at_decision": {
                "anfo_locked_kg": 180.0,
                "rho_g_cm3": 2.14,
                "trickle": True,
            },
        },
        "proposed_action": {
            "actor": "level supervisor following the REJECT",
            "summary": "install the grizzly, keep the drawpoint on trickle, do not fire; reload k_rock before any vendor map is evidentiary",
            "basis_claimed": "REJECT already forbade the shot; isolation is the remaining operational envelope",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "The pass is not left as-found: a hanging-wall slough is still possible on broken-ore fill. MODIFY the isolation line-up — grizzly on, drawpoint metered, ANFO locked — rather than ACCEPTing an unmodified resume of full draw. Do not treat isolation as permission to blast later without a fresh reconstruction.",
            "threshold": "grizzly_on AND anfo_locked AND no_shot; full-draw resume forbidden until rho and witnesses agree",
        },
        "executed_action": {
            "summary": "grizzly on at t_s 10200; drawpoint isolated at 11400; companion MODIFY at 12600",
            "tool": "op7-drawpoint-iso-exec",
            "observation": "trickle continued; no ANFO movement; plant rho 2.13-2.14",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 9000.0, "event": "ANFO locked"},
                {"t_s": 10200.0, "event": "grizzly on"},
                {"t_s": 12600.0, "event": "MODIFY isolation line-up"},
            ],
            "observed_effects": ["no shot", "vendor map tagged non-evidentiary for explosives"],
            "new_state": {"drawpoint": "metered behind grizzly", "vendor_opacity": "log-only"},
            "latency_ms": 3600000.0,
        },
        "reward_components": reward(
            0.32,
            [
                ("isolation_lineup", 0.12),
                ("no_shot_held", 0.11),
                ("k_freeze", 0.09),
            ],
            "operational companion: isolate the pass without re-opening the blast call",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "drawpoint-iso"]),
    }
    return {
        "id": "nelb-r17-053",
        "spike_events": events,
        "language_view": {
            "description": "Tallowfen OP-7 cosmic-ray muon tomography. Plant-owned Brine-μ paddles reconstruct 2.14 g/cm³ (broken ore) while Lodeveil still maps 2.72 using leftover k_steel. Shift boss proposes a 180 kg ANFO secondary blast. The gate REJECTs; a companion MODIFY isolates the drawpoint behind a grizzly. Distinct from 2026-08-30 r01 dry-cask muon CoK: this is an ore-pass hang-up / wrong-k explosives gate on HIL.",
            "trajectory": traj,
            "trajectory_drawpoint_isolation_execution": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "mu.open / mu.occ": "open and occupied paddle counts the reconstruction consumes",
                "rho.recon": "serialized column density g/cm³; amplitude is the model output",
                "vend.k / vend.cloud": "vendor attenuation constant and opacity map; the denial channel",
                "cam.trickle / seis.hz": "independent witnesses nobody at Lodeveil can write",
                "cal.pe": "HIL polyethylene phantom 0.94 g/cm³",
                "boss.prop / gate.blast / gate.iso": "proposal, REJECT, companion MODIFY",
                "anfo.lock / grizzly.on / draw.iso": "execution channels",
                "mu.hit": "occupied-paddle hits per 36 ms, including a 1.2 ms adapted triplet",
            },
            "temporal_motifs": [
                "cloud-sick while plant-healthy: vend.cloud 2.72 adjacent to rho.recon 2.14",
                "wrong-k as event: vend.cloud 2.72 equals ln(2)/0.255",
                "REJECT then operational MODIFY: gate.blast at 8400 s, gate.iso at 12600 s",
                "adapted paddle triplet at 1.2 ms spacing encodes occupancy at raster scale",
            ],
            "language_to_spike_mapping": "'cloud says hang-up' = vend.cloud 2.72; 'broken ore' = rho.recon 2.14; 'refuse the shot' = gate.blast REJECT; 'isolate the pass' = grizzly.on then companion MODIFY",
            "why_high_value": "New cosmic-ray muon family versus r01 sealed dry-cask CoK: ore-pass hang-up, explosives authorization, wrong-k (k_steel vs k_rock) as the convictable defect, HIL phantom as an unwritable witness. Not r13 VRFB collusion; the vendor error is a leftover constant, not an ACL patch.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 20260918, "stream_note": "stream amplitudes are authored constants (counts, g/cm3, Hz) plus mu.hit adaptation 0.82**k"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "8x8 paddles exist; stream keeps open/occ totals and one hit channel; rho.recon keeps 4 ticks",
                "refractory_floors_ms": {
                    "mu.open": 60000,
                    "mu.occ": 60000,
                    "rho.recon": 60000,
                    "cam.trickle": 60000,
                    "seis.hz": 60000,
                    "cal.pe": 60000,
                    "vend.k": 60000,
                    "vend.cloud": 60000,
                    "boss.prop": 60000,
                    "gate.blast": 60000,
                    "anfo.lock": 60000,
                    "grizzly.on": 60000,
                    "draw.iso": 60000,
                    "gate.iso": 60000,
                    "vend.freeze": 60000,
                    "tonnes.held": 60000,
                    "mu.hit": 0.8,
                },
                "time_alias": "t_rel_ms; t0 = 2026-04-12T06:00:00Z campaign start",
            },
            "distillation_targets": [
                "serialized muon density head: ln(N_open/N_occ)/k_rock = rho",
                "wrong-k detector: vendor rho equals ln(ratio)/k_steel",
                "conjunctive blast SOP: rho AND camera AND seismic, never vendor-map substitution",
            ],
        },
        "reconstruction_model": {
            "name": "brine_mu_column_density",
            "formula": "rho_g_cm3 = ln(N_open / N_occ) / k_atten",
            "parameters": {"k_atten_rock": 0.3239, "k_atten_steel": 0.255},
            "worked_example": {
                "N_open": 1840.0,
                "N_occ": 920.0,
                "rho_plant": 2.14,
                "rho_vendor": 2.72,
            },
            "check": "ln(1840/920)/0.3239 = 2.14; ln(2)/0.255 = 2.72",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 36.0,
            "decision_window_s": 0.036,
            "code": "op7.muon_blast_gate",
            "note": "REJECT accumulator wins: plant density plus camera/seismic overpower the vendor-map blast advocate",
            "populations": [
                gate_pop("muon_density_evidence", 100, 1.5, 50.0, w_s),
                gate_pop("camera_seismic_evidence", 50, 1.1, 25.0, w_s),
                gate_pop("blast_advocate", 40, 0.9, 25.0, w_s),
                gate_pop("reject_accumulator", 80, 1.6, 50.0, w_s),
            ],
        },
        "gate_compute": {
            "per_check": [
                {
                    "check": "op7.density_scorer",
                    "neurons": 80,
                    "mean_rate_hz": 50.0,
                    "window_ms": 36.0,
                    "window_s": 0.036,
                    "spikes": 144,
                },
                {
                    "check": "op7.witness_scorer",
                    "neurons": 50,
                    "mean_rate_hz": 40.0,
                    "window_ms": 36.0,
                    "window_s": 0.036,
                    "spikes": 72,
                },
            ],
            "total_spikes": 216,
            "total_energy_pJ": 4968,
            "total_energy_uJ": 0.004968,
            "model": "spikes = round(neurons * mean_rate_hz * window_s); 23 pJ/spike",
        },
        "meta": meta_common(
            id="nelb-r17-053",
            clock_domain="tf-op7-hil-relative-ms-t0-2026-04-12T06:00:00Z",
            tags=["cosmic-ray-muon-tomography", "REJECT", "MODIFY", "wrong-k", "operational-t2"],
        ),
    }


def rec_054():
    raster = make_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=28.0,
        seed=20260919,
        source="mkd14.dr450.panel",
        target="quernholt.iqi_gate",
        table=[
            {"from": "snr_iqi", "to": "penetrameter_reconstructor", "weight": 1.35},
            {"from": "two_angle_pair", "to": "lot_ship_core", "weight": 1.20},
            {"from": "takt_advocate", "to": "skip_scan_core", "weight": 0.45},
        ],
        third_factor={
            "modulator": "ach.iqi_eligibility",
            "tau_e_s": 1.2,
            "tau_e_ms": 1200.0,
            "eligibility": "pre-post coincidence on ship synapses; the IQI modulator enables potentiation only while 1T penetrameter visibility and a 2-angle pair are co-active inside tau_e",
        },
        channel_prefix="xr.n",
        anchor="DR-450 28 ms frame at disk 12 angle-B SNR 10.5 (t_s 5400) where D_visible 0.25 mm first clears 1T",
    )
    w_s = 0.028
    events = [
        ev(0.0, "kv.set", 450.0, code="KVP", units="kV", note="Quernholt DR-450, IN-718 disks 25.0 mm"),
        ev(3.0e5, "ma.set", 4.2, code="MA", units="mA"),
        ev(6.0e5, "disk.id", 1.0, code="DISK_N", units="count"),
        ev(1.2e6, "snr.a", 10.4, code="SNR", units="ratio", note="disk 1 angle A"),
        ev(1.8e6, "snr.b", 10.6, code="SNR", units="ratio", note="disk 1 angle B"),
        ev(2.4e6, "dvis.recon", 0.25, code="D_VIS_MM", units="mm", note="(10.5-2.5)/32 = 0.25; 1T of 25 mm"),
        ev(3.0e6, "ind.max", 0.12, code="IND_MM", units="mm", note="max indication under 0.40 mm ship floor"),
        ev(3.6e6, "disk.done", 6.0, code="N_TWO_ANGLE", units="count"),
        ev(4.2e6, "snr.a", 10.3, code="SNR", units="ratio", note="disk 12 angle A"),
        ev(5.4e6, "snr.b", 10.5, code="SNR", units="ratio", note="disk 12 angle B; raster frame"),
        ev(5.4012e6, "det.after", 1.82, code="AFTERGLOW", units="adu", note="panel afterglow packet; 1.2 ms"),
        ev(5.4026e6, "det.after", 1.49, code="AFTERGLOW", units="adu", note="adapted 1.4 ms later"),
        ev(5.52e6, "dvis.recon", 0.25, code="D_VIS_MM", units="mm", note="(10.5-2.5)/32 = 0.25 exactly"),
        ev(5.64e6, "teq.pct", 1.00, code="T_EQ_PCT", units="pct", note="0.25/25.0*100 = 1.00; 1T, required 2T"),
        ev(5.76e6, "ind.max", 0.18, code="IND_MM", units="mm"),
        ev(6.0e6, "disk.done", 12.0, code="N_TWO_ANGLE", units="count"),
        ev(6.6e6, "ops.prop", 1.0, code="SHIP_12", units="bool", note="NDT supervisor: ship the 12 that passed 2-angle + 1T"),
        ev(7.2e6, "gate.ship", 1.0, code="ACCEPT", units="decision", note="bounded ship of 12; remainder still open"),
        ev(7.8e6, "takt.prop", 8.0, code="SKIP_REMAINING", units="count", note="production: skip 2nd angle on remaining 8 to save 96 min"),
        ev(8.4e6, "gate.skip", 1.0, code="REJECT", units="decision", note="companion t2: refuse skip-scan"),
        ev(9.0e6, "lot.hold", 8.0, code="N_HELD", units="count"),
        ev(9.6e6, "cert.12", 12.0, code="N_SHIPPED", units="count"),
        ev(10.2e6, "snr.a", 9.1, code="SNR", units="ratio", note="disk 13 angle A only; 2nd angle not taken"),
        ev(10.8e6, "dvis.recon", 0.206, code="D_VIS_MM", units="mm", note="(9.1-2.5)/32 = 0.206; still 1T-class but unpaired"),
        ev(11.4e6, "teq.pct", 0.82, code="T_EQ_PCT", units="pct", note="unpaired; not a ship input"),
        ev(12.0e6, "gate.ship", 1.0, code="ACCEPT_HELD", units="decision"),
        ev(12.6e6, "gate.skip", 1.0, code="REJECT_HELD", units="decision"),
        ev(13.2e6, "takt.saved", 0.0, code="MIN_SAVED", units="min", note="zero minutes saved; 2nd-angle requirement held"),
        ev(13.8e6, "ind.max", 0.18, code="IND_MM", units="mm"),
        ev(14.4e6, "kv.set", 450.0, code="KVP", units="kV"),
        ev(15.0e6, "ma.set", 4.2, code="MA", units="mA"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r17-054-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "QH-DR-2026-0519",
            "domain": "industrial_xray_dr_iqi",
            "setting": "Quernholt Castings, cabinet DR-450 (450 kV, invented). IN-718 turbine disks 25.0 mm, lot MK-D14 (20 off). Simulated digital-radiography campaign with a serialized penetrameter model. 12 disks have completed 2-angle pairs; 8 remain.",
            "observables_at_decision": {
                "snr_angle_b": 10.5,
                "d_visible_mm": 0.25,
                "t_eq_pct": 1.00,
                "ind_max_mm": 0.18,
                "n_two_angle": 12,
                "required_t_eq_pct": 2.00,
                "ship_ind_floor_mm": 0.40,
            },
            "margin_authority": "ship requires 2-angle pair AND t_eq_pct <= 2.00 (2T or better) AND max indication < 0.40 mm. A takt argument cannot drop the 2nd angle.",
        },
        "proposed_action": {
            "actor": "NDT supervisor, citing 12 completed pairs and 1T visibility",
            "summary": "certify and ship the 12 disks that already have 2-angle DR with 1T penetrameter visibility and no indication >= 0.40 mm",
            "basis_claimed": "IQI 1T is tighter than the 2T procedure; indications 0.12-0.18 mm are under the 0.40 mm floor",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "The 12-disk ship is earned and bounded. Serialized penetrameter: D_visible = (SNR-2.5)/32 = (10.5-2.5)/32 = 0.25 mm, t_eq = 0.25/25.0*100 = 1.00 percent (1T), which is tighter than the required 2.00 percent (2T). Max indication 0.18 mm is under 0.40 mm. Every shipped disk has an angle-A and angle-B pair in the stream. ACCEPT the 12. Explicit residual: the remaining 8 are not in this accept; a skip-scan of those 8 is a separate companion and is refused there. 1T on an unpaired single angle (disk 13 SNR 9.1) is not a ship input.",
            "threshold": "2-angle AND t_eq_pct<=2.00 AND ind_max<0.40 mm; scope = disks with both angles",
            "stated_residuals": "8 disks still need angle B; ACCEPT does not extend to them; disk 13 unpaired SNR is archived not shipped",
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 7200: 12 disks certified; lot remainder held",
            "tool": "qh-dr450-ship-gate-cli",
            "observation": "certificates 12; remainder 8 on hold; unpaired disk-13 SNR 9.1 not used as a ship input",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 2400.0, "event": "first 1T reconstruction 0.25 mm"},
                {"t_s": 5400.0, "event": "disk 12 angle B SNR 10.5; raster frame"},
                {"t_s": 6000.0, "event": "12 two-angle completions"},
                {"t_s": 6600.0, "event": "ship-12 proposed"},
                {"t_s": 7200.0, "event": "ACCEPT 12"},
                {"t_s": 8400.0, "event": "companion skip-scan REJECT"},
            ],
            "observed_effects": [
                "penetrameter 1T recomputes from SNR at every dvis.recon event",
                "ACCEPT is scoped to the 12 pairs; remainder stays open",
                "unpaired disk-13 SNR is present and is not treated as a 2-angle substitute",
            ],
            "surprises": [
                "production's 96 min takt save would have been a skip of the same 2nd angle the 12 already paid for",
            ],
            "new_state": {
                "mk_d14_shipped": 12,
                "mk_d14_held": 8,
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 0.0,
        },
        "reward_components": reward(
            0.38,
            [
                ("iqi_reconstruction", 0.13),
                ("two_angle_scope", 0.12),
                ("bounded_accept", 0.10),
                ("indication_floor", 0.06),
                ("remainder_not_laundered", -0.03),
            ],
            "scored for an earned 1T/2-angle ACCEPT whose scope cannot swallow the unpaired remainder",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "industrial-xray", "iqi-1T", "bounded-ship"],
            distillation_note="DR ship gate: serialized (SNR-2.5)/32 penetrameter plus 2-angle pairing; ACCEPT is bounded to paired disks",
        ),
    }
    traj2 = {
        "id": "nelb-r17-054-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "QH-DR-2026-0519-skip",
            "domain": "remaining_lot_skip_scan",
            "setting": "Same MK-D14 after the 12-disk ACCEPT. Operational refusal of a skip-scan on the remaining 8; not a re-vote on the 12.",
            "observables_at_decision": {
                "n_remaining": 8,
                "takt_save_min": 96.0,
                "disk13_snr_a": 9.1,
                "disk13_paired": False,
            },
        },
        "proposed_action": {
            "actor": "production control, citing takt and disk-13 angle-A already at 1T-class SNR",
            "summary": "skip angle B on the remaining 8 disks to save 96 minutes; treat unpaired 1T-class SNR as equivalent to a pair",
            "basis_claimed": "the 12 already proved the technique; repeating angle B is waste",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Skip-scan is refused. The lead ACCEPT was scoped to disks that already have both angles; it is not a technique waiver for the remainder. Disk 13 has only angle A (SNR 9.1 → D_visible 0.206 mm) and is unpaired. SOP requires the pair, not a single-angle 1T-class number. Ordered: hold the 8, take angle B, then re-enter the ship gate per disk. Zero minutes of takt are saved.",
            "threshold": "remainder ship requires angle B; unpaired SNR cannot substitute",
        },
        "executed_action": {
            "summary": "REJECT at t_s 8400: 8 held; angle-B queue kept; 0 min takt saved",
            "tool": "qh-dr450-skip-scan-cli",
            "observation": "no certificate issued for 13-20; disk-13 unpaired SNR archived only",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 7800.0, "event": "skip-scan of 8 proposed"},
                {"t_s": 8400.0, "event": "REJECT skip-scan"},
                {"t_s": 13200.0, "event": "0 min saved held"},
            ],
            "observed_effects": ["12-disk ACCEPT did not leak onto the remainder", "2nd-angle requirement survived takt pressure"],
            "new_state": {"remainder": "held for angle B", "takt_saved_min": 0.0},
            "latency_ms": 0.0,
        },
        "reward_components": reward(
            0.36,
            [
                ("skip_scan_refusal", 0.14),
                ("scope_hygiene", 0.12),
                ("unpaired_nonsubstitution", 0.10),
            ],
            "operational companion: refuse skip-scan rather than re-arguing the 12-disk ship",
        ),
        "meta": meta_common(tags=["REJECT", "operational-execution", "skip-scan"]),
    }
    return {
        "id": "nelb-r17-054",
        "spike_events": events,
        "language_view": {
            "description": "Quernholt DR-450 industrial x-ray of IN-718 disks. Twelve 2-angle pairs reconstruct 1T penetrameter visibility (0.25 mm / 1.00 percent) with indications under 0.40 mm. The gate ACCEPTs a bounded ship of those 12. Production then proposes skipping angle B on the remaining 8; a companion REJECT holds the 2nd-angle requirement. Distinct from r03 LPBF melt-pool photodiodes: this is transmission DR + IQI, not melt-pool monitoring.",
            "trajectory": traj,
            "trajectory_remaining_lot_skip_scan": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "snr.a / snr.b": "per-angle SNR the penetrameter reconstruction consumes",
                "dvis.recon / teq.pct": "serialized D_visible mm and t-equivalent percent",
                "ind.max": "max indication mm; ship floor 0.40",
                "disk.done / cert.12 / lot.hold": "pair count, shipped count, held remainder",
                "ops.prop / gate.ship / takt.prop / gate.skip": "ship proposal, ACCEPT, skip proposal, companion REJECT",
                "det.after": "panel afterglow ADU, including a 1.2 ms adapted pair",
                "kv.set / ma.set": "technique channels",
            },
            "temporal_motifs": [
                "1T as event: dvis.recon 0.25 equals (10.5-2.5)/32",
                "bounded ACCEPT then skip REJECT: gate.ship at 7200 s, gate.skip at 8400 s",
                "unpaired SNR is present and is not a pair: disk 13 snr.a 9.1 after the ACCEPT",
                "adapted afterglow pair at 1.2 ms spacing encodes the raster-scale panel",
            ],
            "language_to_spike_mapping": "'1T visibility' = dvis.recon 0.25 and teq.pct 1.00; 'ship the 12' = gate.ship ACCEPT; 'skip the rest' = takt.prop 8; 'refuse skip' = gate.skip REJECT",
            "why_high_value": "New industrial x-ray DR family (not r03 LPBF photodiodes, not unused Co-60). First earned ACCEPT on a NELB lead this 2026-09-02 window with an explicit remainder residual. Serialized penetrameter plus 2-angle pairing; skip-scan companion is operational, not a governance vote.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 20260919, "stream_note": "stream amplitudes are authored constants (kV, SNR, mm, counts) plus det.after adaptation 0.82**k"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "20 disks exist; stream keeps disks 1/12/13 and aggregate counts; SNR keeps 5 of ~40 shots",
                "refractory_floors_ms": {
                    "kv.set": 60000,
                    "ma.set": 60000,
                    "disk.id": 60000,
                    "snr.a": 60000,
                    "snr.b": 60000,
                    "dvis.recon": 60000,
                    "teq.pct": 60000,
                    "ind.max": 60000,
                    "disk.done": 60000,
                    "ops.prop": 60000,
                    "gate.ship": 60000,
                    "takt.prop": 60000,
                    "gate.skip": 60000,
                    "lot.hold": 60000,
                    "cert.12": 60000,
                    "takt.saved": 60000,
                    "det.after": 0.8,
                },
                "time_alias": "t_rel_ms; t0 = 2026-05-19T08:00:00Z campaign start",
            },
            "distillation_targets": [
                "serialized penetrameter head: (SNR-2.5)/32 = D_visible_mm; D/T*100 = t_eq_pct",
                "bounded ACCEPT: 2-angle scope does not leak onto unpaired remainder",
                "skip-scan refusal: takt cannot substitute for angle B",
            ],
        },
        "reconstruction_model": {
            "name": "dr450_penetrameter_1t",
            "formula": "D_visible_mm = (SNR_px - SNR0) / k_snr; t_eq_pct = (D_visible_mm / T_disk_mm) * 100",
            "parameters": {"SNR0": 2.5, "k_snr": 32.0, "T_disk_mm": 25.0},
            "worked_example": {
                "SNR_px": 10.5,
                "D_visible_mm": 0.25,
                "t_eq_pct": 1.00,
            },
            "check": "(10.5-2.5)/32 = 0.25; 0.25/25.0*100 = 1.00 exactly",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 28.0,
            "decision_window_s": 0.028,
            "code": "qh.dr450_ship_gate",
            "note": "ACCEPT accumulator wins: 1T penetrameter plus 2-angle pairing overpower the takt skip advocate on the 12",
            "populations": [
                gate_pop("iqi_evidence", 80, 1.3, 50.0, w_s),
                gate_pop("two_angle_evidence", 50, 1.2, 50.0, w_s),
                gate_pop("skip_scan_advocate", 40, 0.8, 25.0, w_s),
                gate_pop("accept_accumulator", 64, 1.5, 62.5, w_s),
            ],
        },
        "gate_compute": {
            "per_check": [
                {
                    "check": "qh.iqi_scorer",
                    "neurons": 64,
                    "mean_rate_hz": 50.0,
                    "window_ms": 28.0,
                    "window_s": 0.028,
                    "spikes": 90,
                },
                {
                    "check": "qh.pair_scorer",
                    "neurons": 40,
                    "mean_rate_hz": 50.0,
                    "window_ms": 28.0,
                    "window_s": 0.028,
                    "spikes": 56,
                },
            ],
            "total_spikes": 146,
            "total_energy_pJ": 3358,
            "total_energy_uJ": 0.003358,
            "model": "spikes = round(neurons * mean_rate_hz * window_s); 23 pJ/spike",
        },
        "meta": meta_common(
            id="nelb-r17-054",
            clock_domain="qh-dr450-sim-relative-ms-t0-2026-05-19T08:00:00Z",
            tags=["industrial-xray", "ACCEPT", "REJECT", "iqi-1T", "operational-t2"],
        ),
    }


BANNED_KEY_FRAGMENTS = HIDDEN
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


def walk_banned(obj, path=""):
    hits = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{path}.{k}" if path else k
            nk = str(k).casefold().replace("-", "_").replace(" ", "_")
            if nk in BANNED_KEY_FRAGMENTS or nk in {
                "thought",
                "scratch",
                "inner_monologue",
                "chain_of_thought",
            }:
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
    for rec in records:
        hits = walk_banned(rec)
        if hits:
            raise RuntimeError(f"banned keys {hits}")
        rights = rec["meta"]["rights"]
        if tuple(rights.keys()) != RIGHTS_KEYS:
            raise RuntimeError(f"{rec['id']} rights keys")
        if rights["intended_use"] != "research_only" or rights["linear_issue"] != "RM-793":
            raise RuntimeError(f"{rec['id']} rights values")
        if "RM-793" not in rights["status_basis"]:
            raise RuntimeError("status_basis")
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
        if abs(rast["spikes"] - exp) > 0:
            raise RuntimeError("raster budget")
        if abs(rast["energy_pJ"] - rast["spikes"] * 23) > 1e-6:
            raise RuntimeError("energy pJ")
        if abs(rast["energy_uJ"] - rast["spikes"] * 23e-6) > 1e-9:
            raise RuntimeError("energy uJ")
        tf = rast["routing"]["third_factor"]
        if abs(tf["tau_e_ms"] / 1000.0 - tf["tau_e_s"]) > 1e-9:
            raise RuntimeError("tau pair")
        isi = rast["isi_count_identity"]
        if isi["isi_total"] != isi["spikes"] - isi["distinct_active_neurons"]:
            raise RuntimeError("isi identity")
        if sum(b["count"] for b in rast["isi_histogram"]) != isi["isi_total"]:
            raise RuntimeError("isi hist sum")
        sim = lv["trajectory"]["state"]["sim_or_real"]
        if sim not in {"designed", "simulated", "hil"}:
            raise RuntimeError(sim)
        blob = json.dumps(rec)
        if "training_ready" in blob:
            raise RuntimeError("training_ready claimed")
        gc = rec["gate_compute"]
        if gc["total_spikes"] != sum(p["spikes"] for p in gc["per_check"]):
            raise RuntimeError("gate_compute total")
        if gc["total_energy_pJ"] != gc["total_spikes"] * 23:
            raise RuntimeError("gate_compute pJ")
        if abs(gc["total_energy_uJ"] - gc["total_spikes"] * 23e-6) > 1e-12:
            raise RuntimeError("gate_compute uJ")
        for pop in rec["gate_snn"]["populations"]:
            dw = rec["gate_snn"]["decision_window_s"]
            exp_p = int(round(pop["neurons"] * pop["mean_rate_hz"] * dw))
            if pop["spikes"] != exp_p:
                raise RuntimeError(f"gate pop {pop['name']}")
    if len(ids) != len(set(ids)):
        raise RuntimeError(f"dup ids {ids}")
    print("local_checks ok", [r["id"] for r in records], "ids", len(ids))


def main():
    records = [rec_052(), rec_053(), rec_054()]
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
