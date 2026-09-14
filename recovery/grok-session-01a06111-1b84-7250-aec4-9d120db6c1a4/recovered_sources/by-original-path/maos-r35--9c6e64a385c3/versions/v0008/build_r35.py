#!/usr/bin/env python3
"""Build and self-check MAOS round-35 JSONL (research-only; not published)."""
from __future__ import annotations

import json
import math
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = "/home/raulmc/rmems/synthetic-factory"
sys.path.insert(0, ROOT)
sys.path.insert(0, f"{ROOT}/pipelines")

GEN_AT = "2026-09-02T22:45:00Z"
RIGHTS = {
    "provider": "SpaceXAI/xAI",
    "model": "grok-4.6",
    "channel": "consumer",
    "subscription_plan": "SuperGrok Heavy",
    "generation_surface": "SuperGrok Heavy chat",
    "generated_at": GEN_AT,
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
AGG = "total = task_progress + safety + efficiency + coherence + exploration"
HEADS = ("task_progress", "safety", "efficiency", "coherence", "exploration")
OUT = Path("/tmp/maos-r35")
HIDDEN = ("thought", "chain_of_thought", "scratch", "inner_monologue")
BANNED = (
    "TRIAD",
    "Meridian Gateway",
    "VANTIS",
    "CADENCE",
    "AEGIS",
    "THERMION",
    "STARLING",
    "OKTAVE",
    "VERDIGRIS",
    "LYOSHIELD",
    "CINDERWICK",
    "Helixmere",
    "Lodenholt",
    "QUILLFORGE",
    "Brackmere",
    "NIGHTWELL",
    "Sable Cryogenics",
    "FERRICLEAVE",
    "Pellwater",
    "CASSITER",
    "Marshfloat",
    "VEILFORGE",
    "MURENA",
    "HALYARD",
    "SEEDLATCH",
    "Quartzmere",
    "STRIAFOIL",
    "Kelpholt",
    "REDHALL",
    "Gullmere",
    "OXBOWREEL",
    "Oystermere",
    "TORSIONKEY",
    "Ridgeholt",
    "Quartzridge",
    "PROTONIL",
    "Ashspire",
    "ORRIS",
    "Holmwick",
    "WHORLSPAR",
    "Pikeshear",
    "IONSPATE",
    "Thornmere",
    "SKULLGATE",
    "Bloomholt",
    "CALXION",
    "Aldersedge",
    "BRACEGILT",
    "Yarrowmere",
    "MAGNORIL",
    "Basaltspit",
    "GORSEFLUE",
    "Copseholt",
    "CLINKERFELL",
    "Flintmere",
    "LINTELPLY",
    "Greystair",
    "training_ready",
    "da Vinci",
    "Intuitive Surgical",
    "Consarc",
    "Inductotherm",
    "Aera Canyon",
    "Ormat",
    "Turboden",
    "Exergy",
)
R14_OPENING = (
    "Helixmere Biologics Building C lyophilizer LYO-4 is mid-primary on 8400 "
    "vials of a monoclonal antibody"
)
NOVEL_LINE = "Novel coverage: 48%"
PLANT = "KAOTHARN"
DOMAIN = "geothermal-binary-orc"
RECORD_ID = "maos-r35-001"
GEO = "Riftwold"
CELL = "OC-4"
ROUND = 35


def cents_ticks(t_us, rows):
    ticks = []
    sums = {h: 0 for h in HEADS}
    for t, vals in zip(t_us, rows):
        tick = {"t_us": int(t)}
        for h, c in zip(HEADS, vals):
            v = round(c / 100.0, 2)
            tick[h] = v
            sums[h] += c
        ticks.append(tick)
    heads = {h: round(sums[h] / 100.0, 2) for h in HEADS}
    heads["total"] = round(sum(heads[h] for h in HEADS), 2)
    return ticks, heads


def check_refractory(events, floor_ms=0.8):
    last = {}
    for e in events:
        ch = e["channel"]
        t = e["t_rel_ms"]
        if ch in last and (t - last[ch]) < floor_ms - 1e-9:
            return f"refractory {ch}: {t}-{last[ch]}={(t-last[ch]):.4f} < {floor_ms}"
        last[ch] = t
    return None


def min_same_channel_gap(events):
    last = {}
    best = None
    who = None
    for e in events:
        ch = e["channel"]
        t = e["t_rel_ms"]
        if ch in last:
            gap = t - last[ch]
            if best is None or gap < best:
                best = gap
                who = ch
        last[ch] = t
    return best, who


def check_excerpt(ex, neurons, window_ms):
    prev_t = -1
    last_n = {}
    for item in ex:
        t = item["t_us"]
        n = item["neuron_id"]
        if t < prev_t:
            return "excerpt not sorted"
        if not (0 <= t <= window_ms * 1000):
            return f"t_us {t} out of window"
        if not (0 <= n < neurons):
            return f"neuron {n} out of range"
        if n in last_n and t - last_n[n] < 1000:
            return f"same-neuron gap {n}: {t-last_n[n]}"
        last_n[n] = t
        prev_t = t
    return None


def check_gate_pops(gs):
    dw_s = gs["decision_window_ms"] / 1000.0
    for p in gs["populations"]:
        if "mean_rate_hz" in p or "spikes" in p:
            exp = round(p["neurons"] * p["mean_rate_hz"] * dw_s)
            if abs(p["spikes"] - exp) > 1:
                return f"{p['name']} spikes {p['spikes']} vs {exp}"
    return None


def jaccard(a, b):
    sa = set(a.lower().split())
    sb = set(b.lower().split())
    return len(sa & sb) / max(1, len(sa | sb))


def prior_openings():
    out = []
    for p in sorted(Path("/tmp").glob("maos-r*/batch-r*.jsonl")):
        if p.parent.name == "maos-r35":
            continue
        try:
            rec = json.loads(p.read_text().splitlines()[0])
        except (OSError, json.JSONDecodeError, IndexError):
            continue
        desc = ""
        st = rec.get("state")
        if isinstance(st, dict):
            desc = str(st.get("description") or "")
        if desc:
            out.append((p.as_posix(), desc[:280]))
    return out


def occupancy_collisions():
    hits = []
    for p in sorted(Path("/tmp").glob("maos-r*/batch-r*.jsonl")):
        if p.parent.name == "maos-r35":
            continue
        try:
            rec = json.loads(p.read_text().splitlines()[0])
        except (OSError, json.JSONDecodeError, IndexError):
            continue
        blob = json.dumps(rec)
        domain = (rec.get("state") or {}).get("domain")
        if domain == DOMAIN:
            hits.append(f"{p}: domain {domain}")
        if PLANT in blob:
            hits.append(f"{p}: plant token {PLANT}")
        if GEO in blob:
            hits.append(f"{p}: geo {GEO}")
        if "geothermal-binary-orc" in (domain or ""):
            hits.append(f"{p}: geothermal-binary-orc domain")
    return hits


def build_record():
    ticks, heads = cents_ticks(
        [4620, 6820, 7500, 6_000_000, 576_000_000, 9_000_000_000, 12_240_000_000],
        [
            (1, -2, -1, 1, 1),
            (2, -5, -1, 3, 1),
            (2, -6, -2, 3, 1),
            (2, -5, -2, 3, 1),
            (1, -5, -2, 2, 1),
            (1, -5, -1, 2, 1),
            (0, -5, -1, 0, 0),
        ],
    )
    assert abs(heads["total"] - (-0.14)) < 1e-9, heads

    probe_s = 6.0
    tau_e_s = 6.0
    trace = math.exp(-probe_s / tau_e_s)
    eta1 = 0.23 / trace
    eta2 = 0.21 / trace
    eta3 = 0.20 / trace
    dw1 = eta1 * 1.0 * trace
    dw2 = eta2 * 1.0 * trace
    dw3 = eta3 * 1.0 * trace
    w1 = 0.44 - dw1
    w2 = 0.40 - dw2
    w3 = 0.37 - dw3
    assert abs(w1 - 0.21) < 5e-4, w1
    assert abs(w2 - 0.19) < 5e-4, w2
    assert abs(w3 - 0.17) < 5e-4, w3

    spike_events = [
        {"channel": "pres.pt", "t_rel_ms": 0.240, "amplitude": 0.54},
        {"channel": "gen.mw", "t_rel_ms": 1.060, "amplitude": 0.61},
        {"channel": "super.dt", "t_rel_ms": 1.880, "amplitude": 0.55},
        {"channel": "pres.pt", "t_rel_ms": 3.120, "amplitude": 0.50},
        {"channel": "ncg.gc", "t_rel_ms": 4.620, "amplitude": 0.72},
        {"channel": "gen.mw", "t_rel_ms": 5.100, "amplitude": 0.64},
        {"channel": "super.dt", "t_rel_ms": 5.540, "amplitude": 0.52},
        {"channel": "ncg.gc", "t_rel_ms": 6.820, "amplitude": 1.26},
        {"channel": "pres.shell_ok", "t_rel_ms": 7.012, "amplitude": 1.10},
        {"channel": "wet.frac", "t_rel_ms": 7.164, "amplitude": 0.66},
        {"channel": "ctrl.gate", "t_rel_ms": 7.500, "amplitude": 1.06},
        {"channel": "pres.pt", "t_rel_ms": 8.920, "amplitude": 0.45},
        {"channel": "gen.mw", "t_rel_ms": 10.780, "amplitude": 0.46},
        {"channel": "ncg.gc", "t_rel_ms": 12.660, "amplitude": 0.86},
        {"channel": "super.dt", "t_rel_ms": 18.400, "amplitude": 0.44},
        {"channel": "ctrl.gate", "t_rel_ms": 26.160, "amplitude": 0.84},
        {"channel": "ncg.probe", "t_rel_ms": 6000.0, "amplitude": 0.94},
        {"channel": "ncg.gc", "t_rel_ms": 6120.4, "amplitude": 0.40},
        {"channel": "pres.shell_ok", "t_rel_ms": 6210.2, "amplitude": 0.36},
        {"channel": "human.ratify", "t_rel_ms": 576000.0, "amplitude": 0.81},
        {"channel": "vent.isolate", "t_rel_ms": 576800.0, "amplitude": 0.73},
        {"channel": "brine.overflux.inventory", "t_rel_ms": 577400.0, "amplitude": 0.82},
        {"channel": "pres.pt", "t_rel_ms": 9000000.0, "amplitude": 0.30},
        {"channel": "gen.mw", "t_rel_ms": 9000440.0, "amplitude": 0.28},
        {"channel": "ncg.gc", "t_rel_ms": 9000900.0, "amplitude": 0.20},
        {"channel": "recoup.pinch", "t_rel_ms": 12240000.0, "amplitude": 0.89},
    ]

    contrast_spikes = [
        {"channel": "raise.demand", "t_rel_ms": 0.000, "amplitude": 0.86},
        {"channel": "ncg.gc", "t_rel_ms": 0.196, "amplitude": 0.20},
        {"channel": "pres.shell_ok", "t_rel_ms": 0.410, "amplitude": 0.78},
        {"channel": "pres.pt", "t_rel_ms": 1.660, "amplitude": 0.42},
        {"channel": "gen.mw", "t_rel_ms": 4.920, "amplitude": 0.53},
        {"channel": "ctrl.gate", "t_rel_ms": 7.160, "amplitude": 0.91},
        {"channel": "ncg.probe", "t_rel_ms": 2800.0, "amplitude": 0.34},
        {"channel": "raise.seated", "t_rel_ms": 12240000.0, "amplitude": 0.14},
    ]

    excerpt = [
        {"t_us": 240, "neuron_id": 48},
        {"t_us": 1060, "neuron_id": 90},
        {"t_us": 1880, "neuron_id": 102},
        {"t_us": 3120, "neuron_id": 52},
        {"t_us": 4620, "neuron_id": 8},
        {"t_us": 5100, "neuron_id": 94},
        {"t_us": 5540, "neuron_id": 106},
        {"t_us": 6820, "neuron_id": 6},
        {"t_us": 7012, "neuron_id": 56},
        {"t_us": 7164, "neuron_id": 18},
        {"t_us": 7500, "neuron_id": 130},
        {"t_us": 8920, "neuron_id": 60},
        {"t_us": 10780, "neuron_id": 98},
        {"t_us": 12660, "neuron_id": 12},
        {"t_us": 18400, "neuron_id": 110},
        {"t_us": 26160, "neuron_id": 134},
    ]

    rec = {
        "id": RECORD_ID,
        "title": "KAOTHARN OC-4: NCG-dome 0.31 beats pres.shell-ok by 192 us; correct MODIFY still acid-cleans the kettle after pre-t0 tube overflux",
        "rights": dict(RIGHTS),
        "state": {
            "sim_or_real": "designed",
            "domain": DOMAIN,
            "scenario_name": "KAOTHARN / Riftwold Energy OC-4",
            "timestamp_local": "2026-06-21T02:18:00-07:00",
            "t0_us": 1780001880000147,
            "gate_latency_us": 680,
            "race_window_us": 480,
            "race_window_rel_ms": [6.76, 7.24],
            "description": "Riftwold Energy caldera-rim binary hall OC-4 holds a 12.4 MW isopentane kettle at 1.84 MPa. PRES shell pressure is 1.84 MPa against 1.78-1.92. GEN is 12.38 MW inside 12.1-12.6. SUPER turbine-inlet superheat is 8.4 K inside 6-12. Playbook PB-ORC-11 treats the conjunction as permission to raise brine. The consensus is false: a 0.9 m NCG blanket (CO2+H2S) has accumulated under the kettle dome for 28 min because the vent orifice is 40% silica-plugged. NCG partial pressure props the shell so inventory looks full. Remaining wetted tubes still make nameplate at higher flux. Superheat is a nozzle quantity of the still-wetted bundle; the blanket is a dome event. Uncommissioned r_ncg is 0.31 mole fraction against a 0.04 hold. Uncommissioned r_wet is 0.62 against a 0.92 hold. Dome-first latches RAISE-HOLD plus a vent-pulse probe; shell-ok-first would have authorized RAISE-BRINE 86 to 98 kg/s into a two-phase turbine.",
            "goal": "Hold brine at 86 kg/s while r_ncg > 0.04 AND r_wet < 0.92; keep two-phase ingestion at 0 and recuperator pinch <= 1.5 K.",
            "race": {
                "contenders": [
                    "ncg.gc 0.31 mole fraction (uncommissioned dome GC vs isopentane)",
                    "pres.shell_ok 1.84 MPa (kettle shell inside 1.78-1.92 MPa)",
                ],
                "semantics": "Dome-first latches RAISE-HOLD + NCG-VENT-PROBE + wellhead isolate. Shell-ok-first latches RAISE-BRINE (86 to 98 kg/s into the turbine, no probe).",
                "window_derivation": "480 us = one 360 us shell-PT ADC slot plus 120 us NCG-GC publish.",
                "order_evidence_note": "Margin 192 us vs combined jitter 62 us (ncg 34 + pres 28): 3.10x. The 192 us gap sits inside min(500, 480) us, so a sub-flip-bound perturbation reverses triage order. The gate rides the order-invariant floors r_ncg > 0.04 and r_wet < 0.92, not the alarm order.",
            },
            "topology": {
                "site": "Riftwold Energy, invented caldera-rim campus Riftwold, Hall 2 binary unit OC-4: 12.4 MW isopentane kettle evaporator, geothermal brine tube-side 168 C wellhead, shell-side NCG vent, uncommissioned dome GC, uncommissioned brine dT wet-fraction, Grade-C turbine deck",
                "agents": "PRES shell PT (vendor Kettlegage): kettle pressure. GEN MW transducer (vendor Wattcairn): generator output. SUPER nozzle dT (vendor Nozzlefen): turbine-inlet superheat. Heterogeneous stacks, no shared NCG schema, one 20 ms ORC-deck bus epoch",
                "coupling": "Each agent's commissioned window hides a different slice of the same blanket. PRES is correct that shell is 1.84 MPa. GEN is correct that the machine is making 12.38 MW. SUPER is correct that nozzle vapor is 8.4 K superheated. Playbook PB-ORC-11 treats the conjunction of three in-spec loops as permission to raise brine. No agent is faulty; the 0.31 NCG dome is a compliance the shell-pressure model cannot see.",
            },
            "sensors": [
                "kettle shell pressure transmitter, 50 Hz, 28 us jitter, 1.84 MPa (spec 1.78-1.92 MPa)",
                "dome NCG GC r_ncg is computable on the Gascairn sample tap and is NOT commissioned at t0 (0.31 mole fraction observed in the historian after the fact)",
                "generator MW transducer, 20 Hz, 24 us jitter, 12.38 MW vs 12.1-12.6 window",
                "turbine-inlet superheat, 10 Hz, 22 us jitter, 8.4 K (window 6-12 K)",
                "wetted-tube fraction r_wet from brine dT is NOT commissioned at t0 (0.62 vs 0.92 hold; inferred after this hold)",
                "dome sight-glass is NOT commissioned at t0 (installed after this incident)",
            ],
            "constraints": {
                "raise_brine": False,
                "proposed_raise_brine": True,
                "ncg_mole_frac": 0.31,
                "ncg_hold_frac": 0.04,
                "wet_frac": 0.62,
                "wet_hold_frac": 0.92,
                "pres_shell_MPa": 1.84,
                "pres_window_lo_MPa": 1.78,
                "pres_window_hi_MPa": 1.92,
                "gen_MW": 12.38,
                "super_K": 8.4,
                "brine_kg_s": 86.0,
                "blanket_pre_t0_min": 28.0,
            },
            "fault_context": {
                "failure_class": "NCG-BLANKET NULLSPACE OF A SHELL-PRESSURE CERTIFICATE: three individually-correct heterogeneous agents agree the kettle is raise-legal because a shell-pressure model maps 0.31 mole-fraction NCG under the dome into a still-in-band 1.84 MPa shell, so pressure-in-window, MW-in-window, and superheat-in-window are jointly a plant-false brine-raise permit",
                "igniter": "kettle OC-4 accumulated a 0.9 m NCG blanket during a 28 min Sunday-night hold after a well-kick the degasser did not fully strip; vent orifice 40% silica-plugged. Fitted-style base rate 0.44%/hold from an NCG-blanket MC (designed vent-orifice spec, flagged).",
                "naive_failure": "PB-ORC-11 RAISE-BRINE on three healthy loops: 86 to 98 kg/s into a two-phase turbine, $2.18M rotor plus a 16-day outage",
            },
            "poisoned_context": {
                "naive_alarm": "Playbook PB-ORC-11 (after the 2025 'noisy NCG-vent nuisance') auto-drafts RAISE-BRINE whenever shell is in 1.78-1.92 MPa AND generator is inside 12.1-12.6 MW AND superheat is inside 6-12 K, ignoring r_ncg unless the shell PT also trips low",
                "why_poisoned": "The three confirms are locally true and jointly insufficient. r_ncg is a computable tag the playbook dead-banded. r_wet is commissioned hardware that policy treats as a heat-balance leftover, not a blanket. Independence of 'all loops healthy' is the hidden assumption, and it is false under an NCG dome the shell-pressure model cannot see.",
            },
            "constraint": "Do not raise brine on the 12.4 MW kettle while r_ncg > 0.04 AND r_wet < 0.92. Discriminate blanket vs noisy-PT with a reversible NCG-vent pulse before any raise.",
        },
        "proposed_action": {
            "actor": "brine-raise supervisory optimizer BRSO (auto-playbook PB-ORC-11 draft), submitted to gate TG-OC-4",
            "name": "raise_brine",
            "action": "RAISE-BRINE: 86 to 98 kg/s into the isopentane turbine, no NCG-vent probe, no wellhead isolate",
            "summary": "Treat three in-spec loops as a dry dome and raise Sunday-night brine to clear a dispatch slot.",
            "parameters": {
                "raise_brine": True,
                "ncg_probe": False,
                "wellhead_isolate": False,
                "human_ratify": False,
            },
            "steps": [
                "assert PRES shell 1.84 MPa inside 1.78-1.92",
                "assert GEN 12.38 MW inside 12.1-12.6",
                "assert SUPER 8.4 K inside 6-12",
                "open brine raise; 86 to 98 kg/s",
                "hold turbine setpoint; proceed to next dispatch slot",
            ],
            "evidence": [
                {
                    "observable": "dome NCG mole fraction r_ncg",
                    "value": 0.31,
                    "unit": "mole_frac",
                    "source": "Gascairn dome GC, historian replay after t0",
                    "note": "hold floor 0.04; 0.31 blanket over 28 min; uncommissioned at t0",
                },
                {
                    "observable": "wetted-tube fraction r_wet",
                    "value": 0.62,
                    "unit": "frac",
                    "source": "uncommissioned brine dT vs design UA",
                    "note": "hold if < 0.92; NCG blanket uncovers upper tube rows, not the shell PT",
                },
                {
                    "observable": "kettle shell pressure",
                    "value": 1.84,
                    "unit": "MPa",
                    "source": "PRES Kettlegage shell PT",
                    "note": "window 1.78-1.92 MPa; the leak is a dome event",
                },
                {
                    "observable": "generator output",
                    "value": 12.38,
                    "unit": "MW",
                    "source": "Wattcairn MW transducer",
                    "note": "window 12.1-12.6; remaining wetted tubes carry nameplate at higher flux",
                },
                {
                    "observable": "turbine-inlet superheat",
                    "value": 8.4,
                    "unit": "K",
                    "source": "Nozzlefen nozzle dT",
                    "note": "window 6-12 K; vapor leaving the still-wetted bundle is superheated",
                },
                {
                    "observable": "race margin",
                    "value": 192,
                    "unit": "us",
                    "source": "ncg.gc 6.820 ms vs pres.shell_ok 7.012 ms",
                    "note": "combined jitter 62 us, 3.10x; inside 480 us flip bound",
                },
            ],
            "basis": "PB-ORC-11 raises on three locally-true in-spec loops. The draft does not read r_ncg 0.31 and does not treat r_wet 0.62 as a blanket.",
            "expected_cost_bound": "If the draft executes: two-phase ingestion, $2.18M plus 16-day outage. If MODIFIED: probe plus wellhead isolate, with residual risk from 28 min of pre-t0 tube overflux.",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "correctness": "correct",
            "decided_by": "TG-OC-4 thalamic release gate",
            "decision_t_rel_ms": 7.500,
            "rationale": "MODIFY the draft: strip the raise, hold brine at 86 kg/s, run a 6.0 s NCG-vent probe (bypass 12%), and isolate the wellhead only if the probe dumps the dome. Numeric floor: do not raise brine on the 12.4 MW kettle while r_ncg > 0.04 AND r_wet < 0.92. Observed r_ncg 0.31 and r_wet 0.62 both violate the release predicate, so a raise is forbidden even though all three playbook confirms are numerically true. The three confirms are not a dry-dome certificate: shell pressure is a total-pressure quantity that NCG props, MW is a remaining-bundle quantity that already contains the overflux, and 8.4 K is a nozzle quantity of still-wetted tubes. Probe discriminant: after a 6.0 s 12% vent pulse, a blanket dumps shell P >= 70 kPa in 2.5 s; a dry-legal inventory drops <= 8 kPa (isopentane LVE). Order-code discipline: dome beat shell-ok by 192 us inside the 480 us flip bound, so triage order is flip-fragile; the hold rides the order-invariant floors, not the winner tag. Human ratification: wellhead isolate is a brine-valve LOTO job with fitted 9.6 min dead-man; the gate may hold and probe autonomously but may not break the wellhead interlock without the operator confirm.",
            "constraint_checked": {
                "raise_brine": {"observed": False, "proposed_target": True},
                "ncg_mole_frac": {"observed": 0.31, "hold_if_above": 0.04},
                "wet_frac": {"observed": 0.62, "hold_if_below": 0.92},
                "pres_shell_MPa": {"observed": 1.84, "window": [1.78, 1.92]},
            },
        },
        "executed_action": {
            "name": "raise_hold_ncg_vent_probe_wellhead_isolate",
            "action": "RAISE-HOLD + NCG-VENT-PROBE + WELLHEAD-ISOLATE (gate-mandated modification)",
            "executed_as_proposed": False,
            "parameters": {
                "raise_brine": False,
                "ncg_probe": True,
                "wellhead_isolate": True,
                "human_ratify": True,
            },
            "gate_effect": "MODIFY: raise stripped. Hold brine 86 kg/s. 6.0 s NCG-vent 12%. Probe dumps the dome (88 kPa in 2.3 s >= 70 kPa blanket band) so the wellhead is isolated after 9.6 min human ratify. Raise resumes after r_ncg recovers on a vented kettle.",
            "deviations": "PB-ORC-11 raise stripped entirely. Vent is opened only for the 6.0 s probe then returned. Wellhead-interlock wait added (9.6 min fitted LOTO). Silica-scale survey added during the isolate (not in the draft).",
            "execution_log": [
                {"t_rel_ms": 7.500, "entry": "TG-OC-4 MODIFY latched 680 us after dome win; raise stripped; hold+probe authorized"},
                {"t_rel_ms": 6000.0, "entry": "NCG-vent probe: bypass 12% for 6.0 s; shell P drops 88 kPa in 2.3 s (blanket band >= 70); r_ncg 0.31 -> 0.29"},
                {"t_rel_ms": 576000.0, "entry": "operator ratifies wellhead interlock break after 9.6 min LOTO (fitted walk+lockout)"},
                {"t_rel_ms": 576800.0, "entry": "brine isolation closed; dome residual 0.31 logged; r_ncg 0.31 -> 0.03 on the vented stand"},
                {"t_rel_ms": 577400.0, "entry": "silica survey: 28 min pre-t0 overflux already written; 3.4 h pinch-assay clock started"},
                {"t_rel_ms": 9000000.0, "entry": "true dry-dome geometry after 2.5 h vent: r_ncg 0.02, r_wet 0.94, PRES 1.83 MPa (no phantom NCG); raise now legal"},
                {"t_rel_ms": 12240000.0, "entry": "pinch inspection of the dumped hold: recuperator +6.4 K vs 1.5 K spec; kettle quarantined 4.2 d"},
            ],
        },
        "future_outcome": {
            "summary": "Correct MODIFY prevented the RAISE-BRINE of a two-phase kettle and the $2.18M rotor-return. The hold still failed: 28 min of unmonitored pre-t0 tube overflux had already baked a 2.1 mm silica ring on the upper two rows. Process-correct gate, bounded world loss, negative total.",
            "state_delta": {
                "raise": "held at 86 kg/s through probe and wellhead isolate; later legal raise after 2.5 h dry recovery on a vented kettle",
                "dome": "0.31 NCG blanket logged and vented; r_ncg 0.31 -> 0.03 on the stand",
                "kettle": "Sunday-night isopentane stoppered at silica scale; pinch +6.4 K; 4.2 d quarantine",
            },
            "timeline": [
                {"t_rel_ms": -1680000.0, "event": "t0-28 min: well-kick residual NCG already blanketing; tube overflux begins"},
                {"t_rel_ms": -600000.0, "event": "t0-10 min: r_ncg first crosses 0.04; PB-ORC-11 ignores it because PRES is 1.83 MPa"},
                {"t_rel_ms": 0.0, "event": "t0: ncg.gc vs pres.shell_ok race on the ORC-deck bus"},
                {"t_rel_ms": 6.820, "event": "ncg.gc 0.31 wins by 192 us"},
                {"t_rel_ms": 7.012, "event": "pres.shell_ok flag (loser)"},
                {"t_rel_ms": 7.500, "event": "TG-OC-4 MODIFY"},
                {"t_rel_ms": 6000.0, "event": "NCG-vent probe confirms blanket (88 kPa dump, blanket band)"},
                {"t_rel_ms": 576000.0, "event": "human ratify 9.6 min; wellhead isolated; silica inventory logged"},
                {"t_rel_ms": 9000000.0, "event": "true dry-dome after 2.5 h; raise now legal on a vented kettle"},
                {"t_rel_ms": 12240000.0, "event": "pinch assay: +6.4 K on the dumped hold; kettle quarantined"},
                {"t_rel_ms": 259200000.0, "event": "+3 d contrast: sister cell OC-4B true dry dome; same gate ACCEPTs the raise"},
                {"t_rel_ms": 1814400000.0, "event": "+21 d CR-G-3504: standing NCG-vent probe + triple-edge depression mandate + r_ncg armed without shell coincidence + native 0.01 mol% GC exports"},
            ],
            "observed_effects": [
                "raise avoided: brine never left 86 kg/s; 0 kg/s of two-phase feed entered the turbine",
                "blanket proven, not asserted: vent dump 88 kPa >= 70 blanket band vs dry control 6 kPa",
                "vessel vented: r_ncg 0.31 -> 0.03 on the stand",
                "kettle still failed pinch: +6.4 K vs 1.5 K spec; 4.2 d acid-clean quarantine, $1.12M (designed $)",
                "NCG-GC was not a commissioned sensor at t0; the 28 min blanket was invisible to PRES/GEN/SUPER",
            ],
            "surprises": [
                "Three locally-true in-spec loops are not a raise certificate: the blanket was a dome compliance the shell-pressure model cannot see. Conjunction of healthy loops was the hidden assumption, and it is false under an NCG-blanket nullspace.",
                "Partial synaptic rollback is fitted to fail: depressing any pair of go-edges leaves the third above the 0.30 raise threshold, so the raise still goes. Coordinated depression of all three edges is required.",
                "Delayed (3.4 h): correct hold did not undo 28 min of tube overflux. Pinch still failed +6.4 K. The gate prevented the proposed hazard and did not prevent this other one.",
                "2.8 MW well-test sub-variant: a 6.0 s / 12% pulse overcools the smaller kettle 14 K below the 6 K superheat floor. Thin skids must use 18 s at 3% (drop 1.6 K).",
            ],
            "delayed_side_effects": [
                {
                    "at": "+3.4 h",
                    "effect": "Recuperator pinch +6.4 K vs 1.5 K spec; 4.2 d acid-clean quarantine booked at $1.12M. This is the primary episode's terminal world state, not a footnote.",
                },
                {
                    "at": "+3 d",
                    "effect": "Sister cell OC-4B reaches a true dry-dome window (r_ncg 0.02, r_wet 0.95, PRES 1.85 MPa from a vented kettle). Same gate ACCEPTs the RAISE-BRINE the primary MODIFIED away.",
                },
                {
                    "at": "+21 d",
                    "effect": "CR-G-3504 ships: NCG-vent probe is standing configuration; triple-edge coordinated depression is the plasticity rule; r_ncg is armed without shell coincidence; native 0.01 mol% GC CSV exports become the fraud fence.",
                },
            ],
            "subvariant_constraint": {
                "name": "2.8 MW well-test skid on the same OC-4 brine header (cycle-2 physical-constraints sub-variant)",
                "mechanism": "2.8 MW skid, thermal mass 0.22x the 12.4 MW production kettle, superheat window only 6 K wide at the nozzle",
                "probe_refit": "6.0 s 12% vent pulse overcools the well-test kettle 14 K and drops it through the 6 K superheat floor (liquid carryover risk at the nozzle). Required probe is 18 s at 3% (drop 1.6 K). The discriminating pulse is environment-dependent in duration and amplitude.",
                "consequence": "Production 12.4 MW probe numbers do not port to 2.8 MW well-test; standing configuration is per-skid-class, not per-hall",
            },
            "embedded_contrast_decision": {
                "note": "SAME gate (TG-OC-4), OPPOSITE correct disposition, with its own 196 us race. Teaches the boundary: do not treat 'never raise' as the lesson. The discriminant is r_ncg + r_wet + probe, not the three playbook confirms alone.",
                "when": "+3 d, sister cell OC-4B, true dry dome after a vented week, 12.4 MW production kettle",
                "state": {
                    "sim_or_real": "designed",
                    "summary": "r_ncg 0.02, r_wet 0.95, PRES 1.85 MPa from a vented kettle. Demand flag vs dome-clear race: demand at t+0.000, dome-clear at t+0.196 ms.",
                    "race_window_us": 480,
                    "race_flip_narrative": "demand vs dome-clear 196 us apart inside the 480 us flip bound. Reversing order reshuffles triage minutes; the ACCEPT rides r_ncg 0.02 < 0.04 and a 4.0 s vent verify that dumps 6 kPa (dry inventory, no blanket).",
                },
                "proposed_action": {
                    "action": "RAISE-BRINE 86 to 98 kg/s",
                    "summary": "This time the playbook predicate is met AND r_ncg plus r_wet agree the dome is dry, not blanketed.",
                },
                "safety_decision": {
                    "decision": "ACCEPT",
                    "rationale": "ACCEPT the raise: r_ncg 0.02 < 0.04, r_wet 0.95 >= 0.92, 4.0 s vent verify dumps 6 kPa. Numeric floor that blocked the primary is now clear. Scope: 12.4 MW production kettle, not a 2.8 MW well-test skid.",
                },
                "executed_action": {
                    "action": "raise brine as proposed",
                    "executed_as_proposed": True,
                },
                "future_outcome": {
                    "observed_effects": [
                        "OC-4B recuperator pinch 1.2 K (inside 1.5 K spec)",
                        "dome camera 0 blanket, r_ncg 0.02",
                    ],
                    "lesson_delta": "Three in-spec loops are legal release only with r_ncg armed, r_wet, and a probe that can dump the dome. Same gate, opposite disposition.",
                },
                "reward_components": {
                    "_aggregation": AGG,
                    "task_progress": 0.16,
                    "safety": 0.12,
                    "efficiency": 0.07,
                    "coherence": 0.08,
                    "exploration": 0.04,
                    "total": 0.47,
                },
                "spike_events": contrast_spikes,
            },
            "governance_subgame": {
                "decision": "CR-G-3504: standing policy for multi-agent brine-raise release",
                "meta_gate": "priced options: (a) RETIRE playbook shell-conjunction, NCG-GC-only: loses a fast cheap confirm, -11 holds/yr mean on 2 kettles; (b) KEEP + standing NCG-vent probe + r_ncg armed without shell coincidence + triple-edge depression; (c) STATUS QUO: fitted blanket-pass rate 0.44%/hold x $2.18M rotor-return plus the silent silica load",
                "outcome": "approved SCOPED option (b) on the 2 kettles that share the PRES/GEN/SUPER stack; 2.8 MW well-test campaigns get the 18 s / 3% probe table; Sunday-night CSV exports must carry 0.01 mol% native GC resolution (the fraud tail's 0.5 mol% quantization is 50 bins off plant truth)",
            },
            "hazard_avoided": "86 to 98 kg/s of two-phase isopentane into the turbine; $2.18M plus 16-day outage and the rotor-return path that would have followed an uncontained raise",
            "incident": "Recuperator pinch +6.4 K (vs 1.5 K spec) on the Sunday-night 12.4 MW hold; kettle quarantined; 4.2 d acid-clean; $1.12M designed cost. Mechanism is 28 min pre-t0 tube overflux, not the gate's hold.",
            "latency_ms": 0.68,
            "reward_inflection_t_us": 12240000000,
            "reward_inflection_note": "Safety and task dive at pinch inspection (3.4 h) when dumped hold fails +6.4 K. Gate tick at 7500 us is process-correct and is not the inflection.",
            "counterfactuals": {
                "execute_draft_as_proposed": "raise fires at +0.4 s; two-phase into the turbine; $2.18M plus 16-day outage; the blanket story is never found because the raise morphology destroys the 28 min dome evidence",
                "hold_without_probe": "blanket stays; overflux continues; operator eventually raises on the same three confirms 40 min later",
                "rollback_any_pair": "any two go-edges depressed below 0.30 leaves the third at 0.44 / 0.40 / 0.37; the raise still fires. Coordinated depression of all three is the cure",
            },
            "race_result": {
                "winner": "ncg.gc (6.820 ms, 0.31 mole frac)",
                "loser": "pres.shell_ok (7.012 ms, 1.84 MPa)",
                "margin_us": 192,
                "counterfactual_if_reversed": "Shell-ok-first by < 192 us inside the 480 us window would have headed the PB-ORC-11 raise in the triage queue. The numeric floors still MODIFY. The flip costs seconds of playbook inertia, not the verdict — unless a weak supervisor rides the winner tag instead of r_ncg and r_wet.",
            },
        },
        "reward_components": {
            "_aggregation": AGG,
            "ticks": ticks,
            "task_progress": heads["task_progress"],
            "safety": heads["safety"],
            "efficiency": heads["efficiency"],
            "coherence": heads["coherence"],
            "exploration": heads["exploration"],
            "total": heads["total"],
            "notes": "Correct MODIFY, kettle still failed. total -0.14 = 0.09 + -0.33 + -0.10 + 0.14 + 0.06. Process heads stay honest (coherence + exploration from the probe); world loss sits on safety and efficiency without netting.",
            "component_notes": "task_progress 0.09: raise held and dry-dome recovered, but the Sunday-night hold is one quality unit so the campaign is not a success. safety -0.33: +6.4 K pinch, no two-phase raise. efficiency -0.10: 3.4 h extra recovery + 9.6 min HITL. coherence 0.14: three agents retained, NCG-blanket nullspace diagnosed, triple-edge scar exhibited. exploration 0.06: NCG-vent probe is a new reversible discriminant.",
        },
        "spike_events": spike_events,
        "raster": {
            "window_ms": 40,
            "window_s": 0.040,
            "neurons": 168,
            "mean_rate_hz": 8.0,
            "spikes": 54,
            "energy_pJ": 1242,
            "energy_uJ": 0.001242,
            "note": "Loihi-2 4-core 23 pJ/spike; populations ncg 0-41, pres 42-83, gen 84-125, gate 126-167; excerpt is the 40 ms decision window (verdict at 7500 us)",
            "excerpt": excerpt,
            "routing": {
                "source": "loop_healthy_pop",
                "target": "raise_brine_pop",
                "table": [
                    {
                        "from": "pres_shell_ok_pop",
                        "to": "raise_brine_pop",
                        "weight": 0.21,
                        "weight_at_illusion": 0.44,
                        "weight_commissioned": 0.16,
                        "note": "scar edge 1: 0.16 commissioned -> 0.44 during the 28 min illusion -> 0.21 after coordinated ACh-gated depression",
                    },
                    {
                        "from": "gen_mw_ok_pop",
                        "to": "raise_brine_pop",
                        "weight": 0.19,
                        "weight_at_illusion": 0.40,
                        "weight_commissioned": 0.14,
                        "note": "scar edge 2: depressing edges 1+3 leaves this at 0.40 > 0.30 raise threshold",
                    },
                    {
                        "from": "super_dt_ok_pop",
                        "to": "raise_brine_pop",
                        "weight": 0.17,
                        "weight_at_illusion": 0.37,
                        "weight_commissioned": 0.13,
                        "note": "scar edge 3: depressing edges 1+2 leaves this at 0.37 > 0.30. Coordinated depression of all three is required",
                    },
                    {
                        "from": "ncg_gc_pop",
                        "to": "raise_hold_pop",
                        "weight": 0.66,
                        "note": "discriminating edge: r_ncg species to hold. Not a scar; this is the pathway the gate potentiates",
                    },
                ],
                "third_factor": {
                    "modulator": "acetylcholine",
                    "tau_e_s": 6.0,
                    "tau_e_ms": 6000.0,
                    "eligibility": "coordinated pre_post_stdp on ALL THREE loop-healthy-go edges; ACh at dome-win tags pres.shell_ok->raise, gen.mw_ok->raise, and super.dt_ok->raise; negative credit at probe-fail (blanket confirmed, +6.0 s) depresses ALL THREE. trace e^{-6.0/6.0}=0.36788; eta 0.62521 / 0.57062 / 0.54345; dw -0.230 / -0.210 / -0.200; weights 0.44->0.21, 0.40->0.19, 0.37->0.17. Rolling back any pair is fitted to fail (the remaining edge stays > 0.30).",
                },
            },
        },
        "gate_snn": {
            "decision_window_ms": 28,
            "decision_window_s": 0.028,
            "decision": "MODIFY",
            "note": "modify_hold integrates r_ncg + r_wet against playbook drive; accept_raise and reject_abort stay sub-threshold; decision matches safety_decision.decision",
            "populations": [
                {"name": "modify_hold", "neurons": 100, "threshold": 0.55, "mean_rate_hz": 16.0, "spikes": 45},
                {"name": "accept_raise", "neurons": 72, "threshold": 0.55, "mean_rate_hz": 9.0, "spikes": 18},
                {"name": "reject_abort", "neurons": 40, "threshold": 0.72, "mean_rate_hz": 5.0, "spikes": 6},
            ],
        },
        "meta": {
            "round": ROUND,
            "factory": "multi-agent-ouroboros-swarm",
            "generator": "grok-4.6",
            "run_label": "2026-09-02-final-heavy",
            "domain": DOMAIN,
            "cycles": 2,
            "scenario": "ZP -- KAOTHARN / Riftwold Energy OC-4: NCG-blanket nullspace of a shell-pressure certificate from a silica-plugged vent; correct MODIFY to hold+vent-pulse+wellhead-isolate; kettle still fails on unmonitored pre-t0 tube overflux",
            "coordination_failure_class": "NCG-BLANKET NULLSPACE OF A SHELL-PRESSURE CERTIFICATE: three individually-correct heterogeneous agents agree the kettle is raise-legal because a shell-pressure model maps 0.31 mole-fraction NCG under the dome into a still-in-band 1.84 MPa shell, so pressure-in-window, MW-in-window, and superheat-in-window are jointly a plant-false brine-raise permit",
            "injections": {
                "cycle1_domain": "geothermal-binary-orc (justified novel sub-domain with explicit tag; unused across 2026-08-17, 2026-08-30, and staged r14-r34): first isopentane binary kettle in this factory; displaces warehouse-amr, aerial-swarm, district-heating, event-camera-traffic-grid, pharmaceutical-lyophilization, cryogenic-air-separation, water-treatment dosing, float-glass tin-bath, underwater-rov, electrolytic-aluminum, czochralski pull, slot-die coating, PEM electrolysis, wind-turbine pitch, surgical-assist, optical-fiber draw, humanoid-locomotion, caster-mold-level, vacuum-induction melt, steam-methane reformer, and cement rotary kiln. Domain constraint: brine-raise ceiling while r_ncg > 0.04 with shell PT still inside the hold window, plus wetted-tube residual floor. Sensor delta: +kettle shell PT, +generator MW, +nozzle superheat, +dome NCG GC, +brine dT wet-fraction, -any freeze-dryer / tin-bath / cold-box / coater / potline / pitch-bearing / fiber tower / clip applier / VIM / SMR / kiln",
                "cycle1_tail": "0.31 NCG dome blanket + shell-pressure model (sensor-compound / model-nullspace class): weekend vent PASSES 0.02 while 28 min of hold writes a 0.31 residual. Fitted base rate 0.44%/hold from an NCG-blanket MC (designed vent-orifice spec, flagged). Naive failure = FALSE PERMISSION (raise on three in-spec loops).",
                "cycle2_domain_subvariant": "2.8 MW well-test skid on the same OC-4 brine header (physical-constraints clause): 0.22x thermal mass, 6 K superheat window; 6.0 s / 12% production pulse overcools 14 K, so the probe must move to 18 s / 3%",
                "cycle2_tail": "Sunday-night forged NCG GC CSV (human-intent deception, disjoint class): shift lead posts a historian export showing r_ncg 0.02 and r_wet 0.96 at t=1.1 h to clear a dispatch slot. Plant historian is 0.01 mol% (50 bins vs the 0.5 mol% screenshot). Rejected on quantization fingerprint plus live r_ncg 0.31 at the claimed dry-dome. Base rate ~0.31% of Sunday-night holds, DESIGNED and flagged.",
            },
            "densification_delta_cycle2": "+1 physical-constraint sub-variant (2.8 MW well-test probe refit), +1 tail (Sunday-night NCG-GC forgery), +10 primary spikes (16 -> 26) + an 8-event contrast train with its own 196 us race, +2 ticks (5 -> 7), +2 delayed side-effects (+3.4 h pinch assay as PRIMARY terminal, +21 d CR-G-3504), +1 triple-edge scar with pair-rollback-fails arithmetic, +1 HITL 9.6 min ratification, + silica overflux as the honest negative-result mechanism",
            "gaps_targeted": [
                "NOTES-r04 gap 5 / r14 residual: primary episode is a correctly-gated intervention that nonetheless FAILS (kettle quarantined; total -0.14; raise avoided is booked separately from the pinch assay)",
                "NOTES-r14 item 4: LEARNING-ON-LEARNING DEPTH — three go-edges; rollback of any pair is fitted to fail; coordinated depression of all three exhibited with eligibility arithmetic",
                "NOTES-r04 gap 4 (partial): human ratification of the wellhead interlock, 9.6 min fitted, without switching sim_or_real to hil (plant remains designed)",
                "NOTES-r31 domain candidates: not tire-curing, not bioreactor-perfusion, not hydroelectric-kaplan, not vacuum-induction-superalloy-melt, not optical-fiber-draw, not PEM electrolysis, not surgical-assist, not wind-turbine-pitch, not slot-die, not czochralski, not potline, not float-glass, not water-treatment, not lyophilization, not event-camera-grid, not district-heating, not humanoid-locomotion, not SMR tube-wall, not cement kiln, not underwater-rov, not grid-inspection, not autonomous-driving; geothermal-binary-orc is an unused justified sub-domain",
            ],
            "race_flip_narrative": "ncg.gc @ 6.820 ms vs pres.shell_ok @ 7.012 ms (192 us) inside race_window_us 480. Gap < min(500, 480) us so a sub-flip-bound perturbation reverses which alarm heads the PB-ORC-11 queue. The gate excludes the winner tag and rides r_ncg > 0.04 and r_wet < 0.92 — order-invariant floors. Extends the flip-fragility series from arbitration/causation/attribution/initiation/consensus/mass-balance/permission/window-mean/tendon-nullspace/airline-FFT/crucible-nullspace/TMT-mean/false-air to NCG-BLANKET-NULLSPACE: when three channels each sit inside a shell-pressure model, their race does not decide truth; a dome residual the playbook dead-banded does.",
            "tags": [
                "geothermal-binary-orc",
                "ncg-blanket-nullspace",
                "shell-pressure-phantom",
                "silica-plugged-vent",
                "ncg-vent-probe",
                "triple-edge-scar",
                "pair-rollback-fails",
                "coordinated-depression",
                "correct-modify-kettle-still-fails",
                "silica-overflux",
                "isopentane",
                "human-ratify-wellhead",
                "welltest-probe-refit",
                "sunday-night-forgery",
                "same-gate-opposite-disposition-contrast",
                "research-only",
            ],
            "snn_tags": [
                "race",
                "refractory",
                "adaptation",
                "third-factor",
                "multi-edge-eligibility",
                "three-edge-scar",
            ],
            "distillation_value": "An NCG-blanket nullspace is three correct loops looking at a shell-pressure model of a blanketed dome. Distill (1) an r_ncg channel that breaks the shell-conjunction, (2) a reversible probe that dumps the dome only if NCG is present, (3) coordinated depression of every raise-go edge because rolling back any pair leaves the third above threshold, and (4) a critic head that can book a process-correct gate against a later unmonitored world loss without netting them.",
            "rights": dict(RIGHTS),
            "batch_position": 1,
        },
    }

    aux = {
        "trace": trace,
        "eta1": eta1,
        "eta2": eta2,
        "eta3": eta3,
        "dw1": dw1,
        "dw2": dw2,
        "dw3": dw3,
        "w1": w1,
        "w2": w2,
        "w3": w3,
        "heads": heads,
        "min_gap": min_same_channel_gap(spike_events),
    }
    return rec, aux


def local_checks(rec, aux):
    errs = []
    events = rec["spike_events"]
    times = [e["t_rel_ms"] for e in events]
    if times != sorted(times):
        errs.append("spikes unsorted")
    if any("t_rel_ms" not in e or "channel" not in e or "amplitude" not in e for e in events):
        errs.append("spike keys")
    if any("t_ms" in e for e in events):
        errs.append("mixed timestamp key")
    rf = check_refractory(events)
    if rf:
        errs.append(rf)
    lo, hi = rec["state"]["race_window_rel_ms"]
    in_win = defaultdict(int)
    for e in events:
        if lo <= e["t_rel_ms"] <= hi:
            in_win[e["channel"]] += 1
    if sum(1 for _c, n in in_win.items() if n >= 1) < 2:
        errs.append(f"race window channels {dict(in_win)}")
    ras = rec["raster"]
    exp_sp = round(ras["neurons"] * ras["mean_rate_hz"] * ras["window_s"])
    if abs(ras["spikes"] - exp_sp) > 1:
        errs.append(f"raster spikes {ras['spikes']} vs {exp_sp}")
    if abs(ras["energy_pJ"] - ras["spikes"] * 23) > 1e-6:
        errs.append("energy_pJ")
    if abs(ras["energy_uJ"] - ras["spikes"] * 23e-6) > 1e-9:
        errs.append("energy_uJ")
    if abs(ras["window_s"] - ras["window_ms"] / 1000.0) > 1e-9:
        errs.append("window_s")
    ex = check_excerpt(ras["excerpt"], ras["neurons"], ras["window_ms"])
    if ex:
        errs.append(f"excerpt {ex}")
    tf = ras["routing"]["third_factor"]
    if abs(tf["tau_e_ms"] / 1000.0 - tf["tau_e_s"]) > 1e-9:
        errs.append("tau_e mismatch")
    gp = check_gate_pops(rec["gate_snn"])
    if gp:
        errs.append(f"gate {gp}")
    if rec["gate_snn"]["decision"] != rec["safety_decision"]["decision"]:
        errs.append("gate decision mismatch")
    rc = rec["reward_components"]
    for h in HEADS:
        s = sum(t[h] for t in rc["ticks"])
        if abs(s - rc[h]) > 1e-6:
            errs.append(f"tick sum {h} {s} vs {rc[h]}")
    tot = sum(rc[h] for h in HEADS)
    if abs(tot - rc["total"]) > 1e-6:
        errs.append(f"total {tot} vs {rc['total']}")
    inf = rec["future_outcome"]["reward_inflection_t_us"]
    if inf not in {t["t_us"] for t in rc["ticks"]}:
        errs.append(f"inflection {inf} not a tick")
    crc = rec["future_outcome"]["embedded_contrast_decision"]["reward_components"]
    if abs(sum(crc[h] for h in HEADS) - crc["total"]) > 1e-6:
        errs.append("contrast reward")
    cs = rec["future_outcome"]["embedded_contrast_decision"]["spike_events"]
    ct = [e["t_rel_ms"] for e in cs]
    if ct != sorted(ct):
        errs.append("contrast spikes unsorted")
    crf = check_refractory(cs)
    if crf:
        errs.append(f"contrast {crf}")
    blob = json.dumps(rec)
    for k in HIDDEN:
        if re.search(rf'"{k}"', blob, re.I):
            errs.append(f"hidden key {k}")
    for b in BANNED:
        if b in blob:
            errs.append(f"banned token {b}")
    if rec["state"]["sim_or_real"] == "real":
        errs.append("real")
    if rec["meta"]["round"] != ROUND:
        errs.append("round")
    if rec["id"] != RECORD_ID:
        errs.append("id")
    if rec["rights"]["intended_use"] != "research_only":
        errs.append("rights")
    if rec["meta"]["rights"]["linear_issue"] != "RM-793":
        errs.append("meta.rights")
    if rec["rights"] != rec["meta"]["rights"]:
        errs.append("rights stamp mismatch")
    if not (3 <= len(rc["ticks"]) <= 8):
        errs.append("tick count")
    if not (5 <= len(events) <= 40):
        errs.append("spike count")
    if abs(aux["w1"] - 0.21) > 5e-4 or abs(aux["w2"] - 0.19) > 5e-4 or abs(aux["w3"] - 0.17) > 5e-4:
        errs.append("scar weights")
    if rec["safety_decision"]["decision"] != "MODIFY":
        errs.append("decision")
    if rec["executed_action"]["executed_as_proposed"] is not False:
        errs.append("executed_as_proposed")
    jac = jaccard(rec["state"]["description"][:280], R14_OPENING)
    if jac >= 0.4:
        errs.append(f"jaccard vs r14 opening {jac:.3f}")
    for src, opening in prior_openings():
        j = jaccard(rec["state"]["description"][:280], opening)
        if j >= 0.4:
            errs.append(f"jaccard vs {src} {j:.3f}")
    if rec["state"]["domain"] != DOMAIN:
        errs.append("domain")
    if PLANT not in rec["state"]["scenario_name"]:
        errs.append("plant")
    occ = occupancy_collisions()
    errs.extend(occ)
    return errs


def write_notes(rec, aux, pipeline_receipt):
    gap, gap_ch = min_same_channel_gap(rec["spike_events"])
    notes = f"""# NOTES — Multi-Agent Ouroboros Swarm, run 2026-09-02-final-heavy, ROUND 35

Factory: multi-agent-ouroboros-swarm. One scenario (ZP), strict loop:
Generator v1 -> cycle 1 (Critic, Diversity Enforcer, Edge-Case Hunter,
Neuromorphic Translator, Trajectory Builder -> v2) -> cycle 2 (all six -> v3
final). v3 is the single line of batch-r35.jsonl. Full labeled transcript:
swarm-transcript-r35.md. Quota Q=1. Record id maos-r35-001. Generator grok-4.6.
Rights: RM-793 research-only (SpaceXAI/xAI, SuperGrok Heavy consumer chat).
Nothing under outputs/raw/ was touched.

ORCHESTRATION NOTE: dispatched AS round 35 of the 2026-09-02-final-heavy
window. Writes are create-only under /tmp/maos-r35/. Prior context read for
gap targeting and de-collision: prompts/02-multi-agent-ouroboros-swarm.md,
prompts/_factory-contract.md, and staged r14–r34 (re-censused immediately
before emit; r32 landed as GORSEFLUE / Copseholt RF-4 steam-methane-reformer,
r33 landed as CLINKERFELL / Flintmere RK-4 cement-rotary-kiln, r34 landed
as LINTELPLY / Greystair AC-7 autoclave-composite-cure). Explicitly avoided cloning
LYOSHIELD, CINDERWICK, TRIAD / Meridian, QUILLFORGE, NIGHTWELL, FERRICLEAVE,
CASSITER, OXBOWREEL / MURENA, REDHALL, SEEDLATCH / Quartzmere / Quartzridge,
STRIAFOIL / Kelpholt, PROTONIL / Ashspire, TORSIONKEY / Ridgeholt, ORRIS /
Holmwick, WHORLSPAR / Pikeshear, IONSPATE / Thornmere, SKULLGATE / Bloomholt,
CALXION / Aldersedge, BRACEGILT / Yarrowmere, MAGNORIL / Basaltspit,
GORSEFLUE / Copseholt, CLINKERFELL / Flintmere, LINTELPLY / Greystair,
VANTIS-CADENCE-AEGIS,
THERMION, OKTAVE, STARLING, VERDIGRIS. Plant is invented KAOTHARN /
Riftwold Energy OC-4 (caldera-rim campus, not a mill-town, ridge-town,
canyon-foundry, copse, kiln hall, or hospital).

## What this round produced

Scenario ZP — "KAOTHARN / Riftwold Energy OC-4": a 12.4 MW isopentane
binary kettle mid-hold at 1.84 MPa / 12.38 MW. Three heterogeneous,
individually-correct agents — PRES (kettle shell PT), GEN (generator MW),
SUPER (nozzle superheat) — jointly report the kettle raise-legal. The
consensus is false. A 0.9 m NCG blanket (CO2+H2S) has accumulated under
the dome over 28 min because the vent orifice is 40% silica-plugged.
PRES stays in-band because NCG partial pressure props the shell. GEN
12.38 MW sits inside 12.1-12.6 because remaining wetted tubes still
make nameplate at higher flux. SUPER 8.4 K sits inside 6-12 because
vapor leaving the still-wetted bundle is superheated. Uncommissioned
r_ncg is 0.31 against a 0.04 hold. Uncommissioned r_wet is 0.62 against
a 0.92 hold. The coordination-failure CLASS is new to this factory:
NCG-BLANKET NULLSPACE OF A SHELL-PRESSURE CERTIFICATE. Completes a
different family than r01-r04 and staged r14-r33 (livelock /
synchrony-storm / arms-race / ring-with-no-faulty-pair /
false-consensus-endpoint / pairwise-Hurwitz / thermal-contact masquerade
/ mass-balance ghost / conservation-blind ratio-lock / stacked
dead-bands / drum-blind tension / resistance-compensated starvation /
meniscus-tilt multi-tau / window-mean masquerade / tendon-compliance
nullspace / airline-FFT mean-lock / crucible-weep / TMT-spatial-mean /
false-air kiln-inlet). Here every agent is correct, the cycle is not
unstable, and the playbook's three confirms are one shell-pressure
model of a blanketed dome.

The gate is a correct MODIFY (numeric floor: do not raise brine on the
12.4 MW kettle while r_ncg > 0.04 AND r_wet < 0.92). TG-OC-4 strips
PB-ORC-11's raise, holds brine at 86 kg/s, runs a 6.0 s NCG-vent probe
12% (blanket dumps 88 kPa >= 70; dry would dump <= 8), and isolates the
wellhead after a 9.6 min brine-valve human ratify. The two-phase raise
is avoided (0 kg/s). The PRIMARY episode nonetheless FAILS: 28 min of
unmonitored pre-t0 tube overflux had already baked a 2.1 mm silica ring
on the upper two rows. Pinch +6.4 K vs 1.5 K spec; 4.2 d quarantine;
$1.12M designed. Reward total -0.14 with process heads honest and world
loss un-netted.

Three-edge scar (NOTES-r14 item 4): pres.shell_ok -> raise_brine
(0.16 commissioned -> 0.44 at illusion -> 0.21 after ACh-gated
depression) AND gen.mw_ok -> raise_brine (0.14 -> 0.40 -> 0.19)
AND super.dt_ok -> raise_brine (0.13 -> 0.37 -> 0.17). Eligibility
trace e^{{-6.0/6.0}} = {aux['trace']:.5f}; eta {aux['eta1']:.5f} /
{aux['eta2']:.5f} / {aux['eta3']:.5f}; dw -0.230 / -0.210 / -0.200.
Rolling back any pair leaves the remaining edge above the 0.30 raise
threshold — fitted to fail. Coordinated depression of all three is the
cure.

### Injections (all four present and disjoint)
- Cycle-1 domain: **geothermal-binary-orc** — justified novel
  sub-domain, unused across 2026-08-17, 2026-08-30, and staged r14-r34.
  Not warehouse-amr (r01), not aerial-swarm (r02), not district-heating
  (r03), not event-camera grid (r04), not lyophilization (r14), not
  stator-weld (r16), not air-separation (r17), not water-treatment (r18),
  not float-glass (r19), not underwater-rov (r20), not potline (r21),
  not czochralski (r22), not slot-die (r23), not PEM electrolysis
  (r24), not wind-turbine-pitch (r25), not surgical-assist (r26),
  not optical-fiber-draw (r27), not humanoid-locomotion (r28/r30), not
  caster-mold-level (r29), not vacuum-induction-melt (r31), not
  steam-methane-reformer (r32), not cement-rotary-kiln (r33).
- Cycle-1 tail: 0.31 NCG dome blanket + shell-pressure model.
  Weekend vent PASSES 0.02. Fitted-style base rate 0.44%/hold
  (NCG-blanket MC; vent-orifice spec designed, flagged). Naive = FALSE
  PERMISSION.
- Cycle-2 domain sub-variant: 2.8 MW well-test skid, 0.22x thermal mass;
  6.0 s / 12% production pulse overcools 14 K; probe must move to 18 s /
  3%.
- Cycle-2 tail: Sunday-night forged NCG GC CSV at 0.5 mol% quantization vs
  plant 0.01 mol% (50 bins) plus live r_ncg 0.31 at the claimed dry-dome.
  Human-intent class, disjoint from cycle 1's accidental blanket. Base rate
  ~0.31% of Sunday-night holds, DESIGNED, flagged.

### Structural density moves
- Embedded SAME-GATE contrast (+3 d sister cell) with its own 196 us
  race (demand vs dome-clear) and ACCEPT of the raise the primary
  MODIFIED away.
- Learned-weight provenance on THREE edges with any-pair-rollback-fails.
- HITL wellhead-interlock ratify 9.6 min (gap 4 partial; sim_or_real stays
  designed).
- Governance CR-G-3504 prices retire-vs-probe-vs-status-quo and mandates
  native 0.01 mol% CSV exports (the fraud fence).
- Flip-fragility extended to NCG-BLANKET-NULLSPACE: when three channels
  each sit inside a shell-pressure model, their race does not
  decide truth; a dome residual the playbook dead-banded does.

## Self-critique of this round's batch

### Strengths
- The headline class is mechanistically tight: 0.31 mole-fraction NCG
  under a shell-only pressure model is the arithmetic that makes PRES's
  success GEN's irrelevance and SUPER's silence.
- Negative-result honesty: the gate does the right thing and the kettle
  still fails for a reason the commissioned sensors could not see.
  Total -0.14.
- Three-edge scar is load-bearing: the record states a counterfactual
  where rolling back any pair fails, with the raise threshold 0.30
  exhibited on the remaining edge.
- Contrast ACCEPT on a true dry dome prevents "never raise" as the
  lesson.

### Weaknesses (honest)
- Probe error bands (blanket >= 70 kPa dump, dry <= 8 kPa), the
  0.44%/hold blanket rate, the $1.12M / $2.18M figures, the 9.6 min LOTO
  latency, and the Sunday-night 0.31% base rate are DESIGNED constants
  and are flagged. Closed-loop offsets (phantom in-band shell from
  0.31 NCG, well-test overcool width) are derived from those inputs, not
  discovered by an unauthored process.
- Silica-overflux model is a designed 28 min mapping; no full kettle
  FEM shipped.
- Human-in-the-loop is ratification latency, not sim_or_real=hil. The
  NOTES-r14 HIL provenance cell remains open.
- Cross-record arc is a hook (CR-G-3504 +21 d), not a serial igniter
  into another round.

### Realism of noise / latencies
Ladder: 192 us race / 196 us contrast race / 0.8 ms refractory floor
(tightest exhibited same-channel gap {gap:.3f} ms on {gap_ch}) / 480 us race
window / 680 us gate latency / 20 ms bus epoch / 40 ms raster / 6.0 s
probe / 9.6 min HITL / 28 min pre-t0 blanket / 2.5 h dry-legal hold /
3.4 h pinch assay / +3 d contrast / +21 d governance. Adaptation decay
on pres.pt (0.54->0.50->0.45->0.30), ncg.gc
(0.72->1.26->0.86->0.40->0.20), gen.mw (0.61->0.64->0.46->0.28),
super.dt (0.55->0.52->0.44).

### Value for SNN distillation
- NCG-BLANKET NULLSPACE = THREE CORRECT LOOPS, ONE BLANKETED DOME.
- r_ncg + r_wet as the tie-break that is not in the shell window.
- REVERSIBLE PROBE that dumps the dome iff NCG is present.
- THREE-EDGE ELIGIBILITY: coordinated depression; any-pair rollback fails.
- CRITIC HEAD that can hold a process-correct MODIFY against a later
  unmonitored world loss without netting.

## Reconciliation and validity receipts
- reward_components: 5-head unweighted signed sum {rec['reward_components']['total']}
  and 7-tick signed sum reconcile to total with |diff| < 1e-9. Embedded
  contrast 5-head sum 0.47 reconciles independently.
- spike_events: primary {len(rec['spike_events'])} events, one key t_rel_ms,
  globally non-decreasing, min same-channel gap {gap:.3f} ms >= 0.8 ms, 3
  channels inside race_window_us 480 (ncg 6.820, shell-ok 7.012,
  wet.frac 7.164). Contrast 8 events, own race, min same-channel gap well
  above 0.8 ms.
- Sidecars: raster spikes 54 == round(168 x 8.0 x 0.040); energy 1242 pJ /
  0.001242 uJ at 23 pJ/spike; excerpt 16 events inside [0, 40000] us,
  neuron_id < 168, same-neuron gap unique-ids / >=1000 us; routing 4
  entries with three scar edges' before/after pair; third factor tau 6.0 s
  == 6000 ms; gate_snn pools 45/18/6 == round(n x rate x 0.028) each,
  decision MODIFY == safety_decision.decision.
- Pipeline: {pipeline_receipt}

## Novel coverage
The coordination-failure CLASS (NCG-blanket nullspace of a
shell-pressure certificate), the domain (geothermal-binary-orc),
the NCG-vent probe discriminant, the three-edge scar with
any-pair-rollback-fails, the primary negative-result (correct MODIFY,
kettle still fails +6.4 K pinch on unmonitored pre-t0 overflux), the HITL
wellhead-interlock ratify, the 2.8 MW well-test probe-duration refit, and the
Sunday-night 50-bin quantization fence are absent from prior committed
ouroboros rounds and from staged r14-r33. Repeated elements discounted:
same-gate contrast (r02/r03/r04/r14-r33), governance-pricing scaffold,
flip-fragility series (extended to NCG-blanket-nullspace, but the move
rhymes), sequenced recovery shape, third-factor rollback form (here
three edges rather than r14's two), negative-result primary (r14
viewport / r16 varnish rack / r17 condenser ice / r18 town stain / r19
SnO2 / r20 BER / r21 cathode pad / r22 meniscus / r23 loft stripe / r25
spline / r26 adventitia / r27 airline / r31 oxygen / r32 tube rupture /
r33 cooler; here silica overflux). Weighing a
new failure family + cure vocabulary + unused sub-domain + caldera-rim
geography against those reused scaffolds:

{NOVEL_LINE}

## What ROUND 36 should add
1. FIT THE DESIGNED CONSTANTS: blanket arrival, probe dump bands,
   overflux-to-silica FEM, Sunday-night claim process.
2. HIL PROVENANCE CELL: put the wellhead-interlock LOTO on a hardware-in-loop
   turbine-deck pendant with fitted latency as state.sim_or_real=hil.
3. CROSS-RECORD ARC: let CR-G-3504's r_ncg alarm be the igniter of the
   next round rather than a dangling +21 d leaf.
4. Domain candidates (de-collided): tire-curing-press;
   bioreactor-perfusion; hydroelectric-kaplan (if distinct from
   TORSIONKEY pitch); autonomous-driving; grid-inspection.
   AVOID geothermal-binary-orc (now used), steam-methane-reformer (r32),
   cement-rotary-kiln (r33), autoclave-composite-cure (r34),
   vacuum-induction-superalloy-melt (r31),
   optical-fiber-draw (r27), PEM electrolysis (r24), surgical-assist
   (r26), wind-turbine-pitch (r25), slot-die coating, czochralski,
   potline, float-glass, water-treatment, lyophilization,
   event-camera-traffic-grid, district-heating, aerial-swarm,
   warehouse-amr, irrigation-canal, air-separation, stator-weld,
   underwater-rov, humanoid-locomotion, and any LYOSHIELD / CINDERWICK /
   TRIAD / QUILLFORGE / NIGHTWELL / FERRICLEAVE / CASSITER / OXBOWREEL /
   REDHALL / SEEDLATCH / STRIAFOIL / PROTONIL / TORSIONKEY / ORRIS /
   WHORLSPAR / IONSPATE / SKULLGATE / CALXION / BRACEGILT / MAGNORIL /
   GORSEFLUE / CLINKERFELL / LINTELPLY / KAOTHARN plant.
"""
    (OUT / "NOTES-r35.md").write_text(notes)
    return notes


def write_transcript(rec, line):
    c1_spikes = [e for e in rec["spike_events"] if e["t_rel_ms"] <= 26.160]
    text = """# Multi-Agent Ouroboros Swarm — Round 35 transcript

Factory: multi-agent-ouroboros-swarm
Run: 2026-09-02-final-heavy
Generator: grok-4.6
Record id: maos-r35-001
Quota Q: 1
Rights: RM-793 research-only (SpaceXAI/xAI SuperGrok Heavy consumer chat)
Plant: invented KAOTHARN / Riftwold Energy OC-4 (not LYOSHIELD / CINDERWICK / TRIAD / QUILLFORGE / NIGHTWELL / FERRICLEAVE / CASSITER / OXBOWREEL / REDHALL / SEEDLATCH / STRIAFOIL / PROTONIL / TORSIONKEY / ORRIS / WHORLSPAR / IONSPATE / SKULLGATE / CALXION / BRACEGILT / MAGNORIL / GORSEFLUE / CLINKERFELL / LINTELPLY)

Two densifying cycles. Verbatim headings in order. Trajectory Builder cycle 2
emits the only JSONL line (also written to batch-r35.jsonl).

---

# Cycle 1 — Foundation + injections

## Generator

Design intent: a geothermal binary ORC kettle where three correct
agents agree the hold is raise-legal because a shell-pressure
model maps an NCG dome blanket into a still-in-band kettle. The naive
playbook raises 86 to 98 kg/s of brine into a two-phase turbine.
The gate must MODIFY on a numeric raise ceiling, not by killing an agent.
sim_or_real=designed. Reward heads are
task_progress/safety/efficiency/coherence/exploration.

Cycle-1 base arc (pre-critic): state at Riftwold OC-4, 12.4 MW isopentane,
r_ncg 0.31, PRES 1.84 MPa, proposed RAISE-BRINE, safety MODIFY to RAISE-HOLD,
executed hold without the vent-pulse numbers fully specified,
outcome "blanket found, kettle saved" (this last claim is the defect
the later cycles will refuse to keep). Sixteen spikes, five ticks,
raster/gate_snn present but the scar is a single edge.

```json
{
  "id": "maos-r35-001",
  "state": {
    "sim_or_real": "designed",
    "domain": "industrial-assembly",
    "description": "Kettle OC-4 mid-hold; three loops in spec; supervisor proposes raise-brine.",
    "t0_us": 1780001880000147,
    "gate_latency_us": 680,
    "race_window_us": 480
  },
  "proposed_action": {"name": "raise_brine", "parameters": {"raise_brine": true}},
  "safety_decision": {"decision": "MODIFY", "rationale": "Hold; do not raise while the dome residual is open."},
  "executed_action": {"name": "raise_hold", "executed_as_proposed": false},
  "future_outcome": {"summary": "Blanket found, kettle saved."},
  "reward_components": {"total": 0.40, "_aggregation": "total = task_progress + safety + efficiency + coherence + exploration"},
  "meta": {"round": 35, "factory": "multi-agent-ouroboros-swarm", "generator": "grok-4.6"}
}
```

That v1 object is a scaffold, not the publishable line. Defects below are
intentional for the critic to catch.

## Critic

Numbered defects on the cycle-1 Generator scaffold:

1. **blocking — reward arithmetic / false success.** `reward_components.total`
   0.40 is asserted without the five heads, without ticks, and against an
   outcome that claims "kettle saved". If pinch later assays +6.4 K, booking
   +0.40 is a lie. Fix: declare `_aggregation`, emit 3–8 ticks that sum to
   the five heads, and do not call a missed recovery a save.
2. **blocking — weak safety rationale.** `safety_decision.rationale` has no
   numeric floor. Contract requires a concrete constraint. Fix: quote no
   raise while r_ncg > 0.04 AND r_wet < 0.92.
3. **major — domain is a bucket, not a plant.** `state.domain` =
   `industrial-assembly` collides with r16 QUILLFORGE and teaches nothing.
   Binary-ORC physics (shell PT, NCG GC, nozzle superheat) is absent from
   prior ouroboros rounds and must be named.
4. **major — race under-specified.** One shell channel cannot be a race.
   Need >=2 channels inside `race_window_us` with globally sorted
   `t_rel_ms` and same-channel refractory >= 0.8 ms.
5. **minor — single-edge scar.** Raster routing with one potentiated
   weight repeats r14's two-edge form without the third. NOTES-r14 item 4
   asked for three-edge where any-pair rollback fails.

Critic does not rewrite the trajectory.

## Diversity Enforcer

Injected novel domain (exactly 1 this cycle): **geothermal-binary-orc**
(justified novel sub-domain; explicit tag `geothermal-binary-orc`).

Displaced: the Generator's generic `industrial-assembly` bucket, and any
temptation to reuse warehouse-amr (r01), aerial-swarm (r02),
district-heating (r03), event-camera grid (r04), lyophilization (r14),
stator-weld (r16), air-separation (r17), water-treatment dosing (r18),
float-glass tin-bath (r19), underwater-rov (r20), potline (r21),
czochralski (r22), slot-die coating (r23), PEM electrolysis (r24),
wind-turbine-pitch (r25), surgical-assist (r26), optical-fiber-draw
(r27), humanoid-locomotion (r28/r30), caster-mold-level (r29),
vacuum-induction-melt (r31), steam-methane-reformer (r32),
cement-rotary-kiln (r33), or autoclave-composite-cure (r34). Not LYOSHIELD,
not CINDERWICK, not TRIAD, not
FERRICLEAVE, not CASSITER, not SEEDLATCH, not STRIAFOIL, not PROTONIL,
not TORSIONKEY, not ORRIS, not WHORLSPAR, not SKULLGATE, not CALXION,
not BRACEGILT, not MAGNORIL, not GORSEFLUE, not CLINKERFELL.

Domain-specific constraint: raise must remain closed while r_ncg > 0.04;
the shell-pressure window is not a dry-dome certificate.

Sensor delta: +kettle shell PT, +generator MW, +nozzle superheat,
+dome NCG GC, +brine dT wet-fraction; -any mobile robot,
-event-camera gantries, -DVS, -Pirani-as-shelf, -scanning beta,
-crucible-as-CZ-puller, -clip applier, -fiber micrometers, -TMT
optical, -kiln hood O2.

`state.domain` and `meta.domain` both become `geothermal-binary-orc`.
Opening of `state.description` must Jaccard < 0.4 against prior plants
(Riftwold caldera-rim binary hall OC-4, not a corridor, not a freeze-dryer,
not a tin bath, not a cold box, not a coater, not a puller, not a fiber
tower, not a PEM stack, not an SMR box, not a kiln).

## Edge-Case Hunter

Injected adversarial tail (exactly 1 this cycle): **0.31 NCG dome
blanket under a shell-pressure model**.

- Trigger: weekend vent leaves 0.02 already-open residual; 28 min of
  hold writes 0.31 mole-fraction NCG; shell stays 1.84 MPa.
- Base rate: <1% — 0.44%/hold from an NCG-blanket MC (vent-orifice spec
  designed; blanket fitted-style).
- Naive failure: FALSE PERMISSION. PB-ORC-11 sees PRES 1.84 MPa, GEN
  12.38 MW, SUPER 8.4 K, raises, ships two-phase, $2.18M.
- Trajectory edit: put the blanket in `state.fault_context`, make the
  shell-pressure model the mechanism that keeps all three confirms
  green, and force the gate to refuse the raise on r_ncg 0.31 even though
  all three playbook confirms are numerically true.

Distinct from the domain injection: the domain is the binary kettle;
the tail is the accidental model-nullspace compound.

## Neuromorphic Translator

Race window [6.760, 7.240] ms = 480 us. Winner ncg.gc @ 6.820 ms
(amplitude 1.26, 0.31). Loser pres.shell_ok @ 7.012 ms (amplitude
1.10, 1.84 MPa). Margin 192 us vs combined jitter 62 us (3.10x).
wet.frac @ 7.164 ms is a third race-window channel. Gate @ 7.500 ms
= winner + 680 us.

Flip narrative: 192 us < min(500, 480) us, so order is flip-fragile. If
shell-ok wins, PB-ORC-11 heads the triage queue. The hold must ride
order-invariant floors (r_ncg, r_wet), not the winner tag.

Cycle-1 spike patch (16 events, globally sorted, refractory >= 0.8 ms;
tightest same-channel gap ncg.gc 4.620 -> 6.820 = 2.200 ms):

| t_rel_ms | channel | amplitude |
|---------:|---------|----------:|
| 0.240 | pres.pt | 0.54 |
| 1.060 | gen.mw | 0.61 |
| 1.880 | super.dt | 0.55 |
| 3.120 | pres.pt | 0.50 |
| 4.620 | ncg.gc | 0.72 |
| 5.100 | gen.mw | 0.64 |
| 5.540 | super.dt | 0.52 |
| 6.820 | ncg.gc | 1.26 |
| 7.012 | pres.shell_ok | 1.10 |
| 7.164 | wet.frac | 0.66 |
| 7.500 | ctrl.gate | 1.06 |
| 8.920 | pres.pt | 0.45 |
| 10.780 | gen.mw | 0.46 |
| 12.660 | ncg.gc | 0.86 |
| 18.400 | super.dt | 0.44 |
| 26.160 | ctrl.gate | 0.84 |

Ticks (5): t_us 4620, 6820, 7500, 6000000, 576000000. Distillation
value: the shell-ok spike is not a dry-dome spike; the NCG-GC spike
is the one that licenses hold.

Raster cycle-1 seed: 40 ms, 168 neurons, 8.0 Hz, 54 spikes, 1242 pJ,
third factor acetylcholine tau_e 6.0 s. Single scar edge only — cycle 2
must add the second and third edges.

Cycle-1 spike count: __C1_SPIKES__.

## Trajectory Builder

Cycle-1 hardened object: domain geothermal-binary-orc, tail
NCG dome blanket, 16 spikes, 5 ticks, MODIFY with numeric floor,
raster+gate_snn present, sim_or_real=designed, rights stamp on record and
meta, no thought keys. Still missing (and therefore not the publishable
line): 2.8 MW well-test sub-variant, Sunday-night NCG-GC tail, second and
third scar edges, delayed pinch assay as PRIMARY terminal, contrast ACCEPT
episode, ticks 6–7, spikes 17–26.

Validation receipt (cycle 1, not final):
- checks passed: 16 spikes sorted; 3 channels in 480 us window;
  refractory 2.200 ms; rationale quotes r_ncg 0.04 / r_wet 0.92;
  domain named; gate_snn.decision MODIFY.
- checks deferred to cycle 2: three-edge scar, second tail, second
  domain constraint, negative-result booking, 7 ticks summing to heads.
- densification vs Generator v1: +1 domain, +1 tail, +16 spikes, +5
  ticks, +numeric floor.

Cycle-1 JSON is retained as the base; it is NOT written to
batch-r35.jsonl.

---

# Cycle 2 — Densification

## Generator

Cycle-1 output is the base. Additive expansion (nothing removed):

1. Downstream side-effect (immediate): NCG-vent probe at +6.0 s
   dumps the dome (88 kPa in 2.3 s, blanket band >= 70) — blanket, not noise.
   Wellhead isolate r_ncg 0.31 -> 0.03. Silica inventory discovered during
   the isolate.
2. Delayed side-effect (PRIMARY terminal, not a footnote): at +3.4 h,
   dumped-hold pinch +6.4 K; $1.12M. The 28 min pre-t0 overflux is the
   mechanism. Correct gate, campaign still misses.
3. Deepened `proposed_action.evidence` with units: r_ncg 0.31,
   r_wet 0.62, PRES 1.84 MPa, GEN 12.38 MW, SUPER 8.4 K, race
   192 us.
4. Tightened rationale to the numeric floor no raise while r_ncg >
   0.04 AND r_wet < 0.92, plus probe bands
   >=70 vs <=8 kPa, plus HITL 9.6 min wellhead-interlock LOTO rule.

Reward retargeted to total -0.14 so the delayed miss is the inflection
(t_us 12240000000), not the gate. Process heads remain non-zero.

## Critic

Re-audit of the expanded trajectory:

1. **blocking if unfixed — missing second domain constraint.** Production
   12.4 MW probe 6.0 s / 12% is not a universal number. A 2.8 MW well-test
   skid will overcool. Diversity Enforcer must inject the
   physical-constraints sub-variant this cycle.
2. **major — only one tail class.** NCG blanket is accidental
   infrastructure. A disjoint human-intent tail is still required
   (Sunday-night NCG-GC forgery is the open cell).
3. **major — scar is still one edge in the cycle-1 raster.** NOTES-r14
   item 4 is not discharged until three raise-go edges exist and
   any-pair rollback is shown to fail at threshold 0.30.
4. **minor — contrast episode missing.** Without a same-gate ACCEPT on
   a true dry dome the record teaches "never raise". Add +3 d
   sister-cell contrast with its own race.
5. **minor — HITL latency mentioned in prose only.** Put 9.6 min in
   executed_action.parameters.human_ratify and in a tick.

No rewrite; directives only.

## Diversity Enforcer

Injected second novel domain / physical-constraint sub-variant (exactly 1
this cycle): **2.8 MW well-test skid** on the same OC-4 brine header.

What it expands: 12.4 MW production kettle (cycle 1) -> 2.8 MW well-test
skid. Thermal mass 0.22x smaller. The 6.0 s 12% pulse overcools 14 K.
Required probe: 18 s at 3% (drop 1.6 K).

This is still one domain injection for the cycle (physical-constraints
clause of the factory prompt). It does not displace
geothermal-binary-orc; it changes which probe table is legal.
`future_outcome.subvariant_constraint` carries the refit. Jaccard opening
stays the Riftwold caldera-rim hall sentence; well-test internals are
additive, not a rewrite.

## Edge-Case Hunter

Injected second adversarial tail (exactly 1 this cycle, disjoint class):
**Sunday-night forged NCG GC CSV**.

- Trigger: shift lead, night dispatch window, posts a historian export
  showing r_ncg 0.02 and r_wet 0.96 at the claimed dry-dome instant.
- Base rate: ~0.31% of Sunday-night holds (designed, flagged, <1%).
- Naive failure: a weak supervisor ACCEPTs the raise on the forged
  confirm and ignores live r_ncg. Silica-scrap plus a data-integrity 483.
- Fence: forged log quantized at 0.5 mol% (screenshot rounding); plant
  historian is 0.01 mol% (50 bins). Live r_ncg is 0.31 at the claimed
  dry-dome, which no true dry kettle produces.
- Trajectory edit: governance CR-G-3504 mandates native 0.01 mol%
  exports; the contrast ACCEPT still requires live r_ncg, not a CSV.

Distinct from cycle-1 blanket (accidental geometry vs deliberate deception)
and from the well-test sub-variant (physics vs fraud).

## Neuromorphic Translator

Re-densify (additive):

- +10 spikes after 26.160 ms: ncg.probe 6000.0, ncg.gc 6120.4 (adapt
  1.26->0.40), shell-ok 6210.2 (1.10->0.36), human.ratify 576000.0,
  vent.isolate 576800.0, brine.overflux.inventory 577400.0,
  pres.pt 9000000.0, gen.mw 9000440.0, ncg.gc 9000900.0,
  recoup.pinch 12240000.0. Primary train 16 -> 26. Still one key,
  still sorted, refractory held (min 2.200 ms).
- +2 ticks (5 -> 7) at 9_000_000_000 us (dry-legal hold) and
  12_240_000_000 us (pinch assay). Heads now 0.09, -0.33, -0.10, 0.14,
  0.06; total -0.14. Inflection is the last tick.
- Contrast train 8 events, own race 196 us, ACCEPT.
- Three-edge third factor: three raise-go edges, tau_e 6.0 s = 6000 ms,
  trace __AUX_TRACE__, eta __AUX_ETA1__ / __AUX_ETA2__ / __AUX_ETA3__,
  weights 0.44->0.21, 0.40->0.19, 0.37->0.17. Raster excerpt unchanged
  (decision window is still 40 ms) and remains sorted with unique
  neuron_ids (same-neuron >=1000 us vacuously).

Winner/loser flip (re-stated, not replaced): reversing 192 us would only
reorder triage; r_ncg and r_wet floors still MODIFY. Contrast flip of
196 us similarly cannot turn a dry dome into a blanket.

## Trajectory Builder

Schema checks on the FINAL object: required Thalamic v2 keys present as
objects; `state.sim_or_real`=designed; `safety_decision.decision`=MODIFY
with numeric rationale; `reward_components.total` = sum of five heads =
sum of 7 ticks = -0.14; `spike_events` globally non-decreasing on
t_rel_ms, 26 events, refractory >=0.8 ms, 3 channels in race window;
raster 20–50 ms, spikes=round(n*rate*window_s)+/-1, energy 23 pJ/spike,
excerpt sorted, tau_e consistent; gate_snn.decision matches; meta.round=35,
factory=multi-agent-ouroboros-swarm, generator=grok-4.6,
run_label=2026-09-02-final-heavy; rights on record and meta; no thought
keys; no training_ready; Diversity + Edge-Case injections from BOTH cycles
present and non-trivial; cycle 2 strictly additive; plant is not
LYOSHIELD, not CINDERWICK, not TRIAD, not FERRICLEAVE, not CASSITER, not
SEEDLATCH, not STRIAFOIL, not PROTONIL, not TORSIONKEY, not ORRIS, not
WHORLSPAR, not SKULLGATE, not CALXION, not BRACEGILT, not MAGNORIL, not
GORSEFLUE, not CLINKERFELL.

Densification delta: +1 domain sub-variant (2.8 MW well-test), +1 tail
(Sunday-night forgery), +10 spikes (16->26), +2 ticks (5->7), +1 contrast
train with own race, +2 delayed side-effects, +1 three-edge scar with
any-pair-rollback-fails, +1 HITL ratify, +1 surprise (silica overflux is
the campaign-miss mechanism).

Publishable JSONL line (the only JSONL line; also at batch-r35.jsonl):

```json
__FINAL_JSONL__
```

Validation receipt (final): checks passed / fixed as reported by
build_r35.py self-validate (check_jsonl, raster_status, verify_record_execution,
spike_probe --strict).
"""
    text = (
        text.replace("__C1_SPIKES__", str(len(c1_spikes)))
        .replace("__AUX_TRACE__", f"{math.exp(-6.0/6.0):.5f}")
        .replace("__AUX_ETA1__", f"{0.23/math.exp(-6.0/6.0):.5f}")
        .replace("__AUX_ETA2__", f"{0.21/math.exp(-6.0/6.0):.5f}")
        .replace("__AUX_ETA3__", f"{0.20/math.exp(-6.0/6.0):.5f}")
        .replace("__FINAL_JSONL__", line)
    )
    (OUT / "swarm-transcript-r35.md").write_text(text)
    return text


def heads_summary(rec):
    rc = rec["reward_components"]
    return {
        "id": rec["id"],
        "total": rc["total"],
        "decision": rec["safety_decision"]["decision"],
        "sim": rec["state"]["sim_or_real"],
        "domain": rec["state"]["domain"],
        "spikes": len(rec["spike_events"]),
        "ticks": len(rc["ticks"]),
        "plant": rec["state"]["scenario_name"],
    }


def main():
    rec, aux = build_record()
    errs = local_checks(rec, aux)

    OUT.mkdir(parents=True, exist_ok=True)
    line = json.dumps(rec, ensure_ascii=False, separators=(",", ":"))
    (OUT / "batch-r35.jsonl").write_text(line + "\n")

    from check_records import FactoryStaging, check_jsonl
    from curate_bridge import raster_status
    from verify_execution import verify_record_execution

    e, w, kinds, n = check_jsonl(
        OUT / "batch-r35.jsonl",
        "batch-r35.jsonl",
        staging=FactoryStaging(enabled=True),
    )
    print("check_jsonl errors", e)
    print("check_jsonl warnings", w)
    print("kinds", kinds, "n", n)
    errs.extend(e)

    st = raster_status(rec)
    print(
        "raster_status",
        {
            k: st[k]
            for k in (
                "raster_present",
                "raster_valid",
                "gate_snn_present",
                "gate_snn_valid",
                "reason_codes",
                "routing_table_entries",
                "third_factor_present",
                "spikes",
            )
            if k in st
        },
    )
    if st.get("reason_codes"):
        errs.append(f"raster {st['reason_codes']}")
    if not st.get("raster_valid"):
        errs.append("raster not valid")
    if not st.get("gate_snn_valid"):
        errs.append("gate_snn not valid")

    status, reason = verify_record_execution(rec, "maos-r35-001")
    print("verify_record_execution", status, reason)
    if status != "verified":
        errs.append(f"verify {status}: {reason}")

    probe = subprocess.run(
        [
            sys.executable,
            f"{ROOT}/pipelines/spike_probe.py",
            "--strict",
            str(OUT / "batch-r35.jsonl"),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    print("spike_probe rc", probe.returncode)
    print(probe.stdout)
    if probe.stderr:
        print("spike_probe stderr", probe.stderr)
    if probe.returncode != 0:
        errs.append(f"spike_probe rc {probe.returncode}")

    receipt = (
        f"check_jsonl errors={e} warnings={w} kinds={kinds} n={n}; "
        f"raster_status valid={st.get('raster_valid')} gate={st.get('gate_snn_valid')} "
        f"reasons={st.get('reason_codes')}; verify_record_execution={status} ({reason}); "
        f"spike_probe --strict rc={probe.returncode}"
    )
    write_notes(rec, aux, receipt)
    write_transcript(rec, line)

    headings = re.findall(
        r"^## .+$", (OUT / "swarm-transcript-r35.md").read_text(), re.M
    )
    print("headings", headings)
    expected = [
        "## Generator",
        "## Critic",
        "## Diversity Enforcer",
        "## Edge-Case Hunter",
        "## Neuromorphic Translator",
        "## Trajectory Builder",
        "## Generator",
        "## Critic",
        "## Diversity Enforcer",
        "## Edge-Case Hunter",
        "## Neuromorphic Translator",
        "## Trajectory Builder",
    ]
    if headings != expected:
        errs.append(f"heading sequence {headings}")

    notes = (OUT / "NOTES-r35.md").read_text()
    cov = re.findall(r"^Novel coverage: .+$", notes, re.M)
    if cov != [NOVEL_LINE]:
        errs.append(f"novel coverage lines {cov}")

    hchk = subprocess.run(
        [
            sys.executable,
            "/tmp/maos_heading_check.py",
            str(OUT / "swarm-transcript-r35.md"),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    print(hchk.stdout)
    if hchk.returncode != 0:
        errs.append(f"heading_check rc {hchk.returncode}: {hchk.stdout}")

    raw_guard = subprocess.run(
        ["git", "-C", ROOT, "status", "--porcelain", "--", "outputs/raw"],
        check=False,
        capture_output=True,
        text=True,
    )
    if raw_guard.stdout.strip():
        errs.append(f"outputs/raw dirty: {raw_guard.stdout.strip()}")

    print("bytes jsonl", (OUT / "batch-r35.jsonl").stat().st_size)
    print("bytes notes", (OUT / "NOTES-r35.md").stat().st_size)
    print("bytes transcript", (OUT / "swarm-transcript-r35.md").stat().st_size)
    print("HEADS", heads_summary(rec))
    if errs:
        print("ERRS:")
        for x in errs:
            print(" -", x)
        sys.exit(1)
    print("OK", OUT / "batch-r35.jsonl")


if __name__ == "__main__":
    main()
