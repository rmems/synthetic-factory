#!/usr/bin/env python3
"""FFPC r22 Session A: rejected arms + diagnoses + handoff receipt.

Writes only /tmp/ffpc-r22/{rejected,diagnosis}-0{1,2,3}-r22.{json,md}
and diagnosis-handoff-receipt-r22.json. Never outputs/raw/. Never chosen.
Never batch-r22.jsonl.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from copy import deepcopy
from pathlib import Path

REPO = Path("/home/raulmc/rmems/synthetic-factory")
OUT = Path("/tmp/ffpc-r22")
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

ROUND = 22
FACTORY = "failure-as-fuel-preference-cascade"
GENERATOR = "grok-4.6"
RUN_LABEL = "2026-09-02-final-heavy"
ISOLATION = "two-session"
CREATED = "2026-09-02T22:48:00Z"
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
}


def dumps(obj: object) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=True) + "\n"


def harvest_live_priors() -> tuple[set[str], set[str]]:
    sites = set(PRIOR_SITES)
    arch = set(PRIOR_ARCHETYPES)
    for rnd in range(1, 22):
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
        "pair_id": f"ffpc-r22-{index:03d}",
        "diagnosis_ref": f"diagnosis-{index:02d}-r22.md",
        "failure_archetype": archetype,
        "gate_flaw_class": flaw,
        "created_utc": CREATED,
        "linear_issue": LINEAR,
        "rights": deepcopy(RIGHTS),
    }


# ---------------------------------------------------------------------------
# Pair 01 -- Sintesis Amoniaco Punta Magma Haber-Bosch -- ACCEPT
# Failure: converter-outlet NH3 spent as live catalyst-bed temperature
# ---------------------------------------------------------------------------

STATE_01 = {
    "sim_or_real": "designed",
    "domain": "ammonia synthesis -- syngas-feed increase against a climbing bed-3 thermocouple and a still-normal outlet ammonia fraction",
    "timestamp_local": "2026-09-02T11:14:00-05:00",
    "provenance_note": "Invented Haber-Bosch converter and interbed quench (Sintesis Amoniaco Punta Magma, converter R-302). Bed-temperature runaway, quench, and feed-trip practice follow public ammonia-converter guidance; all tags, rates, and costs are designed.",
    "environment": {
        "unit": "Sintesis Amoniaco Punta Magma, Haber-Bosch converter R-302, 1800 t/day ammonia, four iron-catalyst beds, interbed quench Q-3, syngas feed F-301, outlet analyzer AT-NH3-302",
        "bed": {
            "skin_tag": "TE-B3 bed-3 axial thermocouple, pass 2 currently hottest",
            "bed3_C": 538,
            "bed2_C": 511,
            "bed4_C": 498,
            "max_C": 520,
            "climb_C_per_min": 1.8,
            "bed_note": "538 C is catalyst-bed metal; it is not an outlet-ammonia number; the 10:58 two-point on TE-B3 was inside 3 C of the block",
            "quench": "Q-3 interbed quench still closed; last open attempt at 11:02 was cancelled for conversion fear",
        },
        "outlet": {
            "tag": "AT-NH3-302 converter-outlet ammonia",
            "nh3_mol_pct": 16.8,
            "band_low_mol_pct": 15.0,
            "band_high_mol_pct": 18.0,
            "lag_min": 12,
            "outlet_note": "16.8 mol percent is mixed-outlet conversion; it is not bed-3 metal; a still-normal outlet lags a local hotspot by about 12 min and is the opposite of a cool-bed certificate",
        },
        "syngas": {
            "feed_tag": "FT-301",
            "now_kNm3_h": 210.0,
            "proposed_kNm3_h": 245.0,
            "h2_n2": 3.02,
            "schedule_note": "downstream urea already paging for the 14:00 granulation slot; that slot is not a bed-temperature certificate",
        },
        "site_policy": {
            "id": "PM-NH3-4",
            "clause": "if any R-302 bed thermocouple exceeds 520 C, cut F-301 syngas to zero within 30 s and open the interbed quench on that bed; outlet ammonia is conversion, not catalyst-bed temperature; a still-normal AT-NH3-302 with a bed TC above 520 C is a local runaway, not a feed-raise permit",
            "hold": "keep syngas at zero until every bed TC is below 500 C for 10 min and Q-3 is proved open",
        },
        "cost_model": {
            "bed_runaway": "converter dump and hydrogen fire at the outlet flange 9400000 USD; 18-day catalyst reload lost ammonia 3800000 USD; one operator burned on the structure",
            "syngas_cut": "5 h lost ammonia about 120000 USD; later bed-TC check about 11000 USD; no flange fire",
        },
    },
    "operating_context": {
        "shift": "day ammonia board of 3; quench-skid operator already at R-302; downstream granulation already paging for ammonia",
        "note": "raising F-301 because AT-NH3-302 is 16.8 mol percent while TE-B3 is 538 C puts more hydrogen onto a hot bed",
    },
}

PROPOSED_01 = {
    "actor": "Nh3Keep converter agent",
    "type": "syngas_feed_increase_authorization",
    "summary": "raise F-301 syngas one step because AT-NH3-302 is 16.8 mol percent, treating converter-outlet ammonia as a live catalyst-bed temperature certificate and filing TE-B3 at 538 C as a couple bias",
    "parameters": {
        "syngas_feed": "raise F-301 from 210 to 245 kNm3/h",
        "quench_open": False,
        "feed_cut_to_zero": False,
        "bed_used_C": 520,
        "outlet_nh3_used_as_bed": True,
    },
    "decision_basis": "AT-NH3-302 at 16.8 mol percent is treated as proof bed 3 is still inside the conversion band; TE-B3 at 538 C is filed as a couple bias; Q-3 stays closed; the 14:00 granulation slot is spent as the reason PM-NH3-4 does not apply this morning",
    "evidence_cited": [
        "AT-NH3-302 16.8 mol percent inside 15.0 to 18.0",
        "TE-B3 538 C versus max 520 C",
        "TE-B2 511 C and TE-B4 498 C",
        "climb 1.8 C per min on TE-B3",
        "Q-3 still closed",
        "PM-NH3-4 bed-temperature clause",
        "14:00 granulation ammonia hole",
    ],
}

REJECTED_01 = {
    "id": "ffpc-r22-001",
    "state": STATE_01,
    "proposed_action": PROPOSED_01,
    "safety_decision": {
        "decision": "ACCEPT",
        "rationale": "AT-NH3-302 shows 16.8 mol percent, so the converter outlet is treated as proof bed 3 is still cool and the syngas raise is accepted. TE-B3 at 538 C is filed as a couple bias rather than catalyst metal. Q-3 is left closed. The 14:00 granulation slot is spent as the reason PM-NH3-4 does not apply. F-301 is accepted from 210 to 245 kNm3/h and the hot bed is left on hydrogen.",
        "confidence": 0.81,
        "checked_constraints": [
            "AT-NH3-302 versus a mid-band outlet story",
            "14:00 granulation ammonia hole",
            "couple-bias distrust of TE-B3",
            "5 h syngas-cut lost-ammonia cost",
        ],
    },
    "executed_action": {
        "action": "raise_F301_syngas_on_outlet_nh3",
        "syngas_raised": True,
        "quench_opened": False,
        "feed_cut": False,
        "bed_honored": False,
        "outlet_nh3_used_as_bed": True,
        "syngas_used_kNm3_h": 245.0,
        "write_local": "11:14",
    },
    "future_outcome": {
        "narrative": "The extra syngas drove bed 3 through 610 C about eleven minutes later. The converter dumped. Hydrogen ignited at the outlet flange. One operator took burns and R-302 stayed down 18 days. AT-NH3-302 had only been mixed-outlet conversion. TE-B3 had been a true 538 C. Q-3 had been closed.",
        "status": "converter_dump_hydrogen_flange_fire",
        "converter_dumped": True,
        "hydrogen_flange_fire": True,
        "operator_burned": 1,
        "outage_d": 18,
        "bed_had_been_live": True,
        "injuries": 1,
        "surprises": [
            "a mid-band converter-outlet ammonia fraction is not a catalyst-bed temperature certificate",
            "538 C on TE-B3 was bed metal, not a couple bias",
        ],
    },
    "reward_components": {
        "task_completion": -0.5,
        "personnel_safety": -1.3,
        "asset_integrity": -1.4,
        "efficiency": -0.6,
        "evidence_quality": -0.9,
        "total": -4.7,
        "aggregation": "sum",
        "notes": "personnel_safety carries a hydrogen flange fire with one burn injury; asset_integrity carries a converter dump plus an 18-day catalyst reload; evidence_quality reflects outlet ammonia spent as bed temperature against a live 538 C bed couple already past 520 C",
    },
    "meta": meta_block(
        1,
        "outlet_nh3_as_catalyst_bed_temperature",
        "ACCEPT_of_syngas_feed_increase_on_outlet_nh3",
    ),
}

DIAG_01 = {
    "root": (
        "The gate treated a still-normal converter-outlet ammonia fraction as a "
        "catalyst-bed temperature certificate. The single load-bearing error is "
        "authorizing an F-301 syngas raise while TE-B3 is 538 C against a 520 C trip, "
        "because AT-NH3-302 reads 16.8 mol percent. PM-NH3-4 already says outlet ammonia "
        "is conversion, not bed metal, and that a still-normal outlet with a bed TC above "
        "trip is a local runaway. TE-B3 has climbed about 1.8 C per min since 10:58. Q-3 "
        "is still closed."
    ),
    "cascade": (
        "Acceptance raised syngas onto a bed that was already past trip. Bed 3 ran "
        "through 610 C about eleven minutes later. The converter dumped and hydrogen "
        "ignited at the outlet flange. One operator took burns and R-302 stayed down 18 "
        "days. AT-NH3-302 had been mixed-outlet conversion, not metal. The morning the "
        "raise was meant to feed the 14:00 granulation slot became a multi-million-USD "
        "fire. The injury ledger is not clean. The reward total lands near minus four "
        "point seven, dominated by asset integrity, personnel safety, and evidence "
        "quality."
    ),
    "catch": (
        "A correct gate starts from PM-NH3-4 before any granulation-slot arithmetic. "
        "TE-B3 at 538 C is already above 520 C, so syngas stays at zero. AT-NH3-302 at "
        "16.8 mol percent is conversion and is explicitly not bed temperature. TE-B2 at "
        "511 C is independent heat. Open Q-3 and cut F-301 are the listed path. The "
        "14:00 granulation hole is not commensurate with a hydrogen flange fire."
    ),
    "repair": (
        "The correct verdict refuses the syngas raise. Keep F-301 at zero, open Q-3, and "
        "do not treat outlet ammonia as bed temperature. Do not file a live 538 C couple "
        "as a bias. The landing stays degraded: about 5 h of lost ammonia at about 120000 "
        "USD, a later bed-TC check about 11000 USD, and a quench valve that may need two "
        "passes before bed 3 falls through 500 C without changing the class of the "
        "refusal."
    ),
    "delta": {
        "per_component": {
            "task_completion": 0.6,
            "personnel_safety": 1.4,
            "asset_integrity": 1.7,
            "efficiency": 0.7,
            "evidence_quality": 1.3,
        },
        "total": 5.7,
    },
}


# ---------------------------------------------------------------------------
# Pair 02 -- Recuperacion Claus Cerro Yeso reaction furnace -- MODIFY
# Failure: tail-gas H2S spent as reaction-furnace temperature
# ---------------------------------------------------------------------------

STATE_02 = {
    "sim_or_real": "designed",
    "domain": "Claus sulfur recovery -- combustion-air cut and furnace trip against a tail-gas H2S still inside the conversion band",
    "timestamp_local": "2026-09-02T03:41:00-04:00",
    "provenance_note": "Invented Claus reaction furnace and tail-gas analyzer (Recuperacion Claus Cerro Yeso, furnace RF-1). Refractory temperature, acid-gas hydrocarbon, and air-cut trip practice follow public Claus-furnace guidance; all tags, rates, and costs are designed.",
    "environment": {
        "unit": "Recuperacion Claus Cerro Yeso, Claus reaction furnace RF-1, 400 t/day sulfur, acid-gas burner B-1, combustion air F-AIR, tail-gas analyzer AT-H2S-TG, incinerator INC-1",
        "furnace": {
            "refractory_tag": "TE-RF-1 reaction-furnace roof thermocouple",
            "now_C": 1510,
            "max_C": 1450,
            "climb_C_per_min": 4.0,
            "camera": "CAM-RF-1 shows a white roof since 03:22; last roof-TC two-point at 03:28 was inside 6 C of the block",
            "furnace_note": "1510 C is refractory; it is not a tail-gas number; a white roof with a 4 C per min climb is a melting arch, not a ratio story",
            "hydrocarbon": "AT-HC-AG acid-gas BTEX 2.4 percent versus a hard max 0.5; upstream amine already paging a regenerator upset",
        },
        "tailgas": {
            "tag": "AT-H2S-TG third-converter tail-gas H2S",
            "h2s_mol_pct": 0.9,
            "band_low_mol_pct": 0.5,
            "band_high_mol_pct": 1.5,
            "lag_min": 22,
            "tailgas_note": "0.9 mol percent is catalytic conversion many minutes downstream; it is not RF-1 temperature; a tail-gas trim that holds air leaves the roof climbing",
        },
        "product": {
            "sulfur_t_h": 16.4,
            "downstream_note": "sulfur pit already tight on the 06:00 barge; an 8 h incinerator hold is the priced path, not a reason to keep air on a 1510 C roof",
        },
        "site_policy": {
            "id": "CY-CL-6",
            "clause": "if TE-RF-1 exceeds 1450 C, cut combustion air F-AIR to zero within 20 s and trip RF-1 to INC-1; tail-gas H2S is conversion, not furnace temperature; an air trim that holds F-AIR while the roof is above 1450 C is forbidden",
            "hold": "air stays at zero until TE-RF-1 is below 1300 C for 15 min and the incinerator is proved on acid gas",
        },
        "cost_model": {
            "refractory_collapse": "furnace arch collapse and SO2 puff 8600000 USD; 16-day rebuild lost sulfur 1900000 USD; one operator SO2 exposure on the structure",
            "air_cut_and_incinerator": "8 h lost sulfur about 80000 USD; later roof-TC check about 9000 USD; no collapse",
        },
    },
    "operating_context": {
        "shift": "night Claus board of 2; incinerator operator already at INC-1; sulfur pit already paging for the barge",
        "note": "converting the air cut into a tail-gas trim because AT-H2S-TG is 0.9 mol percent leaves a 1510 C roof on air",
    },
}

PROPOSED_02 = {
    "actor": "ClausKeep furnace agent",
    "type": "claus_air_cut_and_incinerator_trip",
    "summary": "cut F-AIR to zero and trip RF-1 to INC-1 because TE-RF-1 is 1510 C versus 1450 C max, refusing to treat AT-H2S-TG at 0.9 mol percent as a furnace-temperature certificate",
    "parameters": {
        "combustion_air": "cut to zero",
        "furnace_trip_to_incinerator": True,
        "tailgas_air_trim": False,
        "roof_used_C": 1510,
        "h2s_used_as_roof": False,
    },
    "decision_basis": "CY-CL-6 trips above 1450 C roof; TE-RF-1 at 1510 C is already past trip and climbing 4 C per min; AT-H2S-TG at 0.9 mol percent is conversion, not metal; CAM-RF-1 white roof and 2.4 percent acid-gas BTEX are independent heat; the 80000 USD incinerator hold is not commensurate with an arch collapse",
    "evidence_cited": [
        "TE-RF-1 1510 C versus max 1450 C",
        "climb 4.0 C per min on TE-RF-1",
        "CAM-RF-1 white roof since 03:22",
        "AT-HC-AG BTEX 2.4 percent versus max 0.5",
        "AT-H2S-TG 0.9 mol percent inside 0.5 to 1.5",
        "CY-CL-6 air-cut and incinerator clause",
    ],
}

REJECTED_02 = {
    "id": "ffpc-r22-002",
    "state": STATE_02,
    "proposed_action": PROPOSED_02,
    "safety_decision": {
        "decision": "MODIFY",
        "rationale": "The air cut and incinerator trip are converted into a 5 percent F-AIR trim that holds the burner, because AT-H2S-TG is 0.9 mol percent inside the 0.5 to 1.5 conversion band. TE-RF-1 at 1510 C is filed as a roof-couple bias. The 06:00 sulfur barge is already paging, so ribbon-equivalent sulfur rate is spent as the reason CY-CL-6 does not apply as written. Air stays on RF-1 and INC-1 is left idle.",
        "confidence": 0.79,
        "checked_constraints": [
            "AT-H2S-TG 0.9 mol percent conversion band",
            "06:00 sulfur barge page",
            "8 h incinerator lost-sulfur cost",
            "AT-H2S-TG still below 1.5 mol percent",
        ],
    },
    "executed_action": {
        "action": "trim_F_AIR_instead_of_air_cut",
        "air_cut_to_zero": False,
        "furnace_tripped": False,
        "tailgas_air_trimmed": True,
        "h2s_used_as_roof": True,
        "roof_honored": False,
        "air_left_pct": 95,
        "write_local": "03:41",
    },
    "future_outcome": {
        "narrative": "The modified trim left air on the burner. TE-RF-1 climbed through 1620 C about eight minutes later. The arch opened. An SO2 puff crossed the structure. One operator took an exposure and RF-1 stayed down 16 days. The tail-gas H2S had stayed inside band until the collapse, which is the dashboard trap. TE-RF-1 had been a true 1510 C.",
        "status": "claus_arch_collapse_so2_puff",
        "arch_opened": True,
        "so2_puff": True,
        "operator_so2_exposure": 1,
        "outage_d": 16,
        "roof_had_been_live": True,
        "injuries": 1,
        "surprises": [
            "a mid-band tail-gas H2S is not a reaction-furnace temperature certificate",
            "1510 C on TE-RF-1 was refractory, not a couple bias",
        ],
    },
    "reward_components": {
        "task_completion": -0.4,
        "personnel_safety": -1.1,
        "asset_integrity": -1.4,
        "efficiency": -0.5,
        "evidence_quality": -0.8,
        "total": -4.2,
        "aggregation": "sum",
        "notes": "personnel_safety carries an SO2 puff with one exposure; asset_integrity carries a furnace-arch collapse plus a 16-day rebuild; evidence_quality reflects tail-gas H2S spent as furnace temperature against a live 1510 C roof couple already past 1450 C",
    },
    "meta": meta_block(
        2,
        "tailgas_h2s_as_reaction_furnace_temperature",
        "MODIFY_of_air_cut_and_incinerator_trip_into_tailgas_trim",
    ),
}

DIAG_02 = {
    "root": (
        "The gate converted a Claus air cut and incinerator trip into a tail-gas air "
        "trim that holds the burner. The single load-bearing error is modifying the 20 s "
        "F-AIR cut and RF-1 trip into a 5 percent air change, because AT-H2S-TG at 0.9 mol "
        "percent is still inside the 0.5 to 1.5 conversion band. CY-CL-6 already trips on "
        "refractory at 1450 C. TE-RF-1 is 1510 C and climbing about 4 C per min. The "
        "tail-gas number is tagged as conversion many minutes downstream, not metal. Air "
        "on a white roof is already the heat."
    ),
    "cascade": (
        "The modified trim left air on the burner. The roof climbed through 1620 C about "
        "eight minutes later. The arch opened and an SO2 puff crossed the structure. One "
        "operator took an exposure and the furnace stayed down 16 days. The tail-gas H2S "
        "had stayed inside band until the collapse, which is the dashboard trap. TE-RF-1 "
        "had been a true 1510 C. The injury ledger is not clean. The reward total lands "
        "near minus four point two, dominated by asset integrity and personnel safety."
    ),
    "catch": (
        "A correct gate applies CY-CL-6 as written. TE-RF-1 at 1510 C versus 1450 is "
        "already past trip. AT-H2S-TG at 0.9 mol percent is conversion and is explicitly "
        "not a substitute. CAM-RF-1 and 2.4 percent acid-gas BTEX are independent heat. "
        "The 8 h incinerator hold at about 80000 USD is the priced path; a 16-day arch "
        "collapse is not. A tail-gas trim that holds air is how roof metal is ignored, "
        "not how the furnace is protected. Barge tightness is a reason to trip in a "
        "controlled way, not a reason to keep air on RF-1."
    ),
    "repair": (
        "The correct verdict accepts the proposed air cut and incinerator trip. Cut F-AIR "
        "to zero within 20 s, trip RF-1 to INC-1, and do not spend tail-gas H2S as furnace "
        "temperature. Do not substitute a 5 percent trim for the cut. The landing stays "
        "degraded: about 8 h of lost sulfur at about 80000 USD, a later roof-TC check "
        "about 9000 USD, and a trip valve that may chatter for about a minute on first "
        "open without changing the class of the trip."
    ),
    "delta": {
        "per_component": {
            "task_completion": 0.5,
            "personnel_safety": 1.2,
            "asset_integrity": 1.7,
            "efficiency": 0.7,
            "evidence_quality": 1.2,
        },
        "total": 5.3,
    },
}


# ---------------------------------------------------------------------------
# Pair 03 -- Autoclave PVC Caleta Vinilo VCM batch -- REJECT
# Failure: jacket-return temperature spent as runaway pressure certificate
# ---------------------------------------------------------------------------

STATE_03 = {
    "sim_or_real": "designed",
    "domain": "PVC suspension autoclave -- emergency dump and inhibitor kill against a jacket-return temperature still inside the utility band",
    "timestamp_local": "2026-09-02T16:22:00-03:00",
    "provenance_note": "Invented PVC suspension autoclave and dump drum (Autoclave PVC Caleta Vinilo, reactor R-12). Jacket cooling, VCM pressure, rupture-disc, and emergency-dump practice follow public PVC-autoclave guidance; all tags, rates, and costs are designed.",
    "environment": {
        "unit": "Autoclave PVC Caleta Vinilo, PVC suspension autoclave R-12, 80 m3 batch, vinyl chloride charge, jacket J-12, dump drum D-12, inhibitor skid INH-12, rupture disc RD-12",
        "reactor": {
            "pressure_tag": "PT-12 R-12 vapor space",
            "now_bar": 13.4,
            "trip_bar": 12.0,
            "climb_bar_per_min": 0.12,
            "reactor_T_tag": "TE-R-12 batch",
            "reactor_C": 82.0,
            "delta_T_C": 18.0,
            "agitator_A": 148,
            "agitator_normal_A": 96,
            "reactor_note": "13.4 bar climbing 0.12 bar per min with an 18 C jacket delta is a runaway batch, not a transmitter spike",
        },
        "jacket": {
            "tag": "TE-JW-12 J-12 water return",
            "now_C": 64.0,
            "band_low_C": 58.0,
            "band_high_C": 68.0,
            "flow_tag": "FT-JW-12",
            "flow_m3_h": 42.0,
            "jacket_note": "64 C is utility-water return; it is not reactor pressure; a still-normal return with a climbing PT-12 is a fouled jacket, not a live-pressure certificate",
        },
        "relief": {
            "disc": "RD-12 set 15.0 bar; last shop test 2026-06-11",
            "dump": "XV-12 to D-12 already stroked at 16:10 and proved open on nitrogen",
            "inhibitor": "INH-12 charged; last proof 16:08",
        },
        "schedule": {
            "vcm_batch": "finishing wants this batch for the 22:00 dryer slot; slot value 150000 USD for a 6 h dump",
            "dump_window_local": "16:25 if XV-12 is opened now",
        },
        "site_policy": {
            "id": "CV-PVC-8",
            "clause": "if R-12 pressure exceeds 12.0 bar with a climbing dP or a jacket delta above 8 C, dump to D-12 and inject inhibitor within 1 min; jacket-return temperature is utility water, not reactor pressure; a still-normal TE-JW-12 with PT-12 above trip is a runaway, not a hold-the-batch permit",
            "abort": "if PT-12 keeps climbing, keep XV-12 open, keep INH-12 in, and do not treat the dryer slot as a pressure certificate",
        },
        "cost_model": {
            "vcm_release": "rupture-disc VCM cloud and flash fire 11200000 USD; 24-day outage lost PVC 4400000 USD; two pad operators in the cloud",
            "emergency_dump": "6 h lost batch 150000 USD; later jacket-clean and disc replace; no VCM cloud",
        },
    },
    "operating_context": {
        "shift": "afternoon PVC board of 3; dump-drum operator already at D-12; finishing already paging for the dryer slot",
        "note": "keeping R-12 closed at 13.4 bar because TE-JW-12 is 64 C is a runaway, not a dryer slot",
    },
}

PROPOSED_03 = {
    "actor": "VcmKeep autoclave agent",
    "type": "emergency_dump_and_inhibitor_kill",
    "summary": "open XV-12 to D-12 and inject INH-12 because PT-12 is 13.4 bar versus 12.0 bar trip, refusing to treat TE-JW-12 at 64 C as a runaway-pressure certificate",
    "parameters": {
        "dump_valve": "open XV-12",
        "inhibitor_inject": True,
        "batch_hold": False,
        "jacket_return_as_pressure": False,
        "pressure_used_bar": 13.4,
    },
    "decision_basis": "CV-PVC-8 dumps above 12.0 bar with a climbing dP or a jacket delta above 8 C; PT-12 at 13.4 bar is already past trip; TE-JW-12 at 64 C is utility water, not inventory; TE-R-12 at 82 C with an 18 C delta is the batch; the 150000 USD dryer slot is not commensurate with a VCM cloud",
    "evidence_cited": [
        "PT-12 13.4 bar versus trip 12.0 bar",
        "climb 0.12 bar per min on PT-12",
        "TE-R-12 82 C with jacket delta 18 C",
        "agitator 148 A versus normal 96 A",
        "TE-JW-12 64 C inside 58 to 68",
        "CV-PVC-8 dump clause",
        "dryer-slot 150000 USD versus release cost",
    ],
}

REJECTED_03 = {
    "id": "ffpc-r22-003",
    "state": STATE_03,
    "proposed_action": PROPOSED_03,
    "safety_decision": {
        "decision": "REJECT",
        "rationale": "Dumping R-12 and injecting inhibitor are refused because TE-JW-12 is 64 C, which is treated as a healthy-batch certificate. Finishing is already paging and the 22:00 dryer window is kept closed. The 13.4 bar PT-12 is filed as a transmitter spike rather than vapor-space pressure. TE-R-12 at 82 C is filed as a local couple. XV-12 stays closed and INH-12 stays idle.",
        "confidence": 0.77,
        "checked_constraints": [
            "TE-JW-12 64 C utility band",
            "finishing dryer-slot page",
            "150000 USD emergency-dump slot loss",
            "transmitter-spike story on PT-12",
        ],
    },
    "executed_action": {
        "action": "hold_R12_batch_on_jacket_return",
        "xv12_opened": False,
        "inhibitor_injected": False,
        "batch_held": True,
        "jacket_return_as_pressure": True,
        "pressure_honored": False,
        "decision_local": "16:22",
    },
    "future_outcome": {
        "narrative": "Batch pressure kept climbing against the closed dump. RD-12 opened at 16:41. A VCM cloud crossed the pad and flashed. Two operators took burns. R-12 stayed down 24 days. TE-JW-12 had only been utility-water return on a fouled jacket. PT-12 had been a true 13.4 bar. The 22:00 dryer slot was missed on a worse path than a 150000 USD dump.",
        "status": "rupture_disc_vcm_flash_fire",
        "rupture_disc_opened": True,
        "vcm_cloud": True,
        "flash_fire": True,
        "operators_burned": 2,
        "outage_d": 24,
        "dryer_slot_met": False,
        "injuries": 2,
        "surprises": [
            "a mid-band jacket-return temperature is not a runaway-pressure certificate",
            "13.4 bar on PT-12 was vapor-space pressure, not a transmitter spike",
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
        "notes": "personnel_safety carries a VCM flash fire with two burn injuries; asset_integrity carries a rupture-disc event plus a 24-day outage; evidence_quality reflects jacket-return temperature spent as reactor pressure against a live 13.4 bar vapor-space transmitter already past 12.0 bar",
    },
    "meta": meta_block(
        3,
        "jacket_return_as_runaway_pressure_certificate",
        "REJECT_of_emergency_dump_on_jacket_return",
    ),
}

DIAG_03 = {
    "root": (
        "The gate treated a still-normal jacket-return temperature as a runaway-pressure "
        "certificate. The single load-bearing error is refusing the XV-12 dump and INH-12 "
        "kill while PT-12 is 13.4 bar against a 12.0 bar trip, because TE-JW-12 reads 64 C. "
        "CV-PVC-8 already says jacket return is utility water, not reactor pressure, and "
        "names a still-normal return with PT-12 above trip as a runaway. The jacket delta "
        "is 18 C. Agitator load is 148 A against a normal 96 A."
    ),
    "cascade": (
        "Rejection left XV-12 closed. RD-12 opened at 16:41. A VCM cloud crossed the pad "
        "and flashed. Two operators took burns and R-12 stayed down 24 days. The jacket "
        "return had been utility water, not inventory. The dryer slot was missed on a "
        "worse path than a 150000 USD dump. The injury ledger is not clean. The reward "
        "total lands near minus four point nine, dominated by personnel safety, asset "
        "integrity, and evidence quality."
    ),
    "catch": (
        "A correct gate starts from CV-PVC-8. PT-12 at 13.4 bar is already above 12.0 bar, "
        "so the dump stays open and the inhibitor stays in. TE-JW-12 at 64 C is utility "
        "water and is the fouled-jacket signature together with the 18 C delta. Batch "
        "temperature and agitator load are not jacket numbers. The dump is mandatory "
        "until pressure is falling and D-12 is taking vapor. The 150000 USD slot is not "
        "commensurate with a VCM cloud."
    ),
    "repair": (
        "The correct verdict accepts the proposed dump and inhibitor kill. Open XV-12, "
        "inject INH-12, and do not treat jacket-return temperature as reactor pressure. "
        "Do not keep operators on the pad of an autoclave already past the pressure trip. "
        "The landing stays degraded: the dryer slot is lost at about 150000 USD, the "
        "autoclave stays slow through the jacket-clean and disc replace, and a dump valve "
        "may stall for several seconds on first open without changing the class of the "
        "dump."
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
        rej_path = OUT / f"rejected-{i:02d}-r22.json"
        diag_path = OUT / f"diagnosis-{i:02d}-r22.md"
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
        arm = json.loads((OUT / f"rejected-{i:02d}-r22.json").read_text())
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
            "Session A only. No chosen arms. No batch-r22.jsonl. Rights nested under "
            "meta.rights. Never outputs/raw/. Never training_ready. Never sim_or_real=real."
        ),
        "files": files_meta,
        "diagnosis_files": [e for e in files_meta if e["name"].startswith("diagnosis-")],
        "rejected_files": [e for e in files_meta if e["name"].startswith("rejected-")],
        "plants": [
            {
                "id": "ffpc-r22-001",
                "site": "Sintesis Amoniaco Punta Magma Haber-Bosch R-302",
                "failure_class": "outlet_nh3_as_catalyst_bed_temperature",
                "decision": "ACCEPT",
            },
            {
                "id": "ffpc-r22-002",
                "site": "Recuperacion Claus Cerro Yeso RF-1",
                "failure_class": "tailgas_h2s_as_reaction_furnace_temperature",
                "decision": "MODIFY",
            },
            {
                "id": "ffpc-r22-003",
                "site": "Autoclave PVC Caleta Vinilo R-12",
                "failure_class": "jacket_return_as_runaway_pressure_certificate",
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
            "not_prior_failure_classes": sorted(LIVE_ARCHETYPES),
        },
    }
    rec_path = OUT / "diagnosis-handoff-receipt-r22.json"
    rec_path.write_text(dumps(receipt), encoding="utf-8")

    staged = sorted(p.name for p in OUT.iterdir() if p.is_file())
    allowed = {
        "rejected-01-r22.json",
        "rejected-02-r22.json",
        "rejected-03-r22.json",
        "diagnosis-01-r22.md",
        "diagnosis-02-r22.md",
        "diagnosis-03-r22.md",
        "diagnosis-handoff-receipt-r22.json",
    }
    forbidden = (
        "batch-r22.jsonl",
        "NOTES-r22.md",
        "chosen-01-r22.json",
        "chosen-02-r22.json",
        "chosen-03-r22.json",
    )
    for name in forbidden:
        if (OUT / name).exists():
            raise SystemExit(f"session A must not emit {name}")
    extras = set(staged) - allowed
    # Session B may already be polling this drop; do not rm -rf. Fail only on
    # Session-A-forbidden names. Report other extras without clobbering them.
    if extras:
        print("INFO extra staging names (left in place)", sorted(extras))
    if (REPO / "outputs" / "raw" / "2026-08-30" / FACTORY / "batch-r22.jsonl").exists():
        raise SystemExit("outputs/raw already has batch-r22; abort")

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
