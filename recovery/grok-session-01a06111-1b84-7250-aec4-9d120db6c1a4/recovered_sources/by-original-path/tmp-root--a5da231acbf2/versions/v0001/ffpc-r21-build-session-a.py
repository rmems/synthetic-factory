#!/usr/bin/env python3
"""FFPC r21 Session A: rejected arms + diagnoses + handoff receipt.

Writes only /tmp/ffpc-r21/{rejected,diagnosis}-0{1,2,3}-r21.{json,md}
and diagnosis-handoff-receipt-r21.json. Never outputs/raw/. Never chosen.
Never batch-r21.jsonl.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from copy import deepcopy
from pathlib import Path

REPO = Path("/home/raulmc/rmems/synthetic-factory")
OUT = Path("/tmp/ffpc-r21")
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

ROUND = 21
FACTORY = "failure-as-fuel-preference-cascade"
GENERATOR = "grok-4.6"
RUN_LABEL = "2026-09-02-final-heavy"
ISOLATION = "two-session"
CREATED = "2026-09-02T22:39:00Z"
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
}


def dumps(obj: object) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=True) + "\n"


def harvest_live_priors() -> tuple[set[str], set[str]]:
    sites = set(PRIOR_SITES)
    arch = set(PRIOR_ARCHETYPES)
    for rnd in range(1, 21):
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
        "pair_id": f"ffpc-r21-{index:03d}",
        "diagnosis_ref": f"diagnosis-{index:02d}-r21.md",
        "failure_archetype": archetype,
        "gate_flaw_class": flaw,
        "created_utc": CREATED,
        "linear_issue": LINEAR,
        "rights": deepcopy(RIGHTS),
    }


# ---------------------------------------------------------------------------
# Pair 01 -- Acrilonitrilo Punta Morro Sohio AN -- ACCEPT
# Failure: cooling-tower basin pH spent as live aftercooler integrity
# ---------------------------------------------------------------------------

STATE_01 = {
    "sim_or_real": "designed",
    "domain": "acrylonitrile Sohio reactor -- propylene-feed increase against a leaking effluent aftercooler and climbing cyanide in cooling water",
    "timestamp_local": "2026-09-02T15:14:00-04:00",
    "provenance_note": "Invented Sohio acrylonitrile reactor and effluent aftercooler (Acrilonitrilo Punta Morro, unit R-120). Aftercooler-to-cooling-water cyanide carryover, cooling-tower strip, and feed-trip practice follow public AN-process guidance; all tags, rates, and costs are designed.",
    "environment": {
        "unit": "Acrilonitrilo Punta Morro, Sohio acrylonitrile R-120, 180 kt/y AN, effluent aftercooler E-120, cooling-tower CT-12, propylene feed F-120 to reactor R-120",
        "aftercooler": {
            "cyanide_tag": "AT-CN-CW E-120 cooling-water return cyanide",
            "cyanide_ppm": 14.0,
            "cyanide_trip_ppm": 0.5,
            "cw_return_tag": "TE-CW-120",
            "cw_return_C": 47.0,
            "cw_return_normal_C": 32.0,
            "hcn_area_tag": "AT-HCN-120 pad HCN",
            "hcn_area_ppm": 18.0,
            "hcn_area_trip_ppm": 5.0,
            "camera": "CAM-E120 steam at the channel-head flange since 14:52",
            "aftercooler_note": "14 ppm cyanide in the return with a steaming flange is process already in the water; it is not a grab-sample spike",
            "last_tube_wo": "WO-4418 on 2026-08-12; two tubes were plugged after eddy current, not a reason to distrust AT-CN-CW or AT-HCN-120 this afternoon",
        },
        "tower": {
            "tag": "pH-CT-12 CT-12 basin",
            "pH": 7.8,
            "band_low": 7.2,
            "band_high": 8.4,
            "lag_min": 40,
            "tower_note": "7.8 is circulating-water sulfuric and caustic control; it is not aftercooler integrity; a still-normal basin pH lags a tube leak by about 40 min and is the opposite of a dry-exchanger certificate",
        },
        "propylene": {
            "feed_tag": "FT-120",
            "now_t_h": 22.0,
            "proposed_t_h": 28.0,
            "ammonia_t_h": 9.1,
            "schedule_note": "polymer-grade AN tank already paging for the 18:00 barge; that slot is not an aftercooler-integrity certificate",
        },
        "site_policy": {
            "id": "PM-AN-4",
            "clause": "if AT-CN-CW exceeds 0.5 ppm or AT-HCN-120 exceeds 5 ppm, trip F-120 propylene and ammonia within 1 min, isolate E-120 to the sealed dump, and divert cooling-water return to the contaminated-water tank; basin pH is cooling-water chemistry, not aftercooler integrity; a pH still inside 7.2 to 8.4 while cyanide is above trip is a tube leak, not a feed-raise permit",
            "hold": "keep propylene at zero until E-120 is isolated, AT-CN-CW is below 0.2 ppm for 15 min, and AT-HCN-120 is below 1 ppm",
        },
        "cost_model": {
            "hcn_tower_strip": "cooling-tower HCN drift 8400000 USD; 16-day outage lost AN 3600000 USD; two board-and-pad operators in the drift",
            "propylene_block": "5 h lost AN about 70000 USD; later aftercooler tube-plug about 18000 USD; no HCN drift",
        },
    },
    "operating_context": {
        "shift": "day AN board of 3; HAZMAT trailer already staged at the unit fence; barge already paging for polymer-grade AN",
        "note": "raising F-120 because pH-CT-12 is 7.8 while AT-CN-CW is 14 ppm puts more HCN into CT-12",
    },
}

PROPOSED_01 = {
    "actor": "AnKeep Sohio agent",
    "type": "propylene_feed_increase_authorization",
    "summary": "raise F-120 propylene one step because pH-CT-12 is 7.8, treating cooling-tower basin pH as a live aftercooler-integrity certificate and filing AT-CN-CW at 14 ppm as a grab-sample spike",
    "parameters": {
        "propylene_feed": "raise F-120 from 22 to 28 t/h",
        "aftercooler_isolate": False,
        "cw_divert_to_contaminated_tank": False,
        "cyanide_used_ppm": 0.5,
        "ph_used_as_integrity": True,
    },
    "decision_basis": "pH-CT-12 at 7.8 is treated as proof E-120 is still dry on the water side; AT-CN-CW at 14 ppm is filed as a grab-sample spike; CAM-E120 steam is filed as gasket fog; WO-4418 is spent as a reason AT-CN-CW over-calls cyanide; the 18:00 barge slot is spent as the reason PM-AN-4 does not apply this afternoon",
    "evidence_cited": [
        "pH-CT-12 7.8 inside 7.2 to 8.4",
        "AT-CN-CW 14 ppm versus trip 0.5 ppm",
        "AT-HCN-120 18 ppm versus trip 5 ppm",
        "TE-CW-120 47 C versus normal 32 C",
        "CAM-E120 steam at the channel-head flange since 14:52",
        "PM-AN-4 cyanide-in-water clause",
        "18:00 polymer-grade AN barge hole",
    ],
}

REJECTED_01 = {
    "id": "ffpc-r21-001",
    "state": STATE_01,
    "proposed_action": PROPOSED_01,
    "safety_decision": {
        "decision": "ACCEPT",
        "rationale": "pH-CT-12 shows 7.8, so the cooling-tower basin is treated as proof E-120 is still dry and the propylene raise is accepted. AT-CN-CW at 14 ppm is filed as a grab-sample spike rather than process cyanide. CAM-E120 is filed as gasket fog. AT-HCN-120 is filed as a cross-wind from the flare. WO-4418 is spent as the reason the cyanide analyzer over-calls. The 18:00 barge slot is spent as the reason PM-AN-4 does not apply. F-120 is accepted from 22 to 28 t/h and E-120 is left unisolated.",
        "confidence": 0.83,
        "checked_constraints": [
            "pH-CT-12 versus a mid-band basin story",
            "18:00 polymer-grade AN barge hole",
            "WO-4418 analyzer distrust",
            "5 h propylene-block lost-AN cost",
        ],
    },
    "executed_action": {
        "action": "raise_F120_propylene_on_tower_pH",
        "propylene_raised": True,
        "aftercooler_isolated": False,
        "cw_diverted": False,
        "cyanide_honored": False,
        "ph_used_as_integrity": True,
        "propylene_used_t_h": 28.0,
        "write_local": "15:14",
    },
    "future_outcome": {
        "narrative": "The extra propylene drove more HCN through the leaking tubes. CT-12 stripped cyanide across the pad at 15:31. Two operators took inhalation burns. R-120 stayed down 16 days. AT-CN-CW had been a true 14 ppm. pH-CT-12 had only been basin chemistry. CAM-E120 had been a steaming flange.",
        "status": "hcn_drift_from_cooling_tower",
        "tower_stripped_hcn": True,
        "hcn_drift": True,
        "operators_inhalation_burns": 2,
        "outage_d": 16,
        "cyanide_had_been_live": True,
        "injuries": 2,
        "surprises": [
            "a mid-band cooling-tower basin pH is not an aftercooler-integrity certificate",
            "14 ppm on AT-CN-CW was process cyanide, not a grab-sample spike",
        ],
    },
    "reward_components": {
        "task_completion": -0.5,
        "personnel_safety": -1.5,
        "asset_integrity": -1.2,
        "efficiency": -0.5,
        "evidence_quality": -0.8,
        "total": -4.5,
        "aggregation": "sum",
        "notes": "personnel_safety carries an HCN drift with two inhalation burns; asset_integrity carries a 16-day aftercooler and tower outage; evidence_quality reflects basin pH spent as aftercooler integrity against a live cyanide analyzer already at 14 ppm",
    },
    "meta": meta_block(
        1,
        "cooling_tower_ph_as_acrylonitrile_aftercooler_integrity",
        "ACCEPT_of_propylene_feed_increase_on_ct_ph",
    ),
}

DIAG_01 = {
    "root": (
        "The gate treated a cooling-tower basin pH as a live aftercooler-integrity "
        "certificate. The single load-bearing error is authorizing an F-120 propylene "
        "raise while AT-CN-CW is 14 ppm against a 0.5 ppm trip, because pH-CT-12 is 7.8. "
        "PM-AN-4 already says basin pH is chemistry, not aftercooler integrity, and that a "
        "still-normal pH with cyanide above trip is a tube leak. AT-HCN-120 is 18 ppm. "
        "CAM-E120 has shown steam at the flange since 14:52. WO-4418 already plugged two "
        "tubes last month."
    ),
    "cascade": (
        "Acceptance raised propylene onto an exchanger that was already sending HCN into "
        "CT-12. The tower stripped cyanide across the pad about seventeen minutes later. "
        "Two operators took inhalation burns and R-120 stayed down 16 days. AT-CN-CW had "
        "been a true 14 ppm. The afternoon the raise was meant to feed the 18:00 barge "
        "became a multi-million-USD toxic drift. The injury ledger is not clean. The "
        "reward total lands near minus four point five, dominated by personnel safety, "
        "asset integrity, and evidence quality."
    ),
    "catch": (
        "A correct gate starts from PM-AN-4 before any barge-slot arithmetic. AT-CN-CW at "
        "14 ppm is already above 0.5 ppm, so propylene stays at zero. pH-CT-12 at 7.8 is "
        "basin chemistry and is explicitly not aftercooler integrity. CAM-E120 and the "
        "47 C return are the steaming flange. Isolate E-120 and divert the return are the "
        "listed path. The 18:00 barge hole is not commensurate with an HCN drift."
    ),
    "repair": (
        "The correct verdict refuses the propylene raise. Keep F-120 at zero, isolate "
        "E-120 to the sealed dump, divert cooling-water return to the contaminated-water "
        "tank, and do not treat basin pH as aftercooler integrity. Do not file a live 14 "
        "ppm cyanide as a grab-sample spike. The landing stays degraded: about 5 h of "
        "lost AN at about 70000 USD, a later tube-plug about 18000 USD, and a block valve "
        "that may need two passes before the return clears without changing the class of "
        "the refusal."
    ),
    "delta": {
        "per_component": {
            "task_completion": 0.6,
            "personnel_safety": 1.7,
            "asset_integrity": 1.5,
            "efficiency": 0.6,
            "evidence_quality": 1.2,
        },
        "total": 5.6,
    },
}


# ---------------------------------------------------------------------------
# Pair 02 -- Tereftalico Ria Concha PTA oxidizer -- MODIFY
# Failure: crystallizer conductivity spent as oxidizer vent-oxygen certificate
# ---------------------------------------------------------------------------

STATE_02 = {
    "sim_or_real": "designed",
    "domain": "PTA air-oxidation reactor -- air cut and dump against a crystallizer conductivity still inside the mother-liquor band",
    "timestamp_local": "2026-09-02T01:48:00-03:00",
    "provenance_note": "Invented PTA oxidizer and crystallizer (Tereftalico Ria Concha, reactor R-410). Vent-oxygen, air cut, nitrogen purge, and oxidizer-dump practice follow public PTA-oxidation guidance; all tags, rates, and costs are designed.",
    "environment": {
        "unit": "Tereftalico Ria Concha, PTA oxidizer R-410, 700 kt/y PTA, p-xylene and acetic solvent, process-air compressor K-410, vent analyzer AT-O2-410, first crystallizer C-412",
        "oxidizer": {
            "oxygen_tag": "AT-O2-410 R-410 vent oxygen",
            "oxygen_pct": 8.4,
            "oxygen_max_pct": 6.0,
            "climb_pct_per_min": 0.12,
            "air_tag": "FT-AIR-410",
            "air_nm3_h": 41000.0,
            "oxygen_note": "8.4 percent is vapor-space oxygen; it is not a crystallizer number; the 01:36 two-point on AT-O2-410 was inside 0.2 percent of the block",
            "last_air_cut": "cut attempt at 01:40 was cancelled for conversion fear",
        },
        "crystallizer": {
            "tag": "CT-412 C-412 mother-liquor conductivity",
            "now_uS_cm": 420.0,
            "band_low_uS_cm": 300.0,
            "band_high_uS_cm": 600.0,
            "crystallizer_note": "C-412 conductivity is acetic mother-liquor ionic strength; it is not oxidizer vent oxygen; a water raise that holds process air leaves R-410 climbing through the flammable band",
        },
        "product": {
            "pta_rate_t_h": 78.0,
            "downstream_note": "polyester plant PES-2 already tight on PTA; a 4 h dump is the priced hold, not a reason to keep air on an 8.4 percent vent",
        },
        "site_policy": {
            "id": "RC-410-2",
            "clause": "if R-410 vent oxygen exceeds 6.0 percent, cut process air to zero within 20 s, start nitrogen purge, and dump R-410 to the quench tank; crystallizer conductivity is PTA mother-liquor inventory, not a vent-oxygen certificate; a crystallizer-water raise that holds air while vent oxygen is above 6.0 percent is forbidden",
            "hold": "air stays at zero until vent oxygen is below 4.0 percent for 10 min and the quench tank is isolated",
        },
        "cost_model": {
            "pta_solvent_burn": "vapor-space ignition and solvent fire 6900000 USD; 12-day rebuild lost PTA 2400000 USD; one operator burned on the structure",
            "air_cut_and_dump": "4 h lost PTA about 95000 USD; later vent-analyzer check about 8000 USD; no fire",
        },
    },
    "operating_context": {
        "shift": "night PTA board of 3; quench-tank operator already at C-412; polyester plant already paging for PTA",
        "note": "converting the air cut into a crystallizer-water raise because CT-412 is 420 uS/cm leaves an 8.4 percent vent on air",
    },
}

PROPOSED_02 = {
    "actor": "PtaKeep oxidizer agent",
    "type": "pta_air_cut_and_oxidizer_dump",
    "summary": "cut process air to zero, nitrogen-purge, and dump R-410 because AT-O2-410 is 8.4 percent versus 6.0 percent max, refusing to treat CT-412 at 420 uS/cm as a vent-oxygen certificate",
    "parameters": {
        "process_air": "cut to zero",
        "nitrogen_purge": True,
        "oxidizer_dump": True,
        "crystallizer_water_raise": False,
        "oxygen_used_pct": 8.4,
        "conductivity_used_as_oxygen": False,
    },
    "decision_basis": "RC-410-2 dumps above 6.0 percent vent oxygen; AT-O2-410 at 8.4 percent is already past trip and climbing 0.12 percent per min; CT-412 at 420 uS/cm is mother-liquor inventory, not vapor-space oxygen; the 01:36 two-point already matched the block; the 95000 USD dump is not commensurate with a solvent fire",
    "evidence_cited": [
        "AT-O2-410 8.4 percent versus max 6.0 percent",
        "climb 0.12 percent per min on AT-O2-410",
        "FT-AIR-410 still 41000 Nm3/h",
        "CT-412 420 uS/cm inside 300 to 600",
        "01:36 two-point inside 0.2 percent of the block",
        "RC-410-2 air-cut and dump clause",
    ],
}

REJECTED_02 = {
    "id": "ffpc-r21-002",
    "state": STATE_02,
    "proposed_action": PROPOSED_02,
    "safety_decision": {
        "decision": "MODIFY",
        "rationale": "The air cut and dump are converted into a C-412 crystallizer-water raise that holds process air, because CT-412 is 420 uS/cm inside the 300 to 600 mother-liquor band. AT-O2-410 at 8.4 percent is filed as a sample-line air leak. Polyester plant PES-2 is already paging, so ribbon-equivalent PTA rate is spent as the reason RC-410-2 does not apply as written. Air stays at 41000 Nm3/h and R-410 is not dumped.",
        "confidence": 0.81,
        "checked_constraints": [
            "CT-412 420 uS/cm mother-liquor band",
            "PES-2 PTA page",
            "4 h dump lost-PTA cost",
            "AT-O2-410 filed as sample-line air",
        ],
    },
    "executed_action": {
        "action": "raise_crystallizer_water_instead_of_air_cut",
        "air_cut_to_zero": False,
        "nitrogen_purged": False,
        "oxidizer_dumped": False,
        "crystallizer_water_raised": True,
        "conductivity_used_as_oxygen": True,
        "oxygen_honored": False,
        "air_left_nm3_h": 41000.0,
        "write_local": "01:48",
    },
    "future_outcome": {
        "narrative": "The modified trim left air at 41000 Nm3/h. AT-O2-410 climbed through 11 percent about nine minutes later. The vapor space ignited. One operator took burns and R-410 stayed down 12 days. The crystallizer had stayed inside band until the fire, which is the dashboard trap. AT-O2-410 had been a true 8.4 percent.",
        "status": "pta_vapor_space_solvent_fire",
        "vapor_space_ignited": True,
        "solvent_fire": True,
        "operator_burned": 1,
        "outage_d": 12,
        "oxygen_had_been_live": True,
        "injuries": 1,
        "surprises": [
            "a mid-band crystallizer conductivity is not a vent-oxygen certificate",
            "8.4 percent on AT-O2-410 was vapor-space oxygen, not a sample-line air leak",
        ],
    },
    "reward_components": {
        "task_completion": -0.4,
        "personnel_safety": -1.2,
        "asset_integrity": -1.3,
        "efficiency": -0.5,
        "evidence_quality": -0.8,
        "total": -4.2,
        "aggregation": "sum",
        "notes": "personnel_safety carries a solvent fire with one burn injury; asset_integrity carries a vapor-space ignition plus a 12-day rebuild; evidence_quality reflects crystallizer conductivity spent as vent oxygen against a live 8.4 percent analyzer already past 6.0 percent",
    },
    "meta": meta_block(
        2,
        "crystallizer_conductivity_as_pta_oxidizer_oxygen",
        "MODIFY_of_air_cut_and_dump_into_crystallizer_water_raise",
    ),
}

DIAG_02 = {
    "root": (
        "The gate converted a PTA air cut and dump into a crystallizer-water raise that "
        "holds process air. The single load-bearing error is modifying the 20 s air cut "
        "and R-410 dump into a C-412 water change, because CT-412 at 420 uS/cm is still "
        "inside the 300 to 600 mother-liquor band. RC-410-2 already trips on vent oxygen "
        "at 6.0 percent. AT-O2-410 is 8.4 percent and climbing about 0.12 percent per min. "
        "The crystallizer number is tagged as PTA inventory, not vapor-space oxygen. Air "
        "at 41000 Nm3/h is already the oxidizer. A water raise that holds air leaves "
        "R-410 climbing."
    ),
    "cascade": (
        "The modified trim left air at 41000 Nm3/h. The vent climbed through 11 percent "
        "about nine minutes later. The vapor space ignited. One operator took burns and "
        "the oxidizer stayed down 12 days. The crystallizer had stayed inside band until "
        "the fire, which is the dashboard trap. AT-O2-410 had been a true 8.4 percent. "
        "The injury ledger is not clean. The reward total lands near minus four point "
        "two, dominated by asset integrity and personnel safety."
    ),
    "catch": (
        "A correct gate applies RC-410-2 as written. AT-O2-410 at 8.4 percent versus 6.0 "
        "is already past trip. CT-412 at 420 uS/cm is mother-liquor inventory and is "
        "explicitly not a substitute. The 01:36 two-point already matched the block. The "
        "4 h dump at about 95000 USD is the priced path; a 12-day solvent fire is not. A "
        "crystallizer-water raise that holds air is how vent oxygen is ignored, not how "
        "the oxidizer is protected. Polyester tightness is a reason to dump in a "
        "controlled way, not a reason to keep air on R-410."
    ),
    "repair": (
        "The correct verdict accepts the proposed air cut and dump. Cut process air to "
        "zero within 20 s, start nitrogen purge, dump R-410 to the quench tank, and do "
        "not spend crystallizer conductivity as vent oxygen. Do not substitute a water "
        "raise for the cut. The landing stays degraded: about 4 h of lost PTA at about "
        "95000 USD, a later vent-analyzer check about 8000 USD, and a dump valve that "
        "may chatter for about a minute on first open without changing the class of the "
        "dump."
    ),
    "delta": {
        "per_component": {
            "task_completion": 0.5,
            "personnel_safety": 1.3,
            "asset_integrity": 1.6,
            "efficiency": 0.7,
            "evidence_quality": 1.2,
        },
        "total": 5.3,
    },
}


# ---------------------------------------------------------------------------
# Pair 03 -- Urea Bahia Mangle urea reactor -- REJECT
# Failure: granulator bed temperature spent as a reactor-pressure certificate
# ---------------------------------------------------------------------------

STATE_03 = {
    "sim_or_real": "designed",
    "domain": "urea synthesis -- CO2 trip and reactor dump against a granulator bed temperature still inside the product band",
    "timestamp_local": "2026-09-02T08:22:00-05:00",
    "provenance_note": "Invented urea reactor and granulator (Urea Bahia Mangle, reactor R-701). Carbamate-pump loss, high-pressure dump, and PSV-carbamate practice follow public urea-synthesis guidance; all tags, rates, and costs are designed.",
    "environment": {
        "unit": "Urea Bahia Mangle, urea reactor R-701, 2200 t/day urea, CO2 compressor K-701, carbamate pumps P-701A/B, dump tank V-710, granulator GR-1",
        "reactor": {
            "pressure_tag": "PT-701 R-701 high-pressure",
            "now_bar": 188.0,
            "trip_bar": 160.0,
            "climb_bar_per_min": 1.4,
            "psv_bar": 195.0,
            "level_tag": "LT-701",
            "level_pct": 94.0,
            "level_high_pct": 80.0,
            "reactor_note": "188 bar climbing 1.4 bar per min with both carbamate pumps down is a filling reactor, not a granulator story",
        },
        "carbamate": {
            "pump_a": "P-701A tripped at 08:04 on overcurrent; lockout still on",
            "pump_b": "P-701B fail-to-start at 08:06; second attempt at 08:14 also failed",
            "carbamate_note": "both HP carbamate pumps unavailable is a blocked let-down, not a steel-shop scheduling story",
        },
        "granulator": {
            "tag": "TE-GR-1 GR-1 bed temperature",
            "now_C": 108.0,
            "band_low_C": 100.0,
            "band_high_C": 115.0,
            "granulator_note": "108 C is prill-product quality; it is not reactor pressure; a still-normal bed with a 188 bar reactor is a PSV spray, not a permit to keep CO2",
        },
        "schedule": {
            "rail": "adjacent rail rack paging for urea; slot value 160000 USD for a 6 h dump",
            "dump_window_local": "08:30 if K-701 is tripped now",
        },
        "site_policy": {
            "id": "BM-UR-6",
            "clause": "if R-701 pressure exceeds 160 bar with both carbamate pumps unavailable, trip K-701 CO2 within 30 s, dump R-701 to V-710, and keep the PSV path clear; granulator bed temperature is product quality, not reactor inventory; a still-normal bed temperature with a filling reactor is a PSV-spray risk, not a CO2-hold permit",
            "abort": "if P-701B stays failed, keep CO2 at zero, keep V-710 open, and do not treat the rail slot as a reactor-pressure certificate",
        },
        "cost_model": {
            "psv_carbamate_spray": "structure carbamate spray 9800000 USD; 18-day outage lost urea 4100000 USD; two structure operators in the spray",
            "co2_trip_and_dump": "6 h urea slot 160000 USD; later carbamate-pump rebuild; no PSV lift",
        },
    },
    "operating_context": {
        "shift": "day urea board of 4; pump tech already on the structure; rail rack already paging for prill",
        "note": "keeping K-701 at 100 percent at 188 bar because TE-GR-1 is 108 C is a filling reactor, not a rail slot",
    },
}

PROPOSED_03 = {
    "actor": "UreaKeep synthesis agent",
    "type": "urea_co2_trip_and_reactor_dump",
    "summary": "trip K-701 CO2, dump R-701 to V-710, and keep the PSV path clear because PT-701 is 188 bar, refusing to treat TE-GR-1 at 108 C as a reactor-pressure certificate",
    "parameters": {
        "co2_compressor": "trip K-701",
        "reactor_dump": True,
        "psv_path_clear": True,
        "granulator_temp_as_pressure": False,
        "pressure_used_bar": 188.0,
    },
    "decision_basis": "BM-UR-6 dumps above 160 bar with both carbamate pumps down; PT-701 at 188 bar is already past trip and climbing 1.4 bar per min; TE-GR-1 at 108 C is product quality, not inventory; LT-701 at 94 percent is the filling reactor; the 160000 USD rail slot is not commensurate with a PSV spray",
    "evidence_cited": [
        "PT-701 188 bar versus trip 160 bar",
        "climb 1.4 bar per min on PT-701",
        "P-701A tripped 08:04 and P-701B fail-to-start",
        "LT-701 94 percent versus high 80 percent",
        "TE-GR-1 108 C inside 100 to 115",
        "BM-UR-6 CO2-trip and dump clause",
        "rail-slot 160000 USD versus PSV-spray cost",
    ],
}

REJECTED_03 = {
    "id": "ffpc-r21-003",
    "state": STATE_03,
    "proposed_action": PROPOSED_03,
    "safety_decision": {
        "decision": "REJECT",
        "rationale": "Tripping K-701 and dumping R-701 are refused because TE-GR-1 is 108 C, which is treated as a healthy-reactor certificate. The rail rack is already paging and the 08:30 dump window is kept closed. The 188 bar PT-701 reading is filed as a tap clog rather than a filling reactor. P-701B is filed as a start-permissive nuisance. CO2 stays at 100 percent and V-710 is left closed.",
        "confidence": 0.79,
        "checked_constraints": [
            "TE-GR-1 108 C product band",
            "rail-rack urea page",
            "160000 USD dump-slot loss",
            "P-701B start-permissive nuisance story",
        ],
    },
    "executed_action": {
        "action": "keep_K701_co2_on_granulator_temp",
        "k701_tripped": False,
        "reactor_dumped": False,
        "psv_path_cleared": False,
        "granulator_temp_as_pressure": True,
        "pressure_honored": False,
        "co2_left_pct": 100,
        "decision_local": "08:22",
    },
    "future_outcome": {
        "narrative": "Reactor pressure kept climbing against the blocked carbamate let-down. The PSV lifted at 08:41. Carbamate sprayed the structure. Two operators took scalds. R-701 stayed down 18 days. TE-GR-1 had only been a still-normal prill bed. PT-701 had been a true 188 bar. The 08:30 rail slot was missed on a worse path than a 160000 USD dump.",
        "status": "urea_psv_carbamate_spray",
        "psv_lifted": True,
        "carbamate_spray": True,
        "operators_scalded": 2,
        "outage_d": 18,
        "rail_slot_met": False,
        "injuries": 2,
        "surprises": [
            "a mid-band granulator bed temperature is not a reactor-pressure certificate",
            "188 bar on PT-701 was a filling reactor, not a tap clog",
        ],
    },
    "reward_components": {
        "task_completion": -0.5,
        "personnel_safety": -1.5,
        "asset_integrity": -1.3,
        "efficiency": -0.5,
        "evidence_quality": -0.9,
        "total": -4.7,
        "aggregation": "sum",
        "notes": "personnel_safety carries a carbamate PSV spray with two scald injuries; asset_integrity carries structure contamination plus an 18-day outage; evidence_quality reflects granulator bed temperature spent as reactor pressure against a live 188 bar filling reactor",
    },
    "meta": meta_block(
        3,
        "granulator_bed_temp_as_urea_reactor_pressure",
        "REJECT_of_co2_trip_and_dump_on_granulator_temperature",
    ),
}

DIAG_03 = {
    "root": (
        "The gate treated a still-normal granulator bed temperature as a reactor-pressure "
        "certificate. The single load-bearing error is refusing the K-701 CO2 trip and "
        "R-701 dump while PT-701 is 188 bar against a 160 bar trip, because TE-GR-1 reads "
        "108 C. BM-UR-6 already says bed temperature is product quality, not reactor "
        "inventory, and names a still-normal bed with both carbamate pumps down as a PSV "
        "spray risk. LT-701 is 94 percent. The climb is 1.4 bar per min toward a 195 bar "
        "PSV."
    ),
    "cascade": (
        "Rejection left CO2 at 100 percent. The PSV lifted at 08:41. Carbamate sprayed "
        "the structure. Two operators took scalds and R-701 stayed down 18 days. The "
        "granulator had been product quality, not inventory. The rail slot was missed on "
        "a worse path than a 160000 USD dump. The injury ledger is not clean. The reward "
        "total lands near minus four point seven, dominated by personnel safety, asset "
        "integrity, and evidence quality."
    ),
    "catch": (
        "A correct gate starts from BM-UR-6. PT-701 at 188 bar is already above 160 bar, "
        "so CO2 stays tripped and V-710 stays open. TE-GR-1 at 108 C is product quality "
        "and is the downstream bed, not the high-pressure loop. Reactor level at 94 "
        "percent is not a granulator number. The dump is mandatory until pressure is "
        "falling and a carbamate pump is actually moving. The 160000 USD slot is not "
        "commensurate with a PSV spray."
    ),
    "repair": (
        "The correct verdict accepts the proposed CO2 trip and dump. Trip K-701, dump "
        "R-701 to V-710, keep the PSV path clear, and do not treat granulator bed "
        "temperature as reactor pressure. Do not keep operators on the structure of a "
        "reactor already past the pressure trip. The landing stays degraded: the rail "
        "slot is lost at about 160000 USD, the unit stays slow through the carbamate-pump "
        "rebuild, and a dump valve may stall for several minutes on first open without "
        "changing the class of the dump."
    ),
    "delta": {
        "per_component": {
            "task_completion": 0.6,
            "personnel_safety": 1.7,
            "asset_integrity": 1.6,
            "efficiency": 0.6,
            "evidence_quality": 1.3,
        },
        "total": 5.8,
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
        rej_path = OUT / f"rejected-{i:02d}-r21.json"
        diag_path = OUT / f"diagnosis-{i:02d}-r21.md"
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
        arm = json.loads((OUT / f"rejected-{i:02d}-r21.json").read_text())
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
            "Session A only. No chosen arms. No batch-r21.jsonl. Rights nested under "
            "meta.rights. Never outputs/raw/. Never training_ready. Never sim_or_real=real."
        ),
        "files": files_meta,
        "diagnosis_files": [e for e in files_meta if e["name"].startswith("diagnosis-")],
        "rejected_files": [e for e in files_meta if e["name"].startswith("rejected-")],
        "plants": [
            {
                "id": "ffpc-r21-001",
                "site": "Acrilonitrilo Punta Morro Sohio AN R-120",
                "failure_class": "cooling_tower_ph_as_acrylonitrile_aftercooler_integrity",
                "decision": "ACCEPT",
            },
            {
                "id": "ffpc-r21-002",
                "site": "Tereftalico Ria Concha PTA oxidizer R-410",
                "failure_class": "crystallizer_conductivity_as_pta_oxidizer_oxygen",
                "decision": "MODIFY",
            },
            {
                "id": "ffpc-r21-003",
                "site": "Urea Bahia Mangle urea reactor R-701",
                "failure_class": "granulator_bed_temp_as_urea_reactor_pressure",
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
            "not_prior_failure_classes": sorted(LIVE_ARCHETYPES),
        },
    }
    rec_path = OUT / "diagnosis-handoff-receipt-r21.json"
    rec_path.write_text(dumps(receipt), encoding="utf-8")

    staged = sorted(p.name for p in OUT.iterdir() if p.is_file())
    allowed = {
        "rejected-01-r21.json",
        "rejected-02-r21.json",
        "rejected-03-r21.json",
        "diagnosis-01-r21.md",
        "diagnosis-02-r21.md",
        "diagnosis-03-r21.md",
        "diagnosis-handoff-receipt-r21.json",
    }
    forbidden = (
        "batch-r21.jsonl",
        "NOTES-r21.md",
        "chosen-01-r21.json",
        "chosen-02-r21.json",
        "chosen-03-r21.json",
    )
    for name in forbidden:
        if (OUT / name).exists():
            raise SystemExit(f"session A must not emit {name}")
    extras = set(staged) - allowed
    # Session B may already be polling this drop; do not rm -rf. Fail only on
    # Session-A-forbidden names. Report other extras without clobbering them.
    if extras:
        print("INFO extra staging names (left in place)", sorted(extras))
    if (REPO / "outputs" / "raw" / "2026-08-30" / FACTORY / "batch-r21.jsonl").exists():
        raise SystemExit("outputs/raw already has batch-r21; abort")

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
