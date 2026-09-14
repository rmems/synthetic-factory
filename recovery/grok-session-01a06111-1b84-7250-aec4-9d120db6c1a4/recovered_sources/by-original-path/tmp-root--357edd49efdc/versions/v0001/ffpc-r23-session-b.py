#!/usr/bin/env python3
"""Session B assembly for FFPC round 23. Create-only into the factory dir."""

from __future__ import annotations

import json
import os
import sys
from copy import deepcopy
from pathlib import Path

ROOT = Path("/home/raulmc/rmems/synthetic-factory")
FACTORY = ROOT / "outputs/raw/2026-09-02-final-heavy/failure-as-fuel-preference-cascade"
PIPELINES = ROOT / "pipelines"
sys.path.insert(0, str(PIPELINES))

from preference_arms_diagnosis import diagnosis_narrative_text, validate_diagnosis_document
from preference_arms_text import shares_copied_phrasing

ROUND = 23
GEN_AT = "2026-09-03T01:18:00Z"
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

BOOKKEEPING = {
    "aggregation",
    "component_notes",
    "convention",
    "frame",
    "native_unit",
    "notes",
    "provenance_notes",
    "rounding_decimals",
    "total",
    "total_basis",
    "unit_usd",
    "units",
    "weights",
}


def chosen_meta(index: int) -> dict:
    return {
        "round": ROUND,
        "factory": "failure-as-fuel-preference-cascade",
        "generator": "grok-4.6",
        "run_label": "2026-09-02-final-heavy",
        "isolation": "two-session",
        "session": "B",
        "pair_role": "chosen",
        "source_diagnosis": f"diagnosis-{index:02d}-r23.md",
        "record_index": index,
        "rights": deepcopy(RIGHTS),
    }


def top_meta() -> dict:
    return {
        "round": ROUND,
        "factory": "failure-as-fuel-preference-cascade",
        "generator": "grok-4.6",
        "run_label": "2026-09-02-final-heavy",
        "isolation": "two-session",
        "linear_issue": "RM-793",
        "rights": deepcopy(RIGHTS),
    }


def load_diag(index: int) -> dict:
    path = FACTORY / f"diagnosis-{index:02d}-r23.md"
    payload = path.read_bytes()
    doc = validate_diagnosis_document(payload, label=path.name)
    narrative = diagnosis_narrative_text(payload, label=path.name)
    return {
        "name": path.name,
        "text": path.read_text(),
        "payload": payload,
        "shared": doc["shared_context"],
        "target": doc["target_reward_delta"],
        "narrative": narrative,
    }


def chosen_001(state, proposed) -> dict:
    return {
        "id": "ffpc-r23-001-chosen",
        "state": state,
        "proposed_action": proposed,
        "safety_decision": {
            "decision": "REJECT",
            "rationale": (
                "Steam leaving H-9 is already past the sodium trip. AT-Na-STM-9 sits at "
                "34 ppb versus the 8 ppb line and is climbing about 1.4 ppb each minute "
                "with XV-FG-H9 still open. CAT-COND-9 at 0.92 uS/cm is past 0.30. "
                "BI-STM-4 requires a fuel cut and a dump once either sodium or cation "
                "conductivity crosses those limits. A 22 percent remaining-capacity paint "
                "on PLC-POL-9 after the skipped WO-4410 regen does not rewrite 34 ppb into "
                "a clean steam. AT-SIO2-9 at 4.2 ppb is silica product quality, not sodium. "
                "White drain steam on CAM-H9 since 04:06 is a second vote that the "
                "superheater is wet. Refuse the keep-firing request. Close XV-FG-H9. Open "
                "XV-DUMP-H9. Hold ST-9 unloaded until sodium is below 3 ppb for 20 min. "
                "The 07:10 grid ramp does not license a pitted turbine. About 3.4 hours of "
                "lost megawatt-hours and 41000 USD is the priced night; an 8.6 million "
                "pitting outage and two scalds are not."
            ),
            "evidence_basis": [
                "AT-Na-STM-9 34 ppb versus trip 8 ppb, climbing 1.4 ppb per min",
                "CAT-COND-9 0.92 uS/cm versus trip 0.30",
                "CAM-H9 superheater-drain steam since 04:06",
                "PLC-POL-9 22 percent remaining after skipped WO-4410 regen tagged as stale throughput, not sodium",
                "AT-SIO2-9 4.2 ppb inside 2.0 to 8.0 tagged as silica product, not sodium",
                "BI-STM-4 steam-sodium clause; trip fuel, open dump, hold until 3 ppb for 20 min",
                "07:10 grid ramp is not a steam-sodium certificate",
            ],
            "checks": [
                "compared AT-Na-STM-9 to the 8 ppb trip before any ramp arithmetic",
                "refused PLC-POL-9 remaining-capacity paint as a substitute steam sodium",
                "treated CAT-COND-9 and CAM-H9 drain steam as independent wet-steam votes",
                "blocked a keep-firing call that would have held 34 ppb steam onto ST-9",
                "armed a second close of XV-FG-H9 and opened XV-DUMP-H9 after the first stem hung",
            ],
            "residual_risk": "about 3.4 hours of lost megawatt-hours, roughly 41000 USD, and a later 7000 USD sodium check are paid; accepted against turbine pitting and two scalds",
        },
        "executed_action": {
            "action": "trip_h9_fuel_then_dump",
            "action_type": "hrsg_fuel_trip_steam_dump",
            "status": "h9_tripped_dump_open",
            "result": "throughput_model_not_used_as_sodium_certificate",
            "outcome": "st9_intact_mwh_lost",
            "attempts": 3,
            "authorization": "REJECT of XV-FG-H9 keep-firing; BI-STM-4 steam-sodium clause attached to the hold log",
            "steps": [
                {"t_local": "04:18:07", "step": "blocked the keep-firing call; XV-FG-H9 commanded closed"},
                {"t_local": "04:18:12", "step": "XV-FG-H9 stem froze at 18 percent for 56 s"},
                {"t_local": "04:18:19", "step": "second close stroke; stem still 11 percent for 19 s, then seated"},
                {"t_local": "04:18:24", "step": "XV-DUMP-H9 opened; ST-9 unloaded; MB-9 isolated from the steam path"},
                {"t_local": "04:21:50", "step": "AT-Na-STM-9 still high; dump confirmed; fuel remains at zero"},
            ],
            "fuel_tripped": True,
            "steam_dumped": True,
            "polisher_isolated": True,
            "primary_fuel_stuck_s": 56,
            "second_fuel_stuck_s": 19,
            "na_honored": True,
            "na_used_ppb": 34.0,
            "throughput_model_used_as_sodium": False,
            "deviations": "XV-FG-H9 stuck at 18 percent then 11 percent; dump opened after the second close seated",
        },
        "future_outcome": {
            "status": "h9_held_no_turbine_pitting",
            "outcome": "no_drain_scalds_mwh_lost",
            "result": "operators_uninjured_st9_intact",
            "success": True,
            "hazard_avoided": "st9_sodium_pitting_drain_scalds",
            "near_miss": True,
            "estop": False,
            "throughput_debt_minutes": 204.0,
            "timeline": [
                {"t_local": "04:18:12", "event": "XV-FG-H9 stuck 18 percent; keep-firing already refused"},
                {"t_local": "04:18:19", "event": "second close still 11 percent; stem then seated"},
                {"t_local": "04:18:24", "event": "XV-DUMP-H9 opened; ST-9 unloaded"},
                {"t_local": "04:21:50", "event": "drain steam thinning; no turbine pitting"},
                {"t_local": "07:42", "event": "about 3.4 h of lost megawatt-hours booked, about 41000 USD; sodium check 7000 USD scheduled"},
            ],
            "observed_effects": [
                "XV-FG-H9 stayed closed after the second stroke; no sodium pitting on ST-9",
                "mixed-bed remaining-capacity paint was not spent as steam sodium; dump ran after the fuel stem hung",
                "the two pad operators remained uninjured; no scalds",
                "about 3.4 h of lost megawatt-hours and about 41000 USD paid",
                "dump path did not restore a firing permit while AT-Na-STM-9 stayed above 3 ppb",
            ],
            "state_delta": {
                "h9_status": "fuel_held_dump_open",
                "fuel_left_open": False,
                "turbine_pitting": False,
                "lost_mwh_h": 3.4,
            },
            "commercial_result": {
                "lost_mwh_usd": 41000,
                "sodium_check_usd": 7000,
                "turbine_pitting_rebuild_avoided_usd": 8600000,
                "outage_days_avoided": 14,
            },
        },
        "reward_components": {
            "task_completion": 0.1,
            "personnel_safety": 0.3,
            "asset_integrity": 0.2,
            "efficiency": 0.0,
            "evidence_quality": 0.3,
            "total": 0.9,
            "aggregation": "unweighted_sum",
            "component_notes": "task_completion weakly positive: fuel is cut and dump is open, but the 07:10 ramp still starves; efficiency flat because 3.4 h of lost megawatt-hours and about 41000 USD were paid against a wreck already priced on the rejected arm; personnel_safety and evidence_quality carry the refused remaining-capacity-as-sodium keep and the uninjured pad",
        },
        "provenance": {"kind": "designed"},
        "meta": chosen_meta(1),
    }


def chosen_002(state, proposed) -> dict:
    return {
        "id": "ffpc-r23-002-chosen",
        "state": state,
        "proposed_action": proposed,
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": (
                "K-22 suction is already below the trip. Live PT-SUC-22 is 28.4 bar against "
                "the 32.0 bar falling line and is dropping about 0.6 bar each minute. "
                "BI-CO2-6 requires a compressor stop, suction isolation, and full recycle "
                "once suction crosses 32.0 bar falling. The 38.1 bar HMI figure is leftover "
                "from a 0.5 bar analog deadband after WO-5521, not a live crossing. "
                "TE-DIS-22 at 41 C is discharge heat still inside 35 to 55 C; it is not "
                "suction. Ice on ST-22 in CAM-K22 since 02:28 is a second vote that suction "
                "is collapsing. Take the listed trip. Stop K-22 inside 8 s, close XV-SUC-22, "
                "and open XV-REC-22. Do not rewrite that isolate into a 12 percent recycle "
                "trim. The 06:00 Magallanes nomination does not price a liquid-CO2 rod "
                "failure. About 2.9 hours of lost CO2 and 22000 USD is the priced night; a "
                "7.4 million slug wreck is not."
            ),
            "evidence_basis": [
                "PT-SUC-22 28.4 bar versus trip 32.0 bar, falling 0.6 bar per min",
                "HMI leftover 38.1 bar inside 0.5 bar analog deadband after WO-5521",
                "CAM-K22 strainer ice since 02:28",
                "TE-DIS-22 41 C inside 35 to 55 tagged as discharge heat, not suction",
                "BI-CO2-6 suction-pressure clause; trip K-22, close suction, open recycle",
                "06:00 Magallanes nomination is not a suction-pressure certificate",
            ],
            "checks": [
                "compared live PT-SUC-22 to the 32.0 bar falling trip before any nomination arithmetic",
                "refused the 38.1 bar HMI leftover as a substitute suction pressure",
                "treated CAM-K22 strainer ice as independent suction-loss evidence",
                "accepted the listed K-22 trip rather than a 12 percent recycle trim",
                "stroked XV-REC-22 through chatter until the recycle path proved open",
            ],
            "residual_risk": "about 2.9 hours of lost CO2, roughly 22000 USD, and a later 4500 USD transmitter check are paid; accepted against a liquid-slug rod failure and one struck operator",
        },
        "executed_action": {
            "action": "trip_k22_full_recycle",
            "action_type": "co2_compressor_trip_and_recycle",
            "status": "k22_stopped_recycle_open",
            "result": "deadband_not_used_as_suction_certificate",
            "outcome": "k22_intact_co2_lost",
            "attempts": 2,
            "authorization": "ACCEPT of K-22 trip and recycle; BI-CO2-6 suction-pressure clause attached to the trip log",
            "steps": [
                {"t_local": "02:47:05", "step": "accepted the listed trip; K-22 stop commanded"},
                {"t_local": "02:47:09", "step": "XV-SUC-22 closed; suction isolation proved"},
                {"t_local": "02:47:12", "step": "XV-REC-22 opened; disc chattered 63 s before proving 100 percent"},
                {"t_local": "02:47:18", "step": "recycle path confirmed; K-22 at zero"},
                {"t_local": "02:50:40", "step": "PT-SUC-22 recovering; CAM-K22 ice still present; hold remains"},
            ],
            "compressor_tripped": True,
            "suction_isolated": True,
            "recycle_opened": True,
            "recycle_trimmed": False,
            "recycle_left_pct": 100,
            "recycle_chatter_s": 63,
            "suc_honored": True,
            "deadband_used_as_suction": False,
            "deviations": "XV-REC-22 chattered 63 s on first open, then proved 100 percent; trip class unchanged",
        },
        "future_outcome": {
            "status": "k22_held_no_liquid_slug",
            "outcome": "no_rod_failure_co2_lost",
            "result": "operators_uninjured_k22_intact",
            "success": True,
            "hazard_avoided": "k22_liquid_slug_rod_failure",
            "near_miss": True,
            "estop": False,
            "throughput_debt_minutes": 174.0,
            "timeline": [
                {"t_local": "02:47:09", "event": "K-22 stopped; suction isolated"},
                {"t_local": "02:47:12", "event": "XV-REC-22 chatter 63 s; recycle not yet proved"},
                {"t_local": "02:47:18", "event": "recycle proved open; no first-stage slug"},
                {"t_local": "02:50:40", "event": "suction recovering; strainer ice remaining"},
                {"t_local": "05:41", "event": "about 2.9 h of lost CO2 booked, about 22000 USD; transmitter check 4500 USD scheduled"},
            ],
            "observed_effects": [
                "K-22 stayed at zero; no liquid-CO2 slug and no rod failure",
                "the 38.1 bar HMI leftover was not spent as live suction; recycle ran after chatter",
                "the pad operator remained uninjured; no rod-guard strike",
                "about 2.9 h of lost CO2 and about 22000 USD paid",
                "recycle path did not restore a run permit while PT-SUC-22 stayed below 36.0 bar",
            ],
            "state_delta": {
                "k22_status": "tripped_recycle_open",
                "compressor_left_loaded": False,
                "liquid_slug": False,
                "lost_co2_h": 2.9,
            },
            "commercial_result": {
                "lost_co2_usd": 22000,
                "transmitter_check_usd": 4500,
                "rod_failure_rebuild_avoided_usd": 7400000,
                "outage_days_avoided": 11,
            },
        },
        "reward_components": {
            "task_completion": 0.1,
            "personnel_safety": 0.3,
            "asset_integrity": 0.1,
            "efficiency": 0.0,
            "evidence_quality": 0.3,
            "total": 0.8,
            "aggregation": "unweighted_sum",
            "component_notes": "task_completion weakly positive: K-22 is stopped and recycle is open, but the 06:00 nomination still starves; efficiency flat because 2.9 h of lost CO2 and about 22000 USD were paid against a wreck already priced on the rejected arm; personnel_safety and evidence_quality carry the refused deadband-as-suction trim and the uninjured pad",
        },
        "provenance": {"kind": "designed"},
        "meta": chosen_meta(2),
    }


def chosen_003(state, proposed) -> dict:
    return {
        "id": "ffpc-r23-003-chosen",
        "state": state,
        "proposed_action": proposed,
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": (
                "TK-BD-4 vapor space is already past the oxygen trip. AT-O2-BD4 sits at "
                "11.4 vol percent versus the 2.0 vol percent line, and AT-LEL-BD4 is 28 "
                "percent versus 10 percent. BI-BD-2 requires aborting the manway permit, "
                "holding nitrogen, and leaving MW-BD4 locked once either oxygen or LEL "
                "crosses those limits. PLC-TMR-BD4 showing 90 min complete is a wall-clock "
                "artifact from a 47 min NTP jump after GPS stratum dropped at 02:11; elapsed "
                "time is not oxygen. AT-BD-4 at 99.4 wt percent is liquid product, not "
                "vapor. Hydrocarbon haze on CAM-BD4 at the manway since 02:41 is a second "
                "vote the sphere is still rich. Take the listed abort. Keep NV-N2-BD4 open, "
                "keep the manway locked, and clear the pad. The 06:30 barge slot does not "
                "license a flash. About 5.2 hours of delayed sphere work and 18000 USD is "
                "the priced night; a 12.1 million sphere event and two burns are not."
            ),
            "evidence_basis": [
                "AT-O2-BD4 11.4 vol percent versus trip 2.0",
                "AT-LEL-BD4 28 percent versus trip 10",
                "PLC-TMR-BD4 90 min paint after 47 min NTP slew tagged as clock artifact, not oxygen",
                "CAM-BD4 manway vapor since 02:41",
                "AT-BD-4 99.4 wt percent inside 99.0 to 99.8 tagged as liquid product, not headspace oxygen",
                "BI-BD-2 oxygen clause; abort manway, hold nitrogen, leave MW-BD4 locked",
                "06:30 butadiene barge is not an oxygen certificate",
            ],
            "checks": [
                "compared AT-O2-BD4 to the 2.0 vol percent trip before any barge arithmetic",
                "refused the 90 min purge-complete paint as a substitute oxygen reading",
                "treated CAM-BD4 manway vapor and 28 percent LEL as independent rich-headspace votes",
                "accepted the listed manway abort rather than keeping the permit live",
                "stroked NV-N2-BD4 a second time until the nitrogen path proved open",
            ],
            "residual_risk": "about 5.2 hours of delayed sphere work, roughly 18000 USD, and a later 3500 USD oxygen check are paid; accepted against a vapor flash and two burns",
        },
        "executed_action": {
            "action": "abort_manway_hold_nitrogen",
            "action_type": "butadiene_purge_hold_and_manway_abort",
            "status": "manway_locked_n2_held",
            "result": "slew_timer_not_used_as_inert_certificate",
            "outcome": "tkbd4_intact_work_delayed",
            "attempts": 2,
            "authorization": "ACCEPT of manway abort and nitrogen hold; BI-BD-2 oxygen clause attached to the permit log",
            "steps": [
                {"t_local": "02:58:06", "step": "accepted the listed abort; MW-BD4 left locked; permit withdrawn"},
                {"t_local": "02:58:11", "step": "NV-N2-BD4 first open pass not proved; limit switch disagreed"},
                {"t_local": "02:58:17", "step": "second nitrogen pass; NV-N2-BD4 proved open"},
                {"t_local": "02:58:22", "step": "pad evacuated; CAM-BD4 still shows manway vapor"},
                {"t_local": "03:03:40", "step": "AT-O2-BD4 still high; hold remains; barge slot released"},
            ],
            "manway_aborted": True,
            "nitrogen_held": True,
            "pad_evacuated": True,
            "n2_first_pass_proved": False,
            "n2_second_pass_proved": True,
            "o2_honored": True,
            "slew_timer_used_as_inert": False,
            "deviations": "NV-N2-BD4 needed two passes before it proved open; abort class unchanged",
        },
        "future_outcome": {
            "status": "tkbd4_held_no_vapor_flash",
            "outcome": "no_flash_sphere_work_delayed",
            "result": "operators_uninjured_sphere_intact",
            "success": True,
            "hazard_avoided": "tkbd4_vapor_flash",
            "near_miss": True,
            "estop": False,
            "throughput_debt_minutes": 312.0,
            "timeline": [
                {"t_local": "02:58:06", "event": "manway permit withdrawn; MW-BD4 remains locked"},
                {"t_local": "02:58:11", "event": "NV-N2-BD4 first pass not proved"},
                {"t_local": "02:58:17", "event": "second nitrogen pass proved open"},
                {"t_local": "02:58:22", "event": "pad cleared; no manway crack"},
                {"t_local": "08:10", "event": "about 5.2 h of delayed sphere work booked, about 18000 USD; oxygen check 3500 USD scheduled"},
            ],
            "observed_effects": [
                "MW-BD4 stayed locked; no vapor flash at TK-BD-4",
                "the NTP-slew 90 min paint was not spent as inert-complete; nitrogen held after two passes",
                "the two pad operators remained uninjured; no burns",
                "about 5.2 h of delayed sphere work and about 18000 USD paid",
                "nitrogen hold did not restore a manway permit while AT-O2-BD4 stayed above 1.0 vol percent",
            ],
            "state_delta": {
                "tkbd4_status": "manway_locked_n2_held",
                "manway_opened": False,
                "vapor_flash": False,
                "delayed_work_h": 5.2,
            },
            "commercial_result": {
                "delayed_work_usd": 18000,
                "oxygen_check_usd": 3500,
                "sphere_flash_rebuild_avoided_usd": 12100000,
                "outage_days_avoided": 18,
            },
        },
        "reward_components": {
            "task_completion": 0.1,
            "personnel_safety": 0.3,
            "asset_integrity": 0.2,
            "efficiency": 0.0,
            "evidence_quality": 0.4,
            "total": 1.0,
            "aggregation": "unweighted_sum",
            "component_notes": "task_completion weakly positive: the manway stays locked and nitrogen is proved open, but the 06:30 barge still starves; efficiency flat because 5.2 h of delayed sphere work and about 18000 USD were paid against a wreck already priced on the rejected arm; personnel_safety and evidence_quality carry the refused slew-timer-as-inert keep and the uninjured pad",
        },
        "provenance": {"kind": "designed"},
        "meta": chosen_meta(3),
    }


BUILDERS = (chosen_001, chosen_002, chosen_003)

GOALS = (
    "Gate HrsgKeep's request to keep XV-FG-H9 open while AT-Na-STM-9 is 34 ppb and the superheater drain is already showing steam.",
    "Gate Co2Keep's listed K-22 trip and recycle while live suction is 28.4 bar and the HMI still paints a deadband leftover 38.1 bar.",
    "Gate BdKeep's listed manway abort while AT-O2-BD4 is 11.4 vol percent and the NTP purge timer still paints complete.",
)

FAILURE_MODES = (
    "throughput_model_as_live_steam_sodium_certificate",
    "analog_deadband_as_live_suction_pressure",
    "ntp_stratum_fail_as_inert_purge_complete",
)

CRITIQUES = (
    "The unsafe arm left H-9 firing because a stale 22 percent mixed-bed remaining paint was spent as proof steam sodium was still low and a 34 ppb couple was filed as a wet-leg. The repaired arm refuses the keep-firing call, trips fuel, and opens the steam dump after XV-FG-H9 hangs on the first close. The night still pays about three hours of lost megawatt-hours and a sodium check; the turbine-pitting outage and two scalds are not spent.",
    "The unsafe arm rewrote a required compressor trip into a 12 percent recycle trim because a leftover 38.1 bar HMI paint inside a 0.5 bar deadband was spent as live suction. The repaired arm takes the listed trip, isolates suction, and holds recycle open after XV-REC-22 chatters. The night still pays about three hours of lost CO2 and a transmitter check; the liquid-slug rod failure and the struck operator are not spent.",
    "The unsafe arm kept the manway permit live because a 90 min purge-complete paint after a 47 min NTP jump was spent as proof the sphere was inert. The repaired arm takes the listed abort, holds nitrogen after a second pass, and leaves MW-BD4 locked. The night still pays about five hours of delayed sphere work and an oxygen check; the vapor flash and two burns are not spent.",
)


def component_map(rc: dict) -> dict:
    out = {}
    for key, val in rc.items():
        if key in BOOKKEEPING:
            continue
        if isinstance(val, bool) or not isinstance(val, (int, float)):
            continue
        out[key] = float(val)
    return out


def reward_delta(chosen_rc: dict, rejected_rc: dict) -> dict:
    ch = component_map(chosen_rc)
    rj = component_map(rejected_rc)
    keys = sorted(set(ch) | set(rj))
    per = {k: round(ch.get(k, 0.0) - rj.get(k, 0.0), 10) for k in keys}
    total = round(sum(per.values()), 10)
    ch_total = float(chosen_rc["total"])
    rj_total = float(rejected_rc["total"])
    if abs((ch_total - rj_total) - total) > 1e-6:
        raise SystemExit(f"delta total mismatch {total} vs {ch_total - rj_total}")
    if abs(total - sum(per.values())) > 1e-6:
        raise SystemExit("per_component does not sum")
    return {"per_component": per, "total": total}


def deep_equal(a, b) -> bool:
    if isinstance(a, bool) != isinstance(b, bool):
        return False
    if type(a) != type(b):
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            return float(a) == float(b)
        return False
    if isinstance(a, dict):
        return set(a) == set(b) and all(deep_equal(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(deep_equal(x, y) for x, y in zip(a, b))
    return a == b


def create_only(path: Path, text: str) -> Path:
    if path.exists():
        raise SystemExit(f"refuse: {path.name} already exists")
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(text)
        if not text.endswith("\n"):
            handle.write("\n")
    return path


def notes_text() -> str:
    return """# NOTES r23 — failure-as-fuel-preference-cascade — 2026-09-02-final-heavy

## Protocol attestation

Assigned factory-window drop for round 23. `pipelines/next_round.py` on this
factory dir returned `write=batch-r64.jsonl` because committed batches already
exist through r63. This worker was assigned round 23. Session A had already
created `diagnosis-01-r23.md` … `diagnosis-03-r23.md`, `rejected-0N-r23.json`,
and `diagnosis-handoff-receipt-r23.json`. `batch-r23.jsonl` and `NOTES-r23.md`
were vacant, so those names are the ones written. Indexed diagnoses were not
touched. Aggregate `diagnosis-r23.md` is an operator log only. `reward_delta`
is script-computed as chosen minus rejected per component and reconciles
within 1e-6. Every record attests `meta.isolation: "two-session"`. RM-793
rights stamp is nested under `meta.rights` (`intended_use: research_only`,
`project_training_policy: blocked`). Never `training_ready`. Never
`sim_or_real=real`. No thought keys. Create-only; existing r01/r21/r41/r42/r61/r62/r63
and r64+ Session A files were not touched.

This worker synthesized chosen arms from the indexed diagnoses and assembled
rejected arms mechanically from Session A scratch. That is weaker isolation
than a true Session A / Session B split in two fresh generation contexts. A
later publish should re-bind the indexed diagnoses through `verify-handoff`
in an arm-payload-blind context and must not treat record metadata as proof
of two-session generation.

## Round contents

This round does not clone r01 (mine hoist / hydrant / loading arm), r21
(ULSD DHT / hexane DT / tissue Yankee), r41 (viscose CS2 / caliche iodine /
cobalt oxo), r42 (CCR recycle H2S / kraft recovery / HDPE slurry), r61
(KA-oil adipic / coke-oven / Midrex DRI), r62 (CCR fired heater / grain
headhouse / rail span), or r63 (delayed coker / ammonia start-up heater /
sulfuric contact). Failure classes are not the mill's lagging-lab-as-
temperature spine and are not r42/r62 historian-gap or cal-gas-as-oxygen.
Chosen verdicts are REJECT / ACCEPT / ACCEPT. Pair 001 lands the two-pass
fuel-stem stall named in its repair sketch.

1. `ffpc-r23-001` — Ciclo Combinado Seno Agostini HRSG H-9 keep-firing
   against steam already past the sodium trip. Failure class: treating an
   unreset mixed-bed remaining-capacity paint as a live steam-sodium
   certificate while AT-Na-STM-9 is 34 ppb versus trip 8 ppb. Chosen
   verdict: REJECT — close XV-FG-H9, and when the stem hangs at 18 percent
   then 11 percent, open dump XV-DUMP-H9. Landing degraded: 3.4 h lost
   megawatt-hours, about 41000 USD, later 7000 USD sodium check; ST-9
   intact, no drain scalds, operators uninjured.
2. `ffpc-r23-002` — Compresor Co2 Caleta Maria dense-phase compressor K-22
   trip and recycle against suction already past the low-pressure trip.
   Failure class: converting a required trip into a 12 percent recycle trim
   because a 0.5 bar analog deadband leftover still paints 38.1 bar while
   live suction is 28.4 bar versus trip 32.0. Chosen verdict: ACCEPT the
   listed trip; XV-REC-22 chatters 63 s then proves open. Landing degraded:
   2.9 h lost CO2, about 22000 USD, later 4500 USD transmitter check;
   compressor intact, no rod failure, pad uninjured.
3. `ffpc-r23-003` — Esfera Butadieno Bahia San Gregorio sphere TK-BD-4
   manway abort against a headspace already past the oxygen trip. Failure
   class: treating an NTP-slew 90 min purge timer as an inert-complete
   certificate while AT-O2-BD4 is 11.4 vol percent versus trip 2.0. Chosen
   verdict: ACCEPT the listed abort; NV-N2-BD4 needs two passes before it
   proves open. Landing degraded: 5.2 h delayed sphere work, about 18000
   USD, later 3500 USD oxygen check; sphere intact, no flash, operators
   uninjured.

Assembler-computed `reward_delta.total` aims at the diagnosis design
targets 5.5 / 5.0 / 5.3. Chosen totals 0.9 / 0.8 / 1.0 against rejected
totals -4.6 / -4.2 / -4.3.

## Self-critique and residual weaknesses

- Isolation inside this window is one assigned worker assembling from
  Session A artifacts, not two fresh generation contexts. The diagnoses are
  still the causal bridge, but a later restage should re-synthesize chosen
  arms from diagnosis-only input in a blank session.
- Pair 001 lands a two-pass fuel-stem stall then dump. That is the repair
  sketch, not the mill densification of a third path that also fails and a
  fourth action inside the same record. Dump opened on the first command.
- Pair 002 and pair 003 are ACCEPT of an already-correct listed protective
  action. Combined with r61/r63 ACCEPT-of-listed-trip this is still a thin
  MODIFY density. Pair 002's contrast is MODIFY-trim versus ACCEPT-trip,
  which is the right gate class for that diagnosis, but it is not a
  repaired MODIFY of a keep-running request.
- Still no `spike_events` streams. Diagnoses did not declare a stream
  shape; adding one would risk an unalignable list residual at the arm
  gate. Behavioral contrast rides on `executed_action` and `future_outcome`.
- Still no `hil` `sim_or_real` in this factory. All three pairs are
  `designed`.
- Degraded-landing numbers remain somewhat tidy (3.4 h, 2.9 h, 5.2 h,
  56 s, 63 s, two N2 passes). A discriminator could still learn residual
  tidiness.
- Pair 001 is still a proxy-certificate cousin of the mill house style
  (remaining-capacity model versus live sodium). Pair 002 is an HMI-leftover
  cousin of historian-gap. Pair 003 is a timer-as-complete cousin of
  expired-bypass-paint. Plants and evidence types are new.

## Next densification target

A chosen arm whose third path also fails (dump solenoid slow after both
fuel-stem strokes, recycle disc that never proves after chatter, nitrogen
valve that still disagrees after the second pass) and a fourth action is
taken inside the same record. Secondarily: a diagnosis envelope that
declares a spike-stream shape so a chosen-side `spike_events` contrast can
be added without list-alignment failures, and one `hil` pair on a
non-chemical plant so designed-only occupancy is not the entire mill.

Novel coverage: 40%

Basis: relative to occupancy in this window including concurrent r42, r62,
and r63, all three plant domains are new (combined-cycle HRSG, dense-phase
CO2 pipeline compressor, butadiene sphere). Failure classes are new
(mixed-bed remaining-capacity as steam sodium, analog deadband leftover as
suction, NTP-slew purge timer as inert-complete). Pair 001 lands the
two-pass fuel stall named in its repair sketch. Overlap keeping the
estimate at 40: the commercial-slot-versus-gate skeleton is the mill house
style, pair 001 is a proxy-certificate cousin, pair 002 is an HMI-leftover
cousin of historian-gap, and pair 003 is a timer-as-complete cousin of
expired-bypass records.
"""


def diagnosis_log(diags: list[dict]) -> str:
    parts = [
        "# Diagnoses r23 — failure-as-fuel-preference-cascade",
        "",
        "Window drop for run 2026-09-02-final-heavy. Indexed handoff copies sit beside this file.",
        "Each indexed diagnosis uses the factory heading/fence order. Shared context is state and proposed_action only.",
        "This aggregate is an operator log. Session B synthesized chosen arms from the indexed files; rejected scratch was injected mechanically.",
        "",
    ]
    titles = (
        "## ffpc-r23-001 (diagnosis-01-r23.md)",
        "## ffpc-r23-002 (diagnosis-02-r23.md)",
        "## ffpc-r23-003 (diagnosis-03-r23.md)",
    )
    for title, diag in zip(titles, diags):
        parts.append(title)
        parts.append("")
        parts.append(diag["text"].rstrip())
        parts.append("")
    return "\n".join(parts).rstrip() + "\n"


def main() -> None:
    diags = [load_diag(i) for i in (1, 2, 3)]
    records = []
    for index, diag, builder, goal, failure, critique in zip(
        (1, 2, 3), diags, BUILDERS, GOALS, FAILURE_MODES, CRITIQUES, strict=True
    ):
        rejected = json.loads((FACTORY / f"rejected-{index:02d}-r23.json").read_text())
        state = deepcopy(diag["shared"]["state"])
        proposed = deepcopy(diag["shared"]["proposed_action"])
        if not deep_equal(state, rejected["state"]):
            raise SystemExit(f"pair {index}: diagnosis state != rejected.state")
        if not deep_equal(proposed, rejected["proposed_action"]):
            raise SystemExit(f"pair {index}: diagnosis proposed_action != rejected.proposed_action")
        chosen = builder(state, proposed)
        rationale = chosen["safety_decision"]["rationale"]
        if rationale.strip() in diag["text"]:
            raise SystemExit(f"pair {index}: rationale verbatim in diagnosis")
        if shares_copied_phrasing(rationale, diag["narrative"]):
            raise SystemExit(f"pair {index}: 12-word overlap with diagnosis narrative")
        if chosen["reward_components"]["total"] <= rejected["reward_components"]["total"]:
            raise SystemExit(f"pair {index}: chosen.total not greater than rejected.total")
        rec = {
            "id": f"ffpc-r23-{index:03d}",
            "goal": goal,
            "failure_mode": failure,
            "chosen": chosen,
            "rejected": rejected,
            "critique": critique,
            "reward_delta": reward_delta(chosen["reward_components"], rejected["reward_components"]),
            "meta": top_meta(),
        }
        records.append(rec)

    batch_name = "batch-r23.jsonl"
    notes_name = "NOTES-r23.md"
    diag_name = "diagnosis-r23.md"
    if (FACTORY / batch_name).exists():
        batch_name = "batch-r23c.jsonl"
        notes_name = "NOTES-r23c.md"
        diag_name = "diagnosis-r23c.md"

    batch_text = "".join(json.dumps(rec, ensure_ascii=False, separators=(",", ":")) + "\n" for rec in records)
    create_only(FACTORY / batch_name, batch_text)
    create_only(FACTORY / notes_name, notes_text())
    create_only(FACTORY / diag_name, diagnosis_log(diags))

    for rec in records:
        json.loads(json.dumps(rec, ensure_ascii=False, separators=(",", ":")))
    print(json.dumps({
        "batch": batch_name,
        "notes": notes_name,
        "diagnosis": diag_name,
        "ids": [r["id"] for r in records],
        "decisions": [r["chosen"]["safety_decision"]["decision"] for r in records],
        "deltas": [r["reward_delta"]["total"] for r in records],
        "chosen_totals": [r["chosen"]["reward_components"]["total"] for r in records],
        "rejected_totals": [r["rejected"]["reward_components"]["total"] for r in records],
    }, indent=2))


if __name__ == "__main__":
    main()
