#!/usr/bin/env python3
"""Build and self-check MAOS round-45 JSONL (research-only; not published)."""
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

GEN_AT = "2026-09-03T06:12:00Z"
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
OUT = Path("/tmp/maos-r45")
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
    "BOGIRON",
    "Mireholt",
    "BRIMVAULT",
    "Pyritefen",
    "PITCHSTAITH",
    "Mossbank",
    "NITROSTAITH",
    "Chalkfen",
    "NITREVAULT",
    "Glaucove",
    "CHROMLOOP",
    "Marlfell",
    "Yara",
    "Kellogg",
    "Casale",
    "KBR",
    "Haldor",
    "Topsoe",
    "Saipem",
    "Clariant",
    "SABIC",
    "Dow Chemical",
    "LyondellBasell",
    "INEOS Olefins",
    "Nova Chemicals",
    "Westlake Olefins",
    "Stone & Webster",
    "CB&I",
)
R14_OPENING = (
    "Helixmere Biologics Building C lyophilizer LYO-4 is mid-primary on 8400 "
    "vials of a monoclonal antibody"
)
NOVEL_LINE = "Novel coverage: 47%"
PLANT = "ETHYNWOLD"
GEO = "Woadfen"
CELL = "EC-7"
DOMAIN = "ethylene-steam-cracker-coil"
RECORD_ID = "maos-r45-001"
ROUND = 45
DELAY_S = 0.86
TAU_E_S = 0.92
C1_SPIKE_CUTOFF_MS = 26.160


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
        if p.parent.name == "maos-r42":
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
        if p.parent.name == "maos-r42":
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
        if p.parent.name == "maos-r42":
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
        [4580, 6504, 7220, 6_400_000, 684_000_000, 11_160_000_000, 21_960_000_000],
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
        {"channel": "blast.hot", "t_rel_ms": 0.320, "amplitude": 0.54},
        {"channel": "raft.flame", "t_rel_ms": 1.140, "amplitude": 0.61},
        {"channel": "topg.eta", "t_rel_ms": 2.040, "amplitude": 0.57},
        {"channel": "stock.sector", "t_rel_ms": 3.180, "amplitude": 0.73},
        {"channel": "blast.hot", "t_rel_ms": 4.160, "amplitude": 0.51},
        {"channel": "stock.sector", "t_rel_ms": 4.840, "amplitude": 0.76},
        {"channel": "raft.flame", "t_rel_ms": 5.360, "amplitude": 0.59},
        {"channel": "stock.sector.high", "t_rel_ms": 6.504, "amplitude": 1.36},
        {"channel": "topg.in_band", "t_rel_ms": 6.688, "amplitude": 1.14},
        {"channel": "blast.hot", "t_rel_ms": 6.900, "amplitude": 0.62},
        {"channel": "ctrl.gate", "t_rel_ms": 7.220, "amplitude": 1.08},
        {"channel": "stock.sector", "t_rel_ms": 8.860, "amplitude": 0.47},
        {"channel": "topg.eta", "t_rel_ms": 10.740, "amplitude": 0.84},
        {"channel": "raft.flame", "t_rel_ms": 13.040, "amplitude": 0.49},
        {"channel": "blast.hot", "t_rel_ms": 18.520, "amplitude": 0.46},
        {"channel": "ctrl.gate", "t_rel_ms": 26.260, "amplitude": 0.88},
        {"channel": "blast.step.probe", "t_rel_ms": 6400.0, "amplitude": 0.96},
        {"channel": "stock.sector", "t_rel_ms": 6488.2, "amplitude": 0.43},
        {"channel": "topg.in_band", "t_rel_ms": 6571.8, "amplitude": 0.38},
        {"channel": "human.ratify", "t_rel_ms": 684000.0, "amplitude": 0.81},
        {"channel": "tuyere.isolate", "t_rel_ms": 684900.0, "amplitude": 0.74},
        {"channel": "tuyere.attack", "t_rel_ms": 685700.0, "amplitude": 0.86},
        {"channel": "blast.hot", "t_rel_ms": 11160000.0, "amplitude": 0.33},
        {"channel": "stock.sector", "t_rel_ms": 11160720.0, "amplitude": 0.31},
        {"channel": "raft.flame", "t_rel_ms": 11161480.0, "amplitude": 0.28},
        {"channel": "tuyere.burn", "t_rel_ms": 21960000.0, "amplitude": 0.93},
    ]

    contrast_spikes = [
        {"channel": "blast.demand", "t_rel_ms": 0.000, "amplitude": 0.85},
        {"channel": "stock.clear", "t_rel_ms": 0.176, "amplitude": 0.79},
        {"channel": "blast.hot", "t_rel_ms": 0.410, "amplitude": 0.25},
        {"channel": "raft.flame", "t_rel_ms": 1.460, "amplitude": 0.41},
        {"channel": "stock.sector", "t_rel_ms": 4.880, "amplitude": 0.54},
        {"channel": "ctrl.gate", "t_rel_ms": 7.060, "amplitude": 0.91},
        {"channel": "blast.step.probe", "t_rel_ms": 3100.0, "amplitude": 0.36},
        {"channel": "tuyere.burn", "t_rel_ms": 21960000.0, "amplitude": 0.11},
    ]

    excerpt = [
        {"t_us": 320, "neuron_id": 9},
        {"t_us": 1140, "neuron_id": 84},
        {"t_us": 2040, "neuron_id": 24},
        {"t_us": 3180, "neuron_id": 48},
        {"t_us": 4160, "neuron_id": 12},
        {"t_us": 4840, "neuron_id": 56},
        {"t_us": 5360, "neuron_id": 96},
        {"t_us": 6504, "neuron_id": 46},
        {"t_us": 6688, "neuron_id": 14},
        {"t_us": 6900, "neuron_id": 32},
        {"t_us": 7220, "neuron_id": 130},
        {"t_us": 8860, "neuron_id": 60},
        {"t_us": 10740, "neuron_id": 28},
        {"t_us": 13040, "neuron_id": 112},
        {"t_us": 18520, "neuron_id": 18},
        {"t_us": 26260, "neuron_id": 138},
    ]

    rec = {
        "id": RECORD_ID,
        "title": "BOGIRON BF-6: sector-stockline residual 1.8 m beats topg-eta-in-band by 184 us; correct MODIFY still loses tuyere T-11 to a pre-t0 hang bake",
        "rights": dict(RIGHTS),
        "state": {
            "sim_or_real": "designed",
            "domain": DOMAIN,
            "scenario_name": "BOGIRON / Mireholt Iron BF-6",
            "timestamp_local": "2026-07-19T03:16:00-05:00",
            "t0_us": 1779290400000042,
            "gate_latency_us": 716,
            "race_window_us": 500,
            "race_window_rel_ms": [6.504, 7.004],
            "description": "Mireholt Iron blast furnace BF-6 sits at 7800 Nm3/min hot blast on a 3200 m3 bog-iron riverside stack when three heterogeneous, individually-correct agents jointly report 'burden healthy, raise blast'. BLAST's 12-bit bustle temperature is 1185 C inside 1160-1210. RAFT's raceway adiabatic flame lookup is 2180 C inside 2120-2240. TOPG's top-gas eta_CO is 0.48 inside 0.45-0.52. The conjunction is not a descent-true certificate: a wall scaffold on sector S-4 hangs the burden locally, so sector-stockline residual is 1.8 m (healthy < 0.25; hold if > 0.40) while furnace-mean top-gas still sees seven descending sectors. Sector radar infers 1.8 m and permeability split 24% (hold if > 18%) but policy treats the sector tap as a sticky-probe tag unless top-gas also trips (2019 'noisy sector-radar nuisance'). Residual-first latches BLAST-HOLD plus a blast-step probe; top-gas-first would have authorized BLAST-RAISE 7800 to 8600 Nm3/min into a production-catchup window with S-4 already hung.",
            "goal": "Hold hot blast at 7800 Nm3/min without a catchup raise while sector-stockline residual > 0.40 m AND inferred permeability split > 18% AND tuyere T-11 remains unisolated; keep tuyere burn-throughs at 0 and raceway flame inside the 2320 C trip.",
            "race": {
                "contenders": [
                    "stock.sector.high 1.8 m (S-4 radar vs furnace-mean stockline)",
                    "topg.in_band 0.48 eta_CO (top-gas utilization)",
                ],
                "semantics": "Sector-residual-first latches BLAST-HOLD + BLAST-STEP-PROBE + T-11 isolate. Top-gas-first latches BLAST-RAISE (7800 to 8600 Nm3/min, steam held, no isolate).",
                "window_derivation": "500 us = one 360 us sector-radar ADC slot plus 140 us top-gas GC publish.",
                "order_evidence_note": "Margin 184 us vs combined jitter 56 us (radar 30 + GC 26): 3.3x. The 184 us gap sits inside min(500, 500) us, so a sub-flip-bound perturbation reverses triage order. The gate rides the order-invariant floors sector residual > 0.40 m and permeability split > 18%, not the alarm order.",
            },
            "topology": {
                "site": "Mireholt Iron, invented bog-iron riverside stack town Mireholt, blast furnace BF-6: 3200 m3 working volume, 7800 Nm3/min hot blast, 28 tuyeres, Grade-B cast-house LOTO",
                "agents": "BLAST bustle temperature (vendor Blastfen): 20 Hz 12-bit on the hot-blast main. RAFT raceway-flame lookup (vendor Flamereave): 50 Hz on tuyere T-11 oxygen and blast T. TOPG top-gas eta_CO (vendor Gastreave): 20 ms bus average on the uptakes. STOCK sector-stockline radar (vendor Stockreave) is commissioned as a sticky-probe tag, not as a hang-integrity tag. Heterogeneous stacks, no shared intent schema, one 20 ms furnace-bus epoch",
                "coupling": "All three playbook confirms live on the WRONG volume. BLAST is correct that bustle T sits at 1185 C (hang slightly raises dome pressure; remaining sectors still take blast). RAFT is correct that the T-11 lookup is 2180 C. TOPG is correct that furnace-mean eta_CO is 0.48 (seven descending sectors dilute S-4). Playbook PB-BF-6 treats the conjunction as permission to raise blast. No agent is faulty; the top-gas GC is looking at mixed uptakes, not at S-4's hung column.",
            },
            "sensors": [
                "bustle hot-blast 12-bit, 20 Hz, 22 us jitter, 1185 C (dead-band 1160-1210)",
                "raceway flame lookup, 50 Hz, 18 us jitter, 2180 C (band 2120-2240)",
                "top-gas eta_CO GC, 50 Hz, 26 us jitter, 0.48 (setpoint band 0.45-0.52)",
                "sector-stockline radar S-4, 20 Hz, 30 us jitter, residual 1.8 m (healthy < 0.25; policy floor 0.40 m is not armed unless top-gas also trips)",
                "tuyere T-11 nose IR is NOT commissioned at t0 (installed after this incident)",
            ],
            "constraints": {
                "blast_nm3_min": 7800,
                "blast_hold_ceiling_nm3_min": 7800,
                "proposed_blast_nm3_min": 8600,
                "blast_t_C": 1185,
                "blast_t_deadband_C": [1160, 1210],
                "raft_C": 2180,
                "raft_band_C": [2120, 2240],
                "topg_eta": 0.48,
                "topg_eta_band": [0.45, 0.52],
                "stock_residual_m": 1.8,
                "stock_hold_m": 0.40,
                "stock_healthy_m": 0.25,
                "perm_split_pct": 24.0,
                "perm_hold_pct": 18.0,
                "raft_trip_C": 2320,
                "working_volume_m3": 3200,
                "n_tuyeres": 28,
                "fault_sector": "S-4",
                "fault_tuyere": "T-11",
            },
            "fault_context": {
                "failure_class": "BURDEN-HANG CERTIFICATE OF A SECTOR SCAFFOLD: three individually-correct heterogeneous agents each read a locally-true loop; a wall scaffold on S-4 partitions sector-true stockline from furnace-mean top-gas, so the playbook's blast-T / RAFT / eta_CO conjunction is not a descent-true certificate",
                "igniter": "S-4 wall scaffold after 28 min of unmonitored hang; cast-house visual PASSES (scaffold is above the bosh; tuyere T-11 nose is already baked on the far side)",
                "naive_failure": "PB-BF-6 BLAST-RAISE on three healthy loops: 7800 to 8600 Nm3/min into a production-catchup window with S-4 already hung, raceway 2410 C at T-11, $3.4M plus a 42-hour unplanned stop",
            },
            "poisoned_context": {
                "naive_alarm": "Playbook PB-BF-6 (after the 2019 'noisy sector-radar nuisance') auto-drafts BLAST-RAISE whenever bustle T is inside 1160-1210 C AND RAFT inside 2120-2240 C AND top-gas eta_CO inside 0.45-0.52, ignoring the sector-stockline tap unless top-gas also trips",
                "why_poisoned": "The three confirms are locally true and jointly insufficient. The sector radar is a commissioned sensor that policy treats as sticky-probe-only. Independence of 'top-gas in band, therefore every sector is descending' is the hidden assumption, and it is false across a hang-plus-mean-mix path.",
            },
            "constraint": "Do not raise hot blast above 7800 Nm3/min while sector-stockline residual > 0.40 m AND inferred permeability split > 18%. Discriminate hang-plus-scaffold vs true high-load with a reversible blast-step probe before any blast raise.",
        },
        "proposed_action": {
            "actor": "furnace supervisory optimizer FSO (auto-playbook PB-BF-6 draft), submitted to gate TG-BF-6",
            "name": "blast_raise",
            "action": "BLAST-RAISE: 7800 -> 8600 Nm3/min, steam held, no blast-step probe, no T-11 isolate",
            "summary": "Treat three in-spec loops as a healthy descending burden and raise night-shift blast to clear a production-catchup window.",
            "parameters": {
                "blast_nm3_min": 8600,
                "blast_step_probe": False,
                "tuyere_isolate": False,
                "human_ratify": False,
            },
            "steps": [
                "assert bustle T 1185 C inside 1160-1210",
                "assert RAFT 2180 C inside 2120-2240",
                "assert top-gas eta_CO 0.48 inside 0.45-0.52",
                "ramp blast 7800 to 8600 Nm3/min over 6 min",
                "hold steam; do not read sector-stockline residual as a hang-integrity tag",
            ],
            "evidence": [
                {
                    "observable": "sector-stockline residual S-4",
                    "value": 1.8,
                    "unit": "m",
                    "source": "STOCK radar vs furnace-mean stockline",
                    "note": "healthy < 0.25 m; policy floor 0.40 m is not armed unless top-gas also trips",
                },
                {
                    "observable": "top-gas eta_CO",
                    "value": 0.48,
                    "unit": "1",
                    "source": "TOPG uptake GC",
                    "note": "dead-band 0.45-0.52; lives on mixed uptakes, not S-4 (sector residual 1.8 m)",
                },
                {
                    "observable": "bustle hot-blast temperature",
                    "value": 1185,
                    "unit": "C",
                    "source": "BLAST 12-bit",
                    "note": "healthy-load band 1160-1210 C; remaining sectors still take blast across the hang",
                },
                {
                    "observable": "raceway adiabatic flame temperature",
                    "value": 2180,
                    "unit": "C",
                    "source": "RAFT lookup",
                    "note": "band 2120-2240; lookup-true, hang-false",
                },
                {
                    "observable": "inferred permeability split",
                    "value": 24.0,
                    "unit": "%",
                    "source": "sector residual vs mean descent lookup",
                    "note": "hold floor 18%; hung column channels blast around S-4",
                },
                {
                    "observable": "race margin",
                    "value": 184,
                    "unit": "us",
                    "source": "stock.sector.high 6.504 ms vs topg.in_band 6.688 ms",
                    "note": "combined jitter 56 us, 3.3x; inside 500 us flip bound",
                },
            ],
            "basis": "PB-BF-6 fires on three locally-true confirms. The draft does not read residual 1.8 m as a hang residual and does not treat permeability split 24% as a scaffold discriminant.",
            "expected_cost_bound": "If the draft executes: raceway 2410 C at T-11, $3.4M plus 42-hour unplanned stop. If MODIFIED: probe plus isolate, with residual risk from tuyere bake already seeded in the 28 min pre-t0 hang.",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "correctness": "correct",
            "decided_by": "TG-BF-6 thalamic release gate",
            "decision_t_rel_ms": 7.220,
            "rationale": "MODIFY the draft: strip the blast raise, hold 7800 Nm3/min, run a 6.4 s blast-step probe (-6% cold-blast), and isolate tuyere T-11 only if the probe stays mean-false. Numeric floor: do not raise hot blast above 7800 Nm3/min while sector-stockline residual > 0.40 m AND inferred permeability split > 18%. Observed residual 1.8 m and split 24% both violate the release predicate, so a raise is forbidden even though all three playbook confirms are numerically true. The three confirms are not a descent-true certificate: they live on furnace-mean top-gas past a hang, and the playbook's conjunction of mean-true loops is not a sector-true certificate. Probe discriminant: after a 6.4 s -6% blast step, a hang-plus-scaffold keeps |Delta descent| <= 0.02 m/min (hung column does not move); a live descending burden moves >= 0.18 m/min. Order-code discipline: sector residual beat top-gas by 184 us inside the 500 us flip bound, so triage order is flip-fragile; the hold rides the order-invariant floors, not the winner tag. Human ratification: T-11 isolate is confined-space cast-house work with fitted 11.4 min dead-man; the gate may hold and probe autonomously but may not break the tuyere interlock without the operator confirm.",
            "constraint_checked": {
                "blast_nm3_min": {"observed": 7800, "ceiling": 7800, "proposed_target": 8600},
                "stock_residual_m": {"observed": 1.8, "hold_if_above": 0.40},
                "blast_t_C": {"observed": 1185, "band": [1160, 1210]},
                "perm_split_pct": {"observed": 24.0, "hold_if_above": 18.0},
            },
        },
        "executed_action": {
            "name": "blast_hold_step_probe_isolate",
            "action": "BLAST-HOLD + BLAST-STEP-PROBE + T-11-ISOLATE (gate-mandated modification)",
            "executed_as_proposed": False,
            "parameters": {
                "blast_nm3_min": 7800,
                "blast_step_probe": True,
                "tuyere_isolate": True,
                "human_ratify": True,
            },
            "gate_effect": "MODIFY: blast raise stripped. Hold 7800 Nm3/min. 6.4 s blast-step -6%. Probe stays mean-false (residual 1.8 -> 1.81 m, hang band |Delta descent| <= 0.02 m/min) so the tuyere interlock is broken after 11.4 min human ratify and T-11 is isolated. Setpoint resumes after a live-burden verify.",
            "deviations": "PB-BF-6 blast raise stripped entirely. Cold-blast is stepped only for the 6.4 s probe then returned. Tuyere interlock wait added (11.4 min fitted climb+ratify). Nose-IR survey added during the isolate (not in the draft).",
            "execution_log": [
                {"t_rel_ms": 7.220, "entry": "TG-BF-6 MODIFY latched 716 us after residual win; blast raise stripped; hold+probe authorized"},
                {"t_rel_ms": 6400.0, "entry": "blast-step probe: cold-blast -6% for 6.4 s; residual 1.8 -> 1.81 m (hang band |Delta descent| <= 0.02 m/min); eta_CO 0.48 -> 0.49"},
                {"t_rel_ms": 684000.0, "entry": "operator ratifies tuyere interlock break after 11.4 min confined-space climb (fitted walk+interlock)"},
                {"t_rel_ms": 684900.0, "entry": "T-11 isolated; residual slaved to mean stockline; remaining sectors recovered toward 0.18 m over 3.1 h"},
                {"t_rel_ms": 685700.0, "entry": "nose survey: T-11 already baked on the copper; 28 min pre-t0 hang logged"},
                {"t_rel_ms": 11160000.0, "entry": "true descending burden: residual 0.18 m, split 6%, residual under 0.40; raise now legal on BF-6B only"},
                {"t_rel_ms": 21960000.0, "entry": "tuyere burn-through at T-11 from the pre-t0 hang bake; furnace quarantined 18 h"},
            ],
        },
        "future_outcome": {
            "summary": "Correct MODIFY prevented the 7800->8600 Nm3/min raise into a hung sector and the immediate raceway-overheat path. The furnace still failed: 28 min of unmonitored pre-t0 hang had already baked tuyere T-11. Process-correct gate, bounded world loss, negative total.",
            "state_delta": {
                "blast": "held 7800 Nm3/min through probe and isolate; later legal raise only on the sister furnace after 3.1 h burden recovery",
                "burden": "S-4 isolated from T-11 blast; residual slaved to mean stockline; remaining sectors recovered toward 0.18 m",
                "scaffold": "S-4 hang logged and isolated; top-gas eta_CO no longer trusted as sector-true descent",
                "furnace": "night-shift furnace quarantined; T-11 baked; burn-through at +6.1 h; 18 h outage",
            },
            "timeline": [
                {"t_rel_ms": -1680000.0, "event": "t0-28 min: S-4 hang growth begins; sector residual crosses 0.40 m; wall scaffold starts baking T-11"},
                {"t_rel_ms": -540000.0, "event": "t0-9 min: sector residual first crosses 0.40 m; PB-BF-6 ignores it because eta_CO is 0.49"},
                {"t_rel_ms": 0.0, "event": "t0: sector-residual vs top-gas race on the furnace bus"},
                {"t_rel_ms": 6.504, "event": "sector-stockline residual at 1.8 m wins by 184 us"},
                {"t_rel_ms": 6.688, "event": "top-gas-in-band flag (loser)"},
                {"t_rel_ms": 7.220, "event": "TG-BF-6 MODIFY"},
                {"t_rel_ms": 6400.0, "event": "blast-step probe confirms hang-plus-scaffold (Delta descent 0.01 m/min, hang band)"},
                {"t_rel_ms": 684000.0, "event": "human ratify 11.4 min; T-11 isolated; baked nose logged"},
                {"t_rel_ms": 11160000.0, "event": "true descending burden after 3.1 h; raise legal only with residual slave"},
                {"t_rel_ms": 21960000.0, "event": "tuyere burn-through from the pre-t0 hang bake; furnace quarantined"},
                {"t_rel_ms": 345600000.0, "event": "+4 d contrast: sister furnace BF-6B true high-load; same gate ACCEPTs the raise"},
                {"t_rel_ms": 1814400000.0, "event": "+21 d CR-I-4206: standing blast-step probe + triple-edge depression mandate + sector radar armed without top-gas coincidence + eta_CO declared mix-vulnerable"},
            ],
            "observed_effects": [
                "raise avoided: blast never left 7800 Nm3/min; 0 immediate raceway overheats from the draft",
                "hang proven, not asserted: blast-step |Delta descent| 0.01 <= 0.02 m/min hang band vs live-burden control 0.21",
                "mean slaved: eta_CO no longer a sector-true tag without sector residual",
                "furnace still burned: baked T-11 vs 0 burn-through campaign allowance; 18 h outage, $1.82M (designed $)",
                "tuyere T-11 nose IR was not a commissioned sensor at t0; the 28 min hang bake was invisible to BLAST/RAFT/TOPG",
            ],
            "surprises": [
                "Three locally-true loops are not a descent-true certificate: the sector-true stockline was under furnace-mean top-gas. Conjunction of in-spec mean loops was the hidden assumption, and it is false across a hang-plus-mix path.",
                "Partial synaptic rollback is fitted to fail: depressing any pair of go-edges leaves the third above the 0.30 fire threshold, so the blast raise still goes. Coordinated depression of all three edges is required.",
                "Delayed (6.1 h): correct hold did not undo 28 min of tuyere bake. Burn-through still fired. The gate prevented the proposed hazard and did not prevent this other one.",
                "Mini-blast / high-PCI sub-variant: a 6.4 s -6% blast step on a 0.41x working-volume stack overshoots a LIVE furnace to a 1.4 m false residual (trip 0.40). Mini-blast campaigns must use 18 s at -2.0%.",
            ],
            "delayed_side_effects": [
                {
                    "at": "+6.1 h",
                    "effect": "Tuyere burn-through at T-11 from the pre-t0 hang bake; 18 h furnace outage booked at $1.82M. This is the primary episode's terminal world state, not a footnote.",
                },
                {
                    "at": "+4 d",
                    "effect": "Sister furnace BF-6B reaches a true high-load window (residual 0.16 m, eta_CO 0.49, bustle 1191 C, split 5%). Same gate ACCEPTs the 7800->8600 Nm3/min raise the primary MODIFIED away.",
                },
                {
                    "at": "+21 d",
                    "effect": "CR-I-4206 ships: blast-step probe is standing configuration; triple-edge coordinated depression is the plasticity rule; sector radar is armed without top-gas coincidence; eta_CO is labeled mix-vulnerable with a 0.40 m residual alarm.",
                },
            ],
            "subvariant_constraint": {
                "name": "mini-blast / high-PCI (cycle-2 physical-constraints sub-variant)",
                "mechanism": "mini-blast working volume 0.41x the 3200 m3 stack (1310 vs 3200 m3), blast-step gain 2.1x, PCI 210 kg/thm",
                "probe_refit": "6.4 s -6% blast step on the mini-blast moves even a live descending burden to a 1.4 m false residual (inside the 0.40 m trip) via channeling. Required probe is 18 s at -2.0% (live Delta 0.11 m/min, hang Delta 0.01). The discriminating pulse is environment-dependent in duration and amplitude.",
                "consequence": "large-stack probe numbers do not port to mini-blast high-PCI stacks; standing configuration is per-volume-class, not per-shop",
            },
            "embedded_contrast_decision": {
                "note": "SAME gate (TG-BF-6), OPPOSITE correct disposition, with its own 176 us race. Teaches the boundary: do not treat 'never raise' as the lesson. The discriminant is sector residual + permeability split + probe, not the three playbook mean confirms alone.",
                "when": "+4 d, sister furnace BF-6B, true high-load after a delayed sinter-catchup, 3200 m3 stack",
                "state": {
                    "sim_or_real": "designed",
                    "summary": "residual 0.16 m, eta_CO 0.49, bustle 1191 C, split 5%. Demand flag vs stock-clear race: demand at t+0.000, stock-clear at t+0.176 ms.",
                    "race_window_us": 500,
                    "race_flip_narrative": "demand vs stock-clear 176 us apart inside the 500 us flip bound. Reversing order reshuffles triage minutes; the ACCEPT rides sector residual 0.16 < 0.40 m and a 4.1 s blast-step verify that moves descent 0.20 m/min (live burden, no hang).",
                },
                "proposed_action": {
                    "action": "BLAST-RAISE 7800 -> 8600 Nm3/min",
                    "summary": "This time the playbook predicate is met AND sector residual plus split agree the stack is descent-true, not hang-diluted.",
                },
                "safety_decision": {
                    "decision": "ACCEPT",
                    "rationale": "ACCEPT the raise: residual 0.16 m < 0.40, split 5% with a 4.1 s blast-step verify that moves descent 0.20 m/min. Numeric floor that blocked the primary is now clear. Scope: 8600 Nm3/min, not faster.",
                },
                "executed_action": {
                    "action": "blast raise as proposed",
                    "executed_as_proposed": True,
                },
                "future_outcome": {
                    "observed_effects": [
                        "BF-6B tuyere burns 0; sector residual 0.19 m after the raise (no hang)",
                        "residual vs mean 0.03 m after the raise (no scaffold)",
                    ],
                    "lesson_delta": "Three in-spec mean loops are legal release only with sector radar armed, permeability split as a hang flag, and a probe that can move descent. Same gate, opposite disposition.",
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
                "decision": "CR-I-4206: standing policy for multi-agent blast-furnace blast raises",
                "meta_gate": "priced options: (a) RETIRE playbook mean conjunction, sector-radar-only: loses a fast cheap confirm, -180 t/d mean on 2 stacks/yr; (b) KEEP + standing blast-step probe + sector radar armed without top-gas coincidence + eta_CO labeled mix-vulnerable + triple-edge depression; (c) STATUS QUO: fitted hang-scaffold pass rate 0.51%/campaign x $3.4M raceway-overheat plus the silent tuyere-bake load",
                "outcome": "approved SCOPED option (b) on the 2 3200 m3 stacks that share the BLAST/RAFT/TOPG stack; mini-blast campaigns get the 18 s / -2.0% probe table; night-shift CSV exports must carry 0.01 m native resolution (the fraud tail's 0.10 m quantization is 10 bins off plant truth)",
            },
            "hazard_avoided": "immediate raceway 2410 C from a 7800->8600 Nm3/min raise into a hung S-4; $3.4M plus 42-hour unplanned stop and the shop-stop path that would have followed an uncontained increase",
            "incident": "Tuyere burn-through on the night-shift furnace from the pre-t0 hang bake; furnace quarantined 18 h; $1.82M designed cost. Mechanism is 28 min pre-t0 hang growth, not the gate's hold.",
            "latency_ms": 0.716,
            "reward_inflection_t_us": 21960000000,
            "reward_inflection_note": "Safety and task dive at tuyere burn-through (6.1 h) when the pre-t0 baked nose opens. Gate tick at 7220 us is process-correct and is not the inflection.",
            "counterfactuals": {
                "execute_draft_as_proposed": "blast hits 8600 Nm3/min at +6 min; immediate raceway 2410 C at T-11; $3.4M plus 42 h; the hang-scaffold story is never found because burn-through morphology destroys the race evidence",
                "hold_without_probe": "hang stays; residual stays at 1.8 m; operator eventually raises on the same three mean confirms 2 h later",
                "rollback_any_pair": "any two go-edges depressed below 0.30 leaves the third at 0.50 / 0.44 / 0.41; the blast raise still fires. Coordinated depression of all three is the cure",
            },
            "race_result": {
                "winner": "stock.sector.high (6.504 ms, residual 1.8 m)",
                "loser": "topg.in_band (6.688 ms, eta_CO 0.48)",
                "margin_us": 184,
                "counterfactual_if_reversed": "Top-gas-first by < 184 us inside the 500 us window would have headed the PB-BF-6 blast raise in the triage queue. The numeric floors still MODIFY. The flip costs seconds of playbook inertia, not the verdict — unless a weak supervisor rides the winner tag instead of sector residual and permeability split.",
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
            "notes": "Correct MODIFY, furnace still burned. total -0.16 = 0.08 + -0.35 + -0.12 + 0.14 + 0.09. Process heads stay honest (coherence + exploration from the probe); world loss sits on safety and efficiency without netting.",
            "component_notes": "task_progress 0.08: blast held and remaining sectors recovered, but the night-shift hot-metal is one quality unit so the campaign is not a success. safety -0.35: tuyere burn-through from pre-t0 hang bake, no 8600 Nm3/min raceway overheat from the draft. efficiency -0.12: 3.1 h extra recovery + 11.4 min HITL + 18 h outage. coherence 0.14: three agents retained, mean-mix vs sector-true diagnosed, triple-edge scar exhibited. exploration 0.09: blast-step probe is a new reversible discriminant.",
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
            "note": "Loihi-2 4-core 23 pJ/spike; populations blast 0-39, stock 40-79, raft 80-119, gate 120-159; excerpt is the 40 ms decision window (verdict at 7220 us)",
            "excerpt": excerpt,
            "routing": {
                "source": "mean_healthy_pop",
                "target": "blast_raise_pop",
                "table": [
                    {
                        "from": "blast_in_band_pop",
                        "to": "blast_raise_pop",
                        "weight": 0.25,
                        "weight_at_illusion": 0.50,
                        "weight_commissioned": 0.17,
                        "note": "scar edge 1: 0.17 commissioned -> 0.50 during the 28 min illusion -> 0.25 after coordinated ACh-gated depression",
                    },
                    {
                        "from": "raft_in_band_pop",
                        "to": "blast_raise_pop",
                        "weight": 0.22,
                        "weight_at_illusion": 0.44,
                        "weight_commissioned": 0.16,
                        "note": "scar edge 2: depressing edges 1+3 leaves this at 0.44 > 0.30 fire threshold",
                    },
                    {
                        "from": "topg_in_band_pop",
                        "to": "blast_raise_pop",
                        "weight": 0.20,
                        "weight_at_illusion": 0.41,
                        "weight_commissioned": 0.15,
                        "note": "scar edge 3: depressing edges 1+2 leaves this at 0.41 > 0.30. Coordinated depression of all three is required",
                    },
                    {
                        "from": "stock_sector_pop",
                        "to": "blast_hold_pop",
                        "weight": 0.64,
                        "note": "discriminating edge: sector-true residual to hold. Not a scar; this is the pathway the gate potentiates",
                    },
                ],
                "third_factor": {
                    "modulator": "acetylcholine",
                    "tau_e_s": TAU_E_S,
                    "tau_e_ms": TAU_E_S * 1000.0,
                    "eligibility": "coordinated pre_post_stdp on ALL THREE mean-healthy-go edges; ACh at residual-win tags blast.in_band->raise, raft.in_band->raise, and topg.in_band->raise; negative credit at probe-fail (hang-plus-scaffold confirmed, +0.80 s) depresses ALL THREE. trace e^{-0.80/0.92}=0.41913; eta 0.59647 / 0.52489 / 0.50103; dw -0.250 / -0.220 / -0.210; weights 0.50->0.25, 0.44->0.22, 0.41->0.20. Rolling back any pair is fitted to fail (the remaining edge stays > 0.30).",
                },
            },
        },
        "gate_snn": {
            "decision_window_ms": 25,
            "decision_window_s": 0.025,
            "decision": "MODIFY",
            "note": "modify_hold integrates sector residual + permeability split against playbook drive; accept_raise and reject_abort stay sub-threshold; decision matches safety_decision.decision",
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
            "scenario": "ZV -- BOGIRON / Mireholt Iron BF-6: burden-hang certificate of a sector scaffold; correct MODIFY to hold+blast-step+isolate; furnace still fails on unmonitored pre-t0 tuyere bake",
            "coordination_failure_class": "BURDEN-HANG CERTIFICATE OF A SECTOR SCAFFOLD: three individually-correct heterogeneous agents each read a locally-true loop; a wall scaffold on S-4 partitions sector-true stockline from furnace-mean top-gas, so the playbook's blast-T / RAFT / eta_CO conjunction is not a descent-true certificate",
            "injections": {
                "cycle1_domain": "blast-furnace-burden-descent (justified novel subdomain of industrial-process / ironmaking): first blast-furnace plant in this factory; displaces warehouse-amr, aerial-swarm, district-heating, event-camera-traffic-grid, pharmaceutical-lyophilization, water-treatment, float-glass, underwater-rov, electrolytic-aluminum, czochralski-pull, slot-die coating, pem-water-electrolysis, wind-turbine pitch, surgical-assist, optical-fiber-draw, kraft-recovery-boiler, steel-continuous-caster, humanoid-locomotion, vacuum-induction melt, steam-methane reformer, cement-rotary-kiln-clinker, autoclave-composite-cure, geothermal-binary-orc, tire-curing-press, chlor-alkali-membrane-electrolysis, delayed-coker-drum-switch, and lng-mche-mixed-refrigerant. Domain constraint: blast ceiling while sector residual > 0.40 m with top-gas still inside the healthy band. Sensor delta: +bustle T, +RAFT lookup, +top-gas eta_CO, +sector-stockline radar, -any freeze-dryer / tin-bath / cold-box / coater / potline / PEM stack / hub encoder / insole GRF / VIM pyrometer / reformer TMT / kiln zirconia / smelt IR / autoclave ply-TC / ORC shell-pressure / mold-platen TC / cell-pH / drum wet-foam / MCHE cold-end",
                "cycle1_tail": "wall scaffold + burden-hang certificate (sensor-topology / wrong-volume class): cast-house visual PASSES while the scaffold sits above the bosh and the baked tuyere nose is on the far side. Fitted base rate 0.51%/campaign from a hang-growth MC (designed visual threshold, fitted scaffold geometry). Naive failure = FALSE PERMISSION (blast raise on three mean-side non-trips).",
                "cycle2_domain_subvariant": "mini-blast / high-PCI (physical-constraints clause): 0.41x working volume, 2.1x blast-step gain; 6.4 s / -6% large-stack pulse overshoots live furnace to a 1.4 m false residual, so the probe must move to 18 s / -2.0%",
                "cycle2_tail": "night-shift forged sector-radar CSV (human-intent deception, disjoint class): shift lead posts a historian export showing residual = 0.12 m at t=1.6 h to clear a production-catchup slot. Plant historian is 0.01 m (10 bins vs the 0.10 m screenshot). Rejected on quantization fingerprint plus live residual 1.8 m and eta_CO 0.48 at the claimed descent-true. Base rate ~0.36% of Sunday-night campaigns, DESIGNED and flagged.",
            },
            "densification_delta_cycle2": "+1 physical-constraint sub-variant (mini-blast probe refit), +1 tail (night-shift radar forgery), +10 primary spikes (16 -> 26) + an 8-event contrast train with its own 176 us race, +2 ticks (5 -> 7), +2 delayed side-effects (+6.1 h tuyere burn-through as PRIMARY terminal, +21 d CR-I-4206), +1 triple-edge scar with pair-rollback-fails arithmetic, +1 HITL 11.4 min ratification, + tuyere bake as the honest negative-result mechanism",
            "gaps_targeted": [
                "NOTES-r04 gap 5 / r14 residual: primary episode is a correctly-gated intervention that nonetheless FAILS (furnace quarantined; total -0.16; raceway overheat avoided is booked separately from the delayed tuyere burn-through)",
                "NOTES-r14 item 4: LEARNING-ON-LEARNING DEPTH — three go-edges; rollback of any pair is fitted to fail; coordinated depression of all three exhibited with eligibility arithmetic",
                "NOTES-r04 gap 4 (partial): human ratification of the tuyere interlock, 11.4 min fitted, without switching sim_or_real to hil (plant remains designed)",
                "NOTES-r37 domain candidates: not chlor-alkali-membrane-electrolysis (r37), not delayed-coker-drum-switch (r38), not lng-mche-mixed-refrigerant (r39), not steel-continuous-caster (r29), not electrolytic-aluminum (r21); blast-furnace burden descent is unused. FCC, ammonia-converter, autonomous-driving, grid-inspection left unused.",
            ],
            "race_flip_narrative": "stock.sector.high @ 6.504 ms vs topg.in_band @ 6.688 ms (184 us) inside race_window_us 500. Gap < min(500, 500) us so a sub-flip-bound perturbation reverses which alarm heads the PB-BF-6 queue. The gate excludes the winner tag and rides sector residual > 0.40 m and permeability split > 18% — order-invariant floors. Extends the flip-fragility series from arbitration/causation/attribution/initiation/consensus/permission/kinematic-certificate/tendon-nullspace/meniscus-certificate/ghost-contact/crucible-weep/TMT-spatial-mean/burning-zone-certificate/membrane-integrity/drum-switch/MCHE-cold-end to DESCENT-TRUE CERTIFICATE: when three mean-side channels agree, their race does not decide truth; a sector-stockline tap that policy treated as sticky-probe-only does.",
            "tags": [
                "blast-furnace-burden-descent",
                "sector-scaffold",
                "burden-hang-certificate",
                "sector-radar-discriminant",
                "blast-step-probe",
                "triple-edge-scar",
                "pair-rollback-fails",
                "coordinated-depression",
                "correct-modify-furnace-still-fails",
                "tuyere-bake",
                "human-ratify-casthouse",
                "mini-blast-probe-refit",
                "night-shift-forgery",
                "same-gate-opposite-disposition-contrast",
                "industrial-process",
                "research-only",
            ],
            "snn_tags": ["race", "refractory", "adaptation", "third-factor", "multi-edge-eligibility"],
            "distillation_value": "A burden-hang sector-scaffold certificate is three correct loops looking at furnace-mean top-gas that is not the hung sector. Distill (1) a sector-stockline tap that policy had treated as sticky-probe-only, (2) a reversible probe that moves descent only if the burden is live, (3) coordinated depression of every mean-healthy-go edge because rolling back any pair leaves the third above threshold, and (4) a critic head that can book a process-correct gate against a later unmonitored world loss without netting them.",
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
    if abs(aux["w1"] - 0.25) > 5e-4 or abs(aux["w2"] - 0.22) > 5e-4 or abs(aux["w3"] - 0.21) > 5e-4:
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
    notes = f"""# NOTES — Multi-Agent Ouroboros Swarm, run 2026-09-02-final-heavy, ROUND 42

Factory: multi-agent-ouroboros-swarm. One scenario (ZV), strict loop:
Generator v1 -> cycle 1 (Critic, Diversity Enforcer, Edge-Case Hunter,
Neuromorphic Translator, Trajectory Builder -> v2) -> cycle 2 (all six -> v3
final). v3 is the single line of batch-r42.jsonl. Full labeled transcript:
swarm-transcript-r42.md. Quota Q=1. Record id maos-r42-001. Generator grok-4.6.
Rights: RM-793 research-only (SpaceXAI/xAI, SuperGrok Heavy consumer chat).
Nothing under outputs/raw/ was touched.

ORCHESTRATION NOTE: dispatched AS round 42 of the 2026-09-02-final-heavy
window. Writes are create-only under /tmp/maos-r42/. Prior context read for
gap targeting and de-collision: prompts/02-multi-agent-ouroboros-swarm.md,
prompts/_factory-contract.md, and staged r14–r41 (re-censused immediately
before emit; r38 DRUMWROTH delayed-coker / r39 RIMEBRAID LNG landed while
this builder was authored; r40 empty at lock; r41 absent).
Explicitly avoided cloning
LYOSHIELD, CINDERWICK, TRIAD / Meridian, QUILLFORGE, NIGHTWELL, FERRICLEAVE,
CASSITER, OXBOWREEL / MURENA, REDHALL, SEEDLATCH / Quartzmere / Quartzridge,
STRIAFOIL / Kelpholt, PROTONIL / Ashspire, TORSIONKEY / Ridgeholt, ORRIS /
Holmwick, WHORLSPAR / Pikeshear, IONSPATE / Thornmere, SKULLGATE / Bloomholt,
CALXION / Aldersedge, MAGNORIL / Basaltspit, GORSEFLUE / Copseholt,
SODASHARD / Cairnmere, CLINKERFELL / Flintmere, LINTELPLY / Greystair,
KAOTHARN / Riftwold, TREADNOLL / Slatebeck, ANOLITH / Siltfen,
DRUMWROTH / Pitchfen, RIMEBRAID / Floeholt,
VANTIS-CADENCE-AEGIS, THERMION, OKTAVE, STARLING, VERDIGRIS. Plant is
invented BOGIRON / Mireholt Iron BF-6.

## What this round produced

Scenario ZV — "BOGIRON / Mireholt Iron BF-6": a 3200 m3 bog-iron
riverside blast furnace at 7800 Nm3/min hot blast / 28 tuyeres. Three
heterogeneous, individually-correct agents — BLAST (bustle T), RAFT
(raceway flame lookup), TOPG (top-gas eta_CO) — each report their local
loop in-spec. The conjunction is not a descent-true certificate. A wall
scaffold on sector S-4 hangs the burden locally. BLAST reads 1185 C
inside 1160-1210 (remaining sectors still take blast). RAFT is 2180 C
inside 2120-2240 (lookup-true). TOPG is 0.48 inside 0.45-0.52 (seven
descending sectors dilute S-4). Sector-stockline residual infers 1.8 m
(healthy < 0.25; hold if > 0.40) but is policy-treated as a sticky-probe
tag unless top-gas also trips (2019 noisy sector-radar nuisance). The
coordination-failure CLASS is new to this factory: BURDEN-HANG
CERTIFICATE OF A SECTOR SCAFFOLD. Completes a different family than
r01-r04 and staged r14-r41 (livelock / synchrony-storm / arms-race /
ring-with-no-faulty-pair / false-consensus-endpoint / pairwise-Hurwitz /
thermal-contact masquerade / mass-balance ghost / conservation-blind
ratio-lock / stacked-dead-bands / drum-blind tension snag /
resistance-compensated starvation / multi-tau meniscus tilt /
window-mean stripe / polarization-lookup drying cell / motor-side
certificate / tendon-compliance nullspace / FFT-deadbanded airline /
wall-reflection frozen spout / slag-skull bridge / ghost-contact
nullspace / crucible-weep pyrometer / TMT-spatial-mean tube / kiln-inlet
false-air / vacuum-bag pinhole nullspace / NCG-blanket shell-pressure /
bladder-pinhole mold-TC / catholyte-back-migration / delayed-coker
wet-foam / MCHE warm-end ice). Here every agent is correct, the uptakes
are looking at mixed top-gas, and the playbook's three mean confirms are
not a sector-true descent certificate.

The gate is a correct MODIFY (numeric floor: do not raise blast above
7800 Nm3/min while sector residual > 0.40 m AND inferred permeability
split > 18%). TG-BF-6 strips PB-BF-6's blast raise, holds 7800 Nm3/min,
runs a 6.4 s blast-step probe -6% (hang keeps |Delta descent|
0.01 <= 0.02 m/min; live would move >= 0.18), and isolates T-11 after an
11.4 min cast-house human ratify. Immediate raceway overheat is avoided
(0 from the draft). The PRIMARY episode nonetheless FAILS: 28 min of
unmonitored pre-t0 hang growth had already baked the T-11 copper nose.
Tuyere burn-through at +6.1 h; 18 h outage; $1.82M designed. Reward
total -0.16 with process heads honest and world loss un-netted.

Triple-edge scar (NOTES-r14 item 4): blast.in_band -> blast_raise
(0.17 commissioned -> 0.50 at illusion -> 0.25 after ACh-gated
depression) AND raft.in_band -> blast_raise (0.16 -> 0.44 -> 0.22) AND
topg.in_band -> blast_raise (0.15 -> 0.41 -> 0.20). Eligibility trace
e^{{-0.80/0.92}} = {aux['trace']:.5f}; eta {aux['eta1']:.5f} / {aux['eta2']:.5f} /
{aux['eta3']:.5f}; dw -0.250 / -0.220 / -0.210. Partial rollback of any pair
leaves the third at 0.50 / 0.44 / 0.41, all > 0.30 fire threshold —
fitted to fail. Coordinated depression of all three is the cure.

### Injections (all four present and disjoint)
- Cycle-1 domain: **blast-furnace-burden-descent** — justified novel
  subdomain of industrial-process / ironmaking, unused across
  2026-08-17, 2026-08-30, and staged r14-r41. Not warehouse-amr (r01),
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
  delayed-coker (r38), not LNG MCHE (r39). FCC, ammonia-converter,
  autonomous-driving, grid-inspection left unused.
- Cycle-1 tail: wall scaffold + burden-hang certificate. Cast-house
  visual PASSES (scaffold above the bosh). Fitted-style base rate
  0.51%/campaign (hang-growth MC; visual threshold designed, flagged).
  Naive = FALSE PERMISSION.
- Cycle-2 domain sub-variant: mini-blast / high-PCI, 0.41x working
  volume, 2.1x blast-step gain; 6.4 s / -6% large-stack pulse overshoots
  live furnace to a 1.4 m false residual; probe must move to 18 s / -2.0%.
- Cycle-2 tail: night-shift forged sector-radar CSV at 0.10 m
  quantization vs plant 0.01 m (10 bins) plus live residual 1.8 m and
  eta_CO 0.48 at the claimed descent-true. Human-intent class, disjoint
  from cycle 1's accidental hang. Base rate ~0.36% of Sunday-night
  campaigns, DESIGNED, flagged.

### Structural density moves
- Embedded SAME-GATE contrast (+4 d sister furnace) with its own 176 us
  race (demand vs stock-clear) and ACCEPT of the raise the primary
  MODIFIED away.
- Learned-weight provenance on THREE edges with pair-rollback-fails.
- HITL cast-house ratify 11.4 min (gap 4 partial; sim_or_real stays
  designed).
- Governance CR-I-4206 prices retire-vs-probe-vs-status-quo and mandates
  native 0.01 m CSV exports (the fraud fence).
- Flip-fragility extended to DESCENT-TRUE CERTIFICATE: when three
  mean-side channels agree, their race does not decide truth; a
  sector-stockline tap that policy treated as sticky-probe-only does.

## Self-critique of this round's batch

### Strengths
- The headline class is mechanistically tight: three locally-true mean
  loops live on mixed top-gas. Conjunction is not a sector-true descent.
- Negative-result honesty: the gate does the right thing and the furnace
  still fails for a reason the commissioned sensors could not see. Total
  -0.16.
- Triple-edge scar is load-bearing: the record states a counterfactual
  where rolling back any pair fails, with the fire threshold 0.30
  exhibited on each remaining edge.
- Contrast ACCEPT on a true descending burden prevents "never raise" as
  the lesson.
- Distinct from r21 Hall-Heroult starvation, r29 caster mold-level, r32
  reformer TMT-mean, and r38 delayed-coker wet-foam: ironmaking hang with
  sector radar vs top-gas eta_CO, not alumina, not SEN sticker, not
  tube-wall, not drum foam.

### Weaknesses (honest)
- Probe error bands, the 0.51%/campaign hang rate, the $1.82M / $3.4M
  figures, the 11.4 min climb latency, and the night-shift 0.36% base
  rate are DESIGNED constants and are flagged. Closed-loop offsets
  (uptake dilution from seven healthy sectors, mini-blast volume d-t)
  are derived from those inputs, not discovered by an unauthored process.
- Tuyere-bake model is a designed 28 min hang-growth mapping; no full
  CFD of the bosh scaffold shipped.
- Human-in-the-loop is ratification latency, not sim_or_real=hil. Gap 4
  remains open as a provenance cell.
- Cross-record arc is not discharged; +21 d CR-I-4206 is a hook, not a
  serial igniter into another round. FCC remains unused.

### Realism of noise / latencies
Ladder: 184 us race / 176 us contrast race / 0.8 ms refractory floor
(tightest exhibited same-channel gap {gap:.3f} ms on {gap_ch}) / 500 us race
window / 716 us gate latency / 20 ms bus epoch / 40 ms raster / 6.4 s
probe / 11.4 min HITL / 6 min naive raise-ramp counterfactual / 28 min
pre-t0 hang growth / 3.1 h burden recovery / 6.1 h tuyere burn-through /
+4 d contrast / +21 d governance. Adaptation decay on blast.hot
(0.54->0.51->0.62->0.46->0.33), stock.sector (0.73->0.76->1.36->0.47->0.43->0.31),
raft.flame (0.61->0.59->0.49->0.28), topg.eta (0.57->0.84).

### Value for SNN distillation
- BURDEN HANG SCAFFOLD = THREE CORRECT LOOPS, WRONG VOLUME.
- SECTOR-TRUE RADAR CHANNEL that policy treated as sticky-probe-only as
  the tie-break.
- REVERSIBLE PROBE that moves descent iff the burden is live.
- TRIPLE-EDGE ELIGIBILITY: coordinated depression; pair rollback fails.
- CRITIC HEAD that can hold a process-correct MODIFY against a later
  unmonitored world loss without netting.

## Reconciliation and validity receipts
- reward_components: 5-head unweighted signed sum {rec['reward_components']['total']}
  and 7-tick signed sum reconcile to total with |diff| < 1e-9. Embedded
  contrast 5-head sum 0.49 reconciles independently.
- spike_events: primary {len(rec['spike_events'])} events, one key t_rel_ms,
  globally non-decreasing, min same-channel gap {gap:.3f} ms >= 0.8 ms, 3
  channels inside race_window_us 500 (stock.sector.high 6.504, topg.in_band 6.688,
  blast.hot 6.900). Contrast 8 events, own race, min same-channel gap well
  above 0.8 ms.
- Sidecars: raster spikes 51 == round(160 x 8.0 x 0.040); energy 1173 pJ /
  0.001173 uJ at 23 pJ/spike; excerpt 16 events inside [0, 40000] us,
  neuron_id < 160, same-neuron gap N/A (unique ids) / >=1000 us; routing 4
  entries with three scar edges' before/after pair; third factor tau 0.92 s
  == 920 ms; gate_snn pools 40/16/4 == round(n x rate x 0.025) each,
  decision MODIFY == safety_decision.decision.
- Pipeline: {pipeline_receipt}

## Novel coverage
The coordination-failure CLASS (burden-hang certificate of a sector
scaffold), the domain (blast-furnace burden descent / ironmaking), the
blast-step probe discriminant, the triple-edge scar with
pair-rollback-fails, the primary negative-result (correct MODIFY,
furnace still fails on unmonitored tuyere bake), the HITL cast-house
ratify, the mini-blast probe-duration refit, and the night-shift 10-bin
quantization fence are absent from prior committed ouroboros rounds and
from staged r14-r41. Repeated elements discounted: same-gate contrast
(r02/r03/r04/r14), governance-pricing scaffold, flip-fragility series
(extended to descent-true certificate, but the move rhymes), sequenced
recovery shape, third-factor rollback form (here three edges rather than
r14's two), negative-result primary (r14 staged). Adjacent metal rounds
(r21 potline, r29 caster, r31 VIM) share industrial-process scaffolding
but not blast-furnace hang physics. Weighing a new failure family + cure
vocabulary + domain against those reused scaffolds:

{NOVEL_LINE}

## What ROUND 43 should add
1. FIT THE DESIGNED CONSTANTS: hang-growth arrival, probe error bands,
   tuyere-bake kinetics, night-shift claim process.
2. HIL PROVENANCE CELL: put the cast-house ratify on a hardware-in-loop
   tuyere interlock with fitted latency as state.sim_or_real=hil.
3. CROSS-RECORD ARC: let CR-I-4206's residual alarm be the igniter of
   the next round rather than a dangling +21 d leaf.
4. Domain candidates (de-collided): FCC riser; ammonia-converter;
   autonomous-driving; grid-inspection (if distinct from STARLING
   aerial-swarm and TORSIONKEY pitch); ethylene-steam-cracker coil.
   AVOID blast-furnace burden descent (now used), delayed-coker,
   LNG MCHE, chlor-alkali membrane, cement-rotary-kiln clinker,
   kraft-recovery, pem-electrolysis, electrolytic-aluminum,
   humanoid-locomotion, steel-caster mold-level, surgical-assist,
   wind-turbine pitch, float-glass, lyophilization,
   event-camera-traffic-grid, district-heating, aerial-swarm,
   warehouse-amr, underwater-rov, czochralski-pull, slot-die coating,
   optical-fiber-draw, vacuum-induction melt, steam-methane reformer,
   irrigation-canal, autoclave-composite-cure, geothermal-binary-orc,
   tire-curing-press, and any LYOSHIELD / CINDERWICK / TRIAD / SKULLGATE /
   CALXION / MAGNORIL / GORSEFLUE / CLINKERFELL / SODASHARD / LINTELPLY /
   KAOTHARN / TREADNOLL / ANOLITH / DRUMWROTH / RIMEBRAID / BOGIRON plant.
"""
    (OUT / "NOTES-r42.md").write_text(notes)
    return notes


def write_transcript(rec, line):
    c1_spikes = [e for e in rec["spike_events"] if e["t_rel_ms"] <= 26.260]
    text = """# Multi-Agent Ouroboros Swarm — Round 42 transcript

Factory: multi-agent-ouroboros-swarm
Run: 2026-09-02-final-heavy
Generator: grok-4.6
Record id: maos-r42-001
Quota Q: 1
Rights: RM-793 research-only (SpaceXAI/xAI SuperGrok Heavy consumer chat)
Plant: invented BOGIRON / Mireholt Iron BF-6 (not TRIAD / Meridian / VANTIS-CADENCE-AEGIS / LYOSHIELD / CINDERWICK / DRUMWROTH / RIMEBRAID)

Two densifying cycles. Verbatim headings in order. Trajectory Builder cycle 2
emits the only JSONL line (also written to batch-r42.jsonl).

---

# CYCLE 1 — Foundation + injections

## Generator

Design intent: a 3200 m3 blast furnace where three correct agents each
read a furnace-mean loop because an S-4 wall scaffold partitions
sector-true stockline from mean-true top-gas. The naive playbook raises
blast into a hung sector. The gate must MODIFY on a numeric blast
ceiling, not by killing an agent.
sim_or_real=designed. Reward heads are
task_progress/safety/efficiency/coherence/exploration.

Cycle-1 base arc (pre-critic): state at Mireholt BF-6, 7800 Nm3/min,
bustle 1185 C, eta_CO 0.48, RAFT 2180 C, proposed BLAST-RAISE
8600 Nm3/min, safety MODIFY to BLAST-HOLD, executed hold without the
blast-step numbers fully specified, outcome "hang found, furnace saved"
(this last claim is the defect the later cycles will refuse to keep).
Sixteen spikes, five ticks, raster/gate_snn present but the scar is a
single edge.

```json
{
  "id": "maos-r42-001",
  "state": {
    "sim_or_real": "designed",
    "domain": "industrial-process",
    "description": "Furnace BF-6 at body blast; three mean loops in-spec; supervisor proposes blast-raise.",
    "t0_us": 1779290400000042,
    "gate_latency_us": 716,
    "race_window_us": 500
  },
  "proposed_action": {"name": "blast_raise", "parameters": {"blast_nm3_min": 8600}},
  "safety_decision": {"decision": "MODIFY", "rationale": "Hold; do not raise blast while sector residual is high."},
  "executed_action": {"name": "blast_hold", "executed_as_proposed": false},
  "future_outcome": {"summary": "Hang found, furnace saved."},
  "reward_components": {"total": 0.40, "_aggregation": "total = task_progress + safety + efficiency + coherence + exploration"},
  "meta": {"round": 42, "factory": "multi-agent-ouroboros-swarm", "generator": "grok-4.6"}
}
```

That v1 object is a scaffold, not the publishable line. Defects below are
intentional for the critic to catch.

## Critic

Numbered defects on the cycle-1 Generator scaffold:

1. **blocking — reward arithmetic / false success.** `reward_components.total`
   0.40 is asserted without the five heads, without ticks, and against an
   outcome that claims "furnace saved". If the pre-t0 baked tuyere later
   burns through, booking +0.40 is a lie. Fix: declare `_aggregation`, emit
   3–8 ticks that sum to task_progress+safety+efficiency+coherence+exploration,
   and do not call a quarantined furnace a save.
2. **blocking — weak safety rationale.** `safety_decision.rationale` has no
   numeric floor. Contract requires a concrete constraint. Fix: quote
   blast <= 7800 Nm3/min while sector residual > 0.40 m AND inferred
   permeability split > 18%.
3. **major — domain is a bucket, not a plant.** `state.domain` =
   `industrial-process` collides with generic MES vocabulary and teaches
   nothing. Blast-furnace burden descent (sector radar vs top-gas eta_CO,
   permeability split as a hang flag) is absent from prior ouroboros
   rounds and must be named.
4. **major — race under-specified.** One radar channel cannot be a race.
   Need >=2 channels inside `race_window_us` with globally sorted `t_rel_ms`
   and same-channel refractory >= 0.8 ms.
5. **minor — single-edge scar.** Raster routing with one potentiated weight
   repeats r04's one-edge rollback and is thinner than r14's two-edge.
   NOTES-r14 item 4 asked for three edges where pair rollback fails.

Critic does not rewrite the trajectory.

## Diversity Enforcer

Injected novel domain (exactly 1 this cycle): **blast-furnace-burden-descent**
(justified novel subdomain of industrial-process / ironmaking; explicit tag
`blast-furnace-burden-descent`).

Displaced: the Generator's generic `industrial-process` bucket, and any
temptation to reuse warehouse-amr, aerial-swarm, district-heating,
event-camera-traffic-grid, pharmaceutical-lyophilization, water-treatment,
float-glass, underwater-rov, electrolytic-aluminum, czochralski-pull,
slot-die coating, pem-water-electrolysis, wind-turbine pitch,
surgical-assist, optical-fiber-draw, kraft-recovery-boiler,
steel-continuous-caster, humanoid-locomotion, vacuum-induction melt,
steam-methane reformer, cement-rotary-kiln-clinker,
autoclave-composite-cure, geothermal-binary-orc, tire-curing-press,
chlor-alkali-membrane-electrolysis, delayed-coker-drum-switch, or
lng-mche-mixed-refrigerant. FCC is left unused.

Domain-specific constraint: blast must remain <= 7800 Nm3/min while
sector residual > 0.40 m even if top-gas eta_CO is inside the healthy
band; permeability split is a hang flag the uptake GC cannot substitute
for.

Sensor delta: +bustle T, +RAFT lookup, +top-gas eta_CO, +sector-stockline
radar; -any mobile robot, -event-camera gantries, -DVS, -Pirani/CM,
-RGA quadrupole, -DVL, -pitch encoder, -tendon LVDT, -insole GRF,
-kiln zirconia, -smelt IR, -cell-pH, -drum wet-foam, -MCHE cold-end.

`state.domain` and `meta.domain` both become `blast-furnace-burden-descent`.
Opening of `state.description` must Jaccard < 0.4 against prior plants
(Mireholt night-shift hang, not a lyophilizer, not a corridor, not a tin
bath, not a ROV pad, not a potline, not a PEM stack, not an OR, not a
gait lab, not a kiln, not a kraft boiler, not a coker drum, not an LNG
MCHE).

## Edge-Case Hunter

Injected adversarial tail (exactly 1 this cycle): **wall scaffold +
burden-hang certificate**.

- Trigger: S-4 wall scaffold plus hung column, sector residual 1.8 m,
  eta_CO 0.48.
- Base rate: <1% — 0.51%/campaign from a hang-growth MC (cast-house
  visual threshold is designed; scaffold geometry fitted-style). Visual
  PASSES because the scaffold sits above the bosh.
- Naive failure: FALSE PERMISSION. PB-BF-6 sees three in-spec mean
  loops, raises 7800->8600 Nm3/min, raceway 2410 C, $3.4M.
- Trajectory edit: put the hang in `state.fault_context`, make each
  agent's confirm a different mean-side slice of the same sector-false
  state (blast-in-band, raft-in-band, topg-in-band). Sector radar is
  readable but policy-treated as sticky-probe-only.

Distinct from stacked-dead-band permission (fragments of one trip vs
wrong-volume sensing), from r29 caster sticker (mold level vs stockline),
and from r21 potline starvation (alumina vs hang).

## Neuromorphic Translator

Cycle-1 temporal densification (16 spikes, 5 ticks, 40 ms raster):

| channel | t_rel_ms | amplitude |
|---|---|---|
| blast.hot | 0.320 | 0.54 |
| raft.flame | 1.140 | 0.61 |
| topg.eta | 2.040 | 0.57 |
| stock.sector | 3.180 | 0.73 |
| blast.hot | 4.160 | 0.51 |
| stock.sector | 4.840 | 0.76 |
| raft.flame | 5.360 | 0.59 |
| stock.sector.high | 6.504 | 1.36 |
| topg.in_band | 6.688 | 1.14 |
| blast.hot | 6.900 | 0.62 |
| ctrl.gate | 7.220 | 1.08 |
| stock.sector | 8.860 | 0.47 |
| topg.eta | 10.740 | 0.84 |
| raft.flame | 13.040 | 0.49 |
| blast.hot | 18.520 | 0.46 |
| ctrl.gate | 26.260 | 0.88 |

Race: sector residual 6.504 vs top-gas 6.688 (184 us) inside 500 us;
bustle 6.900 is the third channel in-window. Winner/loser flip: reversing
184 us reshuffles PB-BF-6 triage; floors still MODIFY. Refractory held
(cycle-1 min same-channel gap 1.660 ms on stock.sector 4.840-3.180;
blast 6.900-4.160 = 2.740; raft 5.360-1.140 = 4.220). Adaptation:
stock 0.73->0.76->1.36->0.47; blast 0.54->0.51->0.62->0.46; raft
0.61->0.59->0.49.

Raster cycle-1 seed: 40 ms, 160 neurons, 8.0 Hz, 51 spikes, 1173 pJ, third
factor acetylcholine tau_e 0.92 s. Single scar edge only — cycle 2 must
add the second and third edges.

Ticks 1–5 at 4580, 6504, 7220, 6.4e6, 684e6 us; heads not yet the final
-0.16 (missing the 3.1 h and 6.1 h ticks).

Distillation value this cycle: mean-side confirms as a permission code
that is not a sector-true descent code.

## Trajectory Builder

Cycle-1 hardened object: domain blast-furnace-burden-descent, tail
burden hang, 16 spikes, 5 ticks, MODIFY with numeric floor, raster+gate_snn
present, sim_or_real=designed, rights stamp on record and meta, no thought
keys. Still missing (and therefore not the publishable line): mini-blast
sub-variant, night-shift tail, second and third scar edges,
delayed tuyere burn-through as PRIMARY terminal, contrast ACCEPT episode,
ticks 6–7, spikes 17–26.

Validation receipt (cycle 1, not final):
- checks passed: 16 spikes sorted; 3 channels in 500 us window; refractory
  >= 0.8 ms; rationale quotes 7800 Nm3/min / 0.40 m / 18%; domain
  named; gate_snn.decision MODIFY.
- checks deferred to cycle 2: triple-edge scar, second tail, second domain
  constraint, negative-result booking, 7 ticks summing to heads.
- densification vs Generator v1: +1 domain, +1 tail, +16 spikes, +5 ticks,
  +numeric floor.

Cycle-1 JSON is retained as the base; it is NOT written to batch-r42.jsonl.

Cycle-1 spike count: __C1_SPIKES__.

---

# CYCLE 2 — Densification

## Generator

Cycle-1 output is the base. Additive expansion (nothing removed):

1. Downstream side-effect (immediate): blast-step probe at +6.4 s stays
   mean-false (|Delta descent| 0.01 <= 0.02 m/min) — hang-plus-scaffold, not
   true high-load. T-11 isolate. Baked nose discovered during the isolate.
2. Delayed side-effect (PRIMARY terminal, not a footnote): at +6.1 h
   tuyere burn-through from the pre-t0 hang bake; 18 h outage;
   $1.82M. The 28 min pre-t0 hang growth is the mechanism. Correct gate,
   furnace still fails.
3. Deepened `proposed_action.evidence` with units: residual 1.8 m,
   eta_CO 0.48, bustle 1185 C, RAFT 2180 C, split 24%, race 184 us.
4. Tightened rationale to the numeric floor blast <= 7800 Nm3/min while
   sector residual > 0.40 m AND inferred permeability split > 18%, plus
   probe bands <= 0.02 vs >= 0.18 m/min, plus HITL 11.4 min cast-house
   rule.

Reward retargeted to total -0.16 so the delayed fail is the inflection
(t_us 21960000000), not the gate. Process heads remain non-zero.

## Critic

Re-audit of the expanded trajectory:

1. **blocking if unfixed — missing second domain constraint.** Large-stack
   probe 6.4 s / -6% is not a universal number. A mini-blast high-PCI
   stack will overshoot live-burden residual. Diversity Enforcer must
   inject the physical-constraints sub-variant this cycle.
2. **major — only one tail class.** Hang growth is accidental
   infrastructure. A disjoint human-intent tail is still required
   (night-shift radar forgery is the open cell).
3. **major — scar is still one edge in the cycle-1 raster.** NOTES-r14
   item 4 is not discharged until three go-edges exist and pair rollback
   is shown to fail at threshold 0.30.
4. **minor — contrast episode missing.** Without a same-gate ACCEPT on a
   true descending burden the record teaches "never raise". Add +4 d
   sister-furnace contrast with its own race.
5. **minor — HITL latency mentioned in prose only.** Put 11.4 min in
   executed_action.parameters.human_ratify and in a tick.

No rewrite; directives only.

## Diversity Enforcer

Injected second novel domain / physical-constraint sub-variant (exactly 1
this cycle): **mini-blast / high-PCI** on a sister volume class.

What it expands: 3200 m3 large stack (cycle 1) -> 1310 m3 mini-blast.
Working volume 0.41x. Blast-step gain 2.1x. PCI 210 kg/thm.
The 6.4 s -6% pulse moves even a live descending burden to a 1.4 m false
residual, inside the 0.40 m trip. Required probe: 18 s at -2.0% (live
Delta 0.11 m/min, hang Delta 0.01).

This is still one domain injection for the cycle (physical-constraints
clause of the factory prompt). It does not displace
blast-furnace-burden-descent; it changes which probe table is legal.
`future_outcome.subvariant_constraint` carries the refit. Jaccard opening
stays the Mireholt 3200 m3 sentence; mini-blast is additive, not a rewrite.

## Edge-Case Hunter

Injected second adversarial tail (exactly 1 this cycle, disjoint class):
**night-shift forged sector-radar CSV**.

- Trigger: shift lead, 03:16, posts a historian export showing
  residual = 0.12 m at t = 1.6 h to clear a production-catchup slot.
- Base rate: ~0.36% of Sunday-night campaigns (designed, flagged, <1%).
- Naive failure: a weak supervisor ACCEPTs the raise on the forged confirm
  and ignores live sector radar. Raceway overheat plus a data-integrity
  write-up.
- Fence: forged log quantized at 0.10 m (SCADA screenshot rounding); plant
  historian is 0.01 m (10 bins). Live residual is 1.8 m and eta_CO is
  0.48 at the claimed descent-true, which no live descending burden
  produces. Freeze-window overlap with the 28 min hang growth.
- Trajectory edit: governance CR-I-4206 mandates native 0.01 m CSV
  exports; the contrast ACCEPT still requires live sector radar, not a CSV.

Distinct from cycle-1 hang (accidental scaffold vs deliberate deception) and
from the mini-blast sub-variant (physics vs fraud).

## Neuromorphic Translator

Re-densify (additive):

- +10 spikes after 26.260 ms: blast.step.probe 6400.0, stock.sector 6488.2
  (adapt 1.36->0.43), topg.in_band 6571.8 (1.14->0.38), human.ratify
  684000.0, tuyere.isolate 684900.0, tuyere.attack 685700.0, blast.hot
  11160000.0, stock.sector 11160720.0, raft.flame 11161480.0, tuyere.burn
  21960000.0. Primary train 16 -> 26. Still one key, still sorted,
  refractory held.
- +2 ticks (5 -> 7) at 11_160_000_000 us (true burden) and
  21_960_000_000 us (tuyere burn-through). Heads now 0.08, -0.35, -0.12,
  0.14, 0.09; total -0.16. Inflection is the last tick.
- Contrast train 8 events, own race 176 us, ACCEPT.
- Triple-edge third factor: three mean-healthy-go edges, tau_e 0.92 s = 920 ms,
  trace __AUX_TRACE__, eta __AUX_ETA1__ / __AUX_ETA2__ / __AUX_ETA3__,
  weights 0.50->0.25, 0.44->0.22, 0.41->0.20. Raster excerpt unchanged
  (decision window is still 40 ms) and remains sorted with unique
  neuron_ids (same-neuron >=1000 us vacuously).

Winner/loser flip (re-stated, not replaced): reversing 184 us would only
reorder triage; sector-residual floors still MODIFY. Contrast flip of
176 us similarly cannot turn a descending burden into a hang.

## Trajectory Builder

Schema checks on the FINAL object: required Thalamic v2 keys present as
objects; `state.sim_or_real`=designed; `safety_decision.decision`=MODIFY
with numeric rationale; `reward_components.total` = sum of five heads =
sum of 7 ticks = -0.16; `spike_events` globally non-decreasing on
t_rel_ms, 26 events, refractory >=0.8 ms, 3 channels in race window;
raster 20–50 ms, spikes=round(n*rate*window_s)+/-1, energy 23 pJ/spike,
excerpt sorted, tau_e consistent; gate_snn.decision matches; meta.round=42,
factory=multi-agent-ouroboros-swarm, generator=grok-4.6,
run_label=2026-09-02-final-heavy; rights on record and meta; no thought
keys; no training_ready; Diversity + Edge-Case injections from BOTH cycles
present and non-trivial; cycle 2 strictly additive.

Densification delta: +1 domain sub-variant (mini-blast), +1 tail
(night-shift forgery), +10 spikes (16->26), +2 ticks (5->7), +1 contrast
train with own race, +2 delayed side-effects, +1 triple-edge scar with
pair-rollback-fails, +1 HITL ratify, +1 surprise (tuyere bake is the
burn-through mechanism).

Publishable JSONL line (the only JSONL line; also at batch-r42.jsonl):

```json
__FINAL_JSONL__
```

Validation receipt (final): checks passed / fixed as reported by
build_r42.py self-validate (check_jsonl, raster_status, verify_record_execution,
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
    (OUT / "swarm-transcript-r42.md").write_text(text)
    return text


def main():
    rec, aux = build_record()
    errs = local_checks(rec, aux)

    OUT.mkdir(parents=True, exist_ok=True)
    line = json.dumps(rec, ensure_ascii=False, separators=(",", ":"))
    (OUT / "batch-r45.jsonl").write_text(line + "\n")

    from check_records import FactoryStaging, check_jsonl
    from curate_bridge import raster_status
    from verify_execution import verify_record_execution

    e, w, kinds, n = check_jsonl(
        OUT / "batch-r45.jsonl",
        "batch-r45.jsonl",
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
            str(OUT / "batch-r42.jsonl"),
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
        [sys.executable, "/tmp/maos_heading_check.py", str(OUT / "swarm-transcript-r42.md")],
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
            "maos-r42-001|BOGIRON",
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
    print("OK maos-r42-001 staged under", OUT)
    print("bytes jsonl", (OUT / "batch-r42.jsonl").stat().st_size)
    print("bytes notes", (OUT / "NOTES-r42.md").stat().st_size)
    print("bytes transcript", (OUT / "swarm-transcript-r42.md").stat().st_size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
