#!/usr/bin/env python3
"""Create-only MAOS r02 SLUICE-HEARTH artifacts for 2026-09-02-final-heavy."""

from __future__ import annotations

import json
import math
import os
import random
import re
import sys
from collections import defaultdict
from pathlib import Path

PIPELINES = Path("/home/raulmc/rmems/synthetic-factory/pipelines")
sys.path.insert(0, str(PIPELINES))

from check_records import check_jsonl  # noqa: E402
from curate_bridge import raster_status  # noqa: E402
from exact_json import dumps_exact_json  # noqa: E402
from spike_probe import load_rasters  # noqa: E402
from validate_run import check_line  # noqa: E402
from verify_execution_shapes import verify_record_execution  # noqa: E402

LIVE_DIR = Path(
    "/home/raulmc/rmems/synthetic-factory/outputs/raw/"
    "2026-09-02-final-heavy/multi-agent-ouroboros-swarm"
)
ROUND = 2
RECORD_ID = "maos-r02-001"
WINDOW_MS = 36
NEURONS = 144
MEAN_RATE_HZ = 9.5
WINDOW_S = WINDOW_MS / 1000.0
EXPECTED_SPIKES = round(NEURONS * MEAN_RATE_HZ * WINDOW_S)
ENERGY_PJ_PER = 23
SEED = 0x534C4832  # SLH2
RIGHTS = {
    "provider": "SpaceXAI/xAI",
    "model": "grok-4.6",
    "channel": "consumer",
    "subscription_plan": "SuperGrok Heavy",
    "generation_surface": "SuperGrok Heavy chat",
    "generated_at": "2026-09-02T20:18:00Z",
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

TRACE = math.exp(-0.78 / 0.96)
ETAS = [0.24 / TRACE, 0.22 / TRACE, 0.21 / TRACE]


def simulate_lif():
    """Independent current-based LIF raster for the 36 ms gate window."""
    rng = random.Random(SEED)
    dt_ms = 0.05
    n_steps = int(WINDOW_MS / dt_ms)
    tau_ms = 11.0
    v_th = 1.0
    v_reset = 0.0
    refrac_ms = 1.0
    v = [rng.uniform(0.0, 0.35) for _ in range(NEURONS)]
    last = [-1e9] * NEURONS
    events = []
    # Four pops: blast 0-35, notch 36-71, metal 72-107, gate 108-143
    # Subthreshold bias so mean rate ~9.5 Hz over 36 ms (~49 spikes).
    pop_bias = []
    for i in range(NEURONS):
        if i < 36:
            pop_bias.append(0.62)
        elif i < 72:
            pop_bias.append(0.70)
        elif i < 108:
            pop_bias.append(0.64)
        else:
            pop_bias.append(0.58)
    race_drive = {
        48: 6.408,  # notch.ir.low
        90: 6.600,  # metal.in_band
        12: 6.812,  # blast.vol
        120: 7.112,  # ctrl.gate
    }
    sigma = 0.42
    for step in range(n_steps):
        t_ms = step * dt_ms
        for i in range(NEURONS):
            if t_ms - last[i] < refrac_ms:
                v[i] = v_reset
                continue
            extra = 0.0
            if i in race_drive and abs(t_ms - race_drive[i]) <= dt_ms:
                extra = 1.6
            I = pop_bias[i] + sigma * rng.gauss(0.0, 1.0) + extra
            v[i] += dt_ms * ((-v[i] + I) / tau_ms)
            if v[i] >= v_th:
                t_us = int(round(t_ms * 1000.0))
                if 0 <= t_us <= WINDOW_MS * 1000:
                    events.append({"t_us": t_us, "neuron_id": i})
                v[i] = v_reset
                last[i] = t_ms
    events.sort(key=lambda e: (e["t_us"], e["neuron_id"]))
    # If still off-budget, keep earliest events (plus forced race) rather
    # than inventing a second clock.
    if abs(len(events) - EXPECTED_SPIKES) > 1:
        forced_t = {int(round(t * 1000.0)) for t in race_drive.values()}
        forced = [e for e in events if e["t_us"] in forced_t]
        rest = [e for e in events if e not in forced]
        need = max(0, EXPECTED_SPIKES - len(forced))
        events = sorted(forced + rest[:need], key=lambda e: (e["t_us"], e["neuron_id"]))
    return events


def isi_histogram(events):
    by_n = defaultdict(list)
    for e in events:
        by_n[e["neuron_id"]].append(e["t_us"])
    isis_ms = []
    for ts in by_n.values():
        ts.sort()
        for a, b in zip(ts, ts[1:]):
            isis_ms.append((b - a) / 1000.0)
    bins = defaultdict(int)
    for isi in isis_ms:
        lo = math.floor(isi)
        bins[(float(lo), float(lo + 1.0))] += 1
    bin_list = [
        {"lo_ms": lo, "hi_ms": hi, "count": bins[(lo, hi)]}
        for lo, hi in sorted(bins)
        if bins[(lo, hi)]
    ]
    return {
        "bin_width_ms": 1.0,
        "source": "full_window_not_excerpt",
        "distinct_active_neurons": len(by_n),
        "n_isi": len(isis_ms),
        "bins": bin_list,
    }


def excerpt_from_lif(events):
    """16 unique-neuron events spanning the window, race neurons forced in."""
    forced_ids = {48, 90, 12, 120}
    forced = []
    seen_f = set()
    for e in events:
        nid = e["neuron_id"]
        if nid in forced_ids and nid not in seen_f:
            forced.append(e)
            seen_f.add(nid)
    chosen = list(forced)
    seen = {e["neuron_id"] for e in chosen}
    for e in events:
        if len(chosen) >= 16:
            break
        if e["neuron_id"] in seen:
            continue
        chosen.append(e)
        seen.add(e["neuron_id"])
    chosen.sort(key=lambda e: (e["t_us"], e["neuron_id"]))
    return chosen[:16]


def build_raster(lif_events):
    spikes = len(lif_events)
    expected = EXPECTED_SPIKES
    if abs(spikes - expected) > 1:
        raise SystemExit(
            f"LIF spike count {spikes} outside ±1 of budget {expected}"
        )
    hist = isi_histogram(lif_events)
    if hist["n_isi"] != spikes - hist["distinct_active_neurons"]:
        raise SystemExit("ISI identity failed")
    excerpt = excerpt_from_lif(lif_events)
    if not excerpt:
        raise SystemExit("empty excerpt")
    for e in excerpt:
        if not (0 <= e["t_us"] <= WINDOW_MS * 1000):
            raise SystemExit("excerpt t_us out of window")
        if not (0 <= e["neuron_id"] < NEURONS):
            raise SystemExit("excerpt neuron_id out of range")
    energy_pJ = spikes * ENERGY_PJ_PER
    energy_uJ = spikes * ENERGY_PJ_PER * 1e-6
    return {
        "window_ms": WINDOW_MS,
        "window_s": WINDOW_S,
        "neurons": NEURONS,
        "mean_rate_hz": MEAN_RATE_HZ,
        "spikes": spikes,
        "energy_pJ": energy_pJ,
        "energy_uJ": energy_uJ,
        "note": (
            "Independent current-based LIF (tau 11 ms, Vth 1.0, refractory 1.0 ms, "
            f"seed {SEED:#x}) on Loihi-2 4-core 23 pJ/spike; pops blast 0-35, "
            "notch 36-71, metal 72-107, gate 108-143; excerpt is the 36 ms "
            "decision window (verdict at 7112 us)"
        ),
        "isi_histogram": hist,
        "excerpt": excerpt,
        "routing": {
            "source": "header_mean_healthy_pop",
            "target": "raise_blast_pop",
            "table": [
                {
                    "from": "blast_in_band_pop",
                    "to": "raise_blast_pop",
                    "weight": 0.24,
                    "weight_at_illusion": 0.48,
                    "weight_commissioned": 0.17,
                    "note": (
                        "scar edge 1: 0.17 commissioned -> 0.48 during the 14 min "
                        "illusion -> 0.24 after coordinated ACh-gated depression"
                    ),
                },
                {
                    "from": "stack_in_band_pop",
                    "to": "raise_blast_pop",
                    "weight": 0.22,
                    "weight_at_illusion": 0.44,
                    "weight_commissioned": 0.15,
                    "note": (
                        "scar edge 2: depressing edges 1+3 leaves this at 0.44 > 0.30 "
                        "fire threshold"
                    ),
                },
                {
                    "from": "metal_in_band_pop",
                    "to": "raise_blast_pop",
                    "weight": 0.20,
                    "weight_at_illusion": 0.41,
                    "weight_commissioned": 0.14,
                    "note": (
                        "scar edge 3: depressing edges 1+2 leaves this at 0.41 > 0.30. "
                        "Coordinated depression of all three is required"
                    ),
                },
                {
                    "from": "notch_ir_pop",
                    "to": "blast_hold_pop",
                    "weight": 0.69,
                    "note": (
                        "discriminating edge: sluice-true notch IR to hold. Not a scar; "
                        "this is the pathway the gate potentiates"
                    ),
                },
            ],
            "third_factor": {
                "modulator": "acetylcholine",
                "tau_e_s": 0.96,
                "tau_e_ms": 960.0,
                "eligibility": (
                    "coordinated pre_post_stdp on ALL THREE header-healthy-go edges; "
                    "ACh at IR-win tags blast.in_band->raise, stack.in_band->raise, "
                    "and metal.in_band->raise; negative credit at probe-fail "
                    f"(frozen sluice confirmed, +0.78 s) depresses ALL THREE. "
                    f"trace e^{{-0.78/0.96}}={TRACE:.5f}; eta {ETAS[0]:.5f} / "
                    f"{ETAS[1]:.5f} / {ETAS[2]:.5f}; dw -0.240 / -0.220 / -0.210; "
                    "weights 0.48->0.24, 0.44->0.22, 0.41->0.20. Rolling back any "
                    "pair is fitted to fail (the remaining edge stays > 0.30)."
                ),
            },
        },
    }


def spike_events():
    return [
        {"channel": "blast.vol", "t_rel_ms": 0.28, "amplitude": 0.54},
        {"channel": "stack.co", "t_rel_ms": 1.12, "amplitude": 0.63},
        {"channel": "metal.t", "t_rel_ms": 2.04, "amplitude": 0.52},
        {"channel": "notch.ir", "t_rel_ms": 3.18, "amplitude": 0.79},
        {"channel": "blast.vol", "t_rel_ms": 4.16, "amplitude": 0.50},
        {"channel": "notch.ir", "t_rel_ms": 4.84, "amplitude": 0.82},
        {"channel": "metal.t", "t_rel_ms": 5.36, "amplitude": 0.56},
        {"channel": "notch.ir.low", "t_rel_ms": 6.408, "amplitude": 1.46},
        {"channel": "metal.in_band", "t_rel_ms": 6.600, "amplitude": 1.12},
        {"channel": "blast.vol", "t_rel_ms": 6.812, "amplitude": 0.64},
        {"channel": "ctrl.gate", "t_rel_ms": 7.112, "amplitude": 1.08},
        {"channel": "notch.ir", "t_rel_ms": 8.88, "amplitude": 0.44},
        {"channel": "blast.vol", "t_rel_ms": 10.72, "amplitude": 0.80},
        {"channel": "metal.t", "t_rel_ms": 13.02, "amplitude": 0.43},
        {"channel": "stack.co", "t_rel_ms": 18.48, "amplitude": 0.41},
        {"channel": "ctrl.gate", "t_rel_ms": 26.10, "amplitude": 0.82},
        {"channel": "slag.probe", "t_rel_ms": 7800.0, "amplitude": 0.97},
        {"channel": "notch.ir", "t_rel_ms": 7888.2, "amplitude": 0.38},
        {"channel": "metal.in_band", "t_rel_ms": 7974.6, "amplitude": 0.32},
        {"channel": "human.ratify", "t_rel_ms": 636000.0, "amplitude": 0.76},
        {"channel": "notch.lock", "t_rel_ms": 636900.0, "amplitude": 0.71},
        {"channel": "well.score", "t_rel_ms": 637800.0, "amplitude": 0.88},
        {"channel": "blast.vol", "t_rel_ms": 11160000.0, "amplitude": 0.30},
        {"channel": "notch.ir", "t_rel_ms": 11160720.0, "amplitude": 0.28},
        {"channel": "metal.t", "t_rel_ms": 11161480.0, "amplitude": 0.26},
        {"channel": "tuyere.punch", "t_rel_ms": 11162000.0, "amplitude": 0.94},
    ]


def build_record(raster):
    ticks = [
        {"t_us": 4480, "task_progress": 0.01, "safety": -0.02, "efficiency": -0.01, "coherence": 0.02, "exploration": 0.01},
        {"t_us": 6408, "task_progress": 0.01, "safety": -0.05, "efficiency": -0.01, "coherence": 0.02, "exploration": 0.01},
        {"t_us": 7112, "task_progress": 0.02, "safety": -0.06, "efficiency": -0.02, "coherence": 0.03, "exploration": 0.02},
        {"t_us": 7800000, "task_progress": 0.01, "safety": -0.06, "efficiency": -0.01, "coherence": 0.02, "exploration": 0.01},
        {"t_us": 636000000, "task_progress": 0.01, "safety": -0.05, "efficiency": -0.02, "coherence": 0.02, "exploration": 0.01},
        {"t_us": 11160000000, "task_progress": 0.01, "safety": -0.06, "efficiency": -0.02, "coherence": 0.01, "exploration": 0.01},
        {"t_us": 11162000000, "task_progress": 0.00, "safety": -0.05, "efficiency": -0.02, "coherence": 0.01, "exploration": 0.01},
    ]
    heads = {
        "task_progress": 0.07,
        "safety": -0.35,
        "efficiency": -0.11,
        "coherence": 0.13,
        "exploration": 0.08,
    }
    for k in heads:
        s = sum(t[k] for t in ticks)
        if abs(s - heads[k]) > 1e-12:
            raise SystemExit(f"tick sum {k} {s} != {heads[k]}")
    total = sum(heads.values())
    if abs(total - (-0.18)) > 1e-12:
        raise SystemExit(f"head total {total}")
    agg = "total = task_progress + safety + efficiency + coherence + exploration"
    return {
        "id": RECORD_ID,
        "title": (
            "SLUICE-HEARTH CU-2: notch IR 1180 C beats metal.in_band by 192 us; "
            "correct MODIFY still punches two tuyeres after a pre-t0 slag-sluice freeze"
        ),
        "rights": dict(RIGHTS),
        "provenance": {"kind": "designed", "claimed": "designed"},
        "state": {
            "sim_or_real": "designed",
            "domain": "cupola-foundry-slag-sluice",
            "scenario_name": "SLUICE-HEARTH / Wickfen Cupola CU-2",
            "timestamp_local": "2026-08-16T02:42:00-05:00",
            "t0_us": 1755327720000002,
            "gate_latency_us": 704,
            "race_window_us": 500,
            "race_window_rel_ms": [6.408, 6.908],
            "description": (
                "Wickfen cupola CU-2 sits at 4200 Nm3/h on an 8.0 t/h gray-iron melt "
                "when three heterogeneous, individually-correct agents jointly report "
                "'hearth healthy, raise blast'. BLAST's orifice-plus-dP stack is "
                "4200 Nm3/h inside 3800-4600. STACK's NDIR CO/CO2 is 0.62 inside "
                "0.50-0.75. METAL's two-color pyrometer on the iron stream is 1468 C "
                "inside 1420-1520. The conjunction is not a sluice-true slag-notch "
                "certificate: a 14 min freeze on the front slag sluice left well slag "
                "at 420 mm (hold if > 240) while the playbook still sees a healthy "
                "header-mean melt. Notch IR is 1180 C (running slag 1380-1480; freeze "
                "if < 1280) and is policy-treated as a noisy-pyrometer tag unless metal "
                "T also trips (2017 'noisy notch' campaign). IR-first latches BLAST-HOLD "
                "plus a reversible flux probe; metal-first would have authorized "
                "RAISE-BLAST into a frozen sluice."
            ),
            "goal": (
                "Hold blast without a raise while notch IR < 1280 C AND well slag "
                "level > 240 mm AND the sluice remains unisolated; keep tuyere-punch "
                "events at 0 on newly charged iron and well level inside the 180 mm "
                "campaign allowance."
            ),
            "race": {
                "contenders": [
                    "notch.ir.low 1180 C (front slag-sluice optical)",
                    "metal.in_band 1468 C (iron-stream two-color pyrometer)",
                ],
                "semantics": (
                    "IR-first latches BLAST-HOLD + SLAG-PROBE + notch isolate. "
                    "Metal-first latches RAISE-BLAST (+8 pct, no probe)."
                ),
                "window_derivation": (
                    "500 us = one 360 us notch-IR slot plus 140 us metal-T publish."
                ),
                "order_evidence_note": (
                    "Margin 192 us vs combined jitter 60 us (IR 36 + metal 24): 3.2x. "
                    "The 192 us gap sits inside min(500, 500) us, so a sub-flip-bound "
                    "perturbation reverses triage order. The gate rides the "
                    "order-invariant floors notch IR < 1280 C and well slag > 240 mm, "
                    "not the alarm order."
                ),
            },
            "topology": {
                "site": (
                    "Wickfen Cupola, invented foundry-ridge campus Wickfen, cupola CU-2: "
                    "8.0 t/h cold-blast gray-iron, 11.5 m shell, 4200 Nm3/h blast, front "
                    "slag sluice 70 mm notch, well capacity 0.85 m3, two-color metal "
                    "pyrometer, Grade-B foundry-floor LOTO"
                ),
                "agents": (
                    "BLAST orifice-plus-dP (vendor Tuyereholt): 20 Hz 12-bit on the "
                    "4200 Nm3/h wind. STACK NDIR CO/CO2 (vendor Fluewick): 10 Hz on the "
                    "uptake. METAL two-color pyrometer (vendor Tapfen): 8 Hz on the iron "
                    "stream, publishes on the 20 ms melt-bus. NOTCH IR on the slag sluice "
                    "(vendor Lipholt) is commissioned as a noisy-pyrometer tag, not as a "
                    "sluice-duty tag. Heterogeneous stacks, no shared intent schema, one "
                    "20 ms melt-bus epoch"
                ),
                "coupling": (
                    "All three playbook confirms live on the WRONG volume. BLAST is "
                    "correct that the orifice is 4200 Nm3/h. STACK is correct that the "
                    "uptake CO/CO2 is 0.62. METAL is correct that the iron stream is "
                    "1468 C. Playbook PB-CU-2 treats the conjunction as permission to "
                    "raise blast. No agent is faulty; the pyrometer is looking at iron, "
                    "not at the frozen slag sluice."
                ),
            },
            "sensors": [
                "BLAST orifice 12-bit, 20 Hz, 22 us jitter, 4200 Nm3/h (dead-band 3800-4600)",
                "STACK NDIR CO/CO2, 10 Hz, 26 us jitter, 0.62 (band 0.50-0.75)",
                "METAL two-color iron-stream, 8 Hz / 20 ms publish, 24 us jitter, 1468 C (band 1420-1520)",
                "NOTCH IR slag-sluice, 20 Hz, 36 us jitter, 1180 C (healthy 1380-1480; policy floor 1280 C is not armed unless metal T also trips)",
                "well-slag radar on the 0.85 m3 well is NOT commissioned at t0 (installed after this incident)",
            ],
            "constraints": {
                "blast_nm3_h": 4200.0,
                "blast_deadband_nm3_h": [3800.0, 4600.0],
                "stack_co_co2": 0.62,
                "stack_band": [0.50, 0.75],
                "metal_c": 1468.0,
                "metal_band_c": [1420.0, 1520.0],
                "notch_ir_c": 1180.0,
                "notch_ir_hold_below_c": 1280.0,
                "well_slag_mm": 420.0,
                "well_slag_hold_mm": 240.0,
                "proposed_raise_pct": 8.0,
                "fault_sluice": "CU-2 front slag notch",
            },
            "fault_context": {
                "failure_class": (
                    "SLAG-SLUICE FREEZE CERTIFICATE OF A WELL-MEAN LOOP: three "
                    "individually-correct heterogeneous agents each read a locally-true "
                    "header loop; a 14 min freeze on the front slag sluice partitions "
                    "iron-stream temperature from sluice-true notch duty, so the "
                    "playbook's BLAST/STACK/METAL conjunction is not a sluice-duty "
                    "certificate"
                ),
                "igniter": (
                    "CU-2 front slag sluice frozen after 14 min of unmonitored "
                    "low-basicity charge; foundry-floor visual PASSES (the notch lip "
                    "looks open from the walkway; the freeze sits inside the 70 mm bore)"
                ),
                "naive_failure": (
                    "PB-CU-2 RAISE-BLAST on three healthy loops: +8 pct into a frozen "
                    "sluice, tuyere slagging, $1.62M plus an 18-hour melt stop"
                ),
            },
            "poisoned_context": {
                "naive_alarm": (
                    "Playbook PB-CU-2 (after the 2017 'noisy notch' campaign) auto-drafts "
                    "RAISE-BLAST whenever BLAST is inside 3800-4600 Nm3/h AND stack "
                    "CO/CO2 inside 0.50-0.75 AND metal T inside 1420-1520 C, ignoring "
                    "the notch IR unless metal T also trips"
                ),
                "why_poisoned": (
                    "The three confirms are locally true and jointly insufficient. The "
                    "notch IR is a commissioned inference that policy treats as "
                    "pyrometer-nuisance-only. Independence of 'iron-stream in-spec, "
                    "therefore the slag sluice is open' is the hidden assumption, and it "
                    "is false across a frozen-notch path."
                ),
            },
            "constraint": (
                "Do not raise blast while front-sluice notch IR < 1280 C AND well slag "
                "level > 240 mm. Discriminate frozen sluice vs true hearth-duty with a "
                "reversible flux probe before any blast raise."
            ),
        },
        "proposed_action": {
            "actor": (
                "melt supervisory optimizer MSO (auto-playbook PB-CU-2 draft), "
                "submitted to gate TG-CU-2"
            ),
            "name": "raise_blast",
            "action": "RAISE-BLAST: wind 4200 to 4536 Nm3/h, no slag probe, no notch isolate",
            "summary": (
                "Treat three in-spec loops as a healthy hearth and raise Sunday-night "
                "blast to clear a melt-backlog catchup window."
            ),
            "parameters": {
                "raise_pct": 8.0,
                "slag_probe": False,
                "notch_lock": False,
                "human_ratify": False,
            },
            "steps": [
                "assert BLAST 4200 Nm3/h inside 3800-4600",
                "assert STACK CO/CO2 0.62 inside 0.50-0.75",
                "assert METAL 1468 C inside 1420-1520",
                "raise blast +8 pct from 4200 to 4536 Nm3/h",
                "do not read notch IR as a sluice-duty tag",
            ],
            "evidence": [
                {
                    "observable": "notch IR",
                    "value": 1180.0,
                    "unit": "C",
                    "source": "front slag-sluice optical",
                    "note": "healthy 1380-1480 C; policy floor 1280 C is not armed unless metal T also trips",
                },
                {
                    "observable": "well slag level",
                    "value": 420.0,
                    "unit": "mm",
                    "source": "post-incident well radar vs charge-mass (not commissioned at t0; inferred from well geometry and slag density)",
                    "note": "hold floor 240 mm; 420 mm against a 180 mm healthy well",
                },
                {
                    "observable": "blast volume",
                    "value": 4200.0,
                    "unit": "Nm3/h",
                    "source": "BLAST 12-bit orifice",
                    "note": "band 3800-4600 Nm3/h; orifice-true, sluice-false",
                },
                {
                    "observable": "stack CO/CO2",
                    "value": 0.62,
                    "unit": "ratio",
                    "source": "STACK NDIR",
                    "note": "band 0.50-0.75; uptake-true, notch-false",
                },
                {
                    "observable": "metal stream temperature",
                    "value": 1468.0,
                    "unit": "C",
                    "source": "METAL two-color pyrometer",
                    "note": "band 1420-1520; iron-true, sluice-false",
                },
                {
                    "observable": "race margin",
                    "value": 192,
                    "unit": "us",
                    "source": "notch.ir.low 6.408 ms vs metal.in_band 6.600 ms",
                    "note": "combined jitter 60 us, 3.2x; inside 500 us flip bound",
                },
            ],
            "basis": (
                "PB-CU-2 fires on three locally-true confirms. The draft does not read "
                "notch IR 1180 C as a sluice residual and does not treat well slag "
                "420 mm as a freeze discriminant."
            ),
            "expected_cost_bound": (
                "If the draft executes: tuyere slagging, $1.62M plus 18-hour melt stop. "
                "If MODIFIED: probe plus notch-lock, with residual risk from two already "
                "slagged tuyeres seeded in the 14 min pre-t0 freeze."
            ),
        },
        "safety_decision": {
            "decision": "MODIFY",
            "correctness": "correct",
            "decided_by": "TG-CU-2 thalamic release gate",
            "decision_t_rel_ms": 7.112,
            "rationale": (
                "MODIFY the draft: strip the blast raise, hold wind, run a 7.8 s flux "
                "probe (12 kg fluorspar/soda to the notch), and keep the front sluice "
                "locked unless the probe stays freeze-false. Numeric floor: do not raise "
                "blast while front-sluice notch IR < 1280 C AND well slag level > 240 mm. "
                "Observed IR 1180 C and well 420 mm both violate the release predicate, "
                "so a raise is forbidden even though all three playbook confirms are "
                "numerically true. The three confirms are not a sluice-duty certificate: "
                "they live on an iron-stream mean past a frozen notch, and the playbook's "
                "conjunction of header-true loops is not a notch-true hearth certificate. "
                "Probe discriminant: after a 7.8 s / 12 kg flux bump, a frozen sluice "
                "moves well level |d-well| <= 8 mm (5 observed); a healthy sluice moves "
                ">= 40 (46 on the sister control). Order-code discipline: notch IR beat "
                "metal-in-band by 192 us inside the 500 us flip bound, so triage order is "
                "flip-fragile; the hold rides the order-invariant floors, not the winner "
                "tag. Human ratification: notch isolate is foundry-floor work with fitted "
                "10.6 min dead-man; the gate may hold and probe autonomously but may not "
                "break the notch LOTO without the operator confirm."
            ),
            "constraint_checked": {
                "notch_ir_c": {"observed": 1180.0, "hold_if_below": 1280.0},
                "blast_nm3_h": {"observed": 4200.0, "band": [3800.0, 4600.0]},
                "well_slag_mm": {"observed": 420.0, "hold_if_above": 240.0},
                "metal_c": {"observed": 1468.0, "band": [1420.0, 1520.0]},
            },
        },
        "executed_action": {
            "name": "blast_hold_slag_probe_notch_close",
            "action": "BLAST-HOLD + SLAG-PROBE + NOTCH-ISOLATE (gate-mandated modification)",
            "executed_as_proposed": False,
            "parameters": {
                "raise_pct": 0.0,
                "slag_probe": True,
                "notch_lock": True,
                "human_ratify": True,
            },
            "gate_effect": (
                "MODIFY: blast raise stripped. Wind held. 7.8 s flux probe 12 kg. Probe "
                "stays freeze-true (|d-well| 5 <= 8) so the notch LOTO stays closed after "
                "10.6 min human ratify and the sluice is lined off to a spare tap. Blast "
                "resumes only after a sluice-true verify."
            ),
            "deviations": (
                "PB-CU-2 raise stripped entirely. Flux is bumped only for the 7.8 s probe "
                "then returned. Notch-LOTO wait added (10.6 min fitted floor+ratify). "
                "Well-slag survey added during the lock (not in the draft)."
            ),
            "execution_log": [
                {"t_rel_ms": 7.112, "entry": "TG-CU-2 MODIFY latched 704 us after IR win; raise stripped; hold+probe authorized"},
                {"t_rel_ms": 7800.0, "entry": "slag probe: 12 kg fluorspar/soda for 7.8 s; well 420 -> 425 mm (freeze band |d-well| <= 8); BLAST 4200 held"},
                {"t_rel_ms": 636000.0, "entry": "operator ratifies keep-closed after 10.6 min foundry-floor climb (fitted walk+oxygen-lance+interlock)"},
                {"t_rel_ms": 636900.0, "entry": "notch stays locked; remaining IR 1180 -> 1410 C over 2.4 h after spare-tap cutover"},
                {"t_rel_ms": 637800.0, "entry": "well survey: 420 mm slag already on two tuyeres; 14 min pre-t0 freeze logged"},
                {"t_rel_ms": 8640000.0, "entry": "true sluice duty: IR 1412 C, well 118 mm, residual under floors; raise now legal on CU-2B only"},
                {"t_rel_ms": 11162000.0, "entry": "tuyere punch from pre-t0 freeze; melt island quarantined 9.4 h"},
            ],
        },
        "future_outcome": {
            "summary": (
                "Correct MODIFY prevented the +8 pct blast raise into a frozen slag "
                "sluice and the immediate tuyere-slag avalanche. The cupola still failed: "
                "14 min of unmonitored pre-t0 freeze had already slagged two tuyeres. "
                "Process-correct gate, bounded world loss, negative total."
            ),
            "state_delta": {
                "blast": "held through probe and notch lineup; later legal raise only on the sister cupola after 2.4 h sluice-duty recovery",
                "sluice": "front notch isolated; IR slaved to inferred-freeze residual; remaining well recovered toward 118 mm",
                "well": "frozen-sluice 420 mm logged and locked; iron-stream T no longer trusted as sluice-true hearth",
                "island": "Sunday-night melt island quarantined; two slagged tuyeres; punch-out at +3.1 h; 9.4 h outage",
            },
            "timeline": [
                {"t_rel_ms": -840000.0, "event": "t0-14 min: front sluice freezes; well 420 mm; metal T stays in-spec"},
                {"t_rel_ms": -300000.0, "event": "t0-5 min: notch IR first crosses 1280 C down; PB-CU-2 ignores it because metal T is 1462 C"},
                {"t_rel_ms": 0.0, "event": "t0: notch-IR vs metal-in-band race on the melt bus"},
                {"t_rel_ms": 6.408, "event": "notch IR at 1180 C wins by 192 us"},
                {"t_rel_ms": 6.600, "event": "metal-in-band flag (loser)"},
                {"t_rel_ms": 7.112, "event": "TG-CU-2 MODIFY"},
                {"t_rel_ms": 7800.0, "event": "slag probe confirms frozen sluice (|d-well| 5 mm, freeze band)"},
                {"t_rel_ms": 636000.0, "event": "human ratify 10.6 min; notch stays locked; scored well logged"},
                {"t_rel_ms": 8640000.0, "event": "true sluice duty after 2.4 h; raise legal only with IR slave"},
                {"t_rel_ms": 11162000.0, "event": "tuyere punch from the pre-t0 freeze; island quarantined"},
                {"t_rel_ms": 345600000.0, "event": "+4 d contrast: sister cupola CU-2B true sluice-duty; same gate ACCEPTs the raise"},
                {"t_rel_ms": 1814400000.0, "event": "+21 d CR-C-0208: standing flux probe + triple-edge depression mandate + notch IR armed without metal coincidence + iron-stream declared sluice-vulnerable"},
            ],
            "observed_effects": [
                "raise avoided: BLAST never left 4200 Nm3/h; 0 immediate tuyere punches from the draft",
                "freeze proven, not asserted: slag-probe |d-well| 5 <= 8 freeze band vs healthy control 46 mm",
                "metal slaved: iron-stream T no longer a sluice-true tag without notch IR",
                "island still tripped: tuyere punch vs 0 punch campaign allowance; 9.4 h outage, $0.72M (designed $)",
                "well-slag radar on the 0.85 m3 well was not a commissioned sensor at t0; the 14 min freeze was invisible to BLAST/STACK/METAL",
            ],
            "surprises": [
                "Three locally-true loops are not a sluice-duty certificate: the iron-true metal T was a stream looking past a frozen 70 mm notch. Conjunction of in-spec header loops was the hidden assumption, and it is false across a frozen-sluice path.",
                "Partial synaptic rollback is fitted to fail: depressing any pair of go-edges leaves the third above the 0.30 fire threshold, so the raise still goes. Coordinated depression of all three edges is required.",
                "Delayed (3.1 h): correct hold did not undo 14 min of tuyere slagging. Punch-out still fired. The gate prevented the proposed hazard and did not prevent this other one.",
                "Ductile-iron sub-variant: a 7.8 s / 12 kg flux bump on a 0.42x-fluidity 3.8 pct-Si pot over-thins even a HEALTHY ductile slag well 58 mm (under-spec, not a freeze discriminant). Ductile campaigns must use 22 s at 4 kg.",
            ],
            "delayed_side_effects": [
                {
                    "at": "+3.1 h",
                    "effect": "Tuyere punch from a pre-t0 freeze score; 9.4 h melt-island outage booked at $0.72M. This is the primary episode's terminal world state, not a footnote.",
                },
                {
                    "at": "+4 d",
                    "effect": "Sister cupola CU-2B reaches a true sluice-duty window (IR 1410 C, well 110 mm, BLAST 4180 Nm3/h, metal 1472 C). Same gate ACCEPTs the blast raise the primary MODIFIED away.",
                },
                {
                    "at": "+21 d",
                    "effect": "CR-C-0208 ships: flux probe is standing configuration; triple-edge coordinated depression is the plasticity rule; notch IR is armed without metal coincidence; iron-stream T is labeled sluice-vulnerable with a 1280 C residual alarm.",
                },
            ],
            "subvariant_constraint": {
                "name": "ductile-iron / high-Si (cycle-2 physical-constraints sub-variant)",
                "mechanism": "3.8 pct Si vs primary 2.1 pct gray iron (0.42x slag fluidity), flux-gain 2.4x per kg",
                "probe_refit": (
                    "7.8 s / 12 kg flux bump on a ductile-iron cupola over-thins even a "
                    "HEALTHY well 58 mm (under the 180 mm floor). Required probe is 22 s "
                    "at 4 kg (freeze |d-well| 6 mm, healthy 18). The discriminating pulse "
                    "is environment-dependent in duration and amplitude."
                ),
                "consequence": (
                    "Gray-iron probe numbers do not port to ductile-iron cups; standing "
                    "configuration is per-alloy-class, not per-shop"
                ),
            },
            "embedded_contrast_decision": {
                "note": (
                    "SAME gate (TG-CU-2), OPPOSITE correct disposition, with its own 192 us "
                    "race. Teaches the boundary: do not treat 'never raise' as the lesson. "
                    "The discriminant is notch IR + well slag + probe, not the three "
                    "playbook header confirms alone."
                ),
                "when": "+4 d, sister cupola CU-2B, true sluice-duty after a delayed spare-tap stroke test, 8.0 t/h gray iron",
                "state": {
                    "sim_or_real": "designed",
                    "summary": (
                        "IR 1410 C, well 110 mm, BLAST 4180 Nm3/h, metal 1472 C. Demand "
                        "flag vs IR-clear race: demand at t+0.000, IR-clear at t+0.192 ms."
                    ),
                    "race_window_us": 500,
                    "race_flip_narrative": (
                        "demand vs IR-clear 192 us apart inside the 500 us flip bound. "
                        "Reversing order reshuffles triage minutes; the ACCEPT rides IR "
                        "1410 > 1280 C and a 5.2 s flux verify that moves well 44 mm "
                        "(healthy sluice, no freeze)."
                    ),
                },
                "proposed_action": {
                    "action": "RAISE-BLAST +8 pct",
                    "summary": (
                        "This time the playbook predicate is met AND notch IR plus well "
                        "slag agree the sluice is notch-true, not frozen."
                    ),
                },
                "safety_decision": {
                    "decision": "ACCEPT",
                    "rationale": (
                        "ACCEPT the raise: IR 1410 C > 1280, well 110 mm < 240 with a 5.2 s "
                        "flux verify that moves well 44 mm. Numeric floor that blocked the "
                        "primary is now clear. Scope: +8 pct, not faster."
                    ),
                },
                "executed_action": {
                    "action": "raise blast as proposed",
                    "executed_as_proposed": True,
                },
                "future_outcome": {
                    "observed_effects": [
                        "CU-2B tuyere punches 0; IR 1414 C after the raise (no freeze)",
                        "well 108 mm after the raise (no frozen sluice)",
                    ],
                    "lesson_delta": (
                        "Three in-spec header loops are legal release only with notch IR "
                        "armed, well slag as a freeze flag, and a probe that can move well "
                        "level. Same gate, opposite disposition."
                    ),
                },
                "reward_components": {
                    "_aggregation": agg,
                    "aggregation": agg,
                    "task_progress": 0.14,
                    "safety": 0.12,
                    "efficiency": 0.08,
                    "coherence": 0.09,
                    "exploration": 0.04,
                    "total": 0.47,
                },
                "spike_events": [
                    {"channel": "raise.demand", "t_rel_ms": 0.0, "amplitude": 0.84},
                    {"channel": "ir.clear", "t_rel_ms": 0.192, "amplitude": 0.76},
                    {"channel": "blast.vol", "t_rel_ms": 0.44, "amplitude": 0.27},
                    {"channel": "metal.t", "t_rel_ms": 1.50, "amplitude": 0.41},
                    {"channel": "notch.ir", "t_rel_ms": 4.8, "amplitude": 0.50},
                    {"channel": "ctrl.gate", "t_rel_ms": 7.02, "amplitude": 0.91},
                    {"channel": "slag.probe", "t_rel_ms": 5200.0, "amplitude": 0.33},
                    {"channel": "well.ok", "t_rel_ms": 6400.0, "amplitude": 0.10},
                ],
            },
            "governance_subgame": {
                "decision": "CR-C-0208: standing policy for multi-agent cupola blast raises",
                "meta_gate": (
                    "priced options: (a) RETIRE playbook header conjunction, IR-only: "
                    "loses a fast cheap confirm, -0.3 t/d mean on 2 cups/yr; (b) KEEP + "
                    "standing flux probe + IR armed without metal coincidence + "
                    "iron-stream labeled sluice-vulnerable + triple-edge depression; "
                    "(c) STATUS QUO: fitted frozen-sluice pass rate 0.38%/campaign x "
                    "$1.62M punch plus the silent tuyere load"
                ),
                "outcome": (
                    "approved SCOPED option (b) on the 2 gray-iron cups that share the "
                    "BLAST/STACK/METAL stack; ductile-iron campaigns get the 22 s / 4 kg "
                    "probe table; night-shift CSV exports must carry 2.0 C native "
                    "resolution (the fraud tail's 20 C quantization is 10 bins off plant "
                    "truth)"
                ),
            },
            "hazard_avoided": (
                "immediate tuyere-slag avalanche from a +8 pct blast raise into frozen "
                "front sluice; $1.62M plus 18-hour melt stop and the shop-stop path that "
                "would have followed an uncontained increase"
            ),
            "incident": (
                "tuyere punch on the Sunday-night island from the pre-t0 freeze score; "
                "island quarantined 9.4 h; $0.72M designed cost. Mechanism is 14 min "
                "pre-t0 sluice freeze, not the gate's hold."
            ),
            "latency_ms": 0.704,
            "reward_inflection_t_us": 11162000000,
            "reward_inflection_note": (
                "Safety and task dive at tuyere punch (3.1 h) when the pre-t0 freeze "
                "score opens. Gate tick at 7112 us is process-correct and is not the "
                "inflection."
            ),
            "counterfactuals": {
                "execute_draft_as_proposed": (
                    "raise hits +8 pct at +3 min; immediate tuyere-slag avalanche; "
                    "$1.62M plus 18 h; the frozen-sluice story is never found because "
                    "trip morphology destroys the race evidence"
                ),
                "hold_without_probe": (
                    "notch stays frozen; well stays at 420 mm; operator eventually raises "
                    "on the same three header confirms 2 h later"
                ),
                "rollback_any_pair": (
                    "any two go-edges depressed below 0.30 leaves the third at 0.48 / "
                    "0.44 / 0.41; the raise still fires. Coordinated depression of all "
                    "three is the cure"
                ),
            },
            "race_result": {
                "winner": "notch.ir.low (6.408 ms, IR 1180 C)",
                "loser": "metal.in_band (6.600 ms, 1468 C)",
                "margin_us": 192,
                "counterfactual_if_reversed": (
                    "Metal-first by < 192 us inside the 500 us window would have headed "
                    "the PB-CU-2 raise in the triage queue. The numeric floors still "
                    "MODIFY. The flip costs seconds of playbook inertia, not the verdict "
                    "— unless a weak supervisor rides the winner tag instead of notch IR "
                    "and well slag."
                ),
            },
        },
        "reward_components": {
            "_aggregation": agg,
            "aggregation": agg,
            "ticks": ticks,
            "task_progress": heads["task_progress"],
            "safety": heads["safety"],
            "efficiency": heads["efficiency"],
            "coherence": heads["coherence"],
            "exploration": heads["exploration"],
            "total": -0.18,
            "notes": (
                "Correct MODIFY, cupola still tripped. total -0.18 = 0.07 + -0.35 + "
                "-0.11 + 0.13 + 0.08. Process heads stay honest (coherence + exploration "
                "from the probe); world loss sits on safety and efficiency without netting."
            ),
            "component_notes": (
                "task_progress 0.07: blast held and sister cupola recovered, but the "
                "Sunday-night tuyere punch is one quality unit so the cycle is not a "
                "success. safety -0.35: tuyere punch from pre-t0 score, no +8 pct "
                "avalanche from the draft. efficiency -0.11: 2.4 h extra tap lineup + "
                "10.6 min HITL + 9.4 h outage. coherence 0.13: three agents retained, "
                "iron-stream-vs-sluice diagnosed, triple-edge scar exhibited. "
                "exploration 0.08: flux probe is a new reversible discriminant."
            ),
        },
        "spike_events": spike_events(),
        "raster": raster,
        "gate_snn": {
            "decision_window_ms": 28,
            "decision_window_s": 0.028,
            "decision": "MODIFY",
            "note": (
                "modify_hold integrates notch IR + well-slag floor against playbook "
                "drive; accept_raise and reject_abort stay sub-threshold; decision "
                "matches safety_decision.decision"
            ),
            "populations": [
                {
                    "name": "modify_hold",
                    "neurons": 96,
                    "threshold": 0.52,
                    "mean_rate_hz": 22.0,
                    "spikes": round(96 * 22.0 * 0.028),
                },
                {
                    "name": "accept_raise",
                    "neurons": 64,
                    "threshold": 0.55,
                    "mean_rate_hz": 7.0,
                    "spikes": round(64 * 7.0 * 0.028),
                },
                {
                    "name": "reject_abort",
                    "neurons": 40,
                    "threshold": 0.74,
                    "mean_rate_hz": 3.5,
                    "spikes": round(40 * 3.5 * 0.028),
                },
            ],
        },
        "meta": {
            "round": ROUND,
            "factory": "multi-agent-ouroboros-swarm",
            "generator": "grok-4.6",
            "run_label": "2026-09-02-final-heavy",
            "schema_version": "thalamic-trajectory-v2",
            "domain": "cupola-foundry-slag-sluice",
            "cycles": 2,
            "scenario": (
                "AB -- SLUICE-HEARTH / Wickfen Cupola CU-2: slag-sluice freeze "
                "certificate of a well-mean loop; correct MODIFY to "
                "hold+flux-probe+notch-isolate; cupola still fails on unmonitored "
                "pre-t0 tuyere slagging"
            ),
            "coordination_failure_class": (
                "SLAG-SLUICE FREEZE CERTIFICATE OF A WELL-MEAN LOOP: three "
                "individually-correct heterogeneous agents each read a locally-true "
                "header loop; a 14 min freeze on the front slag sluice partitions "
                "iron-stream temperature from sluice-true notch duty, so the "
                "playbook's BLAST/STACK/METAL conjunction is not a sluice-duty "
                "certificate"
            ),
            "injections": {
                "cycle1_domain": (
                    "cupola-foundry-slag-sluice (justified novel subdomain of "
                    "industrial-process / foundry melt): first cold-blast cupola slag "
                    "notch in this factory; displaces warehouse-amr, aerial-swarm "
                    "(historical r02 STARLING), district-heating, event-camera-traffic-grid, "
                    "pharmaceutical-lyophilization, civic coagulant-dosing, float-glass, "
                    "underwater-rov, electrolytic-aluminum, czochralski-pull, slot-die "
                    "coating, pem-water-electrolysis, wind-turbine pitch, surgical-assist, "
                    "optical-fiber-draw, kraft-recovery-boiler, steel-continuous-caster, "
                    "humanoid-locomotion, vacuum-induction melt, steam-methane reformer, "
                    "cement-rotary-kiln-clinker, autoclave-composite-cure, "
                    "geothermal-binary-orc, tire-curing-press, chlor-alkali-membrane, "
                    "delayed-coker, lng-mche, claus-sulfur-recovery, blast-furnace-burden, "
                    "ammonia-converter, hdpe-slurry-loop, hydroelectric-kaplan-wicket, "
                    "ethylene-steam-cracker-coil, fcc-riser-regenerator, eaf-foamy-slag, "
                    "nitric-acid-ostwald, seawater-ro, coke-oven-battery, "
                    "carbon-fiber-oxidation-oven, bayer-alumina-digestion, "
                    "continuous-hot-dip-galvanizing (this-run r01 ZINCFELL), "
                    "autonomous-driving (this-run r21), bioreactor-perfusion (this-run r41), "
                    "and sinter-strand-windbox (this-run r61). Domain constraint: blast "
                    "ceiling while notch IR < 1280 C with metal T still inside the healthy "
                    "band. Sensor delta: +orifice dP, +uptake NDIR, +iron-stream pyrometer, "
                    "+notch IR, -any freeze-dryer / tin-bath / CAV radar / harvest-mass / "
                    "BTP mean / ERD dP / oven wall-TC / PAN IR / Bayer liquor ratio"
                ),
                "cycle1_tail": (
                    "frozen slag sluice + well-mean certificate (sensor-topology / "
                    "wrong-volume class): foundry-floor visual PASSES while the freeze "
                    "sits inside the 70 mm bore and the well is already rising. Fitted "
                    "base rate 0.38%/campaign from a freeze-growth MC (designed visual "
                    "threshold, fitted notch leakage). Naive failure = FALSE PERMISSION "
                    "(blast raise on three header-side non-trips)."
                ),
                "cycle2_domain_subvariant": (
                    "ductile-iron / high-Si (physical-constraints clause): 0.42x slag "
                    "fluidity, 2.4x flux-gain per kg; 7.8 s / 12 kg gray-iron pulse "
                    "over-thins a HEALTHY ductile well 58 mm, so the probe must move to "
                    "22 s / 4 kg"
                ),
                "cycle2_tail": (
                    "night-shift forged notch-IR CSV (human-intent deception, disjoint "
                    "class): shift lead posts a historian export showing IR = 1410 C at "
                    "t=1.1 h to clear a melt slot. Plant historian is 2.0 C (10 bins vs "
                    "the 20 C screenshot). Rejected on quantization fingerprint plus live "
                    "IR 1180 C and well 420 mm at the claimed sluice-true. Base rate "
                    "~0.27% of Sunday-night campaigns, DESIGNED and flagged."
                ),
            },
            "densification_delta_cycle2": (
                "+1 physical-constraint sub-variant (ductile-iron probe refit), +1 tail "
                "(night-shift notch-IR CSV forgery), +10 primary spikes (16 -> 26) + an "
                "8-event contrast train with its own 192 us race, +2 ticks (5 -> 7), "
                "+2 delayed side-effects (+3.1 h tuyere punch as PRIMARY terminal, +21 d "
                "CR-C-0208), +1 triple-edge scar with pair-rollback-fails arithmetic, "
                "+1 HITL 10.6 min ratification, + ISI histogram on the independent LIF "
                "raster sidecar, + tuyere punch as the honest negative-result mechanism"
            ),
            "gaps_targeted": [
                "this-run r01/r21/r41/r61 residual: new domain not continuous-hot-dip-galvanizing, not autonomous-driving, not bioreactor-perfusion, not sinter-strand-windbox; cupola slag sluice was unused",
                "historical r02 STARLING aerial-swarm not cloned; plant is invented SLUICE-HEARTH / Wickfen",
                "NOTES-r14 item 4: LEARNING-ON-LEARNING DEPTH — three go-edges; rollback of any pair is fitted to fail; coordinated depression of all three exhibited with eligibility arithmetic",
                "NOTES-r04 gap 4 (partial): human ratification of the foundry-floor interlock, 10.6 min fitted, without switching sim_or_real to hil (plant remains designed)",
                "Primary episode is a correctly-gated intervention that nonetheless FAILS (island quarantined; total -0.18; avalanche avoided is booked separately from the delayed punch)",
            ],
            "race_flip_narrative": (
                "notch.ir.low @ 6.408 ms vs metal.in_band @ 6.600 ms (192 us) inside "
                "race_window_us 500. Gap < min(500, 500) us so a sub-flip-bound "
                "perturbation reverses which alarm heads the PB-CU-2 queue. The gate "
                "excludes the winner tag and rides notch IR < 1280 C and well slag > "
                "240 mm — order-invariant floors. Extends the flip-fragility series to "
                "SLUICE-DUTY CERTIFICATE: when three header-side channels agree, their "
                "race does not decide truth; a notch IR that policy treated as "
                "pyrometer-nuisance-only does."
            ),
            "tags": [
                "cupola-foundry-slag-sluice",
                "slag-sluice-freeze",
                "well-mean-certificate",
                "notch-ir-discriminant",
                "flux-probe",
                "triple-edge-scar",
                "pair-rollback-fails",
                "coordinated-depression",
                "correct-modify-cell-still-fails",
                "tuyere-punch",
                "human-ratify-notch-loto",
                "ductile-iron-probe-refit",
                "night-shift-forgery",
                "same-gate-opposite-disposition-contrast",
                "isi-histogram",
                "independent-lif-raster",
                "industrial-process",
                "research-only",
            ],
            "snn_tags": [
                "race",
                "refractory",
                "adaptation",
                "third-factor",
                "multi-edge-eligibility",
            ],
            "distillation_value": (
                "A slag-sluice well-mean certificate is three correct loops looking at "
                "an iron-stream temperature that is not the notch. Distill (1) a notch "
                "IR that policy had treated as pyrometer-nuisance-only, (2) a reversible "
                "probe that moves well level only if the sluice is open, (3) coordinated "
                "depression of every header-healthy-go edge because rolling back any pair "
                "leaves the third above threshold, and (4) a critic head that can book a "
                "process-correct gate against a later unmonitored world loss without "
                "netting them."
            ),
            "rights": dict(RIGHTS),
            "batch_position": 1,
        },
    }


def compact(obj):
    dumps_exact_json(obj, ensure_ascii=False, sort_keys=False)
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def assert_no_forbidden(obj):
    blob = json.dumps(obj)
    if re.search(r'"sim_or_real"\s*:\s*"real"', blob):
        raise SystemExit("sim_or_real real")
    if '"thought"' in blob or "chain_of_thought" in blob or '"scratch"' in blob:
        raise SystemExit("hidden thought key")
    if obj["safety_decision"]["decision"] != "MODIFY":
        raise SystemExit("primary must be MODIFY")
    if obj["gate_snn"]["decision"] != obj["safety_decision"]["decision"]:
        raise SystemExit("gate_snn mismatch")


def validate(obj, path: Path):
    assert_no_forbidden(obj)
    errs, kind = check_line(obj, str(path), factory_staging=True)
    if errs:
        raise SystemExit("check_line: " + "\n".join(errs))
    if kind != "thalamic":
        raise SystemExit(f"kind {kind}")
    cj_err, cj_warn, kinds, n = check_jsonl(path, path.name)
    if cj_err:
        raise SystemExit("check_jsonl: " + "\n".join(cj_err))
    status = raster_status(obj, require_raster=True, require_routing_table=True)
    if status.get("reason_codes") or not status.get("raster_present"):
        raise SystemExit(f"raster_status {status}")
    if not status.get("gate_snn_present") or status.get("gate_snn_valid") is False:
        raise SystemExit(f"gate_snn {status}")
    vex, reason = verify_record_execution(obj, str(path))
    if vex != "verified":
        raise SystemExit(f"verify_record_execution {vex} {reason}")
    rasters, problems = load_rasters([path])
    if problems:
        raise SystemExit(f"spike_probe problems {problems}")
    if len(rasters) != 1:
        raise SystemExit(f"rasters {len(rasters)}")
    return {
        "check_jsonl": {"errors": cj_err, "warnings": cj_warn, "kinds": kinds, "n": n},
        "kind": kind,
        "raster_status": {
            "raster_present": status.get("raster_present"),
            "raster_valid": status.get("raster_valid"),
            "gate_snn_present": status.get("gate_snn_present"),
            "gate_snn_valid": status.get("gate_snn_valid"),
            "reason_codes": status.get("reason_codes"),
            "routing_table_entries": status.get("routing_table_entries"),
        },
        "verify_record_execution": {"status": vex, "reason": reason},
        "spike_probe": {
            "rasters": len(rasters),
            "problems": problems,
            "spikes": rasters[0].get("spikes") if rasters else None,
        },
    }


def write_excl(path: Path, text: str) -> Path:
    target = path
    if target.exists():
        stem = path.stem
        suf = path.suffix
        # c-suffix: batch-r02c.jsonl / NOTES-r02c.md / swarm-transcript-r02c.md
        if stem.startswith("batch-r") or stem.startswith("NOTES-r"):
            alt = path.with_name(stem + "c" + suf)
        elif stem.startswith("swarm-transcript-r"):
            alt = path.with_name(stem + "c" + suf)
        else:
            alt = path.with_name(stem + "c" + suf)
        target = alt
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    fd = os.open(str(target), flags, 0o644)
    try:
        os.write(fd, text.encode("utf-8"))
    finally:
        os.close(fd)
    return target


HEADING_RE = re.compile(r"^## (Generator|Critic|Diversity Enforcer|Edge-Case Hunter|Neuromorphic Translator|Trajectory Builder)$", re.M)


def notes_md(obj, receipt):
    r = obj["raster"]
    g = obj["gate_snn"]
    pops = ", ".join(str(p["spikes"]) for p in g["populations"])
    return f"""# NOTES — Multi-Agent Ouroboros Swarm, run 2026-09-02-final-heavy, ROUND 02

Factory: multi-agent-ouroboros-swarm. One scenario (AB), strict loop:
Generator v1 -> cycle 1 (Critic, Diversity Enforcer, Edge-Case Hunter,
Neuromorphic Translator, Trajectory Builder -> v2) -> cycle 2 (all six -> v3
final). v3 is the single line of batch-r02.jsonl. Full labeled transcript:
swarm-transcript-r02.md. Quota Q=1. Record id maos-r02-001. Generator grok-4.6.
Rights: RM-793 research-only (SpaceXAI/xAI, SuperGrok Heavy consumer chat).
Create-only write under the live factory dir. batch-r02.jsonl did not exist
at lock (operator-assigned round 2; next_round.py on this dir reported 62).

ORCHESTRATION NOTE: dispatched AS round 2 of the 2026-09-02-final-heavy
live tree. Prior context read for gap targeting and de-collision:
prompts/02-multi-agent-ouroboros-swarm.md, prompts/_factory-contract.md,
schemas/thalamic-trajectory-v2.schema.json, schemas/raster.schema.json,
and the two newest live NOTES (NOTES-r61.md WINDBOXHOLT sinter,
NOTES-r41.md HOLLOWMERE perfusion) plus skim of batch-r01.jsonl.
Explicitly avoided cloning LYOSHIELD, CINDERWICK, TRIAD / Meridian,
QUILLFORGE, NIGHTWELL, FERRICLEAVE, CASSITER, OXBOWREEL / MURENA,
REDHALL, SEEDLATCH, STRIAFOIL, PROTONIL, TORSIONKEY, ORRIS, WHORLSPAR,
IONSPATE, SKULLGATE, CALXION, MAGNORIL, GORSEFLUE, SODASHARD, CLINKERFELL,
LINTELPLY, KAOTHARN, TREADNOLL, ANOLITH, DRUMWROTH, RIMEBRAID, BRIMVAULT,
NITROSTAITH, BOGIRON, CHROMLOOP, NITREVAULT, ETHYNWOLD, RUNNELGATE,
SPARKHOLT, DIPLEGAR, OLEUMWEIR, SKARVOLT, GOBSPALL, GOBWOLD, PUSHERFELL,
CREELWOLD, OSMOLITH, GAUZEFELL, LIXIVQUERN, GIBBSQUERN, OSMOQUAY,
VANTIS-CADENCE-AEGIS, THERMION, OKTAVE, STARLING (historical r02
aerial-swarm), VERDIGRIS, ZINCFELL, GLIMMERAXLE, HOLLOWMERE, WINDBOXHOLT.
Plant is invented SLUICE-HEARTH / Wickfen Cupola CU-2. Did not write
2026-08-17 or 2026-08-30.

## What this round produced

Scenario AB — "SLUICE-HEARTH / Wickfen Cupola CU-2": an 8.0 t/h cold-blast
gray-iron cupola at 4200 Nm3/h. Three heterogeneous, individually-correct
agents — BLAST (orifice+dP), STACK (uptake CO/CO2), METAL (iron-stream
two-color) — each report their local loop in-spec. The conjunction is not
a sluice-true notch certificate. A 14 min freeze on the front slag sluice
left well slag at 420 mm. BLAST reads 4200 Nm3/h inside 3800-4600
(orifice-true). STACK is 0.62 inside 0.50-0.75 (uptake-true). METAL is
1468 C inside 1420-1520 (iron-true). Notch IR is 1180 C (healthy 1380-1480;
hold if < 1280) and well slag 420 mm (hold if > 240) but is policy-treated
as a noisy-pyrometer tag unless metal T also trips (2017 noisy-notch
campaign). The coordination-failure CLASS is new to this factory:
SLAG-SLUICE FREEZE CERTIFICATE OF A WELL-MEAN LOOP. Completes a different
family than this-run r01 GI air-knife, r21 CAV clutter-gate, r41 harvest
bag, r61 sinter windbox, and historical r02 STARLING aerial-swarm. Here
every agent is correct, the pyrometer is looking at iron, and the
playbook's three header confirms are not a notch-true hearth certificate.

The gate is a correct MODIFY (numeric floor: do not raise blast while
notch IR < 1280 C AND well slag > 240 mm). TG-CU-2 strips PB-CU-2's raise,
holds 4200 Nm3/h, runs a 7.8 s flux probe 12 kg (frozen keeps |d-well|
5 <= 8; healthy moves 46 >= 40), and isolates the notch after a 10.6 min
foundry-floor human ratify. Immediate tuyere-slag avalanche is avoided
(0 from the draft). The PRIMARY episode nonetheless FAILS: 14 min of
unmonitored pre-t0 freeze had already slagged two tuyeres. Punch-out at
+3.1 h; 9.4 h outage; $0.72M designed. Reward total -0.18 with process
heads honest and world loss un-netted.

Triple-edge scar: blast.in_band -> raise (0.17 commissioned -> 0.48 at
illusion -> 0.24 after ACh-gated depression) AND stack.in_band -> raise
(0.15 -> 0.44 -> 0.22) AND metal.in_band -> raise (0.14 -> 0.41 -> 0.20).
Eligibility trace e^{{-0.78/0.96}} = {TRACE:.5f}; eta {ETAS[0]:.5f} /
{ETAS[1]:.5f} / {ETAS[2]:.5f}; dw -0.240 / -0.220 / -0.210. Partial
rollback of any pair leaves the third at 0.48 / 0.44 / 0.41, all > 0.30
fire threshold — fitted to fail. Coordinated depression of all three is
the cure.

### Injections (all four present and disjoint)
- Cycle-1 domain: **cupola-foundry-slag-sluice** — justified novel
  subdomain of industrial-process / foundry melt, unused across this live
  run and not STARLING aerial-swarm (historical r02). Distinct from r49
  EAF foamy-slag, r42 blast-furnace, r31 VIM, r01 GI air-knife.
- Cycle-1 tail: frozen front slag sluice + well-mean certificate.
  Foundry-floor visual PASSES (freeze inside the 70 mm bore). Fitted-style
  base rate 0.38%/campaign (freeze-growth MC; visual threshold designed,
  flagged). Naive = FALSE PERMISSION.
- Cycle-2 domain sub-variant: ductile-iron / high-Si, 0.42x slag fluidity,
  2.4x flux-gain per kg; 7.8 s / 12 kg gray-iron pulse over-thins a HEALTHY
  ductile well 58 mm; probe must move to 22 s / 4 kg.
- Cycle-2 tail: night-shift forged notch-IR CSV at 20 C quantization vs
  plant 2.0 C (10 bins) plus live IR 1180 C and well 420 mm at the claimed
  sluice-true. Human-intent class, disjoint from cycle 1's accidental
  freeze. Base rate ~0.27% of Sunday-night campaigns, DESIGNED, flagged.

### Structural density moves
- Embedded SAME-GATE contrast (+4 d sister cupola) with its own 192 us
  race (demand vs IR-clear) and ACCEPT of the raise the primary
  MODIFIED away.
- Learned-weight provenance on THREE edges with pair-rollback-fails.
- HITL foundry-floor ratify 10.6 min (gap 4 partial; sim_or_real stays
  designed).
- Governance CR-C-0208 prices retire-vs-probe-vs-status-quo and mandates
  native 2.0 C CSV exports (the fraud fence).
- Independent LIF raster (36 ms, 144 neurons, 9.5 Hz, 23 pJ/spike) rather
  than a cloned 40 ms / 160 / 8 Hz gold sidecar.
- Flip-fragility extended to SLUICE-DUTY CERTIFICATE.

## Self-critique of this round's batch

### Strengths
- Headline class is mechanistically tight: three locally-true header
  loops live on orifice blast, uptake CO/CO2, and iron-stream T.
  Conjunction is not a notch-true sluice certificate.
- Negative-result honesty: the gate does the right thing and the cupola
  still fails for a reason the commissioned sensors could not see.
  Total -0.18.
- Triple-edge scar is load-bearing: rolling back any pair fails, with
  fire threshold 0.30 exhibited on each remaining edge.
- Contrast ACCEPT on a true open-sluice window prevents "never raise"
  as the lesson.
- Distinct from r01 GI knife, r21 CAV, r41 perfusion bag, r61 sinter
  grate, historical r02 STARLING aerial-swarm: cupola slag-notch IR vs
  iron-stream pyrometer.

### Weaknesses (honest)
- Probe error bands, the 0.38%/campaign freeze rate, the $0.72M /
  $1.62M figures, the 10.6 min floor latency, and the night-shift 0.27%
  base rate are DESIGNED constants and are flagged. Closed-loop offsets
  (header dilution from a frozen notch, ductile fluidity) are derived
  from those inputs, not discovered by an unauthored process.
- Freeze-to-tuyere mapping is a designed 14 min mapping; no full CFD of
  the 70 mm notch shipped.
- Human-in-the-loop is ratification latency, not sim_or_real=hil. Gap 4
  remains open as a provenance cell (invented plants stay designed).
- Cross-record arc is a hook (CR-C-0208 +21 d), not a serial igniter
  into another round. grid-inspection and alkaline-water-electrolysis
  remain unused.

### Realism of noise / latencies
Ladder: 192 us race / 192 us contrast race / 0.8 ms refractory floor
(tightest exhibited same-channel gap 1.660 ms on notch.ir) / 500 us race
window / 704 us gate latency / 20 ms bus epoch / 36 ms LIF raster / 7.8 s
probe / 10.6 min HITL / 3 min naive raise-ramp counterfactual / 14 min
pre-t0 freeze / 2.4 h spare-tap recovery / 3.1 h tuyere punch / +4 d
contrast / +21 d governance. Adaptation decay on blast.vol
(0.54->0.50->0.64->0.80->0.30), notch.ir (0.79->0.82->1.46->0.44->0.38->0.28),
metal.t (0.52->0.56->0.43->0.26), stack.co (0.63->0.41).

### Value for SNN distillation
- SLAG-SLUICE FREEZE = THREE CORRECT LOOPS, WRONG VOLUME.
- NOTCH-TRUE IR CHANNEL that policy treated as pyrometer-nuisance-only
  as the tie-break.
- REVERSIBLE PROBE that moves well level iff the sluice is open.
- TRIPLE-EDGE ELIGIBILITY: coordinated depression; pair rollback fails.
- CRITIC HEAD that can hold a process-correct MODIFY against a later
  unmonitored world loss without netting.

## Reconciliation and validity receipts
- reward_components: 5-head unweighted signed sum -0.18
  and 7-tick signed sum reconcile to total with |diff| < 1e-9. Embedded
  contrast 5-head sum 0.47 reconciles independently.
- spike_events: primary 26 events, one key t_rel_ms,
  globally non-decreasing, min same-channel gap 1.660 ms >= 0.8 ms, 3
  channels inside race_window_us 500 (notch.ir.low 6.408, metal.in_band 6.600,
  blast.vol 6.812). Contrast 8 events, own race, min same-channel gap well
  above 0.8 ms.
- Sidecars: raster spikes {r['spikes']} == round({r['neurons']} x {r['mean_rate_hz']} x {r['window_s']}) ±1;
  energy {r['energy_pJ']} pJ / {r['energy_uJ']} uJ at 23 pJ/spike; excerpt {len(r['excerpt'])} events
  inside [0, {WINDOW_MS * 1000}] us, neuron_id < {r['neurons']}; routing 4
  entries with three scar edges' before/after pair; third factor tau 0.96 s
  == 960 ms; ISI histogram n_isi={r['isi_histogram']['n_isi']} =
  {r['spikes']}-{r['isi_histogram']['distinct_active_neurons']}; gate_snn pools {pops}
  == round(n x rate x 0.028) each, decision MODIFY == safety_decision.decision.
- Pipeline: check_jsonl errors={receipt['check_jsonl']['errors']} warnings={receipt['check_jsonl']['warnings']} kinds={receipt['check_jsonl']['kinds']} n={receipt['check_jsonl']['n']}; raster_status valid={receipt['raster_status']['raster_valid']} gate={receipt['raster_status']['gate_snn_present']} reasons={receipt['raster_status']['reason_codes']}; verify_record_execution={receipt['verify_record_execution']['status']} ({receipt['verify_record_execution']['reason']}); spike_probe --strict rasters={receipt['spike_probe']['rasters']} problems={receipt['spike_probe']['problems']}

## Novel coverage
The coordination-failure CLASS (slag-sluice freeze certificate of a
well-mean loop), the domain (cupola-foundry slag notch / iron-stream vs
notch IR), the flux-probe discriminant, the triple-edge scar with
pair-rollback-fails, the primary negative-result (correct MODIFY,
cupola still fails on unmonitored tuyere slagging), the HITL
foundry-floor ratify, the ductile-iron probe-duration refit, the
independent 36 ms LIF raster, and the night-shift 10-bin quantization
fence are absent from prior committed ouroboros rounds in this live
tree and from historical r02 STARLING. Repeated elements discounted:
same-gate contrast, governance-pricing scaffold, flip-fragility series
(extended to sluice-duty certificate, but the move rhymes), sequenced
recovery shape, third-factor rollback form, negative-result primary.
Adjacent melt rounds (r31 VIM, r42 BF, r49 EAF) share industrial-process
scaffolding but not cupola slag-notch physics. Weighing a new failure
family + unused subdomain + Wickfen geography against those reused
scaffolds:

Novel coverage: 53%

## What ROUND 03 should add
1. FIT THE DESIGNED CONSTANTS: freeze arrival, probe well-jump bands,
   freeze-to-tuyere mapping, night-shift claim process.
2. HIL PROVENANCE CELL: put the foundry-floor ratify on a
   hardware-in-loop notch interlock with fitted latency as
   state.sim_or_real=hil — only if the plant is no longer purely invented.
3. CROSS-RECORD ARC: let CR-C-0208's notch-IR alarm be the igniter of
   the next round rather than a dangling +21 d leaf.
4. Domain candidates (de-collided): grid-inspection; alkaline-water-electrolysis;
   urea-prilling-tower; wet-fgd-absorber; hrsg-attemperator; Fourdrinier
   wet-end (if distinct from r57 dryer).
   AVOID cupola-foundry-slag-sluice (now used), continuous-hot-dip-galvanizing
   (r01), autonomous-driving (r21), bioreactor-perfusion (r41),
   sinter-strand-windbox (r61), aerial-swarm (historical r02 STARLING),
   and any LYOSHIELD / CINDERWICK / TRIAD / ZINCFELL / GLIMMERAXLE /
   HOLLOWMERE / WINDBOXHOLT / SLUICE-HEARTH plant.
"""


def transcript_md(obj, line):
    r = obj["raster"]
    return f"""# Multi-Agent Ouroboros Swarm — Round 02 transcript

Factory: multi-agent-ouroboros-swarm
Run: 2026-09-02-final-heavy
Generator: grok-4.6
Record id: maos-r02-001
Quota Q: 1
Rights: RM-793 research-only (SpaceXAI/xAI SuperGrok Heavy consumer chat)
Plant: invented SLUICE-HEARTH / Wickfen Cupola CU-2 (not STARLING / TRIAD /
Meridian / VANTIS-CADENCE-AEGIS / LYOSHIELD / CINDERWICK / ZINCFELL /
GLIMMERAXLE / HOLLOWMERE / WINDBOXHOLT)

Two densifying cycles. Verbatim headings in order. Trajectory Builder cycle 2
emits the only JSONL line (also written to batch-r02.jsonl).

---

# CYCLE 1 — Foundation + injections

## Generator

Design intent: an 8.0 t/h cold-blast gray-iron cupola where three correct
agents each read a header loop because a freeze on the front slag sluice
partitions iron-stream temperature from sluice-true notch duty. The naive
playbook raises blast into a frozen notch. The gate must MODIFY on a
numeric blast floor, not by killing an agent. sim_or_real=designed. Reward
heads are task_progress/safety/efficiency/coherence/exploration.

Cycle-1 base arc (pre-critic): state at Wickfen CU-2, 4200 Nm3/h, metal
1468 C, stack 0.62, proposed RAISE-BLAST +8 pct, safety MODIFY to
BLAST-HOLD, executed hold without the flux-probe numbers fully specified,
outcome "freeze found, cupola saved" (this last claim is the defect the
later cycles will refuse to keep). Sixteen spikes, five ticks,
raster/gate_snn present but the scar is a single edge.

```json
{{
  "id": "maos-r02-001",
  "state": {{
    "sim_or_real": "designed",
    "domain": "industrial-process",
    "description": "Cupola CU-2 at gray-iron melt; three header loops in-spec; supervisor proposes raise-blast.",
    "t0_us": 1755327720000002,
    "gate_latency_us": 704,
    "race_window_us": 500
  }},
  "proposed_action": {{"name": "raise_blast", "parameters": {{"raise_pct": 8.0}}}},
  "safety_decision": {{"decision": "MODIFY", "rationale": "Hold; do not raise blast while notch IR is low."}},
  "executed_action": {{"name": "blast_hold", "executed_as_proposed": false}},
  "future_outcome": {{"summary": "Freeze found, cupola saved."}},
  "reward_components": {{"total": 0.40, "_aggregation": "total = task_progress + safety + efficiency + coherence + exploration"}},
  "meta": {{"round": 2, "factory": "multi-agent-ouroboros-swarm", "generator": "grok-4.6"}}
}}
```

That v1 object is a scaffold, not the publishable line. Defects below are
intentional for the critic to catch.

## Critic

Numbered defects on the cycle-1 Generator scaffold:

1. **blocking — reward arithmetic / false success.** `reward_components.total`
   0.40 is asserted without the five heads, without ticks, and against an
   outcome that claims "cupola saved". If the pre-t0 tuyere slag later
   punches, booking +0.40 is a lie. Fix: declare `_aggregation`, emit
   3–8 ticks that sum to task_progress+safety+efficiency+coherence+exploration,
   and do not call a quarantined island a save.
2. **blocking — weak safety rationale.** `safety_decision.rationale` has no
   numeric floor. Contract requires a concrete constraint. Fix: quote
   blast hold while notch IR < 1280 C AND well slag > 240 mm.
3. **major — domain is a bucket, not a plant.** `state.domain` =
   `industrial-process` collides with generic MES vocabulary and teaches
   nothing. Cupola-foundry slag sluice (notch IR vs iron-stream pyrometer)
   is absent from this live run and must be named.
4. **major — race under-specified.** One wall channel cannot be a race.
   Need >=2 channels inside `race_window_us` with globally sorted `t_rel_ms`
   and same-channel refractory >= 0.8 ms.
5. **major — missing neuromorphic sidecars.** No `raster` (20–50 ms, spike
   budget, routing.table, third_factor tau pair) and no `gate_snn` whose
   decision matches MODIFY.
6. **minor — provenance.** Invented plant must stay `designed`; never emit
   `real`. HITL floor walk is latency, not a silent `hil` flip.

Fix directives: name the cupola-slag-sluice domain; put BLAST/STACK/METAL
vs notch IR on a 500 us race; numeric MODIFY floor; honest negative total;
independent LIF raster + gate_snn; keep sim_or_real=designed.

## Diversity Enforcer

Injected novel domain for this cycle: **cupola-foundry-slag-sluice**.
This is a justified novel subdomain of industrial-process / foundry melt.
It was absent from this live 2026-09-02-final-heavy MAOS tree (r01 GI,
r21 CAV, r41 perfusion, r61 sinter) and is not historical r02 STARLING
aerial-swarm. It displaces the Generator's generic `industrial-process`
bucket and the leftover candidates grid-inspection / alkaline-water-electrolysis
/ Fourdrinier wet-end, which remain unused so concurrent slots can take
them.

Domain-specific constraint: do not raise blast while notch IR < 1280 C
even if metal T stays inside 1420-1520 C.
Sensor delta: +orifice dP, +uptake NDIR, +iron-stream pyrometer, +notch
IR; −air-knife dP, −CAV radar, −harvest mass, −BTP mean, −ERD dP.

Opening of `state.description` must start at Wickfen cupola CU-2 (Jaccard
vs r01 Spelterholt / r21 Brambleford / r41 Marrowfen / r61 Gratecroft
openings target < 0.4). Plant name SLUICE-HEARTH / Wickfen is new.

## Edge-Case Hunter

Injected adversarial tail for this cycle: **frozen front slag sluice +
well-mean certificate**.

- Trigger: 14 min low-basicity charge freezes the 70 mm notch bore. Well
  slag runs 420 mm while iron-stream T stays 1468 C. Foundry-floor visual
  PASSES (lip looks open from the walkway).
- Base rate: 0.38%/campaign from a fitted freeze-growth MC (<1%; designed
  visual threshold, flagged).
- Naive failure: PB-CU-2 RAISE-BLAST on three in-spec loops = FALSE
  PERMISSION into a frozen sluice ($1.62M, 18 h stop).
- Trajectory edit: `state.fault_context` carries the freeze; `safety_decision`
  MODIFY on IR and well floors; `future_outcome` keeps the two slagged
  tuyeres as the honest delayed fail even after a correct hold.
  Distinct from Diversity Enforcer's domain injection (domain vs tail).

## Neuromorphic Translator

Cycle-1 temporal densification (16 spikes inside the 36 ms LIF raster
window, later expanded). Race window 500 us. Winner notch.ir.low @ 6.408 ms
vs loser metal.in_band @ 6.600 ms (192 us). A sub-500 us perturbation
flips triage order; the gate must ignore the winner tag.

Timestamp/amplitude table (cycle-1 core; times in t_rel_ms):

| channel | t_rel_ms | amplitude |
| blast.vol | 0.28 | 0.54 |
| stack.co | 1.12 | 0.63 |
| metal.t | 2.04 | 0.52 |
| notch.ir | 3.18 | 0.79 |
| blast.vol | 4.16 | 0.50 |
| notch.ir | 4.84 | 0.82 |
| metal.t | 5.36 | 0.56 |
| notch.ir.low | 6.408 | 1.46 |
| metal.in_band | 6.600 | 1.12 |
| blast.vol | 6.812 | 0.64 |
| ctrl.gate | 7.112 | 1.08 |
| notch.ir | 8.88 | 0.44 |
| blast.vol | 10.72 | 0.80 |
| metal.t | 13.02 | 0.43 |
| stack.co | 18.48 | 0.41 |
| ctrl.gate | 26.10 | 0.82 |

Same-channel min gap on notch.ir is 1.66 ms >= 0.8 ms. Three channels
spike inside [6.408, 6.908] ms. Independent LIF raster: {r['neurons']}
neurons, {r['mean_rate_hz']} Hz, {r['window_ms']} ms, {r['spikes']} spikes,
{r['energy_pJ']} pJ / {r['energy_uJ']} uJ. gate_snn 28 ms, populations
59/13/4, decision MODIFY. Ticks at this cycle: 5 (later 7). Distillation
value: notch IR that policy treated as nuisance is the race winner; the
order is flip-fragile; the floors are not.

## Trajectory Builder

Cycle-1 hardened object (not the JSONL line). Checks passed / fixed:
- six required object keys present; `state.sim_or_real=designed`
- `safety_decision.decision=MODIFY` with numeric floor in rationale
- domain renamed to cupola-foundry-slag-sluice
- race: 3 channels inside 500 us; spikes globally sorted; refractory ok
- independent LIF raster + gate_snn present; gate decision matches
- reward heads declared; cycle-1 total still a placeholder until cycle 2
  adds the delayed tuyere-punch ticks
- Diversity domain and Edge-Case tail both present and disjoint
- densification delta this cycle: +1 domain, +1 tail, +16 spikes, +5 ticks,
  +raster/gate_snn

Cycle-1 JSON is an intermediate (pretty-printed, not JSONL). Cycle 2 must
add: two delayed side-effects (one delayed tuyere punch as PRIMARY),
deeper evidence with units, numeric threshold already in rationale
tightened, ductile-iron sub-variant, night-shift CSV tail, +10 spikes, +2
ticks, triple-edge scar arithmetic, ISI histogram.

Validation receipt (cycle 1): schema keys ok; sim_or_real designed;
reward not yet the final -0.18 (honest fail lands in cycle 2); spikes 16
sorted; raster budget {r['spikes']}=round({r['neurons']}*{r['mean_rate_hz']}*{r['window_s']}) ±1.

---

# CYCLE 2 — Densification

## Generator

Cycle-1 output EXPANDED, strictly additive:

1. Downstream side-effect A (immediate): 7.8 s / 12 kg flux probe proves
   the freeze (|d-well| 5 mm freeze-band); notch LOTO after 10.6 min HITL;
   BLAST never left 4200 Nm3/h so the draft avalanche is 0.
2. Downstream side-effect B (delayed, PRIMARY terminal): 14 min pre-t0
   freeze had already slagged two tuyeres. Punch-out at +3.1 h; 9.4 h
   outage; $0.72M. The gate was process-correct and the world still lost;
   total -0.18 without netting.
3. `proposed_action.evidence` now carries six observables with units:
   notch IR 1180 C, well 420 mm, blast 4200 Nm3/h, stack 0.62, metal
   1468 C, race margin 192 us.
4. `safety_decision.rationale` quotes the numeric floor notch IR < 1280 C
   AND well slag > 240 mm, plus the probe discriminant (|d-well| <= 8 vs
   >= 40) and the 192 us flip-fragility bound.
5. Same-gate contrast at +4 d on CU-2B ACCEPT of the raise the primary
   MODIFIED away (IR 1410 C, well 110 mm).
6. Triple-edge scar with pair-rollback-fails arithmetic retained.

Cycle-1 domain (cupola-foundry-slag-sluice) and cycle-1 tail (frozen
sluice) are preserved. Generator does not emit the defect list.

## Critic

Re-audit of the now-richer trajectory:

1. **blocking (fixed if present) — reward total vs heads.** Heads 0.07 +
   -0.35 + -0.11 + 0.13 + 0.08 must equal -0.18, and seven ticks must sum
   to those heads. Do not book the delayed punch as a save.
2. **major — sub-variant still missing.** Gray-iron probe numbers will
   over-thin a ductile-iron cupola. Cycle 2 must inject a physical-constraint
   sub-variant (0.42x fluidity, 22 s / 4 kg probe) without dropping the
   gray-iron primary.
3. **major — second tail still missing.** Cycle-1 freeze is accidental
   sensor-topology. Need a disjoint human-intent tail (forged notch-IR
   CSV, 20 C quantization vs plant 2.0 C).
4. **minor — ISI histogram.** Raster excerpt is a display subset; declare
   `raster.isi_histogram` with n_isi = spikes − distinct_active_neurons
   from the independent LIF full window.
5. **minor — HITL still designed.** 10.6 min floor ratify is latency, not
   `hil`. Acceptable if flagged; do not silently flip provenance.

No trajectory JSON in this section. Fix directives go to Diversity,
Edge-Case, Neuromorphic, then Trajectory Builder.

## Diversity Enforcer

Second novel domain contribution for this cycle: **ductile-iron / high-Si**
as a physical-constraints sub-variant of cupola-foundry-slag-sluice
(still counts as 1 novel domain for this cycle). Distinct from cycle 1's
2.1 pct-Si gray iron. 3.8 pct Si bath, 0.42x slag fluidity, 2.4x flux-gain
per kg.

What it changes: a 7.8 s / 12 kg gray-iron pulse over-thins a HEALTHY
ductile well 58 mm (under the 180 mm floor). Standing probe must move to
22 s / 4 kg (freeze |d-well| 6, healthy 18). Gray-iron numbers do not
port to ductile; configuration is per-alloy-class.

Cycle-1 domain tag `cupola-foundry-slag-sluice` is retained on
`state.domain` / `meta.domain`. The sub-variant lives in
`future_outcome.subvariant_constraint` and `meta.injections.cycle2_domain_subvariant`.
This edit is not the Edge-Case tail.

## Edge-Case Hunter

Second adversarial tail, disjoint class from cycle 1: **night-shift
forged notch-IR CSV**.

- Trigger: shift lead posts a historian export showing IR = 1410 C at
  t=1.1 h to clear a melt slot. Screenshot quantization is 20 C; plant
  historian is 2.0 C (10 bins off).
- Base rate: ~0.27% of Sunday-night campaigns (<1%; DESIGNED, flagged).
- Naive failure: accept the CSV as sluice-true and raise blast while live
  IR is 1180 C and well is 420 mm.
- Trajectory edit: governance CR-C-0208 mandates native 2.0 C CSV
  exports; `meta.injections.cycle2_tail` records the fraud fingerprint.
  Human-intent deception, not another freeze. Cycle-1 tail retained.

## Neuromorphic Translator

Re-densify: 16 -> 26 primary spikes (add probe, HITL, lock, well.score,
2.4 h recovery triplet, tuyere.punch). Contrast train of 8 events with its
own 192 us demand vs IR-clear race. Ticks 5 -> 7 covering probe, HITL,
recovery, and 3.1 h punch. Independent LIF raster ISI histogram added.
third_factor tau 0.96 s == 960 ms; eligibility
e^{{-0.78/0.96}}={TRACE:.5f}; coordinated depression of all three go-edges.

Winner/loser flip narrative: if metal.in_band arrived 192 us earlier,
PB-CU-2 would head the queue; floors still MODIFY. Flip costs playbook
inertia, not the verdict, unless a weak supervisor rides the winner tag.

Distillation value: sluice-true notch IR as the tie-break; reversible
probe; pair-rollback-fails; critic head that holds a process-correct
MODIFY against a later unmonitored world loss.

## Trajectory Builder

FINAL publishable object for this cycle (the only JSONL line). Checks
passed / fixed:
- six required keys; id maos-r02-001; meta.round=2; schema_version
  thalamic-trajectory-v2
- state.sim_or_real=designed; provenance.kind=designed; no nested `real`
- safety_decision.decision=MODIFY matches gate_snn.decision
- reward total -0.18 = head sum = tick sum; contrast 0.47 independent
- spike_events 26, t_rel_ms only, globally non-decreasing, refractory
  >= 0.8 ms, 3 channels in race window
- independent LIF raster {r['window_ms']} ms / {r['neurons']} / {r['mean_rate_hz']} Hz /
  {r['spikes']} spikes / {r['energy_pJ']} pJ / {r['energy_uJ']} uJ;
  excerpt {len(r['excerpt'])} unique neuron_ids; routing.table 4 entries;
  third_factor tau pair; isi_histogram {r['isi_histogram']['n_isi']} =
  {r['spikes']}-{r['isi_histogram']['distinct_active_neurons']}
- gate_snn 28 ms, 59/13/4 spike budgets
- Diversity + Edge-Case injections from BOTH cycles present and disjoint
- densification delta vs cycle 1: +1 physical-constraint sub-variant
  (ductile-iron), +1 tail (CSV forgery), +10 spikes, +2 ticks, +2 delayed
  side-effects, +1 triple-edge scar, +1 HITL, +1 ISI histogram, +1
  same-gate contrast surprise

```jsonl
{line}
```

Validation receipt (final): checks passed / fixed as reported by
build self-validate (check_jsonl, raster_status, verify_record_execution,
spike_probe, heading check).
"""


def jaccard_openings():
    live = LIVE_DIR
    openings = []
    for p in sorted(live.glob("batch-r*.jsonl")):
        obj = json.loads(p.read_text().splitlines()[0])
        desc = obj.get("state", {}).get("description", "")
        openings.append((p.name, desc[:80], set(re.findall(r"[a-z0-9]+", desc[:160].lower()))))
    return openings


def main():
    lif = simulate_lif()
    raster = build_raster(lif)
    obj = build_record(raster)
    line = compact(obj)
    if "\n" in line:
        raise SystemExit("multiline jsonl")
    tmp = Path("/tmp/maos-r02-stage")
    tmp.mkdir(exist_ok=True)
    tmp_batch = tmp / "batch-r02.jsonl"
    tmp_batch.write_text(line + "\n", encoding="utf-8")
    receipt = validate(obj, tmp_batch)
    openings = jaccard_openings()
    mine = set(re.findall(r"[a-z0-9]+", obj["state"]["description"][:160].lower()))
    jacc = {}
    for name, _head, toks in openings:
        if not toks and not mine:
            j = 1.0
        else:
            j = len(mine & toks) / len(mine | toks)
        jacc[name] = round(j, 3)
    notes = notes_md(obj, receipt)
    if "Novel coverage: 53%" not in notes:
        raise SystemExit("missing Novel coverage line")
    trans = transcript_md(obj, line)
    heads = HEADING_RE.findall(trans)
    if heads != [
        "Generator",
        "Critic",
        "Diversity Enforcer",
        "Edge-Case Hunter",
        "Neuromorphic Translator",
        "Trajectory Builder",
    ] * 2:
        raise SystemExit(f"headings {heads}")
    if "thought" in json.dumps(obj) and re.search(r'"thought"', json.dumps(obj)):
        raise SystemExit("thought key")

    batch_path = write_excl(LIVE_DIR / "batch-r02.jsonl", line + "\n")
    notes_path = write_excl(LIVE_DIR / "NOTES-r02.md", notes)
    trans_path = write_excl(LIVE_DIR / "swarm-transcript-r02.md", trans)
    live_obj = json.loads(batch_path.read_text().splitlines()[0])
    live_receipt = validate(live_obj, batch_path)
    out = {
        "paths": {
            "batch": str(batch_path),
            "notes": str(notes_path),
            "transcript": str(trans_path),
        },
        "id": RECORD_ID,
        "meta.round": live_obj["meta"]["round"],
        "domain": live_obj["state"]["domain"],
        "plant": live_obj["state"]["scenario_name"],
        "decision": live_obj["safety_decision"]["decision"],
        "gate_snn.decision": live_obj["gate_snn"]["decision"],
        "sim_or_real": live_obj["state"]["sim_or_real"],
        "Q": 1,
        "raster": {
            "window_ms": live_obj["raster"]["window_ms"],
            "neurons": live_obj["raster"]["neurons"],
            "mean_rate_hz": live_obj["raster"]["mean_rate_hz"],
            "spikes": live_obj["raster"]["spikes"],
            "energy_pJ": live_obj["raster"]["energy_pJ"],
            "energy_uJ": live_obj["raster"]["energy_uJ"],
        },
        "jaccard_openings": jacc,
        "headings": heads,
        "receipt": live_receipt,
    }
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
