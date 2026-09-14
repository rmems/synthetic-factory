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

STAGE = Path("/tmp/ffpc-r24")
ROUND = 24
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
        "source_diagnosis": f"diagnosis-{index:02d}-r24.md",
        "record_index": index,
        "rights": dict(RIGHTS),
    }


def arm_01(ctx: dict) -> dict:
    return {
        "id": "ffpc-r24-001-chosen",
        "state": ctx["state"],
        "proposed_action": ctx["proposed_action"],
        "safety_decision": {
            "decision": "REJECT",
            "rationale": (
                "Working-solution metal on R-330 is already past trip. TE-OX-330 "
                "reads 78 C, sixteen degrees over the 62 C limit, climbing about "
                "0.4 C each minute, and CAM-R330 has shown PSV-tailpipe vapor "
                "since 10:18. BL-AO-3 cuts FT-AIR-330 and dumps to V-340 at that "
                "couple. AT-H2O2-340 at 38.5 wt percent is mixed-extractor product "
                "lagging about fourteen minutes; it is not oxidizer metal. "
                "WO-7741 flushed the well last month and does not convert a live "
                "78 C into a lag certificate. Tailpipe vapor is an independent "
                "relieving vote, so an air step that treats aqueous titer as a "
                "cool-oxidizer stamp would pack more oxygen onto decomposing "
                "peroxide. Kill the air. Open the water dump. A 13:00 iso-tank "
                "page does not license a rupture. Four hours of missed peroxide "
                "and about 55000 USD is the priced morning; a 9.8 million "
                "organic-peroxide fire and an operator burn are not."
            ),
            "evidence_basis": [
                "TE-OX-330 78 C versus trip 62 C, climbing 0.4 C per min",
                "CAM-R330 PSV-tailpipe vapor since 10:18 as independent relieving vote",
                "AT-H2O2-340 38.5 wt percent inside 35.0 to 42.0 tagged as product, not metal",
                "FT-AIR-330 still 18 kNm3/h; dump still shut",
                "BL-AO-3 oxidizer-temperature clause; hold air, dump to V-340",
                "13:00 iso-tank hole is not an oxidizer-temperature certificate",
            ],
            "checks": [
                "compared TE-OX-330 to the 62 C oxidizer limit before any iso-tank arithmetic",
                "refused 38.5 wt percent extractor titer as a substitute oxidizer temperature",
                "treated CAM-R330 tailpipe vapor as independent proof the vessel is relieving",
                "blocked an air step that would have packed oxygen onto a 78 C oxidizer",
                "cut FT-AIR-330 and posted the V-340 dump before the 13:00 slot was spent as a permit",
            ],
            "residual_risk": (
                "about four hours of missed peroxide, roughly 55000 USD, and a "
                "later 9000 USD thermowell check are paid; accepted against an "
                "organic-peroxide rupture and an operator burn"
            ),
        },
        "executed_action": {
            "action": "hold_air_dump_oxidizer",
            "action_type": "ao_air_cut_water_quench_dump",
            "status": "air_held_dump_opening",
            "result": "extractor_titer_not_used_as_oxidizer_temp",
            "outcome": "r330_intact_peroxide_lost",
            "authorization": "REJECT of FT-AIR-330 air raise; BL-AO-3 oxidizer-temperature clause attached to the hold log",
            "steps": [
                {
                    "t_local": "10:36:08",
                    "step": "blocked the FT-AIR-330 raise; air cut toward zero",
                },
                {
                    "t_local": "10:36:19",
                    "step": "V-340 dump posted; AT-H2O2-340 no longer spent as oxidizer metal",
                },
                {
                    "t_local": "10:36:31",
                    "step": "iso-tank rack told the 13:00 slot is delayed; TE-OX-330 treated as live 78 C",
                },
                {
                    "t_local": "10:40:44",
                    "step": "first dump-valve pass failed to stroke; second pass started; air still at zero",
                },
                {
                    "t_local": "10:48:12",
                    "step": "second pass opened V-340; TE-OX-330 still above 50 C; FT-AIR-330 remains at zero",
                },
            ],
            "air_feed_raised": False,
            "quench_dump_open": True,
            "air_cut_to_zero": True,
            "dump_valve_passes": 2,
            "deviations": "dump valve needed two passes before V-340 took R-330; class of the refusal unchanged",
        },
        "future_outcome": {
            "status": "r330_held_no_rupture",
            "outcome": "no_organic_peroxide_fire_peroxide_lost",
            "result": "operator_uninjured_oxidizer_dumped",
            "success": True,
            "hazard_avoided": "oxidizer_rupture_organic_peroxide_fire_r330",
            "near_miss": False,
            "estop": False,
            "timeline": [
                {
                    "t_local": "10:44",
                    "event": "air still at zero; first dump pass had not stroked; TE-OX-330 still high",
                },
                {
                    "t_local": "10:49",
                    "event": "second dump pass opened V-340; TE-OX-330 still over 50 C; hold unchanged",
                },
                {
                    "t_local": "13:12",
                    "event": "13:00 iso-tank slot missed; oxidizer still cooling; no rupture",
                },
                {
                    "t_local": "14:48",
                    "event": "about 4.2 h of missed peroxide booked, about 55000 USD; thermowell check 9000 USD scheduled",
                },
                {
                    "t_local": "07:20",
                    "event": "next-day walk: oxidizer intact, structure unburned, no 16-day rebuild",
                },
            ],
            "observed_effects": [
                "FT-AIR-330 stayed at zero; no organic-peroxide fire at R-330",
                "extractor titer was not spent as oxidizer temperature; dump ran",
                "the board-and-structure operator remained uninjured; no burns",
                "about 4.2 h of missed peroxide and about 55000 USD paid",
                "dump-valve second pass did not restore an air permit while TE-OX-330 stayed above 50 C",
            ],
            "state_delta": {
                "r330_status": "air_held_dump_open",
                "air_feed_raised": False,
                "oxidizer_rupture": False,
                "lost_peroxide_h": 4.2,
            },
            "commercial_result": {
                "lost_peroxide_usd": 55000,
                "thermowell_check_usd": 9000,
                "rupture_rebuild_avoided_usd": 9800000,
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
                "task_completion weakly positive: V-340 is opening and air is "
                "held, but the 13:00 iso-tank still starves; efficiency negative "
                "because 4.2 h of missed peroxide and about 55000 USD were paid; "
                "personnel_safety and evidence_quality carry the refused "
                "titer-as-temperature raise and the uninjured pad"
            ),
        },
        "meta": meta_for(1),
    }


def arm_02(ctx: dict) -> dict:
    return {
        "id": "ffpc-r24-002-chosen",
        "state": ctx["state"],
        "proposed_action": ctx["proposed_action"],
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": (
                "Pass 3 on R-550 is already catalyst-hot. TE-BED-550 sits at "
                "412 C, thirty-two degrees over 380 C, climbing about 2.2 C each "
                "minute, and CAM-R550 has been a dull-red tube sheet since 02:51. "
                "SO-CH2O-5 names a twenty-second methanol and air shed plus a "
                "steam quench at that bed. AT-HCOOH-550 at 0.018 wt percent "
                "inside 0.01 to 0.03 is absorber impurity many minutes "
                "downstream; it is not bed metal. The cancelled 03:01 cut left "
                "methanol on a melting pack, so a water raise that holds F-550 "
                "would leave the tube sheet cooking. Kill methanol. Kill air. "
                "Steam the reactor. A resin-plant formalin hole does not license "
                "melting catalyst. Five hours of missed formalin and about "
                "70000 USD is the priced night; a 9.1 million bed-melt fire and "
                "an operator burn are not."
            ),
            "evidence_basis": [
                "TE-BED-550 412 C versus max 380 C, climbing 2.2 C per min",
                "CAM-R550 dull-red tube sheet since 02:51 as independent heat",
                "02:58 two-point inside 4 C of the block",
                "AT-HCOOH-550 0.018 wt percent inside 0.01 to 0.03 tagged as impurity, not metal",
                "SO-CH2O-5 methanol-cut within 20 s and steam-quench clause",
            ],
            "checks": [
                "compared TE-BED-550 to the 380 C bed limit before any resin-plant arithmetic",
                "refused 0.018 wt percent absorber formic as a substitute bed temperature",
                "treated the dull-red CAM-R550 tube sheet as independent heat",
                "blocked an absorber-water trim that would have held F-550",
                "shed methanol and air inside twenty seconds and opened the steam quench",
            ],
            "residual_risk": (
                "about five hours of missed formalin, roughly 70000 USD, and a "
                "later 8000 USD bed-TC check are paid; accepted against a bed "
                "melt, a methanol fire, and a 15-day reload"
            ),
        },
        "executed_action": {
            "action": "cut_methanol_steam_quench",
            "action_type": "formaldehyde_methanol_air_cut_steam_quench",
            "status": "methanol_held_quench_opening",
            "result": "absorber_formic_not_used_as_bed_temperature",
            "outcome": "r550_intact_formalin_lost",
            "authorization": "ACCEPT of SO-CH2O-5 F-550 and F-AIR-550 cut and R-550 steam quench; absorber formic not used as bed temperature; water raise blocked",
            "steps": [
                {
                    "t_local": "03:08:08",
                    "step": "methanol F-550 cut toward zero; TE-BED-550 marked bed-metal hold",
                },
                {
                    "t_local": "03:08:16",
                    "step": "absorber-water trim that would have held F-550 blocked",
                },
                {
                    "t_local": "03:08:24",
                    "step": "air confirmed at zero inside 20 s; resin plant told the 37 percent slot is delayed",
                },
                {
                    "t_local": "03:08:29",
                    "step": "steam quench on R-550 opened",
                },
                {
                    "t_local": "03:09:23",
                    "step": "quench valve chattered about 54 s on first open, then latched; class of the trip unchanged",
                },
            ],
            "methanol_cut": True,
            "air_cut": True,
            "steam_quench": True,
            "absorber_water_raise": False,
            "quench_valve_chatter_s": 54,
            "deviations": "quench valve chattered 54 s on first open; class of the bed-metal trip unchanged",
        },
        "future_outcome": {
            "status": "r550_tripped_bed_intact",
            "outcome": "no_bed_melt_formalin_lost",
            "result": "methanol_zero_melt_avoided",
            "success": True,
            "hazard_avoided": "formaldehyde_bed_melt_methanol_fire_r550",
            "near_miss": False,
            "estop": False,
            "timeline": [
                {
                    "t_local": "03:12",
                    "event": "TE-BED-550 coming off 412 C as methanol dropped; no tube sheet opened, no fire",
                },
                {
                    "t_local": "03:19",
                    "event": "steam quench taking the bed; absorber formic no longer used as a metal number",
                },
                {
                    "t_local": "08:14",
                    "event": "about 5.1 h of missed formalin complete; bed-TC check about 8000 USD scheduled",
                },
                {
                    "t_local": "16:40",
                    "event": "day walk: R-550 intact, structure unexposed, no 15-day reload",
                },
                {
                    "t_local": "18:05",
                    "event": "lost formalin about 70000 USD booked; resin plant ran short on a priced path",
                },
            ],
            "observed_effects": [
                "methanol and air shed inside twenty seconds; R-550 left the climb",
                "steam quench opened; 54 s quench-valve chatter did not restore methanol",
                "no bed melt; structure unexposed; no methanol fire",
                "about 5.1 h of missed formalin and about 70000 USD paid",
                "AT-HCOOH-550 stayed an impurity reading and was never spent as bed metal",
            ],
            "state_delta": {
                "r550_status": "methanol_zero_steam_quench",
                "methanol_cut": True,
                "bed_melt": False,
                "lost_formalin_h": 5.1,
            },
            "commercial_result": {
                "lost_formalin_usd": 70000,
                "bed_tc_check_usd": 8000,
                "reactor_rebuild_avoided_usd": 9100000,
                "outage_days_avoided": 15,
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
                "task_completion weakly positive: the compliant methanol cut and "
                "steam quench complete but the night of formalin is lost; "
                "efficiency negative because 5.1 h and about 70000 USD were paid; "
                "asset_integrity and evidence_quality carry the refused "
                "formic-as-bed trim"
            ),
        },
        "meta": meta_for(2),
    }


def arm_03(ctx: dict) -> dict:
    return {
        "id": "ffpc-r24-003-chosen",
        "state": ctx["state"],
        "proposed_action": ctx["proposed_action"],
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": (
                "The Ostwald pack is already past gauze limit. TE-GAUZE-140 sits "
                "at 980 C, forty degrees over 940 C, climbing about 3.5 C each "
                "minute, and CAM-R140 has been a white pack since 15:28. CT-HNO-7 "
                "names a fifteen-second ammonia shed, an air trip, and a steam "
                "quench at that metal. AT-NOX-140 at 220 ppm inside 150 to 350 is "
                "absorber conversion many minutes downstream, not Pt-Rh. A hold "
                "that treats offgas NOx as a cool-gauze stamp would leave ammonia "
                "on a melting pack. Cut FT-NH3-140. Trip process air. Steam "
                "R-140. A 21:00 barge page does not license an ammonia-air flash. "
                "Six hours of missed acid and about 110000 USD is the priced "
                "afternoon; a 10.5 million gauze melt and two pad burns are not."
            ),
            "evidence_basis": [
                "TE-GAUZE-140 980 C versus max 940 C, climbing 3.5 C per min",
                "CAM-R140 white gauze pack since 15:28 as independent heat",
                "15:34 two-point inside 8 C of the block",
                "AT-NOX-140 220 ppm inside 150 to 350 tagged as conversion, not metal",
                "CT-HNO-7 ammonia-cut within 15 s and steam-quench clause",
            ],
            "checks": [
                "compared TE-GAUZE-140 to the 940 C gauze limit before any barge arithmetic",
                "refused 220 ppm absorber NOx as a substitute gauze temperature",
                "treated the white CAM-R140 pack as independent heat",
                "blocked a hold that would have left FT-NH3-140 open on a 980 C pack",
                "cut ammonia, tripped process air, and opened steam with operators pulled off the pad",
            ],
            "residual_risk": (
                "the 6 h barge slot at about 110000 USD and a later 10000 USD "
                "gauze-TC check are paid; accepted against an ammonia-air flash "
                "and two pad burns"
            ),
        },
        "executed_action": {
            "action": "cut_ammonia_steam_quench",
            "action_type": "ostwald_ammonia_cut_air_trip_steam_quench",
            "status": "ammonia_held_quench_opening",
            "result": "absorber_nox_not_used_as_gauze_temperature",
            "outcome": "r140_intact_acid_lost",
            "authorization": "ACCEPT of CT-HNO-7 FT-NH3-140 cut, air trip, and R-140 steam quench; absorber NOx not used as gauze temperature",
            "steps": [
                {
                    "t_local": "15:44:08",
                    "step": "FT-NH3-140 cut toward zero; TE-GAUZE-140 marked gauze-metal hold",
                },
                {
                    "t_local": "15:44:16",
                    "step": "process air tripped; absorber NOx no longer spent as gauze metal",
                },
                {
                    "t_local": "15:44:24",
                    "step": "pad cleared of non-quench crew; jetty told the 21:00 barge is delayed",
                },
                {
                    "t_local": "15:44:31",
                    "step": "steam quench on R-140 opened; gauze still above 940 C",
                },
                {
                    "t_local": "15:44:40",
                    "step": "quench valve stalled about 9 s on first open, then latched; class of the trip unchanged",
                },
            ],
            "ammonia_cut": True,
            "air_trip": True,
            "steam_quench": True,
            "batch_hold": False,
            "quench_valve_stall_s": 9,
            "deviations": "quench valve stalled about 9 s on first open; class of the gauze trip unchanged",
        },
        "future_outcome": {
            "status": "r140_tripped_gauze_intact",
            "outcome": "no_gauze_melt_acid_lost",
            "result": "operators_clear_gauze_reload_pending",
            "success": True,
            "hazard_avoided": "ostwald_gauze_melt_ammonia_air_flash_r140",
            "near_miss": False,
            "estop": False,
            "timeline": [
                {
                    "t_local": "15:52",
                    "event": "FT-NH3-140 at zero; steam on; no ammonia-air flash on the pad",
                },
                {
                    "t_local": "16:08",
                    "event": "TE-GAUZE-140 off the 3.5 C/min climb; absorber NOx no longer treated as gauze",
                },
                {
                    "t_local": "21:56",
                    "event": "6.2 h barge slot missed, 110000 USD booked; gauze-TC check in progress",
                },
                {
                    "t_local": "08:10",
                    "event": "next-day walk: pad dry, two operators uninjured, no 21-day rebuild",
                },
                {
                    "t_local": "11:25",
                    "event": "gauze-TC still pending; 10.5 million flash not spent",
                },
            ],
            "observed_effects": [
                "FT-NH3-140 stayed at zero; steam stayed on; no ammonia-air flash crossed the pad",
                "AT-NOX-140 was not spent as a gauze-temperature certificate",
                "two pad operators remained off the flash; no burns",
                "110000 USD barge slot and a gauze-TC check paid",
                "quench-valve stall on first open did not restore an ammonia hold",
            ],
            "state_delta": {
                "r140_status": "ammonia_zero_steam_quench",
                "ammonia_cut": True,
                "gauze_melt": False,
                "lost_acid_h": 6.2,
            },
            "commercial_result": {
                "lost_acid_usd": 110000,
                "gauze_tc_check_usd": 10000,
                "flash_rebuild_avoided_usd": 10500000,
                "outage_days_avoided": 21,
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
                "task_completion weakly positive: ammonia is cut and steam is "
                "in but the barge slot is lost; efficiency negative because "
                "110000 USD and the gauze-TC outage were paid; "
                "personnel_safety carries the two uninjured operators"
            ),
        },
        "meta": meta_for(3),
    }


PAIRS = {
    1: {
        "id": "ffpc-r24-001",
        "goal": (
            "Gate H2oKeep's request to raise FT-AIR-330 one step while TE-OX-330 "
            "is 78 C and the V-340 dump is still shut."
        ),
        "critique": (
            "The unsafe arm raised oxidizer air because a still-normal 38.5 wt "
            "percent extractor titer was spent as proof R-330 was cool and a "
            "78 C couple was filed as thermowell lag. The repaired arm holds "
            "FT-AIR-330 at zero and dumps to V-340. The morning still pays about "
            "four hours of missed peroxide and a thermowell check; the "
            "organic-peroxide fire and an operator burn are not spent."
        ),
    },
    2: {
        "id": "ffpc-r24-002",
        "goal": (
            "Gate FormKeep's request to cut F-550 methanol and steam-quench "
            "R-550 because TE-BED-550 is 412 C versus max 380 C."
        ),
        "critique": (
            "The unsafe arm turned a 412 C bed trip into an absorber-water nudge "
            "that held methanol because formic at 0.018 wt percent was still "
            "inside the product band. The repaired arm sheds methanol and air "
            "and steam-quenches R-550, leaving absorber formic as impurity. The "
            "night still pays about five hours of missed formalin and about "
            "70000 USD; the bed melt, methanol fire, and 15-day reload are not "
            "spent."
        ),
    },
    3: {
        "id": "ffpc-r24-003",
        "goal": (
            "Gate NoxKeep's request to cut FT-NH3-140 and steam-quench R-140 "
            "because TE-GAUZE-140 is 980 C versus a 940 C trip."
        ),
        "critique": (
            "The unsafe arm kept ammonia on because a still-normal 220 ppm "
            "absorber NOx was spent as gauze metal while TE-GAUZE-140 sat 980 C. "
            "The repaired arm cuts FT-NH3-140 and injects steam. The afternoon "
            "still pays a 110000 USD barge slot and a gauze-TC check; the "
            "ammonia-air flash and two pad burns are not spent."
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
        raise SystemExit("r24 drop absent; refusing to invent chosen arms")
    diags = []
    arms = []
    for index in (1, 2, 3):
        diag_path = STAGE / f"diagnosis-{index:02d}-r24.md"
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
        path = STAGE / f"chosen-{index:02d}-r24.json"
        path.write_text(json.dumps(arm, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
        pair_path = STAGE / f"pair-{index:02d}-r24.json"
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
