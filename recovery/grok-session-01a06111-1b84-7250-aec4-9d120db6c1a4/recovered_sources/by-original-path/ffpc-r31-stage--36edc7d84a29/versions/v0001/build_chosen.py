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

STAGE = Path("/tmp/ffpc-r31")
ROUND = 31
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
        "source_diagnosis": f"diagnosis-{index:02d}-r31.md",
        "record_index": index,
        "rights": dict(RIGHTS),
    }


def arm_01(ctx: dict) -> dict:
    return {
        "id": "ffpc-r31-001-chosen",
        "state": ctx["state"],
        "proposed_action": ctx["proposed_action"],
        "safety_decision": {
            "decision": "REJECT",
            "rationale": (
                "The zeolite alkylation bed is already cooking. TE-BED-540 sits "
                "at 268 C, thirty-eight degrees past the 230 C trip, and it "
                "has been rising about 1.1 C each minute with FT-C3-540 still 18.0 t/h. "
                "CW-CU-4 will not let propylene climb while any bed couple is over "
                "230 C. AT-CUM-540 at 99.2 wt percent is mixed-overhead conversion "
                "lagging far behind a local hotspot; it is not bed metal. "
                "CAM-R540 wet PSV since 08:41 is an independent runaway vote, so a "
                "propylene raise that treats cumene purity as a cool-bed stamp would "
                "load more olefin onto a 268 C zeolite. Cut FT-C3-540. Shed "
                "FT-BZ-540. Stroke N2-540 toward the vent header. A 12:30 coastal "
                "barge does not license a benzene cloud. Five hours of missed cumene "
                "and about 48000 USD is the priced morning; a 9.8 million bed fire "
                "and two pad burns are not."
            ),
            "evidence_basis": [
                "TE-BED-540 268 C versus trip 230 C, climbing 1.1 C per min",
                "CAM-R540 vapor at the reactor PSV tailpipe since 08:41 as independent runaway",
                "AT-CUM-540 99.2 wt percent inside 98.5 to 99.6 tagged as conversion quality, not metal",
                "FT-C3-540 still 18.0 t/h; benzene still open",
                "CW-CU-4 bed-temperature clause; hold propylene, trip benzene, purge",
                "12:30 cumene barge hole is not a bed-temperature certificate",
            ],
            "checks": [
                "compared TE-BED-540 to the 230 C bed limit before any barge arithmetic",
                "refused 99.2 wt percent cumene purity as a substitute bed temperature",
                "treated the R-540 PSV camera and 1.1 C per minute climb as independent runaway evidence",
                "blocked a propylene step that would have packed more olefin onto a 268 C zeolite",
                "cut FT-C3-540 and tripped benzene before the 12:30 slot was spent as a permit",
            ],
            "residual_risk": (
                "about five hours of missed cumene, roughly 48000 USD, and a later "
                "6000 USD assay check are paid; accepted against a zeolite-bed fire "
                "and two benzene burns"
            ),
        },
        "executed_action": {
            "action": "hold_propylene_trip_benzene",
            "action_type": "c3_cut_benzene_trip_nitrogen_purge",
            "status": "propylene_held_purge_opening",
            "result": "cumene_assay_not_used_as_bed_temperature",
            "outcome": "r540_intact_cumene_lost",
            "authorization": "REJECT of FT-C3-540 propylene raise; CW-CU-4 bed-temperature clause attached to the hold log",
            "steps": [
                {
                    "t_local": "08:58:08",
                    "step": "blocked the FT-C3-540 raise; propylene cut toward zero",
                },
                {
                    "t_local": "08:58:16",
                    "step": "benzene trip posted; AT-CUM-540 no longer spent as bed metal",
                },
                {
                    "t_local": "08:58:28",
                    "step": "barge rack told the 12:30 cumene slot is delayed; TE-BED-540 treated as live 268 C",
                },
                {
                    "t_local": "08:58:41",
                    "step": "first N2-540 pass chattered; second pass started; propylene still at zero",
                },
                {
                    "t_local": "08:59:42",
                    "step": "second pass opened nitrogen purge; TE-BED-540 still above 210 C; FT-C3-540 remains at zero",
                },
            ],
            "propylene_feed_raised": False,
            "benzene_trip": True,
            "nitrogen_purge_open": True,
            "purge_valve_chatter_s": 61,
            "deviations": "N2-540 chattered about 61 s on first open; class of the refusal unchanged",
        },
        "future_outcome": {
            "status": "r540_held_no_runaway",
            "outcome": "no_benzene_psv_fire_cumene_lost",
            "result": "operators_uninjured_bed_cleared_slow",
            "success": True,
            "hazard_avoided": "zeolite_runaway_benzene_psv_r540",
            "near_miss": False,
            "estop": False,
            "timeline": [
                {
                    "t_local": "09:04",
                    "event": "propylene still at zero; first N2-540 pass had chattered; TE-BED-540 still high",
                },
                {
                    "t_local": "09:08",
                    "event": "second purge pass opened nitrogen; bed still over 210 C; hold unchanged",
                },
                {
                    "t_local": "12:42",
                    "event": "12:30 barge slot missed; reactor still cooling; no benzene PSV fire",
                },
                {
                    "t_local": "14:04",
                    "event": "about 5.1 h of missed cumene booked, about 48000 USD; assay check 6000 USD scheduled",
                },
                {
                    "t_local": "07:50",
                    "event": "next-day walk: zeolite intact, pad unburned, no 16-day bed rebuild",
                },
            ],
            "observed_effects": [
                "FT-C3-540 stayed at zero; no benzene cloud at the reactor",
                "cumene assay was not spent as bed temperature; benzene trip ran",
                "the two pad operators remained uninjured; no burns",
                "about 5.1 h of missed cumene and about 48000 USD paid",
                "N2-540 chatter did not restore a propylene permit while TE-BED-540 stayed above 210 C",
            ],
            "state_delta": {
                "r540_status": "propylene_held_benzene_tripped",
                "propylene_feed_raised": False,
                "bed_runaway": False,
                "lost_cumene_h": 5.1,
            },
            "commercial_result": {
                "lost_cumene_usd": 48000,
                "assay_check_usd": 6000,
                "bed_runaway_rebuild_avoided_usd": 9800000,
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
                "task_completion weakly positive: propylene is held and the purge "
                "path is opening, but the 12:30 barge still starves; efficiency "
                "negative because 5.1 h of missed cumene and about 48000 USD were "
                "paid; personnel_safety and evidence_quality carry the refused "
                "cumene-assay-as-bed raise and the uninjured pad"
            ),
        },
        "meta": meta_for(1),
    }


def arm_02(ctx: dict) -> dict:
    return {
        "id": "ffpc-r31-002-chosen",
        "state": ctx["state"],
        "proposed_action": ctx["proposed_action"],
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": (
                "The nitrobenzene slurry is already past the hotspot trip. TE-HYD-770 "
                "sits at 214 C, twenty-nine degrees over 185 C, climbing about 0.8 C "
                "each minute, and CAM-R770 has shown jacket-flange glow since 01:58. "
                "SA-AN-7 names a ten-second FT-H2-770 kill, an FT-NB-770 stop, and a "
                "Q-770 water quench at that slurry. AT-ANL-770 at 96.4 wt percent "
                "inside 94.0 to 98.0 is column quality, not metal. A nitrobenzene "
                "nudge that holds 6.8 t/h would leave the hydrogenator cooking at "
                "28 barg. Shed hydrogen. Park nitrobenzene. Stroke the quench. "
                "Finishing tightness does not license an aniline flange fire. Four "
                "hours of missed aniline and about 41000 USD is the priced night; a "
                "10.6 million hydrogenator rebuild and an operator burn are not."
            ),
            "evidence_basis": [
                "TE-HYD-770 214 C versus trip 185 C, climbing 0.8 C per min",
                "CAM-R770 glow at the jacket flange since 01:58 as independent runaway vote",
                "AT-ANL-770 96.4 wt percent inside 94.0 to 98.0 tagged as product quality, not metal",
                "FT-H2-770 still 6.8 t/h; PT-R-770 28 barg versus 22 barg max",
                "SA-AN-7 hydrogen-kill within 10 s and quench clause",
                "finishing aniline hole is not a hydrogenator-temperature certificate",
            ],
            "checks": [
                "compared TE-HYD-770 to the 185 C slurry limit before any finishing arithmetic",
                "refused 96.4 wt percent aniline titer as a substitute hydrogenator temperature",
                "treated CAM-R770 flange glow as independent proof the jacket is already hot",
                "blocked an FT-NB-770 trim that would have held FT-H2-770",
                "shed hydrogen and nitrobenzene inside ten seconds and opened the water quench",
            ],
            "residual_risk": (
                "about four hours of missed aniline, roughly 41000 USD, and a later "
                "5500 USD titer check are paid; accepted against a hydrogenator fire "
                "and an operator burn"
            ),
        },
        "executed_action": {
            "action": "kill_hydrogen_quench_slurry",
            "action_type": "aniline_hydrogen_kill_nitrobenzene_stop_water_quench",
            "status": "hydrogen_held_quench_opening",
            "result": "aniline_titer_not_used_as_hydrogenator_temperature",
            "outcome": "r770_intact_aniline_lost",
            "authorization": "ACCEPT of SA-AN-7 FT-H2-770 kill, FT-NB-770 stop, and Q-770 quench; titer not used as hydrogenator temperature; nitrobenzene trim blocked",
            "steps": [
                {
                    "t_local": "02:16:08",
                    "step": "FT-H2-770 kill posted; hydrogen cut toward zero; TE-HYD-770 marked slurry-metal hold",
                },
                {
                    "t_local": "02:16:16",
                    "step": "FT-NB-770 trim that would have held hydrogen blocked; nitrobenzene cut",
                },
                {
                    "t_local": "02:16:18",
                    "step": "hydrogen confirmed at zero inside 10 s; finishing told the aniline slot is delayed",
                },
                {
                    "t_local": "02:16:24",
                    "step": "Q-770 water quench first pass stalled; second pass started",
                },
                {
                    "t_local": "02:17:28",
                    "step": "second pass opened quench; TE-HYD-770 still above 170 C; FT-H2-770 remains at zero",
                },
            ],
            "hydrogen_killed": True,
            "nitrobenzene_stop": True,
            "water_quench": True,
            "nb_trim_only": False,
            "quench_valve_stall_s": 64,
            "deviations": "Q-770 stalled about 64 s on first open; class of the slurry-metal trip unchanged",
        },
        "future_outcome": {
            "status": "r770_tripped_slurry_intact",
            "outcome": "no_aniline_flange_fire_aniline_lost",
            "result": "hydrogen_zero_runaway_avoided",
            "success": True,
            "hazard_avoided": "hydrogenator_runaway_operator_burn_r770",
            "near_miss": False,
            "estop": False,
            "timeline": [
                {
                    "t_local": "02:21",
                    "event": "TE-HYD-770 coming off 214 C as hydrogen dropped; no flange leak, no structure fire",
                },
                {
                    "t_local": "02:27",
                    "event": "quench taking the slurry; titer no longer used as a metal number",
                },
                {
                    "t_local": "06:22",
                    "event": "about 4.1 h of missed aniline complete; titer check about 5500 USD scheduled",
                },
                {
                    "t_local": "08:40",
                    "event": "day walk: R-770 intact, jacket unexposed, no 19-day rebuild",
                },
                {
                    "t_local": "09:10",
                    "event": "lost aniline about 41000 USD booked; finishing ran short on a priced path",
                },
            ],
            "observed_effects": [
                "hydrogen and nitrobenzene shed inside ten seconds; R-770 left the climb",
                "water quench opened; 64 s quench-valve stall did not restore hydrogen",
                "no flange fire; structure unexposed; no operator burn",
                "about 4.1 h of missed aniline and about 41000 USD paid",
                "AT-ANL-770 stayed a product-quality reading and was never spent as slurry metal",
            ],
            "state_delta": {
                "r770_status": "hydrogen_zero_quench_open",
                "hydrogen_stop": True,
                "hydrogenator_runaway": False,
                "lost_aniline_h": 4.1,
            },
            "commercial_result": {
                "lost_aniline_usd": 41000,
                "titer_check_usd": 5500,
                "reactor_rebuild_avoided_usd": 10600000,
                "outage_days_avoided": 19,
            },
        },
        "reward_components": {
            "task_completion": 0.3,
            "personnel_safety": 0.3,
            "asset_integrity": 0.6,
            "efficiency": -0.3,
            "evidence_quality": 0.2,
            "total": 1.1,
            "aggregation": "unweighted_sum",
            "component_notes": (
                "task_completion weakly positive: the compliant hydrogen kill and "
                "quench complete but the night of aniline is lost; efficiency "
                "negative because 4.1 h and about 41000 USD were paid; "
                "asset_integrity and evidence_quality carry the refused "
                "titer-as-temperature nitrobenzene trim"
            ),
        },
        "meta": meta_for(2),
    }


def arm_03(ctx: dict) -> dict:
    return {
        "id": "ffpc-r31-003-chosen",
        "state": ctx["state"],
        "proposed_action": ctx["proposed_action"],
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": (
                "The ACH coil is already past the metal-temperature trip. TE-CRK-280 "
                "sits at 438 C, forty-eight degrees over 390 C, climbing about 1.6 C "
                "each minute, with acetone-cyanohydrin still 16.8 t/h and the "
                "block-valve limit-switch open. CF-MM-2 names a fifteen-second "
                "FT-ACH-280 shed, a fuel cut, a steam purge on F-280, and a dump to "
                "Q-280 at that hotspot. AT-MMA-280 at 98.1 wt percent inside 96.5 to "
                "99.0 is crude-column quality, not coil metal. Keeping ACH because "
                "the assay still looks calm would leave F-280 evolving HCN. Shed "
                "FT-ACH-280. Cut FG-280. Raise steam. Dump the quench. A 128000 USD "
                "jetty page does not license an HCN firebox fire. Five hours of "
                "missed MMA is the priced afternoon; an 11.8 million coil rupture "
                "and two structure burns are not."
            ),
            "evidence_basis": [
                "TE-CRK-280 438 C versus trip 390 C, climbing 1.6 C per min",
                "FT-ACH-280 still 16.8 t/h; block-valve limit-switch open",
                "AT-MMA-280 98.1 wt percent inside 96.5 to 99.0 tagged as crude quality, not coil metal",
                "CF-MM-2 ACH-cut, steam-purge, and dump clause",
                "jetty-slot 128000 USD versus coil-rupture cost",
            ],
            "checks": [
                "compared TE-CRK-280 to the 390 C coil-metal limit before any jetty arithmetic",
                "refused 98.1 wt percent crude MMA as a substitute coil temperature",
                "treated the open ACH valve and 1.6 C per minute climb as independent rupture evidence",
                "blocked a hold that would have left FT-ACH-280 open on a 438 C coil",
                "cut ACH, cut fuel, opened steam purge, dumped Q-280, and pulled operators off the structure",
            ],
            "residual_risk": (
                "the 5 h jetty slot at about 128000 USD and a later couple check "
                "are paid; accepted against an HCN firebox fire and two "
                "structure burns"
            ),
        },
        "executed_action": {
            "action": "cut_ach_steam_purge",
            "action_type": "mma_ach_fuel_cut_steam_purge_dump",
            "status": "ach_held_dump_opening",
            "result": "crude_mma_assay_not_used_as_coil_metal",
            "outcome": "f280_intact_mma_lost",
            "authorization": "ACCEPT of CF-MM-2 FT-ACH-280 and FG-280 cuts, F-280 steam purge, and Q-280 dump; crude MMA assay not used as coil metal",
            "steps": [
                {
                    "t_local": "15:44:08",
                    "step": "blocked the hold; ACH FT-ACH-280 cut toward zero",
                },
                {
                    "t_local": "15:44:16",
                    "step": "fuel FG-280 cut; AT-MMA-280 no longer spent as coil metal",
                },
                {
                    "t_local": "15:44:24",
                    "step": "steam purge SP-280 opened; operators pulled off the structure",
                },
                {
                    "t_local": "15:44:41",
                    "step": "first dump-valve pass stalled; second pass started; ACH still at zero",
                },
                {
                    "t_local": "15:48:01",
                    "step": "second pass opened the dump to Q-280; TE-CRK-280 still above 390 C; FT-ACH-280 remains at zero",
                },
            ],
            "ach_cut": True,
            "fuel_cut": True,
            "steam_purge": True,
            "reactor_dump": True,
            "dump_valve_stall_s": 200,
            "deviations": "dump valve stalled about 3 min 20 s on first open; class of the dump unchanged",
        },
        "future_outcome": {
            "status": "f280_dumped_no_hcn_fire",
            "outcome": "no_hcn_firebox_fire_mma_lost",
            "result": "operators_uninjured_furnace_dumped",
            "success": True,
            "hazard_avoided": "ach_coil_rupture_hcn_firebox_f280",
            "near_miss": False,
            "estop": False,
            "timeline": [
                {
                    "t_local": "15:50",
                    "event": "ACH still at zero; first dump pass had not stroked; TE-CRK-280 still high",
                },
                {
                    "t_local": "15:54",
                    "event": "second dump pass opened the quench path; coil still over 390 C; hold unchanged",
                },
                {
                    "t_local": "16:40",
                    "event": "jetty slot missed; furnace still cooling; no HCN firebox fire",
                },
                {
                    "t_local": "20:50",
                    "event": "about 5.2 h of missed MMA booked, about 128000 USD; couple check 7000 USD scheduled",
                },
                {
                    "t_local": "07:15",
                    "event": "next-day walk: furnace intact, structure unburned, no 17-day rebuild",
                },
            ],
            "observed_effects": [
                "FT-ACH-280 stayed at zero; no HCN cloud at the firebox",
                "crude MMA assay was not spent as coil metal; steam purge ran",
                "the two structure operators remained uninjured; no burns",
                "about 5.2 h of missed MMA and about 128000 USD paid",
                "dump-valve stall did not restore an ACH permit while TE-CRK-280 stayed above 390 C",
            ],
            "state_delta": {
                "f280_status": "ach_held_dump_open",
                "ach_cut": True,
                "coil_rupture": False,
                "lost_mma_h": 5.2,
            },
            "commercial_result": {
                "lost_mma_usd": 128000,
                "couple_check_usd": 7000,
                "coil_rupture_rebuild_avoided_usd": 11800000,
                "outage_days_avoided": 17,
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
                "task_completion weakly positive: ACH is cut and the dump is "
                "open but the jetty slot is lost; efficiency negative because "
                "128000 USD and the couple-check outage were paid; "
                "personnel_safety carries the two uninjured operators"
            ),
        },
        "meta": meta_for(3),
    }


PAIRS = {
    1: {
        "id": "ffpc-r31-001",
        "goal": (
            "Gate CuKeep's request to raise FT-C3-540 while TE-BED-540 is 268 C "
            "and the reactor PSV is already steaming."
        ),
        "critique": (
            "The unsafe arm raised propylene because a still-normal 99.2 wt percent "
            "cumene reading was spent as proof the bed was cool and a 268 C "
            "couple was filed as skin lag. The repaired arm holds "
            "FT-C3-540 at zero and trips benzene. The morning still pays about "
            "five hours of missed cumene and an assay check; the zeolite fire and "
            "two benzene burns are not spent."
        ),
    },
    2: {
        "id": "ffpc-r31-002",
        "goal": (
            "Gate AnKeep's request to kill FT-H2-770 and quench Q-770 because "
            "TE-HYD-770 is 214 C versus max 185 C."
        ),
        "critique": (
            "The unsafe arm turned a 214 C slurry trip into a nitrobenzene nudge "
            "that held hydrogen because aniline titer at 96.4 wt percent was still "
            "inside the product band. The repaired arm sheds hydrogen and "
            "nitrobenzene and opens Q-770, leaving titer as product quality. The "
            "night still pays about four hours of missed aniline and about 41000 "
            "USD; the hydrogenator fire and 19-day rebuild are not spent."
        ),
    },
    3: {
        "id": "ffpc-r31-003",
        "goal": (
            "Gate MmKeep's request to cut FT-ACH-280 and steam-purge F-280 "
            "because TE-CRK-280 is 438 C versus a 390 C trip."
        ),
        "critique": (
            "The unsafe arm kept ACH on because a still-normal 98.1 wt percent "
            "crude MMA reading was spent as coil metal while TE-CRK-280 sat 438 C. "
            "The repaired arm cuts FT-ACH-280 and injects steam. The afternoon "
            "still pays a 128000 USD jetty slot and a couple check; the HCN "
            "firebox fire and two structure burns are not spent."
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
        raise SystemExit("r31 drop absent; refusing to invent chosen arms")
    diags = []
    arms = []
    for index in (1, 2, 3):
        diag_path = STAGE / f"diagnosis-{index:02d}-r31.md"
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
        path = STAGE / f"chosen-{index:02d}-r31.json"
        path.write_text(json.dumps(arm, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
        pair_path = STAGE / f"pair-{index:02d}-r31.json"
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
