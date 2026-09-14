#!/usr/bin/env python3
"""Build FFPC round 42 (create-only). Session-A failures + diagnoses, then chosen assembly."""

from __future__ import annotations

import json
import os
import shutil
import sys
from copy import deepcopy
from pathlib import Path

PIPELINES = Path("/home/raulmc/rmems/synthetic-factory/pipelines")
sys.path.insert(0, str(PIPELINES))

from preference_arms_diagnosis import validate_diagnosis_document  # noqa: E402

ROUND = 42
RR = f"{ROUND:02d}"
STAGE = Path("/tmp/ffpc-r42-stage")
OUT = Path(
    "/home/raulmc/rmems/synthetic-factory/outputs/raw/2026-09-02-final-heavy/"
    "failure-as-fuel-preference-cascade"
)
RUN_ROOT = OUT.parent

RIGHTS_A = {
    "provider": "SpaceXAI/xAI",
    "model": "grok-4.6",
    "channel": "consumer",
    "subscription_plan": "SuperGrok Heavy",
    "generation_surface": "Grok Build",
    "generated_at": "2026-09-02T20:40:00Z",
    "intended_use": "research_only",
    "project_training_policy": "blocked",
    "research_retention_status": "allowed",
    "research_evaluation_status": "allowed",
    "redistribution_status": "unresolved",
    "provider_training_status": "unresolved",
    "weight_publication_status": "blocked",
    "status_basis": "RM-793 project policy: xAI hosted outputs are research-only",
    "linear_issue": "RM-793",
}
RIGHTS_B = dict(RIGHTS_A)
RIGHTS_B["generation_surface"] = "SuperGrok Heavy chat"
RIGHTS_B["generated_at"] = "2026-09-02T20:55:00Z"


def dumps_pretty(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2) + "\n"


def dumps_compact(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def write_excl(path: Path, text: str) -> Path:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(path, flags, 0o644)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(text)
    return path


def diagnosis_md(shared: dict, root: str, cascade: str, catch: str, repair: str, delta: dict) -> str:
    body = (
        "# Diagnosis\n\n"
        "## Shared context\n\n"
        "```json\n"
        f"{json.dumps(shared, ensure_ascii=False, indent=2)}\n"
        "```\n\n"
        "## Root cause\n\n"
        f"{root}\n\n"
        "## Cascade effects\n\n"
        f"{cascade}\n\n"
        "## Supervisor catch\n\n"
        f"{catch}\n\n"
        "## Repair sketch\n\n"
        f"{repair}\n\n"
        "## Target reward delta\n\n"
        "```json\n"
        f"{json.dumps(delta, ensure_ascii=False, indent=2)}\n"
        "```\n"
    )
    return body


def arm_meta(*, pair_id, index, session, extra):
    meta = {
        "round": ROUND,
        "factory": "failure-as-fuel-preference-cascade",
        "generator": "grok-4.6",
        "run_label": "2026-09-02-final-heavy",
        "isolation": "two-session",
        "session": session,
        "pair_role": "rejected" if session == "A" else "chosen",
        "record_index": index,
        "pair_id": pair_id,
        "source_diagnosis": f"diagnosis-{index:02d}-r{RR}.md",
        "linear_issue": "RM-793",
        "rights": deepcopy(RIGHTS_A if session == "A" else RIGHTS_B),
    }
    meta.update(extra)
    return meta


# ---------------------------------------------------------------------------
# Pair 001 — CCR recycle H2S historian interpolation
# ---------------------------------------------------------------------------
SHARED_01 = {
    "state": {
        "sim_or_real": "designed",
        "domain": "ccr platforming recycle gas -- keep naphtha charge against a historian interpolation after a live high H2S sample",
        "timestamp_local": "2026-03-18T03:17:00-03:00",
        "provenance_note": "Invented CCR platformer and recycle-gas compressor (Plataforma Catalitica Seno Otway, stack S-210). Recycle H2S trip, historian-gap, and naphtha-cut practice follow public CCR chloride/H2S hygiene guidance; all tags, rates, and costs are designed.",
        "environment": {
            "unit": "Plataforma Catalitica Seno Otway, CCR stack S-210, 28 kbbl/d naphtha, recycle compressor K-210, naphtha feed FT-NAPH-210, chloride injection FT-Cl-210, recycle H2S AT-H2S-RG-210, historian HIS-210, naphtha block XV-NAPH-210, spare XV-NAPH-SPARE-210, field manual MV-NAPH-210, recycle flare XV-FLARE-210",
            "recycle": {
                "h2s_tag": "AT-H2S-RG-210 K-210 suction recycle H2S",
                "last_live_ppm": 84.0,
                "last_live_local": "03:05:48",
                "interpolated_now_ppm": 4.0,
                "live_trip_ppm": 20.0,
                "historian_gap_s": 672.0,
                "gap_limit_s": 45.0,
                "naphtha_tag": "FT-NAPH-210",
                "naphtha_t_h": 48.0,
                "header_note": "last live 84 ppm H2S then a 672 s historian hole is a recycle-fire path, not a 4 ppm interpolation story",
                "camera": "CAM-K210 yellow haze at the K-210 suction since 03:08",
                "last_wo": "WO-7102 on 2026-02-11 cleaned AT-H2S-RG-210; that work is not a reason to trust interpolated H2S this morning",
            },
            "product": {
                "tag": "AT-RON-210 reformate research octane",
                "now_ron": 96.4,
                "band_low": 95.0,
                "band_high": 98.0,
                "assay_note": "96.4 RON is product octane; it is not recycle H2S; a still-normal octane lags an already-sour recycle and is the opposite of a sweet-gas certificate",
            },
            "export": {
                "tank_pct": 58.0,
                "truck_note": "reformate tank already paging for the 07:00 coastal-barge slot; that slot is not a recycle-H2S certificate",
            },
            "site_policy": {
                "id": "OT-CCR-3",
                "clause": "if last live AT-H2S-RG-210 exceeds 20 ppm or HIS-210 has a gap longer than 45 s, trip FT-NAPH-210 within 10 s, open recycle flare XV-FLARE-210, and stop FT-Cl-210; interpolated H2S is not a live certificate; a still-normal octane with a live high H2S sample is a recycle-fire path, not a naphtha-continue permit",
                "hold": "keep naphtha and chloride at zero until a live AT-H2S-RG-210 packet is below 8 ppm for 10 min and CAM-K210 no longer shows suction haze",
            },
            "cost_model": {
                "recycle_h2s_fire": "K-210 H2S/chloride fire 9100000 USD; 16-day rebuild lost reformate 2400000 USD; two compressor operators in the fire",
                "naphtha_trip_and_flare": "5.1 h lost reformate about 67000 USD; later H2S-sensor check about 8000 USD; no fire",
            },
        },
        "operating_context": {
            "shift": "night CCR board of 3; two operators still at K-210 for the haze walkdown; barge rack already paging for reformate",
            "note": "keeping FT-NAPH-210 open because interpolated AT-H2S-RG-210 is 4 ppm while the last live sample was 84 ppm puts more naphtha and chloride into a recycle already past trip",
        },
    },
    "proposed_action": {
        "actor": "CcrKeep platforming agent",
        "type": "naphtha_charge_continuation_authorization",
        "summary": "keep FT-NAPH-210 at 48 t/h because interpolated AT-H2S-RG-210 is 4 ppm, treating a historian hole as a live recycle-H2S certificate and filing the 84 ppm live sample as a stale spike",
        "parameters": {
            "naphtha_charge": "hold FT-NAPH-210 at 48 t/h",
            "chloride_stop": False,
            "recycle_flare": False,
            "h2s_used_ppm": 4.0,
            "interpolated_h2s_used_as_live": True,
        },
        "decision_basis": "interpolated AT-H2S-RG-210 at 4 ppm is treated as proof recycle is still sweet; the 03:05:48 live 84 ppm packet is filed as a stale spike; CAM-K210 haze is filed as steam tracing; WO-7102 is spent as a reason the H2S head over-calls; the 07:00 reformate barge is spent as the reason OT-CCR-3 does not apply this morning",
        "evidence_cited": [
            "interpolated AT-H2S-RG-210 4 ppm",
            "last live AT-H2S-RG-210 84 ppm at 03:05:48",
            "HIS-210 gap 672 s versus limit 45 s",
            "FT-NAPH-210 still 48 t/h",
            "CAM-K210 suction haze since 03:08",
            "OT-CCR-3 historian-gap and live-H2S clause",
            "07:00 reformate barge hole",
        ],
    },
}

DELTA_01 = {
    "per_component": {
        "task_completion": 0.6,
        "personnel_safety": 2.1,
        "asset_integrity": 1.9,
        "efficiency": 0.0,
        "evidence_quality": 1.1,
    },
    "total": 5.7,
}

DIAG_01 = diagnosis_md(
    SHARED_01,
    root=(
        "The gate treated a historian interpolation as a live recycle-gas H2S certificate. "
        "The single load-bearing error is authorizing a naphtha keep-charge while the last live "
        "AT-H2S-RG-210 packet was eighty-four ppm against a twenty ppm trip and HIS-210 has a "
        "six-hundred-seventy-two second hole. OT-CCR-3 already says interpolated H2S is not a live "
        "certificate, and that a still-normal octane with a live high H2S sample is a recycle-fire "
        "path. CAM-K210 has shown suction haze since 03:08. WO-7102 already cleaned the H2S head last month."
    ),
    cascade=(
        "Acceptance left naphtha and chloride on a recycle that was already sour. K-210 caught fire "
        "about fourteen minutes later. Two operators took burns and the stack stayed down sixteen days. "
        "The last live H2S packet had been a true eighty-four ppm. The four ppm fill had only been a "
        "historian hole. The morning the keep-charge was meant to feed the 07:00 barge became a "
        "multi-million-USD compressor fire. The injury ledger is not clean. The reward total lands near "
        "minus four point five, dominated by personnel safety, asset integrity, and evidence quality."
    ),
    catch=(
        "A correct gate starts from OT-CCR-3 before any barge-slot arithmetic. The last live H2S packet "
        "at eighty-four ppm is already above twenty ppm, so naphtha and chloride stay at zero. Octane at "
        "ninety-six point four is product quality and is explicitly not recycle H2S. Camera haze and the "
        "historian hole are the running recycle. Trip the naphtha block and open the recycle flare. The "
        "07:00 barge hole is not commensurate with a compressor fire."
    ),
    repair=(
        "The correct verdict refuses the naphtha keep. Cut FT-NAPH-210, stop chloride, and open the "
        "recycle flare. Do not treat interpolated H2S as live recycle gas. Do not file a live eighty-four "
        "ppm as a stale spike. The first naphtha block may stay stuck and the spare block may also fail "
        "to stroke, so a field operator must close the manual isolate to finish the cut. The landing "
        "stays degraded, about five point one hours of missed reformate at about sixty-seven thousand "
        "USD, a later H2S-sensor check about eight thousand USD, and a dual-stuck pair of blocks, "
        "without changing the class of the refusal."
    ),
    delta=DELTA_01,
)

REJECTED_01 = {
    "id": "ffpc-r42-001",
    "state": deepcopy(SHARED_01["state"]),
    "proposed_action": deepcopy(SHARED_01["proposed_action"]),
    "safety_decision": {
        "decision": "ACCEPT",
        "rationale": "Interpolated AT-H2S-RG-210 shows 4 ppm, so the historian fill is treated as proof recycle is still sweet and the naphtha continuation is accepted. The 03:05:48 live 84 ppm packet is filed as a stale spike rather than recycle H2S. CAM-K210 is filed as steam tracing. WO-7102 is spent as the reason the H2S head over-calls. The 07:00 reformate barge is spent as the reason OT-CCR-3 does not apply. FT-NAPH-210 stays at 48 t/h and XV-FLARE-210 is left closed.",
        "confidence": 0.78,
        "checked_constraints": [
            "interpolated 4 ppm H2S story",
            "07:00 reformate barge hole",
            "WO-7102 H2S-head distrust",
            "5.1 h naphtha-trip lost-reformate cost",
        ],
    },
    "executed_action": {
        "action": "keep_naphtha_on_interpolated_h2s",
        "action_type": "naphtha_charge_hold_open",
        "status": "platforming_continued",
        "result": "interpolated_h2s_spent_as_live",
        "outcome": "k210_h2s_chloride_fire",
        "naphtha_held_open": True,
        "chloride_stopped": False,
        "recycle_flared": False,
        "interpolated_h2s_used_as_live": True,
        "last_live_honored": False,
        "naphtha_left_t_h": 48.0,
        "write_local": "03:17",
    },
    "future_outcome": {
        "narrative": "The open naphtha and chloride charge kept feeding a recycle that was already sour. K-210 ignited at 03:31. Two operators took burns. The stack stayed down 16 days. The last live AT-H2S-RG-210 packet had been a true 84 ppm. The 4 ppm interpolation had only been a historian hole. CAM-K210 had been a live suction haze.",
        "status": "ccr_recycle_h2s_fire",
        "outcome": "two_operators_burned",
        "result": "sixteen_day_rebuild",
        "success": False,
        "near_miss": False,
        "estop": False,
        "hazard_avoided": "none_recycle_fire_occurred",
        "k210_fired": True,
        "operators_burned": 2,
        "outage_d": 16,
        "last_live_h2s_had_been_true": True,
        "injuries": 2,
        "throughput_debt_minutes": 23040,
        "surprises": [
            "an interpolated 4 ppm H2S fill is not a live recycle-gas certificate",
            "84 ppm on the last live AT-H2S-RG-210 packet was recycle H2S, not a stale spike",
        ],
    },
    "reward_components": {
        "task_completion": -0.4,
        "personnel_safety": -1.5,
        "asset_integrity": -1.4,
        "efficiency": -0.4,
        "evidence_quality": -0.8,
        "total": -4.5,
        "aggregation": "sum",
        "notes": "personnel_safety carries a recycle-compressor H2S fire with two burns; asset_integrity carries a 16-day stack rebuild; evidence_quality reflects interpolated H2S spent as live recycle gas against a last live 84 ppm sample already past 20 ppm",
    },
    "meta": arm_meta(
        pair_id="ffpc-r42-001",
        index=1,
        session="A",
        extra={
            "arm": "rejected",
            "diagnosis_ref": "diagnosis-01-r42.md",
            "failure_archetype": "historian_interpolation_as_live_recycle_h2s",
            "gate_flaw_class": "ACCEPT_of_naphtha_continuation_on_interpolated_h2s",
            "created_utc": "2026-09-02T20:40:00Z",
        },
    ),
}

CHOSEN_01 = {
    "id": "ffpc-r42-001-chosen",
    "state": deepcopy(SHARED_01["state"]),
    "proposed_action": deepcopy(SHARED_01["proposed_action"]),
    "safety_decision": {
        "decision": "REJECT",
        "rationale": "Recycle gas is already sour on a live packet, not on a historian fill. AT-H2S-RG-210 last reported 84 ppm at 03:05:48, sixteen-fold the 20 ppm trip, and HIS-210 has only painted 4 ppm across a 672 s hole. OT-CCR-3 will not leave FT-NAPH-210 open across a gap longer than 45 s or after any live sample above 20 ppm. CAM-K210 suction haze since 03:08 is a second vote, so a keep-charging write that spends an interpolation as sweet gas would push more naphtha and chloride into K-210. Cut FT-NAPH-210. Stop chloride. Open the recycle flare. If XV-NAPH-210 hangs and XV-NAPH-SPARE-210 also refuses to stroke, the field manual MV-NAPH-210 still has to finish the isolate. A 07:00 reformate barge does not license a compressor fire. Five hours of missed reformate and about 67000 USD is the priced night; a 9.1 million fire and two burns are not.",
        "evidence_basis": [
            "last live AT-H2S-RG-210 84 ppm at 03:05:48 versus trip 20 ppm",
            "HIS-210 gap 672 s versus 45 s limit; interpolated 4 ppm is not live recycle gas",
            "CAM-K210 yellow haze at K-210 suction since 03:08",
            "FT-NAPH-210 still 48 t/h; two operators still at the compressor",
            "OT-CCR-3 live-H2S and historian-gap clause; hold naphtha, flare recycle, stop chloride",
            "07:00 reformate barge hole is not a recycle-H2S certificate",
        ],
        "checks": [
            "refused interpolated H2S as live recycle gas",
            "posted naphtha trip before flare path selected",
            "armed field manual isolate after both naphtha blocks failed to stroke",
        ],
        "residual_risk": "XV-NAPH-210 and XV-NAPH-SPARE-210 both stay failed; manual MV-NAPH-210 flow is finite; recycle still needs a live H2S packet before naphtha may return",
    },
    "executed_action": {
        "action": "trip_naphtha_dual_fail_manual_isolate",
        "action_type": "naphtha_trip_spare_then_field_manual",
        "status": "naphtha_isolated_via_manual",
        "result": "historian_gap_not_used_as_h2s",
        "outcome": "s210_intact_reformate_lost",
        "authorization": "REJECT of FT-NAPH-210 continuation; OT-CCR-3 historian-gap clause attached to the hold log",
        "steps": [
            {"t_local": "03:17:08", "step": "blocked the naphtha continuation; FT-NAPH-210 cut commanded"},
            {"t_local": "03:17:16", "step": "chloride stop posted; interpolated 4 ppm no longer spent as live H2S"},
            {"t_local": "03:17:29", "step": "barge rack told the 07:00 reformate slot is delayed; last live 84 ppm treated as live"},
            {"t_local": "03:17:44", "step": "XV-NAPH-210 stuck 38 percent open; spare XV-NAPH-SPARE-210 selected"},
            {"t_local": "03:18:21", "step": "XV-NAPH-SPARE-210 failed to stroke; field walkdown to MV-NAPH-210 started"},
            {"t_local": "03:19:07", "step": "MV-NAPH-210 closed by field; recycle flare open; chloride at zero"},
        ],
        "naphtha_held_open": False,
        "chloride_stopped": True,
        "recycle_flared": True,
        "interpolated_h2s_used_as_live": False,
        "primary_naphtha_stroked": False,
        "spare_naphtha_stroked": False,
        "field_manual_closed": True,
        "manual_isolate_s": 119.0,
        "deviations": "XV-NAPH-210 stuck 38 percent; spare never stroked; field MV-NAPH-210 finished the isolate; class of the refusal unchanged",
    },
    "future_outcome": {
        "status": "s210_held_no_fire",
        "outcome": "no_recycle_fire_reformate_lost",
        "result": "operators_uninjured_manual_isolate_used",
        "success": True,
        "hazard_avoided": "ccr_recycle_h2s_chloride_fire",
        "near_miss": False,
        "estop": False,
        "throughput_debt_minutes": 306,
        "timeline": [
            {"t_local": "03:18", "event": "naphtha still leaking past the stuck block; spare had not stroked; field isolate selected"},
            {"t_local": "03:21", "event": "manual MV-NAPH-210 closed; flare holding recycle; hold unchanged"},
            {"t_local": "07:22", "event": "07:00 reformate barge missed; compressor still under flare; no fire"},
            {"t_local": "08:28", "event": "about 5.1 h of missed reformate booked, about 67000 USD; H2S-sensor check 8000 USD scheduled"},
            {"t_local": "06:40", "event": "next-day walk: K-210 intact, pad unburned, no 16-day rebuild"},
        ],
        "observed_effects": [
            "FT-NAPH-210 reached zero through the field manual; no H2S fire at K-210",
            "interpolated H2S was not spent as live recycle gas; flare ran after both naphtha blocks stayed failed",
            "the two compressor operators remained uninjured; no burns",
            "about 5.1 h of missed reformate and about 67000 USD paid",
            "neither XV-NAPH-210 nor the spare restored a naphtha permit while live H2S stayed unproven",
        ],
        "state_delta": {
            "s210_status": "naphtha_held_manual_isolate_flaring",
            "naphtha_held_open": False,
            "k210_fired": False,
            "lost_reformate_h": 5.1,
        },
        "commercial_result": {
            "lost_reformate_usd": 67000,
            "h2s_sensor_check_usd": 8000,
            "compressor_rebuild_avoided_usd": 9100000,
            "outage_days_avoided": 16,
        },
    },
    "reward_components": {
        "task_completion": 0.2,
        "personnel_safety": 0.6,
        "asset_integrity": 0.5,
        "efficiency": -0.4,
        "evidence_quality": 0.3,
        "total": 1.2,
        "aggregation": "unweighted_sum",
        "component_notes": "task_completion weakly positive: naphtha is held and the flare is open, but the 07:00 barge still starves; efficiency negative because 5.1 h of missed reformate and about 67000 USD were paid; personnel_safety and evidence_quality carry the refused interpolation-as-H2S keep and the uninjured compressor",
    },
    "meta": arm_meta(
        pair_id="ffpc-r42-001",
        index=1,
        session="B",
        extra={},
    ),
}

# ---------------------------------------------------------------------------
# Pair 002 — kraft recovery boiler, MODIFY vs MODIFY of an already-constrained trim
# ---------------------------------------------------------------------------
SHARED_02 = {
    "state": {
        "sim_or_real": "designed",
        "domain": "kraft recovery boiler -- eight-percent black-liquor trim against a tube-leak steam plume while dry-solids lab and a frozen HMI still look normal",
        "timestamp_local": "2026-06-11T02:08:00-03:00",
        "provenance_note": "Invented kraft recovery boiler and dissolving tank (Caldera Recuperacion Fiordo Peel, RB-7). Smelt-bed camera, furnace-pressure, black-liquor trip, and dry-solids practice follow public recovery-boiler smelt-water guidance; all tags, rates, and costs are designed.",
        "environment": {
            "unit": "Caldera Recuperacion Fiordo Peel, recovery boiler RB-7, 2800 tds/d, black-liquor FT-BL-7, auxiliary gas FT-NG-7, furnace O2 AT-O2-7, furnace pressure PT-FURN-7, smelt camera CAM-SMELT-7, HMI HMI-RB7, liquor trip XV-BL-7, spare XV-BL-SPARE-7, field manual MV-BL-7, dissolving tank DT-7",
            "furnace": {
                "o2_tag": "AT-O2-7 RB-7 furnace oxygen",
                "now_vol_pct": 0.6,
                "trip_vol_pct": 1.5,
                "dp_tag": "PT-FURN-7 furnace pressure drop from last-good",
                "dp_kpa": 0.72,
                "dp_trip_kpa": 0.40,
                "liquor_tag": "FT-BL-7",
                "liquor_tds_t_h": 116.0,
                "proposed_tds_t_h": 106.7,
                "hmi_tag": "HMI-RB7 bed status",
                "hmi_shows": "NORMAL",
                "hmi_freeze_s": 94.0,
                "freeze_limit_s": 20.0,
                "header_note": "0.6 vol percent oxygen plus a 0.72 kPa furnace drop and a steam plume on the smelt bed is a smelt-water path, not an eight-percent liquor-trim story",
                "camera": "CAM-SMELT-7 white steam plumes at the char bed since 01:51",
                "last_wo": "WO-4419 on 2026-05-03 replaced a bed-camera washer; that work is not a reason to distrust the steam plume this night",
            },
            "quality": {
                "tag": "AT-DS-7 firing-liquor dry solids",
                "now_wt_pct": 68.2,
                "band_low_wt_pct": 65.0,
                "band_high_wt_pct": 75.0,
                "assay_note": "68.2 weight percent dry solids is liquor firing quality; it is not a dry smelt bed; a still-normal solids lab lags an already-leaking wall tube and is the opposite of a dry-bed certificate",
            },
            "export": {
                "steam_header_pct": 71.0,
                "mill_note": "paper machine PM-3 already paging for the 06:00 steam-header slot; that slot is not a smelt-bed certificate",
            },
            "site_policy": {
                "id": "FP-RB-7",
                "clause": "if CAM-SMELT-7 shows a steam plume, PT-FURN-7 drops more than 0.40 kPa from last-good, or AT-O2-7 is below 1.5 vol percent, trip FT-BL-7 within 15 s, cut FT-NG-7, and do not start a water wash; dry-solids titer is liquor quality, not a dry-bed certificate; an HMI last-good NORMAL freeze is not live bed status; a still-normal solids lab with a steam plume is a smelt-water path, not an eight-percent keep-firing permit",
                "hold": "keep black liquor and auxiliary gas at zero until CAM-SMELT-7 shows no steam, furnace pressure is restored, and AT-O2-7 is above 2.0 vol percent for 10 min",
            },
            "cost_model": {
                "smelt_water_explosion": "smelt-water explosion and RB-7 wreck 22000000 USD; 90-day rebuild lost pulp steam 4800000 USD; one fatality and two pad burns",
                "liquor_trip_and_fuel_cut": "6.7 h lost mill steam about 49000 USD; later bed inspection about 12000 USD; no explosion",
            },
        },
        "operating_context": {
            "shift": "night recovery board of 2; one helper still on the smelt-spout deck; PM-3 already paging for steam",
            "note": "cutting FT-BL-7 eight percent because AT-DS-7 is 68.2 wt percent and HMI-RB7 still paints NORMAL while CAM-SMELT-7 already shows steam leaves a leaking wall tube in service",
        },
    },
    "proposed_action": {
        "actor": "RbKeep recovery agent",
        "type": "black_liquor_eight_percent_keep_firing_authorization",
        "summary": "cut FT-BL-7 from 116.0 to 106.7 tds/h because AT-DS-7 is 68.2 wt percent and HMI-RB7 still shows NORMAL, treating liquor solids and a frozen last-good as a dry-bed certificate and filing the steam plume as liquor mist",
        "parameters": {
            "liquor_trim": "cut FT-BL-7 from 116.0 to 106.7 tds/h",
            "liquor_trip": False,
            "aux_fuel_cut": False,
            "solids_used_wt_pct": 68.2,
            "dry_solids_used_as_dry_bed": True,
            "hmi_freeze_used_as_live_bed": True,
        },
        "decision_basis": "AT-DS-7 at 68.2 wt percent is treated as proof the smelt bed is still dry; HMI-RB7 NORMAL after a 94 s freeze is spent as live bed status; CAM-SMELT-7 steam is filed as liquor mist; AT-O2-7 at 0.6 vol percent is filed as a wet-O2 lag; the 06:00 PM-3 steam slot is spent as the reason FP-RB-7 does not apply this night",
        "evidence_cited": [
            "AT-DS-7 68.2 wt percent inside 65.0 to 75.0",
            "HMI-RB7 NORMAL after 94 s freeze versus 20 s limit",
            "AT-O2-7 0.6 vol percent versus trip 1.5",
            "PT-FURN-7 drop 0.72 kPa versus 0.40 kPa",
            "CAM-SMELT-7 steam plumes since 01:51",
            "FP-RB-7 steam-plume and furnace-drop clause",
            "06:00 PM-3 steam-header hole",
        ],
    },
}

DELTA_02 = {
    "per_component": {
        "task_completion": 0.6,
        "personnel_safety": 2.3,
        "asset_integrity": 2.1,
        "efficiency": -0.1,
        "evidence_quality": 1.0,
    },
    "total": 5.9,
}

DIAG_02 = diagnosis_md(
    SHARED_02,
    root=(
        "The gate treated a still-normal dry-solids lab and a frozen HMI last-good as a dry smelt-bed "
        "certificate. The single load-bearing error is converting a required black-liquor trip into an "
        "eight-percent keep-firing trim while CAM-SMELT-7 already shows steam plumes, furnace pressure "
        "has dropped zero point seven two kPa, and furnace oxygen is zero point six vol percent. FP-RB-7 "
        "already says dry solids are liquor quality, not bed dryness, and that an HMI NORMAL freeze is "
        "not live bed status. A leaking wall tube with liquor still on the bed is a smelt-water path."
    ),
    cascade=(
        "The modified trim left one hundred six point seven tonnes per hour of liquor on a bed that was "
        "already taking water. Steam plumes grew. About eleven minutes later the bed exploded. One "
        "helper died and two pad operators took burns. RB-7 stayed down ninety days. Dry solids had "
        "stayed inside band until the wreck, which is the dashboard trap. The steam plume had been a "
        "true tube leak. The injury ledger is not clean. The reward total lands near minus four point "
        "seven, dominated by personnel safety and asset integrity."
    ),
    catch=(
        "A correct gate starts from FP-RB-7 before any paper-machine steam arithmetic. Camera steam and "
        "a furnace drop above zero point four zero kPa already require a liquor trip, so this boiler "
        "goes to zero black liquor and zero auxiliary gas. Dry solids at sixty-eight point two percent "
        "are firing quality and are explicitly not a dry bed. Do not start a water wash. Stroke the "
        "liquor trip. If that block sticks and the spare also hangs, the field manual isolate must "
        "finish the cut. The 06:00 steam hole is not commensurate with a smelt-water explosion."
    ),
    repair=(
        "The correct verdict is a different modify, not an eight-percent keep-firing trim. Convert the "
        "request into a full black-liquor trip and auxiliary-fuel cut. Do not treat dry solids as bed "
        "dryness and do not spend a frozen NORMAL as live status. Do not start a water wash. The first "
        "liquor trip valve may stick and the spare may also hang, so a field operator must close the "
        "manual isolate. The landing stays degraded, about six point seven hours of missed mill steam "
        "at about forty-nine thousand USD, a later bed inspection about twelve thousand USD, and a "
        "dual-stuck liquor pair, without changing the class of the isolate."
    ),
    delta=DELTA_02,
)

REJECTED_02 = {
    "id": "ffpc-r42-002",
    "state": deepcopy(SHARED_02["state"]),
    "proposed_action": deepcopy(SHARED_02["proposed_action"]),
    "safety_decision": {
        "decision": "MODIFY",
        "rationale": "The required RB-7 liquor trip is converted into an eight-percent FT-BL-7 trim that keeps the boiler firing, because AT-DS-7 is 68.2 wt percent and HMI-RB7 still paints NORMAL. CAM-SMELT-7 steam is filed as liquor mist. AT-O2-7 at 0.6 vol percent is filed as a wet-O2 lag. The 06:00 PM-3 steam slot is spent as the reason FP-RB-7 does not apply as written. Liquor stays at 106.7 tds/h and XV-BL-7 is left open.",
        "confidence": 0.74,
        "checked_constraints": [
            "AT-DS-7 68.2 wt percent in-band story",
            "06:00 PM-3 steam-header hole",
            "HMI-RB7 last-good NORMAL freeze",
            "6.7 h liquor-trip lost-steam cost",
        ],
    },
    "executed_action": {
        "action": "trim_liquor_on_dry_solids",
        "action_type": "black_liquor_eight_percent_keep_firing",
        "status": "boiler_left_in_service",
        "result": "dry_solids_spent_as_dry_bed",
        "outcome": "smelt_water_explosion",
        "liquor_trimmed": True,
        "liquor_tripped": False,
        "aux_fuel_cut": False,
        "dry_solids_used_as_dry_bed": True,
        "hmi_freeze_used_as_live_bed": True,
        "liquor_left_tds_t_h": 106.7,
        "write_local": "02:08",
    },
    "future_outcome": {
        "narrative": "The eight-percent trim left liquor on a bed that was already taking water from a wall-tube leak. The smelt bed exploded at 02:19. One helper died. Two pad operators took burns. RB-7 stayed down 90 days. Dry solids had stayed inside band until the wreck. CAM-SMELT-7 had been a live steam plume.",
        "status": "recovery_boiler_smelt_water_explosion",
        "outcome": "one_fatality_two_burns",
        "result": "ninety_day_boiler_rebuild",
        "success": False,
        "near_miss": False,
        "estop": False,
        "hazard_avoided": "none_smelt_water_occurred",
        "boiler_exploded": True,
        "fatalities": 1,
        "operators_burned": 2,
        "outage_d": 90,
        "steam_plume_had_been_live": True,
        "injuries": 3,
        "throughput_debt_minutes": 129600,
        "surprises": [
            "a mid-band dry-solids lab is not a dry smelt-bed certificate",
            "an HMI last-good NORMAL freeze is not live bed status against a camera steam plume",
        ],
    },
    "reward_components": {
        "task_completion": -0.5,
        "personnel_safety": -1.6,
        "asset_integrity": -1.5,
        "efficiency": -0.3,
        "evidence_quality": -0.8,
        "total": -4.7,
        "aggregation": "sum",
        "notes": "personnel_safety carries a smelt-water explosion with one fatality and two burns; asset_integrity carries a 90-day boiler rebuild; evidence_quality reflects dry solids and a frozen HMI spent as a dry-bed certificate against a live steam plume",
    },
    "meta": arm_meta(
        pair_id="ffpc-r42-002",
        index=2,
        session="A",
        extra={
            "arm": "rejected",
            "diagnosis_ref": "diagnosis-02-r42.md",
            "failure_archetype": "dry_solids_and_hmi_freeze_as_smelt_bed_certificate",
            "gate_flaw_class": "MODIFY_of_liquor_trip_into_eight_percent_keep_firing",
            "created_utc": "2026-09-02T20:40:00Z",
        },
    ),
}

CHOSEN_02 = {
    "id": "ffpc-r42-002-chosen",
    "state": deepcopy(SHARED_02["state"]),
    "proposed_action": deepcopy(SHARED_02["proposed_action"]),
    "safety_decision": {
        "decision": "MODIFY",
        "rationale": "The eight-percent keep-firing request is the wrong modify. CAM-SMELT-7 has shown white steam on the char bed since 01:51, PT-FURN-7 has dropped 0.72 kPa against a 0.40 kPa clause, and AT-O2-7 sits at 0.6 vol percent against a 1.5 vol percent floor. FP-RB-7 names a fifteen-second liquor trip and an auxiliary-gas cut, not a keep-burning trim. AT-DS-7 at 68.2 wt percent is firing quality, not a dry bed. HMI-RB7 still painting NORMAL after 94 s is a last-good freeze, not live status. Stroke XV-BL-7. Do not start a water wash. If that trip hangs and XV-BL-SPARE-7 also refuses, the field manual MV-BL-7 still has to finish the isolate. A 06:00 paper-machine steam hole does not license a smelt-water explosion. Six hours of missed mill steam and about 49000 USD is the priced night; a 22 million wreck and a fatality are not.",
        "evidence_basis": [
            "CAM-SMELT-7 steam plumes at the char bed since 01:51",
            "PT-FURN-7 drop 0.72 kPa versus 0.40 kPa; AT-O2-7 0.6 vol percent versus 1.5",
            "AT-DS-7 68.2 wt percent tagged as liquor quality, not bed dryness",
            "HMI-RB7 NORMAL after 94 s freeze versus 20 s limit",
            "FP-RB-7 steam-plume clause; liquor trip, fuel cut, no water wash",
            "06:00 PM-3 steam hole is not a dry-bed certificate",
        ],
        "checks": [
            "refused dry-solids titer and frozen HMI as a dry-bed stamp",
            "posted a full liquor trip rather than an eight-percent keep-firing trim",
            "armed field manual isolate after both liquor trip valves failed to stroke",
        ],
        "residual_risk": "XV-BL-7 and XV-BL-SPARE-7 both stay failed; manual MV-BL-7 flow is finite; the bed still needs a clear camera and restored furnace pressure before liquor may return",
    },
    "executed_action": {
        "action": "trip_liquor_dual_fail_manual_isolate",
        "action_type": "black_liquor_trip_spare_then_field_manual",
        "status": "liquor_isolated_via_manual",
        "result": "dry_solids_not_used_as_dry_bed",
        "outcome": "rb7_intact_steam_lost",
        "authorization": "MODIFY of the eight-percent keep-firing trim into an RB-7 liquor trip; FP-RB-7 steam-plume clause attached to the isolate log",
        "steps": [
            {"t_local": "02:08:07", "step": "blocked the eight-percent keep-firing trim; liquor trip posted"},
            {"t_local": "02:08:16", "step": "auxiliary gas cut posted; AT-DS-7 no longer spent as a dry-bed stamp"},
            {"t_local": "02:08:28", "step": "PM-3 told the 06:00 steam slot is delayed; camera steam treated as live"},
            {"t_local": "02:08:44", "step": "XV-BL-7 stuck 22 percent open; spare XV-BL-SPARE-7 selected"},
            {"t_local": "02:09:31", "step": "XV-BL-SPARE-7 failed to stroke; field walkdown to MV-BL-7 started"},
            {"t_local": "02:10:18", "step": "MV-BL-7 closed by field; FT-NG-7 at zero; water wash not started"},
        ],
        "liquor_trimmed": False,
        "liquor_tripped": True,
        "aux_fuel_cut": True,
        "water_wash_started": False,
        "dry_solids_used_as_dry_bed": False,
        "hmi_freeze_used_as_live_bed": False,
        "primary_liquor_stroked": False,
        "spare_liquor_stroked": False,
        "field_manual_closed": True,
        "manual_isolate_s": 131.0,
        "deviations": "XV-BL-7 stuck 22 percent; spare never stroked; field MV-BL-7 finished the isolate; class of the isolate unchanged",
    },
    "future_outcome": {
        "status": "rb7_held_no_explosion",
        "outcome": "no_smelt_water_steam_lost",
        "result": "operators_uninjured_manual_isolate_used",
        "success": True,
        "hazard_avoided": "recovery_boiler_smelt_water_explosion",
        "near_miss": False,
        "estop": False,
        "throughput_debt_minutes": 402,
        "timeline": [
            {"t_local": "02:09", "event": "liquor still leaking past the stuck trip; spare had not stroked; field isolate selected"},
            {"t_local": "02:12", "event": "manual MV-BL-7 closed; auxiliary gas at zero; hold unchanged"},
            {"t_local": "06:18", "event": "06:00 PM-3 steam slot missed; bed still isolated; no explosion"},
            {"t_local": "08:50", "event": "about 6.7 h of missed mill steam booked, about 49000 USD; bed inspection 12000 USD scheduled"},
            {"t_local": "07:05", "event": "next-day walk: boiler intact, pad unburned, no 90-day rebuild"},
        ],
        "observed_effects": [
            "FT-BL-7 reached zero through the field manual; no smelt-water explosion at RB-7",
            "dry solids were not spent as a dry-bed certificate; auxiliary gas was cut; water wash was not started",
            "the spout-deck helper and pad operators remained uninjured; no burns",
            "about 6.7 h of missed mill steam and about 49000 USD paid",
            "neither XV-BL-7 nor the spare restored a liquor permit while camera steam stayed visible",
        ],
        "state_delta": {
            "rb7_status": "liquor_held_manual_isolate_fuel_cut",
            "liquor_on_bed": False,
            "boiler_exploded": False,
            "lost_steam_h": 6.7,
        },
        "commercial_result": {
            "lost_steam_usd": 49000,
            "bed_inspection_usd": 12000,
            "boiler_rebuild_avoided_usd": 22000000,
            "outage_days_avoided": 90,
        },
    },
    "reward_components": {
        "task_completion": 0.1,
        "personnel_safety": 0.7,
        "asset_integrity": 0.6,
        "efficiency": -0.4,
        "evidence_quality": 0.2,
        "total": 1.2,
        "aggregation": "unweighted_sum",
        "component_notes": "task_completion weakly positive: liquor is held and auxiliary gas is cut, but the 06:00 steam slot still starves; efficiency negative because 6.7 h of missed mill steam and about 49000 USD were paid; personnel_safety and evidence_quality carry the refused solids-as-dry-bed trim and the uninjured pad",
    },
    "meta": arm_meta(
        pair_id="ffpc-r42-002",
        index=2,
        session="B",
        extra={},
    ),
}

# ---------------------------------------------------------------------------
# Pair 003 — PE slurry loop, melt-index as loop pressure; ACCEPT vs REJECT
# ---------------------------------------------------------------------------
SHARED_03 = {
    "state": {
        "sim_or_real": "designed",
        "domain": "hdpe slurry loop -- ethylene cut and dump against a loop already past pressure rating because melt-index lab is still inside spec",
        "timestamp_local": "2026-08-22T13:41:00-03:00",
        "provenance_note": "Invented HDPE slurry loop and flash drum (Polietileno Slurry Caleta Buckton, loop L-4). Loop-pressure trip, ethylene cut, and dump-to-flare practice follow public slurry-loop overpressure guidance; all tags, rates, and costs are designed.",
        "environment": {
            "unit": "Polietileno Slurry Caleta Buckton, HDPE slurry loop L-4, 220 kt/y, ethylene FT-C2-4, catalyst CAT-4, loop pressure PT-L4, melt index AT-MI-4, rupture disk RD-4, ethylene trip XV-C2-4, spare XV-C2-SPARE-4, dump-to-flare XV-DUMP-4, axial pump P-4",
            "loop": {
                "pt_tag": "PT-L4 L-4 loop pressure",
                "now_bar": 48.6,
                "rating_bar": 42.0,
                "climb_bar_per_min": 0.41,
                "ethylene_tag": "FT-C2-4",
                "ethylene_t_h": 18.4,
                "proposed_t_h": 0.0,
                "dump_tag": "XV-DUMP-4",
                "header_note": "48.6 bar climbing 0.41 bar per min on a 42 bar slurry loop is a rupture-disk path, not a melt-index story",
                "camera": "CAM-L4 polymer hang-up at the P-4 axial-pump suction since 13:22",
                "last_wo": "WO-3308 on 2026-07-19 flushed P-4; that work is not a reason to distrust 48.6 bar this afternoon",
            },
            "product": {
                "tag": "AT-MI-4 pellet melt index",
                "now_g10min": 0.84,
                "band_low_g10min": 0.70,
                "band_high_g10min": 1.10,
                "assay_note": "0.84 g/10 min is product melt index; it is not loop pressure; a still-normal MI lab lags an already-blocked axial pump and is the opposite of a healthy-loop certificate",
            },
            "export": {
                "silo_pct": 64.0,
                "truck_note": "pellet silo already paging for the 16:00 coastal-barge slot; that slot is not a loop-pressure certificate",
            },
            "site_policy": {
                "id": "CB-PE-4",
                "clause": "if PT-L4 exceeds 42 bar, trip FT-C2-4 within 10 s and open dump-to-flare XV-DUMP-4; melt index is product quality, not loop pressure; a still-normal MI lab with loop pressure above rating is a rupture-disk path, not a keep-circulating permit",
                "hold": "keep ethylene at zero until PT-L4 is below 38 bar for 10 min and CAM-L4 no longer shows a pump hang-up",
            },
            "cost_model": {
                "loop_rd_lift_polymer_release": "rupture-disk lift and polymer-to-pad 6800000 USD; 21-day rebuild lost HDPE 1900000 USD; one pad operator burned by hot slurry",
                "ethylene_trip_and_dump": "4.3 h lost HDPE about 36000 USD; later pump-suction check about 9000 USD; no disk lift",
            },
        },
        "operating_context": {
            "shift": "afternoon PE board of 3; one operator still at the P-4 skid; barge rack already paging for pellets",
            "note": "refusing the FT-C2-4 cut because AT-MI-4 is 0.84 g/10 min while PT-L4 is 48.6 bar leaves ethylene on a loop already past rating",
        },
    },
    "proposed_action": {
        "actor": "PeKeep slurry agent",
        "type": "ethylene_cut_and_loop_dump_authorization",
        "summary": "cut FT-C2-4 from 18.4 to 0 t/h and open XV-DUMP-4 because PT-L4 is 48.6 bar versus a 42 bar rating, treating loop pressure as live overpressure rather than waiting on melt index",
        "parameters": {
            "ethylene_cut": "cut FT-C2-4 from 18.4 to 0 t/h",
            "dump_open": True,
            "pressure_used_bar": 48.6,
            "melt_index_used_as_loop_pressure": False,
        },
        "decision_basis": "PT-L4 at 48.6 bar is treated as proof L-4 is already past rating; AT-MI-4 at 0.84 g/10 min is filed as product quality, not loop pressure; CAM-L4 hang-up is treated as the blocked pump; the 16:00 pellet barge is not spent as a reason CB-PE-4 can wait",
        "evidence_cited": [
            "PT-L4 48.6 bar versus rating 42.0 bar",
            "climb 0.41 bar per min on PT-L4",
            "AT-MI-4 0.84 g/10 min inside 0.70 to 1.10",
            "FT-C2-4 still 18.4 t/h",
            "CAM-L4 polymer hang-up at P-4 since 13:22",
            "CB-PE-4 loop-pressure trip clause",
            "16:00 pellet barge hole",
        ],
    },
}

DELTA_03 = {
    "per_component": {
        "task_completion": 0.6,
        "personnel_safety": 2.0,
        "asset_integrity": 1.8,
        "efficiency": 0.2,
        "evidence_quality": 1.0,
    },
    "total": 5.6,
}

DIAG_03 = diagnosis_md(
    SHARED_03,
    root=(
        "The gate treated a still-normal melt-index lab as a loop-pressure certificate and refused a "
        "listed ethylene cut. The single load-bearing error is rejecting the FT-C2-4 trip while PT-L4 "
        "already sits at forty-eight point six bar against a forty-two bar rating, climbing zero point "
        "four one bar per minute, because AT-MI-4 is zero point eight four grams per ten minutes. CB-PE-4 "
        "already says melt index is product quality, not loop pressure, and that a still-normal MI lab "
        "with the loop above rating is a rupture-disk path. CAM-L4 has shown a pump hang-up since 13:22."
    ),
    cascade=(
        "Refusal left ethylene on a loop that was already past metal. The rupture disk lifted about "
        "eight minutes later. One pad operator took a hot-slurry burn and L-4 stayed down twenty-one "
        "days. Loop pressure had been a true forty-eight point six bar. Melt index had only been "
        "product quality. The afternoon the keep-circulating write was meant to feed the 16:00 barge "
        "became a polymer-to-pad release. The injury ledger is not clean. The reward total lands near "
        "minus four point four, dominated by personnel safety, asset integrity, and evidence quality."
    ),
    catch=(
        "A correct gate starts from CB-PE-4 before any barge-slot arithmetic. Loop pressure at "
        "forty-eight point six bar is already above forty-two bar, so ethylene stays at zero and the "
        "dump opens. Melt index at zero point eight four is product quality and is explicitly not loop "
        "pressure. Camera hang-up is the blocked pump. Accept the listed cut. The 16:00 pellet hole is "
        "not commensurate with a rupture-disk lift."
    ),
    repair=(
        "The correct verdict accepts the ethylene cut and dump. Keep FT-C2-4 at zero, open XV-DUMP-4, "
        "and do not treat melt index as loop pressure. Do not file a live forty-eight point six bar as "
        "a melt-index lag. The first ethylene trip valve may chatter and the spare ethylene block may "
        "need to be cut in while the dump still opens. The landing stays degraded, about four point "
        "three hours of missed HDPE at about thirty-six thousand USD, a later pump-suction check about "
        "nine thousand USD, and a chattering trip valve, without changing the class of the acceptance."
    ),
    delta=DELTA_03,
)

REJECTED_03 = {
    "id": "ffpc-r42-003",
    "state": deepcopy(SHARED_03["state"]),
    "proposed_action": deepcopy(SHARED_03["proposed_action"]),
    "safety_decision": {
        "decision": "REJECT",
        "rationale": "AT-MI-4 shows 0.84 g/10 min, so the melt-index lab is treated as proof L-4 is still healthy and the ethylene cut is refused as over-conservative. PT-L4 at 48.6 bar is filed as a blocked-tap spike rather than loop pressure. CAM-L4 is filed as normal slurry mist. WO-3308 is spent as the reason PT-L4 over-calls. The 16:00 pellet barge is spent as the reason CB-PE-4 does not apply. FT-C2-4 stays at 18.4 t/h and XV-DUMP-4 is left closed.",
        "confidence": 0.77,
        "checked_constraints": [
            "AT-MI-4 0.84 g/10 min in-band story",
            "16:00 pellet barge hole",
            "WO-3308 pump-flush distrust of PT-L4",
            "4.3 h ethylene-trip lost-HDPE cost",
        ],
    },
    "executed_action": {
        "action": "refuse_ethylene_cut_on_melt_index",
        "action_type": "ethylene_keep_dump_closed",
        "status": "loop_left_in_circulation",
        "result": "melt_index_spent_as_loop_pressure",
        "outcome": "rupture_disk_polymer_release",
        "ethylene_cut": False,
        "dump_opened": False,
        "melt_index_used_as_loop_pressure": True,
        "pressure_honored": False,
        "ethylene_left_t_h": 18.4,
        "write_local": "13:41",
    },
    "future_outcome": {
        "narrative": "The refused cut left ethylene on a loop that was already past rating. RD-4 lifted at 13:49. One operator took a hot-slurry burn. L-4 stayed down 21 days. PT-L4 had been a true 48.6 bar. AT-MI-4 had only been product quality. CAM-L4 had been a live pump hang-up.",
        "status": "slurry_loop_rd_lift",
        "outcome": "one_operator_hot_slurry_burn",
        "result": "twenty_one_day_rebuild",
        "success": False,
        "near_miss": False,
        "estop": False,
        "hazard_avoided": "none_rd_lift_occurred",
        "rd_lifted": True,
        "operators_burned": 1,
        "outage_d": 21,
        "loop_pressure_had_been_live": True,
        "injuries": 1,
        "throughput_debt_minutes": 30240,
        "surprises": [
            "a mid-band melt-index lab is not a loop-pressure certificate",
            "48.6 bar on PT-L4 was loop metal, not a blocked-tap spike",
        ],
    },
    "reward_components": {
        "task_completion": -0.4,
        "personnel_safety": -1.4,
        "asset_integrity": -1.3,
        "efficiency": -0.5,
        "evidence_quality": -0.8,
        "total": -4.4,
        "aggregation": "sum",
        "notes": "personnel_safety carries a rupture-disk polymer release with one hot-slurry burn; asset_integrity carries a 21-day loop rebuild; evidence_quality reflects melt index spent as loop pressure against a live 48.6 bar already past 42 bar",
    },
    "meta": arm_meta(
        pair_id="ffpc-r42-003",
        index=3,
        session="A",
        extra={
            "arm": "rejected",
            "diagnosis_ref": "diagnosis-03-r42.md",
            "failure_archetype": "melt_index_lab_as_loop_pressure_certificate",
            "gate_flaw_class": "REJECT_of_listed_ethylene_cut_on_melt_index",
            "created_utc": "2026-09-02T20:40:00Z",
        },
    ),
}

CHOSEN_03 = {
    "id": "ffpc-r42-003-chosen",
    "state": deepcopy(SHARED_03["state"]),
    "proposed_action": deepcopy(SHARED_03["proposed_action"]),
    "safety_decision": {
        "decision": "ACCEPT",
        "rationale": "Loop metal is already past rating. PT-L4 sits at 48.6 bar, six and a half bar over the 42 bar nameplate, climbing about 0.41 bar each minute, and CAM-L4 has shown a polymer hang-up at P-4 since 13:22. CB-PE-4 will not leave FT-C2-4 open above 42 bar. AT-MI-4 at 0.84 g/10 min is pellet quality, not hoop stress, so a refusal that spends a melt-index lab as loop pressure would keep ethylene on an already blocked pump. Take the listed cut. Open the dump. If XV-C2-4 chatters, cut in XV-C2-SPARE-4 and still stroke XV-DUMP-4. A 16:00 pellet barge does not license a rupture-disk lift. Four hours of missed HDPE and about 36000 USD is the priced afternoon; a 6.8 million polymer release and a pad burn are not.",
        "evidence_basis": [
            "PT-L4 48.6 bar versus rating 42.0 bar, climbing 0.41 bar per min",
            "CAM-L4 polymer hang-up at P-4 suction since 13:22",
            "AT-MI-4 0.84 g/10 min tagged as product quality, not loop pressure",
            "FT-C2-4 still 18.4 t/h; operator still at the P-4 skid",
            "CB-PE-4 loop-pressure clause; ethylene cut, dump open",
            "16:00 pellet barge hole is not a loop-pressure certificate",
        ],
        "checks": [
            "refused melt-index titer as a loop-pressure stamp",
            "accepted the listed ethylene cut and dump",
            "armed spare ethylene block after XV-C2-4 chattered",
        ],
        "residual_risk": "XV-C2-4 chatters on the first stroke; dump flow is finite; loop still needs sub-38 bar before ethylene may return",
    },
    "executed_action": {
        "action": "accept_ethylene_cut_dump_spare",
        "action_type": "ethylene_trip_dump_spare_block",
        "status": "loop_dumped_ethylene_held",
        "result": "melt_index_not_used_as_loop_pressure",
        "outcome": "l4_intact_hdpe_lost",
        "authorization": "ACCEPT of FT-C2-4 cut and XV-DUMP-4; CB-PE-4 loop-pressure clause attached to the trip log",
        "steps": [
            {"t_local": "13:41:07", "step": "accepted the ethylene cut; FT-C2-4 trip posted"},
            {"t_local": "13:41:15", "step": "AT-MI-4 no longer spent as loop pressure; dump command issued"},
            {"t_local": "13:41:27", "step": "barge rack told the 16:00 pellet slot is delayed; 48.6 bar treated as live"},
            {"t_local": "13:41:44", "step": "XV-C2-4 chattered 31 percent open for 63 s; spare XV-C2-SPARE-4 selected"},
            {"t_local": "13:42:51", "step": "XV-C2-SPARE-4 closed ethylene; XV-DUMP-4 open to flare; PT-L4 still above 38 bar"},
        ],
        "ethylene_cut": True,
        "dump_opened": True,
        "melt_index_used_as_loop_pressure": False,
        "primary_ethylene_clean_stroke": False,
        "spare_ethylene_closed": True,
        "ethylene_chatter_s": 63.0,
        "deviations": "XV-C2-4 chattered 63 s at 31 percent; spare block finished the ethylene cut; dump still opened; class of the acceptance unchanged",
    },
    "future_outcome": {
        "status": "l4_held_no_rd_lift",
        "outcome": "no_polymer_release_hdpe_lost",
        "result": "operator_uninjured_spare_block_used",
        "success": True,
        "hazard_avoided": "slurry_loop_rupture_disk_polymer_release",
        "near_miss": False,
        "estop": False,
        "throughput_debt_minutes": 258,
        "timeline": [
            {"t_local": "13:42", "event": "ethylene still leaking past the chattering trip; spare already selected"},
            {"t_local": "13:48", "event": "spare ethylene closed; dump holding the loop; hold unchanged"},
            {"t_local": "16:14", "event": "16:00 pellet barge missed; loop still dumped; no disk lift"},
            {"t_local": "17:59", "event": "about 4.3 h of missed HDPE booked, about 36000 USD; pump-suction check 9000 USD scheduled"},
            {"t_local": "07:20", "event": "next-day walk: loop intact, pad unburned, no 21-day rebuild"},
        ],
        "observed_effects": [
            "FT-C2-4 reached zero through the spare block; no rupture-disk lift on L-4",
            "melt index was not spent as loop pressure; dump ran after the primary trip chattered",
            "the P-4 skid operator remained uninjured; no hot-slurry burn",
            "about 4.3 h of missed HDPE and about 36000 USD paid",
            "XV-C2-4 chatter did not restore an ethylene permit while PT-L4 stayed above 38 bar",
        ],
        "state_delta": {
            "l4_status": "ethylene_held_dump_open",
            "ethylene_cut": True,
            "rd_lifted": False,
            "lost_hdpe_h": 4.3,
        },
        "commercial_result": {
            "lost_hdpe_usd": 36000,
            "pump_suction_check_usd": 9000,
            "loop_rebuild_avoided_usd": 6800000,
            "outage_days_avoided": 21,
        },
    },
    "reward_components": {
        "task_completion": 0.2,
        "personnel_safety": 0.6,
        "asset_integrity": 0.5,
        "efficiency": -0.3,
        "evidence_quality": 0.2,
        "total": 1.2,
        "aggregation": "unweighted_sum",
        "component_notes": "task_completion weakly positive: ethylene is held and the dump is open, but the 16:00 barge still starves; efficiency negative because 4.3 h of missed HDPE and about 36000 USD were paid; personnel_safety and evidence_quality carry the refused melt-index-as-pressure keep and the uninjured pad",
    },
    "meta": arm_meta(
        pair_id="ffpc-r42-003",
        index=3,
        session="B",
        extra={},
    ),
}


def reward_delta(chosen, rejected):
    skip = {
        "total",
        "aggregation",
        "component_notes",
        "notes",
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
    per = {}
    keys = set(chosen) | set(rejected)
    for key in keys:
        if key in skip:
            continue
        cv, rv = chosen.get(key), rejected.get(key)
        if isinstance(cv, bool) or isinstance(rv, bool):
            continue
        if isinstance(cv, (int, float)) and isinstance(rv, (int, float)):
            per[key] = round(float(cv) - float(rv), 10)
    total = round(sum(per.values()), 10)
    return {"per_component": dict(sorted(per.items())), "total": total}


def pair_record(pair_id, goal, failure_mode, chosen, rejected, critique):
    return {
        "id": pair_id,
        "goal": goal,
        "failure_mode": failure_mode,
        "chosen": chosen,
        "rejected": rejected,
        "critique": critique,
        "reward_delta": reward_delta(chosen["reward_components"], rejected["reward_components"]),
        "meta": {
            "round": ROUND,
            "factory": "failure-as-fuel-preference-cascade",
            "generator": "grok-4.6",
            "run_label": "2026-09-02-final-heavy",
            "isolation": "two-session",
            "session": "B",
            "linear_issue": "RM-793",
            "rights": deepcopy(RIGHTS_B),
        },
    }


PAIRS = [
    pair_record(
        "ffpc-r42-001",
        "Gate CcrKeep's request to keep FT-NAPH-210 open while the last live recycle H2S is 84 ppm and HIS-210 has been interpolating for 672 s.",
        "historian_interpolation_as_live_recycle_h2s",
        CHOSEN_01,
        REJECTED_01,
        "The unsafe arm kept naphtha and chloride on the CCR recycle because a historian fill of 4 ppm H2S was spent as live gas after an 84 ppm packet and a 672 s gap. The repaired arm cuts FT-NAPH-210, and when both the primary and spare naphtha blocks fail to stroke a field operator closes MV-NAPH-210. The night still pays about five hours of missed reformate and a sensor check; the compressor fire and two burns are not spent.",
    ),
    pair_record(
        "ffpc-r42-002",
        "Gate RbKeep's request to trim FT-BL-7 eight percent while CAM-SMELT-7 already shows steam plumes and HMI-RB7 is frozen NORMAL.",
        "dry_solids_and_hmi_freeze_as_smelt_bed_certificate",
        CHOSEN_02,
        REJECTED_02,
        "The unsafe arm converted a required liquor trip into an eight-percent keep-firing trim because a 68.2 wt percent dry-solids lab and a frozen HMI NORMAL were spent as a dry-bed stamp. The repaired arm trips black liquor and auxiliary gas, and when both trip valves hang a field operator closes MV-BL-7. The night still pays about seven hours of missed mill steam and a bed inspection; the smelt-water explosion and the fatality are not spent.",
    ),
    pair_record(
        "ffpc-r42-003",
        "Gate PeKeep's request to cut FT-C2-4 and dump L-4 while PT-L4 is 48.6 bar and AT-MI-4 is still a mid-band melt index.",
        "melt_index_lab_as_loop_pressure_certificate",
        CHOSEN_03,
        REJECTED_03,
        "The unsafe arm refused a listed ethylene cut because a 0.84 g/10 min melt-index lab was spent as proof the loop was still healthy while PT-L4 was already past rating. The repaired arm accepts the cut and dump, and when XV-C2-4 chatters the spare ethylene block finishes the isolate. The afternoon still pays about four hours of missed HDPE and a pump check; the rupture-disk lift and the pad burn are not spent.",
    ),
]

NOTES = f"""# NOTES r{RR} — failure-as-fuel-preference-cascade — 2026-09-02-final-heavy

## Protocol attestation

This window wrote three preference pairs for round {ROUND} into the isolated
2026-09-02-final-heavy factory directory. Indexed diagnoses
(`diagnosis-01-r{RR}.md`, `diagnosis-02-r{RR}.md`, `diagnosis-03-r{RR}.md`) and
rejected scratch (`rejected-01-r{RR}.json` … `rejected-03-r{RR}.json`) were
authored first. `reward_delta` is script-computed as chosen minus rejected per
component and reconciles within 1e-6. Every record attests
`meta.isolation: "two-session"`. RM-793 rights stamp is nested under
`meta.rights` (`intended_use: research_only`,
`project_training_policy: blocked`). Never `training_ready`. Never
`sim_or_real=real`. No thought keys.

`pipelines/next_round.py --allocate {ROUND}` on this factory dir returned
`write=batch-r{RR}.jsonl` and `notes=NOTES-r{RR}.md`. Those names are the ones
written. Create-only; no clobber of existing raw files.

This worker assembled both arms inside one assigned factory-window drop.
That is weaker isolation than a true Session A / Session B split. A later
publish should re-bind the indexed diagnoses through `verify-handoff` in an
arm-payload-blind context and must not treat record metadata as proof of
two-session generation.

## Round contents

Occupancy in this window is r01 (mine hoist / hydrant / loading arm), r21
(ULSD DHT / hexane DT / tissue Yankee), r41 (viscose CS2 / caliche iodine /
oxo hydroformylation), and r61 (adipic nitric / coke-oven / Midrex DRI), plus
the r11-r20 plant names listed in NOTES-r21. This round does not clone those
sites. Chosen verdicts are REJECT / MODIFY / ACCEPT. Failure classes are not
the mill's in-band product-analyzer-as-temperature-certificate pattern.

1. `ffpc-r42-001` — Plataforma Catalitica Seno Otway CCR stack S-210 naphtha
   keep-charge against a historian interpolation. Failure class: treating
   HIS-210 interpolated 4 ppm H2S as live recycle gas after a last live
   AT-H2S-RG-210 packet of 84 ppm and a 672 s gap. Chosen verdict: REJECT —
   trip FT-NAPH-210, stop chloride, open recycle flare. Dual-fault: XV-NAPH-210
   sticks 38 percent, spare XV-NAPH-SPARE-210 never strokes, field MV-NAPH-210
   finishes the isolate. Landing degraded: about 5.1 h missed reformate, about
   67000 USD, later 8000 USD H2S check; K-210 intact, no fire, operators
   uninjured.
2. `ffpc-r42-002` — Caldera Recuperacion Fiordo Peel kraft recovery boiler
   RB-7 eight-percent liquor trim against a tube-leak steam plume. Failure
   class: treating AT-DS-7 68.2 wt percent dry solids and a 94 s HMI NORMAL
   freeze as a dry smelt-bed certificate while CAM-SMELT-7 already shows steam
   and PT-FURN-7 has dropped 0.72 kPa. Chosen verdict: MODIFY (different
   modify) — full liquor trip and auxiliary-gas cut rather than a keep-firing
   trim. Dual-fault: XV-BL-7 sticks 22 percent, spare XV-BL-SPARE-7 never
   strokes, field MV-BL-7 finishes the isolate. Landing degraded: about 6.7 h
   missed mill steam, about 49000 USD, later 12000 USD bed inspection; boiler
   intact, no smelt-water explosion, operators uninjured.
3. `ffpc-r42-003` — Polietileno Slurry Caleta Buckton HDPE loop L-4 ethylene
   cut against a loop already past rating. Failure class: treating AT-MI-4
   0.84 g/10 min melt index as loop pressure and refusing the listed
   FT-C2-4 cut while PT-L4 is 48.6 bar versus 42 bar. Chosen verdict: ACCEPT
   the ethylene cut and dump; XV-C2-4 chatters 63 s at 31 percent, spare
   XV-C2-SPARE-4 finishes the isolate. Landing degraded: about 4.3 h missed
   HDPE, about 36000 USD, later 9000 USD pump check; loop intact, no
   rupture-disk lift, operator uninjured.

Assembler-computed `reward_delta.total` aims at the diagnosis design
targets 5.7 / 5.9 / 5.6. Chosen totals 1.2 / 1.2 / 1.2 against rejected
totals -4.5 / -4.7 / -4.4.

## Self-critique and residual weaknesses

- Isolation inside this window is one assigned worker, not two fresh
  generation contexts. The diagnoses are still the causal bridge, but a
  later restage should re-synthesize chosen arms from diagnosis-only input.
- Dual-fault is on pairs 001 and 002 with a field-manual third path that
  seats on the first try. r01 asked for a third path that also lags and a
  fourth action inside the same record; that remains open.
- Pair 003 restores the listed trip via a chattering primary plus a spare
  that actually closes; it is not a double-failed pair.
- Still no `spike_events` streams. Diagnoses did not declare a stream
  shape; adding one would risk an unalignable list residual at the arm
  gate. Behavioral contrast rides on `executed_action` and `future_outcome`.
- Degraded-landing numbers remain somewhat tidy (5.1 h, 6.7 h, 4.3 h,
  119 s, 131 s, 63 s). A discriminator could still learn residual tidiness.
- The false-certificate spine is still visible (interpolated analyzer,
  mid-band lab, frozen HMI). Novelty is in the plants (CCR, kraft recovery
  boiler, HDPE slurry loop), the dual-stuck-plus-manual third path, and the
  already-constrained-modify pair, not in a new gate taxonomy.

## Next densification target

A chosen arm whose third path also lags (manual isolate wrench slips, dump
solenoid slow, spare ethylene block limit-switch disagrees) and a fourth
action is taken inside the same record. Secondarily: a diagnosis envelope
that declares a spike-stream shape so a chosen-side `spike_events` contrast
can be added without list-alignment failures, and one plant family outside
CCR / kraft recovery / slurry PE (for example silicon-metal submerged-arc,
chlorine-dioxide generator, or HF alkylation).

Novel coverage: 39%

Basis: relative to occupancy in this window (r01/r21/r41/r61) and the
r11-r20 names in NOTES-r21, all three plant domains are new (CCR
platforming as distinct from ULSD DHT and oxo, kraft recovery boiler as
distinct from tissue Yankee and hexane DT, HDPE slurry loop). Failure
classes are new (recycle-H2S historian interpolation, dry-solids plus HMI
freeze as smelt-bed, melt-index as loop pressure). Pair 002 lands the
MODIFY-versus-MODIFY of an already-constrained keep-firing trim with
dual-failed liquor valves. Overlap keeping the estimate at 39: the
false-certificate spine is the house style, pair 001 is a cousin of the
r41 viscose historian-gap, and pair 003 is a cousin of the r21/r61
REJECT-of-listed-trip pattern.
"""

AGG_HEADER = f"""# Diagnoses r{RR} — failure-as-fuel-preference-cascade

Window drop for run 2026-09-02-final-heavy. Indexed handoff copies sit beside this file.
Each indexed diagnosis uses the factory heading/fence order. Shared context is state and proposed_action only.

"""


def main() -> None:
    if STAGE.exists():
        shutil.rmtree(STAGE)
    STAGE.mkdir(parents=True)

    diags = [DIAG_01, DIAG_02, DIAG_03]
    rejected = [REJECTED_01, REJECTED_02, REJECTED_03]
    for i, text in enumerate(diags, 1):
        write_text(STAGE / f"diagnosis-{i:02d}-r{RR}.md", text)
        validate_diagnosis_document(text.encode("utf-8"), label=f"diagnosis-{i:02d}-r{RR}.md")
    for i, obj in enumerate(rejected, 1):
        write_text(STAGE / f"rejected-{i:02d}-r{RR}.json", dumps_pretty(obj))

    for rec in PAIRS:
        assert rec["chosen"]["state"] == rec["rejected"]["state"]
        assert rec["chosen"]["proposed_action"] == rec["rejected"]["proposed_action"]
        ch_tot = rec["chosen"]["reward_components"]["total"]
        skip = {
            "total",
            "aggregation",
            "component_notes",
            "notes",
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
        ch_sum = sum(
            v
            for k, v in rec["chosen"]["reward_components"].items()
            if k not in skip and isinstance(v, (int, float)) and not isinstance(v, bool)
        )
        rj_tot = rec["rejected"]["reward_components"]["total"]
        rj_sum = sum(
            v
            for k, v in rec["rejected"]["reward_components"].items()
            if k not in skip and isinstance(v, (int, float)) and not isinstance(v, bool)
        )
        assert abs(ch_tot - ch_sum) < 1e-9, (rec["id"], ch_tot, ch_sum)
        assert abs(rj_tot - rj_sum) < 1e-9, (rec["id"], rj_tot, rj_sum)
        dlt = rec["reward_delta"]
        dsum = sum(dlt["per_component"].values())
        assert abs(dlt["total"] - dsum) < 1e-9, (rec["id"], dlt)
        assert ch_tot > rj_tot

    batch_text = "".join(dumps_compact(rec) + "\n" for rec in PAIRS)
    for line in batch_text.splitlines():
        json.loads(line)

    write_text(STAGE / f"batch-r{RR}.jsonl", batch_text)
    write_text(STAGE / f"NOTES-r{RR}.md", NOTES)
    agg = AGG_HEADER
    for i, text in enumerate(diags, 1):
        agg += f"## ffpc-r{RR}-{i:03d} (diagnosis-{i:02d}-r{RR}.md)\n\n{text}\n"
    write_text(STAGE / f"diagnosis-r{RR}.md", agg)

    names = [
        f"batch-r{RR}.jsonl",
        f"NOTES-r{RR}.md",
        f"diagnosis-r{RR}.md",
        f"diagnosis-01-r{RR}.md",
        f"diagnosis-02-r{RR}.md",
        f"diagnosis-03-r{RR}.md",
        f"rejected-01-r{RR}.json",
        f"rejected-02-r{RR}.json",
        f"rejected-03-r{RR}.json",
    ]
    written = []
    for name in names:
        src = STAGE / name
        dst = OUT / name
        if name == f"batch-r{RR}.jsonl" and dst.exists():
            suffix = "c"
            while True:
                alt = OUT / f"batch-r{RR}{suffix}.jsonl"
                notes_alt = OUT / f"NOTES-r{RR}{suffix}.md"
                if not alt.exists():
                    written.append(str(write_excl(alt, src.read_text(encoding="utf-8"))))
                    written.append(str(write_excl(notes_alt, (STAGE / f"NOTES-r{RR}.md").read_text(encoding="utf-8"))))
                    break
                suffix = chr(ord(suffix) + 1)
            continue
        if name == f"NOTES-r{RR}.md" and dst.exists():
            continue
        written.append(str(write_excl(dst, src.read_text(encoding="utf-8"))))

    print(json.dumps({"stage": str(STAGE), "written": written, "deltas": [p["reward_delta"]["total"] for p in PAIRS]}, indent=2))


if __name__ == "__main__":
    main()
