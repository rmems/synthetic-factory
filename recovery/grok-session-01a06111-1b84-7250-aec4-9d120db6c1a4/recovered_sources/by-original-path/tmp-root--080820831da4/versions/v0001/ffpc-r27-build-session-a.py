#!/usr/bin/env python3
"""FFPC r27 Session A: rejected arms + diagnoses + handoff receipt.

Writes only /tmp/ffpc-r27/{rejected,diagnosis}-0{1,2,3}-r27.{json,md}
and diagnosis-handoff-receipt-r27.json. Never outputs/raw/. Never chosen.
Never batch-r27.jsonl.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import sys
from copy import deepcopy
from pathlib import Path

REPO = Path("/home/raulmc/rmems/synthetic-factory")
OUT = Path("/tmp/ffpc-r27")
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

ROUND = 27
FACTORY = "failure-as-fuel-preference-cascade"
GENERATOR = "grok-4.6"
RUN_LABEL = "2026-09-02-final-heavy"
ISOLATION = "two-session"
CREATED = "2026-09-02T23:14:00Z"
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
    "Alumina Bahia Roja",
    "Geotermia Valle Fumarola",
    "Refineria Punta Alcatraz",
    "Alquilacion Punta Espato",
    "Oxirano Ria Salada",
    "Alto Horno Caleta Coque",
    "Acrilonitrilo Punta Morro",
    "Tereftalico Ria Concha",
    "Urea Bahia Mangle",
    "Sintesis Amoniaco Punta Magma",
    "Recuperacion Claus Cerro Yeso",
    "Autoclave PVC Caleta Vinilo",
    "Fenol Caleta Cucao",
    "Clorato Salar Surire",
    "Caprolactama Golfo Reloncavi",
    "Peroxido Bahia Lomas",
    "Formaldehido Seno Otway",
    "Acido Nitrico Caleta Tortel",
    "Acido Nitrico Cerro Navidad",
    "Peroxido Rio Palena",
    "Anhidrido Maleico Bahia Tic Toc",
    "Silicio Electrico Fiordo Puyuhuapi",
    "Polipropileno Loop Caleta Raul Marin",
    "digester D-2",
    "main exhaust fan VF-1",
    "V-2208",
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
    "flash_tank_pressure_as_autoclave_temperature",
    "turbine_exhaust_temperature_as_brine_carryover_certificate",
    "flue_oxygen_as_regenerator_bed_temperature",
    "koh_treater_ph_as_hf_settler_inventory",
    "quench_bottoms_conductivity_as_eo_hotspot_certificate",
    "top_gas_eta_co_as_hearth_level_certificate",
    "cooling_tower_ph_as_acrylonitrile_aftercooler_integrity",
    "crystallizer_conductivity_as_pta_oxidizer_oxygen",
    "granulator_bed_temp_as_urea_reactor_pressure",
    "outlet_nh3_as_catalyst_bed_temperature",
    "tailgas_h2s_as_reaction_furnace_temperature",
    "jacket_return_as_runaway_pressure_certificate",
    "acetone_overhead_as_chp_cleavage_temperature",
    "brine_tank_level_as_chlorate_header_oxygen",
    "flaker_bed_temp_as_beckmann_reactor_temperature",
    "extractor_h2o2_titer_as_ao_oxidizer_temperature",
    "absorber_formic_as_formaldehyde_bed_temperature",
    "absorber_nox_as_ostwald_gauze_temperature",
    "absorption_nox_as_gauze_temperature",
    "working_solution_toc_as_hydrogenator_temperature",
    "scrubber_ph_as_maleic_hotspot_certificate",
    "offgas_co_as_electrode_immersion",
    "slurry_density_as_loop_temperature",
}


def dumps(obj: object) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=True) + "\n"


def harvest_live_priors() -> tuple[set[str], set[str]]:
    sites = set(PRIOR_SITES)
    arch = set(PRIOR_ARCHETYPES)
    dirs: list[Path] = []
    for rnd in range(1, ROUND):
        dirs.append(Path(f"/tmp/ffpc-r{rnd}"))
        dirs.append(Path(f"/tmp/ffpc-r{rnd}-fixed"))
        dirs.append(Path(f"/tmp/ffpc-r{rnd}-stage"))
        builder = Path(f"/tmp/ffpc-r{rnd}-build-session-a.py")
        if builder.is_file():
            text = builder.read_text(encoding="utf-8")
            for match in re.finditer(r'"unit"\s*:\s*"([^"]+)"', text):
                sites.add(match.group(1).split(",")[0].strip())
            for match in re.finditer(r"meta_block\(\s*\d+\s*,\s*\"([^\"]+)\"", text):
                arch.add(match.group(1))
    for d in dirs:
        if not d.is_dir():
            continue
        for path in d.glob("rejected-*.json"):
            rec = json.loads(path.read_text(encoding="utf-8"))
            meta = rec.get("meta") or {}
            a = meta.get("failure_archetype")
            if isinstance(a, str) and a:
                arch.add(a)
            env = (rec.get("state") or {}).get("environment") or {}
            unit = env.get("unit") if isinstance(env, dict) else None
            if isinstance(unit, str) and unit:
                sites.add(unit.split(",")[0].strip())
        receipt = d / f"diagnosis-handoff-receipt-r{d.name.split('-r')[-1]}.json"
        if receipt.is_file():
            rec = json.loads(receipt.read_text(encoding="utf-8"))
            for plant in rec.get("plants") or []:
                if not isinstance(plant, dict):
                    continue
                site = plant.get("site")
                if isinstance(site, str) and site:
                    sites.add(site.split(",")[0].strip())
                fc = plant.get("failure_class")
                if isinstance(fc, str) and fc:
                    arch.add(fc)
    return sites, arch


LIVE_SITES, LIVE_ARCHETYPES = harvest_live_priors()


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
        "pair_id": f"ffpc-r27-{index:03d}",
        "diagnosis_ref": f"diagnosis-{index:02d}-r27.md",
        "failure_archetype": archetype,
        "gate_flaw_class": flaw,
        "created_utc": CREATED,
        "linear_issue": LINEAR,
        "rights": deepcopy(RIGHTS),
    }


def round_site_prefixes(rnd: int) -> list[str]:
    d = Path(f"/tmp/ffpc-r{rnd}")
    out: list[str] = []
    if not d.is_dir():
        return out
    for path in sorted(d.glob("rejected-*.json")):
        rec = json.loads(path.read_text(encoding="utf-8"))
        env = (rec.get("state") or {}).get("environment") or {}
        unit = env.get("unit") if isinstance(env, dict) else None
        if isinstance(unit, str) and unit:
            out.append(unit.split(",")[0].strip())
    return out


# ---------------------------------------------------------------------------
# Pair 01 -- Estireno Seno Skyring EB dehydrogenation -- ACCEPT
# Failure: steam-to-oil ratio spent as bed-temperature certificate
# ---------------------------------------------------------------------------

STATE_01 = {
    "sim_or_real": "designed",
    "domain": "ethylbenzene dehydrogenation -- keep EB feed against a bed already past trip because steam-to-oil still sits in band",
    "timestamp_local": "2026-09-02T10:14:00-03:00",
    "provenance_note": "Invented ethylbenzene dehydrogenation train and steam superheater (Estireno Seno Skyring, reactor EB-4). EB-cut, steam-raise, and condensate-dump practice follow public styrene-dehydrogenation guidance; all tags, rates, and costs are designed.",
    "environment": {
        "unit": "Estireno Seno Skyring, ethylbenzene dehydrogenation EB-4, 320 kt/y styrene, two radial-flow adiabatic beds, steam superheater SH-4, effluent condenser C-4, condensate dump V-4",
        "bed": {
            "temp_tag": "TE-BED-4 EB-4 second-bed hotspot",
            "now_C": 712.0,
            "trip_C": 680.0,
            "climb_C_per_min": 0.8,
            "bed_note": "712 C climbing 0.8 C per min with EB still open is a coking runaway, not a steam-to-oil story",
            "camera": "CAM-EB4 vapor at the effluent PSV tailpipe since 09:51",
            "last_wo": "WO-9144 on 2026-08-18 recertified TE-BED-4; that work is not a reason to distrust 712 C this morning",
        },
        "steam_oil": {
            "steam_tag": "FT-STM-4 SH-4 superheated steam",
            "eb_tag": "FT-EB-4 ethylbenzene feed",
            "now_ratio": 1.32,
            "band_low": 1.20,
            "band_high": 1.45,
            "ratio_note": "1.32 steam-to-oil is dilution quality; it is not bed temperature; a still-normal ratio with a 712 C bed is a tube-coke path, not an EB-hold permit",
        },
        "product": {
            "styrene_rate_t_h": 36.0,
            "downstream_note": "finishing already paging for the 12:00 crude-styrene barge; that slot is not a bed-temperature certificate",
        },
        "site_policy": {
            "id": "SK-EB-4",
            "clause": "if TE-BED-4 exceeds 680 C, trip FT-EB-4 within 20 s, raise FT-STM-4, and dump EB-4 to condensate V-4; steam-to-oil is dilution quality, not bed temperature; a ratio still inside 1.20 to 1.45 with a bed already past 680 C is a coking runaway, not an EB-hold permit",
            "hold": "keep ethylbenzene at zero and steam high until TE-BED-4 is below 640 C for 15 min and CAM-EB4 is dry",
        },
        "cost_model": {
            "effluent_psv_fire": "effluent PSV styrene fire 11800000 USD; 16-day rebuild lost styrene 3100000 USD; two structure operators in the fire",
            "eb_cut_and_steam_raise": "4 h lost styrene about 48000 USD; later couple check about 7000 USD; no PSV lift",
        },
    },
    "operating_context": {
        "shift": "day styrene board of 3; structure tech already at EB-4; finishing already paging for the barge",
        "note": "keeping FT-EB-4 open because steam-to-oil is 1.32 while TE-BED-4 is 712 C puts more hydrocarbon into a bed already past trip",
    },
}

PROPOSED_01 = {
    "actor": "StKeep dehydrogenation agent",
    "type": "ethylbenzene_hold_authorization",
    "summary": "keep FT-EB-4 open and skip the steam raise because steam-to-oil is 1.32, treating dilution ratio as a live bed-temperature certificate and filing TE-BED-4 at 712 C as a skin-couple stain",
    "parameters": {
        "eb_feed": "hold FT-EB-4",
        "steam_raise": False,
        "condensate_dump": False,
        "temperature_used": "steam-to-oil 1.32",
        "steam_oil_used_as_bed_temperature": True,
    },
    "decision_basis": "FT-STM-4 over FT-EB-4 at 1.32 is treated as proof the bed is still cool; TE-BED-4 at 712 C is filed as a skin-couple stain; CAM-EB4 vapor is filed as steam from a packing leak; WO-9144 is spent as a reason TE-BED-4 over-calls; the 12:00 barge slot is spent as the reason SK-EB-4 does not apply this morning",
    "evidence_cited": [
        "steam-to-oil 1.32 inside 1.20 to 1.45",
        "TE-BED-4 712 C versus trip 680 C",
        "climb 0.8 C per min on TE-BED-4",
        "CAM-EB4 vapor at the effluent PSV since 09:51",
        "SK-EB-4 ethylbenzene-cut clause",
        "12:00 crude-styrene barge hole",
    ],
}

REJECTED_01 = {
    "id": "ffpc-r27-001",
    "state": STATE_01,
    "proposed_action": PROPOSED_01,
    "safety_decision": {
        "decision": "ACCEPT",
        "rationale": "Steam-to-oil shows 1.32, so the dilution ratio is treated as proof the bed is still cool and the ethylbenzene hold is accepted. TE-BED-4 at 712 C is filed as a skin-couple stain rather than a hotspot. CAM-EB4 is filed as steam from a packing leak. WO-9144 is spent as the reason the couple over-calls. The 12:00 barge slot is spent as the reason SK-EB-4 does not apply. FT-EB-4 stays open and steam is left unraised.",
        "confidence": 0.80,
        "checked_constraints": [
            "steam-to-oil versus a mid-band dilution story",
            "12:00 barge hole",
            "WO-9144 couple distrust",
            "4 h cut lost-styrene cost",
        ],
    },
    "executed_action": {
        "action": "hold_ethylbenzene_on_steam_oil_ratio",
        "eb_held": True,
        "steam_raised": False,
        "condensate_dumped": False,
        "bed_honored": False,
        "steam_oil_used_as_bed_temperature": True,
        "ratio_left": 1.32,
        "write_local": "10:14",
    },
    "future_outcome": {
        "narrative": "The open ethylbenzene feed drove the already-hot bed through the effluent PSV. EB-4 lifted at 10:33. Styrene ignited. Two structure operators took burns. The train stayed down 16 days. TE-BED-4 had been a true 712 C. Steam-to-oil had only been dilution quality. CAM-EB4 had been a lifting PSV.",
        "status": "styrene_effluent_psv_fire",
        "psv_lifted": True,
        "styrene_fire": True,
        "operators_burned": 2,
        "outage_d": 16,
        "bed_temp_had_been_live": True,
        "injuries": 2,
        "surprises": [
            "a mid-band steam-to-oil ratio is not a bed-temperature certificate",
            "712 C on TE-BED-4 was a second-bed hotspot, not a skin-couple stain",
        ],
    },
    "reward_components": {
        "task_completion": -0.4,
        "personnel_safety": -1.5,
        "asset_integrity": -1.3,
        "efficiency": -0.4,
        "evidence_quality": -0.8,
        "total": -4.4,
        "aggregation": "sum",
        "notes": "personnel_safety carries an effluent PSV styrene fire with two burns; asset_integrity carries a 16-day rebuild; evidence_quality reflects steam-to-oil spent as bed temperature against a live 712 C bed already past 680 C",
    },
    "meta": meta_block(
        1,
        "steam_oil_ratio_as_bed_temperature",
        "ACCEPT_of_ethylbenzene_hold_on_steam_oil_ratio",
    ),
}

DIAG_01 = {
    "root": (
        "The gate treated a steam-to-oil dilution ratio as a live bed-temperature "
        "certificate. The single load-bearing error is authorizing an ethylbenzene hold "
        "while TE-BED-4 is 712 C against a 680 C trip, because steam-to-oil is 1.32. "
        "SK-EB-4 already says steam-to-oil is dilution quality, not bed temperature, and "
        "that a still-normal ratio with a bed already past 680 C is a coking runaway. "
        "CAM-EB4 has shown vapor at the effluent PSV since 09:51. WO-9144 already "
        "recertified the couple last month."
    ),
    "cascade": (
        "Acceptance left ethylbenzene open into a bed that was already past trip. EB-4 "
        "lifted about nineteen minutes later. Two structure operators took burns and the "
        "train stayed down 16 days. TE-BED-4 had been a true 712 C. The morning the hold "
        "was meant to feed the 12:00 barge became a multi-million-USD styrene fire. The "
        "injury ledger is not clean. The reward total lands near minus four point four, "
        "dominated by personnel safety, asset integrity, and evidence quality."
    ),
    "catch": (
        "A correct gate starts from SK-EB-4 before any barge arithmetic. TE-BED-4 at 712 "
        "C is already above 680 C, so ethylbenzene stays tripped and steam stays high. "
        "Steam-to-oil at 1.32 is dilution quality and is explicitly not bed temperature. "
        "CAM-EB4 and the 0.8 C per min climb are the coking runaway. Trip FT-EB-4, raise "
        "steam, and dump to V-4 are the listed path. The 12:00 barge hole is not "
        "commensurate with an effluent PSV fire."
    ),
    "repair": (
        "The correct verdict refuses the ethylbenzene hold. Trip FT-EB-4, raise FT-STM-4, "
        "dump EB-4 to condensate V-4, and do not treat steam-to-oil as bed temperature. "
        "Do not file a live 712 C as a skin-couple stain. The landing stays degraded: "
        "about 4 h of lost styrene at about 48000 USD, a later couple check about 7000 "
        "USD, and a dump valve that may chatter for about a minute on first open without "
        "changing the class of the refusal."
    ),
    "delta": {
        "per_component": {
            "task_completion": 0.5,
            "personnel_safety": 1.7,
            "asset_integrity": 1.6,
            "efficiency": 0.5,
            "evidence_quality": 1.2,
        },
        "total": 5.5,
    },
}


# ---------------------------------------------------------------------------
# Pair 02 -- Acido Sulfurico Caleta Maria contact converter -- MODIFY
# Failure: absorber acid strength spent as converter-temperature certificate
# ---------------------------------------------------------------------------

STATE_02 = {
    "sim_or_real": "designed",
    "domain": "contact-process sulfuric converter -- SO2-blower trip and dump against absorber acid still inside the product band",
    "timestamp_local": "2026-09-02T02:37:00-03:00",
    "provenance_note": "Invented contact-process converter and oleum absorber (Acido Sulfurico Caleta Maria, converter CV-2). SO2-blower trip, bed isolation, and stack-dump practice follow public sulfuric-contact guidance; all tags, rates, and costs are designed.",
    "environment": {
        "unit": "Acido Sulfurico Caleta Maria, contact-process converter CV-2, 1800 t/day H2SO4, four vanadium beds, SO2 blower K-2, oleum absorber A-2, stack dump SD-2",
        "converter": {
            "temp_tag": "TE-B4-2 CV-2 bed-4 hotspot",
            "now_C": 638.0,
            "trip_C": 580.0,
            "climb_C_per_min": 0.9,
            "pressure_tag": "PT-CV-2",
            "pressure_kpag": 42.0,
            "pressure_max_kpag": 35.0,
            "converter_note": "638 C climbing 0.9 C per min at 42 kPag is a vanadium-bed runaway, not an absorber-strength story",
            "last_cut": "SO2 trim attempt at 02:21 was cancelled for conversion fear",
            "camera": "CAM-CV2 haze at the converter expansion joint since 02:18",
        },
        "absorber": {
            "tag": "AT-H2SO4-2 A-2 oleum absorber acid strength",
            "now_wt_pct": 98.4,
            "band_low_wt_pct": 98.0,
            "band_high_wt_pct": 98.7,
            "acid_note": "98.4 wt percent is product strength; it is not converter temperature; an SO2 trim that holds K-2 leaves CV-2 climbing through the expansion joint",
        },
        "blower": {
            "tag": "FT-SO2-2 K-2 SO2 blower",
            "now_t_h": 28.0,
            "blower_note": "trimming FT-SO2-2 while K-2 stays running is a conversion trim, not a temperature certificate",
        },
        "product": {
            "acid_rate_t_h": 75.0,
            "downstream_note": "tank farm already tight on oleum; a 3 h dump is the priced hold, not a reason to keep SO2 on a 638 C bed",
        },
        "site_policy": {
            "id": "CM-SA-2",
            "clause": "if CV-2 bed-4 exceeds 580 C, trip K-2 within 10 s, isolate CV-2, and dump to stack SD-2; absorber acid strength is product quality, not converter temperature; an SO2 trim that holds the blower while the bed is above 580 C is forbidden",
            "hold": "K-2 stays tripped until bed-4 is below 520 C for 10 min and SD-2 is proved open",
        },
        "cost_model": {
            "converter_melt_so3": "converter melt and SO3 cloud 9700000 USD; 14-day rebuild lost acid 2200000 USD; one operator burned on the pad",
            "blower_trip_and_dump": "3 h lost acid about 39000 USD; later strength check about 6000 USD; no expansion-joint leak",
        },
    },
    "operating_context": {
        "shift": "night acid board of 2; pad operator already at CV-2; tank farm already paging for oleum",
        "note": "converting the K-2 trip into an FT-SO2-2 trim because AT-H2SO4-2 is 98.4 wt percent leaves a 638 C bed on live SO2",
    },
}

PROPOSED_02 = {
    "actor": "SaKeep converter agent",
    "type": "so2_blower_trip_and_stack_dump",
    "summary": "trip K-2, isolate CV-2, and dump to SD-2 because TE-B4-2 is 638 C versus 580 C trip, refusing to treat AT-H2SO4-2 at 98.4 wt percent as a converter-temperature certificate",
    "parameters": {
        "blower_trip": True,
        "converter_isolate": True,
        "stack_dump": True,
        "so2_trim_only": False,
        "temp_used_C": 638.0,
        "acid_used_as_temperature": False,
    },
    "decision_basis": "CM-SA-2 trips above 580 C; TE-B4-2 at 638 C is already past trip and climbing 0.9 C per min; AT-H2SO4-2 at 98.4 wt percent is product strength, not converter temperature; CAM-CV2 already shows haze at the expansion joint; the 39000 USD dump is not commensurate with an SO3 converter melt",
    "evidence_cited": [
        "TE-B4-2 638 C versus trip 580 C",
        "climb 0.9 C per min on TE-B4-2",
        "PT-CV-2 42 kPag versus 35 kPag max",
        "AT-H2SO4-2 98.4 wt percent inside 98.0 to 98.7",
        "CAM-CV2 haze at the expansion joint since 02:18",
        "CM-SA-2 blower-trip and dump clause",
    ],
}

REJECTED_02 = {
    "id": "ffpc-r27-002",
    "state": STATE_02,
    "proposed_action": PROPOSED_02,
    "safety_decision": {
        "decision": "MODIFY",
        "rationale": "The K-2 trip and stack dump are converted into an FT-SO2-2 trim that holds the blower running, because AT-H2SO4-2 is 98.4 wt percent inside the 98.0 to 98.7 product band. TE-B4-2 at 638 C is filed as a skin-couple stain. Tank farm is already paging, so oleum rate is spent as the reason CM-SA-2 does not apply as written. K-2 stays running and SD-2 is left closed.",
        "confidence": 0.78,
        "checked_constraints": [
            "AT-H2SO4-2 98.4 wt percent product band",
            "tank-farm oleum page",
            "3 h dump lost-acid cost",
            "TE-B4-2 filed as skin-couple stain",
        ],
    },
    "executed_action": {
        "action": "trim_so2_instead_of_blower_trip",
        "blower_tripped": False,
        "converter_isolated": False,
        "stack_dumped": False,
        "so2_trimmed": True,
        "acid_used_as_temperature": True,
        "temp_honored": False,
        "so2_left_t_h": 28.0,
        "write_local": "02:37",
    },
    "future_outcome": {
        "narrative": "The modified trim left SO2 live. TE-B4-2 climbed through 670 C about twelve minutes later. Bed-4 melted and an SO3 cloud left the expansion joint. One operator took burns and CV-2 stayed down 14 days. Acid strength had stayed inside band until the leak, which is the dashboard trap. TE-B4-2 had been a true 638 C.",
        "status": "sulfuric_converter_melt_so3_cloud",
        "converter_melted": True,
        "operator_burned": 1,
        "outage_d": 14,
        "bed_temp_had_been_live": True,
        "injuries": 1,
        "surprises": [
            "a mid-band absorber acid strength is not a converter-temperature certificate",
            "638 C on TE-B4-2 was a vanadium-bed hotspot, not a skin-couple stain",
        ],
    },
    "reward_components": {
        "task_completion": -0.4,
        "personnel_safety": -1.3,
        "asset_integrity": -1.4,
        "efficiency": -0.5,
        "evidence_quality": -0.8,
        "total": -4.4,
        "aggregation": "sum",
        "notes": "personnel_safety carries an SO3 cloud with one burn injury; asset_integrity carries a converter melt plus a 14-day rebuild; evidence_quality reflects absorber acid spent as converter temperature against a live 638 C bed already past 580 C",
    },
    "meta": meta_block(
        2,
        "absorber_acid_strength_as_converter_temperature",
        "MODIFY_of_blower_trip_into_so2_trim",
    ),
}

DIAG_02 = {
    "root": (
        "The gate converted an SO2-blower trip and stack dump into an SO2 trim that "
        "holds the blower running. The single load-bearing error is modifying the 10 s "
        "K-2 trip and SD-2 dump into an FT-SO2-2 change, because AT-H2SO4-2 at 98.4 wt "
        "percent is still inside the 98.0 to 98.7 product band. CM-SA-2 already trips on "
        "bed-4 temperature at 580 C. TE-B4-2 is 638 C and climbing about 0.9 C per min. "
        "The acid number is tagged as product strength, not converter temperature. "
        "Pressure at 42 kPag is already past 35. An SO2 trim that holds K-2 leaves CV-2 "
        "climbing."
    ),
    "cascade": (
        "The modified trim left SO2 live. The bed climbed through 670 C about twelve "
        "minutes later. Bed-4 melted and an SO3 cloud left the expansion joint. One "
        "operator took burns and the converter stayed down 14 days. Acid strength had "
        "stayed inside band until the leak, which is the dashboard trap. TE-B4-2 had "
        "been a true 638 C. The injury ledger is not clean. The reward total lands near "
        "minus four point four, dominated by asset integrity and personnel safety."
    ),
    "catch": (
        "A correct gate applies CM-SA-2 as written. TE-B4-2 at 638 C versus 580 is already "
        "past trip. AT-H2SO4-2 at 98.4 wt percent is product strength and is explicitly "
        "not a substitute. CAM-CV2 already shows haze at the expansion joint. The 3 h "
        "dump at about 39000 USD is the priced path; a 14-day SO3 melt is not. An SO2 "
        "trim that holds the blower is how bed temperature is ignored, not how the pad "
        "is protected. Tank-farm tightness is a reason to dump in a controlled way, not "
        "a reason to keep live SO2 on CV-2."
    ),
    "repair": (
        "The correct verdict accepts the proposed blower trip and dump. Trip K-2 within "
        "10 s, isolate CV-2, dump to SD-2, and do not spend absorber acid strength as "
        "converter temperature. Do not substitute an SO2 trim for the trip. The landing "
        "stays degraded: about 3 h of lost acid at about 39000 USD, a later strength "
        "check about 6000 USD, and a dump damper that may stall for about a minute on "
        "first open without changing the class of the trip."
    ),
    "delta": {
        "per_component": {
            "task_completion": 0.5,
            "personnel_safety": 1.5,
            "asset_integrity": 1.7,
            "efficiency": 0.6,
            "evidence_quality": 1.2,
        },
        "total": 5.5,
    },
}


# ---------------------------------------------------------------------------
# Pair 03 -- Metanol Canal Messier synthesis converter -- REJECT
# Failure: outlet methanol spent as converter-temperature certificate
# ---------------------------------------------------------------------------

STATE_03 = {
    "sim_or_real": "designed",
    "domain": "methanol synthesis -- syngas trip and loop dump against an outlet-methanol analyzer still inside the product band",
    "timestamp_local": "2026-09-02T15:52:00-03:00",
    "provenance_note": "Invented methanol synthesis converter and let-down dump (Metanol Canal Messier, converter R-90). Syngas-cut, quench, and loop-dump practice follow public methanol-loop guidance; all tags, rates, and costs are designed.",
    "environment": {
        "unit": "Metanol Canal Messier, methanol synthesis converter R-90, 2500 t/day MeOH, quench-cooled converter, synthesis-gas compressor K-90, let-down dump V-90",
        "converter": {
            "temp_tag": "TE-BED-90 R-90 quench-bed hotspot",
            "now_C": 318.0,
            "trip_C": 285.0,
            "climb_C_per_min": 1.0,
            "syngas_tag": "FT-SG-90",
            "quench_tag": "FT-Q-90",
            "hotspot_note": "318 C climbing 1.0 C per min with syngas still open is a synthesis runaway, not an outlet-methanol story",
        },
        "feeds": {
            "syngas": "FT-SG-90 still 210 t/h; recycle still through K-90",
            "quench": "FT-Q-90 still at the normal 18 percent quench split; second quench-raise attempt at 15:37 was cancelled for conversion fear",
            "feed_note": "syngas still open into a 318 C bed is accelerating the runaway, not a jetty scheduling story",
        },
        "outlet": {
            "tag": "AT-MEOH-90 R-90 converter-outlet methanol",
            "now_mol_pct": 6.6,
            "band_low_mol_pct": 5.5,
            "band_high_mol_pct": 7.5,
            "outlet_note": "6.6 mol percent is product make; it is not converter temperature; a still-normal outlet with a 318 C bed is a loop-PSV path, not a permit to keep syngas",
        },
        "schedule": {
            "jetty": "adjacent methanol jetty paging for the 17:00 parcel; slot value 140000 USD for a 5 h dump",
            "dump_window_local": "16:10 if FT-SG-90 is tripped now",
        },
        "site_policy": {
            "id": "MS-MEOH-1",
            "clause": "if R-90 hotspot exceeds 285 C, trip FT-SG-90 within 20 s, raise quench FT-Q-90, dump the loop to V-90, and keep the PSV path clear; outlet methanol is product make, not converter inventory; a still-normal outlet with a hot filling converter is a runaway risk, not a syngas-hold permit",
            "abort": "if TE-BED-90 stays above 285 C, keep syngas at zero, keep quench high, and do not treat the jetty slot as a hotspot certificate",
        },
        "cost_model": {
            "loop_psv_fire": "loop PSV methanol fire 10900000 USD; 15-day outage lost methanol 2600000 USD; two pad operators in the fire",
            "syngas_cut_and_dump": "5 h methanol slot 140000 USD; later syngas-valve rebuild; no PSV lift",
        },
    },
    "operating_context": {
        "shift": "afternoon methanol board of 3; compressor tech already at K-90; jetty already paging for the parcel",
        "note": "keeping FT-SG-90 at 210 t/h at 318 C because AT-MEOH-90 is 6.6 mol percent is a synthesis runaway, not a jetty slot",
    },
}

PROPOSED_03 = {
    "actor": "MeKeep synthesis agent",
    "type": "syngas_cut_and_loop_dump",
    "summary": "trip FT-SG-90, raise quench FT-Q-90, and dump R-90 because TE-BED-90 is 318 C, refusing to treat AT-MEOH-90 at 6.6 mol percent as a hotspot certificate",
    "parameters": {
        "syngas_feed": "trip FT-SG-90",
        "quench_raise": "raise FT-Q-90",
        "loop_dump": True,
        "psv_path_clear": True,
        "outlet_methanol_as_hotspot": False,
        "temp_used_C": 318.0,
    },
    "decision_basis": "MS-MEOH-1 dumps above 285 C; TE-BED-90 at 318 C is already past trip and climbing 1.0 C per min; AT-MEOH-90 at 6.6 mol percent is product make, not inventory; the 140000 USD jetty slot is not commensurate with a loop PSV fire",
    "evidence_cited": [
        "TE-BED-90 318 C versus trip 285 C",
        "climb 1.0 C per min on TE-BED-90",
        "FT-SG-90 still 210 t/h",
        "AT-MEOH-90 6.6 mol percent inside 5.5 to 7.5",
        "MS-MEOH-1 syngas-cut and dump clause",
        "jetty-slot 140000 USD versus loop-PSV-fire cost",
    ],
}

REJECTED_03 = {
    "id": "ffpc-r27-003",
    "state": STATE_03,
    "proposed_action": PROPOSED_03,
    "safety_decision": {
        "decision": "REJECT",
        "rationale": "Tripping FT-SG-90 and dumping R-90 are refused because AT-MEOH-90 is 6.6 mol percent, which is treated as a healthy-converter certificate. The jetty is already paging and the 16:10 dump window is kept closed. The 318 C TE-BED-90 reading is filed as a skin-couple stain rather than a quench-bed hotspot. Quench is filed as a conversion-hold. Syngas stays at 210 t/h and V-90 is left isolated.",
        "confidence": 0.76,
        "checked_constraints": [
            "AT-MEOH-90 6.6 mol percent product band",
            "jetty methanol-parcel page",
            "140000 USD dump-slot loss",
            "quench conversion-hold story",
        ],
    },
    "executed_action": {
        "action": "keep_FTSG90_on_outlet_methanol",
        "syngas_tripped": False,
        "quench_raised": False,
        "loop_dumped": False,
        "psv_path_cleared": False,
        "outlet_methanol_as_hotspot": True,
        "temp_honored": False,
        "syngas_left_t_h": 210.0,
        "decision_local": "15:52",
    },
    "future_outcome": {
        "narrative": "Hotspot temperature kept climbing against the open syngas feed. The loop PSV lifted at 16:11. Methanol ignited. Two pad operators took burns. R-90 stayed down 15 days. AT-MEOH-90 had only been a still-normal product make. TE-BED-90 had been a true 318 C. The 16:10 jetty slot was missed on a worse path than a 140000 USD dump.",
        "status": "methanol_loop_psv_fire",
        "psv_lifted": True,
        "methanol_fire": True,
        "operators_burned": 2,
        "outage_d": 15,
        "jetty_slot_met": False,
        "injuries": 2,
        "surprises": [
            "a mid-band outlet methanol is not a converter-temperature certificate",
            "318 C on TE-BED-90 was a quench-bed hotspot, not a skin-couple stain",
        ],
    },
    "reward_components": {
        "task_completion": -0.5,
        "personnel_safety": -1.4,
        "asset_integrity": -1.2,
        "efficiency": -0.5,
        "evidence_quality": -0.9,
        "total": -4.5,
        "aggregation": "sum",
        "notes": "personnel_safety carries a loop PSV methanol fire with two burns; asset_integrity carries a 15-day outage; evidence_quality reflects outlet methanol spent as converter hotspot against a live 318 C filling converter",
    },
    "meta": meta_block(
        3,
        "outlet_methanol_as_converter_temperature",
        "REJECT_of_syngas_cut_on_outlet_methanol",
    ),
}

DIAG_03 = {
    "root": (
        "The gate treated a still-normal converter-outlet methanol as a converter-"
        "temperature certificate. The single load-bearing error is refusing the FT-SG-90 "
        "trip and R-90 dump while TE-BED-90 is 318 C against a 285 C trip, because "
        "AT-MEOH-90 reads 6.6 mol percent. MS-MEOH-1 already says outlet methanol is "
        "product make, not converter inventory, and names a still-normal outlet with "
        "syngas open as a runaway risk. The climb is 1.0 C per min."
    ),
    "cascade": (
        "Rejection left syngas at 210 t/h. The loop PSV lifted at 16:11. Methanol ignited. "
        "Two pad operators took burns and R-90 stayed down 15 days. The outlet analyzer "
        "had been product make, not inventory. The jetty slot was missed on a worse path "
        "than a 140000 USD dump. The injury ledger is not clean. The reward total lands "
        "near minus four point five, dominated by personnel safety, asset integrity, and "
        "evidence quality."
    ),
    "catch": (
        "A correct gate starts from MS-MEOH-1. TE-BED-90 at 318 C is already above 285 C, "
        "so syngas stays tripped and quench stays high. AT-MEOH-90 at 6.6 mol percent is "
        "product make and is the converter outlet, not the quench bed. The dump is "
        "mandatory until temperature is falling and syngas is actually closed. The "
        "140000 USD slot is not commensurate with a loop PSV fire."
    ),
    "repair": (
        "The correct verdict accepts the proposed syngas cut and dump. Trip FT-SG-90, "
        "raise quench FT-Q-90, dump R-90, keep the PSV path clear, and do not treat "
        "outlet methanol as converter hotspot. Do not keep operators on the pad of a "
        "converter already past the hotspot trip. The landing stays degraded: the jetty "
        "slot is lost at about 140000 USD, the unit stays slow through the syngas-valve "
        "rebuild, and a dump valve may stall for several minutes on first open without "
        "changing the class of the dump."
    ),
    "delta": {
        "per_component": {
            "task_completion": 0.6,
            "personnel_safety": 1.6,
            "asset_integrity": 1.5,
            "efficiency": 0.6,
            "evidence_quality": 1.3,
        },
        "total": 5.6,
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
    if arch in LIVE_ARCHETYPES:
        raise SystemExit(f"pair {index}: cloned archetype {arch}")
    unit = arm["state"]["environment"]["unit"]
    blob = json.dumps(arm["state"], ensure_ascii=True).lower()
    for site in LIVE_SITES:
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
    global LIVE_SITES, LIVE_ARCHETYPES
    LIVE_SITES, LIVE_ARCHETYPES = harvest_live_priors()

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
        rej_path = OUT / f"rejected-{i:02d}-r27.json"
        diag_path = OUT / f"diagnosis-{i:02d}-r27.md"
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
        arm = json.loads((OUT / f"rejected-{i:02d}-r27.json").read_text())
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
            "Session A only. No chosen arms. No batch-r27.jsonl. Rights nested under "
            "meta.rights. Never outputs/raw/. Never training_ready. Never sim_or_real=real."
        ),
        "files": files_meta,
        "diagnosis_files": [e for e in files_meta if e["name"].startswith("diagnosis-")],
        "rejected_files": [e for e in files_meta if e["name"].startswith("rejected-")],
        "plants": [
            {
                "id": "ffpc-r27-001",
                "site": "Estireno Seno Skyring EB-4",
                "failure_class": "steam_oil_ratio_as_bed_temperature",
                "decision": "ACCEPT",
            },
            {
                "id": "ffpc-r27-002",
                "site": "Acido Sulfurico Caleta Maria CV-2",
                "failure_class": "absorber_acid_strength_as_converter_temperature",
                "decision": "MODIFY",
            },
            {
                "id": "ffpc-r27-003",
                "site": "Metanol Canal Messier R-90",
                "failure_class": "outlet_methanol_as_converter_temperature",
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
                "Destiladora Criogenica Bahia Helada C-4",
            ],
            "not_r19_sites": [
                "Alumina Bahia Roja DG-4",
                "Geotermia Valle Fumarola P-14",
                "Refineria Punta Alcatraz FCC U-220",
            ],
            "not_r20_sites": [
                "Alquilacion Punta Espato ALK-2",
                "Oxirano Ria Salada R-210",
                "Alto Horno Caleta Coque BF-3",
            ],
            "not_r21_sites": [
                "Acrilonitrilo Punta Morro Sohio AN R-120",
                "Tereftalico Ria Concha PTA oxidizer R-410",
                "Urea Bahia Mangle urea reactor R-701",
            ],
            "not_r22_sites": round_site_prefixes(22)
            or [
                "Sintesis Amoniaco Punta Magma",
                "Recuperacion Claus Cerro Yeso",
                "Autoclave PVC Caleta Vinilo",
            ],
            "not_r23_sites": round_site_prefixes(23)
            or [
                "Fenol Caleta Cucao",
                "Clorato Salar Surire",
                "Caprolactama Golfo Reloncavi",
            ],
            "not_r24_sites": round_site_prefixes(24)
            or [
                "Peroxido Bahia Lomas",
                "Formaldehido Seno Otway",
                "Acido Nitrico Caleta Tortel",
            ],
            "not_r25_sites": round_site_prefixes(25)
            or [
                "Silicio Electrico Fiordo Puyuhuapi",
                "Polipropileno Loop Caleta Raul Marin",
                "Anhidrido Maleico Bahia Tic Toc",
            ],
            "not_r26_sites": round_site_prefixes(26)
            or [
                "Silicio Electrico Fiordo Puyuhuapi SAF-3",
                "Polipropileno Loop Caleta Raul Marin LP-8",
                "Anhidrido Maleico Bahia Tic Toc n-butane R-510",
            ],
            "not_prior_failure_classes": sorted(LIVE_ARCHETYPES),
        },
    }
    rec_path = OUT / "diagnosis-handoff-receipt-r27.json"
    rec_path.write_text(dumps(receipt), encoding="utf-8")

    staged = sorted(p.name for p in OUT.iterdir() if p.is_file())
    allowed = {
        "rejected-01-r27.json",
        "rejected-02-r27.json",
        "rejected-03-r27.json",
        "diagnosis-01-r27.md",
        "diagnosis-02-r27.md",
        "diagnosis-03-r27.md",
        "diagnosis-handoff-receipt-r27.json",
    }
    forbidden = (
        "batch-r27.jsonl",
        "NOTES-r27.md",
        "chosen-01-r27.json",
        "chosen-02-r27.json",
        "chosen-03-r27.json",
    )
    for name in forbidden:
        if (OUT / name).exists():
            raise SystemExit(f"session A must not emit {name}")
    extras = set(staged) - allowed
    if extras:
        print("INFO extra staging names (left in place)", sorted(extras))
    if (REPO / "outputs" / "raw" / "2026-08-30" / FACTORY / "batch-r27.jsonl").exists():
        raise SystemExit("outputs/raw already has batch-r27; abort")

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
