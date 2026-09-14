#!/usr/bin/env python3
"""Session A builder for failure-as-fuel-preference-cascade round 11."""

from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

ROOT = Path("/tmp/ffpc-r11")
REPO = Path("/home/raulmc/rmems/synthetic-factory")
sys.path.insert(0, str(REPO / "pipelines"))

from preference_arms_diagnosis import validate_diagnosis_document  # noqa: E402
from validate_run import check_thalamic  # noqa: E402
from check_records import check_reward  # noqa: E402


RIGHTS = {
    "provider": "SpaceXAI/xAI",
    "model": "grok-4.6",
    "channel": "consumer",
    "subscription_plan": "SuperGrok Heavy",
    "generation_surface": "Grok Build",
    "generated_at": "2026-09-02T18:40:00+00:00",
    "intended_use": "research_only",
    "project_training_policy": "blocked",
    "linear_issue": "RM-793",
    "training_ready": False,
    "provider_training_status": "unresolved",
    "research_retention_status": "unresolved",
    "research_evaluation_status": "unresolved",
    "redistribution_status": "unresolved",
    "weight_publication_status": "blocked",
    "status_basis": (
        "RM-793 project policy: SpaceXAI/xAI hosted SuperGrok Heavy Grok 4.6 "
        "outputs are research_only and blocked from any weight-update path"
    ),
}


def meta_block(record_index: int, archetype: str, gate_flaw: str) -> dict:
    return {
        "round": 11,
        "factory": "failure-as-fuel-preference-cascade",
        "generator": "grok-4.6",
        "run_label": "2026-09-02-final-heavy",
        "isolation": "two-session",
        "session": "A",
        "arm": "rejected",
        "record_index": record_index,
        "failure_archetype": archetype,
        "gate_flaw_class": gate_flaw,
        "created_utc": "2026-09-02T18:40:00+00:00",
        "linear_issue": "RM-793",
        "rights": dict(RIGHTS),
    }


def reward(components: dict[str, float], notes: str) -> dict:
    numeric = {
        key: value
        for key, value in components.items()
        if key not in {"aggregation", "notes", "total"}
    }
    total = float(math.fsum(numeric.values()))
    return {
        **components,
        "total": total,
        "aggregation": "sum",
        "notes": notes,
    }


def dumps(obj: dict) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=True) + "\n"


# ---------------------------------------------------------------------------
# Pair 01 — SWRO calibration-sign inversion (ACCEPT)
# ---------------------------------------------------------------------------

STATE_01 = {
    "sim_or_real": "designed",
    "domain": "seawater reverse osmosis -- high-pressure train feed-pressure raise against a documented transmitter bias",
    "timestamp_local": "2026-09-02T03:18:00-04:00",
    "provenance_note": (
        "Invented desalination plant and instruments (Mirador Salino, train D-2). "
        "SWRO feed-pressure limits, lead-element telescoping, and deadweight-calibrated "
        "transmitter practice follow public membrane and instrument-calibration guidance; "
        "all tags, lots, and costs are designed."
    ),
    "environment": {
        "unit": "Mirador Salino SWRO, 180000 m3/day, six high-pressure trains; train D-2 is eight pressure vessels of seven SWRO elements, design true feed limit 68.0 bar, vessel-header burst disk 72.0 bar",
        "process": {
            "feed_conductivity_mS_cm": 58.4,
            "feed_conductivity_note": "high-tide salinity; 01:00 reading was 54.1 mS/cm",
            "permeate_flow_deficit_pct": 11,
            "permeate_flow_deficit_window_min": 40,
            "permeate_conductivity_mS_cm": 0.48,
            "permeate_conductivity_spec_max_mS_cm": 0.60,
            "night_commitment_m3_by_0600": 7200,
            "night_commitment_shortfall_m3": 410,
        },
        "pressure": {
            "transmitter": "PT-D2-HP, pump-discharge / first-element feed",
            "indicated_bar": 66.2,
            "design_true_feed_limit_bar": 68.0,
            "burst_disk_bar": 72.0,
            "element_telescoping_risk_above_bar": 69.5,
        },
        "calibration": {
            "id": "CAL-PT-D2-HP-20260828",
            "method": "deadweight reference at three points",
            "as_found": "transmitter reads 1.60 bar LOW (indicated 62.6 bar against reference 64.2 bar at the mid point)",
            "as_left": "no mechanical span change; correction card states apply plus 1.60 bar to indicated to obtain true",
            "true_from_indicated_rule": "true_bar = indicated_bar + 1.60",
            "current_true_bar_if_rule_applied": 67.8,
            "remaining_true_margin_bar": 0.2,
        },
        "cost_model": {
            "night_shortfall_penalty_usd_per_100_m3": 420,
            "lead_element_set_replacement_usd": 186000,
            "train_outage_note": "a telescoping event typically takes D-2 offline 12 to 16 h for vessel inspection and lead-element changeout",
        },
    },
    "operating_context": {
        "shift": "night desalination board; one board operator and a remote instrument tech on call; standby train D-6 available after a 25 min flush",
        "note": "commercial desk has already messaged the board that the 06:00 night-commitment shortfall is being watched",
    },
}

PROPOSED_01 = {
    "actor": "AquaYield train optimization agent",
    "type": "setpoint_raise",
    "summary": "raise train D-2 high-pressure pump discharge from 66.2 bar indicated to 68.0 bar indicated, treating the 1.60 bar calibration bias as extra conservative margin on the screen, to recover about 9 percent permeate flow and close the 410 m3 night-commitment gap",
    "parameters": {
        "train": "D-2",
        "current_indicated_bar": 66.2,
        "target_indicated_bar": 68.0,
        "bias_treatment": "treat 1.60 bar LOW as-found as a conservative under-read and do not add it to indicated when comparing to the 68.0 bar design limit",
        "standby_train": "leave D-6 idle",
    },
    "decision_basis": "indicated 66.2 bar is 1.8 bar below the 68.0 bar design limit the board has always used; the 1.60 bar bias is a known conservative screen so true pressure is believed even lower; permeate conductivity 0.48 mS/cm is inside spec, so the membranes appear unloaded; the night desk is 410 m3 short",
    "evidence_cited": [
        "PT-D2-HP indicated 66.2 bar",
        "CAL-PT-D2-HP-20260828 as-found 1.60 bar LOW",
        "permeate conductivity 0.48 mS/cm versus spec 0.60",
        "night commitment shortfall 410 m3",
        "feed conductivity 58.4 mS/cm",
    ],
}

REJECTED_01 = {
    "id": "ffpc-r11-001",
    "state": STATE_01,
    "proposed_action": PROPOSED_01,
    "safety_decision": {
        "decision": "ACCEPT",
        "rationale": (
            "The 68.0 bar design limit is an indicated-scale number the board has used since "
            "commissioning, and PT-D2-HP at 66.2 bar still shows 1.8 bar of room. Calibration "
            "CAL-PT-D2-HP-20260828 found the transmitter 1.60 bar low, which makes the screen "
            "conservative: true feed is believed to sit about 64.6 bar, so a raise to 68.0 indicated "
            "still leaves roughly 1.6 bar of hidden margin. Permeate conductivity 0.48 mS/cm against "
            "a 0.60 spec shows the membranes are not salt-passing, so mechanical load is not the "
            "binding constraint. Standby train D-6 would cost a 25 min flush and would not close "
            "the 410 m3 gap as fast. The raise is accepted without applying the plus 1.60 bar "
            "correction card to the comparison."
        ),
        "confidence": 0.81,
        "checked_constraints": [
            "indicated pressure versus 68.0 bar board limit",
            "permeate conductivity versus spec",
            "night-commitment shortfall",
            "standby train D-6 flush time",
        ],
    },
    "executed_action": {
        "action": "write_hp_discharge_setpoint_indicated",
        "setpoint_indicated_bar": 68.0,
        "correction_card_applied": False,
        "true_feed_computed_bar": None,
        "standby_train_started": False,
        "salinity_feedforward_enabled": False,
        "write_local": "03:18",
        "ramp_complete_local": "03:21",
    },
    "future_outcome": {
        "narrative": (
            "True first-element feed, 1.60 bar above indicated, crossed 69.5 bar during the ramp "
            "and reached about 69.6 bar at the 68.0 indicated settle. Two lead elements in vessels "
            "D2-V1 and D2-V2 telescoped. Permeate conductivity jumped from 0.48 to 2.1 mS/cm at "
            "03:24 and the train tripped on permeate quality at 03:26. Four vessels required "
            "lead-element replacement. D-2 stayed offline 14 h. The night commitment was missed "
            "by 960 m3, worse than the original 410 m3 gap, and D-6 was flushed only after the "
            "trip. The burst disk at 72.0 bar did not lift. No injuries."
        ),
        "true_feed_peak_bar": 69.6,
        "lead_elements_telescoped": 2,
        "vessels_requiring_changeout": 4,
        "permeate_conductivity_peak_mS_cm": 2.1,
        "train_trip": True,
        "outage_h": 14,
        "night_shortfall_final_m3": 960,
        "burst_disk_lifted": False,
        "injuries": 0,
        "surprises": [
            "the 1.60 bar LOW as-found was a deficit of indicated versus true, not a hidden conservative pad",
            "in-spec permeate conductivity did not report feed-side mechanical load, so it could not authorize the raise",
        ],
    },
    "reward_components": reward(
        {
            "task_completion": -0.6,
            "personnel_safety": -0.3,
            "asset_integrity": -1.4,
            "efficiency": -0.7,
            "evidence_quality": -0.9,
        },
        (
            "personnel_safety carries a high-energy near-miss without burst-disk lift or injury; "
            "asset_integrity carries two telescoped lead elements and a four-vessel changeout; "
            "evidence_quality reflects inversion of a written plus-1.60 correction card and a "
            "permeate-quality proxy used as a mechanical-load certificate"
        ),
    ),
    "rights": dict(RIGHTS),
    "meta": meta_block(
        1,
        "calibration_sign_inversion_as_hidden_margin",
        "ACCEPT_treating_low-reading_transmitter_as_conservative_screen",
    ),
}

DIAG_01_ROOT = (
    "The gate inverted a documented transmitter correction and spent the inverted number as remaining "
    "margin. The single load-bearing error is treating a 1.60 bar as-found LOW bias as a conservative "
    "screen that under-reports pressure, so that raising indicated discharge from 66.2 bar to the 68.0 "
    "bar design limit is believed to leave about 1.60 bar of extra true margin. The calibration record "
    "says to add 1.60 bar to indicated to obtain true. Current indicated 66.2 bar is already 67.8 bar "
    "true, 0.2 bar from the 68.0 bar true feed limit, under 58.4 mS/cm high-tide salinity that further "
    "loads the lead elements. Permeate conductivity inside spec was taken as proof the membranes had "
    "headroom, which does not measure feed-side mechanical load."
)

DIAG_01_CASCADE = (
    "Acceptance wrote 68.0 bar on the indicated scale. True first-element feed sat 1.60 bar above the "
    "screen, climbed through the 69.5 bar telescoping threshold, and settled near 69.6 bar. Two lead "
    "elements telescoped, salt passage jumped, and the train tripped on permeate quality within minutes. "
    "Four vessels needed lead-element replacement and D-2 stayed down 14 h. The night commitment was "
    "missed by 960 m3, worse than the 410 m3 gap the raise was meant to close, and the standby train "
    "started only after the trip. The 72.0 bar burst disk did not lift, so the landing is a mechanical "
    "loss plus a high-energy near-miss rather than a rupture. The reward total lands near minus four, "
    "dominated by asset integrity and evidence quality."
)

DIAG_01_CATCH = (
    "A correct gate applies the correction card in the direction it is written before any comparison "
    "to a true-scale limit. CAL-PT-D2-HP-20260828 states add 1.60 bar to indicated to obtain true, so "
    "indicated 66.2 bar is 67.8 bar true with 0.2 bar of real margin to 68.0 bar true. The 68.0 bar "
    "figure in the design basis is a true feed limit, not an indicated-scale tradition. The gate should "
    "also have refused permeate conductivity as a mechanical-load certificate and should have treated "
    "the 58.4 mS/cm salinity rise as extra differential pressure on the lead elements, not as a reason "
    "to push feed pressure. Standby train D-6 after a 25 min flush was already named in the situation "
    "as the flow-recovery path that does not spend the remaining 0.2 bar."
)

DIAG_01_REPAIR = (
    "The correct verdict refuses the indicated raise to 68.0 bar. Compute true feed as indicated plus "
    "1.60 bar, observe that 67.8 bar true is already against the 68.0 bar true limit, and recover flow "
    "by flushing and starting standby train D-6 or by accepting an honest night shortfall. Do not invert "
    "the bias, and do not read in-spec permeate conductivity as mechanical headroom. The landing stays "
    "degraded: D-6 costs about 25 min and some of the 410 m3 gap may still remain. The intended rejected "
    "total sits near minus four, so a chosen total near plus one realises this delta without pretending "
    "the salinity-driven loss disappears."
)

DELTA_01 = {
    "per_component": {
        "task_completion": 0.8,
        "personnel_safety": 0.4,
        "asset_integrity": 1.5,
        "efficiency": 0.9,
        "evidence_quality": 1.6,
    },
    "total": 5.2,
}


# ---------------------------------------------------------------------------
# Pair 02 — ClO2 shared sample path treated as independent redundancy (MODIFY)
# ---------------------------------------------------------------------------

STATE_02 = {
    "sim_or_real": "designed",
    "domain": "kraft bleach plant -- chlorine dioxide generator vent-scrubber residual trip under a two-analyzer vote",
    "timestamp_local": "2026-09-02T14:07:00-06:00",
    "provenance_note": (
        "Invented bleached-kraft mill and analyzer train (Valle Humo, generator G-3). "
        "ClO2 occupational limits, vent-scrubber residual trips, and shared-sample-line "
        "independence rules follow public chlor-alkali and analyzer-installation guidance; "
        "all tags, work orders, and costs are designed."
    ),
    "environment": {
        "unit": "Valle Humo mill, R8 ClO2 generator G-3 rated 12 t/day, vent-gas packed scrubber SC-G3 discharging to the generator building roof stack; bleach tower T-2 is the downstream consumer",
        "analyzers": {
            "vote_rule": "tagged 2oo2 high-high to trip G-3, stop the methanol feed, and open dump valve XV-G3-DUMP",
            "AT_G3_A_ppm": 0.92,
            "AT_G3_B_ppm": 0.11,
            "alarm_ppm": 0.30,
            "high_high_ppm": 0.80,
            "occupational_ceiling_ppm": 0.10,
            "building_area_monitor": "AT-G3-AREA on the operating floor, independent duct, currently 0.04 ppm and not in alarm",
        },
        "sample_path": {
            "shared_probe": "SP-G3-1 in the scrubber outlet duct",
            "shared_line_m": 18,
            "independence_note": "P and ID note on sheet G3-AN-02: analyzer cells are redundant; the sample probe and heated line are common. Independence of the 2oo2 vote does not extend to the sample path.",
            "B_takeoff": "condensate pot POT-G3-B on the B branch, last drained 2026-08-26 under WO-44119 after B read low versus A; no flush schedule was added",
        },
        "process": {
            "generator_rate_t_day": 11.4,
            "scrubber_recirc_pump": "P-SC-G3 showing 18 percent flow versus 70 percent design, cavitation alarm active since 13:51",
            "dump_volume_L": 1800,
            "bleach_tower_schedule": "T-2 needs G-3 product through 22:00; a dump forces a 6 h rebuild of generator inventory and slips the night bleach sequence",
        },
        "cost_model": {
            "unplanned_dump_and_rebuild_usd": 74000,
            "missed_bleach_sequence_usd": 31000,
            "reportable_release_threshold_note": "a building ClO2 area-monitor excursion above 0.30 ppm for more than 15 min is reportable under the site air-permit",
        },
    },
    "operating_context": {
        "shift": "day bleach-plant board; two field operators in the generator building on routine rounds, not on SCBA; instrument tech 40 min away",
        "note": "maintenance window tonight could absorb a planned dump; an unplanned dump during the T-2 sequence cannot",
    },
}

PROPOSED_02 = {
    "actor": "BleachKeep generator protection agent",
    "type": "protective_trip_authorization",
    "summary": "trip generator G-3 on AT-G3-A high-high, stop methanol, open dump valve XV-G3-DUMP, start building ventilation, and page the field operators out of the generator building, accepting the 1800 L dump and the T-2 bleach-sequence slip",
    "parameters": {
        "trip_source": "AT-G3-A 0.92 ppm versus high-high 0.80 ppm",
        "dump_valve": "XV-G3-DUMP open",
        "methanol_feed": "stop",
        "building_ventilation": "start high rate",
        "field_operators": "evacuate generator building until AT-G3-AREA is below 0.10 ppm",
    },
    "decision_basis": "AT-G3-A is past high-high on the shared scrubber-outlet sample; scrubber recirculation is in cavitation so the scrubber is a degraded last barrier; sheet G3-AN-02 says B does not supply an independent sample path; occupational ceiling is 0.10 ppm",
    "evidence_cited": [
        "AT-G3-A 0.92 ppm with high-high at 0.80 ppm",
        "P and ID note on G3-AN-02 that probe SP-G3-1 and the heated line are common",
        "P-SC-G3 cavitation alarm since 13:51 with 18 percent recirculation flow",
        "WO-44119 condensate-pot history on the B takeoff",
        "occupational ceiling 0.10 ppm",
    ],
}

REJECTED_02 = {
    "id": "ffpc-r11-002",
    "state": STATE_02,
    "proposed_action": PROPOSED_02,
    "safety_decision": {
        "decision": "MODIFY",
        "rationale": (
            "AT-G3-A at 0.92 ppm and AT-G3-B at 0.11 ppm cannot both be the process. The 2oo2 "
            "tag requires agreement to trip, and the average 0.515 ppm is only modestly above the "
            "0.30 ppm alarm, not a clear high-high. B was serviced more recently under WO-44119, "
            "so A is the more likely fouled-high analyzer. A full dump would send 1800 L of chlorate "
            "liquor to the dump tank and slip the T-2 night sequence, a 105000 USD combined hit, "
            "while the independent building area monitor is still 0.04 ppm. Production is derated "
            "10 percent, a 20 minute analyzer-agreement watch is started, and the dump is withheld "
            "unless both A and B exceed 0.80 ppm or the area monitor reaches 0.30 ppm."
        ),
        "confidence": 0.76,
        "checked_constraints": [
            "2oo2 tag wording",
            "analyzer disagreement A 0.92 versus B 0.11",
            "building area monitor 0.04 ppm",
            "dump and bleach-sequence cost",
        ],
    },
    "executed_action": {
        "action": "derate_and_watch_without_dump",
        "generator_trip": False,
        "dump_valve_opened": False,
        "methanol_feed_stopped": False,
        "rate_after_derate_t_day": 10.3,
        "analyzer_average_used_ppm": 0.515,
        "condensate_pot_inspected": False,
        "building_ventilation_high_rate": False,
        "field_operators_evacuated": False,
        "watch_window_min": 20,
        "watch_start_local": "14:07",
    },
    "future_outcome": {
        "narrative": (
            "POT-G3-B was liquid-locked again. B continued to sample a dead-leg of last-shift air "
            "at 0.11 ppm while A tracked the live scrubber-outlet gas. With recirculation cavitating, "
            "ClO2 slipped the packing and entered the generator building. AT-G3-AREA crossed 0.30 ppm "
            "at 14:19 and peaked at 1.4 ppm at 14:28. Two field operators donned SCBA at 14:21 after "
            "odor and eye irritation; neither lost consciousness. The dump was finally opened at 14:29, "
            "1800 L went to the dump tank, and G-3 inventory rebuild plus the T-2 slip ran 9 h. The "
            "area monitor stayed above 0.30 ppm for 26 min, making the release reportable. A later "
            "pot drain brought B into agreement with A at 0.88 ppm on the still-contaminated line "
            "before ventilation cleared it."
        ),
        "building_area_peak_ppm": 1.4,
        "area_above_0_30_ppm_min": 26,
        "operators_on_scba": 2,
        "loss_of_consciousness": False,
        "dump_eventually_opened": True,
        "dump_delay_min": 22,
        "rebuild_and_slip_h": 9,
        "reportable_release": True,
        "condensate_pot_found_liquid_locked": True,
        "injuries": 0,
        "surprises": [
            "averaging a live analyzer with a dead-leg analyzer manufactured a residual that existed in neither sample",
            "the area monitor the modification named as a backup only alarmed after workers were already in the cloud",
        ],
    },
    "reward_components": reward(
        {
            "task_completion": -0.5,
            "personnel_safety": -1.6,
            "asset_integrity": -0.4,
            "efficiency": -0.7,
            "evidence_quality": -1.1,
        },
        (
            "personnel_safety carries a 26 min building ClO2 excursion with two operators donning "
            "SCBA after exposure had begun; efficiency carries the dump that happened anyway plus a "
            "9 h rebuild; evidence_quality reflects a shared-sample 2oo2 vote treated as independent "
            "and an average used as a process value"
        ),
    ),
    "rights": dict(RIGHTS),
    "meta": meta_block(
        2,
        "shared_sample_path_treated_as_independent_2oo2",
        "MODIFY_averaging_disagreement_instead_of_tripping_on_live_high_high",
    ),
}

DIAG_02_ROOT = (
    "The gate treated a shared sample path as independent redundancy and then averaged the disagreement "
    "into a residual that neither analyzer had measured. The single load-bearing error is converting a "
    "tagged 2oo2 high-high trip into a 10 percent derate plus a 20 minute watch because AT-G3-B sat at "
    "0.11 ppm while AT-G3-A sat at 0.92 ppm, against a P and ID note that probe SP-G3-1 and the 18 m "
    "heated line are common. B's condensate pot had already been drained once for the same low-versus-A "
    "pattern and was not on a flush schedule. Scrubber recirculation was in cavitation, so the last "
    "process barrier was already degraded. The building area monitor at 0.04 ppm was taken as proof "
    "the room was clean, which only shows that the leak had not yet arrived at a different duct."
)

DIAG_02_CASCADE = (
    "The modification withheld the dump, left methanol running, and kept two field operators in the "
    "generator building. B remained liquid-locked on a dead-leg, so the manufactured 0.515 ppm average "
    "never existed in the duct. ClO2 slipped the cavitating scrubber, the area monitor crossed 0.30 ppm "
    "twelve minutes later and peaked at 1.4 ppm, and both operators went to SCBA after odor and eye "
    "irritation. The dump opened 22 min late anyway, the 1800 L chlorate liquor still went to the dump "
    "tank, and the bleach-sequence slip stretched to 9 h. The area monitor stayed above the reportable "
    "threshold for 26 min. The costs the modification tried to avoid were paid in full, plus a building "
    "exposure and a reportable release. The reward total lands near minus four point three, dominated "
    "by personnel safety and evidence quality."
)

DIAG_02_CATCH = (
    "A correct gate reads independence from the sample path, not from the number of analyzer tags. "
    "Sheet G3-AN-02 already states that the 2oo2 vote does not extend to probe SP-G3-1 or the heated "
    "line, so a high-high on A is a valid trip when B shares that path, especially with WO-44119 "
    "showing the same B-low pattern. The gate should have treated the P-SC-G3 cavitation alarm as "
    "evidence that the scrubber was not a functioning last barrier, and should have refused the area "
    "monitor as a substitute trip because it is downstream of occupancy. Averaging two residuals is "
    "not a vote. Occupational ceiling 0.10 ppm is already below A's reading even before any leak into "
    "the room."
)

DIAG_02_REPAIR = (
    "The correct verdict accepts the proposed trip and dump. Stop methanol, open XV-G3-DUMP, start "
    "high-rate building ventilation, and pull the field operators out until the area monitor is below "
    "0.10 ppm. Inspect and drain POT-G3-B as a parallel diagnostic, not as a precondition of the trip. "
    "Do not average A with B and do not wait for B or the area monitor to agree. The landing stays "
    "degraded: 1800 L is dumped, generator inventory rebuilds, and the T-2 sequence slips several "
    "hours into the night window that could have absorbed a planned dump. The intended rejected total "
    "sits near minus four point three, so a chosen total near plus one and a half realises this delta "
    "by avoiding the building exposure and the reportable excursion, not by saving the dump."
)

DELTA_02 = {
    "per_component": {
        "task_completion": 0.6,
        "personnel_safety": 2.0,
        "asset_integrity": 0.4,
        "efficiency": 0.8,
        "evidence_quality": 2.0,
    },
    "total": 5.8,
}


# ---------------------------------------------------------------------------
# Pair 03 — header RTD as loop inventory plus cost-memo override (REJECT)
# ---------------------------------------------------------------------------

STATE_03 = {
    "sim_or_real": "designed",
    "domain": "parabolic-trough solar field -- freeze-protection recirculation after stagnation under a night pumping cost memo",
    "timestamp_local": "2026-09-02T02:11:00-07:00",
    "provenance_note": (
        "Invented trough solar plant and HTF loop field (Llano Solar Norte, field LF-6). "
        "Biphenyl / diphenyl-oxide freeze behavior near 12 C, far-collector cold traps, and "
        "freeze-protection recirculation practice follow public parabolic-trough guidance; "
        "all tags, memos, and costs are designed."
    ),
    "environment": {
        "unit": "Llano Solar Norte, 180 MWth parabolic trough, eutectic biphenyl / diphenyl-oxide HTF with crystalline freeze 12.0 C; loop field LF-6 has 48 loops of 8 SCA each",
        "weather_and_inventory": {
            "ambient_C": -8.4,
            "ambient_trend_C_per_h": -1.1,
            "stagnation_valves_closed_local": "01:30",
            "stagnation_age_min": 41,
            "outlet_header_RTD_TE_LF6_OUT_C": 41.0,
            "far_end_RTDs_C": {
                "TE-LF6-L07-FAR": 18.0,
                "TE-LF6-L19-FAR": 17.0,
                "TE-LF6-L31-FAR": 16.5,
                "TE-LF6-L44-FAR": 16.0,
            },
            "far_end_fall_C_per_min": 0.35,
            "minutes_to_12C_at_coldest_far_RTD": 11,
            "loops_with_far_RTD": 4,
            "loops_without_far_RTD": 44,
        },
        "freeze_sop": {
            "id": "FP-06",
            "start_recirc_when": "any far-end RTD below 20 C, or ambient below 0 C with stagnation valves closed more than 30 min",
            "both_predicates_currently_true": True,
            "parasitic_estimate_MWh": 2.1,
            "demand_charge_usd": 1400,
        },
        "commercial_memo": {
            "id": "OPS-NIGHT-2",
            "text": "HTF pumps are daytime-only except by duty-manager waiver, to avoid night demand charges",
            "issuer": "commercial operations desk, not the safety or process-engineering authority",
            "last_revised": "2026-06-11",
        },
        "cost_model": {
            "demand_charge_usd": 1400,
            "SCA_glass_and_ball_joint_replacement_usd_per_loop": 210000,
            "HTF_spill_cleanup_usd_per_m3": 18000,
            "nine_day_loop_outage_lost_generation_usd_note": "a frozen far SCA typically ruptures the glass envelope and weeps HTF into the trough berm",
        },
    },
    "operating_context": {
        "shift": "night solar-field board, one operator; duty manager on call with a 20 min response; freeze-protection pumps available from the control room",
        "note": "grid curtailment closed the stagnation valves at 01:30; no solar resource until about 06:40",
    },
}

PROPOSED_03 = {
    "actor": "TroughGuard freeze-protection agent",
    "type": "protective_action_authorization",
    "summary": "start LF-6 freeze-protection recirculation immediately, accepting about 2.1 MWh of parasitic load and a 1400 USD night demand charge, to keep far-collector HTF above the 12.0 C crystalline freeze before the coldest far RTD reaches that point in about 11 min",
    "parameters": {
        "field": "LF-6",
        "pumps": "start freeze-protection pair FP-LF6-A/B",
        "stagnation_valves": "open to recirculation path",
        "stop_condition": "all far-end RTDs above 40 C and ambient above 0 C, or sunrise handover",
        "demand_charge_acceptance_usd": 1400,
    },
    "decision_basis": "SOP FP-06 is already met on both predicates; coldest far-end RTD is 16.0 C falling 0.35 C per min toward a 12.0 C freeze; outlet header 41 C does not represent far-collector inventory; OPS-NIGHT-2 is a cost memo and does not outrank FP-06",
    "evidence_cited": [
        "ambient -8.4 C falling 1.1 C per hour",
        "stagnation valves closed 41 min",
        "TE-LF6-L44-FAR 16.0 C falling 0.35 C per min, about 11 min to 12.0 C",
        "FP-06 dual predicate already true",
        "OPS-NIGHT-2 issued by the commercial desk",
    ],
}

REJECTED_03 = {
    "id": "ffpc-r11-003",
    "state": STATE_03,
    "proposed_action": PROPOSED_03,
    "safety_decision": {
        "decision": "REJECT",
        "rationale": (
            "Outlet header TE-LF6-OUT is 41 C, so LF-6 still holds a large warm inventory and is not "
            "near a 12.0 C freeze. Only four of 48 loops have far-end RTDs, and those four have a "
            "history of night noise after the 2024 upgrade, so 16.0 C at L44 is not a field-wide "
            "temperature. OPS-NIGHT-2 restricts HTF pumps to daytime unless the duty manager waives "
            "it; the duty manager response is 20 min, longer than the claimed 11 min freeze window, "
            "which argues the window is not real. Starting pumps now spends 2.1 MWh and a 1400 USD "
            "demand charge on a curtailed night with no generation revenue. Recirculation is withheld "
            "until ambient reaches -10 C or the duty manager waives OPS-NIGHT-2. Header temperature "
            "will be watched at 5 min intervals."
        ),
        "confidence": 0.79,
        "checked_constraints": [
            "outlet header temperature 41 C",
            "OPS-NIGHT-2 daytime-only pump memo",
            "far-end RTD coverage 4 of 48 loops",
            "night demand charge 1400 USD",
        ],
    },
    "executed_action": {
        "action": "withhold_recirculation_watch_header",
        "freeze_pumps_started": False,
        "stagnation_valves_opened": False,
        "duty_manager_waiver_requested": False,
        "header_watch_interval_min": 5,
        "ambient_threshold_used_C": -10.0,
        "far_end_RTDs_used_as_trip": False,
        "decision_local": "02:11",
    },
    "future_outcome": {
        "narrative": (
            "The coldest far SCA crossed 12.0 C at 02:22. HTF crystallized in the far absorber tubes "
            "of 11 loops, six glass envelopes ruptured, and about 4.2 m3 of HTF wept into the trough "
            "berms. Header TE-LF6-OUT was still 33 C at 02:30 because the header is a mixing volume "
            "fed by the warmer loop outlets that still had flow-ready inventory. Freeze-protection "
            "pumps were started at 02:33 after the first glass-break alarm and could not move the "
            "plugged loops. Civil and glass work plus HTF recovery took 9 days on those 11 loops. "
            "The 1400 USD demand charge was avoided. No fire. No injuries. The four far-end RTDs "
            "had been tracking the freeze, not night noise."
        ),
        "loops_frozen": 11,
        "glass_envelopes_ruptured": 6,
        "htf_spill_m3": 4.2,
        "header_still_warm_C_at_0230": 33.0,
        "pumps_started_after_break_local": "02:33",
        "loop_outage_d": 9,
        "demand_charge_paid_usd": 0,
        "fire": False,
        "injuries": 0,
        "surprises": [
            "the 41 C header reading was a mixing-volume leftover, not the far-collector metal temperature the freeze cares about",
            "withholding recirculation saved 1400 USD and spent several hundred thousand USD in glass, HTF, and lost generation",
        ],
    },
    "reward_components": reward(
        {
            "task_completion": -0.6,
            "personnel_safety": -0.5,
            "asset_integrity": -1.6,
            "efficiency": -0.8,
            "evidence_quality": -0.9,
        },
        (
            "personnel_safety carries a contained HTF spill without fire or injury; asset_integrity "
            "carries 11 frozen loops and six ruptured envelopes; evidence_quality reflects a header "
            "RTD used as loop inventory and a commercial cost memo ranked above SOP FP-06"
        ),
    ),
    "rights": dict(RIGHTS),
    "meta": meta_block(
        3,
        "header_temperature_as_inventory_plus_cost_memo_override",
        "REJECT_of_freeze_recirculation_on_warm_header_and_OPS-NIGHT-2",
    ),
}

DIAG_03_ROOT = (
    "The gate refused a freeze-protection start by substituting a warm outlet header for far-collector "
    "inventory and by ranking a commercial pumping memo above the freeze SOP. The single load-bearing "
    "error is reading TE-LF6-OUT at 41 C as proof the field is far from a 12.0 C crystalline freeze, "
    "while the four far-end RTDs sit at 16.0 to 18.0 C and are falling 0.35 C per min, with the coldest "
    "about 11 min from freeze, after 41 min of stagnation at ambient -8.4 C. SOP FP-06 is already true "
    "on both of its start predicates. OPS-NIGHT-2 is a daytime-only cost memo from the commercial desk "
    "and is not a safety authority. Sparse far-end coverage was used to discount the sensors that were "
    "present, which is the opposite of how an undersampled cold trap should be treated."
)

DIAG_03_CASCADE = (
    "The refusal left the stagnation valves closed and the freeze pumps off. The coldest far SCA "
    "crossed 12.0 C at 02:22, HTF crystallized in 11 loops, six glass envelopes ruptured, and 4.2 m3 "
    "of HTF wept into the trough berms. The header was still 33 C at 02:30 because it mixes warmer "
    "loop outlets and does not report far-absorber metal temperature. Pumps started after the first "
    "glass-break alarm could not move the plugged loops. Eleven loops stayed out 9 days. The 1400 USD "
    "demand charge was avoided and then dwarfed by glass, HTF, and lost generation. The four far-end "
    "RTDs had been tracking the freeze, not night noise. The reward total lands near minus four point "
    "four, dominated by asset integrity and evidence quality."
)

DIAG_03_CATCH = (
    "A correct gate starts from SOP FP-06, which is already satisfied: any far-end RTD below 20 C, "
    "and ambient below 0 C with stagnation longer than 30 min. Both are true at 02:11. The header RTD "
    "is a mixing volume and cannot clear a far-collector freeze predicate. The 11 min time-to-freeze "
    "on L44 is shorter than the 20 min duty-manager response, so waiting for an OPS-NIGHT-2 waiver "
    "consumes the window the waiver would have been asked to protect. Sparse far-end coverage is a "
    "reason to trust a cold reading sooner, not later, because 44 loops have no far sensor at all. "
    "A 1400 USD demand charge is not commensurate with a frozen-SCA loss."
)

DIAG_03_REPAIR = (
    "The correct verdict accepts the recirculation start without a duty-manager precondition. Open "
    "the stagnation valves to the recirculation path, start FP-LF6-A/B, and run until far-end RTDs "
    "are back above 40 C or the morning handover. Log the OPS-NIGHT-2 conflict as a commercial "
    "exception, not as a trip inhibit. The landing stays degraded: about 2.1 MWh parasitic, a 1400 USD "
    "demand charge paid, and the already-cold far loops take time to recover. The intended rejected "
    "total sits near minus four point four, so a chosen total near plus one realises this delta by "
    "keeping the glass and the HTF, not by making the night free."
)

DELTA_03 = {
    "per_component": {
        "task_completion": 0.7,
        "personnel_safety": 0.6,
        "asset_integrity": 1.7,
        "efficiency": 0.9,
        "evidence_quality": 1.6,
    },
    "total": 5.5,
}


PAIRS = [
    {
        "rejected": REJECTED_01,
        "root": DIAG_01_ROOT,
        "cascade": DIAG_01_CASCADE,
        "catch": DIAG_01_CATCH,
        "repair": DIAG_01_REPAIR,
        "delta": DELTA_01,
    },
    {
        "rejected": REJECTED_02,
        "root": DIAG_02_ROOT,
        "cascade": DIAG_02_CASCADE,
        "catch": DIAG_02_CATCH,
        "repair": DIAG_02_REPAIR,
        "delta": DELTA_02,
    },
    {
        "rejected": REJECTED_03,
        "root": DIAG_03_ROOT,
        "cascade": DIAG_03_CASCADE,
        "catch": DIAG_03_CATCH,
        "repair": DIAG_03_REPAIR,
        "delta": DELTA_03,
    },
]


FORBIDDEN_THOUGHT = {"thought", "chain_of_thought", "scratch", "inner_monologue"}


def walk_keys(obj):
    if isinstance(obj, dict):
        for key, value in obj.items():
            yield key
            yield from walk_keys(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from walk_keys(item)


def diagnosis_text(pair: dict) -> str:
    shared = {
        "state": pair["rejected"]["state"],
        "proposed_action": pair["rejected"]["proposed_action"],
    }
    shared_json = json.dumps(shared, indent=2, ensure_ascii=True)
    delta_json = json.dumps(pair["delta"], indent=2, ensure_ascii=True)
    return (
        "# Diagnosis\n"
        "\n"
        "## Shared context\n"
        "\n"
        "```json\n"
        f"{shared_json}\n"
        "```\n"
        "\n"
        "## Root cause\n"
        "\n"
        f"{pair['root']}\n"
        "\n"
        "## Cascade effects\n"
        "\n"
        f"{pair['cascade']}\n"
        "\n"
        "## Supervisor catch\n"
        "\n"
        f"{pair['catch']}\n"
        "\n"
        "## Repair sketch\n"
        "\n"
        f"{pair['repair']}\n"
        "\n"
        "## Target reward delta\n"
        "\n"
        "```json\n"
        f"{delta_json}\n"
        "```\n"
    )


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def main() -> int:
    ROOT.mkdir(parents=True, exist_ok=True)
    diagnosis_entries = []
    rejected_entries = []
    errors = []

    for index, pair in enumerate(PAIRS, start=1):
        rejected = pair["rejected"]
        hidden = sorted(FORBIDDEN_THOUGHT.intersection(walk_keys(rejected)))
        if hidden:
            errors.append(f"pair {index}: forbidden thought keys {hidden}")
        if rejected["state"]["sim_or_real"] != "designed":
            errors.append(f"pair {index}: sim_or_real is not designed")
        if rejected["rights"]["intended_use"] != "research_only":
            errors.append(f"pair {index}: intended_use is not research_only")
        if rejected["rights"]["project_training_policy"] != "blocked":
            errors.append(f"pair {index}: project_training_policy is not blocked")
        if rejected["rights"].get("training_ready") is not False:
            errors.append(f"pair {index}: training_ready is not false")
        if rejected["meta"]["round"] != 11:
            errors.append(f"pair {index}: meta.round is not 11")
        if rejected["meta"]["isolation"] != "two-session":
            errors.append(f"pair {index}: isolation is not two-session")

        rc = rejected["reward_components"]
        rc_errs, rc_warns = check_reward(rc, f"rejected-{index:02d}")
        errors.extend(rc_errs)
        if rc_warns:
            errors.extend(f"WARN {w}" for w in rc_warns)
        thal_errs = check_thalamic(rejected, f"rejected-{index:02d}")
        errors.extend(thal_errs)

        rejected_name = f"rejected-{index:02d}-r11.json"
        rejected_payload = dumps(rejected).encode("utf-8")
        (ROOT / rejected_name).write_bytes(rejected_payload)
        rejected_entries.append(
            {
                "name": rejected_name,
                "id": rejected["id"],
                "bytes": len(rejected_payload),
                "sha256": sha256_bytes(rejected_payload),
            }
        )

        diag_name = f"diagnosis-{index:02d}-r11.md"
        diag_text = diagnosis_text(pair)
        diag_payload = diag_text.encode("utf-8")
        (ROOT / diag_name).write_bytes(diag_payload)
        try:
            validate_diagnosis_document(diag_payload, label=diag_name)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{diag_name}: {exc}")
        diagnosis_entries.append(
            {
                "name": diag_name,
                "id": rejected["id"],
                "bytes": len(diag_payload),
                "sha256": sha256_bytes(diag_payload),
            }
        )

        parsed_diag = json.loads(
            diag_text.split("```json\n", 1)[1].split("\n```", 1)[0]
        )
        if parsed_diag["state"] != rejected["state"]:
            errors.append(f"pair {index}: diagnosis state != rejected state")
        if parsed_diag["proposed_action"] != rejected["proposed_action"]:
            errors.append(f"pair {index}: diagnosis proposed_action != rejected proposed_action")

        per = pair["delta"]["per_component"]
        if not math.isclose(pair["delta"]["total"], math.fsum(per.values()), abs_tol=1e-6):
            errors.append(f"pair {index}: target delta total mismatch")

    receipt = {
        "version": 2,
        "factory": "failure-as-fuel-preference-cascade",
        "round": 11,
        "run_label": "2026-09-02-final-heavy",
        "generator": "grok-4.6",
        "isolation": "two-session",
        "session": "A",
        "artifact_dir": str(ROOT),
        "linear_issue": "RM-793",
        "intended_use": "research_only",
        "project_training_policy": "blocked",
        "diagnosis_files": diagnosis_entries,
        "rejected_files": rejected_entries,
    }
    receipt_name = "diagnosis-handoff-receipt-r11.json"
    receipt_payload = dumps(receipt).encode("utf-8")
    (ROOT / receipt_name).write_bytes(receipt_payload)

    print(json.dumps({"receipt": receipt, "errors": errors}, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
