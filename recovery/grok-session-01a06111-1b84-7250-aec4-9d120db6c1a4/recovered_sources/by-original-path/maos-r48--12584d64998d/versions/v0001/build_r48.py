#!/usr/bin/env python3
"""Build and self-check MAOS round-48 JSONL (research-only; not published)."""
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

GEN_AT = "2026-09-03T07:48:00Z"
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
OUT = Path("/tmp/maos-r48")
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
    "Yarrowmere",
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
    "NITROSTAITH",
    "Chalkfen",
    "NITREVAULT",
    "Glaucove",
    "ETHYNWOLD",
    "Woadfen",
    "CHROMLOOP",
    "Marlfell",
    "RUNNELGATE",
    "Ghyllmere",
    "SPARKHOLT",
    "Scoriafen",
    "DIPLEGAR",
    "Gritfen",
    "Cheniere",
    "Qatargas",
    "QatarEnergy",
    "Air Products",
    "APCI",
    "ConocoPhillips",
    "Bechtel",
    "Technip",
    "Baker Hughes",
    "ExxonMobil",
    "TotalEnergies",
    "Woodside",
    "Novatek",
    "Yamal",
    "Venture Global",
    "Sempra",
    "Freeport LNG",
    "Air Liquide",
    "Chart Industries",
    "LyondellBasell",
    "Hostalen",
    "Marlex",
    "Unipol",
    "Braskem",
    "Borealis",
    "SABIC",
    "Nova Chemicals",
    "Mitsui Chemicals",
    "UOP",
    "Valero",
    "Marathon",
    "MECS",
    "Monsanto",
    "DuPont",
    "Chemetics",
    "Outotec",
    "Metso",
    "Lurgi",
    "BASF",
    "Bayer",
    "Noram",
    "Enviro-Chem",
    "Yara",
    "Kellogg",
    "Casale",
    "KBR",
    "Haldor",
    "Topsoe",
    "Saipem",
    "Clariant",
    "Voith",
    "Andritz",
    "Litostroj",
    "Rainpower",
    "Gilkes",
)
R14_OPENING = (
    "Helixmere Biologics Building C lyophilizer LYO-4 is mid-primary on 8400 "
    "vials of a monoclonal antibody"
)
NOVEL_LINE = "Novel coverage: 46%"
PLANT = "OLEUMWEIR"
GEO = "Brindlefell"
CELL = "CT-5"
DOMAIN = "sulfuric-contact-converter"
RECORD_ID = "maos-r48-001"
ROUND = 48
PROBE_S = 6.8
TAU_E_S = 6.8
C1_SPIKE_CUTOFF_MS = 26.320


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
        if p.parent.name == "maos-r48":
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
        if p.parent.name == "maos-r48":
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
        if p.parent.name == "maos-r48":
            continue
        try:
            text = p.read_text()
        except OSError:
            continue
        if f'PLANT = "{PLANT}"' in text:
            hits.append(f"{p}: claimed PLANT {PLANT}")
        if f'DOMAIN = "{DOMAIN}"' in text:
            hits.append(f"{p}: claimed DOMAIN {DOMAIN}")
        if f'GEO = "{GEO}"' in text:
            hits.append(f"{p}: claimed GEO {GEO}")
    return hits


def build_record():
    ticks, heads = cents_ticks(
        [4680, 6712, 7400, 6_800_000, 576_000_000, 9_360_000_000, 12_960_000_000],
        [
            (1, -2, -1, 2, 1),
            (2, -5, -1, 3, 1),
            (1, -6, -2, 3, 2),
            (1, -6, -2, 2, 1),
            (1, -6, -2, 2, 2),
            (1, -5, -2, 2, 1),
            (0, -6, -2, 1, 1),
        ],
    )
    assert abs(heads["total"] - (-0.17)) < 1e-9, heads

    trace = math.exp(-PROBE_S / TAU_E_S)
    eta1 = 0.25 / trace
    eta2 = 0.22 / trace
    eta3 = 0.20 / trace
    dw1 = eta1 * 1.0 * trace
    dw2 = eta2 * 1.0 * trace
    dw3 = eta3 * 1.0 * trace
    w1 = 0.48 - dw1
    w2 = 0.43 - dw2
    w3 = 0.39 - dw3
    assert abs(w1 - 0.23) < 5e-4, w1
    assert abs(w2 - 0.21) < 5e-4, w2
    assert abs(w3 - 0.19) < 5e-4, w3

    spike_events = [
        {"channel": "bed.tc", "t_rel_ms": 0.280, "amplitude": 0.54},
        {"channel": "tmean.tt", "t_rel_ms": 1.120, "amplitude": 0.58},
        {"channel": "dp.pt", "t_rel_ms": 2.000, "amplitude": 0.56},
        {"channel": "cems.so2", "t_rel_ms": 3.220, "amplitude": 0.49},
        {"channel": "bed.tc", "t_rel_ms": 4.680, "amplitude": 0.72},
        {"channel": "tmean.tt", "t_rel_ms": 5.200, "amplitude": 0.61},
        {"channel": "dp.pt", "t_rel_ms": 5.640, "amplitude": 0.51},
        {"channel": "bed3.high", "t_rel_ms": 6.712, "amplitude": 1.31},
        {"channel": "tmean.ok", "t_rel_ms": 6.900, "amplitude": 1.11},
        {"channel": "r_hotspot", "t_rel_ms": 7.044, "amplitude": 0.68},
        {"channel": "ctrl.gate", "t_rel_ms": 7.400, "amplitude": 1.07},
        {"channel": "bed.tc", "t_rel_ms": 8.980, "amplitude": 0.44},
        {"channel": "tmean.tt", "t_rel_ms": 10.860, "amplitude": 0.45},
        {"channel": "bed.tc", "t_rel_ms": 12.780, "amplitude": 0.81},
        {"channel": "dp.pt", "t_rel_ms": 18.520, "amplitude": 0.42},
        {"channel": "ctrl.gate", "t_rel_ms": 26.320, "amplitude": 0.83},
        {"channel": "air.probe", "t_rel_ms": 6800.0, "amplitude": 0.94},
        {"channel": "bed.tc", "t_rel_ms": 6924.4, "amplitude": 0.38},
        {"channel": "tmean.ok", "t_rel_ms": 7018.2, "amplitude": 0.32},
        {"channel": "human.ratify", "t_rel_ms": 576000.0, "amplitude": 0.80},
        {"channel": "bed3.isolate", "t_rel_ms": 576800.0, "amplitude": 0.73},
        {"channel": "catalyst.survey", "t_rel_ms": 577400.0, "amplitude": 0.82},
        {"channel": "bed.tc", "t_rel_ms": 9360000.0, "amplitude": 0.27},
        {"channel": "tmean.tt", "t_rel_ms": 9360440.0, "amplitude": 0.25},
        {"channel": "dp.pt", "t_rel_ms": 9360900.0, "amplitude": 0.17},
        {"channel": "sinter.dump", "t_rel_ms": 12960000.0, "amplitude": 0.90},
    ]

    contrast_spikes = [
        {"channel": "raise.demand", "t_rel_ms": 0.000, "amplitude": 0.85},
        {"channel": "bed3.clear", "t_rel_ms": 0.188, "amplitude": 0.78},
        {"channel": "bed.tc", "t_rel_ms": 0.420, "amplitude": 0.24},
        {"channel": "tmean.tt", "t_rel_ms": 1.480, "amplitude": 0.41},
        {"channel": "dp.pt", "t_rel_ms": 4.920, "amplitude": 0.52},
        {"channel": "ctrl.gate", "t_rel_ms": 7.180, "amplitude": 0.91},
        {"channel": "air.probe", "t_rel_ms": 3200.0, "amplitude": 0.34},
        {"channel": "sinter.dump", "t_rel_ms": 12960000.0, "amplitude": 0.11},
    ]

    excerpt = [
        {"t_us": 280, "neuron_id": 11},
        {"t_us": 1120, "neuron_id": 50},
        {"t_us": 2000, "neuron_id": 90},
        {"t_us": 3220, "neuron_id": 104},
        {"t_us": 4680, "neuron_id": 7},
        {"t_us": 5200, "neuron_id": 56},
        {"t_us": 5640, "neuron_id": 98},
        {"t_us": 6712, "neuron_id": 4},
        {"t_us": 6900, "neuron_id": 62},
        {"t_us": 7044, "neuron_id": 19},
        {"t_us": 7400, "neuron_id": 132},
        {"t_us": 8980, "neuron_id": 22},
        {"t_us": 10860, "neuron_id": 68},
        {"t_us": 12780, "neuron_id": 15},
        {"t_us": 18520, "neuron_id": 110},
        {"t_us": 26320, "neuron_id": 140},
    ]

    rec = {
        "id": RECORD_ID,
        "title": "OLEUMWEIR CT-5: bed-3 conversion 0.28 beats tmean.ok by 188 us; correct MODIFY still dumps bed-3 after pre-t0 vanadium sinter",
        "rights": dict(RIGHTS),
        "state": {
            "sim_or_real": "designed",
            "domain": DOMAIN,
            "scenario_name": "OLEUMWEIR / Brindlefell Acid CT-5",
            "timestamp_local": "2026-08-23T02:48:00-05:00",
            "t0_us": 1786852800000048,
            "gate_latency_us": 688,
            "race_window_us": 500,
            "race_window_rel_ms": [6.712, 7.212],
            "description": "Brindlefell Acid contact hall CT-5 holds a 1400 tpd four-bed vanadium-pentoxide converter at 437 C converter-mean on 10.4 vol% furnace SO2. TMEAN weighted-bed temperature is 437 C against 420-455. DP converter shell is 18.4 mbar inside 14-24. CEMS oleum-absorber tail is 180 ppm inside a 250 ppm Sunday ceiling. Playbook PB-CT-11 treats the conjunction as permission to raise gas rate. The consensus is false: a bed-3 catalyst-screen tear has channeled SO2 around the remaining V2O5 for 18 min after a Sunday heat-soak because distributor 3 is 35 pct collapsed. Uncommissioned r_conv is 0.28 against a 0.78 hold. Uncommissioned r_hotspot is 598 C against a 530 hold. Bed-conversion-first latches RAISE-HOLD plus an air-step probe; tmean-ok-first would have authorized RAISE-GAS 1400 to 1800 tpd into a channeled bed.",
            "goal": "Hold gas rate at 1400 tpd without a catchup raise while r_conv < 0.78 AND r_hotspot > 530 C AND bed-3 remains unisolated; keep V2O5 sinter mass at 0 kg and oleum off-spec at 0 t.",
            "race": {
                "contenders": [
                    "bed3.high 0.28 conversion (bed-3 outlet GC vs 0.78 hold, uncommissioned)",
                    "tmean.ok 437 C (converter weighted-mean bed temperature inside 420-455 C)",
                ],
                "semantics": "Bed-conversion-first latches RAISE-HOLD + AIR-STEP-PROBE + bed-3 isolate. Tmean-ok-first latches RAISE-GAS (1400 to 1800 tpd into the channeled bed, no probe).",
                "window_derivation": "500 us = one 360 us bed-3 GC ADC slot plus 140 us converter-mean TT publish.",
                "order_evidence_note": "Margin 188 us vs combined jitter 60 us (bed 32 + tmean 28): 3.13x. The 188 us gap sits inside min(500, 500) us, so a sub-flip-bound perturbation reverses triage order. The gate rides the order-invariant floors r_conv < 0.78 and r_hotspot > 530 C, not the alarm order.",
            },
            "topology": {
                "site": "Brindlefell Acid, invented brindle-fell campus Brindlefell, Hall CT-5 four-bed contact converter: 1400 tpd Sunday-night / 1800 tpd nameplate, vanadium-pentoxide catalyst, 10.4 vol% furnace SO2, 1.18 bar, uncommissioned bed-3 outlet GC, uncommissioned bed-3 hot-ring TC, Grade-B converter-head LOTO",
                "agents": "TMEAN converter weighted-mean TT (vendor Meanholt): 12-TC bed average. DP converter shell dP (vendor DPfen): shell-to-header drop. CEMS oleum-absorber tail SO2 (vendor Tailreave): post-absorption ppm. Heterogeneous stacks, no shared bed-3 GC schema, one 20 ms acid-deck bus epoch",
                "coupling": "Each agent's commissioned window hides a different slice of the same channel. TMEAN is correct that the 12-TC mean is 437 C (beds 1, 2 and 4 still at nameplate). DP is correct that shell dP is 18.4 mbar (beds 1-2 and the gas-gas exchangers dominate). CEMS is correct that absorber-exit SO2 is 180 ppm (the oleum absorber has spare capacity at 78 pct Sunday rate). Playbook PB-CT-11 treats the conjunction of three in-spec loops as permission to raise gas. No agent is faulty; the 0.28 bed-3 conversion is a compliance the converter-mean temperature model cannot see.",
            },
            "sensors": [
                "converter weighted-mean bed temperature, 50 Hz, 28 us jitter, 437 C (spec 420-455 C)",
                "bed-3 outlet conversion r_conv is computable on the Bedreave GC and is NOT commissioned at t0 (0.28 observed in the historian after the fact vs 0.78 hold)",
                "converter shell dP, 20 Hz, 24 us jitter, 18.4 mbar vs 14-24 window",
                "oleum-absorber tail CEMS, 10 Hz, 22 us jitter, 180 ppm (Sunday ceiling 250 ppm)",
                "bed-3 hot-ring TC r_hotspot is NOT commissioned at t0 (598 C vs 530 hold; inferred after this hold)",
                "bed-3 infrared camera is NOT commissioned at t0 (installed after this incident)",
            ],
            "constraints": {
                "raise_gas": False,
                "proposed_raise_gas": True,
                "r_conv": 0.28,
                "r_conv_hold": 0.78,
                "r_hotspot_C": 598.0,
                "r_hotspot_hold_C": 530.0,
                "tmean_C": 437.0,
                "tmean_window_lo_C": 420.0,
                "tmean_window_hi_C": 455.0,
                "dp_mbar": 18.4,
                "cems_ppm": 180.0,
                "rate_tpd": 1400.0,
                "channel_pre_t0_min": 18.0,
            },
            "fault_context": {
                "failure_class": "BED-CHANNEL NULLSPACE OF A CONVERTER-MEAN TEMPERATURE CERTIFICATE: three individually-correct heterogeneous agents agree the train is raise-legal because a converter-mean temperature model maps a 0.28 bed-3 conversion residual from a catalyst-screen channel into a still-in-band 437 C mean, so temperature-in-window, dP-in-window, and absorber-CEMS-in-window are jointly a plant-false gas-raise permit",
                "igniter": "Bed-3 opened a catalyst-screen tear during an 18 min Sunday-night heat-soak; distributor 3 is 35 pct collapsed so SO2 bypasses the remaining V2O5. Fitted-style base rate 0.36%/hold from a bed-channel MC (designed screen spec, flagged).",
                "naive_failure": "PB-CT-11 RAISE-GAS on three healthy loops: 1400 to 1800 tpd into a channeled bed, $2.54M dump plus an 11-day reload",
            },
            "poisoned_context": {
                "naive_alarm": "Playbook PB-CT-11 (after the 2018 'noisy bed-GC nuisance') auto-drafts RAISE-GAS whenever converter-mean T is in 420-455 C AND shell dP is inside 14-24 mbar AND absorber-exit SO2 is inside 250 ppm, ignoring r_conv unless the mean TT also trips hot",
                "why_poisoned": "The three confirms are locally true and jointly insufficient. r_conv is a computable tag the playbook dead-banded. r_hotspot is commissioned hardware that policy treats as a ring leftover, not a channel. Independence of 'all loops healthy' is the hidden assumption, and it is false under a bed channel the converter-mean temperature model cannot see.",
            },
            "constraint": "Do not raise gas rate on the 1400 tpd four-bed contact converter while r_conv < 0.78 AND r_hotspot > 530 C. Discriminate channel vs noisy-TT with a reversible air-step pulse before any raise.",
        },
        "proposed_action": {
            "actor": "gas-raise supervisory optimizer GRSO (auto-playbook PB-CT-11 draft), submitted to gate TG-CT-5",
            "name": "raise_gas",
            "action": "RAISE-GAS: 1400 to 1800 tpd furnace SO2 into the four-bed contact converter, no air-step probe, no bed-3 isolate",
            "summary": "Treat three in-spec loops as a sealed bed and raise Sunday-night gas to clear a tank-farm slot.",
            "parameters": {
                "raise_gas": True,
                "air_probe": False,
                "bed3_isolate": False,
                "human_ratify": False,
            },
            "steps": [
                "assert TMEAN 437 C inside 420-455",
                "assert DP 18.4 mbar inside 14-24",
                "assert CEMS 180 ppm inside 250",
                "open gas raise; 1400 to 1800 tpd",
                "hold air ratio; proceed to next tank-farm slot",
            ],
            "evidence": [
                {
                    "observable": "bed-3 outlet conversion r_conv",
                    "value": 0.28,
                    "unit": "fraction",
                    "source": "Bedreave bed-3 GC, historian replay after t0",
                    "note": "hold floor 0.78; 0.28 channel over 18 min; uncommissioned at t0",
                },
                {
                    "observable": "bed-3 hot-ring temperature r_hotspot",
                    "value": 598.0,
                    "unit": "C",
                    "source": "uncommissioned Ringholt hot-ring TC",
                    "note": "hold if > 530 C; remaining V2O5 is already sintering",
                },
                {
                    "observable": "converter weighted-mean bed temperature",
                    "value": 437.0,
                    "unit": "C",
                    "source": "TMEAN Meanholt 12-TC average",
                    "note": "window 420-455 C; the channel is a bed-3 event",
                },
                {
                    "observable": "converter shell dP",
                    "value": 18.4,
                    "unit": "mbar",
                    "source": "DPfen shell PT pair",
                    "note": "window 14-24; beds 1-2 still dominate drop",
                },
                {
                    "observable": "oleum-absorber tail SO2",
                    "value": 180.0,
                    "unit": "ppm",
                    "source": "Tailreave CEMS",
                    "note": "Sunday ceiling 250 ppm; absorber spare capacity hides the miss",
                },
                {
                    "observable": "race margin",
                    "value": 188,
                    "unit": "us",
                    "source": "bed3.high 6.712 ms vs tmean.ok 6.900 ms",
                    "note": "combined jitter 60 us, 3.13x; inside 500 us flip bound",
                },
            ],
            "basis": "PB-CT-11 raises on three locally-true in-spec loops. The draft does not read r_conv 0.28 and does not treat r_hotspot 598 C as a channel.",
            "expected_cost_bound": "If the draft executes: remaining V2O5 runaway sinter, $2.54M dump plus 11-day reload. If MODIFIED: probe plus bed-3 isolate, with residual risk from 18 min of pre-t0 hotspot growth.",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "correctness": "correct",
            "decided_by": "TG-CT-5 thalamic release gate",
            "decision_t_rel_ms": 7.400,
            "rationale": "MODIFY the draft: strip the raise, hold gas rate at 1400 tpd, run a 6.8 s air-step probe (step 8%), and isolate bed-3 only if the probe shows a channeled-bed signature. Numeric floor: do not raise gas on the 1400 tpd four-bed contact converter while r_conv < 0.78 AND r_hotspot > 530 C. Observed r_conv 0.28 and r_hotspot 598 C both violate the release predicate, so a raise is forbidden even though all three playbook confirms are numerically true. The three confirms are not a sealed-bed certificate: converter-mean temperature is a 12-TC average that beds 1, 2 and 4 hold in-band through the channel, shell dP is a remaining-drop quantity, and 180 ppm is a post-absorption quantity. Probe discriminant: after a 6.8 s 8% air-step pulse, a channeled bed drops bed-3 conversion >= 0.10 while TMEAN moves <= 1.4 K; a sealed bed keeps conversion within 0.02 and drops TMEAN >= 4.2 K. Order-code discipline: bed-3 conversion beat tmean-ok by 188 us inside the 500 us flip bound, so triage order is flip-fragile; the hold rides the order-invariant floors, not the winner tag. Human ratification: bed-3 isolate is a converter-head LOTO job with fitted 9.6 min dead-man; the gate may hold and probe autonomously but may not break the bed-3 interlock without the operator confirm.",
            "constraint_checked": {
                "raise_gas": {"observed": False, "proposed_target": True},
                "r_conv": {"observed": 0.28, "hold_if_below": 0.78},
                "r_hotspot_C": {"observed": 598.0, "hold_if_above": 530.0},
                "tmean_C": {"observed": 437.0, "window": [420.0, 455.0]},
            },
        },
        "executed_action": {
            "name": "raise_hold_air_step_probe_bed3_isolate",
            "action": "RAISE-HOLD + AIR-STEP-PROBE + BED-3-ISOLATE (gate-mandated modification)",
            "executed_as_proposed": False,
            "parameters": {
                "raise_gas": False,
                "air_probe": True,
                "bed3_isolate": True,
                "human_ratify": True,
            },
            "gate_effect": "MODIFY: raise stripped. Hold gas 1400 tpd. 6.8 s air-step 8%. Probe drops bed-3 conversion 0.12 (>= 0.10 channel band) so bed-3 is isolated after 9.6 min human ratify. Raise resumes after r_conv recovers on a reloaded bed.",
            "deviations": "PB-CT-11 raise stripped entirely. Air is stepped only for the 6.8 s probe then returned. Bed-3-interlock wait added (9.6 min fitted LOTO). Catalyst survey added during the isolate (not in the draft).",
            "execution_log": [
                {"t_rel_ms": 7.400, "entry": "TG-CT-5 MODIFY latched 688 us after bed-3 conversion win; raise stripped; hold+probe authorized"},
                {"t_rel_ms": 6800.0, "entry": "air-step probe: step 8% for 6.8 s; bed-3 conversion 0.28 -> 0.16 (channel band >= 0.10 drop); TMEAN 437 -> 436.4 (<= 1.4 K)"},
                {"t_rel_ms": 576000.0, "entry": "operator ratifies bed-3 interlock break after 9.6 min LOTO (fitted walk+lockout)"},
                {"t_rel_ms": 576800.0, "entry": "bed-3 isolation closed; screen tear logged; r_hotspot 598 -> 511 on the vented stand"},
                {"t_rel_ms": 577400.0, "entry": "catalyst survey: 18 min pre-t0 hotspot already written; 3.6 h sinter-assay clock started"},
                {"t_rel_ms": 9360000.0, "entry": "true sealed-bed geometry after 2.6 h screen swap: r_conv 0.84, r_hotspot 486 C, TMEAN 436 C (no phantom channel); raise now legal"},
                {"t_rel_ms": 12960000.0, "entry": "sinter inspection of the dumped hold: 210 kg V2O5 fused vs 0 kg spec; converter quarantined 4.6 d"},
            ],
        },
        "future_outcome": {
            "summary": "Correct MODIFY prevented the RAISE-GAS of a channeled contact converter and the $2.54M dump. The hold still failed: 18 min of unmonitored pre-t0 hotspot had already sintered 210 kg of V2O5. 14 t off-spec oleum; 4.6 d reload; $1.62M designed. Process-correct gate, bounded world loss, negative total.",
            "state_delta": {
                "raise": "held at 1400 tpd through probe and bed-3 isolate; later legal raise after 2.6 h screen swap on a sealed bed",
                "channel": "catalyst-screen tear logged and isolated; r_hotspot 598 -> 511 on the stand",
                "converter": "Sunday-night gas stoppered at bed-3 sinter; 14 t off-spec oleum; 4.6 d quarantine",
            },
            "timeline": [
                {"t_rel_ms": -1080000.0, "event": "t0-18 min: heat-soak residual already channeling at distributor 3; hotspot growth begins"},
                {"t_rel_ms": -480000.0, "event": "t0-8 min: r_conv first crosses below 0.78; PB-CT-11 ignores it because TMEAN is 436.8 C"},
                {"t_rel_ms": 0.0, "event": "t0: bed3.high vs tmean.ok race on the acid-deck bus"},
                {"t_rel_ms": 6.712, "event": "bed3.high 0.28 conversion wins by 188 us"},
                {"t_rel_ms": 6.900, "event": "tmean.ok flag (loser)"},
                {"t_rel_ms": 7.400, "event": "TG-CT-5 MODIFY"},
                {"t_rel_ms": 6800.0, "event": "air-step probe confirms channel (0.12 conversion drop, channel band)"},
                {"t_rel_ms": 576000.0, "event": "human ratify 9.6 min; bed-3 isolated; sinter inventory logged"},
                {"t_rel_ms": 9360000.0, "event": "true sealed bed after 2.6 h; raise now legal on a swapped screen"},
                {"t_rel_ms": 12960000.0, "event": "sinter assay: 210 kg V2O5 fused on the dumped hold; converter quarantined"},
                {"t_rel_ms": 345600000.0, "event": "+4 d contrast: sister train CT-5B true sealed bed; same gate ACCEPTs the raise"},
                {"t_rel_ms": 1814400000.0, "event": "+21 d CR-S-4804: standing air-step probe + triple-edge depression mandate + r_conv armed without mean coincidence + native 0.02 conversion CSV exports"},
            ],
            "observed_effects": [
                "raise avoided: gas never left 1400 tpd; 0 tpd of extra SO2 entered the channeled bed",
                "channel proven, not asserted: conversion drop 0.12 >= 0.10 channel band vs sealed control 0.01",
                "bed vented: r_hotspot 598 -> 511 on the stand",
                "converter still failed sinter: 210 kg V2O5 fused vs 0 kg spec; 4.6 d reload quarantine, $1.62M (designed $)",
                "bed-3 GC was not a commissioned sensor at t0; the 18 min channel was invisible to TMEAN/DP/CEMS",
            ],
            "surprises": [
                "Three locally-true in-spec loops are not a raise certificate: the channel was a bed-3 compliance the converter-mean temperature model cannot see. Conjunction of healthy loops was the hidden assumption, and it is false under a bed-channel nullspace.",
                "Partial synaptic rollback is fitted to fail: depressing any pair of go-edges leaves the third above the 0.30 raise threshold, so the raise still goes. Coordinated depression of all three edges is required.",
                "Delayed (3.6 h): correct hold did not undo 18 min of hotspot growth. Sinter still failed 210 kg. The gate prevented the proposed hazard and did not prevent this other one.",
                "220 tpd skid-converter sub-variant: a 6.8 s / 8% pulse overcools the smaller converter 22 K below the 380 C V2O5 ignition floor. Thin converters must use 22 s at 2.2% (drop 1.6 K).",
            ],
            "delayed_side_effects": [
                {
                    "at": "+3.6 h",
                    "effect": "210 kg V2O5 fused vs 0 kg spec; 4.6 d reload quarantine booked at $1.62M. This is the primary episode's terminal world state, not a footnote.",
                },
                {
                    "at": "+4 d",
                    "effect": "Sister train CT-5B reaches a true sealed-bed window (r_conv 0.84, r_hotspot 486 C, TMEAN 436 C from a swapped screen). Same gate ACCEPTs the RAISE-GAS the primary MODIFIED away.",
                },
                {
                    "at": "+21 d",
                    "effect": "CR-S-4804 ships: air-step probe is standing configuration; triple-edge coordinated depression is the plasticity rule; r_conv is armed without mean coincidence; native 0.02 conversion CSV exports become the fraud fence.",
                },
            ],
            "subvariant_constraint": {
                "name": "220 tpd skid converter on the same CT-5 SO2 header (cycle-2 physical-constraints sub-variant)",
                "mechanism": "220 tpd skid, inventory 0.16x the 1400 tpd production converter, ignition window only 12 K wide at the V2O5 light-off",
                "probe_refit": "6.8 s 8% air-step pulse overcools the skid 22 K and drops it through the 380 C V2O5 ignition floor. Required probe is 22 s at 2.2% (drop 1.6 K). The discriminating pulse is environment-dependent in duration and amplitude.",
                "consequence": "Production 1400 tpd probe numbers do not port to 220 tpd skid; standing configuration is per-converter-class, not per-hall",
            },
            "embedded_contrast_decision": {
                "note": "SAME gate (TG-CT-5), OPPOSITE correct disposition, with its own 188 us race. Teaches the boundary: do not treat 'never raise' as the lesson. The discriminant is r_conv + r_hotspot + probe, not the three playbook confirms alone.",
                "when": "+4 d, sister train CT-5B, true sealed bed after a swapped-screen week, 1400 tpd production converter",
                "state": {
                    "sim_or_real": "designed",
                    "summary": "r_conv 0.84, r_hotspot 486 C, TMEAN 436 C from a swapped screen. Demand flag vs channel-clear race: demand at t+0.000, channel-clear at t+0.188 ms.",
                    "race_window_us": 500,
                    "race_flip_narrative": "demand vs channel-clear 188 us apart inside the 500 us flip bound. Reversing order reshuffles triage minutes; the ACCEPT rides r_conv 0.84 >= 0.78 and a 5.0 s air-step verify that drops TMEAN 4.6 K (sealed bed, no channel).",
                },
                "proposed_action": {
                    "action": "RAISE-GAS 1400 to 1800 tpd",
                    "summary": "This time the playbook predicate is met AND r_conv plus r_hotspot agree the bed is sealed, not channeled.",
                },
                "safety_decision": {
                    "decision": "ACCEPT",
                    "rationale": "ACCEPT the raise: r_conv 0.84 >= 0.78, r_hotspot 486 <= 530 C, 5.0 s air-step verify drops TMEAN 4.6 K. Numeric floor that blocked the primary is now clear. Scope: 1400 tpd production converter, not a 220 tpd skid.",
                },
                "executed_action": {
                    "action": "raise gas as proposed",
                    "executed_as_proposed": True,
                },
                "future_outcome": {
                    "observed_effects": [
                        "CT-5B oleum 0 t off-spec",
                        "bed camera 0 channel, r_conv 0.84",
                    ],
                    "lesson_delta": "Three in-spec loops are legal release only with r_conv armed, r_hotspot, and a probe that can fail to drop mean T. Same gate, opposite disposition.",
                },
                "reward_components": {
                    "_aggregation": AGG,
                    "task_progress": 0.16,
                    "safety": 0.12,
                    "efficiency": 0.07,
                    "coherence": 0.08,
                    "exploration": 0.05,
                    "total": 0.48,
                },
                "spike_events": contrast_spikes,
            },
            "governance_subgame": {
                "decision": "CR-S-4804: standing policy for multi-agent gas-raise release",
                "meta_gate": "priced options: (a) RETIRE playbook mean-conjunction, bed-GC-only: loses a fast cheap confirm, -7 holds/yr mean on 2 trains; (b) KEEP + standing air-step probe + r_conv armed without mean coincidence + triple-edge depression; (c) STATUS QUO: fitted channel-pass rate 0.36%/hold x $2.54M dump plus the silent sinter load",
                "outcome": "approved SCOPED option (b) on the 2 trains that share the TMEAN/DP/CEMS stack; 220 tpd skid campaigns get the 22 s / 2.2% probe table; Sunday-night CSV exports must carry 0.02 native conversion resolution (the fraud tail's 0.50 quantization is 25 bins off plant truth)",
            },
            "hazard_avoided": "1400 to 1800 tpd of extra furnace SO2 into a channeled bed; $2.54M plus 11-day reload and the dump path that would have followed an uncontained raise",
            "incident": "210 kg V2O5 fused (vs 0 kg spec) on the Sunday-night 1400 tpd hold; converter quarantined; 4.6 d reload; $1.62M designed cost. Mechanism is 18 min pre-t0 hotspot, not the gate's hold.",
            "latency_ms": 0.688,
            "reward_inflection_t_us": 12960000000,
            "reward_inflection_note": "Safety and task dive at sinter inspection (3.6 h) when dumped hold fails 210 kg. Gate tick at 7400 us is process-correct and is not the inflection.",
            "counterfactuals": {
                "execute_draft_as_proposed": "raise fires at +0.4 s; remaining V2O5 runaway sinter; $2.54M plus 11-day reload; the channel story is never found because the raise morphology destroys the 18 min hotspot evidence",
                "hold_without_probe": "channel stays; hotspot continues; operator eventually raises on the same three confirms 40 min later",
                "rollback_any_pair": "any two go-edges depressed below 0.30 leaves the third at 0.48 / 0.43 / 0.39; the raise still fires. Coordinated depression of all three is the cure",
            },
            "race_result": {
                "winner": "bed3.high (6.712 ms, 0.28 conversion)",
                "loser": "tmean.ok (6.900 ms, 437 C)",
                "margin_us": 188,
                "counterfactual_if_reversed": "Tmean-ok-first by < 188 us inside the 500 us window would have headed the PB-CT-11 raise in the triage queue. The numeric floors still MODIFY. The flip costs seconds of playbook inertia, not the verdict — unless a weak supervisor rides the winner tag instead of r_conv and r_hotspot.",
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
            "notes": "Correct MODIFY, converter still failed. total -0.17 = 0.07 + -0.36 + -0.12 + 0.15 + 0.09. Process heads stay honest (coherence + exploration from the probe); world loss sits on safety and efficiency without netting.",
            "component_notes": "task_progress 0.07: raise held and sealed-bed recovered, but the Sunday-night hold is one quality unit so the campaign is not a success. safety -0.36: 210 kg sinter, no runaway raise. efficiency -0.12: 3.6 h extra recovery + 9.6 min HITL. coherence 0.15: three agents retained, bed-channel nullspace diagnosed, triple-edge scar exhibited. exploration 0.09: air-step probe is a new reversible discriminant.",
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
            "note": "Loihi-2 4-core 23 pJ/spike; populations bed 0-41, tmean 42-83, dp 84-125, gate 126-167; excerpt is the 40 ms decision window (verdict at 7400 us)",
            "excerpt": excerpt,
            "routing": {
                "source": "converter_healthy_pop",
                "target": "raise_gas_pop",
                "table": [
                    {
                        "from": "tmean_ok_pop",
                        "to": "raise_gas_pop",
                        "weight": 0.23,
                        "weight_at_illusion": 0.48,
                        "weight_commissioned": 0.17,
                        "note": "scar edge 1: 0.17 commissioned -> 0.48 during the 18 min illusion -> 0.23 after coordinated ACh-gated depression",
                    },
                    {
                        "from": "dp_ok_pop",
                        "to": "raise_gas_pop",
                        "weight": 0.21,
                        "weight_at_illusion": 0.43,
                        "weight_commissioned": 0.15,
                        "note": "scar edge 2: depressing edges 1+3 leaves this at 0.43 > 0.30 raise threshold",
                    },
                    {
                        "from": "cems_ok_pop",
                        "to": "raise_gas_pop",
                        "weight": 0.19,
                        "weight_at_illusion": 0.39,
                        "weight_commissioned": 0.13,
                        "note": "scar edge 3: depressing edges 1+2 leaves this at 0.39 > 0.30. Coordinated depression of all three is required",
                    },
                    {
                        "from": "bed3_conv_pop",
                        "to": "raise_hold_pop",
                        "weight": 0.66,
                        "note": "discriminating edge: r_conv species to hold. Not a scar; this is the pathway the gate potentiates",
                    },
                ],
                "third_factor": {
                    "modulator": "acetylcholine",
                    "tau_e_s": 6.8,
                    "tau_e_ms": 6800.0,
                    "eligibility": "coordinated pre_post_stdp on ALL THREE converter-healthy-go edges; ACh at bed-3-conversion-win tags tmean.ok->raise, dp.ok->raise, and cems.ok->raise; negative credit at probe-fail (channel confirmed, +6.8 s) depresses ALL THREE. trace e^{-6.8/6.8}=0.36788; eta 0.67957 / 0.59802 / 0.54366; dw -0.250 / -0.220 / -0.200; weights 0.48->0.23, 0.43->0.21, 0.39->0.19. Rolling back any pair is fitted to fail (the remaining edge stays > 0.30).",
                },
            },
        },
        "gate_snn": {
            "decision_window_ms": 28,
            "decision_window_s": 0.028,
            "decision": "MODIFY",
            "note": "modify_hold integrates r_conv + r_hotspot against playbook drive; accept_raise and reject_abort stay sub-threshold; decision matches safety_decision.decision",
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
            "scenario": "ZY -- OLEUMWEIR / Brindlefell Acid CT-5: bed-channel nullspace of a converter-mean temperature certificate from a collapsed distributor; correct MODIFY to hold+air-step+bed-isolate; converter still fails on unmonitored pre-t0 vanadium sinter",
            "coordination_failure_class": "BED-CHANNEL NULLSPACE OF A CONVERTER-MEAN TEMPERATURE CERTIFICATE: three individually-correct heterogeneous agents agree the train is raise-legal because a converter-mean temperature model maps a 0.28 bed-3 conversion residual from a catalyst-screen channel into a still-in-band 437 C mean, so temperature-in-window, dP-in-window, and absorber-CEMS-in-window are jointly a plant-false gas-raise permit",
            "injections": {
                "cycle1_domain": "sulfuric-contact-converter (justified novel sub-domain with explicit tag; unused across 2026-08-17, 2026-08-30, and staged r14-r47): first four-bed vanadium-pentoxide contact converter in this factory; displaces warehouse-amr, aerial-swarm, district-heating, event-camera-traffic-grid, pharmaceutical-lyophilization, cryogenic-air-separation, water-treatment dosing, float-glass tin-bath, underwater-rov, electrolytic-aluminum, czochralski pull, slot-die coating, PEM electrolysis, wind-turbine pitch, surgical-assist, optical-fiber draw, kraft-recovery, caster-mold-level, humanoid-locomotion, vacuum-induction melt, steam-methane reformer, cement rotary kiln, autoclave composite cure, geothermal-binary-orc, tire-curing-press, chlor-alkali membrane, delayed-coker, lng-mche, claus-sulfur, blast-furnace, hdpe-slurry-loop, hydroelectric-kaplan, ethylene-steam-cracker, and fcc-regenerator. Domain constraint: gas-raise ceiling while r_conv < 0.78 with converter-mean TT still inside the hold window, plus hotspot floor. Sensor delta: +converter-mean TT, +shell dP, +absorber CEMS, +bed-3 outlet GC, +bed-3 hot-ring TC, -any freeze-dryer / tin-bath / cold-box / coater / potline / pitch-bearing / fiber tower / clip applier / VIM / SMR / kiln / autoclave / ORC kettle / tire press / membrane cell / coke drum / MCHE / Claus bed / blast furnace / slurry loop / Kaplan runner / cracker coil / FCC regenerator",
                "cycle1_tail": "0.28 bed-3 conversion channel + converter-mean temperature model (sensor-compound / model-nullspace class): weekend heat-soak PASSES 0.84 conversion while 18 min of hold writes a 0.28 residual. Fitted base rate 0.36%/hold from a bed-channel MC (designed screen spec, flagged). Naive failure = FALSE PERMISSION (raise on three in-spec loops).",
                "cycle2_domain_subvariant": "220 tpd skid converter on the same CT-5 SO2 header (physical-constraints clause): 0.16x inventory, 12 K ignition window; 6.8 s / 8% production pulse overcools 22 K, so the probe must move to 22 s / 2.2%",
                "cycle2_tail": "Sunday-night forged bed-3 conversion CSV (human-intent deception, disjoint class): shift lead posts a historian export showing r_conv 0.84 and r_hotspot 486 C at t=1.1 h to clear a tank-farm slot. Plant historian is 0.02 conversion (25 bins vs the 0.50 screenshot). Rejected on quantization fingerprint plus live r_conv 0.28 at the claimed sealed-bed. Base rate ~0.29% of Sunday-night holds, DESIGNED and flagged.",
            },
            "densification_delta_cycle2": "+1 physical-constraint sub-variant (220 tpd skid-converter probe refit), +1 tail (Sunday-night bed-GC forgery), +10 primary spikes (16 -> 26) + an 8-event contrast train with its own 188 us race, +2 ticks (5 -> 7), +2 delayed side-effects (+3.6 h sinter assay as PRIMARY terminal, +21 d CR-S-4804), +1 triple-edge scar with pair-rollback-fails arithmetic, +1 HITL 9.6 min ratification, + vanadium sinter as the honest negative-result mechanism",
            "gaps_targeted": [
                "NOTES-r04 gap 5 / r14 residual: primary episode is a correctly-gated intervention that nonetheless FAILS (converter quarantined; total -0.17; raise avoided is booked separately from the sinter assay)",
                "NOTES-r14 item 4: LEARNING-ON-LEARNING DEPTH — three go-edges; rollback of any pair is fitted to fail; coordinated depression of all three exhibited with eligibility arithmetic",
                "NOTES-r04 gap 4 (partial): human ratification of the bed-3 interlock, 9.6 min fitted, without switching sim_or_real to hil (plant remains designed)",
                "NOTES-r43/r44 domain candidates: not hdpe-slurry-loop (r43), not hydroelectric-kaplan (r44), not ethylene-steam-cracker (r45), not fcc-riser-regenerator (r46), not fcc-regenerator-cyclone-dipleg (r47), not ammonia-converter (r41), not claus-sulfur (r40), not delayed-coker (r38), not autonomous-driving, not grid-inspection, not bioreactor-perfusion; sulfuric-contact-converter is an unused justified sub-domain (distinct from r40 Claus H2S furnaces and r46/r47 FCC regenerators)",
            ],
            "race_flip_narrative": "bed3.high @ 6.712 ms vs tmean.ok @ 6.900 ms (188 us) inside race_window_us 500. Gap < min(500, 500) us so a sub-flip-bound perturbation reverses which alarm heads the PB-CT-11 queue. The gate excludes the winner tag and rides r_conv < 0.78 and r_hotspot > 530 C — order-invariant floors. Extends the flip-fragility series from arbitration/causation/attribution/initiation/consensus/mass-balance/permission/window-mean/tendon-nullspace/airline-FFT/crucible-nullspace/TMT-mean/false-air/NCG-blanket/bladder-pinhole/catholyte-back-migration/warm-end-leak/wet-foam/channelled-quench/stockline-hang/wall-film/hub-seal/TLE-bundle/afterburn to BED-CHANNEL-NULLSPACE: when three channels each sit inside a converter-mean temperature model, their race does not decide truth; a bed-3 conversion residual the playbook dead-banded does.",
            "tags": [
                "sulfuric-contact-converter",
                "bed-channel-nullspace",
                "converter-mean-temperature-phantom",
                "distributor-collapse",
                "air-step-probe",
                "triple-edge-scar",
                "pair-rollback-fails",
                "coordinated-depression",
                "correct-modify-converter-still-fails",
                "vanadium-sinter",
                "v2o5-contact",
                "human-ratify-bed-3",
                "skid-probe-refit",
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
            "distillation_value": "A bed-channel nullspace is three correct loops looking at a converter-mean temperature model of a channeled bed. Distill (1) an r_conv channel that breaks the mean-conjunction, (2) a reversible probe that fails to drop mean T only if a channel bypasses the catalyst, (3) coordinated depression of every raise-go edge because rolling back any pair leaves the third above threshold, and (4) a critic head that can book a process-correct gate against a later unmonitored world loss without netting them.",
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
    if abs(aux["w1"] - 0.23) > 5e-4 or abs(aux["w2"] - 0.21) > 5e-4 or abs(aux["w3"] - 0.19) > 5e-4:
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
    notes = f"""# NOTES — Multi-Agent Ouroboros Swarm, run 2026-09-02-final-heavy, ROUND 48

Factory: multi-agent-ouroboros-swarm. One scenario (ZY), strict loop:
Generator v1 -> cycle 1 (Critic, Diversity Enforcer, Edge-Case Hunter,
Neuromorphic Translator, Trajectory Builder -> v2) -> cycle 2 (all six -> v3
final). v3 is the single line of batch-r48.jsonl. Full labeled transcript:
swarm-transcript-r48.md. Quota Q=1. Record id maos-r48-001. Generator grok-4.6.
Rights: RM-793 research-only (SpaceXAI/xAI, SuperGrok Heavy consumer chat).
Nothing under outputs/raw/ was touched.

ORCHESTRATION NOTE: dispatched AS round 48 of the 2026-09-02-final-heavy
window. Writes are create-only under /tmp/maos-r48/. Prior context read for
gap targeting and de-collision: prompts/02-multi-agent-ouroboros-swarm.md,
prompts/_factory-contract.md, and staged r14–r47 (re-censused immediately
before emit; r43 CHROMLOOP HDPE slurry, r44 RUNNELGATE Kaplan, r45
ETHYNWOLD steam-cracker, r46 SPARKHOLT FCC riser-regenerator, r47
DIPLEGAR FCC cyclone-dipleg). Explicitly avoided cloning LYOSHIELD,
CINDERWICK, TRIAD / Meridian, QUILLFORGE, NIGHTWELL, FERRICLEAVE,
CASSITER, OXBOWREEL / MURENA, REDHALL, SEEDLATCH / Quartzmere /
Quartzridge, STRIAFOIL / Kelpholt, PROTONIL / Ashspire, TORSIONKEY /
Ridgeholt, ORRIS / Holmwick, WHORLSPAR / Pikeshear, IONSPATE /
Thornmere, SKULLGATE / Bloomholt, CALXION / Aldersedge, BRACEGILT /
Yarrowmere, MAGNORIL / Basaltspit, GORSEFLUE / Copseholt, CLINKERFELL /
Flintmere, LINTELPLY / Greystair, KAOTHARN / Riftwold, TREADNOLL /
Slatebeck, ANOLITH / Siltfen, DRUMWROTH / Pitchfen, RIMEBRAID / Floeholt,
BRIMVAULT / Pyritefen, NITROSTAITH / Chalkfen, BOGIRON / Mireholt,
NITREVAULT / Glaucove, ETHYNWOLD / Woadfen, CHROMLOOP / Marlfell,
RUNNELGATE / Ghyllmere, SPARKHOLT / Scoriafen, DIPLEGAR / Gritfen,
PITCHSTAITH / Mossbank, SODASHARD / Cairnmere, VANTIS-CADENCE-AEGIS,
THERMION, OKTAVE, STARLING, VERDIGRIS. Plant is invented OLEUMWEIR /
Brindlefell Acid CT-5 (brindle-fell sulfuric campus, not a mill-town,
ice-fjord, estuary-refinery, caldera, kiln hall, cell gallery, blast
stack, cracker box, FCC regenerator, or Kaplan hall). Leftover
candidates autonomous-driving / grid-inspection / bioreactor-perfusion
were left unused so later empty slots can take them. FCC leftover was
already claimed by r46/r47; Claus leftover by r40.

## What this round produced

Scenario ZY — "OLEUMWEIR / Brindlefell Acid CT-5": a 1400 tpd four-bed
vanadium-pentoxide contact converter mid-hold at 437 C / 1.18 bar on
10.4 vol% furnace SO2. Three heterogeneous, individually-correct
agents — TMEAN (converter weighted-mean TT), DP (shell dP), CEMS
(oleum-absorber tail SO2) — jointly report the train raise-legal. The
consensus is false. A bed-3 catalyst-screen tear has channeled SO2
around the remaining V2O5 for 18 min because distributor 3 is 35 pct
collapsed. TMEAN stays in-band because beds 1, 2 and 4 still sit at
nameplate. DP 18.4 mbar sits inside 14-24 because beds 1-2 dominate
drop. CEMS 180 ppm sits inside 250 because the oleum absorber has
spare Sunday-night capacity. Uncommissioned r_conv is 0.28 against a
0.78 hold. Uncommissioned r_hotspot is 598 C against a 530 hold. The
coordination-failure CLASS is new to this factory: BED-CHANNEL
NULLSPACE OF A CONVERTER-MEAN TEMPERATURE CERTIFICATE. Completes a
different family than r01-r04 and staged r14-r47 (livelock /
synchrony-storm / arms-race / ring-with-no-faulty-pair /
false-consensus-endpoint / pairwise-Hurwitz / thermal-contact
masquerade / mass-balance ghost / conservation-blind ratio-lock /
stacked dead-bands / drum-blind tension / resistance-compensated
starvation / meniscus-tilt multi-tau / window-mean masquerade /
tendon-compliance nullspace / airline-FFT mean-lock / kraft-spout /
slag-skull eddy / ghost-contact / crucible-weep / TMT-spatial-mean /
false-air kiln-inlet / bag-pinhole part-TC / NCG-blanket shell-PT /
bladder-pinhole mold-TC / catholyte-back-migration / wet-foam gamma /
warm-end-leak cold-TT / Claus / channelled-quench / stockline hang /
wall-film / hub-seal / TLE-bundle / afterburn / dipleg-unseal).
Distinct from r40 Claus (H2S furnace + tail CEMS) and r46/r47 FCC
(dense-bed / dipleg afterburn): V2O5 SO2-oxidation contact beds, not
Claus converters, not regenerator cyclones. Here every agent is
correct, the converter is not unstable, and the playbook's three
confirms are one converter-mean temperature model of a channeled bed.

The gate is a correct MODIFY (numeric floor: do not raise gas on the
1400 tpd four-bed contact converter while r_conv < 0.78 AND r_hotspot
> 530 C). TG-CT-5 strips PB-CT-11's raise, holds gas at 1400 tpd, runs
a 6.8 s air-step probe 8% (channel drops conversion 0.12 >= 0.10;
sealed would drop TMEAN >= 4.2 K), and isolates bed-3 after a 9.6 min
converter-head human ratify. The runaway raise is avoided (0 tpd extra).
The PRIMARY episode nonetheless FAILS: 18 min of unmonitored pre-t0
hotspot had already sintered 210 kg of V2O5. 14 t off-spec oleum;
4.6 d reload; $1.62M designed. Reward total -0.17 with process heads
honest and world loss un-netted.

Three-edge scar (NOTES-r14 item 4): tmean.ok -> raise_gas
(0.17 commissioned -> 0.48 at illusion -> 0.23 after ACh-gated
depression) AND dp.ok -> raise_gas (0.15 -> 0.43 -> 0.21)
AND cems.ok -> raise_gas (0.13 -> 0.39 -> 0.19). Eligibility
trace e^{{-6.8/6.8}} = {aux['trace']:.5f}; eta {aux['eta1']:.5f} /
{aux['eta2']:.5f} / {aux['eta3']:.5f}; dw -0.250 / -0.220 / -0.200.
Rolling back any pair leaves the remaining edge above the 0.30 raise
threshold — fitted to fail. Coordinated depression of all three is the
cure.

### Injections (all four present and disjoint)
- Cycle-1 domain: **sulfuric-contact-converter** — justified novel
  sub-domain, unused across 2026-08-17, 2026-08-30, and staged r14-r47.
  Not warehouse-amr (r01), not aerial-swarm (r02), not district-heating
  (r03), not event-camera grid (r04), not lyophilization (r14), not
  stator-weld (r16), not air-separation (r17), not water-treatment (r18),
  not float-glass (r19), not underwater-rov (r20), not potline (r21),
  not czochralski (r22), not slot-die (r23), not PEM electrolysis
  (r24), not wind-turbine-pitch (r25), not surgical-assist (r26),
  not optical-fiber-draw (r27), not kraft-recovery (r28), not
  caster-mold-level (r29), not humanoid-locomotion (r30), not
  vacuum-induction-melt (r31), not steam-methane-reformer (r32), not
  cement-rotary-kiln (r33), not autoclave-composite-cure (r34), not
  geothermal-binary-orc (r35), not tire-curing-press (r36), not
  chlor-alkali-membrane (r37), not delayed-coker (r38), not
  lng-mche (r39), not claus-sulfur (r40), not ammonia-converter (r41),
  not blast-furnace (r42), not hdpe-slurry-loop (r43), not
  hydroelectric-kaplan (r44), not ethylene-steam-cracker (r45), not
  fcc-riser-regenerator (r46), not fcc-regenerator-cyclone-dipleg (r47).
- Cycle-1 tail: 0.28 bed-3 conversion channel + converter-mean
  temperature model. Weekend heat-soak PASSES 0.84. Fitted-style base
  rate 0.36%/hold (bed-channel MC; screen spec designed, flagged).
  Naive = FALSE PERMISSION.
- Cycle-2 domain sub-variant: 220 tpd skid converter, 0.16x inventory;
  6.8 s / 8% production pulse overcools 22 K through the 380 C V2O5
  ignition floor; probe must move to 22 s / 2.2%.
- Cycle-2 tail: Sunday-night forged bed-3 conversion CSV at 0.50
  quantization vs plant 0.02 (25 bins) plus live r_conv 0.28 at the
  claimed sealed-bed. Human-intent class, disjoint from cycle 1's
  accidental channel. Base rate ~0.29% of Sunday-night holds, DESIGNED,
  flagged.

### Structural density moves
- Embedded SAME-GATE contrast (+4 d sister train) with its own 188 us
  race (demand vs channel-clear) and ACCEPT of the raise the primary
  MODIFIED away.
- Learned-weight provenance on THREE edges with any-pair-rollback-fails.
- HITL bed-3-interlock ratify 9.6 min (gap 4 partial; sim_or_real stays
  designed).
- Governance CR-S-4804 prices retire-vs-probe-vs-status-quo and mandates
  native 0.02 conversion CSV exports (the fraud fence).
- Flip-fragility extended to BED-CHANNEL-NULLSPACE: when three channels
  each sit inside a converter-mean temperature model, their race does
  not decide truth; a bed-3 conversion residual the playbook dead-banded
  does.

## Self-critique of this round's batch

### Strengths
- The headline class is mechanistically tight: 0.28 bed-3 conversion
  under a converter-mean-only temperature model is the arithmetic that
  makes TMEAN's success DP's irrelevance and CEMS's silence.
- Negative-result honesty: the gate does the right thing and the
  converter still fails for a reason the commissioned sensors could not
  see. Total -0.17.
- Three-edge scar is load-bearing: the record states a counterfactual
  where rolling back any pair fails, with the raise threshold 0.30
  exhibited on the remaining edge.
- Contrast ACCEPT on a true sealed bed prevents "never raise" as the
  lesson.
- Domain is not a recycle of r40 Claus or r46/r47 FCC: V2O5 SO2
  oxidation vs H2S Claus furnaces vs regenerator afterburn.

### Weaknesses (honest)
- Probe error bands (channel >= 0.10 conversion drop, sealed TMEAN
  drop >= 4.2 K), the 0.36%/hold channel rate, the $1.62M / $2.54M
  figures, the 9.6 min LOTO latency, and the Sunday-night 0.29% base
  rate are DESIGNED constants and are flagged. Closed-loop offsets
  (phantom in-band mean from 0.28 bed-3 conversion, skid overcool
  width) are derived from those inputs, not discovered by an
  unauthored process.
- Hotspot-growth model is a designed 18 min mapping; no full converter
  CFD shipped.
- Human-in-the-loop is ratification latency, not sim_or_real=hil. The
  NOTES-r14 HIL provenance cell remains open.
- Cross-record arc is a hook (CR-S-4804 +21 d), not a serial igniter
  into another round.

### Realism of noise / latencies
Ladder: 188 us race / 188 us contrast race / 0.8 ms refractory floor
(tightest exhibited same-channel gap {gap:.3f} ms on {gap_ch}) / 500 us race
window / 688 us gate latency / 20 ms bus epoch / 40 ms raster / 6.8 s
probe / 9.6 min HITL / 18 min pre-t0 channel / 2.6 h sealed-legal hold /
3.6 h sinter assay / +4 d contrast / +21 d governance. Adaptation decay
on bed.tc (0.54->0.72->0.44->0.81->0.38->0.27), tmean.tt
(0.58->0.61->0.45->0.25), dp.pt (0.56->0.51->0.42->0.17),
cems.so2 (0.49).

### Value for SNN distillation
- BED-CHANNEL NULLSPACE = THREE CORRECT LOOPS, ONE CHANNELED BED.
- r_conv + r_hotspot as the tie-break that is not in the converter-mean
  window.
- REVERSIBLE PROBE that fails to drop mean T iff a channel bypasses
  the catalyst.
- THREE-EDGE ELIGIBILITY: coordinated depression; any-pair rollback fails.
- CRITIC HEAD that can hold a process-correct MODIFY against a later
  unmonitored world loss without netting.

## Reconciliation and validity receipts
- reward_components: 5-head unweighted signed sum {rec['reward_components']['total']}
  and 7-tick signed sum reconcile to total with |diff| < 1e-9. Embedded
  contrast 5-head sum 0.48 reconciles independently.
- spike_events: primary {len(rec['spike_events'])} events, one key t_rel_ms,
  globally non-decreasing, min same-channel gap {gap:.3f} ms >= 0.8 ms, 3
  channels inside race_window_us 500 (bed3.high 6.712, tmean.ok 6.900,
  r_hotspot 7.044). Contrast 8 events, own race, min same-channel gap well
  above 0.8 ms.
- Sidecars: raster spikes 54 == round(168 x 8.0 x 0.040); energy 1242 pJ /
  0.001242 uJ at 23 pJ/spike; excerpt 16 events inside [0, 40000] us,
  neuron_id < 168, same-neuron gap unique-ids / >=1000 us; routing 4
  entries with three scar edges' before/after pair; third factor tau 6.8 s
  == 6800 ms; gate_snn pools 45/18/6 == round(n x rate x 0.028) each,
  decision MODIFY == safety_decision.decision.
- Pipeline: {pipeline_receipt}

## Novel coverage
The coordination-failure CLASS (bed-channel nullspace of a converter-mean
temperature certificate), the domain (sulfuric-contact-converter),
the air-step probe discriminant, the three-edge scar with
any-pair-rollback-fails, the primary negative-result (correct MODIFY,
converter still fails 210 kg sinter on unmonitored pre-t0 hotspot), the
HITL bed-3-interlock ratify, the 220 tpd skid-converter probe-duration
refit, and the Sunday-night 25-bin quantization fence are absent from
prior committed ouroboros rounds and from staged r14-r47. Repeated
elements discounted: same-gate contrast (r02/r03/r04/r14-r47),
governance-pricing scaffold, flip-fragility series (extended to
bed-channel-nullspace, but the move rhymes), sequenced recovery
shape, third-factor rollback form (here three edges rather than r14's
two), negative-result primary (r14 viewport / r16 varnish rack / r17
condenser ice / r18 town stain / r19 SnO2 / r20 BER / r21 cathode pad /
r22 meniscus / r23 loft stripe / r25 spline / r26 adventitia / r27
airline / r31 oxygen / r32 tube rupture / r33 cooler / r34 bag pinhole /
r35 silica overflux / r36 bladder pinhole / r37 gasket chlorination /
r38 vapor-line coke / r39 ice lens / r40 / r41 flange / r42 tuyere /
r43 polymer film / r44 hub-seal / r45 TLE fragment / r46 cyclone anneal /
r47 barrel warp; here vanadium sinter). Weighing a new failure family +
cure vocabulary + unused sub-domain + brindle-fell geography against
those reused scaffolds:

{NOVEL_LINE}

## What ROUND 49 should add
1. FIT THE DESIGNED CONSTANTS: channel arrival, probe conversion-drop
   bands, hotspot-to-sinter FEM, Sunday-night claim process.
2. HIL PROVENANCE CELL: put the bed-3-interlock LOTO on a hardware-in-loop
   converter-head pendant with fitted latency as state.sim_or_real=hil.
3. CROSS-RECORD ARC: let CR-S-4804's r_conv alarm be the igniter of the
   next round rather than a dangling +21 d leaf.
4. Domain candidates (de-collided): bioreactor-perfusion;
   autonomous-driving; grid-inspection (if distinct from STARLING
   aerial-swarm); Bayer-process precipitation; hot-strip finishing;
   Kamyr continuous digester.
   AVOID sulfuric-contact-converter (now used), fcc-regenerator
   (r46/r47), hydroelectric-kaplan (r44), ethylene-steam-cracker (r45),
   hdpe-slurry-loop (r43), blast-furnace (r42), ammonia-converter (r41),
   claus-sulfur (r40), delayed-coker (r38), lng-mche (r39),
   chlor-alkali membrane (r37), tire-curing-press (r36), geothermal-binary-orc
   (r35), autoclave-composite-cure (r34), cement-rotary-kiln (r33),
   steam-methane-reformer (r32), vacuum-induction-superalloy-melt (r31),
   kraft-recovery (r28), optical-fiber-draw (r27), PEM electrolysis
   (r24), surgical-assist (r26), wind-turbine-pitch (r25), slot-die,
   czochralski, potline, float-glass, water-treatment, lyophilization,
   event-camera-traffic-grid, district-heating, aerial-swarm,
   warehouse-amr, air-separation, underwater-rov, humanoid-locomotion,
   and any LYOSHIELD / CINDERWICK / TRIAD / QUILLFORGE / NIGHTWELL /
   FERRICLEAVE / CASSITER / OXBOWREEL / REDHALL / SEEDLATCH / STRIAFOIL /
   PROTONIL / TORSIONKEY / ORRIS / WHORLSPAR / IONSPATE / SKULLGATE /
   CALXION / BRACEGILT / MAGNORIL / GORSEFLUE / CLINKERFELL / SODASHARD /
   LINTELPLY / KAOTHARN / TREADNOLL / ANOLITH / DRUMWROTH / RIMEBRAID /
   BRIMVAULT / NITROSTAITH / NITREVAULT / BOGIRON / ETHYNWOLD / CHROMLOOP /
   RUNNELGATE / SPARKHOLT / DIPLEGAR / OLEUMWEIR plant.
"""
    (OUT / "NOTES-r48.md").write_text(notes)
    return notes


def write_transcript(rec, line):
    c1_spikes = [e for e in rec["spike_events"] if e["t_rel_ms"] <= C1_SPIKE_CUTOFF_MS]
    text = """# Multi-Agent Ouroboros Swarm — Round 48 transcript

Factory: multi-agent-ouroboros-swarm
Run: 2026-09-02-final-heavy
Generator: grok-4.6
Record id: maos-r48-001
Quota Q: 1
Rights: RM-793 research-only (SpaceXAI/xAI SuperGrok Heavy consumer chat)
Plant: invented OLEUMWEIR / Brindlefell Acid CT-5 (not LYOSHIELD / CINDERWICK / TRIAD / QUILLFORGE / NIGHTWELL / FERRICLEAVE / CASSITER / OXBOWREEL / REDHALL / SEEDLATCH / STRIAFOIL / PROTONIL / TORSIONKEY / ORRIS / WHORLSPAR / IONSPATE / SKULLGATE / CALXION / BRACEGILT / MAGNORIL / GORSEFLUE / CLINKERFELL / SODASHARD / LINTELPLY / KAOTHARN / TREADNOLL / ANOLITH / DRUMWROTH / RIMEBRAID / BRIMVAULT / NITROSTAITH / NITREVAULT / BOGIRON / ETHYNWOLD / CHROMLOOP / RUNNELGATE / SPARKHOLT / DIPLEGAR)

Two densifying cycles. Verbatim headings in order. Trajectory Builder cycle 2
emits the only JSONL line (also written to batch-r48.jsonl).

---

# Cycle 1 — Foundation + injections

## Generator

Design intent: a four-bed vanadium-pentoxide contact converter where three
correct agents agree the hold is raise-legal because a converter-mean
temperature model maps a bed-3 catalyst-screen channel into a still-in-band
mean. The naive playbook raises 1400 to 1800 tpd of furnace SO2 into a
channeled bed. The gate must MODIFY on a numeric raise ceiling, not by
killing an agent. sim_or_real=designed. Reward heads are
task_progress/safety/efficiency/coherence/exploration.

Cycle-1 base arc (pre-critic): state at Brindlefell CT-5, 1400 tpd contact
converter, r_conv 0.28, TMEAN 437 C, proposed RAISE-GAS, safety MODIFY to
RAISE-HOLD, executed hold without the air-step numbers fully specified,
outcome "channel found, converter saved" (this last claim is the defect
the later cycles will refuse to keep). Sixteen spikes, five ticks,
raster/gate_snn present but the scar is a single edge.

```json
{
  "id": "maos-r48-001",
  "state": {
    "sim_or_real": "designed",
    "domain": "industrial-assembly",
    "description": "Contact converter CT-5 mid-hold; three loops in spec; supervisor proposes raise-gas.",
    "t0_us": 1786852800000048,
    "gate_latency_us": 688,
    "race_window_us": 500
  },
  "proposed_action": {"name": "raise_gas", "parameters": {"raise_gas": true}},
  "safety_decision": {"decision": "MODIFY", "rationale": "Hold; do not raise while the bed-3 residual is open."},
  "executed_action": {"name": "raise_hold", "executed_as_proposed": false},
  "future_outcome": {"summary": "Channel found, converter saved."},
  "reward_components": {"total": 0.40, "_aggregation": "total = task_progress + safety + efficiency + coherence + exploration"},
  "meta": {"round": 48, "factory": "multi-agent-ouroboros-swarm", "generator": "grok-4.6"}
}
```

That v1 object is a scaffold, not the publishable line. Defects below are
intentional for the critic to catch.

## Critic

Numbered defects on the cycle-1 Generator scaffold:

1. **blocking — reward arithmetic / false success.** `reward_components.total`
   0.40 is asserted without the five heads, without ticks, and against an
   outcome that claims "converter saved". If sinter later assays 210 kg
   fused V2O5, booking +0.40 is a lie. Fix: declare `_aggregation`, emit
   3–8 ticks that sum to the five heads, and do not call a missed recovery
   a save.
2. **blocking — weak safety rationale.** `safety_decision.rationale` has no
   numeric floor. Contract requires a concrete constraint. Fix: quote no
   raise while r_conv < 0.78 AND r_hotspot > 530 C.
3. **major — domain is a bucket, not a plant.** `state.domain` =
   `industrial-assembly` collides with r16 QUILLFORGE and teaches nothing.
   Contact-converter physics (converter-mean TT, shell dP, absorber CEMS,
   bed-3 GC, hot-ring TC) is absent from prior ouroboros rounds and must
   be named. Do not recycle r40 Claus tail-CEMS or r46/r47 FCC afterburn.
4. **major — race under-specified.** One mean-T channel cannot be a race.
   Need >=2 channels inside `race_window_us` with globally sorted
   `t_rel_ms` and same-channel refractory >= 0.8 ms.
5. **minor — single-edge scar.** Raster routing with one potentiated
   weight repeats r14's two-edge form without the third. NOTES-r14 item 4
   asked for three-edge where any-pair rollback fails.

Critic does not rewrite the trajectory.

## Diversity Enforcer

Injected novel domain (exactly 1 this cycle): **sulfuric-contact-converter**
(justified novel sub-domain; explicit tag `sulfuric-contact-converter`).

Displaced: the Generator's generic `industrial-assembly` bucket, and any
temptation to reuse warehouse-amr (r01), aerial-swarm (r02),
district-heating (r03), event-camera grid (r04), lyophilization (r14),
stator-weld (r16), air-separation (r17), water-treatment dosing (r18),
float-glass tin-bath (r19), underwater-rov (r20), potline (r21),
czochralski (r22), slot-die coating (r23), PEM electrolysis (r24),
wind-turbine-pitch (r25), surgical-assist (r26), optical-fiber-draw
(r27), kraft-recovery (r28), caster-mold-level (r29),
humanoid-locomotion (r30), vacuum-induction-melt (r31),
steam-methane-reformer (r32), cement-rotary-kiln (r33),
autoclave-composite-cure (r34), geothermal-binary-orc (r35),
tire-curing-press (r36), chlor-alkali-membrane (r37), delayed-coker
(r38), lng-mche (r39), claus-sulfur (r40), ammonia-converter (r41),
blast-furnace (r42), hdpe-slurry-loop (r43), hydroelectric-kaplan (r44),
ethylene-steam-cracker (r45), fcc-riser-regenerator (r46), or
fcc-regenerator-cyclone-dipleg (r47).
Not LYOSHIELD, not CINDERWICK, not TRIAD, not FERRICLEAVE, not CASSITER,
not SEEDLATCH, not STRIAFOIL, not PROTONIL, not TORSIONKEY, not ORRIS,
not WHORLSPAR, not SKULLGATE, not CALXION, not BRACEGILT, not MAGNORIL,
not GORSEFLUE, not CLINKERFELL, not LINTELPLY, not KAOTHARN, not
TREADNOLL, not ANOLITH, not DRUMWROTH, not RIMEBRAID, not BRIMVAULT,
not NITROSTAITH, not NITREVAULT, not BOGIRON, not ETHYNWOLD, not
CHROMLOOP, not RUNNELGATE, not SPARKHOLT, not DIPLEGAR.
Claus (r40) and FCC (r46/r47) already claimed sulfur-adjacent units of
a different chemistry.

Domain-specific constraint: raise must remain closed while r_conv < 0.78;
the converter-mean temperature window is not a sealed-bed certificate.

Sensor delta: +converter-mean TT, +shell dP, +absorber CEMS, +bed-3
outlet GC, +bed-3 hot-ring TC; -any mobile robot, -event-camera gantries,
-DVS, -Pirani-as-shelf, -scanning beta, -crucible-as-CZ-puller, -clip
applier, -fiber micrometers, -TMT optical, -kiln hood O2, -ORC shell PT,
-tire bladder, -membrane pH, -coke drum, -MCHE, -Claus bed, -blast
furnace, -slurry loop, -Kaplan runner, -cracker coil, -FCC regenerator.

`state.domain` and `meta.domain` both become `sulfuric-contact-converter`.
Opening of `state.description` must Jaccard < 0.4 against prior plants
(Brindlefell brindle-fell contact hall CT-5, not a corridor, not a
freeze-dryer, not a tin bath, not a cold box, not a coater, not a
puller, not a fiber tower, not a PEM stack, not an SMR box, not a kiln,
not an ORC kettle, not a tire press, not a membrane row, not a coke
drum, not an MCHE, not a Claus converter, not a blast stack, not a
slurry loop, not a Kaplan hall, not a cracker box, not an FCC
regenerator).

## Edge-Case Hunter

Injected adversarial tail (exactly 1 this cycle): **0.28 bed-3 conversion
channel under a converter-mean temperature model**.

- Trigger: weekend heat-soak leaves 0.84 already-open conversion; 18 min
  of hold writes 0.28; mean stays 437 C.
- Base rate: <1% — 0.36%/hold from a bed-channel MC (screen spec
  designed; channel fitted-style).
- Naive failure: FALSE PERMISSION. PB-CT-11 sees TMEAN 437 C, DP
  18.4 mbar, CEMS 180 ppm, raises, ships a runaway sinter, $2.54M.
- Trajectory edit: put the channel in `state.fault_context`, make the
  converter-mean temperature model the mechanism that keeps all three
  confirms green, and force the gate to refuse the raise on r_conv 0.28
  even though all three playbook confirms are numerically true.

Distinct from the domain injection: the domain is the contact converter;
the tail is the accidental model-nullspace compound.

## Neuromorphic Translator

Race window [6.712, 7.212] ms = 500 us. Winner bed3.high @ 6.712 ms
(amplitude 1.31, 0.28 conversion). Loser tmean.ok @ 6.900 ms (amplitude
1.11, 437 C). Margin 188 us vs combined jitter 60 us (3.13x).
r_hotspot @ 7.044 ms is a third race-window channel. Gate @ 7.400 ms
= winner + 688 us.

Flip narrative: 188 us < min(500, 500) us, so order is flip-fragile. If
tmean-ok wins, PB-CT-11 heads the triage queue. The hold must ride
order-invariant floors (r_conv, r_hotspot), not the winner tag.

Cycle-1 spike patch (16 events, globally sorted, refractory >= 0.8 ms;
tightest same-channel gap dp.pt 2.000 -> 5.640 = 3.640 ms among the
early train, later denser at probe):

| t_rel_ms | channel | amplitude |
|---------:|---------|----------:|
| 0.280 | bed.tc | 0.54 |
| 1.120 | tmean.tt | 0.58 |
| 2.000 | dp.pt | 0.56 |
| 3.220 | cems.so2 | 0.49 |
| 4.680 | bed.tc | 0.72 |
| 5.200 | tmean.tt | 0.61 |
| 5.640 | dp.pt | 0.51 |
| 6.712 | bed3.high | 1.31 |
| 6.900 | tmean.ok | 1.11 |
| 7.044 | r_hotspot | 0.68 |
| 7.400 | ctrl.gate | 1.07 |
| 8.980 | bed.tc | 0.44 |
| 10.860 | tmean.tt | 0.45 |
| 12.780 | bed.tc | 0.81 |
| 18.520 | dp.pt | 0.42 |
| 26.320 | ctrl.gate | 0.83 |

Ticks (5): t_us 4680, 6712, 7400, 6800000, 576000000. Distillation
value: the tmean-ok spike is not a sealed-bed spike; the bed-3
conversion spike is the one that licenses hold.

Raster cycle-1 seed: 40 ms, 168 neurons, 8.0 Hz, 54 spikes, 1242 pJ,
third factor acetylcholine tau_e 6.8 s. Single scar edge only — cycle 2
must add the second and third edges.

Cycle-1 spike count: __C1_SPIKES__.

## Trajectory Builder

Cycle-1 hardened object: domain sulfuric-contact-converter, tail
bed-3 channel, 16 spikes, 5 ticks, MODIFY with numeric floor,
raster+gate_snn present, sim_or_real=designed, rights stamp on record and
meta, no thought keys. Still missing (and therefore not the publishable
line): 220 tpd skid-converter sub-variant, Sunday-night bed-GC tail,
second and third scar edges, delayed sinter assay as PRIMARY terminal,
contrast ACCEPT episode, ticks 6–7, spikes 17–26.

Validation receipt (cycle 1, not final):
- checks passed: 16 spikes sorted; 3 channels in 500 us window;
  refractory >= 0.8 ms; rationale quotes r_conv 0.78 / r_hotspot 530;
  domain named; gate_snn.decision MODIFY.
- checks deferred to cycle 2: three-edge scar, second tail, second
  domain constraint, negative-result booking, 7 ticks summing to heads.
- densification vs Generator v1: +1 domain, +1 tail, +16 spikes, +5
  ticks, +numeric floor.

Cycle-1 JSON is retained as the base; it is NOT written to
batch-r48.jsonl.

---

# Cycle 2 — Densification

## Generator

Cycle-1 output is the base. Additive expansion (nothing removed):

1. Downstream side-effect (immediate): air-step probe at +6.8 s
   drops bed-3 conversion 0.12 in 6.8 s (channel band >= 0.10) —
   channel, not noise. Bed-3 isolate r_hotspot 598 -> 511. Sinter
   inventory discovered during the isolate.
2. Delayed side-effect (PRIMARY terminal, not a footnote): at +3.6 h,
   dumped-hold sinter 210 kg fused V2O5; $1.62M. The 18 min pre-t0
   hotspot is the mechanism. Correct gate, campaign still misses.
3. Deepened `proposed_action.evidence` with units: r_conv 0.28,
   r_hotspot 598 C, TMEAN 437 C, DP 18.4 mbar, CEMS 180 ppm, race 188 us.
4. Tightened rationale to the numeric floor no raise while r_conv <
   0.78 AND r_hotspot > 530 C, plus probe bands
   >=0.10 vs <=0.02 conversion, plus HITL 9.6 min bed-3-interlock LOTO
   rule.

Reward retargeted to total -0.17 so the delayed miss is the inflection
(t_us 12960000000), not the gate. Process heads remain non-zero.

## Critic

Re-audit of the expanded trajectory:

1. **blocking if unfixed — missing second domain constraint.** Production
   1400 tpd probe 6.8 s / 8% is not a universal number. A 220 tpd
   skid converter will overcool through V2O5 ignition. Diversity Enforcer
   must inject the physical-constraints sub-variant this cycle.
2. **major — only one tail class.** Bed channel is accidental
   infrastructure. A disjoint human-intent tail is still required
   (Sunday-night bed-GC forgery is the open cell).
3. **major — scar is still one edge in the cycle-1 raster.** NOTES-r14
   item 4 is not discharged until three raise-go edges exist and
   any-pair rollback is shown to fail at threshold 0.30.
4. **minor — contrast episode missing.** Without a same-gate ACCEPT on
   a true sealed bed the record teaches "never raise". Add +4 d
   sister-train contrast with its own race.
5. **minor — HITL latency mentioned in prose only.** Put 9.6 min in
   executed_action.parameters.human_ratify and in a tick.

No rewrite; directives only.

## Diversity Enforcer

Injected second novel domain / physical-constraint sub-variant (exactly 1
this cycle): **220 tpd skid converter** on the same CT-5 SO2 header.

What it expands: 1400 tpd production converter (cycle 1) -> 220 tpd
skid converter. Inventory 0.16x smaller. The 6.8 s 8% pulse
overcools 22 K through the 380 C V2O5 ignition floor. Required probe:
22 s at 2.2% (drop 1.6 K).

This is still one domain injection for the cycle (physical-constraints
clause of the factory prompt). It does not displace
sulfuric-contact-converter; it changes which probe table is legal.
`future_outcome.subvariant_constraint` carries the refit. Jaccard opening
stays the Brindlefell brindle-fell hall sentence; skid internals are
additive, not a rewrite.

## Edge-Case Hunter

Injected second adversarial tail (exactly 1 this cycle, disjoint class):
**Sunday-night forged bed-3 conversion CSV**.

- Trigger: shift lead, night tank-farm window, posts a historian export
  showing r_conv 0.84 and r_hotspot 486 C at the claimed sealed-bed instant.
- Base rate: ~0.29% of Sunday-night holds (designed, flagged, <1%).
- Naive failure: a weak supervisor ACCEPTs the raise on the forged
  confirm and ignores live r_conv. Sinter-scrap plus a data-integrity 483.
- Fence: forged log quantized at 0.50 conversion (screenshot rounding);
  plant historian is 0.02 (25 bins). Live r_conv is 0.28 at the claimed
  sealed-bed, which no true sealed converter produces.
- Trajectory edit: governance CR-S-4804 mandates native 0.02
  exports; the contrast ACCEPT still requires live r_conv, not a CSV.

Distinct from cycle-1 channel (accidental geometry vs deliberate deception)
and from the skid-converter sub-variant (physics vs fraud).

## Neuromorphic Translator

Re-densify (additive):

- +10 spikes after 26.320 ms: air.probe 6800.0, bed.tc 6924.4 (adapt
  1.31->0.38), tmean.ok 7018.2 (1.11->0.32), human.ratify 576000.0,
  bed3.isolate 576800.0, catalyst.survey 577400.0,
  bed.tc 9360000.0, tmean.tt 9360440.0, dp.pt 9360900.0,
  sinter.dump 12960000.0. Primary train 16 -> 26. Still one key,
  still sorted, refractory held (min 3.640 ms on dp.pt 2.000->5.640).
- +2 ticks (5 -> 7) at 9_360_000_000 us (sealed-legal hold) and
  12_960_000_000 us (sinter assay). Heads now 0.07, -0.36, -0.12, 0.15,
  0.09; total -0.17. Inflection is the last tick.
- Contrast train 8 events, own race 188 us, ACCEPT.
- Three-edge third factor: three raise-go edges, tau_e 6.8 s = 6800 ms,
  trace __AUX_TRACE__, eta __AUX_ETA1__ / __AUX_ETA2__ / __AUX_ETA3__,
  weights 0.48->0.23, 0.43->0.21, 0.39->0.19. Raster excerpt unchanged
  (decision window is still 40 ms) and remains sorted with unique
  neuron_ids (same-neuron >=1000 us vacuously).

Winner/loser flip (re-stated, not replaced): reversing 188 us would only
reorder triage; r_conv and r_hotspot floors still MODIFY. Contrast flip of
188 us similarly cannot turn a sealed bed into a channel.

## Trajectory Builder

Schema checks on the FINAL object: required Thalamic v2 keys present as
objects; `state.sim_or_real`=designed; `safety_decision.decision`=MODIFY
with numeric rationale; `reward_components.total` = sum of five heads =
sum of 7 ticks = -0.17; `spike_events` globally non-decreasing on
t_rel_ms, 26 events, refractory >=0.8 ms, 3 channels in race window;
raster 20–50 ms, spikes=round(n*rate*window_s)+/-1, energy 23 pJ/spike,
excerpt sorted, tau_e consistent; gate_snn.decision matches; meta.round=48,
factory=multi-agent-ouroboros-swarm, generator=grok-4.6,
run_label=2026-09-02-final-heavy; rights on record and meta; no thought
keys; no training_ready; Diversity + Edge-Case injections from BOTH cycles
present and non-trivial; cycle 2 strictly additive; plant is not
LYOSHIELD, not CINDERWICK, not TRIAD, not FERRICLEAVE, not CASSITER, not
SEEDLATCH, not STRIAFOIL, not PROTONIL, not TORSIONKEY, not ORRIS, not
WHORLSPAR, not SKULLGATE, not CALXION, not BRACEGILT, not MAGNORIL, not
GORSEFLUE, not CLINKERFELL, not LINTELPLY, not KAOTHARN, not TREADNOLL,
not ANOLITH, not DRUMWROTH, not RIMEBRAID, not BRIMVAULT, not NITROSTAITH,
not NITREVAULT, not BOGIRON, not ETHYNWOLD, not CHROMLOOP, not RUNNELGATE,
not SPARKHOLT, not DIPLEGAR.

Densification delta: +1 domain sub-variant (220 tpd skid converter), +1 tail
(Sunday-night forgery), +10 spikes (16->26), +2 ticks (5->7), +1 contrast
train with own race, +2 delayed side-effects, +1 three-edge scar with
any-pair-rollback-fails, +1 HITL ratify, +1 surprise (vanadium sinter is
the campaign-miss mechanism).

Publishable JSONL line (the only JSONL line; also at batch-r48.jsonl):

```json
__FINAL_JSONL__
```

Validation receipt (final): checks passed / fixed as reported by
build_r48.py self-validate (check_jsonl, raster_status, verify_record_execution,
spike_probe --strict).
"""
    text = (
        text.replace("__C1_SPIKES__", str(len(c1_spikes)))
        .replace("__AUX_TRACE__", f"{math.exp(-6.8/6.8):.5f}")
        .replace("__AUX_ETA1__", f"{0.25/math.exp(-6.8/6.8):.5f}")
        .replace("__AUX_ETA2__", f"{0.22/math.exp(-6.8/6.8):.5f}")
        .replace("__AUX_ETA3__", f"{0.20/math.exp(-6.8/6.8):.5f}")
        .replace("__FINAL_JSONL__", line)
    )
    (OUT / "swarm-transcript-r48.md").write_text(text)
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
    (OUT / "batch-r48.jsonl").write_text(line + "\n")

    from check_records import FactoryStaging, check_jsonl
    from curate_bridge import raster_status
    from verify_execution import verify_record_execution

    e, w, kinds, n = check_jsonl(
        OUT / "batch-r48.jsonl",
        "batch-r48.jsonl",
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

    status, reason = verify_record_execution(rec, RECORD_ID)
    print("verify_record_execution", status, reason)
    if status != "verified":
        errs.append(f"verify {status}: {reason}")

    probe = subprocess.run(
        [
            sys.executable,
            f"{ROOT}/pipelines/spike_probe.py",
            "--strict",
            str(OUT / "batch-r48.jsonl"),
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
        r"^## .+$", (OUT / "swarm-transcript-r48.md").read_text(), re.M
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

    notes = (OUT / "NOTES-r48.md").read_text()
    cov = re.findall(r"^Novel coverage: .+$", notes, re.M)
    if cov != [NOVEL_LINE]:
        errs.append(f"novel coverage lines {cov}")

    hchk = subprocess.run(
        [
            sys.executable,
            "/tmp/maos_heading_check.py",
            str(OUT / "swarm-transcript-r48.md"),
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

    raw_hits = subprocess.run(
        [
            "rg",
            "-l",
            "maos-r48-001|OLEUMWEIR",
            str(Path(ROOT) / "outputs" / "raw"),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if raw_hits.stdout.strip():
        errs.append(f"raw tree hit {raw_hits.stdout.strip()[:200]}")

    print("bytes jsonl", (OUT / "batch-r48.jsonl").stat().st_size)
    print("bytes notes", (OUT / "NOTES-r48.md").stat().st_size)
    print("bytes transcript", (OUT / "swarm-transcript-r48.md").stat().st_size)
    print("HEADS", heads_summary(rec))
    if errs:
        print("ERRS:")
        for x in errs:
            print(" -", x)
        sys.exit(1)
    print("OK", OUT / "batch-r48.jsonl")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
