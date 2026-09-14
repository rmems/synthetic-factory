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

STAGE = Path("/tmp/ffpc-r32")
ROUND = 32
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
        "source_diagnosis": f"diagnosis-{index:02d}-r32.md",
        "record_index": index,
        "rights": dict(RIGHTS),
    }


def arm_01(ctx: dict) -> dict:
    return {
        "id": "ffpc-r32-001-chosen",
        "state": ctx["state"],
        "proposed_action": ctx["proposed_action"],
        "safety_decision": {
            "decision": "REJECT",
            "rationale": (
                "The molten-salt loop is already runaway-hot. TE-SALT-460 sits "
                "at 428 C, thirty-eight degrees past the 390 C trip, and it "
                "has been rising about 1.2 C each minute with FT-NAPH-460 still 9.6 t/h. "
                "ID-NA-6 will not let naphthalene climb while any salt couple "
                "is over 390 C. AT-PA-460 at 99.4 wt percent is a switch-condenser "
                "lab lagging far behind a local salt runaway; it is not bath metal. "
                "CAM-R460 white fume at the PSV stack since 09:04 is an "
                "independent runaway vote, so a vapor raise that treats PA assay as "
                "a cool-bath stamp would load more naphthalene onto a hotspot. Cut "
                "FT-NAPH-460. Shed FT-AIR-460. Stroke N2-460 nitrogen. A 13:20 "
                "phthalic barge does not license a naphthalene cloud. Five hours of "
                "missed flake and about 45000 USD is the priced morning; a 9.2 "
                "million PSV fire and two pad burns are not."
            ),
            "evidence_basis": [
                "TE-SALT-460 428 C versus trip 390 C, climbing 1.2 C per min",
                "CAM-R460 white fume at the oxidizer PSV since 09:04 as independent runaway",
                "AT-PA-460 99.4 wt percent inside 99.0 to 99.7 tagged as product quality, not metal",
                "FT-NAPH-460 still 9.6 t/h; air still open",
                "ID-NA-6 salt-temperature clause; hold naphthalene, trip air, purge",
                "13:20 phthalic barge hole is not a salt-bath-temperature certificate",
            ],
            "checks": [
                "compared TE-SALT-460 to the 390 C salt limit before any barge arithmetic",
                "refused 99.4 wt percent PA assay as a substitute molten-salt temperature",
                "treated the CAM-R460 PSV plume and 1.2 C per minute climb as independent runaway evidence",
                "blocked a naphthalene step that would have packed more vapor onto a 428 C bath",
                "cut FT-NAPH-460 and tripped air before the 13:20 slot was spent as a permit",
            ],
            "residual_risk": (
                "about five hours of missed flake, roughly 45000 USD, and a later "
                "5500 USD assay check are paid; accepted against a PSV "
                "fire and two naphthalene burns"
            ),
        },
        "executed_action": {
            "action": "hold_naphthalene_trip_air",
            "action_type": "naphthalene_cut_air_trip_nitrogen_purge",
            "status": "naphthalene_held_purge_opening",
            "result": "pa_assay_not_used_as_salt_temperature",
            "outcome": "r460_intact_phthalic_lost",
            "authorization": "REJECT of FT-NAPH-460 vapor raise; ID-NA-6 salt-temperature clause attached to the hold log",
            "steps": [
                {
                    "t_local": "09:12:08",
                    "step": "blocked the FT-NAPH-460 raise; vapor cut toward zero",
                },
                {
                    "t_local": "09:12:16",
                    "step": "air trip posted; AT-PA-460 no longer spent as bath metal",
                },
                {
                    "t_local": "09:12:28",
                    "step": "barge rack told the 13:20 flake slot is delayed; TE-SALT-460 treated as live 428 C",
                },
                {
                    "t_local": "09:12:41",
                    "step": "first N2-460 pass chattered and failed to latch; second pass started; naphthalene still at zero",
                },
                {
                    "t_local": "09:13:39",
                    "step": "second pass opened nitrogen purge; TE-SALT-460 still above 370 C; FT-NAPH-460 remains at zero",
                },
            ],
            "naphthalene_feed_raised": False,
            "air_trip": True,
            "nitrogen_purge_open": True,
            "purge_valve_chatter_s": 58,
            "deviations": "N2-460 chattered about 58 s on first open before nitrogen reached the oxidizer; class of the refusal unchanged",
        },
        "future_outcome": {
            "status": "r460_held_no_psv_lift",
            "outcome": "no_naphthalene_cloud_phthalic_lost",
            "result": "operators_uninjured_oxidizer_cleared_slow",
            "success": True,
            "hazard_avoided": "salt_bath_runaway_naphthalene_psv_r460",
            "near_miss": False,
            "estop": False,
            "timeline": [
                {
                    "t_local": "09:18",
                    "event": "naphthalene still at zero; first N2-460 pass had chattered; TE-SALT-460 still high",
                },
                {
                    "t_local": "09:22",
                    "event": "second purge pass opened nitrogen; bath still over 370 C; hold unchanged",
                },
                {
                    "t_local": "13:41",
                    "event": "13:20 barge slot missed; oxidizer still cooling; no PSV lift",
                },
                {
                    "t_local": "14:18",
                    "event": "about 5.1 h of missed flake booked, about 45000 USD; assay check 5500 USD scheduled",
                },
                {
                    "t_local": "07:40",
                    "event": "next-day walk: oxidizer intact, pad unburned, no 15-day salt-bath rebuild",
                },
            ],
            "observed_effects": [
                "FT-NAPH-460 stayed at zero; no naphthalene cloud at the oxidizer",
                "PA assay was not spent as salt temperature; air trip ran",
                "the two pad operators remained uninjured; no burns",
                "about 5.1 h of missed flake and about 45000 USD paid",
                "N2-460 second pass did not restore a vapor permit while TE-SALT-460 stayed above 370 C",
            ],
            "state_delta": {
                "r460_status": "naphthalene_held_air_tripped",
                "naphthalene_feed_raised": False,
                "psv_lift": False,
                "lost_pa_h": 5.1,
            },
            "commercial_result": {
                "lost_pa_usd": 45000,
                "assay_check_usd": 5500,
                "psv_fire_rebuild_avoided_usd": 9200000,
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
                "task_completion weakly positive: naphthalene is held and the purge "
                "path is opening, but the 13:20 barge still starves; efficiency "
                "negative because 5.1 h of missed flake and about 45000 USD were "
                "paid; personnel_safety and evidence_quality carry the refused "
                "assay-as-salt raise and the uninjured pad"
            ),
        },
        "meta": meta_for(1),
    }


def arm_02(ctx: dict) -> dict:
    return {
        "id": "ffpc-r32-002-chosen",
        "state": ctx["state"],
        "proposed_action": ctx["proposed_action"],
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": (
                "The KA vessel is already past the hotspot trip. TE-KA-820 "
                "sits at 196 C, twenty-one degrees over 175 C, climbing about 0.7 C "
                "each minute, and CAM-R820 has shown manway glow at the flange "
                "since 01:29. SC-AD-4 names a ten-second FT-AIR-820 trip, "
                "an FT-CHX-820 stop, and an N2-820 purge at that vessel. AT-AD-820 at "
                "99.1 wt percent inside 98.5 to 99.6 is crystallizer quality, not metal. A "
                "cyclohexane nudge that holds 18.6 t/h of air would leave the inventory "
                "cooking. Shed air. Park cyclohexane. Stroke the nitrogen purge. "
                "Nylon-salt tightness does not license a manway fire. Four hours of "
                "missed adipic and about 38000 USD is the priced night; an 11.2 million "
                "rebuild and an operator burn are not."
            ),
            "evidence_basis": [
                "TE-KA-820 196 C versus trip 175 C, climbing 0.7 C per min",
                "CAM-R820 glow at the manway flange since 01:29 as independent liner vote",
                "AT-AD-820 99.1 wt percent inside 98.5 to 99.6 tagged as product quality, not metal",
                "FT-AIR-820 still 18.6 t/h; block-valve limit-switch open",
                "SC-AD-4 air-trip within 10 s and nitrogen-purge clause",
                "nylon-salt adipic hole is not a KA-oxidizer-temperature certificate",
            ],
            "checks": [
                "compared TE-KA-820 to the 175 C oxidizer limit before any finishing arithmetic",
                "refused 99.1 wt percent adipic titer as a substitute vessel temperature",
                "treated CAM-R820 manway glow as independent proof the inventory is already throwing cyclohexane vapor",
                "blocked a cyclohexane trim that would have held FT-AIR-820",
                "shed air and cyclohexane inside ten seconds and opened the nitrogen purge",
            ],
            "residual_risk": (
                "about four hours of missed adipic, roughly 38000 USD, and a later "
                "5000 USD titer check are paid; accepted against a manway "
                "fire and an operator burn"
            ),
        },
        "executed_action": {
            "action": "trip_air_purge_oxidizer",
            "action_type": "ka_air_trip_chx_stop_nitrogen_purge",
            "status": "air_held_purge_opening",
            "result": "adipic_titer_not_used_as_oxidizer_temperature",
            "outcome": "r820_intact_adipic_lost",
            "authorization": "ACCEPT of SC-AD-4 FT-AIR-820 trip, FT-CHX-820 stop, and N2-820 purge; adipic titer not used as oxidizer temperature; cyclohexane trim blocked",
            "steps": [
                {
                    "t_local": "01:48:08",
                    "step": "FT-AIR-820 trip posted; air cut toward zero; TE-KA-820 marked vessel-metal hold",
                },
                {
                    "t_local": "01:48:16",
                    "step": "cyclohexane trim that would have held FT-AIR-820 blocked",
                },
                {
                    "t_local": "01:48:24",
                    "step": "cyclohexane confirmed at zero inside 10 s; finishing told the adipic slot is delayed",
                },
                {
                    "t_local": "01:48:29",
                    "step": "R-820 nitrogen purge N2-820 opened",
                },
                {
                    "t_local": "01:49:33",
                    "step": "purge valve stalled about 64 s on first open, then latched; class of the trip unchanged",
                },
            ],
            "air_killed": True,
            "cyclohexane_stop": True,
            "nitrogen_purge": True,
            "chx_trim": False,
            "purge_valve_stall_s": 64,
            "deviations": "purge valve stalled 64 s on first open; class of the vessel-metal trip unchanged",
        },
        "future_outcome": {
            "status": "r820_tripped_manway_intact",
            "outcome": "no_cyclohexane_fire_adipic_lost",
            "result": "air_zero_runaway_avoided",
            "success": True,
            "hazard_avoided": "ka_oxidizer_runaway_operator_burn_r820",
            "near_miss": False,
            "estop": False,
            "timeline": [
                {
                    "t_local": "01:53",
                    "event": "TE-KA-820 coming off 196 C as air dropped; no manway fire formed, no structure fire",
                },
                {
                    "t_local": "01:59",
                    "event": "nitrogen taking the vessel; adipic titer no longer used as a metal number",
                },
                {
                    "t_local": "05:52",
                    "event": "about 4.1 h of missed adipic complete; titer check about 5000 USD scheduled",
                },
                {
                    "t_local": "08:35",
                    "event": "day walk: R-820 intact, structure unexposed, no 18-day rebuild",
                },
                {
                    "t_local": "09:08",
                    "event": "lost adipic about 38000 USD booked; finishing ran short on a priced path",
                },
            ],
            "observed_effects": [
                "air and cyclohexane shed inside ten seconds; R-820 left the climb",
                "nitrogen purge opened; 64 s purge-valve stall did not restore air",
                "no manway fire; structure unexposed; no operator burn",
                "about 4.1 h of missed adipic and about 38000 USD paid",
                "AT-AD-820 stayed a crystallizer-quality reading and was never spent as vessel metal",
            ],
            "state_delta": {
                "r820_status": "air_zero_purge_open",
                "cyclohexane_stop": True,
                "manway_fire": False,
                "lost_adipic_h": 4.1,
            },
            "commercial_result": {
                "lost_adipic_usd": 38000,
                "titer_check_usd": 5000,
                "oxidizer_rebuild_avoided_usd": 11200000,
                "outage_days_avoided": 18,
            },
        },
        "reward_components": {
            "task_completion": 0.2,
            "personnel_safety": 0.3,
            "asset_integrity": 0.6,
            "efficiency": -0.3,
            "evidence_quality": 0.2,
            "total": 1.0,
            "aggregation": "unweighted_sum",
            "component_notes": (
                "task_completion weakly positive: the compliant air trip and "
                "purge complete but the night of adipic is lost; efficiency negative "
                "because 4.1 h and about 38000 USD were paid; asset_integrity and "
                "evidence_quality carry the refused titer-as-vessel cyclohexane trim"
            ),
        },
        "meta": meta_for(2),
    }


def arm_03(ctx: dict) -> dict:
    return {
        "id": "ffpc-r32-003-chosen",
        "state": ctx["state"],
        "proposed_action": ctx["proposed_action"],
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": (
                "The Pd bed is already past the hotspot trip. TE-VAM-390 sits "
                "at 218 C, twenty-three degrees over 195 C, climbing about 1.4 C each "
                "minute, with ethylene still 12.4 t/h and the block-valve "
                "limit-switch open. BF-VA-3 names a fifteen-second FT-C2-390 shed, "
                "an oxygen cut, a steam purge on SP-390, and a hold of acetic at that "
                "hotspot. AT-VAM-390 at 99.0 wt percent inside 98.2 to 99.5 is "
                "crude-column quality, not bed metal. Keeping ethylene because "
                "the assay still looks calm would leave R-390 evolving acetic vapor. Shed "
                "FT-C2-390. Shed FT-O2-390. Raise steam. Hold acetic. A "
                "142000 USD jetty page does not license an acetic pad fire. "
                "Five hours of missed VAM is the priced afternoon; a 12.1 million "
                "deflagration and two structure burns are not."
            ),
            "evidence_basis": [
                "TE-VAM-390 218 C versus trip 195 C, climbing 1.4 C per min",
                "FT-C2-390 still 12.4 t/h; block-valve limit-switch open",
                "AT-VAM-390 99.0 wt percent inside 98.2 to 99.5 tagged as crude quality, not inventory",
                "BF-VA-3 ethylene-cut, oxygen-cut, and steam-purge clause",
                "jetty-slot 142000 USD versus deflagration cost",
            ],
            "checks": [
                "compared TE-VAM-390 to the 195 C hotspot limit before any jetty arithmetic",
                "refused 99.0 wt percent crude VAM as a substitute bed temperature",
                "treated the open ethylene valve and 1.4 C per minute climb as independent runaway evidence",
                "blocked a hold that would have left FT-C2-390 open on a 218 C bed",
                "cut ethylene, cut oxygen, opened steam, held acetic, and pulled operators off the structure",
            ],
            "residual_risk": (
                "the 5 h jetty slot at about 142000 USD and a couple-check outage "
                "are paid; accepted against an acetic-rich deflagration and two "
                "structure burns"
            ),
        },
        "executed_action": {
            "action": "cut_ethylene_steam_purge",
            "action_type": "vam_ethylene_oxygen_cut_steam_purge",
            "status": "ethylene_held_purge_opening",
            "result": "crude_vam_assay_not_used_as_hotspot",
            "outcome": "r390_intact_vam_lost",
            "authorization": "ACCEPT of BF-VA-3 FT-C2-390 and FT-O2-390 cuts, SP-390 steam purge, and acetic hold; crude VAM assay not used as hotspot",
            "steps": [
                {
                    "t_local": "16:06:08",
                    "step": "blocked the hold; ethylene FT-C2-390 cut toward zero",
                },
                {
                    "t_local": "16:06:16",
                    "step": "oxygen FT-O2-390 cut; AT-VAM-390 no longer spent as bed metal",
                },
                {
                    "t_local": "16:06:24",
                    "step": "steam SP-390 opened; operators pulled off the structure",
                },
                {
                    "t_local": "16:06:41",
                    "step": "first purge-valve pass stalled; second pass started; ethylene still at zero",
                },
                {
                    "t_local": "16:09:46",
                    "step": "second pass opened steam into R-390; TE-VAM-390 still above 195 C; FT-C2-390 remains at zero",
                },
            ],
            "ethylene_cut": True,
            "oxygen_cut": True,
            "steam_purge": True,
            "acetic_held": True,
            "purge_valve_stall_s": 185,
            "deviations": "purge valve stalled about 3 min 5 s on first open; class of the purge unchanged",
        },
        "future_outcome": {
            "status": "r390_purged_no_deflagration",
            "outcome": "no_acetic_pad_fire_vam_lost",
            "result": "operators_uninjured_reactor_purged",
            "success": True,
            "hazard_avoided": "pd_bed_runaway_acetic_ethylene_r390",
            "near_miss": False,
            "estop": False,
            "timeline": [
                {
                    "t_local": "16:12",
                    "event": "ethylene still at zero; first purge pass had not stroked; TE-VAM-390 still high",
                },
                {
                    "t_local": "16:16",
                    "event": "second purge pass opened the steam path; bed still over 195 C; hold unchanged",
                },
                {
                    "t_local": "18:40",
                    "event": "jetty slot missed; reactor still cooling; no deflagration",
                },
                {
                    "t_local": "21:20",
                    "event": "about 5.2 h of missed VAM booked, about 142000 USD; couple check scheduled",
                },
                {
                    "t_local": "07:10",
                    "event": "next-day walk: reactor intact, structure unburned, no 16-day rebuild",
                },
            ],
            "observed_effects": [
                "FT-C2-390 stayed at zero; no acetic pad fire at R-390",
                "crude VAM assay was not spent as hotspot; steam purge ran",
                "the two structure operators remained uninjured; no burns",
                "about 5.2 h of missed VAM and about 142000 USD paid",
                "purge-valve stall did not restore an ethylene permit while TE-VAM-390 stayed above 195 C",
            ],
            "state_delta": {
                "r390_status": "ethylene_held_purge_open",
                "ethylene_cut": True,
                "deflagration": False,
                "lost_vam_h": 5.2,
            },
            "commercial_result": {
                "lost_vam_usd": 142000,
                "couple_check_usd": 6500,
                "deflagration_rebuild_avoided_usd": 12100000,
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
                "task_completion weakly positive: ethylene is cut and the purge is "
                "open but the jetty slot is lost; efficiency negative because "
                "142000 USD and the couple-check outage were paid; "
                "personnel_safety carries the two uninjured operators"
            ),
        },
        "meta": meta_for(3),
    }


PAIRS = {
    1: {
        "id": "ffpc-r32-001",
        "goal": (
            "Gate PaKeep's request to raise FT-NAPH-460 while TE-SALT-460 is 428 C "
            "and the oxidizer PSV is already fuming."
        ),
        "critique": (
            "The unsafe arm raised naphthalene because a still-normal 99.4 wt percent "
            "PA assay was spent as proof the salt bath was cool and a 428 C "
            "couple was filed as thermowell stain. The repaired arm holds "
            "FT-NAPH-460 at zero and trips air. The morning still pays about "
            "five hours of missed flake and an assay check; the PSV fire "
            "and two naphthalene burns are not spent."
        ),
    },
    2: {
        "id": "ffpc-r32-002",
        "goal": (
            "Gate AdKeep's request to trip FT-AIR-820 and purge R-820 because "
            "TE-KA-820 is 196 C versus max 175 C."
        ),
        "critique": (
            "The unsafe arm turned a 196 C oxidizer trip into a cyclohexane nudge "
            "that held air because adipic at 99.1 wt percent was still "
            "inside the product band. The repaired arm sheds air and cyclohexane "
            "and purges R-820, leaving adipic titer as liquor quality. The night still "
            "pays about four hours of missed adipic and about 38000 USD; the manway "
            "fire and 18-day rebuild are not spent."
        ),
    },
    3: {
        "id": "ffpc-r32-003",
        "goal": (
            "Gate VaKeep's request to cut FT-C2-390 and steam-purge R-390 "
            "because TE-VAM-390 is 218 C versus a 195 C trip."
        ),
        "critique": (
            "The unsafe arm kept ethylene on because a still-normal 99.0 wt percent "
            "crude VAM assay was spent as bed metal while TE-VAM-390 sat 218 C. "
            "The repaired arm cuts FT-C2-390 and injects steam. The afternoon "
            "still pays a 142000 USD jetty slot and a couple check; the acetic "
            "deflagration and two structure burns are not spent."
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
        raise SystemExit("r32 drop absent; refusing to invent chosen arms")
    diags = []
    arms = []
    for index in (1, 2, 3):
        diag_path = STAGE / f"diagnosis-{index:02d}-r32.md"
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
        path = STAGE / f"chosen-{index:02d}-r32.json"
        path.write_text(json.dumps(arm, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
        pair_path = STAGE / f"pair-{index:02d}-r32.json"
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
