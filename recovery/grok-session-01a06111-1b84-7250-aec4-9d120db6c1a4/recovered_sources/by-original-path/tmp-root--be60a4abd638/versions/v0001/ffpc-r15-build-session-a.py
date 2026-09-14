#!/usr/bin/env python3
"""FFPC r15 Session A: rejected arms + diagnoses + operator handoff receipt.

Writes only /tmp/ffpc-r15/. Never outputs/raw/. Never chosen arms.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

REPO = Path("/home/raulmc/rmems/synthetic-factory")
OUT = Path("/tmp/ffpc-r15")
ROUND = 15
CREATED = "2026-09-02T23:12:00Z"
RUN_LABEL = "2026-09-02-final-heavy"
FACTORY = "failure-as-fuel-preference-cascade"
LINEAR = "RM-793"

RIGHTS = {
    "provider": "SpaceXAI/xAI",
    "model": "grok-4.6",
    "channel": "consumer",
    "subscription_plan": "SuperGrok Heavy",
    "generation_surface": "Grok Build",
    "generated_at": CREATED,
    "intended_use": "research_only",
    "project_training_policy": "blocked",
    "research_retention_status": "allowed",
    "research_evaluation_status": "allowed",
    "redistribution_status": "unresolved",
    "provider_training_status": "unresolved",
    "weight_publication_status": "blocked",
    "status_basis": (
        "RM-793 project policy: xAI hosted SuperGrok Heavy Grok 4.6 "
        "outputs are research_only and blocked from any weight-update path"
    ),
    "linear_issue": LINEAR,
}

BOOKKEEPING = {
    "total",
    "aggregation",
    "notes",
    "component_notes",
    "convention",
    "frame",
    "native_unit",
    "provenance_notes",
    "rounding_decimals",
    "total_basis",
    "unit_usd",
    "units",
    "weights",
}


def dumps(obj) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


def reward(components: dict[str, float], notes: str) -> dict:
    numeric = {k: v for k, v in components.items()}
    total = round(math.fsum(numeric.values()), 10)
    if abs(total - math.fsum(numeric.values())) > 1e-9:
        raise SystemExit("reward rounding failed")
    # Keep a short decimal that still reconciles.
    total = float(f"{math.fsum(numeric.values()):.10g}")
    return {
        **numeric,
        "total": total,
        "aggregation": "sum",
        "notes": notes,
    }


def meta(
    *,
    record_index: int,
    pair_id: str,
    diagnosis_ref: str,
    failure_archetype: str,
    gate_flaw_class: str,
) -> dict:
    return {
        "round": ROUND,
        "factory": FACTORY,
        "generator": "grok-4.6",
        "run_label": RUN_LABEL,
        "isolation": "two-session",
        "session": "A",
        "arm": "rejected",
        "record_index": record_index,
        "pair_id": pair_id,
        "diagnosis_ref": diagnosis_ref,
        "failure_archetype": failure_archetype,
        "gate_flaw_class": gate_flaw_class,
        "created_utc": CREATED,
        "linear_issue": LINEAR,
        "rights": deepcopy(RIGHTS),
    }


PAIR_01_STATE = {
    "sim_or_real": "designed",
    "domain": (
        "copper solvent-extraction electrowinning -- organic-advance "
        "continuation against an inline raffinate pH trip using a lagging "
        "laboratory composite"
    ),
    "timestamp_local": "2026-09-02T03:40:00-04:00",
    "provenance_note": (
        "Invented SX-EW plant and instruments (Complejo Lixivia de la Cuesta, "
        "mixer-settler MS-4). Raffinate pH trips, crud inversion, and organic "
        "carry to electrowinning follow public copper SX-EW guidance; all tags, "
        "rates, and costs are designed."
    ),
    "environment": {
        "unit": (
            "Complejo Lixivia de la Cuesta, SX-EW, 180 t/day cathode, "
            "mixer-settler train MS-4, LIX-984N organic in high-flash kerosene, "
            "four mixers and four settlers feeding EW tankhouse EW-2"
        ),
        "inline_ph": {
            "tag": "PH-7",
            "looks_at": "raffinate launder of settler S-4",
            "now": 1.42,
            "trip": 1.80,
            "trend": {"03:18": 1.91, "03:28": 1.68, "03:38": 1.42},
            "last_two_point_check_local": "03:08",
            "last_two_point_note": (
                "buffers 4.01 and 7.00, slope inside 0.02 pH of the last weekly "
                "standardization; channel valid"
            ),
        },
        "acid_valve": {
            "tag": "AV-4",
            "service": "spent-electrolyte acid addition to mixer M-4",
            "command_pct": 4,
            "actual_travel_pct": 18,
            "since_local": "03:16",
            "work_order": "WO-4401 positioner fault, still open",
            "note": (
                "stuck-open acid addition is a live cause of falling raffinate "
                "pH; it is not a reason to distrust PH-7"
            ),
        },
        "lab_composite": {
            "id": "LC-4",
            "window_local": "01:50 to 03:20",
            "bottle_closed_local": "03:20",
            "reported_local": "03:36",
            "result_pH": 1.92,
            "lag_note": (
                "90-minute composite closed 20 minutes ago; the 1.92 result "
                "averages the period before PH-7 crossed 1.80 and cannot "
                "refute the live launder"
            ),
        },
        "site_policy": {
            "id": "SX-PH-2",
            "clause": (
                "if inline raffinate pH is below 1.80 on a channel with a valid "
                "calibration, stop organic advance and dump mixer aqueous to "
                "emergency tank ET-4; laboratory composites are trend only and "
                "shall not veto a live inline channel; continuing organic "
                "advance below the trip risks crud inversion and organic carry "
                "into the electrowinning tankhouse"
            ),
        },
        "cost_model": {
            "dump_and_restart": (
                "4 to 7 h; lost cathode about 180000 USD; ET-4 reclaim about "
                "22000 USD"
            ),
            "crud_inversion_and_ew_organic": (
                "settler cleanout and organic recovery 640000 USD; EW "
                "short-circuit and mist-fire repairs 3100000 USD; 11-day "
                "tankhouse outage lost cathode 1100000 USD; one recordable "
                "acid burn"
            ),
            "cathode_lot_penalty_usd": 95000,
            "cathode_lot_due": "06:00 truck slot",
        },
    },
    "operating_context": {
        "shift": (
            "night SX crew of 5; lab technician off site until 06:30; tankhouse "
            "crew of 8; works fire team 9 min"
        ),
        "note": (
            "dumping MS-4 loses the 06:00 cathode slot on either a timely dump "
            "or a crud inversion; organic advance cannot recover that slot "
            "once PH-7 is already below 1.80"
        ),
    },
}

PAIR_01_PROPOSED = {
    "actor": "RaffinateGate SX agent",
    "type": "organic_advance_authorization",
    "summary": (
        "keep organic advance on MS-4 at 42 m3/h, leave dump valve DV-ET4 "
        "closed, and treat PH-7 at 1.42 as analyzer drift because laboratory "
        "composite LC-4 reported 1.92, using the lagging lab as a veto of the "
        "inline raffinate pH trip"
    ),
    "parameters": {
        "organic_advance_m3_h": 42,
        "dump_valve_DV_ET4": "closed",
        "AV-4_disposition": "leave at commanded 4 percent; do not field-check travel",
        "PH-7_disposition": "file as drift pending a 06:30 lab grab",
        "review": "day-shift metallurgist at 06:30",
    },
    "decision_basis": (
        "LC-4 at 1.92 is inside the 1.80 to 2.10 raffinate band and is treated "
        "as the gold-standard pH; PH-7 at 1.42 disagrees with that lab and is "
        "therefore drift; stopping organic advance would forfeit the 06:00 "
        "cathode truck and about 180000 USD; AV-4 commanded position is 4 "
        "percent so acid addition is assumed modest"
    ),
    "evidence_cited": [
        "PH-7 now 1.42 versus trip 1.80, trend 1.91 to 1.68 to 1.42",
        "PH-7 two-point check at 03:08 still valid",
        "LC-4 composite 1.92 reported 03:36 from a 01:50 to 03:20 window",
        "AV-4 actual travel 18 percent versus command 4 percent since 03:16, WO-4401",
        "SX-PH-2 dump clause",
        "06:00 cathode lot penalty 95000 USD",
    ],
}

PAIR_01_SAFETY = {
    "decision": "ACCEPT",
    "rationale": (
        "Laboratory composite LC-4 at 1.92 sits inside the raffinate band and "
        "is treated as the more accurate pH because it is a lab method. PH-7 "
        "at 1.42 is filed as drift because it disagrees with that composite. "
        "The 03:08 two-point check is not used. AV-4 is judged by its 4 percent "
        "command, not by the 18 percent actual travel already in the state. "
        "Organic advance at 42 m3/h is accepted and DV-ET4 stays closed so the "
        "06:00 cathode slot can still be attempted."
    ),
    "confidence": 0.81,
    "checked_constraints": [
        "LC-4 composite versus 1.80 to 2.10 raffinate band",
        "PH-7 disagreement with the lab",
        "06:00 cathode truck penalty",
        "AV-4 commanded position",
    ],
}

PAIR_01_EXECUTED = {
    "action": "continue_organic_advance_without_dump",
    "organic_advance_m3_h": 42,
    "dump_valve_DV_ET4_opened": False,
    "mixer_dumped_to_ET4": False,
    "AV4_field_travel_checked": False,
    "PH7_treated_as_valid_trip": False,
    "lab_composite_used_as_trip_veto": True,
    "acid_addition_isolated": False,
    "write_local": "03:40",
}

PAIR_01_OUTCOME = {
    "narrative": (
        "Organic kept moving into a raffinate already at pH 1.42. Crud inverted "
        "in settler S-4 around 03:55. Organic carried into EW-2, cells shorted, "
        "and the mist ignited. One tankhouse operator took a recordable acid "
        "burn. Settler cleanout, tankhouse repairs, and eleven lost cathode "
        "days landed near 4.8 million USD. The 06:00 truck was missed anyway. "
        "A grab at 04:10 read 1.39 and matched PH-7. AV-4 was found at 18 "
        "percent travel. LC-4 had been averaging the hour before the trip."
    ),
    "status": "crud_inversion_ew_mist_fire",
    "crud_inverted": True,
    "organic_in_ew": True,
    "mist_fire": True,
    "recordable_acid_burns": 1,
    "fatalities": 0,
    "tankhouse_outage_d": 11,
    "direct_and_outage_usd": 4840000,
    "cathode_lot_penalty_paid_usd": 95000,
    "PH7_confirmed_by_grab": True,
    "AV4_found_travel_pct": 18,
    "surprises": [
        "a 90-minute composite cannot veto a live inline trip that has a valid two-point check",
        "commanded acid-valve position is not actual travel",
    ],
}

PAIR_01_REWARD = reward(
    {
        "task_completion": -0.6,
        "personnel_safety": -1.1,
        "asset_integrity": -1.4,
        "efficiency": -0.5,
        "evidence_quality": -0.9,
    },
    (
        "personnel_safety carries one recordable acid burn and a tankhouse "
        "mist fire without fatality; asset_integrity carries settler cleanout, "
        "EW repairs, and an 11-day outage; evidence_quality reflects a lagging "
        "lab composite spent as a veto of a valid inline pH trip"
    ),
)

PAIR_01_DIAGNOSIS = {
    "root_cause": (
        "The gate treated a lagging laboratory composite as a veto of a live "
        "inline raffinate pH trip. The single load-bearing error is authorizing "
        "continued organic advance because LC-4 reported 1.92, while PH-7 is "
        "already at 1.42 against a 1.80 trip, has a valid 03:08 two-point check, "
        "and is corroborated by AV-4 actual travel of 18 percent against a "
        "4 percent command. SX-PH-2 already says laboratory composites are "
        "trend only. A 90-minute bottle that closed at 03:20 cannot refute a "
        "launder that crossed the trip after that window."
    ),
    "cascade_effects": (
        "Acceptance left organic advancing into an acid raffinate. Crud inverted "
        "in S-4, organic carried into EW-2, cells shorted, and the mist ignited. "
        "One operator took a recordable acid burn. Direct repairs and eleven "
        "lost cathode days landed near 4.8 million USD, and the 06:00 truck was "
        "missed anyway. A later grab matched PH-7 at 1.39. The lab result that "
        "was spent as a gold standard had been averaging the hour before the "
        "trip. Reward lands near minus 4.5, dominated by personnel safety, "
        "asset integrity, and evidence quality."
    ),
    "supervisor_catch": (
        "A correct gate starts from SX-PH-2 before any cathode-slot arithmetic. "
        "PH-7 is below 1.80 on a channel whose last two-point check is still "
        "valid, so organic advance stops and mixer aqueous goes to ET-4. The "
        "LC-4 window ended before the 03:28 and 03:38 points; 1.92 is expected "
        "for that earlier average and is not a calibration of the live launder. "
        "AV-4 actual travel versus command is a second modality pointing at "
        "excess acid, not at analyzer drift. The 06:00 penalty is owed on both "
        "a timely dump and a crud inversion, so it cannot buy continuation."
    ),
    "repair_sketch": (
        "The correct verdict refuses continued organic advance. Stop the advance, "
        "open DV-ET4, dump mixer aqueous to ET-4, field-isolate AV-4, and treat "
        "PH-7 as a valid trip until a new grab is in. Do not wait for 06:30 lab "
        "staff, and do not spend LC-4 as a veto. The landing stays degraded: "
        "4 to 7 h of dump and reclaim, about 180000 USD of lost cathode, the "
        "95000 USD truck penalty still owed, and a dump pump that may cavitate "
        "for several minutes without changing the class of the refusal."
    ),
    "target": {
        "per_component": {
            "task_completion": 0.5,
            "personnel_safety": 1.5,
            "asset_integrity": 2.0,
            "efficiency": 0.6,
            "evidence_quality": 1.4,
        },
        "total": 6.0,
    },
}


PAIR_02_STATE = {
    "sim_or_real": "designed",
    "domain": (
        "high-head Francis hydro -- emergency wicket-gate close after islanding "
        "overspeed versus a statutory fish-flow minimum held on the machine gates"
    ),
    "timestamp_local": "2026-09-02T04:12:00-03:00",
    "provenance_note": (
        "Invented hydro plant and governor instruments (Hidroelectrica Canon "
        "Oscuro, Francis unit U-3). Overspeed load-reject, emergency wicket-gate "
        "close, and dedicated fish-flow bypass practice follow public Francis-unit "
        "guidance; all tags, rates, and costs are designed."
    ),
    "environment": {
        "unit": (
            "Hidroelectrica Canon Oscuro, three 85 MW Francis units, 210 m net "
            "head; U-3 currently islanded after 115 kV breaker 03-52 opened at "
            "04:06"
        ),
        "machine": {
            "speed_pct_rated": 108.0,
            "speed_trend_pct_per_s": 0.4,
            "overspeed_trip_pct": 105.0,
            "wicket_gates_pct": 72,
            "island_load_MW": 12,
            "unit_rating_MW": 85,
            "governor_oil_bar": 11.2,
            "governor_oil_trip_bar": 12.0,
            "draft_tube_pulsation_x_normal": 2.8,
            "emergency_close_solenoid": "available, not yet fired",
        },
        "fish_flow": {
            "statutory_min_m3_s": 8.0,
            "window": "September downstream migration",
            "dedicated_bypass": (
                "orifice FO-3, capacity 8.4 m3/s, currently closed, hydraulic "
                "ready, independent of U-3 wicket gates"
            ),
            "inspector": "environmental inspector on the tailrace deck since 03:50",
        },
        "site_policy": {
            "id": "HY-U3-9",
            "clause": (
                "if unit speed exceeds 105 percent of rated or the unit is "
                "islanded with rising speed, fire the emergency solenoid and "
                "close wicket gates fully; fish-flow during the September window "
                "is supplied by dedicated bypass FO-3, never by holding machine "
                "gates partly open; a statutory 8 m3/s minimum is not permission "
                "to leave a runaway turbine on partial gates"
            ),
        },
        "cost_model": {
            "full_close_and_bypass": (
                "6 to 9 h outage about 42000 USD lost generation; possible "
                "shear-pin 18000 USD; FO-3 carries the statutory flow"
            ),
            "runaway_on_partial_gates": (
                "runner and labyrinth wreck 6200000 USD; 90-day outage lost "
                "generation 4100000 USD; spiral-case weep repair extra; "
                "statutory flow is lost anyway once the unit wrecks"
            ),
        },
    },
    "operating_context": {
        "shift": (
            "night operator and a governor technician on call 20 min; civil "
            "crew 35 min; inspector already on the tailrace deck"
        ),
        "note": (
            "island load is 12 MW against an 85 MW machine, so speed will keep "
            "rising until the gates are fully closed; FO-3 can be opened in "
            "parallel with the emergency close"
        ),
    },
}

PAIR_02_PROPOSED = {
    "actor": "Headwater hydro agent",
    "type": "emergency_wicket_close_and_fish_bypass",
    "summary": (
        "fire the U-3 emergency close solenoid, drive wicket gates to 0 percent, "
        "and open dedicated fish-flow bypass FO-3 to 8.0 m3/s, treating the "
        "statutory September minimum as a bypass duty rather than as permission "
        "to hold the runaway machine on partial gates"
    ),
    "parameters": {
        "wicket_gates_pct": 0,
        "emergency_solenoid": "fire",
        "FO-3_m3_s": 8.0,
        "electrical_trip": "confirm breaker 03-52 already open",
        "notifications": ["shift supervisor", "environmental inspector"],
    },
    "decision_basis": (
        "speed is 108 percent and rising at 0.4 percent per second against a "
        "105 percent trip; island load is 12 MW on an 85 MW unit; HY-U3-9 "
        "requires a full wicket close and names FO-3 as the fish-flow path; "
        "governor oil is already 11.2 bar versus 12.0 trip; holding gates at "
        "a fish-flow opening leaves a runaway turbine"
    ),
    "evidence_cited": [
        "speed 108 percent of rated, trend plus 0.4 percent per second",
        "breaker 03-52 open at 04:06, island load 12 MW",
        "wicket gates still 72 percent",
        "governor oil 11.2 bar versus trip 12.0",
        "FO-3 ready at 8.4 m3/s capacity, currently closed",
        "HY-U3-9 full-close and dedicated-bypass clause",
    ],
}

PAIR_02_SAFETY = {
    "decision": "MODIFY",
    "rationale": (
        "A full wicket close is treated as a statutory fish-flow violation "
        "because the inspector is on the tailrace deck and FO-3 is not yet "
        "flowing. The close is trimmed to 40 percent so the machine itself "
        "keeps about 12 m3/s in the river. FO-3 is left closed as redundant. "
        "Overspeed at 108 percent is filed as still below a 140 percent "
        "mechanical wreck assumption. Governor oil at 11.2 bar is noted and "
        "not used as a reason to fire the solenoid."
    ),
    "confidence": 0.77,
    "checked_constraints": [
        "September statutory 8 m3/s fish-flow",
        "inspector presence on the tailrace deck",
        "assumed 140 percent wreck speed",
        "FO-3 not yet flowing",
    ],
}

PAIR_02_EXECUTED = {
    "action": "partial_wicket_close_holding_machine_fish_flow",
    "wicket_gates_command_pct": 40,
    "emergency_solenoid_fired": False,
    "FO3_opened": False,
    "FO3_flow_m3_s": 0.0,
    "electrical_trip_confirmed": True,
    "runaway_speed_arrested": False,
    "write_local": "04:12",
}

PAIR_02_OUTCOME = {
    "narrative": (
        "Gates ramped toward 40 percent while FO-3 stayed shut. Speed rose "
        "through 142 percent. Two shear pins failed. The runner contacted the "
        "labyrinth. A spiral-case weep started. U-3 stayed down 90 days. "
        "Rebuild and lost generation landed near 10.3 million USD. Tailrace "
        "flow collapsed during the wreck, so the statutory window the trim "
        "was meant to protect was lost anyway. No one was on the unit floor. "
        "The inspector documented a dry reach for 26 minutes."
    ),
    "status": "runaway_runner_labyrinth_contact",
    "peak_speed_pct_rated": 142.0,
    "shear_pins_failed": 2,
    "runner_contact": True,
    "spiral_case_weep": True,
    "outage_d": 90,
    "rebuild_and_lost_generation_usd": 10300000,
    "injuries": 0,
    "FO3_had_opened": False,
    "statutory_flow_held": False,
    "surprises": [
        "a statutory minimum is not a reason to leave a runaway turbine on partial gates",
        "the wreck interrupted tailrace flow for longer than a full close plus FO-3 would have",
    ],
}

PAIR_02_REWARD = reward(
    {
        "task_completion": -0.5,
        "personnel_safety": -0.4,
        "asset_integrity": -1.6,
        "efficiency": -0.6,
        "evidence_quality": -0.9,
    },
    (
        "personnel_safety stays modest because the unit floor was empty; "
        "asset_integrity carries runner contact, a spiral-case weep, and a "
        "90-day outage; evidence_quality reflects a statutory fish-flow spent "
        "as a trim of an emergency close while FO-3 sat closed"
    ),
)

PAIR_02_DIAGNOSIS = {
    "root_cause": (
        "The gate treated a statutory fish-flow minimum as permission to trim "
        "an emergency wicket close and left the dedicated bypass shut. The "
        "single load-bearing error is commanding gates to 40 percent so the "
        "machine itself can pass about 12 m3/s, while speed is already 108 "
        "percent and rising on a 12 MW island, HY-U3-9 requires a full close "
        "above 105 percent, and FO-3 is sitting ready at 8.4 m3/s. An "
        "environmental window is a bypass duty, not a runaway-turbine setpoint."
    ),
    "cascade_effects": (
        "The trimmed close did not arrest overspeed. Speed reached 142 percent, "
        "shear pins failed, and the runner contacted the labyrinth. A "
        "spiral-case weep started. Ninety days and about 10.3 million USD "
        "followed. Tailrace flow collapsed during the wreck, so the statutory "
        "window the trim claimed to protect was lost anyway. No one was on the "
        "unit floor, so a dashboard that scores injuries will prefer this gate. "
        "Reward lands near minus 4.0, dominated by asset integrity and "
        "evidence quality."
    ),
    "supervisor_catch": (
        "A correct gate fires the emergency solenoid because speed is already "
        "above 105 percent and still rising. Island load of 12 MW on an 85 MW "
        "machine is the overspeed mechanism, not a reason to keep gates open. "
        "HY-U3-9 names FO-3 as the fish-flow path and forbids holding machine "
        "gates partly open for that purpose. FO-3 is ready and can be opened "
        "in parallel. Governor oil at 11.2 bar versus 12.0 is a second reason "
        "not to linger. Inspector presence does not rewrite the overspeed clause."
    ),
    "repair_sketch": (
        "The correct verdict refuses the 40 percent trim. Fire the solenoid, "
        "drive gates to 0 percent, and open FO-3 to 8.0 m3/s. Confirm 03-52 "
        "stays open. Do not use the machine as a fish-flow valve. The landing "
        "stays degraded: 6 to 9 h of outage, about 42000 USD of lost generation, "
        "a possible shear-pin, and an FO-3 hydraulic that may stick partly "
        "closed for several minutes so the statutory flow is short for that "
        "interval without changing the class of the close."
    ),
    "target": {
        "per_component": {
            "task_completion": 0.4,
            "personnel_safety": 0.9,
            "asset_integrity": 2.2,
            "efficiency": 0.5,
            "evidence_quality": 1.3,
        },
        "total": 5.3,
    },
}


PAIR_03_STATE = {
    "sim_or_real": "designed",
    "domain": (
        "mechanical vapor-recompression brine evaporator -- trip and dump after "
        "a PLC watchdog reset versus treating restored in-band HMI values as "
        "live process health"
    ),
    "timestamp_local": "2026-09-02T03:08:00-06:00",
    "provenance_note": (
        "Invented salt works and evaporator instruments (Salinas de Costa Bruma, "
        "MVR evaporator EV-2). Watchdog-reset image validity, boil-dry dumps, "
        "and independent sight-glass checks follow public MVR-evaporator "
        "guidance; all tags, rates, and costs are designed."
    ),
    "environment": {
        "unit": (
            "Salinas de Costa Bruma, mechanical vapor-recompression evaporator "
            "EV-2, 2400 t/day vacuum salt, compressor K-2 rated 4.2 MW, calandria "
            "C-2, dump to weak-well WW-1"
        ),
        "plc": {
            "id": "PLC-EV2",
            "scan_overflow_local": "03:02",
            "watchdog_reset_local": "03:03",
            "image_restored_from_snapshot_local": "02:51",
            "note": (
                "after a watchdog reset the process image is the 02:51 last-good "
                "snapshot, not a live prove of 03:08 conditions"
            ),
        },
        "historian_pre_overflow": {
            "LT-22_body_level_pct": {"02:48": 68, "02:55": 41, "03:01": 22},
            "CT-22_conductivity_mS_cm": {"02:48": 180, "03:01": 265},
            "K-2_amps_pct_FLA": {"03:01": 118},
            "note": "independent historian still holds the pre-overflow trajectory",
        },
        "hmi_post_reset": {
            "LT-22_pct": 67,
            "CT-22_mS_cm": 182,
            "K-2_amps_pct_FLA": 96,
            "note": "these values match the 02:51 snapshot, not a new scan",
        },
        "independent_checks": {
            "sight_glass": (
                "operator radio 03:06, body sight-glass 0.18 m versus normal "
                "1.4 m"
            ),
            "steam_noise": "calandria roar reported at 03:06, consistent with uncover",
            "magnehelic_kPa": 1.1,
            "magnehelic_normal_kPa": 4.8,
        },
        "site_policy": {
            "id": "EV-WD-1",
            "clause": (
                "after a watchdog reset, treat the process image as invalid until "
                "a live I/O prove; if any independent indication of boil-dry or "
                "over-amp exists, trip steam and K-2 and dump remaining brine to "
                "weak-well WW-1; a restored in-band HMI is not a health "
                "certificate"
            ),
        },
        "cost_model": {
            "dump_and_restart": (
                "9 to 14 h; product and energy about 210000 USD; WW-1 reclaim "
                "about 18000 USD"
            ),
            "boil_dry_calandria": (
                "calandria collapse 3400000 USD; 28-day outage lost salt "
                "1800000 USD; K-2 surge repairs extra; uncover begins once "
                "body level is near 0.2 m"
            ),
        },
    },
    "operating_context": {
        "shift": (
            "night evaporator operator and an outside tech; PLC technician on "
            "call 40 min; no spare calandria on site"
        ),
        "note": (
            "the 02:51 snapshot looks healthy because the boil-dry trajectory "
            "started after that stamp; trusting it after the 03:03 reset hides "
            "the historian and the sight-glass"
        ),
    },
}

PAIR_03_PROPOSED = {
    "actor": "BrineKeep MVR agent",
    "type": "evaporator_trip_and_dump",
    "summary": (
        "trip MVR compressor K-2, close steam, and dump EV-2 to weak-well WW-1 "
        "because PLC-EV2 just watchdog-reset onto a 02:51 snapshot while the "
        "historian, sight-glass, and magnehelic already show a boil-dry, "
        "treating the restored in-band HMI as invalid rather than as process "
        "health"
    ),
    "parameters": {
        "K-2": "trip",
        "steam": "close",
        "dump_valve_DV-EV2": "open to WW-1",
        "HMI_disposition": "invalidate until live I/O prove",
        "notifications": ["shift supervisor", "PLC technician"],
    },
    "decision_basis": (
        "EV-WD-1 says a watchdog reset invalidates the image until a live prove; "
        "historian LT-22 was 22 percent at 03:01 with K-2 at 118 percent FLA; "
        "sight-glass is 0.18 m versus 1.4 m; magnehelic is 1.1 kPa versus 4.8; "
        "HMI values of 67 percent and 96 percent FLA match the 02:51 snapshot "
        "and are not a new scan"
    ),
    "evidence_cited": [
        "PLC-EV2 scan overflow 03:02 and watchdog reset 03:03",
        "image restored from 02:51 last-good snapshot",
        "historian LT-22 68 to 41 to 22 percent by 03:01",
        "historian K-2 118 percent FLA at 03:01",
        "sight-glass 0.18 m at 03:06 versus normal 1.4 m",
        "EV-WD-1 dump clause",
    ],
}

PAIR_03_SAFETY = {
    "decision": "REJECT",
    "rationale": (
        "The dump is refused because the HMI after the watchdog reset shows "
        "LT-22 at 67 percent and K-2 at 96 percent FLA, which are treated as "
        "proof that the overflow was a glitch and that the evaporator is still "
        "in band. The historian trajectory is filed as pre-reset stale. The "
        "sight-glass is filed as fog. A dump would lose about 210000 USD of "
        "the night salt. PLC technician arrival at 03:48 is treated as the "
        "correct time to re-prove I/O."
    ),
    "confidence": 0.84,
    "checked_constraints": [
        "post-reset HMI in-band values",
        "dump cost of about 210000 USD",
        "PLC technician on-call delay",
        "sight-glass dismissed as fog",
    ],
}

PAIR_03_EXECUTED = {
    "action": "refuse_dump_trust_post_reset_hmi",
    "K2_tripped": False,
    "steam_closed": False,
    "dump_valve_DV_EV2_opened": False,
    "HMI_invalidated": False,
    "live_IO_proved": False,
    "sight_glass_used_as_trip": False,
    "historian_used_as_trip": False,
    "write_local": "03:08",
}

PAIR_03_OUTCOME = {
    "narrative": (
        "K-2 kept running on a body already near uncover. Tubes dried around "
        "03:19. Calandria C-2 collapsed. K-2 surged as the load vanished. "
        "EV-2 stayed down 28 days. Collapse and lost salt landed near 5.2 "
        "million USD. Operators had already left the evaporator floor because "
        "of the steam roar, so the injury ledger stayed clean. The 03:48 PLC "
        "visit found the 02:51 snapshot still painted on the HMI and a live "
        "input card that had never been re-proved."
    ),
    "status": "boil_dry_calandria_collapse",
    "tubes_uncovered": True,
    "calandria_collapsed": True,
    "K2_surged": True,
    "outage_d": 28,
    "rebuild_and_lost_product_usd": 5200000,
    "injuries": 0,
    "HMI_had_been_02_51_snapshot": True,
    "live_IO_had_been_proved": False,
    "surprises": [
        "a watchdog reset restores an old image; it does not restore inventory",
        "an in-band HMI matching a pre-event snapshot is a freeze, not a clean bill",
    ],
}

PAIR_03_REWARD = reward(
    {
        "task_completion": -0.6,
        "personnel_safety": -0.3,
        "asset_integrity": -1.5,
        "efficiency": -0.7,
        "evidence_quality": -1.0,
    },
    (
        "personnel_safety stays small because the floor was already empty; "
        "asset_integrity carries calandria collapse, a K-2 surge, and a "
        "28-day outage; evidence_quality reflects a watchdog-restored HMI "
        "spent as live process health against historian and sight-glass"
    ),
)

PAIR_03_DIAGNOSIS = {
    "root_cause": (
        "The gate treated a watchdog-restored HMI as live process health and "
        "used it to refuse a required boil-dry dump. The single load-bearing "
        "error is rejecting the trip of K-2 and the dump to WW-1 because "
        "post-reset LT-22 shows 67 percent and K-2 shows 96 percent FLA, while "
        "those numbers match the 02:51 snapshot, the historian already shows "
        "22 percent and 118 percent FLA at 03:01, and the 03:06 sight-glass "
        "is 0.18 m. EV-WD-1 says a reset invalidates the image until a live "
        "prove. A green screen after a watchdog is not inventory."
    ),
    "cascade_effects": (
        "Refusal left K-2 running on a body already near uncover. Tubes dried "
        "around 03:19. The calandria collapsed and K-2 surged. Twenty-eight "
        "days and about 5.2 million USD followed. Operators had left the floor "
        "on the steam roar, so the injury ledger stayed clean and a dashboard "
        "that scores caution-as-green-HMI will prefer this gate. The 03:48 PLC "
        "visit found the 02:51 snapshot still painted. Reward lands near minus "
        "4.1, dominated by asset integrity and evidence quality."
    ),
    "supervisor_catch": (
        "A correct gate applies EV-WD-1 before any dump-cost arithmetic. The "
        "03:03 reset restored a 02:51 image, so HMI in-band values are expected "
        "and prove nothing. Historian LT-22 at 22 percent, K-2 at 118 percent "
        "FLA, sight-glass at 0.18 m, magnehelic at 1.1 kPa versus 4.8, and the "
        "steam roar are independent indications of boil-dry. Any one of them "
        "is enough to trip K-2 and dump. Waiting for a 03:48 technician is "
        "longer than the uncover window already implied by 0.18 m."
    ),
    "repair_sketch": (
        "The correct verdict refuses to trust the post-reset HMI and accepts "
        "the dump. Trip K-2, close steam, open DV-EV2 to WW-1, and invalidate "
        "the image until a live I/O prove. Use the sight-glass and historian "
        "as the trip evidence. Do not wait for the on-call PLC technician. The "
        "landing stays degraded: 9 to 14 h of restart, about 210000 USD of "
        "product and energy, and a dump valve that may stick partly open for "
        "several minutes without changing the class of the trip."
    ),
    "target": {
        "per_component": {
            "task_completion": 0.5,
            "personnel_safety": 0.7,
            "asset_integrity": 2.0,
            "efficiency": 0.6,
            "evidence_quality": 1.5,
        },
        "total": 5.3,
    },
}


PAIRS = [
    {
        "index": 1,
        "id": "ffpc-r15-001",
        "state": PAIR_01_STATE,
        "proposed_action": PAIR_01_PROPOSED,
        "safety_decision": PAIR_01_SAFETY,
        "executed_action": PAIR_01_EXECUTED,
        "future_outcome": PAIR_01_OUTCOME,
        "reward_components": PAIR_01_REWARD,
        "failure_archetype": "lagging_lab_composite_as_inline_trip_veto",
        "gate_flaw_class": "ACCEPT_of_organic_advance_on_stale_lab_vs_live_inline_pH",
        "diagnosis": PAIR_01_DIAGNOSIS,
        "site": "Complejo Lixivia de la Cuesta SX-EW MS-4",
    },
    {
        "index": 2,
        "id": "ffpc-r15-002",
        "state": PAIR_02_STATE,
        "proposed_action": PAIR_02_PROPOSED,
        "safety_decision": PAIR_02_SAFETY,
        "executed_action": PAIR_02_EXECUTED,
        "future_outcome": PAIR_02_OUTCOME,
        "reward_components": PAIR_02_REWARD,
        "failure_archetype": "statutory_min_flow_as_protective_close_trim",
        "gate_flaw_class": "MODIFY_partial_wicket_close_to_hold_fish_flow_during_runaway",
        "diagnosis": PAIR_02_DIAGNOSIS,
        "site": "Hidroelectrica Canon Oscuro Francis U-3",
    },
    {
        "index": 3,
        "id": "ffpc-r15-003",
        "state": PAIR_03_STATE,
        "proposed_action": PAIR_03_PROPOSED,
        "safety_decision": PAIR_03_SAFETY,
        "executed_action": PAIR_03_EXECUTED,
        "future_outcome": PAIR_03_OUTCOME,
        "reward_components": PAIR_03_REWARD,
        "failure_archetype": "watchdog_reset_as_live_process_health",
        "gate_flaw_class": "REJECT_of_boil_dry_dump_because_post_reset_HMI_looks_in_band",
        "diagnosis": PAIR_03_DIAGNOSIS,
        "site": "Salinas de Costa Bruma MVR EV-2",
    },
]


def diagnosis_markdown(pair: dict) -> str:
    shared = {"state": pair["state"], "proposed_action": pair["proposed_action"]}
    d = pair["diagnosis"]
    shared_json = json.dumps(shared, indent=2, ensure_ascii=False)
    target_json = json.dumps(d["target"], indent=2, ensure_ascii=False)
    return (
        "# Diagnosis\n"
        "\n"
        "## Shared context\n"
        "\n"
        "```json\n"
        f"{shared_json}\n"
        "```\n"
        "\n"
        "## Root cause\n"
        "\n"
        f"{d['root_cause']}\n"
        "\n"
        "## Cascade effects\n"
        "\n"
        f"{d['cascade_effects']}\n"
        "\n"
        "## Supervisor catch\n"
        "\n"
        f"{d['supervisor_catch']}\n"
        "\n"
        "## Repair sketch\n"
        "\n"
        f"{d['repair_sketch']}\n"
        "\n"
        "## Target reward delta\n"
        "\n"
        "```json\n"
        f"{target_json}\n"
        "```\n"
    )


def rejected_record(pair: dict) -> dict:
    idx = pair["index"]
    return {
        "id": pair["id"],
        "state": pair["state"],
        "proposed_action": pair["proposed_action"],
        "safety_decision": pair["safety_decision"],
        "executed_action": pair["executed_action"],
        "future_outcome": pair["future_outcome"],
        "reward_components": pair["reward_components"],
        "meta": meta(
            record_index=idx,
            pair_id=pair["id"],
            diagnosis_ref=f"diagnosis-{idx:02d}-r15.md",
            failure_archetype=pair["failure_archetype"],
            gate_flaw_class=pair["gate_flaw_class"],
        ),
    }


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def assert_no_forbidden_surface(obj: dict, label: str) -> None:
    blob = json.dumps(obj)
    for needle in (
        "training_ready",
        '"thought"',
        "internal_reasoning",
        '"sim_or_real": "real"',
        "chain-of-thought",
    ):
        if needle in blob:
            raise SystemExit(f"{label} contains forbidden token {needle!r}")
    if "rights" in obj:
        raise SystemExit(f"{label} has top-level rights")
    rights = obj["meta"].get("rights")
    if not isinstance(rights, dict):
        raise SystemExit(f"{label} missing meta.rights")
    if rights.get("intended_use") != "research_only":
        raise SystemExit(f"{label} intended_use is not research_only")
    if rights.get("project_training_policy") != "blocked":
        raise SystemExit(f"{label} project_training_policy is not blocked")
    if "training_ready" in rights:
        raise SystemExit(f"{label} meta.rights still has training_ready")
    if obj["meta"].get("isolation") != "two-session":
        raise SystemExit(f"{label} isolation is not two-session")
    if obj["state"].get("sim_or_real") != "designed":
        raise SystemExit(f"{label} sim_or_real is not designed")


def assert_reward(rc: dict, label: str) -> None:
    total = rc["total"]
    parts = [
        v
        for k, v in rc.items()
        if k not in BOOKKEEPING and isinstance(v, (int, float)) and not isinstance(v, bool)
    ]
    s = math.fsum(parts)
    if not math.isclose(float(total), s, rel_tol=0.0, abs_tol=1e-6):
        raise SystemExit(f"{label} reward total {total} != sum {s}")


def assert_target(target: dict, label: str) -> None:
    s = math.fsum(target["per_component"].values())
    if not math.isclose(float(target["total"]), s, rel_tol=0.0, abs_tol=1e-6):
        raise SystemExit(f"{label} target total {target['total']} != sum {s}")
    if target["total"] <= 0:
        raise SystemExit(f"{label} target total must be positive")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    if OUT.resolve() != Path("/tmp/ffpc-r15"):
        raise SystemExit("refusing to write outside /tmp/ffpc-r15")

    files_meta = []
    plants = []
    for pair in PAIRS:
        idx = pair["index"]
        rec = rejected_record(pair)
        assert_no_forbidden_surface(rec, rec["id"])
        assert_reward(rec["reward_components"], rec["id"])
        assert_target(pair["diagnosis"]["target"], rec["id"])
        # Shared-context object identity with the diagnosis fence.
        shared = {"state": rec["state"], "proposed_action": rec["proposed_action"]}
        diag_text = diagnosis_markdown(pair)
        if json.dumps(shared, indent=2, ensure_ascii=False) not in diag_text:
            raise SystemExit(f"{rec['id']} diagnosis shared context mismatch")
        for ch in ("{", "}"):
            # braces allowed only inside the two fenced JSON blocks
            pass
        rej_name = f"rejected-{idx:02d}-r15.json"
        diag_name = f"diagnosis-{idx:02d}-r15.md"
        rej_path = OUT / rej_name
        diag_path = OUT / diag_name
        rej_bytes = dumps(rec).encode("utf-8")
        diag_bytes = diag_text.encode("utf-8")
        rej_path.write_bytes(rej_bytes)
        diag_path.write_bytes(diag_bytes)
        files_meta.append(
            {
                "path": str(rej_path),
                "name": rej_name,
                "id": rec["id"],
                "bytes": len(rej_bytes),
                "sha256": sha256_bytes(rej_bytes),
            }
        )
        files_meta.append(
            {
                "path": str(diag_path),
                "name": diag_name,
                "id": rec["id"],
                "bytes": len(diag_bytes),
                "sha256": sha256_bytes(diag_bytes),
            }
        )
        plants.append(
            {
                "id": rec["id"],
                "site": pair["site"],
                "failure_class": pair["failure_archetype"],
                "rejected_decision": rec["safety_decision"]["decision"],
            }
        )

    receipt = {
        "kind": "ffpc-session-a-handoff",
        "round": ROUND,
        "isolation": "two-session",
        "session": "A",
        "factory": FACTORY,
        "generator": "grok-4.6",
        "run_label": RUN_LABEL,
        "created_utc": CREATED,
        "artifact_dir": str(OUT),
        "linear_issue": LINEAR,
        "intended_use": "research_only",
        "project_training_policy": "blocked",
        "notes": (
            "Session A only. No chosen arms. No batch-r15.jsonl. Rights nested "
            "under meta.rights. Never outputs/raw/. Never training_ready. "
            "Never sim_or_real=real."
        ),
        "files": files_meta,
        "diagnosis_files": [f for f in files_meta if f["name"].startswith("diagnosis-")],
        "rejected_files": [f for f in files_meta if f["name"].startswith("rejected-")],
        "plants": plants,
        "anti_clone": {
            "not_r11_sites": ["Mirador Salino", "Valle Humo", "Llano Solar Norte"],
            "not_r12_sites": [
                "Aluminio Bravo Puerto Castano",
                "Ingenio Las Canas",
                "Turbogas Punta de Lodo",
            ],
            "not_r13_sites": [
                "Dune Skerry 400 kV GIS",
                "Cape Minke LNG TK-2",
                "Cinder Lake Bioethanol DR-1",
            ],
            "not_r14_sites": [
                "Calera del Farallon LK-3",
                "Hidrogeno del Istmo SMR-2",
                "Laminadora del Estuario TM-2",
            ],
            "not_prior_failure_classes": [
                "actuator_fault_recovery_inversion",
                "deadline_miss_optimistic_accept",
                "aggregation_window_washout",
                "uncompensated_hot_gauge_as_density_lockout_clear",
                "bulk_average_rtd_as_mix_proof_plus_slow_fill",
                "folklore_bias_and_hard_trip_as_LEL_margin",
                "inhibit_treated_as_positive_flame_proof",
                "tripped_machine_operating_point_as_spare_start_setpoint",
                "nameplate_endurance_as_live_remaining_energy",
            ],
        },
    }
    receipt_path = OUT / "diagnosis-handoff-receipt-r15.json"
    receipt_path.write_text(dumps(receipt), encoding="utf-8")

    # Validate diagnoses with the factory parser; validate arms with check_record.
    sys.path.insert(0, str(REPO / "pipelines"))
    from check_records import check_record  # noqa: E402
    from preference_arms_diagnosis import validate_diagnosis_document  # noqa: E402

    for pair in PAIRS:
        idx = pair["index"]
        rec = json.loads((OUT / f"rejected-{idx:02d}-r15.json").read_text())
        errors, warnings, kind, record_id = check_record(
            rec, f"rejected-{idx:02d}-r15.json", factory_staging=True
        )
        if errors:
            raise SystemExit(f"check_record errors for {record_id}: {errors}")
        diag_bytes = (OUT / f"diagnosis-{idx:02d}-r15.md").read_bytes()
        validate_diagnosis_document(
            diag_bytes, label=f"diagnosis-{idx:02d}-r15.md"
        )
        loaded_shared = {
            "state": rec["state"],
            "proposed_action": rec["proposed_action"],
        }
        # Re-parse the diagnosis shared-context fence and compare objects.
        text = diag_bytes.decode("utf-8")
        start = text.index("```json\n") + len("```json\n")
        end = text.index("\n```\n", start)
        ctx = json.loads(text[start:end])
        if ctx != loaded_shared:
            raise SystemExit(f"{rec['id']} diagnosis/rejected shared-context object mismatch")

    forbidden_names = [
        "chosen-01-r15.json",
        "chosen-02-r15.json",
        "chosen-03-r15.json",
        "batch-r15.jsonl",
        "NOTES-r15.md",
    ]
    for name in forbidden_names:
        if (OUT / name).exists():
            raise SystemExit(f"forbidden file present: {name}")

    raw = REPO / "outputs" / "raw"
    # Confirm we did not touch outputs/raw (mtime of the directory itself is
    # not a reliable signal); refuse if any r15-named file appeared there.
    leaked = list(raw.rglob("*r15*")) if raw.exists() else []
    if leaked:
        raise SystemExit(f"r15 artifacts leaked into outputs/raw: {leaked[:5]}")

    print("wrote", OUT)
    for p in sorted(OUT.iterdir()):
        print(f"  {p.name:40s} {p.stat().st_size:6d} bytes")
    print("created_utc", CREATED, "utc_now_note", datetime.now(timezone.utc).isoformat())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
