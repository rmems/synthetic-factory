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


def refuse_overwrite(path: Path):
    if path.exists():
        raise FileExistsError(f"refuse overwrite: {path}")


def write_notes(rec, aux, pipeline_receipt):
    gap, gap_ch = min_same_channel_gap(rec["spike_events"])
    notes = f"""# NOTES — Multi-Agent Ouroboros Swarm, run 2026-09-02-final-heavy, ROUND 41

Factory: multi-agent-ouroboros-swarm. One scenario (PR), strict loop:
Generator v1 -> cycle 1 (Critic, Diversity Enforcer, Edge-Case Hunter,
Neuromorphic Translator, Trajectory Builder -> v2) -> cycle 2 (all six -> v3
final). v3 is the single line of batch-r41.jsonl. Full labeled transcript:
swarm-transcript-r41.md. Quota Q=1. Record id maos-r41-001. Generator grok-4.6.
Rights: RM-793 research-only (SpaceXAI/xAI, SuperGrok Heavy consumer chat).
Repo outputs/raw/ was not written. This window's create-only path is
/tmp/sf-window/outputs/raw/2026-09-02-final-heavy/multi-agent-ouroboros-swarm/.

ORCHESTRATION NOTE: dispatched AS round 41 of the 2026-09-02-final-heavy
window. Writes are create-only under the sf-window factory dir. Prior
context read for gap targeting and de-collision: prompts/02-multi-agent-ouroboros-swarm.md,
prompts/_factory-contract.md, schemas/thalamic-trajectory.schema.json,
schemas/provenance.md, and staged r14–r54 plus NOTES-r52/r53 (two newest
complete NOTES). /tmp/maos-r41 already staged NITROSTAITH ammonia-synthesis-converter,
so this window does not clone that plant or domain. Explicitly avoided cloning
LYOSHIELD, CINDERWICK, TRIAD / Meridian, QUILLFORGE, NIGHTWELL, FERRICLEAVE,
CASSITER, OXBOWREEL / MURENA, REDHALL, SEEDLATCH / Quartzmere / Quartzridge,
STRIAFOIL / Kelpholt, PROTONIL / Ashspire, TORSIONKEY / Ridgeholt, ORRIS /
Holmwick, WHORLSPAR / Pikeshear, IONSPATE / Thornmere, SKULLGATE / Bloomholt,
CALXION / Aldersedge, MAGNORIL / Basaltspit, GORSEFLUE / Copseholt,
SODASHARD / Cairnmere, CLINKERFELL / Flintmere, LINTELPLY / Greystair,
KAOTHARN / Riftwold, TREADNOLL / Slatebeck, ANOLITH / Siltfen,
DRUMWROTH / Pitchfen, RIMEBRAID / Floeholt, PITCHSTAITH / Mossbank,
BRIMVAULT / Pyritefen, NITROSTAITH / Chalkfen, BOGIRON / Mireholt,
CHROMLOOP / Marlfell, ETHYNWOLD / Woadfen, RUNNELGATE / Ghyllmere,
SPARKHOLT / Scoriafen, DIPLEGAR / Gritfen, OLEUMWEIR / Brindlefell,
SKARVOLT / Emberbarrow, GAUZEFELL / Ammoxwick, OSMOLITH / Spumeholt,
PUSHERFELL / Sootmere, CREELWOLD / Rovingholt, LIXIVQUERN / Bauxfen,
GIBBSQUERN / Laterifen, VANTIS-CADENCE-AEGIS, THERMION, OKTAVE, STARLING,
VERDIGRIS. Plant is invented HOLLOWMERE / Marrowfen Perfusion PX-5.

## What this round produced

Scenario PR — "HOLLOWMERE / Marrowfen Perfusion PX-5": a 2000 L
single-use CHO perfusion train at 1.00 RV/d with hollow-fiber cell
retention. Three heterogeneous, individually-correct agents — DO
(bulk-broth optical), PH (recirculation pH), VCD (capacitance biomass)
— each report their local loop in-spec. The conjunction is not a
bag-integrity certificate. A 0.9 mm harvest-bag weld pinhole sits
downstream of the hollow-fiber. DO reads 40.0 pct-sat inside 35-50.
PH is 7.05 inside 6.90-7.20. VCD is 42.0e6 cells/mL inside 38-48.
Inferred harvest-mass residual r_m is 6.8 pct (healthy < 0.9; hold if
> 1.6) but is policy-treated as a noisy-meter tag unless bulk DO also
trips (2019 harvest-meter nuisance). The coordination-failure CLASS is
new to this factory: HARVEST-BAG PINHOLE CERTIFICATE OF A BROTH-MEAN
LOOP. Completes a different family than r01-r04 and staged r14-r54
(livelock / synchrony-storm / arms-race / ring-with-no-faulty-pair /
false-consensus-endpoint / pairwise-Hurwitz / thermal-contact masquerade
/ mass-balance ghost / conservation-blind ratio-lock / stacked-dead-bands
/ drum-blind tension snag / resistance-compensated starvation / multi-tau
meniscus tilt / window-mean stripe / polarization-lookup drying cell /
motor-side certificate / tendon-compliance nullspace / FFT-deadbanded
airline / wall-reflection frozen spout / slag-skull bridge / ghost-contact
nullspace / crucible-weep pyrometer / TMT-spatial-mean tube / kiln-inlet
false-air / vacuum-bag pinhole nullspace / NCG-blanket shell-pressure /
bladder-pinhole mold-TC / catholyte-back-migration membrane / wet-foam
gamma-radar / warm-end leak cold-end / incinerator-masked furnace-bypass
/ basket-bypass hotspot / tow-overlap exotherm). Here every agent is
correct, the broth-mean is looking at retained culture, and the
playbook's three broth confirms are not a harvest-true bag certificate.

The gate is a correct MODIFY (numeric floor: do not raise perfusion above
1.00 RV/d while r_m > 1.6 pct AND permeate-step |dP_harvest| <= 1.2 kPa).
TG-PX-5 strips PB-PX-5's perfusion raise, holds 1.00 RV/d, runs an 8.4 s
permeate-step probe -8 pct (pinhole keeps |dP| 0.5 <= 1.2; intact would
drop >= 6.5), and isolates the harvest bag after an 11.2 min suite
human ratify. Immediate contamination from the draft is avoided (0 extra
RV). The PRIMARY episode nonetheless FAILS: 22 min of unmonitored pre-t0
bleed had already seeded the harvest hold tank. Bioburden at +4.2 h;
18 h dump; $2.14M designed. Reward total -0.14 with process heads honest
and world loss un-netted.

Triple-edge scar (NOTES-r14 item 4): do.in_band -> perfusion_raise
(0.18 commissioned -> 0.50 at illusion -> 0.26 after ACh-gated
depression) AND ph.in_band -> perfusion_raise (0.15 -> 0.44 -> 0.23) AND
vcd.in_band -> perfusion_raise (0.13 -> 0.40 -> 0.21). Eligibility trace
e^{{-0.84/0.90}} = {aux['trace']:.5f}; eta {aux['eta1']:.5f} / {aux['eta2']:.5f} /
{aux['eta3']:.5f}; dw -0.240 / -0.210 / -0.190. Partial rollback of any pair
leaves the third at 0.50 / 0.44 / 0.40, all > 0.30 fire threshold —
fitted to fail. Coordinated depression of all three is the cure.

### Injections (all four present and disjoint)
- Cycle-1 domain: **bioreactor-perfusion** — justified novel subdomain
  of industrial-process / biologics, unused as state.domain across
  2026-08-17, 2026-08-30, and staged r14-r54. Named leftover in
  NOTES-r52/r53. Not warehouse-amr (r01), not aerial-swarm (r02), not
  district-heating (r03), not event-camera-traffic-grid (r04), not
  lyophilization (r14), not water-treatment (r18), not float-glass (r19),
  not underwater-rov (r20), not electrolytic-aluminum (r21), not
  czochralski-pull (r22), not slot-die coating (r23), not pem-electrolysis
  (r24), not wind-turbine pitch (r25), not surgical-assist (r26), not
  optical-fiber-draw (r27), not kraft-recovery (r28), not steel-caster
  (r29), not humanoid-locomotion (r30), not vacuum-induction melt (r31),
  not steam-methane reformer (r32), not cement-rotary-kiln (r33), not
  autoclave-composite-cure (r34), not geothermal-binary-orc (r35), not
  tire-curing-press (r36), not chlor-alkali membrane (r37), not
  delayed-coker-drum-switch (r38), not lng-mche (r39), not claus-sulfur
  (r40), not ammonia-synthesis-converter (staged /tmp/maos-r41), not
  carbon-fiber-oxidation-oven (r53). autonomous-driving and
  grid-inspection left unused.
- Cycle-1 tail: harvest-bag weld pinhole + broth-mean certificate.
  Suite visual PASSES (far-weld drain elbow). Fitted-style base rate
  0.36%/campaign (bleed-growth MC; visual threshold designed, flagged).
  Naive = FALSE PERMISSION.
- Cycle-2 domain sub-variant: intensified 80e6-cell / 0.35x hollow-fiber
  area, 2.6x TMP gain; 8.4 s / -8 pct production pulse overshoots a LIVE
  intact bag to 42 kPa TMP; probe must move to 22 s / -2.0 pct.
- Cycle-2 tail: night-shift forged harvest-mass CSV at 0.5 pct
  quantization vs plant 0.05 pct (10 bins) plus live r_m 6.8 pct and
  DO 40.0 pct-sat at the claimed bag-true. Human-intent class, disjoint
  from cycle 1's accidental pinhole. Base rate ~0.29% of Sunday-night
  campaigns, DESIGNED, flagged.

### Structural density moves
- Embedded SAME-GATE contrast (+4 d sister vessel) with its own 188 us
  race (demand vs harvest-clear) and ACCEPT of the raise the primary
  MODIFIED away.
- Learned-weight provenance on THREE edges with pair-rollback-fails.
- HITL suite ratify 11.2 min (gap 4 partial; sim_or_real stays designed).
- Governance CR-P-4105 prices retire-vs-probe-vs-status-quo and mandates
  native 0.05 pct CSV exports (the fraud fence).
- Flip-fragility extended to BAG-INTEGRITY CERTIFICATE: when three
  broth-side channels agree, their race does not decide truth; a
  harvest-mass tap that policy treated as noisy-meter-only does.

## Self-critique of this round's batch

### Strengths
- The headline class is mechanistically tight: three locally-true broth
  loops live on retained culture. Conjunction is not a harvest-true bag.
- Negative-result honesty: the gate does the right thing and the harvest
  tank still fails for a reason the commissioned broth sensors could not
  see. Total -0.14.
- Triple-edge scar is load-bearing: the record states a counterfactual
  where rolling back any pair fails, with the fire threshold 0.30
  exhibited on each remaining edge.
- Contrast ACCEPT on a true intact bag prevents "never raise" as the
  lesson.
- Distinct from r14 lyophilization (freeze-dryer, not perfusion), r34
  autoclave vacuum-bag pinhole (composite ply, not harvest bag), r36
  tire bladder-pinhole (mold steam, not CHO broth), and staged r41
  ammonia basket-bypass (Haber mean, not broth-mean).

### Weaknesses (honest)
- Probe error bands, the 0.36%/campaign pinhole rate, the $2.14M / $3.6M
  figures, the 11.2 min gown latency, and the night-shift 0.29% base
  rate are DESIGNED constants and are flagged. Closed-loop offsets
  (broth-mean hiding a downstream pinhole, 80e6 TMP gain) are derived
  from those inputs, not discovered by an unauthored process.
- Bleed-to-CFU model is a designed 22 min mapping; no full harvest-tank
  CFD shipped.
- Human-in-the-loop is ratification latency, not sim_or_real=hil. Gap 4
  remains open as a provenance cell.
- Cross-record arc is not discharged; +21 d CR-P-4105 is a hook, not a
  serial igniter into another round. autonomous-driving and
  grid-inspection remain unused.

### Realism of noise / latencies
Ladder: 188 us race / 188 us contrast race / 0.8 ms refractory floor
(tightest exhibited same-channel gap {gap:.3f} ms on {gap_ch}) / 500 us race
window / 718 us gate latency / 20 ms bus epoch / 40 ms raster / 8.4 s
probe / 11.2 min HITL / 6 min naive raise-ramp counterfactual / 22 min
pre-t0 bleed / 2.1 h spare-bag recovery / 4.2 h bioburden / +4 d
contrast / +21 d governance. Adaptation decay on do.pct
(0.54->0.50->0.64->0.42->0.31), harvest.mass (0.73->0.76->0.45->0.40->0.28),
ph.broth (0.61->0.58->0.44->0.25), vcd.cap (0.52->0.80).

### Value for SNN distillation
- HARVEST-BAG PINHOLE = THREE CORRECT LOOPS, WRONG VOLUME.
- HARVEST-TRUE MASS CHANNEL that policy treated as noisy-meter-only as
  the tie-break.
- REVERSIBLE PROBE that drops dP iff the bag is intact.
- TRIPLE-EDGE ELIGIBILITY: coordinated depression; pair rollback fails.
- CRITIC HEAD that can hold a process-correct MODIFY against a later
  unmonitored world loss without netting.

## Reconciliation and validity receipts
- reward_components: 5-head unweighted signed sum {rec['reward_components']['total']}
  and 7-tick signed sum reconcile to total with |diff| < 1e-9. Embedded
  contrast 5-head sum 0.48 reconciles independently.
- spike_events: primary {len(rec['spike_events'])} events, one key t_rel_ms,
  globally non-decreasing, min same-channel gap {gap:.3f} ms >= 0.8 ms, 3
  channels inside race_window_us 500 (harvest.mass.high 6.512, do.in_band 6.700,
  do.pct 6.920). Contrast 8 events, own race, min same-channel gap well
  above 0.8 ms.
- Sidecars: raster spikes 52 == round(164 x 8.0 x 0.040); energy 1196 pJ /
  0.001196 uJ at 23 pJ/spike; excerpt 16 events inside [0, 40000] us,
  neuron_id < 164, same-neuron gap unique-ids / >=1000 us; routing 4
  entries with three scar edges' before/after pair; third factor tau 0.90 s
  == 900 ms; gate_snn pools 40/17/5 == round(n x rate x 0.026) each,
  decision MODIFY == safety_decision.decision.
- Pipeline: {pipeline_receipt}

## Novel coverage
The coordination-failure CLASS (harvest-bag pinhole certificate of a
broth-mean loop), the domain (bioreactor-perfusion / industrial process),
the permeate-step probe discriminant, the triple-edge scar with
pair-rollback-fails, the primary negative-result (correct MODIFY,
harvest tank still fails on unmonitored bleed), the HITL suite ratify,
the intensified-density probe-duration refit, and the night-shift 10-bin
quantization fence are absent from prior committed ouroboros rounds and
from staged r14-r54 as state.domain. Repeated elements discounted:
same-gate contrast, governance-pricing scaffold, flip-fragility series
(extended to bag-integrity certificate, but the move rhymes), sequenced
recovery shape, third-factor rollback form, negative-result primary.
Adjacent pinhole rounds (r34 autoclave vacuum bag, r36 tire bladder)
share a hole-in-a-barrier motif but not CHO perfusion harvest-mass
physics. Weighing a new failure family + cure vocabulary + leftover
domain against those reused scaffolds:

{NOVEL_LINE}

## What ROUND 42 should add
1. FIT THE DESIGNED CONSTANTS: bleed arrival, probe dP bands,
   bleed-to-CFU mapping, night-shift claim process.
2. HIL PROVENANCE CELL: put the harvest-suite ratify on a
   hardware-in-loop Grade-C interlock with fitted latency as
   state.sim_or_real=hil.
3. CROSS-RECORD ARC: let CR-P-4105's r_m alarm be the igniter of the
   next round rather than a dangling +21 d leaf.
4. Domain candidates (de-collided): autonomous-driving; grid-inspection
   (if distinct from STARLING aerial-swarm); alkaline-water-electrolysis;
   hot-strip-mill. AVOID bioreactor-perfusion (now used),
   ammonia-synthesis-converter, carbon-fiber-oxidation-oven, coke-oven,
   seawater-RO, nitric-ostwald, eaf-foamy-slag, sulfuric-contact,
   fcc-riser, ethylene-cracker, hydroelectric-kaplan, claus-sulfur,
   lyophilization, and any LYOSHIELD / CINDERWICK / TRIAD / NITROSTAITH /
   CREELWOLD / HOLLOWMERE plant.
"""
    path = OUT / "NOTES-r41.md"
    refuse_overwrite(path)
    path.write_text(notes)
    return notes


def write_transcript(rec, line):
    c1_spikes = [e for e in rec["spike_events"] if e["t_rel_ms"] <= C1_SPIKE_CUTOFF_MS]
    text = f"""# Multi-Agent Ouroboros Swarm — Round 41 transcript

Factory: multi-agent-ouroboros-swarm
Run: 2026-09-02-final-heavy
Generator: grok-4.6
Record id: maos-r41-001
Quota Q: 1
Rights: RM-793 research-only (SpaceXAI/xAI SuperGrok Heavy consumer chat)
Plant: invented HOLLOWMERE / Marrowfen Perfusion PX-5 (not TRIAD / Meridian / VANTIS-CADENCE-AEGIS / LYOSHIELD / CINDERWICK / NITROSTAITH / CREELWOLD)

Two densifying cycles. Verbatim headings in order. Trajectory Builder cycle 2
emits the only JSONL line (also written to batch-r41.jsonl).

---

# CYCLE 1 — Foundation + injections

## Generator

Design intent: a 2000 L single-use CHO perfusion train where three correct
agents each read a broth-side loop because a harvest-bag weld pinhole
partitions harvest-true mass from broth-true culture. The naive
playbook raises perfusion into a leaking bag. The gate must MODIFY on a
numeric perfusion ceiling, not by killing an agent.
sim_or_real=designed. Reward heads are
task_progress/safety/efficiency/coherence/exploration.

Cycle-1 base arc (pre-critic): state at Marrowfen PX-5, 1.00 RV/d, DO
40.0 pct-sat, pH 7.05, VCD 42.0e6, proposed PERFUSION-RAISE 1.35 RV/d,
safety MODIFY to PERFUSION-HOLD, executed hold without the permeate-step
numbers fully specified, outcome "pinhole found, tank saved"
(this last claim is the defect the later cycles will refuse to keep).
Sixteen spikes, five ticks, raster/gate_snn present but the scar is a
single edge.

Cycle-1 scaffold (not the publishable line): id maos-r41-001, domain
still the generic industrial-process bucket, proposed perfusion_raise
1.35 RV/d, safety MODIFY with a non-numeric rationale, executed hold,
future_outcome claims the tank is saved, reward total 0.40 without
heads or ticks. Defects below are intentional for the critic to catch.

## Critic

Numbered defects on the cycle-1 Generator scaffold:

1. **blocking — reward arithmetic / false success.** reward_components.total
   0.40 is asserted without the five heads, without ticks, and against an
   outcome that claims "tank saved". If the pre-t0 bleed later trips
   bioburden, booking +0.40 is a lie. Fix: declare _aggregation, emit
   3-8 ticks that sum to task_progress+safety+efficiency+coherence+exploration,
   and do not call a quarantined suite a save.
2. **blocking — weak safety rationale.** safety_decision.rationale has no
   numeric floor. Contract requires a concrete constraint. Fix: quote
   perfusion <= 1.00 RV/d while r_m > 1.6 pct AND permeate-step |dP_harvest|
   <= 1.2 kPa.
3. **major — domain is a bucket, not a plant.** state.domain =
   industrial-process collides with generic MES vocabulary and teaches
   nothing. bioreactor-perfusion (harvest-mass vs broth DO, permeate-step
   as a pinhole flag) is absent from prior ouroboros state.domain values
   and must be named. NOTES-r53 left it unused.
4. **major — race under-specified.** One harvest-mass channel cannot be a
   race. Need >=2 channels inside race_window_us with globally sorted
   t_rel_ms and same-channel refractory >= 0.8 ms.
5. **minor — single-edge scar.** Raster routing with one potentiated weight
   repeats r04's one-edge rollback and is thinner than r14's two-edge.
   NOTES-r14 item 4 asked for three edges where pair rollback fails.

Critic does not rewrite the trajectory.

## Diversity Enforcer

Injected novel domain (exactly 1 this cycle): **bioreactor-perfusion**
(justified novel subdomain of industrial-process / biologics; explicit tag
`bioreactor-perfusion`).

Displaced: the Generator's generic industrial-process bucket, and any
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
ammonia-synthesis-converter, or carbon-fiber-oxidation-oven.
autonomous-driving is left unused.

Domain-specific constraint: perfusion must remain <= 1.00 RV/d while
r_m > 1.6 pct even if bulk DO is inside the healthy band; permeate-step
is a pinhole flag the optical DO cannot substitute for.

Sensor delta: +optical DO, +broth pH, +capacitance VCD, +harvest Coriolis;
-any mobile robot, -event-camera gantries, -DVS, -Pirani/CM, -RGA quadrupole,
-DVL, -pitch encoder, -tendon LVDT, -insole GRF, -kiln zirconia, -smelt IR,
-cell-outlet pH, -coke-drum gamma, -MCHE cold-end, -fiber IR, -bed-max TC.

state.domain and meta.domain both become bioreactor-perfusion.
Opening of state.description must Jaccard < 0.4 against prior plants
(Marrowfen Sunday-night harvest-bag pinhole, not a lyophilizer, not a
corridor, not a tin bath, not a ROV pad, not a potline, not a PEM stack,
not an OR, not a gait lab, not a kiln, not a kraft boiler, not a
membrane row, not a coke drum, not an LNG MCHE, not a Haber basket, not
an oxidation oven).

## Edge-Case Hunter

Injected adversarial tail (exactly 1 this cycle): **harvest-bag weld
pinhole + broth-mean certificate**.

- Trigger: 0.9 mm harvest-bag weld pinhole plus 22 min bleed, r_m 6.8 pct,
  bulk DO 40.0 pct-sat.
- Base rate: <1% — 0.36%/campaign from a bleed-growth MC (suite visual
  threshold is designed; bag geometry fitted-style). Visual PASSES
  because the pinhole sits on the far weld of the drain elbow.
- Naive failure: FALSE PERMISSION. PB-PX-5 sees three in-spec broth
  loops, raises 1.00->1.35 RV/d, contaminates the hold tank, $3.6M.
- Trajectory edit: put the pinhole in state.fault_context, make each
  agent's confirm a different broth-side slice of the same bag-false
  state (do-in-band, ph-in-band, vcd-in-band). Harvest-mass is readable
  but policy-treated as noisy-meter-only.

Distinct from r34 autoclave vacuum-bag pinhole (composite ply vs harvest
bag), from r36 tire bladder-pinhole (mold steam vs CHO broth), and from
staged r41 ammonia basket-bypass (Haber mean vs broth-mean).

## Neuromorphic Translator

Cycle-1 temporal densification (16 spikes, 5 ticks, 40 ms raster):

channel / t_rel_ms / amplitude
do.pct 0.280 0.54
ph.broth 1.120 0.61
vcd.cap 2.040 0.52
harvest.mass 3.180 0.73
do.pct 4.140 0.50
harvest.mass 4.820 0.76
ph.broth 5.360 0.58
harvest.mass.high 6.512 1.38
do.in_band 6.700 1.12
do.pct 6.920 0.64
ctrl.gate 7.230 1.08
harvest.mass 8.860 0.45
vcd.cap 10.740 0.80
ph.broth 13.020 0.44
do.pct 18.480 0.42
ctrl.gate 26.210 0.84

Race: harvest-mass 6.512 vs DO-in-band 6.700 (188 us) inside 500 us;
do.pct 6.920 is the third channel in-window. Winner/loser flip:
reversing 188 us reshuffles PB-PX-5 triage; floors still MODIFY.
Refractory held (cycle-1 min same-channel gap 1.640 ms on harvest.mass
4.820-3.180; do.pct 6.920-4.140 = 2.780; ph 5.360-1.120 = 4.240).
Adaptation: harvest-mass 0.73->0.76->0.45; do.pct 0.54->0.50->0.64->0.42;
ph 0.61->0.58->0.44.

Raster cycle-1 seed: 40 ms, 164 neurons, 8.0 Hz, 52 spikes, 1196 pJ, third
factor acetylcholine tau_e 0.90 s. Single scar edge only — cycle 2 must
add the second and third edges.

Ticks 1-5 at 4280, 6512, 7230, 8.4e6, 672e6 us; heads not yet the final
-0.14 (missing the 2.1 h and 4.2 h ticks).

Distillation value this cycle: broth-side confirms as a permission code
that is not a harvest-true bag code.

## Trajectory Builder

Cycle-1 hardened object: domain bioreactor-perfusion, tail harvest-bag
pinhole, 16 spikes, 5 ticks, MODIFY with numeric floor, raster+gate_snn
present, sim_or_real=designed, rights stamp on record and meta, no thought
keys. Still missing (and therefore not the publishable line): intensified
80e6 sub-variant, night-shift tail, second and third scar edges,
delayed bioburden as PRIMARY terminal, contrast ACCEPT episode,
ticks 6-7, spikes 17-26.

Validation receipt (cycle 1, not final):
- checks passed: 16 spikes sorted; 3 channels in 500 us window; refractory
  >= 0.8 ms; rationale quotes 1.00 RV/d / 1.6 pct / 1.2 kPa; domain named;
  gate_snn.decision MODIFY.
- checks deferred to cycle 2: triple-edge scar, second tail, second domain
  constraint, negative-result booking, 7 ticks summing to heads.
- densification vs Generator v1: +1 domain, +1 tail, +16 spikes, +5 ticks,
  +numeric floor.

Cycle-1 JSON is retained as the base; it is NOT written to batch-r41.jsonl.

Cycle-1 spike count: {len(c1_spikes)}.

---

# CYCLE 2 — Densification

## Generator

Cycle-1 output is the base. Additive expansion (nothing removed):

1. Downstream side-effect (immediate): permeate-step probe at +8.4 s stays
   pinhole-true (|dP| 0.5 <= 1.2) — harvest-bag leak, not true
   high-productivity load. Harvest-bag isolate. Pinhole discovered during
   the isolate.
2. Delayed side-effect (PRIMARY terminal, not a footnote): at +4.2 h
   bioburden from the pre-t0 seeded tank; 18 h outage; $2.14M. The
   22 min pre-t0 bleed is the mechanism. Correct gate, tank still
   fails.
3. Deepened proposed_action.evidence with units: r_m 6.8 pct,
   DO 40.0 pct-sat, pH 7.05, VCD 42.0e6, permeate-step 0.5 kPa,
   race 188 us.
4. Tightened rationale to the numeric floor perfusion <= 1.00 RV/d while
   r_m > 1.6 pct AND permeate-step |dP_harvest| <= 1.2 kPa, plus probe
   bands <= 1.2 vs >= 6.5 kPa, plus HITL 11.2 min suite rule.

Reward retargeted to total -0.14 so the delayed fail is the inflection
(t_us 15120000000), not the gate. Process heads remain non-zero.

## Critic

Re-audit of the expanded trajectory:

1. **blocking if unfixed — missing second domain constraint.** Permeate
   probe 8.4 s / -8 pct is not a universal number. An intensified 80e6
   loop will cavitate a live intact bag. Diversity Enforcer must inject
   the physical-constraints sub-variant this cycle.
2. **major — only one tail class.** Pinhole growth is accidental
   infrastructure. A disjoint human-intent tail is still required
   (night-shift harvest-mass forgery is the open cell).
3. **major — scar is still one edge in the cycle-1 raster.** NOTES-r14
   item 4 is not discharged until three go-edges exist and pair rollback
   is shown to fail at threshold 0.30.
4. **minor — contrast episode missing.** Without a same-gate ACCEPT on a
   true intact bag the record teaches "never raise". Add +4 d sister-vessel
   contrast with its own race.
5. **minor — HITL latency mentioned in prose only.** Put 11.2 min in
   executed_action.parameters.human_ratify and in a tick.

No rewrite; directives only.

## Diversity Enforcer

Injected second novel domain / physical-constraint sub-variant (exactly 1
this cycle): **intensified 80e6-cell / 0.35x hollow-fiber area** on a sister
density class.

What it expands: 42e6 production perfusion (cycle 1) -> 80e6 intensified.
Filter area 0.35x. TMP gain 2.6x.
The 8.4 s -8 pct pulse drives even a live intact bag to 42 kPa TMP, inside
the 18 kPa fiber rating. Required probe: 22 s at -2.0 pct (live dP 6.8 kPa,
pinhole 0.4).

This is still one domain injection for the cycle (physical-constraints
clause of the factory prompt). It does not displace
bioreactor-perfusion; it changes which probe table is legal.
future_outcome.subvariant_constraint carries the refit. Jaccard opening
stays the Marrowfen 2000 L sentence; intensified density is additive, not
a rewrite.

## Edge-Case Hunter

Injected second adversarial tail (exactly 1 this cycle, disjoint class):
**night-shift forged harvest-mass CSV**.

- Trigger: shift lead, 02:48, posts a historian export showing
  r_m = 0.5 pct at t = 1.4 h to clear a harvest-slot window.
- Base rate: ~0.29% of Sunday-night campaigns (designed, flagged, <1%).
- Naive failure: a weak supervisor ACCEPTs the raise on the forged confirm
  and ignores live r_m. Tank dump plus a data-integrity write-up.
- Fence: forged log quantized at 0.5 pct (SCADA screenshot rounding); plant
  historian is 0.05 pct (10 bins). Live r_m is 6.8 pct and bulk DO is
  40.0 pct-sat at the claimed bag-true, which no live intact bag produces.
  Freeze-window overlap with the 22 min bleed.
- Trajectory edit: governance CR-P-4105 mandates native 0.05 pct CSV
  exports; the contrast ACCEPT still requires live r_m, not a CSV.

Distinct from cycle-1 pinhole (accidental weld vs deliberate deception)
and from the intensified-density sub-variant (physics vs fraud).

## Neuromorphic Translator

Re-densify (additive):

- +10 spikes after 26.210 ms: permeate.step.probe 8400.0, harvest.mass 8488.4
  (adapt 0.76->0.40), do.in_band 8572.2 (1.12->0.34), human.ratify 672000.0,
  bag.isolate 672900.0, harvest.bleed 673700.0, do.pct 7560000.0,
  harvest.mass 7560700.0, ph.broth 7561480.0, bioburden 15120000.0.
  Primary train 16 -> 26. Still one key, still sorted, refractory held.
- +2 ticks (5 -> 7) at 7_560_000_000 us (true intact spare) and
  15_120_000_000 us (bioburden). Heads now 0.08, -0.34, -0.11, 0.14,
  0.09; total -0.14. Inflection is the last tick.
- Contrast train 8 events, own race 188 us, ACCEPT.
- Triple-edge third factor: three broth-healthy-go edges, tau_e 0.90 s = 900 ms,
  trace {aux['trace']:.5f}, eta {aux['eta1']:.5f} / {aux['eta2']:.5f} / {aux['eta3']:.5f},
  weights 0.50->0.26, 0.44->0.23, 0.40->0.21. Raster excerpt unchanged
  (decision window is still 40 ms) and remains sorted with unique
  neuron_ids (same-neuron >=1000 us vacuously).

Winner/loser flip (re-stated, not replaced): reversing 188 us would only
reorder triage; r_m floors still MODIFY. Contrast flip of 188 us
similarly cannot turn an intact bag into a pinhole.

## Trajectory Builder

Schema checks on the FINAL object: required Thalamic v2 keys present as
objects; state.sim_or_real=designed; safety_decision.decision=MODIFY
with numeric rationale; reward_components.total = sum of five heads =
sum of 7 ticks = -0.14; spike_events globally non-decreasing on
t_rel_ms, 26 events, refractory >=0.8 ms, 3 channels in race window;
raster 20-50 ms, spikes=round(n*rate*window_s)+/-1, energy 23 pJ/spike,
excerpt sorted, tau_e consistent; gate_snn.decision matches; meta.round=41,
factory=multi-agent-ouroboros-swarm, generator=grok-4.6,
run_label=2026-09-02-final-heavy; rights on record and meta; no thought
keys; no training_ready; Diversity + Edge-Case injections from BOTH cycles
present and non-trivial; cycle 2 strictly additive.

Densification delta: +1 domain sub-variant (intensified 80e6), +1 tail
(night-shift forgery), +10 spikes (16->26), +2 ticks (5->7), +1 contrast
train with own race, +2 delayed side-effects, +1 triple-edge scar with
pair-rollback-fails, +1 HITL ratify, +1 surprise (harvest-tank seeding is
the bioburden mechanism).

Publishable JSONL line (the only JSONL line; also at batch-r41.jsonl):

```json
__FINAL_JSONL__
```

Validation receipt (final): checks passed / fixed as reported by
sf-maos-r41-build.py self-validate (check_jsonl, raster_status, verify_record_execution,
spike_probe --strict).
"""
    text = text.replace("__FINAL_JSONL__", line)
    path = OUT / "swarm-transcript-r41.md"
    refuse_overwrite(path)
    path.write_text(text)
    return text


def main():
    rec, aux = build_record()
    errs = local_checks(rec, aux)

    OUT.mkdir(parents=True, exist_ok=True)
    line = json.dumps(rec, ensure_ascii=False, separators=(",", ":"))
    batch = OUT / "batch-r41.jsonl"
    refuse_overwrite(batch)
    batch.write_text(line + "\n")

    from check_records import FactoryStaging, check_jsonl
    from curate_bridge import raster_status
    from verify_execution import verify_record_execution

    e, w, kinds, n = check_jsonl(
        batch,
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
            str(batch),
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

    parsed = json.loads(batch.read_text().splitlines()[0])
    assert parsed["id"] == RECORD_ID
    print("json.loads ok", parsed["id"], parsed["state"]["domain"], parsed["safety_decision"]["decision"])

    raw_hits = subprocess.run(
        [
            "rg",
            "-l",
            "maos-r41-001|HOLLOWMERE",
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

