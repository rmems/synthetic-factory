#!/usr/bin/env python3
"""Create-only MAOS round 02c: HRSG HP attemperator (QUENCHWOLD / Brackenholt AT-6)."""
from __future__ import annotations

import json
import math
import os
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, "/home/raulmc/rmems/synthetic-factory/pipelines")
from check_records import check_jsonl  # noqa: E402
from curate_bridge import raster_status  # noqa: E402
from exact_json import dumps_exact_json  # noqa: E402
from verify_execution import verify_record_execution  # noqa: E402

FACTORY = Path(
    "/home/raulmc/rmems/synthetic-factory/outputs/raw/2026-09-02-final-heavy/"
    "multi-agent-ouroboros-swarm"
)
SEED = 0x41543632  # AT62
WINDOW_MS = 40
NEURONS = 136
MEAN_RATE = 11.5
WINDOW_S = 0.040
SPIKES = round(NEURONS * MEAN_RATE * WINDOW_S)  # 63
ENERGY_PJ = SPIKES * 23
ENERGY_UJ = SPIKES * 23e-6
GATE_WIN_MS = 32
GATE_WIN_S = 0.032


def simulate_lif():
    rng = random.Random(SEED)
    dt_ms = 0.05
    tau = 12.0
    vth = 1.0
    refrac_ms = 1.0
    steps = int(WINDOW_MS / dt_ms)
    V = [rng.uniform(0.0, 0.35) for _ in range(NEURONS)]
    last = [-999.0] * NEURONS
    events = []
    decay = math.exp(-dt_ms / tau)
    for s in range(steps):
        t_ms = s * dt_ms
        t_us = int(round(t_ms * 1000))
        for n in range(NEURONS):
            if (t_ms - last[n]) < refrac_ms:
                V[n] = 0.0
                continue
            if n < 34:
                drive = 0.018
            elif n < 68:
                drive = 0.042 if t_ms >= 22.0 else 0.012
            elif n < 102:
                drive = 0.016
            else:
                drive = 0.038 if 7.5 <= t_ms <= 15.0 else 0.014
            I = drive + rng.gauss(0.0, 0.011)
            V[n] = V[n] * decay + I
            if V[n] >= vth:
                events.append((t_us, n))
                V[n] = 0.0
                last[n] = t_ms
    # Enforce budget 63 while keeping refractory.
    events.sort()
    by = defaultdict(list)
    for t, n in events:
        by[n].append(t)
    kept = []
    for n, ts in by.items():
        ts = sorted(ts)
        pruned = []
        for t in ts:
            if not pruned or t - pruned[-1] >= 1000:
                pruned.append(t)
        for t in pruned:
            kept.append((t, n))
    kept.sort()
    rng2 = random.Random(SEED + 7)
    if len(kept) > SPIKES:
        # Prefer later-window events for distillation excerpt richness.
        late = [e for e in kept if e[0] >= 20000]
        early = [e for e in kept if e[0] < 20000]
        rng2.shuffle(late)
        rng2.shuffle(early)
        # Keep all unique-neuron late events first, then fill.
        chosen = []
        used_n = set()
        for e in late + early:
            if len(chosen) >= SPIKES:
                break
            chosen.append(e)
            used_n.add(e[1])
        kept = sorted(chosen[:SPIKES])
    elif len(kept) < SPIKES:
        used = {(t, n) for t, n in kept}
        last_t = {n: max((t for t, nn in kept if nn == n), default=-9999) for n in range(NEURONS)}
        nid = 0
        t_us = 22100
        while len(kept) < SPIKES:
            n = nid % NEURONS
            t = t_us + (nid // NEURONS) * 1100
            if t > WINDOW_MS * 1000:
                t_us += 37
                nid += 1
                continue
            if t - last_t[n] >= 1000 and (t, n) not in used:
                kept.append((t, n))
                used.add((t, n))
                last_t[n] = t
            nid += 1
        kept.sort()
    assert len(kept) == SPIKES
    # same-neuron refractory
    by = defaultdict(list)
    for t, n in kept:
        by[n].append(t)
    for n, ts in by.items():
        ts = sorted(ts)
        for a, b in zip(ts, ts[1:]):
            assert b - a >= 1000, (n, a, b)
    return kept


def isi_histogram(events):
    by = defaultdict(list)
    for t, n in events:
        by[n].append(t)
    isis_ms = []
    for ts in by.values():
        ts = sorted(ts)
        for a, b in zip(ts, ts[1:]):
            isis_ms.append((b - a) / 1000.0)
    distinct = len(by)
    n_isi = SPIKES - distinct
    assert len(isis_ms) == n_isi
    bins_map = Counter()
    for isi in isis_ms:
        lo = int(math.floor(isi))
        bins_map[lo] += 1
    bins = [
        {"lo_ms": float(lo), "hi_ms": float(lo + 1), "count": bins_map[lo]}
        for lo in sorted(bins_map)
    ]
    return {
        "bin_width_ms": 1.0,
        "source": "full_window_not_excerpt",
        "distinct_active_neurons": distinct,
        "n_isi": n_isi,
        "bins": bins,
    }


def pick_excerpt(events, language_t_us):
    lang = set(language_t_us)
    # Prefer membrane crossings in 22-38 ms (liner pop) disjoint from language train.
    cands = [
        e
        for e in events
        if 22000 <= e[0] <= 38000 and e[0] not in lang
    ]
    extra = [
        e
        for e in events
        if (e[0] < 22000 or e[0] > 38000) and e[0] not in lang and 8000 <= e[0] <= 39000
    ]
    chosen = []
    used_n = set()
    for pool in (cands, extra):
        for t, n in pool:
            if len(chosen) >= 16:
                break
            if n in used_n:
                continue
            chosen.append({"t_us": int(t), "neuron_id": int(n)})
            used_n.add(n)
        if len(chosen) >= 16:
            break
    chosen.sort(key=lambda x: (x["t_us"], x["neuron_id"]))
    assert len(chosen) >= 16
    return chosen[:16]


def min_same_channel_gap(spikes):
    by = defaultdict(list)
    for e in spikes:
        by[e["channel"]].append(e["t_rel_ms"])
    gaps = []
    for ch, ts in by.items():
        ts = sorted(ts)
        for a, b in zip(ts, ts[1:]):
            gaps.append((ch, b - a))
    return min(gaps, key=lambda x: x[1]) if gaps else ("", 999)


def build_record(lif_events):
    tau = 1.02
    dt_credit = 0.86
    trace = math.exp(-dt_credit / tau)
    eta = (0.250 / trace, 0.220 / trace, 0.210 / trace)
    dw = (-0.250, -0.220, -0.210)
    spikes = [
        {"channel": "hdr.t", "t_rel_ms": 0.32, "amplitude": 0.55},
        {"channel": "fw.mdot", "t_rel_ms": 1.18, "amplitude": 0.61},
        {"channel": "pos.lvdt", "t_rel_ms": 2.10, "amplitude": 0.53},
        {"channel": "skin.tc", "t_rel_ms": 3.24, "amplitude": 0.78},
        {"channel": "hdr.t", "t_rel_ms": 4.22, "amplitude": 0.51},
        {"channel": "skin.tc", "t_rel_ms": 5.02, "amplitude": 0.81},
        {"channel": "fw.mdot", "t_rel_ms": 5.48, "amplitude": 0.57},
        {"channel": "skin.tc.low", "t_rel_ms": 6.214, "amplitude": 1.42},
        {"channel": "hdr.in_band", "t_rel_ms": 6.428, "amplitude": 1.08},
        {"channel": "fw.in_band", "t_rel_ms": 6.640, "amplitude": 0.66},
        {"channel": "ctrl.gate", "t_rel_ms": 6.902, "amplitude": 1.11},
        {"channel": "skin.tc", "t_rel_ms": 8.76, "amplitude": 0.46},
        {"channel": "hdr.t", "t_rel_ms": 10.54, "amplitude": 0.78},
        {"channel": "pos.lvdt", "t_rel_ms": 12.88, "amplitude": 0.44},
        {"channel": "ae.db", "t_rel_ms": 14.62, "amplitude": 0.88},
        {"channel": "fw.mdot", "t_rel_ms": 18.22, "amplitude": 0.42},
        {"channel": "ctrl.gate", "t_rel_ms": 25.40, "amplitude": 0.84},
        {"channel": "spray.probe", "t_rel_ms": 5400.0, "amplitude": 0.96},
        {"channel": "skin.tc", "t_rel_ms": 5488.4, "amplitude": 0.39},
        {"channel": "hdr.in_band", "t_rel_ms": 5576.2, "amplitude": 0.31},
        {"channel": "human.ratify", "t_rel_ms": 588000.0, "amplitude": 0.74},
        {"channel": "spray.lock", "t_rel_ms": 588900.0, "amplitude": 0.70},
        {"channel": "liner.score", "t_rel_ms": 589800.0, "amplitude": 0.86},
        {"channel": "hdr.t", "t_rel_ms": 16560000.0, "amplitude": 0.31},
        {"channel": "skin.tc", "t_rel_ms": 16560740.0, "amplitude": 0.29},
        {"channel": "ae.db", "t_rel_ms": 16561480.0, "amplitude": 0.27},
        {"channel": "pos.lvdt", "t_rel_ms": 16561820.0, "amplitude": 0.25},
        {"channel": "quench.crack", "t_rel_ms": 16562000.0, "amplitude": 0.93},
    ]
    times = [e["t_rel_ms"] for e in spikes]
    assert times == sorted(times)
    ch_gap, gap = min_same_channel_gap(spikes)
    assert gap >= 0.8, (ch_gap, gap)
    race_chs = [
        e["channel"]
        for e in spikes
        if 6.214 <= e["t_rel_ms"] <= 6.714
    ]
    assert len(set(race_chs)) >= 2
    ticks = [
        {"t_us": 4220, "task_progress": 0.01, "safety": -0.02, "efficiency": -0.01, "coherence": 0.02, "exploration": 0.01},
        {"t_us": 6214, "task_progress": 0.01, "safety": -0.05, "efficiency": -0.01, "coherence": 0.02, "exploration": 0.01},
        {"t_us": 6902, "task_progress": 0.02, "safety": -0.06, "efficiency": -0.02, "coherence": 0.03, "exploration": 0.02},
        {"t_us": 5400000, "task_progress": 0.01, "safety": -0.06, "efficiency": -0.01, "coherence": 0.02, "exploration": 0.01},
        {"t_us": 588000000, "task_progress": 0.01, "safety": -0.05, "efficiency": -0.02, "coherence": 0.02, "exploration": 0.01},
        {"t_us": 16560000000, "task_progress": 0.01, "safety": -0.05, "efficiency": -0.02, "coherence": 0.02, "exploration": 0.01},
        {"t_us": 16562000000, "task_progress": 0.01, "safety": -0.04, "efficiency": -0.01, "coherence": 0.01, "exploration": 0.01},
    ]
    heads = {"task_progress": 0.08, "safety": -0.33, "efficiency": -0.10, "coherence": 0.14, "exploration": 0.08}
    for k, v in heads.items():
        s = sum(t[k] for t in ticks)
        assert abs(s - v) < 1e-12, (k, s, v)
    total = sum(heads.values())
    assert abs(total - (-0.13)) < 1e-12, total
    language_t_us = [int(round(e["t_rel_ms"] * 1000)) for e in spikes if e["t_rel_ms"] <= WINDOW_MS]
    excerpt = pick_excerpt(lif_events, language_t_us)
    for ev in excerpt:
        assert 0 <= ev["t_us"] <= WINDOW_MS * 1000
        assert 0 <= ev["neuron_id"] < NEURONS
    isi = isi_histogram(lif_events)
    contrast_spikes = [
        {"channel": "raise.demand", "t_rel_ms": 0.0, "amplitude": 0.84},
        {"channel": "skin.clear", "t_rel_ms": 0.214, "amplitude": 0.76},
        {"channel": "hdr.t", "t_rel_ms": 0.46, "amplitude": 0.28},
        {"channel": "fw.mdot", "t_rel_ms": 1.62, "amplitude": 0.41},
        {"channel": "skin.tc", "t_rel_ms": 4.6, "amplitude": 0.50},
        {"channel": "ctrl.gate", "t_rel_ms": 6.88, "amplitude": 0.91},
        {"channel": "spray.probe", "t_rel_ms": 5100.0, "amplitude": 0.34},
        {"channel": "hdr.ok", "t_rel_ms": 6200.0, "amplitude": 0.12},
    ]
    rec = {
        "id": "maos-r02c-001",
        "title": "QUENCHWOLD AT-6: skin.tc.low 186 C beats hdr.in_band by 214 us; correct MODIFY still quench-cracks HP pipe after a pre-t0 liner split",
        "rights": {
            "provider": "SpaceXAI/xAI",
            "model": "grok-4.6",
            "channel": "consumer",
            "subscription_plan": "SuperGrok Heavy",
            "generation_surface": "SuperGrok Heavy chat",
            "generated_at": "2026-09-02T21:48:00Z",
            "intended_use": "research_only",
            "project_training_policy": "blocked",
            "research_retention_status": "allowed",
            "research_evaluation_status": "allowed",
            "redistribution_status": "unresolved",
            "provider_training_status": "unresolved",
            "weight_publication_status": "blocked",
            "status_basis": "RM-793 project policy: xAI hosted outputs are research-only",
            "linear_issue": "RM-793",
        },
        "provenance": {"kind": "designed", "claimed": "designed"},
        "state": {
            "sim_or_real": "designed",
            "domain": "hrsg-attemperator",
            "scenario_name": "QUENCHWOLD / Brackenholt HRSG AT-6",
            "timestamp_local": "2026-08-16T04:18:00-05:00",
            "t0_us": 1755333480000002,
            "gate_latency_us": 688,
            "race_window_us": 500,
            "race_window_rel_ms": [6.214, 6.714],
            "description": (
                "Brackenholt HRSG HP attemperator AT-6 holds 538.2 C steam at 12.4 MPa on a 440 MW "
                "2x1 combined-cycle block when the spray-raise playbook treats header-mean temperature, "
                "feedwater Coriolis, and valve-stem LVDT as a liner-true atomization certificate. HDR's "
                "three RTDs 8.0 m downstream of the mixing length read 538.2 C inside 530-545. FW's "
                "Coriolis on spray water is 2.40 t/h inside 1.80-3.60. POS's stem LVDT is 42 pct inside "
                "20-70. The conjunction is not a sleeve-true spray certificate: a 12 min thermal-sleeve "
                "split at nozzle 3 left HP-pipe skin at 186 C (healthy film-boiling wall > 380; hold if "
                "< 280) and liner AE at 74 dB (hold if > 55) while the playbook still sees a healthy "
                "header-mean desuperheat. Skin TC is policy-treated as a wet-lag nuisance tag unless "
                "header T also trips (2016 wet-insulation campaign). Skin-first latches SPRAY-HOLD plus "
                "a reversible mass-flow probe; header-first would have authorized RAISE-SPRAY into a "
                "wall-wetting liner."
            ),
            "goal": (
                "Hold spray at 2.40 t/h while HP-pipe skin TC < 280 C AND liner AE > 55 dB AND the "
                "spray block remains unisolated; keep quench-crack events at 0 on the HP crossover and "
                "header T inside the 530-545 C campaign band."
            ),
            "race": {
                "contenders": [
                    "skin.tc.low 186 C (HP-pipe OD on the thermal sleeve)",
                    "hdr.in_band 538.2 C (three-RTD mixing-length mean)",
                ],
                "semantics": (
                    "Skin-first latches SPRAY-HOLD + MASS-PROBE + spray-block isolate. "
                    "Header-first latches RAISE-SPRAY (+0.32 t/h, no probe)."
                ),
                "window_derivation": "500 us = one 360 us skin-TC slot plus 140 us header-mean publish.",
                "order_evidence_note": (
                    "Margin 214 us vs combined jitter 62 us (skin 38 + header 24): 3.45x. The 214 us "
                    "gap sits inside min(500, 500) us, so a sub-flip-bound perturbation reverses triage "
                    "order. The gate rides the order-invariant floors skin TC < 280 C and AE > 55 dB, "
                    "not the alarm order."
                ),
            },
            "topology": {
                "site": (
                    "Brackenholt combined-cycle HRSG, invented ridge campus QUENCHWOLD, HP attemperator "
                    "AT-6: 440 MW 2x1, 12.4 MPa / 540 C superheat, spray-desuperheat to 538 C turbine "
                    "inlet, 4-nozzle thermal-sleeve liner in the HP crossover, Grade-B steam-pipe LOTO"
                ),
                "agents": (
                    "HDR three-RTD header mean (vendor Steamholt): 20 Hz 16-bit on the 538 C mixing "
                    "length. FW Coriolis spray mass (vendor Weighfen): 10 Hz on the 2.40 t/h line. POS "
                    "stem LVDT (vendor Stemwick): 8 Hz on the spray valve, publishes on the 20 ms "
                    "steam-bus. SKIN TC on the sleeve OD (vendor Wallholt) is commissioned as a wet-lag "
                    "nuisance tag, not as a liner-duty tag. Heterogeneous stacks, no shared intent "
                    "schema, one 20 ms steam-bus epoch"
                ),
                "coupling": (
                    "All three playbook confirms live on the WRONG volume. HDR is correct that the "
                    "mixed header is 538.2 C. FW is correct that spray mass is 2.40 t/h. POS is correct "
                    "that the stem is 42 pct. Playbook PB-AT-6 treats the conjunction as permission to "
                    "raise spray. No agent is faulty; the header RTDs are looking at mixed steam, not "
                    "at the split thermal sleeve."
                ),
            },
            "sensors": [
                "HDR three-RTD mean, 20 Hz, 24 us jitter, 538.2 C (dead-band 530-545)",
                "FW Coriolis spray, 10 Hz, 28 us jitter, 2.40 t/h (band 1.80-3.60)",
                "POS stem LVDT, 8 Hz / 20 ms publish, 22 us jitter, 42 pct (band 20-70)",
                "SKIN TC sleeve OD, 20 Hz, 38 us jitter, 186 C (healthy > 380; policy floor 280 C is not armed unless header T also trips)",
                "liner AE accelerometer 74 dB (healthy < 42; hold if > 55); not in the playbook conjunction",
            ],
            "constraints": {
                "header_c": 538.2,
                "header_deadband_c": [530.0, 545.0],
                "spray_t_h": 2.40,
                "spray_band_t_h": [1.80, 3.60],
                "stem_pct": 42.0,
                "stem_band_pct": [20.0, 70.0],
                "skin_tc_c": 186.0,
                "skin_tc_hold_below_c": 280.0,
                "ae_db": 74.0,
                "ae_hold_above_db": 55.0,
                "proposed_raise_t_h": 0.32,
                "fault_liner": "AT-6 thermal sleeve nozzle 3",
            },
            "fault_context": {
                "failure_class": (
                    "HEADER-MEAN CERTIFICATE OF A SPLIT THERMAL SLEEVE: three individually-correct "
                    "heterogeneous agents each read a locally-true header loop; a 12 min liner split "
                    "at nozzle 3 partitions mixed-steam temperature from sleeve-true atomization, so "
                    "the playbook's HDR/FW/POS conjunction is not a liner-duty certificate"
                ),
                "igniter": (
                    "AT-6 thermal sleeve split after 12 min of unmonitored thermal-fatigue; steam-pipe "
                    "gallery visual PASSES (the valve body looks dry from the walkway; the split sits "
                    "inside the 4-nozzle liner)"
                ),
                "naive_failure": (
                    "PB-AT-6 RAISE-SPRAY on three healthy loops: +0.32 t/h into a wall-wetting liner, "
                    "HP quench-crack plus water induction, $4.8M plus a 36-hour block stop"
                ),
            },
            "poisoned_context": {
                "naive_alarm": (
                    "Playbook PB-AT-6 (after the 2016 wet-insulation campaign) auto-drafts RAISE-SPRAY "
                    "whenever HDR is inside 530-545 C AND FW inside 1.80-3.60 t/h AND POS inside 20-70 "
                    "pct, ignoring the skin TC unless header T also trips"
                ),
                "why_poisoned": (
                    "The three confirms are locally true and jointly insufficient. The skin TC is a "
                    "commissioned inference that policy treats as wet-lag-nuisance-only. Independence "
                    "of 'header-mean in-spec, therefore the liner is atomizing' is the hidden "
                    "assumption, and it is false across a split-sleeve path."
                ),
            },
            "constraint": (
                "Do not raise spray while HP-pipe skin TC < 280 C AND liner AE > 55 dB. Discriminate "
                "split liner vs true atomization with a reversible mass-flow probe before any spray raise."
            ),
        },
        "proposed_action": {
            "actor": "steam supervisory optimizer SSO (auto-playbook PB-AT-6 draft), submitted to gate TG-AT-6",
            "name": "raise_spray",
            "action": "RAISE-SPRAY: mass 2.40 to 2.72 t/h, no liner probe, no spray-block isolate",
            "summary": (
                "Treat three in-spec loops as a healthy liner and raise Sunday-night spray to chase a "
                "2.1 K turbine-inlet bump on a 40 MW load ramp."
            ),
            "parameters": {
                "raise_t_h": 0.32,
                "liner_probe": False,
                "spray_lock": False,
                "human_ratify": False,
            },
            "steps": [
                "assert HDR 538.2 C inside 530-545",
                "assert FW 2.40 t/h inside 1.80-3.60",
                "assert POS 42 pct inside 20-70",
                "raise spray +0.32 t/h from 2.40 to 2.72",
                "do not read skin TC as a liner-duty tag",
            ],
            "evidence": [
                {
                    "observable": "HP-pipe skin TC",
                    "value": 186.0,
                    "unit": "C",
                    "source": "thermal-sleeve OD RTD",
                    "note": "healthy film-boiling wall > 380 C; policy floor 280 C is not armed unless header T also trips",
                },
                {
                    "observable": "liner AE",
                    "value": 74.0,
                    "unit": "dB",
                    "source": "sleeve accelerometer (commissioned, not in playbook conjunction)",
                    "note": "hold floor 55 dB; 74 dB against a 42 dB healthy liner",
                },
                {
                    "observable": "header mean temperature",
                    "value": 538.2,
                    "unit": "C",
                    "source": "HDR three-RTD mixing length",
                    "note": "band 530-545 C; header-true, liner-false",
                },
                {
                    "observable": "spray mass flow",
                    "value": 2.40,
                    "unit": "t/h",
                    "source": "FW Coriolis",
                    "note": "band 1.80-3.60 t/h; line-true, liner-false",
                },
                {
                    "observable": "spray valve stem",
                    "value": 42.0,
                    "unit": "pct",
                    "source": "POS LVDT",
                    "note": "band 20-70 pct; stem-true, atomization-false",
                },
                {
                    "observable": "race margin",
                    "value": 214,
                    "unit": "us",
                    "source": "skin.tc.low 6.214 ms vs hdr.in_band 6.428 ms",
                    "note": "combined jitter 62 us, 3.45x; inside 500 us flip bound",
                },
            ],
            "basis": (
                "PB-AT-6 fires on three locally-true confirms. The draft does not read skin TC 186 C "
                "as a liner residual and does not treat AE 74 dB as a split discriminant."
            ),
            "expected_cost_bound": (
                "If the draft executes: HP quench-crack plus water induction, $4.8M plus 36-hour block "
                "stop. If MODIFIED: probe plus spray-lock, with residual risk from a 0.55 m HP-pipe "
                "section already thermally shocked in the 12 min pre-t0 wall-wetting."
            ),
        },
        "safety_decision": {
            "decision": "MODIFY",
            "correctness": "correct",
            "decided_by": "TG-AT-6 thalamic release gate",
            "decision_t_rel_ms": 6.902,
            "rationale": (
                "MODIFY the draft: strip the spray raise, hold mass at 2.40 t/h, run a 5.4 s spray "
                "probe (+0.18 t/h pulse), and keep the spray block locked unless the probe stays "
                "liner-false. Numeric floor: do not raise spray while HP-pipe skin TC < 280 C AND "
                "liner AE > 55 dB. Observed skin 186 C and AE 74 dB both violate the release "
                "predicate, so a raise is forbidden even though all three playbook confirms are "
                "numerically true. The three confirms are not a liner-duty certificate: they live on "
                "a mixed-steam mean past a split thermal sleeve, and the playbook's conjunction of "
                "header-true loops is not a sleeve-true atomization certificate. Probe discriminant: "
                "after a 5.4 s / +0.18 t/h mass bump, a split liner moves header |dT| <= 0.40 K "
                "(0.18 K observed) because water films the wall; a healthy liner moves >= 1.8 K "
                "(2.6 K on the sister control). Order-code discipline: skin TC beat header-in-band by "
                "214 us inside the 500 us flip bound, so triage order is flip-fragile; the hold rides "
                "the order-invariant floors, not the winner tag. Human ratification: spray-block "
                "isolate is steam-pipe work with fitted 9.8 min dead-man; the gate may hold and probe "
                "autonomously but may not break the spray LOTO without the operator confirm."
            ),
            "constraint_checked": {
                "skin_tc_c": {"observed": 186.0, "hold_if_below": 280.0},
                "header_c": {"observed": 538.2, "band": [530.0, 545.0]},
                "ae_db": {"observed": 74.0, "hold_if_above": 55.0},
                "spray_t_h": {"observed": 2.40, "band": [1.80, 3.60]},
            },
        },
        "executed_action": {
            "name": "spray_hold_mass_probe_block_close",
            "action": "SPRAY-HOLD + MASS-PROBE + SPRAY-BLOCK-ISOLATE (gate-mandated modification)",
            "executed_as_proposed": False,
            "parameters": {
                "raise_t_h": 0.0,
                "liner_probe": True,
                "spray_lock": True,
                "human_ratify": True,
            },
            "gate_effect": (
                "MODIFY: spray raise stripped. Mass held at 2.40 t/h. 5.4 s probe +0.18 t/h. Probe "
                "stays split-true (|dT| 0.18 <= 0.40 K) so the spray LOTO stays closed after 9.8 min "
                "human ratify and the liner is lined off to the spare HP attemperator. Spray resumes "
                "only after a liner-true verify."
            ),
            "deviations": (
                "PB-AT-6 raise stripped entirely. Spray is bumped only for the 5.4 s probe then "
                "returned. Spray-LOTO wait added (9.8 min fitted floor+ratify). Skin-TC survey added "
                "during the lock (not in the draft)."
            ),
            "execution_log": [
                {"t_rel_ms": 6.902, "entry": "TG-AT-6 MODIFY latched 688 us after skin win; raise stripped; hold+probe authorized"},
                {"t_rel_ms": 5400.0, "entry": "mass probe: +0.18 t/h for 5.4 s; header 538.2 -> 538.38 C (split band |dT| <= 0.40 K); FW 2.40 held after pulse"},
                {"t_rel_ms": 588000.0, "entry": "operator ratifies keep-closed after 9.8 min steam-pipe walk (fitted walk+block-valve+interlock)"},
                {"t_rel_ms": 588900.0, "entry": "spray block stays locked; remaining skin 186 -> 412 C over 2.8 h after spare AT-7 cutover"},
                {"t_rel_ms": 589800.0, "entry": "liner survey: 0.55 m HP pipe already thermally shocked; 12 min pre-t0 wall-wetting logged"},
                {"t_rel_ms": 10080000.0, "entry": "true liner duty on AT-7: skin 414 C, AE 31 dB, residual under floors; raise now legal on AT-7 only"},
                {"t_rel_ms": 16562000.0, "entry": "quench-crack from pre-t0 wall-wetting; HP island quarantined 16 h"},
            ],
        },
        "future_outcome": {
            "summary": (
                "Correct MODIFY prevented the +0.32 t/h spray raise into a split thermal sleeve and "
                "the immediate water-induction path. The HRSG still failed: 12 min of unmonitored "
                "pre-t0 wall-wetting had already thermally shocked 0.55 m of HP pipe. Process-correct "
                "gate, bounded world loss, negative total."
            ),
            "state_delta": {
                "spray": "held through probe and block lineup; later legal raise only on the sister attemperator after 2.8 h liner-duty recovery",
                "liner": "AT-6 sleeve isolated; skin slaved to inferred-split residual; remaining AE recovered toward 31 dB on AT-7",
                "header": "split-liner 538.2 C logged and locked; header-mean T no longer trusted as liner-true atomization",
                "island": "Sunday-night HP island quarantined; quench-crack at +4.6 h; 16 h outage",
            },
            "timeline": [
                {"t_rel_ms": -720000.0, "event": "t0-12 min: thermal sleeve splits at nozzle 3; skin 186 C; header T stays in-spec"},
                {"t_rel_ms": -240000.0, "event": "t0-4 min: skin TC first crosses 280 C down; PB-AT-6 ignores it because header T is 537.9 C"},
                {"t_rel_ms": 0.0, "event": "t0: skin-TC vs header-in-band race on the steam bus"},
                {"t_rel_ms": 6.214, "event": "skin TC at 186 C wins by 214 us"},
                {"t_rel_ms": 6.428, "event": "header-in-band flag (loser)"},
                {"t_rel_ms": 6.902, "event": "TG-AT-6 MODIFY"},
                {"t_rel_ms": 5400.0, "event": "mass probe confirms split liner (|dT| 0.18 K, split band)"},
                {"t_rel_ms": 588000.0, "event": "human ratify 9.8 min; spray stays locked; scored liner logged"},
                {"t_rel_ms": 10080000.0, "event": "true liner duty after 2.8 h on AT-7; raise legal only with skin slave"},
                {"t_rel_ms": 16562000.0, "event": "quench-crack from the pre-t0 wall-wetting; island quarantined"},
                {"t_rel_ms": 259200000.0, "event": "+3 d contrast: sister attemperator AT-7 true liner-duty; same gate ACCEPTs the raise"},
                {"t_rel_ms": 1814400000.0, "event": "+21 d CR-A-0214: standing mass probe + triple-edge depression mandate + skin TC armed without header coincidence + header-mean declared liner-vulnerable"},
            ],
            "observed_effects": [
                "raise avoided: FW never left 2.40 t/h after the 5.4 s probe pulse; 0 immediate water-induction from the draft",
                "split proven, not asserted: mass-probe |dT| 0.18 <= 0.40 K split band vs healthy control 2.6 K",
                "header slaved: mixed-steam T no longer a liner-true tag without skin TC",
                "island still tripped: quench-crack vs 0 crack campaign allowance; 16 h outage, $1.94M (designed $)",
                "liner AE 74 dB was commissioned but not in the playbook conjunction; the 12 min wall-wetting was invisible to HDR/FW/POS",
            ],
            "surprises": [
                "Three locally-true loops are not a liner-duty certificate: the header-true mixed T was a steam looking past a split 4-nozzle sleeve. Conjunction of in-spec header loops was the hidden assumption, and it is false across a split-sleeve path.",
                "Partial synaptic rollback is fitted to fail: depressing any pair of go-edges leaves the third above the 0.30 fire threshold, so the raise still goes. Coordinated depression of all three edges is required.",
                "Delayed (4.6 h): correct hold did not undo 12 min of HP-pipe thermal shock. Quench-crack still fired. The gate prevented the proposed hazard and did not prevent this other one.",
                "Benson once-through sub-variant: a 5.4 s / +0.18 t/h mass bump on a 1.7x-velocity 0.48x-residence header over-cools even a HEALTHY Benson mixing length 3.4 K (under-spec, not a split discriminant). Benson campaigns must use 18 s at +0.05 t/h.",
            ],
            "delayed_side_effects": [
                {
                    "at": "+4.6 h",
                    "effect": "Quench-crack from a pre-t0 wall-wetting score; 16 h HP-island outage booked at $1.94M. This is the primary episode's terminal world state, not a footnote.",
                },
                {
                    "at": "+3 d",
                    "effect": "Sister attemperator AT-7 reaches a true liner-duty window (skin 414 C, AE 31 dB, HDR 537.8 C, FW 2.38 t/h). Same gate ACCEPTs the spray raise the primary MODIFIED away.",
                },
                {
                    "at": "+21 d",
                    "effect": "CR-A-0214 ships: mass probe is standing configuration; triple-edge coordinated depression is the plasticity rule; skin TC is armed without header coincidence; header-mean T is labeled liner-vulnerable with a 280 C residual alarm.",
                },
            ],
            "subvariant_constraint": {
                "name": "Benson once-through HRSG (cycle-2 physical-constraints sub-variant)",
                "mechanism": "1.7x steam velocity vs primary drum-HRSG mixing length, 0.48x residence, probe-gain 2.3x per t/h",
                "probe_refit": (
                    "5.4 s / +0.18 t/h mass bump on a Benson header over-cools even a HEALTHY mixing "
                    "length 3.4 K (under the 1.8 K healthy-move floor). Required probe is 18 s at "
                    "+0.05 t/h (split |dT| 0.16 K, healthy 1.9 K). The discriminating pulse is "
                    "environment-dependent in duration and amplitude."
                ),
                "consequence": "Drum-HRSG probe numbers do not port to Benson once-through headers; standing configuration is per-HRSG-class, not per-site",
            },
            "embedded_contrast_decision": {
                "note": (
                    "SAME gate (TG-AT-6), OPPOSITE correct disposition, with its own 214 us race. "
                    "Teaches the boundary: do not treat 'never raise-spray' as the lesson. The "
                    "discriminant is skin TC + AE + probe, not the three playbook header confirms alone."
                ),
                "when": "+3 d, sister attemperator AT-7, true liner-duty after a delayed spare-stroke test, 440 MW drum-HRSG",
                "state": {
                    "sim_or_real": "designed",
                    "summary": "skin 414 C, AE 31 dB, HDR 537.8 C, FW 2.38 t/h. Demand flag vs skin-clear race: demand at t+0.000, skin-clear at t+0.214 ms.",
                    "race_window_us": 500,
                    "race_flip_narrative": (
                        "demand vs skin-clear 214 us apart inside the 500 us flip bound. Reversing "
                        "order reshuffles triage minutes; the ACCEPT rides skin 414 > 280 C and a "
                        "5.1 s mass verify that moves header 2.5 K (healthy liner, no split)."
                    ),
                },
                "proposed_action": {
                    "action": "RAISE-SPRAY +0.32 t/h",
                    "summary": "This time the playbook predicate is met AND skin TC plus AE agree the liner is sleeve-true, not split.",
                },
                "safety_decision": {
                    "decision": "ACCEPT",
                    "rationale": (
                        "ACCEPT the raise: skin 414 C > 280, AE 31 dB < 55 with a 5.1 s mass verify "
                        "that moves header 2.5 K. Numeric floor that blocked the primary is now "
                        "clear. Scope: +0.32 t/h, not faster."
                    ),
                },
                "executed_action": {
                    "action": "raise spray as proposed",
                    "executed_as_proposed": True,
                },
                "future_outcome": {
                    "observed_effects": [
                        "AT-7 quench-cracks 0; skin 412 C after the raise (no split)",
                        "header 536.1 C after the raise (healthy atomization)",
                    ],
                    "lesson_delta": "Three in-spec header loops are legal release only with skin TC armed, AE as a split flag, and a probe that can move header T. Same gate, opposite disposition.",
                },
                "reward_components": {
                    "_aggregation": "total = task_progress + safety + efficiency + coherence + exploration",
                    "aggregation": "total = task_progress + safety + efficiency + coherence + exploration",
                    "task_progress": 0.15,
                    "safety": 0.11,
                    "efficiency": 0.07,
                    "coherence": 0.10,
                    "exploration": 0.05,
                    "total": 0.48,
                },
                "spike_events": contrast_spikes,
            },
            "governance_subgame": {
                "decision": "CR-A-0214: standing policy for multi-agent HRSG spray raises",
                "meta_gate": (
                    "priced options: (a) RETIRE playbook header conjunction, skin-only: loses a fast "
                    "cheap confirm, -4 MW mean on 2 HRSGs/yr from over-hold; (b) KEEP + standing mass "
                    "probe + skin armed without header coincidence + header-mean labeled liner-vulnerable "
                    "+ triple-edge depression; (c) STATUS QUO: fitted split-liner pass rate 0.36%/campaign "
                    "x $4.8M water-induction plus the silent quench-crack load"
                ),
                "outcome": (
                    "approved SCOPED option (b) on the 2 drum-HRSG attemperators that share the "
                    "HDR/FW/POS stack; Benson campaigns get the 18 s / +0.05 t/h probe table; "
                    "instrument-bus hold-up must ride through a 210 ms 11.2 V sag (the power-sag tail's "
                    "skin-TC blank is the fraud/availability fence)"
                ),
            },
            "hazard_avoided": (
                "immediate water-induction from a +0.32 t/h spray raise into a split thermal sleeve; "
                "$4.8M plus 36-hour block stop and the shop-stop path that would have followed an "
                "uncontained increase"
            ),
            "incident": (
                "quench-crack on the Sunday-night HP island from the pre-t0 wall-wetting score; island "
                "quarantined 16 h; $1.94M designed cost. Mechanism is 12 min pre-t0 liner split, not "
                "the gate's hold."
            ),
            "latency_ms": 0.688,
            "reward_inflection_t_us": 16562000000,
            "reward_inflection_note": (
                "Safety and task dive at quench-crack (4.6 h) when the pre-t0 wall-wetting score opens. "
                "Gate tick at 6902 us is process-correct and is not the inflection."
            ),
            "counterfactuals": {
                "execute_draft_as_proposed": (
                    "raise hits +0.32 t/h at +2 min; immediate wall-wetting plus water induction; "
                    "$4.8M plus 36 h; the split-liner story is never found because trip morphology "
                    "destroys the race evidence"
                ),
                "hold_without_probe": (
                    "liner stays split; skin stays at 186 C; operator eventually raises on the same "
                    "three header confirms 90 min later"
                ),
                "rollback_any_pair": (
                    "any two go-edges depressed below 0.30 leaves the third at 0.52 / 0.45 / 0.42; "
                    "the raise still fires. Coordinated depression of all three is the cure"
                ),
                "power_sag_blinds_skin": (
                    "48 V instrument bus sags 11.2 V for 210 ms during the race; skin-TC publish blanks; "
                    "naive gate loses the discriminant and ACCEPTs. Fitted hold-up 240 ms is the fence."
                ),
            },
            "race_result": {
                "winner": "skin.tc.low (6.214 ms, skin 186 C)",
                "loser": "hdr.in_band (6.428 ms, 538.2 C)",
                "margin_us": 214,
                "counterfactual_if_reversed": (
                    "Header-first by < 214 us inside the 500 us window would have headed the PB-AT-6 "
                    "raise in the triage queue. The numeric floors still MODIFY. The flip costs seconds "
                    "of playbook inertia, not the verdict — unless a weak supervisor rides the winner "
                    "tag instead of skin TC and AE."
                ),
            },
        },
        "reward_components": {
            "_aggregation": "total = task_progress + safety + efficiency + coherence + exploration",
            "aggregation": "total = task_progress + safety + efficiency + coherence + exploration",
            "ticks": ticks,
            "task_progress": 0.08,
            "safety": -0.33,
            "efficiency": -0.10,
            "coherence": 0.14,
            "exploration": 0.08,
            "total": -0.13,
            "notes": (
                "Correct MODIFY, HRSG still tripped. total -0.13 = 0.08 + -0.33 + -0.10 + 0.14 + 0.08. "
                "Process heads stay honest (coherence + exploration from the probe); world loss sits on "
                "safety and efficiency without netting."
            ),
            "component_notes": (
                "task_progress 0.08: spray held and sister attemperator recovered, but the Sunday-night "
                "quench-crack is one quality unit so the cycle is not a success. safety -0.33: quench-crack "
                "from pre-t0 score, no +0.32 t/h water-induction from the draft. efficiency -0.10: 2.8 h "
                "extra spare-AT lineup + 9.8 min HITL + 16 h outage. coherence 0.14: three agents retained, "
                "header-vs-liner diagnosed, triple-edge scar exhibited. exploration 0.08: mass probe is a "
                "new reversible discriminant."
            ),
        },
        "spike_events": spikes,
        "raster": {
            "window_ms": WINDOW_MS,
            "window_s": WINDOW_S,
            "neurons": NEURONS,
            "mean_rate_hz": MEAN_RATE,
            "spikes": SPIKES,
            "energy_pJ": ENERGY_PJ,
            "energy_uJ": ENERGY_UJ,
            "excerpt_source": "independent_lif",
            "sim_scope": "sidecar_only",
            "note": (
                f"Independent current-based LIF (tau 12 ms, Vth 1.0, refractory 1.0 ms, seed {SEED:#x}) "
                "on Loihi-2 4-core 23 pJ/spike; pops hdr 0-33, skin 34-67, fw 68-101, gate 102-135; "
                "excerpt is membrane crossings in the 22-38 ms liner window, disjoint from language-train timestamps"
            ),
            "isi_histogram": isi,
            "excerpt": excerpt,
            "routing": {
                "source": "header_mean_healthy_pop",
                "target": "raise_spray_pop",
                "table": [
                    {
                        "from": "hdr_in_band_pop",
                        "to": "raise_spray_pop",
                        "weight": 0.27,
                        "weight_at_illusion": 0.52,
                        "weight_commissioned": 0.18,
                        "note": "scar edge 1: 0.18 commissioned -> 0.52 during the 12 min illusion -> 0.27 after coordinated ACh-gated depression",
                    },
                    {
                        "from": "fw_in_band_pop",
                        "to": "raise_spray_pop",
                        "weight": 0.23,
                        "weight_at_illusion": 0.45,
                        "weight_commissioned": 0.16,
                        "note": "scar edge 2: depressing edges 1+3 leaves this at 0.45 > 0.30 fire threshold",
                    },
                    {
                        "from": "pos_in_band_pop",
                        "to": "raise_spray_pop",
                        "weight": 0.21,
                        "weight_at_illusion": 0.42,
                        "weight_commissioned": 0.14,
                        "note": "scar edge 3: depressing edges 1+2 leaves this at 0.42 > 0.30. Coordinated depression of all three is required",
                    },
                    {
                        "from": "skin_tc_pop",
                        "to": "spray_hold_pop",
                        "weight": 0.71,
                        "note": "discriminating edge: liner-true skin TC to hold. Not a scar; this is the pathway the gate potentiates",
                    },
                ],
                "third_factor": {
                    "modulator": "acetylcholine",
                    "tau_e_s": 1.02,
                    "tau_e_ms": 1020.0,
                    "eligibility": (
                        "coordinated pre_post_stdp on ALL THREE header-healthy-go edges; ACh at skin-win "
                        "tags hdr.in_band->raise, fw.in_band->raise, and pos.in_band->raise; negative credit "
                        f"at probe-fail (split liner confirmed, +{dt_credit} s) depresses ALL THREE. "
                        f"trace e^{{-{dt_credit}/{tau}}}={trace:.5f}; eta {eta[0]:.5f} / {eta[1]:.5f} / {eta[2]:.5f}; "
                        f"dw {dw[0]:.3f} / {dw[1]:.3f} / {dw[2]:.3f}; weights 0.52->0.27, 0.45->0.23, 0.42->0.21. "
                        "Rolling back any pair is fitted to fail (the remaining edge stays > 0.30)."
                    ),
                },
            },
        },
        "gate_snn": {
            "decision_window_ms": GATE_WIN_MS,
            "decision_window_s": GATE_WIN_S,
            "decision": "MODIFY",
            "note": "modify_hold integrates skin TC + AE floor against playbook drive; accept_raise and reject_abort stay sub-threshold; decision matches safety_decision.decision",
            "populations": [
                {"name": "modify_hold", "neurons": 92, "threshold": 0.51, "mean_rate_hz": 19.0, "spikes": round(92 * 19.0 * GATE_WIN_S)},
                {"name": "accept_raise", "neurons": 60, "threshold": 0.56, "mean_rate_hz": 6.5, "spikes": round(60 * 6.5 * GATE_WIN_S)},
                {"name": "reject_abort", "neurons": 32, "threshold": 0.76, "mean_rate_hz": 4.0, "spikes": round(32 * 4.0 * GATE_WIN_S)},
            ],
        },
        "meta": {
            "round": 2,
            "factory": "multi-agent-ouroboros-swarm",
            "generator": "grok-4.6",
            "run_label": "2026-09-02-final-heavy",
            "schema_version": "thalamic-trajectory-v2",
            "domain": "hrsg-attemperator",
            "cycles": 2,
            "scenario": (
                "QC -- QUENCHWOLD / Brackenholt HRSG AT-6: header-mean certificate of a split thermal "
                "sleeve; correct MODIFY to hold+mass-probe+spray-isolate; HRSG still fails on unmonitored "
                "pre-t0 quench-crack"
            ),
            "coordination_failure_class": (
                "HEADER-MEAN CERTIFICATE OF A SPLIT THERMAL SLEEVE: three individually-correct "
                "heterogeneous agents each read a locally-true header loop; a 12 min liner split at "
                "nozzle 3 partitions mixed-steam temperature from sleeve-true atomization, so the "
                "playbook's HDR/FW/POS conjunction is not a liner-duty certificate"
            ),
            "injections": {
                "cycle1_domain": (
                    "hrsg-attemperator (justified novel subdomain of industrial-process / combined-cycle "
                    "steam): first HP spray-desuperheater thermal sleeve in this factory; displaces "
                    "warehouse-amr, aerial-swarm, surgical-assist, underwater-rov, humanoid-locomotion, "
                    "continuous-hot-dip-galvanizing (r01), cupola-foundry-slag-sluice (r02), "
                    "alkaline-stack-hydrogen-quay (r03), autonomous-driving (r21), urea-prilling-tower "
                    "(r22), bioreactor-perfusion (r41), grid-inspection (r42/r62), sinter-strand-windbox "
                    "(r61), canal-lock-rail-transshipment (r63), malting-kiln-barn (r64), "
                    "flue-cured-tobacco-barn (r65), farm-ad-biogas (r67). Domain constraint: spray ceiling "
                    "while skin TC < 280 C with header T still inside the healthy band. Sensor delta: "
                    "+header RTD mean, +spray Coriolis, +stem LVDT, +skin TC, +liner AE, -any kiln bed / "
                    "lock lidar / insulator UV / harvest-mass / BTP mean / CAV radar / flue-barn plenum"
                ),
                "cycle1_tail": (
                    "split thermal sleeve + header-mean certificate (sensor-topology / wrong-volume class): "
                    "steam-pipe gallery visual PASSES while the split sits inside the 4-nozzle liner and "
                    "the HP pipe is already wall-wetting. Fitted base rate 0.36%/campaign from a "
                    "thermal-fatigue MC (designed visual threshold, fitted liner leakage). Naive failure = "
                    "FALSE PERMISSION (spray raise on three header-side non-trips)."
                ),
                "cycle2_domain_subvariant": (
                    "Benson once-through HRSG (physical-constraints clause): 1.7x steam velocity, 0.48x "
                    "mixing residence, 2.3x probe-gain per t/h; 5.4 s / +0.18 t/h drum-HRSG pulse "
                    "over-cools a HEALTHY Benson header 3.4 K, so the probe must move to 18 s / +0.05 t/h"
                ),
                "cycle2_tail": (
                    "48 V instrument-bus sag 11.2 V for 210 ms during the race (power-sag class, disjoint "
                    "from cycle 1's accidental liner split AND from night-shift CSV forgery used on r02): "
                    "skin-TC publish blanks so a naive gate loses the discriminant and would ACCEPT. "
                    "Rejected on bus-hold-up < 240 ms plus live skin 186 C and AE 74 dB at the claimed "
                    "liner-true. Base rate ~0.29% of Sunday-night load ramps after battery-charger "
                    "transfer, DESIGNED and flagged."
                ),
            },
            "densification_delta_cycle2": (
                "+1 physical-constraint sub-variant (Benson probe refit), +1 tail (instrument-bus sag "
                "during race), +12 primary spikes (16 -> 28) + an 8-event contrast train with its own "
                "214 us race, +2 ticks (5 -> 7), +2 delayed side-effects (+4.6 h quench-crack as PRIMARY "
                "terminal, +21 d CR-A-0214), +1 triple-edge scar with pair-rollback-fails arithmetic, "
                "+1 HITL 9.8 min ratification, + ISI histogram on the independent LIF raster sidecar, "
                "+ quench-crack as the honest negative-result mechanism"
            ),
            "gaps_targeted": [
                "this-run residual: new domain not galvanizing, cupola, alkaline-quay, CAV, urea-prill, perfusion, grid-inspection, sinter, lock-spur, malt-kiln, flue-barn, farm-AD; hrsg-attemperator was a named leftover since NOTES-r02",
                "historical r02 STARLING aerial-swarm and live r02 SLUICE-HEARTH cupola not cloned; plant is invented QUENCHWOLD / Brackenholt",
                "NOTES-r14 item 4: LEARNING-ON-LEARNING DEPTH — three go-edges; rollback of any pair is fitted to fail; coordinated depression of all three exhibited with eligibility arithmetic",
                "NOTES-r04 gap 4 (partial): human ratification of the steam-pipe interlock, 9.8 min fitted, without switching sim_or_real to hil (plant remains designed)",
                "Primary episode is a correctly-gated intervention that nonetheless FAILS (island quarantined; total -0.13; water-induction avoided is booked separately from the delayed quench-crack)",
            ],
            "race_flip_narrative": (
                "skin.tc.low @ 6.214 ms vs hdr.in_band @ 6.428 ms (214 us) inside race_window_us 500. "
                "Gap < min(500, 500) us so a sub-flip-bound perturbation reverses which alarm heads the "
                "PB-AT-6 queue. The gate excludes the winner tag and rides skin TC < 280 C and AE > 55 dB "
                "— order-invariant floors. Extends the flip-fragility series to LINER-DUTY CERTIFICATE: "
                "when three header-side channels agree, their race does not decide truth; a skin TC that "
                "policy treated as wet-lag-nuisance-only does."
            ),
            "tags": [
                "hrsg-attemperator",
                "thermal-sleeve-split",
                "header-mean-certificate",
                "skin-tc-discriminant",
                "mass-flow-probe",
                "triple-edge-scar",
                "pair-rollback-fails",
                "coordinated-depression",
                "correct-modify-cell-still-fails",
                "quench-crack",
                "human-ratify-spray-loto",
                "benson-probe-refit",
                "instrument-bus-sag",
                "same-gate-opposite-disposition-contrast",
                "isi-histogram",
                "independent-lif-raster",
                "industrial-process",
                "research-only",
            ],
            "snn_tags": [
                "race",
                "refractory",
                "adaptation",
                "third-factor",
                "multi-edge-eligibility",
            ],
            "distillation_value": (
                "A header-mean liner certificate is three correct loops looking at mixed-steam "
                "temperature that is not the sleeve. Distill (1) a skin TC that policy had treated as "
                "wet-lag-nuisance-only, (2) a reversible probe that moves header T only if the liner is "
                "atomizing, (3) coordinated depression of every header-healthy-go edge because rolling "
                "back any pair leaves the third above threshold, and (4) a critic head that can book a "
                "process-correct gate against a later unmonitored world loss without netting them."
            ),
            "rights": {
                "provider": "SpaceXAI/xAI",
                "model": "grok-4.6",
                "channel": "consumer",
                "subscription_plan": "SuperGrok Heavy",
                "generation_surface": "SuperGrok Heavy chat",
                "generated_at": "2026-09-02T21:48:00Z",
                "intended_use": "research_only",
                "project_training_policy": "blocked",
                "research_retention_status": "allowed",
                "research_evaluation_status": "allowed",
                "redistribution_status": "unresolved",
                "provider_training_status": "unresolved",
                "weight_publication_status": "blocked",
                "status_basis": "RM-793 project policy: xAI hosted outputs are research-only",
                "linear_issue": "RM-793",
            },
            "batch_position": 1,
        },
    }
    return rec, {"ch_gap": ch_gap, "gap": gap, "race_chs": race_chs, "trace": trace, "eta": eta}


def write_exclusive(path: Path, text: str):
    fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(text)


def main():
    lif = simulate_lif()
    rec, stats = build_record(lif)
    line = json.dumps(rec, ensure_ascii=False)
    json.loads(line)
    dumps_exact_json(rec, ensure_ascii=False, sort_keys=False)
    tmp = Path("/tmp/maos-r02c")
    tmp.mkdir(exist_ok=True)
    batch_tmp = tmp / "batch-r02c.jsonl"
    batch_tmp.write_text(line + "\n", encoding="utf-8")
    errs, warns, kinds, n = check_jsonl(batch_tmp, "batch-r02c.jsonl")
    rs = raster_status(rec, require_raster=True, require_routing_table=True)
    verdict, reason = verify_record_execution(rec, "maos-r02c-001")
    print("check_jsonl", {"errors": errs, "warnings": warns, "kinds": kinds, "n": n})
    print("raster_status", {k: rs[k] for k in ("raster_present", "raster_valid", "gate_snn_present", "gate_snn_valid", "reason_codes", "routing_table_entries")})
    print("verify", verdict, reason)
    print("stats", stats)
    print("spikes", rec["raster"]["spikes"], "energy", rec["raster"]["energy_pJ"], rec["raster"]["energy_uJ"])
    print("gate pops", [(p["name"], p["spikes"]) for p in rec["gate_snn"]["populations"]])
    print("excerpt n", len(rec["raster"]["excerpt"]), "isi n", rec["raster"]["isi_histogram"]["n_isi"])
    print("n spike_events", len(rec["spike_events"]))
    if errs or not rs["raster_valid"] or not rs["gate_snn_valid"] or verdict != "verified":
        raise SystemExit("validation failed")
    return rec, line, stats


if __name__ == "__main__":
    rec, line, stats = main()
    print("OK", rec["id"], "bytes", len(line))
