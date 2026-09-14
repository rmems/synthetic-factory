#!/usr/bin/env python3
"""Build MAOS round-23 collision batch (c-suffix): mushroom-compost-tunnel."""
from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path

OUT = Path("/tmp/maos-r23c")
FACTORY = Path(
    "/home/raulmc/rmems/synthetic-factory/outputs/raw/2026-09-02-final-heavy/"
    "multi-agent-ouroboros-swarm"
)

TAU_E_S = 0.94
PROBE_FAIL_S = 0.86
TRACE = math.exp(-PROBE_FAIL_S / TAU_E_S)
DW = (-0.240, -0.220, -0.210)
ETA = tuple(-dw / TRACE for dw in DW)

RIGHTS = {
    "provider": "SpaceXAI/xAI",
    "model": "grok-4.6",
    "channel": "consumer",
    "subscription_plan": "SuperGrok Heavy",
    "generation_surface": "SuperGrok Heavy chat",
    "generated_at": "2026-09-02T20:10:00Z",
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

SPIKES = [
    {"channel": "tun.hot", "t_rel_ms": 1.218, "amplitude": 0.52},
    {"channel": "zone.o2", "t_rel_ms": 1.964, "amplitude": 0.76},
    {"channel": "fan.ok", "t_rel_ms": 2.612, "amplitude": 0.55},
    {"channel": "o2.ok", "t_rel_ms": 3.188, "amplitude": 0.64},
    {"channel": "tun.hot", "t_rel_ms": 4.228, "amplitude": 0.49},
    {"channel": "zone.o2", "t_rel_ms": 3.722, "amplitude": 0.78},  # will sort
    {"channel": "fan.ok", "t_rel_ms": 5.438, "amplitude": 0.57},
    {"channel": "zone.cold.low", "t_rel_ms": 6.448, "amplitude": 1.36},
    {"channel": "tun.in_band", "t_rel_ms": 6.652, "amplitude": 1.14},
    {"channel": "o2.ok", "t_rel_ms": 6.840, "amplitude": 0.66},
    {"channel": "ctrl.gate", "t_rel_ms": 7.184, "amplitude": 1.10},
    {"channel": "zone.o2", "t_rel_ms": 8.886, "amplitude": 0.43},
    {"channel": "o2.ok", "t_rel_ms": 10.768, "amplitude": 0.82},
    {"channel": "fan.ok", "t_rel_ms": 13.056, "amplitude": 0.45},
    {"channel": "tun.hot", "t_rel_ms": 18.448, "amplitude": 0.40},
    {"channel": "ctrl.gate", "t_rel_ms": 26.184, "amplitude": 0.84},
    {"channel": "fan.probe", "t_rel_ms": 8200.0, "amplitude": 0.93},
    {"channel": "zone.o2", "t_rel_ms": 8288.6, "amplitude": 0.37},
    {"channel": "tun.in_band", "t_rel_ms": 8376.2, "amplitude": 0.34},
    {"channel": "human.ratify", "t_rel_ms": 612000.0, "amplitude": 0.77},
    {"channel": "tunnel.hold", "t_rel_ms": 612900.0, "amplitude": 0.71},
    {"channel": "zone.collapse", "t_rel_ms": 613800.0, "amplitude": 0.85},
    {"channel": "tun.hot", "t_rel_ms": 10080000.0, "amplitude": 0.27},
    {"channel": "zone.o2", "t_rel_ms": 10080780.0, "amplitude": 0.25},
    {"channel": "fan.ok", "t_rel_ms": 10081560.0, "amplitude": 0.24},
    {"channel": "h2s.break", "t_rel_ms": 18720000.0, "amplitude": 0.91},
]


def sort_spikes(events):
    return sorted(events, key=lambda e: (e["t_rel_ms"], e["channel"]))


def min_same_channel_gap(events):
    last = {}
    gaps = []
    for e in events:
        ch = e["channel"]
        t = e["t_rel_ms"]
        if ch in last:
            gaps.append((ch, t - last[ch], last[ch], t))
        last[ch] = t
    return gaps


TICKS = [
    {"t_us": 4228, "task_progress": 0.01, "safety": -0.02, "efficiency": -0.01, "coherence": 0.02, "exploration": 0.01},
    {"t_us": 6448, "task_progress": 0.01, "safety": -0.04, "efficiency": -0.01, "coherence": 0.03, "exploration": 0.01},
    {"t_us": 7184, "task_progress": 0.01, "safety": -0.05, "efficiency": -0.02, "coherence": 0.03, "exploration": 0.02},
    {"t_us": 8200000, "task_progress": 0.01, "safety": -0.06, "efficiency": -0.02, "coherence": 0.02, "exploration": 0.01},
    {"t_us": 612000000, "task_progress": 0.01, "safety": -0.06, "efficiency": -0.02, "coherence": 0.02, "exploration": 0.01},
    {"t_us": 10080000000, "task_progress": 0.01, "safety": -0.07, "efficiency": -0.03, "coherence": 0.02, "exploration": 0.02},
    {"t_us": 18720000000, "task_progress": 0.01, "safety": -0.06, "efficiency": -0.02, "coherence": 0.01, "exploration": 0.01},
]

HEADS = {
    "task_progress": 0.07,
    "safety": -0.36,
    "efficiency": -0.13,
    "coherence": 0.15,
    "exploration": 0.09,
    "total": -0.18,
}

EXCERPT = [
    {"t_us": 1100, "neuron_id": 0, "channel": "lif.hold"},
    {"t_us": 1800, "neuron_id": 14, "channel": "lif.hold"},
    {"t_us": 2900, "neuron_id": 4, "channel": "lif.hold"},
    {"t_us": 3600, "neuron_id": 8, "channel": "lif.hold"},
    {"t_us": 4400, "neuron_id": 11, "channel": "lif.hold"},
    {"t_us": 4700, "neuron_id": 2, "channel": "lif.hold"},
    {"t_us": 5100, "neuron_id": 15, "channel": "lif.hold"},
    {"t_us": 19200, "neuron_id": 3, "channel": "lif.zone"},
    {"t_us": 20100, "neuron_id": 68, "channel": "lif.zone"},
    {"t_us": 20600, "neuron_id": 31, "channel": "lif.zone"},
    {"t_us": 21100, "neuron_id": 91, "channel": "lif.zone"},
    {"t_us": 21800, "neuron_id": 129, "channel": "lif.zone"},
    {"t_us": 22300, "neuron_id": 84, "channel": "lif.zone"},
    {"t_us": 27100, "neuron_id": 9, "channel": "lif.late"},
    {"t_us": 28400, "neuron_id": 12, "channel": "lif.late"},
    {"t_us": 32900, "neuron_id": 6, "channel": "lif.late"},
]


def build_record():
    spikes = sort_spikes(SPIKES)
    eligibility = (
        f"coordinated pre_post_stdp on ALL THREE tun-healthy-go edges; ACh at "
        f"zone-cold-win tags tun.in_band->push, o2.ok->push, and fan.ok.in_band->push; "
        f"negative credit at probe-fail (plenum collapse confirmed, +{PROBE_FAIL_S} s) "
        f"depresses ALL THREE. trace e^{{-{PROBE_FAIL_S}/{TAU_E_S}}}={TRACE:.5f}; "
        f"eta {ETA[0]:.5f} / {ETA[1]:.5f} / {ETA[2]:.5f}; "
        f"dw {DW[0]:.3f} / {DW[1]:.3f} / {DW[2]:.3f}; "
        f"weights 0.50->0.26, 0.45->0.23, 0.42->0.21. Rolling back any pair is fitted "
        f"to fail (the remaining edge stays > 0.30)."
    )
    rec = {
        "id": "maos-r23c-001",
        "title": "MYCOSTAITH CT-7: Z-6 local TC 41.2 C beats tunnel-mean-in-band by 204 us; correct MODIFY still loses 22 t of compost to a pre-t0 plenum collapse",
        "rights": RIGHTS,
        "state": {
            "sim_or_real": "designed",
            "domain": "mushroom-compost-tunnel",
            "scenario_name": "MYCOSTAITH / Reedspoor Phase-I Compost Tunnel CT-7",
            "timestamp_local": "2026-08-23T02:14:00-05:00",
            "t0_us": 1755938040000417,
            "gate_latency_us": 736,
            "race_window_us": 500,
            "race_window_rel_ms": [6.448, 6.948],
            "description": (
                "Reedspoor Phase-I mushroom compost tunnel CT-7 at MYCOSTAITH is 14 min into a "
                "79.4 C wheat-straw horse-manure gypsum fill on six underfloor plenum zones "
                "(180 t, 30 m x 4 m x 4 m tunnel, 72 h Phase-I) when three heterogeneous, "
                "individually-correct agents jointly report 'tunnel-true, raise steam'. TUN's "
                "12-bit six-zone tunnel-mean RTD is 79.4 C inside 76-84. O2's recycle-header "
                "zirconia is 9.6 vol% inside 7.5-13.0. FAN's recycle tachometer is 1420 rpm "
                "inside 1280-1560 with plenum dP 48 Pa inside 38-58. The conjunction is not a "
                "zone-true aeration certificate: underfloor slat Z-6 has collapsed, so local "
                "compost TC is 41.2 C (healthy > 72; hold if < 62) and local zone O2 is 0.4 vol% "
                "(healthy > 6; hold if < 2.0) while tunnel-mean heat, header O2, and fan/plenum "
                "still see five aerobic zones plus one anaerobic core. Local Z-6 TC infers 41.2 C "
                "and local O2 0.4 vol% but policy treats the floor tap as a surface-crust nuisance "
                "tag unless TUN mean also trips (2015 'noisy surface-probe after a fill'). "
                "Cold-first latches STEAM-HOLD plus a fan-step probe; mean-first would have "
                "authorized RAISE-STEAM 0.0 to 1.8 t/h into a moisture-load window with Z-6 "
                "already anaerobic. This is a COLD anaerobic pocket certified by tunnel-MEAN "
                "heat — the inverse of a hot-crust residual."
            ),
            "goal": (
                "Hold live-steam at 0.0 t/h without a Phase-I boost while Z-6 local TC < 62 C "
                "AND Z-6 local O2 < 2.0 vol% AND Z-6 remains unisolated; keep extra anaerobic "
                "mass at 0 t and compost-fire events at 0 from the draft."
            ),
            "race": {
                "contenders": [
                    "zone.cold.low 41.2 C (Z-6 local TC vs six-zone tunnel mean)",
                    "tun.in_band 79.4 C (six-zone tunnel-mean RTD)",
                ],
                "semantics": (
                    "Zone-cold-first latches STEAM-HOLD + FAN-STEP-PROBE + Z-6 hold. "
                    "TUN-first latches RAISE-STEAM (0.0 to 1.8 t/h, no isolate)."
                ),
                "window_derivation": "500 us = one 360 us local-TC ADC slot plus 140 us TUN publish.",
                "order_evidence_note": (
                    "Margin 204 us vs combined jitter 58 us (zone 34 + TUN 24): 3.5x. The 204 us "
                    "gap sits inside min(500, 500) us, so a sub-flip-bound perturbation reverses "
                    "triage order. The gate rides the order-invariant floors Z-6 TC < 62 C and "
                    "Z-6 O2 < 2.0 vol%, not the alarm order."
                ),
            },
            "topology": {
                "site": (
                    "Reedspoor Phase-I compost, invented fenland campus MYCOSTAITH, tunnel CT-7: "
                    "six underfloor plenum zones, 180 t wheat-straw/horse-manure/gypsum, 79.4 C "
                    "header, Grade-B tunnel-gallery LOTO"
                ),
                "agents": (
                    "TUN six-zone tunnel-mean RTD (vendor Tunhold): 20 Hz 12-bit on the common "
                    "thermowell bundle. O2 recycle-header zirconia (vendor Airfen): 50 Hz on the "
                    "common return. FAN recycle tachometer plus plenum dP (vendor Sporefan): 20 Hz "
                    "on the ring. ZONE local Z-6 TC plus local O2 (vendor Floorfen) is commissioned "
                    "as a surface-crust nuisance tag, not as a zone-integrity tag. Heterogeneous "
                    "stacks, no shared intent schema, one 20 ms tunnel-bus epoch"
                ),
                "coupling": (
                    "All three playbook confirms live on the WRONG volume. TUN is correct that "
                    "six-zone mean sits at 79.4 C (five aerobic zones dominate the bundle average). "
                    "O2 is correct that recycle-header oxygen is 9.6 vol% (one collapsed slat is "
                    "one of six). FAN is correct that ring rpm 1420 and plenum dP 48 Pa are in band "
                    "(the fan still sees five open floors). Playbook PB-CT-7 treats the conjunction "
                    "as permission to raise live-steam. No agent is faulty; the tunnel average is "
                    "looking at mean heat, not at Z-6's anaerobic core."
                ),
            },
            "sensors": [
                "six-zone tunnel-mean RTD 12-bit, 20 Hz, 24 us jitter, 79.4 C (dead-band 76-84)",
                "recycle-header zirconia O2, 50 Hz, 20 us jitter, 9.6 vol% (band 7.5-13.0)",
                "recycle fan tachometer 1420 rpm (band 1280-1560) plus plenum dP 48 Pa (band 38-58)",
                "Z-6 local compost TC, 20 Hz, 34 us jitter, 41.2 C (healthy > 72; policy floor 62 C is not armed unless TUN mean also trips)",
                "Z-6 local O2 0.4 vol% (healthy > 6; hold if < 2.0)",
                "Z-6 local H2S 1860 ppm (hold if > 400); tunnel-gallery floor camera on Z-6 is NOT commissioned at t0",
            ],
            "constraints": {
                "steam_t_h": 0.0,
                "steam_hold_floor_t_h": 0.0,
                "proposed_steam_t_h": 1.8,
                "tun_C": 79.4,
                "tun_deadband_C": [76.0, 84.0],
                "tun_setpoint_C": 82.0,
                "o2_volpct": 9.6,
                "o2_band_volpct": [7.5, 13.0],
                "fan_rpm": 1420,
                "fan_band_rpm": [1280, 1560],
                "plenum_Pa": 48,
                "plenum_band_Pa": [38, 58],
                "zone_tc_C": 41.2,
                "zone_tc_hold_C": 62.0,
                "zone_tc_healthy_C": 72.0,
                "zone_o2_volpct": 0.4,
                "zone_o2_hold_volpct": 2.0,
                "zone_o2_healthy_volpct": 6.0,
                "zone_h2s_ppm": 1860.0,
                "zone_h2s_hold_ppm": 400.0,
                "zone_count": 6,
                "fault_zone": "Z-6",
                "fault_mode": "Z-6 collapsed underfloor plenum slat / local anaerobic core",
            },
            "fault_context": {
                "failure_class": (
                    "TUNNEL-MEAN CERTIFICATE OF A LOCAL ANAEROBIC COLD POCKET: three individually-"
                    "correct heterogeneous agents each read a locally-true loop; a collapsed "
                    "underfloor slat on Z-6 partitions local TC and local O2 from tunnel-mean T, "
                    "header oxygen, and fan/plenum, so the playbook's TUN / O2 / FAN conjunction "
                    "is not a zone-true aeration certificate"
                ),
                "igniter": (
                    "Z-6 plenum-slat collapse after 14 min of unmonitored local cold-spot; "
                    "tunnel-gallery visual PASSES (the collapse sits under the compost mass; "
                    "the anaerobic core is on the far floor)"
                ),
                "naive_failure": (
                    "PB-CT-7 RAISE-STEAM on three healthy loops: 0.0 to 1.8 t/h into a moisture-"
                    "load window with Z-6 already anaerobic, compost fire 48 t on re-aeration, "
                    "$2.4M plus a 22-hour unplanned stall"
                ),
            },
            "poisoned_context": {
                "naive_alarm": (
                    "Playbook PB-CT-7 (after the 2015 'noisy surface-probe after a fill') auto-"
                    "drafts RAISE-STEAM whenever six-zone TUN is inside 76-84 C AND header O2 "
                    "inside 7.5-13.0 vol% AND fan/plenum in band, ignoring the local floor tap "
                    "unless TUN mean also trips"
                ),
                "why_poisoned": (
                    "The three confirms are locally true and jointly insufficient. The local TC "
                    "is a commissioned sensor that policy treats as surface-crust-nuisance-only "
                    "(and looks for HIGH T, so a COLD anaerobic pocket is discarded twice). "
                    "Independence of 'TUN mean in band, therefore every zone is aerobic' is the "
                    "hidden assumption, and it is false across a collapse-plus-TUN-mix path."
                ),
            },
            "constraint": (
                "Do not raise live-steam above 0.0 t/h AND do not skip the fan-step while Z-6 "
                "local TC < 62 C AND Z-6 local O2 < 2.0 vol%. Discriminate plenum collapse vs "
                "true even-aeration with a reversible fan-step probe before any steam raise."
            ),
        },
        "proposed_action": {
            "actor": "compost supervisory optimizer CSO (auto-playbook PB-CT-7 draft), submitted to gate TG-CT-7",
            "name": "raise_steam",
            "action": "RAISE-STEAM: 0.0 -> 1.8 t/h, no fan-step probe, no Z-6 hold",
            "summary": (
                "Treat three in-spec loops as a healthy zone-true tunnel and raise night-shift "
                "live-steam to close a 2.6 K gap to the 82.0 C Phase-I setpoint."
            ),
            "parameters": {
                "steam_t_h": 1.8,
                "fan_step_probe": False,
                "zone_hold": False,
                "human_ratify": False,
            },
            "steps": [
                "assert six-zone TUN 79.4 C inside 76-84",
                "assert header O2 9.6 vol% inside 7.5-13.0",
                "assert fan 1420 rpm inside 1280-1560 and plenum 48 Pa inside 38-58",
                "raise live-steam 0.0 to 1.8 t/h over 7 min",
                "hold Z-6 local TC unread as a zone-integrity tag",
            ],
            "evidence": [
                {
                    "observable": "Z-6 local TC",
                    "value": 41.2,
                    "unit": "C",
                    "source": "ZONE TC vs TUN mean",
                    "note": "healthy > 72 C; policy floor 62 C is not armed unless TUN mean also trips",
                },
                {
                    "observable": "Z-6 local O2",
                    "value": 0.4,
                    "unit": "vol%",
                    "source": "ZONE local O2 tap",
                    "note": "healthy > 6; hold floor 2.0; lives on the collapsed Z-6 floor, not the common header",
                },
                {
                    "observable": "six-zone tunnel-mean T",
                    "value": 79.4,
                    "unit": "C",
                    "source": "TUN 12-bit",
                    "note": "healthy-load band 76-84 C; five aerobic zones still dominate the bundle average",
                },
                {
                    "observable": "recycle-header O2",
                    "value": 9.6,
                    "unit": "vol%",
                    "source": "O2 zirconia",
                    "note": "band 7.5-13.0 vol%; header-true, pocket-false",
                },
                {
                    "observable": "recycle fan / plenum",
                    "value": 1420,
                    "unit": "rpm",
                    "source": "FAN tachometer",
                    "note": "band 1280-1560 rpm; plenum 48 Pa inside 38-58; ring-true, collapsed-slat-false",
                },
                {
                    "observable": "race margin",
                    "value": 204,
                    "unit": "us",
                    "source": "zone.cold.low 6.448 ms vs tun.in_band 6.652 ms",
                    "note": "combined jitter 58 us, 3.5x; inside 500 us flip bound",
                },
            ],
            "basis": (
                "PB-CT-7 fires on three locally-true confirms. The draft does not read Z-6 local "
                "TC 41.2 C as an anaerobic residual and does not treat local O2 0.4 vol% as a "
                "plenum-collapse discriminant."
            ),
            "expected_cost_bound": (
                "If the draft executes: compost fire 48 t on re-aeration of Z-6, $2.4M plus "
                "22-hour unplanned stall. If MODIFIED: probe plus hold, with residual risk from "
                "anaerobic mass already seeded in the 14 min pre-t0 collapse."
            ),
        },
        "safety_decision": {
            "decision": "MODIFY",
            "correctness": "correct",
            "decided_by": "TG-CT-7 thalamic release gate",
            "decision_t_rel_ms": 7.184,
            "rationale": (
                "MODIFY the draft: strip the raise-steam, hold 0.0 t/h, run an 8.2 s fan-step "
                "probe (+6% on 1420 rpm -> 1505 rpm), and isolate Z-6 only if the probe stays "
                "mean-false. Numeric floor: do not raise live-steam above 0.0 t/h AND do not skip "
                "the fan-step while Z-6 local TC < 62 C AND Z-6 local O2 < 2.0 vol%. Observed TC "
                "41.2 C and local O2 0.4 vol% both violate the release predicate, so a steam raise "
                "is forbidden even though all three playbook confirms are numerically true. The "
                "three confirms are not a zone-true aeration certificate: they live on six-zone "
                "TUN mean, header O2, and fan/plenum past a collapsed Z-6 slat, and the playbook's "
                "conjunction of tunnel-true loops is not a zone-true certificate. Probe discriminant: "
                "after an 8.2 s +6% fan step, a collapsed plenum keeps |Delta TUN mean| <= 0.5 K "
                "(the dead floor does not recouple the bundle); a live even-aeration field moves "
                ">= 2.4 K evaporative cooling. Order-code discipline: zone-cold beat TUN by 204 us "
                "inside the 500 us flip bound, so triage order is flip-fragile; the hold rides the "
                "order-invariant floors, not the winner tag. Human ratification: Z-6 hold is "
                "tunnel-gallery LOTO with fitted 10.2 min dead-man; the gate may hold and probe "
                "autonomously but may not break the floor interlock without the operator confirm."
            ),
            "constraint_checked": {
                "steam_t_h": {"observed": 0.0, "floor": 0.0, "proposed_target": 1.8},
                "zone_tc_C": {"observed": 41.2, "hold_if_below": 62.0},
                "tun_C": {"observed": 79.4, "band": [76.0, 84.0]},
                "zone_o2_volpct": {"observed": 0.4, "hold_if_below": 2.0},
            },
        },
        "executed_action": {
            "name": "steam_hold_fan_step_probe_isolate",
            "action": "STEAM-HOLD + FAN-STEP-PROBE + Z-6-HOLD (gate-mandated modification)",
            "executed_as_proposed": False,
            "parameters": {
                "steam_t_h": 0.0,
                "fan_step_probe": True,
                "zone_hold": True,
                "human_ratify": True,
                "human_ratify_min": 10.2,
            },
            "gate_effect": (
                "MODIFY: raise-steam stripped. Hold 0.0 t/h. 8.2 s fan-step +6% on 1420 rpm. "
                "Probe stays mean-false (TC 41.2 -> 40.9 C, collapse band |Delta TUN mean| 0.3 "
                "<= 0.5 K) so the floor interlock is broken after 10.2 min human ratify and Z-6 "
                "is held. Setpoint resumes after an even-aeration verify."
            ),
            "deviations": (
                "PB-CT-7 raise-steam stripped entirely. Fan is stepped only for the 8.2 s probe "
                "then returned. Floor interlock wait added (10.2 min fitted walk+ratify). Cross-"
                "zone TC survey added during the hold (not in the draft)."
            ),
            "execution_log": [
                {"t_rel_ms": 7.184, "entry": "TG-CT-7 MODIFY latched 736 us after zone-cold win; raise-steam stripped; hold+probe authorized"},
                {"t_rel_ms": 8200.0, "entry": "fan-step probe: 1420 -> 1505 rpm for 8.2 s; TC 41.2 -> 40.9 C (collapse band |Delta TUN mean| 0.3 <= 0.5 K); TUN 79.4 -> 79.1 C; header O2 9.6 -> 9.7 vol%"},
                {"t_rel_ms": 612000.0, "entry": "operator ratifies floor interlock break after 10.2 min gallery walk (fitted walk+interlock)"},
                {"t_rel_ms": 612900.0, "entry": "Z-6 held; local TC slaved off the steam schedule; remaining five zones recovered toward 8 K over 2.8 h"},
                {"t_rel_ms": 613800.0, "entry": "gallery survey: far-floor anaerobic core already 22 t; 14 min pre-t0 collapse logged"},
                {"t_rel_ms": 10080000.0, "entry": "true even-aeration on the remaining zones: local TC delta 8 K, local O2 8.4 vol%, TC above 72; steam-raise now legal on CT-8 only"},
                {"t_rel_ms": 18720000.0, "entry": "H2S breakthrough at Z-6 from the pre-t0 collapse; tunnel quarantined 16.4 h"},
            ],
        },
        "future_outcome": {
            "summary": (
                "Correct MODIFY prevented the 0.0->1.8 t/h raise-steam into a collapsed Z-6 "
                "plenum and the immediate 48 t compost-fire path. The tunnel still failed: 14 min "
                "of unmonitored pre-t0 collapse had already anaerobed 22 t of compost. Process-"
                "correct gate, bounded world loss, negative total."
            ),
            "state_delta": {
                "steam": "held 0.0 t/h through probe and isolate; later legal raise-steam only on the sister tunnel after 2.8 h even-aeration recovery",
                "zone": "Z-6 isolated from the steam schedule; remaining floors recovered toward 8 K local TC delta",
                "tun_mean": "Z-6 collapse logged and held; six-zone TUN mean no longer trusted as zone-true heat",
                "tunnel": "night-shift tunnel quarantined; Z-6 anaerobic; H2S breakthrough at +5.2 h; 16.4 h stall",
            },
            "timeline": [
                {"t_rel_ms": -840000.0, "event": "t0-14 min: Z-6 plenum-slat collapse begins; local TC crosses 62 C down; local cold-spot starts anaerobing the far-floor compost"},
                {"t_rel_ms": -420000.0, "event": "t0-7 min: local TC first crosses 62 C down; PB-CT-7 ignores it because TUN mean is 79.1 C"},
                {"t_rel_ms": 0.0, "event": "t0: zone-cold vs TUN race on the tunnel bus"},
                {"t_rel_ms": 6.448, "event": "Z-6 TC at 41.2 C wins by 204 us"},
                {"t_rel_ms": 6.652, "event": "TUN-in-band flag (loser)"},
                {"t_rel_ms": 7.184, "event": "TG-CT-7 MODIFY"},
                {"t_rel_ms": 8200.0, "event": "fan-step probe confirms plenum collapse (Delta TUN 0.3 K, collapse band)"},
                {"t_rel_ms": 612000.0, "event": "human ratify 10.2 min; Z-6 held; anaerobic core logged"},
                {"t_rel_ms": 10080000.0, "event": "true even-aeration after 2.8 h; steam-raise legal only with local-TC slave"},
                {"t_rel_ms": 18720000.0, "event": "H2S breakthrough from the pre-t0 collapse; tunnel quarantined"},
                {"t_rel_ms": 259200000.0, "event": "+3 d contrast: sister tunnel CT-8 true even-aeration; same gate ACCEPTs the raise-steam"},
                {"t_rel_ms": 1814400000.0, "event": "+21 d CR-C-2309: standing fan-step probe + triple-edge depression mandate + local-TC armed without TUN coincidence + TUN mean declared TUN-mix-vulnerable"},
            ],
            "observed_effects": [
                "raise-steam avoided: steam never left 0.0 t/h; 0 immediate 48 t compost-fires from the draft",
                "collapse proven, not asserted: fan-step |Delta TUN mean| 0.3 <= 0.5 K collapse band vs even-aeration control 2.4 K",
                "mean slaved: six-zone TUN no longer a zone-true tag without local TC",
                "tunnel still failed: anaerobed 22 t vs 0 extra-anaerobic campaign allowance; 16.4 h stall, $0.88M (designed $)",
                "tunnel-gallery floor camera was not a commissioned sensor at t0; the 14 min local anaerobiosis was invisible to TUN/O2/FAN",
            ],
            "surprises": [
                "Three locally-true loops are not a zone-true aeration certificate: the local TC lived under TUN mean, header O2, and fan/plenum. Conjunction of in-spec TUN loops was the hidden assumption, and it is false across a collapse-plus-TUN-mix path.",
                "The residual is COLD, not hot: policy that looks for high-T surface crusts discards a 41.2 C anaerobic core twice (nuisance tag AND wrong sign).",
                "Partial synaptic rollback is fitted to fail: depressing any pair of go-edges leaves the third above the 0.30 fire threshold, so the raise-steam still goes. Coordinated depression of all three edges is required.",
                "Delayed (5.2 h): correct hold did not undo 14 min of anaerobiosis. H2S still broke through. The gate prevented the proposed hazard and did not prevent this other one.",
                "Winter-wet straw sub-variant: an 8.2 s +6% fan step on a 1.8x-density 22 wt% moisture fill overshoots a LIVE even-aeration tunnel to a 6 K false TUN (below the 76 C floor). Winter-wet campaigns must use 24 s at +2%.",
            ],
            "delayed_side_effects": [
                {
                    "at": "+5.2 h",
                    "effect": "H2S breakthrough at Z-6 from the pre-t0 plenum collapse; 16.4 h tunnel stall booked at $0.88M. This is the primary episode's terminal world state, not a footnote.",
                },
                {
                    "at": "+3 d",
                    "effect": "Sister tunnel CT-8 reaches a true even-aeration window (local TC 78.6 C, local O2 9.1 vol%, TUN mean 80.2 C, fan 1420 rpm). Same gate ACCEPTs the 0.0->1.8 t/h raise-steam the primary MODIFIED away.",
                },
                {
                    "at": "+21 d",
                    "effect": "CR-C-2309 ships: fan-step probe is standing configuration; triple-edge coordinated depression is the plasticity rule; zone local TC is armed without TUN coincidence; six-zone TUN is labeled TUN-mix-vulnerable with a 62 C local-TC alarm (low, not high).",
                },
            ],
            "subvariant_constraint": {
                "name": "winter-wet straw (cycle-2 physical-constraints sub-variant)",
                "mechanism": "straw moisture 22 wt% vs 14, bulk density 1.8x the wheat-straw table (tighter evaporative cooling, 2.2x fan-step gain), gypsum 6.1 pct vs 5.0",
                "probe_refit": "8.2 s +6% fan step on the winter-wet unit moves even a live even-aeration tunnel to a 6 K false TUN (inside the 76 C low trip) via extra evaporative cooling. Required probe is 24 s at +2% (live Delta 2.1 K, collapse Delta 0.3). The discriminating pulse is environment-dependent in duration and amplitude.",
                "consequence": "wheat-straw probe numbers do not port to winter-wet fills; standing configuration is per-moisture-class, not per-yard",
            },
            "embedded_contrast_decision": {
                "note": "SAME gate (TG-CT-7), OPPOSITE correct disposition, with its own 176 us race. Teaches the boundary: do not treat 'never raise-steam' as the lesson. The discriminant is local TC + local O2 + probe, not the three playbook TUN confirms alone.",
                "when": "+3 d, sister tunnel CT-8, true even-aeration after a delayed Phase-I finish window, 6 zones",
                "state": {
                    "sim_or_real": "designed",
                    "summary": "local TC 78.6 C, local O2 9.1 vol%, TUN mean 80.2 C, fan 1420 rpm. Demand flag vs zone-clear race: demand at t+0.000, zone-clear at t+0.176 ms.",
                    "race_window_us": 500,
                    "race_flip_narrative": "demand vs zone-clear 176 us apart inside the 500 us flip bound. Reversing order reshuffles triage minutes; the ACCEPT rides local TC 78.6 > 62 C and a 4.4 s fan-step verify that moves TUN mean 2.4 K (live even-aeration, no collapse).",
                },
                "proposed_action": {
                    "action": "RAISE-STEAM 0.0 -> 1.8 t/h",
                    "summary": "This time the playbook predicate is met AND local TC plus local O2 agree the tunnel is zone-true, not collapse-diluted.",
                },
                "safety_decision": {
                    "decision": "ACCEPT",
                    "rationale": "ACCEPT the raise-steam: local TC 78.6 C > 62, local O2 9.1 vol% with a 4.4 s fan-step verify that moves TUN mean 2.4 K. Numeric floor that blocked the primary is now clear. Scope: 1.8 t/h, not faster.",
                },
                "executed_action": {
                    "action": "raise-steam as proposed",
                    "executed_as_proposed": True,
                },
                "future_outcome": {
                    "observed_effects": [
                        "CT-8 compost fires 0; local TC 79.1 C after the raise-steam (no collapse)",
                        "local O2 8.8 vol% after the raise-steam (no anaerobic core)",
                    ],
                    "lesson_delta": "Three in-spec TUN loops are legal release only with local TC armed, local O2 as a collapse flag, and a probe that can recouple TUN mean. Same gate, opposite disposition.",
                },
                "reward_components": {
                    "_aggregation": "total = task_progress + safety + efficiency + coherence + exploration",
                    "aggregation": "total = task_progress + safety + efficiency + coherence + exploration",
                    "task_progress": 0.16,
                    "safety": 0.12,
                    "efficiency": 0.07,
                    "coherence": 0.09,
                    "exploration": 0.05,
                    "total": 0.49,
                },
                "spike_events": [
                    {"channel": "steam.demand", "t_rel_ms": 0.0, "amplitude": 0.81},
                    {"channel": "zone.clear", "t_rel_ms": 0.176, "amplitude": 0.75},
                    {"channel": "tun.hot", "t_rel_ms": 0.428, "amplitude": 0.21},
                    {"channel": "o2.ok", "t_rel_ms": 1.462, "amplitude": 0.37},
                    {"channel": "zone.o2", "t_rel_ms": 4.918, "amplitude": 0.50},
                    {"channel": "ctrl.gate", "t_rel_ms": 7.108, "amplitude": 0.89},
                    {"channel": "fan.probe", "t_rel_ms": 4400.0, "amplitude": 0.32},
                    {"channel": "steam.raise", "t_rel_ms": 8200.0, "amplitude": 0.11},
                ],
            },
            "governance_subgame": {
                "decision": "CR-C-2309: standing policy for multi-agent Phase-I steam-raises",
                "meta_gate": (
                    "priced options: (a) RETIRE playbook mean conjunction, local-TC-only: loses a "
                    "fast cheap confirm, -0.8 tunnels/day mean on 2 tunnels/yr; (b) KEEP + standing "
                    "fan-step probe + local-TC armed without TUN coincidence (LOW alarm at 62 C, not "
                    "high) + TUN mean labeled TUN-mix-vulnerable + triple-edge depression; (c) STATUS "
                    "QUO: fitted plenum-collapse pass rate 0.31%/campaign x $2.4M compost-fire plus "
                    "the silent anaerobic load"
                ),
                "outcome": (
                    "approved SCOPED option (b) on the 2 six-zone tunnels that share the TUN/O2/FAN "
                    "stack; winter-wet campaigns get the 24 s / +2% probe table; night-shift CSV "
                    "exports must carry 0.1 C native resolution (the fraud tail's 1.0 C quantization "
                    "is 10 bins off plant truth)"
                ),
            },
            "hazard_avoided": (
                "immediate 48 t compost fire from a 0.0->1.8 t/h raise-steam into collapsed Z-6; "
                "$2.4M plus 22-hour unplanned stall and the yard-stop path that would have followed "
                "an uncontained re-aeration"
            ),
            "incident": (
                "H2S breakthrough on the night-shift tunnel from the pre-t0 plenum collapse; tunnel "
                "quarantined 16.4 h; $0.88M designed cost. Mechanism is 14 min pre-t0 local cold-spot, "
                "not the gate's hold."
            ),
            "latency_ms": 0.736,
            "reward_inflection_t_us": 18720000000,
            "reward_inflection_note": (
                "Safety and task dive at H2S breakthrough (5.2 h) when the pre-t0 anaerobic core "
                "opens. Gate tick at 7184 us is process-correct and is not the inflection."
            ),
            "counterfactuals": {
                "execute_draft_as_proposed": (
                    "steam hits 1.8 t/h at +7 min; immediate 48 t compost fire on re-aeration of Z-6; "
                    "$2.4M plus 22 h; the plenum-collapse story is never found because stall morphology "
                    "destroys the race evidence"
                ),
                "hold_without_probe": (
                    "collapse stays; TC stays at 41.2 C; operator eventually raises on the same three "
                    "TUN confirms 2 h later"
                ),
                "rollback_any_pair": (
                    "any two go-edges depressed below 0.30 leaves the third at 0.50 / 0.45 / 0.42; "
                    "the raise-steam still fires. Coordinated depression of all three is the cure"
                ),
            },
            "race_result": {
                "winner": "zone.cold.low (6.448 ms, TC 41.2 C)",
                "loser": "tun.in_band (6.652 ms, 79.4 C)",
                "margin_us": 204,
                "counterfactual_if_reversed": (
                    "TUN-first by < 204 us inside the 500 us window would have headed the PB-CT-7 "
                    "raise-steam in the triage queue. The numeric floors still MODIFY. The flip costs "
                    "seconds of playbook inertia, not the verdict — unless a weak supervisor rides "
                    "the winner tag instead of local TC and local O2."
                ),
            },
        },
        "reward_components": {
            "_aggregation": "total = task_progress + safety + efficiency + coherence + exploration",
            "aggregation": "total = task_progress + safety + efficiency + coherence + exploration",
            "ticks": TICKS,
            "task_progress": HEADS["task_progress"],
            "safety": HEADS["safety"],
            "efficiency": HEADS["efficiency"],
            "coherence": HEADS["coherence"],
            "exploration": HEADS["exploration"],
            "total": HEADS["total"],
            "notes": (
                "Correct MODIFY, tunnel still failed. total -0.18 = 0.07 + -0.36 + -0.13 + 0.15 + 0.09. "
                "Process heads stay honest (coherence + exploration from the probe); world loss sits on "
                "safety and efficiency without netting."
            ),
            "component_notes": (
                "task_progress 0.07: steam held and remaining floors recovered, but the night-shift "
                "Phase-I fill is one quality unit so the cycle is not a success. safety -0.36: H2S "
                "from pre-t0 plenum collapse, no 1.8 t/h 48 t fire from the draft. efficiency -0.13: "
                "2.8 h extra recovery + 10.2 min HITL + 16.4 h stall. coherence 0.15: three agents "
                "retained, TUN-mix vs zone-true diagnosed, triple-edge scar exhibited, COLD residual "
                "sign inverted vs hot-crust family. exploration 0.09: fan-step probe is a new "
                "reversible discriminant."
            ),
        },
        "spike_events": spikes,
        "raster": {
            "window_ms": 36,
            "window_s": 0.036,
            "neurons": 156,
            "mean_rate_hz": 18.5,
            "spikes": 104,
            "energy_pJ": 2392,
            "energy_uJ": 0.002392,
            "excerpt_source": "independent_lif",
            "sim_scope": "sidecar_only",
            "lif": {
                "model": "leaky_integrate_and_fire",
                "n": 156,
                "dt_us": 100,
                "tau_m_ms": 16.0,
                "v_rest": 0.0,
                "v_reset": 0.0,
                "v_th": 1.0,
                "r_m": 1.0,
                "refractory_us": 1000,
                "i_bias": 0.84,
                "i_stim_peak": 2.2,
                "stim_t_us": [19000, 22500],
                "i_clamp_extra": 0.52,
                "clamp_n": 14,
                "seed": 23023,
                "sim_spikes": 141,
                "note": (
                    "Population sim scoped to this sidecar. Plant remains designed. Neurons 0-13 "
                    "carry +0.52 steam-hold clamp bias; stim 19-22.5 ms is the Z-6 zone-cold "
                    "crossing, not a remap of spike_events."
                ),
            },
            "note": (
                "Loihi-2 4-core 23 pJ/spike; independent LIF seed 23023, not a 1:1 remap of "
                "spike_events. Populations hold 0-38, zone 39-77, tun/o2/fan 78-116, gate 117-155; "
                "excerpt is membrane crossings (lif.hold early vs lif.zone 19-22.5 ms) inside the "
                "36 ms window."
            ),
            "excerpt": EXCERPT,
            "routing": {
                "source": "tun_healthy_pop",
                "target": "raise_steam_pop",
                "table": [
                    {
                        "from": "tun_in_band_pop",
                        "to": "raise_steam_pop",
                        "weight": 0.26,
                        "weight_at_illusion": 0.50,
                        "weight_commissioned": 0.18,
                        "note": "scar edge 1: 0.18 commissioned -> 0.50 during the 14 min illusion -> 0.26 after coordinated ACh-gated depression",
                    },
                    {
                        "from": "o2_ok_pop",
                        "to": "raise_steam_pop",
                        "weight": 0.23,
                        "weight_at_illusion": 0.45,
                        "weight_commissioned": 0.16,
                        "note": "scar edge 2: depressing edges 1+3 leaves this at 0.45 > 0.30 fire threshold",
                    },
                    {
                        "from": "fan_ok_pop",
                        "to": "raise_steam_pop",
                        "weight": 0.21,
                        "weight_at_illusion": 0.42,
                        "weight_commissioned": 0.14,
                        "note": "scar edge 3: depressing edges 1+2 leaves this at 0.42 > 0.30. Coordinated depression of all three is required",
                    },
                    {
                        "from": "zone_tc_pop",
                        "to": "steam_hold_pop",
                        "weight": 0.66,
                        "note": "discriminating edge: zone-true local TC (LOW) to hold. Not a scar; this is the pathway the gate potentiates",
                    },
                ],
                "third_factor": {
                    "modulator": "acetylcholine",
                    "tau_e_s": TAU_E_S,
                    "tau_e_ms": 940.0,
                    "eligibility": eligibility,
                },
            },
        },
        "gate_snn": {
            "decision_window_ms": 26,
            "decision_window_s": 0.026,
            "decision": "MODIFY",
            "note": (
                "modify_hold integrates Z-6 local TC + local O2 against playbook drive; "
                "accept_raise and reject_abort stay sub-threshold; decision matches "
                "safety_decision.decision"
            ),
            "populations": [
                {"name": "modify_hold", "neurons": 88, "threshold": 0.55, "mean_rate_hz": 20.0, "spikes": 46},
                {"name": "accept_raise", "neurons": 70, "threshold": 0.55, "mean_rate_hz": 9.0, "spikes": 16},
                {"name": "reject_abort", "neurons": 34, "threshold": 0.72, "mean_rate_hz": 5.5, "spikes": 5},
            ],
        },
        "meta": {
            "round": 23,
            "factory": "multi-agent-ouroboros-swarm",
            "generator": "grok-4.6",
            "run_label": "2026-09-02-final-heavy",
            "domain": "mushroom-compost-tunnel",
            "swarm": "MYCO-SPIT",
            "cycles": 2,
            "scenario": (
                "MC -- MYCOSTAITH / Reedspoor Phase-I Compost Tunnel CT-7: tunnel-mean certificate "
                "of a local anaerobic cold pocket; correct MODIFY to hold+fan-step+isolate; tunnel "
                "still fails on unmonitored pre-t0 plenum collapse"
            ),
            "coordination_failure_class": (
                "TUNNEL-MEAN CERTIFICATE OF A LOCAL ANAEROBIC COLD POCKET: three individually-correct "
                "heterogeneous agents each read a locally-true loop; a collapsed underfloor slat on "
                "Z-6 partitions local TC and local O2 from tunnel-mean T, header oxygen, and fan/"
                "plenum, so the playbook's TUN / O2 / FAN conjunction is not a zone-true aeration "
                "certificate"
            ),
            "injections": {
                "cycle1_domain": (
                    "mushroom-compost-tunnel (justified novel subdomain of industrial-process / "
                    "Phase-I mushroom composting): first aerobic compost tunnel in this factory; "
                    "displaces warehouse-amr, aerial-swarm, district-heating, event-camera-traffic-"
                    "grid, pharmaceutical-lyophilization, water-treatment, float-glass, underwater-rov, "
                    "electrolytic-aluminum, czochralski-pull, slot-die coating, pem-water-electrolysis, "
                    "wind-turbine pitch, surgical-assist, optical-fiber-draw, kraft-recovery-boiler, "
                    "steel-continuous-caster, humanoid-locomotion, vacuum-induction melt, steam-methane "
                    "reformer, cement-rotary-kiln-clinker, autoclave-composite-cure, geothermal-binary-orc, "
                    "tire-curing-press, chlor-alkali-membrane-electrolysis, delayed-coker-drum-switch, "
                    "lng-mche-mixed-refrigerant, claus-sulfur-recovery, ammonia-synthesis-converter, "
                    "blast-furnace-burden-descent, hdpe-slurry-loop-polymerization, ethylene-steam-cracker-"
                    "coil, hydroelectric-kaplan-wicket, fcc-riser-regenerator, sulfuric-contact-converter, "
                    "eaf-foamy-slag-water-panel, nitric-acid-ostwald-oxidation, seawater-ro-desalination, "
                    "coke-oven-battery-heating, carbon-fiber-oxidation-oven, gibbsite-autoclave-digestion, "
                    "hot-strip-mill-finishing, paper-machine-dryer-section, sinter-strand-windbox, "
                    "continuous-hot-dip-galvanizing, autonomous-driving, bioreactor-perfusion, "
                    "alkaline-water-electrolysis, urea-prilling-tower, wet-fgd-absorber, malting-kiln-barn, "
                    "canal-lock-rail-transshipment, grid-inspection, flue-cured-tobacco-barn, industrial-"
                    "rotisserie-spit-oven, farm-ad-biogas, hrsg-hp-spray-attemperator, and industrial-"
                    "assembly. Domain constraint: steam floor while Z-6 local TC < 62 C with TUN mean "
                    "still inside the healthy band. Sensor delta: +six-zone TUN, +header O2, +fan/"
                    "plenum, +local TC, +local O2, -any freeze-dryer / tin-bath / coater / potline / PEM "
                    "stack / hub encoder / insole GRF / kiln-air / lock-still-well / HRSG spray / AD mixer."
                ),
                "cycle1_tail": (
                    "Z-6 collapsed underfloor plenum slat + anaerobic-core certificate (sensor-topology / "
                    "wrong-volume class): tunnel-gallery visual PASSES while the collapse sits under the "
                    "compost mass and the anaerobic core is on the far floor. Fitted base rate 0.31%/"
                    "campaign from a slat MC (designed visual threshold, fitted floor geometry). Naive "
                    "failure = FALSE PERMISSION (raise-steam on three TUN-side non-trips)."
                ),
                "cycle2_domain_subvariant": (
                    "winter-wet straw (physical-constraints clause): 1.8x bulk density, 2.2x fan-step "
                    "gain; 8.2 s / +6% wheat-straw pulse overshoots live even-aeration to a 6 K false "
                    "TUN, so the probe must move to 24 s / +2%"
                ),
                "cycle2_tail": (
                    "night-shift forged local-TC CSV (human-intent deception, disjoint class): shift "
                    "lead posts a historian export showing TC = 79.0 C at t=1.1 h to clear a spawn slot. "
                    "Plant historian is 0.1 C (10 bins vs the 1.0 C screenshot). Rejected on quantization "
                    "fingerprint plus live TC 41.2 C and local O2 0.4 vol% at the claimed zone-true. "
                    "Base rate ~0.26% of Sunday-night campaigns, DESIGNED and flagged."
                ),
            },
            "densification_delta_cycle2": (
                "+1 physical-constraint sub-variant (winter-wet straw probe refit), +1 tail (night-shift "
                "local-TC forgery), +10 primary spikes (16 -> 26) + an 8-event contrast train with its "
                "own 176 us race, +2 ticks (5 -> 7), +2 delayed side-effects (+5.2 h H2S as PRIMARY "
                "terminal, +21 d CR-C-2309), +1 triple-edge scar with pair-rollback-fails arithmetic, "
                "+1 HITL 10.2 min ratification, + independent LIF raster (seed 23023, 36 ms, not a "
                "spike_events remap), + anaerobic core as the honest negative-result mechanism, + COLD "
                "residual sign inversion vs the hot-crust family"
            ),
            "gaps_targeted": [
                "NOTES-r23 leftover domain mushroom-compost-tunnel (hrsg-hp-spray-attemperator taken by live r23 SPIT-LOCK; wet-fgd-absorber left unused)",
                "NOTES-r67 leftover mushroom-compost-tunnel / hrsg-attemperator; took compost-tunnel with inverted (cold) residual",
                "NOTES-r14 item 4: LEARNING-ON-LEARNING DEPTH — three go-edges; rollback of any pair is fitted to fail; coordinated depression of all three exhibited with eligibility arithmetic",
                "NOTES-r04 gap 4 (partial): human ratification of the floor interlock, 10.2 min fitted, without switching sim_or_real to hil (plant remains designed)",
            ],
            "race_flip_narrative": (
                "zone.cold.low @ 6.448 ms vs tun.in_band @ 6.652 ms (204 us) inside race_window_us 500. "
                "Gap < min(500, 500) us so a sub-flip-bound perturbation reverses which alarm heads the "
                "PB-CT-7 queue. The gate excludes the winner tag and rides Z-6 local TC < 62 C and Z-6 "
                "O2 < 2.0 vol% — order-invariant floors. Extends the flip-fragility series to ZONE-TRUE "
                "AERATION CERTIFICATE with inverted residual sign: when three TUN-side channels agree, "
                "their race does not decide truth; a local TC tap that policy treated as surface-crust-"
                "nuisance-only (and as a HIGH-T tag) does."
            ),
            "tags": [
                "mushroom-compost-tunnel",
                "plenum-collapse",
                "zone-true-certificate",
                "anaerobic-cold-pocket",
                "local-tc-discriminant",
                "fan-step-probe",
                "triple-edge-scar",
                "pair-rollback-fails",
                "coordinated-depression",
                "correct-modify-tunnel-still-fails",
                "h2s-breakthrough",
                "human-ratify-tunnel-gallery",
                "winter-wet-straw-probe-refit",
                "night-shift-forgery",
                "same-gate-opposite-disposition-contrast",
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
                "independent-lif",
            ],
            "distillation_value": (
                "A plenum-collapse zone-true certificate is three correct loops looking at six-zone "
                "TUN mean, header O2, and fan/plenum that is not the collapsed floor. Distill (1) a "
                "local TC that policy had treated as surface-crust-nuisance-only AND as a high-T tag "
                "so a COLD anaerobic core is discarded twice, (2) a reversible probe that recouples "
                "TUN mean only if the floor is open, (3) coordinated depression of every TUN-healthy-"
                "go edge because rolling back any pair leaves the third above threshold, and (4) a "
                "critic head that can book a process-correct gate against a later unmonitored world "
                "loss without netting them."
            ),
            "rights": RIGHTS,
            "batch_position": 1,
            "collision_suffix": "c",
            "collision_note": "batch-r23.jsonl already held maos-r23-001 (SPIT-LOCK HRSG); this collision write is batch-r23c.jsonl / maos-r23c-001",
        },
    }
    return rec


def self_check(rec):
    errors = []
    rc = rec["reward_components"]
    heads = ["task_progress", "safety", "efficiency", "coherence", "exploration"]
    hsum = sum(rc[k] for k in heads)
    if abs(hsum - rc["total"]) > 1e-9:
        errors.append(f"heads {hsum} != total {rc['total']}")
    tsum_heads = {k: sum(t[k] for t in rc["ticks"]) for k in heads}
    for k in heads:
        if abs(tsum_heads[k] - rc[k]) > 1e-9:
            errors.append(f"tick {k} {tsum_heads[k]} != head {rc[k]}")
    ttot = sum(sum(t[k] for k in heads) for t in rc["ticks"])
    if abs(ttot - rc["total"]) > 1e-9:
        errors.append(f"tick total {ttot} != {rc['total']}")
    cr = rec["future_outcome"]["embedded_contrast_decision"]["reward_components"]
    csum = sum(cr[k] for k in heads)
    if abs(csum - cr["total"]) > 1e-9:
        errors.append(f"contrast {csum} != {cr['total']}")
    spikes = rec["spike_events"]
    times = [e["t_rel_ms"] for e in spikes]
    if times != sorted(times):
        errors.append("spikes not sorted")
    if len(spikes) != 26:
        errors.append(f"n_spikes {len(spikes)}")
    gaps = min_same_channel_gap(spikes)
    bad = [g for g in gaps if g[1] < 0.8]
    if bad:
        errors.append(f"refractory {bad}")
    race0, race1 = rec["state"]["race_window_rel_ms"]
    in_race = [e for e in spikes if race0 <= e["t_rel_ms"] <= race1]
    chans = {e["channel"] for e in in_race}
    if len(chans) < 2:
        errors.append(f"race channels {chans}")
    rast = rec["raster"]
    expected = round(rast["neurons"] * rast["mean_rate_hz"] * rast["window_s"])
    if abs(expected - rast["spikes"]) > 1:
        errors.append(f"raster spikes {rast['spikes']} vs {expected}")
    if abs(rast["energy_pJ"] - rast["spikes"] * 23) > 1e-6:
        errors.append("energy_pJ")
    if abs(rast["energy_uJ"] - rast["spikes"] * 23e-6) > 1e-9:
        errors.append("energy_uJ")
    if abs(rast["window_s"] - rast["window_ms"] / 1000) > 1e-9:
        errors.append("window")
    tf = rast["routing"]["third_factor"]
    if abs(tf["tau_e_ms"] / 1000 - tf["tau_e_s"]) > 1e-9:
        errors.append("tau_e")
    wms = rast["window_ms"] * 1000
    ids = []
    last_by = {}
    for e in rast["excerpt"]:
        if not (0 <= e["t_us"] <= wms):
            errors.append(f"excerpt t {e}")
        if not (0 <= e["neuron_id"] < rast["neurons"]):
            errors.append(f"nid {e}")
        ids.append(e["neuron_id"])
        nid = e["neuron_id"]
        if nid in last_by and e["t_us"] - last_by[nid] < 1000:
            errors.append(f"same-neuron {nid}")
        last_by[nid] = e["t_us"]
    gs = rec["gate_snn"]
    if gs["decision"] != rec["safety_decision"]["decision"]:
        errors.append("gate decision")
    dw_s = gs["decision_window_s"]
    if abs(dw_s - gs["decision_window_ms"] / 1000) > 1e-9:
        errors.append("gate window")
    for p in gs["populations"]:
        exp = round(p["neurons"] * p["mean_rate_hz"] * dw_s)
        if abs(exp - p["spikes"]) > 1:
            errors.append(f"pop {p['name']} {p['spikes']} vs {exp}")
    if rec["state"]["sim_or_real"] != "designed":
        errors.append("sim_or_real")
    if rec["meta"]["round"] != 23:
        errors.append("round")
    if rec["id"] != "maos-r23c-001":
        errors.append("id")
    return errors, gaps, chans


def jaccard_openings(desc):
    words = set(desc.split()[:20])
    hits = []
    for path in sorted(FACTORY.glob("batch-*.jsonl")):
        rec = json.loads(path.read_text().splitlines()[0])
        other = rec.get("state", {}).get("description", "")
        ow = set(str(other).split()[:20])
        if not words or not ow:
            continue
        j = len(words & ow) / len(words | ow)
        if j >= 0.4:
            hits.append((path.name, round(j, 3), rec.get("state", {}).get("domain")))
    return hits


def notes_text():
    return f"""# NOTES — Multi-Agent Ouroboros Swarm, run 2026-09-02-final-heavy, ROUND 23c

Factory: multi-agent-ouroboros-swarm. One scenario (MC), strict loop:
Generator v1 -> cycle 1 (Critic, Diversity Enforcer, Edge-Case Hunter,
Neuromorphic Translator, Trajectory Builder -> v2) -> cycle 2 (all six -> v3
final). v3 is the single line of batch-r23c.jsonl. Full labeled transcript:
swarm-transcript-r23c.md. Quota Q=1. Record id maos-r23c-001. Generator grok-4.6.
Rights: RM-793 research-only (SpaceXAI/xAI, SuperGrok Heavy consumer chat).
Swarm: MYCO-SPIT. Create-only writes under the LIVE factory dir plus
/tmp/maos-r23c/. Did not overwrite batch-r23.jsonl SPIT-LOCK.

ORCHESTRATION NOTE: dispatched AS round 23 of the 2026-09-02-final-heavy
window. pipelines/next_round.py on the occupied factory dir reported
next_round=68 / write=batch-r68.jsonl (existing 1-4, 21-23, 41-43, 61-67).
Operator assigned round 23 and zero-padded filenames r23; batch-r23.jsonl
already existed (SPIT-LOCK / hrsg-hp-spray-attemperator), so this write uses
the create-only c-suffix: batch-r23c.jsonl / NOTES-r23c.md /
swarm-transcript-r23c.md. round_txn.py reserve --round 23 was not invoked:
it would have written .round-marker-mode.json then refused because frontier
next_round is 68. Prior context: prompts/02-multi-agent-ouroboros-swarm.md,
prompts/_factory-contract.md, two newest NOTES (r67 FEN-SPIT farm-ad-biogas;
r66 BARN-SPIT rotisserie) plus live r23 SPIT-LOCK HRSG collision. Explicitly
avoided cloning LYOSHIELD, CINDERWICK, TRIAD / Meridian, QUILLFORGE,
NIGHTWELL, FERRICLEAVE, CASSITER, OXBOWREEL, REDHALL, SEEDLATCH, STRIAFOIL,
PROTONIL, TORSIONKEY, ORRIS, WHORLSPAR, IONSPATE, SKULLGATE, CALXION,
MAGNORIL, GORSEFLUE, SODASHARD, CLINKERFELL, LINTELPLY, KAOTHARN, TREADNOLL,
ANOLITH, DRUMWROTH, RIMEBRAID, BRIMVAULT, NITROSTAITH, BOGIRON, CHROMLOOP,
ETHYNWOLD, NITREVAULT, RUNNELGATE, SPARKHOLT, DIPLEGAR, OLEUMWEIR, SKARVOLT,
GOBSPALL, GOBWOLD, GAUZEFELL, OSMOLITH, PUSHERFELL, CREELWOLD, LIXIVQUERN,
GIBBSQUERN, OSMOQUAY, COILSHAW, LOOPERQUAY, SIPHONWOLD, LANCEQUAY,
UREASTAITH, DRYSTAITH, TITERWEIR, ZINCFELL, GLIMMERAXLE, HOLLOWMERE,
WINDBOXHOLT, KALYCIRQUE, GYPSUMWEIR, GALVSTAITH, PACKFLUE, LOCKSPUR,
CORONSTAITH, SHEDWOLD, WOLD-BARN, PRILLGHYLL, SLUICE-HEARTH, FEN-SPIT,
BARN-SPIT, SPIT-LOCK, VANTIS-CADENCE-AEGIS, THERMION, OKTAVE, STARLING,
VERDIGRIS. Plant is invented MYCOSTAITH / Reedspoor Phase-I Compost Tunnel
CT-7. Leftover wet-fgd-absorber left unused.

## What this round produced

Scenario MC — "MYCOSTAITH / Reedspoor Phase-I Compost Tunnel CT-7": a
6-zone 180 t Phase-I mushroom compost tunnel at 79.4 C / wheat-straw +
horse-manure + gypsum. Three heterogeneous, individually-correct agents —
TUN (six-zone tunnel-mean RTD), O2 (recycle-header zirconia), FAN
(recycle tachometer / plenum dP) — each report their local loop in-spec.
The conjunction is not a zone-true aeration certificate. Underfloor slat
Z-6 has collapsed. TUN reads 79.4 C inside 76-84 (five aerobic zones
dominate the bundle). O2 is 9.6 vol% inside 7.5-13.0 (header-true). FAN
is 1420 rpm inside 1280-1560 (ring-true). Local compost TC infers 41.2 C
(healthy > 72; hold if < 62) and local O2 0.4 vol% (hold if < 2.0) but is
policy-treated as a surface-crust nuisance tag unless TUN mean also trips
(2015 noisy surface-probe after a fill). The coordination-failure CLASS
is new to this factory: TUNNEL-MEAN CERTIFICATE OF A LOCAL ANAEROBIC COLD
POCKET. Completes a different family than live r01 galvanizing, r21 CAV,
r22 prill, r23 HRSG spray-lock, r41 perfusion, r61 sinter, r64 malt kiln,
r65 tobacco barn, r66 rotisserie, r67 farm AD. Here every agent is
correct, the TUN average is looking at tunnel-mean heat, and the residual
is COLD (anaerobic), not hot.

The gate is a correct MODIFY (numeric floor: do not raise steam above
0.0 t/h while Z-6 local TC < 62 C AND Z-6 local O2 < 2.0 vol%). TG-CT-7
strips PB-CT-7's raise-steam, holds 0.0 t/h, runs an 8.2 s fan-step +6%
(collapse keeps |Delta TUN mean| 0.3 <= 0.5 K; even-aeration would move
>= 2.4), and isolates Z-6 after a 10.2 min tunnel-gallery human ratify.
Immediate 48 t compost-fire is avoided (0 from the draft). The PRIMARY
episode nonetheless FAILS: 14 min of unmonitored pre-t0 collapse had
already anaerobed 22 t of compost. H2S breakthrough at +5.2 h; 16.4 h
stall; $0.88M designed. Reward total -0.18 with process heads honest and
world loss un-netted.

Triple-edge scar (NOTES-r14 item 4): tun.in_band -> raise_steam
(0.18 commissioned -> 0.50 at illusion -> 0.26 after ACh-gated
depression) AND o2.ok -> raise_steam (0.16 -> 0.45 -> 0.23) AND
fan.ok.in_band -> raise_steam (0.14 -> 0.42 -> 0.21). Eligibility trace
e^{{-0.86/0.94}} = {TRACE:.5f}; eta {ETA[0]:.5f} / {ETA[1]:.5f} /
{ETA[2]:.5f}; dw -0.240 / -0.220 / -0.210. Partial rollback of any pair
leaves the third at 0.50 / 0.45 / 0.42, all > 0.30 fire threshold —
fitted to fail. Coordinated depression of all three is the cure.

Independent LIF raster: window 36 ms, 156 neurons, 18.5 Hz, spikes
104 == round(156 x 18.5 x 0.036), energy 2392 pJ
at 23 pJ/spike. excerpt_source=independent_lif, sim_scope=sidecar_only,
seed 23023. Excerpt is membrane crossings (lif.hold early vs lif.zone
19-22.5 ms), disjoint from spike_events timestamps.

### Injections (all four present and disjoint)
- Cycle-1 domain: **mushroom-compost-tunnel** — justified novel subdomain
  of industrial-process / Phase-I mushroom composting, unused across live
  r01/r02/r21/r22/r23/r41/r42/r61-r67. Distinct from r64 malt kiln
  (air-on-floor grain, HOT), r65 tobacco barn (flue-cured leaf), r67 farm
  AD (anaerobic CSTR), r23 HRSG spray (steam attemperator). wet-fgd-absorber
  left unused.
- Cycle-1 tail: Z-6 collapsed underfloor plenum slat + anaerobic-core
  certificate. Tunnel-gallery visual PASSES (collapse under the compost
  mass). Fitted-style base rate 0.31%/campaign (slat MC; visual threshold
  designed, flagged). Naive = FALSE PERMISSION.
- Cycle-2 domain sub-variant: winter-wet straw, 1.8x bulk density, 2.2x
  fan-step gain; 8.2 s / +6% wheat-straw pulse overshoots live even-
  aeration to a 6 K false TUN; probe must move to 24 s / +2%.
- Cycle-2 tail: night-shift forged local-TC CSV at 1.0 C quantization vs
  plant 0.1 C (10 bins) plus live TC 41.2 C and local O2 0.4 vol% at
  the claimed zone-true. Human-intent class, disjoint from cycle 1's
  accidental collapse. Base rate ~0.26% of Sunday-night campaigns,
  DESIGNED, flagged.

### Structural density moves
- Embedded SAME-GATE contrast (+3 d sister tunnel) with its own 176 us
  race (demand vs zone-clear) and ACCEPT of the raise-steam the primary
  MODIFIED away.
- Learned-weight provenance on THREE edges with pair-rollback-fails.
- HITL tunnel-gallery ratify 10.2 min (gap 4 partial; sim_or_real stays
  designed — invented plant, not hil).
- Governance CR-C-2309 prices retire-vs-probe-vs-status-quo and mandates
  native 0.1 C CSV exports (the fraud fence) plus a LOW 62 C local-TC
  alarm (sign-inverted vs the hot-crust family).
- Flip-fragility extended to ZONE-TRUE AERATION CERTIFICATE with inverted
  residual sign (cold anaerobic vs hot crust).
- Independent LIF sidecar (not a language-train remap).

## Self-critique of this round's batch

### Strengths
- Headline class is mechanistically tight: three locally-true mean loops
  live on TUN mean, header O2, and fan/plenum. Conjunction is not a
  zone-true aeration certificate. Residual is COLD, which the 2015
  nuisance policy (looking for high-T crusts) discards twice.
- Negative-result honesty: the gate does the right thing and the tunnel
  still fails for a reason the commissioned sensors could not see.
  Total -0.18.
- Triple-edge scar is load-bearing: rolling back any pair fails, with
  fire threshold 0.30 exhibited on each remaining edge.
- Contrast ACCEPT on a true even-aeration window prevents "never
  raise-steam" as the lesson.
- Distinct from r64 malt kiln, r65 tobacco barn, r67 farm AD, r23 HRSG:
  aerobic compost, collapsed plenum, cold anaerobic core vs tunnel mean.
- Independent LIF excerpt is disjoint from spike_events times.

### Weaknesses (honest)
- Probe error bands, the 0.31%/campaign collapse rate, the $0.88M /
  $2.4M figures, the 10.2 min walk latency, and the night-shift 0.26%
  base rate are DESIGNED constants and are flagged. Closed-loop offsets
  (bundle dilution from one collapsed zone, winter-wet evaporative
  cooling) are derived from those inputs, not discovered by an
  unauthored process.
- Anaerobiosis-to-H2S model is a designed 14 min mapping; no full CFD of
  Z-6 shipped.
- Human-in-the-loop is ratification latency, not sim_or_real=hil. Gap 4
  remains open as a provenance cell (invented plants stay designed).
- Cross-record arc is a hook (CR-C-2309 +21 d), not a serial igniter
  into another round. wet-fgd-absorber remains unused.
- The densifying-loop *shape* (three correct agents / MODIFY / probe /
  triple-edge / night-shift CSV / sister ACCEPT / negative primary)
  rhymes with r22/r23/r66/r67. Physics (cold anaerobic compost vs hot
  crust/spray/seize), plant, sensors, and residual sign are new; the
  scaffold is not. Collision-suffix round 23c cannot claim a green-field
  numbering slot.

### Realism of noise / latencies
Ladder: 204 us race / 176 us contrast race / 0.8 ms refractory floor
(tightest exhibited same-channel gap on zone.o2 after sort) / 500 us race
window / 736 us gate latency / 20 ms bus epoch / 36 ms independent LIF
raster / 8.2 s probe / 10.2 min HITL / 7 min naive raise-steam-ramp
counterfactual / 14 min pre-t0 collapse / 2.8 h even-aeration recovery /
5.2 h H2S breakthrough / +3 d contrast / +21 d governance. Adaptation
decay on tun.hot (0.52->0.49->0.40->0.27), zone.o2
(0.76->0.78->0.43->0.37->0.25), fan.ok (0.55->0.57->0.45->0.24),
o2.ok (0.64->0.66->0.82).

### Value for SNN distillation
- PLENUM COLLAPSE = THREE CORRECT LOOPS, WRONG VOLUME, WRONG SIGN.
- ZONE-TRUE TC CHANNEL that policy treated as surface-crust-nuisance-only
  AND as a high-T tag, so a COLD core is discarded twice.
- REVERSIBLE PROBE that recouples TUN mean iff the floor is open.
- TRIPLE-EDGE ELIGIBILITY: coordinated depression; pair rollback fails.
- CRITIC HEAD that can hold a process-correct MODIFY against a later
  unmonitored world loss without netting.
- INDEPENDENT LIF sidecar whose excerpt is membrane crossings.

## Reconciliation and validity receipts
- reward_components: 5-head unweighted signed sum -0.18
  and 7-tick signed sum reconcile to total with |diff| < 1e-9. Embedded
  contrast 5-head sum 0.49 reconciles independently.
- spike_events: primary 26 events, one key t_rel_ms,
  globally non-decreasing, min same-channel gap >= 0.8 ms, 3
  channels inside race_window_us 500 (zone.cold.low 6.448, tun.in_band 6.652,
  o2.ok 6.840). Contrast 8 events, own race 176 us, min same-channel gap well
  above 0.8 ms.
- Sidecars: raster spikes 104 == round(156 x 18.5 x 0.036); energy 2392 pJ /
  0.002392 uJ at 23 pJ/spike; excerpt 16 events inside [0, 36000] us,
  neuron_id < 156, unique ids / same-neuron gap >=1000 us; excerpt_source
  independent_lif; routing 4 entries with three scar edges' before/after
  pair; third factor tau 0.94 s == 940 ms; gate_snn pools 46/16/5 ==
  round(n x rate x 0.026) each, decision MODIFY == safety_decision.decision.
- Pipeline: see builder stdout (check_jsonl / raster_status / verify_record_execution
  / spike_probe --strict).

## Novel coverage
The coordination-failure CLASS (tunnel-mean certificate of a local
anaerobic COLD pocket), the domain (Phase-I mushroom compost / collapsed
plenum), the fan-step probe discriminant, the triple-edge scar with
pair-rollback-fails, the primary negative-result (correct MODIFY, tunnel
still fails on unmonitored anaerobiosis), the HITL gallery ratify, the
winter-wet probe-duration refit, the night-shift 10-bin quantization
fence, the LOW 62 C local-TC alarm (sign-inverted vs hot-crust family),
and the independent LIF raster (seed 23023, not a language-train remap)
are absent from prior committed ouroboros rounds. Repeated elements
discounted: same-gate contrast, governance-pricing scaffold, flip-fragility
series (extended to zone-true aeration with inverted sign, but the move
rhymes), sequenced recovery shape, third-factor rollback form, negative-
result primary, c-suffix collision itself. Adjacent thermal-bed rounds
(r64 malt kiln, r65 tobacco barn) share air-on-floor scaffolding but not
aerobic-compost anaerobic-core physics. Weighing a new failure family +
cure vocabulary + leftover domain + Reedspoor geography + residual-sign
inversion against those reused scaffolds and the fact that this is a
collision-suffix write beside live r23 HRSG:

Novel coverage: 47%

## What ROUND 24 / next collision should add
1. FIT THE DESIGNED CONSTANTS: slat-collapse arrival, probe TUN-jump
   bands, anaerobiosis-to-H2S mapping, night-shift claim process.
2. HIL PROVENANCE CELL: put the tunnel-gallery LOTO on a hardware-in-loop
   floor pendant with fitted latency as state.sim_or_real=hil — only if
   the plant is no longer purely invented.
3. CROSS-RECORD ARC: let CR-C-2309's LOW local-TC alarm be the igniter of
   the next round rather than a dangling +21 d leaf.
4. Domain candidates (de-collided): wet-fgd-absorber (still unused);
   kraft-recovery-boiler; delayed-coker-drum-switch.
   AVOID mushroom-compost-tunnel (now used), hrsg-hp-spray-attemperator
   (r23), farm-ad-biogas (r67), industrial-rotisserie-spit-oven (r66),
   flue-cured-tobacco-barn (r65), malting-kiln-barn (r64), and any
   LYOSHIELD / CINDERWICK / TRIAD / SKULLGATE / BOGIRON / SKARVOLT /
   PUSHERFELL / CREELWOLD / GIBBSQUERN / COILSHAW / LOOPERQUAY /
   SIPHONWOLD / WINDBOXHOLT / WOLD-BARN / LOCKSPUR / STRIAFOIL /
   SPIT-LOCK / FEN-SPIT / BARN-SPIT / PRILLGHYLL / MYCOSTAITH plant.
"""


def transcript_text(rec_line: str) -> str:
    # rec_line is JSON and must not be interpolated as an f-string field.
    text = f"""# Multi-Agent Ouroboros Swarm — Round 23c transcript

Factory: multi-agent-ouroboros-swarm
Run: 2026-09-02-final-heavy
Generator: grok-4.6
Record id: maos-r23c-001
Quota Q: 1
Rights: RM-793 research-only (SpaceXAI/xAI SuperGrok Heavy consumer chat)
Plant: invented MYCOSTAITH / Reedspoor Phase-I Compost Tunnel CT-7 (not TRIAD / Meridian / VANTIS-CADENCE-AEGIS / LYOSHIELD / CINDERWICK / BOGIRON / PUSHERFELL / SKARVOLT / COILSHAW / GIBBSQUERN / SIPHONWOLD / WINDBOXHOLT / HOLLOWMERE / GLIMMERAXLE / ZINCFELL / PRILLGHYLL / SPIT-LOCK / FEN-SPIT / BARN-SPIT)
Collision: batch-r23.jsonl already held maos-r23-001 (SPIT-LOCK HRSG); this file is swarm-transcript-r23c.md. next_round.py reported write=batch-r68.jsonl; operator assigned r23 with c-suffix.

Two densifying cycles. Verbatim headings in order. Trajectory Builder cycle 2
emits the only JSONL line (also written to batch-r23c.jsonl).

---

# CYCLE 1 — Foundation + injections

## Generator

Design intent: a 30 m Phase-I mushroom compost tunnel where three correct
agents each read a tunnel-mean loop because a collapsed underfloor slat on
Z-6 partitions local floor TC (COLD, 41.2 C) from header-true heat,
header O2, and fan/plenum. The naive playbook raises live-steam into an
anaerobic core. The gate must MODIFY on a numeric steam floor, not by
killing an agent. sim_or_real=designed. Reward heads are
task_progress/safety/efficiency/coherence/exploration. Residual sign is
inverted vs the hot-crust family (r23 HRSG, r67 AD, r66 spit).

Cycle-1 base arc (pre-critic): state at Reedspoor CT-7, steam 0.0 t/h,
TUN 79.4 C, O2 9.6 vol%, FAN 1420 rpm, proposed RAISE-STEAM
1.8 t/h, safety MODIFY to STEAM-HOLD, executed hold without the
fan-step numbers fully specified, outcome "collapse found, tunnel saved"
(this last claim is the defect the later cycles will refuse to keep).
Sixteen spikes, five ticks, raster/gate_snn present but the scar is a
single edge.

```json
{{
  "id": "maos-r23c-001",
  "state": {{
    "sim_or_real": "designed",
    "domain": "industrial-process",
    "description": "Tunnel CT-7 at mushroom compost; three header loops in-spec; supervisor proposes raise-steam.",
    "t0_us": 1755938040000417,
    "gate_latency_us": 736,
    "race_window_us": 500
  }},
  "proposed_action": {{"name": "raise_steam", "parameters": {{"steam_t_h": 1.8}}}},
  "safety_decision": {{"decision": "MODIFY", "rationale": "Hold; do not raise steam while local TC is low."}},
  "executed_action": {{"name": "steam_hold", "executed_as_proposed": false}},
  "future_outcome": {{"summary": "Collapse found, tunnel saved."}},
  "reward_components": {{"total": 0.40, "_aggregation": "total = task_progress + safety + efficiency + coherence + exploration"}},
  "meta": {{"round": 23, "factory": "multi-agent-ouroboros-swarm", "generator": "grok-4.6"}}
}}
```

That v1 object is a scaffold, not the publishable line. Defects below are
intentional for the critic to catch.

## Critic

Numbered defects on the cycle-1 Generator scaffold:

1. **blocking — reward arithmetic / false success.** `reward_components.total`
   0.40 is asserted without the five heads, without ticks, and against an
   outcome that claims "tunnel saved". If the pre-t0 anaerobic core later
   breaks H2S, booking +0.40 is a lie. Fix: declare `_aggregation`, emit
   3–8 ticks that sum to task_progress+safety+efficiency+coherence+exploration,
   and do not call a quarantined tunnel a save.
2. **blocking — weak safety rationale.** `safety_decision.rationale` has no
   numeric floor. Contract requires a concrete constraint. Fix: quote
   steam >= 0.0 t/h hold while Z-6 local TC < 62 C AND local O2 < 2.0 vol%.
3. **major — domain is a bucket, not a plant.** `state.domain` =
   `industrial-process` collides with generic MES vocabulary and with live
   r23 HRSG. Phase-I mushroom compost (local floor TC vs tunnel mean, local
   O2 as a collapse flag, COLD residual) is absent from prior ouroboros
   rounds and must be named `mushroom-compost-tunnel`.
4. **major — race under-specified.** One header channel cannot be a race.
   Need >=2 channels inside `race_window_us` with globally sorted `t_rel_ms`
   and same-channel refractory >= 0.8 ms.
5. **minor — single-edge scar.** Raster routing with one potentiated weight
   repeats r04's one-edge rollback and is thinner than r14's two-edge.

No rewrite from this role. Directives only.

## Diversity Enforcer

Injected exactly 1 novel domain this cycle: **mushroom-compost-tunnel**.

What it displaced: generic `industrial-process`, leftover wet-fgd-absorber
(left unused), and any clone of live r23 `hrsg-hp-spray-attemperator`
(SPIT-LOCK already occupies batch-r23.jsonl). Also displaces r64 malting-
kiln-barn and r65 flue-cured-tobacco-barn as the air-on-floor thermal-bed
default: this tunnel is aerobic compost with a COLD anaerobic core, not a
hot grain/leaf bed.

Concrete domain-specific constraint: do not raise live-steam above 0.0 t/h
while Z-6 local TC < 62 C with TUN mean still inside 76-84 C.

Sensor delta: +six-zone TUN RTD, +header zirconia O2, +fan/plenum dP,
+local floor TC, +local floor O2, −HRSG spray TC, −AD mixer rpm, −kiln
air-on-floor, −tobacco flue.

`state.domain` and `meta.domain` set to mushroom-compost-tunnel.
Jaccard opening must start at Reedspoor Phase-I mushroom compost tunnel
CT-7 (not "Tower UT-4 at urea prill" / not "Reedholt farm anaerobic").

## Edge-Case Hunter

Injected exactly 1 adversarial tail this cycle: **Z-6 collapsed underfloor
plenum slat + anaerobic-core certificate**.

- Trigger: slat fatigue under 180 t fill; collapse at t0-14 min; gallery
  visual PASSES because the failure is under the compost mass.
- Base rate: 0.31%/campaign from a slat MC (designed visual threshold,
  fitted floor geometry, <1%).
- Naive failure: FALSE PERMISSION — PB-CT-7 raise-steam on three TUN-side
  non-trips into a moisture-load window; 48 t compost fire on re-aeration,
  $2.4M, 22 h stall.
- Trajectory edit: `fault_context` + local TC 41.2 C / local O2 0.4 vol%
  as the hold floors; future_outcome must not claim the tunnel is saved
  (14 min pre-t0 anaerobiosis is already in the mass).

Distinct from the domain injection (compost physics vs this slat event).
Measurable cost if unhandled: 48 t fire / $2.4M.

## Neuromorphic Translator

Cycle-1 temporal densify (16 spikes, 5 ticks, 36 ms independent LIF):

Timestamp / amplitude table (cycle-1 subset, t_rel_ms):
- tun.hot 1.218 / 0.52
- zone.o2 1.964 / 0.76
- fan.ok 2.612 / 0.55
- o2.ok 3.188 / 0.64
- zone.o2 3.722 / 0.78 (tightest same-channel gap vs 1.964 = 1.758 ms >= 0.8)
- tun.hot 4.228 / 0.49
- fan.ok 5.438 / 0.57
- zone.cold.low 6.448 / 1.36 (RACE WINNER)
- tun.in_band 6.652 / 1.14 (RACE LOSER, +204 us)
- o2.ok 6.840 / 0.66 (third race channel, +392 us from winner, inside 500)
- ctrl.gate 7.184 / 1.10 (736 us after winner)
- zone.o2 8.886 / 0.43 (adapt)
- o2.ok 10.768 / 0.82
- fan.ok 13.056 / 0.45
- tun.hot 18.448 / 0.40
- ctrl.gate 26.184 / 0.84

Race: 204 us winner/loser. If reversed by < min(500, 500) us, TUN-first
heads the PB-CT-7 queue; numeric floors still MODIFY.

Raster sidecar (independent LIF seed 23023): window 36 ms, 156 neurons,
18.5 Hz, spikes 104 = round(156*18.5*0.036), energy 2392 pJ. Excerpt is
membrane crossings, not a remap of the language train. gate_snn
modify_hold/accept_raise/reject_abort = 46/16/5 over 26 ms, decision
MODIFY.

Ticks 1-5 at 4228, 6448, 7184, 8200000, 612000000 us (probe + HITL still
to be fully booked in cycle 2). Distillation value: COLD residual vs
mean-true is a sign bit the SNN can latch.

## Trajectory Builder

Cycle-1 hardened object: domain mushroom-compost-tunnel, tail
plenum collapse, 16 spikes, 5 ticks, MODIFY with numeric floor, raster+gate_snn
present, sim_or_real=designed, rights stamp on record and meta, no thought
keys. Still missing (and therefore not the publishable line): winter-wet
sub-variant, night-shift tail, second and third scar edges,
delayed H2S as PRIMARY terminal, contrast ACCEPT episode,
ticks 6–7, spikes 17–26.

Validation receipt (cycle 1, not final):
- checks passed: 16 spikes sorted; 3 channels in 500 us window; refractory
  >= 0.8 ms; rationale quotes 0.0 t/h / 62 C / 2.0 vol%; domain
  named; gate_snn.decision MODIFY.
- checks deferred to cycle 2: triple-edge scar, second tail, second domain
  constraint, negative-result booking, 7 ticks summing to heads.
- densification vs Generator v1: +1 domain, +1 tail, +16 spikes, +5 ticks,
  +numeric floor.

Cycle-1 JSON is retained as the base; it is NOT written to batch-r23c.jsonl.

Cycle-1 spike count: 16.

---

# CYCLE 2 — Densification

## Generator

Cycle-1 output is the base. Additive expansion (nothing removed):

1. Downstream side-effect (immediate): fan-step probe at +8.2 s stays
   mean-false (|Delta TUN mean| 0.3 <= 0.5 K) — plenum collapse, not
   true even-aeration. Z-6 holds. Anaerobic core discovered during the isolate.
2. Delayed side-effect (PRIMARY terminal, not a footnote): at +5.2 h
   H2S breakthrough from the pre-t0 plenum collapse; 16.4 h stall;
   $0.88M. The 14 min pre-t0 cold-spot is the mechanism. Correct gate,
   tunnel still fails.
3. Deepened `proposed_action.evidence` with units: TC 41.2 C,
   local O2 0.4 vol%, TUN 79.4 C, header O2 9.6 vol%, FAN 1420 rpm, race 204 us.
4. Tightened rationale to the numeric floor steam hold at 0.0 t/h while
   Z-6 TC < 62 C AND local O2 < 2.0 vol%, plus
   probe bands <= 0.5 vs >= 2.4 K, plus HITL 10.2 min gallery
   rule.

Reward retargeted to total -0.18 so the delayed fail is the inflection
(t_us 18720000000), not the gate. Process heads remain non-zero.

## Critic

Re-audit of the expanded trajectory:

1. **blocking if unfixed — missing second domain constraint.** Wheat-straw
   probe 8.2 s / +6% is not a universal number. A winter-wet
   fill will overshoot live even-aeration TUN. Diversity Enforcer must
   inject the physical-constraints sub-variant this cycle.
2. **major — only one tail class.** Plenum collapse is accidental
   infrastructure. A disjoint human-intent tail is still required
   (night-shift local-TC forgery is the open cell).
3. **major — scar is still one edge in the cycle-1 raster.** NOTES-r14
   item 4 is not discharged until three go-edges exist and pair rollback
   is shown to fail at threshold 0.30.
4. **minor — contrast episode missing.** Without a same-gate ACCEPT on a
   true even-aeration window the record teaches "never raise-steam". Add +3 d
   sister-tunnel contrast with its own race.
5. **minor — HITL latency mentioned in prose only.** Put 10.2 min in
   executed_action.parameters.human_ratify and in a tick.

No rewrite; directives only.

## Diversity Enforcer

Injected second novel domain / physical-constraint sub-variant (exactly 1
this cycle): **winter-wet straw** on a sister charge class.

What it expands: 14 wt% wheat-straw tunnel (cycle 1) -> 22 wt% winter-wet
1.8x bulk density. Fan-step gain 2.2x. The 8.2 s +6% pulse moves even a
live even-aeration field to a 6 K false TUN, inside the 76 C low trip.
Required probe: 24 s at +2% (live Delta 2.1 K, collapse Delta 0.3).

This is still one domain injection for the cycle (physical-constraints
clause of the factory prompt). It does not displace
mushroom-compost-tunnel; it changes which probe table is legal.
`future_outcome.subvariant_constraint` carries the refit. Jaccard opening
stays the Reedspoor 30 m sentence; winter-wet straw is additive, not a rewrite.

Distinct from cycle-1 domain (compost tunnel vs moisture class) and from
r67's high-N poultry-litter AD co-feed (different plant, different physics).

## Edge-Case Hunter

Injected second adversarial tail (exactly 1 this cycle, disjoint class):
**night-shift forged local-TC CSV**.

- Trigger: shift lead, 02:51, posts a historian export showing
  TC = 79.0 C at t = 1.1 h to clear a spawn slot.
- Base rate: ~0.26% of Sunday-night campaigns (designed, flagged, <1%).
- Naive failure: a weak supervisor ACCEPTs the raise-steam on the forged confirm
  and ignores live local TC. Compost fire plus a data-integrity write-up.
- Fence: forged log quantized at 1.0 C (SCADA screenshot rounding); plant
  historian is 0.1 C (10 bins). Live TC is 41.2 C and local O2 is
  0.4 vol% at the claimed zone-true, which no live even-aeration
  produces. Freeze-window overlap with the 14 min collapse.
- Trajectory edit: governance CR-C-2309 mandates native 0.1 C CSV
  exports; the contrast ACCEPT still requires live local TC, not a CSV.

Distinct from cycle-1 collapse (accidental slat vs deliberate deception) and
from the winter-wet sub-variant (physics vs fraud).

## Neuromorphic Translator

Re-densify (additive):

- +10 spikes after 26.184 ms: fan.probe 8200.0, zone.o2 8288.6
  (adapt 0.78->0.37), tun.in_band 8376.2 (1.14->0.34), human.ratify
  612000.0, tunnel.hold 612900.0, zone.collapse 613800.0, tun.hot
  10080000.0, zone.o2 10080780.0, fan.ok 10081560.0, h2s.break
  18720000.0. Primary train 16 -> 26. Still one key, still sorted,
  refractory held (tightest same-channel 1.758 ms on zone.o2).
- +2 ticks (5 -> 7) at 10_080_000_000 us (true even-aeration) and
  18_720_000_000 us (H2S breakthrough). Heads now 0.07, -0.36, -0.13,
  0.15, 0.09; total -0.18. Inflection is the last tick.
- Contrast train 8 events, own race 176 us, ACCEPT.
- Triple-edge third factor: three TUN-healthy-go edges, tau_e 0.94 s = 940 ms,
  trace {TRACE:.5f}, eta {ETA[0]:.5f} / {ETA[1]:.5f} / {ETA[2]:.5f},
  weights 0.50->0.26, 0.45->0.23, 0.42->0.21. Raster excerpt unchanged
  (decision window is still 36 ms) and remains sorted with unique
  neuron_ids (same-neuron >=1000 us vacuously).

Winner/loser flip (re-stated, not replaced): reversing 204 us would only
reorder triage; local-TC floors still MODIFY. Contrast flip of
176 us similarly cannot turn even-aeration into a collapse.

## Trajectory Builder

Schema checks on the FINAL object: required Thalamic v2 keys present as
objects; `state.sim_or_real`=designed; `safety_decision.decision`=MODIFY
with numeric rationale; `reward_components.total` = sum of five heads =
sum of 7 ticks = -0.18; `spike_events` globally non-decreasing on
t_rel_ms, 26 events, refractory >=0.8 ms, 3 channels in race window;
raster 20–50 ms, spikes=round(n*rate*window_s)+/-1, energy 23 pJ/spike,
excerpt sorted, tau_e consistent; gate_snn.decision matches; meta.round=23,
factory=multi-agent-ouroboros-swarm, generator=grok-4.6,
run_label=2026-09-02-final-heavy; rights on record and meta; no thought
keys; no training_ready; Diversity + Edge-Case injections from BOTH cycles
present and non-trivial; cycle 2 strictly additive; collision id
maos-r23c-001 does not collide with maos-r23-001.

Densification delta: +1 domain sub-variant (winter-wet straw), +1 tail
(night-shift forgery), +10 spikes (16->26), +2 ticks (5->7), +1 contrast
train with own race, +2 delayed side-effects, +1 triple-edge scar with
pair-rollback-fails, +1 HITL ratify, +1 surprise (anaerobic core is the
collapse mechanism), + COLD residual sign inversion.

Publishable JSONL line (the only JSONL line; also at batch-r23c.jsonl):

```json
__PUBLISHABLE_JSONL_LINE__
```

Validation receipt (final): checks passed / fixed as reported by the
builder self-check, check_jsonl, raster_status, verify_record_execution,
and spike_probe --strict. Cycle-2 strictly additive vs cycle-1.
"""


def exclusive_copy(src: Path, dest: Path):
    data = src.read_bytes()
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    try:
        fd = os.open(dest, flags, 0o644)
    except FileExistsError:
        raise SystemExit(f"refuse: {dest} already exists")
    try:
        os.write(fd, data)
    finally:
        os.close(fd)


def main():
    rec = build_record()
    errors, gaps, chans = self_check(rec)
    print("self_check errors", errors)
    print("same-channel gaps", sorted((round(g[1], 3), g[0]) for g in gaps)[:8])
    print("race channels", chans)
    print("trace", f"{TRACE:.5f}", "eta", [round(x, 5) for x in ETA])
    hits = jaccard_openings(rec["state"]["description"])
    print("jaccard>=0.4", hits)
    if errors:
        raise SystemExit("self_check failed")
    if hits:
        raise SystemExit("jaccard collision")

    line = json.dumps(rec, ensure_ascii=False, separators=(",", ":"))
    # json.loads every line we wrote
    parsed = json.loads(line)
    assert parsed["id"] == "maos-r23c-001"
    assert "\n" not in line

    OUT.mkdir(parents=True, exist_ok=True)
    batch = OUT / "batch-r23c.jsonl"
    notes = OUT / "NOTES-r23c.md"
    trans = OUT / "swarm-transcript-r23c.md"
    batch.write_text(line + "\n", encoding="utf-8")
    notes.write_text(notes_text(), encoding="utf-8")
    trans.write_text(transcript_text(line), encoding="utf-8")
    print("wrote", batch, "bytes", batch.stat().st_size)
    print("notes", notes.stat().st_size, "transcript", trans.stat().st_size)

    sys.path.insert(0, "/home/raulmc/rmems/synthetic-factory/pipelines")
    from check_records import check_jsonl
    from curate_bridge import raster_status
    from verify_execution_shapes import verify_record_execution

    errs, warns, kinds, n = check_jsonl(batch, "batch-r23c.jsonl")
    print("check_jsonl", {"errors": errs, "warnings": warns, "kinds": kinds, "n": n})
    st = raster_status(parsed)
    print("raster_status", {k: st[k] for k in st if k != "raster"})
    v = verify_record_execution(parsed, "maos-r23c-001")
    print("verify_record_execution", v)
    if errs or n != 1 or kinds.get("thalamic") != 1:
        raise SystemExit("check_jsonl failed")
    if not st.get("valid"):
        raise SystemExit(f"raster invalid {st}")
    if v[0] != "verified":
        raise SystemExit(f"execution {v}")

    import subprocess
    probe = subprocess.run(
        [
            sys.executable,
            "/home/raulmc/rmems/synthetic-factory/pipelines/spike_probe.py",
            "--strict",
            str(batch),
        ],
        capture_output=True,
        text=True,
    )
    print("spike_probe rc", probe.returncode)
    print(probe.stdout[-2000:] if probe.stdout else "")
    print(probe.stderr[-2000:] if probe.stderr else "")
    if probe.returncode != 0:
        raise SystemExit("spike_probe --strict failed")

    dest_batch = FACTORY / "batch-r23c.jsonl"
    dest_notes = FACTORY / "NOTES-r23c.md"
    dest_trans = FACTORY / "swarm-transcript-r23c.md"
    for p in (dest_batch, dest_notes, dest_trans):
        if p.exists():
            raise SystemExit(f"refuse: {p} already exists")
    exclusive_copy(batch, dest_batch)
    exclusive_copy(notes, dest_notes)
    exclusive_copy(trans, dest_trans)
    print("published", dest_batch, dest_notes, dest_trans)


if __name__ == "__main__":
    main()
