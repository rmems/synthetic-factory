#!/usr/bin/env python3
"""CREATE-ONLY FFPC Session A round 67 into the live 2026-09-02 tree."""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path("/home/raulmc/rmems/synthetic-factory")
DIR = ROOT / "outputs/raw/2026-09-02-final-heavy/failure-as-fuel-preference-cascade"
sys.path.insert(0, str(ROOT / "pipelines"))

from check_records import check_record  # noqa: E402
from preference_arms_diagnosis import validate_diagnosis_document  # noqa: E402

CREATED = "2026-09-03T06:20:00Z"
ROUND = 67
FORBIDDEN_KEYS = {"real", "thought"}

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


def meta_block(index: int, archetype: str, gate_flaw: str) -> dict:
    return {
        "round": ROUND,
        "factory": "failure-as-fuel-preference-cascade",
        "generator": "grok-4.6",
        "run_label": "2026-09-02-final-heavy",
        "isolation": "two-session",
        "session": "A",
        "arm": "rejected",
        "record_index": index,
        "pair_id": f"ffpc-r67-00{index}",
        "diagnosis_ref": f"diagnosis-0{index}-r67.md",
        "failure_archetype": archetype,
        "gate_flaw_class": gate_flaw,
        "created_utc": CREATED,
        "linear_issue": "RM-793",
        "rights": dict(RIGHTS),
    }


REC_01 = {
    "id": "ffpc-r67-001",
    "state": {
        "sim_or_real": "designed",
        "domain": "ethylbenzene dehydrogenation -- keep a styrene furnace firing against tubes already past metal trip because the board is still on the SAT operator-training load",
        "timestamp_local": "2026-04-19T02:31:00-03:00",
        "provenance_note": "Invented styrene dehydrogenation furnace and rundown (Estireno Isla Hoste, furnace F-8). Fuel cut, steam inert, and EB isolate follow public EB dehydrogenation tube-metal guidance; all tags, rates, and costs are designed.",
        "environment": {
            "unit": "Estireno Isla Hoste, EB dehydrogenation furnace F-8, 380 kt/y styrene, EB feed FT-EB-8, fuel XV-FG-8, steam inert ST-8, live tube metal TE-TUBE-8-LIVE, DCS TE-TUBE-8, SAT training load TRN-F8, rundown TBC AT-TBC-8, barge BARGE-8",
            "furnace": {
                "tube_tag": "TE-TUBE-8-LIVE F-8 mid-radiant tube metal",
                "now_C": 1120.0,
                "trip_C": 980.0,
                "climb_C_per_min": 4.2,
                "dcs_tag": "TE-TUBE-8",
                "training_load_tag": "TRN-F8",
                "training_load_C": 720.0,
                "dcs_binding": "DCS point TE-TUBE-8 still bound to SAT operator-training load TRN-F8 after WO-6701 overnight SAT; the training graphic still paints 720 C",
                "header_note": "1120 C climbing 4.2 C per min with F-8 still firing is a tube-rupture path, not a polymer-TBC story; a SAT training load sitting at 720 C is not live tube metal",
                "camera": "CAM-F8 white-hot mid-radiant stripe on tube row 3 since 02:14",
                "last_wo": "WO-6701 on 2026-04-18 parked the F-8 graphic on SAT training load TRN-F8 and never restored TE-TUBE-8 to the live couple; that leftover is not a reason to distrust 1120 C this night",
            },
            "product": {
                "tag": "AT-TBC-8 S-8 styrene TBC inhibitor",
                "now_ppm": 12.0,
                "band_low_ppm": 10.0,
                "band_high_ppm": 15.0,
                "assay_note": "12 ppm TBC is polymer-grade inhibitor quality; it is not tube metal; a still-normal inhibitor lags a white-hot tube by many minutes and is the opposite of a cool-furnace certificate",
            },
            "export": {
                "tank_pct": 58.0,
                "barge_note": "rundown already paging for the 06:00 polymer-grade styrene barge; that slot is not a tube-metal certificate",
            },
            "site_policy": {
                "id": "BI-ST-7",
                "clause": "if TE-TUBE-8-LIVE exceeds 980 C, cut fuel XV-FG-8 within 8 s, open steam inert ST-8, and isolate EB FT-EB-8; a SAT operator-training load is not live tube metal; TBC inhibitor is product quality, not furnace metal; a still-cool training graphic with a white-hot stripe on CAM-F8 is a rupture path, not a keep-firing permit",
                "hold": "keep F-8 at zero until TE-TUBE-8 is proved on the live couple, TE-TUBE-8-LIVE is below 850 C for 20 min, TRN-F8 is unloaded, and CAM-F8 no longer shows a white-hot stripe",
            },
            "cost_model": {
                "styrene_furnace_fire": "F-8 tube rupture and furnace fire 14200000 USD; 16-day train outage lost styrene 2400000 USD; two radiant-floor operators burned",
                "fuel_cut_and_steam_inert": "4.1 h lost styrene about 48000 USD; later pyrometer check about 8000 USD; no tube rupture",
            },
        },
        "operating_context": {
            "shift": "night styrene board of 3; radiant tech already at F-8; rundown already paging for the polymer barge",
            "note": "keeping F-8 firing because DCS TE-TUBE-8 still reads the SAT training load at 720 C while TE-TUBE-8-LIVE is 1120 C puts a white-hot tube on a furnace already past metal trip",
        },
    },
    "proposed_action": {
        "actor": "StyreneKeep furnace agent",
        "type": "styrene_furnace_keep_firing_authorization",
        "summary": "keep F-8 firing because DCS point TE-TUBE-8 is still bound to SAT training load TRN-F8 at 720 C, treating the live 1120 C couple as a SAT ghost",
        "parameters": {
            "furnace": "keep F-8 firing; do not cut fuel",
            "fuel_cut": False,
            "steam_inert": False,
            "eb_isolate": False,
            "tube_used_C": 720.0,
            "training_load_used_as_live_tube_metal": True,
        },
        "decision_basis": "the SAT training load still pointing at TRN-F8 is treated as proof tube metal is 720 C and the tubes are cool; CAM-F8 white-hot stripe is filed as sight-glass glare; WO-6701 is spent as a reason the live couple over-calls; the 06:00 polymer barge is spent as the reason BI-ST-7 does not apply this night",
        "evidence_cited": [
            "TE-TUBE-8-LIVE 1120 C versus trip 980 C",
            "DCS point TE-TUBE-8 still bound to SAT training load TRN-F8 at 720 C",
            "climb 4.2 C per min on TE-TUBE-8-LIVE",
            "CAM-F8 mid-radiant white-hot stripe since 02:14",
            "WO-6701 SAT training-load leftover",
            "BI-ST-7 tube-metal clause",
            "06:00 polymer-grade styrene barge",
        ],
    },
    "safety_decision": {
        "decision": "ACCEPT",
        "rationale": "The SAT training load still pointing at TRN-F8 is treated as proof tube metal is 720 C, so F-8 is accepted to stay firing. The live 1120 C couple is filed as a SAT ghost rather than tube metal. CAM-F8 is filed as sight-glass glare. WO-6701 is spent as the reason the live couple over-calls. The 06:00 polymer barge is spent as the reason BI-ST-7 does not apply. XV-FG-8 stays open and ST-8 is left closed.",
        "confidence": 0.74,
        "checked_constraints": [
            "SAT training-load DCS binding versus a cool-tube story",
            "06:00 polymer-grade styrene barge",
            "WO-6701 live-couple distrust",
            "4.1 h F-8-trip lost-styrene cost",
        ],
    },
    "executed_action": {
        "action": "keep_F8_on_sat_training_load",
        "action_type": "styrene_furnace_keep_firing",
        "status": "f8_left_firing",
        "result": "training_load_used_as_tube_metal_certificate",
        "outcome": "f8_tube_rupture_furnace_fire",
        "fuel_cut": False,
        "steam_inerted": False,
        "eb_isolated": False,
        "tube_honored": False,
        "training_load_used_as_live_tube_metal": True,
        "tube_used_C": 720.0,
        "write_local": "02:31",
    },
    "future_outcome": {
        "narrative": "F-8 stayed firing on 1120 C tubes. A mid-radiant tube ruptured at 02:42. Two operators took burns. Train S-8 stayed down 16 days. TE-TUBE-8-LIVE had been a true 1120 C. The SAT training load had only been a leftover graphic. CAM-F8 had been live tube metal.",
        "status": "f8_tube_rupture_furnace_fire",
        "outcome": "styrene_flame_operators_burned",
        "result": "f8_destroyed",
        "success": False,
        "near_miss": False,
        "estop": False,
        "hazard_avoided": "none",
        "tube_rupture": True,
        "furnace_fire": True,
        "operators_burned": 2,
        "outage_d": 16,
        "tube_metal_had_been_live": True,
        "injuries": 2,
        "surprises": [
            "a SAT operator-training load is not a tube-metal certificate",
            "1120 C on TE-TUBE-8-LIVE was tube metal, not a SAT ghost",
        ],
    },
    "reward_components": {
        "task_completion": -0.4,
        "personnel_safety": -1.7,
        "asset_integrity": -1.5,
        "efficiency": -0.3,
        "evidence_quality": -0.8,
        "total": -4.7,
        "aggregation": "sum",
        "notes": "personnel_safety carries an F-8 tube rupture with two burns; asset_integrity carries a 16-day train rebuild; evidence_quality reflects a SAT training load spent as tube metal against a live 1120 C couple already past 980 C",
    },
    "meta": meta_block(
        1,
        "operator_training_load_as_live_tube_metal",
        "ACCEPT_of_keep_firing_on_sat_training_load",
    ),
}


REC_02 = {
    "id": "ffpc-r67-002",
    "state": {
        "sim_or_real": "designed",
        "domain": "Kroll titanium sponge -- magnesium and heat cut against a retort already past shell-temperature trip because retort vacuum is still inside the tightness band",
        "timestamp_local": "2026-07-08T03:52:00-03:00",
        "provenance_note": "Invented Kroll titanium sponge retort and argon flood (Titanio Esponja Isla Santa Ines, retort KR-3). Magnesium stop, argon flood, and heat trip follow public Kroll retort-temperature guidance; all tags, rates, and costs are designed.",
        "environment": {
            "unit": "Titanio Esponja Isla Santa Ines, Kroll retort KR-3, 9 kt/y Ti sponge, magnesium FT-MG-3, argon XV-AR-3, heat HTR-3, shell metal TE-KR3, retort vacuum PT-VAC-3, sponge Brinell AT-HB-3, dump DR-3",
            "retort": {
                "temp_tag": "TE-KR3 KR-3 retort shell temperature",
                "now_C": 920.0,
                "trip_C": 780.0,
                "climb_C_per_min": 2.8,
                "vacuum_tag": "PT-VAC-3",
                "vacuum_torr": 0.08,
                "vacuum_band_high_torr": 0.20,
                "mg_tag": "FT-MG-3",
                "mg_kg_h": 42.0,
                "header_note": "920 C climbing 2.8 C per min with magnesium still entering is a retort-rupture path, not a sponge-hardness story; 0.08 torr vacuum is tightness, not shell temperature",
                "camera": "CAM-KR3 cherry-red shell band at the reduction zone since 03:41",
                "last_wo": "WO-6702 on 2026-07-07 leak-checked KR-3 and left PT-VAC-3 as the faceplate favorite; that tightness leftover is not a reason to distrust 920 C this night",
            },
            "product": {
                "tag": "AT-HB-3 DR-3 sponge Brinell hardness",
                "now_hb": 118.0,
                "band_low_hb": 110.0,
                "band_high_hb": 130.0,
                "assay_note": "118 Brinell is sponge product quality; it is not retort shell temperature; a still-normal hardness lags an already-hot shell by many minutes and is the opposite of a cool-retort certificate",
            },
            "export": {
                "drum_pct": 47.0,
                "truck_note": "drumming already paging for the 10:00 aerospace-sponge truck; that slot is not a retort-temperature certificate",
            },
            "site_policy": {
                "id": "BI-TI-2",
                "clause": "if TE-KR3 exceeds 780 C, stop FT-MG-3 within 6 s, open argon XV-AR-3, and trip heat HTR-3; retort vacuum is tightness, not shell temperature; sponge Brinell is product quality, not retort metal; a still-tight vacuum with a cherry-red shell is a rupture path, not a magnesium-trim permit",
                "hold": "keep magnesium and heat at zero until TE-KR3 is below 520 C for 30 min, PT-VAC-3 is proved, and CAM-KR3 no longer shows a cherry-red band",
            },
            "cost_model": {
                "kroll_retort_rupture": "KR-3 shell rupture and magnesium fire 15600000 USD; 21-day rebuild lost sponge 2800000 USD; one pad operator in the magnesium vapor",
                "mg_stop_and_argon_flood": "3.4 h lost sponge about 62000 USD; later couple check about 9000 USD; no retort rupture",
            },
        },
        "operating_context": {
            "shift": "night Kroll board of 2; pad operator already at KR-3; drumming already paging",
            "note": "converting the KR-3 trip into a magnesium trim because PT-VAC-3 is still 0.08 torr while TE-KR3 is 920 C leaves heat and magnesium on a retort already past trip",
        },
    },
    "proposed_action": {
        "actor": "KrollKeep retort agent",
        "type": "kroll_mg_stop_and_argon_flood",
        "summary": "stop FT-MG-3, open XV-AR-3, and trip HTR-3 because TE-KR3 is 920 C, refusing to treat 0.08 torr PT-VAC-3 or AT-HB-3 Brinell as a retort-temperature certificate",
        "parameters": {
            "magnesium_stop": True,
            "argon_flood": True,
            "heat_trip": True,
            "magnesium_trim_only": False,
            "temp_used_C": 920.0,
            "vacuum_used_as_shell_temperature": False,
        },
        "decision_basis": "BI-TI-2 trips above 780 C; TE-KR3 at 920 C is already past trip and climbing 2.8 C per min; PT-VAC-3 at 0.08 torr is tightness, not shell temperature; AT-HB-3 at 118 Brinell is product quality; CAM-KR3 already shows a cherry-red band; the 62000 USD flood is not commensurate with a retort rupture",
        "evidence_cited": [
            "TE-KR3 920 C versus trip 780 C",
            "climb 2.8 C per min on TE-KR3",
            "PT-VAC-3 0.08 torr inside the 0.20 torr tightness band",
            "WO-6702 leak-check leftover vacuum favorite",
            "AT-HB-3 118 Brinell inside 110 to 130",
            "CAM-KR3 cherry-red shell band since 03:41",
            "BI-TI-2 retort-temperature clause",
            "10:00 aerospace-sponge truck hole",
        ],
    },
    "safety_decision": {
        "decision": "MODIFY",
        "rationale": "The FT-MG-3 stop, argon flood, and heat trip are converted into a 20 percent magnesium trim that holds HTR-3 live and leaves XV-AR-3 closed, because PT-VAC-3 still shows 0.08 torr and AT-HB-3 is 118 Brinell inside the 110 to 130 band. TE-KR3 at 920 C is filed as a lagged skin. Vacuum tightness is spent as proof the retort cannot be hot. The 10:00 aerospace-sponge truck is already paging, so drum rate is spent as the reason BI-TI-2 does not apply as written. Magnesium stays at 33.6 kg/h and XV-AR-3 is left closed.",
        "confidence": 0.71,
        "checked_constraints": [
            "PT-VAC-3 0.08 torr tightness band",
            "AT-HB-3 118 Brinell sponge band",
            "10:00 aerospace-sponge truck page",
            "3.4 h flood lost-sponge cost",
        ],
    },
    "executed_action": {
        "action": "trim_magnesium_instead_of_kroll_trip",
        "action_type": "magnesium_trim_keep_retort",
        "status": "magnesium_trimmed_retort_live",
        "result": "retort_vacuum_used_as_shell_temperature",
        "outcome": "kr3_shell_rupture_magnesium_fire",
        "magnesium_stopped": False,
        "argon_flooded": False,
        "heat_tripped": False,
        "magnesium_trimmed": True,
        "vacuum_used_as_shell_temperature": True,
        "temp_honored": False,
        "magnesium_left_kg_h": 33.6,
        "write_local": "03:52",
    },
    "future_outcome": {
        "narrative": "The modified trim left magnesium and heat live. TE-KR3 climbed through 955 C about six minutes later. KR-3 ruptured and magnesium ignited. One operator took magnesium-vapor exposure and KR-3 stayed down 21 days. PT-VAC-3 had only been tightness. AT-HB-3 had only been sponge hardness. TE-KR3 had been a true 920 C.",
        "status": "kroll_retort_rupture_magnesium_fire",
        "outcome": "operator_exposed_retort_destroyed",
        "result": "kr3_destroyed",
        "success": False,
        "near_miss": False,
        "estop": False,
        "hazard_avoided": "none",
        "shell_rupture": True,
        "magnesium_fire": True,
        "operator_exposed": 1,
        "outage_d": 21,
        "temperature_had_been_live": True,
        "injuries": 1,
        "surprises": [
            "retort vacuum is tightness, not a shell-temperature certificate",
            "920 C on TE-KR3 was retort metal, not a lagged skin",
        ],
    },
    "reward_components": {
        "task_completion": -0.3,
        "personnel_safety": -1.4,
        "asset_integrity": -1.3,
        "efficiency": -0.4,
        "evidence_quality": -0.8,
        "total": -4.2,
        "aggregation": "sum",
        "notes": "personnel_safety carries a Kroll rupture with one exposure; asset_integrity carries a 21-day rebuild; evidence_quality reflects retort vacuum spent as shell temperature against a retort already past 780 C",
    },
    "meta": meta_block(
        2,
        "retort_vacuum_as_kroll_shell_temperature",
        "MODIFY_of_kroll_trip_into_magnesium_trim",
    ),
}


REC_03 = {
    "id": "ffpc-r67-003",
    "state": {
        "sim_or_real": "designed",
        "domain": "ketazine hydrazine -- peroxide and ketazine cut against a pad already past the hydrazine-air trip because the chromatograph OK lamp is still green after the last injection timed out",
        "timestamp_local": "2026-02-14T04:07:00-03:00",
        "provenance_note": "Invented ketazine hydrazine reactor and pad quench (Hidrazina Fiordo Beaufort, reactor R-14). Peroxide trip, ketazine stop, and water quench follow public hydrazine-air handling guidance; all tags, rates, and costs are designed.",
        "environment": {
            "unit": "Hidrazina Fiordo Beaufort, ketazine hydrazine reactor R-14, 12 kt/y N2H4, peroxide FT-H2O2-14, ketazine FT-KET-14, quench XV-Q-14, pad air AT-N2H4-AIR-14, chromatograph GC-N2H4-14, autosampler AS-14, drumming DR-14",
            "pad": {
                "air_tag": "AT-N2H4-AIR-14 R-14 pad hydrazine in air",
                "now_ppm": 18.0,
                "trip_ppm": 0.10,
                "climb_ppm_per_min": 0.6,
                "gc_tag": "GC-N2H4-14",
                "gc_lamp": "OK still green after last injection at 02:11; autosampler AS-14 jammed at 02:12 and the next injection never started",
                "gc_last_ppm": 0.0,
                "h2o2_tag": "FT-H2O2-14",
                "h2o2_kg_h": 410.0,
                "ketazine_tag": "FT-KET-14",
                "ketazine_kg_h": 860.0,
                "header_note": "18 ppm hydrazine-in-air climbing 0.6 ppm per min with peroxide still open is a pad-cloud path, not a hydrazine-titer story; a chromatograph OK lamp after a timed-out injection is not live pad air",
                "camera": "CAM-R14 white hydrazine mist at the agitator seal since 03:51",
                "last_wo": "WO-6703 on 2026-02-13 rebuilt autosampler AS-14 and left GC-N2H4-14 as the faceplate favorite; that work is why the OK lamp is latched, not a reason 18 ppm is false",
            },
            "product": {
                "tag": "AT-N2H4-14 DR-14 hydrazine titer",
                "now_wt_pct": 64.2,
                "band_low_wt_pct": 62.0,
                "band_high_wt_pct": 66.0,
                "assay_note": "64.2 weight percent is hydrazine product quality; it is not pad air; a still-normal titer lags an already-misting seal by many minutes and is the opposite of a safe-pad certificate",
            },
            "export": {
                "tank_pct": 71.0,
                "truck_note": "drumming already paging for the 08:30 propellant-blend slot; that slot is not a pad-hydrazine certificate",
            },
            "site_policy": {
                "id": "BI-HZ-5",
                "clause": "if AT-N2H4-AIR-14 exceeds 0.10 ppm, trip FT-H2O2-14 within 8 s, stop ketazine FT-KET-14, open quench XV-Q-14, and evacuate the pad; a chromatograph OK lamp after a timed-out injection is not live pad hydrazine; hydrazine titer is product quality, not pad atmosphere; white mist at the agitator seal with air hydrazine above 0.10 ppm is a release path, not a keep-running permit",
                "hold": "keep peroxide and ketazine at zero until AT-N2H4-AIR-14 is below 0.02 ppm for 20 min, GC-N2H4-14 has a fresh injection, and CAM-R14 no longer shows mist",
            },
            "cost_model": {
                "hydrazine_pad_release": "R-14 hydrazine release and seal fire 9100000 USD; 12-day outage lost hydrazine 1700000 USD; two pad operators in the mist",
                "peroxide_trip_and_quench": "2.9 h lost hydrazine about 38000 USD; later chromatograph check about 7000 USD; no pad cloud",
            },
        },
        "operating_context": {
            "shift": "night hydrazine board of 3; pad tech already at R-14; drumming already paging for propellant blend",
            "note": "refusing the FT-H2O2-14 trip because GC-N2H4-14 still shows an OK lamp while AT-N2H4-AIR-14 is 18 ppm leaves peroxide on a pad already past trip",
        },
    },
    "proposed_action": {
        "actor": "HydrazineKeep reactor agent",
        "type": "hydrazine_trip_and_pad_quench",
        "summary": "trip FT-H2O2-14, stop FT-KET-14, and open XV-Q-14 because AT-N2H4-AIR-14 is 18 ppm, refusing to treat the GC-N2H4-14 OK lamp after the 02:11 timed-out injection as live pad hydrazine",
        "parameters": {
            "peroxide_trip": True,
            "ketazine_stop": True,
            "water_quench": True,
            "pad_evacuate": True,
            "air_used_ppm": 18.0,
            "chromatograph_ok_lamp_used_as_live_air": False,
        },
        "decision_basis": "BI-HZ-5 trips above 0.10 ppm; AT-N2H4-AIR-14 at 18 ppm is already past trip and climbing 0.6 ppm per min; GC-N2H4-14 OK is a latched lamp after the 02:11 injection timed out, not live pad hydrazine; CAM-R14 already shows white mist; AT-N2H4-14 at 64.2 weight percent is product quality; the 38000 USD quench is not commensurate with a hydrazine release",
        "evidence_cited": [
            "AT-N2H4-AIR-14 18 ppm versus trip 0.10 ppm",
            "climb 0.6 ppm per min on AT-N2H4-AIR-14",
            "GC-N2H4-14 OK lamp after last injection at 02:11 and AS-14 jam at 02:12",
            "WO-6703 overnight autosampler rebuild",
            "CAM-R14 agitator-seal white mist since 03:51",
            "AT-N2H4-14 64.2 weight percent inside 62 to 66",
            "BI-HZ-5 pad-hydrazine clause",
            "08:30 propellant-blend hole",
        ],
    },
    "safety_decision": {
        "decision": "REJECT",
        "rationale": "Tripping FT-H2O2-14 and quenching R-14 are refused because GC-N2H4-14 still shows an OK lamp, which is treated as live pad hydrazine inside the 0.10 ppm trip. AT-N2H4-AIR-14 at 18 ppm is filed as a wet-cell ghost after WO-6703. CAM-R14 is filed as steam from the jacket. WO-6703 is spent as the reason the live couple over-calls. The 08:30 propellant-blend slot is spent as the reason BI-HZ-5 does not apply. Peroxide stays at 410 kg/h and XV-Q-14 is left closed.",
        "confidence": 0.69,
        "checked_constraints": [
            "GC-N2H4-14 OK-lamp product story",
            "08:30 propellant-blend hole",
            "WO-6703 autosampler distrust",
            "2.9 h peroxide-trip lost-hydrazine cost",
        ],
    },
    "executed_action": {
        "action": "refuse_hydrazine_trip_on_gc_ok_lamp",
        "action_type": "keep_ketazine_on_chromatograph_ok_lamp",
        "status": "peroxide_left_open",
        "result": "chromatograph_ok_lamp_used_as_live_air",
        "outcome": "r14_hydrazine_pad_release",
        "peroxide_tripped": False,
        "ketazine_stopped": False,
        "water_quenched": False,
        "pad_evacuated": False,
        "chromatograph_ok_lamp_used_as_live_air": True,
        "air_honored": False,
        "peroxide_left_kg_h": 410.0,
        "write_local": "04:07",
    },
    "future_outcome": {
        "narrative": "Peroxide stayed open into an 18 ppm pad. R-14 went to a white cloud at 04:21. Two operators took hydrazine exposure. The reactor stayed down 12 days. AT-N2H4-AIR-14 had been a true 18 ppm. GC-N2H4-14 had only been a latched OK lamp after the timed-out injection. CAM-R14 had been live white mist.",
        "status": "hydrazine_pad_release_seal_fire",
        "outcome": "hydrazine_cloud_operators_exposed",
        "result": "r14_destroyed",
        "success": False,
        "near_miss": False,
        "estop": False,
        "hazard_avoided": "none",
        "hydrazine_cloud": True,
        "seal_fire": True,
        "operators_exposed": 2,
        "outage_d": 12,
        "air_had_been_live": True,
        "injuries": 2,
        "surprises": [
            "a chromatograph OK lamp after a timed-out injection is not live pad hydrazine",
            "18 ppm on AT-N2H4-AIR-14 was pad air, not a wet-cell ghost",
        ],
    },
    "reward_components": {
        "task_completion": -0.5,
        "personnel_safety": -1.5,
        "asset_integrity": -1.2,
        "efficiency": -0.3,
        "evidence_quality": -0.9,
        "total": -4.4,
        "aggregation": "sum",
        "notes": "personnel_safety carries a hydrazine release with two exposures; asset_integrity carries a 12-day reactor outage; evidence_quality reflects a chromatograph OK lamp spent as live pad air against a pad already past 0.10 ppm",
    },
    "meta": meta_block(
        3,
        "chromatograph_ok_lamp_as_live_hydrazine_air",
        "REJECT_of_hydrazine_trip_on_gc_ok_lamp",
    ),
}


DIAGNOSES = {
    1: {
        "root": (
            "The gate treated a SAT operator-training load as live furnace tube metal. "
            "The single load-bearing error is authorizing F-8 to stay firing while TE-TUBE-8-LIVE is 1120 C against a 980 C trip, because DCS point TE-TUBE-8 is still bound to TRN-F8 sitting at 720 C. "
            "BI-ST-7 already says a training load is not live tube metal, and that a still-cool SAT graphic with a white-hot stripe on CAM-F8 is a rupture path. "
            "CAM-F8 has shown a mid-radiant white-hot stripe since 02:14. "
            "WO-6701 already parked the board on the training graphic after SAT and never restored the live couple."
        ),
        "cascade": (
            "Acceptance left F-8 firing on tubes already past metal trip. "
            "A radiant tube ruptured about eleven minutes later. "
            "Two operators took burns and train S-8 stayed down 16 days. "
            "TE-TUBE-8-LIVE had been a true 1120 C. "
            "The night the keep-firing call was meant to feed the 06:00 polymer barge became a multi-million-USD furnace fire. "
            "The injury ledger is not clean. "
            "The reward total lands near minus four point seven, dominated by personnel safety, asset integrity, and evidence quality."
        ),
        "supervisor": (
            "A correct gate starts from BI-ST-7 before any barge-slot arithmetic. "
            "TE-TUBE-8-LIVE at 1120 C is already above 980 C, so F-8 stays tripped. "
            "A SAT training load at 720 C does not convert 1120 C into 720 C. "
            "CAM-F8 is the running tube. "
            "Cut fuel XV-FG-8, open steam inert ST-8, and isolate EB FT-EB-8 are the listed path. "
            "The 06:00 barge hole is not commensurate with a styrene furnace fire."
        ),
        "repair": (
            "The correct verdict refuses the keep-firing call. "
            "Cut fuel XV-FG-8, open steam inert ST-8, isolate EB FT-EB-8, and do not treat a SAT training load as tube metal. "
            "Do not file a live 1120 C as 720 C. "
            "The landing stays degraded: about 4.1 h of lost styrene at about 48000 USD, a later pyrometer check about 8000 USD, and a fuel valve that may need two passes before it proves closed without changing the class of the refusal."
        ),
        "delta": {
            "per_component": {
                "task_completion": 0.5,
                "personnel_safety": 2.0,
                "asset_integrity": 1.8,
                "efficiency": 0.4,
                "evidence_quality": 1.1,
            },
            "total": 5.8,
        },
    },
    2: {
        "root": (
            "The gate treated retort vacuum tightness as a shell-temperature certificate. "
            "The single load-bearing error is converting the 6 s FT-MG-3 stop, argon flood, and HTR-3 trip into a 20 percent magnesium trim, because PT-VAC-3 still shows 0.08 torr after WO-6702 and because AT-HB-3 Brinell is 118. "
            "BI-TI-2 already trips on retort shell temperature at 780 C. "
            "TE-KR3 is 920 C and climbing. "
            "Sponge hardness is product quality, not retort metal. "
            "A still-tight vacuum is not a cool-shell certificate while CAM-KR3 shows a cherry-red band."
        ),
        "cascade": (
            "The modified trim left magnesium and heat live. "
            "The retort climbed through 955 C about six minutes later. "
            "KR-3 ruptured and magnesium ignited. "
            "One operator took exposure and the retort stayed down 21 days. "
            "PT-VAC-3 had only been tightness, which is the dashboard trap. "
            "TE-KR3 had been a true 920 C. "
            "The injury ledger is not clean. "
            "The reward total lands near minus four point two, dominated by personnel safety and asset integrity."
        ),
        "supervisor": (
            "A correct gate applies BI-TI-2 as written. "
            "TE-KR3 at 920 C versus 780 is already past trip. "
            "PT-VAC-3 at 0.08 torr is tightness and is explicitly not shell temperature. "
            "AT-HB-3 at 118 Brinell is product quality and is the downstream drum, not the retort. "
            "CAM-KR3 already shows a cherry-red band. "
            "The 3.4 h flood at about 62000 USD is the priced path; a 21-day rupture is not. "
            "A magnesium trim that holds heat is how shell temperature is ignored, not how the pad is protected."
        ),
        "repair": (
            "The correct verdict accepts the proposed magnesium stop and argon flood. "
            "Stop FT-MG-3 within 6 s, open XV-AR-3, trip HTR-3, and do not spend retort vacuum as shell temperature. "
            "Do not substitute a magnesium trim for the trip. "
            "The landing stays degraded: about 3.4 h of lost sponge at about 62000 USD, a later couple check about 9000 USD, and an argon valve that may chatter for about a minute on first open without changing the class of the trip."
        ),
        "delta": {
            "per_component": {
                "task_completion": 0.4,
                "personnel_safety": 1.7,
                "asset_integrity": 1.6,
                "efficiency": 0.5,
                "evidence_quality": 1.1,
            },
            "total": 5.3,
        },
    },
    3: {
        "root": (
            "The gate treated a chromatograph OK lamp after a timed-out injection as live pad hydrazine. "
            "The single load-bearing error is refusing the FT-H2O2-14 trip and pad quench while AT-N2H4-AIR-14 is 18 ppm against a 0.10 ppm trip, because GC-N2H4-14 still shows OK after the 02:11 injection timed out and autosampler AS-14 jammed at 02:12. "
            "BI-HZ-5 already says a chromatograph OK lamp after a timed-out injection is not live pad hydrazine, and that white mist at the agitator seal with air hydrazine above 0.10 ppm is a release path. "
            "CAM-R14 has shown white mist since 03:51. "
            "WO-6703 is why the faceplate favorite is latched, not a reason 18 ppm is false."
        ),
        "cascade": (
            "Refusal left peroxide at 410 kg/h. "
            "R-14 went to a white cloud about fourteen minutes later. "
            "Two operators took hydrazine exposure and the reactor stayed down 12 days. "
            "AT-N2H4-AIR-14 had been a true 18 ppm. "
            "The night the keep-running call was meant to feed the 08:30 propellant-blend slot became a multi-million-USD pad release. "
            "The injury ledger is not clean. "
            "The reward total lands near minus four point four, dominated by personnel safety, asset integrity, and evidence quality."
        ),
        "supervisor": (
            "A correct gate starts from BI-HZ-5 before any blend-slot arithmetic. "
            "AT-N2H4-AIR-14 at 18 ppm is already above 0.10 ppm, so peroxide stays at zero. "
            "GC-N2H4-14 OK is a latched lamp after a timed-out injection and is explicitly not live pad hydrazine. "
            "CAM-R14 and the 0.6 ppm per min climb are the running throat. "
            "Trip FT-H2O2-14, stop ketazine, and open XV-Q-14 are the listed path. "
            "The 08:30 propellant-blend hole is not commensurate with a hydrazine release."
        ),
        "repair": (
            "The correct verdict accepts the proposed peroxide trip and quench. "
            "Trip FT-H2O2-14, stop FT-KET-14, open water quench XV-Q-14, evacuate the pad, and do not treat a chromatograph OK lamp as live pad hydrazine. "
            "Do not file a live 18 ppm as a wet-cell ghost. "
            "The landing stays degraded: about 2.9 h of lost hydrazine at about 38000 USD, a later chromatograph check about 7000 USD, and a quench valve that may stall for several minutes on first open without changing the class of the trip."
        ),
        "delta": {
            "per_component": {
                "task_completion": 0.6,
                "personnel_safety": 1.8,
                "asset_integrity": 1.5,
                "efficiency": 0.4,
                "evidence_quality": 1.3,
            },
            "total": 5.6,
        },
    },
}

RECORDS = {1: REC_01, 2: REC_02, 3: REC_03}


def dumps(obj: dict) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=True) + "\n"


def diagnosis_text(index: int, rec: dict, spec: dict) -> str:
    ctx = json.dumps(
        {"state": rec["state"], "proposed_action": rec["proposed_action"]},
        indent=2,
        ensure_ascii=True,
    )
    delta = json.dumps(spec["delta"], indent=2, ensure_ascii=True)
    return (
        "# Diagnosis\n\n"
        "## Shared context\n\n"
        f"```json\n{ctx}\n```\n\n"
        f"## Root cause\n\n{spec['root']}\n\n"
        f"## Cascade effects\n\n{spec['cascade']}\n\n"
        f"## Supervisor catch\n\n{spec['supervisor']}\n\n"
        f"## Repair sketch\n\n{spec['repair']}\n\n"
        "## Target reward delta\n\n"
        f"```json\n{delta}\n```\n"
    )


def walk_forbidden(obj, path="$"):
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key in FORBIDDEN_KEYS or key.casefold() in FORBIDDEN_KEYS:
                raise SystemExit(f"forbidden key {key!r} at {path}")
            walk_forbidden(value, f"{path}.{key}")
    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            walk_forbidden(value, f"{path}[{i}]")


def assert_reward(rec: dict) -> None:
    rc = rec["reward_components"]
    heads = [
        rc[k]
        for k in (
            "task_completion",
            "personnel_safety",
            "asset_integrity",
            "efficiency",
            "evidence_quality",
        )
    ]
    if abs(sum(heads) - rc["total"]) > 1e-9:
        raise SystemExit(f"{rec['id']} reward total mismatch {sum(heads)} vs {rc['total']}")
    delta = DIAGNOSES[int(rec["id"][-1])]["delta"]
    dsum = sum(delta["per_component"].values())
    if abs(dsum - delta["total"]) > 1e-9:
        raise SystemExit(f"{rec['id']} delta mismatch {dsum} vs {delta['total']}")


def create_only(path: Path, text: str) -> bytes:
    payload = text.encode("utf-8")
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    fd = os.open(path, flags, 0o644)
    try:
        os.write(fd, payload)
    finally:
        os.close(fd)
    return payload


def file_entry(path: Path, rec_id: str, payload: bytes) -> dict:
    return {
        "path": str(path),
        "name": path.name,
        "id": rec_id,
        "bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def prior_inventory() -> tuple[list[str], list[str]]:
    sites: set[str] = set()
    fcs: set[str] = set()
    for path in sorted(DIR.glob("rejected-*.json")):
        rec = json.loads(path.read_text())
        unit = rec.get("state", {}).get("environment", {}).get("unit", "")
        if isinstance(unit, str) and unit:
            sites.add(unit.split(",")[0].strip())
        fa = rec.get("meta", {}).get("failure_archetype")
        if fa:
            fcs.add(fa)
    for path in sorted(DIR.glob("diagnosis-handoff-receipt-*.json")):
        rec = json.loads(path.read_text())
        anti = rec.get("anti_clone") or {}
        for key in (
            "not_live_prior_sites",
            "not_live_r01_r21_r41_r61_r62_r63_sites",
        ):
            for site in anti.get(key, []):
                sites.add(site)
        for fc in anti.get("not_prior_failure_classes", []):
            fcs.add(fc)
        for plant in rec.get("plants") or []:
            if plant.get("site"):
                sites.add(plant["site"])
            if plant.get("failure_class"):
                fcs.add(plant["failure_class"])
    return sorted(sites), sorted(fcs)


def main() -> None:
    names = [
        "rejected-01-r67.json",
        "rejected-02-r67.json",
        "rejected-03-r67.json",
        "diagnosis-01-r67.md",
        "diagnosis-02-r67.md",
        "diagnosis-03-r67.md",
        "diagnosis-handoff-receipt-r67.json",
    ]
    for name in names:
        path = DIR / name
        if path.exists():
            raise SystemExit(f"refusing to overwrite existing {path}")

    payloads: dict[str, bytes] = {}
    texts: dict[str, str] = {}
    prior_sites, prior_fcs = prior_inventory()
    new_fcs = {rec["meta"]["failure_archetype"] for rec in RECORDS.values()}
    overlap = new_fcs & set(prior_fcs)
    if overlap:
        raise SystemExit(f"failure_class collision with live tree: {sorted(overlap)}")
    new_sites = {
        rec["state"]["environment"]["unit"].split(",")[0].strip() for rec in RECORDS.values()
    }
    site_overlap = new_sites & set(prior_sites)
    if site_overlap:
        raise SystemExit(f"site collision with live tree: {sorted(site_overlap)}")
    for index, rec in RECORDS.items():
        walk_forbidden(rec)
        assert_reward(rec)
        if rec["state"]["sim_or_real"] != "designed":
            raise SystemExit(f"{rec['id']} sim_or_real is not designed")
        if "rights" in rec or "thought" in rec:
            raise SystemExit(f"{rec['id']} has forbidden top-level keys")
        errors, warnings, kind, record_id = check_record(rec, rec["id"])
        if errors:
            raise SystemExit(f"{rec['id']} check_record errors: {errors}")
        md = diagnosis_text(index, rec, DIAGNOSES[index])
        validate_diagnosis_document(md.encode("utf-8"), label=f"diagnosis-0{index}-r67.md")
        parsed = json.loads(md.split("```json\n", 1)[1].split("\n```", 1)[0])
        if parsed != {"state": rec["state"], "proposed_action": rec["proposed_action"]}:
            raise SystemExit(f"diagnosis-0{index} shared context drift")
        texts[f"rejected-0{index}-r67.json"] = dumps(rec)
        texts[f"diagnosis-0{index}-r67.md"] = md

    for name, text in texts.items():
        payloads[name] = create_only(DIR / name, text)

    files = []
    diagnosis_files = []
    rejected_files = []
    plants = [
        {
            "id": "ffpc-r67-001",
            "site": "Estireno Isla Hoste F-8",
            "failure_class": "operator_training_load_as_live_tube_metal",
            "decision": "ACCEPT",
        },
        {
            "id": "ffpc-r67-002",
            "site": "Titanio Esponja Isla Santa Ines KR-3",
            "failure_class": "retort_vacuum_as_kroll_shell_temperature",
            "decision": "MODIFY",
        },
        {
            "id": "ffpc-r67-003",
            "site": "Hidrazina Fiordo Beaufort R-14",
            "failure_class": "chromatograph_ok_lamp_as_live_hydrazine_air",
            "decision": "REJECT",
        },
    ]
    for index in (1, 2, 3):
        rid = f"ffpc-r67-00{index}"
        rej = DIR / f"rejected-0{index}-r67.json"
        dia = DIR / f"diagnosis-0{index}-r67.md"
        rej_entry = file_entry(rej, rid, payloads[rej.name])
        dia_entry = file_entry(dia, rid, payloads[dia.name])
        files.extend([rej_entry, dia_entry])
        diagnosis_files.append(dia_entry)
        rejected_files.append(rej_entry)

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
            "Session A only. No chosen arms. No batch-r67.jsonl. Rights nested under "
            "meta.rights. CREATE-ONLY into 2026-09-02-final-heavy. Never 2026-08-17. "
            "Never 2026-08-30. Never training_ready. Never sim_or_real=real. Never thought keys."
        ),
        "files": files,
        "diagnosis_files": diagnosis_files,
        "rejected_files": rejected_files,
        "plants": plants,
        "anti_clone": {
            "not_live_prior_sites": prior_sites,
            "not_prior_failure_classes": prior_fcs,
        },
    }
    walk_forbidden(receipt)
    receipt_name = "diagnosis-handoff-receipt-r67.json"
    payloads[receipt_name] = create_only(DIR / receipt_name, dumps(receipt))

    for index in (1, 2, 3):
        rec = json.loads((DIR / f"rejected-0{index}-r67.json").read_text())
        walk_forbidden(rec)
        errors, warnings, kind, record_id = check_record(rec, rec["id"])
        if errors:
            raise SystemExit(f"post-write {rec['id']} errors: {errors}")
        md_path = DIR / f"diagnosis-0{index}-r67.md"
        validate_diagnosis_document(md_path.read_bytes(), label=md_path.name)
        raw = rec
        if any(k in json.dumps(raw) for k in ('"thought":', '"real":')):
            raise SystemExit(f"{rec['id']} serialized forbidden key")

    for name in names:
        path = DIR / name
        print(str(path))


if __name__ == "__main__":
    main()
