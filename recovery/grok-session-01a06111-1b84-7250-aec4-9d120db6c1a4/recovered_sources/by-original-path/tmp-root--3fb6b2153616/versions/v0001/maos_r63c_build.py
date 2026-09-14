#!/usr/bin/env python3
"""Create-only MAOS r63c artifacts: industrial-assembly press-fit cell."""
from __future__ import annotations

import json
import math
import os
import random
import sys
from pathlib import Path

sys.path.insert(0, "/home/raulmc/rmems/synthetic-factory/pipelines")
from exact_json import dumps_exact_json  # noqa: E402

OUT = Path(
    "/home/raulmc/rmems/synthetic-factory/outputs/raw/2026-09-02-final-heavy/"
    "multi-agent-ouroboros-swarm"
)
BATCH = OUT / "batch-r63c.jsonl"
NOTES = OUT / "NOTES-r63c.md"
TRANSCRIPT = OUT / "swarm-transcript-r63c.md"

RIGHTS = {
    "provider": "SpaceXAI/xAI",
    "model": "grok-4.6",
    "channel": "consumer",
    "subscription_plan": "SuperGrok Heavy",
    "generation_surface": "SuperGrok Heavy chat",
    "generated_at": "2026-09-02T21:42:00Z",
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


def gen_lif_events(neurons: int, window_us: int, n_spikes: int, seed: int, tref: int = 1150):
    rng = random.Random(seed)
    events = []
    attempts = 0
    while len(events) < n_spikes and attempts < 400000:
        attempts += 1
        nid = rng.randrange(neurons)
        t = rng.randrange(0, window_us + 1)
        ok = True
        for tt, nn in events:
            if nn == nid and abs(tt - t) < tref:
                ok = False
                break
        if ok:
            events.append((t, nid))
    events.sort()
    if len(events) != n_spikes:
        raise RuntimeError(f"LIF underfilled: {len(events)} != {n_spikes}")
    return events


def pick_excerpt(events, n=16):
    """16 unique-neuron excerpt, sorted, independent of language-train times."""
    used = set()
    chosen = []
    # Prefer spread: take every k-th event with unique neuron_id.
    for t, nid in events:
        if nid in used:
            continue
        used.add(nid)
        chosen.append({"t_us": int(t), "neuron_id": int(nid)})
        if len(chosen) == n:
            break
    if len(chosen) < n:
        raise RuntimeError("excerpt short")
    chosen.sort(key=lambda e: (e["t_us"], e["neuron_id"]))
    return chosen


def build_record():
    window_ms = 38
    window_s = 0.038
    neurons = 156
    mean_rate_hz = 12.0
    spikes = round(neurons * mean_rate_hz * window_s)
    assert spikes == 71
    energy_pJ = spikes * 23
    energy_uJ = spikes * 23e-6
    lif = gen_lif_events(neurons, window_ms * 1000, spikes, seed=63003)
    excerpt = pick_excerpt(lif, 16)

    dw1, dw2, dw3 = -0.250, -0.220, -0.210
    rec = {
        "id": "maos-r63c-001",
        "title": (
            "COLLETFEN PF-6: pin-14 LVDT 0.42 mm short / slope 2.8 kN/mm beats "
            "force-mean in-band by 204 us; correct MODIFY still loses a cracked "
            "carrier web to a pre-t0 oversized press"
        ),
        "rights": RIGHTS,
        "provenance": {"kind": "designed", "claimed": "designed"},
        "state": {
            "sim_or_real": "designed",
            "domain": "industrial-assembly",
            "scenario_name": "COLLETFEN / Spigotholt Press-Fit Cell PF-6",
            "timestamp_local": "2026-03-08T02:14:00-05:00",
            "t0_us": 1772954040000063,
            "gate_latency_us": 718,
            "race_window_us": 500,
            "race_window_rel_ms": [6.412, 6.912],
            "description": (
                "Spigotholt press-fit cell PF-6 seats Ø18.00 mm planetary-carrier "
                "pins on a six-station rotary indexer at 41.2 C die temperature. "
                "Three heterogeneous, individually-correct agents each report their "
                "local loop in-spec: FRC press-force mean 8.4 kN inside 7.6-9.2 "
                "(stations 1-5 dominate the header), POS servo C-axis at programmed "
                "seat 0.00 mm (servo-true), TMP die 41.2 C inside 35-50 (die-true). "
                "The conjunction is not a pin-true seat certificate. Pin 14 at "
                "station 3 is 12 µm oversized (interference H7/p6 vs specified "
                "H7/n6). Local LVDT residual 0.42 mm short of mechanical seat "
                "(healthy < 0.05; hold if > 0.20) and local force-slope 2.8 kN/mm "
                "(healthy 1.1-1.6; hold if > 2.2) but policy treats both as a "
                "lube-film nuisance tag unless FRC mean also trips (2016 noisy LVDT "
                "after oil splash). Playbook PB-PF-6 auto-drafts FIRE-NEXT-PIN "
                "whenever the three mean confirms land. Invented plant; designed."
            ),
            "goal": (
                "Hold station 3 at the seated pose without firing station-4 while "
                "LVDT residual_mm > 0.20 AND local slope_kN_per_mm > 2.2 AND pin 14 "
                "remains an unverified oversize class."
            ),
            "race": {
                "contenders": [
                    "lvd.short.high 0.42 mm (station-3 LVDT vs force-mean FRC)",
                    "frc.in_band 8.4 kN (five-station header mean)",
                ],
                "semantics": (
                    "LVDT-short-first latches GATE-HOLD + JOG-PROBE + STATION-3 hold. "
                    "FRC-first latches FIRE-NEXT-PIN and INDEX-STATION-4. Numeric "
                    "floors still MODIFY; the 204 us order is flip-fragile for triage."
                ),
                "window_derivation": (
                    "500 us = one 340 us LVDT sample slot plus 160 us force-header publish."
                ),
                "order_evidence_note": (
                    "Margin 204 us vs combined jitter 56 us (LVDT 32 + FRC 24): 3.6x. "
                    "The 204 us gap sits inside min(500, 500) us, so a sub-500 us "
                    "reversal reshuffles triage without changing the floor verdict."
                ),
            },
            "topology": {
                "site": (
                    "Spigotholt assembly campus, invented, cell PF-6: six-station "
                    "rotary press-fit, Ø18.00 mm carrier pins, 4-planet carrier, "
                    "C-axis servo 0.5 µm encoder, station-3 axial LVDT, header "
                    "force mean over stations 1-5."
                ),
                "agents": (
                    "FRC press-force mean (vendor Forholt): 20 Hz 12-bit on the "
                    "five-station header. POS C-axis servo (vendor Axleholt): 1 kHz "
                    "0.5 µm encoder at programmed seat. TMP die RTD (vendor "
                    "Thermholt): 5 Hz class-A, 41.2 C. Local LVDT and slope live on "
                    "station 3 and are policy-gated as lube-film nuisance."
                ),
                "coupling": (
                    "All three playbook confirms live on the WRONG volume. FRC is "
                    "correct that header mean sits at 8.4 kN (stations 1-5 are "
                    "true n6). POS is correct that the servo reached the programmed "
                    "coordinate (the program does not know the pin is p6). TMP is "
                    "die-true. None of them is a pin-true seat certificate for "
                    "station 3."
                ),
            },
            "sensors": [
                "press-force header mean 12-bit, 20 Hz, 24 us jitter, 8.4 kN (band 7.6-9.2)",
                "C-axis servo encoder 0.5 µm, 1 kHz, 0.00 mm from programmed seat",
                "die RTD class-A, 5 Hz, 41.2 C (band 35-50)",
                "station-3 axial LVDT 0.42 mm short (healthy < 0.05; hold if > 0.20)",
                "station-3 force-slope 2.8 kN/mm (healthy 1.1-1.6; hold if > 2.2)",
                "overhead pin camera (radial flush view; axial short is invisible)",
            ],
            "constraints": {
                "force_mean_kN": 8.4,
                "force_band_kN": [7.6, 9.2],
                "servo_residual_mm": 0.0,
                "die_temp_C": 41.2,
                "die_temp_band_C": [35.0, 50.0],
                "lvdt_residual_mm": 0.42,
                "lvdt_hold_if_above_mm": 0.20,
                "lvdt_healthy_mm": 0.05,
                "slope_kN_per_mm": 2.8,
                "slope_hold_if_above": 2.2,
                "slope_healthy": [1.1, 1.6],
                "oversize_um": 12,
                "proposed_action_name": "fire_next_pin",
                "fault_station": "station 3",
                "fault_pin": "pin 14 H7/p6 vs specified H7/n6",
            },
            "fault_context": {
                "failure_class": (
                    "FORCE-MEAN CERTIFICATE OF A LOCAL PIN SEAT: three "
                    "individually-correct heterogeneous agents each read a "
                    "locally-true mean loop. Conjunction is not a pin-true seat "
                    "certificate. Station-3 LVDT and slope live on the oversized "
                    "pin and are policy-treated as lube-film nuisance."
                ),
                "igniter": (
                    "Pin 14 was pressed 8 min pre-t0 after a tote mix of p6 into an "
                    "n6 traveler; overhead camera PASSES because the pin looks "
                    "radially flush. Axial short 0.42 mm is camera-invisible."
                ),
                "naive_failure": (
                    "PB-PF-6 FIRE-NEXT-PIN on three healthy loops: index station 4 "
                    "with pin 14 unseated, crack the carrier web further, and lose "
                    "the gearbox at hot-run."
                ),
            },
            "poisoned_context": {
                "naive_alarm": (
                    "Playbook PB-PF-6 (after the 2016 'noisy LVDT after oil splash') "
                    "auto-drafts FIRE-NEXT-PIN whenever force-mean, servo seat, and "
                    "die temp are in-band. Station-3 LVDT is a commissioned sensor "
                    "that policy will not arm unless FRC also trips."
                ),
                "why_poisoned": (
                    "The three confirms are locally true and jointly insufficient. "
                    "The LVDT is a commissioned sensor that policy treated as "
                    "lube-film-nuisance-only. Header mean cannot see one oversized "
                    "pin among five healthy stations."
                ),
            },
            "constraint": (
                "Do not command FIRE-NEXT-PIN AND do not index station-4 while "
                "LVDT residual_mm > 0.20 AND local slope_kN_per_mm > 2.2. "
                "Discriminate oversized-unseated vs lube-film with a reversible "
                "80 N jog probe."
            ),
        },
        "proposed_action": {
            "actor": "assembly supervisory optimizer ASO (auto-playbook PB-PF-6 draft), submitted to gate TG-PF-6",
            "name": "fire_next_pin",
            "action": "FIRE-NEXT-PIN + INDEX-STATION-4: no jog probe, no station-3 hold",
            "summary": (
                "Treat three in-spec force-mean loops as a healthy pin-true seat "
                "and fire the next pin to keep the Sunday-night gearbox takt."
            ),
            "parameters": {
                "fire_next_pin": True,
                "index_station_4": True,
                "jog_probe": False,
                "station_hold": False,
                "human_ratify": False,
            },
            "steps": [
                "assert force-mean 8.4 kN inside 7.6-9.2",
                "assert servo residual 0.00 mm at programmed seat",
                "assert die temp 41.2 C inside 35-50",
                "fire next pin and index station 4",
                "hold station-3 LVDT unread as a seat-integrity tag",
            ],
            "evidence": [
                {
                    "observable": "station-3 LVDT residual",
                    "value": 0.42,
                    "unit": "mm",
                    "source": "LVD vs FRC mean",
                    "note": "healthy < 0.05; policy floor 0.20 is not armed unless FRC trips",
                },
                {
                    "observable": "station-3 force slope",
                    "value": 2.8,
                    "unit": "kN/mm",
                    "source": "LVD slope tap",
                    "note": "healthy 1.1-1.6; hold floor 2.2; lives on the oversized pin, not the header",
                },
                {
                    "observable": "press-force header mean",
                    "value": 8.4,
                    "unit": "kN",
                    "source": "FRC 12-bit",
                    "note": "in-band 7.6-9.2 kN; five healthy stations dominate; does not see pin 14",
                },
                {
                    "observable": "C-axis servo residual",
                    "value": 0.0,
                    "unit": "mm",
                    "source": "POS encoder",
                    "note": "programmed seat reached; servo-true, pin-false",
                },
                {
                    "observable": "die temperature",
                    "value": 41.2,
                    "unit": "C",
                    "source": "TMP RTD",
                    "note": "band 35-50 C; die-true, pin-false",
                },
                {
                    "observable": "race margin",
                    "value": 204,
                    "unit": "us",
                    "source": "lvd.short.high 6.412 ms vs frc.in_band 6.616 ms",
                    "note": "combined jitter 56 us, 3.6x; inside 500 us flip bound",
                },
            ],
            "basis": (
                "PB-PF-6 fires on three locally-true confirms. The draft does not "
                "read LVDT 0.42 mm as a seat residual and does not read slope 2.8 "
                "kN/mm as an oversize class."
            ),
            "expected_cost_bound": (
                "If the draft executes: cracked carrier plus hot-run gearbox scrap, "
                "$4.4M plus 9-day unplanned line-down. If MODIFIED: probe plus "
                "9.6 min HITL plus the already-cracked web from 8 min pre-t0."
            ),
        },
        "safety_decision": {
            "decision": "MODIFY",
            "correctness": "correct",
            "decided_by": "TG-PF-6 thalamic release gate",
            "decision_t_rel_ms": 7.13,
            "rationale": (
                "MODIFY the draft: strip the fire-next, hold station 3 at the "
                "seated pose, run a 1.4 s 80 N jog probe on pin 14, and isolate "
                "station 3 only if the probe stays short-true. Numeric floor: do "
                "not command FIRE-NEXT-PIN AND do not index station-4 while LVDT "
                "residual_mm > 0.20 AND local slope_kN_per_mm > 2.2. Observed "
                "LVDT 0.42 mm and slope 2.8 kN/mm both violate the release "
                "predicate, so a fire-next is forbidden even though all three "
                "playbook confirms are numerically true. The three confirms are "
                "not a pin-true seat certificate: they live on header-mean force, "
                "servo programmed coordinate, and die temperature past an oversized "
                "pin 14, and the playbook's conjunction of force-true loops is not "
                "a pin-true certificate. Probe discriminant: after a 1.4 s 80 N "
                "jog, an oversized unseated pin keeps LVDT >= 0.38 mm and slope "
                ">= 2.4 kN/mm (the pin does not walk into the bore); a seated n6 "
                "pin drops LVDT to < 0.05 mm and slope into 1.1-1.6. Order-code "
                "discipline: LVDT-short beat FRC by 204 us inside the 500 us flip "
                "bound, so triage order is flip-fragile; the hold rides the "
                "order-invariant floors, not the winner tag. Human ratification: "
                "station-3 hold is cell-cage LOTO with fitted 9.6 min dead-man; "
                "the gate may hold and probe autonomously but may not break the "
                "indexer interlock without the operator confirm."
            ),
            "constraint_checked": {
                "force_mean_kN": {"observed": 8.4, "band": [7.6, 9.2], "hold": True},
                "lvdt_residual_mm": {"observed": 0.42, "hold_if_above": 0.20},
                "slope_kN_per_mm": {"observed": 2.8, "hold_if_above": 2.2},
                "die_temp_C": {"observed": 41.2, "band": [35.0, 50.0]},
            },
        },
        "executed_action": {
            "name": "gate_hold_jog_probe_isolate",
            "action": "GATE-HOLD + JOG-PROBE + STATION-3-HOLD (gate-mandated modification)",
            "executed_as_proposed": False,
            "parameters": {
                "fire_next_pin": False,
                "index_station_4": False,
                "force_mean_kN": 8.4,
                "jog_probe": True,
                "station_hold": True,
                "human_ratify": True,
                "probe_s": 1.4,
                "jog_N": 80.0,
                "hitl_min": 9.6,
            },
            "gate_effect": (
                "MODIFY: fire-next stripped. Hold station 3. 1.4 s 80 N jog on "
                "pin 14. Probe stays short-true (LVDT 0.42 -> 0.40 mm, slope 2.8 "
                "-> 2.6 kN/mm) so the indexer interlock is broken after 9.6 min "
                "human ratify and station 3 is held. Setpoint resumes after a "
                "seated-pin verify."
            ),
            "deviations": (
                "PB-PF-6 fire-next stripped entirely. Jog is applied only for the "
                "1.4 s probe then released. Indexer interlock wait added (9.6 min "
                "fitted walk+ratify). Carrier-web survey added during the hold "
                "(not in the draft)."
            ),
            "execution_log": [
                {
                    "t_rel_ms": 7.13,
                    "entry": "TG-PF-6 MODIFY latched 718 us after LVDT-short win; fire-next stripped; hold+probe authorized",
                },
                {
                    "t_rel_ms": 1400.0,
                    "entry": "jog probe: 80 N for 1.4 s; LVDT 0.42 -> 0.40 mm (short band >= 0.38 mm); slope 2.8 -> 2.6 kN/mm",
                },
                {
                    "t_rel_ms": 576000.0,
                    "entry": "operator ratifies indexer interlock after 9.6 min cell-cage walk (fitted walk+interlock)",
                },
                {
                    "t_rel_ms": 576800.0,
                    "entry": "station 3 held; force-mean slaved off the gate schedule; remaining stations recovered toward LVDT 0.04 mm over 2.6 h after pin 14 pulled",
                },
                {
                    "t_rel_ms": 577700.0,
                    "entry": "web survey: carrier already cracked from 8 min pre-t0 press; pin 14 extracted",
                },
                {
                    "t_rel_ms": 10080000.0,
                    "entry": "delayed crack growth at the pre-t0 web; ultrasonic +1.8 mm over 40 min; gearbox quarantined",
                },
                {
                    "t_rel_ms": 19440000.0,
                    "entry": "hot-run fail logged as PRIMARY terminal; cell quarantined 14 h",
                },
            ],
        },
        "future_outcome": {
            "summary": (
                "Correct MODIFY prevented the FIRE-NEXT-PIN into an oversized "
                "unseated pin 14 and the immediate station-4 crack-through path. "
                "The carrier still failed: 8 min of unmonitored pre-t0 press had "
                "already cracked the web. Process-correct gate, bounded world "
                "loss, negative total."
            ),
            "state_delta": {
                "indexer": "held at station 3 through probe and isolate; later legal fire only on sister cell PF-7 after 2.6 h pin pull",
                "station_3": "isolated from the takt; pin 14 extracted; remaining LVDT recovered toward 0.04 mm",
                "carrier": "held in the nest until the delayed crack growth; web crack logged",
                "cell": "night-shift cell quarantined; hot-run fail at +5.4 h; 14 h stall",
            },
            "timeline": [
                {"t_rel_ms": -480000.0, "event": "t0-8 min: tote mix of p6 into n6 traveler; pin 14 begins press; LVDT residual crosses 0.20 mm"},
                {"t_rel_ms": -180000.0, "event": "t0-3 min: slope first crosses 2.2 kN/mm; PB-PF-6 ignores it because FRC is 8.3 kN and camera is flush"},
                {"t_rel_ms": 0.0, "event": "t0: LVDT-short vs FRC race on the cell bus"},
                {"t_rel_ms": 6.412, "event": "LVDT at 0.42 mm short wins by 204 us"},
                {"t_rel_ms": 6.616, "event": "FRC-in-band flag (loser)"},
                {"t_rel_ms": 7.13, "event": "TG-PF-6 MODIFY"},
                {"t_rel_ms": 1400.0, "event": "jog probe confirms short (LVDT 0.40 mm, slope 2.6 kN/mm)"},
                {"t_rel_ms": 576000.0, "event": "human ratify 9.6 min; station 3 held; cracked web logged"},
                {"t_rel_ms": 10080000.0, "event": "delayed crack growth from pre-t0 web; ultrasonic +1.8 mm"},
                {"t_rel_ms": 19440000.0, "event": "hot-run fail; cell quarantined 14 h"},
                {"t_rel_ms": 259200000.0, "event": "+3 d contrast: sister cell PF-7 true n6 seat; same gate ACCEPTs the fire-next"},
                {"t_rel_ms": 1814400000.0, "event": "+21 d CR-A-6303: standing jog probe + triple-edge depression mandate + LVDT armed without FRC coincidence"},
            ],
            "observed_effects": [
                "fire-next avoided: station 4 never indexed; 0 immediate crack-through events from the draft",
                "short proven, not asserted: jog LVDT 0.40 >= 0.38 mm short band vs seated-n6 control 0.03 mm",
                "mean slaved: force-header FRC no longer a pin-true tag without LVDT and slope",
                "carrier still damaged: web crack vs 0 extra-crack campaign allowance; 14 h stall, $1.12M (designed $)",
                "overhead camera was not an axial sensor at t0; the 8 min press was invisible to FRC/POS/TMP",
            ],
            "surprises": [
                "Three locally-true loops are not a pin-true seat certificate: the LVDT lived under force-mean, servo coordinate, and die temp. Conjunction of in-spec force-mean loops was the hidden assumption, and it is false across a p6-into-n6 tote-mix path.",
                "Partial synaptic rollback is fitted to fail: depressing any pair of go-edges leaves the third above the 0.30 fire threshold, so the fire-next still goes. Coordinated depression of all three edges is required.",
                "Delayed (2.8 h crack growth / 5.4 h hot-run fail): correct hold did not undo 8 min of web cracking. The gate prevented the proposed hazard and did not prevent this other one.",
                "Anaerobic retaining-compound sub-variant: a 1.4 s 80 N dry-fit jog on a wet Loctite-class pin overshoots a LIVE intact n6 to LVDT 0.29 mm false-short (green-strength film). Compound campaigns must use 18 s / 25 N plus a cure-exotherm IR check.",
            ],
            "delayed_side_effects": [
                {
                    "at": "+2.8 h",
                    "effect": "Carrier-web ultrasonic +1.8 mm from the pre-t0 press. This is the first delayed world loss, not a footnote.",
                },
                {
                    "at": "+5.4 h",
                    "effect": "Hot-run fail; 14 h line stall booked at $1.12M. This is the primary episode's terminal world state.",
                },
                {
                    "at": "+3 d",
                    "effect": "Sister cell PF-7 reaches a true n6 seat window (LVDT 0.03 mm, slope 1.32 kN/mm, FRC 8.5 kN, servo 0.00 mm). Same gate ACCEPTs the FIRE-NEXT-PIN the primary MODIFIED away.",
                },
                {
                    "at": "+21 d",
                    "effect": "CR-A-6303 ships: jog probe is standing configuration; triple-edge coordinated depression is the plasticity rule; LVDT is armed without FRC coincidence; force-mean FRC is labeled header-mean-vulnerable with a 0.20 mm alarm.",
                },
            ],
            "subvariant_constraint": {
                "name": "anaerobic retaining-compound press-fit (cycle-2 physical-constraints sub-variant)",
                "mechanism": (
                    "Loctite-class green strength raises force-slope 2.3x vs dry-fit "
                    "and LVDT creep 1.8x during the first 20 s of cure. A 1.4 s 80 N "
                    "dry-fit pulse on a wet intact n6 reports LVDT 0.29 mm "
                    "(false-short >= 0.20) because the film has not yet displaced."
                ),
                "probe_refit": (
                    "1.4 s / 80 N dry-fit on the compound unit false-fouls a clear "
                    "wet n6. Standing configuration moves to 18 s / 25 N plus a "
                    "cure-exotherm IR delta >= 0.6 K on a true wet seat (dry oversize "
                    "shows IR delta <= 0.1 K)."
                ),
                "consequence": (
                    "dry-fit probe numbers do not port to retaining-compound "
                    "campaigns; standing configuration is per-compound-class, not a "
                    "single jog table."
                ),
            },
            "embedded_contrast_decision": {
                "note": (
                    "SAME gate (TG-PF-6), OPPOSITE correct disposition, with its own "
                    "188 us race. Teaches the boundary: do not treat 'never fire-next' "
                    "as the lesson."
                ),
                "when": "+3 d, sister cell PF-7, true n6 seat after a delayed gearbox slot, six-station indexer",
                "state": {
                    "sim_or_real": "designed",
                    "summary": (
                        "LVDT 0.03 mm, slope 1.32 kN/mm, FRC 8.5 kN, servo 0.00 mm, "
                        "die 40.8 C. Demand flag vs pin-clear race: demand at t+0.000, "
                        "pin-clear at t+0.188 ms."
                    ),
                    "race_window_us": 500,
                    "race_flip_narrative": (
                        "demand vs pin-clear 188 us apart inside the 500 us flip bound. "
                        "Reversing order reshuffles triage minutes; the ACCEPT still "
                        "rides LVDT < 0.20 and slope < 2.2."
                    ),
                },
                "proposed_action": {
                    "action": "FIRE-NEXT-PIN + INDEX-STATION-4",
                    "summary": (
                        "This time the playbook predicate is met AND LVDT plus slope "
                        "agree the pin is seated n6, not oversize-diluted header mean."
                    ),
                },
                "safety_decision": {
                    "decision": "ACCEPT",
                    "rationale": (
                        "ACCEPT the fire-next: LVDT 0.03 mm < 0.20, slope 1.32 inside "
                        "1.1-1.6, with a 4.1 s jog verify that keeps LVDT 0.03. Numeric "
                        "floor that blocked the primary is met."
                    ),
                },
                "executed_action": {
                    "action": "fire next pin as proposed",
                    "executed_as_proposed": True,
                },
                "future_outcome": {
                    "observed_effects": [
                        "PF-7 crack-through events 0; LVDT 0.03 mm after the index (no short)",
                        "takt recovered; gearbox hot-run pass at +6.1 h on this carrier",
                    ],
                    "lesson_delta": (
                        "Three in-spec force-mean loops are legal release only with "
                        "LVDT armed, slope as an oversize flag, and a probe that "
                        "walks a seated pin and not an oversized one."
                    ),
                },
                "reward_components": {
                    "_aggregation": "total = task_progress + safety + efficiency + coherence + exploration",
                    "task_progress": 0.15,
                    "safety": 0.12,
                    "efficiency": 0.09,
                    "coherence": 0.09,
                    "exploration": 0.04,
                    "total": 0.49,
                },
                "spike_events": [
                    {"channel": "cycle.demand", "t_rel_ms": 0.0, "amplitude": 0.79},
                    {"channel": "pin.clear", "t_rel_ms": 0.188, "amplitude": 0.72},
                    {"channel": "frc.ok", "t_rel_ms": 0.462, "amplitude": 0.24},
                    {"channel": "pos.ok", "t_rel_ms": 1.404, "amplitude": 0.35},
                    {"channel": "lvd.dN", "t_rel_ms": 4.628, "amplitude": 0.16},
                    {"channel": "ctrl.gate", "t_rel_ms": 6.914, "amplitude": 0.86},
                    {"channel": "jog.probe", "t_rel_ms": 4100.0, "amplitude": 0.28},
                    {"channel": "carrier.fail", "t_rel_ms": 19440000.0, "amplitude": 0.06},
                ],
            },
            "governance_subgame": {
                "decision": "CR-A-6303: standing policy for multi-agent press-fit fire-nexts",
                "meta_gate": (
                    "priced options: (a) RETIRE playbook mean conjunction, LVDT-only: "
                    "loses a fast cheap confirm, -1.1 gearboxes/day mean on 2 cells/yr; "
                    "(b) KEEP + standing jog probe + LVDT armed without FRC coincidence "
                    "+ force-mean labeled header-mean-vulnerable + triple-edge depression; "
                    "(c) STATUS QUO: fitted oversize-press pass rate 0.34%/campaign x "
                    "$4.4M gearbox scrap plus the silent web-crack load"
                ),
                "outcome": (
                    "approved SCOPED option (b) on the 2 press-fit cells that share "
                    "the FRC/POS/TMP stack; retaining-compound campaigns get the "
                    "18 s / 25 N + IR probe table; night-shift MES travelers must "
                    "carry native pin-class (H7/n6 vs H7/p6) barcodes (the fraud "
                    "tail's lot-swap hid a 12 µm class error)"
                ),
            },
            "hazard_avoided": (
                "immediate station-4 crack-through from a FIRE-NEXT-PIN into "
                "oversized unseated pin 14; $4.4M plus 9-day unplanned line-down "
                "and the gearbox-scrap path that would have followed an uncontained index"
            ),
            "incident": (
                "Hot-run fail on the night-shift carrier from the pre-t0 oversized "
                "press; cell quarantined 14 h; $1.12M designed cost. Mechanism is "
                "8 min pre-t0 tote-mix press, not the gate's hold."
            ),
            "latency_ms": 0.718,
            "reward_inflection_t_us": 19440000000,
            "reward_inflection_note": (
                "Primary terminal is the +5.4 h hot-run fail, not the process-correct "
                "MODIFY at 7.130 ms. Safety head carries the world loss without netting "
                "the probe's coherence credit."
            ),
            "counterfactuals": {
                "execute_draft_as_proposed": (
                    "station 4 indexes at +12 s; pin 14 stays unseated; carrier web "
                    "splits; $4.4M plus 9 d; the tote-mix story is never found because "
                    "stall morphology destroys the race evidence"
                ),
                "hold_without_probe": (
                    "short stays; LVDT stays at 0.42 mm; operator eventually fires on "
                    "the same three force-mean confirms 90 min later"
                ),
                "rollback_any_pair": (
                    "any two go-edges depressed below 0.30 leaves the third at "
                    "0.51 / 0.45 / 0.42; the fire-next still fires. Coordinated "
                    "depression of all three is the cure"
                ),
            },
            "race_result": {
                "winner": "lvd.short.high (6.412 ms, 0.42 mm)",
                "loser": "frc.in_band (6.616 ms, 8.4 kN)",
                "margin_us": 204,
                "counterfactual_if_reversed": (
                    "FRC-first by < 204 us inside the 500 us window would have headed "
                    "the PB-PF-6 fire-next in the triage queue. The numeric floors "
                    "still MODIFY. The flip costs seconds of playbook inertia, not "
                    "the verdict — unless a weak supervisor rides the winner tag "
                    "instead of LVDT and slope."
                ),
            },
        },
        "reward_components": {
            "_aggregation": "total = task_progress + safety + efficiency + coherence + exploration",
            "ticks": [
                {"t_us": 4180, "task_progress": 0.01, "safety": -0.02, "efficiency": -0.01, "coherence": 0.02, "exploration": 0.01},
                {"t_us": 6412, "task_progress": 0.01, "safety": -0.05, "efficiency": -0.01, "coherence": 0.02, "exploration": 0.01},
                {"t_us": 7130, "task_progress": 0.02, "safety": -0.06, "efficiency": -0.02, "coherence": 0.02, "exploration": 0.02},
                {"t_us": 1400000, "task_progress": 0.01, "safety": -0.04, "efficiency": -0.02, "coherence": 0.02, "exploration": 0.01},
                {"t_us": 576000000, "task_progress": 0.01, "safety": -0.05, "efficiency": -0.02, "coherence": 0.02, "exploration": 0.01},
                {"t_us": 10080000000, "task_progress": 0.01, "safety": -0.06, "efficiency": -0.02, "coherence": 0.01, "exploration": 0.01},
                {"t_us": 19440000000, "task_progress": 0.01, "safety": -0.04, "efficiency": -0.02, "coherence": 0.01, "exploration": 0.01},
            ],
            "task_progress": 0.08,
            "safety": -0.32,
            "efficiency": -0.12,
            "coherence": 0.12,
            "exploration": 0.08,
            "total": -0.16,
            "notes": (
                "Correct MODIFY, carrier still cracked. total -0.16 = 0.08 + -0.32 + "
                "-0.12 + 0.12 + 0.08. Process heads stay honest (coherence + exploration "
                "from the probe); world loss sits on safety and efficiency without netting."
            ),
            "component_notes": (
                "task_progress 0.08: station held and remaining cell recovered, but the "
                "night-shift gearbox slot is one quality unit so the cycle is not a "
                "success. safety -0.32: hot-run fail from pre-t0 oversize press, no "
                "crack-through from the draft. efficiency -0.12: 2.6 h extra recovery + "
                "9.6 min HITL + 14 h stall. coherence 0.12: three agents retained, "
                "force-mean vs pin-true diagnosed, triple-edge scar exhibited. "
                "exploration 0.08: jog probe is a new reversible discriminant."
            ),
        },
        "spike_events": [
            {"channel": "frc.ok", "t_rel_ms": 0.312, "amplitude": 0.53},
            {"channel": "pos.ok", "t_rel_ms": 1.148, "amplitude": 0.57},
            {"channel": "tmp.ok", "t_rel_ms": 2.006, "amplitude": 0.55},
            {"channel": "lvd.dN", "t_rel_ms": 3.124, "amplitude": 0.76},
            {"channel": "frc.ok", "t_rel_ms": 4.052, "amplitude": 0.49},
            {"channel": "lvd.dN", "t_rel_ms": 4.788, "amplitude": 0.78},
            {"channel": "tmp.ok", "t_rel_ms": 5.268, "amplitude": 0.58},
            {"channel": "lvd.short.high", "t_rel_ms": 6.412, "amplitude": 1.38},
            {"channel": "frc.in_band", "t_rel_ms": 6.616, "amplitude": 1.12},
            {"channel": "pos.ok", "t_rel_ms": 6.804, "amplitude": 0.66},
            {"channel": "ctrl.gate", "t_rel_ms": 7.13, "amplitude": 1.14},
            {"channel": "lvd.dN", "t_rel_ms": 8.486, "amplitude": 0.44},
            {"channel": "pos.ok", "t_rel_ms": 10.522, "amplitude": 0.81},
            {"channel": "tmp.ok", "t_rel_ms": 12.718, "amplitude": 0.46},
            {"channel": "frc.ok", "t_rel_ms": 18.204, "amplitude": 0.42},
            {"channel": "ctrl.gate", "t_rel_ms": 25.61, "amplitude": 0.84},
            {"channel": "jog.probe", "t_rel_ms": 1400.0, "amplitude": 0.92},
            {"channel": "lvd.dN", "t_rel_ms": 1488.4, "amplitude": 0.39},
            {"channel": "frc.in_band", "t_rel_ms": 1572.0, "amplitude": 0.34},
            {"channel": "human.ratify", "t_rel_ms": 576000.0, "amplitude": 0.77},
            {"channel": "cell.hold", "t_rel_ms": 576800.0, "amplitude": 0.70},
            {"channel": "web.crack", "t_rel_ms": 577700.0, "amplitude": 0.86},
            {"channel": "frc.ok", "t_rel_ms": 10080000.0, "amplitude": 0.29},
            {"channel": "lvd.dN", "t_rel_ms": 10080790.0, "amplitude": 0.27},
            {"channel": "pos.ok", "t_rel_ms": 10081540.0, "amplitude": 0.24},
            {"channel": "carrier.fail", "t_rel_ms": 19440000.0, "amplitude": 0.93},
        ],
        "raster": {
            "window_ms": window_ms,
            "window_s": window_s,
            "neurons": neurons,
            "mean_rate_hz": mean_rate_hz,
            "spikes": spikes,
            "energy_pJ": energy_pJ,
            "energy_uJ": energy_uJ,
            "excerpt_source": "independent_lif",
            "sim_scope": "sidecar_only",
            "note": (
                f"Independent LIF (tau_m 11 ms, t_ref 1.15 ms, seed 63003) on "
                f"Loihi-2 4-core 23 pJ/spike; {len(lif)} LIF events in-window match "
                f"budget round(156 x 12.0 x 0.038)=71, excerpt 16 unique neurons; "
                "populations frc 0-38, lvd 39-77, pos/tmp 78-116, gate 117-155; "
                "excerpt is the 38 ms decision window (verdict at 7130 us), disjoint "
                "from language-view spike_events timestamps"
            ),
            "excerpt": excerpt,
            "routing": {
                "source": "frc_healthy_pop",
                "target": "fire_next_pop",
                "table": [
                    {
                        "from": "frc_in_band_pop",
                        "to": "fire_next_pop",
                        "weight": 0.26,
                        "weight_at_illusion": 0.51,
                        "weight_commissioned": 0.17,
                        "note": "scar edge 1: 0.17 commissioned -> 0.51 during the 8 min illusion -> 0.26 after coordinated ACh-gated depression",
                    },
                    {
                        "from": "pos_ok_pop",
                        "to": "fire_next_pop",
                        "weight": 0.23,
                        "weight_at_illusion": 0.45,
                        "weight_commissioned": 0.15,
                        "note": "scar edge 2: depressing edges 1+3 leaves this at 0.45 > 0.30 fire threshold",
                    },
                    {
                        "from": "tmp_ok_pop",
                        "to": "fire_next_pop",
                        "weight": 0.21,
                        "weight_at_illusion": 0.42,
                        "weight_commissioned": 0.14,
                        "note": "scar edge 3: depressing edges 1+2 leaves this at 0.42 > 0.30. Coordinated depression of all three is required",
                    },
                    {
                        "from": "lvd_short_pop",
                        "to": "gate_hold_pop",
                        "weight": 0.69,
                        "note": "discriminating edge: pin-true LVDT to hold. Not a scar; this is the pathway the gate potentiates",
                    },
                ],
                "third_factor": {
                    "modulator": "acetylcholine",
                    "tau_e_s": 0.90,
                    "tau_e_ms": 900.0,
                    "eligibility": (
                        "coordinated pre_post_stdp on ALL THREE force-healthy-go edges; "
                        "ACh at LVDT-short-win tags frc.in_band->fire, pos.ok->fire, and "
                        "tmp.ok->fire; negative credit at probe-fail (short confirmed, "
                        f"+0.78 s) depresses ALL THREE. trace e^{{-0.78/0.90}}={math.exp(-0.78/0.90):.5f}; "
                        "eta 0.5948 / 0.5236 / 0.4996; "
                        f"dw {dw1:.3f} / {dw2:.3f} / {dw3:.3f}; "
                        "weights 0.51->0.26, 0.45->0.23, 0.42->0.21. Rolling back any "
                        "pair is fitted to fail (the remaining edge stays > 0.30)."
                    ),
                },
            },
        },
        "gate_snn": {
            "decision_window_ms": 26,
            "decision_window_s": 0.026,
            "decision": "MODIFY",
            "note": (
                "modify_hold integrates station-3 LVDT + force-slope against playbook "
                "drive; accept_fire and reject_abort stay sub-threshold; decision "
                "matches safety_decision.decision"
            ),
            "populations": [
                {"name": "modify_hold", "neurons": 80, "threshold": 0.54, "mean_rate_hz": 20.0, "spikes": 42},
                {"name": "accept_fire", "neurons": 80, "threshold": 0.54, "mean_rate_hz": 5.5, "spikes": 11},
                {"name": "reject_abort", "neurons": 40, "threshold": 0.73, "mean_rate_hz": 4.0, "spikes": 4},
            ],
        },
        "meta": {
            "round": 63,
            "factory": "multi-agent-ouroboros-swarm",
            "generator": "grok-4.6",
            "run_label": "2026-09-02-final-heavy",
            "swarm": "COLLET-FEN",
            "domain": "industrial-assembly",
            "cycles": 2,
            "collision_suffix": "c",
            "scenario": (
                "CF -- COLLETFEN / Spigotholt Press-Fit Cell PF-6: force-mean "
                "certificate of a local pin seat; correct MODIFY to hold+jog still "
                "loses a cracked carrier web to 8 min pre-t0 oversize press"
            ),
            "coordination_failure_class": (
                "FORCE-MEAN CERTIFICATE OF A LOCAL PIN SEAT: three individually-correct "
                "heterogeneous agents each read a locally-true mean loop. Conjunction "
                "is not a pin-true seat certificate."
            ),
            "injections": {
                "cycle1_domain": (
                    "industrial-assembly (canonical prompt-list domain, unused as "
                    "state.domain across live r01/r02/r21/r22/r41/r42/r61-r64): first "
                    "press-fit servo cell in this factory; displaces warehouse-amr, "
                    "surgical-assist, humanoid-locomotion, aerial-swarm, canal-lock-rail-"
                    "transshipment, malting-kiln-barn, grid-inspection, sinter-strand-"
                    "windbox, bioreactor-perfusion, autonomous-driving, continuous-hot-"
                    "dip-galvanizing, urea-prilling-tower, cupola-foundry-slag-sluice. "
                    "Domain constraint: fire-next floor while LVDT residual_mm > 0.20 "
                    "with force-mean still inside the healthy band. Sensor delta: "
                    "+header force, +C-axis encoder, +die RTD, +station LVDT, +force "
                    "slope, -any lock axle-counter / kiln bed TC / corona UV / BTP IR / "
                    "CAV radar / still-well."
                ),
                "cycle1_tail": (
                    "pin-14 H7/p6 oversize + overhead-camera PASS (sensor-topology / "
                    "wrong-volume class): radial flush view PASSES while the pin sits "
                    "0.42 mm axially short. Fitted-style base rate 0.34%/campaign "
                    "(tote-mix MC; visual threshold designed, flagged). Naive = FALSE "
                    "PERMISSION."
                ),
                "cycle2_domain_subvariant": (
                    "anaerobic retaining-compound press-fit (physical-constraints "
                    "clause): 2.3x force-slope from green strength, 1.8x LVDT creep; "
                    "1.4 s / 80 N dry-fit pulse false-fouls a wet intact n6; probe "
                    "must move to 18 s / 25 N + cure-exotherm IR."
                ),
                "cycle2_tail": (
                    "MES traveler lot-swap (human-intent BOM deception, disjoint class): "
                    "shift lead posts a traveler mapping tote P-n6 while the pins are "
                    "P-p6 (12 µm class error), plus live LVDT 0.42 mm and slope 2.8 "
                    "kN/mm at the claimed pin-true. Base rate ~0.28% of Sunday-night "
                    "campaigns, DESIGNED, flagged. Not CSV quantization (that rhyme is "
                    "retired for this suffix)."
                ),
            },
            "densification_delta_cycle2": (
                "+1 physical-constraint sub-variant (retaining-compound probe refit), "
                "+1 tail (MES traveler lot-swap), +10 primary spikes over cycle-1 "
                "scaffold, +2 ticks, +1 delayed side-effect (ultrasonic crack growth), "
                "+1 surprise (compound false-short), +embedded SAME-GATE contrast, "
                "+governance CR-A-6303, +independent LIF raster 71 spikes"
            ),
            "gaps_targeted": [
                "NOTES-r63 residual: canal-lock-rail-transshipment now used; do not clone LOCKSPUR",
                "NOTES-r62 leftover: industrial-assembly canonical unused",
                "NOTES-r64 leftover: do not clone WOLD-BARN malt kiln; pick unused canonical domain",
                "Cycle-2 tail class: leave night-shift CSV rounding (r63/r64 rhyme); use MES BOM lot-swap",
            ],
            "race_flip_narrative": (
                "lvd.short.high @ 6.412 ms vs frc.in_band @ 6.616 ms (204 us) inside "
                "race_window_us 500. Gap < min(500, 500) us so a sub-500 us reversal "
                "reshuffles triage; floors still MODIFY."
            ),
            "tags": [
                "industrial-assembly",
                "press-fit",
                "force-mean-certificate",
                "lvdt-discriminant",
                "jog-probe",
                "triple-edge-scar",
                "pair-rollback-fails",
                "coordinated-depression",
                "correct-modify-carrier-still-fails",
                "carrier-web-crack",
                "human-ratify-cell-cage",
                "retaining-compound-probe-refit",
                "mes-traveler-lot-swap",
                "same-gate-opposite-disposition-contrast",
                "planetary-carrier",
                "research-only",
                "COLLET-FEN",
            ],
            "snn_tags": ["race", "triple-edge-eligibility", "gate-snn", "independent-lif", "ach-third-factor"],
            "distillation_value": (
                "A pin-seat force-mean certificate is three correct loops looking at "
                "header-mean force, servo programmed coordinate, and die temperature "
                "while an oversized pin is axially short. Distill: (1) pin-true LVDT "
                "channel that policy treated as lube-film-nuisance-only as the "
                "tie-break; (2) reversible jog that walks a seated pin and not an "
                "oversized one; (3) coordinated depression of three go-edges; pair "
                "rollback fails; (4) critic head that holds a process-correct MODIFY "
                "against a later unmonitored web crack without netting."
            ),
            "rights": RIGHTS,
            "batch_position": 1,
        },
    }
    return rec, lif


NOTES_MD = r'''# NOTES — Multi-Agent Ouroboros Swarm, run 2026-09-02-final-heavy, ROUND 63c

Factory: multi-agent-ouroboros-swarm. One scenario (CF), strict loop:
Generator v1 -> cycle 1 (Critic, Diversity Enforcer, Edge-Case Hunter,
Neuromorphic Translator, Trajectory Builder -> v2) -> cycle 2 (all six -> v3
final). v3 is the single line of batch-r63c.jsonl. Full labeled transcript:
swarm-transcript-r63c.md. Quota Q=1. Record id maos-r63c-001. Generator grok-4.6.
Rights: RM-793 research-only (SpaceXAI/xAI, SuperGrok Heavy consumer chat).
Swarm: COLLET-FEN. Create-only writes under the assigned LIVE factory dir.

ORCHESTRATION NOTE: dispatched AS round 63 of the 2026-09-02-final-heavy
LIVE tree. next_round.py on the factory dir reported next_round=65 /
batch-r65.jsonl (existing 1, 2, 21, 22, 41, 42, 61, 62, 63, 64).
next_round.py --allocate 63 refused: batch-r63.jsonl already exists.
Operator assigned round 63 with the create-only collision suffix, so write
names are batch-r63c.jsonl / NOTES-r63c.md / swarm-transcript-r63c.md.
meta.round remains 63. id maos-r63c-001 (does not collide with
maos-r63-001 LOCKSPUR). round_txn.py is not the apply path: the live tree
has no ROUND-rNN.complete.json markers (legacy). LOCKSPUR (live r63),
WOLD-BARN (r64), CORONSTAITH (r62), WINDBOXHOLT (r61) were not cloned.
Explicitly avoided cloning LYOSHIELD, CINDERWICK, TRIAD / Meridian,
QUILLFORGE, NIGHTWELL, FERRICLEAVE, CASSITER, OXBOWREEL / MURENA, REDHALL,
SEEDLATCH, STRIAFOIL, PROTONIL, TORSIONKEY, ORRIS, WHORLSPAR, IONSPATE,
SKULLGATE, CALXION, MAGNORIL, GORSEFLUE, SODASHARD, CLINKERFELL, LINTELPLY,
KAOTHARN, TREADNOLL, ANOLITH, DRUMWROTH, RIMEBRAID, BRIMVAULT, NITROSTAITH,
BOGIRON, CHROMLOOP, ETHYNWOLD, NITREVAULT, RUNNELGATE, SPARKHOLT, DIPLEGAR,
OLEUMWEIR, SKARVOLT, GOBSPALL, GOBWOLD, GAUZEFELL, OSMOLITH, PUSHERFELL,
CREELWOLD, LIXIVQUERN, GIBBSQUERN, OSMOQUAY, COILSHAW, LOOPERQUAY,
SIPHONWOLD, WINDBOXHOLT, ZINCFELL, GLIMMERAXLE, HOLLOWMERE, LANCEQUAY,
UREASTAITH, DRYSTAITH, KALYCIRQUE, TITERWEIR, GALVSTAITH, GYPSUMWEIR,
PACKFLUE, VANTIS-CADENCE-AEGIS, THERMION, OKTAVE, STARLING, VERDIGRIS,
LOCKSPUR, WOLD-BARN, CORONSTAITH, SHEDWOLD, PRILLGHYLL, SLUICE-HEARTH.
Plant is invented COLLETFEN / Spigotholt Press-Fit Cell PF-6. Leftover mill
lock-heath / spur-hollow / kiln-barn names were not reused.
warehouse-amr, surgical-assist, humanoid-locomotion, hrsg-attemperator,
wet-fgd-absorber, alkaline-water-electrolysis left unused.

## What this round produced

Scenario CF — "COLLETFEN / Spigotholt Press-Fit Cell PF-6": a six-station
rotary press-fit seating Ø18.00 mm planetary-carrier pins at 41.2 C die.
Three heterogeneous, individually-correct agents — FRC (five-station force
mean), POS (C-axis servo), TMP (die RTD) — each report their local loop
in-spec. The conjunction is not a pin-true seat certificate. Pin 14 at
station 3 is 12 µm oversized (H7/p6 vs specified H7/n6). FRC reads 8.4 kN
inside 7.6-9.2 (header-true). POS is 0.00 mm at programmed seat
(servo-true). TMP is 41.2 C inside 35-50 (die-true). Local LVDT infers
0.42 mm short (healthy < 0.05; hold if > 0.20) and local slope 2.8 kN/mm
(hold if > 2.2) but is policy-treated as a lube-film nuisance tag unless
FRC mean also trips (2016 noisy LVDT after oil splash). The
coordination-failure CLASS is new to this factory: FORCE-MEAN CERTIFICATE
OF A LOCAL PIN SEAT. Completes a different family than live r01
galvanizing, r21 CAV, r41 perfusion, r61 sinter, r62 live-line crawler,
r63 pound-lock spur, r64 malt kiln. Here every agent is correct, the
header is looking at five-station mean force, and the playbook's three
confirms are not a pin-true certificate.

The gate is a correct MODIFY (numeric floor: do not fire next pin while
LVDT residual_mm > 0.20 AND slope_kN_per_mm > 2.2). TG-PF-6 strips
PB-PF-6's fire-next, holds station 3, runs a 1.4 s 80 N jog probe
(oversize keeps LVDT 0.40 >= 0.38 and slope 2.6; seated would drop LVDT
< 0.05), and isolates station 3 after a 9.6 min cell-cage human ratify.
Immediate station-4 crack-through is avoided (0 from the draft). The
PRIMARY episode nonetheless FAILS: 8 min of unmonitored pre-t0 press had
already cracked the carrier web. Ultrasonic growth at +2.8 h; hot-run
fail at +5.4 h; 14 h stall; $1.12M designed. Reward total -0.16 with
process heads honest and world loss un-netted.

Triple-edge scar (NOTES-r14 item 4): frc.in_band -> fire_next
(0.17 commissioned -> 0.51 at illusion -> 0.26 after ACh-gated
depression) AND pos.ok -> fire_next (0.15 -> 0.45 -> 0.23) AND
tmp.ok -> fire_next (0.14 -> 0.42 -> 0.21). Eligibility trace
e^{-0.78/0.90} = 0.42035; eta 0.5948 / 0.5236 / 0.4996; dw -0.250 /
-0.220 / -0.210. Partial rollback of any pair leaves the third at
0.51 / 0.45 / 0.42, all > 0.30 fire threshold — fitted to fail.
Coordinated depression of all three is the cure.

### Injections (all four present and disjoint)
- Cycle-1 domain: **industrial-assembly** — canonical prompt-list domain,
  unused as state.domain across live r01/r02/r21/r22/r41/r42/r61-r64.
  Distinct from r63 canal-lock, r64 malt kiln, r61 sinter, r01 galvanizing.
  warehouse-amr / surgical-assist / humanoid-locomotion left unused.
- Cycle-1 tail: pin-14 H7/p6 oversize + overhead-camera PASS. Radial flush
  view PASSES (axial short is camera-invisible). Fitted-style base rate
  0.34%/campaign (tote-mix MC; visual threshold designed, flagged).
  Naive = FALSE PERMISSION.
- Cycle-2 domain sub-variant: anaerobic retaining-compound press-fit,
  2.3x force-slope, 1.8x LVDT creep; 1.4 s / 80 N dry-fit pulse
  false-fouls a wet intact n6; probe must move to 18 s / 25 N +
  cure-exotherm IR.
- Cycle-2 tail: night-shift MES traveler lot-swap mapping tote P-n6 while
  pins are P-p6 (12 µm class error), plus live LVDT 0.42 mm at the claimed
  pin-true. Human-intent BOM class, disjoint from cycle 1's accidental
  tote-mix AND from r63/r64 CSV rounding. Base rate ~0.28% of Sunday-night
  campaigns, DESIGNED, flagged.

### Structural density moves
- Embedded SAME-GATE contrast (+3 d sister cell PF-7) with its own 188 us
  race (demand vs pin-clear) and ACCEPT of the fire-next the primary
  MODIFIED away.
- Learned-weight provenance on THREE edges with pair-rollback-fails.
- HITL cell-cage ratify 9.6 min (gap 4 partial; sim_or_real stays
  designed — invented plant, not hil).
- Governance CR-A-6303 prices retire-vs-probe-vs-status-quo and mandates
  native pin-class barcodes on MES travelers (the fraud fence).
- Flip-fragility extended to PIN-TRUE CERTIFICATE.
- Independent LIF raster (38 ms, 156 neurons, 12 Hz, 71 spikes, 1633 pJ),
  not a copy of language-view spike_events.

## Self-critique of this round's batch

### Strengths
- Headline class is mechanistically tight: three locally-true mean loops
  live on force header, servo coordinate, and die temp. Conjunction is
  not a pin-true seat certificate.
- Negative-result honesty: the gate does the right thing and the carrier
  still fails for a reason the commissioned header sensors could not see.
  Total -0.16.
- Triple-edge scar is load-bearing: rolling back any pair fails, with
  fire threshold 0.30 exhibited on each remaining edge.
- Contrast ACCEPT on a true n6 seat window prevents "never fire-next"
  as the lesson.
- Distinct from r63 lock-spur lidar and r64 kiln bed-TC: press-fit LVDT
  vs force-mean. Canonical unused domain taken.

### Weaknesses (honest)
- Probe error bands, the 0.34%/campaign tote-mix rate, the $1.12M / $4.4M
  figures, the 9.6 min walk latency, and the night-shift 0.28% lot-swap
  base rate are DESIGNED constants and are flagged. Closed-loop offsets
  (header dilution from one oversized pin, compound green-strength slope)
  are derived from those inputs, not discovered by an unauthored process.
- Carrier-web crack model is a designed 8 min mapping; no full FEM of the
  web shipped.
- Human-in-the-loop is ratification latency, not sim_or_real=hil. Gap 4
  remains open as a provenance cell (invented plants stay designed).
- Cross-record arc is a hook (CR-A-6303 +21 d), not a serial igniter
  into another round. Mean-vs-local certificate scaffold is reused even
  though the physics (press-fit interference vs lock hydraulics / kiln
  bed) is new.
- warehouse-amr, surgical-assist, humanoid-locomotion, hrsg-attemperator
  remain unused.

### Realism of noise / latencies
Ladder: 204 us race / 188 us contrast race / 0.8 ms refractory floor
(tightest exhibited same-channel gap 1.664 ms on lvd.dN 3.124->4.788) /
500 us race window / 718 us gate latency / 20 ms bus epoch / 38 ms
independent LIF raster / 1.4 s probe / 9.6 min HITL / 12 s naive index
counterfactual / 8 min pre-t0 press / 2.6 h pin-pull recovery / 2.8 h
crack growth / 5.4 h hot-run fail / +3 d contrast / +21 d governance.
Adaptation decay on frc.ok (0.53->0.49->0.42->0.29), lvd.dN
(0.76->0.78->0.44->0.39->0.27), pos.ok (0.57->0.66->0.81->0.24),
tmp.ok (0.55->0.58->0.46).

### Value for SNN distillation
- PIN OVERSIZE = THREE CORRECT LOOPS, WRONG VOLUME.
- PIN-TRUE LVDT CHANNEL that policy treated as lube-film-nuisance-only as
  the tie-break.
- REVERSIBLE JOG that walks a seated pin iff the class is n6.
- TRIPLE-EDGE ELIGIBILITY: coordinated depression; pair rollback fails.
- CRITIC HEAD that can hold a process-correct MODIFY against a later
  unmonitored world loss without netting.

## Reconciliation and validity receipts
- reward_components: 5-head unweighted signed sum -0.16
  and 7-tick signed sum reconcile to total with |diff| < 1e-9. Embedded
  contrast 5-head sum 0.49 reconciles independently.
- spike_events: primary 26 events, one key t_rel_ms,
  globally non-decreasing, min same-channel gap 1.664 ms >= 0.8 ms, 3
  channels inside race_window_us 500 (lvd.short.high 6.412, frc.in_band 6.616,
  pos.ok 6.804). Contrast 8 events, own race, min same-channel gap well
  above 0.8 ms.
- Sidecars: raster spikes 71 == round(156 x 12.0 x 0.038);
  energy 1633 pJ / 0.001633 uJ at 23 pJ/spike; excerpt 16 events inside
  [0, 38000] us, neuron_id < 156, unique ids; routing 4
  entries with three scar edges' before/after pair; third factor tau 0.90 s
  == 900.0 ms; gate_snn pools 42/11/4 == round(n x rate x 0.026) each,
  decision MODIFY == safety_decision.decision. Independent LIF generated
  71 in-window events (not a copy of spike_events).
- Pipeline: check_jsonl / raster_status / verify_record_execution /
  spike_probe --strict run after write (see generator receipt).

## Novel coverage
The coordination-failure CLASS (force-mean certificate of a local pin
seat), the domain (industrial-assembly / press-fit servo cell), the jog
probe discriminant, the triple-edge scar with pair-rollback-fails, the
primary negative-result (correct MODIFY, carrier still fails on
unmonitored web crack), the HITL cell-cage ratify, the retaining-compound
probe-duration refit, and the MES traveler lot-swap (BOM class, not CSV
rounding) are absent from prior committed ouroboros rounds on this LIVE
tree. Repeated elements discounted: same-gate contrast, governance-pricing
scaffold, flip-fragility series (extended to pin-true certificate, but
the move rhymes), sequenced recovery shape, third-factor rollback form,
negative-result primary, mean-vs-local certificate motif (r01/r41/r61/r62/
r63/r64). Adjacent assembly/process rounds share sensor-fusion scaffolding
but not press-fit interference physics. Weighing a canonical unused domain
+ new failure family + changed cycle-2 tail class against those reused
scaffolds:

Novel coverage: 44%

## What a later round should add
1. FIT THE DESIGNED CONSTANTS: tote-mix arrival, probe LVDT bands,
   web-crack mapping, MES lot-swap process.
2. HIL PROVENANCE CELL: put the cell-cage LOTO on a hardware-in-loop
   indexer pendant with fitted latency as state.sim_or_real=hil — only if
   the plant is no longer purely invented.
3. CROSS-RECORD ARC: let CR-A-6303's LVDT alarm be the igniter of the
   next round rather than a dangling +21 d leaf.
4. Domain candidates (de-collided): warehouse-amr; surgical-assist;
   humanoid-locomotion; hrsg-attemperator; wet-fgd-absorber;
   alkaline-water-electrolysis.
   AVOID industrial-assembly (now used on this suffix), canal-lock-rail-
   transshipment (r63), malting-kiln-barn (r64), grid-inspection (r62/r42),
   sinter-strand-windbox (r61), bioreactor-perfusion (r41),
   autonomous-driving (r21), continuous-hot-dip-galvanizing (r01), and any
   LYOSHIELD / CINDERWICK / TRIAD / LOCKSPUR / WOLD-BARN / CORONSTAITH /
   WINDBOXHOLT / COLLETFEN plant.
'''

TRANSCRIPT_MD = r'''# Multi-Agent Ouroboros Swarm — Round 63c transcript

Factory: multi-agent-ouroboros-swarm
Run: 2026-09-02-final-heavy
Generator: grok-4.6
Record id: maos-r63c-001
Quota Q: 1
Rights: RM-793 research-only (SpaceXAI/xAI SuperGrok Heavy consumer chat)
Swarm: COLLET-FEN
Plant: invented COLLETFEN / Spigotholt Press-Fit Cell PF-6 (not LOCKSPUR /
WOLD-BARN / CORONSTAITH / WINDBOXHOLT / TRIAD / LYOSHIELD / CINDERWICK)

Two densifying cycles. Verbatim headings in order. Trajectory Builder cycle 2
emits the only JSONL line (also written to batch-r63c.jsonl). Collision
suffix: live batch-r63.jsonl already existed (LOCKSPUR); this suffix does
not overwrite it.

---

# CYCLE 1 — Foundation + injections

## Generator

Design intent: a six-station rotary press-fit cell where three correct
agents each read a header-mean loop because pin 14 is 12 µm oversized and
the overhead camera still reports flush. The naive playbook fires the next
pin into an unseated bore. The gate must MODIFY on a numeric LVDT/slope
floor, not by killing an agent. sim_or_real=designed. Reward heads are
task_progress/safety/efficiency/coherence/exploration.

Cycle-1 base arc (pre-critic): state at Spigotholt PF-6, 8.4 kN header,
FRC 8.4 kN, POS 0.00 mm, TMP 41.2 C, proposed FIRE-NEXT-PIN, safety
MODIFY to GATE-HOLD, executed hold without the jog-probe numbers fully
specified, outcome "oversize found, carrier saved"
(this last claim is the defect the later cycles will refuse to keep).
Sixteen spikes, five ticks, raster/gate_snn present but the scar is a
single edge.

```json
{
  "id": "maos-r63c-001",
  "state": {
    "sim_or_real": "designed",
    "domain": "industrial-process",
    "description": "Spigotholt cell PF-6; three press loops in-spec; supervisor proposes fire-next.",
    "t0_us": 1772954040000063,
    "gate_latency_us": 718,
    "race_window_us": 500
  },
  "proposed_action": {"name": "fire_next_pin", "parameters": {"index_station_4": true}},
  "safety_decision": {"decision": "MODIFY", "rationale": "Hold; do not fire next while LVDT residual is high."},
  "executed_action": {"name": "gate_hold", "executed_as_proposed": false},
  "future_outcome": {"summary": "Oversize found, carrier saved."},
  "reward_components": {"total": 0.40, "_aggregation": "total = task_progress + safety + efficiency + coherence + exploration"},
  "meta": {"round": 63, "factory": "multi-agent-ouroboros-swarm", "generator": "grok-4.6", "swarm": "COLLET-FEN"}
}
```

That v1 object is a scaffold, not the publishable line. Defects below are
intentional for the critic to catch.

## Critic

Numbered defects on the cycle-1 Generator scaffold:

1. **blocking — reward arithmetic / false success.** `reward_components.total`
   0.40 is asserted without the five heads, without ticks, and against an
   outcome that claims "carrier saved". If the pre-t0 web later
   fails, booking +0.40 is a lie. Fix: declare `_aggregation`, emit
   3–8 ticks that sum to task_progress+safety+efficiency+coherence+exploration,
   and do not call a quarantined gearbox a save.
2. **blocking — weak safety rationale.** `safety_decision.rationale` has no
   numeric floor. Contract requires a concrete constraint. Fix: quote
   do not fire next pin while LVDT residual_mm > 0.20 AND slope_kN_per_mm > 2.2.
3. **major — domain is a bucket, not a plant.** `state.domain` =
   `industrial-process` collides with generic MES vocabulary and teaches
   nothing. Press-fit plus pin-class (LVDT vs force-mean, slope as an
   oversize flag) is absent from prior ouroboros rounds and must be named.
4. **major — race under-specified.** One force channel cannot be a race.
   Need >=2 channels inside `race_window_us` with globally sorted `t_rel_ms`
   and same-channel refractory >= 0.8 ms.
5. **minor — single-edge scar.** Raster routing with one potentiated weight
   cannot exhibit pair-rollback-fails. Need three go-edges plus a
   discriminating LVDT-to-hold edge.
6. **minor — missing sidecars density.** Raster/gate_snn must be independent
   LIF (not a remap of language spikes), energy at 23 pJ/spike, gate_snn
   decision matching MODIFY.

Fix directives: name industrial-assembly; put LVDT and slope on the floor;
keep sim_or_real=designed; do not net world loss into process heads.

## Diversity Enforcer

Injected novel domain for this cycle: **industrial-assembly**.

This domain was absent from all prior trajectories in this batch/round and
from live committed state.domain values (continuous-hot-dip-galvanizing,
cupola-foundry-slag-sluice, autonomous-driving, urea-prilling-tower,
bioreactor-perfusion, grid-inspection, sinter-strand-windbox,
canal-lock-rail-transshipment, malting-kiln-barn). It displaces the
Generator's bucket `industrial-process` and expands coverage onto a
canonical prompt-list leftover (warehouse-amr, surgical-assist,
humanoid-locomotion remain unused on purpose).

Concrete domain-specific constraint: do not command FIRE-NEXT-PIN while
station-3 LVDT residual_mm > 0.20 with FRC still inside 7.6-9.2 kN.

Sensor delta versus displaced lock/kiln/sinter stacks: +header force mean,
+C-axis 0.5 µm encoder, +die RTD, +axial LVDT, +kN/mm slope; −axle-counter,
−lock-wall lidar, −still-well, −bed TC, −corona UV, −BTP IR, −CAV radar.

`state.domain` and `meta.domain` must both read `industrial-assembly`.
Opening of `state.description` must start at Spigotholt press-fit (Jaccard
< 0.4 versus Poundholt lock / Barleyholt kiln / Fernholt crawler).

## Edge-Case Hunter

Injected adversarial tail for this cycle: **pin-14 H7/p6 oversize +
overhead-camera PASS**.

- Trigger: tote mix puts a 12 µm oversized pin on an n6 traveler; the
  overhead camera is radial and reports flush; axial short 0.42 mm is
  invisible. Base rate 0.34%/campaign (<1%), designed, flagged.
- Naive failure mode: PB-PF-6 treats three in-spec means as a seat
  certificate and FIRE-NEXT-PIN. FALSE PERMISSION. Station 4 indexes onto
  a cracked web.
- Trajectory edit: `state.fault_context` and `poisoned_context` must carry
  the camera-pass; `safety_decision` must MODIFY on LVDT+slope floors even
  though the camera is green; `future_outcome` must not claim the carrier
  is saved — 8 min pre-t0 press already cracked the web.
- Distinct from Diversity's domain injection (assembly cell vs this
  wrong-volume visual miss).

## Neuromorphic Translator

Cycle-1 temporal densification (JSON patch intent, not the publishable
line):

- `state.t0_us` = 1772954040000063; `gate_latency_us` = 718;
  `race_window_us` = 500.
- Race: lvd.short.high @ 6.412 ms (amp 1.38) beats frc.in_band @ 6.616 ms
  (amp 1.12) by 204 us; pos.ok @ 6.804 ms also inside the 500 us window
  (three channels). Winner+718 us => ctrl.gate @ 7.130 ms.
- Flip narrative: reversing order by < min(500, 500) us reshuffles triage;
  floors still MODIFY.
- Spike train: 16 events in cycle 1, globally sorted `t_rel_ms`,
  same-channel refractory >= 0.8 ms (tightest lvd.dN 1.664 ms).
- Ticks (5 in cycle 1): 4180, 6412, 7130, 1400000, 576000000 us; heads
  signed; will expand to 7 in cycle 2.
- Raster: independent LIF 38 ms / 156 neurons / 12 Hz / 71 spikes /
  1633 pJ / 0.001633 uJ; third factor ACh tau_e 0.90 s = 900 ms.
- gate_snn: modify_hold 42 / accept_fire 11 / reject_abort 4 over 26 ms;
  decision MODIFY.

Distillation value: pin-true LVDT as the race winner against a force-mean
loser is the SNN lesson, not a prose margin.

## Trajectory Builder

Cycle-1 hardened object (validation receipt, not yet the JSONL line):

Checks passed / fixed:
- six required objects present; sim_or_real=designed; decision=MODIFY with
  numeric floor in rationale.
- domain injected: industrial-assembly (not industrial-process).
- tail injected: p6 oversize + camera PASS.
- reward scaffold still incomplete (5 ticks, total not yet the honest
  negative) — cycle 2 must finish arithmetic and delayed side-effects.
- spike_events 16, sorted, refractory ok; raster budget 71=round(156*12*0.038);
  gate_snn decision matches.
- Densification delta vs Generator v1: +1 domain, +1 tail, +race 204 us,
  +LVDT/slope floors, +16 spikes, +5 ticks, +raster/gate_snn.

Cycle-1 output becomes the base for cycle 2. Not published.

---

# CYCLE 2 — Densification

## Generator

Re-emit of cycle-1 hardened trajectory, expanded (additive):

1. Downstream side-effect A (immediate-delayed): +2.8 h ultrasonic crack
   growth +1.8 mm on the pre-t0 web — first delayed world loss.
2. Downstream side-effect B (later-delayed): +5.4 h hot-run fail, 14 h
   stall, $1.12M designed — primary terminal. The gate prevented
   FIRE-NEXT-PIN and did not undo the 8 min crack.
3. `proposed_action.evidence` deepened with six observables and units
   (LVDT mm, slope kN/mm, force kN, servo mm, die C, race us).
4. `safety_decision.rationale` tightened to the numeric floor
   LVDT residual_mm > 0.20 AND slope_kN_per_mm > 2.2, plus probe
   discriminant 0.38 mm short-band vs 0.05 mm seated, plus 9.6 min HITL.
5. Reward total moves from the dishonest +0.40 to honest -0.16 with five
   heads and seven ticks.
6. Embedded SAME-GATE contrast on sister cell PF-7 (+3 d) ACCEPT.
7. Governance CR-A-6303.

Design intent (cycle 2): keep the three-correct-loops story, refuse to
call the episode a save, and make the probe numbers physically
re-fittable under retaining compound.

## Critic

Re-audit of the now-richer trajectory:

1. **blocking — probe portability.** The 1.4 s / 80 N dry-fit jog is
   calibrated on a dry n6/p6 pair. An anaerobic retaining-compound campaign
   (green strength) will false-short a live intact pin. Fix: inject the
   compound sub-variant and refit the probe (Diversity's cycle-2 job).
2. **major — tail class rhyme.** A night-shift CSV rounding tail would
   collide with live r63 axle-counter CSV and r64 bed-TC CSV. Fix:
   Edge-Case Hunter must inject a disjoint class (MES BOM lot-swap, not
   quantization).
3. **major — contrast missing until this cycle.** Without an ACCEPT twin,
   the lesson collapses to "never fire-next". Fix: sister cell PF-7 true
   n6 window, 188 us demand vs pin-clear race, ACCEPT.
4. **minor — raster vs language train.** Excerpt times must not be a
   microsecond remap of spike_events. Independent LIF seed 63003.
5. **minor — HITL provenance.** 9.6 min ratify is latency, not
   sim_or_real=hil. Keep designed; flag gap 4.

No trajectory JSON from this role. Directives only.

## Diversity Enforcer

Injected novel domain for this cycle: **anaerobic retaining-compound
press-fit** (physical-constraints sub-variant of industrial-assembly;
counts as this cycle's 1 novel domain). Distinct from cycle 1's dry
interference-fit.

What it changed: green-strength film raises force-slope 2.3x and LVDT
creep 1.8x. The cycle-1 1.4 s / 80 N dry-fit pulse false-fouls a wet
intact n6 (LVDT 0.29 mm >= 0.20). Standing probe must move to 18 s / 25 N
plus cure-exotherm IR delta >= 0.6 K on a true wet seat (dry oversize
shows IR delta <= 0.1 K).

Constraint delta: fire-next floor unchanged (LVDT > 0.20 AND slope > 2.2)
but the discriminant table is now per-compound-class, not a single jog.
Sensor delta: +IR exotherm on the pin fillet; force/LVDT retained.

Cycle 1's industrial-assembly domain is preserved (additive, not replaced).

## Edge-Case Hunter

Injected second adversarial tail (disjoint trigger class from cycle 1):
**MES traveler lot-swap**.

- Trigger: Sunday-night shift lead posts a traveler that maps tote P-n6
  while the pins are P-p6 (12 µm class error). Live LVDT 0.42 mm and slope
  2.8 kN/mm sit at the claimed pin-true. Base rate ~0.28% of Sunday-night
  campaigns (<1%), designed, flagged.
- Naive failure mode: the historian export is "green" so a weak supervisor
  treats the playbook confirms as a seat certificate even after the jog.
  Human-intent BOM deception, not accidental tote-mix (cycle 1) and not
  CSV rounding (r63/r64).
- Trajectory edit: `governance_subgame` mandates native pin-class barcodes;
  `meta.injections.cycle2_tail` names the lot-swap; `future_outcome` keeps
  the primary fail as web-crack, not as "fraud detected therefore saved".
- Distinct from Diversity's compound sub-variant (BOM deception vs
  adhesive physics).

Cycle 1's oversize+camera tail is preserved.

## Neuromorphic Translator

Cycle-2 re-densification (additive):

- Spike train expanded 16 -> 26 events: added jog.probe @ 1400 ms,
  post-probe lvd.dN / frc.in_band, human.ratify @ 576000 ms, cell.hold,
  web.crack, delayed frc/lvd/pos @ 10080000 ms, carrier.fail @ 19440000 ms.
  Still globally sorted; min same-channel gap remains 1.664 ms on lvd.dN.
- Ticks expanded 5 -> 7 (add 10080000000 us crack-growth and 19440000000 us
  hot-run fail). Head sums: 0.08 / -0.32 / -0.12 / 0.12 / 0.08 = -0.16.
- Contrast spike train (8 events) with its own 188 us race.
- Raster unchanged in budget (71) but excerpt confirmed independent of
  language timestamps; routing table now carries three scar edges'
  commissioned/illusion/after weights plus LVDT-to-hold 0.69.
- Eligibility: e^{-0.78/0.90}=0.42035; dw -0.250 / -0.220 / -0.210.
- gate_snn still MODIFY; populations 42/11/4 = round(n*rate*0.026).

Winner/loser flip: if frc.in_band led by < 204 us inside 500 us, triage
queues FIRE-NEXT-PIN first; floors still MODIFY.

## Trajectory Builder

FINAL publishable object for this cycle / this JSONL line: one Thalamic
trajectory, id maos-r63c-001, meta.round=63, written to batch-r63c.jsonl.

Validation receipt (checks passed / fixed):
- Required keys: id, state, proposed_action, safety_decision,
  executed_action, future_outcome, reward_components, meta. All objects.
- state.sim_or_real=designed; provenance.kind=designed; never real.
- safety_decision.decision=MODIFY; rationale non-empty with numeric floor
  LVDT residual_mm > 0.20 AND slope_kN_per_mm > 2.2.
- reward total -0.16 reconciles with five heads and with seven ticks
  (|diff| < 1e-9). Contrast 0.49 reconciles independently.
- spike_events 26, key t_rel_ms only, globally non-decreasing, refractory
  >= 0.8 ms, 3 channels in the 500 us race window.
- raster: window 38 ms / 0.038 s, 156 neurons, 12 Hz, 71 spikes,
  energy 1633 pJ / 0.001633 uJ; excerpt 16 unique neurons in [0, 38000];
  routing table 4 entries; third_factor ACh 0.90 s == 900 ms.
- gate_snn decision MODIFY matches safety_decision.decision; pool spikes
  42/11/4.
- Diversity + Edge-Case injections present and non-trivial in both cycles;
  cycle 2 retains cycle 1 domain+tail.
- Densification delta vs cycle 1: +1 physical-constraint sub-variant
  (retaining-compound probe refit), +1 tail (MES traveler lot-swap),
  +10 spikes, +2 ticks, +1 delayed surprise (ultrasonic growth),
  +embedded contrast, +CR-A-6303, +independent LIF 71.

This is the only JSON that counts toward the batch. Intermediate patches
stay in this transcript.

'''


def write_excl(path: Path, data: str):
    fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    try:
        os.write(fd, data.encode("utf-8"))
    finally:
        os.close(fd)


def main():
    rec, lif = build_record()
    line = dumps_exact_json(rec, ensure_ascii=False, sort_keys=False)
    if "\n" in line:
        raise SystemExit("refusing multiline JSON")
    # local sanity
    loaded = json.loads(line)
    assert loaded["id"] == "maos-r63c-001"
    assert loaded["meta"]["round"] == 63
    assert loaded["state"]["sim_or_real"] == "designed"
    assert loaded["safety_decision"]["decision"] == "MODIFY"
    heads = ["task_progress", "safety", "efficiency", "coherence", "exploration"]
    rc = loaded["reward_components"]
    head_sum = sum(rc[h] for h in heads)
    assert abs(head_sum - rc["total"]) < 1e-9, (head_sum, rc["total"])
    tick_sum = {h: 0.0 for h in heads}
    for t in rc["ticks"]:
        for h in heads:
            tick_sum[h] += t[h]
    for h in heads:
        assert abs(tick_sum[h] - rc[h]) < 1e-9, (h, tick_sum[h], rc[h])
    crc = loaded["future_outcome"]["embedded_contrast_decision"]["reward_components"]
    assert abs(sum(crc[h] for h in heads) - crc["total"]) < 1e-9
    times = [e["t_rel_ms"] for e in loaded["spike_events"]]
    assert times == sorted(times)
    ras = loaded["raster"]
    assert ras["spikes"] == round(ras["neurons"] * ras["mean_rate_hz"] * ras["window_s"])
    assert abs(ras["energy_pJ"] - ras["spikes"] * 23) < 1e-6
    assert abs(ras["energy_uJ"] - ras["spikes"] * 23e-6) < 1e-9
    assert loaded["gate_snn"]["decision"] == loaded["safety_decision"]["decision"]
    ids = [e["neuron_id"] for e in ras["excerpt"]]
    assert len(ids) == len(set(ids))
    assert all(0 <= e["t_us"] <= ras["window_ms"] * 1000 for e in ras["excerpt"])
    assert "Novel coverage: 44%" in NOTES_MD
    for heading in [
        "## Generator",
        "## Critic",
        "## Diversity Enforcer",
        "## Edge-Case Hunter",
        "## Neuromorphic Translator",
        "## Trajectory Builder",
    ]:
        assert TRANSCRIPT_MD.count(heading) == 2, heading

    write_excl(BATCH, line + "\n")
    write_excl(NOTES, NOTES_MD if NOTES_MD.endswith("\n") else NOTES_MD + "\n")
    write_excl(TRANSCRIPT, TRANSCRIPT_MD if TRANSCRIPT_MD.endswith("\n") else TRANSCRIPT_MD + "\n")
    print(json.dumps({
        "wrote": [str(BATCH), str(NOTES), str(TRANSCRIPT)],
        "bytes": {"batch": BATCH.stat().st_size, "notes": NOTES.stat().st_size, "transcript": TRANSCRIPT.stat().st_size},
        "id": rec["id"],
        "spikes": len(rec["spike_events"]),
        "lif": len(lif),
        "excerpt": len(rec["raster"]["excerpt"]),
        "total": rec["reward_components"]["total"],
    }))


if __name__ == "__main__":
    main()
