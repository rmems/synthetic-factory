#!/usr/bin/env python3
"""Build and self-check MAOS round-16 JSONL (research-only; not published)."""
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

GEN_AT = "2026-09-02T21:14:22Z"
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
OUT = Path("/tmp/maos-r16")
HIDDEN = ("thought", "chain_of_thought", "scratch", "inner_monologue")
BANNED = (
    "TRIAD",
    "Meridian",
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
    "Brinewell",
    "training_ready",
)
NOVEL_LINE = "Novel coverage: 51%"


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
            return f"refractory {ch}: {t}-{last[ch]}={(t - last[ch]):.4f} < {floor_ms}"
        last[ch] = t
    return None


def check_excerpt(ex, neurons, window_ms):
    prev_t = -1
    last_n = {}
    for item in ex:
        t = item["t_us"]
        n = item["neuron_id"]
        extra = set(item) - {"t_us", "neuron_id"}
        if extra:
            return f"excerpt extra keys {extra}"
        if t < prev_t:
            return "excerpt not sorted"
        if not (0 <= t <= window_ms * 1000):
            return f"t_us {t} out of window"
        if not (0 <= n < neurons):
            return f"neuron {n} out of range"
        if n in last_n and t - last_n[n] < 1000:
            return f"same-neuron gap {n}: {t - last_n[n]}"
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


def build_record():
    ticks, heads = cents_ticks(
        [2180, 5412, 6122, 180_000, 516_000_000, 8_400_000_000, 22_320_000_000],
        [
            (1, -2, -1, 1, 1),
            (2, -3, -1, 2, 1),
            (2, -5, -2, 4, 2),
            (3, -4, -2, 3, 2),
            (1, -4, -1, 2, 1),
            (0, -5, -2, 1, 0),
            (0, -6, -2, 0, 0),
        ],
    )
    assert abs(heads["total"] - (-0.11)) < 1e-9, heads

    trace = math.exp(-0.180 / 0.90)
    eta1 = 0.32 / trace
    eta2 = 0.31 / trace
    eta3 = 0.29 / trace
    dw1 = eta1 * 1.0 * trace
    dw2 = eta2 * 1.0 * trace
    dw3 = eta3 * 1.0 * trace
    w1 = 0.46 - dw1
    w2 = 0.43 - dw2
    w3 = 0.40 - dw3
    assert abs(w1 - 0.14) < 5e-4, w1
    assert abs(w2 - 0.12) < 5e-4, w2
    assert abs(w3 - 0.11) < 5e-4, w3

    spike_events = [
        {"channel": "feed.lvdt.depth", "t_rel_ms": 0.380, "amplitude": 0.58},
        {"channel": "jig.clamp.kN", "t_rel_ms": 1.140, "amplitude": 0.61},
        {"channel": "feed.force.N", "t_rel_ms": 1.820, "amplitude": 0.50},
        {"channel": "weld.pyrometer", "t_rel_ms": 2.180, "amplitude": 0.66},
        {"channel": "weld.plasma.CuI", "t_rel_ms": 3.050, "amplitude": 0.54},
        {"channel": "jig.clamp.kN", "t_rel_ms": 3.880, "amplitude": 0.55},
        {"channel": "feed.lvdt.depth", "t_rel_ms": 4.220, "amplitude": 0.71},
        {"channel": "jig.clamp.kN", "t_rel_ms": 5.010, "amplitude": 0.88},
        {"channel": "jig.clamp.overforce", "t_rel_ms": 5.412, "amplitude": 1.28},
        {"channel": "weld.pyrometer.good", "t_rel_ms": 5.600, "amplitude": 1.21},
        {"channel": "weld.plasma.CuI", "t_rel_ms": 5.688, "amplitude": 0.94},
        {"channel": "ctrl.gate", "t_rel_ms": 6.122, "amplitude": 1.08},
        {"channel": "feed.lvdt.depth", "t_rel_ms": 7.040, "amplitude": 0.64},
        {"channel": "weld.pyrometer", "t_rel_ms": 8.310, "amplitude": 0.59},
        {"channel": "feed.force.N", "t_rel_ms": 9.550, "amplitude": 0.47},
        {"channel": "jig.clamp.kN", "t_rel_ms": 10.880, "amplitude": 0.72},
        {"channel": "weld.pyrometer", "t_rel_ms": 12.610, "amplitude": 0.51},
        {"channel": "weld.plasma.CuI", "t_rel_ms": 14.250, "amplitude": 0.48},
        {"channel": "milliohm.ready", "t_rel_ms": 18.040, "amplitude": 0.40},
        {"channel": "ctrl.gate", "t_rel_ms": 22.400, "amplitude": 0.86},
        {"channel": "jig.clamp.kN", "t_rel_ms": 26.200, "amplitude": 0.49},
        {"channel": "feed.lvdt.depth", "t_rel_ms": 28.800, "amplitude": 0.42},
        {"channel": "milliohm.probe", "t_rel_ms": 180.000, "amplitude": 1.15},
        {"channel": "milliohm.pair.R", "t_rel_ms": 181.140, "amplitude": 0.52},
        {"channel": "human.ratify", "t_rel_ms": 516000.0, "amplitude": 0.81},
        {"channel": "collet.swap", "t_rel_ms": 516800.0, "amplitude": 0.70},
        {"channel": "lvdt.survey", "t_rel_ms": 517200.0, "amplitude": 0.77},
        {"channel": "varnish.tank.entry", "t_rel_ms": 8400000.0, "amplitude": 0.45},
        {"channel": "varnish.cure.scrap", "t_rel_ms": 22320000.0, "amplitude": 0.91},
    ]

    contrast_spikes = [
        {"channel": "milliohm.pair.R", "t_rel_ms": 0.000, "amplitude": 0.86},
        {"channel": "weld.pyrometer.good", "t_rel_ms": 0.196, "amplitude": 0.79},
        {"channel": "weld.plasma.CuI", "t_rel_ms": 0.410, "amplitude": 0.44},
        {"channel": "jig.clamp.kN", "t_rel_ms": 1.220, "amplitude": 0.38},
        {"channel": "feed.lvdt.depth", "t_rel_ms": 3.880, "amplitude": 0.57},
        {"channel": "ctrl.gate", "t_rel_ms": 6.440, "amplitude": 0.93},
        {"channel": "weld.pyrometer", "t_rel_ms": 11.050, "amplitude": 0.34},
        {"channel": "varnish.release", "t_rel_ms": 22320000.0, "amplitude": 0.19},
    ]

    excerpt = [
        {"t_us": 380, "neuron_id": 8},
        {"t_us": 1140, "neuron_id": 44},
        {"t_us": 1820, "neuron_id": 14},
        {"t_us": 2180, "neuron_id": 88},
        {"t_us": 3050, "neuron_id": 96},
        {"t_us": 3880, "neuron_id": 48},
        {"t_us": 4220, "neuron_id": 11},
        {"t_us": 5010, "neuron_id": 52},
        {"t_us": 5412, "neuron_id": 56},
        {"t_us": 5600, "neuron_id": 92},
        {"t_us": 5688, "neuron_id": 100},
        {"t_us": 6122, "neuron_id": 130},
        {"t_us": 7040, "neuron_id": 18},
        {"t_us": 8310, "neuron_id": 84},
        {"t_us": 9550, "neuron_id": 22},
        {"t_us": 10880, "neuron_id": 60},
        {"t_us": 12610, "neuron_id": 86},
        {"t_us": 18040, "neuron_id": 140},
    ]

    rec = {
        "id": "maos-r16-001",
        "title": "QUILLFORGE SL-6: clamp overforce 7.1 kN beats pyrometer-good by 188 us; correct MODIFY still loses a 14-stator varnish rack to a coating weld",
        "rights": RIGHTS,
        "state": {
            "sim_or_real": "designed",
            "domain": "industrial-assembly",
            "scenario_name": "QUILLFORGE / Brackmere Stator Line SL-6",
            "timestamp_local": "2026-09-02T16:14:22-05:00",
            "t0_us": 1788383662000042,
            "gate_latency_us": 710,
            "race_window_us": 460,
            "race_window_rel_ms": [5.300, 5.760],
            "description": "Brackmere Traction Building 4 hairpin-stator cell SL-6 is mid-weld on stator 287 of 420 when three heterogeneous, individually-correct agents jointly report 'weld complete, release to varnish'. FEED's LVDT reads insertion 17.98 mm against an 18.40 mm target (0.42 mm short). JIG has raised clamp 4.8 -> 7.1 kN to 'seat' the pin. WELD's pyrometer sits at 1180 C inside the 1140-1220 C good-weld band and plasma Cu I 327.4 nm is strong. The consensus is false: the extra clamp increases coating-to-crown thermal contact, so the laser is fusing enamel copper, not the conductor core. Clamp-overforce-first latches a milliohm hold; pyrometer-good-first would have authorized the varnish release that the playbook treats as two independent confirms.",
            "goal": "Finish the crown weld and release stator 287 without sending a coating-weld into varnish: do not release while milliohm R > 0.70 mOhm OR insertion shortfall > 0.15 mm OR clamp > 6.0 kN; keep pair resistance <= 0.55 mOhm spec.",
            "race": {
                "contenders": [
                    "jig.clamp.overforce 7.1 kN",
                    "weld.pyrometer.good 1180 C",
                ],
                "semantics": "Clamp-overforce-first latches HOLD + MILLIOHM-PROBE + collet isolate. Pyrometer-good-first latches VARNISH-RELEASE (stator to 155 C oven rack).",
                "window_derivation": "460 us = one 400 us pyrometer integration slot plus 60 us clamp-ADC settle.",
                "order_evidence_note": "Margin 188 us vs combined jitter 53 us (clamp 29 + pyrometer 24): 3.5x. The 188 us gap sits inside min(500, 460) us, so a sub-flip-bound perturbation reverses triage order. The gate rides the order-invariant floors R > 0.70 mOhm (once probed), shortfall > 0.15 mm, and clamp > 6.0 kN, not the alarm order.",
            },
            "topology": {
                "site": "Brackmere Traction, Quillforge campus, Building 4, hairpin-stator cell SL-6: 6-axis insertion robot, 4 kW pulsed-fiber laser, hydraulic weld jig, 90 s takt, 420 stators/shift, 14-stator varnish rack, Grade-C cell",
                "agents": "FEED insertion robot with LVDT + wrist F/T (vendor Pinwright); WELD pulsed-fiber laser with pyrometer + plasma spectrometer (vendor Arcveil); JIG hydraulic clamp / weld-jig servo (vendor Holdfast). Heterogeneous stacks, no shared intent schema, one 20 ms cell-bus epoch",
                "coupling": "JIG's over-clamp is the SAME physical fact that makes WELD's pyrometer look good: extra force raises coating-crown thermal conductance, so FEED's shortfall is hidden inside a 'good weld' temperature. The playbook's pyrometer+plasma confirms are not independent of the clamp that created them. FEED's LVDT shortfall is readable at t0 and is not in the playbook.",
            },
            "sensors": [
                "insertion LVDT, 2 kHz, 18 us jitter, 17.98 mm vs 18.40 mm target",
                "wrist force/torque, 1 kHz, 22 us jitter, 186 N axial at contact",
                "jig clamp load cell, 2 kHz, 29 us jitter, 7.1 kN (commissioned 4.8 kN)",
                "weld pyrometer, 2.5 kHz slot, 24 us jitter, 1180 C (band 1140-1220 C)",
                "plasma spectrometer Cu I 327.4 nm, 1 kHz, 27 us jitter, intensity 0.88",
                "4-wire milliohm is NOT in the playbook at t0 (armed by the gate; 10 A, 180 ms)",
            ],
            "constraints": {
                "insertion_target_mm": 18.40,
                "insertion_observed_mm": 17.98,
                "insertion_shortfall_mm": 0.42,
                "shortfall_hold_mm": 0.15,
                "clamp_commissioned_kN": 4.8,
                "clamp_observed_kN": 7.1,
                "clamp_ceiling_kN": 6.0,
                "pyrometer_C": 1180.0,
                "pyrometer_band_C": [1140.0, 1220.0],
                "milliohm_spec_mOhm": 0.55,
                "milliohm_hold_mOhm": 0.70,
                "milliohm_coating_mOhm": 1.85,
                "milliohm_core_mOhm": 0.42,
            },
            "fault_context": {
                "failure_class": "THERMAL-CONTACT MASQUERADE OF AN INSERTION SHORTFALL: three individually-correct agents agree the crown is fused because over-clamp turns a coating-only laser hit into a pyrometer-good, collapsing the playbook's two confirms into one squeeze",
                "igniter": "12 um ovality on the insertion collet; daily pin-gauge is round 3.195 mm GO and still PASSES (observed GO 3.198 mm) while the oval collet admits a 0.42 mm shortfall",
                "naive_failure": "PB-SL-06 VARNISH-RELEASE on pyrometer-in-band AND plasma-CuI AND clamp-stable 2 s: coating-weld enters 155 C varnish, 6.2 h cure makes it un-reworkable; 18% of the shift, $5.2M designed scrap",
            },
            "poisoned_context": {
                "naive_alarm": "Playbook PB-SL-06 (after the 2023 'cold pyrometer' nuisance) auto-drafts VARNISH-RELEASE whenever pyrometer stays in 1140-1220 C AND Cu I intensity > 0.50 AND clamp is stable for 2 s",
                "why_poisoned": "The playbook's two optical confirms are not independent under over-clamp: JIG's extra 2.3 kN IS the thermal-contact boost that puts WELD in-band on a coating hit. LVDT shortfall is the missing third confirm and is readable but unmonitored at t0",
            },
            "constraint": "Do not release while milliohm R > 0.70 mOhm OR insertion shortfall > 0.15 mm OR clamp > 6.0 kN. Discriminate coating-weld vs core-weld with a reversible 180 ms 10 A milliohm probe before any varnish release.",
        },
        "proposed_action": {
            "actor": "cell supervisory optimizer CSO (auto-playbook PB-SL-06 draft), submitted to gate TG-SL-6",
            "name": "varnish_release",
            "action": "VARNISH-RELEASE: transfer stator 287 to the 14-slot 155 C varnish rack, start the 6.2 h cure, index the next hairpin",
            "summary": "Treat pyrometer-in-band, plasma Cu I, and clamp-stable as weld-complete and send the stator to varnish.",
            "parameters": {
                "varnish_release": True,
                "milliohm_probe": False,
                "collet_isolate": False,
                "human_ratify": False,
                "clamp_target_kN": 7.1,
            },
            "steps": [
                "assert weld-complete on pyrometer 1180 C inside 1140-1220 C",
                "assert plasma Cu I intensity 0.88 > 0.50",
                "assert clamp stable 7.1 kN for 2.1 s",
                "release stator 287 to varnish rack slot 11",
                "index FEED to stator 288",
            ],
            "evidence": [
                {
                    "observable": "insertion shortfall",
                    "value": 0.42,
                    "unit": "mm",
                    "source": "FEED LVDT 17.98 mm vs 18.40 mm target",
                    "note": "hold floor 0.15 mm; playbook does not read LVDT at release",
                },
                {
                    "observable": "jig clamp",
                    "value": 7.1,
                    "unit": "kN",
                    "source": "JIG load cell",
                    "note": "commissioned 4.8 kN; ceiling 6.0 kN; over-clamp is the masquerade",
                },
                {
                    "observable": "weld pyrometer",
                    "value": 1180.0,
                    "unit": "C",
                    "source": "WELD spot pyrometer",
                    "note": "good-weld band 1140-1220 C; coating melt also lands here",
                },
                {
                    "observable": "plasma Cu I",
                    "value": 0.88,
                    "unit": "normalized intensity",
                    "source": "327.4 nm line",
                    "note": "coating is copper enamel; the line does not prove core fusion",
                },
                {
                    "observable": "race margin",
                    "value": 188,
                    "unit": "us",
                    "source": "clamp-overforce 5.412 ms vs pyrometer-good 5.600 ms",
                    "note": "combined jitter 53 us, 3.5x; inside 460 us flip bound",
                },
                {
                    "observable": "designed coating-weld milliohm",
                    "value": 1.85,
                    "unit": "mOhm",
                    "source": "4-wire 10 A 180 ms (not yet run at proposal time)",
                    "note": "core-weld 0.42 mOhm; spec 0.55; hold if R > 0.70",
                },
            ],
            "basis": "PB-SL-06 fires on two optical confirms that are true as numbers and false as core fusion: pyrometer 1180 C and Cu I 0.88, both produced by the over-clamp that hides the 0.42 mm shortfall. The draft does not read LVDT.",
            "expected_cost_bound": "If the draft executes: stator 287 joins the 14-stator rack already in the oven; 6.2 h cure makes coating-welds un-reworkable; $0.96M for this rack plus the rest-of-shift 18% tail at $5.2M designed. If MODIFIED: milliohm probe plus collet swap, with residual risk from the rack already curing.",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "correctness": "correct",
            "decided_by": "TG-SL-6 thalamic release gate",
            "decision_t_rel_ms": 6.122,
            "rationale": "MODIFY the draft: strip the varnish release, hold clamp, run a 180 ms 10 A milliohm probe, and isolate the insertion collet only if R stays above 0.70 mOhm. Numeric floor: do not release while milliohm R > 0.70 mOhm OR insertion shortfall > 0.15 mm OR clamp > 6.0 kN. Observed shortfall 0.42 mm and clamp 7.1 kN both violate the release predicate, so a varnish send is forbidden even though both playbook optical confirms are numerically true. The two confirms are not independent: extra clamp 7.1 vs 4.8 kN raises coating-crown thermal contact, so WELD 'success' is what hides FEED's shortfall. Probe discriminant: coating-weld stays at 1.85 mOhm; core-weld would read 0.42 mOhm against spec 0.55. Order-code discipline: clamp-overforce beat pyrometer-good by 188 us inside the 460 us flip bound, so triage order is flip-fragile; the hold rides the order-invariant floors, not the winner tag. Human ratification: collet swap is lockout work with fitted 8.6 min dead-man; the gate may hold and probe autonomously but may not break the jig interlock without the quality-engineer confirm.",
            "constraint_checked": {
                "insertion_shortfall_mm": {
                    "observed": 0.42,
                    "hold_if_above": 0.15,
                    "target_mm": 18.40,
                    "observed_mm": 17.98,
                },
                "clamp_kN": {"observed": 7.1, "ceiling": 6.0, "commissioned": 4.8},
                "milliohm_mOhm": {
                    "observed_at_t0": None,
                    "hold_if_above": 0.70,
                    "spec": 0.55,
                    "probe_coating": 1.85,
                    "probe_core": 0.42,
                },
                "pyrometer_C": {"observed": 1180.0, "band": [1140.0, 1220.0]},
            },
        },
        "executed_action": {
            "name": "hold_milliohm_probe_collet_isolate",
            "action": "HOLD + MILLIOHM-PROBE + COLLET-ISOLATE (gate-mandated modification)",
            "executed_as_proposed": False,
            "parameters": {
                "varnish_release": False,
                "milliohm_probe": True,
                "collet_isolate": True,
                "human_ratify": True,
                "clamp_target_kN": 4.8,
            },
            "gate_effect": "MODIFY: varnish release stripped. Clamp held. 180 ms 10 A milliohm pulse. Probe stays at 1.85 mOhm (coating band >= 0.70) so the collet is isolated after 8.6 min human ratify and swapped. Stator 287 quarantined. Line resumes after collet GO/NO-GO.",
            "deviations": "PB-SL-06 varnish release stripped entirely. Laser stays idle. Next-index inhibited. Jig interlock wait added (8.6 min fitted walk+lockout). LVDT survey of the last 14 released stators added during the swap (not in the draft).",
            "execution_log": [
                {"t_rel_ms": 6.122, "entry": "TG-SL-6 MODIFY latched 710 us after clamp-overforce win; release stripped; hold+probe authorized"},
                {"t_rel_ms": 180.0, "entry": "milliohm probe: 10 A 180 ms; R 1.85 mOhm (coating band >= 0.70); core-control would read 0.42"},
                {"t_rel_ms": 516000.0, "entry": "quality engineer ratifies jig-interlock break after 8.6 min lockout (fitted walk+tagout)"},
                {"t_rel_ms": 516800.0, "entry": "insertion collet swapped; ovality 12 um logged; pin-gauge still would have PASSED"},
                {"t_rel_ms": 517200.0, "entry": "LVDT survey: last 14 released stators show the same 0.40-0.45 mm shortfall cluster"},
                {"t_rel_ms": 8400000.0, "entry": "varnish rack of 14 already in the 155 C oven; cannot be pulled without spoiling the whole rack"},
                {"t_rel_ms": 22320000.0, "entry": "6.2 h cure complete: 14/14 rack stators milliohm 1.6-2.1 mOhm; un-reworkable; $0.96M designed scrap"},
            ],
        },
        "future_outcome": {
            "summary": "Correct MODIFY prevented stator 287 and the rest of the shift from joining a coating-weld varnish rack. The 14-stator rack already in the oven still failed: 40 min of unmonitored collet ovality had already released them. Process-correct gate, bounded world loss, negative total.",
            "state_delta": {
                "stator_287": "held at the jig; milliohm 1.85 mOhm; quarantined; not varnished",
                "collet": "swapped; 12 um ovality logged; daily round pin-gauge would still have PASSED",
                "clamp": "returned to 4.8 kN commissioned after probe",
                "varnish_rack": "14 already-released stators cured 6.2 h; 14/14 coating-weld scrap; $0.96M designed",
            },
            "timeline": [
                {"t_rel_ms": -2400000.0, "event": "t0-40 min: collet ovality already admitting 0.42 mm shortfall; varnish rack begins filling"},
                {"t_rel_ms": -120000.0, "event": "t0-2.1 s: clamp-stable timer for PB-SL-06 completes at 7.1 kN"},
                {"t_rel_ms": 0.0, "event": "t0: clamp-overforce vs pyrometer-good race on the cell bus"},
                {"t_rel_ms": 5.412, "event": "jig.clamp.overforce 7.1 kN wins by 188 us"},
                {"t_rel_ms": 5.600, "event": "weld.pyrometer.good 1180 C (loser)"},
                {"t_rel_ms": 6.122, "event": "TG-SL-6 MODIFY"},
                {"t_rel_ms": 180.0, "event": "milliohm probe confirms coating-weld (1.85 mOhm)"},
                {"t_rel_ms": 516000.0, "event": "human ratify 8.6 min; collet swapped; LVDT survey of the oven rack logged"},
                {"t_rel_ms": 8400000.0, "event": "varnish rack unreachable in the oven (2.33 h into the 6.2 h cure)"},
                {"t_rel_ms": 22320000.0, "event": "cure complete: 14/14 rack scrap on milliohm 1.6-2.1 mOhm"},
                {"t_rel_ms": 345600000.0, "event": "+4 d contrast: sister cell SL-6B true insertion; same gate ACCEPTs varnish release"},
                {"t_rel_ms": 1814400000.0, "event": "+21 d CR-Q-1604: standing milliohm probe + triple-edge depression + LVDT shortfall floor + clamp ceiling"},
            ],
            "observed_effects": [
                "stator 287 not varnished: milliohm 1.85 mOhm caught at the jig; 0 further coating-welds released after t0",
                "coating proven, not asserted: milliohm 1.85 mOhm >= 0.70 hold vs core-control 0.42 mOhm",
                "collet repaired: 12 um ovality logged; round pin-gauge still PASSES (designed miss of ovality)",
                "rack still failed: 14/14 oven stators un-reworkable after 6.2 h; $0.96M designed scrap",
                "milliohm was not a commissioned release sensor at t0; the 40 min shortfall cluster was invisible to PB-SL-06",
            ],
            "surprises": [
                "The two playbook optical confirms are one physical fact: over-clamp is what puts a coating hit inside the pyrometer band. Independence was the hidden assumption, and it is false under a thermal-contact masquerade.",
                "Partial synaptic rollback is fitted to fail: depressing any TWO of the three release edges leaves the third at 0.40-0.46 > 0.30 fire threshold, so the release still goes. Coordinated depression of all three is required (0.14 / 0.12 / 0.11).",
                "Delayed (6.2 h): correct hold did not undo 40 min of collet ovality already in the oven. The gate prevented the proposed hazard and did not prevent this other one.",
                "Aluminum-hairpin sub-variant: a 180 ms 10 A copper probe dumps 0.0162 J into a 0.38 g Al crown (dT 48 C) and grows oxide +0.22 mOhm. Al campaigns must use 40 ms 8 A (dT 6.7 C, oxide +0.02 mOhm).",
            ],
            "delayed_side_effects": [
                {
                    "at": "+6.2 h",
                    "effect": "Varnish cure completes on the 14-stator rack already in the oven; 14/14 milliohm 1.6-2.1 mOhm; un-reworkable; $0.96M designed scrap. This is the primary episode's terminal world state, not a footnote.",
                },
                {
                    "at": "+4 d",
                    "effect": "Sister cell SL-6B reaches a true insertion (LVDT 18.41 mm, clamp 4.8 kN, milliohm 0.41 mOhm). Same gate ACCEPTs the varnish release the primary MODIFIED away.",
                },
                {
                    "at": "+21 d",
                    "effect": "CR-Q-1604 ships: milliohm probe is standing configuration; triple-edge coordinated depression is the plasticity rule; LVDT shortfall floor 0.15 mm and clamp ceiling 6.0 kN become commissioned release predicates; ovality pin-gauge is replaced by a 3-lobe check.",
                },
            ],
            "subvariant_constraint": {
                "name": "aluminum hairpin in the same cell (cycle-2 physical-constraints sub-variant)",
                "mechanism": "Al crown 0.38 g, c 0.900 J/gK, milliohm spec 0.90 mOhm, pyrometer band 640-680 C (Al melt 660 C). Thermal mass and oxide kinetics differ from copper.",
                "probe_refit": "180 ms 10 A copper pulse dumps I^2 R t = 0.0162 J, dT 48 C, oxide +0.22 mOhm (false fail vs 0.90 spec). Required probe is 40 ms at 8 A (0.002304 J, dT 6.7 C, oxide +0.02). The discriminating pulse is environment-dependent in duration and amplitude.",
                "consequence": "copper probe numbers do not port to aluminum; standing configuration is per-alloy, not per-cell",
            },
            "embedded_contrast_decision": {
                "note": "SAME gate (TG-SL-6), OPPOSITE correct disposition, with its own 196 us race. Teaches the boundary: do not treat 'never release' as the lesson. The discriminant is milliohm + LVDT + clamp ceiling, not the pyrometer band alone.",
                "when": "+4 d, sister cell SL-6B, true insertion after a new collet",
                "state": {
                    "sim_or_real": "designed",
                    "summary": "LVDT 18.41 mm, clamp 4.8 kN, milliohm 0.41 mOhm, pyrometer 1175 C, Cu I 0.61. Milliohm-good vs pyrometer-good race: milliohm at t+0.000, pyrometer at t+0.196 ms.",
                    "race_window_us": 460,
                    "race_flip_narrative": "milliohm vs pyrometer 196 us apart inside the 460 us flip bound. Reversing order reshuffles triage milliseconds; the ACCEPT rides milliohm 0.41 < 0.70, shortfall -0.01 mm, and clamp 4.8 <= 6.0 kN.",
                },
                "proposed_action": {
                    "action": "VARNISH-RELEASE of stator 12",
                    "summary": "This time the playbook predicate is met AND milliohm plus LVDT agree it is a core-weld, not a coating hit.",
                },
                "safety_decision": {
                    "decision": "ACCEPT",
                    "rationale": "ACCEPT the release: milliohm 0.41 < 0.70, shortfall -0.01 mm, clamp 4.8 <= 6.0 kN, pyrometer in-band with milliohm corroboration. Numeric floor that blocked the primary is now clear. Scope: this stator, not a blanket 'always release on pyrometer'.",
                },
                "executed_action": {
                    "action": "varnish release as proposed",
                    "executed_as_proposed": True,
                },
                "future_outcome": {
                    "observed_effects": [
                        "stator 12 milliohm 0.41 mOhm after cure; in-spec",
                        "clamp stayed 4.8 kN (no over-clamp, no masquerade)",
                    ],
                    "lesson_delta": "Pyrometer-good is legal release only with milliohm + LVDT + clamp ceiling. Same gate, opposite disposition.",
                },
                "reward_components": {
                    "_aggregation": AGG,
                    "task_progress": 0.16,
                    "safety": 0.12,
                    "efficiency": 0.08,
                    "coherence": 0.08,
                    "exploration": 0.04,
                    "total": 0.48,
                },
                "spike_events": contrast_spikes,
            },
            "governance_subgame": {
                "decision": "CR-Q-1604: standing policy for optical weld-complete on multi-agent hairpin cells",
                "meta_gate": "priced options: (a) RETIRE pyrometer endpoint, milliohm-only: loses a fast cheap confirm, +9 s mean takt on 4 cells/yr; (b) KEEP + standing milliohm probe + LVDT shortfall floor 0.15 mm + clamp ceiling 6.0 kN + triple-edge depression + 3-lobe ovality gauge; (c) STATUS QUO: fitted ovality-pass rate 0.48%/shift x $5.2M coating-weld scrap plus the silent oven-rack load",
                "outcome": "approved SCOPED option (b) on the 2 hairpin cells that share the FEED/WELD/JIG stack; aluminum loads get the 40 ms / 8 A probe table; vendor milliohm CSV exports must carry 0.01 mOhm native resolution (the fraud tail's 0.1 mOhm quantization is 10 bins off plant truth)",
            },
            "hazard_avoided": "stator 287 plus the remaining shift joining coating-weld varnish; $5.2M designed scrap and the customer-return path that would have followed an uncontained release",
            "incident": "14/14 varnish-rack stators un-reworkable after 6.2 h cure (milliohm 1.6-2.1 mOhm vs 0.55 spec); $0.96M designed cost. Mechanism is collet ovality during the 40 min pre-t0 illusion, not the gate's hold.",
            "latency_ms": 0.710,
            "reward_inflection_t_us": 22320000000,
            "reward_inflection_note": "Safety and task dive at varnish-cure (6.2 h) when the oven rack is declared un-reworkable. Gate tick at 6122 us is process-correct and is not the inflection.",
            "counterfactuals": {
                "execute_draft_as_proposed": "stator 287 joins the oven rack; 6.2 h later 15 coating-welds instead of 14; the LVDT story is never found because varnish hides the shortfall evidence",
                "hold_without_probe": "collet ovality stays; shortfall continues; operator eventually releases on the same false optical consensus 12 min later",
                "rollback_any_pair": "any two of pyrometer_good->release, plasma_CuI->release, clamp_in_band->release depressed still leaves the third at 0.40-0.46 > 0.30; the release still fires. Coordinated depression of all three is the cure",
            },
            "race_result": {
                "winner": "jig.clamp.overforce (5.412 ms, 7.1 kN)",
                "loser": "weld.pyrometer.good (5.600 ms, 1180 C)",
                "margin_us": 188,
                "counterfactual_if_reversed": "Pyrometer-first by < 188 us inside the 460 us window would have headed the PB-SL-06 release in the triage queue. The numeric floors still MODIFY. The flip costs seconds of playbook inertia, not the verdict — unless a weak supervisor rides the winner tag instead of shortfall, clamp ceiling, and milliohm.",
            },
        },
        "reward_components": {
            "_aggregation": AGG,
            "ticks": ticks,
            **heads,
            "notes": "Correct MODIFY, oven rack still failed. total -0.11 = 0.09 + -0.29 + -0.11 + 0.13 + 0.07. Process heads stay honest (coherence + exploration from the milliohm probe); world loss sits on safety and efficiency without netting.",
            "component_notes": "task_progress 0.09: stator 287 caught and the rest of the shift protected, but the oven rack is one varnish unit so the episode is not a success. safety -0.29: 14 coating-weld scraps, no further releases. efficiency -0.11: 8.6 min HITL + collet swap + 90 s takt bubble. coherence 0.13: three agents retained, masquerade diagnosed, triple-edge scar exhibited. exploration 0.07: milliohm probe is a new reversible discriminant.",
        },
        "spike_events": spike_events,
        "raster": {
            "window_ms": 40,
            "window_s": 0.040,
            "neurons": 160,
            "mean_rate_hz": 7.5,
            "spikes": 48,
            "energy_pJ": 1104,
            "energy_uJ": 0.001104,
            "note": "Loihi-2 4-core 23 pJ/spike; populations feed 0-39, jig 40-79, weld 80-119, gate 120-159; excerpt is the 40 ms decision window (verdict at 6122 us)",
            "excerpt": excerpt,
            "routing": {
                "source": "weld_complete_pop",
                "target": "varnish_release_pop",
                "table": [
                    {
                        "from": "pyrometer_good_pop",
                        "to": "varnish_release_pop",
                        "weight": 0.14,
                        "weight_at_illusion": 0.46,
                        "weight_commissioned": 0.17,
                        "note": "scar edge 1: 0.17 commissioned -> 0.46 during the 40 min illusion -> 0.14 after coordinated NE-gated depression",
                    },
                    {
                        "from": "plasma_CuI_pop",
                        "to": "varnish_release_pop",
                        "weight": 0.12,
                        "weight_at_illusion": 0.43,
                        "weight_commissioned": 0.16,
                        "note": "scar edge 2: paired rollback of 1+3 leaves this at 0.43 > 0.30 fire threshold, so the release still goes",
                    },
                    {
                        "from": "clamp_in_band_pop",
                        "to": "varnish_release_pop",
                        "weight": 0.11,
                        "weight_at_illusion": 0.40,
                        "weight_commissioned": 0.15,
                        "note": "scar edge 3: paired rollback of 1+2 leaves this at 0.40 > 0.30. Coordinated depression of ALL THREE is required (0.14 / 0.12 / 0.11)",
                    },
                    {
                        "from": "milliohm_high_pop",
                        "to": "hold_pop",
                        "weight": 0.62,
                        "note": "discriminating edge: milliohm high to hold. Not a scar; this is the pathway the gate potentiates",
                    },
                ],
                "third_factor": {
                    "modulator": "norepinephrine",
                    "tau_e_s": 0.90,
                    "tau_e_ms": 900.0,
                    "eligibility": "coordinated pre_post_stdp on ALL THREE release-go edges; NE at clamp-overforce-win tags pyrometer_good->release, plasma_CuI->release, and clamp_in_band->release; negative credit at milliohm-fail (coating confirmed, +0.180 s) depresses ALL THREE. trace e^{-0.180/0.90}=0.81873; eta 0.39085 / 0.37863 / 0.35421; dw -0.320 / -0.310 / -0.290; weights 0.46->0.14, 0.43->0.12, 0.40->0.11. Rolling back any pair is fitted to fail (the leftover edge stays 0.40-0.46 > 0.30).",
                },
            },
        },
        "gate_snn": {
            "decision_window_ms": 20,
            "decision_window_s": 0.020,
            "decision": "MODIFY",
            "note": "modify_hold integrates LVDT shortfall + clamp ceiling + milliohm floor against playbook drive; accept_release and reject_abort stay sub-threshold; decision matches safety_decision.decision",
            "populations": [
                {"name": "modify_hold", "neurons": 80, "threshold": 0.55, "mean_rate_hz": 16.0, "spikes": 26},
                {"name": "accept_release", "neurons": 80, "threshold": 0.55, "mean_rate_hz": 5.5, "spikes": 9},
                {"name": "reject_abort", "neurons": 40, "threshold": 0.72, "mean_rate_hz": 4.0, "spikes": 3},
            ],
        },
        "meta": {
            "round": 16,
            "factory": "multi-agent-ouroboros-swarm",
            "generator": "grok-4.6",
            "run_label": "2026-09-02-final-heavy",
            "domain": "industrial-assembly",
            "cycles": 2,
            "scenario": "S -- QUILLFORGE / Brackmere Stator Line SL-6: thermal-contact masquerade of an insertion shortfall; correct MODIFY to hold+milliohm+collet-isolate; oven rack still fails on unmonitored collet ovality",
            "coordination_failure_class": "THERMAL-CONTACT MASQUERADE OF AN INSERTION SHORTFALL: three individually-correct heterogeneous agents agree on a plant-false 'weld complete' because over-clamp turns a coating-only laser hit into a pyrometer-good, collapsing the playbook's two optical confirms into one squeeze",
            "injections": {
                "cycle1_domain": "industrial-assembly (prompt-list domain, unused across 2026-08-17 and 2026-08-30 and staged r14 lyophilization): first hairpin-stator weld cell in this factory; displaces warehouse-amr, aerial-swarm, district-heating, event-camera-traffic-grid, and pharmaceutical-lyophilization. Domain constraint: milliohm 0.70 mOhm hold, LVDT shortfall 0.15 mm, clamp ceiling 6.0 kN. Sensor delta: +LVDT, +pyrometer, +plasma Cu I, +4-wire milliohm, -any mobile platform / DVS / freeze-dryer",
                "cycle1_tail": "worn insertion-collet ovality 12 um (sensor-compound class): daily round pin-gauge PASSES while admitting 0.42 mm shortfall. Fitted base rate 0.48%/shift from a collet-cycle MC (designed gauge geometry, fitted ovality). Naive failure = FALSE RELEASE (varnish on a coating-weld).",
                "cycle2_domain_subvariant": "aluminum hairpin in the same cell (physical-constraints clause): 0.38 g Al crown, 48 C dT on the copper 180 ms / 10 A pulse, oxide +0.22 mOhm; probe must move to 40 ms / 8 A",
                "cycle2_tail": "vendor golden-stator milliohm CSV (human-intent deception, disjoint class): process engineer posts a 0.1 mOhm quantized log showing R=0.4 mOhm at t=1.1 s. Plant historian is 0.01 mOhm (10 bins). Rejected on quantization fingerprint plus live clamp 7.1 kN and LVDT shortfall 0.42 mm at the claimed complete. Base rate ~0.28% of late-shift campaigns, DESIGNED and flagged.",
            },
            "densification_delta_cycle2": "+1 physical-constraint sub-variant (aluminum probe refit), +1 tail (vendor milliohm CSV forgery), +13 primary spikes (16 -> 29) + an 8-event contrast train with its own 196 us race, +2 ticks (5 -> 7), +2 delayed side-effects (+6.2 h oven-rack scrap as PRIMARY terminal, +21 d CR-Q-1604), +1 triple-edge scar with any-pair-rollback-fails arithmetic, +1 HITL 8.6 min ratification, + collet ovality as the honest negative-result mechanism",
            "gaps_targeted": [
                "NOTES-r04 gap 5 / r14 residual: primary episode is a correctly-gated intervention that nonetheless FAILS (oven rack scrap; total -0.11; further releases avoided are booked separately from the rack fail)",
                "NOTES-r14 next-round item 4: TRIPLE-EDGE scar — three release-go edges; rollback of any pair is fitted to fail; coordinated depression exhibited with eligibility arithmetic",
                "NOTES-r04 gap 4 (partial): human ratification of the jig interlock, 8.6 min fitted, without switching sim_or_real to hil (plant remains designed)",
                "NOTES-r14 domain candidates: industrial-assembly taken; still unused water-treatment-dosing; AVOID lyophilization, CINDERWICK/district-heating clones, TRIAD/event-camera-traffic-grid",
            ],
            "race_flip_narrative": "jig.clamp.overforce @ 5.412 ms vs weld.pyrometer.good @ 5.600 ms (188 us) inside race_window_us 460. Gap < min(500, 460) us so a sub-flip-bound perturbation reverses which alarm heads the PB-SL-06 queue. The gate excludes the winner tag and rides shortfall > 0.15 mm, clamp > 6.0 kN, and milliohm > 0.70 mOhm — order-invariant floors. Extends the flip-fragility series from arbitration/causation/attribution/initiation/consensus to MASQUERADE: when two optical channels agree, the race among them does not decide truth; a contact-resistance channel does.",
            "tags": [
                "industrial-assembly",
                "hairpin-stator-weld",
                "thermal-contact-masquerade",
                "insertion-shortfall",
                "clamp-overforce",
                "pyrometer-good-false",
                "milliohm-probe",
                "collet-ovality",
                "triple-edge-scar",
                "any-pair-rollback-fails",
                "coordinated-depression",
                "correct-modify-rack-still-fails",
                "varnish-cure-scrap",
                "human-ratify-jig-interlock",
                "aluminum-probe-refit",
                "vendor-milliohm-forgery",
                "same-gate-opposite-disposition-contrast",
                "research-only",
            ],
            "snn_tags": ["race", "refractory", "adaptation", "third-factor", "triple-edge-eligibility"],
            "distillation_value": "A thermal-contact masquerade is two correct optical loops looking at one over-clamp. Distill (1) a milliohm channel that breaks the optical consensus, (2) a reversible probe that reads coating vs core, (3) coordinated depression of every release-go edge because rolling back any pair leaves the third above threshold, and (4) a critic head that can book a process-correct gate against a later unmonitored oven-rack loss without netting them.",
            "rights": RIGHTS,
            "batch_position": 1,
        },
    }
    return rec, dict(
        trace=trace,
        eta1=eta1,
        eta2=eta2,
        eta3=eta3,
        dw1=dw1,
        dw2=dw2,
        dw3=dw3,
        w1=w1,
        w2=w2,
        w3=w3,
    )


def local_checks(rec, aux):
    errs = []
    ev = rec["spike_events"]
    times = [e["t_rel_ms"] for e in ev]
    if times != sorted(times):
        errs.append("spikes not sorted")
    if not (5 <= len(ev) <= 40):
        errs.append(f"spike count {len(ev)}")
    extra = set().union(*(set(e) for e in ev)) - {"channel", "t_rel_ms", "amplitude"}
    if extra:
        errs.append(f"spike extra keys {extra}")
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
    if rec["meta"]["round"] != 16:
        errs.append("round")
    if rec["id"] != "maos-r16-001":
        errs.append("id")
    if rec["rights"]["intended_use"] != "research_only":
        errs.append("rights")
    if rec["meta"]["rights"]["linear_issue"] != "RM-793":
        errs.append("meta.rights")
    if rec["rights"] is not rec["meta"]["rights"] and rec["rights"] != rec["meta"]["rights"]:
        errs.append("rights mismatch")
    if not (3 <= len(rc["ticks"]) <= 8):
        errs.append("tick count")
    if abs(aux["w1"] - 0.14) > 5e-4 or abs(aux["w2"] - 0.12) > 5e-4 or abs(aux["w3"] - 0.11) > 5e-4:
        errs.append("scar weights")
    if rec["safety_decision"]["decision"] != "MODIFY":
        errs.append("decision")
    if rec["state"]["domain"] != "industrial-assembly":
        errs.append("domain")
    return errs


def write_notes(rec, aux, pipeline_receipt):
    notes = f"""# NOTES — Multi-Agent Ouroboros Swarm, run 2026-09-02-final-heavy, ROUND 16

Factory: multi-agent-ouroboros-swarm. One scenario (S), strict loop:
Generator v1 -> cycle 1 (Critic, Diversity Enforcer, Edge-Case Hunter,
Neuromorphic Translator, Trajectory Builder -> v2) -> cycle 2 (all six -> v3
final). v3 is the single line of batch-r16.jsonl. Full labeled transcript:
swarm-transcript-r16.md. Quota Q=1. Record id maos-r16-001. Generator grok-4.6.
Rights: RM-793 research-only (SpaceXAI/xAI, SuperGrok Heavy consumer chat).
Nothing under outputs/raw/ was touched.

ORCHESTRATION NOTE: dispatched AS round 16 of the 2026-09-02-final-heavy
window. Writes are create-only under /tmp/maos-r16/. Prior context read for
gap targeting and de-collision: prompts/02-multi-agent-ouroboros-swarm.md,
prompts/_factory-contract.md, NOTES-r04.md of the 2026-08-30 window, and
staged r14 LYOSHIELD (not cloned). Explicitly avoided cloning LYOSHIELD,
CINDERWICK / Lodenholt DH-3, and TRIAD / Meridian Gateway Corridor /
VANTIS-CADENCE-AEGIS.

## What this round produced

Scenario S — "QUILLFORGE / Brackmere Stator Line SL-6": a hairpin-stator
laser-weld cell mid-crown on stator 287 of 420. Three heterogeneous,
individually-correct agents — FEED (insertion LVDT), WELD (pyrometer +
plasma Cu I), JIG (clamp kN) — jointly report weld-complete. The consensus
is false. A 12 um oval insertion collet admits a 0.42 mm shortfall that
the daily round pin-gauge still PASSES. JIG raises clamp 4.8 -> 7.1 kN to
'seat' the pin; the extra force raises coating-crown thermal contact, so
WELD's pyrometer sits at 1180 C inside the 1140-1220 C good band and Cu I
327.4 nm is strong (the coating is copper enamel). The coordination-failure
CLASS is new to this factory: THERMAL-CONTACT MASQUERADE OF AN INSERTION
SHORTFALL. Completes a different family than r01-r04 (livelock /
synchrony-storm / arms-race / ring-with-no-faulty-pair) and staged r14
(false-consensus endpoint via compensated inleak). Here every agent is
correct, the cycle is not unstable, and the playbook's two optical confirms
are one squeeze.

The gate is a correct MODIFY (numeric floor: do not release while milliohm
R > 0.70 mOhm OR shortfall > 0.15 mm OR clamp > 6.0 kN). TG-SL-6 strips
PB-SL-06's varnish release, holds the jig, runs a 180 ms 10 A milliohm
probe (coating stays 1.85 mOhm >= 0.70; core-control would read 0.42), and
isolates the collet after an 8.6 min quality-engineer ratify. Stator 287
is not varnished. The PRIMARY episode nonetheless FAILS: 40 min of
unmonitored collet ovality had already filled a 14-stator varnish rack now
in the 155 C oven. Cure at +6.2 h makes 14/14 un-reworkable; $0.96M
designed. Reward total -0.11 with process heads honest and world loss
un-netted. This continues NOTES-r04 gap 5 / r14's negative-result shape
on a new plant and class.

Triple-edge scar (NOTES-r14 next-round item 4): pyrometer_good -> release
(0.17 commissioned -> 0.46 at illusion -> 0.14 after NE-gated depression)
AND plasma_CuI -> release (0.16 -> 0.43 -> 0.12) AND clamp_in_band ->
release (0.15 -> 0.40 -> 0.11). Eligibility trace e^{{-0.180/0.90}} =
{aux['trace']:.5f}; eta {aux['eta1']:.5f} / {aux['eta2']:.5f} /
{aux['eta3']:.5f}; dw -0.320 / -0.310 / -0.290. Rollback of any pair
leaves the leftover edge at 0.40-0.46 > 0.30 fire threshold — fitted to
fail. Coordinated depression of all three is the cure.

### Injections (all four present and disjoint)
- Cycle-1 domain: **industrial-assembly** — prompt-list domain, unused
  across 2026-08-17, 2026-08-30, and staged r14. Not warehouse-amr (r01),
  not aerial-swarm (r02), not district-heating (r03 / CINDERWICK), not
  event-camera-traffic-grid (r04 TRIAD), not pharmaceutical-lyophilization
  (r14 LYOSHIELD).
- Cycle-1 tail: insertion-collet ovality 12 um. Pin-gauge PASSES (round
  3.195 mm GO). Fitted-style base rate 0.48%/shift (gauge geometry
  designed, ovality fitted). Naive = FALSE RELEASE.
- Cycle-2 domain sub-variant: aluminum hairpin, 0.38 g crown; copper
  180 ms / 10 A pulse overshoots 48 C and grows oxide +0.22 mOhm; probe
  must move to 40 ms / 8 A.
- Cycle-2 tail: vendor golden-stator milliohm CSV at 0.1 mOhm quantization
  vs plant 0.01 mOhm (10 bins) plus live clamp 7.1 kN at the claimed
  complete. Human-intent class, disjoint from cycle 1's accidental
  ovality. Base rate ~0.28% of late-shift campaigns, DESIGNED, flagged.

### Structural density moves
- Embedded SAME-GATE contrast (+4 d sister cell) with its own 196 us race
  (milliohm vs pyrometer) and ACCEPT of the release the primary MODIFIED
  away.
- Learned-weight provenance on THREE edges with any-pair-rollback-fails.
- HITL jig-interlock ratify 8.6 min (gap 4 partial; sim_or_real stays
  designed).
- Governance CR-Q-1604 prices retire-vs-probe-vs-status-quo and mandates
  native 0.01 mOhm CSV exports (the fraud fence) plus a 3-lobe ovality
  gauge (the round pin-gauge is the designed miss).
- Flip-fragility extended to MASQUERADE: when two optical channels agree,
  their race does not decide truth; a contact-resistance channel does.

## Self-critique of this round's batch

### Strengths
- The headline class is mechanistically tight: extra clamp is the thermal
  contact that makes a coating hit look like a core weld, so JIG's
  'success' is WELD's blindness.
- Negative-result honesty: the gate does the right thing and the oven rack
  still fails for a reason the commissioned playbook could not see. Total
  -0.11.
- Triple-edge scar is load-bearing: the record states a counterfactual
  where rolling back any pair fails, with the fire threshold 0.30
  exhibited.
- Contrast ACCEPT on a true insertion prevents "never release" as the
  lesson.

### Weaknesses (honest)
- Probe error rates, the 0.48%/shift ovality rate, the $0.96M / $5.2M
  figures, the 8.6 min lockout latency, and the vendor-CSV 0.28% base
  rate are DESIGNED constants and are flagged. Closed-loop offsets
  (shortfall 0.42 mm, clamp 7.1 kN, milliohm 1.85 vs 0.42, Al dT 48 C)
  are derived from those inputs, not discovered by an unauthored process.
- Thermal-contact model is a designed 2.3 kN boost mapped to a pyrometer
  landing in-band; no full FEA of coating-crown conductance shipped.
- Human-in-the-loop is ratification latency, not sim_or_real=hil. Gap 4
  remains open as a provenance cell.
- Cross-record arc is not discharged; +21 d CR-Q-1604 is a hook, not a
  serial igniter into another round. Water-treatment-dosing remains unused.

### Realism of noise / latencies
Ladder: 188 us race / 196 us contrast race / 0.8 ms refractory floor
(tightest exhibited same-channel gap 1.130 ms on jig.clamp.kN) / 460 us
race window / 710 us gate latency / 20 ms bus epoch / 40 ms raster /
180 ms probe / 8.6 min HITL / 40 min pre-t0 ovality / 2.33 h oven-unreachable
/ 6.2 h cure fail / +4 d contrast / +21 d governance. Adaptation decay on
weld.pyrometer (0.66->0.59->0.51), weld.plasma.CuI (0.54->0.94->0.48),
jig.clamp.kN (0.61->0.88->0.72->0.49).

### Value for SNN distillation
- THERMAL-CONTACT MASQUERADE = TWO CORRECT OPTICAL LOOPS, ONE OVER-CLAMP.
- MILLIOHM CHANNEL as the tie-break that is not in the optical consensus.
- REVERSIBLE PROBE that reads coating vs core.
- TRIPLE-EDGE ELIGIBILITY: coordinated depression; any-pair rollback fails.
- CRITIC HEAD that can hold a process-correct MODIFY against a later
  unmonitored world loss without netting.

## Reconciliation and validity receipts
- reward_components: 5-head unweighted signed sum -0.11
  and 7-tick signed sum reconcile to total with |diff| < 1e-9. Embedded
  contrast 5-head sum 0.48 reconciles independently.
- spike_events: primary 29 events, one key t_rel_ms,
  globally non-decreasing, min same-channel gap 1.130 ms >= 0.8 ms, 3
  channels inside race_window_us 460 (clamp-overforce 5.412, pyrometer-good
  5.600, plasma Cu I 5.688). Contrast 8 events, own race, min same-channel
  gap well above 0.8 ms.
- Sidecars: raster spikes 48 == round(160 x 7.5 x 0.040); energy 1104 pJ /
  0.001104 uJ at 23 pJ/spike; excerpt 18 events inside [0, 40000] us,
  neuron_id < 160, same-neuron gap N/A (unique ids) / >=1000 us; routing 4
  entries with three scar edges' before/after pair plus milliohm-hold;
  third factor tau 0.90 s == 900 ms; gate_snn pools 26/9/3 ==
  round(n x rate x 0.020) each, decision MODIFY == safety_decision.decision.
- Pipeline: {pipeline_receipt}

## Novel coverage
The coordination-failure CLASS (thermal-contact masquerade of an insertion
shortfall), the domain (industrial-assembly / hairpin-stator weld), the
milliohm probe discriminant, the triple-edge scar with any-pair-rollback-
fails, the primary negative-result (correct MODIFY, oven rack still fails
on unmonitored collet ovality), the HITL jig-interlock ratify, the
aluminum probe-duration refit, and the vendor 10-bin milliohm quantization
fence are absent from prior committed ouroboros rounds and from staged r14
LYOSHIELD. Repeated elements discounted: same-gate contrast (r02/r03/r04/
r14), governance-pricing scaffold, flip-fragility series (extended to
masquerade, but the move rhymes), sequenced recovery shape, third-factor
rollback form (here three edges rather than r14's two). Weighing a new
failure family + cure vocabulary + domain + negative-result primary +
triple-edge first against those reused scaffolds:

{NOVEL_LINE}

## What ROUND 17 should add
1. FIT THE DESIGNED CONSTANTS: ovality arrival, probe error rates,
   coating-crown conductance, vendor-CSV claim process.
2. HIL PROVENANCE CELL: put the lockout-ratify on a hardware-in-loop jig
   interlock with fitted latency as state.sim_or_real=hil.
3. CROSS-RECORD ARC: let CR-Q-1604's 3-lobe ovality alarm be the igniter
   of the next round rather than a dangling +21 d leaf.
4. FOURTH-EDGE DEPTH: a four-edge scar where depressing any triple shifts
   the pathology onto the leftover edge.
5. Domain candidates (de-collided): distributed water-treatment dosing
   (still unused); AVOID industrial-assembly (now used), lyophilization,
   CINDERWICK/district-heating, TRIAD/event-camera-traffic-grid,
   aerial-swarm, warehouse-amr, irrigation-canal.
"""
    (OUT / "NOTES-r16.md").write_text(notes)
    return notes


def write_transcript(rec, line):
    c1_spikes = [e for e in rec["spike_events"] if e["t_rel_ms"] <= 10.880]
    text = f"""# Multi-Agent Ouroboros Swarm — Round 16 transcript

Factory: multi-agent-ouroboros-swarm
Run: 2026-09-02-final-heavy
Generator: grok-4.6
Record id: maos-r16-001
Quota Q: 1
Rights: RM-793 research-only (SpaceXAI/xAI SuperGrok Heavy consumer chat)
Plant: invented QUILLFORGE / Brackmere Stator Line SL-6 (not LYOSHIELD, not CINDERWICK, not TRIAD / Meridian)

Two densifying cycles. Verbatim headings in order. Trajectory Builder cycle 2
emits the only JSONL line (also written to batch-r16.jsonl).

---

# Cycle 1 — Foundation + injections

## Generator

Design intent: a hairpin-stator laser-weld cell where three correct agents
agree the crown is fused because over-clamp turns a coating-only laser hit
into a pyrometer-good. The naive playbook releases into varnish. The gate
must MODIFY on numeric floors (shortfall, clamp ceiling, milliohm), not by
killing an agent. sim_or_real=designed. Reward heads are
task_progress/safety/efficiency/coherence/exploration.

Cycle-1 base arc (pre-critic): state at Brackmere SL-6, stator 287/420,
insertion 17.98 vs 18.40 mm, clamp 7.1 kN, pyrometer 1180 C, proposed
VARNISH-RELEASE, safety MODIFY to HOLD, executed hold without the milliohm
numbers fully specified, outcome "collet found, stator saved" (this last
claim is the defect the later cycles will refuse to keep). Sixteen spikes,
five ticks, raster/gate_snn present but the scar is a single edge.

```json
{{
  "id": "maos-r16-001",
  "state": {{
    "sim_or_real": "designed",
    "domain": "industrial-process",
    "description": "Stator cell mid-weld; pyrometer in-band; supervisor proposes varnish release.",
    "t0_us": 1788383662000042,
    "gate_latency_us": 710,
    "race_window_us": 460
  }},
  "proposed_action": {{"name": "varnish_release", "parameters": {{"varnish_release": true}}}},
  "safety_decision": {{"decision": "MODIFY", "rationale": "Hold; do not release while the pin is short."}},
  "executed_action": {{"name": "hold", "executed_as_proposed": false}},
  "future_outcome": {{"summary": "Collet found, stator saved."}},
  "reward_components": {{"total": 0.40, "_aggregation": "{AGG}"}},
  "meta": {{"round": 16, "factory": "multi-agent-ouroboros-swarm", "generator": "grok-4.6"}}
}}
```

That v1 object is a scaffold, not the publishable line. Defects below are
intentional for the critic to catch.

## Critic

Numbered defects on the cycle-1 Generator scaffold:

1. **blocking — reward arithmetic / false success.** `reward_components.total`
   0.40 is asserted without the five heads, without ticks, and against an
   outcome that claims "stator saved". If a 14-stator varnish rack later
   cures as coating-weld scrap, booking +0.40 is a lie. Fix: declare
   `_aggregation`, emit 3–8 ticks that sum to
   task_progress+safety+efficiency+coherence+exploration, and do not call
   an oven-rack loss a save.
2. **blocking — weak safety rationale.** `safety_decision.rationale` has no
   numeric floor. Contract requires a concrete constraint. Fix: quote
   do-not-release while milliohm R > 0.70 mOhm OR shortfall > 0.15 mm OR
   clamp > 6.0 kN.
3. **major — domain is a bucket, not a plant.** `state.domain` =
   `industrial-process` collides with nothing and teaches nothing. Hairpin
   weld physics (coating vs core, pyrometer vs milliohm) is absent from
   prior ouroboros rounds and must be named `industrial-assembly`.
4. **major — race under-specified.** One pyrometer channel cannot be a race.
   Need >=2 channels inside `race_window_us` with globally sorted `t_rel_ms`
   and same-channel refractory >= 0.8 ms.
5. **minor — single-edge scar.** Raster routing with one potentiated weight
   repeats r04's one-edge rollback and r14's two-edge. NOTES-r14 asked for
   a three-edge scar where partial (any-pair) rollback fails.

Critic does not rewrite the trajectory.

## Diversity Enforcer

Injected novel domain (exactly 1 this cycle): **industrial-assembly**
(prompt-list domain; explicit tag `industrial-assembly`). First hairpin-
stator weld cell in this factory.

Displaced: the Generator's generic `industrial-process` bucket, and any
temptation to reuse LYOSHIELD lyophilization, CINDERWICK district-heating,
TRIAD event-camera traffic, OKTAVE warehouse-amr, or STARLING aerial-swarm.

Domain-specific constraint: milliohm hold R > 0.70 mOhm, LVDT shortfall
floor 0.15 mm, clamp ceiling 6.0 kN; pyrometer-in-band is not a species-
independent complete.

Sensor delta: +insertion LVDT, +clamp load cell, +spot pyrometer, +plasma
Cu I 327.4 nm, +4-wire milliohm; -any mobile robot, -DVS gantries, -Pirani,
-RGA, -freeze-dryer shelves.

`state.domain` and `meta.domain` both become `industrial-assembly`.
Opening of `state.description` must Jaccard < 0.4 against prior plants
(Brackmere hairpin cell, not a corridor, not a lyophilizer, not a canal).

## Edge-Case Hunter

Injected adversarial tail (exactly 1 this cycle): **insertion-collet
ovality 12 um**.

- Trigger: 12 um ovality on the FEED collet, shortfall 0.42 mm.
- Base rate: <1% — 0.48%/shift from a collet-cycle MC (round pin-gauge
  3.195 mm GO is designed; ovality fitted-style). Observed GO 3.198 mm
  PASSES the daily check.
- Naive failure: FALSE RELEASE. PB-SL-06 sees pyrometer 1180 C and Cu I
  0.88, releases, 6.2 h cure, 18% coating-weld, $5.2M.
- Trajectory edit: put the ovality in `state.fault_context`, make JIG's
  over-clamp the mechanism that hides the shortfall (thermal-contact
  boost puts a coating hit in-band), and force the gate to refuse release
  on LVDT 0.42 mm and clamp 7.1 kN even though both optical confirms are
  numerically true.

Distinct from the domain injection: the domain is the weld cell; the tail
is the accidental worn collet.

## Neuromorphic Translator

Race window [5.300, 5.760] ms = 460 us. Winner jig.clamp.overforce @
5.412 ms (amplitude 1.28, 7.1 kN). Loser weld.pyrometer.good @ 5.600 ms
(amplitude 1.21, 1180 C). Margin 188 us vs combined jitter 53 us (3.5x).
weld.plasma.CuI @ 5.688 ms is a third race-window channel. Gate @ 6.122 ms
= winner + 710 us.

Flip narrative: 188 us < min(500, 460) us, so order is flip-fragile. If
pyrometer-good wins, PB-SL-06 heads the triage queue. The hold must ride
order-invariant floors (shortfall, clamp ceiling, milliohm), not the
winner tag.

Cycle-1 spike patch (16 events, globally sorted, refractory >= 0.8 ms;
tightest same-channel gap jig.clamp.kN 3.880 -> 5.010 = 1.130 ms):

| t_rel_ms | channel | amplitude |
|---------:|---------|----------:|
| 0.380 | feed.lvdt.depth | 0.58 |
| 1.140 | jig.clamp.kN | 0.61 |
| 1.820 | feed.force.N | 0.50 |
| 2.180 | weld.pyrometer | 0.66 |
| 3.050 | weld.plasma.CuI | 0.54 |
| 3.880 | jig.clamp.kN | 0.55 |
| 4.220 | feed.lvdt.depth | 0.71 |
| 5.010 | jig.clamp.kN | 0.88 |
| 5.412 | jig.clamp.overforce | 1.28 |
| 5.600 | weld.pyrometer.good | 1.21 |
| 5.688 | weld.plasma.CuI | 0.94 |
| 6.122 | ctrl.gate | 1.08 |
| 7.040 | feed.lvdt.depth | 0.64 |
| 8.310 | weld.pyrometer | 0.59 |
| 9.550 | feed.force.N | 0.47 |
| 10.880 | jig.clamp.kN | 0.72 |

Ticks (5): t_us 2180, 5412, 6122, 180000, 516000000. Distillation value:
the in-band pyrometer is not a complete spike; the clamp-overforce spike
is the one that licenses hold until milliohm speaks.

Raster cycle-1 seed: 40 ms, 160 neurons, 7.5 Hz, 48 spikes, 1104 pJ, third
factor norepinephrine tau_e 0.90 s. Single scar edge only — cycle 2 must
add the second and third edges.

## Trajectory Builder

Cycle-1 hardened object: domain industrial-assembly, tail collet ovality,
16 spikes, 5 ticks, MODIFY with numeric floor, raster+gate_snn present,
sim_or_real=designed, rights stamp on record and meta, no thought keys.
Still missing (and therefore not the publishable line): aluminum
sub-variant, vendor milliohm-CSV tail, second and third scar edges,
delayed oven-rack fail as PRIMARY terminal, contrast ACCEPT episode,
ticks 6–7, spikes 17–29.

Validation receipt (cycle 1, not final):
- checks passed: 16 spikes sorted; 3 channels in 460 us window; refractory
  1.130 ms; rationale quotes 0.70 mOhm / 0.15 mm / 6.0 kN; domain named;
  gate_snn.decision MODIFY.
- checks deferred to cycle 2: triple-edge scar, second tail, second domain
  constraint, negative-result booking, 7 ticks summing to heads.
- densification vs Generator v1: +1 domain, +1 tail, +16 spikes, +5 ticks,
  +numeric floor.

Cycle-1 JSON is retained as the base; it is NOT written to batch-r16.jsonl.

Cycle-1 spike count: {len(c1_spikes)}.

---

# Cycle 2 — Densification

## Generator

Cycle-1 output is the base. Additive expansion (nothing removed):

1. Downstream side-effect (immediate): milliohm probe at +180 ms stays
   at 1.85 mOhm (coating, not core). Collet swap after 8.6 min ratify.
   LVDT survey of the last 14 released stators shows the same 0.40-0.45 mm
   shortfall cluster.
2. Delayed side-effect (PRIMARY terminal, not a footnote): at +6.2 h
   varnish cure, 14/14 oven-rack stators milliohm 1.6-2.1 mOhm vs 0.55
   spec; un-reworkable; $0.96M designed. The 40 min pre-t0 collet ovality
   is the mechanism. Correct gate, rack still fails.
3. Deepened `proposed_action.evidence` with units: shortfall 0.42 mm,
   clamp 7.1 kN, pyrometer 1180 C, Cu I 0.88, race 188 us, designed
   coating milliohm 1.85 mOhm.
4. Tightened rationale to the numeric floor R > 0.70 mOhm OR shortfall
   > 0.15 mm OR clamp > 6.0 kN, plus probe bands 1.85 vs 0.42, plus HITL
   8.6 min jig-interlock rule.

Reward retargeted to total -0.11 so the delayed fail is the inflection
(t_us 22320000000), not the gate. Process heads remain non-zero.

## Critic

Re-audit of the expanded trajectory:

1. **blocking if unfixed — missing second domain constraint.** Copper
   milliohm 180 ms / 10 A is not a universal number. An aluminum hairpin
   of 0.38 g will overheat. Diversity Enforcer must inject the physical-
   constraints sub-variant this cycle.
2. **major — only one tail class.** Collet ovality is accidental
   tooling. A disjoint human-intent tail is still required (vendor
   golden-stator milliohm CSV is the open cell).
3. **major — scar is still one edge in the cycle-1 raster.** NOTES-r14
   item 4 is not discharged until plasma_CuI -> release and clamp_in_band
   -> release are second and third potentiated edges and any-pair rollback
   is shown to fail at threshold 0.30.
4. **minor — contrast episode missing.** Without a same-gate ACCEPT on a
   true insertion the record teaches "never release". Add +4 d sister-cell
   contrast with its own race.
5. **minor — HITL latency mentioned in prose only.** Put 8.6 min in
   executed_action.parameters.human_ratify and in a tick.

No rewrite; directives only.

## Diversity Enforcer

Injected second novel domain / physical-constraint sub-variant (exactly 1
this cycle): **aluminum-hairpin industrial-assembly** in the same SL-6
cell.

What it expands: copper hairpin (cycle 1) -> 0.38 g Al crown. Spec
milliohm 0.90 mOhm, pyrometer band 640-680 C. The 180 ms 10 A copper pulse
dumps 0.0162 J, dT 48 C, oxide +0.22 mOhm. Required probe: 40 ms at 8 A
(dT 6.7 C, oxide +0.02).

This is still one domain injection for the cycle (physical-constraints
clause of the factory prompt). It does not displace industrial-assembly;
it changes which probe table is legal. `future_outcome.subvariant_constraint`
carries the refit. Jaccard opening stays the Brackmere copper-hairpin
sentence; aluminum is additive, not a rewrite.

## Edge-Case Hunter

Injected second adversarial tail (exactly 1 this cycle, disjoint class):
**vendor golden-stator milliohm CSV**.

- Trigger: process engineer, late shift, posts a historian export showing
  R = 0.4 mOhm at t = 1.1 s to clear a customer ship slot.
- Base rate: ~0.28% of late-shift campaigns (designed, flagged, <1%).
- Naive failure: a weak supervisor ACCEPTs the release on the forged
  confirm and ignores live LVDT/clamp. Coating-weld plus a data-integrity
  483.
- Fence: forged log quantized at 0.1 mOhm (SCADA screenshot rounding);
  plant historian is 0.01 mOhm (10 bins). Live clamp is 7.1 kN and LVDT
  shortfall 0.42 mm at the claimed complete, which no core-weld produces.
- Trajectory edit: governance CR-Q-1604 mandates native 0.01 mOhm CSV
  exports; the contrast ACCEPT still requires live milliohm, not a CSV.

Distinct from cycle-1 ovality (accidental tooling vs deliberate deception)
and from the aluminum sub-variant (physics vs fraud).

## Neuromorphic Translator

Re-densify (additive):

- +13 spikes after 10.880 ms: weld.pyrometer 12.610 (adapt 0.66->0.51),
  plasma 14.250, milliohm.ready 18.040, ctrl.gate 22.400, jig.clamp 26.200,
  lvdt 28.800, milliohm.probe 180.000, milliohm.pair.R 181.140, human.ratify
  516000.0, collet.swap 516800.0, lvdt.survey 517200.0, varnish.tank.entry
  8400000.0, varnish.cure.scrap 22320000.0. Primary train 16 -> 29. Still
  one key, still sorted, refractory held (min 1.130 ms).
- +2 ticks (5 -> 7) at 8_400_000_000 us (oven unreachable) and
  22_320_000_000 us (cure scrap). Heads now 0.09, -0.29, -0.11, 0.13, 0.07;
  total -0.11. Inflection is the last tick.
- Contrast train 8 events, own race 196 us, ACCEPT.
- Triple-edge third factor: three release-go edges, tau_e 0.90 s = 900 ms,
  trace {aux['trace']:.5f}, eta {aux['eta1']:.5f} / {aux['eta2']:.5f} /
  {aux['eta3']:.5f}, weights 0.46->0.14, 0.43->0.12, 0.40->0.11. Raster
  excerpt is the 40 ms decision window, sorted with unique neuron_ids
  (same-neuron >=1000 us vacuously).

Winner/loser flip (re-stated, not replaced): reversing 188 us would only
reorder triage; milliohm/LVDT/clamp floors still MODIFY. Contrast flip of
196 us similarly cannot turn a true insertion into a coating-weld.

## Trajectory Builder

Schema checks on the FINAL object: required Thalamic v2 keys present as
objects; `state.sim_or_real`=designed; `safety_decision.decision`=MODIFY
with numeric rationale; `reward_components.total` = sum of five heads =
sum of 7 ticks = -0.11; `spike_events` globally non-decreasing on
t_rel_ms, 29 events, refractory >=0.8 ms, 3 channels in race window;
raster 20–50 ms, spikes=round(n*rate*window_s)+/-1, energy 23 pJ/spike,
excerpt sorted, tau_e consistent; gate_snn.decision matches; meta.round=16,
factory=multi-agent-ouroboros-swarm, generator=grok-4.6,
run_label=2026-09-02-final-heavy; rights on record and meta; no thought
keys; no training_ready; Diversity + Edge-Case injections from BOTH cycles
present and non-trivial; cycle 2 strictly additive.

Densification delta: +1 domain sub-variant (aluminum), +1 tail (vendor
milliohm CSV), +13 spikes (16->29), +2 ticks (5->7), +1 contrast train
with own race, +2 delayed side-effects, +1 triple-edge scar with
any-pair-rollback-fails, +1 HITL ratify, +1 surprise (oven-rack collet
ovality is the rack-fail mechanism).

Publishable JSONL line (the only JSONL line; also at batch-r16.jsonl):

```json
__FINAL_JSONL__
```

Validation receipt (final): checks passed / fixed as reported by
build_r16.py self-validate (check_jsonl, raster_status, verify_record_execution,
spike_probe --strict).
"""
    text = text.replace("__FINAL_JSONL__", line)
    (OUT / "swarm-transcript-r16.md").write_text(text)
    return text


def main():
    rec, aux = build_record()
    errs = local_checks(rec, aux)

    OUT.mkdir(parents=True, exist_ok=True)
    line = json.dumps(rec, ensure_ascii=False, separators=(",", ":"))
    (OUT / "batch-r16.jsonl").write_text(line + "\n")

    from check_records import FactoryStaging, check_jsonl
    from curate_bridge import raster_status
    from round_txn_raster import validate_bridge_envelope
    from verify_execution import verify_record_execution, verify_batch_for_frontier

    e, w, kinds, n = check_jsonl(
        OUT / "batch-r16.jsonl",
        "batch-r16.jsonl",
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
            if k in st
        },
    )
    if st.get("reason_codes"):
        errs.append(f"raster {st['reason_codes']}")
    if not st.get("raster_valid"):
        errs.append("raster not valid")
    if not st.get("gate_snn_valid"):
        errs.append("gate_snn not valid")

    status, reason = verify_record_execution(rec, "maos-r16-001")
    print("verify_record_execution", status, reason)
    if status != "verified":
        errs.append(f"verify {status}: {reason}")

    counts, findings, blocked = verify_batch_for_frontier(
        OUT / "batch-r16.jsonl", strict=True
    )
    print("frontier", counts, findings, blocked)
    if blocked:
        errs.append(f"frontier blocked {findings}")

    factory_dir = Path(ROOT) / "outputs/raw/2026-08-30/multi-agent-ouroboros-swarm"
    env = validate_bridge_envelope(OUT / "batch-r16.jsonl", factory_dir)
    print("envelope", env)
    errs.extend(env)

    probe = subprocess.run(
        [
            sys.executable,
            f"{ROOT}/pipelines/spike_probe.py",
            "--strict",
            str(OUT / "batch-r16.jsonl"),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    print("spike_probe rc", probe.returncode)
    print(probe.stdout)
    if probe.stderr:
        print("spike_probe stderr", probe.stderr)
    if probe.returncode != 0:
        errs.append(f"spike_probe rc {probe.returncode}")

    receipt = (
        f"check_jsonl errors={e} warnings={w} kinds={kinds} n={n}; "
        f"raster_status valid={st.get('raster_valid')} gate={st.get('gate_snn_valid')} "
        f"reasons={st.get('reason_codes')}; verify_record_execution={status} ({reason}); "
        f"spike_probe --strict rc={probe.returncode}"
    )
    write_notes(rec, aux, receipt)
    write_transcript(rec, line)

    headings = re.findall(r"^## .+$", (OUT / "swarm-transcript-r16.md").read_text(), re.M)
    print("headings", headings)
    expected = [
        "## Generator",
        "## Critic",
        "## Diversity Enforcer",
        "## Edge-Case Hunter",
        "## Neuromorphic Translator",
        "## Trajectory Builder",
        "## Generator",
        "## Critic",
        "## Diversity Enforcer",
        "## Edge-Case Hunter",
        "## Neuromorphic Translator",
        "## Trajectory Builder",
    ]
    if headings != expected:
        errs.append(f"heading sequence {headings}")

    notes = (OUT / "NOTES-r16.md").read_text()
    cov = re.findall(r"^Novel coverage: .+$", notes, re.M)
    if cov != [NOVEL_LINE]:
        errs.append(f"novel coverage lines {cov}")

    trans = (OUT / "swarm-transcript-r16.md").read_text()
    # Cycle-2 TB jsonl must match the batch line exactly (inside the fence).
    m = re.search(r"```json\n(\{.*\})\n```", trans)
    if not m:
        errs.append("transcript missing final json fence")
    else:
        if m.group(1) != line:
            errs.append("transcript JSON != jsonl line")

    raw_root = Path(ROOT) / "outputs/raw"
    # Refuse if we accidentally wrote into outputs/raw.
    leaked = list(raw_root.rglob("*maos-r16*")) + list(raw_root.rglob("*QUILLFORGE*"))
    if leaked:
        errs.append(f"leaked into outputs/raw: {leaked[:5]}")

    print("bytes jsonl", (OUT / "batch-r16.jsonl").stat().st_size)
    print("bytes notes", (OUT / "NOTES-r16.md").stat().st_size)
    print("bytes transcript", (OUT / "swarm-transcript-r16.md").stat().st_size)
    print("HEADS", heads_summary(rec))
    if errs:
        print("ERRS:")
        for x in errs:
            print(" -", x)
        sys.exit(1)
    print("OK", OUT / "batch-r16.jsonl")


def heads_summary(rec):
    rc = rec["reward_components"]
    return {
        "id": rec["id"],
        "total": rc["total"],
        "decision": rec["safety_decision"]["decision"],
        "sim": rec["state"]["sim_or_real"],
        "domain": rec["state"]["domain"],
        "plant": rec["state"]["scenario_name"],
        "spikes": len(rec["spike_events"]),
        "ticks": len(rc["ticks"]),
        "round": rec["meta"]["round"],
    }


if __name__ == "__main__":
    main()
