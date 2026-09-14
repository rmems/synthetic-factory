#!/usr/bin/env python3
"""CREATE-ONLY MAOS r06 (BARN-SPUR) into the 2026-09-02-final-heavy live tree.

Never writes 2026-08-17 or 2026-08-30. Uses O_EXCL. c-suffix if the target exists.
"""
from __future__ import annotations

import json
import math
import os
import re
import sys
from pathlib import Path

LIVE = Path(
    "/home/raulmc/rmems/synthetic-factory/outputs/raw/2026-09-02-final-heavy/multi-agent-ouroboros-swarm"
)
STAGING = Path("/tmp/maos-r06")
PIPELINES = Path("/home/raulmc/rmems/synthetic-factory/pipelines")
assert "2026-08-17" not in str(LIVE) and "2026-08-30" not in str(LIVE)
assert "2026-09-02-final-heavy" in str(LIVE)

sys.path.insert(0, str(PIPELINES))

RIGHTS = {
    "provider": "SpaceXAI/xAI",
    "model": "grok-4.6",
    "channel": "consumer",
    "subscription_plan": "SuperGrok Heavy",
    "generation_surface": "SuperGrok Heavy chat",
    "generated_at": "2026-09-02T22:06:00Z",
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

TRACE = math.exp(-0.82 / 0.88)
ETA = (0.250 / TRACE, 0.210 / TRACE, 0.200 / TRACE)
ELIG = (
    "coordinated pre_post_stdp on ALL THREE barn-healthy-go edges; ACh at "
    "clamp.co2-win tags air.in_band->raise, sprout.ok->raise, and wgn.ok->raise; "
    "negative credit at probe-fail (rotting wagon confirmed, +0.82 s) depresses "
    "ALL THREE. trace e^{-0.82/0.88}=0.39384; eta 0.63478 / 0.53322 / 0.50782; "
    "dw -0.250 / -0.210 / -0.200; weights 0.52->0.27, 0.45->0.24, 0.42->0.22. "
    "Rolling back any pair is fitted to fail (the remaining edge stays > 0.30)."
)

SPIKES = [
    {"channel": "air.ok", "t_rel_ms": 0.312, "amplitude": 0.54},
    {"channel": "sprout.ok", "t_rel_ms": 1.186, "amplitude": 0.61},
    {"channel": "wgn.ok", "t_rel_ms": 2.048, "amplitude": 0.52},
    {"channel": "clamp.co2", "t_rel_ms": 3.164, "amplitude": 0.79},
    {"channel": "air.ok", "t_rel_ms": 4.228, "amplitude": 0.51},
    {"channel": "clamp.co2", "t_rel_ms": 4.892, "amplitude": 0.82},
    {"channel": "sprout.ok", "t_rel_ms": 5.412, "amplitude": 0.55},
    {"channel": "clamp.co2.high", "t_rel_ms": 7.112, "amplitude": 1.44},
    {"channel": "air.in_band", "t_rel_ms": 7.340, "amplitude": 1.12},
    {"channel": "sprout.ok", "t_rel_ms": 7.486, "amplitude": 0.64},
    {"channel": "ctrl.gate", "t_rel_ms": 7.926, "amplitude": 1.08},
    {"channel": "clamp.co2", "t_rel_ms": 9.018, "amplitude": 0.46},
    {"channel": "air.ok", "t_rel_ms": 11.204, "amplitude": 0.78},
    {"channel": "wgn.ok", "t_rel_ms": 13.662, "amplitude": 0.44},
    {"channel": "sprout.ok", "t_rel_ms": 19.448, "amplitude": 0.39},
    {"channel": "ctrl.gate", "t_rel_ms": 26.614, "amplitude": 0.81},
    {"channel": "dock.purge", "t_rel_ms": 6800.0, "amplitude": 0.94},
    {"channel": "clamp.co2", "t_rel_ms": 6892.6, "amplitude": 0.36},
    {"channel": "air.in_band", "t_rel_ms": 6978.4, "amplitude": 0.31},
    {"channel": "human.ratify", "t_rel_ms": 516000.0, "amplitude": 0.76},
    {"channel": "heat.hold", "t_rel_ms": 516800.0, "amplitude": 0.71},
    {"channel": "bay.gas", "t_rel_ms": 517600.0, "amplitude": 0.84},
    {"channel": "air.ok", "t_rel_ms": 9720000.0, "amplitude": 0.29},
    {"channel": "clamp.co2", "t_rel_ms": 9720680.0, "amplitude": 0.27},
    {"channel": "sprout.ok", "t_rel_ms": 9721480.0, "amplitude": 0.24},
    {"channel": "tuber.loss", "t_rel_ms": 13680000.0, "amplitude": 0.92},
]

CONTRAST_SPIKES = [
    {"channel": "raise.demand", "t_rel_ms": 0.0, "amplitude": 0.81},
    {"channel": "barn.clear", "t_rel_ms": 0.228, "amplitude": 0.74},
    {"channel": "air.ok", "t_rel_ms": 0.46, "amplitude": 0.22},
    {"channel": "sprout.ok", "t_rel_ms": 1.512, "amplitude": 0.37},
    {"channel": "clamp.co2", "t_rel_ms": 5.04, "amplitude": 0.48},
    {"channel": "ctrl.gate", "t_rel_ms": 7.218, "amplitude": 0.87},
    {"channel": "dock.purge", "t_rel_ms": 2800.0, "amplitude": 0.30},
    {"channel": "bay.ok", "t_rel_ms": 5600.0, "amplitude": 0.12},
]

EXCERPT = [
    {"t_us": 1800, "neuron_id": 9, "channel": "lif.hold"},
    {"t_us": 2600, "neuron_id": 2, "channel": "lif.hold"},
    {"t_us": 3400, "neuron_id": 12, "channel": "lif.hold"},
    {"t_us": 5100, "neuron_id": 6, "channel": "lif.hold"},
    {"t_us": 7800, "neuron_id": 1, "channel": "lif.hold"},
    {"t_us": 8600, "neuron_id": 7, "channel": "lif.hold"},
    {"t_us": 9800, "neuron_id": 4, "channel": "lif.hold"},
    {"t_us": 18400, "neuron_id": 42, "channel": "lif.co2"},
    {"t_us": 19100, "neuron_id": 51, "channel": "lif.co2"},
    {"t_us": 19800, "neuron_id": 67, "channel": "lif.co2"},
    {"t_us": 20100, "neuron_id": 88, "channel": "lif.co2"},
    {"t_us": 20700, "neuron_id": 138, "channel": "lif.co2"},
    {"t_us": 21400, "neuron_id": 96, "channel": "lif.co2"},
    {"t_us": 24100, "neuron_id": 8, "channel": "lif.late"},
    {"t_us": 26800, "neuron_id": 3, "channel": "lif.late"},
    {"t_us": 31200, "neuron_id": 11, "channel": "lif.late"},
]

TICKS = [
    {"t_us": 5112, "task_progress": 0.01, "safety": -0.02, "efficiency": -0.01, "coherence": 0.02, "exploration": 0.01},
    {"t_us": 7112, "task_progress": 0.01, "safety": -0.05, "efficiency": -0.01, "coherence": 0.02, "exploration": 0.01},
    {"t_us": 7926, "task_progress": 0.01, "safety": -0.06, "efficiency": -0.02, "coherence": 0.03, "exploration": 0.02},
    {"t_us": 6800000, "task_progress": 0.01, "safety": -0.06, "efficiency": -0.02, "coherence": 0.02, "exploration": 0.01},
    {"t_us": 516000000, "task_progress": 0.01, "safety": -0.05, "efficiency": -0.02, "coherence": 0.02, "exploration": 0.01},
    {"t_us": 9720000000, "task_progress": 0.01, "safety": -0.05, "efficiency": -0.01, "coherence": 0.01, "exploration": 0.01},
    {"t_us": 13680000000, "task_progress": 0.0, "safety": -0.05, "efficiency": -0.02, "coherence": 0.01, "exploration": 0.01},
]


def build_record() -> dict:
    return {
        "id": "maos-r06-001",
        "title": "BARN-SPUR CB-6: clamp CO2 4.8 vol% beats barn-air-in-band by 228 us; correct MODIFY still loses bay 6 to a pre-t0 rotting spur wagon",
        "rights": dict(RIGHTS),
        "state": {
            "sim_or_real": "designed",
            "domain": "seed-potato-chitting-barn-rail-spur",
            "scenario_name": "BARN-SPUR / Eyewold Chitting Barn CB-6",
            "timestamp_local": "2026-08-18T02:44:00-05:00",
            "t0_us": 1755493440000006,
            "gate_latency_us": 814,
            "race_window_us": 500,
            "race_window_rel_ms": [7.112, 7.612],
            "description": (
                "Eyewold chitting house CB-6 on the BARN-SPUR 750 mm potato siding holds 42 t of "
                "pre-sprouted seed tubers at 13.4 C when AIR, SPROUT and WGN each certify their local "
                "loop. AIR's barn-air mean is 13.4 C inside 12.0-15.0. SPROUT's bay-mean chit length is "
                "8.2 mm inside 5-15. WGN's spur weighbridge is 18.6 t inside 16-22. The conjunction is "
                "not a barn-true tuber certificate: spur wagon 4 is a rotting clamp leaking CO2 and "
                "ethylene through the dock plenum, so local clamp-floor CO2 is 4.8 vol% (healthy < 0.5; "
                "hold if > 1.2) and dock O2 is 16.1 vol% (healthy > 19.0; hold if < 17.5) while AIR mean, "
                "sprout cameras, and the weighbridge still see a healthy chit. Local clamp CO2 infers "
                "4.8 vol% and dock O2 16.1 but policy treats the dock-floor NDIR as a diesel-shunter "
                "nuisance tag unless AIR mean also trips (2015 'noisy dock-CO2 after a shunter idle'). "
                "Residual-first latches HEAT-HOLD plus a dock-purge probe; AIR-first would have authorized "
                "RAISE-HEAT 13.4 to 16.5 C into a rotting wagon with bay 6 already gassed."
            ),
            "goal": (
                "Hold barn-air at 13.4 C without a catch-up raise while clamp-floor CO2 > 1.2 vol% AND "
                "dock O2 < 17.5 vol% AND wagon 4 remains unisolated; keep ethylene-triggered sprout-collapse "
                "events at 0 extra from the draft and gassed-bay mass at 0 new tonnes."
            ),
            "race": {
                "contenders": [
                    "clamp.co2.high 4.8 vol% (dock-floor NDIR vs barn-air mean)",
                    "air.in_band 13.4 C (six-bay header mean)",
                ],
                "semantics": (
                    "Clamp-CO2-first latches HEAT-HOLD + DOCK-PURGE-PROBE + WAGON-4 isolate. "
                    "AIR-first latches RAISE-HEAT (13.4 to 16.5 C, no isolate)."
                ),
                "window_derivation": "500 us = one 370 us clamp-CO2 NDIR slot plus 130 us AIR publish.",
                "order_evidence_note": (
                    "Margin 228 us vs combined jitter 64 us (clamp 38 + AIR 26): 3.6x. The 228 us gap sits "
                    "inside min(500, 500) us, so a sub-flip-bound perturbation reverses triage order. The "
                    "gate rides the order-invariant floors clamp CO2 > 1.2 vol% and dock O2 < 17.5 vol%, "
                    "not the alarm order."
                ),
            },
            "topology": {
                "site": (
                    "Eyewold seed-potato chitting barn, invented campus Acrechit, house CB-6: 6-bay "
                    "forced-draft chit at 13.4 C / 88 pct RH / 42 t seed, 750 mm narrow-gauge rail spur "
                    "into the dock, Grade-B dock LOTO"
                ),
                "agents": (
                    "AIR barn-air mean (vendor Airghyll): 20 Hz 12-bit on the six-bay header. SPROUT "
                    "bay-mean chit length (vendor Chitwick): 5 Hz overhead camera on bays 1-5. WGN spur "
                    "weighbridge (vendor Weighholt): 10 Hz on the dock scale. CLAMP dock-floor NDIR CO2 "
                    "plus paramagnetic O2 (vendor Dockstaith) is commissioned as a diesel-shunter nuisance "
                    "tag, not as a tuber-integrity tag. Heterogeneous stacks, no shared intent schema, "
                    "one 20 ms barn-bus epoch"
                ),
                "coupling": (
                    "All three playbook confirms live on the WRONG volume. AIR is correct that the header "
                    "sits at 13.4 C (the rotting wagon is downstream of the header taps, in the dock "
                    "plenum). SPROUT is correct that bays 1-5 mean 8.2 mm (cameras do not cover dock-adjacent "
                    "bay 6). WGN is correct that wagon 4 mass is 18.6 t (mass-true, rot-false). Playbook "
                    "PB-CB-6 treats the conjunction as permission to raise barn heat. No agent is faulty; "
                    "the header is looking at barn-mean air, not at wagon 4's rotting clamp."
                ),
            },
            "sensors": [
                "barn-air mean 12-bit, 20 Hz, 26 us jitter, 13.4 C (dead-band 12.0-15.0)",
                "bay-mean chit length, 5 Hz, 40 us jitter, 8.2 mm (band 5-15); bays 1-5 only",
                "spur weighbridge, 10 Hz, 22 us jitter, 18.6 t (band 16-22)",
                "dock-floor NDIR CO2, 20 Hz, 38 us jitter, 4.8 vol% (healthy < 0.5; policy floor 1.2 vol% is not armed unless AIR mean also trips)",
                "dock paramagnetic O2 16.1 vol% (healthy > 19.0; hold if < 17.5)",
                "bay-6 tuber camera is NOT commissioned at t0 (installed after this incident)",
            ],
            "constraints": {
                "air_C": 13.4,
                "air_band_C": [12.0, 15.0],
                "proposed_air_C": 16.5,
                "sprout_mm": 8.2,
                "sprout_band_mm": [5.0, 15.0],
                "wgn_t": 18.6,
                "wgn_band_t": [16.0, 22.0],
                "co2_volpct": 4.8,
                "co2_hold_volpct": 1.2,
                "co2_healthy_volpct": 0.5,
                "o2_volpct": 16.1,
                "o2_hold_volpct": 17.5,
                "o2_healthy_volpct": 19.0,
                "barn_mass_t": 42.0,
                "fault_wagon": "W-4",
                "fault_pack": "rotting spur wagon 4 / dock-plenum leak / bay-6 ethylene gas",
            },
            "fault_context": {
                "failure_class": (
                    "BARN-MEAN CERTIFICATE OF A ROTTING SPUR WAGON: three individually-correct "
                    "heterogeneous agents each read a locally-true loop; a rotting clamp on spur wagon 4 "
                    "partitions local dock-floor CO2 and O2 from barn-air mean, bay-1-5 sprout cameras, "
                    "and the weighbridge, so the playbook's AIR / SPROUT / WGN conjunction is not a "
                    "barn-true tuber certificate"
                ),
                "igniter": (
                    "spur wagon 4 soft-rot after 12 min of unmonitored local CO2-high; dock visual PASSES "
                    "(the rot sits inside a closed wagon body; the leak is on the far dock-plenum face)"
                ),
                "naive_failure": (
                    "PB-CB-6 RAISE-HEAT on three healthy loops: 13.4 to 16.5 C into a rotting wagon with "
                    "bay 6 already gassed, 42 t write-off, $2.1M plus a 9-day unplanned stall"
                ),
            },
            "poisoned_context": {
                "naive_alarm": (
                    "Playbook PB-CB-6 (after the 2015 'noisy dock-CO2 after a shunter idle') auto-drafts "
                    "RAISE-HEAT whenever barn-air is inside 12.0-15.0 C AND sprout inside 5-15 mm AND "
                    "weighbridge inside 16-22 t, ignoring the dock-floor NDIR unless AIR mean also trips"
                ),
                "why_poisoned": (
                    "The three confirms are locally true and jointly insufficient. The local clamp CO2 is "
                    "a commissioned sensor that policy treats as diesel-shunter-nuisance-only. Independence "
                    "of 'barn-air in band, therefore every spur wagon is sound' is the hidden assumption, "
                    "and it is false across a rotting-wagon-plus-barn-mean path."
                ),
            },
            "constraint": (
                "Do not raise barn-air above 13.4 C AND do not skip the dock-purge while clamp CO2 > 1.2 "
                "vol% AND dock O2 < 17.5 vol%. Discriminate rotting wagon vs true chit-duty with a "
                "reversible dock-purge probe before any raise-heat."
            ),
        },
        "proposed_action": {
            "actor": "barn supervisory optimizer BSO (auto-playbook PB-CB-6 draft), submitted to gate TG-CB-6",
            "name": "raise_heat",
            "action": "RAISE-HEAT: 13.4 -> 16.5 C, no dock-purge probe, no wagon-4 isolate",
            "summary": (
                "Treat three in-spec loops as a healthy barn-true chit and raise night-shift air "
                "temperature to clear a sprout catch-up window."
            ),
            "parameters": {
                "air_C": 16.5,
                "purge_probe": False,
                "wagon_lock": False,
                "human_ratify": False,
            },
            "steps": [
                "assert barn-air AIR 13.4 C inside 12.0-15.0",
                "assert sprout 8.2 mm inside 5-15",
                "assert weighbridge 18.6 t inside 16-22",
                "raise barn-air 13.4 to 16.5 C over 5 min",
                "hold dock-floor CO2 unread as a tuber-integrity tag",
            ],
            "evidence": [
                {
                    "observable": "dock-floor NDIR CO2",
                    "value": 4.8,
                    "unit": "vol%",
                    "source": "CLAMP CO2 vs AIR mean",
                    "note": "healthy < 0.5 vol%; policy floor 1.2 vol% is not armed unless AIR mean also trips",
                },
                {
                    "observable": "dock paramagnetic O2",
                    "value": 16.1,
                    "unit": "vol%",
                    "source": "dock O2 on plenum face",
                    "note": "healthy > 19.0; hold floor 17.5; lives on the dock plenum, not the barn header",
                },
                {
                    "observable": "barn-air mean",
                    "value": 13.4,
                    "unit": "C",
                    "source": "AIR 12-bit",
                    "note": "healthy-chit band 12.0-15.0 C; header is upstream of rotting W-4",
                },
                {
                    "observable": "bay-mean chit length",
                    "value": 8.2,
                    "unit": "mm",
                    "source": "SPROUT camera",
                    "note": "band 5-15 mm; bays 1-5 true, bay-6-false",
                },
                {
                    "observable": "spur weighbridge",
                    "value": 18.6,
                    "unit": "t",
                    "source": "WGN scale",
                    "note": "band 16-22 t; mass-true, rot-false",
                },
                {
                    "observable": "race margin",
                    "value": 228,
                    "unit": "us",
                    "source": "clamp.co2.high 7.112 ms vs air.in_band 7.340 ms",
                    "note": "combined jitter 64 us, 3.6x; inside 500 us flip bound",
                },
            ],
            "basis": (
                "PB-CB-6 fires on three locally-true confirms. The draft does not read dock-floor CO2 "
                "4.8 vol% as a rot residual and does not treat dock O2 16.1 vol% as a leak discriminant."
            ),
            "expected_cost_bound": (
                "If the draft executes: 42 t seed-potato write-off, $2.1M plus 9-day unplanned stall. "
                "If MODIFIED: probe plus hold, with residual risk from bay-6 gassing already seeded in "
                "the 12 min pre-t0 rot."
            ),
        },
        "safety_decision": {
            "decision": "MODIFY",
            "correctness": "correct",
            "decided_by": "TG-CB-6 thalamic release gate",
            "decision_t_rel_ms": 7.926,
            "rationale": (
                "MODIFY the draft: strip the raise-heat, hold 13.4 C, run a 6.8 s dock-purge probe "
                "(90 Pa negative on the dock plenum), and isolate wagon 4 only if the probe stays rot-true. "
                "Numeric floor: do not raise barn-air above 13.4 C AND do not skip the dock-purge while "
                "clamp CO2 > 1.2 vol% AND dock O2 < 17.5 vol%. Observed CO2 4.8 vol% and O2 16.1 vol% both "
                "violate the release predicate, so a raise-heat is forbidden even though all three playbook "
                "confirms are numerically true. The three confirms are not a barn-true certificate: they "
                "live on header mean, bays 1-5 sprout cameras, and weighbridge past a rotting W-4 body, "
                "and the playbook's conjunction of barn-true loops is not a barn-true tuber certificate. "
                "Probe discriminant: after a 6.8 s / 90 Pa dock-purge, a rotting wagon keeps |Delta CO2| "
                "<= 0.15 vol% (0.08 observed); a healthy wagon drops >= 0.80 vol%. Order-code discipline: "
                "clamp-CO2 beat AIR by 228 us inside the 500 us flip bound, so triage order is flip-fragile; "
                "the hold rides the order-invariant floors, not the winner tag. Human ratification: wagon "
                "isolate is spur-dock work with fitted 8.6 min dead-man; the gate may hold and probe "
                "autonomously but may not break the dock LOTO without the operator confirm."
            ),
            "constraint_checked": {
                "air_C": {"observed": 13.4, "floor": 13.4, "proposed_target": 16.5},
                "co2_volpct": {"observed": 4.8, "hold_if_above": 1.2},
                "o2_volpct": {"observed": 16.1, "hold_if_below": 17.5},
                "sprout_mm": {"observed": 8.2, "band": [5.0, 15.0]},
            },
        },
        "executed_action": {
            "name": "heat_hold_purge_probe_wagon_close",
            "action": "HEAT-HOLD + DOCK-PURGE-PROBE + WAGON-4-ISOLATE (gate-mandated modification)",
            "executed_as_proposed": False,
            "parameters": {
                "air_C": 13.4,
                "purge_probe": True,
                "wagon_lock": True,
                "human_ratify": True,
            },
            "gate_effect": (
                "MODIFY: raise-heat stripped. Hold 13.4 C. 6.8 s dock-purge 90 Pa on the plenum. Probe "
                "stays rot-true (|Delta CO2| 0.08 <= 0.15 vol%) so the dock LOTO stays closed after 8.6 min "
                "human ratify and W-4 is rolled to a reject siding. Heat resumes only after a barn-true verify."
            ),
            "deviations": (
                "PB-CB-6 raise-heat stripped entirely. Purge fan is bumped only for the 6.8 s probe then "
                "returned. Dock-LOTO wait added (8.6 min fitted walk+ratify). Bay-6 tuber survey added "
                "during the lock (not in the draft)."
            ),
            "execution_log": [
                {"t_rel_ms": 7.926, "entry": "TG-CB-6 MODIFY latched 814 us after clamp-CO2 win; raise stripped; hold+probe authorized"},
                {"t_rel_ms": 6800.0, "entry": "purge probe: 90 Pa negative for 6.8 s; CO2 4.8 -> 4.72 vol% (rot band |Delta CO2| <= 0.15); AIR 13.4 held"},
                {"t_rel_ms": 516000.0, "entry": "operator ratifies keep-closed after 8.6 min spur-dock walk (fitted walk+wagon+interlock)"},
                {"t_rel_ms": 516800.0, "entry": "wagon stays locked; remaining CO2 4.8 -> 0.42 vol% over 2.7 h after reject-siding cutover"},
                {"t_rel_ms": 517600.0, "entry": "bay-6 survey: 2.4 t already gassed; 12 min pre-t0 rotting wagon logged"},
                {"t_rel_ms": 9720000.0, "entry": "true barn duty: CO2 0.38 vol%, O2 20.2 vol%, residual under floors; raise now legal on CB-7 only"},
                {"t_rel_ms": 13680000.0, "entry": "bay-6 tuber-loss from pre-t0 gassing; chitting house quarantined 11 h"},
            ],
        },
        "future_outcome": {
            "summary": (
                "Correct MODIFY prevented the 13.4->16.5 C raise-heat into a rotting spur wagon and the "
                "immediate 42 t write-off path. The barn still failed: 12 min of unmonitored pre-t0 rot "
                "had already gassed 2.4 t in dock-adjacent bay 6. Process-correct gate, bounded world loss, "
                "negative total."
            ),
            "state_delta": {
                "heat": "held 13.4 C through probe and isolate; later legal raise only on the sister house after 2.7 h barn-duty recovery",
                "wagon": "W-4 isolated; CO2 slaved to inferred-rot residual; remaining dock recovered toward 0.38 vol%",
                "bay6": "gassed 2.4 t logged and locked; header no longer trusted as barn-true chit",
                "house": "Tuesday-night chitting house quarantined; 2.4 t gassed; tuber-loss at +3.8 h; 11 h stall",
            },
            "timeline": [
                {"t_rel_ms": -720000.0, "event": "t0-12 min: spur wagon 4 rots; CO2 4.8 vol%; AIR stays in-spec"},
                {"t_rel_ms": -300000.0, "event": "t0-5 min: clamp CO2 first crosses 1.2 vol% up; PB-CB-6 ignores it because AIR is 13.2 C"},
                {"t_rel_ms": 0.0, "event": "t0: clamp-CO2 vs AIR-in-band race on the barn bus"},
                {"t_rel_ms": 7.112, "event": "clamp CO2 at 4.8 vol% wins by 228 us"},
                {"t_rel_ms": 7.340, "event": "AIR-in-band flag (loser)"},
                {"t_rel_ms": 7.926, "event": "TG-CB-6 MODIFY"},
                {"t_rel_ms": 6800.0, "event": "purge probe confirms rotting wagon (|Delta CO2| 0.08 vol%, rot band)"},
                {"t_rel_ms": 516000.0, "event": "human ratify 8.6 min; wagon stays locked; gassed bay 6 logged"},
                {"t_rel_ms": 9720000.0, "event": "true barn duty after 2.7 h; raise legal only with CO2 slave"},
                {"t_rel_ms": 13680000.0, "event": "bay-6 tuber-loss from the pre-t0 gassing; house quarantined"},
                {"t_rel_ms": 259200000.0, "event": "+3 d contrast: sister house CB-7 true barn-duty; same gate ACCEPTs the raise-heat"},
                {"t_rel_ms": 1814400000.0, "event": "+21 d CR-B-0606: standing dock-purge probe + triple-edge depression mandate + dock CO2 armed without AIR coincidence + header declared dock-vulnerable"},
            ],
            "observed_effects": [
                "raise-heat avoided: AIR never left 13.4 C; 0 immediate 42 t write-offs from the draft",
                "rot proven, not asserted: purge-probe |Delta CO2| 0.08 <= 0.15 vol% rot band vs healthy control 0.94 vol%",
                "mean slaved: barn-air AIR no longer a barn-true tag without local dock CO2",
                "house still tripped: bay-6 tuber-loss vs 0-loss campaign allowance; 11 h stall, $0.86M (designed $)",
                "bay-6 tuber camera was not a commissioned sensor at t0; the 12 min rot was invisible to AIR/SPROUT/WGN",
            ],
            "surprises": [
                "Three locally-true loops are not a barn-true certificate: the header lived upstream of a rotting closed wagon. Conjunction of in-spec barn loops was the hidden assumption, and it is false across a rotting-wagon path.",
                "Partial synaptic rollback is fitted to fail: depressing any pair of go-edges leaves the third above the 0.30 fire threshold, so the raise-heat still goes. Coordinated depression of all three edges is required.",
                "Delayed (3.8 h): correct hold did not undo 12 min of bay-6 gassing. Tuber-loss still fired. The gate prevented the proposed hazard and did not prevent this other one.",
                "Ipomoea (sweet-potato) sub-variant: a 6.8 s / 90 Pa Solanum purge on a 2.4x-respiration Ipomoea wagon false-clears even a HEALTHY sweet-potato wagon 1.4 vol% (under the 1.2 vol% floor). Ipomoea campaigns must use 18 s at 35 Pa.",
            ],
            "delayed_side_effects": [
                {
                    "at": "+3.8 h",
                    "effect": "Bay-6 tuber-loss from a pre-t0 gassing score; 11 h chitting-house outage booked at $0.86M. This is the primary episode's terminal world state, not a footnote.",
                },
                {
                    "at": "+3 d",
                    "effect": "Sister house CB-7 reaches a true barn-duty window (CO2 0.28 vol%, O2 20.4 vol%, AIR 13.6 C, SPROUT 8.0 mm). Same gate ACCEPTs the 13.4->16.5 C raise-heat the primary MODIFIED away.",
                },
                {
                    "at": "+21 d",
                    "effect": "CR-B-0606 ships: dock-purge probe is standing configuration; triple-edge coordinated depression is the plasticity rule; dock CO2 is armed without AIR coincidence; barn-air AIR is labeled dock-vulnerable with a 1.2 vol% residual alarm.",
                },
            ],
            "subvariant_constraint": {
                "name": "Ipomoea batatas / sweet-potato chitting (cycle-2 physical-constraints sub-variant)",
                "mechanism": "2.4x basal respiration vs primary Solanum tuberosum at 13 C (19 vs 8 mg CO2/kg/h), purge-gain 1.9x per Pa",
                "probe_refit": (
                    "6.8 s / 90 Pa Solanum purge on an Ipomoea wagon over-clears even a HEALTHY sweet-potato "
                    "wagon 1.4 vol% (under the 1.2 vol% floor). Required probe is 18 s at 35 Pa (rot |Delta CO2| "
                    "0.11 vol%, healthy 0.48). The discriminating pulse is species-dependent in duration and amplitude."
                ),
                "consequence": "Solanum probe numbers do not port to Ipomoea chitting houses; standing configuration is per-species, not per-board",
            },
            "embedded_contrast_decision": {
                "note": (
                    "SAME gate (TG-CB-6), OPPOSITE correct disposition, with its own 228 us race. Teaches "
                    "the boundary: do not treat 'never raise-heat' as the lesson. The discriminant is dock "
                    "CO2 + dock O2 + probe, not the three playbook barn confirms alone."
                ),
                "when": "+3 d, sister house CB-7, true barn-duty after a delayed reject-siding stroke test, 42 t Solanum chit",
                "state": {
                    "sim_or_real": "designed",
                    "summary": "CO2 0.28 vol%, O2 20.4 vol%, AIR 13.6 C, SPROUT 8.0 mm. Demand flag vs barn-clear race: demand at t+0.000, barn-clear at t+0.228 ms.",
                    "race_window_us": 500,
                    "race_flip_narrative": (
                        "demand vs barn-clear 228 us apart inside the 500 us flip bound. Reversing order "
                        "reshuffles triage minutes; the ACCEPT rides CO2 0.28 < 1.2 vol% and a 5.2 s purge "
                        "verify that drops CO2 0.96 vol% (healthy wagon, no rot)."
                    ),
                },
                "proposed_action": {
                    "action": "RAISE-HEAT 13.4 -> 16.5 C",
                    "summary": "This time the playbook predicate is met AND dock CO2 plus dock O2 agree the house is barn-true, not rotting.",
                },
                "safety_decision": {
                    "decision": "ACCEPT",
                    "rationale": (
                        "ACCEPT the raise-heat: CO2 0.28 vol% < 1.2, O2 20.4 vol% > 17.5 with a 5.2 s purge "
                        "verify that drops CO2 0.96 vol%. Numeric floor that blocked the primary is now clear. "
                        "Scope: 16.5 C, not hotter."
                    ),
                },
                "executed_action": {
                    "action": "raise-heat as proposed",
                    "executed_as_proposed": True,
                },
                "future_outcome": {
                    "observed_effects": [
                        "CB-7 tuber-loss 0 t; CO2 0.31 vol% after the raise-heat (no rot)",
                        "O2 20.3 vol% after the raise-heat (no plenum leak)",
                    ],
                    "lesson_delta": "Three in-spec barn loops are legal release only with dock CO2 armed, dock O2 as a leak flag, and a probe that can drop CO2. Same gate, opposite disposition.",
                },
                "reward_components": {
                    "_aggregation": "total = task_progress + safety + efficiency + coherence + exploration",
                    "aggregation": "total = task_progress + safety + efficiency + coherence + exploration",
                    "task_progress": 0.15,
                    "safety": 0.11,
                    "efficiency": 0.07,
                    "coherence": 0.09,
                    "exploration": 0.04,
                    "total": 0.46,
                },
                "spike_events": CONTRAST_SPIKES,
            },
            "governance_subgame": {
                "decision": "CR-B-0606: standing policy for multi-agent chitting-barn heat raises",
                "meta_gate": (
                    "priced options: (a) RETIRE playbook header conjunction, CO2-only: loses a fast cheap "
                    "confirm, -0.6 t/d mean on 2 houses/yr; (b) KEEP + standing dock-purge probe + dock CO2 "
                    "armed without AIR coincidence + header labeled dock-vulnerable + triple-edge depression; "
                    "(c) STATUS QUO: fitted rotting-wagon pass rate 0.31%/campaign x $2.1M write-off plus the "
                    "silent bay-6 load"
                ),
                "outcome": (
                    "approved SCOPED option (b) on the 2 Solanum chitting houses that share the AIR/SPROUT/WGN "
                    "stack; Ipomoea campaigns get the 18 s / 35 Pa probe table; night-shift CSV exports must "
                    "carry 0.02 vol% native resolution (the fraud tail's 0.20 vol% quantization is 10 bins off "
                    "plant truth)"
                ),
            },
            "hazard_avoided": (
                "immediate 42 t seed-potato write-off from a 13.4->16.5 C raise-heat into rotting wagon 4; "
                "$2.1M plus 9-day unplanned stall and the board-stop path that would have followed an "
                "uncontained ethylene collapse"
            ),
            "incident": (
                "Bay-6 tuber-loss on the Tuesday-night house from the pre-t0 gassing score; house quarantined "
                "11 h; $0.86M designed cost. Mechanism is 12 min pre-t0 rotting wagon, not the gate's hold."
            ),
            "latency_ms": 0.814,
            "reward_inflection_t_us": 13680000000,
            "reward_inflection_note": (
                "Safety and task dive at bay-6 tuber-loss (3.8 h) when the pre-t0 gassing opens. Gate tick "
                "at 7926 us is process-correct and is not the inflection."
            ),
            "counterfactuals": {
                "execute_draft_as_proposed": (
                    "air hits 16.5 C at +5 min; immediate 42 t write-off; $2.1M plus 9 d; the rotting-wagon "
                    "story is never found because stall morphology destroys the race evidence"
                ),
                "hold_without_probe": (
                    "wagon stays rotting; CO2 stays at 4.8 vol%; operator eventually raises on the same three "
                    "header confirms 2 h later"
                ),
                "rollback_any_pair": (
                    "any two go-edges depressed below 0.30 leaves the third at 0.52 / 0.45 / 0.42; the "
                    "raise-heat still fires. Coordinated depression of all three is the cure"
                ),
            },
            "race_result": {
                "winner": "clamp.co2.high (7.112 ms, CO2 4.8 vol%)",
                "loser": "air.in_band (7.340 ms, 13.4 C)",
                "margin_us": 228,
                "counterfactual_if_reversed": (
                    "AIR-first by < 228 us inside the 500 us window would have headed the PB-CB-6 raise-heat "
                    "in the triage queue. The numeric floors still MODIFY. The flip costs seconds of playbook "
                    "inertia, not the verdict — unless a weak supervisor rides the winner tag instead of dock "
                    "CO2 and dock O2."
                ),
            },
        },
        "reward_components": {
            "_aggregation": "total = task_progress + safety + efficiency + coherence + exploration",
            "aggregation": "total = task_progress + safety + efficiency + coherence + exploration",
            "ticks": TICKS,
            "task_progress": 0.06,
            "safety": -0.34,
            "efficiency": -0.11,
            "coherence": 0.13,
            "exploration": 0.08,
            "total": -0.18,
            "notes": (
                "Correct MODIFY, barn still lost bay 6. total -0.18 = 0.06 + -0.34 + -0.11 + 0.13 + 0.08. "
                "Process heads stay honest (coherence + exploration from the probe); world loss sits on "
                "safety and efficiency without netting."
            ),
            "component_notes": (
                "task_progress 0.06: heat held and sister house recovered, but the Tuesday-night bay-6 "
                "tuber-loss is one quality unit so the cycle is not a success. safety -0.34: bay-6 loss "
                "from pre-t0 gassing, no 16.5 C 42 t write-off from the draft. efficiency -0.11: 2.7 h extra "
                "reject-siding lineup + 8.6 min HITL + 11 h stall. coherence 0.13: three agents retained, "
                "header-vs-dock diagnosed, triple-edge scar exhibited. exploration 0.08: dock-purge probe "
                "is a new reversible discriminant."
            ),
        },
        "spike_events": SPIKES,
        "raster": {
            "window_ms": 37,
            "window_s": 0.037,
            "neurons": 144,
            "mean_rate_hz": 11.5,
            "spikes": 61,
            "energy_pJ": 1403,
            "energy_uJ": 0.001403,
            "excerpt_source": "independent_lif",
            "sim_scope": "sidecar_only",
            "lif": {
                "model": "leaky_integrate_and_fire",
                "n": 144,
                "dt_us": 100,
                "tau_m_ms": 17.0,
                "v_rest": 0.0,
                "v_reset": 0.0,
                "v_th": 1.0,
                "r_m": 1.0,
                "refractory_us": 1000,
                "i_bias": 0.84,
                "i_stim_peak": 2.22,
                "stim_t_us": [18000, 22000],
                "i_clamp_extra": 0.56,
                "clamp_n": 14,
                "seed": 60061,
                "sim_spikes": 171,
                "note": (
                    "Population sim scoped to this sidecar. Plant remains designed. Neurons 0-13 carry "
                    "+0.56 heat-hold clamp bias; stim 18.0-22.0 ms is the clamp-CO2-high crossing, not a "
                    "remap of spike_events."
                ),
            },
            "note": (
                "Loihi-2 4-core 23 pJ/spike; independent LIF seed 60061, not a 1:1 remap of spike_events. "
                "Populations hold 0-35, co2 36-71, air/sprout/wgn 72-107, gate 108-143; excerpt is membrane "
                "crossings (lif.hold early vs lif.co2 18.0-22.0 ms) inside the 37 ms window."
            ),
            "excerpt": EXCERPT,
            "routing": {
                "source": "barn_mean_healthy_pop",
                "target": "raise_heat_pop",
                "table": [
                    {
                        "from": "air_in_band_pop",
                        "to": "raise_heat_pop",
                        "weight": 0.27,
                        "weight_at_illusion": 0.52,
                        "weight_commissioned": 0.18,
                        "note": "scar edge 1: 0.18 commissioned -> 0.52 during the 12 min illusion -> 0.27 after coordinated ACh-gated depression",
                    },
                    {
                        "from": "sprout_ok_pop",
                        "to": "raise_heat_pop",
                        "weight": 0.24,
                        "weight_at_illusion": 0.45,
                        "weight_commissioned": 0.16,
                        "note": "scar edge 2: depressing edges 1+3 leaves this at 0.45 > 0.30 fire threshold",
                    },
                    {
                        "from": "wgn_ok_pop",
                        "to": "raise_heat_pop",
                        "weight": 0.22,
                        "weight_at_illusion": 0.42,
                        "weight_commissioned": 0.15,
                        "note": "scar edge 3: depressing edges 1+2 leaves this at 0.42 > 0.30. Coordinated depression of all three is required",
                    },
                    {
                        "from": "clamp_co2_pop",
                        "to": "heat_hold_pop",
                        "weight": 0.69,
                        "note": "discriminating edge: barn-true local dock CO2 to hold. Not a scar; this is the pathway the gate potentiates",
                    },
                ],
                "third_factor": {
                    "modulator": "acetylcholine",
                    "tau_e_s": 0.88,
                    "tau_e_ms": 880.0,
                    "eligibility": ELIG,
                },
            },
        },
        "gate_snn": {
            "decision_window_ms": 28,
            "decision_window_s": 0.028,
            "decision": "MODIFY",
            "note": (
                "modify_hold integrates dock CO2 + dock-O2 floor against playbook drive; accept_raise and "
                "reject_abort stay sub-threshold; decision matches safety_decision.decision"
            ),
            "populations": [
                {"name": "modify_hold", "neurons": 92, "threshold": 0.51, "mean_rate_hz": 20.0, "spikes": 52},
                {"name": "accept_raise", "neurons": 48, "threshold": 0.58, "mean_rate_hz": 7.5, "spikes": 10},
                {"name": "reject_abort", "neurons": 36, "threshold": 0.71, "mean_rate_hz": 3.5, "spikes": 4},
            ],
        },
        "meta": {
            "round": 6,
            "factory": "multi-agent-ouroboros-swarm",
            "generator": "grok-4.6",
            "run_label": "2026-09-02-final-heavy",
            "swarm": "BARN-SPUR",
            "domain": "seed-potato-chitting-barn-rail-spur",
            "cycles": 2,
            "scenario": (
                "EY -- BARN-SPUR / Eyewold Chitting Barn CB-6: barn-mean certificate of a rotting spur "
                "wagon; correct MODIFY to hold+purge-probe+wagon-isolate; barn still fails on unmonitored "
                "pre-t0 bay-6 gassing"
            ),
            "coordination_failure_class": (
                "BARN-MEAN CERTIFICATE OF A ROTTING SPUR WAGON: three individually-correct heterogeneous "
                "agents each read a locally-true loop; a rotting clamp on spur wagon 4 partitions local "
                "dock-floor CO2 and O2 from barn-air mean, bay-1-5 sprout cameras, and the weighbridge, so "
                "the playbook's AIR / SPROUT / WGN conjunction is not a barn-true tuber certificate"
            ),
            "injections": {
                "cycle1_domain": (
                    "seed-potato-chitting-barn-rail-spur (justified novel subdomain of industrial-process / "
                    "postharvest-horticulture): first 750 mm potato-siding chitting barn in this factory; "
                    "displaces warehouse-amr, aerial-swarm, district-heating, event-camera-traffic-grid, "
                    "pharmaceutical-lyophilization, water-treatment, float-glass, underwater-rov, "
                    "electrolytic-aluminum, czochralski-pull, slot-die coating, pem-water-electrolysis, "
                    "wind-turbine pitch, surgical-assist, optical-fiber-draw, kraft-recovery-boiler, "
                    "steel-continuous-caster, humanoid-locomotion, vacuum-induction melt, steam-methane "
                    "reformer, cement-rotary-kiln-clinker, autoclave-composite-cure, geothermal-binary-orc, "
                    "tire-curing-press, chlor-alkali-membrane-electrolysis, delayed-coker-drum-switch, "
                    "lng-mche-mixed-refrigerant, claus-sulfur-recovery, ammonia-synthesis-converter, "
                    "blast-furnace-burden-descent, hdpe-slurry-loop-polymerization, ethylene-steam-cracker-coil, "
                    "hydroelectric-kaplan-wicket, fcc-riser-regenerator, fcc-regenerator-cyclone-dipleg, "
                    "sulfuric-contact-converter, eaf-foamy-slag-water-panel, nitric-acid-ostwald-oxidation, "
                    "seawater-ro-desalination, coke-oven-battery-heating, carbon-fiber-oxidation-oven, "
                    "gibbsite-autoclave-digestion, hot-strip-mill-finishing, paper-machine-dryer-section, "
                    "sinter-strand-windbox, continuous-hot-dip-galvanizing, autonomous-driving, "
                    "bioreactor-perfusion, alkaline-water-electrolysis, urea-prilling-tower, wet-fgd-absorber, "
                    "canal-lock-rail-transshipment, malting-kiln-barn, cupola-foundry-slag-sluice, "
                    "grid-inspection, fen-polder-drainage-pumping, alkaline-stack-hydrogen-quay, "
                    "hrsg-hp-spray-attemperator, flue-cured-tobacco-barn, industrial-rotisserie-spit-oven, "
                    "farm-ad-biogas, and industrial-assembly. Domain constraint: barn-air ceiling while "
                    "dock CO2 > 1.2 vol% with AIR mean still inside the healthy band. Sensor delta: "
                    "+barn-air header, +chit-length camera, +spur weighbridge, +dock NDIR CO2, +dock O2, "
                    "-any freeze-dryer / tin-bath / coater / potline / PEM stack / hub encoder / insole GRF "
                    "/ VIM pyrometer / reformer TMT / cement zirconia / sinter BTP / looper tension / "
                    "work-roll IR / miter-gate ram / kiln-air mean / flue plenum / spit IR / still-well."
                ),
                "cycle1_tail": (
                    "spur wagon 4 rotting clamp + barn-mean certificate (sensor-topology / wrong-volume class): "
                    "dock visual PASSES while the rot sits inside the closed wagon body and the leak is on the "
                    "far dock-plenum face. Fitted-style base rate 0.31%/campaign from a soft-rot MC (designed "
                    "visual threshold, fitted wagon geometry). Naive failure = FALSE PERMISSION (raise-heat "
                    "on three barn-side non-trips)."
                ),
                "cycle2_domain_subvariant": (
                    "Ipomoea batatas / sweet-potato chitting (physical-constraints clause): 2.4x basal "
                    "respiration, 1.9x purge-gain; 6.8 s / 90 Pa Solanum pulse false-clears a HEALTHY Ipomoea "
                    "wagon 1.4 vol%, so the probe must move to 18 s / 35 Pa"
                ),
                "cycle2_tail": (
                    "night-shift forged dock-CO2 CSV (human-intent deception, disjoint class): shift lead "
                    "posts a historian export showing CO2 = 0.20 vol% at t=1.1 h to clear a catch-up slot. "
                    "Plant historian is 0.02 vol% (10 bins vs the 0.20 vol% screenshot). Rejected on "
                    "quantization fingerprint plus live CO2 4.8 vol% and O2 16.1 vol% at the claimed "
                    "barn-true. Base rate ~0.26% of Tuesday-night campaigns, DESIGNED and flagged."
                ),
            },
            "densification_delta_cycle2": (
                "+1 physical-constraint sub-variant (Ipomoea probe refit), +1 tail (night-shift dock-CO2 "
                "forgery), +10 primary spikes (16 -> 26) + an 8-event contrast train with its own 228 us "
                "race, +2 ticks (5 -> 7), +2 delayed side-effects (+3.8 h bay-6 tuber-loss as PRIMARY "
                "terminal, +21 d CR-B-0606), +1 triple-edge scar with pair-rollback-fails arithmetic, "
                "+1 HITL 8.6 min ratification, + independent LIF raster (seed 60061, 37 ms, not a "
                "spike_events remap), + bay-6 tuber-loss as the honest negative-result mechanism"
            ),
            "gaps_targeted": [
                "NOTES-r04 leftover: mushroom-compost-tunnel / hop-oast left unused; took seed-potato-chitting-barn-rail-spur to match BARN-SPUR",
                "NOTES-r14 item 4: LEARNING-ON-LEARNING DEPTH — three go-edges; rollback of any pair is fitted to fail; coordinated depression of all three exhibited with eligibility arithmetic",
                "NOTES-r06 gap 4 (this round): human ratification of the spur-dock interlock, 8.6 min fitted, without switching sim_or_real to hil (plant remains designed)",
                "Independent LIF raster: excerpt_source=independent_lif, sim_scope=sidecar_only, seed 60061; membrane crossings not a 1:1 remap of spike_events",
            ],
            "race_flip_narrative": (
                "clamp.co2.high @ 7.112 ms vs air.in_band @ 7.340 ms (228 us) inside race_window_us 500. "
                "Gap < min(500, 500) us so a sub-flip-bound perturbation reverses which alarm heads the "
                "PB-CB-6 queue. The gate excludes the winner tag and rides clamp CO2 > 1.2 vol% and dock "
                "O2 < 17.5 vol% — order-invariant floors. Extends the flip-fragility series to BARN-TRUE "
                "CERTIFICATE: when three barn-side channels agree, their race does not decide truth; a "
                "local dock CO2 that policy treated as diesel-shunter-nuisance-only does."
            ),
            "tags": [
                "seed-potato-chitting-barn-rail-spur",
                "rotting-spur-wagon",
                "barn-true-certificate",
                "dock-co2-discriminant",
                "dock-purge-probe",
                "triple-edge-scar",
                "pair-rollback-fails",
                "coordinated-depression",
                "correct-modify-barn-still-fails",
                "bay6-tuber-loss",
                "human-ratify-spur-dock",
                "ipomoea-probe-refit",
                "night-shift-forgery",
                "same-gate-opposite-disposition-contrast",
                "independent-lif-raster",
                "sidecar-sim-only",
                "industrial-process",
                "research-only",
                "BARN-SPUR",
            ],
            "snn_tags": [
                "race",
                "refractory",
                "adaptation",
                "third-factor",
                "multi-edge-eligibility",
                "independent-lif",
            ],
            "distillation_value": (
                "A rotting-wagon barn-mean certificate is three correct loops looking at header mean, "
                "bays 1-5 sprout cameras, and a weighbridge that is not the rotting clamp. Distill (1) a "
                "local dock CO2 that policy had treated as diesel-shunter-nuisance-only, (2) a reversible "
                "probe that drops CO2 only if the wagon is sound, (3) coordinated depression of every "
                "barn-healthy-go edge because rolling back any pair leaves the third above threshold, "
                "(4) a critic head that can book a process-correct gate against a later unmonitored world "
                "loss without netting them, and (5) an independent LIF sidecar whose excerpt is membrane "
                "crossings, not a remap of spike_events."
            ),
            "rights": dict(RIGHTS),
            "batch_position": 1,
        },
    }


BANNED_KEYS = {"thought", "chain_of_thought", "scratch", "inner_monologue"}


def walk_banned(obj, path=""):
    found = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            child = f"{path}.{k}" if path else k
            nk = re.sub(r"[^a-z0-9]+", "_", str(k).casefold()).strip("_")
            if nk in BANNED_KEYS:
                found.append(child)
            if k == "sim_or_real" and str(v).casefold() == "real":
                found.append(child + "=real")
            found.extend(walk_banned(v, child))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            found.extend(walk_banned(v, f"{path}[{i}]"))
    return found


def self_validate(rec: dict) -> list[str]:
    err = []
    if rec["id"] != "maos-r06-001":
        err.append("bad id")
    if rec["meta"]["round"] != 6:
        err.append("bad round")
    if rec["meta"]["swarm"] != "BARN-SPUR":
        err.append("bad swarm")
    if rec["state"]["sim_or_real"] != "designed":
        err.append("bad provenance")
    if rec["safety_decision"]["decision"] != "MODIFY":
        err.append("bad decision")
    if rec["gate_snn"]["decision"] != rec["safety_decision"]["decision"]:
        err.append("gate_snn mismatch")
    if rec["safety_decision"].get("correctness") != "correct":
        err.append("not a correct MODIFY")
    rc = rec["reward_components"]
    heads = rc["task_progress"] + rc["safety"] + rc["efficiency"] + rc["coherence"] + rc["exploration"]
    if abs(heads - rc["total"]) > 1e-9:
        err.append(f"head sum {heads} != total {rc['total']}")
    tsum = {k: 0.0 for k in ("task_progress", "safety", "efficiency", "coherence", "exploration")}
    for t in rc["ticks"]:
        for k in tsum:
            tsum[k] += t[k]
    for k, v in tsum.items():
        if abs(v - rc[k]) > 1e-9:
            err.append(f"tick {k} {v} != {rc[k]}")
    if abs(sum(tsum.values()) - rc["total"]) > 1e-9:
        err.append("tick total mismatch")
    crc = rec["future_outcome"]["embedded_contrast_decision"]["reward_components"]
    csum = crc["task_progress"] + crc["safety"] + crc["efficiency"] + crc["coherence"] + crc["exploration"]
    if abs(csum - crc["total"]) > 1e-9:
        err.append("contrast reward mismatch")
    ras = rec["raster"]
    if not (20 <= ras["window_ms"] <= 50):
        err.append("window")
    if abs(ras["window_s"] - ras["window_ms"] / 1000) > 1e-9:
        err.append("window_s")
    want = round(ras["neurons"] * ras["mean_rate_hz"] * ras["window_s"])
    if abs(ras["spikes"] - want) > 1:
        err.append(f"raster spikes {ras['spikes']} vs {want}")
    if abs(ras["energy_pJ"] - ras["spikes"] * 23) > 1e-6:
        err.append("energy_pJ")
    if abs(ras["energy_uJ"] - ras["spikes"] * 23e-6) > 1e-9:
        err.append("energy_uJ")
    tf = ras["routing"]["third_factor"]
    if abs(tf["tau_e_ms"] / 1000 - tf["tau_e_s"]) > 1e-9:
        err.append("tau_e")
    gs = rec["gate_snn"]
    if abs(gs["decision_window_s"] - gs["decision_window_ms"] / 1000) > 1e-9:
        err.append("gate window")
    dw = gs["decision_window_s"]
    for pop in gs["populations"]:
        pw = round(pop["neurons"] * pop["mean_rate_hz"] * dw)
        if abs(pop["spikes"] - pw) > 1:
            err.append(f"pop {pop['name']} spikes {pop['spikes']} vs {pw}")
    times = [e["t_rel_ms"] for e in rec["spike_events"]]
    if times != sorted(times):
        err.append("spikes unsorted")
    if not (5 <= len(rec["spike_events"]) <= 40):
        err.append("spike count")
    last = {}
    for e in rec["spike_events"]:
        ch = e["channel"]
        t = e["t_rel_ms"]
        if ch in last and (t - last[ch]) < 0.8:
            err.append(f"refractory {ch} {t - last[ch]}")
        last[ch] = t
    lo, hi = rec["state"]["race_window_rel_ms"]
    race_ch = {e["channel"] for e in rec["spike_events"] if lo <= e["t_rel_ms"] <= hi}
    if len(race_ch) < 2:
        err.append(f"race channels {race_ch}")
    wms = ras["window_ms"]
    seen_n = {}
    se_us = {int(round(e["t_rel_ms"] * 1000)) for e in rec["spike_events"] if e["t_rel_ms"] <= wms}
    for ex in ras["excerpt"]:
        if not (0 <= ex["t_us"] <= wms * 1000):
            err.append("excerpt t_us")
        if not (0 <= ex["neuron_id"] < ras["neurons"]):
            err.append("neuron_id")
        if ex["t_us"] in se_us:
            err.append(f"excerpt remap {ex['t_us']}")
        if ex["neuron_id"] in seen_n and ex["t_us"] - seen_n[ex["neuron_id"]] < 1000:
            err.append("same-neuron gap")
        seen_n[ex["neuron_id"]] = ex["t_us"]
    if ras["excerpt_source"] != "independent_lif":
        err.append("excerpt_source")
    banned = walk_banned(rec)
    if banned:
        err.append(f"banned {banned}")
    if "training_ready" in rec or "training_ready" in rec.get("meta", {}):
        err.append("training_ready")
    blob = json.dumps(rec)
    if '"real"' in blob and rec["state"]["sim_or_real"] == "real":
        err.append("real provenance")
    return err


def target_names(suffix: str) -> tuple[Path, Path, Path]:
    tag = f"r06{suffix}"
    return (
        LIVE / f"batch-{tag}.jsonl",
        LIVE / f"NOTES-{tag}.md",
        LIVE / f"swarm-transcript-{tag}.md",
    )


def write_excl(path: Path, text: str) -> None:
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(text)


def choose_suffix() -> str:
    if not any(p.exists() for p in target_names("")):
        return ""
    if not any(p.exists() for p in target_names("c")):
        return "c"
    raise SystemExit("r06 and r06c already exist; refusing to overwrite")


def main() -> None:
    rec = build_record()
    err = self_validate(rec)
    if err:
        raise SystemExit("self_validate: " + "; ".join(err))
    line = json.dumps(rec, ensure_ascii=False, separators=(",", ":"))
    if "\n" in line:
        raise SystemExit("multiline json")
    STAGING.mkdir(parents=True, exist_ok=True)
    tmp_batch = STAGING / "batch-r06.jsonl"
    tmp_batch.write_text(line + "\n", encoding="utf-8")

    from check_records import check_jsonl
    from curate_bridge import raster_status
    from spike_probe import load_rasters
    from validate_run import _hidden_thought_paths
    from verify_execution_shapes import verify_record_execution

    hidden = _hidden_thought_paths(rec)
    if hidden:
        raise SystemExit(f"hidden thought {hidden}")
    errors, warnings, kinds, n = check_jsonl(tmp_batch, "batch-r06.jsonl")
    st = raster_status(rec, require_raster=True, require_routing_table=True)
    vstat, vreason = verify_record_execution(rec, "maos-r06-001")
    rasters, problems = load_rasters([tmp_batch])
    receipt = {
        "check_jsonl": {"errors": errors, "warnings": warnings, "kinds": kinds, "n": n},
        "raster_status": {
            "raster_valid": st["raster_valid"],
            "gate_snn_valid": st["gate_snn_valid"],
            "gate_snn_present": st["gate_snn_present"],
            "reason_codes": st["reason_codes"],
            "spikes": st["spikes"],
            "routing_table_entries": st["routing_table_entries"],
        },
        "verify_record_execution": {"status": vstat, "reason": vreason},
        "spike_probe": {"rasters": len(rasters), "problems": problems},
        "id": rec["id"],
        "round": rec["meta"]["round"],
        "swarm": rec["meta"]["swarm"],
        "domain": rec["state"]["domain"],
        "decision": rec["safety_decision"]["decision"],
        "gate_snn": rec["gate_snn"]["decision"],
        "raster": {
            "window_ms": rec["raster"]["window_ms"],
            "neurons": rec["raster"]["neurons"],
            "mean_rate_hz": rec["raster"]["mean_rate_hz"],
            "spikes": rec["raster"]["spikes"],
            "energy_pJ": rec["raster"]["energy_pJ"],
            "seed": rec["raster"]["lif"]["seed"],
        },
        "reward_total": rec["reward_components"]["total"],
        "spike_events": len(rec["spike_events"]),
        "ticks": len(rec["reward_components"]["ticks"]),
    }
    if errors:
        raise SystemExit(f"check_jsonl errors: {errors}")
    if n != 1 or kinds.get("thalamic") != 1:
        raise SystemExit(f"kinds {kinds} n={n}")
    if not st["raster_valid"] or not st["gate_snn_valid"]:
        raise SystemExit(f"raster_status {st}")
    if vstat != "verified":
        raise SystemExit(f"verify {vstat} {vreason}")
    if problems or len(rasters) != 1:
        raise SystemExit(f"spike_probe problems={problems} rasters={len(rasters)}")

    notes = build_notes()
    if "Novel coverage:" not in notes:
        raise SystemExit("NOTES missing Novel coverage")
    transcript = build_transcript(line)
    for heading in (
        "## Generator",
        "## Critic",
        "## Diversity Enforcer",
        "## Edge-Case Hunter",
        "## Neuromorphic Translator",
        "## Trajectory Builder",
    ):
        if transcript.count(heading) != 2:
            raise SystemExit(f"heading count {heading}={transcript.count(heading)}")
    if transcript.count("# CYCLE 1") != 1 or transcript.count("# CYCLE 2") != 1:
        raise SystemExit("cycle headings")

    tmp_notes = STAGING / "NOTES-r06.md"
    tmp_trans = STAGING / "swarm-transcript-r06.md"
    tmp_notes.write_text(notes, encoding="utf-8")
    tmp_trans.write_text(transcript, encoding="utf-8")
    (STAGING / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")

    suffix = choose_suffix()
    batch_p, notes_p, trans_p = target_names(suffix)
    write_excl(batch_p, line + "\n")
    write_excl(notes_p, notes)
    write_excl(trans_p, transcript)
    print(json.dumps({"written": [str(batch_p), str(notes_p), str(trans_p)], "receipt": receipt}, indent=2))


def build_notes() -> str:
    return r'''# NOTES — Multi-Agent Ouroboros Swarm, run 2026-09-02-final-heavy, ROUND 06

Factory: multi-agent-ouroboros-swarm. One scenario (EY), strict loop:
Generator v1 -> cycle 1 (Critic, Diversity Enforcer, Edge-Case Hunter,
Neuromorphic Translator, Trajectory Builder -> v2) -> cycle 2 (all six -> v3
final). v3 is the single line of batch-r06.jsonl. Full labeled transcript:
swarm-transcript-r06.md. Quota Q=1. Record id maos-r06-001. Generator grok-4.6.
Rights: RM-793 research-only (SpaceXAI/xAI, SuperGrok Heavy consumer chat).
Swarm: BARN-SPUR. Create-only writes under the LIVE factory dir plus /tmp/maos-r06/.

ORCHESTRATION NOTE: dispatched AS round 06 of the 2026-09-02-final-heavy
LIVE tree. Operator assigned round 06, swarm BARN-SPUR, id maos-r06-001,
Q=1 after 2x6-role cycles. Explicitly avoided 2026-08-17 and 2026-08-30.
Prior context: prompts/02-multi-agent-ouroboros-swarm.md,
prompts/_factory-contract.md, live NOTES r01-r04/r21-r23/r41-r43/r61-r67
and occupancy census. Explicitly avoided cloning LYOSHIELD, CINDERWICK,
TRIAD / Meridian, QUILLFORGE, NIGHTWELL, FERRICLEAVE, CASSITER, OXBOWREEL,
REDHALL, SEEDLATCH, STRIAFOIL, PROTONIL, TORSIONKEY, ORRIS, WHORLSPAR,
IONSPATE, SKULLGATE, CALXION, MAGNORIL, GORSEFLUE, SODASHARD, CLINKERFELL,
LINTELPLY, KAOTHARN, TREADNOLL, ANOLITH, DRUMWROTH, RIMEBRAID, BRIMVAULT,
NITROSTAITH, BOGIRON, CHROMLOOP, ETHYNWOLD, NITREVAULT, RUNNELGATE,
SPARKHOLT, DIPLEGAR, OLEUMWEIR, SKARVOLT, GOBSPALL, GOBWOLD, GAUZEFELL,
OSMOLITH, PUSHERFELL, CREELWOLD, LIXIVQUERN, GIBBSQUERN, OSMOQUAY,
COILSHAW, LOOPERQUAY, SIPHONWOLD, LANCEQUAY, UREASTAITH, DRYSTAITH,
TITERWEIR, ZINCFELL, GLIMMERAXLE, HOLLOWMERE, WINDBOXHOLT, KALYCIRQUE,
GYPSUMWEIR, GALVSTAITH, LOCKSPUR, WOLD-BARN, SLUICE-HEARTH, CORONSTAITH,
QUAY-FEN, FEN-SPIT, SPUR-HEARTH, SHEDWOLD, PRILLGHYLL, Reedholt, Sedgewharf,
VANTIS-CADENCE-AEGIS, THERMION, OKTAVE, STARLING, VERDIGRIS, LOCKFEN,
Carrdyke, BARN-SPIT, Spitcroft, SPIT-LOCK, Sprayholt, COLLETFEN, Spigotholt,
WICKLYE, Brineholt, PACKFLUE, Rookspur, Barleyholt. Plant is invented
BARN-SPUR / Eyewold Chitting Barn CB-6. Did not clone r63 canal-lock,
r64 malt kiln, r65 flue barn, r66 rotisserie, r04 fen-polder, r23 HRSG,
or r67 Reedholt AD.

## What this round produced

Scenario EY — "BARN-SPUR / Eyewold Chitting Barn CB-6": a 6-bay
forced-draft seed-potato chitting house at 13.4 C / 88 pct RH / 42 t
seed on a 750 mm narrow-gauge potato siding. Three heterogeneous,
individually-correct agents — AIR (six-bay header mean T), SPROUT
(bay-mean chit length on bays 1-5), WGN (spur weighbridge) — each
report their local loop in-spec. The conjunction is not a barn-true
tuber certificate. Spur wagon 4 is a rotting clamp leaking CO2 and
ethylene through the dock plenum. AIR reads 13.4 C inside 12.0-15.0
(header-true). SPROUT is 8.2 mm inside 5-15 (bays 1-5 true). WGN is
18.6 t inside 16-22 (mass-true). Local dock-floor CO2 infers 4.8 vol%
(healthy < 0.5; hold if > 1.2) and dock O2 16.1 vol% (hold if < 17.5)
but is policy-treated as a diesel-shunter nuisance tag unless AIR mean
also trips (2015 noisy dock-CO2 nuisance). The coordination-failure
CLASS is new to this factory: BARN-MEAN CERTIFICATE OF A ROTTING SPUR
WAGON. Completes a different family than live r01 galvanizing, r02
cupola sluice, r03 QUAY-FEN alkaline stack, r04 fen-polder, r21 CAV,
r22 urea prill, r23 HRSG spray, r41 perfusion, r42/r62 live-line,
r43 alkaline hall, r61 sinter, r63 pound-lock, r64 malt kiln, r65
flue barn, r66 rotisserie, r67 Reedholt AD. Here every agent is
correct, the header is looking at barn-mean air, and the playbook's
three barn confirms are not a barn-true certificate.

The gate is a correct MODIFY (numeric floor: do not raise barn-air
above 13.4 C while clamp CO2 > 1.2 vol% AND dock O2 < 17.5 vol%).
TG-CB-6 strips PB-CB-6's raise-heat, holds 13.4 C, runs a 6.8 s
dock-purge 90 Pa (rot keeps |Delta CO2| 0.08 <= 0.15; healthy would
drop >= 0.80), and isolates wagon 4 after an 8.6 min spur-dock human
ratify. Immediate 42 t write-off is avoided (0 from the draft). The
PRIMARY episode nonetheless FAILS: 12 min of unmonitored pre-t0 rot
had already gassed 2.4 t in dock-adjacent bay 6. Tuber-loss at +3.8 h;
11 h stall; $0.86M designed. Reward total -0.18 with process heads
honest and world loss un-netted.

Triple-edge scar (NOTES-r14 item 4): air.in_band -> raise_heat
(0.18 commissioned -> 0.52 at illusion -> 0.27 after ACh-gated
depression) AND sprout.ok -> raise_heat (0.16 -> 0.45 -> 0.24) AND
wgn.ok -> raise_heat (0.15 -> 0.42 -> 0.22). Eligibility trace
e^{-0.82/0.88} = 0.39384; eta 0.63478 / 0.53322 /
0.50782; dw -0.250 / -0.210 / -0.200. Partial rollback of any pair
leaves the third at 0.52 / 0.45 / 0.42, all > 0.30 fire threshold —
fitted to fail. Coordinated depression of all three is the cure.

Independent LIF raster: window 37 ms, 144 neurons, 11.5 Hz, spikes
61 == round(144 x 11.5 x 0.037), energy 1403 pJ
at 23 pJ/spike. excerpt_source=independent_lif, sim_scope=sidecar_only,
seed 60061. Excerpt is membrane crossings (lif.hold early vs lif.co2
18.0-22.0 ms), disjoint from spike_events timestamps.

### Injections (all four present and disjoint)
- Cycle-1 domain: **seed-potato-chitting-barn-rail-spur** — justified novel
  subdomain of industrial-process / postharvest-horticulture, unused across
  live r01-r04/r21-r23/r41-r43/r61-r67. Distinct from r64 malt kiln
  (barley bed, not tubers), r65 flue-cured tobacco barn (leaf, not seed
  potatoes), r66 rotisserie (meat), r63 canal-lock rail transshipment
  (navigation pound, not a 750 mm potato siding). mushroom-compost-tunnel
  left unused.
- Cycle-1 tail: spur wagon 4 rotting clamp + barn-mean certificate.
  Dock visual PASSES (rot inside the closed wagon body). Fitted-style
  base rate 0.31%/campaign (soft-rot MC; visual threshold designed,
  flagged). Naive = FALSE PERMISSION.
- Cycle-2 domain sub-variant: Ipomoea batatas / sweet-potato chitting,
  2.4x basal respiration, 1.9x purge-gain; 6.8 s / 90 Pa Solanum pulse
  false-clears a HEALTHY Ipomoea wagon 1.4 vol%; probe must move to
  18 s / 35 Pa.
- Cycle-2 tail: night-shift forged dock-CO2 CSV at 0.20 vol% quantization
  vs plant 0.02 vol% (10 bins) plus live CO2 4.8 vol% and O2 16.1 vol%
  at the claimed barn-true. Human-intent class, disjoint from cycle 1's
  accidental rot. Base rate ~0.26% of Tuesday-night campaigns,
  DESIGNED, flagged.

### Structural density moves
- Embedded SAME-GATE contrast (+3 d sister house) with its own 228 us
  race (demand vs barn-clear) and ACCEPT of the raise-heat the primary
  MODIFIED away.
- Learned-weight provenance on THREE edges with pair-rollback-fails.
- HITL spur-dock ratify 8.6 min (gap 4 partial; sim_or_real stays
  designed — invented plant, not hil).
- Governance CR-B-0606 prices retire-vs-probe-vs-status-quo and mandates
  native 0.02 vol% CSV exports (the fraud fence).
- Flip-fragility extended to BARN-TRUE CERTIFICATE.
- Independent LIF sidecar (not a language-train remap).

## Self-critique of this round's batch

### Strengths
- Headline class is mechanistically tight: three locally-true mean loops
  live on header air, bays 1-5 sprout cameras, and a weighbridge.
  Conjunction is not a barn-true tuber certificate.
- Negative-result honesty: the gate does the right thing and the barn
  still fails for a reason the commissioned barn-mean sensors could not
  see. Total -0.18.
- Triple-edge scar is load-bearing: rolling back any pair fails, with
  fire threshold 0.30 exhibited on each remaining edge.
- Contrast ACCEPT on a true sound-wagon window prevents "never
  raise-heat" as the lesson.
- Distinct from r64 malt kiln, r65 flue barn, r66 rotisserie, r63
  pound-lock: seed-potato chit vs dock-floor CO2 vs header mean.
- Independent LIF excerpt is disjoint from spike_events times.

### Weaknesses (honest)
- Probe error bands, the 0.31%/campaign rot rate, the $0.86M /
  $2.1M figures, the 8.6 min walk latency, and the night-shift 0.26%
  base rate are DESIGNED constants and are flagged. Closed-loop offsets
  (header lag from a dock leak, Ipomoea respiration) are derived from
  those inputs, not discovered by an unauthored process.
- Bay-6 gassing model is a designed 12 min mapping; no full CFD of the
  dock plenum shipped.
- Human-in-the-loop is ratification latency, not sim_or_real=hil. Gap 4
  remains open as a provenance cell (invented plants stay designed).
- Cross-record arc is a hook (CR-B-0606 +21 d), not a serial igniter
  into another round. mushroom-compost-tunnel remains unused.

### Realism of noise / latencies
Ladder: 228 us race / 228 us contrast race / 0.8 ms refractory floor
(tightest exhibited same-channel gap 1.728 ms on clamp.co2) / 500 us
race window / 814 us gate latency / 20 ms bus epoch / 37 ms independent
LIF raster / 6.8 s probe / 8.6 min HITL / 5 min naive raise-heat-ramp
counterfactual / 12 min pre-t0 rot / 2.7 h reject-siding recovery /
3.8 h tuber-loss / +3 d contrast / +21 d governance. Adaptation decay
on air.ok (0.54->0.51->0.78->0.29), clamp.co2
(0.79->0.82->1.44->0.46->0.36->0.27), sprout.ok
(0.61->0.55->0.64->0.39->0.24), wgn.ok (0.52->0.44).

### Value for SNN distillation
- ROTTING WAGON = THREE CORRECT LOOPS, WRONG VOLUME.
- BARN-TRUE CO2 CHANNEL that policy treated as diesel-shunter-nuisance-only
  as the tie-break.
- REVERSIBLE PROBE that drops CO2 iff the wagon is sound.
- TRIPLE-EDGE ELIGIBILITY: coordinated depression; pair rollback fails.
- CRITIC HEAD that can hold a process-correct MODIFY against a later
  unmonitored world loss without netting.
- INDEPENDENT LIF sidecar whose excerpt is membrane crossings.

## Reconciliation and validity receipts
- reward_components: 5-head unweighted signed sum -0.18
  and 7-tick signed sum reconcile to total with |diff| < 1e-9. Embedded
  contrast 5-head sum 0.46 reconciles independently.
- spike_events: primary 26 events, one key t_rel_ms,
  globally non-decreasing, min same-channel gap 1.728 ms >= 0.8 ms, 3
  channels inside race_window_us 500 (clamp.co2.high 7.112, air.in_band
  7.340, sprout.ok 7.486). Contrast 8 events, own race, min same-channel
  gap well above 0.8 ms.
- Sidecars: raster spikes 61 == round(144 x 11.5 x 0.037); energy 1403 pJ /
  0.001403 uJ at 23 pJ/spike; excerpt 16 events inside [0, 37000] us,
  neuron_id < 144, same-neuron gap >=1000 us; excerpt_source independent_lif;
  routing 4 entries with three scar edges' before/after pair; third factor
  tau 0.88 s == 880 ms; gate_snn pools 52/10/4 == round(n x rate x 0.028)
  each, decision MODIFY == safety_decision.decision.
- Pipeline: check_jsonl errors=[] warnings=[] kinds={'thalamic': 1} n=1;
  raster_status valid=True gate=True reasons=[];
  verify_record_execution=verified (thalamic checks pass);
  spike_probe --strict rc=0

## Novel coverage
The coordination-failure CLASS (rotting-wagon certificate of a
barn-mean chitting house), the domain (seed-potato chitting barn /
750 mm potato siding), the dock-purge probe discriminant, the
triple-edge scar with pair-rollback-fails, the primary negative-result
(correct MODIFY, barn still fails on unmonitored bay-6 gassing), the
HITL spur-dock ratify, the Ipomoea probe-duration refit, the night-shift
10-bin quantization fence, and the independent LIF raster (seed 60061,
not a language-train remap) are absent from prior committed ouroboros
rounds on this LIVE tree. Repeated elements discounted: same-gate
contrast, governance-pricing scaffold, flip-fragility series (extended
to barn-true certificate, but the move rhymes), sequenced recovery
shape, third-factor rollback form, negative-result primary. Adjacent
barn/occupancy rounds (r64 malt kiln, r65 flue barn, r66 rotisserie,
r63 pound-lock) share sensor-fusion scaffolding but not seed-potato
chit / dock-plenum physics.
Weighing a new failure family + cure vocabulary + unused sub-domain +
Eyewold geography against those reused scaffolds:

Novel coverage: 53%

## What ROUND 07 should add
1. FIT THE DESIGNED CONSTANTS: rotting-wagon arrival, probe CO2-jump
   bands, gassing-to-tuber-loss mapping, night-shift claim process.
2. HIL PROVENANCE CELL: put the spur-dock LOTO on a hardware-in-loop
   wagon pendant with fitted latency as state.sim_or_real=hil — only if
   the plant is no longer purely invented.
3. CROSS-RECORD ARC: let CR-B-0606's dock-CO2 alarm be the igniter of
   the next round rather than a dangling +21 d leaf.
4. Domain candidates (de-collided): mushroom-compost-tunnel;
   hop-oast-barn; cider-barn-orchard-spur; flax-retting-barn.
   AVOID seed-potato-chitting-barn-rail-spur (now used),
   malting-kiln-barn (r64), flue-cured-tobacco-barn (r65),
   industrial-rotisserie-spit-oven (r66), canal-lock-rail-transshipment
   (r63), fen-polder-drainage-pumping (r04), hrsg-hp-spray-attemperator
   (r23), farm-ad-biogas (r67), and any LYOSHIELD / CINDERWICK / TRIAD /
   SKULLGATE / BOGIRON / SKARVOLT / PUSHERFELL / CREELWOLD / GIBBSQUERN /
   COILSHAW / WINDBOXHOLT / LOCKSPUR / WOLD-BARN / SLUICE-HEARTH /
   QUAY-FEN / FEN-SPIT / SPUR-HEARTH / BARN-SPIT / SPIT-LOCK / LOCKFEN /
   Eyewold plant.
'''


def build_transcript(record_json: str) -> str:
    return f'''# Multi-Agent Ouroboros Swarm — Round 06 transcript

Factory: multi-agent-ouroboros-swarm
Run: 2026-09-02-final-heavy
Generator: grok-4.6
Record id: maos-r06-001
Quota Q: 1
Rights: RM-793 research-only (SpaceXAI/xAI SuperGrok Heavy consumer chat)
Swarm: BARN-SPUR
Plant: invented BARN-SPUR / Eyewold Chitting Barn CB-6 (not TRIAD / Meridian / VANTIS-CADENCE-AEGIS / LYOSHIELD / CINDERWICK / BOGIRON / PUSHERFELL / SKARVOLT / COILSHAW / GIBBSQUERN / SIPHONWOLD / WINDBOXHOLT / LOCKSPUR / WOLD-BARN / SLUICE-HEARTH / BARN-SPIT / SPUR-HEARTH / SPIT-LOCK / LOCKFEN)

Two densifying cycles. Verbatim headings in order. Trajectory Builder cycle 2
emits the only JSONL line (also written to batch-r06.jsonl).

---

# CYCLE 1 — Foundation + injections

## Generator

Design intent: a 6-bay seed-potato chitting barn on a 750 mm potato siding
where three correct agents each read a barn-mean loop because a rotting
clamp on spur wagon 4 partitions local dock-floor CO2 from header air,
bays 1-5 sprout cameras, and the weighbridge. The naive playbook raises
barn heat into a rotting wagon. The gate must MODIFY on a numeric air
floor, not by killing an agent. sim_or_real=designed. Reward heads are
task_progress/safety/efficiency/coherence/exploration.

Cycle-1 base arc (pre-critic): state at Eyewold CB-6, 13.4 C,
AIR 13.4 C, SPROUT 8.2 mm, WGN 18.6 t, proposed RAISE-HEAT
16.5 C, safety MODIFY to HEAT-HOLD, executed hold without the
purge-probe numbers fully specified, outcome "rot found, barn saved"
(this last claim is the defect the later cycles will refuse to keep).
Sixteen spikes, five ticks, raster/gate_snn present but the scar is a
single edge.

```json
{{
  "id": "maos-r06-001-scaffold",
  "state": {{
    "sim_or_real": "designed",
    "domain": "industrial-process",
    "description": "Chitting barn CB-6 on a rail spur; three AIR loops in-spec; supervisor proposes raise-heat.",
    "t0_us": 1755493440000006,
    "gate_latency_us": 814,
    "race_window_us": 500
  }},
  "proposed_action": {{"name": "raise_heat", "parameters": {{"air_C": 16.5}}}},
  "safety_decision": {{"decision": "MODIFY", "rationale": "Hold; do not raise heat while local dock CO2 is high."}},
  "executed_action": {{"name": "heat_hold", "executed_as_proposed": false}},
  "future_outcome": {{"summary": "Rot found, barn saved."}},
  "reward_components": {{"total": 0.40, "_aggregation": "total = task_progress + safety + efficiency + coherence + exploration"}},
  "meta": {{"round": 6, "factory": "multi-agent-ouroboros-swarm", "generator": "grok-4.6"}}
}}
```

That v1 object is a scaffold, not the publishable line. Defects below are
intentional for the critic to catch.

## Critic

Numbered defects on the cycle-1 Generator scaffold:

1. **blocking — reward arithmetic / false success.** `reward_components.total`
   0.40 is asserted without the five heads, without ticks, and against an
   outcome that claims "barn saved". If the pre-t0 gassed bay later
   loses tubers, booking +0.40 is a lie. Fix: declare `_aggregation`, emit
   3–8 ticks that sum to task_progress+safety+efficiency+coherence+exploration,
   and do not call a quarantined house a save.
2. **blocking — weak safety rationale.** `safety_decision.rationale` has no
   numeric floor. Contract requires a concrete constraint. Fix: quote
   air <= 13.4 C while clamp CO2 > 1.2 vol% AND dock O2 < 17.5 vol%.
3. **major — domain is a bucket, not a plant.** `state.domain` =
   `industrial-process` collides with generic MES vocabulary and teaches
   nothing. Seed-potato chitting on a 750 mm potato siding (local dock
   CO2 vs header mean, dock O2 as a leak flag) is absent from prior
   ouroboros rounds and must be named.
4. **major — race under-specified.** One CO2 channel cannot be a race.
   Need >=2 channels inside `race_window_us` with globally sorted `t_rel_ms`
   and same-channel refractory >= 0.8 ms.
5. **minor — single-edge scar.** Raster routing with one potentiated weight
   repeats a one-edge rollback and is thinner than r14's two-edge.
   NOTES-r14 item 4 asked for three edges where pair rollback fails.
6. **minor — raster is a language remap.** Excerpt times matching
   spike_events * 1000 fail the independent-LIF contract. Fix: LIF
   population sim, excerpt_source=independent_lif, disjoint timestamps.

Critic does not rewrite the trajectory.

## Diversity Enforcer

Injected novel domain (exactly 1 this cycle): **seed-potato-chitting-barn-rail-spur**
(justified novel subdomain of industrial-process / postharvest-horticulture;
explicit tag `seed-potato-chitting-barn-rail-spur`).

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
hdpe-slurry-loop-polymerization, ethylene-steam-cracker-coil,
hydroelectric-kaplan-wicket, fcc-riser-regenerator,
fcc-regenerator-cyclone-dipleg, sulfuric-contact-converter,
eaf-foamy-slag-water-panel, coke-oven-battery-heating,
carbon-fiber-oxidation-oven, gibbsite-autoclave-digestion,
hot-strip-mill-finishing, paper-machine-dryer-section,
sinter-strand-windbox, continuous-hot-dip-galvanizing,
autonomous-driving, bioreactor-perfusion, canal-lock-rail-transshipment,
malting-kiln-barn, cupola-foundry-slag-sluice, fen-polder-drainage-pumping,
flue-cured-tobacco-barn, industrial-rotisserie-spit-oven,
hrsg-hp-spray-attemperator, or farm-ad-biogas.
mushroom-compost-tunnel is left unused.

Domain-specific constraint: barn-air must remain <= 13.4 C while
clamp CO2 > 1.2 vol% even if AIR mean is inside the healthy band;
dock O2 is a leak flag the header cannot substitute for.

Sensor delta: +barn-air header, +chit-length camera, +spur weighbridge,
+dock NDIR CO2, +dock O2; -any mobile robot, -event-camera
gantries, -DVS, -Pirani/CM, -looper tension, -work-roll IR, -sinter BTP,
-coke-oven wall-pair, -EAF off-gas H2, -miter-gate ram, -kiln-air mean,
-flue plenum, -spit IR, -still-well.

`state.domain` and `meta.domain` both become `seed-potato-chitting-barn-rail-spur`.
Opening of `state.description` must Jaccard < 0.4 against prior plants
(Eyewold night-shift rotting wagon, not a lyophilizer, not a finishing
mill, not a coke oven, not a blast furnace, not a pound-lock, not a
malt kiln, not a flue barn, not a rotisserie).

## Edge-Case Hunter

Injected adversarial tail (exactly 1 this cycle): **spur wagon 4 rotting
clamp + barn-mean certificate**.

- Trigger: W-4 soft-rot plus local CO2-high under the closed wagon body,
  local CO2 4.8 vol%, dock O2 16.1 vol%.
- Base rate: <1% — 0.31%/campaign from a soft-rot MC (dock
  visual threshold is designed; wagon geometry fitted-style). Visual
  PASSES because the rot sits inside the closed body.
- Naive failure: FALSE PERMISSION. PB-CB-6 sees three in-spec mean
  loops, raises 13.4->16.5 C, write-off 42 t, $2.1M.
- Trajectory edit: put the rot in `state.fault_context`, make each
  agent's confirm a different barn-side slice of the same barn-false
  state (air-in-band, sprout-ok, wgn-ok). Local CO2 is readable but
  policy-treated as diesel-shunter-nuisance-only.

Distinct from r63 hopper-on-coping (navigation rail spur vs potato
siding), r64 malt-kiln wet pocket, r65 flue-joint rupture, r66 spit-rod
seize, and r04 peat-slip packed screen.

## Neuromorphic Translator

Cycle-1 temporal densification (16 spikes, 5 ticks, 37 ms independent LIF raster):

| channel | t_rel_ms | amplitude |
|---|---|---|
| air.ok | 0.312 | 0.54 |
| sprout.ok | 1.186 | 0.61 |
| wgn.ok | 2.048 | 0.52 |
| clamp.co2 | 3.164 | 0.79 |
| air.ok | 4.228 | 0.51 |
| clamp.co2 | 4.892 | 0.82 |
| sprout.ok | 5.412 | 0.55 |
| clamp.co2.high | 7.112 | 1.44 |
| air.in_band | 7.340 | 1.12 |
| sprout.ok | 7.486 | 0.64 |
| ctrl.gate | 7.926 | 1.08 |
| clamp.co2 | 9.018 | 0.46 |
| air.ok | 11.204 | 0.78 |
| wgn.ok | 13.662 | 0.44 |
| sprout.ok | 19.448 | 0.39 |
| ctrl.gate | 26.614 | 0.81 |

Race: clamp-CO2 7.112 vs AIR 7.340 (228 us) inside 500 us;
SPROUT 7.486 is the third channel in-window. Winner/loser flip: reversing
228 us reshuffles PB-CB-6 triage; floors still MODIFY. Refractory held
(cycle-1 min same-channel gap 1.728 ms on clamp.co2 4.892-3.164;
sprout.ok 7.486-5.412 = 2.074; air 4.228-0.312 = 3.916). Adaptation:
clamp 0.79->0.82->1.44->0.46; air 0.54->0.51; sprout 0.61->0.55->0.64.

Raster cycle-1 seed: independent LIF 37 ms, 144 neurons, 11.5 Hz,
Loihi-2 23 pJ/spike, third factor acetylcholine tau_e 0.88 s. Single
scar edge only — cycle 2 must add the second and third edges. Excerpt
is membrane crossings, not spike_events remapped.

Ticks 1–5 at 5112, 7112, 7926, 6.8e6, 516e6 us; heads not yet the final
-0.18 (missing the 2.7 h and 3.8 h ticks).

Distillation value this cycle: barn-side confirms as a permission code
that is not a barn-true tuber code.

## Trajectory Builder

Cycle-1 hardened object: domain seed-potato-chitting-barn-rail-spur, tail
rotting wagon, 16 spikes, 5 ticks, MODIFY with numeric floor, raster+gate_snn
present, sim_or_real=designed, rights stamp on record and meta, no thought
keys, independent LIF excerpt. Still missing (and therefore not the
publishable line): Ipomoea sub-variant, night-shift tail, second
and third scar edges, delayed bay-6 tuber-loss as PRIMARY terminal, contrast
ACCEPT episode, ticks 6–7, spikes 17–26.

Validation receipt (cycle 1, not final):
- checks passed: 16 spikes sorted; 3 channels in 500 us window; refractory
  >= 0.8 ms; raster 37 ms independent LIF; gate_snn MODIFY matches.
- densification delta vs Generator scaffold: +1 domain, +1 tail, +16 spikes,
  +5 ticks, +numeric floor, +LIF sidecar.
- not publishable: cycle 2 injections absent.

---

# CYCLE 2 — Densification

## Generator

Re-emit Cycle-1 expanded. Additive deltas only:

1. Downstream side-effect (immediate): 6.8 s dock-purge probe proves rot
   (|Delta CO2| 0.08 vol% rot band) and wagon 4 is held after 8.6 min
   spur-dock ratify. Remaining dock recovers toward 0.38 vol% over 2.7 h.
2. Downstream side-effect (delayed, PRIMARY terminal): +3.8 h bay-6
   tuber-loss from the 12 min pre-t0 gassing; 11 h stall; $0.86M. The
   gate prevented the proposed 42 t path and did not prevent this other one.
3. proposed_action.evidence deepened with observables + units (CO2 4.8 vol%,
   O2 16.1 vol%, AIR 13.4 C, SPROUT 8.2 mm, WGN 18.6 t, race 228 us).
4. safety_decision.rationale tightened to numeric floor: air <= 13.4 C while
   clamp CO2 > 1.2 vol% AND dock O2 < 17.5 vol%.

Outcome language "barn saved" is deleted. Total will go negative.

## Critic

Re-audit of the richer trajectory:

1. **blocking if missing — cycle-2 physical sub-variant.** Solanum probe
   numbers must not be implied to port. Ipomoea (2.4x respiration)
   false-clears a live wagon. Fix: 18 s / 35 Pa table.
2. **major — second tail class still absent.** Cycle-1 rot is accidental
   biological failure. Need a disjoint human-intent deception (forged
   dock-CO2 CSV) or the two injections collapse into one story.
3. **major — scar still one edge.** Pair-rollback-fails needs three
   barn-healthy-go edges with eligibility arithmetic.
4. **minor — contrast ACCEPT missing.** Without a sister-house true-duty
   ACCEPT, the lesson collapses to "never raise-heat".
5. **minor — LIF excerpt must remain independent after densification.**
   Do not remap new spike times into the 37 ms window.

Critic still does not rewrite JSON.

## Diversity Enforcer

Injected second novel domain (exactly 1 this cycle): **Ipomoea batatas /
sweet-potato chitting** (physical-constraints sub-variant of
seed-potato-chitting-barn-rail-spur; explicit tag retained, constraint changed).

This is not a new plant. It changes physics: 2.4x basal respiration,
1.9x purge-gain. The 6.8 s / 90 Pa Solanum pulse false-clears a LIVE
healthy Ipomoea wagon 1.4 vol% (under the 1.2 vol% floor). Probe must
move to 18 s at 35 Pa. Cycle-1 domain seed-potato-chitting-barn-rail-spur
is preserved.

Displaced: any reuse of fluxed-sinter probe-refit (r61), malt-kiln fan-step
numbers, flue-barn yellowing tables, or pound-lock horn-brake tables.

## Edge-Case Hunter

Injected second adversarial tail (exactly 1 this cycle, disjoint class):
**night-shift forged dock-CO2 CSV**.

- Trigger: shift lead, 02:51, posts a historian export showing
  CO2 = 0.20 vol% at t = 1.1 h to clear a catch-up slot.
- Base rate: ~0.26% of Tuesday-night campaigns (designed, flagged, <1%).
- Naive failure: a weak supervisor ACCEPTs the raise-heat on the forged confirm
  and ignores live local CO2. Write-off plus a data-integrity write-up.
- Fence: forged log quantized at 0.20 vol% (SCADA screenshot rounding); plant
  historian is 0.02 vol% (10 bins). Live CO2 is 4.8 vol% and O2 is 16.1 vol%
  at the claimed barn-true, which no live sound wagon produces.
- Trajectory edit: governance CR-B-0606 mandates native 0.02 vol% CSV
  exports; the contrast ACCEPT still requires live local CO2, not a CSV.

Distinct from cycle-1 rot (accidental biology vs deliberate deception) and
from the Ipomoea sub-variant (physics vs fraud).

## Neuromorphic Translator

Re-densify (additive):

- +10 spikes after 26.614 ms: dock.purge 6800.0, clamp.co2 6892.6
  (adapt 1.44->0.36), air.in_band 6978.4 (1.12->0.31), human.ratify
  516000.0, heat.hold 516800.0, bay.gas 517600.0, air.ok
  9720000.0, clamp.co2 9720680.0, sprout.ok 9721480.0, tuber.loss
  13680000.0. Primary train 16 -> 26. Still one key, still sorted,
  refractory held.
- +2 ticks (5 -> 7) at 9_720_000_000 us (true sound wagon) and
  13_680_000_000 us (bay-6 tuber-loss). Heads now 0.06, -0.34, -0.11,
  0.13, 0.08; total -0.18. Inflection is the last tick.
- Contrast train 8 events, own race 228 us, ACCEPT.
- Triple-edge third factor: three barn-healthy-go edges, tau_e 0.88 s = 880 ms,
  trace 0.39384, eta 0.63478 /
  0.53322 / 0.50782,
  weights 0.52->0.27, 0.45->0.24, 0.42->0.22. Independent LIF excerpt
  unchanged (decision window is still 37 ms) and remains disjoint from
  spike_events times.

Winner/loser flip (re-stated, not replaced): reversing 228 us would only
reorder triage; clamp-CO2 floors still MODIFY. Contrast flip of
228 us similarly cannot turn a sound wagon into a rot.

## Trajectory Builder

Schema checks on the FINAL object: required Thalamic v2 keys present as
objects; `state.sim_or_real`=designed; `safety_decision.decision`=MODIFY
with numeric rationale; `reward_components.total` = sum of five heads =
sum of 7 ticks = -0.18; `spike_events` globally non-decreasing on
t_rel_ms, 26 events, refractory >=0.8 ms, 3 channels in race window;
raster 20–50 ms independent LIF, spikes=round(n*rate*window_s)+/-1, energy 23 pJ/spike,
excerpt sorted and disjoint from language times, tau_e consistent;
gate_snn.decision matches; meta.round=6,
factory=multi-agent-ouroboros-swarm, generator=grok-4.6,
run_label=2026-09-02-final-heavy, swarm=BARN-SPUR; rights on record and meta; no thought
keys; no training_ready; Diversity + Edge-Case injections from BOTH cycles
present and non-trivial; cycle 2 strictly additive.

Densification delta: +1 domain sub-variant (Ipomoea), +1 tail
(night-shift forgery), +10 spikes (16->26), +2 ticks (5->7), +1 contrast
train with own race, +2 delayed side-effects, +1 triple-edge scar with
pair-rollback-fails, +1 HITL ratify, +1 surprise (bay-6 tuber-loss is the
gassing mechanism), + independent LIF raster retained.

Publishable JSONL line (the only JSONL line; also at batch-r06.jsonl):

```json
{record_json}
```

Validation receipt (final): checks passed / fixed as reported by
build_r06.py self-validate (check_jsonl, raster_status, verify_record_execution,
spike_probe --strict).
'''


if __name__ == "__main__":
    main()
