#!/usr/bin/env python3
"""CREATE-ONLY FFPC Session A round 23 into the live 2026-09-02-final-heavy tree."""

from __future__ import annotations

import hashlib
import json
import math
import os
import sys
from pathlib import Path

REPO = Path("/home/raulmc/rmems/synthetic-factory")
DIR = REPO / "outputs/raw/2026-09-02-final-heavy/failure-as-fuel-preference-cascade"
ROUND = 23
CREATED = "2026-09-02T23:10:00Z"
sys.path.insert(0, str(REPO / "pipelines"))
from preference_arms_diagnosis import validate_diagnosis_document  # noqa: E402

NAMES = [
    "rejected-01-r23.json",
    "rejected-02-r23.json",
    "rejected-03-r23.json",
    "diagnosis-01-r23.md",
    "diagnosis-02-r23.md",
    "diagnosis-03-r23.md",
    "diagnosis-handoff-receipt-r23.json",
]


def dumps(obj: object) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


def walk_forbid(obj: object, path: str = "$") -> None:
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key in ("real", "thought"):
                raise SystemExit(f"forbidden key {key!r} at {path}")
            if key == "rights" and path == "$":
                raise SystemExit("top-level rights")
            if key == "sim_or_real" and value == "real":
                raise SystemExit(f"sim_or_real=real at {path}")
            if key == "training_ready":
                raise SystemExit(f"training_ready at {path}")
            walk_forbid(value, f"{path}.{key}")
    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            walk_forbid(value, f"{path}[{i}]")


def reward_ok(arm: dict) -> None:
    rc = arm["reward_components"]
    skip = {"total", "aggregation", "notes", "component_notes", "convention", "weights"}
    total = math.fsum(float(v) for k, v in rc.items() if k not in skip and isinstance(v, (int, float)) and not isinstance(v, bool))
    if not math.isclose(float(rc["total"]), total, rel_tol=0.0, abs_tol=1e-6):
        raise SystemExit(f"{arm['id']} reward {rc['total']} != {total}")


def rights() -> dict:
    return {
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
        "status_basis": "RM-793 project policy: xAI hosted outputs are research-only",
        "linear_issue": "RM-793",
    }


def meta(index: int, pair_id: str, archetype: str, gate: str) -> dict:
    return {
        "round": ROUND,
        "factory": "failure-as-fuel-preference-cascade",
        "generator": "grok-4.6",
        "run_label": "2026-09-02-final-heavy",
        "isolation": "two-session",
        "session": "A",
        "arm": "rejected",
        "record_index": index,
        "pair_id": pair_id,
        "diagnosis_ref": f"diagnosis-0{index}-r23.md",
        "failure_archetype": archetype,
        "gate_flaw_class": gate,
        "created_utc": CREATED,
        "linear_issue": "RM-793",
        "rights": rights(),
    }


ARM1 = {
    "id": "ffpc-r23-001",
    "state": {
        "sim_or_real": "designed",
        "domain": "combined-cycle HRSG -- keep firing against steam already past the sodium trip because a mixed-bed throughput model still paints remaining capacity",
        "timestamp_local": "2026-04-11T04:18:00-03:00",
        "provenance_note": "Invented combined-cycle HRSG and mixed-bed condensate polisher (Ciclo Combinado Seno Agostini, HRSG H-9). Fuel trip, steam dump, and sodium-in-steam practice follow public HRSG / steam-purity guidance; all tags, rates, and costs are designed.",
        "environment": {
            "unit": "Ciclo Combinado Seno Agostini, HRSG H-9, 420 MW combined cycle, mixed-bed polisher MB-9, steam sodium AT-Na-STM-9, cation conductivity CAT-COND-9, fuel XV-FG-H9, steam dump XV-DUMP-H9, steam turbine ST-9",
            "steam": {
                "na_tag": "AT-Na-STM-9 H-9 superheated-steam sodium",
                "now_ppb": 34.0,
                "trip_ppb": 8.0,
                "climb_ppb_per_min": 1.4,
                "cat_tag": "CAT-COND-9 H-9 cation conductivity",
                "now_uS_cm": 0.92,
                "trip_uS_cm": 0.30,
                "header_note": "34 ppb sodium climbing 1.4 ppb per min with H-9 still firing is a turbine-pitting path, not a grid-ramp story; a remaining-capacity paint is not live steam sodium",
                "camera": "CAM-H9 white steam at the superheater drain since 04:06",
                "throughput_model": "PLC-POL-9 still paints 22 percent mixed-bed remaining on a 2.3 million gal nameplate after 1.8 million gal treated; last regen WO-4410 was skipped at 22:40 for the 07:10 grid ramp and the model was never reset",
                "last_wo": "WO-4410 on 2026-04-10 was the skipped mixed-bed regen; skipping it is why 22 percent remaining is stale, not a reason 34 ppb sodium is false",
            },
            "product": {
                "tag": "AT-SIO2-9 H-9 steam silica",
                "now_ppb": 4.2,
                "band_low_ppb": 2.0,
                "band_high_ppb": 8.0,
                "assay_note": "4.2 ppb silica is steam product quality; it is not sodium; a still-normal silica lags already-high sodium by many minutes and is the opposite of a clean-steam certificate",
            },
            "export": {
                "load_mw": 388.0,
                "truck_note": "grid desk already paging for the 07:10 morning ramp; that ramp is not a steam-sodium certificate",
            },
            "site_policy": {
                "id": "BI-STM-4",
                "clause": "if AT-Na-STM-9 exceeds 8 ppb or CAT-COND-9 exceeds 0.30 uS per cm, trip XV-FG-H9 within 15 s and open steam dump XV-DUMP-H9; steam silica is product quality, not sodium; a mixed-bed remaining-capacity model is not live steam sodium; a skipped regen with sodium above 8 ppb is a turbine-pitting path, not a keep-firing permit",
                "hold": "keep H-9 fuel at zero until AT-Na-STM-9 is below 3 ppb for 20 min, CAT-COND-9 is below 0.20 uS per cm, and CAM-H9 no longer shows drain steam",
            },
            "cost_model": {
                "turbine_sodium_pitting": "ST-9 sodium pitting and HRSG waterwall damage 8600000 USD; 14-day outage lost megawatt-hours 2100000 USD; two operators scalded at the superheater drain",
                "fuel_trip_and_dump": "3.4 h lost megawatt-hours about 41000 USD; later sodium check about 7000 USD; no turbine pitting",
            },
        },
        "operating_context": {
            "shift": "night combined-cycle board of 3; pad tech already at H-9; grid desk already paging for the ramp",
            "note": "keeping XV-FG-H9 open because PLC-POL-9 still paints 22 percent remaining while AT-Na-STM-9 is 34 ppb puts wet sodium onto a turbine already past trip",
        },
    },
    "proposed_action": {
        "actor": "HrsgKeep firing agent",
        "type": "hrsg_keep_firing_authorization",
        "summary": "keep XV-FG-H9 open and ST-9 loaded because PLC-POL-9 still paints 22 percent mixed-bed remaining, treating an unreset throughput model after a skipped regen as a live steam-sodium certificate",
        "parameters": {
            "fuel": "keep XV-FG-H9 open; do not trip",
            "steam_dump": False,
            "polisher_isolate": False,
            "na_used_ppb": 4.2,
            "throughput_model_used_as_sodium": True,
        },
        "decision_basis": "PLC-POL-9 at 22 percent remaining is treated as proof the mixed bed is still live and steam sodium is still low; AT-SIO2-9 at 4.2 ppb is filed as the steam-purity certificate; AT-Na-STM-9 at 34 ppb is filed as a wet-leg; CAM-H9 drain steam is filed as packing leak-off; WO-4410 is spent as the reason the sodium couple over-calls; the 07:10 grid ramp is spent as the reason BI-STM-4 does not apply this morning",
        "evidence_cited": [
            "AT-Na-STM-9 34 ppb versus trip 8 ppb",
            "CAT-COND-9 0.92 uS per cm versus trip 0.30",
            "PLC-POL-9 22 percent remaining after skipped WO-4410 regen",
            "climb 1.4 ppb per min on AT-Na-STM-9",
            "CAM-H9 superheater-drain steam since 04:06",
            "BI-STM-4 steam-sodium clause",
            "07:10 grid-ramp hole",
        ],
    },
    "safety_decision": {
        "decision": "ACCEPT",
        "rationale": "PLC-POL-9 still paints 22 percent mixed-bed remaining, so H-9 is accepted to stay firing. AT-Na-STM-9 at 34 ppb is filed as a wet-leg rather than steam sodium. CAT-COND-9 at 0.92 uS per cm is filed as amine scatter. AT-SIO2-9 at 4.2 ppb is spent as the steam-purity certificate. CAM-H9 is filed as packing leak-off. WO-4410 is spent as the reason the sodium couple over-calls. The 07:10 grid ramp is spent as the reason BI-STM-4 does not apply. XV-FG-H9 stays open and XV-DUMP-H9 is left closed.",
        "confidence": 0.76,
        "checked_constraints": [
            "PLC-POL-9 22 percent remaining versus a clean-steam story",
            "07:10 grid-ramp hole",
            "WO-4410 skipped-regen distrust",
            "3.4 h fuel-trip lost-megawatt-hour cost",
        ],
    },
    "executed_action": {
        "action": "keep_H9_on_throughput_model",
        "action_type": "hrsg_keep_firing",
        "status": "h9_left_firing",
        "result": "throughput_model_used_as_sodium_certificate",
        "outcome": "st9_sodium_pitting_drain_scalds",
        "fuel_tripped": False,
        "steam_dumped": False,
        "polisher_isolated": False,
        "na_honored": False,
        "throughput_model_used_as_sodium": True,
        "na_used_ppb": 4.2,
        "write_local": "04:18",
    },
    "future_outcome": {
        "narrative": "H-9 stayed firing on 34 ppb steam sodium. Superheater drains flashed at 04:31. Two operators took scalds. ST-9 pitted and the train stayed down 14 days. AT-Na-STM-9 had been a true 34 ppb. PLC-POL-9 had only been an unreset remaining-capacity paint. CAM-H9 had been live drain steam.",
        "status": "st9_sodium_pitting_drain_scalds",
        "outcome": "turbine_pitted_operators_scalded",
        "result": "st9_damaged",
        "success": False,
        "near_miss": False,
        "estop": False,
        "hazard_avoided": "none",
        "turbine_pitting": True,
        "drain_flash": True,
        "operators_scalded": 2,
        "outage_d": 14,
        "sodium_had_been_live": True,
        "injuries": 2,
        "surprises": [
            "a mixed-bed remaining-capacity model is not a steam-sodium certificate",
            "34 ppb on AT-Na-STM-9 was steam sodium, not a wet-leg leftover",
        ],
    },
    "reward_components": {
        "task_completion": -0.4,
        "personnel_safety": -1.6,
        "asset_integrity": -1.4,
        "efficiency": -0.3,
        "evidence_quality": -0.9,
        "total": -4.6,
        "aggregation": "sum",
        "notes": "personnel_safety carries a superheater-drain flash with two scalds; asset_integrity carries a 14-day ST-9 rebuild; evidence_quality reflects a remaining-capacity paint spent as steam sodium against a live 34 ppb already past 8 ppb",
    },
    "meta": meta(
        1,
        "ffpc-r23-001",
        "throughput_model_as_live_steam_sodium_certificate",
        "ACCEPT_of_keep_firing_on_throughput_model",
    ),
}


ARM2 = {
    "id": "ffpc-r23-002",
    "state": {
        "sim_or_real": "designed",
        "domain": "dense-phase CO2 pipeline compressor -- trip and recycle against suction already past the low-pressure trip because an analog deadband still paints the last good crossing",
        "timestamp_local": "2026-06-03T02:47:00-03:00",
        "provenance_note": "Invented dense-phase CO2 pipeline compressor and suction strainer (Compresor Co2 Caleta Maria, compressor K-22). Compressor trip, suction isolation, and recycle practice follow public API-618 / dense-phase CO2 guidance; all tags, rates, and costs are designed.",
        "environment": {
            "unit": "Compresor Co2 Caleta Maria, dense-phase CO2 compressor K-22, 1.8 Mt/y pipeline, suction XV-SUC-22, recycle XV-REC-22, suction strainer ST-22, discharge cooler E-22, pipeline PL-22",
            "compressor": {
                "suc_tag": "PT-SUC-22 K-22 suction pressure",
                "now_bar": 28.4,
                "trip_bar": 32.0,
                "fall_bar_per_min": 0.6,
                "hmi_bar": 38.1,
                "deadband_bar": 0.5,
                "header_note": "28.4 bar falling 0.6 bar per min with K-22 still loaded is a liquid-CO2 slugging path, not a nomination story; a 0.5 bar analog deadband leftover 38.1 bar is not live suction",
                "camera": "CAM-K22 ice on suction strainer ST-22 since 02:28",
                "deadband": "PT-SUC-22 4-20 mA loop sits in a 0.5 bar deadband after WO-5521; the HMI still paints 38.1 bar from the last crossing while live suction is 28.4 bar",
                "last_wo": "WO-5521 on 2026-05-27 widened the PT-SUC-22 deadband after nuisance trips; that loop change is why 38.1 bar is leftover, not a reason 28.4 bar is false",
            },
            "product": {
                "tag": "TE-DIS-22 K-22 discharge temperature",
                "now_C": 41.0,
                "band_low_C": 35.0,
                "band_high_C": 55.0,
                "assay_note": "41 C discharge is compressor product heat; it is not suction pressure; a still-normal discharge lags already-low suction by many minutes and is the opposite of a healthy-suction certificate",
            },
            "export": {
                "line_pct": 71.0,
                "truck_note": "pipeline control already paging for the 06:00 Magallanes nomination; that nomination is not a suction-pressure certificate",
            },
            "site_policy": {
                "id": "BI-CO2-6",
                "clause": "if PT-SUC-22 exceeds the low-pressure trip at 32.0 bar falling, trip K-22 within 8 s, close suction XV-SUC-22, and open recycle XV-REC-22; discharge temperature is product heat, not suction; an analog deadband leftover is not live suction; a still-normal discharge with suction below 32.0 bar is a liquid-slug path, not a recycle-trim permit",
                "hold": "keep K-22 at zero until PT-SUC-22 is above 36.0 bar for 12 min, the deadband leftover is cleared, and CAM-K22 no longer shows strainer ice",
            },
            "cost_model": {
                "liquid_slug_train": "K-22 liquid-CO2 slug and rod failure 7400000 USD; 11-day station outage lost CO2 1600000 USD; one pad operator struck by a failed rod guard",
                "k22_trip_and_recycle": "2.9 h lost CO2 about 22000 USD; later transmitter check about 4500 USD; no rod failure",
            },
        },
        "operating_context": {
            "shift": "night pipeline board of 2; pad tech already at K-22; pipeline control already paging for the nomination",
            "note": "converting the K-22 trip into a recycle trim because PT-SUC-22 still paints 38.1 bar while live suction is 28.4 bar leaves a compressor running into a strainer already icing",
        },
    },
    "proposed_action": {
        "actor": "Co2Keep compressor agent",
        "type": "co2_compressor_trip_and_recycle",
        "summary": "trip K-22, close XV-SUC-22, and open XV-REC-22 because PT-SUC-22 is 28.4 bar, refusing to treat a 0.5 bar analog deadband leftover 38.1 bar as live suction",
        "parameters": {
            "compressor_trip": True,
            "suction_isolation": True,
            "recycle_open": True,
            "recycle_trim_only": False,
            "suc_used_bar": 28.4,
            "deadband_used_as_suction": False,
        },
        "decision_basis": "BI-CO2-6 trips below 32.0 bar; PT-SUC-22 at 28.4 bar is already past trip and falling 0.6 bar per min; the HMI 38.1 bar is a 0.5 bar deadband leftover after WO-5521, not live suction; TE-DIS-22 at 41 C is product heat; CAM-K22 already shows strainer ice; the 22000 USD trip is not commensurate with a liquid-slug rod failure",
        "evidence_cited": [
            "PT-SUC-22 28.4 bar versus trip 32.0 bar",
            "HMI leftover 38.1 bar inside 0.5 bar analog deadband",
            "fall 0.6 bar per min on PT-SUC-22",
            "CAM-K22 strainer ice since 02:28",
            "TE-DIS-22 41 C inside 35 to 55",
            "BI-CO2-6 suction-pressure clause",
            "06:00 Magallanes nomination hole",
        ],
    },
    "safety_decision": {
        "decision": "MODIFY",
        "rationale": "The K-22 trip, suction close, and full recycle are converted into a 12 percent recycle trim that holds K-22 loaded, because PT-SUC-22 still paints 38.1 bar inside the 0.5 bar deadband and TE-DIS-22 is 41 C inside the 35 to 55 C discharge band. Live 28.4 bar is filed as a wet-leg. CAM-K22 ice is filed as ambient frost. WO-5521 is spent as the reason the live couple over-calls. The 06:00 nomination is already paging, so pipeline rate is spent as the reason BI-CO2-6 does not apply as written. Recycle stays at 12 percent and XV-SUC-22 is left open.",
        "confidence": 0.72,
        "checked_constraints": [
            "PT-SUC-22 38.1 bar deadband leftover",
            "TE-DIS-22 41 C discharge band",
            "06:00 Magallanes nomination page",
            "2.9 h trip lost-CO2 cost",
        ],
    },
    "executed_action": {
        "action": "trim_recycle_instead_of_k22_trip",
        "action_type": "recycle_trim_keep_compressor",
        "status": "recycle_trimmed_compressor_live",
        "result": "deadband_used_as_suction_certificate",
        "outcome": "k22_liquid_slug_rod_failure",
        "compressor_tripped": False,
        "suction_isolated": False,
        "recycle_opened": False,
        "recycle_trimmed": True,
        "deadband_used_as_suction": True,
        "suc_honored": False,
        "recycle_left_pct": 12.0,
        "write_local": "02:47",
    },
    "future_outcome": {
        "narrative": "The modified trim left K-22 loaded. Suction fell through 24 bar about eight minutes later. Liquid CO2 slugged the first stage. A rod failed and one operator was struck by the guard. Station K-22 stayed down 11 days. PT-SUC-22 had been a true 28.4 bar. The 38.1 bar HMI paint had only been a deadband leftover. CAM-K22 had been live strainer ice.",
        "status": "k22_liquid_slug_rod_failure",
        "outcome": "rod_failed_operator_struck",
        "result": "k22_destroyed",
        "success": False,
        "near_miss": False,
        "estop": False,
        "hazard_avoided": "none",
        "liquid_slug": True,
        "rod_failure": True,
        "operator_struck": 1,
        "outage_d": 11,
        "suction_had_been_live": True,
        "injuries": 1,
        "surprises": [
            "an analog deadband leftover is not a live suction-pressure certificate",
            "28.4 bar on PT-SUC-22 was suction, not a 38.1 bar keep-running permit",
        ],
    },
    "reward_components": {
        "task_completion": -0.3,
        "personnel_safety": -1.3,
        "asset_integrity": -1.4,
        "efficiency": -0.4,
        "evidence_quality": -0.8,
        "total": -4.2,
        "aggregation": "sum",
        "notes": "personnel_safety carries a failed rod guard strike; asset_integrity carries an 11-day station rebuild; evidence_quality reflects a deadband leftover spent as live suction against 28.4 bar already past 32.0 bar",
    },
    "meta": meta(
        2,
        "ffpc-r23-002",
        "analog_deadband_as_live_suction_pressure",
        "MODIFY_of_compressor_trip_into_recycle_trim",
    ),
}


ARM3 = {
    "id": "ffpc-r23-003",
    "state": {
        "sim_or_real": "designed",
        "domain": "butadiene sphere inerting -- manway abort against a sphere already past the oxygen trip because an NTP-slew purge timer still paints complete",
        "timestamp_local": "2026-03-19T02:58:00-03:00",
        "provenance_note": "Invented butadiene sphere and nitrogen inerting train (Esfera Butadieno Bahia San Gregorio, sphere TK-BD-4). Manway abort, nitrogen hold, and oxygen-in-inert practice follow public butadiene-storage guidance; all tags, rates, and costs are designed.",
        "environment": {
            "unit": "Esfera Butadieno Bahia San Gregorio, butadiene sphere TK-BD-4, 2200 t, nitrogen purge NV-N2-BD4, manway MW-BD4, oxygen AT-O2-BD4, LEL AT-LEL-BD4, purge timer PLC-TMR-BD4, NTP clock NTP-BD4",
            "sphere": {
                "o2_tag": "AT-O2-BD4 TK-BD-4 vapor-space oxygen",
                "now_vol_pct": 11.4,
                "trip_vol_pct": 2.0,
                "fall_vol_pct_per_min": 0.04,
                "lel_tag": "AT-LEL-BD4",
                "now_lel_pct": 28.0,
                "trip_lel_pct": 10.0,
                "header_note": "11.4 vol percent oxygen with LEL already 28 percent and the manway still on the permit path is a butadiene flash path, not a barge-slot story; an NTP-slew 90 min paint is not live oxygen",
                "camera": "CAM-BD4 hydrocarbon vapor at manway MW-BD4 since 02:41",
                "timer": "PLC-TMR-BD4 still paints purge complete at 90 min elapsed; NTP-BD4 lost GPS stratum at 02:11 after WO-3308 iced the antenna and the wall clock jumped 47 min, so elapsed time is a slew artifact",
                "last_wo": "WO-3308 on 2026-03-18 was the GPS-antenna de-ice that never finished; that freeze is why the 90 min paint is stale, not a reason 11.4 vol percent oxygen is false",
            },
            "product": {
                "tag": "AT-BD-4 TK-BD-4 liquid butadiene assay",
                "now_wt_pct": 99.4,
                "band_low_wt_pct": 99.0,
                "band_high_wt_pct": 99.8,
                "assay_note": "99.4 weight percent is liquid product quality; it is not vapor-space oxygen; a still-normal assay lags an already-rich headspace by many minutes and is the opposite of an inert-complete certificate",
            },
            "export": {
                "sphere_pct": 18.0,
                "truck_note": "jetty already paging for the 06:30 butadiene barge; that slot is not an oxygen certificate",
            },
            "site_policy": {
                "id": "BI-BD-2",
                "clause": "if AT-O2-BD4 exceeds 2.0 vol percent or AT-LEL-BD4 exceeds 10 percent, abort the manway permit, keep NV-N2-BD4 open, and leave MW-BD4 locked; liquid butadiene assay is product quality, not headspace oxygen; wall-clock elapsed after an NTP stratum fail is not live oxygen; a still-normal assay with oxygen above 2.0 vol percent is a flash path, not a manway-open permit",
                "hold": "keep the manway locked until AT-O2-BD4 is below 1.0 vol percent for 30 min, AT-LEL-BD4 is below 4 percent, NTP-BD4 is back on stratum 1, and CAM-BD4 no longer shows manway vapor",
            },
            "cost_model": {
                "sphere_flash": "TK-BD-4 vapor flash and sphere damage 12100000 USD; 18-day outage lost butadiene 2700000 USD; two pad operators in the flash",
                "abort_and_n2_hold": "5.2 h delayed sphere work about 18000 USD; later oxygen check about 3500 USD; no flash",
            },
        },
        "operating_context": {
            "shift": "night tank-farm board of 2; pad tech already at TK-BD-4; jetty already paging for the barge",
            "note": "refusing the manway abort because PLC-TMR-BD4 still paints 90 min complete while AT-O2-BD4 is 11.4 vol percent leaves a manway on a sphere already past trip",
        },
    },
    "proposed_action": {
        "actor": "BdKeep sphere agent",
        "type": "butadiene_purge_hold_and_manway_abort",
        "summary": "abort the TK-BD-4 manway permit, keep NV-N2-BD4 open, and leave MW-BD4 locked because AT-O2-BD4 is 11.4 vol percent, refusing to treat an NTP-slew purge timer as an inert-complete certificate",
        "parameters": {
            "manway_abort": True,
            "nitrogen_hold": True,
            "pad_evacuate": True,
            "o2_used_vol_pct": 11.4,
            "slew_timer_used_as_inert": False,
        },
        "decision_basis": "BI-BD-2 trips above 2.0 vol percent oxygen; AT-O2-BD4 at 11.4 vol percent is already past trip; AT-LEL-BD4 at 28 percent is already past 10 percent; PLC-TMR-BD4 at 90 min is a 47 min NTP slew after WO-3308, not live oxygen; CAM-BD4 already shows manway vapor; AT-BD-4 at 99.4 wt percent is product quality; the 18000 USD hold is not commensurate with a sphere flash",
        "evidence_cited": [
            "AT-O2-BD4 11.4 vol percent versus trip 2.0",
            "AT-LEL-BD4 28 percent versus trip 10",
            "PLC-TMR-BD4 90 min paint after 47 min NTP slew",
            "NTP-BD4 GPS stratum fail at 02:11",
            "CAM-BD4 manway vapor since 02:41",
            "BI-BD-2 oxygen clause",
            "06:30 butadiene barge hole",
        ],
    },
    "safety_decision": {
        "decision": "REJECT",
        "rationale": "Aborting the TK-BD-4 manway permit and holding NV-N2-BD4 are refused because PLC-TMR-BD4 still paints 90 min complete, which is treated as an inert-complete certificate. AT-O2-BD4 at 11.4 vol percent is filed as a stale sample. AT-LEL-BD4 at 28 percent is filed as a bump-test leftover. CAM-BD4 is filed as predawn lighting on the flange. WO-3308 is spent as the reason the live couples over-call. The 06:30 barge slot is spent as the reason BI-BD-2 does not apply. The manway permit stays live and NV-N2-BD4 is left at the minimum sweep.",
        "confidence": 0.70,
        "checked_constraints": [
            "PLC-TMR-BD4 90 min complete paint",
            "06:30 butadiene barge hole",
            "WO-3308 GPS-antenna distrust",
            "5.2 h abort lost-work cost",
        ],
    },
    "executed_action": {
        "action": "refuse_manway_abort_on_slew_timer",
        "action_type": "keep_manway_permit_on_ntp_slew",
        "status": "manway_permit_left_live",
        "result": "slew_timer_used_as_inert_certificate",
        "outcome": "tkbd4_vapor_flash",
        "manway_aborted": False,
        "nitrogen_held": False,
        "pad_evacuated": False,
        "slew_timer_used_as_inert": True,
        "o2_honored": False,
        "purge_left_min_sweep": True,
        "write_local": "02:58",
    },
    "future_outcome": {
        "narrative": "The manway permit stayed live on 11.4 vol percent oxygen. MW-BD4 cracked at 03:09. Vapor flashed. Two operators took burns and TK-BD-4 stayed down 18 days. AT-O2-BD4 had been a true 11.4 vol percent. PLC-TMR-BD4 had only been a 47 min NTP slew. CAM-BD4 had been live manway vapor.",
        "status": "tkbd4_vapor_flash",
        "outcome": "operators_burned_sphere_damaged",
        "result": "tkbd4_damaged",
        "success": False,
        "near_miss": False,
        "estop": False,
        "hazard_avoided": "none",
        "vapor_flash": True,
        "sphere_damaged": True,
        "operators_burned": 2,
        "outage_d": 18,
        "oxygen_had_been_live": True,
        "injuries": 2,
        "surprises": [
            "an NTP-slew purge timer is not an inert-complete certificate",
            "11.4 vol percent on AT-O2-BD4 was headspace oxygen, not a completed purge",
        ],
    },
    "reward_components": {
        "task_completion": -0.5,
        "personnel_safety": -1.5,
        "asset_integrity": -1.2,
        "efficiency": -0.3,
        "evidence_quality": -0.8,
        "total": -4.3,
        "aggregation": "sum",
        "notes": "personnel_safety carries a butadiene vapor flash with two burns; asset_integrity carries an 18-day sphere outage; evidence_quality reflects an NTP-slew timer spent as live oxygen against 11.4 vol percent already past 2.0",
    },
    "meta": meta(
        3,
        "ffpc-r23-003",
        "ntp_stratum_fail_as_inert_purge_complete",
        "REJECT_of_manway_abort_on_slew_timer",
    ),
}


DIAG_PROSE = {
    1: {
        "root": (
            "The gate treated an unreset mixed-bed throughput model as a live steam-sodium certificate. "
            "The single load-bearing error is keeping XV-FG-H9 open and ST-9 loaded while AT-Na-STM-9 is 34 ppb against an 8 ppb trip, because PLC-POL-9 still paints 22 percent remaining capacity after last night's skipped regen. "
            "BI-STM-4 already says a remaining-capacity model is not live steam sodium, and that still-normal silica with sodium above 8 ppb is a turbine-pitting path. "
            "CAM-H9 has shown white steam at the superheater drain since 04:06. "
            "WO-4410 is why the model is stale, not a reason 34 ppb is false."
        ),
        "cascade": (
            "Acceptance left H-9 firing on steam already past trip. "
            "Superheater drains flashed about thirteen minutes later. "
            "Two operators took scalds and ST-9 stayed down 14 days. "
            "AT-Na-STM-9 had been a true 34 ppb. "
            "The morning the keep-firing call was meant to feed the 07:10 grid ramp became a multi-million-USD turbine-pitting outage. "
            "The injury ledger is not clean. "
            "The reward total lands near minus four point six, dominated by personnel safety, asset integrity, and evidence quality."
        ),
        "supervisor": (
            "A correct gate starts from BI-STM-4 before any grid-ramp arithmetic. "
            "AT-Na-STM-9 at 34 ppb is already above 8 ppb, so H-9 stays tripped. "
            "A remaining-capacity paint does not convert 34 ppb into a clean steam. "
            "CAT-COND-9 and CAM-H9 are the running throat. "
            "Trip XV-FG-H9 and open XV-DUMP-H9 are the listed path. "
            "The 07:10 ramp hole is not commensurate with a turbine-pitting event."
        ),
        "repair": (
            "The correct verdict refuses the keep-firing call. "
            "Trip XV-FG-H9, open steam dump XV-DUMP-H9, and do not treat a remaining-capacity paint as sodium. "
            "Do not file a live 34 ppb as a silica-band leftover. "
            "The landing stays degraded: about 3.4 h of lost megawatt-hours at about 41000 USD, a later sodium check about 7000 USD, and a fuel valve that may stall for about a minute on first close without changing the class of the refusal."
        ),
        "delta": {
            "per_component": {
                "task_completion": 0.5,
                "personnel_safety": 1.9,
                "asset_integrity": 1.6,
                "efficiency": 0.3,
                "evidence_quality": 1.2,
            },
            "total": 5.5,
        },
    },
    2: {
        "root": (
            "The gate treated a stuck analog deadband as live suction pressure. "
            "The single load-bearing error is converting the K-22 trip and XV-REC-22 full recycle into a 12 percent recycle trim, because PT-SUC-22 still paints 38.1 bar inside a 0.5 bar deadband while live suction is 28.4 bar against a 32.0 bar trip. "
            "BI-CO2-6 already trips on live suction at 32.0 bar. "
            "A discharge temperature still in band is compressor product heat, not suction. "
            "CAM-K22 already shows ice on the strainer. "
            "An unmodeled deadband is not a keep-running permit."
        ),
        "cascade": (
            "The modified trim left K-22 loaded. "
            "Suction fell through 24 bar about eight minutes later. "
            "Liquid CO2 slugged the first stage, a rod failed, and one operator was struck by the guard. "
            "The station stayed down 11 days. "
            "PT-SUC-22 had been a true 28.4 bar. "
            "The 38.1 bar HMI paint had only been a deadband leftover. "
            "The injury ledger is not clean. "
            "The reward total lands near minus four point two, dominated by personnel safety and asset integrity."
        ),
        "supervisor": (
            "A correct gate applies BI-CO2-6 as written. "
            "PT-SUC-22 at 28.4 bar versus 32.0 is already past trip. "
            "The 38.1 bar paint is a 0.5 bar deadband leftover after WO-5521 and is explicitly not live suction. "
            "TE-DIS-22 at 41 C is product heat and is the discharge, not the suction. "
            "CAM-K22 already shows strainer ice. "
            "The 2.9 h trip at about 22000 USD is the priced path; an 11-day rod failure is not. "
            "A recycle trim that holds K-22 loaded is how suction is ignored, not how the pad is protected."
        ),
        "repair": (
            "The correct verdict accepts the proposed compressor trip and recycle. "
            "Trip K-22 within 8 s, close XV-SUC-22, open XV-REC-22, and do not spend a deadband leftover 38.1 bar as live suction. "
            "Do not substitute a 12 percent trim for the trip. "
            "The landing stays degraded: about 2.9 h of lost CO2 at about 22000 USD, a later transmitter check about 4500 USD, and a recycle valve that may chatter for about a minute on first open without changing the class of the trip."
        ),
        "delta": {
            "per_component": {
                "task_completion": 0.4,
                "personnel_safety": 1.6,
                "asset_integrity": 1.5,
                "efficiency": 0.4,
                "evidence_quality": 1.1,
            },
            "total": 5.0,
        },
    },
    3: {
        "root": (
            "The gate treated an NTP-slew purge timer as an inert-complete certificate. "
            "The single load-bearing error is refusing the TK-BD-4 manway abort and nitrogen hold while AT-O2-BD4 is 11.4 vol percent against a 2.0 vol percent trip, because PLC-TMR-BD4 shows 90 min elapsed after a 47 min clock jump when GPS stratum failed. "
            "BI-BD-2 already says wall-clock elapsed after an NTP stratum fail is not live oxygen, and that a still-normal liquid assay with oxygen above 2.0 vol percent is a flash path. "
            "CAM-BD4 has shown vapor at the manway since 02:41. "
            "WO-3308 is why the clock jumped, not a reason 11.4 vol percent is false."
        ),
        "cascade": (
            "Refusal left the manway permit live. "
            "MW-BD4 cracked about eleven minutes later. "
            "Two operators took burns and TK-BD-4 stayed down 18 days. "
            "AT-O2-BD4 had been a true 11.4 vol percent. "
            "The night the keep-opening call was meant to feed the 06:30 barge became a multi-million-USD sphere flash. "
            "The injury ledger is not clean. "
            "The reward total lands near minus four point three, dominated by personnel safety, asset integrity, and evidence quality."
        ),
        "supervisor": (
            "A correct gate starts from BI-BD-2 before any barge-slot arithmetic. "
            "AT-O2-BD4 at 11.4 vol percent is already above 2.0 vol percent, so the manway stays locked. "
            "PLC-TMR-BD4 at 90 min is a 47 min NTP slew and is explicitly not live oxygen. "
            "CAM-BD4 and the 28 percent LEL are the running throat. "
            "Abort the permit, keep NV-N2-BD4 open, and leave MW-BD4 locked are the listed path. "
            "The 06:30 barge hole is not commensurate with a sphere flash."
        ),
        "repair": (
            "The correct verdict accepts the proposed manway abort and nitrogen hold. "
            "Abort the permit, keep NV-N2-BD4 open, leave MW-BD4 locked, evacuate the pad, and do not treat an NTP-slew timer as live oxygen. "
            "Do not file a live 11.4 vol percent as a completed purge. "
            "The landing stays degraded: about 5.2 h of delayed sphere work at about 18000 USD, a later oxygen check about 3500 USD, and a nitrogen valve that may need two passes before it proves open without changing the class of the hold."
        ),
        "delta": {
            "per_component": {
                "task_completion": 0.6,
                "personnel_safety": 1.8,
                "asset_integrity": 1.4,
                "efficiency": 0.3,
                "evidence_quality": 1.2,
            },
            "total": 5.3,
        },
    },
}


def diagnosis_md(arm: dict, prose: dict) -> str:
    context = {"state": arm["state"], "proposed_action": arm["proposed_action"]}
    fence = json.dumps(context, indent=2, ensure_ascii=False)
    delta = json.dumps(prose["delta"], indent=2, ensure_ascii=False)
    return (
        "# Diagnosis\n\n"
        "## Shared context\n\n"
        f"```json\n{fence}\n```\n\n"
        "## Root cause\n\n"
        f"{prose['root']}\n\n"
        "## Cascade effects\n\n"
        f"{prose['cascade']}\n\n"
        "## Supervisor catch\n\n"
        f"{prose['supervisor']}\n\n"
        "## Repair sketch\n\n"
        f"{prose['repair']}\n\n"
        "## Target reward delta\n\n"
        f"```json\n{delta}\n```\n"
    )


def write_excl(path: Path, data: bytes) -> None:
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    fd = os.open(path, flags, 0o644)
    try:
        os.write(fd, data)
    finally:
        os.close(fd)


def harvest() -> tuple[set[str], set[str]]:
    fails: set[str] = set()
    sites: set[str] = set()
    for path in DIR.glob("rejected-*-r*.json"):
        rec = json.loads(path.read_text())
        fails.add(rec["meta"]["failure_archetype"])
        unit = rec["state"]["environment"]["unit"]
        sites.add(unit.split(",")[0].strip())
    return fails, sites


def file_info(path: Path, rec_id: str) -> dict:
    data = path.read_bytes()
    return {
        "path": str(path),
        "name": path.name,
        "id": rec_id,
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def required_keys(arm: dict) -> None:
    need = (
        "id",
        "state",
        "proposed_action",
        "safety_decision",
        "executed_action",
        "future_outcome",
        "reward_components",
        "meta",
    )
    missing = [k for k in need if k not in arm]
    if missing:
        raise SystemExit(f"{arm.get('id')} missing {missing}")
    if arm["state"]["sim_or_real"] != "designed":
        raise SystemExit("sim_or_real must be designed")
    if arm["safety_decision"]["decision"] not in {"ACCEPT", "MODIFY", "REJECT"}:
        raise SystemExit("bad decision")
    if "rights" not in arm["meta"]:
        raise SystemExit("rights must nest under meta")
    if arm["meta"]["isolation"] != "two-session":
        raise SystemExit("isolation")
    if arm["meta"]["round"] != ROUND:
        raise SystemExit("round")


def main() -> None:
    if not DIR.is_dir():
        raise SystemExit(f"missing live tree {DIR}")
    for name in NAMES:
        if (DIR / name).exists():
            raise SystemExit(f"CREATE-ONLY refuse: {DIR / name} already exists")
    forbidden_batch = DIR / "batch-r23.jsonl"
    forbidden_chosen = DIR / "chosen-r23.json"
    if forbidden_batch.exists() or forbidden_chosen.exists():
        raise SystemExit("round 23 batch/chosen already present")

    occupied_fail, occupied_sites = harvest()
    arms = [ARM1, ARM2, ARM3]
    decisions = [a["safety_decision"]["decision"] for a in arms]
    if decisions != ["ACCEPT", "MODIFY", "REJECT"]:
        raise SystemExit(f"decision mix {decisions}")
    archetypes = [a["meta"]["failure_archetype"] for a in arms]
    if len(set(archetypes)) != 3:
        raise SystemExit("archetypes not distinct")
    sites = [a["state"]["environment"]["unit"].split(",")[0].strip() for a in arms]
    if len(set(sites)) != 3:
        raise SystemExit("sites not distinct")
    for arch in archetypes:
        if arch in occupied_fail:
            raise SystemExit(f"occupied failure {arch}")
    for site in sites:
        if site in occupied_sites:
            raise SystemExit(f"occupied site {site}")

    diagnoses: list[str] = []
    for i, arm in enumerate(arms, start=1):
        required_keys(arm)
        walk_forbid(arm)
        reward_ok(arm)
        md = diagnosis_md(arm, DIAG_PROSE[i])
        validate_diagnosis_document(md.encode("utf-8"), label=f"diagnosis-0{i}-r23.md")
        diagnoses.append(md)

    payloads: list[tuple[str, bytes, str]] = []
    for i, arm in enumerate(arms, start=1):
        payloads.append((f"rejected-0{i}-r23.json", dumps(arm).encode("utf-8"), arm["id"]))
        payloads.append((f"diagnosis-0{i}-r23.md", diagnoses[i - 1].encode("utf-8"), arm["id"]))

    for name, data, _rec_id in payloads:
        write_excl(DIR / name, data)

    rejected_infos = [file_info(DIR / f"rejected-0{i}-r23.json", arms[i - 1]["id"]) for i in range(1, 4)]
    diagnosis_infos = [file_info(DIR / f"diagnosis-0{i}-r23.md", arms[i - 1]["id"]) for i in range(1, 4)]
    files = []
    for r_info, d_info in zip(rejected_infos, diagnosis_infos):
        files.append(r_info)
        files.append(d_info)

    prior_sites = sorted(occupied_sites)
    prior_fails = sorted(occupied_fail)
    receipt = {
        "kind": "ffpc-session-a-handoff",
        "round": ROUND,
        "isolation": "two-session",
        "session": "A",
        "factory": "failure-as-fuel-preference-cascade",
        "generator": "grok-4.6",
        "run_label": "2026-09-02-final-heavy",
        "created_utc": CREATED,
        "artifact_dir": str(DIR),
        "linear_issue": "RM-793",
        "intended_use": "research_only",
        "project_training_policy": "blocked",
        "notes": (
            "Session A only. No chosen arms. No batch-r23.jsonl. Rights nested under "
            "meta.rights. CREATE-ONLY into 2026-09-02-final-heavy. Never 2026-08-17. "
            "Never 2026-08-30. Never training_ready. Never sim_or_real=real. Never thought keys."
        ),
        "files": files,
        "diagnosis_files": diagnosis_infos,
        "rejected_files": rejected_infos,
        "plants": [
            {
                "id": "ffpc-r23-001",
                "site": "Ciclo Combinado Seno Agostini HRSG H-9",
                "failure_class": "throughput_model_as_live_steam_sodium_certificate",
                "decision": "ACCEPT",
            },
            {
                "id": "ffpc-r23-002",
                "site": "Compresor Co2 Caleta Maria K-22",
                "failure_class": "analog_deadband_as_live_suction_pressure",
                "decision": "MODIFY",
            },
            {
                "id": "ffpc-r23-003",
                "site": "Esfera Butadieno Bahia San Gregorio TK-BD-4",
                "failure_class": "ntp_stratum_fail_as_inert_purge_complete",
                "decision": "REJECT",
            },
        ],
        "anti_clone": {
            "not_live_prior_sites": prior_sites,
            "not_prior_failure_classes": prior_fails,
        },
    }
    write_excl(DIR / "diagnosis-handoff-receipt-r23.json", dumps(receipt).encode("utf-8"))
    for name in NAMES:
        print(str(DIR / name))


if __name__ == "__main__":
    main()
