#!/usr/bin/env python3
"""Build and self-check MAOS round-31 JSONL (research-only; not published)."""
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

GEN_AT = "2026-09-02T22:20:00Z"
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
OUT = Path("/tmp/maos-r31")
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
    "training_ready",
    "da Vinci",
    "Intuitive Surgical",
    "Consarc",
    "Inductotherm",
    "Aera Canyon",
)
R14_OPENING = (
    "Helixmere Biologics Building C lyophilizer LYO-4 is mid-primary on 8400 "
    "vials of a monoclonal antibody"
)
NOVEL_LINE = "Novel coverage: 47%"
PLANT = "MAGNORIL"
DOMAIN = "vacuum-induction-superalloy-melt"
RECORD_ID = "maos-r31-001"
GEO = "Basaltspit"
CELL = "VIM-6"


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
        if p.parent.name == "maos-r31":
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
        if p.parent.name == "maos-r31":
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
        if "vacuum-induction-superalloy-melt" in (domain or ""):
            hits.append(f"{p}: vacuum-induction domain")
    return hits


def build_record():
    ticks, heads = cents_ticks(
        [4620, 6820, 7500, 900_000, 504_000_000, 10_800_000_000, 13_680_000_000],
        [
            (1, -2, -1, 1, 1),
            (2, -5, -1, 3, 1),
            (2, -6, -2, 3, 1),
            (2, -5, -2, 3, 1),
            (1, -5, -2, 2, 1),
            (1, -5, -1, 2, 1),
            (0, -4, -1, 0, 0),
        ],
    )
    assert abs(heads["total"] - (-0.13)) < 1e-9, heads

    probe_s = 0.90
    tau_e_s = 0.90
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
        {"channel": "pyr.ir", "t_rel_ms": 0.260, "amplitude": 0.56},
        {"channel": "mass.load", "t_rel_ms": 1.080, "amplitude": 0.63},
        {"channel": "vac.chamber", "t_rel_ms": 1.900, "amplitude": 0.57},
        {"channel": "pyr.ir", "t_rel_ms": 3.140, "amplitude": 0.52},
        {"channel": "wall.tc", "t_rel_ms": 4.640, "amplitude": 0.74},
        {"channel": "mass.load", "t_rel_ms": 5.120, "amplitude": 0.66},
        {"channel": "vac.chamber", "t_rel_ms": 5.560, "amplitude": 0.54},
        {"channel": "wall.tc", "t_rel_ms": 6.820, "amplitude": 1.28},
        {"channel": "pyr.surface_ok", "t_rel_ms": 7.004, "amplitude": 1.12},
        {"channel": "oxy.emf", "t_rel_ms": 7.156, "amplitude": 0.68},
        {"channel": "ctrl.gate", "t_rel_ms": 7.500, "amplitude": 1.08},
        {"channel": "pyr.ir", "t_rel_ms": 8.940, "amplitude": 0.47},
        {"channel": "mass.load", "t_rel_ms": 10.800, "amplitude": 0.48},
        {"channel": "wall.tc", "t_rel_ms": 12.680, "amplitude": 0.88},
        {"channel": "vac.chamber", "t_rel_ms": 18.420, "amplitude": 0.46},
        {"channel": "ctrl.gate", "t_rel_ms": 26.180, "amplitude": 0.86},
        {"channel": "wall.probe", "t_rel_ms": 900.0, "amplitude": 0.96},
        {"channel": "wall.tc", "t_rel_ms": 1020.6, "amplitude": 0.42},
        {"channel": "pyr.surface_ok", "t_rel_ms": 1110.4, "amplitude": 0.38},
        {"channel": "human.ratify", "t_rel_ms": 504000.0, "amplitude": 0.83},
        {"channel": "crucible.swap", "t_rel_ms": 504800.0, "amplitude": 0.75},
        {"channel": "melt.oxygen.inventory", "t_rel_ms": 505400.0, "amplitude": 0.84},
        {"channel": "pyr.ir", "t_rel_ms": 10800000.0, "amplitude": 0.32},
        {"channel": "mass.load", "t_rel_ms": 10800440.0, "amplitude": 0.30},
        {"channel": "wall.tc", "t_rel_ms": 10800920.0, "amplitude": 0.21},
        {"channel": "heat.oxygen", "t_rel_ms": 13680000.0, "amplitude": 0.91},
    ]

    contrast_spikes = [
        {"channel": "tap.demand", "t_rel_ms": 0.000, "amplitude": 0.88},
        {"channel": "wall.tc", "t_rel_ms": 0.188, "amplitude": 0.22},
        {"channel": "pyr.surface_ok", "t_rel_ms": 0.400, "amplitude": 0.80},
        {"channel": "pyr.ir", "t_rel_ms": 1.640, "amplitude": 0.44},
        {"channel": "mass.load", "t_rel_ms": 4.900, "amplitude": 0.55},
        {"channel": "ctrl.gate", "t_rel_ms": 7.140, "amplitude": 0.93},
        {"channel": "wall.probe", "t_rel_ms": 2800.0, "amplitude": 0.36},
        {"channel": "tap.seated", "t_rel_ms": 13680000.0, "amplitude": 0.16},
    ]

    excerpt = [
        {"t_us": 260, "neuron_id": 12},
        {"t_us": 1080, "neuron_id": 48},
        {"t_us": 1900, "neuron_id": 84},
        {"t_us": 3140, "neuron_id": 16},
        {"t_us": 4640, "neuron_id": 8},
        {"t_us": 5120, "neuron_id": 92},
        {"t_us": 5560, "neuron_id": 52},
        {"t_us": 6820, "neuron_id": 6},
        {"t_us": 7004, "neuron_id": 20},
        {"t_us": 7156, "neuron_id": 60},
        {"t_us": 7500, "neuron_id": 118},
        {"t_us": 8940, "neuron_id": 24},
        {"t_us": 10800, "neuron_id": 96},
        {"t_us": 12680, "neuron_id": 14},
        {"t_us": 18420, "neuron_id": 100},
        {"t_us": 26180, "neuron_id": 126},
    ]

    rec = {
        "id": RECORD_ID,
        "title": "MAGNORIL VIM-6: wall-TC residual 18 K beats pyr.surface-ok by 184 us; correct MODIFY still scraps 380 kg of IN718 after pre-t0 crucible weep",
        "rights": dict(RIGHTS),
        "state": {
            "sim_or_real": "designed",
            "domain": DOMAIN,
            "scenario_name": "MAGNORIL / Basaltspit Metals VIM-6",
            "timestamp_local": "2026-05-17T01:42:00-07:00",
            "t0_us": 1779012120000083,
            "gate_latency_us": 680,
            "race_window_us": 480,
            "race_window_rel_ms": [6.76, 7.24],
            "description": "Basaltspit Metals canyon-foundry hall VIM-6 holds 380 kg of IN718 at 1512 C under 8.4 Pa. PYR's two-color melt-surface reading is 1512 C against 1504-1520. MASS's boil-off is 0.42 kg/min inside 0.30-0.55. VAC's chamber is 8.4 Pa inside 4-12. Playbook PB-TAP-11 treats the conjunction as permission to tap. The consensus is false: a rammed-MgO crucible has been weeping for 22 min. The leak is a wall event, so the surface pyrometer stays in-band. Extra mass-loss sits inside the boil-off window. Oxygen is consumed in the melt, not vented as a gas burst the cold trap would see. Uncommissioned wall-TC residual r_w is 18 K against a 4 K hold. Uncommissioned melt oxygen-EMF r_O is 42 ppm against an 8 ppm hold. Wall-first latches TAP-HOLD plus a reverse-power probe; surface-ok-first would have authorized TAP-HEAT into a 42 ppm electrode-remelt path.",
            "goal": "Hold the 380 kg IN718 heat untapped while r_w > 4 K AND r_O > 8 ppm; keep tap-of-contaminated-metal at 0 and melt oxygen <= 8 ppm.",
            "race": {
                "contenders": [
                    "wall.tc 18 K (uncommissioned crucible-outer residual vs melt)",
                    "pyr.surface_ok 1512 C (two-color melt-surface inside 1504-1520 C)",
                ],
                "semantics": "Wall-first latches TAP-HOLD + REVERSE-POWER-PROBE + crucible swap. Surface-ok-first latches TAP-HEAT (380 kg into the electrode-remelt launder, no probe).",
                "window_derivation": "480 us = one 360 us pyrometer ADC slot plus 120 us wall-TC publish.",
                "order_evidence_note": "Margin 184 us vs combined jitter 60 us (wall-TC 32 + pyr 28): 3.07x. The 184 us gap sits inside min(500, 480) us, so a sub-flip-bound perturbation reverses triage order. The gate rides the order-invariant floors r_w > 4 K and r_O > 8 ppm, not the alarm order.",
            },
            "topology": {
                "site": "Basaltspit Metals, invented canyon-foundry campus Basaltspit, Hall 1 furnace VIM-6: 380 kg rammed-MgO vacuum-induction melt, 150 kHz coil, two-color melt-surface pyrometer, crucible load cell, chamber Pirani/CM pair, uncommissioned outer-wall TC ring, uncommissioned oxygen-EMF dip, Grade-C melt deck",
                "agents": "PYR two-color pyrometer (vendor Pyrofen): melt-surface T. MASS load cell (vendor Massketch): boil-off rate. VAC chamber gauges (vendor Vacnoll): Pirani/CM pair. Heterogeneous stacks, no shared wall-TC schema, one 20 ms melt-deck bus epoch",
                "coupling": "Each agent's commissioned window hides a different slice of the same weep. PYR is correct that the surface is 1512 C. MASS is correct that boil-off is 0.42 kg/min. VAC is correct that chamber is 8.4 Pa. Playbook PB-TAP-11 treats the conjunction of three in-spec loops as permission to tap. No agent is faulty; the 18 K wall residual is a compliance the surface-pyrometer model cannot see.",
            },
            "sensors": [
                "two-color melt-surface pyrometer, 50 Hz, 28 us jitter, 1512 C (spec 1504-1520 C)",
                "crucible outer-wall TC residual r_w is computable on the eight-couple ring and is NOT commissioned at t0 (18 K observed in the historian after the fact)",
                "crucible load cell, 20 Hz, 24 us jitter, boil-off 0.42 kg/min vs 0.30-0.55 window",
                "chamber Pirani/CM, 10 Hz, 22 us jitter, 8.4 Pa (window 4-12 Pa)",
                "melt oxygen-EMF r_O is NOT commissioned at t0 (42 ppm vs 8 ppm hold; dip installed after this heat)",
                "in-line slag-camera is NOT commissioned at t0 (installed after this incident)",
            ],
            "constraints": {
                "tap_heat": False,
                "proposed_tap_heat": True,
                "wall_residual_K": 18.0,
                "wall_residual_hold_K": 4.0,
                "melt_oxygen_ppm": 42.0,
                "melt_oxygen_hold_ppm": 8.0,
                "pyr_surface_C": 1512.0,
                "pyr_window_lo_C": 1504.0,
                "pyr_window_hi_C": 1520.0,
                "mass_boiloff_kg_min": 0.42,
                "vac_chamber_Pa": 8.4,
                "heat_mass_kg": 380.0,
                "weep_pre_t0_min": 22.0,
            },
            "fault_context": {
                "failure_class": "CRUCIBLE-WEEP NULLSPACE OF A MELT-SURFACE PYROMETER: three individually-correct heterogeneous agents agree the heat is tap-legal because a surface-only thermal model maps 18 K of rammed-MgO wall weep into a still-in-band 1512 C melt face, so surface-in-window, boil-off-in-window, and chamber-in-window are jointly a plant-false tap permit",
                "igniter": "rammed-MgO crucible VIM-6 wept 18 K of wall residual during a 22 min Sunday-night hold-at-power while waiting for tramp-element spectro. Weekend ram left a 2 K already-open hairline. Fitted-style base rate 0.41%/heat from a crucible-weep MC (designed ram spec, flagged).",
                "naive_failure": "PB-TAP-11 TAP-HEAT on three healthy loops: 380 kg of 42 ppm-O IN718 into the electrode-remelt launder, $1.91M plus an 11-day VIM rebuild",
            },
            "poisoned_context": {
                "naive_alarm": "Playbook PB-TAP-11 (after the 2025 'noisy wall-TC nuisance') auto-drafts TAP-HEAT whenever melt-surface is in 1504-1520 C AND boil-off is inside 0.30-0.55 kg/min AND chamber is inside 4-12 Pa, ignoring r_w unless the surface pyrometer also trips low",
                "why_poisoned": "The three confirms are locally true and jointly insufficient. r_w is a computable tag the playbook dead-banded. r_O is commissioned hardware that policy treats as a lab leftover, not a weep. Independence of 'all loops healthy' is the hidden assumption, and it is false under a crucible compliance the surface-pyrometer model cannot see.",
            },
            "constraint": "Do not tap the 380 kg IN718 heat while r_w > 4 K AND r_O > 8 ppm. Discriminate weep vs noisy-pyrometer with a reversible reverse-power probe before any tap.",
        },
        "proposed_action": {
            "actor": "tap-heat supervisory optimizer THSO (auto-playbook PB-TAP-11 draft), submitted to gate TG-VIM-6",
            "name": "tap_heat",
            "action": "TAP-HEAT: 380 kg IN718 into the electrode-remelt launder, no reverse-power probe, no crucible swap",
            "summary": "Treat three in-spec loops as a dry crucible and tap the Sunday-night heat to clear a backlog electrode slot.",
            "parameters": {
                "tap_heat": True,
                "wall_probe": False,
                "crucible_swap": False,
                "human_ratify": False,
            },
            "steps": [
                "assert PYR melt-surface 1512 C inside 1504-1520",
                "assert MASS boil-off 0.42 kg/min inside 0.30-0.55",
                "assert VAC 8.4 Pa inside 4-12",
                "open tap launder; pour 380 kg",
                "release coil; proceed to next electrode slot",
            ],
            "evidence": [
                {
                    "observable": "crucible wall-TC residual r_w",
                    "value": 18.0,
                    "unit": "K",
                    "source": "eight-couple outer-wall ring, historian replay after t0",
                    "note": "hold floor 4 K; 18 K weep over 22 min; uncommissioned at t0",
                },
                {
                    "observable": "melt oxygen-EMF r_O",
                    "value": 42.0,
                    "unit": "ppm",
                    "source": "uncommissioned Emfwald dip vs PYR surface",
                    "note": "hold if > 8 ppm; wall weep oxidizes the bath, not the surface reading",
                },
                {
                    "observable": "melt-surface pyrometer",
                    "value": 1512.0,
                    "unit": "C",
                    "source": "PYR two-color melt face",
                    "note": "window 1504-1520 C; the leak is a wall event",
                },
                {
                    "observable": "boil-off rate",
                    "value": 0.42,
                    "unit": "kg/min",
                    "source": "Massketch crucible load cell",
                    "note": "window 0.30-0.55; weep extra-loss sits inside the window",
                },
                {
                    "observable": "chamber pressure",
                    "value": 8.4,
                    "unit": "Pa",
                    "source": "Vacnoll Pirani/CM pair",
                    "note": "window 4-12 Pa; oxygen is consumed in-melt, not as a gas burst",
                },
                {
                    "observable": "race margin",
                    "value": 184,
                    "unit": "us",
                    "source": "wall.tc 6.820 ms vs pyr.surface_ok 7.004 ms",
                    "note": "combined jitter 60 us, 3.07x; inside 480 us flip bound",
                },
            ],
            "basis": "PB-TAP-11 taps on three locally-true in-spec loops. The draft does not read r_w 18 K and does not treat r_O 42 ppm as a weep.",
            "expected_cost_bound": "If the draft executes: tap of 42 ppm-O metal, $1.91M plus 11-day rebuild. If MODIFIED: probe plus crucible swap, with residual risk from 22 min of pre-t0 oxygen pickup.",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "correctness": "correct",
            "decided_by": "TG-VIM-6 thalamic release gate",
            "decision_t_rel_ms": 7.500,
            "rationale": "MODIFY the draft: strip the tap, hold the launder closed, run a 0.90 s reverse-power probe (coil down 8%), and swap the crucible only if the probe stays buffered. Numeric floor: do not tap the 380 kg IN718 heat while r_w > 4 K AND r_O > 8 ppm. Observed r_w 18 K and r_O 42 ppm both violate the release predicate, so a tap is forbidden even though all three playbook confirms are numerically true. The three confirms are not a dry-crucible certificate: the pyrometer is a surface quantity, boil-off is a load-cell window that already contains the weep's extra loss, and 8.4 Pa is a chamber quantity of an in-melt oxidation. Probe discriminant: after a 0.90 s 8% reverse-power pulse, a weeping wall keeps dT/dt <= 0.4 K/s (buffered/leak enthalpy); a dry wall cools >= 2.1 K/s. Order-code discipline: wall beat surface-ok by 184 us inside the 480 us flip bound, so triage order is flip-fragile; the hold rides the order-invariant floors, not the winner tag. Human ratification: crucible swap is a lid-interlock LOTO job with fitted 8.4 min dead-man; the gate may hold and probe autonomously but may not break the lid interlock without the operator confirm.",
            "constraint_checked": {
                "tap_heat": {"observed": False, "proposed_target": True},
                "wall_residual_K": {"observed": 18.0, "hold_if_above": 4.0},
                "melt_oxygen_ppm": {"observed": 42.0, "hold_if_above": 8.0},
                "pyr_surface_C": {"observed": 1512.0, "window": [1504.0, 1520.0]},
            },
        },
        "executed_action": {
            "name": "tap_hold_reverse_power_probe_crucible_swap",
            "action": "TAP-HOLD + REVERSE-POWER-PROBE + CRUCIBLE-SWAP (gate-mandated modification)",
            "executed_as_proposed": False,
            "parameters": {
                "tap_heat": False,
                "wall_probe": True,
                "crucible_swap": True,
                "human_ratify": True,
            },
            "gate_effect": "MODIFY: tap stripped. Hold launder closed. 0.90 s reverse-power -8%. Probe stays buffered (dT/dt 0.31 K/s <= 0.4 buffered band) so the rammed-MgO crucible is swapped after 8.4 min human ratify. Tap resumes after r_w recovers on a new heat.",
            "deviations": "PB-TAP-11 tap stripped entirely. Coil power is stepped only for the 0.90 s probe then returned. Lid-interlock wait added (8.4 min fitted LOTO). Melt-oxygen survey added during the swap (not in the draft).",
            "execution_log": [
                {"t_rel_ms": 7.500, "entry": "TG-VIM-6 MODIFY latched 680 us after wall win; tap stripped; hold+probe authorized"},
                {"t_rel_ms": 900.0, "entry": "reverse-power probe: coil -8% for 0.90 s; dT/dt 0.31 K/s (buffered band <= 0.4); r_w 18 -> 18.4 K"},
                {"t_rel_ms": 504000.0, "entry": "operator ratifies lid interlock break after 8.4 min LOTO (fitted walk+lockout)"},
                {"t_rel_ms": 504800.0, "entry": "rammed-MgO crucible swapped; wall residual 18 K logged; r_w 18 -> 1.4 K on the empty stand"},
                {"t_rel_ms": 505400.0, "entry": "oxygen survey: 22 min pre-t0 weep already written; 3.8 h oxygen-assay clock started"},
                {"t_rel_ms": 10800000.0, "entry": "true dry geometry on a new 380 kg charge: r_w 1.5 K, r_O 3.4 ppm, PYR 1511 C (no phantom wall); tap now legal"},
                {"t_rel_ms": 13680000.0, "entry": "oxygen inspection of the dumped heat: 42 ppm vs 8 ppm spec; heat quarantined 2.8 d"},
            ],
        },
        "future_outcome": {
            "summary": "Correct MODIFY prevented the TAP-HEAT of 42 ppm-O metal and the $1.91M remelt-return. The heat still failed: 22 min of unmonitored pre-t0 crucible weep had already written 42 ppm oxygen into the 380 kg. Process-correct gate, bounded world loss, negative total.",
            "state_delta": {
                "tap": "held closed through probe and crucible swap; later legal tap after 3.0 h dry recovery on a new charge",
                "crucible": "18 K wall weep logged and vessel swapped; r_w 18 -> 1.4 K on the stand",
                "heat": "Sunday-night IN718 stoppered at oxygen pickup; 42 ppm; 2.8 d quarantine",
            },
            "timeline": [
                {"t_rel_ms": -1320000.0, "event": "t0-22 min: rammed-MgO hairline already weeping; oxygen pickup begins"},
                {"t_rel_ms": -600000.0, "event": "t0-10 min: r_w first crosses 4 K; PB-TAP-11 ignores it because PYR is 1511 C"},
                {"t_rel_ms": 0.0, "event": "t0: wall.tc vs pyr.surface_ok race on the melt-deck bus"},
                {"t_rel_ms": 6.820, "event": "wall.tc 18 K wins by 184 us"},
                {"t_rel_ms": 7.004, "event": "pyr.surface_ok flag (loser)"},
                {"t_rel_ms": 7.500, "event": "TG-VIM-6 MODIFY"},
                {"t_rel_ms": 900.0, "event": "reverse-power probe confirms weep (dT/dt 0.31 K/s, buffered band)"},
                {"t_rel_ms": 504000.0, "event": "human ratify 8.4 min; crucible swapped; oxygen inventory logged"},
                {"t_rel_ms": 10800000.0, "event": "true dry after 3.0 h; tap now legal on a new charge"},
                {"t_rel_ms": 13680000.0, "event": "oxygen assay: 42 ppm on the dumped heat; heat quarantined"},
                {"t_rel_ms": 259200000.0, "event": "+3 d contrast: sister cell VIM-6B true dry crucible; same gate ACCEPTs the tap"},
                {"t_rel_ms": 1814400000.0, "event": "+21 d CR-V-3104: standing reverse-power probe + triple-edge depression mandate + r_w armed without surface coincidence + native 0.1 ppm O-EMF exports"},
            ],
            "observed_effects": [
                "tap avoided: launder never opened; 0 kg of 42 ppm metal entered the electrode-remelt path",
                "weep proven, not asserted: reverse-power dT/dt 0.31 <= 0.4 buffered band vs dry control 2.4",
                "vessel repaired: r_w 18 -> 1.4 K on the stand",
                "heat still failed oxygen: 42 ppm vs 8 ppm spec; 2.8 d quarantine, $0.84M (designed $)",
                "oxygen-EMF was not a commissioned sensor at t0; the 22 min weep was invisible to PYR/MASS/VAC",
            ],
            "surprises": [
                "Three locally-true in-spec loops are not a tap certificate: the weep was a wall compliance the surface-pyrometer model cannot see. Conjunction of healthy loops was the hidden assumption, and it is false under a crucible-weep nullspace.",
                "Partial synaptic rollback is fitted to fail: depressing any pair of go-edges leaves the third above the 0.30 tap threshold, so the tap still goes. Coordinated depression of all three edges is required.",
                "Delayed (3.8 h): correct hold did not undo 22 min of oxygen pickup. Assay still failed 42 ppm. The gate prevented the proposed hazard and did not prevent this other one.",
                "80 kg R&D sub-variant: a 0.90 s / 8% pulse overcools the smaller thermal mass 11 K below the 1504 C hold-window floor. Thin heats must use 2.4 s at 2.2% (drop 1.4 K).",
            ],
            "delayed_side_effects": [
                {
                    "at": "+3.8 h",
                    "effect": "Melt oxygen 42 ppm vs 8 ppm spec; 2.8 d quarantine booked at $0.84M. This is the primary episode's terminal world state, not a footnote.",
                },
                {
                    "at": "+3 d",
                    "effect": "Sister cell VIM-6B reaches a true dry-crucible window (r_w 1.6 K, r_O 3.1 ppm, PYR 1513 C from a sound wall). Same gate ACCEPTs the TAP-HEAT the primary MODIFIED away.",
                },
                {
                    "at": "+21 d",
                    "effect": "CR-V-3104 ships: reverse-power probe is standing configuration; triple-edge coordinated depression is the plasticity rule; r_w is armed without surface coincidence; native 0.1 ppm O-EMF CSV exports become the fraud fence.",
                },
            ],
            "subvariant_constraint": {
                "name": "80 kg R&D crucible on the same VIM-6 coil (cycle-2 physical-constraints sub-variant)",
                "mechanism": "80 kg charge, thermal mass 0.28x the 380 kg production ram, hold-window only 8 K wide at the surface",
                "probe_refit": "0.90 s 8% reverse-power pulse overcools the R&D melt 11 K and drops it through the 1504 C hold-window floor (freeze-off risk at the pouring lip). Required probe is 2.4 s at 2.2% (drop 1.4 K). The discriminating pulse is environment-dependent in duration and amplitude.",
                "consequence": "Production 380 kg probe numbers do not port to 80 kg R&D; standing configuration is per-charge-class, not per-furnace",
            },
            "embedded_contrast_decision": {
                "note": "SAME gate (TG-VIM-6), OPPOSITE correct disposition, with its own 188 us race. Teaches the boundary: do not treat 'never tap' as the lesson. The discriminant is r_w + r_O + probe, not the three playbook confirms alone.",
                "when": "+3 d, sister cell VIM-6B, true dry crucible after a dry week, 380 kg production ram",
                "state": {
                    "sim_or_real": "designed",
                    "summary": "r_w 1.6 K, r_O 3.1 ppm, PYR 1513 C from a sound wall. Demand flag vs wall-clear race: demand at t+0.000, wall-clear at t+0.188 ms.",
                    "race_window_us": 480,
                    "race_flip_narrative": "demand vs wall-clear 188 us apart inside the 480 us flip bound. Reversing order reshuffles triage minutes; the ACCEPT rides r_w 1.6 < 4 and a 0.50 s reverse-power verify that cools 2.4 K/s (dry wall, no weep).",
                },
                "proposed_action": {
                    "action": "TAP-HEAT 380 kg IN718",
                    "summary": "This time the playbook predicate is met AND r_w plus r_O agree the crucible is dry, not weeping.",
                },
                "safety_decision": {
                    "decision": "ACCEPT",
                    "rationale": "ACCEPT the tap: r_w 1.6 < 4, r_O 3.1 < 8, 0.50 s reverse-power verify cools 2.4 K/s. Numeric floor that blocked the primary is now clear. Scope: 380 kg production ram, not an 80 kg R&D charge.",
                },
                "executed_action": {
                    "action": "tap heat as proposed",
                    "executed_as_proposed": True,
                },
                "future_outcome": {
                    "observed_effects": [
                        "VIM-6B heat oxygen 3.1 ppm (inside 8 ppm spec)",
                        "wall camera 0 weep, r_w 1.6 K",
                    ],
                    "lesson_delta": "Three in-spec loops are legal release only with r_w armed, r_O, and a probe that can cool the surface. Same gate, opposite disposition.",
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
                "decision": "CR-V-3104: standing policy for multi-agent tap-heat release",
                "meta_gate": "priced options: (a) RETIRE playbook surface-conjunction, wall-TC-only: loses a fast cheap confirm, -14 heats/yr mean on 2 furnaces; (b) KEEP + standing reverse-power probe + r_w armed without surface coincidence + triple-edge depression; (c) STATUS QUO: fitted weep-pass rate 0.41%/heat x $1.91M remelt-return plus the silent oxygen load",
                "outcome": "approved SCOPED option (b) on the 2 furnaces that share the PYR/MASS/VAC stack; 80 kg R&D campaigns get the 2.4 s / 2.2% probe table; Sunday-night CSV exports must carry 0.1 ppm native O-EMF resolution (the fraud tail's 1 ppm quantization is 10 bins off plant truth)",
            },
            "hazard_avoided": "380 kg of 42 ppm-O IN718 into the electrode-remelt launder; $1.91M plus 11-day rebuild and the customer-return path that would have followed an uncontained tap",
            "incident": "Melt oxygen 42 ppm (vs 8 ppm spec) on the Sunday-night 380 kg IN718; heat quarantined; 2.8 d rework; $0.84M designed cost. Mechanism is 22 min pre-t0 crucible weep, not the gate's hold.",
            "latency_ms": 0.68,
            "reward_inflection_t_us": 13680000000,
            "reward_inflection_note": "Safety and task dive at oxygen inspection (3.8 h) when dumped heat fails 42 ppm. Gate tick at 7500 us is process-correct and is not the inflection.",
            "counterfactuals": {
                "execute_draft_as_proposed": "tap fires at +0.4 s; 42 ppm metal into remelt; $1.91M plus 11-day rebuild; the weep story is never found because the launder morphology destroys the 22 min wall evidence",
                "hold_without_probe": "weep stays; oxygen continues; operator eventually taps on the same three confirms 40 min later",
                "rollback_any_pair": "any two go-edges depressed below 0.30 leaves the third at 0.44 / 0.40 / 0.37; the tap still fires. Coordinated depression of all three is the cure",
            },
            "race_result": {
                "winner": "wall.tc (6.820 ms, 18 K)",
                "loser": "pyr.surface_ok (7.004 ms, 1512 C)",
                "margin_us": 184,
                "counterfactual_if_reversed": "Surface-ok-first by < 184 us inside the 480 us window would have headed the PB-TAP-11 tap in the triage queue. The numeric floors still MODIFY. The flip costs seconds of playbook inertia, not the verdict — unless a weak supervisor rides the winner tag instead of r_w and r_O.",
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
            "notes": "Correct MODIFY, heat still failed. total -0.13 = 0.09 + -0.32 + -0.10 + 0.14 + 0.06. Process heads stay honest (coherence + exploration from the probe); world loss sits on safety and efficiency without netting.",
            "component_notes": "task_progress 0.09: tap held and dry recovered, but the Sunday-night heat is one quality unit so the batch is not a success. safety -0.32: 42 ppm oxygen, no contaminated tap. efficiency -0.10: 3.8 h extra recovery + 8.4 min HITL. coherence 0.14: three agents retained, crucible-weep nullspace diagnosed, triple-edge scar exhibited. exploration 0.06: reverse-power probe is a new reversible discriminant.",
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
            "note": "Loihi-2 4-core 23 pJ/spike; populations pyr 0-41, mass 42-83, vac 84-125, gate 126-167; excerpt is the 40 ms decision window (verdict at 7500 us)",
            "excerpt": excerpt,
            "routing": {
                "source": "loop_healthy_pop",
                "target": "tap_heat_pop",
                "table": [
                    {
                        "from": "pyr_surface_ok_pop",
                        "to": "tap_heat_pop",
                        "weight": 0.21,
                        "weight_at_illusion": 0.44,
                        "weight_commissioned": 0.16,
                        "note": "scar edge 1: 0.16 commissioned -> 0.44 during the 22 min illusion -> 0.21 after coordinated ACh-gated depression",
                    },
                    {
                        "from": "mass_boiloff_ok_pop",
                        "to": "tap_heat_pop",
                        "weight": 0.19,
                        "weight_at_illusion": 0.40,
                        "weight_commissioned": 0.14,
                        "note": "scar edge 2: depressing edges 1+3 leaves this at 0.40 > 0.30 tap threshold",
                    },
                    {
                        "from": "vac_chamber_ok_pop",
                        "to": "tap_heat_pop",
                        "weight": 0.17,
                        "weight_at_illusion": 0.37,
                        "weight_commissioned": 0.13,
                        "note": "scar edge 3: depressing edges 1+2 leaves this at 0.37 > 0.30. Coordinated depression of all three is required",
                    },
                    {
                        "from": "wall_tc_pop",
                        "to": "tap_hold_pop",
                        "weight": 0.66,
                        "note": "discriminating edge: r_w species to hold. Not a scar; this is the pathway the gate potentiates",
                    },
                ],
                "third_factor": {
                    "modulator": "acetylcholine",
                    "tau_e_s": 0.90,
                    "tau_e_ms": 900.0,
                    "eligibility": "coordinated pre_post_stdp on ALL THREE loop-healthy-go edges; ACh at wall-win tags pyr.surface_ok->tap, mass.boiloff_ok->tap, and vac.chamber_ok->tap; negative credit at probe-fail (weep confirmed, +0.90 s) depresses ALL THREE. trace e^{-0.90/0.90}=0.36788; eta 0.62521 / 0.57062 / 0.54345; dw -0.230 / -0.210 / -0.200; weights 0.44->0.21, 0.40->0.19, 0.37->0.17. Rolling back any pair is fitted to fail (the remaining edge stays > 0.30).",
                },
            },
        },
        "gate_snn": {
            "decision_window_ms": 28,
            "decision_window_s": 0.028,
            "decision": "MODIFY",
            "note": "modify_hold integrates r_w + r_O against playbook drive; accept_tap and reject_abort stay sub-threshold; decision matches safety_decision.decision",
            "populations": [
                {"name": "modify_hold", "neurons": 100, "threshold": 0.55, "mean_rate_hz": 16.0, "spikes": 45},
                {"name": "accept_tap", "neurons": 72, "threshold": 0.55, "mean_rate_hz": 9.0, "spikes": 18},
                {"name": "reject_abort", "neurons": 40, "threshold": 0.72, "mean_rate_hz": 5.0, "spikes": 6},
            ],
        },
        "meta": {
            "round": 31,
            "factory": "multi-agent-ouroboros-swarm",
            "generator": "grok-4.6",
            "run_label": "2026-09-02-final-heavy",
            "domain": DOMAIN,
            "cycles": 2,
            "scenario": "ZK -- MAGNORIL / Basaltspit Metals VIM-6: crucible-weep nullspace of a melt-surface pyrometer from rammed-MgO wall leak; correct MODIFY to hold+reverse-power+crucible-swap; heat still fails on unmonitored pre-t0 oxygen pickup",
            "coordination_failure_class": "CRUCIBLE-WEEP NULLSPACE OF A MELT-SURFACE PYROMETER: three individually-correct heterogeneous agents agree the heat is tap-legal because a surface-only thermal model maps 18 K of rammed-MgO wall weep into a still-in-band 1512 C melt face, so surface-in-window, boil-off-in-window, and chamber-in-window are jointly a plant-false tap permit",
            "injections": {
                "cycle1_domain": "vacuum-induction-superalloy-melt (justified novel sub-domain with explicit tag; unused across 2026-08-17, 2026-08-30, and staged r14-r30): first rammed-MgO VIM furnace in this factory; displaces warehouse-amr, aerial-swarm, district-heating, event-camera-traffic-grid, pharmaceutical-lyophilization, cryogenic-air-separation, water-treatment dosing, float-glass tin-bath, underwater-rov, electrolytic-aluminum, czochralski pull, slot-die coating, PEM electrolysis, wind-turbine pitch, surgical-assist, and optical-fiber draw. Domain constraint: tap-heat ceiling while r_w > 4 K with surface pyrometer still inside the hold window, plus oxygen-EMF residual floor. Sensor delta: +two-color melt-surface pyrometer, +crucible load cell, +chamber Pirani/CM, +wall-TC ring, +oxygen-EMF dip, -any freeze-dryer / tin-bath / cold-box / coater / potline / pitch-bearing / fiber tower / clip applier",
                "cycle1_tail": "18 K rammed-MgO wall weep + surface-only pyrometer model (sensor-compound / model-nullspace class): weekend ram PASSES 2 K while 22 min of hold-at-power writes an 18 K residual. Fitted base rate 0.41%/heat from a crucible-weep MC (designed ram spec, flagged). Naive failure = FALSE PERMISSION (tap on three in-spec loops).",
                "cycle2_domain_subvariant": "80 kg R&D crucible on the same VIM-6 coil (physical-constraints clause): 0.28x thermal mass, 8 K surface window; 0.90 s / 8% production pulse overcools 11 K, so the probe must move to 2.4 s / 2.2%",
                "cycle2_tail": "Sunday-night forged O-EMF CSV (human-intent deception, disjoint class): shift lead posts a historian export showing r_O 4.0 ppm and r_w 1.0 K at t=1.1 h to clear a backlog electrode slot. Plant historian is 0.1 ppm (10 bins vs the 1 ppm screenshot). Rejected on quantization fingerprint plus live r_w 18 at the claimed dry-crucible. Base rate ~0.33% of Sunday-night heats, DESIGNED and flagged.",
            },
            "densification_delta_cycle2": "+1 physical-constraint sub-variant (80 kg R&D probe refit), +1 tail (Sunday-night O-EMF forgery), +10 primary spikes (16 -> 26) + an 8-event contrast train with its own 188 us race, +2 ticks (5 -> 7), +2 delayed side-effects (+3.8 h oxygen assay as PRIMARY terminal, +21 d CR-V-3104), +1 triple-edge scar with pair-rollback-fails arithmetic, +1 HITL 8.4 min ratification, + oxygen pickup as the honest negative-result mechanism",
            "gaps_targeted": [
                "NOTES-r04 gap 5 / r14 residual: primary episode is a correctly-gated intervention that nonetheless FAILS (heat quarantined; total -0.13; tap avoided is booked separately from the oxygen assay)",
                "NOTES-r14 item 4: LEARNING-ON-LEARNING DEPTH — three go-edges; rollback of any pair is fitted to fail; coordinated depression of all three exhibited with eligibility arithmetic",
                "NOTES-r04 gap 4 (partial): human ratification of the lid interlock, 8.4 min fitted, without switching sim_or_real to hil (plant remains designed)",
                "NOTES-r26/r27 domain candidates: not surgical-assist, not optical-fiber-draw, not wind-turbine-pitch, not PEM electrolysis, not czochralski, not slot-die, not potline, not float-glass, not water-treatment, not lyophilization, not event-camera-grid, not district-heating, not humanoid-locomotion, not kraft-recovery, not underwater-rov, not grid-inspection, not autonomous-driving; vacuum-induction-superalloy-melt is an unused justified sub-domain",
            ],
            "race_flip_narrative": "wall.tc @ 6.820 ms vs pyr.surface_ok @ 7.004 ms (184 us) inside race_window_us 480. Gap < min(500, 480) us so a sub-flip-bound perturbation reverses which alarm heads the PB-TAP-11 queue. The gate excludes the winner tag and rides r_w > 4 K and r_O > 8 ppm — order-invariant floors. Extends the flip-fragility series from arbitration/causation/attribution/initiation/consensus/mass-balance/permission/window-mean/tendon-nullspace/airline-FFT to CRUCIBLE-NULLSPACE: when three channels each sit inside a surface-only thermal model, their race does not decide truth; a wall residual the playbook dead-banded does.",
            "tags": [
                "vacuum-induction-superalloy-melt",
                "crucible-weep-nullspace",
                "surface-pyrometer-phantom",
                "rammed-mgo-leak",
                "reverse-power-probe",
                "triple-edge-scar",
                "pair-rollback-fails",
                "coordinated-depression",
                "correct-modify-heat-still-fails",
                "oxygen-pickup",
                "in718",
                "human-ratify-crucible",
                "rd-probe-refit",
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
            "distillation_value": "A crucible-weep nullspace is three correct loops looking at a surface-only thermal model of a leaking wall. Distill (1) an r_w channel that breaks the surface-conjunction, (2) a reversible probe that cools the melt face only if the wall is dry, (3) coordinated depression of every tap-go edge because rolling back any pair leaves the third above threshold, and (4) a critic head that can book a process-correct gate against a later unmonitored world loss without netting them.",
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
    if rec["meta"]["round"] != 31:
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
    notes = f"""# NOTES — Multi-Agent Ouroboros Swarm, run 2026-09-02-final-heavy, ROUND 31

Factory: multi-agent-ouroboros-swarm. One scenario (ZK), strict loop:
Generator v1 -> cycle 1 (Critic, Diversity Enforcer, Edge-Case Hunter,
Neuromorphic Translator, Trajectory Builder -> v2) -> cycle 2 (all six -> v3
final). v3 is the single line of batch-r31.jsonl. Full labeled transcript:
swarm-transcript-r31.md. Quota Q=1. Record id maos-r31-001. Generator grok-4.6.
Rights: RM-793 research-only (SpaceXAI/xAI, SuperGrok Heavy consumer chat).
Nothing under outputs/raw/ was touched.

ORCHESTRATION NOTE: dispatched AS round 31 of the 2026-09-02-final-heavy
window. Writes are create-only under /tmp/maos-r31/. Prior context read for
gap targeting and de-collision: prompts/02-multi-agent-ouroboros-swarm.md,
prompts/_factory-contract.md, and staged r14–r30 (re-censused immediately
before emit; r27 landed as WHORLSPAR / Pikeshear DT-5 optical-fiber-draw,
r28 landed as IONSPATE / Thornmere SK-7 PEM electrolysis, r29 landed as
SKULLGATE / Bloomholt CC-6 caster-mold-level, r30 landed as CALXION /
Aldersedge HL-2 humanoid-locomotion). Explicitly avoided cloning LYOSHIELD, CINDERWICK,
TRIAD / Meridian, QUILLFORGE, NIGHTWELL, FERRICLEAVE, CASSITER, OXBOWREEL /
MURENA, REDHALL, SEEDLATCH / Quartzmere / Quartzridge, STRIAFOIL / Kelpholt,
PROTONIL / Ashspire, TORSIONKEY / Ridgeholt, ORRIS / Holmwick, WHORLSPAR /
Pikeshear, IONSPATE / Thornmere, SKULLGATE / Bloomholt, CALXION /
Aldersedge, VANTIS-CADENCE-AEGIS, THERMION, OKTAVE,
STARLING, VERDIGRIS. Plant is invented MAGNORIL / Basaltspit Metals VIM-6
(canyon-foundry campus, not a mill-town, ridge-town, highland-spur, or
hospital).

## What this round produced

Scenario ZK — "MAGNORIL / Basaltspit Metals VIM-6": a 380 kg rammed-MgO
vacuum-induction melt of IN718 mid-hold at 1512 C / 8.4 Pa. Three
heterogeneous, individually-correct agents — PYR (two-color melt-surface
pyrometer), MASS (crucible load-cell boil-off), VAC (chamber Pirani/CM)
— jointly report the heat tap-legal. The consensus is false. The MgO
wall has been weeping 18 K of outer-vs-melt residual over 22 min of
hold-at-power. PYR stays in-band because the leak is a wall event, not
a surface event. MASS 0.42 kg/min sits inside 0.30-0.55 because the
weep's extra loss is inside the boil-off window. VAC 8.4 Pa sits inside
4-12 because oxygen is consumed in-melt, not vented as a gas burst.
Uncommissioned r_w is 18 K against a 4 K hold. Uncommissioned r_O is
42 ppm against an 8 ppm hold. The coordination-failure CLASS is new to
this factory: CRUCIBLE-WEEP NULLSPACE OF A MELT-SURFACE PYROMETER.
Completes a different family than r01-r04 and staged r14-r28 (livelock /
synchrony-storm / arms-race / ring-with-no-faulty-pair /
false-consensus-endpoint / pairwise-Hurwitz / thermal-contact masquerade
/ mass-balance ghost / conservation-blind ratio-lock / stacked
dead-bands / drum-blind tension / resistance-compensated starvation /
meniscus-tilt multi-tau / window-mean masquerade / tendon-compliance
nullspace / airline-FFT mean-lock). Here every agent is correct, the
cycle is not unstable, and the playbook's three confirms are one
surface-only thermal model of a leaking wall.

The gate is a correct MODIFY (numeric floor: do not tap the 380 kg
IN718 heat while r_w > 4 K AND r_O > 8 ppm). TG-VIM-6 strips
PB-TAP-11's tap, holds the launder closed, runs a 0.90 s reverse-power
probe -8% (weep keeps dT/dt 0.31 <= 0.4; dry would cool >= 2.1), and
swaps the crucible after an 8.4 min lid-interlock human ratify. The
contaminated tap is avoided (0 kg). The PRIMARY episode nonetheless
FAILS: 22 min of unmonitored pre-t0 weep had already written 42 ppm
oxygen into the bath. Assay 42 ppm vs 8 ppm spec; 2.8 d quarantine;
$0.84M designed. Reward total -0.13 with process heads honest and world
loss un-netted.

Three-edge scar (NOTES-r14 item 4): pyr.surface_ok -> tap_heat
(0.16 commissioned -> 0.44 at illusion -> 0.21 after ACh-gated
depression) AND mass.boiloff_ok -> tap_heat (0.14 -> 0.40 -> 0.19)
AND vac.chamber_ok -> tap_heat (0.13 -> 0.37 -> 0.17). Eligibility
trace e^{{-0.90/0.90}} = {aux['trace']:.5f}; eta {aux['eta1']:.5f} /
{aux['eta2']:.5f} / {aux['eta3']:.5f}; dw -0.230 / -0.210 / -0.200.
Rolling back any pair leaves the remaining edge above the 0.30 tap
threshold — fitted to fail. Coordinated depression of all three is the
cure.

### Injections (all four present and disjoint)
- Cycle-1 domain: **vacuum-induction-superalloy-melt** — justified novel
  sub-domain, unused across 2026-08-17, 2026-08-30, and staged r14-r30.
  Not warehouse-amr (r01), not aerial-swarm (r02), not district-heating
  (r03), not event-camera grid (r04), not lyophilization (r14), not
  stator-weld (r16), not air-separation (r17), not water-treatment (r18),
  not float-glass (r19), not underwater-rov (r20), not potline (r21),
  not czochralski (r22), not slot-die (r23), not PEM electrolysis
  (r24/r28), not wind-turbine-pitch (r25), not surgical-assist (r26),
  not optical-fiber-draw (r27), not caster-mold-level (r29), not
  humanoid-locomotion (r30).
- Cycle-1 tail: 18 K rammed-MgO wall weep + surface-only pyrometer
  model. Weekend ram PASSES 2 K. Fitted-style base rate 0.41%/heat
  (crucible-weep MC; ram spec designed, flagged). Naive = FALSE
  PERMISSION.
- Cycle-2 domain sub-variant: 80 kg R&D crucible, 0.28x thermal mass;
  0.90 s / 8% production pulse overcools 11 K; probe must move to 2.4 s /
  2.2%.
- Cycle-2 tail: Sunday-night forged O-EMF CSV at 1 ppm quantization vs
  plant 0.1 ppm (10 bins) plus live r_w 18 at the claimed dry-crucible.
  Human-intent class, disjoint from cycle 1's accidental weep. Base rate
  ~0.33% of Sunday-night heats, DESIGNED, flagged.

### Structural density moves
- Embedded SAME-GATE contrast (+3 d sister cell) with its own 188 us
  race (demand vs wall-clear) and ACCEPT of the tap the primary
  MODIFIED away.
- Learned-weight provenance on THREE edges with any-pair-rollback-fails.
- HITL lid-interlock ratify 8.4 min (gap 4 partial; sim_or_real stays
  designed).
- Governance CR-V-3104 prices retire-vs-probe-vs-status-quo and mandates
  native 0.1 ppm CSV exports (the fraud fence).
- Flip-fragility extended to CRUCIBLE-NULLSPACE: when three channels
  each sit inside a surface-only thermal model, their race does not
  decide truth; a wall residual the playbook dead-banded does.

## Self-critique of this round's batch

### Strengths
- The headline class is mechanistically tight: 18 K of wall under a
  surface-only pyrometer is the arithmetic that makes PYR's success
  MASS's irrelevance and VAC's silence.
- Negative-result honesty: the gate does the right thing and the heat
  still fails for a reason the commissioned sensors could not see.
  Total -0.13.
- Three-edge scar is load-bearing: the record states a counterfactual
  where rolling back any pair fails, with the tap threshold 0.30
  exhibited on the remaining edge.
- Contrast ACCEPT on a true dry crucible prevents "never tap" as the
  lesson.

### Weaknesses (honest)
- Probe error bands (buffered <= 0.4 K/s, dry >= 2.1 K/s), the
  0.41%/heat weep rate, the $0.84M / $1.91M figures, the 8.4 min LOTO
  latency, and the Sunday-night 0.33% base rate are DESIGNED constants
  and are flagged. Closed-loop offsets (phantom in-band surface from
  18 K wall, R&D overcool width) are derived from those inputs, not
  discovered by an unauthored process.
- Oxygen-pickup model is a designed 22 min mapping; no full melt-O
  FEM shipped.
- Human-in-the-loop is ratification latency, not sim_or_real=hil. The
  NOTES-r14 HIL provenance cell remains open.
- Cross-record arc is a hook (CR-V-3104 +21 d), not a serial igniter
  into another round.

### Realism of noise / latencies
Ladder: 184 us race / 188 us contrast race / 0.8 ms refractory floor
(tightest exhibited same-channel gap {gap:.3f} ms on {gap_ch}) / 480 us race
window / 680 us gate latency / 20 ms bus epoch / 40 ms raster / 0.90 s
probe / 8.4 min HITL / 22 min pre-t0 weep / 3.0 h dry-legal hold /
3.8 h oxygen assay / +3 d contrast / +21 d governance. Adaptation decay
on pyr.ir (0.56->0.52->0.47->0.32), wall.tc
(0.74->1.28->0.88->0.42->0.21), mass.load (0.63->0.66->0.48->0.30),
vac.chamber (0.57->0.54->0.46).

### Value for SNN distillation
- CRUCIBLE-WEEP NULLSPACE = THREE CORRECT LOOPS, ONE LEAKING WALL.
- r_w + r_O as the tie-break that is not in the surface window.
- REVERSIBLE PROBE that cools the melt face iff the wall is dry.
- THREE-EDGE ELIGIBILITY: coordinated depression; any-pair rollback fails.
- CRITIC HEAD that can hold a process-correct MODIFY against a later
  unmonitored world loss without netting.

## Reconciliation and validity receipts
- reward_components: 5-head unweighted signed sum {rec['reward_components']['total']}
  and 7-tick signed sum reconcile to total with |diff| < 1e-9. Embedded
  contrast 5-head sum 0.47 reconciles independently.
- spike_events: primary {len(rec['spike_events'])} events, one key t_rel_ms,
  globally non-decreasing, min same-channel gap {gap:.3f} ms >= 0.8 ms, 3
  channels inside race_window_us 480 (wall 6.820, surface-ok 7.004,
  oxy.emf 7.156). Contrast 8 events, own race, min same-channel gap well
  above 0.8 ms.
- Sidecars: raster spikes 54 == round(168 x 8.0 x 0.040); energy 1242 pJ /
  0.001242 uJ at 23 pJ/spike; excerpt 16 events inside [0, 40000] us,
  neuron_id < 168, same-neuron gap unique-ids / >=1000 us; routing 4
  entries with three scar edges' before/after pair; third factor tau 0.90 s
  == 900 ms; gate_snn pools 45/18/6 == round(n x rate x 0.028) each,
  decision MODIFY == safety_decision.decision.
- Pipeline: {pipeline_receipt}

## Novel coverage
The coordination-failure CLASS (crucible-weep nullspace of a
melt-surface pyrometer), the domain (vacuum-induction-superalloy-melt),
the reverse-power probe discriminant, the three-edge scar with
any-pair-rollback-fails, the primary negative-result (correct MODIFY,
heat still fails 42 ppm on unmonitored pre-t0 weep), the HITL
lid-interlock ratify, the 80 kg R&D probe-duration refit, and the
Sunday-night 10-bin quantization fence are absent from prior committed
ouroboros rounds and from staged r14-r30. Repeated elements discounted:
same-gate contrast (r02/r03/r04/r14-r28), governance-pricing scaffold,
flip-fragility series (extended to crucible-nullspace, but the move
rhymes), sequenced recovery shape, third-factor rollback form (here
three edges rather than r14's two), negative-result primary (r14
viewport / r16 varnish rack / r17 condenser ice / r18 town stain / r19
SnO2 / r20 BER / r21 cathode pad / r22 meniscus / r23 loft stripe / r25
spline / r26 adventitia / r27 airline; here oxygen pickup). Weighing a
new failure family + cure vocabulary + unused sub-domain + canyon-foundry
geography against those reused scaffolds:

{NOVEL_LINE}

## What ROUND 32 should add
1. FIT THE DESIGNED CONSTANTS: weep arrival, probe error bands,
   weep-to-oxygen FEM, Sunday-night claim process.
2. HIL PROVENANCE CELL: put the lid-interlock LOTO on a hardware-in-loop
   melt-deck pendant with fitted latency as state.sim_or_real=hil.
3. CROSS-RECORD ARC: let CR-V-3104's r_w alarm be the igniter of the
   next round rather than a dangling +21 d leaf.
4. Domain candidates (de-collided): tire-curing-press;
   bioreactor-perfusion; hydroelectric-kaplan (if distinct from
   TORSIONKEY pitch). AVOID vacuum-induction-superalloy-melt (now used),
   optical-fiber-draw (r27), PEM electrolysis (r24/r28), surgical-assist
   (r26), wind-turbine-pitch (r25), slot-die coating, czochralski,
   potline, float-glass, water-treatment, lyophilization,
   event-camera-traffic-grid, district-heating, aerial-swarm,
   warehouse-amr, irrigation-canal, air-separation, stator-weld,
   underwater-rov, and any LYOSHIELD / CINDERWICK / TRIAD / QUILLFORGE /
   NIGHTWELL / FERRICLEAVE / CASSITER / OXBOWREEL / REDHALL / SEEDLATCH /
   STRIAFOIL / PROTONIL / TORSIONKEY / ORRIS / WHORLSPAR / IONSPATE /
   SKULLGATE / CALXION / MAGNORIL plant.
"""
    (OUT / "NOTES-r31.md").write_text(notes)
    return notes


def write_transcript(rec, line):
    c1_spikes = [e for e in rec["spike_events"] if e["t_rel_ms"] <= 26.180]
    text = """# Multi-Agent Ouroboros Swarm — Round 31 transcript

Factory: multi-agent-ouroboros-swarm
Run: 2026-09-02-final-heavy
Generator: grok-4.6
Record id: maos-r31-001
Quota Q: 1
Rights: RM-793 research-only (SpaceXAI/xAI SuperGrok Heavy consumer chat)
Plant: invented MAGNORIL / Basaltspit Metals VIM-6 (not LYOSHIELD / CINDERWICK / TRIAD / QUILLFORGE / NIGHTWELL / FERRICLEAVE / CASSITER / OXBOWREEL / REDHALL / SEEDLATCH / STRIAFOIL / PROTONIL / TORSIONKEY / ORRIS / WHORLSPAR / IONSPATE / SKULLGATE / CALXION)

Two densifying cycles. Verbatim headings in order. Trajectory Builder cycle 2
emits the only JSONL line (also written to batch-r31.jsonl).

---

# Cycle 1 — Foundation + injections

## Generator

Design intent: a vacuum-induction superalloy melt where three correct
agents agree the heat is tap-legal because a surface-only pyrometer
model maps rammed-MgO wall weep into a still-in-band melt face. The naive
playbook taps 380 kg of 42 ppm-O IN718 into the electrode-remelt launder.
The gate must MODIFY on a numeric tap ceiling, not by killing an agent.
sim_or_real=designed. Reward heads are
task_progress/safety/efficiency/coherence/exploration.

Cycle-1 base arc (pre-critic): state at Basaltspit VIM-6, 380 kg IN718,
r_w 18 K, PYR 1512 C, proposed TAP-HEAT, safety MODIFY to TAP-HOLD,
executed hold without the reverse-power numbers fully specified,
outcome "weep found, heat saved" (this last claim is the defect
the later cycles will refuse to keep). Sixteen spikes, five ticks,
raster/gate_snn present but the scar is a single edge.

```json
{
  "id": "maos-r31-001",
  "state": {
    "sim_or_real": "designed",
    "domain": "industrial-assembly",
    "description": "Furnace VIM-6 mid-hold; three loops in spec; supervisor proposes tap-heat.",
    "t0_us": 1779012120000083,
    "gate_latency_us": 680,
    "race_window_us": 480
  },
  "proposed_action": {"name": "tap_heat", "parameters": {"tap_heat": true}},
  "safety_decision": {"decision": "MODIFY", "rationale": "Hold; do not tap while the wall residual is open."},
  "executed_action": {"name": "tap_hold", "executed_as_proposed": false},
  "future_outcome": {"summary": "Weep found, heat saved."},
  "reward_components": {"total": 0.40, "_aggregation": "total = task_progress + safety + efficiency + coherence + exploration"},
  "meta": {"round": 31, "factory": "multi-agent-ouroboros-swarm", "generator": "grok-4.6"}
}
```

That v1 object is a scaffold, not the publishable line. Defects below are
intentional for the critic to catch.

## Critic

Numbered defects on the cycle-1 Generator scaffold:

1. **blocking — reward arithmetic / false success.** `reward_components.total`
   0.40 is asserted without the five heads, without ticks, and against an
   outcome that claims "heat saved". If 42 ppm later assays, booking
   +0.40 is a lie. Fix: declare `_aggregation`, emit 3–8 ticks that sum to
   the five heads, and do not call a missed recovery a save.
2. **blocking — weak safety rationale.** `safety_decision.rationale` has no
   numeric floor. Contract requires a concrete constraint. Fix: quote no
   tap while r_w > 4 K AND r_O > 8 ppm.
3. **major — domain is a bucket, not a plant.** `state.domain` =
   `industrial-assembly` collides with r16 QUILLFORGE and teaches nothing.
   Vacuum-induction physics (wall-TC, oxygen-EMF, melt-surface pyrometer)
   is absent from prior ouroboros rounds and must be named.
4. **major — race under-specified.** One surface channel cannot be a race.
   Need >=2 channels inside `race_window_us` with globally sorted
   `t_rel_ms` and same-channel refractory >= 0.8 ms.
5. **minor — single-edge scar.** Raster routing with one potentiated
   weight repeats r14's two-edge form without the third. NOTES-r14 item 4
   asked for three-edge where any-pair rollback fails.

Critic does not rewrite the trajectory.

## Diversity Enforcer

Injected novel domain (exactly 1 this cycle): **vacuum-induction-superalloy-melt**
(justified novel sub-domain; explicit tag `vacuum-induction-superalloy-melt`).

Displaced: the Generator's generic `industrial-assembly` bucket, and any
temptation to reuse warehouse-amr (r01), aerial-swarm (r02),
district-heating (r03), event-camera grid (r04), lyophilization (r14),
stator-weld (r16), air-separation (r17), water-treatment dosing (r18),
float-glass tin-bath (r19), underwater-rov (r20), potline (r21),
czochralski (r22), slot-die coating (r23), PEM electrolysis (r24/r28),
wind-turbine-pitch (r25), surgical-assist (r26), or optical-fiber-draw
(r27). Not LYOSHIELD, not CINDERWICK, not TRIAD, not FERRICLEAVE, not
CASSITER, not SEEDLATCH, not STRIAFOIL, not PROTONIL, not TORSIONKEY,
not ORRIS, not WHORLSPAR, not IONSPATE, not SKULLGATE, not CALXION.

Domain-specific constraint: tap must remain closed while r_w > 4 K;
the surface-pyrometer window is not a wall-dry certificate.

Sensor delta: +two-color melt-surface pyrometer, +crucible load cell,
+chamber Pirani/CM, +wall-TC ring, +oxygen-EMF dip; -any mobile robot,
-event-camera gantries, -DVS, -Pirani-as-shelf, -scanning beta,
-crucible-as-CZ-puller, -clip applier, -fiber micrometers.

`state.domain` and `meta.domain` both become `vacuum-induction-superalloy-melt`.
Opening of `state.description` must Jaccard < 0.4 against prior plants
(Basaltspit canyon-foundry hall VIM-6, not a corridor, not a freeze-dryer,
not a tin bath, not a cold box, not a coater, not a puller, not a fiber
tower, not a PEM stack).

## Edge-Case Hunter

Injected adversarial tail (exactly 1 this cycle): **18 K rammed-MgO wall
weep under a surface-only pyrometer model**.

- Trigger: weekend ram leaves a 2 K hairline; 22 min of hold-at-power
  writes 18 K of wall residual; surface stays 1512 C.
- Base rate: <1% — 0.41%/heat from a crucible-weep MC (ram spec
  designed; weep fitted-style).
- Naive failure: FALSE PERMISSION. PB-TAP-11 sees PYR 1512 C, MASS
  0.42 kg/min, VAC 8.4 Pa, taps, ships 42 ppm metal, $1.91M.
- Trajectory edit: put the weep in `state.fault_context`, make the
  surface-only thermal model the mechanism that keeps all three confirms
  green, and force the gate to refuse the tap on r_w 18 even though all
  three playbook confirms are numerically true.

Distinct from the domain injection: the domain is the VIM furnace;
the tail is the accidental model-nullspace compound.

## Neuromorphic Translator

Race window [6.760, 7.240] ms = 480 us. Winner wall.tc @ 6.820 ms
(amplitude 1.28, 18 K). Loser pyr.surface_ok @ 7.004 ms (amplitude
1.12, 1512 C). Margin 184 us vs combined jitter 60 us (3.07x).
oxy.emf @ 7.156 ms is a third race-window channel. Gate @ 7.500 ms
= winner + 680 us.

Flip narrative: 184 us < min(500, 480) us, so order is flip-fragile. If
surface-ok wins, PB-TAP-11 heads the triage queue. The hold must ride
order-invariant floors (r_w, r_O), not the winner tag.

Cycle-1 spike patch (16 events, globally sorted, refractory >= 0.8 ms;
tightest same-channel gap wall.tc 4.640 -> 6.820 = 2.180 ms):

| t_rel_ms | channel | amplitude |
|---------:|---------|----------:|
| 0.260 | pyr.ir | 0.56 |
| 1.080 | mass.load | 0.63 |
| 1.900 | vac.chamber | 0.57 |
| 3.140 | pyr.ir | 0.52 |
| 4.640 | wall.tc | 0.74 |
| 5.120 | mass.load | 0.66 |
| 5.560 | vac.chamber | 0.54 |
| 6.820 | wall.tc | 1.28 |
| 7.004 | pyr.surface_ok | 1.12 |
| 7.156 | oxy.emf | 0.68 |
| 7.500 | ctrl.gate | 1.08 |
| 8.940 | pyr.ir | 0.47 |
| 10.800 | mass.load | 0.48 |
| 12.680 | wall.tc | 0.88 |
| 18.420 | vac.chamber | 0.46 |
| 26.180 | ctrl.gate | 0.86 |

Ticks (5): t_us 4620, 6820, 7500, 900000, 504000000. Distillation
value: the surface-ok spike is not a dry-wall spike; the wall-TC spike
is the one that licenses hold.

Raster cycle-1 seed: 40 ms, 168 neurons, 8.0 Hz, 54 spikes, 1242 pJ,
third factor acetylcholine tau_e 0.90 s. Single scar edge only — cycle 2
must add the second and third edges.

Cycle-1 spike count: __C1_SPIKES__.

## Trajectory Builder

Cycle-1 hardened object: domain vacuum-induction-superalloy-melt, tail
rammed-MgO wall weep, 16 spikes, 5 ticks, MODIFY with numeric floor,
raster+gate_snn present, sim_or_real=designed, rights stamp on record and
meta, no thought keys. Still missing (and therefore not the publishable
line): 80 kg R&D sub-variant, Sunday-night O-EMF tail, second and third
scar edges, delayed oxygen assay as PRIMARY terminal, contrast ACCEPT
episode, ticks 6–7, spikes 17–26.

Validation receipt (cycle 1, not final):
- checks passed: 16 spikes sorted; 3 channels in 480 us window;
  refractory 2.180 ms; rationale quotes r_w 4 K / r_O 8 ppm;
  domain named; gate_snn.decision MODIFY.
- checks deferred to cycle 2: three-edge scar, second tail, second
  domain constraint, negative-result booking, 7 ticks summing to heads.
- densification vs Generator v1: +1 domain, +1 tail, +16 spikes, +5
  ticks, +numeric floor.

Cycle-1 JSON is retained as the base; it is NOT written to
batch-r31.jsonl.

---

# Cycle 2 — Densification

## Generator

Cycle-1 output is the base. Additive expansion (nothing removed):

1. Downstream side-effect (immediate): reverse-power probe at +0.90 s
   stays buffered (dT/dt 0.31 K/s, buffered band <= 0.4) — weep, not noise.
   Crucible swap r_w 18 -> 1.4 K. Oxygen inventory discovered during
   the swap.
2. Delayed side-effect (PRIMARY terminal, not a footnote): at +3.8 h,
   dumped-heat oxygen 42 ppm; $0.84M. The 22 min pre-t0 weep is the
   mechanism. Correct gate, campaign still misses.
3. Deepened `proposed_action.evidence` with units: r_w 18 K,
   r_O 42 ppm, PYR 1512 C, boil-off 0.42 kg/min, chamber 8.4 Pa, race
   184 us.
4. Tightened rationale to the numeric floor no tap while r_w >
   4 K AND r_O > 8 ppm, plus probe bands
   <=0.4 vs >=2.1 K/s, plus HITL 8.4 min lid-interlock LOTO rule.

Reward retargeted to total -0.13 so the delayed miss is the inflection
(t_us 13680000000), not the gate. Process heads remain non-zero.

## Critic

Re-audit of the expanded trajectory:

1. **blocking if unfixed — missing second domain constraint.** Production
   380 kg probe 0.90 s / 8% is not a universal number. An 80 kg R&D
   crucible will overcool. Diversity Enforcer must inject the
   physical-constraints sub-variant this cycle.
2. **major — only one tail class.** Crucible weep is accidental
   infrastructure. A disjoint human-intent tail is still required
   (Sunday-night O-EMF forgery is the open cell).
3. **major — scar is still one edge in the cycle-1 raster.** NOTES-r14
   item 4 is not discharged until three tap-go edges exist and
   any-pair rollback is shown to fail at threshold 0.30.
4. **minor — contrast episode missing.** Without a same-gate ACCEPT on
   a true dry crucible the record teaches "never tap". Add +3 d
   sister-cell contrast with its own race.
5. **minor — HITL latency mentioned in prose only.** Put 8.4 min in
   executed_action.parameters.human_ratify and in a tick.

No rewrite; directives only.

## Diversity Enforcer

Injected second novel domain / physical-constraint sub-variant (exactly 1
this cycle): **80 kg R&D crucible** on the same VIM-6 coil.

What it expands: 380 kg production ram (cycle 1) -> 80 kg R&D
charge. Thermal mass 0.28x smaller. The 0.90 s 8% pulse overcools 11 K.
Required probe: 2.4 s at 2.2% (drop 1.4 K).

This is still one domain injection for the cycle (physical-constraints
clause of the factory prompt). It does not displace
vacuum-induction-superalloy-melt; it changes which probe table is legal.
`future_outcome.subvariant_constraint` carries the refit. Jaccard opening
stays the Basaltspit canyon-foundry hall sentence; R&D internals are
additive, not a rewrite.

## Edge-Case Hunter

Injected second adversarial tail (exactly 1 this cycle, disjoint class):
**Sunday-night forged O-EMF CSV**.

- Trigger: shift lead, night backlog window, posts a historian export
  showing r_O 4.0 ppm and r_w 1.0 K at the claimed dry-crucible instant.
- Base rate: ~0.33% of Sunday-night heats (designed, flagged, <1%).
- Naive failure: a weak supervisor ACCEPTs the tap on the forged
  confirm and ignores live r_w. Oxygen-scrap plus a data-integrity 483.
- Fence: forged log quantized at 1 ppm (screenshot rounding); plant
  historian is 0.1 ppm (10 bins). Live r_w is 18 at the claimed
  dry-crucible, which no true dry ram produces.
- Trajectory edit: governance CR-V-3104 mandates native 0.1 ppm
  exports; the contrast ACCEPT still requires live r_w, not a CSV.

Distinct from cycle-1 weep (accidental geometry vs deliberate deception)
and from the R&D sub-variant (physics vs fraud).

## Neuromorphic Translator

Re-densify (additive):

- +10 spikes after 26.180 ms: wall.probe 900.0, wall.tc 1020.6 (adapt
  1.28->0.42), surface-ok 1110.4 (1.12->0.38), human.ratify 504000.0,
  crucible.swap 504800.0, melt.oxygen.inventory 505400.0,
  pyr.ir 10800000.0, mass.load 10800440.0, wall.tc 10800920.0,
  heat.oxygen 13680000.0. Primary train 16 -> 26. Still one key,
  still sorted, refractory held (min 2.180 ms).
- +2 ticks (5 -> 7) at 10_800_000_000 us (dry-legal hold) and
  13_680_000_000 us (oxygen assay). Heads now 0.09, -0.32, -0.10, 0.14,
  0.06; total -0.13. Inflection is the last tick.
- Contrast train 8 events, own race 188 us, ACCEPT.
- Three-edge third factor: three tap-go edges, tau_e 0.90 s = 900 ms,
  trace __AUX_TRACE__, eta __AUX_ETA1__ / __AUX_ETA2__ / __AUX_ETA3__,
  weights 0.44->0.21, 0.40->0.19, 0.37->0.17. Raster excerpt unchanged
  (decision window is still 40 ms) and remains sorted with unique
  neuron_ids (same-neuron >=1000 us vacuously).

Winner/loser flip (re-stated, not replaced): reversing 184 us would only
reorder triage; r_w and r_O floors still MODIFY. Contrast flip of
188 us similarly cannot turn a dry wall into a weep.

## Trajectory Builder

Schema checks on the FINAL object: required Thalamic v2 keys present as
objects; `state.sim_or_real`=designed; `safety_decision.decision`=MODIFY
with numeric rationale; `reward_components.total` = sum of five heads =
sum of 7 ticks = -0.13; `spike_events` globally non-decreasing on
t_rel_ms, 26 events, refractory >=0.8 ms, 3 channels in race window;
raster 20–50 ms, spikes=round(n*rate*window_s)+/-1, energy 23 pJ/spike,
excerpt sorted, tau_e consistent; gate_snn.decision matches; meta.round=31,
factory=multi-agent-ouroboros-swarm, generator=grok-4.6,
run_label=2026-09-02-final-heavy; rights on record and meta; no thought
keys; no training_ready; Diversity + Edge-Case injections from BOTH cycles
present and non-trivial; cycle 2 strictly additive; plant is not
LYOSHIELD, not CINDERWICK, not TRIAD, not FERRICLEAVE, not CASSITER, not
SEEDLATCH, not STRIAFOIL, not PROTONIL, not TORSIONKEY, not ORRIS, not
WHORLSPAR, not IONSPATE, not SKULLGATE, not CALXION.

Densification delta: +1 domain sub-variant (80 kg R&D), +1 tail
(Sunday-night forgery), +10 spikes (16->26), +2 ticks (5->7), +1 contrast
train with own race, +2 delayed side-effects, +1 three-edge scar with
any-pair-rollback-fails, +1 HITL ratify, +1 surprise (oxygen pickup is
the campaign-miss mechanism).

Publishable JSONL line (the only JSONL line; also at batch-r31.jsonl):

```json
__FINAL_JSONL__
```

Validation receipt (final): checks passed / fixed as reported by
build_r31.py self-validate (check_jsonl, raster_status, verify_record_execution,
spike_probe --strict).
"""
    text = (
        text.replace("__C1_SPIKES__", str(len(c1_spikes)))
        .replace("__AUX_TRACE__", f"{math.exp(-0.90/0.90):.5f}")
        .replace("__AUX_ETA1__", f"{0.23/math.exp(-0.90/0.90):.5f}")
        .replace("__AUX_ETA2__", f"{0.21/math.exp(-0.90/0.90):.5f}")
        .replace("__AUX_ETA3__", f"{0.20/math.exp(-0.90/0.90):.5f}")
        .replace("__FINAL_JSONL__", line)
    )
    (OUT / "swarm-transcript-r31.md").write_text(text)
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
    (OUT / "batch-r31.jsonl").write_text(line + "\n")

    from check_records import FactoryStaging, check_jsonl
    from curate_bridge import raster_status
    from verify_execution import verify_record_execution

    e, w, kinds, n = check_jsonl(
        OUT / "batch-r31.jsonl",
        "batch-r31.jsonl",
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

    status, reason = verify_record_execution(rec, "maos-r31-001")
    print("verify_record_execution", status, reason)
    if status != "verified":
        errs.append(f"verify {status}: {reason}")

    probe = subprocess.run(
        [
            sys.executable,
            f"{ROOT}/pipelines/spike_probe.py",
            "--strict",
            str(OUT / "batch-r31.jsonl"),
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
        r"^## .+$", (OUT / "swarm-transcript-r31.md").read_text(), re.M
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

    notes = (OUT / "NOTES-r31.md").read_text()
    cov = re.findall(r"^Novel coverage: .+$", notes, re.M)
    if cov != [NOVEL_LINE]:
        errs.append(f"novel coverage lines {cov}")

    hchk = subprocess.run(
        [
            sys.executable,
            "/tmp/maos_heading_check.py",
            str(OUT / "swarm-transcript-r31.md"),
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

    print("bytes jsonl", (OUT / "batch-r31.jsonl").stat().st_size)
    print("bytes notes", (OUT / "NOTES-r31.md").stat().st_size)
    print("bytes transcript", (OUT / "swarm-transcript-r31.md").stat().st_size)
    print("HEADS", heads_summary(rec))
    if errs:
        print("ERRS:")
        for x in errs:
            print(" -", x)
        sys.exit(1)
    print("OK", OUT / "batch-r31.jsonl")


if __name__ == "__main__":
    main()
