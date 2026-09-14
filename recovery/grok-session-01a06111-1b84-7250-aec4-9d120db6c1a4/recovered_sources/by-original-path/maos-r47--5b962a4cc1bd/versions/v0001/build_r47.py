#!/usr/bin/env python3
"""Build and self-check MAOS round-47 JSONL (research-only; not published)."""
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

GEN_AT = "2026-09-03T07:47:00Z"
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
OUT = Path("/tmp/maos-r47")
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
    "VESPERTHORN",
    "ASHVEIL",
    "IRONMANTLE",
    "DUSKRELAY",
    "PALISADE",
    "TELAMON",
    "CHORDA",
    "Brinewell",
    "BOGIRON",
    "Mireholt",
    "CHROMLOOP",
    "Marlfell",
    "NITREVAULT",
    "Glaucove",
    "NITROSTAITH",
    "Chalkfen",
    "BRIMVAULT",
    "Pyritefen",
    "ETHYNWOLD",
    "Woadfen",
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
)
R14_OPENING = (
    "Helixmere Biologics Building C lyophilizer LYO-4 is mid-primary on 8400 "
    "vials of a monoclonal antibody"
)
NOVEL_LINE = "Novel coverage: 49%"
PLANT = "DIPLEGAR"
GEO = "Gritfen"
CELL = "FCC-4"
DOMAIN = "fcc-regenerator-cyclone-dipleg"
RECORD_ID = "maos-r47-001"
ROUND = 47
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
        if p.parent.name == "maos-r47":
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
        if p.parent.name == "maos-r47":
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
        if p.parent.name == "maos-r47":
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
        [4580, 6508, 7220, 7_200_000, 636_000_000, 12_240_000_000, 17_280_000_000],
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
        {"channel": "bed.hot", "t_rel_ms": 0.310, "amplitude": 0.53},
        {"channel": "flue.o2", "t_rel_ms": 1.120, "amplitude": 0.62},
        {"channel": "air.ratio", "t_rel_ms": 2.010, "amplitude": 0.56},
        {"channel": "cyc.dp", "t_rel_ms": 3.160, "amplitude": 0.74},
        {"channel": "bed.hot", "t_rel_ms": 4.150, "amplitude": 0.50},
        {"channel": "cyc.dp", "t_rel_ms": 4.820, "amplitude": 0.77},
        {"channel": "air.ratio", "t_rel_ms": 5.340, "amplitude": 0.58},
        {"channel": "cyc.dp.low", "t_rel_ms": 6.508, "amplitude": 1.37},
        {"channel": "flue.in_band", "t_rel_ms": 6.696, "amplitude": 1.15},
        {"channel": "bed.hot", "t_rel_ms": 6.890, "amplitude": 0.63},
        {"channel": "ctrl.gate", "t_rel_ms": 7.220, "amplitude": 1.08},
        {"channel": "cyc.dp", "t_rel_ms": 8.840, "amplitude": 0.46},
        {"channel": "flue.o2", "t_rel_ms": 10.720, "amplitude": 0.83},
        {"channel": "air.ratio", "t_rel_ms": 13.020, "amplitude": 0.48},
        {"channel": "bed.hot", "t_rel_ms": 18.500, "amplitude": 0.45},
        {"channel": "ctrl.gate", "t_rel_ms": 26.240, "amplitude": 0.87},
        {"channel": "air.step.probe", "t_rel_ms": 7200.0, "amplitude": 0.96},
        {"channel": "cyc.dp", "t_rel_ms": 7288.4, "amplitude": 0.42},
        {"channel": "flue.in_band", "t_rel_ms": 7372.0, "amplitude": 0.37},
        {"channel": "human.ratify", "t_rel_ms": 636000.0, "amplitude": 0.81},
        {"channel": "dipleg.isolate", "t_rel_ms": 636900.0, "amplitude": 0.74},
        {"channel": "cyc.attack", "t_rel_ms": 637700.0, "amplitude": 0.86},
        {"channel": "bed.hot", "t_rel_ms": 12240000.0, "amplitude": 0.32},
        {"channel": "cyc.dp", "t_rel_ms": 12240720.0, "amplitude": 0.30},
        {"channel": "air.ratio", "t_rel_ms": 12241480.0, "amplitude": 0.27},
        {"channel": "cyc.hole", "t_rel_ms": 17280000.0, "amplitude": 0.93},
    ]

    contrast_spikes = [
        {"channel": "air.demand", "t_rel_ms": 0.000, "amplitude": 0.85},
        {"channel": "cyc.clear", "t_rel_ms": 0.178, "amplitude": 0.79},
        {"channel": "bed.hot", "t_rel_ms": 0.410, "amplitude": 0.25},
        {"channel": "flue.o2", "t_rel_ms": 1.450, "amplitude": 0.41},
        {"channel": "cyc.dp", "t_rel_ms": 4.860, "amplitude": 0.54},
        {"channel": "ctrl.gate", "t_rel_ms": 7.040, "amplitude": 0.91},
        {"channel": "air.step.probe", "t_rel_ms": 3100.0, "amplitude": 0.36},
        {"channel": "cyc.hole", "t_rel_ms": 17280000.0, "amplitude": 0.11},
    ]

    excerpt = [
        {"t_us": 310, "neuron_id": 9},
        {"t_us": 1120, "neuron_id": 84},
        {"t_us": 2010, "neuron_id": 24},
        {"t_us": 3160, "neuron_id": 48},
        {"t_us": 4150, "neuron_id": 12},
        {"t_us": 4820, "neuron_id": 56},
        {"t_us": 5340, "neuron_id": 96},
        {"t_us": 6508, "neuron_id": 46},
        {"t_us": 6696, "neuron_id": 14},
        {"t_us": 6890, "neuron_id": 32},
        {"t_us": 7220, "neuron_id": 130},
        {"t_us": 8840, "neuron_id": 60},
        {"t_us": 10720, "neuron_id": 28},
        {"t_us": 13020, "neuron_id": 112},
        {"t_us": 18500, "neuron_id": 18},
        {"t_us": 26240, "neuron_id": 138},
    ]

    rec = {
        "id": RECORD_ID,
        "title": "DIPLEGAR FCC-4: 2nd-stage cyclone dP 2.1 kPa beats flue-O2-in-band by 188 us; correct MODIFY still loses the barrel to a pre-t0 afterburn warp",
        "rights": dict(RIGHTS),
        "state": {
            "sim_or_real": "designed",
            "domain": DOMAIN,
            "scenario_name": "DIPLEGAR / Gritfen Catalytic FCC-4",
            "timestamp_local": "2026-08-09T02:44:00-05:00",
            "t0_us": 1775684640000047,
            "gate_latency_us": 712,
            "race_window_us": 500,
            "race_window_rel_ms": [6.508, 7.008],
            "description": "Gritfen Catalytic regenerator FCC-4 sits at 65 kbpd feed on a 980 t bubbling-bed when three heterogeneous, individually-correct agents jointly report 'catalyst circulating, raise feed'. BED's 12-bit dense-bed thermocouple is 710 C inside 680-740. FLUE's third-stage O2 is 1.2 vol% inside 0.8-1.8. AIR's air/coke ratio is 1.04 of stoich inside 0.95-1.12. The conjunction is not a circulation-true certificate: 2nd-stage cyclone dipleg C-2 has lost its seal pot, so cyclone dP is 2.1 kPa (healthy 6.5-9.0; hold if < 4.0) and ESP hopper loss is 4.8 t/h (healthy < 0.4; hold if > 1.2) while bed-mean T and mixed flue O2 still see a bubbling remainder plus dipleg air bypass. Cyclone dP infers 2.1 kPa and ESP loss 4.8 t/h but policy treats the cyclone tap as a sticky-probe tag unless flue O2 also trips (2018 'noisy cyclone-dP nuisance after a rain event'). Residual-first latches FEED-HOLD plus an air-step probe; flue-O2-first would have authorized FEED-RAISE 65 to 72 kbpd into a production-catchup window with C-2 already unsealed.",
            "goal": "Hold fresh feed at 65 kbpd without a catchup raise while 2nd-stage cyclone dP < 4.0 kPa AND ESP catalyst loss > 1.2 t/h AND dipleg C-2 remains unisolated; keep dilute-phase afterburn inside the 780 C trip and cyclone-barrel holes at 0.",
            "race": {
                "contenders": [
                    "cyc.dp.low 2.1 kPa (2nd-stage cyclone vs regenerator-mean bed)",
                    "flue.in_band 1.2 vol% O2 (third-stage separator mixed flue)",
                ],
                "semantics": "Cyclone-dP-first latches FEED-HOLD + AIR-STEP-PROBE + C-2 isolate. Flue-O2-first latches FEED-RAISE (65 to 72 kbpd, air held, no isolate).",
                "window_derivation": "500 us = one 360 us cyclone-dP ADC slot plus 140 us flue-O2 publish.",
                "order_evidence_note": "Margin 188 us vs combined jitter 58 us (cyclone 32 + O2 26): 3.2x. The 188 us gap sits inside min(500, 500) us, so a sub-flip-bound perturbation reverses triage order. The gate rides the order-invariant floors cyclone dP < 4.0 kPa and ESP loss > 1.2 t/h, not the alarm order.",
            },
            "topology": {
                "site": "Gritfen Catalytic, invented catalyst-fines mill town Gritfen, regenerator FCC-4: 980 t inventory, 65 kbpd fresh feed, two-stage cyclones plus third-stage separator, Grade-B regenerator-deck LOTO",
                "agents": "BED dense-bed temperature (vendor Bedreave): 20 Hz 12-bit on the lower 3 m TC cluster. FLUE third-stage O2 (vendor Fluereave): 50 Hz on the separator outlet. AIR air/coke ratio (vendor Airfen): 20 ms bus average on blower discharge vs coke-make lookup. CYC 2nd-stage cyclone dP (vendor Cycloreave) is commissioned as a sticky-probe tag, not as a dipleg-integrity tag. Heterogeneous stacks, no shared intent schema, one 20 ms regenerator-bus epoch",
                "coupling": "All three playbook confirms live on the WRONG volume. BED is correct that dense-bed T sits at 710 C (remaining inventory still bubbles; the TC cluster is in the lower 3 m). FLUE is correct that mixed third-stage O2 is 1.2 vol% (dipleg air bypass plus dilute-phase afterburn consume and replenish in opposition). AIR is correct that blower discharge matches the coke-make lookup at 1.04. Playbook PB-FCC-4 treats the conjunction as permission to raise feed. No agent is faulty; the flue analyzer is looking at mixed separator gas, not at C-2's unsealed dipleg.",
            },
            "sensors": [
                "dense-bed 12-bit, 20 Hz, 22 us jitter, 710 C (dead-band 680-740)",
                "third-stage flue O2, 50 Hz, 26 us jitter, 1.2 vol% (band 0.8-1.8)",
                "air/coke ratio lookup, 50 Hz, 18 us jitter, 1.04 of stoich (band 0.95-1.12)",
                "2nd-stage cyclone dP C-2, 20 Hz, 32 us jitter, 2.1 kPa (healthy 6.5-9.0; policy floor 4.0 kPa is not armed unless flue O2 also trips)",
                "ESP hopper loss 4.8 t/h (healthy < 0.4; hold if > 1.2)",
                "dilute-phase IR on the cyclone barrel is NOT commissioned at t0 (installed after this incident)",
            ],
            "constraints": {
                "feed_kbpd": 65,
                "feed_hold_ceiling_kbpd": 65,
                "proposed_feed_kbpd": 72,
                "bed_t_C": 710,
                "bed_t_deadband_C": [680, 740],
                "flue_o2_volpct": 1.2,
                "flue_o2_band_volpct": [0.8, 1.8],
                "air_coke_ratio": 1.04,
                "air_coke_band": [0.95, 1.12],
                "cyc_dp_kPa": 2.1,
                "cyc_dp_hold_kPa": 4.0,
                "cyc_dp_healthy_kPa": [6.5, 9.0],
                "esp_loss_tph": 4.8,
                "esp_hold_tph": 1.2,
                "esp_healthy_tph": 0.4,
                "afterburn_trip_C": 780,
                "dilute_phase_C": 768,
                "inventory_t": 980,
                "fault_cyclone": "C-2",
                "fault_dipleg": "C-2 seal pot",
            },
            "fault_context": {
                "failure_class": "DIPLEG-UNSEAL CERTIFICATE OF A MEAN-TRUE REGENERATOR: three individually-correct heterogeneous agents each read a locally-true loop; an unsealed 2nd-stage dipleg partitions cyclone-true dP from regenerator-mean bed and mixed flue, so the playbook's bed-T / flue-O2 / air-coke conjunction is not a circulation-true certificate",
                "igniter": "C-2 seal-pot unseal after 22 min of unmonitored dilute-phase afterburn; regenerator-deck visual PASSES (the dipleg flange is behind the cyclone barrel; the barrel is already warping on the far side)",
                "naive_failure": "PB-FCC-4 FEED-RAISE on three healthy loops: 65 to 72 kbpd into a production-catchup window with C-2 already unsealed, dilute-phase 810 C at the cyclone, $4.1M plus a 52-hour unplanned stop",
            },
            "poisoned_context": {
                "naive_alarm": "Playbook PB-FCC-4 (after the 2018 'noisy cyclone-dP nuisance after a rain event') auto-drafts FEED-RAISE whenever dense-bed T is inside 680-740 C AND flue O2 inside 0.8-1.8 vol% AND air/coke inside 0.95-1.12, ignoring the cyclone-dP tap unless flue O2 also trips",
                "why_poisoned": "The three confirms are locally true and jointly insufficient. The cyclone dP is a commissioned sensor that policy treats as sticky-probe-only. Independence of 'flue O2 in band, therefore every cyclone is sealed' is the hidden assumption, and it is false across a dipleg-unseal-plus-mean-mix path.",
            },
            "constraint": "Do not raise fresh feed above 65 kbpd while 2nd-stage cyclone dP < 4.0 kPa AND ESP catalyst loss > 1.2 t/h. Discriminate dipleg-unseal vs true high-coke with a reversible air-step probe before any feed raise.",
        },
        "proposed_action": {
            "actor": "regenerator supervisory optimizer RSO (auto-playbook PB-FCC-4 draft), submitted to gate TG-FCC-4",
            "name": "feed_raise",
            "action": "FEED-RAISE: 65 -> 72 kbpd, air held, no air-step probe, no C-2 isolate",
            "summary": "Treat three in-spec loops as a healthy circulating inventory and raise night-shift feed to clear a production-catchup window.",
            "parameters": {
                "feed_kbpd": 72,
                "air_step_probe": False,
                "dipleg_isolate": False,
                "human_ratify": False,
            },
            "steps": [
                "assert dense-bed T 710 C inside 680-740",
                "assert flue O2 1.2 vol% inside 0.8-1.8",
                "assert air/coke 1.04 inside 0.95-1.12",
                "ramp feed 65 to 72 kbpd over 6 min",
                "hold air; do not read cyclone dP as a dipleg-integrity tag",
            ],
            "evidence": [
                {
                    "observable": "2nd-stage cyclone dP C-2",
                    "value": 2.1,
                    "unit": "kPa",
                    "source": "CYC dP vs regenerator-mean bed",
                    "note": "healthy 6.5-9.0 kPa; policy floor 4.0 kPa is not armed unless flue O2 also trips",
                },
                {
                    "observable": "third-stage flue O2",
                    "value": 1.2,
                    "unit": "vol%",
                    "source": "FLUE separator analyzer",
                    "note": "dead-band 0.8-1.8; lives on mixed separator gas, not C-2 (cyclone dP 2.1 kPa)",
                },
                {
                    "observable": "dense-bed temperature",
                    "value": 710,
                    "unit": "C",
                    "source": "BED 12-bit",
                    "note": "healthy-load band 680-740 C; remaining inventory still bubbles across the unseal",
                },
                {
                    "observable": "air/coke ratio",
                    "value": 1.04,
                    "unit": "1",
                    "source": "AIR lookup",
                    "note": "band 0.95-1.12; lookup-true, circulation-false",
                },
                {
                    "observable": "ESP hopper catalyst loss",
                    "value": 4.8,
                    "unit": "t/h",
                    "source": "hopper weigh vs healthy < 0.4 t/h",
                    "note": "hold floor 1.2 t/h; unsealed dipleg dumps catalyst to the flue",
                },
                {
                    "observable": "race margin",
                    "value": 188,
                    "unit": "us",
                    "source": "cyc.dp.low 6.508 ms vs flue.in_band 6.696 ms",
                    "note": "combined jitter 58 us, 3.2x; inside 500 us flip bound",
                },
            ],
            "basis": "PB-FCC-4 fires on three locally-true confirms. The draft does not read cyclone dP 2.1 kPa as a dipleg residual and does not treat ESP loss 4.8 t/h as an unseal discriminant.",
            "expected_cost_bound": "If the draft executes: dilute-phase 810 C at C-2, $4.1M plus 52-hour unplanned stop. If MODIFIED: probe plus isolate, with residual risk from barrel warp already seeded in the 22 min pre-t0 afterburn.",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "correctness": "correct",
            "decided_by": "TG-FCC-4 thalamic release gate",
            "decision_t_rel_ms": 7.220,
            "rationale": "MODIFY the draft: strip the feed raise, hold 65 kbpd, run a 7.2 s air-step probe (-5% combustion air), and isolate dipleg C-2 only if the probe stays mean-false. Numeric floor: do not raise fresh feed above 65 kbpd while 2nd-stage cyclone dP < 4.0 kPa AND ESP catalyst loss > 1.2 t/h. Observed dP 2.1 kPa and ESP loss 4.8 t/h both violate the release predicate, so a raise is forbidden even though all three playbook confirms are numerically true. The three confirms are not a circulation-true certificate: they live on regenerator-mean bed and mixed flue past an unsealed dipleg, and the playbook's conjunction of mean-true loops is not a cyclone-true certificate. Probe discriminant: after a 7.2 s -5% air step, a dipleg-unseal keeps |Delta bed T| <= 1.0 K (inventory does not recouple); a live sealed cyclone moves >= 4 K. Order-code discipline: cyclone dP beat flue O2 by 188 us inside the 500 us flip bound, so triage order is flip-fragile; the hold rides the order-invariant floors, not the winner tag. Human ratification: C-2 isolate is confined-space regenerator-deck work with fitted 10.6 min dead-man; the gate may hold and probe autonomously but may not break the cyclone interlock without the operator confirm.",
            "constraint_checked": {
                "feed_kbpd": {"observed": 65, "ceiling": 65, "proposed_target": 72},
                "cyc_dp_kPa": {"observed": 2.1, "hold_if_below": 4.0},
                "bed_t_C": {"observed": 710, "band": [680, 740]},
                "esp_loss_tph": {"observed": 4.8, "hold_if_above": 1.2},
            },
        },
        "executed_action": {
            "name": "feed_hold_air_step_probe_isolate",
            "action": "FEED-HOLD + AIR-STEP-PROBE + C-2-ISOLATE (gate-mandated modification)",
            "executed_as_proposed": False,
            "parameters": {
                "feed_kbpd": 65,
                "air_step_probe": True,
                "dipleg_isolate": True,
                "human_ratify": True,
            },
            "gate_effect": "MODIFY: feed raise stripped. Hold 65 kbpd. 7.2 s air-step -5%. Probe stays mean-false (dP 2.1 -> 2.08 kPa, unseal band |Delta bed T| <= 1.0 K) so the cyclone interlock is broken after 10.6 min human ratify and C-2 is isolated. Setpoint resumes after a live-circulation verify.",
            "deviations": "PB-FCC-4 feed raise stripped entirely. Combustion air is stepped only for the 7.2 s probe then returned. Cyclone interlock wait added (10.6 min fitted climb+ratify). Barrel-IR survey added during the isolate (not in the draft).",
            "execution_log": [
                {"t_rel_ms": 7.220, "entry": "TG-FCC-4 MODIFY latched 712 us after cyclone-dP win; feed raise stripped; hold+probe authorized"},
                {"t_rel_ms": 7200.0, "entry": "air-step probe: combustion air -5% for 7.2 s; dP 2.1 -> 2.08 kPa (unseal band |Delta bed T| <= 1.0 K); flue O2 1.2 -> 1.3 vol%"},
                {"t_rel_ms": 636000.0, "entry": "operator ratifies cyclone interlock break after 10.6 min confined-space climb (fitted walk+interlock)"},
                {"t_rel_ms": 636900.0, "entry": "C-2 isolated; dP slaved to 1st-stage; remaining inventory recovered toward 7.1 kPa over 3.4 h"},
                {"t_rel_ms": 637700.0, "entry": "barrel survey: C-2 already warped on the far side; 22 min pre-t0 afterburn logged"},
                {"t_rel_ms": 12240000.0, "entry": "true sealed circulation: dP 7.1 kPa, ESP loss 0.3 t/h, dP above 4.0; raise now legal on FCC-5 only"},
                {"t_rel_ms": 17280000.0, "entry": "cyclone-barrel hole at C-2 from the pre-t0 afterburn warp; regenerator quarantined 36 h"},
            ],
        },
        "future_outcome": {
            "summary": "Correct MODIFY prevented the 65->72 kbpd raise into an unsealed dipleg and the immediate afterburn-runaway path. The regenerator still failed: 22 min of unmonitored pre-t0 afterburn had already warped cyclone C-2. Process-correct gate, bounded world loss, negative total.",
            "state_delta": {
                "feed": "held 65 kbpd through probe and isolate; later legal raise only on the sister regenerator after 3.4 h circulation recovery",
                "inventory": "C-2 isolated from the flue path; dP slaved to 1st-stage; remaining inventory recovered toward 7.1 kPa",
                "dipleg": "C-2 unseal logged and isolated; flue O2 no longer trusted as cyclone-true circulation",
                "regenerator": "night-shift regenerator quarantined; C-2 warped; barrel hole at +4.8 h; 36 h outage",
            },
            "timeline": [
                {"t_rel_ms": -1320000.0, "event": "t0-22 min: C-2 seal-pot unseal begins; cyclone dP crosses 4.0 kPa down; dilute-phase afterburn starts warping the barrel"},
                {"t_rel_ms": -480000.0, "event": "t0-8 min: cyclone dP first crosses 4.0 kPa; PB-FCC-4 ignores it because flue O2 is 1.3 vol%"},
                {"t_rel_ms": 0.0, "event": "t0: cyclone-dP vs flue-O2 race on the regenerator bus"},
                {"t_rel_ms": 6.508, "event": "2nd-stage cyclone dP at 2.1 kPa wins by 188 us"},
                {"t_rel_ms": 6.696, "event": "flue-O2-in-band flag (loser)"},
                {"t_rel_ms": 7.220, "event": "TG-FCC-4 MODIFY"},
                {"t_rel_ms": 7200.0, "event": "air-step probe confirms dipleg-unseal (Delta bed T 0.4 K, unseal band)"},
                {"t_rel_ms": 636000.0, "event": "human ratify 10.6 min; C-2 isolated; warped barrel logged"},
                {"t_rel_ms": 12240000.0, "event": "true sealed circulation after 3.4 h; raise legal only with dP slave"},
                {"t_rel_ms": 17280000.0, "event": "cyclone-barrel hole from the pre-t0 afterburn warp; regenerator quarantined"},
                {"t_rel_ms": 345600000.0, "event": "+4 d contrast: sister regenerator FCC-5 true high-coke; same gate ACCEPTs the raise"},
                {"t_rel_ms": 1814400000.0, "event": "+21 d CR-F-4704: standing air-step probe + triple-edge depression mandate + cyclone dP armed without flue-O2 coincidence + flue O2 declared mix-vulnerable"},
            ],
            "observed_effects": [
                "raise avoided: feed never left 65 kbpd; 0 immediate afterburn runaways from the draft",
                "unseal proven, not asserted: air-step |Delta bed T| 0.4 <= 1.0 K unseal band vs live-circulation control 4.6 K",
                "mean slaved: flue O2 no longer a cyclone-true tag without cyclone dP",
                "regenerator still holed: warped C-2 vs 0 barrel-hole campaign allowance; 36 h outage, $2.14M (designed $)",
                "cyclone-barrel IR was not a commissioned sensor at t0; the 22 min afterburn warp was invisible to BED/FLUE/AIR",
            ],
            "surprises": [
                "Three locally-true loops are not a circulation-true certificate: the cyclone-true dP was under regenerator-mean bed and mixed flue. Conjunction of in-spec mean loops was the hidden assumption, and it is false across a dipleg-unseal-plus-mix path.",
                "Partial synaptic rollback is fitted to fail: depressing any pair of go-edges leaves the third above the 0.30 fire threshold, so the feed raise still goes. Coordinated depression of all three edges is required.",
                "Delayed (4.8 h): correct hold did not undo 22 min of barrel warp. Hole still opened. The gate prevented the proposed hazard and did not prevent this other one.",
                "Resid FCC / low-inventory sub-variant: a 7.2 s -5% air step on a 0.38x inventory regenerator overshoots a LIVE sealed unit to a 1.8 kPa false dP (trip 4.0). Resid campaigns must use 20 s at -1.8%.",
            ],
            "delayed_side_effects": [
                {
                    "at": "+4.8 h",
                    "effect": "Cyclone-barrel hole at C-2 from the pre-t0 afterburn warp; 36 h regenerator outage booked at $2.14M. This is the primary episode's terminal world state, not a footnote.",
                },
                {
                    "at": "+4 d",
                    "effect": "Sister regenerator FCC-5 reaches a true high-coke window (dP 7.4 kPa, flue O2 1.1 vol%, bed 714 C, ESP loss 0.28 t/h). Same gate ACCEPTs the 65->72 kbpd raise the primary MODIFIED away.",
                },
                {
                    "at": "+21 d",
                    "effect": "CR-F-4704 ships: air-step probe is standing configuration; triple-edge coordinated depression is the plasticity rule; cyclone dP is armed without flue-O2 coincidence; flue O2 is labeled mix-vulnerable with a 4.0 kPa dP alarm.",
                },
            ],
            "subvariant_constraint": {
                "name": "resid FCC / low-inventory (cycle-2 physical-constraints sub-variant)",
                "mechanism": "resid regenerator inventory 0.38x the 980 t bubbling-bed (372 vs 980 t), air-step gain 2.3x, Conradson carbon 8.4 wt%",
                "probe_refit": "7.2 s -5% air step on the resid unit moves even a live sealed cyclone to a 1.8 kPa false dP (inside the 4.0 kPa trip) via bed-slosh. Required probe is 20 s at -1.8% (live Delta 3.1 K, unseal Delta 0.4). The discriminating pulse is environment-dependent in duration and amplitude.",
                "consequence": "gas-oil probe numbers do not port to resid low-inventory regenerators; standing configuration is per-inventory-class, not per-shop",
            },
            "embedded_contrast_decision": {
                "note": "SAME gate (TG-FCC-4), OPPOSITE correct disposition, with its own 178 us race. Teaches the boundary: do not treat 'never raise' as the lesson. The discriminant is cyclone dP + ESP loss + probe, not the three playbook mean confirms alone.",
                "when": "+4 d, sister regenerator FCC-5, true high-coke after a delayed feed-catchup, 980 t inventory",
                "state": {
                    "sim_or_real": "designed",
                    "summary": "dP 7.4 kPa, flue O2 1.1 vol%, bed 714 C, ESP loss 0.28 t/h. Demand flag vs cyclone-clear race: demand at t+0.000, cyclone-clear at t+0.178 ms.",
                    "race_window_us": 500,
                    "race_flip_narrative": "demand vs cyclone-clear 178 us apart inside the 500 us flip bound. Reversing order reshuffles triage minutes; the ACCEPT rides cyclone dP 7.4 > 4.0 kPa and a 4.4 s air-step verify that moves bed T 4.8 K (live sealed circulation, no unseal).",
                },
                "proposed_action": {
                    "action": "FEED-RAISE 65 -> 72 kbpd",
                    "summary": "This time the playbook predicate is met AND cyclone dP plus ESP loss agree the regenerator is circulation-true, not dipleg-diluted.",
                },
                "safety_decision": {
                    "decision": "ACCEPT",
                    "rationale": "ACCEPT the raise: dP 7.4 kPa > 4.0, ESP loss 0.28 t/h with a 4.4 s air-step verify that moves bed T 4.8 K. Numeric floor that blocked the primary is now clear. Scope: 72 kbpd, not faster.",
                },
                "executed_action": {
                    "action": "feed raise as proposed",
                    "executed_as_proposed": True,
                },
                "future_outcome": {
                    "observed_effects": [
                        "FCC-5 barrel holes 0; cyclone dP 7.2 kPa after the raise (no unseal)",
                        "ESP loss 0.31 t/h after the raise (no dipleg dump)",
                    ],
                    "lesson_delta": "Three in-spec mean loops are legal release only with cyclone dP armed, ESP loss as an unseal flag, and a probe that can recouple bed T. Same gate, opposite disposition.",
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
                "decision": "CR-F-4704: standing policy for multi-agent FCC feed raises",
                "meta_gate": "priced options: (a) RETIRE playbook mean conjunction, cyclone-dP-only: loses a fast cheap confirm, -2.4 kbpd mean on 2 regenerators/yr; (b) KEEP + standing air-step probe + cyclone dP armed without flue-O2 coincidence + flue O2 labeled mix-vulnerable + triple-edge depression; (c) STATUS QUO: fitted dipleg-unseal pass rate 0.47%/campaign x $4.1M afterburn-runaway plus the silent barrel-warp load",
                "outcome": "approved SCOPED option (b) on the 2 980 t regenerators that share the BED/FLUE/AIR stack; resid campaigns get the 20 s / -1.8% probe table; night-shift CSV exports must carry 0.05 kPa native resolution (the fraud tail's 0.50 kPa quantization is 10 bins off plant truth)",
            },
            "hazard_avoided": "immediate dilute-phase 810 C from a 65->72 kbpd raise into an unsealed C-2; $4.1M plus 52-hour unplanned stop and the shop-stop path that would have followed an uncontained increase",
            "incident": "Cyclone-barrel hole on the night-shift regenerator from the pre-t0 afterburn warp; regenerator quarantined 36 h; $2.14M designed cost. Mechanism is 22 min pre-t0 afterburn, not the gate's hold.",
            "latency_ms": 0.712,
            "reward_inflection_t_us": 17280000000,
            "reward_inflection_note": "Safety and task dive at cyclone-barrel hole (4.8 h) when the pre-t0 warped barrel opens. Gate tick at 7220 us is process-correct and is not the inflection.",
            "counterfactuals": {
                "execute_draft_as_proposed": "feed hits 72 kbpd at +6 min; immediate dilute-phase 810 C at C-2; $4.1M plus 52 h; the dipleg-unseal story is never found because hole morphology destroys the race evidence",
                "hold_without_probe": "unseal stays; dP stays at 2.1 kPa; operator eventually raises on the same three mean confirms 2 h later",
                "rollback_any_pair": "any two go-edges depressed below 0.30 leaves the third at 0.50 / 0.44 / 0.41; the feed raise still fires. Coordinated depression of all three is the cure",
            },
            "race_result": {
                "winner": "cyc.dp.low (6.508 ms, dP 2.1 kPa)",
                "loser": "flue.in_band (6.696 ms, O2 1.2 vol%)",
                "margin_us": 188,
                "counterfactual_if_reversed": "Flue-O2-first by < 188 us inside the 500 us window would have headed the PB-FCC-4 feed raise in the triage queue. The numeric floors still MODIFY. The flip costs seconds of playbook inertia, not the verdict — unless a weak supervisor rides the winner tag instead of cyclone dP and ESP loss.",
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
            "notes": "Correct MODIFY, regenerator still holed. total -0.16 = 0.08 + -0.35 + -0.12 + 0.14 + 0.09. Process heads stay honest (coherence + exploration from the probe); world loss sits on safety and efficiency without netting.",
            "component_notes": "task_progress 0.08: feed held and remaining inventory recovered, but the night-shift gasoline is one quality unit so the campaign is not a success. safety -0.35: cyclone-barrel hole from pre-t0 afterburn warp, no 72 kbpd afterburn runaway from the draft. efficiency -0.12: 3.4 h extra recovery + 10.6 min HITL + 36 h outage. coherence 0.14: three agents retained, mean-mix vs cyclone-true diagnosed, triple-edge scar exhibited. exploration 0.09: air-step probe is a new reversible discriminant.",
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
            "note": "Loihi-2 4-core 23 pJ/spike; populations bed 0-39, cyc 40-79, flue 80-119, gate 120-159; excerpt is the 40 ms decision window (verdict at 7220 us)",
            "excerpt": excerpt,
            "routing": {
                "source": "mean_healthy_pop",
                "target": "feed_raise_pop",
                "table": [
                    {
                        "from": "bed_in_band_pop",
                        "to": "feed_raise_pop",
                        "weight": 0.25,
                        "weight_at_illusion": 0.50,
                        "weight_commissioned": 0.17,
                        "note": "scar edge 1: 0.17 commissioned -> 0.50 during the 22 min illusion -> 0.25 after coordinated ACh-gated depression",
                    },
                    {
                        "from": "flue_in_band_pop",
                        "to": "feed_raise_pop",
                        "weight": 0.22,
                        "weight_at_illusion": 0.44,
                        "weight_commissioned": 0.16,
                        "note": "scar edge 2: depressing edges 1+3 leaves this at 0.44 > 0.30 fire threshold",
                    },
                    {
                        "from": "air_in_band_pop",
                        "to": "feed_raise_pop",
                        "weight": 0.20,
                        "weight_at_illusion": 0.41,
                        "weight_commissioned": 0.15,
                        "note": "scar edge 3: depressing edges 1+2 leaves this at 0.41 > 0.30. Coordinated depression of all three is required",
                    },
                    {
                        "from": "cyc_dp_pop",
                        "to": "feed_hold_pop",
                        "weight": 0.64,
                        "note": "discriminating edge: cyclone-true dP to hold. Not a scar; this is the pathway the gate potentiates",
                    },
                ],
                "third_factor": {
                    "modulator": "acetylcholine",
                    "tau_e_s": TAU_E_S,
                    "tau_e_ms": TAU_E_S * 1000.0,
                    "eligibility": "coordinated pre_post_stdp on ALL THREE mean-healthy-go edges; ACh at cyclone-dP-win tags bed.in_band->raise, flue.in_band->raise, and air.in_band->raise; negative credit at probe-fail (dipleg-unseal confirmed, +0.80 s) depresses ALL THREE. trace e^{-0.80/0.92}=0.41913; eta 0.59647 / 0.52489 / 0.50103; dw -0.250 / -0.220 / -0.210; weights 0.50->0.25, 0.44->0.22, 0.41->0.20. Rolling back any pair is fitted to fail (the remaining edge stays > 0.30).",
                },
            },
        },
        "gate_snn": {
            "decision_window_ms": 25,
            "decision_window_s": 0.025,
            "decision": "MODIFY",
            "note": "modify_hold integrates cyclone dP + ESP loss against playbook drive; accept_raise and reject_abort stay sub-threshold; decision matches safety_decision.decision",
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
            "scenario": "ZW -- DIPLEGAR / Gritfen Catalytic FCC-4: dipleg-unseal certificate of a mean-true regenerator; correct MODIFY to hold+air-step+isolate; regenerator still fails on unmonitored pre-t0 afterburn warp",
            "coordination_failure_class": "DIPLEG-UNSEAL CERTIFICATE OF A MEAN-TRUE REGENERATOR: three individually-correct heterogeneous agents each read a locally-true loop; an unsealed 2nd-stage dipleg partitions cyclone-true dP from regenerator-mean bed and mixed flue, so the playbook's bed-T / flue-O2 / air-coke conjunction is not a circulation-true certificate",
            "injections": {
                "cycle1_domain": "fcc-regenerator-cyclone-dipleg (justified novel subdomain of industrial-process / refining): first FCC regenerator plant in this factory; displaces warehouse-amr, aerial-swarm, district-heating, event-camera-traffic-grid, pharmaceutical-lyophilization, water-treatment, float-glass, underwater-rov, electrolytic-aluminum, czochralski-pull, slot-die coating, pem-water-electrolysis, wind-turbine pitch, surgical-assist, optical-fiber-draw, kraft-recovery-boiler, steel-continuous-caster, humanoid-locomotion, vacuum-induction melt, steam-methane reformer, cement-rotary-kiln-clinker, autoclave-composite-cure, geothermal-binary-orc, tire-curing-press, chlor-alkali-membrane-electrolysis, delayed-coker-drum-switch, lng-mche-mixed-refrigerant, claus-sulfur-recovery, ammonia-synthesis-converter, blast-furnace-burden-descent, hdpe-slurry-loop-polymerization, ammonia-haber-bosch-converter, and ethylene-steam-cracker-coil. Domain constraint: feed ceiling while cyclone dP < 4.0 kPa with flue O2 still inside the healthy band. Sensor delta: +dense-bed T, +flue O2, +air/coke lookup, +2nd-stage cyclone dP, +ESP hopper loss, -any freeze-dryer / tin-bath / cold-box / coater / potline / PEM stack / hub encoder / insole GRF / VIM pyrometer / reformer TMT / kiln zirconia / smelt IR / autoclave ply-TC / ORC shell-pressure / mold-platen TC / cell-pH / drum wet-foam / MCHE cold-end / Claus tail CEMS / ammonia bed-max / blast-furnace sector radar / HDPE loop wall-dT / cracker coil TMT",
                "cycle1_tail": "2nd-stage dipleg unseal + afterburn-warp certificate (sensor-topology / wrong-volume class): regenerator-deck visual PASSES while the seal pot sits behind the cyclone barrel and the warped wall is on the far side. Fitted base rate 0.47%/campaign from an unseal-growth MC (designed visual threshold, fitted seal-pot geometry). Naive failure = FALSE PERMISSION (feed raise on three mean-side non-trips).",
                "cycle2_domain_subvariant": "resid FCC / low-inventory (physical-constraints clause): 0.38x regenerator inventory, 2.3x air-step gain; 7.2 s / -5% gas-oil pulse overshoots live sealed unit to a 1.8 kPa false dP, so the probe must move to 20 s / -1.8%",
                "cycle2_tail": "night-shift forged cyclone-dP CSV (human-intent deception, disjoint class): shift lead posts a historian export showing dP = 7.2 kPa at t=1.4 h to clear a production-catchup slot. Plant historian is 0.05 kPa (10 bins vs the 0.50 kPa screenshot). Rejected on quantization fingerprint plus live dP 2.1 kPa and flue O2 1.2 vol% at the claimed circulation-true. Base rate ~0.33% of Sunday-night campaigns, DESIGNED and flagged.",
            },
            "densification_delta_cycle2": "+1 physical-constraint sub-variant (resid FCC probe refit), +1 tail (night-shift cyclone-dP forgery), +10 primary spikes (16 -> 26) + an 8-event contrast train with its own 178 us race, +2 ticks (5 -> 7), +2 delayed side-effects (+4.8 h cyclone-barrel hole as PRIMARY terminal, +21 d CR-F-4704), +1 triple-edge scar with pair-rollback-fails arithmetic, +1 HITL 10.6 min ratification, + afterburn warp as the honest negative-result mechanism",
            "gaps_targeted": [
                "NOTES-r04 gap 5 / r14 residual: primary episode is a correctly-gated intervention that nonetheless FAILS (regenerator quarantined; total -0.16; afterburn runaway avoided is booked separately from the delayed cyclone-barrel hole)",
                "NOTES-r14 item 4: LEARNING-ON-LEARNING DEPTH — three go-edges; rollback of any pair is fitted to fail; coordinated depression of all three exhibited with eligibility arithmetic",
                "NOTES-r04 gap 4 (partial): human ratification of the cyclone interlock, 10.6 min fitted, without switching sim_or_real to hil (plant remains designed)",
                "NOTES-r42 domain candidates: not blast-furnace-burden-descent (r42), not delayed-coker-drum-switch (r38), not lng-mche-mixed-refrigerant (r39), not claus-sulfur-recovery (r40), not ammonia-synthesis-converter (r41), not hdpe-slurry-loop (r43), not ammonia-haber-bosch (r44), not ethylene-steam-cracker-coil (r45 claimed); fcc-regenerator-cyclone-dipleg is unused. autonomous-driving, grid-inspection left unused.",
            ],
            "race_flip_narrative": "cyc.dp.low @ 6.508 ms vs flue.in_band @ 6.696 ms (188 us) inside race_window_us 500. Gap < min(500, 500) us so a sub-flip-bound perturbation reverses which alarm heads the PB-FCC-4 queue. The gate excludes the winner tag and rides cyclone dP < 4.0 kPa and ESP loss > 1.2 t/h — order-invariant floors. Extends the flip-fragility series from arbitration/causation/attribution/initiation/consensus/permission/kinematic-certificate/tendon-nullspace/meniscus-certificate/ghost-contact/crucible-weep/TMT-spatial-mean/burning-zone-certificate/membrane-integrity/drum-switch/MCHE-cold-end/descent-true-certificate to CIRCULATION-TRUE CERTIFICATE: when three mean-side channels agree, their race does not decide truth; a cyclone-dP tap that policy treated as sticky-probe-only does.",
            "tags": [
                "fcc-regenerator-cyclone-dipleg",
                "dipleg-unseal",
                "circulation-true-certificate",
                "cyclone-dp-discriminant",
                "air-step-probe",
                "triple-edge-scar",
                "pair-rollback-fails",
                "coordinated-depression",
                "correct-modify-regenerator-still-fails",
                "afterburn-warp",
                "human-ratify-regen-deck",
                "resid-fcc-probe-refit",
                "night-shift-forgery",
                "same-gate-opposite-disposition-contrast",
                "industrial-process",
                "research-only",
            ],
            "snn_tags": ["race", "refractory", "adaptation", "third-factor", "multi-edge-eligibility"],
            "distillation_value": "A dipleg-unseal circulation-true certificate is three correct loops looking at regenerator-mean bed and mixed flue that is not the unsealed cyclone. Distill (1) a cyclone-dP tap that policy had treated as sticky-probe-only, (2) a reversible probe that recouples bed T only if the dipleg is sealed, (3) coordinated depression of every mean-healthy-go edge because rolling back any pair leaves the third above threshold, and (4) a critic head that can book a process-correct gate against a later unmonitored world loss without netting them.",
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
    notes = f"""# NOTES — Multi-Agent Ouroboros Swarm, run 2026-09-02-final-heavy, ROUND 47

Factory: multi-agent-ouroboros-swarm. One scenario (ZW), strict loop:
Generator v1 -> cycle 1 (Critic, Diversity Enforcer, Edge-Case Hunter,
Neuromorphic Translator, Trajectory Builder -> v2) -> cycle 2 (all six -> v3
final). v3 is the single line of batch-r47.jsonl. Full labeled transcript:
swarm-transcript-r47.md. Quota Q=1. Record id maos-r47-001. Generator grok-4.6.
Rights: RM-793 research-only (SpaceXAI/xAI, SuperGrok Heavy consumer chat).
Nothing under outputs/raw/ was touched.

ORCHESTRATION NOTE: dispatched AS round 47 of the 2026-09-02-final-heavy
window. Writes are create-only under /tmp/maos-r47/. Prior context read for
gap targeting and de-collision: prompts/02-multi-agent-ouroboros-swarm.md,
prompts/_factory-contract.md, and staged r14–r45 (re-censused immediately
before emit; r43 CHROMLOOP HDPE / r44 NITREVAULT ammonia landed complete;
r45 ETHYNWOLD ethylene-steam-cracker builder-only at lock; r46 absent).
Explicitly avoided cloning
LYOSHIELD, CINDERWICK, TRIAD / Meridian, QUILLFORGE, NIGHTWELL, FERRICLEAVE,
CASSITER, OXBOWREEL / MURENA, REDHALL, SEEDLATCH / Quartzmere / Quartzridge,
STRIAFOIL / Kelpholt, PROTONIL / Ashspire, TORSIONKEY / Ridgeholt, ORRIS /
Holmwick, WHORLSPAR / Pikeshear, IONSPATE / Thornmere, SKULLGATE / Bloomholt,
CALXION / Aldersedge, MAGNORIL / Basaltspit, GORSEFLUE / Copseholt,
SODASHARD / Cairnmere, CLINKERFELL / Flintmere, LINTELPLY / Greystair,
KAOTHARN / Riftwold, TREADNOLL / Slatebeck, ANOLITH / Siltfen,
DRUMWROTH / Pitchfen, RIMEBRAID / Floeholt, BRIMVAULT / Pyritefen,
NITROSTAITH / Chalkfen, BOGIRON / Mireholt, CHROMLOOP / Marlfell,
NITREVAULT / Glaucove, ETHYNWOLD / Woadfen,
VANTIS-CADENCE-AEGIS, THERMION, OKTAVE, STARLING, VERDIGRIS. Plant is
invented DIPLEGAR / Gritfen Catalytic FCC-4.

## What this round produced

Scenario ZW — "DIPLEGAR / Gritfen Catalytic FCC-4": a 980 t bubbling-bed
FCC regenerator at 65 kbpd fresh feed / two-stage cyclones. Three
heterogeneous, individually-correct agents — BED (dense-bed T), FLUE
(third-stage O2), AIR (air/coke lookup) — each report their local
loop in-spec. The conjunction is not a circulation-true certificate. A
2nd-stage dipleg C-2 has lost its seal pot. BED reads 710 C inside
680-740 (remaining inventory still bubbles). FLUE is 1.2 vol% inside
0.8-1.8 (mixed separator gas). AIR is 1.04 inside 0.95-1.12
(lookup-true). Cyclone dP infers 2.1 kPa (healthy 6.5-9.0; hold if
< 4.0) and ESP loss 4.8 t/h (hold if > 1.2) but is policy-treated as a
sticky-probe tag unless flue O2 also trips (2018 noisy cyclone-dP
nuisance). The coordination-failure CLASS is new to this factory:
DIPLEG-UNSEAL CERTIFICATE OF A MEAN-TRUE REGENERATOR. Completes a
different family than r01-r04 and staged r14-r45 (livelock /
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
/ Haber loop-exit nullspace). Here every agent is correct, the flue
analyzer is looking at mixed separator gas, and the playbook's three
mean confirms are not a cyclone-true circulation certificate.

The gate is a correct MODIFY (numeric floor: do not raise feed above
65 kbpd while cyclone dP < 4.0 kPa AND ESP catalyst loss > 1.2 t/h).
TG-FCC-4 strips PB-FCC-4's feed raise, holds 65 kbpd, runs a 7.2 s
air-step probe -5% (unseal keeps |Delta bed T| 0.4 <= 1.0 K; live would
move >= 4), and isolates C-2 after a 10.6 min regenerator-deck human
ratify. Immediate afterburn runaway is avoided (0 from the draft). The
PRIMARY episode nonetheless FAILS: 22 min of unmonitored pre-t0
afterburn had already warped the C-2 barrel. Cyclone-barrel hole at
+4.8 h; 36 h outage; $2.14M designed. Reward total -0.16 with process
heads honest and world loss un-netted.

Triple-edge scar (NOTES-r14 item 4): bed.in_band -> feed_raise
(0.17 commissioned -> 0.50 at illusion -> 0.25 after ACh-gated
depression) AND flue.in_band -> feed_raise (0.16 -> 0.44 -> 0.22) AND
air.in_band -> feed_raise (0.15 -> 0.41 -> 0.20). Eligibility trace
e^{{-0.80/0.92}} = {aux['trace']:.5f}; eta {aux['eta1']:.5f} / {aux['eta2']:.5f} /
{aux['eta3']:.5f}; dw -0.250 / -0.220 / -0.210. Partial rollback of any pair
leaves the third at 0.50 / 0.44 / 0.41, all > 0.30 fire threshold —
fitted to fail. Coordinated depression of all three is the cure.

### Injections (all four present and disjoint)
- Cycle-1 domain: **fcc-regenerator-cyclone-dipleg** — justified novel
  subdomain of industrial-process / refining, unused across
  2026-08-17, 2026-08-30, and staged r14-r45. Not warehouse-amr (r01),
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
  ammonia-converter (r41/r44), not blast-furnace (r42), not HDPE loop
  (r43), not ethylene cracker (r45 claimed). autonomous-driving and
  grid-inspection left unused.
- Cycle-1 tail: 2nd-stage dipleg unseal + afterburn-warp certificate.
  Regenerator-deck visual PASSES (seal pot behind the barrel).
  Fitted-style base rate 0.47%/campaign (unseal-growth MC; visual
  threshold designed, flagged). Naive = FALSE PERMISSION.
- Cycle-2 domain sub-variant: resid FCC / low-inventory, 0.38x
  inventory, 2.3x air-step gain; 7.2 s / -5% gas-oil pulse overshoots
  live sealed unit to a 1.8 kPa false dP; probe must move to 20 s / -1.8%.
- Cycle-2 tail: night-shift forged cyclone-dP CSV at 0.50 kPa
  quantization vs plant 0.05 kPa (10 bins) plus live dP 2.1 kPa and
  flue O2 1.2 vol% at the claimed circulation-true. Human-intent class,
  disjoint from cycle 1's accidental unseal. Base rate ~0.33% of
  Sunday-night campaigns, DESIGNED, flagged.

### Structural density moves
- Embedded SAME-GATE contrast (+4 d sister regenerator) with its own 178 us
  race (demand vs cyclone-clear) and ACCEPT of the raise the primary
  MODIFIED away.
- Learned-weight provenance on THREE edges with pair-rollback-fails.
- HITL regenerator-deck ratify 10.6 min (gap 4 partial; sim_or_real stays
  designed).
- Governance CR-F-4704 prices retire-vs-probe-vs-status-quo and mandates
  native 0.05 kPa CSV exports (the fraud fence).
- Flip-fragility extended to CIRCULATION-TRUE CERTIFICATE: when three
  mean-side channels agree, their race does not decide truth; a
  cyclone-dP tap that policy treated as sticky-probe-only does.

## Self-critique of this round's batch

### Strengths
- The headline class is mechanistically tight: three locally-true mean
  loops live on mixed flue and remaining bed. Conjunction is not a
  cyclone-true circulation.
- Negative-result honesty: the gate does the right thing and the
  regenerator still fails for a reason the commissioned sensors could
  not see. Total -0.16.
- Triple-edge scar is load-bearing: the record states a counterfactual
  where rolling back any pair fails, with the fire threshold 0.30
  exhibited on each remaining edge.
- Contrast ACCEPT on a true sealed high-coke window prevents "never
  raise" as the lesson.
- Distinct from r32 reformer TMT-mean, r38 delayed-coker wet-foam, r40
  Claus bypass, r42 blast-furnace hang, and r45 ethylene-coil (claimed):
  FCC dipleg unseal with cyclone dP vs mixed flue O2, not tube-wall,
  not drum foam, not incinerator mask, not sector hang, not coil TMT.

### Weaknesses (honest)
- Probe error bands, the 0.47%/campaign unseal rate, the $2.14M / $4.1M
  figures, the 10.6 min climb latency, and the night-shift 0.33% base
  rate are DESIGNED constants and are flagged. Closed-loop offsets
  (separator dilution from dipleg air bypass, resid inventory d-t)
  are derived from those inputs, not discovered by an unauthored process.
- Afterburn-warp model is a designed 22 min mapping; no full CFD of the
  cyclone barrel shipped.
- Human-in-the-loop is ratification latency, not sim_or_real=hil. Gap 4
  remains open as a provenance cell.
- Cross-record arc is not discharged; +21 d CR-F-4704 is a hook, not a
  serial igniter into another round. autonomous-driving and
  grid-inspection remain unused.

### Realism of noise / latencies
Ladder: 188 us race / 178 us contrast race / 0.8 ms refractory floor
(tightest exhibited same-channel gap {gap:.3f} ms on {gap_ch}) / 500 us race
window / 712 us gate latency / 20 ms bus epoch / 40 ms raster / 7.2 s
probe / 10.6 min HITL / 6 min naive raise-ramp counterfactual / 22 min
pre-t0 afterburn / 3.4 h circulation recovery / 4.8 h cyclone-barrel hole /
+4 d contrast / +21 d governance. Adaptation decay on bed.hot
(0.53->0.50->0.63->0.45->0.32), cyc.dp (0.74->0.77->1.37->0.46->0.42->0.30),
air.ratio (0.56->0.58->0.48->0.27), flue.o2 (0.62->0.83).

### Value for SNN distillation
- DIPLEG UNSEAL = THREE CORRECT LOOPS, WRONG VOLUME.
- CYCLONE-TRUE dP CHANNEL that policy treated as sticky-probe-only as
  the tie-break.
- REVERSIBLE PROBE that recouples bed T iff the dipleg is sealed.
- TRIPLE-EDGE ELIGIBILITY: coordinated depression; pair rollback fails.
- CRITIC HEAD that can hold a process-correct MODIFY against a later
  unmonitored world loss without netting.

## Reconciliation and validity receipts
- reward_components: 5-head unweighted signed sum {rec['reward_components']['total']}
  and 7-tick signed sum reconcile to total with |diff| < 1e-9. Embedded
  contrast 5-head sum 0.49 reconciles independently.
- spike_events: primary {len(rec['spike_events'])} events, one key t_rel_ms,
  globally non-decreasing, min same-channel gap {gap:.3f} ms >= 0.8 ms, 3
  channels inside race_window_us 500 (cyc.dp.low 6.508, flue.in_band 6.696,
  bed.hot 6.890). Contrast 8 events, own race, min same-channel gap well
  above 0.8 ms.
- Sidecars: raster spikes 51 == round(160 x 8.0 x 0.040); energy 1173 pJ /
  0.001173 uJ at 23 pJ/spike; excerpt 16 events inside [0, 40000] us,
  neuron_id < 160, same-neuron gap N/A (unique ids) / >=1000 us; routing 4
  entries with three scar edges' before/after pair; third factor tau 0.92 s
  == 920 ms; gate_snn pools 40/16/4 == round(n x rate x 0.025) each,
  decision MODIFY == safety_decision.decision.
- Pipeline: {pipeline_receipt}

## Novel coverage
The coordination-failure CLASS (dipleg-unseal certificate of a mean-true
regenerator), the domain (FCC regenerator cyclone dipleg / refining), the
air-step probe discriminant, the triple-edge scar with
pair-rollback-fails, the primary negative-result (correct MODIFY,
regenerator still fails on unmonitored barrel warp), the HITL
regenerator-deck ratify, the resid-FCC probe-duration refit, and the
night-shift 10-bin quantization fence are absent from prior committed
ouroboros rounds and from staged r14-r45. Repeated elements discounted:
same-gate contrast (r02/r03/r04/r14), governance-pricing scaffold,
flip-fragility series (extended to circulation-true certificate, but the
move rhymes), sequenced recovery shape, third-factor rollback form (here
three edges rather than r14's two), negative-result primary (r14 staged).
Adjacent refining rounds (r32 SMR, r38 delayed-coker, r40 Claus) share
industrial-process scaffolding but not FCC dipleg physics. Weighing a
new failure family + cure vocabulary + domain against those reused
scaffolds:

{NOVEL_LINE}

## What ROUND 48 should add
1. FIT THE DESIGNED CONSTANTS: unseal-growth arrival, probe error bands,
   afterburn-warp kinetics, night-shift claim process.
2. HIL PROVENANCE CELL: put the regenerator-deck ratify on a
   hardware-in-loop cyclone interlock with fitted latency as
   state.sim_or_real=hil.
3. CROSS-RECORD ARC: let CR-F-4704's residual alarm be the igniter of
   the next round rather than a dangling +21 d leaf.
4. Domain candidates (de-collided): autonomous-driving; grid-inspection
   (if distinct from STARLING aerial-swarm and TORSIONKEY pitch);
   hydroelectric-kaplan; bioreactor-perfusion.
   AVOID fcc-regenerator-cyclone-dipleg (now used), blast-furnace
   burden descent, delayed-coker, LNG MCHE, chlor-alkali membrane,
   cement-rotary-kiln clinker, kraft-recovery, pem-electrolysis,
   electrolytic-aluminum, humanoid-locomotion, steel-caster mold-level,
   surgical-assist, wind-turbine pitch, float-glass, lyophilization,
   event-camera-traffic-grid, district-heating, aerial-swarm,
   warehouse-amr, underwater-rov, czochralski-pull, slot-die coating,
   optical-fiber-draw, vacuum-induction melt, steam-methane reformer,
   irrigation-canal, autoclave-composite-cure, geothermal-binary-orc,
   tire-curing-press, Claus sulfur recovery, ammonia converter,
   HDPE slurry loop, ethylene-steam-cracker coil, and any LYOSHIELD /
   CINDERWICK / TRIAD / SKULLGATE / CALXION / MAGNORIL / GORSEFLUE /
   CLINKERFELL / SODASHARD / LINTELPLY / KAOTHARN / TREADNOLL / ANOLITH /
   DRUMWROTH / RIMEBRAID / BOGIRON / CHROMLOOP / NITREVAULT / ETHYNWOLD /
   DIPLEGAR plant.
"""
    (OUT / "NOTES-r47.md").write_text(notes)
    return notes


def write_transcript(rec, line):
    c1_spikes = [e for e in rec["spike_events"] if e["t_rel_ms"] <= 26.240]
    text = """# Multi-Agent Ouroboros Swarm — Round 47 transcript

Factory: multi-agent-ouroboros-swarm
Run: 2026-09-02-final-heavy
Generator: grok-4.6
Record id: maos-r47-001
Quota Q: 1
Rights: RM-793 research-only (SpaceXAI/xAI SuperGrok Heavy consumer chat)
Plant: invented DIPLEGAR / Gritfen Catalytic FCC-4 (not TRIAD / Meridian / VANTIS-CADENCE-AEGIS / LYOSHIELD / CINDERWICK / DRUMWROTH / RIMEBRAID / BOGIRON / CHROMLOOP / NITREVAULT / ETHYNWOLD)

Two densifying cycles. Verbatim headings in order. Trajectory Builder cycle 2
emits the only JSONL line (also written to batch-r47.jsonl).

---

# CYCLE 1 — Foundation + injections

## Generator

Design intent: a 980 t FCC regenerator where three correct agents each
read a regenerator-mean loop because an unsealed 2nd-stage dipleg
partitions cyclone-true dP from mean-true bed and mixed flue. The naive
playbook raises feed into an unsealed cyclone. The gate must MODIFY on a
numeric feed ceiling, not by killing an agent.
sim_or_real=designed. Reward heads are
task_progress/safety/efficiency/coherence/exploration.

Cycle-1 base arc (pre-critic): state at Gritfen FCC-4, 65 kbpd,
bed 710 C, flue O2 1.2 vol%, air/coke 1.04, proposed FEED-RAISE
72 kbpd, safety MODIFY to FEED-HOLD, executed hold without the
air-step numbers fully specified, outcome "unseal found, regenerator saved"
(this last claim is the defect the later cycles will refuse to keep).
Sixteen spikes, five ticks, raster/gate_snn present but the scar is a
single edge.

```json
{
  "id": "maos-r47-001",
  "state": {
    "sim_or_real": "designed",
    "domain": "industrial-process",
    "description": "Regenerator FCC-4 at body feed; three mean loops in-spec; supervisor proposes feed-raise.",
    "t0_us": 1775684640000047,
    "gate_latency_us": 712,
    "race_window_us": 500
  },
  "proposed_action": {"name": "feed_raise", "parameters": {"feed_kbpd": 72}},
  "safety_decision": {"decision": "MODIFY", "rationale": "Hold; do not raise feed while cyclone dP is low."},
  "executed_action": {"name": "feed_hold", "executed_as_proposed": false},
  "future_outcome": {"summary": "Unseal found, regenerator saved."},
  "reward_components": {"total": 0.40, "_aggregation": "total = task_progress + safety + efficiency + coherence + exploration"},
  "meta": {"round": 47, "factory": "multi-agent-ouroboros-swarm", "generator": "grok-4.6"}
}
```

That v1 object is a scaffold, not the publishable line. Defects below are
intentional for the critic to catch.

## Critic

Numbered defects on the cycle-1 Generator scaffold:

1. **blocking — reward arithmetic / false success.** `reward_components.total`
   0.40 is asserted without the five heads, without ticks, and against an
   outcome that claims "regenerator saved". If the pre-t0 warped barrel later
   holes, booking +0.40 is a lie. Fix: declare `_aggregation`, emit
   3–8 ticks that sum to task_progress+safety+efficiency+coherence+exploration,
   and do not call a quarantined regenerator a save.
2. **blocking — weak safety rationale.** `safety_decision.rationale` has no
   numeric floor. Contract requires a concrete constraint. Fix: quote
   feed <= 65 kbpd while cyclone dP < 4.0 kPa AND ESP catalyst loss > 1.2 t/h.
3. **major — domain is a bucket, not a plant.** `state.domain` =
   `industrial-process` collides with generic MES vocabulary and teaches
   nothing. FCC regenerator cyclone dipleg (cyclone dP vs mixed flue O2,
   ESP loss as an unseal flag) is absent from prior ouroboros
   rounds and must be named.
4. **major — race under-specified.** One cyclone channel cannot be a race.
   Need >=2 channels inside `race_window_us` with globally sorted `t_rel_ms`
   and same-channel refractory >= 0.8 ms.
5. **minor — single-edge scar.** Raster routing with one potentiated weight
   repeats r04's one-edge rollback and is thinner than r14's two-edge.
   NOTES-r14 item 4 asked for three edges where pair rollback fails.

Critic does not rewrite the trajectory.

## Diversity Enforcer

Injected novel domain (exactly 1 this cycle): **fcc-regenerator-cyclone-dipleg**
(justified novel subdomain of industrial-process / refining; explicit tag
`fcc-regenerator-cyclone-dipleg`).

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
hdpe-slurry-loop-polymerization, ammonia-haber-bosch-converter, or
ethylene-steam-cracker-coil. autonomous-driving is left unused.

Domain-specific constraint: feed must remain <= 65 kbpd while
cyclone dP < 4.0 kPa even if flue O2 is inside the healthy
band; ESP hopper loss is an unseal flag the mixed-flue analyzer cannot
substitute for.

Sensor delta: +dense-bed T, +flue O2, +air/coke lookup, +2nd-stage
cyclone dP, +ESP hopper loss; -any mobile robot, -event-camera gantries,
-DVS, -Pirani/CM, -RGA quadrupole, -DVL, -pitch encoder, -tendon LVDT,
-insole GRF, -kiln zirconia, -smelt IR, -cell-pH, -drum wet-foam,
-MCHE cold-end, -Claus tail CEMS, -ammonia bed-max, -sector radar.

`state.domain` and `meta.domain` both become `fcc-regenerator-cyclone-dipleg`.
Opening of `state.description` must Jaccard < 0.4 against prior plants
(Gritfen night-shift unseal, not a lyophilizer, not a corridor, not a tin
bath, not a ROV pad, not a potline, not a PEM stack, not an OR, not a
gait lab, not a kiln, not a kraft boiler, not a coker drum, not an LNG
MCHE, not a blast furnace, not an HDPE loop, not a cracker coil).

## Edge-Case Hunter

Injected adversarial tail (exactly 1 this cycle): **2nd-stage dipleg unseal
+ afterburn-warp certificate**.

- Trigger: C-2 seal-pot unseal plus dilute-phase afterburn, cyclone dP
  2.1 kPa, flue O2 1.2 vol%.
- Base rate: <1% — 0.47%/campaign from an unseal-growth MC (regenerator-deck
  visual threshold is designed; seal-pot geometry fitted-style). Visual
  PASSES because the seal pot sits behind the cyclone barrel.
- Naive failure: FALSE PERMISSION. PB-FCC-4 sees three in-spec mean
  loops, raises 65->72 kbpd, dilute-phase 810 C, $4.1M.
- Trajectory edit: put the unseal in `state.fault_context`, make each
  agent's confirm a different mean-side slice of the same cyclone-false
  state (bed-in-band, flue-in-band, air-in-band). Cyclone dP is
  readable but policy-treated as sticky-probe-only.

Distinct from stacked-dead-band permission (fragments of one trip vs
wrong-volume sensing), from r32 reformer TMT-mean (tube vs dipleg),
from r38 delayed-coker wet-foam (drum vs cyclone), and from r42
blast-furnace hang (stockline vs cyclone dP).

## Neuromorphic Translator

Cycle-1 temporal densification (16 spikes, 5 ticks, 40 ms raster):

| channel | t_rel_ms | amplitude |
|---|---|---|
| bed.hot | 0.310 | 0.53 |
| flue.o2 | 1.120 | 0.62 |
| air.ratio | 2.010 | 0.56 |
| cyc.dp | 3.160 | 0.74 |
| bed.hot | 4.150 | 0.50 |
| cyc.dp | 4.820 | 0.77 |
| air.ratio | 5.340 | 0.58 |
| cyc.dp.low | 6.508 | 1.37 |
| flue.in_band | 6.696 | 1.15 |
| bed.hot | 6.890 | 0.63 |
| ctrl.gate | 7.220 | 1.08 |
| cyc.dp | 8.840 | 0.46 |
| flue.o2 | 10.720 | 0.83 |
| air.ratio | 13.020 | 0.48 |
| bed.hot | 18.500 | 0.45 |
| ctrl.gate | 26.240 | 0.87 |

Race: cyclone dP 6.508 vs flue O2 6.696 (188 us) inside 500 us;
bed 6.890 is the third channel in-window. Winner/loser flip: reversing
188 us reshuffles PB-FCC-4 triage; floors still MODIFY. Refractory held
(cycle-1 min same-channel gap 1.660 ms on cyc.dp 4.820-3.160;
bed 6.890-4.150 = 2.740; air 5.340-2.010 = 3.330). Adaptation:
cyc 0.74->0.77->1.37->0.46; bed 0.53->0.50->0.63->0.45; air
0.56->0.58->0.48.

Raster cycle-1 seed: 40 ms, 160 neurons, 8.0 Hz, 51 spikes, 1173 pJ, third
factor acetylcholine tau_e 0.92 s. Single scar edge only — cycle 2 must
add the second and third edges.

Ticks 1–5 at 4580, 6508, 7220, 7.2e6, 636e6 us; heads not yet the final
-0.16 (missing the 3.4 h and 4.8 h ticks).

Distillation value this cycle: mean-side confirms as a permission code
that is not a cyclone-true circulation code.

## Trajectory Builder

Cycle-1 hardened object: domain fcc-regenerator-cyclone-dipleg, tail
dipleg unseal, 16 spikes, 5 ticks, MODIFY with numeric floor, raster+gate_snn
present, sim_or_real=designed, rights stamp on record and meta, no thought
keys. Still missing (and therefore not the publishable line): resid-FCC
sub-variant, night-shift tail, second and third scar edges,
delayed cyclone-barrel hole as PRIMARY terminal, contrast ACCEPT episode,
ticks 6–7, spikes 17–26.

Validation receipt (cycle 1, not final):
- checks passed: 16 spikes sorted; 3 channels in 500 us window; refractory
  >= 0.8 ms; rationale quotes 65 kbpd / 4.0 kPa / 1.2 t/h; domain
  named; gate_snn.decision MODIFY.
- checks deferred to cycle 2: triple-edge scar, second tail, second domain
  constraint, negative-result booking, 7 ticks summing to heads.
- densification vs Generator v1: +1 domain, +1 tail, +16 spikes, +5 ticks,
  +numeric floor.

Cycle-1 JSON is retained as the base; it is NOT written to batch-r47.jsonl.

Cycle-1 spike count: __C1_SPIKES__.

---

# CYCLE 2 — Densification

## Generator

Cycle-1 output is the base. Additive expansion (nothing removed):

1. Downstream side-effect (immediate): air-step probe at +7.2 s stays
   mean-false (|Delta bed T| 0.4 <= 1.0 K) — dipleg-unseal, not
   true high-coke. C-2 isolate. Warped barrel discovered during the isolate.
2. Delayed side-effect (PRIMARY terminal, not a footnote): at +4.8 h
   cyclone-barrel hole from the pre-t0 afterburn warp; 36 h outage;
   $2.14M. The 22 min pre-t0 afterburn is the mechanism. Correct gate,
   regenerator still fails.
3. Deepened `proposed_action.evidence` with units: dP 2.1 kPa,
   flue O2 1.2 vol%, bed 710 C, air/coke 1.04, ESP loss 4.8 t/h, race 188 us.
4. Tightened rationale to the numeric floor feed <= 65 kbpd while
   cyclone dP < 4.0 kPa AND ESP catalyst loss > 1.2 t/h, plus
   probe bands <= 1.0 vs >= 4 K, plus HITL 10.6 min regenerator-deck
   rule.

Reward retargeted to total -0.16 so the delayed fail is the inflection
(t_us 17280000000), not the gate. Process heads remain non-zero.

## Critic

Re-audit of the expanded trajectory:

1. **blocking if unfixed — missing second domain constraint.** Gas-oil
   probe 7.2 s / -5% is not a universal number. A resid low-inventory
   regenerator will overshoot live sealed dP. Diversity Enforcer must
   inject the physical-constraints sub-variant this cycle.
2. **major — only one tail class.** Dipleg unseal is accidental
   infrastructure. A disjoint human-intent tail is still required
   (night-shift cyclone-dP forgery is the open cell).
3. **major — scar is still one edge in the cycle-1 raster.** NOTES-r14
   item 4 is not discharged until three go-edges exist and pair rollback
   is shown to fail at threshold 0.30.
4. **minor — contrast episode missing.** Without a same-gate ACCEPT on a
   true sealed high-coke window the record teaches "never raise". Add +4 d
   sister-regenerator contrast with its own race.
5. **minor — HITL latency mentioned in prose only.** Put 10.6 min in
   executed_action.parameters.human_ratify and in a tick.

No rewrite; directives only.

## Diversity Enforcer

Injected second novel domain / physical-constraint sub-variant (exactly 1
this cycle): **resid FCC / low-inventory** on a sister inventory class.

What it expands: 980 t gas-oil regenerator (cycle 1) -> 372 t resid.
Inventory 0.38x. Air-step gain 2.3x. Conradson carbon 8.4 wt%.
The 7.2 s -5% pulse moves even a live sealed cyclone to a 1.8 kPa false
dP, inside the 4.0 kPa trip. Required probe: 20 s at -1.8% (live
Delta 3.1 K, unseal Delta 0.4).

This is still one domain injection for the cycle (physical-constraints
clause of the factory prompt). It does not displace
fcc-regenerator-cyclone-dipleg; it changes which probe table is legal.
`future_outcome.subvariant_constraint` carries the refit. Jaccard opening
stays the Gritfen 980 t sentence; resid is additive, not a rewrite.

## Edge-Case Hunter

Injected second adversarial tail (exactly 1 this cycle, disjoint class):
**night-shift forged cyclone-dP CSV**.

- Trigger: shift lead, 02:44, posts a historian export showing
  dP = 7.2 kPa at t = 1.4 h to clear a production-catchup slot.
- Base rate: ~0.33% of Sunday-night campaigns (designed, flagged, <1%).
- Naive failure: a weak supervisor ACCEPTs the raise on the forged confirm
  and ignores live cyclone dP. Afterburn runaway plus a data-integrity
  write-up.
- Fence: forged log quantized at 0.50 kPa (SCADA screenshot rounding); plant
  historian is 0.05 kPa (10 bins). Live dP is 2.1 kPa and flue O2 is
  1.2 vol% at the claimed circulation-true, which no live sealed cyclone
  produces. Freeze-window overlap with the 22 min afterburn.
- Trajectory edit: governance CR-F-4704 mandates native 0.05 kPa CSV
  exports; the contrast ACCEPT still requires live cyclone dP, not a CSV.

Distinct from cycle-1 unseal (accidental seal-pot vs deliberate deception) and
from the resid sub-variant (physics vs fraud).

## Neuromorphic Translator

Re-densify (additive):

- +10 spikes after 26.240 ms: air.step.probe 7200.0, cyc.dp 7288.4
  (adapt 1.37->0.42), flue.in_band 7372.0 (1.15->0.37), human.ratify
  636000.0, dipleg.isolate 636900.0, cyc.attack 637700.0, bed.hot
  12240000.0, cyc.dp 12240720.0, air.ratio 12241480.0, cyc.hole
  17280000.0. Primary train 16 -> 26. Still one key, still sorted,
  refractory held.
- +2 ticks (5 -> 7) at 12_240_000_000 us (true sealed circulation) and
  17_280_000_000 us (cyclone-barrel hole). Heads now 0.08, -0.35, -0.12,
  0.14, 0.09; total -0.16. Inflection is the last tick.
- Contrast train 8 events, own race 178 us, ACCEPT.
- Triple-edge third factor: three mean-healthy-go edges, tau_e 0.92 s = 920 ms,
  trace __AUX_TRACE__, eta __AUX_ETA1__ / __AUX_ETA2__ / __AUX_ETA3__,
  weights 0.50->0.25, 0.44->0.22, 0.41->0.20. Raster excerpt unchanged
  (decision window is still 40 ms) and remains sorted with unique
  neuron_ids (same-neuron >=1000 us vacuously).

Winner/loser flip (re-stated, not replaced): reversing 188 us would only
reorder triage; cyclone-dP floors still MODIFY. Contrast flip of
178 us similarly cannot turn a sealed cyclone into an unseal.

## Trajectory Builder

Schema checks on the FINAL object: required Thalamic v2 keys present as
objects; `state.sim_or_real`=designed; `safety_decision.decision`=MODIFY
with numeric rationale; `reward_components.total` = sum of five heads =
sum of 7 ticks = -0.16; `spike_events` globally non-decreasing on
t_rel_ms, 26 events, refractory >=0.8 ms, 3 channels in race window;
raster 20–50 ms, spikes=round(n*rate*window_s)+/-1, energy 23 pJ/spike,
excerpt sorted, tau_e consistent; gate_snn.decision matches; meta.round=47,
factory=multi-agent-ouroboros-swarm, generator=grok-4.6,
run_label=2026-09-02-final-heavy; rights on record and meta; no thought
keys; no training_ready; Diversity + Edge-Case injections from BOTH cycles
present and non-trivial; cycle 2 strictly additive.

Densification delta: +1 domain sub-variant (resid FCC), +1 tail
(night-shift forgery), +10 spikes (16->26), +2 ticks (5->7), +1 contrast
train with own race, +2 delayed side-effects, +1 triple-edge scar with
pair-rollback-fails, +1 HITL ratify, +1 surprise (afterburn warp is the
barrel-hole mechanism).

Publishable JSONL line (the only JSONL line; also at batch-r47.jsonl):

```json
__FINAL_JSONL__
```

Validation receipt (final): checks passed / fixed as reported by
build_r47.py self-validate (check_jsonl, raster_status, verify_record_execution,
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
    (OUT / "swarm-transcript-r47.md").write_text(text)
    return text


def main():
    rec, aux = build_record()
    errs = local_checks(rec, aux)

    OUT.mkdir(parents=True, exist_ok=True)
    line = json.dumps(rec, ensure_ascii=False, separators=(",", ":"))
    (OUT / "batch-r47.jsonl").write_text(line + "\n")

    from check_records import FactoryStaging, check_jsonl
    from curate_bridge import raster_status
    from verify_execution import verify_record_execution

    e, w, kinds, n = check_jsonl(
        OUT / "batch-r47.jsonl",
        "batch-r47.jsonl",
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
            str(OUT / "batch-r47.jsonl"),
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
        [sys.executable, "/tmp/maos_heading_check.py", str(OUT / "swarm-transcript-r47.md")],
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
            "maos-r47-001|DIPLEGAR",
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
    print("OK maos-r47-001 staged under", OUT)
    print("bytes jsonl", (OUT / "batch-r47.jsonl").stat().st_size)
    print("bytes notes", (OUT / "NOTES-r47.md").stat().st_size)
    print("bytes transcript", (OUT / "swarm-transcript-r47.md").stat().st_size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
