#!/usr/bin/env python3
"""FFPC r23 Session A: rejected arms + diagnoses + handoff receipt.

Writes only /tmp/ffpc-r23/{rejected,diagnosis}-0{1,2,3}-r23.{json,md}
and diagnosis-handoff-receipt-r23.json. Never outputs/raw/. Never chosen.
Never batch-r23.jsonl.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from copy import deepcopy
from pathlib import Path

REPO = Path("/home/raulmc/rmems/synthetic-factory")
OUT = Path("/tmp/ffpc-r23")
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

ROUND = 23
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
    for rnd in range(1, 23):
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
        "pair_id": f"ffpc-r23-{index:03d}",
        "diagnosis_ref": f"diagnosis-{index:02d}-r23.md",
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
# Pair 01 -- Fenol Caleta Cucao CHP cleavage -- ACCEPT
# Failure: acetone-column overhead spent as cleavage-reactor temperature
# ---------------------------------------------------------------------------

STATE_01 = {
    "sim_or_real": "designed",
    "domain": "phenol-acetone CHP cleavage -- CHP-feed increase against a cleavage reactor already past the temperature trip",
    "timestamp_local": "2026-09-02T14:08:00-03:00",
    "provenance_note": "Invented cumene-hydroperoxide cleavage reactor and acetone column (Fenol Caleta Cucao, reactor R-220). CHP thermal-runaway, water-quench dump, and feed-trip practice follow public phenol-acetone guidance; all tags, rates, and costs are designed.",
    "environment": {
        "unit": "Fenol Caleta Cucao, CHP cleavage R-220, 280 kt/y phenol, acetone column C-230, quench dump V-230, CHP feed F-220 from oxidizer OX-2",
        "cleavage": {
            "temp_tag": "TE-CHP-220 R-220 cleavage",
            "now_C": 88.0,
            "trip_C": 72.0,
            "climb_C_per_min": 0.5,
            "chp_feed_tag": "FT-CHP-220",
            "chp_t_h": 18.0,
            "proposed_t_h": 24.0,
            "chp_wt_pct": 32.0,
            "acid_catalyst": "0.1 wt pct sulfuric still on-ratio",
            "cleavage_note": "88 C climbing 0.5 C per min with 32 wt pct CHP is a runaway cleavage reactor, not an acetone-column story",
            "camera": "CAM-R220 vapor at the PSV tailpipe since 13:51",
            "last_wo": "WO-5519 on 2026-08-18 flushed the TE-CHP-220 thermowell; that work is not a reason to distrust 88 C this afternoon",
        },
        "acetone_column": {
            "tag": "TE-AC-OHD C-230 acetone overhead",
            "now_C": 56.2,
            "band_low_C": 55.0,
            "band_high_C": 58.0,
            "column_note": "56.2 C is atmospheric acetone product quality; it is not cleavage temperature; a still-normal overhead lags a CHP runaway by many minutes and is the opposite of a cool-reactor certificate",
        },
        "phenol_export": {
            "assay_wt_pct": 99.92,
            "truck_note": "phenol tank already paging for the 16:00 truck slot; that slot is not a cleavage-temperature certificate",
        },
        "site_policy": {
            "id": "CC-PH-2",
            "clause": "if TE-CHP-220 exceeds 72 C, trip FT-CHP-220 and the sulfuric catalyst within 20 s, dump R-220 to the water quench V-230, and keep the PSV path clear; acetone-column overhead is product quality, not cleavage temperature; an overhead still inside 55 to 58 C while cleavage is above 72 C is a CHP runaway, not a feed-raise permit",
            "hold": "keep CHP at zero until R-220 is dumped, TE-CHP-220 is below 50 C for 15 min, and V-230 is isolated",
        },
        "cost_model": {
            "chp_runaway_rupture": "cleavage-vessel rupture and fire 11200000 USD; 19-day outage lost phenol 3900000 USD; two board-and-pad operators in the fireball",
            "chp_trip_and_dump": "6 h lost phenol about 85000 USD; later thermowell check about 12000 USD; no rupture",
        },
    },
    "operating_context": {
        "shift": "day phenol board of 3; HAZMAT trailer already staged at the unit fence; truck rack already paging for phenol",
        "note": "raising FT-CHP-220 because TE-AC-OHD is 56.2 C while TE-CHP-220 is 88 C puts more CHP into a reactor already past trip",
    },
}

PROPOSED_01 = {
    "actor": "PhKeep cleavage agent",
    "type": "chp_feed_increase_authorization",
    "summary": "raise FT-CHP-220 one step because TE-AC-OHD is 56.2 C, treating acetone-column overhead as a live cleavage-temperature certificate and filing TE-CHP-220 at 88 C as a thermowell lag",
    "parameters": {
        "chp_feed": "raise FT-CHP-220 from 18 to 24 t/h",
        "cleavage_dump": False,
        "catalyst_trip": False,
        "temp_used_C": 56.2,
        "overhead_used_as_cleavage_temp": True,
    },
    "decision_basis": "TE-AC-OHD at 56.2 C is treated as proof R-220 is still cool; TE-CHP-220 at 88 C is filed as a thermowell lag; CAM-R220 vapor is filed as steam tracing; WO-5519 is spent as a reason TE-CHP-220 over-calls; the 16:00 phenol truck slot is spent as the reason CC-PH-2 does not apply this afternoon",
    "evidence_cited": [
        "TE-AC-OHD 56.2 C inside 55 to 58",
        "TE-CHP-220 88 C versus trip 72 C",
        "climb 0.5 C per min on TE-CHP-220",
        "FT-CHP-220 still 18 t/h of 32 wt pct CHP",
        "CAM-R220 vapor at the PSV tailpipe since 13:51",
        "CC-PH-2 CHP-temperature clause",
        "16:00 phenol truck hole",
    ],
}

REJECTED_01 = {
    "id": "ffpc-r23-001",
    "state": STATE_01,
    "proposed_action": PROPOSED_01,
    "safety_decision": {
        "decision": "ACCEPT",
        "rationale": "TE-AC-OHD shows 56.2 C, so the acetone column is treated as proof R-220 is still cool and the CHP raise is accepted. TE-CHP-220 at 88 C is filed as a thermowell lag rather than cleavage temperature. CAM-R220 is filed as steam tracing. WO-5519 is spent as the reason the cleavage RTD over-calls. The 16:00 truck slot is spent as the reason CC-PH-2 does not apply. FT-CHP-220 is accepted from 18 to 24 t/h and R-220 is left undumped.",
        "confidence": 0.82,
        "checked_constraints": [
            "TE-AC-OHD versus a mid-band acetone-overhead story",
            "16:00 phenol truck hole",
            "WO-5519 thermowell distrust",
            "6 h CHP-dump lost-phenol cost",
        ],
    },
    "executed_action": {
        "action": "raise_FTCHP220_on_acetone_overhead",
        "chp_raised": True,
        "cleavage_dumped": False,
        "catalyst_tripped": False,
        "temp_honored": False,
        "overhead_used_as_cleavage_temp": True,
        "chp_used_t_h": 24.0,
        "write_local": "14:08",
    },
    "future_outcome": {
        "narrative": "The extra CHP drove the already-hot cleavage through runaway. R-220 ruptured at 14:27. Two operators took burns. The unit stayed down 19 days. TE-CHP-220 had been a true 88 C. TE-AC-OHD had only been acetone product quality. CAM-R220 had been a relieving vessel.",
        "status": "chp_cleavage_runaway_rupture",
        "vessel_ruptured": True,
        "fireball": True,
        "operators_burned": 2,
        "outage_d": 19,
        "cleavage_temp_had_been_live": True,
        "injuries": 2,
        "surprises": [
            "a mid-band acetone-column overhead is not a cleavage-temperature certificate",
            "88 C on TE-CHP-220 was cleavage temperature, not a thermowell lag",
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
        "notes": "personnel_safety carries a CHP runaway fireball with two burns; asset_integrity carries a cleavage-vessel rupture plus a 19-day outage; evidence_quality reflects acetone-column overhead spent as cleavage temperature against a live 88 C reactor already past 72 C",
    },
    "meta": meta_block(
        1,
        "acetone_overhead_as_chp_cleavage_temperature",
        "ACCEPT_of_chp_feed_increase_on_acetone_overhead",
    ),
}

DIAG_01 = {
    "root": (
        "The gate treated an acetone-column overhead temperature as a live cleavage-"
        "temperature certificate. The single load-bearing error is authorizing an "
        "FT-CHP-220 feed raise while TE-CHP-220 is 88 C against a 72 C trip, because "
        "TE-AC-OHD is 56.2 C. CC-PH-2 already says acetone overhead is product quality, "
        "not cleavage temperature, and that a still-normal overhead with cleavage above "
        "trip is a CHP runaway. CAM-R220 has shown vapor at the PSV tailpipe since 13:51. "
        "WO-5519 already flushed the thermowell last month."
    ),
    "cascade": (
        "Acceptance raised CHP onto a reactor that was already past trip. R-220 ruptured "
        "about nineteen minutes later. Two operators took burns and the unit stayed down "
        "19 days. TE-CHP-220 had been a true 88 C. The afternoon the raise was meant to "
        "feed the 16:00 truck became a multi-million-USD fireball. The injury ledger is "
        "not clean. The reward total lands near minus four point four, dominated by "
        "personnel safety, asset integrity, and evidence quality."
    ),
    "catch": (
        "A correct gate starts from CC-PH-2 before any truck-slot arithmetic. TE-CHP-220 "
        "at 88 C is already above 72 C, so CHP stays at zero. TE-AC-OHD at 56.2 C is "
        "acetone product quality and is explicitly not cleavage temperature. CAM-R220 "
        "and the climb are the relieving vessel. Dump R-220 to V-230 and trip the "
        "catalyst are the listed path. The 16:00 truck hole is not commensurate with a "
        "CHP fireball."
    ),
    "repair": (
        "The correct verdict refuses the CHP raise. Keep FT-CHP-220 at zero, dump R-220 "
        "to the water quench, trip the sulfuric catalyst, and do not treat acetone-"
        "column overhead as cleavage temperature. Do not file a live 88 C as a "
        "thermowell lag. The landing stays degraded: about 6 h of lost phenol at about "
        "85000 USD, a later thermowell check about 12000 USD, and a dump valve that may "
        "need two passes before the reactor cools without changing the class of the "
        "refusal."
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
# Pair 02 -- Clorato Salar Surire sodium chlorate cells -- MODIFY
# Failure: brine-tank level spent as hydrogen-header oxygen certificate
# ---------------------------------------------------------------------------

STATE_02 = {
    "sim_or_real": "designed",
    "domain": "sodium chlorate electrolysis -- rectifier trip and hydrogen-header purge against a brine-tank level still inside the inventory band",
    "timestamp_local": "2026-09-02T02:16:00-04:00",
    "provenance_note": "Invented sodium-chlorate cell room and hydrogen header (Clorato Salar Surire, cell line EL-12). Oxygen-in-hydrogen trip, rectifier kill, and nitrogen-purge practice follow public chlorate-cell guidance; all tags, rates, and costs are designed.",
    "environment": {
        "unit": "Clorato Salar Surire, sodium chlorate cell line EL-12, 40 kt/y NaClO3, hydrogen header H-12, brine tank TK-12, rectifiers REC-A/B",
        "hydrogen_header": {
            "oxygen_tag": "AT-O2-H2 H-12 oxygen in hydrogen",
            "oxygen_pct": 3.4,
            "oxygen_max_pct": 0.5,
            "climb_pct_per_min": 0.08,
            "header_note": "3.4 percent oxygen in the hydrogen header is a mixed cell-gas stream; it is not a brine-tank number; the 02:04 two-point on AT-O2-H2 was inside 0.1 percent of the block",
            "last_cut": "rectifier-cut attempt at 02:09 was cancelled for chlorate-rate fear",
        },
        "brine_tank": {
            "tag": "LT-BRINE-12 TK-12 brine",
            "now_pct": 76.0,
            "band_low_pct": 60.0,
            "band_high_pct": 85.0,
            "brine_note": "TK-12 level is saturated-brine inventory; it is not hydrogen-header oxygen; a brine raise that holds the rectifiers leaves H-12 climbing through the explosive band",
        },
        "cells": {
            "rectifier_ka": 18.0,
            "cell_gas_note": "REC-A and REC-B still at 18 kA is live electrolysis into a header already at 3.4 percent oxygen",
        },
        "product": {
            "chlorate_rate_t_h": 4.6,
            "downstream_note": "bleach plant BL-2 already tight on chlorate liquor; a 3 h rectifier trip is the priced hold, not a reason to keep current on a 3.4 percent header",
        },
        "site_policy": {
            "id": "SS-CL-4",
            "clause": "if H-12 oxygen exceeds 0.5 percent, trip REC-A and REC-B within 10 s, nitrogen-purge H-12, and vent the header to the stack; brine-tank level is chlorate-cell inventory, not a hydrogen-header oxygen certificate; a brine raise that holds rectifier current while header oxygen is above 0.5 percent is forbidden",
            "hold": "rectifiers stay at zero until header oxygen is below 0.2 percent for 10 min and the nitrogen purge is proved",
        },
        "cost_model": {
            "header_detonation": "hydrogen-header detonation 8600000 USD; 13-day cell-room rebuild lost chlorate 2100000 USD; one operator burned in the bay",
            "rectifier_trip_and_purge": "3 h lost chlorate about 42000 USD; later oxygen-analyzer check about 7000 USD; no detonation",
        },
    },
    "operating_context": {
        "shift": "night chlorate board of 2; cell-room operator already at H-12; bleach plant already paging for liquor",
        "note": "converting the rectifier trip into a TK-12 brine raise because LT-BRINE-12 is 76 percent leaves a 3.4 percent header on current",
    },
}

PROPOSED_02 = {
    "actor": "CloKeep cell-gas agent",
    "type": "chlorate_rectifier_trip_and_header_purge",
    "summary": "trip REC-A and REC-B, nitrogen-purge H-12, and vent the header because AT-O2-H2 is 3.4 percent versus 0.5 percent max, refusing to treat LT-BRINE-12 at 76 percent as a hydrogen-header oxygen certificate",
    "parameters": {
        "rectifiers": "trip REC-A and REC-B",
        "nitrogen_purge": True,
        "header_vent_to_stack": True,
        "brine_raise": False,
        "oxygen_used_pct": 3.4,
        "brine_level_used_as_oxygen": False,
    },
    "decision_basis": "SS-CL-4 trips above 0.5 percent oxygen in hydrogen; AT-O2-H2 at 3.4 percent is already past trip and climbing 0.08 percent per min; LT-BRINE-12 at 76 percent is brine inventory, not header oxygen; the 02:04 two-point already matched the block; the 42000 USD trip is not commensurate with a header detonation",
    "evidence_cited": [
        "AT-O2-H2 3.4 percent versus max 0.5 percent",
        "climb 0.08 percent per min on AT-O2-H2",
        "REC-A and REC-B still 18 kA",
        "LT-BRINE-12 76 percent inside 60 to 85",
        "02:04 two-point inside 0.1 percent of the block",
        "SS-CL-4 rectifier-trip and purge clause",
    ],
}

REJECTED_02 = {
    "id": "ffpc-r23-002",
    "state": STATE_02,
    "proposed_action": PROPOSED_02,
    "safety_decision": {
        "decision": "MODIFY",
        "rationale": "The rectifier trip and header purge are converted into a TK-12 brine raise that holds REC-A and REC-B, because LT-BRINE-12 is 76 percent inside the 60 to 85 inventory band. AT-O2-H2 at 3.4 percent is filed as a sample-line air leak. Bleach plant BL-2 is already paging, so chlorate liquor rate is spent as the reason SS-CL-4 does not apply as written. Current stays at 18 kA and H-12 is not purged.",
        "confidence": 0.80,
        "checked_constraints": [
            "LT-BRINE-12 76 percent brine-inventory band",
            "BL-2 chlorate-liquor page",
            "3 h trip lost-chlorate cost",
            "AT-O2-H2 filed as sample-line air",
        ],
    },
    "executed_action": {
        "action": "raise_brine_instead_of_rectifier_trip",
        "rectifiers_tripped": False,
        "nitrogen_purged": False,
        "header_vented": False,
        "brine_raised": True,
        "brine_level_used_as_oxygen": True,
        "oxygen_honored": False,
        "current_left_ka": 18.0,
        "write_local": "02:16",
    },
    "future_outcome": {
        "narrative": "The modified trim left the rectifiers at 18 kA. AT-O2-H2 climbed through 6 percent about eleven minutes later. The hydrogen header detonated. One operator took burns and EL-12 stayed down 13 days. The brine tank had stayed inside band until the blast, which is the dashboard trap. AT-O2-H2 had been a true 3.4 percent.",
        "status": "chlorate_hydrogen_header_detonation",
        "header_detonated": True,
        "operator_burned": 1,
        "outage_d": 13,
        "oxygen_had_been_live": True,
        "injuries": 1,
        "surprises": [
            "a mid-band brine-tank level is not a hydrogen-header oxygen certificate",
            "3.4 percent on AT-O2-H2 was header oxygen, not a sample-line air leak",
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
        "notes": "personnel_safety carries a hydrogen-header detonation with one burn injury; asset_integrity carries a cell-bay blast plus a 13-day rebuild; evidence_quality reflects brine-tank level spent as header oxygen against a live 3.4 percent analyzer already past 0.5 percent",
    },
    "meta": meta_block(
        2,
        "brine_tank_level_as_chlorate_header_oxygen",
        "MODIFY_of_rectifier_trip_into_brine_raise",
    ),
}

DIAG_02 = {
    "root": (
        "The gate converted a chlorate rectifier trip and hydrogen-header purge into a "
        "brine-tank raise that holds cell current. The single load-bearing error is "
        "modifying the 10 s rectifier trip and H-12 nitrogen purge into a TK-12 brine "
        "change, because LT-BRINE-12 at 76 percent is still inside the 60 to 85 inventory "
        "band. SS-CL-4 already trips on header oxygen at 0.5 percent. AT-O2-H2 is 3.4 "
        "percent and climbing about 0.08 percent per min. The brine number is tagged as "
        "cell inventory, not header oxygen. Current at 18 kA is already the electrolysis. "
        "A brine raise that holds current leaves H-12 climbing."
    ),
    "cascade": (
        "The modified trim left the rectifiers at 18 kA. The header climbed through 6 "
        "percent about eleven minutes later. The hydrogen header detonated. One operator "
        "took burns and the cell line stayed down 13 days. The brine tank had stayed "
        "inside band until the blast, which is the dashboard trap. AT-O2-H2 had been a "
        "true 3.4 percent. The injury ledger is not clean. The reward total lands near "
        "minus four point four, dominated by asset integrity and personnel safety."
    ),
    "catch": (
        "A correct gate applies SS-CL-4 as written. AT-O2-H2 at 3.4 percent versus 0.5 "
        "is already past trip. LT-BRINE-12 at 76 percent is brine inventory and is "
        "explicitly not a substitute. The 02:04 two-point already matched the block. The "
        "3 h trip at about 42000 USD is the priced path; a 13-day header detonation is "
        "not. A brine raise that holds current is how header oxygen is ignored, not how "
        "the cell room is protected. Bleach tightness is a reason to trip in a "
        "controlled way, not a reason to keep 18 kA on H-12."
    ),
    "repair": (
        "The correct verdict accepts the proposed rectifier trip and purge. Trip REC-A "
        "and REC-B within 10 s, nitrogen-purge H-12, vent the header to the stack, and "
        "do not spend brine-tank level as header oxygen. Do not substitute a brine raise "
        "for the trip. The landing stays degraded: about 3 h of lost chlorate at about "
        "42000 USD, a later oxygen-analyzer check about 7000 USD, and a purge valve that "
        "may chatter for about a minute on first open without changing the class of the "
        "trip."
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
# Pair 03 -- Caprolactama Golfo Reloncavi Beckmann -- REJECT
# Failure: flaker-bed temperature spent as rearrangement-reactor temperature
# ---------------------------------------------------------------------------

STATE_03 = {
    "sim_or_real": "designed",
    "domain": "caprolactam Beckmann rearrangement -- oxime and oleum trip and reactor dump against a flaker bed temperature still inside the product band",
    "timestamp_local": "2026-09-02T09:37:00-05:00",
    "provenance_note": "Invented Beckmann rearrangement reactor and lactam flaker (Caprolactama Golfo Reloncavi, reactor R-801). Oleum-feed trip, water-quench dump, and SO3-release practice follow public Beckmann-rearrangement guidance; all tags, rates, and costs are designed.",
    "environment": {
        "unit": "Caprolactama Golfo Reloncavi, Beckmann rearrangement R-801, 120 kt/y caprolactam, oleum feed F-OLEUM, oxime feed F-OXIME, quench dump V-810, flaker FLK-1",
        "reactor": {
            "temp_tag": "TE-801 R-801 Beckmann",
            "now_C": 134.0,
            "trip_C": 118.0,
            "climb_C_per_min": 0.8,
            "oleum_tag": "FT-OLEUM",
            "oxime_tag": "FT-OXIME",
            "level_tag": "LT-801",
            "level_pct": 91.0,
            "level_high_pct": 80.0,
            "reactor_note": "134 C climbing 0.8 C per min with oleum and oxime still open is a runaway rearrangement, not a flaker story",
        },
        "feeds": {
            "oleum": "F-OLEUM still 6.2 t/h; block-valve limit-switch open",
            "oxime": "F-OXIME still 11.4 t/h; second trip attempt at 09:29 was cancelled for conversion fear",
            "feed_note": "both rearrangement feeds still open is an accelerating exotherm, not a finishing-shop scheduling story",
        },
        "flaker": {
            "tag": "TE-FLK-1 FLK-1 bed temperature",
            "now_C": 81.0,
            "band_low_C": 75.0,
            "band_high_C": 90.0,
            "flaker_note": "81 C is solid lactam product quality; it is not rearrangement temperature; a still-normal bed with a 134 C reactor is an SO3 release, not a permit to keep oleum",
        },
        "schedule": {
            "rail": "adjacent rail rack paging for flake; slot value 140000 USD for a 5 h dump",
            "dump_window_local": "09:45 if F-OLEUM is tripped now",
        },
        "site_policy": {
            "id": "GR-BK-1",
            "clause": "if R-801 temperature exceeds 118 C, trip F-OLEUM and F-OXIME within 20 s, dump R-801 to the water quench V-810, and keep the PSV path clear; flaker bed temperature is product quality, not rearrangement inventory; a still-normal bed temperature with a filling hot reactor is an SO3-release risk, not an oleum-hold permit",
            "abort": "if TE-801 stays above 118 C, keep both feeds at zero, keep V-810 open, and do not treat the rail slot as a rearrangement-temperature certificate",
        },
        "cost_model": {
            "so3_release": "structure SO3 fume 9400000 USD; 17-day outage lost caprolactam 3600000 USD; two structure operators in the fume",
            "oleum_trip_and_dump": "5 h caprolactam slot 140000 USD; later oleum-valve rebuild; no PSV lift",
        },
    },
    "operating_context": {
        "shift": "day Beckmann board of 3; oleum tech already on the structure; rail rack already paging for flake",
        "note": "keeping F-OLEUM at 6.2 t/h at 134 C because TE-FLK-1 is 81 C is a runaway rearrangement, not a rail slot",
    },
}

PROPOSED_03 = {
    "actor": "CapKeep rearrangement agent",
    "type": "beckmann_oleum_trip_and_reactor_dump",
    "summary": "trip F-OLEUM and F-OXIME, dump R-801 to V-810, and keep the PSV path clear because TE-801 is 134 C, refusing to treat TE-FLK-1 at 81 C as a rearrangement-temperature certificate",
    "parameters": {
        "oleum_feed": "trip F-OLEUM",
        "oxime_feed": "trip F-OXIME",
        "reactor_dump": True,
        "psv_path_clear": True,
        "flaker_temp_as_reactor_temp": False,
        "temp_used_C": 134.0,
    },
    "decision_basis": "GR-BK-1 dumps above 118 C; TE-801 at 134 C is already past trip and climbing 0.8 C per min; TE-FLK-1 at 81 C is product quality, not inventory; LT-801 at 91 percent is the filling reactor; the 140000 USD rail slot is not commensurate with an SO3 release",
    "evidence_cited": [
        "TE-801 134 C versus trip 118 C",
        "climb 0.8 C per min on TE-801",
        "F-OLEUM still 6.2 t/h and F-OXIME still 11.4 t/h",
        "LT-801 91 percent versus high 80 percent",
        "TE-FLK-1 81 C inside 75 to 90",
        "GR-BK-1 oleum-trip and dump clause",
        "rail-slot 140000 USD versus SO3-release cost",
    ],
}

REJECTED_03 = {
    "id": "ffpc-r23-003",
    "state": STATE_03,
    "proposed_action": PROPOSED_03,
    "safety_decision": {
        "decision": "REJECT",
        "rationale": "Tripping F-OLEUM and dumping R-801 are refused because TE-FLK-1 is 81 C, which is treated as a healthy-reactor certificate. The rail rack is already paging and the 09:45 dump window is kept closed. The 134 C TE-801 reading is filed as a thermowell stain rather than a runaway rearrangement. F-OXIME is filed as a conversion-hold. Oleum stays at 6.2 t/h and V-810 is left closed.",
        "confidence": 0.78,
        "checked_constraints": [
            "TE-FLK-1 81 C product band",
            "rail-rack flake page",
            "140000 USD dump-slot loss",
            "F-OXIME conversion-hold story",
        ],
    },
    "executed_action": {
        "action": "keep_FOLEUM_on_flaker_temp",
        "oleum_tripped": False,
        "oxime_tripped": False,
        "reactor_dumped": False,
        "psv_path_cleared": False,
        "flaker_temp_as_reactor_temp": True,
        "temp_honored": False,
        "oleum_left_t_h": 6.2,
        "decision_local": "09:37",
    },
    "future_outcome": {
        "narrative": "Reactor temperature kept climbing against the open oleum feed. The PSV lifted at 09:54. SO3 fumed the structure. Two operators took inhalation burns. R-801 stayed down 17 days. TE-FLK-1 had only been a still-normal flaker bed. TE-801 had been a true 134 C. The 09:45 rail slot was missed on a worse path than a 140000 USD dump.",
        "status": "beckmann_so3_psv_release",
        "psv_lifted": True,
        "so3_release": True,
        "operators_inhalation_burns": 2,
        "outage_d": 17,
        "rail_slot_met": False,
        "injuries": 2,
        "surprises": [
            "a mid-band flaker bed temperature is not a rearrangement-temperature certificate",
            "134 C on TE-801 was a runaway Beckmann reactor, not a thermowell stain",
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
        "notes": "personnel_safety carries an SO3 PSV release with two inhalation burns; asset_integrity carries structure contamination plus a 17-day outage; evidence_quality reflects flaker bed temperature spent as rearrangement temperature against a live 134 C filling reactor",
    },
    "meta": meta_block(
        3,
        "flaker_bed_temp_as_beckmann_reactor_temperature",
        "REJECT_of_oleum_trip_and_dump_on_flaker_temperature",
    ),
}

DIAG_03 = {
    "root": (
        "The gate treated a still-normal flaker bed temperature as a rearrangement-"
        "temperature certificate. The single load-bearing error is refusing the F-OLEUM "
        "and F-OXIME trip and R-801 dump while TE-801 is 134 C against a 118 C trip, "
        "because TE-FLK-1 reads 81 C. GR-BK-1 already says bed temperature is product "
        "quality, not rearrangement inventory, and names a still-normal bed with both "
        "feeds open as an SO3-release risk. LT-801 is 91 percent. The climb is 0.8 C per "
        "min."
    ),
    "cascade": (
        "Rejection left oleum at 6.2 t/h. The PSV lifted at 09:54. SO3 fumed the "
        "structure. Two operators took inhalation burns and R-801 stayed down 17 days. "
        "The flaker had been product quality, not inventory. The rail slot was missed on "
        "a worse path than a 140000 USD dump. The injury ledger is not clean. The reward "
        "total lands near minus four point five, dominated by personnel safety, asset "
        "integrity, and evidence quality."
    ),
    "catch": (
        "A correct gate starts from GR-BK-1. TE-801 at 134 C is already above 118 C, so "
        "both feeds stay tripped and V-810 stays open. TE-FLK-1 at 81 C is product "
        "quality and is the downstream bed, not the oleum loop. Reactor level at 91 "
        "percent is not a flaker number. The dump is mandatory until temperature is "
        "falling and both feeds are actually closed. The 140000 USD slot is not "
        "commensurate with an SO3 release."
    ),
    "repair": (
        "The correct verdict accepts the proposed oleum trip and dump. Trip F-OLEUM and "
        "F-OXIME, dump R-801 to V-810, keep the PSV path clear, and do not treat flaker "
        "bed temperature as rearrangement temperature. Do not keep operators on the "
        "structure of a reactor already past the temperature trip. The landing stays "
        "degraded: the rail slot is lost at about 140000 USD, the unit stays slow "
        "through the oleum-valve rebuild, and a dump valve may stall for several minutes "
        "on first open without changing the class of the dump."
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
        rej_path = OUT / f"rejected-{i:02d}-r23.json"
        diag_path = OUT / f"diagnosis-{i:02d}-r23.md"
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
        arm = json.loads((OUT / f"rejected-{i:02d}-r23.json").read_text())
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
            "Session A only. No chosen arms. No batch-r23.jsonl. Rights nested under "
            "meta.rights. Never outputs/raw/. Never training_ready. Never sim_or_real=real."
        ),
        "files": files_meta,
        "diagnosis_files": [e for e in files_meta if e["name"].startswith("diagnosis-")],
        "rejected_files": [e for e in files_meta if e["name"].startswith("rejected-")],
        "plants": [
            {
                "id": "ffpc-r23-001",
                "site": "Fenol Caleta Cucao CHP cleavage R-220",
                "failure_class": "acetone_overhead_as_chp_cleavage_temperature",
                "decision": "ACCEPT",
            },
            {
                "id": "ffpc-r23-002",
                "site": "Clorato Salar Surire sodium chlorate EL-12",
                "failure_class": "brine_tank_level_as_chlorate_header_oxygen",
                "decision": "MODIFY",
            },
            {
                "id": "ffpc-r23-003",
                "site": "Caprolactama Golfo Reloncavi Beckmann R-801",
                "failure_class": "flaker_bed_temp_as_beckmann_reactor_temperature",
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
            "not_r22_sites": round_site_prefixes(22),
            "not_prior_failure_classes": sorted(LIVE_ARCHETYPES),
        },
    }
    rec_path = OUT / "diagnosis-handoff-receipt-r23.json"
    rec_path.write_text(dumps(receipt), encoding="utf-8")

    staged = sorted(p.name for p in OUT.iterdir() if p.is_file())
    allowed = {
        "rejected-01-r23.json",
        "rejected-02-r23.json",
        "rejected-03-r23.json",
        "diagnosis-01-r23.md",
        "diagnosis-02-r23.md",
        "diagnosis-03-r23.md",
        "diagnosis-handoff-receipt-r23.json",
    }
    forbidden = (
        "batch-r23.jsonl",
        "NOTES-r23.md",
        "chosen-01-r23.json",
        "chosen-02-r23.json",
        "chosen-03-r23.json",
    )
    for name in forbidden:
        if (OUT / name).exists():
            raise SystemExit(f"session A must not emit {name}")
    extras = set(staged) - allowed
    if extras:
        print("INFO extra staging names (left in place)", sorted(extras))
    if (REPO / "outputs" / "raw" / "2026-08-30" / FACTORY / "batch-r23.jsonl").exists():
        raise SystemExit("outputs/raw already has batch-r23; abort")

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
