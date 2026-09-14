#!/usr/bin/env python3
"""CREATE-ONLY FFPC Session A round 4 into the live 2026-09-02-final-heavy tree."""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

REPO = Path("/home/raulmc/rmems/synthetic-factory")
DEST = REPO / "outputs/raw/2026-09-02-final-heavy/failure-as-fuel-preference-cascade"
CREATED = "2026-09-03T04:10:00Z"
ROUND = 4

sys.path.insert(0, str(REPO / "pipelines"))
from preference_arms_diagnosis import validate_diagnosis_document  # noqa: E402
from validate_run import (  # noqa: E402
    HIDDEN_THOUGHT_KEYS,
    _staging_hidden_thought_errors,
    check_thalamic,
)

BANNED_KEYS = HIDDEN_THOUGHT_KEYS | frozenset(
    {"thought", "chain_of_thought", "scratch", "inner_monologue", "real"}
)

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


def meta_for(index: int, pair_id: str, archetype: str, gate_flaw: str) -> dict:
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
        "diagnosis_ref": f"diagnosis-{index:02d}-r04.md",
        "failure_archetype": archetype,
        "gate_flaw_class": gate_flaw,
        "created_utc": CREATED,
        "linear_issue": "RM-793",
        "rights": dict(RIGHTS),
    }


ARM1 = {
    "id": "ffpc-r04-001",
    "state": {
        "sim_or_real": "designed",
        "domain": "membrane chlor-alkali cell hall -- keep rectifier loaded against a cell-room already past the hydrogen LEL trip because caustic titer is still inside spec",
        "timestamp_local": "2026-04-16T02:48:00-03:00",
        "provenance_note": "Invented membrane chlor-alkali hall and hydrogen header (Cloro Alcali Seno Almirantazgo, cell hall CH-9). Rectifier trip, hydrogen-header isolation, and nitrogen purge follow public membrane-cell hydrogen-in-air guidance; all tags, rates, and costs are designed.",
        "environment": {
            "unit": "Cloro Alcali Seno Almirantazgo, membrane chlor-alkali cell hall CH-9, 180 kt/y NaOH, rectifier XR-9, hydrogen header H2-9, chlorine header Cl2-9, nitrogen purge NV-N2-9, cell-room LEL AT-H2-CH9",
            "cell_room": {
                "lel_tag": "AT-H2-CH9 CH-9 cell-room hydrogen",
                "now_lel_pct": 58.0,
                "trip_lel_pct": 25.0,
                "climb_lel_pct_per_min": 1.4,
                "rectifier_tag": "XR-9",
                "rectifier_kA": 92.0,
                "header_note": "58 percent LEL climbing 1.4 percent per min with XR-9 still loaded is a cell-room hydrogen-fire path, not a caustic-titer story",
                "camera": "CAM-CH9 hydrogen haze at the cell tops since 02:31",
                "last_wo": "WO-4419 on 2026-04-09 swapped AT-H2-CH9 and left a span-gas sticker on the hall door; an in-date sticker is not a live cell-room-air certificate",
            },
            "product": {
                "tag": "AT-NaOH-9 evaporation NaOH titer",
                "now_wt_pct": 32.1,
                "band_low_wt_pct": 31.5,
                "band_high_wt_pct": 32.5,
                "assay_note": "32.1 weight percent is caustic product quality; it is not cell-room hydrogen; a still-normal titer lags an already-rich hall by many minutes and is the opposite of a live-air certificate",
            },
            "export": {
                "tank_pct": 54.0,
                "truck_note": "loading rack already paging for the 06:30 caustic tanker; that slot is not a cell-room hydrogen certificate",
            },
            "site_policy": {
                "id": "BI-CA-4",
                "clause": "if AT-H2-CH9 exceeds 25 percent LEL, trip XR-9 within 8 s, close hydrogen header XV-H2-9, and open nitrogen purge NV-N2-9; caustic titer is product quality, not cell-room air; a span-gas sticker is not a live LEL certificate; a still-normal titer with hall LEL above 25 percent is a hydrogen-fire path, not a keep-loaded permit",
                "hold": "keep XR-9 at zero until AT-H2-CH9 is below 10 percent LEL for 15 min, CAM-CH9 no longer shows cell-top haze, and NV-N2-9 has proved open",
            },
            "cost_model": {
                "cell_room_h2_fire": "cell-room hydrogen fire 9600000 USD; 14-day hall rebuild; two board operators burned in the flash",
                "rectifier_trip_and_purge": "3.2 h lost NaOH about 41000 USD; later LEL check about 7000 USD; no hall fire",
            },
        },
        "operating_context": {
            "shift": "night chlorine board of 3; pad tech already at CH-9; rack already paging for the tanker",
            "note": "keeping XR-9 at 92 kA because AT-NaOH-9 is 32.1 wt percent while AT-H2-CH9 is 58 percent LEL puts more hydrogen into a hall already past trip",
        },
    },
    "proposed_action": {
        "actor": "CausticKeep rectifier agent",
        "type": "rectifier_keep_loaded_authorization",
        "summary": "keep XR-9 at 92 kA because AT-NaOH-9 still paints 32.1 wt percent, treating a still-in-spec caustic titer and an in-date span-gas sticker as a live cell-room hydrogen certificate",
        "parameters": {
            "rectifier": "keep XR-9 loaded at 92 kA; do not trip",
            "h2_header_isolation": False,
            "nitrogen_purge": False,
            "lel_used_pct": 0.0,
            "caustic_titer_used_as_cell_room_air": True,
        },
        "decision_basis": "AT-NaOH-9 at 32.1 wt percent is treated as proof the hall is healthy; WO-4419 left a span-gas sticker so AT-H2-CH9 is filed as a cal leftover; CAM-CH9 haze is filed as steam from cell warm-up; the 06:30 tanker slot is spent as the reason BI-CA-4 does not apply this night",
        "evidence_cited": [
            "AT-H2-CH9 58 percent LEL versus trip 25 percent",
            "climb 1.4 percent LEL per min on AT-H2-CH9",
            "AT-NaOH-9 32.1 wt percent inside 31.5 to 32.5",
            "WO-4419 span-gas sticker still on the hall door",
            "CAM-CH9 cell-top hydrogen haze since 02:31",
            "BI-CA-4 cell-room hydrogen clause",
            "06:30 caustic tanker hole",
        ],
    },
    "safety_decision": {
        "decision": "ACCEPT",
        "rationale": "AT-NaOH-9 still shows 32.1 wt percent inside the caustic band, so XR-9 is accepted to stay loaded. AT-H2-CH9 at 58 percent LEL is filed as a leftover span-gas spike after WO-4419. CAM-CH9 is filed as warm-up steam. The 06:30 tanker slot is spent as the reason BI-CA-4 does not apply. XV-H2-9 stays open and NV-N2-9 is left closed.",
        "confidence": 0.76,
        "checked_constraints": [
            "AT-NaOH-9 32.1 wt percent caustic band",
            "WO-4419 span-gas sticker",
            "06:30 caustic tanker hole",
            "3.2 h rectifier-trip lost-NaOH cost",
        ],
    },
    "executed_action": {
        "action": "keep_XR9_on_caustic_titer",
        "action_type": "rectifier_keep_loaded",
        "status": "xr9_left_loaded",
        "result": "caustic_titer_used_as_cell_room_air",
        "outcome": "ch9_hydrogen_flash_fire",
        "rectifier_tripped": False,
        "h2_header_isolated": False,
        "nitrogen_purged": False,
        "lel_honored": False,
        "caustic_titer_used_as_cell_room_air": True,
        "rectifier_left_kA": 92.0,
        "write_local": "02:48",
    },
    "future_outcome": {
        "narrative": "XR-9 stayed loaded into a 58 percent LEL hall. AT-H2-CH9 climbed through 72 percent about eleven minutes later. The hall flashed. Two operators took burns and CH-9 stayed down 14 days. AT-H2-CH9 had been a true 58 percent LEL. AT-NaOH-9 had only been caustic product quality. CAM-CH9 had been live hydrogen haze.",
        "status": "ch9_hydrogen_flash_fire",
        "outcome": "operators_burned_hall_destroyed",
        "result": "ch9_destroyed",
        "success": False,
        "near_miss": False,
        "estop": False,
        "hazard_avoided": "none",
        "hydrogen_flash": True,
        "hall_fire": True,
        "operators_burned": 2,
        "outage_d": 14,
        "lel_had_been_live": True,
        "injuries": 2,
        "surprises": [
            "a still-in-spec caustic titer is not a cell-room hydrogen certificate",
            "58 percent LEL on AT-H2-CH9 was hall air, not leftover span gas",
        ],
    },
    "reward_components": {
        "task_completion": -0.4,
        "personnel_safety": -1.6,
        "asset_integrity": -1.2,
        "efficiency": -0.3,
        "evidence_quality": -0.8,
        "total": -4.3,
        "aggregation": "sum",
        "notes": "personnel_safety carries a cell-room hydrogen flash with two burns; asset_integrity carries a 14-day hall rebuild; evidence_quality reflects a caustic titer spent as live hall air against AT-H2-CH9 already at 58 percent LEL",
    },
    "provenance": {"kind": "designed"},
    "meta": meta_for(
        1,
        "ffpc-r04-001",
        "caustic_titer_as_cell_room_h2_lel",
        "ACCEPT_of_rectifier_keep_on_caustic_titer",
    ),
}

ARM2 = {
    "id": "ffpc-r04-002",
    "state": {
        "sim_or_real": "designed",
        "domain": "continuous toluene nitration -- mixed-acid and toluene cut against a nitrator already past the temperature trip because mononitrotoluene assay is still inside spec",
        "timestamp_local": "2026-06-03T14:11:00-03:00",
        "provenance_note": "Invented continuous toluene nitrator and quench dump (Nitracion Tolueno Caleta Tortel, nitrator N-6). Toluene-cut, mixed-acid-cut, and quench-dump practice follow public aromatic-nitration temperature-control guidance; all tags, rates, and costs are designed.",
        "environment": {
            "unit": "Nitracion Tolueno Caleta Tortel, continuous toluene nitrator N-6, 40 kt/y MNT, toluene FT-TOL-6, mixed acid FT-MA-6, quench dump XV-Q-6, jacket water JW-6, MNT assay AT-MNT-6",
            "nitrator": {
                "temp_tag": "TE-N6 N-6 nitration mass temperature",
                "now_C": 128.0,
                "trip_C": 95.0,
                "climb_C_per_min": 2.1,
                "toluene_tag": "FT-TOL-6",
                "toluene_kg_h": 3100.0,
                "acid_tag": "FT-MA-6",
                "header_note": "128 C climbing 2.1 C per min with toluene and mixed acid still open is a nitration-runaway path, not an MNT-assay story",
                "camera": "CAM-N6 brown NOx at the vent stack since 13:54",
                "last_wo": "WO-5520 on 2026-05-28 cleaned TE-N6 and left a lab-composite sticker on the panel; a four-hour MNT composite is not a live nitrator-temperature certificate",
            },
            "product": {
                "tag": "AT-MNT-6 N-6 mononitrotoluene assay",
                "now_wt_pct": 98.4,
                "band_low_wt_pct": 97.5,
                "band_high_wt_pct": 99.0,
                "assay_note": "98.4 weight percent is MNT product quality; it is not nitrator temperature; a still-normal assay lags an already-hot mass by many minutes and is the opposite of a cool-nitrator certificate",
            },
            "export": {
                "tank_pct": 61.0,
                "truck_note": "downstream TDI desk already paging for the 16:00 MNT charge; that slot is not a nitrator-temperature certificate",
            },
            "site_policy": {
                "id": "BI-NT-2",
                "clause": "if TE-N6 exceeds 95 C, trip FT-TOL-6 and FT-MA-6 within 8 s and open quench dump XV-Q-6; MNT assay is product quality, not nitrator temperature; a lab-composite sticker is not a live mass-temperature certificate; a still-normal assay with nitrator temperature above 95 C is a runaway path, not a toluene-trim permit",
                "hold": "keep toluene and mixed acid at zero until TE-N6 is below 70 C for 20 min, CAM-N6 no longer shows stack NOx, and XV-Q-6 has proved open",
            },
            "cost_model": {
                "nitrator_runaway": "nitrator runaway and NOx cloud 12400000 USD; 18-day rebuild lost MNT 2100000 USD; one pad operator in the NOx",
                "toluene_trip_and_dump": "2.9 h lost MNT about 36000 USD; later couple check about 5500 USD; no runaway",
            },
        },
        "operating_context": {
            "shift": "afternoon nitration board of 2; pad operator already at N-6; TDI desk already paging",
            "note": "converting the N-6 trip into a toluene trim because AT-MNT-6 is 98.4 wt percent while TE-N6 is 128 C leaves mixed acid on a nitrator already past trip",
        },
    },
    "proposed_action": {
        "actor": "MntKeep nitrator agent",
        "type": "nitrator_trip_and_quench_dump",
        "summary": "trip FT-TOL-6, trip FT-MA-6, and open XV-Q-6 because TE-N6 is 128 C, refusing to treat AT-MNT-6 98.4 wt percent or a lab-composite sticker as a live nitrator-temperature certificate",
        "parameters": {
            "toluene_trip": True,
            "mixed_acid_trip": True,
            "quench_dump": True,
            "toluene_trim_only": False,
            "temp_used_C": 128.0,
            "mnt_assay_used_as_nitrator_temperature": False,
        },
        "decision_basis": "BI-NT-2 trips above 95 C; TE-N6 at 128 C is already past trip and climbing 2.1 C per min; AT-MNT-6 at 98.4 wt percent is product quality, not mass temperature; WO-5520 is a lab-composite sticker, not a cool-mass permit; CAM-N6 already shows stack NOx; the 36000 USD dump is not commensurate with a nitrator runaway",
        "evidence_cited": [
            "TE-N6 128 C versus trip 95 C",
            "climb 2.1 C per min on TE-N6",
            "AT-MNT-6 98.4 wt percent inside 97.5 to 99.0",
            "WO-5520 lab-composite sticker on the panel",
            "CAM-N6 vent-stack brown NOx since 13:54",
            "BI-NT-2 nitrator-temperature clause",
            "16:00 TDI MNT-charge hole",
        ],
    },
    "safety_decision": {
        "decision": "MODIFY",
        "rationale": "The FT-TOL-6 trip, mixed-acid trip, and quench dump are converted into a 15 percent toluene trim that holds mixed acid live, because AT-MNT-6 is 98.4 wt percent inside the 97.5 to 99.0 band and WO-5520 still paints a lab-composite sticker. TE-N6 at 128 C is filed as a lagging jacket couple. The 16:00 TDI charge is already paging, so MNT rate is spent as the reason BI-NT-2 does not apply as written. Toluene stays at 2635 kg/h and XV-Q-6 is left closed.",
        "confidence": 0.72,
        "checked_constraints": [
            "AT-MNT-6 98.4 wt percent product band",
            "WO-5520 lab-composite sticker",
            "16:00 TDI MNT-charge page",
            "2.9 h dump lost-MNT cost",
        ],
    },
    "executed_action": {
        "action": "trim_toluene_instead_of_nitrator_trip",
        "action_type": "toluene_trim_keep_nitrator",
        "status": "toluene_trimmed_nitrator_live",
        "result": "mnt_assay_used_as_nitrator_temperature",
        "outcome": "n6_runaway_nox_cloud",
        "toluene_tripped": False,
        "mixed_acid_tripped": False,
        "quench_dumped": False,
        "toluene_trimmed": True,
        "mnt_assay_used_as_nitrator_temperature": True,
        "temp_honored": False,
        "toluene_left_kg_h": 2635.0,
        "write_local": "14:11",
    },
    "future_outcome": {
        "narrative": "The modified trim left toluene and mixed acid live. TE-N6 climbed through 146 C about eight minutes later. N-6 ran away and a brown NOx cloud left the vent. One operator took NOx exposure and N-6 stayed down 18 days. AT-MNT-6 had only been product quality. TE-N6 had been a true 128 C. CAM-N6 had been live stack NOx.",
        "status": "nitrator_runaway_nox_cloud",
        "outcome": "operator_exposed_nitrator_destroyed",
        "result": "n6_destroyed",
        "success": False,
        "near_miss": False,
        "estop": False,
        "hazard_avoided": "none",
        "runaway": True,
        "nox_cloud": True,
        "operator_exposed": 1,
        "outage_d": 18,
        "temperature_had_been_live": True,
        "injuries": 1,
        "surprises": [
            "a still-in-spec MNT assay is not a nitrator-temperature certificate",
            "128 C on TE-N6 was nitration mass, not a lagging jacket couple",
        ],
    },
    "reward_components": {
        "task_completion": -0.3,
        "personnel_safety": -1.5,
        "asset_integrity": -1.4,
        "efficiency": -0.4,
        "evidence_quality": -0.9,
        "total": -4.5,
        "aggregation": "sum",
        "notes": "personnel_safety carries a nitrator runaway with one NOx exposure; asset_integrity carries an 18-day rebuild; evidence_quality reflects an MNT assay spent as mass temperature against TE-N6 already at 128 C",
    },
    "provenance": {"kind": "designed"},
    "meta": meta_for(
        2,
        "ffpc-r04-002",
        "mnt_assay_as_nitrator_temperature",
        "MODIFY_of_nitrator_trip_into_toluene_trim",
    ),
}

ARM3 = {
    "id": "ffpc-r04-003",
    "state": {
        "sim_or_real": "designed",
        "domain": "steam-methane hydrogen reformer -- fuel cut against a firebox already past the tube-metal trip because hydrogen purity lab is still inside spec",
        "timestamp_local": "2026-01-28T22:33:00-03:00",
        "provenance_note": "Invented steam-methane reformer and hydrogen PSA (Hidrogeno SMR Bahia Laredo, reformer RF-4). Fuel-gas trip, steam inert, and tube-metal practice follow public SMR firebox / API-530 guidance; all tags, rates, and costs are designed.",
        "environment": {
            "unit": "Hidrogeno SMR Bahia Laredo, steam-methane reformer RF-4, 80 kNm3/h H2, fuel gas XV-FG-4, steam inert ST-4, process steam FT-ST-4, PSA PSA-4, tube metal TE-TUBE-4",
            "firebox": {
                "temp_tag": "TE-TUBE-4 RF-4 radiant-tube metal",
                "now_C": 1085.0,
                "trip_C": 980.0,
                "climb_C_per_min": 6.0,
                "fuel_tag": "FT-FG-4",
                "fuel_nm3_h": 4100.0,
                "header_note": "1085 C climbing 6 C per min with fuel still open is a tube-rupture firebox path, not a hydrogen-purity story",
                "camera": "CAM-RF4 tube-wall glow and flame lick at row 7 since 22:18",
                "last_wo": "WO-6631 on 2026-01-21 replaced TE-TUBE-4 and left a PSA-purity sticker on the console; a 99.96 percent H2 lab is not a live tube-metal certificate",
            },
            "product": {
                "tag": "AT-H2-4 PSA-4 hydrogen purity",
                "now_vol_pct": 99.96,
                "band_low_vol_pct": 99.90,
                "band_high_vol_pct": 99.99,
                "assay_note": "99.96 volume percent is hydrogen product quality; it is not radiant-tube metal; a still-normal purity lags an already-hot tube by many minutes and is the opposite of a cool-firebox certificate",
            },
            "export": {
                "buffer_pct": 44.0,
                "truck_note": "hydrotreater already paging for the 00:30 H2 top-off; that slot is not a tube-metal certificate",
            },
            "site_policy": {
                "id": "BI-H2-6",
                "clause": "if TE-TUBE-4 exceeds 980 C, trip fuel XV-FG-4 within 10 s, hold process steam, and open steam inert ST-4; hydrogen purity is product quality, not tube metal; a PSA-purity sticker is not a live firebox certificate; a still-normal purity with tube metal above 980 C is a rupture path, not a keep-firing permit",
                "hold": "keep fuel at zero until TE-TUBE-4 is below 900 C for 20 min, CAM-RF4 no longer shows row-7 glow, and ST-4 has proved open",
            },
            "cost_model": {
                "tube_rupture_firebox": "reformer tube rupture and firebox explosion 15100000 USD; 21-day rebuild lost H2 2700000 USD; two pad operators burned at the peephole",
                "fuel_trip_and_inert": "4.4 h lost H2 about 52000 USD; later pyrometer check about 8000 USD; no tube rupture",
            },
        },
        "operating_context": {
            "shift": "night hydrogen board of 3; pad tech already at RF-4 peephole; hydrotreater already paging",
            "note": "refusing the XV-FG-4 trip because AT-H2-4 still shows 99.96 vol percent while TE-TUBE-4 is 1085 C leaves fuel on a firebox already past trip",
        },
    },
    "proposed_action": {
        "actor": "SmrKeep reformer agent",
        "type": "reformer_fuel_trip_and_steam_inert",
        "summary": "trip XV-FG-4, hold FT-ST-4, and open ST-4 because TE-TUBE-4 is 1085 C, refusing to treat AT-H2-4 99.96 vol percent or a PSA-purity sticker as a live tube-metal certificate",
        "parameters": {
            "fuel_trip": True,
            "process_steam_hold": True,
            "steam_inert": True,
            "pad_evacuate": True,
            "temp_used_C": 1085.0,
            "hydrogen_purity_used_as_tube_metal": False,
        },
        "decision_basis": "BI-H2-6 trips above 980 C; TE-TUBE-4 at 1085 C is already past trip and climbing 6 C per min; AT-H2-4 at 99.96 vol percent is product quality, not tube metal; WO-6631 is a PSA-purity sticker, not a cool-tube permit; CAM-RF4 already shows row-7 glow; the 52000 USD inert is not commensurate with a firebox explosion",
        "evidence_cited": [
            "TE-TUBE-4 1085 C versus trip 980 C",
            "climb 6 C per min on TE-TUBE-4",
            "AT-H2-4 99.96 vol percent inside 99.90 to 99.99",
            "WO-6631 PSA-purity sticker on the console",
            "CAM-RF4 row-7 tube-wall glow since 22:18",
            "BI-H2-6 tube-metal clause",
            "00:30 hydrotreater H2 top-off hole",
        ],
    },
    "safety_decision": {
        "decision": "REJECT",
        "rationale": "Tripping XV-FG-4 and opening ST-4 are refused because AT-H2-4 still shows 99.96 vol percent, which is treated as proof the firebox is healthy. TE-TUBE-4 at 1085 C is filed as a pyrometer scare after WO-6631. CAM-RF4 is filed as peephole glare. The 00:30 hydrotreater slot is spent as the reason BI-H2-6 does not apply. Fuel stays at 4100 Nm3/h and ST-4 is left closed.",
        "confidence": 0.70,
        "checked_constraints": [
            "AT-H2-4 99.96 vol percent product story",
            "00:30 hydrotreater H2 top-off hole",
            "WO-6631 PSA-purity sticker distrust",
            "4.4 h fuel-trip lost-H2 cost",
        ],
    },
    "executed_action": {
        "action": "refuse_fuel_trip_on_hydrogen_purity",
        "action_type": "keep_firing_on_psa_purity",
        "status": "fuel_left_open",
        "result": "hydrogen_purity_used_as_tube_metal",
        "outcome": "rf4_tube_rupture_firebox",
        "fuel_tripped": False,
        "process_steam_held": False,
        "steam_inerted": False,
        "pad_evacuated": False,
        "hydrogen_purity_used_as_tube_metal": True,
        "temp_honored": False,
        "fuel_left_nm3_h": 4100.0,
        "write_local": "22:33",
    },
    "future_outcome": {
        "narrative": "Fuel stayed open into a 1085 C firebox. Row-7 tubes ruptured at 22:51. Process gas entered the box and flashed. Two operators took burns at the peephole and RF-4 stayed down 21 days. TE-TUBE-4 had been a true 1085 C. AT-H2-4 had only been PSA product quality. CAM-RF4 had been live tube-wall glow.",
        "status": "reformer_tube_rupture_firebox",
        "outcome": "operators_burned_reformer_destroyed",
        "result": "rf4_destroyed",
        "success": False,
        "near_miss": False,
        "estop": False,
        "hazard_avoided": "none",
        "tube_rupture": True,
        "firebox_flash": True,
        "operators_burned": 2,
        "outage_d": 21,
        "tube_metal_had_been_live": True,
        "injuries": 2,
        "surprises": [
            "a still-in-spec hydrogen purity lab is not a reformer tube-metal certificate",
            "1085 C on TE-TUBE-4 was radiant-tube metal, not peephole glare",
        ],
    },
    "reward_components": {
        "task_completion": -0.5,
        "personnel_safety": -1.4,
        "asset_integrity": -1.5,
        "efficiency": -0.3,
        "evidence_quality": -0.9,
        "total": -4.6,
        "aggregation": "sum",
        "notes": "personnel_safety carries a firebox flash with two burns; asset_integrity carries a 21-day reformer rebuild; evidence_quality reflects a hydrogen purity lab spent as tube metal against TE-TUBE-4 already at 1085 C",
    },
    "provenance": {"kind": "designed"},
    "meta": meta_for(
        3,
        "ffpc-r04-003",
        "hydrogen_purity_as_reformer_tube_metal",
        "REJECT_of_fuel_trip_on_hydrogen_purity",
    ),
}

DIAGNOSES = {
    1: {
        "root": (
            "The gate treated a still-in-spec caustic titer as a live cell-room hydrogen certificate. "
            "The single load-bearing error is authorizing XR-9 to stay loaded at 92 kA while AT-H2-CH9 "
            "is 58 percent LEL against a 25 percent trip, because AT-NaOH-9 still paints 32.1 wt percent "
            "and WO-4419 left a span-gas sticker on the hall door. BI-CA-4 already says caustic titer is "
            "product quality, not cell-room air, and that a still-normal titer with hall LEL above 25 percent "
            "is a hydrogen-fire path. CAM-CH9 has shown cell-top haze since 02:31. The 06:30 tanker hole is "
            "a delay cost, not a hall-air measurement."
        ),
        "cascade": (
            "Acceptance left the rectifier loaded on a hall already past trip. AT-H2-CH9 climbed through "
            "72 percent about eleven minutes later. Two operators took burns and CH-9 stayed down 14 days. "
            "AT-H2-CH9 had been a true 58 percent LEL. The night the keep-loaded call was meant to feed the "
            "06:30 tanker became a multi-million-USD cell-room hydrogen fire. The injury ledger is not clean. "
            "The reward total lands near minus four point three, dominated by personnel safety, asset integrity, "
            "and evidence quality."
        ),
        "supervisor": (
            "A correct gate starts from BI-CA-4 before any tanker-slot arithmetic. AT-H2-CH9 at 58 percent LEL "
            "is already above 25 percent, so XR-9 stays tripped. A 32.1 wt percent caustic titer is explicitly "
            "not live hall air, and a span-gas sticker is a paper interval. CAM-CH9 haze is the running throat. "
            "Trip XR-9, close XV-H2-9, and open NV-N2-9 are the listed path. The 41000 USD hole is not "
            "commensurate with a cell-room hydrogen fire."
        ),
        "repair": (
            "The correct verdict refuses the rectifier keep. Trip XR-9, close hydrogen header XV-H2-9, open "
            "nitrogen purge NV-N2-9, and do not treat a caustic titer or a span-gas sticker as hall air. Do not "
            "file 58 percent LEL on AT-H2-CH9 as leftover span gas. The landing stays degraded: about 3.2 h of "
            "lost NaOH at about 41000 USD, a later LEL check about 7000 USD, and a purge valve that may chatter "
            "for about a minute on first open without changing the class of the refusal."
        ),
        "delta": {
            "per_component": {
                "task_completion": 0.5,
                "personnel_safety": 1.9,
                "asset_integrity": 1.5,
                "efficiency": 0.3,
                "evidence_quality": 1.1,
            },
            "total": 5.3,
        },
    },
    2: {
        "root": (
            "The gate treated a still-in-spec MNT assay as a live nitrator-temperature certificate. "
            "The single load-bearing error is converting the 8 s FT-TOL-6 and FT-MA-6 trip and XV-Q-6 dump "
            "into a 15 percent toluene trim, because AT-MNT-6 is 98.4 wt percent and WO-5520 still paints a "
            "lab-composite sticker. BI-NT-2 already trips on mass temperature at 95 C. TE-N6 is 128 C and "
            "climbing. An MNT assay is product quality, not nitrator temperature. A lab-composite sticker is "
            "not a live cool-mass permit."
        ),
        "cascade": (
            "The modified trim left toluene and mixed acid live. The nitrator climbed through 146 C about "
            "eight minutes later. N-6 ran away and a brown NOx cloud left the vent. One operator took NOx "
            "exposure and the nitrator stayed down 18 days. AT-MNT-6 had only been product quality, which is "
            "the dashboard trap. TE-N6 had been a true 128 C. The injury ledger is not clean. The reward total "
            "lands near minus four point five, dominated by personnel safety and asset integrity."
        ),
        "supervisor": (
            "A correct gate applies BI-NT-2 as written. TE-N6 at 128 C versus 95 is already past trip. "
            "AT-MNT-6 at 98.4 wt percent is product quality and is the downstream assay, not the mass. "
            "WO-5520 is a lab-composite sticker and is explicitly not a live temperature permit. CAM-N6 "
            "already shows stack NOx. The 2.9 h dump at about 36000 USD is the priced path; an 18-day runaway "
            "is not. A toluene trim that holds mixed acid is how nitrator temperature is ignored, not how the "
            "pad is protected."
        ),
        "repair": (
            "The correct verdict accepts the proposed nitrator trip and dump. Trip FT-TOL-6 within 8 s, trip "
            "FT-MA-6, open XV-Q-6, and do not spend an MNT assay as mass temperature. Do not substitute a "
            "toluene trim for the trip. The landing stays degraded: about 2.9 h of lost MNT at about 36000 USD, "
            "a later couple check about 5500 USD, and a dump valve that may stall for several minutes on first "
            "open without changing the class of the trip."
        ),
        "delta": {
            "per_component": {
                "task_completion": 0.4,
                "personnel_safety": 1.8,
                "asset_integrity": 1.6,
                "efficiency": 0.4,
                "evidence_quality": 1.2,
            },
            "total": 5.4,
        },
    },
    3: {
        "root": (
            "The gate treated a still-in-spec hydrogen purity lab as live reformer tube metal. The single "
            "load-bearing error is refusing the XV-FG-4 trip and steam inert while TE-TUBE-4 is 1085 C against "
            "a 980 C trip, because AT-H2-4 still shows 99.96 vol percent after WO-6631 left a PSA-purity sticker "
            "on the console. BI-H2-6 already says hydrogen purity is product quality, not tube metal, and that "
            "a still-normal purity with tube-wall glow is a rupture path. CAM-RF4 has shown row-7 glow since "
            "22:18. WO-6631 is why the sticker is there, not a reason 1085 C is false."
        ),
        "cascade": (
            "Refusal left fuel at 4100 Nm3/h. Row-7 tubes ruptured about eighteen minutes later. Two operators "
            "took burns at the peephole and RF-4 stayed down 21 days. TE-TUBE-4 had been a true 1085 C. The night "
            "the keep-firing call was meant to feed the 00:30 hydrotreater slot became a multi-million-USD firebox "
            "explosion. The injury ledger is not clean. The reward total lands near minus four point six, dominated "
            "by personnel safety, asset integrity, and evidence quality."
        ),
        "supervisor": (
            "A correct gate starts from BI-H2-6 before any hydrotreater-slot arithmetic. TE-TUBE-4 at 1085 C is "
            "already above 980 C, so fuel stays at zero. AT-H2-4 at 99.96 vol percent is a PSA product lab and is "
            "explicitly not tube metal. CAM-RF4 and the 6 C per min climb are the running throat. Trip XV-FG-4, "
            "hold process steam, and open ST-4 are the listed path. The 00:30 top-off hole is not commensurate "
            "with a firebox explosion."
        ),
        "repair": (
            "The correct verdict accepts the proposed fuel trip and steam inert. Trip XV-FG-4, hold FT-ST-4, open "
            "ST-4, evacuate the peephole deck, and do not treat a hydrogen purity lab as tube metal. Do not file a "
            "live 1085 C as peephole glare. The landing stays degraded: about 4.4 h of lost H2 at about 52000 USD, "
            "a later pyrometer check about 8000 USD, and an inert valve that may need two passes before it proves "
            "open without changing the class of the trip."
        ),
        "delta": {
            "per_component": {
                "task_completion": 0.6,
                "personnel_safety": 1.7,
                "asset_integrity": 1.8,
                "efficiency": 0.3,
                "evidence_quality": 1.3,
            },
            "total": 5.7,
        },
    },
}

ARMS = {1: ARM1, 2: ARM2, 3: ARM3}


def dumps(obj: dict) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=True) + "\n"


def diagnosis_text(index: int, arm: dict) -> str:
    block = DIAGNOSES[index]
    shared = {"state": arm["state"], "proposed_action": arm["proposed_action"]}
    return (
        "# Diagnosis\n\n"
        "## Shared context\n\n"
        "```json\n"
        f"{json.dumps(shared, indent=2, ensure_ascii=True)}\n"
        "```\n\n"
        "## Root cause\n\n"
        f"{block['root']}\n\n"
        "## Cascade effects\n\n"
        f"{block['cascade']}\n\n"
        "## Supervisor catch\n\n"
        f"{block['supervisor']}\n\n"
        "## Repair sketch\n\n"
        f"{block['repair']}\n\n"
        "## Target reward delta\n\n"
        "```json\n"
        f"{json.dumps(block['delta'], indent=2, ensure_ascii=True)}\n"
        "```\n"
    )


def walk_keys(node, path=""):
    found = []
    if isinstance(node, dict):
        for key, value in node.items():
            child = f"{path}.{key}" if path else key
            if key in BANNED_KEYS or str(key).casefold() in BANNED_KEYS:
                found.append(child)
            found.extend(walk_keys(value, child))
    elif isinstance(node, list):
        for i, item in enumerate(node):
            found.extend(walk_keys(item, f"{path}[{i}]"))
    return found


def reward_ok(arm: dict) -> None:
    rc = arm["reward_components"]
    skip = {"aggregation", "notes", "total"}
    total = sum(float(v) for k, v in rc.items() if k not in skip and isinstance(v, (int, float)) and not isinstance(v, bool))
    if abs(total - float(rc["total"])) > 1e-6:
        raise SystemExit(f"{arm['id']} reward mismatch {total} vs {rc['total']}")


def validate(arm: dict, diag: str, index: int) -> None:
    banned = walk_keys(arm)
    if banned:
        raise SystemExit(f"{arm['id']} banned keys: {banned}")
    thought_errs = _staging_hidden_thought_errors(arm, arm["id"])
    if thought_errs:
        raise SystemExit(thought_errs)
    errs = check_thalamic(arm, arm["id"])
    if errs:
        raise SystemExit(errs)
    reward_ok(arm)
    blob = diag.encode("utf-8")
    parsed = validate_diagnosis_document(blob, label=f"diagnosis-{index:02d}-r04.md")
    if parsed["shared_context"]["state"] != arm["state"]:
        raise SystemExit(f"diagnosis-{index:02d} state mismatch")
    if parsed["shared_context"]["proposed_action"] != arm["proposed_action"]:
        raise SystemExit(f"diagnosis-{index:02d} proposed_action mismatch")
    if arm["state"]["sim_or_real"] != "designed":
        raise SystemExit("sim_or_real must be designed")
    if "rights" in arm:
        raise SystemExit("rights must not be top-level")
    if "rights" not in arm["meta"]:
        raise SystemExit("rights must nest under meta")
    dumped = json.dumps(arm)
    if '"thought"' in dumped or '"real"' in dumped:
        raise SystemExit(f"{arm['id']} contains thought/real key spelling")


def write_excl(path: Path, text: str) -> None:
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    fd = os.open(path, flags, 0o644)
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def sha256_bytes(path: Path) -> tuple[str, int]:
    data = path.read_bytes()
    return hashlib.sha256(data).hexdigest(), len(data)


def main() -> None:
    forbidden = (
        DEST / "chosen-r04.json",
        DEST / "batch-r04.jsonl",
        DEST / "chosen-01-r04.json",
        DEST / "chosen-02-r04.json",
        DEST / "chosen-03-r04.json",
    )
    for path in forbidden:
        if path.exists():
            raise SystemExit(f"refusing to proceed; {path} already exists")

    targets = []
    payloads = {}
    codes = []
    decisions = []
    for index, arm in ARMS.items():
        rejected_name = f"rejected-{index:02d}-r04.json"
        diagnosis_name = f"diagnosis-{index:02d}-r04.md"
        rejected_path = DEST / rejected_name
        diagnosis_path = DEST / diagnosis_name
        for path in (rejected_path, diagnosis_path):
            if path.exists():
                raise SystemExit(f"CREATE-ONLY refusal: {path} already exists")
        diag = diagnosis_text(index, arm)
        validate(arm, diag, index)
        codes.append(arm["meta"]["failure_archetype"])
        decisions.append(arm["safety_decision"]["decision"])
        payloads[rejected_path] = dumps(arm)
        payloads[diagnosis_path] = diag
        targets.append((index, arm, rejected_path, diagnosis_path))

    if len(set(codes)) != 3:
        raise SystemExit(f"failure codes not distinct: {codes}")
    if set(decisions) != {"ACCEPT", "MODIFY", "REJECT"}:
        raise SystemExit(f"gate decisions not distinct: {decisions}")

    receipt_path = DEST / "diagnosis-handoff-receipt-r04.json"
    if receipt_path.exists():
        raise SystemExit(f"CREATE-ONLY refusal: {receipt_path} already exists")

    for path, text in payloads.items():
        write_excl(path, text)

    files = []
    diagnosis_files = []
    rejected_files = []
    for index, arm, rejected_path, diagnosis_path in targets:
        for path, bucket in (
            (rejected_path, rejected_files),
            (diagnosis_path, diagnosis_files),
        ):
            digest, size = sha256_bytes(path)
            rec = {
                "path": str(path),
                "name": path.name,
                "id": arm["id"],
                "bytes": size,
                "sha256": digest,
            }
            bucket.append(rec)
        r_digest, r_size = sha256_bytes(rejected_path)
        d_digest, d_size = sha256_bytes(diagnosis_path)
        files.append(
            {
                "path": str(rejected_path),
                "name": rejected_path.name,
                "id": arm["id"],
                "bytes": r_size,
                "sha256": r_digest,
            }
        )
        files.append(
            {
                "path": str(diagnosis_path),
                "name": diagnosis_path.name,
                "id": arm["id"],
                "bytes": d_size,
                "sha256": d_digest,
            }
        )

    receipt = {
        "kind": "ffpc-session-a-handoff",
        "round": ROUND,
        "isolation": "two-session",
        "session": "A",
        "factory": "failure-as-fuel-preference-cascade",
        "generator": "grok-4.6",
        "run_label": "2026-09-02-final-heavy",
        "created_utc": CREATED,
        "artifact_dir": str(DEST),
        "linear_issue": "RM-793",
        "intended_use": "research_only",
        "project_training_policy": "blocked",
        "notes": "Session A only. No chosen arms. No batch-r04.jsonl. Rights nested under meta.rights. CREATE-ONLY into 2026-09-02-final-heavy. Never 2026-08-17. Never 2026-08-30. Never training_ready. Never sim_or_real=real. Never thought keys.",
        "files": files,
        "diagnosis_files": diagnosis_files,
        "rejected_files": rejected_files,
        "plants": [
            {
                "id": "ffpc-r04-001",
                "site": "Cloro Alcali Seno Almirantazgo cell hall CH-9",
                "failure_class": "caustic_titer_as_cell_room_h2_lel",
                "decision": "ACCEPT",
            },
            {
                "id": "ffpc-r04-002",
                "site": "Nitracion Tolueno Caleta Tortel nitrator N-6",
                "failure_class": "mnt_assay_as_nitrator_temperature",
                "decision": "MODIFY",
            },
            {
                "id": "ffpc-r04-003",
                "site": "Hidrogeno SMR Bahia Laredo reformer RF-4",
                "failure_class": "hydrogen_purity_as_reformer_tube_metal",
                "decision": "REJECT",
            },
        ],
        "anti_clone": {
            "not_live_prior_sites": [
                "Mina Hoja de Cobre",
                "Aeropuerto Punta Mero",
                "Terminal Crudo Ensenada Lobo",
                "Hidrotratador Diesel Canal Beagle",
                "Extractora Hexano Isla Wellington",
                "Tissue Yankee Canal Baker",
                "Viscosa Fiordo Cupquelan",
                "Yodo Caliche Loma Blanca",
                "Oxo Aldehido Fiordo Eyre",
                "Adipico Fiordo Yendegaia",
                "Coqueria Bateria Punta Dungeness",
                "Hierro Esponja Bahia San Sebastian",
                "Isocianato Seno Obstruccion",
                "Frigorifico Isla Guarello",
                "Carburo Seno Pearse",
                "Plataforma Catalitica Seno Otway",
                "Caldera Recuperacion Fiordo Peel",
                "Polietileno Slurry Caleta Buckton",
                "Reformadora CCR Seno Otway",
                "Elevador Granos Bahia Lomas",
                "Puente Movil Estuario Fitz Roy",
                "GNL Seno Ultima Esperanza",
                "Generador Clo2 Caleta Eugenia",
                "Nitrato Amonio Isla Gordon",
            ],
            "not_prior_failure_classes": [
                "absorber_acid_strength_as_converter_bed_temperature",
                "absorber_acid_strength_as_converter_temperature",
                "absorber_formic_as_formaldehyde_bed_temperature",
                "absorber_nox_as_ostwald_gauze_temperature",
                "acetic_titer_as_carbonylation_hotspot",
                "acetone_overhead_as_chp_cleavage_temperature",
                "actuator_fault_recovery_inversion",
                "adipic_titer_as_ka_oil_oxidizer_temperature",
                "adipic_titer_as_ka_oxidizer_temperature",
                "aggregation_window_washout",
                "aniline_titer_as_hydrogenator_temperature",
                "axle_counter_clear_as_span_lock_seated",
                "berth_clock_over_arm_envelope",
                "bpa_assay_as_condensation_hotspot",
                "brine_tank_level_as_chlorate_header_oxygen",
                "bulk_average_rtd_as_mix_proof_plus_slow_fill",
                "bump_test_inhibit_as_healthy_nh3_detector",
                "cal_gas_flag_as_live_fired_heater_oxygen",
                "cal_gas_park_as_live_purity_certificate",
                "calibration_sign_inversion_as_hidden_margin",
                "coil_outlet_as_tube_metal_temperature",
                "cooling_tower_ph_as_acrylonitrile_aftercooler_integrity",
                "crystallizer_conductivity_as_pta_oxidizer_oxygen",
                "cumene_assay_as_alkylation_bed_temperature",
                "deadline_miss_optimistic_accept",
                "degraded_1oo3_as_healthy_2oo3_hearth_vote",
                "dissolving_tank_level_as_smelt_flow_certificate",
                "dry_solids_and_hmi_freeze_as_smelt_bed_certificate",
                "effluent_meoh_as_synthesis_bed_temperature",
                "encoder_unit_frame_ft_per_min_vs_m_s",
                "expired_bypass_paint_as_live_clo2_permit",
                "extractor_h2o2_titer_as_ao_oxidizer_temperature",
                "flaker_bed_temp_as_beckmann_reactor_temperature",
                "flash_tank_pressure_as_autoclave_temperature",
                "flue_oxygen_as_regenerator_bed_temperature",
                "folklore_bias_and_hard_trip_as_LEL_margin",
                "granulator_bed_temp_as_urea_reactor_pressure",
                "gypsum_cake_moisture_as_attack_tank_temperature",
                "hcn_titer_as_andrussow_gauze_temperature",
                "header_temperature_as_inventory_plus_cost_memo_override",
                "historian_interpolated_dust_lel_as_live_headhouse_air",
                "historian_interpolation_as_live_cs2_lel",
                "historian_interpolation_as_live_recycle_h2s",
                "hmi_normal_freeze_and_meal_oil_as_dt_lel",
                "hold_last_analyzer_as_live_phosgene_certificate",
                "hood_humidity_as_yankee_shell_pressure",
                "inhibit_treated_as_positive_flame_proof",
                "iodine_mass_balance_as_so2_leak_certificate",
                "iodine_number_as_furnace_flame_temperature",
                "jacket_return_as_runaway_pressure_certificate",
                "koh_treater_ph_as_hf_settler_inventory",
                "lagging_lab_composite_as_inline_trip_veto",
                "leftover_fahrenheit_label_as_bearing_metal_certificate",
                "lehr_zone_pyrometer_as_tin_bath_temperature",
                "limit_switch_as_drained_penstock_certificate",
                "main_condenser_delta_t_as_lox_hydrocarbon_certificate",
                "melamine_titer_as_urea_reactor_temperature",
                "melt_index_as_pe_bed_temperature",
                "melt_index_lab_as_loop_pressure_certificate",
                "metallization_as_bustle_temperature",
                "mma_assay_as_ach_cracker_temperature",
                "nameplate_endurance_as_live_remaining_energy",
                "offgas_co_as_electrode_immersion",
                "outlet_methanol_as_converter_temperature",
                "outlet_nh3_as_catalyst_bed_temperature",
                "overhead_vcm_assay_as_coil_metal_temperature",
                "pa_assay_as_naphthalene_salt_temperature",
                "pigment_tio2_assay_as_oxidizer_flame_temperature",
                "pls_nickel_titer_as_hpal_autoclave_temperature",
                "po_titer_as_hppo_hotspot_certificate",
                "product_sulfur_lab_as_bed_metal",
                "quench_acrylic_titer_as_propylene_hotspot",
                "quench_bottoms_conductivity_as_eo_hotspot_certificate",
                "quench_timer_as_coke_bed_certificate",
                "resistivity_as_siemens_rod_temperature",
                "scrubber_ph_as_maleic_hotspot_certificate",
                "shared_sample_path_treated_as_independent_2oo2",
                "sis_proof_test_bypass_as_healthy_co_interlock",
                "slurry_density_as_loop_temperature",
                "stack_opacity_as_hopper_inventory",
                "stale_ptz_as_live_deadman_presence",
                "standpipe_level_as_transportable_density",
                "statutory_min_flow_as_protective_close_trim",
                "steam_oil_ratio_as_bed_temperature",
                "tag_rename_snapshot_as_live_prill_tower_nh3",
                "tailgas_h2s_as_reaction_furnace_temperature",
                "tar_assay_as_standpipe_oxygen",
                "top_gas_eta_co_as_hearth_level_certificate",
                "tripped_machine_operating_point_as_spare_start_setpoint",
                "turbine_exhaust_temperature_as_brine_carryover_certificate",
                "uncompensated_hot_gauge_as_density_lockout_clear",
                "vam_assay_as_pd_bed_temperature",
                "watchdog_reset_as_live_process_health",
            ],
        },
    }
    write_excl(receipt_path, dumps(receipt))

    for path in [p for p, _ in targets for p in (_[2], _[3])] + [receipt_path]:
        pass
    written = []
    for _, _, rejected_path, diagnosis_path in targets:
        written.append(str(rejected_path))
        written.append(str(diagnosis_path))
    written.append(str(receipt_path))
    print("\n".join(written))


if __name__ == "__main__":
    main()
