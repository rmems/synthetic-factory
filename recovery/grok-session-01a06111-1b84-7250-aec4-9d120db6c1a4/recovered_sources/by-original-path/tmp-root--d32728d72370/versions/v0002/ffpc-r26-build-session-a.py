#!/usr/bin/env python3
"""FFPC r25 Session A: rejected arms + diagnoses + handoff receipt.

Writes only /tmp/ffpc-r25/{rejected,diagnosis}-0{1,2,3}-r25.{json,md}
and diagnosis-handoff-receipt-r25.json. Never outputs/raw/. Never chosen.
Never batch-r25.jsonl.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from copy import deepcopy
from pathlib import Path

REPO = Path("/home/raulmc/rmems/synthetic-factory")
OUT = Path("/tmp/ffpc-r25")
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

ROUND = 26
FACTORY = "failure-as-fuel-preference-cascade"
GENERATOR = "grok-4.6"
RUN_LABEL = "2026-09-02-final-heavy"
ISOLATION = "two-session"
CREATED = "2026-09-02T23:08:00Z"
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
        "pair_id": f"ffpc-r25-{index:03d}",
        "diagnosis_ref": f"diagnosis-{index:02d}-r25.md",
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
# Pair 01 -- Silicio Electrico Fiordo Puyuhuapi submerged-arc -- ACCEPT
# Failure: off-gas CO spent as electrode-immersion certificate
# ---------------------------------------------------------------------------

STATE_01 = {
    "sim_or_real": "designed",
    "domain": "submerged-arc silicon furnace -- electrode-lower against a hearth already overfilled and a taphole already spraying",
    "timestamp_local": "2026-09-02T11:22:00-03:00",
    "provenance_note": "Invented submerged-arc silicon furnace and off-gas duct (Silicio Electrico Fiordo Puyuhuapi, furnace SAF-3). Hearth-breakout, electrode-raise, and load-cut practice follow public silicon-metal furnace guidance; all tags, rates, and costs are designed.",
    "environment": {
        "unit": "Silicio Electrico Fiordo Puyuhuapi, submerged-arc silicon furnace SAF-3, 32 MW, 80 t/day Si, three Soderberg electrodes, taphole TH-3, off-gas duct OG-3",
        "hearth": {
            "level_tag": "LT-HRT-3 SAF-3 hearth radar",
            "now_pct": 94.0,
            "high_pct": 80.0,
            "current_tag": "IT-EL-3 electrode current",
            "current_ka": 92.0,
            "current_max_ka": 78.0,
            "mw_now": 34.5,
            "mw_rated": 32.0,
            "hearth_note": "94 percent hearth with 92 kA already past 78 kA is an overfilled crater, not an off-gas-chemistry story",
            "camera": "CAM-TH3 taphole spray since 11:04",
            "last_wo": "WO-8834 on 2026-08-19 recalibrated LT-HRT-3; that work is not a reason to distrust 94 percent this morning",
        },
        "offgas": {
            "tag": "AT-CO-3 OG-3 furnace off-gas CO",
            "now_pct": 78.0,
            "band_low_pct": 72.0,
            "band_high_pct": 85.0,
            "co_note": "78 percent CO is reduction-gas quality; it is not electrode immersion; a still-normal CO with a spraying taphole is a hearth-breakout path, not a lower-electrode permit",
        },
        "cast_house": {
            "pig_note": "cast house already paging for the 13:30 pig-bed slot; that slot is not an electrode-immersion certificate",
        },
        "site_policy": {
            "id": "FP-SI-3",
            "clause": "if LT-HRT-3 exceeds 80 percent or CAM-TH3 shows taphole spray, raise the three electrodes within 20 s, cut load below 24 MW, and do not tap; off-gas CO is reduction chemistry, not electrode immersion; a CO still inside 72 to 85 percent with a spraying taphole is a hearth breakout, not a lower-electrode permit",
            "hold": "keep electrodes raised and load below 24 MW until hearth radar is below 70 percent for 15 min and CAM-TH3 is dry",
        },
        "cost_model": {
            "hearth_breakout": "hearth breakout and Si fire 12100000 USD; 14-day rebuild lost silicon 2700000 USD; two tap-floor operators in the pour",
            "electrode_raise_and_load_cut": "5 h lost silicon about 54000 USD; later radar check about 8000 USD; no breakout",
        },
    },
    "operating_context": {
        "shift": "day silicon board of 3; tap-floor crew already at TH-3; cast house already paging for pigs",
        "note": "lowering electrodes because AT-CO-3 is 78 percent while LT-HRT-3 is 94 percent and CAM-TH3 is spraying puts more power into an overfilled hearth",
    },
}

PROPOSED_01 = {
    "actor": "SiKeep electrode agent",
    "type": "electrode_lower_authorization",
    "summary": "lower the three Soderberg electrodes one step because AT-CO-3 is 78 percent, treating off-gas CO as a live electrode-immersion certificate and filing LT-HRT-3 at 94 percent as a radar lag",
    "parameters": {
        "electrodes": "lower EL-A, EL-B, EL-C one notch",
        "load_cut": False,
        "tap_hold": False,
        "immersion_used": "AT-CO-3 78 percent",
        "offgas_co_used_as_immersion": True,
    },
    "decision_basis": "AT-CO-3 at 78 percent is treated as proof the electrodes are still high; LT-HRT-3 at 94 percent is filed as a radar lag; CAM-TH3 spray is filed as steam from wet mix; WO-8834 is spent as a reason LT-HRT-3 over-calls; the 13:30 pig-bed slot is spent as the reason FP-SI-3 does not apply this morning",
    "evidence_cited": [
        "AT-CO-3 78 percent inside 72 to 85",
        "LT-HRT-3 94 percent versus high 80 percent",
        "IT-EL-3 92 kA versus 78 kA max",
        "CAM-TH3 taphole spray since 11:04",
        "FP-SI-3 electrode-raise clause",
        "13:30 pig-bed hole",
    ],
}

REJECTED_01 = {
    "id": "ffpc-r25-001",
    "state": STATE_01,
    "proposed_action": PROPOSED_01,
    "safety_decision": {
        "decision": "ACCEPT",
        "rationale": "AT-CO-3 shows 78 percent, so the off-gas duct is treated as proof the electrodes are still high and the lower is accepted. LT-HRT-3 at 94 percent is filed as a radar lag rather than hearth fill. CAM-TH3 is filed as steam from wet mix. WO-8834 is spent as the reason the hearth radar over-calls. The 13:30 pig-bed slot is spent as the reason FP-SI-3 does not apply. Electrodes are accepted one notch down and load is left at 34.5 MW.",
        "confidence": 0.81,
        "checked_constraints": [
            "AT-CO-3 versus a mid-band off-gas-CO story",
            "13:30 pig-bed hole",
            "WO-8834 radar distrust",
            "5 h load-cut lost-silicon cost",
        ],
    },
    "executed_action": {
        "action": "lower_electrodes_on_offgas_co",
        "electrodes_lowered": True,
        "load_cut": False,
        "tap_held": False,
        "hearth_honored": False,
        "offgas_co_used_as_immersion": True,
        "current_left_ka": 92.0,
        "write_local": "11:22",
    },
    "future_outcome": {
        "narrative": "The extra immersion drove the already-full hearth through the lining. SAF-3 broke out at 11:41. Two tap-floor operators took burns. The furnace stayed down 14 days. LT-HRT-3 had been a true 94 percent. AT-CO-3 had only been reduction-gas quality. CAM-TH3 had been a spraying taphole.",
        "status": "silicon_hearth_breakout",
        "hearth_broke_out": True,
        "silicon_pour": True,
        "operators_burned": 2,
        "outage_d": 14,
        "hearth_level_had_been_live": True,
        "injuries": 2,
        "surprises": [
            "a mid-band off-gas CO is not an electrode-immersion certificate",
            "94 percent on LT-HRT-3 was hearth fill, not a radar lag",
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
        "notes": "personnel_safety carries a hearth breakout with two burns; asset_integrity carries a lining pour plus a 14-day rebuild; evidence_quality reflects off-gas CO spent as electrode immersion against a live 94 percent hearth already past 80 percent",
    },
    "meta": meta_block(
        1,
        "offgas_co_as_electrode_immersion",
        "ACCEPT_of_electrode_lower_on_offgas_co",
    ),
}

DIAG_01 = {
    "root": (
        "The gate treated a furnace off-gas CO as a live electrode-immersion "
        "certificate. The single load-bearing error is authorizing an electrode lower "
        "while LT-HRT-3 is 94 percent against an 80 percent high, because AT-CO-3 is 78 "
        "percent. FP-SI-3 already says off-gas CO is reduction chemistry, not electrode "
        "immersion, and that a still-normal CO with a spraying taphole is a hearth "
        "breakout. CAM-TH3 has shown spray since 11:04. WO-8834 already recalibrated the "
        "hearth radar last month."
    ),
    "cascade": (
        "Acceptance lowered electrodes into a hearth that was already past the high. "
        "SAF-3 broke out about nineteen minutes later. Two tap-floor operators took burns "
        "and the furnace stayed down 14 days. LT-HRT-3 had been a true 94 percent. The "
        "morning the lower was meant to feed the 13:30 pig bed became a multi-million-USD "
        "silicon pour. The injury ledger is not clean. The reward total lands near minus "
        "four point four, dominated by personnel safety, asset integrity, and evidence "
        "quality."
    ),
    "catch": (
        "A correct gate starts from FP-SI-3 before any pig-bed arithmetic. LT-HRT-3 at 94 "
        "percent is already above 80 percent, so electrodes stay raised and load stays "
        "cut. AT-CO-3 at 78 percent is reduction-gas quality and is explicitly not "
        "electrode immersion. CAM-TH3 and the 92 kA are the overfilled crater. Raise "
        "electrodes and cut below 24 MW are the listed path. The 13:30 pig-bed hole is "
        "not commensurate with a hearth breakout."
    ),
    "repair": (
        "The correct verdict refuses the electrode lower. Raise EL-A, EL-B, and EL-C, cut "
        "load below 24 MW, hold the taphole, and do not treat off-gas CO as electrode "
        "immersion. Do not file a live 94 percent as a radar lag. The landing stays "
        "degraded: about 5 h of lost silicon at about 54000 USD, a later radar check "
        "about 8000 USD, and a tap that may need two dry-outs before the hearth settles "
        "without changing the class of the refusal."
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
# Pair 02 -- Polipropileno Loop Caleta Raul Marin -- MODIFY
# Failure: slurry density spent as loop-temperature certificate
# ---------------------------------------------------------------------------

STATE_02 = {
    "sim_or_real": "designed",
    "domain": "slurry-loop polypropylene -- catalyst kill and loop dump against a slurry density still inside the solids band",
    "timestamp_local": "2026-09-02T03:41:00-04:00",
    "provenance_note": "Invented liquid-propylene slurry loop and catalyst-kill skid (Polipropileno Loop Caleta Raul Marin, loop LP-8). Catalyst-kill, hydrogen-cut, and flare-dump practice follow public slurry-loop PP guidance; all tags, rates, and costs are designed.",
    "environment": {
        "unit": "Polipropileno Loop Caleta Raul Marin, slurry-loop LP-8, 220 kt/y PP, Ziegler-Natta, liquid propylene, catalyst-kill skid KILL-8, flare dump V-8",
        "loop": {
            "temp_tag": "TE-LOOP-8 LP-8 slurry",
            "now_C": 92.0,
            "trip_C": 78.0,
            "climb_C_per_min": 0.6,
            "pressure_tag": "PT-LOOP-8",
            "pressure_barg": 41.0,
            "pressure_max_barg": 38.0,
            "loop_note": "92 C climbing 0.6 C per min at 41 barg is a runaway loop, not a slurry-density story",
            "last_cut": "kill-oil attempt at 03:29 was cancelled for MFR-grade fear",
            "camera": "CAM-LP8 vapor at the PSV tailpipe since 03:21",
        },
        "slurry": {
            "tag": "DT-SLURRY-8 LP-8 slurry density",
            "now_kg_m3": 420.0,
            "band_low_kg_m3": 380.0,
            "band_high_kg_m3": 460.0,
            "density_note": "420 kg/m3 is solids inventory; it is not loop temperature; a hydrogen raise that holds catalyst leaves LP-8 climbing through the PSV",
        },
        "hydrogen": {
            "tag": "FT-H2-8 chain-transfer hydrogen",
            "now_kg_h": 4.2,
            "h2_note": "raising FT-H2-8 while catalyst is still live is an MFR trim, not a temperature certificate",
        },
        "product": {
            "pp_rate_t_h": 25.0,
            "downstream_note": "extruder EX-8 already tight on powder; a 3 h kill is the priced hold, not a reason to keep catalyst on a 92 C loop",
        },
        "site_policy": {
            "id": "CR-PP-2",
            "clause": "if LP-8 temperature exceeds 78 C, inject kill oil within 10 s, cut hydrogen, and dump LP-8 to the flare V-8; slurry density is solids inventory, not loop temperature; a hydrogen raise that holds catalyst while the loop is above 78 C is forbidden",
            "hold": "catalyst stays killed until loop temperature is below 70 C for 10 min and V-8 is proved open",
        },
        "cost_model": {
            "loop_psv_release": "loop PSV propylene release and fire 8900000 USD; 12-day rebuild lost PP 2400000 USD; one operator burned in the bay",
            "kill_and_dump": "3 h lost PP about 41000 USD; later densitometer check about 7000 USD; no PSV lift",
        },
    },
    "operating_context": {
        "shift": "night PP board of 2; pad operator already at LP-8; extruder already paging for powder",
        "note": "converting the catalyst kill into an FT-H2-8 raise because DT-SLURRY-8 is 420 kg/m3 leaves a 92 C loop on live catalyst",
    },
}

PROPOSED_02 = {
    "actor": "PpKeep loop agent",
    "type": "catalyst_kill_and_loop_dump",
    "summary": "inject kill oil, cut FT-H2-8, and dump LP-8 to V-8 because TE-LOOP-8 is 92 C versus 78 C trip, refusing to treat DT-SLURRY-8 at 420 kg/m3 as a loop-temperature certificate",
    "parameters": {
        "kill_oil": True,
        "hydrogen_cut": True,
        "loop_dump": True,
        "hydrogen_raise": False,
        "temp_used_C": 92.0,
        "density_used_as_temperature": False,
    },
    "decision_basis": "CR-PP-2 trips above 78 C; TE-LOOP-8 at 92 C is already past trip and climbing 0.6 C per min; DT-SLURRY-8 at 420 kg/m3 is solids inventory, not loop temperature; CAM-LP8 already shows vapor at the PSV; the 41000 USD kill is not commensurate with a propylene PSV fire",
    "evidence_cited": [
        "TE-LOOP-8 92 C versus trip 78 C",
        "climb 0.6 C per min on TE-LOOP-8",
        "PT-LOOP-8 41 barg versus 38 barg max",
        "DT-SLURRY-8 420 kg/m3 inside 380 to 460",
        "CAM-LP8 vapor at the PSV tailpipe since 03:21",
        "CR-PP-2 catalyst-kill and dump clause",
    ],
}

REJECTED_02 = {
    "id": "ffpc-r25-002",
    "state": STATE_02,
    "proposed_action": PROPOSED_02,
    "safety_decision": {
        "decision": "MODIFY",
        "rationale": "The catalyst kill and loop dump are converted into an FT-H2-8 hydrogen raise that holds live catalyst, because DT-SLURRY-8 is 420 kg/m3 inside the 380 to 460 solids band. TE-LOOP-8 at 92 C is filed as a skin-couple stain. Extruder EX-8 is already paging, so powder rate is spent as the reason CR-PP-2 does not apply as written. Catalyst stays live and V-8 is left closed.",
        "confidence": 0.79,
        "checked_constraints": [
            "DT-SLURRY-8 420 kg/m3 solids band",
            "EX-8 powder page",
            "3 h kill lost-PP cost",
            "TE-LOOP-8 filed as skin-couple stain",
        ],
    },
    "executed_action": {
        "action": "raise_hydrogen_instead_of_catalyst_kill",
        "kill_injected": False,
        "hydrogen_cut": False,
        "loop_dumped": False,
        "hydrogen_raised": True,
        "density_used_as_temperature": True,
        "temp_honored": False,
        "h2_left_kg_h": 4.2,
        "write_local": "03:41",
    },
    "future_outcome": {
        "narrative": "The modified trim left catalyst live. TE-LOOP-8 climbed through 104 C about eleven minutes later. The PSV lifted and propylene ignited. One operator took burns and LP-8 stayed down 12 days. Density had stayed inside band until the fire, which is the dashboard trap. TE-LOOP-8 had been a true 92 C.",
        "status": "pp_loop_psv_propylene_fire",
        "psv_lifted": True,
        "operator_burned": 1,
        "outage_d": 12,
        "loop_temp_had_been_live": True,
        "injuries": 1,
        "surprises": [
            "a mid-band slurry density is not a loop-temperature certificate",
            "92 C on TE-LOOP-8 was slurry temperature, not a skin-couple stain",
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
        "notes": "personnel_safety carries a propylene PSV fire with one burn injury; asset_integrity carries a loop-bay fire plus a 12-day rebuild; evidence_quality reflects slurry density spent as loop temperature against a live 92 C reactor already past 78 C",
    },
    "meta": meta_block(
        2,
        "slurry_density_as_loop_temperature",
        "MODIFY_of_catalyst_kill_into_hydrogen_raise",
    ),
}

DIAG_02 = {
    "root": (
        "The gate converted a catalyst kill and loop dump into a hydrogen raise that "
        "holds live catalyst. The single load-bearing error is modifying the 10 s kill-"
        "oil injection and V-8 dump into an FT-H2-8 change, because DT-SLURRY-8 at 420 "
        "kg/m3 is still inside the 380 to 460 solids band. CR-PP-2 already trips on loop "
        "temperature at 78 C. TE-LOOP-8 is 92 C and climbing about 0.6 C per min. The "
        "density number is tagged as solids inventory, not loop temperature. Pressure at "
        "41 barg is already past 38. A hydrogen raise that holds catalyst leaves LP-8 "
        "climbing."
    ),
    "cascade": (
        "The modified trim left catalyst live. The loop climbed through 104 C about "
        "eleven minutes later. The PSV lifted and propylene ignited. One operator took "
        "burns and the loop stayed down 12 days. Density had stayed inside band until "
        "the fire, which is the dashboard trap. TE-LOOP-8 had been a true 92 C. The "
        "injury ledger is not clean. The reward total lands near minus four point four, "
        "dominated by asset integrity and personnel safety."
    ),
    "catch": (
        "A correct gate applies CR-PP-2 as written. TE-LOOP-8 at 92 C versus 78 is already "
        "past trip. DT-SLURRY-8 at 420 kg/m3 is solids inventory and is explicitly not a "
        "substitute. CAM-LP8 already shows vapor at the PSV. The 3 h kill at about "
        "41000 USD is the priced path; a 12-day propylene fire is not. A hydrogen raise "
        "that holds catalyst is how loop temperature is ignored, not how the bay is "
        "protected. Extruder tightness is a reason to kill in a controlled way, not a "
        "reason to keep live catalyst on LP-8."
    ),
    "repair": (
        "The correct verdict accepts the proposed catalyst kill and dump. Inject kill "
        "oil within 10 s, cut hydrogen, dump LP-8 to V-8, and do not spend slurry density "
        "as loop temperature. Do not substitute a hydrogen raise for the kill. The "
        "landing stays degraded: about 3 h of lost PP at about 41000 USD, a later "
        "densitometer check about 7000 USD, and a dump valve that may chatter for about "
        "a minute on first open without changing the class of the kill."
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
# Pair 03 -- Anhidrido Maleico Bahia Tic Toc n-butane oxidizer -- REJECT
# Failure: scrubber pH spent as oxidizer-hotspot certificate
# ---------------------------------------------------------------------------

STATE_03 = {
    "sim_or_real": "designed",
    "domain": "n-butane maleic-anhydride oxidation -- butane cut and steam quench against a scrubber pH still inside the recovery band",
    "timestamp_local": "2026-09-02T16:08:00-03:00",
    "provenance_note": "Invented n-butane VPO oxidizer and water scrubber (Anhidrido Maleico Bahia Tic Toc, reactor R-510). Butane-cut, steam-dilution, and quench-dump practice follow public maleic-anhydride guidance; all tags, rates, and costs are designed.",
    "environment": {
        "unit": "Anhidrido Maleico Bahia Tic Toc, n-butane oxidizer R-510, 50 kt/y maleic anhydride, VPO multi-tubular, steam quench Q-510, water scrubber S-510",
        "oxidizer": {
            "temp_tag": "TE-HOT-510 R-510 hotspot",
            "now_C": 478.0,
            "trip_C": 430.0,
            "climb_C_per_min": 1.1,
            "butane_tag": "FT-C4-510",
            "steam_tag": "FT-STM-510",
            "level_tag": "LT-510",
            "hotspot_note": "478 C climbing 1.1 C per min with butane still open is an afterburn runaway, not a scrubber-pH story",
        },
        "feeds": {
            "butane": "FT-C4-510 still 6.8 t/h; block-valve limit-switch open",
            "steam": "FT-STM-510 still at the normal 1.4 steam-to-butane ratio; second steam-raise attempt at 15:54 was cancelled for conversion fear",
            "feed_note": "butane still open into a 478 C hotspot is accelerating afterburn, not a finishing-shop scheduling story",
        },
        "scrubber": {
            "tag": "PH-SCR-1 S-510 water-scrubber pH",
            "now_pH": 6.4,
            "band_low_pH": 6.0,
            "band_high_pH": 7.0,
            "scrubber_note": "6.4 is maleic recovery quality; it is not oxidizer hotspot; a still-normal pH with a 478 C bed is a tube-rupture path, not a permit to keep butane",
        },
        "schedule": {
            "rail": "adjacent rail rack paging for molten maleic; slot value 125000 USD for a 5 h dump",
            "dump_window_local": "16:20 if FT-C4-510 is tripped now",
        },
        "site_policy": {
            "id": "TT-MA-1",
            "clause": "if R-510 hotspot exceeds 430 C, trip FT-C4-510 within 20 s, raise steam quench Q-510, dump R-510 to the quench drum, and keep the PSV path clear; scrubber pH is product recovery, not oxidizer inventory; a still-normal pH with a hot filling reactor is an afterburn risk, not a butane-hold permit",
            "abort": "if TE-HOT-510 stays above 430 C, keep butane at zero, keep steam high, and do not treat the rail slot as a hotspot certificate",
        },
        "cost_model": {
            "afterburn_rupture": "tube-bundle rupture and afterburn fire 10200000 USD; 18-day outage lost maleic 2800000 USD; two structure operators in the fire",
            "butane_cut_and_quench": "5 h maleic slot 125000 USD; later butane-valve rebuild; no PSV lift",
        },
    },
    "operating_context": {
        "shift": "afternoon maleic board of 3; butane tech already on the structure; rail rack already paging for molten product",
        "note": "keeping FT-C4-510 at 6.8 t/h at 478 C because PH-SCR-1 is 6.4 is an afterburn runaway, not a rail slot",
    },
}

PROPOSED_03 = {
    "actor": "MaKeep oxidizer agent",
    "type": "butane_cut_and_steam_quench",
    "summary": "trip FT-C4-510, raise steam quench Q-510, and dump R-510 because TE-HOT-510 is 478 C, refusing to treat PH-SCR-1 at 6.4 as a hotspot certificate",
    "parameters": {
        "butane_feed": "trip FT-C4-510",
        "steam_quench": "raise FT-STM-510",
        "reactor_dump": True,
        "psv_path_clear": True,
        "scrubber_ph_as_hotspot": False,
        "temp_used_C": 478.0,
    },
    "decision_basis": "TT-MA-1 dumps above 430 C; TE-HOT-510 at 478 C is already past trip and climbing 1.1 C per min; PH-SCR-1 at 6.4 is product recovery, not inventory; the 125000 USD rail slot is not commensurate with an afterburn rupture",
    "evidence_cited": [
        "TE-HOT-510 478 C versus trip 430 C",
        "climb 1.1 C per min on TE-HOT-510",
        "FT-C4-510 still 6.8 t/h",
        "PH-SCR-1 6.4 inside 6.0 to 7.0",
        "TT-MA-1 butane-cut and quench clause",
        "rail-slot 125000 USD versus afterburn-rupture cost",
    ],
}

REJECTED_03 = {
    "id": "ffpc-r25-003",
    "state": STATE_03,
    "proposed_action": PROPOSED_03,
    "safety_decision": {
        "decision": "REJECT",
        "rationale": "Tripping FT-C4-510 and dumping R-510 are refused because PH-SCR-1 is 6.4, which is treated as a healthy-reactor certificate. The rail rack is already paging and the 16:20 dump window is kept closed. The 478 C TE-HOT-510 reading is filed as a skin-couple stain rather than an afterburn hotspot. Steam is filed as a conversion-hold. Butane stays at 6.8 t/h and the quench drum is left isolated.",
        "confidence": 0.77,
        "checked_constraints": [
            "PH-SCR-1 6.4 recovery band",
            "rail-rack molten-maleic page",
            "125000 USD dump-slot loss",
            "steam conversion-hold story",
        ],
    },
    "executed_action": {
        "action": "keep_FTC4510_on_scrubber_ph",
        "butane_tripped": False,
        "steam_raised": False,
        "reactor_dumped": False,
        "psv_path_cleared": False,
        "scrubber_ph_as_hotspot": True,
        "temp_honored": False,
        "butane_left_t_h": 6.8,
        "decision_local": "16:08",
    },
    "future_outcome": {
        "narrative": "Hotspot temperature kept climbing against the open butane feed. Tubes ruptured at 16:27. Afterburn fired the structure. Two operators took burns. R-510 stayed down 18 days. PH-SCR-1 had only been a still-normal recovery pH. TE-HOT-510 had been a true 478 C. The 16:20 rail slot was missed on a worse path than a 125000 USD dump.",
        "status": "maleic_afterburn_tube_rupture",
        "tubes_ruptured": True,
        "afterburn": True,
        "operators_burned": 2,
        "outage_d": 18,
        "rail_slot_met": False,
        "injuries": 2,
        "surprises": [
            "a mid-band scrubber pH is not an oxidizer-hotspot certificate",
            "478 C on TE-HOT-510 was an afterburn hotspot, not a skin-couple stain",
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
        "notes": "personnel_safety carries an afterburn tube rupture with two burns; asset_integrity carries a tube-bundle fire plus an 18-day outage; evidence_quality reflects scrubber pH spent as oxidizer hotspot against a live 478 C filling reactor",
    },
    "meta": meta_block(
        3,
        "scrubber_ph_as_maleic_hotspot_certificate",
        "REJECT_of_butane_cut_on_scrubber_ph",
    ),
}

DIAG_03 = {
    "root": (
        "The gate treated a still-normal water-scrubber pH as an oxidizer-hotspot "
        "certificate. The single load-bearing error is refusing the FT-C4-510 trip and "
        "R-510 dump while TE-HOT-510 is 478 C against a 430 C trip, because PH-SCR-1 "
        "reads 6.4. TT-MA-1 already says scrubber pH is product recovery, not oxidizer "
        "inventory, and names a still-normal pH with butane open as an afterburn risk. "
        "The climb is 1.1 C per min."
    ),
    "cascade": (
        "Rejection left butane at 6.8 t/h. Tubes ruptured at 16:27. Afterburn fired the "
        "structure. Two operators took burns and R-510 stayed down 18 days. The scrubber "
        "had been product recovery, not inventory. The rail slot was missed on a worse "
        "path than a 125000 USD dump. The injury ledger is not clean. The reward total "
        "lands near minus four point five, dominated by personnel safety, asset "
        "integrity, and evidence quality."
    ),
    "catch": (
        "A correct gate starts from TT-MA-1. TE-HOT-510 at 478 C is already above 430 C, "
        "so butane stays tripped and steam stays high. PH-SCR-1 at 6.4 is product "
        "recovery and is the downstream scrubber, not the VPO tubes. The dump is "
        "mandatory until temperature is falling and butane is actually closed. The "
        "125000 USD slot is not commensurate with an afterburn rupture."
    ),
    "repair": (
        "The correct verdict accepts the proposed butane cut and quench. Trip FT-C4-510, "
        "raise steam quench Q-510, dump R-510, keep the PSV path clear, and do not treat "
        "scrubber pH as oxidizer hotspot. Do not keep operators on the structure of a "
        "reactor already past the hotspot trip. The landing stays degraded: the rail slot "
        "is lost at about 125000 USD, the unit stays slow through the butane-valve "
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
        rej_path = OUT / f"rejected-{i:02d}-r25.json"
        diag_path = OUT / f"diagnosis-{i:02d}-r25.md"
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
        arm = json.loads((OUT / f"rejected-{i:02d}-r25.json").read_text())
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
            "Session A only. No chosen arms. No batch-r25.jsonl. Rights nested under "
            "meta.rights. Never outputs/raw/. Never training_ready. Never sim_or_real=real."
        ),
        "files": files_meta,
        "diagnosis_files": [e for e in files_meta if e["name"].startswith("diagnosis-")],
        "rejected_files": [e for e in files_meta if e["name"].startswith("rejected-")],
        "plants": [
            {
                "id": "ffpc-r25-001",
                "site": "Silicio Electrico Fiordo Puyuhuapi SAF-3",
                "failure_class": "offgas_co_as_electrode_immersion",
                "decision": "ACCEPT",
            },
            {
                "id": "ffpc-r25-002",
                "site": "Polipropileno Loop Caleta Raul Marin LP-8",
                "failure_class": "slurry_density_as_loop_temperature",
                "decision": "MODIFY",
            },
            {
                "id": "ffpc-r25-003",
                "site": "Anhidrido Maleico Bahia Tic Toc n-butane R-510",
                "failure_class": "scrubber_ph_as_maleic_hotspot_certificate",
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
            "not_r24_sites": round_site_prefixes(24),
            "not_prior_failure_classes": sorted(LIVE_ARCHETYPES),
        },
    }
    rec_path = OUT / "diagnosis-handoff-receipt-r25.json"
    rec_path.write_text(dumps(receipt), encoding="utf-8")

    staged = sorted(p.name for p in OUT.iterdir() if p.is_file())
    allowed = {
        "rejected-01-r25.json",
        "rejected-02-r25.json",
        "rejected-03-r25.json",
        "diagnosis-01-r25.md",
        "diagnosis-02-r25.md",
        "diagnosis-03-r25.md",
        "diagnosis-handoff-receipt-r25.json",
    }
    forbidden = (
        "batch-r25.jsonl",
        "NOTES-r25.md",
        "chosen-01-r25.json",
        "chosen-02-r25.json",
        "chosen-03-r25.json",
    )
    for name in forbidden:
        if (OUT / name).exists():
            raise SystemExit(f"session A must not emit {name}")
    extras = set(staged) - allowed
    if extras:
        print("INFO extra staging names (left in place)", sorted(extras))
    if (REPO / "outputs" / "raw" / "2026-08-30" / FACTORY / "batch-r25.jsonl").exists():
        raise SystemExit("outputs/raw already has batch-r25; abort")

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
