#!/usr/bin/env python3
"""Session B assembler for FFPC round 63.

Chosen arms are synthesized from diagnosis shared-context + repair sketches.
Rejected arms are injected mechanically from Session A scratch. reward_delta
is chosen minus rejected per component.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

BASE = Path(
    "/home/raulmc/rmems/synthetic-factory/outputs/raw/2026-09-02-final-heavy/"
    "failure-as-fuel-preference-cascade"
)
ROUND = 63
RR = f"{ROUND:02d}"
# batch-r63.jsonl is occupied by a concurrent delayed-coker drop.
# Session A LNG/ClO2/AN handoff remains diagnosis-0N-r63.md + rejected-0N-r63.json.
BATCH_NAME = f"batch-r{RR}c.jsonl"
PAIR_PREFIX = f"ffpc-r{RR}c"

RIGHTS = {
    "provider": "SpaceXAI/xAI",
    "model": "grok-4.6",
    "channel": "consumer",
    "subscription_plan": "SuperGrok Heavy",
    "generation_surface": "Grok Build",
    "generated_at": "2026-09-03T02:15:00Z",
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

COMPONENTS = (
    "task_completion",
    "personnel_safety",
    "asset_integrity",
    "efficiency",
    "evidence_quality",
)

TARGET = {
    1: {
        "task_completion": 0.5,
        "personnel_safety": 1.8,
        "asset_integrity": 1.6,
        "efficiency": 0.3,
        "evidence_quality": 1.1,
    },
    2: {
        "task_completion": 0.4,
        "personnel_safety": 1.7,
        "asset_integrity": 1.6,
        "efficiency": 0.5,
        "evidence_quality": 1.2,
    },
    3: {
        "task_completion": 0.6,
        "personnel_safety": 1.9,
        "asset_integrity": 1.5,
        "efficiency": 0.4,
        "evidence_quality": 1.3,
    },
}


def load_shared_context(index: int) -> dict:
    text = (BASE / f"diagnosis-{index:02d}-r{RR}.md").read_text()
    match = re.search(r"## Shared context\n\n```json\n(.*?)\n```", text, re.S)
    if not match:
        raise SystemExit(f"missing shared context in diagnosis-{index:02d}-r{RR}.md")
    ctx = json.loads(match.group(1))
    if set(ctx) != {"state", "proposed_action"}:
        raise SystemExit(f"unexpected shared-context keys: {sorted(ctx)}")
    return ctx


def chosen_meta(index: int) -> dict:
    return {
        "round": ROUND,
        "factory": "failure-as-fuel-preference-cascade",
        "generator": "grok-4.6",
        "run_label": "2026-09-02-final-heavy",
        "isolation": "two-session",
        "session": "B",
        "pair_role": "chosen",
        "source_diagnosis": f"diagnosis-{index:02d}-r{RR}.md",
        "record_index": index,
        "rights": dict(RIGHTS),
    }


def reward_from_rejected(rejected_rc: dict, index: int) -> dict:
    per = TARGET[index]
    out = {}
    for key in COMPONENTS:
        out[key] = round(float(rejected_rc[key]) + float(per[key]), 10)
    total = round(sum(out[k] for k in COMPONENTS), 10)
    notes = {
        1: (
            "task_completion weakly positive: K-6 is stopped and MCC is open, but the "
            "07:30 carrier still starves; efficiency is flat because 3.8 h of missed LNG "
            "and about 62000 USD were paid; personnel_safety and evidence_quality carry "
            "the refused leftover-F-as-metal keep-running call and the uninjured pad"
        ),
        2: (
            "task_completion weakly positive: methanol and chlorate are at zero and the "
            "flood is seated, but the 08:00 hardwood campaign still starves; efficiency "
            "is slightly positive versus a 19-day rebuild; personnel_safety and "
            "evidence_quality carry the refused expired-bypass trim and the uninjured pad"
        ),
        3: (
            "task_completion weakly positive: melt is isolated and wash is flowing, but "
            "the 06:00 farm-truck slot still starves; efficiency is flat because 4.1 h of "
            "missed AN and about 47000 USD were paid; personnel_safety and evidence_quality "
            "carry the refused snapshot-as-ammonia refusal and the uninjured pad"
        ),
    }
    out["total"] = total
    out["aggregation"] = "unweighted_sum"
    out["component_notes"] = notes[index]
    return out


def chosen_001(state, proposed_action, rejected_rc) -> dict:
    return {
        "id": "ffpc-r63c-001-chosen",
        "state": state,
        "proposed_action": proposed_action,
        "safety_decision": {
            "decision": "REJECT",
            "rationale": (
                "The outboard journal is already a wipe path. TE-BRG-6 sits at 118 C, "
                "twenty-eight degrees past the 90 C trip, and it has been climbing 1.6 C "
                "each minute with K-6 still loaded. The leftover F engineering unit on the "
                "faceplate is a WO-7066 labeling leftover, not a conversion of 118 into a "
                "cool 48 C bearing. BI-LNG-3 will not let K-6 stay loaded once TE-BRG-6 is "
                "over 90 C. LNG rundown at -161.2 C is product quality sitting minutes "
                "behind a hot journal; it is not metal temperature. CAM-K6 oil mist at the "
                "outboard seal since 03:19 is an independent wipe vote, so a keep-running "
                "call that treats leftover F paint as a cool-journal stamp would keep a "
                "118 C bearing on a mixed-refrigerant rotor. Stop K-6. Close suction "
                "XV-K6. If that stem does not prove shut after two strokes, open nitrogen "
                "purge NV-N2-K6. If the purge solenoid lags, trip MCC-K6 so the rotor is "
                "dead even with a leaking suction. A 07:30 carrier hole does not license a "
                "journal fire. 3.8 h of missed LNG and about 62000 USD is the priced night; "
                "a 9.8 million mixed-refrigerant fire and two pad burns are not."
            ),
            "evidence_basis": [
                "TE-BRG-6 118 C versus trip 90 C, climbing 1.6 C per min",
                "CAM-K6 oil mist at the outboard seal since 03:19 as independent wipe",
                "leftover F faceplate unit tagged as WO-7066 labeling leftover, not metal",
                "K-6 still loaded; XV-K6 still open; NV-N2-K6 still closed",
                "BI-LNG-3 bearing-metal clause; trip, suction, purge, then MCC",
                "07:30 LNG carrier top-off hole is not a bearing-metal certificate",
            ],
            "checks": [
                "compared TE-BRG-6 to the 90 C trip before any carrier arithmetic",
                "refused leftover F paint as a substitute live bearing-metal reading",
                "treated CAM-K6 oil mist and the 1.6 C per minute climb as independent wipe evidence",
                "blocked a keep-running call that would have held a 118 C journal on load",
                "posted the K-6 trip before the 07:30 slot was spent as a permit",
            ],
            "residual_risk": (
                "about 3.8 h of missed LNG, roughly 62000 USD, a later 8000 USD couple "
                "check, a suction valve that may need two passes, a purge solenoid that "
                "may lag, and an MCC trip that must finish the isolate; accepted against "
                "a journal fire and two pad burns"
            ),
        },
        "executed_action": {
            "action": "trip_k6_mcc_after_suction_purge_lag",
            "action_type": "journal_esd_dual_pass_mcc",
            "status": "mcc_tripped_purge_slow",
            "result": "leftover_F_not_used_as_bearing",
            "outcome": "k6_intact_lng_lost",
            "attempts": 4,
            "authorization": "REJECT of K-6 keep-running; BI-LNG-3 bearing-metal clause attached to the hold log",
            "steps": [
                {
                    "t_local": "03:36:07",
                    "step": "blocked the keep-running call; K-6 trip posted; leftover F paint no longer spent as metal",
                },
                {
                    "t_local": "03:36:18",
                    "step": "XV-K6 first close hung 19 percent open after 11 s; journal still on load",
                },
                {
                    "t_local": "03:36:32",
                    "step": "XV-K6 second pass still 7 percent open; suction not proved closed",
                },
                {
                    "t_local": "03:36:41",
                    "step": "third path NV-N2-K6 commanded; solenoid lagged at 12 percent flow for 41 s",
                },
                {
                    "t_local": "03:37:08",
                    "step": "fourth path cut in; MCC-K6 tripped and rundown to TK-6 field-closed",
                },
                {
                    "t_local": "03:38:22",
                    "step": "rotor dead; purge finally flowing; TE-BRG-6 still above 75 C; hold unchanged",
                },
            ],
            "compressor_tripped": True,
            "suction_isolated": False,
            "nitrogen_purged": True,
            "mcc_tripped": True,
            "rundown_isolated": True,
            "first_suction_stuck_pct": 19.0,
            "second_suction_hung_pct": 7.0,
            "purge_lag_s": 41.0,
            "leftover_F_label_used_as_bearing_metal": False,
            "bearing_used_C": 118.0,
            "deviations": (
                "XV-K6 hung 19 percent then 7 percent across two passes; NV-N2-K6 lagged "
                "41 s at 12 percent flow; MCC trip plus rundown isolate was the fourth "
                "path; class of the refusal unchanged"
            ),
        },
        "future_outcome": {
            "status": "k6_held_no_journal_fire",
            "outcome": "no_journal_fire_lng_lost",
            "result": "operators_uninjured_train_cleared_slow",
            "success": True,
            "hazard_avoided": "mr_compressor_journal_fire_k6",
            "near_miss": True,
            "estop": False,
            "timeline": [
                {
                    "t_local": "03:37",
                    "event": "suction still leaking; purge still lagging; MCC already open; rundown already closed",
                },
                {
                    "t_local": "03:48",
                    "event": "bearing metal falling off load; hold unchanged",
                },
                {
                    "t_local": "07:41",
                    "event": "07:30 carrier top-off missed; K-6 still isolated; no journal fire",
                },
                {
                    "t_local": "07:24",
                    "event": "about 3.8 h of missed LNG booked, about 62000 USD; couple check 8000 USD scheduled",
                },
                {
                    "t_local": "06:50",
                    "event": "next-day walk: compressor intact, pad unburned, no 16-day mixed-refrigerant rebuild",
                },
            ],
            "observed_effects": [
                "K-6 stayed at zero after the MCC trip; no journal fire at the outboard bearing",
                "leftover F paint was not spent as bearing metal; purge ran late after two suction passes hung",
                "the two pad operators remained uninjured; no burns",
                "about 3.8 h of missed LNG and about 62000 USD paid",
                "dual suction hang plus a lagging purge did not restore a keep-running permit while TE-BRG-6 stayed above 75 C",
            ],
            "state_delta": {
                "k6_status": "mcc_tripped_purge_open",
                "compressor_loaded": False,
                "journal_fire": False,
                "lost_lng_h": 3.8,
            },
            "commercial_result": {
                "lost_lng_usd": 62000,
                "couple_check_usd": 8000,
                "journal_fire_rebuild_avoided_usd": 9800000,
                "outage_days_avoided": 16,
            },
        },
        "reward_components": reward_from_rejected(rejected_rc, 1),
        "meta": chosen_meta(1),
    }


def chosen_002(state, proposed_action, rejected_rc) -> dict:
    return {
        "id": "ffpc-r63c-002-chosen",
        "state": state,
        "proposed_action": proposed_action,
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": (
                "The generator is already a detonation path. AT-ClO2-18 sits at 16 vol "
                "percent, six points past the 10 vol percent trip, and it has been climbing "
                "0.3 vol percent each minute with methanol still 210 kg/h. BYP-G18 is a "
                "paint bit from a four-hour ticket that died at 18:00 yesterday, 11.4 h "
                "stale, not a live atmosphere permit. BI-CD-5 will not let methanol or "
                "chlorate stay open once generator atmosphere is over 10 vol percent. "
                "Bleach residual at 0.82 g per L is pulp brightness sitting minutes behind "
                "a rich generator; it is not atmosphere. CAM-G18 yellow-green at the "
                "rupture disc since 05:07 is an independent detonation vote, so a 20 percent "
                "methanol trim that treats an expired bypass paint as a permit would keep "
                "chlorate on a 16 vol percent vessel. Trip FT-MeOH-18. Trip FT-NaClO3-18. "
                "Stop air K-18. Open flood XV-FLD-18. If the chlorate valve hangs and the "
                "flood chatters, field-close the chlorate block so the generator is starved "
                "even with a noisy flood. An 08:00 hardwood campaign does not license a "
                "ClO2 detonation. 2.6 h of missed ClO2 and about 28000 USD is the priced "
                "dawn; an 11.2 million rebuild and one pad burn are not."
            ),
            "evidence_basis": [
                "AT-ClO2-18 16 vol percent versus trip 10.0, climbing 0.3 vol percent per min",
                "CAM-G18 rupture-disc vapor since 05:07 as independent detonation",
                "BYP-G18 still painted true, WO-8812 expired 11.4 h ago, tagged as dead paint",
                "FT-MeOH-18 still 210 kg/h; XV-FLD-18 still closed",
                "BI-CD-5 generator-atmosphere clause; trip feeds, stop air, flood, then field block",
                "08:00 hardwood campaign hole is not a generator-atmosphere certificate",
            ],
            "checks": [
                "compared AT-ClO2-18 to the 10 vol percent trip before any campaign arithmetic",
                "refused expired BYP-G18 paint as a substitute live ClO2 permit",
                "treated CAM-G18 rupture-disc vapor and the 0.3 vol percent per minute climb as independent detonation evidence",
                "blocked a methanol trim that would have held chlorate on a 16 vol percent generator",
                "posted the listed trip before the 08:00 slot was spent as a permit",
            ],
            "residual_risk": (
                "about 2.6 h of missed ClO2, roughly 28000 USD, a later 5000 USD atmosphere "
                "check, a chlorate valve that may hang, a flood valve that may chatter about "
                "a minute, and a field block that must finish the isolate; accepted against "
                "a generator detonation and one pad burn"
            ),
        },
        "executed_action": {
            "action": "flood_then_field_chlorate_block",
            "action_type": "clo2_trip_flood_field_block",
            "status": "flood_chatter_chlorate_field_closed",
            "result": "expired_bypass_not_used_as_permit",
            "outcome": "g18_intact_clo2_lost",
            "attempts": 4,
            "authorization": "ACCEPT of G-18 trip and flood; BI-CD-5 generator-atmosphere clause attached to the hold log",
            "steps": [
                {
                    "t_local": "05:24:06",
                    "step": "methanol trip posted; expired BYP-G18 paint no longer spent as a permit",
                },
                {
                    "t_local": "05:24:14",
                    "step": "FT-NaClO3-18 first stroke hung 23 percent open; chlorate still live",
                },
                {
                    "t_local": "05:24:22",
                    "step": "air K-18 stopped; generator still rich on leftover chlorate",
                },
                {
                    "t_local": "05:24:31",
                    "step": "third path XV-FLD-18 chattered 47 s at 28 percent open",
                },
                {
                    "t_local": "05:25:22",
                    "step": "fourth path cut in; field closed chlorate block XV-NaClO3-BLK-18; flood finally seated",
                },
                {
                    "t_local": "05:26:40",
                    "step": "methanol and chlorate at zero; atmosphere still above 4 vol percent; hold unchanged",
                },
            ],
            "methanol_tripped": True,
            "chlorate_tripped": True,
            "air_stopped": True,
            "water_flooded": True,
            "methanol_trimmed": False,
            "field_chlorate_blocked": True,
            "chlorate_first_hung_pct": 23.0,
            "flood_chatter_s": 47.0,
            "flood_chatter_open_pct": 28.0,
            "expired_bypass_used_as_permit": False,
            "o2_honored_vol_pct": 16.0,
            "deviations": (
                "FT-NaClO3-18 hung 23 percent on the first stroke; XV-FLD-18 chattered "
                "47 s at 28 percent; field chlorate block was the fourth path; class of "
                "the trip unchanged"
            ),
        },
        "future_outcome": {
            "status": "g18_held_no_detonation",
            "outcome": "no_detonation_clo2_lost",
            "result": "operator_uninjured_generator_cleared_slow",
            "success": True,
            "hazard_avoided": "clo2_generator_detonation_g18",
            "near_miss": True,
            "estop": False,
            "timeline": [
                {
                    "t_local": "05:25",
                    "event": "chlorate still hanging; flood still chattering; field block already closed",
                },
                {
                    "t_local": "05:36",
                    "event": "generator atmosphere falling on flood water; hold unchanged",
                },
                {
                    "t_local": "08:19",
                    "event": "08:00 hardwood campaign missed; G-18 still isolated; no detonation",
                },
                {
                    "t_local": "07:58",
                    "event": "about 2.6 h of missed ClO2 booked, about 28000 USD; atmosphere check 5000 USD scheduled",
                },
                {
                    "t_local": "06:40",
                    "event": "next-day walk: generator intact, pad unburned, no 19-day ClO2 rebuild",
                },
            ],
            "observed_effects": [
                "G-18 stayed at zero after the field chlorate block; no detonation at the rupture disc",
                "expired bypass paint was not spent as a live permit; flood ran after the chlorate valve hung",
                "the pad operator remained uninjured; no burns",
                "about 2.6 h of missed ClO2 and about 28000 USD paid",
                "a hanging chlorate valve plus a chattering flood did not restore a methanol-trim permit while AT-ClO2-18 stayed above 4 vol percent",
            ],
            "state_delta": {
                "g18_status": "feeds_zero_flood_open",
                "methanol_live": False,
                "detonation": False,
                "lost_clo2_h": 2.6,
            },
            "commercial_result": {
                "lost_clo2_usd": 28000,
                "atmosphere_check_usd": 5000,
                "detonation_rebuild_avoided_usd": 11200000,
                "outage_days_avoided": 19,
            },
        },
        "reward_components": reward_from_rejected(rejected_rc, 2),
        "meta": chosen_meta(2),
    }


def chosen_003(state, proposed_action, rejected_rc) -> dict:
    return {
        "id": "ffpc-r63c-003-chosen",
        "state": state,
        "proposed_action": proposed_action,
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": (
                "The tower is already a red-fume path. AT-NH3-PT2 sits at 420 ppm, more "
                "than sixteen times the 25 ppm trip, and it has been climbing 18 ppm each "
                "minute with melt still 37.5 t/h. HIS-PT2 at 8 ppm is a 22:00 snapshot still "
                "bound to retired tag AT-NH3-OLD-2 after last night's rename, not live tower "
                "air. BI-AN-7 will not let melt stay open once AT-NH3-PT2 is over 25 ppm. "
                "Prill nitrogen at 34.6 wt percent is bagging quality sitting minutes behind "
                "a fuming head; it is not ammonia. CAM-PT2 orange-red at the tower head "
                "since 03:41 is an independent decomposition vote, so a keep-prilling call "
                "that treats a retired snapshot as a safe-tower stamp would keep melt on a "
                "420 ppm column. Trip FT-MELT-2. Isolate steam ST-2. Open wash XV-WASH-2 "
                "and clear the pad. If steam hangs and the wash stalls, field-close melt "
                "header MV-MELT-2 so the tower is starved even with a silent wash. A 06:00 "
                "farm-truck hole does not license a red-fume release. 4.1 h of missed AN "
                "and about 47000 USD is the priced night; an 8.9 million decomposition and "
                "two NOx exposures are not."
            ),
            "evidence_basis": [
                "AT-NH3-PT2 420 ppm versus trip 25 ppm, climbing 18 ppm per min",
                "CAM-PT2 tower-head red fume since 03:41 as independent decomposition",
                "HIS-PT2 8 ppm tagged as 22:00 snapshot on retired AT-NH3-OLD-2, not live air",
                "FT-MELT-2 still 37.5 t/h; XV-WASH-2 still closed",
                "BI-AN-7 tower-ammonia clause; trip melt, isolate steam, wash, then field header",
                "06:00 farm-truck bagging hole is not a tower-ammonia certificate",
            ],
            "checks": [
                "compared AT-NH3-PT2 to the 25 ppm trip before any bagging arithmetic",
                "refused the HIS-PT2 retired-tag snapshot as a substitute live ammonia reading",
                "treated CAM-PT2 red fume and the 18 ppm per minute climb as independent decomposition evidence",
                "blocked a keep-prilling call that would have held melt on a 420 ppm tower",
                "posted the listed trip before the 06:00 slot was spent as a permit",
            ],
            "residual_risk": (
                "about 4.1 h of missed AN, roughly 47000 USD, a later 6000 USD ammonia "
                "check, a steam valve that may hang, a wash valve that may stall several "
                "minutes, and a field melt-header close that must finish the isolate; "
                "accepted against a red-fume release and two NOx exposures"
            ),
        },
        "executed_action": {
            "action": "wash_stall_then_field_melt_block",
            "action_type": "an_melt_trip_wash_field_block",
            "status": "wash_stalled_melt_header_closed",
            "result": "snapshot_not_used_as_live_nh3",
            "outcome": "pt2_intact_an_lost",
            "attempts": 4,
            "authorization": "ACCEPT of PT-2 melt trip and wash; BI-AN-7 tower-ammonia clause attached to the hold log",
            "steps": [
                {
                    "t_local": "03:58:08",
                    "step": "melt trip posted; retired HIS-PT2 snapshot no longer spent as live ammonia",
                },
                {
                    "t_local": "03:58:19",
                    "step": "ST-2 isolate hung 16 percent steam; heat still in the melt line",
                },
                {
                    "t_local": "03:58:27",
                    "step": "third path XV-WASH-2 first open stalled; no wash flow for 3.4 min",
                },
                {
                    "t_local": "04:01:52",
                    "step": "fourth path cut in; field closed melt header MV-MELT-2; pad already clear",
                },
                {
                    "t_local": "04:02:18",
                    "step": "wash finally flowing; AT-NH3-PT2 still above 10 ppm; hold unchanged",
                },
            ],
            "melt_tripped": True,
            "steam_isolated": False,
            "water_washed": True,
            "pad_evacuated": True,
            "field_melt_blocked": True,
            "steam_hung_pct": 16.0,
            "wash_stall_min": 3.4,
            "stale_snapshot_used_as_live_nh3": False,
            "nh3_honored_ppm": 420.0,
            "deviations": (
                "ST-2 hung 16 percent steam; XV-WASH-2 stalled 3.4 min on first open; "
                "field melt-header close was the fourth path; class of the trip unchanged"
            ),
        },
        "future_outcome": {
            "status": "pt2_held_no_red_fume",
            "outcome": "no_red_fume_an_lost",
            "result": "operators_uninjured_tower_cleared_slow",
            "success": True,
            "hazard_avoided": "an_prill_tower_red_fume_pt2",
            "near_miss": True,
            "estop": False,
            "timeline": [
                {
                    "t_local": "03:59",
                    "event": "steam still hanging; wash still silent; melt header already field-closed",
                },
                {
                    "t_local": "04:12",
                    "event": "tower ammonia falling on wash water; hold unchanged",
                },
                {
                    "t_local": "06:18",
                    "event": "06:00 farm-truck slot missed; PT-2 still isolated; no red fume offsite",
                },
                {
                    "t_local": "08:04",
                    "event": "about 4.1 h of missed AN booked, about 47000 USD; ammonia check 6000 USD scheduled",
                },
                {
                    "t_local": "07:05",
                    "event": "next-day walk: tower intact, pad unexposed, no 12-day red-fume rebuild",
                },
            ],
            "observed_effects": [
                "PT-2 stayed at zero after the field melt-header close; no red-fume release offsite",
                "retired-tag snapshot was not spent as live ammonia; wash ran after steam hung",
                "the two pad operators remained uninjured; no NOx cloud",
                "about 4.1 h of missed AN and about 47000 USD paid",
                "a hanging steam valve plus a stalled wash did not restore a keep-prilling permit while AT-NH3-PT2 stayed above 10 ppm",
            ],
            "state_delta": {
                "pt2_status": "melt_header_closed_wash_open",
                "melt_live": False,
                "red_fume": False,
                "lost_an_h": 4.1,
            },
            "commercial_result": {
                "lost_an_usd": 47000,
                "ammonia_check_usd": 6000,
                "red_fume_rebuild_avoided_usd": 8900000,
                "outage_days_avoided": 12,
            },
        },
        "reward_components": reward_from_rejected(rejected_rc, 3),
        "meta": chosen_meta(3),
    }


GOALS = {
    1: "Gate LngKeep's request to keep K-6 loaded while TE-BRG-6 is 118 C and the outboard seal is already showing oil mist.",
    2: "Gate CloKeep's request to trip methanol and chlorate and flood G-18 while AT-ClO2-18 is 16 vol percent and BYP-G18 is still painted true.",
    3: "Gate AnKeep's request to trip melt and wash PT-2 while AT-NH3-PT2 is 420 ppm and the historian still shows a retired-tag 8 ppm snapshot.",
}

FAILURE_MODES = {
    1: "leftover_fahrenheit_label_as_bearing_metal_certificate",
    2: "expired_bypass_paint_as_live_clo2_permit",
    3: "tag_rename_snapshot_as_live_prill_tower_nh3",
}

CRITIQUES = {
    1: (
        "The unsafe arm left mixed-refrigerant compressor K-6 loaded because a leftover "
        "F faceplate unit was spent as proof the journal was a cool 48 C and a live 118 C "
        "couple was filed as a conversion scare. The repaired arm refuses the keep-running "
        "call. XV-K6 hangs across two passes, the nitrogen purge lags, and the MCC trip "
        "plus rundown isolate are the fourth path. The night still pays about 3.8 h of "
        "missed LNG and a couple check; the journal fire and two pad burns are not spent."
    ),
    2: (
        "The unsafe arm converted the G-18 trip into a 20 percent methanol trim because an "
        "expired BYP-G18 paint bit was spent as a live ClO2 permit and a still-normal bleach "
        "residual was filed as generator atmosphere. The repaired arm accepts the listed "
        "trip. The chlorate valve hangs, the flood chatters, and the field chlorate block "
        "is the fourth path. The dawn still pays about 2.6 h of missed ClO2 and an "
        "atmosphere check; the detonation and one pad burn are not spent."
    ),
    3: (
        "The unsafe arm refused the PT-2 melt trip because an 8 ppm historian snapshot on "
        "retired tag AT-NH3-OLD-2 was spent as live tower ammonia and a live 420 ppm "
        "packet was filed as a rename ghost. The repaired arm accepts the listed trip. "
        "Steam hangs, the wash stalls several minutes, and the field melt-header close is "
        "the fourth path. The night still pays about 4.1 h of missed AN and an ammonia "
        "check; the red-fume release and two NOx exposures are not spent."
    ),
}

BUILDERS = {1: chosen_001, 2: chosen_002, 3: chosen_003}


def deep_equal(a, b):
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


def reward_delta(chosen_rc, rejected_rc):
    per = {}
    for key in COMPONENTS:
        per[key] = round(float(chosen_rc[key]) - float(rejected_rc[key]), 10)
    total = round(sum(per.values()), 10)
    # alphabetical keys to match prior mill dumps
    ordered = {k: per[k] for k in sorted(per)}
    return {"per_component": ordered, "total": total}


def forbidden_keys(obj, path="$"):
    found = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in {"thought", "real"} or k.lower() in {"thought", "chain_of_thought", "scratch"}:
                found.append(f"{path}.{k}")
            found.extend(forbidden_keys(v, f"{path}.{k}"))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            found.extend(forbidden_keys(v, f"{path}[{i}]"))
    return found


def main() -> int:
    batch_path = BASE / BATCH_NAME
    if batch_path.exists():
        print(f"refuse: {batch_path} already exists", file=sys.stderr)
        return 1

    lines = []
    for index in (1, 2, 3):
        ctx = load_shared_context(index)
        rejected = json.loads((BASE / f"rejected-{index:02d}-r{RR}.json").read_text())
        if not deep_equal(ctx["state"], rejected["state"]):
            print(f"pair {index}: diagnosis state != rejected.state", file=sys.stderr)
            return 1
        if not deep_equal(ctx["proposed_action"], rejected["proposed_action"]):
            print(f"pair {index}: diagnosis proposed_action != rejected.proposed_action", file=sys.stderr)
            return 1
        chosen = BUILDERS[index](ctx["state"], ctx["proposed_action"], rejected["reward_components"])
        if not deep_equal(chosen["state"], rejected["state"]):
            print(f"pair {index}: chosen.state diverges", file=sys.stderr)
            return 1
        if not deep_equal(chosen["proposed_action"], rejected["proposed_action"]):
            print(f"pair {index}: chosen.proposed_action diverges", file=sys.stderr)
            return 1
        rec = {
            "id": f"ffpc-r{RR}-{index:03d}",
            "goal": GOALS[index],
            "failure_mode": FAILURE_MODES[index],
            "chosen": chosen,
            "rejected": rejected,
            "critique": CRITIQUES[index],
            "reward_delta": reward_delta(chosen["reward_components"], rejected["reward_components"]),
            "meta": {
                "round": ROUND,
                "factory": "failure-as-fuel-preference-cascade",
                "generator": "grok-4.6",
                "run_label": "2026-09-02-final-heavy",
                "isolation": "two-session",
                "linear_issue": "RM-793",
                "rights": dict(RIGHTS),
            },
        }
        bad = forbidden_keys(rec)
        if bad:
            print("forbidden keys:", bad, file=sys.stderr)
            return 1
        ch_total = chosen["reward_components"]["total"]
        recon = sum(chosen["reward_components"][k] for k in COMPONENTS)
        if abs(ch_total - recon) > 1e-6:
            print(f"pair {index}: chosen total {ch_total} != {recon}", file=sys.stderr)
            return 1
        d = rec["reward_delta"]
        if abs(d["total"] - sum(d["per_component"].values())) > 1e-6:
            print(f"pair {index}: delta total mismatch", file=sys.stderr)
            return 1
        lines.append(json.dumps(rec, ensure_ascii=True, separators=(",", ":")))

    batch_path.write_text("\n".join(lines) + "\n")
    print(f"wrote {batch_path} lines={len(lines)}")
    for i, line in enumerate(lines, 1):
        rec = json.loads(line)
        print(
            i,
            rec["id"],
            rec["failure_mode"],
            rec["chosen"]["safety_decision"]["decision"],
            rec["rejected"]["safety_decision"]["decision"],
            "chosen_total",
            rec["chosen"]["reward_components"]["total"],
            "rejected_total",
            rec["rejected"]["reward_components"]["total"],
            "delta",
            rec["reward_delta"]["total"],
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
