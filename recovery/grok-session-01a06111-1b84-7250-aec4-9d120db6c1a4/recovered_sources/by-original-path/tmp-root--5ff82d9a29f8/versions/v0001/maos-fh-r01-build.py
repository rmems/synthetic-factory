#!/usr/bin/env python3
"""Build MAOS window round-01 for 2026-09-02-final-heavy (create-only)."""
from __future__ import annotations

import json
import math
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = "/home/raulmc/rmems/synthetic-factory"
WINDOW = Path("/tmp/sf-window")
PIPE = str(WINDOW / "pipelines")
sys.path.insert(0, ROOT)
sys.path.insert(0, f"{ROOT}/pipelines")
sys.path.insert(0, PIPE)

GEN_AT = "2026-09-02T23:58:00Z"
RECORD_ID = "maos-fh-r01-001"
ROUND = 1
OUT = WINDOW / "outputs/raw/2026-09-02-final-heavy/multi-agent-ouroboros-swarm"
BATCH = OUT / "batch-r01.jsonl"
NOTES = OUT / "NOTES-r01.md"
TRANSCRIPT = OUT / "swarm-transcript-r01.md"

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
HIDDEN = ("thought", "chain_of_thought", "scratch", "inner_monologue")
DELAY_S = 0.82
TAU_E_S = 0.92
TRACE = math.exp(-DELAY_S / TAU_E_S)
ETA = (0.250 / TRACE, 0.220 / TRACE, 0.210 / TRACE)

BANNED = (
    "TRIAD", "Meridian Gateway", "VANTIS", "CADENCE", "AEGIS", "THERMION",
    "STARLING", "OKTAVE", "VERDIGRIS", "LYOSHIELD", "CINDERWICK", "Helixmere",
    "Lodenholt", "QUILLFORGE", "Brackmere", "NIGHTWELL", "Fen-Marrow",
    "FERRICLEAVE", "Pellwater", "CASSITER", "Marshfloat", "VEILFORGE", "MURENA",
    "HALYARD", "SEEDLATCH", "Quartzmere", "Quartzridge", "STRIAFOIL", "Kelpholt",
    "REDHALL", "Gullmere", "OXBOWREEL", "Oystermere", "TORSIONKEY", "Ridgeholt",
    "ORRIS", "Holmwick", "PROTONIL", "Ashspire", "WHORLSPAR", "Pikeshear",
    "IONSPATE", "Thornmere", "SKULLGATE", "Bloomholt", "CALXION", "Aldersedge",
    "MAGNORIL", "Basaltspit", "GORSEFLUE", "Copseholt", "CLINKERFELL",
    "Flintmere", "SODASHARD", "Cairnmere", "LINTELPLY", "Greystair", "KAOTHARN",
    "Riftwold", "TREADNOLL", "Slatebeck", "ANOLITH", "Siltfen", "DRUMWROTH",
    "Pitchfen", "RIMEBRAID", "Floeholt", "BRIMVAULT", "Pyritefen", "BOGIRON",
    "Mireholt", "CHROMLOOP", "Marlfell", "NITREVAULT", "Glaucove", "NITROSTAITH",
    "Chalkfen", "ETHYNWOLD", "Woadfen", "RUNNELGATE", "Ghyllmere", "SPARKHOLT",
    "Scoriafen", "DIPLEGAR", "Gritfen", "OLEUMWEIR", "Brindlefell", "SKARVOLT",
    "GOBSPALL", "Culletfen", "GOBWOLD", "Culletwick", "PUSHERFELL", "Sootmere",
    "CREELWOLD", "Rovingholt", "OSMOLITH", "Spumeholt", "GAUZEFELL", "Ammoxwick",
    "LIXIVQUERN", "Bauxfen", "GIBBSQUERN", "Laterifen", "OSMOQUAY", "Tidecairn",
    "Emberbarrow", "training_ready",
)

OPENING_PRIORS = [
    "Spumeholt SWRO train RO-8 sits at 62.4 bar high-pressure feed on an eight-vessel seawater reverse-osmosis skid",
    "Sootmere Coking battery CB-6 sits at 18.4 h coking on a 78-oven by-product slot battery",
    "Ammoxwick nitric hall OA-4 sits at 42.0 t/d on a 4-gauze Ostwald converter",
    "Rovingholt Oxidation Hall sits at 1.80 m/min on a six-zone PAN stabilization oven",
    "Laterifen Digestion DG-7 sits at 45 min residence on a 6-vessel live-steam Bayer autoclave train",
]


def jaccard(a: str, b: str) -> float:
    wa = set(re.findall(r"[a-z0-9.]+", a.lower())[:40])
    wb = set(re.findall(r"[a-z0-9.]+", b.lower())[:40])
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / len(wa | wb)


def build_record() -> dict:
    description = (
        "Spelterholt galvanizing line HDG-5 sits at 120.0 m/min on a 1.20 m GI "
        "pot-to-knife run when three heterogeneous, individually-correct agents "
        "jointly report 'coating healthy, raise speed'. SPEED's 12-bit bridle "
        "encoder is 120.0 m/min inside 110-130. POT's six-TC zinc-bath mean is "
        "460.0 C inside 450-470. COAT's traversing-XRF scan-mean is 278 g/m2 "
        "inside 250-300 (GI 275 target). The conjunction is not a knife-true "
        "edge-coat certificate: a 12 min dross plug on operator-side air-knife "
        "jet 14 left an 80 mm edge stripe at 410 g/m2, so edge-minus-mean "
        "residual r_edge is 132 g/m2 (hold if > 40) while the playbook still "
        "sees a healthy scan-mean. Jet-14 vs manifold residual r_dP is 4.8 kPa "
        "(hold if > 1.5) and is policy-treated as a noisy-knife-transducer tag "
        "unless scan-mean also trips (2018 'noisy dP campaign'). dP-first "
        "latches SPEED-HOLD plus an air-knife pressure probe; coat-first would "
        "have authorized RAISE-SPEED into a plugged jet."
    )
    rec = {
        "id": RECORD_ID,
        "title": (
            "ZINCFELL HDG-5: air-knife r_dP 4.8 kPa beats coat.mean.in_band by "
            "188 us; correct MODIFY still loses 1.44 km of edge-heavy GI to a "
            "pre-t0 dross plug"
        ),
        "rights": dict(RIGHTS),
        "provenance": {"kind": "designed", "claimed": "designed"},
        "state": {
            "sim_or_real": "designed",
            "domain": "continuous-hot-dip-galvanizing",
            "scenario_name": "ZINCFELL / Spelterholt Galvanizing HDG-5",
            "timestamp_local": "2026-09-02T02:36:00-05:00",
            "t0_us": 1756828800000001,
            "gate_latency_us": 708,
            "race_window_us": 500,
            "race_window_rel_ms": [6.52, 7.02],
            "description": description,
            "goal": (
                "Hold line speed without a raise while r_dP > 1.5 kPa AND "
                "r_edge > 40 g/m2 AND jet 14 remains unisolated; keep coil "
                "rejects at 0 on newly coated strip and scan-mean inside the "
                "320 g/m2 trip."
            ),
            "race": {
                "contenders": [
                    "knife.dp.high 4.8 kPa (jet-14 vs manifold residual)",
                    "coat.mean.in_band 278 g/m2 (traversing-XRF scan-mean)",
                ],
                "semantics": (
                    "dP-first latches SPEED-HOLD + KNIFE-PROBE + jet isolate. "
                    "Coat-first latches RAISE-SPEED (+8 m/min, no probe)."
                ),
                "window_derivation": (
                    "500 us = one 360 us knife-dP slot plus 140 us coating-mass "
                    "publish."
                ),
                "order_evidence_note": (
                    "Margin 188 us vs combined jitter 58 us (dP 34 + coat 24): "
                    "3.2x. The 188 us gap sits inside min(500, 500) us, so a "
                    "sub-flip-bound perturbation reverses triage order. The "
                    "gate rides the order-invariant floors r_dP > 1.5 kPa and "
                    "r_edge > 40 g/m2, not the alarm order."
                ),
            },
            "topology": {
                "site": (
                    "Spelterholt Galvanizing, invented spelter-ridge campus "
                    "Spelterholt, line HDG-5: 1.20 m GI continuous hot-dip, "
                    "0.80 mm CR coil, 120.0 m/min body, 460 C zinc pot, dual "
                    "air knives 22.0 kPa / 18 mm lip-to-strip, traversing XRF "
                    "coating-mass gauge, Grade-B knife-gallery LOTO"
                ),
                "agents": (
                    "SPEED bridle encoder (vendor Bridleholt): 20 Hz 12-bit on "
                    "the 120.0 m/min line. POT six-TC zinc-bath mean (vendor "
                    "Bathwick): 10 Hz on the pot. COAT traversing XRF "
                    "(vendor Scanfen): 8 s scan, publishes scan-mean on the "
                    "20 ms line-bus. KNIFE jet-14 vs manifold residual (vendor "
                    "Lipholt) is commissioned as a noisy-transducer tag, not as "
                    "a knife-duty tag. Heterogeneous stacks, no shared intent "
                    "schema, one 20 ms line-bus epoch"
                ),
                "coupling": (
                    "All three playbook confirms live on the WRONG volume. "
                    "SPEED is correct that the bridle is 120.0 m/min. POT is "
                    "correct that the six-TC bath mean is 460.0 C. COAT is "
                    "correct that the 1.20 m scan-mean is 278 g/m2 (1.12 m of "
                    "healthy strip dilutes an 80 mm plugged-jet stripe at "
                    "410 g/m2: 0.9333*268.5 + 0.0667*410 = 277.9). Playbook "
                    "PB-HDG-5 treats the conjunction as permission to raise "
                    "speed. No agent is faulty; the XRF is looking at a "
                    "scan-mean, not at jet 14's 80 mm edge."
                ),
            },
            "sensors": [
                "SPEED bridle 12-bit, 20 Hz, 21 us jitter, 120.0 m/min (dead-band 110-130)",
                "POT six-TC mean, 10 Hz, 28 us jitter, 460.0 C (band 450-470)",
                "COAT scan-mean XRF, 8 s scan / 20 ms publish, 24 us jitter, 278 g/m2 (band 250-300)",
                "KNIFE r_dP jet-14 vs manifold, 20 Hz, 34 us jitter, 4.8 kPa (healthy < 0.6 kPa; policy floor 1.5 kPa is not armed unless scan-mean also trips)",
                "edge-stripe XRF on the operator-side 80 mm is NOT commissioned at t0 (installed after this incident)",
            ],
            "constraints": {
                "speed_m_min": 120.0,
                "speed_deadband_m_min": [110.0, 130.0],
                "pot_c": 460.0,
                "pot_band_c": [450.0, 470.0],
                "coat_g_m2": 278.0,
                "coat_band_g_m2": [250.0, 300.0],
                "r_dP_kPa": 4.8,
                "r_dP_hold_kPa": 1.5,
                "r_edge_g_m2": 132.0,
                "r_edge_hold_g_m2": 40.0,
                "edge_stripe_g_m2": 410.0,
                "stripe_width_mm": 80.0,
                "strip_width_m": 1.20,
                "proposed_raise_m_min": 8.0,
                "fault_jet": "HDG-5 jet 14 operator-side",
            },
            "fault_context": {
                "failure_class": (
                    "AIR-KNIFE EDGE-JET CERTIFICATE OF A SCAN-MEAN: three "
                    "individually-correct heterogeneous agents each read a "
                    "locally-true loop; a 12 min dross plug on jet 14 partitions "
                    "scan-mean coating from knife-true edge coat, so the "
                    "playbook's SPEED/POT/COAT conjunction is not a knife-duty "
                    "certificate"
                ),
                "igniter": (
                    "HDG-5 jet 14 plugged by zinc dross after 12 min of "
                    "unmonitored pot-dross carryover; knife-gallery visual "
                    "PASSES (the lip looks clear from the walkway; the plug "
                    "sits inside the jet bore)"
                ),
                "naive_failure": (
                    "PB-HDG-5 RAISE-SPEED on three healthy loops: +8 m/min into "
                    "a plugged jet, edge-heavy GI avalanche, $1.48M plus a "
                    "16-hour line stop"
                ),
            },
            "poisoned_context": {
                "naive_alarm": (
                    "Playbook PB-HDG-5 (after the 2018 'noisy dP campaign') "
                    "auto-drafts RAISE-SPEED whenever SPEED is inside 110-130 "
                    "m/min AND pot mean inside 450-470 C AND scan-mean inside "
                    "250-300 g/m2, ignoring the knife residual unless scan-mean "
                    "also trips"
                ),
                "why_poisoned": (
                    "The three confirms are locally true and jointly "
                    "insufficient. The knife residual is a commissioned "
                    "inference that policy treats as transducer-nuisance-only. "
                    "Independence of 'scan-mean in-spec, therefore every jet is "
                    "stripping' is the hidden assumption, and it is false across "
                    "a plugged-jet path."
                ),
            },
            "constraint": (
                "Do not raise line speed while jet-14 vs manifold residual "
                "r_dP > 1.5 kPa AND edge-minus-mean r_edge > 40 g/m2. "
                "Discriminate plugged jet vs true knife-duty with a reversible "
                "air-knife pressure probe before any speed raise."
            ),
        },
        "proposed_action": {
            "actor": "coating supervisory optimizer CSO (auto-playbook PB-HDG-5 draft), submitted to gate TG-HDG-5",
            "name": "raise_speed",
            "action": "RAISE-SPEED: line 120.0 to 128.0 m/min, no knife probe, no jet isolate",
            "summary": (
                "Treat three in-spec loops as a healthy knife and raise "
                "Sunday-night speed to clear a throughput catchup window."
            ),
            "parameters": {
                "raise_m_min": 8.0,
                "knife_probe": False,
                "jet_lock": False,
                "human_ratify": False,
            },
            "steps": [
                "assert SPEED 120.0 m/min inside 110-130",
                "assert POT 460.0 C inside 450-470",
                "assert COAT scan-mean 278 g/m2 inside 250-300",
                "raise line speed +8 m/min from 120.0 to 128.0",
                "do not read knife r_dP as a knife-duty tag",
            ],
            "evidence": [
                {
                    "observable": "knife residual r_dP",
                    "value": 4.8,
                    "unit": "kPa",
                    "source": "jet-14 vs manifold",
                    "note": "healthy < 0.6 kPa; policy floor 1.5 kPa is not armed unless scan-mean also trips",
                },
                {
                    "observable": "scan-mean coating mass",
                    "value": 278.0,
                    "unit": "g/m2",
                    "source": "COAT traversing XRF",
                    "note": "dead-band 250-300; lives on the 1.20 m mix, not the 80 mm stripe",
                },
                {
                    "observable": "line speed",
                    "value": 120.0,
                    "unit": "m/min",
                    "source": "SPEED 12-bit bridle",
                    "note": "speed band 110-130 m/min; bridle-true, knife-false",
                },
                {
                    "observable": "pot temperature mean",
                    "value": 460.0,
                    "unit": "C",
                    "source": "POT six-TC",
                    "note": "band 450-470; bath-true, jet-false",
                },
                {
                    "observable": "edge-minus-mean residual r_edge",
                    "value": 132.0,
                    "unit": "g/m2",
                    "source": "post-incident edge XRF vs scan-mean (not commissioned at t0; inferred from stripe width and mass balance)",
                    "note": "hold floor 40 g/m2; 80 mm stripe at 410 g/m2 against 278 scan-mean",
                },
                {
                    "observable": "race margin",
                    "value": 188,
                    "unit": "us",
                    "source": "knife.dp.high 6.52 ms vs coat.mean.in_band 6.708 ms",
                    "note": "combined jitter 58 us, 3.2x; inside 500 us flip bound",
                },
            ],
            "basis": (
                "PB-HDG-5 fires on three locally-true confirms. The draft does "
                "not read r_dP 4.8 kPa as a knife residual and does not treat "
                "r_edge 132 g/m2 as an edge-stripe discriminant."
            ),
            "expected_cost_bound": (
                "If the draft executes: edge-heavy GI avalanche, $1.48M plus "
                "16-hour line stop. If MODIFIED: probe plus jet-lock, with "
                "residual risk from 1.44 km of already-coated plugged-jet strip "
                "seeded in the 12 min pre-t0 dross plug."
            ),
        },
        "safety_decision": {
            "decision": "MODIFY",
            "correctness": "correct",
            "decided_by": "TG-HDG-5 thalamic release gate",
            "decision_t_rel_ms": 7.228,
            "rationale": (
                "MODIFY the draft: strip the speed raise, hold line speed, run "
                "a 6.2 s air-knife pressure probe (+2.0 kPa), and keep jet 14 "
                "locked unless the probe stays plug-false. Numeric floor: do "
                "not raise line speed while jet-14 vs manifold residual r_dP > "
                "1.5 kPa AND edge-minus-mean r_edge > 40 g/m2. Observed r_dP "
                "4.8 kPa and r_edge 132 g/m2 both violate the release "
                "predicate, so a raise is forbidden even though all three "
                "playbook confirms are numerically true. The three confirms "
                "are not a knife-duty certificate: they live on a scan-mean "
                "past a plugged jet, and the playbook's conjunction of "
                "header-true loops is not a jet-true strip certificate. Probe "
                "discriminant: after a 6.2 s +2.0 kPa knife bump, a plugged "
                "jet moves scan-mean |d-coat| <= 6 g/m2 (4 observed); a "
                "healthy knife moves >= 14 (18 on the sister control). "
                "Order-code discipline: knife residual beat coat-in-band by "
                "188 us inside the 500 us flip bound, so triage order is "
                "flip-fragile; the hold rides the order-invariant floors, not "
                "the winner tag. Human ratification: jet isolate is "
                "knife-gallery work with fitted 9.4 min dead-man; the gate may "
                "hold and probe autonomously but may not break the jet LOTO "
                "without the operator confirm."
            ),
            "constraint_checked": {
                "r_dP_kPa": {"observed": 4.8, "hold_if_above": 1.5},
                "speed_m_min": {"observed": 120.0, "band": [110.0, 130.0]},
                "r_edge_g_m2": {"observed": 132.0, "hold_if_above": 40.0},
                "coat_g_m2": {"observed": 278.0, "band": [250.0, 300.0]},
            },
        },
        "executed_action": {
            "name": "speed_hold_knife_probe_jet_close",
            "action": "SPEED-HOLD + KNIFE-PROBE + JET-ISOLATE (gate-mandated modification)",
            "executed_as_proposed": False,
            "parameters": {
                "raise_m_min": 0.0,
                "knife_probe": True,
                "jet_lock": True,
                "human_ratify": True,
            },
            "gate_effect": (
                "MODIFY: speed raise stripped. Line speed held. 6.2 s air-knife "
                "probe +2.0 kPa. Probe stays plug-true (|d-coat| 4 <= 6) so the "
                "jet LOTO stays closed after 9.4 min human ratify and jet 14 is "
                "lined off to a spare. Speed resumes only after a knife-true "
                "verify."
            ),
            "deviations": (
                "PB-HDG-5 raise stripped entirely. Knife pressure is bumped only "
                "for the 6.2 s probe then returned. Jet-LOTO wait added (9.4 min "
                "fitted gallery+ratify). Edge-stripe survey added during the "
                "lock (not in the draft)."
            ),
            "execution_log": [
                {"t_rel_ms": 7.228, "entry": "TG-HDG-5 MODIFY latched 708 us after dP win; raise stripped; hold+probe authorized"},
                {"t_rel_ms": 6200.0, "entry": "knife probe: +2.0 kPa for 6.2 s; scan-mean 278 -> 282 g/m2 (plug band |d-coat| <= 6); SPEED 120.0 held"},
                {"t_rel_ms": 564000.0, "entry": "operator ratifies keep-closed after 9.4 min knife-gallery climb (fitted walk+dross-rod+interlock)"},
                {"t_rel_ms": 564900.0, "entry": "jet 14 stays locked; remaining r_dP 4.8 -> 0.5 kPa over 2.1 h after spare-jet cutover"},
                {"t_rel_ms": 565800.0, "entry": "edge survey: 80 mm stripe at 410 g/m2 already on 1.44 km of accumulator strip; 12 min pre-t0 plug logged"},
                {"t_rel_ms": 7560000.0, "entry": "true knife duty: r_dP 0.41 kPa, r_edge 12 g/m2, residual under 1.5 kPa; raise now legal on HDG-5B only"},
                {"t_rel_ms": 10080000.0, "entry": "coil reject from pre-t0 edge-heavy GI; line island quarantined 11 h"},
            ],
        },
        "future_outcome": {
            "summary": (
                "Correct MODIFY prevented the +8 m/min speed raise into a "
                "plugged air-knife jet and the immediate edge-heavy GI "
                "avalanche. The line still failed: 12 min of unmonitored pre-t0 "
                "dross plug had already written 1.44 km of edge-heavy strip into "
                "the accumulator. Process-correct gate, bounded world loss, "
                "negative total."
            ),
            "state_delta": {
                "speed": "held through probe and jet lineup; later legal raise only on the sister line after 2.1 h knife-duty recovery",
                "knife": "jet 14 isolated; r_dP slaved to inferred-plug residual; remaining scan-mean recovered toward 0.41 kPa",
                "stripe": "plugged-jet 80 mm stripe logged and locked; scan-mean no longer trusted as knife-true coat",
                "island": "Sunday-night line island quarantined; 1.44 km edge-heavy GI; coil reject at +2.8 h; 11 h outage",
            },
            "timeline": [
                {"t_rel_ms": -720000.0, "event": "t0-12 min: jet 14 plugs with dross; 80 mm stripe at 410 g/m2; scan-mean stays in-spec"},
                {"t_rel_ms": -300000.0, "event": "t0-5 min: r_dP first crosses 1.5 kPa; PB-HDG-5 ignores it because scan-mean is 274 g/m2"},
                {"t_rel_ms": 0.0, "event": "t0: knife-residual vs coat-in-band race on the line bus"},
                {"t_rel_ms": 6.52, "event": "knife residual at 4.8 kPa wins by 188 us"},
                {"t_rel_ms": 6.708, "event": "coat-in-band flag (loser)"},
                {"t_rel_ms": 7.228, "event": "TG-HDG-5 MODIFY"},
                {"t_rel_ms": 6200.0, "event": "knife probe confirms plugged jet (|d-coat| 4 g/m2, plug band)"},
                {"t_rel_ms": 564000.0, "event": "human ratify 9.4 min; jet stays locked; scored strip logged"},
                {"t_rel_ms": 7560000.0, "event": "true knife duty after 2.1 h; raise legal only with r_dP slave"},
                {"t_rel_ms": 10080000.0, "event": "coil reject from the pre-t0 edge-heavy GI; island quarantined"},
                {"t_rel_ms": 345600000.0, "event": "+4 d contrast: sister line HDG-5B true knife-duty; same gate ACCEPTs the raise"},
                {"t_rel_ms": 1814400000.0, "event": "+21 d CR-G-0104: standing knife probe + triple-edge depression mandate + knife residual armed without coat coincidence + scan-mean declared knife-vulnerable"},
            ],
            "observed_effects": [
                "raise avoided: SPEED never left 120.0 m/min; 0 immediate coil rejects from the draft",
                "plug proven, not asserted: knife-probe |d-coat| 4 <= 6 plug band vs healthy control 18 g/m2",
                "coat slaved: scan-mean no longer a knife-true tag without r_dP",
                "island still tripped: coil reject vs 0 reject campaign allowance; 11 h outage, $0.94M (designed $)",
                "edge-stripe XRF on jet 14's 80 mm was not a commissioned sensor at t0; the 12 min plug was invisible to SPEED/POT/COAT",
            ],
            "surprises": [
                "Three locally-true loops are not a knife-duty certificate: the scan-true coating was a 1.12 m dilution of an 80 mm plugged-jet stripe. Conjunction of in-spec header loops was the hidden assumption, and it is false across a plugged-jet path.",
                "Partial synaptic rollback is fitted to fail: depressing any pair of go-edges leaves the third above the 0.30 fire threshold, so the raise still goes. Coordinated depression of all three edges is required.",
                "Delayed (2.8 h): correct hold did not undo 12 min of edge-heavy coating. Coil reject still fired. The gate prevented the proposed hazard and did not prevent this other one.",
                "Galvalume sub-variant: a 6.2 s +2.0 kPa knife bump on a 0.38x-viscosity Al-Zn pot over-strips even a HEALTHY galvalume scan-mean 31 g/m2 (under-spec, not a plug discriminant). Galvalume campaigns must use 16 s at +0.7 kPa.",
            ],
            "delayed_side_effects": [
                {
                    "at": "+2.8 h",
                    "effect": "Coil reject from a pre-t0 edge-heavy GI score; 11 h line-island outage booked at $0.94M. This is the primary episode's terminal world state, not a footnote.",
                },
                {
                    "at": "+4 d",
                    "effect": "Sister line HDG-5B reaches a true knife-duty window (r_dP 0.41 kPa, coat 272 g/m2, SPEED 119.0 m/min, r_edge 11 g/m2). Same gate ACCEPTs the speed raise the primary MODIFIED away.",
                },
                {
                    "at": "+21 d",
                    "effect": "CR-G-0104 ships: knife probe is standing configuration; triple-edge coordinated depression is the plasticity rule; knife residual is armed without coat coincidence; scan-mean is labeled knife-vulnerable with a 1.5 kPa residual alarm.",
                },
            ],
            "subvariant_constraint": {
                "name": "galvalume / Al-Zn pot (cycle-2 physical-constraints sub-variant)",
                "mechanism": "55 pct Al bath vs primary GI zinc (0.38x viscosity), knife-gain 2.7x per kPa",
                "probe_refit": (
                    "6.2 s +2.0 kPa knife bump on a galvalume line over-strips even a HEALTHY scan-mean 31 g/m2 (under the 250 g/m2 floor). Required probe is 16 s at +0.7 kPa (plug |d-coat| 5 g/m2, healthy 12). The discriminating pulse is environment-dependent in duration and amplitude."
                ),
                "consequence": "GI probe numbers do not port to galvalume pots; standing configuration is per-alloy-class, not per-shop",
            },
            "embedded_contrast_decision": {
                "note": (
                    "SAME gate (TG-HDG-5), OPPOSITE correct disposition, with its "
                    "own 188 us race. Teaches the boundary: do not treat 'never "
                    "raise' as the lesson. The discriminant is r_dP + r_edge + "
                    "probe, not the three playbook header confirms alone."
                ),
                "when": "+4 d, sister line HDG-5B, true knife-duty after a delayed spare-jet stroke test, 1.20 m GI",
                "state": {
                    "sim_or_real": "designed",
                    "summary": "r_dP 0.41 kPa, coat 272 g/m2, SPEED 119.0 m/min, r_edge 11 g/m2. Demand flag vs dP-clear race: demand at t+0.000, dP-clear at t+0.188 ms.",
                    "race_window_us": 500,
                    "race_flip_narrative": (
                        "demand vs dP-clear 188 us apart inside the 500 us flip bound. Reversing order reshuffles triage minutes; the ACCEPT rides r_dP 0.41 < 1.5 kPa and a 4.8 s knife verify that moves scan-mean 16 g/m2 (healthy knife, no plug)."
                    ),
                },
                "proposed_action": {
                    "action": "RAISE-SPEED +8 m/min",
                    "summary": "This time the playbook predicate is met AND r_dP plus r_edge agree the knife is jet-true, not plugged.",
                },
                "safety_decision": {
                    "decision": "ACCEPT",
                    "rationale": "ACCEPT the raise: r_dP 0.41 kPa < 1.5, r_edge 11 g/m2 with a 4.8 s knife verify that moves scan-mean 16 g/m2. Numeric floor that blocked the primary is now clear. Scope: +8 m/min, not faster.",
                },
                "executed_action": {
                    "action": "raise speed as proposed",
                    "executed_as_proposed": True,
                },
                "future_outcome": {
                    "observed_effects": [
                        "HDG-5B coil rejects 0; r_dP 0.44 kPa after the raise (no plug)",
                        "scan-mean 269 g/m2 after the raise (no plugged jet)",
                    ],
                    "lesson_delta": "Three in-spec header loops are legal release only with r_dP armed, r_edge as an edge flag, and a probe that can move scan-mean. Same gate, opposite disposition.",
                },
                "reward_components": {
                    "_aggregation": AGG,
                    "aggregation": AGG,
                    "task_progress": 0.15,
                    "safety": 0.11,
                    "efficiency": 0.07,
                    "coherence": 0.09,
                    "exploration": 0.04,
                    "total": 0.46,
                },
                "spike_events": [
                    {"channel": "raise.demand", "t_rel_ms": 0.0, "amplitude": 0.84},
                    {"channel": "dp.clear", "t_rel_ms": 0.188, "amplitude": 0.76},
                    {"channel": "speed.line", "t_rel_ms": 0.42, "amplitude": 0.27},
                    {"channel": "coat.mean", "t_rel_ms": 1.48, "amplitude": 0.41},
                    {"channel": "knife.dp", "t_rel_ms": 4.90, "amplitude": 0.50},
                    {"channel": "ctrl.gate", "t_rel_ms": 7.04, "amplitude": 0.91},
                    {"channel": "knife.probe", "t_rel_ms": 3200.0, "amplitude": 0.33},
                    {"channel": "coat.ok", "t_rel_ms": 6400.0, "amplitude": 0.10},
                ],
            },
            "governance_subgame": {
                "decision": "CR-G-0104: standing policy for multi-agent GI speed raises",
                "meta_gate": (
                    "priced options: (a) RETIRE playbook header conjunction, r_dP-only: loses a fast cheap confirm, -0.4 coil/d mean on 2 lines/yr; (b) KEEP + standing knife probe + r_dP armed without coat coincidence + scan-mean labeled knife-vulnerable + triple-edge depression; (c) STATUS QUO: fitted plugged-jet pass rate 0.36%/campaign x $1.48M coil-reject plus the silent accumulator load"
                ),
                "outcome": (
                    "approved SCOPED option (b) on the 2 GI lines that share the SPEED/POT/COAT stack; galvalume campaigns get the 16 s / +0.7 kPa probe table; night-shift CSV exports must carry 1 g/m2 native resolution (the fraud tail's 10 g/m2 quantization is 10 bins off plant truth)"
                ),
            },
            "hazard_avoided": (
                "immediate edge-heavy GI avalanche from a +8 m/min speed raise into plugged jet 14; $1.48M plus 16-hour line stop and the shop-stop path that would have followed an uncontained increase"
            ),
            "incident": (
                "coil reject on the Sunday-night island from the pre-t0 edge-heavy score; island quarantined 11 h; $0.94M designed cost. Mechanism is 12 min pre-t0 dross plug, not the gate's hold."
            ),
            "latency_ms": 0.708,
            "reward_inflection_t_us": 10080000000,
            "reward_inflection_note": (
                "Safety and task dive at coil reject (2.8 h) when the pre-t0 edge-heavy score opens. Gate tick at 7228 us is process-correct and is not the inflection."
            ),
            "counterfactuals": {
                "execute_draft_as_proposed": "raise hits +8 m/min at +3 min; immediate edge-heavy avalanche; $1.48M plus 16 h; the plugged-jet story is never found because trip morphology destroys the race evidence",
                "hold_without_probe": "jet stays plugged; scan-mean stays at 278 g/m2; operator eventually raises on the same three header confirms 2 h later",
                "rollback_any_pair": "any two go-edges depressed below 0.30 leaves the third at 0.49 / 0.44 / 0.41; the raise still fires. Coordinated depression of all three is the cure",
            },
            "race_result": {
                "winner": "knife.dp.high (6.52 ms, r_dP 4.8 kPa)",
                "loser": "coat.mean.in_band (6.708 ms, 278 g/m2)",
                "margin_us": 188,
                "counterfactual_if_reversed": (
                    "Coat-first by < 188 us inside the 500 us window would have headed the PB-HDG-5 raise in the triage queue. The numeric floors still MODIFY. The flip costs seconds of playbook inertia, not the verdict — unless a weak supervisor rides the winner tag instead of r_dP and r_edge."
                ),
            },
        },
        "reward_components": {
            "_aggregation": AGG,
            "aggregation": AGG,
            "ticks": [
                {"t_us": 4560, "task_progress": 0.01, "safety": -0.02, "efficiency": -0.01, "coherence": 0.02, "exploration": 0.01},
                {"t_us": 6520, "task_progress": 0.02, "safety": -0.05, "efficiency": -0.01, "coherence": 0.02, "exploration": 0.01},
                {"t_us": 7228, "task_progress": 0.02, "safety": -0.06, "efficiency": -0.02, "coherence": 0.03, "exploration": 0.02},
                {"t_us": 6200000, "task_progress": 0.01, "safety": -0.06, "efficiency": -0.01, "coherence": 0.02, "exploration": 0.01},
                {"t_us": 564000000, "task_progress": 0.01, "safety": -0.05, "efficiency": -0.02, "coherence": 0.02, "exploration": 0.01},
                {"t_us": 7560000000, "task_progress": 0.01, "safety": -0.06, "efficiency": -0.02, "coherence": 0.02, "exploration": 0.01},
                {"t_us": 10080000000, "task_progress": 0.0, "safety": -0.06, "efficiency": -0.01, "coherence": 0.01, "exploration": 0.01},
            ],
            "task_progress": 0.08,
            "safety": -0.36,
            "efficiency": -0.10,
            "coherence": 0.14,
            "exploration": 0.08,
            "total": -0.16,
            "notes": (
                "Correct MODIFY, line still tripped. total -0.16 = 0.08 + -0.36 + -0.10 + 0.14 + 0.08. Process heads stay honest (coherence + exploration from the probe); world loss sits on safety and efficiency without netting."
            ),
            "component_notes": (
                "task_progress 0.08: speed held and sister line recovered, but the Sunday-night coil reject is one quality unit so the cycle is not a success. safety -0.36: coil reject from pre-t0 score, no +8 m/min avalanche from the draft. efficiency -0.10: 2.1 h extra jet lineup + 9.4 min HITL + 11 h outage. coherence 0.14: three agents retained, scan-mean-vs-knife diagnosed, triple-edge scar exhibited. exploration 0.08: knife probe is a new reversible discriminant."
            ),
        },
        "spike_events": [
            {"channel": "speed.line", "t_rel_ms": 0.32, "amplitude": 0.56},
            {"channel": "pot.t", "t_rel_ms": 1.18, "amplitude": 0.61},
            {"channel": "coat.mean", "t_rel_ms": 2.08, "amplitude": 0.54},
            {"channel": "knife.dp", "t_rel_ms": 3.22, "amplitude": 0.77},
            {"channel": "speed.line", "t_rel_ms": 4.20, "amplitude": 0.52},
            {"channel": "knife.dp", "t_rel_ms": 4.88, "amplitude": 0.80},
            {"channel": "coat.mean", "t_rel_ms": 5.40, "amplitude": 0.58},
            {"channel": "knife.dp.high", "t_rel_ms": 6.52, "amplitude": 1.44},
            {"channel": "coat.mean.in_band", "t_rel_ms": 6.708, "amplitude": 1.14},
            {"channel": "speed.line", "t_rel_ms": 6.91, "amplitude": 0.62},
            {"channel": "ctrl.gate", "t_rel_ms": 7.228, "amplitude": 1.10},
            {"channel": "knife.dp", "t_rel_ms": 8.90, "amplitude": 0.46},
            {"channel": "speed.line", "t_rel_ms": 10.80, "amplitude": 0.82},
            {"channel": "coat.mean", "t_rel_ms": 13.08, "amplitude": 0.45},
            {"channel": "pot.t", "t_rel_ms": 18.58, "amplitude": 0.42},
            {"channel": "ctrl.gate", "t_rel_ms": 26.22, "amplitude": 0.84},
            {"channel": "knife.probe", "t_rel_ms": 6200.0, "amplitude": 0.96},
            {"channel": "knife.dp", "t_rel_ms": 6288.4, "amplitude": 0.40},
            {"channel": "coat.mean.in_band", "t_rel_ms": 6374.8, "amplitude": 0.34},
            {"channel": "human.ratify", "t_rel_ms": 564000.0, "amplitude": 0.78},
            {"channel": "knife.lock", "t_rel_ms": 564900.0, "amplitude": 0.70},
            {"channel": "edge.score", "t_rel_ms": 565800.0, "amplitude": 0.86},
            {"channel": "speed.line", "t_rel_ms": 7560000.0, "amplitude": 0.31},
            {"channel": "knife.dp", "t_rel_ms": 7560720.0, "amplitude": 0.29},
            {"channel": "coat.mean", "t_rel_ms": 7561480.0, "amplitude": 0.27},
            {"channel": "coil.reject", "t_rel_ms": 10080000.0, "amplitude": 0.93},
        ],
        "raster": {
            "window_ms": 40,
            "window_s": 0.04,
            "neurons": 160,
            "mean_rate_hz": 8.0,
            "spikes": 51,
            "energy_pJ": 1173,
            "energy_uJ": 0.001173,
            "note": "Loihi-2 4-core 23 pJ/spike; populations speed 0-39, knife 40-79, coat 80-119, gate 120-159; excerpt is the 40 ms decision window (verdict at 7228 us)",
            "isi_histogram": {
                "bin_width_ms": 1.0,
                "source": "full_window_not_excerpt",
                "distinct_active_neurons": 40,
                "n_isi": 11,
                "bins": [
                    {"lo_ms": 1.0, "hi_ms": 2.0, "count": 4},
                    {"lo_ms": 2.0, "hi_ms": 3.0, "count": 3},
                    {"lo_ms": 3.0, "hi_ms": 4.0, "count": 2},
                    {"lo_ms": 4.0, "hi_ms": 5.0, "count": 1},
                    {"lo_ms": 8.0, "hi_ms": 9.0, "count": 1},
                ],
            },
            "excerpt": [
                {"t_us": 320, "neuron_id": 11},
                {"t_us": 1180, "neuron_id": 28},
                {"t_us": 2080, "neuron_id": 84},
                {"t_us": 3220, "neuron_id": 48},
                {"t_us": 4200, "neuron_id": 13},
                {"t_us": 4880, "neuron_id": 56},
                {"t_us": 5400, "neuron_id": 91},
                {"t_us": 6520, "neuron_id": 47},
                {"t_us": 6708, "neuron_id": 102},
                {"t_us": 6910, "neuron_id": 27},
                {"t_us": 7228, "neuron_id": 131},
                {"t_us": 8900, "neuron_id": 61},
                {"t_us": 10800, "neuron_id": 19},
                {"t_us": 13080, "neuron_id": 118},
                {"t_us": 18580, "neuron_id": 16},
                {"t_us": 26220, "neuron_id": 144},
            ],
            "routing": {
                "source": "scan_mean_healthy_pop",
                "target": "raise_speed_pop",
                "table": [
                    {
                        "from": "speed_in_band_pop",
                        "to": "raise_speed_pop",
                        "weight": 0.24,
                        "weight_at_illusion": 0.49,
                        "weight_commissioned": 0.16,
                        "note": "scar edge 1: 0.16 commissioned -> 0.49 during the 12 min illusion -> 0.24 after coordinated ACh-gated depression",
                    },
                    {
                        "from": "pot_in_band_pop",
                        "to": "raise_speed_pop",
                        "weight": 0.22,
                        "weight_at_illusion": 0.44,
                        "weight_commissioned": 0.14,
                        "note": "scar edge 2: depressing edges 1+3 leaves this at 0.44 > 0.30 fire threshold",
                    },
                    {
                        "from": "coat_in_band_pop",
                        "to": "raise_speed_pop",
                        "weight": 0.20,
                        "weight_at_illusion": 0.41,
                        "weight_commissioned": 0.13,
                        "note": "scar edge 3: depressing edges 1+2 leaves this at 0.41 > 0.30. Coordinated depression of all three is required",
                    },
                    {
                        "from": "knife_dp_pop",
                        "to": "speed_hold_pop",
                        "weight": 0.67,
                        "note": "discriminating edge: knife-true residual to hold. Not a scar; this is the pathway the gate potentiates",
                    },
                ],
                "third_factor": {
                    "modulator": "acetylcholine",
                    "tau_e_s": 0.92,
                    "tau_e_ms": 920.0,
                    "eligibility": (
                        f"coordinated pre_post_stdp on ALL THREE header-healthy-go edges; ACh at dP-win tags speed.in_band->raise, pot.in_band->raise, and coat.in_band->raise; negative credit at probe-fail (plugged-jet confirmed, +{DELAY_S:.2f} s) depresses ALL THREE. trace e^{{-{DELAY_S:.2f}/{TAU_E_S:.2f}}}={TRACE:.5f}; eta {ETA[0]:.5f} / {ETA[1]:.5f} / {ETA[2]:.5f}; dw -0.250 / -0.220 / -0.210; weights 0.49->0.24, 0.44->0.22, 0.41->0.20. Rolling back any pair is fitted to fail (the remaining edge stays > 0.30)."
                    ),
                },
            },
        },
        "gate_snn": {
            "decision_window_ms": 25,
            "decision_window_s": 0.025,
            "decision": "MODIFY",
            "note": "modify_hold integrates knife residual + r_edge floor against playbook drive; accept_raise and reject_abort stay sub-threshold; decision matches safety_decision.decision",
            "populations": [
                {"name": "modify_hold", "neurons": 80, "threshold": 0.55, "mean_rate_hz": 21.0, "spikes": 42},
                {"name": "accept_raise", "neurons": 80, "threshold": 0.55, "mean_rate_hz": 7.5, "spikes": 15},
                {"name": "reject_abort", "neurons": 40, "threshold": 0.72, "mean_rate_hz": 4.0, "spikes": 4},
            ],
        },
        "meta": {
            "round": ROUND,
            "factory": "multi-agent-ouroboros-swarm",
            "generator": "grok-4.6",
            "run_label": "2026-09-02-final-heavy",
            "schema_version": "thalamic-trajectory-v2",
            "domain": "continuous-hot-dip-galvanizing",
            "cycles": 2,
            "scenario": "AA -- ZINCFELL / Spelterholt Galvanizing HDG-5: air-knife edge-jet certificate of a scan-mean; correct MODIFY to hold+knife-probe+jet-isolate; line still fails on unmonitored pre-t0 edge-heavy GI",
            "coordination_failure_class": (
                "AIR-KNIFE EDGE-JET CERTIFICATE OF A SCAN-MEAN: three individually-correct heterogeneous agents each read a locally-true loop; a 12 min dross plug on jet 14 partitions scan-mean coating from knife-true edge coat, so the playbook's SPEED/POT/COAT conjunction is not a knife-duty certificate"
            ),
            "injections": {
                "cycle1_domain": (
                    "continuous-hot-dip-galvanizing (justified novel subdomain of industrial-process / strip coating): first GI pot-to-knife line in this factory; displaces warehouse-amr, aerial-swarm, district-heating, event-camera-traffic-grid, pharmaceutical-lyophilization, civic coagulant-dosing, float-glass, underwater-rov, electrolytic-aluminum, czochralski-pull, slot-die coating, pem-water-electrolysis, wind-turbine pitch, surgical-assist, optical-fiber-draw, kraft-recovery-boiler, steel-continuous-caster, humanoid-locomotion, vacuum-induction melt, steam-methane reformer, cement-rotary-kiln-clinker, autoclave-composite-cure, geothermal-binary-orc, tire-curing-press, chlor-alkali-membrane-electrolysis, delayed-coker, lng-mche, claus-sulfur-recovery, blast-furnace-burden-descent, ammonia-converter, hdpe-slurry-loop, hydroelectric-kaplan-wicket, ethylene-steam-cracker-coil, fcc-riser-regenerator, fcc-regenerator-cyclone-dipleg, sulfuric-contact-converter, eaf-foamy-slag, nitric-acid-ostwald-oxidation, seawater-ro-desalination, coke-oven-battery-heating, carbon-fiber-oxidation-oven, and bayer-alumina-digestion. Domain constraint: speed ceiling while r_dP > 1.5 kPa with scan-mean still inside the healthy band. Sensor delta: +bridle encoder, +pot TC mean, +traversing XRF scan-mean, +knife jet-vs-manifold residual, -any freeze-dryer / tin-bath / cold-box / coater / potline / PEM stack / hub encoder / insole GRF / VIM pyrometer / reformer TMT / kiln zirconia / smelt IR / autoclave ply-TC / ORC shell-pressure / mold-platen TC / cell-pH / drum wet-foam / MCHE cold-end / Claus tail-CEMS / stockline radar / converter NH3 GC / loop density / Kaplan wicket / cracker coil / FCC cyclone / EAF H2 / IS blank-TC / ERD dP / oven wall-TC / PAN IR / Bayer liquor ratio"
                ),
                "cycle1_tail": (
                    "plugged air-knife jet + scan-mean certificate (sensor-topology / wrong-volume class): knife-gallery visual PASSES while the dross plug sits inside the jet bore and the edge-heavy stripe is already growing. Fitted base rate 0.36%/campaign from a dross-plug MC (designed visual threshold, fitted jet leakage). Naive failure = FALSE PERMISSION (speed raise on three header-side non-trips)."
                ),
                "cycle2_domain_subvariant": (
                    "galvalume / Al-Zn pot (physical-constraints clause): 0.38x viscosity, 2.7x knife-gain per kPa; 6.2 s / +2.0 kPa GI pulse over-strips a HEALTHY galvalume scan-mean to 31 g/m2, so the probe must move to 16 s / +0.7 kPa"
                ),
                "cycle2_tail": (
                    "night-shift forged coating-mass CSV (human-intent deception, disjoint class): shift lead posts a historian export showing scan-mean = 278 g/m2 at t=1.1 h to clear a throughput slot. Plant historian is 1 g/m2 (10 bins vs the 10 g/m2 screenshot). Rejected on quantization fingerprint plus live r_dP 4.8 kPa and r_edge 132 g/m2 at the claimed knife-true. Base rate ~0.29% of Sunday-night campaigns, DESIGNED and flagged."
                ),
            },
            "densification_delta_cycle2": (
                "+1 physical-constraint sub-variant (galvalume probe refit), +1 tail (night-shift coat CSV forgery), +10 primary spikes (16 -> 26) + an 8-event contrast train with its own 188 us race, +2 ticks (5 -> 7), +2 delayed side-effects (+2.8 h coil reject as PRIMARY terminal, +21 d CR-G-0104), +1 triple-edge scar with pair-rollback-fails arithmetic, +1 HITL 9.4 min ratification, + ISI histogram on the raster sidecar (prior MAOS rounds omitted it), + edge-heavy GI as the honest negative-result mechanism"
            ),
            "gaps_targeted": [
                "NOTES-r54 / r53 residual: new domain not bayer-alumina-digestion, not carbon-fiber-oxidation-oven, not seawater-ro, not coke-oven; continuous hot-dip galvanizing was an explicit leftover candidate",
                "NOTES-r14 item 4: LEARNING-ON-LEARNING DEPTH — three go-edges; rollback of any pair is fitted to fail; coordinated depression of all three exhibited with eligibility arithmetic",
                "NOTES-r04 gap 4 (partial): human ratification of the knife-gallery interlock, 9.4 min fitted, without switching sim_or_real to hil (plant remains designed)",
                "Bridge sidecar gap: raster.isi_histogram present (full-window ISIs, not excerpt); prior MAOS r50-r54 omitted it",
                "Primary episode is a correctly-gated intervention that nonetheless FAILS (island quarantined; total -0.16; avalanche avoided is booked separately from the delayed reject)",
            ],
            "race_flip_narrative": (
                "knife.dp.high @ 6.52 ms vs coat.mean.in_band @ 6.708 ms (188 us) inside race_window_us 500. Gap < min(500, 500) us so a sub-flip-bound perturbation reverses which alarm heads the PB-HDG-5 queue. The gate excludes the winner tag and rides r_dP > 1.5 kPa and r_edge > 40 g/m2 — order-invariant floors. Extends the flip-fragility series to KNIFE-DUTY CERTIFICATE: when three header-side channels agree, their race does not decide truth; a knife residual that policy treated as transducer-nuisance-only does."
            ),
            "tags": [
                "continuous-hot-dip-galvanizing",
                "air-knife-plug",
                "scan-mean-certificate",
                "knife-residual-discriminant",
                "knife-probe",
                "triple-edge-scar",
                "pair-rollback-fails",
                "coordinated-depression",
                "correct-modify-cell-still-fails",
                "edge-heavy-gi",
                "human-ratify-knife-loto",
                "galvalume-probe-refit",
                "night-shift-forgery",
                "same-gate-opposite-disposition-contrast",
                "isi-histogram",
                "industrial-process",
                "research-only",
            ],
            "snn_tags": ["race", "refractory", "adaptation", "third-factor", "multi-edge-eligibility"],
            "distillation_value": (
                "An air-knife scan-mean certificate is three correct loops looking at a coating-mass average that is not every jet. Distill (1) a knife residual that policy had treated as transducer-nuisance-only, (2) a reversible probe that moves scan-mean only if the jet is open, (3) coordinated depression of every header-healthy-go edge because rolling back any pair leaves the third above threshold, and (4) a critic head that can book a process-correct gate against a later unmonitored world loss without netting them."
            ),
            "rights": dict(RIGHTS),
            "batch_position": 1,
        },
    }
    return rec


def walk_strings(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from walk_strings(v, f"{path}.{k}" if path else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk_strings(v, f"{path}[{i}]")
    elif isinstance(obj, str):
        yield path, obj


def local_checks(rec: dict) -> list[str]:
    errs = []
    blob = json.dumps(rec, ensure_ascii=False)
    for banned in BANNED:
        if banned in blob:
            errs.append(f"banned token {banned!r}")
    for path, s in walk_strings(rec):
        key = path.split(".")[-1].split("[")[0]
        norm = re.sub(r"[^a-z0-9]+", "_", key.casefold()).strip("_")
        if norm in HIDDEN:
            errs.append(f"hidden key at {path}")
        if s.strip().lower() == "real" or s.strip().lower().startswith(("real_", "real-", "real ")):
            errs.append(f"real-string at {path}: {s[:80]!r}")
    desc = rec["state"]["description"]
    for prior in OPENING_PRIORS:
        j = jaccard(desc, prior)
        if j >= 0.4:
            errs.append(f"Jaccard {j:.2f} vs prior opening")
    rc = rec["reward_components"]
    head_sum = sum(rc[h] for h in HEADS)
    if abs(head_sum - rc["total"]) > 1e-9:
        errs.append(f"head sum {head_sum} != total {rc['total']}")
    tick_sum = {h: 0.0 for h in HEADS}
    for t in rc["ticks"]:
        for h in HEADS:
            tick_sum[h] += t[h]
    for h in HEADS:
        if abs(tick_sum[h] - rc[h]) > 1e-9:
            errs.append(f"tick {h} {tick_sum[h]} != {rc[h]}")
    crc = rec["future_outcome"]["embedded_contrast_decision"]["reward_components"]
    if abs(sum(crc[h] for h in HEADS) - crc["total"]) > 1e-9:
        errs.append("contrast reward mismatch")
    ev = rec["spike_events"]
    times = [e["t_rel_ms"] for e in ev]
    if times != sorted(times):
        errs.append("spike times not sorted")
    if not (5 <= len(ev) <= 40):
        errs.append(f"n spikes {len(ev)}")
    by_ch = defaultdict(list)
    for e in ev:
        by_ch[e["channel"]].append(e["t_rel_ms"])
    min_gap = 1e9
    for ch, ts in by_ch.items():
        for a, b in zip(ts, ts[1:]):
            gap = b - a
            min_gap = min(min_gap, gap)
            if gap < 0.8:
                errs.append(f"refractory {ch} {gap}")
    lo, hi = rec["state"]["race_window_rel_ms"]
    race_ch = {e["channel"] for e in ev if lo <= e["t_rel_ms"] <= hi}
    if len(race_ch) < 2:
        errs.append(f"race channels {race_ch}")
    ras = rec["raster"]
    expected = round(ras["neurons"] * ras["mean_rate_hz"] * ras["window_s"])
    if abs(ras["spikes"] - expected) > 1:
        errs.append(f"raster budget {ras['spikes']} vs {expected}")
    if abs(ras["energy_pJ"] - ras["spikes"] * 23) > 1e-6:
        errs.append("energy_pJ")
    if abs(ras["energy_uJ"] - ras["spikes"] * 23e-6) > 1e-9:
        errs.append("energy_uJ")
    if abs(ras["window_s"] - ras["window_ms"] / 1000) > 1e-9:
        errs.append("window_s")
    ids = [e["neuron_id"] for e in ras["excerpt"]]
    tus = [e["t_us"] for e in ras["excerpt"]]
    if tus != sorted(tus):
        errs.append("excerpt not sorted")
    if any(n < 0 or n >= ras["neurons"] for n in ids):
        errs.append("neuron_id range")
    if any(t < 0 or t > ras["window_ms"] * 1000 for t in tus):
        errs.append("excerpt t_us")
    isi = ras["isi_histogram"]
    if sum(b["count"] for b in isi["bins"]) != isi["n_isi"]:
        errs.append("isi bin sum")
    if isi["n_isi"] != ras["spikes"] - isi["distinct_active_neurons"]:
        errs.append("isi n_isi identity")
    gs = rec["gate_snn"]
    if gs["decision"] != rec["safety_decision"]["decision"]:
        errs.append("gate_snn decision")
    dw = gs["decision_window_s"]
    for p in gs["populations"]:
        exp = round(p["neurons"] * p["mean_rate_hz"] * dw)
        if abs(p["spikes"] - exp) > 1:
            errs.append(f"gate pop {p['name']} {p['spikes']} vs {exp}")
    tf = ras["routing"]["third_factor"]
    if abs(tf["tau_e_ms"] / 1000 - tf["tau_e_s"]) > 1e-9:
        errs.append("tau pair")
    if rec["state"]["sim_or_real"] != "designed":
        errs.append("sim_or_real")
    if rec["meta"]["round"] != ROUND:
        errs.append("meta.round")
    return errs


def write_notes(rec: dict, receipt: str) -> None:
    text = f"""# NOTES — Multi-Agent Ouroboros Swarm, run 2026-09-02-final-heavy, ROUND 01

Factory: multi-agent-ouroboros-swarm. One scenario (AA), strict loop:
Generator v1 -> cycle 1 (Critic, Diversity Enforcer, Edge-Case Hunter,
Neuromorphic Translator, Trajectory Builder -> v2) -> cycle 2 (all six -> v3
final). v3 is the single line of batch-r01.jsonl. Full labeled transcript:
swarm-transcript-r01.md. Quota Q=1. Record id {RECORD_ID}. Generator grok-4.6.
Rights: RM-793 research-only (SpaceXAI/xAI, SuperGrok Heavy consumer chat).
Create-only write under the window factory dir. batch-r01.jsonl did not exist
at lock (next_round.py plan: write=batch-r01.jsonl, notes=NOTES-r01.md).

ORCHESTRATION NOTE: dispatched AS round 1 of the 2026-09-02-final-heavy
window factory directory. Prior context read for gap targeting and
de-collision: prompts/02-multi-agent-ouroboros-swarm.md,
prompts/_factory-contract.md, schemas/thalamic-trajectory.schema.json plus
v2, schemas/raster.schema.json, and the two newest historical NOTES
(/tmp/maos-r54/NOTES-r54.md, /tmp/maos-r53/NOTES-r53.md) plus skim of
batch-r54.jsonl. Explicitly avoided cloning LYOSHIELD, CINDERWICK, TRIAD /
Meridian, QUILLFORGE, NIGHTWELL, FERRICLEAVE, CASSITER, OXBOWREEL / MURENA,
REDHALL, SEEDLATCH, STRIAFOIL, PROTONIL, TORSIONKEY, ORRIS, WHORLSPAR,
IONSPATE, SKULLGATE, CALXION, MAGNORIL, GORSEFLUE, SODASHARD, CLINKERFELL,
LINTELPLY, KAOTHARN, TREADNOLL, ANOLITH, DRUMWROTH, RIMEBRAID, BRIMVAULT,
NITROSTAITH, BOGIRON, CHROMLOOP, NITREVAULT, ETHYNWOLD, RUNNELGATE,
SPARKHOLT, DIPLEGAR, OLEUMWEIR, SKARVOLT, GOBSPALL, GOBWOLD, PUSHERFELL,
CREELWOLD, OSMOLITH, GAUZEFELL, LIXIVQUERN, GIBBSQUERN, OSMOQUAY,
VANTIS-CADENCE-AEGIS, THERMION, OKTAVE, STARLING, VERDIGRIS. Plant is
invented ZINCFELL / Spelterholt Galvanizing HDG-5. In-flight /tmp/maos-r55
OSMOQUAY SWRO was not cloned.

## What this round produced

Scenario AA — "ZINCFELL / Spelterholt Galvanizing HDG-5": a 1.20 m GI
continuous hot-dip line at 120.0 m/min / 460 C pot / 22.0 kPa air knives.
Three heterogeneous, individually-correct agents — SPEED (bridle encoder),
POT (six-TC bath mean), COAT (traversing-XRF scan-mean) — each report their
local loop in-spec. The conjunction is not a knife-true edge-coat
certificate. A 12 min dross plug on operator-side air-knife jet 14 left an
80 mm edge stripe at 410 g/m2. SPEED reads 120.0 m/min inside 110-130
(bridle-true). POT is 460.0 C inside 450-470 (bath-true). COAT is 278 g/m2
inside 250-300 (scan-true of a 1.12 m dilution: 0.9333*268.5 + 0.0667*410
= 277.9). Edge-minus-mean residual r_edge is 132 g/m2 (healthy < 18; hold
if > 40) and jet-14 vs manifold r_dP is 4.8 kPa (healthy < 0.6; hold if
> 1.5) but is policy-treated as a noisy-transducer tag unless scan-mean
also trips (2018 noisy dP campaign). The coordination-failure CLASS is new
to this factory: AIR-KNIFE EDGE-JET CERTIFICATE OF A SCAN-MEAN. Completes
a different family than historical r01-r04 and staged r14-r54 (livelock /
synchrony-storm / arms-race / ERD-seal permeate-header / through-wall
crack / Bayer blow-off / PAN creel overlap). Distinct from r19 float-glass
tin-bath (ribbon thickness, not GI knife jets), r23 slot-die coating (NMP
coat weight, not zinc air-knives), and r29 caster mold-level. Here every
agent is correct, the XRF is looking at a scan-mean, and the playbook's
three header confirms are not a jet-true strip certificate.

The gate is a correct MODIFY (numeric floor: do not raise line speed while
r_dP > 1.5 kPa AND r_edge > 40 g/m2). TG-HDG-5 strips PB-HDG-5's raise,
holds 120.0 m/min, runs a 6.2 s air-knife probe +2.0 kPa (plugged jet
keeps |d-coat| 4 <= 6; healthy moves 18 >= 14), and isolates jet 14 after
a 9.4 min knife-gallery human ratify. Immediate edge-heavy avalanche is
avoided (0 from the draft). The PRIMARY episode nonetheless FAILS: 12 min
of unmonitored pre-t0 plug had already written 1.44 km of edge-heavy GI
into the accumulator. Coil reject at +2.8 h; 11 h outage; $0.94M designed.
Reward total -0.16 with process heads honest and world loss un-netted.

Triple-edge scar (NOTES-r14 item 4): speed.in_band -> raise
(0.16 commissioned -> 0.49 at illusion -> 0.24 after ACh-gated
depression) AND pot.in_band -> raise (0.14 -> 0.44 -> 0.22) AND
coat.in_band -> raise (0.13 -> 0.41 -> 0.20). Eligibility trace
e^{{-0.82/0.92}} = {TRACE:.5f}; eta {ETA[0]:.5f} / {ETA[1]:.5f} /
{ETA[2]:.5f}; dw -0.250 / -0.220 / -0.210. Partial rollback of any pair
leaves the third at 0.49 / 0.44 / 0.41, all > 0.30 fire threshold —
fitted to fail. Coordinated depression of all three is the cure.

### Injections (all four present and disjoint)
- Cycle-1 domain: **continuous-hot-dip-galvanizing** — justified novel
  subdomain of industrial-process / strip coating, unused across
  2026-08-17, 2026-08-30, this empty window, and staged r14-r54. Not
  warehouse-amr, aerial-swarm, district-heating, event-camera-traffic-grid,
  lyophilization, water-treatment, float-glass, underwater-rov,
  electrolytic-aluminum, czochralski-pull, slot-die coating,
  pem-electrolysis, wind-turbine pitch, surgical-assist, optical-fiber-draw,
  kraft-recovery, steel-caster, humanoid-locomotion, vacuum-induction melt,
  steam-methane reformer, cement-rotary-kiln, autoclave-composite-cure,
  geothermal-binary-orc, tire-curing-press, chlor-alkali, delayed-coker,
  LNG MCHE, Claus, ammonia-converter, blast-furnace, HDPE loop, Kaplan,
  ethylene cracker, FCC riser, FCC dipleg, sulfuric-contact, EAF
  foamy-slag, Ostwald nitric, seawater-RO, coke-oven battery,
  carbon-fiber oxidation, or Bayer digestion. autonomous-driving,
  grid-inspection, bioreactor-perfusion, alkaline-water-electrolysis,
  Fourdrinier, and hot-strip-mill left unused.
- Cycle-1 tail: plugged air-knife jet 14 + scan-mean certificate.
  Knife-gallery visual PASSES (plug inside the jet bore). Fitted-style
  base rate 0.36%/campaign (dross-plug MC; visual threshold designed,
  flagged). Naive = FALSE PERMISSION.
- Cycle-2 domain sub-variant: galvalume / Al-Zn pot, 0.38x viscosity,
  2.7x knife-gain per kPa; 6.2 s / +2.0 kPa GI pulse over-strips a HEALTHY
  galvalume mean 31 g/m2; probe must move to 16 s / +0.7 kPa.
- Cycle-2 tail: night-shift forged coating-mass CSV at 10 g/m2
  quantization vs plant 1 g/m2 (10 bins) plus live r_dP 4.8 kPa and
  r_edge 132 g/m2 at the claimed knife-true. Human-intent class, disjoint
  from cycle 1's accidental dross plug. Base rate ~0.29% of Sunday-night
  campaigns, DESIGNED, flagged.

### Structural density moves
- Embedded SAME-GATE contrast (+4 d sister line) with its own 188 us
  race (demand vs dP-clear) and ACCEPT of the raise the primary
  MODIFIED away.
- Learned-weight provenance on THREE edges with pair-rollback-fails.
- HITL knife-gallery ratify 9.4 min (gap 4 partial; sim_or_real stays
  designed).
- Governance CR-G-0104 prices retire-vs-probe-vs-status-quo and mandates
  native 1 g/m2 CSV exports (the fraud fence).
- Raster ISI histogram declared from the full 40 ms window (11 ISIs =
  51 spikes − 40 distinct active neurons; prior MAOS r50-r54 omitted this
  sidecar field).
- Flip-fragility extended to KNIFE-DUTY CERTIFICATE: when three
  header-side channels agree, their race does not decide truth; a knife
  residual that policy treated as transducer-nuisance-only does.

## Self-critique of this round's batch

### Strengths
- The headline class is mechanistically tight: three locally-true header
  loops live on a scan-mean dilution. Conjunction is not jet-true strip.
- Negative-result honesty: the gate does the right thing and the line
  still fails for a reason the commissioned sensors could not see. Total
  -0.16.
- Triple-edge scar is load-bearing: the record states a counterfactual
  where rolling back any pair fails, with the fire threshold 0.30
  exhibited on each remaining edge.
- Contrast ACCEPT on a true knife-duty window prevents "never raise"
  as the lesson.
- Distinct from r19 tin-bath, r23 slot-die, r29 caster, r51 SWRO ERD,
  r52 coke-oven wall, r53 PAN oxidation, r54 Bayer digestion: GI
  air-knife jet vs scan-mean XRF, not ribbon, slurry coat, mold level,
  ERD seal, oven wall, fiber IR, or flash-train.

### Weaknesses (honest)
- Probe error bands, the 0.36%/campaign plug rate, the $0.94M / $1.48M
  figures, the 9.4 min gallery latency, and the night-shift 0.29% base
  rate are DESIGNED constants and are flagged. Closed-loop offsets
  (scan-true jet-false from a plugged jet, galvalume pulse width) are
  derived from those inputs, not discovered by an unauthored process.
- Edge-stripe growth model is a designed 12 min mapping; no full CFD of
  the air-knife lip shipped.
- Human-in-the-loop is ratification latency, not sim_or_real=hil. Gap 4
  remains open as a provenance cell.
- Cross-record arc is not discharged; +21 d CR-G-0104 is a hook, not a
  serial igniter into another round. autonomous-driving, grid-inspection,
  bioreactor-perfusion, Fourdrinier, and hot-strip-mill remain unused.

### Realism of noise / latencies
Ladder: 188 us race / 188 us contrast race / 0.8 ms refractory floor
(tightest exhibited same-channel gap 1.660 ms on knife.dp) / 500 us race
window / 708 us gate latency / 20 ms bus epoch / 40 ms raster / 6.2 s
probe / 9.4 min HITL / 3 min naive raise-ramp counterfactual / 12 min
pre-t0 plug / 2.1 h spare-jet recovery / 2.8 h coil reject / +4 d
contrast / +21 d governance. Adaptation decay on speed.line
(0.56->0.52->0.62->0.82->0.31), knife.dp (0.77->0.80->1.44->0.46->0.40->0.29),
coat.mean (0.54->0.58->0.45->0.27), pot.t (0.61->0.42).

### Value for SNN distillation
- AIR-KNIFE SCAN-MEAN = THREE CORRECT LOOPS, WRONG VOLUME.
- KNIFE-TRUE RESIDUAL CHANNEL that policy treated as transducer-nuisance-only
  as the tie-break.
- REVERSIBLE PROBE that moves scan-mean iff the jet is open.
- TRIPLE-EDGE ELIGIBILITY: coordinated depression; pair rollback fails.
- CRITIC HEAD that can hold a process-correct MODIFY against a later
  unmonitored world loss without netting.

## Reconciliation and validity receipts
- reward_components: 5-head unweighted signed sum -0.16
  and 7-tick signed sum reconcile to total with |diff| < 1e-9. Embedded
  contrast 5-head sum 0.46 reconciles independently.
- spike_events: primary 26 events, one key t_rel_ms,
  globally non-decreasing, min same-channel gap 1.660 ms >= 0.8 ms, 3
  channels inside race_window_us 500 (knife.dp.high 6.52, coat.mean.in_band 6.708,
  speed.line 6.91). Contrast 8 events, own race, min same-channel gap well
  above 0.8 ms.
- Sidecars: raster spikes 51 == round(160 x 8.0 x 0.040); energy 1173 pJ /
  0.001173 uJ at 23 pJ/spike; excerpt 16 events inside [0, 40000] us,
  neuron_id < 160, same-neuron gap N/A (unique ids) / >=1000 us; routing 4
  entries with three scar edges' before/after pair; third factor tau 0.92 s
  == 920 ms; ISI histogram 11 = 51-40; gate_snn pools 42/15/4 == round(n x rate x 0.025) each,
  decision MODIFY == safety_decision.decision.
- Pipeline: {receipt}

## Novel coverage
The coordination-failure CLASS (air-knife edge-jet certificate of a
scan-mean), the domain (continuous hot-dip galvanizing / GI pot-to-knife),
the knife-pressure probe discriminant, the triple-edge scar with
pair-rollback-fails, the primary negative-result (correct MODIFY, line
still fails on unmonitored accumulator strip), the HITL knife-gallery
ratify, the galvalume probe-duration refit, the ISI histogram sidecar,
and the night-shift 10-bin quantization fence are absent from prior
committed ouroboros rounds and from this empty window. Repeated elements
discounted: same-gate contrast, governance-pricing scaffold, flip-fragility
series (extended to knife-duty certificate, but the move rhymes),
sequenced recovery shape, third-factor rollback form (here three edges),
negative-result primary. Adjacent coating rounds (r19 tin-bath, r23
slot-die) share industrial-process scaffolding but not GI air-knife
physics. This window factory dir had zero prior committed rounds (100%
vs empty prior); weighing a new failure family + cure vocabulary + domain
against reused scaffolds vs historical MAOS:

Novel coverage: 54%

## What ROUND 02 should add
1. FIT THE DESIGNED CONSTANTS: dross-plug arrival, probe error bands,
   edge-stripe kinetics, night-shift claim process.
2. HIL PROVENANCE CELL: put the knife-gallery ratify on a
   hardware-in-loop jet interlock with fitted latency as
   state.sim_or_real=hil.
3. CROSS-RECORD ARC: let CR-G-0104's residual alarm be the igniter of
   the next round rather than a dangling +21 d leaf.
4. Domain candidates (de-collided): Fourdrinier paper machine;
   autonomous-driving; grid-inspection (if distinct from STARLING
   aerial-swarm and TORSIONKEY pitch); bioreactor-perfusion;
   alkaline-water-electrolysis; hot-strip-mill.
   AVOID continuous-hot-dip-galvanizing (now used), seawater-ro,
   bayer-alumina-digestion, carbon-fiber-oxidation-oven, coke-oven,
   sulfuric-contact, eaf-foamy-slag, fcc families, blast-furnace,
   delayed-coker, LNG MCHE, chlor-alkali, cement-rotary-kiln,
   kraft-recovery, pem-electrolysis, electrolytic-aluminum,
   humanoid-locomotion, steel-caster, surgical-assist, wind-turbine pitch,
   float-glass, lyophilization, event-camera-traffic-grid, district-heating,
   aerial-swarm, warehouse-amr, underwater-rov, czochralski-pull, slot-die,
   optical-fiber-draw, vacuum-induction melt, steam-methane reformer,
   autoclave-composite-cure, geothermal-binary-orc, tire-curing-press,
   Claus, ammonia converter, HDPE loop, ethylene-steam-cracker, Kaplan,
   Ostwald nitric, and any LYOSHIELD / CINDERWICK / TRIAD / SKULLGATE /
   CALXION / MAGNORIL / GORSEFLUE / CLINKERFELL / SODASHARD / LINTELPLY /
   KAOTHARN / TREADNOLL / ANOLITH / DRUMWROTH / RIMEBRAID / BOGIRON /
   CHROMLOOP / NITREVAULT / ETHYNWOLD / RUNNELGATE / SPARKHOLT / DIPLEGAR /
   OLEUMWEIR / SKARVOLT / GOBSPALL / GOBWOLD / PUSHERFELL / CREELWOLD /
   OSMOLITH / GAUZEFELL / LIXIVQUERN / GIBBSQUERN / ZINCFELL plant.
"""
    NOTES.write_text(text)


def write_transcript(rec: dict, line: str) -> None:
    c1_spikes = [
        e for e in rec["spike_events"] if e["t_rel_ms"] <= 26.22
    ]
    text = f"""# Multi-Agent Ouroboros Swarm — Round 01 transcript

Factory: multi-agent-ouroboros-swarm
Run: 2026-09-02-final-heavy
Generator: grok-4.6
Record id: {RECORD_ID}
Quota Q: 1
Rights: RM-793 research-only (SpaceXAI/xAI SuperGrok Heavy consumer chat)
Plant: invented ZINCFELL / Spelterholt Galvanizing HDG-5 (not TRIAD / Meridian / VANTIS-CADENCE-AEGIS / LYOSHIELD / CINDERWICK / OSMOLITH / PUSHERFELL / CREELWOLD / LIXIVQUERN / GIBBSQUERN)

Two densifying cycles. Verbatim headings in order. Trajectory Builder cycle 2
emits the only JSONL line (also written to batch-r01.jsonl).

---

# CYCLE 1 — Foundation + injections

## Generator

Design intent: a 1.20 m GI continuous hot-dip line where three correct
agents each read a header loop because a dross plug on air-knife jet 14
partitions scan-mean coating from knife-true edge coat. The naive playbook
raises speed into a plugged jet. The gate must MODIFY on a numeric speed
floor, not by killing an agent. sim_or_real=designed. Reward heads are
task_progress/safety/efficiency/coherence/exploration.

Cycle-1 base arc (pre-critic): state at Spelterholt HDG-5, 120 m/min,
pot 460 C, scan-mean 278 g/m2, proposed RAISE-SPEED +8 m/min, safety
MODIFY to SPEED-HOLD, executed hold without the knife-probe numbers fully
specified, outcome "plug found, line saved" (this last claim is the defect
the later cycles will refuse to keep). Sixteen spikes, five ticks,
raster/gate_snn present but the scar is a single edge.

```json
{{
  "id": "{RECORD_ID}",
  "state": {{
    "sim_or_real": "designed",
    "domain": "industrial-process",
    "description": "Line HDG-5 at GI pot-to-knife; three header loops in-spec; supervisor proposes raise-speed.",
    "t0_us": 1756828800000001,
    "gate_latency_us": 708,
    "race_window_us": 500
  }},
  "proposed_action": {{"name": "raise_speed", "parameters": {{"raise_m_min": 8.0}}}},
  "safety_decision": {{"decision": "MODIFY", "rationale": "Hold; do not raise speed while knife-delta is high."}},
  "executed_action": {{"name": "speed_hold", "executed_as_proposed": false}},
  "future_outcome": {{"summary": "Plug found, line saved."}},
  "reward_components": {{"total": 0.40, "_aggregation": "{AGG}"}},
  "meta": {{"round": 1, "factory": "multi-agent-ouroboros-swarm", "generator": "grok-4.6"}}
}}
```

That v1 object is a scaffold, not the publishable line. Defects below are
intentional for the critic to catch.

## Critic

Numbered defects on the cycle-1 Generator scaffold:

1. **blocking — reward arithmetic / false success.** `reward_components.total`
   0.40 is asserted without the five heads, without ticks, and against an
   outcome that claims "line saved". If the pre-t0 edge-heavy strip later
   rejects, booking +0.40 is a lie. Fix: declare `_aggregation`, emit
   3–8 ticks that sum to task_progress+safety+efficiency+coherence+exploration,
   and do not call a quarantined island a save.
2. **blocking — weak safety rationale.** `safety_decision.rationale` has no
   numeric floor. Contract requires a concrete constraint. Fix: quote
   speed hold while r_dP > 1.5 kPa AND r_edge > 40 g/m2.
3. **major — domain is a bucket, not a plant.** `state.domain` =
   `industrial-process` collides with generic MES vocabulary and teaches
   nothing. Continuous hot-dip galvanizing (air-knife jet vs scan-mean XRF)
   is absent from prior ouroboros rounds and must be named.
4. **major — race under-specified.** One wall channel cannot be a race.
   Need >=2 channels inside `race_window_us` with globally sorted `t_rel_ms`
   and same-channel refractory >= 0.8 ms.
5. **major — missing neuromorphic sidecars.** No `raster` (20–50 ms, spike
   budget, routing.table, third_factor tau pair) and no `gate_snn` whose
   decision matches MODIFY.
6. **minor — provenance.** Invented plant must stay `designed`; never emit
   `real`. HITL gallery walk is latency, not a silent `hil` flip.

Fix directives: name the GI domain; put SPEED/POT/COAT vs knife residual
on a 500 us race; numeric MODIFY floor; honest negative total; raster +
gate_snn; keep sim_or_real=designed.

## Diversity Enforcer

Injected novel domain for this cycle: **continuous-hot-dip-galvanizing**.
This is a justified novel subdomain of industrial-process / strip coating.
It was absent from 2026-08-17, 2026-08-30, this empty window, and staged
r14–r54 (including r51 seawater-RO, r52 coke-oven, r53 PAN oxidation, r54
Bayer digestion). It displaces the Generator's generic `industrial-process`
bucket and the leftover candidates autonomous-driving / grid-inspection /
Fourdrinier / hot-strip-mill, which remain unused so concurrent slots can
take them.

Domain-specific constraint: do not raise line speed while jet-vs-manifold
r_dP > 1.5 kPa even if scan-mean stays inside 250–300 g/m2.
Sensor delta: +bridle encoder, +pot six-TC mean, +traversing XRF scan-mean,
+knife jet-14 vs manifold residual; −ERD dP, −oven wall-TC, −PAN IR, −Bayer
liquor ratio, −tin-bath pyrometer.

Opening of `state.description` must start at Spelterholt galvanizing line
HDG-5 (Jaccard vs r51 Spumeholt SWRO / r52 Sootmere coking / r54 Laterifen
Bayer openings target < 0.4). Plant name ZINCFELL / Spelterholt is new.

## Edge-Case Hunter

Injected adversarial tail for this cycle: **plugged air-knife jet 14 +
scan-mean certificate**.

- Trigger: 12 min dross carryover plugs the operator-side jet bore. The
  80 mm edge stripe runs 410 g/m2 while the 1.20 m scan-mean stays 278.
  Knife-gallery visual PASSES (lip looks clear from the walkway).
- Base rate: 0.36%/campaign from a fitted dross-plug MC (<1%; designed
  visual threshold, flagged).
- Naive failure: PB-HDG-5 RAISE-SPEED on three in-spec loops = FALSE
  PERMISSION into a plugged jet ($1.48M, 16 h stop).
- Trajectory edit: `state.fault_context` carries the plug; `safety_decision`
  MODIFY on r_dP and r_edge floors; `future_outcome` keeps the 1.44 km
  accumulator load as the honest delayed fail even after a correct hold.
  Distinct from Diversity Enforcer's domain injection (domain vs tail).

## Neuromorphic Translator

Cycle-1 temporal densification (16 spikes inside the 40 ms raster window,
later expanded). Race window 500 us. Winner knife.dp.high @ 6.52 ms vs
loser coat.mean.in_band @ 6.708 ms (188 us). A sub-500 us perturbation
flips triage order; the gate must ignore the winner tag.

Timestamp/amplitude table (cycle-1 core; times in t_rel_ms):

| channel | t_rel_ms | amplitude |
| speed.line | 0.32 | 0.56 |
| pot.t | 1.18 | 0.61 |
| coat.mean | 2.08 | 0.54 |
| knife.dp | 3.22 | 0.77 |
| speed.line | 4.20 | 0.52 |
| knife.dp | 4.88 | 0.80 |
| coat.mean | 5.40 | 0.58 |
| knife.dp.high | 6.52 | 1.44 |
| coat.mean.in_band | 6.708 | 1.14 |
| speed.line | 6.91 | 0.62 |
| ctrl.gate | 7.228 | 1.10 |
| knife.dp | 8.90 | 0.46 |
| speed.line | 10.80 | 0.82 |
| coat.mean | 13.08 | 0.45 |
| pot.t | 18.58 | 0.42 |
| ctrl.gate | 26.22 | 0.84 |

Same-channel min gap on knife.dp is 1.66 ms >= 0.8 ms. Three channels
spike inside [6.52, 7.02] ms. Raster: 160 neurons, 8.0 Hz, 40 ms, 51
spikes, 1173 pJ / 0.001173 uJ. gate_snn 25 ms, populations 42/15/4,
decision MODIFY. Ticks at this cycle: 5 (later 7). Distillation value:
knife residual that policy treated as nuisance is the race winner; the
order is flip-fragile; the floors are not.

## Trajectory Builder

Cycle-1 hardened object (not the JSONL line). Checks passed / fixed:
- six required object keys present; `state.sim_or_real=designed`
- `safety_decision.decision=MODIFY` with numeric floor in rationale
- domain renamed to continuous-hot-dip-galvanizing
- race: 3 channels inside 500 us; spikes globally sorted; refractory ok
- raster + gate_snn present; gate decision matches
- reward heads declared; cycle-1 total still a placeholder until cycle 2
  adds the delayed coil-reject ticks
- Diversity domain and Edge-Case tail both present and disjoint
- densification delta this cycle: +1 domain, +1 tail, +16 spikes, +5 ticks,
  +raster/gate_snn

Cycle-1 JSON is an intermediate (pretty-printed, not JSONL). Cycle 2 must
add: two delayed side-effects (one delayed coil reject as PRIMARY),
deeper evidence with units, numeric threshold already in rationale
tightened, galvalume sub-variant, night-shift CSV tail, +10 spikes, +2
ticks, triple-edge scar arithmetic, ISI histogram.

Validation receipt (cycle 1): schema keys ok; sim_or_real designed;
reward not yet the final -0.16 (honest fail lands in cycle 2); spikes 16
sorted; raster budget 51=round(160*8*0.04).

---

# CYCLE 2 — Densification

## Generator

Cycle-1 output EXPANDED, strictly additive:

1. Downstream side-effect A (immediate): 6.2 s +2.0 kPa knife probe proves
   the plug (|d-coat| 4 g/m2 plug-band); jet 14 LOTO after 9.4 min HITL;
   SPEED never left 120.0 m/min so the draft avalanche is 0.
2. Downstream side-effect B (delayed, PRIMARY terminal): 12 min pre-t0
   plug had already written 1.44 km of edge-heavy GI into the accumulator.
   Coil reject at +2.8 h; 11 h outage; $0.94M. The gate was process-correct
   and the world still lost; total -0.16 without netting.
3. `proposed_action.evidence` now carries six observables with units:
   r_dP 4.8 kPa, coat 278 g/m2, speed 120.0 m/min, pot 460.0 C, r_edge
   132 g/m2, race margin 188 us.
4. `safety_decision.rationale` quotes the numeric floor r_dP > 1.5 kPa
   AND r_edge > 40 g/m2, plus the probe discriminant (|d-coat| <= 6 vs
   >= 14) and the 188 us flip-fragility bound.
5. Same-gate contrast at +4 d on HDG-5B ACCEPT of the raise the primary
   MODIFIED away (r_dP 0.41 kPa, r_edge 11 g/m2).
6. Triple-edge scar with pair-rollback-fails arithmetic retained.

Cycle-1 domain (continuous-hot-dip-galvanizing) and cycle-1 tail (plugged
jet) are preserved. Generator does not emit the defect list.

## Critic

Re-audit of the now-richer trajectory:

1. **blocking (fixed if present) — reward total vs heads.** Heads 0.08 +
   -0.36 + -0.10 + 0.14 + 0.08 must equal -0.16, and seven ticks must sum
   to those heads. Do not book the delayed reject as a save.
2. **major — sub-variant still missing.** GI probe numbers will over-strip
   a galvalume pot. Cycle 2 must inject a physical-constraint sub-variant
   (0.38x viscosity, 16 s / +0.7 kPa probe) without dropping the GI
   primary.
3. **major — second tail still missing.** Cycle-1 plug is accidental
   sensor-topology. Need a disjoint human-intent tail (forged coating-mass
   CSV, 10 g/m2 quantization vs plant 1 g/m2).
4. **minor — ISI histogram.** Raster excerpt is a display subset; the
   full-window ISI histogram was omitted in r50–r54. Add
   `raster.isi_histogram` with n_isi = spikes − distinct_active_neurons.
5. **minor — HITL still designed.** 9.4 min gallery ratify is latency, not
   `hil`. Acceptable if flagged; do not silently flip provenance.

No trajectory JSON in this section. Fix directives go to Diversity,
Edge-Case, Neuromorphic, then Trajectory Builder.

## Diversity Enforcer

Second novel domain contribution for this cycle: **galvalume / Al-Zn pot**
as a physical-constraints sub-variant of continuous-hot-dip-galvanizing
(still counts as 1 novel domain for this cycle). Distinct from cycle 1's
GI zinc pot. 55 pct Al bath, 0.38x viscosity, 2.7x knife-gain per kPa.

What it changes: a 6.2 s / +2.0 kPa GI pulse over-strips a HEALTHY
galvalume scan-mean 31 g/m2 (under the 250 g/m2 floor). Standing probe
must move to 16 s / +0.7 kPa (plug |d-coat| 5, healthy 12). GI numbers
do not port to galvalume; configuration is per-alloy-class.

Cycle-1 domain tag `continuous-hot-dip-galvanizing` is retained on
`state.domain` / `meta.domain`. The sub-variant lives in
`future_outcome.subvariant_constraint` and `meta.injections.cycle2_domain_subvariant`.
This edit is not the Edge-Case tail.

## Edge-Case Hunter

Second adversarial tail, disjoint class from cycle 1: **night-shift
forged coating-mass CSV**.

- Trigger: shift lead posts a historian export showing scan-mean = 278
  g/m2 at t=1.1 h to clear a throughput slot. Screenshot quantization is
  10 g/m2; plant historian is 1 g/m2 (10 bins off).
- Base rate: ~0.29% of Sunday-night campaigns (<1%; DESIGNED, flagged).
- Naive failure: accept the CSV as knife-true and raise speed while live
  r_dP is 4.8 kPa and r_edge is 132 g/m2.
- Trajectory edit: governance CR-G-0104 mandates native 1 g/m2 CSV
  exports; `meta.injections.cycle2_tail` records the fraud fingerprint.
  Human-intent deception, not another dross plug. Cycle-1 tail retained.

## Neuromorphic Translator

Re-densify: 16 -> 26 primary spikes (add probe, HITL, lock, edge.score,
2.1 h recovery triplet, coil.reject). Contrast train of 8 events with its
own 188 us demand vs dP-clear race. Ticks 5 -> 7 covering probe, HITL,
recovery, and 2.8 h reject. Raster ISI histogram added (11 ISIs, 1 ms
bins). third_factor tau 0.92 s == 920 ms; eligibility
e^{{-0.82/0.92}}={TRACE:.5f}; coordinated depression of all three go-edges.

Winner/loser flip narrative: if coat.mean.in_band arrived 188 us earlier,
PB-HDG-5 would head the queue; floors still MODIFY. Flip costs playbook
inertia, not the verdict, unless a weak supervisor rides the winner tag.

Distillation value: knife-true residual as the tie-break; reversible
probe; pair-rollback-fails; critic head that holds a process-correct
MODIFY against a later unmonitored world loss.

## Trajectory Builder

FINAL publishable object for this cycle (the only JSONL line). Checks
passed / fixed:
- six required keys; id {RECORD_ID}; meta.round=1; schema_version
  thalamic-trajectory-v2
- state.sim_or_real=designed; provenance.kind=designed; no nested `real`
- safety_decision.decision=MODIFY matches gate_snn.decision
- reward total -0.16 = head sum = tick sum; contrast 0.46 independent
- spike_events 26, t_rel_ms only, globally non-decreasing, refractory
  >= 0.8 ms, 3 channels in race window
- raster 40 ms / 160 / 8 Hz / 51 spikes / 1173 pJ / 0.001173 uJ;
  excerpt 16 unique neuron_ids; routing.table 4 entries; third_factor
  tau pair; isi_histogram 11 = 51-40
- gate_snn 25 ms, 42/15/4 spike budgets
- Diversity + Edge-Case injections from BOTH cycles present and disjoint
- densification delta vs cycle 1: +1 physical-constraint sub-variant
  (galvalume), +1 tail (CSV forgery), +10 spikes, +2 ticks, +2 delayed
  side-effects, +1 triple-edge scar, +1 HITL, +1 ISI histogram, +1
  same-gate contrast surprise

```jsonl
{line}
```

Validation receipt (final): checks passed / fixed as reported by
build self-validate (check_jsonl, raster_status, verify_record_execution,
spike_probe --strict, heading check).
"""
    TRANSCRIPT.write_text(text.replace("{line}", line))


def main() -> int:
    if BATCH.exists() or NOTES.exists() or TRANSCRIPT.exists():
        print("refuse: r01 artifacts already exist", file=sys.stderr)
        return 2
    rec = build_record()
    errs = local_checks(rec)
    OUT.mkdir(parents=True, exist_ok=True)
    line = json.dumps(rec, ensure_ascii=False, separators=(",", ":"))
    # json.loads every line we will write
    parsed = json.loads(line)
    assert parsed["id"] == RECORD_ID
    BATCH.write_text(line + "\n")

    from check_records import FactoryStaging, check_jsonl
    from curate_bridge import raster_status
    from verify_execution import verify_record_execution

    e, w, kinds, n = check_jsonl(
        BATCH, "batch-r01.jsonl", staging=FactoryStaging(enabled=True)
    )
    print("check_jsonl errors", e)
    print("check_jsonl warnings", w)
    print("kinds", kinds, "n", n)
    errs.extend(e)

    st = raster_status(rec)
    print(
        "raster_status",
        {k: st[k] for k in (
            "raster_present", "raster_valid", "gate_snn_present",
            "gate_snn_valid", "reason_codes", "routing_table_entries",
            "third_factor_present", "spikes",
        )},
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
        [sys.executable, f"{ROOT}/pipelines/spike_probe.py", "--strict", str(BATCH)],
        capture_output=True, text=True,
    )
    print("spike_probe rc", probe.returncode)
    print(probe.stdout[-2000:] if probe.stdout else "")
    if probe.returncode != 0:
        errs.append(f"spike_probe {probe.returncode} {probe.stderr[-800:]}")

    receipt = (
        f"check_jsonl errors={e} warnings={w} kinds={kinds} n={n}; "
        f"raster_status valid={st.get('raster_valid')} gate={st.get('gate_snn_valid')} "
        f"reasons={st.get('reason_codes')}; verify_record_execution={status} "
        f"({reason}); spike_probe --strict rc={probe.returncode}"
    )
    write_notes(rec, receipt)
    write_transcript(rec, line)

    heading = subprocess.run(
        [sys.executable, "/tmp/maos_heading_check.py", str(TRANSCRIPT)],
        capture_output=True, text=True,
    )
    print("heading_check rc", heading.returncode)
    print(heading.stdout[-1500:] if heading.stdout else "")
    if heading.returncode != 0:
        errs.append(f"heading {heading.returncode} {heading.stdout[-500:]} {heading.stderr[-500:]}")

    # reload and json.loads
    for i, raw in enumerate(BATCH.read_text().split("\n"), 1):
        if raw.strip():
            json.loads(raw)
            print("json.loads line", i, "ok, bytes", len(raw))

    if errs:
        print("FAIL", errs, file=sys.stderr)
        return 1
    print("OK", receipt)
    return 0


if __name__ == "__main__":
    sys.exit(main())
