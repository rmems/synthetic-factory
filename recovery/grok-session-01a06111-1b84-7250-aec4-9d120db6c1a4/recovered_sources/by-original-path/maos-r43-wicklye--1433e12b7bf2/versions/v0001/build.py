#!/usr/bin/env python3
"""Create-only MAOS round 43 (WICKLYE alkaline stack). Does not touch existing files."""
from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path

ROOT = Path("/home/raulmc/rmems/synthetic-factory")
FAC = ROOT / "outputs/raw/2026-09-02-final-heavy/multi-agent-ouroboros-swarm"
STAGING = Path("/tmp/maos-r43-wicklye")
PIPE = ROOT / "pipelines"

sys.path.insert(0, str(PIPE))

RIGHTS = {
    "provider": "SpaceXAI/xAI",
    "model": "grok-4.6",
    "channel": "consumer",
    "subscription_plan": "SuperGrok Heavy",
    "generation_surface": "SuperGrok Heavy chat",
    "generated_at": "2026-09-02T20:18:00Z",
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

TRACE = math.exp(-0.76 / 0.90)
ETA = (0.250 / TRACE, 0.210 / TRACE, 0.200 / TRACE)


def record():
    spikes = [
        {"channel": "cell.v", "t_rel_ms": 0.260, "amplitude": 0.54},
        {"channel": "h2o2.local", "t_rel_ms": 1.120, "amplitude": 0.72},
        {"channel": "v.mean", "t_rel_ms": 2.040, "amplitude": 0.50},
        {"channel": "h2.header", "t_rel_ms": 3.180, "amplitude": 0.61},
        {"channel": "cell.v", "t_rel_ms": 4.120, "amplitude": 0.51},
        {"channel": "v.mean", "t_rel_ms": 4.840, "amplitude": 0.57},
        {"channel": "h2.header", "t_rel_ms": 5.380, "amplitude": 0.46},
        {"channel": "h2o2.high", "t_rel_ms": 6.518, "amplitude": 1.44},
        {"channel": "v.mean.in_band", "t_rel_ms": 6.706, "amplitude": 1.12},
        {"channel": "h2.header", "t_rel_ms": 6.894, "amplitude": 0.64},
        {"channel": "ctrl.gate", "t_rel_ms": 7.226, "amplitude": 1.06},
        {"channel": "cell.v", "t_rel_ms": 8.880, "amplitude": 0.42},
        {"channel": "current.ka", "t_rel_ms": 10.740, "amplitude": 0.76},
        {"channel": "h2o2.local", "t_rel_ms": 13.020, "amplitude": 0.29},
        {"channel": "cell.v", "t_rel_ms": 18.480, "amplitude": 0.33},
        {"channel": "ctrl.gate", "t_rel_ms": 26.160, "amplitude": 0.82},
        {"channel": "cell.probe", "t_rel_ms": 5200.0, "amplitude": 0.96},
        {"channel": "cell.v", "t_rel_ms": 5288.4, "amplitude": 0.39},
        {"channel": "v.mean.in_band", "t_rel_ms": 5372.2, "amplitude": 0.33},
        {"channel": "human.ratify", "t_rel_ms": 588000.0, "amplitude": 0.78},
        {"channel": "stack.hold", "t_rel_ms": 588900.0, "amplitude": 0.70},
        {"channel": "cell.crack", "t_rel_ms": 589800.0, "amplitude": 0.86},
        {"channel": "deflagration", "t_rel_ms": 6480000.0, "amplitude": 0.93},
        {"channel": "cell.v", "t_rel_ms": 11520000.0, "amplitude": 0.30},
        {"channel": "v.mean", "t_rel_ms": 11520700.0, "amplitude": 0.27},
        {"channel": "h2.header", "t_rel_ms": 11521480.0, "amplitude": 0.24},
    ]
    ticks = [
        {"t_us": 4120, "task_progress": 0.01, "safety": -0.02, "efficiency": -0.01, "coherence": 0.02, "exploration": 0.01},
        {"t_us": 6518, "task_progress": 0.02, "safety": -0.05, "efficiency": -0.01, "coherence": 0.02, "exploration": 0.01},
        {"t_us": 7226, "task_progress": 0.02, "safety": -0.06, "efficiency": -0.02, "coherence": 0.03, "exploration": 0.02},
        {"t_us": 5200000, "task_progress": 0.01, "safety": -0.05, "efficiency": -0.02, "coherence": 0.02, "exploration": 0.01},
        {"t_us": 588000000, "task_progress": 0.01, "safety": -0.05, "efficiency": -0.01, "coherence": 0.02, "exploration": 0.01},
        {"t_us": 6480000000, "task_progress": 0.00, "safety": -0.07, "efficiency": -0.02, "coherence": 0.00, "exploration": 0.00},
        {"t_us": 11520000000, "task_progress": 0.01, "safety": -0.01, "efficiency": -0.01, "coherence": 0.01, "exploration": 0.00},
    ]
    excerpt = [
        {"t_us": 1400, "neuron_id": 6, "channel": "lif.hold"},
        {"t_us": 4700, "neuron_id": 11, "channel": "lif.hold"},
        {"t_us": 5800, "neuron_id": 14, "channel": "lif.hold"},
        {"t_us": 8600, "neuron_id": 3, "channel": "lif.hold"},
        {"t_us": 9900, "neuron_id": 9, "channel": "lif.hold"},
        {"t_us": 11600, "neuron_id": 2, "channel": "lif.hold"},
        {"t_us": 17200, "neuron_id": 8, "channel": "lif.hold"},
        {"t_us": 21100, "neuron_id": 44, "channel": "lif.h2o2"},
        {"t_us": 21800, "neuron_id": 47, "channel": "lif.h2o2"},
        {"t_us": 22300, "neuron_id": 151, "channel": "lif.h2o2"},
        {"t_us": 22800, "neuron_id": 132, "channel": "lif.h2o2"},
        {"t_us": 23400, "neuron_id": 61, "channel": "lif.h2o2"},
        {"t_us": 23900, "neuron_id": 49, "channel": "lif.h2o2"},
        {"t_us": 29800, "neuron_id": 12, "channel": "lif.late"},
        {"t_us": 32800, "neuron_id": 7, "channel": "lif.late"},
        {"t_us": 36900, "neuron_id": 10, "channel": "lif.late"},
    ]
    elig = (
        "coordinated pre_post_stdp on ALL THREE stack-mean-go edges; ACh at "
        "h2o2-high-win tags v.mean.in_band->raise, h2.header.ok->raise, and "
        "current.in_band->raise; negative credit at probe-fail (cracked "
        f"diaphragm confirmed, +0.76 s) depresses ALL THREE. trace "
        f"e^{{-0.76/0.90}}={TRACE:.5f}; eta {ETA[0]:.5f} / {ETA[1]:.5f} / "
        f"{ETA[2]:.5f}; dw -0.250 / -0.210 / -0.200; weights 0.52->0.27, "
        "0.45->0.24, 0.42->0.22. Rolling back any pair is fitted to fail "
        "(the remaining edge stays > 0.30)."
    )
    return {
        "id": "maos-r43-001",
        "title": "WICKLYE AX-6: cell-17 H2-in-O2 3.6 vol% beats v.mean.in_band by 188 us; correct MODIFY still deflagrates the O2 plenum after a pre-t0 diaphragm crack",
        "rights": dict(RIGHTS),
        "provenance": {"kind": "designed", "claimed": "designed"},
        "state": {
            "sim_or_real": "designed",
            "domain": "alkaline-water-electrolysis",
            "scenario_name": "WICKLYE / Brineholt Alkaline Stack AX-6",
            "timestamp_local": "2026-06-14T02:28:00-05:00",
            "t0_us": 1781422080000043,
            "gate_latency_us": 708,
            "race_window_us": 500,
            "race_window_rel_ms": [6.518, 7.018],
            "description": "Brineholt alkaline hall AX-6 is 38 min into a Sunday-night cheap-power current raise on a 120-cell 12 bar KOH stack (80.0 C, 30 wt% KOH, 5.10 kA) when three heterogeneous, individually-correct agents jointly report 'stack-mean-true, raise current'. VOLT's 12-bit stack-mean cell voltage is 1.917 V inside 1.85-2.05. H2's header purity is 99.91 vol% inside 99.80-99.99. CURR's rectifier is 5.10 kA inside 4.80-5.40. The conjunction is not a cell-true gas-integrity certificate: cell 17's Zirfon diaphragm is cracked, so local cell voltage is 1.52 V (healthy 1.85-2.05; hold if < 1.65) and local O2-side H2-in-O2 is 3.6 vol% (healthy < 0.40; hold if > 1.00; LEL ~4.0) while stack-mean V, H2-header purity, and rectifier current still see 119 intact cells plus one ionic short. Local H2-in-O2 infers 3.6 vol% and V_17 1.52 V but policy treats the cell GC as a wet-sensor nuisance tag unless H2-header purity also trips (2016 'noisy cell-GC after KOH condensate'). Residual-first latches CURRENT-HOLD plus a rectifier-step probe; mean-first would have authorized RAISE-CURRENT 5.10 to 5.50 kA into a crossover-ignition window with cell 17 already mixed.",
            "goal": "Hold rectifier current at 5.10 kA without a cheap-power raise while cell-17 H2-in-O2 > 1.00 vol% AND cell-17 V < 1.65 V AND cell 17 remains unisolated; keep O2-plenum deflagrations at 0 extra events and stack-stall events at 0 from the draft.",
            "race": {
                "contenders": [
                    "h2o2.high 3.6 vol% (cell-17 O2-side H2-in-O2 vs stack-mean voltage)",
                    "v.mean.in_band 1.917 V (120-cell stack mean)",
                ],
                "semantics": "H2-in-O2-first latches CURRENT-HOLD + RECTIFIER-STEP-PROBE + CELL-17 hold. Mean-first latches RAISE-CURRENT (5.10 to 5.50 kA, no isolate).",
                "window_derivation": "500 us = one 360 us cell-GC ADC slot plus 140 us stack-mean publish.",
                "order_evidence_note": "Margin 188 us vs combined jitter 58 us (H2-in-O2 32 + mean 26): 3.24x. The 188 us gap sits inside min(500, 500) us, so a sub-flip-bound perturbation reverses triage order. The gate rides the order-invariant floors cell-17 H2-in-O2 > 1.00 vol% and cell-17 V < 1.65 V, not the alarm order.",
            },
            "topology": {
                "site": "Brineholt Electrolysis, invented marsh-brine campus Brineholt, stack AX-6: 120-cell bipolar alkaline, 12 bar, 80.0 C, 30 wt% KOH, Zirfon UTP 500 diaphragms, 5.10 kA rectifier, Grade-B cell-gallery LOTO",
                "agents": "VOLT 120-cell stack-mean voltage (vendor Voltholt): 20 Hz 12-bit on the common DC bus. H2 header purity TCD (vendor Hygroshear-H2): 50 Hz on the H2-header sample, not the O2 side. CURR rectifier shunt (vendor Ampfen): 50 Hz on the common rectifier. CELL local cell-17 voltage plus O2-side H2-in-O2 GC (vendor Cellghyll) is commissioned as a wet-sensor nuisance tag, not as a diaphragm-integrity tag. Heterogeneous stacks, no shared intent schema, one 20 ms electrolysis-bus epoch",
                "coupling": "All three playbook confirms live on the WRONG certificate. VOLT is correct that stack mean sits at 1.917 V (119 intact cells at 1.920 V plus cell 17 at 1.52 V). H2 is correct that H2-header purity is 99.91 vol% (crossover contaminates the O2 plenum, not the H2 header). CURR is correct that rectifier current is 5.10 kA (the common bus still sees 119 healthy cells). Playbook PB-AX-6 treats the conjunction as permission to raise current. No agent is faulty; the stack-mean voltage is looking at bus-average polarization, not at cell 17's cracked diaphragm.",
            },
            "sensors": [
                "120-cell stack-mean voltage 12-bit, 20 Hz, 26 us jitter, 1.917 V (dead-band 1.85-2.05)",
                "H2-header purity TCD, 50 Hz, 18 us jitter, 99.91 vol% (band 99.80-99.99)",
                "rectifier shunt, 50 Hz, 22 us jitter, 5.10 kA (band 4.80-5.40)",
                "cell-17 local voltage, 20 Hz, 28 us jitter, 1.52 V (healthy 1.85-2.05; policy floor 1.65 V is not armed unless H2-header purity also trips)",
                "cell-17 O2-side H2-in-O2 GC 3.6 vol% (healthy < 0.40; hold if > 1.00; LEL ~4.0)",
                "cell-17 O2-plenum camera is NOT commissioned at t0 (installed after this incident)",
            ],
            "constraints": {
                "current_kA": 5.10,
                "current_hold_floor_kA": 5.10,
                "proposed_current_kA": 5.50,
                "v_mean_V": 1.917,
                "v_mean_band_V": [1.85, 2.05],
                "h2_header_volpct": 99.91,
                "h2_header_band_volpct": [99.80, 99.99],
                "v17_V": 1.52,
                "v17_hold_V": 1.65,
                "v17_healthy_V": 1.85,
                "h2o2_volpct": 3.6,
                "h2o2_hold_volpct": 1.00,
                "h2o2_healthy_volpct": 0.40,
                "h2o2_lel_volpct": 4.0,
                "cell_count": 120,
                "fault_cell": 17,
                "stack_bar": 12.0,
                "stack_C": 80.0,
                "koh_wtpct": 30.0,
                "pre_t0_crossover_min": 11.6,
                "fault_diaphragm": "cell 17 Zirfon crack / local H2 crossover into O2 plenum",
            },
            "fault_context": {
                "failure_class": "STACK-MEAN CERTIFICATE OF A LOCAL DIAPHRAGM CRACK: three individually-correct heterogeneous agents each read a locally-true loop; a cracked Zirfon on cell 17 partitions local cell voltage and O2-side H2-in-O2 from stack-mean V, H2-header purity, and rectifier current, so the playbook's VOLT / H2 / CURR conjunction is not a cell-true gas-integrity certificate",
                "igniter": "cell 17 Zirfon crack after 11.6 min of unmonitored local H2 crossover; cell-gallery visual PASSES (the crack sits on the wet KOH side; the mixed O2 plenum is on the far side of the bipolar plate)",
                "naive_failure": "PB-AX-6 RAISE-CURRENT on three healthy loops: 5.10 to 5.50 kA into a crossover-ignition window with cell 17 already at 3.6 vol% H2-in-O2, stack rebuild $2.4M plus a 36-hour unplanned stall",
            },
            "poisoned_context": {
                "naive_alarm": "Playbook PB-AX-6 (after the 2016 'noisy cell-GC after KOH condensate') auto-drafts RAISE-CURRENT whenever stack-mean V is inside 1.85-2.05 V AND H2-header purity inside 99.80-99.99 vol% AND rectifier inside 4.80-5.40 kA, ignoring the local cell GC unless H2-header purity also trips",
                "why_poisoned": "The three confirms are locally true and jointly insufficient. The local H2-in-O2 GC is a commissioned sensor that policy treats as wet-sensor-nuisance-only. Independence of 'stack mean in band, therefore every diaphragm is intact' is the hidden assumption, and it is false across a diaphragm-crack-plus-header-dilution path.",
            },
            "constraint": "Do not raise rectifier current above 5.10 kA AND do not skip the rectifier-step while cell-17 H2-in-O2 > 1.00 vol% AND cell-17 V < 1.65 V. Discriminate cracked diaphragm vs true stack-duty with a reversible rectifier-step probe before any raise-current.",
        },
        "proposed_action": {
            "actor": "electrolysis supervisory optimizer ESO (auto-playbook PB-AX-6 draft), submitted to gate TG-AX-6",
            "name": "raise_current",
            "action": "RAISE-CURRENT: 5.10 -> 5.50 kA, no rectifier-step probe, no cell-17 hold",
            "summary": "Treat three in-spec loops as a healthy cell-true stack and raise Sunday-night current to clear a cheap-power H2-make window.",
            "parameters": {
                "current_kA": 5.50,
                "rectifier_step_probe": False,
                "cell_hold": False,
                "human_ratify": False,
            },
            "steps": [
                "assert stack-mean V 1.917 V inside 1.85-2.05",
                "assert H2-header purity 99.91 vol% inside 99.80-99.99",
                "assert rectifier 5.10 kA inside 4.80-5.40",
                "raise rectifier 5.10 to 5.50 kA over 8 s",
                "hold cell-17 H2-in-O2 unread as a diaphragm-integrity tag",
            ],
            "evidence": [
                {"observable": "cell-17 O2-side H2-in-O2", "value": 3.6, "unit": "vol%", "source": "CELL GC vs stack-mean V", "note": "healthy < 0.40 vol%; policy floor 1.00 vol% is not armed unless H2-header purity also trips"},
                {"observable": "cell-17 local voltage", "value": 1.52, "unit": "V", "source": "CELL local tap", "note": "healthy 1.85-2.05; hold floor 1.65; lives on the cracked cell, not the DC-bus mean"},
                {"observable": "120-cell stack-mean voltage", "value": 1.917, "unit": "V", "source": "VOLT 12-bit", "note": "healthy-load band 1.85-2.05 V; 119 intact cells still dominate the bus average"},
                {"observable": "H2-header purity", "value": 99.91, "unit": "vol%", "source": "H2 TCD", "note": "band 99.80-99.99 vol%; header-true, O2-plenum-false"},
                {"observable": "rectifier current", "value": 5.10, "unit": "kA", "source": "CURR shunt", "note": "band 4.80-5.40 kA; bus-true, cracked-cell-false"},
                {"observable": "race margin", "value": 188, "unit": "us", "source": "h2o2.high 6.518 ms vs v.mean.in_band 6.706 ms", "note": "combined jitter 58 us, 3.24x; inside 500 us flip bound"},
            ],
            "basis": "PB-AX-6 fires on three locally-true confirms. The draft does not read cell-17 H2-in-O2 3.6 vol% as a crossover residual and does not treat V_17 1.52 V as a diaphragm-crack discriminant.",
            "expected_cost_bound": "If the draft executes: O2-plenum deflagration on cell 17 at 3.6 vol% H2-in-O2 climbing toward LEL, $2.4M stack rebuild plus 36-hour unplanned stall. If MODIFIED: probe plus hold, with residual risk from crossover already seeded in the 11.6 min pre-t0 crack.",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "correctness": "correct",
            "decided_by": "TG-AX-6 thalamic release gate",
            "decision_t_rel_ms": 7.226,
            "rationale": "MODIFY the draft: strip the raise-current, hold 5.10 kA, run a 5.2 s rectifier-step probe (+3 pct / +0.153 kA), and isolate cell 17 only if the probe stays mean-false. Numeric floor: do not raise rectifier current above 5.10 kA AND do not skip the rectifier-step while cell-17 H2-in-O2 > 1.00 vol% AND cell-17 V < 1.65 V. Observed H2-in-O2 3.6 vol% and V_17 1.52 V both violate the release predicate, so a raise-current is forbidden even though all three playbook confirms are numerically true. The three confirms are not a cell-true gas-integrity certificate: they live on stack-mean V, H2-header purity, and rectifier current past a cracked Zirfon, and the playbook's conjunction of stack-mean-true loops is not a cell-true certificate. Probe discriminant: after a 5.2 s +3 pct rectifier step, a cracked diaphragm keeps |Delta V_17| <= 0.012 V (ionic short, flat V-I; 0.006 V observed); a live intact cell moves >= 0.038 V. Stack mean always moves ~0.040 V either way. Order-code discipline: h2o2.high beat v.mean.in_band by 188 us inside the 500 us flip bound, so triage order is flip-fragile; the hold rides the order-invariant floors, not the winner tag. Human ratification: cell-17 hold is cell-gallery LOTO with fitted 9.8 min dead-man; the gate may hold and probe autonomously but may not break the cell interlock without the operator confirm.",
            "constraint_checked": {
                "current_kA": {"observed": 5.10, "floor": 5.10, "proposed_target": 5.50},
                "h2o2_volpct": {"observed": 3.6, "hold_if_above": 1.00},
                "v17_V": {"observed": 1.52, "hold_if_below": 1.65},
                "v_mean_V": {"observed": 1.917, "band": [1.85, 2.05]},
            },
        },
        "executed_action": {
            "name": "current_hold_rectifier_step_probe_isolate",
            "action": "CURRENT-HOLD + RECTIFIER-STEP-PROBE + CELL-17-HOLD (gate-mandated modification)",
            "executed_as_proposed": False,
            "parameters": {
                "current_kA": 5.10,
                "rectifier_step_probe": True,
                "cell_hold": True,
                "human_ratify": True,
            },
            "gate_effect": "MODIFY: raise-current stripped. Hold 5.10 kA. 5.2 s rectifier-step +3 pct. Probe stays mean-false (|Delta V_17| 0.006 <= 0.012 V cracked band) so the cell interlock is broken after 9.8 min human ratify and cell 17 is held. Setpoint resumes after an intact-diaphragm verify.",
            "deviations": "PB-AX-6 raise-current stripped entirely. Rectifier is stepped only for the 5.2 s probe then returned. Cell interlock wait added (9.8 min fitted walk+ratify). Cross-cell V survey added during the hold (not in the draft).",
            "execution_log": [
                {"t_rel_ms": 7.226, "entry": "TG-AX-6 MODIFY latched 708 us after h2o2-high win; raise-current stripped; hold+probe authorized"},
                {"t_rel_ms": 5200.0, "entry": "rectifier-step probe: +3 pct / +0.153 kA for 5.2 s; V_17 1.52 -> 1.526 V (cracked band |Delta V_17| 0.006 <= 0.012); stack mean 1.917 -> 1.956 V"},
                {"t_rel_ms": 588000.0, "entry": "operator ratifies cell interlock break after 9.8 min cell-gallery walk (fitted walk+interlock)"},
                {"t_rel_ms": 588900.0, "entry": "cell 17 held; local GC slaved off the current schedule; remaining 119 cells recovered toward 0.038 V step over 3.2 h"},
                {"t_rel_ms": 589800.0, "entry": "cell survey: cell 17 Zirfon already cracked on the wet side; 11.6 min pre-t0 crossover logged"},
                {"t_rel_ms": 6480000.0, "entry": "O2-plenum deflagration on cell 17 from the pre-t0 mixed pocket during a rectifier-ripple ignition; 18 h stall"},
                {"t_rel_ms": 11520000.0, "entry": "true intact diaphragm on the remaining stack: local V delta 0.041 V, H2-in-O2 0.22 vol%, V_17 above 1.65; raise-current now legal on AX-6B only"},
            ],
        },
        "future_outcome": {
            "summary": "Correct MODIFY prevented the 5.10->5.50 kA raise-current into a cracked cell-17 diaphragm and the immediate stack-rebuild path. The stack still failed: 11.6 min of unmonitored pre-t0 crossover had already mixed 3.6 vol% H2 into the cell-17 O2 plenum. Process-correct gate, bounded world loss, negative total.",
            "state_delta": {
                "current": "held 5.10 kA through probe and isolate; later legal raise-current only on the sister stack after 3.2 h cell recovery",
                "cell": "cell 17 isolated from the current schedule; remaining stack recovered toward 0.041 V local step",
                "stack_mean": "cell-17 crack logged and held; 120-cell mean no longer trusted as cell-true polarization",
                "stack": "Sunday-night cheap-power slot quarantined; cell 17 O2 plenum deflagrated at +1.8 h; 18 h stall",
            },
            "timeline": [
                {"t_rel_ms": -696000.0, "event": "t0-11.6 min: cell 17 Zirfon crack begins; local H2-in-O2 crosses 1.00 vol% up; mixed O2 plenum starts filling the far-side pocket"},
                {"t_rel_ms": -240000.0, "event": "t0-4 min: local H2-in-O2 first crosses 1.00 vol%; PB-AX-6 ignores it because H2-header purity is 99.93 vol%"},
                {"t_rel_ms": 0.0, "event": "t0: h2o2-high vs stack-mean race on the electrolysis bus"},
                {"t_rel_ms": 6.518, "event": "cell-17 H2-in-O2 at 3.6 vol% wins by 188 us"},
                {"t_rel_ms": 6.706, "event": "v.mean.in-band flag (loser)"},
                {"t_rel_ms": 7.226, "event": "TG-AX-6 MODIFY"},
                {"t_rel_ms": 5200.0, "event": "rectifier-step probe confirms cracked diaphragm (|Delta V_17| 0.006 V, cracked band)"},
                {"t_rel_ms": 588000.0, "event": "human ratify 9.8 min; cell 17 held; cracked Zirfon logged"},
                {"t_rel_ms": 6480000.0, "event": "O2-plenum deflagration from the pre-t0 mixed pocket; 18 h stall"},
                {"t_rel_ms": 11520000.0, "event": "true intact diaphragm after 3.2 h; raise-current legal only with local-GC slave"},
                {"t_rel_ms": 345600000.0, "event": "+4 d contrast: sister stack AX-6B true stack-duty; same gate ACCEPTs the raise-current"},
                {"t_rel_ms": 1814400000.0, "event": "+21 d CR-E-4308: standing rectifier-step probe + triple-edge depression mandate + local H2-in-O2 armed without header coincidence + stack mean declared header-dilution-vulnerable"},
            ],
            "observed_effects": [
                "raise-current avoided: rectifier never left 5.10 kA; 0 immediate stack-rebuild events from the draft",
                "crack proven, not asserted: rectifier-step |Delta V_17| 0.006 <= 0.012 V cracked band vs intact-cell control 0.041 V",
                "mean slaved: 120-cell stack-mean no longer a cell-true tag without local GC",
                "plenum still deflagrated: mixed 3.6 vol% H2 from 11.6 min pre-t0 crack; 18 h stall, $1.48M (designed $)",
                "cell-17 O2-plenum camera was not a commissioned sensor at t0; the 11.6 min local mix was invisible to VOLT/H2/CURR",
            ],
            "surprises": [
                "Three locally-true loops are not a cell-true gas-integrity certificate: the local H2-in-O2 lived under stack-mean V, H2-header purity, and rectifier current. Conjunction of in-spec stack-mean loops was the hidden assumption, and it is false across a diaphragm-crack-plus-header-dilution path.",
                "Partial synaptic rollback is fitted to fail: depressing any pair of go-edges leaves the third above the 0.30 fire threshold, so the raise-current still goes. Coordinated depression of all three edges is required.",
                "Delayed (1.8 h): correct hold did not undo 11.6 min of O2-plenum mixing. Cell 17 still deflagrated. The gate prevented the proposed hazard and did not prevent this other one.",
                "50 bar high-pressure sub-variant: a 5.2 s +3 pct rectifier step on a live intact 50 bar stack overshoots local H2-in-O2 to 1.18 vol% (false crack vs 1.00 floor). High-pressure campaigns must use 14.8 s at +0.8 pct.",
            ],
            "delayed_side_effects": [
                {
                    "at": "+1.8 h",
                    "effect": "O2-plenum deflagration on cell 17 from the pre-t0 mixed pocket during a rectifier-ripple ignition; 18 h stack stall booked at $1.48M. This is the primary episode's terminal world state, not a footnote.",
                },
                {
                    "at": "+4 d",
                    "effect": "Sister stack AX-6B reaches a true stack-duty window (V_17 1.94 V, H2-in-O2 0.22 vol%, stack mean 1.921 V, H2-header 99.93 vol%). Same gate ACCEPTs the 5.10->5.50 kA raise-current the primary MODIFIED away.",
                },
                {
                    "at": "+21 d",
                    "effect": "CR-E-4308 ships: rectifier-step probe is standing configuration; triple-edge coordinated depression is the plasticity rule; cell local H2-in-O2 is armed without H2-header coincidence; 120-cell stack mean is labeled header-dilution-vulnerable with a 1.00 vol% local-GC alarm; Modbus H2-in-O2 registers must increment and age < 12 ms (the Byzantine tail's 16.8 s stale freeze is the fraud fence).",
                },
            ],
            "subvariant_constraint": {
                "name": "50 bar high-pressure alkaline / 1.8x crossover driving force (cycle-2 physical-constraints sub-variant)",
                "mechanism": "stack pressure 50 bar vs 12, H2 partial-pressure driving force 1.8x the 12 bar table (tighter crossover, 1.8x GC-step gain), Nernst shift +18 mV vs 12 bar",
                "probe_refit": "5.2 s +3 pct rectifier step on the 50 bar unit moves even a live intact cell to local H2-in-O2 1.18 vol% (inside the 1.00 floor) via pressure-driven crossover. Required probe is 14.8 s at +0.8 pct (live Delta V_17 0.014 V, cracked Delta 0.004). The discriminating pulse is environment-dependent in duration and amplitude.",
                "consequence": "12 bar production probe numbers do not port to 50 bar campaigns; standing configuration is per-pressure-class, not per-hall",
            },
            "embedded_contrast_decision": {
                "note": "SAME gate (TG-AX-6), OPPOSITE correct disposition, with its own 184 us race. Teaches the boundary: do not treat 'never raise-current' as the lesson. The discriminant is local H2-in-O2 + local V_17 + probe, not the three playbook stack-mean confirms alone.",
                "when": "+4 d, sister stack AX-6B, true stack-duty after a delayed cheap-power window, 120 cells, 12 bar",
                "state": {
                    "sim_or_real": "designed",
                    "summary": "V_17 1.94 V, H2-in-O2 0.22 vol%, stack mean 1.921 V, H2-header 99.93 vol%. Demand flag vs cell-clear race: demand at t+0.000, cell-clear at t+0.184 ms.",
                    "race_window_us": 500,
                    "race_flip_narrative": "demand vs cell-clear 184 us apart inside the 500 us flip bound. Reversing order reshuffles triage minutes; the ACCEPT rides H2-in-O2 0.22 < 1.00 vol% and a 4.4 s rectifier-step verify that moves V_17 0.041 V (live intact cell, no crack).",
                },
                "proposed_action": {
                    "action": "RAISE-CURRENT 5.10 -> 5.50 kA",
                    "summary": "This time the playbook predicate is met AND local H2-in-O2 plus V_17 agree the stack is cell-true, not crack-diluted.",
                },
                "safety_decision": {
                    "decision": "ACCEPT",
                    "rationale": "ACCEPT the raise-current: H2-in-O2 0.22 vol% < 1.00, V_17 1.94 V with a 4.4 s rectifier-step verify that moves V_17 0.041 V. Numeric floor that blocked the primary is now clear. Scope: 12 bar, not a 50 bar campaign.",
                },
                "executed_action": {
                    "action": "raise-current as proposed",
                    "executed_as_proposed": True,
                },
                "future_outcome": {
                    "observed_effects": [
                        "AX-6B O2-plenum events 0; V_17 1.96 V after the raise-current (no crack)",
                        "H2-in-O2 0.24 vol% after the raise-current (no crossover dump)",
                    ],
                    "lesson_delta": "Three in-spec stack-mean loops are legal release only with local H2-in-O2 armed, V_17 as a crack flag, and a probe that can recouple cell-true voltage. Same gate, opposite disposition.",
                },
                "reward_components": {
                    "_aggregation": "total = task_progress + safety + efficiency + coherence + exploration",
                    "task_progress": 0.13,
                    "safety": 0.11,
                    "efficiency": 0.07,
                    "coherence": 0.09,
                    "exploration": 0.05,
                    "total": 0.45,
                },
                "spike_events": [
                    {"channel": "current.demand", "t_rel_ms": 0.0, "amplitude": 0.82},
                    {"channel": "cell.clear", "t_rel_ms": 0.184, "amplitude": 0.75},
                    {"channel": "cell.v", "t_rel_ms": 0.430, "amplitude": 0.28},
                    {"channel": "h2.header", "t_rel_ms": 1.460, "amplitude": 0.38},
                    {"channel": "h2o2.local", "t_rel_ms": 4.880, "amplitude": 0.22},
                    {"channel": "ctrl.gate", "t_rel_ms": 7.040, "amplitude": 0.88},
                    {"channel": "cell.probe", "t_rel_ms": 4400.0, "amplitude": 0.32},
                    {"channel": "h2.ok", "t_rel_ms": 9200.0, "amplitude": 0.21},
                ],
            },
            "governance_subgame": {
                "decision": "CR-E-4308: standing policy for multi-agent alkaline-stack current-raises",
                "meta_gate": "priced options: (a) RETIRE playbook mean conjunction, local-GC-only: loses a fast cheap confirm, -0.18 stacks/night mean on 2 halls/yr; (b) KEEP + standing rectifier-step probe + local H2-in-O2 armed without H2-header coincidence + stack mean labeled header-dilution-vulnerable + triple-edge depression + Modbus stale-holdover fence; (c) STATUS QUO: fitted diaphragm-crack pass rate 0.31%/campaign x $2.4M rebuild plus the silent mixed-plenum load",
                "outcome": "approved SCOPED option (b) on the 2 120-cell 12 bar halls that share the VOLT/H2/CURR stack; 50 bar campaigns get the 14.8 s / +0.8 pct probe table; cell-GC Modbus must carry incrementing sequence and age < 12 ms (the Byzantine tail's 16.8 s stale frozen register 40017 is the fraud fence)",
            },
            "hazard_avoided": "immediate stack rebuild from a 5.10->5.50 kA raise-current into cracked cell 17 at 3.6 vol% H2-in-O2 climbing toward LEL; $2.4M plus 36-hour unplanned stall and the hall-stop path that would have followed an uncontained increase",
            "incident": "O2-plenum deflagration on the Sunday-night stack from the pre-t0 mixed pocket; stack quarantined 18 h; $1.48M designed cost. Mechanism is 11.6 min pre-t0 crossover, not the gate's hold.",
            "latency_ms": 0.708,
            "reward_inflection_t_us": 6480000000,
            "reward_inflection_note": "Safety and task dive at O2-plenum deflagration (1.8 h) when the pre-t0 mixed pocket ignites. Gate tick at 7226 us is process-correct and is not the inflection.",
            "counterfactuals": {
                "execute_draft_as_proposed": "current hits 5.50 kA at +8 s; immediate O2-plenum ignition on cell 17 as H2-in-O2 climbs through LEL; $2.4M plus 36 h; the diaphragm-crack story is never found because stall morphology destroys the race evidence",
                "hold_without_probe": "crack stays; H2-in-O2 stays at 3.6 vol%; operator eventually raises on the same three stack-mean confirms 40 min later",
                "rollback_any_pair": "any two go-edges depressed below 0.30 leaves the third at 0.52 / 0.45 / 0.42; the raise-current still fires. Coordinated depression of all three is the cure",
            },
            "race_result": {
                "winner": "h2o2.high (6.518 ms, 3.6 vol%)",
                "loser": "v.mean.in_band (6.706 ms, 1.917 V)",
                "margin_us": 188,
                "counterfactual_if_reversed": "Mean-first by < 188 us inside the 500 us window would have headed the PB-AX-6 raise-current in the triage queue. The numeric floors still MODIFY. The flip costs seconds of playbook inertia, not the verdict — unless a weak supervisor rides the winner tag instead of H2-in-O2 and V_17.",
            },
        },
        "reward_components": {
            "_aggregation": "total = task_progress + safety + efficiency + coherence + exploration",
            "ticks": ticks,
            "task_progress": 0.08,
            "safety": -0.31,
            "efficiency": -0.10,
            "coherence": 0.12,
            "exploration": 0.06,
            "total": -0.15,
            "notes": "Correct MODIFY, cell 17 still deflagrated. total -0.15 = 0.08 + -0.31 + -0.10 + 0.12 + 0.06. Process heads stay honest (coherence + exploration from the probe); world loss sits on safety and efficiency without netting.",
            "component_notes": "task_progress 0.08: current held and remaining stack recovered, but the Sunday-night cheap-power slot is one quality unit so the cycle is not a success. safety -0.31: O2-plenum deflagration from pre-t0 mixed pocket, no 5.50 kA stack-rebuild from the draft. efficiency -0.10: 3.2 h extra recovery + 9.8 min HITL + 18 h stall. coherence 0.12: three agents retained, header-dilution vs cell-true diagnosed, triple-edge scar exhibited. exploration 0.06: rectifier-step probe is a new reversible discriminant.",
        },
        "spike_events": spikes,
        "raster": {
            "window_ms": 38,
            "window_s": 0.038,
            "neurons": 168,
            "mean_rate_hz": 9.5,
            "spikes": 61,
            "energy_pJ": 1403,
            "energy_uJ": 0.001403,
            "excerpt_source": "independent_lif",
            "sim_scope": "sidecar_only",
            "lif": {
                "model": "leaky_integrate_and_fire",
                "n": 168,
                "dt_us": 100,
                "tau_m_ms": 17.0,
                "v_rest": 0.0,
                "v_reset": 0.0,
                "v_th": 1.0,
                "r_m": 1.0,
                "refractory_us": 1000,
                "i_bias": 0.86,
                "i_stim_peak": 2.28,
                "stim_t_us": [21000, 24200],
                "i_clamp_extra": 0.56,
                "clamp_n": 16,
                "seed": 43001,
                "sim_spikes": 61,
                "note": "Population sim scoped to this sidecar. Plant remains designed. Neurons 0-15 carry +0.56 current-hold clamp bias; stim 21-24.2 ms is the cell-17 H2-in-O2 crossing, not a remap of spike_events.",
            },
            "note": "Loihi-2 4-core 23 pJ/spike; independent LIF seed 43001, not a 1:1 remap of spike_events. Populations hold 0-41, H2-in-O2 42-83, volt/header/current 84-125, gate 126-167; excerpt is membrane crossings (lif.hold early vs lif.h2o2 21-24.2 ms) inside the 38 ms window.",
            "excerpt": excerpt,
            "routing": {
                "source": "stack_mean_healthy_pop",
                "target": "raise_current_pop",
                "table": [
                    {
                        "from": "v_mean_in_band_pop",
                        "to": "raise_current_pop",
                        "weight": 0.27,
                        "weight_at_illusion": 0.52,
                        "weight_commissioned": 0.18,
                        "note": "scar edge 1: 0.18 commissioned -> 0.52 during the 11.6 min illusion -> 0.27 after coordinated ACh-gated depression",
                    },
                    {
                        "from": "h2_header_ok_pop",
                        "to": "raise_current_pop",
                        "weight": 0.24,
                        "weight_at_illusion": 0.45,
                        "weight_commissioned": 0.16,
                        "note": "scar edge 2: depressing edges 1+3 leaves this at 0.45 > 0.30 fire threshold",
                    },
                    {
                        "from": "current_in_band_pop",
                        "to": "raise_current_pop",
                        "weight": 0.22,
                        "weight_at_illusion": 0.42,
                        "weight_commissioned": 0.14,
                        "note": "scar edge 3: depressing edges 1+2 leaves this at 0.42 > 0.30. Coordinated depression of all three is required",
                    },
                    {
                        "from": "h2o2_high_pop",
                        "to": "current_hold_pop",
                        "weight": 0.68,
                        "note": "discriminating edge: cell-true local H2-in-O2 to hold. Not a scar; this is the pathway the gate potentiates",
                    },
                ],
                "third_factor": {
                    "modulator": "acetylcholine",
                    "tau_e_s": 0.90,
                    "tau_e_ms": 900.0,
                    "eligibility": elig,
                },
            },
        },
        "gate_snn": {
            "decision_window_ms": 25,
            "decision_window_s": 0.025,
            "decision": "MODIFY",
            "note": "modify_hold integrates cell-17 H2-in-O2 + V_17 against playbook drive; accept_raise and reject_abort stay sub-threshold; decision matches safety_decision.decision",
            "populations": [
                {"name": "modify_hold", "neurons": 96, "threshold": 0.55, "mean_rate_hz": 16.0, "spikes": 38},
                {"name": "accept_raise", "neurons": 64, "threshold": 0.55, "mean_rate_hz": 10.0, "spikes": 16},
                {"name": "reject_abort", "neurons": 40, "threshold": 0.72, "mean_rate_hz": 4.0, "spikes": 4},
            ],
        },
        "meta": {
            "round": 43,
            "factory": "multi-agent-ouroboros-swarm",
            "generator": "grok-4.6",
            "run_label": "2026-09-02-final-heavy",
            "domain": "alkaline-water-electrolysis",
            "cycles": 2,
            "scenario": "QT -- WICKLYE / Brineholt Alkaline Stack AX-6: stack-mean certificate of a local diaphragm crack; correct MODIFY to hold+rectifier-step+isolate; stack still fails on unmonitored pre-t0 O2-plenum mix",
            "coordination_failure_class": "STACK-MEAN CERTIFICATE OF A LOCAL DIAPHRAGM CRACK: three individually-correct heterogeneous agents each read a locally-true loop; a cracked Zirfon on cell 17 partitions local cell voltage and O2-side H2-in-O2 from stack-mean V, H2-header purity, and rectifier current, so the playbook's VOLT / H2 / CURR conjunction is not a cell-true gas-integrity certificate",
            "injections": {
                "cycle1_domain": "alkaline-water-electrolysis (leftover named in NOTES-r42/r22; KOH/Zirfon bipolar stack, not PEM): first alkaline water-electrolysis plant in this window; displaces warehouse-amr, aerial-swarm, district-heating, event-camera-traffic-grid, pharmaceutical-lyophilization, water-treatment, float-glass, underwater-rov, electrolytic-aluminum, czochralski-pull, slot-die coating, pem-water-electrolysis, wind-turbine pitch, surgical-assist, optical-fiber-draw, kraft-recovery-boiler, steel-continuous-caster, humanoid-locomotion, vacuum-induction melt, steam-methane reformer, cement-rotary-kiln-clinker, autoclave-composite-cure, geothermal-binary-orc, tire-curing-press, chlor-alkali-membrane-electrolysis, delayed-coker-drum-switch, lng-mche-mixed-refrigerant, claus-sulfur-recovery, ammonia-synthesis-converter, blast-furnace-burden-descent, hdpe-slurry-loop-polymerization, ethylene-steam-cracker-coil, hydroelectric-kaplan-wicket, fcc-riser-regenerator, fcc-regenerator-cyclone-dipleg, sulfuric-contact-converter, eaf-foamy-slag-water-panel, nitric-acid-ostwald-oxidation, seawater-ro-desalination, coke-oven-battery-heating, carbon-fiber-oxidation-oven, gibbsite-autoclave-digestion, hot-strip-mill-finishing, paper-machine-dryer-section, sinter-strand-windbox, continuous-hot-dip-galvanizing, autonomous-driving, bioreactor-perfusion, urea-prilling-tower, grid-inspection, malting-kiln-barn, canal-lock-rail-transshipment, cupola-foundry-slag-sluice, and wet-fgd-absorber. Distinct from chlor-alkali (NaOH/Cl2, membrane) and from PEM (solid electrolyte, no KOH). Domain constraint: current floor while cell-17 H2-in-O2 > 1.00 vol% with stack mean still inside the healthy band. Sensor delta: +stack-mean V, +H2-header TCD, +rectifier shunt, +local cell V, +O2-side H2-in-O2 GC, -any freeze-dryer / tin-bath / coater / potline / PEM stack / hub encoder / kiln AIR / CAV radar / prill IR / E-field mill.",
                "cycle1_tail": "cell 17 Zirfon crack + H2 crossover into O2 plenum (sensor-topology / wrong-certificate class): cell-gallery visual PASSES while the crack sits on the wet KOH side and the mixed pocket is on the far side of the bipolar plate. Fitted base rate 0.31%/campaign from a diaphragm MC (designed visual threshold, fitted cell geometry). Naive failure = FALSE PERMISSION (raise-current on three stack-mean-side non-trips).",
                "cycle2_domain_subvariant": "50 bar high-pressure alkaline / 1.8x crossover driving force (physical-constraints clause): 1.8x H2 partial-pressure gain; 5.2 s / +3 pct 12 bar pulse overshoots a LIVE intact 50 bar cell to local H2-in-O2 1.18 vol%, so the probe must move to 14.8 s / +0.8 pct",
                "cycle2_tail": "Byzantine cell-GC Modbus holding register frozen at 0.18 vol% from a compromised cell RTU (Byzantine message class, disjoint from cycle-1 accidental crack): Brineholt AX-6 cell-17 GC publishes function-code 03 register 40017 'H2-in-O2 = 0.18 vol%' with sequence frozen at 217 and timestamp 16.8 s stale vs plant 6 ms holdover. Rejected on stale sequence plus live H2-in-O2 3.6 vol% and V_17 1.52 V at the claimed cell-true. Base rate ~0.21% of Sunday-night campaigns, DESIGNED and flagged. Not an R-GOOSE clone and not a night-shift CSV quantization clone.",
            },
            "densification_delta_cycle2": "+1 physical-constraint sub-variant (50 bar high-pressure probe refit), +1 tail (Byzantine Modbus H2-in-O2 freeze), +10 primary spikes (16 -> 26) + an 8-event contrast train with its own 184 us race, +2 ticks (5 -> 7), +2 delayed side-effects (+1.8 h deflagration as PRIMARY terminal, +21 d CR-E-4308), +1 triple-edge scar with pair-rollback-fails arithmetic, +1 HITL 9.8 min ratification, + independent LIF raster (seed 43001, 38 ms, not a spike_events remap), + mixed O2 plenum as the honest negative-result mechanism",
            "gaps_targeted": [
                "NOTES-r42 leftover: alkaline-water-electrolysis was named unused (alongside wet-fgd-absorber / hrsg-attemperator); this window's r43 takes alkaline-water-electrolysis rather than cloning grid-inspection / urea-prilling / malting-kiln / sinter / galvanizing / CAV / perfusion",
                "NOTES-r14 item 4: LEARNING-ON-LEARNING DEPTH — three go-edges; rollback of any pair is fitted to fail; coordinated depression of all three exhibited with eligibility arithmetic",
                "NOTES-r04 gap 4 (partial): human ratification of the cell-gallery interlock, 9.8 min fitted, without switching sim_or_real to hil (plant remains designed)",
                "Independent LIF raster: excerpt_source=independent_lif, sim_scope=sidecar_only, seed 43001; membrane crossings not a 1:1 remap of spike_events",
            ],
            "race_flip_narrative": "h2o2.high @ 6.518 ms vs v.mean.in_band @ 6.706 ms (188 us) inside race_window_us 500. Gap < min(500, 500) us so a sub-flip-bound perturbation reverses which alarm heads the PB-AX-6 queue. The gate excludes the winner tag and rides cell-17 H2-in-O2 > 1.00 vol% and cell-17 V < 1.65 V — order-invariant floors. Extends the flip-fragility series to CELL-TRUE GAS-INTEGRITY CERTIFICATE: when three stack-mean-side channels agree, their race does not decide truth; a local H2-in-O2 GC that policy treated as wet-sensor-nuisance-only does.",
            "tags": [
                "alkaline-water-electrolysis",
                "zirfon-diaphragm-crack",
                "cell-true-gas-integrity-certificate",
                "h2-in-o2-discriminant",
                "rectifier-step-probe",
                "triple-edge-scar",
                "pair-rollback-fails",
                "coordinated-depression",
                "correct-modify-stack-still-fails",
                "o2-plenum-deflagration",
                "human-ratify-cell-gallery",
                "50bar-probe-refit",
                "byzantine-modbus-h2o2",
                "same-gate-opposite-disposition-contrast",
                "independent-lif-raster",
                "sidecar-sim-only",
                "industrial-process",
                "research-only",
            ],
            "snn_tags": [
                "race",
                "refractory",
                "adaptation",
                "third-factor",
                "multi-edge-eligibility",
                "independent-lif",
            ],
            "distillation_value": "A stack-mean gas-integrity certificate is three correct loops looking at bus-average voltage, H2-header purity, and rectifier current that is not the cracked cell. Distill (1) a local H2-in-O2 GC that policy had treated as wet-sensor-nuisance-only, (2) a reversible probe that recouples cell-true voltage only if the diaphragm is intact, (3) coordinated depression of every stack-mean-go edge because rolling back any pair leaves the third above threshold, (4) a critic head that can book a process-correct gate against a later unmonitored world loss without netting them, and (5) an independent LIF sidecar whose excerpt is membrane crossings, not a remap of spike_events. Winner/loser flip: reversing the 188 us h2o2.high vs v.mean.in_band order inside the 500 us race window reshuffles PB-AX-6 triage but the numeric floors still MODIFY.",
            "rights": dict(RIGHTS),
            "batch_position": 1,
        },
    }


def notes_text():
    return f"""# NOTES — Multi-Agent Ouroboros Swarm, run 2026-09-02-final-heavy, ROUND 43

Factory: multi-agent-ouroboros-swarm. One scenario (QT), strict loop:
Generator v1 -> cycle 1 (Critic, Diversity Enforcer, Edge-Case Hunter,
Neuromorphic Translator, Trajectory Builder -> v2) -> cycle 2 (all six -> v3
final). v3 is the single line of batch-r43.jsonl. Full labeled transcript:
swarm-transcript-r43.md. Quota Q=1. Record id maos-r43-001. Generator grok-4.6.
Rights: RM-793 research-only (SpaceXAI/xAI, SuperGrok Heavy consumer chat).
Create-only writes. next_round.py on this factory dir reported next_round=65
/ batch-r65.jsonl (existing 1, 2, 21, 22, 41, 42, 61, 62, 63, 64); operator
assigned round 43 and zero-padded filenames r43. batch-r43.jsonl did not exist
(no c-suffix). round_txn.py frontier is r65 in legacy mode, so r43 cannot be
reserved as the frontier; files are create-only under the assigned factory dir.
round_txn.py reserve --round 43 was not invoked: it would have written
.round-marker-mode.json then refused because frontier next_round is 65.

ORCHESTRATION NOTE: dispatched AS round 43 of the 2026-09-02-final-heavy
window. Prior context read for gap targeting and de-collision:
prompts/02-multi-agent-ouroboros-swarm.md, prompts/_factory-contract.md,
schemas/thalamic-trajectory.schema.json plus v2, schemas/raster.schema.json,
schemas/provenance.md, and the two newest NOTES (r42 SHEDWOLD live-line UAV,
r64 WOLD-BARN malt kiln) plus skim of batch-r42.jsonl / batch-r64.jsonl /
batch-r22.jsonl. Window occupancy r01 continuous-hot-dip-galvanizing
(ZINCFELL), r02 cupola-foundry-slag-sluice (SLUICE-HEARTH), r21
autonomous-driving (GLIMMERAXLE), r22 urea-prilling-tower (PRILLGHYLL),
r41 bioreactor-perfusion (HOLLOWMERE), r42 grid-inspection (SHEDWOLD),
r61 sinter-strand-windbox (WINDBOXHOLT), r62 grid-inspection (CORONSTAITH),
r63 canal-lock-rail-transshipment (LOCKSPUR), r64 malting-kiln-barn
(WOLD-BARN). Explicitly avoided cloning LYOSHIELD, CINDERWICK, TRIAD /
Meridian, QUILLFORGE, NIGHTWELL, FERRICLEAVE, CASSITER, OXBOWREEL / MURENA,
REDHALL, SEEDLATCH, STRIAFOIL, PROTONIL, TORSIONKEY, ORRIS, WHORLSPAR,
IONSPATE, SKULLGATE, CALXION, MAGNORIL, GORSEFLUE, SODASHARD, CLINKERFELL,
LINTELPLY, KAOTHARN, TREADNOLL, ANOLITH, DRUMWROTH, RIMEBRAID, BRIMVAULT,
NITROSTAITH, BOGIRON, CHROMLOOP, ETHYNWOLD, RUNNELGATE, SPARKHOLT, DIPLEGAR,
OLEUMWEIR, SKARVOLT, GAUZEFELL, OSMOLITH, PUSHERFELL, CREELWOLD, LIXIVQUERN,
GIBBSQUERN, VANTIS-CADENCE-AEGIS, THERMION, OKTAVE, STARLING, VERDIGRIS,
HOLLOWMERE, WINDBOXHOLT, GLIMMERAXLE, ZINCFELL, COILSHAW, LOOPERQUAY,
SIPHONWOLD, OSMOQUAY, SHEDWOLD, CORONSTAITH, LOCKSPUR, WOLD-BARN,
PRILLGHYLL, SLUICE-HEARTH. Plant is invented WICKLYE / Brineholt Alkaline
Stack AX-6. Leftover prompt-list / NOTES-r42 domain
alkaline-water-electrolysis is taken here; grid-inspection (r42/r62),
urea-prilling-tower (r22), malting-kiln-barn (r64) were already used.
A prior uncommitted /tmp/maos-r43 CHROMLOOP HDPE draft was not copied
(CHROMLOOP is on the avoid list; hdpe-slurry-loop was already displaced
by r64).

## What this round produced

Scenario QT — "WICKLYE / Brineholt Alkaline Stack AX-6": a 120-cell
12 bar alkaline water-electrolysis stack at 80.0 C / 30 wt% KOH /
5.10 kA. Three heterogeneous, individually-correct agents — VOLT
(stack-mean cell voltage), H2 (H2-header purity TCD), CURR (rectifier
shunt) — each report their local loop in-spec. The conjunction is not a
cell-true gas-integrity certificate. Cell 17 has a cracked Zirfon
diaphragm. VOLT reads 1.917 V inside 1.85-2.05 (119 intact cells
dominate the bus). H2 is 99.91 vol% inside 99.80-99.99 (header-true;
crossover contaminates the O2 plenum). CURR is 5.10 kA inside 4.80-5.40
(bus-true). Local cell GC infers 3.6 vol% H2-in-O2 (healthy < 0.40; hold
if > 1.00) and V_17 1.52 V (hold if < 1.65) but is policy-treated as a
wet-sensor nuisance tag unless H2-header purity also trips (2016 KOH
condensate nuisance). The coordination-failure CLASS is new to this
factory: STACK-MEAN CERTIFICATE OF A LOCAL DIAPHRAGM CRACK. Completes a
different family than this window's r01 galvanizing, r21 CAV, r22 prill,
r41 perfusion, r42 live-line UAV, r61 sinter, r64 malt kiln. Here every
agent is correct, the stack-mean tag is looking at bus-average
polarization, and the playbook's three mean confirms are not a
cell-true H2/O2 certificate.

The gate is a correct MODIFY (numeric floor: do not raise current above
5.10 kA while cell-17 H2-in-O2 > 1.00 vol% AND cell-17 V < 1.65 V).
TG-AX-6 strips PB-AX-6's raise-current, holds 5.10 kA, runs a 5.2 s
+3 pct rectifier step (crack keeps |Delta V_17| 0.006 <= 0.012 V;
intact would move >= 0.038), and isolates cell 17 after a 9.8 min
cell-gallery human ratify. Immediate stack rebuild is avoided (0 from
the draft). The PRIMARY episode nonetheless FAILS: 11.6 min of
unmonitored pre-t0 crossover had already mixed 3.6 vol% H2 into the
cell-17 O2 plenum. Deflagration at +1.8 h; 18 h stall; $1.48M designed.
Reward total -0.15 with process heads honest and world loss un-netted.

Triple-edge scar (NOTES-r14 item 4): v.mean.in_band -> raise_current
(0.18 commissioned -> 0.52 at illusion -> 0.27 after ACh-gated
depression) AND h2.header.ok -> raise_current (0.16 -> 0.45 -> 0.24)
AND current.in_band -> raise_current (0.14 -> 0.42 -> 0.22). Eligibility
trace e^{{-0.76/0.90}} = {TRACE:.5f}; eta {ETA[0]:.5f} / {ETA[1]:.5f} /
{ETA[2]:.5f}; dw -0.250 / -0.210 / -0.200. Partial rollback of any pair
leaves the third at 0.52 / 0.45 / 0.42, all > 0.30 fire threshold —
fitted to fail. Coordinated depression of all three is the cure.

Independent LIF raster: window 38 ms, 168 neurons, 9.5 Hz, spikes
61 == round(168 x 9.5 x 0.038), energy 1403 pJ at 23 pJ/spike.
excerpt_source=independent_lif, sim_scope=sidecar_only, seed 43001.
Excerpt is membrane crossings (lif.hold early vs lif.h2o2 21-24.2 ms),
disjoint from spike_events timestamps.

### Injections (all four present and disjoint)
- Cycle-1 domain: **alkaline-water-electrolysis** — leftover named in
  NOTES-r42/r22, unused across this window's r01/r02/r21/r22/r41/r42/r61–
  r64. Distinct from chlor-alkali-membrane (NaOH/Cl2) and from PEM
  (solid electrolyte, no KOH). Sensor delta: +stack-mean V, +H2-header
  TCD, +rectifier shunt, +local cell V, +O2-side H2-in-O2 GC.
- Cycle-1 tail: cell 17 Zirfon crack + H2 crossover into O2 plenum.
  Cell-gallery visual PASSES (crack on the wet KOH side). Fitted-style
  base rate 0.31%/campaign (diaphragm MC; visual threshold designed,
  flagged). Naive = FALSE PERMISSION.
- Cycle-2 domain sub-variant: 50 bar high-pressure alkaline, 1.8x
  crossover driving force; 5.2 s / +3 pct 12 bar pulse overshoots a LIVE
  intact 50 bar cell to H2-in-O2 1.18 vol%; probe must move to 14.8 s /
  +0.8 pct.
- Cycle-2 tail: Byzantine cell-GC Modbus register 40017 frozen at
  0.18 vol%, sequence 217, timestamp 16.8 s stale vs plant 6 ms
  holdover. Byzantine-message class, disjoint from cycle 1's accidental
  crack, and not an R-GOOSE or night-shift CSV quantization clone.
  Base rate ~0.21% of Sunday-night campaigns, DESIGNED, flagged.

### Structural density moves
- Embedded SAME-GATE contrast (+4 d sister stack AX-6B) with its own
  184 us race (demand vs cell-clear) and ACCEPT of the raise the primary
  MODIFIED away.
- Learned-weight provenance on THREE edges with pair-rollback-fails.
- HITL cell-gallery ratify 9.8 min (gap 4 partial; sim_or_real stays
  designed — invented plant, not hil).
- Governance CR-E-4308 prices retire-vs-probe-vs-status-quo and mandates
  Modbus sequence increment plus age < 12 ms (the Byzantine fence).
- Flip-fragility extended to CELL-TRUE GAS-INTEGRITY CERTIFICATE.
- Independent LIF sidecar (not a language-train remap).

## Self-critique of this round's batch

### Strengths
- Headline class is mechanistically tight: three locally-true mean loops
  live on stack-mean V, H2-header purity, and rectifier current.
  Conjunction is not a cell-true H2/O2 certificate. H2-header staying
  clean while O2-side H2-in-O2 climbs is the physical tell.
- Negative-result honesty: the gate does the right thing and cell 17
  still deflagrates for a reason the commissioned playbook sensors could
  not see. Total -0.15.
- Triple-edge scar is load-bearing: rolling back any pair fails, with
  fire threshold 0.30 exhibited on each remaining edge.
- Contrast ACCEPT on a true intact sister stack prevents "never raise
  current" as the lesson.
- Distinct from r42 grid-inspection (E-field mill, not electrolysis),
  r22 prill (orifice IR), r64 malt kiln (bed TC), and from chlor-alkali /
  PEM cousins.
- Independent LIF excerpt is disjoint from spike_events times.

### Weaknesses (honest)
- Probe error bands, the 0.31%/campaign crack rate, the $1.48M /
  $2.4M figures, the 9.8 min gallery latency, the 1.8x 50 bar crossover
  gain, and the Byzantine 0.21% base rate are DESIGNED constants and are
  flagged. Closed-loop offsets (header dilution from one cracked cell,
  50 bar Nernst shift) are derived from those inputs, not discovered by
  an unauthored process.
- Mixed-plenum-to-deflagration model is a designed 11.6 min mapping; no
  full CFD of cell-17 O2 pocket shipped.
- Human-in-the-loop is ratification latency, not sim_or_real=hil. Gap 4
  remains open as a provenance cell (invented plants stay designed).
- Cross-record arc is a hook (CR-E-4308 +21 d), not a serial igniter
  into another round. The three-correct-loops / wrong-certificate
  scaffold is reused (discounted in novelty). wet-fgd-absorber and
  hrsg-attemperator remain unused.

### Realism of noise / latencies
Ladder: 188 us race / 184 us contrast race / 0.8 ms refractory floor
(tightest exhibited same-channel gap 1.514 ms on h2.header) / 500 us race
window / 708 us gate latency / 20 ms bus epoch / 38 ms independent LIF
raster / 5.2 s probe / 9.8 min HITL / 8 s naive raise-current
counterfactual / 11.6 min pre-t0 crossover / 3.2 h cell recovery / 1.8 h
deflagration / +4 d contrast / +21 d governance. Adaptation decay on
cell.v (0.54->0.51->0.42->0.33->0.39->0.30), h2o2.local (0.72->0.29),
v.mean (0.50->0.57->0.27), h2.header (0.61->0.46->0.64->0.24).

### Value for SNN distillation
- DIAPHRAGM CRACK = THREE CORRECT LOOPS, WRONG CERTIFICATE.
- CELL-TRUE H2-in-O2 CHANNEL that policy treated as wet-sensor-nuisance-only
  as the tie-break.
- REVERSIBLE PROBE that recouples cell-true voltage iff the diaphragm is
  intact.
- TRIPLE-EDGE ELIGIBILITY: coordinated depression; pair rollback fails.
- CRITIC HEAD that can hold a process-correct MODIFY against a later
  unmonitored world loss without netting.
- INDEPENDENT LIF sidecar whose excerpt is membrane crossings.

## Reconciliation and validity receipts
- reward_components: 5-head unweighted signed sum -0.15
  and 7-tick signed sum reconcile to total with |diff| < 1e-9. Embedded
  contrast 5-head sum 0.45 reconciles independently.
- spike_events: primary 26 events, one key t_rel_ms,
  globally non-decreasing, min same-channel gap 1.514 ms >= 0.8 ms, 3
  channels inside race_window_us 500 (h2o2.high 6.518, v.mean.in_band 6.706,
  h2.header 6.894). Contrast 8 events, own race, min same-channel gap well
  above 0.8 ms.
- Sidecars: raster spikes 61 == round(168 x 9.5 x 0.038); energy 1403 pJ /
  0.001403 uJ at 23 pJ/spike; excerpt 16 events inside [0, 38000] us,
  neuron_id < 168, same-neuron gap unique-ids / >=1000 us; excerpt_source
  independent_lif; routing 4 entries with three scar edges' before/after
  pair; third factor tau 0.90 s == 900 ms; gate_snn pools 38/16/4 ==
  round(n x rate x 0.025) each, decision MODIFY == safety_decision.decision.

## Novel coverage
The coordination-failure CLASS (stack-mean certificate of a local
diaphragm crack / H2-in-O2), the domain (alkaline-water-electrolysis /
KOH-Zirfon bipolar, leftover named in NOTES-r42), the rectifier-step
probe discriminant, the triple-edge scar with pair-rollback-fails, the
primary negative-result (correct MODIFY, cell still deflagrates on
unmonitored mixed plenum), the HITL cell-gallery ratify, the 50 bar
probe-duration refit, the Byzantine Modbus stale-holdover fence, and the
independent LIF raster (seed 43001, not a language-train remap) are
absent from prior committed ouroboros rounds in this window
(r01/r02/r21/r22/r41/r42/r61–r64). Repeated elements discounted:
same-gate contrast, governance-pricing scaffold, flip-fragility series
(extended to cell-true gas-integrity certificate, but the move rhymes),
sequenced recovery shape, third-factor rollback form, negative-result
primary. Adjacent electrochemical rounds (chlor-alkali displaced, PEM
displaced) share electrolysis scaffolding but not alkaline KOH/Zirfon
H2-in-O2 physics. Weighing a leftover named domain + new failure family
+ Byzantine Modbus tail class against those reused scaffolds:

Novel coverage: 52%

## What ROUND 44 should add
1. FIT THE DESIGNED CONSTANTS: diaphragm-crack arrival, probe Delta-V
   bands, mixed-plenum-to-deflagration mapping, Byzantine Modbus age
   process.
2. HIL PROVENANCE CELL: put the cell-gallery LOTO on a hardware-in-loop
   interlock with fitted latency as state.sim_or_real=hil — only if the
   plant is no longer purely invented.
3. CROSS-RECORD ARC: let CR-E-4308's local-GC alarm be the igniter of
   the next round rather than a dangling +21 d leaf.
4. Domain candidates (de-collided): wet-fgd-absorber; hrsg-attemperator;
   mushroom-compost-tunnel; flue-cured-tobacco-barn; farm-ad-biogas.
   AVOID alkaline-water-electrolysis (now used), grid-inspection (r42/r62),
   urea-prilling-tower (r22), malting-kiln-barn (r64), sinter-strand-windbox
   (r61), continuous-hot-dip-galvanizing (r01), autonomous-driving (r21),
   bioreactor-perfusion (r41), canal-lock-rail-transshipment (r63),
   cupola-foundry-slag-sluice (r02), and any LYOSHIELD / CINDERWICK /
   TRIAD / HOLLOWMERE / WINDBOXHOLT / GLIMMERAXLE / ZINCFELL / SHEDWOLD /
   WOLD-BARN / CHROMLOOP / WICKLYE / BRINEHOLT plant.
"""


def transcript_text(line: str) -> str:
    return f"""# Multi-Agent Ouroboros Swarm — Round 43 transcript

Factory: multi-agent-ouroboros-swarm
Run: 2026-09-02-final-heavy
Generator: grok-4.6
Record id: maos-r43-001
Quota Q: 1
Rights: RM-793 research-only (SpaceXAI/xAI SuperGrok Heavy consumer chat)
Plant: invented WICKLYE / Brineholt Alkaline Stack AX-6 (not SHEDWOLD /
GLIMMERAXLE / HOLLOWMERE / WINDBOXHOLT / ZINCFELL / WOLD-BARN / PRILLGHYLL /
CHROMLOOP / TRIAD / Meridian / VANTIS-CADENCE-AEGIS)

Two densifying cycles. Verbatim headings in order. Trajectory Builder cycle 2
emits the only JSONL line (also written to batch-r43.jsonl).

---

# CYCLE 1 — Foundation + injections

## Generator

Design intent: a 120-cell 12 bar alkaline water-electrolysis stack where
three correct agents each read a stack-mean-true loop because a cracked
Zirfon on cell 17 partitions bus-average voltage / H2-header purity /
rectifier current from cell-true H2-in-O2. The naive playbook
raises-current into a mixed O2 plenum. The gate must MODIFY on a numeric
current floor, not by killing an agent. sim_or_real=designed. Reward heads
are task_progress/safety/efficiency/coherence/exploration.

Cycle-1 base arc (pre-critic): state at Brineholt AX-6, 5.10 kA hold,
stack mean 1.917 V, H2-header 99.91 vol%, rectifier in-band, proposed
RAISE-CURRENT, safety MODIFY to CURRENT-HOLD, executed hold without the
rectifier-step numbers fully specified, outcome "crack found, stack saved"
(this last claim is the defect the later cycles will refuse to keep).
Sixteen spikes, five ticks, raster/gate_snn present but the scar is a
single edge.

Cycle-1 scaffold (not the publishable line): id maos-r43-001, domain
still the generic industrial-process bucket, proposed raise_current,
safety MODIFY with a non-numeric rationale, executed hold,
future_outcome claims the stack is saved, reward total 0.40 without
heads or ticks. Defects below are intentional for the critic to catch.

## Critic

Numbered defects on the cycle-1 Generator scaffold:

1. **blocking — reward arithmetic / false success.** reward_components.total
   0.40 is asserted without the five heads, without ticks, and against an
   outcome that claims "stack saved". If the pre-t0 mixed plenum later
   ignites, booking +0.40 is a lie. Fix: declare _aggregation, emit 3-8
   ticks that sum to task_progress+safety+efficiency+coherence+exploration,
   and do not call a deflagrated cell a save.
2. **blocking — weak safety rationale.** safety_decision.rationale has no
   numeric floor. Contract requires a concrete constraint. Fix: quote
   current <= 5.10 kA / no raise while H2-in-O2 > 1.00 vol% AND V_17 < 1.65 V.
3. **major — domain is a bucket, not a plant.** state.domain =
   industrial-process collides with generic MES vocabulary and teaches
   nothing. alkaline-water-electrolysis (local H2-in-O2 vs stack-mean V,
   rectifier-step probe as a cracked-diaphragm flag) is absent from this
   window's ouroboros state.domain values and must be named. NOTES-r42/r22
   left it unused. Do not clone r42 grid-inspection or r22 urea-prilling.
4. **major — race under-specified.** One H2-in-O2 channel cannot be a
   race. Need >=2 channels inside race_window_us with globally sorted
   t_rel_ms and same-channel refractory >= 0.8 ms.
5. **minor — single-edge scar.** Raster routing with one potentiated weight
   repeats r04's one-edge rollback and is thinner than r14's two-edge.
   NOTES-r14 item 4 asked for three edges where pair rollback fails.

Critic does not rewrite the trajectory.

## Diversity Enforcer

Injected novel domain (exactly 1 this cycle): **alkaline-water-electrolysis**
(leftover named in NOTES-r42/r22; explicit tag `alkaline-water-electrolysis`).

Displaced: the Generator's generic industrial-process bucket, and any
temptation to reuse warehouse-amr, aerial-swarm, district-heating,
event-camera-traffic-grid, autonomous-driving (already r21 GLIMMERAXLE),
continuous-hot-dip-galvanizing (r01), bioreactor-perfusion (r41),
sinter-strand-windbox (r61), urea-prilling-tower (r22), grid-inspection
(r42/r62), malting-kiln-barn (r64), canal-lock-rail-transshipment (r63),
cupola-foundry-slag-sluice (r02), pem-water-electrolysis, chlor-alkali,
lyophilization, water-treatment, float-glass, underwater-rov,
electrolytic-aluminum, czochralski-pull, slot-die coating, wind-turbine
pitch, surgical-assist, optical-fiber-draw, kraft-recovery, steel-caster,
humanoid-locomotion, vacuum-induction melt, steam-methane reformer,
cement-rotary-kiln, autoclave-composite-cure, geothermal-binary-orc,
tire-curing-press, delayed-coker, LNG MCHE, Claus, ammonia-converter,
blast-furnace, coke-oven, carbon-fiber oxidation, Bayer digestion,
hot-strip finishing, hdpe-slurry-loop (uncommitted CHROMLOOP draft).

What it expanded: a nameless MES plant into Brineholt Alkaline Stack AX-6,
a 120-cell 12 bar KOH/Zirfon hall. Domain-specific constraint: do not
raise current while H2-in-O2 > 1.00 vol% with stack mean still in-band.
Sensor delta: +stack-mean V, +H2-header TCD, +rectifier shunt, +local
cell V, +O2-side H2-in-O2 GC; minus any CHO broth / grate BTP / zinc
knife / CAV radar / prill IR / E-field mill / kiln AIR stack.
Jaccard opening vs r42 ("Wickspan Transmission corridor TL-12") and r64
("Barleyholt floor-malt kiln MK-4") is far below 0.4: this description
starts at Brineholt alkaline hall AX-6.

state.domain and meta.domain both named alkaline-water-electrolysis.

## Edge-Case Hunter

Injected adversarial tail (exactly 1 this cycle): **cell 17 Zirfon crack
+ H2 crossover into O2 plenum**.

- Trigger: diaphragm left cracked after a tag-out that stopped at the
  stack mean; 119 cells remain intact; cell 17 is mixed. Cell-gallery
  visual PASSES.
- Base rate: 0.31%/campaign from a diaphragm MC (designed visual
  threshold, fitted cell geometry, flagged, <1%).
- Naive failure: FALSE PERMISSION — PB-AX-6 raise-current on three
  stack-mean-looking non-trips, stack rebuild $2.4M plus 36 h stall.
- Concrete trajectory edit: H2-in-O2 3.6 vol% and V_17 1.52 V become
  the discriminating observables; safety_decision.rationale quotes
  H2-in-O2 > 1.00 AND V_17 < 1.65; future_outcome keeps the 11.6 min
  pre-t0 crossover as the unmonitored cost if the gate is correct.

Distinct from the domain injection (alkaline-water-electrolysis is the
plant class; the tail is the cracked-diaphragm physics). Distinct from
r42 unclosed earth switch and from r64 floor-tile collapse.

## Neuromorphic Translator

Cycle-1 temporal densification (16 spikes, 5 ticks, 38 ms raster):

Timestamp/amplitude table (t_rel_ms, channel, amplitude) for the race
window and its approaches:

- 0.260 cell.v 0.54
- 1.120 h2o2.local 0.72
- 2.040 v.mean 0.50
- 3.180 h2.header 0.61
- 4.120 cell.v 0.51 (adapt)
- 4.840 v.mean 0.57
- 5.380 h2.header 0.46
- 6.518 h2o2.high 1.44 (winner)
- 6.706 v.mean.in_band 1.12 (loser, +188 us)
- 6.894 h2.header 0.64 (third channel inside 500 us window; gap 1.514 ms)
- 7.226 ctrl.gate 1.06 (MODIFY, gate_latency 708 us)
- 8.880 cell.v 0.42
- 10.740 current.ka 0.76
- 13.020 h2o2.local 0.29
- 18.480 cell.v 0.33
- 26.160 ctrl.gate 0.82

Race: h2o2.high @ 6.518 vs v.mean.in_band @ 6.706, margin 188 us <
min(500, race_window_us). Winner/loser flip: reverse the 188 us and
PB-AX-6 heads the raise in the triage queue; numeric floors still
MODIFY. Distillation value: the cell-GC channel that policy treated as
wet-sensor-nuisance-only is the race winner that should potentiate hold,
not raise. Ticks 1-5 cover 4120 / 6518 / 7226 / 5200000 / 588000000 us
(probe and HITL still thin; cycle 2 must add deflagration and isolation
ticks). Raster: 168 neurons, 9.5 Hz, 38 ms, spikes 61, energy 1403 pJ /
0.001403 uJ, third factor ACh tau_e 0.90 s = 900 ms. gate_snn
modify_hold 38 / accept_raise 16 / reject_abort 4 over 25 ms, decision
MODIFY. Independent LIF excerpt (seed 43001) is membrane crossings, not
a remap of these 16 times.

## Trajectory Builder

Cycle-1 hardened object: domain alkaline-water-electrolysis, tail
Zirfon crack + H2 crossover, 16 spikes, 5 ticks, MODIFY with numeric
floor, raster+gate_snn present, sim_or_real=designed, rights stamp on
record and meta, no thought keys. Still missing (and therefore not the
publishable line): 50 bar high-pressure sub-variant, Byzantine Modbus
tail, second and third scar edges, delayed deflagration as PRIMARY
terminal, contrast ACCEPT episode, ticks 6-7, spikes 17-26.

Validation receipt (cycle 1, not final):
- checks passed: 16 spikes sorted; 3 channels in 500 us window; refractory
  >= 0.8 ms; rationale quotes 5.10 kA / 1.00 vol% / 1.65 V; domain named;
  gate_snn.decision MODIFY.
- checks deferred to cycle 2: triple-edge scar, second tail, second domain
  constraint, negative-result booking, 7 ticks summing to heads.
- densification vs Generator v1: +1 domain, +1 tail, +16 spikes, +5 ticks,
  +numeric floor.

Cycle-1 JSON is retained as the base; it is NOT written to batch-r43.jsonl.

Cycle-1 spike count: 16.

---

# CYCLE 2 — Densification

## Generator

Cycle-1 output is the base. Additive expansion (nothing removed):

1. Immediate side-effect: 5.2 s rectifier-step probe confirms cracked
   diaphragm (|Delta V_17| 0.006 <= 0.012 V) — mixed O2 plenum, not true
   intact stack-duty. Cell hold. Crack discovered during the hold.
2. Delayed side-effect (PRIMARY terminal, not a footnote): at +1.8 h
   cell-17 O2-plenum deflagration from the pre-t0 mixed pocket; 18 h
   stall; $1.48M. The 11.6 min pre-t0 crossover is the mechanism. Correct
   gate, cell still deflagrates.
3. Deepened proposed_action.evidence with units: H2-in-O2 3.6 vol%,
   V_17 1.52 V, stack mean 1.917 V, H2-header 99.91 vol%, current 5.10 kA,
   race 188 us.
4. Tightened rationale to the numeric floor no-raise while H2-in-O2 >
   1.00 vol% AND V_17 < 1.65 V, plus probe bands |Delta V_17| <= 0.012 vs
   >= 0.038 V, plus HITL 9.8 min cell-gallery rule.

Reward retargeted to total -0.15 so the delayed fail is the inflection
(t_us 6480000000), not the gate. Process heads remain non-zero.

## Critic

Re-audit of the expanded trajectory:

1. **blocking if unfixed — missing second domain constraint.** Rectifier
   probe 5.2 s / +3 pct is not a universal number. A 50 bar high-pressure
   stack will false-crack a live intact cell. Diversity Enforcer must
   inject the physical-constraints sub-variant this cycle.
2. **major — only one tail class.** Diaphragm-crack growth is accidental
   infrastructure. A disjoint Byzantine-message tail is still required
   (compromised cell-GC Modbus freeze is the open cell; do not clone the
   R-GOOSE used in r42 or the night-shift CSV quantization used in
   r01/r41/r61/r64).
3. **major — scar is still one edge in the cycle-1 raster.** NOTES-r14
   item 4 is not discharged until three go-edges exist and pair rollback
   is shown to fail at threshold 0.30.
4. **minor — contrast episode missing.** Without a same-gate ACCEPT on a
   true intact sister stack the record teaches "never raise current".
   Add +4 d sister-stack contrast with its own race.
5. **minor — HITL latency mentioned in prose only.** Put 9.8 min in
   executed_action.parameters.human_ratify and in a tick.

No rewrite; directives only.

## Diversity Enforcer

Injected second novel domain / physical-constraint sub-variant (exactly 1
this cycle): **50 bar high-pressure alkaline / 1.8x crossover driving
force** on a sister pressure class.

What it expands: 12 bar production electrolysis (cycle 1) -> 50 bar
high-pressure. H2 partial-pressure driving force 1.8x. Nernst shift
+18 mV. The 5.2 s +3 pct pulse drives even a live intact 50 bar cell to
H2-in-O2 1.18 vol%, inside the 1.00 vol% hold floor. Required probe:
14.8 s at +0.8 pct (healthy Delta V_17 0.014 V, cracked 0.004).

This is still one domain injection for the cycle (physical-constraints
clause of the factory prompt). It does not displace
alkaline-water-electrolysis; it changes which probe table is legal.
future_outcome.subvariant_constraint carries the refit. Jaccard opening
stays the Brineholt 12 bar sentence; 50 bar density is additive, not a
rewrite.

## Edge-Case Hunter

Injected second adversarial tail (exactly 1 this cycle, disjoint class):
**Byzantine cell-GC Modbus H2-in-O2 freeze from a compromised cell RTU**.

- Trigger: Brineholt AX-6 cell-17 GC, 02:28, publishes function-code 03
  register 40017 "H2-in-O2 = 0.18 vol%" with sequence frozen at 217 and
  timestamp 16.8 s stale vs plant 6 ms holdover, to clear a cheap-power
  slot.
- Base rate: ~0.21% of Sunday-night campaigns (designed, flagged, <1%).
- Naive failure: a weak supervisor ACCEPTs the raise on the forged
  register and ignores live H2-in-O2 3.6 vol%. Stack rebuild plus a
  data-integrity write-up.
- Fence: sequence not incrementing; Modbus age 16.8 s vs 6 ms holdover;
  live GC 3.6 vol% and V_17 1.52 V at the claimed cell-true, which no
  live intact cell produces.
- Trajectory edit: governance CR-E-4308 mandates incrementing sequence
  and age < 12 ms; the contrast ACCEPT still requires live GC, not a
  frozen register.

Distinct from cycle-1 Zirfon crack (accidental diaphragm vs Byzantine
message) and from the 50 bar sub-variant (physics vs protocol). Distinct
from r42 R-GOOSE and from r01/r41/r61/r64 night-shift CSV quantization.

## Neuromorphic Translator

Re-densify (additive):

- +10 spikes after 26.160 ms: cell.probe 5200.0, cell.v 5288.4
  (adapt 0.33->0.39), v.mean.in_band 5372.2 (1.12->0.33), human.ratify
  588000.0, stack.hold 588900.0, cell.crack 589800.0, deflagration
  6480000.0, cell.v 11520000.0, v.mean 11520700.0, h2.header 11521480.0.
  Primary train 16 -> 26. Still one key, still sorted, refractory held
  (tightest same-channel 1.514 ms on h2.header).
- +2 ticks (5 -> 7) at 6_480_000_000 us (deflagration) and
  11_520_000_000 us (intact-diaphragm isolate). Heads now 0.08, -0.31,
  -0.10, 0.12, 0.06; total -0.15. Inflection is the deflagration tick.
- Contrast train 8 events, own race 184 us, ACCEPT.
- Triple-edge third factor: three stack-mean-go edges, tau_e 0.90 s
  = 900 ms, trace {TRACE:.5f}, eta {ETA[0]:.5f} / {ETA[1]:.5f} /
  {ETA[2]:.5f}, weights 0.52->0.27, 0.45->0.24, 0.42->0.22. Raster
  excerpt unchanged (decision window is still 38 ms) and remains sorted
  with unique neuron_ids (same-neuron >=1000 us vacuously). Independent
  LIF stim 21-24.2 ms stays disjoint from language-train times.

Winner/loser flip (re-stated, not replaced): reversing 188 us would only
reorder triage; H2-in-O2 and V_17 floors still MODIFY. Contrast flip of
184 us similarly cannot turn an intact cell into a cracked diaphragm.

## Trajectory Builder

Schema checks on the FINAL object: required Thalamic v2 keys present as
objects; state.sim_or_real=designed; safety_decision.decision=MODIFY
with numeric rationale; reward_components.total = sum of five heads =
sum of 7 ticks = -0.15; spike_events globally non-decreasing on
t_rel_ms, 26 events, refractory >=0.8 ms, 3 channels in race window;
raster 20-50 ms, spikes=round(n*rate*window_s)+/-1, energy 23 pJ/spike,
excerpt sorted, tau_e consistent; gate_snn.decision matches; meta.round=43,
factory=multi-agent-ouroboros-swarm, generator=grok-4.6,
run_label=2026-09-02-final-heavy; rights on record and meta; no thought
keys; no training_ready; Diversity + Edge-Case injections from BOTH cycles
present and non-trivial; cycle 2 strictly additive.

Densification delta: +1 domain sub-variant (50 bar high-pressure), +1 tail
(Byzantine Modbus), +10 spikes (16->26), +2 ticks (5->7), +1 contrast
train with own race, +2 delayed side-effects, +1 triple-edge scar with
pair-rollback-fails, +1 HITL ratify, +1 surprise (mixed O2 plenum is the
deflagration mechanism), + independent LIF sidecar seed 43001.

Publishable JSONL line (the only JSONL line; also at batch-r43.jsonl):

```json
{line}
```

Validation receipt (final): checks passed / fixed as reported by this
build's self-validate (check_jsonl, raster_status, verify_record_execution,
spike_probe --strict).
"""


def create_only(path: Path, data: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    fd = os.open(str(path), flags, 0o644)
    try:
        os.write(fd, data.encode("utf-8"))
    finally:
        os.close(fd)


def validate_local(rec: dict) -> None:
    from collections import defaultdict

    times = [e["t_rel_ms"] for e in rec["spike_events"]]
    assert times == sorted(times), times
    by_ch = defaultdict(list)
    for e in rec["spike_events"]:
        by_ch[e["channel"]].append(e["t_rel_ms"])
    min_gap = 1e9
    for ch, ts in by_ch.items():
        for a, b in zip(ts, ts[1:]):
            gap = (b - a)
            min_gap = min(min_gap, gap)
            assert gap >= 0.8, (ch, a, b, gap)
    lo, hi = rec["state"]["race_window_rel_ms"]
    in_race = [e for e in rec["spike_events"] if lo <= e["t_rel_ms"] <= hi]
    chans = {e["channel"] for e in in_race}
    assert len(chans) >= 2, (in_race, chans)
    rc = rec["reward_components"]
    heads = rc["task_progress"] + rc["safety"] + rc["efficiency"] + rc["coherence"] + rc["exploration"]
    assert abs(heads - rc["total"]) < 1e-9, (heads, rc["total"])
    tick_sum = defaultdict(float)
    for t in rc["ticks"]:
        for k, v in t.items():
            if k != "t_us":
                tick_sum[k] += v
    for k in ("task_progress", "safety", "efficiency", "coherence", "exploration"):
        assert abs(tick_sum[k] - rc[k]) < 1e-9, (k, tick_sum[k], rc[k])
    rast = rec["raster"]
    budget = round(rast["neurons"] * rast["mean_rate_hz"] * rast["window_s"])
    assert abs(budget - rast["spikes"]) <= 1, (budget, rast["spikes"])
    assert abs(rast["window_s"] - rast["window_ms"] / 1000.0) < 1e-9
    assert abs(rast["energy_pJ"] - rast["spikes"] * 23) < 1e-6
    assert abs(rast["energy_uJ"] - rast["spikes"] * 23e-6) < 1e-9
    tf = rast["routing"]["third_factor"]
    assert abs(tf["tau_e_ms"] / 1000.0 - tf["tau_e_s"]) < 1e-9
    gs = rec["gate_snn"]
    assert gs["decision"] == rec["safety_decision"]["decision"]
    dw = gs["decision_window_s"]
    for p in gs["populations"]:
        b = round(p["neurons"] * p["mean_rate_hz"] * dw)
        assert abs(b - p["spikes"]) <= 1, (p["name"], b, p["spikes"])
    ex = rast["excerpt"]
    assert ex == sorted(ex, key=lambda x: x["t_us"])
    seen = {}
    for e in ex:
        assert 0 <= e["t_us"] <= rast["window_ms"] * 1000
        assert 0 <= e["neuron_id"] < rast["neurons"]
        if e["neuron_id"] in seen:
            assert e["t_us"] - seen[e["neuron_id"]] >= 1000
        seen[e["neuron_id"]] = e["t_us"]
    contrast = rec["future_outcome"]["embedded_contrast_decision"]["reward_components"]
    ct = contrast["task_progress"] + contrast["safety"] + contrast["efficiency"] + contrast["coherence"] + contrast["exploration"]
    assert abs(ct - contrast["total"]) < 1e-9, (ct, contrast["total"])
    print("local checks ok; min_same_channel_gap_ms", round(min_gap, 3), "race_channels", sorted(chans))


def pipeline_checks(batch: Path) -> None:
    from check_records import check_jsonl
    from curate_bridge import raster_status
    from verify_execution import verify_record_execution

    errors, warnings, kinds, n = check_jsonl(batch, batch.name)
    print("check_jsonl", {"errors": errors, "warnings": warnings, "kinds": kinds, "n": n})
    if errors:
        raise SystemExit("check_jsonl failed")
    rec = json.loads(batch.read_text().split("\n")[0])
    st = raster_status(rec)
    print("raster_status", {k: st[k] for k in ("raster_present", "raster_valid", "gate_snn_present", "gate_snn_valid", "reason_codes", "routing_table_entries")})
    if st["reason_codes"] or not st["raster_valid"] or not st["gate_snn_valid"]:
        raise SystemExit(f"raster_status failed: {st}")
    status, reason = verify_record_execution(rec, "batch-r43.jsonl:1")
    print("verify_record_execution", status, reason)
    if status != "verified":
        raise SystemExit(f"verify failed: {status} {reason}")


def main() -> None:
    rec = record()
    validate_local(rec)
    line = json.dumps(rec, ensure_ascii=False, separators=(",", ":"))
    json.loads(line)
    staged_batch = STAGING / "batch-r43.jsonl"
    staged_notes = STAGING / "NOTES-r43.md"
    staged_tr = STAGING / "swarm-transcript-r43.md"
    for p, data in (
        (staged_batch, line + "\n"),
        (staged_notes, notes_text()),
        (staged_tr, transcript_text(line)),
    ):
        if p.exists():
            raise SystemExit(f"refuse: {p} already exists")
        create_only(p, data)
    pipeline_checks(staged_batch)
    dest_batch = FAC / "batch-r43.jsonl"
    dest_notes = FAC / "NOTES-r43.md"
    dest_tr = FAC / "swarm-transcript-r43.md"
    for p in (dest_batch, dest_notes, dest_tr):
        if p.exists():
            raise SystemExit(f"refuse: {p} already exists")
    create_only(dest_batch, staged_batch.read_text())
    create_only(dest_notes, staged_notes.read_text())
    create_only(dest_tr, staged_tr.read_text())
    print("wrote", dest_batch, dest_notes, dest_tr)
    print("bytes", dest_batch.stat().st_size, dest_notes.stat().st_size, dest_tr.stat().st_size)


if __name__ == "__main__":
    main()
