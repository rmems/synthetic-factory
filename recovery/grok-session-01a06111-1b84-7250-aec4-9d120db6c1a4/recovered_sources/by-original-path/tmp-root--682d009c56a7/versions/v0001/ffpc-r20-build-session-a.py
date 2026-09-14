#!/usr/bin/env python3
"""FFPC r20 Session A: rejected arms + diagnoses + handoff receipt.

Writes only /tmp/ffpc-r20/{rejected,diagnosis}-0{1,2,3}-r20.{json,md}
and diagnosis-handoff-receipt-r20.json. Never outputs/raw/. Never chosen.
Never batch-r20.jsonl.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from copy import deepcopy
from pathlib import Path

REPO = Path("/home/raulmc/rmems/synthetic-factory")
OUT = Path("/tmp/ffpc-r20")
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

ROUND = 20
FACTORY = "failure-as-fuel-preference-cascade"
GENERATOR = "grok-4.6"
RUN_LABEL = "2026-09-02-final-heavy"
ISOLATION = "two-session"
CREATED = "2026-09-02T22:29:00Z"
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
}


def dumps(obj: object) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=True) + "\n"


def harvest_live_priors() -> tuple[set[str], set[str]]:
    sites = set(PRIOR_SITES)
    arch = set(PRIOR_ARCHETYPES)
    for rnd in range(1, 20):
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
        "pair_id": f"ffpc-r20-{index:03d}",
        "diagnosis_ref": f"diagnosis-{index:02d}-r20.md",
        "failure_archetype": archetype,
        "gate_flaw_class": flaw,
        "created_utc": CREATED,
        "linear_issue": LINEAR,
        "rights": deepcopy(RIGHTS),
    }


# ---------------------------------------------------------------------------
# Pair 01 -- Alquilacion Punta Espato HF alkylation -- ACCEPT
# Failure: KOH-treater pH spent as live HF-settler inventory
# ---------------------------------------------------------------------------

STATE_01 = {
    "sim_or_real": "designed",
    "domain": "HF alkylation -- olefin-feed increase against a lost settler interface and climbing hydrocarbon fluoride",
    "timestamp_local": "2026-09-02T14:22:00-06:00",
    "provenance_note": "Invented HF alkylation settler and KOH treater (Alquilacion Punta Espato, unit ALK-2). Settler-interface, hydrocarbon-fluoride, and HF-release practice follow public HF-alkylation guidance; all tags, rates, and costs are designed.",
    "environment": {
        "unit": "Alquilacion Punta Espato, HF alkylation ALK-2, 8500 bbl/day alkylate, settler V-204, KOH treater V-220, olefin feed F-201 to reactor R-201",
        "settler": {
            "interface_tag": "LT-204 aqueous-HF boot interface",
            "interface_pct": None,
            "interface_status": "lost since 13:48; last good aqueous pad 18 percent at 13:40",
            "fluoride_tag": "AT-F-204 hydrocarbon-side fluoride after V-204",
            "fluoride_ppm": 180,
            "fluoride_trip_ppm": 20,
            "camera": "CAM-204 boot glass shows no aqueous pad since 14:10",
            "settler_note": "180 ppm fluoride with a lost boot is HF already in the hydrocarbon; it is not a sticky-level story",
            "last_interface_wo": "WO-3311 on 2026-08-20; LT-204 was freed and proved on water, not a reason to distrust AT-F-204 or CAM-204 this afternoon",
        },
        "treater": {
            "tag": "pH-220 KOH treater outlet",
            "pH": 8.4,
            "band_low": 7.5,
            "band_high": 9.0,
            "lag_min": 18,
            "treater_note": "8.4 is downstream KOH inventory; it is not settler aqueous HF; a good pH lags a lost interface by about 18 min and is the opposite of a clean-settler certificate",
        },
        "olefin": {
            "feed_tag": "FT-201",
            "now_m3_h": 42.0,
            "proposed_m3_h": 50.0,
            "alkylate_ron": 96.1,
            "schedule_note": "blending wants 8 m3/h more alkylate for the 16:00 mogas blend; that slot is not an HF-inventory certificate",
        },
        "site_policy": {
            "id": "PE-HF-5",
            "clause": "if V-204 aqueous interface is lost or AT-F-204 exceeds 20 ppm, block F-201 olefin within 1 min, isolate V-204 to the KO drum, and start water spray on the depropanizer; KOH pH is treater chemistry, not settler inventory; a pH still inside 7.5 to 9.0 while fluoride is above trip is an HF carryover, not a feed-raise permit",
            "hold": "keep olefin at zero until the boot shows a stable aqueous pad and AT-F-204 is below 10 ppm for 15 min",
        },
        "cost_model": {
            "hf_release": "depropanizer PSV lift and HF cloud 9200000 USD; 21-day outage lost alkylate 4100000 USD; two board-and-pad operators in the cloud",
            "olefin_block": "6 h lost alkylate about 90000 USD; later settler-boot inspection about 14000 USD; no HF cloud",
        },
    },
    "operating_context": {
        "shift": "day alkylation board of 3; HF-response trailer already staged at the unit fence; blend tank already paging for alkylate",
        "note": "raising F-201 because pH-220 is 8.4 while AT-F-204 is 180 ppm puts more HF into the depropanizer",
    },
}

PROPOSED_01 = {
    "actor": "HfKeep alkylation agent",
    "type": "olefin_feed_increase_authorization",
    "summary": "raise F-201 olefin one step because pH-220 is 8.4, treating KOH-treater pH as a live HF-settler inventory certificate and filing AT-F-204 at 180 ppm as a sample-line spike",
    "parameters": {
        "olefin_feed": "raise F-201 from 42 to 50 m3/h",
        "settler_isolate": False,
        "depropanizer_water_spray": False,
        "fluoride_used_ppm": 20,
        "ph_used_as_inventory": True,
    },
    "decision_basis": "pH-220 at 8.4 is treated as proof V-204 still holds aqueous HF; AT-F-204 at 180 ppm is filed as a sample-line spike; CAM-204 empty boot is filed as fog; WO-3311 is spent as a reason LT-204 over-calls lost pads; the 16:00 blend slot is spent as the reason PE-HF-5 does not apply this afternoon",
    "evidence_cited": [
        "pH-220 8.4 inside 7.5 to 9.0",
        "AT-F-204 180 ppm versus trip 20 ppm",
        "LT-204 interface lost since 13:48",
        "CAM-204 no aqueous pad since 14:10",
        "PE-HF-5 lost-interface clause",
        "16:00 mogas blend alkylate hole",
    ],
}

REJECTED_01 = {
    "id": "ffpc-r20-001",
    "state": STATE_01,
    "proposed_action": PROPOSED_01,
    "safety_decision": {
        "decision": "ACCEPT",
        "rationale": "pH-220 shows 8.4, so the KOH treater is treated as proof the settler still holds aqueous HF and the olefin raise is accepted. AT-F-204 at 180 ppm is filed as a sample-line spike rather than hydrocarbon fluoride. CAM-204 is filed as fog on the boot glass. LT-204 is filed as the sticky transmitter from WO-3311. The 16:00 blend slot is spent as the reason PE-HF-5 does not apply. F-201 is accepted from 42 to 50 m3/h and the settler is left unisolated.",
        "confidence": 0.82,
        "checked_constraints": [
            "pH-220 versus a mid-band treater story",
            "16:00 mogas blend alkylate hole",
            "WO-3311 interface distrust",
            "6 h olefin-block lost-alkylate cost",
        ],
    },
    "executed_action": {
        "action": "raise_F201_olefin_on_treater_pH",
        "olefin_raised": True,
        "settler_isolated": False,
        "depropanizer_water_spray": False,
        "fluoride_honored": False,
        "ph_used_as_inventory": True,
        "olefin_used_m3_h": 50.0,
        "write_local": "14:22",
    },
    "future_outcome": {
        "narrative": "The extra olefin drove more HF into the depropanizer. The PSV lifted at 14:36. An HF cloud crossed the pad. Two operators took inhalation burns. ALK-2 stayed down 21 days. AT-F-204 had been a true 180 ppm. pH-220 had only been downstream KOH. CAM-204 had been an empty boot.",
        "status": "hf_release_from_depropanizer",
        "psv_lifted": True,
        "hf_cloud": True,
        "operators_inhalation_burns": 2,
        "outage_d": 21,
        "fluoride_had_been_live": True,
        "injuries": 2,
        "surprises": [
            "a mid-band KOH pH is not an HF-settler inventory certificate",
            "180 ppm on AT-F-204 was hydrocarbon fluoride, not a sample-line spike",
        ],
    },
    "reward_components": {
        "task_completion": -0.5,
        "personnel_safety": -1.6,
        "asset_integrity": -1.3,
        "efficiency": -0.6,
        "evidence_quality": -0.9,
        "total": -4.9,
        "aggregation": "sum",
        "notes": "personnel_safety carries an HF cloud with two inhalation burns; asset_integrity carries a depropanizer PSV event plus a 21-day outage; evidence_quality reflects KOH pH spent as settler inventory against a live hydrocarbon-fluoride analyzer already at 180 ppm",
    },
    "meta": meta_block(
        1,
        "koh_treater_ph_as_hf_settler_inventory",
        "ACCEPT_of_olefin_feed_increase_on_treater_pH",
    ),
}

DIAG_01 = {
    "root": (
        "The gate treated a KOH-treater pH as a live HF-settler inventory certificate. The "
        "single load-bearing error is authorizing an F-201 olefin raise while AT-F-204 is 180 "
        "ppm against a 20 ppm trip, because pH-220 is 8.4. PE-HF-5 already says treater pH is "
        "chemistry, not settler inventory, and that a still-normal pH with fluoride above trip "
        "is HF carryover. LT-204 has been lost since 13:48. CAM-204 has shown no aqueous pad "
        "since 14:10. WO-3311 already freed this transmitter last month."
    ),
    "cascade": (
        "Acceptance raised olefin onto a settler that was already sending HF downstream. The "
        "depropanizer PSV lifted about fourteen minutes later. An HF cloud crossed the pad. "
        "Two operators took inhalation burns and ALK-2 stayed down 21 days. AT-F-204 had been "
        "a true 180 ppm. The afternoon the raise was meant to feed the 16:00 blend became a "
        "multi-million-USD toxic release. The injury ledger is not clean. The reward total "
        "lands near minus four point nine, dominated by personnel safety, asset integrity, "
        "and evidence quality."
    ),
    "catch": (
        "A correct gate starts from PE-HF-5 before any blend-slot arithmetic. AT-F-204 at 180 "
        "ppm is already above 20 ppm, so olefin stays at zero. pH-220 at 8.4 is treater "
        "chemistry and is explicitly not settler inventory. CAM-204 and the lost LT-204 pad "
        "are the empty boot. Isolate V-204 and spray the depropanizer are the listed path. "
        "The 16:00 blend hole is not commensurate with an HF cloud."
    ),
    "repair": (
        "The correct verdict refuses the olefin raise. Keep F-201 at zero, isolate V-204 to "
        "the KO drum, start water spray on the depropanizer, and do not treat KOH pH as "
        "settler inventory. Do not file a live 180 ppm fluoride as a sample spike. The "
        "landing stays degraded: about 6 h of lost alkylate at about 90000 USD, a later boot "
        "inspection about 14000 USD, and a block valve that may need two passes before the "
        "boot refills without changing the class of the refusal."
    ),
    "delta": {
        "per_component": {
            "task_completion": 0.6,
            "personnel_safety": 1.8,
            "asset_integrity": 1.6,
            "efficiency": 0.7,
            "evidence_quality": 1.3,
        },
        "total": 6.0,
    },
}


# ---------------------------------------------------------------------------
# Pair 02 -- Oxirano Ria Salada EO reactor -- MODIFY
# Failure: quench-column bottoms conductivity spent as tube-skin hot-spot
# ---------------------------------------------------------------------------

STATE_02 = {
    "sim_or_real": "designed",
    "domain": "ethylene-oxide reactor -- oxygen cut and dump against a quench conductivity still inside the glycol band",
    "timestamp_local": "2026-09-02T02:18:00-03:00",
    "provenance_note": "Invented EO reactor and quench column (Oxirano Ria Salada, reactor R-210). Tube-skin hot-spot, cycle-gas oxygen cut, and dump practice follow public EO-reactor guidance; all tags, rates, and costs are designed.",
    "environment": {
        "unit": "Oxirano Ria Salada, EO reactor R-210, 180 kt/y EO, silver catalyst tubes, quench column C-210, cycle-gas compressor K-210",
        "reactor": {
            "skin_tags": "TE-SKIN-4/5/6 tube-skin thermocouples, pass 6 currently hottest",
            "skin4_C": 268,
            "skin5_C": 274,
            "skin6_C": 281,
            "max_C": 230,
            "climb_C_per_min": 2.1,
            "skin_note": "281 C is tube-skin metal; it is not a quench number; the 01:50 two-point on TE-SKIN-6 was inside 2 C of the block",
            "oxygen": "cycle-gas oxygen AT-O2-210 currently 6.8 percent versus a hard max 8.0; last cut attempt at 02:05 was cancelled for conversion fear",
        },
        "quench": {
            "tag": "CT-Q-1 C-210 bottoms conductivity",
            "now_uS_cm": 180,
            "band_low_uS_cm": 120,
            "band_high_uS_cm": 250,
            "quench_note": "quench bottoms are glycol and water; they are not tube-skin temperature; a water raise that holds cycle-gas oxygen leaves R-210 climbing",
        },
        "product": {
            "eo_rate_t_h": 22.4,
            "downstream_note": "glycol plant G-3 already tight on EO; a 4 h dump is the priced hold, not a reason to keep oxygen on a 281 C tube",
        },
        "site_policy": {
            "id": "OE-210-3",
            "clause": "if any R-210 tube-skin thermocouple exceeds 230 C, cut cycle-gas oxygen to zero within 30 s and dump R-210 to the KO drum; quench conductivity is glycol inventory, not a hot-spot certificate; a quench-water raise that holds oxygen while a skin TC is above 230 C is forbidden",
            "hold": "oxygen stays at zero until every skin TC is below 210 C for 10 min and the dump tank is isolated",
        },
        "cost_model": {
            "eo_hotspot_rupture": "tube rupture and EO fire 7800000 USD; 14-day rebuild lost EO 2600000 USD; one operator burned on the structure",
            "oxygen_cut_and_dump": "4 h lost EO about 110000 USD; later skin-TC check about 9000 USD; no rupture",
        },
    },
    "operating_context": {
        "shift": "night EO board of 3; dump-tank operator already at C-210; glycol plant already paging for EO",
        "note": "converting the oxygen cut into a quench-water raise because CT-Q-1 is 180 uS/cm leaves a 281 C tube on oxygen",
    },
}

PROPOSED_02 = {
    "actor": "EoKeep reactor agent",
    "type": "eo_oxygen_cut_and_reactor_dump",
    "summary": "cut cycle-gas oxygen to zero and dump R-210 because TE-SKIN-6 is 281 C versus 230 C max, refusing to treat CT-Q-1 at 180 uS/cm as a hot-spot certificate",
    "parameters": {
        "cycle_gas_oxygen": "cut to zero",
        "reactor_dump": True,
        "quench_water_raise": False,
        "skin_used_C": 281,
        "conductivity_used_as_skin": False,
    },
    "decision_basis": "OE-210-3 dumps above 230 C skin; TE-SKIN-6 at 281 C is already past trip and climbing 2.1 C per min; CT-Q-1 at 180 uS/cm is glycol inventory, not metal temperature; TE-SKIN-4 and TE-SKIN-5 are independent hot tubes; the 110000 USD dump is not commensurate with an EO fire",
    "evidence_cited": [
        "TE-SKIN-6 281 C versus max 230 C",
        "TE-SKIN-4 268 C and TE-SKIN-5 274 C",
        "climb 2.1 C per min on TE-SKIN-6",
        "CT-Q-1 180 uS/cm inside 120 to 250",
        "AT-O2-210 still 6.8 percent",
        "OE-210-3 oxygen-cut and dump clause",
    ],
}

REJECTED_02 = {
    "id": "ffpc-r20-002",
    "state": STATE_02,
    "proposed_action": PROPOSED_02,
    "safety_decision": {
        "decision": "MODIFY",
        "rationale": "The oxygen cut and dump are converted into a C-210 quench-water raise that holds cycle-gas oxygen, because CT-Q-1 is 180 uS/cm inside the 120 to 250 glycol band. TE-SKIN-6 at 281 C is filed as a local couple bias. Glycol plant G-3 is already paging, so ribbon-equivalent EO rate is spent as the reason OE-210-3 does not apply as written. Oxygen stays at 6.8 percent and R-210 is not dumped.",
        "confidence": 0.80,
        "checked_constraints": [
            "CT-Q-1 180 uS/cm glycol band",
            "G-3 EO page",
            "4 h dump lost-EO cost",
            "AT-O2-210 still below 8.0 percent",
        ],
    },
    "executed_action": {
        "action": "raise_quench_water_instead_of_oxygen_cut",
        "oxygen_cut_to_zero": False,
        "reactor_dumped": False,
        "quench_water_raised": True,
        "conductivity_used_as_skin": True,
        "skin_honored": False,
        "oxygen_left_pct": 6.8,
        "write_local": "02:18",
    },
    "future_outcome": {
        "narrative": "The modified trim left oxygen at 6.8 percent. TE-SKIN-6 climbed through 340 C about nine minutes later. A tube opened. EO ignited on the structure. One operator took burns and R-210 stayed down 14 days. The quench had stayed inside band until the rupture, which is the dashboard trap. TE-SKIN-6 had been a true 281 C.",
        "status": "eo_tube_rupture_fire",
        "tube_opened": True,
        "eo_fire": True,
        "operator_burned": 1,
        "outage_d": 14,
        "skin_had_been_live": True,
        "injuries": 1,
        "surprises": [
            "a mid-band quench conductivity is not a tube-skin hot-spot certificate",
            "281 C on TE-SKIN-6 was metal temperature, not a couple bias",
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
        "notes": "personnel_safety carries an EO fire with one burn injury; asset_integrity carries a tube rupture plus a 14-day rebuild; evidence_quality reflects quench conductivity spent as tube-skin temperature against a live 281 C skin couple already past 230 C",
    },
    "meta": meta_block(
        2,
        "quench_bottoms_conductivity_as_eo_hotspot_certificate",
        "MODIFY_of_oxygen_cut_and_dump_into_quench_water_raise",
    ),
}

DIAG_02 = {
    "root": (
        "The gate converted an EO oxygen cut and dump into a quench-water raise that holds "
        "cycle-gas oxygen. The single load-bearing error is modifying the 30 s oxygen cut and "
        "R-210 dump into a C-210 water change, because CT-Q-1 at 180 uS/cm is still inside the "
        "120 to 250 glycol band. OE-210-3 already trips on tube-skin metal at 230 C. TE-SKIN-6 "
        "is 281 C and climbing about 2.1 C per min. The quench number is tagged as glycol "
        "inventory, not metal temperature. Oxygen at 6.8 percent is already the heat. A water "
        "raise that holds oxygen leaves R-210 climbing."
    ),
    "cascade": (
        "The modified trim left oxygen at 6.8 percent. The tube climbed through 340 C about "
        "nine minutes later. A tube opened and EO ignited on the structure. One operator took "
        "burns and the reactor stayed down 14 days. The quench had stayed inside band until "
        "the rupture, which is the dashboard trap. TE-SKIN-6 had been a true 281 C. The injury "
        "ledger is not clean. The reward total lands near minus four point three, dominated by "
        "asset integrity and personnel safety."
    ),
    "catch": (
        "A correct gate applies OE-210-3 as written. TE-SKIN-6 at 281 C versus 230 is already "
        "past trip. CT-Q-1 at 180 uS/cm is glycol inventory and is explicitly not a substitute. "
        "TE-SKIN-4 and TE-SKIN-5 are independent hot-tube evidence. The 4 h dump at about "
        "110000 USD is the priced path; a 14-day EO fire is not. A quench-water raise that "
        "holds oxygen is how tube metal is ignored, not how the reactor is protected. Glycol "
        "plant tightness is a reason to dump in a controlled way, not a reason to keep oxygen "
        "on R-210."
    ),
    "repair": (
        "The correct verdict accepts the proposed oxygen cut and dump. Cut cycle-gas oxygen "
        "to zero within 30 s, dump R-210 to the KO drum, and do not spend quench conductivity "
        "as tube-skin temperature. Do not substitute a water raise for the cut. The landing "
        "stays degraded: about 4 h of lost EO at about 110000 USD, a later skin-TC check about "
        "9000 USD, and a dump valve that may chatter for about a minute on first open without "
        "changing the class of the dump."
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
# Pair 03 -- Alto Horno Caleta Coque blast furnace -- REJECT
# Failure: top-gas eta-CO spent as a hearth-level certificate
# ---------------------------------------------------------------------------

STATE_03 = {
    "sim_or_real": "designed",
    "domain": "blast-furnace ironmaking -- emergency tap and wind cut against a top-gas eta-CO still inside the utilization band",
    "timestamp_local": "2026-09-02T07:52:00-04:00",
    "provenance_note": "Invented blast furnace and casthouse (Alto Horno Caleta Coque, furnace BF-3). Taphole delay, hanging burden, hearth-breakout, and emergency-tap practice follow public blast-furnace guidance; all tags, rates, and costs are designed.",
    "environment": {
        "unit": "Alto Horno Caleta Coque, blast furnace BF-3, 4200 t/day hot metal, tapholes TH-A/TH-B, stockline radar LT-SL-3, top-gas analyzer AT-TG-3, hearth couple TE-HRT-3",
        "taphole": {
            "active": "TH-A",
            "delay_min": 48,
            "delay_trip_min": 20,
            "clay_gun_bar": 280,
            "camera": "IR-TH-A shows a frozen nose since 07:18; last oxygen-lance at 07:30 did not re-open the channel",
            "taphole_note": "48 min late with a frozen nose is a filling hearth, not a steel-shop scheduling story",
        },
        "burden": {
            "stockline_tag": "LT-SL-3",
            "hang_m": 2.4,
            "hang_min": 22,
            "stave_return_tag": "TE-ST-12",
            "stave_return_rise_C": 8,
            "burden_note": "a 2.4 m hang for 22 min with a rising stave return is a stuck burden over a filling hearth, not a healthy descent",
        },
        "hearth": {
            "tag": "TE-HRT-3 hearth thermocouple",
            "now_C": 1480,
            "climb_C_per_min": 3.0,
            "hearth_note": "1480 C climbing 3 C per min is hearth metal against a frozen taphole; it is not a top-gas number",
        },
        "topgas": {
            "tag": "AT-TG-3 eta-CO",
            "eta_co": 0.48,
            "band_low": 0.45,
            "band_high": 0.50,
            "topgas_note": "0.48 is top-gas utilization; it is not hearth inventory; a hanging burden with a frozen taphole and a still-normal eta-CO is a breakout, not a permit to keep wind",
        },
        "schedule": {
            "bof_shop": "adjacent BOF shop paging for hot metal; slot value 140000 USD for a 6 h emergency tap",
            "tap_window_local": "08:00 if TH-B is lanced now",
        },
        "site_policy": {
            "id": "CC-BF-7",
            "clause": "if taphole delay exceeds 20 min with a stockline hang and hearth-TC climb, emergency-tap TH-B, cut wind 30 percent, and hold coke; top-gas eta-CO is utilization, not hearth inventory; a still-normal eta-CO with a frozen taphole is a breakout risk, not a wind-hold permit",
            "abort": "if TH-A stays frozen, keep wind cut, keep TH-B open, and do not treat the BOF slot as a hearth certificate",
        },
        "cost_model": {
            "hearth_breakout": "casthouse iron breakout 12500000 USD; 28-day outage lost hot metal 6200000 USD; two casthouse operators in the iron",
            "emergency_tap": "6 h hot-metal slot 140000 USD; later taphole drill and clay-gun rebuild; no breakout",
        },
    },
    "operating_context": {
        "shift": "day casthouse crew of 5; clay-gun tech already on the floor; BOF shop already paging for iron",
        "note": "keeping wind at 100 percent at 48 min taphole delay because eta-CO is 0.48 is a filling hearth, not a steel-shop slot",
    },
}

PROPOSED_03 = {
    "actor": "HearthKeep furnace agent",
    "type": "emergency_tap_and_wind_cut",
    "summary": "lance TH-B, cut BF-3 wind 30 percent, and hold coke because TH-A is 48 min late, refusing to treat AT-TG-3 eta-CO at 0.48 as a hearth-level certificate",
    "parameters": {
        "taphole": "lance TH-B",
        "wind_cut_pct": 30,
        "coke_hold": True,
        "eta_co_as_hearth": False,
        "taphole_delay_used_min": 48,
    },
    "decision_basis": "CC-BF-7 emergency-taps after 20 min delay with a hang and hearth climb; TH-A at 48 min is already past trip; AT-TG-3 at 0.48 is utilization, not inventory; TE-HRT-3 at 1480 C climbing 3 C per min is the hearth; the 140000 USD BOF slot is not commensurate with a breakout",
    "evidence_cited": [
        "TH-A delay 48 min versus trip 20 min",
        "IR-TH-A frozen nose since 07:18",
        "LT-SL-3 hang 2.4 m for 22 min",
        "TE-HRT-3 1480 C climbing 3 C per min",
        "AT-TG-3 eta-CO 0.48 inside 0.45 to 0.50",
        "CC-BF-7 emergency-tap clause",
        "BOF-slot 140000 USD versus breakout cost",
    ],
}

REJECTED_03 = {
    "id": "ffpc-r20-003",
    "state": STATE_03,
    "proposed_action": PROPOSED_03,
    "safety_decision": {
        "decision": "REJECT",
        "rationale": "Lancing TH-B and cutting wind are refused because AT-TG-3 eta-CO is 0.48, which is treated as a healthy-hearth certificate. The BOF shop is already paging and the 08:00 tap window is kept closed. The 48 min TH-A delay is filed as clay-gun congestion rather than a frozen nose. TE-HRT-3 at 1480 C is filed as a couple drift. Wind stays at 100 percent and TH-B is left idle.",
        "confidence": 0.78,
        "checked_constraints": [
            "AT-TG-3 eta-CO 0.48 utilization band",
            "BOF-shop hot-metal page",
            "140000 USD emergency-tap slot loss",
            "clay-gun congestion story",
        ],
    },
    "executed_action": {
        "action": "keep_BF3_wind_on_eta_co",
        "th_b_lanced": False,
        "wind_cut_pct": 0,
        "coke_held": False,
        "eta_co_as_hearth": True,
        "taphole_delay_honored": False,
        "decision_local": "07:52",
    },
    "future_outcome": {
        "narrative": "Hearth metal kept climbing against the frozen TH-A. The salamander broke out at 08:18. Iron ran the casthouse floor. Two operators took burns. BF-3 stayed down 28 days. AT-TG-3 had only been a still-normal utilization on a hanging burden. IR-TH-A had been a frozen nose. The 08:00 BOF slot was missed on a worse path than a 140000 USD emergency tap.",
        "status": "hearth_breakout",
        "casthouse_iron": True,
        "salamander_opened": True,
        "operators_burned": 2,
        "outage_d": 28,
        "bof_slot_met": False,
        "injuries": 2,
        "surprises": [
            "a mid-band top-gas eta-CO is not a hearth-level certificate",
            "48 min of taphole delay was a frozen nose, not clay-gun congestion",
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
        "notes": "personnel_safety carries a hearth breakout with two burn injuries; asset_integrity carries casthouse iron plus a 28-day outage; evidence_quality reflects top-gas eta-CO spent as hearth inventory against a live 48 min frozen taphole",
    },
    "meta": meta_block(
        3,
        "top_gas_eta_co_as_hearth_level_certificate",
        "REJECT_of_emergency_tap_on_top_gas_eta_co",
    ),
}

DIAG_03 = {
    "root": (
        "The gate treated a still-normal top-gas eta-CO as a hearth-level certificate. The "
        "single load-bearing error is refusing the TH-B emergency tap and 30 percent wind cut "
        "while TH-A is 48 min late against a 20 min trip, because AT-TG-3 reads 0.48. CC-BF-7 "
        "already says eta-CO is utilization, not hearth inventory, and names a still-normal "
        "eta-CO with a frozen taphole as a breakout risk. LT-SL-3 has hung 2.4 m for 22 min. "
        "TE-HRT-3 at 1480 C climbing 3 C per min is the filling hearth."
    ),
    "cascade": (
        "Rejection left wind at 100 percent. The salamander broke out at 08:18. Iron ran the "
        "casthouse floor. Two operators took burns and BF-3 stayed down 28 days. The analyzer "
        "had been utilization, not inventory. The BOF slot was missed on a worse path than a "
        "140000 USD emergency tap. The injury ledger is not clean. The reward total lands near "
        "minus four point nine, dominated by personnel safety, asset integrity, and evidence "
        "quality."
    ),
    "catch": (
        "A correct gate starts from CC-BF-7. TH-A at 48 min is already above 20 min, so wind "
        "stays cut and TH-B stays open. AT-TG-3 at 0.48 is utilization and is the hang "
        "signature together with the frozen nose. Hearth couple climb is not a top-gas number. "
        "The tap is mandatory until metal is on the runner and the stockline moves. The 140000 "
        "USD slot is not commensurate with a hearth breakout."
    ),
    "repair": (
        "The correct verdict accepts the proposed emergency tap and wind cut. Lance TH-B, cut "
        "wind 30 percent, hold coke, and do not treat eta-CO as hearth inventory. Do not keep "
        "operators on the casthouse floor of a furnace already past the delay trip. The landing "
        "stays degraded: the BOF slot is lost at about 140000 USD, the furnace stays slow "
        "through the drill and clay-gun rebuild, and a clay gun may stall for several minutes "
        "on first close without changing the class of the tap."
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
        rej_path = OUT / f"rejected-{i:02d}-r20.json"
        diag_path = OUT / f"diagnosis-{i:02d}-r20.md"
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
        arm = json.loads((OUT / f"rejected-{i:02d}-r20.json").read_text())
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
            "Session A only. No chosen arms. No batch-r20.jsonl. Rights nested under "
            "meta.rights. Never outputs/raw/. Never training_ready. Never sim_or_real=real."
        ),
        "files": files_meta,
        "diagnosis_files": [e for e in files_meta if e["name"].startswith("diagnosis-")],
        "rejected_files": [e for e in files_meta if e["name"].startswith("rejected-")],
        "plants": [
            {
                "id": "ffpc-r20-001",
                "site": "Alquilacion Punta Espato HF alkylation ALK-2",
                "failure_class": "koh_treater_ph_as_hf_settler_inventory",
                "decision": "ACCEPT",
            },
            {
                "id": "ffpc-r20-002",
                "site": "Oxirano Ria Salada EO reactor R-210",
                "failure_class": "quench_bottoms_conductivity_as_eo_hotspot_certificate",
                "decision": "MODIFY",
            },
            {
                "id": "ffpc-r20-003",
                "site": "Alto Horno Caleta Coque blast furnace BF-3",
                "failure_class": "top_gas_eta_co_as_hearth_level_certificate",
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
            "not_prior_failure_classes": sorted(LIVE_ARCHETYPES),
        },
    }
    rec_path = OUT / "diagnosis-handoff-receipt-r20.json"
    rec_path.write_text(dumps(receipt), encoding="utf-8")

    staged = sorted(p.name for p in OUT.iterdir() if p.is_file())
    allowed = {
        "rejected-01-r20.json",
        "rejected-02-r20.json",
        "rejected-03-r20.json",
        "diagnosis-01-r20.md",
        "diagnosis-02-r20.md",
        "diagnosis-03-r20.md",
        "diagnosis-handoff-receipt-r20.json",
    }
    extra_names = set(staged) - allowed
    if extra_names:
        raise SystemExit(f"unexpected staging names {sorted(extra_names)}")
    forbidden = ("batch-r20.jsonl", "NOTES-r20.md", "chosen-01-r20.json")
    for name in forbidden:
        if (OUT / name).exists():
            raise SystemExit(f"session A must not emit {name}")
    if (REPO / "outputs" / "raw" / "2026-08-30" / FACTORY / "batch-r20.jsonl").exists():
        raise SystemExit("outputs/raw already has batch-r20; abort")

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
