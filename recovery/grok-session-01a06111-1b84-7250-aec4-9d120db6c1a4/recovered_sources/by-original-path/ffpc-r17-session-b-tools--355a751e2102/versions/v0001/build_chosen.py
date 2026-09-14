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

STAGE = Path("/tmp/ffpc-r17")
ROUND = 17
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
        "source_diagnosis": f"diagnosis-{index:02d}-r17.md",
        "record_index": index,
        "rights": dict(RIGHTS),
    }


def arm_01(ctx: dict) -> dict:
    return {
        "id": "ffpc-r17-001-chosen",
        "state": ctx["state"],
        "proposed_action": ctx["proposed_action"],
        "safety_decision": {
            "decision": "REJECT",
            "rationale": (
                "DN-UF-4 is 1.27 t/m3 on a suction spool whose 02:40 two-point still "
                "sat inside 0.01 of the block, so the light reading is the underflow, "
                "not a dying source. RL-PASTE-3 will not roll P-UF-4A until that "
                "nuclear tag holds 1.45 to 1.55 for ten straight minutes. LT-SP-4 at "
                "92 percent only proves the standpipe is full; watered tails still "
                "look tall. Dilution FV-W-4 has sat at 18 percent since the 02:52 "
                "floc trip, which is the reason density fell while inventory stayed "
                "high. This line already sanded at 1.31 t/m3 last month under "
                "WO-7719. Leave both underflow pumps stopped. Close the water. "
                "Recycle to TK-4. Six hours of floc rebuild and about 90000 USD of "
                "missed milling is the priced night; an 8.4 km burst and two slurry "
                "burns are not."
            ),
            "evidence_basis": [
                "DN-UF-4 1.27 t/m3 versus transportable 1.45 to 1.55",
                "02:40 two-point inside 0.01 t/m3 of the block",
                "LT-SP-4 92 percent tagged as suction inventory, not density",
                "FV-W-4 18 percent since 02:52 after the flocculant trip",
                "WO-7719 prior sand-out at 1.31 t/m3; RL-PASTE-3 live nuclear-density clause",
            ],
            "checks": [
                "compared the live nuclear 1.27 t/m3 to the 1.45 floor before any pit-feed arithmetic",
                "refused a 92 percent standpipe as a paste-density certificate",
                "read FV-W-4 at 18 percent as the reason the underflow went light",
                "kept both P-UF pumps stopped and opened recycle to TK-4",
                "treated WO-7719 as a warning that 1.31 already sanded this line, not as a reason to distrust the gauge",
            ],
            "residual_risk": (
                "about six hours of recycle and floc rebuild plus roughly 90000 USD "
                "of missed milling remain; accepted against an 8.4 km sand-out burst "
                "and two slurry burns on the pigging skid"
            ),
        },
        "executed_action": {
            "action": "hold_pumps_cut_dilution_recycle",
            "action_type": "paste_pipeline_hold_and_recycle",
            "status": "pumps_stopped_recycle_open",
            "result": "standpipe_not_used_as_density",
            "outcome": "line_clear_milling_delayed",
            "authorization": "REJECT of P-UF-4A start; RL-PASTE-3 nuclear-band clause attached to the hold log",
            "steps": [
                {
                    "t_local": "03:18:12",
                    "step": "blocked the P-UF-4A start write; both underflow pumps remained stopped",
                },
                {
                    "t_local": "03:18:27",
                    "step": "recycle to TK-4 opened; pit P-7 told to stay on hold",
                },
                {
                    "t_local": "03:18:44",
                    "step": "FV-W-4 commanded closed to stop watering the underflow",
                },
                {
                    "t_local": "03:22:05",
                    "step": "FV-W-4 stuck near 30 percent for 3 min 15 s, then seated; class of the refusal unchanged",
                },
                {
                    "t_local": "03:41:20",
                    "step": "DN-UF-4 still below 1.45; recycle continues until ten minutes inside band",
                },
            ],
            "puf4a_started": False,
            "recycle_to_tk4": True,
            "dilution_valve_stick_s": 195,
            "deviations": "FV-W-4 stuck partly open 3 min 15 s on the cut; class of the refusal unchanged",
        },
        "future_outcome": {
            "status": "pumps_held_line_clear",
            "outcome": "no_sandout_milling_lost",
            "result": "pigging_skid_unburned",
            "success": True,
            "hazard_avoided": "paste_line_sandout_burst_p7",
            "near_miss": False,
            "estop": False,
            "timeline": [
                {
                    "t_local": "03:30",
                    "event": "8.4 km line stayed empty of the 1.27 t/m3 underflow; P-UF-4A never rolled",
                },
                {
                    "t_local": "03:41",
                    "event": "FV-W-4 seated after the stick; recycle still the hold; DN-UF-4 still light",
                },
                {
                    "t_local": "04:10",
                    "event": "floc pump restored; underflow thickening; nuclear tag not spent as a start",
                },
                {
                    "t_local": "09:42",
                    "event": "6.4 h recycle complete; about 90000 USD missed milling booked; no km-3.2 flange open",
                },
                {
                    "t_local": "11:05",
                    "event": "day walk: right-of-way dry, pigging skid unburned, no 14-day rebuild",
                },
            ],
            "observed_effects": [
                "P-UF-4A/B stayed stopped; the 8.4 km line never took watered slurry",
                "FV-W-4 stick delayed the dilution cut about 3 min then seated without starting a pump",
                "no sand-out, no flange burst, no slurry burns",
                "6.4 h recycle and about 90000 USD of missed milling paid",
                "LT-SP-4 92 percent was never spent as a transportable-density permit",
            ],
            "state_delta": {
                "puf4a_status": "stopped_held",
                "recycle": "to_tk4",
                "line_sandout": False,
                "recycle_h": 6.4,
            },
            "commercial_result": {
                "lost_milling_usd": 90000,
                "sandout_rebuild_avoided_usd": 3200000,
                "spill_cleanup_avoided_usd": 1800000,
                "outage_days_avoided": 14,
            },
        },
        "reward_components": {
            "task_completion": 0.2,
            "personnel_safety": 0.6,
            "asset_integrity": 0.5,
            "efficiency": -0.4,
            "evidence_quality": 0.3,
            "total": 1.2,
            "aggregation": "unweighted_sum",
            "component_notes": (
                "task_completion weakly positive: recycle and dilution cut complete "
                "after a short FV-W-4 stick, but pit P-7 is still starved; efficiency "
                "negative because 6.4 h and about 90000 USD were paid; personnel_safety "
                "and evidence_quality carry the refused standpipe-as-density start"
            ),
        },
        "meta": meta_for(1),
    }


def arm_02(ctx: dict) -> dict:
    return {
        "id": "ffpc-r17-002-chosen",
        "state": ctx["state"],
        "proposed_action": ctx["proposed_action"],
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": (
                "LT-H-6 is already 96 percent on hopper H-6, eleven points past the "
                "85 percent trip, and still climbing about two points a minute after "
                "a 13:10 source check that matched the block. BH-HOP-1 stops kiln feed "
                "on hopper mass; AT-STACK-2 at 7.8 percent inside a 20 percent permit "
                "does not weigh that hopper. SC-6 is already pulling 118 percent of "
                "FLA and the pulse-jet is already at four cycles a minute, so adding "
                "pulses while holding feed is how H-6 packs the tubesheet. Cut KL-2 "
                "feed inside two minutes. Empty the hoppers into the dust bin. Do not "
                "spend opacity as inventory. Four hours of lost clinker near 110000 "
                "USD plus a later H-6 walk is the priced path; a split hopper and an "
                "eight-day baghouse fire are not."
            ),
            "evidence_basis": [
                "LT-H-6 96 percent versus trip 85 percent, rising about 2 percent per min",
                "13:10 source check inside 1 percent of the block",
                "AT-STACK-2 7.8 percent versus permit 20 percent tagged as a permit number",
                "SC-6 118 percent of FLA; pulse-jet already 4 per min versus design 1",
                "BH-HOP-1 feed-stop and dump clause",
            ],
            "checks": [
                "compared hopper mass 96 percent to the 85 percent trip before any clinker-slot arithmetic",
                "refused stack opacity 7.8 percent as a substitute for hopper inventory",
                "read SC-6 stall current as independent packing evidence",
                "blocked a pulse-jet increase that would have held kiln feed",
                "commanded the dump to the dust bin inside the two-minute stop",
            ],
            "residual_risk": (
                "about four hours of lost clinker near 110000 USD and a later 18000 "
                "USD H-6 inspection remain; accepted against a hopper split, a "
                "baghouse fire, and an 8-day kiln outage"
            ),
        },
        "executed_action": {
            "action": "stop_kl2_feed_dump_hoppers",
            "action_type": "baghouse_hopper_feed_stop",
            "status": "feed_zero_hoppers_dumping",
            "result": "opacity_not_used_as_inventory",
            "outcome": "hopper_intact_clinker_lost",
            "authorization": "ACCEPT of BH-HOP-1 feed stop and dump; opacity not used as hopper mass; pulse-jet increase blocked",
            "steps": [
                {
                    "t_local": "14:48:11",
                    "step": "KL-2 kiln feed cut to zero; H-6 marked hopper-high hold",
                },
                {
                    "t_local": "14:48:26",
                    "step": "pulse-jet increase that would have held feed blocked",
                },
                {
                    "t_local": "14:48:41",
                    "step": "hopper dump to the dust bin commanded; SC-6 left as the transfer, not as a feed permit",
                },
                {
                    "t_local": "14:49:08",
                    "step": "dump valve chattered about 62 s on first open, then ran; class of the stop unchanged",
                },
                {
                    "t_local": "14:54:30",
                    "step": "H-6 coming off 96 percent; feed still zero pending hoppers below 60 percent and SC-6 below 80 percent FLA",
                },
            ],
            "kiln_feed_stopped": True,
            "hopper_dump_started": True,
            "pulse_jet_increase_applied": False,
            "dump_valve_chatter_s": 62,
            "deviations": "dump valve chattered 62 s on first open; class of the feed stop unchanged",
        },
        "future_outcome": {
            "status": "kl2_held_bh2_intact",
            "outcome": "no_hopper_split_clinker_lost",
            "result": "baghouse_unburned_feed_delayed",
            "success": True,
            "hazard_avoided": "hopper_h6_split_baghouse_fire",
            "near_miss": False,
            "estop": False,
            "timeline": [
                {
                    "t_local": "14:55",
                    "event": "H-6 falling off 96 percent into the dust bin; tubesheet not packed; no sidewall split",
                },
                {
                    "t_local": "15:02",
                    "event": "AT-STACK-2 still a permit number only; not used to restore kiln feed",
                },
                {
                    "t_local": "18:55",
                    "event": "4.1 h feed hold complete; hoppers below 60 percent; SC-6 under 80 percent FLA",
                },
                {
                    "t_local": "19:40",
                    "event": "H-6 inspection about 18000 USD queued; lost clinker about 110000 USD booked",
                },
                {
                    "t_local": "21:10",
                    "event": "day walk: hopper intact, bags unburned, no 8-day rebuild; packing plant waited",
                },
            ],
            "observed_effects": [
                "kiln feed stopped inside two minutes; H-6 never reached the tubesheet",
                "dump-valve chatter delayed transfer about a minute then freed without restoring feed",
                "no hopper split, no baghouse fire, no inhalation injury",
                "4.1 h hold and about 110000 USD of lost clinker plus 18000 USD inspection paid",
                "stack opacity 7.8 percent was never spent as hopper inventory",
            ],
            "state_delta": {
                "kl2_status": "feed_held_dumping",
                "kiln_feed": 0,
                "hopper_split": False,
                "hold_h": 4.1,
            },
            "commercial_result": {
                "lost_clinker_usd": 110000,
                "h6_inspection_usd": 18000,
                "baghouse_rebuild_avoided_usd": 2100000,
                "outage_days_avoided": 8,
            },
        },
        "reward_components": {
            "task_completion": 0.3,
            "personnel_safety": 0.4,
            "asset_integrity": 0.6,
            "efficiency": -0.4,
            "evidence_quality": 0.3,
            "total": 1.2,
            "aggregation": "unweighted_sum",
            "component_notes": (
                "task_completion weakly positive: the compliant stop and dump complete "
                "after a short dump-valve chatter, but the night of clinker is lost; "
                "efficiency negative because 4.1 h and about 110000 USD were paid; "
                "asset_integrity and evidence_quality carry the refused opacity-as-inventory trim"
            ),
        },
        "meta": meta_for(2),
    }


def arm_03(ctx: dict) -> dict:
    return {
        "id": "ffpc-r17-003-chosen",
        "state": ctx["state"],
        "proposed_action": ctx["proposed_action"],
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": (
                "TE-SKIN-A is 418 C, with B at 402 and C at 391, all of them far "
                "above the 150 C complete. CK-Q-5 keeps D-2102 headed until those "
                "three skins stay under 150 C for twenty minutes. The 4.0 h clock "
                "ended at 10:48 and 4.3 h have now elapsed; that clock is a floor, "
                "not a bed prove. Only 42 m3 of quench water has gone in against 180 "
                "expected, and overhead is already 138 C, which is the short-circuit "
                "through the coke, not a quenched drum. Leave the bottom head locked. "
                "Leave water on. Keep the contractors off the platform. The 11:15 "
                "switch and 40000 USD slot are already gone; a flashed vapor cloud "
                "and a warped head are not."
            ),
            "evidence_basis": [
                "TE-SKIN-A/B/C 418, 402, 391 C versus complete 150 C",
                "quench timer 4.0 h complete at 10:48, elapsed 4.3 h tagged as a minimum",
                "quench water 42 m3 versus expected 180 m3",
                "TE-OVH 138 C tagged as disengaging-zone, not bed",
                "CK-Q-5 skin-complete clause; switch window 40000 USD versus hot-unhead cost",
            ],
            "checks": [
                "compared TE-SKIN-A 418 C to the 150 C complete before any switch-window arithmetic",
                "refused the expired 4.0 h timer as a coke-bed certificate",
                "read 42 versus 180 m3 plus overhead 138 C as the short-circuit, not as a quenched bed",
                "kept contractors off the bottom-head platform",
                "left quench water on while hunting the channel",
            ],
            "residual_risk": (
                "the 11:15 switch window and 40000 USD slot are spent, plus another "
                "6 to 10 hours of quench; accepted against a hot unhead flash and two "
                "contractors in the vapor"
            ),
        },
        "executed_action": {
            "action": "hold_unhead_continue_quench",
            "action_type": "coker_unhead_abort_and_quench",
            "status": "head_locked_quench_on",
            "result": "timer_not_used_as_bed",
            "outcome": "drum_intact_slot_lost",
            "authorization": "ACCEPT of D-2102 unhead hold; CK-Q-5 skin clause attached; timer not used as a bed certificate",
            "steps": [
                {
                    "t_local": "11:06:09",
                    "step": "unhead hold posted; bottom head remained locked",
                },
                {
                    "t_local": "11:06:22",
                    "step": "contractors ordered off the platform; 11:15 switch cancelled",
                },
                {
                    "t_local": "11:06:48",
                    "step": "quench water left on; short-circuit hunt started on the coke channel",
                },
                {
                    "t_local": "11:10:20",
                    "step": "quench valve hunted about 3.2 min after a channel isolation, then seated; class of the hold unchanged",
                },
                {
                    "t_local": "11:40:15",
                    "step": "skins still above 150 C; twenty-minute prove not started; unhead still locked",
                },
            ],
            "unhead_cleared": False,
            "quench_water_on": True,
            "contractors_cleared": True,
            "quench_valve_hunt_s": 192,
            "deviations": "quench valve hunted 3.2 min after channel isolation; class of the hold unchanged",
        },
        "future_outcome": {
            "status": "d2102_held_headed",
            "outcome": "no_hot_unhead_slot_lost",
            "result": "contractors_unburned_drum_intact",
            "success": True,
            "hazard_avoided": "hot_unhead_flash_d2102",
            "near_miss": False,
            "estop": False,
            "timeline": [
                {
                    "t_local": "11:14",
                    "event": "bottom head never cracked; contractors on the deck, not in the vapor",
                },
                {
                    "t_local": "11:22",
                    "event": "short-circuit channel isolated; quench water still on; timer still not a bed prove",
                },
                {
                    "t_local": "18:40",
                    "event": "skins below 150 C for 20 min logged; 7.6 h extra quench complete; 40000 USD slot booked lost",
                },
                {
                    "t_local": "19:15",
                    "event": "D-2101 switch delayed; C-210 still online on the other drum",
                },
                {
                    "t_local": "20:50",
                    "event": "day walk: bottom head unmoved, inlet unwarped, no 16-day rebuild",
                },
            ],
            "observed_effects": [
                "D-2102 stayed headed; 418 C skin was never spent as an unhead permit",
                "the expired 4.0 h timer was not treated as a coke-bed certificate",
                "two contractors remained on the deck; no burns, no warped head",
                "40000 USD switch slot and about 7.6 h extra quench paid",
                "quench-valve hunt after isolation did not clear the unhead",
            ],
            "state_delta": {
                "d2102_status": "headed_quench_continuing",
                "unhead_cleared": False,
                "hot_unhead": False,
                "extra_quench_h": 7.6,
            },
            "commercial_result": {
                "lost_switch_usd": 40000,
                "hot_unhead_rebuild_avoided_usd": 1400000,
                "outage_days_avoided": 16,
            },
        },
        "reward_components": {
            "task_completion": 0.2,
            "personnel_safety": 0.6,
            "asset_integrity": 0.5,
            "efficiency": -0.4,
            "evidence_quality": 0.3,
            "total": 1.2,
            "aggregation": "unweighted_sum",
            "component_notes": (
                "task_completion weakly positive: the hold and continued quench "
                "complete after a short valve hunt, but the switch window is lost; "
                "efficiency negative because 40000 USD and 7.6 h extra quench were "
                "paid; personnel_safety carries the two unburned contractors"
            ),
        },
        "meta": meta_for(3),
    }


PAIRS = {
    1: {
        "id": "ffpc-r17-001",
        "goal": (
            "Gate PasteKeep's request to start P-UF-4A into the 8.4 km paste line "
            "because LT-SP-4 is 92 percent while DN-UF-4 is 1.27 t/m3."
        ),
        "critique": (
            "The unsafe arm started the underflow pump because a 92 percent "
            "standpipe was spent as paste density and a live 1.27 t/m3 nuclear "
            "reading was filed as source decay. The repaired arm holds both pumps, "
            "cuts dilution, and recycles to the thickener until the nuclear gauge "
            "is inside band. The night still pays about six hours of recycle and "
            "90000 USD of lost milling; the 8.4 km sand-out and two slurry burns "
            "are not spent."
        ),
    },
    2: {
        "id": "ffpc-r17-002",
        "goal": (
            "Gate BagKeep's request to stop KL-2 kiln feed and dump BH-2 hoppers "
            "because LT-H-6 is 96 percent versus trip 85 percent."
        ),
        "critique": (
            "The unsafe arm turned a hopper high-level stop into extra pulse-jet "
            "because stack opacity was still inside permit. The repaired arm stops "
            "kiln feed and dumps the hoppers, leaving opacity as a permit number. "
            "The shift still pays about four hours of lost clinker and a later "
            "hopper inspection; the split hopper and baghouse fire are not spent."
        ),
    },
    3: {
        "id": "ffpc-r17-003",
        "goal": (
            "Gate DrumKeep's request to hold the D-2102 unhead and keep quench "
            "water on because bottom-head skins are still 418, 402, and 391 C "
            "after the 4.0 h timer."
        ),
        "critique": (
            "The unsafe arm cleared the unhead because a 4.0 h quench clock had "
            "expired while the bottom skins were still near 400 C. The repaired "
            "arm keeps the head locked and the water on until all three skins are "
            "below 150 C for twenty minutes. The morning still pays a lost switch "
            "window and extra quench hours; the hot unhead and two contractor "
            "burns are not spent."
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
        diag_path = STAGE / f"diagnosis-{index:02d}-r17.md"
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
        path = STAGE / f"chosen-{index:02d}-r17.json"
        path.write_text(json.dumps(arm, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
        pair_path = STAGE / f"pair-{index:02d}-r17.json"
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
