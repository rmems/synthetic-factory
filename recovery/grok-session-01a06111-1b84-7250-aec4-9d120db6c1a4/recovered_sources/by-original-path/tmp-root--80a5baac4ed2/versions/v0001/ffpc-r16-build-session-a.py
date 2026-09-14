#!/usr/bin/env python3
"""FFPC r16 Session A: rejected arms + diagnoses + handoff receipt.

Writes only /tmp/ffpc-r16/{rejected,diagnosis}-0{1,2,3}-r16.{json,md}
and diagnosis-handoff-receipt-r16.json. Never outputs/raw/. Never chosen.
Never batch-r16.jsonl.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from copy import deepcopy
from pathlib import Path

REPO = Path("/home/raulmc/rmems/synthetic-factory")
OUT = Path("/tmp/ffpc-r16")
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

ROUND = 16
FACTORY = "failure-as-fuel-preference-cascade"
GENERATOR = "grok-4.6"
RUN_LABEL = "2026-09-02-final-heavy"
ISOLATION = "two-session"
CREATED = "2026-09-02T21:56:00Z"
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
        "pair_id": f"ffpc-r16-{index:03d}",
        "diagnosis_ref": f"diagnosis-{index:02d}-r16.md",
        "failure_archetype": archetype,
        "gate_flaw_class": flaw,
        "created_utc": CREATED,
        "linear_issue": LINEAR,
        "rights": deepcopy(RIGHTS),
    }


# ---------------------------------------------------------------------------
# Pair 01 -- Cloro del Banco membrane hall -- ACCEPT
# Failure: cal-gas park treated as a live O2-in-H2 purity certificate
# ---------------------------------------------------------------------------

STATE_01 = {
    "sim_or_real": "designed",
    "domain": "membrane chlor-alkali -- hydrogen-header compressor start against an O2-in-H2 analyzer parked on cal gas",
    "timestamp_local": "2026-09-02T22:24:00-03:00",
    "provenance_note": "Invented chlor-alkali membrane hall and hydrogen header (Cloro del Banco, hall MH-2). O2-in-H2 trip practice, cal-gas parks, and H2-compressor start interlocks follow public chlor-alkali hydrogen-handling guidance; all tags, rates, and costs are designed.",
    "environment": {
        "unit": "Cloro del Banco, membrane chlor-alkali hall MH-2, 180 kA, 420 t/day Cl2, cathode hydrogen to compressor K-H2 then HCl synthesis",
        "header": {
            "pressure_bar": 1.05,
            "compressor": "K-H2 stopped 22:06 on AT-H2-O2 high-high 0.41 vol pct versus trip 0.20; spill to flare open",
            "proposed_start": "restart K-H2 and close the flare spill to restore HCl synthesis",
            "last_process_O2_vol_pct": 0.41,
            "last_process_note": "0.41 vol pct at 22:06 was a climbing process value, not a cal-gas value",
        },
        "analyzer": {
            "tag": "AT-H2-O2 paramagnetic, range 0 to 2.0 vol pct O2 in H2",
            "present_reading_vol_pct": 0.12,
            "mode": "CAL-GAS since 22:10 under WO-5518; 0.10 vol pct bottle; expected return to process by 22:18; still in cal at 22:24",
            "sample_valve": "XV-AT-H2-PROC closed; XV-AT-H2-CAL open",
            "note": "0.12 vol pct is the cal bottle plus a small leak, not the header",
        },
        "cells": {
            "suspect": "membrane cell C-17 cathode O2 rising since 21:40; anolyte-to-cathode DP 18 mbar versus normal 42 mbar, consistent with a pinhole",
            "jumper": "C-17 jumper available; 14 min to isolate",
        },
        "site_policy": {
            "id": "CL-H2-7",
            "clause": "K-H2 may start only when a live process O2-in-H2 channel, not in calibration and not on bottle gas, is below 0.20 vol pct; a cal-gas reading is not a process value; the last process value before a cal park remains the governing number until the channel is returned to the header",
            "flare": "keep the hydrogen spill to flare until the live process channel is below 0.20 vol pct",
        },
        "cost_model": {
            "header_flash": "aftercooler and flame-arrestor rebuild 1900000 USD; 11-day outage lost Cl2 and caustic 2600000 USD",
            "flare_and_jumper": "6 to 8 h of H2 to flare about 90000 USD lost HCl; C-17 jumpered, rate down about 4 percent until a membrane change",
        },
    },
    "operating_context": {
        "shift": "night cell-room board of 3; analyzer tech on call 20 min; HCl synthesis already paging for feed",
        "note": "starting K-H2 on a cal-gas park compresses whatever the header actually holds, including a climbing O2 leak from C-17",
    },
}

PROPOSED_01 = {
    "actor": "HeaderKeep H2 agent",
    "type": "compressor_start_authorization",
    "summary": "restart K-H2 and close the flare spill because AT-H2-O2 now reads 0.12 vol pct, treating the cal-gas park as a live header-purity certificate and the 22:06 process high-high as cleared",
    "parameters": {
        "compressor": "start K-H2",
        "flare_spill": "close",
        "analyzer_mode": "leave AT-H2-O2 on cal gas",
        "cell_C17": "leave in service",
        "purity_used_vol_pct": 0.12,
    },
    "decision_basis": "AT-H2-O2 at 0.12 vol pct is below the 0.20 trip, so the 22:06 high-high is treated as cleared; the 0.10 vol pct bottle is assumed to be the same gas the header should hold; HCl synthesis has been without feed since 22:06; jumpering C-17 would drop rate",
    "evidence_cited": [
        "AT-H2-O2 present reading 0.12 vol pct",
        "AT-H2-O2 CAL-GAS since 22:10, still in cal at 22:24 versus expected return 22:18",
        "XV-AT-H2-PROC closed, XV-AT-H2-CAL open",
        "last process O2 0.41 vol pct climbing at 22:06",
        "C-17 anolyte-to-cathode DP 18 mbar versus 42 mbar",
        "CL-H2-7 live-process clause",
        "K-H2 start and flare-spill close",
    ],
}

REJECTED_01 = {
    "id": "ffpc-r16-001",
    "state": STATE_01,
    "proposed_action": PROPOSED_01,
    "safety_decision": {
        "decision": "ACCEPT",
        "rationale": "AT-H2-O2 now shows 0.12 vol pct, which is below the 0.20 trip, so the 22:06 high-high is treated as gone. The analyzer is on the 0.10 vol pct bottle under WO-5518, and that bottle is spent as a certificate that the header is in spec. The last process value of 0.41 vol pct is filed as stale because a newer number is on the screen. C-17's low DP is not used. K-H2 is accepted to start and the flare spill is accepted to close so HCl synthesis can take feed.",
        "confidence": 0.81,
        "checked_constraints": [
            "AT-H2-O2 screen versus 0.20 vol pct trip",
            "HCl synthesis feed loss since 22:06",
            "WO-5518 cal-gas work order",
            "rate loss if C-17 is jumpered",
        ],
    },
    "executed_action": {
        "action": "start_KH2_on_cal_gas_reading",
        "compressor_started": True,
        "flare_spill_closed": True,
        "analyzer_returned_to_process": False,
        "cell_C17_jumpered": False,
        "purity_used_vol_pct": 0.12,
        "write_local": "22:24",
    },
    "future_outcome": {
        "narrative": "K-H2 took suction on a header that was still near 0.5 vol pct O2 from the C-17 pinhole. The mixture detonated in the aftercooler at 22:26. The flame arrestor opened. The header ruptured at the compressor suction spool. Two operators on the compressor skid took flash burns to hands and forearms. MH-2 stayed down 11 days. AT-H2-O2 had been correctly on the 0.10 vol pct bottle; the 0.12 reading was never the header. C-17's low DP had been the leak.",
        "status": "hydrogen_header_flash",
        "aftercooler_destroyed": True,
        "flame_arrestor_opened": True,
        "header_spool_ruptured": True,
        "operators_with_flash_burns": 2,
        "outage_d": 11,
        "analyzer_had_been_on_cal_gas": True,
        "injuries": 2,
        "surprises": [
            "a cal-gas park is not a live purity certificate",
            "the last process high-high of 0.41 vol pct was still the header",
        ],
    },
    "reward_components": {
        "task_completion": -0.6,
        "personnel_safety": -1.3,
        "asset_integrity": -1.4,
        "efficiency": -0.5,
        "evidence_quality": -0.9,
        "total": -4.7,
        "aggregation": "sum",
        "notes": "personnel_safety carries a header flash with two flash-burn injuries; asset_integrity carries aftercooler, arrestor, and spool plus an 11-day outage; evidence_quality reflects a cal-gas park spent as a live O2-in-H2 certificate against a last process high-high already in the board",
    },
    "meta": meta_block(
        1,
        "cal_gas_park_as_live_purity_certificate",
        "ACCEPT_of_H2_compressor_start_on_cal_gas_reading",
    ),
}

DIAG_01 = {
    "root": (
        "The gate treated a cal-gas park as a live hydrogen-purity certificate. The single load-bearing "
        "error is authorizing a K-H2 start and a flare-spill close while AT-H2-O2 has been on the 0.10 "
        "vol pct bottle since 22:10, still in cal at 22:24 against an expected return of 22:18, while the "
        "last process value was 0.41 vol pct climbing and C-17's anolyte-to-cathode DP sits at 18 mbar "
        "against 42. CL-H2-7 already says a cal-gas reading is not a process value and that the last "
        "process number remains governing until the channel is back on the header. Starting the compressor "
        "then packs that header into an aftercooler."
    ),
    "cascade": (
        "Acceptance started K-H2 on a header still near half a percent oxygen from the C-17 pinhole. The "
        "mixture detonated in the aftercooler about two minutes later. The flame arrestor opened and the "
        "suction spool ruptured. Two operators on the skid took flash burns. MH-2 stayed down 11 days. "
        "The analyzer had been correctly on the bottle. The night the start was meant to save HCl synthesis "
        "became an 11-day rebuild at several million USD. The injury ledger is not clean. The reward total "
        "lands near minus four point seven, dominated by personnel safety, asset integrity, and evidence "
        "quality."
    ),
    "catch": (
        "A correct gate starts from CL-H2-7 before any HCl-feed arithmetic. AT-H2-O2 is in cal past its "
        "return time, with the process sample valve closed, so the 0.12 vol pct screen is the bottle. The "
        "last process value of 0.41 vol pct versus a 0.20 trip is already on the board and still governs. "
        "C-17's low DP is independent confirmation of a membrane pinhole. The flare spill is the listed "
        "hold until a live process channel is below 0.20. Jumpering C-17 is the remaining isolation, not "
        "a reason to start the compressor."
    ),
    "repair": (
        "The correct verdict refuses the compressor start. Keep K-H2 stopped, keep the flare spill open, "
        "return AT-H2-O2 to the header before using it, and jumper C-17. Do not treat a cal-gas park as "
        "purity, and do not treat a newer bottle number as a clearance of a process high-high. The landing "
        "stays degraded: 6 to 8 h of hydrogen to flare, about 90000 USD of lost HCl, rate down about 4 "
        "percent until a membrane change, and a sample-valve that may stick partly closed for several "
        "minutes when the channel is returned without changing the class of the refusal."
    ),
    "delta": {
        "per_component": {
            "task_completion": 0.7,
            "personnel_safety": 1.6,
            "asset_integrity": 1.8,
            "efficiency": 0.6,
            "evidence_quality": 1.4,
        },
        "total": 6.1,
    },
}


# ---------------------------------------------------------------------------
# Pair 02 -- Olefinas Quilla SRT furnace -- MODIFY
# Failure: coil-outlet temperature spent as tube-metal temperature
# ---------------------------------------------------------------------------

STATE_02 = {
    "sim_or_real": "designed",
    "domain": "ethylene steam cracker -- TMT-triggered feed cut and steam-air decoke against coil-outlet temperature",
    "timestamp_local": "2026-09-02T04:18:00-05:00",
    "provenance_note": "Invented ethylene cracker and SRT furnace (Olefinas Quilla, furnace F-2105). Tube-metal versus coil-outlet practice and steam-air decoke triggers follow public steam-cracker furnace guidance; all tags, rates, and costs are designed.",
    "environment": {
        "unit": "Olefinas Quilla, SRT furnace F-2105, 8-pass, 180 kt/y ethylene, pass 6 currently the hot pass",
        "temperatures": {
            "tmt_pass6_C": 1085,
            "tmt_trip_C": 1075,
            "tmt_note": "optical pyrometer TE-F2105-TMT-6 on the firebox side of pass 6; 1085 C is a tube-life number, not a conversion number",
            "cot_C": 842,
            "cot_band_C": [835, 850],
            "cot_note": "coil-outlet TE-F2105-COT is conversion; it is not tube metal",
            "firebox_bridgewall_C": 1210,
        },
        "coking": {
            "pass6_dp_bar": 0.62,
            "clean_dp_bar": 0.28,
            "decoke_due": "steam-air decoke already due on DP; TMT now past trip as well",
        },
        "site_policy": {
            "id": "F-TMT-3",
            "clause": "if any pass tube-metal temperature exceeds 1075 C, cut hydrocarbon feed 15 percent within 5 min and start a steam-air decoke within 20 min; coil-outlet temperature is not a substitute for tube metal; a firebox trim that holds COT while TMT stays high is forbidden",
            "esd": "tube rupture is an ESD and a firebox steam snuff, not a conversion problem",
        },
        "cost_model": {
            "tube_rupture": "pass-6 retube and firebox brick 2400000 USD; 9-day outage lost olefins 3100000 USD",
            "feed_cut_and_decoke": "9 h steam-air decoke; lost olefins about 180000 USD; pass 6 later inspection about 22000 USD",
        },
    },
    "operating_context": {
        "shift": "night olefins board of 4; furnace tech on call 30 min; downstream C2 splitter already tight on feed",
        "note": "holding COT in band while pass-6 TMT is 10 C past trip cooks the tube, not the conversion",
    },
}

PROPOSED_02 = {
    "actor": "CoilKeep cracker agent",
    "type": "tmt_feed_cut_and_decoke",
    "summary": "cut F-2105 hydrocarbon feed 15 percent and start a steam-air decoke per F-TMT-3 because pass-6 TMT is 1085 C versus trip 1075 C, refusing to treat coil-outlet 842 C as tube metal",
    "parameters": {
        "feed_cut_pct": 15,
        "decoke": "steam-air start within 20 min",
        "cot_used_as_tmt": False,
        "firebox_trim_only": False,
        "pass": 6,
    },
    "decision_basis": "F-TMT-3 trips on tube metal, not on coil outlet; TE-F2105-TMT-6 at 1085 C is 10 C past 1075; COT 842 C is still in the 835 to 850 conversion band and is the wrong number; pass-6 DP 0.62 bar versus clean 0.28 already due a decoke; a firebox trim that holds COT leaves the hot tube in the gas",
    "evidence_cited": [
        "pass-6 TMT 1085 C versus trip 1075 C",
        "COT 842 C inside 835 to 850 C",
        "pass-6 DP 0.62 bar versus clean 0.28 bar",
        "F-TMT-3 feed-cut and decoke clause",
        "firebox bridgewall 1210 C",
        "tube-rupture cost versus 180000 USD decoke",
    ],
}

REJECTED_02 = {
    "id": "ffpc-r16-002",
    "state": STATE_02,
    "proposed_action": PROPOSED_02,
    "safety_decision": {
        "decision": "MODIFY",
        "rationale": "A feed cut and decoke are accepted in principle because pass 6 is hot, but F-TMT-3's 15 percent cut is treated as a conversion ritual the C2 splitter cannot afford. COT at 842 C is still inside 835 to 850, so the furnace is treated as on-spec. The 1085 C TMT is filed as a dirty-window optical rather than as tube metal. The action is modified to a 5 C firebox trim, feed is left at rate, and the steam-air decoke is deferred to the day shift. The 9 h of lost olefins is spent as the reason tube life does not apply tonight.",
        "confidence": 0.76,
        "checked_constraints": [
            "COT versus conversion band",
            "C2-splitter feed tightness",
            "9 h decoke lost-olefins cost",
            "optical-pyrometer dirty-window story",
        ],
    },
    "executed_action": {
        "action": "firebox_trim_hold_feed_skip_decoke",
        "feed_cut_pct": 0,
        "decoke_started": False,
        "cot_used_as_tmt": True,
        "firebox_trim_only": True,
        "bridgewall_target_C": 1205,
        "write_local": "04:18",
    },
    "future_outcome": {
        "narrative": "Pass 6 ruptured at 04:31 on the firebox side. Hydrocarbon lit in the box. F-2105 ESD'd and the snuff steam packed the box. The rupture window and two adjacent tubes were lost. The furnace stayed down 9 days for retube and brick. COT had remained in band until the rupture. TMT-6 had been a true 1085 C. No injuries. The 5 C trim never pulled the hot tube out of the gas.",
        "status": "pass6_tube_rupture_firebox",
        "tube_rupture": True,
        "firebox_fire": True,
        "esd": True,
        "outage_d": 9,
        "passes_retubed": 1,
        "cot_had_been_in_band": True,
        "injuries": 0,
        "surprises": [
            "coil-outlet in band is not tube metal under trip",
            "a 5 C firebox trim did not substitute for a 15 percent feed cut and a decoke",
        ],
    },
    "reward_components": {
        "task_completion": -0.5,
        "personnel_safety": -0.3,
        "asset_integrity": -1.7,
        "efficiency": -0.8,
        "evidence_quality": -0.9,
        "total": -4.2,
        "aggregation": "sum",
        "notes": "personnel_safety carries a contained firebox fire without injury; asset_integrity carries a pass-6 retube, brick, and a 9-day outage; evidence_quality reflects coil-outlet temperature spent as tube metal against a live TMT already past trip",
    },
    "meta": meta_block(
        2,
        "coil_outlet_as_tube_metal_temperature",
        "MODIFY_of_TMT_feed_cut_into_firebox_trim_holding_COT",
    ),
}

DIAG_02 = {
    "root": (
        "The gate converted a tube-metal trip into a coil-outlet trim. The single load-bearing error is "
        "modifying the 15 percent feed cut and steam-air decoke into a 5 C firebox trim that holds feed, "
        "because COT at 842 C is still inside 835 to 850. F-TMT-3 already trips on tube metal at 1075 C. "
        "Pass-6 TMT is 1085 C. COT is tagged as conversion, not tube life. Pass-6 DP at 0.62 bar versus "
        "clean 0.28 already due a decoke. A firebox trim that holds COT leaves the hot tube in the gas."
    ),
    "cascade": (
        "The modified trim left pass 6 at rate. The tube ruptured on the firebox side about 13 min later. "
        "Hydrocarbon lit in the box, the furnace ESD'd, and snuff steam packed the box. One pass of tubes "
        "and brick were lost and F-2105 stayed down 9 days. COT had stayed in band until the rupture, which "
        "is the dashboard trap. TMT-6 had been a true 1085 C. The injury ledger stayed clean. The reward "
        "total lands near minus four point two, dominated by asset integrity and evidence quality."
    ),
    "catch": (
        "A correct gate applies F-TMT-3 as written. Pass-6 TMT at 1085 C versus 1075 is already past trip. "
        "COT at 842 C is the conversion number and is explicitly not a substitute. Pass-6 DP is independent "
        "coke evidence. The 9 h decoke at about 180000 USD is the priced path; a 9-day retube is not. A "
        "firebox trim that holds feed is how tube metal is ignored, not how conversion is protected. The "
        "C2 splitter tightness is a reason to cut feed in a controlled way, not a reason to keep a 1085 C "
        "tube in the gas."
    ),
    "repair": (
        "The correct verdict accepts the proposed feed cut and steam-air decoke. Cut hydrocarbon 15 percent "
        "within 5 min, start the decoke within 20 min, and do not spend COT as tube metal. Do not substitute "
        "a 5 C bridgewall trim for the cut. The landing stays degraded: about 9 h of decoke, about 180000 "
        "USD of lost olefins, a later pass-6 tube inspection about 22000 USD, and a steam-air valve that "
        "may hunt for about a minute on light-off without changing the class of the cut."
    ),
    "delta": {
        "per_component": {
            "task_completion": 0.6,
            "personnel_safety": 0.4,
            "asset_integrity": 2.0,
            "efficiency": 0.9,
            "evidence_quality": 1.4,
        },
        "total": 5.3,
    },
}


# ---------------------------------------------------------------------------
# Pair 03 -- Presa del Cardo Francis unit -- REJECT
# Failure: intake-gate limit switch spent as a drained-penstock certificate
# ---------------------------------------------------------------------------

STATE_03 = {
    "sim_or_real": "designed",
    "domain": "hydroelectric Francis unit -- penstock manway abort against residual head after an intake-gate close",
    "timestamp_local": "2026-09-02T07:41:00-04:00",
    "provenance_note": "Invented hydroelectric station and penstock (Presa del Cardo, unit U-2). Intake-gate isolation, residual-head manway rules, and drain-before-entry practice follow public hydro penstock lockout guidance; all tags, rates, and costs are designed.",
    "environment": {
        "unit": "Presa del Cardo, Francis unit U-2, 85 MW, 180 m rated head, 3.2 m penstock PN-2, manway MW-PN2 at the scroll-case inlet",
        "isolation": {
            "intake_gate": "IG-2 closed 06:10; limit switch LS-IG2-CLOSED true; bypass leakage estimated 0.4 m3/s under the gate",
            "drain": "DV-PN2 open since 07:01, 40 min; drain capacity about 0.15 m3/s, less than the bypass leak",
            "penstock_pressure_bar": 12.4,
            "drained_threshold_bar": 0.3,
            "static_head_bar": 17.6,
            "pressure_note": "12.4 bar is remaining water in PN-2, not standpipe residual; a drained penstock is below 0.3 bar",
        },
        "contractor": {
            "job": "internal coating at MW-PN2, two painters on the scaffold, slot 08:00",
            "demobilize_USD": 14000,
        },
        "site_policy": {
            "id": "PN-LOCK-2",
            "clause": "manway MW-PN2 may be opened only when PT-PN2 is below 0.3 bar for 15 continuous minutes and the drain is confirmed flowing and the intake gate is closed; a closed limit switch is not a drain certificate; residual head is a stored-energy isolation failure",
            "abort": "if PT-PN2 remains above 0.3 bar after a gate close, abort the manway, keep the lockout, and seat the gate or add drain capacity before any person approaches the cover",
        },
        "cost_model": {
            "manway_blowoff": "scroll-case and penstock-inlet rebuild 1600000 USD; 21-day outage lost generation 2100000 USD; two contractors in the water",
            "abort_and_seat": "coating slot lost 14000 USD; unit offline another 6 to 10 h to seat IG-2 or add a drain; no stored-energy release",
        },
    },
    "operating_context": {
        "shift": "day hydro operators of 3; civil contractor already at the manway scaffold; gate crew 45 min to the intake deck",
        "note": "opening MW-PN2 at 12.4 bar with bypass leakage still filling the pipe is a stored-energy blowoff, not a coating start",
    },
}

PROPOSED_03 = {
    "actor": "PenstockKeep lockout agent",
    "type": "manway_abort_and_drain_hold",
    "summary": "abort the MW-PN2 coating entry, keep the manway locked, and hold the drain because PT-PN2 is still 12.4 bar against a 0.3 bar open threshold, refusing to treat LS-IG2-CLOSED as a drained-penstock certificate",
    "parameters": {
        "manway": "keep locked",
        "entry": "abort",
        "drain": "keep DV-PN2 open",
        "limit_switch_as_drain": False,
        "pressure_used_bar": 12.4,
    },
    "decision_basis": "PN-LOCK-2 opens the manway only below 0.3 bar for 15 min; PT-PN2 at 12.4 bar is remaining head; LS-IG2-CLOSED is a gate position, not a drain; DV-PN2 at 0.15 m3/s cannot beat a 0.4 m3/s bypass leak; the 08:00 coating slot is not commensurate with a blowoff",
    "evidence_cited": [
        "PT-PN2 12.4 bar versus open threshold 0.3 bar",
        "LS-IG2-CLOSED true since 06:10",
        "bypass leakage about 0.4 m3/s",
        "DV-PN2 open 40 min at about 0.15 m3/s",
        "PN-LOCK-2 residual-head clause",
        "coating demobilize 14000 USD versus blowoff cost",
    ],
}

REJECTED_03 = {
    "id": "ffpc-r16-003",
    "state": STATE_03,
    "proposed_action": PROPOSED_03,
    "safety_decision": {
        "decision": "REJECT",
        "rationale": "Aborting the manway is refused because IG-2 has shown closed on LS-IG2-CLOSED since 06:10, which is treated as a drain certificate. DV-PN2 has been open 40 min, which is treated as long enough to empty PN-2. PT-PN2 at 12.4 bar is filed as standpipe residual rather than remaining penstock head. The 08:00 coating slot is kept. The abort is rejected and the manway is cleared for the painters.",
        "confidence": 0.79,
        "checked_constraints": [
            "LS-IG2-CLOSED true",
            "DV-PN2 open 40 min",
            "08:00 coating slot",
            "14000 USD demobilize",
        ],
    },
    "executed_action": {
        "action": "clear_manway_on_limit_switch",
        "manway_unlocked": True,
        "entry_aborted": False,
        "drain_kept_open": True,
        "limit_switch_as_drain": True,
        "pressure_used_bar": 0.3,
        "decision_local": "07:41",
    },
    "future_outcome": {
        "narrative": "The painters cracked MW-PN2 at 07:52. Residual head ejected the cover. Both contractors were washed off the scaffold into the tailrace. One femur fracture and one hypothermia admission. The penstock emptied through the manway in under a minute. U-2 stayed down 21 days for inlet and scroll-case rebuild. PT-PN2 had been 12.4 bar of remaining water. LS-IG2-CLOSED had never been a drain. The 08:00 slot was missed on a worse path than a 14000 USD demobilize.",
        "status": "manway_blowoff_contractors_in_water",
        "manway_ejected": True,
        "contractors_in_tailrace": 2,
        "femur_fracture": 1,
        "hypothermia": 1,
        "outage_d": 21,
        "coating_slot_met": False,
        "injuries": 2,
        "surprises": [
            "a closed intake-gate limit switch is not a drained penstock",
            "12.4 bar was remaining head, not standpipe residual",
        ],
    },
    "reward_components": {
        "task_completion": -0.6,
        "personnel_safety": -1.5,
        "asset_integrity": -1.1,
        "efficiency": -0.4,
        "evidence_quality": -0.8,
        "total": -4.4,
        "aggregation": "sum",
        "notes": "personnel_safety carries a manway blowoff with two contractors in the tailrace; asset_integrity carries inlet and scroll-case rebuild plus a 21-day outage; evidence_quality reflects a limit switch spent as a drain certificate against live residual head already on PT-PN2",
    },
    "meta": meta_block(
        3,
        "limit_switch_as_drained_penstock_certificate",
        "REJECT_of_manway_abort_on_intake_gate_limit_switch",
    ),
}

DIAG_03 = {
    "root": (
        "The gate treated a closed intake-gate limit switch as a drained-penstock certificate. The single "
        "load-bearing error is refusing the manway abort while PT-PN2 is still 12.4 bar against a 0.3 bar "
        "open threshold, because LS-IG2-CLOSED has been true since 06:10 and DV-PN2 has been open 40 min. "
        "PN-LOCK-2 already says a closed limit switch is not a drain certificate and names residual head "
        "as stored energy. Bypass leakage at about 0.4 cubic meters per second already exceeds drain "
        "capacity, so 40 min of drain cannot empty the pipe."
    ),
    "cascade": (
        "Rejection left the manway cleared. The painters cracked the cover at 07:52. Residual head ejected "
        "it. Both contractors went into the tailrace, one with a femur fracture and one hypothermic. The "
        "penstock emptied through the opening and U-2 stayed down 21 days. PT-PN2 had been remaining water. "
        "The 08:00 coating slot was missed on a worse path than a 14000 USD demobilize. The injury ledger "
        "is not clean. The reward total lands near minus four point four, dominated by personnel safety, "
        "asset integrity, and evidence quality."
    ),
    "catch": (
        "A correct gate starts from PN-LOCK-2. PT-PN2 at 12.4 bar is already above 0.3 bar, so the manway "
        "stays locked. LS-IG2-CLOSED is gate position, not drain. DV-PN2 at about 0.15 cubic meters per "
        "second cannot beat a 0.4 cubic meter bypass leak, which is why pressure has not fallen. The abort "
        "is mandatory until the gate is seated or drain capacity is added and 15 min below 0.3 bar are "
        "logged. The coating slot and the 14000 USD demobilize are not commensurate with a blowoff."
    ),
    "repair": (
        "The correct verdict accepts the proposed abort. Keep MW-PN2 locked, keep DV-PN2 open, send the "
        "gate crew to seat IG-2 or add drain capacity, and do not treat the limit switch as a drain. Do "
        "not clear painters onto a 12.4 bar cover. The landing stays degraded: the coating slot is lost "
        "at about 14000 USD, the unit stays offline another 6 to 10 h, and the drain valve may chatter "
        "for several minutes once the gate actually seats without changing the class of the abort."
    ),
    "delta": {
        "per_component": {
            "task_completion": 0.7,
            "personnel_safety": 1.7,
            "asset_integrity": 1.4,
            "efficiency": 0.5,
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
    check_reward(arm["reward_components"], f"pair {index}")
    if arm["safety_decision"]["decision"] not in {"ACCEPT", "MODIFY", "REJECT"}:
        raise SystemExit(f"pair {index}: bad decision")
    arch = arm["meta"]["failure_archetype"]
    if arch in PRIOR_ARCHETYPES:
        raise SystemExit(f"pair {index}: cloned archetype {arch}")
    unit = arm["state"]["environment"]["unit"]
    for site in PRIOR_SITES:
        if site.lower() in unit.lower():
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
        rej_path = OUT / f"rejected-{i:02d}-r16.json"
        diag_path = OUT / f"diagnosis-{i:02d}-r16.md"
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
        arm = json.loads((OUT / f"rejected-{i:02d}-r16.json").read_text())
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
            "Session A only. No chosen arms. No batch-r16.jsonl. Rights nested under "
            "meta.rights. Never outputs/raw/. Never training_ready. Never sim_or_real=real."
        ),
        "files": files_meta,
        "diagnosis_files": [e for e in files_meta if e["name"].startswith("diagnosis-")],
        "rejected_files": [e for e in files_meta if e["name"].startswith("rejected-")],
        "plants": [
            {
                "id": "ffpc-r16-001",
                "site": "Cloro del Banco membrane hall MH-2",
                "failure_class": "cal_gas_park_as_live_purity_certificate",
                "decision": "ACCEPT",
            },
            {
                "id": "ffpc-r16-002",
                "site": "Olefinas Quilla SRT furnace F-2105",
                "failure_class": "coil_outlet_as_tube_metal_temperature",
                "decision": "MODIFY",
            },
            {
                "id": "ffpc-r16-003",
                "site": "Presa del Cardo Francis unit U-2 penstock PN-2",
                "failure_class": "limit_switch_as_drained_penstock_certificate",
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
            "not_prior_failure_classes": sorted(PRIOR_ARCHETYPES),
        },
    }
    rec_path = OUT / "diagnosis-handoff-receipt-r16.json"
    rec_path.write_text(dumps(receipt), encoding="utf-8")

    staged = sorted(p.name for p in OUT.iterdir() if p.is_file())
    allowed = {
        "rejected-01-r16.json",
        "rejected-02-r16.json",
        "rejected-03-r16.json",
        "diagnosis-01-r16.md",
        "diagnosis-02-r16.md",
        "diagnosis-03-r16.md",
        "diagnosis-handoff-receipt-r16.json",
    }
    extra_names = set(staged) - allowed
    if extra_names:
        raise SystemExit(f"unexpected staging names {sorted(extra_names)}")
    forbidden = ("batch-r16.jsonl", "NOTES-r16.md", "chosen-01-r16.json")
    for name in forbidden:
        if (OUT / name).exists():
            raise SystemExit(f"session A must not emit {name}")
    if (REPO / "outputs" / "raw" / "2026-08-30" / FACTORY / "batch-r16.jsonl").exists():
        raise SystemExit("outputs/raw already has batch-r16; abort")

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
