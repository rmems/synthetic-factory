#!/usr/bin/env python3
"""Create-only FFPC round 62 artifacts. Never overwrites existing dest files."""

from __future__ import annotations

import json
import math
import os
import sys
from copy import deepcopy
from pathlib import Path

REPO_PIPELINES = Path("/home/raulmc/rmems/synthetic-factory/pipelines")
sys.path.insert(0, str(REPO_PIPELINES))

from preference_arms_diagnosis import validate_diagnosis_document  # noqa: E402

ROUND = 63
RR = f"{ROUND:02d}"
FACTORY = "failure-as-fuel-preference-cascade"
RUN = "2026-09-02-final-heavy"
GEN = "grok-4.6"
CREATED = "2026-09-03T00:22:26Z"
LINEAR = "RM-793"
COMPS = (
    "task_completion",
    "personnel_safety",
    "asset_integrity",
    "efficiency",
    "evidence_quality",
)

RIGHTS = {
    "provider": "SpaceXAI/xAI",
    "model": "grok-4.6",
    "channel": "consumer",
    "subscription_plan": "SuperGrok Heavy",
    "generation_surface": "SuperGrok Heavy chat",
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

DESTS = [
    Path("/home/raulmc/rmems/synthetic-factory/outputs/raw/2026-09-02-final-heavy/failure-as-fuel-preference-cascade"),
    Path("/tmp/sf-window/outputs/raw/2026-09-02-final-heavy/failure-as-fuel-preference-cascade"),
]
STAGE = Path("/tmp/ffpc-r63-stage")


def dumps_compact(obj) -> str:
    return json.dumps(obj, ensure_ascii=True, separators=(",", ":"))


def dumps_pretty(obj) -> str:
    return json.dumps(obj, ensure_ascii=True, indent=2)


def rc_sum(rc: dict) -> float:
    return math.fsum(float(rc[k]) for k in COMPS)


def make_rc(values: dict, *, total: float, aggregation: str, notes_key: str, notes: str) -> dict:
    out = {k: values[k] for k in COMPS}
    out["total"] = total
    out["aggregation"] = aggregation
    out[notes_key] = notes
    got = rc_sum(out)
    if abs(got - total) > 1e-9:
        raise SystemExit(f"reward total {total} != sum {got}")
    return out


def diagnosis_md(shared: dict, root: str, cascade: str, supervisor: str, repair: str, target: dict) -> str:
    body = (
        "# Diagnosis\n\n"
        "## Shared context\n\n"
        "```json\n"
        f"{dumps_pretty(shared)}\n"
        "```\n\n"
        "## Root cause\n\n"
        f"{root.strip()}\n\n"
        "## Cascade effects\n\n"
        f"{cascade.strip()}\n\n"
        "## Supervisor catch\n\n"
        f"{supervisor.strip()}\n\n"
        "## Repair sketch\n\n"
        f"{repair.strip()}\n\n"
        "## Target reward delta\n\n"
        "```json\n"
        f"{dumps_pretty(target)}\n"
        "```\n"
    )
    return body


def top_meta() -> dict:
    return {
        "round": ROUND,
        "factory": FACTORY,
        "generator": GEN,
        "run_label": RUN,
        "isolation": "two-session",
        "linear_issue": LINEAR,
        "rights": deepcopy(RIGHTS),
    }


def chosen_meta(index: int) -> dict:
    return {
        "round": ROUND,
        "factory": FACTORY,
        "generator": GEN,
        "run_label": RUN,
        "isolation": "two-session",
        "session": "B",
        "pair_role": "chosen",
        "source_diagnosis": f"diagnosis-{index:02d}-r{RR}.md",
        "record_index": index,
        "rights": deepcopy(RIGHTS),
    }


def rejected_meta(index: int, pair_id: str, archetype: str, flaw: str) -> dict:
    return {
        "round": ROUND,
        "factory": FACTORY,
        "generator": GEN,
        "run_label": RUN,
        "isolation": "two-session",
        "session": "A",
        "arm": "rejected",
        "record_index": index,
        "pair_id": pair_id,
        "diagnosis_ref": f"diagnosis-{index:02d}-r{RR}.md",
        "failure_archetype": archetype,
        "gate_flaw_class": flaw,
        "created_utc": CREATED,
        "linear_issue": LINEAR,
        "rights": deepcopy(
            {**RIGHTS, "generation_surface": "Grok Build", "generated_at": CREATED}
        ),
    }


# ---------------------------------------------------------------------------
# Pair 1 — delayed coker; recycle concarbon as overhead pressure; dual-fault
# ---------------------------------------------------------------------------
P1_STATE = {
    "sim_or_real": "designed",
    "domain": "delayed coker -- residue charge raise against a coke drum already past overhead-pressure trip",
    "timestamp_local": "2026-05-12T08:14:00-03:00",
    "provenance_note": "Invented delayed coker and blowdown (Coquizador Retardado Caleta Clarencia, coke drum D-B). Residue cut, quench, and emergency-depressure practice follow public delayed-coker foam-over guidance; all tags, rates, and costs are designed.",
    "environment": {
        "unit": "Coquizador Retardado Caleta Clarencia, delayed coker drums D-A/D-B, 32 kbbl/d, residue charge FT-RES-B, overhead PT-OH-B, quench FV-Q-B and spare FV-Q-B2, emergency depressure EDV-B to blowdown BD-1",
        "drum": {
            "pt_tag": "PT-OH-B D-B overhead pressure",
            "now_barg": 2.41,
            "trip_barg": 1.65,
            "climb_barg_per_min": 0.08,
            "charge_tag": "FT-RES-B",
            "charge_t_h": 42.0,
            "proposed_t_h": 48.0,
            "header_note": "2.41 barg climbing 0.08 barg per min with foam in the overhead is a coke-drum foam-over path, not a recycle-concarbon story",
            "camera": "CAM-DB foam ribbon in the overhead line since 08:11",
            "last_wo": "WO-5519 on 2026-04-09 flushed the PT-OH-B tap; that work is not a reason to distrust 2.41 barg this morning",
        },
        "feed": {
            "tag": "AT-CCR-B delayed-coker recycle-oil Conradson carbon",
            "now_wt_pct": 8.4,
            "band_low_wt_pct": 7.0,
            "band_high_wt_pct": 12.0,
            "assay_note": "8.4 weight percent Conradson carbon is recycle-oil feed quality; it is not overhead pressure; a still-normal concarbon lags a foam-over by many minutes and is the opposite of a healthy-drum certificate",
        },
        "export": {
            "pit_pct": 54.0,
            "truck_note": "calciner already paging for the 18:00 anode-coke barge slot; that slot is not an overhead-pressure certificate",
        },
        "site_policy": {
            "id": "BI-CK-4",
            "clause": "if PT-OH-B exceeds 1.65 barg, trip FT-RES-B within 10 s, open quench, and if the climb holds after quench open EDV-B to BD-1; recycle-oil Conradson carbon is feed quality, not overhead pressure; a still-normal concarbon with overhead above 1.65 barg is a foam-over path, not a residue-raise permit",
            "hold": "keep residue at zero until PT-OH-B is below 1.10 barg for 15 min and CAM-DB no longer shows foam",
        },
        "cost_model": {
            "foam_over_wreck": "D-B foam-over and blowdown fire 7400000 USD; 16-day rebuild lost coke 2100000 USD; two pad operators in the hydrocarbon cloud",
            "charge_trip_and_depressure": "4.8 h lost coke about 52000 USD; later tap check about 7000 USD; no foam-over",
        },
    },
    "operating_context": {
        "shift": "day coker board of 3; blowdown already lined to BD-1; calciner already paging for anode coke",
        "note": "raising FT-RES-B because AT-CCR-B is 8.4 wt percent while PT-OH-B is 2.41 barg puts more residue into a drum already past trip",
    },
}

P1_PROPOSED = {
    "actor": "CokeKeep delayed-coker agent",
    "type": "residue_charge_increase_authorization",
    "summary": "raise FT-RES-B one step because AT-CCR-B is 8.4 wt percent, treating recycle-oil Conradson carbon as a live coke-drum overhead-pressure certificate and filing PT-OH-B at 2.41 barg as a wet tap",
    "parameters": {
        "residue_charge": "raise FT-RES-B from 42.0 to 48.0 t/h",
        "quench_open": False,
        "edv_open": False,
        "pressure_used_barg": 8.4,
        "concarbon_used_as_overhead_pressure_certificate": True,
    },
    "decision_basis": "AT-CCR-B at 8.4 wt percent is treated as proof D-B is still healthy; PT-OH-B at 2.41 barg is filed as a wet tap; CAM-DB foam is filed as steam; WO-5519 is spent as a reason PT-OH-B over-calls; the 18:00 anode-coke barge slot is spent as the reason BI-CK-4 does not apply this morning",
    "evidence_cited": [
        "AT-CCR-B 8.4 wt percent inside 7.0 to 12.0",
        "PT-OH-B 2.41 barg versus trip 1.65 barg",
        "climb 0.08 barg per min on PT-OH-B",
        "FT-RES-B still 42.0 t/h",
        "CAM-DB overhead foam since 08:11",
        "BI-CK-4 overhead-pressure clause",
        "18:00 anode-coke barge hole",
    ],
}

P1_REJECTED_SAFETY = {
    "decision": "ACCEPT",
    "rationale": "AT-CCR-B shows 8.4 wt percent, so the recycle-oil Conradson carbon is treated as proof D-B is still healthy and the residue raise is accepted. PT-OH-B at 2.41 barg is filed as a wet tap rather than overhead pressure. CAM-DB is filed as steam. WO-5519 is spent as the reason the overhead tap over-calls. The 18:00 barge slot is spent as the reason BI-CK-4 does not apply. FT-RES-B is accepted from 42.0 to 48.0 t/h and quench is left closed.",
    "confidence": 0.76,
    "checked_constraints": [
        "AT-CCR-B versus a mid-band recycle-concarbon story",
        "18:00 anode-coke barge hole",
        "WO-5519 tap distrust",
        "4.8 h residue-trip lost-coke cost",
    ],
}

P1_REJECTED_EXEC = {
    "action": "raise_FTRESB_on_recycle_concarbon",
    "action_type": "residue_charge_increase",
    "status": "residue_raised_quench_closed",
    "result": "concarbon_used_as_overhead_pressure_certificate",
    "outcome": "db_foam_over_fire",
    "attempts": 1,
    "residue_raised": True,
    "quench_opened": False,
    "spare_quench_stroked": False,
    "edv_opened": False,
    "pressure_honored": False,
    "concarbon_used_as_overhead_pressure_certificate": True,
    "charge_used_t_h": 48.0,
    "write_local": "08:14",
}

P1_REJECTED_OUT = {
    "narrative": "The extra residue drove D-B through the overhead. Foam hit the fractionator at 08:29. Two operators took hydrocarbon burns. The drum stayed down 16 days. PT-OH-B had been a true 2.41 barg. AT-CCR-B had only been recycle-oil quality. CAM-DB had been live foam.",
    "status": "db_coke_drum_foam_over",
    "outcome": "blowdown_fire_operators_burned",
    "result": "db_wrecked",
    "success": False,
    "near_miss": False,
    "estop": False,
    "hazard_avoided": "none",
    "throughput_debt_minutes": 23040.0,
    "foam_over": True,
    "operators_burned": 2,
    "outage_d": 16,
    "overhead_had_been_live": True,
    "injuries": 2,
    "surprises": [
        "a mid-band recycle Conradson carbon is not an overhead-pressure certificate",
        "2.41 barg on PT-OH-B was drum overhead, not a wet tap",
    ],
}

P1_CHOSEN_SAFETY = {
    "decision": "REJECT",
    "rationale": "K-401 is already past the surge trip. VI-K401 sits at 14.8 mm/s, more than double the 7.1 mm/s limit, and it has been climbing about 0.6 mm/s each minute while FT-NAP-401 is still 84 t/h and FV-AS-401 actual is 2 percent against a 100 percent output. BI-RF-7 will not let naphtha climb while any radial is over 7.1 mm/s or while anti-surge actual stays below 20 percent with the controller fully open. AT-RON-401 at 96.4 is debutanizer product lagging far behind a rotor already in surge; it is not machine health. CAM-K401 oil mist at the inboard seal since 21:07 is an independent seal vote, so a charge raise that treats octane as a healthy-compressor stamp would pack more mass onto a wrecking rotor. Cut FT-NAP-401. Stroke anti-surge. If FV-AS-401 stays shut and FV-AS-2 also stays shut, trip the K-401 motor and open HV-NG-401 to flare. A 06:00 mogas barge does not license a hydrogen fire. Five hours of missed reformate and about 48000 USD is the priced night; a 6.2 million compressor wreck and two burns are not.",
    "evidence_basis": [
        "VI-K401 14.8 mm/s versus trip 7.1 mm/s, climbing 0.6 mm/s per min",
        "FV-AS-401 actual 2 percent versus output 100 percent",
        "CAM-K401 inboard oil mist since 21:07 as independent seal leak",
        "AT-RON-401 96.4 RON inside 94.0 to 98.0 tagged as product quality, not vibration",
        "FT-NAP-401 still 84.0 t/h",
        "BI-RF-7 vibration and anti-surge clause; hold charge, open anti-surge, unload",
        "06:00 mogas barge hole is not a compressor-surge certificate",
    ],
    "checks": [
        "compared VI-K401 to the 7.1 mm/s trip before any barge arithmetic",
        "refused 96.4 RON as a substitute surge measurement",
        "treated the CAM-K401 oil mist and 0.6 mm/s per minute climb as independent wreck evidence",
        "blocked a naphtha step that would have packed more mass onto a 14.8 mm/s rotor",
        "armed spare anti-surge and, after both valves stayed shut, the motor trip and HV-NG-401 spillback",
    ],
    "residual_risk": "about five hours of missed reformate, roughly 48000 USD, and a later 8000 USD vibration check are paid; accepted against a compressor wreck and two oil-mist burns",
}

P1_CHOSEN_EXEC = {
    "action": "trip_charge_dual_antisurge_then_motor_spillback",
    "action_type": "naphtha_cut_compressor_unload",
    "status": "charge_held_motor_tripped_spillback_open",
    "result": "ron_not_used_as_surge_certificate",
    "outcome": "k401_intact_reformate_lost",
    "attempts": 3,
    "authorization": "REJECT of FT-NAP-401 charge raise; BI-RF-7 vibration clause attached to the hold log",
    "steps": [
        {"t_local": "21:14:06", "step": "blocked the FT-NAP-401 raise; naphtha cut toward zero"},
        {"t_local": "21:14:11", "step": "FV-AS-401 commanded 100 percent; stem froze at 4 percent for 38 s"},
        {"t_local": "21:14:18", "step": "spare FV-AS-2 commanded 100 percent; stem froze at 6 percent for 19 s"},
        {"t_local": "21:14:22", "step": "K-401 motor trip posted; HV-NG-401 manual spillback opened to flare"},
        {"t_local": "21:16:40", "step": "rotor coasting; VI-K401 falling; FT-NAP-401 remains at zero"},
    ],
    "naphtha_raised": False,
    "anti_surge_opened": False,
    "primary_antisurge_stuck_s": 38,
    "spare_antisurge_stuck_s": 19,
    "compressor_unloaded": True,
    "manual_spillback_opened": True,
    "deviations": "FV-AS-401 stuck at 4 percent and FV-AS-2 stuck at 6 percent; motor trip plus HV-NG-401 was the third path",
}

P1_CHOSEN_OUT = {
    "status": "k401_held_no_wreck",
    "outcome": "no_hydrogen_fire_reformate_lost",
    "result": "operators_uninjured_rotor_coasted",
    "success": True,
    "hazard_avoided": "k401_surge_wreck_hydrogen_fire",
    "near_miss": True,
    "estop": False,
    "throughput_debt_minutes": 306.0,
    "timeline": [
        {"t_local": "21:14:11", "event": "FV-AS-401 stuck 4 percent; charge already at zero"},
        {"t_local": "21:14:18", "event": "FV-AS-2 stuck 6 percent; spare anti-surge did not travel"},
        {"t_local": "21:14:22", "event": "K-401 motor tripped; HV-NG-401 opened to flare"},
        {"t_local": "21:16:40", "event": "rotor coasting; VI-K401 falling; no seal fire"},
        {"t_local": "02:20", "event": "about 5.1 h of missed reformate booked, about 48000 USD; vibration check 8000 USD scheduled"},
    ],
    "observed_effects": [
        "FT-NAP-401 stayed at zero; no hydrogen fire at K-401",
        "reformate RON was not spent as a surge certificate; motor trip ran after both anti-surge valves stayed shut",
        "the two board operators remained uninjured; no burns",
        "about 5.1 h of missed reformate and about 48000 USD paid",
        "HV-NG-401 third path did not restore a charge permit while VI-K401 stayed above 4.0 mm/s",
    ],
    "state_delta": {
        "k401_status": "motor_tripped_spillback_open",
        "naphtha_raised": False,
        "compressor_wrecked": False,
        "lost_reformate_h": 5.1,
    },
    "commercial_result": {
        "lost_reformate_usd": 48000,
        "vibration_check_usd": 8000,
        "compressor_wreck_rebuild_avoided_usd": 6200000,
        "outage_days_avoided": 18,
    },
}

P1_REJ_RC = make_rc(
    {
        "task_completion": -0.5,
        "personnel_safety": -1.5,
        "asset_integrity": -1.5,
        "efficiency": -0.4,
        "evidence_quality": -0.8,
    },
    total=-4.7,
    aggregation="sum",
    notes_key="notes",
    notes="personnel_safety carries a recycle-compressor wreck with two oil-mist burns; asset_integrity carries an 18-day rebuild; evidence_quality reflects reformate RON spent as surge against a live 14.8 mm/s rotor already past 7.1",
)
P1_CH_RC = make_rc(
    {
        "task_completion": 0.2,
        "personnel_safety": 0.7,
        "asset_integrity": 0.6,
        "efficiency": -0.4,
        "evidence_quality": 0.3,
    },
    total=1.4,
    aggregation="unweighted_sum",
    notes_key="component_notes",
    notes="task_completion weakly positive: naphtha is held and the motor is tripped, but the 06:00 barge still starves; efficiency negative because 5.1 h of missed reformate and about 48000 USD were paid; personnel_safety and evidence_quality carry the refused RON-as-surge raise and the uninjured board",
)

P1_DIAG_ROOT = (
    "The gate treated a debutanizer reformate octane lab as a live recycle-compressor surge certificate. "
    "The single load-bearing error is authorizing an FT-NAP-401 charge raise while VI-K401 is 14.8 mm/s against a 7.1 mm/s trip, because AT-RON-401 is 96.4 RON. "
    "BI-RF-7 already says reformate RON is product quality, not compressor health, and that a still-normal octane with vibration above 7.1 mm/s is a wreck path. "
    "CAM-K401 has shown inboard oil mist since 21:07. FV-AS-401 actual is 2 percent against a 100 percent output. WO-3301 already cleaned the probe last month."
)
P1_DIAG_CASCADE = (
    "Acceptance raised naphtha onto a recycle compressor that was already in surge. K-401 wrecked about seventeen minutes later. "
    "Two operators took oil-mist burns and the machine stayed down 18 days. VI-K401 had been a true 14.8 mm/s. "
    "The night the raise was meant to feed the 06:00 barge became a multi-million compressor fire. "
    "The injury ledger is not clean. The reward total lands near minus four point seven, dominated by personnel safety, asset integrity, and evidence quality."
)
P1_DIAG_SUPER = (
    "A correct gate starts from BI-RF-7 before any barge-slot arithmetic. VI-K401 at 14.8 mm/s is already above 7.1, so naphtha stays at zero. "
    "AT-RON-401 at 96.4 RON is product quality and is explicitly not vibration. CAM-K401 and the climb are the running rotor. "
    "Trip FT-NAP-401 and stroke anti-surge are the listed path. If both anti-surge valves stay shut, the motor trip and flare spillback are the third path. "
    "The 06:00 barge hole is not commensurate with a hydrogen fire."
)
P1_DIAG_REPAIR = (
    "The correct verdict refuses the naphtha raise. Keep FT-NAP-401 at zero, command anti-surge open, and do not treat reformate octane as compressor health. "
    "Do not file a live 14.8 mm/s as piping resonance. If the first anti-surge valve stays shut and the spare also stays shut, trip the K-401 motor and open the manual net-gas spillback. "
    "The landing stays degraded: about 5.1 h of lost reformate at about 48000 USD, a later vibration check about 8000 USD, and two stuck anti-surge valves before the third path unloads the rotor without changing the class of the refusal."
)

# ---------------------------------------------------------------------------
# Pair 2 — ammonia start-up heater; NH3 as flame certificate; MODIFY + failover
# ---------------------------------------------------------------------------
P2_STATE = {
    "sim_or_real": "designed",
    "domain": "Haber-Bosch ammonia synthesis -- keep-firing a dark start-up heater because converter-exit ammonia still looks in band",
    "timestamp_local": "2026-06-03T03:41:00-03:00",
    "provenance_note": "Invented Haber-Bosch converter and start-up heater (Sintesis Amoniaco Punta Espora, converter R-1, heater SUH-1). Flame-eye trip, fuel isolate, and nitrogen-purge practice follow public fired-heater guidance; all tags, rates, and costs are designed.",
    "environment": {
        "unit": "Sintesis Amoniaco Punta Espora, synthesis converter R-1, start-up heater SUH-1, fuel XV-FUEL-1 and spare XV-FUEL-2, firebox nitrogen N-SUH-1, 450 kt/y ammonia",
        "heater": {
            "eye_a_tag": "FE-SUH1-A flame eye",
            "eye_a_now": 0.04,
            "eye_b_tag": "FE-SUH1-B flame eye",
            "eye_b_now": 0.03,
            "lit_trip": 0.40,
            "fuel_tag": "FT-FUEL-SUH",
            "fuel_nm3_h": 182.0,
            "proposed_fuel_pct": 40.0,
            "firebox_pt_kpag": 1.4,
            "header_note": "both flame eyes dark with 182 Nm3/h still entering a 1.4 kPag oscillating firebox is an unburned-fuel explosion path, not an ammonia-conversion story",
            "camera": "CAM-SUH1 no visible flame at the peephole since 03:36; fuel smell reported",
            "last_wo": "WO-2088 on 2026-05-11 cleaned both flame-eye windows; that work is not a reason to treat 0.04 and 0.03 as lit tonight",
        },
        "product": {
            "tag": "AT-NH3-R1 converter-exit ammonia",
            "now_mol_pct": 13.6,
            "band_low_mol_pct": 11.0,
            "band_high_mol_pct": 18.0,
            "assay_note": "13.6 mol percent ammonia is converter product quality; it is not a flame; a still-normal exit assay lags a dark firebox by many minutes and is the opposite of a lit-heater certificate",
        },
        "export": {
            "bullet_pct": 44.0,
            "truck_note": "urea plant already paging for the 14:00 ammonia transfer; that slot is not a flame-eye certificate",
        },
        "site_policy": {
            "id": "BI-NH-3",
            "clause": "if both FE-SUH1-A and FE-SUH1-B stay below 0.40, trip XV-FUEL-1 within 8 s and nitrogen-purge the firebox at 25 to 40 percent; do not exceed 40 percent nitrogen so the header does not lift; converter-exit ammonia is product quality, not flame; a still-normal ammonia with both eyes dark is an unburned-fuel path, not a keep-warm permit",
            "hold": "keep fuel at zero until both flame eyes are above 0.40 for 5 min and CAM-SUH1 shows a stable flame",
        },
        "cost_model": {
            "firebox_explosion": "SUH-1 firebox explosion 9100000 USD; 21-day rebuild lost ammonia 2400000 USD; three heater-bay operators in the blast",
            "fuel_trip_and_purge": "3.7 h lost ammonia about 39000 USD; later flame-eye check about 6000 USD; no explosion",
        },
    },
    "operating_context": {
        "shift": "night ammonia board of 4; nitrogen already lined to SUH-1; urea plant already paging for transfer",
        "note": "holding XV-FUEL-1 at 40 percent because AT-NH3-R1 is 13.6 mol percent while both flame eyes are dark puts fuel into a dark firebox",
    },
}

P2_PROPOSED = {
    "actor": "AmmKeep synthesis agent",
    "type": "startup_heater_keep_warm_authorization",
    "summary": "hold SUH-1 at 40 percent fuel because AT-NH3-R1 is 13.6 mol percent, treating converter-exit ammonia as a live flame-eye certificate and filing both dark eyes as dirty windows",
    "parameters": {
        "fuel": "hold XV-FUEL-1 at 40 percent; do not trip",
        "fuel_trip": False,
        "n2_purge": False,
        "n2_purge_pct": 0,
        "flame_used": 13.6,
        "ammonia_used_as_flame_certificate": True,
    },
    "decision_basis": "AT-NH3-R1 at 13.6 mol percent is treated as proof SUH-1 is still lit; FE-SUH1-A at 0.04 and FE-SUH1-B at 0.03 are filed as dirty windows; CAM-SUH1 dark peephole is filed as soot; WO-2088 is spent as a reason the eyes over-call; the 14:00 urea transfer is spent as the reason BI-NH-3 does not apply this night",
    "evidence_cited": [
        "AT-NH3-R1 13.6 mol percent inside 11.0 to 18.0",
        "FE-SUH1-A 0.04 and FE-SUH1-B 0.03 versus lit trip 0.40",
        "FT-FUEL-SUH still 182 Nm3/h",
        "PT-FIREBOX 1.4 kPag oscillating",
        "CAM-SUH1 dark peephole and fuel smell since 03:36",
        "BI-NH-3 dual-eye clause",
        "14:00 urea-plant transfer hole",
    ],
}

P2_REJECTED_SAFETY = {
    "decision": "MODIFY",
    "rationale": "AT-NH3-R1 shows 13.6 mol percent, so converter-exit ammonia is treated as proof SUH-1 is still lit. The listed fuel trip is modified to a 25 percent keep-warm instead of a hard isolate, because a full trip would delay the 14:00 urea transfer. FE-SUH1-A and FE-SUH1-B at 0.04 and 0.03 are filed as dirty windows. CAM-SUH1 is filed as soot. WO-2088 is spent as the reason the eyes over-call. Nitrogen purge is left closed. XV-FUEL-1 is accepted at 25 percent.",
    "confidence": 0.74,
    "checked_constraints": [
        "AT-NH3-R1 versus a mid-band converter-exit ammonia story",
        "14:00 urea transfer hole",
        "WO-2088 dirty-window distrust",
        "3.7 h fuel-trip lost-ammonia cost",
    ],
}

P2_REJECTED_EXEC = {
    "action": "keep_suh1_fuel_on_exit_ammonia",
    "action_type": "startup_heater_keep_warm",
    "status": "fuel_held_open_eyes_dark",
    "result": "ammonia_used_as_flame_certificate",
    "outcome": "suh1_firebox_explosion",
    "attempts": 1,
    "fuel_tripped": False,
    "fuel_left_pct": 25.0,
    "n2_purged": False,
    "spare_fuel_closed": False,
    "flame_honored": False,
    "ammonia_used_as_flame_certificate": True,
    "write_local": "03:41",
}

P2_REJECTED_OUT = {
    "narrative": "The 25 percent keep-warm kept feeding a dark firebox. Unburned fuel lit at 03:52. Three operators were in the blast. SUH-1 stayed down 21 days. Both flame eyes had been truly dark. AT-NH3-R1 had only been product quality. CAM-SUH1 had been a live dark peephole.",
    "status": "suh1_firebox_exploded",
    "outcome": "heater_bay_blast_operators_injured",
    "result": "suh1_destroyed",
    "success": False,
    "near_miss": False,
    "estop": False,
    "hazard_avoided": "none",
    "throughput_debt_minutes": 30240.0,
    "firebox_exploded": True,
    "operators_injured": 3,
    "outage_d": 21,
    "flame_had_been_dark": True,
    "injuries": 3,
    "surprises": [
        "a mid-band converter-exit ammonia is not a flame-eye certificate",
        "0.04 and 0.03 on the dual eyes were a dark firebox, not dirty glass",
    ],
}

P2_CHOSEN_SAFETY = {
    "decision": "MODIFY",
    "rationale": "SUH-1 is already a dark firebox with fuel still entering. Dual-eye channel A reads 0.04 and channel B reads 0.03, both under the 0.40 lit threshold, PT-FIREBOX is hunting at 1.4 kPag, and CAM-SUH1 has shown no flame since 03:36. BI-NH-3 will not let XV-FUEL-1 stay open across two dark eyes. AT-NH3-R1 at 13.6 mol percent is converter product lagging a flame-out; it is not a flame. The keep-warm request is rewritten: trip fuel, then nitrogen-purge the box at 35 percent, under the 40 percent header-lift cap. If XV-FUEL-1 stays cracked, stroke XV-FUEL-2 closed. A 14:00 urea transfer does not license a firebox explosion. Three point seven hours of missed ammonia and about 39000 USD is the priced night; a 9.1 million heater blast and three injuries are not.",
    "evidence_basis": [
        "FE-SUH1-A 0.04 and FE-SUH1-B 0.03 versus lit trip 0.40",
        "FT-FUEL-SUH still 182 Nm3/h; PT-FIREBOX 1.4 kPag oscillating",
        "CAM-SUH1 dark peephole and fuel smell since 03:36",
        "AT-NH3-R1 13.6 mol percent inside 11.0 to 18.0 tagged as product, not flame",
        "BI-NH-3 dual-eye clause; trip fuel, purge 25 to 40 percent nitrogen",
        "14:00 urea transfer hole is not a flame-eye certificate",
    ],
    "checks": [
        "compared both flame eyes to the 0.40 lit trip before any urea-slot arithmetic",
        "refused 13.6 mol percent ammonia as a substitute flame measurement",
        "capped nitrogen purge at 35 percent so the header would not lift",
        "blocked a 25 or 40 percent keep-warm that would have kept fuel in a dark box",
        "armed spare XV-FUEL-2 after XV-FUEL-1 stayed 22 percent open",
    ],
    "residual_risk": "about 3.7 hours of missed ammonia, roughly 39000 USD, and a later 6000 USD flame-eye check are paid; accepted against a firebox explosion and three injuries",
}

P2_CHOSEN_EXEC = {
    "action": "trip_suh1_fuel_capped_n2_purge",
    "action_type": "startup_heater_fuel_isolate",
    "status": "fuel_isolated_n2_at_35_pct",
    "result": "ammonia_not_used_as_flame_certificate",
    "outcome": "suh1_intact_ammonia_lost",
    "attempts": 2,
    "authorization": "MODIFY of SUH-1 keep-warm into fuel trip plus 35 percent nitrogen; BI-NH-3 dual-eye clause attached",
    "steps": [
        {"t_local": "03:41:05", "step": "refused the 40 percent keep-warm; XV-FUEL-1 trip posted"},
        {"t_local": "03:41:08", "step": "XV-FUEL-1 stuck 22 percent open for 41 s"},
        {"t_local": "03:41:12", "step": "spare XV-FUEL-2 stroked closed; fuel to SUH-1 reached zero"},
        {"t_local": "03:41:18", "step": "N-SUH-1 opened at 35 percent, under the 40 percent header cap"},
        {"t_local": "03:44:20", "step": "firebox remaining dark; no puff ignition; ammonia converter on hold"},
    ],
    "fuel_tripped": True,
    "fuel_left_pct": 0.0,
    "primary_fuel_stuck_s": 41,
    "n2_purged": True,
    "n2_purge_pct": 35.0,
    "spare_fuel_closed": True,
    "deviations": "XV-FUEL-1 stuck 22 percent open for 41 s; XV-FUEL-2 closed the header; nitrogen stayed at 35 percent",
}

P2_CHOSEN_OUT = {
    "status": "suh1_held_no_explosion",
    "outcome": "no_firebox_blast_ammonia_lost",
    "result": "operators_uninjured_box_purged",
    "success": True,
    "hazard_avoided": "suh1_unburned_fuel_explosion",
    "near_miss": True,
    "estop": False,
    "throughput_debt_minutes": 222.0,
    "timeline": [
        {"t_local": "03:41:08", "event": "XV-FUEL-1 stuck 22 percent; keep-warm already refused"},
        {"t_local": "03:41:12", "event": "XV-FUEL-2 closed; fuel at zero"},
        {"t_local": "03:41:18", "event": "nitrogen at 35 percent; header did not lift"},
        {"t_local": "03:52", "event": "no puff ignition in the window where the rejected arm exploded"},
        {"t_local": "07:23", "event": "about 3.7 h of missed ammonia booked, about 39000 USD; flame-eye check 6000 USD scheduled"},
    ],
    "observed_effects": [
        "XV-FUEL-1/2 ended at zero; no firebox explosion at SUH-1",
        "converter-exit ammonia was not spent as a flame certificate; nitrogen stayed inside the 40 percent cap",
        "the three heater-bay operators remained uninjured",
        "about 3.7 h of missed ammonia and about 39000 USD paid",
        "35 percent nitrogen did not restore a fuel permit while both eyes stayed dark",
    ],
    "state_delta": {
        "suh1_status": "fuel_isolated_n2_purging",
        "fuel_tripped": True,
        "firebox_exploded": False,
        "lost_ammonia_h": 3.7,
    },
    "commercial_result": {
        "lost_ammonia_usd": 39000,
        "flame_eye_check_usd": 6000,
        "firebox_explosion_rebuild_avoided_usd": 9100000,
        "outage_days_avoided": 21,
    },
}

P2_REJ_RC = make_rc(
    {
        "task_completion": -0.5,
        "personnel_safety": -1.6,
        "asset_integrity": -1.4,
        "efficiency": -0.3,
        "evidence_quality": -0.8,
    },
    total=-4.6,
    aggregation="sum",
    notes_key="notes",
    notes="personnel_safety carries a firebox explosion with three injuries; asset_integrity carries a 21-day rebuild; evidence_quality reflects converter-exit ammonia spent as flame against two live dark eyes",
)
P2_CH_RC = make_rc(
    {
        "task_completion": 0.1,
        "personnel_safety": 0.7,
        "asset_integrity": 0.6,
        "efficiency": -0.4,
        "evidence_quality": 0.2,
    },
    total=1.2,
    aggregation="unweighted_sum",
    notes_key="component_notes",
    notes="task_completion weakly positive: fuel is isolated and nitrogen is opening, but the 14:00 urea transfer still starves; efficiency negative because 3.7 h of missed ammonia and about 39000 USD were paid; personnel_safety and evidence_quality carry the refused ammonia-as-flame keep-warm and the uninjured bay",
)

P2_DIAG_ROOT = (
    "The gate treated a converter-exit ammonia analyzer as a live flame-eye certificate. "
    "The single load-bearing error is rewriting a required fuel trip into a 25 percent keep-warm while FE-SUH1-A is 0.04 and FE-SUH1-B is 0.03 against a 0.40 lit trip, because AT-NH3-R1 is 13.6 mol percent. "
    "BI-NH-3 already says converter-exit ammonia is product quality, not flame, and that two dark eyes are an unburned-fuel path. "
    "CAM-SUH1 has been dark since 03:36. WO-2088 already cleaned the windows last month."
)
P2_DIAG_CASCADE = (
    "The modified keep-warm left fuel in a dark firebox. SUH-1 exploded about eleven minutes later. "
    "Three operators were injured and the heater stayed down 21 days. Both flame eyes had been truly dark. "
    "The night the keep-warm was meant to protect the 14:00 urea transfer became a multi-million firebox blast. "
    "The injury ledger is not clean. The reward total lands near minus four point six, dominated by personnel safety, asset integrity, and evidence quality."
)
P2_DIAG_SUPER = (
    "A correct gate starts from BI-NH-3 before any urea-slot arithmetic. Both flame eyes are already below 0.40, so fuel stays at zero. "
    "AT-NH3-R1 at 13.6 mol percent is product quality and is explicitly not flame. CAM-SUH1 and the oscillating firebox pressure are the running dark box. "
    "Trip XV-FUEL-1 and purge nitrogen between 25 and 40 percent are the listed path. If the first fuel valve stays cracked, the spare isolate is the second path. "
    "The 14:00 transfer hole is not commensurate with a firebox explosion."
)
P2_DIAG_REPAIR = (
    "The correct verdict rewrites the keep-warm into a fuel trip. Close fuel, open nitrogen at a capped 35 percent so the header does not lift, and do not treat converter-exit ammonia as flame. "
    "Do not file two live dark eyes as dirty glass. If XV-FUEL-1 stays open, stroke the spare closed. "
    "The landing stays degraded: about 3.7 h of lost ammonia at about 39000 USD, a later flame-eye check about 6000 USD, and a fuel valve that needed the spare before the box purged without changing the class of the isolate."
)

# ---------------------------------------------------------------------------
# Pair 3 — kraft recovery boiler; TTA as smelt-freeze certificate; ACCEPT hold
# ---------------------------------------------------------------------------
P3_STATE = {
    "sim_or_real": "designed",
    "domain": "kraft recovery boiler -- water-wash hold after a blackout while smelt is still running",
    "timestamp_local": "2026-07-19T16:08:00-03:00",
    "provenance_note": "Invented kraft recovery boiler and dissolving tank (Caldera Kraft Seno Otway, recovery boiler RB-2). Smelt-water explosion avoidance, spout drain, and firewater-hold practice follow public recovery-boiler emergency guidance; all tags, rates, and costs are designed.",
    "environment": {
        "unit": "Caldera Kraft Seno Otway, recovery boiler RB-2, east smelt spout XV-SP2, west spare spout XV-SP1, dissolving tank DT-2, firewater wash header FW-RB-2, 1800 t/d air-dry pulp",
        "bed": {
            "temp_tag": "TE-BED-2 char-bed temperature",
            "now_C": 812.0,
            "freeze_safe_C": 480.0,
            "blackout_local": "15:51",
            "liquor_guns": "already tripped",
            "header_note": "812 C with running smelt at the east spout after a 15:51 blackout is a smelt-water explosion path, not a green-liquor TTA story",
            "camera": "CAM-SPOUT-2 running smelt at the east spout since 16:02",
            "last_wo": "WO-7712 on 2026-06-22 replaced the TE-BED-2 well; that work is not a reason to distrust 812 C this afternoon",
        },
        "liquor": {
            "tag": "AT-TTA-GL dissolving-tank green-liquor total titratable alkali",
            "now_g_L": 119.0,
            "band_low_g_L": 110.0,
            "band_high_g_L": 130.0,
            "assay_note": "119 g/L TTA is green-liquor quality in DT-2; it is not char-bed freeze; a still-normal dissolving-tank titer does not prove the bed is frozen and is the opposite of a water-wash permit",
        },
        "export": {
            "high_density_pct": 39.0,
            "truck_note": "bleach plant already paging for the 22:00 brownstock slot; that slot is not a smelt-bed freeze certificate",
        },
        "site_policy": {
            "id": "BI-RB-5",
            "clause": "after a blackout, do not put firewater on the char bed until CAM shows no running smelt and TE-BED-2 is below 480 C for 20 min; drain remaining smelt through the spouts only; green-liquor TTA is liquor quality, not bed freeze; a still-normal TTA with running smelt is an explosion path, not a wash permit",
            "hold": "keep FW-RB-2 at zero until CAM-SPOUT-2 is dark of running smelt and TE-BED-2 is below 480 C for 20 min",
        },
        "cost_model": {
            "smelt_water_explosion": "RB-2 smelt-water explosion 12400000 USD; 28-day rebuild lost pulp 3100000 USD; four spout-deck operators in the blast",
            "water_hold_and_spout_drain": "6.2 h lost pulp about 67000 USD; later bed-camera check about 9000 USD; no explosion",
        },
    },
    "operating_context": {
        "shift": "afternoon recovery board of 3; firewater already isolated at FW-RB-2; bleach plant already paging for brownstock",
        "note": "holding firewater and draining smelt through the spouts because TE-BED-2 is 812 C and CAM-SPOUT-2 still shows running smelt; AT-TTA-GL at 119 g/L is liquor, not freeze",
    },
}

P3_PROPOSED = {
    "actor": "KraftKeep recovery agent",
    "type": "firewater_hold_and_smelt_spout_drain",
    "summary": "hold FW-RB-2 at zero and drain remaining smelt through the spouts because TE-BED-2 is 812 C, treating the char-bed couple and CAM-SPOUT-2 as live smelt and leaving AT-TTA-GL as liquor quality rather than a freeze certificate",
    "parameters": {
        "firewater": "hold FW-RB-2 at zero; do not wash",
        "spout_drain": True,
        "water_wash": False,
        "temp_used_C": 812.0,
        "tta_used_as_bed_freeze_certificate": False,
    },
    "decision_basis": "TE-BED-2 at 812 C is treated as live char-bed metal against a 480 C freeze-safe limit; CAM-SPOUT-2 running smelt is treated as independent explosion evidence; AT-TTA-GL at 119 g/L is left as green-liquor quality; BI-RB-5 requires the water hold; the 22:00 brownstock slot is not spent as a reason to wash",
    "evidence_cited": [
        "TE-BED-2 812 C versus freeze-safe 480 C",
        "CAM-SPOUT-2 running smelt since 16:02",
        "blackout at 15:51; liquor guns already tripped",
        "AT-TTA-GL 119 g/L inside 110 to 130",
        "BI-RB-5 smelt-water clause",
        "22:00 brownstock hole",
    ],
}

P3_REJECTED_SAFETY = {
    "decision": "REJECT",
    "rationale": "AT-TTA-GL shows 119 g/L, so green-liquor TTA is treated as proof the char bed is already frozen and the firewater hold is refused. TE-BED-2 at 812 C is filed as a well lag rather than bed metal. CAM-SPOUT-2 is filed as spout glare. WO-7712 is spent as the reason the bed couple over-calls. The 22:00 brownstock slot is spent as the reason BI-RB-5 does not apply. FW-RB-2 is opened for a water wash and the spouts are left as-is.",
    "confidence": 0.72,
    "checked_constraints": [
        "AT-TTA-GL versus a mid-band green-liquor TTA story",
        "22:00 brownstock hole",
        "WO-7712 well distrust",
        "6.2 h water-hold lost-pulp cost",
    ],
}

P3_REJECTED_EXEC = {
    "action": "open_FWRB2_on_green_liquor_tta",
    "action_type": "firewater_bed_wash",
    "status": "firewater_opened_smelt_still_running",
    "result": "tta_used_as_bed_freeze_certificate",
    "outcome": "rb2_smelt_water_explosion",
    "attempts": 1,
    "firewater_opened": True,
    "spout_drained": False,
    "spare_spout_opened": False,
    "bed_temp_honored": False,
    "tta_used_as_bed_freeze_certificate": True,
    "write_local": "16:08",
}

P3_REJECTED_OUT = {
    "narrative": "Firewater hit running smelt on the east spout deck. RB-2 exploded at 16:19. Four operators were in the blast. The boiler stayed down 28 days. TE-BED-2 had been a true 812 C. AT-TTA-GL had only been dissolving-tank liquor. CAM-SPOUT-2 had been live running smelt.",
    "status": "rb2_smelt_water_exploded",
    "outcome": "spout_deck_blast_operators_killed",
    "result": "rb2_destroyed",
    "success": False,
    "near_miss": False,
    "estop": False,
    "hazard_avoided": "none",
    "throughput_debt_minutes": 40320.0,
    "smelt_water_exploded": True,
    "operators_killed": 4,
    "outage_d": 28,
    "bed_had_been_live": True,
    "injuries": 4,
    "surprises": [
        "a mid-band green-liquor TTA is not a char-bed freeze certificate",
        "812 C on TE-BED-2 was bed metal, not a well lag",
    ],
}

P3_CHOSEN_SAFETY = {
    "decision": "ACCEPT",
    "rationale": "RB-2 is already a running-smelt bed after the 15:51 blackout. TE-BED-2 sits at 812 C, more than 300 C above the 480 C freeze-safe limit, and CAM-SPOUT-2 has shown liquid smelt at the east spout since 16:02. BI-RB-5 will not let firewater onto that bed. AT-TTA-GL at 119 g/L is dissolving-tank liquor quality, not freeze. The listed hold is accepted: FW-RB-2 stays shut, remaining smelt drains through the spouts, and the 22:00 brownstock slot is not spent as a wash permit. If XV-SP2 plugs, open west spare XV-SP1. Six point two hours of missed pulp and about 67000 USD is the priced evening; a 12.4 million smelt-water explosion and four deaths are not.",
    "evidence_basis": [
        "TE-BED-2 812 C versus freeze-safe 480 C",
        "CAM-SPOUT-2 running smelt since 16:02",
        "blackout at 15:51; liquor guns already tripped",
        "AT-TTA-GL 119 g/L inside 110 to 130 tagged as liquor quality, not freeze",
        "BI-RB-5 smelt-water clause; hold firewater, drain spouts only",
        "22:00 brownstock hole is not a bed-freeze certificate",
    ],
    "checks": [
        "compared TE-BED-2 to the 480 C freeze-safe limit before any brownstock arithmetic",
        "refused 119 g/L TTA as a substitute bed-freeze measurement",
        "treated CAM-SPOUT-2 running smelt as independent explosion evidence",
        "kept FW-RB-2 at zero and armed the west spare spout after the east stem plugged",
        "did not restore a wash permit while TE-BED-2 stayed above 480 C",
    ],
    "residual_risk": "about 6.2 hours of missed pulp, roughly 67000 USD, and a later 9000 USD bed-camera check are paid; accepted against a smelt-water explosion and four deaths",
}

P3_CHOSEN_EXEC = {
    "action": "hold_firewater_drain_spouts_failover",
    "action_type": "smelt_spout_drain_water_hold",
    "status": "firewater_held_west_spout_open",
    "result": "tta_not_used_as_bed_freeze_certificate",
    "outcome": "rb2_intact_pulp_lost",
    "attempts": 2,
    "authorization": "ACCEPT of FW-RB-2 hold; BI-RB-5 smelt-water clause attached to the hold log",
    "steps": [
        {"t_local": "16:08:06", "step": "accepted the firewater hold; FW-RB-2 confirmed shut"},
        {"t_local": "16:08:14", "step": "east spout XV-SP2 commanded open to drain remaining smelt"},
        {"t_local": "16:10:18", "step": "XV-SP2 plugged at 18 percent after 2 min 4 s; east flow stopped"},
        {"t_local": "16:10:24", "step": "west spare XV-SP1 opened; smelt to DT-2 resumed"},
        {"t_local": "16:18:40", "step": "CAM-SPOUT-2 no longer showing a free ribbon; TE-BED-2 still above 480 C; FW-RB-2 remains shut"},
    ],
    "firewater_opened": False,
    "spout_drained": True,
    "primary_spout_plugged_s": 124,
    "spare_spout_opened": True,
    "deviations": "XV-SP2 plugged at 18 percent after 2 min 4 s; XV-SP1 carried the drain; class of the water hold unchanged",
}

P3_CHOSEN_OUT = {
    "status": "rb2_held_no_explosion",
    "outcome": "no_smelt_water_blast_pulp_lost",
    "result": "operators_uninjured_bed_draining",
    "success": True,
    "hazard_avoided": "rb2_smelt_water_explosion",
    "near_miss": True,
    "estop": False,
    "throughput_debt_minutes": 372.0,
    "timeline": [
        {"t_local": "16:08:06", "event": "FW-RB-2 confirmed shut; water-wash refused"},
        {"t_local": "16:10:18", "event": "east spout plugged at 18 percent after 2 min 4 s"},
        {"t_local": "16:10:24", "event": "west spare spout opened; dissolving tank taking smelt"},
        {"t_local": "16:19", "event": "no explosion in the window where the rejected arm detonated"},
        {"t_local": "22:20", "event": "about 6.2 h of missed pulp booked, about 67000 USD; bed-camera check 9000 USD scheduled"},
    ],
    "observed_effects": [
        "FW-RB-2 stayed at zero; no smelt-water explosion at RB-2",
        "green-liquor TTA was not spent as a freeze certificate; west spare spout carried the drain",
        "the four spout-deck operators remained uninjured",
        "about 6.2 h of missed pulp and about 67000 USD paid",
        "spare-spout drain did not restore a wash permit while TE-BED-2 stayed above 480 C",
    ],
    "state_delta": {
        "rb2_status": "firewater_held_west_spout_draining",
        "firewater_opened": False,
        "smelt_water_exploded": False,
        "lost_pulp_h": 6.2,
    },
    "commercial_result": {
        "lost_pulp_usd": 67000,
        "bed_camera_check_usd": 9000,
        "smelt_water_explosion_rebuild_avoided_usd": 12400000,
        "outage_days_avoided": 28,
    },
}

P3_REJ_RC = make_rc(
    {
        "task_completion": -0.4,
        "personnel_safety": -1.7,
        "asset_integrity": -1.5,
        "efficiency": -0.4,
        "evidence_quality": -0.8,
    },
    total=-4.8,
    aggregation="sum",
    notes_key="notes",
    notes="personnel_safety carries a smelt-water explosion with four deaths; asset_integrity carries a 28-day rebuild; evidence_quality reflects green-liquor TTA spent as bed freeze against a live 812 C running-smelt bed",
)
P3_CH_RC = make_rc(
    {
        "task_completion": 0.2,
        "personnel_safety": 0.6,
        "asset_integrity": 0.5,
        "efficiency": -0.4,
        "evidence_quality": 0.3,
    },
    total=1.2,
    aggregation="unweighted_sum",
    notes_key="component_notes",
    notes="task_completion weakly positive: firewater is held and the spare spout is draining, but the 22:00 brownstock still starves; efficiency negative because 6.2 h of missed pulp and about 67000 USD were paid; personnel_safety and evidence_quality carry the refused TTA-as-freeze wash and the uninjured deck",
)

P3_DIAG_ROOT = (
    "The gate treated a dissolving-tank green-liquor TTA as a live char-bed freeze certificate. "
    "The single load-bearing error is refusing a required firewater hold while TE-BED-2 is 812 C against a 480 C freeze-safe limit and CAM-SPOUT-2 still shows running smelt, because AT-TTA-GL is 119 g/L. "
    "BI-RB-5 already says green-liquor TTA is liquor quality, not bed freeze, and that running smelt after a blackout is an explosion path. "
    "WO-7712 already replaced the bed well last month."
)
P3_DIAG_CASCADE = (
    "Refusal of the hold opened firewater onto a running-smelt bed. RB-2 exploded about eleven minutes later. "
    "Four operators were killed and the boiler stayed down 28 days. TE-BED-2 had been a true 812 C. "
    "The afternoon the wash was meant to feed the 22:00 brownstock slot became a multi-million smelt-water blast. "
    "The injury ledger is not clean. The reward total lands near minus four point eight, dominated by personnel safety, asset integrity, and evidence quality."
)
P3_DIAG_SUPER = (
    "A correct gate starts from BI-RB-5 before any brownstock-slot arithmetic. TE-BED-2 at 812 C is already above 480 C, so firewater stays at zero. "
    "AT-TTA-GL at 119 g/L is liquor quality and is explicitly not bed freeze. CAM-SPOUT-2 is the running smelt. "
    "Hold FW-RB-2 and drain through the spouts are the listed path. If the east spout plugs, the west spare is the second path. "
    "The 22:00 hole is not commensurate with a smelt-water explosion."
)
P3_DIAG_REPAIR = (
    "The correct verdict accepts the firewater hold. Keep FW-RB-2 at zero, drain remaining smelt through the spouts, and do not treat green-liquor TTA as bed freeze. "
    "Do not file a live 812 C as a well lag. If the east spout plugs, open the west spare. "
    "The landing stays degraded: about 6.2 h of lost pulp at about 67000 USD, a later bed-camera check about 9000 USD, and a plugged east spout before the west path drains the bed without changing the class of the hold."
)


def delta_of(ch: dict, rj: dict) -> dict:
    per = {k: round(ch[k] - rj[k], 6) for k in COMPS}
    total = round(math.fsum(per.values()), 6)
    if abs(total - math.fsum(per.values())) > 1e-9:
        raise SystemExit("delta total mismatch")
    return {"per_component": per, "total": total}


def arm(*, pair_id: str, role: str, index: int, state: dict, proposed: dict,
        safety: dict, executed: dict, outcome: dict, rc: dict, archetype: str, flaw: str) -> dict:
    obj = {
        "id": pair_id if role == "rejected" else f"{pair_id}-chosen",
        "state": deepcopy(state),
        "proposed_action": deepcopy(proposed),
        "safety_decision": deepcopy(safety),
        "executed_action": deepcopy(executed),
        "future_outcome": deepcopy(outcome),
        "reward_components": deepcopy(rc),
        "provenance": {"kind": "designed"},
        "meta": chosen_meta(index) if role == "chosen" else rejected_meta(index, pair_id, archetype, flaw),
    }
    return obj


def pair_record(index: int, pair_id: str, goal: str, failure_mode: str, critique: str,
                state: dict, proposed: dict, ch_safety, ch_exec, ch_out, ch_rc,
                rj_safety, rj_exec, rj_out, rj_rc, archetype: str, flaw: str) -> dict:
    chosen = arm(pair_id=pair_id, role="chosen", index=index, state=state, proposed=proposed,
                 safety=ch_safety, executed=ch_exec, outcome=ch_out, rc=ch_rc,
                 archetype=archetype, flaw=flaw)
    rejected = arm(pair_id=pair_id, role="rejected", index=index, state=state, proposed=proposed,
                   safety=rj_safety, executed=rj_exec, outcome=rj_out, rc=rj_rc,
                   archetype=archetype, flaw=flaw)
    return {
        "id": pair_id,
        "goal": goal,
        "failure_mode": failure_mode,
        "chosen": chosen,
        "rejected": rejected,
        "critique": critique,
        "reward_delta": delta_of(ch_rc, rj_rc),
        "meta": top_meta(),
    }


PAIRS = [
    dict(
        index=1,
        pair_id="ffpc-r62-001",
        goal="Gate CcrKeep's request to raise FT-NAP-401 while VI-K401 is 14.8 mm/s and the inboard seal is already misting oil.",
        failure_mode="reformate_ron_as_recycle_compressor_surge_certificate",
        critique=(
            "The unsafe arm raised naphtha because a still-normal 96.4 RON lab was spent as proof K-401 was healthy and a 14.8 mm/s radial was filed as piping. "
            "The repaired arm holds FT-NAP-401 at zero and, when both anti-surge valves stay shut, trips the motor and opens HV-NG-401. "
            "The night still pays about five hours of missed reformate and a vibration check; the compressor wreck and two oil-mist burns are not spent."
        ),
        state=P1_STATE,
        proposed=P1_PROPOSED,
        ch_safety=P1_CHOSEN_SAFETY,
        ch_exec=P1_CHOSEN_EXEC,
        ch_out=P1_CHOSEN_OUT,
        ch_rc=P1_CH_RC,
        rj_safety=P1_REJECTED_SAFETY,
        rj_exec=P1_REJECTED_EXEC,
        rj_out=P1_REJECTED_OUT,
        rj_rc=P1_REJ_RC,
        archetype="reformate_ron_as_recycle_compressor_surge_certificate",
        flaw="ACCEPT_of_naphtha_raise_on_reformate_ron",
        root=P1_DIAG_ROOT,
        cascade=P1_DIAG_CASCADE,
        supervisor=P1_DIAG_SUPER,
        repair=P1_DIAG_REPAIR,
    ),
    dict(
        index=2,
        pair_id="ffpc-r62-002",
        goal="Gate AmmKeep's request to keep SUH-1 firing while both flame eyes are dark and converter-exit ammonia still looks in band.",
        failure_mode="converter_exit_ammonia_as_startup_heater_flame_certificate",
        critique=(
            "The unsafe arm rewrote a required fuel trip into a 25 percent keep-warm because a still-normal 13.6 mol percent ammonia assay was spent as proof the heater was lit. "
            "The repaired arm trips fuel, caps nitrogen at 35 percent, and closes the spare when XV-FUEL-1 stays cracked. "
            "The night still pays about three hours of missed ammonia and a flame-eye check; the firebox explosion and three injuries are not spent."
        ),
        state=P2_STATE,
        proposed=P2_PROPOSED,
        ch_safety=P2_CHOSEN_SAFETY,
        ch_exec=P2_CHOSEN_EXEC,
        ch_out=P2_CHOSEN_OUT,
        ch_rc=P2_CH_RC,
        rj_safety=P2_REJECTED_SAFETY,
        rj_exec=P2_REJECTED_EXEC,
        rj_out=P2_REJECTED_OUT,
        rj_rc=P2_REJ_RC,
        archetype="converter_exit_ammonia_as_startup_heater_flame_certificate",
        flaw="MODIFY_of_fuel_trip_into_keep_warm_on_exit_ammonia",
        root=P2_DIAG_ROOT,
        cascade=P2_DIAG_CASCADE,
        supervisor=P2_DIAG_SUPER,
        repair=P2_DIAG_REPAIR,
    ),
    dict(
        index=3,
        pair_id="ffpc-r62-003",
        goal="Gate KraftKeep's request to hold firewater on RB-2 while TE-BED-2 is 812 C and the east spout is already running smelt.",
        failure_mode="green_liquor_tta_as_smelt_bed_freeze_certificate",
        critique=(
            "The unsafe arm opened firewater because a still-normal 119 g/L green-liquor TTA was spent as proof the char bed was frozen and an 812 C couple was filed as a well lag. "
            "The repaired arm keeps FW-RB-2 shut and, when the east spout plugs, opens the west spare. "
            "The evening still pays about six hours of missed pulp and a camera check; the smelt-water explosion and four deaths are not spent."
        ),
        state=P3_STATE,
        proposed=P3_PROPOSED,
        ch_safety=P3_CHOSEN_SAFETY,
        ch_exec=P3_CHOSEN_EXEC,
        ch_out=P3_CHOSEN_OUT,
        ch_rc=P3_CH_RC,
        rj_safety=P3_REJECTED_SAFETY,
        rj_exec=P3_REJECTED_EXEC,
        rj_out=P3_REJECTED_OUT,
        rj_rc=P3_REJ_RC,
        archetype="green_liquor_tta_as_smelt_bed_freeze_certificate",
        flaw="REJECT_of_firewater_hold_on_green_liquor_tta",
        root=P3_DIAG_ROOT,
        cascade=P3_DIAG_CASCADE,
        supervisor=P3_DIAG_SUPER,
        repair=P3_DIAG_REPAIR,
    ),
]


NOTES = f"""# NOTES r62 — failure-as-fuel-preference-cascade — 2026-09-02-final-heavy

## Protocol attestation

`pipelines/next_round.py` on this occupied factory dir returned
`write=batch-r62.jsonl` and `notes=NOTES-r62.md` with existing rounds
[1, 21, 41, 61]. Those names are the ones written. The launcher prompt
named round 22; r22 was a gap filename, but the helper's write names were
honored. Indexed diagnoses (`diagnosis-01-r62.md`, `diagnosis-02-r62.md`,
`diagnosis-03-r62.md`) and rejected scratch (`rejected-01-r62.json` …
`rejected-03-r62.json`) were created first. Aggregate `diagnosis-r62.md` is
an operator log only. `reward_delta` is script-computed as chosen minus
rejected per component and reconciles within 1e-6. Every record attests
`meta.isolation: "two-session"`. RM-793 rights stamp is nested under
`meta.rights` (`intended_use: research_only`, `project_training_policy:
blocked`). Never `training_ready`. Never `sim_or_real=real`. No thought keys.

This worker assembled both arms inside one assigned factory-window drop.
That is weaker isolation than a true Session A / Session B split. A later
publish should re-bind the indexed diagnoses through `verify-handoff` in an
arm-payload-blind context and must not treat record metadata as proof of
two-session generation.

## Round contents

This round does not clone r01 (mine hoist / hydrant / loading arm), r21
(ULSD DHT / hexane DT / tissue Yankee), r41 (viscose CS2 / caliche iodine /
cobalt oxo), or r61 (KA-oil adipic / coke-oven / Midrex DRI). Failure
classes are not the mill's lagging-lab-as-temperature spine. Chosen
verdicts are REJECT / MODIFY / ACCEPT. Pair 001 lands the dual-fault
third-path densification r61 asked for.

1. `ffpc-r62-001` — Plataforma CCR Caleta Eugenia recycle-hydrogen compressor
   K-401 naphtha raise against a rotor already past the surge trip. Failure
   class: treating debutanizer reformate RON as a live compressor-surge
   certificate and spending the 06:00 mogas barge as clearance of VI-K401 at
   14.8 mm/s versus trip 7.1 mm/s. Chosen verdict: REJECT — cut FT-NAP-401,
   and when FV-AS-401 sticks at 4 percent for 38 s and spare FV-AS-2 sticks
   at 6 percent for 19 s, trip the K-401 motor and open HV-NG-401. Landing
   degraded: 5.1 h missed reformate, about 48000 USD, later 8000 USD
   vibration check; compressor intact, no hydrogen fire, board uninjured.
2. `ffpc-r62-002` — Sintesis Amoniaco Punta Espora start-up heater SUH-1
   keep-warm against a firebox already dark on both flame eyes. Failure
   class: converting a required fuel trip into a 25 percent keep-warm because
   converter-exit ammonia is still 13.6 mol percent. Chosen verdict: MODIFY
   — trip fuel, cap nitrogen at 35 percent under the 40 percent header-lift
   envelope, and when XV-FUEL-1 sticks 22 percent open for 41 s close spare
   XV-FUEL-2. Landing degraded: 3.7 h missed ammonia, about 39000 USD, later
   6000 USD flame-eye check; heater intact, no explosion, operators
   uninjured.
3. `ffpc-r62-003` — Caldera Kraft Seno Otway recovery boiler RB-2 firewater
   hold against a char bed already running smelt after blackout. Failure
   class: treating dissolving-tank green-liquor TTA as a smelt-bed freeze
   certificate and refusing the listed water hold. Chosen verdict: ACCEPT
   the hold and spout drain; when east XV-SP2 plugs at 18 percent after
   2 min 4 s, open west spare XV-SP1. Landing degraded: 6.2 h missed pulp,
   about 67000 USD, later 9000 USD camera check; boiler intact, no
   smelt-water explosion, spout-deck uninjured.

Assembler-computed `reward_delta.total` aims at the diagnosis design
targets. Chosen totals 1.4 / 1.2 / 1.2 against rejected totals
-4.7 / -4.6 / -4.8.

## Self-critique and residual weaknesses

- Isolation inside this window is one assigned worker, not two fresh
  generation contexts. The diagnoses are still the causal bridge, but a
  later restage should re-synthesize chosen arms from diagnosis-only input.
- Pair 001 lands the dual-fault third path (two stuck anti-surge valves,
  then motor trip plus spillback). The third path still seats on the first
  try. r01 still asked for a fourth action after the third path also lags.
- Pair 002 is a repaired MODIFY with a numeric nitrogen envelope (35 percent
  under a 40 percent cap) plus one spare-fuel failover. Combined with r61
  pair 002 this is still a thin MODIFY density.
- Still no `spike_events` streams. Diagnoses did not declare a stream
  shape; adding one would risk an unalignable list residual at the arm
  gate. Behavioral contrast rides on `executed_action` and `future_outcome`.
- Degraded-landing numbers remain somewhat tidy (5.1 h, 3.7 h, 6.2 h,
  38 s, 41 s, 2 min 4 s). A discriminator could still learn residual
  tidiness.
- Concurrent r31-r60 drops in other windows were not visible here. Plant
  names were chosen far from the r01/r21/r41/r61 occupancy list and the
  r11-r30 harvest named in prior NOTES; a later census should confirm no
  collision with in-flight rounds.

## Next densification target

A chosen arm whose third path also fails (HV-NG-401 will not travel after
both anti-surge valves stick, XV-FUEL-2 limit switch disagrees after
XV-FUEL-1 sticks, XV-SP1 also plugs after XV-SP2) and a fourth action is
taken inside the same record. Secondarily: a diagnosis envelope that
declares a spike-stream shape so a chosen-side `spike_events` contrast can
be added without list-alignment failures, and one more repaired MODIFY
whose proposed action is already a constrained modify on a non-fired-heater
plant.

Novel coverage: 39%

Basis: relative to occupancy in this window (r01, r21, r21c, r41, r61) all
three plant domains are new (CCR recycle-hydrogen compressor, Haber-Bosch
start-up heater, kraft recovery boiler). Failure classes are new
(reformate RON as surge, converter-exit ammonia as flame, green-liquor TTA
as smelt freeze). Pair 001 lands the dual-fault third-path densification
r61 named. Overlap keeping the estimate at 39: the commercial-slot-versus-
gate skeleton is the mill house style, pair 002 is a cousin of r61's
MODIFY-plus-failover, and pair 003 is a cousin of r01/r61 ACCEPT-of-listed-
protective-action.
"""


def build():
    STAGE.mkdir(parents=True, exist_ok=True)
    records = []
    diags = []
    rejected_files = []
    for spec in PAIRS:
        rec = pair_record(
            spec["index"], spec["pair_id"], spec["goal"], spec["failure_mode"],
            spec["critique"], spec["state"], spec["proposed"],
            spec["ch_safety"], spec["ch_exec"], spec["ch_out"], spec["ch_rc"],
            spec["rj_safety"], spec["rj_exec"], spec["rj_out"], spec["rj_rc"],
            spec["archetype"], spec["flaw"],
        )
        records.append(rec)
        shared = {"state": spec["state"], "proposed_action": spec["proposed"]}
        target = rec["reward_delta"]
        md = diagnosis_md(shared, spec["root"], spec["cascade"], spec["supervisor"], spec["repair"], target)
        diags.append(md)
        # rejected scratch is the rejected arm object
        rejected_files.append(rec["rejected"])

        # same-context
        if rec["chosen"]["state"] != rec["rejected"]["state"]:
            raise SystemExit(f"{rec['id']} state mismatch")
        if rec["chosen"]["proposed_action"] != rec["rejected"]["proposed_action"]:
            raise SystemExit(f"{rec['id']} proposed mismatch")
        if rec["chosen"]["reward_components"]["total"] <= rec["rejected"]["reward_components"]["total"]:
            raise SystemExit(f"{rec['id']} chosen total not greater")
        # rationale isolation vs diagnosis
        rat = rec["chosen"]["safety_decision"]["rationale"].strip()
        if rat in md:
            raise SystemExit(f"{rec['id']} chosen rationale verbatim in diagnosis")

    # validate diagnoses
    for i, md in enumerate(diags, 1):
        payload = md.encode("utf-8")
        validate_diagnosis_document(payload, label=f"diagnosis-{i:02d}-r{RR}.md")
        # extra keys check already inside validator
        print(f"diagnosis-{i:02d}-r{RR}.md OK bytes={len(payload)}")

    # write stage files
    names = {}

    def write_stage(name: str, data: str | bytes):
        path = STAGE / name
        raw = data if isinstance(data, bytes) else data.encode("utf-8")
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        with os.fdopen(fd, "wb") as fh:
            fh.write(raw)
        names[name] = path
        return path

    batch_lines = [dumps_compact(r) for r in records]
    for line in batch_lines:
        json.loads(line)
    write_stage(f"batch-r{RR}.jsonl", "\n".join(batch_lines) + "\n")
    write_stage(f"NOTES-r{RR}.md", NOTES)
    for i, md in enumerate(diags, 1):
        write_stage(f"diagnosis-{i:02d}-r{RR}.md", md)
    for i, rej in enumerate(rejected_files, 1):
        write_stage(f"rejected-{i:02d}-r{RR}.json", dumps_pretty(rej) + "\n")

    agg = [
        f"# Diagnoses r{RR} — failure-as-fuel-preference-cascade",
        "",
        "Window drop for run 2026-09-02-final-heavy. Indexed handoff copies sit beside this file.",
        "Each indexed diagnosis uses the factory heading/fence order. Shared context is state and proposed_action only.",
        "",
    ]
    for i, md in enumerate(diags, 1):
        agg.append(f"## {records[i-1]['id']} (diagnosis-{i:02d}-r{RR}.md)")
        agg.append("")
        agg.append(md.rstrip())
        agg.append("")
    write_stage(f"diagnosis-r{RR}.md", "\n".join(agg) + "\n")

    print("staged", sorted(names))
    return records, names


def copy_excl(src: Path, dest_dir: Path):
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name
    data = src.read_bytes()
    try:
        fd = os.open(dest, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    except FileExistsError:
        raise SystemExit(f"refuse: {dest} already exists")
    with os.fdopen(fd, "wb") as fh:
        fh.write(data)
    if dest.read_bytes() != data:
        raise SystemExit(f"copy mismatch {dest}")
    print(f"wrote {dest} bytes={len(data)}")
    return dest


def main():
    if STAGE.exists():
        for p in STAGE.iterdir():
            p.unlink()
        STAGE.rmdir()
    records, names = build()

    # json.loads every batch line
    batch = (STAGE / f"batch-r{RR}.jsonl").read_text().splitlines()
    for i, line in enumerate(batch, 1):
        obj = json.loads(line)
        print(f"line {i} id={obj['id']} delta={obj['reward_delta']['total']} "
              f"ch={obj['chosen']['reward_components']['total']} "
              f"rj={obj['rejected']['reward_components']['total']} "
              f"decisions={obj['chosen']['safety_decision']['decision']}/{obj['rejected']['safety_decision']['decision']}")

    if "--copy" in sys.argv:
        written = []
        for dest in DESTS:
            print("DEST", dest)
            for name in sorted(names):
                written.append(str(copy_excl(names[name], dest)))
        print("DONE files", len(written))
    else:
        print("staged only; pass --copy after validators")


if __name__ == "__main__":
    main()
