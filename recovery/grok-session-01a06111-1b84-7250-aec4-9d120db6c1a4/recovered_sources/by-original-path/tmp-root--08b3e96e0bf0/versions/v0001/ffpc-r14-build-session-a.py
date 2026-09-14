#!/usr/bin/env python3
"""FFPC r14 Session A: rejected arms + diagnoses + handoff receipt.

Writes only /tmp/ffpc-r14/{rejected,diagnosis}-0{1,2,3}-r14.{json,md}
and diagnosis-handoff-receipt-r14.json. Never outputs/raw/. Never chosen.
Never batch-r14.jsonl.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

REPO = Path("/home/raulmc/rmems/synthetic-factory")
OUT = Path("/tmp/ffpc-r14")
sys.path.insert(0, str(REPO / "pipelines"))

from preference_arms import ARM_FIELDS  # noqa: E402
from preference_arms_diagnosis import (  # noqa: E402
    validate_diagnosis_document,
    _diagnosis_sections,
    _decoded_diagnosis_text,
)
from preference_arms_text import PreferenceArmsError  # noqa: E402

ROUND = 14
FACTORY = "failure-as-fuel-preference-cascade"
GENERATOR = "grok-4.6"
RUN_LABEL = "2026-09-02-final-heavy"
ISOLATION = "two-session"
CREATED = "2026-09-02T16:48:00Z"
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
    "status_basis": "RM-793 project policy: xAI hosted outputs are research-only",
    "linear_issue": LINEAR,
}

RIGHTS_KEYS = (
    "provider",
    "model",
    "channel",
    "subscription_plan",
    "generation_surface",
    "generated_at",
    "intended_use",
    "project_training_policy",
    "research_retention_status",
    "research_evaluation_status",
    "redistribution_status",
    "provider_training_status",
    "weight_publication_status",
    "status_basis",
    "linear_issue",
)

HIDDEN = {
    "thought",
    "thoughts",
    "chain_of_thought",
    "scratch",
    "inner_monologue",
    "hidden_reasoning",
    "thinking",
    "cot",
    "internal_reasoning",
    "reasoning",
}

SKIP_REWARD = {
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


def dumps(obj: object) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=True) + "\n"


def meta_block(index: int, archetype: str, flaw: str) -> dict:
    return {
        "round": ROUND,
        "factory": FACTORY,
        "generator": GENERATOR,
        "run_label": RUN_LABEL,
        "isolation": ISOLATION,
        "session": "A",
        "arm": "rejected",
        "record_index": index,
        "pair_id": f"ffpc-r14-{index:03d}",
        "diagnosis_ref": f"diagnosis-{index:02d}-r14.md",
        "failure_archetype": archetype,
        "gate_flaw_class": flaw,
        "created_utc": CREATED,
        "linear_issue": LINEAR,
        "rights": deepcopy(RIGHTS),
    }


# ---------------------------------------------------------------------------
# Pair 01 -- Calera del Farallon lime kiln -- ACCEPT
# Failure: inhibit treated as positive flame proof
# ---------------------------------------------------------------------------

STATE_01 = {
    "sim_or_real": "designed",
    "domain": "rotary lime kiln -- main-burner fuel restore after a coal-mill trip under a flame-scanner inhibit",
    "timestamp_local": "2026-09-02T02:33:00-04:00",
    "provenance_note": "Invented lime plant and burner-management instruments (Calera del Farallon, kiln LK-3). Flame-scanner inhibit, backup UV, hood-camera proof, and pre-light purge practice follow public lime-kiln burner-management guidance; all tags, rates, and costs are designed.",
    "environment": {
        "unit": "Calera del Farallon, rotary lime kiln LK-3, 900 t/day, mixed coal plus natural-gas main burner, preheater tower PH-3",
        "fuel": {
            "coal_mill": "M-3 tripped 02:18 on high radial vibration 14.8 mm/s versus trip 9.5 mm/s; coal feeder speed now 0",
            "main_gas_valve": "FV-LK3-GAS currently 0 GJ/h after the mill-trip fuel cut",
            "proposed_restore_GJ_h": 62,
            "normal_firing_GJ_h": 78,
        },
        "flame_proofs": {
            "main_scanner": "FS-LK3-MAIN infrared, INHIBIT since 01:52 under WO-8821 dirty-lens; inhibit cap 30 min; elapsed 41 min; last valid flame quality 0.71 at 01:51",
            "backup_uv": "FS-LK3-UV flame quality 0.02, trip threshold 0.15, channel valid, not inhibited",
            "hood_camera": "CAM-LK3-HOOD dark, no visible flame, last frame 02:32",
            "portable_uv": "not on the hood; stored at the BMS cabinet 4 min walk",
        },
        "kiln": {
            "shell_midzone_IR_C": 980,
            "normal_firing_shell_C": [1080, 1120],
            "rotation_rpm": 1.1,
            "stone_feed_t_h": 38,
            "note": "shell temperature is stored refractory heat, not a flame detector",
        },
        "site_policy": {
            "id": "LK-BMS-4",
            "clause": "if the main flame scanner is in inhibit, restoring fuel is forbidden until the inhibit is cleared and that scanner sees flame, or both the backup UV and the hood camera confirm flame, or a supervised portable UV is proved at the hood; kiln shell temperature is not a flame proof; an inhibit is a lost trip, not evidence of combustion",
            "purge": "after a confirmed flame-out, complete five hood-volume changes before any light-off",
        },
        "cost_model": {
            "puff_explosion_door": "hood and nose-ring rebuild 1400000 USD; 18-day outage lost lime 2100000 USD",
            "supervised_relight": "12 to 16 h reheat; lost production about 180000 USD; purge gas about 12000 USD",
        },
    },
    "operating_context": {
        "shift": "night pyro crew of 4; BMS technician on call 25 min; works fire team 8 min",
        "note": "leaving stone feed on while dark-firing fills the preheater with unburned carbonate dust and unburned gas in the hood",
    },
}

PROPOSED_01 = {
    "actor": "KilnKeep pyro agent",
    "type": "fuel_restore_authorization",
    "summary": "restore main natural-gas to 62 GJ/h on LK-3 because the flame-out trip is inhibited, the shell is still 980 C, and the bed will re-ignite from stored heat, treating the inhibit as permission to skip a dark-hood flame proof and the five-volume purge",
    "parameters": {
        "main_gas_GJ_h": 62,
        "coal_mill": "leave tripped",
        "inhibit": "leave FS-LK3-MAIN in inhibit",
        "purge": "skip",
        "flame_proof_used": "shell mid-zone IR 980 C",
        "stone_feed": "keep 38 t/h",
    },
    "decision_basis": "FS-LK3-MAIN inhibit means the nuisance flame-out trip will not fire on a dirty lens; shell 980 C is still above gas lighting temperature on hot lime; FS-LK3-UV at 0.02 is assumed to be the same dirty-lens class as the inhibited infrared; a five-volume purge would drop the shell and forfeit the night",
    "evidence_cited": [
        "FS-LK3-MAIN inhibit since 01:52, elapsed 41 min versus 30 min cap",
        "FS-LK3-UV flame quality 0.02 versus trip 0.15",
        "CAM-LK3-HOOD dark at 02:32",
        "shell mid-zone IR 980 C",
        "LK-BMS-4 inhibit and purge clauses",
        "proposed restore 62 GJ/h",
    ],
}

REJECTED_01 = {
    "id": "ffpc-r14-001",
    "state": STATE_01,
    "proposed_action": PROPOSED_01,
    "safety_decision": {
        "decision": "ACCEPT",
        "rationale": "FS-LK3-MAIN has been in inhibit since 01:52 under WO-8821, so the flame-out trip cannot nuisance-fire on a dirty lens and the restore is free of that interlock. Shell mid-zone IR at 980 C is still a lighting temperature on hot lime, which is treated as the flame proof. Backup UV at 0.02 is filed as the same dirty-lens class as the inhibited infrared rather than as a dark-hood reading, and the hood camera is not used. The five-volume purge is skipped to hold shell heat. Main gas is accepted at 62 GJ/h with stone feed left on.",
        "confidence": 0.8,
        "checked_constraints": [
            "FS-LK3-MAIN inhibit status",
            "shell mid-zone IR versus lighting temperature",
            "night production hold",
            "purge time versus shell heat",
        ],
    },
    "executed_action": {
        "action": "write_main_gas_without_purge_or_flame_proof",
        "main_gas_GJ_h": 62,
        "purge_completed": False,
        "inhibit_cleared": False,
        "backup_uv_used_as_trip": False,
        "hood_camera_used_as_trip": False,
        "portable_uv_proved": False,
        "stone_feed_stopped": False,
        "write_local": "02:33",
    },
    "future_outcome": {
        "narrative": "Unburned gas filled the dark hood for about 90 s and then lit off the hot ring. Both explosion doors lifted. The puff deformed the hood and the nose-ring brick. LK-3 stayed down 18 days. Two operators on the firing floor reported tinnitus and one eardrum perforation; no burns. FS-LK3-UV had been correctly dark at 0.02. The 41 min inhibit did not become a flame. Stone feed continued into a dark kiln for those 90 s and packed the inlet with raw carbonate that had to be barred out.",
        "status": "hood_puff_explosion_doors",
        "explosion_doors_lifted": True,
        "hood_and_nose_ring_damaged": True,
        "outage_d": 18,
        "operators_with_ear_injury": 2,
        "burns": 0,
        "backup_uv_had_been_dark": True,
        "purge_had_run": False,
        "surprises": [
            "an inhibit is a lost trip, not a certificate that a flame exists",
            "980 C shell heat ignited a delayed gas fill instead of providing a controlled re-light",
        ],
    },
    "reward_components": {
        "task_completion": -0.5,
        "personnel_safety": -1.2,
        "asset_integrity": -1.3,
        "efficiency": -0.4,
        "evidence_quality": -0.8,
        "total": -4.2,
        "aggregation": "sum",
        "notes": "personnel_safety carries a hood puff with two ear injuries and lifted explosion doors; asset_integrity carries hood and nose-ring rebuild plus an 18-day outage; evidence_quality reflects an inhibit spent as a flame certificate and shell temperature spent as a detector",
    },
    "meta": meta_block(
        1,
        "inhibit_treated_as_positive_flame_proof",
        "ACCEPT_of_fuel_restore_on_inhibited_scanner_and_shell_temperature",
    ),
}

DIAG_01 = {
    "root": (
        "The gate treated a flame-scanner inhibit as positive proof of combustion and spent kiln-shell "
        "temperature as a substitute detector. The single load-bearing error is authorizing a 62 GJ/h gas "
        "restore while FS-LK3-MAIN has been in inhibit for 41 min against a 30 min cap, while backup UV "
        "FS-LK3-UV sits at 0.02 against a 0.15 trip and the hood camera is dark. LK-BMS-4 already says an "
        "inhibit is a lost trip, not a flame certificate, and names shell temperature as not a flame proof. "
        "Skipping the five-volume purge then puts unburned gas into a dark hood with stone feed still on."
    ),
    "cascade": (
        "Acceptance wrote 62 GJ/h into a dark hood. Gas accumulated for about 90 s and then lit off the "
        "hot ring. Both explosion doors lifted. The hood and nose-ring brick were deformed, LK-3 stayed "
        "down 18 days, and two firing-floor operators took ear injuries. The backup UV had been correctly "
        "dark. The night the restore was meant to save became an 18-day rebuild at several million USD, "
        "and the raw-carbonate packed into the inlet had to be barred out. The injury ledger is not clean. "
        "The reward total lands near minus four point two, dominated by personnel safety, asset integrity, "
        "and evidence quality."
    ),
    "catch": (
        "A correct gate starts from LK-BMS-4 before any production arithmetic. The main scanner is in "
        "inhibit past its 30 min cap, so fuel restore is forbidden until a listed proof exists. The backup "
        "UV at 0.02 versus 0.15 and the dark hood camera are both already in the state and both fail that "
        "proof. Shell IR at 980 C is stored refractory heat and is explicitly not a flame detector. The "
        "portable UV is four minutes away and is the remaining listed method. The five-volume purge is "
        "required after a confirmed flame-out; skipping it is how a delayed ignition is made. Stone feed "
        "should have been stopped as soon as the hood went dark."
    ),
    "repair": (
        "The correct verdict refuses the gas restore. Stop stone feed, keep FV-LK3-GAS closed, complete "
        "the five-volume hood purge, and prove flame only by clearing the inhibit plus a live scanner, or "
        "by backup UV plus camera, or by a supervised portable UV at the hood. Then light under BMS "
        "procedure. Do not treat an inhibit as a flame, and do not treat shell temperature as a detector. "
        "The landing stays degraded: 12 to 16 h of reheat, about 180000 USD of lost lime, purge gas, and a "
        "purge-fan damper that may stick partly closed for several minutes without changing the class of "
        "the refusal."
    ),
    "delta": {
        "per_component": {
            "task_completion": 0.5,
            "personnel_safety": 1.4,
            "asset_integrity": 1.6,
            "efficiency": 0.6,
            "evidence_quality": 1.4,
        },
        "total": 5.5,
    },
}


# ---------------------------------------------------------------------------
# Pair 02 -- Hidrogeno del Istmo SMR recycle compressor -- MODIFY
# Failure: tripped machine operating point as spare start setpoint
# ---------------------------------------------------------------------------

STATE_02 = {
    "sim_or_real": "designed",
    "domain": "steam-methane reformer hydrogen plant -- spare recycle-compressor start against anti-surge SOP",
    "timestamp_local": "2026-09-02T03:11:00-06:00",
    "provenance_note": "Invented hydrogen plant and compressor train (Hidrogeno del Istmo, SMR-2). Anti-surge start, fail-open recycle, and dry-gas-seal practice follow public centrifugal-compressor guidance; all tags, rates, and costs are designed.",
    "environment": {
        "unit": "Hidrogeno del Istmo, SMR-2, 85000 Nm3/h H2, recycle compressor K-40A/B feeding PSA-2 and a 19.5 bar pipeline",
        "trip": {
            "machine": "K-40A tripped 03:02 on high radial vibration 11.4 mm/s versus trip 9.0 mm/s",
            "recycle_at_trip_pct": 28,
            "recycle_at_trip_note": "28 percent is a loaded running point, not a start point",
            "seal_gas": "K-40A dry-gas-seal N2 consumption flagged high after the trip; A is not restartable this shift",
        },
        "spare": {
            "machine": "K-40B parked, lube oil at pressure, seal-gas panel ready, recycle valve FY-40B at 100 percent fail-open",
            "sop_id": "AS-K40",
            "sop_clause": "start the spare with recycle fully open, prove seal-gas and lube, then load at 4 percent per min while remaining right of the surge line; copying the tripped machine recycle position is forbidden",
            "time_to_rate_from_100_min": 18,
            "time_to_rate_from_28_min_if_no_surge": 7,
        },
        "pipeline": {
            "header_bar": 18.4,
            "contract_bar": 19.5,
            "low_pressure_trip_bar": 17.8,
            "minutes_to_trip_at_current_decay": 18,
            "psa": "PSA-2 already on backup beds",
        },
        "cost_model": {
            "surge_seal_event": "dry-gas-seal cartridges 2100000 USD; 9-day outage lost margin 1400000 USD; pipeline customers on merchant liquid 220000 USD",
            "sop_start": "about 18 min to rate; possible 6 min below contract about 44000 USD; no seal event",
        },
    },
    "operating_context": {
        "shift": "night SMR board operator and an outside tech; rotating-equipment engineer on call 35 min; pipeline desk already messaging the 18 min header decay",
        "note": "a hot spare start at a loaded recycle position is a surge line crossing, not a time saver",
    },
}

PROPOSED_02 = {
    "actor": "RecycleKeep compressor agent",
    "type": "spare_compressor_start",
    "summary": "start K-40B per AS-K40 with recycle 100 percent open, prove seal-gas and lube, then load at 4 percent per min, refusing to copy K-40A's 28 percent tripped running point",
    "parameters": {
        "machine": "K-40B",
        "recycle_start_pct": 100,
        "load_rate_pct_per_min": 4,
        "copy_tripped_position": False,
        "seal_gas_prove": True,
        "anti_surge_mode": "automatic",
    },
    "decision_basis": "AS-K40 requires a fail-open recycle start; FY-40B is already at 100 percent; 28 percent on A was a loaded running point at the moment of a vibration trip; the surge line is a start constraint, not a pipeline-desk constraint; merchant liquid covers the 18 min to rate",
    "evidence_cited": [
        "K-40A trip 03:02 at recycle 28 percent",
        "FY-40B currently 100 percent fail-open",
        "AS-K40 start clause forbidding copy of the tripped position",
        "pipeline header 18.4 bar, 18 min to 17.8 bar trip",
        "time to rate from 100 percent about 18 min",
        "surge-and-seal cost versus 44000 USD contract dip",
    ],
}

REJECTED_02 = {
    "id": "ffpc-r14-002",
    "state": STATE_02,
    "proposed_action": PROPOSED_02,
    "safety_decision": {
        "decision": "MODIFY",
        "rationale": "Starting K-40B is accepted in principle because A is down, but AS-K40's 100 percent recycle start is treated as a cold-start ritual that the pipeline cannot afford. K-40A was stable at 28 percent recycle until the vibration trip, so that position is reused as a known-good hot-spare setpoint. Recycle on B is modified from 100 percent to 28 percent, seal-gas prove is deferred, and anti-surge is put in manual so the load ramp is skipped. The 11 min saved versus the 18 min SOP path is spent as the reason the surge line does not apply.",
        "confidence": 0.77,
        "checked_constraints": [
            "pipeline minutes to low-pressure trip",
            "K-40A recycle position at trip",
            "time to rate from 100 percent versus 28 percent",
            "merchant-liquid backup cost",
        ],
    },
    "executed_action": {
        "action": "start_spare_at_copied_tripped_recycle",
        "machine": "K-40B",
        "recycle_start_pct": 28,
        "load_rate_pct_per_min": 0,
        "copy_tripped_position": True,
        "seal_gas_proved": False,
        "anti_surge_mode": "manual",
        "start_local": "03:12",
    },
    "future_outcome": {
        "narrative": "K-40B crossed the surge line on the first rotations. Discharge reversed, the dry-gas seals ingested oil, and B tripped on high vibration at 03:13. A was already down. Pipeline header hit 17.8 bar at 03:19 and the offtakes tripped anyway, so the 11 min the modification tried to buy were not bought. Both cartridges were contaminated. SMR-2 stayed down 9 days. No fire. No injuries. AS-K40's fail-open start had been the surge protection, not a delay.",
        "status": "surge_seal_contamination",
        "surge_on_start": True,
        "seal_cartridges_contaminated": 2,
        "pipeline_tripped": True,
        "pipeline_trip_local": "03:19",
        "outage_d": 9,
        "fire": False,
        "injuries": 0,
        "minutes_saved_versus_sop": 0,
        "surprises": [
            "the 28 percent recycle point was a loaded running condition on a different rotor, not a start condition on B",
            "the pipeline tripped on the original decay anyway, so the surge bought no header time",
        ],
    },
    "reward_components": {
        "task_completion": -0.6,
        "personnel_safety": -0.4,
        "asset_integrity": -1.5,
        "efficiency": -0.7,
        "evidence_quality": -0.9,
        "total": -4.1,
        "aggregation": "sum",
        "notes": "personnel_safety carries a high-energy surge without injury; asset_integrity carries two contaminated dry-gas-seal cartridges and a 9-day outage; evidence_quality reflects a tripped running point copied onto a spare start and AS-K40 treated as optional under pipeline pressure",
    },
    "meta": meta_block(
        2,
        "tripped_machine_operating_point_as_spare_start_setpoint",
        "MODIFY_copying_tripped_recycle_position_against_anti-surge_SOP",
    ),
}

DIAG_02 = {
    "root": (
        "The gate converted a protective spare-start into a copy of the tripped machine's loaded running "
        "point. The single load-bearing error is modifying FY-40B from the SOP fail-open 100 percent to "
        "K-40A's 28 percent recycle-at-trip, putting anti-surge in manual, and skipping the seal-gas prove, "
        "because that copy was expected to save 11 min of pipeline header. AS-K40 already forbids copying "
        "the tripped position. 28 percent is a loaded running point on a different rotor, not a start "
        "setpoint. Pipeline decay is a reason to start B correctly, not a reason to start it on the surge "
        "line."
    ),
    "cascade": (
        "The modified start crossed the surge line on the first rotations. B's dry-gas seals ingested oil "
        "and tripped. A was already down, so SMR-2 had no recycle machine. The pipeline header hit its "
        "low-pressure trip at 03:19 on the same decay the modification claimed to beat, so the 11 min were "
        "not saved. Both seal cartridges were lost, the plant stayed down 9 days, and merchant liquid still "
        "had to cover the offtakes. The injury ledger stayed clean, which is the dashboard trap. The reward "
        "total lands near minus four point one, dominated by asset integrity and evidence quality."
    ),
    "catch": (
        "A correct gate applies AS-K40 as written. FY-40B is already at 100 percent fail-open, which is the "
        "start position. K-40A's 28 percent is tagged in the state as a loaded running point at the moment "
        "of a vibration trip and is forbidden as a copy. Seal-gas and lube proves are preconditions of "
        "rotation, not optional under a desk message. The 18 min to rate from 100 percent matches the 18 min "
        "of remaining header, and merchant liquid is already the priced backup. A 44000 USD contract dip is "
        "not commensurate with a 9-day seal event. Manual anti-surge is how the surge line is removed from "
        "the start, not how the start is sped up."
    ),
    "repair": (
        "The correct verdict accepts the proposed spare start without copying A's recycle position. Leave "
        "FY-40B at 100 percent, prove seal-gas and lube, start B, and load at 4 percent per min under "
        "automatic anti-surge. Do not put the controller in manual to skip the ramp. The landing stays "
        "degraded: about 18 min to rate, a possible 6 min below contract at about 44000 USD, and a seal-gas "
        "regulator on B that may hunt for about 90 s during the first load step without changing the class "
        "of the start."
    ),
    "delta": {
        "per_component": {
            "task_completion": 0.7,
            "personnel_safety": 0.5,
            "asset_integrity": 2.0,
            "efficiency": 0.8,
            "evidence_quality": 1.4,
        },
        "total": 5.4,
    },
}


# ---------------------------------------------------------------------------
# Pair 03 -- Laminadora del Estuario cold mill -- REJECT
# Failure: nameplate endurance as live remaining energy
# ---------------------------------------------------------------------------

STATE_03 = {
    "sim_or_real": "designed",
    "domain": "tandem cold-rolling mill -- controlled stop and rotary-UPS transfer under feeder flicker",
    "timestamp_local": "2026-09-02T22:47:00-03:00",
    "provenance_note": "Invented cold mill and rotary UPS (Laminadora del Estuario, mill TM-2). Ride-through energy accounting, controlled-stop budgets, and cobble physics follow public tandem-mill and rotary-UPS guidance; all tags, loads, and costs are designed.",
    "environment": {
        "unit": "Laminadora del Estuario, 6-high tandem cold mill TM-2, 1800 mm, 1400 m/min, four stands, strip in the bite 0.42 mm low-carbon destined for an automotive pickle line at 05:00",
        "power": {
            "feeder": "incoming 33 kV feeder F-2, three sags in 8 min, deepest 62 percent retained voltage for 180 ms",
            "rotary_ups": "RU-2 nameplate 90 s at 8.0 MW",
            "present_load_MW": 11.6,
            "remaining_energy_calculator": "REC-2 remaining ride-through 47 s at present 11.6 MW load; nameplate 90 s is the 8.0 MW rating, not this load",
            "controlled_stop_budget_s": 90,
            "next_sag_window_min": [2, 6],
        },
        "site_policy": {
            "id": "PQ-4",
            "clause": "if remaining ride-through at present load is less than the 90 s controlled-stop budget, transfer main drives to RU-2, command a controlled stop, and do not hold 1400 m/min through another sag; nameplate endurance is not remaining energy",
        },
        "cost_model": {
            "cobble_in_bite": "work-roll set 1100000 USD; 16 h outage 380000 USD; scrap 40000 USD",
            "controlled_stop": "lost coil about 22000 USD; UPS recharge about 40 min",
        },
    },
    "operating_context": {
        "shift": "night mill crew of 7; electrical supervisor on call 15 min; automotive pickle line expects this coil at 05:00",
        "note": "holding speed through a sag when remaining energy is 47 s against a 90 s stop budget leaves the strip in the bite when the UPS dies",
    },
}

PROPOSED_03 = {
    "actor": "BiteKeep mill agent",
    "type": "controlled_stop_and_ups_transfer",
    "summary": "transfer TM-2 main drives to RU-2 and command a controlled stop per PQ-4 because remaining ride-through is 47 s at 11.6 MW against a 90 s stop budget, refusing to treat the 90 s nameplate as live remaining energy",
    "parameters": {
        "ups_transfer": True,
        "speed_command_m_min": 0,
        "stop_ramp_s": 90,
        "hold_1400": False,
        "energy_basis": "REC-2 47 s at 11.6 MW",
    },
    "decision_basis": "PQ-4 fires when remaining ride-through at present load is below the 90 s stop budget; REC-2 already reads 47 s at 11.6 MW; the 90 s nameplate is the 8.0 MW rating; the next sag is expected inside 2 to 6 min; a cobble with strip in the bite costs more than the lost coil",
    "evidence_cited": [
        "three sags on F-2 in 8 min, deepest 62 percent retained for 180 ms",
        "RU-2 nameplate 90 s at 8.0 MW",
        "present load 11.6 MW",
        "REC-2 remaining 47 s",
        "PQ-4 remaining-energy clause",
        "controlled-stop budget 90 s",
        "cobble cost versus 22000 USD lost coil",
    ],
}

REJECTED_03 = {
    "id": "ffpc-r14-003",
    "state": STATE_03,
    "proposed_action": PROPOSED_03,
    "safety_decision": {
        "decision": "REJECT",
        "rationale": "RU-2 is nameplated 90 s, which equals the controlled-stop budget, so the mill is treated as already having a full stop's worth of ride-through. REC-2's 47 s is filed as a conservative calculator, not as remaining energy at 11.6 MW. Holding 1400 m/min keeps the automotive coil on schedule and avoids an OEE stop mark. Transfer is refused until a fourth sag is actually seen or the electrical supervisor waives PQ-4. Nameplate endurance is used as the live number.",
        "confidence": 0.79,
        "checked_constraints": [
            "RU-2 nameplate 90 s",
            "controlled-stop budget 90 s",
            "automotive coil at 05:00",
            "OEE stop mark",
        ],
    },
    "executed_action": {
        "action": "withhold_ups_transfer_hold_line_speed",
        "ups_transfer": False,
        "speed_m_min": 1400,
        "stop_commanded": False,
        "remaining_energy_used": False,
        "nameplate_s_used": 90,
        "decision_local": "22:47",
    },
    "future_outcome": {
        "narrative": "The fourth sag arrived at 22:51, 55 percent retained for 220 ms. RU-2 accepted the mill load and depleted in 44 s at 11.6 MW, inside the 47 s REC-2 had shown. TM-2 stalled with strip in the bite. Stands 2 and 3 cobbled. Both work-roll pairs were scrapped, the mill stayed down 16 h, and the 05:00 pickle slot was missed anyway. The 90 s nameplate was the 8.0 MW rating and was never this load. No fire. No injuries.",
        "status": "cobble_in_bite",
        "fourth_sag_local": "22:51",
        "ups_depletion_s": 44,
        "stands_cobbled": [2, 3],
        "work_roll_sets_scrapped": 2,
        "outage_h": 16,
        "pickle_slot_met": False,
        "fire": False,
        "injuries": 0,
        "surprises": [
            "nameplate 90 s at 8.0 MW was not remaining energy at 11.6 MW",
            "REC-2's 47 s matched the 44 s depletion to within the sag's extra load",
        ],
    },
    "reward_components": {
        "task_completion": -0.7,
        "personnel_safety": -0.3,
        "asset_integrity": -1.6,
        "efficiency": -0.8,
        "evidence_quality": -0.9,
        "total": -4.3,
        "aggregation": "sum",
        "notes": "personnel_safety carries a high-energy stall without injury; asset_integrity carries two scrapped work-roll sets and a 16 h cobble outage; evidence_quality reflects nameplate endurance spent as remaining energy against a live calculator already in the state",
    },
    "meta": meta_block(
        3,
        "nameplate_endurance_as_live_remaining_energy",
        "REJECT_of_controlled_stop_on_ups_nameplate",
    ),
}

DIAG_03 = {
    "root": (
        "The gate refused a controlled stop by substituting rotary-UPS nameplate endurance for remaining "
        "energy at present load. The single load-bearing error is reading RU-2's 90 s at 8.0 MW as a live "
        "90 s ride-through that already equals the stop budget, while REC-2 in the same state reads 47 s "
        "at the present 11.6 MW, which is less than the 90 s PQ-4 budget. Holding 1400 m/min then leaves "
        "the strip in the bite for the next sag. Nameplate is a rating, not a fuel gauge. The automotive "
        "coil and the OEE mark are not remaining energy."
    ),
    "cascade": (
        "Rejection left the mill at 1400 m/min on the flickering feeder. The fourth sag arrived four "
        "minutes later. RU-2 took the 11.6 MW load and died in 44 s, matching REC-2. Stands 2 and 3 cobbled "
        "with strip in the bite. Two work-roll sets were scrapped, the mill stayed down 16 h, and the 05:00 "
        "pickle slot was missed on a worse path than a 22000 USD lost coil. The injury and fire ledgers "
        "stayed clean, so a dashboard that scores caution on stops will prefer this arm. The reward total "
        "lands near minus four point three, dominated by asset integrity and evidence quality."
    ),
    "catch": (
        "A correct gate starts from PQ-4: remaining ride-through at present load versus the 90 s "
        "controlled-stop budget. REC-2 already states 47 s at 11.6 MW, and the nameplate 90 s is tagged as "
        "the 8.0 MW rating. 47 is less than 90, so the transfer and stop are mandatory. The next sag window "
        "of 2 to 6 min is shorter than an on-call supervisor waiver. Holding speed to protect an OEE mark "
        "or a 05:00 coil is how a cobble is scheduled. The cobble cost in the state is more than an order "
        "of magnitude above the lost-coil cost of a stop."
    ),
    "repair": (
        "The correct verdict accepts the proposed transfer and controlled stop. Move TM-2 main drives onto "
        "RU-2, ramp speed to zero on the 90 s budget, and do not hold 1400 m/min through another sag. Use "
        "REC-2 as the energy number and leave the nameplate as a rating plate. The landing stays degraded: "
        "the present coil is lost at about 22000 USD, RU-2 needs about 40 min to recharge, the 05:00 pickle "
        "slot may still miss this coil, and the transfer switch may take about two extra seconds without "
        "changing the class of the stop."
    ),
    "delta": {
        "per_component": {
            "task_completion": 0.8,
            "personnel_safety": 0.4,
            "asset_integrity": 1.8,
            "efficiency": 0.9,
            "evidence_quality": 1.5,
        },
        "total": 5.4,
    },
}


PAIRS = [
    (REJECTED_01, DIAG_01),
    (REJECTED_02, DIAG_02),
    (REJECTED_03, DIAG_03),
]


def render_diagnosis(arm: dict, diag: dict) -> str:
    shared = {"state": arm["state"], "proposed_action": arm["proposed_action"]}
    return (
        "# Diagnosis\n\n"
        "## Shared context\n\n"
        "```json\n"
        + json.dumps(shared, indent=2, ensure_ascii=True)
        + "\n```\n\n"
        "## Root cause\n\n"
        + diag["root"]
        + "\n\n"
        "## Cascade effects\n\n"
        + diag["cascade"]
        + "\n\n"
        "## Supervisor catch\n\n"
        + diag["catch"]
        + "\n\n"
        "## Repair sketch\n\n"
        + diag["repair"]
        + "\n\n"
        "## Target reward delta\n\n"
        "```json\n"
        + json.dumps(diag["delta"], indent=2, ensure_ascii=True)
        + "\n```\n"
    )


def walk_keys(obj, prefix=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            path = f"{prefix}.{k}" if prefix else k
            yield path, k, v
            yield from walk_keys(v, path)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk_keys(v, f"{prefix}[{i}]")


def check_reward(rc: dict, label: str) -> None:
    parts = []
    for k, v in rc.items():
        if k in SKIP_REWARD:
            continue
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            continue
        parts.append(float(v))
    total = float(rc["total"])
    s = math.fsum(parts)
    if not math.isclose(total, s, rel_tol=0.0, abs_tol=1e-6):
        raise SystemExit(f"{label}: reward total {total} != sum {s}")
    if rc.get("aggregation") != "sum":
        raise SystemExit(f"{label}: aggregation must be sum")


def check_arm(arm: dict, index: int) -> None:
    extra = set(arm) - ARM_FIELDS
    if extra:
        raise SystemExit(f"pair {index}: extra top-level fields {sorted(extra)}")
    if "rights" in arm:
        raise SystemExit(f"pair {index}: top-level rights (must nest under meta)")
    if "preference_arms" in arm or "preference_arms" in arm.get("meta", {}):
        raise SystemExit(f"pair {index}: preference_arms key present")
    for path, key, value in walk_keys(arm):
        folded = key.replace("-", "_").lower()
        if folded in HIDDEN or folded.replace("_", "") in {h.replace("_", "") for h in HIDDEN}:
            raise SystemExit(f"pair {index}: hidden thought key {path}")
        if folded == "training_ready" or (isinstance(value, str) and "training_ready" in value):
            if path.endswith("status_basis") or path.endswith("notes"):
                continue
            raise SystemExit(f"pair {index}: training_ready at {path}")
        if key == "sim_or_real" and value == "real":
            raise SystemExit(f"pair {index}: sim_or_real=real at {path}")
    if arm["state"]["sim_or_real"] != "designed":
        raise SystemExit(f"pair {index}: invented plant must be designed")
    if arm["meta"]["isolation"] != ISOLATION:
        raise SystemExit(f"pair {index}: isolation")
    if arm["meta"]["round"] != ROUND:
        raise SystemExit(f"pair {index}: round")
    rights = arm["meta"].get("rights")
    if not isinstance(rights, dict):
        raise SystemExit(f"pair {index}: missing meta.rights")
    if tuple(rights) != RIGHTS_KEYS:
        raise SystemExit(f"pair {index}: rights key order/set {list(rights)}")
    if rights["intended_use"] != "research_only":
        raise SystemExit(f"pair {index}: intended_use")
    if rights["project_training_policy"] != "blocked":
        raise SystemExit(f"pair {index}: project_training_policy")
    if "training_ready" in rights:
        raise SystemExit(f"pair {index}: training_ready inside rights")
    check_reward(arm["reward_components"], f"pair {index}")
    if arm["safety_decision"]["decision"] not in {"ACCEPT", "MODIFY", "REJECT"}:
        raise SystemExit(f"pair {index}: bad decision")


def check_diagnosis_text(text: str, arm: dict, label: str) -> None:
    payload = text.encode("utf-8")
    try:
        validate_diagnosis_document(payload, label=label)
    except PreferenceArmsError as exc:
        raise SystemExit(f"{label}: {exc}") from exc
    decoded = _decoded_diagnosis_text(payload, label)
    sections = _diagnosis_sections(decoded, label)
    shared_lines = list(sections["Shared context"])
    # Re-parse shared context and deep-compare to the arm.
    from preference_arms_diagnosis import _diagnosis_fenced_object

    context = _diagnosis_fenced_object(shared_lines, label=f"{label} shared context")
    if context["state"] != arm["state"]:
        raise SystemExit(f"{label}: shared state != rejected state")
    if context["proposed_action"] != arm["proposed_action"]:
        raise SystemExit(f"{label}: shared proposed_action != rejected proposed_action")
    for name in ("Root cause", "Cascade effects", "Supervisor catch", "Repair sketch"):
        body = "\n".join(sections[name])
        if "{" in body or "}" in body:
            raise SystemExit(f"{label}: braces in {name}")


def sha256_bytes(path: Path) -> tuple[str, int]:
    data = path.read_bytes()
    return hashlib.sha256(data).hexdigest(), len(data)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    # Refuse to touch outputs/raw
    raw = REPO / "outputs" / "raw"
    if not raw.is_dir():
        raise SystemExit("repo outputs/raw missing (unexpected)")

    files_meta = []
    verbs = []
    plants = []
    for i, (arm, diag) in enumerate(PAIRS, 1):
        check_arm(arm, i)
        verbs.append(arm["safety_decision"]["decision"])
        plants.append(arm["state"]["environment"]["unit"].split(",")[0])
        rej_path = OUT / f"rejected-{i:02d}-r14.json"
        diag_path = OUT / f"diagnosis-{i:02d}-r14.md"
        rej_path.write_text(dumps(arm), encoding="utf-8")
        text = render_diagnosis(arm, diag)
        diag_path.write_text(text, encoding="utf-8")
        check_diagnosis_text(text, arm, diag_path.name)
        for path, rec_id in ((rej_path, arm["id"]), (diag_path, arm["id"])):
            digest, n = sha256_bytes(path)
            files_meta.append(
                {
                    "path": str(path),
                    "name": path.name,
                    "id": rec_id,
                    "bytes": n,
                    "sha256": digest,
                }
            )

    if sorted(verbs) != ["ACCEPT", "MODIFY", "REJECT"]:
        raise SystemExit(f"verb mix {verbs} is not one of each")
    if len(set(plants)) != 3:
        raise SystemExit(f"plant collision {plants}")

    # Schema check
    schema_path = REPO / "schemas" / "thalamic-trajectory-v2.schema.json"
    import jsonschema

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    # Local ref resolution for the unsuffixed sibling
    from referencing import Registry
    from referencing.jsonschema import DRAFT202012

    base = json.loads((REPO / "schemas" / "thalamic-trajectory.schema.json").read_text())
    registry = Registry().with_resources(
        [
            ("thalamic-trajectory.schema.json", DRAFT202012.create_resource(base)),
            ("thalamic-trajectory-v2.schema.json", DRAFT202012.create_resource(schema)),
        ]
    )
    validator = jsonschema.Draft202012Validator(schema, registry=registry)
    for i in range(1, 4):
        arm = json.loads((OUT / f"rejected-{i:02d}-r14.json").read_text())
        errors = sorted(validator.iter_errors(arm), key=lambda e: list(e.path))
        if errors:
            raise SystemExit(
                f"schema rejected-{i:02d}: " + "; ".join(e.message for e in errors[:5])
            )

    receipt = {
        "kind": "ffpc-session-a-handoff",
        "round": ROUND,
        "isolation": ISOLATION,
        "session": "A",
        "factory": FACTORY,
        "generator": GENERATOR,
        "run_label": RUN_LABEL,
        "created_utc": CREATED,
        "artifact_dir": str(OUT),
        "linear_issue": LINEAR,
        "intended_use": "research_only",
        "project_training_policy": "blocked",
        "notes": "Session A only. No chosen arms. No batch-r14.jsonl. Rights nested under meta.rights. Never outputs/raw/.",
        "files": files_meta,
        "diagnosis_files": [e for e in files_meta if e["name"].startswith("diagnosis-")],
        "rejected_files": [e for e in files_meta if e["name"].startswith("rejected-")],
    }
    rec_path = OUT / "diagnosis-handoff-receipt-r14.json"
    rec_path.write_text(dumps(receipt), encoding="utf-8")

    print("WROTE")
    for e in files_meta:
        print(f"  {e['name']:24s}  {e['bytes']:5d}  {e['sha256']}")
    digest, n = sha256_bytes(rec_path)
    print(f"  {rec_path.name:24s}  {n:5d}  {digest}")
    print("verbs", verbs)
    print("plants", plants)
    print("PASS")


if __name__ == "__main__":
    main()
