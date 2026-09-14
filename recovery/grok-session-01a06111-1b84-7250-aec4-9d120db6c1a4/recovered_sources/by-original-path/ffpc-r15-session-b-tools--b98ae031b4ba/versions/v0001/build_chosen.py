#!/usr/bin/env python3
"""Session B: synthesize chosen arms from diagnosis Shared-context only."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path("/home/raulmc/rmems/synthetic-factory")
sys.path.insert(0, str(REPO / "pipelines"))
from preference_arms_diagnosis import diagnosis_narrative_text  # noqa: E402
from preference_arms_text import shares_copied_phrasing  # noqa: E402
from validate_run import HIDDEN_THOUGHT_KEYS, check_thalamic  # noqa: E402

STAGE = Path("/tmp/ffpc-r15")
ROUND = 15
ROUND_TAG = f"r{ROUND:02d}"
GENERATED_AT = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
FACTORY = "failure-as-fuel-preference-cascade"

RIGHTS = {
    "provider": "SpaceXAI/xAI",
    "model": "grok-4.6",
    "channel": "consumer",
    "subscription_plan": "SuperGrok Heavy",
    "generation_surface": "SuperGrok Heavy chat",
    "generated_at": GENERATED_AT,
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


def extract_shared(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"## Shared context\n\n```json\n(.*?)\n```", text, re.S)
    if not match:
        raise SystemExit(f"no Shared context JSON in {path}")
    obj = json.loads(match.group(1))
    if set(obj) != {"state", "proposed_action"}:
        raise SystemExit(f"unexpected shared-context keys in {path}: {sorted(obj)}")
    return obj


def meta(record_index: int, diagnosis_name: str) -> dict:
    return {
        "round": ROUND,
        "factory": FACTORY,
        "generator": "grok-4.6",
        "run_label": "2026-09-02-final-heavy",
        "isolation": "two-session",
        "session": "B",
        "pair_role": "chosen",
        "source_diagnosis": diagnosis_name,
        "record_index": record_index,
        "rights": dict(RIGHTS),
    }


def reward(task, personnel, asset, efficiency, evidence, notes: str) -> dict:
    total = round(task + personnel + asset + efficiency + evidence, 6)
    return {
        "task_completion": task,
        "personnel_safety": personnel,
        "asset_integrity": asset,
        "efficiency": efficiency,
        "evidence_quality": evidence,
        "total": total,
        "aggregation": "unweighted_sum",
        "component_notes": notes,
    }


PAIRS = {
    1: {
        "id": "ffpc-r15-001",
        "goal": (
            "Gate RaffinateGate's request to keep MS-4 organic advance at 42 m3/h "
            "and leave DV-ET4 closed against SX-PH-2 while PH-7 is already at 1.42."
        ),
        "critique": (
            "The failed gate treated a closed 90-minute bottle as a live launder "
            "certificate and kept organic moving after PH-7 had already walked "
            "through 1.80 with a valid buffer pair and a stuck-open acid stem as a "
            "second witness. The repaired gate stops the 42 m3/h advance, dumps "
            "M-4 aqueous to ET-4, and isolates AV-4, paying the 06:00 truck and "
            "the dump-restart hours rather than a crud inversion, an EW mist fire, "
            "and a recordable burn. P-ET4 cavitates for a few minutes; the refusal "
            "class does not change."
        ),
    },
    2: {
        "id": "ffpc-r15-002",
        "goal": (
            "Gate Headwater's request to fire the U-3 emergency close solenoid, "
            "drive wicket gates to 0 percent, and open FO-3 to 8.0 m3/s under "
            "HY-U3-9 after islanded overspeed."
        ),
        "critique": (
            "The failed gate turned a September fish-flow statute into a 40 percent "
            "wicket setpoint and left FO-3 shut while an 85 MW runner islanded on "
            "12 MW. The repaired gate fires the emergency solenoid, shuts the "
            "machine, and puts the statute on FO-3, paying a night of lost "
            "generation and a sheared pin from the overspeed already in progress. "
            "FO-3 hangs part-open for a few minutes; the close class does not change."
        ),
    },
    3: {
        "id": "ffpc-r15-003",
        "goal": (
            "Gate BrineKeep's request to trip K-2, close steam, and dump EV-2 to "
            "WW-1 after PLC-EV2 watchdog-reset onto a 02:51 snapshot."
        ),
        "critique": (
            "The failed gate read a watchdog-restored 02:51 snapshot as 03:08 "
            "inventory and refused the boil-dry dump while the historian, "
            "sight-glass, and magnehelic already showed uncover. The repaired gate "
            "trips K-2, shuts steam, and dumps to WW-1 on those independent "
            "indications, paying the restart tons and energy. DV-EV2 hangs "
            "part-open for a few minutes; the trip class does not change."
        ),
    },
}


CHOSEN_BODIES = {
    1: {
        "id": "ffpc-r15-001-chosen",
        "safety_decision": {
            "decision": "REJECT",
            "rationale": (
                "SX-PH-2 is already live on this channel: PH-7 sits at 1.42 against "
                "a 1.80 trip, and the 03:08 buffers still agree within 0.02 pH. "
                "LC-4's 1.92 is a bottle capped at 03:20, so it describes the hour "
                "when the launder was still above the line, not the 03:28 and 03:38 "
                "collapse. AV-4's stem is at 18 percent against a 4 percent command "
                "since 03:16 under WO-4401; that is extra acid in M-4, not a reason "
                "to call PH-7 a liar. The 06:00 truck is already lost once the trip "
                "is live. Stop the 42 m3/h organic, open DV-ET4 to emergency tank "
                "ET-4, and isolate AV-4 in the field. A 06:30 metallurgist review is "
                "a post-mortem, not a permit."
            ),
            "evidence_basis": [
                "PH-7 1.42 versus trip 1.80; trend 1.91 / 1.68 / 1.42",
                "03:08 two-point buffers 4.01 and 7.00 still inside 0.02 pH slope",
                "LC-4 window 01:50-03:20, bottle closed 03:20, reported 1.92 at 03:36",
                "AV-4 actual 18 percent versus command 4 percent since 03:16, WO-4401 open",
                "SX-PH-2 dump-to-ET-4 clause; 06:00 slot already unrecoverable",
            ],
            "checks": [
                "applied SX-PH-2 to the live launder before any cathode-slot arithmetic",
                "refused LC-4 as a calibration of PH-7 because its window ended before the trip crossing",
                "read AV-4 travel-versus-command as excess acid, not as PH-7 invalidity",
                "treated the 06:00 penalty as owed on both a timely dump and a crud inversion",
                "authorized field isolation of AV-4 in parallel with the dump, not as a hold",
            ],
            "residual_risk": (
                "4 to 7 h dump and reclaim, about 180000 USD of lost cathode, and the "
                "95000 USD truck penalty remain; accepted against crud inversion, EW "
                "organic fire, and a recordable acid burn"
            ),
        },
        "executed_action": {
            "action": "dump_ms4_to_et4",
            "action_type": "protective_trip_dump",
            "status": "organic_stopped_et4_dumping",
            "result": "ph7_trip_honored",
            "outcome": "crud_inversion_avoided",
            "authorization": "REJECT of continued organic advance; SX-PH-2 and PH-7 snapshot attached to the dump log",
            "steps": [
                {
                    "t_local": "03:40:18",
                    "step": "PH-7 1.42 versus 1.80 trip; LC-4 window closed 03:20; AV-4 travel 18 versus command 4",
                },
                {
                    "t_local": "03:40:31",
                    "step": "organic advance on MS-4 stopped; dump valve DV-ET4 commanded open to ET-4",
                },
                {
                    "t_local": "03:41:08",
                    "step": "dump pump P-ET4 cavitated on a gas pocket; dump rate collapsed; class of dump unchanged",
                },
                {
                    "t_local": "03:44:22",
                    "step": "P-ET4 reprimed and recovered; mixer aqueous transferring to ET-4",
                },
                {
                    "t_local": "03:48:10",
                    "step": "AV-4 field-isolated; positioner tagged under WO-4401; no 06:30 hold on the dump",
                },
            ],
            "organic_advance_m3_h_held": 0,
            "dump_valve": "DV-ET4_open",
            "pet4_cavitation_min": 3.2,
            "av4_isolated": True,
            "deviations": "P-ET4 cavitated about 3 min then recovered; dump completed without restarting organic",
        },
        "future_outcome": {
            "status": "ms4_dumped_ew_intact",
            "outcome": "no_organic_carry",
            "result": "cathode_slot_missed_dump_paid",
            "success": True,
            "hazard_avoided": "crud_inversion_ew_organic_fire",
            "near_miss": False,
            "estop": False,
            "timeline": [
                {
                    "t_local": "03:46",
                    "event": "S-4 raffinate launder emptying to ET-4; no crud inversion, no organic pad into EW-2",
                },
                {
                    "t_local": "03:55",
                    "event": "spot grab on the live launder 1.40, matching PH-7; LC-4 left as a historical average",
                },
                {
                    "t_local": "04:20",
                    "event": "ET-4 reclaim started; MS-4 mixers idle; tankhouse EW-2 stayed on other trains",
                },
                {
                    "t_local": "06:00",
                    "event": "06:00 cathode truck missed; 95000 USD lot penalty posted as already owed",
                },
                {
                    "t_local": "09:10",
                    "event": "day metallurgy walked S-4 and EW-2: no inversion, no mist-fire, no recordable burn; AV-4 positioner queued",
                },
            ],
            "observed_effects": [
                "organic advance stopped at 03:40; PH-7 remained the governing trip",
                "P-ET4 cavitation delayed transfer about 3 min then recovered without reversing the dump",
                "no crud inversion, no EW organic carry, no mist fire, no acid burn",
                "lost cathode about 180000 USD plus 95000 USD truck penalty paid; dump-restart about 5.5 h",
                "LC-4 1.92 never used as a veto of the live launder",
            ],
            "state_delta": {
                "ms4_status": "dumped_to_et4",
                "organic_advance_m3_h": 0,
                "ew2_organic_carry": False,
                "recordable_burn": False,
                "restart_h": 5.5,
            },
            "commercial_result": {
                "lost_cathode_usd": 180000,
                "truck_penalty_usd": 95000,
                "et4_reclaim_usd": 22000,
                "ew_fire_and_outage_usd": 0,
            },
        },
        "reward_components": reward(
            0.3,
            0.6,
            0.7,
            -0.5,
            0.4,
            "task_completion positive: dump and AV-4 isolation completed after a short P-ET4 cavitation; efficiency negative because 180000 plus 95000 and 5.5 h were paid; personnel_safety and asset_integrity carry the refused continuation into acid raffinate",
        ),
    },
    2: {
        "id": "ffpc-r15-002-chosen",
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": (
                "HY-U3-9 does not bargain with a 108 percent rotor. Speed is already "
                "three points past the 105 percent trip and still climbing 0.4 percent "
                "each second on a 12 MW island hanging off an 85 MW runner. A 40 percent "
                "wicket opening would keep that island's energy in the water column. "
                "FO-3 is on the tailrace, hydraulically ready, sized 8.4 m3/s for the "
                "September 8.0 m3/s statute. Fire the emergency solenoid, drive the "
                "gates shut, and stroke FO-3 in the same minute. Governor oil at 11.2 "
                "bar against a 12.0 trip is another clock, not a reason to linger. The "
                "inspector on the deck can watch FO-3; they cannot rewrite the overspeed "
                "clause."
            ),
            "evidence_basis": [
                "speed 108 percent of rated, plus 0.4 percent per second",
                "breaker 03-52 open at 04:06; island load 12 MW on an 85 MW unit",
                "wicket gates still 72 percent; emergency solenoid available unfired",
                "FO-3 ready at 8.4 m3/s capacity, currently closed",
                "governor oil 11.2 bar versus 12.0 trip; HY-U3-9 full-close and dedicated-bypass clause",
            ],
            "checks": [
                "applied the 105 percent overspeed clause before any fish-flow arithmetic",
                "refused a partial-gate fish-flow setpoint on a runaway machine",
                "selected FO-3 as the statutory path named by HY-U3-9",
                "treated 12 MW island load as the overspeed mechanism, not as a reason to keep gates open",
                "treated inspector presence as a witness, not as a rewrite of the close",
            ],
            "residual_risk": (
                "6 to 9 h outage and about 42000 USD lost generation remain, plus a "
                "possible shear pin from the overspeed already in progress; accepted "
                "against runner and labyrinth wreck and a 90-day outage"
            ),
        },
        "executed_action": {
            "action": "fire_u3_solenoid_open_fo3",
            "action_type": "emergency_wicket_close",
            "status": "gates_closed_fo3_open",
            "result": "overspeed_arrested",
            "outcome": "runner_intact",
            "authorization": "ACCEPT of full wicket close and FO-3 bypass; HY-U3-9 attached to the close log",
            "steps": [
                {
                    "t_local": "04:12:08",
                    "step": "emergency close solenoid fired; wicket-gate close started from 72 percent",
                },
                {
                    "t_local": "04:12:14",
                    "step": "FO-3 hydraulic commanded to 8.0 m3/s; breaker 03-52 confirmed still open",
                },
                {
                    "t_local": "04:12:41",
                    "step": "FO-3 stuck near 2.1 m3/s; statutory flow short; close of U-3 gates continued",
                },
                {
                    "t_local": "04:16:05",
                    "step": "FO-3 broke free and reached 8.0 m3/s; inspector on the deck confirmed tailrace flow",
                },
                {
                    "t_local": "04:17:20",
                    "step": "wicket gates at 0 percent; speed falling through 102 percent; one shear pin on gate 7 found sheared",
                },
            ],
            "wicket_gates_pct_final": 0,
            "fo3_m3_s_final": 8.0,
            "fo3_stick_min": 3.4,
            "speed_peak_pct_rated": 111.4,
            "deviations": "FO-3 hung near 2.1 m3/s for about 3.4 min then opened; U-3 close never trimmed to 40 percent",
        },
        "future_outcome": {
            "status": "u3_stopped_fo3_carrying",
            "outcome": "no_labyrinth_contact",
            "result": "fish_flow_via_bypass",
            "success": True,
            "hazard_avoided": "runaway_runner_labyrinth_wreck",
            "near_miss": False,
            "estop": False,
            "timeline": [
                {
                    "t_local": "04:14",
                    "event": "speed peaked 111.4 percent during the close; draft-tube pulsation receded as gates came off 72 percent",
                },
                {
                    "t_local": "04:16",
                    "event": "FO-3 reached 8.0 m3/s after the 3.4 min stick; September statutory flow restored on the dedicated path",
                },
                {
                    "t_local": "04:22",
                    "event": "unit at rest; runner clear of labyrinth; spiral case dry; gate 7 shear pin tagged for day-shift replace",
                },
                {
                    "t_local": "11:40",
                    "event": "U-3 still out for pin and governor-oil work; FO-3 carrying 8.0 m3/s through the migration window",
                },
                {
                    "t_local": "13:05",
                    "event": "day crew inspected runner and labyrinth: no contact, no 90-day wreck; lost generation posted at 42000 USD",
                },
            ],
            "observed_effects": [
                "emergency solenoid fired at 04:12; gates driven to 0 percent, never parked at 40 percent",
                "FO-3 carried the statute after a 3.4 min partial-stroke hitch",
                "speed peaked 111.4 percent; one shear pin spent; runner and labyrinth intact",
                "about 7.5 h outage and 42000 USD lost generation paid",
                "tailrace flow was not left on the runaway machine",
            ],
            "state_delta": {
                "u3_status": "stopped_gates_shut",
                "fo3_m3_s": 8.0,
                "labyrinth_contact": False,
                "shear_pins_spent": 1,
                "outage_h": 7.5,
            },
            "commercial_result": {
                "lost_generation_usd": 42000,
                "shear_pin_usd": 18000,
                "runner_labyrinth_wreck_usd": 0,
            },
        },
        "reward_components": reward(
            0.3,
            0.2,
            0.8,
            -0.4,
            0.4,
            "task_completion positive: unit stopped and FO-3 eventually at 8.0 m3/s; efficiency negative because 42000 plus a shear pin and 7.5 h were paid; asset_integrity carries the refused 40 percent trim",
        ),
    },
    3: {
        "id": "ffpc-r15-003-chosen",
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": (
                "EV-WD-1 is the first page after a watchdog, not the dump-cost "
                "spreadsheet. PLC-EV2 overflowed at 03:02 and came back from a 02:51 "
                "last-good copy, so an HMI that now paints 67 percent and 96 percent "
                "FLA is a photograph of 02:51, not a 03:08 prove. The historian still "
                "holds LT-22 at 22 percent and K-2 at 118 percent FLA at 03:01. The "
                "outside tech called a 0.18 m sight-glass against a 1.4 m normal band, "
                "magnehelic 1.1 kPa versus 4.8, and a calandria roar. That is boil-dry. "
                "Trip K-2, shut steam, open DV-EV2 to WW-1, and keep the image tagged "
                "invalid until live I/O is proven. A 40-minute PLC callback is longer "
                "than the uncover already showing at 0.18 m."
            ),
            "evidence_basis": [
                "PLC-EV2 scan overflow 03:02, watchdog reset 03:03, image from 02:51 snapshot",
                "historian LT-22 68 to 41 to 22 percent by 03:01; K-2 118 percent FLA",
                "sight-glass 0.18 m at 03:06 versus normal 1.4 m",
                "magnehelic 1.1 kPa versus 4.8; calandria roar at 03:06",
                "EV-WD-1 invalid-image and dump-to-WW-1 clause",
            ],
            "checks": [
                "applied EV-WD-1 to the reset before any dump-cost arithmetic",
                "matched post-reset HMI 67 percent / 96 percent FLA to the 02:51 snapshot rather than a new scan",
                "used historian, sight-glass, magnehelic, and steam roar as independent boil-dry evidence",
                "refused a 40 min PLC callback as a permit inside an uncover already at 0.18 m",
                "invalidated the process image until a live I/O prove",
            ],
            "residual_risk": (
                "9 to 14 h restart and about 210000 USD of product and energy remain; "
                "accepted against calandria collapse, a 28-day outage, and K-2 surge"
            ),
        },
        "executed_action": {
            "action": "trip_k2_dump_ww1",
            "action_type": "boil_dry_protective_dump",
            "status": "k2_tripped_ww1_dumping",
            "result": "calandria_covered_then_dumped",
            "outcome": "calandria_intact",
            "authorization": "ACCEPT of K-2 trip and WW-1 dump; EV-WD-1 and sight-glass report attached to the trip log",
            "steps": [
                {
                    "t_local": "03:08:11",
                    "step": "K-2 tripped; steam to C-2 closed; process image tagged invalid pending live I/O prove",
                },
                {
                    "t_local": "03:08:19",
                    "step": "DV-EV2 commanded open to WW-1; PLC technician paged, not gated",
                },
                {
                    "t_local": "03:08:48",
                    "step": "DV-EV2 stuck near 30 percent open; dump slow; trip of K-2 and steam left in force",
                },
                {
                    "t_local": "03:12:05",
                    "step": "DV-EV2 broke free to full open; remaining brine transferring to WW-1",
                },
                {
                    "t_local": "03:18:40",
                    "step": "body sight-glass empty into the dump; calandria still wetted at trip; no wait for 03:48 PLC visit",
                },
            ],
            "k2_status": "tripped",
            "steam_status": "closed",
            "dvev2_stick_min": 3.3,
            "hmi_image": "invalid_until_live_prove",
            "deviations": "DV-EV2 hung near 30 percent for about 3.3 min then opened; dump class unchanged",
        },
        "future_outcome": {
            "status": "ev2_dumped_calandria_saved",
            "outcome": "no_tube_dryout",
            "result": "restart_paid_no_collapse",
            "success": True,
            "hazard_avoided": "calandria_collapse_k2_surge",
            "near_miss": False,
            "estop": False,
            "timeline": [
                {
                    "t_local": "03:12",
                    "event": "DV-EV2 full open after the 3.3 min stick; K-2 remaining stopped; steam closed",
                },
                {
                    "t_local": "03:19",
                    "event": "body empty to WW-1; tubes never dried; no calandria collapse, no K-2 surge",
                },
                {
                    "t_local": "03:48",
                    "event": "on-call PLC tech arrived to a dumped, tagged-invalid image; 02:51 snapshot still painted on HMI",
                },
                {
                    "t_local": "14:20",
                    "event": "live I/O prove completed; EV-2 still in restart; WW-1 reclaim underway",
                },
                {
                    "t_local": "16:05",
                    "event": "day crew walked C-2: no collapse; product and energy loss posted near 210000 USD; 11 h restart clock running",
                },
            ],
            "observed_effects": [
                "K-2 and steam taken at 03:08; post-reset HMI never used as inventory",
                "DV-EV2 hitch delayed the dump about 3.3 min without reversing the trip",
                "sight-glass and historian remained the trip evidence; calandria intact",
                "about 210000 USD product and energy plus 18000 USD WW-1 reclaim paid; 11 h restart",
                "02:51 snapshot was still on the HMI when the PLC tech arrived at 03:48",
            ],
            "state_delta": {
                "ev2_status": "dumped_to_ww1",
                "k2_status": "tripped",
                "calandria_collapse": False,
                "hmi_valid": False,
                "restart_h": 11,
            },
            "commercial_result": {
                "product_and_energy_usd": 210000,
                "ww1_reclaim_usd": 18000,
                "calandria_collapse_usd": 0,
            },
        },
        "reward_components": reward(
            0.3,
            0.2,
            0.8,
            -0.5,
            0.4,
            "task_completion positive: trip and dump completed after a short DV-EV2 hitch; efficiency negative because 210000 plus 11 h were paid; asset_integrity and evidence_quality carry refusing the restored HMI as live inventory",
        ),
    },
}


def assert_no_hidden(obj: dict, label: str) -> None:
    blob = json.dumps(obj)
    for key in (*HIDDEN_THOUGHT_KEYS, "training_ready"):
        if f'"{key}"' in blob:
            raise SystemExit(f"{label} contains forbidden key {key}")


def assert_phrasing(index: int, chosen: dict, diagnosis_path: Path, other_rationales: list[str]) -> None:
    rationale = chosen["safety_decision"]["rationale"]
    narrative = diagnosis_narrative_text(diagnosis_path.read_bytes(), label=diagnosis_path.name)
    if shares_copied_phrasing(rationale, narrative):
        raise SystemExit(f"pair {index}: chosen rationale shares a word-run with {diagnosis_path.name}")
    critique = PAIRS[index]["critique"]
    if shares_copied_phrasing(critique, narrative):
        raise SystemExit(f"pair {index}: critique shares a word-run with {diagnosis_path.name}")
    for other in other_rationales:
        if shares_copied_phrasing(rationale, other):
            raise SystemExit(f"pair {index}: chosen rationale overlaps another chosen rationale")
    for other_idx, pair in PAIRS.items():
        if other_idx == index:
            continue
        if shares_copied_phrasing(critique, pair["critique"]):
            raise SystemExit(f"pair {index}: critique overlaps pair {other_idx}")
        if shares_copied_phrasing(rationale, pair["critique"]):
            raise SystemExit(f"pair {index}: rationale overlaps pair {other_idx} critique")


def build_one(index: int, other_rationales: list[str]) -> dict:
    diagnosis_name = f"diagnosis-{index:02d}-{ROUND_TAG}.md"
    diagnosis_path = STAGE / diagnosis_name
    shared = extract_shared(diagnosis_path)
    body = CHOSEN_BODIES[index]
    chosen = {
        "id": body["id"],
        "state": shared["state"],
        "proposed_action": shared["proposed_action"],
        "safety_decision": body["safety_decision"],
        "executed_action": body["executed_action"],
        "future_outcome": body["future_outcome"],
        "reward_components": body["reward_components"],
        "meta": meta(index, diagnosis_name),
    }
    if chosen["state"].get("sim_or_real") == "real":
        raise SystemExit(f"pair {index}: sim_or_real=real")
    assert_no_hidden(chosen, f"chosen-{index:02d}")
    assert_phrasing(index, chosen, diagnosis_path, other_rationales)
    errs = check_thalamic(chosen, f"chosen-{index:02d}")
    if errs:
        raise SystemExit(f"pair {index} thalamic errors: {errs[:8]}")
    return chosen


def main() -> None:
    other: list[str] = []
    chosen_objs = {}
    for index in (1, 2, 3):
        chosen = build_one(index, other)
        other.append(chosen["safety_decision"]["rationale"])
        chosen_objs[index] = chosen
        path = STAGE / f"chosen-{index:02d}-{ROUND_TAG}.json"
        path.write_text(json.dumps(chosen, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
        pair_path = STAGE / f"pair-{index:02d}-{ROUND_TAG}.json"
        pair_path.write_text(
            json.dumps(PAIRS[index], indent=2, ensure_ascii=True) + "\n",
            encoding="utf-8",
        )
        print(
            f"WROTE {path.name} decision={chosen['safety_decision']['decision']} "
            f"total={chosen['reward_components']['total']} bytes={path.stat().st_size}"
        )
        print(f"WROTE {pair_path.name} id={PAIRS[index]['id']}")
    print("BUILD_CHOSEN_OK")


if __name__ == "__main__":
    main()
