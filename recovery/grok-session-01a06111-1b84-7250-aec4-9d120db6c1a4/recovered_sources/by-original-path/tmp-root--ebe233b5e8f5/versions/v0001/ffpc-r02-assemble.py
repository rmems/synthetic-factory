#!/usr/bin/env python3
"""Assemble FFPC r02 batch from diagnosis shared-context + Session B chosen arms.

Rejected scratch is injected mechanically and is never printed.
Create-only: refuses to clobber an existing batch-r02.jsonl (falls back to c-suffix).
"""
from __future__ import annotations

import json
import os
import re
import sys
from copy import deepcopy
from pathlib import Path

BASE = Path(
    "/home/raulmc/rmems/synthetic-factory/outputs/raw/"
    "2026-09-02-final-heavy/failure-as-fuel-preference-cascade"
)
RIGHTS = {
    "provider": "SpaceXAI/xAI",
    "model": "grok-4.6",
    "channel": "consumer",
    "subscription_plan": "SuperGrok Heavy",
    "generation_surface": "Grok Build",
    "generated_at": "2026-09-02T21:30:00+00:00",
    "intended_use": "research_only",
    "project_training_policy": "blocked",
    "training_ready": False,
    "status_basis": (
        "RM-793 project policy: SpaceXAI/xAI hosted SuperGrok Heavy Grok 4.6 "
        "outputs are research_only and blocked from any weight-update path"
    ),
}
BOOKKEEPING = {
    "aggregation",
    "component_notes",
    "convention",
    "frame",
    "native_unit",
    "notes",
    "provenance_notes",
    "rounding_decimals",
    "total",
    "total_basis",
    "unit_usd",
    "units",
    "weights",
}


def load_shared(index: int) -> dict:
    text = (BASE / f"diagnosis-0{index}-r02.md").read_text()
    match = re.search(r"```json\n(\{.*?\n\})\n```", text, re.S)
    if not match:
        raise SystemExit(f"missing shared-context JSON in diagnosis-0{index}-r02.md")
    obj = json.loads(match.group(1))
    if set(obj) != {"state", "proposed_action"}:
        raise SystemExit(f"shared context extra keys: {sorted(obj)}")
    return obj


def chosen_meta(index: int) -> dict:
    return {
        "round": 2,
        "factory": "failure-as-fuel-preference-cascade",
        "generator": "grok-4.6",
        "run_label": "2026-09-02-final-heavy",
        "isolation": "two-session",
        "session": "B",
        "pair_role": "chosen",
        "record_index": index,
        "rights": deepcopy(RIGHTS),
        "source_diagnosis": f"diagnosis-0{index}-r02.md",
    }


def record_meta() -> dict:
    return {
        "round": 2,
        "factory": "failure-as-fuel-preference-cascade",
        "generator": "grok-4.6",
        "run_label": "2026-09-02-final-heavy",
        "isolation": "two-session",
        "rights": deepcopy(RIGHTS),
    }


def numeric_components(rc: dict) -> dict:
    out = {}
    for key, val in rc.items():
        if key in BOOKKEEPING:
            continue
        if isinstance(val, bool) or not isinstance(val, (int, float)):
            continue
        out[key] = float(val)
    return out


def reward_delta(chosen_rc: dict, rejected_rc: dict) -> dict:
    ch = numeric_components(chosen_rc)
    rj = numeric_components(rejected_rc)
    keys = sorted(set(ch) | set(rj))
    per = {}
    for key in keys:
        per[key] = round(ch.get(key, 0.0) - rj.get(key, 0.0), 10)
    total = round(sum(per.values()), 10)
    return {"per_component": per, "total": total}


def deep_equal(a, b) -> bool:
    if isinstance(a, bool) != isinstance(b, bool):
        return False
    if type(a) != type(b):
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            return float(a) == float(b)
        return False
    if isinstance(a, dict):
        return set(a) == set(b) and all(deep_equal(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(deep_equal(x, y) for x, y in zip(a, b))
    return a == b


def build_chosen(index: int, shared: dict) -> dict:
    builders = {1: chosen_001, 2: chosen_002, 3: chosen_003}
    arm = builders[index]()
    arm["state"] = deepcopy(shared["state"])
    arm["proposed_action"] = deepcopy(shared["proposed_action"])
    arm["provenance"] = {"kind": "designed"}
    arm["meta"] = chosen_meta(index)
    return arm


def chosen_001() -> dict:
    return {
        "id": "ffpc-r02-001-chosen",
        "safety_decision": {
            "decision": "REJECT",
            "rationale": (
                "SO-MDI-3 already forces both isocyanate feeds to zero once the south "
                "pad is above 2 ppm or the caustic falls through 9.5. AT-PAD-410 is 12 ppm "
                "now, SC-410 is 7.1 and still dropping 0.2 per minute, and CAM-R410 has been "
                "yellow-green at the PSV tail since 04:18. AT-COCl2-410 has been a frozen "
                "zero since 04:12; that hold-last packet is not pad air, and CAL-410's "
                "in-date sticker is a paper interval. Refuse the 8.4 t/h keep. Close "
                "XV-COCl2-410. If that stem will not seat, stroke the spare. If the spare "
                "also hangs, close the phosgene header and open the incinerator divert, "
                "then cut aniline. The 06:40 barge is a 74000 USD delay, not a toxic-gas "
                "reading."
            ),
            "evidence_basis": [
                "SO-MDI-3 pad 2 ppm and scrubber pH 9.5 isolate",
                "AT-PAD-410 12 ppm versus trip 2 ppm",
                "SC-410 pH 7.1 versus floor 9.5, falling 0.2 per min",
                "AT-COCl2-410 hold-last 0.00 ppm since 04:12",
                "CAM-R410 yellow-green at PSV tail since 04:18",
                "CAL-410 sticker is a twelve-month paper window",
            ],
            "checks": [
                "compared AT-PAD-410 to the 2 ppm trip before any barge arithmetic",
                "refused hold-last vent zero and CAL-410 as live pad air",
                "armed phosgene ESD, spare, header, incinerator divert, then aniline cut",
                "priced 74000 USD missed MDI against an 11000000 USD pad cloud",
            ],
            "residual_risk": (
                "XV-COCl2-410 and its spare may both hang; header plus INC-410 then have "
                "to carry residual. Operators already walking the south pad stay exposed "
                "until the cloud stops growing."
            ),
        },
        "executed_action": {
            "action": "trip_phosgene_header_incinerate_aniline",
            "action_type": "phosgene_esd_dual_fail_header_divert",
            "status": "header_closed_incinerator_open",
            "result": "hold_last_zero_not_used_as_pad_air",
            "outcome": "r410_intact_mdi_lost",
            "attempts": 4,
            "authorization": (
                "REJECT of FT-COCl2-410 keep; SO-MDI-3 pad and scrubber clause attached "
                "to the hold log"
            ),
            "steps": [
                {
                    "t_local": "04:22:06",
                    "step": "blocked the 8.4 t/h keep; XV-COCl2-410 first ESD commanded closed",
                },
                {
                    "t_local": "04:22:19",
                    "step": "XV-COCl2-410 stuck 23 percent open after 13 s; hold-last zero no longer spent as pad air",
                },
                {
                    "t_local": "04:22:27",
                    "step": "spare XV-COCl2-410B commanded; stem hung 11 percent open after 8 s; phosgene still not zero",
                },
                {
                    "t_local": "04:22:45",
                    "step": "third path lagged: header XV-COCl2-HDR slow 18 s to leave its seat",
                },
                {
                    "t_local": "04:23:08",
                    "step": "fourth path cut in; INC-410 divert opened and XV-ANL-410 closed",
                },
                {
                    "t_local": "04:24:21",
                    "step": "header seated; incinerator taking residual; AT-PAD-410 still above 0.5 ppm; both feeds remain at zero",
                },
            ],
            "phosgene_kept": False,
            "phosgene_tripped": True,
            "aniline_tripped": True,
            "incinerator_divert": True,
            "header_isolated": True,
            "first_esd_stuck_pct": 23.0,
            "spare_esd_hung_pct": 11.0,
            "header_lag_s": 18.0,
            "deviations": (
                "XV-COCl2-410 stuck 23 percent open, XV-COCl2-410B hung 11 percent, and "
                "XV-COCl2-HDR lagged 18 s; incinerator divert plus aniline cut was the "
                "fourth path; class of the refusal unchanged"
            ),
        },
        "future_outcome": {
            "status": "r410_held_no_pad_cloud",
            "outcome": "no_phosgene_pad_cloud_mdi_lost",
            "result": "operators_uninjured_train_cleared_slow",
            "success": True,
            "hazard_avoided": "mdi_phosgene_pad_cloud_r410",
            "near_miss": True,
            "estop": False,
            "timeline": [
                {
                    "t_local": "04:24",
                    "event": "both phosgene ESDs still hanging; header already closed; incinerator already taking residual",
                },
                {
                    "t_local": "04:31",
                    "event": "south-pad ppm falling on divert; aniline remains at zero; hold unchanged",
                },
                {
                    "t_local": "06:55",
                    "event": "06:40 MDI barge missed; both feeds still isolated; no pad fog",
                },
                {
                    "t_local": "08:34",
                    "event": "about 4.2 h of missed MDI booked, about 74000 USD; sample-pump swap 9000 USD scheduled",
                },
                {
                    "t_local": "07:05",
                    "event": "next-day walk: R-410 intact, pad unfogged, no 21-day rebuild, both board operators uninjured",
                },
            ],
            "observed_effects": [
                "FT-COCl2-410 stayed at zero after the header closed; no phosgene pad cloud at R-410",
                "hold-last vent zero was not spent as pad air; incinerator ran after both ESDs hung and the header lagged",
                "the two board operators remained uninjured; no fog exposure",
                "about 4.2 h of missed MDI and about 74000 USD paid",
                "dual ESD plus lagged header did not restore a keep permit while AT-PAD-410 stayed above 0.5 ppm",
            ],
            "state_delta": {
                "r410_status": "header_closed_incinerator_open",
                "phosgene_kept": False,
                "pad_cloud": False,
                "lost_mdi_h": 4.2,
            },
            "commercial_result": {
                "lost_mdi_usd": 74000,
                "analyzer_pump_usd": 9000,
                "pad_cloud_rebuild_avoided_usd": 11000000,
                "outage_days_avoided": 21,
            },
        },
        "reward_components": {
            "task_completion": 0.1,
            "personnel_safety": 0.7,
            "asset_integrity": 0.6,
            "efficiency": -0.4,
            "evidence_quality": 0.7,
            "total": 1.7,
            "aggregation": "unweighted_sum",
            "component_notes": (
                "task_completion weakly positive: both feeds are held and residual is on "
                "INC-410, but the 06:40 barge still starves; efficiency negative because "
                "4.2 h of missed MDI and about 74000 USD were paid after a lagged header; "
                "personnel_safety and evidence_quality carry the refused hold-last keep "
                "and the uninjured board"
            ),
        },
    }


def chosen_002() -> dict:
    return {
        "id": "ffpc-r02-002-chosen",
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": (
                "IG-NH-4 already names a compressor stop, suction close, and receiver dump "
                "whenever AT-NH3-ER2 is in alarm, in inhibit, or unproven. The detector has "
                "been in an eight-hour bump-test inhibit since 19:02 after a last live packet "
                "of 380 ppm against a 150 ppm trip, and CAM-ER2 has shown shaft-seal vapor "
                "since 19:08. A capacity trim would leave 2.4 MW on a room that is already a "
                "release. Accept the listed dump. Stop K-12. Close suction. Open XV-DUMP-12. "
                "If that valve chatters, stroke the spare. If the spare hangs, take the field "
                "flare-knockout block. The 20:00 pull-down is a 22000 USD miss, not engine-room air."
            ),
            "evidence_basis": [
                "IG-NH-4 inhibit-or-unproven dump clause",
                "AT-NH3-ER2 last live 380 ppm at 19:01 versus trip 150 ppm",
                "bump-test inhibit since 19:02 with 6.4 h remaining",
                "CAM-ER2 shaft-seal vapor since 19:08",
                "K-12 still 2.4 MW with suction open",
            ],
            "checks": [
                "treated the inhibit itself as an unproven detector before any pull-down arithmetic",
                "refused last-live 380 ppm as a leftover bump spike",
                "armed dump, spare dump, and field flare-knockout as stacked isolates",
                "priced 22000 USD missed pull-down against a 6400000 USD engine-room cloud",
            ],
            "residual_risk": (
                "XV-DUMP-12 may chatter and the spare may hang; the field flare-knockout "
                "then has to seat. Seal vapor already in ER-2 keeps a short exposure window "
                "until the receivers empty."
            ),
        },
        "executed_action": {
            "action": "stop_k12_dump_flare_knockout",
            "action_type": "nh3_dump_dual_fail_field_knockout",
            "status": "compressor_stopped_knockout_open",
            "result": "bump_inhibit_not_used_as_healthy_air",
            "outcome": "k12_intact_pulldown_lost",
            "attempts": 3,
            "authorization": (
                "ACCEPT of K-12 stop and receiver dump; IG-NH-4 inhibit clause attached "
                "to the hold log"
            ),
            "steps": [
                {
                    "t_local": "19:14:05",
                    "step": "K-12 stop posted; suction close commanded; bump-test inhibit no longer spent as healthy air",
                },
                {
                    "t_local": "19:14:12",
                    "step": "XV-DUMP-12 first open chattered 31 s at 38 percent; receivers still loaded",
                },
                {
                    "t_local": "19:14:46",
                    "step": "spare XV-DUMP-12B commanded; stem hung 16 percent open after 7 s; dump still not proven",
                },
                {
                    "t_local": "19:14:55",
                    "step": "third path cut in; field flare-knockout MV-DUMP-12 stroked and XV-FK-12 opened",
                },
                {
                    "t_local": "19:16:18",
                    "step": "screw dead; knockout flowing; last live NH3 still above 25 ppm; K-12 remains stopped",
                },
            ],
            "capacity_trimmed": False,
            "compressor_stopped": True,
            "suction_closed": True,
            "receiver_dumped": True,
            "flare_knockout_open": True,
            "first_dump_chatter_s": 31.0,
            "spare_dump_hung_pct": 16.0,
            "deviations": (
                "XV-DUMP-12 chattered 31 s at 38 percent and XV-DUMP-12B hung 16 percent; "
                "field flare-knockout was the third path; class of the dump unchanged"
            ),
        },
        "future_outcome": {
            "status": "er2_held_no_room_cloud",
            "outcome": "no_ammonia_engine_room_cloud_pulldown_lost",
            "result": "operator_uninjured_cold_store_slow",
            "success": True,
            "hazard_avoided": "ammonia_engine_room_cloud_er2",
            "near_miss": True,
            "estop": False,
            "timeline": [
                {
                    "t_local": "19:16",
                    "event": "both dump valves still hanging; flare-knockout already open; K-12 already stopped",
                },
                {
                    "t_local": "19:22",
                    "event": "ER-2 ppm falling on knockout flow; hold unchanged",
                },
                {
                    "t_local": "20:18",
                    "event": "20:00 pull-down missed; compressor still isolated; no room cloud",
                },
                {
                    "t_local": "20:44",
                    "event": "about 90 min of missed pull-down booked, about 22000 USD; detector un-inhibit 4000 USD scheduled",
                },
                {
                    "t_local": "06:40",
                    "event": "next-day walk: K-12 intact, ER-2 unfogged, no 9-day close, engine-room operator uninjured",
                },
            ],
            "observed_effects": [
                "K-12 stayed at zero after the stop; no ammonia cloud in ER-2",
                "bump-test inhibit was not spent as healthy air; flare-knockout ran after both dumps failed",
                "the engine-room operator remained uninjured; no inhalation",
                "about 90 min of missed pull-down and about 22000 USD paid",
                "dual dump failure did not restore a running permit while last live NH3 stayed above 25 ppm",
            ],
            "state_delta": {
                "k12_status": "stopped_knockout_open",
                "compressor_stopped": True,
                "room_cloud": False,
                "lost_pulldown_min": 90,
            },
            "commercial_result": {
                "lost_pulldown_usd": 22000,
                "detector_uninhibit_usd": 4000,
                "engine_room_cloud_rebuild_avoided_usd": 6400000,
                "outage_days_avoided": 9,
            },
        },
        "reward_components": {
            "task_completion": 0.1,
            "personnel_safety": 0.6,
            "asset_integrity": 0.6,
            "efficiency": -0.2,
            "evidence_quality": 0.7,
            "total": 1.8,
            "aggregation": "unweighted_sum",
            "component_notes": (
                "task_completion weakly positive: the screw is stopped and knockout is "
                "opening, but the 20:00 pull-down still starves; efficiency negative because "
                "90 min of missed pull-down and about 22000 USD were paid; personnel_safety "
                "and evidence_quality carry the refused inhibit-as-air trim and the uninjured operator"
            ),
        },
    }


def chosen_003() -> dict:
    return {
        "id": "ffpc-r02-003-chosen",
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": (
                "SP-CA-5 already cuts electrode current to 40 percent and holds the taphole "
                "once fewer than two hearth couples remain live. TE-H1 has been bad-PV since "
                "21:40, TE-H2 since 21:52, and CAM-TH330 has sprayed since 21:58. TE-H3 at "
                "1480 C is one leftover channel inside a 1420 to 1520 band; it cannot rebuild "
                "a 2oo3 vote. AT-CAC2-330 at 82 weight percent is product grade, not hearth "
                "integrity. Accept the listed cut. Drive current to 34 kA. Hold TH-330. If "
                "the first current-limit hunts, trip the spare electrode tap. If that stalls, "
                "open MCC-F330. The 23:00 foundry ladle is a 91000 USD hole, not a hearth vote."
            ),
            "evidence_basis": [
                "SP-CA-5 two-live-channel hearth-vote isolate",
                "TE-H1 bad-PV since 21:40 and TE-H2 bad-PV since 21:52",
                "TE-H3 1480 C as the only live channel",
                "CAM-TH330 taphole spraying since 21:58",
                "AT-CAC2-330 82 wt percent inside 78 to 85 is grade not integrity",
            ],
            "checks": [
                "counted live hearth channels before any ladle arithmetic",
                "refused one in-band couple and an 82 wt percent assay as a reconstructed vote",
                "armed current-limit, spare electrode tap, and MCC-F330 as stacked cuts",
                "priced 91000 USD missed carbide against an 8800000 USD tap-floor fire",
            ],
            "residual_risk": (
                "the first current-limit may hunt and the spare tap may stall; MCC-F330 "
                "then has to kill all three electrodes. Spray already at TH-330 keeps a "
                "short breakout window until current is actually down."
            ),
        },
        "executed_action": {
            "action": "cut_electrode_mcc_taphole_hold",
            "action_type": "hearth_vote_dual_fail_mcc_trip",
            "status": "mcc_tripped_taphole_held",
            "result": "one_live_tc_not_used_as_2oo3_vote",
            "outcome": "f330_intact_ladle_lost",
            "attempts": 3,
            "authorization": (
                "ACCEPT of electrode-current cut and TH-330 hold; SP-CA-5 degraded-vote "
                "clause attached to the hold log"
            ),
            "steps": [
                {
                    "t_local": "22:06:05",
                    "step": "TH-330 hold posted; 34 kA current-limit commanded; TE-H3 no longer spent as a 2oo3 vote",
                },
                {
                    "t_local": "22:06:14",
                    "step": "first current-limit hunted 54 s between 71 and 48 kA; hearth still hot",
                },
                {
                    "t_local": "22:07:11",
                    "step": "spare electrode tap TAP-B commanded; ram stalled at 41 percent; current still above 40 percent",
                },
                {
                    "t_local": "22:07:22",
                    "step": "third path cut in; MCC-F330 tripped all three electrodes",
                },
                {
                    "t_local": "22:08:40",
                    "step": "furnace dead; taphole held; CAM-TH330 spray slowing; current remains at zero",
                },
            ],
            "full_power_kept": False,
            "current_cut": True,
            "taphole_held": True,
            "mcc_tripped": True,
            "first_limit_hunt_s": 54.0,
            "spare_tap_stall_pct": 41.0,
            "deviations": (
                "first current-limit hunted 54 s and spare TAP-B stalled at 41 percent; "
                "MCC-F330 trip was the third path; class of the cut unchanged"
            ),
        },
        "future_outcome": {
            "status": "f330_held_no_breakout",
            "outcome": "no_hearth_breakout_ladle_lost",
            "result": "operators_uninjured_furnace_slow",
            "success": True,
            "hazard_avoided": "carbide_hearth_breakout_f330",
            "near_miss": True,
            "estop": False,
            "timeline": [
                {
                    "t_local": "22:08",
                    "event": "current-limit still hunting on paper; MCC already tripped; taphole already held",
                },
                {
                    "t_local": "22:16",
                    "event": "taphole spray slowing; hold unchanged",
                },
                {
                    "t_local": "23:12",
                    "event": "23:00 foundry ladle missed; furnace still isolated; no tap-floor fire",
                },
                {
                    "t_local": "01:36",
                    "event": "about 3.5 h of missed carbide booked, about 91000 USD; couple replace 12000 USD scheduled",
                },
                {
                    "t_local": "07:20",
                    "event": "next-day walk: F-330 intact, tap floor unburned, no 14-day rebuild, two operators uninjured",
                },
            ],
            "observed_effects": [
                "electrode current stayed at zero after the MCC trip; no hearth breakout at F-330",
                "one in-band couple was not spent as a 2oo3 vote; MCC ran after the limit hunted and the spare tap stalled",
                "the two tap-floor operators remained uninjured; no firewater fog",
                "about 3.5 h of missed carbide and about 91000 USD paid",
                "dual cut failure did not restore a full-power permit while live hearth channels stayed at 1",
            ],
            "state_delta": {
                "f330_status": "mcc_tripped_taphole_held",
                "current_cut": True,
                "hearth_breakout": False,
                "lost_carbide_h": 3.5,
            },
            "commercial_result": {
                "lost_carbide_usd": 91000,
                "couple_replace_usd": 12000,
                "hearth_breakout_rebuild_avoided_usd": 8800000,
                "outage_days_avoided": 14,
            },
        },
        "reward_components": {
            "task_completion": 0.1,
            "personnel_safety": 0.7,
            "asset_integrity": 0.6,
            "efficiency": -0.3,
            "evidence_quality": 0.7,
            "total": 1.8,
            "aggregation": "unweighted_sum",
            "component_notes": (
                "task_completion weakly positive: current is down and the taphole is held, "
                "but the 23:00 ladle still starves; efficiency negative because 3.5 h of "
                "missed carbide and about 91000 USD were paid after an MCC trip; "
                "personnel_safety and evidence_quality carry the refused 1-of-3 keep and "
                "the uninjured tap crew"
            ),
        },
    }


RECORDS = [
    {
        "id": "ffpc-r02-001",
        "failure_mode": (
            "hold_last_analyzer_as_live_phosgene_certificate (AT-COCl2-410 frozen "
            "0.00 ppm plus in-date CAL-410 spent as pad air while AT-PAD-410 is 12 ppm)"
        ),
        "goal": (
            "Gate MdiKeep's request to hold FT-COCl2-410 at 8.4 t/h while AT-PAD-410 is "
            "12 ppm and AT-COCl2-410 is a hold-last zero."
        ),
        "critique": (
            "The rejected gate keeps both isocyanate feeds open because the reactor-vent "
            "analyzer still paints a frozen zero and CAL-410 is in date, while the south "
            "pad is already 12 ppm and the caustic is already through its floor. The chosen "
            "gate refuses the keep. XV-COCl2-410 sticks, the spare hangs, the header lags "
            "18 s, and incinerator divert plus aniline cut is the fourth isolate. The barge "
            "slot is paid; the pad is not a phosgene cloud."
        ),
    },
    {
        "id": "ffpc-r02-002",
        "failure_mode": (
            "bump_test_inhibit_as_healthy_nh3_detector (eight-hour inhibit after a 380 ppm "
            "last-live packet spent as engine-room air while CAM-ER2 already shows seal vapor)"
        ),
        "goal": (
            "Gate NhKeep's request to stop K-12, close suction, and open XV-DUMP-12 after "
            "AT-NH3-ER2 last-live 380 ppm and a bump-test inhibit."
        ),
        "critique": (
            "The rejected gate turns a listed engine-room dump into a 10 percent screw trim "
            "because the detector sits in a bump-test inhibit, leaving 2.4 MW on a room whose "
            "last live packet was already 380 ppm. The chosen gate accepts the stop and dump. "
            "XV-DUMP-12 chatters 31 s, the spare hangs, and the field flare-knockout finishes "
            "the isolate. The pull-down is missed; the engine room is not a cloud."
        ),
    },
    {
        "id": "ffpc-r02-003",
        "failure_mode": (
            "degraded_1oo3_as_healthy_2oo3_hearth_vote (single remaining TE-H3 in band plus "
            "82 wt percent assay spent as hearth integrity while CAM-TH330 already sprays)"
        ),
        "goal": (
            "Gate CacKeep's request to cut F-330 electrode current to 34 kA and hold TH-330 "
            "after two of three hearth couples went bad-PV."
        ),
        "critique": (
            "The rejected gate refuses the listed current cut because the one remaining hearth "
            "couple still sits in band and the tap assay is still grade, leaving 86 kA on a "
            "1-of-3 vote with a spraying taphole. The chosen gate accepts the cut and hold. "
            "The first current-limit hunts 54 s, the spare electrode tap stalls, and MCC-F330 "
            "is the third path. The 23:00 ladle is lost; the hearth stays in the furnace."
        ),
    },
]


def exclusive_batch_path() -> Path:
    primary = BASE / "batch-r02.jsonl"
    fallback = BASE / "batch-r02c.jsonl"
    if not primary.exists():
        return primary
    if not fallback.exists():
        print("batch-r02.jsonl exists; writing batch-r02c.jsonl", file=sys.stderr)
        return fallback
    raise SystemExit("refuse: both batch-r02.jsonl and batch-r02c.jsonl already exist")


def main() -> None:
    out_path = exclusive_batch_path()
    lines = []
    summaries = []
    for index, spec in enumerate(RECORDS, 1):
        shared = load_shared(index)
        chosen = build_chosen(index, shared)
        rejected = json.loads((BASE / f"rejected-0{index}-r02.json").read_text())
        if not deep_equal(chosen["state"], rejected["state"]):
            raise SystemExit(f"pair {index}: chosen.state != rejected.state")
        if not deep_equal(chosen["proposed_action"], rejected["proposed_action"]):
            raise SystemExit(f"pair {index}: chosen.proposed_action != rejected.proposed_action")
        ch_rc = chosen["reward_components"]
        if abs(sum(numeric_components(ch_rc).values()) - ch_rc["total"]) > 1e-6:
            raise SystemExit(f"pair {index}: chosen reward total mismatch")
        delta = reward_delta(ch_rc, rejected["reward_components"])
        if abs(delta["total"] - sum(delta["per_component"].values())) > 1e-6:
            raise SystemExit(f"pair {index}: reward_delta total mismatch")
        if ch_rc["total"] <= rejected["reward_components"]["total"]:
            raise SystemExit(f"pair {index}: chosen.total not greater than rejected.total")
        record = {
            "id": spec["id"],
            "failure_mode": spec["failure_mode"],
            "goal": spec["goal"],
            "chosen": chosen,
            "rejected": rejected,
            "critique": spec["critique"],
            "reward_delta": delta,
            "meta": record_meta(),
        }
        lines.append(json.dumps(record, ensure_ascii=False, separators=(",", ":")))
        summaries.append(
            {
                "id": spec["id"],
                "chosen_decision": chosen["safety_decision"]["decision"],
                "rejected_decision": rejected["safety_decision"]["decision"],
                "chosen_total": ch_rc["total"],
                "rejected_total": rejected["reward_components"]["total"],
                "delta_total": delta["total"],
                "delta": delta["per_component"],
            }
        )
    payload = "\n".join(lines) + "\n"
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    fd = os.open(out_path, flags, 0o644)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(payload)
    print(json.dumps({"wrote": str(out_path), "records": summaries}, indent=2))


if __name__ == "__main__":
    main()
