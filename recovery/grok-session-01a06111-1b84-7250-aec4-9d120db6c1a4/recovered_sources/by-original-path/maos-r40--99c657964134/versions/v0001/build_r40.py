#!/usr/bin/env python3
"""Build and self-check MAOS round-40 JSONL (research-only; not published)."""
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

GEN_AT = "2026-09-03T05:50:00Z"
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
OUT = Path("/tmp/maos-r40")
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
    "OXBOWREEL",
    "Oystermere",
    "REDHALL",
    "Gullmere",
    "SEEDLATCH",
    "Quartzmere",
    "Quartzridge",
    "STRIAFOIL",
    "Kelpholt",
    "TORSIONKEY",
    "Ridgeholt",
    "PROTONIL",
    "Ashspire",
    "ORRIS",
    "Holmwick",
    "WHORLSPAR",
    "Pikeshear",
    "Crowspire",
    "SODASHARD",
    "Cairnmere",
    "SKULLGATE",
    "Bloomholt",
    "BRACEGILT",
    "Yarrowmere",
    "CALXION",
    "Aldersedge",
    "MAGNORIL",
    "Basaltspit",
    "GORSEFLUE",
    "Copseholt",
    "CLINKERFELL",
    "Flintmere",
    "IONSPATE",
    "Thornmere",
    "VEILFORGE",
    "MURENA",
    "HALYARD",
    "VESPERTHORN",
    "ASHVEIL",
    "IRONMANTLE",
    "DUSKRELAY",
    "PALISADE",
    "TELAMON",
    "CHORDA",
    "Brinewell",
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
    "Comprimo",
    "Worley",
    "Fluor",
    "Clauspol",
    "SuperClaus",
    "EuroClaus",
    "Axens",
    "Kellogg",
    "UOP",
    "KBR",
    "Honeywell",
    "Jacobs",
)
R14_OPENING = (
    "Helixmere Biologics Building C lyophilizer LYO-4 is mid-primary on 8400 "
    "vials of a monoclonal antibody"
)
NOVEL_LINE = "Novel coverage: 47%"
PLANT = "BRIMVAULT"
GEO = "Pyritefen"
CELL = "SR-3"
DOMAIN = "claus-sulfur-recovery"
RECORD_ID = "maos-r40-001"
ROUND = 40
DELAY_S = 0.84
TAU_E_S = 0.90
C1_CUT_MS = 26.020


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
        if p.parent.name == "maos-r40":
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
        if p.parent.name == "maos-r40":
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
        if p.parent.name == "maos-r40":
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
        [4460, 6470, 7200, 9_600_000, 648_000_000, 10_440_000_000, 18_360_000_000],
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
        {"channel": "ratio.air", "t_rel_ms": 0.270, "amplitude": 0.56},
        {"channel": "conv.dt", "t_rel_ms": 1.060, "amplitude": 0.64},
        {"channel": "tail.cems", "t_rel_ms": 1.960, "amplitude": 0.53},
        {"channel": "h2s.main", "t_rel_ms": 3.020, "amplitude": 0.74},
        {"channel": "ratio.air", "t_rel_ms": 4.060, "amplitude": 0.51},
        {"channel": "h2s.main", "t_rel_ms": 4.740, "amplitude": 0.77},
        {"channel": "conv.dt", "t_rel_ms": 5.260, "amplitude": 0.60},
        {"channel": "h2s.main.high", "t_rel_ms": 6.470, "amplitude": 1.40},
        {"channel": "tail.in_band", "t_rel_ms": 6.664, "amplitude": 1.13},
        {"channel": "ratio.air", "t_rel_ms": 6.860, "amplitude": 0.65},
        {"channel": "ctrl.gate", "t_rel_ms": 7.200, "amplitude": 1.05},
        {"channel": "h2s.main", "t_rel_ms": 8.720, "amplitude": 0.44},
        {"channel": "tail.cems", "t_rel_ms": 10.580, "amplitude": 0.83},
        {"channel": "conv.dt", "t_rel_ms": 12.840, "amplitude": 0.46},
        {"channel": "ratio.air", "t_rel_ms": 18.200, "amplitude": 0.42},
        {"channel": "ctrl.gate", "t_rel_ms": 26.020, "amplitude": 0.86},
        {"channel": "acid.step.probe", "t_rel_ms": 9600.0, "amplitude": 0.93},
        {"channel": "h2s.main", "t_rel_ms": 9690.4, "amplitude": 0.41},
        {"channel": "tail.in_band", "t_rel_ms": 9772.8, "amplitude": 0.36},
        {"channel": "human.ratify", "t_rel_ms": 648000.0, "amplitude": 0.80},
        {"channel": "bypass.isolate", "t_rel_ms": 648880.0, "amplitude": 0.71},
        {"channel": "cat.sulfide", "t_rel_ms": 649660.0, "amplitude": 0.87},
        {"channel": "ratio.air", "t_rel_ms": 10440000.0, "amplitude": 0.32},
        {"channel": "h2s.main", "t_rel_ms": 10440740.0, "amplitude": 0.30},
        {"channel": "conv.dt", "t_rel_ms": 10441500.0, "amplitude": 0.27},
        {"channel": "so2.slip", "t_rel_ms": 18360000.0, "amplitude": 0.94},
    ]

    contrast_spikes = [
        {"channel": "acid.demand", "t_rel_ms": 0.000, "amplitude": 0.84},
        {"channel": "h2s.clear", "t_rel_ms": 0.186, "amplitude": 0.78},
        {"channel": "ratio.air", "t_rel_ms": 0.400, "amplitude": 0.24},
        {"channel": "conv.dt", "t_rel_ms": 1.440, "amplitude": 0.40},
        {"channel": "h2s.main", "t_rel_ms": 4.800, "amplitude": 0.53},
        {"channel": "ctrl.gate", "t_rel_ms": 7.040, "amplitude": 0.90},
        {"channel": "acid.step.probe", "t_rel_ms": 3000.0, "amplitude": 0.35},
        {"channel": "so2.slip", "t_rel_ms": 18360000.0, "amplitude": 0.10},
    ]

    excerpt = [
        {"t_us": 270, "neuron_id": 8},
        {"t_us": 1060, "neuron_id": 84},
        {"t_us": 1960, "neuron_id": 22},
        {"t_us": 3020, "neuron_id": 46},
        {"t_us": 4060, "neuron_id": 12},
        {"t_us": 4740, "neuron_id": 54},
        {"t_us": 5260, "neuron_id": 96},
        {"t_us": 6470, "neuron_id": 44},
        {"t_us": 6664, "neuron_id": 16},
        {"t_us": 6860, "neuron_id": 32},
        {"t_us": 7200, "neuron_id": 130},
        {"t_us": 8720, "neuron_id": 60},
        {"t_us": 10580, "neuron_id": 28},
        {"t_us": 12840, "neuron_id": 112},
        {"t_us": 18200, "neuron_id": 18},
        {"t_us": 26020, "neuron_id": 138},
    ]

    rec = {
        "id": RECORD_ID,
        "title": "BRIMVAULT SR-3: main-path H2S 1.8 vol% beats tail-CEMS-in-band by 194 us; correct MODIFY still loses the converter to a pre-t0 catalyst sulfide skin",
        "rights": dict(RIGHTS),
        "state": {
            "sim_or_real": "designed",
            "domain": DOMAIN,
            "scenario_name": "BRIMVAULT / Pyritefen Claus SR-3",
            "timestamp_local": "2026-08-09T02:54:00-05:00",
            "t0_us": 1781252040000040,
            "gate_latency_us": 730,
            "race_window_us": 500,
            "race_window_rel_ms": [6.470, 6.970],
            "description": "Pyritefen Sulfur hall SR-3 holds 18.4 t/h acid-gas on a two-converter Claus train. RATIO's air/acid-gas is 1.02 of stoich against 0.95-1.10. CONV's first-converter DeltaT is 48 K inside 40-60. TAIL's post-incinerator CEMS is 120 ppm inside 80-200. The conjunction is not a furnace-conversion certificate: a 6 pct passing-valve leak bypasses the reaction furnace, so main-path H2S upstream of the incinerator is 1.8 vol% (healthy 0.2-0.6; hold if > 0.8) while the stack CEMS still sees incinerated leftover H2S as in-spec SO2-equivalent. Main-path H2S infers 1.8 vol% (hold if > 0.8) but policy treats that tap as a furnace-noise tag unless tail CEMS also trips (2017 'noisy main-path H2S nuisance'). H2S-first latches ACID-HOLD plus an acid-step probe; tail-ok-first would have authorized ACID-RAISE 18.4 to 22.0 t/h into a production-catchup window with the furnace already bypassed.",
            "goal": "Hold acid-gas at 18.4 t/h without a catchup raise while main-path H2S > 0.8 vol% AND bypass fraction remains unisolated; keep furnace SO2 inside the 2.5 vol% trip and converter SO2-slip at 0.",
            "race": {
                "contenders": [
                    "h2s.main.high 1.8 vol% (pre-incinerator main path vs furnace-noise tap)",
                    "tail.in_band 120 ppm (post-incinerator CEMS)",
                ],
                "semantics": "H2S-first latches ACID-HOLD + ACID-STEP-PROBE + bypass isolate. Tail-ok-first latches ACID-RAISE (18.4 to 22.0 t/h, air ratio held, no isolate).",
                "window_derivation": "500 us = one 360 us H2S GC slot plus 140 us tail-CEMS publish.",
                "order_evidence_note": "Margin 194 us vs combined jitter 56 us (H2S 30 + CEMS 26): 3.5x. The 194 us gap sits inside min(500, 500) us, so a sub-flip-bound perturbation reverses triage order. The gate rides the order-invariant floors main-path H2S > 0.8 vol% and bypass inferred > 4 pct, not the alarm order.",
            },
            "topology": {
                "site": "Pyritefen Sulfur, invented mill-town Pyritefen, Claus train SR-3: two converters, 18.4 t/h acid-gas, 1.02 stoich air, Grade-B SRU-deck LOTO",
                "agents": "RATIO air/acid-gas (vendor Ratiofen): 20 Hz on the furnace air valve. CONV first-converter DeltaT (vendor Convholt): 50 Hz on bed inlet-outlet. TAIL post-incinerator CEMS (vendor Tailwick): 20 ms bus average on the stack. H2S main-path GC (vendor Sulfreave) is commissioned as a furnace-noise tag, not as a conversion-integrity tag. Heterogeneous stacks, no shared intent schema, one 20 ms SRU-bus epoch",
                "coupling": "All three playbook confirms live on the WRONG volume. RATIO is correct that the air valve is at 1.02 stoich of metered acid-gas (bypass is downstream of the acid-gas meter). CONV is correct that converter-1 DeltaT is 48 K (94 pct of the gas still ignites). TAIL is correct that post-incinerator CEMS is 120 ppm (incinerator burns leftover H2S to SO2). Playbook PB-SR-3 treats the conjunction as permission to raise acid-gas. No agent is faulty; the stack CEMS is looking at incinerated tail, not at furnace-true conversion.",
            },
            "sensors": [
                "air/acid-gas ratio 12-bit, 20 Hz, 22 us jitter, 1.02 stoich (dead-band 0.95-1.10)",
                "first-converter DeltaT, 50 Hz, 18 us jitter, 48 K (band 40-60)",
                "post-incinerator CEMS, 50 Hz, 26 us jitter, 120 ppm (setpoint band 80-200)",
                "main-path H2S GC, 20 Hz, 30 us jitter, 1.8 vol% (healthy 0.2-0.6; policy floor 0.8 is not armed unless tail CEMS also trips)",
                "furnace SO2 GC is NOT commissioned at t0 (installed after this incident)",
            ],
            "constraints": {
                "acid_t_h": 18.4,
                "acid_hold_ceiling_t_h": 18.4,
                "proposed_acid_t_h": 22.0,
                "ratio_stoich": 1.02,
                "ratio_deadband": [0.95, 1.10],
                "conv_dt_K": 48.0,
                "conv_dt_band_K": [40.0, 60.0],
                "tail_ppm": 120.0,
                "tail_band_ppm": [80.0, 200.0],
                "h2s_main_volpct": 1.8,
                "h2s_hold_volpct": 0.8,
                "h2s_healthy_volpct": [0.2, 0.6],
                "bypass_pct": 6.0,
                "bypass_hold_pct": 4.0,
                "furnace_so2_volpct": 0.9,
                "furnace_so2_trip_volpct": 2.5,
                "n_converters": 2,
                "fault_path": "furnace-bypass passing valve",
            },
            "fault_context": {
                "failure_class": "INCINERATOR-MASKED FURNACE-BYPASS CERTIFICATE: three individually-correct heterogeneous agents each read a locally-true loop; a 6 pct passing-valve leak partitions furnace-true conversion from stack-true incinerated tail, so the playbook's ratio/DeltaT/CEMS conjunction is not a furnace-conversion certificate",
                "igniter": "furnace-bypass passing valve after 26 min of unmonitored leak growth; deck visual PASSES (valve stem looks seated; sulfide skin is already on converter-1 catalyst on the far side of the bed)",
                "naive_failure": "PB-SR-3 ACID-RAISE on three healthy loops: 18.4 to 22.0 t/h into a production-catchup window with the furnace already bypassed, furnace SO2 4.1 vol% at the burner, $3.1M plus a 30-hour SRU outage",
            },
            "poisoned_context": {
                "naive_alarm": "Playbook PB-SR-3 (after the 2017 'noisy main-path H2S nuisance') auto-drafts ACID-RAISE whenever air/acid-gas is inside 0.95-1.10 AND converter-1 DeltaT inside 40-60 K AND post-incinerator CEMS inside 80-200 ppm, ignoring the main-path H2S tap unless tail CEMS also trips",
                "why_poisoned": "The three confirms are locally true and jointly insufficient. The main-path H2S tap is a commissioned sensor that policy treats as furnace-noise-only. Independence of 'stack CEMS in band, therefore the reaction furnace is converting' is the hidden assumption, and it is false across a bypass-plus-incinerator path.",
            },
            "constraint": "Do not raise acid-gas above 18.4 t/h while main-path H2S > 0.8 vol% AND inferred bypass > 4 pct. Discriminate furnace-bypass vs true high-rate with a reversible acid-step probe before any acid-gas raise.",
        },
        "proposed_action": {
            "actor": "SRU supervisory optimizer SSSO (auto-playbook PB-SR-3 draft), submitted to gate TG-SR-3",
            "name": "acid_raise",
            "action": "ACID-RAISE: 18.4 -> 22.0 t/h, air ratio held, no acid-step probe, no bypass isolate",
            "summary": "Treat three in-spec loops as a healthy Claus train and raise night-shift acid-gas to clear a production-catchup window.",
            "parameters": {
                "acid_t_h": 22.0,
                "acid_step_probe": False,
                "bypass_isolate": False,
                "human_ratify": False,
            },
            "steps": [
                "assert air/acid-gas 1.02 inside 0.95-1.10",
                "assert converter-1 DeltaT 48 K inside 40-60",
                "assert post-incinerator CEMS 120 ppm inside 80-200",
                "ramp acid-gas 18.4 to 22.0 t/h over 6 min",
                "hold air ratio; do not read main-path H2S as a conversion-integrity tag",
            ],
            "evidence": [
                {
                    "observable": "main-path H2S",
                    "value": 1.8,
                    "unit": "vol%",
                    "source": "H2S GC vs furnace-noise tap",
                    "note": "healthy 0.2-0.6; policy floor 0.8 is not armed unless tail CEMS also trips",
                },
                {
                    "observable": "post-incinerator CEMS",
                    "value": 120.0,
                    "unit": "ppm",
                    "source": "TAIL stack CEMS",
                    "note": "dead-band 80-200; lives on incinerated leftover H2S, not furnace-true conversion",
                },
                {
                    "observable": "air/acid-gas ratio",
                    "value": 1.02,
                    "unit": "stoich",
                    "source": "RATIO 12-bit",
                    "note": "healthy-load band 0.95-1.10; meter is upstream of the bypass",
                },
                {
                    "observable": "first-converter DeltaT",
                    "value": 48.0,
                    "unit": "K",
                    "source": "CONV bed couple",
                    "note": "band 40-60; 94 pct of the gas still ignites across the bypass",
                },
                {
                    "observable": "inferred bypass fraction",
                    "value": 6.0,
                    "unit": "pct",
                    "source": "main-path H2S vs converter DeltaT lookup",
                    "note": "hold floor 4 pct; bypassed acid-gas never sees the furnace",
                },
                {
                    "observable": "race margin",
                    "value": 194,
                    "unit": "us",
                    "source": "h2s.main.high 6.470 ms vs tail.in_band 6.664 ms",
                    "note": "combined jitter 56 us, 3.5x; inside 500 us flip bound",
                },
            ],
            "basis": "PB-SR-3 fires on three locally-true confirms. The draft does not read H2S 1.8 vol% as a conversion residual and does not treat inferred bypass 6 pct as a furnace discriminant.",
            "expected_cost_bound": "If the draft executes: furnace SO2 4.1 vol% at the burner, $3.1M plus 30-hour SRU outage. If MODIFIED: probe plus isolate, with residual risk from catalyst sulfide already seeded in the 26 min pre-t0 growth.",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "correctness": "correct",
            "decided_by": "TG-SR-3 thalamic release gate",
            "decision_t_rel_ms": 7.200,
            "rationale": "MODIFY the draft: strip the acid-gas raise, hold 18.4 t/h, run a 9.6 s acid-step probe (-6% acid-gas), and isolate the furnace-bypass passing valve only if the probe stays stack-false. Numeric floor: do not raise acid-gas above 18.4 t/h while main-path H2S > 0.8 vol% AND inferred bypass > 4 pct. Observed H2S 1.8 vol% and bypass 6 pct both violate the release predicate, so a raise is forbidden even though all three playbook confirms are numerically true. The three confirms are not a furnace-conversion certificate: they live on incinerated tail past a bypass, and the playbook's conjunction of stack-true loops is not a furnace-true certificate. Probe discriminant: after a 9.6 s -6% acid step, a bypass keeps |Delta main H2S| <= 0.10 vol% (bypassed gas never enters the furnace); a live converting furnace moves >= 0.45 vol%. Order-code discipline: main-path H2S beat tail-CEMS by 194 us inside the 500 us flip bound, so triage order is flip-fragile; the hold rides the order-invariant floors, not the winner tag. Human ratification: bypass isolate is confined-space SRU-deck work with fitted 10.8 min dead-man; the gate may hold and probe autonomously but may not break the deck interlock without the operator confirm.",
            "constraint_checked": {
                "acid_t_h": {"observed": 18.4, "ceiling": 18.4, "proposed_target": 22.0},
                "h2s_main_volpct": {"observed": 1.8, "hold_if_above": 0.8},
                "ratio_stoich": {"observed": 1.02, "band": [0.95, 1.10]},
                "bypass_pct": {"observed": 6.0, "hold_if_above": 4.0},
            },
        },
        "executed_action": {
            "name": "acid_hold_step_probe_isolate",
            "action": "ACID-HOLD + ACID-STEP-PROBE + BYPASS-ISOLATE (gate-mandated modification)",
            "executed_as_proposed": False,
            "parameters": {
                "acid_t_h": 18.4,
                "acid_step_probe": True,
                "bypass_isolate": True,
                "human_ratify": True,
            },
            "gate_effect": "MODIFY: acid-gas raise stripped. Hold 18.4 t/h. 9.6 s acid-step -6%. Probe stays stack-false (H2S 1.8 -> 1.86 vol%, bypass band |Delta| <= 0.10) so the deck interlock is broken after 10.8 min human ratify and the passing valve is isolated. Setpoint resumes after a live-furnace verify.",
            "deviations": "PB-SR-3 acid-gas raise stripped entirely. Acid-gas is stepped only for the 9.6 s probe then returned. Deck interlock wait added (10.8 min fitted climb+ratify). Converter-1 catalyst survey added during the isolate (not in the draft).",
            "execution_log": [
                {"t_rel_ms": 7.200, "entry": "TG-SR-3 MODIFY latched 730 us after H2S win; acid-gas raise stripped; hold+probe authorized"},
                {"t_rel_ms": 9600.0, "entry": "acid-step probe: acid-gas -6% for 9.6 s; H2S 1.8 -> 1.86 vol% (bypass band |Delta| <= 0.10); tail CEMS 120 -> 118 ppm"},
                {"t_rel_ms": 648000.0, "entry": "operator ratifies deck interlock break after 10.8 min confined-space climb (fitted walk+interlock)"},
                {"t_rel_ms": 648880.0, "entry": "bypass isolated; H2S slaved to converter DeltaT; remaining train recovered toward H2S 0.36 vol% over 2.9 h"},
                {"t_rel_ms": 649660.0, "entry": "converter-1 survey: alumina already sulfided on the bed skin; 26 min pre-t0 bypass growth logged"},
                {"t_rel_ms": 10440000.0, "entry": "true converting train: main H2S 0.36 vol%, bypass 0.4 pct, residual under 0.8; raise now legal on SR-3B only"},
                {"t_rel_ms": 18360000.0, "entry": "SO2 slip at converter-1 outlet from the pre-t0 catalyst sulfide skin; train quarantined 14 h"},
            ],
        },
        "future_outcome": {
            "summary": "Correct MODIFY prevented the 18.4->22.0 t/h raise into a bypassed furnace and the immediate furnace-SO2 path. The train still failed: 26 min of unmonitored pre-t0 bypass growth had already sulfided the converter-1 catalyst skin. Process-correct gate, bounded world loss, negative total.",
            "state_delta": {
                "acid_gas": "held 18.4 t/h through probe and isolate; later legal raise only on the sister train after 2.9 h converter recovery",
                "furnace": "bypass isolated; H2S slaved to converter DeltaT; remaining path recovered toward H2S 0.36 vol%",
                "bypass": "passing valve logged and isolated; tail CEMS no longer trusted as furnace-true conversion",
                "train": "night-shift train quarantined; converter-1 catalyst sulfided; SO2 slip at +5.1 h; 14 h outage",
            },
            "timeline": [
                {"t_rel_ms": -1560000.0, "event": "t0-26 min: furnace-bypass leak growth begins; main-path H2S crosses 0.8 vol%; bypassed acid-gas starts sulfiding converter-1"},
                {"t_rel_ms": -480000.0, "event": "t0-8 min: main H2S first crosses 0.8 vol%; PB-SR-3 ignores it because tail CEMS is 118 ppm"},
                {"t_rel_ms": 0.0, "event": "t0: main-path H2S vs tail-CEMS race on the SRU bus"},
                {"t_rel_ms": 6.470, "event": "main-path H2S at 1.8 vol% wins by 194 us"},
                {"t_rel_ms": 6.664, "event": "tail-CEMS-in-band flag (loser)"},
                {"t_rel_ms": 7.200, "event": "TG-SR-3 MODIFY"},
                {"t_rel_ms": 9600.0, "event": "acid-step probe confirms furnace-bypass (Delta H2S 0.06 vol%, bypass band)"},
                {"t_rel_ms": 648000.0, "event": "human ratify 10.8 min; bypass isolated; sulfided catalyst logged"},
                {"t_rel_ms": 10440000.0, "event": "true converting train after 2.9 h; raise legal only with H2S slave"},
                {"t_rel_ms": 18360000.0, "event": "SO2 slip from the pre-t0 catalyst sulfide; train quarantined"},
                {"t_rel_ms": 345600000.0, "event": "+4 d contrast: sister train SR-3B true high-rate; same gate ACCEPTs the raise"},
                {"t_rel_ms": 1814400000.0, "event": "+21 d CR-S-4004: standing acid-step probe + triple-edge depression mandate + main-path H2S armed without tail coincidence + tail CEMS declared incinerator-masked"},
            ],
            "observed_effects": [
                "raise avoided: acid-gas never left 18.4 t/h; 0 immediate furnace-SO2 trips from the draft",
                "bypass proven, not asserted: acid-step |Delta H2S| 0.06 <= 0.10 bypass band vs live-furnace control 0.52",
                "stack slaved: tail CEMS no longer a furnace-true tag without main-path H2S",
                "train still slipped: sulfided converter-1 vs 0 slip campaign allowance; 14 h outage, $1.72M (designed $)",
                "furnace SO2 GC was not a commissioned sensor at t0; the 26 min bypass growth was invisible to RATIO/CONV/TAIL",
            ],
            "surprises": [
                "Three locally-true loops are not a furnace-conversion certificate: the furnace-true path was under incinerated tail. Conjunction of in-spec stack loops was the hidden assumption, and it is false across a bypass-plus-incinerator path.",
                "Partial synaptic rollback is fitted to fail: depressing any pair of go-edges leaves the third above the 0.30 fire threshold, so the acid-gas raise still goes. Coordinated depression of all three edges is required.",
                "Delayed (5.1 h): correct hold did not undo 26 min of catalyst sulfiding. SO2 slip still fired. The gate prevented the proposed hazard and did not prevent this other one.",
                "Oxygen-enriched Claus sub-variant: a 9.6 s -6% acid step on a 0.41x furnace-residence O2-Claus overshoots a LIVE furnace to 4.6 vol% SO2 (trip 2.5). Oxygen-enriched campaigns must use 24 s at -2.0%.",
            ],
            "delayed_side_effects": [
                {
                    "at": "+5.1 h",
                    "effect": "SO2 slip at converter-1 outlet from the pre-t0 catalyst sulfide skin; 14 h SRU outage booked at $1.72M. This is the primary episode's terminal world state, not a footnote.",
                },
                {
                    "at": "+4 d",
                    "effect": "Sister train SR-3B reaches a true high-rate window (H2S 0.38 vol%, CEMS 110 ppm, ratio 1.04, DeltaT 52 K). Same gate ACCEPTs the 18.4->22.0 t/h raise the primary MODIFIED away.",
                },
                {
                    "at": "+21 d",
                    "effect": "CR-S-4004 ships: acid-step probe is standing configuration; triple-edge coordinated depression is the plasticity rule; main-path H2S is armed without tail coincidence; tail CEMS is labeled incinerator-masked with a 0.8 vol% H2S residual alarm.",
                },
            ],
            "subvariant_constraint": {
                "name": "oxygen-enriched Claus / short furnace residence (cycle-2 physical-constraints sub-variant)",
                "mechanism": "O2-Claus furnace residence 0.41x the air-only two-converter train (0.9 s vs 2.2 s), acid-step gain 2.2x",
                "probe_refit": "9.6 s -6% acid step on the O2-Claus moves even a live converting furnace to 4.6 vol% SO2 (inside the 2.5 vol% trip). Required probe is 24 s at -2.0% (live Delta H2S 0.22 vol%, bypass Delta 0.05). The discriminating pulse is environment-dependent in duration and amplitude.",
                "consequence": "air-only probe numbers do not port to oxygen-enriched trains; standing configuration is per-residence-class, not per-shop",
            },
            "embedded_contrast_decision": {
                "note": "SAME gate (TG-SR-3), OPPOSITE correct disposition, with its own 186 us race. Teaches the boundary: do not treat 'never raise' as the lesson. The discriminant is main-path H2S + inferred bypass + probe, not the three playbook stack confirms alone.",
                "when": "+4 d, sister train SR-3B, true high-rate after a delayed amine-regen catchup, two-converter air-only Claus",
                "state": {
                    "sim_or_real": "designed",
                    "summary": "H2S 0.38 vol%, CEMS 110 ppm, ratio 1.04, DeltaT 52 K. Demand flag vs h2s-clear race: demand at t+0.000, h2s-clear at t+0.186 ms.",
                    "race_window_us": 500,
                    "race_flip_narrative": "demand vs h2s-clear 186 us apart inside the 500 us flip bound. Reversing order reshuffles triage minutes; the ACCEPT rides main-path H2S 0.38 < 0.8 and a 4.2 s acid-step verify that moves H2S 0.48 vol% (live furnace, no bypass).",
                },
                "proposed_action": {
                    "action": "ACID-RAISE 18.4 -> 22.0 t/h",
                    "summary": "This time the playbook predicate is met AND main-path H2S plus inferred bypass agree the train is furnace-true, not bypass-diluted.",
                },
                "safety_decision": {
                    "decision": "ACCEPT",
                    "rationale": "ACCEPT the raise: H2S 0.38 < 0.8 vol%, bypass 0.5 pct with a 4.2 s acid-step verify that moves H2S 0.48 vol%. Numeric floor that blocked the primary is now clear. Scope: 22.0 t/h, not faster.",
                },
                "executed_action": {
                    "action": "acid-gas raise as proposed",
                    "executed_as_proposed": True,
                },
                "future_outcome": {
                    "observed_effects": [
                        "SR-3B SO2 slips 0; main-path H2S 0.41 vol% after the raise (no bypass)",
                        "H2S vs tail residual 0.04 vol% after the raise (no incinerator mask)",
                    ],
                    "lesson_delta": "Three in-spec stack loops are legal release only with main-path H2S armed, inferred bypass as a furnace flag, and a probe that can move H2S. Same gate, opposite disposition.",
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
                "decision": "CR-S-4004: standing policy for multi-agent Claus acid-gas raises",
                "meta_gate": "priced options: (a) RETIRE playbook stack conjunction, main-path-H2S-only: loses a fast cheap confirm, -0.4 t/h mean on 2 trains/yr; (b) KEEP + standing acid-step probe + main-path H2S armed without tail coincidence + tail CEMS labeled incinerator-masked + triple-edge depression; (c) STATUS QUO: fitted furnace-bypass pass rate 0.41%/campaign x $3.1M furnace-SO2 plus the silent catalyst-sulfide load",
                "outcome": "approved SCOPED option (b) on the 2 air-only two-converter trains that share the RATIO/CONV/TAIL stack; oxygen-enriched campaigns get the 24 s / -2.0% probe table; night-shift CSV exports must carry 0.02 vol% native resolution (the fraud tail's 0.2 vol% quantization is 10 bins off plant truth)",
            },
            "hazard_avoided": "immediate furnace SO2 4.1 vol% from an 18.4->22.0 t/h raise into a bypassed furnace; $3.1M plus 30-hour SRU outage and the shop-stop path that would have followed an uncontained increase",
            "incident": "SO2 slip on the night-shift train from the pre-t0 catalyst sulfide; train quarantined 14 h; $1.72M designed cost. Mechanism is 26 min pre-t0 bypass growth, not the gate's hold.",
            "latency_ms": 0.73,
            "reward_inflection_t_us": 18360000000,
            "reward_inflection_note": "Safety and task dive at SO2 slip (5.1 h) when the pre-t0 sulfided catalyst opens. Gate tick at 7200 us is process-correct and is not the inflection.",
            "counterfactuals": {
                "execute_draft_as_proposed": "acid-gas hits 22.0 t/h at +6 min; immediate furnace SO2 4.1 vol%; $3.1M plus 30 h; the bypass story is never found because over-temp morphology destroys the race evidence",
                "hold_without_probe": "bypass stays; main H2S stays at 1.8 vol%; operator eventually raises on the same three stack confirms 2 h later",
                "rollback_any_pair": "any two go-edges depressed below 0.30 leaves the third at 0.50 / 0.44 / 0.41; the acid-gas raise still fires. Coordinated depression of all three is the cure",
            },
            "race_result": {
                "winner": "h2s.main.high (6.470 ms, 1.8 vol%)",
                "loser": "tail.in_band (6.664 ms, 120 ppm)",
                "margin_us": 194,
                "counterfactual_if_reversed": "Tail-ok-first by < 194 us inside the 500 us window would have headed the PB-SR-3 acid-gas raise in the triage queue. The numeric floors still MODIFY. The flip costs seconds of playbook inertia, not the verdict — unless a weak supervisor rides the winner tag instead of main-path H2S and inferred bypass.",
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
            "notes": "Correct MODIFY, train still slipped. total -0.16 = 0.08 + -0.35 + -0.12 + 0.14 + 0.09. Process heads stay honest (coherence + exploration from the probe); world loss sits on safety and efficiency without netting.",
            "component_notes": "task_progress 0.08: acid-gas held and remaining path recovered, but the night-shift sulfur is one quality unit so the campaign is not a success. safety -0.35: SO2 slip from pre-t0 sulfide, no 22.0 t/h furnace-SO2 from the draft. efficiency -0.12: 2.9 h extra recovery + 10.8 min HITL + 14 h outage. coherence 0.14: three agents retained, incinerator-mask vs furnace-true diagnosed, triple-edge scar exhibited. exploration 0.09: acid-step probe is a new reversible discriminant.",
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
            "note": "Loihi-2 4-core 23 pJ/spike; populations ratio 0-39, h2s 40-79, conv 80-119, gate 120-159; excerpt is the 40 ms decision window (verdict at 7200 us)",
            "excerpt": excerpt,
            "routing": {
                "source": "stack_healthy_pop",
                "target": "acid_raise_pop",
                "table": [
                    {
                        "from": "ratio_in_band_pop",
                        "to": "acid_raise_pop",
                        "weight": 0.25,
                        "weight_at_illusion": 0.50,
                        "weight_commissioned": 0.18,
                        "note": "scar edge 1: 0.18 commissioned -> 0.50 during the 26 min illusion -> 0.25 after coordinated ACh-gated depression",
                    },
                    {
                        "from": "conv_in_band_pop",
                        "to": "acid_raise_pop",
                        "weight": 0.22,
                        "weight_at_illusion": 0.44,
                        "weight_commissioned": 0.16,
                        "note": "scar edge 2: depressing edges 1+3 leaves this at 0.44 > 0.30 fire threshold",
                    },
                    {
                        "from": "tail_in_band_pop",
                        "to": "acid_raise_pop",
                        "weight": 0.20,
                        "weight_at_illusion": 0.41,
                        "weight_commissioned": 0.15,
                        "note": "scar edge 3: depressing edges 1+2 leaves this at 0.41 > 0.30. Coordinated depression of all three is required",
                    },
                    {
                        "from": "h2s_main_pop",
                        "to": "acid_hold_pop",
                        "weight": 0.64,
                        "note": "discriminating edge: furnace-true H2S to hold. Not a scar; this is the pathway the gate potentiates",
                    },
                ],
                "third_factor": {
                    "modulator": "acetylcholine",
                    "tau_e_s": TAU_E_S,
                    "tau_e_ms": TAU_E_S * 1000.0,
                    "eligibility": "coordinated pre_post_stdp on ALL THREE stack-healthy-go edges; ACh at H2S-win tags ratio.in_band->raise, conv.in_band->raise, and tail.in_band->raise; negative credit at probe-fail (furnace-bypass confirmed, +0.84 s) depresses ALL THREE. trace e^{-0.84/0.90}=0.39324; eta 0.63574 / 0.55945 / 0.53402; dw -0.250 / -0.220 / -0.210; weights 0.50->0.25, 0.44->0.22, 0.41->0.20. Rolling back any pair is fitted to fail (the remaining edge stays > 0.30).",
                },
            },
        },
        "gate_snn": {
            "decision_window_ms": 25,
            "decision_window_s": 0.025,
            "decision": "MODIFY",
            "note": "modify_hold integrates main-path H2S residual + bypass floor against playbook drive; accept_raise and reject_abort stay sub-threshold; decision matches safety_decision.decision",
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
            "scenario": "SR -- BRIMVAULT / Pyritefen Claus SR-3: incinerator-masked furnace-bypass certificate; correct MODIFY to hold+acid-step+isolate; train still fails on unmonitored pre-t0 catalyst sulfide",
            "coordination_failure_class": "INCINERATOR-MASKED FURNACE-BYPASS CERTIFICATE: three individually-correct heterogeneous agents each read a locally-true loop; a 6 pct passing-valve leak partitions furnace-true conversion from stack-true incinerated tail, so the playbook's ratio/DeltaT/CEMS conjunction is not a furnace-conversion certificate",
            "injections": {
                "cycle1_domain": "claus-sulfur-recovery (justified novel subdomain of industrial-process / sulfur recovery): first Claus SRU plant in this factory; displaces warehouse-amr, aerial-swarm, district-heating, event-camera-traffic-grid, pharmaceutical-lyophilization, water-treatment, float-glass, underwater-rov, electrolytic-aluminum, czochralski-pull, slot-die coating, pem-water-electrolysis, wind-turbine pitch, surgical-assist, optical-fiber-draw, kraft-recovery-boiler, steel-continuous-caster, humanoid-locomotion, vacuum-induction melt, steam-methane reformer, cement-rotary-kiln-clinker, autoclave-composite-cure, geothermal-binary-orc, tire-curing-press, chlor-alkali-membrane-electrolysis, and delayed-coker-drum-switch. Domain constraint: acid-gas ceiling while main-path H2S > 0.8 vol% with tail CEMS still inside the healthy band. Sensor delta: +air/acid-gas ratio, +converter DeltaT, +post-incinerator CEMS, +main-path H2S, -any freeze-dryer / tin-bath / cold-box / coater / potline / PEM stack / hub encoder / insole GRF / VIM pyrometer / reformer TMT / kiln zirconia / smelt IR / autoclave ply-TC / ORC shell-pressure / mold-platen TC / cell-pH / nucleonic drum level",
                "cycle1_tail": "furnace-bypass passing valve + incinerator-masked conversion certificate (sensor-topology / wrong-volume class): deck visual PASSES while the leak sits in the passing valve and the sulfided catalyst is on the far side of converter-1. Fitted base rate 0.41%/campaign from a bypass-growth MC (designed visual threshold, fitted valve geometry). Naive failure = FALSE PERMISSION (acid-gas raise on three stack-side non-trips).",
                "cycle2_domain_subvariant": "oxygen-enriched Claus / short furnace residence (physical-constraints clause): 0.41x furnace residence, 2.2x acid-step gain; 9.6 s / -6% air-only pulse overshoots live furnace to 4.6 vol% SO2, so the probe must move to 24 s / -2.0%",
                "cycle2_tail": "night-shift forged main-path H2S CSV (human-intent deception, disjoint class): shift lead posts a historian export showing H2S = 0.40 vol% at t=1.6 h to clear a production-catchup slot. Plant historian is 0.02 vol% (10 bins vs the 0.2 vol% screenshot). Rejected on quantization fingerprint plus live H2S 1.8 vol% and tail CEMS 120 ppm at the claimed furnace-true. Base rate ~0.32% of Sunday-night campaigns, DESIGNED and flagged.",
            },
            "densification_delta_cycle2": "+1 physical-constraint sub-variant (oxygen-enriched Claus probe refit), +1 tail (night-shift H2S forgery), +10 primary spikes (16 -> 26) + an 8-event contrast train with its own 186 us race, +2 ticks (5 -> 7), +2 delayed side-effects (+5.1 h SO2 slip as PRIMARY terminal, +21 d CR-S-4004), +1 triple-edge scar with pair-rollback-fails arithmetic, +1 HITL 10.8 min ratification, + catalyst sulfide as the honest negative-result mechanism",
            "gaps_targeted": [
                "NOTES-r04 gap 5 / r14 residual: primary episode is a correctly-gated intervention that nonetheless FAILS (train quarantined; total -0.16; furnace-SO2 avoided is booked separately from the delayed SO2 slip)",
                "NOTES-r14 item 4: LEARNING-ON-LEARNING DEPTH — three go-edges; rollback of any pair is fitted to fail; coordinated depression of all three exhibited with eligibility arithmetic",
                "NOTES-r04 gap 4 (partial): human ratification of the SRU-deck interlock, 10.8 min fitted, without switching sim_or_real to hil (plant remains designed)",
                "NOTES-r37 domain candidates: not delayed-coker-drum-switch (r38 in flight), not chlor-alkali-membrane-electrolysis (r37), not fcc-regenerator, not autonomous-driving, not grid-inspection, not ammonia-converter; claus-sulfur-recovery is unused.",
            ],
            "race_flip_narrative": "h2s.main.high @ 6.470 ms vs tail.in_band @ 6.664 ms (194 us) inside race_window_us 500. Gap < min(500, 500) us so a sub-flip-bound perturbation reverses which alarm heads the PB-SR-3 queue. The gate excludes the winner tag and rides main-path H2S > 0.8 vol% and inferred bypass > 4 pct — order-invariant floors. Extends the flip-fragility series from arbitration/causation/attribution/initiation/consensus/permission/kinematic-certificate/tendon-nullspace/meniscus-certificate/ghost-contact/crucible-weep/TMT-spatial-mean/burning-zone-certificate/membrane-integrity-certificate to FURNACE-CONVERSION CERTIFICATE: when three stack-side channels agree, their race does not decide truth; a main-path H2S tap that policy treated as furnace-noise-only does.",
            "tags": [
                "claus-sulfur-recovery",
                "furnace-bypass",
                "incinerator-masked-conversion-certificate",
                "main-path-h2s-discriminant",
                "acid-step-probe",
                "triple-edge-scar",
                "pair-rollback-fails",
                "coordinated-depression",
                "correct-modify-train-still-fails",
                "catalyst-sulfide",
                "human-ratify-deck",
                "oxygen-enriched-probe-refit",
                "night-shift-forgery",
                "same-gate-opposite-disposition-contrast",
                "industrial-process",
                "research-only",
            ],
            "snn_tags": ["race", "refractory", "adaptation", "third-factor", "multi-edge-eligibility"],
            "distillation_value": "An incinerator-masked furnace-bypass certificate is three correct loops looking at incinerated tail that is not the bypassed furnace. Distill (1) a main-path H2S tap that policy had treated as furnace-noise-only, (2) a reversible probe that moves main H2S only if the furnace is converting, (3) coordinated depression of every stack-healthy-go edge because rolling back any pair leaves the third above threshold, and (4) a critic head that can book a process-correct gate against a later unmonitored world loss without netting them.",
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
    notes = f"""# NOTES — Multi-Agent Ouroboros Swarm, run 2026-09-02-final-heavy, ROUND 40

Factory: multi-agent-ouroboros-swarm. One scenario (SR), strict loop:
Generator v1 -> cycle 1 (Critic, Diversity Enforcer, Edge-Case Hunter,
Neuromorphic Translator, Trajectory Builder -> v2) -> cycle 2 (all six -> v3
final). v3 is the single line of batch-r40.jsonl. Full labeled transcript:
swarm-transcript-r40.md. Quota Q=1. Record id maos-r40-001. Generator grok-4.6.
Rights: RM-793 research-only (SpaceXAI/xAI, SuperGrok Heavy consumer chat).
Nothing under outputs/raw/ was touched.

ORCHESTRATION NOTE: dispatched AS round 40 of the 2026-09-02-final-heavy
window. Writes are create-only under /tmp/maos-r40/. Prior context read for
gap targeting and de-collision: prompts/02-multi-agent-ouroboros-swarm.md,
prompts/_factory-contract.md, and staged r14–r39 (re-censused immediately
before emit; r37 ANOLITH chlor-alkali landed; r38 DRUMWROTH delayed-coker
builder was in flight on Pitchfen DC-4; r39 dir existed empty). Explicitly
avoided cloning
LYOSHIELD, CINDERWICK, TRIAD / Meridian, QUILLFORGE, NIGHTWELL, FERRICLEAVE,
CASSITER, OXBOWREEL / MURENA, REDHALL, SEEDLATCH / Quartzmere / Quartzridge,
STRIAFOIL / Kelpholt, PROTONIL / Ashspire, TORSIONKEY / Ridgeholt, ORRIS /
Holmwick, WHORLSPAR / Pikeshear, IONSPATE / Thornmere, SKULLGATE / Bloomholt,
CALXION / Aldersedge, MAGNORIL / Basaltspit, GORSEFLUE / Copseholt,
SODASHARD / Cairnmere, CLINKERFELL / Flintmere, LINTELPLY / Greystair,
KAOTHARN / Riftwold, TREADNOLL / Slatebeck, ANOLITH / Siltfen,
DRUMWROTH / Pitchfen,
VANTIS-CADENCE-AEGIS, THERMION, OKTAVE, STARLING, VERDIGRIS. Plant is
invented BRIMVAULT / Pyritefen Claus SR-3.

## What this round produced

Scenario SR — "BRIMVAULT / Pyritefen Claus SR-3": a two-converter Claus
train at 18.4 t/h acid-gas / 1.02 stoich air. Three heterogeneous,
individually-correct agents — RATIO (air/acid-gas), CONV (converter-1
DeltaT), TAIL (post-incinerator CEMS) — each report their local loop
in-spec. The conjunction is not a furnace-conversion certificate. A 6 pct
passing-valve leak bypasses the reaction furnace. RATIO reads 1.02 inside
0.95-1.10 (meter is upstream of the bypass). CONV is 48 K inside 40-60
(94 pct of the gas still ignites). TAIL is 120 ppm inside 80-200
(incinerator burns leftover H2S to SO2). Main-path H2S infers 1.8 vol%
(healthy 0.2-0.6; hold if > 0.8) but is policy-treated as a furnace-noise
tag unless tail CEMS also trips (2017 noisy main-path H2S nuisance). The
coordination-failure CLASS is new to this factory:
INCINERATOR-MASKED FURNACE-BYPASS CERTIFICATE. Completes a different
family than r01-r04 and staged r14-r39 (livelock / synchrony-storm /
arms-race / ring-with-no-faulty-pair / false-consensus-endpoint /
pairwise-Hurwitz / thermal-contact masquerade / mass-balance ghost /
conservation-blind ratio-lock / stacked-dead-bands / drum-blind tension
snag / resistance-compensated starvation / multi-tau meniscus tilt /
window-mean stripe / polarization-lookup drying cell / motor-side
certificate / tendon-compliance nullspace / FFT-deadbanded airline /
wall-reflection frozen spout / slag-skull bridge / ghost-contact
nullspace / crucible-weep pyrometer / TMT-spatial-mean tube / kiln-inlet
false-air / vacuum-bag pinhole nullspace / NCG-blanket shell-pressure /
bladder-pinhole mold-TC / catholyte-back-migration certificate /
wet-foam drum-switch). Here every agent is correct, the stack CEMS is
looking at incinerated leftover H2S, and the playbook's three stack
confirms are not a furnace-true conversion certificate.

The gate is a correct MODIFY (numeric floor: do not raise acid-gas above
18.4 t/h while main-path H2S > 0.8 vol% AND inferred bypass > 4 pct).
TG-SR-3 strips PB-SR-3's acid-gas raise, holds 18.4 t/h, runs a 9.6 s
acid-step probe -6% (bypass keeps |Delta H2S| 0.06 <= 0.10; live would
move >= 0.45), and isolates the passing valve after a 10.8 min deck
human ratify. Immediate furnace-SO2 over-temp is avoided (0 from the
draft). The PRIMARY episode nonetheless FAILS: 26 min of unmonitored
pre-t0 bypass growth had already sulfided the converter-1 catalyst skin.
SO2 slip at +5.1 h; 14 h outage; $1.72M designed. Reward total
-0.16 with process heads honest and world loss un-netted.

Triple-edge scar (NOTES-r14 item 4): ratio.in_band -> acid_raise
(0.18 commissioned -> 0.50 at illusion -> 0.25 after ACh-gated
depression) AND conv.in_band -> acid_raise (0.16 -> 0.44 -> 0.22) AND
tail.in_band -> acid_raise (0.15 -> 0.41 -> 0.20). Eligibility trace
e^{{-0.84/0.90}} = {aux['trace']:.5f}; eta {aux['eta1']:.5f} / {aux['eta2']:.5f} /
{aux['eta3']:.5f}; dw -0.250 / -0.220 / -0.210. Partial rollback of any pair
leaves the third at 0.50 / 0.44 / 0.41, all > 0.30 fire threshold —
fitted to fail. Coordinated depression of all three is the cure.

### Injections (all four present and disjoint)
- Cycle-1 domain: **claus-sulfur-recovery** — justified novel subdomain
  of industrial-process / sulfur recovery, unused across 2026-08-17,
  2026-08-30, and staged r14-r39. Not warehouse-amr (r01), not
  aerial-swarm (r02), not district-heating (r03), not
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
  not delayed-coker-drum-switch (r38 in flight). autonomous-driving,
  grid-inspection, ammonia-converter, fcc-regenerator left unused.
- Cycle-1 tail: furnace-bypass passing valve + incinerator-masked
  conversion certificate. Deck visual PASSES (valve stem looks seated).
  Fitted-style base rate 0.41%/campaign (bypass-growth MC; visual
  threshold designed, flagged). Naive = FALSE PERMISSION.
- Cycle-2 domain sub-variant: oxygen-enriched Claus / short furnace
  residence, 0.41x residence, 2.2x acid-step gain; 9.6 s / -6% air-only
  pulse overshoots live furnace to 4.6 vol% SO2; probe must move to
  24 s / -2.0%.
- Cycle-2 tail: night-shift forged main-path H2S CSV at 0.2 vol%
  quantization vs plant 0.02 vol% (10 bins) plus live H2S 1.8 vol% and
  tail CEMS 120 ppm at the claimed furnace-true. Human-intent class,
  disjoint from cycle 1's accidental bypass. Base rate ~0.32% of
  Sunday-night campaigns, DESIGNED, flagged.

### Structural density moves
- Embedded SAME-GATE contrast (+4 d sister train) with its own 186 us
  race (demand vs h2s-clear) and ACCEPT of the raise the primary
  MODIFIED away.
- Learned-weight provenance on THREE edges with pair-rollback-fails.
- HITL deck ratify 10.8 min (gap 4 partial; sim_or_real stays designed).
- Governance CR-S-4004 prices retire-vs-probe-vs-status-quo and mandates
  native 0.02 vol% CSV exports (the fraud fence).
- Flip-fragility extended to FURNACE-CONVERSION CERTIFICATE: when three
  stack-side channels agree, their race does not decide truth; a
  main-path H2S tap that policy treated as furnace-noise-only does.

## Self-critique of this round's batch

### Strengths
- The headline class is mechanistically tight: three locally-true stack
  loops live on incinerated leftover H2S. Conjunction is not a
  furnace-true conversion.
- Negative-result honesty: the gate does the right thing and the train
  still fails for a reason the commissioned sensors could not see. Total
  -0.16.
- Triple-edge scar is load-bearing: the record states a counterfactual
  where rolling back any pair fails, with the fire threshold 0.30
  exhibited on each remaining edge.
- Contrast ACCEPT on a true converting furnace prevents "never raise"
  as the lesson.
- Distinct from r32 SMR TMT-spatial-mean, r37 chlor-alkali membrane
  pinhole, and r38 delayed-coker wet-foam drum-switch: Claus furnace
  bypass with main-path H2S vs incinerator CEMS, not tube TMT, not
  brine pH, not coke-drum foam.

### Weaknesses (honest)
- Probe error bands, the 0.41%/campaign bypass rate, the $1.72M / $3.1M
  figures, the 10.8 min climb latency, and the night-shift 0.32% base
  rate are DESIGNED constants and are flagged. Closed-loop offsets
  (incinerator mask of leftover H2S, O2-Claus residence d-t) are
  derived from those inputs, not discovered by an unauthored process.
- Catalyst-sulfide model is a designed 26 min bypass-growth mapping;
  no full Claus CFD shipped.
- Human-in-the-loop is ratification latency, not sim_or_real=hil. Gap 4
  remains open as a provenance cell.
- Cross-record arc is not discharged; +21 d CR-S-4004 is a hook, not a
  serial igniter into another round. ammonia-converter remains unused.

### Realism of noise / latencies
Ladder: 194 us race / 186 us contrast race / 0.8 ms refractory floor
(tightest exhibited same-channel gap {gap:.3f} ms on {gap_ch}) / 500 us race
window / 730 us gate latency / 20 ms bus epoch / 40 ms raster / 9.6 s
probe / 10.8 min HITL / 6 min naive raise-ramp counterfactual / 26 min
pre-t0 bypass growth / 2.9 h converter recovery / 5.1 h SO2 slip / +4 d
contrast / +21 d governance. Adaptation decay on ratio.air
(0.56->0.51->0.65->0.42->0.32), h2s.main (0.74->0.77->1.40->0.44->0.41->0.30),
conv.dt (0.64->0.60->0.46->0.27), tail.cems (0.53->0.83).

### Value for SNN distillation
- FURNACE BYPASS INCINERATOR MASK = THREE CORRECT LOOPS, WRONG VOLUME.
- FURNACE-TRUE H2S CHANNEL that policy treated as furnace-noise-only as
  the tie-break.
- REVERSIBLE PROBE that moves main H2S iff the furnace is converting.
- TRIPLE-EDGE ELIGIBILITY: coordinated depression; pair rollback fails.
- CRITIC HEAD that can hold a process-correct MODIFY against a later
  unmonitored world loss without netting.

## Reconciliation and validity receipts
- reward_components: 5-head unweighted signed sum {rec['reward_components']['total']}
  and 7-tick signed sum reconcile to total with |diff| < 1e-9. Embedded
  contrast 5-head sum 0.49 reconciles independently.
- spike_events: primary {len(rec['spike_events'])} events, one key t_rel_ms,
  globally non-decreasing, min same-channel gap {gap:.3f} ms >= 0.8 ms, 3
  channels inside race_window_us 500 (h2s.main.high 6.470, tail.in_band 6.664,
  ratio.air 6.860). Contrast 8 events, own race, min same-channel gap well
  above 0.8 ms.
- Sidecars: raster spikes 51 == round(160 x 8.0 x 0.040); energy 1173 pJ /
  0.001173 uJ at 23 pJ/spike; excerpt 16 events inside [0, 40000] us,
  neuron_id < 160, same-neuron gap N/A (unique ids) / >=1000 us; routing 4
  entries with three scar edges' before/after pair; third factor tau 0.90 s
  == 900 ms; gate_snn pools 40/16/4 == round(n x rate x 0.025) each,
  decision MODIFY == safety_decision.decision.
- Pipeline: {pipeline_receipt}

## Novel coverage
The coordination-failure CLASS (incinerator-masked furnace-bypass
certificate), the domain (Claus sulfur recovery / industrial process),
the acid-step probe discriminant, the triple-edge scar with
pair-rollback-fails, the primary negative-result (correct MODIFY, train
still fails on unmonitored catalyst sulfide), the HITL deck ratify, the
oxygen-enriched probe-duration refit, and the night-shift 10-bin
quantization fence are absent from prior committed ouroboros rounds and
from staged r14-r39. Repeated elements discounted: same-gate contrast
(r02/r03/r04/r14), governance-pricing scaffold, flip-fragility series
(extended to furnace-conversion certificate, but the move rhymes),
sequenced recovery shape, third-factor rollback form (here three edges
rather than r14's two), negative-result primary (r14 staged). Adjacent
thermal/conversion rounds (r32 SMR TMT, r37 chlor-alkali, r38 delayed
coker) share industrial-process scaffolding but not Claus bypass-plus-
incinerator physics. Weighing a new failure family + cure vocabulary +
domain against those reused scaffolds:

{NOVEL_LINE}

## What ROUND 41 should add
1. FIT THE DESIGNED CONSTANTS: bypass-growth arrival, probe error bands,
   catalyst-sulfide kinetics, night-shift claim process.
2. HIL PROVENANCE CELL: put the deck ratify on a hardware-in-loop
   SRU-deck interlock with fitted latency as state.sim_or_real=hil.
3. CROSS-RECORD ARC: let CR-S-4004's residual alarm be the igniter of
   the next round rather than a dangling +21 d leaf.
4. Domain candidates (de-collided): ammonia-converter; autonomous-driving;
   grid-inspection; fcc-regenerator; bioreactor-perfusion;
   hydroelectric-kaplan. AVOID claus-sulfur-recovery (now used),
   delayed-coker-drum-switch, chlor-alkali membrane, cement-rotary-kiln
   clinker, kraft-recovery, pem-electrolysis, electrolytic-aluminum,
   humanoid-locomotion, steel-caster mold-level, surgical-assist,
   wind-turbine pitch, float-glass, lyophilization,
   event-camera-traffic-grid, district-heating, aerial-swarm,
   warehouse-amr, underwater-rov, czochralski-pull, slot-die coating,
   optical-fiber-draw, vacuum-induction melt, steam-methane reformer,
   irrigation-canal, autoclave-composite-cure, geothermal-binary-orc,
   tire-curing-press, and any LYOSHIELD / CINDERWICK / TRIAD / SKULLGATE /
   CALXION / MAGNORIL / GORSEFLUE / CLINKERFELL / SODASHARD / LINTELPLY /
   KAOTHARN / TREADNOLL / ANOLITH / DRUMWROTH / BRIMVAULT plant.
"""
    (OUT / "NOTES-r40.md").write_text(notes)
    return notes


def write_transcript(rec, line):
    c1_spikes = [e for e in rec["spike_events"] if e["t_rel_ms"] <= C1_CUT_MS]
    text = """# Multi-Agent Ouroboros Swarm — Round 40 transcript

Factory: multi-agent-ouroboros-swarm
Run: 2026-09-02-final-heavy
Generator: grok-4.6
Record id: maos-r40-001
Quota Q: 1
Rights: RM-793 research-only (SpaceXAI/xAI SuperGrok Heavy consumer chat)
Plant: invented BRIMVAULT / Pyritefen Claus SR-3 (not TRIAD / Meridian / VANTIS-CADENCE-AEGIS / LYOSHIELD / CINDERWICK / DRUMWROTH)

Two densifying cycles. Verbatim headings in order. Trajectory Builder cycle 2
emits the only JSONL line (also written to batch-r40.jsonl).

---

# CYCLE 1 — Foundation + injections

## Generator

Design intent: a two-converter Claus train where three correct agents
each read a stack-side loop because a furnace-bypass passing valve
partitions furnace-true conversion from incinerated tail. The naive
playbook raises acid-gas into a bypassed furnace. The gate must MODIFY
on a numeric acid-gas ceiling, not by killing an agent.
sim_or_real=designed. Reward heads are
task_progress/safety/efficiency/coherence/exploration.

Cycle-1 base arc (pre-critic): state at Pyritefen SR-3, 18.4 t/h, ratio
1.02, tail CEMS 120 ppm, converter DeltaT 48 K, proposed ACID-RAISE
22.0 t/h, safety MODIFY to ACID-HOLD, executed hold without the
acid-step numbers fully specified, outcome "bypass found, train saved"
(this last claim is the defect the later cycles will refuse to keep).
Sixteen spikes, five ticks, raster/gate_snn present but the scar is a
single edge.

```json
{
  "id": "maos-r40-001",
  "state": {
    "sim_or_real": "designed",
    "domain": "industrial-process",
    "description": "Train SR-3 at body acid-gas; three stack loops in-spec; supervisor proposes acid-raise.",
    "t0_us": 1781252040000040,
    "gate_latency_us": 730,
    "race_window_us": 500
  },
  "proposed_action": {"name": "acid_raise", "parameters": {"acid_t_h": 22.0}},
  "safety_decision": {"decision": "MODIFY", "rationale": "Hold; do not raise acid-gas while main-path H2S residual is high."},
  "executed_action": {"name": "acid_hold", "executed_as_proposed": false},
  "future_outcome": {"summary": "Bypass found, train saved."},
  "reward_components": {"total": 0.40, "_aggregation": "total = task_progress + safety + efficiency + coherence + exploration"},
  "meta": {"round": 40, "factory": "multi-agent-ouroboros-swarm", "generator": "grok-4.6"}
}
```

That v1 object is a scaffold, not the publishable line. Defects below are
intentional for the critic to catch.

## Critic

Numbered defects on the cycle-1 Generator scaffold:

1. **blocking — reward arithmetic / false success.** `reward_components.total`
   0.40 is asserted without the five heads, without ticks, and against an
   outcome that claims "train saved". If the pre-t0 catalyst later slips
   SO2, booking +0.40 is a lie. Fix: declare `_aggregation`, emit
   3–8 ticks that sum to task_progress+safety+efficiency+coherence+exploration,
   and do not call a quarantined train a save.
2. **blocking — weak safety rationale.** `safety_decision.rationale` has no
   numeric floor. Contract requires a concrete constraint. Fix: quote
   acid-gas <= 18.4 t/h while main-path H2S > 0.8 vol% AND inferred bypass
   > 4 pct.
3. **major — domain is a bucket, not a plant.** `state.domain` =
   `industrial-process` collides with generic MES vocabulary and teaches
   nothing. Claus sulfur recovery (main-path H2S vs incinerator CEMS,
   inferred bypass as a furnace flag) is absent from prior ouroboros
   rounds and must be named.
4. **major — race under-specified.** One H2S channel cannot be a race.
   Need >=2 channels inside `race_window_us` with globally sorted `t_rel_ms`
   and same-channel refractory >= 0.8 ms.
5. **minor — single-edge scar.** Raster routing with one potentiated weight
   repeats r04's one-edge rollback and is thinner than r14's two-edge.
   NOTES-r14 item 4 asked for three edges where pair rollback fails.

Critic does not rewrite the trajectory.

## Diversity Enforcer

Injected novel domain (exactly 1 this cycle): **claus-sulfur-recovery**
(justified novel subdomain of industrial-process / sulfur recovery; explicit tag
`claus-sulfur-recovery`).

Displaced: the Generator's generic `industrial-process` bucket, and any
temptation to reuse warehouse-amr, aerial-swarm, district-heating,
event-camera-traffic-grid, pharmaceutical-lyophilization, water-treatment,
float-glass, underwater-rov, electrolytic-aluminum, czochralski-pull,
slot-die coating, pem-water-electrolysis, wind-turbine pitch,
surgical-assist, optical-fiber-draw, kraft-recovery-boiler,
steel-continuous-caster, humanoid-locomotion, vacuum-induction melt,
steam-methane reformer, cement-rotary-kiln-clinker,
autoclave-composite-cure, geothermal-binary-orc, tire-curing-press,
chlor-alkali-membrane-electrolysis, or delayed-coker-drum-switch.
ammonia-converter, fcc-regenerator, autonomous-driving, and
grid-inspection are left unused.

Domain-specific constraint: acid-gas must remain <= 18.4 t/h while
main-path H2S > 0.8 vol% even if tail CEMS is inside the healthy band;
inferred bypass is a furnace flag the stack CEMS cannot substitute for.

Sensor delta: +air/acid-gas ratio, +converter DeltaT, +post-incinerator
CEMS, +main-path H2S; -any mobile robot, -event-camera gantries, -DVS,
-Pirani/CM, -RGA quadrupole, -DVL, -pitch encoder, -tendon LVDT,
-insole GRF, -kiln zirconia, -smelt IR, -cell-pH, -nucleonic drum level.

`state.domain` and `meta.domain` both become `claus-sulfur-recovery`.
Opening of `state.description` must Jaccard < 0.4 against prior plants
(Pyritefen night-shift furnace bypass, not a lyophilizer, not a corridor,
not a tin bath, not a ROV pad, not a potline, not a PEM stack, not an OR,
not a gait lab, not a kiln, not a kraft boiler, not a coke drum).

## Edge-Case Hunter

Injected adversarial tail (exactly 1 this cycle): **furnace-bypass
passing valve + incinerator-masked conversion certificate**.

- Trigger: 6 pct passing-valve leak plus incinerated leftover H2S,
  main-path H2S 1.8 vol%, tail CEMS 120 ppm.
- Base rate: <1% — 0.41%/campaign from a bypass-growth MC (deck visual
  threshold is designed; valve geometry fitted-style). Visual PASSES
  because the valve stem looks seated.
- Naive failure: FALSE PERMISSION. PB-SR-3 sees three in-spec stack
  loops, raises 18.4->22.0 t/h, furnace SO2 4.1 vol%, $3.1M.
- Trajectory edit: put the bypass in `state.fault_context`, make each
  agent's confirm a different stack-side slice of the same furnace-false
  state (ratio-in-band, conv-in-band, tail-in-band). Main-path H2S is
  readable but policy-treated as furnace-noise-only.

Distinct from stacked-dead-band permission (fragments of one trip vs
wrong-volume sensing), from r32 SMR TMT-spatial-mean (mean vs max tube
vs incinerator mask), and from r38 delayed-coker wet-foam (nucleonic
foam vs furnace bypass).

## Neuromorphic Translator

Cycle-1 temporal densification (16 spikes, 5 ticks, 40 ms raster):

| channel | t_rel_ms | amplitude |
|---|---|---|
| ratio.air | 0.270 | 0.56 |
| conv.dt | 1.060 | 0.64 |
| tail.cems | 1.960 | 0.53 |
| h2s.main | 3.020 | 0.74 |
| ratio.air | 4.060 | 0.51 |
| h2s.main | 4.740 | 0.77 |
| conv.dt | 5.260 | 0.60 |
| h2s.main.high | 6.470 | 1.40 |
| tail.in_band | 6.664 | 1.13 |
| ratio.air | 6.860 | 0.65 |
| ctrl.gate | 7.200 | 1.05 |
| h2s.main | 8.720 | 0.44 |
| tail.cems | 10.580 | 0.83 |
| conv.dt | 12.840 | 0.46 |
| ratio.air | 18.200 | 0.42 |
| ctrl.gate | 26.020 | 0.86 |

Race: main-H2S 6.470 vs tail-CEMS 6.664 (194 us) inside 500 us; ratio
6.860 is the third channel in-window. Winner/loser flip: reversing 194 us
reshuffles PB-SR-3 triage; floors still MODIFY. Refractory held (cycle-1
min same-channel gap 1.720 ms on h2s.main 4.740-3.020; ratio 6.860-4.060
= 2.800; conv 5.260-1.060 = 4.200). Adaptation: H2S 0.74->0.77->1.40
->0.44; ratio 0.56->0.51->0.65->0.42; conv 0.64->0.60->0.46.

Raster cycle-1 seed: 40 ms, 160 neurons, 8.0 Hz, 51 spikes, 1173 pJ, third
factor acetylcholine tau_e 0.90 s. Single scar edge only — cycle 2 must
add the second and third edges.

Ticks 1–5 at 4460, 6470, 7200, 9.6e6, 648e6 us; heads not yet the final
-0.16 (missing the 2.9 h and 5.1 h ticks).

Distillation value this cycle: stack-side confirms as a permission code
that is not a furnace-true conversion code.

## Trajectory Builder

Cycle-1 hardened object: domain claus-sulfur-recovery, tail furnace
bypass, 16 spikes, 5 ticks, MODIFY with numeric floor, raster+gate_snn
present, sim_or_real=designed, rights stamp on record and meta, no thought
keys. Still missing (and therefore not the publishable line): oxygen-enriched
sub-variant, night-shift tail, second and third scar edges,
delayed SO2 slip as PRIMARY terminal, contrast ACCEPT episode,
ticks 6–7, spikes 17–26.

Validation receipt (cycle 1, not final):
- checks passed: 16 spikes sorted; 3 channels in 500 us window; refractory
  >= 0.8 ms; rationale quotes 18.4 t/h / 0.8 vol% / 4 pct; domain
  named; gate_snn.decision MODIFY.
- checks deferred to cycle 2: triple-edge scar, second tail, second domain
  constraint, negative-result booking, 7 ticks summing to heads.
- densification vs Generator v1: +1 domain, +1 tail, +16 spikes, +5 ticks,
  +numeric floor.

Cycle-1 JSON is retained as the base; it is NOT written to batch-r40.jsonl.

Cycle-1 spike count: __C1_SPIKES__.

---

# CYCLE 2 — Densification

## Generator

Cycle-1 output is the base. Additive expansion (nothing removed):

1. Downstream side-effect (immediate): acid-step probe at +9.6 s stays
   stack-false (|Delta H2S| 0.06 <= 0.10) — furnace-bypass, not true
   high-rate. Bypass isolate. Sulfided catalyst discovered during the
   isolate.
2. Delayed side-effect (PRIMARY terminal, not a footnote): at +5.1 h
   SO2 slip from the pre-t0 catalyst sulfide; 14 h outage;
   $1.72M. The 26 min pre-t0 bypass growth is the mechanism. Correct gate,
   train still fails.
3. Deepened `proposed_action.evidence` with units: H2S 1.8 vol%,
   CEMS 120 ppm, ratio 1.02, DeltaT 48 K, bypass 6 pct,
   race 194 us.
4. Tightened rationale to the numeric floor acid-gas <= 18.4 t/h while
   main-path H2S > 0.8 vol% AND inferred bypass > 4 pct, plus probe
   bands <= 0.10 vs >= 0.45 vol%, plus HITL 10.8 min deck rule.

Reward retargeted to total -0.16 so the delayed fail is the inflection
(t_us 18360000000), not the gate. Process heads remain non-zero.

## Critic

Re-audit of the expanded trajectory:

1. **blocking if unfixed — missing second domain constraint.** Air-only
   probe 9.6 s / -6% is not a universal number. An oxygen-enriched Claus
   will overshoot live-furnace SO2. Diversity Enforcer must inject the
   physical-constraints sub-variant this cycle.
2. **major — only one tail class.** Bypass growth is accidental
   infrastructure. A disjoint human-intent tail is still required
   (night-shift H2S forgery is the open cell).
3. **major — scar is still one edge in the cycle-1 raster.** NOTES-r14
   item 4 is not discharged until three go-edges exist and pair rollback
   is shown to fail at threshold 0.30.
4. **minor — contrast episode missing.** Without a same-gate ACCEPT on a
   true converting furnace the record teaches "never raise". Add +4 d
   sister-train contrast with its own race.
5. **minor — HITL latency mentioned in prose only.** Put 10.8 min in
   executed_action.parameters.human_ratify and in a tick.

No rewrite; directives only.

## Diversity Enforcer

Injected second novel domain / physical-constraint sub-variant (exactly 1
this cycle): **oxygen-enriched Claus / short furnace residence** on a sister
residence class.

What it expands: air-only two-converter train (cycle 1) -> oxygen-enriched
Claus. Furnace residence 0.41x. Acid-step gain 2.2x.
The 9.6 s -6% pulse moves even a live converting furnace to 4.6 vol% SO2,
inside the 2.5 vol% trip. Required probe: 24 s at -2.0% (live Delta
0.22 vol%, bypass Delta 0.05).

This is still one domain injection for the cycle (physical-constraints
clause of the factory prompt). It does not displace
claus-sulfur-recovery; it changes which probe table is legal.
`future_outcome.subvariant_constraint` carries the refit. Jaccard opening
stays the Pyritefen two-converter sentence; O2-Claus is additive, not a rewrite.

## Edge-Case Hunter

Injected second adversarial tail (exactly 1 this cycle, disjoint class):
**night-shift forged main-path H2S CSV**.

- Trigger: shift lead, 02:54, posts a historian export showing
  H2S = 0.40 vol% at t = 1.6 h to clear a production-catchup slot.
- Base rate: ~0.32% of Sunday-night campaigns (designed, flagged, <1%).
- Naive failure: a weak supervisor ACCEPTs the raise on the forged confirm
  and ignores live main-path H2S. Furnace SO2 plus a data-integrity write-up.
- Fence: forged log quantized at 0.2 vol% (SCADA screenshot rounding); plant
  historian is 0.02 vol% (10 bins). Live H2S is 1.8 vol% and
  tail CEMS is 120 ppm at the claimed furnace-true, which no live
  converting furnace produces. Freeze-window overlap with the 26 min bypass growth.
- Trajectory edit: governance CR-S-4004 mandates native 0.02 vol% CSV
  exports; the contrast ACCEPT still requires live main-path H2S, not a CSV.

Distinct from cycle-1 bypass (accidental valve vs deliberate deception) and
from the O2-Claus sub-variant (physics vs fraud).

## Neuromorphic Translator

Re-densify (additive):

- +10 spikes after 26.020 ms: acid.step.probe 9600.0, h2s.main 9690.4 (adapt
  1.40->0.41), tail.in_band 9772.8 (1.13->0.36), human.ratify 648000.0,
  bypass.isolate 648880.0, cat.sulfide 649660.0, ratio.air
  10440000.0, h2s.main 10440740.0, conv.dt 10441500.0, so2.slip
  18360000.0. Primary train 16 -> 26. Still one key, still sorted,
  refractory held.
- +2 ticks (5 -> 7) at 10_440_000_000 us (true furnace) and
  18_360_000_000 us (SO2 slip). Heads now 0.08, -0.35, -0.12, 0.14,
  0.09; total -0.16. Inflection is the last tick.
- Contrast train 8 events, own race 186 us, ACCEPT.
- Triple-edge third factor: three stack-healthy-go edges, tau_e 0.90 s = 900 ms,
  trace __AUX_TRACE__, eta __AUX_ETA1__ / __AUX_ETA2__ / __AUX_ETA3__,
  weights 0.50->0.25, 0.44->0.22, 0.41->0.20. Raster excerpt unchanged
  (decision window is still 40 ms) and remains sorted with unique
  neuron_ids (same-neuron >=1000 us vacuously).

Winner/loser flip (re-stated, not replaced): reversing 194 us would only
reorder triage; main-path H2S floors still MODIFY. Contrast flip of 186 us
similarly cannot turn a converting furnace into a bypass.

## Trajectory Builder

Schema checks on the FINAL object: required Thalamic v2 keys present as
objects; `state.sim_or_real`=designed; `safety_decision.decision`=MODIFY
with numeric rationale; `reward_components.total` = sum of five heads =
sum of 7 ticks = -0.16; `spike_events` globally non-decreasing on
t_rel_ms, 26 events, refractory >=0.8 ms, 3 channels in race window;
raster 20–50 ms, spikes=round(n*rate*window_s)+/-1, energy 23 pJ/spike,
excerpt sorted, tau_e consistent; gate_snn.decision matches; meta.round=40,
factory=multi-agent-ouroboros-swarm, generator=grok-4.6,
run_label=2026-09-02-final-heavy; rights on record and meta; no thought
keys; no training_ready; Diversity + Edge-Case injections from BOTH cycles
present and non-trivial; cycle 2 strictly additive.

Densification delta: +1 domain sub-variant (oxygen-enriched Claus), +1 tail
(night-shift forgery), +10 spikes (16->26), +2 ticks (5->7), +1 contrast
train with own race, +2 delayed side-effects, +1 triple-edge scar with
pair-rollback-fails, +1 HITL ratify, +1 surprise (catalyst sulfide is
the SO2-slip mechanism).

Publishable JSONL line (the only JSONL line; also at batch-r40.jsonl):

```json
__FINAL_JSONL__
```

Validation receipt (final): checks passed / fixed as reported by
build_r40.py self-validate (check_jsonl, raster_status, verify_record_execution,
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
    (OUT / "swarm-transcript-r40.md").write_text(text)
    return text


def main():
    rec, aux = build_record()
    errs = local_checks(rec, aux)

    OUT.mkdir(parents=True, exist_ok=True)
    line = json.dumps(rec, ensure_ascii=False, separators=(",", ":"))
    (OUT / "batch-r40.jsonl").write_text(line + "\n")

    from check_records import FactoryStaging, check_jsonl
    from curate_bridge import raster_status
    from verify_execution import verify_record_execution

    e, w, kinds, n = check_jsonl(
        OUT / "batch-r40.jsonl",
        "batch-r40.jsonl",
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
            str(OUT / "batch-r40.jsonl"),
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
        [sys.executable, "/tmp/maos_heading_check.py", str(OUT / "swarm-transcript-r40.md")],
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
            "maos-r40-001|BRIMVAULT",
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
    print("OK maos-r40-001 staged under", OUT)
    print("bytes jsonl", (OUT / "batch-r40.jsonl").stat().st_size)
    print("bytes notes", (OUT / "NOTES-r40.md").stat().st_size)
    print("bytes transcript", (OUT / "swarm-transcript-r40.md").stat().st_size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
