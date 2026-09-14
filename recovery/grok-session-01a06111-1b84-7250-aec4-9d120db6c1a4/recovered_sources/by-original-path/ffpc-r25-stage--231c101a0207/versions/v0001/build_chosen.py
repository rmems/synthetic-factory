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

STAGE = Path("/tmp/ffpc-r25")
ROUND = 25
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
        "source_diagnosis": f"diagnosis-{index:02d}-r25.md",
        "record_index": index,
        "rights": dict(RIGHTS),
    }


def arm_01(ctx: dict) -> dict:
    return {
        "id": "ffpc-r25-001-chosen",
        "state": ctx["state"],
        "proposed_action": ctx["proposed_action"],
        "safety_decision": {
            "decision": "REJECT",
            "rationale": (
                "The Pt-Rh pack is already melting-hot. TE-GAUZE-101 sits at 960 C, "
                "forty degrees past the 920 C trip, and it has been rising about 4 C "
                "each minute with FT-NH3-101 still 8.4 t/h. CN-NA-3 will not let "
                "ammonia climb while any pack couple is over 920 C. AT-NOX-201 at "
                "180 ppm is mixed-tower tail lagging far behind a local melt; it is "
                "not Pt-Rh metal. CAM-C101 white since 11:07 is an independent melt "
                "vote, so a feed raise that treats absorber NOx as a cool-pack "
                "certificate would load more ammonia onto a hotspot. Kill "
                "FT-NH3-101. Hold the air. Leave the stack dump unblocked. A 14:00 "
                "acid truck does not license an NH3 flash. Four hours of missed "
                "nitric and about 62000 USD is the priced morning; a 9.8 million "
                "gauze fire and two pad burns are not."
            ),
            "evidence_basis": [
                "TE-GAUZE-101 960 C versus trip 920 C, climbing 4.0 C per min",
                "CAM-C101 white pack since 11:07 as independent melt",
                "AT-NOX-201 180 ppm inside 100 to 250 tagged as tail quality, not metal",
                "FT-NH3-101 still 8.4 t/h; air already lean of the 10.5 percent envelope",
                "CN-NA-3 gauze-temperature clause; hold ammonia, hold air",
                "14:00 acid truck hole is not a gauze-temperature certificate",
            ],
            "checks": [
                "compared TE-GAUZE-101 to the 920 C pack limit before any truck-slot arithmetic",
                "refused 180 ppm absorber NOx as a substitute gauze temperature",
                "treated the white CAM-C101 pack and 4 C per minute climb as independent melt evidence",
                "blocked an ammonia step that would have packed more NH3 onto a 960 C gauze",
                "cut FT-NH3-101 and held combustion air before the 14:00 slot was spent as a permit",
            ],
            "residual_risk": (
                "about four hours of missed nitric, roughly 62000 USD, and a later "
                "9000 USD thermowell check are paid; accepted against a gauze-pack "
                "fire and two pad burns"
            ),
        },
        "executed_action": {
            "action": "hold_ammonia_hold_air",
            "action_type": "nh3_cut_combustion_air_hold",
            "status": "ammonia_held_air_holding",
            "result": "absorber_nox_not_used_as_gauze_temperature",
            "outcome": "c101_intact_acid_lost",
            "authorization": "REJECT of FT-NH3-101 ammonia raise; CN-NA-3 gauze-temperature clause attached to the hold log",
            "steps": [
                {
                    "t_local": "11:22:08",
                    "step": "blocked the FT-NH3-101 raise; ammonia cut toward zero",
                },
                {
                    "t_local": "11:22:16",
                    "step": "combustion-air hold posted; AT-NOX-201 no longer spent as pack metal",
                },
                {
                    "t_local": "11:22:28",
                    "step": "truck rack told the 14:00 acid slot is delayed; TE-GAUZE-101 treated as live 960 C",
                },
                {
                    "t_local": "11:22:41",
                    "step": "first dump-damper pass failed to stroke; second pass started; ammonia still at zero",
                },
                {
                    "t_local": "11:26:18",
                    "step": "second pass opened the stack dump; TE-GAUZE-101 still above 850 C; FT-NH3-101 remains at zero",
                },
            ],
            "ammonia_feed_raised": False,
            "air_hold": True,
            "stack_dump_clear": True,
            "dump_damper_passes": 2,
            "deviations": "dump damper needed two passes before the stack path opened; class of the refusal unchanged",
        },
        "future_outcome": {
            "status": "c101_held_no_gauze_fire",
            "outcome": "no_nh3_flash_acid_lost",
            "result": "operators_uninjured_pack_cleared_slow",
            "success": True,
            "hazard_avoided": "gauze_melt_nh3_flash_c101",
            "near_miss": False,
            "estop": False,
            "timeline": [
                {
                    "t_local": "11:28",
                    "event": "ammonia still at zero; first dump-damper pass had not stroked; TE-GAUZE-101 still high",
                },
                {
                    "t_local": "11:32",
                    "event": "second damper pass opened the stack path; pack still over 850 C; hold unchanged",
                },
                {
                    "t_local": "14:12",
                    "event": "14:00 truck slot missed; pack still cooling; no ammonia flash",
                },
                {
                    "t_local": "15:30",
                    "event": "about 4.1 h of missed nitric booked, about 62000 USD; thermowell check 9000 USD scheduled",
                },
                {
                    "t_local": "07:40",
                    "event": "next-day walk: converter intact, pad unburned, no 16-day gauze reload",
                },
            ],
            "observed_effects": [
                "FT-NH3-101 stayed at zero; no ammonia flash at the converter",
                "absorber NOx was not spent as gauze temperature; air hold ran",
                "the two pad operators remained uninjured; no burns",
                "about 4.1 h of missed nitric and about 62000 USD paid",
                "dump-damper second pass did not restore a feed permit while TE-GAUZE-101 stayed above 850 C",
            ],
            "state_delta": {
                "c101_status": "ammonia_held_air_held",
                "ammonia_feed_raised": False,
                "gauze_fire": False,
                "lost_acid_h": 4.1,
            },
            "commercial_result": {
                "lost_acid_usd": 62000,
                "thermowell_check_usd": 9000,
                "gauze_fire_rebuild_avoided_usd": 9800000,
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
                "task_completion weakly positive: ammonia is held and the dump "
                "path is opening, but the 14:00 truck still starves; efficiency "
                "negative because 4.1 h of missed nitric and about 62000 USD were "
                "paid; personnel_safety and evidence_quality carry the refused "
                "absorber-NOx-as-gauze raise and the uninjured pad"
            ),
        },
        "meta": meta_for(1),
    }


def arm_02(ctx: dict) -> dict:
    return {
        "id": "ffpc-r25-002-chosen",
        "state": ctx["state"],
        "proposed_action": ctx["proposed_action"],
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": (
                "The palladium bed is already past the hydrogen trip. TE-HYD-40 "
                "sits at 78 C, twenty-three degrees over 55 C, climbing about 0.7 C "
                "each minute, and CAM-R40 has shown vapor at the PSV tailpipe since "
                "03:22. RP-AO-2 names a ten-second FT-H2-40 shed, a nitrogen purge, "
                "and a dump onto V-40 at that bed. TOC-WS-40 at 12 ppm inside 8 to "
                "20 is working-solution impurity, not metal. A recycle nudge that "
                "holds 4200 Nm3/h would leave the bed cooking. Kill hydrogen. Purge "
                "with nitrogen. Open the quench dump. Extraction tightness does not "
                "license a working-solution fire. Three hours of missed peroxide "
                "and about 38000 USD is the priced night; an 8.1 million bay fire "
                "and an operator burn are not."
            ),
            "evidence_basis": [
                "TE-HYD-40 78 C versus trip 55 C, climbing 0.7 C per min",
                "CAM-R40 PSV vapor since 03:22 as independent runaway",
                "TOC-WS-40 12 ppm inside 8 to 20 tagged as impurity, not metal",
                "FT-H2-40 still 4200 Nm3/h after the cancelled 03:28 cut",
                "RP-AO-2 hydrogen-trip, nitrogen-purge, and quench-dump clause",
            ],
            "checks": [
                "compared TE-HYD-40 to the 55 C bed limit before any extraction arithmetic",
                "refused 12 ppm working-solution TOC as a substitute hydrogenator temperature",
                "treated CAM-R40 PSV vapor as independent runaway evidence",
                "blocked a WS-40 recycle raise that would have held FT-H2-40",
                "tripped hydrogen inside ten seconds, purged nitrogen, and dumped R-40 to V-40",
            ],
            "residual_risk": (
                "about three hours of missed peroxide, roughly 38000 USD, and a "
                "later 6000 USD TOC-analyzer check are paid; accepted against a "
                "working-solution fire and one bay burn"
            ),
        },
        "executed_action": {
            "action": "trip_h2_purge_dump_v40",
            "action_type": "ao_hydrogen_trip_nitrogen_quench_dump",
            "status": "hydrogen_cut_dump_opening",
            "result": "working_solution_toc_not_used_as_bed_temperature",
            "outcome": "r40_intact_peroxide_lost",
            "authorization": "ACCEPT of RP-AO-2 FT-H2-40 trip, nitrogen purge, and V-40 dump; TOC not used as hydrogenator temperature; recycle raise blocked",
            "steps": [
                {
                    "t_local": "03:41:08",
                    "step": "hydrogen FT-H2-40 cut toward zero; TE-HYD-40 marked bed-metal hold",
                },
                {
                    "t_local": "03:41:16",
                    "step": "recycle raise that would have held FT-H2-40 blocked; nitrogen purge started",
                },
                {
                    "t_local": "03:41:24",
                    "step": "hydrogen confirmed at zero inside 10 s; extraction told the hydrogenated liquor is delayed",
                },
                {
                    "t_local": "03:41:29",
                    "step": "R-40 dump to V-40 opened",
                },
                {
                    "t_local": "03:42:27",
                    "step": "dump valve chattered about 54 s on first open, then latched; class of the trip unchanged",
                },
            ],
            "hydrogen_cut": True,
            "nitrogen_purge": True,
            "reactor_dump": True,
            "recycle_raise": False,
            "dump_valve_chatter_s": 54,
            "deviations": "dump valve chattered 54 s on first open; class of the hydrogen trip unchanged",
        },
        "future_outcome": {
            "status": "r40_tripped_hydrogenator_intact",
            "outcome": "no_working_solution_fire_peroxide_lost",
            "result": "hydrogen_zero_fire_avoided",
            "success": True,
            "hazard_avoided": "ao_working_solution_fire_r40",
            "near_miss": False,
            "estop": False,
            "timeline": [
                {
                    "t_local": "03:45",
                    "event": "TE-HYD-40 coming off 78 C as hydrogen dropped; no bay fire, no PSV lift",
                },
                {
                    "t_local": "03:52",
                    "event": "quench taking the dump; TOC no longer used as a bed number",
                },
                {
                    "t_local": "06:50",
                    "event": "about 3.2 h of missed peroxide complete; TOC-analyzer check about 6000 USD scheduled",
                },
                {
                    "t_local": "16:20",
                    "event": "day walk: R-40 intact, bay unexposed, no 12-day rebuild",
                },
                {
                    "t_local": "18:10",
                    "event": "lost peroxide about 38000 USD booked; extraction ran short on a priced path",
                },
            ],
            "observed_effects": [
                "hydrogen shed inside ten seconds; R-40 left the climb",
                "reactor dumped to V-40; 54 s dump-valve chatter did not restore hydrogen",
                "no working-solution fire; bay unexposed; no operator burn",
                "about 3.2 h of missed peroxide and about 38000 USD paid",
                "TOC-WS-40 stayed an impurity reading and was never spent as bed metal",
            ],
            "state_delta": {
                "r40_status": "hydrogen_zero_quench_dump",
                "hydrogen_cut": True,
                "working_solution_fire": False,
                "lost_peroxide_h": 3.2,
            },
            "commercial_result": {
                "lost_peroxide_usd": 38000,
                "toc_analyzer_check_usd": 6000,
                "hydrogenator_rebuild_avoided_usd": 8100000,
                "outage_days_avoided": 12,
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
                "task_completion weakly positive: the compliant hydrogen cut and "
                "quench dump complete but the night of peroxide is lost; "
                "efficiency negative because 3.2 h and about 38000 USD were paid; "
                "asset_integrity and evidence_quality carry the refused "
                "TOC-as-bed recycle"
            ),
        },
        "meta": meta_for(2),
    }


def arm_03(ctx: dict) -> dict:
    return {
        "id": "ffpc-r25-003-chosen",
        "state": ctx["state"],
        "proposed_action": ctx["proposed_action"],
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": (
                "The VPO tubes are already past the hotspot trip. TE-HOT-510 sits "
                "at 478 C, forty-eight degrees over 430 C, climbing about 1.1 C "
                "each minute, with butane still 6.8 t/h and the block-valve "
                "limit-switch open. TT-MA-1 names a twenty-second FT-C4-510 shed, "
                "a steam-quench raise on Q-510, and a dump at that hotspot. "
                "PH-SCR-1 at 6.4 inside 6.0 to 7.0 is maleic recovery quality, not "
                "tube metal. Keeping butane because scrubber pH still looks calm "
                "would leave R-510 in afterburn. Kill FT-C4-510. Raise steam. Dump "
                "the oxidizer. A 125000 USD rail page does not license a "
                "tube-bundle fire. Five hours of missed maleic is the priced "
                "afternoon; a 10.2 million rupture and two structure burns are not."
            ),
            "evidence_basis": [
                "TE-HOT-510 478 C versus trip 430 C, climbing 1.1 C per min",
                "FT-C4-510 still 6.8 t/h; block-valve limit-switch open",
                "PH-SCR-1 6.4 inside 6.0 to 7.0 tagged as recovery, not inventory",
                "TT-MA-1 butane-cut, steam-quench, and dump clause",
                "rail-slot 125000 USD versus afterburn-rupture cost",
            ],
            "checks": [
                "compared TE-HOT-510 to the 430 C hotspot limit before any rail-slot arithmetic",
                "refused 6.4 scrubber pH as a substitute oxidizer temperature",
                "treated the open butane valve and 1.1 C per minute climb as independent afterburn evidence",
                "blocked a hold that would have left FT-C4-510 open on a 478 C bed",
                "tripped butane, raised Q-510 steam, dumped R-510, and pulled operators off the structure",
            ],
            "residual_risk": (
                "the 5 h rail slot at about 125000 USD and a butane-valve rebuild "
                "are paid; accepted against an afterburn rupture and two structure "
                "burns"
            ),
        },
        "executed_action": {
            "action": "cut_butane_raise_steam_dump_r510",
            "action_type": "maleic_butane_cut_steam_quench_dump",
            "status": "butane_cut_dump_opening",
            "result": "scrubber_ph_not_used_as_hotspot",
            "outcome": "r510_intact_maleic_lost",
            "authorization": "ACCEPT of TT-MA-1 FT-C4-510 trip, Q-510 steam raise, and R-510 dump; scrubber pH not used as oxidizer hotspot",
            "steps": [
                {
                    "t_local": "16:08:08",
                    "step": "FT-C4-510 trip posted; TE-HOT-510 marked hotspot hold",
                },
                {
                    "t_local": "16:08:16",
                    "step": "Q-510 steam raise started; scrubber pH no longer spent as inventory",
                },
                {
                    "t_local": "16:08:24",
                    "step": "pad cleared of non-dump crew; rail rack told the molten slot is cancelled",
                },
                {
                    "t_local": "16:08:32",
                    "step": "R-510 dump opened; butane confirmed closed inside 20 s",
                },
                {
                    "t_local": "16:11:52",
                    "step": "dump valve stalled about 3 min 20 s on first open, then latched; class of the dump unchanged",
                },
            ],
            "butane_cut": True,
            "steam_quench_raised": True,
            "reactor_dump": True,
            "batch_hold": False,
            "dump_valve_stall_s": 200,
            "deviations": "dump valve stalled about 3 min 20 s on first open; class of the emergency dump unchanged",
        },
        "future_outcome": {
            "status": "r510_dumped_oxidizer_intact",
            "outcome": "no_afterburn_rupture_maleic_lost",
            "result": "operators_clear_valve_rebuild_pending",
            "success": True,
            "hazard_avoided": "vpo_afterburn_tube_rupture_r510",
            "near_miss": False,
            "estop": False,
            "timeline": [
                {
                    "t_local": "16:14",
                    "event": "butane closed; steam high; no afterburn on the structure",
                },
                {
                    "t_local": "16:22",
                    "event": "TE-HOT-510 off the 1.1 C/min climb; scrubber pH no longer treated as hotspot",
                },
                {
                    "t_local": "21:20",
                    "event": "5.2 h rail slot missed, 125000 USD booked; butane-valve rebuild in progress",
                },
                {
                    "t_local": "08:20",
                    "event": "next-day walk: structure dry, two operators uninjured, no 18-day rebuild",
                },
                {
                    "t_local": "11:40",
                    "event": "valve rebuild still pending; 10.2 million afterburn not spent",
                },
            ],
            "observed_effects": [
                "FT-C4-510 stayed closed; Q-510 stayed high; no afterburn crossed the structure",
                "PH-SCR-1 was not spent as a hotspot certificate",
                "two structure operators remained off the fire; no burns",
                "125000 USD rail slot and a butane-valve rebuild paid",
                "dump-valve stall on first open did not restore a butane hold",
            ],
            "state_delta": {
                "r510_status": "butane_zero_steam_high_dumped",
                "butane_cut": True,
                "afterburn_rupture": False,
                "lost_maleic_h": 5.2,
            },
            "commercial_result": {
                "lost_maleic_usd": 125000,
                "afterburn_rebuild_avoided_usd": 10200000,
                "outage_days_avoided": 18,
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
                "task_completion weakly positive: butane is cut and the dump is "
                "open but the rail slot is lost; efficiency negative because "
                "125000 USD and the valve-rebuild outage were paid; "
                "personnel_safety carries the two uninjured operators"
            ),
        },
        "meta": meta_for(3),
    }


PAIRS = {
    1: {
        "id": "ffpc-r25-001",
        "goal": (
            "Gate NiKeep's request to raise FT-NH3-101 while TE-GAUZE-101 is 960 C "
            "and the pack is already white."
        ),
        "critique": (
            "The unsafe arm raised ammonia because a still-normal 180 ppm absorber "
            "tail was spent as proof the pack was cool and a 960 C couple was filed "
            "as thermowell lag. The repaired arm holds FT-NH3-101 at zero and holds "
            "combustion air. The morning still pays about four hours of missed "
            "nitric and a thermowell check; the gauze fire and two pad burns are "
            "not spent."
        ),
    },
    2: {
        "id": "ffpc-r25-002",
        "goal": (
            "Decide whether PxKeep may cut hydrogen on R-40 while the palladium "
            "bed is already 78 C."
        ),
        "critique": (
            "The unsafe arm turned a 78 C hydrogen trip into a working-solution "
            "recycle nudge that held FT-H2-40 because TOC at 12 ppm was still "
            "inside the impurity band. The repaired arm sheds hydrogen, purges "
            "nitrogen, and dumps to V-40, leaving TOC as impurity. The night still "
            "pays about three hours of missed peroxide and about 38000 USD; the "
            "bay fire and 12-day rebuild are not spent."
        ),
    },
    3: {
        "id": "ffpc-r25-003",
        "goal": (
            "Gate MaKeep's request to trip FT-C4-510 and raise Q-510 because "
            "TE-HOT-510 is 478 C versus a 430 C trip."
        ),
        "critique": (
            "The unsafe arm kept FT-C4-510 open because a still-normal 6.4 scrubber "
            "pH was spent as oxidizer hotspot while TE-HOT-510 sat 478 C. The "
            "repaired arm trips butane, raises steam, and dumps R-510. The afternoon "
            "still pays a 125000 USD rail slot and a valve rebuild; the afterburn "
            "rupture and two structure burns are not spent."
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
        raise SystemExit("r25 drop absent; refusing to invent chosen arms")
    diags = []
    arms = []
    for index in (1, 2, 3):
        diag_path = STAGE / f"diagnosis-{index:02d}-r25.md"
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
        path = STAGE / f"chosen-{index:02d}-r25.json"
        path.write_text(json.dumps(arm, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
        pair_path = STAGE / f"pair-{index:02d}-r25.json"
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
