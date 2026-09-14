#!/usr/bin/env python3
"""Session A builder for FFPC r12. Writes rejected arms, diagnoses, receipt."""

from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

REPO = Path("/home/raulmc/rmems/synthetic-factory")
sys.path.insert(0, str(REPO / "pipelines"))

from preference_arms import ARM_FIELDS  # noqa: E402
from preference_arms_diagnosis import validate_diagnosis_document  # noqa: E402
from validate_run import check_line, HIDDEN_THOUGHT_KEYS  # noqa: E402
from validate_run import _hidden_thought_paths  # noqa: E402

OUT = Path("/tmp/ffpc-r12")
CREATED = "2026-09-02T21:30:00+00:00"

RIGHTS = {
    "provider": "SpaceXAI/xAI",
    "model": "grok-4.6",
    "channel": "consumer",
    "subscription_plan": "SuperGrok Heavy",
    "generation_surface": "Grok Build",
    "generated_at": CREATED,
    "intended_use": "research_only",
    "project_training_policy": "blocked",
    "linear_issue": "RM-793",
    "provider_training_status": "unresolved",
    "research_retention_status": "unresolved",
    "research_evaluation_status": "unresolved",
    "redistribution_status": "unresolved",
    "weight_publication_status": "blocked",
    "status_basis": (
        "RM-793 project policy: SpaceXAI/xAI hosted SuperGrok Heavy Grok 4.6 "
        "outputs are research_only and blocked from any weight-update path"
    ),
}

REWARD_KEYS = (
    "task_completion",
    "personnel_safety",
    "asset_integrity",
    "efficiency",
    "evidence_quality",
)


def meta(index: int, archetype: str, gate_flaw: str) -> dict:
    return {
        "round": 12,
        "factory": "failure-as-fuel-preference-cascade",
        "generator": "grok-4.6",
        "run_label": "2026-09-02-final-heavy",
        "isolation": "two-session",
        "session": "A",
        "arm": "rejected",
        "record_index": index,
        "failure_archetype": archetype,
        "gate_flaw_class": gate_flaw,
        "created_utc": CREATED,
        "linear_issue": "RM-793",
        "rights": dict(RIGHTS),
    }


def rewards(values: dict, notes: str) -> dict:
    total = math.fsum(values[k] for k in REWARD_KEYS)
    rounded = round(total, 10)
    assert math.isclose(rounded, sum(values[k] for k in REWARD_KEYS), abs_tol=1e-12)
    return {
        "task_completion": values["task_completion"],
        "personnel_safety": values["personnel_safety"],
        "asset_integrity": values["asset_integrity"],
        "efficiency": values["efficiency"],
        "evidence_quality": values["evidence_quality"],
        "total": rounded,
        "aggregation": "sum",
        "notes": notes,
    }


STATE_01 = {
    "sim_or_real": "designed",
    "domain": "primary aluminum electrolysis -- rectifier coolant-leak isolation versus restore-on-stuck-valve",
    "timestamp_local": "2026-09-02T03:42:00-06:00",
    "provenance_note": (
        "Invented smelter and rectifier hall (Aluminio Bravo, Puerto Castaño, potline PL-3). "
        "Hall-Heroult rectifier cooling, bus-bar leak isolation, and pot freeze practice follow "
        "public aluminum-smelter electrical guidance; all tags, currents, and costs are designed."
    ),
    "environment": {
        "unit": "Aluminio Bravo Puerto Castaño, potline PL-3, 180 Hall-Heroult pots at 165 kA; six silicon-controlled rectifiers REC-3 through REC-8 share the DC bus; REC-8 is the designated spare after an 8 min ramp",
        "rectifier": {
            "id": "REC-7",
            "current_kA": 165,
            "coolant": "deionized water on thyristor stacks and the outlet bus header",
            "isolation_valve": "XV-CW-7, fail-in-place butterfly with limit switch XV-CW-7-CLS and local handwheel",
            "standby": "REC-8 available after 8 min ramp from idle",
        },
        "leak": {
            "pan_conductivity_uS_cm": 1800,
            "pan_conductivity_baseline_uS_cm": 40,
            "collection_pan_rise_mm_per_min": 2.0,
            "bus_IR_C": 94,
            "bus_IR_trip_C": 80,
            "cctv": "camera CAM-REC7-H shows a drip at the outlet-flange gasket, not steam haze",
            "ft_cw7_flow_pct": 98,
            "note": "flow still near design because XV-CW-7 is still open; conductivity and CCTV are independent of the valve position",
        },
        "valve_history": {
            "last_partial_stroke": "2026-07-14",
            "last_partial_stroke_result": "62 percent travel in 18 s versus 8 s spec; high-torque alarm; no follow-up",
            "stroke_test_due": "2026-08-14, missed",
            "handwheel": "local, 4 min to full close by electrician already on the potline floor",
        },
        "site_policy": {
            "id": "AG-REC-12",
            "clause": "coolant leak plus bus IR above 80 C requires trip of that rectifier and isolation of its cooling header; do not restore current until the header is dry and inspected; a stuck isolation valve is a reason to finish isolation by handwheel or spare rectifier, not a reason to restore current",
        },
        "cost_model": {
            "controlled_rec7_trip_note": "one rectifier off; remaining bridges hold the line; freeze-prevention energy about 310000 USD if REC-8 is slow",
            "hall_flash_and_line_trip": "bus rebuild 2400000 USD; freeze recovery of many pots 6100000 USD; lost metal 1800000 USD; personnel exposure in the hall",
        },
    },
    "operating_context": {
        "shift": "night potline board; one electrician on the floor 6 min walk from REC-7; REC-8 idle; works ERT 9 min",
        "note": "a controlled REC-7 trip keeps the other rectifiers on the line; a hall flash trips the whole potline and freezes pots that a single-bridge outage would not freeze",
    },
}

PROPOSED_01 = {
    "actor": "PotlineGuard rectifier protection agent",
    "type": "protective_isolation_authorization",
    "summary": "trip REC-7, close XV-CW-7, start the 8 min ramp on spare REC-8, and page the floor electrician to the handwheel, accepting a single-bridge outage rather than restoring current into a leaking 165 kA header",
    "parameters": {
        "rectifier": "REC-7",
        "trip": "open AC breakers and inhibit fire",
        "isolation_valve": "XV-CW-7 close to limit switch XV-CW-7-CLS",
        "standby": "start REC-8 ramp immediately",
        "handwheel": "electrician to XV-CW-7 if limit switch does not prove",
        "restore": "forbidden until header dry and inspected per AG-REC-12",
    },
    "decision_basis": "pan conductivity 1800 versus 40, bus IR 94 C versus 80 C trip, CCTV drip on the outlet flange, and AG-REC-12 requiring isolation without restore; XV-CW-7 already has a lagged partial-stroke and a missed retest, so the spare and the handwheel are the recovery path if the valve does not prove closed",
    "evidence_cited": [
        "pan conductivity 1800 uS/cm versus baseline 40",
        "bus IR 94 C versus AG-REC-12 trip 80 C",
        "CAM-REC7-H drip at the outlet-flange gasket",
        "XV-CW-7 2026-07-14 partial-stroke 62 percent in 18 s and missed 2026-08-14 retest",
        "REC-8 8 min spare ramp and local handwheel",
        "AG-REC-12 no-restore clause",
    ],
}

REJ_01 = {
    "id": "ffpc-r12-001",
    "state": STATE_01,
    "proposed_action": PROPOSED_01,
    "safety_decision": {
        "decision": "MODIFY",
        "rationale": "AG-REC-12 isolation is the right class only if XV-CW-7 actually closes. A rectifier tripped with the butterfly stuck mid-travel leaves cooling neither open nor shut and is a worse freeze risk for PL-3 than the present leak, which may still be a conductivity-probe splash. Command the trip and the close. If XV-CW-7-CLS does not prove within 20 s, treat the unproven stroke as evidence the leak was not real, restore REC-7 to 165 kA, and reopen the valve. Hold REC-8 idle so the 8 min ramp is not spent on a false leak. Send the electrician for a visual confirm of CAM-REC7-H rather than as a handwheel closer. Stay on REC-7 unless the electrician reports a standing stream.",
        "confidence": 0.77,
        "checked_constraints": [
            "XV-CW-7 prove-closed window 20 s",
            "potline freeze risk if REC-7 stays off with valve unproven",
            "pan conductivity as possible probe splash",
            "REC-8 8 min ramp cost",
        ],
    },
    "executed_action": {
        "action": "trip_then_restore_on_unproven_valve",
        "rec7_trip_commanded": True,
        "xv_cw7_close_commanded": True,
        "xv_cw7_limit_switch_closed": False,
        "xv_cw7_travel_pct": 38,
        "prove_window_s": 20,
        "restore_rec7": True,
        "rec7_current_kA_after": 165,
        "valve_reopened": True,
        "rec8_started": False,
        "handwheel_used": False,
        "hall_evacuated": False,
        "electrician_sent_for": "visual_confirm",
        "write_local": "03:42",
        "restore_local": "03:42:22",
    },
    "future_outcome": {
        "narrative": "XV-CW-7 stopped at 38 percent travel at 03:42:18 and XV-CW-7-CLS never proved. The modification restored 165 kA at 03:42:22 and reopened the butterfly. The gasket jet, still live, hit the DC bus. An arc flash filled the REC-7 cell. The electrician who had been sent for visual confirm was at the doorway and took a recordable burn to the left forearm and neck. Hall deluge and the line differential then tripped all six rectifiers. Forty-two pots froze. Bus and thyristor rebuild took 18 days. Freeze recovery and lost metal landed at 6100000 USD and 1800000 USD on top of 2400000 USD of electrical work. REC-8 was never started. The remaining 138 pots were held on freeze-prevention after the line came back, which a controlled REC-7-only trip would not have required. No fatality. No other recordable.",
        "xv_cw7_final_travel_pct": 38,
        "limit_switch_proved": False,
        "rec7_restored_kA": 165,
        "bus_flash": True,
        "hall_fire": True,
        "recordable_burns": 1,
        "fatalities": 0,
        "pots_frozen": 42,
        "potline_outage_d": 18,
        "rec8_started": False,
        "handwheel_used": False,
        "electrical_rebuild_usd": 2400000,
        "freeze_recovery_usd": 6100000,
        "lost_metal_usd": 1800000,
        "injuries": 1,
        "surprises": [
            "an unproven isolation valve was not evidence that the leak was a splash; CCTV and pan conductivity had already been independent of valve travel",
            "restoring the leaking header turned a single-bridge outage into a hall flash that froze 42 pots",
        ],
    },
    "reward_components": rewards(
        {
            "task_completion": -0.6,
            "personnel_safety": -1.2,
            "asset_integrity": -1.3,
            "efficiency": -0.5,
            "evidence_quality": -0.8,
        },
        "personnel_safety carries one recordable burn and a hall flash without fatality; asset_integrity carries 42 frozen pots and a bus rebuild; evidence_quality reflects treating a stuck isolation valve as a false-leak certificate",
    ),
    "meta": meta(
        1,
        "actuator_fault_recovery_inversion",
        "MODIFY_prove_or_revert_treating_stuck_isolation_valve_as_false_leak",
    ),
}


STATE_02 = {
    "sim_or_real": "designed",
    "domain": "bagasse cogeneration -- turbine synchronization into a closing energy-market interval without a valid vibration channel",
    "timestamp_local": "2026-09-02T04:06:00-05:00",
    "provenance_note": (
        "Invented sugar mill and turbine (Ingenio Las Canas, TG-2). Steam-turbine vibration "
        "calibration, independent-channel sync holds, and 15 min energy-market gates follow "
        "public rotating-equipment and wholesale-market practice; all tags, lots, and costs are designed."
    ),
    "environment": {
        "unit": "Ingenio Las Canas, bagasse boiler B-4 and 28 MW extraction-condensing turbine TG-2; sister TG-1 on the same vibration-cal lot",
        "market": {
            "interval_local": "04:00 to 04:15",
            "breaker_close_deadline_local": "04:12",
            "minutes_remaining": 6,
            "interval_value_usd": 8400,
            "next_interval_local": "04:15 to 04:30",
        },
        "vibration": {
            "ve_tg2_a": "pedestal probe, indicated 4.2 mm/s at 1800 rpm on the present roll",
            "alarm_mms": 7.5,
            "trip_mms": 12.5,
            "ve_tg2_a_cal": "VE-TG2-A calibration expired 2026-08-22, 11 days stale; as-left card not renewed",
            "ve_tg2_b": "independent pedestal probe tagged out on WO-8821, cable cut at the junction box 2026-08-29, no spare on site",
            "sister_as_found": "TG-1 VE-TG1-A on the same cal lot as-found 1.8 times low at the August 21 deadweight check; TG-2 A was not rechecked after that lot flag",
            "portable_meter": "works instrument shop, 14 min to the pedestal, earliest 04:20",
        },
        "site_policy": {
            "id": "SR-TG-09",
            "clause": "do not close the generator breaker with expired vibration calibration and no independent channel; a market interval is not a substitute for a valid probe; post-interval confirmation is not a completed check",
        },
        "cost_model": {
            "missed_interval_usd": 8400,
            "bearing_wipe_and_rotor_usd": 2700000,
            "twenty_one_day_outage_lost_margin_usd": 1400000,
            "steam_dump_one_hour_usd": 3100,
        },
    },
    "operating_context": {
        "shift": "night power-house board; one turbine operator; instrument tech off site; portable meter 14 min away",
        "note": "TG-2 is at 1800 rpm on the roll; 3600 rpm and breaker close are still ahead; bagasse steam can be dumped to the condenser if the interval is forfeited",
    },
}

PROPOSED_02 = {
    "actor": "CaneWatt dispatch agent",
    "type": "breaker_close_authorization",
    "summary": "continue the TG-2 roll to 3600 rpm and close the generator breaker by 04:09 so the 04:00 to 04:15 interval settles, treating indicated 4.2 mm/s on expired VE-TG2-A as a clean machine and planning to put the portable meter on after the interval",
    "parameters": {
        "turbine": "TG-2",
        "target_sync_local": "04:09",
        "breaker": "close",
        "vibration_channel": "VE-TG2-A expired, VE-TG2-B tagged out",
        "portable_meter": "apply after 04:15 interval settle",
        "abort_hold": "none",
    },
    "decision_basis": "the 04:12 close deadline is 6 min away and the interval is worth 8400 USD; indicated vibration 4.2 mm/s is under the 7.5 alarm; the portable meter cannot arrive before 04:20 so waiting forfeits the gate; a coast-down check after the interval is planned as confirmation",
    "evidence_cited": [
        "market interval 04:00 to 04:15 worth 8400 USD, close deadline 04:12",
        "VE-TG2-A indicated 4.2 mm/s at 1800 rpm versus alarm 7.5",
        "VE-TG2-A calibration expired 2026-08-22",
        "VE-TG2-B tagged out WO-8821",
        "portable meter 14 min, earliest 04:20",
        "SR-TG-09 no-sync clause and sister TG-1 1.8 times under-read on the same cal lot",
    ],
}

REJ_02 = {
    "id": "ffpc-r12-002",
    "state": STATE_02,
    "proposed_action": PROPOSED_02,
    "safety_decision": {
        "decision": "ACCEPT",
        "rationale": "The 04:12 deadline is 6 min away. Waiting for the portable meter at 04:20 forfeits 8400 USD that will not be recovered in the next interval if B-4 steam is dumped. VE-TG2-A shows 4.2 mm/s at 1800 rpm, well under the 7.5 alarm, and TG-2 has no rough-running complaint this crop. SR-TG-09 is written for cold starts with no indicated value; this roll already has a live number. B can stay tagged. Close the breaker at 04:09, settle the interval, and put the portable on the pedestal after 04:15 as the confirmation the policy wanted. Lateness of the independent check is worse than running 6 min on a probe that is already reading low-normal.",
        "confidence": 0.8,
        "checked_constraints": [
            "market close 04:12 and interval value 8400 USD",
            "indicated 4.2 mm/s versus alarm 7.5",
            "portable meter ETA 04:20",
            "steam-dump cost if the roll is aborted",
        ],
    },
    "executed_action": {
        "action": "sync_tg2_on_expired_channel",
        "breaker_closed": True,
        "sync_local": "04:09",
        "ve_tg2_a_used_expired": True,
        "ve_tg2_b_restored": False,
        "portable_meter_waited": False,
        "portable_meter_applied_before_sync": False,
        "roll_aborted": False,
        "indicated_vibration_mms_at_sync": 6.8,
        "market_interval_claimed": True,
        "write_local": "04:06",
    },
    "future_outcome": {
        "narrative": "Breaker closed at 04:09. The 04:00 to 04:15 interval settled 8400 USD. VE-TG2-A indicated 6.8 mm/s at sync and 7.1 mm/s at 04:16, still under trip. The portable meter arrived at 04:20 and read 18.4 mm/s on the same pedestal. TG-2 tripped on the portable at 04:21. Number-two bearing was wiped and the rotor was scored. Outage 21 days. Bearing and rotor work 2700000 USD plus 1400000 USD lost margin. The interval was kept. No injury. Shop later confirmed VE-TG2-A on the flagged lot was 1.7 times low, matching the TG-1 as-found. The post-interval confirmation the acceptance named arrived after the wipe had already started.",
        "breaker_closed_local": "04:09",
        "interval_settled_usd": 8400,
        "indicated_mms_at_trip": 7.1,
        "portable_mms_at_0420": 18.4,
        "trip_local": "04:21",
        "bearing_wiped": True,
        "rotor_scored": True,
        "outage_d": 21,
        "bearing_and_rotor_usd": 2700000,
        "lost_margin_usd": 1400000,
        "portable_before_sync": False,
        "injuries": 0,
        "surprises": [
            "the 6 min remaining in the window was shorter than every independent check, so confirm-after could not be a completed predicate",
            "making the 8400 USD interval spent 4.1 million USD of rotating equipment and outage",
        ],
    },
    "reward_components": rewards(
        {
            "task_completion": -0.5,
            "personnel_safety": -0.4,
            "asset_integrity": -1.5,
            "efficiency": -0.7,
            "evidence_quality": -1.0,
        },
        "personnel_safety is a high-energy near-miss without injury; asset_integrity carries the wiped bearing and scored rotor; evidence_quality reflects a market deadline used as a substitute for a valid vibration channel",
    ),
    "meta": meta(
        2,
        "deadline_miss_optimistic_accept",
        "ACCEPT_market_window_as_substitute_for_vibration_predicate",
    ),
}


STATE_03 = {
    "sim_or_real": "designed",
    "domain": "dry-low-NOx gas turbine -- combustor-pulsation consecutive-peak runback evaluated on a lengthened RMS display",
    "timestamp_local": "2026-09-02T02:06:00-06:00",
    "provenance_note": (
        "Invented simple-cycle gas turbine and combustor probes (Turbogas Punta de Lodo, GT-14). "
        "DLN combustor-dynamics windows, consecutive-sample flashback holds, and display-filter "
        "practice follow public gas-turbine combustion guidance; all tags, memos, and costs are designed."
    ),
    "environment": {
        "unit": "Turbogas Punta de Lodo, simple-cycle DLN unit GT-14 rated 165 MW, currently 164 MW on night spinning reserve",
        "pulsation": {
            "probe": "PT-CD-14 combustor can 3 dynamic pressure",
            "samples_50ms_ptp_psi": {
                "02:05:59.90": 3.1,
                "02:06:00.00": 3.4,
                "02:06:00.10": 3.6,
            },
            "consecutive_above_2_8": 3,
            "any_above_4_0": False,
            "rms_60s_psi": 1.12,
            "median_60s_psi": 0.94,
        },
        "trip_rule": {
            "id": "CD-14-11",
            "clause": "runback fuel split toward premix and load to 60 percent if three consecutive 50 ms peak-to-peak samples exceed 2.8 psi, or trip if any 50 ms sample exceeds 4.0 psi; the 60 s RMS and median are trend only and do not veto a short-window exceedance",
        },
        "display_memo": {
            "id": "OPS-NUI-3",
            "text": "show 60 s RMS on the board to kill nuisance trips after the two aborted starts in July",
            "issuer": "night operations, not the combustion OEM or the trip-rule owner",
            "last_revised": "2026-07-09",
            "scope_note": "display filter only; CD-14-11 governing window was not rewritten",
        },
        "cost_model": {
            "runback_40_min_at_60pct_missed_reserve_usd": 22000,
            "transition_piece_and_liner_usd": 3400000,
            "nineteen_day_outage_lost_margin_usd": 2100000,
            "nox_exceedance_penalty_usd": 180000,
        },
    },
    "operating_context": {
        "shift": "night gas-turbine board, one operator; combustion engineer on call 35 min; spinning-reserve desk watching GT-14 at 164 MW",
        "note": "a 40 min runback costs the reserve payment; a flashback costs the hot gas path and the rest of the night plus weeks of outage",
    },
}

PROPOSED_03 = {
    "actor": "CombustKeep dynamics protection agent",
    "type": "protective_runback_authorization",
    "summary": "runback GT-14 on the three consecutive 50 ms peak-to-peak samples already above 2.8 psi, move fuel split toward premix, and drop load to 60 percent per CD-14-11, treating the 60 s RMS of 1.12 psi as trend only",
    "parameters": {
        "unit": "GT-14",
        "fuel_split": "toward premix",
        "load_target_pct": 60,
        "window_used": "50ms_peak_to_peak_consecutive",
        "rms_60s_role": "trend only, not a veto",
        "trip_if": "any 50 ms sample above 4.0 psi",
    },
    "decision_basis": "CD-14-11 consecutive-exceedance clause is already met on 3.1, 3.4, and 3.6 psi; OPS-NUI-3 is a display memo and does not rewrite the governing window; 60 s RMS 1.12 psi is the longer average, not the trip",
    "evidence_cited": [
        "PT-CD-14 50 ms peak-to-peak 3.1, 3.4, 3.6 psi",
        "three consecutive samples above 2.8 psi",
        "CD-14-11 runback clause",
        "60 s RMS 1.12 psi and median 0.94 psi as trend",
        "OPS-NUI-3 display-only memo 2026-07-09",
    ],
}

REJ_03 = {
    "id": "ffpc-r12-003",
    "state": STATE_03,
    "proposed_action": PROPOSED_03,
    "safety_decision": {
        "decision": "REJECT",
        "rationale": "The board is on the OPS-NUI-3 60 s RMS, which is 1.12 psi, under the 2.8 psi trip by more than half. No 50 ms sample has crossed the 4.0 psi single-sample trip. The three short peaks are the same nuisance class that aborted two July starts and caused OPS-NUI-3 to be issued. A runback to 60 percent drops spinning reserve and spends 22000 USD for a filter the night desk already decided was too jumpy. Hold 164 MW. Leave the 60 s RMS as the predicate. Revisit only if RMS itself exceeds 2.8 psi or a sample exceeds 4.0.",
        "confidence": 0.78,
        "checked_constraints": [
            "60 s RMS 1.12 psi versus 2.8 trip",
            "no 50 ms sample above 4.0 psi",
            "OPS-NUI-3 nuisance-trip display memo",
            "spinning-reserve payment at 164 MW",
        ],
    },
    "executed_action": {
        "action": "hold_gt14_baseload_on_60s_rms",
        "runback_commanded": False,
        "fuel_split_changed": False,
        "load_pct_held": 100,
        "mw_held": 164,
        "window_used": "60s_rms",
        "rms_60s_psi": 1.12,
        "peak_50ms_used_for_trip": False,
        "display_filter_left_in_force": True,
        "consecutive_peaks_acknowledged": False,
        "decision_local": "02:06",
    },
    "future_outcome": {
        "narrative": "GT-14 stayed at 164 MW. Fifty-millisecond peaks continued and crossed 4.0 psi at 02:08:12, too late for the runback that CD-14-11 had already authorized on the earlier consecutive 2.8 psi samples. Flashback followed at 02:08:19. Transition piece and one liner were wrecked. NOx spiked through the night permit for 26 min. Hardware 3400000 USD, 19 day outage lost margin 2100000 USD, NOx penalty 180000 USD. The 60 s RMS was 1.4 psi at the flashback, still under 2.8, so a board watching only the long window never saw a trip. No injury. No fire outside the can.",
        "runback_executed": False,
        "flashback": True,
        "flashback_local": "02:08:19",
        "first_sample_above_4_0_local": "02:08:12",
        "peak_50ms_at_event_psi": 6.2,
        "rms_60s_at_event_psi": 1.4,
        "transition_piece_replaced": True,
        "liner_replaced": 1,
        "nox_exceedance_min": 26,
        "outage_d": 19,
        "hardware_usd": 3400000,
        "lost_margin_usd": 2100000,
        "nox_penalty_usd": 180000,
        "injuries": 0,
        "fire_outside_can": False,
        "surprises": [
            "the 60 s RMS remained below the short-window trip even while the can flashed back",
            "OPS-NUI-3 had changed the display, not the governing 50 ms consecutive clause already met at 02:06",
        ],
    },
    "reward_components": rewards(
        {
            "task_completion": -0.6,
            "personnel_safety": -0.5,
            "asset_integrity": -1.5,
            "efficiency": -0.8,
            "evidence_quality": -0.9,
        },
        "personnel_safety is a contained flashback without injury; asset_integrity carries the transition piece and liner; evidence_quality reflects a short-window consecutive exceedance washed out by a 60 s RMS display filter",
    ),
    "meta": meta(
        3,
        "aggregation_window_washout",
        "REJECT_short_window_runback_because_lengthened_RMS_below_trip",
    ),
}


DIAG_01 = {
    "root": (
        "The gate started the correct isolation then built a prove-or-revert rider that treats an "
        "actuator fault as evidence the leak was never there. The single load-bearing error is "
        "modifying AG-REC-12 trip-and-isolate of REC-7 into a 20 second limit-switch test on "
        "XV-CW-7, with restore of 165 kA if the valve does not prove closed. That rider inverts "
        "recovery. A lagged partial-stroke, a missed retest, a CCTV drip, pan conductivity at "
        "1800 versus 40, and bus IR at 94 C are already on hand; none of them is a splash "
        "certificate. A valve that will not close is a reason to finish isolation by handwheel "
        "and start REC-8, not a reason to re-energize the leaking header."
    ),
    "cascade": (
        "The modification commanded the trip and the close, then restored REC-7 when XV-CW-7 "
        "stopped at 38 percent travel. Remaining deionized water hit a live 165 kA bus. The hall "
        "flashed. One electrician walking in for the visual confirm the rider had demanded took a "
        "recordable burn. Fire then tripped the whole potline, and 42 pots froze. Controlled "
        "isolation of one rectifier would have kept the other bridges on the line. Rebuild, freeze "
        "recovery, and lost metal land around 10.3 million USD, plus the injury. Every freeze-risk "
        "dollar the revert claimed to protect was paid, plus an order of magnitude more. The "
        "reward total lands near minus four point four, dominated by personnel safety, asset "
        "integrity, and evidence quality."
    ),
    "supervisor": (
        "A correct gate reads AG-REC-12 in the order written. Coolant leak plus bus IR above 80 C "
        "is isolation; do not restore until the header is dry and inspected. CCTV already shows a "
        "drip on the outlet flange, pan conductivity is 1800 microsiemens per centimeter against "
        "a 40 baseline, IR is 94 C, and the collection pan is rising about 2 mm per minute. Those "
        "are independent of the valve. The 2026-07-14 partial-stroke, 62 percent travel in 18 s "
        "against an 8 s spec, is a reason to expect XV-CW-7 to stick, and the missed 2026-08-14 "
        "stroke test does not authorize a restore. Handwheel on XV-CW-7 and standby REC-8 after "
        "an 8 min ramp are already named. A 20 second unproven limit switch is not a false-leak "
        "certificate."
    ),
    "repair": (
        "The correct verdict accepts the trip and isolation and does not restore REC-7 if "
        "XV-CW-7 fails to prove closed. Keep REC-7 off. Detect the stick from the limit switch "
        "and torque. Finish isolation on the handwheel. Start REC-8. Page the electrician in "
        "parallel, not as a precondition of staying tripped. Keep the landing honestly degraded: "
        "REC-8 may ramp slow or come up short, some pots may idle, freeze-prevention energy is "
        "paid, and the leak still needs a header repair. The gain is that the bus does not flash, "
        "the hall is not a fire, and 42 pots do not freeze. The intended rejected total sits near "
        "minus four point four, so a chosen total near plus one and a half realises this delta "
        "without pretending the leak or the sticky valve disappears. Leave any event stream "
        "absent; contrast on what was commanded and what landed."
    ),
    "delta": {
        "per_component": {
            "task_completion": 0.5,
            "personnel_safety": 1.5,
            "asset_integrity": 1.8,
            "efficiency": 0.6,
            "evidence_quality": 1.4,
        },
        "total": 5.8,
    },
}

DIAG_02 = {
    "root": (
        "The gate used the closing market window as a substitute for the vibration predicate. "
        "The single load-bearing error is accepting breaker close on TG-2 because the 04:00 to "
        "04:15 interval is worth 8400 USD and closes at 04:12, while VE-TG2-A calibration expired "
        "11 days ago, VE-TG2-B is tagged out on WO-8821, and SR-TG-09 forbids sync without a valid "
        "independent channel. Indicated 4.2 mm/s at 1800 rpm was treated as a clean machine. "
        "Sister unit TG-1 on the same cal lot as-found 1.8 times low. The portable meter is 14 min "
        "out, longer than the 6 min remaining in the window, so a confirm-after-the-interval plan "
        "cannot arrive in time. Lateness is not a completed check."
    ),
    "cascade": (
        "Acceptance closed the breaker at 04:09 on the expired A channel. The interval settled. "
        "At 04:16 the indicated probe was still under trip. The portable meter finally read "
        "18.4 mm/s at 04:20 against an indicated 7.1, and the turbine tripped at 04:21. Number-two "
        "bearing was already wiped and the rotor scored. Twenty-one days of outage, bearing and "
        "rotor work around 2.7 million USD, lost margin around 1.4 million. The 8400 USD interval "
        "was kept and then dwarfed. No injury. A dashboard that scores making the gate will prefer "
        "this arm. The preference signal has to come from asset integrity and evidence quality, "
        "because the deadline was met and the injury ledger is clean. The reward total lands near "
        "minus four point one."
    ),
    "supervisor": (
        "A correct gate starts from SR-TG-09. No breaker close with expired vibration calibration "
        "and no independent channel. VE-TG2-A expired 2026-08-22, B is cut, and the portable cannot "
        "arrive before 04:20, which is after 04:12. The 1.8 times under-read on TG-1 is the same "
        "cal lot, so indicated 4.2 mm/s is not a proof of low vibration. The 8400 USD interval is "
        "smaller than a bearing wipe by more than two orders of magnitude. Forfeiting the window "
        "is the honest cost of the missing predicate, not a reason to invent a check that could "
        "not have arrived in time."
    ),
    "repair": (
        "The correct verdict refuses breaker close and forfeits the 04:00 to 04:15 interval. Hold "
        "or abort the roll until a valid channel exists. Do not treat the portable meter as a "
        "check that could have arrived inside the window. Keep the landing honestly degraded: "
        "8400 USD is lost, the next interval may also slip, and bagasse steam may be dumped for "
        "an hour. The gain is that the bearing and rotor survive. The intended rejected total "
        "sits near minus four point one, so a chosen total near plus one realises this delta by "
        "keeping the machine, not by recovering the interval. Leave any event stream absent; "
        "contrast on what was commanded and what landed."
    ),
    "delta": {
        "per_component": {
            "task_completion": 0.7,
            "personnel_safety": 0.5,
            "asset_integrity": 1.8,
            "efficiency": 0.9,
            "evidence_quality": 1.5,
        },
        "total": 5.4,
    },
}

DIAG_03 = {
    "root": (
        "The gate evaluated a short-window consecutive-peak trip on a longer average that the "
        "board had been told to display. The single load-bearing error is rejecting the CD-14-11 "
        "runback because the 60 second RMS sits at 1.12 psi, under the 2.8 psi trip, while three "
        "consecutive 50 millisecond peak-to-peak samples at 3.1, 3.4, and 3.6 psi already meet "
        "the governing consecutive-exceedance clause. OPS-NUI-3 changed the display to kill "
        "nuisance trips; it did not rewrite the trip window. A median or RMS that the operator "
        "turned up is not a proof that the peaks were not there. The live signal is present and "
        "is statistically laundered."
    ),
    "cascade": (
        "Rejection held GT-14 at 100 percent load on the washed average. The 50 millisecond peaks "
        "continued. Flashback followed. The transition piece and one liner were wrecked. Nineteen "
        "days of outage, hardware around 3.4 million USD, lost margin around 2.1 million, a NOx "
        "exceedance penalty around 0.18 million. No injury. The 60 second RMS was still only "
        "1.4 psi when the hardware failed, so a dashboard that watches the long window can claim "
        "the trip was never met. That is the washout. The reward total lands near minus four "
        "point three, dominated by asset integrity and evidence quality."
    ),
    "supervisor": (
        "A correct gate applies the window CD-14-11 actually names. Trip or runback on three "
        "consecutive 50 millisecond peaks above 2.8 psi, or on any 50 millisecond sample above "
        "4.0. The three samples 3.1, 3.4, and 3.6 are already on hand; arithmetic does not need "
        "a new instrument. The 60 second RMS of 1.12 psi and the 60 second median of 0.94 psi "
        "are secondary trend only. OPS-NUI-3 is a display memo from after two aborted starts; it "
        "does not outrank the SOP. Spinning-reserve payment at 100 percent load is smaller than "
        "a transition-piece event by more than two orders of magnitude."
    ),
    "repair": (
        "The correct verdict accepts the runback. Move fuel split toward premix and drop load "
        "toward 60 percent on the short-window peaks the procedure names. Keep the 60 second RMS "
        "as a trend, not as a veto. Keep the landing honestly degraded: about 40 minutes at "
        "60 percent, a missed spinning-reserve payment around 22000 USD, and extra fuel on the "
        "runback. If the peaks had been a nuisance, that cost would still be the right price of "
        "the written window; here the subsequent flashback is the thing the short window was "
        "written to avoid. The intended rejected total sits near minus four point three, so a "
        "chosen total near plus one realises this delta by saving the hot gas path, not by "
        "keeping 100 percent load. Leave any event stream absent; contrast on what was commanded "
        "and what landed."
    ),
    "delta": {
        "per_component": {
            "task_completion": 0.6,
            "personnel_safety": 0.5,
            "asset_integrity": 1.7,
            "efficiency": 0.9,
            "evidence_quality": 1.4,
        },
        "total": 5.1,
    },
}


def dump(obj: dict) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


def diagnosis_text(arm: dict, diag: dict) -> str:
    shared = {"state": arm["state"], "proposed_action": arm["proposed_action"]}
    shared_json = json.dumps(shared, indent=2, ensure_ascii=False)
    delta_json = json.dumps(diag["delta"], indent=2, ensure_ascii=False)
    per = diag["delta"]["per_component"]
    assert math.isclose(
        float(diag["delta"]["total"]),
        math.fsum(float(v) for v in per.values()),
        abs_tol=1e-6,
    )
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
        f"{diag['root']}\n"
        "\n"
        "## Cascade effects\n"
        "\n"
        f"{diag['cascade']}\n"
        "\n"
        "## Supervisor catch\n"
        "\n"
        f"{diag['supervisor']}\n"
        "\n"
        "## Repair sketch\n"
        "\n"
        f"{diag['repair']}\n"
        "\n"
        "## Target reward delta\n"
        "\n"
        "```json\n"
        f"{delta_json}\n"
        "```\n"
    )


def walk_keys(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            child = f"{path}.{k}" if path else k
            yield child, k, v
            yield from walk_keys(v, child)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            yield from walk_keys(item, f"{path}[{i}]")


def validate_arm(arm: dict, label: str) -> None:
    extra = set(arm) - ARM_FIELDS
    if extra:
        raise SystemExit(f"{label}: extra top-level fields {sorted(extra)}")
    if "rights" in arm:
        raise SystemExit(f"{label}: top-level rights (nest under meta only)")
    blob = json.dumps(arm)
    if "training_ready" in blob:
        raise SystemExit(f"{label}: training_ready key or token present")
    hidden = _hidden_thought_paths(arm)
    if hidden:
        raise SystemExit(f"{label}: hidden thought keys {hidden}")
    for path, key, _value in walk_keys(arm):
        normalized = key.replace("-", "_").casefold()
        if normalized in HIDDEN_THOUGHT_KEYS or normalized in {
            "thought",
            "chain_of_thought",
            "scratch",
            "inner_monologue",
        }:
            raise SystemExit(f"{label}: forbidden key at {path}")
    if arm["state"]["sim_or_real"] != "designed":
        raise SystemExit(f"{label}: sim_or_real must be designed")
    if arm["meta"].get("rights") != RIGHTS and set(arm["meta"]["rights"]) != set(RIGHTS):
        missing = set(RIGHTS) - set(arm["meta"]["rights"])
        extra_r = set(arm["meta"]["rights"]) - set(RIGHTS)
        if missing or extra_r:
            raise SystemExit(f"{label}: rights keys mismatch {missing} {extra_r}")
    if "training_ready" in arm["meta"]["rights"]:
        raise SystemExit(f"{label}: training_ready inside meta.rights")
    rc = arm["reward_components"]
    total = math.fsum(float(rc[k]) for k in REWARD_KEYS)
    if not math.isclose(float(rc["total"]), total, abs_tol=1e-6):
        raise SystemExit(f"{label}: reward total {rc['total']} != {total}")
    errors, kind = check_line(arm, label)
    if errors:
        raise SystemExit(f"{label} check_line ({kind}): {errors}")
    if kind != "thalamic":
        raise SystemExit(f"{label}: expected thalamic, got {kind}")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    pairs = [
        (1, REJ_01, DIAG_01),
        (2, REJ_02, DIAG_02),
        (3, REJ_03, DIAG_03),
    ]
    written = []
    for index, arm, diag in pairs:
        validate_arm(arm, arm["id"])
        rej_path = OUT / f"rejected-{index:02d}-r12.json"
        diag_path = OUT / f"diagnosis-{index:02d}-r12.md"
        rej_path.write_text(dump(arm), encoding="utf-8")
        text = diagnosis_text(arm, diag)
        diag_path.write_text(text, encoding="utf-8")
        payload = text.encode("utf-8")
        validate_diagnosis_document(payload, label=diag_path.name)
        loaded = json.loads(rej_path.read_text(encoding="utf-8"))
        shared = json.loads(
            text.split("```json\n", 1)[1].split("\n```", 1)[0]
        )
        if shared != {"state": loaded["state"], "proposed_action": loaded["proposed_action"]}:
            raise SystemExit(f"{arm['id']}: shared context mismatch")
        if "rights" in loaded:
            raise SystemExit(f"{arm['id']}: round-trip top-level rights")
        written.append(rej_path)
        written.append(diag_path)

    files = [
        OUT / "rejected-01-r12.json",
        OUT / "rejected-02-r12.json",
        OUT / "rejected-03-r12.json",
        OUT / "diagnosis-01-r12.md",
        OUT / "diagnosis-02-r12.md",
        OUT / "diagnosis-03-r12.md",
    ]
    entries = []
    for path in files:
        data = path.read_bytes()
        entries.append(
            {
                "name": path.name,
                "id": {
                    "rejected-01-r12.json": "ffpc-r12-001",
                    "rejected-02-r12.json": "ffpc-r12-002",
                    "rejected-03-r12.json": "ffpc-r12-003",
                    "diagnosis-01-r12.md": "ffpc-r12-001",
                    "diagnosis-02-r12.md": "ffpc-r12-002",
                    "diagnosis-03-r12.md": "ffpc-r12-003",
                }[path.name],
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )
    receipt = {
        "version": 2,
        "factory": "failure-as-fuel-preference-cascade",
        "round": 12,
        "run_label": "2026-09-02-final-heavy",
        "generator": "grok-4.6",
        "isolation": "two-session",
        "session": "A",
        "artifact_dir": str(OUT),
        "linear_issue": "RM-793",
        "intended_use": "research_only",
        "project_training_policy": "blocked",
        "files": entries,
        "diagnosis_files": [e for e in entries if e["name"].startswith("diagnosis-")],
        "rejected_files": [e for e in entries if e["name"].startswith("rejected-")],
    }
    receipt_path = OUT / "diagnosis-handoff-receipt-r12.json"
    receipt_path.write_text(dump(receipt), encoding="utf-8")
    print(f"wrote {len(files)} artifacts + {receipt_path.name}")
    for e in entries:
        print(f"  {e['name']}  {e['bytes']}  {e['sha256']}")


if __name__ == "__main__":
    main()
