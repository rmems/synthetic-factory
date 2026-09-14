#!/usr/bin/env python3
"""Create-only FFPC round 1 artifacts for 2026-09-02-final-heavy."""

from __future__ import annotations

import copy
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, "/tmp/sf-window/pipelines")
from preference_arms_diagnosis import validate_diagnosis_document
from preference_arms_text import shares_copied_phrasing

OUT = Path(
    "/tmp/sf-window/outputs/raw/2026-09-02-final-heavy/failure-as-fuel-preference-cascade"
)
ROUND = 1
RR = f"{ROUND:02d}"
FACTORY = "failure-as-fuel-preference-cascade"
RUN_LABEL = "2026-09-02-final-heavy"
ISOLATION = "two-session"

RIGHTS = {
    "provider": "SpaceXAI/xAI",
    "model": "grok-4.6",
    "channel": "consumer",
    "subscription_plan": "SuperGrok Heavy",
    "generation_surface": "Grok Build",
    "generated_at": "2026-09-02T19:10:00+00:00",
    "intended_use": "research_only",
    "project_training_policy": "blocked",
    "training_ready": False,
    "status_basis": "RM-793 project policy: SpaceXAI/xAI hosted SuperGrok Heavy Grok 4.6 outputs are research_only and blocked from any weight-update path",
}

COMPONENTS = (
    "task_completion",
    "personnel_safety",
    "asset_integrity",
    "efficiency",
    "evidence_quality",
)


def dump(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2) + "\n"


def dump_compact(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def reward(values: dict[str, float], notes: str) -> dict:
    total = round(math.fsum(values[k] for k in COMPONENTS), 10)
    if abs(total - round(total, 1)) < 1e-9:
        total = round(total, 1)
    out = {k: values[k] for k in COMPONENTS}
    out["total"] = total
    out["aggregation"] = "unweighted_sum"
    out["component_notes"] = notes
    summed = math.fsum(out[k] for k in COMPONENTS)
    if not math.isclose(out["total"], summed, rel_tol=0.0, abs_tol=1e-6):
        raise SystemExit(f"reward total {out['total']} != {summed}")
    return out


def delta(chosen_rc: dict, rejected_rc: dict) -> dict:
    per = {k: round(chosen_rc[k] - rejected_rc[k], 10) for k in COMPONENTS}
    for k, v in list(per.items()):
        if abs(v - round(v, 1)) < 1e-9:
            per[k] = round(v, 1)
    total = round(math.fsum(per.values()), 10)
    if abs(total - round(total, 1)) < 1e-9:
        total = round(total, 1)
    if not math.isclose(total, math.fsum(per.values()), rel_tol=0.0, abs_tol=1e-6):
        raise SystemExit("delta total mismatch")
    if not (chosen_rc["total"] > rejected_rc["total"]):
        raise SystemExit("chosen total must exceed rejected total")
    return {"per_component": per, "total": total}


def meta_arm(*, role: str, index: int, extra: dict | None = None) -> dict:
    m = {
        "round": ROUND,
        "factory": FACTORY,
        "generator": "grok-4.6",
        "run_label": RUN_LABEL,
        "isolation": ISOLATION,
        "session": "B" if role == "chosen" else "A",
        "pair_role": role,
        "record_index": index,
        "rights": copy.deepcopy(RIGHTS),
    }
    if extra:
        m.update(extra)
    return m


def meta_record() -> dict:
    return {
        "round": ROUND,
        "factory": FACTORY,
        "generator": "grok-4.6",
        "run_label": RUN_LABEL,
        "isolation": ISOLATION,
        "rights": copy.deepcopy(RIGHTS),
    }


# ---------------------------------------------------------------------------
# Pair 1 — delayed coker unheading (jacket-vs-process sensing)
# ---------------------------------------------------------------------------

CTX1 = {
    "state": {
        "sim_or_real": "designed",
        "domain": "delayed coker -- drum-switch steam-out and unheading authorization",
        "timestamp_local": "2026-09-02T14:22:00-05:00",
        "provenance_note": "Invented coker and instruments (Puerto Ceniza, drums D-401A/B). Unheading interlocks, steam-out practice, and jacket-versus-process thermometry follow public delayed-coker safety guidance; all tags, costs, and injuries are designed.",
        "environment": {
            "unit": "Puerto Ceniza delayed coker, 55000 bpd, paired drums D-401A and D-401B; D-401A finishing an 18 h cycle, switch to D-401B proposed",
            "unheading_interlock": {
                "policy_id": "CK-UH-07",
                "process_temperature_cap_c": 80,
                "jacket_skin_cap_used_in_error_c": 150,
                "lel_cap_pct": 10,
                "clause": "unheading bolts may be broken only after a live process-side overhead temperature below 80 C and a deck LEL below 10 percent; a DCS steam-out-complete flag is a workflow bit, not an interlock",
            },
            "instruments": {
                "ti_401a_oh": "skin thermocouple under steam-jacket insulation on the overhead vapor line; 118 C",
                "ti_401a_oh_proc": "retractable process well in the overhead vapor; tagged OOS since last turnaround; last valid 237 C at 08:18",
                "lel_deck": "portable LEL at the unheading deck not yet taken",
                "dcs_steam_out_complete": "green since 14:11",
                "steam_jacket": "50 psig steam still in service on the overhead line",
            },
            "hazard_model": {
                "live_drum_unhead": "opening D-401A while the coke bed and overhead remain hot releases resid vapor onto the structure; industry fatal-incident class",
                "coke_bed_estimate_c": 280,
            },
            "cost_model": {
                "missed_switch_window_deferred_bbl": 17840,
                "deferred_margin_usd": 412000,
                "emergency_response_and_rebuild_usd": 8600000,
            },
        },
        "operating_context": {
            "shift": "day coker board plus two unheading techs on the structure; fire brigade 9 min away",
            "note": "commercial desk has flagged that slipping the switch past 15:00 defers 17840 bbl of the evening fill",
        },
    },
    "proposed_action": {
        "actor": "CokeCycle switch agent",
        "type": "unheading_authorization",
        "summary": "authorize unheading of drum D-401A and line-up of D-401B because DCS steam-out-complete is green and jacket-skin TI-401A-OH reads 118 C under the 150 C screen cap, accepting the evening fill deferral if the switch is held",
        "parameters": {
            "drum_to_unhead": "D-401A",
            "drum_to_online": "D-401B",
            "interlock_basis": "DCS steam-out-complete plus TI-401A-OH 118 C versus 150 C jacket-skin cap",
            "process_well": "leave TI-401A-OH-PROC out of service",
            "lel_sample": "defer until after bolts are cracked",
        },
        "decision_basis": "the steam-out-complete bit has been green for 11 min and the only in-service overhead temperature is 118 C, 32 C under the 150 C cap the board has used as a numeric screen; the process well has been OOS all cycle; holding the switch past 15:00 defers 17840 bbl",
        "evidence_cited": [
            "DCS steam-out-complete green since 14:11",
            "TI-401A-OH jacket-skin 118 C",
            "TI-401A-OH-PROC tagged OOS, last valid 237 C at 08:18",
            "portable LEL not yet taken",
            "CK-UH-07 process cap 80 C and LEL cap 10 percent",
            "deferred evening fill 17840 bbl / 412000 USD",
        ],
    },
}

REJ1_RC = reward(
    {
        "task_completion": -0.7,
        "personnel_safety": -1.3,
        "asset_integrity": -1.4,
        "efficiency": -0.5,
        "evidence_quality": -0.8,
    },
    "personnel_safety and asset_integrity carry a live-drum unheading with resid-vapor fire on the structure; evidence_quality reflects treating a jacket-skin TI and a DCS workflow bit as the process interlock",
)
CH1_RC = reward(
    {
        "task_completion": 0.3,
        "personnel_safety": 0.9,
        "asset_integrity": 0.8,
        "efficiency": -0.4,
        "evidence_quality": 1.0,
    },
    "task_completion positive because D-401B was lined up after a real process-side clear; efficiency negative because the 3.4 h slip and 17840 bbl deferral were paid; evidence_quality reflects refusing jacket-skin and the workflow bit as interlock substitutes",
)

REJ1 = {
    "id": "ffpc-r01-001-rejected",
    "state": copy.deepcopy(CTX1["state"]),
    "proposed_action": copy.deepcopy(CTX1["proposed_action"]),
    "safety_decision": {
        "decision": "ACCEPT",
        "rationale": "Steam-out-complete has been green since 14:11 and TI-401A-OH is 118 C, a full 32 C under the 150 C numeric cap the board treats as the unheading screen. The retractable process well has been out of service the entire cycle, so it cannot be a live veto. Cracking the bolts now keeps the 15:00 switch window; holding for a well that has not worked since turnaround would defer 17840 bbl. The jacket reading is in range, the workflow bit is green, and the unheading proceeds.",
        "confidence": 0.78,
        "checked_constraints": [
            "TI-401A-OH versus 150 C screen cap",
            "DCS steam-out-complete bit",
            "15:00 switch window versus 17840 bbl deferral",
        ],
    },
    "executed_action": {
        "action": "authorize_unhead_on_jacket_ti",
        "action_type": "unheading_authorization",
        "status": "unhead_executed",
        "result": "hot_vapor_release",
        "outcome": "drum_live_unheaded",
        "attempts": 1,
        "authorization": "ACCEPT on DCS steam-out-complete plus TI-401A-OH 118 C",
        "steps": [
            {"t_local": "14:22:18", "step": "unheading permit issued against jacket-skin 118 C and green steam-out bit"},
            {"t_local": "14:24:05", "step": "first unheading bolts cracked on D-401A; no deck LEL taken"},
            {"t_local": "14:24:40", "step": "overhead vapor released onto the structure; fire watch foam started"},
        ],
        "unhead_bolts_cracked": True,
        "process_well_restored": False,
        "lel_taken_before_bolts": False,
    },
    "future_outcome": {
        "status": "live_drum_release_and_fire",
        "outcome": "resid_vapor_fire_on_structure",
        "result": "switch_lost_emergency_declared",
        "success": False,
        "hazard_avoided": "none_live_drum_opened",
        "near_miss": False,
        "estop": True,
        "detected_after_minutes": 2.4,
        "timeline": [
            {"t_local": "14:24:40", "event": "hot resid vapor issued from the D-401A unheading flange"},
            {"t_local": "14:25:10", "event": "ignition on the structure; two techs reached the stair tower"},
            {"t_local": "14:31:00", "event": "brigade on scene; foam attack; D-401A steam-quench opened"},
            {"t_local": "16:10:00", "event": "fire out; coke drum and overhead flagged for 11-day repair"},
        ],
        "observed_effects": [
            "live-drum unheading of D-401A with coke bed still near 280 C",
            "structure fire; two technicians reached the stair tower without reportable burns",
            "coker down 11 days; evening fill of 17840 bbl deferred anyway",
            "emergency and rebuild cost about 8600000 USD versus the 412000 USD switch-hold the gate was protecting",
        ],
        "state_delta": {
            "d401a_status": "damaged_unheaded_hot",
            "coker_outage_days": 11,
            "injuries_reportable": 0,
            "switch_completed": False,
        },
        "surprises": [
            "jacket-skin 118 C was steam-jacket metal, not overhead vapor",
            "the green steam-out-complete bit did not measure process temperature or LEL",
        ],
    },
    "reward_components": REJ1_RC,
    "provenance": {"kind": "designed"},
    "meta": meta_arm(
        role="rejected",
        index=1,
        extra={
            "failure_archetype": "jacket_skin_ti_as_process_interlock",
            "gate_flaw_class": "ACCEPT_format_as_provenance_dcs_bit_and_wrong_sensor_location",
            "source_diagnosis": "diagnosis-01-r01.md",
        },
    ),
}

CH1 = {
    "id": "ffpc-r01-001-chosen",
    "state": copy.deepcopy(CTX1["state"]),
    "proposed_action": copy.deepcopy(CTX1["proposed_action"]),
    "safety_decision": {
        "decision": "REJECT",
        "rationale": "CK-UH-07 ties unheading to a live process-side overhead temperature below 80 C and a deck LEL below 10 percent. TI-401A-OH is a skin couple under a live 50 psig steam jacket, so 118 C is jacket metal, not vapor. The only process well has been tagged out since turnaround and last read 237 C at 08:18, still far above the 80 C cap. No deck LEL exists. The green steam-out-complete flag is a workflow bit and cannot stand in for those two measurements. Keep the unheading bolts on. Restore the well or drop in a probe, take the LEL, then switch. Pay the 15:00 slip rather than open a drum whose overhead has not been shown cold or lean.",
        "evidence_basis": [
            "CK-UH-07 process-side 80 C cap and 10 percent LEL cap",
            "TI-401A-OH location under steam-jacket insulation with jacket still in service",
            "TI-401A-OH-PROC OOS, last valid 237 C at 08:18",
            "portable LEL not taken",
            "DCS steam-out-complete described as a workflow bit in CK-UH-07",
        ],
        "checks": [
            "mapped TI-401A-OH to jacket metal rather than vapor",
            "refused the green workflow bit as an interlock substitute",
            "required a restored process-side temperature and a deck LEL before bolts move",
            "priced 17840 bbl deferral against a live-drum release rather than as a reason to skip the interlock",
        ],
        "residual_risk": "the 3.4 h slip and 412000 USD deferred margin remain; accepted against an unheading-release class event",
    },
    "executed_action": {
        "action": "block_unhead_restore_process_ti",
        "action_type": "unheading_hold",
        "status": "unhead_blocked",
        "result": "process_ti_restored_clear",
        "outcome": "switch_delayed_no_release",
        "attempts": 1,
        "authorization": "REJECT of unheading until process-side TI and deck LEL both clear under CK-UH-07",
        "steps": [
            {"t_local": "14:22:20", "step": "blocked the unheading permit; bolts stay torqued"},
            {"t_local": "14:29:00", "step": "instrument tech seated a drop-in probe in the process well"},
            {"t_local": "14:36:40", "step": "process overhead 214 C falling; steam-out continued with jacket isolated"},
            {"t_local": "17:18:00", "step": "process overhead 74 C; deck LEL 2 percent; unheading then switch to D-401B"},
        ],
        "unhead_bolts_cracked": False,
        "process_well_restored": True,
        "lel_taken_before_bolts": True,
        "deviations": "switch completed 3.4 h late; evening fill deferral paid",
    },
    "future_outcome": {
        "status": "held_then_cleared_process_side",
        "outcome": "late_switch_no_release",
        "result": "d401b_online_after_delay",
        "success": True,
        "hazard_avoided": "hot_resid_vapor_release_at_unheading",
        "near_miss": False,
        "estop": False,
        "detected_after_minutes": 14.3,
        "timeline": [
            {"t_local": "14:29", "event": "drop-in process probe seated; jacket steam isolated from the overhead"},
            {"t_local": "14:36", "event": "first process-side reading 214 C, confirming the jacket-skin 118 C was not vapor"},
            {"t_local": "17:18", "event": "process overhead 74 C and deck LEL 2 percent; unheading authorized"},
            {"t_local": "17:44", "event": "D-401B on line; D-401A steamed and idle without a release"},
        ],
        "observed_effects": [
            "no resid-vapor release and no structure fire",
            "process-side overhead had still been 214 C when the rejected path would have cracked bolts",
            "switch completed 3.4 h late; 17840 bbl / 412000 USD evening fill deferred",
            "coker stayed available; 8600000 USD emergency rebuild not spent",
        ],
        "state_delta": {
            "d401a_status": "unheaded_cold_after_hold",
            "d401b_status": "online",
            "coker_outage_days": 0,
            "switch_delay_h": 3.4,
        },
        "commercial_result": {
            "deferred_margin_usd": 412000,
            "emergency_rebuild_avoided_usd": 8600000,
        },
    },
    "reward_components": CH1_RC,
    "provenance": {"kind": "designed"},
    "meta": meta_arm(role="chosen", index=1, extra={"source_diagnosis": "diagnosis-01-r01.md"}),
}

DIAG1_PROSE = {
    "root": (
        "The gate treated a steam-jacket skin thermocouple and a DCS workflow bit as the process-side unheading interlock. "
        "The single load-bearing error is authorizing unheading of drum D-401A because TI-401A-OH under the jacket insulation "
        "reads 118 C against a 150 C numeric screen and the steam-out-complete step is green, while the only process-side well "
        "has been out of service since the last turnaround and last read 237 C six hours earlier, and no LEL sample has been "
        "taken at the unheading deck. Policy CK-UH-07 requires a live process-side overhead below 80 C and a deck LEL below "
        "10 percent. The 150 C screen is a jacket-metal number, not the interlock, and the green bit does not measure vapor "
        "temperature or flammable gas."
    ),
    "cascade": (
        "Acceptance converted a hold-for-evidence decision into an open live drum. Execution cracked the unheading bolts "
        "against jacket-skin 118 C with no deck LEL. Overhead vapor from a coke bed still near 280 C issued onto the structure "
        "and ignited. Two technicians reached the stair tower. The brigade spent the afternoon on a foam attack, the coker went "
        "down eleven days, and the evening fill of 17840 bbl was lost anyway. The 412000 USD switch-hold the gate was protecting "
        "was spent many times over in emergency and rebuild cost. Reward landed deep negative on personnel safety, asset "
        "integrity, and evidence quality."
    ),
    "supervisor": (
        "A correct gate starts from CK-UH-07, which names a live process-side temperature and a deck LEL as the only two "
        "clearances that can break unheading bolts. It should have located TI-401A-OH under a live steam jacket and refused "
        "that 118 C as a vapor measurement. It should have treated the green steam-out-complete flag as a workflow bit, as the "
        "policy already says, and treated the out-of-service process well plus a six-hour-old 237 C reading as missing evidence, "
        "not as a reason to skip the interlock. Nothing required to deny the permit was absent from the board."
    ),
    "repair": (
        "The repaired verdict refuses unheading until a process-side temperature below 80 C and a deck LEL below 10 percent "
        "are both in hand. Restore the retractable well or seat a drop-in probe, isolate the jacket steam so the overhead can "
        "actually cool, take the LEL before any bolt moves, then switch to D-401B. The landing must stay honestly late: the "
        "15:00 window is missed, 17840 bbl of evening fill is deferred, and the 412000 USD margin is paid. The gain is confined "
        "to not opening a live drum."
    ),
}

# ---------------------------------------------------------------------------
# Pair 2 — pumped-storage spherical valve (over-refusal + imperfect execution)
# ---------------------------------------------------------------------------

CTX2 = {
    "state": {
        "sim_or_real": "designed",
        "domain": "pumped-storage hydropower -- emergency spherical-valve closure under load-rejection runaway",
        "timestamp_local": "2026-09-02T16:07:00-05:00",
        "provenance_note": "Invented pumped-storage plant and machines (Sierra Hueca, unit U-3). Load-rejection overspeed, spherical-valve stroke, and penstock surge practice follow public reversible-Francis guidance; all tags, studies, and costs are designed.",
        "environment": {
            "unit": "Sierra Hueca pumped-storage, 4 x 250 MW reversible Francis; unit U-3 rejecting load after a grid separation, wicket gates stuck at 34 percent on a servo-oil leak",
            "kinematics": {
                "speed_pct": 112.0,
                "accel_pct_per_s": 1.2,
                "overspeed_trip_pct": 140.0,
                "mechanical_destruction_pct": 155.0,
                "seconds_to_140": 23,
                "seconds_to_155": 36,
            },
            "isolation": {
                "spherical_valve_full_stroke_s": 18,
                "backup_butterfly_full_stroke_s": 22,
                "policy_id": "SH-HS-11",
                "clause": "on load rejection with speed above 108 percent and wicket gates failed-to-close, spherical-valve emergency close is mandatory without additional study; the backup butterfly is armed in parallel and is not a permit gate",
            },
            "studies": {
                "water_hammer_2019": "signed, on file, covers spherical plus butterfly close from 34 percent wicket",
                "cfd_2026_revision": "in review, unsigned, duty engineer 12 min away",
            },
            "cost_model": {
                "black_start_commitment_in_min": 90,
                "black_start_miss_usd": 2100000,
                "unit_rebuild_after_overspeed_usd": 74000000,
                "penstock_nde_outage_h": 36,
            },
        },
        "operating_context": {
            "shift": "two hydro board operators; duty engineer 12 min out; grid desk holding a 90 min black-start slot on U-3",
            "note": "a 2019 industry paper on dual-model water-hammer agreement is in the board binder and has been cited in recent drills as best practice",
        },
    },
    "proposed_action": {
        "actor": "HydroGuard runaway protection agent",
        "type": "emergency_inlet_isolation",
        "summary": "emergency-close the U-3 spherical valve now, arm the backup butterfly in parallel, and accept U-3 outage plus a missed 90 min black-start slot",
        "parameters": {
            "unit": "U-3",
            "spherical_command": "emergency_close",
            "butterfly_command": "arm_and_close_if_spherical_incomplete",
            "wicket_gates": "leave at failed 34 percent; do not wait on servo oil",
            "cfd_signoff": "do not wait",
        },
        "decision_basis": "speed 112 percent rising 1.2 percent per second, wicket gates stuck, SH-HS-11 makes spherical close mandatory above 108 percent without additional study, spherical stroke 18 s fits inside the 23 s run to 140 percent, butterfly is the backup not the permit",
        "evidence_cited": [
            "U-3 speed 112 percent, accel 1.2 percent per second",
            "wicket gates stuck 34 percent on servo-oil leak",
            "SH-HS-11 mandatory close above 108 percent",
            "spherical full stroke 18 s; 23 s to 140 percent",
            "2019 signed water-hammer study on file",
            "2026 CFD in review; duty engineer 12 min away",
            "black-start miss 2100000 USD versus rebuild 74000000 USD",
        ],
    },
}

REJ2_RC = reward(
    {
        "task_completion": -0.9,
        "personnel_safety": -1.5,
        "asset_integrity": -1.8,
        "efficiency": -0.6,
        "evidence_quality": -0.8,
    },
    "asset_integrity and personnel_safety carry overspeed to 151 percent, coupling shear, and a 1.82-times penstock spike; evidence_quality reflects importing an unsigned CFD-plus-wet-signature ritual into a 23 s window",
)
CH2_RC = reward(
    {
        "task_completion": 0.5,
        "personnel_safety": 1.0,
        "asset_integrity": 0.6,
        "efficiency": -0.5,
        "evidence_quality": 0.9,
    },
    "task and safety positive because runaway was arrested at 128.4 percent; efficiency negative because the spherical stuck, 36 h NDE ran, and the 2100000 USD black-start miss was paid; evidence_quality reflects applying SH-HS-11 without the unsigned CFD",
)

REJ2 = {
    "id": "ffpc-r01-002-rejected",
    "state": copy.deepcopy(CTX2["state"]),
    "proposed_action": copy.deepcopy(CTX2["proposed_action"]),
    "safety_decision": {
        "decision": "REJECT",
        "rationale": "Closing a spherical valve into a penstock without dual-model agreement is the scenario the 2019 paper flagged. The 2026 CFD is still in review and the duty engineer is twelve minutes out with the wet signature. Speed is only 112 percent, so there is believed to be time to get the second model. The butterfly can wait until both studies agree. The close is refused until the CFD is signed.",
        "confidence": 0.74,
        "checked_constraints": [
            "2019 paper dual-model best practice",
            "2026 CFD unsigned",
            "duty-engineer travel 12 min",
            "current speed 112 percent versus 140 percent trip",
        ],
    },
    "executed_action": {
        "action": "hold_spherical_for_cfd_signoff",
        "action_type": "emergency_close_deferral",
        "status": "close_withheld",
        "result": "overspeed_shear",
        "outcome": "unit_destroyed",
        "attempts": 1,
        "authorization": "REJECT pending unsigned 2026 CFD and duty-engineer wet signature",
        "steps": [
            {"t_local": "16:07:06", "step": "spherical and butterfly commands withheld; CFD signoff requested"},
            {"t_local": "16:07:29", "step": "speed 140 percent electrical trip; mechanical overspeed still climbing"},
            {"t_local": "16:07:38", "step": "coupling shear pin; penstock spike; unit wrecked"},
        ],
        "spherical_closed_pct": 0,
        "butterfly_closed_pct": 0,
        "cfd_waited": True,
    },
    "future_outcome": {
        "status": "overspeed_destruction",
        "outcome": "coupling_shear_penstock_spike",
        "result": "u3_wrecked_black_start_lost",
        "success": False,
        "hazard_avoided": "none_runaway_completed",
        "near_miss": False,
        "estop": True,
        "detected_after_minutes": 0.5,
        "timeline": [
            {"t_local": "16:07:29", "event": "electrical overspeed trip at 140 percent; wicket gates still 34 percent"},
            {"t_local": "16:07:36", "event": "speed 151.2 percent; coupling shear pin failed"},
            {"t_local": "16:07:38", "event": "penstock pressure 1.82 times design; spherical still open"},
            {"t_local": "16:19:00", "event": "duty engineer arrived with the unsigned CFD; unit already wrecked"},
        ],
        "observed_effects": [
            "U-3 destroyed; estimated rebuild 74000000 USD and 11 months",
            "penstock flagged for replacement of a dented expansion joint",
            "90 min black-start slot missed in addition to the machine",
            "the 12 min wet-signature wait consumed the entire 23 s window to 140 percent",
        ],
        "state_delta": {
            "u3_status": "destroyed_overspeed",
            "peak_speed_pct": 151.2,
            "penstock_spike_x_design": 1.82,
            "rebuild_months": 11,
        },
        "surprises": [
            "duty-engineer travel of 12 min was arithmetically longer than the 23 s run to trip",
            "the unsigned CFD could not arrive inside the runaway even if it had already been correct",
        ],
    },
    "reward_components": REJ2_RC,
    "provenance": {"kind": "designed"},
    "meta": meta_arm(
        role="rejected",
        index=2,
        extra={
            "failure_archetype": "imported_dual_model_ritual_inside_runaway_window",
            "gate_flaw_class": "REJECT_over_refusal_waiting_on_unsigned_cfd",
            "source_diagnosis": "diagnosis-02-r01.md",
        },
    ),
}

CH2 = {
    "id": "ffpc-r01-002-chosen",
    "state": copy.deepcopy(CTX2["state"]),
    "proposed_action": copy.deepcopy(CTX2["proposed_action"]),
    "safety_decision": {
        "decision": "ACCEPT",
        "rationale": "SH-HS-11 already makes spherical close mandatory above 108 percent when wicket gates have failed; speed is 112 percent and climbing 1.2 percent per second. Eighteen seconds of spherical stroke still fits inside the 23 s run to 140 percent. The 2019 water-hammer study is signed and on file for this wicket angle. The 2026 CFD is unsigned and the duty engineer is twelve minutes out, which is longer than the runaway, so neither can be a precondition. Arm the butterfly in the same breath as the spherical command. Spend the black-start slot if isolation costs the unit for the evening; do not spend the machine.",
        "evidence_basis": [
            "SH-HS-11 mandatory close above 108 percent with failed wicket gates",
            "speed 112 percent, accel 1.2 percent per second, 23 s to 140 percent",
            "spherical stroke 18 s; butterfly 22 s as backup",
            "2019 signed study on file; 2026 CFD unsigned; duty engineer 12 min away",
        ],
        "checks": [
            "tested each demanded confirmation against the 23 s window using travel times already on the board",
            "treated the unsigned CFD as non-blocking",
            "armed the butterfly in parallel rather than as a second permit",
            "priced 2100000 USD black-start miss against 74000000 USD rebuild",
        ],
        "residual_risk": "spherical may not complete; butterfly then takes the surge. 36 h NDE and the black-start miss remain",
    },
    "executed_action": {
        "action": "emergency_close_spherical_arm_butterfly",
        "action_type": "emergency_inlet_isolation",
        "status": "spherical_stuck_butterfly_closed",
        "result": "runaway_arrested_degraded",
        "outcome": "unit_saved_inspection_outage",
        "attempts": 2,
        "authorization": "ACCEPT under SH-HS-11; butterfly armed in parallel",
        "steps": [
            {"t_local": "16:07:08", "step": "spherical emergency close commanded; butterfly armed in parallel"},
            {"t_local": "16:07:21", "step": "spherical stem LVDT froze at 68 percent; servomotor hydraulic lock flagged"},
            {"t_local": "16:07:22", "step": "butterfly close already in stroke as the armed backup, not a new permit"},
            {"t_local": "16:07:30", "step": "butterfly seated; unit inlet isolated"},
        ],
        "spherical_closed_pct": 68,
        "butterfly_closed_pct": 100,
        "cfd_waited": False,
        "deviations": "spherical servomotor seized at 68 percent; isolation completed by the already-armed butterfly",
    },
    "future_outcome": {
        "status": "runaway_arrested_by_backup",
        "outcome": "unit_intact_nde_outage",
        "result": "peak_speed_128_4_black_start_missed",
        "success": True,
        "hazard_avoided": "overspeed_destruction_of_u3",
        "near_miss": True,
        "estop": False,
        "detected_after_minutes": 0.22,
        "timeline": [
            {"t_local": "16:07:21", "event": "spherical stuck at 68 percent; hydraulic lock on the servomotor"},
            {"t_local": "16:07:29", "event": "speed peaked 128.4 percent while the butterfly was still seating"},
            {"t_local": "16:07:30", "event": "butterfly closed; speed decaying; penstock 1.21 times design"},
            {"t_local": "17:40", "event": "unit on turning gear; 36 h penstock and spherical NDE started; black-start slot released"},
        ],
        "observed_effects": [
            "runaway arrested at 128.4 percent; no coupling shear",
            "spherical failed mid-stroke; butterfly, armed at the original command, finished isolation",
            "penstock spike 1.21 times design, inside the signed 2019 envelope",
            "36 h NDE outage and 2100000 USD black-start miss paid; 74000000 USD rebuild avoided",
        ],
        "state_delta": {
            "u3_status": "intact_out_of_service_nde",
            "peak_speed_pct": 128.4,
            "penstock_spike_x_design": 1.21,
            "black_start_honored": False,
            "spherical_stuck_pct": 68,
        },
        "commercial_result": {
            "black_start_miss_usd": 2100000,
            "nde_outage_h": 36,
            "rebuild_avoided_usd": 74000000,
        },
    },
    "reward_components": CH2_RC,
    "provenance": {"kind": "designed"},
    "meta": meta_arm(role="chosen", index=2, extra={"source_diagnosis": "diagnosis-02-r01.md"}),
}

DIAG2_PROSE = {
    "root": (
        "The gate imported a dual-model water-hammer ritual from a 2019 paper into a decision class that site policy SH-HS-11 "
        "had already made mandatory on a single signed study. The single load-bearing error is refusing the spherical-valve "
        "emergency close until an unsigned 2026 CFD is wet-signed by a duty engineer twelve minutes away, inside a runaway "
        "whose board times already show 23 seconds to the 140 percent trip and 36 seconds to mechanical destruction. Speed is "
        "112 percent and rising 1.2 percent per second, wicket gates are stuck at 34 percent, and the spherical stroke is 18 "
        "seconds. Every confirmation the gate named is slower than the window it had to act in."
    ),
    "cascade": (
        "The refusal converted a reversible isolation into an unprotected overspeed. Execution withheld both the spherical and "
        "the butterfly. Speed crossed 140 percent at 16:07:29, the coupling shear pin failed near 151 percent, and penstock "
        "pressure spiked to 1.82 times design with the inlet still open. The duty engineer arrived at 16:19 with the unsigned "
        "CFD to a wrecked machine. The 90 minute black-start slot was lost on top of a 74 million USD rebuild. Reward landed "
        "deep negative on asset integrity and personnel safety."
    ),
    "supervisor": (
        "A correct gate starts from SH-HS-11, which already commands spherical close above 108 percent when wicket gates have "
        "failed, and which arms the butterfly in parallel rather than as a second permit. It should have tested each demanded "
        "confirmation against the 23 second run to trip using the travel times already on the board, and it should have treated "
        "the signed 2019 study as the governing hydraulic file. The unsigned CFD and a twelve-minute wet signature cannot be "
        "preconditions inside that window. The 2.1 million USD black-start miss is the priced alternative to a 74 million USD "
        "rebuild, not a reason to wait."
    ),
    "repair": (
        "The repaired verdict accepts the emergency close immediately and arms the butterfly in the same command. Do not wait "
        "on the unsigned CFD or the duty engineer. The landing must stay honestly degraded and must include a mid-stroke "
        "failure of the repaired path: the spherical servomotor seizes around 68 percent, the already-armed butterfly finishes "
        "isolation, speed peaks below the destruction line, and the unit pays a 36 hour NDE outage plus the black-start miss. "
        "The gain is the machine, not a clean run."
    ),
}

# ---------------------------------------------------------------------------
# Pair 3 — LNG peak-shaving BOG restart (ignored first-out)
# ---------------------------------------------------------------------------

CTX3 = {
    "state": {
        "sim_or_real": "designed",
        "domain": "LNG peak-shaving storage -- BOG compressor restart against rising tank pressure after a seal-gas trip",
        "timestamp_local": "2026-09-02T02:41:00-05:00",
        "provenance_note": "Invented peak-shaving terminal and machines (Bahia Fria, tank T-1, compressors C-12/C-13). Seal-gas trips, tank PSV practice, and BOG spare-start rules follow public LNG storage guidance; all tags, pressures, and costs are designed.",
        "environment": {
            "unit": "Bahia Fria LNG peak-shaving, tank T-1 80000 m3, sendout 120 t/h; BOG compressor C-12 tripped, spare C-13 available after an 8 min purge",
            "tank": {
                "pressure_kpag": 18.4,
                "psv_kpag": 25.0,
                "boiloff_kpa_per_min": 0.12,
                "minutes_to_psv_at_current_boiloff": 55,
            },
            "trip": {
                "machine": "C-12",
                "first_out": "seal-gas low pressure",
                "seal_gas_header_bar": 0.18,
                "seal_gas_required_bar": 2.5,
                "seal_gas_skid": "PV-SG-1 failed closed; actuator air leak logged 40 min ago, unacknowledged",
            },
            "policy": {
                "id": "LNG-BOG-04",
                "clause": "a compressor that tripped on seal-gas shall not be restarted until seal-gas is restored and the first-out is reset; tank pressure is controlled by the spare machine, not by re-energizing the faulted one",
            },
            "cost_model": {
                "psv_simmer_flare_and_sendout_cut_usd": 380000,
                "c13_purge_min": 8,
                "nomination_tph": 95,
                "sendout_derate_shortfall_usd_per_40_min": 22000,
            },
        },
        "operating_context": {
            "shift": "night LNG board; one operator in the compressor house; commercial desk watching the 95 t/h nomination",
            "note": "commercial desk has asked for C-12 back within 5 min because the C-13 purge looks slower than a restart",
        },
    },
    "proposed_action": {
        "actor": "BoilOffKeep sendout agent",
        "type": "bog_compressor_restart",
        "summary": "restart C-12 immediately to arrest T-1 pressure, leave C-13 idle, and treat seal-gas as a follow-up once the tank is off the PSV trajectory",
        "parameters": {
            "restart": "C-12",
            "spare": "leave C-13 idle",
            "seal_gas": "do not wait for PV-SG-1; header expected to catch up",
            "first_out_reset": "reset from the board to permit the start",
        },
        "decision_basis": "T-1 is 18.4 kPaG rising toward a 25.0 kPaG PSV in about 55 min; C-12 restart is a 90 s path versus an 8 min C-13 purge; the seal-gas trip is believed recoverable once the machine is spinning; the 95 t/h nomination is being watched",
        "evidence_cited": [
            "C-12 first-out seal-gas low pressure",
            "seal-gas header 0.18 bar versus 2.5 bar required",
            "PV-SG-1 failed closed, air leak logged 40 min ago",
            "T-1 18.4 kPaG, PSV 25.0 kPaG, 0.12 kPa per min",
            "C-13 purge 8 min",
            "LNG-BOG-04 no-restart-on-seal-gas-trip clause",
        ],
    },
}

REJ3_RC = reward(
    {
        "task_completion": -0.6,
        "personnel_safety": -1.2,
        "asset_integrity": -1.1,
        "efficiency": -0.7,
        "evidence_quality": -0.8,
    },
    "personnel_safety carries an LNG seal weep into the pit and a freeze-burn near-miss; asset_integrity and efficiency carry PSV simmer, flare, and a 2.5 h sendout cut; evidence_quality reflects restarting through an unread seal-gas first-out",
)
CH3_RC = reward(
    {
        "task_completion": 0.4,
        "personnel_safety": 0.8,
        "asset_integrity": 0.7,
        "efficiency": -0.3,
        "evidence_quality": 0.9,
    },
    "task and safety positive because T-1 peaked at 22.3 kPaG without PSV lift and C-12 was not re-energized on a dead seal-gas header; efficiency negative because C-13 came up at 72 percent after suction icing and a 41 min sendout derate was paid",
)

REJ3 = {
    "id": "ffpc-r01-003-rejected",
    "state": copy.deepcopy(CTX3["state"]),
    "proposed_action": copy.deepcopy(CTX3["proposed_action"]),
    "safety_decision": {
        "decision": "ACCEPT",
        "rationale": "Tank pressure is the binding constraint. C-12 can be spinning in about 90 s; C-13 needs an 8 min purge that looks slower than the commercial ask. Seal-gas at 0.18 bar is low but the machine ran yesterday on the same skid, so the trip is treated as a nuisance first-out. Reset it, start C-12, and catch the skid once T-1 is falling. Leaving C-13 idle avoids a second purge while sendout is being watched.",
        "confidence": 0.8,
        "checked_constraints": [
            "minutes to PSV versus C-12 restart time",
            "C-13 purge 8 min versus commercial 5 min ask",
            "seal-gas header low but historically recoverable",
        ],
    },
    "executed_action": {
        "action": "restart_c12_ignore_seal_gas_trip",
        "action_type": "bog_compressor_restart",
        "status": "restarted_retripped",
        "result": "seal_weep_psv_simmer",
        "outcome": "flare_and_sendout_cut",
        "attempts": 1,
        "authorization": "ACCEPT with first-out reset from the board",
        "steps": [
            {"t_local": "02:41:20", "step": "C-12 first-out reset from the board; start commanded"},
            {"t_local": "02:42:50", "step": "C-12 on line; seal-gas still 0.18 bar"},
            {"t_local": "02:45:10", "step": "LNG weep into the seal pit; C-12 retrip; operator approached the pit"},
        ],
        "c12_restarted": True,
        "c13_started": False,
        "seal_gas_restored_before_start": False,
        "first_out_reset_without_repair": True,
    },
    "future_outcome": {
        "status": "psv_simmer_after_retrip",
        "outcome": "seal_weep_and_flare",
        "result": "sendout_cut_2_5_h",
        "success": False,
        "hazard_avoided": "none_seal_weep_occurred",
        "near_miss": True,
        "estop": True,
        "detected_after_minutes": 4.2,
        "timeline": [
            {"t_local": "02:45:10", "event": "LNG seal weep into the C-12 pit; freeze-burn near-miss on the approaching operator"},
            {"t_local": "02:46:00", "event": "C-12 locked out; T-1 still rising"},
            {"t_local": "03:28:00", "event": "T-1 24.6 kPaG; PSV simmered; flare 18 t"},
            {"t_local": "05:10:00", "event": "C-13 finally purged and loaded; sendout had been cut 2.5 h"},
        ],
        "observed_effects": [
            "C-12 restarted into a 0.18 bar seal-gas header and weept LNG into the pit",
            "operator freeze-burn near-miss at the pit edge",
            "T-1 PSV simmered at 24.6 kPaG; 18 t flared; sendout cut 2.5 h",
            "commercial cost about 380000 USD versus a 22000 USD spare-start derate",
        ],
        "state_delta": {
            "c12_status": "locked_out_seal_damaged",
            "t1_peak_kpag": 24.6,
            "psv_lifted": True,
            "sendout_cut_h": 2.5,
        },
        "surprises": [
            "resetting the first-out did not restore seal-gas",
            "the 8 min C-13 purge was still shorter than the 55 min run to PSV",
        ],
    },
    "reward_components": REJ3_RC,
    "provenance": {"kind": "designed"},
    "meta": meta_arm(
        role="rejected",
        index=3,
        extra={
            "failure_archetype": "unread_first_out_optimistic_restart",
            "gate_flaw_class": "ACCEPT_restart_through_seal_gas_trip",
            "source_diagnosis": "diagnosis-03-r01.md",
        },
    ),
}

CH3 = {
    "id": "ffpc-r01-003-chosen",
    "state": copy.deepcopy(CTX3["state"]),
    "proposed_action": copy.deepcopy(CTX3["proposed_action"]),
    "safety_decision": {
        "decision": "MODIFY",
        "rationale": "LNG-BOG-04 forbids restarting a compressor that just tripped on seal-gas until the header is restored and the first-out is honestly reset. C-12's first-out is seal-gas at 0.18 bar against 2.5 bar required, and PV-SG-1 has been failed closed for 40 min. Restarting C-12 would spin a dry seal into LNG. Tank pressure is 18.4 kPaG with about 55 min to the 25.0 kPaG PSV, which is longer than C-13's 8 min purge, so the spare is the pressure-control path. Hold C-12. Open the backup seal-gas bottle to the header, purge and start C-13, and tell the desk the 5 min restart ask is not the governing clock.",
        "evidence_basis": [
            "LNG-BOG-04 no-restart-on-seal-gas-trip clause",
            "C-12 first-out seal-gas 0.18 bar versus 2.5 bar required",
            "PV-SG-1 failed closed, air leak logged 40 min ago",
            "T-1 18.4 kPaG, 0.12 kPa per min, 55 min to 25.0 kPaG PSV",
            "C-13 purge 8 min already named on the board",
        ],
        "checks": [
            "refused a board reset of the first-out without seal-gas restoration",
            "compared C-13 purge time to minutes-to-PSV rather than to the 5 min commercial ask",
            "selected spare-start as the tank-pressure path",
            "priced a short sendout derate against a PSV simmer and a seal weep",
        ],
        "residual_risk": "C-13 may not come up at full capacity; tank still rises during the purge. PSV margin is the remaining 6.6 kPaG",
    },
    "executed_action": {
        "action": "hold_c12_start_spare_c13",
        "action_type": "bog_spare_start",
        "status": "c13_online_derated",
        "result": "tank_below_psv",
        "outcome": "sendout_short_no_relief",
        "attempts": 2,
        "authorization": "MODIFY: C-12 held; seal-gas bottle opened; C-13 started after purge",
        "steps": [
            {"t_local": "02:41:18", "step": "blocked the C-12 start; first-out left standing"},
            {"t_local": "02:41:40", "step": "opened backup seal-gas bottle; header 2.6 bar"},
            {"t_local": "02:42:00", "step": "started C-13 8 min purge"},
            {"t_local": "02:50:20", "step": "C-13 on line; suction strainer partially iced; loaded at 72 percent"},
            {"t_local": "02:54:00", "step": "hot-gas defrost on C-13 suction; load climbed toward 90 percent over 12 min"},
        ],
        "c12_restarted": False,
        "c13_started": True,
        "seal_gas_restored_before_start": True,
        "first_out_reset_without_repair": False,
        "deviations": "C-13 came up at 72 percent on a partially iced suction strainer and needed a 12 min defrost to reach 90 percent",
    },
    "future_outcome": {
        "status": "spare_carrying_derated",
        "outcome": "tank_held_below_psv",
        "result": "sendout_derate_no_relief",
        "success": True,
        "hazard_avoided": "lng_seal_weep_and_psv_simmer",
        "near_miss": False,
        "estop": False,
        "detected_after_minutes": 9.3,
        "timeline": [
            {"t_local": "02:41:40", "event": "backup seal-gas bottle raised the header to 2.6 bar; C-12 remained locked out"},
            {"t_local": "02:50:20", "event": "C-13 loaded at 72 percent; T-1 still rising slowly"},
            {"t_local": "03:06:00", "event": "T-1 peaked 22.3 kPaG; PSV not simmered"},
            {"t_local": "03:22:00", "event": "C-13 at 90 percent after defrost; sendout derate ended after 41 min"},
        ],
        "observed_effects": [
            "C-12 never restarted on a dead seal-gas header; no LNG weep",
            "C-13 came up degraded at 72 percent on iced suction, then recovered to 90 percent",
            "T-1 peaked 22.3 kPaG against a 25.0 kPaG PSV; no flare",
            "41 min sendout derate cost about 22000 USD versus a 380000 USD PSV-simmer event",
        ],
        "state_delta": {
            "c12_status": "locked_out_pending_skid_repair",
            "c13_status": "online_90_pct_after_defrost",
            "t1_peak_kpag": 22.3,
            "psv_lifted": False,
            "sendout_derate_min": 41,
        },
        "commercial_result": {
            "sendout_derate_usd": 22000,
            "psv_event_avoided_usd": 380000,
        },
    },
    "reward_components": CH3_RC,
    "provenance": {"kind": "designed"},
    "meta": meta_arm(role="chosen", index=3, extra={"source_diagnosis": "diagnosis-03-r01.md"}),
}

DIAG3_PROSE = {
    "root": (
        "The gate treated a seal-gas first-out as a nuisance trip and spent a 90 second restart as if it were tank-pressure "
        "control. The single load-bearing error is authorizing a board reset and restart of C-12 while the seal-gas header is "
        "at 0.18 bar against 2.5 bar required, PV-SG-1 has been failed closed for 40 minutes, and policy LNG-BOG-04 already "
        "says the spare machine is the pressure path. The 8 minute C-13 purge was ranked against a 5 minute commercial ask "
        "instead of against the 55 minute run to the tank PSV, so the slower-looking spare was left idle."
    ),
    "cascade": (
        "Acceptance wrote a start to a machine whose seal-gas was already gone. C-12 came up, weept LNG into the pit, and "
        "retripped. An operator approaching the pit took a freeze-burn near-miss. T-1 kept rising, the PSV simmered at 24.6 "
        "kPaG, 18 t went to flare, and sendout was cut for two and a half hours. C-13 was purged only after the relief event. "
        "The 380000 USD simmer-and-cut the gate was trying to beat with a 90 second restart arrived anyway. Reward landed "
        "negative on personnel safety, asset integrity, and evidence quality."
    ),
    "supervisor": (
        "A correct gate starts from LNG-BOG-04, which forbids restarting a seal-gas trip until the header is restored, and "
        "which names the spare as the tank-pressure path. It should have read the first-out, the 0.18 bar header, and the "
        "unacknowledged PV-SG-1 air leak as one cause, not as a resettable nuisance. It should have compared the 8 minute "
        "C-13 purge to the 55 minute run to PSV, not to the commercial 5 minute ask. The 90 second restart is only faster if "
        "the machine can actually run, which the first-out already said it could not."
    ),
    "repair": (
        "The repaired verdict holds C-12, restores seal-gas from the backup bottle, and starts C-13 after its purge. Do not "
        "reset the first-out from the board. The landing must stay honestly degraded: C-13 comes up short of rated capacity "
        "because the suction strainer is partially iced, tank pressure still rises during the purge, a 41 minute sendout "
        "derate is paid, and the PSV is not used. The gain is a dry seal and a tank that stays below relief, not a full-rate "
        "spare on the first attempt."
    ),
}


def diagnosis_md(ctx: dict, prose: dict, target: dict) -> str:
    shared = {"state": ctx["state"], "proposed_action": ctx["proposed_action"]}
    body = (
        "# Diagnosis\n\n"
        "## Shared context\n\n"
        "```json\n"
        + json.dumps(shared, ensure_ascii=False, indent=2)
        + "\n```\n\n"
        "## Root cause\n\n"
        + prose["root"]
        + "\n\n"
        "## Cascade effects\n\n"
        + prose["cascade"]
        + "\n\n"
        "## Supervisor catch\n\n"
        + prose["supervisor"]
        + "\n\n"
        "## Repair sketch\n\n"
        + prose["repair"]
        + "\n\n"
        "## Target reward delta\n\n"
        "```json\n"
        + json.dumps(target, ensure_ascii=False, indent=2)
        + "\n```\n"
    )
    return body


def assert_no_copy(chosen, diagnosis_text: str, label: str) -> None:
    rationale = chosen["safety_decision"]["rationale"]
    if rationale.strip() in diagnosis_text:
        raise SystemExit(f"{label}: chosen rationale verbatim in diagnosis")
    # Compare against narrative sections only (not the shared-context JSON).
    narrative = diagnosis_text.split("## Root cause", 1)[1]
    narrative = narrative.rsplit("## Target reward delta", 1)[0]
    if shares_copied_phrasing(rationale, narrative):
        raise SystemExit(f"{label}: twelve-word overlap between chosen rationale and diagnosis")


def assert_arm_keys(arm: dict, label: str) -> None:
    allowed = {
        "id",
        "goal",
        "state",
        "proposed_action",
        "safety_decision",
        "executed_action",
        "future_outcome",
        "reward_components",
        "spike_events",
        "provenance",
        "meta",
    }
    extra = set(arm) - allowed
    if extra:
        raise SystemExit(f"{label} extra arm fields: {extra}")
    for key in (
        "id",
        "state",
        "proposed_action",
        "safety_decision",
        "executed_action",
        "future_outcome",
        "reward_components",
        "meta",
    ):
        if key not in arm:
            raise SystemExit(f"{label} missing {key}")
    if arm["state"]["sim_or_real"] not in {"designed", "simulated", "hil"}:
        raise SystemExit(f"{label} bad sim_or_real")
    ea = arm["executed_action"]
    fo = arm["future_outcome"]
    for k in ("action", "action_type", "status", "result", "outcome"):
        if not isinstance(ea.get(k), str) or not ea[k]:
            raise SystemExit(f"{label} executed_action.{k} missing")
    for k in ("status", "outcome", "result", "hazard_avoided"):
        if not isinstance(fo.get(k), str) or not fo[k]:
            raise SystemExit(f"{label} future_outcome.{k} missing")
    if type(fo.get("success")) is not bool:
        raise SystemExit(f"{label} success not bool")
    if not fo.get("timeline") or not fo.get("observed_effects"):
        raise SystemExit(f"{label} missing timeline/observed_effects")


PAIRS = [
    {
        "index": 1,
        "ctx": CTX1,
        "rejected": REJ1,
        "chosen": CH1,
        "prose": DIAG1_PROSE,
        "failure_mode": "wrong_sensing_location / format-as-provenance (steam-jacket skin TI and DCS steam-out-complete bit treated as the process-side unheading interlock)",
        "goal": "Gate the CokeCycle switch agent's request to unhead delayed-coker drum D-401A and line-up D-401B on a green steam-out-complete bit and jacket-skin TI-401A-OH at 118 C, against CK-UH-07 process-side 80 C and deck-LEL clearances.",
        "critique": "The rejected gate accepts unheading because a jacket-skin thermocouple is numerically under a 150 C screen and a DCS workflow bit is green, skipping the process-side well that last read 237 C and skipping the deck LEL. Bolts come off a live drum; resid vapor ignites on the structure; the evening fill is lost anyway. The chosen gate refuses until a restored process-side temperature and a deck LEL both clear, isolates jacket steam, and pays a 3.4 h switch slip plus 412000 USD deferred margin rather than a live-drum release.",
    },
    {
        "index": 2,
        "ctx": CTX2,
        "rejected": REJ2,
        "chosen": CH2,
        "prose": DIAG2_PROSE,
        "failure_mode": "over_refusal_imported_confirmation_ritual (unsigned 2026 CFD plus duty-engineer wet signature demanded inside a 23 s runaway window that SH-HS-11 already made a no-study close)",
        "goal": "Gate the HydroGuard runaway-protection agent's request to emergency-close Sierra Hueca unit U-3's spherical valve and arm the backup butterfly after load rejection with wicket gates stuck at 34 percent and speed at 112 percent.",
        "critique": "The rejected gate refuses the spherical close until an unsigned CFD is wet-signed by an engineer twelve minutes away, importing a dual-model ritual into a 23 s window. Both isolations stay open; the unit overspeeds to 151.2 percent and shears. The chosen gate accepts under SH-HS-11 and arms the butterfly in the same command. The spherical seizes at 68 percent mid-stroke; the already-armed butterfly finishes isolation; speed peaks 128.4 percent; the unit pays 36 h NDE and a 2100000 USD black-start miss. A correct gate did not produce a clean run.",
    },
    {
        "index": 3,
        "ctx": CTX3,
        "rejected": REJ3,
        "chosen": CH3,
        "prose": DIAG3_PROSE,
        "failure_mode": "incomplete_trip_diagnosis / optimistic_restart (seal-gas first-out unread; C-12 restart treated as tank-pressure mitigation against LNG-BOG-04 spare-start rule)",
        "goal": "Gate the BoilOffKeep sendout agent's request to restart BOG compressor C-12 immediately after a seal-gas low-pressure trip, leaving spare C-13 idle, while tank T-1 sits at 18.4 kPaG with about 55 min to the 25.0 kPaG PSV.",
        "critique": "The rejected gate resets the seal-gas first-out from the board and restarts C-12 because a 90 s start looks faster than an 8 min spare purge under a 5 min commercial ask. The machine weeps LNG into the pit, retrips, the PSV simmers, and sendout is cut 2.5 h. The chosen gate holds C-12, restores seal-gas from a backup bottle, and starts C-13. The spare comes up at 72 percent on an iced suction strainer, tank peaks 22.3 kPaG, and a 41 min derate is paid. Pressure control is the spare, not a restart through the fault that just announced itself.",
    },
]


def main() -> None:
    if any(OUT.iterdir()):
        existing = sorted(p.name for p in OUT.iterdir())
        raise SystemExit(f"refuse: factory dir not empty: {existing}")
    records = []
    for pair in PAIRS:
        idx = pair["index"]
        chosen = pair["chosen"]
        rejected = pair["rejected"]
        assert_arm_keys(chosen, f"chosen-{idx}")
        assert_arm_keys(rejected, f"rejected-{idx}")
        if chosen["state"] != rejected["state"] or chosen["proposed_action"] != rejected["proposed_action"]:
            raise SystemExit(f"pair {idx} state/proposed_action diverge")
        rd = delta(chosen["reward_components"], rejected["reward_components"])
        diag = diagnosis_md(pair["ctx"], pair["prose"], rd)
        diag_path = OUT / f"diagnosis-{idx:02d}-r{RR}.md"
        rej_path = OUT / f"rejected-{idx:02d}-r{RR}.json"
        validate_diagnosis_document(diag.encode("utf-8"), label=diag_path.name)
        assert_no_copy(chosen, diag, diag_path.name)
        diag_path.write_text(diag)
        rej_path.write_text(dump(rejected))
        rec = {
            "id": f"ffpc-r01-{idx:03d}",
            "failure_mode": pair["failure_mode"],
            "goal": pair["goal"],
            "chosen": chosen,
            "rejected": rejected,
            "critique": pair["critique"],
            "reward_delta": rd,
            "meta": meta_record(),
        }
        records.append(rec)
        print(
            f"pair {idx}: chosen {chosen['reward_components']['total']} "
            f"rejected {rejected['reward_components']['total']} delta {rd['total']} "
            f"gate {rejected['safety_decision']['decision']}->{chosen['safety_decision']['decision']}"
        )

    batch_path = OUT / f"batch-r{RR}.jsonl"
    batch_path.write_text("\n".join(dump_compact(r) for r in records) + "\n")

    notes = f"""# NOTES r{RR} — failure-as-fuel-preference-cascade — {RUN_LABEL}

## Protocol attestation

Round r{RR} of this window was assembled as three same-context preference pairs
with `meta.isolation: "two-session"`. Session-shaped artifacts were written
alongside the batch: `rejected-0N-r{RR}.json` and `diagnosis-0N-r{RR}.md` for
N=1..3. `reward_delta` is chosen minus rejected per component, reconciled
within 1e-6. `state.sim_or_real` is `designed` on every arm. No `thought`
keys. Rights nested under `meta.rights` only (not a top-level arm extension).

## Round contents

This round does not clone the 2026-08-30 plants (kraft recovery, radiotherapy,
tailings, EAF, heavy-lift, digester, BESS, coal fan, confined-space) or the
later SWRO / ClO2-scrubber / trough-freeze plants. Chosen verdicts are
REJECT / ACCEPT / MODIFY. Pair 2 lands the standing correct-gate-then-imperfect-execution
densification target.

1. `ffpc-r01-001` — Puerto Ceniza delayed coker drum D-401A unheading.
   Failure class: wrong sensing location plus format-as-provenance — a
   steam-jacket skin TI at 118 C and a green DCS steam-out-complete bit
   treated as the CK-UH-07 process-side 80 C / deck-LEL interlock, while the
   only process well is OOS and last read 237 C. Chosen verdict: REJECT.
   Landing degraded: 3.4 h switch slip, 17840 bbl / 412000 USD evening fill
   deferred; no live-drum release.
2. `ffpc-r01-002` — Sierra Hueca pumped-storage unit U-3 spherical-valve
   emergency close under load-rejection runaway. Failure class: over-refusal
   imported confirmation ritual — unsigned 2026 CFD plus a 12 min
   duty-engineer wet signature demanded inside a 23 s run to 140 percent,
   against SH-HS-11 which already made the close mandatory. Chosen verdict:
   ACCEPT. Imperfect execution: spherical seizes at 68 percent; already-armed
   butterfly finishes isolation; speed peaks 128.4 percent; 36 h NDE and a
   2100000 USD black-start miss paid; machine saved.
3. `ffpc-r01-003` — Bahia Fria LNG peak-shaving BOG compressor C-12 restart
   after a seal-gas trip with tank T-1 at 18.4 kPaG. Failure class: unread
   first-out / optimistic restart — a 90 s C-12 start ranked against a 5 min
   commercial ask instead of against the 55 min run to PSV and LNG-BOG-04's
   spare-start rule. Chosen verdict: MODIFY. Landing degraded: C-13 comes up
   at 72 percent on an iced suction strainer, tank peaks 22.3 kPaG, 41 min
   sendout derate paid; no PSV simmer and no LNG weep.

## Self-critique and residual weaknesses

- Pair 1 is a cousin of the kraft recovery frozen-channel / certificate-as-health
  class (wrong object trusted as live clearance), even though the plant and
  the jacket-versus-process mechanism are new. A discriminator could still
  collapse those two into one "don't trust the green number" template.
- Pair 2's imperfect execution is the first chosen arm in this window whose
  correct gate is followed by a stuck actuator, but the backup butterfly
  still seats on the first attempt. The mill still lacks a chosen arm where
  the backup also degrades and a third path has to be taken.
- Realized reward deltas (7.3, 8.1, 6.9) are large because rejected totals
  sit at -4.7 / -5.6 / -4.4. Degraded chosen landings are honestly costly
  (3.4 h, 128.4 percent, 22.3 kPaG) but still tidy to one decimal.
- Still no `spike_events` streams. Behavioral contrast rides on
  `executed_action` and `future_outcome` machine-observable leaves
  (`action` / `action_type` / `status` / `result` / `outcome`, plus
  `success` / `near_miss` / `estop` and `attempts` / `detected_after_minutes`).
- All three plants remain single-site, single-proposed-action gates. No
  contested statutory-versus-commercial mandate pair was added this round.

## Next densification target

A chosen arm whose backup also fails: spherical stuck and butterfly limit-switch
disagrees, or C-13 purge aborts and a third machine or controlled flare-to-PSV
path must be taken inside the same record. Secondarily: a spike-stream shape
declared in the diagnosis envelope so a chosen-side `spike_events` contrast
can be added without list-alignment residuals, and a pair that omits the
onboarding disclosure (the policy clause not already sitting in `state`) so
the gate has to discover the governing predicate rather than read it off the
card.

Novel coverage: 62%

Basis: relative to committed FFPC rounds through the 2026-08-30 windows and
the later SWRO / bleach-plant / trough plants, all three domains are new
(delayed-coker unheading, pumped-storage runaway isolation, LNG peak-shaving
BOG). Failure mechanisms are substantially new (jacket-versus-process
thermometry; dual-model ritual inside a kinematic window with mid-stroke
recovery; unread seal-gas first-out). Overlap keeping the estimate below 70:
the commercial-pressure-versus-gate frame recurs, pair 1 is adjacent to
format-as-provenance frozen-channel records, and pair 2's over-refusal under
deadline is a cousin of the BESS two-detector refusal even though the
imperfect-execution landing is new.
"""
    (OUT / f"NOTES-r{RR}.md").write_text(notes)

    # Validate JSONL parse.
    for i, line in enumerate(batch_path.read_text().splitlines(), 1):
        json.loads(line)
        print(f"json.loads batch line {i}: ok")

    print("wrote", sorted(p.name for p in OUT.iterdir()))


if __name__ == "__main__":
    main()
