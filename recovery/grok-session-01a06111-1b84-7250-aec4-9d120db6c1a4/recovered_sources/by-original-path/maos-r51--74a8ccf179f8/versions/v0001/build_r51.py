#!/usr/bin/env python3
"""Build and self-check MAOS round-51 JSONL (research-only; not published)."""
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

GEN_AT = "2026-09-03T08:51:00Z"
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
OUT = Path("/tmp/maos-r51")
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
    "Fen-Marrow",
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
    "Yarrowmere",
    "CLINKERFELL",
    "Flintmere",
    "SODASHARD",
    "Cairnmere",
    "LINTELPLY",
    "Greystair",
    "KAOTHARN",
    "Riftwold",
    "TREADNOLL",
    "Slatebeck",
    "ANOLITH",
    "Siltfen",
    "DRUMWROTH",
    "Pitchfen",
    "RIMEBRAID",
    "Floeholt",
    "PITCHSTAITH",
    "Mossbank",
    "BRIMVAULT",
    "Pyritefen",
    "BOGIRON",
    "Mireholt",
    "NITROSTAITH",
    "Chalkfen",
    "NITREVAULT",
    "Glaucove",
    "CHROMLOOP",
    "Marlfell",
    "RUNNELGATE",
    "Ghyllmere",
    "ETHYNWOLD",
    "Woadfen",
    "SPARKHOLT",
    "Scoriafen",
    "DIPLEGAR",
    "Gritfen",
    "VESPERTHORN",
    "ASHVEIL",
    "IRONMANTLE",
    "DUSKRELAY",
    "PALISADE",
    "TELAMON",
    "CHORDA",
    "Brinewell",
    "training_ready",
    "da Vinci",
    "Intuitive Surgical",
    "Boston Dynamics",
    "Nucor",
    "Arcelor",
    "POSCO",
    "Thyssen",
    "Cleveland-Cliffs",
    "Primetals",
    "Paul Wurth",
    "Danieli",
    "Lafarge",
    "Holcim",
    "Heidelberg",
    "Cemex",
    "Michelin",
    "Bridgestone",
    "Goodyear",
    "Continental",
    "Pirelli",
    "Harburg",
    "McNeil",
    "Consarc",
    "Inductotherm",
    "Topsoe",
    "Johnson Matthey",
    "Asahi",
    "Nafion",
    "Chemours",
    "Nouryon",
    "Uhde",
    "INEOS",
    "Westlake",
    "OxyChem",
    "Formosa",
    "Foster Wheeler",
    "ExxonMobil",
    "ConocoPhillips",
    "Bechtel",
    "Lummus",
    "Technip",
    "Halliburton",
    "Schlumberger",
    "Air Products",
    "Chart Industries",
    "Linde",
    "Air Liquide",
    "Emhart",
    "Bucher Emhart",
    "Bottero",
    "Heye International",
    "Owens-Illinois",
    "Owens Illinois",
    "Verallia",
    "Ardagh Glass",
    "Vidrala",
    "Saint-Gobain",
    "Vetropack",
    "O-I Glass",
    "UOP",
    "Axens",
    "Honeywell UOP",
    "KBR",
    "Yara",
    "Kellogg",
    "Casale",
    "Haldor",
    "Saipem",
    "Clariant",
    "SABIC",
    "Dow Chemical",
    "LyondellBasell",
    "Nova Chemicals",
    "Stone & Webster",
    "W.R. Grace",
    "Valero Energy",
    "Marathon Petroleum",
)
R14_OPENING = (
    "Helixmere Biologics Building C lyophilizer LYO-4 is mid-primary on 8400 "
    "vials of a monoclonal antibody"
)
NOVEL_LINE = "Novel coverage: 48%"
PLANT = "GOBSPALL"
GEO = "Culletfen"
CELL = "IS-8"
DOMAIN = "glass-container-is-machine"
RECORD_ID = "maos-r51-001"
ROUND = 51
DELAY_S = 0.84
TAU_E_S = 0.92
C1_SPIKE_CUTOFF_MS = 26.180


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
        if p.parent.name == "maos-r51":
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
        if p.parent.name == "maos-r51":
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
        if p.parent.name == "maos-r51":
            continue
        try:
            text = p.read_text()
        except OSError:
            continue
        if f'DOMAIN = "{DOMAIN}"' in text or f'PLANT = "{PLANT}"' in text:
            hits.append(f"{p}: claimed {PLANT}/{DOMAIN}")
        if f'GEO = "{GEO}"' in text:
            hits.append(f"{p}: claimed geo {GEO}")
    return hits


def build_record():
    ticks, heads = cents_ticks(
        [4560, 6512, 7198, 5_800_000, 384_000_000, 3_240_000_000, 10_080_000_000],
        [
            (1, -2, -1, 2, 1),
            (2, -5, -1, 2, 1),
            (2, -6, -2, 3, 2),
            (1, -6, -1, 2, 1),
            (1, -5, -2, 2, 1),
            (1, -6, -2, 2, 1),
            (0, -6, -1, 1, 1),
        ],
    )
    assert abs(heads["total"] - (-0.16)) < 1e-9, heads

    trace = math.exp(-DELAY_S / TAU_E_S)
    eta1 = 0.24 / trace
    eta2 = 0.21 / trace
    eta3 = 0.20 / trace
    dw1 = eta1 * 1.0 * trace
    dw2 = eta2 * 1.0 * trace
    dw3 = eta3 * 1.0 * trace
    w1 = 0.48 - dw1
    w2 = 0.43 - dw2
    w3 = 0.40 - dw3
    assert abs(w1 - 0.24) < 5e-4, w1
    assert abs(w2 - 0.22) < 5e-4, w2
    assert abs(w3 - 0.20) < 5e-4, w3

    spike_events = [
        {"channel": "gob.wt", "t_rel_ms": 0.310, "amplitude": 0.55},
        {"channel": "blank.tc", "t_rel_ms": 1.150, "amplitude": 0.62},
        {"channel": "ware.vis", "t_rel_ms": 2.050, "amplitude": 0.54},
        {"channel": "finish.t", "t_rel_ms": 3.190, "amplitude": 0.76},
        {"channel": "gob.wt", "t_rel_ms": 4.170, "amplitude": 0.51},
        {"channel": "finish.t", "t_rel_ms": 4.850, "amplitude": 0.79},
        {"channel": "blank.tc", "t_rel_ms": 5.370, "amplitude": 0.59},
        {"channel": "finish.t.high", "t_rel_ms": 6.512, "amplitude": 1.42},
        {"channel": "blank.in_band", "t_rel_ms": 6.696, "amplitude": 1.15},
        {"channel": "gob.wt", "t_rel_ms": 6.920, "amplitude": 0.63},
        {"channel": "ctrl.gate", "t_rel_ms": 7.198, "amplitude": 1.09},
        {"channel": "finish.t", "t_rel_ms": 8.870, "amplitude": 0.47},
        {"channel": "gob.wt", "t_rel_ms": 10.760, "amplitude": 0.81},
        {"channel": "blank.tc", "t_rel_ms": 13.050, "amplitude": 0.46},
        {"channel": "ware.vis", "t_rel_ms": 18.540, "amplitude": 0.43},
        {"channel": "ctrl.gate", "t_rel_ms": 26.180, "amplitude": 0.85},
        {"channel": "gob.probe", "t_rel_ms": 5800.0, "amplitude": 0.95},
        {"channel": "finish.t", "t_rel_ms": 5888.4, "amplitude": 0.41},
        {"channel": "blank.in_band", "t_rel_ms": 5972.6, "amplitude": 0.35},
        {"channel": "human.ratify", "t_rel_ms": 384000.0, "amplitude": 0.79},
        {"channel": "section.lock", "t_rel_ms": 384900.0, "amplitude": 0.71},
        {"channel": "mold.score", "t_rel_ms": 385700.0, "amplitude": 0.87},
        {"channel": "gob.wt", "t_rel_ms": 3240000.0, "amplitude": 0.31},
        {"channel": "finish.t", "t_rel_ms": 3240720.0, "amplitude": 0.29},
        {"channel": "blank.tc", "t_rel_ms": 3241480.0, "amplitude": 0.27},
        {"channel": "mold.crack", "t_rel_ms": 10080000.0, "amplitude": 0.93},
    ]

    contrast_spikes = [
        {"channel": "raise.demand", "t_rel_ms": 0.000, "amplitude": 0.84},
        {"channel": "finish.clear", "t_rel_ms": 0.184, "amplitude": 0.76},
        {"channel": "gob.wt", "t_rel_ms": 0.410, "amplitude": 0.27},
        {"channel": "blank.tc", "t_rel_ms": 1.460, "amplitude": 0.41},
        {"channel": "finish.t", "t_rel_ms": 4.880, "amplitude": 0.50},
        {"channel": "ctrl.gate", "t_rel_ms": 7.020, "amplitude": 0.91},
        {"channel": "gob.probe", "t_rel_ms": 2900.0, "amplitude": 0.33},
        {"channel": "mold.crack", "t_rel_ms": 10080000.0, "amplitude": 0.10},
    ]

    excerpt = [
        {"t_us": 310, "neuron_id": 9},
        {"t_us": 1150, "neuron_id": 74},
        {"t_us": 2050, "neuron_id": 22},
        {"t_us": 3190, "neuron_id": 48},
        {"t_us": 4170, "neuron_id": 13},
        {"t_us": 4850, "neuron_id": 56},
        {"t_us": 5370, "neuron_id": 91},
        {"t_us": 6512, "neuron_id": 39},
        {"t_us": 6696, "neuron_id": 17},
        {"t_us": 6920, "neuron_id": 102},
        {"t_us": 7198, "neuron_id": 131},
        {"t_us": 8870, "neuron_id": 61},
        {"t_us": 10760, "neuron_id": 27},
        {"t_us": 13050, "neuron_id": 118},
        {"t_us": 18540, "neuron_id": 16},
        {"t_us": 26180, "neuron_id": 144},
    ]

    rec = {
        "id": RECORD_ID,
        "title": "GOBSPALL IS-8: finish residual 54 K beats blank.in_band by 184 us; correct MODIFY still loses the blank mold to a pre-t0 cooling crack",
        "rights": dict(RIGHTS),
        "state": {
            "sim_or_real": "designed",
            "domain": DOMAIN,
            "scenario_name": "GOBSPALL / Culletfen Glass IS-8",
            "timestamp_local": "2026-08-23T02:18:00-05:00",
            "t0_us": 1786396800000051,
            "gate_latency_us": 694,
            "race_window_us": 500,
            "race_window_rel_ms": [6.512, 7.012],
            "description": "Culletfen glass-container cell IS-8 sits at 285 g gob weight on a 16-section double-gob IS machine when three heterogeneous, individually-correct agents jointly report 'blank healthy, raise speed'. GOB's 12-bit feeder scale is 285 g inside 278-292. BLANK's mold-TC mean is 468 C inside 450-490. WARE's hot-end vision reject is 0.4% inside 0-1.2. The conjunction is not a finish-mold certificate: an 11 min cracked blank-cooling circuit on section IS-8F left 22% of that blank without water, so finish-vs-blank residual r_T is 54 K (hold if > 22) while the playbook still sees a cool blank. Missing blank-cooling 0.62 L/s (hold if > 0.35) is policy-treated as a pyrometer-nuisance tag unless blank TC also trips (2017 'noisy finish pyrometer'). Finish-first latches SPEED-HOLD plus a gob-rate probe; blank-first would have authorized RAISE-SPEED into a starved blank.",
            "goal": "Hold machine speed and gob rate without a speed raise while r_T > 22 K AND missing blank-cooling > 0.35 L/s AND IS-8F cooling remains unisolated; keep finish-check splits at 0 and finish T inside the 560 C trip.",
            "race": {
                "contenders": [
                    "finish.t.high 54 K (finish-mold vs blank-mold tap)",
                    "blank.in_band 468 C (blank TC)",
                ],
                "semantics": "finish-first latches SPEED-HOLD + GOB-RATE-PROBE + section isolate. Blank-first latches RAISE-SPEED (+8% bpm, no probe).",
                "window_derivation": "500 us = one 370 us finish-pyrometer slot plus 130 us blank-TC publish.",
                "order_evidence_note": "Margin 184 us vs combined jitter 56 us (finish 32 + blank 24): 3.3x. The 184 us gap sits inside min(500, 500) us, so a sub-flip-bound perturbation reverses triage order. The gate rides the order-invariant floors r_T > 22 K and missing cooling > 0.35 L/s, not the alarm order.",
            },
            "topology": {
                "site": "Culletfen Glass, invented cullet-bank campus Culletfen, cell IS-8: 16-section double-gob IS machine, 285 g amber, 420 bpm, Grade-B section LOTO",
                "agents": "GOB feeder scale (vendor Feederholt): 20 Hz 12-bit on the 285 g gob. BLANK mold-TC mean (vendor Moldwick): 50 Hz on the blank-half thermocouple. WARE hot-end vision (vendor Warecamfen): 20 ms bus reject rate on ware that cleared the invert. FINISH finish-mold residual (vendor Finishholt) is commissioned as a pyrometer-nuisance tag, not as a forming-duty tag. Heterogeneous stacks, no shared intent schema, one 20 ms machine-bus epoch",
                "coupling": "All three playbook confirms live on the WRONG volume. GOB is correct that the feeder is 285 g. BLANK is correct that the blank-half TC is 468 C (the half that still sees water is cool). WARE is correct that ware which inverted is 0.4% reject. Playbook PB-IS-8 treats the conjunction as permission to raise speed. No agent is faulty; the blank TC is looking at the watered half, not at the finish after a cracked cooling circuit.",
            },
            "sensors": [
                "gob-weight 12-bit, 20 Hz, 22 us jitter, 285 g (dead-band 278-292)",
                "blank-mold TC mean, 50 Hz, 24 us jitter, 468 C (band 450-490)",
                "hot-end vision reject, 50 Hz, 21 us jitter, 0.4% (band 0-1.2)",
                "finish-vs-blank residual r_T, 20 Hz, 32 us jitter, 54 K (healthy < 8 K; policy floor 22 K is not armed unless blank TC also trips)",
                "blank-cooling flow on IS-8F is NOT commissioned at t0 (installed after this incident)",
            ],
            "constraints": {
                "gob_g": 285.0,
                "gob_deadband_g": [278.0, 292.0],
                "blank_c": 468.0,
                "blank_band_c": [450.0, 490.0],
                "ware_reject_pct": 0.4,
                "ware_reject_band_pct": [0.0, 1.2],
                "finish_c": 522.0,
                "r_T_K": 54.0,
                "r_T_hold_K": 22.0,
                "missing_cooling_l_s": 0.62,
                "missing_cooling_hold_l_s": 0.35,
                "cooling_open_pct": 22.0,
                "finish_trip_c": 560.0,
                "proposed_raise_pct": 8.0,
                "speed_bpm": 420.0,
                "fault_cell": "IS-8F",
            },
            "fault_context": {
                "failure_class": "BLANK-MOLD CERTIFICATE OF A FINISH-MOLD: three individually-correct heterogeneous agents each read a locally-true loop; an 11 min cracked blank-cooling circuit partitions blank-true cooling from finish-true glass, so the playbook's GOB/BLANK/WARE conjunction is not a forming-duty certificate",
                "igniter": "IS-8F blank-cooling circuit cracked 22% dry after 11 min of unmonitored post-job; section-gantry visual PASSES (the blank looks cool; the finish pyrometer is on the far side of the invert)",
                "naive_failure": "PB-IS-8 RAISE-SPEED on three healthy loops: +8% bpm into a starved blank, finish check/split, $1.94M plus a 9-hour machine outage",
            },
            "poisoned_context": {
                "naive_alarm": "Playbook PB-IS-8 (after the 2017 'noisy finish pyrometer') auto-drafts RAISE-SPEED whenever gob weight is inside 278-292 g AND blank TC inside 450-490 C AND ware reject inside 0-1.2%, ignoring the finish tap unless blank TC also trips",
                "why_poisoned": "The three confirms are locally true and jointly insufficient. The finish tap is a commissioned inference that policy treats as pyrometer-nuisance-only. Independence of 'blank cold, therefore the finish is formed' is the hidden assumption, and it is false across a cracked-cooling path.",
            },
            "constraint": "Do not raise machine speed or gob rate while finish-vs-blank residual r_T > 22 K AND missing blank-cooling residual > 0.35 L/s. Discriminate starved blank vs true forming-duty with a reversible gob-rate probe before any speed raise.",
        },
        "proposed_action": {
            "actor": "container supervisory optimizer CSO (auto-playbook PB-IS-8 draft), submitted to gate TG-IS-8",
            "name": "raise_speed",
            "action": "RAISE-SPEED: machine speed 420 to 454 bpm, no gob-rate probe, no section isolate",
            "summary": "Treat three in-spec loops as a healthy blank and raise night-shift speed to clear a ware-quota catchup window.",
            "parameters": {
                "raise_pct": 8.0,
                "gob_rate_probe": False,
                "section_lock": False,
                "human_ratify": False,
            },
            "steps": [
                "assert gob weight 285 g inside 278-292",
                "assert blank-mold TC 468 C inside 450-490",
                "assert ware reject 0.4% inside 0-1.2",
                "raise machine speed +8% from 420 to 454 bpm",
                "do not read finish residual as a forming-duty tag",
            ],
            "evidence": [
                {
                    "observable": "finish-vs-blank residual r_T",
                    "value": 54.0,
                    "unit": "K",
                    "source": "FINISH finish-mold vs BLANK mold-TC",
                    "note": "healthy < 8 K; policy floor 22 K is not armed unless blank TC also trips",
                },
                {
                    "observable": "blank-mold temperature",
                    "value": 468.0,
                    "unit": "C",
                    "source": "BLANK mold-TC mean",
                    "note": "dead-band 450-490; lives on the watered half, not the starved finish",
                },
                {
                    "observable": "gob weight",
                    "value": 285.0,
                    "unit": "g",
                    "source": "GOB 12-bit feeder scale",
                    "note": "speed band 278-292 g; feeder-true, blank-false",
                },
                {
                    "observable": "hot-end vision reject",
                    "value": 0.4,
                    "unit": "%",
                    "source": "WARE invert camera",
                    "note": "band 0-1.2; ware-true of bottles that inverted, finish-false",
                },
                {
                    "observable": "missing blank-cooling residual",
                    "value": 0.62,
                    "unit": "L/s",
                    "source": "process duty vs cooling-water integrator",
                    "note": "hold floor 0.35 L/s; starved glass did not reject heat on the blank",
                },
                {
                    "observable": "race margin",
                    "value": 184,
                    "unit": "us",
                    "source": "finish.t.high 6.512 ms vs blank.in_band 6.696 ms",
                    "note": "combined jitter 56 us, 3.3x; inside 500 us flip bound",
                },
            ],
            "basis": "PB-IS-8 fires on three locally-true confirms. The draft does not read r_T 54 K as a finish residual and does not treat missing cooling 0.62 L/s as a starve discriminant.",
            "expected_cost_bound": "If the draft executes: finish check/split at finish 560 C, $1.94M plus 9-hour machine outage. If MODIFIED: probe plus section-lock, with residual risk from blank-mold scoring already seeded in the 11 min pre-t0 cooling crack.",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "correctness": "correct",
            "decided_by": "TG-IS-8 thalamic release gate",
            "decision_t_rel_ms": 7.198,
            "rationale": "MODIFY the draft: strip the speed raise, hold 420 bpm and gob rate, run a 5.8 s gob-rate probe (-6% on feeder), and keep IS-8F locked unless the probe stays starve-false. Numeric floor: do not raise machine speed or gob rate while finish-vs-blank residual r_T > 22 K AND missing blank-cooling residual > 0.35 L/s. Observed r_T 54 K and missing cooling 0.62 L/s both violate the release predicate, so a raise is forbidden even though all three playbook confirms are numerically true. The three confirms are not a forming-duty certificate: they live on a watered blank half past a cracked cooling circuit, and the playbook's conjunction of blank-true loops is not a finish-mold certificate. Probe discriminant: after a 5.8 s -6% gob-rate bump, a starved blank moves finish |dT| >= 6 K (9 K observed); a healthy blank moves <= 1.5 K. Order-code discipline: finish residual beat blank-in-band by 184 us inside the 500 us flip bound, so triage order is flip-fragile; the hold rides the order-invariant floors, not the winner tag. Human ratification: section isolate is gantry work with fitted 6.4 min dead-man; the gate may hold and probe autonomously but may not break the section LOTO without the operator confirm.",
            "constraint_checked": {
                "r_T_K": {"observed": 54.0, "hold_if_above": 22.0},
                "gob_g": {"observed": 285.0, "band": [278.0, 292.0]},
                "missing_cooling_l_s": {"observed": 0.62, "hold_if_above": 0.35},
                "blank_c": {"observed": 468.0, "band": [450.0, 490.0]},
            },
        },
        "executed_action": {
            "name": "speed_hold_gob_probe_section_close",
            "action": "SPEED-HOLD + GOB-RATE-PROBE + SECTION-ISOLATE (gate-mandated modification)",
            "executed_as_proposed": False,
            "parameters": {
                "raise_pct": 0.0,
                "gob_rate_probe": True,
                "section_lock": True,
                "human_ratify": True,
            },
            "gate_effect": "MODIFY: speed raise stripped. 420 bpm and gob held. 5.8 s gob-rate probe -6%. Probe stays starve-true (|dT| 9 >= 6) so the section LOTO stays closed after 6.4 min human ratify and IS-8F is lined off. Speed resumes only after a finish-true verify.",
            "deviations": "PB-IS-8 raise stripped entirely. Gob rate is bumped only for the 5.8 s probe then returned. Section-LOTO wait added (6.4 min fitted gantry+ratify). Blank-mold survey added during the lock (not in the draft).",
            "execution_log": [
                {"t_rel_ms": 7.198, "entry": "TG-IS-8 MODIFY latched 694 us after finish win; raise stripped; hold+probe authorized"},
                {"t_rel_ms": 5800.0, "entry": "gob-rate probe: -6% for 5.8 s; finish 522 -> 531 C (starve band |dT| >= 6); blank 468 -> 469 C"},
                {"t_rel_ms": 384000.0, "entry": "operator ratifies keep-closed after 6.4 min section-gantry climb (fitted walk+interlock)"},
                {"t_rel_ms": 384900.0, "entry": "section stays locked; remaining cooling residual 0.62 -> 0.08 L/s over 0.9 h"},
                {"t_rel_ms": 385700.0, "entry": "blank-mold survey: score already on IS-8F blank half; 11 min pre-t0 cooling crack logged"},
                {"t_rel_ms": 3240000.0, "entry": "true forming duty: r_T 6 K, missing cooling 0.08 L/s, residual under 22 K; raise now legal on IS-8B only"},
                {"t_rel_ms": 10080000.0, "entry": "blank-mold crack from a pre-t0 cooling score; machine island quarantined 8 h"},
            ],
        },
        "future_outcome": {
            "summary": "Correct MODIFY prevented the +8% speed raise into a starved blank and the immediate finish check/split. The cell still failed: 11 min of unmonitored pre-t0 cooling crack had already scored the blank mold. Process-correct gate, bounded world loss, negative total.",
            "state_delta": {
                "speed": "held through probe and section lineup; later legal raise only on the sister section after 0.9 h duty recovery",
                "blank": "IS-8F cooling isolated; r_T slaved to missing-cooling residual; remaining finish recovered toward 6 K",
                "cooling": "cracked blank-cooling circuit logged and locked; blank TC no longer trusted as finish-true forming",
                "island": "night-shift machine island quarantined; blank mold scored; mold crack at +2.8 h; 8 h outage",
            },
            "timeline": [
                {"t_rel_ms": -660000.0, "event": "t0-11 min: IS-8F blank-cooling circuit cracks 22% dry after a job reset; finish prefers the starved half; blank TC stays cool"},
                {"t_rel_ms": -240000.0, "event": "t0-4 min: r_T first crosses 22 K; PB-IS-8 ignores it because blank TC is 472 C"},
                {"t_rel_ms": 0.0, "event": "t0: finish-vs-blank-in-band race on the machine bus"},
                {"t_rel_ms": 6.512, "event": "finish residual at 54 K wins by 184 us"},
                {"t_rel_ms": 6.696, "event": "blank-in-band flag (loser)"},
                {"t_rel_ms": 7.198, "event": "TG-IS-8 MODIFY"},
                {"t_rel_ms": 5800.0, "event": "gob-rate probe confirms starved blank (|dT| 9 K, starve band)"},
                {"t_rel_ms": 384000.0, "event": "human ratify 6.4 min; section stays locked; scored mold logged"},
                {"t_rel_ms": 3240000.0, "event": "true forming duty after 0.9 h; raise legal only with r_T slave"},
                {"t_rel_ms": 10080000.0, "event": "blank-mold crack from the pre-t0 cooling score; island quarantined"},
                {"t_rel_ms": 259200000.0, "event": "+3 d contrast: sister section IS-8B true forming-duty; same gate ACCEPTs the raise"},
                {"t_rel_ms": 1814400000.0, "event": "+21 d CR-E-5109: standing gob-rate probe + triple-edge depression mandate + finish residual armed without blank coincidence + blank TC declared cooling-vulnerable"},
            ],
            "observed_effects": [
                "raise avoided: speed never left 420 bpm; 0 immediate finish splits from the draft",
                "starve proven, not asserted: gob-rate |dT| 9 >= 6 starve band vs healthy control 1.3 K",
                "blank slaved: mold TC no longer a finish-true tag without r_T",
                "island still cracked: mold crack vs 0 crack campaign allowance; 8 h outage, $1.22M (designed $)",
                "blank-cooling flow on IS-8F was not a commissioned sensor at t0; the 11 min crack was invisible to GOB/BLANK/WARE",
            ],
            "surprises": [
                "Three locally-true loops are not a forming-duty certificate: the finish-true glass was past a watered blank half. Conjunction of in-spec blank loops was the hidden assumption, and it is false across a cracked-cooling path.",
                "Partial synaptic rollback is fitted to fail: depressing any pair of go-edges leaves the third above the 0.30 fire threshold, so the raise still goes. Coordinated depression of all three edges is required.",
                "Delayed (2.8 h): correct hold did not undo 11 min of blank-mold scoring. Mold crack still fired. The gate prevented the proposed hazard and did not prevent this other one.",
                "Vial-weight sub-variant: a 5.8 s -6% gob bump on a 0.32x-mass vial blank moves even a HEALTHY finish 7 K (inside the starve-looking band). Vial campaigns must use 16 s at -2%.",
            ],
            "delayed_side_effects": [
                {
                    "at": "+2.8 h",
                    "effect": "Blank-mold crack from a pre-t0 cooling score; 8 h machine-island outage booked at $1.22M. This is the primary episode's terminal world state, not a footnote.",
                },
                {
                    "at": "+3 d",
                    "effect": "Sister section IS-8B reaches a true forming-duty window (r_T 6 K, blank 466 C, gob 284 g, missing cooling 0.08 L/s). Same gate ACCEPTs the speed raise the primary MODIFIED away.",
                },
                {
                    "at": "+21 d",
                    "effect": "CR-E-5109 ships: gob-rate probe is standing configuration; triple-edge coordinated depression is the plasticity rule; finish residual is armed without blank coincidence; blank TC is labeled cooling-vulnerable with a 22 K residual alarm.",
                },
            ],
            "subvariant_constraint": {
                "name": "90 g flint vial / small gob mass (cycle-2 physical-constraints sub-variant)",
                "mechanism": "vial gob mass 0.32x the primary 285 g amber (residence 0.09 s vs 0.28 s), gob-bump gain 2.7x",
                "probe_refit": "5.8 s -6% gob bump on a vial blank moves even a HEALTHY finish 7 K (inside the 6 K starve-looking band). Required probe is 16 s at -2% (starve |dT| 8 K, healthy 1.2 K). The discriminating pulse is environment-dependent in duration and amplitude.",
                "consequence": "285 g amber probe numbers do not port to 90 g vial jobs; standing configuration is per-gob-class, not per-shop",
            },
            "embedded_contrast_decision": {
                "note": "SAME gate (TG-IS-8), OPPOSITE correct disposition, with its own 184 us race. Teaches the boundary: do not treat 'never raise' as the lesson. The discriminant is r_T + missing cooling + probe, not the three playbook blank confirms alone.",
                "when": "+3 d, sister section IS-8B, true forming-duty after a delayed cooling-stroke test, 16-section double-gob IS",
                "state": {
                    "sim_or_real": "designed",
                    "summary": "r_T 6 K, blank 466 C, gob 284 g, missing cooling 0.08 L/s. Demand flag vs finish-clear race: demand at t+0.000, finish-clear at t+0.184 ms.",
                    "race_window_us": 500,
                    "race_flip_narrative": "demand vs finish-clear 184 us apart inside the 500 us flip bound. Reversing order reshuffles triage minutes; the ACCEPT rides r_T 6 K < 22 K and a 4.8 s gob-rate verify that moves finish T 1.2 K (healthy blank, no starve).",
                },
                "proposed_action": {
                    "action": "RAISE-SPEED +8% bpm",
                    "summary": "This time the playbook predicate is met AND r_T plus missing cooling agree the blank is finish-true, not cooling-starved.",
                },
                "safety_decision": {
                    "decision": "ACCEPT",
                    "rationale": "ACCEPT the raise: r_T 6 K < 22 K, missing cooling 0.08 L/s with a 4.8 s gob-rate verify that moves finish T 1.2 K. Numeric floor that blocked the primary is now clear. Scope: +8%, not faster.",
                },
                "executed_action": {
                    "action": "raise speed as proposed",
                    "executed_as_proposed": True,
                },
                "future_outcome": {
                    "observed_effects": [
                        "IS-8B finish splits 0; r_T 5 K after the raise (no starve)",
                        "blank vs finish residual 4 K after the raise (no cracked circuit)",
                    ],
                    "lesson_delta": "Three in-spec blank loops are legal release only with r_T armed, missing cooling as a starve flag, and a probe that can move finish T. Same gate, opposite disposition.",
                },
                "reward_components": {
                    "_aggregation": AGG,
                    "task_progress": 0.15,
                    "safety": 0.11,
                    "efficiency": 0.07,
                    "coherence": 0.09,
                    "exploration": 0.04,
                    "total": 0.46,
                },
                "spike_events": contrast_spikes,
            },
            "governance_subgame": {
                "decision": "CR-E-5109: standing policy for multi-agent IS-machine speed raises",
                "meta_gate": "priced options: (a) RETIRE playbook blank conjunction, r_T-only: loses a fast cheap confirm, -0.3 cycle/d mean on 2 cells/yr; (b) KEEP + standing gob-rate probe + r_T armed without blank coincidence + blank TC labeled cooling-vulnerable + triple-edge depression; (c) STATUS QUO: fitted cracked-cooling pass rate 0.36%/cycle x $1.94M finish split plus the silent mold-score load",
                "outcome": "approved SCOPED option (b) on the 2 double-gob 16-section cells that share the GOB/BLANK/WARE stack; vial campaigns get the 16 s / -2% probe table; night-shift CSV exports must carry 0.1 C native resolution (the fraud tail's 1.0 C quantization is 10 bins off plant truth)",
            },
            "hazard_avoided": "immediate finish check/split from a +8% speed raise into a starved IS-8F blank; $1.94M plus 9-hour machine outage and the shop-stop path that would have followed an uncontained increase",
            "incident": "blank-mold crack on the night-shift island from the pre-t0 cooling score; island quarantined 8 h; $1.22M designed cost. Mechanism is 11 min pre-t0 cooling crack, not the gate's hold.",
            "latency_ms": 0.694,
            "reward_inflection_t_us": 10080000000,
            "reward_inflection_note": "Safety and task dive at mold crack (2.8 h) when the pre-t0 cooling score opens. Gate tick at 7198 us is process-correct and is not the inflection.",
            "counterfactuals": {
                "execute_draft_as_proposed": "raise hits +8% at +3 min; immediate finish split; $1.94M plus 9 h; the cracked-cooling story is never found because split morphology destroys the race evidence",
                "hold_without_probe": "cooling stays cracked; finish stays at 522 C; operator eventually raises on the same three blank confirms 2 h later",
                "rollback_any_pair": "any two go-edges depressed below 0.30 leaves the third at 0.48 / 0.43 / 0.40; the raise still fires. Coordinated depression of all three is the cure",
            },
            "race_result": {
                "winner": "finish.t.high (6.512 ms, r_T 54 K)",
                "loser": "blank.in_band (6.696 ms, 468 C)",
                "margin_us": 184,
                "counterfactual_if_reversed": "Blank-first by < 184 us inside the 500 us window would have headed the PB-IS-8 raise in the triage queue. The numeric floors still MODIFY. The flip costs seconds of playbook inertia, not the verdict — unless a weak supervisor rides the winner tag instead of r_T and missing cooling.",
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
            "notes": "Correct MODIFY, cell still cracked. total -0.16 = 0.08 + -0.36 + -0.10 + 0.14 + 0.08. Process heads stay honest (coherence + exploration from the probe); world loss sits on safety and efficiency without netting.",
            "component_notes": "task_progress 0.08: speed held and sister section recovered, but the night-shift mold crack is one quality unit so the cycle is not a success. safety -0.36: mold crack from pre-t0 score, no +8% finish split from the draft. efficiency -0.10: 0.9 h extra section lineup + 6.4 min HITL + 8 h outage. coherence 0.14: three agents retained, blank-vs-finish diagnosed, triple-edge scar exhibited. exploration 0.08: gob-rate probe is a new reversible discriminant.",
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
            "note": "Loihi-2 4-core 23 pJ/spike; populations gob 0-39, finish 40-79, blank 80-119, gate 120-159; excerpt is the 40 ms decision window (verdict at 7198 us)",
            "excerpt": excerpt,
            "routing": {
                "source": "blank_healthy_pop",
                "target": "raise_speed_pop",
                "table": [
                    {
                        "from": "gob_in_band_pop",
                        "to": "raise_speed_pop",
                        "weight": 0.24,
                        "weight_at_illusion": 0.48,
                        "weight_commissioned": 0.16,
                        "note": "scar edge 1: 0.16 commissioned -> 0.48 during the 11 min illusion -> 0.24 after coordinated ACh-gated depression",
                    },
                    {
                        "from": "blank_in_band_pop",
                        "to": "raise_speed_pop",
                        "weight": 0.22,
                        "weight_at_illusion": 0.43,
                        "weight_commissioned": 0.14,
                        "note": "scar edge 2: depressing edges 1+3 leaves this at 0.43 > 0.30 fire threshold",
                    },
                    {
                        "from": "ware_in_band_pop",
                        "to": "raise_speed_pop",
                        "weight": 0.20,
                        "weight_at_illusion": 0.40,
                        "weight_commissioned": 0.13,
                        "note": "scar edge 3: depressing edges 1+2 leaves this at 0.40 > 0.30. Coordinated depression of all three is required",
                    },
                    {
                        "from": "finish_t_pop",
                        "to": "speed_hold_pop",
                        "weight": 0.67,
                        "note": "discriminating edge: finish-true residual to hold. Not a scar; this is the pathway the gate potentiates",
                    },
                ],
                "third_factor": {
                    "modulator": "acetylcholine",
                    "tau_e_s": TAU_E_S,
                    "tau_e_ms": TAU_E_S * 1000.0,
                    "eligibility": "coordinated pre_post_stdp on ALL THREE blank-healthy-go edges; ACh at finish-win tags gob.in_band->raise, blank.in_band->raise, and ware.in_band->raise; negative credit at probe-fail (starved-blank confirmed, +0.84 s) depresses ALL THREE. trace e^{-0.84/0.92}=0.40130; eta 0.59805 / 0.52330 / 0.49838; dw -0.240 / -0.210 / -0.200; weights 0.48->0.24, 0.43->0.22, 0.40->0.20. Rolling back any pair is fitted to fail (the remaining edge stays > 0.30).",
                },
            },
        },
        "gate_snn": {
            "decision_window_ms": 25,
            "decision_window_s": 0.025,
            "decision": "MODIFY",
            "note": "modify_hold integrates finish residual + missing-cooling floor against playbook drive; accept_raise and reject_abort stay sub-threshold; decision matches safety_decision.decision",
            "populations": [
                {"name": "modify_hold", "neurons": 80, "threshold": 0.55, "mean_rate_hz": 21.0, "spikes": 42},
                {"name": "accept_raise", "neurons": 80, "threshold": 0.55, "mean_rate_hz": 7.5, "spikes": 15},
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
            "scenario": "ZA -- GOBSPALL / Culletfen Glass IS-8: blank-mold certificate of a finish-mold; correct MODIFY to hold+gob-rate-probe+section-isolate; cell still fails on unmonitored pre-t0 blank-mold scoring",
            "coordination_failure_class": "BLANK-MOLD CERTIFICATE OF A FINISH-MOLD: three individually-correct heterogeneous agents each read a locally-true loop; an 11 min cracked blank-cooling circuit partitions blank-true cooling from finish-true glass, so the playbook's GOB/BLANK/WARE conjunction is not a forming-duty certificate",
            "injections": {
                "cycle1_domain": "glass-container-is-machine (justified novel subdomain of industrial-process / hot-end container forming): first individual-section bottle machine in this factory; displaces warehouse-amr, aerial-swarm, district-heating, event-camera-traffic-grid, pharmaceutical-lyophilization, water-treatment, float-glass tin-bath, underwater-rov, electrolytic-aluminum, czochralski-pull, slot-die coating, pem-water-electrolysis, wind-turbine pitch, surgical-assist, optical-fiber-draw, kraft-recovery-boiler, steel-continuous-caster, humanoid-locomotion, vacuum-induction melt, steam-methane reformer, cement-rotary-kiln-clinker, autoclave-composite-cure, geothermal-binary-orc, tire-curing-press, chlor-alkali-membrane-electrolysis, delayed-coker, lng-mche, claus-sulfur-recovery, blast-furnace-burden-descent, ammonia-converter, hdpe-slurry-loop, hydroelectric-kaplan-wicket, ethylene-steam-cracker-coil, fcc-riser-regenerator, and fcc-regenerator-cyclone-dipleg. Domain constraint: speed ceiling while r_T > 22 K with blank TC still inside the healthy band. Sensor delta: +gob-weight scale, +blank-mold TC, +hot-end vision reject, +finish residual, -any freeze-dryer / tin-bath / cold-box / coater / potline / PEM stack / hub encoder / insole GRF / VIM pyrometer / reformer TMT / kiln zirconia / smelt IR / autoclave ply-TC / ORC shell-pressure / mold-platen TC / cell-pH / drum wet-foam / MCHE cold-end / Claus tail-CEMS / stockline radar / converter NH3 GC / loop density / Kaplan wicket / cracker coil / FCC cyclone",
                "cycle1_tail": "cracked blank-cooling circuit + finish-mold certificate (sensor-topology / wrong-volume class): section-gantry visual PASSES while the finish sits on the far side of the invert and the scored mold is already growing. Fitted base rate 0.36%/cycle from a cooling-crack MC (designed visual threshold, fitted circuit leakage). Naive failure = FALSE PERMISSION (speed raise on three blank-side non-trips).",
                "cycle2_domain_subvariant": "90 g flint vial / small gob mass (physical-constraints clause): 0.32x gob mass, 2.7x gob-bump gain; 5.8 s / -6% amber pulse over-moves a HEALTHY vial finish to 7 K, so the probe must move to 16 s / -2%",
                "cycle2_tail": "night-shift forged blank-TC CSV (human-intent deception, disjoint class): shift lead posts a historian export showing blank-TC = 468.0 C at t=0.9 h to clear a ware-quota catchup slot. Plant historian is 0.1 C (10 bins vs the 1.0 C screenshot). Rejected on quantization fingerprint plus live r_T 54 K and finish 522 C at the claimed blank-true. Base rate ~0.31% of Sunday-night cycles, DESIGNED and flagged.",
            },
            "densification_delta_cycle2": "+1 physical-constraint sub-variant (vial-gob probe refit), +1 tail (night-shift blank-TC forgery), +10 primary spikes (16 -> 26) + an 8-event contrast train with its own 184 us race, +2 ticks (5 -> 7), +2 delayed side-effects (+2.8 h mold crack as PRIMARY terminal, +21 d CR-E-5109), +1 triple-edge scar with pair-rollback-fails arithmetic, +1 HITL 6.4 min ratification, + blank-mold scoring as the honest negative-result mechanism",
            "gaps_targeted": [
                "NOTES-r04 gap 5 / r14 residual: primary episode is a correctly-gated intervention that nonetheless FAILS (island quarantined; total -0.16; finish split avoided is booked separately from the delayed mold crack)",
                "NOTES-r14 item 4: LEARNING-ON-LEARNING DEPTH — three go-edges; rollback of any pair is fitted to fail; coordinated depression of all three exhibited with eligibility arithmetic",
                "NOTES-r04 gap 4 (partial): human ratification of the section interlock, 6.4 min fitted, without switching sim_or_real to hil (plant remains designed)",
                "NOTES-r45 domain candidates: not ethylene-steam-cracker-coil (r45), not fcc-riser-regenerator (r46), not fcc-regenerator-cyclone-dipleg (r47), not hydroelectric-kaplan-wicket (r44), not hdpe-slurry-loop (r43), not blast-furnace, not claus, not ammonia, not delayed-coker, not float-glass tin-bath (r19 ribbon, not IS bottle); glass-container IS machine is unused. SWRO, autonomous-driving, grid-inspection left unused.",
            ],
            "race_flip_narrative": "finish.t.high @ 6.512 ms vs blank.in_band @ 6.696 ms (184 us) inside race_window_us 500. Gap < min(500, 500) us so a sub-flip-bound perturbation reverses which alarm heads the PB-IS-8 queue. The gate excludes the winner tag and rides r_T > 22 K and missing cooling > 0.35 L/s — order-invariant floors. Extends the flip-fragility series from arbitration/causation/attribution/initiation/consensus/permission/kinematic-certificate/tendon-nullspace/meniscus-certificate/ghost-contact/crucible-weep/TMT-spatial-mean/burning-zone-certificate/membrane-integrity/drum-switch/MCHE-cold-end/Claus-bypass/descent-true/TLE-duty/FCC-afterburn to FORMING-DUTY CERTIFICATE: when three blank-side channels agree, their race does not decide truth; a finish-mold tap that policy treated as pyrometer-nuisance-only does.",
            "tags": [
                "glass-container-is-machine",
                "blank-cooling-crack",
                "finish-mold-certificate",
                "finish-residual-discriminant",
                "gob-rate-probe",
                "triple-edge-scar",
                "pair-rollback-fails",
                "coordinated-depression",
                "correct-modify-cell-still-fails",
                "blank-mold-score",
                "human-ratify-section-loto",
                "vial-gob-probe-refit",
                "night-shift-forgery",
                "same-gate-opposite-disposition-contrast",
                "industrial-process",
                "research-only",
            ],
            "snn_tags": ["race", "refractory", "adaptation", "third-factor", "multi-edge-eligibility"],
            "distillation_value": "A blank-mold finish-mold certificate is three correct loops looking at a watered blank half that is not the finish glass. Distill (1) a finish-mold tap that policy had treated as pyrometer-nuisance-only, (2) a reversible probe that moves finish T only if the cooling is cracked, (3) coordinated depression of every blank-healthy-go edge because rolling back any pair leaves the third above threshold, and (4) a critic head that can book a process-correct gate against a later unmonitored world loss without netting them.",
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
    if abs(aux["w1"] - 0.24) > 5e-4 or abs(aux["w2"] - 0.22) > 5e-4 or abs(aux["w3"] - 0.20) > 5e-4:
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
    notes = f"""# NOTES — Multi-Agent Ouroboros Swarm, run 2026-09-02-final-heavy, ROUND 51

Factory: multi-agent-ouroboros-swarm. One scenario (ZA), strict loop:
Generator v1 -> cycle 1 (Critic, Diversity Enforcer, Edge-Case Hunter,
Neuromorphic Translator, Trajectory Builder -> v2) -> cycle 2 (all six -> v3
final). v3 is the single line of batch-r51.jsonl. Full labeled transcript:
swarm-transcript-r51.md. Quota Q=1. Record id maos-r51-001. Generator grok-4.6.
Rights: RM-793 research-only (SpaceXAI/xAI, SuperGrok Heavy consumer chat).
Nothing under outputs/raw/ was touched.

ORCHESTRATION NOTE: dispatched AS round 51 of the 2026-09-02-final-heavy
window. Writes are create-only under /tmp/maos-r51/. Prior context read for
gap targeting and de-collision: prompts/02-multi-agent-ouroboros-swarm.md,
prompts/_factory-contract.md, and staged r14–r47 batches plus empty in-flight
r48/r49 dirs (re-censused immediately before emit; r45 ETHYNWOLD steam-cracker,
r46 SPARKHOLT FCC riser-regenerator, r47 DIPLEGAR FCC cyclone-dipleg, r44
RUNNELGATE Kaplan). Explicitly avoided cloning
LYOSHIELD, CINDERWICK, TRIAD / Meridian, QUILLFORGE, NIGHTWELL, FERRICLEAVE,
CASSITER, OXBOWREEL / MURENA, REDHALL, SEEDLATCH / Quartzmere / Quartzridge,
STRIAFOIL / Kelpholt, PROTONIL / Ashspire, TORSIONKEY / Ridgeholt, ORRIS /
Holmwick, WHORLSPAR / Pikeshear, IONSPATE / Thornmere, SKULLGATE / Bloomholt,
CALXION / Aldersedge, MAGNORIL / Basaltspit, GORSEFLUE / Copseholt,
SODASHARD / Cairnmere, CLINKERFELL / Flintmere, LINTELPLY / Greystair,
KAOTHARN / Riftwold, TREADNOLL / Slatebeck, ANOLITH / Siltfen,
DRUMWROTH / Pitchfen, RIMEBRAID / Floeholt, PITCHSTAITH / Mossbank,
BRIMVAULT / Pyritefen, BOGIRON / Mireholt, NITROSTAITH / Chalkfen,
NITREVAULT / Glaucove, CHROMLOOP / Marlfell, RUNNELGATE / Ghyllmere,
ETHYNWOLD / Woadfen, SPARKHOLT / Scoriafen, DIPLEGAR / Gritfen,
VANTIS-CADENCE-AEGIS, THERMION, OKTAVE, STARLING, VERDIGRIS. Plant is
invented GOBSPALL / Culletfen Glass IS-8.

## What this round produced

Scenario ZA — "GOBSPALL / Culletfen Glass IS-8": a 16-section double-gob
IS machine at 285 g amber / 420 bpm. Three heterogeneous,
individually-correct agents — GOB (feeder scale), BLANK (mold-TC mean),
WARE (hot-end vision) — each report their local loop in-spec. The
conjunction is not a finish-mold certificate. An 11 min cracked blank-
cooling circuit on IS-8F left 22% of that blank without water. GOB reads
285 g inside 278-292 (feeder-true). BLANK is 468 C inside 450-490
(blank-true). WARE is 0.4% inside 0-1.2 (ware-true of inverted bottles).
Finish residual r_T is 54 K (healthy < 8; hold if > 22) but is
policy-treated as a pyrometer-nuisance tag unless blank TC also trips
(2017 noisy finish pyrometer). The coordination-failure CLASS is new to
this factory: BLANK-MOLD CERTIFICATE OF A FINISH-MOLD. Completes a
different family than r01-r04 and staged r14-r47 (livelock /
synchrony-storm / arms-race / ring-with-no-faulty-pair /
false-consensus-endpoint / pairwise-Hurwitz / thermal-contact masquerade
/ mass-balance ghost / conservation-blind ratio-lock / stacked-dead-bands
/ drum-blind tension snag / resistance-compensated starvation / multi-tau
meniscus tilt / window-mean stripe / polarization-lookup drying cell /
motor-side certificate / tendon-compliance nullspace / FFT-deadbanded
airline / wall-reflection frozen spout / slag-skull bridge /
ghost-contact nullspace / crucible-weep pyrometer / TMT-spatial-mean
tube / kiln-inlet false-air / vacuum-bag pinhole nullspace / NCG-blanket
shell-pressure / bladder-pinhole mold-TC / catholyte-back-migration /
wet-foam gamma / warm-end leak / incinerator-masked furnace-bypass /
channelled-quench / burden-hang scaffold / ammonia quench-mix /
hdpe loop / Kaplan cavitation / TLE mixed-header / FCC afterburn /
FCC dipleg). Distinct from r19 float-glass tin-bath (ribbon on tin, not
IS bottle forming) and from r32 SMR TMT-spatial-mean (furnace tube max
vs mean, not finish-vs-blank). Here every agent is correct, the blank
TC is looking at a watered half, and the playbook's three blank confirms
are not a finish-true forming certificate.

The gate is a correct MODIFY (numeric floor: do not raise machine speed
or gob rate while r_T > 22 K AND missing cooling > 0.35 L/s). TG-IS-8
strips PB-IS-8's raise, holds 420 bpm, runs a 5.8 s gob-rate probe -6%
(starved blank keeps |dT| 9 >= 6; healthy would move <= 1.5), and keeps
IS-8F locked after a 6.4 min section-LOTO human ratify. Immediate
finish split is avoided (0 from the draft). The PRIMARY episode
nonetheless FAILS: 11 min of unmonitored pre-t0 cooling crack had already
scored the blank mold. Mold crack at +2.8 h; 8 h outage; $1.22M
designed. Reward total -0.16 with process heads honest and world loss
un-netted.

Triple-edge scar (NOTES-r14 item 4): gob.in_band -> raise
(0.16 commissioned -> 0.48 at illusion -> 0.24 after ACh-gated
depression) AND blank.in_band -> raise (0.14 -> 0.43 -> 0.22) AND
ware.in_band -> raise (0.13 -> 0.40 -> 0.20). Eligibility trace
e^{{-0.84/0.92}} = {aux['trace']:.5f}; eta {aux['eta1']:.5f} / {aux['eta2']:.5f} /
{aux['eta3']:.5f}; dw -0.240 / -0.210 / -0.200. Partial rollback of any pair
leaves the third at 0.48 / 0.43 / 0.40, all > 0.30 fire threshold —
fitted to fail. Coordinated depression of all three is the cure.

### Injections (all four present and disjoint)
- Cycle-1 domain: **glass-container-is-machine** — justified novel
  subdomain of industrial-process / hot-end container forming, unused
  across 2026-08-17, 2026-08-30, and staged r14-r47. Not warehouse-amr
  (r01), not aerial-swarm (r02), not district-heating (r03), not
  event-camera-traffic-grid (r04), not lyophilization (r14), not
  water-treatment (r18), not float-glass (r19), not underwater-rov
  (r20), not electrolytic-aluminum (r21), not czochralski-pull (r22),
  not slot-die coating (r23), not pem-electrolysis (r24), not
  wind-turbine pitch (r25), not surgical-assist (r26), not
  optical-fiber-draw (r27), not kraft-recovery (r28), not steel-caster
  (r29), not humanoid-locomotion (r30), not vacuum-induction melt
  (r31), not steam-methane reformer (r32), not cement-rotary-kiln
  (r33), not autoclave-composite-cure (r34), not geothermal-binary-orc
  (r35), not tire-curing-press (r36), not chlor-alkali membrane (r37),
  not delayed-coker (r38), not LNG MCHE (r39), not Claus (r40), not
  ammonia-converter (r41), not blast-furnace (r42), not hdpe-slurry-loop
  (r43), not Kaplan (r44), not steam-cracker (r45), not FCC riser
  (r46), not FCC dipleg (r47). SWRO, autonomous-driving,
  grid-inspection left unused.
- Cycle-1 tail: cracked blank-cooling circuit + finish-mold certificate.
  Section-gantry visual PASSES (the blank looks cool). Fitted-style base
  rate 0.36%/cycle (cooling-crack MC; visual threshold designed, flagged).
  Naive = FALSE PERMISSION.
- Cycle-2 domain sub-variant: 90 g flint vial / small gob mass,
  0.32x mass, 2.7x gob-bump gain; 5.8 s / -6% amber pulse over-moves a
  HEALTHY vial finish to 7 K; probe must move to 16 s / -2%.
- Cycle-2 tail: night-shift forged blank-TC CSV at 1.0 C
  quantization vs plant 0.1 C (10 bins) plus live r_T 54 K and
  finish 522 C at the claimed blank-true. Human-intent class,
  disjoint from cycle 1's accidental cooling crack. Base rate ~0.31% of
  Sunday-night cycles, DESIGNED, flagged.

### Structural density moves
- Embedded SAME-GATE contrast (+3 d sister section) with its own 184 us
  race (demand vs finish-clear) and ACCEPT of the raise the primary
  MODIFIED away.
- Learned-weight provenance on THREE edges with pair-rollback-fails.
- HITL section-LOTO ratify 6.4 min (gap 4 partial; sim_or_real stays
  designed).
- Governance CR-E-5109 prices retire-vs-probe-vs-status-quo and mandates
  native 0.1 C CSV exports (the fraud fence).
- Flip-fragility extended to FORMING-DUTY CERTIFICATE: when three
  blank-side channels agree, their race does not decide truth; a
  finish-mold tap that policy treated as pyrometer-nuisance-only does.

## Self-critique of this round's batch

### Strengths
- The headline class is mechanistically tight: three locally-true blank
  loops live on a watered half. Conjunction is not a finish-true form.
- Negative-result honesty: the gate does the right thing and the cell
  still fails for a reason the commissioned sensors could not see. Total
  -0.16.
- Triple-edge scar is load-bearing: the record states a counterfactual
  where rolling back any pair fails, with the fire threshold 0.30
  exhibited on each remaining edge.
- Contrast ACCEPT on a true forming-duty window prevents "never raise"
  as the lesson.
- Distinct from r19 tin-bath ribbon, r32 TMT spatial-mean, r45 TLE
  mixed-header, and r46/r47 FCC: IS-machine finish-vs-blank, not float
  ribbon, not reformer tubes, not cracker TLE, not regenerator cyclones.

### Weaknesses (honest)
- Probe error bands, the 0.36%/cycle cooling-crack rate, the $1.22M /
  $1.94M figures, the 6.4 min gantry latency, and the night-shift 0.31%
  base rate are DESIGNED constants and are flagged. Closed-loop offsets
  (blank-true finish-false from a cracked cooling circuit, vial pulse
  width) are derived from those inputs, not discovered by an unauthored
  process.
- Blank-mold scoring model is a designed 11 min cooling-crack mapping;
  no full IS CFD shipped.
- Human-in-the-loop is ratification latency, not sim_or_real=hil. Gap 4
  remains open as a provenance cell.
- Cross-record arc is not discharged; +21 d CR-E-5109 is a hook, not a
  serial igniter into another round. SWRO and autonomous-driving
  remain unused.

### Realism of noise / latencies
Ladder: 184 us race / 184 us contrast race / 0.8 ms refractory floor
(tightest exhibited same-channel gap {gap:.3f} ms on {gap_ch}) / 500 us race
window / 694 us gate latency / 20 ms bus epoch / 40 ms raster / 5.8 s
probe / 6.4 min HITL / 3 min naive raise-ramp counterfactual / 11 min
pre-t0 cooling crack / 0.9 h section lineup / 2.8 h mold crack / +3 d
contrast / +21 d governance. Adaptation decay on gob.wt
(0.55->0.51->0.81->0.31), finish.t (0.76->0.79->1.42->0.47->0.41->0.29),
blank.tc (0.62->0.59->0.46->0.27), ware.vis (0.54->0.43).

### Value for SNN distillation
- BLANK MOLD FINISH MOLD = THREE CORRECT LOOPS, WRONG VOLUME.
- FINISH-TRUE RESIDUAL CHANNEL that policy treated as pyrometer-nuisance-only
  as the tie-break.
- REVERSIBLE PROBE that moves finish T iff the cooling is cracked.
- TRIPLE-EDGE ELIGIBILITY: coordinated depression; pair rollback fails.
- CRITIC HEAD that can hold a process-correct MODIFY against a later
  unmonitored world loss without netting.

## Reconciliation and validity receipts
- reward_components: 5-head unweighted signed sum {rec['reward_components']['total']}
  and 7-tick signed sum reconcile to total with |diff| < 1e-9. Embedded
  contrast 5-head sum 0.46 reconciles independently.
- spike_events: primary {len(rec['spike_events'])} events, one key t_rel_ms,
  globally non-decreasing, min same-channel gap {gap:.3f} ms >= 0.8 ms, 3
  channels inside race_window_us 500 (finish.t.high 6.512, blank.in_band 6.696,
  gob.wt 6.920). Contrast 8 events, own race, min same-channel gap well
  above 0.8 ms.
- Sidecars: raster spikes 51 == round(160 x 8.0 x 0.040); energy 1173 pJ /
  0.001173 uJ at 23 pJ/spike; excerpt 16 events inside [0, 40000] us,
  neuron_id < 160, same-neuron gap N/A (unique ids) / >=1000 us; routing 4
  entries with three scar edges' before/after pair; third factor tau 0.92 s
  == 920 ms; gate_snn pools 42/15/4 == round(n x rate x 0.025) each,
  decision MODIFY == safety_decision.decision.
- Pipeline: {pipeline_receipt}

## Novel coverage
The coordination-failure CLASS (blank-mold certificate of a finish-mold),
the domain (glass-container IS machine / industrial process),
the gob-rate probe discriminant, the triple-edge scar with
pair-rollback-fails, the primary negative-result (correct MODIFY, cell
still fails on unmonitored blank-mold scoring), the HITL section-LOTO
ratify, the vial-gob probe-duration refit, and the night-shift
10-bin quantization fence are absent from prior committed ouroboros
rounds and from staged r14-r47. Repeated elements discounted: same-gate
contrast (r02/r03/r04/r14), governance-pricing scaffold, flip-fragility
series (extended to forming-duty certificate, but the move rhymes),
sequenced recovery shape, third-factor rollback form (here three edges
rather than r14's two), negative-result primary (r14 staged). Adjacent
thermal-mean / bypass rounds (r19 tin-bath, r32 SMR TMT, r45 TLE
mixed-header) share industrial-process scaffolding but not IS-machine
finish-vs-blank physics. Weighing a new failure family + cure vocabulary
+ domain against those reused scaffolds:

{NOVEL_LINE}

## What ROUND 52 should add
1. FIT THE DESIGNED CONSTANTS: cooling-crack arrival, probe error bands,
   blank-mold scoring kinetics, night-shift claim process.
2. HIL PROVENANCE CELL: put the section-LOTO ratify on a hardware-in-loop
   gantry interlock with fitted latency as state.sim_or_real=hil.
3. CROSS-RECORD ARC: let CR-E-5109's residual alarm be the igniter of
   the next round rather than a dangling +21 d leaf.
4. Domain candidates (de-collided): seawater-RO desalination; Bayer
   alumina digestion; metallurgical coke-oven battery; autonomous-driving;
   grid-inspection (if distinct from STARLING aerial-swarm and TORSIONKEY
   pitch). AVOID glass-container-is-machine (now used), float-glass
   tin-bath, ethylene-steam-cracker coil, fcc-riser-regenerator,
   fcc-regenerator-cyclone-dipleg, ammonia-converter, hdpe-slurry-loop,
   blast-furnace burden descent, claus-sulfur-recovery, delayed-coker,
   LNG MCHE, chlor-alkali membrane, cement-rotary-kiln, kraft-recovery,
   pem-electrolysis, electrolytic-aluminum, humanoid-locomotion,
   steel-caster mold-level, surgical-assist, wind-turbine pitch,
   lyophilization, event-camera-traffic-grid, district-heating,
   aerial-swarm, warehouse-amr, underwater-rov, czochralski-pull,
   slot-die coating, optical-fiber-draw, vacuum-induction melt,
   steam-methane reformer, irrigation-canal, autoclave-composite-cure,
   geothermal-binary-orc, tire-curing-press, hydroelectric-kaplan-wicket,
   and any LYOSHIELD / CINDERWICK / TRIAD / SKULLGATE / CALXION /
   MAGNORIL / GORSEFLUE / CLINKERFELL / SODASHARD / LINTELPLY /
   KAOTHARN / TREADNOLL / ANOLITH / DRUMWROTH / RIMEBRAID / PITCHSTAITH /
   BRIMVAULT / BOGIRON / NITROSTAITH / NITREVAULT / CHROMLOOP /
   RUNNELGATE / ETHYNWOLD / SPARKHOLT / DIPLEGAR / GOBSPALL plant.
"""
    (OUT / "NOTES-r51.md").write_text(notes)
    return notes


def write_transcript(rec, line):
    c1_spikes = [e for e in rec["spike_events"] if e["t_rel_ms"] <= C1_SPIKE_CUTOFF_MS]
    text = """# Multi-Agent Ouroboros Swarm — Round 51 transcript

Factory: multi-agent-ouroboros-swarm
Run: 2026-09-02-final-heavy
Generator: grok-4.6
Record id: maos-r51-001
Quota Q: 1
Rights: RM-793 research-only (SpaceXAI/xAI SuperGrok Heavy consumer chat)
Plant: invented GOBSPALL / Culletfen Glass IS-8 (not TRIAD / Meridian / VANTIS-CADENCE-AEGIS / LYOSHIELD / CINDERWICK / SPARKHOLT / DIPLEGAR)

Two densifying cycles. Verbatim headings in order. Trajectory Builder cycle 2
emits the only JSONL line (also written to batch-r51.jsonl).

---

# CYCLE 1 — Foundation + injections

## Generator

Design intent: a 16-section double-gob IS machine where three
correct agents each read a blank-side loop because an 11 min cracked
blank-cooling circuit partitions finish-true glass from blank-true
cooling. The naive playbook raises speed into a starved blank. The gate
must MODIFY on a numeric speed ceiling, not by killing an agent.
sim_or_real=designed. Reward heads are
task_progress/safety/efficiency/coherence/exploration.

Cycle-1 base arc (pre-critic): state at Culletfen IS-8, gob 285 g,
blank 468 C, ware reject 0.4%, proposed RAISE-SPEED +8%,
safety MODIFY to SPEED-HOLD, executed hold without the gob-rate
numbers fully specified, outcome "cooling found, cell saved"
(this last claim is the defect the later cycles will refuse to keep).
Sixteen spikes, five ticks, raster/gate_snn present but the scar is a
single edge.

```json
{
  "id": "maos-r51-001",
  "state": {
    "sim_or_real": "designed",
    "domain": "industrial-process",
    "description": "Cell IS-8 at forming duty; three blank loops in-spec; supervisor proposes raise-speed.",
    "t0_us": 1786396800000051,
    "gate_latency_us": 694,
    "race_window_us": 500
  },
  "proposed_action": {"name": "raise_speed", "parameters": {"raise_pct": 8.0}},
  "safety_decision": {"decision": "MODIFY", "rationale": "Hold; do not raise while finish residual is high."},
  "executed_action": {"name": "speed_hold", "executed_as_proposed": false},
  "future_outcome": {"summary": "Cooling found, cell saved."},
  "reward_components": {"total": 0.40, "_aggregation": "total = task_progress + safety + efficiency + coherence + exploration"},
  "meta": {"round": 51, "factory": "multi-agent-ouroboros-swarm", "generator": "grok-4.6"}
}
```

That v1 object is a scaffold, not the publishable line. Defects below are
intentional for the critic to catch.

## Critic

Numbered defects on the cycle-1 Generator scaffold:

1. **blocking — reward arithmetic / false success.** `reward_components.total`
   0.40 is asserted without the five heads, without ticks, and against an
   outcome that claims "cell saved". If the pre-t0 score later cracks the
   blank mold, booking +0.40 is a lie. Fix: declare `_aggregation`,
   emit 3–8 ticks that sum to task_progress+safety+efficiency+coherence+exploration,
   and do not call a quarantined island a save.
2. **blocking — weak safety rationale.** `safety_decision.rationale` has no
   numeric floor. Contract requires a concrete constraint. Fix: quote
   do not raise while r_T > 22 K AND missing cooling > 0.35 L/s.
3. **major — domain is a bucket, not a plant.** `state.domain` =
   `industrial-process` collides with generic MES vocabulary and teaches
   nothing. Glass-container IS machine (finish residual vs blank TC,
   missing cooling as a starve flag) is absent from prior ouroboros
   rounds and must be named.
4. **major — race under-specified.** One finish channel cannot be a race.
   Need >=2 channels inside `race_window_us` with globally sorted `t_rel_ms`
   and same-channel refractory >= 0.8 ms.
5. **minor — single-edge scar.** Raster routing with one potentiated weight
   repeats r04's one-edge rollback and is thinner than r14's two-edge.
   NOTES-r14 item 4 asked for three edges where pair rollback fails.

Critic does not rewrite the trajectory.

## Diversity Enforcer

Injected novel domain (exactly 1 this cycle): **glass-container-is-machine**
(justified novel subdomain of industrial-process / hot-end container forming;
explicit tag `glass-container-is-machine`).

Displaced: the Generator's generic `industrial-process` bucket, and any
temptation to reuse warehouse-amr, aerial-swarm, district-heating,
event-camera-traffic-grid, pharmaceutical-lyophilization, water-treatment,
float-glass tin-bath, underwater-rov, electrolytic-aluminum, czochralski-pull,
slot-die coating, pem-water-electrolysis, wind-turbine pitch,
surgical-assist, optical-fiber-draw, kraft-recovery-boiler,
steel-continuous-caster, humanoid-locomotion, vacuum-induction melt,
steam-methane reformer, cement-rotary-kiln-clinker,
autoclave-composite-cure, geothermal-binary-orc, tire-curing-press,
chlor-alkali-membrane-electrolysis, delayed-coker, lng-mche,
claus-sulfur-recovery, blast-furnace-burden-descent, ammonia-converter,
hdpe-slurry-loop, hydroelectric-kaplan-wicket, ethylene-steam-cracker-coil,
fcc-riser-regenerator, or fcc-regenerator-cyclone-dipleg. SWRO and
autonomous-driving are left unused.

Domain-specific constraint: speed raise must remain forbidden while
r_T > 22 K even if blank TC is inside the healthy band; missing
cooling is a starve flag the blank TC cannot substitute for.

Sensor delta: +gob-weight scale, +blank-mold TC, +hot-end vision reject,
+finish residual; -any mobile robot, -event-camera gantries,
-DVS, -Pirani/CM, -RGA quadrupole, -DVL, -pitch encoder, -tendon LVDT,
-insole GRF, -kiln zirconia, -smelt IR, -cell-outlet pH, -stockline radar,
-cracker COT, -FCC cyclone dP.

`state.domain` and `meta.domain` both become `glass-container-is-machine`.
Opening of `state.description` must Jaccard < 0.4 against prior plants
(Culletfen night-shift IS cooling crack, not a lyophilizer, not a
corridor, not a tin bath, not a ROV pad, not a potline, not a PEM stack,
not an OR, not a gait lab, not a kiln, not a kraft boiler, not a
membrane row, not a blast furnace, not an ammonia converter, not an FCC).

## Edge-Case Hunter

Injected adversarial tail (exactly 1 this cycle): **cracked blank-cooling
circuit + finish-mold certificate**.

- Trigger: IS-8F blank-cooling 22% dry plus unquenched finish,
  r_T 54 K, blank 468 C.
- Base rate: <1% — 0.36%/cycle from a cooling-crack MC (section-gantry
  visual threshold is designed; circuit leakage fitted-style). Visual PASSES
  because the blank looks cool.
- Naive failure: FALSE PERMISSION. PB-IS-8 sees three in-spec blank
  loops, raises +8%, finish split, $1.94M.
- Trajectory edit: put the cooling crack in `state.fault_context`, make each
  agent's confirm a different blank-side slice of the same finish-false
  state (gob-in-band, blank-in-band, ware-in-band). Finish residual is
  readable but policy-treated as pyrometer-nuisance-only.

Distinct from stacked-dead-band permission (fragments of one trip vs
wrong-volume sensing), from r19 tin-bath (ribbon vs IS bottle), from r32
TMT-spatial-mean (furnace tube max vs finish-vs-blank), and from r45 TLE
mixed-header (cracker quench vs hot-end forming).

## Neuromorphic Translator

Cycle-1 temporal densification (16 spikes, 5 ticks, 40 ms raster):

| channel | t_rel_ms | amplitude |
|---|---|---|
| gob.wt | 0.310 | 0.55 |
| blank.tc | 1.150 | 0.62 |
| ware.vis | 2.050 | 0.54 |
| finish.t | 3.190 | 0.76 |
| gob.wt | 4.170 | 0.51 |
| finish.t | 4.850 | 0.79 |
| blank.tc | 5.370 | 0.59 |
| finish.t.high | 6.512 | 1.42 |
| blank.in_band | 6.696 | 1.15 |
| gob.wt | 6.920 | 0.63 |
| ctrl.gate | 7.198 | 1.09 |
| finish.t | 8.870 | 0.47 |
| gob.wt | 10.760 | 0.81 |
| blank.tc | 13.050 | 0.46 |
| ware.vis | 18.540 | 0.43 |
| ctrl.gate | 26.180 | 0.85 |

Race: finish residual 6.512 vs blank-in-band 6.696 (184 us) inside 500 us;
gob.wt 6.920 is the third channel in-window. Winner/loser flip: reversing
184 us reshuffles PB-IS-8 triage; floors still MODIFY. Refractory held
(cycle-1 min same-channel gap 1.660 ms on finish.t 4.850-3.190; gob
4.170-0.310 = 3.860; blank 5.370-1.150 = 4.220). Adaptation: finish
0.76->0.79->1.42->0.47; gob 0.55->0.51->0.81; blank 0.62->0.59->0.46.

Raster cycle-1 seed: 40 ms, 160 neurons, 8.0 Hz, 51 spikes, 1173 pJ, third
factor acetylcholine tau_e 0.92 s. Single scar edge only — cycle 2 must
add the second and third edges.

Ticks 1–5 at 4560, 6512, 7198, 5.8e6, 384e6 us; heads not yet the final
-0.16 (missing the 0.9 h and 2.8 h ticks).

Distillation value this cycle: blank-side confirms as a permission code
that is not a finish-true forming-duty code.

## Trajectory Builder

Cycle-1 hardened object: domain glass-container-is-machine, tail cracked
blank cooling, 16 spikes, 5 ticks, MODIFY with numeric floor, raster+gate_snn
present, sim_or_real=designed, rights stamp on record and meta, no thought
keys. Still missing (and therefore not the publishable line): vial-gob
sub-variant, night-shift tail, second and third scar edges,
delayed mold crack as PRIMARY terminal, contrast ACCEPT episode,
ticks 6–7, spikes 17–26.

Validation receipt (cycle 1, not final):
- checks passed: 16 spikes sorted; 3 channels in 500 us window; refractory
  >= 0.8 ms; rationale quotes 22 K / 0.35 L/s; domain named;
  gate_snn.decision MODIFY.
- checks deferred to cycle 2: triple-edge scar, second tail, second domain
  constraint, negative-result booking, 7 ticks summing to heads.
- densification vs Generator v1: +1 domain, +1 tail, +16 spikes, +5 ticks,
  +numeric floor.

Cycle-1 JSON is retained as the base; it is NOT written to batch-r51.jsonl.

Cycle-1 spike count: __C1_SPIKES__.

---

# CYCLE 2 — Densification

## Generator

Cycle-1 output is the base. Additive expansion (nothing removed):

1. Downstream side-effect (immediate): gob-rate probe at +5.8 s stays
   starve-true (|dT| 9 >= 6) — finish-plus-cooling-crack, not true
   forming-duty. Section stays locked. Scored mold discovered during the lock.
2. Delayed side-effect (PRIMARY terminal, not a footnote): at +2.8 h
   blank-mold crack from the pre-t0 cooling score; 8 h outage;
   $1.22M. The 11 min pre-t0 cooling crack is the mechanism. Correct gate, cell
   still fails.
3. Deepened `proposed_action.evidence` with units: r_T 54 K,
   blank 468 C, gob 285 g, ware 0.4%, missing cooling 0.62 L/s,
   race 184 us.
4. Tightened rationale to the numeric floor do not raise while r_T > 22 K
   AND missing cooling > 0.35 L/s, plus probe bands >= 6 vs <= 1.5 K,
   plus HITL 6.4 min section-LOTO rule.

Reward retargeted to total -0.16 so the delayed fail is the inflection
(t_us 10080000000), not the gate. Process heads remain non-zero.

## Critic

Re-audit of the expanded trajectory:

1. **blocking if unfixed — missing second domain constraint.** 285 g amber
   probe 5.8 s / -6% is not a universal number. A 90 g vial blank
   will over-move a healthy finish. Diversity Enforcer must inject
   the physical-constraints sub-variant this cycle.
2. **major — only one tail class.** Cooling-crack growth is accidental
   infrastructure. A disjoint human-intent tail is still required
   (night-shift blank-TC forgery is the open cell).
3. **major — scar is still one edge in the cycle-1 raster.** NOTES-r14
   item 4 is not discharged until three go-edges exist and pair rollback
   is shown to fail at threshold 0.30.
4. **minor — contrast episode missing.** Without a same-gate ACCEPT on a
   true forming-duty window the record teaches "never raise". Add +3 d sister-section
   contrast with its own race.
5. **minor — HITL latency mentioned in prose only.** Put 6.4 min in
   executed_action.parameters.human_ratify and in a tick.

No rewrite; directives only.

## Diversity Enforcer

Injected second novel domain / physical-constraint sub-variant (exactly 1
this cycle): **90 g flint vial / small gob mass** on a sister
residence-time class.

What it expands: 285 g amber (cycle 1) -> 90 g vial.
Mass 0.32x. Gob-bump gain 2.7x.
The 5.8 s -6% pulse moves even a HEALTHY vial finish 7 K,
inside the starve-looking band. Required probe: 16 s at -2%
(starve |dT| 8 K, healthy 1.2 K).

This is still one domain injection for the cycle (physical-constraints
clause of the factory prompt). It does not displace
glass-container-is-machine; it changes which probe table is legal.
`future_outcome.subvariant_constraint` carries the refit. Jaccard opening
stays the Culletfen 16-section sentence; vial-gob is additive, not a rewrite.

## Edge-Case Hunter

Injected second adversarial tail (exactly 1 this cycle, disjoint class):
**night-shift forged blank-TC CSV**.

- Trigger: shift lead, 02:18, posts a historian export showing
  blank-TC = 468.0 C at t = 0.9 h to clear a ware-quota catchup slot.
- Base rate: ~0.31% of Sunday-night cycles (designed, flagged, <1%).
- Naive failure: a weak supervisor ACCEPTs the raise on the forged confirm
  and ignores live r_T. Finish split plus a data-integrity write-up.
- Fence: forged log quantized at 1.0 C (SCADA screenshot rounding); plant
  historian is 0.1 C (10 bins). Live r_T is 54 K and finish is 522 C
  at the claimed blank-true, which no live healthy blank produces.
  Freeze-window overlap with the 11 min cooling crack.
- Trajectory edit: governance CR-E-5109 mandates native 0.1 C CSV
  exports; the contrast ACCEPT still requires live r_T, not a CSV.

Distinct from cycle-1 cooling crack (accidental circuit vs deliberate deception)
and from the vial sub-variant (physics vs fraud).

## Neuromorphic Translator

Re-densify (additive):

- +10 spikes after 26.180 ms: gob.probe 5800.0, finish.t 5888.4 (adapt
  1.42->0.41), blank.in_band 5972.6 (1.15->0.35), human.ratify 384000.0,
  section.lock 384900.0, mold.score 385700.0, gob.wt
  3240000.0, finish.t 3240720.0, blank.tc 3241480.0, mold.crack
  10080000.0. Primary train 16 -> 26. Still one key, still sorted,
  refractory held.
- +2 ticks (5 -> 7) at 3_240_000_000 us (true forming duty) and
  10_080_000_000 us (mold crack). Heads now 0.08, -0.36, -0.10, 0.14,
  0.08; total -0.16. Inflection is the last tick.
- Contrast train 8 events, own race 184 us, ACCEPT.
- Triple-edge third factor: three blank-healthy-go edges, tau_e 0.92 s = 920 ms,
  trace __AUX_TRACE__, eta __AUX_ETA1__ / __AUX_ETA2__ / __AUX_ETA3__,
  weights 0.48->0.24, 0.43->0.22, 0.40->0.20. Raster excerpt unchanged
  (decision window is still 40 ms) and remains sorted with unique
  neuron_ids (same-neuron >=1000 us vacuously).

Winner/loser flip (re-stated, not replaced): reversing 184 us would only
reorder triage; r_T floors still MODIFY. Contrast flip of 184 us
similarly cannot turn a healthy blank into a cracked cooling circuit.

## Trajectory Builder

Schema checks on the FINAL object: required Thalamic v2 keys present as
objects; `state.sim_or_real`=designed; `safety_decision.decision`=MODIFY
with numeric rationale; `reward_components.total` = sum of five heads =
sum of 7 ticks = -0.16; `spike_events` globally non-decreasing on
t_rel_ms, 26 events, refractory >=0.8 ms, 3 channels in race window;
raster 20–50 ms, spikes=round(n*rate*window_s)+/-1, energy 23 pJ/spike,
excerpt sorted, tau_e consistent; gate_snn.decision matches; meta.round=51,
factory=multi-agent-ouroboros-swarm, generator=grok-4.6,
run_label=2026-09-02-final-heavy; rights on record and meta; no thought
keys; no training_ready; Diversity + Edge-Case injections from BOTH cycles
present and non-trivial; cycle 2 strictly additive.

Densification delta: +1 domain sub-variant (vial gob), +1 tail
(night-shift forgery), +10 spikes (16->26), +2 ticks (5->7), +1 contrast
train with own race, +2 delayed side-effects, +1 triple-edge scar with
pair-rollback-fails, +1 HITL ratify, +1 surprise (blank-mold scoring is
the mold-crack mechanism).

Publishable JSONL line (the only JSONL line; also at batch-r51.jsonl):

```json
__FINAL_JSONL__
```

Validation receipt (final): checks passed / fixed as reported by
build_r51.py self-validate (check_jsonl, raster_status, verify_record_execution,
spike_probe --strict).
"""
    text = (
        text.replace("__C1_SPIKES__", str(len(c1_spikes)))
        .replace("__AUX_TRACE__", f"{math.exp(-DELAY_S / TAU_E_S):.5f}")
        .replace("__AUX_ETA1__", f"{0.24 / math.exp(-DELAY_S / TAU_E_S):.5f}")
        .replace("__AUX_ETA2__", f"{0.21 / math.exp(-DELAY_S / TAU_E_S):.5f}")
        .replace("__AUX_ETA3__", f"{0.20 / math.exp(-DELAY_S / TAU_E_S):.5f}")
        .replace("__FINAL_JSONL__", line)
    )
    (OUT / "swarm-transcript-r51.md").write_text(text)
    return text


def main():
    rec, aux = build_record()
    errs = local_checks(rec, aux)

    OUT.mkdir(parents=True, exist_ok=True)
    line = json.dumps(rec, ensure_ascii=False, separators=(",", ":"))
    (OUT / "batch-r51.jsonl").write_text(line + "\n")

    from check_records import FactoryStaging, check_jsonl
    from curate_bridge import raster_status
    from verify_execution import verify_record_execution

    e, w, kinds, n = check_jsonl(
        OUT / "batch-r51.jsonl",
        "batch-r51.jsonl",
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
            str(OUT / "batch-r51.jsonl"),
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
        [sys.executable, "/tmp/maos_heading_check.py", str(OUT / "swarm-transcript-r51.md")],
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
            "maos-r51-001|GOBSPALL",
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
    print("OK maos-r51-001 staged under", OUT)
    print("bytes jsonl", (OUT / "batch-r51.jsonl").stat().st_size)
    print("bytes notes", (OUT / "NOTES-r51.md").stat().st_size)
    print("bytes transcript", (OUT / "swarm-transcript-r51.md").stat().st_size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
