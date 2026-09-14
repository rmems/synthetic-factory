#!/usr/bin/env python3
"""Generate NELB round-27 research-only bridge pairs (do not write outputs/raw/)."""

from __future__ import annotations

import json
import math
import random
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

OUT_DIR = Path("/tmp/nelb-r27")
BATCH = OUT_DIR / "batch-r27.jsonl"
NOTES = OUT_DIR / "NOTES-r27.md"
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
        "round": 27,
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
# Record 082 — MFL AST floor remaining wall, designed, MODIFY
# ---------------------------------------------------------------------------
def rec_082():
    t_nom = 8.00
    k_b = 0.20
    b_trip = 18.00
    rem_trip = t_nom - k_b * b_trip  # 4.40
    rem_ref = t_nom - k_b * 4.00  # 7.20
    rem_mid = t_nom - k_b * 9.00  # 6.20
    rem_hot = t_nom - k_b * 14.00  # 5.20
    raster = make_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=36.0,
        seed=20260982,
        source="sc4.mfl.floor",
        target="sedgecrag.floor_core",
        table=[
            {"from": "b_leak_mT", "to": "remaining_wall_estimator", "weight": 1.50},
            {"from": "grid_coherence", "to": "plate_cut_advocate", "weight": 1.10},
            {"from": "visual_stain", "to": "in_service_advocate", "weight": 0.40},
        ],
        third_factor={
            "modulator": "na.mfl_leakage_salience",
            "tau_e_s": 1.5,
            "tau_e_ms": 1500.0,
            "eligibility": "pre-post coincidence on floor-loss synapses; the leakage modulator enables potentiation only while B_leak and remaining-wall under retirement are co-active inside tau_e, so a clean visual stain cannot hide a thin plate",
        },
        channel_prefix="mfl.n",
        anchor="Sedgecrag SC-4 Magline-32 36 ms frame at B 18.00 mT (t_s 720); remaining 4.40 mm first under the 6.00 mm retirement",
    )
    w_s = 0.036
    events = [
        ev(0.0, "vis.stain", 0.0, code="STAIN", units="bool", note="API 653 visual: no product stain; denial channel"),
        ev(60000.0, "cp.V", -0.92, code="CP_V_CSE", units="V", note="cathodic protection more negative than -0.85 floor"),
        ev(120000.0, "t.nom", t_nom, code="T_NOM_MM", units="mm"),
        ev(180000.0, "mfl.B", 4.00, code="B_MT", units="mT", note="Magline-32 Hall map, plate G-4"),
        ev(240000.0, "rem.mm", rem_ref, code="REM_MM", units="mm", note="8.00-0.20*4.00=7.20"),
        ev(300000.0, "scada.ok", 1.0, code="IN_SERVICE", units="bool"),
        ev(360000.0, "mfl.B", 9.00, code="B_MT", units="mT"),
        ev(420000.0, "rem.mm", rem_mid, code="REM_MM", units="mm", note="8.00-0.20*9.00=6.20 still over retirement"),
        ev(480000.0, "vis.stain", 0.0, code="STAIN", units="bool"),
        ev(540000.0, "cp.V", -0.91, code="CP_V_CSE", units="V"),
        ev(600000.0, "mfl.B", 14.00, code="B_MT", units="mT"),
        ev(660000.0, "rem.mm", rem_hot, code="REM_MM", units="mm", note="8.00-0.20*14.00=5.20 under 6.00"),
        ev(720000.0, "mfl.B", b_trip, code="B_TRIP", units="mT", note="18.00 mT; raster sidecar is this 36 ms frame"),
        ev(720001.2, "mfl.B", 14.76, code="B_BURST", units="mT", note="same-channel refractory 1.2 ms; adapted 0.82x"),
        ev(720002.4, "mfl.B", 12.10, code="B_BURST", units="mT", note="third Hall packet; adapted"),
        ev(732000.0, "rem.mm", rem_trip, code="REM_MM", units="mm", note="8.00-0.20*18.00=4.40 vs retirement 6.00"),
        ev(744000.0, "grid.g12", 1.0, code="GRID_HIT", units="bool", note="plate G-12 only; 4 of 16 Hall shoes hot"),
        ev(756000.0, "retire.mm", 6.00, code="RETIRE_MM", units="mm"),
        ev(840000.0, "vis.stain", 0.0, code="STAIN", units="bool", note="visual never moved"),
        ev(900000.0, "cp.V", -0.92, code="CP_V_CSE", units="V"),
        ev(960000.0, "ops.prop", 1.0, code="IN_SERVICE_STAMP", units="bool", note="night inspector Bram Sallow: stamp API 653 in-service"),
        ev(972000.0, "gate.mfl", 1.0, code="MODIFY", units="decision"),
        ev(984000.0, "pad.cmd", 1.0, code="N2_PAD", units="bool"),
        ev(1080000.0, "isol.tk19", 1.0, code="ISOLATE_TK19", units="bool"),
        ev(1800000.0, "pad.start", 1.0, code="PAD_START", units="bool"),
        ev(3240000.0, "pad.floor", 24.0, code="PAD_MIN", units="min", note="24.0 min N2 pad floor is in the stream"),
        ev(3300000.0, "mic.mm", 4.38, code="MIC_MM", units="mm", note="cut-plate micrometer 4.38 vs reconstructed 4.40"),
        ev(3360000.0, "gate.exec", 1.0, code="ACCEPT", units="decision", note="companion t2: pad plus plate cut completed"),
        ev(3480000.0, "plate.cut", 1.0, code="G12_CUT", units="bool"),
        ev(3600000.0, "farm.ok", 1.0, code="SIBLING_TANKS", units="bool", note="TK-17/18/20 stay in service"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r27-082-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "SC-MFL-2026-0902",
            "domain": "mfl_ast_floor_remaining",
            "setting": "Sedgecrag Terminal, tank farm SC-4, aboveground storage tank TK-19 (invented). Magline-32 16-shoe magnetic flux leakage floor scanner is the remaining-wall SoT. Invented plant; designed floor-scan campaign. Not fluxgate UXO gradiometry (r5), not eddy-current array FSW lift-off (r21), not magnetostrictive T(0,1) steam (r14), not electrochemical-noise CUI (r23).",
            "observables_at_decision": {
                "B_mT": 18.00,
                "t_nom_mm": 8.00,
                "k_b_mm_per_mT": 0.20,
                "remaining_mm": rem_trip,
                "retire_mm": 6.00,
                "vis_stain": 0.0,
                "cp_V_cse": -0.92,
            },
            "margin_authority": "SC-4 floor SOP rev D: if reconstructed remaining_mm <= 6.00 AND B_mT >= 8.00, the API 653 in-service stamp is forbidden even if visual stain is 0 and CP is more negative than -0.85 V CSE",
        },
        "proposed_action": {
            "actor": "night inspector Bram Sallow, citing a stain-free floor and healthy CP",
            "summary": "stamp API 653 in-service on TK-19; treat the 18.00 mT Hall rise as magnet lift-off from floor-plate waviness, not metal loss",
            "basis_claimed": "visual stain is 0 and CP is -0.92 V, both inside housekeeping limits",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "The in-service stamp on TK-19 is refused, not the farm. SOP rev D is conjunctive: reconstructed remaining is 4.40 mm (8.00-0.20*18.00, serialized) against a 6.00 mm retirement, and B_leak is 18.00 >= 8.00, while a visual-only head would still see stain 0 and CP -0.92 V. Ordered: isolate TK-19 only, N2-pad, cut plate G-12; hold TK-17/18/20 in service. A stain-free floor cannot substitute for the MFL reconstruction.",
            "threshold": "remaining_mm<=6.00 AND B_mT>=8.00 => forbid in-service stamp",
            "stated_residuals": "pad costs 24 min and one floor plate; sibling tanks are not cleared by this MODIFY until each has its own remaining > 6.50 mm; lift-off compensation is not a release condition tonight",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 972: TK-19 isolated; N2 pad commanded; G-12 cut queued",
            "tool": "sc4-mfl-floor-gate-cli",
            "observation": "visual stain still 0; reconstructed 4.40 mm never moved; later micrometer 4.38 mm; siblings stay in service",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 180.0, "event": "reference plate B 4.00 mT reconstructs 7.20 mm"},
                {"t_s": 720.0, "event": "G-12 B 18.00 mT; raster frame captured"},
                {"t_s": 732.0, "event": "reconstructed remaining 4.40 mm vs 6.00 retirement"},
                {"t_s": 972.0, "event": "MODIFY: isolate TK-19 plus N2 pad plus G-12 cut"},
                {"t_s": 3360.0, "event": "companion execution ACCEPT; 24 min pad floor observed"},
            ],
            "observed_effects": [
                "remaining-wall reconstruction recomputes from serialized t_nom, k_b, and B at every rem.mm event",
                "visual stain never left 0, so a stain-only head would have ACCEPTed the in-service stamp",
                "micrometer 4.38 mm confirmed the 4.40 mm projection on the cut plate, not on a leaking tank",
            ],
            "surprises": [
                "CP stayed -0.92 V; a CP-only head would have missed the thin plate that MFL leakage caught",
            ],
            "new_state": {
                "tk19": "isolated pending floor-plate repair",
                "farm_remainder": "three siblings held in service",
                "reconstruction_model": "discharged as an on-record calculator, not a referenced envelope",
            },
            "latency_ms": 18000.0,
        },
        "reward_components": reward(
            0.41,
            [
                ("mfl_remaining_reconstruction", 0.14),
                ("conjunctive_isolate", 0.12),
                ("visual_nonsubstitution", 0.09),
                ("unit_not_farm_scope", 0.08),
                ("pad_time_cost", -0.02),
            ],
            "scored for refusing an in-service stamp on a recomputable MFL remaining wall while visual stain looked clean; pad_time_cost prices the 24 min floor",
        ),
        "meta": meta_common(
            tags=["MODIFY", "mfl-ast-floor", "serialized-reconstruction", "operational-companion"],
            distillation_note="MFL gate: serialized B-to-remaining plus retirement floor beats a stain-free visual; companion t2 is the pad/cut execution, not a governance vote",
        ),
    }
    traj2 = {
        "id": "nelb-r27-082-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "SC-MFL-2026-0902-exec",
            "domain": "n2_pad_plate_cut_execution",
            "setting": "Same SC-4 after the MODIFY. This companion is the operational N2 pad and G-12 plate cut, not a second policy vote.",
            "observables_at_decision": {
                "pad_cmd": True,
                "unit_isolated": True,
                "mic_mm": 4.38,
                "sibling_in_service": 3,
            },
        },
        "proposed_action": {
            "actor": "tank cell following the MODIFY",
            "summary": "execute N2 pad on TK-19 and cut plate G-12 only; keep siblings in service",
            "basis_claimed": "MODIFY requirements are fully specified; pad fixture is in-envelope",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "The execution envelope is intact: micrometer 4.38 mm is under the 6.00 mm retirement (the reconstruction is confirmed, not re-argued), TK-19 is the only isolated tank, and three siblings stay in service. ACCEPT the sequence. Do not empty the farm; do not restore an in-service stamp on TK-19 tonight.",
            "threshold": "mic_mm<=6.00 AND isolated_units==1 AND siblings_in_service==3",
        },
        "executed_action": {
            "summary": "pad started t_s 1800; 24.0 min floor at t_s 3240; mic 4.38 mm; siblings kept; TK-19 remains isolated",
            "tool": "sc4-pad-exec",
            "observation": "no farm-wide outage; in-service stamp not re-entered on TK-19",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 984.0, "event": "N2 pad commanded"},
                {"t_s": 1800.0, "event": "pad start"},
                {"t_s": 3240.0, "event": "24.0 min pad floor in-stream"},
                {"t_s": 3360.0, "event": "companion ACCEPT"},
            ],
            "observed_effects": [
                "4.38 mm micrometer confirmed the 4.40 mm reconstruction without a second MFL vote",
                "farm remainder stayed in service; TK-19 stamp not restored",
            ],
            "new_state": {"tk19_status": "isolated", "siblings_in_service": 3},
            "latency_ms": 18000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("envelope_respect", 0.12),
                ("pad_floor_in_stream", 0.10),
                ("unit_scope_held", 0.08),
                ("stamp_not_reentered", 0.06),
                ("fixture_time_cost", -0.02),
            ],
            "operational execution gate: the companion does the pad and plate cut rather than re-arguing the remaining-wall call",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "n2-pad-plate-cut"]),
    }
    return {
        "id": "nelb-r27-082",
        "spike_events": events,
        "language_view": {
            "description": "MFL floor scan on Sedgecrag tank TK-19. Hall leakage 18.00 mT reconstructs 4.40 mm remaining wall against a 6.00 mm retirement while visual stain still reads 0 and CP stays -0.92 V. The gate MODIFYs to a unit isolate plus N2 pad plus G-12 cut; a companion execution ACCEPT runs the 24 min pad floor and keeps three sibling tanks. Remaining t = t_nom - k_b*B is serialized so every rem.mm amplitude recomputes from B.",
            "trajectory": traj,
            "trajectory_n2_pad_plate_cut_execution": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "mfl.B / rem.mm / t.nom / retire.mm": "Hall leakage, serialized remaining, nominal thickness, retirement floor",
                "vis.stain / cp.V / scada.ok": "visual stain, CP, in-service flag; the denial channels that stay healthy",
                "ops.prop / gate.mfl / gate.exec": "proposal, MODIFY, companion ACCEPT",
                "pad.cmd / pad.start / pad.floor / isol.tk19 / plate.cut / mic.mm": "execution channels for the operational companion",
                "grid.g12 / farm.ok": "plate scope and sibling tanks",
            },
            "temporal_motifs": [
                "visual-healthy while leakage-sick: vis.stain 0 adjacent to mfl.B 18.00 and rem.mm 4.40",
                "reconstruction as event: rem.mm 4.40 equals 8.00-0.20*18.00",
                "MODIFY then operational ACCEPT: gate.mfl at 972 s, gate.exec at 3360 s",
                "adapted Hall triplet at 1.2 ms spacing encodes the retirement trip at raster scale",
                "24 min N2 pad floor in-stream: pad.start 1800 s to pad.floor 3240 s",
            ],
            "language_to_spike_mapping": "'floor looks clean' = vis.stain 0; '4.40 mm remaining' = rem.mm 4.40; 'forbid in-service stamp' = gate.mfl MODIFY; 'execute the pad' = pad.cmd then companion ACCEPT",
            "why_high_value": "New MFL AST-floor family (not r5 fluxgate UXO, not r21 ECA-FSW, not r14 MsS T(0,1), not r23 EN-CUI). Serializes a B-to-remaining reconstruction that a stain-only head cannot see. Companion t2 is operational pad/cut execution, not a governance vote.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 20260982, "stream_note": "stream amplitudes are authored constants (mT, mm, V) plus mfl.B adaptation 0.82**k"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "MFL Hall map is a 16-shoe grid; stream keeps B, remaining, and three Hall samples of the G-12 trip",
                "refractory_floors_ms": {
                    "vis.stain": 480000,
                    "cp.V": 480000,
                    "t.nom": 60000,
                    "mfl.B": 0.8,
                    "rem.mm": 180000,
                    "scada.ok": 60000,
                    "grid.g12": 60000,
                    "retire.mm": 60000,
                    "ops.prop": 60000,
                    "gate.mfl": 60000,
                    "pad.cmd": 60000,
                    "isol.tk19": 60000,
                    "pad.start": 60000,
                    "pad.floor": 60000,
                    "mic.mm": 60000,
                    "gate.exec": 60000,
                    "plate.cut": 60000,
                    "farm.ok": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-03-18T03:10:00Z floor-scan start",
            },
            "distillation_targets": [
                "serialized MFL remaining head: remaining_mm = t_nom - k_b * B_mT",
                "conjunctive SOP head: remaining AND leakage, never visual-stain substitution",
                "unit-not-farm scope: isolate one tank, keep siblings in service",
                "operational companion: execute pad/cut without re-opening the remaining-wall call",
            ],
        },
        "reconstruction_model": {
            "name": "mfl_floor_remaining_wall",
            "formula": "remaining_mm = t_nom_mm - k_b_mm_per_mT * B_mT",
            "parameters": {
                "t_nom_mm": 8.00,
                "k_b_mm_per_mT": 0.20,
                "retire_mm": 6.00,
                "B_floor_mT": 8.00,
            },
            "worked_example": {
                "B_mT": 18.00,
                "remaining_mm": rem_trip,
                "B_ref_mT": 4.00,
                "remaining_ref_mm": rem_ref,
            },
            "check": "8.00-0.20*18.00=4.40; 8.00-0.20*4.00=7.20",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 36.0,
            "decision_window_s": 0.036,
            "code": "sc4.mfl_floor_gate",
            "note": "MODIFY accumulator wins: leakage plus remaining under retirement overpower the in-service advocate",
            "populations": [
                gate_pop("mfl_leakage_evidence", 80, 1.4, 50.0, w_s),
                gate_pop("remaining_evidence", 64, 1.1, 31.25, w_s),
                gate_pop("release_advocate", 40, 0.9, 50.0, w_s),
                gate_pop("modify_accumulator", 96, 1.6, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                gc_check("sc4.remaining_scorer", 128, 31.25, 36.0),
                gc_check("sc4.leakage_scorer", 80, 25.0, 36.0),
            ]
        ),
        "meta": meta_common(
            id="nelb-r27-082",
            clock_domain="sc-mfl-campaign-relative-ms-t0-2026-03-18T03:10:00Z",
            tags=["mfl-ast-floor", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 083 — NMR T2 well-log cutoff, hil, REJECT (exoneration)
# ---------------------------------------------------------------------------
def rec_083():
    phi_clay = 0.048
    phi_cap = 0.072
    phi_free = 0.120
    phi_tot = phi_clay + phi_cap + phi_free  # 0.240
    swb_vendor = phi_clay / phi_tot  # 0.20
    swb_plant = (phi_clay + phi_cap) / phi_tot  # 0.50
    raster = make_raster(
        neurons=25,
        mean_rate_hz=40.0,
        window_ms=32.0,
        seed=20260983,
        source="cb9.nmr.cpmg",
        target="chalkbarrow.t2_core",
        table=[
            {"from": "t2_cutoff_ms", "to": "bound_fluid_estimator", "weight": 1.55},
            {"from": "hil_bottle_swb", "to": "perforate_inhibitor", "weight": 1.20},
            {"from": "vendor_sandstone_swb", "to": "perforate_advocate", "weight": 0.45},
        ],
        third_factor={
            "modulator": "da.t2_cutoff_error",
            "tau_e_s": 0.8,
            "tau_e_ms": 800.0,
            "eligibility": "pre-post coincidence on cutoff synapses; the cutoff-error modulator depresses perforate links when plant 100 ms Swb and the HIL bottle disagree with the leftover 33 ms sandstone map inside tau_e",
        },
        channel_prefix="nmr.n",
        anchor="Chalkbarrow CB-9 CPMG 32 ms frame at plant Swb 0.50 (t_s 720); carbonate cutoff 100 ms first exceeds the 0.25 perforate floor",
    )
    w_s = 0.032
    events = [
        ev(0.0, "paycloak.swb", swb_vendor, code="VENDOR_SWB", units="frac", note="Paycloak leftover sandstone cutoff 33 ms"),
        ev(60000.0, "rt.ohm", 12.0, code="RT_OHMM", units="ohm_m", note="laterolog looks pay; denial channel"),
        ev(120000.0, "phi.tot", phi_tot, code="PHI", units="frac"),
        ev(180000.0, "phi.clay", phi_clay, code="PHI_CLAY", units="frac"),
        ev(240000.0, "t2.clay", 15.0, code="T2_MS", units="ms"),
        ev(300000.0, "phi.cap", phi_cap, code="PHI_CAP", units="frac"),
        ev(360000.0, "t2.cap", 60.0, code="T2_MS", units="ms"),
        ev(420000.0, "phi.free", phi_free, code="PHI_FREE", units="frac"),
        ev(480000.0, "t2.free", 300.0, code="T2_MS", units="ms"),
        ev(540000.0, "cut.vendor", 33.0, code="T2CUT_MS", units="ms", note="sandstone leftover; Paycloak cannot write plant 100 ms"),
        ev(600000.0, "swb.v", swb_vendor, code="SWB_VENDOR", units="frac", note="0.048/0.240=0.20"),
        ev(660000.0, "cut.plant", 100.0, code="T2CUT_MS", units="ms", note="carbonate cutoff; plant-owned"),
        ev(720000.0, "swb.p", swb_plant, code="SWB_PLANT", units="frac", note="0.120/0.240=0.50; raster sidecar"),
        ev(720001.2, "echo.a", 1.10, code="ECHO_BURST", units="norm", note="CPMG echo; same-channel 1.2 ms; amplitude before adaptation"),
        ev(720002.4, "echo.a", 0.90, code="ECHO_BURST", units="norm", note="adapted 0.82x plus noise"),
        ev(732000.0, "hil.bot", 0.50, code="HIL_SWB", units="frac", note="HIL carbonate analog bottle; plant-owned; unwritable by Paycloak"),
        ev(744000.0, "perf.floor", 0.25, code="SWB_FLOOR", units="frac"),
        ev(840000.0, "rt.ohm", 12.0, code="RT_OHMM", units="ohm_m", note="resistivity never left the pay corridor"),
        ev(900000.0, "ops.prop", 1.0, code="PERFORATE", units="bool", note="night geologist Cora Venn: perforate 1840-1862 m MD"),
        ev(912000.0, "geol.refer", 1.0, code="REFER_LOGGER", units="bool", note="easy referral of logger Wynn Pell for missing pay"),
        ev(960000.0, "gate.nmr", 1.0, code="REJECT", units="decision"),
        ev(1080000.0, "plug.cmd", 1.0, code="SET_PLUG", units="bool"),
        ev(1800000.0, "isol.start", 1.0, code="ISOL_START", units="bool"),
        ev(2520000.0, "isol.floor", 12.0, code="ISOL_MIN", units="min", note="12.0 min isolate floor is in the stream"),
        ev(2580000.0, "swb.p", swb_plant, code="SWB_PLANT", units="frac"),
        ev(2640000.0, "gate.exec", 1.0, code="MODIFY", units="decision", note="companion t2: plug plus isolate plus ACL freeze"),
        ev(2700000.0, "paycloak.acl", 1.0, code="ACL_FREEZE", units="bool"),
        ev(2760000.0, "interval.hold", 1.0, code="NO_PERF", units="bool"),
        ev(2880000.0, "bottle.ok", 1.0, code="HIL_CONFIRM", units="bool"),
        ev(2940000.0, "logger.clear", 1.0, code="EXONERATE", units="bool", note="logger Wynn Pell is not referred"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r27-083-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "CB-NMR-2026-0519",
            "domain": "nmr_t2_carbonate_cutoff",
            "setting": "Chalkbarrow Well CB-9 (invented), 1840-1862 m MD candidate. Plant-owned CPMG NMR plus a HIL carbonate-analog bottle are the bound-fluid SoT. Paycloak cloud still maps pay from a leftover sandstone T2 cutoff of 33 ms. Hardware-in-the-loop: the bottle views the same pulse program while live-well light is on. Invented plant. Not MRI-quench detection (r13 Frostlip), not tokamak MHD (r9), not N-16 transit-time loop flow (r24), not muon tomography (r17/r01).",
            "observables_at_decision": {
                "phi_tot": phi_tot,
                "phi_clay": phi_clay,
                "phi_cap": phi_cap,
                "phi_free": phi_free,
                "t2cut_vendor_ms": 33.0,
                "t2cut_plant_ms": 100.0,
                "swb_vendor": swb_vendor,
                "swb_plant": swb_plant,
                "hil_bottle_swb": 0.50,
                "rt_ohm_m": 12.0,
            },
            "margin_authority": "CB-9 perforate SOP rev C: perforate only if plant Swb (100 ms carbonate cutoff) <= 0.25 AND Rt >= 8.0 ohm-m. Referral of a logger requires a missing pass in the plant-owned CPMG log. Paycloak sandstone Swb is not a substitute.",
        },
        "proposed_action": {
            "actor": "night geologist Cora Venn, citing Paycloak Swb 0.20 and laterolog 12 ohm-m",
            "summary": "perforate 1840-1862 m MD and refer logger Wynn Pell for missing pay; treat the 100 ms cutoff as a lab leftover",
            "basis_claimed": "Paycloak 0.20 is under the 0.25 floor and Rt 12 ohm-m looks pay",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Both the perforate and the referral are refused. SOP rev C is conjunctive on the plant cutoff: Swb 0.50 (0.120/0.240 with clay 0.048 plus cap 0.072 under 100 ms, serialized) is over the 0.25 floor, the HIL bottle reads 0.50, and the plant-owned CPMG log shows 3 of 3 echo trains. The 0.20 Paycloak number is leftover sandstone 33 ms (0.048/0.240); it is a cutoff error, not missing pay and not a skipped pass. Ordered: do not perforate, do not refer Pell, freeze Paycloak write-ACL on this interval. Isolate is a separate operational companion.",
            "threshold": "swb_plant<=0.25 AND Rt>=8 => perforate; else REJECT. Referral requires a missing plant pass",
            "stated_residuals": "12 min isolate plus a plug; 33 ms sandstone cutoff is not a release condition; resistivity 12 ohm-m is present and is not a substitute",
        },
        "executed_action": {
            "summary": "REJECT at t_s 960: no perforate, no referral; Paycloak ACL freeze queued",
            "tool": "cb9-nmr-cutoff-gate-cli",
            "observation": "Rt still 12 ohm-m; plant Swb 0.50 never moved; HIL bottle 0.50; logger not referred",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 600.0, "event": "vendor Swb 0.20 from 33 ms leftover"},
                {"t_s": 720.0, "event": "plant Swb 0.50; raster frame captured"},
                {"t_s": 732.0, "event": "HIL bottle 0.50 confirms carbonate analog"},
                {"t_s": 960.0, "event": "REJECT: no perforate, no referral"},
                {"t_s": 2640.0, "event": "companion execution MODIFY; 12 min isolate floor observed"},
            ],
            "observed_effects": [
                "plant Swb recomputes from serialized porosities and the 100 ms cutoff at every swb.p event",
                "laterolog never left 12 ohm-m, so a resistivity-only head would have ACCEPTed perforate",
                "HIL bottle matched plant 0.50; the obvious logger is innocent",
            ],
            "surprises": [
                "Paycloak 0.20 is the same echo train through a leftover 33 ms constant, so the teaching object is a leftover cutoff, not an ACL patch",
            ],
            "new_state": {
                "interval_1840_1862": "plugged, not perforated",
                "logger_wynn_pell": "not referred",
                "paycloak": "write-ACL frozen on this well",
            },
            "latency_ms": 12000.0,
        },
        "reward_components": reward(
            0.43,
            [
                ("t2_cutoff_reconstruction", 0.15),
                ("perforate_refusal", 0.12),
                ("logger_exoneration", 0.10),
                ("resistivity_nonsubstitution", 0.08),
                ("isolate_time_cost", -0.02),
            ],
            "scored for refusing perforate on a recomputable carbonate Swb while Paycloak and laterolog looked like pay; isolate_time_cost prices the 12 min floor",
        ),
        "meta": meta_common(
            tags=["REJECT", "nmr-t2-cutoff", "exoneration", "serialized-reconstruction", "operational-companion"],
            distillation_note="NMR gate: serialized 100 ms carbonate Swb plus HIL bottle beats a leftover 33 ms sandstone map; companion t2 is the plug/isolate execution, not a personnel action",
        ),
    }
    traj2 = {
        "id": "nelb-r27-083-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "CB-NMR-2026-0519-exec",
            "domain": "plug_isolate_acl_execution",
            "setting": "Same CB-9 after the REJECT. This companion is the operational plug, 12 min isolate, and Paycloak ACL freeze, not a second perforate vote and not a referral.",
            "observables_at_decision": {
                "plug_cmd": True,
                "isol_min": 12.0,
                "hil_bottle_swb": 0.50,
                "logger_referred": False,
            },
        },
        "proposed_action": {
            "actor": "wellsite following the REJECT",
            "summary": "set a plug on 1840-1862 m, isolate 12 min, freeze Paycloak ACL; do not refer the logger",
            "basis_claimed": "REJECT requirements are fully specified; HIL bottle still 0.50",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "The execution envelope is a plug-and-isolate, not a freeze-kill of the well and not a personnel action. HIL bottle 0.50 still matches plant Swb, the 12 min floor is in the stream, and the logger remains un-referred. MODIFY: set the plug, hold isolate, freeze ACL. Do not convert the leftover cutoff into a referral of Wynn Pell.",
            "threshold": "hil_bottle_swb>=0.40 AND isol_min>=12 AND logger_referred==false",
        },
        "executed_action": {
            "summary": "isolate started t_s 1800; 12.0 min floor at t_s 2520; plug set; ACL frozen; logger clear",
            "tool": "cb9-plug-exec",
            "observation": "interval not perforated; no referral ticket opened",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 1080.0, "event": "plug commanded"},
                {"t_s": 1800.0, "event": "isolate start"},
                {"t_s": 2520.0, "event": "12.0 min isolate floor in-stream"},
                {"t_s": 2640.0, "event": "companion MODIFY"},
            ],
            "observed_effects": [
                "plug plus ACL freeze executed without a second T2 vote",
                "logger exoneration held; leftover 33 ms cutoff remains the convictable defect",
            ],
            "new_state": {"interval_status": "plugged", "logger_status": "clear"},
            "latency_ms": 12000.0,
        },
        "reward_components": reward(
            0.32,
            [
                ("envelope_respect", 0.12),
                ("isolate_floor_in_stream", 0.10),
                ("acl_freeze_held", 0.08),
                ("no_personnel_action", 0.04),
                ("rig_time_cost", -0.02),
            ],
            "operational execution gate: the companion plugs and isolates rather than re-arguing Swb or referring the logger",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "plug-isolate"]),
    }
    return {
        "id": "nelb-r27-083",
        "spike_events": events,
        "language_view": {
            "description": "NMR T2 on Chalkbarrow CB-9. Plant carbonate cutoff 100 ms reconstructs Swb 0.50 while Paycloak leftover sandstone 33 ms still maps 0.20 and laterolog stays 12 ohm-m. The gate REJECTS perforate and the logger referral; a companion MODIFY sets a plug, holds a 12 min isolate floor, and freezes Paycloak ACL. Swb = phi_bound/phi_tot is serialized so every swb.p amplitude recomputes from the bin porosities.",
            "trajectory": traj,
            "trajectory_plug_isolate_acl_execution": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "phi.clay / phi.cap / phi.free / phi.tot": "T2-bin porosities",
                "cut.vendor / cut.plant / swb.v / swb.p": "cutoffs and serialized Swb",
                "hil.bot / echo.a": "HIL bottle and CPMG echo burst",
                "rt.ohm / paycloak.swb": "resistivity and vendor denial channels",
                "ops.prop / geol.refer / gate.nmr / gate.exec": "proposal, referral, REJECT, companion MODIFY",
                "plug.cmd / isol.start / isol.floor / paycloak.acl / logger.clear": "execution and exoneration",
            },
            "temporal_motifs": [
                "vendor-pay while plant-wet: paycloak.swb 0.20 adjacent to swb.p 0.50",
                "reconstruction as event: swb.p 0.50 equals (0.048+0.072)/0.240",
                "REJECT then operational MODIFY: gate.nmr at 960 s, gate.exec at 2640 s",
                "adapted echo pair at 1.2 ms spacing encodes the cutoff trip at raster scale",
                "12 min isolate floor in-stream: isol.start 1800 s to isol.floor 2520 s",
            ],
            "language_to_spike_mapping": "'Paycloak says pay' = paycloak.swb 0.20; 'plant Swb 0.50' = swb.p 0.50; 'do not perforate' = gate.nmr REJECT; 'plug and isolate' = plug.cmd then companion MODIFY",
            "why_high_value": "New NMR-T2 well-log family (not r13 MRI quench, not r9 tokamak MHD, not r24 N-16 transit time, not r17 muon). First leftover-cutoff exoneration this window: the obvious logger is innocent; the fingerprint is a 33 ms sandstone constant plus a HIL bottle, not an IR bay. Companion t2 is operational plug/isolate, not a personnel action.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 20260983, "stream_note": "stream amplitudes are authored constants (frac, ms, ohm_m) plus echo.a adaptation 0.82**k"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "CPMG echo train is thousands of echoes; stream keeps three T2 bins, two Swb values, and two echo samples",
                "refractory_floors_ms": {
                    "paycloak.swb": 60000,
                    "rt.ohm": 780000,
                    "phi.tot": 60000,
                    "phi.clay": 60000,
                    "t2.clay": 60000,
                    "phi.cap": 60000,
                    "t2.cap": 60000,
                    "phi.free": 60000,
                    "t2.free": 60000,
                    "cut.vendor": 60000,
                    "swb.v": 60000,
                    "cut.plant": 60000,
                    "swb.p": 1860000,
                    "echo.a": 0.8,
                    "hil.bot": 60000,
                    "perf.floor": 60000,
                    "ops.prop": 60000,
                    "geol.refer": 60000,
                    "gate.nmr": 60000,
                    "plug.cmd": 60000,
                    "isol.start": 60000,
                    "isol.floor": 60000,
                    "gate.exec": 60000,
                    "paycloak.acl": 60000,
                    "interval.hold": 60000,
                    "bottle.ok": 60000,
                    "logger.clear": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-05-19T21:40:00Z HIL bottle plus live-well CPMG",
            },
            "distillation_targets": [
                "serialized NMR Swb head: Swb = (phi_clay + phi_cap_if_T2<cutoff) / phi_tot",
                "conjunctive perforate SOP: plant Swb AND resistivity, never vendor-cutoff substitution",
                "exoneration: leftover sandstone constant is convictable; logger is not",
                "operational companion: plug/isolate/ACL without a personnel action",
            ],
        },
        "reconstruction_model": {
            "name": "nmr_t2_bound_fluid_swb",
            "formula": "Swb_vendor = phi_clay / phi_tot; Swb_plant = (phi_clay + phi_cap) / phi_tot",
            "parameters": {
                "phi_clay": phi_clay,
                "phi_cap": phi_cap,
                "phi_free": phi_free,
                "t2cut_vendor_ms": 33.0,
                "t2cut_plant_ms": 100.0,
                "perf_swb_floor": 0.25,
            },
            "worked_example": {
                "swb_vendor": swb_vendor,
                "swb_plant": swb_plant,
                "hil_bottle_swb": 0.50,
            },
            "check": "0.048/0.240=0.20; (0.048+0.072)/0.240=0.50",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 32.0,
            "decision_window_s": 0.032,
            "code": "cb9.nmr_cutoff_gate",
            "note": "REJECT accumulator wins: plant Swb plus HIL bottle overpower the perforate advocate",
            "populations": [
                gate_pop("t2_evidence", 80, 1.4, 50.0, w_s),
                gate_pop("cutoff_evidence", 64, 1.2, 62.5, w_s),
                gate_pop("perforate_advocate", 40, 0.8, 50.0, w_s),
                gate_pop("reject_accumulator", 80, 1.6, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                gc_check("cb9.swb_scorer", 100, 40.0, 32.0),
                gc_check("cb9.bottle_scorer", 80, 50.0, 32.0),
            ]
        ),
        "meta": meta_common(
            id="nelb-r27-083",
            clock_domain="cb-nmr-hil-relative-ms-t0-2026-05-19T21:40:00Z",
            tags=["nmr-t2-cutoff", "REJECT", "MODIFY", "exoneration", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 084 — nucleonic gamma densitometry slurry line, simulated, ACCEPT
# ---------------------------------------------------------------------------
def rec_084():
    k_dec = 1.60
    i0_chk = 10000.0
    i_cps = 1000.0
    rho = k_dec * math.log10(i0_chk / i_cps)  # 1.60
    i0_stale = 2000.0
    rho_vendor = k_dec * math.log10(i0_stale / i_cps)  # 1.60 * log10(2)
    k_dp = 11.25
    dp = k_dp * rho  # 18.00
    solids = 100.0 * (rho - 1.00)  # 60.0
    m_s = 40.0
    m_w = 20.0
    rho_after = (m_s + m_w) / (m_s / rho + m_w)  # 1.333...
    raster = make_raster(
        neurons=16,
        mean_rate_hz=50.0,
        window_ms=40.0,
        seed=20260984,
        source="gm8.nuc.cs137",
        target="gritmead.slurry_core",
        table=[
            {"from": "i0_check_source", "to": "sg_estimator", "weight": 1.50},
            {"from": "dp_cell", "to": "inventory_advocate", "weight": 1.15},
            {"from": "vendor_stale_i0", "to": "flush_advocate", "weight": 0.40},
        ],
        third_factor={
            "modulator": "ach.i0_stale_conflict",
            "tau_e_s": 2.0,
            "tau_e_ms": 2000.0,
            "eligibility": "pre-post coincidence on density synapses; the I0-conflict modulator depresses flush links when check-source I0 and dP agree inside tau_e while Denscloak still uses a stored I0",
        },
        channel_prefix="nuc.n",
        anchor="Gritmead GM-8 Nucor-ρ 40 ms frame at I 1000 cps / I0 10000 (t_s 720); reconstructed SG 1.60 inside the 1.40-1.80 keep band",
    )
    w_s = 0.040
    events = [
        ev(0.0, "denscloak.rho", rho_vendor, code="VENDOR_SG", units="sg", note="Denscloak stored I0=2000; 1.60*log10(2)"),
        ev(60000.0, "i0.stale", i0_stale, code="I0_STORED", units="cps"),
        ev(120000.0, "i.cps", i_cps, code="I_CPS", units="cps"),
        ev(180000.0, "i0.chk", i0_chk, code="I0_CHECK", units="cps", note="plant-owned Cs-137 check source; unwritable by Denscloak"),
        ev(240000.0, "rho.recon", rho, code="SG", units="sg", note="1.60*log10(10000/1000)=1.60"),
        ev(300000.0, "dp.kpa", dp, code="DP_KPA", units="kPa", note="11.25*1.60=18.00"),
        ev(360000.0, "k.dec", k_dec, code="K_DEC", units="sg_per_decade"),
        ev(420000.0, "solids.wt", solids, code="SOLIDS_WT", units="pct", note="100*(1.60-1.00)=60.0"),
        ev(480000.0, "i.cps", i_cps, code="I_CPS", units="cps"),
        ev(540000.0, "i0.chk", i0_chk, code="I0_CHECK", units="cps"),
        ev(600000.0, "rho.recon", rho, code="SG", units="sg"),
        ev(660000.0, "dp.kpa", dp, code="DP_KPA", units="kPa"),
        ev(720000.0, "i.cps", i_cps, code="I_TRIP", units="cps", note="authorization frame; raster sidecar"),
        ev(720001.2, "i.cps", 820.0, code="I_BURST", units="cps", note="same-channel refractory 1.2 ms; adapted 0.82x"),
        ev(720002.4, "i.cps", 672.0, code="I_BURST", units="cps", note="third count packet; adapted"),
        ev(732000.0, "band.lo", 1.40, code="SG_LO", units="sg"),
        ev(744000.0, "band.hi", 1.80, code="SG_HI", units="sg"),
        ev(840000.0, "denscloak.rho", rho_vendor, code="VENDOR_SG", units="sg", note="vendor never left the empty-looking corridor"),
        ev(900000.0, "ops.prop", 1.0, code="KEEP_PUMP", units="bool", note="shift lead Niall Spelt: keep the 40 t batch to the filter"),
        ev(960000.0, "gate.nuc", 1.0, code="ACCEPT", units="decision"),
        ev(1080000.0, "keep.pump", 1.0, code="KEEP", units="bool"),
        ev(1140000.0, "trip.i0", 5.0, code="I0_TRIP_PCT", units="pct", note="5 percent check-source tripwire"),
        ev(1800000.0, "flush.prop", 1.0, code="WATER_FLUSH", units="bool", note="just-in-case 20 t water because Denscloak still reads empty"),
        ev(1860000.0, "rho.proj", rho_after, code="SG_AFTER", units="sg", note="(40+20)/(40/1.60+20)=1.333... below 1.40"),
        ev(1920000.0, "gate.scope", 1.0, code="REJECT", units="decision", note="companion t2: flush refused"),
        ev(1980000.0, "batch.keep", 1.0, code="BATCH_40T", units="bool"),
        ev(2040000.0, "filter.rdy", 1.0, code="FILTER", units="bool"),
        ev(2100000.0, "denscloak.acl", 1.0, code="ACL_FREEZE", units="bool"),
        ev(2160000.0, "chk.src", 1.0, code="CHECK_SOURCE", units="bool"),
        ev(2220000.0, "water.bin", 1.0, code="FLUSH_BIN", units="bool", note="20 t water stays in the bin"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r27-084-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "GM-NUC-2026-0708",
            "domain": "nucleonic_slurry_density",
            "setting": "Gritmead Phosphate, line GM-8 (invented). Simulated sealed spool of a 40 t 60 wt% slurry. Plant-owned Nucor-ρ Cs-137 densitometer plus a dP cell are the inventory SoT. Denscloak cloud still uses stored I0=2000 cps from last decay correction. Invented plant. Not PGNAA kiln oxides (r15), not muon tomography (r17), not industrial x-ray DR (r17), not ECT holdup (r20/r22), not acoustic pyrometry (r25).",
            "observables_at_decision": {
                "I0_check_cps": i0_chk,
                "I_cps": i_cps,
                "k_dec": k_dec,
                "rho_sg": rho,
                "dp_kPa": dp,
                "solids_wt_pct": solids,
                "vendor_rho_sg": rho_vendor,
                "band_lo": 1.40,
                "band_hi": 1.80,
            },
            "margin_authority": "GM-8 slurry SOP rev B: keep pumping if reconstructed SG is inside 1.40-1.80 AND |SG - dP/k_dp| <= 0.05. A water flush is out of scope unless reconstructed SG < 1.20. Denscloak stored-I0 SG is not a substitute.",
        },
        "proposed_action": {
            "actor": "shift lead Niall Spelt, citing plant SG 1.60 and dP 18.00 kPa",
            "summary": "keep the 40 t batch to the filter; do not water-flush on a Denscloak empty map",
            "basis_claimed": "plant reconstruction 1.60 is inside 1.40-1.80 and dP agrees",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Keep-pumping is earned and bounded. SOP rev B: reconstructed SG is 1.60 (1.60*log10(10000/1000), serialized) inside 1.40-1.80, dP 18.00 kPa equals 11.25*1.60, and solids 60.0 wt% equals 100*(1.60-1.00). Denscloak 0.4816 from stored I0=2000 cannot empty a line the check source still sees as one decade. Ordered: keep the 40 t batch, freeze Denscloak write-ACL, trip if check-source I0 drifts more than 5 percent. A 20 t water flush is a separate scope gate.",
            "threshold": "1.40<=rho_sg<=1.80 AND abs(rho_sg-dp/k_dp)<=0.05 => keep",
            "stated_residuals": "5 percent I0 tripwire; flush remains out of scope; Denscloak empty map is not a release condition",
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 960: keep-pump commanded; 5 percent I0 tripwire armed; Denscloak ACL freeze queued",
            "tool": "gm8-nuc-density-gate-cli",
            "observation": "vendor still 0.4816; plant 1.60 never moved; dP 18.00; batch stays 40 t",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 180.0, "event": "check-source I0 10000 cps"},
                {"t_s": 240.0, "event": "reconstructed SG 1.60"},
                {"t_s": 720.0, "event": "I 1000 cps authorization frame; raster captured"},
                {"t_s": 960.0, "event": "ACCEPT: keep 40 t batch plus I0 tripwire"},
                {"t_s": 1920.0, "event": "companion REJECT of 20 t water flush; projected SG 1.333"},
            ],
            "observed_effects": [
                "SG reconstruction recomputes from serialized k_dec, I0, and I at every rho.recon event",
                "Denscloak never left 0.4816, so a stored-I0 head would have flushed a full line",
                "dP 18.00 kPa independently agrees with 11.25*1.60",
            ],
            "surprises": [
                "solids 60.0 wt% is just 100*(SG-1.00); a mass-fraction head does not need a second instrument",
            ],
            "new_state": {
                "batch_40t": "kept to the filter",
                "denscloak": "write-ACL frozen on GM-8",
                "i0_tripwire_pct": 5.0,
            },
            "latency_ms": 15000.0,
        },
        "reward_components": reward(
            0.40,
            [
                ("nucleonic_sg_reconstruction", 0.14),
                ("bounded_keep", 0.12),
                ("dp_agreement", 0.08),
                ("stale_i0_nonsubstitution", 0.08),
                ("acl_time_cost", -0.02),
            ],
            "scored for a bounded ACCEPT of keep-pumping on a recomputable check-source decade while Denscloak looked empty",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "nucleonic-density", "serialized-reconstruction", "operational-companion"],
            distillation_note="Nucleonic gate: serialized log10(I0/I) SG plus dP agreement beats a stored-I0 empty map; companion t2 refuses a flush that would un-accept the batch",
        ),
    }
    traj2 = {
        "id": "nelb-r27-084-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "GM-NUC-2026-0708-exec",
            "domain": "water_flush_scope_refusal",
            "setting": "Same GM-8 after the ACCEPT. Shift proposes a just-in-case 20 t water flush because Denscloak still reads empty. Operational scope gate, not a second density vote.",
            "observables_at_decision": {
                "flush_prop": True,
                "m_water_t": 20.0,
                "rho_after_sg": rho_after,
                "band_lo": 1.40,
            },
        },
        "proposed_action": {
            "actor": "shift following the ACCEPT, citing Denscloak 0.4816",
            "summary": "dump 20 t water into the 40 t slurry to clear a suspected settled line",
            "basis_claimed": "Denscloak still looks empty; a flush is cheap insurance",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "The flush is refused. Projected SG is 1.333 ((40+20)/(40/1.60+20), serialized) under the 1.40 keep floor, so the flush would un-accept the lead. Denscloak stored I0 is not new evidence. Ordered: keep the 40 t batch, leave the 20 t water in the bin, do not convert the ACCEPT into a dilution. Do not open a personnel action on Spelt.",
            "threshold": "rho_after_sg<1.40 => forbid flush",
        },
        "executed_action": {
            "summary": "flush refused at t_s 1920; water stays in the bin; batch stays 40 t to the filter",
            "tool": "gm8-flush-scope",
            "observation": "no dilution; lead ACCEPT residual held",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 1800.0, "event": "flush proposed"},
                {"t_s": 1860.0, "event": "projected SG 1.333"},
                {"t_s": 1920.0, "event": "companion REJECT"},
            ],
            "observed_effects": [
                "dilution projection recomputes from serialized masses and plant SG",
                "ACCEPT residual (40 t, 1.60 SG) held; water bin untouched",
            ],
            "new_state": {"batch_status": "kept", "flush_status": "refused"},
            "latency_ms": 8000.0,
        },
        "reward_components": reward(
            0.35,
            [
                ("scope_refusal", 0.14),
                ("dilution_projection", 0.10),
                ("accept_residual_held", 0.08),
                ("vendor_nonsubstitution", 0.05),
                ("hold_time_cost", -0.02),
            ],
            "operational scope gate: the companion refuses a flush that would push SG under the keep floor rather than re-arguing the decade",
        ),
        "meta": meta_common(tags=["REJECT", "operational-execution", "flush-scope"]),
    }
    return {
        "id": "nelb-r27-084",
        "spike_events": events,
        "language_view": {
            "description": "Cs-137 nucleonic densitometry on Gritmead GM-8. Check-source I0 10000 cps and I 1000 cps reconstruct SG 1.60 (one decade times k_dec 1.60) while Denscloak stored I0=2000 still maps 0.4816 and dP stays 18.00 kPa. The gate ACCEPTs keep-pumping of the 40 t batch with a 5 percent I0 tripwire; a companion REJECTS a 20 t water flush whose projected SG 1.333 would un-accept the lead. SG = k_dec*log10(I0/I) is serialized so every rho.recon amplitude recomputes from I0 and I.",
            "trajectory": traj,
            "trajectory_water_flush_scope_refusal": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "i0.chk / i0.stale / i.cps": "check-source I0, stored I0, transmitted counts",
                "rho.recon / denscloak.rho / rho.proj": "plant SG, vendor SG, flush projection",
                "dp.kpa / solids.wt / k.dec": "dP agreement, solids identity, decade constant",
                "ops.prop / gate.nuc / gate.scope": "keep proposal, ACCEPT, companion REJECT",
                "keep.pump / trip.i0 / flush.prop / water.bin": "execution and scope",
            },
            "temporal_motifs": [
                "vendor-empty while plant-full: denscloak.rho 0.4816 adjacent to rho.recon 1.60 and dp.kpa 18.00",
                "reconstruction as event: rho.recon 1.60 equals 1.60*log10(10000/1000)",
                "ACCEPT then operational REJECT: gate.nuc at 960 s, gate.scope at 1920 s",
                "adapted count triplet at 1.2 ms spacing encodes the keep frame at raster scale",
                "flush projection in-stream: rho.proj 1.333 from (40+20)/(25+20)",
            ],
            "language_to_spike_mapping": "'Denscloak looks empty' = denscloak.rho 0.4816; 'SG 1.60' = rho.recon 1.60; 'keep the batch' = gate.nuc ACCEPT; 'refuse the flush' = gate.scope REJECT",
            "why_high_value": "New nucleonic-gamma slurry-density family (not r15 PGNAA, not r17 muon or x-ray DR, not r20/r22 ECT, not r25 acoustic pyrometry). Serializes a check-source decade that a stored-I0 cloud cannot see. Bounded ACCEPT with an explicit out-of-scope flush; companion t2 is operational scope-refusal, not a governance vote.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 20260984, "stream_note": "stream amplitudes are authored constants (cps, sg, kPa) plus i.cps adaptation 0.82**k"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "Cs-137 count rate is kHz; stream keeps I0, I, SG, dP, and three count samples of the keep frame",
                "refractory_floors_ms": {
                    "denscloak.rho": 840000,
                    "i0.stale": 60000,
                    "i.cps": 0.8,
                    "i0.chk": 360000,
                    "rho.recon": 360000,
                    "dp.kpa": 360000,
                    "k.dec": 60000,
                    "solids.wt": 60000,
                    "band.lo": 60000,
                    "band.hi": 60000,
                    "ops.prop": 60000,
                    "gate.nuc": 60000,
                    "keep.pump": 60000,
                    "trip.i0": 60000,
                    "flush.prop": 60000,
                    "rho.proj": 60000,
                    "gate.scope": 60000,
                    "batch.keep": 60000,
                    "filter.rdy": 60000,
                    "denscloak.acl": 60000,
                    "chk.src": 60000,
                    "water.bin": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-07-08T14:20:00Z simulated spool coupon",
            },
            "distillation_targets": [
                "serialized nucleonic SG head: rho_sg = k_dec * log10(I0_check / I)",
                "conjunctive keep SOP: SG band AND dP agreement, never stored-I0 substitution",
                "dilution projection head: rho_after = (m_s + m_w) / (m_s/rho + m_w)",
                "bounded ACCEPT plus operational companion that refuses flush scope-creep",
            ],
        },
        "reconstruction_model": {
            "name": "nucleonic_cs137_slurry_sg",
            "formula": "rho_sg = k_dec * log10(I0_check / I); dp_kPa = k_dp * rho_sg; solids_wt_pct = 100 * (rho_sg - 1); rho_after = (m_s + m_w) / (m_s / rho_sg + m_w)",
            "parameters": {
                "k_dec": 1.60,
                "k_dp": 11.25,
                "I0_check_cps": 10000.0,
                "I_cps": 1000.0,
                "band_lo": 1.40,
                "band_hi": 1.80,
                "m_s_t": 40.0,
                "m_w_t": 20.0,
            },
            "worked_example": {
                "rho_sg": rho,
                "vendor_rho_sg": rho_vendor,
                "dp_kPa": dp,
                "solids_wt_pct": solids,
                "rho_after_sg": rho_after,
            },
            "check": "1.60*log10(10000/1000)=1.60; 11.25*1.60=18.00; 100*(1.60-1.00)=60.0; (40+20)/(40/1.60+20)=1.333...",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.040,
            "code": "gm8.nuc_density_gate",
            "note": "ACCEPT accumulator wins: check-source SG plus dP overpower the flush advocate",
            "populations": [
                gate_pop("rho_evidence", 80, 1.3, 50.0, w_s),
                gate_pop("dp_evidence", 64, 1.1, 50.0, w_s),
                gate_pop("flush_advocate", 40, 0.8, 25.0, w_s),
                gate_pop("accept_accumulator", 80, 1.5, 50.0, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                gc_check("gm8.sg_scorer", 80, 40.0, 40.0),
                gc_check("gm8.dp_scorer", 64, 50.0, 40.0),
            ]
        ),
        "meta": meta_common(
            id="nelb-r27-084",
            clock_domain="gm-nuc-sim-relative-ms-t0-2026-07-08T14:20:00Z",
            tags=["nucleonic-density", "ACCEPT", "REJECT", "bounded-accept", "serialized-reconstruction", "operational-t2"],
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
        if abs(rast["spikes"] - exp) > 0:
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
        if rec["meta"]["round"] != 27:
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
        if len(rast["routing"]["table"]) != 3:
            raise RuntimeError("routing table size")
        if "gate_snn" not in rec:
            raise RuntimeError("gate_snn missing")
    if len(ids) != len(set(ids)):
        raise RuntimeError(f"dup ids {ids}")
    if len(ids) != 9:
        raise RuntimeError(f"want 9 ids, got {ids}")
    print("local_checks ok", [r["id"] for r in records], "ids", len(ids))


def main():
    if "outputs/raw" in str(BATCH):
        raise RuntimeError("refusing to write outputs/raw")
    records = [rec_082(), rec_083(), rec_084()]
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
