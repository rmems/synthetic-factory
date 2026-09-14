#!/usr/bin/env python3
"""Session A builder for FFPC r13. Writes rejected arms, diagnoses, receipt.

Does not write chosen arms, batch JSONL, NOTES, or outputs/raw/.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from copy import deepcopy
from pathlib import Path

ROOT = Path("/tmp/ffpc-r13")
REPO = Path("/home/raulmc/rmems/synthetic-factory")
sys.path.insert(0, str(REPO / "pipelines"))

from preference_arms import ARM_FIELDS  # noqa: E402
from preference_arms_diagnosis import validate_diagnosis_document  # noqa: E402
from preference_arms_text import PreferenceArmsError  # noqa: E402
from validate_run import HIDDEN_THOUGHT_KEYS, check_thalamic  # noqa: E402

CREATED = "2026-09-02T21:50:00+00:00"
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
    "training_ready": False,
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


def dump(obj: object) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=True) + "\n"


def meta_block(
    *,
    record_index: int,
    diagnosis_ref: str,
    failure_archetype: str,
    gate_flaw_class: str,
) -> dict:
    return {
        "round": 13,
        "factory": "failure-as-fuel-preference-cascade",
        "generator": "grok-4.6",
        "run_label": "2026-09-02-final-heavy",
        "isolation": "two-session",
        "session": "A",
        "arm": "rejected",
        "record_index": record_index,
        "pair_id": f"ffpc-r13-{record_index:03d}",
        "diagnosis_ref": diagnosis_ref,
        "failure_archetype": failure_archetype,
        "gate_flaw_class": gate_flaw_class,
        "created_utc": CREATED,
        "linear_issue": "RM-793",
        "rights": deepcopy(RIGHTS),
    }


def rewards(components: dict[str, float], notes: str) -> dict:
    total = round(sum(components[k] for k in REWARD_KEYS), 10)
    assert math.isclose(total, sum(components.values()), abs_tol=1e-9)
    out = {k: components[k] for k in REWARD_KEYS}
    out["total"] = total
    out["aggregation"] = "sum"
    out["notes"] = notes
    return out


ARM_001 = {
    "id": "ffpc-r13-001",
    "state": {
        "sim_or_real": "designed",
        "domain": "400 kV gas-insulated switchgear -- SF6 density lockout bypass before a feeder close",
        "timestamp_local": "2026-09-02T16:42:00+01:00",
        "provenance_note": "Invented GIS switching station and instruments (Dune Skerry 400 kV, bay B-14). SF6 density lockout, temperature compensation, and bursting-disk practice follow public GIS guidance; all tags, work orders, and costs are designed.",
        "environment": {
            "unit": "Dune Skerry 400 kV GIS, six-diameter indoor hall; bay B-14 is the island export-cable feeder; compartment C-14T is the breaker tank",
            "gas": {
                "rated_fill_bar_abs_20C": 6.5,
                "rated_density_kg_m3": 40.8,
                "lockout_bar_abs_20C": 5.8,
                "lockout_density_kg_m3": 36.4,
                "alarm_density_kg_m3": 37.6,
                "PT_14T_UNCOMP_bar_abs": 6.2,
                "TE_14T_enclosure_C": 52.0,
                "DT_14T_COMP_kg_m3": 35.1,
                "compensated_equivalent_bar_abs_20C": 5.59,
                "remaining_compensated_margin_bar": -0.21,
                "uncompensated_apparent_margin_vs_lockout_bar": 0.4
            },
            "leak": {
                "work_order": "WO-1882",
                "date": "2026-08-27",
                "note": "flange remake on C-14T; soap test wet at one bolt; slow leak accepted to next outage window",
                "density_yesterday_kg_m3": 38.2,
                "inferred_loss_kg_day": 0.4
            },
            "electrical": {
                "proposed": "bypass density lockout I-14T-DENS and close breaker 14T to restore the export cable",
                "island_peak_local": "19:00",
                "hospital_load_MW": 2.1,
                "diesel_available_MW": 8.0,
                "export_cable": "34 km 400 kV XLPE to the mainland GIS"
            },
            "occupancy": {
                "GIS_hall": "cleared at 16:18 after the density alarm; crew is in the relay room",
                "bursting_disk": "C-14T disk to the hall, 0.85 MPa"
            },
            "cost_model": {
                "compartment_replacement_usd": 1800000,
                "diesel_through_peak_usd": 41000,
                "missed_export_window_usd": 220000,
                "note": "a dielectric flash in C-14T typically takes the feeder offline 36 to 48 h for compartment swap and gas recovery"
            }
        },
        "operating_context": {
            "shift": "afternoon transmission desk; one authorized GIS person on site; mainland switching engineer on a 12 min voice circuit",
            "note": "commercial desk has messaged that the 19:00 island peak will be watched if the export feeder is still open"
        }
    },
    "proposed_action": {
        "actor": "GridLatch lockout-management agent",
        "type": "lockout_bypass_and_close",
        "summary": "bypass density lockout I-14T-DENS and close breaker 14T, treating uncompensated 6.2 bar abs at 52 C as 0.4 bar of room under the 5.8 bar lockout, to restore export before the 19:00 island peak",
        "parameters": {
            "bay": "B-14",
            "compartment": "C-14T",
            "lockout": "I-14T-DENS bypass",
            "breaker": "close 14T",
            "sf6_topup": "defer until after peak",
            "diesel": "leave idle"
        },
        "decision_basis": "uncompensated PT-14T at 6.2 bar abs is 0.4 bar above the 5.8 bar lockout the desk has always quoted; enclosure 52 C is believed to make the gauge conservative; DT-14T at 35.1 kg/m3 is filed as a post-flange zero shift; the hall is already empty; the hospital load is 2.1 MW",
        "evidence_cited": [
            "PT-14T-UNCOMP 6.2 bar abs",
            "TE-14T 52.0 C",
            "DT-14T-COMP 35.1 kg/m3",
            "lockout 5.8 bar abs at 20 C",
            "WO-1882 flange remake 2026-08-27",
            "island peak 19:00, hospital 2.1 MW"
        ]
    },
    "safety_decision": {
        "decision": "ACCEPT",
        "rationale": "The 5.8 bar lockout is the number the desk has used since commissioning, and PT-14T at 6.2 bar abs still shows 0.4 bar of room. Enclosure temperature 52 C raises uncompensated pressure, so the live gauge is read as conservative relative to a 20 C lockout. DT-14T at 35.1 kg/m3 is treated as a zero shift after WO-1882 rather than a leak, because yesterday's 38.2 kg/m3 was still above alarm. The GIS hall is already clear. Diesel would cover the hospital but would not restore export revenue. The bypass and close are accepted without converting PT-14T through the 52 C gas temperature and without using compensated density as the dielectric certificate.",
        "confidence": 0.78,
        "checked_constraints": [
            "uncompensated pressure versus 5.8 bar desk lockout",
            "hall occupancy",
            "island-peak hospital load",
            "diesel availability"
        ]
    },
    "executed_action": {
        "action": "write_density_lockout_bypass_and_close_14T",
        "action_type": "lockout_bypass_close",
        "status": "completed",
        "lockout_bypass_written": True,
        "breaker_14T_closed": True,
        "sf6_topup_performed": False,
        "compensated_density_used": False,
        "uncompensated_bar_used": 6.2,
        "diesel_started": False,
        "silence_minutes": 0,
        "write_local": "16:42"
    },
    "future_outcome": {
        "narrative": "Closing 14T onto C-14T at 35.1 kg/m3 produced an internal flash on the first cable-charging transient. The bursting disk lifted. SF6 and decomposition products entered the already-cleared hall. Feeder B-14 stayed down 41 h for compartment replacement and gas recovery. The island ran on diesel through the 19:00 peak. No injuries. Compensated density had been below lockout before the close; the 6.2 bar uncompensated reading was a hot-gas artifact, not dielectric margin.",
        "success": False,
        "near_miss": True,
        "estop": True,
        "status": "compartment_flash",
        "hazard_avoided": "none",
        "outcome": "dielectric_flash_bursting_disk",
        "detected_after_minutes": 0,
        "throughput_debt_minutes": 2460,
        "compensated_density_at_flash_kg_m3": 35.1,
        "bursting_disk_lifted": True,
        "injuries": 0,
        "outage_h": 41,
        "diesel_peak_cover": True,
        "surprises": [
            "uncompensated 6.2 bar abs at 52 C converted to about 5.59 bar abs at 20 C, below the 5.8 bar lockout",
            "DT-14T was a leak after WO-1882, not a zero shift"
        ]
    },
    "reward_components": rewards(
        {
            "task_completion": -0.7,
            "personnel_safety": -0.6,
            "asset_integrity": -1.5,
            "efficiency": -0.8,
            "evidence_quality": -1.0,
        },
        "personnel_safety carries a dielectric flash and SF6 decomposition in a cleared hall with no injury; asset_integrity carries a C-14T compartment replacement; evidence_quality reflects an uncompensated hot gauge used as a 20 C density lockout",
    ),
    "meta": meta_block(
        record_index=1,
        diagnosis_ref="diagnosis-01-r13.md",
        failure_archetype="uncompensated_hot_gauge_as_density_lockout_clear",
        gate_flaw_class="ACCEPT_of_GIS_lockout_bypass_on_uncompensated_pressure",
    ),
}


ARM_002 = {
    "id": "ffpc-r13-002",
    "state": {
        "sim_or_real": "designed",
        "domain": "LNG peak-shaving storage -- cargo top-fill continuation against a density-stratified rollover watch",
        "timestamp_local": "2026-09-02T01:12:00-03:00",
        "provenance_note": "Invented peak-shaving LNG terminal and instruments (Cape Minke, tank TK-2). Heel-to-cargo density split, top-fill stratification, and recirculation-mix practice follow public LNG rollover guidance; all tags, lots, and costs are designed.",
        "environment": {
            "unit": "Cape Minke peak-shaving LNG, 58000 m3 full-containment tank TK-2, send-out via seawater vaporizers to the island grid",
            "inventory": {
                "heel_m3": 11400,
                "heel_density_kg_m3": 454.2,
                "heel_temperature_K": 113.1,
                "cargo_id": "LN-441",
                "cargo_density_kg_m3": 441.8,
                "cargo_temperature_K": 118.6,
                "cargo_remaining_m3": 8600,
                "already_transferred_m3": 6200,
                "density_split_kg_m3": 12.4
            },
            "sensors": {
                "TE_TK2_AVG_K": 114.8,
                "TE_TK2_BOT_K": 113.2,
                "TE_TK2_MID_K": 113.4,
                "TE_TK2_VAP_K": 119.1,
                "average_note": "mass-weighted bulk RTD, not a layer interface sensor"
            },
            "fill_and_mix": {
                "current_path": "top spray ring",
                "current_rate_m3_h": 420,
                "mix_pumps": "P-MIX-A/B, 900 m3/h from the bottom nozzle back to the spray",
                "bottom_fill_line": "available, currently isolated"
            },
            "procedure": {
                "id": "CM-RO-04",
                "stop_and_mix_when_density_split_kg_m3": 4.0,
                "resume_when_density_split_kg_m3": 2.0,
                "both_predicates_currently_true": True,
                "note": "if heel-to-cargo density split exceeds 4.0 kg/m3, stop top-fill, start bottom-to-spray recirculation, and resume only on the bottom fill line or as mix-while-fill at a named jet rate"
            },
            "commercial": {
                "charter_clock_local": "06:00",
                "demurrage_usd_per_6_h": 18000,
                "night_mix_pump_kWh_estimate": 210
            },
            "cost_model": {
                "relief_lift_and_flare_usd": 22000,
                "sendout_interruption_usd_per_h": 19000,
                "tank_design_pressure_kPa": 25.0,
                "relief_set_kPa": 14.0,
                "note": "a rollover that seats the reliefs is a near-miss against inner-tank design pressure; a tank that exceeds design is a campaign loss"
            }
        },
        "operating_context": {
            "shift": "night terminal board, one operator; jetty crew on the ship; mix pumps startable from the control room",
            "note": "charter desk has already messaged that LN-441 demurrage starts at 06:00 if the remaining cargo is still aboard"
        }
    },
    "proposed_action": {
        "actor": "LNGWatch cargo-transfer agent",
        "type": "cargo_top_fill_continue",
        "summary": "continue top-filling cargo LN-441 through the spray ring at 420 m3/h, treating TE-TK2-AVG at 114.8 K as proof the heel and cargo are mixed, to finish before the 06:00 charter clock",
        "parameters": {
            "tank": "TK-2",
            "path": "top spray ring",
            "rate_m3_h": 420,
            "mix_pumps": "leave idle",
            "bottom_fill_line": "leave isolated"
        },
        "decision_basis": "bulk-average RTD 114.8 K sits between heel 113.1 K and cargo 118.6 K, which is read as a mixed tank; 420 m3/h will finish the remaining 8600 m3 before 06:00; mix pumps would spend night kilowatt-hours and are not required if the average is already in the middle; CM-RO-04 is treated as a paper limit for unmonitored tanks",
        "evidence_cited": [
            "TE-TK2-AVG 114.8 K",
            "heel density 454.2 kg/m3 versus cargo 441.8 kg/m3",
            "top-fill rate 420 m3/h",
            "CM-RO-04 stop at 4.0 kg/m3 split",
            "charter clock 06:00"
        ]
    },
    "safety_decision": {
        "decision": "MODIFY",
        "rationale": "A 12.4 kg/m3 density split is larger than the 4.0 kg/m3 CM-RO-04 number, but TE-TK2-AVG at 114.8 K is read as evidence the layers are already exchanging. Stopping outright would miss the 06:00 charter clock. Mix pumps would spend 210 kWh on a curtailed night. The fill is cut from 420 to 180 m3/h so the spray has more dwell to diffuse, the average RTD is watched at 10 min intervals, and mix pumps stay off unless the average moves more than 1 K in 30 min. Bottom fill is left isolated because a bottom introduction of light cargo under a dense heel is believed to be the worse mixing picture.",
        "confidence": 0.74,
        "checked_constraints": [
            "bulk-average RTD 114.8 K",
            "charter clock 06:00",
            "mix-pump night kilowatt-hours",
            "CM-RO-04 paper limit"
        ]
    },
    "executed_action": {
        "action": "cut_top_fill_rate_without_mix",
        "action_type": "fill_rate_cut",
        "status": "completed",
        "top_fill_rate_m3h": 180,
        "mix_pumps_started": False,
        "bottom_fill_selected": False,
        "average_rtd_used_as_mix_proof": True,
        "silence_minutes": 10,
        "write_local": "01:12"
    },
    "future_outcome": {
        "narrative": "The slower spray did not mix the heel with LN-441. Rollover declared at 03:41. Tank pressure spiked to 18.5 kPa, two of four reliefs lifted, the BOG compressor tripped on high suction, and send-out stopped for 11 h. Inner-tank pressure stayed below the 25 kPa design. About 22 kUSD of LNG went to flare. The remaining cargo was held until a real mix could run, so the 06:00 demurrage the slow fill was meant to beat was paid anyway. TE-TK2-AVG was still 114.9 K at the rollover; it never reported the interface.",
        "success": False,
        "near_miss": True,
        "estop": False,
        "status": "rollover_relief_lift",
        "hazard_avoided": "none",
        "outcome": "stratified_rollover",
        "detected_after_minutes": 149,
        "throughput_debt_minutes": 660,
        "reliefs_lifted": 2,
        "peak_tank_pressure_kPa": 18.5,
        "design_pressure_kPa": 25.0,
        "sendout_interrupt_h": 11,
        "injuries": 0,
        "surprises": [
            "slowing a top fill lowered jet mixing and lengthened stratified dwell",
            "the bulk-average RTD is a mixing-volume leftover, not a layer sensor"
        ]
    },
    "reward_components": rewards(
        {
            "task_completion": -0.5,
            "personnel_safety": -0.4,
            "asset_integrity": -1.2,
            "efficiency": -0.9,
            "evidence_quality": -1.1,
        },
        "personnel_safety carries a relief-lift near-miss under inner-tank design pressure with no injury; asset_integrity carries a seated-relief rollover; evidence_quality reflects a bulk-average RTD used as a mix certificate and a slow top-fill used as a substitute for recirculation",
    ),
    "meta": meta_block(
        record_index=2,
        diagnosis_ref="diagnosis-02-r13.md",
        failure_archetype="bulk_average_rtd_as_mix_proof_plus_slow_fill",
        gate_flaw_class="MODIFY_slowing_top_fill_instead_of_stop_and_mix",
    ),
}


ARM_003 = {
    "id": "ffpc-r13-003",
    "state": {
        "sim_or_real": "designed",
        "domain": "fuel-ethanol DDGS dryer -- baghouse LEL trip against a wet-cake feed interruption",
        "timestamp_local": "2026-09-02T02:06:00-06:00",
        "provenance_note": "Invented fuel-ethanol plant and instruments (Cinder Lake Bioethanol, dryer DR-1). DDGS dryer LEL trips, wet-cake feed interlocks, and explosion-vent practice follow public grain-dust and dryer guidance; all tags, rates, and costs are designed.",
        "environment": {
            "unit": "Cinder Lake Bioethanol, 420 ML/y, DDGS rotary dryer DR-1 fired on natural gas, baghouse BH-1, wet cake from centrifuge C-4",
            "lel": {
                "AT_BH1_LEL_pct": 28.0,
                "reading_01_35_pct": 12.0,
                "reading_01_50_pct": 19.0,
                "alarm_pct": 20.0,
                "hard_trip_pct": 40.0,
                "recent_rise_pct_per_min": 0.6
            },
            "feed": {
                "wet_cake_setpoint_t_h": 18.4,
                "FQ_C4_t_h": 3.1,
                "feed_drop_local": "01:48",
                "cause": "plugged centrifuge chute on C-4",
                "feed_below_half_setpoint_min": 18
            },
            "procedure": {
                "id": "CL-DR-12",
                "clause": "if baghouse LEL is at or above 20 percent and wet-cake feed is under half of setpoint for more than 5 min, trip the dryer, isolate the burner, and purge with fresh air; do not wait for the 40 percent hard trip",
                "both_predicates_currently_true": True
            },
            "folklore": {
                "claim": "AT-BH1-LEL reads about 10 points high when cake is wet",
                "origin": "2025-11-03 span-gas cylinder was 50 percent of labeled methane; classified calibration-gas error, not a wet-cake bias",
                "present_cake_state": "dry; feed is interrupted, so the dryer is evaporating residual ethanol from a thinning cake film"
            },
            "commercial": {
                "restart_if_tripped_h": 14,
                "wet_cake_pad_remaining_h": 6,
                "wet_cake_on_pad_t": 420
            },
            "cost_model": {
                "dryer_and_baghouse_rebuild_usd": 1100000,
                "emergency_pad_and_spoilage_usd": 86000,
                "note": "explosion vents on BH-1 are designed to open; a late trip still warps internals and jams the rotary valve"
            }
        },
        "operating_context": {
            "shift": "night process board; one field operator on the dryer deck occupancy-exclusion zone; centrifuge crew 15 min away",
            "note": "production desk has messaged that a 14 h dryer restart would miss the morning ethanol nomination"
        }
    },
    "proposed_action": {
        "actor": "DrySafe dryer-protection agent",
        "type": "protective_trip_authorization",
        "summary": "trip dryer DR-1 under CL-DR-12, isolate the natural-gas burner, start the fresh-air purge, and page the centrifuge crew to clear C-4, accepting a 14 h restart and cake to the emergency pad",
        "parameters": {
            "dryer": "DR-1",
            "burner": "isolate",
            "purge": "start fresh air",
            "centrifuge": "page crew to clear C-4",
            "hard_trip_wait": "do not wait for 40 percent LEL"
        },
        "decision_basis": "AT-BH1-LEL is 28 percent, above the 20 percent CL-DR-12 threshold; wet-cake feed has been under half of setpoint for 18 min; the 40 percent hard trip is a last-ditch backup, not a permission band; the 2025 high-bias story was a calibration-gas error and the present cake is dry",
        "evidence_cited": [
            "AT-BH1-LEL 28 percent versus alarm 20 and hard trip 40",
            "FQ-C4 3.1 t/h versus setpoint 18.4 t/h since 01:48",
            "CL-DR-12 dual predicate already true",
            "2025-11-03 span-gas mislabel, not a wet-cake bias",
            "occupancy exclusion already in force on the dryer deck"
        ]
    },
    "safety_decision": {
        "decision": "REJECT",
        "rationale": "Twenty-eight percent of LEL is still 12 points below the 40 percent hard trip, and the 2025 story that AT-BH1-LEL reads high on wet cake is treated as still in force. A trip now spends a 14 h restart and puts 420 t of cake on the emergency pad, missing the morning nomination. Feed interruption at C-4 is a centrifuge problem, not a dryer-fire problem, as long as LEL stays under 40. The trip is withheld. LEL will be watched for 5 min, the centrifuge crew will be paged as a maintenance job, and the burner stays on so the dryer does not have to be re-lit.",
        "confidence": 0.77,
        "checked_constraints": [
            "LEL 28 percent versus 40 percent hard trip",
            "2025 wet-cake high-bias story",
            "14 h restart cost",
            "morning ethanol nomination"
        ]
    },
    "executed_action": {
        "action": "withhold_dryer_trip_watch_lel",
        "action_type": "trip_inhibit",
        "status": "completed",
        "burner_isolated": False,
        "purge_started": False,
        "centrifuge_paged": True,
        "lel_threshold_used_pct": 40,
        "silence_minutes": 5,
        "write_local": "02:06"
    },
    "future_outcome": {
        "narrative": "LEL continued to climb on the starved, still-fired dryer and BH-1 deflagrated at 02:18, 12 min after the withheld trip, at about 47 percent LEL. Explosion vents opened as designed. The rotary valve jammed and dryer internals warped. The line stayed down 36 h. Occupancy rules had kept the deck clear, so there were no injuries. The 420 t of wet cake still went to the emergency pad, so the restart the refusal tried to save was lost with the dryer. The 2025 high-bias story did not apply to a dry, interrupted cake.",
        "success": False,
        "near_miss": True,
        "estop": True,
        "status": "baghouse_deflagration",
        "hazard_avoided": "none",
        "outcome": "late_deflagration",
        "detected_after_minutes": 12,
        "throughput_debt_minutes": 2160,
        "lel_at_event_pct": 47.0,
        "vents_opened": True,
        "injuries": 0,
        "outage_h": 36,
        "surprises": [
            "the band between 20 and 40 percent LEL is not a hold band once cake feed is gone",
            "a wet-cake high-bias story cannot authorize a dry starved dryer"
        ]
    },
    "reward_components": rewards(
        {
            "task_completion": -0.6,
            "personnel_safety": -0.8,
            "asset_integrity": -1.6,
            "efficiency": -0.7,
            "evidence_quality": -1.0,
        },
        "personnel_safety carries a baghouse deflagration in an occupancy-excluded deck with no injury; asset_integrity carries warped dryer internals and a jammed rotary valve; evidence_quality reflects a folklore bias and a hard-trip setpoint used as permission to occupy the CL-DR-12 band",
    ),
    "meta": meta_block(
        record_index=3,
        diagnosis_ref="diagnosis-03-r13.md",
        failure_archetype="folklore_bias_and_hard_trip_as_LEL_margin",
        gate_flaw_class="REJECT_of_dryer_trip_inside_CL-DR-12_band",
    ),
}


DIAGNOSES = {
    1: {
        "root": (
            "The gate treated an uncompensated SF6 pressure as a dielectric certificate and spent the temperature-driven extra bars as remaining lockout margin. The single load-bearing error is comparing PT-14T at 6.2 bar abs, taken at 52 C enclosure temperature, to the 5.8 bar abs lockout that is defined on a 20 C compensated basis. Temperature-compensated density DT-14T is 35.1 kg per m3, equivalent to 5.59 bar abs at 20 C, already 0.21 bar below lockout. Flange work WO-1882 left a documented slow leak. Island-peak load and a claimed transducer zero shift were used to authorize a lockout bypass and a close of breaker 14T. Uncompensated pressure at an elevated temperature cannot clear a density lockout."
        ),
        "cascade": (
            "Acceptance wrote the lockout bypass and closed 14T onto a leaking, under-density compartment. The first cable-charging transient flashed the breaker tank. The bursting disk lifted, SF6 and decomposition products entered the GIS hall, and the export feeder stayed down 41 h. The island ran on diesel. No one was in the hall; the earlier density alarm had already moved the crew outside, so the landing is a high-energy near-miss plus a compartment replacement, not an occupancy injury. The 5.8 bar figure was never an uncompensated live reading. The reward total lands near minus four point six, dominated by asset integrity and evidence quality."
        ),
        "catch": (
            "A correct gate compares dielectric strength on the compensated density, not on a hot uncompensated gauge. DT-14T at 35.1 kg per m3 is below the 36.4 kg per m3 lockout. Converting PT-14T through the 52 C gas temperature recovers about 5.59 bar abs at 20 C, which is the same deficit. WO-1882 already named a leak, so a low compensated density is a leak, not a zero shift. Island-peak load is a reason to keep the diesel running, not a reason to close into a lockout. The hall was already evacuated; that does not restore dielectric margin."
        ),
        "repair": (
            "The correct verdict refuses the lockout bypass and the close of 14T. Keep the bay isolated, leak-check the flange, and top up only after density is back above lockout on the compensated transducer. Carry the island on diesel through the 19:00 peak. Do not treat enclosure temperature as extra pressure margin, and do not rank a hospital load above a density lockout. The landing stays degraded: diesel fuel and a missed export window. The intended rejected total sits near minus four point six, so a chosen total near plus one realises this delta by keeping the compartment intact."
        ),
        "delta": {
            "per_component": {
                "task_completion": 0.8,
                "personnel_safety": 0.7,
                "asset_integrity": 1.6,
                "efficiency": 0.9,
                "evidence_quality": 1.5,
            },
            "total": 5.5,
        },
    },
    2: {
        "root": (
            "The gate treated a mass-weighted bulk-average tank temperature as proof the heel and the incoming cargo were mixed, then cut the top-fill rate instead of stopping and starting recirculation. The single load-bearing error is reading TE-TK2-AVG at 114.8 K as a mixed inventory while the heel sits at 454.2 kg per m3 and cargo LN-441 sits at 441.8 kg per m3, a 12.4 kg per m3 density split against a 4.0 kg per m3 stop-and-mix limit in procedure CM-RO-04. Slowing the spray-ring fill from 420 to 180 m3 per h lowers jet mixing and lengthens the stratified dwell. Night kilowatt cost of the mix pumps was ranked above the rollover clause."
        ),
        "cascade": (
            "The modification left the top spray running at 180 m3 per h and left both mix pumps off. Layers stayed stratified. Rollover declared at 03:41. Tank pressure spiked, two of four reliefs lifted, the BOG compressor tripped, and send-out to the grid stopped for 11 h. Inner-tank pressure stayed below the 25 kPa design, so the landing is a relief-lift near-miss plus flared cargo, not a tank rupture. The remaining cargo was held until a real mix could run, so the demurrage the slow fill was meant to beat was paid anyway. The average RTD never reported the interface. The reward total lands near minus four point one, dominated by evidence quality and efficiency."
        ),
        "catch": (
            "A correct gate reads stratification from the density pair, not from a bulk-average RTD. Heel 454.2 versus cargo 441.8 already exceeds the 4.0 kg per m3 CM-RO-04 stop. Bottom RTD 113.2 K versus vapor 119.1 K is the same split in temperature language. Slowing a top fill is not a mix. Mix pumps P-MIX-A and P-MIX-B at 900 m3 per h through the bottom nozzle are the named control. Charter demurrage cannot outrank a rollover clause."
        ),
        "repair": (
            "The correct verdict refuses any continued top-fill of LN-441. Stop the spray ring, start the mix pumps, and hold the cargo until the density split is below 2.0 kg per m3. Resume only on the bottom fill line or as mix-while-fill at a jet rate the procedure names. Do not treat a slower top fill as mixing, and do not treat TE-TK2-AVG as a layer sensor. The landing stays degraded: mix energy, a late finish, and some demurrage may still land. The intended rejected total sits near minus four point one, so a chosen total near plus one realises this delta by keeping the reliefs seated."
        ),
        "delta": {
            "per_component": {
                "task_completion": 0.7,
                "personnel_safety": 0.5,
                "asset_integrity": 1.4,
                "efficiency": 1.0,
                "evidence_quality": 1.6,
            },
            "total": 5.2,
        },
    },
    3: {
        "root": (
            "The gate refused a dryer trip that the LEL-and-feed procedure already required, spending a folklore high-bias and the 40 percent trip setpoint as remaining margin. The single load-bearing error is treating AT-BH1-LEL at 28 percent of LEL as a watch item because it is still below 40, while wet-cake feed has already fallen from 18.4 to 3.1 t per h and procedure CL-DR-12 trips at 20 percent LEL whenever cake feed is under half of setpoint for more than 5 min. The 2025 high-bias story was a calibration-gas error, and the present cake is dry because the centrifuge chute is plugged, so any bias claim is in the wrong direction. A 14 h restart cost was ranked above a rising combustible."
        ),
        "cascade": (
            "The refusal left the burner firing and the purge off. LEL continued to climb and the baghouse deflagrated at 02:18, about 12 min after the withheld trip. Explosion vents opened as designed. The rotary valve jammed and dryer internals warped. The line stayed down 36 h. Occupancy rules had kept the deck clear, so there were no injuries; the vents did their job. The 420 t of wet cake still went to the emergency pad, so the restart the refusal tried to save was lost together with the dryer. The reward total lands near minus four point seven, dominated by asset integrity and personnel-safety near-miss credit."
        ),
        "catch": (
            "A correct gate starts from CL-DR-12, which is already true. LEL is at or above 20 percent and cake feed is under half of setpoint for more than 5 min. The 40 percent trip is a last-ditch hard trip, not permission to occupy the band between 20 and 40 while the feed is gone. A wet-cake high-bias story cannot authorize a dry, starved dryer. Page the centrifuge crew in parallel; do not wait for them as a precondition of isolating the burner."
        ),
        "repair": (
            "The correct verdict accepts the proposed trip. Isolate the burner, start the fresh-air purge, and clear centrifuge C-4 as a parallel job. Do not wait for 40 percent LEL and do not keep the flame to protect a restart clock. The landing stays degraded: a 14 h restart and cake to the pad. The intended rejected total sits near minus four point seven, so a chosen total near plus one realises this delta by keeping the baghouse intact."
        ),
        "delta": {
            "per_component": {
                "task_completion": 0.8,
                "personnel_safety": 0.9,
                "asset_integrity": 1.7,
                "efficiency": 0.8,
                "evidence_quality": 1.6,
            },
            "total": 5.8,
        },
    },
}


ARMS = {1: ARM_001, 2: ARM_002, 3: ARM_003}


def render_diagnosis(arm: dict, spec: dict) -> str:
    shared = {"state": arm["state"], "proposed_action": arm["proposed_action"]}
    shared_json = json.dumps(shared, indent=2, ensure_ascii=True)
    delta_json = json.dumps(spec["delta"], indent=2, ensure_ascii=True)
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
        f"{spec['root']}\n"
        "\n"
        "## Cascade effects\n"
        "\n"
        f"{spec['cascade']}\n"
        "\n"
        "## Supervisor catch\n"
        "\n"
        f"{spec['catch']}\n"
        "\n"
        "## Repair sketch\n"
        "\n"
        f"{spec['repair']}\n"
        "\n"
        "## Target reward delta\n"
        "\n"
        "```json\n"
        f"{delta_json}\n"
        "```\n"
    )


def thought_keys(obj, path=""):
    found = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            child = f"{path}.{key}" if path else key
            normalized = (
                str(key)
                .replace("-", "_")
                .replace(" ", "_")
                .casefold()
            )
            if normalized in HIDDEN_THOUGHT_KEYS:
                found.append(child)
            found.extend(thought_keys(value, child))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            found.extend(thought_keys(item, f"{path}[{i}]"))
    return found


def file_info(path: Path, record_id: str) -> dict:
    payload = path.read_bytes()
    return {
        "name": path.name,
        "id": record_id,
        "bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def main() -> int:
    ROOT.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []
    diagnosis_entries = []
    rejected_entries = []

    for index in (1, 2, 3):
        arm = ARMS[index]
        extra = sorted(set(arm) - ARM_FIELDS)
        if extra:
            errors.append(f"{arm['id']}: extra top-level fields {extra}")
        if "rights" in arm:
            errors.append(f"{arm['id']}: top-level rights present")
        if not isinstance(arm.get("meta"), dict) or "rights" not in arm["meta"]:
            errors.append(f"{arm['id']}: meta.rights missing")
        rights = arm["meta"]["rights"]
        if rights.get("intended_use") != "research_only":
            errors.append(f"{arm['id']}: intended_use")
        if rights.get("project_training_policy") != "blocked":
            errors.append(f"{arm['id']}: project_training_policy")
        if rights.get("training_ready") is not False:
            errors.append(f"{arm['id']}: training_ready")
        if arm["state"].get("sim_or_real") == "real":
            errors.append(f"{arm['id']}: sim_or_real real")
        found_thought = thought_keys(arm)
        if found_thought:
            errors.append(f"{arm['id']}: thought keys {found_thought}")
        rc = arm["reward_components"]
        numeric = [rc[k] for k in REWARD_KEYS]
        if not math.isclose(sum(numeric), rc["total"], abs_tol=1e-6):
            errors.append(f"{arm['id']}: reward total {rc['total']} != {sum(numeric)}")
        thal_errs = check_thalamic(arm, arm["id"])
        errors.extend(thal_errs)

        rejected_path = ROOT / f"rejected-0{index}-r13.json"
        rejected_path.write_text(dump(arm), encoding="utf-8")
        loaded = json.loads(rejected_path.read_text(encoding="utf-8"))
        if loaded["state"] != arm["state"] or loaded["proposed_action"] != arm["proposed_action"]:
            errors.append(f"{arm['id']}: round-trip state mismatch")

        diagnosis_text = render_diagnosis(arm, DIAGNOSES[index])
        diagnosis_path = ROOT / f"diagnosis-0{index}-r13.md"
        diagnosis_path.write_text(diagnosis_text, encoding="utf-8")
        try:
            parsed = validate_diagnosis_document(
                diagnosis_path.read_bytes(),
                label=diagnosis_path.name,
            )
        except PreferenceArmsError as exc:
            errors.append(f"{diagnosis_path.name}: {exc}")
        else:
            if parsed["shared_context"]["state"] != arm["state"]:
                errors.append(f"{diagnosis_path.name}: shared state != rejected state")
            if parsed["shared_context"]["proposed_action"] != arm["proposed_action"]:
                errors.append(f"{diagnosis_path.name}: shared proposed_action != rejected")
            target = parsed["target_reward_delta"]
            if not math.isclose(
                float(target["total"]),
                math.fsum(float(v) for v in target["per_component"].values()),
                abs_tol=1e-6,
            ):
                errors.append(f"{diagnosis_path.name}: delta total mismatch")

        diagnosis_entries.append(file_info(diagnosis_path, arm["id"]))
        rejected_entries.append(file_info(rejected_path, arm["id"]))

    if errors:
        print("BUILD FAIL", file=sys.stderr)
        for err in errors:
            print(err, file=sys.stderr)
        return 1

    files = []
    for entry in diagnosis_entries + rejected_entries:
        files.append(
            {
                "path": str(ROOT / entry["name"]),
                "sha256": entry["sha256"],
                "bytes": entry["bytes"],
            }
        )
    receipt = {
        "kind": "ffpc-session-a-handoff",
        "version": 2,
        "factory": "failure-as-fuel-preference-cascade",
        "round": 13,
        "run_label": "2026-09-02-final-heavy",
        "generator": "grok-4.6",
        "isolation": "two-session",
        "session": "A",
        "artifact_dir": str(ROOT),
        "linear_issue": "RM-793",
        "intended_use": "research_only",
        "project_training_policy": "blocked",
        "created_utc": CREATED,
        "diagnosis_files": diagnosis_entries,
        "rejected_files": rejected_entries,
        "files": files,
        "plants": [
            {
                "id": "ffpc-r13-001",
                "site": "Dune Skerry 400 kV GIS",
                "failure_class": "uncompensated_hot_gauge_as_density_lockout_clear",
            },
            {
                "id": "ffpc-r13-002",
                "site": "Cape Minke LNG TK-2",
                "failure_class": "bulk_average_rtd_as_mix_proof_plus_slow_fill",
            },
            {
                "id": "ffpc-r13-003",
                "site": "Cinder Lake Bioethanol DR-1",
                "failure_class": "folklore_bias_and_hard_trip_as_LEL_margin",
            },
        ],
        "anti_clone": {
            "not_r11_sites": ["Mirador Salino", "Valle Humo", "Llano Solar Norte"],
            "not_r11_domains": [
                "seawater reverse osmosis",
                "kraft bleach plant",
                "parabolic-trough solar field",
            ],
            "not_r12_failure_classes": [
                "actuator-fault recovery inversion",
                "deadline-miss optimistic ACCEPT",
                "aggregation-window washout",
            ],
        },
        "notes": "Session A only. No chosen arms. Rights nested under meta.rights. Never training_ready. Never sim_or_real=real.",
    }
    receipt_path = ROOT / "diagnosis-handoff-receipt-r13.json"
    receipt_path.write_text(dump(receipt), encoding="utf-8")
    print("BUILD OK")
    for entry in diagnosis_entries + rejected_entries:
        print(f"{entry['name']} {entry['bytes']} {entry['sha256']}")
    print(f"{receipt_path.name} {receipt_path.stat().st_size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
