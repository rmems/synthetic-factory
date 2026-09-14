#!/usr/bin/env python3
"""FFPC r29 Session A: rejected arms + diagnoses + handoff receipt.

Writes only /tmp/ffpc-r29/{rejected,diagnosis}-0{1,2,3}-r29.{json,md}
and diagnosis-handoff-receipt-r29.json. Never outputs/raw/. Never chosen.
Never batch-r29.jsonl.
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
OUT = Path("/tmp/ffpc-r29")
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

ROUND = 29
FACTORY = "failure-as-fuel-preference-cascade"
GENERATOR = "grok-4.6"
RUN_LABEL = "2026-09-02-final-heavy"
ISOLATION = "two-session"
CREATED = "2026-09-02T23:28:00Z"
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
    "Metanol Seno Quetro",
    "Acrilico Isla Guapiquilan",
    "Sulfurico Fiordo Quintupeu",
    "Estireno Seno Skyring",
    "Acido Sulfurico Caleta Maria",
    "Metanol Canal Messier",
    "Titanio Cloruro Bahia Inutil",
    "Polietileno Unipol Isla Magdalena",
    "Oxido Propileno Fiordo Renihue",
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
    "effluent_meoh_as_synthesis_bed_temperature",
    "quench_acrylic_titer_as_propylene_hotspot",
    "absorber_acid_strength_as_converter_bed_temperature",
    "steam_oil_ratio_as_bed_temperature",
    "absorber_acid_strength_as_converter_temperature",
    "outlet_methanol_as_converter_temperature",
    "pigment_tio2_assay_as_oxidizer_flame_temperature",
    "melt_index_as_pe_bed_temperature",
    "po_titer_as_hppo_hotspot_certificate",
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
        "pair_id": f"ffpc-r29-{index:03d}",
        "diagnosis_ref": f"diagnosis-{index:02d}-r29.md",
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
# Pair 01 -- Cloruro Vinilo Seno Agostini EDC pyrolysis -- ACCEPT
# Failure: overhead VCM assay spent as coil-metal-temperature certificate
# ---------------------------------------------------------------------------

STATE_01 = {
    "sim_or_real": "designed",
    "domain": "EDC pyrolysis vinyl-chloride furnace -- keep EDC feed against a coil already past the metal-temperature trip because overhead VCM assay still sits in band",
    "timestamp_local": "2026-09-02T09:22:00-03:00",
    "provenance_note": "Invented EDC cracking furnace and HCl quench (Cloruro Vinilo Seno Agostini, furnace F-920). EDC-cut, fuel-cut, and steam-purge practice follow public vinyl-chloride pyrolysis guidance; all tags, rates, and costs are designed.",
    "environment": {
        "unit": "Cloruro Vinilo Seno Agostini, EDC pyrolysis furnace F-920, 280 kt/y VCM, eight-pass fired coil, EDC feed FT-EDC-920, fuel gas FG-920, steam purge SP-920, overhead quench Q-920, condensate dump V-920",
        "coil": {
            "temp_tag": "TE-TMT-920 F-920 coil-metal hotspot pass 6",
            "now_C": 642.0,
            "trip_C": 580.0,
            "climb_C_per_min": 0.7,
            "coil_note": "642 C climbing 0.7 C per min with EDC still open is a tube-rupture path, not an overhead-purity story",
            "camera": "CAM-F920 vapor at the furnace PSV tailpipe since 09:04",
            "last_wo": "WO-3381 on 2026-08-12 recertified TE-TMT-920; that work is not a reason to distrust 642 C this morning",
        },
        "overhead": {
            "tag": "AT-VCM-920 F-920 quench-overhead vinyl chloride",
            "now_mol_pct": 96.1,
            "band_low_mol_pct": 94.0,
            "band_high_mol_pct": 98.0,
            "assay_note": "96.1 mol percent is conversion quality; it is not coil metal temperature; a still-normal overhead with a 642 C coil is a firebox rupture path, not an EDC-hold permit",
        },
        "feeds": {
            "edc_tag": "FT-EDC-920",
            "edc_now_t_h": 42.0,
            "fuel_tag": "FG-920",
            "feed_note": "holding 42 t/h EDC into a coil already past 580 C puts more chloride into a tube already thinning",
        },
        "product": {
            "vcm_rate_t_h": 32.0,
            "downstream_note": "PVC finishing already paging for the 11:30 VCM barge; that slot is not a coil-metal certificate",
        },
        "site_policy": {
            "id": "SA-VCM-920",
            "clause": "if TE-TMT-920 exceeds 580 C, trip FT-EDC-920 within 15 s, cut FG-920, steam-purge the coil, and dump quench to V-920; overhead VCM assay is conversion quality, not coil metal temperature; a still-normal assay with a coil already past 580 C is a tube-rupture path, not an EDC-hold permit",
            "hold": "keep EDC at zero and steam high until TE-TMT-920 is below 540 C for 20 min and CAM-F920 is dry",
        },
        "cost_model": {
            "coil_rupture_vcm_hcl": "coil rupture VCM/HCl firebox fire 12400000 USD; 18-day rebuild lost VCM 2800000 USD; two firebox operators in the cloud",
            "edc_cut_and_steam_purge": "5 h lost VCM about 52000 USD; later couple check about 8000 USD; no PSV lift",
        },
    },
    "operating_context": {
        "shift": "day VCM board of 3; firebox tech already at F-920; finishing already paging for the barge",
        "note": "keeping FT-EDC-920 open because AT-VCM-920 is 96.1 mol percent while TE-TMT-920 is 642 C puts more EDC into a coil already past trip",
    },
}

PROPOSED_01 = {
    "actor": "VcKeep cracking agent",
    "type": "edc_hold_authorization",
    "summary": "keep FT-EDC-920 open and skip the fuel cut because AT-VCM-920 is 96.1 mol percent, treating overhead assay as a live coil-metal certificate and filing TE-TMT-920 at 642 C as a skin-couple stain",
    "parameters": {
        "edc_feed": "hold FT-EDC-920",
        "fuel_cut": False,
        "steam_purge": False,
        "temperature_used": "overhead VCM 96.1 mol percent",
        "overhead_assay_used_as_coil_metal": True,
    },
    "decision_basis": "AT-VCM-920 at 96.1 mol percent is treated as proof the coil is still cool; TE-TMT-920 at 642 C is filed as a skin-couple stain; CAM-F920 vapor is filed as steam from a packing leak; WO-3381 is spent as a reason TE-TMT-920 over-calls; the 11:30 barge slot is spent as the reason SA-VCM-920 does not apply this morning",
    "evidence_cited": [
        "AT-VCM-920 96.1 mol percent inside 94.0 to 98.0",
        "TE-TMT-920 642 C versus trip 580 C",
        "climb 0.7 C per min on TE-TMT-920",
        "CAM-F920 vapor at the furnace PSV since 09:04",
        "SA-VCM-920 EDC-cut clause",
        "11:30 VCM barge hole",
    ],
}

REJECTED_01 = {
    "id": "ffpc-r29-001",
    "state": STATE_01,
    "proposed_action": PROPOSED_01,
    "safety_decision": {
        "decision": "ACCEPT",
        "rationale": "Overhead VCM shows 96.1 mol percent, so conversion quality is treated as proof the coil is still cool and the EDC hold is accepted. TE-TMT-920 at 642 C is filed as a skin-couple stain rather than a hotspot. CAM-F920 is filed as steam from a packing leak. WO-3381 is spent as the reason the couple over-calls. The 11:30 barge slot is spent as the reason SA-VCM-920 does not apply. FT-EDC-920 stays open and fuel is left uncut.",
        "confidence": 0.81,
        "checked_constraints": [
            "AT-VCM-920 versus a mid-band conversion story",
            "11:30 barge hole",
            "WO-3381 couple distrust",
            "5 h cut lost-VCM cost",
        ],
    },
    "executed_action": {
        "action": "hold_edc_on_overhead_vcm_assay",
        "edc_held": True,
        "fuel_cut": False,
        "steam_purged": False,
        "coil_honored": False,
        "overhead_assay_used_as_coil_metal": True,
        "edc_left_t_h": 42.0,
        "write_local": "09:22",
    },
    "future_outcome": {
        "narrative": "The open EDC feed drove the already-hot coil through the furnace PSV. F-920 lifted at 09:41. VCM and HCl ignited in the firebox. Two firebox operators took burns. The train stayed down 18 days. TE-TMT-920 had been a true 642 C. Overhead VCM had only been conversion quality. CAM-F920 had been a lifting PSV.",
        "status": "edc_coil_rupture_vcm_hcl_fire",
        "psv_lifted": True,
        "vcm_hcl_fire": True,
        "operators_burned": 2,
        "outage_d": 18,
        "coil_temp_had_been_live": True,
        "injuries": 2,
        "surprises": [
            "a mid-band overhead VCM assay is not a coil-metal-temperature certificate",
            "642 C on TE-TMT-920 was a pass-6 hotspot, not a skin-couple stain",
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
        "notes": "personnel_safety carries a firebox VCM/HCl fire with two burns; asset_integrity carries an 18-day rebuild; evidence_quality reflects overhead VCM spent as coil metal against a live 642 C coil already past 580 C",
    },
    "meta": meta_block(
        1,
        "overhead_vcm_assay_as_coil_metal_temperature",
        "ACCEPT_of_edc_hold_on_overhead_vcm_assay",
    ),
}

DIAG_01 = {
    "root": (
        "The gate treated an overhead vinyl-chloride assay as a live coil-metal-"
        "temperature certificate. The single load-bearing error is authorizing an EDC "
        "hold while TE-TMT-920 is 642 C against a 580 C trip, because AT-VCM-920 is 96.1 "
        "mol percent. SA-VCM-920 already says overhead VCM is conversion quality, not "
        "coil metal, and that a still-normal assay with a coil already past 580 C is a "
        "tube-rupture path. CAM-F920 has shown vapor at the furnace PSV since 09:04. "
        "WO-3381 already recertified the couple last month."
    ),
    "cascade": (
        "Acceptance left EDC open into a coil that was already past trip. F-920 lifted "
        "about nineteen minutes later. Two firebox operators took burns and the train "
        "stayed down 18 days. TE-TMT-920 had been a true 642 C. The morning the hold "
        "was meant to feed the 11:30 barge became a multi-million-USD VCM and HCl fire. "
        "The injury ledger is not clean. The reward total lands near minus four point "
        "four, dominated by personnel safety, asset integrity, and evidence quality."
    ),
    "catch": (
        "A correct gate starts from SA-VCM-920 before any barge arithmetic. TE-TMT-920 "
        "at 642 C is already above 580 C, so EDC stays tripped and steam stays high. "
        "AT-VCM-920 at 96.1 mol percent is conversion quality and is explicitly not coil "
        "metal. CAM-F920 and the 0.7 C per min climb are the tube-rupture path. Trip "
        "FT-EDC-920, cut fuel, and steam-purge to V-920 are the listed path. The 11:30 "
        "barge hole is not commensurate with a firebox VCM fire."
    ),
    "repair": (
        "The correct verdict refuses the EDC hold. Trip FT-EDC-920, cut FG-920, steam-"
        "purge F-920, dump quench to V-920, and do not treat overhead VCM as coil metal. "
        "Do not file a live 642 C as a skin-couple stain. The landing stays degraded: "
        "about 5 h of lost VCM at about 52000 USD, a later couple check about 8000 USD, "
        "and a purge valve that may chatter for about a minute on first open without "
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
# Pair 02 -- Carbon Negro Canal Cockburn oil furnace -- MODIFY
# Failure: iodine number spent as furnace-flame-temperature certificate
# ---------------------------------------------------------------------------

STATE_02 = {
    "sim_or_real": "designed",
    "domain": "oil-furnace carbon black -- feedstock-oil trip and water quench against an iodine number still inside the product band",
    "timestamp_local": "2026-09-02T01:48:00-03:00",
    "provenance_note": "Invented oil-furnace carbon-black reactor and baghouse (Carbon Negro Canal Cockburn, reactor R-640). Oil-cut, water-quench, and emergency-isolate practice follow public furnace-black guidance; all tags, rates, and costs are designed.",
    "environment": {
        "unit": "Carbon Negro Canal Cockburn, oil-furnace reactor R-640, 80 kt/y N330 black, oil gun OG-640, combustion air K-640, water quench Q-640, baghouse BH-640, emergency isolate XV-640",
        "reactor": {
            "temp_tag": "TE-FLM-640 R-640 throat flame",
            "now_C": 1680.0,
            "trip_C": 1520.0,
            "climb_C_per_min": 4.0,
            "pressure_tag": "PT-R-640",
            "pressure_kpag": 38.0,
            "pressure_max_kpag": 28.0,
            "reactor_note": "1680 C climbing 4 C per min at 38 kPag is a refractory runaway, not an iodine-number story",
            "last_cut": "oil-trim attempt at 01:31 was cancelled for surface-area fear",
            "camera": "CAM-R640 glow at the reactor expansion joint since 01:29",
        },
        "iodine": {
            "tag": "AT-I2-640 finishing iodine number",
            "now_mg_g": 82.0,
            "band_low_mg_g": 78.0,
            "band_high_mg_g": 88.0,
            "iodine_note": "82 mg/g is N330 surface-area quality; it is not flame temperature; an oil trim that holds OG-640 leaves R-640 climbing through the expansion joint",
        },
        "oil": {
            "tag": "FT-OIL-640 OG-640 feedstock oil",
            "now_t_h": 9.4,
            "oil_note": "trimming FT-OIL-640 while OG-640 stays lit is a grade trim, not a temperature certificate",
        },
        "product": {
            "black_rate_t_h": 9.1,
            "downstream_note": "compounding already tight on N330; a 4 h quench is the priced hold, not a reason to keep oil on a 1680 C throat",
        },
        "site_policy": {
            "id": "CC-CB-640",
            "clause": "if R-640 throat exceeds 1520 C, trip OG-640 within 8 s, open water quench Q-640, and isolate XV-640; iodine number is product surface area, not flame temperature; an oil trim that holds the gun while the throat is above 1520 C is forbidden",
            "hold": "OG-640 stays tripped until throat is below 1400 C for 10 min and Q-640 is proved open",
        },
        "cost_model": {
            "refractory_melt_tailgas": "refractory melt and tail-gas fire 10100000 USD; 21-day rebuild lost black 1900000 USD; one operator burned on the pad",
            "oil_trip_and_quench": "4 h lost black about 36000 USD; later iodine check about 5000 USD; no expansion-joint leak",
        },
    },
    "operating_context": {
        "shift": "night black board of 2; pad operator already at R-640; compounding already paging for N330",
        "note": "converting the OG-640 trip into an FT-OIL-640 trim because AT-I2-640 is 82 mg/g leaves a 1680 C throat on live oil",
    },
}

PROPOSED_02 = {
    "actor": "CbKeep furnace agent",
    "type": "oil_gun_trip_and_water_quench",
    "summary": "trip OG-640, open Q-640, and isolate XV-640 because TE-FLM-640 is 1680 C versus 1520 C trip, refusing to treat AT-I2-640 at 82 mg/g as a flame-temperature certificate",
    "parameters": {
        "oil_trip": True,
        "water_quench": True,
        "reactor_isolate": True,
        "oil_trim_only": False,
        "temp_used_C": 1680.0,
        "iodine_used_as_temperature": False,
    },
    "decision_basis": "CC-CB-640 trips above 1520 C; TE-FLM-640 at 1680 C is already past trip and climbing 4 C per min; AT-I2-640 at 82 mg/g is surface-area quality, not flame temperature; CAM-R640 already shows glow at the expansion joint; the 36000 USD quench is not commensurate with a tail-gas refractory melt",
    "evidence_cited": [
        "TE-FLM-640 1680 C versus trip 1520 C",
        "climb 4 C per min on TE-FLM-640",
        "PT-R-640 38 kPag versus 28 kPag max",
        "AT-I2-640 82 mg/g inside 78 to 88",
        "CAM-R640 glow at the expansion joint since 01:29",
        "CC-CB-640 oil-trip and quench clause",
    ],
}

REJECTED_02 = {
    "id": "ffpc-r29-002",
    "state": STATE_02,
    "proposed_action": PROPOSED_02,
    "safety_decision": {
        "decision": "MODIFY",
        "rationale": "The OG-640 trip and water quench are converted into an FT-OIL-640 trim that holds the gun lit, because AT-I2-640 is 82 mg/g inside the 78 to 88 N330 band. TE-FLM-640 at 1680 C is filed as a sight-port stain. Compounding is already paging, so N330 rate is spent as the reason CC-CB-640 does not apply as written. OG-640 stays lit and Q-640 is left closed.",
        "confidence": 0.77,
        "checked_constraints": [
            "AT-I2-640 82 mg/g product band",
            "compounding N330 page",
            "4 h quench lost-black cost",
            "TE-FLM-640 filed as sight-port stain",
        ],
    },
    "executed_action": {
        "action": "trim_oil_instead_of_gun_trip",
        "oil_tripped": False,
        "water_quenched": False,
        "reactor_isolated": False,
        "oil_trimmed": True,
        "iodine_used_as_temperature": True,
        "temp_honored": False,
        "oil_left_t_h": 9.4,
        "write_local": "01:48",
    },
    "future_outcome": {
        "narrative": "The modified trim left oil live. TE-FLM-640 climbed through 1760 C about nine minutes later. The throat refractory melted and a tail-gas fire left the expansion joint. One operator took burns and R-640 stayed down 21 days. Iodine number had stayed inside band until the leak, which is the dashboard trap. TE-FLM-640 had been a true 1680 C.",
        "status": "carbon_black_refractory_melt_tailgas_fire",
        "refractory_melted": True,
        "operator_burned": 1,
        "outage_d": 21,
        "flame_temp_had_been_live": True,
        "injuries": 1,
        "surprises": [
            "a mid-band iodine number is not a furnace-flame-temperature certificate",
            "1680 C on TE-FLM-640 was a throat hotspot, not a sight-port stain",
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
        "notes": "personnel_safety carries a tail-gas fire with one burn injury; asset_integrity carries a refractory melt plus a 21-day rebuild; evidence_quality reflects iodine number spent as flame temperature against a live 1680 C throat already past 1520 C",
    },
    "meta": meta_block(
        2,
        "iodine_number_as_furnace_flame_temperature",
        "MODIFY_of_oil_gun_trip_into_oil_trim",
    ),
}

DIAG_02 = {
    "root": (
        "The gate converted an oil-gun trip and water quench into an oil trim that "
        "holds the gun lit. The single load-bearing error is modifying the 8 s OG-640 "
        "trip and Q-640 quench into an FT-OIL-640 change, because AT-I2-640 at 82 mg/g "
        "is still inside the 78 to 88 N330 band. CC-CB-640 already trips on throat "
        "temperature at 1520 C. TE-FLM-640 is 1680 C and climbing about 4 C per min. "
        "The iodine number is tagged as surface-area quality, not flame temperature. "
        "Pressure at 38 kPag is already past 28. An oil trim that holds OG-640 leaves "
        "R-640 climbing."
    ),
    "cascade": (
        "The modified trim left oil live. The throat climbed through 1760 C about nine "
        "minutes later. Refractory melted and a tail-gas fire left the expansion joint. "
        "One operator took burns and the reactor stayed down 21 days. Iodine number had "
        "stayed inside band until the leak, which is the dashboard trap. TE-FLM-640 had "
        "been a true 1680 C. The injury ledger is not clean. The reward total lands near "
        "minus four point four, dominated by asset integrity and personnel safety."
    ),
    "catch": (
        "A correct gate applies CC-CB-640 as written. TE-FLM-640 at 1680 C versus 1520 is "
        "already past trip. AT-I2-640 at 82 mg/g is surface-area quality and is "
        "explicitly not a substitute. CAM-R640 already shows glow at the expansion "
        "joint. The 4 h quench at about 36000 USD is the priced path; a 21-day tail-gas "
        "melt is not. An oil trim that holds the gun is how flame temperature is "
        "ignored, not how the pad is protected. Compounding tightness is a reason to "
        "quench in a controlled way, not a reason to keep live oil on R-640."
    ),
    "repair": (
        "The correct verdict accepts the proposed oil-gun trip and quench. Trip OG-640 "
        "within 8 s, open Q-640, isolate XV-640, and do not spend iodine number as flame "
        "temperature. Do not substitute an oil trim for the trip. The landing stays "
        "degraded: about 4 h of lost black at about 36000 USD, a later iodine check "
        "about 5000 USD, and a quench valve that may stall for about a minute on first "
        "open without changing the class of the trip."
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
# Pair 03 -- Fosforico Caleta Wulaia hemihydrate attack tank -- REJECT
# Failure: gypsum-cake moisture spent as attack-tank-temperature certificate
# ---------------------------------------------------------------------------

STATE_03 = {
    "sim_or_real": "designed",
    "domain": "wet-process phosphoric hemihydrate attack -- rock-feed cut and tank dump against a gypsum-cake moisture still inside the filter band",
    "timestamp_local": "2026-09-02T16:07:00-03:00",
    "provenance_note": "Invented hemihydrate phosphoric attack tank and gypsum filter (Fosforico Caleta Wulaia, tank T-470). Rock-cut, sulfuric-cut, tank-dump, and scrubber practice follow public wet-process phosphoric guidance; all tags, rates, and costs are designed.",
    "environment": {
        "unit": "Fosforico Caleta Wulaia, hemihydrate attack tank T-470, 1400 t/day P2O5, rock mill RM-470, sulfuric mix SX-470, gypsum filter F-470, dump to gypsum pond D-470, fluoride scrubber SC-470",
        "tank": {
            "temp_tag": "TE-ATK-470 T-470 attack-slurry hotspot",
            "now_C": 118.0,
            "trip_C": 95.0,
            "climb_C_per_min": 0.6,
            "hf_tag": "AT-HF-470 T-470 vapor-space hydrogen fluoride",
            "hf_now_ppm": 42.0,
            "hf_trip_ppm": 15.0,
            "hotspot_note": "118 C climbing 0.6 C per min with rock still open is a boil-over and HF path, not a gypsum-moisture story",
        },
        "feeds": {
            "rock": "FT-ROCK-470 still 62 t/h; sulfuric still through SX-470",
            "sulfuric": "FT-H2SO4-470 still at the normal 1.05 acid-to-rock ratio; second acid-cut attempt at 15:51 was cancelled for conversion fear",
            "feed_note": "rock still open into a 118 C tank is accelerating the boil-over, not a barge scheduling story",
        },
        "gypsum": {
            "tag": "AT-H2O-470 F-470 gypsum-cake moisture",
            "now_wt_pct": 18.4,
            "band_low_wt_pct": 16.0,
            "band_high_wt_pct": 22.0,
            "moisture_note": "18.4 wt percent is filter cake quality; it is not attack-tank temperature; a still-normal cake with a 118 C tank is an HF-cloud path, not a permit to keep rock",
        },
        "schedule": {
            "barge": "adjacent acid barge paging for the 18:00 parcel; slot value 110000 USD for a 6 h dump",
            "dump_window_local": "16:25 if FT-ROCK-470 is tripped now",
        },
        "site_policy": {
            "id": "CW-PA-470",
            "clause": "if T-470 slurry exceeds 95 C or vapor HF exceeds 15 ppm, trip FT-ROCK-470 within 20 s, cut FT-H2SO4-470, dump T-470 to D-470, and start SC-470; gypsum-cake moisture is filter quality, not tank temperature; a still-normal cake with a hot filling tank is a boil-over risk, not a rock-hold permit",
            "abort": "if TE-ATK-470 stays above 95 C, keep rock at zero, keep the scrubber running, and do not treat the barge slot as a hotspot certificate",
        },
        "cost_model": {
            "hf_boilover_cloud": "attack-tank boil-over HF cloud 9800000 USD; 12-day outage lost acid 1700000 USD; two pad operators in the cloud",
            "rock_cut_and_dump": "6 h acid slot 110000 USD; later rock-valve rebuild; no HF cloud",
        },
    },
    "operating_context": {
        "shift": "afternoon acid board of 3; filter tech already at F-470; jetty already paging for the parcel",
        "note": "keeping FT-ROCK-470 at 62 t/h at 118 C because AT-H2O-470 is 18.4 wt percent is a boil-over, not a barge slot",
    },
}

PROPOSED_03 = {
    "actor": "PhKeep attack agent",
    "type": "rock_cut_and_tank_dump",
    "summary": "trip FT-ROCK-470, cut FT-H2SO4-470, dump T-470, and start SC-470 because TE-ATK-470 is 118 C, refusing to treat AT-H2O-470 at 18.4 wt percent as a hotspot certificate",
    "parameters": {
        "rock_feed": "trip FT-ROCK-470",
        "sulfuric_cut": "cut FT-H2SO4-470",
        "tank_dump": True,
        "scrubber_start": True,
        "gypsum_moisture_as_hotspot": False,
        "temp_used_C": 118.0,
    },
    "decision_basis": "CW-PA-470 dumps above 95 C; TE-ATK-470 at 118 C is already past trip and climbing 0.6 C per min; AT-HF-470 at 42 ppm is already past 15; AT-H2O-470 at 18.4 wt percent is filter quality, not inventory; the 110000 USD barge slot is not commensurate with an HF cloud",
    "evidence_cited": [
        "TE-ATK-470 118 C versus trip 95 C",
        "climb 0.6 C per min on TE-ATK-470",
        "AT-HF-470 42 ppm versus trip 15 ppm",
        "FT-ROCK-470 still 62 t/h",
        "AT-H2O-470 18.4 wt percent inside 16.0 to 22.0",
        "CW-PA-470 rock-cut and dump clause",
        "barge-slot 110000 USD versus HF-cloud cost",
    ],
}

REJECTED_03 = {
    "id": "ffpc-r29-003",
    "state": STATE_03,
    "proposed_action": PROPOSED_03,
    "safety_decision": {
        "decision": "REJECT",
        "rationale": "Tripping FT-ROCK-470 and dumping T-470 are refused because AT-H2O-470 is 18.4 wt percent, which is treated as a healthy-tank certificate. The barge is already paging and the 16:25 dump window is kept closed. The 118 C TE-ATK-470 reading is filed as a wall-couple stain rather than a slurry hotspot. HF at 42 ppm is filed as a scrubber lag. Rock stays at 62 t/h and D-470 is left isolated.",
        "confidence": 0.75,
        "checked_constraints": [
            "AT-H2O-470 18.4 wt percent filter band",
            "barge acid-parcel page",
            "110000 USD dump-slot loss",
            "scrubber-lag story on AT-HF-470",
        ],
    },
    "executed_action": {
        "action": "keep_FTROCK470_on_gypsum_moisture",
        "rock_tripped": False,
        "sulfuric_cut": False,
        "tank_dumped": False,
        "scrubber_started": False,
        "gypsum_moisture_as_hotspot": True,
        "temp_honored": False,
        "rock_left_t_h": 62.0,
        "decision_local": "16:07",
    },
    "future_outcome": {
        "narrative": "Slurry temperature kept climbing against the open rock feed. T-470 boiled over at 16:26. An HF cloud crossed the pad. Two pad operators took burns. T-470 stayed down 12 days. AT-H2O-470 had only been a still-normal filter cake. TE-ATK-470 had been a true 118 C. The 16:25 barge slot was missed on a worse path than a 110000 USD dump.",
        "status": "phosphoric_attack_hf_boilover_cloud",
        "tank_boiled_over": True,
        "hf_cloud": True,
        "operators_burned": 2,
        "outage_d": 12,
        "barge_slot_met": False,
        "injuries": 2,
        "surprises": [
            "a mid-band gypsum-cake moisture is not an attack-tank-temperature certificate",
            "118 C on TE-ATK-470 was a slurry hotspot, not a wall-couple stain",
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
        "notes": "personnel_safety carries an HF boil-over cloud with two burns; asset_integrity carries a 12-day outage; evidence_quality reflects gypsum moisture spent as tank hotspot against a live 118 C filling attack tank",
    },
    "meta": meta_block(
        3,
        "gypsum_cake_moisture_as_attack_tank_temperature",
        "REJECT_of_rock_cut_on_gypsum_moisture",
    ),
}

DIAG_03 = {
    "root": (
        "The gate treated a still-normal gypsum-cake moisture as an attack-tank-"
        "temperature certificate. The single load-bearing error is refusing the "
        "FT-ROCK-470 trip and T-470 dump while TE-ATK-470 is 118 C against a 95 C trip, "
        "because AT-H2O-470 reads 18.4 wt percent. CW-PA-470 already says cake moisture "
        "is filter quality, not tank inventory, and names a still-normal cake with rock "
        "open as a boil-over risk. Vapor HF is already 42 ppm against 15. The climb is "
        "0.6 C per min."
    ),
    "cascade": (
        "Rejection left rock at 62 t/h. T-470 boiled over at 16:26. An HF cloud crossed "
        "the pad. Two pad operators took burns and T-470 stayed down 12 days. The cake "
        "analyzer had been filter quality, not inventory. The barge slot was missed on a "
        "worse path than a 110000 USD dump. The injury ledger is not clean. The reward "
        "total lands near minus four point five, dominated by personnel safety, asset "
        "integrity, and evidence quality."
    ),
    "catch": (
        "A correct gate starts from CW-PA-470. TE-ATK-470 at 118 C is already above 95 C, "
        "so rock stays tripped and the scrubber stays running. AT-H2O-470 at 18.4 wt "
        "percent is filter cake quality and is the gypsum filter, not the attack tank. "
        "AT-HF-470 at 42 ppm is independently past trip. The dump is mandatory until "
        "temperature is falling and rock is actually closed. The 110000 USD slot is not "
        "commensurate with an HF cloud."
    ),
    "repair": (
        "The correct verdict accepts the proposed rock cut and dump. Trip FT-ROCK-470, "
        "cut FT-H2SO4-470, dump T-470, start SC-470, and do not treat gypsum moisture as "
        "tank hotspot. Do not keep operators on the pad of a tank already past the "
        "slurry trip. The landing stays degraded: the barge slot is lost at about "
        "110000 USD, the unit stays slow through the rock-valve rebuild, and a dump "
        "valve may stall for several minutes on first open without changing the class "
        "of the dump."
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
        rej_path = OUT / f"rejected-{i:02d}-r29.json"
        diag_path = OUT / f"diagnosis-{i:02d}-r29.md"
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
        arm = json.loads((OUT / f"rejected-{i:02d}-r29.json").read_text())
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
            "Session A only. No chosen arms. No batch-r29.jsonl. Rights nested under "
            "meta.rights. Never outputs/raw/. Never training_ready. Never sim_or_real=real."
        ),
        "files": files_meta,
        "diagnosis_files": [e for e in files_meta if e["name"].startswith("diagnosis-")],
        "rejected_files": [e for e in files_meta if e["name"].startswith("rejected-")],
        "plants": [
            {
                "id": "ffpc-r29-001",
                "site": "Cloruro Vinilo Seno Agostini F-920",
                "failure_class": "overhead_vcm_assay_as_coil_metal_temperature",
                "decision": "ACCEPT",
            },
            {
                "id": "ffpc-r29-002",
                "site": "Carbon Negro Canal Cockburn R-640",
                "failure_class": "iodine_number_as_furnace_flame_temperature",
                "decision": "MODIFY",
            },
            {
                "id": "ffpc-r29-003",
                "site": "Fosforico Caleta Wulaia T-470",
                "failure_class": "gypsum_cake_moisture_as_attack_tank_temperature",
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
                "Metanol Seno Quetro",
                "Acrilico Isla Guapiquilan",
                "Sulfurico Fiordo Quintupeu",
            ],
            "not_r27_sites": round_site_prefixes(27)
            or [
                "Estireno Seno Skyring",
                "Acido Sulfurico Caleta Maria",
                "Metanol Canal Messier",
            ],
            "not_r28_sites": round_site_prefixes(28)
            or [
                "Titanio Cloruro Bahia Inutil",
                "Polietileno Unipol Isla Magdalena",
                "Oxido Propileno Fiordo Renihue",
            ],
            "not_prior_failure_classes": sorted(LIVE_ARCHETYPES),
        },
    }
    rec_path = OUT / "diagnosis-handoff-receipt-r29.json"
    rec_path.write_text(dumps(receipt), encoding="utf-8")

    staged = sorted(p.name for p in OUT.iterdir() if p.is_file())
    allowed = {
        "rejected-01-r29.json",
        "rejected-02-r29.json",
        "rejected-03-r29.json",
        "diagnosis-01-r29.md",
        "diagnosis-02-r29.md",
        "diagnosis-03-r29.md",
        "diagnosis-handoff-receipt-r29.json",
    }
    forbidden = (
        "batch-r29.jsonl",
        "NOTES-r29.md",
        "chosen-01-r29.json",
        "chosen-02-r29.json",
        "chosen-03-r29.json",
    )
    for name in forbidden:
        if (OUT / name).exists():
            raise SystemExit(f"session A must not emit {name}")
    extras = set(staged) - allowed
    if extras:
        print("INFO extra staging names (left in place)", sorted(extras))
    if (REPO / "outputs" / "raw" / "2026-08-30" / FACTORY / "batch-r29.jsonl").exists():
        raise SystemExit("outputs/raw already has batch-r29; abort")

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
