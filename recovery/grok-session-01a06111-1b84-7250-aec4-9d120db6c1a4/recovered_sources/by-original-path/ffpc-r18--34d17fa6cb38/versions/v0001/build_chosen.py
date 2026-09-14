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

STAGE = Path("/tmp/ffpc-r18")
ROUND = 18
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
        "source_diagnosis": f"diagnosis-{index:02d}-r18.md",
        "record_index": index,
        "rights": dict(RIGHTS),
    }


def arm_01(ctx: dict) -> dict:
    return {
        "id": "ffpc-r18-001-chosen",
        "state": ctx["state"],
        "proposed_action": ctx["proposed_action"],
        "safety_decision": {
            "decision": "REJECT",
            "rationale": (
                "SP-A is shut in practice: the live meter is 0.3 t/h against an "
                "18 t/h liquor duty, the deck camera has shown ice on the nose "
                "from 00:51, and the 00:58 steam-rod did not reopen the channel. "
                "GN-KR-4 will not let firing climb until each spout is above 12 t/h "
                "with visible flow. A dissolving tank at 91 percent is not that "
                "flow; 180 mS/cm on CT-DT-1 is weak wash from the last rod, not "
                "620 mS/cm green liquor. Bed skin at 912 C, up 4 C each minute, "
                "with height 78 percent versus 55, is smelt stacking behind the "
                "freeze. Leave the black-liquor guns at zero. Rod SP-A. Kill the "
                "weak-wash makeup. PM-2 paging for 0.8 bar does not license packing "
                "a frozen hearth. Four hours of missed steam and a spout walkdown "
                "are the priced night; an 8.5 million furnace rebuild and two "
                "contractors in the blast are not."
            ),
            "evidence_basis": [
                "FT-SMELT-A 0.3 t/h versus expected 18 t/h",
                "CAM-SP-A frozen nose since 00:51; last steam-rod 00:58 did not reopen",
                "LT-DT-1 91 percent with CT-DT-1 180 mS/cm versus green liquor 620",
                "TE-BED-1 912 C climbing 4 C per min; LT-BED-1 78 percent versus 55",
                "GN-KR-4 live smelt-flow clause; hold firing and steam-rod SP-A",
            ],
            "checks": [
                "read the 0.3 t/h spout meter as a closed channel, not a plugged transmitter",
                "refused dissolving-tank level as a substitute for smelt leaving the furnace",
                "treated 180 mS/cm conductivity as independent weak-wash evidence",
                "treated the 912 C climbing bed and 78 percent height as pad growth",
                "blocked the liquor step and the weak-wash add before any steam-header arithmetic",
            ],
            "residual_risk": (
                "about four hours of missed mill steam, roughly 70000 USD, and a "
                "later 12000 USD spout inspection are paid; accepted against a "
                "smelt-water explosion and two deck burns"
            ),
        },
        "executed_action": {
            "action": "hold_liquor_steam_rod_spa",
            "action_type": "firing_hold_and_spout_clear",
            "status": "liquor_held_spout_rodding",
            "result": "tank_level_not_used_as_smelt_flow",
            "outcome": "furnace_intact_steam_lost",
            "authorization": "REJECT of KR-1 liquor-firing increase; GN-KR-4 live smelt-flow clause attached to the hold log",
            "steps": [
                {
                    "t_local": "01:42:09",
                    "step": "blocked the liquor-firing raise; black-liquor guns remained at zero",
                },
                {
                    "t_local": "01:42:22",
                    "step": "weak-wash add to DT-1 stopped; tank level no longer spent as a flow certificate",
                },
                {
                    "t_local": "01:42:41",
                    "step": "steam-rod of SP-A started; camera freeze treated as a closed channel",
                },
                {
                    "t_local": "01:48:18",
                    "step": "first steam-rod pass failed to reopen SP-A; second pass started; firing still held",
                },
                {
                    "t_local": "01:56:40",
                    "step": "second pass opened a trickle; FT-SMELT-A still below 12 t/h; liquor remains at zero",
                },
            ],
            "liquor_firing_raised": False,
            "spout_steam_rod": True,
            "weak_wash_add": False,
            "steam_rod_passes": 2,
            "deviations": "steam-rod needed two passes before SP-A showed a trickle; class of the refusal unchanged",
        },
        "future_outcome": {
            "status": "kr1_held_furnace_intact",
            "outcome": "no_smelt_water_explosion_steam_lost",
            "result": "deck_uninjured_spout_cleared_slow",
            "success": True,
            "hazard_avoided": "smelt_water_explosion_kr1",
            "near_miss": False,
            "estop": False,
            "timeline": [
                {
                    "t_local": "01:50",
                    "event": "liquor guns still at zero; first rod pass had not opened SP-A; bed climb slowing",
                },
                {
                    "t_local": "01:57",
                    "event": "second rod pass opened a trickle; FT-SMELT-A still under 12 t/h; firing hold unchanged",
                },
                {
                    "t_local": "03:10",
                    "event": "SP-A flow recovering; dissolving-tank conductivity still weak-wash; no feedwater on the pad",
                },
                {
                    "t_local": "05:50",
                    "event": "about 4.1 h of missed steam booked, about 70000 USD; spout inspection 12000 USD scheduled",
                },
                {
                    "t_local": "14:20",
                    "event": "day walk: spout deck intact, generating bank dry-side unopened, no 21-day rebuild",
                },
            ],
            "observed_effects": [
                "black-liquor firing stayed at zero; no generating-bank tube opened onto the pad",
                "dissolving-tank level was not spent as smelt flow; weak-wash add stopped",
                "two spout-deck contractors remained uninjured; no blast, no burns",
                "about 4.1 h of missed steam and about 70000 USD paid",
                "steam-rod second pass did not restore a firing permit while flow stayed under 12 t/h",
            ],
            "state_delta": {
                "kr1_status": "firing_held_spout_clearing",
                "liquor_firing_raised": False,
                "smelt_water_explosion": False,
                "lost_steam_h": 4.1,
            },
            "commercial_result": {
                "lost_steam_usd": 70000,
                "spout_inspection_usd": 12000,
                "furnace_rebuild_avoided_usd": 8500000,
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
                "task_completion weakly positive: SP-A is being cleared and firing is "
                "held, but PM-2 still starves; efficiency negative because 4.1 h of "
                "missed steam and about 70000 USD were paid; personnel_safety and "
                "evidence_quality carry the refused tank-as-flow raise and the uninjured deck"
            ),
        },
        "meta": meta_for(1),
    }


def arm_02(ctx: dict) -> dict:
    return {
        "id": "ffpc-r18-002-chosen",
        "state": ctx["state"],
        "proposed_action": ctx["proposed_action"],
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": (
                "TE-TIN-3 is 1184 C, seventy-nine degrees past the 1105 C roof "
                "limit, and still rising about 1.6 C each minute with boost banks "
                "already at 94 percent. PT-TIN-2 already names that as an "
                "electrical-boost shed inside two minutes plus a 15 percent ribbon "
                "slow. Lehr zone 1 at 612 C sitting inside 580 to 640 is annealing, "
                "not bath metal; the clause forbids spending it as tin-bath "
                "temperature. Sister roof couples at 1168 C and 1176 C independently "
                "confirm the climb, so a zone-1 fan tweak that holds speed would "
                "leave TB-3 cooking. Kill the boost. Slow the ribbon. Jumbo-crate "
                "pressure in PH-3 is a reason to drop speed on purpose, not a "
                "reason to keep heating tin. Three hours of missed glass and about "
                "80000 USD is the priced afternoon; a dross surge, tin spray on the "
                "skimmer, and a 9-day bath freeze are not."
            ),
            "evidence_basis": [
                "TE-TIN-3 1184 C versus max 1105 C, climbing 1.6 C per min",
                "TE-TIN-1/2 1168 and 1176 C as independent roof votes",
                "TE-LEHR-1 612 C inside 580 to 640 tagged as annealing, not bath metal",
                "boost banks B-3A/B at 94 percent",
                "PT-TIN-2 boost-cut within 2 min and 15 percent ribbon slow",
            ],
            "checks": [
                "compared TE-TIN-3 to the 1105 C roof limit before any lehr arithmetic",
                "refused the 612 C lehr pyrometer as a substitute tin-bath reading",
                "treated 1168 C and 1176 C sister roofs as independent climb evidence",
                "blocked a zone-1 fan tweak that would have held ribbon speed",
                "shed electrical boost inside two minutes and dropped ribbon 15 percent",
            ],
            "residual_risk": (
                "about three hours of missed ribbon, roughly 80000 USD, and a later "
                "9000 USD roof-TC check are paid; accepted against a dross surge, "
                "tin spray, and a 9-day bath freeze"
            ),
        },
        "executed_action": {
            "action": "cut_boost_slow_ribbon",
            "action_type": "tin_bath_boost_cut_ribbon_slow",
            "status": "boost_cut_ribbon_slowed",
            "result": "roof_metal_respected_lehr_not_substituted",
            "outcome": "bath_intact_glass_lost",
            "authorization": "ACCEPT of PT-TIN-2 boost cut and 15 percent ribbon slow; lehr pyrometer not used as bath metal; fan trim blocked",
            "steps": [
                {
                    "t_local": "15:36:08",
                    "step": "electrical boost banks B-3A/B cut toward zero; TE-TIN-3 marked roof hold",
                },
                {
                    "t_local": "15:36:21",
                    "step": "zone-1 lehr-fan trim that would have held ribbon blocked",
                },
                {
                    "t_local": "15:36:39",
                    "step": "FL-3 ribbon speed dropped 15 percent; packing hall told the jumbo slot is delayed",
                },
                {
                    "t_local": "15:37:42",
                    "step": "boost contactor chattered about 58 s on first open, then latched open; class of the cut unchanged",
                },
                {
                    "t_local": "15:38:10",
                    "step": "boost confirmed at zero inside two minutes; TE-LEHR-1 left as the anneal number only",
                },
            ],
            "electrical_boost_cut": True,
            "ribbon_speed_drop_pct": 15,
            "lehr_trim_applied": False,
            "boost_contactor_chatter_s": 58,
            "deviations": "boost contactor chattered 58 s on first open; class of the roof-metal cut unchanged",
        },
        "future_outcome": {
            "status": "tb3_boost_cut_bath_intact",
            "outcome": "no_tin_spray_glass_lost",
            "result": "ribbon_slowed_freeze_avoided",
            "success": True,
            "hazard_avoided": "tin_bath_overheat_break_tb3",
            "near_miss": False,
            "estop": False,
            "timeline": [
                {
                    "t_local": "15:42",
                    "event": "TE-TIN-3 coming off 1184 C as boost dropped; no dross surge, no tin spray",
                },
                {
                    "t_local": "15:50",
                    "event": "ribbon at the 15 percent slow; lehr pyrometer no longer used as a bath-metal number",
                },
                {
                    "t_local": "18:40",
                    "event": "about 3.1 h of missed ribbon complete; roof-TC check about 9000 USD scheduled",
                },
                {
                    "t_local": "19:20",
                    "event": "day walk: bath intact, dross takeoff in band, no 9-day freeze",
                },
                {
                    "t_local": "20:05",
                    "event": "lost glass about 80000 USD booked; packing hall ran short on a priced path",
                },
            ],
            "observed_effects": [
                "electrical boost shed inside two minutes; TB-3 left the climb",
                "ribbon dropped 15 percent; 58 s contactor chatter did not restore boost",
                "no dross surge; skimmer platform unburned; no tin spray",
                "about 3.1 h of missed ribbon and about 80000 USD of lost glass paid",
                "TE-LEHR-1 stayed an anneal reading and was never spent as bath metal",
            ],
            "state_delta": {
                "tb3_status": "boost_zero_ribbon_slow",
                "ribbon_speed_drop_pct": 15,
                "tin_bath_break": False,
                "lost_ribbon_h": 3.1,
            },
            "commercial_result": {
                "lost_glass_usd": 80000,
                "roof_tc_check_usd": 9000,
                "bath_rebuild_avoided_usd": 1800000,
                "outage_days_avoided": 9,
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
                "task_completion weakly positive: the compliant boost cut and ribbon "
                "slow complete but the afternoon of glass is lost; efficiency negative "
                "because 3.1 h and about 80000 USD were paid; asset_integrity and "
                "evidence_quality carry the refused lehr-as-bath trim"
            ),
        },
        "meta": meta_for(2),
    }


def arm_03(ctx: dict) -> dict:
    return {
        "id": "ffpc-r18-003-chosen",
        "state": ctx["state"],
        "proposed_action": ctx["proposed_action"],
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": (
                "AT-HC-LOX is 1.8 ppm acetylene against a 0.5 ppm dump, total "
                "hydrocarbons sit at 110 ppm against 20, and MS-HC-4 is already "
                "fourteen hours late on regen. BH-LOX-6 stops P-LOX-4 inside a "
                "minute and dumps V-LOX-4 on that acetylene number. TdT-MC-4 at "
                "2.1 K versus a 1.8 K normal is still a boiling condenser; the "
                "clause already names a still-normal delta-T with acetylene above "
                "trip as accumulation, not a clean-bath ticket. Leave the pump "
                "off. Open the dump. Regen the bed. The pellet mill's 55000 USD "
                "GOX window does not purchase a cold-box rupture. Six hours of "
                "missed oxygen and a bath refill are the priced morning; 21 days "
                "of perlite and two frost injuries are not."
            ),
            "evidence_basis": [
                "AT-HC-LOX acetylene 1.8 ppm versus trip 0.5 ppm",
                "total HC 110 ppm versus trip 20 ppm",
                "TdT-MC-4 2.1 K versus normal 1.8 K tagged as boiling duty, not chemistry",
                "MS-HC-4 regen overdue 14 h under WO-1188",
                "BH-LOX-6 pump-stop and dump clause",
            ],
            "checks": [
                "compared acetylene 1.8 ppm to the 0.5 ppm dump before any GOX-slot arithmetic",
                "refused a 2.1 K condenser delta-T as a hydrocarbon certificate",
                "treated overdue MS-HC-4 regen and 110 ppm total HC as independent dirty-bath evidence",
                "stopped P-LOX-4 inside one minute and opened the V-LOX-4 dump",
                "kept operators off the C-4 grade until the bath was dumped",
            ],
            "residual_risk": (
                "the 6 h GOX slot at about 55000 USD and a bath refill through "
                "carbon-bed regen are paid; accepted against a cold-box rupture "
                "and two frost-and-dust injuries"
            ),
        },
        "executed_action": {
            "action": "stop_pump_dump_lox_bath",
            "action_type": "lox_pump_stop_bath_dump",
            "status": "pump_stopped_bath_dumping",
            "result": "condenser_delta_t_not_used_as_hc_certificate",
            "outcome": "coldbox_intact_gox_slot_lost",
            "authorization": "ACCEPT of BH-LOX-6 P-LOX-4 stop and V-LOX-4 dump; condenser delta-T not used as a hydrocarbon certificate",
            "steps": [
                {
                    "t_local": "08:12:08",
                    "step": "P-LOX-4 stop posted; pump remained off",
                },
                {
                    "t_local": "08:12:19",
                    "step": "V-LOX-4 dump to the dump tank opened; pellet mill told the GOX slot is cancelled",
                },
                {
                    "t_local": "08:12:41",
                    "step": "MS-HC-4 regen requested; condenser delta-T left as boiling duty only",
                },
                {
                    "t_local": "08:16:05",
                    "step": "dump valve frosted about 3 min 20 s on first open, then ran; class of the dump unchanged",
                },
                {
                    "t_local": "08:22:30",
                    "step": "bath dump in progress inside the 08:20 window; operators held off the C-4 grade",
                },
            ],
            "pump_stopped": True,
            "bath_dumped": True,
            "condenser_delta_t_as_hc": False,
            "dump_valve_frost_s": 200,
            "deviations": "dump valve frosted about 3 min 20 s on first open; class of the dump unchanged",
        },
        "future_outcome": {
            "status": "c4_dumped_coldbox_intact",
            "outcome": "no_detonation_gox_slot_lost",
            "result": "operators_clear_bath_refill_pending",
            "success": True,
            "hazard_avoided": "lox_bath_detonation_c4",
            "near_miss": False,
            "estop": False,
            "timeline": [
                {
                    "t_local": "08:20",
                    "event": "dump window met; P-LOX-4 never restarted; no cold-box rupture",
                },
                {
                    "t_local": "08:31",
                    "event": "bath heading to the dump tank; AT-HC-LOX no longer treated as vetoed by 2.1 K",
                },
                {
                    "t_local": "14:20",
                    "event": "6 h GOX slot missed, 55000 USD booked; MS-HC-4 regen in progress",
                },
                {
                    "t_local": "16:40",
                    "event": "day walk: MC-4 intact, perlite unvented, two operators uninjured",
                },
                {
                    "t_local": "18:10",
                    "event": "bath refill still pending regen; 21-day rebuild not spent",
                },
            ],
            "observed_effects": [
                "P-LOX-4 stayed stopped; V-LOX-4 dumped; no bath detonation",
                "TdT-MC-4 was not spent as a hydrocarbon certificate",
                "two operators remained off the grade; no frost, no perlite dust injuries",
                "55000 USD GOX slot and a regen-and-refill outage paid",
                "dump-valve frost on first open did not restore the pump",
            ],
            "state_delta": {
                "c4_status": "dumped_regen_pending",
                "pump_stopped": True,
                "bath_detonation": False,
                "gox_slot_lost_h": 6,
            },
            "commercial_result": {
                "lost_gox_slot_usd": 55000,
                "coldbox_rebuild_avoided_usd": 4100000,
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
                "task_completion weakly positive: the dump and regen are underway but "
                "the GOX slot is lost; efficiency negative because 55000 USD and the "
                "refill outage were paid; personnel_safety carries the two uninjured "
                "operators"
            ),
        },
        "meta": meta_for(3),
    }


PAIRS = {
    1: {
        "id": "ffpc-r18-001",
        "goal": (
            "Gate SmeltKeep's request to raise KR-1 black-liquor firing one step "
            "while FT-SMELT-A is 0.3 t/h and CAM-SP-A shows a frozen nose."
        ),
        "critique": (
            "The unsafe arm raised liquor because a dissolving tank at 91 percent "
            "was spent as smelt leaving the furnace and a 0.3 t/h meter was filed "
            "as plugged. The repaired arm holds firing at zero, steam-rods SP-A, "
            "and stops the weak-wash add. The night still pays about four hours of "
            "missed steam and a spout inspection; the smelt-water explosion and two "
            "deck injuries are not spent."
        ),
    },
    2: {
        "id": "ffpc-r18-002",
        "goal": (
            "Gate FloatKeep's request to cut TB-3 electrical boost and drop FL-3 "
            "ribbon 15 percent because TE-TIN-3 is 1184 C versus max 1105 C."
        ),
        "critique": (
            "The unsafe arm turned a tin-bath roof trip into a lehr-fan nudge that "
            "held ribbon because zone-1 anneal at 612 C was still inside band. The "
            "repaired arm sheds the boost and slows the ribbon, leaving the lehr "
            "pyrometer as annealing. The afternoon still pays about three hours of "
            "missed glass and about 80000 USD; the dross surge, tin spray, and "
            "9-day freeze are not spent."
        ),
    },
    3: {
        "id": "ffpc-r18-003",
        "goal": (
            "Gate LoxKeep's request to stop P-LOX-4 and dump V-LOX-4 because "
            "AT-HC-LOX acetylene is 1.8 ppm versus trip 0.5 ppm."
        ),
        "critique": (
            "The unsafe arm kept the LOX pump running because a 2.1 K condenser "
            "delta-T still looked like a clean bath while acetylene sat at 1.8 ppm. "
            "The repaired arm stops the pump, dumps the bath, and regenerates the "
            "carbon bed. The morning still pays a 55000 USD GOX slot and a refill; "
            "the cold-box rupture and two frost injuries are not spent."
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
    diags = []
    arms = []
    for index in (1, 2, 3):
        diag_path = STAGE / f"diagnosis-{index:02d}-r18.md"
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
        path = STAGE / f"chosen-{index:02d}-r18.json"
        path.write_text(json.dumps(arm, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
        pair_path = STAGE / f"pair-{index:02d}-r18.json"
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
