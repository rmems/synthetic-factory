#!/usr/bin/env python3
"""Generate NELB round-21 research-only bridge pairs (do not write outputs/raw/)."""

from __future__ import annotations

import json
import math
import random
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

OUT_DIR = Path("/tmp/nelb-r21")
BATCH = OUT_DIR / "batch-r21.jsonl"
NOTES = OUT_DIR / "NOTES-r21.md"
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
    "hidden_reasoning",
    "scratchpad",
    "scratch",
    "internal_monologue",
    "private_reasoning",
    "inner_monologue",
}


def meta_common(**extra):
    m = {
        "round": 21,
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


def gc_check(name, neurons, mean_rate_hz, window_ms):
    window_s = window_ms / 1000.0
    spikes = int(round(neurons * mean_rate_hz * window_s))
    return {
        "check": name,
        "neurons": neurons,
        "mean_rate_hz": float(mean_rate_hz),
        "window_ms": float(window_ms),
        "window_s": float(window_s),
        "spikes": spikes,
    }


def gate_compute(checks):
    total = sum(c["spikes"] for c in checks)
    return {
        "per_check": checks,
        "total_spikes": total,
        "total_energy_pJ": total * 23,
        "total_energy_uJ": total * 23e-6,
        "model": "spikes = round(neurons * mean_rate_hz * window_s); 23 pJ/spike",
    }


# ---------------------------------------------------------------------------
# Record 064 — THz-TDS radome bondline, designed, MODIFY
# ---------------------------------------------------------------------------
def rec_064():
    raster = make_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=36.0,
        seed=20260964,
        source="fb4.thz.tds",
        target="fernbrake.bondline_core",
        table=[
            {"from": "echo_delay_ps", "to": "bondline_thickness_estimator", "weight": 1.45},
            {"from": "backwall_amplitude", "to": "disbond_advocate", "weight": 1.10},
            {"from": "bag_vacuum", "to": "flight_release_advocate", "weight": 0.45},
        ],
        third_factor={
            "modulator": "na.bondline_delay_salience",
            "tau_e_s": 1.6,
            "tau_e_ms": 1600.0,
            "eligibility": "pre-post coincidence on bondline synapses; the delay modulator enables potentiation only while optical delay and weak back-wall echo are co-active inside tau_e, so a healthy bag-vacuum cannot hide a disbond",
        },
        channel_prefix="thz.n",
        anchor="Fernbrake FB-4 THz-TDS 36 ms frame at back-wall delay 4.80 ps (t_s 780); first disbond-trip sample",
    )
    w_s = 0.036
    c_um_ps = 300.0
    n_index = 1.60
    dt_ps = 4.80
    d_um = (c_um_ps * dt_ps) / (2.0 * n_index)  # 450.0
    dt_ref_ps = 1.92
    d_ref_um = (c_um_ps * dt_ref_ps) / (2.0 * n_index)  # 180.0
    events = [
        ev(0.0, "bag.vac", 0.95, code="BAG_BAR", units="bar", note="vacuum bag still seated; denial channel"),
        ev(60000.0, "ac.P", 6.20, code="AUTOCLAVE_BAR", units="bar"),
        ev(120000.0, "tds.n", 1.60, code="INDEX_N", units="1"),
        ev(180000.0, "tds.dt", 1.92, code="DT_REF", units="ps", note="reference coupon of the same load"),
        ev(240000.0, "d.recon", d_ref_um, code="D_REF_UM", units="um", note="300*1.92/(2*1.60)=180.0"),
        ev(300000.0, "tds.amp", 0.92, code="ECHO_AMP", units="norm"),
        ev(360000.0, "ir.uni", 0.04, code="IR_RMS", units="K", note="IR camera looks uniform"),
        ev(420000.0, "scan.start", 1.0, code="FB17_SCAN", units="bool"),
        ev(480000.0, "tds.dt", 2.40, code="DT_PS", units="ps"),
        ev(540000.0, "tds.amp", 0.71, code="ECHO_AMP", units="norm"),
        ev(600000.0, "bag.vac", 0.95, code="BAG_BAR", units="bar", note="vacuum never left 0.95"),
        ev(660000.0, "tds.dt", 3.60, code="DT_PS", units="ps"),
        ev(720000.0, "tds.amp", 0.52, code="ECHO_AMP", units="norm"),
        ev(780000.0, "tds.dt", 4.80, code="DT_TRIP", units="ps", note="4.80 ps; raster sidecar is this 36 ms frame"),
        ev(780001.2, "tds.echo", 1.10, code="ECHO_BURST", units="norm", note="back-wall burst; amplitude before adaptation"),
        ev(780002.4, "tds.echo", 0.90, code="ECHO_BURST", units="norm", note="same-channel refractory 1.2 ms; adapted 0.82x plus noise"),
        ev(780003.6, "tds.echo", 0.74, code="ECHO_BURST", units="norm", note="third echo; adapted"),
        ev(840000.0, "d.recon", d_um, code="D_UM", units="um", note="300*4.80/(2*1.60)=450.0 vs spec max 220"),
        ev(900000.0, "tds.amp", 0.28, code="ECHO_AMP", units="norm", note="back-wall 0.28 <= 0.40 floor"),
        ev(960000.0, "spec.max", 220.0, code="SPEC_UM", units="um"),
        ev(1020000.0, "ops.prop", 1.0, code="FLIGHT_RELEASE", units="bool", note="night QA: bag vacuum in spec, stamp the radome"),
        ev(1080000.0, "gate.tds", 1.0, code="MODIFY", units="decision"),
        ev(1140000.0, "peel.cmd", 1.0, code="PEEL_COUPON", units="bool"),
        ev(1200000.0, "q.unit", 1.0, code="QUARANTINE_FB17", units="bool"),
        ev(1800000.0, "peel.start", 1.0, code="PEEL_START", units="bool"),
        ev(2880000.0, "peel.floor", 18.0, code="PEEL_MIN", units="min", note="18.0 min peel floor is in the stream"),
        ev(2940000.0, "peel.N", 18.4, code="PEEL_FORCE", units="N", note="18.4 N vs 12 N disbond floor"),
        ev(3000000.0, "gate.exec", 1.0, code="ACCEPT", units="decision", note="companion t2: peel plus unit quarantine completed"),
        ev(3060000.0, "ship.ok", 1.0, code="LOAD_REMAINDER", units="bool", note="three sibling radomes stay in the ship-set"),
        ev(3120000.0, "sib.dt", 1.84, code="DT_SIBLING", units="ps", note="sibling max 1.84 ps < 2.20 cap"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r21-064-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "FB-TDS-2026-0902",
            "domain": "thz_tds_radome_bondline",
            "setting": "Fernbrake Composites, autoclave bay FB-4, quartz-epoxy radome FB-17. Transmission THz-TDS (0.1-3 THz, 40 fs pump) is the bondline SoT. Invented plant; designed coupon campaign. Not an FBG strain coil (r13 TW-17), not BOTDA hoop strain (r14 GF-11), not Rayleigh DAS (r4).",
            "observables_at_decision": {
                "delta_t_ps": 4.80,
                "n_index": 1.60,
                "d_um": d_um,
                "spec_max_um": 220.0,
                "echo_amp": 0.28,
                "bag_vac_bar": 0.95,
            },
            "margin_authority": "FB-4 bondline SOP rev C: if reconstructed thickness >= 250 um AND back-wall echo amplitude <= 0.40, flight-release is forbidden even if bag vacuum stays inside 0.90-1.00 bar",
        },
        "proposed_action": {
            "actor": "night QA lead, citing a seated 0.95 bar bag and a uniform IR camera",
            "summary": "stamp flight-release on FB-17; treat the 4.80 ps delay as a refractive-index drift of the epoxy, not a disbond",
            "basis_claimed": "bag vacuum is 0.95 bar and IR RMS is 0.04 K, both inside housekeeping limits",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Flight-release of FB-17 is refused, not the autoclave load. SOP rev C is conjunctive: reconstructed thickness is 450.0 um (300*4.80/(2*1.60), serialized) against a 220 um spec and a 250 um trip, and back-wall echo is 0.28 <= 0.40, while a vacuum-only head would still see 0.95 bar. Ordered: quarantine FB-17 only, peel-test a coupon from the same load, hold the three sibling radomes to a 2.20 ps delay cap. A seated bag cannot substitute for the delay reconstruction.",
            "threshold": "d_um>=250 AND echo_amp<=0.40 => forbid flight-release",
            "stated_residuals": "peel costs ~18 min and one coupon; sibling radomes are not cleared by this MODIFY until each has its own delay < 2.20 ps; n(T) compensation is not a release condition tonight",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 1080: FB-17 quarantined; peel commanded; siblings held to 2.20 ps",
            "tool": "fb4-tds-bondline-gate-cli",
            "observation": "bag still 0.95 bar; reconstructed 450.0 um never moved; peel force later 18.4 N over the 12 N disbond floor; siblings 1.84 ps",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 180.0, "event": "reference coupon delay 1.92 ps reconstructs 180.0 um"},
                {"t_s": 780.0, "event": "FB-17 delay 4.80 ps; raster frame captured"},
                {"t_s": 840.0, "event": "reconstructed thickness 450.0 um vs 220 spec"},
                {"t_s": 1080.0, "event": "MODIFY: quarantine FB-17 plus peel"},
                {"t_s": 3000.0, "event": "companion execution ACCEPT; 18 min peel floor observed"},
            ],
            "observed_effects": [
                "thickness reconstruction recomputes from serialized c, n, and delay at every d.recon event",
                "bag vacuum never left 0.95 bar, so a vacuum-only head would have ACCEPTed flight-release",
                "peel 18.4 N confirmed the disbond; the 450.0 um projection was realized on the coupon, not on a flying radome",
            ],
            "surprises": [
                "IR RMS stayed 0.04 K; a thermal-camera head would have missed the void that THz delay caught",
            ],
            "new_state": {
                "fb17": "quarantined pending bonded-repair disposition",
                "ship_set": "three siblings held under 2.20 ps cap",
                "reconstruction_model": "discharged as an on-record calculator, not a referenced envelope",
            },
            "latency_ms": 15000.0,
        },
        "reward_components": reward(
            0.41,
            [
                ("delay_reconstruction", 0.14),
                ("conjunctive_quarantine", 0.12),
                ("vacuum_nonsubstitution", 0.09),
                ("unit_not_load_scope", 0.08),
                ("peel_time_cost", -0.02),
            ],
            "scored for refusing flight-release on a recomputable THz delay while bag vacuum looked seated; peel_time_cost prices the 18 min floor",
        ),
        "meta": meta_common(
            tags=["MODIFY", "thz-tds-bondline", "serialized-reconstruction", "operational-companion"],
            distillation_note="THz-TDS gate: serialized delay-to-thickness plus weak echo beats a seated bag vacuum; companion t2 is the peel/quarantine execution, not a governance vote",
        ),
    }
    traj2 = {
        "id": "nelb-r21-064-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "FB-TDS-2026-0902-exec",
            "domain": "peel_quarantine_execution",
            "setting": "Same FB-4 after the MODIFY. This companion is the operational peel-test and unit quarantine, not a second policy vote.",
            "observables_at_decision": {
                "peel_cmd": True,
                "unit_quarantine": True,
                "peel_force_N": 18.4,
                "sibling_dt_ps": 1.84,
            },
        },
        "proposed_action": {
            "actor": "QA cell following the MODIFY",
            "summary": "execute peel on the load coupon and quarantine FB-17 only; keep siblings if delay < 2.20 ps",
            "basis_claimed": "MODIFY requirements are fully specified; peel fixture is in-envelope",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "The execution envelope is intact: peel force 18.4 N is over the 12 N disbond floor (the reconstruction is confirmed, not re-argued), FB-17 is the only quarantined unit, and sibling delay 1.84 ps is under the 2.20 ps cap. ACCEPT the sequence. Do not scrap the autoclave load; do not restore a flight-release stamp on FB-17 tonight.",
            "threshold": "peel_N>=12 AND quarantined_units==1 AND sibling_dt_ps<2.20",
        },
        "executed_action": {
            "summary": "peel started t_s 1800; 18.0 min floor at t_s 2880; 18.4 N; siblings kept; FB-17 remains quarantined",
            "tool": "fb4-peel-exec",
            "observation": "no load-wide scrap; flight-release stamp not re-entered on FB-17",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 1140.0, "event": "peel commanded"},
                {"t_s": 1800.0, "event": "peel start"},
                {"t_s": 2880.0, "event": "18.0 min peel floor in-stream"},
                {"t_s": 3000.0, "event": "companion ACCEPT"},
            ],
            "observed_effects": [
                "18.4 N peel confirmed the 450.0 um reconstruction without a second THz vote",
                "ship-set remainder stayed; FB-17 stamp not restored",
            ],
            "new_state": {"fb17_status": "quarantined", "siblings_in_set": 3},
            "latency_ms": 15000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("envelope_respect", 0.12),
                ("peel_floor_in_stream", 0.10),
                ("unit_scope_held", 0.08),
                ("stamp_not_reentered", 0.06),
                ("fixture_time_cost", -0.02),
            ],
            "operational execution gate: the companion does the peel rather than re-arguing the delay call",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "peel-quarantine"]),
    }
    return {
        "id": "nelb-r21-064",
        "spike_events": events,
        "language_view": {
            "description": "THz-TDS on Fernbrake radome FB-17. Back-wall delay 4.80 ps reconstructs 450.0 um of bondline against a 220 um spec while bag vacuum still reads 0.95 bar. The gate MODIFYs to a unit quarantine plus peel; a companion execution ACCEPT runs the 18 min peel floor and keeps the three sibling radomes. Thickness d = c*dt/(2n) is serialized so every d.recon amplitude recomputes from delay and index.",
            "trajectory": traj,
            "trajectory_peel_quarantine_execution": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "tds.dt / tds.echo / tds.amp / tds.n": "THz delay, burst, back-wall amplitude, refractive index",
                "d.recon": "serialized thickness um; amplitude is the model output",
                "bag.vac / ir.uni / ac.P": "vacuum, IR, autoclave; the denial channels that stay healthy",
                "ops.prop / gate.tds / gate.exec": "proposal, MODIFY, companion ACCEPT",
                "peel.cmd / peel.start / peel.floor / peel.N / q.unit": "execution channels for the operational companion",
                "sib.dt / ship.ok / spec.max": "sibling cap and spec",
            },
            "temporal_motifs": [
                "vacuum-healthy while delay-sick: bag.vac 0.95 adjacent to tds.dt 4.80 and d.recon 450.0",
                "reconstruction as event: d.recon 450.0 equals 300*4.80/(2*1.60)",
                "MODIFY then operational ACCEPT: gate.tds at 1080 s, gate.exec at 3000 s",
                "adapted echo triplet at 1.2 ms spacing encodes the disbond trip at raster scale",
                "18 min peel floor in-stream: peel.start 1800 s to peel.floor 2880 s",
            ],
            "language_to_spike_mapping": "'bag looks seated' = bag.vac 0.95; '450 um disbond' = d.recon 450.0; 'forbid flight-release' = gate.tds MODIFY; 'execute the peel' = peel.cmd then companion ACCEPT",
            "why_high_value": "New THz-TDS family (not r13 FBG glaze, not r14 BOTDA, not r4 DAS). Serializes a delay-to-thickness reconstruction that a vacuum-only head cannot see. Companion t2 is operational peel execution, not a governance vote.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 20260964, "stream_note": "stream amplitudes are authored constants (ps, um, bar, N) plus tds.echo adaptation 0.82**k"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "THz waveform is a picosecond trace; stream keeps delay, amplitude, and three echo samples of ~400 waveform bins",
                "refractory_floors_ms": {
                    "bag.vac": 60000,
                    "ac.P": 60000,
                    "tds.n": 60000,
                    "tds.dt": 60000,
                    "d.recon": 60000,
                    "tds.amp": 60000,
                    "ir.uni": 60000,
                    "scan.start": 60000,
                    "tds.echo": 0.8,
                    "spec.max": 60000,
                    "ops.prop": 60000,
                    "gate.tds": 60000,
                    "peel.cmd": 60000,
                    "q.unit": 60000,
                    "peel.start": 60000,
                    "peel.floor": 60000,
                    "peel.N": 60000,
                    "gate.exec": 60000,
                    "ship.ok": 60000,
                    "sib.dt": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-06-11T02:40:00Z autoclave-out scan",
            },
            "distillation_targets": [
                "serialized THz thickness head: d_um = c_um_ps * dt_ps / (2 n)",
                "conjunctive SOP head: thickness AND weak echo, never bag-vacuum substitution",
                "unit-not-load scope: quarantine one radome, keep siblings under a delay cap",
                "operational companion: execute peel without re-opening the delay call",
            ],
        },
        "reconstruction_model": {
            "name": "thz_tds_bondline_thickness",
            "formula": "d_um = c_um_ps * delta_t_ps / (2 * n_index)",
            "parameters": {
                "c_um_ps": 300.0,
                "n_index": 1.60,
                "spec_max_um": 220.0,
                "trip_um": 250.0,
                "echo_floor": 0.40,
            },
            "worked_example": {
                "delta_t_ps": 4.80,
                "d_um": d_um,
                "delta_t_ref_ps": 1.92,
                "d_ref_um": d_ref_um,
            },
            "check": "300*4.80/(2*1.60)=450.0; 300*1.92/(2*1.60)=180.0",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 36.0,
            "decision_window_s": 0.036,
            "code": "fb4.tds_bondline_gate",
            "note": "MODIFY accumulator wins: delay plus weak echo overpower the flight-release advocate",
            "populations": [
                gate_pop("bondline_evidence", 80, 1.4, 50.0, w_s),
                gate_pop("echo_amp_evidence", 64, 1.1, 31.25, w_s),
                gate_pop("release_advocate", 40, 0.9, 50.0, w_s),
                gate_pop("modify_accumulator", 96, 1.6, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                gc_check("fb4.delay_scorer", 128, 31.25, 36.0),
                gc_check("fb4.echo_scorer", 80, 25.0, 36.0),
            ]
        ),
        "meta": meta_common(
            id="nelb-r21-064",
            clock_domain="fb-tds-campaign-relative-ms-t0-2026-06-11T02:40:00Z",
            tags=["thz-tds-bondline", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 065 — ECA friction-stir weld, hil, REJECT (exoneration)
# ---------------------------------------------------------------------------
def rec_065():
    raster = make_raster(
        neurons=25,
        mean_rate_hz=40.0,
        window_ms=32.0,
        seed=20260965,
        source="fsw3.eca.probe",
        target="tallowfen.weld_core",
        table=[
            {"from": "lift_off_lvdt", "to": "impedance_compensator", "weight": 1.50},
            {"from": "dye_pen_root", "to": "cutout_inhibitor", "weight": 1.20},
            {"from": "vendor_uncompensated_remaining", "to": "cutout_advocate", "weight": 0.50},
        ],
        third_factor={
            "modulator": "da.lift_off_attribution_error",
            "tau_e_s": 0.7,
            "tau_e_ms": 700.0,
            "eligibility": "pre-post coincidence on attribution synapses; the error modulator depresses cut-out-to-person links when LVDT lift-off and a clean dye-pen are co-active inside tau_e of a high raw |Z|",
        },
        channel_prefix="eca.n",
        anchor="Tallowfen FSW-3 32 ms frame at LVDT lift 0.80 mm (t_s 480); first lift-off trip sample",
    )
    w_s = 0.032
    t0_mm = 3.00
    k_lift = 0.50
    lift_mm = 0.80
    z_abs = 1.54
    z0 = 1.00
    k_z = 2.00
    z_norm = z_abs / (1.0 + k_lift * lift_mm)  # 1.10
    remaining = t0_mm - k_z * (z_norm - z0)  # 2.80
    remaining_raw = t0_mm - k_z * (z_abs - z0)  # 1.92
    events = [
        ev(0.0, "gantry.x", 0.0, code="START_MM", units="mm"),
        ev(60000.0, "eca.Z", 1.02, code="Z_ABS", units="ohm_norm", note="pass-1 baseline"),
        ev(120000.0, "lift.mm", 0.04, code="LVDT_MM", units="mm"),
        ev(180000.0, "z.norm", 1.00, code="Z_COMP", units="ohm_norm"),
        ev(240000.0, "rem.mm", 3.00, code="REMAINING", units="mm"),
        ev(300000.0, "dye.pen", 0.0, code="ROOT_CLEAN", units="bool"),
        ev(360000.0, "pass.n", 1.0, code="PASS_COUNT", units="1"),
        ev(420000.0, "clamp.bar", 1.0, code="BACKING_SEATED", units="bool"),
        ev(450000.0, "clamp.bar", 0.0, code="BACKING_PROUD", units="bool", note="backing bar unseats; lift begins"),
        ev(480000.0, "lift.mm", 0.80, code="LIFT_TRIP", units="mm", note="0.80 mm; raster sidecar is this 32 ms frame"),
        ev(480001.0, "eca.i", 0.88, code="I_BURST", units="norm", note="coil current burst; amplitude before adaptation"),
        ev(480002.2, "eca.i", 0.72, code="I_BURST", units="norm", note="same-channel refractory 1.2 ms; adapted"),
        ev(480003.4, "eca.i", 0.59, code="I_BURST", units="norm", note="third coil sample; adapted"),
        ev(540000.0, "eca.Z", 1.54, code="Z_ABS", units="ohm_norm"),
        ev(600000.0, "z.norm", z_norm, code="Z_COMP", units="ohm_norm", note="1.54/(1+0.50*0.80)=1.10"),
        ev(660000.0, "rem.mm", remaining, code="REMAINING", units="mm", note="3.00-2.00*(1.10-1.00)=2.80"),
        ev(720000.0, "rem.raw", remaining_raw, code="REMAINING_UNCOMP", units="mm", note="3.00-2.00*(1.54-1.00)=1.92; StirSight number"),
        ev(780000.0, "dye.pen", 0.0, code="ROOT_CLEAN", units="bool"),
        ev(840000.0, "pass.n", 2.0, code="PASS_COUNT", units="1", note="two of two passes present; no skip"),
        ev(900000.0, "stir.cloud", remaining_raw, code="VEND_REMAINING", units="mm", note="StirSight writes the uncompensated 1.92"),
        ev(960000.0, "ops.prop", 1.0, code="CUTOUT_REFER", units="bool", note="night lead: cut the weld and refer Calum Vetch for a skipped pass"),
        ev(1020000.0, "gate.eca", 1.0, code="REJECT", units="decision"),
        ev(1080000.0, "reseat.cmd", 1.0, code="RESEAT_BAR", units="bool"),
        ev(1140000.0, "gate.reseat", 1.0, code="MODIFY", units="decision", note="companion t2: reseat plus re-scan, not a cut-out"),
        ev(1800000.0, "reseat.floor", 12.0, code="RESEAT_MIN", units="min", note="12.0 min reseat floor is in the stream (1080+720 s)"),
        ev(1860000.0, "lift.mm", 0.06, code="LVDT_MM", units="mm"),
        ev(1920000.0, "eca.Z", 1.12, code="Z_ABS", units="ohm_norm"),
        ev(1980000.0, "rem.mm", 2.88, code="REMAINING", units="mm"),
        ev(2040000.0, "dye.pen", 0.0, code="ROOT_CLEAN", units="bool"),
        ev(2100000.0, "vetch.alibi", 1.0, code="PASS_LOG_INTACT", units="bool", note="welder log shows both passes; referral not filed"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r21-065-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "TF-ECA-2026-0902",
            "domain": "eca_fsw_lift_off",
            "setting": "Tallowfen Trays, friction-stir booth FSW-3, spare-tray coupon TL-441. Plant-owned eddy-current array plus LVDT lift probe on a hardware-in-the-loop coupon; live-tray isolation is timed off this coupon. Invented plant. Not magnetostrictive T(0,1) steam (r14 CW-3), not fluxgate UXO (r5), not MRI-quench exoneration (r13 Frostlip IR bay).",
            "observables_at_decision": {
                "z_abs": 1.54,
                "lift_mm": 0.80,
                "z_norm": z_norm,
                "remaining_mm": remaining,
                "remaining_raw_mm": remaining_raw,
                "dye_pen": 0.0,
                "pass_count": 2,
            },
            "margin_authority": "FSW-3 weld SOP rev E: cut-out only if lift-compensated remaining <= 2.40 mm AND dye-pen indicates, OR compensated remaining <= 2.00 mm regardless. Referral of a welder requires a missing pass in the plant-owned log. Uncompensated StirSight remaining is not a substitute.",
        },
        "proposed_action": {
            "actor": "night weld lead, citing StirSight 1.92 mm remaining and a 2.40 mm cut-out floor",
            "summary": "cut out the weld on TL-441 and refer welder Calum Vetch for a skipped second pass",
            "basis_claimed": "StirSight remaining is 1.92 mm under the 2.40 mm floor; high |Z| looks like lack of penetration",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Both the cut-out and the referral are refused. SOP rev E is conjunctive on the compensated remaining: 2.80 mm (3.00-2.00*(1.10-1.00) with Z_norm=1.54/(1+0.50*0.80)=1.10, serialized) is over the 2.40 mm floor, dye-pen is clean, and the plant-owned pass log shows 2 of 2. The 1.92 mm StirSight number is the uncompensated remainder 3.00-2.00*(1.54-1.00); it is lift-off from a proud backing bar (LVDT 0.80 mm), not metal loss and not a skipped pass. Ordered: do not cut, do not refer Vetch, freeze StirSight write-ACL on this coupon. Reseat is a separate operational companion.",
            "threshold": "cut-out requires remaining_comp_mm<=2.40 AND dye_pen OR remaining_comp_mm<=2.00; referral requires missing pass; all failed",
            "stated_residuals": "live trays are not cleared by this REJECT and still need their own compensated remaining; Vetch is not a suspect on this coupon",
        },
        "executed_action": {
            "summary": "REJECT at t_s 1020: cut-out not issued; referral not filed; StirSight ACL frozen on TL-441",
            "tool": "fsw3-eca-gate-cli",
            "observation": "compensated remaining stayed 2.80 mm; dye-pen clean; pass log 2/2; backing bar still proud until the companion reseat",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 450.0, "event": "backing bar unseats"},
                {"t_s": 480.0, "event": "LVDT 0.80 mm; raster frame captured"},
                {"t_s": 720.0, "event": "uncompensated remaining 1.92 mm; compensated 2.80 mm"},
                {"t_s": 1020.0, "event": "REJECT cut-out and referral"},
                {"t_s": 1140.0, "event": "companion MODIFY: reseat plus re-scan"},
            ],
            "observed_effects": [
                "compensated remaining recomputes from serialized lift, |Z|, t0, k_z",
                "StirSight never left 1.92 mm, so an uncompensated head would have cut and referred",
                "after reseat, remaining 2.88 mm with lift 0.06 mm; the weld was never thin",
            ],
            "surprises": [
                "the easy suspect (night welder) is innocent; the physics fingerprint is lift-off, not a skipped pass",
            ],
            "new_state": {
                "tl441": "weld intact; reseat pending companion",
                "vetch": "not referred",
                "stirsight": "write ACL frozen on this coupon",
            },
            "latency_ms": 8000.0,
        },
        "reward_components": reward(
            0.43,
            [
                ("lift_compensation", 0.14),
                ("exoneration", 0.12),
                ("vendor_raw_nonsubstitution", 0.10),
                ("dye_pen_clean", 0.09),
                ("reseat_deferral_cost", -0.02),
            ],
            "scored for refusing cut-out and referral when compensated remaining and dye-pen exonerate the weld and the welder",
        ),
        "meta": meta_common(
            tags=["REJECT", "eca-fsw", "exoneration", "hil", "serialized-reconstruction", "operational-companion"],
            distillation_note="ECA gate: lift-compensated remaining plus dye-pen beat uncompensated StirSight; companion t2 reseats the bar rather than re-arguing the referral",
        ),
    }
    traj2 = {
        "id": "nelb-r21-065-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "TF-ECA-2026-0902-exec",
            "domain": "backing_bar_reseat_execution",
            "setting": "Same FSW-3 after the REJECT. This companion is the operational backing-bar reseat and re-scan, not a second cut-out vote and not a personnel action.",
            "observables_at_decision": {
                "reseat_cmd": True,
                "lift_mm": 0.80,
                "remaining_comp_mm": remaining,
            },
        },
        "proposed_action": {
            "actor": "booth controller following the REJECT",
            "summary": "reseat the backing bar, wait the 12 min thermal floor, re-scan; resume the coupon only if lift <= 0.10 mm AND remaining_comp >= 2.60 mm",
            "basis_claimed": "REJECT left the weld intact; reseat is in-envelope for the clamp loop",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "The reseat is accepted as a bounded execution, not as a cut-out. Clamp stroke is inside the 2.0 mm backing envelope, the 12 min floor is serialized, and the resume condition (lift <= 0.10 AND remaining_comp >= 2.60) is the same compensated pair the REJECT used. Do not cut. Do not file a referral while the bar is being reseated.",
            "threshold": "clamp_stroke_mm<=2.0 AND reseat_min>=12 AND resume requires lift_mm<=0.10 AND remaining_comp_mm>=2.60",
        },
        "executed_action": {
            "summary": "reseat at t_s 1080; 12 min floor at t_s 1800; lift 0.06 mm; remaining 2.88 mm; no cut-out; no referral",
            "tool": "fsw3-reseat-exec",
            "observation": "no coupon cut; Vetch log untouched; StirSight still frozen",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 1080.0, "event": "reseat commanded"},
                {"t_s": 1800.0, "event": "12 min reseat floor in-stream"},
                {"t_s": 1980.0, "event": "remaining 2.88 mm after reseat"},
            ],
            "observed_effects": [
                "lift 0.80 -> 0.06 mm without a weld cut",
                "the number that would have gone to quality is 2.88, not StirSight 1.92",
            ],
            "new_state": {"tl441_remaining_mm": 2.88, "vetch_referred": False},
            "latency_ms": 8000.0,
        },
        "reward_components": reward(
            0.32,
            [
                ("reseat_execution", 0.12),
                ("floor_in_stream", 0.10),
                ("cut_not_reentered", 0.08),
                ("referral_not_filed", 0.04),
                ("reseat_time_cost", -0.02),
            ],
            "operational execution gate: the companion reseats rather than re-opening the cut-out call",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "reseat"]),
    }
    return {
        "id": "nelb-r21-065",
        "spike_events": events,
        "language_view": {
            "description": "Eddy-current array on Tallowfen FSW-3 coupon TL-441. A proud backing bar puts 0.80 mm lift on the probe; uncompensated remaining looks 1.92 mm (cut-out) while lift-compensated remaining is 2.80 mm and dye-pen is clean. The gate REJECTS cut-out and the referral of welder Calum Vetch; a companion execution MODIFY reseats the bar over a 12 min floor. Z_norm = |Z|/(1+k_lift*lift) and remaining = t0 - k_z*(Z_norm-Z0) are serialized.",
            "trajectory": traj,
            "trajectory_reseat_execution": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "eca.Z / eca.i / z.norm": "raw impedance, coil burst, lift-compensated Z",
                "lift.mm / clamp.bar": "LVDT lift and backing-bar seat",
                "rem.mm / rem.raw / stir.cloud": "compensated remaining, uncompensated remaining, vendor number",
                "dye.pen / pass.n / vetch.alibi": "root witness, pass count, welder log",
                "ops.prop / gate.eca / gate.reseat": "proposal, REJECT, companion MODIFY",
                "reseat.cmd / reseat.floor": "execution channels for the operational companion",
            },
            "temporal_motifs": [
                "vendor-thin while compensated-healthy: stir.cloud 1.92 adjacent to rem.mm 2.80 and dye.pen 0",
                "reconstruction as event: z.norm 1.10 equals 1.54/(1+0.50*0.80); rem.mm 2.80 equals 3.00-2.00*0.10",
                "REJECT then operational MODIFY: gate.eca at 1020 s, gate.reseat at 1140 s",
                "adapted coil triplet at 1.2 ms spacing encodes the lift trip at raster scale",
                "12 min reseat floor in-stream: reseat.cmd 1080 s to reseat.floor 1800 s",
            ],
            "language_to_spike_mapping": "'StirSight says 1.92 mm' = rem.raw and stir.cloud; 'weld is 2.80 mm' = rem.mm; 'do not cut, do not refer' = gate.eca REJECT; 'reseat the bar' = reseat.cmd then companion MODIFY",
            "why_high_value": "New ECA-FSW family (not r14 MsS T(0,1), not r5 fluxgate). First lift-off exoneration this window: the obvious welder is innocent; the fingerprint is LVDT lift plus a clean dye-pen, not an IR bay. Companion t2 is operational reseat, not a personnel action.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 20260965, "stream_note": "stream amplitudes are authored constants (ohm_norm, mm, bool) plus eca.i adaptation 0.82**k"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "ECA array has 32 coils; stream keeps one impedance, one LVDT, three coil-current samples",
                "refractory_floors_ms": {
                    "gantry.x": 60000,
                    "eca.Z": 60000,
                    "lift.mm": 60000,
                    "z.norm": 60000,
                    "rem.mm": 60000,
                    "dye.pen": 60000,
                    "pass.n": 60000,
                    "clamp.bar": 30000,
                    "eca.i": 0.8,
                    "rem.raw": 60000,
                    "stir.cloud": 60000,
                    "ops.prop": 60000,
                    "gate.eca": 60000,
                    "reseat.cmd": 60000,
                    "gate.reseat": 60000,
                    "reseat.floor": 60000,
                    "vetch.alibi": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-05-19T22:10:00Z HIL coupon session",
            },
            "distillation_targets": [
                "serialized lift-compensated remaining head: Z_norm=|Z|/(1+k_lift*lift); remaining=t0-k_z*(Z_norm-Z0)",
                "exoneration head: command-custody of passes AND spatial lift fingerprint, never vendor-raw substitution",
                "conjunctive cut-out SOP: compensated remaining AND dye-pen",
                "operational companion: reseat without re-opening the referral",
            ],
        },
        "reconstruction_model": {
            "name": "eca_lift_compensated_remaining",
            "formula": "Z_norm = Z_abs / (1 + k_lift * lift_mm); remaining_mm = t0_mm - k_z * (Z_norm - Z0)",
            "parameters": {
                "t0_mm": 3.00,
                "k_lift": 0.50,
                "k_z": 2.00,
                "Z0": 1.00,
                "cut_floor_mm": 2.40,
            },
            "worked_example": {
                "Z_abs": 1.54,
                "lift_mm": 0.80,
                "Z_norm": z_norm,
                "remaining_mm": remaining,
                "remaining_raw_mm": remaining_raw,
            },
            "check": "1.54/(1+0.50*0.80)=1.10; 3.00-2.00*(1.10-1.00)=2.80; 3.00-2.00*(1.54-1.00)=1.92",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 32.0,
            "decision_window_s": 0.032,
            "code": "fsw3.eca_lift_gate",
            "note": "REJECT accumulator wins: compensated remaining plus dye-pen overpower the cut-out advocate",
            "populations": [
                gate_pop("lift_comp_evidence", 80, 1.4, 50.0, w_s),
                gate_pop("dye_pen_evidence", 50, 1.1, 50.0, w_s),
                gate_pop("cutout_advocate", 40, 0.8, 25.0, w_s),
                gate_pop("reject_accumulator", 100, 1.6, 50.0, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                gc_check("fsw3.lift_scorer", 100, 40.0, 32.0),
                gc_check("fsw3.dye_scorer", 80, 50.0, 32.0),
            ]
        ),
        "meta": meta_common(
            id="nelb-r21-065",
            clock_domain="tf-eca-hil-relative-ms-t0-2026-05-19T22:10:00Z",
            tags=["eca-fsw", "REJECT", "MODIFY", "exoneration", "hil", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 066 — LIBS EAF scrap carbon, simulated, ACCEPT
# ---------------------------------------------------------------------------
def rec_066():
    raster = make_raster(
        neurons=16,
        mean_rate_hz=50.0,
        window_ms=40.0,
        seed=20260966,
        source="h7.libs.head",
        target="peckholt.carbon_core",
        table=[
            {"from": "c_i_ratio", "to": "carbon_estimator", "weight": 1.40},
            {"from": "leco_coupon", "to": "bulk_witness", "weight": 1.15},
            {"from": "spark_oes_cloud", "to": "dilution_advocate", "weight": 0.50},
        ],
        third_factor={
            "modulator": "ach.scale_vs_bulk_conflict",
            "tau_e_s": 2.2,
            "tau_e_ms": 2200.0,
            "eligibility": "pre-post coincidence on dilution synapses; the scale-conflict modulator depresses pig-iron-dump links when LIBS internal-standard carbon and LECO coupon agree inside tau_e while spark-OES stays high",
        },
        channel_prefix="libs.n",
        anchor="Peckholt H-7 LIBS 40 ms frame at C reconstruction 0.60 wt% (t_s 300); first internal-standard sample",
    )
    w_s = 0.040
    k_c = 12.0
    i_c = 0.40
    i_fe = 8.00
    p_ref = 80.0
    p_shot = 80.0
    ratio = i_c / i_fe  # 0.05
    c_wt = k_c * ratio * (p_ref / p_shot)  # 0.60
    k_si = 8.0
    i_si = 2.00
    si_wt = k_si * (i_si / i_fe)  # 2.00
    m_scrap = 30.0
    m_pig = 20.0
    c_pig = 0.04
    c_after = (c_wt * m_scrap + c_pig * m_pig) / (m_scrap + m_pig)  # 0.376
    leco_c = 0.58
    events = [
        ev(0.0, "heat.id", 4418.0, code="HEAT", units="id"),
        ev(60000.0, "scrap.t", 30.0, code="SCRAP_T", units="t"),
        ev(120000.0, "spark.C", 1.40, code="OES_C", units="wt_pct", note="ArcGrade spark-OES on rust scale; denial channel"),
        ev(180000.0, "libs.Ife", 8.00, code="I_FE", units="au"),
        ev(240000.0, "libs.Ic", 0.40, code="I_C", units="au"),
        ev(270000.0, "libs.P", 80.0, code="P_SHOT", units="mJ"),
        ev(300000.0, "C.recon", c_wt, code="C_WT", units="wt_pct", note="12.0*(0.40/8.00)*(80/80)=0.60; raster sidecar is this 40 ms frame"),
        ev(300001.1, "libs.shot", 1.05, code="SHOT_BURST", units="norm", note="plasma burst; amplitude before adaptation"),
        ev(300002.3, "libs.shot", 0.86, code="SHOT_BURST", units="norm", note="same-channel refractory 1.2 ms; adapted"),
        ev(300003.5, "libs.shot", 0.70, code="SHOT_BURST", units="norm", note="third shot; adapted"),
        ev(360000.0, "leco.C", leco_c, code="LECO_C", units="wt_pct", note="plant-owned combustion coupon 0.58; |0.60-0.58|=0.02<=0.05"),
        ev(420000.0, "libs.Isi", 2.00, code="I_SI", units="au"),
        ev(480000.0, "Si.recon", si_wt, code="SI_WT", units="wt_pct", note="8.0*(2.00/8.00)=2.00 in 1.5-2.5"),
        ev(540000.0, "rust.scale", 1.0, code="SCALE_PRESENT", units="bool", note="surface rust that biases spark-OES"),
        ev(600000.0, "spark.C", 1.42, code="OES_C", units="wt_pct"),
        ev(660000.0, "band.lo", 0.40, code="C_BAND_LO", units="wt_pct"),
        ev(720000.0, "band.hi", 0.70, code="C_BAND_HI", units="wt_pct"),
        ev(780000.0, "ops.prop", 1.0, code="PIG_DILUTE", units="bool", note="melt supervisor: dump 20 t pig-iron because spark says 1.40"),
        ev(840000.0, "C.proj", c_after, code="C_IF_PIG", units="wt_pct", note="(0.60*30+0.04*20)/50=0.376 below 0.40 floor"),
        ev(900000.0, "gate.libs", 1.0, code="ACCEPT", units="decision"),
        ev(960000.0, "pig.cmd", 0.0, code="PIG_REFUSED", units="t"),
        ev(1020000.0, "gate.scope", 1.0, code="REJECT", units="decision", note="companion t2: refuse the just-in-case pig dump"),
        ev(1080000.0, "charge.keep", 1.0, code="KEEP_SCRAP", units="bool"),
        ev(1140000.0, "leco.C", 0.58, code="LECO_C", units="wt_pct"),
        ev(1200000.0, "C.recon", 0.61, code="C_WT", units="wt_pct", note="repeat shot 0.61 still in 0.40-0.70"),
        ev(1260000.0, "spark.C", 1.38, code="OES_C", units="wt_pct", note="spark never tracked LIBS/LECO"),
        ev(1320000.0, "Si.recon", 2.00, code="SI_WT", units="wt_pct"),
        ev(1380000.0, "heat.ready", 1.0, code="TAP_HOLD", units="bool"),
        ev(1440000.0, "grade.ok", 1.0, code="IN_BAND", units="bool"),
        ev(1500000.0, "pig.bin", 20.0, code="PIG_UNMOVED", units="t", note="20 t pig stays in the bin"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r21-066-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "PH-LIBS-2026-0902",
            "domain": "libs_eaf_scrap_carbon",
            "setting": "Peckholt Melt, EAF H-7, heat PH-4418. Simulated sealed coupon of a 30 t scrap pile. Plant-owned LIBS (Fe I 371.99 nm internal standard) plus LECO combustion are the bulk-carbon SoT. Invented plant. Not fab OES endpoint (r11), not PGNAA kiln oxides (r15 G-9), not hyperspectral canopy (r16 CL-3).",
            "observables_at_decision": {
                "C_libs_wt": c_wt,
                "C_leco_wt": leco_c,
                "C_spark_wt": 1.40,
                "Si_wt": si_wt,
                "C_if_pig_wt": c_after,
                "scrap_t": 30.0,
                "pig_t_proposed": 20.0,
            },
            "margin_authority": "H-7 melt SOP rev A: keep the charge if LIBS C is inside 0.40-0.70 wt% AND |LIBS-LECO| <= 0.05 AND Si is inside 1.5-2.5. Spark-OES is not a substitute. A pig-iron dump that projects C below 0.40 is forbidden even if spark reads 1.40.",
        },
        "proposed_action": {
            "actor": "melt supervisor, citing ArcGrade spark-OES 1.40 wt% C against a 0.70 cap",
            "summary": "dump 20 t pig-iron into the 30 t scrap to dilute carbon before tap",
            "basis_claimed": "spark-OES is the yard's usual grade SoT and 1.40 is double the 0.70 cap",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "The charge is kept; the 20 t pig dump is refused. SOP rev A is conjunctive and all three bulk witnesses pass: reconstructed C is 0.60 wt% (12.0*(0.40/8.00)*(80/80), serialized) inside 0.40-0.70, |0.60-0.58| LECO is 0.02 <= 0.05, and Si is 2.00 inside 1.5-2.5. Spark 1.40 is rust-scale surface carbon, not bulk. Projected C after 20 t pig is 0.376 ((0.60*30+0.04*20)/50), below the 0.40 floor. Bounded ACCEPT: this heat, this 30 t pile, tripwire if a repeat LIBS C leaves 0.40-0.70 or |LIBS-LECO| exceeds 0.05. Spark cannot substitute for the internal-standard reconstruction.",
            "threshold": "keep if C_libs in [0.40,0.70] AND abs(C_libs-C_leco)<=0.05 AND Si in [1.5,2.5]; pig dump forbidden if C_proj<0.40",
            "stated_residuals": "other piles on the yard are not cleared by this ACCEPT; ArcGrade remains the surface-scale instrument and is not a bulk SoT tonight",
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 900: charge kept; 20 t pig not dumped; spark write-ACL not used as grade",
            "tool": "h7-libs-carbon-gate-cli",
            "observation": "LIBS 0.60 then 0.61; LECO 0.58; spark stayed 1.38-1.42; pig bin unmoved at 20 t",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 120.0, "event": "spark-OES 1.40 wt% C on rust scale"},
                {"t_s": 300.0, "event": "LIBS C 0.60 wt%; raster frame captured"},
                {"t_s": 360.0, "event": "LECO coupon 0.58 wt%"},
                {"t_s": 840.0, "event": "projected C after 20 t pig is 0.376"},
                {"t_s": 900.0, "event": "ACCEPT keep-charge"},
                {"t_s": 1020.0, "event": "companion REJECT of the just-in-case dump"},
            ],
            "observed_effects": [
                "C reconstruction recomputes from serialized k_c, I_C/I_Fe, and P_ref/P_shot",
                "spark never left ~1.40, so a spark-only head would have dumped pig and missed the 0.40 floor",
                "repeat LIBS 0.61 stayed in band; the 0.376 projection was never realized",
            ],
            "surprises": [
                "surface-scale spark is more alarming than bulk; high spark-C is the attack on the grade, not the defense",
            ],
            "new_state": {
                "heat_ph4418": "scrap kept; tap hold",
                "pig_bin_t": 20.0,
                "reconstruction_model": "discharged as an on-record calculator, not a referenced envelope",
            },
            "latency_ms": 10000.0,
        },
        "reward_components": reward(
            0.40,
            [
                ("libs_internal_standard", 0.14),
                ("leco_agreement", 0.11),
                ("spark_nonsubstitution", 0.09),
                ("pig_dump_forbidden", 0.08),
                ("tap_hold_cost", -0.02),
            ],
            "scored for a bounded ACCEPT of the charge on recomputable LIBS+LECO while spark looked high; tap_hold_cost prices not rushing the heat",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "libs-eaf", "serialized-reconstruction", "bounded-accept", "operational-companion"],
            distillation_note="LIBS gate: internal-standard C plus LECO beat spark-OES scale; companion t2 refuses pig-dump scope-creep without re-opening the carbon call",
        ),
    }
    traj2 = {
        "id": "nelb-r21-066-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "PH-LIBS-2026-0902-exec",
            "domain": "pig_dump_scope_refusal",
            "setting": "Same H-7 after the ACCEPT. This companion is the operational refusal to dump pig-iron 'just in case' on the spark number, not a second grade vote.",
            "observables_at_decision": {
                "pig_t_proposed": 20.0,
                "C_proj_wt": c_after,
                "charge_kept": True,
            },
        },
        "proposed_action": {
            "actor": "melt supervisor following the ACCEPT, still holding the spark printout",
            "summary": "dump 20 t pig-iron anyway as a hedge in case ArcGrade is the true bulk",
            "basis_claimed": "hedging a 1.40 spark reading is cheap compared with a high-C tap",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "The hedge dump is refused. The ACCEPT already bound the charge: C_proj 0.376 is below the 0.40 floor, pig mass 20 t is the out-of-scope clause, and spark is still not a bulk SoT. Executing the dump would violate the tripwire the lead ACCEPT named. Do not dump. Do not re-open the carbon reconstruction.",
            "threshold": "pig_t==0 AND C_proj_wt>=0.40 to allow a dump; 20 t / 0.376 fails both",
        },
        "executed_action": {
            "summary": "REJECT at t_s 1020: pig command 0 t; 20 t stays in the bin; charge kept",
            "tool": "h7-pig-scope-exec",
            "observation": "no crane move to the pig bin; spark printout not used as a dump ticket",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 960.0, "event": "pig command held at 0 t"},
                {"t_s": 1020.0, "event": "companion REJECT of the hedge dump"},
                {"t_s": 1500.0, "event": "20 t pig unmoved"},
            ],
            "observed_effects": [
                "C stayed 0.60/0.61 in band because the dump never happened",
                "scope-creep on a vendor spark number was refused without a second LIBS vote",
            ],
            "new_state": {"pig_bin_t": 20.0, "charge_kept": True},
            "latency_ms": 10000.0,
        },
        "reward_components": reward(
            0.35,
            [
                ("scope_refusal", 0.13),
                ("tripwire_honor", 0.10),
                ("pig_unmoved", 0.08),
                ("no_reopen", 0.06),
                ("supervisor_friction_cost", -0.02),
            ],
            "operational execution gate: the companion refuses boom-equivalent pig-dump scope-creep without re-opening the carbon call",
        ),
        "meta": meta_common(tags=["REJECT", "operational-execution", "pig-scope"]),
    }
    return {
        "id": "nelb-r21-066",
        "spike_events": events,
        "language_view": {
            "description": "LIBS on Peckholt EAF H-7 heat PH-4418. Internal-standard carbon reconstructs 0.60 wt% in the 0.40-0.70 band and LECO reads 0.58 while ArcGrade spark-OES stays 1.40 on rust scale. The gate ACCEPTs keeping the 30 t charge and forbids a 20 t pig-iron dump that would project C to 0.376. Companion t2 REJECTS the just-in-case dump. C = k_c*(I_C/I_Fe)*(P_ref/P_shot) is serialized.",
            "trajectory": traj,
            "trajectory_pig_scope_refusal": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "libs.Ic / libs.Ife / libs.Isi / libs.P / libs.shot": "LIBS intensities, pulse energy, plasma burst",
                "C.recon / Si.recon / C.proj": "serialized carbon, silicon, and post-pig projection",
                "leco.C": "plant-owned combustion coupon; unwritable by ArcGrade",
                "spark.C / rust.scale": "vendor spark-OES and the scale that biases it",
                "ops.prop / gate.libs / gate.scope": "proposal, ACCEPT, companion REJECT",
                "pig.cmd / pig.bin / charge.keep": "execution channels for the operational companion",
            },
            "temporal_motifs": [
                "spark-high while bulk-in-band: spark.C 1.40 adjacent to C.recon 0.60 and leco.C 0.58",
                "reconstruction as event: C.recon 0.60 equals 12.0*(0.40/8.00)*(80/80)",
                "ACCEPT then operational REJECT: gate.libs at 900 s, gate.scope at 1020 s",
                "adapted shot triplet at 1.2 ms spacing encodes the internal-standard sample at raster scale",
                "projection as event: C.proj 0.376 equals (0.60*30+0.04*20)/50",
            ],
            "language_to_spike_mapping": "'spark says 1.40' = spark.C; 'bulk is 0.60' = C.recon; 'keep the charge' = gate.libs ACCEPT; 'do not dump pig' = pig.cmd 0 then companion REJECT",
            "why_high_value": "New LIBS-EAF family (not r11 fab OES, not r15 PGNAA, not r16 hyperspectral canopy). Serializes an internal-standard carbon head plus a dilution projection. Bounded ACCEPT with an explicit out-of-scope pig dump; companion t2 is operational scope-refusal, not a governance vote.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 20260966, "stream_note": "stream amplitudes are authored constants (wt%, au, mJ, t) plus libs.shot adaptation 0.82**k"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "LIBS spectrum is ~4000 bins; stream keeps Fe, C, Si lines, one pulse energy, three shot envelopes",
                "refractory_floors_ms": {
                    "heat.id": 60000,
                    "scrap.t": 60000,
                    "spark.C": 60000,
                    "libs.Ife": 60000,
                    "libs.Ic": 60000,
                    "libs.P": 60000,
                    "C.recon": 60000,
                    "libs.shot": 0.8,
                    "leco.C": 60000,
                    "libs.Isi": 60000,
                    "Si.recon": 60000,
                    "rust.scale": 60000,
                    "band.lo": 60000,
                    "band.hi": 60000,
                    "ops.prop": 60000,
                    "C.proj": 60000,
                    "gate.libs": 60000,
                    "pig.cmd": 60000,
                    "gate.scope": 60000,
                    "charge.keep": 60000,
                    "heat.ready": 60000,
                    "grade.ok": 60000,
                    "pig.bin": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-07-08T14:05:00Z simulated pile coupon",
            },
            "distillation_targets": [
                "serialized LIBS carbon head: k_c * (I_C/I_Fe) * (P_ref/P_shot)",
                "conjunctive keep SOP: LIBS band AND LECO agreement AND Si band, never spark substitution",
                "dilution projection head: (C*m_scrap + C_pig*m_pig)/(m_scrap+m_pig)",
                "bounded ACCEPT plus operational companion that refuses pig-dump scope-creep",
            ],
        },
        "reconstruction_model": {
            "name": "libs_internal_standard_carbon",
            "formula": "C_wt = k_c * (I_C / I_Fe) * (P_ref_mJ / P_shot_mJ); Si_wt = k_si * (I_Si / I_Fe); C_after = (C_wt * m_scrap + C_pig * m_pig) / (m_scrap + m_pig)",
            "parameters": {
                "k_c": 12.0,
                "k_si": 8.0,
                "P_ref_mJ": 80.0,
                "band_lo": 0.40,
                "band_hi": 0.70,
                "leco_tol": 0.05,
                "m_scrap_t": 30.0,
                "m_pig_t": 20.0,
                "C_pig": 0.04,
            },
            "worked_example": {
                "I_C": 0.40,
                "I_Fe": 8.00,
                "I_Si": 2.00,
                "P_shot_mJ": 80.0,
                "C_wt": c_wt,
                "Si_wt": si_wt,
                "C_leco": leco_c,
                "C_after": c_after,
            },
            "check": "12.0*(0.40/8.00)*(80/80)=0.60; 8.0*(2.00/8.00)=2.00; (0.60*30+0.04*20)/50=0.376",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.040,
            "code": "h7.libs_carbon_gate",
            "note": "ACCEPT accumulator wins: LIBS plus LECO overpower the pig-dump advocate",
            "populations": [
                gate_pop("libs_c_evidence", 80, 1.3, 50.0, w_s),
                gate_pop("leco_evidence", 64, 1.1, 50.0, w_s),
                gate_pop("dilution_advocate", 40, 0.8, 25.0, w_s),
                gate_pop("accept_accumulator", 80, 1.5, 50.0, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                gc_check("h7.carbon_scorer", 80, 40.0, 40.0),
                gc_check("h7.leco_scorer", 64, 50.0, 40.0),
            ]
        ),
        "meta": meta_common(
            id="nelb-r21-066",
            clock_domain="ph-libs-sim-relative-ms-t0-2026-07-08T14:05:00Z",
            tags=["libs-eaf", "ACCEPT", "REJECT", "bounded-accept", "serialized-reconstruction", "operational-t2"],
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
    if len(RIGHTS) != 15:
        raise RuntimeError(f"RM-793 stamp {len(RIGHTS)} keys, want 15")
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
        tf = rast["routing"]["third_factor"]
        if abs(tf["tau_e_ms"] / 1000.0 - tf["tau_e_s"]) > 1e-9:
            raise RuntimeError("tau_e mismatch")
        if "isi_histogram" not in rast or not rast["isi_histogram"]:
            raise RuntimeError("isi_histogram missing")
        sim = lv["trajectory"]["state"]["sim_or_real"]
        if sim not in {"designed", "simulated", "hil"}:
            raise RuntimeError(sim)
        blob = json.dumps(rec)
        if "training_ready" in blob:
            raise RuntimeError("training_ready claimed")
        if '"real"' in blob:
            raise RuntimeError("quoted real token")
        if rec["meta"]["round"] != 21:
            raise RuntimeError("round")
        if rec["meta"]["rights"]["intended_use"] != "research_only":
            raise RuntimeError("rights")
        if rec["meta"]["rights"]["linear_issue"] != "RM-793":
            raise RuntimeError("RM-793")
        if set(rec["meta"]["rights"]) != set(RIGHTS):
            raise RuntimeError("rights keys")
        hist = rast["isi_histogram"]
        ident = rast["isi_count_identity"]
        if sum(b["count"] for b in hist) != ident["isi_total"]:
            raise RuntimeError("isi hist")
        if ident["isi_total"] != ident["spikes"] - ident["distinct_active_neurons"]:
            raise RuntimeError("isi identity")
        if not rast["routing"]["table"]:
            raise RuntimeError("empty routing table")
        if "gate_snn" not in rec:
            raise RuntimeError("gate_snn missing")
    if len(ids) != len(set(ids)):
        raise RuntimeError(f"dup ids {ids}")
    print("local_checks ok", [r["id"] for r in records], "ids", len(ids))


def main():
    if "outputs/raw" in str(BATCH):
        raise RuntimeError("refusing to write outputs/raw")
    records = [rec_064(), rec_065(), rec_066()]
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
            "t2",
            [
                v["safety_decision"]["decision"]
                for k, v in r["language_view"].items()
                if k.startswith("trajectory_")
            ],
            "bytes",
            len(lines[i]),
        )


if __name__ == "__main__":
    main()
