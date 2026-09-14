#!/usr/bin/env python3
"""Build MAOS round-41 JSONL for the 2026-09-02-final-heavy sf-window.

Create-only under:
  /tmp/sf-window/outputs/raw/2026-09-02-final-heavy/multi-agent-ouroboros-swarm
Never writes the repo outputs/raw/ tree. Never overwrites existing files.
"""
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

GEN_AT = "2026-09-03T18:42:00Z"
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
OUT = Path(
    "/tmp/sf-window/outputs/raw/2026-09-02-final-heavy/multi-agent-ouroboros-swarm"
)
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
    "BRIMVAULT",
    "Pyritefen",
    "BOGIRON",
    "Mireholt",
    "NITROSTAITH",
    "Chalkfen",
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
    "OLEUMWEIR",
    "Brindlefell",
    "SKARVOLT",
    "Emberbarrow",
    "GAUZEFELL",
    "Ammoxwick",
    "OSMOLITH",
    "Spumeholt",
    "PUSHERFELL",
    "Sootmere",
    "CREELWOLD",
    "Rovingholt",
    "LIXIVQUERN",
    "Bauxfen",
    "GIBBSQUERN",
    "Laterifen",
    "GOBSPALL",
    "GOBWOLD",
    "Culletfen",
    "Culletwick",
    "NITREVAULT",
    "Glaucove",
    "Cytiva",
    "Sartorius",
    "Thermo Fisher",
    "Millipore",
    "Repligen",
    "Xcellerex",
    "HyClone",
    "Applikon",
    "Eppendorf",
    "Broadley",
    "KrosFlo",
    "Danaher",
)
R14_OPENING = (
    "Helixmere Biologics Building C lyophilizer LYO-4 is mid-primary on 8400 "
    "vials of a monoclonal antibody"
)
NOVEL_LINE = "Novel coverage: 52%"
PLANT = "HOLLOWMERE"
GEO = "Marrowfen"
CELL = "PX-5"
DOMAIN = "bioreactor-perfusion"
RECORD_ID = "maos-r41-001"
ROUND = 41
DELAY_S = 0.84
TAU_E_S = 0.90
C1_SPIKE_CUTOFF_MS = 26.210
NEURONS = 164
MEAN_RATE = 8.0
WINDOW_MS = 40
WINDOW_S = 0.040
RASTER_SPIKES = round(NEURONS * MEAN_RATE * WINDOW_S)  # 52
ENERGY_PJ = RASTER_SPIKES * 23  # 1196
ENERGY_UJ = RASTER_SPIKES * 23e-6  # 0.001196


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
    tokens = (PLANT, GEO, CELL)
    for p in sorted(Path("/tmp").glob("maos-r*/batch-r*.jsonl")):
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
    return hits


def build_record():
    ticks, heads = cents_ticks(
        [4280, 6512, 7230, 8_400_000, 672_000_000, 7_560_000_000, 15_120_000_000],
        [
            (1, -2, -1, 2, 1),
            (2, -5, -1, 3, 2),
            (2, -6, -2, 3, 2),
            (1, -6, -2, 2, 1),
            (1, -5, -2, 2, 1),
            (1, -5, -1, 1, 1),
            (0, -5, -2, 1, 1),
        ],
    )
    assert abs(heads["total"] - (-0.14)) < 1e-9, heads

    trace = math.exp(-DELAY_S / TAU_E_S)
    eta1 = 0.24 / trace
    eta2 = 0.21 / trace
    eta3 = 0.19 / trace
    dw1 = eta1 * 1.0 * trace
    dw2 = eta2 * 1.0 * trace
    dw3 = eta3 * 1.0 * trace
    w1 = 0.50 - dw1
    w2 = 0.44 - dw2
    w3 = 0.40 - dw3
    assert abs(w1 - 0.26) < 5e-4, w1
    assert abs(w2 - 0.23) < 5e-4, w2
    assert abs(w3 - 0.21) < 5e-4, w3

    spike_events = [
        {"channel": "do.pct", "t_rel_ms": 0.280, "amplitude": 0.54},
        {"channel": "ph.broth", "t_rel_ms": 1.120, "amplitude": 0.61},
        {"channel": "vcd.cap", "t_rel_ms": 2.040, "amplitude": 0.52},
        {"channel": "harvest.mass", "t_rel_ms": 3.180, "amplitude": 0.73},
        {"channel": "do.pct", "t_rel_ms": 4.140, "amplitude": 0.50},
        {"channel": "harvest.mass", "t_rel_ms": 4.820, "amplitude": 0.76},
        {"channel": "ph.broth", "t_rel_ms": 5.360, "amplitude": 0.58},
        {"channel": "harvest.mass.high", "t_rel_ms": 6.512, "amplitude": 1.38},
        {"channel": "do.in_band", "t_rel_ms": 6.700, "amplitude": 1.12},
        {"channel": "do.pct", "t_rel_ms": 6.920, "amplitude": 0.64},
        {"channel": "ctrl.gate", "t_rel_ms": 7.230, "amplitude": 1.08},
        {"channel": "harvest.mass", "t_rel_ms": 8.860, "amplitude": 0.45},
        {"channel": "vcd.cap", "t_rel_ms": 10.740, "amplitude": 0.80},
        {"channel": "ph.broth", "t_rel_ms": 13.020, "amplitude": 0.44},
        {"channel": "do.pct", "t_rel_ms": 18.480, "amplitude": 0.42},
        {"channel": "ctrl.gate", "t_rel_ms": 26.210, "amplitude": 0.84},
        {"channel": "permeate.step.probe", "t_rel_ms": 8400.0, "amplitude": 0.95},
        {"channel": "harvest.mass", "t_rel_ms": 8488.4, "amplitude": 0.40},
        {"channel": "do.in_band", "t_rel_ms": 8572.2, "amplitude": 0.34},
        {"channel": "human.ratify", "t_rel_ms": 672000.0, "amplitude": 0.78},
        {"channel": "bag.isolate", "t_rel_ms": 672900.0, "amplitude": 0.70},
        {"channel": "harvest.bleed", "t_rel_ms": 673700.0, "amplitude": 0.86},
        {"channel": "do.pct", "t_rel_ms": 7560000.0, "amplitude": 0.31},
        {"channel": "harvest.mass", "t_rel_ms": 7560700.0, "amplitude": 0.28},
        {"channel": "ph.broth", "t_rel_ms": 7561480.0, "amplitude": 0.25},
        {"channel": "bioburden", "t_rel_ms": 15120000.0, "amplitude": 0.92},
    ]

    contrast_spikes = [
        {"channel": "perf.demand", "t_rel_ms": 0.000, "amplitude": 0.82},
        {"channel": "harvest.clear", "t_rel_ms": 0.188, "amplitude": 0.75},
        {"channel": "do.pct", "t_rel_ms": 0.440, "amplitude": 0.28},
        {"channel": "ph.broth", "t_rel_ms": 1.510, "amplitude": 0.38},
        {"channel": "harvest.mass", "t_rel_ms": 4.920, "amplitude": 0.50},
        {"channel": "ctrl.gate", "t_rel_ms": 7.080, "amplitude": 0.88},
        {"channel": "permeate.step.probe", "t_rel_ms": 3100.0, "amplitude": 0.32},
        {"channel": "bioburden", "t_rel_ms": 15120000.0, "amplitude": 0.08},
    ]

    excerpt = [
        {"t_us": 280, "neuron_id": 12},
        {"t_us": 1120, "neuron_id": 88},
        {"t_us": 2040, "neuron_id": 24},
        {"t_us": 3180, "neuron_id": 51},
        {"t_us": 4140, "neuron_id": 15},
        {"t_us": 4820, "neuron_id": 59},
        {"t_us": 5360, "neuron_id": 97},
        {"t_us": 6512, "neuron_id": 46},
        {"t_us": 6700, "neuron_id": 21},
        {"t_us": 6920, "neuron_id": 34},
        {"t_us": 7230, "neuron_id": 131},
        {"t_us": 8860, "neuron_id": 63},
        {"t_us": 10740, "neuron_id": 28},
        {"t_us": 13020, "neuron_id": 112},
        {"t_us": 18480, "neuron_id": 18},
        {"t_us": 26210, "neuron_id": 140},
    ]

    rec = {
        "id": RECORD_ID,
        "title": "HOLLOWMERE PX-5: harvest-mass residual 6.8 pct beats do.in_band by 188 us; correct MODIFY still dumps the harvest tank after a pre-t0 bag pinhole",
        "rights": dict(RIGHTS),
        "state": {
            "sim_or_real": "designed",
            "domain": DOMAIN,
            "scenario_name": "HOLLOWMERE / Marrowfen Perfusion PX-5",
            "timestamp_local": "2026-05-17T02:48:00-05:00",
            "t0_us": 1780004100000041,
            "gate_latency_us": 718,
            "race_window_us": 500,
            "race_window_rel_ms": [6.512, 7.012],
            "description": "Marrowfen Perfusion suite PX-5 is 38 h into a 14-day CHO campaign at 1.00 RV/d. Dissolved-oxygen, broth pH, and capacitance biomass each sit inside their commissioned bands, and the night supervisor drafts a perfusion raise. A 0.9 mm harvest-bag weld pinhole sits downstream of the hollow-fiber cell-retention loop, so the three broth-side loops stay locally true while harvest mass residual r_m is 6.8 pct (hold if > 1.6). DO is 40.0 pct-sat inside 35-50. pH is 7.05 inside 6.90-7.20. VCD is 42.0e6 cells/mL inside 38-48. The conjunction is not a bag-integrity certificate: harvest Coriolis is policy-treated as a noisy-meter tag unless bulk DO also trips (2019 harvest-meter nuisance). Harvest-mass-first latches PERFUSION-HOLD plus a permeate-step probe; broth-first would have authorized PERFUSION-RAISE 1.00 to 1.35 RV/d into a leaking harvest bag.",
            "goal": "Hold perfusion at 1.00 RV/d without a productivity raise while r_m > 1.6 pct AND permeate-step |dP_harvest| <= 1.2 kPa AND PX-5 remains unisolated; keep harvest-tank bioburden at 0 CFU/mL above the 10 CFU spec.",
            "race": {
                "contenders": [
                    "harvest.mass.high 6.8 pct (Coriolis vs media-in integrator)",
                    "do.in_band 40.0 pct-sat (bulk-broth optical DO)",
                ],
                "semantics": "mass-first latches PERFUSION-HOLD + PERMEATE-STEP-PROBE + harvest-bag isolate. Broth-first latches PERFUSION-RAISE (1.00 to 1.35 RV/d, no isolate).",
                "window_derivation": "500 us = one 360 us Coriolis ADC slot plus 140 us optical-DO publish.",
                "order_evidence_note": "Margin 188 us vs combined jitter 58 us (harvest 32 + DO 26): 3.24x. The 188 us gap sits inside min(500, 500) us, so a sub-flip-bound perturbation reverses triage order. The gate rides the order-invariant floors r_m > 1.6 pct and permeate-step |dP_harvest| <= 1.2 kPa, not the alarm order.",
            },
            "topology": {
                "site": "Marrowfen Perfusion, invented marsh-delta biomanufacturing quay Marrowfen, suite PX-5: 2000 L single-use CHO perfusion, hollow-fiber cell-retention, Grade-C harvest-suite LOTO",
                "agents": "DO bulk-broth optical dissolved oxygen (vendor Oxywick): 20 Hz 12-bit pct-sat. PH broth pH (vendor Acidfen): 50 Hz on the recirculation loop. VCD capacitance biomass (vendor Capmere): 20 ms bus average on the vessel. MASS harvest Coriolis (vendor Weighfen) is commissioned as a noisy-meter tag, not as a bag-integrity tag. Heterogeneous stacks, no shared intent schema, one 20 ms perfusion-bus epoch",
                "coupling": "All three playbook confirms live on the WRONG volume. DO is correct that bulk broth is 40.0 pct-sat (the pinhole is downstream of the hollow-fiber). PH is correct that recirculation pH is 7.05. VCD is correct that capacitance biomass is 42.0e6 cells/mL (cells stay in the vessel). Playbook PB-PX-5 treats the conjunction as permission to raise perfusion. No agent is faulty; the broth-mean is looking at the retained culture, not at the leaking harvest bag.",
            },
            "sensors": [
                "bulk-broth optical DO 12-bit, 20 Hz, 26 us jitter, 40.0 pct-sat (dead-band 35-50)",
                "broth pH, 50 Hz, 18 us jitter, 7.05 (band 6.90-7.20)",
                "capacitance biomass, 50 Hz, 22 us jitter, 42.0e6 cells/mL (setpoint band 38-48)",
                "harvest Coriolis, 20 Hz, 32 us jitter, r_m 6.8 pct missing vs media-in integrator (healthy < 0.9; policy floor 1.6 pct is not armed unless bulk DO also trips)",
                "in-bag dye leak test is NOT commissioned at t0 (installed after this incident)",
            ],
            "constraints": {
                "perfusion_rv_d": 1.00,
                "perfusion_hold_ceiling_rv_d": 1.00,
                "proposed_perfusion_rv_d": 1.35,
                "do_pctsat": 40.0,
                "do_deadband_pctsat": [35.0, 50.0],
                "ph": 7.05,
                "ph_band": [6.90, 7.20],
                "vcd_e6_per_ml": 42.0,
                "vcd_band_e6_per_ml": [38.0, 48.0],
                "r_m_pct": 6.8,
                "r_m_hold_pct": 1.6,
                "permeate_step_dP_kPa": 0.5,
                "permeate_step_hold_kPa": 1.2,
                "working_volume_L": 2000.0,
                "pinhole_mm": 0.9,
                "pre_t0_bleed_min": 22.0,
            },
            "fault_context": {
                "failure_class": "HARVEST-BAG PINHOLE CERTIFICATE OF A BROTH-MEAN LOOP: three individually-correct heterogeneous agents each read a locally-true broth loop; a 0.9 mm harvest-bag weld pinhole partitions broth-true culture from harvest-true mass, so the playbook's DO/pH/VCD conjunction is not a bag-integrity certificate",
                "igniter": "harvest-bag weld pinhole after 22 min of unmonitored bleed; suite visual PASSES (the bag looks seated; the pinhole is on the far weld of the drain elbow)",
                "naive_failure": "PB-PX-5 PERFUSION-RAISE on three healthy loops: 1.00 to 1.35 RV/d into a leaking harvest bag, $3.6M plus an 18-hour suite dump",
            },
            "poisoned_context": {
                "naive_alarm": "Playbook PB-PX-5 (after the 2019 'noisy harvest-meter nuisance') auto-drafts PERFUSION-RAISE whenever DO is inside 35-50 pct-sat AND pH inside 6.90-7.20 AND VCD inside 38-48 e6 cells/mL, ignoring the harvest Coriolis tap unless bulk DO also trips",
                "why_poisoned": "The three confirms are locally true and jointly insufficient. The harvest Coriolis tap is a commissioned sensor that policy treats as noisy-meter-only. Independence of 'broth in band, therefore the harvest bag is intact' is the hidden assumption, and it is false across a pinhole-plus-downstream-bleed path.",
            },
            "constraint": "Do not raise perfusion above 1.00 RV/d while inferred harvest-mass residual r_m > 1.6 pct AND a permeate-step |dP_harvest| <= 1.2 kPa. Discriminate harvest-bag pinhole vs true high-productivity load with a reversible permeate-step probe before any perfusion raise.",
        },
        "proposed_action": {
            "actor": "perfusion supervisory optimizer PSSO (auto-playbook PB-PX-5 draft), submitted to gate TG-PX-5",
            "name": "perfusion_raise",
            "action": "PERFUSION-RAISE: 1.00 -> 1.35 RV/d, no permeate-step probe, no harvest-bag isolate",
            "summary": "Treat three in-spec broth loops as a healthy bag and raise Sunday-night perfusion to clear a harvest-slot window.",
            "parameters": {
                "perfusion_rv_d": 1.35,
                "permeate_step_probe": False,
                "bag_isolate": False,
                "human_ratify": False,
            },
            "steps": [
                "assert DO 40.0 pct-sat inside 35-50",
                "assert pH 7.05 inside 6.90-7.20",
                "assert VCD 42.0e6 cells/mL inside 38-48",
                "ramp perfusion 1.00 to 1.35 RV/d over 6 min",
                "hold hollow-fiber TMP; do not read harvest Coriolis as a bag-integrity tag",
            ],
            "evidence": [
                {
                    "observable": "inferred harvest-mass residual r_m",
                    "value": 6.8,
                    "unit": "pct",
                    "source": "MASS harvest Coriolis vs media-in integrator",
                    "note": "healthy < 0.9 pct; policy floor 1.6 pct is not armed unless bulk DO also trips",
                },
                {
                    "observable": "dissolved oxygen",
                    "value": 40.0,
                    "unit": "pct-sat",
                    "source": "DO bulk-broth optical",
                    "note": "dead-band 35-50; lives on retained culture, not harvest bag",
                },
                {
                    "observable": "broth pH",
                    "value": 7.05,
                    "unit": "1",
                    "source": "PH recirculation probe",
                    "note": "band 6.90-7.20; broth-true, bag-false",
                },
                {
                    "observable": "viable cell density",
                    "value": 42.0,
                    "unit": "e6 cells/mL",
                    "source": "VCD capacitance",
                    "note": "band 38-48; cells stay in the vessel across the pinhole",
                },
                {
                    "observable": "permeate-step dP_harvest",
                    "value": 0.5,
                    "unit": "kPa",
                    "source": "harvest dP during -8 pct permeate pulse",
                    "note": "hold if |dP| <= 1.2 kPa; pinhole bag does not see the step as a closed volume",
                },
                {
                    "observable": "race margin",
                    "value": 188,
                    "unit": "us",
                    "source": "harvest.mass.high 6.512 ms vs do.in_band 6.700 ms",
                    "note": "combined jitter 58 us, 3.24x; inside 500 us flip bound",
                },
            ],
            "basis": "PB-PX-5 fires on three locally-true confirms. The draft does not read r_m 6.8 pct as a harvest residual and does not treat permeate-step 0.5 kPa as a pinhole discriminant.",
            "expected_cost_bound": "If the draft executes: harvest-tank contamination at 1.35 RV/d, $3.6M plus 18-hour suite dump. If MODIFIED: probe plus isolate, with residual risk from bleed already seeded in the 22 min pre-t0 pinhole.",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "correctness": "correct",
            "decided_by": "TG-PX-5 thalamic release gate",
            "decision_t_rel_ms": 7.230,
            "rationale": "MODIFY the draft: strip the perfusion raise, hold 1.00 RV/d, run an 8.4 s permeate-step probe (-8 pct harvest takeoff), and isolate the harvest bag only if the probe stays pinhole-true. Numeric floor: do not raise perfusion above 1.00 RV/d while inferred harvest-mass residual r_m > 1.6 pct AND permeate-step |dP_harvest| <= 1.2 kPa. Observed r_m 6.8 pct and dP 0.5 kPa both violate the release predicate, so a raise is forbidden even though all three playbook confirms are numerically true. The three confirms are not a bag-integrity certificate: they live on retained broth past a downstream pinhole, and the playbook's conjunction of broth-true loops is not a harvest-true certificate. Probe discriminant: after an 8.4 s -8 pct permeate step, a pinhole bag keeps |dP_harvest| <= 1.2 kPa (0.5 observed); an intact bag drops >= 6.5 kPa. Order-code discipline: harvest-mass beat DO-in-band by 188 us inside the 500 us flip bound, so triage order is flip-fragile; the hold rides the order-invariant floors, not the winner tag. Human ratification: harvest-bag isolate is Grade-C suite LOTO work with fitted 11.2 min dead-man; the gate may hold and probe autonomously but may not break the harvest interlock without the operator confirm.",
            "constraint_checked": {
                "perfusion_rv_d": {
                    "observed": 1.00,
                    "ceiling": 1.00,
                    "proposed_target": 1.35,
                },
                "r_m_pct": {"observed": 6.8, "hold_if_above": 1.6},
                "do_pctsat": {"observed": 40.0, "band": [35.0, 50.0]},
                "permeate_step_dP_kPa": {"observed": 0.5, "hold_if_at_most": 1.2},
            },
        },
        "executed_action": {
            "name": "perfusion_hold_permeate_step_isolate",
            "action": "PERFUSION-HOLD + PERMEATE-STEP-PROBE + HARVEST-BAG-ISOLATE (gate-mandated modification)",
            "executed_as_proposed": False,
            "parameters": {
                "perfusion_rv_d": 1.00,
                "permeate_step_probe": True,
                "bag_isolate": True,
                "human_ratify": True,
            },
            "gate_effect": "MODIFY: perfusion raise stripped. Hold 1.00 RV/d. 8.4 s permeate-step -8 pct. Probe stays pinhole-true (dP 0.5 <= 1.2) so the harvest interlock is broken after 11.2 min human ratify and the bag is isolated. Setpoint resumes after an intact-bag verify.",
            "deviations": "PB-PX-5 perfusion raise stripped entirely. Permeate is stepped only for the 8.4 s probe then returned. Harvest interlock wait added (11.2 min fitted gown+ratify). Bag survey added during the isolate (not in the draft).",
            "execution_log": [
                {
                    "t_rel_ms": 7.230,
                    "entry": "TG-PX-5 MODIFY latched 718 us after mass win; perfusion raise stripped; hold+probe authorized",
                },
                {
                    "t_rel_ms": 8400.0,
                    "entry": "permeate-step probe: harvest takeoff -8 pct for 8.4 s; dP 0.5 kPa (pinhole band |dP| <= 1.2); DO 40.0 -> 40.1 pct-sat",
                },
                {
                    "t_rel_ms": 672000.0,
                    "entry": "operator ratifies harvest interlock break after 11.2 min Grade-C gown+LOTO (fitted walk+interlock)",
                },
                {
                    "t_rel_ms": 672900.0,
                    "entry": "harvest bag isolated; permeate slaved to a spare bag; remaining culture recovered toward 1.00 RV/d over 2.1 h",
                },
                {
                    "t_rel_ms": 673700.0,
                    "entry": "bag survey: 0.9 mm weld pinhole already on the drain elbow; 22 min pre-t0 bleed logged",
                },
                {
                    "t_rel_ms": 7560000.0,
                    "entry": "true intact bag on the spare: r_m 0.4 pct, DO 40.2 pct-sat, residual under 1.6 pct; raise now legal on PX-5B only",
                },
                {
                    "t_rel_ms": 15120000.0,
                    "entry": "bioburden / harvest-tank dump from the pre-t0 bleed; harvest suite quarantined 18 h",
                },
            ],
        },
        "future_outcome": {
            "summary": "Correct MODIFY prevented the 1.00->1.35 RV/d raise into a leaking harvest bag and the immediate contamination path. The harvest tank still failed: 22 min of unmonitored pre-t0 bleed had already seeded unfiltered broth. Process-correct gate, bounded world loss, negative total.",
            "state_delta": {
                "perfusion": "held 1.00 RV/d through probe and isolate; later legal raise only on the sister vessel after 2.1 h spare-bag recovery",
                "bag": "harvest bag isolated; permeate slaved to spare; remaining culture recovered toward 1.00 RV/d",
                "pinhole": "0.9 mm weld pinhole logged and isolated; broth-mean no longer trusted as bag-true",
                "suite": "Sunday-night harvest suite quarantined; tank seeded; bioburden at +4.2 h; 18 h dump",
            },
            "timeline": [
                {
                    "t_rel_ms": -1320000.0,
                    "event": "t0-22 min: harvest-bag weld pinhole opens; r_m crosses 0.9 pct; bleed starts seeding the hold tank",
                },
                {
                    "t_rel_ms": -480000.0,
                    "event": "t0-8 min: r_m first crosses 1.6 pct; PB-PX-5 ignores it because bulk DO is 40.2 pct-sat",
                },
                {"t_rel_ms": 0.0, "event": "t0: harvest-mass vs DO-in-band race on the perfusion bus"},
                {
                    "t_rel_ms": 6.512,
                    "event": "harvest-mass residual at 6.8 pct wins by 188 us",
                },
                {"t_rel_ms": 6.700, "event": "DO-in-band flag (loser)"},
                {"t_rel_ms": 7.230, "event": "TG-PX-5 MODIFY"},
                {
                    "t_rel_ms": 8400.0,
                    "event": "permeate-step probe confirms harvest-bag pinhole (dP 0.5 kPa, pinhole band)",
                },
                {
                    "t_rel_ms": 672000.0,
                    "event": "human ratify 11.2 min; harvest bag isolated; pinhole logged",
                },
                {
                    "t_rel_ms": 7560000.0,
                    "event": "true intact spare bag after 2.1 h; raise legal only with r_m slave",
                },
                {
                    "t_rel_ms": 15120000.0,
                    "event": "bioburden from the pre-t0 bleed; suite quarantined",
                },
                {
                    "t_rel_ms": 345600000.0,
                    "event": "+4 d contrast: sister vessel PX-5B true high-productivity; same gate ACCEPTs the raise",
                },
                {
                    "t_rel_ms": 1814400000.0,
                    "event": "+21 d CR-P-4105: standing permeate-step probe + triple-edge depression mandate + harvest Coriolis armed without DO coincidence + broth-mean declared bag-vulnerable",
                },
            ],
            "observed_effects": [
                "raise avoided: perfusion never left 1.00 RV/d; 0 extra RV entered the leaking bag from the draft",
                "pinhole proven, not asserted: permeate-step |dP| 0.5 <= 1.2 kPa pinhole band vs intact-bag control 7.1 kPa",
                "broth slaved: DO/pH/VCD no longer a bag-true tag without r_m",
                "tank still dumped: CFU 1.4e3 vs 10 spec; 18 h outage, $2.14M (designed $)",
                "in-bag dye leak test was not a commissioned sensor at t0; the 22 min bleed was invisible to DO/PH/VCD",
            ],
            "surprises": [
                "Three locally-true loops are not a bag-integrity certificate: the harvest-true bleed was under a broth-mean culture. Conjunction of in-spec broth loops was the hidden assumption, and it is false across a pinhole-plus-downstream path.",
                "Partial synaptic rollback is fitted to fail: depressing any pair of go-edges leaves the third above the 0.30 fire threshold, so the perfusion raise still goes. Coordinated depression of all three edges is required.",
                "Delayed (4.2 h): correct hold did not undo 22 min of harvest-tank seeding. Bioburden still fired. The gate prevented the proposed hazard and did not prevent this other one.",
                "Intensified 80e6-cell sub-variant: an 8.4 s -8 pct permeate step on a 0.35x-area hollow-fiber overshoots a LIVE intact bag to 42 kPa TMP (rating 18). Intensified campaigns must use 22 s at -2.0 pct.",
            ],
            "delayed_side_effects": [
                {
                    "at": "+4.2 h",
                    "effect": "bioburden / harvest-tank dump from the pre-t0 bleed; 18 h suite outage booked at $2.14M. This is the primary episode's terminal world state, not a footnote.",
                },
                {
                    "at": "+4 d",
                    "effect": "Sister vessel PX-5B reaches a true high-productivity window (r_m 0.3 pct, DO 39.8 pct-sat, VCD 41.2e6, permeate-step 7.4 kPa). Same gate ACCEPTs the 1.00->1.35 RV/d raise the primary MODIFIED away.",
                },
                {
                    "at": "+21 d",
                    "effect": "CR-P-4105 ships: permeate-step probe is standing configuration; triple-edge coordinated depression is the plasticity rule; harvest Coriolis is armed without DO coincidence; broth-mean is labeled bag-vulnerable with a 1.6 pct residual alarm.",
                },
            ],
            "subvariant_constraint": {
                "name": "intensified 80e6-cell / 0.35x hollow-fiber area (cycle-2 physical-constraints sub-variant)",
                "mechanism": "filter area 0.35x the 42e6 production loop, TMP gain 2.6x, cavitation floor 18 kPa",
                "probe_refit": "8.4 s -8 pct permeate step on the intensified loop drives even a live intact bag to 42 kPa TMP (inside the 18 kPa fiber rating). Required probe is 22 s at -2.0 pct (live dP 6.8 kPa, pinhole dP 0.4). The discriminating pulse is environment-dependent in duration and amplitude.",
                "consequence": "production 42e6 probe numbers do not port to 80e6 intensified campaigns; standing configuration is per-density-class, not per-suite",
            },
            "embedded_contrast_decision": {
                "note": "SAME gate (TG-PX-5), OPPOSITE correct disposition, with its own 188 us race. Teaches the boundary: do not treat 'never raise' as the lesson. The discriminant is r_m + permeate-step + probe, not the three playbook broth confirms alone.",
                "when": "+4 d, sister vessel PX-5B, true high-productivity after a delayed media makeup catchup, 2000 L production density",
                "state": {
                    "sim_or_real": "designed",
                    "summary": "r_m 0.3 pct, DO 39.8 pct-sat, VCD 41.2e6, permeate-step 7.4 kPa. Demand flag vs harvest-clear race: demand at t+0.000, harvest-clear at t+0.188 ms.",
                    "race_window_us": 500,
                    "race_flip_narrative": "demand vs harvest-clear 188 us apart inside the 500 us flip bound. Reversing order reshuffles triage minutes; the ACCEPT rides r_m 0.3 < 1.6 pct and a 6.0 s permeate-step verify that drops dP 7.4 kPa (intact bag, no pinhole).",
                },
                "proposed_action": {
                    "action": "PERFUSION-RAISE 1.00 -> 1.35 RV/d",
                    "summary": "This time the playbook predicate is met AND r_m plus permeate-step agree the harvest bag is intact, not pinhole-bled.",
                },
                "safety_decision": {
                    "decision": "ACCEPT",
                    "rationale": "ACCEPT the raise: r_m 0.3 pct < 1.6 pct, permeate-step 7.4 kPa with a 6.0 s verify that drops dP 7.4. Numeric floor that blocked the primary is now clear. Scope: 1.35 RV/d production density, not an 80e6 intensified campaign.",
                },
                "executed_action": {
                    "action": "perfusion raise as proposed",
                    "executed_as_proposed": True,
                },
                "future_outcome": {
                    "observed_effects": [
                        "PX-5B harvest CFU 4 (inside 10 spec floor)",
                        "bag camera 0 pinhole, r_m 0.3 pct",
                    ],
                    "lesson_delta": "Three in-spec broth loops are legal release only with harvest Coriolis armed, permeate-step as a pinhole flag, and a probe that can drop dP. Same gate, opposite disposition.",
                },
                "reward_components": {
                    "_aggregation": AGG,
                    "task_progress": 0.14,
                    "safety": 0.12,
                    "efficiency": 0.07,
                    "coherence": 0.10,
                    "exploration": 0.05,
                    "total": 0.48,
                },
                "spike_events": contrast_spikes,
            },
            "governance_subgame": {
                "decision": "CR-P-4105: standing policy for multi-agent perfusion raises",
                "meta_gate": "priced options: (a) RETIRE playbook broth conjunction, harvest-mass-only: loses a fast cheap confirm, -0.18 RV/d mean on 2 vessels/yr; (b) KEEP + standing permeate-step probe + harvest Coriolis armed without DO coincidence + broth-mean labeled bag-vulnerable + triple-edge depression; (c) STATUS QUO: fitted pinhole-pass rate 0.36%/campaign x $3.6M dump plus the silent bleed load",
                "outcome": "approved SCOPED option (b) on the 2 2000 L perfusion vessels that share the DO/PH/VCD stack; 80e6 intensified campaigns get the 22 s / -2.0 pct probe table; Sunday-night CSV exports must carry 0.05 pct native harvest-mass resolution (the fraud tail's 0.5 pct quantization is 10 bins off plant truth)",
            },
            "hazard_avoided": "immediate harvest-tank contamination from a 1.00->1.35 RV/d raise into a leaking bag; $3.6M plus 18-hour suite dump and the shop-stop path that would have followed an uncontained raise",
            "incident": "bioburden on the Sunday-night harvest tank from the pre-t0 bleed; suite quarantined 18 h; $2.14M designed cost. Mechanism is 22 min pre-t0 pinhole, not the gate's hold.",
            "latency_ms": 0.718,
            "reward_inflection_t_us": 15120000000,
            "reward_inflection_note": "Safety and task dive at bioburden inspection (4.2 h) when the pre-t0 seeded tank fails 1.4e3 CFU. Gate tick at 7230 us is process-correct and is not the inflection.",
            "counterfactuals": {
                "execute_draft_as_proposed": "perfusion hits 1.35 RV/d at +6 min; immediate harvest-tank contamination; $3.6M plus 18 h; the pinhole story is never found because raise morphology destroys the race evidence",
                "hold_without_probe": "pinhole stays; r_m stays at 6.8 pct; operator eventually raises on the same three broth confirms 40 min later",
                "rollback_any_pair": "any two go-edges depressed below 0.30 leaves the third at 0.50 / 0.44 / 0.40; the perfusion raise still fires. Coordinated depression of all three is the cure",
            },
            "race_result": {
                "winner": "harvest.mass.high (6.512 ms, r_m 6.8 pct)",
                "loser": "do.in_band (6.700 ms, 40.0 pct-sat)",
                "margin_us": 188,
                "counterfactual_if_reversed": "DO-in-band-first by < 188 us inside the 500 us window would have headed the PB-PX-5 perfusion raise in the triage queue. The numeric floors still MODIFY. The flip costs seconds of playbook inertia, not the verdict — unless a weak supervisor rides the winner tag instead of r_m and permeate-step.",
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
            "notes": "Correct MODIFY, harvest tank still dumped. total -0.14 = 0.08 + -0.34 + -0.11 + 0.14 + 0.09. Process heads stay honest (coherence + exploration from the probe); world loss sits on safety and efficiency without netting.",
            "component_notes": "task_progress 0.08: perfusion held and spare bag recovered, but the Sunday-night harvest tank is one quality unit so the campaign is not a success. safety -0.34: CFU 1.4e3 from pre-t0 bleed, no 1.35 RV/d raise from the draft. efficiency -0.11: 2.1 h extra recovery + 11.2 min HITL + 18 h dump. coherence 0.14: three agents retained, broth-mean vs harvest-true diagnosed, triple-edge scar exhibited. exploration 0.09: permeate-step probe is a new reversible discriminant.",
        },
        "spike_events": spike_events,
        "raster": {
            "window_ms": WINDOW_MS,
            "window_s": WINDOW_S,
            "neurons": NEURONS,
            "mean_rate_hz": MEAN_RATE,
            "spikes": RASTER_SPIKES,
            "energy_pJ": ENERGY_PJ,
            "energy_uJ": ENERGY_UJ,
            "note": "Loihi-2 4-core 23 pJ/spike; populations DO 0-40, harvest-mass 41-81, pH/VCD 82-122, gate 123-163; excerpt is the 40 ms decision window (verdict at 7230 us)",
            "excerpt": excerpt,
            "routing": {
                "source": "broth_healthy_pop",
                "target": "perfusion_raise_pop",
                "table": [
                    {
                        "from": "do_in_band_pop",
                        "to": "perfusion_raise_pop",
                        "weight": round(w1, 2),
                        "weight_at_illusion": 0.50,
                        "weight_commissioned": 0.18,
                        "note": "scar edge 1: 0.18 commissioned -> 0.50 during the 22 min illusion -> 0.26 after coordinated ACh-gated depression",
                    },
                    {
                        "from": "ph_in_band_pop",
                        "to": "perfusion_raise_pop",
                        "weight": round(w2, 2),
                        "weight_at_illusion": 0.44,
                        "weight_commissioned": 0.15,
                        "note": "scar edge 2: depressing edges 1+3 leaves this at 0.44 > 0.30 fire threshold",
                    },
                    {
                        "from": "vcd_in_band_pop",
                        "to": "perfusion_raise_pop",
                        "weight": round(w3, 2),
                        "weight_at_illusion": 0.40,
                        "weight_commissioned": 0.13,
                        "note": "scar edge 3: depressing edges 1+2 leaves this at 0.40 > 0.30. Coordinated depression of all three is required",
                    },
                    {
                        "from": "harvest_mass_pop",
                        "to": "perfusion_hold_pop",
                        "weight": 0.68,
                        "note": "discriminating edge: harvest-true mass to hold. Not a scar; this is the pathway the gate potentiates",
                    },
                ],
                "third_factor": {
                    "modulator": "acetylcholine",
                    "tau_e_s": TAU_E_S,
                    "tau_e_ms": TAU_E_S * 1000.0,
                    "eligibility": (
                        "coordinated pre_post_stdp on ALL THREE broth-healthy-go edges; "
                        "ACh at mass-win tags do.in_band->raise, ph.in_band->raise, and vcd.in_band->raise; "
                        "negative credit at probe-fail (pinhole-plus-bleed confirmed, +0.84 s) depresses ALL THREE. "
                        f"trace e^{{-0.84/0.90}}={trace:.5f}; eta {eta1:.5f} / {eta2:.5f} / {eta3:.5f}; "
                        "dw -0.240 / -0.210 / -0.190; weights 0.50->0.26, 0.44->0.23, 0.40->0.21. "
                        "Rolling back any pair is fitted to fail (the remaining edge stays > 0.30)."
                    ),
                },
            },
        },
        "gate_snn": {
            "decision_window_ms": 26,
            "decision_window_s": 0.026,
            "decision": "MODIFY",
            "note": "modify_hold integrates harvest-mass residual + permeate-step floor against playbook drive; accept_raise and reject_abort stay sub-threshold; decision matches safety_decision.decision",
            "populations": [
                {
                    "name": "modify_hold",
                    "neurons": 96,
                    "threshold": 0.55,
                    "mean_rate_hz": 16.0,
                    "spikes": 40,
                },
                {
                    "name": "accept_raise",
                    "neurons": 64,
                    "threshold": 0.55,
                    "mean_rate_hz": 10.0,
                    "spikes": 17,
                },
                {
                    "name": "reject_abort",
                    "neurons": 48,
                    "threshold": 0.72,
                    "mean_rate_hz": 4.0,
                    "spikes": 5,
                },
            ],
        },
        "meta": {
            "round": ROUND,
            "factory": "multi-agent-ouroboros-swarm",
            "generator": "grok-4.6",
            "run_label": "2026-09-02-final-heavy",
            "domain": DOMAIN,
            "cycles": 2,
            "scenario": "PR -- HOLLOWMERE / Marrowfen Perfusion PX-5: harvest-bag pinhole certificate of a broth-mean loop; correct MODIFY to hold+permeate-step+isolate; harvest tank still fails on unmonitored pre-t0 bleed",
            "coordination_failure_class": "HARVEST-BAG PINHOLE CERTIFICATE OF A BROTH-MEAN LOOP: three individually-correct heterogeneous agents each read a locally-true broth loop; a harvest-bag weld pinhole partitions broth-true culture from harvest-true mass, so the playbook's DO/pH/VCD conjunction is not a bag-integrity certificate",
            "injections": {
                "cycle1_domain": (
                    "bioreactor-perfusion (justified novel subdomain of industrial-process / biologics): "
                    "first perfusion bioreactor plant in this factory; displaces warehouse-amr, aerial-swarm, "
                    "district-heating, event-camera-traffic-grid, pharmaceutical-lyophilization, water-treatment, "
                    "float-glass, underwater-rov, electrolytic-aluminum, czochralski-pull, slot-die coating, "
                    "pem-water-electrolysis, wind-turbine pitch, surgical-assist, optical-fiber-draw, "
                    "kraft-recovery-boiler, steel-continuous-caster, humanoid-locomotion, vacuum-induction melt, "
                    "steam-methane reformer, cement-rotary-kiln-clinker, autoclave-composite-cure, "
                    "geothermal-binary-orc, tire-curing-press, chlor-alkali-membrane-electrolysis, "
                    "delayed-coker-drum-switch, lng-mche-mixed-refrigerant, claus-sulfur-recovery, "
                    "ammonia-synthesis-converter, blast-furnace-burden-descent, hdpe-slurry-loop, "
                    "hydroelectric-kaplan-wicket, ethylene-steam-cracker-coil, fcc-riser-regenerator, "
                    "fcc-regenerator-cyclone-dipleg, sulfuric-contact-converter, eaf-foamy-slag-water-panel, "
                    "nitric-acid-ostwald-oxidation, seawater-ro-desalination, coke-oven-battery-heating, "
                    "and carbon-fiber-oxidation-oven. Domain constraint: perfusion ceiling while r_m > 1.6 pct "
                    "with bulk DO still inside the healthy band. Sensor delta: +optical DO, +broth pH, "
                    "+capacitance VCD, +harvest Coriolis, -any freeze-dryer / tin-bath / kiln / coke-drum / "
                    "oxidation-oven / Haber basket / Claus tail / RO skid"
                ),
                "cycle1_tail": (
                    "harvest-bag weld pinhole + broth-mean certificate (sensor-topology / wrong-volume class): "
                    "suite visual PASSES while the pinhole sits on the far weld of the drain elbow. Fitted base "
                    "rate 0.36%/campaign from a bleed-growth MC (designed visual threshold, fitted bag geometry). "
                    "Naive failure = FALSE PERMISSION (perfusion raise on three broth-side non-trips)."
                ),
                "cycle2_domain_subvariant": (
                    "intensified 80e6-cell / 0.35x hollow-fiber area (physical-constraints clause): 0.35x filter "
                    "area, 2.6x TMP gain; 8.4 s / -8 pct production pulse overshoots a LIVE intact bag to 42 kPa "
                    "TMP, so the probe must move to 22 s / -2.0 pct"
                ),
                "cycle2_tail": (
                    "night-shift forged harvest-mass CSV (human-intent deception, disjoint class): shift lead "
                    "posts a historian export showing r_m = 0.5 pct at t=1.4 h to clear a harvest-slot window. "
                    "Plant historian is 0.05 pct (10 bins vs the 0.5 pct screenshot). Rejected on quantization "
                    "fingerprint plus live r_m 6.8 pct and DO 40.0 pct-sat at the claimed bag-true. Base rate "
                    "~0.29% of Sunday-night campaigns, DESIGNED and flagged."
                ),
            },
            "densification_delta_cycle2": (
                "+1 physical-constraint sub-variant (intensified 80e6 probe refit), +1 tail (night-shift "
                "harvest-mass forgery), +10 primary spikes (16 -> 26) + an 8-event contrast train with its "
                "own 188 us race, +2 ticks (5 -> 7), +2 delayed side-effects (+4.2 h bioburden as PRIMARY "
                "terminal, +21 d CR-P-4105), +1 triple-edge scar with pair-rollback-fails arithmetic, +1 "
                "HITL 11.2 min ratification, + harvest-tank seeding as the honest negative-result mechanism"
            ),
            "gaps_targeted": [
                "NOTES-r53 leftover: bioreactor-perfusion was named unused so concurrent empty slots could take it; this window's r41 takes it rather than cloning ammonia-synthesis-converter (already staged under /tmp/maos-r41) or carbon-fiber-oxidation-oven (r53)",
                "NOTES-r14 item 4: LEARNING-ON-LEARNING DEPTH — three go-edges; rollback of any pair is fitted to fail; coordinated depression of all three exhibited with eligibility arithmetic",
                "NOTES-r04 gap 4 (partial): human ratification of the harvest-suite interlock, 11.2 min fitted, without switching sim_or_real to hil (plant remains designed)",
                "NOTES-r04 gap 5 / r14 residual: primary episode is a correctly-gated intervention that nonetheless FAILS (suite quarantined; total -0.14; raise avoided is booked separately from the delayed bioburden)",
            ],
            "race_flip_narrative": (
                "harvest.mass.high @ 6.512 ms vs do.in_band @ 6.700 ms (188 us) inside race_window_us 500. "
                "Gap < min(500, 500) us so a sub-flip-bound perturbation reverses which alarm heads the "
                "PB-PX-5 queue. The gate excludes the winner tag and rides r_m > 1.6 pct and permeate-step "
                "|dP_harvest| <= 1.2 kPa — order-invariant floors. Extends the flip-fragility series to "
                "BAG-INTEGRITY CERTIFICATE: when three broth-side channels agree, their race does not decide "
                "truth; a harvest-mass tap that policy treated as noisy-meter-only does."
            ),
            "tags": [
                "bioreactor-perfusion",
                "harvest-bag-pinhole",
                "broth-mean-certificate",
                "harvest-mass-discriminant",
                "permeate-step-probe",
                "triple-edge-scar",
                "pair-rollback-fails",
                "coordinated-depression",
                "correct-modify-tank-still-fails",
                "bioburden",
                "human-ratify-harvest-suite",
                "intensified-density-probe-refit",
                "night-shift-forgery",
                "same-gate-opposite-disposition-contrast",
                "industrial-process",
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
            "distillation_value": (
                "A harvest-bag pinhole certificate is three correct loops looking at broth-mean culture that "
                "is not the leaking bag. Distill (1) a harvest-mass tap that policy had treated as "
                "noisy-meter-only, (2) a reversible probe that drops dP only if the bag is intact, (3) "
                "coordinated depression of every broth-healthy-go edge because rolling back any pair leaves "
                "the third above threshold, and (4) a critic head that can book a process-correct gate "
                "against a later unmonitored world loss without netting them. Winner/loser flip: reversing "
                "the 188 us harvest.mass.high vs do.in_band order inside the 500 us race window reshuffles "
                "PB-PX-5 triage but the numeric floors still MODIFY."
            ),
            "rights": dict(RIGHTS),
            "batch_position": 1,
        },
    }
    return rec, dict(
        trace=trace, eta1=eta1, eta2=eta2, eta3=eta3, dw1=dw1, dw2=dw2, dw3=dw3, w1=w1, w2=w2, w3=w3
    )


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
    if abs(aux["w1"] - 0.26) > 5e-4 or abs(aux["w2"] - 0.23) > 5e-4 or abs(aux["w3"] - 0.21) > 5e-4:
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
