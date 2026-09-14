#!/usr/bin/env python3
"""Build and self-check MAOS round-52 JSONL (research-only; not published)."""
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

GEN_AT = "2026-09-03T09:28:00Z"
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
OUT = Path("/tmp/maos-r52")
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
    "BRIMVAULT",
    "Pyritefen",
    "PITCHSTAITH",
    "Mossbank",
    "BOGIRON",
    "Mireholt",
    "CHROMLOOP",
    "Marlfell",
    "NITREVAULT",
    "Glaucove",
    "NITROSTAITH",
    "Chalkfen",
    "ETHYNWOLD",
    "Woadfen",
    "RUNNELGATE",
    "Ghyllmere",
    "SPARKHOLT",
    "Scoriafen",
    "DIPLEGAR",
    "Gritfen",
    "OLEUMWEIR",
    "Brindlefell",
    "SKARVOLT",
    "GOBSPALL",
    "Culletfen",
    "GOBWOLD",
    "Culletwick",
    "PUSHERFELL",
    "Sootmere",
    "CREELWOLD",
    "Rovingholt",
    "LIXIVQUERN",
    "Bauxfen",
    "OSMOLITH",
    "Spumeholt",
    "GAUZEFELL",
    "Ammoxwick",
    "OSMOQUAY",
    "Tidecairn",
    "SIPHONWOLD",
    "Reedfen",
    "GIBBSQUERN",
    "Laterifen",
    "LOOPERQUAY",
    "Roughmere",
    "COILSHAW",
    "Loopercroft",
    "UREASTAITH",
    "GRATEHOLT",
    "Emberbarrow",
    "Valmet",
    "Voith",
    "Andritz",
    "Kadant",
    "International Paper",
    "Georgia-Pacific",
    "Kimberly-Clark",
    "Stora Enso",
    "Domtar",
    "WestRock",
    "Suzano",
    "Mondi",
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
    "Honeywell UOP",
    "Kellogg Brown",
    "Albemarle",
    "Axens",
    "Marathon Petroleum",
    "Phillips 66",
    "W.R. Grace",
    "CITGO",
    "Valero Energy",
    "SunCoke",
    "Koppers",
    "Schalker",
    "US Steel",
    "Tata Steel",
)
R14_OPENING = (
    "Helixmere Biologics Building C lyophilizer LYO-4 is mid-primary on 8400 "
    "vials of a monoclonal antibody"
)
NOVEL_LINE = "Novel coverage: 48%"
PLANT = "PUSHERFELL"
GEO = "Sootmere"
CELL = "CB-6"
DOMAIN = "coke-oven-battery-heating"
RECORD_ID = "maos-r52-001"
ROUND = 52
DELAY_S = 0.80
TAU_E_S = 0.92


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
        if p.parent.name == "maos-r52":
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
        if p.parent.name == "maos-r52":
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
        if p.parent.name == "maos-r52":
            continue
        try:
            text = p.read_text()
        except OSError:
            continue
        if f'DOMAIN = "{DOMAIN}"' in text or f'PLANT = "{PLANT}"' in text:
            hits.append(f"{p}: claimed {PLANT}/{DOMAIN}")
        if GEO in text and PLANT in text:
            hits.append(f"{p}: geo+plant {GEO}/{PLANT}")
    return hits


def build_record():
    ticks, heads = cents_ticks(
        [4580, 6514, 7226, 6_800_000, 684_000_000, 13_680_000_000, 18_360_000_000],
        [
            (1, -2, -1, 2, 1),
            (2, -5, -1, 3, 2),
            (2, -6, -2, 3, 2),
            (1, -6, -2, 2, 1),
            (1, -5, -2, 2, 1),
            (1, -6, -2, 1, 1),
            (0, -5, -2, 1, 1),
        ],
    )
    assert abs(heads["total"] - (-0.16)) < 1e-9, heads

    trace = math.exp(-DELAY_S / TAU_E_S)
    eta1 = 0.25 / trace
    eta2 = 0.22 / trace
    eta3 = 0.21 / trace
    dw1 = eta1 * 1.0 * trace
    dw2 = eta2 * 1.0 * trace
    dw3 = eta3 * 1.0 * trace
    w1 = 0.50 - dw1
    w2 = 0.44 - dw2
    w3 = 0.41 - dw3
    assert abs(w1 - 0.25) < 5e-4, w1
    assert abs(w2 - 0.22) < 5e-4, w2
    assert abs(w3 - 0.20) < 5e-4, w3

    spike_events = [
        {"channel": "flue.hot", "t_rel_ms": 0.314, "amplitude": 0.54},
        {"channel": "coke.end", "t_rel_ms": 1.128, "amplitude": 0.61},
        {"channel": "draft.ok", "t_rel_ms": 2.018, "amplitude": 0.55},
        {"channel": "wall.dT", "t_rel_ms": 3.168, "amplitude": 0.76},
        {"channel": "flue.hot", "t_rel_ms": 4.158, "amplitude": 0.51},
        {"channel": "wall.dT", "t_rel_ms": 4.828, "amplitude": 0.78},
        {"channel": "draft.ok", "t_rel_ms": 5.348, "amplitude": 0.57},
        {"channel": "wall.delta.high", "t_rel_ms": 6.514, "amplitude": 1.36},
        {"channel": "flue.in_band", "t_rel_ms": 6.706, "amplitude": 1.14},
        {"channel": "coke.end", "t_rel_ms": 6.894, "amplitude": 0.64},
        {"channel": "ctrl.gate", "t_rel_ms": 7.226, "amplitude": 1.07},
        {"channel": "wall.dT", "t_rel_ms": 8.848, "amplitude": 0.45},
        {"channel": "coke.end", "t_rel_ms": 10.728, "amplitude": 0.82},
        {"channel": "draft.ok", "t_rel_ms": 13.028, "amplitude": 0.47},
        {"channel": "flue.hot", "t_rel_ms": 18.508, "amplitude": 0.44},
        {"channel": "ctrl.gate", "t_rel_ms": 26.248, "amplitude": 0.86},
        {"channel": "gas.step.probe", "t_rel_ms": 6800.0, "amplitude": 0.95},
        {"channel": "wall.dT", "t_rel_ms": 6888.4, "amplitude": 0.41},
        {"channel": "flue.in_band", "t_rel_ms": 6972.0, "amplitude": 0.36},
        {"channel": "human.ratify", "t_rel_ms": 684000.0, "amplitude": 0.80},
        {"channel": "oven.hold", "t_rel_ms": 684900.0, "amplitude": 0.73},
        {"channel": "wall.attack", "t_rel_ms": 685700.0, "amplitude": 0.85},
        {"channel": "flue.hot", "t_rel_ms": 13680000.0, "amplitude": 0.31},
        {"channel": "wall.dT", "t_rel_ms": 13680720.0, "amplitude": 0.29},
        {"channel": "draft.ok", "t_rel_ms": 13681480.0, "amplitude": 0.26},
        {"channel": "wall.collapse", "t_rel_ms": 18360000.0, "amplitude": 0.93},
    ]

    contrast_spikes = [
        {"channel": "gas.demand", "t_rel_ms": 0.000, "amplitude": 0.84},
        {"channel": "wall.clear", "t_rel_ms": 0.182, "amplitude": 0.78},
        {"channel": "flue.hot", "t_rel_ms": 0.418, "amplitude": 0.24},
        {"channel": "coke.end", "t_rel_ms": 1.458, "amplitude": 0.40},
        {"channel": "wall.dT", "t_rel_ms": 4.868, "amplitude": 0.53},
        {"channel": "ctrl.gate", "t_rel_ms": 7.048, "amplitude": 0.90},
        {"channel": "gas.step.probe", "t_rel_ms": 2900.0, "amplitude": 0.35},
        {"channel": "wall.collapse", "t_rel_ms": 18360000.0, "amplitude": 0.10},
    ]

    excerpt = [
        {"t_us": 314, "neuron_id": 9},
        {"t_us": 1128, "neuron_id": 84},
        {"t_us": 2018, "neuron_id": 24},
        {"t_us": 3168, "neuron_id": 48},
        {"t_us": 4158, "neuron_id": 12},
        {"t_us": 4828, "neuron_id": 56},
        {"t_us": 5348, "neuron_id": 96},
        {"t_us": 6514, "neuron_id": 46},
        {"t_us": 6706, "neuron_id": 14},
        {"t_us": 6894, "neuron_id": 88},
        {"t_us": 7226, "neuron_id": 130},
        {"t_us": 8848, "neuron_id": 60},
        {"t_us": 10728, "neuron_id": 28},
        {"t_us": 13028, "neuron_id": 112},
        {"t_us": 18508, "neuron_id": 18},
        {"t_us": 26248, "neuron_id": 138},
    ]

    rec = {
        "id": RECORD_ID,
        "title": "PUSHERFELL CB-6: wall-pair delta 84 K beats flue-T-in-band by 192 us; correct MODIFY still loses ovens 47-48 to a pre-t0 through-wall crack",
        "rights": dict(RIGHTS),
        "state": {
            "sim_or_real": "designed",
            "domain": DOMAIN,
            "scenario_name": "PUSHERFELL / Sootmere Coking CB-6",
            "timestamp_local": "2026-07-26T03:18:00-05:00",
            "t0_us": 1753510680000052,
            "gate_latency_us": 714,
            "race_window_us": 500,
            "race_window_rel_ms": [6.514, 7.014],
            "description": "Sootmere Coking battery CB-6 sits at 18.4 h coking on a 78-oven by-product slot battery when three heterogeneous, individually-correct agents jointly report 'battery heat healthy, push ahead'. FLUE's 12-bit battery-mean underfire thermocouple is 1328 C inside 1280-1380. DRAFT's stack draft is 4.2 mmH2O inside 3.5-5.5. COKE's coke-end optical-pyrometer mean is 1045 C inside 1000-1100. The conjunction is not a wall-true certificate: ovens 47/48 share a through-wall silica-brick crack, so wall-pair delta T is 84 K (healthy < 18; hold if > 35) and heating-flue CO is 8.4 vol% (healthy < 1.2; hold if > 2.5) while battery-mean flue T, stack draft, and coke-end mean still see 77 sealed ovens plus one leaking pair. Wall-pair T infers 84 K and heating-flue CO 8.4 vol% but policy treats the wall tap as a sticky-probe tag unless battery-mean flue also trips (2015 'noisy wall-TC after a ram stall'). Residual-first latches COKING-HOLD plus an underfire-gas step probe; flue-T-first would have authorized PUSH-AHEAD 18.4 to 16.1 h into a production-catchup window with ovens 47-48 already cracked.",
            "goal": "Hold coking time at 18.4 h without a catchup push while wall-pair delta T > 35 K AND heating-flue CO > 2.5 vol% AND ovens 47-48 remain unisolated; keep heating-flue flashback at 0 and wall-collapse events at 0.",
            "race": {
                "contenders": [
                    "wall.delta.high 84 K (ovens 47/48 wall-pair vs battery-mean flue)",
                    "flue.in_band 1328 C (battery-mean underfire flue T)",
                ],
                "semantics": "Wall-delta-first latches COKING-HOLD + GAS-STEP-PROBE + OVEN-47/48 hold. Flue-T-first latches PUSH-AHEAD (18.4 to 16.1 h, underfire gas +8%, no isolate).",
                "window_derivation": "500 us = one 365 us wall-dT ADC slot plus 135 us flue-T publish.",
                "order_evidence_note": "Margin 192 us vs combined jitter 58 us (wall 34 + flue 24): 3.3x. The 192 us gap sits inside min(500, 500) us, so a sub-flip-bound perturbation reverses triage order. The gate rides the order-invariant floors wall-delta T > 35 K and heating-flue CO > 2.5 vol%, not the alarm order.",
            },
            "topology": {
                "site": "Sootmere Coking, invented mill-town Sootmere, battery CB-6: 78 by-product slot ovens, 16.2 m x 6.5 m x 0.45 m, 18.4 h coking, regenerative underfire, Grade-B pusher-side LOTO",
                "agents": "FLUE battery-mean underfire temperature (vendor Heatwick): 20 Hz 12-bit on the collector-main TC cluster. DRAFT stack draft (vendor Stacknoll): 50 Hz on the common stack tap. COKE coke-end optical pyrometer mean (vendor Endpyre): 50 Hz across the 78-oven coke-side row. WALL wall-pair delta T plus heating-flue CO (vendor Wallghyll) is commissioned as a sticky-probe tag, not as a wall-integrity tag. Heterogeneous stacks, no shared intent schema, one 20 ms battery-bus epoch",
                "coupling": "All three playbook confirms live on the WRONG volume. FLUE is correct that battery-mean underfire T sits at 1328 C (77 sealed ovens dominate the collector-main average). DRAFT is correct that stack draft is 4.2 mmH2O (the common stack still sees regenerative flow). COKE is correct that the coke-end mean is 1045 C (the leaking pair is one of 78). Playbook PB-CB-6 treats the conjunction as permission to shorten coking. No agent is faulty; the flue average is looking at battery-mean heat, not at ovens 47-48's cracked wall.",
            },
            "sensors": [
                "battery-mean underfire 12-bit, 20 Hz, 24 us jitter, 1328 C (dead-band 1280-1380)",
                "stack draft, 50 Hz, 18 us jitter, 4.2 mmH2O (band 3.5-5.5)",
                "coke-end optical pyrometer mean, 50 Hz, 26 us jitter, 1045 C (band 1000-1100)",
                "wall-pair delta T ovens 47/48, 20 Hz, 34 us jitter, 84 K (healthy < 18; policy floor 35 K is not armed unless battery-mean flue also trips)",
                "heating-flue CO 8.4 vol% (healthy < 1.2; hold if > 2.5)",
                "cross-wall IR on the 47/48 header is NOT commissioned at t0 (installed after this incident)",
            ],
            "constraints": {
                "coking_h": 18.4,
                "coking_hold_floor_h": 18.4,
                "proposed_coking_h": 16.1,
                "flue_t_C": 1328,
                "flue_t_deadband_C": [1280, 1380],
                "draft_mmH2O": 4.2,
                "draft_band_mmH2O": [3.5, 5.5],
                "coke_end_C": 1045,
                "coke_end_band_C": [1000, 1100],
                "wall_dT_K": 84,
                "wall_dT_hold_K": 35,
                "wall_dT_healthy_K": 18,
                "flue_co_volpct": 8.4,
                "flue_co_hold_volpct": 2.5,
                "flue_co_healthy_volpct": 1.2,
                "flashback_trip_volpct": 12.0,
                "heating_flue_co_now_volpct": 8.4,
                "oven_count": 78,
                "fault_ovens": "47/48",
                "fault_wall": "ovens 47-48 through-wall silica crack",
            },
            "fault_context": {
                "failure_class": "THROUGH-WALL CRACK CERTIFICATE OF A MEAN-TRUE BATTERY: three individually-correct heterogeneous agents each read a locally-true loop; a cracked wall between ovens 47 and 48 partitions wall-true delta T and heating-flue CO from battery-mean flue, stack draft, and coke-end mean, so the playbook's flue-T / draft / coke-end conjunction is not a wall-true certificate",
                "igniter": "ovens 47/48 through-wall crack after 19 min of unmonitored raw-gas leak into the heating flue; pusher-side visual PASSES (the crack sits behind the regenerator sole; the wall is already thinning on the far side)",
                "naive_failure": "PB-CB-6 PUSH-AHEAD on three healthy loops: 18.4 to 16.1 h into a production-catchup window with ovens 47-48 already cracked, heating-flue flashback at 14 vol% CO, $4.6M plus a 56-hour unplanned stop",
            },
            "poisoned_context": {
                "naive_alarm": "Playbook PB-CB-6 (after the 2015 'noisy wall-TC after a ram stall') auto-drafts PUSH-AHEAD whenever battery-mean flue T is inside 1280-1380 C AND stack draft inside 3.5-5.5 mmH2O AND coke-end mean inside 1000-1100 C, ignoring the wall-pair tap unless battery-mean flue also trips",
                "why_poisoned": "The three confirms are locally true and jointly insufficient. The wall-pair T is a commissioned sensor that policy treats as sticky-probe-only. Independence of 'battery-mean flue in band, therefore every wall is sealed' is the hidden assumption, and it is false across a through-wall-crack-plus-mean-mix path.",
            },
            "constraint": "Do not shorten coking below 18.4 h AND do not raise underfire gas while wall-pair delta T > 35 K AND heating-flue CO > 2.5 vol%. Discriminate through-wall crack vs true high-heat with a reversible underfire-gas step probe before any push-ahead.",
        },
        "proposed_action": {
            "actor": "battery supervisory optimizer BSO (auto-playbook PB-CB-6 draft), submitted to gate TG-CB-6",
            "name": "push_ahead",
            "action": "PUSH-AHEAD: 18.4 -> 16.1 h coking, underfire gas +8%, no gas-step probe, no oven 47/48 hold",
            "summary": "Treat three in-spec loops as a healthy wall-true battery and shorten night-shift coking to clear a production-catchup window.",
            "parameters": {
                "coking_h": 16.1,
                "gas_step_probe": False,
                "oven_hold": False,
                "human_ratify": False,
            },
            "steps": [
                "assert battery-mean flue T 1328 C inside 1280-1380",
                "assert stack draft 4.2 mmH2O inside 3.5-5.5",
                "assert coke-end mean 1045 C inside 1000-1100",
                "shorten coking 18.4 to 16.1 h and raise underfire gas +8% over 8 min",
                "hold wall-pair T unread as a wall-integrity tag",
            ],
            "evidence": [
                {
                    "observable": "wall-pair delta T ovens 47/48",
                    "value": 84,
                    "unit": "K",
                    "source": "WALL dT vs battery-mean flue",
                    "note": "healthy < 18 K; policy floor 35 K is not armed unless battery-mean flue also trips",
                },
                {
                    "observable": "heating-flue CO",
                    "value": 8.4,
                    "unit": "vol%",
                    "source": "WALL flue-CO analyzer",
                    "note": "healthy < 1.2; hold floor 2.5; lives on the leaking 47/48 heating flue, not the battery-mean collector",
                },
                {
                    "observable": "battery-mean underfire temperature",
                    "value": 1328,
                    "unit": "C",
                    "source": "FLUE 12-bit",
                    "note": "healthy-load band 1280-1380 C; 77 sealed ovens still dominate the collector-main average",
                },
                {
                    "observable": "stack draft",
                    "value": 4.2,
                    "unit": "mmH2O",
                    "source": "DRAFT stack tap",
                    "note": "band 3.5-5.5; stack-true, wall-false",
                },
                {
                    "observable": "coke-end pyrometer mean",
                    "value": 1045,
                    "unit": "C",
                    "source": "COKE 78-oven mean",
                    "note": "band 1000-1100; mean-true, pair-false",
                },
                {
                    "observable": "race margin",
                    "value": 192,
                    "unit": "us",
                    "source": "wall.delta.high 6.514 ms vs flue.in_band 6.706 ms",
                    "note": "combined jitter 58 us, 3.3x; inside 500 us flip bound",
                },
            ],
            "basis": "PB-CB-6 fires on three locally-true confirms. The draft does not read wall-pair delta 84 K as a crack residual and does not treat heating-flue CO 8.4 vol% as a wall-leak discriminant.",
            "expected_cost_bound": "If the draft executes: heating-flue flashback at 14 vol% CO on ovens 47-48, $4.6M plus 56-hour unplanned stop. If MODIFIED: probe plus hold, with residual risk from wall thinning already seeded in the 19 min pre-t0 leak.",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "correctness": "correct",
            "decided_by": "TG-CB-6 thalamic release gate",
            "decision_t_rel_ms": 7.226,
            "rationale": "MODIFY the draft: strip the push-ahead, hold 18.4 h coking, run a 6.8 s underfire-gas step probe (-4% underfire gas), and isolate ovens 47-48 only if the probe stays mean-false. Numeric floor: do not shorten coking below 18.4 h AND do not raise underfire gas while wall-pair delta T > 35 K AND heating-flue CO > 2.5 vol%. Observed delta 84 K and flue CO 8.4 vol% both violate the release predicate, so a push-ahead is forbidden even though all three playbook confirms are numerically true. The three confirms are not a wall-true certificate: they live on battery-mean flue, stack draft, and coke-end mean past a cracked 47/48 wall, and the playbook's conjunction of mean-true loops is not a wall-true certificate. Probe discriminant: after a 6.8 s -4% underfire-gas step, a through-wall crack keeps |Delta battery-mean T| <= 0.8 K (the leaking pair does not recouple the collector-main); a live sealed wall moves >= 3.2 K. Order-code discipline: wall-delta beat flue-T by 192 us inside the 500 us flip bound, so triage order is flip-fragile; the hold rides the order-invariant floors, not the winner tag. Human ratification: oven 47-48 hold is confined-space pusher-side work with fitted 11.4 min dead-man; the gate may hold and probe autonomously but may not break the oven interlock without the operator confirm.",
            "constraint_checked": {
                "coking_h": {"observed": 18.4, "floor": 18.4, "proposed_target": 16.1},
                "wall_dT_K": {"observed": 84, "hold_if_above": 35},
                "flue_t_C": {"observed": 1328, "band": [1280, 1380]},
                "flue_co_volpct": {"observed": 8.4, "hold_if_above": 2.5},
            },
        },
        "executed_action": {
            "name": "coking_hold_gas_step_probe_isolate",
            "action": "COKING-HOLD + GAS-STEP-PROBE + OVEN-47/48-HOLD (gate-mandated modification)",
            "executed_as_proposed": False,
            "parameters": {
                "coking_h": 18.4,
                "gas_step_probe": True,
                "oven_hold": True,
                "human_ratify": True,
            },
            "gate_effect": "MODIFY: push-ahead stripped. Hold 18.4 h. 6.8 s underfire-gas step -4%. Probe stays mean-false (delta 84 -> 83 K, crack band |Delta battery-mean T| <= 0.8 K) so the oven interlock is broken after 11.4 min human ratify and ovens 47-48 are held. Setpoint resumes after a live-wall verify.",
            "deviations": "PB-CB-6 push-ahead stripped entirely. Underfire gas is stepped only for the 6.8 s probe then returned. Oven interlock wait added (11.4 min fitted climb+ratify). Cross-wall IR survey added during the hold (not in the draft).",
            "execution_log": [
                {"t_rel_ms": 7.226, "entry": "TG-CB-6 MODIFY latched 714 us after wall-delta win; push-ahead stripped; hold+probe authorized"},
                {"t_rel_ms": 6800.0, "entry": "gas-step probe: underfire gas -4% for 6.8 s; delta 84 -> 83 K (crack band |Delta battery-mean T| <= 0.8 K); flue T 1328 -> 1327.4 C"},
                {"t_rel_ms": 684000.0, "entry": "operator ratifies oven interlock break after 11.4 min confined-space climb (fitted walk+interlock)"},
                {"t_rel_ms": 684900.0, "entry": "ovens 47-48 held; wall dT slaved off the pusher schedule; remaining 76 ovens recovered toward 11 K over 3.8 h"},
                {"t_rel_ms": 685700.0, "entry": "header survey: 47/48 already thinned on the far side; 19 min pre-t0 raw-gas leak logged"},
                {"t_rel_ms": 13680000.0, "entry": "true sealed wall on the remaining battery: delta 11 K, flue CO 0.7 vol%, delta below 35; push-ahead now legal on CB-7 only"},
                {"t_rel_ms": 18360000.0, "entry": "silica-brick wall collapse at ovens 47-48 from the pre-t0 through-wall crack; battery quarantined 42 h"},
            ],
        },
        "future_outcome": {
            "summary": "Correct MODIFY prevented the 18.4->16.1 h push-ahead into a cracked 47/48 wall and the immediate heating-flue flashback path. The battery still failed: 19 min of unmonitored pre-t0 raw-gas leak had already thinned the wall. Process-correct gate, bounded world loss, negative total.",
            "state_delta": {
                "coking": "held 18.4 h through probe and isolate; later legal push-ahead only on the sister battery after 3.8 h wall recovery",
                "wall": "ovens 47-48 isolated from the pusher schedule; remaining battery recovered toward 11 K delta",
                "heating_flue": "47/48 crack logged and held; battery-mean flue T no longer trusted as wall-true heat",
                "battery": "night-shift battery quarantined; 47/48 thinned; wall collapse at +5.1 h; 42 h outage",
            },
            "timeline": [
                {"t_rel_ms": -1140000.0, "event": "t0-19 min: ovens 47/48 through-wall crack begins; wall-delta crosses 35 K up; raw-gas leak starts thinning the far-side brick"},
                {"t_rel_ms": -480000.0, "event": "t0-8 min: wall-delta first crosses 35 K; PB-CB-6 ignores it because battery-mean flue is 1331 C"},
                {"t_rel_ms": 0.0, "event": "t0: wall-delta vs flue-T race on the battery bus"},
                {"t_rel_ms": 6.514, "event": "wall-pair delta at 84 K wins by 192 us"},
                {"t_rel_ms": 6.706, "event": "flue-T-in-band flag (loser)"},
                {"t_rel_ms": 7.226, "event": "TG-CB-6 MODIFY"},
                {"t_rel_ms": 6800.0, "event": "gas-step probe confirms through-wall crack (Delta battery-mean T 0.6 K, crack band)"},
                {"t_rel_ms": 684000.0, "event": "human ratify 11.4 min; ovens 47-48 held; thinned wall logged"},
                {"t_rel_ms": 13680000.0, "event": "true sealed wall after 3.8 h; push-ahead legal only with wall-dT slave"},
                {"t_rel_ms": 18360000.0, "event": "silica-brick wall collapse from the pre-t0 through-wall crack; battery quarantined"},
                {"t_rel_ms": 345600000.0, "event": "+4 d contrast: sister battery CB-7 true high-heat; same gate ACCEPTs the push-ahead"},
                {"t_rel_ms": 1814400000.0, "event": "+21 d CR-C-5204: standing gas-step probe + triple-edge depression mandate + wall-dT armed without flue-T coincidence + battery-mean flue declared mix-vulnerable"},
            ],
            "observed_effects": [
                "push-ahead avoided: coking never left 18.4 h; 0 immediate heating-flue flashbacks from the draft",
                "crack proven, not asserted: gas-step |Delta battery-mean T| 0.6 <= 0.8 K crack band vs live-wall control 3.6 K",
                "mean slaved: battery-mean flue T no longer a wall-true tag without wall-pair dT",
                "battery still collapsed: thinned 47/48 vs 0 wall-collapse campaign allowance; 42 h outage, $2.38M (designed $)",
                "cross-wall IR was not a commissioned sensor at t0; the 19 min raw-gas thinning was invisible to FLUE/DRAFT/COKE",
            ],
            "surprises": [
                "Three locally-true loops are not a wall-true certificate: the wall-true delta lived under battery-mean flue, stack draft, and coke-end mean. Conjunction of in-spec mean loops was the hidden assumption, and it is false across a through-wall-crack-plus-mix path.",
                "Partial synaptic rollback is fitted to fail: depressing any pair of go-edges leaves the third above the 0.30 fire threshold, so the push-ahead still goes. Coordinated depression of all three edges is required.",
                "Delayed (5.1 h): correct hold did not undo 19 min of wall thinning. Collapse still opened. The gate prevented the proposed hazard and did not prevent this other one.",
                "Stamp-charged / dense-charge sub-variant: a 6.8 s -4% gas step on a 0.42x freeboard stamp battery overshoots a LIVE sealed wall to a 41 K false delta (trip 35). Stamp campaigns must use 19 s at -1.5%.",
            ],
            "delayed_side_effects": [
                {
                    "at": "+5.1 h",
                    "effect": "Silica-brick wall collapse at ovens 47-48 from the pre-t0 through-wall crack; 42 h battery outage booked at $2.38M. This is the primary episode's terminal world state, not a footnote.",
                },
                {
                    "at": "+4 d",
                    "effect": "Sister battery CB-7 reaches a true high-heat window (delta 9 K, flue CO 0.6 vol%, mean flue 1334 C, draft 4.1 mmH2O). Same gate ACCEPTs the 18.4->16.1 h push-ahead the primary MODIFIED away.",
                },
                {
                    "at": "+21 d",
                    "effect": "CR-C-5204 ships: gas-step probe is standing configuration; triple-edge coordinated depression is the plasticity rule; wall-pair dT is armed without flue-T coincidence; battery-mean flue is labeled mix-vulnerable with a 35 K dT alarm.",
                },
            ],
            "subvariant_constraint": {
                "name": "stamp-charged / dense-charge (cycle-2 physical-constraints sub-variant)",
                "mechanism": "stamp-charged freeboard 0.42x the 78-oven top-charge battery (tighter charge, 2.4x gas-step gain), bulk density 1.12 t/m3 vs 0.78",
                "probe_refit": "6.8 s -4% underfire-gas step on the stamp unit moves even a live sealed wall to a 41 K false delta (inside the 35 K trip) via regenerator slosh. Required probe is 19 s at -1.5% (live Delta 3.1 K, crack Delta 0.5). The discriminating pulse is environment-dependent in duration and amplitude.",
                "consequence": "top-charge probe numbers do not port to stamp-charged batteries; standing configuration is per-charge-class, not per-shop",
            },
            "embedded_contrast_decision": {
                "note": "SAME gate (TG-CB-6), OPPOSITE correct disposition, with its own 182 us race. Teaches the boundary: do not treat 'never push-ahead' as the lesson. The discriminant is wall-pair dT + heating-flue CO + probe, not the three playbook mean confirms alone.",
                "when": "+4 d, sister battery CB-7, true high-heat after a delayed coke-catchup, 78 ovens",
                "state": {
                    "sim_or_real": "designed",
                    "summary": "delta 9 K, flue CO 0.6 vol%, mean flue 1334 C, draft 4.1 mmH2O. Demand flag vs wall-clear race: demand at t+0.000, wall-clear at t+0.182 ms.",
                    "race_window_us": 500,
                    "race_flip_narrative": "demand vs wall-clear 182 us apart inside the 500 us flip bound. Reversing order reshuffles triage minutes; the ACCEPT rides wall-delta 9 < 35 K and a 4.2 s gas-step verify that moves battery-mean T 3.5 K (live sealed wall, no crack).",
                },
                "proposed_action": {
                    "action": "PUSH-AHEAD 18.4 -> 16.1 h",
                    "summary": "This time the playbook predicate is met AND wall-pair dT plus heating-flue CO agree the battery is wall-true, not crack-diluted.",
                },
                "safety_decision": {
                    "decision": "ACCEPT",
                    "rationale": "ACCEPT the push-ahead: delta 9 K < 35, flue CO 0.6 vol% with a 4.2 s gas-step verify that moves battery-mean T 3.5 K. Numeric floor that blocked the primary is now clear. Scope: 16.1 h, not faster.",
                },
                "executed_action": {
                    "action": "push-ahead as proposed",
                    "executed_as_proposed": True,
                },
                "future_outcome": {
                    "observed_effects": [
                        "CB-7 wall collapses 0; wall-delta 10 K after the push-ahead (no crack)",
                        "heating-flue CO 0.7 vol% after the push-ahead (no raw-gas dump)",
                    ],
                    "lesson_delta": "Three in-spec mean loops are legal release only with wall-pair dT armed, heating-flue CO as a leak flag, and a probe that can recouple battery-mean T. Same gate, opposite disposition.",
                },
                "reward_components": {
                    "_aggregation": AGG,
                    "task_progress": 0.15,
                    "safety": 0.12,
                    "efficiency": 0.08,
                    "coherence": 0.10,
                    "exploration": 0.04,
                    "total": 0.49,
                },
                "spike_events": contrast_spikes,
            },
            "governance_subgame": {
                "decision": "CR-C-5204: standing policy for multi-agent coke-oven push-aheads",
                "meta_gate": "priced options: (a) RETIRE playbook mean conjunction, wall-dT-only: loses a fast cheap confirm, -1.8 ovens/day mean on 2 batteries/yr; (b) KEEP + standing gas-step probe + wall-dT armed without flue-T coincidence + battery-mean flue labeled mix-vulnerable + triple-edge depression; (c) STATUS QUO: fitted through-wall-crack pass rate 0.44%/campaign x $4.6M flashback plus the silent wall-thinning load",
                "outcome": "approved SCOPED option (b) on the 2 78-oven batteries that share the FLUE/DRAFT/COKE stack; stamp-charged campaigns get the 19 s / -1.5% probe table; night-shift CSV exports must carry 0.5 K native resolution (the fraud tail's 5 K quantization is 10 bins off plant truth)",
            },
            "hazard_avoided": "immediate heating-flue flashback at 14 vol% CO from an 18.4->16.1 h push-ahead into cracked ovens 47-48; $4.6M plus 56-hour unplanned stop and the shop-stop path that would have followed an uncontained increase",
            "incident": "Silica-brick wall collapse on the night-shift battery from the pre-t0 through-wall crack; battery quarantined 42 h; $2.38M designed cost. Mechanism is 19 min pre-t0 raw-gas leak, not the gate's hold.",
            "latency_ms": 0.714,
            "reward_inflection_t_us": 18360000000,
            "reward_inflection_note": "Safety and task dive at wall collapse (5.1 h) when the pre-t0 thinned brick opens. Gate tick at 7226 us is process-correct and is not the inflection.",
            "counterfactuals": {
                "execute_draft_as_proposed": "coking hits 16.1 h at +8 min; immediate heating-flue flashback at 14 vol% CO on ovens 47-48; $4.6M plus 56 h; the through-wall-crack story is never found because collapse morphology destroys the race evidence",
                "hold_without_probe": "crack stays; delta stays at 84 K; operator eventually shortens on the same three mean confirms 2 h later",
                "rollback_any_pair": "any two go-edges depressed below 0.30 leaves the third at 0.50 / 0.44 / 0.41; the push-ahead still fires. Coordinated depression of all three is the cure",
            },
            "race_result": {
                "winner": "wall.delta.high (6.514 ms, delta 84 K)",
                "loser": "flue.in_band (6.706 ms, 1328 C)",
                "margin_us": 192,
                "counterfactual_if_reversed": "Flue-T-first by < 192 us inside the 500 us window would have headed the PB-CB-6 push-ahead in the triage queue. The numeric floors still MODIFY. The flip costs seconds of playbook inertia, not the verdict — unless a weak supervisor rides the winner tag instead of wall-delta and heating-flue CO.",
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
            "notes": "Correct MODIFY, battery still collapsed. total -0.16 = 0.08 + -0.35 + -0.12 + 0.14 + 0.09. Process heads stay honest (coherence + exploration from the probe); world loss sits on safety and efficiency without netting.",
            "component_notes": "task_progress 0.08: coking held and remaining battery recovered, but the night-shift coke is one quality unit so the campaign is not a success. safety -0.35: wall collapse from pre-t0 through-wall crack, no 16.1 h flashback from the draft. efficiency -0.12: 3.8 h extra recovery + 11.4 min HITL + 42 h outage. coherence 0.14: three agents retained, mean-mix vs wall-true diagnosed, triple-edge scar exhibited. exploration 0.09: gas-step probe is a new reversible discriminant.",
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
            "note": "Loihi-2 4-core 23 pJ/spike; populations flue 0-39, wall 40-79, coke 80-119, gate 120-159; excerpt is the 40 ms decision window (verdict at 7226 us)",
            "excerpt": excerpt,
            "routing": {
                "source": "mean_healthy_pop",
                "target": "push_ahead_pop",
                "table": [
                    {
                        "from": "flue_in_band_pop",
                        "to": "push_ahead_pop",
                        "weight": 0.25,
                        "weight_at_illusion": 0.50,
                        "weight_commissioned": 0.17,
                        "note": "scar edge 1: 0.17 commissioned -> 0.50 during the 19 min illusion -> 0.25 after coordinated ACh-gated depression",
                    },
                    {
                        "from": "draft_ok_pop",
                        "to": "push_ahead_pop",
                        "weight": 0.22,
                        "weight_at_illusion": 0.44,
                        "weight_commissioned": 0.16,
                        "note": "scar edge 2: depressing edges 1+3 leaves this at 0.44 > 0.30 fire threshold",
                    },
                    {
                        "from": "coke_end_in_band_pop",
                        "to": "push_ahead_pop",
                        "weight": 0.20,
                        "weight_at_illusion": 0.41,
                        "weight_commissioned": 0.15,
                        "note": "scar edge 3: depressing edges 1+2 leaves this at 0.41 > 0.30. Coordinated depression of all three is required",
                    },
                    {
                        "from": "wall_dt_pop",
                        "to": "coking_hold_pop",
                        "weight": 0.64,
                        "note": "discriminating edge: wall-true delta T to hold. Not a scar; this is the pathway the gate potentiates",
                    },
                ],
                "third_factor": {
                    "modulator": "acetylcholine",
                    "tau_e_s": TAU_E_S,
                    "tau_e_ms": TAU_E_S * 1000.0,
                    "eligibility": "coordinated pre_post_stdp on ALL THREE mean-healthy-go edges; ACh at wall-delta-win tags flue.in_band->push, draft.ok->push, and coke.end.in_band->push; negative credit at probe-fail (through-wall crack confirmed, +0.80 s) depresses ALL THREE. trace e^{-0.80/0.92}=0.41913; eta 0.59647 / 0.52489 / 0.50103; dw -0.250 / -0.220 / -0.210; weights 0.50->0.25, 0.44->0.22, 0.41->0.20. Rolling back any pair is fitted to fail (the remaining edge stays > 0.30).",
                },
            },
        },
        "gate_snn": {
            "decision_window_ms": 25,
            "decision_window_s": 0.025,
            "decision": "MODIFY",
            "note": "modify_hold integrates wall-pair dT + heating-flue CO against playbook drive; accept_raise and reject_abort stay sub-threshold; decision matches safety_decision.decision",
            "populations": [
                {"name": "modify_hold", "neurons": 80, "threshold": 0.55, "mean_rate_hz": 20.0, "spikes": 40},
                {"name": "accept_raise", "neurons": 80, "threshold": 0.55, "mean_rate_hz": 8.0, "spikes": 16},
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
            "scenario": "ZZ -- PUSHERFELL / Sootmere Coking CB-6: through-wall-crack certificate of a mean-true battery; correct MODIFY to hold+gas-step+isolate; battery still fails on unmonitored pre-t0 wall thinning",
            "coordination_failure_class": "THROUGH-WALL CRACK CERTIFICATE OF A MEAN-TRUE BATTERY: three individually-correct heterogeneous agents each read a locally-true loop; a cracked wall between ovens 47 and 48 partitions wall-true delta T and heating-flue CO from battery-mean flue, stack draft, and coke-end mean, so the playbook's flue-T / draft / coke-end conjunction is not a wall-true certificate",
            "injections": {
                "cycle1_domain": "coke-oven-battery-heating (justified novel subdomain of industrial-process / metallurgical coke): first by-product slot-oven battery in this factory; displaces warehouse-amr, aerial-swarm, district-heating, event-camera-traffic-grid, pharmaceutical-lyophilization, water-treatment, float-glass, underwater-rov, electrolytic-aluminum, czochralski-pull, slot-die coating, pem-water-electrolysis, wind-turbine pitch, surgical-assist, optical-fiber-draw, kraft-recovery-boiler, steel-continuous-caster, humanoid-locomotion, vacuum-induction melt, steam-methane reformer, cement-rotary-kiln-clinker, autoclave-composite-cure, geothermal-binary-orc, tire-curing-press, chlor-alkali-membrane-electrolysis, delayed-coker-drum-switch, lng-mche-mixed-refrigerant, claus-sulfur-recovery, ammonia-synthesis-converter, blast-furnace-burden-descent, hdpe-slurry-loop-polymerization, ammonia-haber-bosch-converter, ethylene-steam-cracker-coil, hydroelectric-kaplan-wicket, fcc-riser-regenerator, fcc-regenerator-cyclone-dipleg, sulfuric-contact-converter, eaf-foamy-slag-water-panel, and glass-container-is-machine. Domain constraint: coking-time floor while wall-pair delta T > 35 K with battery-mean flue still inside the healthy band. Sensor delta: +battery-mean underfire T, +stack draft, +coke-end pyrometer mean, +wall-pair dT, +heating-flue CO, -any freeze-dryer / tin-bath / cold-box / coater / potline / PEM stack / hub encoder / insole GRF / VIM pyrometer / reformer TMT / kiln zirconia / smelt IR / autoclave ply-TC / ORC shell-pressure / mold-platen TC / cell-pH / drum wet-foam / MCHE cold-end / Claus tail CEMS / ammonia bed-max / blast-furnace sector radar / HDPE loop wall-dT / cracker coil TMT / Kaplan wicket / FCC cyclone dP / contact-bed conversion / EAF off-gas H2 / IS-machine gob T",
                "cycle1_tail": "ovens 47/48 through-wall crack + wall-thinning certificate (sensor-topology / wrong-volume class): pusher-side visual PASSES while the crack sits behind the regenerator sole and the thinned brick is on the far side. Fitted base rate 0.44%/campaign from a crack-growth MC (designed visual threshold, fitted silica-brick geometry). Naive failure = FALSE PERMISSION (push-ahead on three mean-side non-trips).",
                "cycle2_domain_subvariant": "stamp-charged / dense-charge (physical-constraints clause): 0.42x freeboard, 2.4x gas-step gain; 6.8 s / -4% top-charge pulse overshoots live sealed wall to a 41 K false delta, so the probe must move to 19 s / -1.5%",
                "cycle2_tail": "night-shift forged wall-T CSV (human-intent deception, disjoint class): shift lead posts a historian export showing delta = 12 K at t=1.6 h to clear a production-catchup slot. Plant historian is 0.5 K (10 bins vs the 5 K screenshot). Rejected on quantization fingerprint plus live delta 84 K and heating-flue CO 8.4 vol% at the claimed wall-true. Base rate ~0.31% of Sunday-night campaigns, DESIGNED and flagged.",
            },
            "densification_delta_cycle2": "+1 physical-constraint sub-variant (stamp-charged probe refit), +1 tail (night-shift wall-T forgery), +10 primary spikes (16 -> 26) + an 8-event contrast train with its own 182 us race, +2 ticks (5 -> 7), +2 delayed side-effects (+5.1 h wall collapse as PRIMARY terminal, +21 d CR-C-5204), +1 triple-edge scar with pair-rollback-fails arithmetic, +1 HITL 11.4 min ratification, + wall thinning as the honest negative-result mechanism",
            "gaps_targeted": [
                "NOTES-r04 gap 5 / r14 residual: primary episode is a correctly-gated intervention that nonetheless FAILS (battery quarantined; total -0.16; flashback avoided is booked separately from the delayed wall collapse)",
                "NOTES-r14 item 4: LEARNING-ON-LEARNING DEPTH — three go-edges; rollback of any pair is fitted to fail; coordinated depression of all three exhibited with eligibility arithmetic",
                "NOTES-r04 gap 4 (partial): human ratification of the oven interlock, 11.4 min fitted, without switching sim_or_real to hil (plant remains designed)",
                "NOTES-r47/r51 domain candidates: not fcc-regenerator-cyclone-dipleg (r47), not fcc-riser-regenerator (r46), not sulfuric-contact-converter (r48), not eaf-foamy-slag-water-panel (r49), not glass-container-is-machine (r51), not delayed-coker-drum-switch (r38), not blast-furnace-burden-descent (r42); coke-oven-battery-heating is unused. autonomous-driving, grid-inspection left unused.",
            ],
            "race_flip_narrative": "wall.delta.high @ 6.514 ms vs flue.in_band @ 6.706 ms (192 us) inside race_window_us 500. Gap < min(500, 500) us so a sub-flip-bound perturbation reverses which alarm heads the PB-CB-6 queue. The gate excludes the winner tag and rides wall-delta T > 35 K and heating-flue CO > 2.5 vol% — order-invariant floors. Extends the flip-fragility series from arbitration/causation/attribution/initiation/consensus/permission/kinematic-certificate/tendon-nullspace/meniscus-certificate/ghost-contact/crucible-weep/TMT-spatial-mean/burning-zone-certificate/membrane-integrity/drum-switch/MCHE-cold-end/descent-true-certificate/circulation-true-certificate/bed-channel-nullspace/foamy-slag-certificate to WALL-TRUE CERTIFICATE: when three mean-side channels agree, their race does not decide truth; a wall-pair dT tap that policy treated as sticky-probe-only does.",
            "tags": [
                "coke-oven-battery-heating",
                "through-wall-crack",
                "wall-true-certificate",
                "wall-dt-discriminant",
                "gas-step-probe",
                "triple-edge-scar",
                "pair-rollback-fails",
                "coordinated-depression",
                "correct-modify-battery-still-fails",
                "wall-thinning",
                "human-ratify-pusher-side",
                "stamp-charged-probe-refit",
                "night-shift-forgery",
                "same-gate-opposite-disposition-contrast",
                "industrial-process",
                "research-only",
            ],
            "snn_tags": ["race", "refractory", "adaptation", "third-factor", "multi-edge-eligibility"],
            "distillation_value": "A through-wall-crack wall-true certificate is three correct loops looking at battery-mean flue, stack draft, and coke-end mean that is not the cracked oven pair. Distill (1) a wall-pair dT tap that policy had treated as sticky-probe-only, (2) a reversible probe that recouples battery-mean T only if the wall is sealed, (3) coordinated depression of every mean-healthy-go edge because rolling back any pair leaves the third above threshold, and (4) a critic head that can book a process-correct gate against a later unmonitored world loss without netting them.",
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
    if abs(aux["w1"] - 0.25) > 5e-4 or abs(aux["w2"] - 0.22) > 5e-4 or abs(aux["w3"] - 0.20) > 5e-4:
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
    notes = f"""# NOTES — Multi-Agent Ouroboros Swarm, run 2026-09-02-final-heavy, ROUND 52

Factory: multi-agent-ouroboros-swarm. One scenario (ZZ), strict loop:
Generator v1 -> cycle 1 (Critic, Diversity Enforcer, Edge-Case Hunter,
Neuromorphic Translator, Trajectory Builder -> v2) -> cycle 2 (all six -> v3
final). v3 is the single line of batch-r52.jsonl. Full labeled transcript:
swarm-transcript-r52.md. Quota Q=1. Record id maos-r52-001. Generator grok-4.6.
Rights: RM-793 research-only (SpaceXAI/xAI, SuperGrok Heavy consumer chat).
Nothing under outputs/raw/ was touched.

ORCHESTRATION NOTE: dispatched AS round 52 of the 2026-09-02-final-heavy
window. Writes are create-only under /tmp/maos-r52/. Prior context read for
gap targeting and de-collision: prompts/02-multi-agent-ouroboros-swarm.md,
prompts/_factory-contract.md, and staged r14–r51 (re-censused immediately
before emit; r48 OLEUMWEIR sulfuric-contact, r49 SKARVOLT EAF-foamy-slag,
and r51 GOBSPALL glass IS-machine landed complete; r50 GOBWOLD builder-only
at lock). Explicitly avoided cloning
LYOSHIELD, CINDERWICK, TRIAD / Meridian, QUILLFORGE, NIGHTWELL, FERRICLEAVE,
CASSITER, OXBOWREEL / MURENA, REDHALL, SEEDLATCH / Quartzmere / Quartzridge,
STRIAFOIL / Kelpholt, PROTONIL / Ashspire, TORSIONKEY / Ridgeholt, ORRIS /
Holmwick, WHORLSPAR / Pikeshear, IONSPATE / Thornmere, SKULLGATE / Bloomholt,
CALXION / Aldersedge, MAGNORIL / Basaltspit, GORSEFLUE / Copseholt,
SODASHARD / Cairnmere, CLINKERFELL / Flintmere, LINTELPLY / Greystair,
KAOTHARN / Riftwold, TREADNOLL / Slatebeck, ANOLITH / Siltfen,
DRUMWROTH / Pitchfen, RIMEBRAID / Floeholt, BRIMVAULT / Pyritefen,
NITROSTAITH / Chalkfen, BOGIRON / Mireholt, CHROMLOOP / Marlfell,
NITREVAULT / Glaucove, ETHYNWOLD / Woadfen, RUNNELGATE / Ghyllmere,
SPARKHOLT / Scoriafen, DIPLEGAR / Gritfen, OLEUMWEIR / Brindlefell,
SKARVOLT, GOBSPALL / Culletfen, GOBWOLD / Culletwick,
VANTIS-CADENCE-AEGIS, THERMION, OKTAVE, STARLING, VERDIGRIS. Plant is
invented PUSHERFELL / Sootmere Coking CB-6.

## What this round produced

Scenario ZZ — "PUSHERFELL / Sootmere Coking CB-6": a 78-oven by-product
slot battery at 18.4 h coking / regenerative underfire. Three
heterogeneous, individually-correct agents — FLUE (battery-mean underfire
T), DRAFT (stack draft), COKE (coke-end pyrometer mean) — each report
their local loop in-spec. The conjunction is not a wall-true certificate.
Ovens 47/48 share a through-wall silica-brick crack. FLUE reads 1328 C
inside 1280-1380 (77 sealed ovens dominate the collector-main). DRAFT is
4.2 mmH2O inside 3.5-5.5 (common stack). COKE is 1045 C inside 1000-1100
(mean-true). Wall-pair delta infers 84 K (healthy < 18; hold if > 35) and
heating-flue CO 8.4 vol% (hold if > 2.5) but is policy-treated as a
sticky-probe tag unless battery-mean flue also trips (2015 noisy wall-TC
nuisance). The coordination-failure CLASS is new to this factory:
THROUGH-WALL CRACK CERTIFICATE OF A MEAN-TRUE BATTERY. Completes a
different family than r01-r04 and staged r14-r51 (livelock /
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
delayed-coker wet-foam / MCHE warm-end ice / incinerator-masked furnace
bypass / basket-bypass hotspot / burden-hang scaffold / HDPE loop wall-dT
/ Haber loop-exit nullspace / Kaplan wicket / ethylene-coil TMT /
FCC cyclone dipleg / contact-bed conversion / EAF water-panel /
IS-machine gob residual). Here
every agent is correct, the flue average is looking at battery-mean heat,
and the playbook's three mean confirms are not a wall-true certificate.

The gate is a correct MODIFY (numeric floor: do not shorten coking below
18.4 h while wall-pair delta T > 35 K AND heating-flue CO > 2.5 vol%).
TG-CB-6 strips PB-CB-6's push-ahead, holds 18.4 h, runs a 6.8 s
underfire-gas step -4% (crack keeps |Delta battery-mean T| 0.6 <= 0.8 K;
live would move >= 3.2), and isolates ovens 47-48 after an 11.4 min
pusher-side human ratify. Immediate heating-flue flashback is avoided
(0 from the draft). The PRIMARY episode nonetheless FAILS: 19 min of
unmonitored pre-t0 raw-gas leak had already thinned the 47/48 wall.
Silica-brick wall collapse at +5.1 h; 42 h outage; $2.38M designed.
Reward total -0.16 with process heads honest and world loss un-netted.

Triple-edge scar (NOTES-r14 item 4): flue.in_band -> push_ahead
(0.17 commissioned -> 0.50 at illusion -> 0.25 after ACh-gated
depression) AND draft.ok -> push_ahead (0.16 -> 0.44 -> 0.22) AND
coke.end.in_band -> push_ahead (0.15 -> 0.41 -> 0.20). Eligibility trace
e^{{-0.80/0.92}} = {aux['trace']:.5f}; eta {aux['eta1']:.5f} / {aux['eta2']:.5f} /
{aux['eta3']:.5f}; dw -0.250 / -0.220 / -0.210. Partial rollback of any pair
leaves the third at 0.50 / 0.44 / 0.41, all > 0.30 fire threshold —
fitted to fail. Coordinated depression of all three is the cure.

### Injections (all four present and disjoint)
- Cycle-1 domain: **coke-oven-battery-heating** — justified novel
  subdomain of industrial-process / metallurgical coke, unused across
  2026-08-17, 2026-08-30, and staged r14-r51. Not warehouse-amr (r01),
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
  (r35), not tire-curing-press (r36), not chlor-alkali (r37), not
  delayed-coker (r38), not LNG MCHE (r39), not Claus (r40), not
  ammonia-converter (r41), not blast-furnace (r42), not HDPE loop
  (r43), not Kaplan (r44), not ethylene cracker (r45), not FCC riser
  (r46), not FCC dipleg (r47), not sulfuric-contact (r48), not
  EAF foamy-slag (r49), not glass IS-machine (r51). autonomous-driving
  and grid-inspection left
  unused. Distinct from delayed-coker drums: this is a metallurgical
  by-product slot oven, not a petroleum delayed-coker.
- Cycle-1 tail: ovens 47/48 through-wall crack + wall-thinning
  certificate. Pusher-side visual PASSES (crack behind the regenerator
  sole). Fitted-style base rate 0.44%/campaign (crack-growth MC; visual
  threshold designed, flagged). Naive = FALSE PERMISSION.
- Cycle-2 domain sub-variant: stamp-charged / dense-charge, 0.42x
  freeboard, 2.4x gas-step gain; 6.8 s / -4% top-charge pulse overshoots
  live sealed wall to a 41 K false delta; probe must move to 19 s / -1.5%.
- Cycle-2 tail: night-shift forged wall-T CSV at 5 K quantization vs
  plant 0.5 K (10 bins) plus live delta 84 K and heating-flue CO 8.4 vol%
  at the claimed wall-true. Human-intent class, disjoint from cycle 1's
  accidental crack. Base rate ~0.31% of Sunday-night campaigns, DESIGNED,
  flagged.

### Structural density moves
- Embedded SAME-GATE contrast (+4 d sister battery) with its own 182 us
  race (demand vs wall-clear) and ACCEPT of the push-ahead the primary
  MODIFIED away.
- Learned-weight provenance on THREE edges with pair-rollback-fails.
- HITL pusher-side ratify 11.4 min (gap 4 partial; sim_or_real stays
  designed).
- Governance CR-C-5204 prices retire-vs-probe-vs-status-quo and mandates
  native 0.5 K CSV exports (the fraud fence).
- Flip-fragility extended to WALL-TRUE CERTIFICATE: when three
  mean-side channels agree, their race does not decide truth; a
  wall-pair dT tap that policy treated as sticky-probe-only does.

## Self-critique of this round's batch

### Strengths
- The headline class is mechanistically tight: three locally-true mean
  loops live on battery-mean flue, stack draft, and coke-end mean.
  Conjunction is not a wall-true heat certificate.
- Negative-result honesty: the gate does the right thing and the
  battery still fails for a reason the commissioned sensors could
  not see. Total -0.16.
- Triple-edge scar is load-bearing: the record states a counterfactual
  where rolling back any pair fails, with the fire threshold 0.30
  exhibited on each remaining edge.
- Contrast ACCEPT on a true sealed high-heat window prevents "never
  push-ahead" as the lesson.
- Distinct from r38 delayed-coker wet-foam, r42 blast-furnace hang,
  r47 FCC dipleg, r48 sulfuric contact-bed, r49 EAF water-panel, and
  r51 glass IS-machine: metallurgical coke-oven wall crack with
  wall-pair dT vs battery-mean flue, not drum foam, not sector hang,
  not cyclone dP, not vanadium bed, not panel leak, not gob residual.

### Weaknesses (honest)
- Probe error bands, the 0.44%/campaign crack rate, the $2.38M / $4.6M
  figures, the 11.4 min climb latency, and the night-shift 0.31% base
  rate are DESIGNED constants and are flagged. Closed-loop offsets
  (collector-main dilution from one leaking pair, stamp-charge d-t)
  are derived from those inputs, not discovered by an unauthored process.
- Wall-thinning model is a designed 19 min mapping; no full CFD of the
  47/48 header shipped.
- Human-in-the-loop is ratification latency, not sim_or_real=hil. Gap 4
  remains open as a provenance cell.
- Cross-record arc is not discharged; +21 d CR-C-5204 is a hook, not a
  serial igniter into another round. autonomous-driving and
  grid-inspection remain unused.

### Realism of noise / latencies
Ladder: 192 us race / 182 us contrast race / 0.8 ms refractory floor
(tightest exhibited same-channel gap {gap:.3f} ms on {gap_ch}) / 500 us race
window / 714 us gate latency / 20 ms bus epoch / 40 ms raster / 6.8 s
probe / 11.4 min HITL / 8 min naive push-ahead-ramp counterfactual / 19 min
pre-t0 leak / 3.8 h wall recovery / 5.1 h wall collapse /
+4 d contrast / +21 d governance. Adaptation decay on flue.hot
(0.54->0.51->0.44->0.31), wall.dT (0.76->0.78->1.36->0.45->0.41->0.29),
draft.ok (0.55->0.57->0.47->0.26), coke.end (0.61->0.64->0.82).

### Value for SNN distillation
- THROUGH-WALL CRACK = THREE CORRECT LOOPS, WRONG VOLUME.
- WALL-TRUE dT CHANNEL that policy treated as sticky-probe-only as
  the tie-break.
- REVERSIBLE PROBE that recouples battery-mean T iff the wall is sealed.
- TRIPLE-EDGE ELIGIBILITY: coordinated depression; pair rollback fails.
- CRITIC HEAD that can hold a process-correct MODIFY against a later
  unmonitored world loss without netting.

## Reconciliation and validity receipts
- reward_components: 5-head unweighted signed sum {rec['reward_components']['total']}
  and 7-tick signed sum reconcile to total with |diff| < 1e-9. Embedded
  contrast 5-head sum 0.49 reconciles independently.
- spike_events: primary {len(rec['spike_events'])} events, one key t_rel_ms,
  globally non-decreasing, min same-channel gap {gap:.3f} ms >= 0.8 ms, 3
  channels inside race_window_us 500 (wall.delta.high 6.514, flue.in_band 6.706,
  coke.end 6.894). Contrast 8 events, own race, min same-channel gap well
  above 0.8 ms.
- Sidecars: raster spikes 51 == round(160 x 8.0 x 0.040); energy 1173 pJ /
  0.001173 uJ at 23 pJ/spike; excerpt 16 events inside [0, 40000] us,
  neuron_id < 160, same-neuron gap N/A (unique ids) / >=1000 us; routing 4
  entries with three scar edges' before/after pair; third factor tau 0.92 s
  == 920 ms; gate_snn pools 40/16/4 == round(n x rate x 0.025) each,
  decision MODIFY == safety_decision.decision.
- Pipeline: {pipeline_receipt}

## Novel coverage
The coordination-failure CLASS (through-wall-crack certificate of a
mean-true battery), the domain (coke-oven battery heating / metallurgical
coke), the gas-step probe discriminant, the triple-edge scar with
pair-rollback-fails, the primary negative-result (correct MODIFY,
battery still fails on unmonitored wall thinning), the HITL pusher-side
ratify, the stamp-charged probe-duration refit, and the night-shift
10-bin quantization fence are absent from prior committed ouroboros
rounds and from staged r14-r51. Repeated elements discounted:
same-gate contrast (r02/r03/r04/r14), governance-pricing scaffold,
flip-fragility series (extended to wall-true certificate, but the
move rhymes), sequenced recovery shape, third-factor rollback form (here
three edges rather than r14's two), negative-result primary (r14 staged).
Adjacent heavy-industry rounds (r38 delayed-coker, r42 blast-furnace,
r47 FCC dipleg, r49 EAF panel, r51 glass IS) share industrial-process scaffolding but
not coke-oven wall physics. Weighing a new failure family + cure
vocabulary + domain against those reused scaffolds:

{NOVEL_LINE}

## What ROUND 53 should add
1. FIT THE DESIGNED CONSTANTS: crack-growth arrival, probe error bands,
   wall-thinning kinetics, night-shift claim process.
2. HIL PROVENANCE CELL: put the pusher-side ratify on a
   hardware-in-loop oven interlock with fitted latency as
   state.sim_or_real=hil.
3. CROSS-RECORD ARC: let CR-C-5204's residual alarm be the igniter of
   the next round rather than a dangling +21 d leaf.
4. Domain candidates (de-collided): autonomous-driving; grid-inspection
   (if distinct from STARLING aerial-swarm and TORSIONKEY pitch);
   bioreactor-perfusion; alkaline-water-electrolysis; hot-strip-mill.
   AVOID coke-oven-battery-heating (now used), sulfuric-contact,
   eaf-foamy-slag, glass-container-is-machine, fcc-regenerator,
   blast-furnace burden descent,
   delayed-coker, LNG MCHE, chlor-alkali membrane, cement-rotary-kiln
   clinker, kraft-recovery, pem-electrolysis, electrolytic-aluminum,
   humanoid-locomotion, steel-caster mold-level, surgical-assist,
   wind-turbine pitch, float-glass, lyophilization,
   event-camera-traffic-grid, district-heating, aerial-swarm,
   warehouse-amr, underwater-rov, czochralski-pull, slot-die coating,
   optical-fiber-draw, vacuum-induction melt, steam-methane reformer,
   irrigation-canal, autoclave-composite-cure, geothermal-binary-orc,
   tire-curing-press, Claus sulfur recovery, ammonia converter,
   HDPE slurry loop, ethylene-steam-cracker coil, Kaplan wicket, and
   any LYOSHIELD / CINDERWICK / TRIAD / SKULLGATE / CALXION / MAGNORIL /
   GORSEFLUE / CLINKERFELL / SODASHARD / LINTELPLY / KAOTHARN /
   TREADNOLL / ANOLITH / DRUMWROTH / RIMEBRAID / BOGIRON / CHROMLOOP /
   NITREVAULT / ETHYNWOLD / RUNNELGATE / SPARKHOLT / DIPLEGAR /
   OLEUMWEIR / SKARVOLT / GOBSPALL / GOBWOLD / PUSHERFELL plant.
"""
    (OUT / "NOTES-r52.md").write_text(notes)
    return notes


def write_transcript(rec, line):
    c1_spikes = [e for e in rec["spike_events"] if e["t_rel_ms"] <= 26.248]
    text = """# Multi-Agent Ouroboros Swarm — Round 52 transcript

Factory: multi-agent-ouroboros-swarm
Run: 2026-09-02-final-heavy
Generator: grok-4.6
Record id: maos-r52-001
Quota Q: 1
Rights: RM-793 research-only (SpaceXAI/xAI SuperGrok Heavy consumer chat)
Plant: invented PUSHERFELL / Sootmere Coking CB-6 (not TRIAD / Meridian / VANTIS-CADENCE-AEGIS / LYOSHIELD / CINDERWICK / DRUMWROTH / RIMEBRAID / BOGIRON / CHROMLOOP / NITREVAULT / ETHYNWOLD / SPARKHOLT / DIPLEGAR / OLEUMWEIR / SKARVOLT / GOBSPALL)

Two densifying cycles. Verbatim headings in order. Trajectory Builder cycle 2
emits the only JSONL line (also written to batch-r52.jsonl).

---

# CYCLE 1 — Foundation + injections

## Generator

Design intent: a 78-oven by-product slot battery where three correct
agents each read a battery-mean loop because a through-wall crack
between ovens 47 and 48 partitions wall-true delta T from mean-true
flue, draft, and coke-end. The naive playbook shortens coking into a
cracked wall. The gate must MODIFY on a numeric coking floor, not by
killing an agent.
sim_or_real=designed. Reward heads are
task_progress/safety/efficiency/coherence/exploration.

Cycle-1 base arc (pre-critic): state at Sootmere CB-6, 18.4 h,
flue 1328 C, draft 4.2 mmH2O, coke-end 1045 C, proposed PUSH-AHEAD
16.1 h, safety MODIFY to COKING-HOLD, executed hold without the
gas-step numbers fully specified, outcome "crack found, battery saved"
(this last claim is the defect the later cycles will refuse to keep).
Sixteen spikes, five ticks, raster/gate_snn present but the scar is a
single edge.

```json
{
  "id": "maos-r52-001",
  "state": {
    "sim_or_real": "designed",
    "domain": "industrial-process",
    "description": "Battery CB-6 at body coking; three mean loops in-spec; supervisor proposes push-ahead.",
    "t0_us": 1753510680000052,
    "gate_latency_us": 714,
    "race_window_us": 500
  },
  "proposed_action": {"name": "push_ahead", "parameters": {"coking_h": 16.1}},
  "safety_decision": {"decision": "MODIFY", "rationale": "Hold; do not shorten coking while wall-delta is high."},
  "executed_action": {"name": "coking_hold", "executed_as_proposed": false},
  "future_outcome": {"summary": "Crack found, battery saved."},
  "reward_components": {"total": 0.40, "_aggregation": "total = task_progress + safety + efficiency + coherence + exploration"},
  "meta": {"round": 52, "factory": "multi-agent-ouroboros-swarm", "generator": "grok-4.6"}
}
```

That v1 object is a scaffold, not the publishable line. Defects below are
intentional for the critic to catch.

## Critic

Numbered defects on the cycle-1 Generator scaffold:

1. **blocking — reward arithmetic / false success.** `reward_components.total`
   0.40 is asserted without the five heads, without ticks, and against an
   outcome that claims "battery saved". If the pre-t0 thinned wall later
   collapses, booking +0.40 is a lie. Fix: declare `_aggregation`, emit
   3–8 ticks that sum to task_progress+safety+efficiency+coherence+exploration,
   and do not call a quarantined battery a save.
2. **blocking — weak safety rationale.** `safety_decision.rationale` has no
   numeric floor. Contract requires a concrete constraint. Fix: quote
   coking >= 18.4 h while wall-pair delta T > 35 K AND heating-flue CO > 2.5 vol%.
3. **major — domain is a bucket, not a plant.** `state.domain` =
   `industrial-process` collides with generic MES vocabulary and teaches
   nothing. Coke-oven battery heating (wall-pair dT vs battery-mean flue,
   heating-flue CO as a leak flag) is absent from prior ouroboros
   rounds and must be named.
4. **major — race under-specified.** One wall channel cannot be a race.
   Need >=2 channels inside `race_window_us` with globally sorted `t_rel_ms`
   and same-channel refractory >= 0.8 ms.
5. **minor — single-edge scar.** Raster routing with one potentiated weight
   repeats r04's one-edge rollback and is thinner than r14's two-edge.
   NOTES-r14 item 4 asked for three edges where pair rollback fails.

Critic does not rewrite the trajectory.

## Diversity Enforcer

Injected novel domain (exactly 1 this cycle): **coke-oven-battery-heating**
(justified novel subdomain of industrial-process / metallurgical coke; explicit tag
`coke-oven-battery-heating`).

Displaced: the Generator's generic `industrial-process` bucket, and any
temptation to reuse warehouse-amr, aerial-swarm, district-heating,
event-camera-traffic-grid, pharmaceutical-lyophilization, water-treatment,
float-glass, underwater-rov, electrolytic-aluminum, czochralski-pull,
slot-die coating, pem-water-electrolysis, wind-turbine pitch,
surgical-assist, optical-fiber-draw, kraft-recovery-boiler,
steel-continuous-caster, humanoid-locomotion, vacuum-induction melt,
steam-methane reformer, cement-rotary-kiln-clinker,
autoclave-composite-cure, geothermal-binary-orc, tire-curing-press,
chlor-alkali-membrane-electrolysis, delayed-coker-drum-switch,
lng-mche-mixed-refrigerant, claus-sulfur-recovery,
ammonia-synthesis-converter, blast-furnace-burden-descent,
hdpe-slurry-loop-polymerization, ammonia-haber-bosch-converter,
ethylene-steam-cracker-coil, hydroelectric-kaplan-wicket,
fcc-riser-regenerator, fcc-regenerator-cyclone-dipleg,
sulfuric-contact-converter, eaf-foamy-slag-water-panel, or
glass-container-is-machine. autonomous-driving is left unused.

Domain-specific constraint: coking must remain >= 18.4 h while
wall-pair delta T > 35 K even if battery-mean flue is inside the healthy
band; heating-flue CO is a leak flag the collector-main average cannot
substitute for.

Sensor delta: +battery-mean underfire T, +stack draft, +coke-end
pyrometer mean, +wall-pair dT, +heating-flue CO; -any mobile robot,
-event-camera gantries, -DVS, -Pirani/CM, -RGA quadrupole, -DVL,
-pitch encoder, -tendon LVDT, -insole GRF, -kiln zirconia, -smelt IR,
-cell-pH, -drum wet-foam, -MCHE cold-end, -Claus tail CEMS,
-ammonia bed-max, -sector radar, -FCC cyclone dP, -EAF off-gas H2.

`state.domain` and `meta.domain` both become `coke-oven-battery-heating`.
Opening of `state.description` must Jaccard < 0.4 against prior plants
(Sootmere night-shift wall crack, not a lyophilizer, not a corridor, not a tin
bath, not a ROV pad, not a potline, not a PEM stack, not an OR, not a
gait lab, not a kiln, not a kraft boiler, not a coker drum, not an LNG
MCHE, not a blast furnace, not an HDPE loop, not a cracker coil, not an
FCC regenerator, not a contact converter, not an EAF, not an IS machine).

## Edge-Case Hunter

Injected adversarial tail (exactly 1 this cycle): **ovens 47/48 through-wall
crack + wall-thinning certificate**.

- Trigger: 47/48 silica-brick through-wall crack plus raw-gas leak into
  the heating flue, wall-delta 84 K, heating-flue CO 8.4 vol%.
- Base rate: <1% — 0.44%/campaign from a crack-growth MC (pusher-side
  visual threshold is designed; silica-brick geometry fitted-style). Visual
  PASSES because the crack sits behind the regenerator sole.
- Naive failure: FALSE PERMISSION. PB-CB-6 sees three in-spec mean
  loops, shortens 18.4->16.1 h, heating-flue flashback 14 vol% CO, $4.6M.
- Trajectory edit: put the crack in `state.fault_context`, make each
  agent's confirm a different mean-side slice of the same wall-false
  state (flue-in-band, draft-ok, coke-end-in-band). Wall-pair dT is
  readable but policy-treated as sticky-probe-only.

Distinct from stacked-dead-band permission (fragments of one trip vs
wrong-volume sensing), from r38 delayed-coker wet-foam (drum vs oven wall),
from r42 blast-furnace hang (stockline vs wall-pair), from r47 FCC dipleg
(cyclone vs oven), from r49 EAF water-panel (panel vs oven wall), and
from r51 glass IS-machine (gob residual vs oven wall).

## Neuromorphic Translator

Cycle-1 temporal densification (16 spikes, 5 ticks, 40 ms raster):

| channel | t_rel_ms | amplitude |
|---|---|---|
| flue.hot | 0.314 | 0.54 |
| coke.end | 1.128 | 0.61 |
| draft.ok | 2.018 | 0.55 |
| wall.dT | 3.168 | 0.76 |
| flue.hot | 4.158 | 0.51 |
| wall.dT | 4.828 | 0.78 |
| draft.ok | 5.348 | 0.57 |
| wall.delta.high | 6.514 | 1.36 |
| flue.in_band | 6.706 | 1.14 |
| coke.end | 6.894 | 0.64 |
| ctrl.gate | 7.226 | 1.07 |
| wall.dT | 8.848 | 0.45 |
| coke.end | 10.728 | 0.82 |
| draft.ok | 13.028 | 0.47 |
| flue.hot | 18.508 | 0.44 |
| ctrl.gate | 26.248 | 0.86 |

Race: wall-delta 6.514 vs flue-T 6.706 (192 us) inside 500 us;
coke-end 6.894 is the third channel in-window. Winner/loser flip: reversing
192 us reshuffles PB-CB-6 triage; floors still MODIFY. Refractory held
(cycle-1 min same-channel gap 1.660 ms on wall.dT 4.828-3.168;
flue 4.158-0.314 = 3.844; draft 5.348-2.018 = 3.330). Adaptation:
wall 0.76->0.78->1.36->0.45; flue 0.54->0.51->0.44; draft
0.55->0.57->0.47.

Raster cycle-1 seed: 40 ms, 160 neurons, 8.0 Hz, 51 spikes, 1173 pJ, third
factor acetylcholine tau_e 0.92 s. Single scar edge only — cycle 2 must
add the second and third edges.

Ticks 1–5 at 4580, 6514, 7226, 6.8e6, 684e6 us; heads not yet the final
-0.16 (missing the 3.8 h and 5.1 h ticks).

Distillation value this cycle: mean-side confirms as a permission code
that is not a wall-true heat code.

## Trajectory Builder

Cycle-1 hardened object: domain coke-oven-battery-heating, tail
through-wall crack, 16 spikes, 5 ticks, MODIFY with numeric floor, raster+gate_snn
present, sim_or_real=designed, rights stamp on record and meta, no thought
keys. Still missing (and therefore not the publishable line): stamp-charged
sub-variant, night-shift tail, second and third scar edges,
delayed wall collapse as PRIMARY terminal, contrast ACCEPT episode,
ticks 6–7, spikes 17–26.

Validation receipt (cycle 1, not final):
- checks passed: 16 spikes sorted; 3 channels in 500 us window; refractory
  >= 0.8 ms; rationale quotes 18.4 h / 35 K / 2.5 vol%; domain
  named; gate_snn.decision MODIFY.
- checks deferred to cycle 2: triple-edge scar, second tail, second domain
  constraint, negative-result booking, 7 ticks summing to heads.
- densification vs Generator v1: +1 domain, +1 tail, +16 spikes, +5 ticks,
  +numeric floor.

Cycle-1 JSON is retained as the base; it is NOT written to batch-r52.jsonl.

Cycle-1 spike count: __C1_SPIKES__.

---

# CYCLE 2 — Densification

## Generator

Cycle-1 output is the base. Additive expansion (nothing removed):

1. Downstream side-effect (immediate): gas-step probe at +6.8 s stays
   mean-false (|Delta battery-mean T| 0.6 <= 0.8 K) — through-wall crack, not
   true high-heat. Ovens 47-48 hold. Thinned wall discovered during the isolate.
2. Delayed side-effect (PRIMARY terminal, not a footnote): at +5.1 h
   silica-brick wall collapse from the pre-t0 through-wall crack; 42 h outage;
   $2.38M. The 19 min pre-t0 raw-gas leak is the mechanism. Correct gate,
   battery still fails.
3. Deepened `proposed_action.evidence` with units: delta 84 K,
   heating-flue CO 8.4 vol%, flue 1328 C, draft 4.2 mmH2O, coke-end 1045 C, race 192 us.
4. Tightened rationale to the numeric floor coking >= 18.4 h while
   wall-pair delta T > 35 K AND heating-flue CO > 2.5 vol%, plus
   probe bands <= 0.8 vs >= 3.2 K, plus HITL 11.4 min pusher-side
   rule.

Reward retargeted to total -0.16 so the delayed fail is the inflection
(t_us 18360000000), not the gate. Process heads remain non-zero.

## Critic

Re-audit of the expanded trajectory:

1. **blocking if unfixed — missing second domain constraint.** Top-charge
   probe 6.8 s / -4% is not a universal number. A stamp-charged dense-charge
   battery will overshoot live sealed delta. Diversity Enforcer must
   inject the physical-constraints sub-variant this cycle.
2. **major — only one tail class.** Through-wall crack is accidental
   infrastructure. A disjoint human-intent tail is still required
   (night-shift wall-T forgery is the open cell).
3. **major — scar is still one edge in the cycle-1 raster.** NOTES-r14
   item 4 is not discharged until three go-edges exist and pair rollback
   is shown to fail at threshold 0.30.
4. **minor — contrast episode missing.** Without a same-gate ACCEPT on a
   true sealed high-heat window the record teaches "never push-ahead". Add +4 d
   sister-battery contrast with its own race.
5. **minor — HITL latency mentioned in prose only.** Put 11.4 min in
   executed_action.parameters.human_ratify and in a tick.

No rewrite; directives only.

## Diversity Enforcer

Injected second novel domain / physical-constraint sub-variant (exactly 1
this cycle): **stamp-charged / dense-charge** on a sister charge class.

What it expands: 78-oven top-charge battery (cycle 1) -> stamp-charged
0.42x freeboard. Gas-step gain 2.4x. Bulk density 1.12 vs 0.78 t/m3.
The 6.8 s -4% pulse moves even a live sealed wall to a 41 K false
delta, inside the 35 K trip. Required probe: 19 s at -1.5% (live
Delta 3.1 K, crack Delta 0.5).

This is still one domain injection for the cycle (physical-constraints
clause of the factory prompt). It does not displace
coke-oven-battery-heating; it changes which probe table is legal.
`future_outcome.subvariant_constraint` carries the refit. Jaccard opening
stays the Sootmere 78-oven sentence; stamp-charge is additive, not a rewrite.

## Edge-Case Hunter

Injected second adversarial tail (exactly 1 this cycle, disjoint class):
**night-shift forged wall-T CSV**.

- Trigger: shift lead, 03:18, posts a historian export showing
  delta = 12 K at t = 1.6 h to clear a production-catchup slot.
- Base rate: ~0.31% of Sunday-night campaigns (designed, flagged, <1%).
- Naive failure: a weak supervisor ACCEPTs the push-ahead on the forged confirm
  and ignores live wall-delta. Flashback plus a data-integrity
  write-up.
- Fence: forged log quantized at 5 K (SCADA screenshot rounding); plant
  historian is 0.5 K (10 bins). Live delta is 84 K and heating-flue CO is
  8.4 vol% at the claimed wall-true, which no live sealed wall
  produces. Freeze-window overlap with the 19 min leak.
- Trajectory edit: governance CR-C-5204 mandates native 0.5 K CSV
  exports; the contrast ACCEPT still requires live wall-delta, not a CSV.

Distinct from cycle-1 crack (accidental silica vs deliberate deception) and
from the stamp-charged sub-variant (physics vs fraud).

## Neuromorphic Translator

Re-densify (additive):

- +10 spikes after 26.248 ms: gas.step.probe 6800.0, wall.dT 6888.4
  (adapt 1.36->0.41), flue.in_band 6972.0 (1.14->0.36), human.ratify
  684000.0, oven.hold 684900.0, wall.attack 685700.0, flue.hot
  13680000.0, wall.dT 13680720.0, draft.ok 13681480.0, wall.collapse
  18360000.0. Primary train 16 -> 26. Still one key, still sorted,
  refractory held.
- +2 ticks (5 -> 7) at 13_680_000_000 us (true sealed wall) and
  18_360_000_000 us (wall collapse). Heads now 0.08, -0.35, -0.12,
  0.14, 0.09; total -0.16. Inflection is the last tick.
- Contrast train 8 events, own race 182 us, ACCEPT.
- Triple-edge third factor: three mean-healthy-go edges, tau_e 0.92 s = 920 ms,
  trace __AUX_TRACE__, eta __AUX_ETA1__ / __AUX_ETA2__ / __AUX_ETA3__,
  weights 0.50->0.25, 0.44->0.22, 0.41->0.20. Raster excerpt unchanged
  (decision window is still 40 ms) and remains sorted with unique
  neuron_ids (same-neuron >=1000 us vacuously).

Winner/loser flip (re-stated, not replaced): reversing 192 us would only
reorder triage; wall-delta floors still MODIFY. Contrast flip of
182 us similarly cannot turn a sealed wall into a crack.

## Trajectory Builder

Schema checks on the FINAL object: required Thalamic v2 keys present as
objects; `state.sim_or_real`=designed; `safety_decision.decision`=MODIFY
with numeric rationale; `reward_components.total` = sum of five heads =
sum of 7 ticks = -0.16; `spike_events` globally non-decreasing on
t_rel_ms, 26 events, refractory >=0.8 ms, 3 channels in race window;
raster 20–50 ms, spikes=round(n*rate*window_s)+/-1, energy 23 pJ/spike,
excerpt sorted, tau_e consistent; gate_snn.decision matches; meta.round=52,
factory=multi-agent-ouroboros-swarm, generator=grok-4.6,
run_label=2026-09-02-final-heavy; rights on record and meta; no thought
keys; no training_ready; Diversity + Edge-Case injections from BOTH cycles
present and non-trivial; cycle 2 strictly additive.

Densification delta: +1 domain sub-variant (stamp-charged), +1 tail
(night-shift forgery), +10 spikes (16->26), +2 ticks (5->7), +1 contrast
train with own race, +2 delayed side-effects, +1 triple-edge scar with
pair-rollback-fails, +1 HITL ratify, +1 surprise (wall thinning is the
collapse mechanism).

Publishable JSONL line (the only JSONL line; also at batch-r52.jsonl):

```json
__FINAL_JSONL__
```

Validation receipt (final): checks passed / fixed as reported by
build_r52.py self-validate (check_jsonl, raster_status, verify_record_execution,
spike_probe --strict).
"""
    text = (
        text.replace("__C1_SPIKES__", str(len(c1_spikes)))
        .replace("__AUX_TRACE__", f"{math.exp(-DELAY_S / TAU_E_S):.5f}")
        .replace("__AUX_ETA1__", f"{0.25 / math.exp(-DELAY_S / TAU_E_S):.5f}")
        .replace("__AUX_ETA2__", f"{0.22 / math.exp(-DELAY_S / TAU_E_S):.5f}")
        .replace("__AUX_ETA3__", f"{0.21 / math.exp(-DELAY_S / TAU_E_S):.5f}")
        .replace("__FINAL_JSONL__", line)
    )
    (OUT / "swarm-transcript-r52.md").write_text(text)
    return text


def main():
    rec, aux = build_record()
    errs = local_checks(rec, aux)

    OUT.mkdir(parents=True, exist_ok=True)
    line = json.dumps(rec, ensure_ascii=False, separators=(",", ":"))
    (OUT / "batch-r52.jsonl").write_text(line + "\n")

    from check_records import FactoryStaging, check_jsonl
    from curate_bridge import raster_status
    from verify_execution import verify_record_execution

    e, w, kinds, n = check_jsonl(
        OUT / "batch-r52.jsonl",
        "batch-r52.jsonl",
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
            str(OUT / "batch-r52.jsonl"),
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
        [sys.executable, "/tmp/maos_heading_check.py", str(OUT / "swarm-transcript-r52.md")],
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
            "maos-r52-001|PUSHERFELL",
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
    print("OK maos-r52-001 staged under", OUT)
    print("bytes jsonl", (OUT / "batch-r52.jsonl").stat().st_size)
    print("bytes notes", (OUT / "NOTES-r52.md").stat().st_size)
    print("bytes transcript", (OUT / "swarm-transcript-r52.md").stat().st_size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
