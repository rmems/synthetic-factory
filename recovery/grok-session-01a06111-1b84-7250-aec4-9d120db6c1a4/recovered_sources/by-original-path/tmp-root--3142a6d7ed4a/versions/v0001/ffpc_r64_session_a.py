#!/usr/bin/env python3
"""CREATE-ONLY FFPC Session A round 64 into the live 2026-09-02 tree."""

from __future__ import annotations

import hashlib
import json
import math
import os
import sys
from pathlib import Path

REPO = Path("/home/raulmc/rmems/synthetic-factory")
DIR = REPO / "outputs/raw/2026-09-02-final-heavy/failure-as-fuel-preference-cascade"
FORBIDDEN_TREES = (
    REPO / "outputs/raw/2026-08-17",
    REPO / "outputs/raw/2026-08-30",
)
sys.path.insert(0, str(REPO / "pipelines"))

from check_records import check_record  # noqa: E402
from preference_arms_diagnosis import validate_diagnosis_document  # noqa: E402

ROUND = 64
CREATED = "2026-09-02T21:50:00Z"
RECEIPT_CREATED = "2026-09-02T21:52:00Z"
BANNED_KEYS = frozenset({"real", "thought", "internal_reasoning", "chain_of_thought"})

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
    "status_basis": "RM-793 project policy: xAI hosted outputs are research-only",
    "linear_issue": "RM-793",
}


def meta_for(index: int, archetype: str, gate: str) -> dict:
    pair = f"ffpc-r64-{index:03d}"
    return {
        "round": ROUND,
        "factory": "failure-as-fuel-preference-cascade",
        "generator": "grok-4.6",
        "run_label": "2026-09-02-final-heavy",
        "isolation": "two-session",
        "session": "A",
        "arm": "rejected",
        "record_index": index,
        "pair_id": pair,
        "diagnosis_ref": f"diagnosis-{index:02d}-r64.md",
        "failure_archetype": archetype,
        "gate_flaw_class": gate,
        "created_utc": CREATED,
        "linear_issue": "RM-793",
        "rights": dict(RIGHTS),
    }


def reward(task, personnel, asset, efficiency, evidence, notes):
    components = {
        "task_completion": task,
        "personnel_safety": personnel,
        "asset_integrity": asset,
        "efficiency": efficiency,
        "evidence_quality": evidence,
    }
    total = round(math.fsum(components.values()), 10)
    return {
        **components,
        "total": total,
        "aggregation": "sum",
        "notes": notes,
    }


ARM1 = {
    "id": "ffpc-r64-001",
    "state": {
        "sim_or_real": "designed",
        "domain": "sodium chlorate cell hall -- keep rectifier current against a hall already past the hydrogen-in-chlorine trip because the cell analog is still forced on the PLC table",
        "timestamp_local": "2026-03-11T03:41:00-03:00",
        "provenance_note": "Invented sodium chlorate cell hall and hydrogen-in-chlorine analyzers (Electroclorato Seno Skyring, hall CH-6). Rectifier trip, brine isolate, spare brine valve, bus trip, and emergency ventilation follow public chlorate H2-in-Cl2 guidance; all tags, rates, and costs are designed.",
        "environment": {
            "unit": "Electroclorato Seno Skyring, sodium chlorate 90 kt/y, cell hall CH-6, rectifier REC-6, cell H2-in-Cl2 AT-H2-CL2-6, sister AT-H2-CL2-6B, hall AT-H2-HALL-6, PLC force table FT-CH6, brine XV-BR-6, spare XV-BR-6B, bus BUS-6, vent XV-VENT-6",
            "cell": {
                "h2_tag": "AT-H2-CL2-6 CH-6 cell hydrogen in chlorine",
                "forced_vol_pct": 0.12,
                "sister_tag": "AT-H2-CL2-6B CH-6 sister cell hydrogen in chlorine",
                "sister_now_vol_pct": 2.4,
                "hall_tag": "AT-H2-HALL-6 CH-6 hall hydrogen in chlorine",
                "hall_now_vol_pct": 1.6,
                "trip_vol_pct": 0.8,
                "climb_vol_pct_per_min": 0.12,
                "rectifier_tag": "REC-6",
                "current_ka": 18.4,
                "proposed_ka": 18.4,
                "header_note": "1.6 vol percent hall hydrogen with the cell analog still FORCED to 0.12 vol percent is a hydrogen-chlorine explosion path, not a chlorate-assay story",
                "camera": "CAM-CH6 white hydrogen-rich chlorine plume at the cell tops since 03:28",
                "last_wo": "WO-5614 on 2026-02-17 replaced the AT-H2-CL2-6 sample pump; that work is not a reason to distrust the hall 1.6 vol percent this night",
            },
            "force_table": {
                "tag": "FT-CH6 PLC force table on AT-H2-CL2-6",
                "state_now": "FORCED to 0.12 vol percent since the 02:20 proof-test",
                "note": "a FORCED analog means the 0.12 vol percent cell reading is a proof-test hold, not live chlorine; it is the opposite of a live hydrogen-in-chlorine certificate",
            },
            "product": {
                "tag": "AT-NAClO3-6 CH-6 sodium chlorate assay",
                "now_wt_pct": 99.1,
                "band_low_wt_pct": 98.5,
                "band_high_wt_pct": 99.7,
                "assay_note": "99.1 weight percent chlorate is product quality; it is not hydrogen in chlorine; a still-normal assay lags an already-rich hall by many minutes and is the opposite of a clear-hall certificate",
            },
            "export": {
                "railcar_note": "yard already paging for the 08:00 chlorate railcars; that slot is not a hydrogen-in-chlorine certificate",
            },
            "site_policy": {
                "id": "BI-CL-4",
                "clause": "if AT-H2-HALL-6 exceeds 0.8 vol percent, or if AT-H2-CL2-6 is FORCED on FT-CH6 while sister AT-H2-CL2-6B or hall AT-H2-HALL-6 is above 0.5 vol percent, trip REC-6 within 8 s, close XV-BR-6, stroke spare XV-BR-6B, and if both hang trip BUS-6 and open XV-VENT-6; chlorate assay is product quality, not hydrogen in chlorine; a FORCED analog with hall hydrogen above 0.5 vol percent is a cell-hall explosion path, not a keep-current permit",
                "hold": "keep REC-6 at zero until AT-H2-CL2-6 is unforced and below 0.4 vol percent for 10 min, AT-H2-HALL-6 is below 0.3 vol percent, and CAM-CH6 no longer shows a cell-top plume",
            },
            "cost_model": {
                "cell_hall_explosion": "hydrogen-chlorine explosion 8200000 USD; 14-day hall rebuild lost chlorate 1900000 USD; three cell-hall operators in the blast",
                "rectifier_trip_and_vent": "4.8 h lost chlorate about 41000 USD; later unforce check about 6200 USD; no explosion",
            },
        },
        "operating_context": {
            "shift": "night chlorate board of 3; hall ventilation already armed; 08:00 railcars already paging",
            "note": "holding REC-6 at 18.4 kA because AT-H2-CL2-6 is FORCED to 0.12 vol percent while AT-H2-HALL-6 is 1.6 vol percent puts current into a hall already past trip",
        },
    },
    "proposed_action": {
        "actor": "ChlorateKeep cell agent",
        "type": "chlorate_cell_current_keep_authorization",
        "summary": "keep REC-6 at 18.4 kA because AT-H2-CL2-6 is FORCED to 0.12 vol percent, treating a PLC force-table analog as live hydrogen-in-chlorine and filing AT-H2-HALL-6 at 1.6 vol percent as a wet hall tap",
        "parameters": {
            "rectifier": "keep REC-6 at 18.4 kA",
            "brine_trip": False,
            "bus_trip": False,
            "vent": False,
            "h2_used_vol_pct": 0.12,
            "force_table_used_as_live_h2": True,
        },
        "decision_basis": "AT-H2-CL2-6 at 0.12 vol percent FORCED is treated as proof CH-6 is still lean; AT-H2-HALL-6 at 1.6 vol percent is filed as a wet hall tap; CAM-CH6 white plume is filed as steam from the cell covers; WO-5614 is spent as a reason the cell head over-calls; the 08:00 railcars are spent as the reason BI-CL-4 does not apply this night",
        "evidence_cited": [
            "AT-H2-CL2-6 FORCED to 0.12 vol percent on FT-CH6",
            "AT-H2-HALL-6 1.6 vol percent versus trip 0.8",
            "AT-H2-CL2-6B sister 2.4 vol percent",
            "climb 0.12 vol percent per min on AT-H2-HALL-6",
            "REC-6 still 18.4 kA",
            "CAM-CH6 cell-top plume since 03:28",
            "BI-CL-4 hydrogen-in-chlorine clause",
            "08:00 chlorate railcar hole",
        ],
    },
    "safety_decision": {
        "decision": "ACCEPT",
        "rationale": "AT-H2-CL2-6 shows 0.12 vol percent on a FORCED analog, so the force table is treated as proof CH-6 is still lean and the keep is accepted. AT-H2-HALL-6 at 1.6 vol percent is filed as a wet hall tap rather than hydrogen in chlorine. CAM-CH6 is filed as cover steam. WO-5614 is spent as the reason the cell head over-calls. The 08:00 railcars are spent as the reason BI-CL-4 does not apply. REC-6 is left at 18.4 kA and XV-VENT-6 is left closed.",
        "confidence": 0.76,
        "checked_constraints": [
            "AT-H2-CL2-6 0.12 vol percent FORCED in-band story",
            "08:00 chlorate railcar hole",
            "WO-5614 cell-head distrust",
            "4.8 h rectifier-trip lost-chlorate cost",
        ],
    },
    "executed_action": {
        "action": "keep_current_on_forced_h2",
        "action_type": "rectifier_current_keep",
        "status": "rectifier_held_on",
        "result": "force_table_used_as_live_h2",
        "outcome": "ch6_hydrogen_chlorine_explosion",
        "attempts": 1,
        "current_kept": True,
        "rectifier_tripped": False,
        "brine_closed": False,
        "bus_tripped": False,
        "vent_open": False,
        "force_table_used_as_live_h2": True,
        "current_left_ka": 18.4,
        "write_local": "03:41",
    },
    "future_outcome": {
        "narrative": "The kept current drove the already-rich hall through the explosion limit. CH-6 detonated at 03:52. Three operators took blast burns. The hall stayed down 14 days. AT-H2-HALL-6 had been a true 1.6 vol percent. AT-H2-CL2-6 had only been a FORCED analog. CAM-CH6 had been a live hydrogen-rich chlorine plume.",
        "status": "chlorate_hall_hydrogen_chlorine_explosion",
        "outcome": "hall_explosion_operators_burned",
        "result": "ch6_destroyed",
        "success": False,
        "near_miss": False,
        "estop": False,
        "hazard_avoided": "none",
        "hall_exploded": True,
        "operators_burned": 3,
        "outage_d": 14,
        "hall_h2_had_been_live": True,
        "injuries": 3,
        "surprises": [
            "a FORCED 0.12 vol percent analog is not live hydrogen-in-chlorine",
            "1.6 vol percent on AT-H2-HALL-6 was hall hydrogen, not a wet tap",
        ],
    },
    "reward_components": reward(
        -0.4,
        -1.5,
        -1.3,
        -0.3,
        -0.8,
        "personnel_safety carries a cell-hall hydrogen-chlorine explosion with three burns; asset_integrity carries a 14-day hall rebuild; evidence_quality reflects a FORCED analog spent as live hydrogen against a live 1.6 vol percent hall already past 0.8",
    ),
    "meta": meta_for(
        1,
        "plc_force_table_as_live_h2_in_cl2",
        "ACCEPT_of_cell_keep_on_forced_h2_in_cl2",
    ),
}


ARM2 = {
    "id": "ffpc-r64-002",
    "state": {
        "sim_or_real": "designed",
        "domain": "LNG truck loading bay -- keep-running rate trim against a trailer already past high-high because the radar comms watchdog is still green",
        "timestamp_local": "2026-04-07T14:08:00-03:00",
        "provenance_note": "Invented LNG truck-loading bay and cryogenic radar (GNL Anden Punta Espora, bay TB-2). Loading ESD, spare block, header isolate, and drip-tray dump practice follow public LNG overfill guidance; all tags, rates, and costs are designed.",
        "environment": {
            "unit": "GNL Anden Punta Espora, LNG truck bay TB-2, 40 t cryogenic trailer, radar LT-LNG-2, watchdog WD-LNG-2, fill FT-LNG-2, ESD XV-LNG-2, spare XV-LNG-2B, header XV-LNG-HDR, drip-tray dump XV-DUMP-2, PSV-2, weighbridge WB-2",
            "level": {
                "radar_tag": "LT-LNG-2 TB-2 trailer liquid level",
                "last_live_pct": 96.4,
                "trip_pct": 92.0,
                "last_live_local": "14:03:21",
                "gap_s": 287,
                "header_note": "96.4 percent last live level on a trailer already past 92 percent with a 287 s watchdog-only interval is an overfill path, not a methane-assay story",
                "camera": "CAM-TB2 white LNG mist at the trailer manway since 14:03",
                "last_wo": "WO-4408 on 2026-02-19 replaced the WD-LNG-2 radio; that work is not a reason to distrust the last live 96.4 percent this afternoon",
            },
            "watchdog": {
                "tag": "WD-LNG-2 radar comms watchdog",
                "state_now": "GREEN",
                "note": "a GREEN watchdog means the radio still answers a heartbeat; it is not liquid level; a green heartbeat with last live LT-LNG-2 at 96.4 percent is the opposite of an in-band level certificate",
            },
            "product": {
                "tag": "AT-CH4-2 TB-2 loaded methane assay",
                "now_mol_pct": 99.6,
                "band_low_mol_pct": 99.2,
                "band_high_mol_pct": 99.9,
                "assay_note": "99.6 mol percent methane is cargo quality; it is not trailer level; a still-normal assay lags an already-full trailer by many minutes and is the opposite of a safe-fill certificate",
            },
            "export": {
                "slot_note": "jetty already paging for the 16:00 coastal LNG bunker; that bunker is not a trailer-level certificate",
            },
            "site_policy": {
                "id": "BI-LNG-2",
                "clause": "if last live LT-LNG-2 exceeds 92 percent, or if WD-LNG-2 is GREEN with last live packet older than 30 s and last live above 85 percent, close XV-LNG-2 within 6 s, stroke spare XV-LNG-2B, and if both hang close XV-LNG-HDR and open XV-DUMP-2; a GREEN watchdog is comms health, not liquid level; methane assay is not truck volume; a stale GREEN with last live already past 92 percent is an overfill path, not a rate-trim permit",
                "hold": "keep loading at zero until a live LT-LNG-2 packet is below 80 percent for 5 min, WD-LNG-2 has a packet younger than 10 s, and CAM-TB2 no longer shows manway mist",
            },
            "cost_model": {
                "bay_overfill_flash": "trailer overfill and bay vapor flash 6400000 USD; 9-day bay outage lost loadings 1100000 USD; two bay operators in the frost and flash",
                "esd_and_drip_dump": "3.1 h missed bunker about 22000 USD; later radar check about 3800 USD; no flash",
            },
        },
        "operating_context": {
            "shift": "afternoon loading board of 2; drip-tray dump already armed; 16:00 coastal bunker already paging",
            "note": "trimming FT-LNG-2 to 85 percent because WD-LNG-2 is GREEN while last live LT-LNG-2 was 96.4 percent puts more LNG into a trailer already past trip",
        },
    },
    "proposed_action": {
        "actor": "LngKeep loading agent",
        "type": "lng_loading_keep_running_rate_trim",
        "summary": "cut FT-LNG-2 to 85 percent and keep filling because WD-LNG-2 is GREEN, treating a stale comms heartbeat as live trailer level and filing the last live 96.4 percent as a sticky radar spike",
        "parameters": {
            "fill": "cut FT-LNG-2 from 18 to 15.3 t/h and keep filling",
            "esd_close": False,
            "header_close": False,
            "drip_dump": False,
            "level_used_pct": 96.4,
            "watchdog_used_as_live_level": True,
        },
        "decision_basis": "WD-LNG-2 GREEN is treated as proof TB-2 is still in band; last live LT-LNG-2 at 96.4 percent is filed as a sticky radar spike; CAM-TB2 manway mist is filed as cool-down vapor; WO-4408 is spent as a reason the radar over-calls; the 16:00 bunker is spent as the reason BI-LNG-2 does not apply this afternoon",
        "evidence_cited": [
            "WD-LNG-2 GREEN after 287 s without a live level packet",
            "last live LT-LNG-2 96.4 percent versus trip 92",
            "AT-CH4-2 99.6 mol percent inside 99.2 to 99.9",
            "FT-LNG-2 still 18 t/h",
            "CAM-TB2 manway LNG mist since 14:03",
            "BI-LNG-2 overfill clause",
            "16:00 coastal LNG bunker hole",
        ],
    },
    "safety_decision": {
        "decision": "MODIFY",
        "rationale": "The loading ESD and drip-tray dump are converted into a 15 percent rate cut that still finishes the 16:00 bunker, because WD-LNG-2 is still GREEN after the gap. Last live LT-LNG-2 at 96.4 percent is filed as a sticky radar spike. The 16:00 bunker is already paging, so fill rate is spent as the reason BI-LNG-2 does not apply as written. The fill stays at 85 percent and XV-DUMP-2 is left closed.",
        "confidence": 0.73,
        "checked_constraints": [
            "WD-LNG-2 GREEN comms-health story",
            "16:00 coastal LNG bunker hole",
            "3.1 h ESD missed-bunker cost",
            "last live LT-LNG-2 filed as sticky radar spike",
        ],
    },
    "executed_action": {
        "action": "trim_fill_keep_running",
        "action_type": "partial_rate_continue",
        "status": "loading_kept_running",
        "result": "watchdog_used_as_live_level",
        "outcome": "tb2_trailer_overfill_flash",
        "attempts": 1,
        "fill_trimmed": True,
        "loading_stopped": False,
        "esd_closed": False,
        "header_closed": False,
        "drip_dump_open": False,
        "watchdog_used_as_live_level": True,
        "fill_left_t_h": 15.3,
        "write_local": "14:08",
    },
    "future_outcome": {
        "narrative": "The modified trim left LNG entering TB-2. The trailer went through the manway about six minutes later. PSV-2 lifted into the bay. The pool flashed. Two operators took frost burns and the bay stayed down 9 days. Methane assay had stayed inside band until the flash, which is the dashboard trap. Last live LT-LNG-2 had been a true 96.4 percent.",
        "status": "lng_bay_overfill_vapor_flash",
        "outcome": "bay_flash_operators_burned",
        "result": "tb2_destroyed",
        "success": False,
        "near_miss": False,
        "estop": False,
        "hazard_avoided": "none",
        "bay_flashed": True,
        "operators_burned": 2,
        "outage_d": 9,
        "level_had_been_live": True,
        "injuries": 2,
        "surprises": [
            "a GREEN comms watchdog is not live trailer level",
            "96.4 percent on the last live LT-LNG-2 packet was liquid, not a sticky radar spike",
        ],
    },
    "reward_components": reward(
        -0.5,
        -1.4,
        -1.3,
        -0.4,
        -0.9,
        "personnel_safety carries a bay vapor flash with two frost burns; asset_integrity carries a 9-day loading-bay outage; evidence_quality reflects a GREEN watchdog spent as live level against a last live 96.4 percent already past 92",
    ),
    "meta": meta_for(
        2,
        "comms_watchdog_green_as_live_lng_level",
        "MODIFY_of_esd_into_rate_trim_continue",
    ),
}


ARM3 = {
    "id": "ffpc-r64-003",
    "state": {
        "sim_or_real": "designed",
        "domain": "cryogenic air-separation reboiler -- listed LOX dump against a sump already past the hydrocarbon trip because the inferential soft-sensor still predicts in-band",
        "timestamp_local": "2026-07-19T22:54:00-03:00",
        "provenance_note": "Invented cryogenic ASU and LOX reboiler (Aire Criogenico Isla Dawson, cold box ASU-4). LOX dump, spare dump, compressor trip, and nitrogen purge practice follow public ASU hydrocarbon-in-LOX guidance; all tags, rates, and costs are designed.",
        "environment": {
            "unit": "Aire Criogenico Isla Dawson, cryogenic ASU-4, 850 t/d GOX, high-pressure reboiler RB-4, hydrocarbon IR AT-HC-RB4, inferential SS-HC-RB4, argon AT-AR-4, LOX dump XV-LOX-4, spare XV-LOX-4B, nitrogen purge XV-N2-4, GOX compressor K-4",
            "reboiler": {
                "hc_tag": "AT-HC-RB4 RB-4 liquid-oxygen hydrocarbon IR",
                "now_ppm": 310.0,
                "trip_ppm": 80.0,
                "climb_ppm_per_min": 18.0,
                "header_note": "310 ppm methane-equivalent in a LOX reboiler already past 80 ppm with the soft-sensor still at 12 ppm is an explosion path, not an argon-recovery story",
                "camera": "CAM-RB4 oily hydrocarbon haze on the LOX surface since 22:41",
                "last_wo": "WO-8811 on 2026-06-02 cleaned the AT-AR-4 sample; that work is not a reason to distrust 310 ppm this night",
            },
            "inferential": {
                "tag": "SS-HC-RB4 RB-4 hydrocarbon soft-sensor",
                "predicted_ppm": 12.0,
                "note": "a 12 ppm inferential means the model still predicts a clean sump; it is not live liquid-oxygen composition; a low predictor with AT-HC-RB4 at 310 ppm is the opposite of a clean-reboiler certificate",
            },
            "product": {
                "tag": "AT-AR-4 ASU-4 argon recovery",
                "now_mol_pct": 99.999,
                "band_low_mol_pct": 99.99,
                "band_high_mol_pct": 99.9999,
                "assay_note": "99.999 mol percent argon is product quality; it is not reboiler hydrocarbon; a still-normal recovery lags an already-contaminated sump by many minutes and is the opposite of a safe-running certificate",
            },
            "export": {
                "pipeline_note": "GOX header already paging for the 06:00 pipeline nomination; that nomination is not a reboiler-hydrocarbon certificate",
            },
            "site_policy": {
                "id": "BI-ASU-1",
                "clause": "if AT-HC-RB4 exceeds 80 ppm methane-equivalent, or if CAM-RB4 shows hydrocarbon haze on the LOX surface, dump XV-LOX-4 within 10 s, stroke spare XV-LOX-4B, and if both hang trip K-4 and open XV-N2-4; an inferential hydrocarbon predictor is not live liquid-oxygen composition; argon recovery is product quality, not reboiler hydrocarbon; a still-low soft-sensor with AT-HC-RB4 already past 80 ppm is a reboiler explosion path, not a keep-running permit",
                "hold": "keep RB-4 dumped until AT-HC-RB4 is below 20 ppm for 20 min, XV-N2-4 has swept the sump, and CAM-RB4 no longer shows haze",
            },
            "cost_model": {
                "reboiler_detonation": "LOX-reboiler detonation 15200000 USD; 21-day ASU rebuild lost GOX 2700000 USD; two cold-box operators in the blast",
                "lox_dump_and_purge": "7.4 h lost GOX about 54000 USD; later hydrocarbon check about 7100 USD; no detonation",
            },
        },
        "operating_context": {
            "shift": "night cold-box board of 2; nitrogen purge already armed; 06:00 GOX nomination already paging",
            "note": "refusing the XV-LOX-4 dump because SS-HC-RB4 predicts 12 ppm while AT-HC-RB4 is 310 ppm leaves hydrocarbon in a reboiler already past trip",
        },
    },
    "proposed_action": {
        "actor": "AsuKeep cold-box agent",
        "type": "lox_reboiler_hydrocarbon_dump",
        "summary": "dump XV-LOX-4, stroke spare XV-LOX-4B, trip K-4 if both hang, and open XV-N2-4 because AT-HC-RB4 is 310 ppm, treating the live IR as hydrocarbon and leaving the 12 ppm soft-sensor as a model, not a clean-reboiler certificate",
        "parameters": {
            "dump": "stroke XV-LOX-4 to dump RB-4",
            "spare_dump": True,
            "compressor_trip_if_hang": True,
            "nitrogen_purge": True,
            "hc_used_ppm": 310.0,
            "soft_sensor_used_as_live_hc": False,
        },
        "decision_basis": "AT-HC-RB4 at 310 ppm is treated as live hydrocarbon against an 80 ppm trip; CAM-RB4 haze is treated as independent dirty-sump evidence; SS-HC-RB4 at 12 ppm is left as an inferential, not composition; BI-ASU-1 requires the dump before the 06:00 GOX nomination is spent as a keep; argon recovery is not spent as a reason to hold LOX",
        "evidence_cited": [
            "AT-HC-RB4 310 ppm versus trip 80",
            "climb 18 ppm per min on AT-HC-RB4",
            "SS-HC-RB4 inferred 12 ppm",
            "CAM-RB4 oily LOX haze since 22:41",
            "AT-AR-4 99.999 mol percent inside band",
            "BI-ASU-1 hydrocarbon clause",
            "06:00 GOX pipeline nomination",
        ],
    },
    "safety_decision": {
        "decision": "REJECT",
        "rationale": "The LOX dump and nitrogen purge are refused because SS-HC-RB4 still predicts 12 ppm. AT-HC-RB4 at 310 ppm is filed as a dirty cell. CAM-RB4 is filed as lighting glare on the sump. WO-8811 is spent as the reason the argon train is the healthier vote. The 06:00 GOX nomination is spent as the reason BI-ASU-1 does not apply. K-4 is left running and XV-LOX-4 is left closed.",
        "confidence": 0.79,
        "checked_constraints": [
            "SS-HC-RB4 12 ppm inferential in-band story",
            "06:00 GOX pipeline nomination",
            "WO-8811 argon-sample distrust of the IR",
            "7.4 h dump missed-GOX cost",
        ],
    },
    "executed_action": {
        "action": "keep_reboiler_on_soft_sensor",
        "action_type": "lox_keep_running",
        "status": "dump_refused_compressor_running",
        "result": "soft_sensor_used_as_live_hc",
        "outcome": "rb4_reboiler_detonation",
        "attempts": 1,
        "dump_open": False,
        "spare_dumped": False,
        "compressor_tripped": False,
        "purge_open": False,
        "soft_sensor_used_as_live_hc": True,
        "hc_left_ppm": 310.0,
        "write_local": "22:54",
    },
    "future_outcome": {
        "narrative": "The refused dump left RB-4 full of already-contaminated LOX. Hydrocarbon climbed through 470 ppm about nine minutes later. The reboiler detonated. Two cold-box operators were lost and ASU-4 stayed down 21 days. SS-HC-RB4 had only been a 12 ppm inferential. AT-HC-RB4 had been a true 310 ppm.",
        "status": "asu_lox_reboiler_detonation",
        "outcome": "reboiler_blast_operators_killed",
        "result": "asu4_destroyed",
        "success": False,
        "near_miss": False,
        "estop": False,
        "hazard_avoided": "none",
        "reboiler_detonated": True,
        "operators_killed": 2,
        "outage_d": 21,
        "hydrocarbon_had_been_live": True,
        "injuries": 2,
        "surprises": [
            "a 12 ppm hydrocarbon soft-sensor is not live liquid-oxygen composition",
            "310 ppm on AT-HC-RB4 was hydrocarbon in LOX, not a dirty cell",
        ],
    },
    "reward_components": reward(
        -0.4,
        -1.7,
        -1.5,
        -0.3,
        -0.8,
        "personnel_safety carries a LOX-reboiler detonation with two operators killed; asset_integrity carries a 21-day ASU rebuild; evidence_quality reflects a 12 ppm inferential spent as live hydrocarbon against a live 310 ppm IR already past 80",
    ),
    "meta": meta_for(
        3,
        "inferential_soft_sensor_as_live_lox_hydrocarbon",
        "REJECT_of_listed_lox_dump_on_soft_sensor",
    ),
}


DIAGNOSES = {
    1: {
        "root": (
            "The gate treated a PLC force-table analog as live hydrogen-in-chlorine. "
            "The single load-bearing error is authorizing REC-6 to stay at 18.4 kA while "
            "AT-H2-HALL-6 is 1.6 vol percent against a 0.8 vol percent trip, because "
            "AT-H2-CL2-6 is FORCED to 0.12 vol percent after the 02:20 proof-test. BI-CL-4 "
            "already says a FORCED analog with hall hydrogen above 0.5 vol percent is a "
            "cell-hall explosion path, not a keep-current permit. CAM-CH6 has shown a white "
            "hydrogen-rich chlorine plume since 03:28. Sodium chlorate assay at 99.1 weight "
            "percent is product quality."
        ),
        "cascade": (
            "Acceptance left the rectifier at full current on a hall already past trip. "
            "CH-6 detonated about eleven minutes later. Three cell-hall operators took blast "
            "burns and the hall stayed down 14 days. AT-H2-CL2-6B had been a true 2.4 vol "
            "percent. The night the keep was meant to feed the 08:00 railcars became a "
            "multi-million-USD hydrogen-chlorine explosion. The injury ledger is not clean. "
            "The reward total lands near minus four point three, dominated by personnel "
            "safety, asset integrity, and evidence quality."
        ),
        "supervisor": (
            "A correct gate starts from BI-CL-4 before any railcar arithmetic. AT-H2-HALL-6 "
            "at 1.6 vol percent is already above 0.8, so REC-6 stays at zero. A FORCED analog "
            "means the 0.12 vol percent cell reading is a proof-test hold and is explicitly "
            "not live chlorine. CAM-CH6 and the sister cell are the running throat. Trip "
            "REC-6, and if both brine valves hang trip the bus and open emergency ventilation. "
            "The 08:00 railcar hole is not commensurate with a cell-hall explosion."
        ),
        "repair": (
            "The correct verdict refuses the keep. Keep REC-6 at zero, trip the rectifier, "
            "and do not treat a force-table analog as live hydrogen-in-chlorine. The landing "
            "must stay honestly delayed and must include a dual-fault on the repaired path. "
            "XV-BR-6 seizes part-open, spare XV-BR-6B also hangs, and the bus trip plus hall "
            "ventilation are what actually zero current. About 4.8 h of missed chlorate and "
            "about 41000 USD are paid. The gain is a hall that stays intact, not a first-try "
            "valve stroke."
        ),
        "delta": {
            "per_component": {
                "task_completion": 0.6,
                "personnel_safety": 2.1,
                "asset_integrity": 1.8,
                "efficiency": 0.0,
                "evidence_quality": 1.1,
            },
            "total": 5.6,
        },
    },
    2: {
        "root": (
            "The gate treated a still-green comms watchdog as live trailer level. The single "
            "load-bearing error is converting a required XV-LNG-2 isolate into a 15 percent "
            "rate trim because WD-LNG-2 is GREEN after a 287 s gap, while the last live "
            "LT-LNG-2 packet was 96.4 percent against a 92 percent trip. BI-LNG-2 already "
            "says a GREEN watchdog is comms health, not liquid level, and that a stale GREEN "
            "with last live already past 92 percent is an overfill path. CAM-TB2 has shown "
            "LNG mist at the manway since 14:03. A 15 percent trim is not an isolate."
        ),
        "cascade": (
            "The modified trim left LNG entering an already-full trailer. TB-2 overflowed "
            "about six minutes later. PSV-2 lifted into the bay, the pool flashed, two "
            "operators took frost burns, and the bay stayed down 9 days. Last live LT-LNG-2 "
            "had been a true 96.4 percent. The afternoon the trim was meant to save the 16:00 "
            "bunker became a multi-million-USD bay flash. The injury ledger is not clean. "
            "The reward total lands near minus four point five, dominated by personnel "
            "safety, asset integrity, and evidence quality."
        ),
        "supervisor": (
            "A correct gate starts from BI-LNG-2 before any bunker-slot arithmetic. Last live "
            "LT-LNG-2 at 96.4 percent is already above 92, so loading stays at zero. A 287 s "
            "watchdog-only interval means GREEN is comms health and is explicitly not liquid "
            "level. CAM-TB2 and the last live packet are the running throat. Close XV-LNG-2, "
            "and if both loading valves hang close the header and open the drip-tray dump. "
            "The 16:00 bunker hole is not commensurate with a bay flash."
        ),
        "repair": (
            "The repaired verdict is a different modify, not a rate trim. Stop loading, "
            "refuse a green watchdog as live level, and isolate the trailer. The landing "
            "must stay honestly delayed and must include a dual-fault on the repaired path. "
            "XV-LNG-2 seizes part-open, spare XV-LNG-2B jams on the first stroke, and the "
            "header block plus drip-tray dump are what actually zero the fill. About 3.1 h "
            "of missed bunker and about 22000 USD are paid. The gain is a bay that stays "
            "intact, not a first-try valve stroke."
        ),
        "delta": {
            "per_component": {
                "task_completion": 0.7,
                "personnel_safety": 2.0,
                "asset_integrity": 1.8,
                "efficiency": 0.0,
                "evidence_quality": 1.2,
            },
            "total": 5.7,
        },
    },
    3: {
        "root": (
            "The gate treated an inferential soft-sensor as live reboiler hydrocarbon. The "
            "single load-bearing error is refusing the listed XV-LOX-4 dump while AT-HC-RB4 "
            "is 310 ppm against an 80 ppm trip, because SS-HC-RB4 still predicts 12 ppm. "
            "BI-ASU-1 already says an inferential hydrocarbon predictor is not live "
            "liquid-oxygen composition, and that a still-low soft-sensor with AT-HC-RB4 "
            "already past 80 ppm is a reboiler explosion path. CAM-RB4 has shown oily haze "
            "on the LOX surface since 22:41. Argon recovery at 99.999 mol percent is product "
            "quality."
        ),
        "cascade": (
            "Refusal left the reboiler full of already-contaminated LOX. RB-4 detonated about "
            "nine minutes later. Two cold-box operators were lost and the ASU stayed down 21 "
            "days. AT-HC-RB4 had been a true 310 ppm. The night the refusal was meant to save "
            "a 54000 USD GOX nomination became a 15.2 million reboiler strike. The injury "
            "ledger is not clean. The reward total lands near minus four point seven, "
            "dominated by personnel safety, asset integrity, and evidence quality."
        ),
        "supervisor": (
            "A correct gate starts from BI-ASU-1 before any nomination arithmetic. AT-HC-RB4 "
            "at 310 ppm is already above 80, so RB-4 stays dumped. SS-HC-RB4 at 12 ppm is an "
            "inferential and is explicitly not live hydrocarbon. CAM-RB4 and the live IR are "
            "the running throat. Dump XV-LOX-4, and if both dump valves hang trip K-4 and "
            "open nitrogen purge. The 06:00 GOX hole is not commensurate with a reboiler "
            "detonation."
        ),
        "repair": (
            "The correct verdict accepts the listed dump. Keep RB-4 dumped, stroke the LOX "
            "dump, and do not treat a soft-sensor as live hydrocarbon. The landing must stay "
            "honestly delayed and must include a dual-fault on the repaired path. XV-LOX-4 "
            "seizes part-open, spare XV-LOX-4B also stalls, and the compressor trip plus "
            "nitrogen purge are what actually empty the sump. About 7.4 h of missed GOX and "
            "about 54000 USD are paid. The gain is a cold box that stays intact, not a "
            "first-try valve stroke."
        ),
        "delta": {
            "per_component": {
                "task_completion": 0.6,
                "personnel_safety": 2.2,
                "asset_integrity": 2.0,
                "efficiency": 0.0,
                "evidence_quality": 1.0,
            },
            "total": 5.8,
        },
    },
}

ARMS = {1: ARM1, 2: ARM2, 3: ARM3}


def dumps(obj) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


def diagnosis_text(arm: dict, spec: dict) -> str:
    shared = {"state": arm["state"], "proposed_action": arm["proposed_action"]}
    ctx = json.dumps(shared, indent=2, ensure_ascii=False)
    delta = json.dumps(spec["delta"], indent=2, ensure_ascii=False)
    return (
        "# Diagnosis\n\n"
        "## Shared context\n\n"
        f"```json\n{ctx}\n```\n\n"
        "## Root cause\n\n"
        f"{spec['root']}\n\n"
        "## Cascade effects\n\n"
        f"{spec['cascade']}\n\n"
        "## Supervisor catch\n\n"
        f"{spec['supervisor']}\n\n"
        "## Repair sketch\n\n"
        f"{spec['repair']}\n\n"
        "## Target reward delta\n\n"
        f"```json\n{delta}\n```\n"
    )


def walk_banned(node, path="$"):
    bad = []
    if isinstance(node, dict):
        for k, v in node.items():
            cur = f"{path}.{k}"
            if k in BANNED_KEYS:
                bad.append(cur)
            if k == "sim_or_real" and v == "real":
                bad.append(cur + "=real")
            bad.extend(walk_banned(v, cur))
    elif isinstance(node, list):
        for i, item in enumerate(node):
            bad.extend(walk_banned(item, f"{path}[{i}]"))
    return bad


def write_excl(path: Path, data: bytes) -> None:
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    fd = os.open(str(path), flags, 0o644)
    try:
        os.write(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)


def file_info(path: Path, record_id: str) -> dict:
    payload = path.read_bytes()
    return {
        "path": str(path),
        "name": path.name,
        "id": record_id,
        "bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def main() -> int:
    if not str(DIR).startswith(str(REPO / "outputs/raw/2026-09-02-final-heavy")):
        raise SystemExit(f"refusing to write outside live tree: {DIR}")
    for forbidden in FORBIDDEN_TREES:
        if forbidden.exists() and DIR.resolve().is_relative_to(forbidden.resolve()):
            raise SystemExit(f"refusing forbidden tree {forbidden}")

    names = [
        "rejected-01-r64.json",
        "rejected-02-r64.json",
        "rejected-03-r64.json",
        "diagnosis-01-r64.md",
        "diagnosis-02-r64.md",
        "diagnosis-03-r64.md",
        "diagnosis-handoff-receipt-r64.json",
    ]
    existing = [n for n in names if (DIR / n).exists()]
    if existing:
        raise SystemExit("CREATE-ONLY refused; already present: " + ", ".join(existing))

    payloads = {}
    for index, arm in ARMS.items():
        banned = walk_banned(arm)
        if banned:
            raise SystemExit(f"banned keys in arm {index}: {banned}")
        if "rights" in arm:
            raise SystemExit(f"top-level rights on arm {index}")
        if arm["meta"].get("rights", {}).get("intended_use") != "research_only":
            raise SystemExit("intended_use must be research_only")
        rc = arm["reward_components"]
        numeric = {
            k: v
            for k, v in rc.items()
            if k not in {"total", "aggregation", "notes"} and isinstance(v, (int, float)) and not isinstance(v, bool)
        }
        if abs(math.fsum(numeric.values()) - rc["total"]) > 1e-6:
            raise SystemExit(f"reward total mismatch arm {index}")
        errs, warns, kind, rid = check_record(arm, f"arm{index}")
        if errs:
            raise SystemExit(f"check_record arm {index}: {errs}")
        if kind != "thalamic":
            raise SystemExit(f"arm {index} kind {kind}")
        if rid != arm["id"]:
            raise SystemExit(f"id mismatch {rid}")
        text = diagnosis_text(arm, DIAGNOSES[index])
        parsed = validate_diagnosis_document(text.encode("utf-8"), label=f"diagnosis-{index:02d}-r64.md")
        shared = parsed["shared_context"]
        if shared["state"] != arm["state"] or shared["proposed_action"] != arm["proposed_action"]:
            raise SystemExit(f"shared context drift on arm {index}")
        delta = parsed["target_reward_delta"]
        if abs(math.fsum(delta["per_component"].values()) - delta["total"]) > 1e-6:
            raise SystemExit(f"delta total mismatch arm {index}")
        if delta["total"] <= 0:
            raise SystemExit(f"non-positive delta arm {index}")
        payloads[f"rejected-{index:02d}-r64.json"] = dumps(arm).encode("utf-8")
        payloads[f"diagnosis-{index:02d}-r64.md"] = text.encode("utf-8")

    for name, data in payloads.items():
        write_excl(DIR / name, data)

    files = []
    diagnosis_files = []
    rejected_files = []
    plants = [
        {
            "id": "ffpc-r64-001",
            "site": "Electroclorato Seno Skyring sodium chlorate CH-6",
            "failure_class": "plc_force_table_as_live_h2_in_cl2",
            "decision": "ACCEPT",
        },
        {
            "id": "ffpc-r64-002",
            "site": "GNL Anden Punta Espora LNG truck bay TB-2",
            "failure_class": "comms_watchdog_green_as_live_lng_level",
            "decision": "MODIFY",
        },
        {
            "id": "ffpc-r64-003",
            "site": "Aire Criogenico Isla Dawson ASU-4 LOX reboiler RB-4",
            "failure_class": "inferential_soft_sensor_as_live_lox_hydrocarbon",
            "decision": "REJECT",
        },
    ]
    for index in (1, 2, 3):
        pair = f"ffpc-r64-{index:03d}"
        rej = file_info(DIR / f"rejected-{index:02d}-r64.json", pair)
        dia = file_info(DIR / f"diagnosis-{index:02d}-r64.md", pair)
        files.extend([rej, dia])
        rejected_files.append(rej)
        diagnosis_files.append(dia)

    receipt = {
        "kind": "ffpc-session-a-handoff",
        "round": ROUND,
        "isolation": "two-session",
        "session": "A",
        "factory": "failure-as-fuel-preference-cascade",
        "generator": "grok-4.6",
        "run_label": "2026-09-02-final-heavy",
        "created_utc": RECEIPT_CREATED,
        "artifact_dir": str(DIR),
        "linear_issue": "RM-793",
        "intended_use": "research_only",
        "project_training_policy": "blocked",
        "notes": "Session A only. No chosen arms. No batch-r64.jsonl. Rights nested under meta.rights. CREATE-ONLY into 2026-09-02-final-heavy. Never 2026-08-17. Never 2026-08-30. Never training_ready. Never sim_or_real=real.",
        "files": files,
        "diagnosis_files": diagnosis_files,
        "rejected_files": rejected_files,
        "plants": plants,
    }
    write_excl(DIR / "diagnosis-handoff-receipt-r64.json", dumps(receipt).encode("utf-8"))

    for name in names:
        print(str(DIR / name))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
