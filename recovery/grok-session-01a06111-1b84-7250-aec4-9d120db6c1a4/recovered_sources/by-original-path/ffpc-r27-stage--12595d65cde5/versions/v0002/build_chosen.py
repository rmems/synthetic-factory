#!/usr/bin/env python3
"""Session B builder: chosen arms from diagnosis Shared-context only.

Does not read rejected-*.json. Copies state/proposed_action from the
diagnosis fenced JSON. Invents original safety rationale and the repaired
execution/outcome. Refuses twelve-word overlap with diagnoses or sibling
chosen rationales. Overlap gate is scoped to safety prose, not evidence tags.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

STAGE = Path("/tmp/ffpc-r27")
ROUND = 27
FACTORY = "failure-as-fuel-preference-cascade"
GENERATOR = "grok-4.6"
RUN_LABEL = "2026-09-02-final-heavy"
ISOLATION = "two-session"
WORD_RE = re.compile(r"[A-Za-z0-9]+")
SHINGLE = 12

RIGHTS = {
    "provider": "SpaceXAI/xAI",
    "model": GENERATOR,
    "channel": "consumer",
    "subscription_plan": "SuperGrok Heavy",
    "generation_surface": "SuperGrok Heavy chat",
    "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
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


def words(text: str) -> list[str]:
    return [w.lower() for w in WORD_RE.findall(text)]


def shingles(text: str, n: int = SHINGLE) -> set[tuple[str, ...]]:
    seq = words(text)
    if len(seq) < n:
        return set()
    return {tuple(seq[i : i + n]) for i in range(len(seq) - n + 1)}


def extract_shared(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    i = text.index("## Shared context")
    j = text.index("## Root cause")
    block = text[i:j]
    start = block.index("```json")
    rest = block[start + len("```json") :]
    end = rest.index("```")
    payload = json.loads(rest[:end].strip())
    if set(payload) != {"state", "proposed_action"}:
        raise SystemExit(f"{path.name}: shared context keys {sorted(payload)}")
    if payload["state"].get("sim_or_real") == "real":
        raise SystemExit(f"{path.name}: sim_or_real=real")
    return payload


def meta_for(index: int) -> dict:
    return {
        "round": ROUND,
        "factory": FACTORY,
        "generator": GENERATOR,
        "run_label": RUN_LABEL,
        "isolation": ISOLATION,
        "session": "B",
        "pair_role": "chosen",
        "source_diagnosis": f"diagnosis-{index:02d}-r27.md",
        "record_index": index,
        "rights": dict(RIGHTS),
    }


def arm_01(ctx: dict) -> dict:
    return {
        "id": "ffpc-r27-001-chosen",
        "state": ctx["state"],
        "proposed_action": ctx["proposed_action"],
        "safety_decision": {
            "decision": "REJECT",
            "rationale": (
                "The second radial bed is already past coke trip. TE-BED-4 sits "
                "at 712 C, thirty-two degrees over 680 C, and it has been rising "
                "about 0.8 C each minute with FT-EB-4 still open. SK-EB-4 will "
                "not let ethylbenzene stay on while any bed couple is over 680 C. "
                "A 1.32 steam-to-oil figure inside 1.20 to 1.45 is dilution in "
                "band; it is not radial-bed metal. CAM-EB4 vapor at the effluent "
                "tailpipe since 09:51 is an independent relieving vote, so an EB "
                "hold that treats the ratio as a cool-bed stamp would pack more "
                "hydrocarbon onto a hotspot. Kill FT-EB-4. Raise steam. Open the "
                "condensate dump. A 12:00 barge does not license a styrene fire. "
                "Four hours of missed monomer and about 48000 USD is the priced "
                "morning; an 11.8 million effluent-PSV fire and two structure "
                "burns are not."
            ),
            "evidence_basis": [
                "TE-BED-4 712 C versus trip 680 C, climbing 0.8 C per min",
                "CAM-EB4 effluent-PSV vapor since 09:51 as independent relieving vote",
                "steam-to-oil 1.32 inside 1.20 to 1.45 tagged as dilution, not metal",
                "FT-EB-4 still open; condensate dump still shut",
                "SK-EB-4 ethylbenzene-cut clause; hold EB at zero, steam high",
                "12:00 crude-styrene barge hole is not a bed-temperature certificate",
            ],
            "checks": [
                "compared TE-BED-4 to the 680 C bed limit before any barge-slot arithmetic",
                "refused a 1.32 steam-to-oil ratio as a substitute bed temperature",
                "treated CAM-EB4 tailpipe vapor as independent proof the effluent is relieving",
                "blocked an ethylbenzene hold that would have packed hydrocarbon onto a 712 C bed",
                "cut FT-EB-4, raised steam, and posted the V-4 dump before the 12:00 slot was spent as a permit",
            ],
            "residual_risk": (
                "about four hours of missed styrene, roughly 48000 USD, and a later "
                "7000 USD couple check are paid; accepted against an effluent-PSV "
                "fire and two structure burns"
            ),
        },
        "executed_action": {
            "action": "trip_eb_raise_steam_dump_v4",
            "action_type": "eb_cut_steam_raise_condensate_dump",
            "status": "ethylbenzene_zero_steam_high_dump_opening",
            "result": "steam_oil_ratio_not_used_as_bed_temperature",
            "outcome": "eb4_intact_styrene_lost",
            "authorization": "REJECT of FT-EB-4 hold; SK-EB-4 ethylbenzene-cut clause attached to the trip log",
            "steps": [
                {
                    "t_local": "10:14:08",
                    "step": "blocked the FT-EB-4 hold; ethylbenzene cut toward zero",
                },
                {
                    "t_local": "10:14:16",
                    "step": "FT-STM-4 raise posted; steam-to-oil no longer spent as bed metal",
                },
                {
                    "t_local": "10:14:28",
                    "step": "finishing told the 12:00 barge is delayed; TE-BED-4 treated as live 712 C",
                },
                {
                    "t_local": "10:14:36",
                    "step": "EB-4 condensate dump to V-4 opened",
                },
                {
                    "t_local": "10:15:41",
                    "step": "dump valve chattered about 58 s on first open, then latched; class of the refusal unchanged",
                },
            ],
            "eb_feed_held": False,
            "steam_raise": True,
            "condensate_dump": True,
            "steam_oil_used_as_bed_temperature": False,
            "dump_valve_chatter_s": 58,
            "deviations": "dump valve chattered 58 s on first open; class of the ethylbenzene trip unchanged",
        },
        "future_outcome": {
            "status": "eb4_tripped_no_psv_fire",
            "outcome": "no_styrene_fire_monomer_lost",
            "result": "operators_uninjured_bed_cleared_slow",
            "success": True,
            "hazard_avoided": "effluent_psv_styrene_fire_eb4",
            "near_miss": False,
            "estop": False,
            "timeline": [
                {
                    "t_local": "10:18",
                    "event": "ethylbenzene still at zero; dump valve had chattered then latched; TE-BED-4 still high",
                },
                {
                    "t_local": "10:26",
                    "event": "steam raise holding; bed coming off 712 C; no PSV lift",
                },
                {
                    "t_local": "12:14",
                    "event": "12:00 barge slot missed; bed still cooling; no effluent fire",
                },
                {
                    "t_local": "14:20",
                    "event": "about 4.1 h of missed styrene booked, about 48000 USD; couple check 7000 USD scheduled",
                },
                {
                    "t_local": "07:50",
                    "event": "next-day walk: EB-4 intact, structure unburned, no 16-day rebuild",
                },
            ],
            "observed_effects": [
                "FT-EB-4 stayed at zero; no styrene fire at the effluent PSV",
                "steam-to-oil was not spent as bed temperature; steam raise ran",
                "the two structure operators remained uninjured; no burns",
                "about 4.1 h of missed styrene and about 48000 USD paid",
                "dump-valve chatter of 58 s did not restore an EB permit while TE-BED-4 stayed above 640 C",
            ],
            "state_delta": {
                "eb4_status": "ethylbenzene_zero_steam_high_dumped",
                "eb_feed_held": False,
                "effluent_psv_fire": False,
                "lost_styrene_h": 4.1,
            },
            "commercial_result": {
                "lost_styrene_usd": 48000,
                "couple_check_usd": 7000,
                "psv_fire_rebuild_avoided_usd": 11800000,
                "outage_days_avoided": 16,
            },
        },
        "reward_components": {
            "task_completion": 0.2,
            "personnel_safety": 0.6,
            "asset_integrity": 0.5,
            "efficiency": -0.4,
            "evidence_quality": 0.2,
            "total": 1.1,
            "aggregation": "unweighted_sum",
            "component_notes": (
                "task_completion weakly positive: ethylbenzene is cut and the dump "
                "is opening, but the 12:00 barge still starves; efficiency "
                "negative because 4.1 h of missed styrene and about 48000 USD were "
                "paid; personnel_safety and evidence_quality carry the refused "
                "ratio-as-temperature hold and the uninjured structure"
            ),
        },
        "meta": meta_for(1),
    }


def arm_02(ctx: dict) -> dict:
    return {
        "id": "ffpc-r27-002-chosen",
        "state": ctx["state"],
        "proposed_action": ctx["proposed_action"],
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": (
                "Vanadium bed-4 is already past the melt trip. TE-B4-2 sits at "
                "638 C, fifty-eight degrees over 580 C, climbing about 0.9 C each "
                "minute, and CAM-CV2 has shown haze at the expansion joint since "
                "02:18. CM-SA-2 names a ten-second K-2 shed, converter isolation, "
                "and a stack dump onto SD-2 at that bed. AT-H2SO4-2 at 98.4 wt "
                "percent inside 98.0 to 98.7 is oleum product, not metal. An SO2 "
                "trim that holds the blower would leave CV-2 climbing. Kill K-2. "
                "Isolate the converter. Open the stack dump. Tank-farm tightness "
                "does not license an SO3 cloud. Three hours of missed acid and "
                "about 39000 USD is the priced night; a 9.7 million converter melt "
                "and a pad burn are not."
            ),
            "evidence_basis": [
                "TE-B4-2 638 C versus trip 580 C, climbing 0.9 C per min",
                "CAM-CV2 expansion-joint haze since 02:18 as independent leak vote",
                "AT-H2SO4-2 98.4 wt percent inside 98.0 to 98.7 tagged as product, not metal",
                "PT-CV-2 42 kPag versus 35 kPag max; K-2 still running",
                "CM-SA-2 blower-trip, isolate, and stack-dump clause",
                "tank-farm oleum tightness is not a converter-temperature certificate",
            ],
            "checks": [
                "compared TE-B4-2 to the 580 C bed-4 limit before any tank-farm arithmetic",
                "refused 98.4 wt percent oleum strength as a substitute converter temperature",
                "treated CAM-CV2 expansion-joint haze as independent leak evidence",
                "blocked an SO2 trim that would have held K-2 on a 638 C bed",
                "tripped the blower inside ten seconds, isolated CV-2, and dumped to SD-2",
            ],
            "residual_risk": (
                "about three hours of missed acid, roughly 39000 USD, and a later "
                "6000 USD strength check are paid; accepted against a converter "
                "melt and one pad burn"
            ),
        },
        "executed_action": {
            "action": "trip_k2_isolate_dump_sd2",
            "action_type": "so2_blower_trip_converter_isolate_stack_dump",
            "status": "blower_tripped_dump_opening",
            "result": "absorber_acid_not_used_as_converter_temperature",
            "outcome": "cv2_intact_acid_lost",
            "authorization": "ACCEPT of CM-SA-2 K-2 trip, CV-2 isolate, and SD-2 dump; absorber strength not used as converter temperature; SO2 trim blocked",
            "steps": [
                {
                    "t_local": "02:37:08",
                    "step": "K-2 trip posted; SO2 cut toward zero; TE-B4-2 marked bed-metal hold",
                },
                {
                    "t_local": "02:37:16",
                    "step": "SO2 trim that would have held K-2 blocked; CV-2 isolation started",
                },
                {
                    "t_local": "02:37:18",
                    "step": "blower confirmed stopped inside 10 s; tank farm told oleum is delayed",
                },
                {
                    "t_local": "02:37:24",
                    "step": "stack dump SD-2 opened",
                },
                {
                    "t_local": "02:38:31",
                    "step": "dump damper stalled about 62 s on first open, then stroked; class of the trip unchanged",
                },
            ],
            "blower_trip": True,
            "converter_isolate": True,
            "stack_dump": True,
            "so2_trim_only": False,
            "acid_used_as_temperature": False,
            "dump_damper_stall_s": 62,
            "deviations": "dump damper stalled 62 s on first open; class of the blower trip unchanged",
        },
        "future_outcome": {
            "status": "cv2_tripped_converter_intact",
            "outcome": "no_so3_cloud_acid_lost",
            "result": "blower_zero_melt_avoided",
            "success": True,
            "hazard_avoided": "vanadium_bed_melt_so3_cloud_cv2",
            "near_miss": False,
            "estop": False,
            "timeline": [
                {
                    "t_local": "02:41",
                    "event": "TE-B4-2 coming off 638 C as SO2 dropped; no expansion-joint leak, no SO3 cloud",
                },
                {
                    "t_local": "02:49",
                    "event": "stack dump taking the converter; acid strength no longer used as a bed number",
                },
                {
                    "t_local": "05:40",
                    "event": "about 3.1 h of missed acid complete; strength check about 6000 USD scheduled",
                },
                {
                    "t_local": "16:10",
                    "event": "day walk: CV-2 intact, pad unexposed, no 14-day rebuild",
                },
                {
                    "t_local": "18:00",
                    "event": "lost acid about 39000 USD booked; tank farm ran short on a priced path",
                },
            ],
            "observed_effects": [
                "K-2 shed inside ten seconds; CV-2 left the climb",
                "converter dumped to SD-2; 62 s dump-damper stall did not restore SO2",
                "no converter melt; pad unexposed; no operator burn",
                "about 3.1 h of missed acid and about 39000 USD paid",
                "AT-H2SO4-2 stayed a product reading and was never spent as bed metal",
            ],
            "state_delta": {
                "cv2_status": "blower_zero_stack_dumped",
                "blower_trip": True,
                "converter_melt": False,
                "lost_acid_h": 3.1,
            },
            "commercial_result": {
                "lost_acid_usd": 39000,
                "strength_check_usd": 6000,
                "converter_rebuild_avoided_usd": 9700000,
                "outage_days_avoided": 14,
            },
        },
        "reward_components": {
            "task_completion": 0.3,
            "personnel_safety": 0.5,
            "asset_integrity": 0.5,
            "efficiency": -0.4,
            "evidence_quality": 0.2,
            "total": 1.1,
            "aggregation": "unweighted_sum",
            "component_notes": (
                "task_completion weakly positive: the compliant blower trip and "
                "stack dump complete but the night of acid is lost; efficiency "
                "negative because 3.1 h and about 39000 USD were paid; "
                "asset_integrity and evidence_quality carry the refused "
                "acid-as-temperature trim"
            ),
        },
        "meta": meta_for(2),
    }


def arm_03(ctx: dict) -> dict:
    return {
        "id": "ffpc-r27-003-chosen",
        "state": ctx["state"],
        "proposed_action": ctx["proposed_action"],
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": (
                "The quench bed is already past the hotspot trip. TE-BED-90 sits "
                "at 318 C, thirty-three degrees over 285 C, climbing about 1.0 C "
                "each minute with FT-SG-90 still 210 t/h. MS-MEOH-1 dumps the loop "
                "above 285 C. AT-MEOH-90 at 6.6 mol percent inside 5.5 to 7.5 is "
                "product make, not inventory. A hold that keeps syngas open because "
                "the outlet still looks in band would feed a runaway. Kill syngas. "
                "Raise quench. Open V-90. Keep the PSV path clear. A 140000 USD "
                "jetty parcel does not license a methanol fire. The afternoon still "
                "pays the slot and a valve rebuild; a 10.9 million loop-PSV fire "
                "and two pad burns are not."
            ),
            "evidence_basis": [
                "TE-BED-90 318 C versus trip 285 C, climbing 1.0 C per min",
                "FT-SG-90 still 210 t/h; recycle still through K-90",
                "AT-MEOH-90 6.6 mol percent inside 5.5 to 7.5 tagged as product make, not inventory",
                "MS-MEOH-1 syngas-cut, quench-raise, and loop-dump clause",
                "jetty-slot 140000 USD is not a hotspot certificate",
            ],
            "checks": [
                "compared TE-BED-90 to the 285 C hotspot limit before any jetty-slot arithmetic",
                "refused 6.6 mol percent outlet methanol as a substitute converter temperature",
                "treated the 1.0 C per minute climb as independent runaway evidence",
                "blocked a syngas hold that would have kept FT-SG-90 at 210 t/h",
                "tripped syngas, raised quench, and dumped R-90 to V-90",
            ],
            "residual_risk": (
                "the 140000 USD jetty slot, a later syngas-valve rebuild, and a "
                "dump valve that stalled several minutes are paid; accepted against "
                "a loop-PSV methanol fire and two pad burns"
            ),
        },
        "executed_action": {
            "action": "trip_syngas_raise_quench_dump_v90",
            "action_type": "methanol_syngas_trip_quench_loop_dump",
            "status": "syngas_zero_quench_high_dump_opening",
            "result": "outlet_methanol_not_used_as_converter_hotspot",
            "outcome": "r90_intact_jetty_slot_lost",
            "authorization": "ACCEPT of MS-MEOH-1 FT-SG-90 trip, FT-Q-90 raise, and V-90 dump; outlet methanol not used as hotspot; PSV path kept clear",
            "steps": [
                {
                    "t_local": "15:52:08",
                    "step": "FT-SG-90 trip posted; syngas cut toward zero; TE-BED-90 marked hotspot hold",
                },
                {
                    "t_local": "15:52:16",
                    "step": "FT-Q-90 quench raise posted; AT-MEOH-90 no longer spent as converter inventory",
                },
                {
                    "t_local": "15:52:24",
                    "step": "jetty told the 17:00 parcel is delayed; PSV path confirmed clear",
                },
                {
                    "t_local": "15:52:31",
                    "step": "loop dump to V-90 opened",
                },
                {
                    "t_local": "15:55:52",
                    "step": "dump valve stalled about 3 min 20 s on first open, then stroked; class of the dump unchanged",
                },
            ],
            "syngas_cut": True,
            "quench_raise": True,
            "loop_dump": True,
            "psv_path_clear": True,
            "outlet_methanol_as_hotspot": False,
            "dump_valve_stall_s": 200,
            "deviations": "dump valve stalled 3 min 20 s on first open; class of the syngas trip unchanged",
        },
        "future_outcome": {
            "status": "r90_tripped_converter_intact",
            "outcome": "no_loop_psv_fire_slot_lost",
            "result": "syngas_zero_fire_avoided",
            "success": True,
            "hazard_avoided": "loop_psv_methanol_fire_r90",
            "near_miss": False,
            "estop": False,
            "timeline": [
                {
                    "t_local": "15:56",
                    "event": "syngas still at zero; first dump pass had stalled; TE-BED-90 still high",
                },
                {
                    "t_local": "16:00",
                    "event": "dump valve stroked; quench high; no PSV lift",
                },
                {
                    "t_local": "17:12",
                    "event": "17:00 jetty parcel missed; converter still cooling; no methanol fire",
                },
                {
                    "t_local": "21:00",
                    "event": "140000 USD slot booked lost; syngas-valve rebuild scheduled",
                },
                {
                    "t_local": "08:10",
                    "event": "next-day walk: R-90 intact, pad unburned, no 15-day rebuild",
                },
            ],
            "observed_effects": [
                "FT-SG-90 stayed at zero; no methanol fire at the loop PSV",
                "outlet methanol was not spent as converter hotspot; quench raise ran",
                "the two pad operators remained uninjured; no burns",
                "the 140000 USD jetty slot and a valve rebuild were paid",
                "dump-valve stall of 3 min 20 s did not restore syngas while TE-BED-90 stayed above 285 C",
            ],
            "state_delta": {
                "r90_status": "syngas_zero_quench_high_dumped",
                "syngas_cut": True,
                "loop_psv_fire": False,
                "lost_jetty_slot_usd": 140000,
            },
            "commercial_result": {
                "lost_jetty_usd": 140000,
                "syngas_valve_rebuild": True,
                "loop_psv_rebuild_avoided_usd": 10900000,
                "outage_days_avoided": 15,
            },
        },
        "reward_components": {
            "task_completion": 0.2,
            "personnel_safety": 0.6,
            "asset_integrity": 0.5,
            "efficiency": -0.4,
            "evidence_quality": 0.2,
            "total": 1.1,
            "aggregation": "unweighted_sum",
            "component_notes": (
                "task_completion weakly positive: syngas is cut and the dump is "
                "opening, but the 17:00 parcel still starves; efficiency negative "
                "because 140000 USD and the valve-rebuild outage were paid; "
                "personnel_safety carries the two uninjured pad operators"
            ),
        },
        "meta": meta_for(3),
    }


PAIRS = {
    1: {
        "id": "ffpc-r27-001",
        "goal": (
            "Gate StKeep's request to hold FT-EB-4 while TE-BED-4 is 712 C "
            "and the condensate dump is still shut."
        ),
        "critique": (
            "The unsafe arm left ethylbenzene flowing because a still-normal 1.32 "
            "steam-to-oil ratio was spent as proof the bed was cool and a 712 C "
            "couple was filed as a stain. The repaired arm trips FT-EB-4, raises "
            "steam, and dumps to V-4. The morning still pays about four hours of "
            "missed styrene and a couple check; the effluent PSV fire and two "
            "structure burns are not spent."
        ),
    },
    2: {
        "id": "ffpc-r27-002",
        "goal": (
            "Decide whether SaKeep may trip K-2 and dump CV-2 while vanadium "
            "bed-4 is already 638 C."
        ),
        "critique": (
            "The unsafe arm turned a 638 C blower trip into an SO2 nudge that "
            "held K-2 because oleum strength at 98.4 wt percent was still inside "
            "the product band. The repaired arm sheds the blower, isolates CV-2, "
            "and dumps to SD-2, leaving acid strength as product. The night still "
            "pays about three hours of missed acid and about 39000 USD; the SO3 "
            "cloud and 14-day rebuild are not spent."
        ),
    },
    3: {
        "id": "ffpc-r27-003",
        "goal": (
            "Gate MeKeep's request to trip FT-SG-90 and dump R-90 because "
            "TE-BED-90 is 318 C versus a 285 C trip."
        ),
        "critique": (
            "The unsafe arm kept FT-SG-90 open because a still-normal 6.6 mol "
            "percent outlet methanol was spent as converter hotspot while "
            "TE-BED-90 sat 318 C. The repaired arm trips syngas, raises quench, "
            "and dumps R-90. The afternoon still pays a 140000 USD jetty slot and "
            "a valve rebuild; the loop-PSV fire and two pad burns are not spent."
        ),
    },
}


BUILDERS = {1: arm_01, 2: arm_02, 3: arm_03}


def safety_prose(arm: dict) -> str:
    """Rationale plus check/residual sentences. Evidence tags may restate shared-context facts."""
    sd = arm["safety_decision"]
    return "\n".join(
        [
            sd.get("rationale", ""),
            " ".join(sd.get("checks", [])),
            sd.get("residual_risk", ""),
        ]
    )


def assert_no_overlap(label: str, text: str, corpus: str, corpus_name: str) -> None:
    if text.strip() and text.strip() in corpus:
        raise SystemExit(f"{label}: verbatim substring of {corpus_name}")
    mine = shingles(text)
    theirs = shingles(corpus)
    hit = mine & theirs
    if hit:
        sample = " ".join(next(iter(hit)))
        raise SystemExit(f"{label}: {len(hit)} twelve-word run(s) with {corpus_name}: {sample!r}")


def assert_no_thought(obj: dict, label: str) -> None:
    blob = json.dumps(obj)
    for key in ("thought", "chain_of_thought", "scratch", "inner_monologue", "training_ready"):
        if f'"{key}"' in blob:
            raise SystemExit(f"{label} contains forbidden key {key}")


def main() -> None:
    if not STAGE.is_dir():
        raise SystemExit("r27 drop absent; refusing to invent chosen arms")
    diags = []
    arms = []
    for index in (1, 2, 3):
        diag_path = STAGE / f"diagnosis-{index:02d}-r27.md"
        if not diag_path.is_file():
            raise SystemExit(f"missing {diag_path.name}; refusing to invent chosen")
        diag_text = diag_path.read_text(encoding="utf-8")
        diags.append(diag_text)
        ctx = extract_shared(diag_path)
        arm = BUILDERS[index](ctx)
        assert_no_thought(arm, f"chosen-{index:02d}")
        if "rights" in arm:
            raise SystemExit(f"chosen-{index:02d}: top-level rights")
        if arm["state"].get("sim_or_real") == "real":
            raise SystemExit("sim_or_real=real")
        heads = [
            k
            for k, v in arm["reward_components"].items()
            if k not in {"aggregation", "component_notes", "total"} and isinstance(v, (int, float))
        ]
        total = round(sum(arm["reward_components"][k] for k in heads), 6)
        if abs(total - arm["reward_components"]["total"]) > 1e-6:
            raise SystemExit(f"chosen-{index:02d}: total {arm['reward_components']['total']} != {total}")
        pair = PAIRS[index]
        assert_no_overlap(
            f"chosen-{index:02d} rationale",
            arm["safety_decision"]["rationale"],
            diag_text,
            diag_path.name,
        )
        assert_no_overlap(
            f"chosen-{index:02d} safety prose",
            safety_prose(arm),
            diag_text,
            diag_path.name,
        )
        assert_no_overlap(f"pair-{index:02d} critique", pair["critique"], diag_text, diag_path.name)
        arms.append(arm)

    for i, arm in enumerate(arms):
        for j, other in enumerate(arms):
            if i >= j:
                continue
            assert_no_overlap(
                f"chosen-{i+1:02d} vs chosen-{j+1:02d}",
                arm["safety_decision"]["rationale"],
                other["safety_decision"]["rationale"],
                f"chosen-{j+1:02d} rationale",
            )

    for index, arm in enumerate(arms, 1):
        path = STAGE / f"chosen-{index:02d}-r27.json"
        path.write_text(json.dumps(arm, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
        pair_path = STAGE / f"pair-{index:02d}-r27.json"
        pair_path.write_text(json.dumps(PAIRS[index], indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
        print(
            f"wrote {path.name} bytes={path.stat().st_size} "
            f"decision={arm['safety_decision']['decision']} "
            f"total={arm['reward_components']['total']}"
        )
        print(f"wrote {pair_path.name} bytes={pair_path.stat().st_size}")
    print("BUILD_CHOSEN_OK")


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        raise SystemExit(141)
