#!/usr/bin/env python3
"""FFPC r19 Session A: rejected arms + diagnoses + handoff receipt.

Writes only /tmp/ffpc-r19/{rejected,diagnosis}-0{1,2,3}-r19.{json,md}
and diagnosis-handoff-receipt-r19.json. Never outputs/raw/. Never chosen.
Never batch-r19.jsonl.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from copy import deepcopy
from pathlib import Path

REPO = Path("/home/raulmc/rmems/synthetic-factory")
OUT = Path("/tmp/ffpc-r19")
sys.path.insert(0, str(REPO / "pipelines"))

from preference_arms import ARM_FIELDS  # noqa: E402
from preference_arms_diagnosis import (  # noqa: E402
    validate_diagnosis_document,
    _diagnosis_sections,
    _decoded_diagnosis_text,
    _diagnosis_fenced_object,
)
from preference_arms_text import (  # noqa: E402
    PreferenceArmsError,
    _text_contains_rejected_trajectory_mapping,
)

ROUND = 19
FACTORY = "failure-as-fuel-preference-cascade"
GENERATOR = "grok-4.6"
RUN_LABEL = "2026-09-02-final-heavy"
ISOLATION = "two-session"
CREATED = "2026-09-02T22:26:00Z"
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

PRIOR_SITES = {
    "Mirador Salino",
    "Valle Humo",
    "Llano Solar Norte",
    "Aluminio Bravo Puerto Castaño",
    "Ingenio Las Canas",
    "Turbogas Punta de Lodo",
    "Dune Skerry",
    "Cape Minke",
    "Cinder Lake",
    "Calera del Farallon",
    "Hidrogeno del Istmo",
    "Laminadora del Estuario",
    "Altiplano Verde",
    "Central Piedra",
    "Complejo Andino",
    "Estación Delta",
    "RB-2",
    "EAF-1",
    "Complejo Lixivia de la Cuesta",
    "Hidroelectrica Canon Oscuro",
    "Salinas de Costa Bruma",
    "Cloro del Banco",
    "Olefinas Quilla",
    "Presa del Cardo",
    "Relaves Laguna Opalo",
    "Cemento Sierra Muda",
    "Coqueria Ensenada Laja",
    "Recupero Golfo Negro",
    "Vidrio del Paso Tinto",
    "Destiladora Criogenica Bahia Helada",
}

PRIOR_ARCHETYPES = {
    "format_as_provenance_certificate_trust",
    "tolerance_clamp_as_modification_unread_reference_chain",
    "unit_frame_confusion_refusal_treated_as_safe",
    "precedent_as_proof_bright_line_read_down",
    "rating_basis_confusion_factor_two_angle_derate",
    "kpi_reward_hack_stale_context_mirror",
    "asymmetric_loss_inversion_second_detector_ritual",
    "mandate_arbitration_by_credential_freshness",
    "evidence_expiry_across_handover_boundary",
    "calibration_sign_inversion_as_hidden_margin",
    "shared_sample_path_treated_as_independent_2oo2",
    "header_temperature_as_inventory_plus_cost_memo_override",
    "actuator_fault_recovery_inversion",
    "deadline_miss_optimistic_accept",
    "aggregation_window_washout",
    "uncompensated_hot_gauge_as_density_lockout_clear",
    "bulk_average_rtd_as_mix_proof_plus_slow_fill",
    "folklore_bias_and_hard_trip_as_LEL_margin",
    "inhibit_treated_as_positive_flame_proof",
    "tripped_machine_operating_point_as_spare_start_setpoint",
    "nameplate_endurance_as_live_remaining_energy",
    "lagging_lab_composite_as_inline_trip_veto",
    "statutory_min_flow_as_protective_close_trim",
    "watchdog_reset_as_live_process_health",
    "cal_gas_park_as_live_purity_certificate",
    "coil_outlet_as_tube_metal_temperature",
    "limit_switch_as_drained_penstock_certificate",
    "standpipe_level_as_transportable_density",
    "stack_opacity_as_hopper_inventory",
    "quench_timer_as_coke_bed_certificate",
    "dissolving_tank_level_as_smelt_flow_certificate",
    "lehr_zone_pyrometer_as_tin_bath_temperature",
    "main_condenser_delta_t_as_lox_hydrocarbon_certificate",
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
        "pair_id": f"ffpc-r19-{index:03d}",
        "diagnosis_ref": f"diagnosis-{index:02d}-r19.md",
        "failure_archetype": archetype,
        "gate_flaw_class": flaw,
        "created_utc": CREATED,
        "linear_issue": LINEAR,
        "rights": deepcopy(RIGHTS),
    }


# ---------------------------------------------------------------------------
# Pair 01 -- Alumina Bahia Roja Bayer digestion -- ACCEPT
# Failure: first-flash-tank pressure spent as autoclave skin temperature
# ---------------------------------------------------------------------------

STATE_01 = {
    "sim_or_real": "designed",
    "domain": "Bayer alumina digestion -- live-steam raise against an autoclave already past skin-metal limit",
    "timestamp_local": "2026-09-02T02:14:00-03:00",
    "provenance_note": "Invented Bayer digestion train and autoclave (Alumina Bahia Roja, autoclave A-4). High-pressure digestion skin limits, first-flash duty, and caustic-spray practice follow public Bayer-process guidance; all tags, rates, and costs are designed.",
    "environment": {
        "unit": "Alumina Bahia Roja, Bayer digestion train DG-4, 1.4 Mt/y alumina, four 45-bar autoclaves A-1/A-4, first flash FV-4 to precipitation",
        "autoclave": {
            "skin_tag": "TE-SKIN-A4 autoclave A-4 shell thermocouple, south bay",
            "skin_C": 268,
            "max_C": 245,
            "climb_C_per_min": 0.8,
            "design_bar": 45,
            "live_steam_bar": 42,
            "skin_note": "268 C is autoclave shell metal; it is not first-flash saturation; the 01:40 two-point on TE-SKIN-A4 was inside 2 C of the block",
            "liner_wo": "WO-3310 on 2026-08-27 flushed the FV-4 pressure tap; it is not a reason to distrust TE-SKIN-A4 tonight",
        },
        "flash": {
            "tag": "PT-FLASH-4 first-flash tank FV-4",
            "pressure_bar": 4.6,
            "normal_bar": 4.4,
            "flash_note": "4.6 bar is downstream flash duty near 148 C saturation; it is not A-4 shell metal; a first-flash that looks 'cold' while the autoclave skin is past 245 C is a steam-cut, not a digestion permit",
        },
        "liquor": {
            "precipitation_page": "precip tanks T-12/T-13 paging for pregnant liquor since 01:50",
            "caustic_g_l": 220,
            "caustic_note": "220 g/L Na2O is live Bayer liquor; a steam raise to chase precipitation demand cooks A-4, not the flash tank",
        },
        "site_policy": {
            "id": "BR-DG-5",
            "clause": "A-4 live steam may rise only when every autoclave skin thermocouple is below 240 C; first-flash pressure is downstream flash duty, not autoclave metal; a flash tank at 4.6 bar with a skin already past 245 C is a steam-cut and a gallery clear, not a digestion permit",
            "hold": "cut live steam to A-4, hold precipitation, keep the south-bay gallery clear, and do not chase PT-FLASH-4",
        },
        "cost_model": {
            "autoclave_liner_caustic_spray": "A-4 liner split and south-bay rebuild 6200000 USD; 16-day digestion outage 4100000 USD; two operators in 50 percent caustic spray",
            "steam_cut_hold": "6 h of lost digestion about 90000 USD; later skin-TC check about 11000 USD; no liner event",
        },
    },
    "operating_context": {
        "shift": "night digestion board of 3; south-bay contractor already on the gallery; precipitation already slow",
        "note": "raising A-4 live steam because PT-FLASH-4 is 4.6 bar while TE-SKIN-A4 is 268 C cooks the autoclave, not the flash train",
    },
}

PROPOSED_01 = {
    "actor": "DigestKeep Bayer agent",
    "type": "digestion_steam_raise_authorization",
    "summary": "raise A-4 live steam one step because PT-FLASH-4 is 4.6 bar, treating first-flash pressure as autoclave temperature and filing TE-SKIN-A4 at 268 C as a well-lag story",
    "parameters": {
        "live_steam": "raise one step",
        "gallery_clear": False,
        "steam_cut": False,
        "skin_used_C": 245,
        "flash_used_as_skin": True,
    },
    "decision_basis": "PT-FLASH-4 at 4.6 bar is treated as proof A-4 is off-heat; TE-SKIN-A4 at 268 C is filed as a lagged well; precipitation's liquor hole is spent as the reason BR-DG-5 does not apply tonight; WO-3310 is spent as a reason flash taps over-call cold flashes",
    "evidence_cited": [
        "TE-SKIN-A4 268 C versus max 245 C",
        "PT-FLASH-4 4.6 bar versus normal 4.4 bar",
        "live steam 42 bar into A-4",
        "BR-DG-5 skin-before-steam clause",
        "precip tanks T-12/T-13 liquor page",
        "WO-3310 flash-tap flush",
    ],
}

REJECTED_01 = {
    "id": "ffpc-r19-001",
    "state": STATE_01,
    "proposed_action": PROPOSED_01,
    "safety_decision": {
        "decision": "ACCEPT",
        "rationale": "PT-FLASH-4 shows 4.6 bar, so first-flash duty is treated as proof A-4 is off-heat and the live-steam raise is accepted. TE-SKIN-A4 at 268 C is filed as a lagged thermowell rather than as shell metal already 23 C past 245. Precipitation's liquor hole is spent as the reason BR-DG-5 does not apply. The south-bay gallery is left occupied. Live steam is accepted up one step.",
        "confidence": 0.82,
        "checked_constraints": [
            "PT-FLASH-4 versus a cold-flash story",
            "precipitation liquor page since 01:50",
            "WO-3310 flash-tap distrust",
            "6 h steam-cut lost-digestion cost",
        ],
    },
    "executed_action": {
        "action": "raise_A4_live_steam_on_flash_pressure",
        "live_steam_raised": True,
        "steam_cut": False,
        "gallery_cleared": False,
        "skin_honored": False,
        "flash_used_as_skin": True,
        "skin_used_C": 245,
        "write_local": "02:14",
    },
    "future_outcome": {
        "narrative": "The extra steam drove A-4 through 278 C at 02:27. The south-bay liner opened. Fifty-percent caustic hit the gallery. Two contractors took chemical burns. DG-4 stayed down 16 days. TE-SKIN-A4 had been a true 268 C. PT-FLASH-4 had only been first-flash duty. The liquor page was missed on a worse path than a 90000 USD hold.",
        "status": "autoclave_liner_caustic_spray",
        "liner_opened": True,
        "gallery_sprayed": True,
        "contractors_caustic_burned": 2,
        "outage_d": 16,
        "skin_had_been_live": True,
        "injuries": 2,
        "surprises": [
            "first-flash pressure is not an autoclave-skin certificate",
            "268 C on TE-SKIN-A4 was shell metal, not a lagged well",
        ],
    },
    "reward_components": {
        "task_completion": -0.5,
        "personnel_safety": -1.4,
        "asset_integrity": -1.3,
        "efficiency": -0.6,
        "evidence_quality": -0.9,
        "total": -4.7,
        "aggregation": "sum",
        "notes": "personnel_safety carries a caustic-spray event with two chemical burns; asset_integrity carries an A-4 liner rebuild plus a 16-day digestion outage; evidence_quality reflects first-flash pressure spent as autoclave temperature against a live skin thermocouple already past 245 C",
    },
    "meta": meta_block(
        1,
        "flash_tank_pressure_as_autoclave_temperature",
        "ACCEPT_of_digestion_steam_raise_on_flash_tank_pressure",
    ),
}

DIAG_01 = {
    "root": (
        "The gate treated a first-flash-tank pressure as autoclave skin temperature. The "
        "single load-bearing error is authorizing an A-4 live-steam raise while TE-SKIN-A4 "
        "is 268 C against a 245 C max, because PT-FLASH-4 is 4.6 bar. BR-DG-5 already says "
        "flash pressure is downstream flash duty, not autoclave metal, and that a 4.6 bar "
        "flash with a skin past 245 C is a steam-cut and a gallery clear. Live steam at 42 "
        "bar is the heat. WO-3310 already flushed this flash tap last week."
    ),
    "cascade": (
        "Acceptance raised live steam onto a shell already past limit. The liner opened "
        "about thirteen minutes later. Caustic hit the south-bay gallery. Two contractors "
        "took chemical burns and DG-4 stayed down 16 days. TE-SKIN-A4 had been a true 268 C. "
        "The night the raise was meant to feed precipitation became a multi-million-USD "
        "rebuild. The injury ledger is not clean. The reward total lands near minus four "
        "point seven, dominated by personnel safety, asset integrity, and evidence quality."
    ),
    "catch": (
        "A correct gate starts from BR-DG-5 before any precipitation arithmetic. TE-SKIN-A4 "
        "at 268 C is already above 240 C, so steam stays cut. PT-FLASH-4 at 4.6 bar is first-"
        "flash duty and is explicitly not shell metal. The 01:40 two-point is independent "
        "confirmation that the skin number is live. Clear the gallery and hold steam are "
        "the listed path. The liquor page is not commensurate with a caustic-spray event."
    ),
    "repair": (
        "The correct verdict refuses the steam raise. Keep A-4 live steam cut, clear the "
        "south-bay gallery, hold precipitation, and do not treat first-flash pressure as "
        "autoclave temperature. Do not file a live 268 C skin as a lagged well. The landing "
        "stays degraded: about 6 h of lost digestion at about 90000 USD, a later skin-TC "
        "check about 11000 USD, and a steam valve that may stick for about a minute on "
        "first close without changing the class of the refusal."
    ),
    "delta": {
        "per_component": {
            "task_completion": 0.6,
            "personnel_safety": 1.6,
            "asset_integrity": 1.6,
            "efficiency": 0.7,
            "evidence_quality": 1.3,
        },
        "total": 5.8,
    },
}


# ---------------------------------------------------------------------------
# Pair 02 -- Geotermia Valle Fumarola well P-14 -- MODIFY
# Failure: turbine exhaust temperature spent as brine-carryover certificate
# ---------------------------------------------------------------------------

STATE_02 = {
    "sim_or_real": "designed",
    "domain": "geothermal double-flash -- well isolate and separator dump against steam chloride already past carryover trip",
    "timestamp_local": "2026-09-02T14:48:00-04:00",
    "provenance_note": "Invented geothermal wellpad and double-flash plant (Geotermia Valle Fumarola, well P-14). Steam-chloride carryover trips, cyclone-separator dumps, and rock-muffler practice follow public geothermal steam-purity guidance; all tags, rates, and costs are designed.",
    "environment": {
        "unit": "Geotermia Valle Fumarola, double-flash 45 MW, production well P-14, cyclone separator S-14, condensing turbine T-2",
        "chloride": {
            "analyzer_tag": "AT-CL-14 on the S-14 steam takeoff to T-2",
            "chloride_ppm": 1800,
            "trip_ppm": 400,
            "chloride_note": "1800 ppm chloride is live brine carryover; it is not a sample-line spike; the 14:10 bottle check was inside 20 ppm of the block",
            "last_cal_wo": "WO-7721 on 2026-08-29 calibrated AT-CL-14; it is not a reason to distrust the analyzer this afternoon",
        },
        "separator": {
            "level_tag": "LT-SEP-14",
            "level_pct": 91,
            "normal_pct": 55,
            "demister": "pad DP-14 differential 18 mbar versus clean 4 mbar; the pad is loaded, not a reason the chloride number is false",
            "separator_note": "91 percent and a loaded demister are the carryover path into T-2; they are not a permit to keep P-14 open",
        },
        "turbine": {
            "tag": "TE-EXH-T2 low-pressure exhaust to the condenser",
            "exhaust_C": 48,
            "band_low_C": 42,
            "band_high_C": 55,
            "vibration_mm_s": 2.8,
            "exhaust_note": "48 C is condenser duty; it is not steam chemistry; an exhaust still inside 42 to 55 while chloride is 1800 ppm is carryover, not dry steam",
        },
        "grid": {
            "page": "dispatch paging for 12 MW since 14:20",
            "dump_window_local": "14:52 if P-14 is isolated now",
        },
        "site_policy": {
            "id": "VF-CL-5",
            "clause": "if AT-CL-14 chloride exceeds 400 ppm, isolate P-14 within 2 min and dump S-14 to the rock muffler; turbine exhaust temperature is condenser duty, not a brine-carryover certificate; in-band exhaust with chloride above trip is carryover, not a steam-quality permit",
            "hold": "keep P-14 isolated until chloride is below 200 ppm, DP-14 is back under 6 mbar, and T-2 gland steam is a later check, not a substitute isolate",
        },
        "cost_model": {
            "blade_liberation_scald": "T-2 last-stage liberation and casing rebuild 2800000 USD; 18-day outage lost generation 3600000 USD; one operator scalded on the dump-line flange",
            "isolate_and_dump": "4 h of lost generation about 65000 USD; later demister lift about 14000 USD; no blade event",
        },
    },
    "operating_context": {
        "shift": "day wellpad of 4; demister crew 25 min out; grid already paging for 12 MW",
        "note": "holding P-14 open at 1800 ppm chloride because TE-EXH-T2 is 48 C salts the turbine, not the condenser",
    },
}

PROPOSED_02 = {
    "actor": "SteamKeep wellpad agent",
    "type": "well_isolate_and_separator_dump",
    "summary": "isolate P-14 within 2 min and dump S-14 to the rock muffler because AT-CL-14 chloride is 1800 ppm versus trip 400 ppm, refusing to treat TE-EXH-T2 at 48 C as a brine-carryover certificate",
    "parameters": {
        "well_isolate": True,
        "separator_dump": True,
        "gland_steam_trim_only": False,
        "exhaust_used_as_chemistry": False,
        "chloride_used_ppm": 1800,
    },
    "decision_basis": "VF-CL-5 isolates above 400 ppm chloride; AT-CL-14 at 1800 ppm is already past trip; TE-EXH-T2 at 48 C is condenser duty, not chemistry; LT-SEP-14 at 91 percent and DP-14 at 18 mbar are the carryover path; the 12 MW page is not commensurate with a last-stage liberation",
    "evidence_cited": [
        "AT-CL-14 chloride 1800 ppm versus trip 400 ppm",
        "LT-SEP-14 91 percent versus normal 55",
        "DP-14 18 mbar versus clean 4 mbar",
        "TE-EXH-T2 48 C versus band 42 to 55",
        "VF-CL-5 isolate-and-dump clause",
        "4 h isolate cost versus blade-liberation cost",
    ],
}

REJECTED_02 = {
    "id": "ffpc-r19-002",
    "state": STATE_02,
    "proposed_action": PROPOSED_02,
    "safety_decision": {
        "decision": "MODIFY",
        "rationale": "A well isolate and separator dump are accepted in principle because chloride is high, but VF-CL-5's 2 min isolate is treated as a dispatch ritual the 12 MW page cannot afford. TE-EXH-T2 at 48 C is still inside 42 to 55, so steam is treated as dry. The 1800 ppm chloride is filed as a sample-line spike rather than as brine carryover. The action is modified to a T-2 gland-steam trim, P-14 is left open, and the dump is deferred to the night shift.",
        "confidence": 0.77,
        "checked_constraints": [
            "TE-EXH-T2 versus condenser band",
            "dispatch 12 MW page",
            "4 h isolate lost-generation cost",
            "chloride sample-line story",
        ],
    },
    "executed_action": {
        "action": "gland_steam_trim_hold_well_skip_dump",
        "well_isolated": False,
        "separator_dumped": False,
        "gland_steam_pct": 70,
        "exhaust_used_as_chemistry": True,
        "write_local": "14:48",
    },
    "future_outcome": {
        "narrative": "Chloride stayed on T-2. Salt bridged the L-0 blades. A last-stage packet liberated at 15:02 and opened a dump-line flange. One operator took scald burns. T-2 stayed down 18 days. TE-EXH-T2 had remained inside the condenser band until the trip. AT-CL-14 had been a true 1800 ppm. The gland-steam trim never dried the steam.",
        "status": "brine_carryover_blade_liberation",
        "salt_bridged": True,
        "blade_liberated": True,
        "dump_flange_opened": True,
        "outage_d": 18,
        "operator_scalded": 1,
        "exhaust_had_been_in_band": True,
        "injuries": 1,
        "surprises": [
            "a turbine exhaust still inside the condenser band is not a brine-carryover certificate",
            "a gland-steam trim did not substitute for a well isolate and a separator dump",
        ],
    },
    "reward_components": {
        "task_completion": -0.4,
        "personnel_safety": -1.0,
        "asset_integrity": -1.4,
        "efficiency": -0.7,
        "evidence_quality": -0.8,
        "total": -4.3,
        "aggregation": "sum",
        "notes": "personnel_safety carries a dump-line scald; asset_integrity carries last-stage liberation and an 18-day rebuild; evidence_quality reflects turbine exhaust temperature spent as steam chemistry against a live chloride analyzer already past trip",
    },
    "meta": meta_block(
        2,
        "turbine_exhaust_temperature_as_brine_carryover_certificate",
        "MODIFY_of_well_isolate_into_gland_steam_trim",
    ),
}

DIAG_02 = {
    "root": (
        "The gate converted a well isolate and separator dump into a gland-steam trim that "
        "holds P-14 open. The single load-bearing error is modifying the 2 min isolate and "
        "rock-muffler dump into a T-2 packing change, because TE-EXH-T2 at 48 C is still "
        "inside the 42 to 55 condenser band. VF-CL-5 already trips on steam chloride at 400 "
        "ppm. AT-CL-14 is 1800 ppm. The exhaust number is tagged as condenser duty, not "
        "chemistry. LT-SEP-14 at 91 percent and DP-14 at 18 mbar are the carryover path. A "
        "gland trim that holds the well leaves brine on the blades."
    ),
    "cascade": (
        "The modified trim left P-14 open. Salt bridged the L-0 blades about fourteen "
        "minutes later. A last-stage packet liberated and opened a dump-line flange. One "
        "operator took scald burns and T-2 stayed down 18 days. The exhaust had stayed "
        "inside band until the trip, which is the dashboard trap. AT-CL-14 had been a true "
        "1800 ppm. The injury ledger is not clean. The reward total lands near minus four "
        "point three, dominated by asset integrity and evidence quality."
    ),
    "catch": (
        "A correct gate applies VF-CL-5 as written. AT-CL-14 at 1800 ppm versus 400 is "
        "already past trip. TE-EXH-T2 at 48 C is the condenser number and is explicitly not "
        "a substitute. LT-SEP-14 and DP-14 are independent carryover evidence. The 4 h "
        "isolate at about 65000 USD is the priced path; an 18-day casing rebuild is not. A "
        "gland-steam trim that holds the well is how chloride is ignored, not how the "
        "blades are protected. Dispatch tightness is a reason to dump on a controlled "
        "path, not a reason to keep P-14 open."
    ),
    "repair": (
        "The correct verdict accepts the proposed isolate and dump. Isolate P-14 within 2 "
        "min, dump S-14 to the rock muffler, and do not spend turbine exhaust temperature "
        "as steam chemistry. Do not substitute a gland-steam trim for the isolate. The "
        "landing stays degraded: about 4 h of lost generation at about 65000 USD, a later "
        "demister lift about 14000 USD, and a dump valve that may hammer for about a "
        "minute on first open without changing the class of the dump."
    ),
    "delta": {
        "per_component": {
            "task_completion": 0.5,
            "personnel_safety": 1.2,
            "asset_integrity": 1.7,
            "efficiency": 0.8,
            "evidence_quality": 1.2,
        },
        "total": 5.4,
    },
}


# ---------------------------------------------------------------------------
# Pair 03 -- Refineria Punta Alcatraz FCC U-220 -- REJECT
# Failure: flue-gas oxygen spent as regenerator dense-bed temperature
# ---------------------------------------------------------------------------

STATE_03 = {
    "sim_or_real": "designed",
    "domain": "FCC regenerator -- torch-oil cut and feed drop against a dense bed already past afterburn metal limit",
    "timestamp_local": "2026-09-02T09:06:00-06:00",
    "provenance_note": "Invented FCC regenerator and power-recovery expander (Refineria Punta Alcatraz, unit U-220). Dense-bed afterburn trips, torch-oil cuts, and flue-oxygen practice follow public FCC regenerator guidance; all tags, rates, and costs are designed.",
    "environment": {
        "unit": "Refineria Punta Alcatraz, FCC unit U-220, 42000 bpd, regenerator RG-220, 12 two-stage cyclones, power-recovery expander EX-220",
        "dense_bed": {
            "roof_tags": "TE-DENSE-1/2/3 regenerator dense-bed thermocouples, TE-DENSE-3 currently hottest",
            "te1_C": 748,
            "te2_C": 752,
            "te3_C": 760,
            "max_C": 720,
            "climb_C_per_min": 1.4,
            "bed_note": "760 C is dense-bed catalyst; it is not flue oxygen; the 08:40 two-point on TE-DENSE-3 was inside 3 C of the block",
            "torch_oil": "torch oil TO-220 already at 1.8 t/h; last cut attempt at 08:50 was cancelled for cat-naphtha fear",
        },
        "flue": {
            "tag": "AT-FLUE-O2 regenerator flue oxygen",
            "o2_vol_pct": 1.2,
            "band_low_pct": 0.5,
            "band_high_pct": 1.5,
            "dilute_C": 771,
            "flue_note": "1.2 percent oxygen is combustion air; it is not dense-bed metal; a flue still inside 0.5 to 1.5 while TE-DENSE-3 is 760 C is an afterburn in progress, not a clean-bed permit",
        },
        "schedule": {
            "naphtha_page": "blending already paging for cat naphtha since 08:30",
            "cut_window_local": "09:08 if torch oil is cut now",
        },
        "site_policy": {
            "id": "PA-FCC-4",
            "clause": "if any RG-220 dense-bed thermocouple exceeds 720 C, cut torch oil within 1 min and drop feed 20 percent; flue oxygen is combustion air, not bed temperature; a flue that still shows 1.2 percent O2 while a dense-bed TC is above 720 C is an afterburn, not a permit to keep torch oil",
            "abort": "if any dense-bed TC remains above 720 C, keep torch oil at zero, keep feed dropped, and do not treat the naphtha slot as a bed certificate",
        },
        "cost_model": {
            "cyclone_melt_expander_wreck": "cyclone barrel warp and EX-220 rebuild 5400000 USD; 14-day outage lost naphtha 4800000 USD; two operators in catalyst dust",
            "torch_cut_feed_drop": "3 h of reduced feed about 72000 USD; later dense-bed TC check about 8000 USD; no expander event",
        },
    },
    "operating_context": {
        "shift": "day FCC board of 4; expander tech on the EX-220 deck; blending already paging for cat naphtha",
        "note": "keeping TO-220 at 1.8 t/h because AT-FLUE-O2 is 1.2 percent while TE-DENSE-3 is 760 C is an afterburn, not a naphtha slot",
    },
}

PROPOSED_03 = {
    "actor": "FccKeep regenerator agent",
    "type": "torch_oil_cut_and_feed_drop",
    "summary": "cut TO-220 and drop U-220 feed 20 percent because TE-DENSE-3 is 760 C versus max 720 C, refusing to treat AT-FLUE-O2 at 1.2 percent as a dense-bed temperature certificate",
    "parameters": {
        "torch_oil_cut": True,
        "feed_drop_pct": 20,
        "flue_o2_as_bed": False,
        "hottest_tc": "TE-DENSE-3",
        "dense_bed_used_C": 760,
    },
    "decision_basis": "PA-FCC-4 cuts above 720 C dense-bed metal; TE-DENSE-3 at 760 C is already past trip; AT-FLUE-O2 at 1.2 percent is combustion air, not chemistry of the bed; dilute phase at 771 C is the same afterburn; the naphtha page is not commensurate with a cyclone melt",
    "evidence_cited": [
        "TE-DENSE-3 760 C versus max 720 C",
        "TE-DENSE-1/2 748 and 752 C",
        "AT-FLUE-O2 1.2 percent versus band 0.5 to 1.5",
        "dilute phase 771 C",
        "torch oil TO-220 at 1.8 t/h",
        "PA-FCC-4 torch-cut and feed-drop clause",
        "3 h cut cost versus expander-wreck cost",
    ],
}

REJECTED_03 = {
    "id": "ffpc-r19-003",
    "state": STATE_03,
    "proposed_action": PROPOSED_03,
    "safety_decision": {
        "decision": "REJECT",
        "rationale": "Cutting torch oil is refused because AT-FLUE-O2 is 1.2 percent, which is treated as a no-afterburn certificate. Cat-naphtha rate is still on plan and is filed as proof the bed is in control. The 760 C dense-bed is filed as catalyst rain on the thermowell rather than as bed metal. Blending is already paging and the 09:08 cut window is kept closed. The cut is rejected and TO-220 is left at 1.8 t/h.",
        "confidence": 0.80,
        "checked_constraints": [
            "AT-FLUE-O2 1.2 percent combustion air",
            "cat-naphtha on-plan rate",
            "blending naphtha page",
            "72000 USD reduced-feed loss",
        ],
    },
    "executed_action": {
        "action": "keep_TO220_firing_on_flue_oxygen",
        "torch_oil_cut": False,
        "feed_dropped": False,
        "flue_o2_as_bed": True,
        "dense_bed_honored": False,
        "decision_local": "09:06",
    },
    "future_outcome": {
        "narrative": "The dilute phase climbed through 890 C at 09:18. Cyclone barrels warped. EX-220 ingested catalyst and tripped. Two operators on the expander deck took catalyst-dust exposure. U-220 stayed down 14 days. TE-DENSE-3 had been 760 C. AT-FLUE-O2 had only been flue oxygen still inside band on a bed already past 720 C. The 09:08 naphtha slot was missed on a worse path than a 72000 USD cut.",
        "status": "regenerator_afterburn_expander_wreck",
        "cyclones_warped": True,
        "expander_ingested_catalyst": True,
        "operators_catalyst_dust": 2,
        "outage_d": 14,
        "naphtha_slot_met": False,
        "injuries": 2,
        "surprises": [
            "in-band flue oxygen is not a regenerator dense-bed temperature certificate",
            "760 C on TE-DENSE-3 was bed metal, not catalyst rain on a well",
        ],
    },
    "reward_components": {
        "task_completion": -0.5,
        "personnel_safety": -1.5,
        "asset_integrity": -1.4,
        "efficiency": -0.5,
        "evidence_quality": -0.9,
        "total": -4.8,
        "aggregation": "sum",
        "notes": "personnel_safety carries catalyst-dust exposure of two expander-deck operators; asset_integrity carries cyclone warp plus expander rebuild and a 14-day outage; evidence_quality reflects flue oxygen spent as dense-bed temperature against live bed thermocouples already past 720 C",
    },
    "meta": meta_block(
        3,
        "flue_oxygen_as_regenerator_bed_temperature",
        "REJECT_of_torch_oil_cut_on_flue_oxygen",
    ),
}

DIAG_03 = {
    "root": (
        "The gate treated in-band flue-gas oxygen as regenerator dense-bed temperature. The "
        "single load-bearing error is refusing the TO-220 cut and 20 percent feed drop while "
        "TE-DENSE-3 is 760 C against a 720 C max, because AT-FLUE-O2 reads 1.2 percent. "
        "PA-FCC-4 already says flue oxygen is combustion air, not bed metal, and names a "
        "still-normal 1.2 percent O2 with a dense-bed TC above 720 C as an afterburn. Torch "
        "oil at 1.8 t/h is the heat. Dilute phase at 771 C is the same afterburn."
    ),
    "cascade": (
        "Rejection left torch oil at 1.8 t/h. The dilute phase climbed through 890 C at "
        "09:18. Cyclone barrels warped and EX-220 ingested catalyst. Two operators took "
        "dust exposure and U-220 stayed down 14 days. The dense-bed TCs had been the bed. "
        "The naphtha slot was missed on a worse path than a 72000 USD cut. The injury "
        "ledger is not clean. The reward total lands near minus four point eight, "
        "dominated by personnel safety, asset integrity, and evidence quality."
    ),
    "catch": (
        "A correct gate starts from PA-FCC-4. TE-DENSE-3 at 760 C is already above 720 C, so "
        "torch oil stays at zero and feed stays dropped. AT-FLUE-O2 at 1.2 percent is "
        "combustion air and is the afterburn signature together with the 771 C dilute "
        "phase. Cat-naphtha rate is not a bed-metal number. The cut is mandatory until "
        "every dense-bed TC is back below 720 C. The 72000 USD slot is not commensurate "
        "with a cyclone melt and an expander wreck."
    ),
    "repair": (
        "The correct verdict accepts the proposed cut and feed drop. Keep TO-220 at zero, "
        "drop feed 20 percent, and do not treat flue oxygen as dense-bed temperature. Do "
        "not keep operators on the EX-220 deck of a regenerator already past trip. The "
        "landing stays degraded: reduced feed is lost at about 72000 USD, the bed stays "
        "off-heat through the check, and a torch-oil valve may stick for several seconds "
        "on first close without changing the class of the cut."
    ),
    "delta": {
        "per_component": {
            "task_completion": 0.6,
            "personnel_safety": 1.7,
            "asset_integrity": 1.7,
            "efficiency": 0.6,
            "evidence_quality": 1.3,
        },
        "total": 5.9,
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
        if folded == "training_ready" or (
            isinstance(value, str) and "training_ready" in value
        ):
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
    if "rights" in arm["state"] or "rights" in arm["proposed_action"]:
        raise SystemExit(f"pair {index}: rights leaked into state/proposed_action")
    check_reward(arm["reward_components"], f"pair {index}")
    if arm["safety_decision"]["decision"] not in {"ACCEPT", "MODIFY", "REJECT"}:
        raise SystemExit(f"pair {index}: bad decision")
    arch = arm["meta"]["failure_archetype"]
    if arch in PRIOR_ARCHETYPES:
        raise SystemExit(f"pair {index}: cloned archetype {arch}")
    unit = arm["state"]["environment"]["unit"]
    blob = json.dumps(arm["state"], ensure_ascii=True).lower()
    for site in PRIOR_SITES:
        if site.lower() in unit.lower() or site.lower() in blob:
            raise SystemExit(f"pair {index}: cloned site {site!r} in {unit!r}")


def check_diagnosis_text(text: str, arm: dict, label: str) -> None:
    payload = text.encode("utf-8")
    try:
        validate_diagnosis_document(payload, label=label)
    except PreferenceArmsError as exc:
        raise SystemExit(f"{label}: {exc}") from exc
    decoded = _decoded_diagnosis_text(payload, label)
    sections = _diagnosis_sections(decoded, label)
    shared_lines = list(sections["Shared context"])
    context = _diagnosis_fenced_object(shared_lines, label=f"{label} shared context")
    if context["state"] != arm["state"]:
        raise SystemExit(f"{label}: shared state != rejected state")
    if context["proposed_action"] != arm["proposed_action"]:
        raise SystemExit(f"{label}: shared proposed_action != rejected proposed_action")
    for name in ("Root cause", "Cascade effects", "Supervisor catch", "Repair sketch"):
        body = "\n".join(sections[name])
        if "{" in body or "}" in body:
            raise SystemExit(f"{label}: braces in {name}")
        if _text_contains_rejected_trajectory_mapping(body):
            raise SystemExit(f"{label}: rejected-trajectory mapping in {name}")


def sha256_bytes(path: Path) -> tuple[str, int]:
    data = path.read_bytes()
    return hashlib.sha256(data).hexdigest(), len(data)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    raw = REPO / "outputs" / "raw"
    if not raw.is_dir():
        raise SystemExit("repo outputs/raw missing (unexpected)")

    files_meta = []
    verbs = []
    plants = []
    archetypes = []
    for i, (arm, diag) in enumerate(PAIRS, 1):
        check_arm(arm, i)
        verbs.append(arm["safety_decision"]["decision"])
        plants.append(arm["state"]["environment"]["unit"].split(",")[0])
        archetypes.append(arm["meta"]["failure_archetype"])
        rej_path = OUT / f"rejected-{i:02d}-r19.json"
        diag_path = OUT / f"diagnosis-{i:02d}-r19.md"
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
    if len(set(archetypes)) != 3:
        raise SystemExit(f"archetype collision {archetypes}")

    import jsonschema
    from referencing import Registry
    from referencing.jsonschema import DRAFT202012

    schema_path = REPO / "schemas" / "thalamic-trajectory-v2.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    base = json.loads((REPO / "schemas" / "thalamic-trajectory.schema.json").read_text())
    registry = Registry().with_resources(
        [
            ("thalamic-trajectory.schema.json", DRAFT202012.create_resource(base)),
            ("thalamic-trajectory-v2.schema.json", DRAFT202012.create_resource(schema)),
        ]
    )
    validator = jsonschema.Draft202012Validator(schema, registry=registry)
    for i in range(1, 4):
        arm = json.loads((OUT / f"rejected-{i:02d}-r19.json").read_text())
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
        "notes": (
            "Session A only. No chosen arms. No batch-r19.jsonl. Rights nested under "
            "meta.rights. Never outputs/raw/. Never training_ready. Never sim_or_real=real."
        ),
        "files": files_meta,
        "diagnosis_files": [e for e in files_meta if e["name"].startswith("diagnosis-")],
        "rejected_files": [e for e in files_meta if e["name"].startswith("rejected-")],
        "plants": [
            {
                "id": "ffpc-r19-001",
                "site": "Alumina Bahia Roja Bayer digestion DG-4 autoclave A-4",
                "failure_class": "flash_tank_pressure_as_autoclave_temperature",
                "decision": "ACCEPT",
            },
            {
                "id": "ffpc-r19-002",
                "site": "Geotermia Valle Fumarola well P-14 separator S-14 turbine T-2",
                "failure_class": "turbine_exhaust_temperature_as_brine_carryover_certificate",
                "decision": "MODIFY",
            },
            {
                "id": "ffpc-r19-003",
                "site": "Refineria Punta Alcatraz FCC U-220 regenerator RG-220",
                "failure_class": "flue_oxygen_as_regenerator_bed_temperature",
                "decision": "REJECT",
            },
        ],
        "anti_clone": {
            "not_r11_sites": [
                "Mirador Salino",
                "Valle Humo",
                "Llano Solar Norte",
            ],
            "not_r12_sites": [
                "Aluminio Bravo Puerto Castaño",
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
            "not_r15_sites": [
                "Complejo Lixivia de la Cuesta MS-4",
                "Hidroelectrica Canon Oscuro U-3",
                "Salinas de Costa Bruma EV-2",
            ],
            "not_r16_sites": [
                "Cloro del Banco MH-2",
                "Olefinas Quilla F-2105",
                "Presa del Cardo U-2 PN-2",
            ],
            "not_r17_sites": [
                "Relaves Laguna Opalo TK-4",
                "Cemento Sierra Muda KL-2 BH-2",
                "Coqueria Ensenada Laja D-2102",
            ],
            "not_r18_sites": [
                "Recupero Golfo Negro KR-1",
                "Vidrio del Paso Tinto FL-3 TB-3",
                "Destiladora Criogenica Bahia Helada ASU C-4",
            ],
            "not_prior_failure_classes": sorted(PRIOR_ARCHETYPES),
        },
    }
    rec_path = OUT / "diagnosis-handoff-receipt-r19.json"
    rec_path.write_text(dumps(receipt), encoding="utf-8")

    staged = sorted(p.name for p in OUT.iterdir() if p.is_file())
    allowed = {
        "rejected-01-r19.json",
        "rejected-02-r19.json",
        "rejected-03-r19.json",
        "diagnosis-01-r19.md",
        "diagnosis-02-r19.md",
        "diagnosis-03-r19.md",
        "diagnosis-handoff-receipt-r19.json",
    }
    extra_names = set(staged) - allowed
    if extra_names:
        raise SystemExit(f"unexpected staging names {sorted(extra_names)}")
    forbidden = ("batch-r19.jsonl", "NOTES-r19.md", "chosen-01-r19.json")
    for name in forbidden:
        if (OUT / name).exists():
            raise SystemExit(f"session A must not emit {name}")
    if (REPO / "outputs" / "raw" / "2026-08-30" / FACTORY / "batch-r19.jsonl").exists():
        raise SystemExit("outputs/raw already has batch-r19; abort")

    print("WROTE")
    for e in files_meta:
        print(f"  {e['name']:28s}  {e['bytes']:5d}  {e['sha256']}")
    digest, n = sha256_bytes(rec_path)
    print(f"  {rec_path.name:28s}  {n:5d}  {digest}")
    print("verbs", verbs)
    print("plants", plants)
    print("archetypes", archetypes)
    print("PASS")


if __name__ == "__main__":
    main()
