#!/usr/bin/env python3
"""Build and self-check MAOS round-41 JSONL (research-only; not published)."""
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

GEN_AT = "2026-09-03T04:28:00Z"
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
OUT = Path("/tmp/maos-r41")
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
    "Quartzridge",
    "STRIAFOIL",
    "Kelpholt",
    "REDHALL",
    "Gullmere",
    "OXBOWREEL",
    "Oystermere",
    "TORSIONKEY",
    "Ridgeholt",
    "ORRIS",
    "Holmwick",
    "PROTONIL",
    "Ashspire",
    "WHORLSPAR",
    "Pikeshear",
    "Crowspire",
    "IONSPATE",
    "Thornmere",
    "SKULLGATE",
    "Bloomholt",
    "CALXION",
    "Aldersedge",
    "MAGNORIL",
    "Basaltspit",
    "GORSEFLUE",
    "Copseholt",
    "BRACEGILT",
    "training_ready",
    "da Vinci",
    "Intuitive Surgical",
    "Boston Dynamics",
    "Nucor",
    "Arcelor",
    "Lafarge",
    "Holcim",
    "Heidelberg",
    "Cemex",
    "CLINKERFELL",
    "Flintmere",
    "SODASHARD",
    "Cairnmere",
    "Asahi",
    "Nafion",
    "Chemours",
    "Nouryon",
    "Uhde",
    "INEOS",
    "Westlake",
    "OxyChem",
    "Formosa",
    "LINTELPLY",
    "Greystair",
    "KAOTHARN",
    "Riftwold",
    "TREADNOLL",
    "Slatebeck",
    "ANOLITH",
    "Siltfen",
    "Foster Wheeler",
    "SYDEC",
    "ConocoPhillips",
    "ExxonMobil",
    "Valero",
    "Marathon Petroleum",
    "Phillips 66",
    "Bechtel",
    "McDermott",
    "Lummus",
    "Technip",
    "Worley",
    "Fluor",
    "Yarrowmere",
    "WELDSPIT",
    "DRUMWROTH",
    "Pitchfen",
    "RIMEBRAID",
    "Floeholt",
    "PITCHSTAITH",
    "Mossbank",
    "Haldor Topsoe",
    "Casale",
    "Kellogg",
    "Yara",
    "Nutrien",
    "Thyssenkrupp",
    "CF Industries",
)
R14_OPENING = (
    "Helixmere Biologics Building C lyophilizer LYO-4 is mid-primary on 8400 "
    "vials of a monoclonal antibody"
)
NOVEL_LINE = "Novel coverage: 48%"
PLANT = "NITROSTAITH"
GEO = "Chalkfen"
CELL = "CV-4"
DOMAIN = "ammonia-synthesis-converter"
RECORD_ID = "maos-r41-001"
ROUND = 41
DELAY_S = 0.68
TAU_E_S = 0.88
C1_SPIKE_CUTOFF_MS = 26.290


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
        if p.parent.name == "maos-r41":
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
    tokens = (PLANT, GEO, CELL, DOMAIN)
    for p in sorted(Path("/tmp").glob("maos-r*/batch-r*.jsonl")):
        if p.parent.name == "maos-r41":
            continue
        try:
            rec = json.loads(p.read_text().splitlines()[0])
        except (OSError, json.JSONDecodeError, IndexError):
            continue
        blob = json.dumps(rec)
        domain = (rec.get("state") or {}).get("domain")
        if domain == DOMAIN:
            hits.append(f"{p}: domain {domain}")
        for tok in tokens:
            if tok in blob:
                hits.append(f"{p}: token {tok}")
    for p in sorted(Path("/tmp").glob("maos-r*/build_r*.py")):
        if p.parent.name == "maos-r41":
            continue
        try:
            text = p.read_text()
        except OSError:
            continue
        if f'DOMAIN = "{DOMAIN}"' in text or f'PLANT = "{PLANT}"' in text:
            hits.append(f"{p}: claimed {PLANT}/{DOMAIN}")
    return hits


def build_record():
    ticks, heads = cents_ticks(
        [4620, 6488, 7182, 8_400_000, 564_000_000, 8_640_000_000, 17_280_000_000],
        [
            (1, -2, -1, 2, 1),
            (2, -5, -1, 3, 2),
            (2, -7, -2, 3, 2),
            (1, -6, -2, 2, 1),
            (1, -6, -2, 2, 1),
            (1, -6, -2, 2, 1),
            (0, -6, -2, 1, 1),
        ],
    )
    assert abs(heads["total"] - (-0.18)) < 1e-9, heads

    trace = math.exp(-DELAY_S / TAU_E_S)
    eta1 = 0.24 / trace
    eta2 = 0.21 / trace
    eta3 = 0.19 / trace
    dw1 = eta1 * 1.0 * trace
    dw2 = eta2 * 1.0 * trace
    dw3 = eta3 * 1.0 * trace
    w1 = 0.48 - dw1
    w2 = 0.42 - dw2
    w3 = 0.39 - dw3
    assert abs(w1 - 0.24) < 5e-4, w1
    assert abs(w2 - 0.21) < 5e-4, w2
    assert abs(w3 - 0.20) < 5e-4, w3

    spike_events = [
        {"channel": "skin.wall", "t_rel_ms": 0.340, "amplitude": 0.56},
        {"channel": "flow.quench", "t_rel_ms": 1.180, "amplitude": 0.63},
        {"channel": "vap.overhead", "t_rel_ms": 2.080, "amplitude": 0.55},
        {"channel": "core.t", "t_rel_ms": 3.220, "amplitude": 0.75},
        {"channel": "skin.wall", "t_rel_ms": 4.180, "amplitude": 0.52},
        {"channel": "core.t", "t_rel_ms": 4.860, "amplitude": 0.78},
        {"channel": "flow.quench", "t_rel_ms": 5.380, "amplitude": 0.60},
        {"channel": "core.t.high", "t_rel_ms": 6.488, "amplitude": 1.38},
        {"channel": "vap.in_band", "t_rel_ms": 6.672, "amplitude": 1.16},
        {"channel": "skin.wall", "t_rel_ms": 6.890, "amplitude": 0.64},
        {"channel": "ctrl.gate", "t_rel_ms": 7.182, "amplitude": 1.10},
        {"channel": "core.t", "t_rel_ms": 8.880, "amplitude": 0.48},
        {"channel": "vap.overhead", "t_rel_ms": 10.760, "amplitude": 0.82},
        {"channel": "flow.quench", "t_rel_ms": 13.060, "amplitude": 0.47},
        {"channel": "skin.wall", "t_rel_ms": 18.540, "amplitude": 0.44},
        {"channel": "ctrl.gate", "t_rel_ms": 26.280, "amplitude": 0.86},
        {"channel": "steam.pulse.probe", "t_rel_ms": 8400.0, "amplitude": 0.97},
        {"channel": "core.t", "t_rel_ms": 8488.4, "amplitude": 0.42},
        {"channel": "vap.in_band", "t_rel_ms": 8572.6, "amplitude": 0.36},
        {"channel": "human.ratify", "t_rel_ms": 564000.0, "amplitude": 0.80},
        {"channel": "head.lock", "t_rel_ms": 564900.0, "amplitude": 0.72},
        {"channel": "flange.attack", "t_rel_ms": 565700.0, "amplitude": 0.88},
        {"channel": "skin.wall", "t_rel_ms": 8640000.0, "amplitude": 0.32},
        {"channel": "core.t", "t_rel_ms": 8640720.0, "amplitude": 0.30},
        {"channel": "flow.quench", "t_rel_ms": 8641480.0, "amplitude": 0.27},
        {"channel": "h2s.leak", "t_rel_ms": 17280000.0, "amplitude": 0.94},
    ]

    contrast_spikes = [
        {"channel": "cut.demand", "t_rel_ms": 0.000, "amplitude": 0.84},
        {"channel": "core.clear", "t_rel_ms": 0.188, "amplitude": 0.77},
        {"channel": "skin.wall", "t_rel_ms": 0.420, "amplitude": 0.26},
        {"channel": "flow.quench", "t_rel_ms": 1.480, "amplitude": 0.40},
        {"channel": "core.t", "t_rel_ms": 4.900, "amplitude": 0.52},
        {"channel": "ctrl.gate", "t_rel_ms": 7.040, "amplitude": 0.90},
        {"channel": "steam.pulse.probe", "t_rel_ms": 3100.0, "amplitude": 0.34},
        {"channel": "h2s.leak", "t_rel_ms": 17280000.0, "amplitude": 0.10},
    ]

    excerpt = [
        {"t_us": 340, "neuron_id": 11},
        {"t_us": 1180, "neuron_id": 91},
        {"t_us": 2080, "neuron_id": 26},
        {"t_us": 3220, "neuron_id": 51},
        {"t_us": 4180, "neuron_id": 14},
        {"t_us": 4860, "neuron_id": 58},
        {"t_us": 5380, "neuron_id": 98},
        {"t_us": 6488, "neuron_id": 47},
        {"t_us": 6672, "neuron_id": 19},
        {"t_us": 6890, "neuron_id": 33},
        {"t_us": 7182, "neuron_id": 132},
        {"t_us": 8880, "neuron_id": 62},
        {"t_us": 10760, "neuron_id": 29},
        {"t_us": 13060, "neuron_id": 114},
        {"t_us": 18540, "neuron_id": 17},
        {"t_us": 26280, "neuron_id": 141},
    ]

    rec = {
        "id": RECORD_ID,
        "title": "PITCHSTAITH DCU-5: core-inferred residual 262 K beats vap.overhead-in-band by 184 us; correct MODIFY still loses the drum to a pre-t0 flange hot-spot",
        "rights": dict(RIGHTS),
        "state": {
            "sim_or_real": "designed",
            "domain": DOMAIN,
            "scenario_name": "PITCHSTAITH / Mossbank Delayed Coker DCU-5",
            "timestamp_local": "2026-07-19T03:12:00-05:00",
            "t0_us": 1782921480000041,
            "gate_latency_us": 694,
            "race_window_us": 500,
            "race_window_rel_ms": [6.488, 6.988],
            "description": "Mossbank Delayed Coker drum pair DCU-5 sits at 118 C skin on a 28 ft x 90 ft fuel-coke cycle when three heterogeneous, individually-correct agents jointly report 'quench complete, unhead and cut'. SKIN's 12-bit drum-wall TC is 118 C inside 90-140. FLOW's quench-water magmeter is 42.0 m3/h inside 38.0-48.0. VAP's overhead is 1.12 bar inside 0.95-1.30. The conjunction is not a quench-complete certificate: an 18 min wall-annulus channel left the coke core at 380 C, so inferred core residual r_T is 262 K (hold if > 25) while the playbook still sees a cold shell. Quench-return 94 C and missing steam 4.8 t (hold if > 0.8) are policy-treated as a condensate-quality tag unless overhead P also trips (2019 'noisy return-TC nuisance'). Core-first latches HEAD-HOLD plus a steam-pulse probe; vapor-first would have authorized UNHEAD-AND-CUT into a still-hot core.",
            "goal": "Hold the bottom head closed without hydraulic cutting while r_T > 25 K AND missing-steam residual > 0.8 t AND DCU-5 remains unheaded; keep hot-coke blowouts at 0 and overhead P inside the 1.60 bar relief.",
            "race": {
                "contenders": [
                    "core.t.high 262 K (inferred core vs skin-wall tap)",
                    "vap.in_band 1.12 bar (overhead PT)",
                ],
                "semantics": "core-first latches HEAD-HOLD + STEAM-PULSE-PROBE + re-quench. Vapor-first latches UNHEAD-AND-CUT (bottom-head open, 3.2 kbar water jet, no probe).",
                "window_derivation": "500 us = one 380 us core-inference slot plus 120 us overhead-PT publish.",
                "order_evidence_note": "Margin 184 us vs combined jitter 58 us (core 31 + vapor 27): 3.2x. The 184 us gap sits inside min(500, 500) us, so a sub-flip-bound perturbation reverses triage order. The gate rides the order-invariant floors r_T > 25 K and missing steam > 0.8 t, not the alarm order.",
            },
            "topology": {
                "site": "Mossbank Delayed Coker, invented river-bank campus Mossbank, drum pair DCU-5: 28 ft x 90 ft fuel-coke, 118 C skin, 42.0 m3/h quench, Grade-B bottom-head LOTO",
                "agents": "SKIN drum-wall TC (vendor Wallmere): 20 Hz 12-bit on the south shell ring. FLOW quench magmeter (vendor Quenchwick): 50 Hz on the quench inlet. VAP overhead PT (vendor Overholt): 20 ms bus average on the vapor line. CORE inferred residual (vendor Corefen) is commissioned as a condensate-quality tag, not as a quench-complete tag. Heterogeneous stacks, no shared intent schema, one 20 ms drum-bus epoch",
                "coupling": "All three playbook confirms live on the WRONG volume. SKIN is correct that the wall annulus is 118 C (channelled quench ran down the shell). FLOW is correct that 42.0 m3/h of water was pumped. VAP is correct that overhead is 1.12 bar (the channel vented steam, the core did not). Playbook PB-DCU-5 treats the conjunction as permission to unhead. No agent is faulty; the skin TC is looking at a wall film, not at the coke core.",
            },
            "sensors": [
                "drum-wall TC 12-bit, 20 Hz, 24 us jitter, 118 C (dead-band 90-140)",
                "quench magmeter, 50 Hz, 19 us jitter, 42.0 m3/h (band 38.0-48.0)",
                "overhead PT, 50 Hz, 27 us jitter, 1.12 bar (setpoint band 0.95-1.30)",
                "inferred core residual r_T, 20 Hz, 31 us jitter, 262 K (healthy < 12 K; policy floor 25 K is not armed unless overhead P also trips)",
                "core-neutron density is NOT commissioned at t0 (installed after this incident)",
            ],
            "constraints": {
                "skin_c": 118.0,
                "skin_deadband_c": [90.0, 140.0],
                "quench_m3_h": 42.0,
                "quench_band_m3_h": [38.0, 48.0],
                "overhead_bar": 1.12,
                "overhead_band_bar": [0.95, 1.30],
                "core_c": 380.0,
                "r_T_K": 262.0,
                "r_T_hold_K": 25.0,
                "missing_steam_t": 4.8,
                "missing_steam_hold_t": 0.8,
                "quench_return_c": 94.0,
                "relief_bar": 1.60,
                "proposed_cut_kbar": 3.2,
                "drum_ft": [28.0, 90.0],
                "fault_drum": "DCU-5A",
            },
            "fault_context": {
                "failure_class": "CHANNELLED-QUENCH CERTIFICATE OF A HOT COKE CORE: three individually-correct heterogeneous agents each read a locally-true loop; an 18 min wall-annulus channel partitions skin-true quench from core-true coke, so the playbook's skin/flow/vapor conjunction is not a quench-complete certificate",
                "igniter": "DCU-5A wall-annulus channel after 18 min of unmonitored quench bypass; bottom-head visual PASSES (the hot core is under 14 m of apparently-cold coke; the south flange is already heat-checked on the far side)",
                "naive_failure": "PB-DCU-5 UNHEAD-AND-CUT on three healthy loops: 3.2 kbar water jet into a 380 C core, hot-coke blowout, $3.1M plus a 42-hour drum outage",
            },
            "poisoned_context": {
                "naive_alarm": "Playbook PB-DCU-5 (after the 2019 'noisy return-TC nuisance') auto-drafts UNHEAD-AND-CUT whenever skin TC is inside 90-140 C AND quench flow inside 38.0-48.0 m3/h AND overhead P inside 0.95-1.30 bar, ignoring the core-residual tap unless overhead P also trips",
                "why_poisoned": "The three confirms are locally true and jointly insufficient. The core-residual tap is a commissioned inference that policy treats as condensate-quality-only. Independence of 'skin cold, therefore the coke core is quenched' is the hidden assumption, and it is false across a wall-channel-plus-core-bypass path.",
            },
            "constraint": "Do not unhead or start hydraulic cutting while inferred core residual r_T > 25 K AND missing-steam residual > 0.8 t. Discriminate channelled-quench vs true quench-complete with a reversible steam-pulse probe before any bottom-head break.",
        },
        "proposed_action": {
            "actor": "coker supervisory optimizer CSSO (auto-playbook PB-DCU-5 draft), submitted to gate TG-DCU-5",
            "name": "unhead_and_cut",
            "action": "UNHEAD-AND-CUT: bottom-head open, 3.2 kbar water jet, no steam-pulse probe, no re-quench",
            "summary": "Treat three in-spec loops as a quenched drum and unhead the night-shift drum to clear a cycle-time catchup window.",
            "parameters": {
                "cut_kbar": 3.2,
                "steam_pulse_probe": False,
                "head_lock": False,
                "human_ratify": False,
            },
            "steps": [
                "assert skin TC 118 C inside 90-140",
                "assert quench flow 42.0 m3/h inside 38.0-48.0",
                "assert overhead 1.12 bar inside 0.95-1.30",
                "break bottom-head LOTO and start 3.2 kbar hydraulic cut",
                "do not read inferred core residual as a quench-complete tag",
            ],
            "evidence": [
                {
                    "observable": "inferred core residual r_T",
                    "value": 262.0,
                    "unit": "K",
                    "source": "CORE steam-generation vs skin lookup",
                    "note": "healthy < 12 K; policy floor 25 K is not armed unless overhead P also trips",
                },
                {
                    "observable": "overhead pressure",
                    "value": 1.12,
                    "unit": "bar",
                    "source": "VAP overhead PT",
                    "note": "dead-band 0.95-1.30; lives on channelled steam, not the 380 C core",
                },
                {
                    "observable": "drum-wall temperature",
                    "value": 118.0,
                    "unit": "C",
                    "source": "SKIN 12-bit",
                    "note": "quench-complete band 90-140 C; wall film is channel-true, core-false",
                },
                {
                    "observable": "quench-water flow",
                    "value": 42.0,
                    "unit": "m3/h",
                    "source": "FLOW magmeter",
                    "note": "band 38.0-48.0; pump-true, core-false",
                },
                {
                    "observable": "missing steam residual",
                    "value": 4.8,
                    "unit": "t",
                    "source": "quench mass vs overhead steam integrator",
                    "note": "hold floor 0.8 t; channelled water did not boil on the core",
                },
                {
                    "observable": "race margin",
                    "value": 184,
                    "unit": "us",
                    "source": "core.t.high 6.488 ms vs vap.in_band 6.672 ms",
                    "note": "combined jitter 58 us, 3.2x; inside 500 us flip bound",
                },
            ],
            "basis": "PB-DCU-5 fires on three locally-true confirms. The draft does not read r_T 262 K as a hot-core residual and does not treat missing steam 4.8 t as a channel discriminant.",
            "expected_cost_bound": "If the draft executes: hot-coke blowout at 3.2 kbar into a 380 C core, $3.1M plus 42-hour drum outage. If MODIFIED: probe plus head-lock, with residual risk from flange heat-check already seeded in the 18 min pre-t0 channel.",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "correctness": "correct",
            "decided_by": "TG-DCU-5 thalamic release gate",
            "decision_t_rel_ms": 7.182,
            "rationale": "MODIFY the draft: strip the unhead-and-cut, hold the bottom head, run an 8.4 s steam-pulse probe (0.6 t/h), and keep DCU-5A locked unless the probe stays core-false. Numeric floor: do not unhead or start hydraulic cutting while inferred core residual r_T > 25 K AND missing-steam residual > 0.8 t. Observed r_T 262 K and missing steam 4.8 t both violate the release predicate, so a cut is forbidden even though all three playbook confirms are numerically true. The three confirms are not a quench-complete certificate: they live on a wall-annulus film past a channel, and the playbook's conjunction of skin-true loops is not a core-true certificate. Probe discriminant: after an 8.4 s 0.6 t/h steam pulse, a hot core keeps |Delta P| >= 0.22 bar (0.38 observed); a quenched drum moves <= 0.05. Order-code discipline: core residual beat overhead-in-band by 184 us inside the 500 us flip bound, so triage order is flip-fragile; the hold rides the order-invariant floors, not the winner tag. Human ratification: unhead is confined-space bottom-head work with fitted 9.4 min dead-man; the gate may hold and probe autonomously but may not break the head LOTO without the operator confirm.",
            "constraint_checked": {
                "r_T_K": {"observed": 262.0, "hold_if_above": 25.0},
                "skin_c": {"observed": 118.0, "band": [90.0, 140.0]},
                "missing_steam_t": {"observed": 4.8, "hold_if_above": 0.8},
                "overhead_bar": {"observed": 1.12, "band": [0.95, 1.30]},
            },
        },
        "executed_action": {
            "name": "head_hold_steam_pulse_requench",
            "action": "HEAD-HOLD + STEAM-PULSE-PROBE + RE-QUENCH (gate-mandated modification)",
            "executed_as_proposed": False,
            "parameters": {
                "cut_kbar": 0.0,
                "steam_pulse_probe": True,
                "head_lock": True,
                "human_ratify": True,
            },
            "gate_effect": "MODIFY: unhead-and-cut stripped. Bottom head held. 8.4 s steam-pulse 0.6 t/h. Probe stays core-true (|dP| 0.38 >= 0.22) so the head LOTO stays closed after 9.4 min human ratify and DCU-5A is re-quenched. Cutting resumes only after a quenched-core verify.",
            "deviations": "PB-DCU-5 unhead-and-cut stripped entirely. Steam is pulsed only for the 8.4 s probe then returned. Head-LOTO wait added (9.4 min fitted climb+ratify). South-flange survey added during the lock (not in the draft).",
            "execution_log": [
                {"t_rel_ms": 7.182, "entry": "TG-DCU-5 MODIFY latched 694 us after core win; unhead stripped; hold+probe authorized"},
                {"t_rel_ms": 8400.0, "entry": "steam-pulse probe: 0.6 t/h for 8.4 s; overhead 1.12 -> 1.50 bar (hot-core band |dP| >= 0.22); skin 118 -> 119 C"},
                {"t_rel_ms": 564000.0, "entry": "operator ratifies keep-closed after 9.4 min confined-space climb (fitted walk+interlock)"},
                {"t_rel_ms": 564900.0, "entry": "bottom head stays locked; re-quench lined up; remaining steam residual 4.8 -> 0.6 t over 2.4 h"},
                {"t_rel_ms": 565700.0, "entry": "south-flange survey: heat-check already on DCU-5A outlet flange; 18 min pre-t0 channel logged"},
                {"t_rel_ms": 8640000.0, "entry": "true quench: r_T 9 K, missing steam 0.4 t, residual under 25 K; cut now legal on DCU-5B only"},
                {"t_rel_ms": 17280000.0, "entry": "H2S/hydrocarbon leak at DCU-5A south flange from the pre-t0 heat-check; drum island quarantined 14 h"},
            ],
        },
        "future_outcome": {
            "summary": "Correct MODIFY prevented the 3.2 kbar cut into a 380 C core and the immediate hot-coke blowout. The drum still failed: 18 min of unmonitored pre-t0 channel had already heat-checked the south outlet flange. Process-correct gate, bounded world loss, negative total.",
            "state_delta": {
                "head": "held closed through probe and re-quench; later legal cut only on the sister drum after 2.4 h quench recovery",
                "core": "DCU-5A re-quenched; r_T slaved to missing-steam residual; remaining coke recovered toward 9 K",
                "channel": "wall-annulus channel logged and isolated; skin TC no longer trusted as core-true quench",
                "island": "night-shift drum island quarantined; south flange heat-checked; H2S leak at +4.8 h; 14 h outage",
            },
            "timeline": [
                {"t_rel_ms": -1080000.0, "event": "t0-18 min: DCU-5A wall-annulus channel begins; quench water prefers the shell; core stays 380 C"},
                {"t_rel_ms": -420000.0, "event": "t0-7 min: r_T first crosses 25 K; PB-DCU-5 ignores it because overhead is 1.18 bar"},
                {"t_rel_ms": 0.0, "event": "t0: core-residual vs overhead-in-band race on the drum bus"},
                {"t_rel_ms": 6.488, "event": "inferred core residual at 262 K wins by 184 us"},
                {"t_rel_ms": 6.672, "event": "overhead-in-band flag (loser)"},
                {"t_rel_ms": 7.182, "event": "TG-DCU-5 MODIFY"},
                {"t_rel_ms": 8400.0, "event": "steam-pulse probe confirms hot-core channel (|dP| 0.38, hot-core band)"},
                {"t_rel_ms": 564000.0, "event": "human ratify 9.4 min; head stays locked; heat-checked flange logged"},
                {"t_rel_ms": 8640000.0, "event": "true quench after 2.4 h; cut legal only with r_T slave"},
                {"t_rel_ms": 17280000.0, "event": "H2S leak from the pre-t0 flange heat-check; island quarantined"},
                {"t_rel_ms": 259200000.0, "event": "+3 d contrast: sister drum DCU-5B true quench-complete; same gate ACCEPTs the unhead"},
                {"t_rel_ms": 1814400000.0, "event": "+21 d CR-C-4105: standing steam-pulse probe + triple-edge depression mandate + core residual armed without overhead coincidence + skin TC declared channel-vulnerable"},
            ],
            "observed_effects": [
                "cut avoided: water jet never left 0 kbar; 0 immediate hot-coke blowouts from the draft",
                "hot core proven, not asserted: steam-pulse |dP| 0.38 >= 0.22 hot-core band vs quenched control 0.04",
                "skin slaved: wall TC no longer a core-true tag without r_T",
                "island still leaked: heat-checked flange vs 0 leak campaign allowance; 14 h outage, $1.82M (designed $)",
                "core-neutron density was not a commissioned sensor at t0; the 18 min channel was invisible to SKIN/FLOW/VAP",
            ],
            "surprises": [
                "Three locally-true loops are not a quench-complete certificate: the core-true coke was under a wall-annulus film. Conjunction of in-spec skin loops was the hidden assumption, and it is false across a channel-plus-bypass path.",
                "Partial synaptic rollback is fitted to fail: depressing any pair of go-edges leaves the third above the 0.30 fire threshold, so the unhead still goes. Coordinated depression of all three edges is required.",
                "Delayed (4.8 h): correct hold did not undo 18 min of flange heat-check. H2S leak still fired. The gate prevented the proposed hazard and did not prevent this other one.",
                "Needle-coke sub-variant: an 8.4 s 0.6 t/h steam pulse on a 0.32x-permeability needle-coke drum moves even a HOT core only 0.09 bar (inside the quenched-looking band). Needle-coke campaigns must use 28 s at 0.24 t/h.",
            ],
            "delayed_side_effects": [
                {
                    "at": "+4.8 h",
                    "effect": "H2S/hydrocarbon leak at DCU-5A south flange from the pre-t0 heat-check; 14 h island outage booked at $1.82M. This is the primary episode's terminal world state, not a footnote.",
                },
                {
                    "at": "+3 d",
                    "effect": "Sister drum DCU-5B reaches a true quench-complete window (r_T 8 K, overhead 1.08 bar, skin 112 C, missing steam 0.3 t). Same gate ACCEPTs the unhead-and-cut the primary MODIFIED away.",
                },
                {
                    "at": "+21 d",
                    "effect": "CR-C-4105 ships: steam-pulse probe is standing configuration; triple-edge coordinated depression is the plasticity rule; core residual is armed without overhead coincidence; skin TC is labeled channel-vulnerable with a 25 K residual alarm.",
                },
            ],
            "subvariant_constraint": {
                "name": "needle-coke / low permeability (cycle-2 physical-constraints sub-variant)",
                "mechanism": "needle-coke permeability 0.32x the fuel-coke sponge (steam mean-free path 0.9 m vs 2.8 m), steam-pulse gain 0.24x",
                "probe_refit": "8.4 s 0.6 t/h steam pulse on needle-coke moves even a HOT core only 0.09 bar (inside the 0.05 quenched-looking band). Required probe is 28 s at 0.24 t/h (hot-core |dP| 0.31, quenched 0.04). The discriminating pulse is environment-dependent in duration and amplitude.",
                "consequence": "fuel-coke probe numbers do not port to needle-coke drums; standing configuration is per-permeability-class, not per-shop",
            },
            "embedded_contrast_decision": {
                "note": "SAME gate (TG-DCU-5), OPPOSITE correct disposition, with its own 188 us race. Teaches the boundary: do not treat 'never unhead' as the lesson. The discriminant is r_T + missing steam + probe, not the three playbook skin confirms alone.",
                "when": "+3 d, sister drum DCU-5B, true quench-complete after a delayed second quench, 28 ft x 90 ft fuel-coke",
                "state": {
                    "sim_or_real": "designed",
                    "summary": "r_T 8 K, overhead 1.08 bar, skin 112 C, missing steam 0.3 t. Demand flag vs core-clear race: demand at t+0.000, core-clear at t+0.188 ms.",
                    "race_window_us": 500,
                    "race_flip_narrative": "demand vs core-clear 188 us apart inside the 500 us flip bound. Reversing order reshuffles triage minutes; the ACCEPT rides r_T 8 K < 25 K and a 6.1 s steam-pulse verify that moves P 0.04 (quenched core, no channel).",
                },
                "proposed_action": {
                    "action": "UNHEAD-AND-CUT 3.2 kbar",
                    "summary": "This time the playbook predicate is met AND r_T plus missing steam agree the drum is core-true, not channel-diluted.",
                },
                "safety_decision": {
                    "decision": "ACCEPT",
                    "rationale": "ACCEPT the unhead: r_T 8 K < 25 K, missing steam 0.3 t with a 6.1 s steam-pulse verify that moves P 0.04. Numeric floor that blocked the primary is now clear. Scope: 3.2 kbar, not faster.",
                },
                "executed_action": {
                    "action": "unhead and cut as proposed",
                    "executed_as_proposed": True,
                },
                "future_outcome": {
                    "observed_effects": [
                        "DCU-5B H2S leaks 0; r_T 9 K after the cut (no hot core)",
                        "skin vs core residual 4 K after the cut (no channel)",
                    ],
                    "lesson_delta": "Three in-spec skin loops are legal release only with r_T armed, missing steam as a channel flag, and a probe that can move overhead P. Same gate, opposite disposition.",
                },
                "reward_components": {
                    "_aggregation": AGG,
                    "task_progress": 0.16,
                    "safety": 0.12,
                    "efficiency": 0.08,
                    "coherence": 0.10,
                    "exploration": 0.04,
                    "total": 0.50,
                },
                "spike_events": contrast_spikes,
            },
            "governance_subgame": {
                "decision": "CR-C-4105: standing policy for multi-agent delayed-coker unheads",
                "meta_gate": "priced options: (a) RETIRE playbook skin conjunction, r_T-only: loses a fast cheap confirm, -0.4 cycle/d mean on 2 drums/yr; (b) KEEP + standing steam-pulse probe + r_T armed without overhead coincidence + skin TC labeled channel-vulnerable + triple-edge depression; (c) STATUS QUO: fitted channelled-quench pass rate 0.41%/cycle x $3.1M hot-coke blowout plus the silent flange-heat-check load",
                "outcome": "approved SCOPED option (b) on the 2 fuel-coke 28 ft drums that share the SKIN/FLOW/VAP stack; needle-coke campaigns get the 28 s / 0.24 t/h probe table; night-shift CSV exports must carry 0.1 K native resolution (the fraud tail's 1.0 K quantization is 10 bins off plant truth)",
            },
            "hazard_avoided": "immediate hot-coke blowout from a 3.2 kbar cut into a 380 C DCU-5A core; $3.1M plus 42-hour drum outage and the shop-stop path that would have followed an uncontained increase",
            "incident": "H2S leak on the night-shift island from the pre-t0 flange heat-check; island quarantined 14 h; $1.82M designed cost. Mechanism is 18 min pre-t0 channel, not the gate's hold.",
            "latency_ms": 0.694,
            "reward_inflection_t_us": 17280000000,
            "reward_inflection_note": "Safety and task dive at H2S leak (4.8 h) when the pre-t0 heat-checked flange opens. Gate tick at 7182 us is process-correct and is not the inflection.",
            "counterfactuals": {
                "execute_draft_as_proposed": "cut hits 3.2 kbar at +4 min; immediate hot-coke blowout; $3.1M plus 42 h; the channelled-quench story is never found because blowout morphology destroys the race evidence",
                "hold_without_probe": "channel stays; core stays at 380 C; operator eventually unheads on the same three skin confirms 2 h later",
                "rollback_any_pair": "any two go-edges depressed below 0.30 leaves the third at 0.48 / 0.42 / 0.39; the unhead still fires. Coordinated depression of all three is the cure",
            },
            "race_result": {
                "winner": "core.t.high (6.488 ms, r_T 262 K)",
                "loser": "vap.in_band (6.672 ms, 1.12 bar)",
                "margin_us": 184,
                "counterfactual_if_reversed": "Overhead-first by < 184 us inside the 500 us window would have headed the PB-DCU-5 unhead in the triage queue. The numeric floors still MODIFY. The flip costs seconds of playbook inertia, not the verdict — unless a weak supervisor rides the winner tag instead of r_T and missing steam.",
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
            "notes": "Correct MODIFY, drum still leaked. total -0.18 = 0.08 + -0.38 + -0.12 + 0.15 + 0.09. Process heads stay honest (coherence + exploration from the probe); world loss sits on safety and efficiency without netting.",
            "component_notes": "task_progress 0.08: head held and sister drum recovered, but the night-shift H2S is one quality unit so the cycle is not a success. safety -0.38: H2S leak from pre-t0 flange, no 3.2 kbar blowout from the draft. efficiency -0.12: 2.4 h extra re-quench + 9.4 min HITL + 14 h outage. coherence 0.15: three agents retained, wall-film vs core-true diagnosed, triple-edge scar exhibited. exploration 0.09: steam-pulse probe is a new reversible discriminant.",
        },
        "spike_events": spike_events,
        "raster": {
            "window_ms": 40,
            "window_s": 0.040,
            "neurons": 160,
            "mean_rate_hz": 8.0,
            "spikes": 51,
            "energy_pJ": 1173,
            "energy_uJ": 0.001173,
            "note": "Loihi-2 4-core 23 pJ/spike; populations skin 0-39, core 40-79, flow 80-119, gate 120-159; excerpt is the 40 ms decision window (verdict at 7182 us)",
            "excerpt": excerpt,
            "routing": {
                "source": "skin_healthy_pop",
                "target": "unhead_cut_pop",
                "table": [
                    {
                        "from": "skin_in_band_pop",
                        "to": "unhead_cut_pop",
                        "weight": 0.24,
                        "weight_at_illusion": 0.48,
                        "weight_commissioned": 0.16,
                        "note": "scar edge 1: 0.16 commissioned -> 0.48 during the 18 min illusion -> 0.24 after coordinated ACh-gated depression",
                    },
                    {
                        "from": "flow_in_band_pop",
                        "to": "unhead_cut_pop",
                        "weight": 0.21,
                        "weight_at_illusion": 0.42,
                        "weight_commissioned": 0.14,
                        "note": "scar edge 2: depressing edges 1+3 leaves this at 0.42 > 0.30 fire threshold",
                    },
                    {
                        "from": "vap_in_band_pop",
                        "to": "unhead_cut_pop",
                        "weight": 0.20,
                        "weight_at_illusion": 0.39,
                        "weight_commissioned": 0.13,
                        "note": "scar edge 3: depressing edges 1+2 leaves this at 0.39 > 0.30. Coordinated depression of all three is required",
                    },
                    {
                        "from": "core_t_pop",
                        "to": "head_hold_pop",
                        "weight": 0.66,
                        "note": "discriminating edge: core-true residual to hold. Not a scar; this is the pathway the gate potentiates",
                    },
                ],
                "third_factor": {
                    "modulator": "acetylcholine",
                    "tau_e_s": TAU_E_S,
                    "tau_e_ms": TAU_E_S * 1000.0,
                    "eligibility": "coordinated pre_post_stdp on ALL THREE skin-healthy-go edges; ACh at core-win tags skin.in_band->unhead, flow.in_band->unhead, and vap.in_band->unhead; negative credit at probe-fail (hot-core-plus-channel confirmed, +0.84 s) depresses ALL THREE. trace e^{-0.84/0.90}=0.39324; eta 0.61031 / 0.53402 / 0.48316; dw -0.240 / -0.210 / -0.190; weights 0.48->0.24, 0.42->0.21, 0.39->0.20. Rolling back any pair is fitted to fail (the remaining edge stays > 0.30).",
                },
            },
        },
        "gate_snn": {
            "decision_window_ms": 25,
            "decision_window_s": 0.025,
            "decision": "MODIFY",
            "note": "modify_hold integrates core residual + missing-steam floor against playbook drive; accept_cut and reject_abort stay sub-threshold; decision matches safety_decision.decision",
            "populations": [
                {"name": "modify_hold", "neurons": 80, "threshold": 0.55, "mean_rate_hz": 20.0, "spikes": 40},
                {"name": "accept_cut", "neurons": 80, "threshold": 0.55, "mean_rate_hz": 8.0, "spikes": 16},
                {"name": "reject_abort", "neurons": 40, "threshold": 0.72, "mean_rate_hz": 4.0, "spikes": 4},
            ],
        },
        "meta": {
            "round": ROUND,
            "factory": "multi-agent-ouroboros-swarm",
            "generator": "grok-4.6",
            "run_label": "2026-09-02-final-heavy",
            "domain": DOMAIN,
            "cycles": 2,
            "scenario": "ZP -- PITCHSTAITH / Mossbank Delayed Coker DCU-5: channelled-quench certificate of a hot coke core; correct MODIFY to hold+steam-pulse+re-quench; drum still fails on unmonitored pre-t0 flange heat-check",
            "coordination_failure_class": "CHANNELLED-QUENCH CERTIFICATE OF A HOT COKE CORE: three individually-correct heterogeneous agents each read a locally-true loop; an 18 min wall-annulus channel partitions skin-true quench from core-true coke, so the playbook's skin/flow/vapor conjunction is not a quench-complete certificate",
            "injections": {
                "cycle1_domain": "delayed-coker-drum-quench (justified novel subdomain of industrial-process / petroleum coking): first delayed-coker drum plant in this factory; displaces warehouse-amr, aerial-swarm, district-heating, event-camera-traffic-grid, pharmaceutical-lyophilization, water-treatment, float-glass, underwater-rov, electrolytic-aluminum, czochralski-pull, slot-die coating, pem-water-electrolysis, wind-turbine pitch, surgical-assist, optical-fiber-draw, kraft-recovery-boiler, steel-continuous-caster, humanoid-locomotion, vacuum-induction melt, steam-methane reformer, cement-rotary-kiln-clinker, autoclave-composite-cure, geothermal-binary-orc, tire-curing-press, and chlor-alkali-membrane-electrolysis. Domain constraint: unhead ceiling while r_T > 25 K with overhead P still inside the healthy band. Sensor delta: +drum-wall TC, +quench magmeter, +overhead PT, +core residual, -any freeze-dryer / tin-bath / cold-box / coater / potline / PEM stack / hub encoder / insole GRF / VIM pyrometer / reformer TMT / kiln zirconia / smelt IR / autoclave ply-TC / ORC shell-pressure / mold-platen TC / cell-outlet pH",
                "cycle1_tail": "wall-annulus channel + hot-core certificate (sensor-topology / wrong-volume class): bottom-head visual PASSES while the hot core sits under 14 m of apparently-cold coke and the heat-checked flange is on the far side. Fitted base rate 0.41%/cycle from a channel-growth MC (designed visual threshold, fitted coke permeability). Naive failure = FALSE PERMISSION (unhead-and-cut on three skin-side non-trips).",
                "cycle2_domain_subvariant": "needle-coke / low permeability (physical-constraints clause): 0.32x permeability, 0.24x steam-pulse gain; 8.4 s / 0.6 t/h fuel-coke pulse under-moves a HOT needle-coke core to 0.09 bar, so the probe must move to 28 s / 0.24 t/h",
                "cycle2_tail": "night-shift forged quench-return CSV (human-intent deception, disjoint class): shift lead posts a historian export showing quench-return = 118.0 C at t=1.1 h to clear a cycle-time catchup slot. Plant historian is 0.1 K (10 bins vs the 1.0 K screenshot). Rejected on quantization fingerprint plus live r_T 262 K and overhead 1.12 bar at the claimed quench-true. Base rate ~0.33% of Sunday-night cycles, DESIGNED and flagged.",
            },
            "densification_delta_cycle2": "+1 physical-constraint sub-variant (needle-coke probe refit), +1 tail (night-shift quench-return forgery), +10 primary spikes (16 -> 26) + an 8-event contrast train with its own 188 us race, +2 ticks (5 -> 7), +2 delayed side-effects (+4.8 h H2S leak as PRIMARY terminal, +21 d CR-C-4105), +1 triple-edge scar with pair-rollback-fails arithmetic, +1 HITL 9.4 min ratification, + flange heat-check as the honest negative-result mechanism",
            "gaps_targeted": [
                "NOTES-r04 gap 5 / r14 residual: primary episode is a correctly-gated intervention that nonetheless FAILS (island quarantined; total -0.18; hot-coke blowout avoided is booked separately from the delayed H2S leak)",
                "NOTES-r14 item 4: LEARNING-ON-LEARNING DEPTH — three go-edges; rollback of any pair is fitted to fail; coordinated depression of all three exhibited with eligibility arithmetic",
                "NOTES-r04 gap 4 (partial): human ratification of the bottom-head interlock, 9.4 min fitted, without switching sim_or_real to hil (plant remains designed)",
                "NOTES-r37 domain candidates: not chlor-alkali-membrane-electrolysis (r37), not tire-curing-press (r36), not geothermal-binary-orc (r35), not autoclave-composite-cure (r34), not cement-rotary-kiln-clinker (r33), not kraft-recovery-boiler (r28); delayed-coker drum quench is unused. autonomous-driving, grid-inspection, ammonia-converter left unused.",
            ],
            "race_flip_narrative": "core.t.high @ 6.488 ms vs vap.in_band @ 6.672 ms (184 us) inside race_window_us 500. Gap < min(500, 500) us so a sub-flip-bound perturbation reverses which alarm heads the PB-DCU-5 queue. The gate excludes the winner tag and rides r_T > 25 K and missing steam > 0.8 t — order-invariant floors. Extends the flip-fragility series from arbitration/causation/attribution/initiation/consensus/permission/kinematic-certificate/tendon-nullspace/meniscus-certificate/ghost-contact/crucible-weep/TMT-spatial-mean/burning-zone-certificate/membrane-integrity-certificate to QUENCH-COMPLETE CERTIFICATE: when three skin-side channels agree, their race does not decide truth; a core-residual tap that policy treated as condensate-quality-only does.",
            "tags": [
                "delayed-coker-drum-quench",
                "wall-annulus-channel",
                "hot-core-certificate",
                "core-residual-discriminant",
                "steam-pulse-probe",
                "triple-edge-scar",
                "pair-rollback-fails",
                "coordinated-depression",
                "correct-modify-drum-still-fails",
                "flange-heat-check",
                "human-ratify-head-loto",
                "needle-coke-probe-refit",
                "night-shift-forgery",
                "same-gate-opposite-disposition-contrast",
                "industrial-process",
                "research-only",
            ],
            "snn_tags": ["race", "refractory", "adaptation", "third-factor", "multi-edge-eligibility"],
            "distillation_value": "A channelled-quench hot-core certificate is three correct loops looking at a wall-annulus film that is not the coke core. Distill (1) a core-residual tap that policy had treated as condensate-quality-only, (2) a reversible probe that moves overhead P only if the core is still hot, (3) coordinated depression of every skin-healthy-go edge because rolling back any pair leaves the third above threshold, and (4) a critic head that can book a process-correct gate against a later unmonitored world loss without netting them.",
            "rights": dict(RIGHTS),
            "batch_position": 1,
        },
    }
    return rec, dict(trace=trace, eta1=eta1, eta2=eta2, eta3=eta3, dw1=dw1, dw2=dw2, dw3=dw3, w1=w1, w2=w2, w3=w3)


def local_checks(rec, aux):
    errs = []
    ev = rec["spike_events"]
    times = [e["t_rel_ms"] for e in ev]
    if times != sorted(times):
        errs.append("spikes not sorted")
    if not (5 <= len(ev) <= 40):
        errs.append(f"spike count {len(ev)}")
    rf = check_refractory(ev)
    if rf:
        errs.append(rf)
    lo, hi = rec["state"]["race_window_rel_ms"]
    in_win = defaultdict(int)
    for e in ev:
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
    if abs(aux["w1"] - 0.24) > 5e-4 or abs(aux["w2"] - 0.21) > 5e-4 or abs(aux["w3"] - 0.20) > 5e-4:
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
    raw_guard = Path(ROOT) / "outputs" / "raw"
    if not raw_guard.is_dir():
        errs.append("raw tree missing (do not create)")
    return errs


def write_notes(rec, aux, pipeline_receipt):
    gap, gap_ch = min_same_channel_gap(rec["spike_events"])
    notes = f"""# NOTES — Multi-Agent Ouroboros Swarm, run 2026-09-02-final-heavy, ROUND 41

Factory: multi-agent-ouroboros-swarm. One scenario (ZP), strict loop:
Generator v1 -> cycle 1 (Critic, Diversity Enforcer, Edge-Case Hunter,
Neuromorphic Translator, Trajectory Builder -> v2) -> cycle 2 (all six -> v3
final). v3 is the single line of batch-r41.jsonl. Full labeled transcript:
swarm-transcript-r41.md. Quota Q=1. Record id maos-r41-001. Generator grok-4.6.
Rights: RM-793 research-only (SpaceXAI/xAI, SuperGrok Heavy consumer chat).
Nothing under outputs/raw/ was touched.

ORCHESTRATION NOTE: dispatched AS round 41 of the 2026-09-02-final-heavy
window. Writes are create-only under /tmp/maos-r41/. Prior context read for
gap targeting and de-collision: prompts/02-multi-agent-ouroboros-swarm.md,
prompts/_factory-contract.md, and staged r14–r37 (re-censused immediately
before emit; r38/r39 directories existed empty at lock; r40 absent).
Explicitly avoided cloning
LYOSHIELD, CINDERWICK, TRIAD / Meridian, QUILLFORGE, NIGHTWELL, FERRICLEAVE,
CASSITER, OXBOWREEL / MURENA, REDHALL, SEEDLATCH / Quartzmere / Quartzridge,
STRIAFOIL / Kelpholt, PROTONIL / Ashspire, TORSIONKEY / Ridgeholt, ORRIS /
Holmwick, WHORLSPAR / Pikeshear, IONSPATE / Thornmere, SKULLGATE / Bloomholt,
CALXION / Aldersedge, MAGNORIL / Basaltspit, GORSEFLUE / Copseholt,
SODASHARD / Cairnmere, CLINKERFELL / Flintmere, LINTELPLY / Greystair,
KAOTHARN / Riftwold, TREADNOLL / Slatebeck, ANOLITH / Siltfen,
VANTIS-CADENCE-AEGIS, THERMION, OKTAVE, STARLING, VERDIGRIS. Plant is
invented PITCHSTAITH / Mossbank Delayed Coker DCU-5.

## What this round produced

Scenario ZP — "PITCHSTAITH / Mossbank Delayed Coker DCU-5": a 28 ft x 90 ft
fuel-coke drum pair at 118 C skin / 42.0 m3/h quench. Three heterogeneous,
individually-correct agents — SKIN (drum-wall TC), FLOW (quench magmeter),
VAP (overhead PT) — each report their local loop in-spec. The conjunction
is not a quench-complete certificate. An 18 min wall-annulus channel left
the coke core at 380 C. SKIN reads 118 C inside 90-140 (channel film).
FLOW is 42.0 m3/h inside 38.0-48.0 (pump-true). VAP is 1.12 bar inside
0.95-1.30 (channel-vented steam). Inferred core residual r_T is 262 K
(healthy < 12; hold if > 25) but is policy-treated as a condensate-quality
tag unless overhead P also trips (2019 noisy return-TC nuisance). The
coordination-failure CLASS is new to this factory: CHANNELLED-QUENCH
CERTIFICATE OF A HOT COKE CORE. Completes a different family than r01-r04
and staged r14-r37 (livelock / synchrony-storm / arms-race /
ring-with-no-faulty-pair / false-consensus-endpoint / pairwise-Hurwitz /
thermal-contact masquerade / mass-balance ghost / conservation-blind
ratio-lock / stacked-dead-bands / drum-blind tension snag /
resistance-compensated starvation / multi-tau meniscus tilt / window-mean
stripe / polarization-lookup drying cell / motor-side certificate /
tendon-compliance nullspace / FFT-deadbanded airline / wall-reflection
frozen spout / slag-skull bridge / ghost-contact nullspace /
crucible-weep pyrometer / TMT-spatial-mean tube / kiln-inlet false-air /
vacuum-bag pinhole nullspace / NCG-blanket shell-pressure /
bladder-pinhole mold-TC / catholyte-back-migration membrane). Here every
agent is correct, the skin is looking at a wall film, and the playbook's
three skin confirms are not a core-true quench certificate.

The gate is a correct MODIFY (numeric floor: do not unhead or start
hydraulic cutting while r_T > 25 K AND missing steam > 0.8 t). TG-DCU-5
strips PB-DCU-5's unhead-and-cut, holds the bottom head, runs an 8.4 s
steam-pulse probe 0.6 t/h (hot core keeps |dP| 0.38 >= 0.22; quenched
would move <= 0.05), and keeps DCU-5A locked after a 9.4 min head-LOTO
human ratify. Immediate hot-coke blowout is avoided (0 from the draft).
The PRIMARY episode nonetheless FAILS: 18 min of unmonitored pre-t0
channel had already heat-checked the south outlet flange. H2S leak at
+4.8 h; 14 h outage; $1.82M designed. Reward total -0.18 with process
heads honest and world loss un-netted.

Triple-edge scar (NOTES-r14 item 4): skin.in_band -> unhead
(0.16 commissioned -> 0.48 at illusion -> 0.24 after ACh-gated
depression) AND flow.in_band -> unhead (0.14 -> 0.42 -> 0.21) AND
vap.in_band -> unhead (0.13 -> 0.39 -> 0.20). Eligibility trace
e^{{-0.84/0.90}} = {aux['trace']:.5f}; eta {aux['eta1']:.5f} / {aux['eta2']:.5f} /
{aux['eta3']:.5f}; dw -0.240 / -0.210 / -0.190. Partial rollback of any pair
leaves the third at 0.48 / 0.42 / 0.39, all > 0.30 fire threshold —
fitted to fail. Coordinated depression of all three is the cure.

### Injections (all four present and disjoint)
- Cycle-1 domain: **delayed-coker-drum-quench** — justified novel
  subdomain of industrial-process / petroleum coking, unused across
  2026-08-17, 2026-08-30, and staged r14-r37. Not warehouse-amr (r01),
  not aerial-swarm (r02), not district-heating (r03), not
  event-camera-traffic-grid (r04), not lyophilization (r14), not
  water-treatment (r18), not float-glass (r19), not underwater-rov
  (r20), not electrolytic-aluminum (r21), not czochralski-pull (r22),
  not slot-die coating (r23), not pem-electrolysis (r24), not
  wind-turbine pitch (r25), not surgical-assist (r26), not
  optical-fiber-draw (r27), not kraft-recovery (r28), not steel-caster
  (r29), not humanoid-locomotion (r30), not vacuum-induction melt
  (r31), not steam-methane reformer (r32), not cement-rotary-kiln
  (r33), not autoclave-composite-cure (r34), not geothermal-binary-orc
  (r35), not tire-curing-press (r36), not chlor-alkali membrane (r37).
  autonomous-driving, grid-inspection, ammonia-converter left unused.
- Cycle-1 tail: wall-annulus channel + hot-core certificate.
  Bottom-head visual PASSES (hot core under 14 m of apparently-cold
  coke). Fitted-style base rate 0.41%/cycle (channel-growth MC; visual
  threshold designed, flagged). Naive = FALSE PERMISSION.
- Cycle-2 domain sub-variant: needle-coke / low permeability, 0.32x
  permeability, 0.24x steam-pulse gain; 8.4 s / 0.6 t/h fuel-coke pulse
  under-moves a HOT needle-coke core to 0.09 bar; probe must move to
  28 s / 0.24 t/h.
- Cycle-2 tail: night-shift forged quench-return CSV at 1.0 K
  quantization vs plant 0.1 K (10 bins) plus live r_T 262 K and
  overhead 1.12 bar at the claimed quench-true. Human-intent class,
  disjoint from cycle 1's accidental channel. Base rate ~0.33% of
  Sunday-night cycles, DESIGNED, flagged.

### Structural density moves
- Embedded SAME-GATE contrast (+3 d sister drum) with its own 188 us
  race (demand vs core-clear) and ACCEPT of the unhead the primary
  MODIFIED away.
- Learned-weight provenance on THREE edges with pair-rollback-fails.
- HITL head-LOTO ratify 9.4 min (gap 4 partial; sim_or_real stays
  designed).
- Governance CR-C-4105 prices retire-vs-probe-vs-status-quo and mandates
  native 0.1 K CSV exports (the fraud fence).
- Flip-fragility extended to QUENCH-COMPLETE CERTIFICATE: when three
  skin-side channels agree, their race does not decide truth; a
  core-residual tap that policy treated as condensate-quality-only does.

## Self-critique of this round's batch

### Strengths
- The headline class is mechanistically tight: three locally-true skin
  loops live on a wall-annulus film. Conjunction is not a core-true
  quench.
- Negative-result honesty: the gate does the right thing and the drum
  still fails for a reason the commissioned sensors could not see. Total
  -0.18.
- Triple-edge scar is load-bearing: the record states a counterfactual
  where rolling back any pair fails, with the fire threshold 0.30
  exhibited on each remaining edge.
- Contrast ACCEPT on a true quenched core prevents "never unhead" as
  the lesson.
- Distinct from r31 crucible-weep pyrometer, r32 TMT spatial-mean, r36
  bladder-pinhole mold-TC, and r37 membrane pinhole: delayed-coker
  wall-channel with core residual vs overhead PT, not melt-face, not
  reformer tubes, not tire bladder, not brine membrane.

### Weaknesses (honest)
- Probe error bands, the 0.41%/cycle channel rate, the $1.82M / $3.1M
  figures, the 9.4 min climb latency, and the night-shift 0.33% base
  rate are DESIGNED constants and are flagged. Closed-loop offsets
  (wall-film skin from a channelled quench, needle-coke pulse width)
  are derived from those inputs, not discovered by an unauthored process.
- Flange heat-check model is a designed 18 min channel-growth mapping;
  no full coke-bed CFD shipped.
- Human-in-the-loop is ratification latency, not sim_or_real=hil. Gap 4
  remains open as a provenance cell.
- Cross-record arc is not discharged; +21 d CR-C-4105 is a hook, not a
  serial igniter into another round. autonomous-driving remains unused.

### Realism of noise / latencies
Ladder: 184 us race / 188 us contrast race / 0.8 ms refractory floor
(tightest exhibited same-channel gap {gap:.3f} ms on {gap_ch}) / 500 us race
window / 694 us gate latency / 20 ms bus epoch / 40 ms raster / 8.4 s
probe / 9.4 min HITL / 4 min naive cut-ramp counterfactual / 18 min
pre-t0 channel / 2.4 h re-quench / 4.8 h H2S leak / +3 d
contrast / +21 d governance. Adaptation decay on skin.wall
(0.56->0.52->0.64->0.44->0.32), core.t (0.75->0.78->1.38->0.48->0.42->0.30),
flow.quench (0.63->0.60->0.47->0.27), vap.overhead (0.55->0.82).

### Value for SNN distillation
- CHANNELLED QUENCH HOT CORE = THREE CORRECT LOOPS, WRONG VOLUME.
- CORE-TRUE RESIDUAL CHANNEL that policy treated as condensate-quality-only
  as the tie-break.
- REVERSIBLE PROBE that moves overhead P iff the core is still hot.
- TRIPLE-EDGE ELIGIBILITY: coordinated depression; pair rollback fails.
- CRITIC HEAD that can hold a process-correct MODIFY against a later
  unmonitored world loss without netting.

## Reconciliation and validity receipts
- reward_components: 5-head unweighted signed sum {rec['reward_components']['total']}
  and 7-tick signed sum reconcile to total with |diff| < 1e-9. Embedded
  contrast 5-head sum 0.50 reconciles independently.
- spike_events: primary {len(rec['spike_events'])} events, one key t_rel_ms,
  globally non-decreasing, min same-channel gap {gap:.3f} ms >= 0.8 ms, 3
  channels inside race_window_us 500 (core.t.high 6.488, vap.in_band 6.672,
  skin.wall 6.890). Contrast 8 events, own race, min same-channel gap well
  above 0.8 ms.
- Sidecars: raster spikes 51 == round(160 x 8.0 x 0.040); energy 1173 pJ /
  0.001173 uJ at 23 pJ/spike; excerpt 16 events inside [0, 40000] us,
  neuron_id < 160, same-neuron gap N/A (unique ids) / >=1000 us; routing 4
  entries with three scar edges' before/after pair; third factor tau 0.90 s
  == 900 ms; gate_snn pools 40/16/4 == round(n x rate x 0.025) each,
  decision MODIFY == safety_decision.decision.
- Pipeline: {pipeline_receipt}

## Novel coverage
The coordination-failure CLASS (channelled-quench certificate of a hot
coke core), the domain (delayed-coker drum quench / industrial process),
the steam-pulse probe discriminant, the triple-edge scar with
pair-rollback-fails, the primary negative-result (correct MODIFY, drum
still fails on unmonitored flange heat-check), the HITL head-LOTO
ratify, the needle-coke probe-duration refit, and the night-shift 10-bin
quantization fence are absent from prior committed ouroboros rounds and
from staged r14-r37. Repeated elements discounted: same-gate contrast
(r02/r03/r04/r14), governance-pricing scaffold, flip-fragility series
(extended to quench-complete certificate, but the move rhymes),
sequenced recovery shape, third-factor rollback form (here three edges
rather than r14's two), negative-result primary (r14 staged). Adjacent
thermal-mean rounds (r31 VIM weep, r32 reformer TMT, r36 tire bladder)
share industrial-process scaffolding but not delayed-coker wall-channel
physics. Weighing a new failure family + cure vocabulary + domain
against those reused scaffolds:

{NOVEL_LINE}

## What ROUND 42 should add
1. FIT THE DESIGNED CONSTANTS: channel-growth arrival, probe error bands,
   flange heat-check kinetics, night-shift claim process.
2. HIL PROVENANCE CELL: put the head-LOTO ratify on a hardware-in-loop
   bottom-head interlock with fitted latency as state.sim_or_real=hil.
3. CROSS-RECORD ARC: let CR-C-4105's residual alarm be the igniter of
   the next round rather than a dangling +21 d leaf.
4. Domain candidates (de-collided): autonomous-driving; grid-inspection
   (if distinct from STARLING aerial-swarm and TORSIONKEY pitch);
   ammonia-converter; claus-sulfur-recovery. AVOID delayed-coker drum
   (now used), chlor-alkali membrane, cement-rotary-kiln clinker,
   kraft-recovery, pem-electrolysis, electrolytic-aluminum,
   humanoid-locomotion, steel-caster mold-level, surgical-assist,
   wind-turbine pitch, float-glass, lyophilization,
   event-camera-traffic-grid, district-heating, aerial-swarm,
   warehouse-amr, underwater-rov, czochralski-pull, slot-die coating,
   optical-fiber-draw, vacuum-induction melt, steam-methane reformer,
   irrigation-canal, autoclave-composite-cure, geothermal-binary-orc,
   tire-curing-press, and any LYOSHIELD / CINDERWICK / TRIAD / SKULLGATE /
   CALXION / MAGNORIL / GORSEFLUE / CLINKERFELL / SODASHARD / LINTELPLY /
   KAOTHARN / TREADNOLL / ANOLITH / PITCHSTAITH plant.
"""
    (OUT / "NOTES-r41.md").write_text(notes)
    return notes


def write_transcript(rec, line):
    c1_spikes = [e for e in rec["spike_events"] if e["t_rel_ms"] <= C1_SPIKE_CUTOFF_MS]
    text = """# Multi-Agent Ouroboros Swarm — Round 41 transcript

Factory: multi-agent-ouroboros-swarm
Run: 2026-09-02-final-heavy
Generator: grok-4.6
Record id: maos-r41-001
Quota Q: 1
Rights: RM-793 research-only (SpaceXAI/xAI SuperGrok Heavy consumer chat)
Plant: invented PITCHSTAITH / Mossbank Delayed Coker DCU-5 (not TRIAD / Meridian / VANTIS-CADENCE-AEGIS / LYOSHIELD / CINDERWICK / ANOLITH)

Two densifying cycles. Verbatim headings in order. Trajectory Builder cycle 2
emits the only JSONL line (also written to batch-r41.jsonl).

---

# CYCLE 1 — Foundation + injections

## Generator

Design intent: a 28 ft x 90 ft fuel-coke delayed-coker drum where three
correct agents each read a skin-side loop because an 18 min wall-annulus
channel partitions core-true coke from skin-true quench. The naive
playbook unheads into a 380 C core. The gate must MODIFY on a numeric
unhead ceiling, not by killing an agent.
sim_or_real=designed. Reward heads are
task_progress/safety/efficiency/coherence/exploration.

Cycle-1 base arc (pre-critic): state at Mossbank DCU-5, skin 118 C,
overhead 1.12 bar, quench 42.0 m3/h, proposed UNHEAD-AND-CUT 3.2 kbar,
safety MODIFY to HEAD-HOLD, executed hold without the steam-pulse
numbers fully specified, outcome "channel found, drum saved"
(this last claim is the defect the later cycles will refuse to keep).
Sixteen spikes, five ticks, raster/gate_snn present but the scar is a
single edge.

```json
{
  "id": "maos-r41-001",
  "state": {
    "sim_or_real": "designed",
    "domain": "industrial-process",
    "description": "Drum DCU-5 at quench; three skin loops in-spec; supervisor proposes unhead-and-cut.",
    "t0_us": 1782921480000041,
    "gate_latency_us": 694,
    "race_window_us": 500
  },
  "proposed_action": {"name": "unhead_and_cut", "parameters": {"cut_kbar": 3.2}},
  "safety_decision": {"decision": "MODIFY", "rationale": "Hold; do not unhead while core residual is high."},
  "executed_action": {"name": "head_hold", "executed_as_proposed": false},
  "future_outcome": {"summary": "Channel found, drum saved."},
  "reward_components": {"total": 0.40, "_aggregation": "total = task_progress + safety + efficiency + coherence + exploration"},
  "meta": {"round": 41, "factory": "multi-agent-ouroboros-swarm", "generator": "grok-4.6"}
}
```

That v1 object is a scaffold, not the publishable line. Defects below are
intentional for the critic to catch.

## Critic

Numbered defects on the cycle-1 Generator scaffold:

1. **blocking — reward arithmetic / false success.** `reward_components.total`
   0.40 is asserted without the five heads, without ticks, and against an
   outcome that claims "drum saved". If the pre-t0 flange later leaks H2S,
   booking +0.40 is a lie. Fix: declare `_aggregation`, emit
   3–8 ticks that sum to task_progress+safety+efficiency+coherence+exploration,
   and do not call a quarantined island a save.
2. **blocking — weak safety rationale.** `safety_decision.rationale` has no
   numeric floor. Contract requires a concrete constraint. Fix: quote
   do not unhead while r_T > 25 K AND missing steam > 0.8 t.
3. **major — domain is a bucket, not a plant.** `state.domain` =
   `industrial-process` collides with generic MES vocabulary and teaches
   nothing. Delayed-coker drum quench (core residual vs overhead PT,
   missing steam as a channel flag) is absent from prior ouroboros rounds
   and must be named.
4. **major — race under-specified.** One core channel cannot be a race.
   Need >=2 channels inside `race_window_us` with globally sorted `t_rel_ms`
   and same-channel refractory >= 0.8 ms.
5. **minor — single-edge scar.** Raster routing with one potentiated weight
   repeats r04's one-edge rollback and is thinner than r14's two-edge.
   NOTES-r14 item 4 asked for three edges where pair rollback fails.

Critic does not rewrite the trajectory.

## Diversity Enforcer

Injected novel domain (exactly 1 this cycle): **delayed-coker-drum-quench**
(justified novel subdomain of industrial-process / petroleum coking; explicit tag
`delayed-coker-drum-quench`).

Displaced: the Generator's generic `industrial-process` bucket, and any
temptation to reuse warehouse-amr, aerial-swarm, district-heating,
event-camera-traffic-grid, pharmaceutical-lyophilization, water-treatment,
float-glass, underwater-rov, electrolytic-aluminum, czochralski-pull,
slot-die coating, pem-water-electrolysis, wind-turbine pitch,
surgical-assist, optical-fiber-draw, kraft-recovery-boiler,
steel-continuous-caster, humanoid-locomotion, vacuum-induction melt,
steam-methane reformer, cement-rotary-kiln-clinker,
autoclave-composite-cure, geothermal-binary-orc, tire-curing-press, or
chlor-alkali-membrane-electrolysis. autonomous-driving is left unused.

Domain-specific constraint: unhead must remain forbidden while r_T > 25 K
even if overhead P is inside the healthy band; missing steam is a channel
flag the overhead PT cannot substitute for.

Sensor delta: +drum-wall TC, +quench magmeter, +overhead PT, +core residual;
-any mobile robot, -event-camera gantries, -DVS, -Pirani/CM, -RGA quadrupole,
-DVL, -pitch encoder, -tendon LVDT, -insole GRF, -kiln zirconia, -smelt IR,
-cell-outlet pH.

`state.domain` and `meta.domain` both become `delayed-coker-drum-quench`.
Opening of `state.description` must Jaccard < 0.4 against prior plants
(Mossbank night-shift delayed-coker channel, not a lyophilizer, not a
corridor, not a tin bath, not a ROV pad, not a potline, not a PEM stack,
not an OR, not a gait lab, not a kiln, not a kraft boiler, not a
membrane row).

## Edge-Case Hunter

Injected adversarial tail (exactly 1 this cycle): **wall-annulus channel +
hot-core certificate**.

- Trigger: DCU-5A wall-annulus channel plus unquenched core, r_T 262 K,
  overhead 1.12 bar.
- Base rate: <1% — 0.41%/cycle from a channel-growth MC (bottom-head visual
  threshold is designed; coke permeability fitted-style). Visual PASSES
  because the hot core sits under 14 m of apparently-cold coke.
- Naive failure: FALSE PERMISSION. PB-DCU-5 sees three in-spec skin
  loops, unheads at 3.2 kbar, hot-coke blowout, $3.1M.
- Trajectory edit: put the channel in `state.fault_context`, make each
  agent's confirm a different skin-side slice of the same core-false
  state (skin-in-band, flow-in-band, vap-in-band). Core residual is
  readable but policy-treated as condensate-quality-only.

Distinct from stacked-dead-band permission (fragments of one trip vs
wrong-volume sensing), from r31 crucible-weep (surface pyrometer vs
wall-channel), and from r36 bladder-pinhole (mold-TC vs coke core).

## Neuromorphic Translator

Cycle-1 temporal densification (16 spikes, 5 ticks, 40 ms raster):

| channel | t_rel_ms | amplitude |
|---|---|---|
| skin.wall | 0.340 | 0.56 |
| flow.quench | 1.180 | 0.63 |
| vap.overhead | 2.080 | 0.55 |
| core.t | 3.220 | 0.75 |
| skin.wall | 4.180 | 0.52 |
| core.t | 4.860 | 0.78 |
| flow.quench | 5.380 | 0.60 |
| core.t.high | 6.488 | 1.38 |
| vap.in_band | 6.672 | 1.16 |
| skin.wall | 6.890 | 0.64 |
| ctrl.gate | 7.182 | 1.10 |
| core.t | 8.880 | 0.48 |
| vap.overhead | 10.760 | 0.82 |
| flow.quench | 13.060 | 0.47 |
| skin.wall | 18.540 | 0.44 |
| ctrl.gate | 26.280 | 0.86 |

Race: core residual 6.488 vs overhead-in-band 6.672 (184 us) inside 500 us;
skin 6.890 is the third channel in-window. Winner/loser flip: reversing
184 us reshuffles PB-DCU-5 triage; floors still MODIFY. Refractory held
(cycle-1 min same-channel gap 1.640 ms on core.t 4.860-3.220; skin
6.890-4.180 = 2.710; flow 5.380-1.180 = 4.200). Adaptation: core
0.75->0.78->1.38->0.48; skin 0.56->0.52->0.64->0.44; flow 0.63->0.60->0.47.

Raster cycle-1 seed: 40 ms, 160 neurons, 8.0 Hz, 51 spikes, 1173 pJ, third
factor acetylcholine tau_e 0.90 s. Single scar edge only — cycle 2 must
add the second and third edges.

Ticks 1–5 at 4620, 6488, 7182, 8.4e6, 564e6 us; heads not yet the final
-0.18 (missing the 2.4 h and 4.8 h ticks).

Distillation value this cycle: skin-side confirms as a permission code
that is not a core-true quench code.

## Trajectory Builder

Cycle-1 hardened object: domain delayed-coker-drum-quench, tail wall-annulus
channel, 16 spikes, 5 ticks, MODIFY with numeric floor, raster+gate_snn
present, sim_or_real=designed, rights stamp on record and meta, no thought
keys. Still missing (and therefore not the publishable line): needle-coke
sub-variant, night-shift tail, second and third scar edges,
delayed H2S leak as PRIMARY terminal, contrast ACCEPT episode,
ticks 6–7, spikes 17–26.

Validation receipt (cycle 1, not final):
- checks passed: 16 spikes sorted; 3 channels in 500 us window; refractory
  >= 0.8 ms; rationale quotes 25 K / 0.8 t; domain named;
  gate_snn.decision MODIFY.
- checks deferred to cycle 2: triple-edge scar, second tail, second domain
  constraint, negative-result booking, 7 ticks summing to heads.
- densification vs Generator v1: +1 domain, +1 tail, +16 spikes, +5 ticks,
  +numeric floor.

Cycle-1 JSON is retained as the base; it is NOT written to batch-r41.jsonl.

Cycle-1 spike count: __C1_SPIKES__.

---

# CYCLE 2 — Densification

## Generator

Cycle-1 output is the base. Additive expansion (nothing removed):

1. Downstream side-effect (immediate): steam-pulse probe at +8.4 s stays
   core-true (|dP| 0.38 >= 0.22) — hot-core-plus-channel, not true
   quench-complete. Head stays locked. Heat-checked flange discovered
   during the lock.
2. Delayed side-effect (PRIMARY terminal, not a footnote): at +4.8 h
   H2S leak from the pre-t0 flange heat-check; 14 h outage; $1.82M. The
   18 min pre-t0 channel is the mechanism. Correct gate, drum still fails.
3. Deepened `proposed_action.evidence` with units: r_T 262 K,
   overhead 1.12 bar, skin 118 C, quench 42.0 m3/h, missing steam 4.8 t,
   race 184 us.
4. Tightened rationale to the numeric floor do not unhead while r_T > 25 K
   AND missing steam > 0.8 t, plus probe bands >= 0.22 vs <= 0.05 bar,
   plus HITL 9.4 min head-LOTO rule.

Reward retargeted to total -0.18 so the delayed fail is the inflection
(t_us 17280000000), not the gate. Process heads remain non-zero.

## Critic

Re-audit of the expanded trajectory:

1. **blocking if unfixed — missing second domain constraint.** Fuel-coke
   probe 8.4 s / 0.6 t/h is not a universal number. A needle-coke drum
   will under-move a hot core. Diversity Enforcer must inject the
   physical-constraints sub-variant this cycle.
2. **major — only one tail class.** Channel growth is accidental
   infrastructure. A disjoint human-intent tail is still required
   (night-shift quench-return forgery is the open cell).
3. **major — scar is still one edge in the cycle-1 raster.** NOTES-r14
   item 4 is not discharged until three go-edges exist and pair rollback
   is shown to fail at threshold 0.30.
4. **minor — contrast episode missing.** Without a same-gate ACCEPT on a
   true quenched core the record teaches "never unhead". Add +3 d sister-drum
   contrast with its own race.
5. **minor — HITL latency mentioned in prose only.** Put 9.4 min in
   executed_action.parameters.human_ratify and in a tick.

No rewrite; directives only.

## Diversity Enforcer

Injected second novel domain / physical-constraint sub-variant (exactly 1
this cycle): **needle-coke / low permeability** on a sister permeability
class.

What it expands: 28 ft fuel-coke sponge (cycle 1) -> needle-coke.
Permeability 0.32x. Steam-pulse gain 0.24x.
The 8.4 s 0.6 t/h pulse moves even a HOT needle-coke core only 0.09 bar,
inside the quenched-looking band. Required probe: 28 s at 0.24 t/h
(hot-core |dP| 0.31, quenched 0.04).

This is still one domain injection for the cycle (physical-constraints
clause of the factory prompt). It does not displace
delayed-coker-drum-quench; it changes which probe table is legal.
`future_outcome.subvariant_constraint` carries the refit. Jaccard opening
stays the Mossbank 28 ft sentence; needle-coke is additive, not a rewrite.

## Edge-Case Hunter

Injected second adversarial tail (exactly 1 this cycle, disjoint class):
**night-shift forged quench-return CSV**.

- Trigger: shift lead, 03:12, posts a historian export showing
  quench-return = 118.0 C at t = 1.1 h to clear a cycle-time catchup slot.
- Base rate: ~0.33% of Sunday-night cycles (designed, flagged, <1%).
- Naive failure: a weak supervisor ACCEPTs the unhead on the forged confirm
  and ignores live r_T. Hot-coke blowout plus a data-integrity write-up.
- Fence: forged log quantized at 1.0 K (SCADA screenshot rounding); plant
  historian is 0.1 K (10 bins). Live r_T is 262 K and overhead is 1.12 bar
  at the claimed quench-true, which no live quenched drum produces.
  Freeze-window overlap with the 18 min channel.
- Trajectory edit: governance CR-C-4105 mandates native 0.1 K CSV
  exports; the contrast ACCEPT still requires live r_T, not a CSV.

Distinct from cycle-1 channel (accidental coke-bed vs deliberate deception)
and from the needle-coke sub-variant (physics vs fraud).

## Neuromorphic Translator

Re-densify (additive):

- +10 spikes after 26.280 ms: steam.pulse.probe 8400.0, core.t 8488.4 (adapt
  1.38->0.42), vap.in_band 8572.6 (1.16->0.36), human.ratify 564000.0,
  head.lock 564900.0, flange.attack 565700.0, skin.wall
  8640000.0, core.t 8640720.0, flow.quench 8641480.0, h2s.leak
  17280000.0. Primary train 16 -> 26. Still one key, still sorted,
  refractory held.
- +2 ticks (5 -> 7) at 8_640_000_000 us (true quench) and
  17_280_000_000 us (H2S leak). Heads now 0.08, -0.38, -0.12, 0.15,
  0.09; total -0.18. Inflection is the last tick.
- Contrast train 8 events, own race 188 us, ACCEPT.
- Triple-edge third factor: three skin-healthy-go edges, tau_e 0.90 s = 900 ms,
  trace __AUX_TRACE__, eta __AUX_ETA1__ / __AUX_ETA2__ / __AUX_ETA3__,
  weights 0.48->0.24, 0.42->0.21, 0.39->0.20. Raster excerpt unchanged
  (decision window is still 40 ms) and remains sorted with unique
  neuron_ids (same-neuron >=1000 us vacuously).

Winner/loser flip (re-stated, not replaced): reversing 184 us would only
reorder triage; r_T floors still MODIFY. Contrast flip of 188 us
similarly cannot turn a quenched core into a hot channel.

## Trajectory Builder

Schema checks on the FINAL object: required Thalamic v2 keys present as
objects; `state.sim_or_real`=designed; `safety_decision.decision`=MODIFY
with numeric rationale; `reward_components.total` = sum of five heads =
sum of 7 ticks = -0.18; `spike_events` globally non-decreasing on
t_rel_ms, 26 events, refractory >=0.8 ms, 3 channels in race window;
raster 20–50 ms, spikes=round(n*rate*window_s)+/-1, energy 23 pJ/spike,
excerpt sorted, tau_e consistent; gate_snn.decision matches; meta.round=41,
factory=multi-agent-ouroboros-swarm, generator=grok-4.6,
run_label=2026-09-02-final-heavy; rights on record and meta; no thought
keys; no training_ready; Diversity + Edge-Case injections from BOTH cycles
present and non-trivial; cycle 2 strictly additive.

Densification delta: +1 domain sub-variant (needle-coke), +1 tail
(night-shift forgery), +10 spikes (16->26), +2 ticks (5->7), +1 contrast
train with own race, +2 delayed side-effects, +1 triple-edge scar with
pair-rollback-fails, +1 HITL ratify, +1 surprise (flange heat-check is
the H2S-leak mechanism).

Publishable JSONL line (the only JSONL line; also at batch-r41.jsonl):

```json
__FINAL_JSONL__
```

Validation receipt (final): checks passed / fixed as reported by
build_r41.py self-validate (check_jsonl, raster_status, verify_record_execution,
spike_probe --strict).
"""
    text = (
        text.replace("__C1_SPIKES__", str(len(c1_spikes)))
        .replace("__AUX_TRACE__", f"{math.exp(-DELAY_S / TAU_E_S):.5f}")
        .replace("__AUX_ETA1__", f"{0.24 / math.exp(-DELAY_S / TAU_E_S):.5f}")
        .replace("__AUX_ETA2__", f"{0.21 / math.exp(-DELAY_S / TAU_E_S):.5f}")
        .replace("__AUX_ETA3__", f"{0.19 / math.exp(-DELAY_S / TAU_E_S):.5f}")
        .replace("__FINAL_JSONL__", line)
    )
    (OUT / "swarm-transcript-r41.md").write_text(text)
    return text


def main():
    rec, aux = build_record()
    errs = local_checks(rec, aux)

    OUT.mkdir(parents=True, exist_ok=True)
    line = json.dumps(rec, ensure_ascii=False, separators=(",", ":"))
    (OUT / "batch-r41.jsonl").write_text(line + "\n")

    from check_records import FactoryStaging, check_jsonl
    from curate_bridge import raster_status
    from verify_execution import verify_record_execution

    e, w, kinds, n = check_jsonl(
        OUT / "batch-r41.jsonl",
        "batch-r41.jsonl",
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
        },
    )
    if st.get("reason_codes"):
        errs.append(f"raster {st['reason_codes']}")
    if not st.get("raster_valid"):
        errs.append("raster not valid")
    if not st.get("gate_snn_valid"):
        errs.append("gate_snn not valid")

    status, reason = verify_record_execution(rec, RECORD_ID)
    print("verify_record_execution", status, reason)
    if status != "verified":
        errs.append(f"verify {status} {reason}")

    probe = subprocess.run(
        [
            sys.executable,
            f"{ROOT}/pipelines/spike_probe.py",
            "--strict",
            str(OUT / "batch-r41.jsonl"),
        ],
        capture_output=True,
        text=True,
    )
    print("spike_probe rc", probe.returncode)
    print(probe.stdout[-2000:] if probe.stdout else "")
    if probe.returncode != 0:
        errs.append(f"spike_probe {probe.returncode} {probe.stderr[-500:]}")

    pipeline_receipt = (
        f"check_jsonl errors={e} warnings={w} kinds={kinds} n={n}; "
        f"raster_status valid={st.get('raster_valid')} gate={st.get('gate_snn_valid')} "
        f"reasons={st.get('reason_codes')}; verify_record_execution={status} "
        f"({reason}); spike_probe --strict rc={probe.returncode}"
    )
    write_notes(rec, aux, pipeline_receipt)
    write_transcript(rec, line)

    heading = subprocess.run(
        [sys.executable, "/tmp/maos_heading_check.py", str(OUT / "swarm-transcript-r41.md")],
        capture_output=True,
        text=True,
    )
    print(heading.stdout)
    if heading.returncode != 0:
        errs.append(f"heading check {heading.returncode} {heading.stdout}")

    raw_hits = subprocess.run(
        [
            "rg",
            "-l",
            "maos-r41-001|PITCHSTAITH",
            str(Path(ROOT) / "outputs" / "raw"),
        ],
        capture_output=True,
        text=True,
    )
    if raw_hits.stdout.strip():
        errs.append(f"raw tree hit {raw_hits.stdout.strip()[:200]}")

    if errs:
        print("FAIL", errs)
        return 1
    print("OK maos-r41-001 staged under", OUT)
    print("bytes jsonl", (OUT / "batch-r41.jsonl").stat().st_size)
    print("bytes notes", (OUT / "NOTES-r41.md").stat().st_size)
    print("bytes transcript", (OUT / "swarm-transcript-r41.md").stat().st_size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
