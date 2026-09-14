#!/usr/bin/env python3
"""Session B: synthesize chosen arms from diagnosis Shared-context only."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, "/home/raulmc/rmems/synthetic-factory/pipelines")
from preference_arms_diagnosis import diagnosis_narrative_text  # noqa: E402
from preference_arms_text import shares_copied_phrasing  # noqa: E402
from validate_run import HIDDEN_THOUGHT_KEYS, check_thalamic  # noqa: E402

STAGE = Path("/tmp/ffpc-r11")
GENERATED_AT = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

RIGHTS = {
    "provider": "SpaceXAI/xAI",
    "model": "grok-4.6",
    "channel": "consumer",
    "subscription_plan": "SuperGrok Heavy",
    "generation_surface": "SuperGrok Heavy chat",
    "generated_at": GENERATED_AT,
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


def extract_shared(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"## Shared context\n\n```json\n(.*?)\n```", text, re.S)
    if not match:
        raise SystemExit(f"no Shared context JSON in {path}")
    obj = json.loads(match.group(1))
    if set(obj) != {"state", "proposed_action"}:
        raise SystemExit(f"unexpected shared-context keys in {path}: {sorted(obj)}")
    return obj


def meta(record_index: int, diagnosis_name: str) -> dict:
    return {
        "round": 11,
        "factory": "failure-as-fuel-preference-cascade",
        "generator": "grok-4.6",
        "run_label": "2026-09-02-final-heavy",
        "isolation": "two-session",
        "session": "B",
        "pair_role": "chosen",
        "source_diagnosis": diagnosis_name,
        "record_index": record_index,
        "rights": dict(RIGHTS),
    }


def reward(task, personnel, asset, efficiency, evidence, notes: str) -> dict:
    total = round(task + personnel + asset + efficiency + evidence, 6)
    return {
        "task_completion": task,
        "personnel_safety": personnel,
        "asset_integrity": asset,
        "efficiency": efficiency,
        "evidence_quality": evidence,
        "total": total,
        "aggregation": "unweighted_sum",
        "component_notes": notes,
    }


CHOSEN_BODIES = {
    1: {
        "id": "ffpc-r11-001-chosen",
        "safety_decision": {
            "decision": "REJECT",
            "rationale": (
                "CAL-PT-D2-HP-20260828 is an additive span card, not a hidden cushion "
                "on the screen: 66.2 indicated plus 1.60 equals 67.8 bar true. The 68.0 "
                "bar design cap lives on the true-feed scale, so mechanical room left is "
                "0.2 bar. Painting 68.0 on the indicated face would put first-element "
                "feed at 69.6 bar true, already across the 69.5 bar telescoping line. "
                "Permeate at 0.48 mS/cm inside a 0.60 spec does not measure feed-side "
                "thrust, and the 58.4 mS/cm high-tide salinity loads the lead elements "
                "further. Hold train D-2 at 66.2 indicated. Recover cubic metres by "
                "flushing standby D-6, whose 25-minute prep is already named on the "
                "board. Pay whatever slice of the 410 m3 night gap remains after D-6 is "
                "online rather than spend the last 0.2 bar."
            ),
            "evidence_basis": [
                "CAL-PT-D2-HP-20260828 as-found 1.60 bar LOW, as-left rule true = indicated + 1.60",
                "PT-D2-HP indicated 66.2 bar → 67.8 bar true, 0.2 bar under the 68.0 bar true feed limit",
                "telescoping risk tagged above 69.5 bar true; 68.0 indicated would be 69.6 bar true",
                "feed conductivity 58.4 mS/cm versus 54.1 at 01:00, extra lead-element differential",
                "standby train D-6 available after a 25 min flush; night shortfall 410 m3 is commercial not mechanical",
            ],
            "checks": [
                "applied the deadweight card in the written direction before comparing to the true-scale limit",
                "converted the proposed 68.0 indicated target to 69.6 bar true and compared it to the 69.5 bar telescoping line",
                "refused in-spec permeate conductivity as a certificate of feed-side mechanical headroom",
                "treated the high-tide salinity rise as additional lead-element load, not as a reason to push discharge",
                "selected D-6 flush-and-start as the flow-recovery path that does not spend the remaining 0.2 bar",
            ],
            "residual_risk": (
                "D-6's 25 min flush plus any leftover night-volume gap still incur shortfall "
                "penalty; accepted against a telescoping and 12-to-16 h D-2 outage"
            ),
        },
        "executed_action": {
            "action": "hold_d2_start_standby_d6",
            "action_type": "setpoint_hold_standby_start",
            "status": "d2_held_d6_started",
            "result": "true_feed_uncrossed_limit",
            "outcome": "partial_shortfall_no_telescoping",
            "authorization": "REJECT of indicated raise; CAL-PT-D2-HP-20260828 attached to the hold log",
            "steps": [
                {
                    "t_local": "03:18:22",
                    "step": "computed true feed 67.8 bar from indicated 66.2 plus 1.60; remaining true margin 0.2 bar",
                },
                {
                    "t_local": "03:18:41",
                    "step": "blocked the 68.0 indicated write on D-2; discharge held at 66.2 indicated",
                },
                {
                    "t_local": "03:19:05",
                    "step": "started the 25 min flush on standby train D-6; instrument tech paged for the correction-card check",
                },
                {
                    "t_local": "03:44:18",
                    "step": "D-6 online after flush; permeate combined with held D-2 toward the 06:00 commitment",
                },
                {
                    "t_local": "06:00:00",
                    "step": "night volume closed 187 m3 short of 7200 m3; D-2 lead-element differential never crossed 69.5 bar true",
                },
            ],
            "d2_indicated_bar_held": 66.2,
            "d2_true_bar_held": 67.8,
            "d6_flush_min": 25,
            "d6_online_local": "03:44:18",
            "deviations": "none; commercial desk was told the 06:00 gap would not be closed by spending the 0.2 bar",
        },
        "future_outcome": {
            "status": "d2_intact_d6_carrying_share",
            "outcome": "lead_elements_preserved",
            "result": "no_telescoping_partial_shortfall",
            "success": True,
            "hazard_avoided": "lead_element_telescoping_d2",
            "near_miss": False,
            "estop": False,
            "timeline": [
                {
                    "t_local": "03:21",
                    "event": "D-2 true feed remained 67.8 bar; first-element differential stable under 58.4 mS/cm feed",
                },
                {
                    "t_local": "03:44",
                    "event": "D-6 permeate joined the header after the 25 min flush; combined flow recovered most of the 11 percent D-2 deficit",
                },
                {
                    "t_local": "04:10",
                    "event": "permeate conductivity on D-2 stayed 0.49 mS/cm; no salt-passage step-up",
                },
                {
                    "t_local": "06:00",
                    "event": "night commitment 7013 m3 versus 7200; shortfall 187 m3 versus the 410 m3 gap the raise was meant to erase",
                },
                {
                    "t_local": "08:40",
                    "event": "day crew confirmed no telescoping on D-2 lead elements; correction card remains in force pending a mechanical span change",
                },
            ],
            "observed_effects": [
                "D-2 held at 66.2 indicated / 67.8 bar true; telescoping threshold 69.5 bar never reached",
                "standby D-6 carried the recoverable flow after a 25 min flush",
                "night commitment missed by 187 m3 (penalty 785 USD at 420 per 100 m3), better than a post-trip 960 m3 miss and a 14 h D-2 outage",
                "lead-element set replacement 186000 USD avoided; burst disk at 72.0 bar unused",
                "commercial desk received an honest shortfall rather than a train trip",
            ],
            "state_delta": {
                "d2_status": "online_held_at_66_2_indicated",
                "d6_status": "online_after_flush",
                "true_feed_bar": 67.8,
                "night_shortfall_m3": 187,
                "telescoping": False,
            },
            "commercial_result": {
                "shortfall_penalty_usd": 785,
                "lead_element_replacement_avoided_usd": 186000,
                "d2_outage_hours": 0,
            },
        },
        "reward_components": reward(
            0.4,
            0.2,
            0.6,
            -0.3,
            0.4,
            "task_completion positive: D-6 recovered most of the permeate deficit while D-2 stayed inside the true-feed cap; efficiency negative because 187 m3 and the 25 min flush were genuinely paid; evidence_quality reflects applying the card in the written direction and refusing permeate conductivity as a mechanical-load certificate",
        ),
    },
    2: {
        "id": "ffpc-r11-002-chosen",
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": (
                "AT-G3-A at 0.92 ppm has already crossed the 0.80 ppm high-high and sits "
                "well above the 0.10 ppm occupational ceiling. Drawing G3-AN-02 states "
                "that probe SP-G3-1 and the heated line are common, so AT-G3-B at 0.11 "
                "ppm is the same duct seen through condensate pot POT-G3-B, last drained "
                "under WO-44119 and never given a flush cadence. Two analyzer tags on "
                "one probe are one measurement. Recirculation pump P-SC-G3 has cavitated "
                "since 13:51 at 18 percent of design, so packed scrubber SC-G3 is not a "
                "functioning last barrier. Floor monitor AT-G3-AREA at 0.04 ppm only "
                "reports that the leak has not yet reached a different duct; it cannot "
                "veto a generator-outlet high-high. Trip G-3, cut methanol, open "
                "XV-G3-DUMP, raise building ventilation, and pull both operators now. "
                "Drain POT-G3-B in parallel as a diagnostic, never as a permit for the "
                "trip."
            ),
            "evidence_basis": [
                "AT-G3-A 0.92 ppm versus high-high 0.80 ppm and occupational ceiling 0.10 ppm",
                "G3-AN-02 common probe SP-G3-1 and 18 m heated line; 2oo2 vote does not buy sample-path independence",
                "WO-44119 condensate-pot drain on the B takeoff with no flush schedule added",
                "P-SC-G3 cavitation since 13:51 at 18 percent recirculation flow",
                "AT-G3-AREA 0.04 ppm on an independent duct, downstream of occupancy",
            ],
            "checks": [
                "read independence from the sample path, not from the count of analyzer tags",
                "refused a numerical average of A and B as a substitute vote",
                "treated P-SC-G3 cavitation as loss of the last process barrier, not as a reason to wait",
                "refused the building area monitor as a trip substitute because it sits downstream of people",
                "authorized POT-G3-B drain as a parallel diagnostic with no hold on the dump",
            ],
            "residual_risk": (
                "the 1800 L dump, generator rebuild, and T-2 night-sequence slip are paid "
                "either way; accepted against a building ClO2 exposure and a reportable excursion"
            ),
        },
        "executed_action": {
            "action": "trip_dump_evacuate_g3",
            "action_type": "protective_trip_authorization",
            "status": "trip_dump_complete_operators_clear",
            "result": "methanol_stopped_dump_open",
            "outcome": "building_unoccupied_before_excursion",
            "authorization": "ACCEPT of proposed G-3 trip; G3-AN-02 and AT-G3-A snapshot attached to the dump log",
            "steps": [
                {
                    "t_local": "14:07:09",
                    "step": "G-3 trip issued; methanol feed stopped; XV-G3-DUMP commanded open",
                },
                {
                    "t_local": "14:07:21",
                    "step": "dump valve end-switch confirmed open; 1800 L chlorate liquor routing to the dump tank",
                },
                {
                    "t_local": "14:07:28",
                    "step": "building ventilation raised to high rate; both field operators paged out of the generator building",
                },
                {
                    "t_local": "14:07:46",
                    "step": "operators reported clear of the generator building; SCBA staged at the door, unused",
                },
                {
                    "t_local": "14:08:10",
                    "step": "instrument tech tasked to drain POT-G3-B as a parallel diagnostic; trip not gated on that drain",
                },
            ],
            "dump_volume_L": 1800,
            "operators_evacuated": 2,
            "pot_g3_b_drain": "parallel_not_precondition",
            "deviations": "none; tonight's maintenance window absorbs the planned-equivalent dump the T-2 sequence could not",
        },
        "future_outcome": {
            "status": "generator_tripped_building_clear",
            "outcome": "dump_taken_no_reportable_release",
            "result": "occupational_exposure_avoided",
            "success": True,
            "hazard_avoided": "clo2_building_exposure_reportable_release",
            "near_miss": False,
            "estop": False,
            "timeline": [
                {
                    "t_local": "14:09",
                    "event": "AT-G3-A fell through high-high after methanol stop; AT-G3-B stayed liquid-locked near 0.11 ppm until POT-G3-B was drained at 14:51",
                },
                {
                    "t_local": "14:12",
                    "event": "AT-G3-AREA peaked at 0.07 ppm and receded; never approached the 0.30 ppm / 15 min reportable line",
                },
                {
                    "t_local": "14:18",
                    "event": "dump tank received the 1800 L; generator inventory marked for a 6 h rebuild into the night window",
                },
                {
                    "t_local": "20:20",
                    "event": "G-3 inventory restored; T-2 bleach sequence restarted in the window that could absorb a planned dump",
                },
                {
                    "t_local": "22:40",
                    "event": "POT-G3-B found condensate-locked; B cell agreed with A once flushed; flush schedule added under WO-44131",
                },
            ],
            "observed_effects": [
                "dump of 1800 L taken on time; methanol stopped; no late dump after a building leak",
                "two operators left the generator building before any occupational ceiling breach; no SCBA use, no eye irritation",
                "area monitor peak 0.07 ppm, well under the 0.30 ppm / 15 min reportable threshold",
                "unplanned-dump cost 74000 USD and missed-bleach 31000 USD paid; T-2 slipped into the night window rather than a 9 h overrun",
                "B-side condensate lock confirmed after the fact; it was never treated as a dissenting independent vote",
            ],
            "state_delta": {
                "g3_status": "tripped_dump_taken",
                "building_occupancy": "cleared",
                "area_monitor_peak_ppm": 0.07,
                "reportable_release": False,
                "rebuild_h": 6,
            },
            "commercial_result": {
                "dump_and_rebuild_usd": 74000,
                "missed_bleach_sequence_usd": 31000,
                "reportable_release_usd": 0,
            },
        },
        "reward_components": reward(
            0.5,
            0.8,
            0.3,
            -0.6,
            0.5,
            "task_completion positive: the protective trip and dump completed and the night window absorbed the rebuild; efficiency negative because 74000 plus 31000 were paid in full; personnel_safety and evidence_quality carry sample-path independence, the refused average, and operators out before occupancy was the detector",
        ),
    },
    3: {
        "id": "ffpc-r11-003-chosen",
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": (
                "SOP FP-06 is already satisfied on both start tests: a far-end RTD is "
                "under 20 C, and ambient is under 0 C with stagnation valves shut longer "
                "than 30 min. TE-LF6-L44-FAR is 16.0 C and falling 0.35 C each minute, "
                "roughly 11 minutes from the 12.0 C crystalline freeze. Header TE-LF6-OUT "
                "at 41 C is mixed-loop metal and does not speak for far-absorber "
                "inventory. OPS-NIGHT-2 is a commercial-desk pumping memo, not a "
                "freeze-protection override, and the 20-minute duty-manager callback "
                "outlasts the freeze clock. Four instrumented loops out of 48 is a reason "
                "to move sooner: forty-four loops carry no far RTD whatsoever. Start "
                "FP-LF6-A/B now, open the stagnation valves onto the recirculation path, "
                "and book the 1400 USD demand charge as a logged commercial exception."
            ),
            "evidence_basis": [
                "FP-06 dual predicate already true at 02:11",
                "TE-LF6-L44-FAR 16.0 C falling 0.35 C/min, about 11 min to 12.0 C freeze",
                "outlet header 41 C is a mixing volume, not far-collector metal",
                "OPS-NIGHT-2 issued by commercial operations, last revised 2026-06-11, not a safety authority",
                "duty-manager response 20 min versus 11 min freeze clock; 4 of 48 loops have far RTDs",
            ],
            "checks": [
                "evaluated FP-06 on the predicates written, both already true",
                "refused the warm outlet header as a far-collector freeze clearance",
                "compared duty-manager latency to the 11 min time-to-freeze and declined the waiver wait",
                "treated sparse far-end coverage as a reason to trust a cold reading sooner, not later",
                "logged OPS-NIGHT-2 as a commercial exception rather than a trip inhibit",
            ],
            "residual_risk": (
                "about 2.1 MWh parasitic and a 1400 USD night demand charge are paid; "
                "accepted against glass-envelope rupture, HTF weep, and a nine-day loop outage"
            ),
        },
        "executed_action": {
            "action": "start_lf6_freeze_recirc",
            "action_type": "protective_action_authorization",
            "status": "recirc_running_before_freeze",
            "result": "far_rtds_held_above_12c",
            "outcome": "glass_and_htf_intact",
            "authorization": "ACCEPT of FP-06 recirculation; OPS-NIGHT-2 conflict logged as commercial exception EX-LF6-0211",
            "steps": [
                {
                    "t_local": "02:11:12",
                    "step": "freeze-protection pair FP-LF6-A/B started from the control room; no duty-manager precondition",
                },
                {
                    "t_local": "02:11:27",
                    "step": "stagnation valves opened onto the recirculation path; header flow confirmed",
                },
                {
                    "t_local": "02:11:44",
                    "step": "OPS-NIGHT-2 conflict logged as commercial exception; demand-charge acceptance 1400 USD posted",
                },
                {
                    "t_local": "02:18:00",
                    "step": "coldest far RTD TE-LF6-L44-FAR bottomed at 14.3 C and turned up; remaining far RTDs still above 15 C",
                },
                {
                    "t_local": "06:42:00",
                    "step": "sunrise handover; all four far-end RTDs above 40 C; pumps left running until ambient crossed 0 C",
                },
            ],
            "pumps": "FP-LF6-A/B",
            "demand_charge_usd": 1400,
            "l44_minimum_C": 14.3,
            "deviations": "none; duty manager returned the page at 02:29, after recirc was already moving HTF",
        },
        "future_outcome": {
            "status": "freeze_arrested_loops_intact",
            "outcome": "no_glass_rupture_no_htf_weep",
            "result": "far_collectors_above_freeze",
            "success": True,
            "hazard_avoided": "htf_freeze_glass_rupture_lf6",
            "near_miss": False,
            "estop": False,
            "timeline": [
                {
                    "t_local": "02:18",
                    "event": "TE-LF6-L44-FAR minimum 14.3 C; other far RTDs 15.2 to 16.8 C and rising",
                },
                {
                    "t_local": "02:30",
                    "event": "outlet header still 38 C; far-end recovery lagged the header, as expected for previously stagnant loops",
                },
                {
                    "t_local": "03:10",
                    "event": "all four far-end RTDs above 20 C; no glass-break alarms, no berm HTF",
                },
                {
                    "t_local": "06:42",
                    "event": "sunrise handover with far RTDs 41 to 44 C; parasitic energy 2.18 MWh",
                },
                {
                    "t_local": "09:15",
                    "event": "day crew walked L07/L19/L31/L44: envelopes intact, ball joints dry, no nine-day outage",
                },
            ],
            "observed_effects": [
                "coldest far SCA stayed 2.3 C above the 12.0 C freeze; no crystallization, no plugged loops",
                "parasitic 2.18 MWh and 1400 USD demand charge paid as the SOP cost of the night",
                "zero glass-envelope ruptures; zero HTF weep into trough berms",
                "header RTD remained a poor far-collector proxy throughout recovery",
                "OPS-NIGHT-2 exception EX-LF6-0211 queued for commercial review; freeze SOP left in force",
            ],
            "state_delta": {
                "lf6_status": "recirc_running",
                "coldest_far_rtd_min_C": 14.3,
                "loops_frozen": 0,
                "glass_ruptures": 0,
                "htf_wept_m3": 0.0,
            },
            "commercial_result": {
                "demand_charge_usd": 1400,
                "parasitic_mwh": 2.18,
                "glass_and_htf_loss_avoided_usd_note": "210000 per loop plus 18000 per m3 HTF not spent",
            },
        },
        "reward_components": reward(
            0.5,
            0.1,
            0.6,
            -0.4,
            0.3,
            "task_completion positive: freeze-protection recirc met FP-06 before the coldest far RTD reached 12 C; efficiency negative because 2.18 MWh and the 1400 USD demand charge were paid; evidence_quality reflects ranking FP-06 over OPS-NIGHT-2 and refusing the header RTD as far-collector inventory",
        ),
    },
}


def hidden_thought_paths(obj, path=""):
    found = []
    if isinstance(obj, dict):
        for key, val in obj.items():
            child = f"{path}.{key}" if path else key
            norm = re.sub(r"[^a-z0-9]+", "_", str(key)).strip("_").casefold()
            if norm in HIDDEN_THOUGHT_KEYS:
                found.append(child)
            found.extend(hidden_thought_paths(val, child))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            found.extend(hidden_thought_paths(item, f"{path}[{i}]"))
    return found


def main() -> None:
    for index in (1, 2, 3):
        diag_name = f"diagnosis-{index:02d}-r11.md"
        diag_path = STAGE / diag_name
        shared = extract_shared(diag_path)
        body = CHOSEN_BODIES[index]
        chosen = {
            "id": body["id"],
            "state": shared["state"],
            "proposed_action": shared["proposed_action"],
            "safety_decision": body["safety_decision"],
            "executed_action": body["executed_action"],
            "future_outcome": body["future_outcome"],
            "reward_components": body["reward_components"],
            "meta": meta(index, diag_name),
        }
        if set(chosen) - {
            "id",
            "state",
            "proposed_action",
            "safety_decision",
            "executed_action",
            "future_outcome",
            "reward_components",
            "meta",
        }:
            raise SystemExit(f"unexpected chosen keys: {sorted(chosen)}")
        if hidden_thought_paths(chosen):
            raise SystemExit(f"hidden thought keys: {hidden_thought_paths(chosen)}")
        if "training_ready" in json.dumps(chosen):
            raise SystemExit("training_ready leaked")
        rc = chosen["reward_components"]
        siblings = [
            rc[k]
            for k in (
                "task_completion",
                "personnel_safety",
                "asset_integrity",
                "efficiency",
                "evidence_quality",
            )
        ]
        if abs(sum(siblings) - rc["total"]) > 1e-6:
            raise SystemExit(f"reward mismatch {index}: {sum(siblings)} vs {rc['total']}")
        if chosen["state"].get("sim_or_real") == "real":
            raise SystemExit("sim_or_real=real")
        narrative = diagnosis_narrative_text(diag_path.read_bytes(), label=diag_name)
        if shares_copied_phrasing(chosen["safety_decision"]["rationale"], narrative):
            raise SystemExit(f"12-word overlap with diagnosis {diag_name}")
        if chosen["safety_decision"]["rationale"].strip() in diag_path.read_text():
            raise SystemExit(f"verbatim rationale in diagnosis {diag_name}")
        errs = check_thalamic(chosen, f"chosen-{index:02d}")
        if errs:
            raise SystemExit(f"check_thalamic failed {index}: {errs}")
        out = STAGE / f"chosen-{index:02d}-r11.json"
        out.write_text(json.dumps(chosen, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
        print(f"wrote {out} bytes={out.stat().st_size} total={rc['total']} decision={chosen['safety_decision']['decision']}")


if __name__ == "__main__":
    main()
