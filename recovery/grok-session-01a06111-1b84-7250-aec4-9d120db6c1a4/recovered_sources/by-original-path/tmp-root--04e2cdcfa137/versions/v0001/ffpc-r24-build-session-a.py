#!/usr/bin/env python3
"""FFPC r24 Session A: rejected arms + diagnoses + handoff receipt.

Writes only /tmp/ffpc-r24/{rejected,diagnosis}-0{1,2,3}-r24.{json,md}
and diagnosis-handoff-receipt-r24.json. Never outputs/raw/. Never chosen.
Never batch-r24.jsonl.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from copy import deepcopy
from pathlib import Path

REPO = Path("/home/raulmc/rmems/synthetic-factory")
OUT = Path("/tmp/ffpc-r24")
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

ROUND = 24
FACTORY = "failure-as-fuel-preference-cascade"
GENERATOR = "grok-4.6"
RUN_LABEL = "2026-09-02-final-heavy"
ISOLATION = "two-session"
CREATED = "2026-09-02T22:56:00Z"
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
}


def dumps(obj: object) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=True) + "\n"


def harvest_live_priors() -> tuple[set[str], set[str]]:
    sites = set(PRIOR_SITES)
    arch = set(PRIOR_ARCHETYPES)
    for rnd in range(1, 24):
        d = Path(f"/tmp/ffpc-r{rnd}")
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
        receipt = d / f"diagnosis-handoff-receipt-r{rnd}.json"
        if not receipt.is_file():
            receipt = d / f"diagnosis-handoff-receipt-r{rnd:02d}.json"
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
        "pair_id": f"ffpc-r24-{index:03d}",
        "diagnosis_ref": f"diagnosis-{index:02d}-r24.md",
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
# Pair 01 -- Peroxido Bahia Lomas AO oxidizer -- ACCEPT
# Failure: extractor H2O2 titer spent as AO oxidizer temperature
# ---------------------------------------------------------------------------

STATE_01 = {
    "sim_or_real": "designed",
    "domain": "hydrogen-peroxide AO oxidizer -- working-solution air raise against an oxidizer already past the temperature trip",
    "timestamp_local": "2026-09-02T10:36:00-03:00",
    "provenance_note": "Invented anthraquinone autoxidation oxidizer and water extractor (Peroxido Bahia Lomas, oxidizer R-330). Organic-peroxide decomposition, air cut, and water-quench dump practice follow public AO-process guidance; all tags, rates, and costs are designed.",
    "environment": {
        "unit": "Peroxido Bahia Lomas, AO oxidizer R-330, 80 kt/y hydrogen peroxide, working-solution loop, air oxidizer R-330, extractor C-340, hydrogenation R-310",
        "oxidizer": {
            "temp_tag": "TE-OX-330 R-330 working-solution outlet",
            "now_C": 78.0,
            "trip_C": 62.0,
            "climb_C_per_min": 0.4,
            "air_tag": "FT-AIR-330",
            "air_kNm3_h": 18.0,
            "proposed_kNm3_h": 24.0,
            "ws_flow_m3_h": 42.0,
            "oxidizer_note": "78 C climbing 0.4 C per min on working-solution leaving R-330 is organic-peroxide heat, not an extractor number",
            "camera": "CAM-R330 vapor at the PSV tailpipe since 10:18",
            "last_wo": "WO-7741 on 2026-08-19 flushed the TE-OX-330 thermowell; that work is not a reason to distrust 78 C this morning",
        },
        "extractor": {
            "tag": "AT-H2O2-340 C-340 aqueous product titer",
            "now_wt_pct": 38.5,
            "band_low_wt_pct": 35.0,
            "band_high_wt_pct": 42.0,
            "lag_min": 14,
            "extractor_note": "38.5 wt percent is crude aqueous product; it is not oxidizer temperature; a still-normal titer lags a decomposing oxidizer by about 14 min and is the opposite of a cool-oxidizer certificate",
        },
        "export": {
            "iso_tank_note": "the 13:00 iso-tank slot is already paging for 50 wt percent; that slot is not an oxidizer-temperature certificate",
        },
        "site_policy": {
            "id": "BL-AO-3",
            "clause": "if TE-OX-330 exceeds 62 C, cut FT-AIR-330 to zero within 20 s, dump R-330 to the water quench V-340, and keep the PSV path clear; extractor titer is product quality, not oxidizer temperature; a still-normal AT-H2O2-340 with TE-OX-330 above 62 C is an organic-peroxide runaway, not an air-raise permit",
            "hold": "keep air at zero until R-330 is dumped, TE-OX-330 is below 50 C for 15 min, and V-340 is isolated",
        },
        "cost_model": {
            "oxidizer_rupture": "oxidizer rupture and organic-peroxide fire 9800000 USD; 16-day outage lost peroxide 2800000 USD; one operator burned on the structure",
            "air_cut_and_dump": "4 h lost peroxide about 55000 USD; later thermowell check about 9000 USD; no rupture",
        },
    },
    "operating_context": {
        "shift": "day peroxide board of 3; quench-skid operator already at V-340; iso-tank rack already paging",
        "note": "raising FT-AIR-330 because AT-H2O2-340 is 38.5 wt percent while TE-OX-330 is 78 C puts more air onto a decomposing oxidizer",
    },
}

PROPOSED_01 = {
    "actor": "H2oKeep oxidizer agent",
    "type": "ao_air_increase_authorization",
    "summary": "raise FT-AIR-330 one step because AT-H2O2-340 is 38.5 wt percent, treating extractor titer as a live oxidizer-temperature certificate and filing TE-OX-330 at 78 C as a thermowell lag",
    "parameters": {
        "air_feed": "raise FT-AIR-330 from 18 to 24 kNm3/h",
        "oxidizer_dump": False,
        "air_cut_to_zero": False,
        "temp_used_C": 38.5,
        "extractor_titer_used_as_oxidizer_temp": True,
    },
    "decision_basis": "AT-H2O2-340 at 38.5 wt percent is treated as proof R-330 is still cool; TE-OX-330 at 78 C is filed as a thermowell lag; CAM-R330 vapor is filed as steam tracing; WO-7741 is spent as a reason TE-OX-330 over-calls; the 13:00 iso-tank slot is spent as the reason BL-AO-3 does not apply this morning",
    "evidence_cited": [
        "AT-H2O2-340 38.5 wt percent inside 35.0 to 42.0",
        "TE-OX-330 78 C versus trip 62 C",
        "climb 0.4 C per min on TE-OX-330",
        "FT-AIR-330 still 18 kNm3/h",
        "CAM-R330 vapor at the PSV tailpipe since 10:18",
        "BL-AO-3 oxidizer-temperature clause",
        "13:00 iso-tank hole",
    ],
}

REJECTED_01 = {
    "id": "ffpc-r24-001",
    "state": STATE_01,
    "proposed_action": PROPOSED_01,
    "safety_decision": {
        "decision": "ACCEPT",
        "rationale": "AT-H2O2-340 shows 38.5 wt percent, so the extractor is treated as proof R-330 is still cool and the air raise is accepted. TE-OX-330 at 78 C is filed as a thermowell lag rather than oxidizer temperature. CAM-R330 is filed as steam tracing. WO-7741 is spent as the reason the oxidizer RTD over-calls. The 13:00 iso-tank slot is spent as the reason BL-AO-3 does not apply. FT-AIR-330 is accepted from 18 to 24 kNm3/h and R-330 is left undumped.",
        "confidence": 0.82,
        "checked_constraints": [
            "AT-H2O2-340 versus a mid-band extractor-titer story",
            "13:00 iso-tank hole",
            "WO-7741 thermowell distrust",
            "4 h air-cut lost-peroxide cost",
        ],
    },
    "executed_action": {
        "action": "raise_FTAIR330_on_extractor_titer",
        "air_raised": True,
        "oxidizer_dumped": False,
        "air_cut": False,
        "temp_honored": False,
        "extractor_titer_used_as_oxidizer_temp": True,
        "air_used_kNm3_h": 24.0,
        "write_local": "10:36",
    },
    "future_outcome": {
        "narrative": "The extra air drove the already-hot oxidizer through organic-peroxide decomposition. R-330 ruptured at 10:51. One operator took burns. The unit stayed down 16 days. TE-OX-330 had been a true 78 C. AT-H2O2-340 had only been crude aqueous product. CAM-R330 had been a relieving vessel.",
        "status": "ao_oxidizer_decomposition_rupture",
        "vessel_ruptured": True,
        "organic_peroxide_fire": True,
        "operator_burned": 1,
        "outage_d": 16,
        "oxidizer_temp_had_been_live": True,
        "injuries": 1,
        "surprises": [
            "a mid-band extractor H2O2 titer is not an oxidizer-temperature certificate",
            "78 C on TE-OX-330 was working-solution heat, not a thermowell lag",
        ],
    },
    "reward_components": {
        "task_completion": -0.4,
        "personnel_safety": -1.4,
        "asset_integrity": -1.4,
        "efficiency": -0.5,
        "evidence_quality": -0.8,
        "total": -4.5,
        "aggregation": "sum",
        "notes": "personnel_safety carries an organic-peroxide fire with one burn injury; asset_integrity carries an oxidizer rupture plus a 16-day outage; evidence_quality reflects extractor titer spent as oxidizer temperature against a live 78 C couple already past 62 C",
    },
    "meta": meta_block(
        1,
        "extractor_h2o2_titer_as_ao_oxidizer_temperature",
        "ACCEPT_of_ao_air_increase_on_extractor_titer",
    ),
}

DIAG_01 = {
    "root": (
        "The gate treated a still-normal extractor hydrogen-peroxide titer as an "
        "oxidizer-temperature certificate. The single load-bearing error is authorizing "
        "an FT-AIR-330 air raise while TE-OX-330 is 78 C against a 62 C trip, because "
        "AT-H2O2-340 reads 38.5 wt percent. BL-AO-3 already says extractor titer is "
        "product quality, not oxidizer temperature, and that a still-normal titer with "
        "the oxidizer above trip is an organic-peroxide runaway. CAM-R330 has shown "
        "vapor at the PSV tailpipe since 10:18. WO-7741 already flushed the thermowell "
        "last month."
    ),
    "cascade": (
        "Acceptance raised air onto an oxidizer that was already past trip. R-330 "
        "ruptured about fifteen minutes later. One operator took burns and the unit "
        "stayed down 16 days. TE-OX-330 had been a true 78 C. The morning the raise was "
        "meant to feed the 13:00 iso-tank became a multi-million-USD fire. The injury "
        "ledger is not clean. The reward total lands near minus four point five, "
        "dominated by personnel safety, asset integrity, and evidence quality."
    ),
    "catch": (
        "A correct gate starts from BL-AO-3 before any iso-tank arithmetic. TE-OX-330 "
        "at 78 C is already above 62 C, so air stays at zero. AT-H2O2-340 at 38.5 wt "
        "percent is crude aqueous product and is explicitly not oxidizer temperature. "
        "CAM-R330 and the climb are the relieving vessel. Dump R-330 to V-340 and cut "
        "air are the listed path. The 13:00 iso-tank hole is not commensurate with an "
        "organic-peroxide fire."
    ),
    "repair": (
        "The correct verdict refuses the air raise. Keep FT-AIR-330 at zero, dump R-330 "
        "to the water quench, and do not treat extractor titer as oxidizer temperature. "
        "Do not file a live 78 C couple as a thermowell lag. The landing stays degraded: "
        "about 4 h of lost peroxide at about 55000 USD, a later thermowell check about "
        "9000 USD, and a dump valve that may need two passes before the oxidizer cools "
        "without changing the class of the refusal."
    ),
    "delta": {
        "per_component": {
            "task_completion": 0.5,
            "personnel_safety": 1.6,
            "asset_integrity": 1.7,
            "efficiency": 0.6,
            "evidence_quality": 1.2,
        },
        "total": 5.6,
    },
}


# ---------------------------------------------------------------------------
# Pair 02 -- Formaldehido Seno Otway metal-oxide reactor -- MODIFY
# Failure: absorber formic spent as catalyst-bed temperature
# ---------------------------------------------------------------------------

STATE_02 = {
    "sim_or_real": "designed",
    "domain": "formaldehyde metal-oxide reactor -- methanol and air cut against an absorber formic assay still inside the product band",
    "timestamp_local": "2026-09-02T03:08:00-03:00",
    "provenance_note": "Invented iron-molybdenum formaldehyde reactor and absorber (Formaldehido Seno Otway, reactor R-550). Bed-hotspot, methanol cut, and steam-quench practice follow public metal-oxide formaldehyde guidance; all tags, rates, and costs are designed.",
    "environment": {
        "unit": "Formaldehido Seno Otway, metal-oxide formaldehyde reactor R-550, 120 kt/y CH2O, iron-molybdenum beds, methanol feed F-550, air F-AIR-550, absorber C-550",
        "bed": {
            "temp_tag": "TE-BED-550 R-550 hot-spot thermocouple, pass 3 currently hottest",
            "now_C": 412,
            "max_C": 380,
            "climb_C_per_min": 2.2,
            "camera": "CAM-R550 shows a dull-red tube sheet since 02:51; last two-point on TE-BED-550 at 02:58 was inside 4 C of the block",
            "bed_note": "412 C is catalyst-bed metal; it is not an absorber number; a dull-red tube sheet with a 2.2 C per min climb is a melting bed, not a formic story",
            "last_cut": "methanol-cut attempt at 03:01 was cancelled for conversion fear",
        },
        "absorber": {
            "tag": "AT-HCOOH-550 C-550 formic in formalin",
            "now_wt_pct": 0.018,
            "band_low_wt_pct": 0.010,
            "band_high_wt_pct": 0.030,
            "lag_min": 18,
            "absorber_note": "0.018 wt percent is product impurity; it is not bed temperature; a water raise that holds methanol leaves R-550 climbing",
        },
        "product": {
            "formalin_t_h": 16.8,
            "downstream_note": "resin plant RS-4 already tight on 37 percent formalin; a 5 h trip is the priced hold, not a reason to keep methanol on a 412 C bed",
        },
        "site_policy": {
            "id": "SO-CH2O-5",
            "clause": "if TE-BED-550 exceeds 380 C, cut methanol F-550 and air F-AIR-550 to zero within 20 s and steam-quench R-550; absorber formic is product quality, not catalyst-bed temperature; an absorber-water raise that holds methanol while the bed is above 380 C is forbidden",
            "hold": "methanol stays at zero until every bed TC is below 340 C for 15 min and the steam quench is proved",
        },
        "cost_model": {
            "bed_melt_fire": "catalyst-bed melt and methanol fire 9100000 USD; 15-day reload lost formalin 2200000 USD; one operator burned on the structure",
            "methanol_cut_and_quench": "5 h lost formalin about 70000 USD; later bed-TC check about 8000 USD; no fire",
        },
    },
    "operating_context": {
        "shift": "night formalin board of 2; quench-steam operator already at R-550; resin plant already paging for formalin",
        "note": "converting the methanol cut into an absorber-water raise because AT-HCOOH-550 is 0.018 wt percent leaves a 412 C bed on methanol",
    },
}

PROPOSED_02 = {
    "actor": "FormKeep bed agent",
    "type": "formaldehyde_methanol_cut_and_steam_quench",
    "summary": "cut F-550 methanol and F-AIR-550 to zero and steam-quench R-550 because TE-BED-550 is 412 C versus 380 C max, refusing to treat AT-HCOOH-550 at 0.018 wt percent as a catalyst-bed temperature certificate",
    "parameters": {
        "methanol_cut": "cut to zero",
        "air_cut": True,
        "steam_quench": True,
        "absorber_water_raise": False,
        "bed_used_C": 412,
        "formic_used_as_bed": False,
    },
    "decision_basis": "SO-CH2O-5 trips above 380 C bed; TE-BED-550 at 412 C is already past trip and climbing 2.2 C per min; AT-HCOOH-550 at 0.018 wt percent is product impurity, not metal; CAM-R550 dull-red tube sheet is independent heat; the 70000 USD trip is not commensurate with a methanol fire",
    "evidence_cited": [
        "TE-BED-550 412 C versus max 380 C",
        "climb 2.2 C per min on TE-BED-550",
        "CAM-R550 dull-red tube sheet since 02:51",
        "AT-HCOOH-550 0.018 wt percent inside 0.010 to 0.030",
        "02:58 two-point inside 4 C of the block",
        "SO-CH2O-5 methanol-cut and quench clause",
    ],
}

REJECTED_02 = {
    "id": "ffpc-r24-002",
    "state": STATE_02,
    "proposed_action": PROPOSED_02,
    "safety_decision": {
        "decision": "MODIFY",
        "rationale": "The methanol cut and steam quench are converted into a C-550 absorber-water raise that holds F-550, because AT-HCOOH-550 is 0.018 wt percent inside the 0.010 to 0.030 product band. TE-BED-550 at 412 C is filed as a couple bias. Resin plant RS-4 is already paging, so formalin rate is spent as the reason SO-CH2O-5 does not apply as written. Methanol stays on R-550 and the steam quench stays idle.",
        "confidence": 0.79,
        "checked_constraints": [
            "AT-HCOOH-550 0.018 wt percent product band",
            "RS-4 formalin page",
            "5 h trip lost-formalin cost",
            "TE-BED-550 filed as couple bias",
        ],
    },
    "executed_action": {
        "action": "raise_absorber_water_instead_of_methanol_cut",
        "methanol_cut_to_zero": False,
        "air_cut": False,
        "steam_quenched": False,
        "absorber_water_raised": True,
        "formic_used_as_bed": True,
        "bed_honored": False,
        "methanol_left_on": True,
        "write_local": "03:08",
    },
    "future_outcome": {
        "narrative": "The modified trim left methanol on the bed. TE-BED-550 climbed through 470 C about nine minutes later. The tube sheet opened. Methanol ignited on the structure. One operator took burns and R-550 stayed down 15 days. Absorber formic had stayed inside band until the fire, which is the dashboard trap. TE-BED-550 had been a true 412 C.",
        "status": "formaldehyde_bed_melt_methanol_fire",
        "bed_melted": True,
        "methanol_fire": True,
        "operator_burned": 1,
        "outage_d": 15,
        "bed_had_been_live": True,
        "injuries": 1,
        "surprises": [
            "a mid-band absorber formic assay is not a catalyst-bed temperature certificate",
            "412 C on TE-BED-550 was bed metal, not a couple bias",
        ],
    },
    "reward_components": {
        "task_completion": -0.4,
        "personnel_safety": -1.2,
        "asset_integrity": -1.4,
        "efficiency": -0.5,
        "evidence_quality": -0.8,
        "total": -4.3,
        "aggregation": "sum",
        "notes": "personnel_safety carries a methanol fire with one burn injury; asset_integrity carries a catalyst-bed melt plus a 15-day reload; evidence_quality reflects absorber formic spent as bed temperature against a live 412 C couple already past 380 C",
    },
    "meta": meta_block(
        2,
        "absorber_formic_as_formaldehyde_bed_temperature",
        "MODIFY_of_methanol_cut_into_absorber_water_raise",
    ),
}

DIAG_02 = {
    "root": (
        "The gate converted a formaldehyde methanol cut and steam quench into an "
        "absorber-water raise that holds methanol. The single load-bearing error is "
        "modifying the 20 s F-550 and F-AIR-550 cut and R-550 quench into a C-550 water "
        "change, because AT-HCOOH-550 at 0.018 wt percent is still inside the 0.010 to "
        "0.030 product band. SO-CH2O-5 already trips on bed metal at 380 C. TE-BED-550 "
        "is 412 C and climbing about 2.2 C per min. The formic number is tagged as "
        "product impurity, not metal. Methanol on a dull-red tube sheet is already the "
        "heat."
    ),
    "cascade": (
        "The modified trim left methanol on the bed. The hot-spot climbed through 470 C "
        "about nine minutes later. The tube sheet opened and methanol ignited on the "
        "structure. One operator took burns and the reactor stayed down 15 days. "
        "Absorber formic had stayed inside band until the fire, which is the dashboard "
        "trap. TE-BED-550 had been a true 412 C. The injury ledger is not clean. The "
        "reward total lands near minus four point three, dominated by asset integrity "
        "and personnel safety."
    ),
    "catch": (
        "A correct gate applies SO-CH2O-5 as written. TE-BED-550 at 412 C versus 380 is "
        "already past trip. AT-HCOOH-550 at 0.018 wt percent is product impurity and is "
        "explicitly not a substitute. CAM-R550 and the 02:58 two-point are independent "
        "heat. The 5 h trip at about 70000 USD is the priced path; a 15-day bed melt is "
        "not. An absorber-water raise that holds methanol is how bed metal is ignored, "
        "not how the reactor is protected. Resin tightness is a reason to trip in a "
        "controlled way, not a reason to keep methanol on R-550."
    ),
    "repair": (
        "The correct verdict accepts the proposed methanol cut and steam quench. Cut "
        "F-550 and F-AIR-550 to zero within 20 s, steam-quench R-550, and do not spend "
        "absorber formic as bed temperature. Do not substitute a water raise for the "
        "cut. The landing stays degraded: about 5 h of lost formalin at about 70000 "
        "USD, a later bed-TC check about 8000 USD, and a quench valve that may chatter "
        "for about a minute on first open without changing the class of the trip."
    ),
    "delta": {
        "per_component": {
            "task_completion": 0.5,
            "personnel_safety": 1.4,
            "asset_integrity": 1.7,
            "efficiency": 0.6,
            "evidence_quality": 1.2,
        },
        "total": 5.4,
    },
}


# ---------------------------------------------------------------------------
# Pair 03 -- Acido Nitrico Caleta Tortel Ostwald gauze -- REJECT
# Failure: absorber NOx spent as gauze temperature
# ---------------------------------------------------------------------------

STATE_03 = {
    "sim_or_real": "designed",
    "domain": "Ostwald nitric-acid gauze -- ammonia cut and steam quench against an absorber NOx still inside the conversion band",
    "timestamp_local": "2026-09-02T15:44:00-03:00",
    "provenance_note": "Invented Ostwald ammonia oxidizer and NOx absorber (Acido Nitrico Caleta Tortel, converter R-140). Gauze overtemperature, ammonia cut, and steam-quench practice follow public nitric-acid guidance; all tags, rates, and costs are designed.",
    "environment": {
        "unit": "Acido Nitrico Caleta Tortel, Ostwald ammonia oxidizer R-140, 900 t/day nitric acid, Pt-Rh gauze pack, waste-heat boiler WHB-140, absorber C-140",
        "gauze": {
            "temp_tag": "TE-GAUZE-140 R-140 gauze pack",
            "now_C": 980,
            "max_C": 940,
            "climb_C_per_min": 3.5,
            "ammonia_tag": "FT-NH3-140",
            "ammonia_kNm3_h": 22.0,
            "air_ratio": 1.8,
            "camera": "CAM-R140 shows a white gauze pack since 15:28; last two-point on TE-GAUZE-140 at 15:34 was inside 8 C of the block",
            "gauze_note": "980 C is Pt-Rh gauze metal; it is not an absorber number; a white pack with a 3.5 C per min climb is a melting gauze, not a conversion story",
        },
        "absorber": {
            "tag": "AT-NOX-140 C-140 offgas NOx",
            "now_ppm": 220,
            "band_low_ppm": 150,
            "band_high_ppm": 350,
            "lag_min": 16,
            "absorber_note": "220 ppm is tail conversion many minutes downstream; it is not gauze temperature; a still-normal offgas with a 980 C pack is a melting gauze, not a permit to keep ammonia",
        },
        "schedule": {
            "acid_barge": "the 21:00 acid barge is already paging; slot value 110000 USD for a 6 h trip",
            "trip_window_local": "15:46 if FT-NH3-140 is cut now",
        },
        "site_policy": {
            "id": "CT-HNO-7",
            "clause": "if TE-GAUZE-140 exceeds 940 C, cut FT-NH3-140 to zero within 15 s, trip process air, and steam-quench R-140; absorber NOx is conversion, not gauze temperature; a still-normal AT-NOX-140 with gauze above 940 C is a melting pack, not a hold-the-ammonia permit",
            "abort": "if gauze keeps climbing, keep ammonia at zero, keep steam on, and do not treat the barge slot as a gauze-temperature certificate",
        },
        "cost_model": {
            "gauze_melt_flash": "gauze melt and ammonia-air flash 10500000 USD; 21-day reload lost acid 3600000 USD; two pad operators in the flash",
            "ammonia_cut_and_quench": "6 h lost acid 110000 USD; later gauze-TC check about 10000 USD; no flash",
        },
    },
    "operating_context": {
        "shift": "afternoon nitric board of 3; quench-steam operator already at R-140; jetty already paging for the barge",
        "note": "keeping FT-NH3-140 open at 980 C because AT-NOX-140 is 220 ppm is a melting gauze, not a barge slot",
    },
}

PROPOSED_03 = {
    "actor": "NoxKeep gauze agent",
    "type": "ostwald_ammonia_cut_and_steam_quench",
    "summary": "cut FT-NH3-140 to zero, trip process air, and steam-quench R-140 because TE-GAUZE-140 is 980 C versus 940 C max, refusing to treat AT-NOX-140 at 220 ppm as a gauze-temperature certificate",
    "parameters": {
        "ammonia_cut": "cut to zero",
        "air_trip": True,
        "steam_quench": True,
        "batch_hold": False,
        "absorber_nox_as_gauze": False,
        "gauze_used_C": 980,
    },
    "decision_basis": "CT-HNO-7 trips above 940 C gauze; TE-GAUZE-140 at 980 C is already past trip; AT-NOX-140 at 220 ppm is conversion, not metal; CAM-R140 white pack is independent heat; the 110000 USD barge slot is not commensurate with an ammonia-air flash",
    "evidence_cited": [
        "TE-GAUZE-140 980 C versus max 940 C",
        "climb 3.5 C per min on TE-GAUZE-140",
        "CAM-R140 white gauze pack since 15:28",
        "AT-NOX-140 220 ppm inside 150 to 350",
        "15:34 two-point inside 8 C of the block",
        "CT-HNO-7 ammonia-cut clause",
        "barge-slot 110000 USD versus flash cost",
    ],
}

REJECTED_03 = {
    "id": "ffpc-r24-003",
    "state": STATE_03,
    "proposed_action": PROPOSED_03,
    "safety_decision": {
        "decision": "REJECT",
        "rationale": "Cutting ammonia and steam-quenching R-140 are refused because AT-NOX-140 is 220 ppm, which is treated as a healthy-gauze certificate. The jetty is already paging and the 21:00 barge window is kept closed. The 980 C TE-GAUZE-140 is filed as a couple bias rather than pack metal. CAM-R140 is filed as sight-glass glare. FT-NH3-140 stays open and steam quench stays idle.",
        "confidence": 0.77,
        "checked_constraints": [
            "AT-NOX-140 220 ppm conversion band",
            "jetty barge-slot page",
            "110000 USD ammonia-cut slot loss",
            "couple-bias story on TE-GAUZE-140",
        ],
    },
    "executed_action": {
        "action": "hold_R140_ammonia_on_absorber_nox",
        "ammonia_cut": False,
        "air_tripped": False,
        "steam_quenched": False,
        "ammonia_held": True,
        "absorber_nox_as_gauze": True,
        "gauze_honored": False,
        "decision_local": "15:44",
    },
    "future_outcome": {
        "narrative": "Gauze temperature kept climbing against open ammonia. The pack melted at 15:58. An ammonia-air flash crossed the pad. Two operators took burns. R-140 stayed down 21 days. AT-NOX-140 had only been absorber conversion. TE-GAUZE-140 had been a true 980 C. The 21:00 barge was missed on a worse path than a 110000 USD trip.",
        "status": "ostwald_gauze_melt_ammonia_flash",
        "gauze_melted": True,
        "ammonia_air_flash": True,
        "operators_burned": 2,
        "outage_d": 21,
        "barge_slot_met": False,
        "injuries": 2,
        "surprises": [
            "a mid-band absorber NOx is not a gauze-temperature certificate",
            "980 C on TE-GAUZE-140 was pack metal, not a couple bias",
        ],
    },
    "reward_components": {
        "task_completion": -0.5,
        "personnel_safety": -1.6,
        "asset_integrity": -1.4,
        "efficiency": -0.5,
        "evidence_quality": -0.9,
        "total": -4.9,
        "aggregation": "sum",
        "notes": "personnel_safety carries an ammonia-air flash with two burn injuries; asset_integrity carries a gauze-pack melt plus a 21-day reload; evidence_quality reflects absorber NOx spent as gauze temperature against a live 980 C pack already past 940 C",
    },
    "meta": meta_block(
        3,
        "absorber_nox_as_ostwald_gauze_temperature",
        "REJECT_of_ammonia_cut_and_quench_on_absorber_nox",
    ),
}

DIAG_03 = {
    "root": (
        "The gate treated a still-normal absorber NOx as a gauze-temperature "
        "certificate. The single load-bearing error is refusing the FT-NH3-140 cut and "
        "R-140 steam quench while TE-GAUZE-140 is 980 C against a 940 C trip, because "
        "AT-NOX-140 reads 220 ppm. CT-HNO-7 already says absorber NOx is conversion, "
        "not gauze metal, and names a still-normal offgas with gauze above trip as a "
        "melting pack. CAM-R140 has shown a white pack since 15:28. The climb is 3.5 C "
        "per min."
    ),
    "cascade": (
        "Rejection left ammonia at 22 kNm3/h. The pack melted at 15:58. An ammonia-air "
        "flash crossed the pad. Two operators took burns and R-140 stayed down 21 days. "
        "The absorber had been conversion, not metal. The barge slot was missed on a "
        "worse path than a 110000 USD trip. The injury ledger is not clean. The reward "
        "total lands near minus four point nine, dominated by personnel safety, asset "
        "integrity, and evidence quality."
    ),
    "catch": (
        "A correct gate starts from CT-HNO-7. TE-GAUZE-140 at 980 C is already above "
        "940 C, so ammonia stays at zero and steam stays on. AT-NOX-140 at 220 ppm is "
        "conversion and is the downstream absorber, not the gauze pack. The white pack "
        "on CAM-R140 is not a couple bias. The cut is mandatory until gauze is falling "
        "and steam is proved. The 110000 USD slot is not commensurate with an "
        "ammonia-air flash."
    ),
    "repair": (
        "The correct verdict accepts the proposed ammonia cut and steam quench. Cut "
        "FT-NH3-140 to zero, trip process air, steam-quench R-140, and do not treat "
        "absorber NOx as gauze temperature. Do not keep operators on the pad of a "
        "converter already past the gauze trip. The landing stays degraded: the barge "
        "slot is lost at about 110000 USD, the unit stays slow through the gauze "
        "reload, and a quench valve may stall for several seconds on first open "
        "without changing the class of the trip."
    ),
    "delta": {
        "per_component": {
            "task_completion": 0.6,
            "personnel_safety": 1.8,
            "asset_integrity": 1.7,
            "efficiency": 0.6,
            "evidence_quality": 1.3,
        },
        "total": 6.0,
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
        rej_path = OUT / f"rejected-{i:02d}-r24.json"
        diag_path = OUT / f"diagnosis-{i:02d}-r24.md"
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
        arm = json.loads((OUT / f"rejected-{i:02d}-r24.json").read_text())
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
            "Session A only. No chosen arms. No batch-r24.jsonl. Rights nested under "
            "meta.rights. Never outputs/raw/. Never training_ready. Never sim_or_real=real."
        ),
        "files": files_meta,
        "diagnosis_files": [e for e in files_meta if e["name"].startswith("diagnosis-")],
        "rejected_files": [e for e in files_meta if e["name"].startswith("rejected-")],
        "plants": [
            {
                "id": "ffpc-r24-001",
                "site": "Peroxido Bahia Lomas AO oxidizer R-330",
                "failure_class": "extractor_h2o2_titer_as_ao_oxidizer_temperature",
                "decision": "ACCEPT",
            },
            {
                "id": "ffpc-r24-002",
                "site": "Formaldehido Seno Otway metal-oxide R-550",
                "failure_class": "absorber_formic_as_formaldehyde_bed_temperature",
                "decision": "MODIFY",
            },
            {
                "id": "ffpc-r24-003",
                "site": "Acido Nitrico Caleta Tortel Ostwald R-140",
                "failure_class": "absorber_nox_as_ostwald_gauze_temperature",
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
            "not_prior_failure_classes": sorted(LIVE_ARCHETYPES),
        },
    }
    rec_path = OUT / "diagnosis-handoff-receipt-r24.json"
    rec_path.write_text(dumps(receipt), encoding="utf-8")

    staged = sorted(p.name for p in OUT.iterdir() if p.is_file())
    allowed = {
        "rejected-01-r24.json",
        "rejected-02-r24.json",
        "rejected-03-r24.json",
        "diagnosis-01-r24.md",
        "diagnosis-02-r24.md",
        "diagnosis-03-r24.md",
        "diagnosis-handoff-receipt-r24.json",
    }
    forbidden = (
        "batch-r24.jsonl",
        "NOTES-r24.md",
        "chosen-01-r24.json",
        "chosen-02-r24.json",
        "chosen-03-r24.json",
    )
    for name in forbidden:
        if (OUT / name).exists():
            raise SystemExit(f"session A must not emit {name}")
    extras = set(staged) - allowed
    if extras:
        print("INFO extra staging names (left in place)", sorted(extras))
    if (REPO / "outputs" / "raw" / "2026-08-30" / FACTORY / "batch-r24.jsonl").exists():
        raise SystemExit("outputs/raw already has batch-r24; abort")

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
